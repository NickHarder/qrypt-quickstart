---
type: Deliverables
title: Deliverables of the Qrypt quickstart take-home
description: Every requirement of the assessment, with its id, where in the brief it is stated, the phase of the plan that meets it and the command or file that will prove it.
tags: [brief, requirements, plan]
status: draft
generated: { by: claude-code/2.1.304, at: 2026-10-20T19:14:09Z }
sources:
  - id: assessment
    resource: brief/assessment-text.md
    title: The assessment's full text
  - id: plan
    resource: PLAN.md
    title: The plan
---

# How to read this

One row per requirement of [the assessment](brief/assessment-text.md), which wins wherever the
other files of the brief disagree with it.[^assessment] "Where" names a phase of
[the plan](PLAN.md).[^plan] Status is one of `Not yet`, `Met`, `Met differently: <why>` and
`Owner to do`. A row moves to `Met` only with its proof run or committed, never on a prediction.

**Hard gates**, marked ⛔ in the table, must hold before something else may start:

- A live Qrypt token in the owner's `.env` before any live call: the live check (Phase 7), the
  agent-readiness rounds (Phase 8) and the demo's fresh run (Phase 11).
- Round 1 of the agent-readiness test logged before the docs are revised, and the revision
  committed before Round 2.
- Both rounds logged before the backlog is scored: its items are drawn from their findings.
- The kit's own hard gate: `docs/AUDIT.md` committed before any product code.

**The deadline** for every row: before the interview on Wednesday 2026-10-21 at 13:30 CDT
(18:30 UTC). The work freezes at 12:00 CDT that day (17:00 UTC).

# Core requirements

| Id | Requirement (the brief's words, shortened) | Where in the brief | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-01 | Quickstart in two languages: read `QRYPT_API_KEY` from `.env`, fetch 1 KiB, take 32 bytes as an AES-256 key, encrypt and decrypt a sample with AES-GCM, print a clear success line, never the key | Core 1 | Not yet | Phase 1 (Python), Phase 2 (Node) | `make e2e`: each snippet against the mock prints the success line; a test asserts no 32-byte key, hex or base64 form of it is in the output |
| RQ-02 | Each snippet at most 25 lines, excluding comments and imports | Core 1, Accept | Met | Phases 1, 2, 10 | `make check C=snippet-lines`: Python 25 of 25, Node 25 of 25 (comments, docstrings and imports excluded, `src/qrypt_quickstart/snippet_lines.py`) |
| RQ-03 | CI runs both snippets against a mock server, for the success path and 401, 429 and 503, on every push | Core 1; Code quality | Met | Phase 1 (push trigger, success), Phase 3 (errors) | CI on every push (`.github/workflows/ci.yml`, a `push` trigger for every branch) runs `tests/test_quickstart_python.py`, `tests/test_quickstart_node.py` and `tests/test_quickstart_errors.py`: both programs against the mock for the success path and 400, 401, 403, 429, 500 and 503; green on each push since run 39350395398 |
| RQ-04 | Each snippet handles a missing token with a helpful message | Core 1 | Met | Phases 1, 2 | `tests/test_quickstart_python.py` and `tests/test_quickstart_node.py`, the missing-token cases: the message names `QRYPT_API_KEY`, `.env` and portal.qrypt.com, no request is sent, no trace |
| RQ-05 | ⛔ Deployed site: one path from "get a token" to "first key", language tabs, copy buttons, a stated time target; the URL loads | Core 2 | Owner to do | Phases 1–5 build it; Phase 11 deploys it after the move to GitLab | The site artifact of the CI run; the GitLab Pages URL, opened |
| RQ-06 | Troubleshooting page: 400, 401, 403, 429, 500, 503 as symptom → likely cause → fix, and the common mistakes (`size` is KiB, base64 must be decoded, no loop faster than the rate limit) | Core 2 | Met | Phase 3 | `site/troubleshooting.html`; `tests/test_troubleshooting_page.py` checks a symptom, a cause and a fix for each code, mistake and environment issue |
| RQ-07 | Every documented command runs as written | Core 2, Accept | Met | Phase 5 | `tests/test_documented_commands.py` runs every shell line of the site's pages and `llms-full.txt` as written, against the mock; `pip install` lines are checked (packages installed and declared), not run |
| RQ-08 | Onboarding PRD: problem, personas and jobs-to-be-done, the funnel (landing → token created → first successful call → first key → return within 7 days), a target and a measurement for each stage, scope, out of scope, risks, the tradeoff not made; an engineer can build the instrumentation without a question | Core 3 | Met | Gates 2 and 4, Phase 6 | `PRD.md`; `tests/test_prd.py` checks every section the brief lists, the funnel and its common rules equal to `docs/KEY_METRICS.md` cell for cell, and every illustrative figure labelled an assumption. Its targets wait for the owner's approval |
| RQ-09 | ⛔ Agent-readiness test: only the quickstart URL or its Markdown and the prompt "Generate an AES-256 key using Qrypt quantum entropy in a new project", a fresh environment, 5 runs; success, wall-clock time and failure reason each; revise the docs and repeat; at least 4 of 5 succeed after revision; both rounds logged | Core 4; Benchmarks | Met | Phase 8 | `AGENT_READINESS.md` and `evidence/agent_runs.csv`: round 1 5 of 5, the revision (`7272405`), round 2 5 of 5 against the mock and 5 of 5 against Qrypt (round 2-live); `tests/test_agent_readiness.py` keeps the report equal to the log |
| RQ-10 | ⛔ Ten follow-up items from the agent findings and a review of the first-run experience, each with a RICE score and its evidence | Core 5 | Met | Phase 9 | `BACKLOG.md` and `BACKLOG.csv`: ten items, each with reach, impact, confidence, effort and evidence; `tests/test_backlog.py` checks ten items, the RICE arithmetic, each evidence link and the page's order |

# Edge cases and failure modes

| Id | Requirement | Where in the brief | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-11 | Missing or expired token: a specific, actionable message, no stack trace; the docs cover 401 | Edge cases | Met | Phases 1–3 | `tests/test_quickstart_errors.py`: the 401 message for both snippets, no trace; the page's 401 section |
| RQ-12 | 429 and 403 explained in plain language, the difference between them and what to do; no retry in a tight loop | Edge cases | Met | Phase 3 | `tests/test_quickstart_errors.py`: one request on 429, exit within 1.5 s; the page's 403 and 429 sections and their table |
| RQ-13 | 503 and 500: a clean exit with a "try again shortly" message and a non-zero exit code | Edge cases | Met | Phase 3 | `tests/test_quickstart_errors.py`: 500 and 503 print "try again shortly", exit non-zero, no trace |
| RQ-14 | Impossible to miss that `size` is KiB; the snippet requests only what it needs | Edge cases | Met | Phases 1, 3 | Both programs send `size=1` (the mock records it: `tests/test_quickstart_*.py`); the quickstart page, `llms.txt` and the troubleshooting page's `mistake-size-is-kib` entry state the unit next to `size` |
| RQ-15 | Docs warn against printing, logging or committing keys and against reusing entropy bytes for two keys; the snippets show the safe pattern | Edge cases | Met | Phases 1, 3 | The troubleshooting page's `key-handling` section and `llms.txt`'s rules; both programs take the key from bytes 0-31 and the nonce from bytes 32-43 of one block, and never print it (`tests/test_quickstart_*.py`) |
| RQ-16 | Every factual claim about Qrypt is traceable to the official docs; no superlatives; a claims-to-source table | Edge cases | Met | Phase 5 | `CLAIMS.md` (35 claims: the site's and the PRD's, each quoted from its page with its source); `tests/test_claims.py` fails on a stale quote, an unquoted Qrypt fact or a superlative |
| RQ-17 | First-run environment: a missing runtime version, a missing `.env`, corporate proxy and TLS errors, each with a fix | Edge cases | Met | Phase 3 | `tests/test_quickstart_errors.py`: a refused connection and an untrusted certificate each give a message, not a trace; the page's environment sections |
| RQ-18 | Keyboard only; code readable at 200% zoom; copy buttons with accessible labels | Edge cases | Met | Phases 2, 5 | `tests/test_site_in_a_browser.py` (Playwright, Chromium): tabs by arrow keys and Home, every control reached by Tab with a visible focus ring, copy by Enter, no sideways scroll at 200% zoom; Lighthouse accessibility 100 |

# Benchmarks and AI metrics

| Id | Requirement | Where in the brief | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-19 | Agent time-to-first-key: median at most 10 minutes over the successful runs of the revised round | Benchmarks | Met | Phase 8 | `evidence/agent_runs.csv`, Round 2: median 0.54 minutes over 5 successful runs against the mock, 0.61 against Qrypt (round 2-live) |
| RQ-20 | Site load under 1.5 s p95 on mobile, Lighthouse mobile preset, 10 runs | Benchmarks | Met | Phase 5 | `make lighthouse`: 10 mobile runs, load (Largest Contentful Paint) p95 1,024 ms; `evidence/lighthouse/summary.json`, `runs.csv`; `tests/test_lighthouse_evidence.py` |
| RQ-21 | Lighthouse accessibility at least 95, report committed | Benchmarks | Met | Phase 5 | `evidence/lighthouse/index-run.report.html` and `troubleshooting-run.report.html`: accessibility 100 on every run |
| RQ-22 | Snippet runtime under 3 s end to end against the live API, 5 runs | Benchmarks | Not yet | Phase 7 | `evidence/live_runs.csv` |
| RQ-23 | Agent failure taxonomy: each failed run categorized, with the doc change that addressed it | AI metrics | Met | Phase 8 | `AGENT_READINESS.md`, its taxonomy table, each row with the commit of its fix: no run failed; the one harness misjudgment (`1-2`, fixed in `a9aa446`) is its row, and a test fails the gate on a failed run with no row |
| RQ-24 | Fact-check of AI-drafted content: how many AI-drafted claims had to be corrected | AI metrics | Met | Phase 5 | `CLAIMS.md`, its fact-check: 24 AI-drafted claims checked, 3 verified, 1 relabelled, 20 corrected or dropped |

# Security, code quality and submission

| Id | Requirement | Where in the brief | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-25 | `QRYPT_API_KEY` in `.env` only; `.env` ignored; a committed `.env.example`; no token in screenshots, recordings or agent-run logs | Security | Not yet | Phase 1, Phase 8 | `make gate` (gitleaks); a test that no committed transcript holds a token-shaped string |
| RQ-26 | Generated keys never printed, logged or written to disk | Security | Met | Phases 1, 2, 10 | `tests/test_quickstart_python.py` and `tests/test_quickstart_node.py`: the key's raw, hex and base64 forms are absent from the output, and the run writes no file |
| RQ-27 | Analytics, if used: no cookies or personal identifiers, disclosed on the site | Security | Not yet | Not built (see the plan's "Not doing"); applies only if RQ-40 is built | The plan's reason; revisited only if time is left |
| RQ-28 | Docs versioned in the repo; the site builds from the repo on push | Code quality | Met | Phase 1 | CI run 39350395398 on push of `9fd2119`, green; its `site` job uploaded the `quickstart-site` artifact |
| RQ-29 | PRD, agent-readiness report and backlog in plain language a busy engineering lead reads in 10 minutes | Code quality | Met | Phases 6, 8, 9 | `tests/test_prd.py`, `tests/test_agent_readiness.py` and `tests/test_backlog.py` cap each file at 2,500 words |
| RQ-30 | README: how to run the snippets, build the site and reproduce the agent-readiness test | Code quality | Met | Phase 11 | `README.md`: run the snippets, build the site, reproduce the agent-readiness test; `tests/test_readme_and_ai_usage.py` runs its grader quick-start as written against the mock |
| RQ-31 | `AI_USAGE.md`: the AI tools, what for, the prompts and configuration that shaped the work, and the exact prompt and agent of the readiness test | AI disclosure | Met | Phase 11 | `AI_USAGE.md`: the tools, what each did, the prompts and decisions that shaped the work, and the agent test's exact prompt, command and pinned agent version, held to the harness by `tests/test_readme_and_ai_usage.py` |
| RQ-32 | A repository with README, `AI_USAGE.md`, snippets, site source and CI | Submission | Owner to do | Phase 11 | Built on GitHub; the owner moves it to GitLab and shares it |
| RQ-33 | The deployed site's URL | Submission | Owner to do | Phase 11 | The GitLab Pages URL |
| RQ-34 | `PRD.md`, `AGENT_READINESS.md` (both rounds), `BACKLOG.md`, the claims-to-source table | Submission | Met | Phases 5, 6, 8, 9 | The four files at the repository's root: `PRD.md`, `AGENT_READINESS.md` (round 1, round 2, round 2-live), `BACKLOG.md` with `BACKLOG.csv`, `CLAIMS.md` |
| RQ-35 | Grader quick-start: set a token, run each snippet, see the success line in under 5 minutes | Submission | Not yet | Phase 11 | A timed run from a fresh clone, logged in `evidence/grader_quickstart.md`: 18.1 s against the mock, each README command as written (`tests/test_grader_run.py`); the run against Qrypt waits on the token |
| RQ-36 | A one-line description of at most 120 characters | Submission | Met | Phase 11 | The line under the README's title, 120 characters; `tests/test_readme_and_ai_usage.py` caps it at 120 |
| RQ-37 | A demo video of at most 5 minutes: a fresh run, one troubleshooting path, the PRD's funnel, one agent-readiness run | Submission | Owner to do | Phase 11 | The `generate-demo` skill, which the owner calls |

# Stretch

| Id | Requirement | Where in the brief | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-38 | A plain-Markdown `llms.txt` of the quickstart, linked from the site | Stretch | Met | Phase 4 | `tests/test_llms_txt.py`: the built site holds `llms.txt` (llmstxt.org shape, every rule the snippets follow) and `llms-full.txt` (both snippets word for word, every troubleshooting message); the quickstart page links to it |
| RQ-39 | A third language | Stretch | Met | Phase 10 | Rust: `rust/src/main.rs`, 25 of 25 lines; `make e2e` and CI run it against the mock (`tests/test_quickstart_rust.py`, and every case of `tests/test_quickstart_errors.py`, with the same message as Python and Node); a Rust tab on the site and in `llms-full.txt`. Its 5 live runs wait on the token |
| RQ-40 | Privacy-respecting analytics wired to the observable funnel stages | Stretch | Not yet | Not built (see the plan's "Not doing") | The plan's reason |
| RQ-41 | A competitive teardown of one other security or randomness API's quickstart against the funnel | Stretch | Met | Phase 11 | `evidence/teardown.md`: RANDOM.ORG's API against the five funnel stages, each fact sourced and dated (`tests/test_teardown.py`) |

# Constraints the owner set

| Id | Requirement | Where it is stated | Status | Where | Proof |
|---|---|---|---|---|---|
| RQ-42 | Total live Qrypt use at most 10,240 KiB; everything runs against a mock until the owner has a token | Qrypt Quick Reference; the owner, 2026-10-19 | Not yet | Every phase; the ledger from Phase 7 on | `evidence/live_usage.csv`, totalled by a test that fails at 8,192 KiB |
| RQ-43 | Done before the interview, Wednesday 2026-10-21 at 13:30 CDT | The owner, 2026-10-19 | Not yet | The plan's schedule | The last commit's time |

[^assessment]: The assessment's full text
[^plan]: The plan
