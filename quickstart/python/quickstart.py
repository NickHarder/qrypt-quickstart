"""Make an AES-256 key from 1 KiB of Qrypt quantum entropy, and prove it works with AES-GCM.

Setup:  pip install cryptography python-dotenv
        put QRYPT_API_KEY=<your Entropy token> in a .env file next to this script
Run:    python quickstart.py

The key is never printed, logged or written to disk: it lives only in this process's memory.
Every failure prints one line saying what to do and exits non-zero; nothing is retried in a loop.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()  # reads .env from this script's folder (or a parent); a real env variable wins
api_key = os.environ.get("QRYPT_API_KEY", "").strip()
if not api_key:
    sys.exit("Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)")
# QRYPT_API_URL points the script at a local mock for testing; unset, it calls Qrypt.
api_url = os.environ.get("QRYPT_API_URL", "https://api-eus.qrypt.com/api/v1/quantum-entropy")
headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}",
           "User-Agent": "qrypt-quickstart-python/1.0"}
# What to do about each error Qrypt documents; 500, 503 and any other status: try again shortly.
hints = {400: "malformed request: size must be 1-512", 403: "wrong token or allotment spent",
         401: "the token is invalid or expired; get a new one at portal.qrypt.com",
         429: "too many requests in a short time; wait 10 seconds, then run once"}
# size is in KiB (1,024-byte blocks), not bytes: size=1 returns 1,024 bytes, plenty for one key.
request = urllib.request.Request(f"{api_url}?size=1", headers=headers)
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        entropy_bytes = base64.b64decode(json.load(response)["random"][0])
    # Bytes 0-31 are the key and bytes 32-43 the nonce: never reuse entropy bytes for two purposes.
    aes_gcm, nonce = AESGCM(entropy_bytes[:32]), entropy_bytes[32:44]
except urllib.error.HTTPError as error:
    sys.exit(f"Qrypt answered HTTP {error.code}: {hints.get(error.code, 'try again shortly')}.")
except (OSError, KeyError, IndexError, TypeError, ValueError) as error:  # network, TLS, odd answer
    sys.exit(f"Could not get entropy ({getattr(error, 'reason', error)}): "
             "try again shortly, or see troubleshooting (proxy, TLS).")

sample_text = b"Hello from Qrypt quantum entropy"
ciphertext = aes_gcm.encrypt(nonce, sample_text, None)
if aes_gcm.decrypt(nonce, ciphertext, None) != sample_text:
    sys.exit("AES-GCM round trip failed: do not use this key.")
print("Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).")
