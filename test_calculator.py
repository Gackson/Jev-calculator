import json
import threading
import unittest
from fractions import Fraction

from calculator import (DIGITS, SIGN, audit_judgments, evaluate, fixed_two, parse_range,
                        predict, predict_noul, random_candidate, validate_choice, validate_noul)
import random
import io
from types import SimpleNamespace
from unittest.mock import Mock, patch
from calculator import Handler, request_api_key, normalize_api_key, ApiFailure


def answer(choice, criteria):
    return {"type": "choice", "choice": choice, "confidence": .83,
            "probabilities": {key: float(key == choice) for key in criteria}}


class CalculatorTests(unittest.TestCase):
    def test_arithmetic_precedence_and_unicode(self):
        self.assertEqual(evaluate("（48 + 27） × 16")[1], 1200)
        self.assertEqual(evaluate("2 + 3 * 4")[1], 14)
        self.assertEqual(evaluate("-100 ÷ 7")[1], Fraction(-100, 7))

    def test_integer_target_truncates_toward_zero(self):
        self.assertEqual(int(evaluate("-7 / 2")[1]), -3)
        self.assertEqual(int(evaluate("-1 / 9")[1]), 0)

    def test_exact_two_decimal_rounding(self):
        for expression, expected in [("100 / 7", "14.29"), ("-1 / 8", "-0.13"),
                                     ("1 / 200", "0.01"), ("-1 / 1000", "0.00"),
                                     ("99999999999999999 + 2", "100000000000000001.00")]:
            self.assertEqual(fixed_two(evaluate(expression)[1]), expected)

    def test_unsafe_and_unsupported_expressions(self):
        for expression in ["", "1/0", "2**100", "8//3", "1.5+2", "abs(-1)",
                           "__import__('os')", "[1]", "0x10", "(3+2", "1" * 301]:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                evaluate(expression)

    def run_sequence(self, choices, sign="positive", cancel=None, max_digits=24):
        calls, remaining = [], iter(choices)
        event = cancel or threading.Event()
        def call(payload):
            calls.append(json.loads(json.dumps(payload)))
            answers = {"digit": answer(next(remaining), DIGITS)}
            if "sign" in payload["questions"]:
                answers["sign"] = answer(sign, SIGN)
            return {"model": "jev-test", "answers": answers, "usage": {"input_tokens": 10, "output_tokens": 5}}
        result = list(predict("102 + 0", "jev-test", "", event, call=call, max_digits=max_digits))
        return result, calls

    def test_right_to_left_internal_zero_and_end(self):
        events, calls = self.run_sequence(["2", "0", "1", "END", "9"])
        self.assertEqual(len(calls), 4)
        self.assertEqual(events[-1]["result"], "102")
        self.assertEqual(events[-1]["tokens"], 60)
        self.assertEqual(calls[2]["state"]["predicted_digits_right_to_left"], ["2", "0"])
        for call in calls:
            self.assertEqual(set(call["state"]), {"expression", "predicted_digits_right_to_left"})
            self.assertEqual(set(call["questions"]["digit"]["criteria"]), set(DIGITS))

    def test_negative_and_zero_results(self):
        self.assertEqual(self.run_sequence(["5", "8", "END"], "negative")[0][-1]["result"], "-85")
        self.assertEqual(self.run_sequence(["0", "END"], "negative")[0][-1]["result"], "0")

    def test_premature_termination_is_not_zero(self):
        events, calls = self.run_sequence(["END", "1"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(events[-1]["status"], "empty")
        self.assertIsNone(events[-1]["result"])

    def test_digit_limit_without_end_is_incomplete(self):
        events, calls = self.run_sequence(["1"] * 4, max_digits=3)
        self.assertEqual(len(calls), 4)
        self.assertEqual(events[-1]["event"], "limit")
        self.assertFalse(any(e["event"] == "done" for e in events))

    def test_end_after_exact_digit_limit_is_allowed(self):
        events, calls = self.run_sequence(["1", "2", "3", "END"], max_digits=3)
        self.assertEqual(events[-1]["result"], "321")

    def test_cancellation_before_request(self):
        event = threading.Event()
        event.set()
        events, calls = self.run_sequence([], cancel=event)
        self.assertEqual(calls, [])
        self.assertEqual(events, [{"event": "cancelled"}])

    def test_cancellation_during_request(self):
        event = threading.Event()
        def call(payload):
            event.set()
            return {}  # Cancelled responses are discarded before use.
        self.assertEqual(list(predict("1+1", "jev-test", "", event, call)), [{"event": "cancelled"}])

    def test_top_three_and_distinct_confidence(self):
        raw = answer("2", DIGITS)
        raw["probabilities"].update({"2": .6, "4": .3, "END": .1})
        validated = validate_choice(raw, DIGITS)
        self.assertEqual([row["option"] for row in validated["top_three"]], ["2", "4", "END"])
        self.assertEqual(validated["confidence"], .83)
        self.assertEqual(validated["probabilities"]["2"], .6)

    def test_invalid_response_rejected(self):
        for change in [{"confidence": float("nan")}, {"choice": "3"}, {"probabilities": {"2": 1}}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_choice({**answer("2", DIGITS), **change}, DIGITS)

    def test_choice_context_can_be_completely_omitted(self):
        calls = []
        def call(payload):
            calls.append(payload)
            answers = {"digit": answer("2" if len(calls) == 1 else "END", DIGITS)}
            if len(calls) == 1:
                answers["sign"] = answer("positive", SIGN)
            return {"model": "jev-test", "answers": answers}
        events = list(predict("1+1", "jev-test", "", threading.Event(), call, include_context=False))
        self.assertEqual(events[-1]["result"], "2")
        for payload in calls:
            self.assertEqual(payload["state"], {"expression": "1+1"})
            self.assertNotIn("predicted_digits", json.dumps(payload))


class NoulTests(unittest.TestCase):
    def run_model(self, target=100, upper=200, wrong_at=None, equals=None, max_steps=128):
        calls = []
        comparisons = 0
        def call(payload):
            nonlocal comparisons
            calls.append(json.loads(json.dumps(payload)))
            answers = {}
            for key, question in payload["questions"].items():
                self.assertEqual(question["type"], "noul")
                if key == "sign":
                    yes = target < 0
                elif key == "larger":
                    comparisons += 1
                    candidate = int(payload["state"]["candidate"])
                    self.assertNotEqual(candidate, abs(target))
                    yes = candidate > abs(target)
                    if comparisons == wrong_at:
                        yes = not yes
                else:
                    candidate = int(question["instructions"].split("equal to ")[1].split("?")[0])
                    yes = candidate == abs(target) if equals is None else candidate in equals
                answers[key] = {"type": "noul", "noul": .9 if yes else .1}
            return {"model": "jev-test", "answers": answers, "usage": {"input_tokens": 1, "output_tokens": 2}}
        events = list(audit_judgments(predict_noul("50+50", "jev-test", "", threading.Event(),
                         upper, target, call, random.Random(7), max_steps), target))
        return events, calls

    def test_range_must_exceed_actual_absolute_value(self):
        for value in ["100", "99", "-1", "1.5", "", "1e4", 200, "1" * 26]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_range(value, Fraction(-100))
        self.assertEqual(parse_range("101", Fraction(-100)), 101)
        with self.assertRaises(ValueError):
            parse_range("100", Fraction(201, 2))

    def test_uniform_candidate_mapping_excludes_truth(self):
        class Fixed:
            def __init__(self, value): self.value = value
            def randrange(self, low, stop):
                self.bounds = low, stop
                return self.value
        self.assertEqual([random_candidate(0, 5, 3, Fixed(n)) for n in range(5)], [0, 1, 2, 4, 5])
        self.assertEqual(random_candidate(0, 5, 99, Fixed(3)), 3)

    def test_correct_search_and_candidate_confirmation(self):
        events, calls = self.run_model()
        self.assertEqual(events[-1]["result"], "100")
        self.assertIsNone(events[-1]["first_error_index"])
        previous = [0, 200]
        for event in events:
            if event["event"] == "comparison":
                self.assertEqual(list(map(int, event["before"])), previous)
                after = list(map(int, event["after"]))
                self.assertLess(after[1] - after[0], previous[1] - previous[0])
                self.assertTrue(after[0] <= 100 <= after[1])
                previous = after
        candidates = [event for event in events if event["event"] == "candidate"]
        self.assertTrue(1 <= len(candidates) < 5)
        for call in calls:
            self.assertTrue(set(call["state"]) <= {"expression", "candidate"})
            self.assertNotIn("correct", json.dumps(call))
        self.assertEqual(len(candidates), len(calls[-1]["questions"]))

    def test_first_wrong_branch_is_retained_not_repaired(self):
        events, calls = self.run_model(wrong_at=1)
        failures = [event for event in events if event.get("first_error")]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["judgment_index"], 2)
        after = list(map(int, failures[0]["after"]))
        self.assertFalse(after[0] <= 100 <= after[1])
        self.assertEqual(events[-1]["status"], "no_match")
        self.assertEqual(events[-1]["first_error_index"], 2)

    def test_zero_and_negative_and_small_initial_range(self):
        for target, upper in [(0, 3), (-2, 3), (-100, 200)]:
            events, calls = self.run_model(target, upper)
            self.assertEqual(events[-1]["result"], str(target))
            self.assertIsNone(events[-1]["first_error_index"])

    def test_multiple_yes_and_all_no_are_explicit(self):
        events, _ = self.run_model(1, 3, equals={1, 2})
        self.assertEqual(events[-1]["status"], "ambiguous")
        self.assertIsNone(events[-1]["result"])
        events, _ = self.run_model(1, 3, equals=set())
        self.assertEqual(events[-1]["status"], "no_match")
        self.assertEqual(events[-1]["first_error_index"], 3)  # sign, zero, one

    def test_noul_probability_and_threshold(self):
        for p, yes, selected in [(.5, True, .5), (.1, False, .9), (1, True, 1)]:
            value = validate_noul({"type": "noul", "noul": p})
            self.assertEqual(value["yes"], yes)
            self.assertEqual(value["decision_probability"], selected)
            self.assertNotIn("confidence", value)
        for p in [float("nan"), True, -.1, 1.1]:
            with self.assertRaises(ValueError):
                validate_noul({"type": "noul", "noul": p})

    def test_step_limit(self):
        events, _ = self.run_model(max_steps=1)
        self.assertEqual(events[-1]["event"], "limit")

    def test_cancel_discards_response(self):
        event = threading.Event()
        def call(payload):
            event.set()
            return {}
        self.assertEqual(list(predict_noul("1+1", "jev-test", "", event, 10, 2, call)), [{"event": "cancelled"}])

    def test_sign_error_is_first_even_if_digits_correct(self):
        raw = [{"event": "sign", "choice": "positive"}, {"event": "digit", "position": 0, "choice": "2"},
               {"event": "digit", "position": 1, "choice": "END"}, {"event": "done"}]
        events = list(audit_judgments(raw, -2))
        self.assertTrue(events[0]["first_error"])
        self.assertTrue(events[1]["correct"])
        self.assertEqual(events[-1]["first_error_index"], 1)


class ByokTests(unittest.TestCase):
    def handler(self, key=None):
        body = json.dumps({"expression": "1+1", "run_id": "byok-test"}).encode()
        handler = Handler.__new__(Handler)
        handler.path = "/api/calculate"
        handler.headers = {"Host": "127.0.0.1:8765", "Content-Type": "application/json", "Content-Length": str(len(body))}
        if key is not None:
            handler.headers["Authorization"] = "Bearer " + key
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.server = SimpleNamespace(model="jev-test", runs={}, run_lock=threading.Lock())
        handler.json_response = Mock()
        handler.headers_for = Mock()
        return handler

    def test_key_required_even_with_environment_key(self):
        handler = self.handler()
        with patch.dict("os.environ", {"TYPESAFE_API_KEY": "unused-environment-key"}), patch("calculator.predict") as predict_mock:
            handler.do_POST()
        self.assertEqual(handler.json_response.call_args.args[0], 401)
        predict_mock.assert_not_called()

    def test_key_format_validation(self):
        self.assertEqual(request_api_key("Bearer test-key"), "test-key")
        for value in [None, "", "Basic test", "Bearer ", "Bearer test key", "Bearer key\nvalue", "Bearer " + "x" * 2049]:
            with self.subTest(value=str(value)[:20]), self.assertRaises(ValueError):
                request_api_key(value)

    def test_each_request_uses_its_own_key_without_echo(self):
        for key in ["test-key-one", "test-key-two"]:
            handler = self.handler(key)
            with patch("calculator.predict", return_value=iter([{"event": "done", "result": "2"}])) as predict_mock:
                handler.do_POST()
            self.assertEqual(predict_mock.call_args.args[2], key)
            self.assertTrue(predict_mock.call_args.kwargs["include_context"])
            self.assertNotIn(key.encode(), handler.wfile.getvalue())
            self.assertFalse(hasattr(handler.server, "token"))
            self.assertEqual(handler.server.runs, {})

    def test_pasted_wrappers_are_removed_before_forwarding(self):
        for value in ['"test-key"', "'test-key'", 'Bearer test-key', 'Authorization: Bearer test-key',
                      'TYPESAFE_API_KEY="test-key"', "export TYPESAFE_API_KEY='test-key'", '“test-key”']:
            with self.subTest(format=value):
                self.assertEqual(normalize_api_key(value), 'test-key')
                handler = self.handler(value)
                with patch("calculator.predict", return_value=iter([{"event": "done", "result": "2"}])) as predict_mock:
                    handler.do_POST()
                self.assertEqual(predict_mock.call_args.args[2], 'test-key')

    def test_config_reports_byok_without_credentials(self):
        handler = self.handler()
        handler.path = "/api/config"
        handler.do_GET()
        status, data = handler.json_response.call_args.args
        self.assertEqual(status, 200)
        self.assertEqual(data["auth_mode"], "byok")
        self.assertEqual(set(data), {"auth_mode", "model", "max_digits"})

    def test_rejected_key_has_actionable_error(self):
        handler = self.handler("test-invalid-key")
        with patch("calculator.predict", side_effect=ApiFailure("HTTP 401")):
            handler.do_POST()
        events = [json.loads(line) for line in handler.wfile.getvalue().splitlines()]
        self.assertEqual(events[-1]["event"], "error")
        self.assertIn("401", events[-1]["message"])
        self.assertNotIn("test-invalid-key", events[-1]["message"])


if __name__ == "__main__":
    unittest.main()
