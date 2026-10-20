---
type: Audit Area
title: "Audit area: architecture"
description: The one integration point Qrypt offers, what its documentation leaves undefined, the edge in front of it, the SDK that is not for entropy, and what the repository is missing before the first slice.
tags: [audit, architecture]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:20:00Z }
sources:
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-20, page text sha256 3cbfd11e
  - id: qrypt-sdk
    resource: https://docs.qrypt.com/sdk/
    title: Qrypt SDK documentation, read 2026-10-20
  - id: profile
    resource: qrypt_docs_profile.py
    title: The audit's profile of Qrypt's documented contract
  - id: node-process
    resource: https://nodejs.org/api/process.html
    title: Node.js process API, process.loadEnvFile, read 2026-10-20
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
  - id: plan
    resource: /PLAN.md
    title: The plan
---

# What this area had to answer

How the system the project builds on is organized, where its data lives, which integration points
the product can use and which turn out not to exist. There is no codebase of the project's own yet,
so this covers Qrypt's API as documented and the scaffold's readiness for the plan's first slice.
The probes:

1. Confirm what Qrypt offers besides the one GET: a sandbox, a test token, an error body, a
   `Retry-After`.
2. Confirm what sits in front of the API host.
3. Confirm what "Qrypt SDK" names in Qrypt's docs.
4. Confirm that the repository knows the keys and the triggers the plan relies on.
5. Confirm the runtimes and libraries each snippet needs.

# Findings

### [ARCH-01] One GET and nothing to test against: the mock's edges are this project's guesses
- **Severity:** high
- **Location:** docs.qrypt.com/eaas/, the Request and Response sections[^qrypt-eaas]
- **Reproduction:** `python3 -I docs/audit/qrypt_docs_profile.py` prints
  `error body shape documented: False`, `Retry-After mentioned: False` and
  `status for a missing Accept stated: False`[^profile]
- **Impact on the project:** the brief's CI runs the snippets against a mock on every push, and the
  mock is the only test double there is.[^assessment] What it answers to a missing `Accept`, what
  body it sends with an error and what headers come with a 429 are invented. A snippet that parses
  an error body passes in CI and breaks on the real service.
- **Mitigation:** the snippets branch on the status code alone and never read an error body; the
  mock marks each invented answer as its own (as the plan settled for D1)[^plan]; Phase 7 records
  the real 401 and the real answer to a missing `Accept`, within its 12 KiB.

### [ARCH-02] Cloudflare fronts the API, and a Cloudflare 403 reads like Qrypt's allotment 403
- **Severity:** medium
- **Location:** `api-eus.qrypt.com` (DNS); docs.qrypt.com/eaas/, the 403 row ("Limit
  reached")[^qrypt-eaas]
- **Reproduction:** `getent hosts api-eus.qrypt.com` answers in Cloudflare's ranges (PERF-01).
  Against another Cloudflare-fronted host, `curl -sS -o /dev/null -w '%{http_code}\n' -A 'Python-urllib/3.12' https://www.cloudflare.com/ips-v4`
  prints `403` while the same command with `-A curl/8.5.0` or `-A node` prints `200`. The API's own
  rules were not probed: that needs a live call.
- **Impact on the project:** if the API's edge filters Python's default client the same way, the
  Python snippet built on `urllib` fails on its first run with a 403, and the troubleshooting page
  sends the developer to ask for more allotment. An HTML error page from the edge also breaks a
  snippet that expects JSON.
- **Mitigation:** each snippet sends a `User-Agent` that names it (`qrypt-quickstart-python/<version>`),
  which also lets Qrypt count quickstart traffic for the funnel; a 200 whose body is not the
  documented JSON exits with its own message (Phase 3); Phase 7 sends one request with Python's
  default client and records the answer.

### [ARCH-03] "Qrypt SDK" exists, for a different product
- **Severity:** medium
- **Location:** docs.qrypt.com/sdk/ (key generation; its one quickstart is C++)[^qrypt-sdk]
- **Reproduction:** the profile prints `SDK page names a 'Qrypt SDK': True` and
  `SDK quickstart pages in the sitemap: /sdk/quickstarts/cpp/`[^profile]
- **Impact on the project:** the brief names "invented SDK" as an agent failure.[^assessment] An agent
  that searches for a Qrypt package finds a real "Qrypt SDK" and may install or imitate it, though
  the entropy service needs none.
- **Mitigation:** the quickstart and `llms.txt` say in one sentence that the entropy service has no
  SDK and that the Qrypt SDK is a separate key-generation product; the Phase 2 eval case fails a
  program that installs a Qrypt package.

### [ARCH-04] The repository does not yet name the two keys the snippets read
- **Severity:** medium
- **Location:** `.env.example` (no `QRYPT_API_KEY`, no `QRYPT_API_URL`)
- **Reproduction:** `grep -c 'QRYPT_API' .env.example` prints `0` (run through the Grep tool,
  which reads the example file only)
- **Impact on the project:** the brief requires a committed example file with the token's
  name,[^assessment] and the grader's quick-start starts by copying it. The check that keeps the
  file honest (`tests/test_env_example.py`) covers the service's settings only, so it would not
  notice either key missing.
- **Mitigation:** Phase 1 adds both lines (the token empty, the URL defaulting to the live endpoint)
  and a test that every variable a snippet reads is in the example file.

### [ARCH-05] CI does not run on every push
- **Severity:** medium
- **Location:** `.github/workflows/ci.yml:13-17`
- **Reproduction:** `sed -n 13,17p .github/workflows/ci.yml` shows `pull_request`, `push` on
  `tags: ["v*"]` and `workflow_dispatch` only
- **Impact on the project:** the brief asks for the snippets to run against the mock on every
  push.[^assessment]
- **Mitigation:** already decided in the plan: Phase 1 adds a `push` trigger for every branch.[^plan]

### [ARCH-06] What each snippet needs from its runtime
- **Severity:** low
- **Location:** `web/.nvmrc` (`26`), `uv.lock:466` (`python-dotenv`), `rust/Cargo.lock` (no
  dependency)
- **Reproduction:** `node --version` prints `v22.22.0` and
  `node -e 'console.log(typeof process.loadEnvFile)'` prints `function`; Node's documentation gives
  `process.loadEnvFile` as added in v21.7.0 and v20.12.0[^node-process];
  `.venv/bin/python -c 'import cryptography'` fails with `ModuleNotFoundError`;
  `.venv/bin/python -c 'import dotenv'` succeeds
- **Impact on the project:** the Node snippet runs on Node 20.12 and later, not on every Node with
  `fetch`; the Python snippet needs `cryptography` added; the Rust snippet needs an HTTP client with
  TLS, AES-GCM, base64, JSON and `dotenvy`, each pinned, inside 25 lines.
- **Mitigation:** the site states each minimum version and the troubleshooting page covers a
  runtime that is too old; Phase 1 adds `cryptography`; Phase 10 pins the crates.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^qrypt-sdk]: Qrypt SDK documentation
[^profile]: The audit's profile of Qrypt's documented contract
[^node-process]: Node.js process API
[^assessment]: The assessment's full text
[^plan]: The plan
