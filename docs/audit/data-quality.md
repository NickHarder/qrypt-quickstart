---
type: Audit Area
title: "Audit area: data quality"
description: The quality of the data a first-time developer or agent reads, Qrypt's documented contract and its examples, profiled by a committed script, with what is wrong, what is missing, what cannot be found and what agrees with the brief.
tags: [audit, data-quality]
status: stable
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
  - id: partner-notes
    resource: /brief/partner-notes.md
    title: Partner notes on Qrypt
verified:
  - { by: human:nickharder, at: 2026-10-20T21:46:34Z }
approved_sha256: 0103256ab05579690cec294546cc99777af91be17046daadd92a26b4f5fa8522
---

# What this area had to answer

The project holds no dataset. The data a first run depends on is Qrypt's documentation: the
contract (endpoint, unit, range, headers, statuses) and the four examples a developer or an agent
copies. Null rates and orphans become, here: what the page leaves out, what its examples get wrong,
what an agent cannot find, and where it agrees with the brief. The probes:

1. Confirm, example by example, which headers each sends.
2. Confirm whether each example checks the status before reading the body.
3. Confirm that each example runs once its placeholders are filled in as the page says.
4. Confirm how a developer gets a token, as the page tells it.
5. Confirm what an agent finds at `llms.txt`, `robots.txt` and the sitemap.
6. Confirm which facts of the brief's quick reference the page states.

# The profile

[`qrypt_docs_profile.py`](qrypt_docs_profile.py) is the committed, re-runnable profile. It reads
docs.qrypt.com only, never the API, and prints one line per fact with the page's SHA-256, so a later
run shows whether Qrypt changed the page.

```bash
python3 -I docs/audit/qrypt_docs_profile.py                          # live, read only
python3 -I docs/audit/qrypt_docs_profile.py --page-file saved.html   # offline, from a saved page
```

It ran on 2026-10-20 at 00:12 UTC, live and then from the saved page; both gave page text sha256
`3cbfd11ef6d15442d8cd78f23150527c727c780ca2ea965716a52104677807dd`. Its output:

```text
Quantum Entropy page status: 200
size range stated: True
size default stated as 1: True
size unit is KiB: True
Accept header in the request table: True
Accept header in each example: Curl=no, PowerShell=no, Python=no, JavaScript=yes
error statuses listed: 400, 401, 403, 429, 500, 503
rate limit 30 per 10 seconds: True
Retry-After mentioned: False
error body shape documented: False
status for a missing Accept stated: False
allotment amount stated: False
region subdomains: api-eus
token obtained by contacting Qrypt: True
portal registration linked: False
Python example writes the token in source: True
Python example prints every entropy byte: True
Python example checks the status: False
JavaScript example checks the status: False
JavaScript size placeholder spelled { kib_entropy }: True
PowerShell reads response.random without $: True
NIST, SP 800-22 or ESV mentioned: False
words 'truly random' on the page: True
llms.txt status: 404
robots.txt status: 404
sitemap hosts: http://localhost:1313
SDK quickstart pages in the sitemap: /sdk/quickstarts/cpp/
SDK page names a 'Qrypt SDK': True
```

# Findings

### [DQ-01] Three of the four examples leave out the header the page requires
- **Severity:** high
- **Location:** docs.qrypt.com/eaas/, the Curl, PowerShell and Python examples[^qrypt-eaas]
- **Reproduction:** the profile prints `Accept header in the request table: True` and
  `Accept header in each example: Curl=no, PowerShell=no, Python=no, JavaScript=yes`[^profile]
- **Impact on the project:** the brief lists "wrong header" as an agent failure and requires both
  headers.[^assessment] An agent that copies Qrypt's curl or Python example sends one; what the
  service answers then is unknown (ARCH-01).
- **Mitigation:** every snippet and every command on the site sends both headers, the mock's tests
  check both, and the agent-contract eval case fails a program that sends one. The claims table
  records the omission with this page as its source.

### [DQ-02] No example checks the status before reading the body
- **Severity:** medium
- **Location:** docs.qrypt.com/eaas/, the Python (`response.json()['random']`) and JavaScript
  (`.then((response) => response.json())`) examples[^qrypt-eaas]
- **Reproduction:** the profile prints `Python example checks the status: False` and
  `JavaScript example checks the status: False`[^profile]; reading `random` from an error body, as
  the Python example does, fails:
  `python3 -I -c "body={'error':'Unauthorized'}; body['random']"` raises `KeyError: 'random'`
- **Impact on the project:** a 401, 429 or 503 surfaces as a stack trace, which the brief rules
  out,[^assessment] and the developer never sees the status the troubleshooting page is keyed on.
- **Mitigation:** each snippet checks the status first and prints the troubleshooting entry for it;
  Phase 3 tests every documented status and a 200 with an unexpected body.

### [DQ-03] Two examples fail as written once their placeholders are filled in
- **Severity:** low
- **Location:** docs.qrypt.com/eaas/, the JavaScript example (`let kibData = { kib_entropy };`) and
  the PowerShell example (`response.random | foreach`)[^qrypt-eaas]
- **Reproduction:** the profile prints `JavaScript size placeholder spelled { kib_entropy }: True`
  and `PowerShell reads response.random without $: True`[^profile]. The page says to replace
  `{kib_entropy}`, which does not match the spaced form, and the line left as it is fails:
  `node -e 'let kibData = { kib_entropy };'` prints `ReferenceError: kib_entropy is not defined`.
  PowerShell is not installed here, so its line was read, not run.
- **Impact on the project:** a developer who starts from Qrypt's JavaScript gets an error before the
  first request; it is evidence for the backlog, and a reason the site's commands run in CI.
- **Mitigation:** Phase 5's test runs every shell block on the site against the mock; the backlog
  can propose the fix to Qrypt's page.

### [DQ-04] The page has no self-service path to a token
- **Severity:** high
- **Location:** docs.qrypt.com/eaas/ ("This service requires an access token. Please contact us to
  obtain one.")[^qrypt-eaas]
- **Reproduction:** the profile prints `token obtained by contacting Qrypt: True` and
  `portal registration linked: False`[^profile]
- **Impact on the project:** the funnel's second stage, "token created", has no documented
  self-service step: the brief names `portal.qrypt.com/register`,[^assessment] the page names a
  contact form, and the partner notes record one attempt where the portal did not load.[^partner-notes]
  The owner has no token yet, so every live phase waits on a person.
- **Mitigation:** the quickstart gives both routes (the portal, and asking Qrypt or the program
  contact) without claiming the portal works; the PRD measures stage 2 as its own stage, with its
  drop-off named as a risk; the plan's fallback (agent rounds against the mock) stands if no token
  comes by 2026-10-20 18:00 CDT.

### [DQ-05] An agent finds no index of Qrypt's docs
- **Severity:** medium
- **Location:** `https://docs.qrypt.com/llms.txt`, `/robots.txt`, `/sitemap.xml`
- **Reproduction:** the profile prints `llms.txt status: 404`, `robots.txt status: 404` and
  `sitemap hosts: http://localhost:1313`[^profile]; `getent hosts docs.qrypt.com` shows the site is
  served from `qryptinc.github.io`
- **Impact on the project:** an agent has only the HTML page to go on, and a crawler that follows the
  sitemap is sent to `localhost`. This project's `llms.txt` becomes the only agent-readable
  description of the service, so its accuracy carries the agent-readiness score.
- **Mitigation:** Phase 4 builds `llms.txt` and `llms-full.txt` from the same snippet files the tests
  run; the backlog can propose a pull request to Qrypt's public docs repository for both fixes.

### [DQ-06] The page leaves the allotment and the answer's checks to the reader
- **Severity:** medium
- **Location:** docs.qrypt.com/eaas/, the 403 row and the sentence that the response's `size`
  "should match" the request[^qrypt-eaas]
- **Reproduction:** the profile prints `allotment amount stated: False`[^profile]; the page's
  response section says the array size "should match the kib_entropy value specified"
- **Impact on the project:** the 10,240 KiB assessment budget may exceed the account's allotment,
  and a 403 is the first sign of it.[^assessment] A 200 whose `random` is empty or short would give
  a snippet fewer than 44 bytes for the key and the nonce.
- **Mitigation:** the live ledger (Phase 7) is the project's own count (CMP-03); each snippet checks
  that it decoded at least 1,024 bytes before taking the key, and exits with its own message if not.

### [DQ-07] Where the page and the brief agree, and what the page does not claim
- **Severity:** info
- **Location:** docs.qrypt.com/eaas/[^qrypt-eaas]; the brief's Qrypt Quick Reference[^assessment]
- **Reproduction:** the profile prints `True` for the range 1 to 512, the default of 1, the KiB unit,
  the `Accept` header in the request table and the 30-per-10-seconds limit, lists all six error
  statuses, prints `NIST, SP 800-22 or ESV mentioned: False` and
  `words 'truly random' on the page: True`[^profile]
- **Impact on the project:** every fact of the brief's quick reference has a source on Qrypt's page,
  for the claims table. Certification claims have none there, and "truly random" is Qrypt's own
  wording.
- **Mitigation:** the site cites this page for each contract fact; it makes no certification claim
  unless Phase 5 finds a page Qrypt or NIST publishes; it quotes "truly random" only as Qrypt's
  words, with the source.

[^qrypt-eaas]: Qrypt Quantum Entropy documentation
[^profile]: The audit's profile of Qrypt's documented contract
[^assessment]: The assessment's full text
[^partner-notes]: Partner notes on Qrypt
