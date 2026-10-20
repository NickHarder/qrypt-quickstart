# Getting an Entropy token: the portal, as a newcomer meets it

The real path from "no account" to "a token", walked by the owner on 2026-10-20, step by step,
with every friction a newcomer meets. It feeds the backlog (Phase 9) and the quickstart page's
"Get a token" step. No password, token or email address is recorded here.

| # | Step | What happens | Friction | What Qrypt could change |
|---|---|---|---|---|
| 1 | Find the sign-up | The brief's link, `portal.qrypt.com/register`, shows a 404. The portal's login page links "Create trial account" to `/trial`; `/signup` says to contact sales | The documented link is dead, and the working one is reachable only from the login page | Make `/register` lead to the trial sign-up, and link `/trial` from the docs |
| 2 | Start the trial | `portal.qrypt.com/trial` asks for a full name and a work email; "Start trial" | None seen | |
| 3 | Read the temporary password | An email from Qrypt's infrastructure address, "Your temporary password", gives the username and the password in one sentence: "… and temporary password is `<password>`." | The password ends in a period, and the sentence's own full stop follows it, so a reader cannot tell which periods belong to the password. A password made of symbols, inside a sentence, invites a wrong copy | Put the password on a line of its own, in a monospace style, with nothing after it, for example `Temporary password:` then the password alone on the next line, then the rest of the email. Better still, send a one-time link that sets the password, so none is copied at all |
| 4 | First login | Log in with the temporary password, and set one of your own | None reported once the password was read right | |
| 5 | Generate the Entropy token | The portal opens on Dashboard. In its side bar, API Keys; then Create API key; choose the service (two choices: Entropy, and one for another product); Create key. The key is shown, with a way to copy it | The quickstart's word is "token" and the portal's is "API key"; a newcomer has to know they are the same thing | Call it one thing in the portal, the docs and the error messages |
| 6 | The portal's own example | Beside the new key, the portal shows a request to a different API: `POST https://eaas-aws.qrypt.com/api/v1/entropy`, header `X-API-Key: <key>`, JSON body `{"block_size": 32, "block_count": 5}` | Qrypt's documentation (docs.qrypt.com/eaas, read 2026-10-20) names only `GET https://api-eus.qrypt.com/api/v1/quantum-entropy?size=<KiB>` with `Authorization: Bearer <token>`, and never `eaas-aws`. A newcomer, or an agent, cannot tell which API the key is for. Without a key, `eaas-aws` answers 403 | One API in the docs and the portal, or both documented with which key works where |

**Settled, 2026-10-20, by one live request to each (ledger `evidence/live_usage.csv`):** a trial
key from this portal works on the documented endpoint. `GET api-eus.qrypt.com/api/v1/quantum-entropy?size=1`
with `Authorization: Bearer <key>` answered 200 with `{"random": [<one base64 block>], "size": 1}`,
the shape the quickstarts and the mock already use, so the quickstart keeps `api-eus`. The portal's
own example, `POST eaas-aws.qrypt.com/api/v1/entropy` with `X-API-Key` and one 32-byte block,
closed the connection without an answer. A newcomer who copies the portal's example gets nothing
back, which makes step 6 the worst friction on this path.

One more, for the troubleshooting page: both hosts sit behind Cloudflare, which refuses a request
carrying a default library User-Agent (Python's `Python-urllib/3.x`) with 403 "Error 1010: Access
denied" before the key is read. The quickstarts send their own User-Agent; a newcomer's own code
may not.

## How this reaches the product

- The quickstart page's "Get a token" step names each screen and button, from steps 2 to 5.
- Each friction becomes a backlog item, ranked with the agent rounds' findings.
- What a newcomer can do about a friction today goes on the troubleshooting page, once it is
  confirmed. For step 3, that waits on the owner saying which reading of the password worked.
