---
name: align
description: Makes sure the agent and the owner mean the same thing before a plan, a feature or any change that is not trivial. It reads what the repository already settles, says what it found, asks at most four questions whose answers change the work, each with a recommendation, and then goes on with the answers. Use when the owner types /align or asks to align before the work, and before a plan or a feature whose request leaves one of the owner's decisions open.
metadata:
  version: "1.0.0"
---

# Align, then go

One round of questions before the work, then the work. The owner asks for it in the words "Ask
any questions to make sure we align, otherwise go." The questions are only those whose answers
change what is done next; everything else the agent finds out or decides, and says so.

## 1. Read what is already settled

Before asking anything, read what the repository already says about the request: `HANDOFF.md`,
`AGENTS.md`, the plan (`docs/PLAN.md`, or the plan in this conversation), the decision records, and
the code and documents the request touches. Run the command or read the file that answers a
question of fact. A question the repository answers is not asked.

## 2. Say what you found

In a few lines, before the questions:

- What the request asks, in your words.
- Each fact that changes it, with its evidence (`path:line`, a command and its output). A fact that
  goes against the request comes first.
- What you will do by default where nothing needs the owner.

## 3. Ask what only the owner can decide

- Ask only what changes the work: its scope, what is cut, a choice between two designs, who acts
  where the owner's rules say they do (a merge, a push, a tag, a deploy), a paid run with its dollar
  estimate, a creative call (wording, pacing, look).
- Do not ask what a convention, the code or a sensible default answers: pick it, and name it in the
  default of step 2.
- At most four questions, all in one message. Each has two to four options, the recommended one
  first and marked "(Recommended)", each option with what it means and what it costs. In Claude
  Code, use the AskUserQuestion tool; elsewhere, a numbered list the owner answers by number.
- Nothing to ask is an answer: say "Nothing to ask; going on with" and the default, and go.

## 4. Go

- Carry on with the answers. Do not ask "shall I start?": the answers were the go.
- The answers do not lift the owner's "Ask first" rules. A push, a tag, a deploy, a paid run or an
  install still asks, unless an answer here said yes to that very step.
- When the owner says "stand by", wait for their go.
- Record the answers, dated and word for word, where the work's record lives: the plan's decisions
  locked with the owner, or the plan in this conversation. Do not reopen them later unless the
  evidence changes.
- If a fact found later changes an answer, stop and align again on that point alone.

## Rules

- One round. A second only when an answer opens a decision the first could not see.
- Never ask what you can find out, and never read `.env` to answer a question: ask the owner.
- The questions come before the plan; do not hide a plan inside them.
