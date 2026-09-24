import copy
import unittest
from unittest.mock import Mock, patch

from draw_api import DIRECTIONS, draw_step


def answer(selection):
    def call(payload):
        question = payload['questions']['draw']
        result = ({'type': 'noul', 'noul': selection} if question['type'] == 'noul' else
                  {'type': 'choice', 'choice': selection, 'confidence': .8,
                   'probabilities': {key: float(key == selection) for key in question['criteria']}})
        return {'model': 'jev-1.13.0', 'answers': {'draw': result},
                'usage': {'input_tokens': 100, 'output_tokens': 10}}
    return call


class DrawTests(unittest.TestCase):
    def run_steps(self, mode, choices, size=4):
        body = dict(prompt='A small cat', size=size, mode=mode)
        results = []
        for selection in choices:
            result = draw_step(body, 'test-key', call=answer(selection))
            results.append(result)
            body['cursor'] = result['cursor']
        return results

    def test_enumeration_visits_every_pixel_in_order_with_exact_context(self):
        results = self.run_steps('enumeration', [.49, .5, 1, 0] * 4)
        for index, result in enumerate(results):
            step = result['steps'][0]
            self.assertEqual(step['target'], f'{index % 4},{index // 4}')
            self.assertEqual(step['type'], 'noul')
            self.assertEqual(step['index'], index + 1)
            self.assertNotIn('confidence', step)
            self.assertEqual(''.join(step['request']['state']['rows']), results[index - 1]['pixels'] if index else '0' * 16)
            self.assertEqual(result['tokens'], 110)
        self.assertEqual(results[-1]['pixels'], '0110' * 4)
        self.assertEqual(results[-1]['status'], 'complete')
        self.assertIsNone(results[-1]['cursor'])

    def test_all_resolutions_and_all_positions_plus_end(self):
        for mode in ['monte_carlo', 'ballpoint']:
            for size in range(4, 15):
                result = self.run_steps(mode, [f'{size-1},{size-1}'], size)[0]
                criteria = result['steps'][0]['request']['questions']['draw']['criteria']
                self.assertEqual(len(criteria), size * size + 1)
                self.assertIn('END', criteria)
                self.assertEqual(result['pixels'][-1], '1')

    def test_monte_carlo_three_consecutive_same_points_stop(self):
        results = self.run_steps('monte_carlo', ['0,0', '0,0', '1,1', '0,0', '0,0', '0,0'])
        self.assertTrue(all(r['status'] == 'continue' for r in results[:-1]))
        self.assertEqual(results[-1]['status'], 'repeated')
        self.assertEqual(results[-1]['marks'], 6)
        self.assertEqual(results[-1]['pixels'].count('1'), 2)
        # Already-black positions remain available in every round.
        self.assertIn('0,0', results[-1]['steps'][0]['probabilities'])

    def test_monte_carlo_full_canvas(self):
        result = self.run_steps('monte_carlo', [f'{i % 4},{i // 4}' for i in range(16)])[-1]
        self.assertEqual(result['status'], 'full')
        self.assertIsNone(result['cursor'])

    def test_end_can_finish_an_empty_canvas(self):
        for mode in ['monte_carlo', 'ballpoint']:
            result = self.run_steps(mode, ['END'])[0]
            self.assertEqual(result['status'], 'complete')
            self.assertEqual(result['pixels'], '0' * 16)
            self.assertEqual(result['marks'], 0)

    def test_ballpoint_eight_directions_and_corner_boundaries(self):
        for direction, (dx, dy) in DIRECTIONS.items():
            result = self.run_steps('ballpoint', ['1,1', direction])[-1]
            self.assertEqual(result['steps'][0]['target'], f'{1 + dx},{1 + dy}')
            self.assertEqual(set(result['steps'][0]['probabilities']), set(DIRECTIONS) | {'LIFT'})
        result = self.run_steps('ballpoint', ['0,0', 'SE'])[-1]
        self.assertEqual(set(result['steps'][0]['probabilities']), {'E', 'SE', 'S', 'LIFT'})
        self.assertEqual(result['marks'], 2)

    def test_ballpoint_lift_then_new_stroke_then_end(self):
        results = self.run_steps('ballpoint', ['0,0', 'E', 'LIFT', '3,3', 'LIFT', 'END'])
        self.assertEqual(results[2]['marks'], 2)
        self.assertIsNone(results[2]['cursor']['state']['pen'])
        self.assertEqual(results[3]['steps'][0]['phase'], 'place')
        self.assertEqual(results[-1]['marks'], 3)
        self.assertEqual(results[-1]['status'], 'complete')

    def test_ballpoint_limit_is_strictly_greater_than_cell_count(self):
        results = self.run_steps('ballpoint', ['0,0'] + ['E', 'W'] * 8)
        self.assertEqual(results[-2]['marks'], 16)
        self.assertEqual(results[-2]['status'], 'continue')
        self.assertEqual(results[-1]['marks'], 17)
        self.assertEqual(results[-1]['status'], 'limit')
        self.assertEqual(results[-1]['pixels'].count('1'), 2)

    def test_ballpoint_full_canvas(self):
        result = self.run_steps('ballpoint', ['0,0'] + ['E'] * 3 + ['S'] + ['W'] * 3 + ['S'] + ['E'] * 3 + ['S'] + ['W'] * 3)[-1]
        self.assertEqual(result['status'], 'full')
        self.assertEqual(result['marks'], 16)

    def test_invalid_inputs_and_changed_settings_never_call_upstream(self):
        base = dict(prompt='cat', size=4, mode='enumeration')
        cursor = draw_step(base, 'key', call=answer(.7))['cursor']
        invalid = [None, {}, {**base, 'size': True}, {**base, 'size': 3}, {**base, 'size': 15},
                   {**base, 'size': 16}, {**base, 'prompt': ' '}, {**base, 'prompt': 'a'*1001},
                   {**base, 'mode': 'unknown'}, {**base, 'prompt': 'dog', 'cursor': cursor}]
        for field, value in [('pixels', 'x'*16), ('scan', 16), ('pen', -1), ('marks', True), ('judgments', 0)]:
            bad = copy.deepcopy(cursor)
            bad['state'][field] = value
            invalid.append({**base, 'cursor': bad})
        for body in invalid:
            with self.subTest(body=body):
                call = Mock()
                with self.assertRaises(ValueError):
                    draw_step(body, 'key', call=call)
                call.assert_not_called()

    def test_invalid_model_responses(self):
        body = dict(prompt='cat', size=4, mode='monte_carlo')
        for result in [None, {}, {'model': 'other', 'answers': {}},
                       {'model': 'jev-1.13.0', 'answers': {'draw': None}}]:
            with self.assertRaises(ValueError):
                draw_step(body, 'key', call=lambda _: result)
        with self.assertRaises(ValueError):
            draw_step(body, 'key', call=answer('OUTSIDE'))
        with self.assertRaises(ValueError):
            draw_step({**body, 'mode': 'enumeration'}, 'key', call=answer(float('nan')))

    def test_request_is_snapshot_without_credentials(self):
        captured = []
        def call(payload):
            result = answer(.8)(payload)
            captured.append(copy.deepcopy(payload))
            payload['state']['description'] = 'mutated'
            return result
        result = draw_step(dict(prompt='cat', size=4, mode='enumeration'), 'secret-key', call=call)
        self.assertEqual(result['steps'][0]['request'], captured[0])
        self.assertNotIn('secret-key', str(result))

    def test_local_and_vercel_routes_use_shared_draw_operation(self):
        from calculator import Handler
        from api.draw import handler as VercelHandler
        request = Mock()
        request.path = '/api/draw'
        request.server.model = 'jev-1.13.0'
        request.server.local_key = 'local-test-key'
        with patch('step_api.handle_step') as dispatch:
            Handler.do_POST(request)
            dispatch.assert_called_once_with(request, 'jev-1.13.0', local_token='local-test-key', operation=draw_step, backend_resolver=request.server.resolve_backend)
        with patch('api.draw.handle_step') as dispatch:
            VercelHandler.do_POST(request)
            dispatch.assert_called_once_with(request, operation=draw_step)


if __name__ == '__main__':
    unittest.main()
