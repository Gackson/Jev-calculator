"""Minimal TypeSafe HTTP client. No credential storage, redirects, or retries."""
import json
import math
from urllib import error, request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"


class ApiFailure(RuntimeError):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def system_one(token, payload):
    req = request.Request(ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode(), headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "Jev-Calculator/1.0",
    }, method="POST")
    try:
        with request.build_opener(NoRedirect).open(req, timeout=90) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise ApiFailure("TypeSafe 返回了无效响应。")
        return data
    except error.HTTPError as exc:
        # Do not expose response bodies, URLs, or credentials in errors.
        raise ApiFailure(f"HTTP {exc.code}") from None
    except (error.URLError, TimeoutError, OSError):
        raise ApiFailure("无法连接 TypeSafe 或请求超时。") from None
    except (ValueError, UnicodeError):
        raise ApiFailure("TypeSafe 返回了无效响应。") from None


def probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid probability in model response")
    return float(value)
