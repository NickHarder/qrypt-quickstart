/**
 * Make an AES-256 key from 1 KiB of Qrypt quantum entropy, and prove it works with AES-GCM.
 *
 * Setup:  Node.js 20.12 or later; nothing to install.
 *         put QRYPT_API_KEY=<your Entropy token> in a .env file in the folder you run this from
 * Run:    node quickstart.mjs
 *
 * The key is never printed, logged or written to disk: it lives only in this process's memory.
 * Every failure prints one line saying what to do and exits non-zero; nothing is retried in a loop.
 */
import { createCipheriv, createDecipheriv } from "node:crypto";
import { existsSync } from "node:fs";

/** Print a message and stop with a non-zero exit code. @param {string} message @returns {never} */
function exitWith(message) { console.error(message); process.exit(1); }
// Any other failure (network, proxy, TLS, an answer without a block) ends here, after one request.
// `any`: a thrown value has no declared type; the code of its cause (ECONNREFUSED...) helps most.
process.on("uncaughtException", (/** @type {any} */ error) => exitWith(`Could not get entropy (${
  error.cause?.code ?? error.message}): try again shortly, or see troubleshooting (proxy, TLS).`));

if (existsSync(".env")) process.loadEnvFile(); // a real environment variable wins over .env
const apiKey = (process.env.QRYPT_API_KEY ?? "").trim();
if (!apiKey) exitWith("Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)");
// QRYPT_API_URL points the script at a local mock for testing; unset, it calls Qrypt.
const apiUrl = process.env.QRYPT_API_URL ?? "https://api-eus.qrypt.com/api/v1/quantum-entropy";
const headers = { Accept: "application/json", Authorization: `Bearer ${apiKey}`,
  "User-Agent": "qrypt-quickstart-node/1.0" };
// What to do about each error Qrypt documents; 500, 503 and any other status: try again shortly.
/** @type {Record<number, string>} */
const hints = { 400: "malformed request: size must be 1-512", 403: "allotment used up; ask Qrypt",
  401: "the token is invalid or expired; get a new one at portal.qrypt.com",
  429: "over 30 requests in 10 seconds; wait 10 seconds, then run once" };
// size is in KiB (1,024-byte blocks), not bytes: size=1 returns 1,024 bytes, plenty for one key.
const response = await fetch(`${apiUrl}?size=1`, { headers, signal: AbortSignal.timeout(10_000) });
const hint = hints[response.status] ?? "try again shortly";
if (!response.ok) exitWith(`Qrypt answered HTTP ${response.status}: ${hint}.`);
// The answer is {"random": ["<base64 of 1,024 bytes>"], "size": 1}; anything else ends above.
const entropyBytes = Buffer.from(/** @type {any} */ (await response.json()).random[0], "base64");

// Bytes 0-31 are the key and bytes 32-43 the nonce: never reuse entropy bytes for two purposes.
const [aesKey, nonce] = [entropyBytes.subarray(0, 32), entropyBytes.subarray(32, 44)];
const sampleText = "Hello from Qrypt quantum entropy";
const cipher = createCipheriv("aes-256-gcm", aesKey, nonce);
const ciphertext = Buffer.concat([cipher.update(sampleText, "utf8"), cipher.final()]);
// authTagLength makes decryption refuse a shortened tag, which GCM would otherwise accept.
const decipher = createDecipheriv("aes-256-gcm", aesKey, nonce, { authTagLength: 16 });
decipher.setAuthTag(cipher.getAuthTag());
const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
if (decrypted !== sampleText) exitWith("AES-GCM round trip failed: do not use this key.");
console.log("Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).");
