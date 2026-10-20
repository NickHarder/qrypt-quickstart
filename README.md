# Qrypt Quickstart

A 25-line Python, Node and Rust quickstart, troubleshooting site, llms.txt and onboarding PRD for Qrypt quantum entropy.

A developer new to Qrypt, or the AI coding agent working for them, gets from "never heard of Qrypt"
to a working AES-256 key made from quantum entropy: one request for 1 KiB, a key proven with
AES-GCM, and the key never printed. A take-home for Qrypt's Developer Quickstart & Onboarding Funnel
brief (Product Manager role).

## Grader quick-start

You need Python 3.10 or later, Node.js 20.12 or later, and a Qrypt access token for the Entropy
service. Clone the repository, then from its root:

```bash
cp .env.example .env                       # then put your token after QRYPT_API_KEY= in .env
pip install cryptography python-dotenv
python quickstart/python/quickstart.py     # prints the success line
node quickstart/node/quickstart.mjs        # prints the success line
```

Each program asks Qrypt for `size=1` (1 KiB) and prints:

```text
Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).
```

Rust too (the stretch third language, Rust 1.89 or later): `cd rust && cargo run` prints the same
line, reading `.env` from the repository's root.

No token yet? `make bootstrap` then `make e2e` runs all three programs against a local mock of Qrypt's
endpoint, builds the site and checks it shows the code that ran, in under a minute and offline.
Something else printed? Every message is in `site/troubleshooting.html`. Timed from a fresh clone,
these four commands took 18.1 s against the mock ([`evidence/grader_quickstart.md`](evidence/grader_quickstart.md), `make grader-run`).

## Where each deliverable is

| The brief asks for | Here |
|---|---|
| Quickstart code in two languages, at most 25 lines each | [`quickstart/python/quickstart.py`](quickstart/python/quickstart.py), [`quickstart/node/quickstart.mjs`](quickstart/node/quickstart.mjs); a third, Rust (stretch): [`rust/src/main.rs`](rust/src/main.rs) |
| The quickstart site, with troubleshooting | [`site/`](site/index.html), built by `make e2e` into `build/site/`; [`site/troubleshooting.html`](site/troubleshooting.html) |
| Agent-readable docs | [`site/llms.md`](site/llms.md) and [`site/llms-full.md`](site/llms-full.md), built into `llms.txt` and `llms-full.txt` |
| The onboarding PRD | [`PRD.md`](PRD.md) |
| The claims-to-source table, with the fact-check of AI-drafted claims | [`CLAIMS.md`](CLAIMS.md) |
| The agent-readiness test, both rounds | [`AGENT_READINESS.md`](AGENT_READINESS.md) (5 of 5 in round 1, then 5 of 5 on the revised docs against the mock and again against Qrypt) and `evidence/agent_runs.csv`; the harness is [`src/qrypt_quickstart/agent_harness.py`](src/qrypt_quickstart/agent_harness.py) |
| The prioritized backlog | [`BACKLOG.md`](BACKLOG.md), ten RICE-scored items with their evidence; the sheet is `BACKLOG.csv` |
| AI usage | [`AI_USAGE.md`](AI_USAGE.md) |
| Competitive teardown (stretch) | [`evidence/teardown.md`](evidence/teardown.md): RANDOM.ORG's API against the same funnel |
| Timed grader run | [`evidence/grader_quickstart.md`](evidence/grader_quickstart.md) |
| Lighthouse report | [`evidence/lighthouse/`](evidence/lighthouse/summary.json): load p95 1,024 ms on mobile, accessibility 100 |
| CI on every push | [`.github/workflows/ci.yml`](.github/workflows/ci.yml): all three programs against the mock for the success path and 400, 401, 403, 429, 500 and 503 |

## Run the snippets

Against Qrypt, with your token, as above. Against the local mock, which plays Qrypt's endpoint and
answers by token (`mock-200`, `mock-401`, `mock-429`, `mock-503` and others):

```bash
make bootstrap                                                # once per clone
.venv/bin/python -m qrypt_quickstart.mock_server --port 8765  # in one terminal
QRYPT_API_URL=http://127.0.0.1:8765/api/v1/quantum-entropy QRYPT_API_KEY=mock-429 \
  .venv/bin/python quickstart/python/quickstart.py            # in another: prints the 429 message
```

`make e2e` runs all three programs against the mock, counts their lines and builds the site, in one
command. The tests in `tests/` run every error each program can meet, against the mock.

## Build the site

```bash
make bootstrap
.venv/bin/python -m qrypt_quickstart.site_builder --out build/site
python -m http.server --directory build/site 8000   # then open http://127.0.0.1:8000
```

The builder fills each page's code blocks from the files in `quickstart/`, so the site always shows
the code CI runs. CI builds the site on every push and keeps it as an artifact. `make lighthouse`
measures it (10 mobile runs) into `evidence/lighthouse/`.

## Reproduce the agent-readiness test

Each run gives Claude Code, in a new Docker container, a project holding only `.env` and the
quickstart's Markdown, with the brief's prompt (the exact prompt and command are in
[`AI_USAGE.md`](AI_USAGE.md)). Every request its program makes reaches a recording server, and the
harness judges the run from what happened: success, or the failure category.

```bash
docker build -t qrypt-agent-harness agent-harness/
export CLAUDE_CODE_OAUTH_TOKEN=...      # from `claude setup-token`, or set ANTHROPIC_API_KEY
make agent-round ROUND=1                # 5 runs against the mock, logged to evidence/agent_runs.csv
```

In a Claude Code cloud session, set the login as `HARNESS_CLAUDE_CODE_OAUTH_TOKEN` in the
environment's settings: the session keeps `CLAUDE_CODE_OAUTH_TOKEN` for its own login, and the
harness hands the value to the container under that name.

Behind a proxy that inspects TLS, such as a Claude Code cloud session's, build with the proxy's
authority as a secret (`docker build --secret id=extra_ca,src=<its file> ...`) and run with
`HARNESS_OPTIONS='--network host --extra-ca <its file>'`: the container then shares the host's
network, reaches its model and PyPI through the proxy, and still finds `api-eus.qrypt.com` at the mock.

Against the mock, `api-eus.qrypt.com` maps to the mock inside the container, so the agent's program
calls Qrypt's real URL unchanged. `make agent-round ROUND=1 TARGET=live` runs the same round against
Qrypt through a recording relay, which passes every request through unchanged, records it, and
refuses past 64 KiB a run or 8,192 KiB in all; it spends your entropy and needs `QRYPT_API_KEY`.

## Checks

`make gate` is everything a push must pass: lint, types, every test (including the browser tests
and the e2e run), the eval suite and a secrets scan; $0 and offline. `make grader-run` times the
grader quick-start from a fresh clone, against the mock. `make live-check` is the one
check that calls Qrypt (12 KiB, refused past an 8,192 KiB ledger stop); run it only with a token
and on purpose.

## For contributors

[`AGENTS.md`](AGENTS.md) has the working rules, for people and coding agents.
[`HANDOFF.md`](HANDOFF.md) says where the work stands. [`docs/index.md`](docs/index.md) is what the
project knows: the plan, the audit, the users, the architecture, the key metrics and the
deliverables, a level at a time. `make help` lists every command.
