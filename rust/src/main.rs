//! Make an AES-256 key from 1 KiB of Qrypt quantum entropy, and prove it works with AES-GCM.
//!
//! Setup:  `cargo new qrypt-key`, then in `qrypt-key` paste this file over `src/main.rs` and run
//!         `cargo add aes-gcm@0.11.1 base64@0.23.1 dotenvy@0.15.7 serde_json@1.0.151` and
//!         `cargo add ureq@3.4.2 -F platform-verifier`
//!         put `QRYPT_API_KEY=<your Entropy token>` in a `.env` file in the folder you run this from
//! Run:    `cargo run`
//!
//! The key is never printed, logged or written to disk: it lives only in this process's memory.
//! Every failure prints one line saying what to do and exits non-zero; nothing is retried in a loop.
use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Nonce};
use base64::{Engine, engine::general_purpose::STANDARD};
use serde_json::Value;
use std::{env, process::exit, time::Duration};
use ureq::tls::{RootCerts, TlsConfig};

/// Print a message and stop with a non-zero exit code.
#[rustfmt::skip] fn exit_with(message: &str) -> ! { eprintln!("{message}"); exit(1) }

/// Stop on any other failure (network, proxy, TLS, an answer without a block), after one request.
#[rustfmt::skip] fn could_not(reason: &str) -> ! { exit_with(&format!("Could not get entropy ({reason}): try again shortly, or see troubleshooting (proxy, TLS).")) }

/// Ask Qrypt for 1 KiB of entropy, make a key and a nonce of it, and prove them with AES-GCM.
#[rustfmt::skip] fn main() {
    dotenvy::dotenv().ok(); // reads .env from this folder (or a parent); a real env variable wins
    let api_key = env::var("QRYPT_API_KEY").unwrap_or_default().trim().to_owned();
    if api_key.is_empty() { exit_with("Set QRYPT_API_KEY=<token> in .env (Entropy tokens: portal.qrypt.com)") }
    // QRYPT_API_URL points the program at a local mock for testing; unset, it calls Qrypt.
    let api_url = env::var("QRYPT_API_URL").unwrap_or("https://api-eus.qrypt.com/api/v1/quantum-entropy".into());
    // What to do about each error Qrypt documents; 500, 503 and any other status: try again shortly.
    let hint = |status| match status { 400 => "malformed request: size must be 1-512", 403 => "allotment used up; ask Qrypt",
        401 => "the token is invalid or expired; get a new one at portal.qrypt.com",
        429 => "over 30 requests in 10 seconds; wait 10 seconds, then run once", _ => "try again shortly" };
    // size is in KiB (1,024-byte blocks), not bytes: size=1 returns 1,024 bytes, plenty for one key.
    // The platform's certificates (and SSL_CERT_FILE) are trusted, so a company proxy's root works.
    let answer = ureq::get(format!("{api_url}?size=1")).header("Accept", "application/json").header("User-Agent", "qrypt-quickstart-rust/1.0")
        .header("Authorization", format!("Bearer {api_key}")).config().timeout_global(Some(Duration::from_secs(10)))
        .tls_config(TlsConfig::builder().root_certs(RootCerts::PlatformVerifier).build()).build().call();
    let body = match answer.and_then(|mut response| response.body_mut().read_to_string()) { Ok(body) => body,
        Err(ureq::Error::StatusCode(status)) => exit_with(&format!("Qrypt answered HTTP {status}: {}.", hint(status))),
        Err(error) => could_not(&error.to_string()) };
    // The answer is {"random": ["<base64 of 1,024 bytes>"], "size": 1}; anything else ends here.
    let entropy_bytes = serde_json::from_str::<Value>(&body).ok().and_then(|json| STANDARD.decode(json["random"][0].as_str()?).ok())
        .filter(|bytes| bytes.len() >= 44).unwrap_or_else(|| could_not("the answer holds no block of 44 bytes or more"));
    // Bytes 0-31 are the key and bytes 32-43 the nonce: never reuse entropy bytes for two purposes.
    let aes_gcm = Aes256Gcm::new_from_slice(&entropy_bytes[..32]).unwrap_or_else(|_| could_not("a key of 32 bytes"));
    let nonce = Nonce::try_from(&entropy_bytes[32..44]).unwrap_or_else(|_| could_not("a nonce of 12 bytes"));
    let sample_text = b"Hello from Qrypt quantum entropy";
    let ciphertext = aes_gcm.encrypt(&nonce, &sample_text[..]).unwrap_or_else(|_| exit_with("AES-GCM failed: do not use this key."));
    if aes_gcm.decrypt(&nonce, &ciphertext[..]).ok().as_deref() != Some(&sample_text[..]) { exit_with("AES-GCM round trip failed: do not use this key.") }
    println!("Success: an AES-256 key from Qrypt quantum entropy passed AES-GCM (key not shown).");
}
