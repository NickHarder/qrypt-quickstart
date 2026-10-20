# Grader quick-start, timed from a fresh clone

Written by `make grader-run` at 2026-10-20T12:58:13Z. Each command is the README's grader quick-start as
written, run in a fresh clone of the committed repository, against the local mock (no token yet). `pip` is a new
virtualenv's, with its cache off, so the install downloads as on a grader's machine. Not timed:
making that virtualenv, and pasting a token into `.env`, which takes a person a few seconds.

| Command | Time | Exit code |
|---|---|---|
| `git clone --quiet file:///home/user/qrypt-quickstart qrypt-quickstart` | 5.2 s | 0 |
| `cp .env.example .env` | 0.0 s | 0 |
| `pip install cryptography python-dotenv` | 12.6 s | 0 |
| `python quickstart/python/quickstart.py` | 0.1 s | 0 |
| `node quickstart/node/quickstart.mjs` | 0.1 s | 0 |

**Total: 18.1 s**, under the brief's 5 minutes (300 s).
Each step's output ends as `grader_quickstart.json` shows.
