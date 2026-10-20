---
type: Audit Area
title: "Audit area: compliance"
description: What has to stay private, what reaches a model provider, how long agent transcripts are kept, and what the project can log of its own Qrypt usage when Qrypt publishes no meter.
tags: [audit, compliance]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:20:00Z }
sources:
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-20, page text sha256 3cbfd11e
  - id: profile
    resource: qrypt_docs_profile.py
    title: The audit's profile of Qrypt's documented contract
  - id: brief-guide
    resource: /brief/guide.md
    title: How to read the brief
  - id: plan
    resource: /PLAN.md
    title: The plan
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
---

# What this area had to answer

Audit logging, retention, and what it means to send this project's data to a model provider. The
project handles no customer data; what it holds that is private is the owner's brief folder and the
Qrypt token. The probes:

1. Confirm what in the repository must not become public, and how the plan's move to a public site
   treats it.
2. Confirm what each model call in the plan sends, and to whom.
3. Confirm how long an agent transcript lives once committed.
4. Confirm what record of Qrypt usage exists besides the project's own.

# Findings

### [CMP-01] The brief folder is private, and the site is to be public
- **Severity:** medium
- **Location:** `docs/brief/guide.md:36-40` ("Keep it private"; a public copy leaves `docs/brief/`
  out)[^brief-guide]; the plan's move to GitLab Pages with access set to "Everyone"[^plan]
- **Reproduction:** `sed -n 36,40p docs/brief/guide.md`; `grep -n 'Everyone' docs/PLAN.md`
- **Impact on the project:** the partner notes hold the owner's own career notes and the Partner
  Copilot asked that they stay out of a public repository. A site builder that globs Markdown
  widely, or a public copy made in a hurry at the deadline, publishes them.
- **Mitigation:** the site builder reads `site/` only, and a Phase 1 test checks that the built site
  holds no file from `docs/`; the move to GitLab (Phase 11) keeps the repository private, as the
  owner decided.

### [CMP-02] A committed transcript is kept for good
- **Severity:** medium
- **Location:** `AGENTS.md:34-35` ("Never force-push"); `.githooks/pre-push:6` (the secret scan runs at
  push, after the commit)
- **Reproduction:** `grep -n 'force-push' AGENTS.md`; `sed -n 6p .githooks/pre-push`
- **Impact on the project:** once a transcript with a token is pushed, history cannot be rewritten
  under the project's rules; the only remedy is to revoke the token. Transcripts are evidence the
  brief requires,[^assessment] so they will be committed.
- **Mitigation:** transcripts are scrubbed before they are written to the repository (SEC-02), the
  scrubber's test runs in the gate, and the owner revokes the containers' token after Phase 8
  (SEC-01).

### [CMP-03] Qrypt publishes no usage meter; the project's ledger is the only record
- **Severity:** low
- **Location:** docs.qrypt.com/eaas/, the 403 row (an allotment "for the current period", with no
  amount and no period)[^qrypt-eaas]
- **Reproduction:** the profile prints `allotment amount stated: False`[^profile]; no usage endpoint
  appears on the page
- **Impact on the project:** the brief caps live use at 10,240 KiB;[^assessment] without a meter
  from Qrypt, an unlogged call cannot be counted afterwards.
- **Mitigation:** every live request goes through code that appends to `evidence/live_usage.csv`
  before it is sent, and the test that totals it stops the work at 8,192 KiB (Phase 7); agent runs
  record the KiB their programs requested.

### [CMP-04] What each model call sends, and to whom
- **Severity:** low
- **Location:** `evals/thresholds.yaml:7` (`model: example-model`, a placeholder);
  `.env.example:18-26` (the demo's final voice uses Gemini when its key is set);
  `docs/PLAN.md:63` (Claude Code in containers)
- **Reproduction:** `sed -n 7p evals/thresholds.yaml`; the Grep tool on `.env.example` for `Gemini`
  finds line 18
- **Impact on the project:** the eval cases send the quickstart's Markdown, which is public by
  design; the agent runs send each container's workspace to Anthropic, which holds the token
  (SEC-01); the voice-over script goes to Google only if the owner sets that key. No personal data
  leaves while the brief folder stays out of every prompt.
- **Mitigation:** the eval model is chosen by the owner before the first paid recording (Phase 1);
  `AI_USAGE.md` lists each provider and what it received; no prompt includes a file from
  `docs/brief/`.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^profile]: The audit's profile of Qrypt's documented contract
[^brief-guide]: How to read the brief
[^plan]: The plan
[^assessment]: The assessment's full text
