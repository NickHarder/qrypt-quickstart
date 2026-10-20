# Claims to sources

Every factual claim the quickstart site and the PRD make about Qrypt, quoted word for word, with the page it
is on and the source it rests on. `tests/test_claims.py` holds this table and the site to each
other: a quote no longer on its page fails, a Qrypt fact on the site that no row quotes fails, and a
marketing superlative ("unbreakable", "perfectly secure" and others) anywhere on the site fails.

## Sources

| Short name | Source | Read |
|---|---|---|
| EaaS | Qrypt Quantum Entropy documentation, https://docs.qrypt.com/eaas/ | 2026-10-19 |
| SDK | Qrypt SDK quickstarts and overview, https://docs.qrypt.com/sdk/quickstarts/ and https://docs.qrypt.com/sdk/overview/ | 2026-10-20 |
| Brief | The assessment's Qrypt Quick Reference (the partner's own statement of the service) | 2026-10-19 |
| Live | The owner's trial key against `api-eus`, 2026-10-20: `evidence/live_rate_limit.json` and `evidence/live_runs.csv` | 2026-10-20 |
| Snippets | What the quickstart programs do, proved by the tests named in the row | Every commit |

## Claims about Qrypt

| Id | Claim, as the site says it | Page | Source |
|---|---|---|---|
| Q-01 | Endpoint: GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size=1 | `site/llms.md` | EaaS: the endpoint and its `size` parameter |
| Q-02 | Headers, both required: Accept: application/json and Authorization: Bearer <QRYPT_API_KEY>. | `site/llms.md` | EaaS: the two required headers |
| Q-03 | size counts KiB (1,024-byte blocks), from 1 to 512, not bytes. Send size=1: it returns 1,024 bytes, and one key needs 32. | `site/llms.md` | EaaS: `size` is KiB, 1 to 512; an AES-256 key is 32 bytes |
| Q-04 | Answer: {"random": ["<base64 of 1,024 bytes>"], "size": 1}. | `site/llms.md` | EaaS: the response holds base64 blocks of 1,024 bytes and the size |
| Q-05 | No SDK: Qrypt's documentation lists no Python or Node.js package for this API (its SDK is a C/C++ library for key generation). | `site/llms.md` | SDK: the only SDK listed is "Qrypt SDK for C/C++", under Key Generation |
| Q-06 | Get an access token for the Entropy service from the Qrypt portal at portal.qrypt.com/trial. | `site/index.html` | EaaS: tokens are generated in the Qrypt portal; Brief: "create an account at https://portal.qrypt.com/register and generate an access token for the Entropy service"; but the portal, rendered in a browser on 2026-10-20, shows /register as a 404, and its login page's "Create trial account" leads to /trial (full name and work email), so the link goes there. The link's `ref=quickstart` is this project's tag for the PRD's attribution, not a Qrypt feature |
| Q-07 | One run uses 1 KiB of your entropy allotment. | `site/index.html` | Brief: "One quickstart run uses 1 KiB"; Snippets: `size=1`, one request (`tests/test_quickstart_python.py`, `tests/test_quickstart_node.py`) |
| Q-08 | Qrypt reads the request as a malformed URL or invalid parameters, such as a size outside 1 to 512 or not a whole number. | `site/troubleshooting.html` | EaaS: 400 is a malformed URL or invalid parameters; `size` is 1 to 512 |
| Q-09 | Send both headers Qrypt's documentation requires, Accept: application/json and Authorization: Bearer <token>. | `site/troubleshooting.html` | EaaS: the two required headers |
| Q-10 | the access token is invalid or has expired. | `site/troubleshooting.html` | EaaS: 401, access token invalid or expired |
| Q-11 | Qrypt answered HTTP 401: the token is invalid or expired; get a new one at portal.qrypt.com. | `site/troubleshooting.html` | EaaS: 401 and the portal; Snippets: the message both programs print (`tests/test_quickstart_errors.py`) |
| Q-12 | generate a new access token for the Entropy service in the Qrypt portal (portal.qrypt.com) | `site/troubleshooting.html` | EaaS: tokens are generated in the portal; Brief: the Entropy service |
| Q-13 | the account has retrieved its maximum entropy allotment for the current period. | `site/troubleshooting.html` | EaaS: 403, limit reached for the current period |
| Q-14 | Ask Qrypt to change the account's limit. | `site/troubleshooting.html` | EaaS: 403, contact Qrypt to change the limit |
| Q-15 | Qrypt's docs say the limit is 30 requests in 10 seconds, but a trial key was refused for a second request 0.36 s after its first. Qrypt's answer has no Retry-After header. | `site/troubleshooting.html` | EaaS: 429, 30 requests per 10-second interval per token; Live: a 429 at 0.36 s after a 200, with no `Retry-After`, and every 429 cleared within 1.5 s |
| Q-37 | Requests: 30 per 10 seconds per token, Qrypt's docs say; a trial key was refused at two within half a second | `site/troubleshooting.html` | EaaS: the 30-in-10-seconds limit; Live: the same 429 |
| Q-16 | Qrypt answered HTTP 429: too many requests in a short time; wait 10 seconds, then run once. | `site/troubleshooting.html` | EaaS: the 429 status; Live: every 429 cleared within 1.5 s, so 10 seconds is ample; Snippets: the message the three programs print |
| Q-17 | ask for more in one request (up to 512 KiB) | `site/troubleshooting.html` | EaaS: at most 512 KiB per request |
| Q-18 | an error inside Qrypt's service, not in your request. | `site/troubleshooting.html` | EaaS: 500, internal server error; contact Qrypt support |
| Q-19 | Qrypt's entropy supply is temporarily insufficient. | `site/troubleshooting.html` | EaaS: 503, not enough supply; retry later |
| Q-20 | a firewall that blocks api-eus.qrypt.com | `site/troubleshooting.html` | EaaS: the endpoint's host |
| Q-21 | Qrypt reads it as 32 KiB: 32 blocks of 1,024 bytes. | `site/troubleshooting.html` | EaaS: `size` is KiB |
| Q-22 | 429 means requests came too close together (Qrypt's docs say over 30 in 10 seconds; a trial key was refused at two within half a second): wait 10 seconds. 403 means the account's entropy allotment is used up: waiting does not help. 401 means the token is invalid or expired. | `site/llms.md` | EaaS: 429, 403 and 401; Live: a trial key refused with 429 at 0.36 s after a 200 |
| Q-23 | the account has retrieved its maximum entropy for the period. | `site/llms-full.md` | EaaS: 403 |
| Q-24 | Qrypt's entropy supply is temporarily insufficient. | `site/llms-full.md` | EaaS: 503 |

## Claims about Qrypt in the PRD

| Id | Claim, as the PRD says it | Page | Source |
|---|---|---|---|
| Q-29 | Three of Qrypt's four code examples leave out the Accept: application/json header that the same page says is required. | `PRD.md` | EaaS: the curl, Python and PowerShell examples send no `Accept`; the JavaScript example does |
| Q-30 | None checks the HTTP status before reading the body, and the Python example puts the token in source code and prints every entropy byte. | `PRD.md` | EaaS: the four examples, as read 2026-10-19 (`docs/audit/data-quality.md`, `docs/audit/security.md`) |
| Q-31 | A developer who asks for size=32 to get a 32-byte key gets 32 KiB | `PRD.md` | EaaS: `size` is KiB |
| Q-32 | (the only SDK is C/C++, for key generation) | `PRD.md` | SDK |
| Q-33 | There is no llms.txt at docs.qrypt.com (HTTP 404), and no self-service step to a token is documented: the page says to contact Qrypt. | `PRD.md` | `curl` of docs.qrypt.com/llms.txt, HTTP 404 on 2026-10-19; EaaS: tokens come from contacting Qrypt |
| Q-34 | Qrypt sells quantum entropy as one REST endpoint. | `PRD.md` | EaaS: one endpoint, `GET /api/v1/quantum-entropy` |
| Q-36 | In the portal's side bar, under Dashboard, open API Keys, then Create API key. | `site/index.html` | The owner's walk of the portal, 2026-10-20 (`evidence/portal_walkthrough.md`, steps 4 and 5) |
| Q-35 | Cloudflare in front of the API may refuse some HTTP clients with a 403 | `PRD.md` | `docs/audit/architecture.md`: the API answers through Cloudflare, and another Cloudflare-fronted site refused Python's default client; "may" until the live check |

## Claims about the tools the quickstart uses

| Id | Claim, as the site says it | Page | Source |
|---|---|---|---|
| Q-25 | Node.js 20.12 or later. Nothing to install: fetch and node:crypto are built in. | `site/index.html` | Node.js documentation: `process.loadEnvFile` (added in 20.12), `fetch` and `node:crypto` in the core; Snippets: the Node tests run the program with no package installed |
| Q-26 | If you must go through a proxy, Python and the Rust program read HTTPS_PROXY on their own. | `site/troubleshooting.html` | Python documentation: `urllib.request` reads proxy settings from the environment (`getproxies`); ureq 3.4.2's source: its default configuration reads `HTTPS_PROXY` and `NO_PROXY` (`Proxy::try_from_env`) |
| Q-27 | Recent Node.js versions read it when started with --use-env-proxy (see node --help). | `site/troubleshooting.html` | `node --help` of Node.js 22.22.0 lists `--use-env-proxy`; checked 2026-10-20 |
| Q-28 | point the runtime at it. Never turn certificate checks off. | `site/troubleshooting.html` | Python documentation: OpenSSL's default trust store honours `SSL_CERT_FILE`; Node.js documentation: `NODE_EXTRA_CA_CERTS` |

## Fact-check of AI-drafted content

The research blueprint and the design screenshots were drafted by an AI research tool, and this
project's own pages were drafted with an AI coding agent (`AI_USAGE.md`). Every claim from those
drafts that reached, or could have reached, the site or the PRD was checked against a source before
use. `docs/brief/research-review.md` started this list.

**24 AI-drafted claims checked: 3 verified, 1 relabelled as an assumption, 20 corrected or dropped**

| Id | AI-drafted claim | Where it came from | Verdict |
|---|---|---|---|
| A-01 | A missing `Accept` header gives a 401 | Screenshot 1 | Dropped: Qrypt's docs name no status for it |
| A-02 | A missing `Accept` header gives a 400 or 406 | Screenshot 3, blueprint | Dropped: unsourced; the mock's 400 is marked as the mock's own guess |
| A-03 | The token is read from `process.env.QRYPT_TOKEN` | Screenshot 3 | Corrected: `QRYPT_API_KEY` |
| A-04 | `byte_count: 64` and `"64kb"` | Screenshot 3 | Corrected: `size` is an integer count of KiB; the programs send `size=1` |
| A-05 | Ship PowerShell and cURL "SDK snippets" | Screenshot 5 | Dropped: the brief's languages are Python, Node, Go, Rust and C++ |
| A-06 | Stage 3's event joined on `account_id + token_hash`, and on `token_id_hash` | Screenshot 4, blueprint | Corrected: one spec, joined on the account (`docs/KEY_METRICS.md`) |
| A-07 | Effort in months, and in person-weeks | Screenshot 5, blueprint | Corrected: one unit, person-weeks |
| A-08 | Round 2 will "typically" be 5/5 with a median under 2 minutes | Blueprint | Dropped: a prediction; the result comes from the runs |
| A-09 | The backlog's evidence cites Round 2 results | Blueprint | Dropped: the backlog is scored after both rounds |
| A-10 | Qrypt's curl, Python and PowerShell examples omit `Accept` | Blueprint, partner notes | Verified on docs.qrypt.com/eaas, 2026-10-19 |
| A-11 | `docs.qrypt.com/llms.txt` returns 404 | Blueprint, partner notes | Verified: HTTP 404, 2026-10-19 |
| A-12 | `size` defaults to 1 | Blueprint | Verified on docs.qrypt.com/eaas, 2026-10-19 |
| A-13 | The entropy is tested against NIST SP 800-22 under ESV certificate E246 | Blueprint | Dropped from the site: not on Qrypt's EaaS page |
| A-14 | The portal "frequently fails to load or blocks self-service signups" | Blueprint | Dropped: one observation in the partner notes |
| A-15 | Lighthouse added an "Agentic Browsing" `llms.txt` audit in May 2026 | Blueprint | Dropped: not checked, and nothing depends on it |
| A-16 | qseed injects 48 bytes through `C_SeedRandom`; rng-tools feeds `/dev/random` | Blueprint | Dropped: not checked, and nothing on the site depends on it |
| A-17 | A 45-minute baseline and 25% activation | Blueprint, screenshot 4 | Relabelled: the brief's own assumptions, called that wherever they appear |
| A-18 | The snippets and `llms.txt` capture "over 90% of the TTFK reduction" | Blueprint | Dropped: no source |
| A-19 | Official SDKs would take "6 to 8 engineering weeks" | Blueprint | Dropped: no source |
| A-20 | Benchmarks from Stripe, Twilio, Vercel and ReadMe | Blueprint | Dropped: no source |
| A-21 | Node.js 18 and Python 3.10 are enough | Blueprint | Corrected: the Node program needs 20.12 (`process.loadEnvFile`) |
| A-22 | A 400 can mean a missing `Accept` header | Blueprint's troubleshooting table | Corrected: the page gives Qrypt's own 400 cause |
| A-23 | "Qrypt publishes no Python or Node.js package for this API" | This project's draft of `llms.txt` | Corrected: Qrypt's documentation lists none; its SDK is C/C++, for key generation |
| A-24 | A 400 is "most often" a `size` out of range | This project's draft of the troubleshooting page | Corrected: Qrypt's wording, a malformed URL or invalid parameters |
