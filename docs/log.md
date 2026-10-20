# History

What changed in this project and why, newest first. A commit shows the difference; an entry here
gives the reason. The `handoff` skill adds to it at every checkpoint, and the `write-okf-concept`
skill has the format.

## 2026-10-20
* **Change**: the rate limit, measured and acted on, on the owner's go. A probe
  (`evidence/live_rate_limit.json`, 7 KiB) found a trial key refused with 429 for a second request
  0.36 s after its first, with no `Retry-After`, every 429 cleared within 1.5 s. The live check now
  waits 2 s before each request and runs Rust too; run again, 15 of 15 succeeded (medians 0.42 s,
  0.51 s, 0.51 s; slowest 0.66 s). The three snippets' 429 message says "too many requests in a
  short time", and the troubleshooting page, `llms.md` and claims Q-15, Q-16, Q-22 and new Q-37 give
  the documented and the live figure side by side; PERF-02 records it. Also seen live: without
  `Accept`, Qrypt still answers 200 with JSON, and a wrong token gets 403 "Forbidden or entropy
  quota reached", not 401, so the snippets' 403 message ("allotment") misleads a mistyped token.
* **Change**: the first live check, on the owner's go (`evidence/live_runs.csv`,
  `evidence/live_probes.json`; the ledger at 16 KiB). Python and Node each succeeded 3 of 5, median
  0.54 s and 0.52 s, slowest 0.78 s, under the 3 s target. Every failure was a 429 after a few
  requests about half a second apart, against the documented 30 requests in 10 seconds, so a trial
  key's real limit is far lower and claims Q-15, Q-16 and Q-22 are not borne out live. A bad token
  got 403 "Forbidden or entropy quota reached", not 401. Rust's runs are not in the live check yet.
* **Change**: the endpoint question is settled, by the owner's approved probes (ledger
  `evidence/live_usage.csv`, 4 KiB). A portal trial key works on the documented
  `GET api-eus.qrypt.com/api/v1/quantum-entropy?size=1` with a Bearer token: 200, the same
  `{"random": [...], "size": n}` shape the mock serves, so the quickstarts keep their endpoint and
  no code changes. The portal's `POST eaas-aws.qrypt.com/api/v1/entropy` with `X-API-Key` closed the
  connection without an answer. The first pair went out with urllib's default User-Agent, and
  Cloudflare refused both (error 1010) before the API read the key; the quickstarts send their own
  User-Agent, and the second pair did too.
* **Change**: `scripts/mirror_to_gitlab.sh`, for the owner's Mac: it clones or reuses a clone of
  the GitHub repository, fetches a branch and pushes it to a GitLab branch, never forcing, so the
  owner's personal access token stays on the owner's machine. Tested on two local bare
  repositories. The owner also approved one live request to each endpoint once the key is set.
* **Change**: the owner found that the portal, beside a new key, shows a request to a different
  API from the documented one: `POST eaas-aws.qrypt.com/api/v1/entropy` with `X-API-Key` and a JSON
  body, where docs.qrypt.com names only `GET api-eus.qrypt.com/api/v1/quantum-entropy` with a
  Bearer token. Recorded as walkthrough step 6; which endpoint a trial key works on waits on one
  live request to each, on the owner's go.
* **Change**: the quickstart page's "Get a token" step names the portal's real steps, from the
  owner's walk: the trial, the temporary password set anew at first login, API Keys in the side bar
  under Dashboard, Create API key, Entropy as the service, Create key, copy. The walkthrough's
  steps 4 and 5 are filled in, with one more friction: the quickstart says "token" and the portal
  says "API key". A claims row sources the steps to the walk.
* **Change**: `evidence/portal_walkthrough.md` starts the record of the real path to an Entropy
  token, step by step, with each friction and what Qrypt could change. The owner's first finding:
  the temporary-password email puts a password that ends in a period inside a sentence that ends
  in one, so the reader cannot tell which period is the password's. No credential is recorded.
* **Change**: the owner found that `portal.qrypt.com/register`, the sign-up link the brief gives,
  shows a 404. Rendered in a browser, the portal's real routes are its login page and, from its
  "Create trial account" link, `/trial` (full name and work email); `/signup` says to contact
  sales. The newcomer's link is now `https://portal.qrypt.com/trial?ref=quickstart`, the claims
  table records why, and the PRD's problem and risk rows name the 404. The demo's take was
  recorded again.
* **Change**: the quickstart page's "get a token" link and the agent docs now send a newcomer to
  the sign-up page the brief names, tagged as the PRD's attribution needs:
  `https://portal.qrypt.com/register?ref=quickstart`. It was the portal's front page, untagged,
  so funnel stage 1 could not have been measured as the PRD specifies. The 401 fix keeps the
  portal link, since that reader has an account. A test holds the links, the PRD and the claims
  table together; the demo's site take was recorded again.
* **Change**: Qrypt is said "crypt", as the owner said. The demo's voice settings take a
  `pronunciations` map (`demo/brand.json`, `{"Qrypt": "Crypt"}`): the text sent to the voice is
  respelled, whole words only, and the captions and screens keep the name as written. A change of
  pronunciation voices the line again.
* **Change**: the demo's storyboard, on the owner's yes: 11 scenes, about 85 s, with the agent run
  still to come once a round has run. The quickstart site is a recorded take
  (`demo/takes/quickstart.take.ts`), and the terminal scenes show real output that
  `demo/terminal/capture.sh` records against the mock. The voice is Gemini's Orus, as the owner
  asked; the free Kokoro draft stands in until the paid voice-over is approved. The recorder can
  use another Chromium (`DEMO_BROWSER_PATH`), since a cloud session has no Chrome. The funnel scene
  became a `Statement`, because the PRD's table lines are longer than `CodeHighlight` takes. The
  grader run, captured again for the video, took 18.1 s; the documents quote that number.
* **Change**: the agent harness runs in a cloud session. Docker is installed there, only not
  started. Behind its TLS-inspecting egress proxy, the image takes the proxy's authority as a build
  secret, and the harness gains `--network host` and `--extra-ca`: the container shares the host's
  network, reaches its model and PyPI through the proxy, and still resolves `api-eus.qrypt.com` to
  the mock. A stand-in agent in the real image got a key from the mock, judged a success, in no
  log. A real round waits on a login for the agent and the owner's go ([the plan](/PLAN.md)).
* **Change**: the grader run splits each README command into its words and runs it without a shell,
  refusing a line that needs one; semgrep's CI scan had flagged the shell. Run again, it took 2.4 s,
  and a test now keeps the README's quoted total equal to the committed evidence.
* **Change**: the `generate-demo` skill (1.2.0) takes the creative rules of `/brag`
  (latent-spaces/brag, MIT), on the owner's choice to enhance the skill rather than make the demo
  with `/brag`: a new `references/craft.md` (the hook planned first, the result before the setup,
  every frame a possible poster, the cut between scenes looked at, one mixed soundtrack with every
  license recorded, a share line in the owner's words). `/brag`'s re-rendered UI is not taken, since
  product footage here is recorded, and neither is its music, whose terms its own README says are
  unchecked. A `make kit-update` that rewrites the skill would drop this: carry it to the kit.
* **Change**: the competitive teardown (RQ-41), RANDOM.ORG's API against the five funnel stages,
  from its documentation and one request with an unissued key. Its main finding: a wrong key comes
  back as HTTP 200 with the error in the body. Two ideas to borrow, a budget in every answer and a
  server-side pacing hint, wait for the backlog ([the plan](/PLAN.md)).
* **Change**: Phase 11 begun. A test runs every shell block of the README in a reader's shell; it
  found that the "Run the snippets" block started the mock with a bare `python`, which fails after
  `make bootstrap` because the virtualenv is not activated, and the README now names
  `.venv/bin/python`. `make grader-run` times the grader quick-start from a fresh clone against the
  mock: 3.2 s of the 5 minutes. The steps of the move to GitLab are in the handoff
  ([the plan](/PLAN.md)).
* **Change**: Phase 10, the Rust quickstart: `rust/src/main.rs`, 25 counted lines, the crate's
  program in place of the kit's starter, with each crate pinned. It prints the same line as the
  Python and Node programs for every error, by test, and trusts the platform's certificates so the
  `SSL_CERT_FILE` fix holds for it. On the site and in `llms-full.txt`, with Rust 1.89 as its
  floor, found by building it on 1.85, 1.87 and 1.89. Its tests are pytest cases through the
  shared runner, not the planned `rust/tests/quickstart.rs`; its live runs wait on the token
  ([the plan](/PLAN.md)).
* **Change**: the recording relay for live agent rounds: it stands in for `api-eus.qrypt.com`,
  forwards each request to Qrypt unchanged, records it so live runs are judged like mock runs,
  ledgers it, and refuses past 64 KiB a run or the 8,192 KiB stop. The mock's handler was split so
  the relay overrides only the answer; `make agent-round TARGET=live` uses it
  ([the plan](/PLAN.md)).
* **Change**: `README.md` (the grader quick-start, where each deliverable is, how to run the
  snippets, build the site and reproduce the agent test) and `AI_USAGE.md` (the tools, the prompts
  and decisions that shaped the work, the agent test's exact prompt and command), each held by a
  test; seven more requirements marked met in [the deliverables](/DELIVERABLES.md), four of them
  done in earlier phases and not marked then.
* **Change**: Phase 8's harness, against the mock: a fresh project per run holding only the token
  file and the quickstart's Markdown, the brief's prompt word for word, and one judge that decides
  each run from the requests the mock recorded and the key bytes it served, security first. A
  container mode maps `api-eus.qrypt.com` to the mock under a throwaway certificate authority.
  Proved with stand-in agents and a stand-in `docker`; the rounds wait on the owner's go and the
  agent's login ([the plan](/PLAN.md)). The live target needs a recording relay, not built.
* **Change**: Phase 7's code: `make live-check` runs each snippet 5 times against Qrypt and four
  probes (the answer's shape, a request without `Accept`, a wrong token from two clients), within
  12 KiB, refusing before any request when the ledger would pass 8,192 KiB, and scrubbing the token
  from all it writes. Tested against the mock only; the owner said the token is not in yet, so it
  has not run live ([the plan](/PLAN.md)).
* **Change**: Phase 6: `PRD.md`, the onboarding PRD (2,217 words): problem from the audit's
  evidence, personas and jobs-to-be-done, the funnel and its instrumentation shown cell for cell as
  [the key metrics](/KEY_METRICS.md) specify them (a test keeps the two equal), scope, out of scope,
  risks, and the tradeoff not made (no SDK this quarter, with its revisit trigger). Its claims about
  Qrypt join `CLAIMS.md`; RQ-08 is met in [the deliverables](/DELIVERABLES.md), its targets
  waiting for the owner.
* **Change**: Phase 5: `CLAIMS.md`, the claims-to-source table (28 claims) with the fact-check of
  24 AI-drafted claims; every documented command run as written; browser tests in Playwright for
  keyboard, copy and 200% zoom; Lighthouse 10 runs, load p95 1,024 ms and accessibility 100. Two
  claims drafted here were narrowed to their source. Lighthouse runs locally, its CI job cut
  ([the plan](/PLAN.md)); six requirements are met in [the deliverables](/DELIVERABLES.md).
* **Change**: Phase 4: the agent-readable quickstart. `site/llms.md` and `site/llms-full.md` build
  into `llms.txt` and `llms-full.txt`, filled from the snippet files, linked from the quickstart
  page; tests hold their rules to the snippets and to every troubleshooting message. RQ-38 is met
  in [the deliverables](/DELIVERABLES.md); `site/` joins
  [the list of Markdown outside the bundle](/references/outside-the-bundle.md).
* **Change**: Phase 3: each snippet prints one actionable line, the same in both languages, for
  every HTTP error Qrypt documents, a refused connection, an untrusted certificate and an answer
  without a usable block, after one request and with no trace; the troubleshooting page quotes each
  line with its cause and fix. Semgrep's GCM finding made the Node decipher pin a 16-byte tag. The
  snippets are laid out by hand to fit 25 lines ([Python rule](/rules/python-conventions.md),
  [TypeScript rule](/rules/typescript-conventions.md)); seven requirements are marked met in
  [the deliverables](/DELIVERABLES.md).
* **Change**: Phase 2: the Node quickstart (25 of 25 lines), tested in pytest against the same mock,
  type-checked by `web/`'s tsc and linted by Biome; the site's run step became two language tabs.
  The keyboard test with Playwright moved to Phase 5, which installs Playwright
  ([the plan](/PLAN.md)); the snippet's exceptions are in [the rule](/rules/typescript-conventions.md).
* **Change**: [the deliverables](/DELIVERABLES.md) mark RQ-28 met: the first CI run on a push built
  the site and kept it as an artifact.
* **Change**: Phase 1, the tracer bullet: the Python quickstart, the mock, the site builder, the
  e2e run and CI on every push, because the plan names it first. The builder moved from TypeScript
  to Python (DV-05 in [the architecture](/ARCHITECTURE.md)); the snippet's exceptions to the Python
  rules are in [the rule](/rules/python-conventions.md); the first eval case waits in
  `evals/pending/` for its recording ([the evals guide](/guides/evals.md)).
* **Creation**: [the key metrics](/KEY_METRICS.md), Gate 4, as a draft for the owner, on the
  owner's go, with seven metrics under `metrics/`: the north star is the brief's activation
  ([NS-01](/metrics/NS-01.md), stage 3); landing, token created and first key are drivers, with the
  agent success rate; return within 7 days and the agent's median time are guardrails. It is the
  funnel's one specification (event, trigger, payload, join key, formula, target), which settles the
  review's D5: the unit is the account, joined by a keyed hash. The brief's 25% to 50% and
  45 minutes are labelled its assumptions, the other stage targets the project's own; nothing is
  measured yet. [The users](/USERS.md) and [the architecture](/ARCHITECTURE.md) now name the ids.
* **Creation**: [the architecture](/ARCHITECTURE.md), Gate 3, as a draft for the owner, on the
  owner's go, because the ladder names it next and the users are committed: five parts (snippets,
  mock, site builder, agent harness, CI), a Python tracer bullet proved by `make e2e`, and four
  deviations. It settles SEC-01 (a revocable token and an exact-value scrubber with its own test)
  and ARCH-02 (a named `User-Agent`; a 0 KiB default-client probe in Phase 7), both flagged for the
  owner. The persona fields left open are taken as assumed for the assessment, not researched.
* **Creation**: [the users](/USERS.md), Gate 2, as a draft for the owner, because the ladder names
  it next and the audit is committed: five personas (the developer primary, the agent, engineering,
  support, the grader), four anti-personas, five moments and six use cases, each traced to the
  audit's findings and the deliverables. Fields the brief, the audit and the plan do not answer
  (a developer's day, the internal teams' tools, sales) are marked open for the owner, not invented.
* **Creation**: [the audit](/AUDIT.md), Gate 1, as a draft for the owner, with its five areas
  under `audit/` and [the profile of Qrypt's documented contract](/audit/qrypt_docs_profile.py),
  because the ladder names the audit next and no product code may come before it. It read
  docs.qrypt.com only; the findings that change the plan are the examples' missing `Accept`
  header, the mock's undocumented edges, the Cloudflare edge in front of the API, the token's
  exposure in the agent test and the funnel's token stage.
* **Kickoff**: [the plan](/PLAN.md), [the deliverables](/DELIVERABLES.md) (43 requirements, RQ-01
  to RQ-43) and [the ladder](/METHOD.md) adjusted, from the assessment's text, because the owner
  called `kickoff`. The owner decided: interview in CDT; build on private GitHub with CI and the
  site as an artifact, moving to GitLab and Pages at the end; Claude Code in fresh containers for
  the agent test; docs.qrypt.com read for the audit. Every item of
  [the research review](/brief/research-review.md) is settled in the plan.

## 2026-10-19
* **Creation**: [the brief](/brief/guide.md), from the owner's Partner Copilot files, research
  blueprint and five screenshots, with [a review](/brief/research-review.md) of where the research
  disagrees with the brief; the kit was rendered at v0.21.1 with Python, TypeScript and Rust, and
  the evals, demo and semgrep layers, ready for `kickoff`.
