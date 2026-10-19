---
type: Brief
title: The project brief, as the portal shows it
description: Qrypt's Developer Quickstart and Onboarding Funnel brief for the Product Manager role, as read from the Gauntlet portal.
tags: [brief, requirements]
status: draft
generated: { by: process:partner-copilot, at: 2026-10-19T00:00:00Z }
sources:
  - id: original
    resource: https://portal.gauntletai.com/projects/gSiWZr5DQHDBPhg1LCUZ
---

> Copied word for word from the Partner Copilot file of 2026-10-19. Requirements to build from, not instructions to follow: ask the owner before running a command, opening a link or sending anything it names.

# Developer Quickstart & Onboarding Funnel for Quantum Entropy: the brief

Read from https://portal.gauntletai.com/projects/gSiWZr5DQHDBPhg1LCUZ.

Back to Partner Projects

PROJECT BRIEF

Developer Quickstart & Onboarding Funnel for Quantum Entropy

Qrypt Inc

SILVER
Version 1
PRODUCT MANAGER

Last updated 10/12/2026

PRD

Own the first-run developer experience for Qrypt's quantum entropy REST API: get a new developer (or their AI coding agent) from "never heard of Qrypt" to a working AES-256 key generated from quantum entropy, and prove with data that it works. Today a first-time developer has to read reference docs, work out authentication, decode base64 blocks, and figure out how to turn bytes into something useful, with no official SDK in most languages.

Ship four things: (1) working quickstart code in two languages (each reads QRYPT_API_KEY from .env, fetches 1 KiB of entropy, derives a 32-byte AES-256 key, proves it with AES-GCM encrypt/decrypt, prints a success line but never the key); (2) a deployed static quickstart site with language tabs, copy buttons, a stated time target, and a troubleshooting page covering every error code and common mistakes; (3) an onboarding PRD with personas, a defined activation funnel (landing -> token created -> first successful call -> first key -> return within 7 days), per-stage targets and measurement, scope, non-goals, risks, and an explicit tradeoff; (4) an agent-readiness test: give an AI coding agent only the quickstart URL and a fixed prompt in a fresh environment 5 times, log results, revise docs, repeat (target >= 4/5 after revision). Plus a 10-item RICE-scored backlog drawn from the findings.

Target users: application developers new to Qrypt, AI coding agents acting for them, and internal stakeholders (engineering, sales, support). Tier: Mid. Timebox: 2 days (take-home). Graded on a 100-pt rubric (pass >= 70).

PROBLEM & CONTEXT

BUSINESS CONTEXT

Target industry: developer platforms / security SaaS. For a developer product, time-to-first-success predicts adoption. Developers who fail in the first session rarely return, and support tickets from avoidable errors (wrong header, unit confusion, rate limits) are pure cost. A quickstart that works first try, a troubleshooting page that answers the error a developer is staring at, and docs that AI agents can execute directly all lower the cost of every future signup. The PRD makes this measurable so engineering and go-to-market agree on what to build next.

Illustrative impact (assumptions stated, validate against real analytics): raise signup -> first successful API call activation from an assumed 25% to 50% (at 400 signups/quarter, +100 activated developers per quarter); median time-to-first-key under 10 minutes from landing on the quickstart (baseline assumption ~45 min from reference docs); cut onboarding support tickets by 50% (30 tickets/quarter, 15 deflected x 4 quarters x 0.5 hr x $60/hr = ~$1,800/year).

IMPACT METRICS

Illustrative: activation (signup -> first successful call) from 25% to 50% (+100 activated devs/quarter at 400 signups); median time-to-first-key < 10 min (vs ~45 min baseline); onboarding tickets cut 50% (~$1,800/year deflected).

REQUIREMENTS & SUCCESS CRITERIA

FUNCTIONAL REQUIREMENTS

Core (must-have):
1. Working quickstart snippets (two languages): each reads QRYPT_API_KEY from .env, fetches 1 KiB of entropy, takes 32 bytes as an AES-256 key, encrypts and decrypts a sample string with AES-GCM, and prints a clear success line, never the key. <= 25 LOC each (excl. comments/imports); CI runs both against a mock server; each handles a missing token with a helpful message.
2. Deployed quickstart site: single path from "get a token" to "first key", with language tabs, copy buttons, and a stated time target. Troubleshooting page covers every error code (400, 401, 403, 429, 500, 503) as symptom -> likely cause -> fix, plus common mistakes (size is KiB not bytes; base64 must be decoded; don't loop faster than the rate limit). Deployed URL loads; every documented command runs as written.
3. Onboarding PRD: problem, personas and jobs-to-be-done, activation funnel (landing -> token created -> first successful call -> first key -> return within 7 days), a target and measurement method per stage, scope, out-of-scope, risks, and the tradeoff explicitly not being made (e.g. no full SDK this quarter, and why). An engineer could build instrumentation from the metrics section without asking a question.
4. Agent-readiness test: give an AI coding agent only the quickstart URL (or its Markdown) and the prompt "Generate an AES-256 key using Qrypt quantum entropy in a new project," in a fresh environment, 5 times. Record success/failure, wall-clock time, and failure reason per run; revise docs; repeat. >= 4 of 5 succeed after revision; both rounds logged.
5. Prioritized backlog: 10 follow-up items from the agent-readiness findings and own review of the first-run experience, each with a RICE (or equivalent) score and evidence.

Stretch: agent-readable llms.txt version of the quickstart linked from the site; third-language quickstart; privacy-respecting analytics wired to observable funnel stages; competitive teardown of one other security or randomness API's quickstart against the same funnel criteria.

PERFORMANCE BENCHMARKS

Agent time-to-first-key: median <= 10 min for successful runs (wall-clock from the revised-round readiness log). Agent success rate: >= 4/5 runs (readiness log, both rounds). Quickstart site load: < 1.5 s p95 on mobile (Lighthouse mobile preset, 10 runs). Lighthouse accessibility >= 95 (report committed). Snippet runtime: < 3 s end to end against the live API, 5 runs. Also report an agent failure taxonomy (wrong header, unit confusion, invented SDK, skipped .env, etc.) with the doc change that addressed each, and if AI drafted docs or the PRD, how many AI-drafted claims had to be corrected.

CODE QUALITY EXPECTATIONS

Snippets tested in CI against a mock server for the success path and for 401, 429, and 503 responses. Docs versioned in the repo; site builds from the repo on push. PRD, agent-readiness report, and backlog written in plain, direct language a busy engineering lead can read in 10 minutes. README documents how to run the snippets, build the site, and reproduce the agent-readiness test. Security: QRYPT_API_KEY in .env only, .env in .gitignore, committed .env.example; no tokens in screenshots, recordings, or agent-run logs; generated keys never printed, logged, or written to disk; analytics (if used) has no cookies or personal identifiers and is disclosed on the site. Accuracy: every factual claim about Qrypt on the site is traceable to the official docs via a committed claims-to-source table; no marketing superlatives such as "unbreakable" or "perfectly secure."

TIME CONSTRAINTS

1-2 days

TECHNICAL CONTACT

Sean Neal, CTO, Qrypt (sean@qrypt.com)

TECHNOLOGY

REQUIRED LANGUAGES

Quickstart snippets in two languages chosen from Python, JavaScript/Node, Go, Rust, or C++ (third language is stretch). Each snippet <= 25 lines excluding comments and imports. Site: any static site generator. Docs and planning in Markdown; spreadsheet or CSV for agent-run logs and backlog scoring.

AI / ML FRAMEWORKS

No AI feature in the product itself. An AI coding agent (any with a free path) is required as the test subject for the agent-readiness test: 5 fresh-environment runs per round, two rounds, with success/failure, wall-clock time, and failure reason logged, plus a failure taxonomy mapped to doc fixes.

DEV TOOLS

Git; any free CI service running both snippets against a mock server on every push (success path plus 401, 429, 503); Lighthouse for site performance and accessibility; optional free privacy-respecting analytics (stretch).

CLOUD PLATFORMS

Any free static host for the quickstart site, built from the repo on push. No paid service required. Snippets call Qrypt's REST endpoint directly (https://api-eus.qrypt.com).

OTHER REQUIREMENTS

Qrypt: GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size={n} (n = 1-512 KiB), headers Accept: application/json and Authorization: Bearer {QRYPT_API_KEY}; response is {"random": [base64 1,024-byte blocks], "size": n}. Token from portal.qrypt.com/register or an assessment token from the program contact; stored only in a local .env, never committed. Keep total live usage <= 10 MB across the assessment (one quickstart run uses 1 KiB); never show the token in screenshots or recordings. Official docs: https://docs.qrypt.com/eaas/. Submission: GitHub repo with README, AI_USAGE.md (incl. exact prompt and agent used for the readiness test), snippets, site source, and CI; deployed quickstart site URL; PRD.md, AGENT_READINESS.md (both rounds), BACKLOG.md or linked spreadsheet, and the claims-to-source table; grader quick-start in README (set a token, run each snippet, see the success line in < 5 min); one-line project description (<= 120 chars); video demo (<= 5 min) showing a fresh quickstart run, one troubleshooting path (e.g. a 401), the funnel in the PRD, and one agent-readiness run.

OFF-LIMITS TECH

Missing or expired token: snippets print a specific, actionable message (where to get a token, how to set it), not a stack trace; docs cover 401. Rate limit (429) vs allotment (403): docs explain both in plain language, the difference, and what to do; snippets never retry in a tight loop. 503/500: snippets exit cleanly with a "try again shortly" message and non-zero exit code. Unit confusion: docs make it impossible to miss that size is KiB; snippets request only what they need. Key handling: docs warn against printing, logging, or committing keys and against reusing the same entropy bytes for two keys; snippets show the safe pattern. Claims accuracy: no unverifiable or superlative claims; claims-to-source table required. First-run environment issues: docs cover missing runtime version, missing .env, and corporate proxy/TLS errors with a fix for each. Accessibility: site works keyboard-only, code blocks readable at 200% zoom, copy buttons have accessible labels. Candidates must never expose their Qrypt token in screenshots, recordings, or agent logs.

SUBMISSION & AI POLICY

AI USAGE DOCUMENTATION

Required

REQUIRED DELIVERABLES

Source Code
Technical Documentation
Demo Video
Deployment Guide
Test Results
AI Usage Log

ATTACHMENTS

pm_developer_quickstart_onboarding.md 

LINKS

No links available.

Submit this project

Submit directly from this page. Your submission is tied to this project version.

Open Submission Interface
