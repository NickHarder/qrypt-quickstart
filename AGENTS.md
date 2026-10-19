# Qrypt Quickstart

Python, Node and Rust quickstart, agent-verified llms.txt and onboarding funnel for Qrypt Quantum Entropy.

These are the project's instructions for any coding agent. Claude Code and Cursor read this file directly.

## Read first

1. `HANDOFF.md`: where things stand, what is settled, what is open for the owner.
2. `docs/index.md`: what the project knows, a level at a time. Open only what the task needs.

## Commands

| Command | What it does |
|---|---|
| `make tools` | The gate's tools, at CI's versions (on a Mac, `brew`). |
| `make bootstrap` | Once per clone: what the gate needs, and the git hooks. |
| `make gate` | Everything a push must pass. $0, offline. `make gate-lint` runs one group. |
| `make checks` | The project's own checks in any language (`scripts/checks.conf`); `make check C=<name>` runs one. |
| `make docs-index` | After a change under `docs/`: write its index files again. |
| `make look-ahead` | Before a pull request: what else may have to change. |
| `make blockers` | What blocks the work, and where the plan needs the owner. |
| `make skill-costs S=…` | A skill's past cost, in tokens. |
| `make help` | The full list. |

The gate is defined once, in `scripts/gate.sh`. Run it, not an approximation of it. Hooks in
`.claude/settings.json` ready each cloud session, refuse a shell command that reads a `.env` or
force-pushes, and run the lint group before a turn that changed files ends: fix what it names.

## Working rules

1. **Ask the owner before:** a paid model run (say the dollar estimate; a free replay comes first) ·
   anything on production · any `git push`, tag or deploy · any new install on the owner's machine.
2. **Commit locally at every checkpoint**, on a `feat/…` branch, with Conventional Commits. Never
   force-push; a red pipeline gets an ordinary commit on top.
3. **Test first.** Write the test or the eval case, watch it fail, then write the code.
4. **Never weaken a check to make it pass.** A test, an eval expectation, a threshold or a baseline
   changes only with the reason stated in the same change.
5. **Tracer bullet, then vertical slices** (`docs/METHOD.md`). **Every decision is defensible**
   (`defend-decision`).
6. **No secrets or sensitive data** in code, logs, traces, eval output or commits.
7. **Describe the current state:** no sprint or week names in code or configuration; history
   belongs in `docs/log.md`.
8. **Verify before claiming.** Read the source or run the command. Another AI's notes are input.
9. **The repository's documents are the source of truth, not memory:** a durable fact goes in its
   document in the same change.

## Knowledge

`docs/` is an Open Knowledge Format bundle, which the gate checks: write every document there with
the `write-okf-concept` skill, never beside the code. `make docs-approve` and `make
docs-reopen` are the owner's calls: run one only when the owner has said to.

## Code conventions

For every language in this repository:

1. **Names say what the thing is.** Long and descriptive, with the unit, and no abbreviation a
   newcomer would have to look up. The few exceptions are in the language's own rules.
2. **Assign once.** A new name for each intermediate value, so every stage of a computation is
   visible in a debugger and in a stack trace; never rebind a parameter or reuse a name. The few
   exceptions are in the language's own rules.
3. **Type everything**, with the language's strictest checking; an escape hatch gives its reason.
4. **Document as you go.** A doc comment on every module, class and function, changed in the same
   commit as the behavior.

Read a language's rules, which say how these are checked, before you write or change a file in it:
- The Python project lives in `.`: `docs/rules/python-conventions.md`.
- The TypeScript project lives in `web`: `docs/rules/typescript-conventions.md`.
- The Rust crate lives in `rust`: `docs/rules/rust-conventions.md`.

## Skills

Each gate in `docs/METHOD.md` has a skill (`.claude/skills/`): `kickoff` (`docs/PLAN.md`),
`audit-codebase` (`docs/AUDIT.md`), `define-personas` (`docs/USERS.md`), `plan-architecture`
(`docs/ARCHITECTURE.md`), `define-key-metrics` (`docs/KEY_METRICS.md`), `write-evals` (`evals/`).
Start one on your own only under the conditions its text states; the hook before a skill run asks
for a second run of a gate or one over the cap. `kickoff`, `audit-security`, `set-up-deploy` and `generate-demo` run only
when the owner calls them by name. The others: `align`, `defend-decision`, `handoff`,
`estimate-tokens`, `blockers`, `write-okf-concept`, and `look-ahead`, which closes every pull
request and has the `reviewer` sub-agent read the change first.

## Demo video

`demo/` makes the demo video, with the `generate-demo` skill only. Product footage is recorded, never
generated; `make demo-stills` and `make demo-draft` cost $0. `make demo-approve`, `make
demo-reopen` and `make demo-voice CONFIRM=1` are the owner's calls. Its TypeScript follows
`docs/rules/typescript-conventions.md`; read it before you write or change a file there.

## Keys and settings

Every key lives in the root `.env`; `.env.example` names each, and a new key gets its line there in
the same commit. An agent never reads `.env`: a key it reads goes to the
model provider and into the transcript. The settings and the guard refuse it; ask the owner instead.

