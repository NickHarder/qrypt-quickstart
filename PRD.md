# PRD: the first-run developer experience for Qrypt Quantum Entropy

Owner: Nick Harder, Product Manager candidate · Status: draft for review · 2026-10-20

**In one paragraph.** A developer new to Qrypt, or the AI coding agent working for them, should get
from "never heard of Qrypt" to a working AES-256 key made from quantum entropy in under 10 minutes,
on the first try. We ship a 25-line quickstart in Python and Node.js, a site with a troubleshooting
page that answers every error, an `llms.txt` an agent can follow, and a five-stage activation funnel
that engineering can instrument from this document alone. We do not ship an SDK this quarter.

## Problem

Qrypt sells quantum entropy as one REST endpoint. The first run is harder than the endpoint
(evidence: `docs/AUDIT.md`, from Qrypt's docs as read on 2026-10-19):

- **Three of Qrypt's four code examples leave out the `Accept: application/json` header** that the
  same page says is required. None checks the HTTP status before reading the body, and the Python
  example puts the token in source code and prints every entropy byte.
- **`size` counts KiB, not bytes.** A developer who asks for `size=32` to get a 32-byte key gets
  32 KiB, and uses up the allotment 32 times faster.
- **The answer is base64 text.** It has to be decoded, then sliced into a key and a nonce; Qrypt's
  docs stop before that step.
- **No Python or Node.js package exists** (the only SDK is C/C++, for key generation), so an agent
  that guesses `pip install qrypt` fails.
- **There is no `llms.txt`** at docs.qrypt.com (HTTP 404), and no self-service step to a token is
  documented: the page says to contact Qrypt. The sign-up link the brief gives,
  `portal.qrypt.com/register`, shows a 404; the one self-service route, a trial account at
  `portal.qrypt.com/trial`, is linked only from the portal's login page (seen 2026-10-20).

The brief assumes a first key takes about 45 minutes from the reference docs today (an assumption,
not a measurement). Developers who fail in their first session rarely return, and avoidable errors
(a wrong header, a unit mix-up, a rate limit) become support tickets.

## Goal and business case

| Goal | Target | Basis |
|---|---|---|
| Activation: signup to first successful call | 50%, from 25% | The brief's assumptions; with 400 signups a quarter (assumed), +100 activated developers a quarter |
| Time to first key | Median under 10 minutes, from about 45 minutes | The brief's assumptions |
| Onboarding tickets | Half as many: 15 a quarter deflected, about $1,800 a year | The brief's assumptions: 30 tickets a quarter, 0.5 hours each at $60 an hour |
| An AI agent can follow the docs | At least 4 of 5 fresh runs succeed, median at most 10 minutes | The brief's acceptance and benchmark, measured in `AGENT_READINESS.md` |

## Personas and jobs to be done

| Persona | Job to be done | Success looks like |
|---|---|---|
| **Application developer new to Qrypt** (primary) | "When I first try Qrypt, I want a key I can use from one program, so I can judge it in one sitting." | Their own token, one run, the success line, the key never shown, under 10 minutes |
| **AI coding agent acting for the developer** | "Given only the docs and 'Generate an AES-256 key using Qrypt quantum entropy in a new project', write a program that works." | `size=1`, both headers, the token from the environment, no invented SDK, the key never printed |
| **Qrypt engineering lead** | "Instrument onboarding without a meeting." | Each funnel event built from this document with no question back |
| **Qrypt support engineer** | "Answer an onboarding ticket with one link." | Every error message has a troubleshooting entry with its cause and fix |
| **Sales** | "Know what good onboarding means, in numbers." | The funnel below, read weekly; no persona of its own (the brief says nothing of how sales works) |

Out of scope as users: anyone who wants the key printed or saved, a bulk or looping consumer of
entropy, and a reader looking for a certification claim. The quickstart refuses each by design.

## The activation funnel

**landing → token created → first successful call → first key → return within 7 days.** The unit
is the account, not the token or the request; stages 2 to 4 share one weekly signup cohort, so for
any cohort token created ≥ first successful call ≥ first key, and a cohort that breaks that order is
an instrumentation fault, not a result.

| Stage | What it means | Target | Whose target |
|---|---|---|---|
| 1. Landing | A quickstart page view that leads to a signup | 10% of views | This project's assumption |
| 2. Token created | A signup with an Entropy token within 7 days | 80% of signups | This project's assumption |
| 3. First successful call | A signup with a first `200` within 7 days: **the north star** | 50% of signups, from 25% | The brief's assumptions |
| 4. First key | A signup whose first `200` came from a quickstart program | 40% of signups | This project's assumption |
| 5. Return within 7 days | An activated account that calls again, 1 to 7 days later | 50% of activated | This project's assumption |

Every target marked as this project's assumption is replaced by the first measured cohort.

## Metrics and instrumentation

This is the funnel's one specification (`docs/KEY_METRICS.md` holds the same tables; a test fails
if the two differ in any cell).

### Common to every stage

| Rule | What it is |
|---|---|
| Unit | The **account** (one developer's Qrypt account). Stages 2 to 5 count accounts, never tokens or requests; an account with three tokens counts once |
| Cohort | Accounts created in one ISO week (Monday 00:00 to Sunday 24:00 UTC), read from Qrypt's portal account records. The cohort is the denominator of stages 2, 3 and 4 |
| Join key | `account_ref`: HMAC-SHA-256 of Qrypt's internal account id under a key Qrypt holds, as lowercase hex. No event carries an e-mail, a name, an IP address or a token's value |
| Attribution | The quickstart's "get a token" links carry `ref=quickstart`; the portal stores it on the account at signup as `signup_ref` (`quickstart` or empty) |
| Time | Every `occurred_at` is UTC, ISO 8601 with `Z`, set by the emitting system |
| When a cohort is read | Stages 2 to 4 seven days after the cohort week ends; stage 5 fourteen days after |
| Where the API events fire | In Qrypt's API, after Cloudflare's edge (ARCH-02), so an edge refusal is never a funnel event |

### Each stage

| Stage | Metric | Event | Emitted by, on what trigger | Payload | Join key | Formula | Target |
|---|---|---|---|---|---|---|---|
| 1. Landing | DR-01 | `quickstart_page_viewed` | The quickstart site, by a cookieless `navigator.sendBeacon` to Qrypt's collector, once per load of the landing page in a browser | `occurred_at`, `page_path` | None, by design: aggregate only | Accounts of week W with `signup_ref = quickstart` ÷ `quickstart_page_viewed` events in week W | 10% (project's assumption) |
| 2. Token created | DR-02 | `entropy_token_created` | The system that issues Entropy tokens (the portal, or Qrypt's staff tool for a token got by contacting Qrypt, DQ-04), when a token is created | `account_ref`, `token_ref`, `occurred_at`, `issued_via` (`portal` or `staff`) | `account_ref` | Accounts of the cohort with a token within 7 days of signup ÷ the cohort | 80% (project's assumption) |
| 3. First successful call | NS-01 | `entropy_first_success` | Qrypt's API, on the account's first `200` from `/api/v1/quantum-entropy`, any client | `account_ref`, `token_ref`, `occurred_at`, `size_kib`, `client` | `account_ref` | Accounts of the cohort with `entropy_first_success` within 7 days of signup ÷ the cohort | 50%, from 25% (the brief's assumptions) |
| 4. First key | DR-03 | `entropy_first_quickstart_success` | Qrypt's API, on the account's first `200` whose `User-Agent` starts with `qrypt-quickstart-` | `account_ref`, `token_ref`, `occurred_at`, `client` | `account_ref` | Accounts of the cohort with `entropy_first_quickstart_success` within 7 days of signup ÷ the cohort | 40% (project's assumption) |
| 5. Return within 7 days | GR-01 | `entropy_return_success` | Qrypt's API, on the account's first `200` at least 24 hours after its `entropy_first_success` | `account_ref`, `occurred_at`, `first_success_at` | `account_ref` | Activated accounts of the cohort with `entropy_return_success` at most 7 days after `first_success_at` ÷ activated accounts of the cohort | 50% of activated (project's assumption) |

**Field notes.** `client` is the `User-Agent`'s product token when it starts with
`qrypt-quickstart-` (`qrypt-quickstart-python`, `qrypt-quickstart-node`, `qrypt-quickstart-rust`:
the name each program sends) and `other` for any other client. `token_ref` is the same keyed hash
over the token's id, never its value, for debugging only. Stage 4 is a proxy: the key is made on the
developer's machine and never reported, so the first `200` a quickstart program receives stands for
it (the program derives the key from that answer in the same run).

**Agent metrics**, read from the agent-readiness log `evidence/agent_runs.csv`:

| Metric | Formula | Target |
|---|---|---|
| Agent success rate | Runs that printed the success line with a working key ÷ runs, per round of 5 | At least 4 of 5 in the revised round (the brief's acceptance) |
| Agent time to first key | Median wall-clock minutes of the successful runs, revised round | At most 10 minutes (the brief's benchmark) |

**Dashboards and alerts to build.** One weekly-cohort panel with stages 2 to 4 as shares of the
cohort, the north star as its headline and stage 4 split by `client`; one panel for return within 7
days. Alert when a mature cohort's activation falls below 25% (the brief's assumed baseline), or its
return rate below 50%. None of this exists yet.

## Scope

- A quickstart in **Python and Node.js** (Rust if time allows): each at most 25 lines, reading the
  token from the environment, asking for `size=1`, proving the key with AES-GCM, never printing it,
  and failing with one clear line for every error, after one request.
- A **static site**: one path from "get a token" to "first key", language tabs, copy buttons, a
  stated time target, a **troubleshooting page** for every error code and common mistake, and an
  **`llms.txt`** for agents. Keyboard-accessible; Lighthouse accessibility 100.
- A **claims-to-source table** (`CLAIMS.md`) for every fact the site states about Qrypt.
- The **agent-readiness test**: 5 fresh runs, a doc revision, 5 more (`AGENT_READINESS.md`).
- The **funnel specification** above, and a **backlog** scored from the test's findings
  (`BACKLOG.md`).

## Out of scope

- An SDK or a published package in any language (see the tradeoff below).
- Building the analytics: the site sets no cookie and sends no beacon yet. Stage 1's beacon is
  specified, not built.
- Changing Qrypt's portal, its token issuance, or its own docs; the backlog proposes these.
- On-premises appliances, RNG tools and qseed; key generation (the C/C++ SDK).
- Retries, pooling of entropy across runs, or anything beyond one key per run.

## The tradeoff we are not making

**No full SDK this quarter.** The endpoint is one `GET`; what fails a first run is the header, the
unit, the base64 step and the key handling, and a 25-line program the developer can read fixes all
four without a dependency. An SDK in each language would add a package to release, version,
security-review and support for every language, before we know which languages our developers use.
Stage 4's `client` split tells us that. **We will revisit** if the agent-readiness test shows agents
still inventing an SDK after the `llms.txt` revision, or if the first cohorts show most activated
accounts using a language we have no quickstart for.

## Risks

| Risk | Effect | What we do |
|---|---|---|
| No documented self-service path to a token | Stage 2 stalls before the quickstart can help | The quickstart links the portal's trial sign-up and says to ask a Qrypt contact; the backlog ranks a documented self-service token, and the 404 at the brief's `/register` |
| Cloudflare in front of the API may refuse some HTTP clients with a 403 | Looks like a used-up allotment | Each program sends a named `User-Agent`; the live check tests Python's default client |
| The mock answers where Qrypt's docs are silent (error bodies, a missing `Accept`) | Tests pass on guessed behaviour | Each guess is marked in the mock; the live check records Qrypt's real answers |
| The funnel's data lives in Qrypt's systems, unseen here | The specification may not fit them | Every event names its emitter; stage 1 needs no identifier |
| Stage 4 rests on a `User-Agent` | A developer's own client is counted as `other` | Read stage 4 beside stage 3, never alone |
| `account_ref` is pseudonymous, not anonymous | A privacy review may refuse it | Keyed hash under a key Qrypt holds; no e-mail, IP address or token value in any event |
| Five agent runs a round is a small sample | One flaky run moves the rate by 20 points | Log every run and its failure category; read the taxonomy, not just the rate |
| Live entropy budget of 10,240 KiB | A looping agent could spend it | A ledger of every live call; work stops at 8,192 KiB |
