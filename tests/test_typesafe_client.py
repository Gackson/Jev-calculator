import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib import error, request

from typesafe_client import ApiFailure, ENDPOINT, NoRedirect, system_one


class TypeSafeClientTests(unittest.TestCase):
    def test_forwards_key_only_in_header(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'{"model":"jev-test","answers":{}}')
        payload = {"model": "jev-test", "state": {"expression": "1+1"}, "questions": {}}
        with patch("typesafe_client.request.build_opener", return_value=opener):
            result = system_one("test-private-key", payload)
        req = opener.open.call_args.args[0]
        self.assertEqual(req.full_url, ENDPOINT)
        self.assertEqual(req.get_header("Authorization"), "Bearer test-private-key")
        self.assertEqual(json.loads(req.data), payload)
        self.assertNotIn(b"test-private-key", req.data)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 90)
        self.assertEqual(result["model"], "jev-test")

    def test_never_forwards_authorization_to_redirect(self):
        handler = NoRedirect()
        req = request.Request(ENDPOINT, headers={"Authorization": "Bearer test-private-key"})
        self.assertIsNone(handler.redirect_request(req, None, 302, "redirect", {}, "https://example.com"))

    def test_errors_do_not_echo_secrets_and_do_not_retry(self):
        for exc in [error.HTTPError(ENDPOINT, 401, "test-private-key", {}, io.BytesIO(b'test-private-key')),
                    error.URLError("test-private-key"), TimeoutError("test-private-key")]:
            opener = Mock()
            opener.open.side_effect = exc
            with patch("typesafe_client.request.build_opener", return_value=opener):
                with self.assertRaises(ApiFailure) as caught:
                    system_one("test-private-key", {})
            self.assertNotIn("test-private-key", str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)

    def test_invalid_response_is_safe_error(self):
        for response in [b'not-json test-private-key', b'[]', b'null']:
            opener = Mock()
            opener.open.return_value = io.BytesIO(response)
            with patch("typesafe_client.request.build_opener", return_value=opener):
                with self.assertRaises(ApiFailure) as caught:
                    system_one("test-private-key", {})
            self.assertNotIn("test-private-key", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
