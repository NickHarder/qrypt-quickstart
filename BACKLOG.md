# Backlog: what to fix next on the path to a first key

Ten follow-up items from the agent-readiness test (`AGENT_READINESS.md`), the owner's walk of the
portal (`evidence/portal_walkthrough.md`), the live probes against Qrypt and the audit of Qrypt's
docs (`docs/AUDIT.md`). Nine are Qrypt's to fix: this project's quickstart already works around
each of them, but every developer who never finds the quickstart still meets them. The scoring
sheet is `BACKLOG.csv`; `tests/test_backlog.py` checks its arithmetic, its evidence links and this
page's order against it.

## How the items are scored

RICE, on Intercom's scales: **reach** × **impact** × **confidence** ÷ **effort**.

- **Reach** is developers a quarter who meet the problem. There is no traffic data here, so every
  reach rests on the PRD's assumption of **400 signups a quarter** and its funnel targets (80%
  create a token, 50% make a first successful call, half of those return), and each item's share of
  that funnel is a stated assumption in the sheet's `reach_basis` column. The first measured
  cohort replaces them all.
- **Impact** per developer: 3 massive (the path stops), 2 high, 1 medium, 0.5 low, 0.25 minimal.
- **Confidence**: 80% when the problem was seen directly and only its reach is assumed, 50% when
  the reach or the effect is a guess as well. No item is at 100%, because no reach is measured.
- **Effort** in person-weeks, for whoever fixes it. Qrypt's are this project's rough estimates,
  from outside its code.

## The ranking

| Rank | Id | Item | Fix owner | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|---|---|---|
| 1 | B-01 | Make the brief's sign-up link lead to the trial sign-up, and link the trial from the docs | Qrypt | 400 | 2 | 50% | 0.25 | 1,600 |
| 2 | B-02 | One API and one name in the portal: the documented GET example beside a new key, and "token" everywhere | Qrypt | 320 | 3 | 80% | 0.5 | 1,536 |
| 3 | B-03 | Fix Qrypt's own code examples: the `Accept` header, a status check, the token from the environment, no printed entropy | Qrypt | 160 | 2 | 80% | 0.5 | 512 |
| 4 | B-04 | The trial email's temporary password on a line of its own, or a one-time link instead | Qrypt | 400 | 0.5 | 50% | 0.25 | 400 |
| 5 | B-05 | Publish an `llms.txt` at docs.qrypt.com, as a pull request built from this project's | Qrypt | 160 | 1 | 50% | 0.25 | 320 |
| 6 | B-06 | Answer a bad token with the documented 401, or a body of its own | Qrypt | 64 | 2 | 50% | 0.5 | 128 |
| 7 | B-07 | Run the agent test with other agents and a smaller model | This project | 160 | 0.5 | 50% | 0.5 | 80 |
| 8 | B-08 | Document Cloudflare's error 1010 for a library's default User-Agent, or let it through | Qrypt | 32 | 2 | 50% | 0.5 | 64 |
| 9 | B-09 | Document a trial key's real rate limit, and send `Retry-After` with a 429 | Qrypt | 50 | 1 | 80% | 1 | 40 |
| 10 | B-10 | Say the remaining allotment in every answer, as a response header | Qrypt | 100 | 0.5 | 50% | 2.5 | 10 |

## The evidence, item by item

- **B-01.** The brief's link, `portal.qrypt.com/register`, is a 404; the working trial sign-up,
  `/trial`, is linked only from the portal's login page (walkthrough, step 1). Everyone who signs up
  has to find it; the reach of 400 counts only those who did, so it is a floor.
- **B-02.** Beside a new key the portal shows `POST eaas-aws.qrypt.com/api/v1/entropy` with
  `X-API-Key`, an API the docs never name; sent with a trial key, it closed the connection without
  an answer, while the documented `GET api-eus` worked (walkthrough, steps 5 and 6; ledger
  `evidence/live_usage.csv`). The portal also says "API key" where the docs say "token". Every
  token holder sees this screen, and copying its example gets nothing back: impact 3.
- **B-03.** Three of Qrypt's four examples leave out the `Accept` header the same page requires,
  none checks the status before reading the body, and the Python one hard-codes the token and
  prints every entropy byte (`docs/AUDIT.md`, DQ-01 to DQ-03). An agent that falls back on Qrypt's
  page copies all of it.
- **B-04.** The trial email puts the temporary password inside a sentence, and the password ends
  in a period, so a reader cannot tell which periods are the password's (walkthrough, step 3).
  Every trial meets it; impact 0.5 assumes it slows the first login rather than stopping it.
- **B-05.** docs.qrypt.com has no `llms.txt` (DQ-05). With this project's, Claude Code got a key in
  15 of 15 fresh runs, across three rounds (`AGENT_READINESS.md`); the file exists, so the effort
  is a pull request.
- **B-06.** Live, a wrong token gets 403 `{"error": "Forbidden or entropy quota reached"}`, the
  answer to a used-up allotment, where the docs say 401 (`evidence/live_probes.json`). The
  quickstart now says "wrong token or allotment spent" (`evidence/live_wrong_token.json`); other
  clients send a developer to ask for more entropy.
- **B-07.** Only Claude Code had run the agent test. Another agent may stumble where it did not;
  the harness already takes another agent's command, so the effort is the runs and their report.
  **Done 2026-10-20, against the mock:** Claude Code on Haiku 5 of 5; Gemini CLI 1 of 5, its
  other four runs failing the token-file check its own transcripts led to (`AGENT_READINESS.md`, "Other agents").
- **B-08.** Live, Python's default `Python-urllib/3.x` User-Agent got Cloudflare's 403 `Error 1010:
  Access denied` before Qrypt read the token (`evidence/live_probes.json`). It looks like a token
  problem, and nothing in Qrypt's docs explains it.
- **B-09.** Live, a trial key was refused with 429 for a second request 0.36 s after its first,
  with no `Retry-After`, against a documented 30 requests in 10 seconds
  (`evidence/live_rate_limit.json`). Measured, so confidence is 80%; only a script that loops meets
  it.
- **B-10.** RANDOM.ORG says the remaining budget in every answer (`evidence/teardown.md`); Qrypt's
  first sign that an allotment is running out is the 403 that ends it. Useful to returning
  developers, but it is new API surface: the most effort on the list.

## What to do first

The score ranks value for effort; three dependencies change the order of work, not the ranking.

1. **B-01 and B-02 first, together.** They are one portal change, and they sit before the first
   successful call, the PRD's north star: no later fix helps a developer who never gets a working
   token and request.
2. **B-06 before B-10.** A remaining-allotment header is only trusted if a 403 means one thing.
3. **B-03 and B-05 as one docs pull request.** Both are changes to Qrypt's public docs, and
   B-05's file comes from this project.

B-07 is this project's own: it can run at any time, for the cost of the agent runs.
