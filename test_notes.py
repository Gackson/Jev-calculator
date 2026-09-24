"""Global user context reaches every inference step without rewriting the text."""
import io
import json
import threading
import unittest
from unittest.mock import Mock, patch

from calculator import MAX_REQUEST_BODY, predict, predict_noul
from chat_api import chat_step
from draw_api import draw_step
from step_api import calculate_step, handle_step
import test_calculator
import test_step_api
from test_chat_api import response
from test_draw_api import answer

NOTES = '  加油！🧠\nTry this prompt: "check carefully" <script>test</script>\n  '


class NotesTests(unittest.TestCase):
    def test_choice_and_noul_every_step_including_sign_and_end(self):
        helpers = test_step_api.StepTests()
        for context in (False, True):
            call = helpers.choice_call(['2', '1', 'END'])
            events, rounds = helpers.run_steps(dict(expression='12', notes=NOTES, include_context=context), call)
            self.assertEqual(rounds, 3)
            for payload in call.calls:
                self.assertEqual(payload['state']['notes'], NOTES)
                self.assertEqual('predicted_digits_right_to_left' in payload['state'], context)
        for strategy in ('random', 'binary'):
            call = helpers.noul_call(6)
            helpers.run_steps(dict(expression='6', mode='noul', strategy=strategy, notes=NOTES), call)
            self.assertTrue(any('larger' in p['questions'] for p in call.calls))
            for payload in call.calls:
                self.assertEqual(payload['state']['notes'], NOTES)
                self.assertEqual(set(payload['state']), {'expression', 'guess', 'notes'})

    def test_chat_each_character_and_end_keeps_exact_notes_snapshot(self):
        prefix = ''
        for choice in ('H', 'I', 'END'):
            call = Mock(return_value=response(choice))
            result = chat_step(dict(message='Hello', reply=prefix, notes=NOTES), 'key', call=call)
            self.assertEqual(call.call_args.args[0]['state']['notes'], NOTES)
            call.call_args.args[0]['state']['notes'] = 'changed'
            self.assertEqual(result['step']['request']['state']['notes'], NOTES)
            prefix = result['reply']

    def test_all_drawing_phases_and_end(self):
        for mode, selections in [('enumeration', [.7] * 16), ('monte_carlo', ['0,0', 'END']),
                                 ('ballpoint', ['0,0', 'E', 'LIFT', 'END'])]:
            cursor = None
            for choice in selections:
                call = Mock(side_effect=answer(choice))
                result = draw_step(dict(prompt='cat', size=4, mode=mode, notes=NOTES, cursor=cursor), 'key', call=call)
                self.assertEqual(call.call_args.args[0]['state']['notes'], NOTES)
                self.assertEqual(result['steps'][0]['request']['state']['notes'], NOTES)
                cursor = result['cursor']
            self.assertIsNone(cursor)

    def test_notes_cannot_change_mid_cursor(self):
        for operation, body, call in [
            (calculate_step, dict(expression='12'), test_step_api.StepTests().choice_call(['2'])),
            (draw_step, dict(prompt='cat', size=4, mode='ballpoint'), answer('0,0'))]:
            result = operation({**body, 'notes': NOTES}, 'key', model='jev-test' if operation == calculate_step else 'jev-1.13.0', call=call)
            for notes in ('different', ''):
                with self.assertRaises(ValueError):
                    operation({**body, 'notes': notes, 'cursor': result['cursor']}, 'key', call=Mock())

    def test_empty_notes_preserves_original_request_and_invalid_types_never_call_model(self):
        for operation, body, callback in [
            (calculate_step, dict(expression='1'), test_step_api.StepTests().choice_call(['1', '1'])),
            (chat_step, dict(message='Hi'), lambda _: response()),
            (draw_step, dict(prompt='cat', size=4, mode='enumeration'), answer(.7))]:
            for extra in ({}, {'notes': ''}):
                call = Mock(side_effect=callback)
                operation({**body, **extra}, 'key', model='jev-test' if operation == calculate_step else 'jev-1.13.0', call=call)
                self.assertNotIn('notes', call.call_args.args[0]['state'])
            for invalid in (None, True, 4, [], {}):
                call = Mock()
                with self.assertRaises(ValueError):
                    operation({**body, 'notes': invalid}, 'key', call=call)
                call.assert_not_called()

    def test_legacy_stream_passes_notes_to_both_modes(self):
        for mode, function in [('choice', 'predict'), ('noul', 'predict_noul')]:
            handler = test_calculator.ByokTests().handler('test-key')
            data = json.dumps(dict(expression='2', mode=mode, run_id='notes-test', notes=NOTES)).encode()
            handler.headers['Content-Length'] = str(len(data))
            handler.rfile = io.BytesIO(data)
            with patch('calculator.' + function, return_value=iter([])) as stream:
                handler.do_POST()
            self.assertEqual(stream.call_args.kwargs['notes'], NOTES)
        for function, call in [(predict, test_step_api.StepTests().choice_call(['2', 'END'])),
                               (predict_noul, test_step_api.StepTests().noul_call(2))]:
            list(function('2', 'jev-test', 'key', threading.Event(), call=call, notes=NOTES))
            self.assertTrue(all(p['state']['notes'] == NOTES for p in call.calls))

    def test_http_accepts_long_unicode_notes_but_enforces_body_limit(self):
        notes = '加油🧠\n' * 2000
        encoded = json.dumps(dict(message='Hi', notes=notes), ensure_ascii=False).encode()
        h = Mock(headers={'Host': 'localhost', 'Content-Type': 'application/json',
                          'Authorization': 'Bearer key', 'Content-Length': str(len(encoded))},
                 rfile=io.BytesIO(encoded), wfile=io.BytesIO())
        with patch('chat_api.system_one', return_value=response()) as call:
            handle_step(h, operation=chat_step)
        self.assertEqual(h.send_response.call_args.args[0], 200)
        self.assertEqual(call.call_args.args[1]['state']['notes'], notes)
        h.headers['Content-Length'] = str(MAX_REQUEST_BODY + 1)
        h.rfile = Mock()
        handle_step(h, operation=chat_step)
        self.assertEqual(h.send_response.call_args.args[0], 400)
        h.rfile.read.assert_not_called()
