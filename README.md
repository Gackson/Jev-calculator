# jev-olympics

**English** · [简体中文](docs/README.zh-CN.md) · [繁體中文](docs/README.zh-TW.md) · [日本語](docs/README.ja.md) · [Español](docs/README.es.md) · [한국어](docs/README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[Enter the arena](https://jev-olympics.vercel.app/)

Three events. No medals. A detailed incident report for every mistake.

This is a small playground powered by TypeSafe's Jev model. Instead of asking for a finished answer, we make Jev choose its way through arithmetic, conversation, and drawing, one decision at a time. Built for amusement. Any practical value is an unintended side effect.

## The events

- **Calculator:** choose digits from right to left with Choice, or search for an integer using Noul's equality and size judgments. A real calculation runs alongside it, so the disappointment is measurable.
- **Chat:** build an English reply one character or word at a time. Word mode has 249 common words, four punctuation marks (`. , ? !`), `NEWLINE`, and `END`: 255 choices. Spaces are inserted automatically.
- **Canvas:** draw on a 4×4 to 14×14 black-and-white grid by scanning pixels, choosing coordinates, or moving a ballpoint pen. Whether the result resembles the prompt is part of the experiment.
- **Notes:** add instructions, context, or encouragement to every decision. Notes take priority over built-in task instructions, within the available choices.

## Inspect the aftermath

Click a digit, character, word, or drawing decision to see its probabilities, confidence when available, model, timing, and token usage. Expand **View full input** to inspect the exact JSON sent for that step, without credentials.

Predictions stay as Jev made them. We do not repair an answer after consulting the answer sheet. Calculator highlights the first wrong judgment; Chat and Canvas preserve their unfinished work.

The interface supports the same six languages as this README. Switching languages does not translate model instructions or output. Conversation, drawing, and Notes live in page memory and disappear on refresh.

## Rules of the games

- **Calculator:** integer operands, arithmetic operators, and parentheses. Exact rational arithmetic supplies the reference; comparison uses the integer truncated toward zero. Choice allows up to 24 digits plus a final termination check. Noul expands a range, then uses random picks or midpoints. Choice can include or exclude prior predictions from context.
- **Chat:** each step receives the message, reply so far, up to three previous turns, and Notes. Word mode also includes prior selections. Two consecutive spaces or five identical characters stop character mode; five identical selections stop word mode. Limits are 64 / 128 / 256 characters or 32 / 64 / 128 word-mode decisions, including punctuation and control markers. Repeat and limit stops are marked incomplete, never disguised as `END`.
- **Canvas:** enumeration visits pixels in order; Monte Carlo selects coordinates or `END`; ballpoint mode selects a start, direction, pen lift, or `END`. Boundaries, repetition checks, and step limits keep the experiment finite.
- **Notes:** captured at the start of a run and sent unchanged with every judgment. They cannot be edited midway. Notes do not guarantee better predictions.

## Run locally

Python 3.9+; TypeSafe inference needs no additional Python dependencies. From the project root, configure `TYPESAFE_API_KEY` in your environment or a local `.env` file:

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

```bash
python3 calculator.py
```

Open <http://127.0.0.1:8765>. Use `--port 8766` to change the port or `--model jev-latest` to change the model. The default is `jev-1.13.0`. The server listens only on localhost. Restart after changing configuration, and keep real credentials out of Git.

Optional local **Laya** inference is also supported. Installation, deployment, and configuration details are in the [development guide](docs/development.md).

## Development

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

Tests use simulated model responses; HTTP integration tests bind a loopback port. CI runs Python 3.9 and 3.12 and checks frontend JavaScript syntax. The tests verify that the experiment works, not that Jev has acquired common sense.

| Directory | Contents |
| --- | --- |
| `calculator_ui/` | Interface and translations |
| `api/` | Vercel function entry points |
| `tests/` | Unit and HTTP integration tests |
| `docs/` | Translated READMEs and development guide |

References: [TypeSafe quickstart](https://docs.typesafe.ai/introduction/quickstart), [Choice](https://docs.typesafe.ai/primitives/choice), [HTTP API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence).
