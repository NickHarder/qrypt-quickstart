---
type: Audit Area
title: "Audit area: security"
description: Where the Qrypt token and the generated key could leak in the first-run path, in Qrypt's own examples and in this project's agent test, and what the repository's scans can and cannot catch.
tags: [audit, security]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:20:00Z }
sources:
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-20, page text sha256 3cbfd11e
  - id: profile
    resource: qrypt_docs_profile.py
    title: The audit's profile of Qrypt's documented contract
  - id: plan
    resource: /PLAN.md
    title: The plan
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
verified:
  - { by: human:nickharder, at: 2026-10-20T21:46:35Z }
approved_sha256: 4241aabc75cedd2db2c7d1c2cf69154108d328fe6196ff96b62acda7a904aff2
---

# What this area had to answer

Authentication, data exposure, secrets in the repository and the handling of sensitive data, for a
project whose only secret is the owner's Qrypt token (`QRYPT_API_KEY`) and whose only sensitive
output is the AES-256 key the snippet makes. The probes, written before reading:

1. Confirm that no secret is in the tree or the history.
2. Confirm what Qrypt's own examples teach about where the token lives and what gets printed.
3. Confirm whether the agent-readiness design can put the token in front of a model.
4. Confirm whether the secret scan would catch a token in an agent transcript.
5. Confirm what Qrypt says about proxies and certificate errors.
6. Confirm that the lock files have no known vulnerability.

No call went to the Qrypt API: there is no token, and the plan allows docs.qrypt.com read only.[^plan]

# Findings

### [SEC-01] The agent test puts the live token where the agent can read it
- **Severity:** high
- **Location:** `docs/PLAN.md:63` and `docs/PLAN.md:301` (each run's container holds the token in
  the env file the agent's program must read)
- **Reproduction:** `grep -n 'seeded\|the token in' docs/PLAN.md` prints lines 63 and 301; the
  project's own rule says why it matters: `grep -n 'a key it reads goes to the' AGENTS.md` (line 93)
- **Impact on the project:** an agent that opens the env file with its own tools (to check it, or to
  debug a 401) sends the token to the model provider and writes it into the transcript that Phase 8
  commits as evidence. The brief forbids a token in agent-run logs.[^assessment]
- **Mitigation:** the architecture (Gate 3) decides it, with these as the floor: the token used in the
  containers is one the owner can revoke after Phase 8, and the owner revokes it; each transcript is
  scrubbed by the token's exact value before it is written (SEC-02); a run whose agent printed or
  read the token is logged with that failure category, not hidden.

### [SEC-02] The secret scan does not catch a bare token in a transcript
- **Severity:** medium
- **Location:** `.gitleaks.toml:7-8` (gitleaks' default rules, no rule for a Qrypt token, whose shape
  is not published)
- **Reproduction:** in an empty directory, write one JSON line holding a random 64-character
  URL-safe string (`python3 -I -c "import secrets,json;print(json.dumps({'content':'The file holds one line. '+secrets.token_urlsafe(48)}))" > t.jsonl`),
  then `gitleaks dir --no-banner --redact --config .gitleaks.toml .` prints `no leaks found`. The
  same string written as `QRYPT_API_KEY=<value>` or `token = "<hex>"` is found (`leaks found: 2`).
- **Impact on the project:** a token that reaches a transcript as tool output passes the gate and the
  pre-push scan (`.githooks/pre-push:6`) and lands in `evidence/transcripts/`.
- **Mitigation:** Phase 8's scrubber replaces the token by its exact value, read by the shell script
  and never by an agent, and a test plants a fake token in a sample transcript and checks it is
  gone. The pattern scan stays as the second line, not the first.

### [SEC-03] Qrypt's own examples put the token in source and print every entropy byte
- **Severity:** high
- **Location:** docs.qrypt.com/eaas/, the Python example (`accesstoken = '{qrypt_access_token}'`,
  `print( f'{b}')`) and the PowerShell example (`$accesstoken = '{qrypt_access_token}'`)[^qrypt-eaas]
- **Reproduction:** `python3 -I docs/audit/qrypt_docs_profile.py` prints
  `Python example writes the token in source: True` and
  `Python example prints every entropy byte: True`[^profile]
- **Impact on the project:** a developer or an agent that falls back on Qrypt's page copies a token
  literal into a file it may commit, and prints the bytes that become the key. The brief requires the
  token in the env file only and the key never printed, logged or written.[^assessment]
- **Mitigation:** the quickstart reads the token from the environment and prints only a success
  line (Phase 1 tests check the key, its hex and its base64 are absent from the output); the site's
  common-mistakes section names both habits; the agent-contract eval case fails a program that
  hard-codes the token or prints the key.

### [SEC-04] Qrypt says nothing about proxies or certificate errors
- **Severity:** medium
- **Location:** docs.qrypt.com/eaas/ (the page's only security statement is that calls use HTTPS)[^qrypt-eaas]
- **Reproduction:** `grep -ci 'proxy\|certificate\|verify=' eaas.txt` on the page's text (the
  profile's `html_to_text` output) prints `0`
- **Impact on the project:** a developer behind a TLS-inspecting proxy gets a certificate error,
  and the quickest fix found on the web is to turn verification off, which exposes the token.
- **Mitigation:** the troubleshooting page (Phase 3) gives the fix that keeps verification on
  (`SSL_CERT_FILE` for Python, `NODE_EXTRA_CA_CERTS` for Node), and a test checks that no snippet
  and no page disables certificate checks.

### [SEC-05] No secret in the repository, and no known vulnerability in its locks
- **Severity:** info
- **Location:** the whole tree and both commits; `uv.lock`, `web/package-lock.json`,
  `demo/package-lock.json`, `rust/Cargo.lock`
- **Reproduction:** `gitleaks git --no-banner --redact .` and `gitleaks dir --no-banner --redact .`
  print `no leaks found`; `npm audit` in `web/` and `demo/` prints `found 0 vulnerabilities`; the
  22 PyPI packages of `uv.lock`, sent to `https://api.osv.dev/v1/querybatch`, have no known
  vulnerability; `rust/Cargo.lock` holds the crate alone, with no dependency. `pip-audit` and
  `cargo audit` are not installed; OSV is the database both read.
- **Impact on the project:** none now. The snippets' dependencies (`cryptography`, the Rust HTTP
  and AES-GCM crates) are not added yet.
- **Mitigation:** run the same checks when Phase 1 and Phase 10 add dependencies.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^profile]: The audit's profile of Qrypt's documented contract
[^plan]: The plan
[^assessment]: The assessment's full text
