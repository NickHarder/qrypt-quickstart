---
type: Users
title: "Users: who the Qrypt quickstart serves, and when"
description: The developer new to Qrypt, the AI coding agent acting for them, the internal stakeholders and the grader, with the users the quickstart refuses, the moments it serves and the use cases that trace to the audit and the deliverables.
tags: [users, gate]
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:30:43Z }
sources:
  - id: assessment
    resource: /brief/assessment-text.md
    title: The assessment's full text
  - id: project-brief
    resource: /brief/project-brief.md
    title: The project brief, as the portal shows it
  - id: partner-notes
    resource: /brief/partner-notes.md
    title: Partner notes on Qrypt
  - id: blueprint
    resource: /brief/research-blueprint.md
    title: The research blueprint (AI-drafted, not fact-checked)
  - id: audit
    resource: /AUDIT.md
    title: "Audit: Qrypt's first-run path"
  - id: plan
    resource: /PLAN.md
    title: The plan
  - id: deliverables
    resource: /DELIVERABLES.md
    title: Deliverables
verified:
  - { by: human:nickharder, at: 2026-10-20T21:46:35Z }
approved_sha256: 1b08ce75e679f55f838a4e1a073d5ea54ea446e07c12c86347026d911535cb09
---

# How to read this draft

Every field of the skill's templates is here. Where the brief, the audit or the plan answers a
field, the answer carries its source. Where none does, the field says **Open for the owner** and
asks the question; nothing was invented to fill it. The questions are gathered at the end, in
"Open for the owner". There is no user research behind this document: no developer, agent operator,
support engineer or grader was interviewed, so "in their own words" is the brief's words or a
paraphrase of them, and says which.

The product has no AI feature of its own.[^project-brief] What it ships is two to three quickstart
snippets, a static site with a troubleshooting page and `llms.txt`, and four documents at the
repository's root (`PRD.md`, `AGENT_READINESS.md`, `BACKLOG.md`, `CLAIMS.md`).[^plan]

# 1. The setting

| | |
|---|---|
| The service | Qrypt Quantum Entropy: one `GET` to `https://api-eus.qrypt.com/api/v1/quantum-entropy?size={n}`, `size` in KiB from 1 to 512, two required headers (`Accept: application/json`, `Authorization: Bearer`), six documented error statuses, 30 requests per 10 s per token[^assessment] |
| How a developer meets it today | docs.qrypt.com/eaas/, whose examples leave out the `Accept` header (DQ-01), read no status before the body (DQ-02), put the token in source and print every entropy byte (SEC-03); no `llms.txt` (DQ-05); no SDK outside C/C++ (ARCH-03)[^audit] |
| How a token is got | The brief names `portal.qrypt.com/register` or an assessment token from the program contact; Qrypt's page says to contact Qrypt; the partner notes saw the portal fail to load once (DQ-04)[^audit] |
| The industry | Developer platforms and security SaaS[^assessment] |
| The business case | Illustrative, the brief's own assumptions: 400 signups a quarter, activation 25% to 50%, time to first key about 45 minutes to under 10, 30 onboarding tickets a quarter at 0.5 h and $60/h[^assessment] |
| The target users the brief names | Application developers new to Qrypt; AI coding agents acting for them; internal stakeholders in engineering, sales and support[^assessment] |
| Who else uses what this project ships | The assessment's grader, who runs the grader quick-start and scores a 100-point rubric[^assessment] |

**Sales has no persona.** The brief names sales among the internal stakeholders who "need to know
what good onboarding means and how it is measured", and says nothing more about what sales does.[^assessment]
Its need is the same funnel definition P-03 reads (UC-04). A persona of its own waits on the owner.

**Decision: the human developer is the primary persona, the agent secondary.**

- **Claim:** P-01 is primary; P-02 is specified as fully, as the persona that marks the token's
  boundary.
- **Evidence:** the funnel the brief defines is a person's (landing, token created, first call,
  first key, return within 7 days), and every stage but the first two can be reached by an agent
  only with a token a person created.[^assessment]
- **Alternative considered:** the agent as primary, since the brief's headline test is the agent's
  and the blueprint calls agents a "substantial share" of first-run developers.[^blueprint]
- **Why rejected:** the share is the blueprint's, without a source; and the agent never creates the
  token, so it cannot own the funnel.
- **How to reverse:** swap the two headings' roles in section 2 and 3 and re-point the moments; no
  id changes.

# 2. Primary persona

### P-01: Application developer new to Qrypt

| Field | Answer |
|---|---|
| Name and role | An application developer who has "never heard of Qrypt" and is asked to produce a working AES-256 key from quantum entropy[^assessment] |
| The account they sign in with | A Qrypt account at `portal.qrypt.com`, with an access token for the **Entropy** service; or no account, and an assessment token from a program contact.[^assessment] The quickstart site has no sign-in |
| Setting | **Open for the owner:** the size of their organization, their team and their machine. The brief gives only the industry (developer platforms, security SaaS) and the languages a quickstart may be in (Python, Node, Go, Rust, C++)[^assessment] |
| Volume | One first run, which uses 1 KiB.[^assessment] After it: **open for the owner** (how many requests a day a developer who returns makes) |
| A full day, by the clock | **Open for the owner.** Nothing committed says when in a day a developer comes to Qrypt or what the day around it holds. The brief's only timings are the session itself: about 45 minutes from reference docs today (an assumption), under 10 as the target[^assessment] |
| Tools and screens today, in order | docs.qrypt.com/eaas/ → the portal or a contact form for a token → their editor and terminal, copying Qrypt's example → the error the call returns. The order is the audit's reading of Qrypt's page, not an observation[^audit] |
| What they type and what they read | Type: a `.env` line, a copied snippet, a run command. Read: the quickstart page, the success line, and an error message when one comes[^assessment] |
| Interruptions and physical environment | **Open for the owner.** The brief names first-run environment trouble (a missing runtime version, a missing `.env`, a corporate proxy or TLS error) but not the place or the interruptions[^assessment] |
| Trust posture | Treats an unsourced claim about Qrypt as untrusted: every claim on the site must trace to Qrypt's docs and no superlative may appear.[^assessment] "I don't know" is acceptable where Qrypt's docs are silent (a missing `Accept`, an error body, `Retry-After`: ARCH-01), and the site says so rather than guess[^audit] |
| Tolerances | Median time to first key under 10 minutes; the snippet under 3 s end to end; the page under 1.5 s p95 on mobile.[^assessment] Acceptable miss rate: **open for the owner** (the brief sets one only for the agent). Never acceptable: the key printed, logged or written; the token committed or shown; a stack trace instead of a message; a retry loop on 429[^assessment] |
| Must never be shown | The generated key; the token in any screenshot, recording or log; a marketing superlative ("unbreakable", "perfectly secure"); a claim with no source; a stack trace; the private brief (CMP-01)[^assessment] [^audit] |
| Authorization scope | One bearer token for the Entropy service, held in their own `.env` as `QRYPT_API_KEY`; bound by 30 requests per 10 s per token (429) and the account's allotment for the period (403), whose amount Qrypt does not state (DQ-06). On the site: read only, anonymous[^assessment] [^audit] |
| Success, in one sentence | They run the snippet with their own token and see the success line, with a working AES-256 key that was never shown, in under 10 minutes from landing. |

# 3. Secondary personas and anti-personas

### P-02: AI coding agent acting for the developer

| Field | Answer |
|---|---|
| Name and role | An AI coding agent given only the quickstart's URL or Markdown and the prompt "Generate an AES-256 key using Qrypt quantum entropy in a new project"; for the readiness test, Claude Code[^assessment] [^plan] |
| The account they sign in with | None at Qrypt: it acts with the token of the developer who launched it. Its own login is the operator's (Claude Code's `claude setup-token` or an API key, the owner's call in Phase 8)[^plan] |
| Setting | A fresh environment per run: a new Docker container, an empty project, the token in `.env` only[^plan] |
| Volume | 5 runs a round, two rounds, one after another, never in parallel (PERF-02)[^assessment] [^audit] |
| A full day, by the clock | One run, not a day: from the prompt to a program that prints the success line, median at most 10 minutes over successful runs of the revised round.[^assessment] Phase 8 runs both rounds on Tuesday 2026-10-20, 19:00 to 22:00 CDT[^plan] |
| Tools and screens today, in order | The prompt → the quickstart Markdown (or, without it, docs.qrypt.com, which has no `llms.txt`, and its own training) → a shell to create files, install packages and run → the program's output[^audit] [^plan] |
| What they type and what they read | Type: files, install commands, run commands. Read: the Markdown, `llms.txt`, the program's output and errors[^plan] |
| Interruptions and physical environment | None but what the container lacks: the runtime version, a network that may fail, a corporate proxy if the operator has one[^assessment] |
| Trust posture | Takes what the page says as instruction, and fills a gap from training: the failures the brief expects are a wrong header, unit confusion, an invented SDK and a skipped `.env`.[^assessment] It should say "I don't know" rather than invent a package (ARCH-03)[^audit] |
| Tolerances | At least 4 of 5 runs succeed after revision; median at most 10 minutes.[^assessment] Never acceptable: the token read into the transcript or printed (SEC-01); the key printed; `size` above 1; a retry loop[^audit] |
| Must never be shown | The token's value, beyond the `.env` it must read (Gate 3 decides how: SEC-01); the private brief[^audit] |
| Authorization scope | The developer's one Entropy token, by `.env` in its container, and nothing else; the token the containers use is revoked after Phase 8 (CMP-02)[^audit] |
| Success, in one sentence | From only the quickstart and the prompt, it writes a program that fetches `size=1` with both headers and the token from the environment, and prints the success line and never the key. |

### P-03: Qrypt engineering lead who builds the funnel's instrumentation

| Field | Answer |
|---|---|
| Name and role | An internal engineering lead at Qrypt who builds the activation funnel's instrumentation from the PRD's metrics section "without asking you a question"[^assessment] |
| The account they sign in with | Access to the submitted repository (GitHub now, GitLab at the end).[^plan] Their Qrypt-internal accounts (analytics, the API's logs): **open for the owner** |
| Setting | **Open for the owner** (team size, who else instruments). The partner notes describe Qrypt's stack as Rust first, AWS with Terraform[^partner-notes] |
| Volume | One PRD, five funnel stages[^assessment] |
| A full day, by the clock | **Open for the owner.** The brief says only that they are busy and read the PRD in 10 minutes[^assessment] |
| Tools and screens today, in order | `PRD.md`, then `docs/KEY_METRICS.md` (the same funnel, kept equal by a test), then their analytics and the API's logs[^plan] |
| What they type and what they read | Read: each stage's event, trigger, payload, join key, formula and target. Type: the events, in their own systems[^deliverables] |
| Interruptions and physical environment | **Open for the owner** |
| Trust posture | An illustrative number must be labelled an assumption; a number from a run appears only after the run[^plan] |
| Tolerances | Reads the PRD in 10 minutes, under 2,500 words (RQ-29). Never acceptable: two specs for one stage (the research had two for stage 3, D5)[^deliverables] [^plan] |
| Must never be shown | The developer's token or key; any developer's personal identifier in an event (the analytics rule: no cookies, no personal identifiers)[^assessment] |
| Authorization scope | Read access to the repository. What the instrumentation may read of Qrypt's systems is theirs to decide; the PRD names no field that identifies a person |
| Success, in one sentence | They build each stage's event from the PRD alone, with no question back. |

### P-04: Qrypt support engineer who answers onboarding tickets

| Field | Answer |
|---|---|
| Name and role | A support engineer at Qrypt who answers tickets from avoidable first-run errors: a wrong header, unit confusion, rate limits[^assessment] |
| The account they sign in with | **Open for the owner** (Qrypt's ticket system). The troubleshooting page needs none |
| Setting | **Open for the owner** (team size, hours) |
| Volume | About 30 onboarding tickets a quarter, at about 0.5 h each: the brief's assumption[^assessment] |
| A full day, by the clock | **Open for the owner** |
| Tools and screens today, in order | The ticket → docs.qrypt.com/eaas/, whose error table gives a meaning and no fix[^audit] → a reply written by hand. Their ticket tool: **open for the owner** |
| What they type and what they read | Read: the developer's error and the troubleshooting entry. Type: a reply, ideally a link to the entry |
| Interruptions and physical environment | **Open for the owner** |
| Trust posture | Cites only what Qrypt documents; where Qrypt is silent (ARCH-01), says so rather than guess[^audit] |
| Tolerances | Never acceptable: telling a developer to turn TLS verification off (SEC-04); telling them to retry a 429 in a loop; blaming the allotment for an edge refusal (ARCH-02)[^audit] |
| Must never be shown | A developer's token or key, pasted into a ticket |
| Authorization scope | Read the public site. What support may see of a developer's account is Qrypt's: **open for the owner** |
| Success, in one sentence | They answer an onboarding ticket with one link to the troubleshooting entry that fixes it. |

### P-05: The assessment's grader

| Field | Answer |
|---|---|
| Name and role | The person who scores the submission on the 100-point rubric, pass at 70; Qrypt's technical contact is Sean Neal, CTO, but who grades is not stated[^assessment] [^project-brief] |
| The account they sign in with | Access to the repository and the public site URL, which the owner shares; their own Qrypt token for the grader quick-start[^assessment] |
| Setting | **Open for the owner** (one grader or several; their machine) |
| Volume | One submission of this project; how many they grade: **open for the owner** |
| A full day, by the clock | **Open for the owner.** The fixed point is the interview, Wednesday 2026-10-21 at 13:30 CDT[^plan] |
| Tools and screens today, in order | The README's grader quick-start → a terminal → the site → `PRD.md`, `AGENT_READINESS.md`, `BACKLOG.md`, the claims table → the demo video[^assessment] |
| What they type and what they read | Type: the token into `.env` and each snippet's run command. Read: the success line, the documents, the video |
| Interruptions and physical environment | **Open for the owner** |
| Trust posture | Trusts a number only with its measurement and a claim only with its source; the rubric scores "unverified claims" low[^assessment] |
| Tolerances | Set a token, run each snippet and see the success line in under 5 minutes (RQ-35); the video at most 5 minutes[^deliverables] |
| Must never be shown | The owner's token in a recording, a transcript or the repository; the private brief, left out of the public copy[^audit] |
| Authorization scope | Their own Entropy token in their own `.env`; read access to the repository the owner shares |
| Success, in one sentence | They run both snippets from a fresh clone and see each success line in under 5 minutes, then find each rubric item where the README says. |

### AP-01: Whoever wants the key shown, logged or saved

- **Who:** a developer, or an agent told to, who asks the quickstart to print the key, write it to
  a file or log it "to check it".
- **How it is recognized:** the request itself (a flag, an edit, a prompt asking for the key's value).
- **How it is refused:** the snippet has no path that outputs the key; the page and `llms.txt` say
  never to print, log or commit a key, and why. The success line is the proof the key works.[^assessment]

### AP-02: A bulk or looping consumer of entropy

- **Who:** someone using the quickstart as an entropy feed: a larger `size`, a loop, a load test,
  a retry on 429.
- **How it is recognized:** `size` above 1, repeated calls, a 429 or a 403.
- **How it is refused:** the snippet asks for `size=1`, makes one request, never retries, and exits
  on 429 within 1 s with the wait it needs; 403 is explained as the allotment, not retried (RQ-12,
  PERF-02).[^deliverables] [^audit]

### AP-03: A reader looking for a claim the docs do not make

- **Who:** a reader who wants a certification or a superlative to cite ("is it NIST certified",
  "unbreakable").
- **How it is recognized:** a claim that is not in the claims table.
- **How it is refused:** the site makes no certification claim (Qrypt's EaaS page makes none, DQ-07)
  and no superlative; it points to Qrypt.[^audit]

### AP-04: A public reader of the private brief

- **Who:** anyone reaching the owner's notes or the partner's brief through the public site or the
  public copy of the repository.
- **How it is recognized:** a path under `docs/` or `docs/brief/` in the built site or the public
  copy.
- **How it is refused:** the site is built from `site/` only, and a test checks the built site holds
  no file from `docs/` (CMP-01); the public copy leaves `docs/brief/` out.[^audit]

# 4. Moments in the day

### Moment A: the first run

| Field | Answer |
|---|---|
| Who | P-01 |
| Clock time | **Open for the owner** |
| 30 seconds before | Arriving on the quickstart, from where: **open for the owner** (the PRD's landing stage counts the arrival, not its source) |
| The question, in their words | Paraphrase of the brief: "How do I get an AES-256 key out of Qrypt, in my language, now?"[^assessment] |
| What they would open today | docs.qrypt.com/eaas/ and its examples[^audit] |
| Time available | The brief's target is under 10 minutes; developers who fail in the first session rarely return[^assessment] |
| What they do with the answer | Run it, see the success line, and use the pattern in their own code |

### Moment B: staring at an error

| Field | Answer |
|---|---|
| Who | P-01, and P-04 when it becomes a ticket |
| Clock time | **Open for the owner** |
| 30 seconds before | They ran a call or a snippet and it printed an error: 400, 401, 403, 429, 500, 503, or a runtime, `.env`, proxy or TLS failure[^assessment] |
| The question, in their words | The brief's: "the error a developer is staring at"; paraphrased, "What does this mean and what do I do?"[^assessment] |
| What they would open today | Qrypt's error table, which gives a meaning and no fix, then a support ticket[^audit] |
| Time available | **Open for the owner** |
| What they do with the answer | Apply the fix and run again; or, for P-04, send the link |

### Moment C: the agent's run

| Field | Answer |
|---|---|
| Who | P-02 |
| Clock time | In the test, Phase 8, Tuesday 2026-10-20 19:00 to 22:00 CDT; outside it, whenever P-01 delegates[^plan] |
| 30 seconds before | The operator started a fresh container and gave the prompt[^plan] |
| The question, in their words | The brief's prompt, word for word: "Generate an AES-256 key using Qrypt quantum entropy in a new project"[^assessment] |
| What they would open today | docs.qrypt.com, which has no `llms.txt` (DQ-05), and its training, which may name a "Qrypt SDK" that is another product (ARCH-03)[^audit] |
| Time available | Median at most 10 minutes over successful runs[^assessment] |
| What they do with the answer | Write and run the program; report success or the failure |

### Moment D: building the funnel

| Field | Answer |
|---|---|
| Who | P-03 |
| Clock time | **Open for the owner** |
| 30 seconds before | **Open for the owner** |
| The question, in their words | Paraphrase of the brief: "What exactly is each stage, and what event do I emit for it?"[^assessment] |
| What they would open today | **Open for the owner** (whether Qrypt measures onboarding today); the brief's illustrative numbers are assumptions[^assessment] |
| Time available | A 10-minute read (RQ-29)[^deliverables] |
| What they do with the answer | Build the events and the stage formulas |

### Moment E: the grader's five minutes

| Field | Answer |
|---|---|
| Who | P-05 |
| Clock time | **Open for the owner** (before the interview, Wednesday 2026-10-21 13:30 CDT)[^plan] |
| 30 seconds before | Cloned the repository and opened the README |
| The question, in their words | Paraphrase of the brief: "Does it run, as the README says, in under 5 minutes?"[^assessment] |
| What they would open today | The README; nothing else exists |
| Time available | Under 5 minutes for the quick-start[^assessment] |
| What they do with the answer | Score the rubric's 25 points for the quickstart and site, and go on to the documents |

# 5. Use cases

### UC-01: From a token to a first key

| Field | Answer |
|---|---|
| The moment | Moment A |
| The exact question | "How do I get an AES-256 key from Qrypt in Python (or Node, or Rust)?" |
| The data it needs, and where it lives | The token, in the developer's `.env`; 1 KiB of entropy from the live endpoint, or the mock in CI; the snippet, in `quickstart/`[^plan] |
| Required latency | The snippet under 3 s; the page under 1.5 s p95; the whole path a median under 10 minutes[^assessment] |
| What a wrong answer costs, and to whom | A missing header or a wrong `size` fails the first session, and the developer rarely returns (Qrypt loses the signup); a printed key leaks it (the developer and their users)[^assessment] |
| Why this and not what they have | Qrypt's examples, the alternative, send one header, print every byte, put the token in source and stop before the key (DQ-01, DQ-02, SEC-03)[^audit] |
| Refusal behaviors | No token: exit non-zero, naming where to get one and how to set it (RQ-04). Never prints, logs or writes the key (AP-01). Never asks for more than `size=1` (AP-02) |
| Several turns or chained tools | No: one run of one script |
| Eval categories that guard it | `agent-contract` (the plan's first case: `size=1`, both headers, token from the environment, key never printed); `key-handling`[^plan] |
| The metric that proves it | NS-01 (first successful call), with DR-01, DR-02, DR-03 (first key) and GR-01 (return within 7 days): [the key metrics](KEY_METRICS.md) |

### UC-02: The error I am staring at

| Field | Answer |
|---|---|
| The moment | Moment B |
| The exact questions | "What does this 401 (400, 403, 429, 500, 503) mean and what do I do?"; "Why does it say my `.env` is missing?"; "Why does it fail behind my company's proxy?" |
| The data it needs, and where it lives | The status or failure, in the snippet's message; the entry, on the troubleshooting page (`site/troubleshooting.md`)[^plan] |
| Required latency | The page under 1.5 s p95; the snippet's message at once, and on 429 within 1 s[^deliverables] |
| What a wrong answer costs, and to whom | Mistaking 403 for 429 makes a developer retry into the allotment; turning off TLS verification exposes the token (SEC-04); each avoidable ticket is about 0.5 h of support at $60/h, the brief's assumption[^assessment] [^audit] |
| Why this and not what they have | Qrypt's error table, the alternative, gives each status a meaning and no fix, and says nothing about proxies, `.env` or a missing `Accept`[^audit] |
| Refusal behaviors | No status is claimed for what Qrypt does not document, until Phase 7 records it (ARCH-01); no fix turns verification off; no retry loop |
| Several turns or chained tools | No: one page, one entry |
| Eval categories that guard it | `error-handling` (Phase 3's case: given the page and a 429, wait and do not loop, and tell 429 from 403)[^plan] |
| The metric that proves it | NS-01 (first successful call). Ticket deflection stays the brief's assumption, not a key metric: [the key metrics](KEY_METRICS.md) |

### UC-03: An agent writes the program from the quickstart alone

| Field | Answer |
|---|---|
| The moment | Moment C |
| The exact question | "Generate an AES-256 key using Qrypt quantum entropy in a new project"[^assessment] |
| The data it needs, and where it lives | The quickstart's Markdown and `llms.txt` (`site/`); the token in the container's `.env`[^plan] |
| Required latency | Median at most 10 minutes over successful runs[^assessment] |
| What a wrong answer costs, and to whom | An invented SDK or a wrong header fails the run; `size=32` spends 32 KiB of the budget; a token in the transcript leaks it for good (SEC-01, CMP-02); the developer who delegated loses the session[^audit] |
| Why this and not what they have | docs.qrypt.com, the alternative, has no `llms.txt` and examples missing the `Accept` header, and "Qrypt SDK" names a different product (DQ-01, DQ-05, ARCH-03)[^audit] |
| Refusal behaviors | The page and `llms.txt` say there is no SDK for the entropy service, never to print the key, never to read the token aloud, `size=1` only |
| Several turns or chained tools | Yes, inside the agent: read the page, write files, install, run, read the output. The product itself makes no model call |
| Eval categories that guard it | `agent-contract`; `no-sdk` (Phase 2's case: built-in `fetch` and `crypto`, no Qrypt package); a regression case for each Round 1 failure[^plan] |
| The metric that proves it | DR-04 (agent success rate, at least 4 of 5) and GR-02 (agent median time to first key, at most 10 minutes) |

### UC-04: Instrument the funnel from the PRD

| Field | Answer |
|---|---|
| The moment | Moment D |
| The exact question | "For each of landing, token created, first successful call, first key and return within 7 days: what event, fired where, with what payload and join key, and what formula and target?"[^assessment] |
| The data it needs, and where it lives | `PRD.md` and `docs/KEY_METRICS.md`, which a test keeps equal[^plan] |
| Required latency | A 10-minute read[^deliverables] |
| What a wrong answer costs, and to whom | An ambiguous stage is built twice or wrong, and engineering and go-to-market disagree on what to build next (Qrypt)[^assessment] |
| Why this and not what they have | The alternative is the brief's illustrative funnel, named but with no event, payload or join key, and two conflicting specs for stage 3 in the research (D5)[^plan] |
| Refusal behaviors | No illustrative number is shown as measured; no event carries a personal identifier |
| Several turns or chained tools | No |
| Eval categories that guard it | None: a test of `PRD.md` guards it (each stage's fields, equal to `docs/KEY_METRICS.md`, under 2,500 words)[^plan] |
| The metric that proves it | None: the funnel is what P-03 builds, not a number that proves it; the acceptance is the brief's "no question back", and a test of `PRD.md` against [the key metrics](KEY_METRICS.md) |

### UC-05: Run the grader quick-start

| Field | Answer |
|---|---|
| The moment | Moment E |
| The exact question | "Set a token, run each snippet, see the success line: does it work in under 5 minutes?"[^assessment] |
| The data it needs, and where it lives | The README; the grader's token; the snippets |
| Required latency | Under 5 minutes in all (RQ-35)[^deliverables] |
| What a wrong answer costs, and to whom | A step that fails costs the owner the rubric's quickstart points (25)[^assessment] |
| Why this and not what they have | The alternative is reading the code without running it, which proves nothing the rubric scores |
| Refusal behaviors | As UC-01: no token gives the message that names where to get one; the key is never shown |
| Several turns or chained tools | No |
| Eval categories that guard it | None: a timed run from a fresh clone (`evidence/grader_quickstart.md`) and a test of the README's shell blocks[^plan] |
| The metric that proves it | None at Gate 4 by default: RQ-35's timed run |

### UC-06: Trace a claim about Qrypt to its source

| Field | Answer |
|---|---|
| The moment | Moment E, and Moment A for a developer who doubts a line |
| The exact question | "Where does Qrypt say this?" |
| The data it needs, and where it lives | `CLAIMS.md`, each claim with its id and its Qrypt page[^plan] |
| Required latency | **Open for the owner**: the brief sets none |
| What a wrong answer costs, and to whom | An unsourced or overstated claim from a security vendor's docs costs Qrypt trust and the owner the rubric's accuracy points[^assessment] |
| Why this and not what they have | The alternative is checking each sentence against docs.qrypt.com by hand, and the AI-drafted research has unsourced claims (NIST, ESV, benchmarks)[^plan] |
| Refusal behaviors | No claim on the site without an entry; no superlative (AP-03) |
| Several turns or chained tools | No |
| Eval categories that guard it | None: Phase 5's test that every claim id is in the table and no listed superlative appears[^plan] |
| The metric that proves it | None at Gate 4 by default: RQ-24's count of corrected AI-drafted claims |

## Considered and cut

| Use case | Why it was cut |
|---|---|
| Install a Qrypt package for my language | The brief's suggested tradeoff is no SDK this quarter; one `GET` needs only a request[^plan] |
| Fetch entropy in bulk or on a loop | That is AP-02; the quickstart serves one first key |
| Show my usage against the allotment | Qrypt publishes no usage meter (CMP-03); the site cannot read an account[^audit] |
| Try the call in the browser | It would put the token in a web page, against the `.env`-only rule[^assessment] |
| A unit calculator for `size` | A sentence beside every `size` does it (RQ-14); a tool would not beat the sentence[^deliverables] |
| A funnel dashboard for P-03 | Analytics (RQ-40) is not built: no deployed site to observe until the move to GitLab[^plan] |
| A sales pitch page | No committed document says what sales needs beyond the funnel's definition, which UC-04 serves |
| Seed an HSM or the kernel (`qseed`, rng-tools) | Out of the brief's first-run scope; the plan does not use them[^plan] |

# 6. Traceability

| Use case | Persona | Moment | Audit findings | Deliverables |
|---|---|---|---|---|
| UC-01 | P-01 | A | DQ-01, DQ-02, SEC-03, ARCH-04, ARCH-06 | RQ-01, RQ-04, RQ-05, RQ-14, RQ-15, RQ-22 |
| UC-02 | P-01, P-04 | B | ARCH-01, ARCH-02, SEC-04 | RQ-06, RQ-11, RQ-12, RQ-13, RQ-17 |
| UC-03 | P-02 | C | DQ-05, ARCH-03, SEC-01, SEC-02 | RQ-09, RQ-19, RQ-23, RQ-38 |
| UC-04 | P-03 | D | DQ-04 | RQ-08, RQ-29 |
| UC-05 | P-05 | E | ARCH-04 | RQ-30, RQ-35 |
| UC-06 | P-05, P-01 | E, A | DQ-07 | RQ-16, RQ-24 |

# 7. The demo

No seeded data exists yet: the mock and its tokens (`mock-200`, `mock-401` and the rest) come in
Phase 1.[^plan] Until then, the demo is the brief's, mapped to the use cases, and is described again
against the mock once it exists:[^assessment]

1. A fresh run of the quickstart (UC-01), with no token on screen.
2. One troubleshooting path, a 401, from the message to its entry (UC-02).
3. The funnel in the PRD (UC-04).
4. One agent-readiness run (UC-03).

# Open for the owner

1. P-01: the developer's organization, team and machine; a full day by the clock; their
   interruptions and place; an acceptable miss rate; where they arrive from.
2. P-03 and P-04: their accounts and tools inside Qrypt, team sizes, days, and whether Qrypt
   measures onboarding today.
3. P-05: one grader or several, and when they grade.
4. Sales: a persona of its own, or the funnel definition (UC-04) only.
5. The clock times and the 30 seconds before Moments A, B, D and E, and the time available in B.
6. UC-06: a latency target, if any.

[^assessment]: The assessment's full text
[^project-brief]: The project brief, as the portal shows it
[^partner-notes]: Partner notes on Qrypt
[^blueprint]: The research blueprint (AI-drafted, not fact-checked)
[^audit]: "Audit: Qrypt's first-run path"
[^plan]: The plan
[^deliverables]: Deliverables
