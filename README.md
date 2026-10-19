# Qrypt Quickstart

Python, Node and Rust quickstart, agent-verified llms.txt and onboarding funnel for Qrypt Quantum Entropy.

## The brief

A Gauntlet partner project for Qrypt Inc: get a new developer, or their AI coding agent, from
"never heard of Qrypt" to a working AES-256 key made from quantum entropy, and prove it with data.
The brief, the partner notes, the research and the design screenshots are in
[`docs/brief/`](docs/brief/guide.md); start there. The plan comes from the `kickoff` skill.

## Quick start

```bash
make bootstrap    # once per clone: what the gate needs, and the git hooks
make gate         # everything a push must pass; $0, offline
```

## What's here

Skills, which Claude Code and Cursor both run from `.claude/skills/`:

| Skill | What it does | Who starts it | Writes |
|---|---|---|---|
| `kickoff` | Turns your brief into the plan, the gate ladder and the deliverables | You, by name | `docs/PLAN.md`, `docs/DELIVERABLES.md` |
| `audit-codebase` | Audits what the project builds on, one sub-agent per area, skipping the kit's unchanged files | An agent, within the cap | `docs/AUDIT.md` |
| `define-personas` | The users, the moments in their day, the use cases | An agent, within the cap | `docs/USERS.md` |
| `plan-architecture` | Trust boundaries, one request traced, the tracer bullet | An agent, within the cap | `docs/ARCHITECTURE.md` |
| `define-key-metrics` | One north star, its drivers and guardrails, each with a real source | An agent, within the cap | `docs/KEY_METRICS.md`, `docs/metrics/` |
| `write-evals` | Eval cases planned from the north star down, each naming what it guards | An agent, within the cap | cases under `evals/` |
| `align` | Before a plan or a feature: what the repository settles, then only the questions that change the work, then the work | You, or an agent, when it fits | nothing: questions, then the work |
| `handoff` | Says where things stand, so the next session starts from the repository | An agent, when it fits | `HANDOFF.md` |
| `look-ahead` | Closes a change in one pull request: what else has to change with it | An agent, when it fits | the documents, tests, handoff and log of the branch |
| `blockers` | What blocks the work now, and where the plan will need you | An agent, when it fits | nothing: a report |
| `estimate-tokens` | What a skill will cost, from what it cost before | An agent, when it fits | nothing: a number |
| `defend-decision` | Claim, evidence, alternative, why rejected, how to reverse | An agent, when it fits | a decision block in the document at hand |
| `write-okf-concept` | Keeps every document a concept of the bundle | An agent, when it fits | any document under `docs/` |
| `audit-security` | The slow security scan: secrets, static analysis, dependencies | You, by name | `docs/audit/security-review.md` |
| `set-up-deploy` | The deploy path through CI: dev on every merge, production after your approval | You, by name | the deploy workflow, a decision record, the handoff |
| `generate-demo` | The demo video from one storyboard | You, by name | `demo/`, the cut under `demo/out/` |

"Within the cap": a first run goes and sets the estimate; a second run, or one estimated over
`SKILL_RUN_CAP_TOKENS` in `scripts/kit.conf`, asks you first.

The commands you will use most: `make bootstrap` once per clone, `make gate` before a push,
`make blockers` for what waits on you, `make docs-status` for where each document stands, and
`make docs-approve DOC=<file>` to approve one (yours alone). `make help` lists every command.
Your code's own lint and tests, in any language, go in `scripts/checks.conf`, one a line; the gate and
CI run them, and `make checks` lists them.

## Where to look

- [`HANDOFF.md`](HANDOFF.md): where things stand.
- [`AGENTS.md`](AGENTS.md): the working rules and conventions, for people and for coding agents.
- [`docs/index.md`](docs/index.md): what the project knows, a level at a time.
  [`docs/METHOD.md`](docs/METHOD.md) is the gates this project moves through, and the build order.
