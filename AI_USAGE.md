# AI usage

Which AI tools this project used, for what, and the prompts and configuration that shaped it. A
test (`tests/test_readme_and_ai_usage.py`) keeps the agent-readiness test's prompt and command below
equal to the ones the harness runs.

## The tools, and what each did

| Tool | Used for | What a person decided or checked |
|---|---|---|
| **Claude Code** (Anthropic's coding agent), in cloud sessions | Nearly everything in this repository: the plan, the audit, the users, the architecture and the key metrics; the two quickstart programs, the mock, the site builder, the tests and CI; the site's pages, `llms.txt`, `PRD.md` and `CLAIMS.md`; the live check and the agent-readiness harness. It also read Qrypt's documentation pages for the audit and the claims table, through its web-fetch tool, which summarizes a page rather than returning its raw text | The owner made every decision below, approved each install and each push, and has not yet approved the plan, the PRD's targets or its tradeoff |
| **Gauntlet's Partner Copilot** | The partner notes: a deep dive on Qrypt and the friction of its first run | Kept private, as input only |
| **An AI research tool** | A research blueprint and five design mock-ups (an entropy-to-key diagram, Diátaxis quadrants, an agent failure taxonomy, a funnel dashboard, a RICE roadmap) | Treated as unverified input: every claim from them was checked before use (below) |
| **Claude Code**, again, as the agent under test | The subject of the agent-readiness test | The harness judges each run from what happened, not from what the agent reports |

Lighthouse, Playwright, Semgrep and gitleaks are tools, not AI; they measured and scanned.

## How the work was steered

- **The repository's rules.** `AGENTS.md` sets the working rules for any coding agent: ask before
  a paid run, a push, an install or a deploy; test first; never weaken a check to pass it; no
  secrets in code, logs or commits; an agent never reads `.env`. Hooks enforce the last one, and
  the gate (`make gate`) is the definition of done for every commit.
- **A gated method.** The work moved through the gates in `docs/METHOD.md`: kickoff, audit, users,
  architecture, key metrics, then a tracer bullet and vertical slices, each with its tests written
  and seen to fail first.
- **The owner's kickoff prompt**, in substance: plan the take-home from the assessment's text; read
  the brief's other files as context, the assessment winning wherever they disagree; treat the
  research and the screenshots as unverified and settle each item of the research review in the
  plan; Python at the root, Node in `web/`, Rust as a stretch; finish before the interview; keep
  live Qrypt use to 10,240 KiB or less, and run everything against a mock until there is a token.
- **The owner's decisions along the way**, each recorded in `docs/PLAN.md` or `HANDOFF.md`: the
  interview's time zone; build on a private GitHub repository and move to GitLab Pages at the end;
  Claude Code in a fresh container for the agent test; Qrypt's docs read-only; installs of
  `cryptography`, `python-dotenv`, Playwright and Lighthouse; pushes without asking for the rest of
  the plan; the PRD before the live check; the agent rounds against the mock first.

## Fact-check of AI-drafted content

**24 AI-drafted claims** from the research and from this project's own drafts were checked against
a source before reaching the site or the PRD: 3 verified, 1 relabelled as an assumption, 20
corrected or dropped. The table and each verdict are in [`CLAIMS.md`](CLAIMS.md), with every claim
the site and the PRD make about Qrypt and its source.

## The agent-readiness test: the exact agent, prompt and configuration

- **Agent:** Claude Code, the version pinned in `agent-harness/Dockerfile`:
  `@anthropic-ai/claude-code@2.1.304`, run headless, its model the account's default.
- **Environment:** a new Docker container per run (`agent-harness/Dockerfile`: Node.js 22, Python 3,
  Claude Code), holding one project folder with two files: `.env` with `QRYPT_API_KEY`, and the
  quickstart's Markdown (`llms-full.txt`) as `qrypt-quickstart.md`. Nothing else: no repository, no
  `CLAUDE.md`, no settings.
- **Command**, in the container's project folder (`{prompt}` is replaced by the prompt below):

  ```text
  claude -p {prompt} --output-format stream-json --verbose --permission-mode bypassPermissions
  ```

  Permission prompts are off because the container is the sandbox: it holds only the project.
- **Prompt**, the brief's word for word, then one line naming the quickstart's Markdown (the brief
  allows "the quickstart URL (or its Markdown)"; the site is not deployed until the move to GitLab):

  ```text
  Generate an AES-256 key using Qrypt quantum entropy in a new project

  The quickstart's documentation is in qrypt-quickstart.md.
  ```

- **Target:** the local mock first, with `api-eus.qrypt.com` mapped to it inside the container;
  Qrypt's live API once the owner's token is in and a recording relay is built.
- **Judging:** by `src/qrypt_quickstart/agent_harness.py`, from the requests the recording server
  received and the key bytes it served: success, or the first failure category that applies.
  Transcripts are kept with the token's value scrubbed.

## The eval suite's prompt

The eval cases in `evals/pending/` give a model the quickstart page and the brief's prompt in one
turn, with the system prompt in `src/qrypt_quickstart/prompts/agent.md`. They have not been recorded:
recording is a paid run that waits on the owner's model key and approval.
