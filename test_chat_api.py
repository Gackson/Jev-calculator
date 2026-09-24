import copy
import io
import json
import unittest
from unittest.mock import Mock, patch

from chat_api import OPTIONS, chat_step
from step_api import handle_step
from typesafe_client import ApiFailure


def response(choice='A'):
    return {'model': 'jev-1.13.0', 'answers': {'character': {
        'type': 'choice', 'choice': choice, 'confidence': .8,
        'probabilities': {key: float(key == choice) for key in OPTIONS}}},
        'usage': {'input_tokens': 100, 'output_tokens': 10}}


class ChatTests(unittest.TestCase):
    def test_prefix_and_history_are_exact_and_next_step_uses_choice(self):
        history = [{'role': 'user', 'content': '你好'}, {'role': 'assistant', 'content': 'HI!'}]
        call = Mock(return_value=response('SPACE'))
        result = chat_step({'message': 'How are you?', 'reply': 'I AM', 'history': history}, 'key', call=call)
        self.assertEqual(call.call_args.args[0]['state'], {'user_message': 'How are you?', 'reply_so_far': 'I AM', 'conversation': history})
        self.assertEqual(result['reply'], 'I AM ')
        self.assertEqual(result['step']['position'], 4)
        self.assertEqual(result['step']['confidence'], .8)
        self.assertEqual(result['step']['probabilities'], response('SPACE')['answers']['character']['probabilities'])
        self.assertEqual(result['status'], 'continue')
        self.assertEqual(result['step']['request'], call.call_args.args[0])
        self.assertEqual(set(result['step']['request']), {'model', 'state', 'questions'})
        call.call_args.args[0]['state']['reply_so_far'] = 'CHANGED'
        self.assertEqual(result['step']['request']['state']['reply_so_far'], 'I AM')

    def test_end_never_becomes_text_including_empty_reply(self):
        for prefix in ['', 'HI']:
            result = chat_step({'message': 'Hello', 'reply': prefix}, 'key', call=lambda _: response('END'))
            self.assertEqual(result['reply'], prefix)
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(result['step']['character'], '')

    def test_whitespace_punctuation_and_limit(self):
        for choice, char in [('NEWLINE', '\n'), ("'", "'"), ('?', '?'), ('0', '0')]:
            result = chat_step({'message': 'Hello', 'max_characters': 1}, 'key', call=lambda _, c=choice: response(c))
            self.assertEqual(result['reply'], char)
            self.assertEqual(result['status'], 'limit')

    def test_second_consecutive_space_stops_and_preserves_judgment(self):
        for prefix in [' ', 'HI ']:
            for limit in [len(prefix) + 1, 128]:
                with self.subTest(prefix=prefix, limit=limit):
                    result = chat_step({'message': 'Hello', 'reply': prefix, 'max_characters': limit},
                                       'key', call=lambda _: response('SPACE'))
                    self.assertEqual(result['status'], 'repeated_space')
                    self.assertEqual(result['reply'], prefix + ' ')
                    self.assertEqual(result['step']['choice'], 'SPACE')
                    self.assertEqual(result['step']['probabilities']['SPACE'], 1)

    def test_nonconsecutive_spaces_do_not_stop(self):
        for prefix, choice in [('HI', 'SPACE'), ('HI ', 'A'), ('HI \n', 'SPACE')]:
            with self.subTest(prefix=prefix, choice=choice):
                result = chat_step({'message': 'Hello', 'reply': prefix}, 'key',
                                   call=lambda _, c=choice: response(c))
                self.assertEqual(result['status'], 'continue')

    def test_stopped_prefix_never_calls_upstream_again(self):
        call = Mock()
        with self.assertRaises(ValueError):
            chat_step({'message': 'Hello', 'reply': 'HI  '}, 'key', call=call)
        call.assert_not_called()

    def test_fifth_identical_character_stops_with_original_details(self):
        for choice, char in [('A', 'A'), ('0', '0'), ('!', '!'), ('NEWLINE', '\n')]:
            for limit in [8, 128]:
                with self.subTest(choice=choice, limit=limit):
                    prefix = 'HI ' + char * 4
                    result = chat_step({'message': 'Hello', 'reply': prefix, 'max_characters': limit},
                                       'key', call=lambda _, c=choice: response(c))
                    self.assertEqual(result['status'], 'repeated_character')
                    self.assertEqual(result['reply'], prefix + char)
                    self.assertEqual(result['step']['choice'], choice)
                    self.assertEqual(result['step']['probabilities'][choice], 1)
                    self.assertEqual(result['step']['request']['state']['reply_so_far'], prefix)
                    call = Mock()
                    with self.assertRaises(ValueError):
                        chat_step({'message': 'Hello', 'reply': result['reply']}, 'key', call=call)
                    call.assert_not_called()

    def test_four_identical_or_nonconsecutive_characters_continue(self):
        for prefix, choice in [('AAA', 'A'), ('AAAA', 'B'), ('ABABABA', 'A'), ('\n\n\n', 'NEWLINE')]:
            with self.subTest(prefix=prefix, choice=choice):
                result = chat_step({'message': 'Hello', 'reply': prefix}, 'key',
                                   call=lambda _, c=choice: response(c))
                self.assertEqual(result['status'], 'continue')

    def test_invalid_inputs_never_call_upstream(self):
        for body in [None, {}, {'message': ''}, {'message': 'x'*1001}, {'message': 'x', 'reply': 'lowercase'},
                     {'message': 'x', 'reply': 'A', 'max_characters': 1}, {'message': 'x', 'max_characters': True},
                     {'message': 'x', 'max_characters': 257}, {'message': 'x', 'history': [{}]},
                     {'message': 'x', 'history': [{'role': 'system', 'content': 'x'}]}]:
            with self.subTest(body=body):
                call = Mock()
                with self.assertRaises(ValueError): chat_step(body, 'key', call=call)
                call.assert_not_called()

    def test_invalid_distributions_rejected(self):
        for mutation in ['missing', 'confidence', 'choice', 'model']:
            data = copy.deepcopy(response())
            if mutation == 'missing': del data['answers']['character']['probabilities']['END']
            if mutation == 'confidence': data['answers']['character']['confidence'] = float('nan')
            if mutation == 'choice': data['answers']['character']['choice'] = 'B'
            if mutation == 'model': data['model'] = 'other'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                chat_step({'message': 'Hi'}, 'key', call=lambda _: data)

    def handler(self, body=None, **headers):
        encoded = json.dumps(body or {'message': 'Hello'}).encode()
        handler = Mock()
        handler.headers = {'Host': 'localhost', 'Content-Type': 'application/json',
                           'Content-Length': str(len(encoded)), 'Authorization': 'Bearer browser-key', **headers}
        handler.rfile = io.BytesIO(encoded); handler.wfile = io.BytesIO()
        return handler

    def test_route_preserves_key_precedence_and_never_returns_key(self):
        for local, expected in [('', 'browser-key'), ('environment-key', 'environment-key')]:
            handler = self.handler()
            operation = Mock(return_value={'status': 'complete'})
            handle_step(handler, local_token=local, operation=operation)
            self.assertEqual(operation.call_args.args[1], expected)
            handler.send_response.assert_called_with(200)
            self.assertNotIn(expected.encode(), handler.wfile.getvalue())

    def test_route_rejects_origin_and_missing_key(self):
        for headers, status in [({'Origin': 'https://other.example'}, 403), ({'Authorization': ''}, 401)]:
            handler = self.handler(**headers); operation = Mock()
            handle_step(handler, operation=operation)
            handler.send_response.assert_called_with(status); operation.assert_not_called()

    def test_route_hides_provider_error_and_invalid_payload(self):
        for error, status in [(ApiFailure('secret provider payload'), 502), (ValueError('secret value'), 400)]:
            handler = self.handler(); handle_step(handler, operation=Mock(side_effect=error))
            handler.send_response.assert_called_with(status)
            self.assertNotIn(b'secret', handler.wfile.getvalue())


if __name__ == '__main__': unittest.main()
