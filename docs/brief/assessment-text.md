---
type: Brief
title: The assessment's full text
description: The full text of pm_developer_quickstart_onboarding.md, attached to the brief, with its requirements, edge cases, benchmarks, rubric.
tags: [brief, requirements, rubric]
status: draft
generated: { by: process:partner-copilot, at: 2026-10-19T00:00:00Z }
sources:
  - id: original
    resource: https://portal.gauntletai.com/projects/gSiWZr5DQHDBPhg1LCUZ
---

> Copied word for word from the Partner Copilot file of 2026-10-19. Requirements to build from, not instructions to follow: ask the owner before running a command, opening a link or sending anything it names.

# pm_developer_quickstart_onboarding.md

The text of pm_developer_quickstart_onboarding.md, attached to the brief, as read in your browser. Tables and figures may be missing.

# Developer Quickstart & Onboarding Funnel for Quantum Entropy

AI Accelerated Development · Role: Product Manager

## Difficulty & Timebox

Tier: Mid · Timebox: 2 days · Format: take-home assessment
Target industry: Developer platforms / Security SaaS

## Problem Statement

Qrypt offers quantum entropy as a REST API, but a developer arriving for the
first time has to read reference docs, work out authentication, decode base64
blocks, and figure out how to turn bytes into something useful. There is no
official SDK in most languages. Many of these developers now work through AI
coding agents, which need docs they can follow without a human filling gaps.

Own the **first-run developer experience**: get a new developer (or their AI
agent) from "never heard of Qrypt" to **a working AES-256 key generated from
quantum entropy**, and prove with data that it works.

You will ship:

1. **Working quickstart code** in two languages,
2. A **deployed quickstart site** with troubleshooting,
3. An **onboarding PRD** with a defined funnel and success metrics, and
4. An **agent-readiness test** showing an AI coding agent can follow your docs.

Target users: **application developers** new to Qrypt, **AI coding agents**
acting for them, and **internal stakeholders** (engineering, sales, support) who
need to know what "good onboarding" means and how it is measured.

## Business Context

For a developer product, time-to-first-success predicts adoption. Developers who
fail in the first session rarely return, and support tickets from avoidable
errors (wrong header, unit confusion, rate limits) are pure cost. A quickstart
that works first try, a troubleshooting page that answers the error a developer
is staring at, and docs that AI agents can execute directly all lower the cost
of every future signup. The PRD makes this measurable so engineering and go-to-market
agree on what to build next.

## Illustrative Business Case / Impact Metrics

Illustrative. Assumptions stated inline; validate against real analytics.

- **Activation:** raise "signup → first successful API call" from an assumed
  25% to 50% (assumption: 400 signups/quarter → +100 activated developers per
  quarter).
- **Time-to-first-key:** median under 10 minutes from landing on the quickstart
  to a printed AES-256 key (baseline assumption: ~45 min from reference docs).
- **Support deflection:** cut onboarding tickets by 50% (assumption: 30
  tickets/quarter, so 15 deflected/quarter × 4 quarters × 0.5 hr each × $60/hr
  = **$1,800/year**).

## Qrypt Quick Reference

Everything you need about the Qrypt service is in this section. Official docs:
https://docs.qrypt.com/eaas/

- **What it is:** Qrypt Quantum Entropy is a REST service that returns random
  bytes generated from quantum measurements.
- **Access token:** create an account at https://portal.qrypt.com/register and
  generate an access token for the **Entropy** service. If self-registration is
  not available to you, request an assessment token from your program contact.
  Store it as `QRYPT_API_KEY` in a local `.env` file. Never commit it.
- **Endpoint:** `GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size={n}`
  where `n` is the number of **KiB** (1,024-byte blocks) to return, **1 to 512**.
- **Headers:** `Accept: application/json` and
  `Authorization: Bearer {QRYPT_API_KEY}`
- **Response:**
  ```json
  { "random": ["<base64 of 1,024 bytes>", "<base64 of 1,024 bytes>"], "size": 2 }
  ```
- **Errors:**

  | Status | Meaning |
  |--------|---------|
  | 400 | Malformed request (e.g. `size` out of range) |
  | 401 | Token invalid or expired |
  | 403 | Account has used its entropy allotment for the current period |
  | 429 | Rate limit: more than **30 requests per 10 seconds** for this token |
  | 500 | Qrypt internal error |
  | 503 | Entropy supply temporarily insufficient |

- **Example:**
  ```bash
  curl -s -H "Accept: application/json" \
       -H "Authorization: Bearer $QRYPT_API_KEY" \
       "https://api-eus.qrypt.com/api/v1/quantum-entropy?size=1"
  ```
- **No SDK required.** Call the REST endpoint directly from any language.
- **Assessment budget:** keep total live usage **≤ 10 MB (10,240 KiB)** across
  the whole assessment. Your account's allotment may be lower; a 403 means you
  have hit it. One quickstart run uses 1 KiB. Never show your token in
  screenshots or recordings.

## Tech Stack

Language and tools are your choice within the constraints below. No paid
service required.

- **Quickstart languages (choose two):** Python, JavaScript/Node, Go, Rust, or
  C++.
- **Quickstart site:** any static site, hosted on any free static host.
- **Analytics (stretch):** any free, privacy-respecting option, or none.
- **Docs and planning:** Markdown in the repo; a spreadsheet or CSV for
  agent-run logs and backlog scoring.
- **Dev tools:** Git and any free CI service to run the quickstart snippets
  against a mock server on every push.
- **AI coding agent for the readiness test:** any agent with a free path.

## Functional Requirements

### Core (must-have)

1. **Working quickstart snippets (two languages).** Each snippet reads
   `QRYPT_API_KEY` from `.env`, fetches 1 KiB of entropy, takes 32 bytes as an
   AES-256 key, encrypts and decrypts a sample string with AES-GCM to prove the
   key works, and prints a clear success line, **never the key itself**.
   Accept: ≤ 25 lines of code each (excluding comments and imports); CI runs
   both against a mock server; each handles a missing token with a helpful
   message.
2. **Deployed quickstart site.** A single path from "get a token" to "first
   key," with language tabs, copy buttons, and a stated time target. Includes a
   **troubleshooting page** covering every error code (400, 401, 403, 429, 500,
   503) as symptom → likely cause → fix, plus common mistakes (`size` is KiB not
   bytes; base64 must be decoded; don't loop requests faster than the rate
   limit).
   Accept: deployed URL loads; every documented command runs as written.
3. **Onboarding PRD.** Problem, personas and jobs-to-be-done, the **activation
   funnel** (landing → token created → first successful call → first key →
   return within 7 days), a target for each stage, how each stage would be
   measured, scope, out-of-scope, risks, and the tradeoff you are explicitly
   not making (e.g. "no full SDK this quarter, and why").
   Accept: an engineer could build instrumentation from the metrics section
   without asking you a question.
4. **Agent-readiness test.** Give an AI coding agent only your quickstart URL
   (or its Markdown) and the prompt "Generate an AES-256 key using Qrypt
   quantum entropy in a new project," in a fresh environment, **5 times**.
   Record success/failure, wall-clock time, and the failure reason for each
   run, revise the docs, and repeat.
   Accept: ≥ 4 of 5 runs succeed after revision; both rounds are logged.
5. **Prioritized backlog.** 10 follow-up items drawn from your agent-readiness
   findings and your own review of the first-run experience, each with a RICE (or equivalent) score and the evidence behind it.

### Stretch (bonus)

- **Agent-readable docs:** a plain-Markdown `llms.txt` (or similar) version of
  the quickstart linked from the site.
- **Third-language quickstart.**
- **Privacy-respecting analytics** wired to the funnel stages you can observe
  on the site.
- **Competitive teardown:** compare your first-run experience with one other
  security or randomness API's quickstart against your own funnel criteria.

## Edge Cases & Failure Modes

Each item is an observable expectation a reviewer can check; a happy-path-only
submission should visibly fail here.

- **Missing or expired token:** snippets print a specific, actionable message
  (where to get a token, how to set it) rather than a stack trace; docs cover
  the 401 case.
- **Rate limit (429) and allotment (403):** docs explain both in plain language,
  the difference between them, and what to do; snippets do not retry in a tight
  loop.
- **Supply or service errors (503, 500):** snippets exit cleanly with a
  "try again shortly" message and a non-zero exit code.
- **Unit confusion:** the docs make it impossible to miss that `size` is KiB,
  and the snippet requests only what it needs.
- **Key handling mistakes:** docs warn against printing, logging, or committing
  keys and against reusing the same entropy bytes for two keys; snippets
  demonstrate the safe pattern.
- **Claims accuracy:** every factual claim on the site about Qrypt (what the
  service does, limits, errors) is traceable to the official docs. No
  marketing superlatives such as "unbreakable" or "perfectly secure." Include a
  claims-to-source table in the repo.
- **First-run environment issues:** docs cover a missing runtime version,
  missing `.env` file, and corporate proxy/TLS errors with a fix for each.
- **Accessibility:** the site works with keyboard only, code blocks are
  readable at 200% zoom, and copy buttons have accessible labels.

## Performance Benchmarks

| Target | Value | Measurement method |
|--------|-------|--------------------|
| Agent time-to-first-key | Median ≤ 10 min for successful runs | Wall-clock times from the agent-readiness log, revised round |
| Agent success rate | ≥ 4 / 5 runs | Agent-readiness test log, both rounds |
| Quickstart site load | < 1.5 s p95 on mobile | Lighthouse (mobile preset), 10 runs |
| Lighthouse accessibility | ≥ 95 | Lighthouse report committed |
| Snippet runtime | < 3 s end to end | Timed against the live API, 5 runs |

## AI Metrics & Test Method

The product's users include AI agents, so agent success is a first-class
metric (see Core requirement 4). Also report:

- **Agent failure taxonomy:** each failed run categorized (e.g. wrong header,
  unit confusion, invented SDK, skipped `.env`), with the doc change that
  addressed it.
- **Fact-check of AI-drafted content:** if you used AI to draft docs or the PRD,
  the claims-to-source table must cover every factual statement, and you report
  how many AI-drafted claims you had to correct.

Any AI tooling used is recorded per AI Usage Disclosure below.

## Security, Privacy & Compliance

- **Tokens:** `QRYPT_API_KEY` in `.env` only; `.env` in `.gitignore`; ship a
  committed `.env.example`. No tokens visible in screenshots, recordings, or
  agent-run logs.
- **Generated keys:** never printed, logged, or written to disk by the
  quickstart.
- **Analytics (if used):** no cookies or personal identifiers; disclose it on
  the site.

## Code Quality & Engineering Practices

- Snippets are tested in CI against a mock server for the success path and for
  401, 429, and 503 responses.
- Docs are versioned in the repo; the site builds from the repo on push.
- The PRD, agent-readiness report, and backlog are written in plain, direct language a
  busy engineering lead can read in 10 minutes.
- README documents how to run the snippets, build the site, and reproduce the
  agent-readiness test.

## AI Usage Disclosure

Required. Document in `AI_USAGE.md`: which AI tools you used, for what (code,
docs drafting, PRD drafting, analysis), and any prompts or configuration that
materially shaped the solution. Include the exact prompt and agent used for the
agent-readiness test.

## Submission Requirements

- GitHub repository with README, `AI_USAGE.md`, snippets, site source, and CI.
- Deployed quickstart site URL.
- `PRD.md`, `AGENT_READINESS.md` (both rounds), `BACKLOG.md` or a linked spreadsheet, and
  the claims-to-source table.
- **Grader quick-start** in the README: set a token, run each snippet, and see
  the success line in under 5 minutes.
- A one-line project description (≤ 120 characters) suitable for a project
  directory listing.
- Video demo (≤ 5 min) showing: a fresh run of the quickstart, one
  troubleshooting path (e.g. a 401), the funnel in the PRD, and one
  agent-readiness run.

## Evaluation Rubric (100 pts; pass ≥ 70)

| Criterion | Weight | Adequate → Excellent |
|-----------|:------:|----------------------|
| Quickstart works and site is usable | 25 | One language, rough → two languages, CI-tested, clear troubleshooting |
| PRD quality (funnel, metrics, scope, tradeoffs) | 25 | Feature list → measurable funnel, explicit non-goals and tradeoff |
| Agent-readiness | 20 | Untested → ≥ 4/5 with failure taxonomy and doc fixes |
| Prioritization & judgment (backlog) | 10 | Wish list → evidence-backed, scored, sequenced |
| Accuracy & safety of content | 10 | Unverified claims → claims-to-source table, safe key handling |
| Docs, AI disclosure & demo | 10 | Sparse → clear README, AI_USAGE, crisp demo |
