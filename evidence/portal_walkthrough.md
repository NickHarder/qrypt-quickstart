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

## How this reaches the product

- The quickstart page's "Get a token" step names each screen and button, from steps 2 to 5.
- Each friction becomes a backlog item, ranked with the agent rounds' findings.
- What a newcomer can do about a friction today goes on the troubleshooting page, once it is
  confirmed. For step 3, that waits on the owner saying which reading of the password worked.
