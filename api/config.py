from http.server import BaseHTTPRequestHandler
from step_api import MODEL, reply
from calculator import MAX_DIGITS
from cloud_auth import shared_api_key


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        reply(self, 200, {"model": MODEL, "auth_mode": "shared" if shared_api_key() else "byok", "max_digits": MAX_DIGITS})
