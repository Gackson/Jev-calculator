"""Stateless one-round API shared by localhost and Vercel. No stored credentials."""
import json
import re
import threading
from urllib.parse import urlsplit

from calculator import (MAX_DIGITS, ApiFailure, audit_judgments, evaluate, fixed_two,
                        parse_range, predict, predict_noul, request_api_key)

MODEL = "jev-1.13.0"
MAX_BODY = 8192


def bounded_int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("预测进度无效，请重新开始计算。")
    return value


def validate_cursor(cursor, identity, upper):
    if not isinstance(cursor, dict) or cursor.get("input") != identity:
        raise ValueError("算式或设置已改变，请重新开始计算。")
    index = bounded_int(cursor.get("index"), 1, 129)
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
        count = bounded_int(state.get("count"), 1, 128)
        bounds = []
        for key in ("low", "high"):
            value = state.get(key)
            if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]{1,25}", value):
                raise ValueError("候选区间无效。")
            bounds.append(int(value))
        low, high = bounds
        if not (0 <= low <= upper + 1 and -1 <= high <= upper and low <= high + 1) or index != count + 1:
            raise ValueError("候选区间或预测步数无效。")
        clean.update(low=str(low), high=str(high), count=count)
    return clean, index, first


def calculate_step(body, token, model=MODEL, call=None, rng=None):
    if not isinstance(body, dict):
        raise ValueError("请求格式不正确。")
    expression, actual = evaluate(body.get("expression"))
    mode = body.get("mode", "choice")
    context = body.get("include_context", True)
    if mode not in ("choice", "noul") or type(context) is not bool:
        raise ValueError("计算模式或 context 开关无效。")
    upper = parse_range(body.get("upper"), actual) if mode == "noul" else None
    identity = {"expression": expression, "mode": mode, "include_context": context,
                "upper": str(upper) if upper is not None else None}
    cursor = body.get("cursor")
    state, index, first = (None, 0, None) if cursor is None else validate_cursor(cursor, identity, upper)
    target = int(actual)
    events = []
    if cursor is None:
        events.append({"event": "start", **identity, "actual": fixed_two(actual),
                       "integer_target": str(target), "max_digits": MAX_DIGITS})
    cancelled = threading.Event()
    stream = (predict_noul(expression, model, token, cancelled, upper, target, call=call, rng=rng,
                           resume=state, single_step=True) if mode == "noul" else
              predict(expression, model, token, cancelled, call=call, include_context=context,
                      resume=state, single_step=True))
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


def handle_step(handler, model=MODEL, local_token=""):
    # Both production and previews use a same-origin UI; never an open CORS proxy.
    origin = handler.headers.get("Origin")
    host = handler.headers.get("Host", "")
    if origin and (urlsplit(origin).netloc != host or urlsplit(origin).scheme not in ("http", "https")):
        return reply(handler, 403, {"error": "仅允许当前网站调用。"})
    if handler.headers.get("Content-Type", "").split(";")[0] != "application/json":
        return reply(handler, 415, {"error": "需要 JSON 请求。"})
    try:
        token = local_token or request_api_key(handler.headers.get("Authorization"))
    except ValueError as exc:
        return reply(handler, 401, {"error": str(exc)})
    try:
        size = int(handler.headers.get("Content-Length", "0"))
        if not 0 < size <= MAX_BODY:
            raise ValueError("请求过大或为空。")
        body = json.loads(handler.rfile.read(size))
        result = calculate_step(body, token, model)
    except ApiFailure as exc:
        message = {"HTTP 401": ("TypeSafe 拒绝了本地环境 Key（401）。请检查 TYPESAFE_API_KEY 或 .env，修改后重启本地服务。" if local_token else "TypeSafe 拒绝了此 API Key（401）。请检查是否复制完整，或重新填写。"),
                   "HTTP 403": "TypeSafe 拒绝访问（403）。请检查此 Key 的权限或账户状态。"}.get(
                       str(exc), "无法完成 TypeSafe 请求，请稍后重试。")
        return reply(handler, 502, {"error": message})
    except (ValueError, TypeError, KeyError, RecursionError):
        # Do not reflect arbitrary request or upstream content (including keys).
        return reply(handler, 400, {"error": "算式、范围或预测进度无效，请检查输入后重新计算。"})
    except Exception:
        return reply(handler, 500, {"error": "本轮预测未完成，请稍后重试。"})
    return reply(handler, 200, result)
