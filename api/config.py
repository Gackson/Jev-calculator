from http.server import BaseHTTPRequestHandler
from step_api import MODEL, reply
from calculator import MAX_DIGITS


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        reply(self, 200, {"model": MODEL, "auth_mode": "byok", "max_digits": MAX_DIGITS})
