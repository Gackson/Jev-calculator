#!/usr/bin/env python3
"""Local Jev digit-by-digit calculator. Python 3.9+, standard library only."""
import argparse
import ast
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
import shlex
from pathlib import Path
import re
import random
import threading
import time

from typesafe_client import ApiFailure, system_one, probability

ROOT = Path(__file__).resolve().parent
MAX_DIGITS = 24
DIGITS = {str(i): f"The digit at the requested position is {i}." for i in range(10)}
DIGITS["END"] = "No digit exists at this position or further left; stop."
SIGN = {"positive": "The integer is zero or positive.", "negative": "The integer is negative."}


def evaluate(expression):
    """Only integer literals and + - * / parentheses; all arithmetic is exact."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("请输入整数算式。")
    expression = expression.strip().translate(str.maketrans({"×": "*", "÷": "/", "−": "-", "（": "(", "）": ")"}))
    if len(expression) > 300 or not re.fullmatch(r"[0-9+*/()\s-]+", expression):
        raise ValueError("请使用整数、加减乘除和括号，最多 300 个字符。")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError):
        raise ValueError("算式格式不正确，请检查括号和运算符。") from None

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int:
            result = Fraction(node.value)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                result = a + b
            elif isinstance(node.op, ast.Sub):
                result = a - b
            elif isinstance(node.op, ast.Mult):
                result = a * b
            else:
                if b == 0:
                    raise ValueError("除数不能为零。")
                result = a / b
        else:
            raise ValueError("仅支持整数及 +、−、×、÷、括号，不支持幂、整除或小数输入。")
        if max(result.numerator.bit_length(), result.denominator.bit_length()) > 2048:
            raise ValueError("算式的中间结果过大，请缩短输入。")
        return result

    value = visit(tree.body)
    return expression, value


def fixed_two(value):
    # Exact round-half-up, including negative values, without float conversion.
    cents, remainder = divmod(abs(value.numerator) * 100, value.denominator)
    cents += 2 * remainder >= value.denominator
    return ("-" if value < 0 and cents else "") + f"{cents // 100}.{cents % 100:02d}"


def digit_question(position, include_context=True):
    place = ["units", "tens", "hundreds", "thousands"][position] if position < 4 else f"10^{position}"
    return {"type": "choice", "instructions": (
        "Compute `expression` with ordinary arithmetic precedence and real division. "
        "Truncate the FINAL result toward zero (7/2 -> 3, -7/2 -> -3), then consider its absolute value "
        "in ordinary decimal notation without leading zeros. Zero is written as one digit 0. "
        f"Which digit is at the {place} place (zero-based position {position} from the right)? "
        "Choose END if this position is beyond the leftmost digit. Never choose END for units. "
        + ("`predicted_digits_right_to_left` contains earlier model predictions, not verified facts. " if include_context else "") +
        "An internal zero is a digit, not END. For 102: units=2, tens=0, hundreds=1, thousands=END."
    ), "criteria": DIGITS}


def validate_choice(answer, criteria):
    if answer.get("type") != "choice" or set(answer.get("probabilities", {})) != set(criteria):
        raise ValueError("JEV 返回的选项不完整。")
    probs = {key: probability(value) for key, value in answer["probabilities"].items()}
    chosen = answer.get("choice")
    if chosen not in probs or probs[chosen] < max(probs.values()) - 1e-8:
        raise ValueError("JEV 返回的选择与概率不一致。")
    if not math.isclose(sum(probs.values()), 1, abs_tol=len(probs) * .005 + 1e-8):
        raise ValueError("JEV 返回的概率分布无效。")
    confidence = probability(answer.get("confidence"))
    ranked = sorted(probs, key=lambda key: (-probs[key], key != chosen, key))
    return {"choice": chosen, "probabilities": probs, "confidence": confidence,
            "top_three": [{"option": key, "probability": probs[key]} for key in ranked[:3]]}


def predict(expression, model, token, cancelled, call=None, max_digits=MAX_DIGITS, include_context=True, resume=None, single_step=False):
    """Yield actual judgments sequentially; never pass the reference answer to Jev."""
    if call is None:
        call = lambda payload: system_one(token, payload)
    state = resume or {}
    digits, negative = list(state.get("digits", [])), state.get("negative", False)
    started = time.monotonic() - state.get("elapsed_ms", 0) / 1000
    total_tokens = state.get("tokens", 0)
    for position in range(len(digits), max_digits + 1):
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        questions = {"digit": digit_question(position, include_context)}
        if position == 0:
            questions["sign"] = {"type": "choice", "instructions":
                "Compute `expression` using ordinary arithmetic precedence and real division. "
                "Truncate the final result toward zero. Is this integer negative or nonnegative? "
                "Zero, including a negative fraction truncated to zero, is nonnegative.", "criteria": SIGN}
        state = {"expression": expression}
        if include_context:
            state["predicted_digits_right_to_left"] = list(digits)
        payload = {"model": model, "state": state, "questions": questions}
        tick = time.monotonic()
        response = call(payload)
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        if not isinstance(response.get("model"), str) or not response["model"].startswith("jev"):
            raise ValueError("JEV 返回了未知模型。")
        answers = response.get("answers", {})
        if set(answers) != set(questions):
            raise ValueError("JEV 返回的问题数量不匹配。")
        total_tokens += sum(response.get("usage", {}).get(k, 0) for k in ("input_tokens", "output_tokens"))
        if position == 0:
            sign = validate_choice(answers["sign"], SIGN)
            negative = sign["choice"] == "negative"
            yield {"event": "sign", **sign}
        answer = validate_choice(answers["digit"], DIGITS)
        yield {"event": "digit", "position": position, "model": response["model"],
               "latency_ms": round((time.monotonic() - tick) * 1000), **answer}
        if answer["choice"] == "END":
            result = str(int(("-" if negative else "") + "".join(reversed(digits)))) if digits else None
            yield {"event": "done", "result": result, "raw_digits": "".join(reversed(digits)),
                   "status": "complete" if digits else "empty", "tokens": total_tokens,
                   "elapsed_ms": round((time.monotonic() - started) * 1000)}
            return
        if position == max_digits:
            yield {"event": "limit", "message": f"已预测 {max_digits} 位，下一位仍未返回终止符。已停止，本次没有完整结果。"}
            return
        digits.append(answer["choice"])
        if single_step:
            yield {"event": "checkpoint", "state": {"digits": digits, "negative": negative,
                   "tokens": total_tokens, "elapsed_ms": round((time.monotonic() - started) * 1000)}}
            return


ARITHMETIC = ("Compute `expression` using ordinary arithmetic precedence and real division. "
              "Truncate only the FINAL result toward zero (7/2 -> 3, -7/2 -> -3). ")


def validate_noul(answer):
    if answer.get("type") != "noul":
        raise ValueError("JEV 返回的判断类型不是 Noul。")
    p = probability(answer.get("noul"))
    return {"type": "noul", "noul": p, "yes": p >= .5,
            "decision_probability": p if p >= .5 else 1 - p}


def parse_range(value, actual):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,25}", value):
        raise ValueError("绝对值上限须为正整数，且不超过 10^24。")
    upper = int(value)
    if not 1 <= upper <= 10 ** 24 or upper <= abs(actual):
        raise ValueError("绝对值上限必须严格大于真实结果的绝对值，且不超过 10^24。")
    return upper


def random_candidate(low, high, target, rng):
    # Uniform sampling excluding only the true answer, without a rejection loop.
    excludes = low <= target <= high
    value = rng.randrange(low, high + 1 - int(excludes))
    return value + int(excludes and value >= target)


def comparison_candidate(low, high, target, rng, strategy="random"):
    if strategy == "random":
        return random_candidate(low, high, target, rng)
    # Called only for ranges with at least five entries. Moving one place right
    # stays in range and avoids giving the answer away in a comparison question.
    midpoint = (low + high) // 2
    return midpoint + int(midpoint == target)


def predict_noul(expression, model, token, cancelled, upper, target, call=None, rng=None, max_steps=128, resume=None, single_step=False, strategy="random"):
    """Truth is used only to exclude pivots, never to repair model decisions."""
    if call is None:
        call = lambda payload: system_one(token, payload)
    if strategy not in ("random", "binary"):
        raise ValueError("未知取数方式。")
    rng = rng or random.SystemRandom()
    state = resume or {}
    low, high = int(state.get("low", 0)), int(state.get("high", upper))
    count, total_tokens = state.get("count", 0), state.get("tokens", 0)
    negative = state.get("negative")
    started = time.monotonic() - state.get("elapsed_ms", 0) / 1000

    def ask(questions, state):
        nonlocal negative, total_tokens
        first = negative is None
        if first:
            questions["sign"] = {"type": "noul", "instructions": ARITHMETIC +
                "Is the resulting integer strictly negative? Zero is not negative."}
        tick = time.monotonic()
        response = call({"model": model, "state": {"expression": expression, **state}, "questions": questions})
        if cancelled.is_set():
            return {}, {}, None
        if not isinstance(response.get("model"), str) or not response["model"].startswith("jev"):
            raise ValueError("JEV 返回了未知模型。")
        answers = response.get("answers", {})
        if set(answers) != set(questions):
            raise ValueError("JEV 返回的问题数量不匹配。")
        total_tokens += sum(response.get("usage", {}).get(k, 0) for k in ("input_tokens", "output_tokens"))
        metadata = {"model": response["model"], "latency_ms": round((time.monotonic() - tick) * 1000)}
        sign = None
        if first:
            decision = validate_noul(answers["sign"])
            negative = decision["yes"]
            sign = {"event": "sign", "choice": "negative" if negative else "positive", **metadata, **decision}
        return answers, metadata, sign

    while high - low + 1 >= 5:
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        if count >= max_steps:
            yield {"event": "limit", "message": f"已达到 {max_steps} 次区间判断上限，停止本次测试。"}
            return
        candidate = comparison_candidate(low, high, abs(target), rng, strategy)
        questions = {"larger": {"type": "noul", "instructions": ARITHMETIC +
            "Consider the absolute value of that integer. Is `candidate` STRICTLY GREATER than that absolute value?",
            "criteria": {"true": "The candidate is too large.", "false": "The candidate is not greater."}}}
        answers, metadata, sign = ask(questions, {"candidate": str(candidate)})
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        if sign:
            yield sign
        decision = validate_noul(answers["larger"])
        before = [str(low), str(high)]
        if decision["yes"]:
            high = candidate - 1
        else:
            low = candidate + 1
        count += 1
        yield {"event": "comparison", "strategy": strategy, "candidate": str(candidate), "before": before,
               "after": [str(low), str(high)], "choice": "大了" if decision["yes"] else "小了",
               **metadata, **decision}
        if single_step:
            yield {"event": "checkpoint", "state": {"low": str(low), "high": str(high),
                   "count": count, "negative": negative, "tokens": total_tokens,
                   "elapsed_ms": round((time.monotonic() - started) * 1000)}}
            return

    accepted = []
    if low <= high:
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        candidates = list(range(low, high + 1))
        questions = {f"equal_{i}": {"type": "noul", "instructions": ARITHMETIC +
            f"Is the absolute value of the resulting integer exactly equal to {candidate}?"}
            for i, candidate in enumerate(candidates)}
        # Independent yes/no questions share one request, each keeps its own probability.
        answers, metadata, sign = ask(questions, {})
        if cancelled.is_set():
            yield {"event": "cancelled"}
            return
        if sign:
            yield sign
        for i, candidate in enumerate(candidates):
            decision = validate_noul(answers[f"equal_{i}"])
            if decision["yes"]:
                accepted.append(candidate)
            yield {"event": "candidate", "candidate": str(candidate), "before": [str(low), str(high)],
                   "choice": "是" if decision["yes"] else "否", **metadata, **decision}
    result = str(-accepted[0] if negative else accepted[0]) if len(accepted) == 1 else None
    yield {"event": "done", "result": result, "status": "complete" if result is not None else "ambiguous" if accepted else "no_match",
           "accepted": [str(n) for n in accepted], "tokens": total_tokens,
           "elapsed_ms": round((time.monotonic() - started) * 1000)}


def audit_judgments(events, target, index=0, first_error=None):
    """Annotate outputs for display only; these labels never feed model context."""
    for event in events:
        kind = event["event"]
        if kind in ("sign", "digit", "comparison", "candidate"):
            index += 1
            if kind == "sign":
                expected = "negative" if target < 0 else "positive"
            elif kind == "digit":
                digits = str(abs(target))
                expected = digits[-1 - event["position"]] if event["position"] < len(digits) else "END"
            elif kind == "comparison":
                expected = "大了" if int(event["candidate"]) > abs(target) else "小了"
            else:
                expected = "是" if int(event["candidate"]) == abs(target) else "否"
            correct = event["choice"] == expected
            is_first = not correct and first_error is None
            if is_first:
                first_error = index
            event = {**event, "judgment_index": index, "correct": correct,
                     "first_error": is_first, "expected": expected}
        elif kind == "checkpoint":
            event = {**event, "index": index, "first_error": first_error}
        elif kind == "done":
            event = {**event, "first_error_index": first_error, "judgments": index}
        yield event


def normalize_api_key(value):
    if not isinstance(value, str):
        raise ValueError("请先填写自己的 TypeSafe API Key。")
    token = value.strip()
    for _ in range(4):
        previous = token
        if len(token) >= 2 and (token[0], token[-1]) in (("\"", "\""), ("'", "'"), ("“", "”"), ("‘", "’")):
            token = token[1:-1].strip()
        token = re.sub(r"^(?:export\s+)?TYPESAFE_API_KEY\s*=\s*", "", token).strip()
        token = re.sub(r"^(?:Authorization:\s*)?Bearer\s+", "", token, flags=re.IGNORECASE).strip()
        if token == previous:
            break
    if not re.fullmatch(r"[\x21-\x7e]{1,2048}", token):
        raise ValueError("API Key 格式不正确，请检查空格或换行。")
    return token


def request_api_key(authorization):
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise ValueError("请先填写自己的 TypeSafe API Key。")
    return normalize_api_key(authorization[7:])


def local_api_key(env=None, dotenv_path=None):
    """Called only by the local CLI: process environment > project .env > BYOK."""
    env = os.environ if env is None else env
    value = env.get("TYPESAFE_API_KEY", "").strip()
    if value:
        return normalize_api_key(value)
    path = ROOT / ".env" if dotenv_path is None else Path(dotenv_path)
    try:
        content = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeError):
        raise ValueError("无法读取项目 .env 文件，请检查文件权限和编码。") from None
    value = ""
    for line in content.splitlines():
        match = re.match(r"^\s*(?:export\s+)?TYPESAFE_API_KEY\s*=\s*(.*)$", line)
        if not match:
            continue
        try:
            parts = shlex.split(match[1], comments=True, posix=True)
        except ValueError:
            raise ValueError(".env 中的 TYPESAFE_API_KEY 格式不正确，请检查引号。") from None
        if len(parts) > 1:
            raise ValueError(".env 中的 TYPESAFE_API_KEY 格式不正确。")
        value = parts[0] if parts else ""
    return normalize_api_key(value) if value.strip() else ""


class CalculatorServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, model, local_key=""):
        super().__init__(address, Handler)
        self.model = model
        self.local_key = local_key
        self.runs = {}
        self.run_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def headers_for(self, status, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()

    def json_response(self, status, body):
        self.headers_for(status, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path == "/api/config":
            return self.json_response(200, {"model": self.server.model, "auth_mode": "environment" if getattr(self.server, "local_key", "") else "byok", "max_digits": MAX_DIGITS})
        routes = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/i18n.js": ("i18n.js", "text/javascript"), "/style.css": ("style.css", "text/css")}
        if self.path not in routes:
            return self.json_response(404, {"error": "页面不存在。"})
        filename, kind = routes[self.path]
        self.headers_for(200, kind + "; charset=utf-8")
        self.wfile.write((ROOT / "calculator_ui" / filename).read_bytes())

    def do_POST(self):
        if self.path == "/api/step":
            from step_api import handle_step
            return handle_step(self, self.server.model, local_token=getattr(self.server, "local_key", ""))
        # Browser requests must originate from this exact local page.
        origin = self.headers.get("Origin")
        expected = f"http://{self.headers.get('Host')}"
        if origin and origin != expected:
            return self.json_response(403, {"error": "仅允许本地页面调用。"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.json_response(415, {"error": "需要 JSON 请求。"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 4096:
                raise ValueError("请求过大或为空。")
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("请求格式不正确。")
            run_id = body.get("run_id")
            if not isinstance(run_id, str) or not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", run_id):
                raise ValueError("缺少有效的运行标识。")
            if self.path == "/api/cancel":
                with self.server.run_lock:
                    event = self.server.runs.get(run_id)
                    if event:
                        event.set()
                return self.json_response(200, {"cancelled": event is not None})
            if self.path != "/api/calculate":
                return self.json_response(404, {"error": "接口不存在。"})
            expression, actual = evaluate(body.get("expression"))
            mode = body.get("mode", "choice")
            if mode not in ("choice", "noul"):
                raise ValueError("未知计算模式。")
            strategy = body.get("strategy", "random")
            if strategy not in ("random", "binary"):
                raise ValueError("未知取数方式。")
            include_context = body.get("include_context", True)
            if type(include_context) is not bool:
                raise ValueError("context 开关必须为布尔值。")
            upper = parse_range(body.get("upper"), actual) if mode == "noul" else None
        except (ValueError, TypeError, RecursionError) as exc:
            return self.json_response(400, {"error": str(exc)})
        try:
            token = getattr(self.server, "local_key", "") or request_api_key(self.headers.get("Authorization"))
        except ValueError as exc:
            return self.json_response(401, {"error": str(exc)})
        event = threading.Event()
        with self.server.run_lock:
            if self.server.runs:
                return self.json_response(409, {"error": "已有测试正在运行，请等待它结束。"})
            self.server.runs[run_id] = event
        try:
            self.headers_for(200, "application/x-ndjson; charset=utf-8")
            def emit(item):
                self.wfile.write((json.dumps(item, ensure_ascii=False) + "\n").encode())
                self.wfile.flush()
            emit({"event": "start", "expression": expression, "actual": fixed_two(actual),
                  "integer_target": str(int(actual)), "max_digits": MAX_DIGITS, "mode": mode,
                  "include_context": include_context, "strategy": strategy, "upper": str(upper) if upper is not None else None})
            try:
                events = (predict_noul(expression, self.server.model, token, event, upper, int(actual), strategy=strategy)
                          if mode == "noul" else predict(expression, self.server.model, token, event,
                                                        include_context=include_context))
                for item in audit_judgments(events, int(actual)):
                    if item["event"] == "done":
                        item["match"] = item["result"] == str(int(actual))
                    emit(item)
            except ApiFailure as exc:
                message = {"HTTP 401": "TypeSafe 拒绝了此 API Key（401）。请检查是否复制完整，或重新填写。",
                           "HTTP 403": "TypeSafe 拒绝访问（403）。请检查此 Key 的权限或账户状态。"}.get(str(exc), f"预测未完成：{exc}")
                emit({"event": "error", "message": message})
            except (ValueError, KeyError, TypeError) as exc:
                emit({"event": "error", "message": f"预测未完成：{exc}"})
            except Exception:
                emit({"event": "error", "message": "服务发生异常，本次预测未完成。"})
        except (BrokenPipeError, ConnectionResetError):
            event.set()
        finally:
            with self.server.run_lock:
                self.server.runs.pop(run_id, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default="jev-1.13.0")
    args = parser.parse_args()
    try:
        key = local_api_key()
    except ValueError as exc:
        parser.error(str(exc))
    server = CalculatorServer(("127.0.0.1", args.port), args.model, local_key=key)
    print(f"Jev calculator: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
