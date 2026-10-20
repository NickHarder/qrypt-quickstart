---
type: Audit Area
title: "Audit area: performance"
description: What bounds the quickstart's 3-second runtime and the agent's 10-minute target, from Qrypt's one documented region, its rate limit, the size of its answer and the cost of starting each runtime.
tags: [audit, performance]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:20:00Z }
sources:
  - id: qrypt-eaas
    resource: https://docs.qrypt.com/eaas/
    title: Qrypt Quantum Entropy documentation, read 2026-10-20, page text sha256 3cbfd11e
  - id: profile
    resource: qrypt_docs_profile.py
    title: The audit's profile of Qrypt's documented contract
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
---

# What this area had to answer

Where the first run is slow, the shape and volume of the data, and what bounds the latency the brief
sets: a snippet under 3 s end to end against the live API, a site under 1.5 s p95 on mobile, and an
agent's median time to first key under 10 minutes.[^assessment] The probes:

1. Confirm which regions Qrypt documents, and where the API's host resolves.
2. Confirm the rate limit and whether Qrypt says how long to wait after a 429.
3. Confirm the size of the answer to `size=1`.
4. Measure what the local runtimes cost before the first byte is sent.

The API's own latency was not measured: that needs a live call, which waits on the token
(Phase 7).

# Findings

### [PERF-01] One documented region; the 3-second target rests on an unmeasured round trip
- **Severity:** medium
- **Location:** docs.qrypt.com/eaas/, the subdomain table (one row, `api-eus`, Eastern United
  States)[^qrypt-eaas]
- **Reproduction:** `python3 -I docs/audit/qrypt_docs_profile.py` prints
  `region subdomains: api-eus`[^profile]; `getent hosts api-eus.qrypt.com` answers with three
  addresses in Cloudflare's ranges (`172.67.69.16`, `104.26.12.71`, `104.26.13.71`, inside
  `172.64.0.0/13` and `104.16.0.0/13` of `https://www.cloudflare.com/ips-v4`)
- **Impact on the project:** the TLS handshake ends at a nearby Cloudflare edge, but each request
  still reaches Qrypt's origin in the Eastern US. Nothing yet shows the snippet meets 3 s from the
  grader's machine, or from the owner's.
- **Mitigation:** Phase 7 times each snippet 5 times live, as planned; the site states the time
  target only with that measurement beside it.

### [PERF-02] 30 requests per 10 s per token, and no word on how long to wait
- **Severity:** medium
- **Location:** docs.qrypt.com/eaas/, the 429 row[^qrypt-eaas]
- **Reproduction:** the profile prints `rate limit 30 per 10 seconds: True` and
  `Retry-After mentioned: False`[^profile]
- **Impact on the project:** a snippet or an agent's program that retries in a loop reaches the
  limit within a second, and then has no documented time to wait. One token serves the owner's runs,
  the demo and every agent run, so a loop in one agent run can fail the next.
- **Mitigation:** the snippets never retry; on 429 they exit at once with "wait 10 seconds", which
  the documented window supports (Phase 3 test: exit within 1 s after one request). Agent runs go
  one after another, never in parallel.

### [PERF-03] The answer to `size=1` is small; the data is not what bounds latency
- **Severity:** info
- **Location:** docs.qrypt.com/eaas/, the response description (one base64 string per 1,024-byte
  block)[^qrypt-eaas]
- **Reproduction:** `python3 -I -c "import base64,json;print(len(json.dumps({'random':[base64.b64encode(bytes(1024)).decode()],'size':1})))"`
  prints `1395` (bytes of JSON for one block)
- **Impact on the project:** the key and the nonce use 44 of the 1,024 bytes; 1 KiB is the smallest
  request, so the snippet cannot ask for less. Payload size plays no part in the 3-second target.
- **Mitigation:** none needed. The snippet sends `size=1`, as the brief requires.

### [PERF-04] Starting each runtime costs well under a tenth of a second
- **Severity:** info
- **Location:** this machine: Python 3.13 (`python3`), Node v22.22.0
- **Reproduction:** `TIMEFORMAT='%R s'; time python3 -I -c 'import ssl, urllib.request, json, base64, hashlib'`
  gives 0.058 to 0.063 s over three runs; `time node -e 'globalThis.crypto.subtle; fetch'` gives
  0.039 to 0.052 s. The import time of `cryptography` was not measured: it is not installed yet.
- **Impact on the project:** almost all of the 3 s budget is the network's (PERF-01).
- **Mitigation:** Phase 1 measures the Python snippet with `cryptography` installed, against the
  mock, so that the live timing in Phase 7 can be split into local and network time.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^profile]: The audit's profile of Qrypt's documented contract
[^assessment]: The assessment's full text
