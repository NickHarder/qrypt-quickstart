---
name: look-ahead
description: Closes a change in one pull request. It runs the gate, the bundle check and `make look-ahead`, reads their notes, and changes in the same branch what has to change with the code (the documents that name it, the tests beside it, the handoff, the log, a skill's version and the lock), then writes the pull request's text and says what still needs the owner. Use when the work on a branch is done and a pull request is about to be opened or updated, or when the owner asks what else a change touches.
metadata:
  version: "1.2.0"
---

# Look ahead before a pull request

A change is finished when one pull request carries it whole: the code, its tests, and everything
that describes it. This skill finds the rest and does it, in the same branch. Nothing here is
approved, pushed or tagged: those stay the owner's calls.

## Run first

1. The gate (`make gate`; the kit's `AGENTS.md` says what the kit runs instead), and fix what is red.
2. The bundle check's notes. The gate runs it; read its `note:` lines. A drift note names a record
   whose source changed after the record was last written.
3. `make look-ahead`: what this branch changed since `main`, and what may have to change with it.

Every line that starts with `note:` is something to read and decide. None is a failure, and none is
answered by deleting the sentence that caused it.

## For each note

- **A document names a changed file and is unchanged.** Read the sentence. If it still holds, leave
  it. If it does not, change it to what is true now; for a concept under `docs/`, the
  `write-okf-concept` skill says how, and `generated` is set again.
- **A drift note on a record.** Read the record against the code it names. Rewrite what no longer
  holds. Set `generated` again either way, so the note clears only because someone read it.
- **Code changed with no test changed.** Write the test and watch it fail, or say why none is needed.
- **A make target missing from the help header or the `AGENTS.md` table.** Add both lines.
- **The handoff is unchanged, or describes this change as still to come.** Refresh it with the
  `handoff` skill, written as it will be true once the change is merged.
- **The log is unchanged.** Add the entry under today's date: what changed and why.

## Then

1. A skill changed: bump its `metadata.version`. In the kit, `uv run python scripts/skills_lock.py`.
2. Append the skill ledger: `scripts/skill_costs.py append` (in the kit,
   `uv run python -B template/scripts/skill_costs.py append`) writes this project's skill runs
   from this machine's transcripts to `.claude/skill-costs.jsonl`, each once; commit it with the
   change. A cloud session's transcripts go with its container, so this is where they survive.
3. `make docs-index`, and the gate once more.
4. Have the `reviewer` sub-agent (`.claude/agents/reviewer.md`) read the change in a context of its
   own: give it the base branch and the plan the change carries out, if there is one, and nothing
   else. It reports only gaps that affect correctness or a stated requirement. Read each against
   the code, as you would any model's finding: close one that holds, in this branch, with its test
   first, and run the gate again; one that does not hold is left, with the reason in the report.
   Run it once per pull request, not until it finds nothing.
5. Write the pull request's text: what changed and why, what was checked and how, and what needs
   the owner (a record whose claim no longer holds, an approval, a value to decide).
6. Report, in one list: what changed because of a note or the review, what was read and left as
   it was and why, and what waits for the owner.
