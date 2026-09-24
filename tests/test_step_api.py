import io
import json
import random
import threading
import unittest
from unittest.mock import Mock, patch

from calculator import DIGITS, SIGN, MAX_NOUL_STEPS, audit_judgments, predict, predict_noul
from step_api import MAX_BODY, calculate_step, handle_step
from tests.test_calculator import answer


class StepTests(unittest.TestCase):
    def run_steps(self, body, call, rng=None):
        cursor, events, rounds = None, [], 0
        while True:
            before = len(call.calls)
            result = calculate_step({**body, 'cursor': cursor}, 'key-never-returned', model='jev-test', call=call, rng=rng)
            self.assertLessEqual(len(call.calls) - before, 1)
            self.assertNotIn('key-never-returned', json.dumps(result))
            for event in result['events']:
                if event['event'] in ('sign', 'digit', 'comparison', 'equality'):
                    self.assertEqual(event['request'], call.calls[-1])
                    self.assertEqual(set(event['request']), {'model', 'state', 'questions'})
            events.extend(result['events'])
            cursor = result['cursor']
            rounds += 1
            if cursor is None:
                return events, rounds
            self.assertLess(rounds, MAX_NOUL_STEPS + 2)

    def choice_call(self, choices, sign='positive'):
        remaining = iter(choices)
        def call(payload):
            call.calls.append(json.loads(json.dumps(payload)))
            answers = {'digit': answer(next(remaining), DIGITS)}
            if 'sign' in payload['questions']:
                answers['sign'] = answer(sign, SIGN)
            return {'model': 'jev-test', 'answers': answers, 'usage': {'input_tokens': 7, 'output_tokens': 3}}
        call.calls = []
        return call

    def noul_call(self, target, wrong_comparison=False, wrong_sign=False, all_yes=False):
        def call(payload):
            call.calls.append(json.loads(json.dumps(payload)))
            answers = {}
            for key, question in payload['questions'].items():
                if key == 'sign':
                    yes = (target < 0) != wrong_sign
                elif key == 'larger':
                    yes = (int(payload['state']['guess']) > abs(target)) != wrong_comparison
                else:
                    candidate = int(payload['state']['guess'])
                    yes = all_yes or candidate == abs(target)
                answers[key] = {'type': 'noul', 'noul': .9 if yes else .1}
            return {'model': 'jev-test', 'answers': answers, 'usage': {'input_tokens': 10}}
        call.calls = []
        return call

    @staticmethod
    def stable(events):
        return [{k: v for k, v in e.items() if k not in ('latency_ms', 'elapsed_ms', 'match')}
                for e in events if e['event'] != 'start']

    def test_choice_matches_original_flow_and_context(self):
        for context in (False, True):
            with self.subTest(context=context):
                choices = ['2', '0', '1', 'END']
                call = self.choice_call(choices)
                events, rounds = self.run_steps({'expression': '102', 'include_context': context}, call)
                baseline = list(audit_judgments(predict('102', 'jev-test', '', threading.Event(),
                    call=self.choice_call(choices), include_context=context), 102))
                self.assertEqual(self.stable(events), self.stable(baseline))
                self.assertEqual(rounds, 4)
                self.assertTrue(events[-1]['match'])
                for i, payload in enumerate(call.calls):
                    self.assertEqual('predicted_digits_right_to_left' in payload['state'], context)
                    if context:
                        self.assertEqual(payload['state']['predicted_digits_right_to_left'], choices[:i])
                    self.assertNotIn('integer_target', payload['state'])

    def test_first_error_survives_rounds(self):
        events, _ = self.run_steps({'expression': '102'}, self.choice_call(['3', '0', '1', 'END']))
        wrong = [e for e in events if e.get('first_error')]
        self.assertEqual([e['judgment_index'] for e in wrong], [2])
        self.assertEqual(events[-1]['first_error_index'], 2)
        self.assertFalse(events[-1]['match'])

    def test_choice_empty_limit_negative_and_exact_truth(self):
        for expr, seq, sign, status, result in [
            ('0', ['END'], 'positive', 'empty', None),
            ('-7/2', ['3', 'END'], 'negative', 'complete', '-3'),
            ('-1/9', ['0', 'END'], 'negative', 'complete', '0'),
            ('99999999999999999+2', list(reversed('100000000000000001'))+['END'], 'positive', 'complete', '100000000000000001')]:
            with self.subTest(expr=expr):
                events, _ = self.run_steps({'expression': expr}, self.choice_call(seq, sign))
                self.assertEqual(events[-1]['status'], status)
                self.assertEqual(events[-1]['result'], result)
        events, count = self.run_steps({'expression': '1'}, self.choice_call(['1'] * 25))
        self.assertEqual(count, 25)
        self.assertEqual(events[-1]['event'], 'limit')
        events, _ = self.run_steps({'expression': '1'}, self.choice_call(['1'] * 24 + ['END']))
        self.assertEqual(events[-1]['status'], 'complete')

    def test_noul_stepwise_matches_stream_for_both_strategies(self):
        for strategy in ('binary', 'random'):
            for target, wrong, sign, all_yes in [(100,False,False,False), (0,False,False,False),
                    (-100,False,True,False), (100,True,False,False), (1,False,False,True),
                    (3,False,False,False), (2,False,False,False), (10**24+1,False,False,False)]:
                with self.subTest(strategy=strategy, target=target, wrong=wrong, all_yes=all_yes):
                    call = self.noul_call(target, wrong, sign, all_yes)
                    events, _ = self.run_steps({'expression': str(target), 'mode': 'noul', 'strategy': strategy}, call, random.Random(5))
                    baseline = list(audit_judgments(predict_noul(str(target), 'jev-test', '', threading.Event(),
                        call=self.noul_call(target, wrong, sign, all_yes), rng=random.Random(5), strategy=strategy), target))
                    self.assertEqual(self.stable(events), self.stable(baseline))
                    self.assertNotIn('upper', events[0])
                    for payload in call.calls:
                        self.assertEqual(set(payload['state']), {'expression', 'guess'})

    def test_binary_search_midpoint_can_be_answer(self):
        rng = Mock()
        events, _ = self.run_steps({'expression': '6', 'mode': 'noul', 'strategy': 'binary'}, self.noul_call(6), rng)
        self.assertTrue(events[-1]['match'])
        rng.randrange.assert_not_called()
        self.assertEqual(events[-2]['guess'], '6')
        self.assertEqual(events[-2]['event'], 'equality')
        self.assertEqual(events[-2]['before'], ['5', '7'])

    def test_binary_errors_do_not_repair_model_path(self):
        events, _ = self.run_steps({'expression': '100', 'mode': 'noul',
            'strategy': 'binary'}, self.noul_call(100, wrong_comparison=True))
        comparison = next(e for e in events if e['event'] == 'comparison')
        self.assertEqual(comparison['guess'], '4')
        self.assertEqual(comparison['after'], ['3', '3'])
        self.assertTrue(comparison['first_error'])
        self.assertEqual(events[-1]['first_error_index'], 6)
        self.assertFalse(events[-1]['match'])

    def test_noul_invalid_cursor_never_calls_upstream(self):
        body = {'expression': '100', 'mode': 'noul'}
        cursor = calculate_step(body, '', model='jev-test', call=self.noul_call(100))['cursor']
        for changes in ({'phase': 'larger'}, {'phase': 'candidate'}, {'guess': '4'},
                        {'guess': '-1'}, {'low': '2'}, {'high': '3'}, {'count': 512},
                        {'count': 513}, {'guess': '9' * 156}):
            with self.subTest(changes=changes):
                call = Mock()
                with self.assertRaises(ValueError):
                    calculate_step({**body, 'cursor': {**cursor, 'state': {**cursor['state'], **changes}}}, '', call=call)
                call.assert_not_called()

    def test_limit_survives_stateless_expansion(self):
        call = self.noul_call(2**300)
        # Recreate a valid checkpoint just before the request limit.
        body = {'expression': '1', 'mode': 'noul'}
        cursor = calculate_step(body, '', model='jev-test', call=call)['cursor']
        cursor.update(index=512)
        cursor['state'].update(count=511, low=str(2**255+1), high=None, guess=str(2**256), phase='equal')
        result = calculate_step({**body, 'cursor': cursor}, '', model='jev-test', call=call)
        self.assertEqual(result['cursor']['state']['count'], 512)
        before = len(call.calls)
        result = calculate_step({**body, 'cursor': result['cursor']}, '', model='jev-test', call=call)
        self.assertEqual(result['events'][0]['event'], 'limit')
        self.assertIsNone(result['cursor'])
        self.assertEqual(len(call.calls), before)

    def test_strategy_cannot_change_mid_run(self):
        body = {'expression': '100', 'mode': 'noul', 'strategy': 'binary'}
        cursor = calculate_step(body, '', call=self.noul_call(100))['cursor']
        for value in ('random', 'unsupported', None, []):
            call = Mock()
            with self.assertRaises(ValueError):
                calculate_step({**body, 'strategy': value, 'cursor': cursor}, '', call=call)
            call.assert_not_called()

    def test_invalid_cursor_and_inputs_never_call_upstream(self):
        body = {'expression': '102'}
        cursor = calculate_step(body, '', call=self.choice_call(['2']))['cursor']
        cases = [ {'expression':'103','cursor':cursor}, {'expression':'1/0'},
                 {'expression':'1','include_context':'yes'},
                 {'expression':'102','cursor':{}}, {'expression':'102','cursor':{**cursor,'index':129}},
                 {'expression':'102','cursor':{**cursor,'state':{**cursor['state'],'digits':['END']}}}]
        for body in cases:
            call = Mock()
            with self.assertRaises(ValueError):
                calculate_step(body, '', call=call)
            call.assert_not_called()

    def test_no_shared_state_between_clients(self):
        a = calculate_step({'expression':'102'}, 'a', call=self.choice_call(['2']))
        b = calculate_step({'expression':'-3'}, 'b', call=self.choice_call(['3'], 'negative'))
        a2 = calculate_step({'expression':'102','cursor':a['cursor']}, 'a', call=self.choice_call(['0']))
        b2 = calculate_step({'expression':'-3','cursor':b['cursor']}, 'b', call=self.choice_call(['END']))
        self.assertEqual(a2['cursor']['state']['digits'], ['2','0'])
        self.assertEqual(b2['events'][-1]['result'], '-3')

    def test_step_handler_auth_origin_size_and_key_isolation(self):
        def request(body, key='secret-test-key', origin='https://calc.vercel.app'):
            h=Mock()
            payload=json.dumps(body).encode()
            h.headers={'Host':'calc.vercel.app','Origin':origin,'Content-Type':'application/json',
                       'Content-Length':str(len(payload))}
            if key:
                h.headers['Authorization']='Bearer '+key
            h.rfile=io.BytesIO(payload)
            h.wfile=io.BytesIO()
            return h
        with patch('step_api.calculate_step', return_value={'events':[], 'cursor':None}) as call:
            for key in ('first-secret','second-secret'):
                h=request({'expression':'1'},key)
                handle_step(h)
                self.assertEqual(h.send_response.call_args.args[0],200)
                self.assertEqual(call.call_args.args[1],key)
                self.assertNotIn(key,h.wfile.getvalue().decode())
            call.reset_mock()
            for h, status in [(request({},None),401),(request({},origin='https://evil.test'),403),
                              (request({'expression':'1'*(MAX_BODY + 1)}),400)]:
                handle_step(h)
                self.assertEqual(h.send_response.call_args.args[0],status)
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
