# Development guide

[Back to README](../README.md)

## Local configuration

For TypeSafe inference, local credential precedence is process `TYPESAFE_API_KEY`, then the project `.env`, then the value entered in the page. Environment configuration is read on startup; restart after changing it. Invalid credentials produce an error rather than a silent fallback. `.env` is excluded from Git and Vercel uploads.

The default model is `jev-1.13.0`. Use `--model` to override it, or `--port` to change the local port. The server binds only to `127.0.0.1`.

## Optional local Laya

Use a Python version supported by the Laya SDK and an already-downloaded checkpoint:

```bash
python3 -m venv .venv-laya
.venv-laya/bin/python -m pip install -r requirements-laya.txt
.venv-laya/bin/python calculator.py --provider laya --laya-path /absolute/path/to/laya/multilingual
```

The checkpoint must contain `rl_agent_config.json`, `model.safetensors`, `encoder/`, and `tokenizer/`. Loading is offline; the app does not download weights. The local UI can switch between TypeSafe and Laya. `--provider auto` prefers configured TypeSafe credentials, then an available local Laya checkpoint, then manual TypeSafe configuration.

A Laya failure never falls back to cloud inference. `--laya-device auto|cpu|mps|cuda` selects a device. Large option sets can exceed the encoder budget; the app reports an error rather than truncating input. Laya confidence is not directly comparable to Jev confidence. Laya dependencies and weights are excluded from Vercel deployments.

## Deploy your own instance

Link the project to Vercel. If server-side TypeSafe authentication is desired, configure `TYPESAFE_API_KEY` as a Production Secret, then deploy:

```bash
vercel env add TYPESAFE_API_KEY production --sensitive
vercel deploy --prod
```

Enter secrets through the prompt or stdin, never in source or command arguments. Server-side authentication is enabled only when `VERCEL_ENV=production`; previews require credentials supplied with the request. Cloud functions do not load `.env` or local weights. An explicitly supplied credential takes precedence on the cloud routes and never silently falls back if rejected.

Configuration responses contain only the authentication mode. Judgment snapshots omit authentication headers, and upstream error bodies are not reflected to clients. To disable server-side authentication, remove the variable and redeploy.

For any public instance, configure provider-side usage limits appropriate to that instance. The app has no distributed spending cap or rate limiter, and same-origin checks do not prevent direct scripted requests.

## Tests

Run from the repository root:

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.test_chat_words -v
```

Model responses are mocked. HTTP integration tests require a loopback port. GitHub Actions tests Python 3.9 and 3.12 and runs syntax checks on every file in `calculator_ui/*.js`.

## Source map

| File or directory | Purpose |
| --- | --- |
| `calculator.py` | Local server, exact arithmetic, prediction flows |
| `step_api.py`, `cloud_auth.py` | Request validation and cloud authentication |
| `chat_api.py`, `chat_words.py` | Character / word generation and vocabulary |
| `draw_api.py` | Drawing decisions and progress validation |
| `typesafe_client.py` | Fixed-endpoint TypeSafe HTTP client |
| `laya_client.py` | Optional offline inference |
| `api/`, `vercel.json` | Cloud function entry points and deployment configuration |
| `calculator_ui/` | HTML, CSS, JavaScript, translations |
| `tests/` | Unit and HTTP integration tests |
| `docs/` | Translated READMEs and this guide |
