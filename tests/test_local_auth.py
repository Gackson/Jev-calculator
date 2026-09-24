import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from calculator import Handler, local_api_key
from step_api import handle_step
from tests import test_calculator


class LocalAuthTests(unittest.TestCase):
    def load(self, text, env=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            if text is not None:
                path.write_text(text, encoding='utf-8')
            return local_api_key({} if env is None else env, path)

    def test_process_environment_wins_without_reading_dotenv(self):
        with patch.object(Path, 'read_text', side_effect=AssertionError('must not read file')):
            self.assertEqual(local_api_key({'TYPESAFE_API_KEY':'process-key'}), 'process-key')
        self.assertEqual(self.load('TYPESAFE_API_KEY=file-key', {'TYPESAFE_API_KEY':'process-key'}), 'process-key')

    def test_dotenv_formats_and_no_execution(self):
        for value in ['file-key', '"file-key"', "'file-key'", '"file-key" # comment']:
            self.assertEqual(self.load('# comment\nIGNORED=value\nexport TYPESAFE_API_KEY='+value+'\n'), 'file-key')
        self.assertEqual(self.load('\ufeffTYPESAFE_API_KEY=file-key'), 'file-key')
        self.assertEqual(self.load('TYPESAFE_API_KEY=${OTHER_KEY}'), '${OTHER_KEY}')
        self.assertEqual(self.load('TYPESAFE_API_KEY=file-key', {'TYPESAFE_API_KEY':'  '}), 'file-key')

    def test_missing_empty_file_and_unrelated_keys_use_byok(self):
        for value in [None, '', '# comment', 'OTHER=unused', 'TYPESAFE_API_KEY=', 'TYPESAFE_API_KEY=""']:
            self.assertEqual(self.load(value), '')

    def test_malformed_key_reports_no_secret_and_does_not_fall_back(self):
        for text, env in [('TYPESAFE_API_KEY="secret-value', {}),
                          ('TYPESAFE_API_KEY=secret-value with-space', {}),
                          ('TYPESAFE_API_KEY=file-key', {'TYPESAFE_API_KEY':'secret-value with-space'})]:
            with self.assertRaises(ValueError) as error:
                self.load(text, env)
            self.assertNotIn('secret-value', str(error.exception))
            self.assertNotIn('file-key', str(error.exception))

    def test_config_reports_presence_only(self):
        handler=test_calculator.ByokTests().handler()
        handler.server.local_key='never-return-this-key'
        handler.path='/api/config'
        handler.do_GET()
        status,data=handler.json_response.call_args.args
        self.assertEqual(status,200)
        self.assertEqual(data['auth_mode'],'environment')
        self.assertEqual(set(data),{'auth_mode','model','max_digits'})
        self.assertNotIn('never-return-this-key',json.dumps(data))

    def test_local_legacy_endpoint_prefers_environment(self):
        for supplied in (None,'browser-key'):
            handler=test_calculator.ByokTests().handler(supplied)
            handler.server.local_key='local-env-key'
            with patch('calculator.predict',return_value=iter([{'event':'done','result':'2'}])) as predict:
                handler.do_POST()
            self.assertEqual(predict.call_args.args[2],'local-env-key')
            self.assertNotIn(b'local-env-key',handler.wfile.getvalue())

    def test_local_step_route_explicitly_injects_environment(self):
        handler=test_calculator.ByokTests().handler()
        handler.path='/api/step'
        handler.server.local_key='local-env-key'
        with patch('step_api.handle_step') as step:
            handler.do_POST()
        step.assert_called_once_with(handler,'jev-test',local_token='local-env-key')

    def test_step_environment_priority_for_both_calculation_modes(self):
        for mode in ('choice','noul'):
            for supplied in (None,'browser-key'):
                data=json.dumps({'expression':'1+1','mode':mode}).encode()
                handler=Mock(headers={'Host':'127.0.0.1:8765','Origin':'http://127.0.0.1:8765',
                                     'Content-Type':'application/json','Content-Length':str(len(data))},
                             rfile=io.BytesIO(data),wfile=io.BytesIO())
                if supplied:
                    handler.headers['Authorization']='Bearer '+supplied
                with patch('step_api.calculate_step',return_value={'events':[],'cursor':None}) as calculate:
                    handle_step(handler,local_token='local-env-key')
                self.assertEqual(handler.send_response.call_args.args[0],200)
                self.assertEqual(calculate.call_args.args[1],'local-env-key')
                self.assertNotIn(b'local-env-key',handler.wfile.getvalue())

    def test_preview_entrypoints_ignore_environment_and_dotenv(self):
        from api.step import handler as VercelStep
        from api.config import handler as VercelConfig
        h=VercelStep.__new__(VercelStep)
        h.headers={'Host':'example.vercel.app','Content-Type':'application/json'}
        h.wfile=io.BytesIO()
        h.send_response=Mock(); h.send_header=Mock(); h.end_headers=Mock()
        with patch.dict('os.environ',{'TYPESAFE_API_KEY':'server-secret','VERCEL_ENV':'preview'}), patch.object(Path,'read_text',side_effect=AssertionError('no dotenv read')), patch('step_api.calculate_step') as calculate:
            h.do_POST()
        self.assertEqual(h.send_response.call_args.args[0],401)
        calculate.assert_not_called()
        h=VercelConfig.__new__(VercelConfig)
        h.wfile=io.BytesIO()
        h.send_response=Mock(); h.send_header=Mock(); h.end_headers=Mock()
        with patch.dict('os.environ',{'TYPESAFE_API_KEY':'server-secret','VERCEL_ENV':'preview'}): h.do_GET()
        self.assertEqual(json.loads(h.wfile.getvalue())['auth_mode'],'byok')
        self.assertNotIn(b'server-secret',h.wfile.getvalue())


if __name__ == '__main__': unittest.main()
