/**
 * Make an AES-256 key from 1 KiB of Qrypt quantum entropy, and prove it works with AES-GCM.
 *
 * Setup:  Node.js 20.12 or later; nothing to install.
 *         put QRYPT_API_KEY=<your Entropy token> in a .env file in the folder you run this from
 * Run:    node quickstart.mjs
 *
 * The key is never printed, logged or written to disk: it lives only in this process's memory.
 */
import { createCipheriv, createDecipheriv } from "node:crypto";
import { existsSync } from "node:fs";

/** Print a message and stop with a non-zero exit code. @param {string} message @returns {never} */
function exitWith(message) { console.error(message); process.exit(1); }

if (existsSync(".env")) process.loadEnvFile(); // a real environment variable wins over .env
const apiKey = (process.env.QRYPT_API_KEY ?? "").trim();
if (!apiKey) exitWith("Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)");
// QRYPT_API_URL points the script at a local mock for testing; unset, it calls Qrypt.
const apiUrl = process.env.QRYPT_API_URL ?? "https://api-eus.qrypt.com/api/v1/quantum-entropy";
const headers = { Accept: "application/json", Authorization: `Bearer ${apiKey}` };
// size is in KiB (1,024-byte blocks), not bytes: size=1 returns 1,024 bytes, plenty for one key.
const response = await fetch(`${apiUrl}?size=1`, {
  headers: { ...headers, "User-Agent": "qrypt-quickstart-node/1.0" },
  signal: AbortSignal.timeout(10_000),
}).catch((error) => exitWith(`Could not reach Qrypt (${error.message}). Try again shortly.`));
if (!response.ok) exitWith(`Qrypt answered HTTP ${response.status}. See the troubleshooting page.`);
// The answer is {"random": ["<base64 of 1,024 bytes>"], "size": 1}; anything else is refused.
const body = /** @type {{ random?: string[] }} */ (await response.json().catch(() => ({})));
const entropyBytes = Buffer.from(body.random?.[0] ?? "", "base64");
if (entropyBytes.length < 44) exitWith("Qrypt's answer held no entropy. Try again shortly.");

// Bytes 0-31 are the key and bytes 32-43 the nonce: never reuse entropy bytes for two purposes.
const [aesKey, nonce] = [entropyBytes.subarray(0, 32), entropyBytes.subarray(32, 44)];
const sampleText = Buffer.from("Hello from Qrypt quantum entropy");
const cipher = createCipheriv("aes-256-gcm", aesKey, nonce);
const ciphertext = Buffer.concat([cipher.update(sampleText), cipher.final()]);
// authTagLength makes decryption refuse a shortened tag, which GCM would otherwise accept.
const decipher = createDecipheriv("aes-256-gcm", aesKey, nonce, { authTagLength: 16 });
decipher.setAuthTag(cipher.getAuthTag());
const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
if (!decrypted.equals(sampleText)) exitWith("AES-GCM round trip failed: do not use this key.");
console.log("Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).");
