# Competitive teardown: RANDOM.ORG's API against this project's funnel

The brief's stretch item: compare the first-run experience with one other security or randomness
API's quickstart, against this project's own funnel criteria (the five stages of
`docs/KEY_METRICS.md`). The other API is RANDOM.ORG's JSON-RPC API, release 4. It is a randomness
API behind a key, with a free developer tier, like Qrypt's Entropy service.

ANU's Quantum Numbers API was the first choice, as the closest match (quantum randomness behind a
key). Its pages render in the browser and gave no readable text to a fetch [R8], so it was not
compared here.

**How it was done, 2026-10-20.** RANDOM.ORG's published documentation was read [R1–R4], `llms.txt`
was requested at both of its hosts [R5], and one request was sent with a key that was never issued,
to see what a mistyped key returns [R6]. No account was made, so the time to get a key was not
measured. Qrypt's side is this project's quickstart; every fact about Qrypt is a row of
`CLAIMS.md`.

## Stage by stage

| Stage | Qrypt, with this quickstart | RANDOM.ORG | Who does better |
|---|---|---|---|
| 1. Landing | One page from "get a token" to "first key", with a stated target (under 10 minutes), Python, Node.js and Rust tabs, copy buttons, and `llms.txt` for agents | A reference page covering 8 methods [R1]; client libraries on a separate page, official in C#/.NET, Java, JavaScript/Node.js and Python [R4]; no `llms.txt` at either host [R5]; no time target on the pages read | Qrypt: one path, not a menu |
| 2. Token created | An Entropy token from portal.qrypt.com (Q-06) | Keys are UUIDs "generated for you", managed in an API dashboard [R2]; a developer key allows 1,000 requests and 250,000 bits a day [R2] | Not compared: neither sign-up was timed |
| 3. First successful call | `GET` with two headers; `size` counts KiB, 1 to 512 (Q-01 to Q-03) | `POST` of a JSON-RPC 2.0 body to one endpoint, with the key inside the body; `generateBlobs` takes `n` (1 to 100) and `size` in bits (1 to 1,048,576, divisible by 8) [R1] | Even: each has a unit trap, KiB at Qrypt and bits at RANDOM.ORG |
| 4. First key | A 25-line program in each of three languages turns the entropy into an AES-256 key and proves it with AES-GCM, never printing it | Blobs come back as base64 or hex [R1]. 256 bits in one call is one key's worth, but no page read shows how to make a key from them | Qrypt: the brief's job is done in the snippet |
| 5. Return within 7 days | The limits show up only when a request is refused: 403 when the allotment is used up, 429 when requests come too close together (documented as 30 in 10 seconds; live, a trial key was refused at two within half a second), each with its fix (Q-13, Q-15, Q-16) | Every answer carries `bitsLeft`, `requestsLeft` and an `advisoryDelay` in milliseconds before the next request [R1], so a client sees its budget before it hits a limit | RANDOM.ORG: it tells the client before it refuses |

## The first error a developer meets

A mistyped key is the commonest first failure. At RANDOM.ORG it comes back as **HTTP 200**, with
the error inside the body: `{"error": {"code": 400, "message": "The API key you specified does not
exist"}}` [R6]. The error codes page lists it the same way [R3]. A client that checks only the HTTP
status reads that as a success, and the message does not say where to get a key. With this
quickstart, a wrong Qrypt token is an HTTP 401, and the program prints one line saying the token is
invalid or expired and where to get a new one (Q-11).

## What to borrow

1. **Say the budget in every answer.** RANDOM.ORG's `bitsLeft` and `requestsLeft` [R1] would let a
   Qrypt client see its allotment before a 403, which waiting does not fix. A response header would
   do it without changing the JSON. This is a candidate for the backlog (Phase 9), which is ranked
   from the agent rounds.
2. **Tell the client when to come back.** `advisoryDelay` [R1] is a server-side pacing hint. Qrypt's
   429 could carry the standard `Retry-After` header, and the quickstart would print it instead of a
   fixed "wait 10 seconds".
3. **Official libraries are a choice, not a gap.** RANDOM.ORG keeps libraries in four languages [R4];
   the PRD's tradeoff is "no full SDK this quarter", so that the first key needs no package of
   Qrypt's. The teardown does not change that choice.

What not to copy: errors behind an HTTP 200, and a size counted in bits that must be divisible by 8.

## Sources

- [R1] RANDOM.ORG, "JSON-RPC API – Release 4", Basic API: https://api.random.org/json-rpc/4/basic, read 2026-10-20
- [R2] RANDOM.ORG, API keys: https://api.random.org/api-keys, read 2026-10-20
- [R3] RANDOM.ORG, error codes: https://api.random.org/json-rpc/4/error-codes, read 2026-10-20
- [R4] RANDOM.ORG, source code and libraries: https://api.random.org/json-rpc/4/source-code, read 2026-10-20
- [R5] `llms.txt` requested at https://api.random.org/llms.txt and https://www.random.org/llms.txt: HTTP 404 from both, 2026-10-20
- [R6] One `generateBlobs` request to https://api.random.org/json-rpc/4/invoke with a random, never-issued UUID as its key: HTTP 200, error code 400 in the body, 2026-10-20
- [R8] ANU Quantum Numbers, https://quantumnumbers.anu.edu.au/ and its documentation page: no readable text without a browser, 2026-10-20
