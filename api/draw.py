from http.server import BaseHTTPRequestHandler
from draw_api import draw_step
from step_api import handle_step


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        handle_step(self, operation=draw_step, shared_key=True)
