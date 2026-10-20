---
type: Architecture
title: "Architecture: snippets, mock, site builder, agent harness and CI"
description: How the Qrypt quickstart is built from five small parts, where the token and the key may and may not go, what each dependency's failure looks like to the user, and the tracer bullet that proves the design first.
tags: [architecture, gate]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:30:43Z }
sources:
  - id: audit
    resource: /AUDIT.md
    title: "Audit: Qrypt's first-run path"
  - id: users
    resource: /USERS.md
    title: "Users: who the Qrypt quickstart serves, and when"
  - id: plan
    resource: /PLAN.md
    title: The plan
  - id: deliverables
    resource: /DELIVERABLES.md
    title: Deliverables
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
  - id: ci
    resource: ../.github/workflows/ci.yml
    title: The CI workflow as the kit rendered it
---

# How to read this draft

This is Gate 3, kept short as [the method](METHOD.md) asks: five parts and no more. It draws on
[the audit](AUDIT.md), [the users](USERS.md) and [the plan](PLAN.md). Persona fields that
[the users](USERS.md) leaves open for the owner are treated, by the owner's instruction of
2026-10-20, as **assumed for the assessment, not researched**: nothing here depends on them, and
none is filled in. Sales has no persona; its need is the funnel definition of UC-04.

Two decisions are settled here and **flagged for the owner**: the agent-test token (SEC-01) and
the edge probe (ARCH-02). Each has its block below.

# 1. Summary

The product is five small parts with no server of its own: the **snippets** a developer copies,
a **mock** of Qrypt's one endpoint, a **site builder** that turns Markdown and the snippet files
into a static site and `llms.txt`, an **agent harness** that runs Claude Code in fresh containers,
and **CI** that runs all of it on every push. No part makes a model call at run time, and none
stores data beyond the evidence files the plan commits.[^plan]

**One source for each snippet** is the decision everything else leans on. The site, `llms.txt`,
the tests and CI all read the same file under `quickstart/`, so a page cannot show code that CI did
not run. The cost is that a snippet cannot be tuned for display; the 25-line limit already forces
it to be plain.[^plan]

**The mock is the only test double, and it is a guess at the edges.** Qrypt offers no sandbox and
documents no error body, no `Retry-After`, and no status for a missing `Accept` (ARCH-01).[^audit]
So the snippets branch on the status code alone and never parse an error body. The mock answers
by token, records each request, and marks every answer Qrypt does not document as its own. The
live check of Phase 7 is the one place reality corrects it.

**The token crosses three boundaries, and each has an enforcer.** In the developer's process the
snippet reads it from the environment and never prints it; tests check the output. In the repository
gitleaks and an exact-value scrubber keep it out of every commit. In the agent containers, which
must hold it because the brief's program reads `.env`, it is a token the owner revokes after Phase
8, and each transcript is scrubbed by the harness before it touches disk (SEC-01, flagged). The
tradeoff is honest: the model provider may still see the token if an agent opens `.env`; revocation,
not prevention, bounds that.

**Qrypt's API sits behind Cloudflare**, whose 403 reads like Qrypt's allotment 403 (ARCH-02). Each
snippet sends a `User-Agent` naming it, and Phase 7 sends one bad-token request with Python's default
client, which costs no entropy and shows whether the edge refuses that client (flagged).

**Failure is a message, never a stack trace or a loop.** Every status, a refused connection, a
certificate error and a 200 with an odd body each give their own line and a non-zero exit. There is
no retry: a 429 exits within a second, because a retry would teach the loop the brief forbids.[^assessment]

**Speed comes from leaving things out.** The snippet makes one request for 1 KiB; the site is
static, with a few lines of script for tabs and copy buttons and no analytics. The round trip and
the edge are measured once, live, in Phase 7.

**The tracer bullet is the Python quickstart end to end**: `.env`, snippet, mock, success line,
test, eval case, gate, CI on push, and the site built as an artifact, proved by `make e2e`. Node,
errors, `llms.txt`, claims, the PRD, the live check, the agent rounds, the backlog, Rust and the
submission follow as slices. Rust and the teardown are cut first; the token and key invariants,
the ledger and the scrubber are never cut.

# 2. Trust boundaries

| Boundary | What crosses it | What must not | Who enforces it |
|---|---|---|---|
| Developer's `.env` → snippet process | The token, read once from the environment | The token or the key into output, a log or a file | The snippet's code; the Phase 1 test checks the output for the key, its hex and its base64, and that no file is written |
| Snippet → Qrypt (Cloudflare edge, then the API) | One `GET` with `size=1` and the token, over verified TLS | A request with verification off, or more than 1 KiB | The runtime's default TLS; a test that no snippet or page turns verification off (SEC-04); Qrypt enforces the token, the rate and the allotment |
| Snippet → mock | The same request, to `localhost` | Any real token or real entropy | The mock listens on `localhost` only and accepts only its `mock-*` labels |
| Repository → public site | The pages in `site/` and the snippet files | Anything from `docs/`, above all `docs/brief/` (CMP-01) | The builder reads `site/` and `quickstart/` only; a test checks the built site holds no file from `docs/` |
| Owner's machine → agent container | The revocable token in the container's `.env`, the quickstart Markdown, the prompt | The owner's own `.env`, the repository, any other key | The harness script, which the owner starts; it copies one file in |
| Agent container → `evidence/transcripts/` | The transcript, scrubbed | The token's value | The scrubber, with its planted-token test; gitleaks in the gate and the pre-push hook as a second net (SEC-01, SEC-02) |
| Working tree → git remote | Commits | `.env`, any token | `.gitignore`, gitleaks, the guard hook; pushing is the owner's call |

# 3. Data flow: one request, end to end

The developer runs the Python snippet with their own token (UC-01).

1. **Shell:** `python quickstart/python/quickstart.py`.
2. **`.env` reader (`python-dotenv`):** loads `QRYPT_API_KEY` and, if set, `QRYPT_API_URL`. No
   token: the snippet prints where to get one and how to set it, and exits 1.
3. **Snippet, request:** `urllib.request` sends `GET {QRYPT_API_URL}?size=1`, defaulting to the live
   endpoint, with `Accept: application/json`, `Authorization: Bearer <token>` and
   `User-Agent: qrypt-quickstart-python/<version>`.
4. **Network:** live, Cloudflare's edge, then Qrypt's API in its one documented region (PERF-01); in
   CI, the mock on `localhost`, which records the request.[^audit]
5. **Snippet, status:** anything but 200 maps to its own message and a non-zero exit, before the body
   is read (DQ-02).
6. **Snippet, body:** parses the JSON, base64-decodes `random`, and checks it has at least 1,024
   bytes (DQ-06).
7. **Snippet, key:** bytes 0 to 31 are the AES-256 key; the nonce comes from bytes after them, so the
   two never share entropy.[^plan]
8. **`cryptography` AES-GCM:** encrypts and decrypts a sample string; an `if`, not an `assert`,
   compares the result.
9. **Output:** one success line naming the key's length and the round trip; never the key. Exit 0.

The key lives only in the process's memory and is gone when it exits. The Node and Rust snippets
follow the same steps with `fetch` and `node:crypto`, and with `ureq` and `dotenvy`.

# 4. Verification design

| What is checked | How | Where it runs |
|---|---|---|
| Each snippet's contract: `size=1`, both headers, the `User-Agent`, success line, no key, no file | Tests that run the snippet as a subprocess against the mock and read the mock's request record | `make e2e`, the gate, CI |
| Each failure path: 400, 401, 403, 429, 500, 503, refused connection, bad certificate, odd 200 | The mock's error routes, by token | The same, from Phase 3 |
| At most 25 counted lines | `make check C=snippet-lines` | The gate |
| The site shows exactly the snippets, and no file from `docs/` | A test over the built site | `make e2e`, CI |
| What a model writes from the docs | Eval cases (`agent-contract`, `key-handling`, `error-handling`, `no-sdk`, one regression case per Round 1 failure), recorded once, replayed for $0 | The gate |
| No token in a transcript | The scrubber's planted-token test; a test that no committed file holds a token-shaped string; gitleaks | The gate |
| Live use within budget | A test totals `evidence/live_usage.csv` and fails at 8,192 KiB | The gate, from Phase 7 |
| Accessibility and load | Lighthouse, 10 mobile runs | Phase 5, and CI if not cut |

**Known blind spots.**

- **The mock's undocumented edges** (ARCH-01): a snippet tuned to its guesses can pass CI and fail
  live. Branching on status alone, and Phase 7's recorded answers, narrow it.
- **Fixed bytes:** the mock's seeded 200 cannot show a decode bug that only some inputs trigger, so
  one test serves bytes from `os.urandom`.
- **The edge and the round trip** (ARCH-02, PERF-01) exist only live, and Phase 7 sees them once.
- **Five runs a round** is a small sample; the report gives counts, not rates with false precision.
- **The scrubber matches the exact value.** A token split across lines, URL-encoded or base64-encoded
  passes it; gitleaks catches only the assignment shapes (SEC-02). What the model provider received
  cannot be seen at all, which is why the token is revoked.
- **Replayed evals do not see model drift**; a re-recording is a paid run, the owner's call.

# 5. Failure behavior per dependency

| Dependency | Down | Slow | Wrong |
|---|---|---|---|
| Qrypt's API | 500 or 503: "try again shortly", exit non-zero | A 10-second timeout, then a message naming the network and the region, exit non-zero | A 200 whose `random` is missing, short or not base64: its own message, no traceback |
| Cloudflare's edge | Connection refused or reset: a message naming the network and the proxy entry | As above | A 403 from the edge: the message and the troubleshooting entry name two causes, the allotment and an edge refusal (ARCH-02) |
| The developer's token and account | No token: where to get one and how to set it | Not applicable | 401: the token is wrong or expired; 403: the allotment; 429: wait 10 seconds, exit within 1 s, no retry |
| Network, proxy, TLS | Refused connection: its own message | Timeout, as above | A certificate it cannot verify: the fix sets `SSL_CERT_FILE` or `NODE_EXTRA_CA_CERTS`, never turns verification off (SEC-04) |
| The mock (CI only) | It fails to start: `make e2e` fails and the gate is red; no user sees it | Not applicable | Its guesses differ from Qrypt: caught only by Phase 7 |
| GitHub Actions | No CI run: `make gate` on the laptop still gates a commit | Not applicable | Not applicable |
| The static host (GitLab Pages, after the move) | The site does not load: the README points at the same Markdown in the repository | Not applicable | Not applicable |
| The agent harness: Docker, Claude Code's login, the model provider | The run is logged as it happened with the category `harness`, never dropped or rerun silently; the report says so | Logged with its wall-clock time; the harness stops a run at 30 minutes | A run whose agent read or printed the token is logged with the category `token-exposed` |
| The eval model's provider | No effect on the gate: it replays recordings | Not applicable | A missing recording fails the gate; re-recording is a paid run for the owner |

# 6. Speed against completeness

| Target | Budget | What is dropped to meet it |
|---|---|---|
| Snippet under 3 s end to end, live (RQ-22) | Runtime start under 0.07 s (PERF-04); one round trip to one region, unmeasured until Phase 7 (PERF-01); decode and AES-GCM well under a millisecond | Any retry or backoff; a second request; any `size` above 1; an SDK or wrapper; any check of the entropy beyond its length |
| Page under 1.5 s p95 on mobile (RQ-20) | A static page, Markdown rendered at build time | A client framework, web fonts, analytics (RQ-40), a search box, a try-it console |
| Agent median under 10 minutes (RQ-19) | Whatever the agent spends; the docs can only shorten it | Nothing in the product; the docs put the one working program first and the explanation after |
| Grader quick-start under 5 minutes (RQ-35) | Install and one run per snippet | Building the site and running the evals are in the README but not in the quick-start |

# 7. Deviation register

| Id | The brief said | Reality (evidence) | Substitute |
|---|---|---|---|
| DV-01 | "Deployed quickstart site ... deployed URL loads" (RQ-05)[^assessment] | The owner locked building on private GitHub with the site as a CI artifact, moving to GitLab Pages at the very end ([the plan](PLAN.md), "Decisions locked with the owner") | Every push builds the site and uploads it; the owner deploys after the move, and the deliverable waits on that step |
| DV-02 | "No tokens visible in ... agent-run logs"[^assessment] | The agent's program must read the token from `.env` in its container, so the agent can read it too, and what it reads goes to the model provider (SEC-01); a bare token passes gitleaks (SEC-02, its reproduction)[^audit] | Committed transcripts are scrubbed by exact value, with a planted-token test; the containers use a token the owner revokes after Phase 8; an exposed run is logged as `token-exposed`. The provider-side exposure is bounded by revocation, not prevented |
| DV-03 | The audit's ARCH-02 mitigation: "Phase 7 sends one request with Python's default client" | A probe with the real token and `size=1` would take Phase 7 from 12 KiB to 13 ([the plan](PLAN.md), Phase 7's budget); the edge answers before the API reads the token, so a bad-token request shows the same refusal | The probe is a bad-token request with Python's default client, 0 KiB, beside the planned bad-token request with the named `User-Agent`; Phase 7 stays at 12 KiB |
| DV-04 | The agent test runs the quickstart against Qrypt, in a fresh environment[^assessment] | There is no Qrypt token yet ([the handoff](../HANDOFF.md), "Open, for the owner") | If none comes by 2026-10-20 18:00 CDT, both rounds run against the mock with its URL given to the agent, and `AGENT_READINESS.md` and the PRD say so (the plan's cut order, item 7) |

# 8. Traceability matrix

The metric column names the ids of [the key metrics](KEY_METRICS.md).

| Use case | Capability | Data | Audit findings | Eval category | Metric |
|---|---|---|---|---|---|
| UC-01 | Python and Node snippets: `size=1`, both headers, named `User-Agent`, AES-GCM round trip, success line only | Token in `.env`; 1 KiB from the mock or the API; `quickstart/` files | DQ-01, DQ-02, DQ-06, SEC-03, ARCH-02, ARCH-04, ARCH-06 | `agent-contract`, `key-handling` | NS-01, DR-02, DR-03, GR-01 |
| UC-01 | Site built from `site/` and `quickstart/` only, with tabs and copy buttons | `site/*.md`, the snippet files | CMP-01 | None: a site test | DR-01 |
| UC-02 | A message per status and per environment failure; the troubleshooting page | The mock's error routes; `site/troubleshooting.md` | ARCH-01, ARCH-02, SEC-04, PERF-02 | `error-handling` | NS-01 |
| UC-03 | `llms.txt` and the no-SDK sentence | `site/llms.md`, built to `/llms.txt` | DQ-05, ARCH-03 | `agent-contract`, `no-sdk` | DR-04, GR-02 |
| UC-03 | Agent harness: a fresh container per run, the scrubber, the run log | Container `.env` (revocable token); `evidence/agent_runs.csv`; `evidence/transcripts/` | SEC-01, SEC-02, CMP-02 | One regression case per Round 1 failure | DR-04 |
| UC-04 | The PRD's funnel, kept equal to `docs/KEY_METRICS.md` by a test; the `User-Agent` lets Qrypt count quickstart calls | `PRD.md`, `docs/KEY_METRICS.md` | DQ-04, CMP-03 | None: a test of `PRD.md` | None: it specifies every metric |
| UC-05 | CI on every push; the README's grader quick-start, its shell blocks run against the mock | `README.md`, the snippets, [ci.yml](../.github/workflows/ci.yml) | ARCH-04, ARCH-05 | None: a timed run from a fresh clone | None: RQ-35's timed run |
| UC-06 | Claims table and claim ids on the site | `CLAIMS.md` | DQ-07 | None: Phase 5's test | None: RQ-24's count |

# 9. Tracer bullet

**The feature:** a developer runs the Python snippet with a token and sees the success line (Phase 1
of [the plan](PLAN.md), UC-01).

**The layers it crosses:** input (`.env`, through `python-dotenv`); logic (decode, the 32-byte key,
the AES-GCM round trip); the outside call (the mock, standing in for Qrypt, through `QRYPT_API_URL`);
output (the success line, never the key); one test (`tests/test_quickstart_python.py`); one eval
case (`agent-contract`); the gate; CI on push; the site built and uploaded as an artifact.

**The proving command:** `make e2e`. It starts the mock, runs the snippet against it, checks the
request and the output, builds the site and checks its code block is the snippet's file. Then
`make gate`, then the CI run of the first push, which the owner approves.

**The slices that follow**, one at a time, each with its test and eval case first: Node and the
tabs (Phase 2); every error and the troubleshooting page (3); `llms.txt` (4); claims, accessibility
and speed (5); the PRD (6); the live check, with the edge probe (7); the agent harness and both
rounds, the scrubber's test written and seen to fail before any run (8); the backlog (9); Rust (10);
the submission (11). Anything the tracer bullet proves wrong here goes into the register above
before Phase 2 starts.

# 10. Cut order

From the top, as in [the plan](PLAN.md): the analytics (not built in any case), the competitive
teardown, the Rust snippet, `llms-full.txt`, the PRD's risk and scope prose, Lighthouse in CI; then,
without a token by 18:00 CDT, the agent rounds against the mock (DV-04).

**Never cut:** the plan's invariants; the scrubber and its test; the live-use ledger; the mock and
CI on every push; the site built from `site/` only.

# 11. Not built

| Designed | Why it was left out |
|---|---|
| A proxy in each container that adds the token, so the agent never holds it | The brief's program reads `QRYPT_API_KEY` from `.env`; hiding the token changes the task under test |
| An egress allowlist for the containers (Qrypt and the model provider only) | It does not stop the exposure that matters (the provider), and it costs a network setup the timebox does not have |
| A retry with backoff on 429, 500 and 503 | It teaches the loop the brief forbids, and Qrypt sends no `Retry-After` (PERF-02) |
| A shared HTTP helper or a package for the snippets | Each snippet must be one file a developer copies; the brief's tradeoff is no SDK |
| A mock that imitates Qrypt's error bodies | Qrypt documents none (ARCH-01); imitating one would invent behavior |
| A try-it console on the site | It would put the token in a web page, against the `.env`-only rule[^users] |

# Decisions

### The snippets are single files on the standard library's HTTP client

**Claim:** each snippet is one file under `quickstart/` (Rust in `rust/src/main.rs`), with Python on
`urllib.request`, Node on built-in `fetch` and `node:crypto`, and dependencies only for `.env` and
AES-GCM.
**Evidence:** Python's standard library has no AES-GCM, so `cryptography` is needed; Node 18 and later
have `fetch` and `crypto` built in ([the plan](PLAN.md), "Verified facts"); the brief's limit is 25
lines each.[^assessment]
**Alternative considered:** `requests` in Python, the client most developers already know.
**Why rejected:** one more dependency to install on the first run, for one `GET`; the named
`User-Agent` already settles the edge question that a different client would hide.
**How to reverse:** swap the import and two lines in `quickstart/python/quickstart.py` and add the
package to `pyproject.toml`.

### The mock answers by token and marks its guesses

**Claim:** `src/qrypt_quickstart/mock_server.py` serves the one endpoint on `localhost`, picks its
answer by the bearer token (`mock-200` to `mock-503`), records each request, and labels each
undocumented answer as its own.
**Evidence:** ARCH-01, and the plan's settled item D1.[^audit] [^plan]
**Alternative considered:** a recorded-response mock built from live calls.
**Why rejected:** there is no token yet, and recording every error live would spend entropy and need
a 429 and a 503 on demand.
**How to reverse:** replace the routes with recordings from `evidence/` once Phase 7 has them.

### The site builder reads the snippet files

**Claim:** `web/src/build-site.ts` renders `site/*.md` and inserts each snippet's file where its block
goes, writing the site, `llms.txt` and `llms-full.txt`.
**Evidence:** the plan's "one source for each snippet"; RQ-07 asks that every documented command
runs as written.[^plan] [^deliverables]
**Alternative considered:** a static-site generator with the snippets pasted into its pages.
**Why rejected:** a pasted copy drifts from what CI runs, and a generator adds a dependency and its
own configuration.
**How to reverse:** point the builder's input at a generator's content folder; the snippet files
stay the source.

### The agent-test token: revocable, and scrubbed by exact value (SEC-01, for the owner)

**Claim:** the containers use a token the owner revokes after Phase 8 (a second token if Qrypt
issues one); `scripts/agent_run.sh`, started by the owner, pipes each transcript through an
exact-value scrubber before writing it, refuses to write if the token is empty, and logs an exposed
run as `token-exposed`; the scrubber has its own test, which plants a fake token and fails first.
**Evidence:** SEC-01 and SEC-02, with SEC-02's reproduction that gitleaks misses a bare token;
CMP-02, that a pushed transcript cannot be removed.[^audit]
**Alternative considered:** a proxy that adds the token so the agent never holds it.
**Why rejected:** the brief's task is a program that reads `QRYPT_API_KEY` from `.env`; hiding the
token tests a different task, and a run that succeeds through the proxy proves nothing about the
docs.
**How to reverse:** set the container's `QRYPT_API_URL` to a local proxy in `scripts/agent_run.sh`;
the scrubber stays.

### A named `User-Agent`, and one default-client probe at 0 KiB (ARCH-02, for the owner)

**Claim:** each snippet sends `User-Agent: qrypt-quickstart-<language>/<version>`; Phase 7 adds one
bad-token request with Python's default `urllib` client, beside the planned bad-token request with
the named agent, and records both answers, inside its 12 KiB.
**Evidence:** ARCH-02's reproduction (a Cloudflare-fronted host gave Python's default agent 403 and
curl and Node 200); the edge filters before the API reads the token.[^audit]
**Alternative considered:** a default-client request with the real token and `size=1`.
**Why rejected:** it spends 1 KiB beyond Phase 7's budget and shows nothing more about the edge.
**How to reverse:** drop the header from the snippets' header maps and the probe from
`scripts/live_check.py`.

### CI runs on every push

**Claim:** [ci.yml](../.github/workflows/ci.yml) gains a `push` trigger for every branch, a job that
runs `make e2e`, and a job that builds the site and uploads it.
**Evidence:** the workflow runs on pull requests, `v*` tags and manual runs only, and its comment
says so;[^ci] the brief asks for the snippets against a mock "on every push" (ARCH-05).[^assessment]
**Alternative considered:** keep CI to pull requests and run `make gate` before each push.
**Why rejected:** the brief names every push, and a grader reads the CI history.
**How to reverse:** remove the `push` branch filter in `ci.yml`.

# Locked decisions, restated

| Decision ([the plan](PLAN.md)) | Its evidence | What it fixes here |
|---|---|---|
| Private repository | `docs/brief/` holds the partner's brief ([the handoff](../HANDOFF.md)) | The site is built from `site/` only (CMP-01) |
| Python at the root, Node in `web/`, Rust in `rust/` as the stretch | The owner, 2026-10-19 | Three snippets, one mock, one builder in TypeScript |
| Evals, demo video, semgrep, GitHub Actions | The owner, 2026-10-19 | Eval cases replayed in the gate; CI on Actions |
| Build on private GitHub; GitLab Pages at the end | The owner's words, quoted in the plan | DV-01 |
| Claude Code in a fresh container per run, only `.env` seeded, transcripts scrubbed | The owner's choice, quoted in the plan | The agent harness, and the SEC-01 decision |
| docs.qrypt.com read only, no API call before the token | The owner's choice | The mock is the only target until Phase 7 |
| Live use at most 10,240 KiB | The owner's kickoff message | The ledger; DV-03 keeps Phase 7 at 12 KiB |

No evidence has changed since the plan, so none is reopened.

[^audit]: "Audit: Qrypt's first-run path"
[^users]: "Users: who the Qrypt quickstart serves, and when"
[^plan]: The plan
[^deliverables]: Deliverables
[^assessment]: The assessment's full text
[^ci]: The CI workflow as the kit rendered it
