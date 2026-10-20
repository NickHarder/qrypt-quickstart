---
type: Plan
title: "Plan: Qrypt quickstart, onboarding PRD and agent-readiness test"
description: How the Qrypt Developer Quickstart take-home gets built by 2026-10-21 13:30 CDT, as a tracer bullet and ten vertical slices, with the owner's decisions, the live-entropy budget and the points where the owner acts.
tags: [plan, brief]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T01:18:04Z }
sources:
  - id: assessment
    resource: brief/assessment-text.md
    title: The assessment's full text
  - id: review
    resource: brief/research-review.md
    title: What to check in the research before building on it
  - id: deliverables
    resource: DELIVERABLES.md
    title: Deliverables
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-19
  - id: gitlab-pages-access
    resource: https://docs.gitlab.com/user/project/pages/pages_access_control/
    title: GitLab Pages access control, read 2026-10-19
---

# Context

Qrypt sells quantum entropy as one REST endpoint. A developer arriving for the first time has to
work out the headers, the unit of `size` and the base64 decoding before a byte becomes a key, and
there is no SDK in most languages. The assessment asks the Product Manager candidate to own that
first run: quickstart code in two languages, a deployed site with troubleshooting, an onboarding
PRD with a measurable funnel, and a test showing an AI coding agent can follow the docs.[^assessment]
Every requirement has an id and a row in [the deliverables](DELIVERABLES.md).[^deliverables]

**Deadline.** The interview is on Wednesday 2026-10-21 at 13:30 CDT (18:30 UTC). The work freezes
at 12:00 CDT (17:00 UTC). The plan starts on Monday 2026-10-19 at 19:00 CDT (00:00 UTC on the 20th).

## Verified facts (2026-10-19)

| Fact | Evidence |
|---|---|
| The gate is green with the kit only: 4 lint, 2 test and 2 eval checks, secrets clean, in 5 s | `make gate` → `gate: green in 5s` |
| CI runs on pull requests, `v*` tags and manual runs, not on a plain push; the brief asks for every push | `.github/workflows/ci.yml:13-17` |
| Python 3.12 in `.venv`, Node 22 on this machine (the project pins 26), Rust 1.99.1 in `rust/`, gitleaks 8.28; no Lighthouse and no semgrep installed; Chromium at `/opt/pw-browsers` | `.venv/bin/python --version`, `node --version`, `cd rust && rustc --version`, `command -v` |
| The eval suite's model is `example-model`, and no model key is known to be set | `evals/thresholds.yaml:7`; `.env` is not read by agents |
| Qrypt's docs name both headers, `Accept: application/json` and `Authorization: Bearer`; the curl, Python and PowerShell examples send only the second; the JavaScript example sends both | docs.qrypt.com/eaas/, read 2026-10-19[^qrypt-eaas] |
| `size` is KiB, 1 to 512, default 1; rate limit 30 requests per 10 s per token (429); a per-period allotment whose amount is not stated (403); 503 is "not enough supply" | The same page[^qrypt-eaas] |
| The EaaS page makes no claim about NIST SP 800-22 or the ESV certificate | The same page[^qrypt-eaas] |
| `https://docs.qrypt.com/llms.txt` returns 404 | `curl -o /dev/null -w '%{http_code}'` → `404` |
| Python's standard library has no AES-GCM, so the Python snippet needs `cryptography`; Node 18 and later have `fetch` and `crypto` built in | Python and Node documentation |
| GitLab Pages on the Free tier can serve a private project's site to everyone | GitLab docs, read 2026-10-19[^gitlab-pages-access] |
| No Qrypt token yet | `HANDOFF.md`, "Open, for the owner" |

# Decisions locked with the owner (2026-10-19)

| Decision | Choice |
|---|---|
| Repository | Private (settled before kickoff) |
| Languages | Python at the root, Node/TypeScript in `web/`, Rust in `rust/` as the stretch third language (settled before kickoff) |
| Layers | Evals, demo video, semgrep in CI, GitHub Actions (settled before kickoff) |
| Interview time zone | "US Central (CDT)" |
| Host and CI | "build on github private now and then we will migrate to gitlab once done. dont worry about the pages just get the artifacts and ci pipeline working in github. it will be easy to migrate to gitlab at the very end" |
| Agent for the readiness test | "Claude Code, fresh container (Recommended)": `claude -p` with the brief's prompt, each run in a new Docker container with only `.env` seeded, the token scrubbed from the transcripts |
| Reading Qrypt's docs | "Yes, docs.qrypt.com read-only (Recommended)": pages under `/eaas` and `/sdk`, and `/llms.txt`; no API call and no token |
| Live use | At most 10,240 KiB; everything runs against a mock until the owner has a token (the owner's kickoff message) |

## Decisions kickoff made, each reversible

- **The brief's named files live at the root**: `PRD.md`, `AGENT_READINESS.md`, `BACKLOG.md`
  (with `BACKLOG.csv`), `CLAIMS.md` (the claims-to-source table) and `AI_USAGE.md`. The brief
  names them and a grader looks for them there; each goes on the list in
  `docs/references/outside-the-bundle.md` with the grader as its reader. They draw on the gate
  artifacts under `docs/` (`USERS.md`, `KEY_METRICS.md`), and a test keeps the PRD's funnel equal to
  the metrics. Reverse by moving them under `docs/` and linking from the README.
- **Where the code lives.** The snippets a developer copies are single files:
  `quickstart/python/quickstart.py`, `quickstart/node/quickstart.mjs` and the Rust crate's
  `rust/src/main.rs`. The mock server and the site builder are Python, in the package
  (`src/qrypt_quickstart/`); the site's pages are HTML with include lines, in `site/`. The builder
  was planned in TypeScript; the tracer bullet moved it (deviation DV-05 in
  `docs/ARCHITECTURE.md`). Evidence (CSV logs, Lighthouse reports, transcripts)
  goes in `evidence/`.
- **One source for each snippet.** The site, `llms.txt` and the tests all read the same snippet
  file, so the page cannot show code that CI did not run.
- **The Node snippet is plain JavaScript** (`.mjs`), type-checked by `web/`'s `tsc` through JSDoc
  (`checkJs`), so a developer runs it with no build step.
- **The snippets follow the kit's code rules** (names, assign once, types, doc comments), which add
  no counted line, since comments and imports are not counted. Where a rule and the 25-line limit
  cannot both hold, the limit wins, and the exception is written in the language's rule document
  with its reason. This settles item C10 of the review.
- **The mock is chosen by `QRYPT_API_URL`**, which defaults to the live endpoint. The mock answers by
  token (`mock-200`, `mock-401`, `mock-403`, `mock-429`, `mock-500`, `mock-503`) and records each
  request, so tests can check `size=1` and the headers.
- **The mock does not invent Qrypt's behavior.** It answers 400 to a request without `Accept`, and
  that answer is marked as the mock's strictness, not Qrypt's documented behavior, until the live
  check (Phase 7) records what Qrypt does. This settles item D1 of the review.
- **CI runs on every push.** `ci.yml` gains a `push` trigger for every branch, and the comment that
  says otherwise changes with it. The brief asks for both, and pushes are rare enough here.
- **Round 1 of the agent test runs on the docs as built, not on a deliberately weakened draft.** The
  blueprint proposed a weak Round 1 to make the revision look larger; that would misstate the
  result. If Round 1 already passes, the revision fixes what its runs show and the report says so.
- **The agent gets the Markdown, not a URL**, until the site is deployed at the very end. The brief
  allows "the quickstart URL (or its Markdown)".
- **Evals score what a model writes from the docs.** A case gives a model the quickstart's Markdown
  and the brief's prompt, and scores the program it writes: `size=1`, both headers, the token read
  from the environment, the key never printed, no invented SDK. Recorded once, replayed for $0 in
  the gate. Each failure in the agent rounds becomes a regression case.

## The research review, settled

[The review](brief/research-review.md) lists what to check in the research.[^review] Each item is
settled here; the corrected claims count toward the fact-check figure of RQ-24.

| Item | Settled as |
|---|---|
| D1 (missing `Accept` gives 401, 400 or 406) | Unknown. The docs require the header and name no status for its absence. The site says to send both headers and claims no status, until Phase 7 records one with a single call of at most 1 KiB |
| D2 (`QRYPT_TOKEN`) | Corrected: `QRYPT_API_KEY` everywhere, as the brief says |
| D3 (`byte_count: 64`, `"64kb"`) | Corrected: `size` is an integer count of KiB, and the snippet sends `size=1` |
| D4 (PowerShell and cURL snippets) | Corrected: Python and Node, with Rust as the third; curl appears only as the one-line smoke test the brief gives |
| D5 (two event specs for stage 3) | One spec, written in `docs/KEY_METRICS.md` (Gate 4) and shown in `PRD.md` |
| D6 (effort in months against person-weeks) | One unit: person-weeks |
| D7 (Round 2 "typically" 5/5 under 2 minutes) | Dropped: a number goes in only after the run that produces it |
| D8 (backlog evidence citing Round 2 before any run) | Dropped: the backlog is scored after both rounds (Phase 9) |
| `Accept` missing from the docs' examples | Verified on 2026-10-19 for curl, Python and PowerShell; the JavaScript example includes it |
| `llms.txt` returns 404 | Verified on 2026-10-19 |
| `size` defaults to 1 | Verified on 2026-10-19 |
| NIST SP 800-22 and the ESV certificate | Not on the EaaS page. Left off the site unless Phase 5 finds them on a page Qrypt or NIST publishes, and then cited to it |
| "The portal frequently fails to load" | One observation in the partner notes. Not stated on the site; the troubleshooting page says to ask Qrypt for a token if the portal does not load |
| Lighthouse's "Agentic Browsing" audit; qseed's 48 bytes; rng-tools | Not used: nothing on the site depends on them |
| The 45-minute baseline and the 25% activation | Written as the brief's own assumptions, everywhere they appear |
| "Over 90% of the reduction", "6 to 8 engineering weeks", the industry benchmarks | Dropped: no source |
| C1–C3 (a network error or an odd body gives a stack trace or a panic) | A test for each, in Phase 3 (Python, Node) and Phase 10 (Rust) |
| C4, C5 (the `.env` readers) | Each snippet uses its platform's `.env` support (`python-dotenv`, Node's `process.loadEnvFile`, `dotenvy` in Rust); a test covers comments, `export` and quotes |
| C6, C7 (ureq versions, `set_var` is `unsafe`) | Phase 10 pins the crate's versions and sets no environment variable |
| C8 (`assert` skipped under `python -O`) | The check that the decrypted text matches is an `if`, and a test runs the snippet under `-O` |
| C9 (line counts never measured) | `make check C=snippet-lines` counts them in the gate |
| C10 (the kit's rules against the 25-line limit) | Settled above |
| The layout question | Settled above: the brief's files at the root |

# Invariants

Never cut, whatever happens to the schedule:

1. The token is never committed, printed, logged, or shown in a recording or a transcript.
2. A generated key is never printed, logged or written to disk, and the key and the nonce never
   share entropy bytes.
3. Live Qrypt use stays at or under 10,240 KiB in total; the work stops live calls at 8,192 KiB.
   Nothing calls the live API before the owner's token is in `.env`.
4. Two languages, each at most 25 lines, run in CI against the mock for 200, 401, 429 and 503.
5. Both agent rounds are logged as they happened, failures included; no number is written before
   the run that produces it.
6. Every factual claim about Qrypt on the site is in the claims-to-source table.
7. The PRD's funnel has a target and a measurement for each of its five stages.
8. `make gate` is green at every commit.

# Phases

The ladder of `docs/METHOD.md` comes first: Gates 1 to 4 tonight, one lean run each, then the
build. Times are CDT. The phases run in this order; the live phases wait on the token and the rest
does not.

## Gates 1–4: audit, personas, architecture, key metrics

Monday 2026-10-19, 19:00 to 23:30 CDT.

- **Files:** `docs/AUDIT.md` (the first-run audit of Qrypt's docs and API, there being no
  codebase), `docs/USERS.md`, `docs/ARCHITECTURE.md`, `docs/KEY_METRICS.md` and `docs/metrics/`.
- **Tests and eval cases:** none; the gate checks the bundle and the trace.
- **Verify:** `make gate`, `make trace`.
- **Effort:** 4.5 hours. **Cost:** $0 (this session).

## Phase 1: tracer bullet, the Python quickstart end to end

Tuesday 2026-10-20, 07:00 to 10:00 CDT.

**The one feature:** a developer runs the Python snippet with a token and sees the success line.
It crosses every layer: input (`.env`), logic (decode, slice 32 bytes, AES-GCM round trip), the
outside call (the mock, standing in for Qrypt), output (the success line, never the key), one test,
one eval case, the gate, CI on push, and the deploy path as far as the owner wants it now (the
site built and uploaded as a CI artifact).

- **Tests and eval cases, written first:**
  - `tests/test_quickstart_python.py`: against the mock, exit 0 and the success line; the key, its
    hex and its base64 absent from the output; the request was `size=1` with both headers; no file
    written; with no token, a non-zero exit and a message that names where to get a token and how
    to set it.
  - `tests/test_snippet_lines.py`: the snippet has at most 25 counted lines.
  - `tests/test_mock_server.py`: the mock's answers by token.
  - Eval case `evals/cases/agent-contract/`: a model given the quickstart page and the brief's
    prompt writes a program that sends `size=1` and both headers, reads the token from the
    environment and does not print the key.
- **Files:** `quickstart/python/quickstart.py`, `src/qrypt_quickstart/mock_server.py`,
  `site/index.html` (the get-a-token-to-first-key path with the Python block and its copy button),
  `src/qrypt_quickstart/site_builder.py`, `.github/workflows/ci.yml` (the push trigger, a job running the snippets
  against the mock, a job building the site and uploading it), `scripts/checks.conf`
  (`snippet-lines`, `e2e`), `pyproject.toml` (`cryptography`, `python-dotenv`),
  `docs/references/outside-the-bundle.md` (`quickstart/`, `site/`, `evidence/`).
- **Verify:** `make e2e` (the proving command: starts the mock, runs the snippet, builds the site and
  checks that its code block is the snippet's file), then `make gate`, then the CI run of the push.
- **Effort:** 3 hours. **Cost:** about $0.05, to record the eval case.

**You act:** put a model key in `.env` and approve recording the first eval case, about $0.05 (paid run)

**You act:** approve the first push of the branch, which starts CI (push)

## Phase 2: the Node quickstart and the language tabs

Tuesday 2026-10-20, 10:00 to 11:30 CDT.

- **Tests and eval cases, written first:** `tests/test_quickstart_node.py`, the same cases as
  Phase 1 against the same Python mock (moved from vitest so one mock serves every language); the
  line count; a static test of the tabs' ARIA structure and the copy buttons' labels. The
  Playwright test that drives the tabs and copy buttons by keyboard moves to Phase 5, which installs
  Playwright. An eval case (AC-02): asked for a Node program, the model uses built-in `fetch` and
  `crypto` and installs no Qrypt package.
- **Files:** `quickstart/node/quickstart.mjs`, `site/index.html`, `site/copy.js` (tabs, copy
  buttons), `web/tsconfig.json` (`checkJs` over the snippet), `quickstart/biome.json` (Biome over
  the snippet).
- **Verify:** `make e2e`, `make gate`.
- **Effort:** 1.5 hours. **Cost:** about $0.05.

## Phase 3: every error, and the troubleshooting page

Tuesday 2026-10-20, 11:30 to 14:00 CDT.

- **Tests and eval cases, written first:** for each snippet, against the mock: 400, 401, 403, 429,
  500, 503, a refused connection, a certificate it cannot verify, and a 200 with an unexpected body.
  Each exits non-zero with its own actionable message and no traceback; 429 exits within 1 s after
  one request; 500 and 503 say "try again shortly". The Python snippet also passes under
  `python -O`. A test that the troubleshooting page has a symptom, a likely cause and a fix for
  each code, each common mistake and each environment issue. An eval case: given the page and a
  429, the model says to wait and not to loop, and tells 429 from 403.
- **Files:** both snippets, `site/troubleshooting.md`, the mock's error routes.
- **Verify:** `make e2e`, `make gate`.
- **Effort:** 2.5 hours. **Cost:** about $0.05.

## Phase 4: the agent-readable quickstart

Tuesday 2026-10-20, 14:00 to 15:00 CDT.

- **Tests and eval cases, written first:** a test that the built site has `/llms.txt` and
  `/llms-full.txt`, that the quickstart links to them, and that their rules (the headers, `size=1`
  in KiB, no SDK, never print the key) match the snippets. An eval case: given only `llms.txt`, the
  model writes a program that passes the Phase 1 checks.
- **Files:** `site/llms.md`, the builder's `llms.txt` and `llms-full.txt` output.
- **Verify:** `make e2e`, `make gate`.
- **Effort:** 1 hour. **Cost:** about $0.05.

## Phase 5: claims, accessibility and speed

Tuesday 2026-10-20, 15:00 to 17:00 CDT.

- **Tests and eval cases, written first:** every claim on the site carries a claim id found in
  `CLAIMS.md`, with its source; no superlative from a listed set ("unbreakable", "perfectly secure"
  and others) appears; every shell block on the site runs as written against the mock; Playwright
  at 200% zoom shows no clipped code; Lighthouse's mobile preset, 10 runs: accessibility at least
  95 and load p95 under 1.5 s.
- **Files:** `CLAIMS.md` (with the count of corrected AI-drafted claims), `site/` pages,
  `web/scripts/lighthouse.ts`, `evidence/lighthouse/`, a CI job for Lighthouse.
- **Verify:** `make e2e`, `make gate`, `npm --prefix web run lighthouse`.
- **Effort:** 2 hours. **Cost:** $0.

**You act:** approve adding Lighthouse and Playwright as `web/` dev dependencies (install)

## Phase 6: the onboarding PRD

Tuesday 2026-10-20, 17:00 to 19:00 CDT.

- **Tests and eval cases, written first:** a test that `PRD.md` has each section the brief lists;
  that each funnel stage has an event, a trigger, a payload, a join key, a formula and a target
  equal to `docs/KEY_METRICS.md`; that every illustrative number is labelled an assumption; and
  that it stays under 2,500 words.
- **Files:** `PRD.md`.
- **Verify:** `make gate`.
- **Effort:** 2 hours. **Cost:** $0.

**You act:** read the PRD and approve its funnel targets and its tradeoff (approval)

## Phase 7: the live check

As soon as the token is in `.env`, and no later than Tuesday 2026-10-20 at 19:00 CDT. About
30 minutes.

- **Tests and eval cases, written first:** a test that totals `evidence/live_usage.csv` and fails
  at 8,192 KiB; a test that no committed file holds a token-shaped string.
- **What runs live:** each snippet 5 times, timed (10 KiB); the site's curl smoke test once (1 KiB);
  one request without `Accept` to record Qrypt's answer (at most 1 KiB); one request with a bad
  token to see the real 401 (0 KiB).
- **Files:** `evidence/live_runs.csv`, `evidence/live_usage.csv`, `scripts/live_check.py`.
- **Verify:** `make live-check` (prints the runtimes and the running total), `make gate`.
- **Effort:** 0.5 hours. **Cost:** $0, 12 KiB of entropy.

**You act:** put the Qrypt token in `.env` as `QRYPT_API_KEY` (or ask the program contact for one) (access)

**You act:** approve the live check, 12 KiB of the 10,240 KiB budget (paid run)

## Phase 8: the agent-readiness test, two rounds

Tuesday 2026-10-20, 19:00 to 22:00 CDT.

- **Tests and eval cases, written first:** a test that `evidence/agent_runs.csv` has 5 runs per
  round, each with a time, a result and a failure category; that the success rate and the median
  in `AGENT_READINESS.md` equal the CSV's; and that no transcript holds a token. Each Round 1
  failure becomes a regression eval case before its doc fix.
- **How it runs:** `scripts/agent_run.sh` starts a new Docker container per run with Claude Code, an
  empty project, the token in `.env` only and the quickstart's Markdown, and gives it the brief's
  prompt word for word. It records the start, the end, whether the program printed a success line
  with a working key, the entropy requested, and the transcript, with the token scrubbed. Round 1,
  then the doc revision as its own commit, then Round 2.
- **Files:** `scripts/agent_run.sh`, `evidence/agent_runs.csv`, `evidence/transcripts/`,
  `AGENT_READINESS.md`, the revised `site/` pages.
- **Verify:** `make gate`; the counts in `AGENT_READINESS.md` against the CSV.
- **Effort:** 3 hours. **Cost:** $0 on the owner's Claude subscription (about $15 if billed per
  token through an API key: 10 runs at about $1.50); at most 640 KiB of entropy expected
  (10 runs × 64 KiB), the ledger stopping the work at 8,192 KiB in total.

**You act:** give the containers Claude Code's login (`claude setup-token`) or an API key, and approve both rounds, $0 to $15 and up to 640 KiB (paid run)

## Phase 9: the backlog

Tuesday 2026-10-20, 22:00 to 23:00 CDT.

- **Tests and eval cases, written first:** a test that `BACKLOG.csv` has ten items, each with reach,
  impact, confidence, effort in person-weeks and a RICE score that equals its arithmetic, a link to
  its evidence (a run, an audit finding, a page of Qrypt's docs), and that `BACKLOG.md` lists them
  in score order.
- **Files:** `BACKLOG.md`, `BACKLOG.csv`.
- **Verify:** `make gate`.
- **Effort:** 1 hour. **Cost:** $0.

## Phase 10: the Rust quickstart (stretch)

Wednesday 2026-10-21, 07:00 to 08:30 CDT.

- **Tests and eval cases, written first:** `rust/tests/quickstart.rs`, the Phase 1 and Phase 3
  cases against the mock, no panic and no backtrace on any error; the line count.
- **Files:** `rust/src/main.rs`, `rust/Cargo.toml` (versions pinned), a Rust tab on the site.
- **Verify:** `make e2e`, `make gate`; 5 live runs, timed (5 KiB).
- **Effort:** 1.5 hours. **Cost:** $0, 5 KiB.

## Phase 11: the submission

Wednesday 2026-10-21, 08:30 to 12:00 CDT.

- **Tests and eval cases, written first:** a test runs every shell block of `README.md` against the
  mock; a test that the one-line description is at most 120 characters.
- **Files:** `README.md` (the grader quick-start, how to build the site, how to reproduce the agent
  test), `AI_USAGE.md` (tools, uses, the prompts that shaped the work, the agent test's exact prompt
  and agent), `evidence/grader_quickstart.md` (a timed run from a fresh clone, under 5 minutes),
  `evidence/teardown.md` (the competitive teardown, stretch), the demo video (`generate-demo`),
  `HANDOFF.md` (the steps of the move to GitLab).
- **Verify:** `make gate`; the timed grader run; the demo's draft at $0 (`make demo-draft`).
- **Effort:** 3.5 hours. **Cost:** $0 (Kokoro voice).

**You act:** call `generate-demo`, record the product footage with no token on screen, and approve the cut (creative call)

**You act:** move the repository to GitLab, turn on Pages with access set to "Everyone", and check the URL loads (deploy)

**You act:** submit the repository, the site URL and the video on the portal (approval)

# Cut order

If time runs short, cut from the top:

1. Privacy-respecting analytics (RQ-40): not built in any case; see below.
2. The competitive teardown (RQ-41).
3. The Rust quickstart (RQ-39), Phase 10.
4. `llms-full.txt`; `llms.txt` stays.
5. The PRD's risks and scope sections shrink to tables.
6. Lighthouse in CI; the 10 local runs and the committed report stay.
7. If the token has not come by Tuesday 2026-10-20 at 18:00 CDT: run both agent rounds against the
   mock, with the agent given the mock's URL, and say so in `AGENT_READINESS.md` and the PRD; run
   the live check and one live round when the token comes, if it comes before the freeze.

The invariants are never cut.

# Budget

| Phase | Paid model runs | Live entropy |
|---|---|---|
| Gates 1–4 | $0 (this session) | 0 KiB |
| 1–4 | About $0.20 in all: four eval cases recorded once each | 0 KiB (mock) |
| 5, 6 | $0: docs/brief/assessment-text.md, no model calls | 0 KiB |
| 7 | $0 | 12 KiB |
| 8 | $0 on the owner's subscription, about $15 by API key; about $0.50 to record the regression cases | Up to 640 KiB expected |
| 9 | $0: no model calls | 0 KiB |
| 10 | $0 | 5 KiB |
| 11 | $0 (Kokoro voice) | Up to 10 KiB for the demo's fresh run |
| **Total** | **About $0.70 to $16** | **About 670 KiB of 10,240; hard stop at 8,192** |

# Verification

```bash
make gate                    # everything a push must pass, offline, $0
make e2e                     # the mock, every snippet, the site built, its code equal to the snippets
make check C=snippet-lines   # each snippet at most 25 counted lines
make trace                   # the north star down to the eval cases
make live-check              # live: each snippet 5 times, timed, with the running KiB total
npm --prefix web run lighthouse   # 10 mobile runs: accessibility and load p95
```

And the CI run of the last push, green; `AGENT_READINESS.md` with both rounds; the GitLab Pages URL
loading, after the owner's move.

# Not doing, and why

- **No SDK and no package.** The brief suggests "no full SDK this quarter" as the tradeoff; one
  endpoint needs only a request, and an SDK would add a release and a maintenance cost the
  quickstart does not need. The PRD argues it.
- **No PowerShell or curl "snippet"** beyond the one-line smoke test: the brief's languages are
  Python, Node, Go, Rust and C++.
- **No analytics (RQ-40).** It needs a deployed site to observe, and the site deploys only after the
  move to GitLab, minutes before the freeze. The PRD specifies the funnel's events so it can be
  built next.
- **No deploy before the move to GitLab**, by the owner's decision. CI builds the site and keeps it
  as an artifact on every push.
- **No weakened Round 1.** Round 1 tests the docs as built; see the decisions above.
- **No NIST or ESV claim on the site** unless a Qrypt or NIST page backs it.
- **No live call before the token**, and none beyond the budget above.

[^assessment]: The assessment's full text
[^review]: What to check in the research before building on it
[^deliverables]: Deliverables
[^qrypt-eaas]: Qrypt Quantum Entropy documentation, read 2026-10-19
[^gitlab-pages-access]: GitLab Pages access control, read 2026-10-19
