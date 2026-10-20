# History

What changed in this project and why, newest first. A commit shows the difference; an entry here
gives the reason. The `handoff` skill adds to it at every checkpoint, and the `write-okf-concept`
skill has the format.

## 2026-10-20
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
