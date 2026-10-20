---
type: Method
title: "Method: gated, skill-driven delivery"
description: The gates this project moves through, the skill behind each one, and the build order.
status: stable
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-20T00:10:00Z }
---

# Method: gated, skill-driven delivery

Work proceeds as a ladder of gates. Each gate is driven by one skill and produces its artifact (the
first gate produces three). The next gate does not start until that is committed. The skills are in `.claude/skills/`, or in the
owner's `~/.claude/skills/` when the project does not carry its own copy; Claude Code and Cursor read
both places.

| Gate | Skill | Artifact |
|---|---|---|
| 0 | `kickoff` | `docs/PLAN.md`, this ladder adjusted to the project, `docs/DELIVERABLES.md` |
| 1 | `audit-codebase` | `docs/AUDIT.md` (**hard gate**: no product code before it). Adjusted: there is no codebase to audit, so the audit covers the system the project builds on, Qrypt's first-run path (docs.qrypt.com/eaas and the API contract it documents), read only, with no live call |
| 2 | `define-personas` | `docs/USERS.md`, which `PRD.md` draws its personas and jobs-to-be-done from |
| 3 | `plan-architecture` | `docs/ARCHITECTURE.md`, kept short: the snippets, the mock, the site builder and the agent harness |
| 4 | `define-key-metrics` | `docs/KEY_METRICS.md`: the activation funnel's five stages, which `PRD.md` shows and a test keeps equal |
| 5 | `write-evals`, then the build | The tracer bullet: the Python quickstart end to end (Phase 1 of `docs/PLAN.md`), with its test and its eval case, gate green |
| 6 and on | `write-evals`, then the build | Vertical slices, one at a time (Phases 2 to 11 of `docs/PLAN.md`) |

The brief names its own deliverables (`PRD.md`, `AGENT_READINESS.md`, `BACKLOG.md`, `CLAIMS.md`,
`AI_USAGE.md`). They live at the repository's root, where a grader looks, and draw on the gate
artifacts above; `docs/PLAN.md` gives the reason. No gate is removed: each one's artifact feeds a
deliverable, and the gates run lean, one run each, because the timebox is two days.

A gate skill runs on its own when this ladder names it as the next gate and the previous artifact is
committed, its inputs exist, its estimate (`make skill-costs`) is not over the project's cap and its
result is a draft; a first run has no estimate and goes. It asks first, with the number, over the
cap, and for a second run of a gate whose artifact exists: that run is the owner's to start.
`kickoff` runs only when the owner calls it: it needs the owner's brief.

Cross-cutting: `defend-decision` writes the claim / evidence / alternative / why rejected / how to
reverse block used in every document. `handoff` keeps `HANDOFF.md` current. `look-ahead` closes a
change in one pull request: what else has to change with the code, done in the same branch.
`estimate-tokens` says what a skill will cost before it runs, from what it cost before.
`blockers` says what holds the work up now and where the plan will need the owner.
`align` asks, once and before a plan or a feature, only what changes the work, then goes on.
`audit-security` runs the slow security scan, only when the owner asks.
`generate-demo` makes the demo video.
`write-okf-concept` keeps every document under `docs/` a concept of one knowledge bundle, which the
gate checks.

## Build order: tracer bullet, then vertical slices

- The first build gate after the architecture is a **tracer bullet**: one real feature, thin, through
  every layer the architecture names (input, logic, model call, storage, output, one test, one eval
  case, the gate, CI, and the deploy path if there is one, which the owner sets up with the
  `set-up-deploy` skill). It is done when the gate is green on it end to end.
- No second feature and no horizontal work (a complete data layer, a full API surface, a shared
  abstraction) starts before the tracer bullet is committed and green.
- After it, work proceeds one **vertical slice** at a time. A slice is one user-visible capability with
  its own test and eval case, and it leaves the gate green.
- A layer is widened only when a slice needs it.
- Anything the tracer bullet shows to be wrong in the architecture goes into the `docs/ARCHITECTURE.md`
  deviation register before the next slice starts.

## Rules the skills enforce

1. A finding without a reproduction is not a finding.
2. Every capability traces to a `docs/USERS.md` use case, a `docs/AUDIT.md` finding and an eval
   category.
3. A departure from the brief or the plan goes in the `docs/ARCHITECTURE.md` deviation register, with
   evidence and a substitute.
4. No product code exists before `docs/AUDIT.md` is written.
5. No horizontal work exists before the tracer bullet is green.
6. A test or an eval case is written, and seen to fail, before the code that makes it pass.
7. Every eval case names the use case or finding it guards and the key metric it feeds, by id.
   `make trace` prints the chain from the north star down, and the gate fails on an id that is
   defined nowhere.
