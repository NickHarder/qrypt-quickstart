# History

What changed in this project and why, newest first. A commit shows the difference; an entry here
gives the reason. The `handoff` skill adds to it at every checkpoint, and the `write-okf-concept`
skill has the format.

## 2026-10-20
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
