"""Stateless one-round API shared by localhost and Vercel."""
import json
import re
import threading
from urllib.parse import urlsplit
from cloud_auth import shared_api_key

from calculator import (MAX_DIGITS, MAX_NOUL_STEPS, ApiFailure, audit_judgments, evaluate, fixed_two,
                        predict, predict_noul, request_api_key, normalize_api_key, notes_context, MAX_REQUEST_BODY)

MODEL = "jev-1.13.0"
MAX_BODY = MAX_REQUEST_BODY


def bounded_int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("预测进度无效，请重新开始计算。")
    return value


def validate_cursor(cursor, identity):
    if not isinstance(cursor, dict) or cursor.get("input") != identity:
        raise ValueError("算式或设置已改变，请重新开始计算。")
    index = bounded_int(cursor.get("index"), 1, MAX_NOUL_STEPS + 1)
    first = cursor.get("first_error")
    if first is not None:
        bounded_int(first, 1, index)
    state = cursor.get("state")
    if not isinstance(state, dict) or type(state.get("negative")) is not bool:
        raise ValueError("预测进度无效，请重新开始计算。")
    clean = {"negative": state["negative"],
             "tokens": bounded_int(state.get("tokens"), 0, 10 ** 9),
             "elapsed_ms": bounded_int(state.get("elapsed_ms"), 0, 10 ** 9)}
    if identity["mode"] == "choice":
        digits = state.get("digits")
        if not isinstance(digits, list) or not 1 <= len(digits) <= MAX_DIGITS or any(
                not isinstance(d, str) or d not in "0123456789" or len(d) != 1 for d in digits):
            raise ValueError("预测数字无效，请重新开始计算。")
        if index != len(digits) + 1:
            raise ValueError("预测步数无效。")
        clean["digits"] = digits
    else:
        count = bounded_int(state.get("count"), 1, MAX_NOUL_STEPS)

        def number(key):
            value = state.get(key)
            if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]{0,154}", value):
                raise ValueError("搜索进度无效。")
            value = int(value)
            if value > 2 ** MAX_NOUL_STEPS:
                raise ValueError("搜索进度无效。")
            return value

        low, guess = number("low"), number("guess")
        high = None if state.get("high") is None else number("high")
        phase = state.get("phase")
        if (phase not in ("equal", "larger") or index != count + 1 or low > guess
                or (high is not None and not 3 <= low <= guess <= high)
                or (phase == "larger" and guess < 3)):
            raise ValueError("搜索区间或判断步骤无效。")
        if high is None:
            if guess < 3:
                valid = low == guess == count and phase == "equal"
            else:
                # Three initial checks, then equality and size for each power of two.
                valid = (guess >= 4 and guess & (guess - 1) == 0
                         and low == guess // 2 + 1
                         and count == 2 * guess.bit_length() - 3 + (phase == "larger"))
            if not valid:
                raise ValueError("上界探索进度无效。")
        clean.update(low=str(low), high=str(high) if high is not None else None,
                     guess=str(guess), phase=phase, count=count)
    return clean, index, first


def calculate_step(body, token, model=MODEL, call=None, rng=None):
    if not isinstance(body, dict):
        raise ValueError("请求格式不正确。")
    notes = body.get("notes", "")
    extra_context = notes_context(notes)
    expression, actual = evaluate(body.get("expression"))
    mode = body.get("mode", "choice")
    context = body.get("include_context", True)
    if mode not in ("choice", "noul") or type(context) is not bool:
        raise ValueError("计算模式或 context 开关无效。")
    strategy = body.get("strategy", "random")
    if strategy not in ("random", "binary"):
        raise ValueError("未知取数方式。")
    identity = {"expression": expression, "mode": mode, "include_context": context,
                "strategy": strategy, **extra_context}
    cursor = body.get("cursor")
    state, index, first = (None, 0, None) if cursor is None else validate_cursor(cursor, identity)
    target = int(actual)
    events = []
    if cursor is None:
        events.append({"event": "start", **identity, "actual": fixed_two(actual),
                       "integer_target": str(target), "max_digits": MAX_DIGITS})
    cancelled = threading.Event()
    stream = (predict_noul(expression, model, token, cancelled, call=call, rng=rng,
                           resume=state, single_step=True, strategy=strategy, notes=notes) if mode == "noul" else
              predict(expression, model, token, cancelled, call=call, include_context=context,
                      resume=state, single_step=True, notes=notes))
    next_cursor = None
    for item in audit_judgments(stream, target, index, first):
        if item["event"] == "checkpoint":
            next_cursor = {"input": identity, "state": item["state"], "index": item["index"],
                           "first_error": item["first_error"]}
        else:
            if item["event"] == "done":
                item["match"] = item["result"] == str(target)
            events.append(item)
    return {"events": events, "cursor": next_cursor}


def reply(handler, status, data):
    encoded = json.dumps(data, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(encoded)


def handle_step(handler, model=MODEL, local_token="", operation=None, backend_resolver=None, shared_key=False):
    # Both production and previews use a same-origin UI; never an open CORS proxy.
    origin = handler.headers.get("Origin")
    host = handler.headers.get("Host", "")
    if origin and (urlsplit(origin).netloc != host or urlsplit(origin).scheme not in ("http", "https")):
        return reply(handler, 403, {"error": "仅允许当前网站调用。"})
    if handler.headers.get("Content-Type", "").split(";")[0] != "application/json":
        return reply(handler, 415, {"error": "需要 JSON 请求。"})
    call = None
    try:
        if backend_resolver is not None:
            model, call = backend_resolver(handler.headers.get("X-Inference-Provider"))
        elif handler.headers.get("X-Inference-Provider", "typesafe") != "typesafe":
            raise ValueError("本地模型仅限本地服务使用。")
    except ValueError:
        return reply(handler, 400, {"error": "未知或不可用的推理后端。"})
    using_shared = False
    try:
        authorization = handler.headers.get("Authorization")
        if call is not None:
            token = ""
        elif local_token:
            token = local_token
        elif authorization is not None:
            # An explicit personal key never silently falls back to the owner's quota.
            token = request_api_key(authorization)
        elif shared_key and shared_api_key():
            using_shared = True
            token = normalize_api_key(shared_api_key())
        else:
            token = request_api_key(None)
    except ValueError as exc:
        if using_shared:
            return reply(handler, 503, {"error": "共享 Key 暂不可用，请使用自己的 API Key。"})
        return reply(handler, 401, {"error": str(exc)})
    try:
        size = int(handler.headers.get("Content-Length", "0"))
        if not 0 < size <= MAX_BODY:
            raise ValueError("请求过大或为空。")
        body = json.loads(handler.rfile.read(size))
        result = (operation or calculate_step)(body, token, model, **({"call": call} if call is not None else {}))
    except ApiFailure as exc:
        if call is not None:
            return reply(handler, 503, {"error": str(exc)})
        if using_shared:
            return reply(handler, 502, {"error": "共享服务暂不可用，请稍后重试或使用自己的 API Key。"})
        message = {"HTTP 401": ("TypeSafe 拒绝了本地环境 Key（401）。请检查 TYPESAFE_API_KEY 或 .env，修改后重启本地服务。" if local_token else "TypeSafe 拒绝了此 API Key（401）。请检查是否复制完整，或重新填写。"),
                   "HTTP 403": "TypeSafe 拒绝访问（403）。请检查此 Key 的权限或账户状态。"}.get(
                       str(exc), "无法完成 TypeSafe 请求，请稍后重试。")
        return reply(handler, 502, {"error": message})
    except (ValueError, TypeError, KeyError, RecursionError):
        # Do not reflect arbitrary request or upstream content (including keys).
        return reply(handler, 400, {"error": "消息或生成进度无效，请重新发送。" if operation else "算式或预测进度无效，请检查输入后重新计算。"})
    except Exception:
        return reply(handler, 500, {"error": "本轮预测未完成，请稍后重试。"})
    return reply(handler, 200, result)
