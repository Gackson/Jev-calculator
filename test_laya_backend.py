"""Local provider routing, offline failures, and model input coverage."""
import io
import json
import threading
import tempfile
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from http.client import HTTPConnection

from calculator import CalculatorServer, default_provider
from laya_client import LayaClient, LocalModelFailure
from typesafe_client import model_matches


def local_answer(payload):
    answers = {}
    for key, question in payload['questions'].items():
        if question['type'] == 'noul':
            answers[key] = {'type': 'noul', 'noul': .7}
        else:
            options = question['criteria']
            choice = next(iter(options))
            answers[key] = {'type': 'choice', 'choice': choice, 'confidence': .9,
                            'probabilities': {k: float(k == choice) for k in options}}
    return {'model': 'laya-local', 'answers': answers, 'usage': {'input_tokens': 100}}


class LocalBackendTests(unittest.TestCase):
    def setUp(self):
        self.server = CalculatorServer(('127.0.0.1', 0), 'jev-test', local_key='environment-secret')
        self.server.laya = Mock(side_effect=local_answer, model='laya-local')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, data=None, provider='laya', extra=None):
        conn = HTTPConnection(*self.server.server_address, timeout=5)
        headers = {'Content-Type': 'application/json'}
        if provider is not None:
            headers['X-Inference-Provider'] = provider
        headers.update(extra or {})
        conn.request('GET' if data is None else 'POST', path,
                     body=None if data is None else json.dumps(data), headers=headers)
        response = conn.getresponse()
        body = response.read()
        conn.close()
        return response.status, body

    def test_all_features_local_without_key_or_remote_calls(self):
        cases = [('/api/step', {'expression': '1+1', 'mode': 'choice'}),
                 ('/api/step', {'expression': '1+1', 'mode': 'noul'}),
                 ('/api/chat', {'message': 'Say hello'}),
                 *[('/api/draw', {'prompt': 'cat', 'size': 14, 'mode': mode})
                   for mode in ('enumeration', 'monte_carlo', 'ballpoint')]]
        with patch('typesafe_client.request.build_opener', side_effect=AssertionError('network')):
            for path, data in cases:
                with self.subTest(path=path, data=data):
                    status, body = self.request(path, data, extra={'Authorization': 'malformed ignored'})
                    self.assertEqual(status, 200, body)
                    self.assertIn(b'laya-local', body)
                    self.assertNotIn(b'environment-secret', body)
                    self.assertEqual(self.server.laya.call_args.args[0]['model'], 'laya-local')
        self.assertEqual(self.server.laya.call_count, 6)

    def test_default_provider_config_and_legacy_stream(self):
        self.server.provider = 'laya'
        config = json.loads(self.request('/api/config')[1])
        self.assertEqual(config['provider'], 'laya')
        self.assertEqual(config['providers'], ['typesafe', 'laya'])
        self.assertNotIn('environment-secret', str(config))
        status, body = self.request('/api/calculate', {'expression': '1+1', 'run_id': 'local'}, provider=None)
        self.assertEqual(status, 200)
        self.assertIn(b'laya-local', body)

    def test_typesafe_auth_still_required_and_environment_priority(self):
        with patch('step_api.calculate_step', return_value={'events': [], 'cursor': None}) as call:
            self.assertEqual(self.request('/api/step', {'expression': '1'}, 'typesafe')[0], 200)
            self.assertEqual(call.call_args.args[1], 'environment-secret')
            self.assertNotIn('call', call.call_args.kwargs)
            self.server.local_key = ''
            self.assertEqual(self.request('/api/step', {'expression': '1'}, 'typesafe')[0], 401)
        self.server.laya.assert_not_called()

    def test_reject_unknown_provider_and_cross_origin(self):
        self.assertEqual(self.request('/api/chat', {'message': 'hi'}, 'unknown')[0], 400)
        self.assertEqual(self.request('/api/chat', {'message': 'hi'}, extra={'Origin': 'https://evil.example'})[0], 403)
        self.server.laya.assert_not_called()

    def test_local_error_is_actionable_no_cloud_fallback(self):
        self.server.laya.side_effect = LocalModelFailure('请检查 --laya-path')
        status, body = self.request('/api/chat', {'message': 'hi'})
        self.assertEqual(status, 503)
        self.assertIn('--laya-path', json.loads(body)['error'])

    def test_vercel_rejects_local_provider_and_requires_byok_for_all_features(self):
        import importlib
        for endpoint in ('step', 'chat', 'draw'):
            for local, expected in [(True, 400), (False, 401)]:
                with self.subTest(endpoint=endpoint, local=local):
                    handler = importlib.import_module('api.' + endpoint).handler
                    h = handler.__new__(handler)
                    h.headers = {'Host': 'example.com', 'Content-Type': 'application/json'}
                    if local:
                        h.headers.update({'Authorization': 'Bearer test', 'X-Inference-Provider': 'laya'})
                    h.wfile = io.BytesIO()
                    h.send_response = Mock(); h.send_header = Mock(); h.end_headers = Mock()
                    with patch('typesafe_client.request.build_opener', side_effect=AssertionError('network')):
                        h.do_POST()
                    self.assertEqual(h.send_response.call_args.args[0], expected)


class DefaultProviderTests(unittest.TestCase):
    def test_environment_key_wins_without_checking_laya(self):
        laya = Mock()
        self.assertEqual(default_provider('environment-key', laya), 'typesafe')
        laya.available.assert_not_called()

    def test_no_key_prefers_available_laya_otherwise_byok(self):
        for available, expected in [(True, 'laya'), (False, 'typesafe')]:
            laya = Mock(); laya.available.return_value = available
            self.assertEqual(default_provider('', laya), expected)
            laya.available.assert_called_once_with()

    def test_server_auto_and_explicit_overrides(self):
        for key, configured, available, expected in [
            ('', 'auto', True, 'laya'), ('', 'auto', False, 'typesafe'),
            ('environment-key', 'auto', True, 'typesafe'),
            ('environment-key', 'laya', True, 'laya'), ('', 'typesafe', True, 'typesafe')]:
            with self.subTest(key=bool(key), configured=configured, available=available):
                with patch.object(LayaClient, 'available', return_value=available) as probe:
                    server = CalculatorServer(('127.0.0.1', 0), 'jev-test', local_key=key, provider=configured)
                    try:
                        self.assertEqual(server.provider, expected)
                        self.assertEqual(server.resolve_backend()[0], 'laya-local' if expected == 'laya' else 'jev-test')
                        if key or configured != 'auto': probe.assert_not_called()
                    finally:
                        server.server_close()

    def test_availability_checks_files_and_sdk_without_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            client = LayaClient(directory)
            with patch('laya_client.importlib.util.find_spec', return_value=object()), patch.object(client, '_load') as load:
                self.assertFalse(client.available())
                for name in ['encoder', 'tokenizer']: (Path(directory) / name).mkdir()
                for name in ['rl_agent_config.json', 'model.safetensors']: (Path(directory) / name).touch()
                self.assertTrue(client.available())
                load.assert_not_called()
            with patch('laya_client.importlib.util.find_spec', return_value=None):
                self.assertFalse(client.available())


class LayaClientTests(unittest.TestCase):
    def test_model_identity_validation(self):
        self.assertTrue(model_matches('laya-local', 'laya-local'))
        self.assertFalse(model_matches('laya-local', 'jev-test'))
        self.assertFalse(model_matches('jev-test', 'laya-local'))

    def test_missing_checkpoint_does_not_import_or_download(self):
        client = LayaClient('/nonexistent/laya-model')
        with self.assertRaisesRegex(LocalModelFailure, '--laya-path'):
            client({})

    def test_lazy_load_once_and_raw_predictions_preserved(self):
        client = LayaClient()
        response = {'model': 'laya-rl-agent', 'answers': {'test': {'noul': .1234}}, 'usage': {}}
        agent = Mock(); agent.predict.return_value = response
        def load(): client.agent = agent
        payload = {'state': {'message': 'hello'}, 'questions': {}}
        with patch.object(client, '_load', side_effect=load) as loader, patch.object(client, '_budget'):
            for _ in range(2):
                result = client(payload)
                self.assertEqual(result['answers'], response['answers'])
                self.assertEqual(result['model'], 'laya-local')
        loader.assert_called_once()
        agent.predict.assert_called_with(payload['state'], payload['questions'])

    def test_budget_preserves_large_options_and_long_instructions(self):
        # Fake tokenizer and SDK renderer make budget boundaries deterministic.
        import sys
        client = LayaClient()
        tokenizer = Mock(side_effect=lambda text, **kw: {'input_ids': list(text)})
        tokenizer.mask_token = '[MASK]'
        client.agent = SimpleNamespace(tok=tokenizer, cfg={},
            _to_internal=lambda q: {'t': q['type'], 'ins': q['instructions'], 'crit': q['criteria']},
            model=SimpleNamespace(encoder=SimpleNamespace(config=SimpleNamespace(max_position_embeddings=8192))))
        common = SimpleNamespace(render_options=lambda q: list(q['crit']), serialize_state=json.dumps)
        questions = {'q': {'type': 'choice', 'instructions': 'x' * 500,
                            'criteria': {str(i): None for i in range(197)}}}
        with patch.dict(sys.modules, {'laya.common': common}):
            client._budget({'description': 'cat'}, questions)
            self.assertGreater(client.agent.cfg['head_max_len'], 1000)
            self.assertGreater(client.agent.cfg['max_len'], client.agent.cfg['head_max_len'])
            with self.assertRaisesRegex(LocalModelFailure, '上下文容量'):
                client._budget('x' * 8192, questions)


if __name__ == '__main__':
    unittest.main()
