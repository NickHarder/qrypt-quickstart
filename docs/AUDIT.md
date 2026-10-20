---
type: Audit
title: "Audit: Qrypt's first-run path, before any product code"
description: What a first-time developer or agent meets in Qrypt's documented entropy API, and in this repository before its first slice, with a reproduction for each finding and the decision it forces in the plan.
tags: [audit, gate]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:30:00Z }
sources:
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-20, page text sha256 3cbfd11e
  - id: method
    resource: /METHOD.md
    title: "Method: gated, skill-driven delivery"
  - id: plan
    resource: /PLAN.md
    title: The plan
verified:
  - { by: human:nickharder, at: 2026-10-20T21:46:32Z }
approved_sha256: ebfba7b6d64ea11342bb170b94e8a56a222db149cc16d4b5d88c7a7925c148a0
---

# Scope

**Scope line.** Kit v0.21.1 (`.copier-answers.yml`); `make kit-files JSON=1` exited 3 because copier
is not installed, and installing it is the owner's call, so no file was sorted and none was skipped:
all 233 tracked files were in scope, every one scanned (gitleaks over the tree and both commits; the
four lock files through `npm audit` and OSV), and read where the plan's first slices depend on them.
Commit audited: `31537f6`.

As the adjusted ladder says, there is no codebase to audit, so the audit covers the system the
project builds on: Qrypt's first-run path at docs.qrypt.com and the API contract it documents, read
only, with no call to the API.[^method] The five areas ran one after another in one agent, not in
parallel sub-agents: the agent that ran this gate had no tool to start one. No area was dropped;
data quality is read as the quality of the documented contract, profiled by
[`audit/qrypt_docs_profile.py`](audit/qrypt_docs_profile.py).

# Summary

Qrypt's entropy service is one GET with a clear contract, and the page that documents it agrees
with the brief on every fact the snippets need: `size` counts KiB from 1 to 512 and defaults to 1,
both headers are required, six error statuses are listed, and the limit is 30 requests per 10
seconds.[^qrypt-eaas] The audit's profile script confirmed each of these on 2026-10-20 and recorded
the page's hash, so a later run will show whether Qrypt changed it. What matters to the product is
what lies around that contract.

**The examples teach the mistakes the brief scores.** Three of Qrypt's four examples leave out the
`Accept` header that the page itself requires (DQ-01). None checks the status before reading the
body, so any error becomes a stack trace (DQ-02). The Python example writes the token into source
and prints every entropy byte (SEC-03), and two examples fail once their placeholders are filled in
(DQ-03). An agent that falls back on Qrypt's page reproduces these, which makes this project's
quickstart and `llms.txt` the only agent-ready description of the service: Qrypt serves no
`llms.txt`, and its sitemap points at `localhost` (DQ-05).

**The mock carries more weight than it can bear alone.** Qrypt offers no sandbox and documents no
error body, no `Retry-After` and no status for a missing `Accept` (ARCH-01). Whatever the mock does
at those edges is this project's guess, so the snippets must branch on the status code alone, and
the live check must record the real answers. The API's host sits behind Cloudflare, and a
Cloudflare-fronted host refused Python's default client with a 403 that curl and Node did not get
(ARCH-02). If the API's edge behaves the same, the Python snippet fails on first run with a 403 that
the troubleshooting page would blame on the allotment. A named `User-Agent` and one live probe
settle it.

**The token is the one secret, and the agent test puts it in reach.** Each agent-readiness container
holds the live token where the agent can read it, and a token that reaches a transcript as plain
text passes the secret scan untouched (SEC-01, SEC-02). Once pushed, it cannot be removed, only
revoked (CMP-02). The transcripts need an exact-value scrubber with its own test, and a token the
owner revokes after the runs.

**The funnel's second stage has no documented self-service step.** The page says to contact Qrypt
for a token; the brief names a registration portal that the partner notes once saw fail to load
(DQ-04). The owner has no token yet, so every live phase waits on a person, and the PRD should
treat token creation as the stage most likely to lose developers.

**What is fine.** No secret is in the repository or its history; the Python and Node lock files have
no known vulnerability and the Rust crate has no dependencies yet (SEC-05). Local runtimes start in
well under a tenth of a second, so the 3-second target depends on the network round trip to the one
documented region, which only Phase 7 can measure (PERF-01, PERF-04). Smaller gaps: the example env
file does not name the token yet, CI does not run on every push, and "Qrypt SDK" names a different
product an agent may reach for (ARCH-03 to ARCH-05).

# How this changes the plan

| Finding | The decision it forces |
|---|---|
| DQ-01, SEC-03 | Every snippet, command and `llms.txt` sends both headers and reads the token from the environment; the agent-contract eval case fails a program that sends one header, hard-codes the token or prints the key. The claims table records Qrypt's omissions with their source |
| DQ-02, DQ-06 | Each snippet checks the status before the body and checks it decoded at least 1,024 bytes; Phase 3 adds a short `random` to the 200-with-an-odd-body case |
| ARCH-01 | The snippets never parse an error body. The mock marks each answer Qrypt does not document as its own. Phase 7 records the real 401 and the missing-`Accept` answer |
| ARCH-02 | New: each snippet sends a `User-Agent` naming it; Phase 7 adds one request with Python's default client (within its 12 KiB); the troubleshooting page's 403 entry names an edge refusal as a second cause |
| ARCH-03 | The quickstart and `llms.txt` say the entropy service has no SDK and the Qrypt SDK is a separate product; Phase 2's eval case checks for it |
| ARCH-04 | Phase 1 adds `QRYPT_API_KEY` and `QRYPT_API_URL` to the example env file, with a test over every variable a snippet reads |
| ARCH-05 | None: the plan already adds the push trigger in Phase 1 |
| ARCH-06 | The site states each runtime's minimum (Node 20.12 for `process.loadEnvFile`); Phase 1 adds `cryptography` |
| SEC-01, SEC-02, CMP-02 | Gate 3 designs the agent-run sandbox: an exact-value scrubber with a planted-token test before any transcript is committed, and the owner revokes the containers' token after Phase 8 |
| SEC-04 | The troubleshooting page's proxy entry keeps verification on (`SSL_CERT_FILE`, `NODE_EXTRA_CA_CERTS`); a test checks no snippet or page turns it off |
| DQ-04 | The quickstart gives both routes to a token without claiming the portal works; the PRD measures token creation as its own stage, with its loss named as a risk |
| DQ-05 | None new: Phase 4 builds `llms.txt`. The backlog gains a pull request to Qrypt's public docs repository |
| DQ-03 | None for the build; evidence for the backlog |
| DQ-07 | The claims table cites the Qrypt page for each contract fact; no certification claim; "truly random" only as Qrypt's quoted words |
| PERF-01 | None new: Phase 7's five timed runs stand; the site's time target is stated beside the measurement |
| PERF-02 | None new: no retry, exit within 1 s on 429; agent runs strictly one after another |
| PERF-03, PERF-04, SEC-05 | None |
| CMP-01 | Phase 1's site test checks the built site holds no file from `docs/` |
| CMP-03 | None new: the Phase 7 ledger is the only usage record, so every live call goes through it |
| CMP-04 | `AI_USAGE.md` lists each provider and what it received; the owner picks the eval model before the first paid recording |

# Security

Full findings: [the security area](audit/security.md).

| Id | Severity | Finding | Response |
|---|---|---|---|
| SEC-01 | high | The agent test puts the live token where the agent can read it | Revocable token, exact-value scrub, logged as a failure category |
| SEC-02 | medium | The secret scan misses a bare token in a transcript | Exact-value scrubber with a planted-token test |
| SEC-03 | high | Qrypt's examples put the token in source and print every entropy byte | Env-only token, success line only, an eval case checks both |
| SEC-04 | medium | Qrypt says nothing about proxies or certificate errors | Troubleshooting fix that keeps verification on, and a test |
| SEC-05 | info | No secret in the repository; no known vulnerability in its locks | Run again when dependencies are added |

# Performance

Full findings: [the performance area](audit/performance.md).

| Id | Severity | Finding | Response |
|---|---|---|---|
| PERF-01 | medium | One documented region; the 3-second target rests on an unmeasured round trip | Phase 7 measures it before the site states it |
| PERF-02 | medium | 30 requests per 10 s per token, no `Retry-After` | No retry; agent runs one at a time |
| PERF-03 | info | The answer to `size=1` is about 1.4 KB of JSON | None |
| PERF-04 | info | Runtimes start in under 0.07 s | Phase 1 times the snippet against the mock |

# Architecture

Full findings: [the architecture area](audit/architecture.md).

| Id | Severity | Finding | Response |
|---|---|---|---|
| ARCH-01 | high | One GET and no sandbox: the mock's edges are this project's guesses | Status codes only; the mock marks its guesses; Phase 7 records the real answers |
| ARCH-02 | medium | Cloudflare fronts the API; its 403 reads like the allotment 403 | Named `User-Agent`, one live probe, a second cause on the 403 entry |
| ARCH-03 | medium | "Qrypt SDK" is a different product | Say so on the quickstart and in `llms.txt`; an eval case |
| ARCH-04 | medium | The example env file names neither key | Phase 1 adds both, with a test |
| ARCH-05 | medium | CI does not run on every push | Already in Phase 1 |
| ARCH-06 | low | Minimum runtimes and missing libraries | State the minimums; add `cryptography`; pin the crates |

# Data quality

Full findings and the profile's output: [the data-quality area](audit/data-quality.md).

| Id | Severity | Finding | Response |
|---|---|---|---|
| DQ-01 | high | Three of four examples leave out the required `Accept` header | Both headers everywhere; an eval case |
| DQ-02 | medium | No example checks the status before the body | Status first; Phase 3 tests each code |
| DQ-03 | low | Two examples fail as written | Backlog evidence; every site command runs in CI |
| DQ-04 | high | No self-service path to a token on the page | Both routes on the site; stage 2 measured as a risk |
| DQ-05 | medium | No `llms.txt` or `robots.txt`; the sitemap points at `localhost` | This project's `llms.txt`; a backlog pull request to Qrypt |
| DQ-06 | medium | Allotment unstated; the answer's size "should match" | The ledger; check the decoded length |
| DQ-07 | info | The page agrees with the brief; it makes no certification claim | Claims table cites the page |

# Compliance

Full findings: [the compliance area](audit/compliance.md).

| Id | Severity | Finding | Response |
|---|---|---|---|
| CMP-01 | medium | The brief folder is private; the site is to be public | Site built from `site/` only, and a test |
| CMP-02 | medium | A committed transcript is kept for good | Scrub before writing; revoke after Phase 8 |
| CMP-03 | low | Qrypt publishes no usage meter | Every live call through the ledger |
| CMP-04 | low | What each model call sends, and to whom | `AI_USAGE.md` lists each; no brief file in a prompt |

# Test-data defense: the mock

The project's test data is synthetic: the mock server the plan puts in `src/qrypt_quickstart/`,
which answers by token (`mock-200`, `mock-401`, `mock-403`, `mock-429`, `mock-500`, `mock-503`) and
records each request.[^plan] It does not exist yet; this is what it must hold to.

- **Why it is safe.** It holds no real token and no real entropy, and it listens on `localhost`
  only. Its tokens are labels, not secrets, so a log or a transcript that shows one leaks nothing.
- **How it is reproduced.** Its answers are fixed by token, and its 200 returns bytes from a fixed
  seed, so every test run sees the same body; `make e2e` starts it, runs each snippet, and stops it.
- **Which of its flaws become product failure modes.** Every answer Qrypt does not document is a
  guess (ARCH-01): the 400 for a missing `Accept`, any error body, the headers of a 429. A snippet
  tuned to the mock's guesses could pass CI and fail live. Fixed bytes cannot show a decode bug that
  only some inputs trigger, so a test also runs the snippet on a 200 whose bytes come from
  `os.urandom`.
- **What it cannot show.** Latency and the 3-second target (PERF-01), the edge in front of the API
  (ARCH-02), the real 401 and allotment answers, and how an agent behaves against the real service.
  Phase 7 and the agent rounds cover these, and the agent-readiness report says which rounds ran
  against the mock if the token does not come in time.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^method]: "Method: gated, skill-driven delivery"
[^plan]: The plan
