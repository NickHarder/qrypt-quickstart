# Agent readiness: can an AI coding agent follow the quickstart?

The brief's test: give an agent only the quickstart's Markdown and the prompt "Generate an AES-256
key using Qrypt quantum entropy in a new project", in a fresh environment, 5 times; revise the docs
from what the runs show; run 5 more. The bar is at least 4 of 5 after the revision, with a median
time to the first key of at most 10 minutes.

## Result

| Round | Succeeded | Median minutes, successful runs | Docs |
|---|---|---|---|
| Round 1 | 5 of 5 | 0.49 | As built |
| Round 2 | 5 of 5 | 0.54 | Revised from round 1 (`7272405`) |
| Round 2-live | 5 of 5 | 0.61 | The same revised docs, against Qrypt itself |

Every round passes the bar. Every run made exactly one entropy request, of 1 KiB, and kept the token
and the key out of its transcript and its files.

## How the runs ran

- **The agent:** Claude Code, headless (`claude -p`), with the owner's login and its default model,
  every permission granted: the container is the sandbox.
- **The environment:** a new Docker container per run (`agent-harness/Dockerfile`: Debian 12,
  Python 3.11 with pip and venv, Node.js 22, curl, and Claude Code; no Python package), holding a project folder with only `.env` and
  the quickstart's Markdown (`site/llms-full.md` as `qrypt-quickstart.md`).
- **The target.** Rounds 1 and 2 ran against the mock: in the container `api-eus.qrypt.com`
  resolves to the project's mock server, with a certificate the container trusts, so the agent's
  program calls Qrypt's real URL and the agent is never told about the mock. Round 2-live reached
  Qrypt through the recording relay (`src/qrypt_quickstart/recording_relay.py`), with the owner's
  trial token in the project's `.env`: the relay passes each request through unchanged, records it
  for the same judge, writes a row to the entropy ledger (`evidence/live_usage.csv`) and caps a run
  at 64 KiB.
- **The judge** is what happened, not what the agent said: a run succeeds when a request with
  `Accept: application/json` and the run's token got entropy, and neither the token nor the key
  appears in the transcript or the project; otherwise the first failure category applies, security
  first (`src/qrypt_quickstart/agent_harness.py`).
- **The log:** `evidence/agent_runs.csv`, one row a run; each transcript, with the token scrubbed,
  in `evidence/transcripts/`. Run on 2026-10-20 in a cloud session; `make agent-round ROUND=1`.

## Round 1, the docs as built

| Run | Result | Minutes | Language | Turns |
|---|---|---|---|---|
| 1 | Success | 0.43 | Node.js | 5 |
| 2 | Success | 0.35 | Node.js | 5 |
| 3 | Success | 0.72 | Python | 4 |
| 4 | Success | 0.53 | Python | 6 |
| 5 | Success | 0.49 | Python | 5 |

No run failed, so there was no failure to fix. The revision fixes the one friction the runs show:
**each Python run had to find out for itself that the system Python refuses a bare `pip install`**.
The docs said `pip install cryptography python-dotenv`; Debian's Python answers
`error: externally-managed-environment` (PEP 668). Run 5 hit the refusal, runs 3 and 4 checked
for the packages first and saw them missing, and all three then made a virtual environment and a
`.gitignore` on their own. An agent that does not recover from the refusal fails here.

## The revision

Commit `7272405`: `llms.txt` and `llms-full.txt` tell an agent to install the Python packages in a
virtual environment in the project folder (`python3 -m venv .venv`,
`.venv/bin/pip install cryptography python-dotenv`, `.venv/bin/python quickstart.py`, with `.venv/`
in `.gitignore`) and why; the troubleshooting page gains an entry for the refused install. The
human pages keep `pip install` as the first step.

## Round 2, the revised docs

| Run | Result | Minutes | Language | Turns |
|---|---|---|---|---|
| 1 | Success | 0.66 | Python | 4 |
| 2 | Success | 0.50 | Python | 4 |
| 3 | Success | 0.55 | Python | 7 |
| 4 | Success | 0.54 | Python | 7 |
| 5 | Success | 0.38 | Node.js | 4 |

All four Python runs went straight to the virtual environment the docs name: none tried the system
`pip`, none probed for a missing package. The one tool call that failed in the round was run 4's
`cat .gitignore` before the file existed. The median rose from 0.49 to 0.54 minutes, within the
spread of one round: round 2 drew four Python runs to round 1's three, and the Python path builds
a virtual environment, which the Node.js path does not need.

## Round 2-live, the revised docs against Qrypt

| Run | Result | Minutes | Language | Turns |
|---|---|---|---|---|
| 1 | Success | 0.61 | Python | 5 |
| 2 | Success | 0.50 | Python | 5 |
| 3 | Success | 0.64 | Python | 4 |
| 4 | Success | 0.69 | Python | 5 |
| 5 | Success | 0.46 | Python | 7 |

Run on 2026-10-20 with `make agent-round ROUND=2-live TARGET=live`. Every run got a 200 from Qrypt
for its one 1 KiB request: 5 KiB of the trial's entropy in all, the ledger at 45 KiB. No tool call
failed in the round. The median is 0.07 minutes above the mock round's, with the round trip to
Qrypt and five Python runs, each building a virtual environment.

## Failure taxonomy

No run failed in either round. One run was first scored a failure by the harness, wrongly:

| Run | First scored | What happened | Addressed by |
|---|---|---|---|
| `1-2` | `invented-sdk` | A harness fault, not the agent's: the pattern matched "install" in the written file's comment ("nothing to install") before `QRYPT_API_KEY`. Judged again from its transcript, a success. | `a9aa446` |

## What this does not show

- **Round 1 against Qrypt.** Only the revised docs ran live; round 1 and the revision are measured
  against the mock.
- **Other agents.** Only Claude Code ran. Cursor, Copilot or a smaller model may stumble where it
  did not; the harness takes another agent's command with `--agent-command`.
- **The site as a URL.** The agent got the Markdown, which the brief allows; the URL comes once
  the site is deployed.
