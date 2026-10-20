# Qrypt Quickstart: an AES-256 key from Qrypt quantum entropy (full version)

> Everything an AI coding agent needs to generate an AES-256 key from Qrypt's Quantum Entropy REST API in a new project: the rules, complete Python, Node.js and Rust programs, and every error message with its fix. Target: a working key in under 10 minutes.

## Rules for AI coding agents

- No SDK: Qrypt's documentation lists no Python or Node.js package for this API (its SDK is a C/C++ library for key generation). Do not install one (no `pip install qrypt`, no `npm install qrypt`); call the REST endpoint with the language's own HTTP client.
- Endpoint: `GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size=1`
- Headers, both required: `Accept: application/json` and `Authorization: Bearer <QRYPT_API_KEY>`.
- Also send a `User-Agent` that names your program (the quickstart sends `qrypt-quickstart-python/1.0`): Cloudflare in front of the API refuses an HTTP library's default one, such as `Python-urllib/3.x`, with 403 `Error 1010: Access denied` before the token is read.
- `size` counts KiB (1,024-byte blocks), from 1 to 512, not bytes. Send `size=1`: it returns 1,024 bytes, and one key needs 32.
- Token: read `QRYPT_API_KEY` from a `.env` file in the project folder, or from the environment. Never hard-code, print or commit it; add `.env` to `.gitignore`. If it is missing, stop and tell the user to get an Entropy token at https://portal.qrypt.com/trial?ref=quickstart and put `QRYPT_API_KEY=<token>` in `.env`.
- Answer: `{"random": ["<base64 of 1,024 bytes>"], "size": 1}`. Base64-decode `random[0]` first; then bytes 0-31 are the AES-256 key and bytes 32-43 the AES-GCM nonce. Never reuse entropy bytes for two purposes.
- Never print, log or write the key to disk. Prove it works by encrypting and decrypting a sample string with AES-GCM, and print only a success line.
- Errors: make one request and stop; never retry in a loop. 429 means requests came too close together (Qrypt's docs say over 30 in 10 seconds; a trial key was refused at two within half a second): wait 10 seconds. 403 means a wrong token or a used-up entropy allotment: Qrypt's docs say 401 for a bad token, but Qrypt answers a wrong token with 403 and the same body as a used-up allotment, so check `QRYPT_API_KEY` first, then ask Qrypt; waiting does not help. 401 means the token is invalid or expired. 500 and 503: try again shortly.
- On any failure, exit non-zero with one clear line, not a stack trace.
- Python: install the packages in a virtual environment in the project folder, never into the system Python: `python3 -m venv .venv`, then `.venv/bin/pip install cryptography python-dotenv`, and run with `.venv/bin/python quickstart.py`; add `.venv/` to `.gitignore`. A system Python often refuses a bare `pip install` with `externally-managed-environment` (PEP 668).

## Step 1: the token

Put the token in a file named `.env` in the project folder, and add `.env` to `.gitignore`:

```text
QRYPT_API_KEY=paste-your-token-here
```

## Step 2, Python: quickstart.py

Python 3.10 or later. Install the two packages, save the program as `quickstart.py`, and run it. If `pip` refuses with `externally-managed-environment`, or for an agent working in a fresh project, use a virtual environment instead: `python3 -m venv .venv`, `.venv/bin/pip install cryptography python-dotenv`, `.venv/bin/python quickstart.py`, with `.venv/` in `.gitignore`.

```shell
pip install cryptography python-dotenv
python quickstart.py
```

```python
<!-- include: quickstart/python/quickstart.py -->```

## Step 2, Node.js: quickstart.mjs

Node.js 20.12 or later; nothing to install. Save the program as `quickstart.mjs`, and run it:

```shell
node quickstart.mjs
```

```javascript
<!-- include: quickstart/node/quickstart.mjs -->```

## Step 2, Rust: src/main.rs

Rust 1.89 or later. Make a project, add five crates, save the program over `src/main.rs`, put `.env` in the project's folder, and run it:

```shell
cargo new qrypt-key && cd qrypt-key
cargo add aes-gcm@0.11.1 base64@0.23.1 dotenvy@0.15.7 serde_json@1.0.151
cargo add ureq@3.4.2 -F platform-verifier
cargo run
```

```rust
<!-- include: rust/src/main.rs -->```

## Step 3: what success looks like

```text
Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).
```

## Every error message, its cause and its fix

Each program makes one request and prints one line on failure, with a non-zero exit code.

- `Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)`: there is no `.env` with a `QRYPT_API_KEY` line in the folder the program ran from. Create it there.
- `Qrypt answered HTTP 400: malformed request: size must be 1-512.`: the request is malformed; send `size` as a whole number from 1 to 512, with both headers.
- `Qrypt answered HTTP 401: the token is invalid or expired; get a new one at portal.qrypt.com.`: generate a new Entropy token and replace the `QRYPT_API_KEY` line, with no quotes or spaces.
- `Qrypt answered HTTP 403: wrong token or allotment spent.`: most likely a wrong token (mistyped, cut short, or from another account), which Qrypt answers with 403 `{"error": "Forbidden or entropy quota reached"}` although its docs say 401; check `QRYPT_API_KEY` against the portal's API Keys page. Otherwise the account has retrieved its maximum entropy for the period. Stop; waiting does not help. Ask Qrypt to change the limit.
- `Error 1010: Access denied` (HTTP 403, a JSON body from Cloudflare, not Qrypt): the request carried an HTTP library's default `User-Agent`, such as `Python-urllib/3.x`, which Cloudflare refuses before the token is read. Send a `User-Agent` that names your program; the token is not the problem.
- `Qrypt answered HTTP 429: too many requests in a short time; wait 10 seconds, then run once.`: the rate limit. Wait 10 seconds, then run once; never retry in a loop.
- `Qrypt answered HTTP 500: try again shortly.`: an error inside Qrypt. Run again in a minute; if it persists, contact Qrypt support.
- `Qrypt answered HTTP 503: try again shortly.`: Qrypt's entropy supply is temporarily insufficient. Run again in a minute with `size=1`.
- `Could not get entropy (...)`: no network, a timeout, a proxy, or a certificate the machine does not trust. Behind a TLS-inspecting proxy, point the runtime at the company's root certificate: `SSL_CERT_FILE=/path/to/company-ca.pem` for Python, `NODE_EXTRA_CA_CERTS=/path/to/company-ca.pem` for Node.js; the Rust program trusts the operating system's certificates, and `SSL_CERT_FILE` on Linux. Never turn certificate checks off.

More detail: [Troubleshooting](troubleshooting.html). Qrypt's own reference: [docs.qrypt.com/eaas](https://docs.qrypt.com/eaas/).
