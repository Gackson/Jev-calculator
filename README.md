# jev-olympics

**English** · [简体中文](docs/README.zh-CN.md) · [繁體中文](docs/README.zh-TW.md) · [日本語](docs/README.ja.md) · [Español](docs/README.es.md) · [한국어](docs/README.ko.md)

Let Jev do math, chat, and draw things—in a probabilistic way.

[Try it online](https://jev-olympics.vercel.app/)

A collection of experiments powered by TypeSafe's Jev model. Each step asks the model to make a choice or estimate a probability, then shows exactly what it selected. Predictions are never repaired to match an expected answer.

- **Calculator:** choose digits from right to left with Choice, or search for an integer with Noul's “equal / larger / smaller” judgments. Compare the prediction with the exact arithmetic result.
- **Chat:** compose replies one character or one word at a time. Word mode offers 249 common English words, four punctuation marks (`. , ? !`), `NEWLINE`, and `END`: 255 choices. Spaces are inserted automatically.
- **Canvas:** draw a black-and-white grid, from 4×4 to 14×14, by scanning pixels, choosing coordinates, or moving a ballpoint pen.
- **Notes:** add shared instructions or encouragement to every model judgment. Notes take priority over built-in task instructions, within each judgment's available options.

Click a digit, word, character, or drawing judgment to inspect its probabilities, confidence (when provided), model, timing, and token usage. “View full input” expands the exact JSON request for that step, without credentials. The UI supports the same six languages as this README; changing UI language does not translate model instructions or output. Conversation, drawing, Notes, and personal keys stay in page memory and are cleared on refresh.

## Use the hosted app

The production site uses a **shared server-side API key** by default, so visitors can try it without entering a key. Click the key button to use your own TypeSafe key instead; clearing it restores shared access. A rejected personal key never falls back to the owner's quota.

To get your own key, visit the [TypeSafe console](https://console.typesafe.ai/keys). Keys entered in the UI are sent over HTTPS to the app backend and then to the fixed TypeSafe endpoint. They are not stored in browser storage or returned in API responses.

## Run locally

Python 3.9+; no third-party dependencies are required for TypeSafe inference.

```bash
python3 calculator.py
```

Open <http://127.0.0.1:8765>. Use `--port 8766` to change the port or `--model jev-latest` to change the model. The default is `jev-1.13.0`; the local server binds only to `127.0.0.1`.

For a local environment key, create `.env` in the project root:

```dotenv
TYPESAFE_API_KEY=your-typesafe-api-key
```

Local precedence is **process environment → project `.env` → browser BYOK**. Restart after changing the environment key. Local environment keys retain priority over UI keys; this differs from the hosted app, where an explicit personal key overrides shared access. Invalid keys cause an error rather than a silent fallback. `.env` is excluded from Git and Vercel uploads.

## Deploy with a shared key

Link the project to Vercel, then add `TYPESAFE_API_KEY` to **Production** as a **Secret** and redeploy:

```bash
vercel env add TYPESAFE_API_KEY production --sensitive
vercel deploy --prod
```

Enter the value through the CLI prompt or stdin; never put a real key in source, a command argument, or documentation. The Python functions read this variable only when `VERCEL_ENV=production`. Preview deployments remain BYOK, even if the variable exists there. Cloud functions never load `.env` or local Laya weights.

`/api/config` reports only the authentication mode, never the key. Request snapshots omit authentication headers, and upstream error bodies are not reflected to clients. The browser receives no shared credential. Removing the production variable and redeploying disables shared access.

**Quota:** public requests spend the owner's TypeSafe quota. The owner manages that quota in the TypeSafe console. There is no application-wide distributed spending cap or rate limiter; same-origin checks do not prevent direct scripted requests. This deployment intentionally allows public trials without a password.

## Experiment behavior

**Calculator:** supports integer operands, arithmetic operators, and parentheses. Exact rational arithmetic supplies the reference result; comparisons use the integer truncated toward zero. Choice has a 24-digit limit plus a final termination check. Noul expands a search range, then uses random picks or midpoints. Wrong predictions remain visible, including the first wrong judgment. Prior predictions can be excluded from Choice context.

**Chat:** context includes the current message, reply so far, up to three previous turns, and Notes. Word mode also sends the exact sequence of prior choices. Character mode stops after two consecutive spaces or five identical characters; word mode stops after five identical selections. Character limits are 64 / 128 / 256; word-mode step limits are 32 / 64 / 128, counting punctuation and control markers. A limit or repeat stop is marked incomplete, never treated as a model-selected `END`. Click tokens or use arrow keys to inspect their steps.

**Canvas:** enumeration visits every pixel in order; Monte Carlo chooses coordinates or `END`; ballpoint mode chooses a start, direction, pen lift, or `END`. The app enforces grid boundaries, repetition stops, and step limits. Each visible decision comes from Jev. Stop and failure preserve the partial drawing.

**Notes:** exact text accompanies each step in `state.highest_priority_user_instructions`, with a priority instruction attached to every question. Notes are captured at the start of a run, cannot change midway, and do not guarantee better results.

## Optional local Laya

Install the optional dependencies with a Python version supported by the Laya SDK and supply an already-downloaded checkpoint:

```bash
python3 -m venv .venv-laya
.venv-laya/bin/python -m pip install -r requirements-laya.txt
.venv-laya/bin/python calculator.py --provider laya --laya-path /absolute/path/to/laya/multilingual
```

The checkpoint must contain `rl_agent_config.json`, `model.safetensors`, `encoder/`, and `tokenizer/`. Loading is offline; the app does not download weights. Select TypeSafe or Laya in the local UI. `--provider auto` prefers a local TypeSafe key, then an available local Laya checkpoint, then BYOK. A Laya failure never falls back to paid cloud inference. Use `--laya-device auto|cpu|mps|cuda` to choose a device. Large option sets may exceed the local encoder budget and produce an explicit error rather than truncated input. Laya confidence is not directly comparable to Jev confidence. Laya is excluded from Vercel deployments.

## Development

Run from the project root:

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
node --check calculator_ui/app.js
```

Tests mock model responses and do not spend API quota. HTTP integration tests bind a loopback port. GitHub Actions runs the suite on Python 3.9 and 3.12, plus syntax checks for every frontend JavaScript file.

| Path | Purpose |
| --- | --- |
| `calculator.py` | Local server, arithmetic and prediction flows |
| `step_api.py`, `cloud_auth.py` | Step validation and cloud authentication |
| `chat_api.py`, `chat_words.py` | Character / word generation and vocabulary |
| `draw_api.py` | Drawing decisions and progress validation |
| `typesafe_client.py` | Fixed-endpoint TypeSafe HTTP client |
| `laya_client.py` | Optional local inference |
| `api/`, `vercel.json` | Vercel function entry points and configuration |
| `calculator_ui/` | HTML, CSS, JavaScript, and UI translations |
| `tests/` | Unit and HTTP integration tests |
| `docs/` | Translated READMEs |

References: [TypeSafe quickstart](https://docs.typesafe.ai/introduction/quickstart), [Choice](https://docs.typesafe.ai/primitives/choice), [HTTP API](https://docs.typesafe.ai/api), [confidence](https://docs.typesafe.ai/confidence), [Vercel secrets](https://vercel.com/docs/environment-variables/sensitive-environment-variables).
