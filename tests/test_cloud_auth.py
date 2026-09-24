import importlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from calculator import ApiFailure
from step_api import handle_step


class CloudAuthTests(unittest.TestCase):
    def handler(self, endpoint='step', authorization=None):
        cls = importlib.import_module('api.' + endpoint).handler
        h = cls.__new__(cls)
        h.headers = {'Host': 'example.com', 'Origin': 'https://example.com',
                     'Content-Type': 'application/json', 'Content-Length': '2'}
        if authorization is not None:
            h.headers['Authorization'] = authorization
        h.rfile = io.BytesIO(b'{}'); h.wfile = io.BytesIO()
        h.send_response = Mock(); h.send_header = Mock(); h.end_headers = Mock()
        return h

    @patch.dict('os.environ', {'VERCEL_ENV': 'production', 'TYPESAFE_API_KEY': 'owner-secret'})
    def test_all_cloud_routes_use_shared_key_without_leaking_it(self):
        for endpoint, target in [('step', 'step_api.calculate_step'), ('chat', 'api.chat.chat_step'), ('draw', 'api.draw.draw_step')]:
            with self.subTest(endpoint=endpoint), patch(target, return_value={'ok': True}) as operation, patch.object(Path, 'read_text', side_effect=AssertionError('dotenv')):
                h = self.handler(endpoint); h.do_POST()
                h.send_response.assert_called_with(200)
                self.assertEqual(operation.call_args.args[1], 'owner-secret')
                self.assertNotIn(b'owner-secret', h.wfile.getvalue())

    @patch.dict('os.environ', {'VERCEL_ENV': 'production', 'TYPESAFE_API_KEY': 'owner-secret'})
    def test_explicit_byok_wins_and_never_falls_back_on_error(self):
        for authorization, status in [('Bearer personal-key', 200), ('', 401), ('Bearer ', 401), ('invalid', 401)]:
            h = self.handler(authorization=authorization); operation = Mock(return_value={'ok': True})
            handle_step(h, operation=operation, shared_key=True)
            h.send_response.assert_called_with(status)
            if status == 200:
                self.assertEqual(operation.call_args.args[1], 'personal-key')
            else:
                operation.assert_not_called()
        h = self.handler(authorization='Bearer personal-key')
        operation = Mock(side_effect=ApiFailure('HTTP 401'))
        handle_step(h, operation=operation, shared_key=True)
        self.assertEqual(operation.call_count, 1)
        self.assertEqual(operation.call_args.args[1], 'personal-key')
        h.send_response.assert_called_with(502)

    def test_config_only_reveals_mode_and_preview_never_uses_shared_key(self):
        for env, secret, expected in [('production','owner-secret','shared'), ('preview','owner-secret','byok'), ('development','owner-secret','byok'), ('production','','byok')]:
            with patch.dict('os.environ', {'VERCEL_ENV': env, 'TYPESAFE_API_KEY': secret}):
                h = self.handler('config'); h.do_GET()
                self.assertEqual(json.loads(h.wfile.getvalue())['auth_mode'], expected)
                self.assertNotIn(b'owner-secret', h.wfile.getvalue())
                if expected == 'byok':
                    h = self.handler(); operation = Mock()
                    handle_step(h, operation=operation, shared_key=True)
                    h.send_response.assert_called_with(401); operation.assert_not_called()

    @patch.dict('os.environ', {'VERCEL_ENV': 'production', 'TYPESAFE_API_KEY': 'owner-secret'})
    def test_origin_local_provider_and_error_sanitization(self):
        for headers, status in [({'Origin': 'https://other.example'}, 403), ({'X-Inference-Provider': 'laya'}, 400)]:
            h = self.handler(); h.headers.update(headers); operation = Mock()
            handle_step(h, operation=operation, shared_key=True)
            h.send_response.assert_called_with(status); operation.assert_not_called()
        for error, status in [(ApiFailure('owner-secret'),502), (ValueError('owner-secret'),400), (RuntimeError('owner-secret'),500)]:
            h = self.handler()
            handle_step(h, operation=Mock(side_effect=error), shared_key=True)
            h.send_response.assert_called_with(status)
            self.assertNotIn(b'owner-secret', h.wfile.getvalue())

    @patch.dict('os.environ', {'VERCEL_ENV': 'production', 'TYPESAFE_API_KEY': 'bad secret'})
    def test_invalid_shared_configuration_is_sanitized_but_byok_still_works(self):
        h = self.handler(); operation = Mock(return_value={'ok': True})
        handle_step(h, operation=operation, shared_key=True)
        h.send_response.assert_called_with(503); operation.assert_not_called()
        self.assertNotIn(b'bad secret', h.wfile.getvalue())
        h = self.handler(authorization='Bearer personal-key')
        handle_step(h, operation=operation, shared_key=True)
        h.send_response.assert_called_with(200)
