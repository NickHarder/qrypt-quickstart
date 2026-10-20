# Qrypt Quickstart: an AES-256 key from Qrypt quantum entropy

> How to generate an AES-256 key from Qrypt's Quantum Entropy REST API in a new project, in Python, Node.js or Rust, with no SDK: one request for 1 KiB of entropy, a key proven with AES-GCM, and the key never printed.

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
- Python 3.10 or later needs two packages, installed in a virtual environment in the project folder: `python3 -m venv .venv`, then `.venv/bin/pip install cryptography python-dotenv`, and run with `.venv/bin/python quickstart.py`; add `.venv/` to `.gitignore`. A system Python often refuses a bare `pip install` with `externally-managed-environment` (PEP 668). Node.js 20.12 or later needs nothing. Rust 1.89 or later needs five crates: `cargo add aes-gcm@0.11.1 base64@0.23.1 dotenvy@0.15.7 serde_json@1.0.151` and `cargo add ureq@3.4.2 -F platform-verifier`.

## Docs

- [Quickstart, with complete Python, Node.js and Rust programs](llms-full.txt): the rules, the three programs and every error message, in one file
- [Quickstart page](index.html): the same path for people, with language tabs and copy buttons
- [Troubleshooting](troubleshooting.html): every message the quickstart can print, its cause and its fix

## Optional

- [Qrypt's API reference](https://docs.qrypt.com/eaas/): the upstream documentation of the endpoint
