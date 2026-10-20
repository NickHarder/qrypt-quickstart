# Qrypt Quickstart: an AES-256 key from Qrypt quantum entropy (full version)

> Everything an AI coding agent needs to generate an AES-256 key from Qrypt's Quantum Entropy REST API in a new project: the rules, a complete Python program, a complete Node.js program, and every error message with its fix. Target: a working key in under 10 minutes.

## Rules for AI coding agents

- No SDK: Qrypt publishes no Python or Node.js package for this API. Do not install one (no `pip install qrypt`, no `npm install qrypt`); call the REST endpoint with the language's own HTTP client.
- Endpoint: `GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size=1`
- Headers, both required: `Accept: application/json` and `Authorization: Bearer <QRYPT_API_KEY>`.
- `size` counts KiB (1,024-byte blocks), from 1 to 512, not bytes. Send `size=1`: it returns 1,024 bytes, and one key needs 32.
- Token: read `QRYPT_API_KEY` from a `.env` file in the project folder, or from the environment. Never hard-code, print or commit it; add `.env` to `.gitignore`. If it is missing, stop and tell the user to get an Entropy token at portal.qrypt.com and put `QRYPT_API_KEY=<token>` in `.env`.
- Answer: `{"random": ["<base64 of 1,024 bytes>"], "size": 1}`. Base64-decode `random[0]` first; then bytes 0-31 are the AES-256 key and bytes 32-43 the AES-GCM nonce. Never reuse entropy bytes for two purposes.
- Never print, log or write the key to disk. Prove it works by encrypting and decrypting a sample string with AES-GCM, and print only a success line.
- Errors: make one request and stop; never retry in a loop. 429 means more than 30 requests in 10 seconds: wait 10 seconds. 403 means the account's entropy allotment is used up: waiting does not help. 401 means the token is invalid or expired. 500 and 503: try again shortly.
- On any failure, exit non-zero with one clear line, not a stack trace.

## Step 1: the token

Put the token in a file named `.env` in the project folder, and add `.env` to `.gitignore`:

```text
QRYPT_API_KEY=paste-your-token-here
```

## Step 2, Python: quickstart.py

Python 3.10 or later. Install the two packages, save the program as `quickstart.py`, and run it:

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

## Step 3: what success looks like

```text
Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).
```

## Every error message, its cause and its fix

Each program makes one request and prints one line on failure, with a non-zero exit code.

- `Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)`: there is no `.env` with a `QRYPT_API_KEY` line in the folder the program ran from. Create it there.
- `Qrypt answered HTTP 400: malformed request: size must be 1-512.`: the request is malformed; send `size` as a whole number from 1 to 512, with both headers.
- `Qrypt answered HTTP 401: the token is invalid or expired; get a new one at portal.qrypt.com.`: generate a new Entropy token and replace the `QRYPT_API_KEY` line, with no quotes or spaces.
- `Qrypt answered HTTP 403: allotment used up; ask Qrypt.`: the account has retrieved its maximum entropy for the period. Stop; waiting does not help. Ask Qrypt to change the limit.
- `Qrypt answered HTTP 429: over 30 requests in 10 seconds; wait 10 seconds, then run once.`: the rate limit. Wait 10 seconds, then run once; never retry in a loop.
- `Qrypt answered HTTP 500: try again shortly.`: an error inside Qrypt. Run again in a minute; if it persists, contact Qrypt support.
- `Qrypt answered HTTP 503: try again shortly.`: Qrypt's entropy supply is temporarily insufficient. Run again in a minute with `size=1`.
- `Could not get entropy (...)`: no network, a timeout, a proxy, or a certificate the machine does not trust. Behind a TLS-inspecting proxy, point the runtime at the company's root certificate: `SSL_CERT_FILE=/path/to/company-ca.pem` for Python, `NODE_EXTRA_CA_CERTS=/path/to/company-ca.pem` for Node.js. Never turn certificate checks off.

More detail: [Troubleshooting](troubleshooting.html). Qrypt's own reference: [docs.qrypt.com/eaas](https://docs.qrypt.com/eaas/).
