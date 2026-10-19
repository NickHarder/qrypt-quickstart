---
name: blockers
description: Lists what blocks the work now and where the current plan will need the owner, each with who unblocks it and how. `make blockers` gives the mechanical half (the gate, git, the next gate and what the hook would say, documents and deliverables that wait on the owner, the handoff's open items, the plan's `**You act:**` lines); the skill walks the plan for the points no line marks. Use when the owner asks what is blocked or what will need them, before starting a plan, or when the agent is stuck. It reports only.
metadata:
  version: "1.0.1"
---

# Blockers, now and ahead

Two questions, one report: what holds the work up right now, and where the plan will need the
owner (a human in the loop) before it is done. The owner's rules say when they act: "Ask first" in
the standing rules, `AGENTS.md` for who decides what. This skill finds each such point; it never
clears one itself.

## Now

1. Run `make blockers` (in the kit: `uv run python -B template/scripts/blockers.py`). With a plan
   that is not `docs/PLAN.md`, add `PLAN=<file>` (in the kit, `--plan <file>`). It takes a few
   seconds: it runs the gate. `--no-gate` skips that when the gate has just run.
2. Report each `blocked:` and `waits:` line as it is: what, who unblocks it, the command or the
   decision. Say which the agent can clear now (a red group, a file to commit) and which only the
   owner can (a push, an approval, a call of `kickoff`, a yes to a gate skill that would ask).
3. `next:` names the gate that comes next and whether it may start on its own. It is not a
   blocker; say it so the owner knows what follows.

## Ahead

1. Find the current plan, the first of: the plan in this conversation (approved, or the plan-mode
   file); `docs/PLAN.md`'s phases; the newest file in `docs/plans/`; the handoff's open items.
2. Every `**You act:**` line is a point the plan already names: take it as written. `make
   blockers` lists those of `docs/PLAN.md`.
3. Walk every other step of the plan, in order, and ask of each whether it is one of these kinds.
   Name the kind, and the rule or command it comes from:

   | Kind | Where the rule is |
   |---|---|
   | paid run | "Ask first": say the dollar estimate, the free replay first |
   | production | "Ask first" |
   | push, tag or deploy | "Ask first" |
   | install on the owner's machine | "Ask first" (`make tools`, `brew`, a new package) |
   | second gate run, or one over the cap | the hook before a skill call; `make skill-costs S=<skill>` |
   | approval | `make docs-approve`, `make demo-approve`, `make demo-reopen` |
   | creative call | wording, pacing, look: the owner decides |
   | owner-only skill | `kickoff`, `audit-security`, `generate-demo`, `set-up-deploy`: called by name |
   | stand by | the owner said "stand by" |
   | credential or account | a key in `.env` (never read it), a login, a repository's access |

4. A step that needs the owner and has no `**You act:**` line: flag it as missing from the plan.
   A step you are unsure of: list it, marked "inferred".

## The report

- **Now**, then **Ahead**, each a table, most urgent first:
  `| When | What | Kind | Who | What unblocks it |`.
- Then, in one line each: the next point where the owner must act, and what can go on without
  them until then.
- Nothing found is an answer: say so in one line.

## Rules

- Report only. Do not run, approve, push, tag, install or pay for anything this lists, and do not
  write the handoff: the `handoff` skill writes "Open, for the owner".
- Never read `.env` to see whether a key is set: ask the owner.
- A plan's point where the owner acts is a line of its own: `**You act:** <what> (<kind>)`. When
  you write a plan, mark each one so.
