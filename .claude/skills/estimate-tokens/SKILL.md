---
name: estimate-tokens
description: Says what a skill will cost before it runs, from what it cost before. `make skill-costs S=<skill>` reads the transcripts on this machine and the project's ledger and gives the median output tokens of the skill's runs, or its floor and the words "no history" when it has never run. Use when the owner or an agent asks what a skill will cost, before a skill that asks over a cap is started, or when deciding whether a run is worth it. It never runs the skill it estimates.
metadata:
  version: "1.1.0"
---

# Estimate a skill's tokens

A skill's cost is the work that follows its instructions, which only a run reveals: there is no dry
run. What there is: every run before, on this machine (Claude Code keeps a session's transcript
thirty days) and in the project's ledger (`.claude/skill-costs.jsonl`, committed, which `look-ahead`
appends before each pull request). The estimate is the median of those runs, in tokens. Not dollars:
prices move, and a subscription has no per-run price.

## Steps

1. `make skill-costs S=<skill>` (in the kit: `uv run python -B template/scripts/skill_costs.py report <skill>`).
2. Report its lines as they are: the estimate, how many runs it comes from, the largest, the last
   run's date, the models, and the floor.
3. "No history" is the answer when that is the truth. Give the floor (the skill's own text, at four
   characters a token), say that the first run sets the estimate, and do not guess a number.
4. Nothing else. Do not run the skill it estimates, and do not convert to dollars.

## Reading the number

- **Output tokens** are what the model wrote, thinking included: the part that scales with the work.
  **Tokens read** is what the run's turns took in, cached mostly, summed; it grows with the session's
  context, so a run late in a long session reads more than the same run early.
- **The largest run** says what it can be. A skill whose largest is many times its median depends on
  its input: an audit of a large codebase, evals for a wide slice.
- A run is counted from the skill's marker to the owner's next prompt. A skill typed as `/skill` is
  counted exactly; one the model invokes in the middle of a turn is counted to the end of that turn,
  and so includes what followed it. The median moves little for one such run once there are others.
- A skill that runs in a sub-agent of its own (`context: fork`) is counted from the sub-agent's
  transcript. A sub-agent's transcript writes a response's usage before the response ends, so such
  a run is counted from what its responses wrote, at four characters a token, without the thinking,
  and the line says **approximate**: a lower bound, not a count. Say so when you report it.
- `make skill-costs` without `S` lists every skill with history, one line each.
