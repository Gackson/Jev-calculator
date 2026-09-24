"""Global user context reaches every inference step without rewriting the text."""
import copy
import io
import json
import threading
import unittest
from unittest.mock import Mock, patch

from calculator import MAX_REQUEST_BODY, model_request, predict, predict_noul
from chat_api import chat_step
from draw_api import draw_step
from step_api import calculate_step, handle_step
from tests import test_calculator
from tests import test_step_api
from tests.test_chat_api import response
from tests.test_draw_api import answer

NOTES = '  加油！🧠\nTry this prompt: "check carefully" <script>test</script>\n  '


class NotesTests(unittest.TestCase):
    def assert_priority(self, payload, notes=NOTES):
        self.assertEqual(payload['state']['highest_priority_user_instructions'], notes)
        self.assertNotIn('notes', payload['state'])
        self.assertEqual(next(iter(payload['state'])), 'highest_priority_user_instructions')
        for question in payload['questions'].values():
            priority, task = question['instructions'].split('\n\n', 1)
            self.assertIn('`highest_priority_user_instructions`', priority)
            self.assertIn('override the default task instructions and option descriptions', priority)
            self.assertIn('whenever they conflict', priority)
            self.assertTrue(task)

    def test_priority_wrapper_preserves_task_options_and_shared_definitions(self):
        state = {'expression': '1+1', 'notes': NOTES}
        questions = {'digit': {'type': 'choice', 'instructions': 'Choose the units digit.',
                              'criteria': {'2': 'Two', '7': 'Seven'}},
                     'sign': {'type': 'noul', 'instructions': 'Is the result negative?'}}
        original_state, original_questions = copy.deepcopy(state), copy.deepcopy(questions)
        payload = model_request('jev-test', state, questions)
        self.assert_priority(payload)
        self.assertEqual(state, original_state)
        self.assertEqual(questions, original_questions)
        for key, question in payload['questions'].items():
            original = original_questions[key]
            self.assertTrue(question['instructions'].endswith(original['instructions']))
            self.assertEqual({k: v for k, v in question.items() if k != 'instructions'},
                             {k: v for k, v in original.items() if k != 'instructions'})
        plain_state = {'expression': '1+1'}
        self.assertEqual(model_request('jev-test', plain_state, questions),
                         {'model': 'jev-test', 'state': plain_state, 'questions': original_questions})

    def test_choice_and_noul_every_step_including_sign_and_end(self):
        helpers = test_step_api.StepTests()
        for context in (False, True):
            call = helpers.choice_call(['2', '1', 'END'])
            events, rounds = helpers.run_steps(dict(expression='12', notes=NOTES, include_context=context), call)
            self.assertEqual(rounds, 3)
            for payload in call.calls:
                self.assert_priority(payload)
                self.assertEqual('predicted_digits_right_to_left' in payload['state'], context)
        for strategy in ('random', 'binary'):
            call = helpers.noul_call(6)
            helpers.run_steps(dict(expression='6', mode='noul', strategy=strategy, notes=NOTES), call)
            self.assertTrue(any('larger' in p['questions'] for p in call.calls))
            for payload in call.calls:
                self.assert_priority(payload)
                self.assertEqual(set(payload['state']), {'expression', 'guess', 'highest_priority_user_instructions'})

    def test_chat_each_character_and_end_keeps_exact_notes_snapshot(self):
        prefix = ''
        for choice in ('H', 'I', 'END'):
            call = Mock(return_value=response(choice))
            result = chat_step(dict(message='Hello', reply=prefix, notes=NOTES), 'key', call=call)
            self.assert_priority(call.call_args.args[0])
            call.call_args.args[0]['state']['highest_priority_user_instructions'] = 'changed'
            self.assertEqual(result['step']['request']['state']['highest_priority_user_instructions'], NOTES)
            prefix = result['reply']

    def test_all_drawing_phases_and_end(self):
        for mode, selections in [('enumeration', [.7] * 16), ('monte_carlo', ['0,0', 'END']),
                                 ('ballpoint', ['0,0', 'E', 'LIFT', 'END'])]:
            cursor = None
            for choice in selections:
                call = Mock(side_effect=answer(choice))
                result = draw_step(dict(prompt='cat', size=4, mode=mode, notes=NOTES, cursor=cursor), 'key', call=call)
                self.assert_priority(call.call_args.args[0])
                self.assertEqual(result['steps'][0]['request']['state']['highest_priority_user_instructions'], NOTES)
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
                payload = call.call_args.args[0]
                self.assertNotIn('notes', payload['state'])
                self.assertNotIn('highest_priority_user_instructions', payload['state'])
                for question in payload['questions'].values():
                    self.assertNotIn('highest_priority_user_instructions', question['instructions'])
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
            for payload in call.calls:
                self.assert_priority(payload)

    def test_http_accepts_long_unicode_notes_but_enforces_body_limit(self):
        notes = '加油🧠\n' * 2000
        encoded = json.dumps(dict(message='Hi', notes=notes), ensure_ascii=False).encode()
        h = Mock(headers={'Host': 'localhost', 'Content-Type': 'application/json',
                          'Authorization': 'Bearer key', 'Content-Length': str(len(encoded))},
                 rfile=io.BytesIO(encoded), wfile=io.BytesIO())
        with patch('chat_api.system_one', return_value=response()) as call:
            handle_step(h, operation=chat_step)
        self.assertEqual(h.send_response.call_args.args[0], 200)
        self.assert_priority(call.call_args.args[1], notes)
        h.headers['Content-Length'] = str(MAX_REQUEST_BODY + 1)
        h.rfile = Mock()
        handle_step(h, operation=chat_step)
        self.assertEqual(h.send_response.call_args.args[0], 400)
        h.rfile.read.assert_not_called()
