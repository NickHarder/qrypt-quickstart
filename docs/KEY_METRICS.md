---
type: Key Metrics
title: "Key metrics: the activation funnel and the agent's readiness"
description: The one specification of the five-stage activation funnel (event, trigger, payload, join key, formula and target for each stage) and the two agent-readiness metrics, with the north star, the drivers, the guardrails, what was rejected and where each one is watched.
tags: [metrics, gate]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:30:43Z }
sources:
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
  - id: review
    resource: /brief/research-review.md
    title: What to check in the research before building on it
  - id: users
    resource: /USERS.md
    title: "Users: who the Qrypt quickstart serves, and when"
  - id: architecture
    resource: /ARCHITECTURE.md
    title: "Architecture: snippets, mock, site builder, agent harness and CI"
  - id: audit
    resource: /AUDIT.md
    title: "Audit: Qrypt's first-run path"
  - id: plan
    resource: /PLAN.md
    title: The plan
verified:
  - { by: human:nickharder, at: 2026-10-20T21:46:36Z }
approved_sha256: 83e27680075758303171fff44b0f8e05d0da118673991c4ed2236f85f202e761
---

# How to read this draft

Gate 4, run lean on the owner's go of 2026-10-20. The metrics are the brief's activation funnel
(landing → token created → first successful call → first key → return within 7 days)[^assessment]
and the two agent-readiness numbers the brief benchmarks. This is the **one** specification of the
funnel (it settles the review's D5: two specs for stage 3[^review]); `PRD.md` shows it, and a test
in Phase 6 keeps the two equal.[^plan]

**Every target is an assumption or a requirement, and says which.** Activation from 25% to 50% and
the 45-minute baseline for a human's time to first key are **the brief's assumptions**.[^assessment]
The agent's ≥ 4 of 5 and median ≤ 10 minutes are the brief's acceptance and benchmark. Every other
stage target is **this project's own assumption**, to be replaced by the first measured value.
**No value has been measured yet**: no metric carries a measured line. Effort, wherever this
project states it (the backlog), is in person-weeks.[^plan]

# 1. North star

- [NS-01](/metrics/NS-01.md): Activation, signup to first successful call (stage 3)

# 2. Drivers

- [DR-01](/metrics/DR-01.md): Landing to signup (stage 1)
- [DR-02](/metrics/DR-02.md): Token created (stage 2)
- [DR-03](/metrics/DR-03.md): First key through the quickstart (stage 4)
- [DR-04](/metrics/DR-04.md): Agent success rate

# 3. Guardrails

- [GR-01](/metrics/GR-01.md): Return within 7 days (stage 5)
- [GR-02](/metrics/GR-02.md): Agent median time to first key

# The funnel's one specification

## Common to every stage

| Rule | What it is |
|---|---|
| Unit | The **account** (one developer's Qrypt account). Stages 2 to 5 count accounts, never tokens or requests; an account with three tokens counts once |
| Cohort | Accounts created in one ISO week (Monday 00:00 to Sunday 24:00 UTC), read from Qrypt's portal account records. The cohort is the denominator of stages 2, 3 and 4 |
| Join key | `account_ref`: HMAC-SHA-256 of Qrypt's internal account id under a key Qrypt holds, as lowercase hex. No event carries an e-mail, a name, an IP address or a token's value |
| Attribution | The quickstart's "get a token" links carry `ref=quickstart`; the portal stores it on the account at signup as `signup_ref` (`quickstart` or empty) |
| Time | Every `occurred_at` is UTC, ISO 8601 with `Z`, set by the emitting system |
| When a cohort is read | Stages 2 to 4 seven days after the cohort week ends; stage 5 fourteen days after |
| Where the API events fire | In Qrypt's API, after Cloudflare's edge (ARCH-02), so an edge refusal is never a funnel event[^audit] |

## Each stage

| Stage | Metric | Event | Emitted by, on what trigger | Payload | Join key | Formula | Target |
|---|---|---|---|---|---|---|---|
| 1. Landing | DR-01 | `quickstart_page_viewed` | The quickstart site, by a cookieless `navigator.sendBeacon` to Qrypt's collector, once per load of the landing page in a browser | `occurred_at`, `page_path` | None, by design: aggregate only | Accounts of week W with `signup_ref = quickstart` ÷ `quickstart_page_viewed` events in week W | 10% (project's assumption) |
| 2. Token created | DR-02 | `entropy_token_created` | The system that issues Entropy tokens (the portal, or Qrypt's staff tool for a token got by contacting Qrypt, DQ-04), when a token is created | `account_ref`, `token_ref`, `occurred_at`, `issued_via` (`portal` or `staff`) | `account_ref` | Accounts of the cohort with a token within 7 days of signup ÷ the cohort | 80% (project's assumption) |
| 3. First successful call | NS-01 | `entropy_first_success` | Qrypt's API, on the account's first `200` from `/api/v1/quantum-entropy`, any client | `account_ref`, `token_ref`, `occurred_at`, `size_kib`, `client` | `account_ref` | Accounts of the cohort with `entropy_first_success` within 7 days of signup ÷ the cohort | 50%, from 25% (the brief's assumptions) |
| 4. First key | DR-03 | `entropy_first_quickstart_success` | Qrypt's API, on the account's first `200` whose `User-Agent` starts with `qrypt-quickstart-` | `account_ref`, `token_ref`, `occurred_at`, `client` | `account_ref` | Accounts of the cohort with `entropy_first_quickstart_success` within 7 days of signup ÷ the cohort | 40% (project's assumption) |
| 5. Return within 7 days | GR-01 | `entropy_return_success` | Qrypt's API, on the account's first `200` at least 24 hours after its `entropy_first_success` | `account_ref`, `occurred_at`, `first_success_at` | `account_ref` | Activated accounts of the cohort with `entropy_return_success` at most 7 days after `first_success_at` ÷ activated accounts of the cohort | 50% of activated (project's assumption) |

`client` is the `User-Agent`'s product token when it starts with `qrypt-quickstart-`
(`qrypt-quickstart-python`, `-node`, `-rust`, the names each snippet sends[^architecture]), and
`other` for any other client. `token_ref` is the same keyed hash over the token's id, never its
value, for debugging only.

Stages 2 to 4 share one denominator, so they read as a funnel: DR-02 ≥ NS-01 ≥ DR-03 for any
cohort, and a cohort that breaks that order is an instrumentation fault, not a result.

# 4. Considered and rejected

| Metric | Why rejected |
|---|---|
| Raw request counts (calls to the API a week) | They rise with one looping consumer (AP-02) and say nothing about a developer reaching a key[^users] |
| Developer satisfaction (a survey, a thumbs-up) | Nothing collects it; an uninstrumented number would be invented |
| Model tokens per agent run, as a product metric | A cost of the test, not a user outcome; the brief's agent numbers are success and time[^assessment] |
| A human's time to first key, landing to key (the brief's 45 minutes to under 10) | Landing cannot be joined to an account without a cookie or an identifier, which the brief's analytics rule forbids;[^assessment] the observable part, token to first quickstart `200`, is a breakdown of DR-03. The 45-minute baseline stays the brief's assumption, in `PRD.md`'s business case |
| Onboarding tickets deflected (the brief's $1,800 a year) | Qrypt's ticket system and its tags are not known (P-04's tools are open for the owner);[^users] it stays in the PRD's business case as the brief's assumption |
| The eval pass rate, as a product metric | It is a test of what a model writes from the docs; its `agent-contract` cases feed DR-04 instead |
| Entropy used per account | Qrypt publishes no usage meter (CMP-03);[^audit] and more entropy is not a better first run |

# 5. Dashboard and alert mapping

**No dashboard and no alert exists yet.** Analytics (RQ-40) is not built, and this project cannot
see Qrypt's systems.[^plan] The panels and alerts below are the specification P-03 builds; the
agent metrics are watched in the repository.

| Metric | Panel | Alert |
|---|---|---|
| NS-01 | "Activation funnel, weekly cohorts": stages 2 to 4 as shares of the cohort, NS-01 the headline | A mature cohort below 25%, the brief's assumed baseline |
| DR-01 | "Quickstart landings and quickstart signups, weekly" | None: a driver |
| DR-02 | The funnel panel, stage 2 | None: a driver |
| DR-03 | The funnel panel, stage 4, split by `client`; the median minutes from `entropy_token_created` to `entropy_first_quickstart_success` | None: a driver |
| GR-01 | "Return within 7 days, of activated accounts, weekly cohorts" | A mature cohort below 50% |
| DR-04 | `AGENT_READINESS.md`'s table, read from `evidence/agent_runs.csv` (Phase 8) | The Phase 8 test fails the gate when the table and the log disagree[^plan] |
| GR-02 | The same table, median minutes of the successful runs | The same test |

# Decisions

### The account is the unit, joined by a keyed hash; landing stays aggregate

**Claim:** stages 2 to 5 count accounts, joined by `account_ref`; stage 1 is a weekly ratio of
aggregates, joined to nothing.
**Evidence:** the brief's activation is a share of signups (400 a quarter), that is of accounts;[^assessment]
a token is not a developer, and one developer may hold several; the site's analytics may hold no
cookie or personal identifier.[^assessment]
**Alternative considered:** the research's two specs, `account_id + token_hash` and
`token_id_hash`.[^review]
**Why rejected:** a token join counts a developer once per token, so a rate over tokens and a rate
over accounts disagree; two keys for one stage is the ambiguity D5 names.
**How to reverse:** replace `account_ref` by `token_ref` in each formula; the events already carry
both.

### The north star is stage 3, the brief's activation

**Claim:** NS-01 is signup to first successful call within 7 days.
**Evidence:** it is the one stage the brief gives a baseline and a target for, and the business
case (+100 activated developers a quarter) rests on it.[^assessment]
**Alternative considered:** stage 4, first key, which is the quickstart's own promise (UC-01).
**Why rejected:** stage 4 is observed through a `User-Agent`, a proxy that a developer's own client
does not send; a north star should not rest on a proxy.
**How to reverse:** swap the `role` of NS-01 and DR-03 and their `supports`.

### First key is observed as the first `200` to a quickstart client

**Claim:** stage 4's event is the account's first `200` whose `User-Agent` starts with
`qrypt-quickstart-`.
**Evidence:** the key is made in the developer's process and is never sent or shown;[^users] the
snippet derives it from that one `200` in the same run, and sends the named `User-Agent`.[^architecture]
**Alternative considered:** a beacon from the snippet after its AES-GCM check.
**Why rejected:** it adds a second request, telemetry in a security quickstart, and a call that
works with no network to the collector only by failing quietly.
**How to reverse:** add the beacon to the snippets and fire `entropy_first_quickstart_success`
from it.

# Open for the owner

1. **The funnel's sources are Qrypt's, and unseen.** The account records, the token issuer and the
   API's handling of each `200` exist at Qrypt, but this project has not seen them, and stage 1's
   beacon does not exist (RQ-40 is not built). The rubric's "a source that already exists" holds
   only for the agent metrics, and only once Phase 8 writes `evidence/agent_runs.csv`.
2. **No dashboard or alert exists**; section 5 is a specification.
3. **The project's own targets**: 10% (DR-01), 80% (DR-02), 40% (DR-03), 50% (GR-01). Approve or
   replace them, with the PRD's funnel targets in Phase 6.
4. **`account_ref` is pseudonymous**, not anonymous. The brief's rule forbids personal identifiers
   in the site's analytics, which the beacon keeps; whether Qrypt's server-side events may carry a
   keyed hash is the owner's and Qrypt's call.

[^assessment]: The assessment's full text
[^review]: What to check in the research before building on it
[^users]: "Users: who the Qrypt quickstart serves, and when"
[^architecture]: "Architecture: snippets, mock, site builder, agent harness and CI"
[^audit]: "Audit: Qrypt's first-run path"
[^plan]: The plan
