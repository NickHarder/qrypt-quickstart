"""Make an AES-256 key from 1 KiB of Qrypt quantum entropy, and prove it works with AES-GCM.

Setup:  pip install cryptography python-dotenv
        put QRYPT_API_KEY=<your Entropy token> in a .env file next to this script
Run:    python quickstart.py

The key is never printed, logged or written to disk: it lives only in this process's memory.
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
    sys.exit("Set QRYPT_API_KEY=<token> in a .env file. Get an Entropy token: portal.qrypt.com")
# QRYPT_API_URL points the script at a local mock for testing; unset, it calls Qrypt.
api_url = os.environ.get("QRYPT_API_URL", "https://api-eus.qrypt.com/api/v1/quantum-entropy")
headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
# size is in KiB (1,024-byte blocks), not bytes: size=1 returns 1,024 bytes, plenty for one key.
request = urllib.request.Request(f"{api_url}?size=1", headers=headers)
request.add_header("User-Agent", "qrypt-quickstart-python/1.0")
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        entropy_bytes = base64.b64decode(json.load(response)["random"][0])
except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as failure:
    sys.exit(f"Could not get entropy from Qrypt ({failure}). See the troubleshooting page.")

# Bytes 0-31 are the key and bytes 32-43 the nonce: never reuse entropy bytes for two purposes.
aes_key, nonce = entropy_bytes[:32], entropy_bytes[32:44]
sample_text = b"Hello from Qrypt quantum entropy"
ciphertext = AESGCM(aes_key).encrypt(nonce, sample_text, None)
if AESGCM(aes_key).decrypt(nonce, ciphertext, None) != sample_text:
    sys.exit("The AES-GCM round trip did not match: do not use this key.")
print("Success: a 256-bit AES key from Qrypt quantum entropy passed AES-GCM. It was not shown.")
