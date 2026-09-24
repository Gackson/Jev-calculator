from http.server import BaseHTTPRequestHandler
from step_api import handle_step


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        handle_step(self, shared_key=True)
