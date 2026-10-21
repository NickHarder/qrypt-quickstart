# Handoff: Qrypt Quickstart

If you are picking this work up, human or model: read this file top to bottom first. The `handoff` skill
refreshes it; it describes the current state.

Last updated: 2026-10-20, after the agent test (5 of 5 in round 1, round 2 and round 2-live against Qrypt) and Phase 10: the three quickstarts, the site, the claims table, the
onboarding PRD and the agent harness are done against the mock; the token works on the documented
endpoint, and the live check passed 15 of 15.

This is the Qrypt Developer Quickstart & Onboarding Funnel take-home (Product Manager role), due
before the interview on Wednesday 2026-10-21 at 13:30 CDT (18:30 UTC). Start with `docs/PLAN.md`.

## Where things stand

| Area | State | Proof |
|---|---|---|
| Scaffold | Created from the kit | `.copier-answers.yml` |
| The brief | Filed as concepts in `docs/brief/`: the portal brief, the assessment's full text, the partner notes, the AI research blueprint, the five design screenshots, and a review of where the research disagrees with the brief | `docs/brief/guide.md` |
| Gate | Green (6 lint checks, 3 test checks with `e2e`, evals, secrets) | `make gate` |
| Plan and gates 1–4 | Drafts, all pushed, none approved yet: plan, audit, personas, architecture, key metrics | `docs/PLAN.md`, `make docs-status` |
| Phase 1, tracer bullet | Done: `quickstart/python/quickstart.py` (19 of 25 lines), the mock, the site builder, CI on push with the site as an artifact | `make e2e` |
| Phase 2, Node and tabs | Done: `quickstart/node/quickstart.mjs`, the site's run step in Python and Node.js tabs | `make e2e` |
| Phase 3, errors | Done: both snippets at 25 of 25 lines, one message per failure, `site/troubleshooting.html` | `tests/test_quickstart_errors.py` |
| Phase 4, llms.txt | Done: `llms.txt` and `llms-full.txt`, built from `site/*.md` and the snippet files, linked from the quickstart | `tests/test_llms_txt.py` |
| Phase 5, claims and quality | Done: `CLAIMS.md`, documented commands run as written, browser tests, Lighthouse (load p95 1,024 ms, accessibility 100) | `make lighthouse`, `tests/test_claims.py` |
| Phase 6, PRD | Done, draft: `PRD.md`; its targets and its tradeoff wait for the owner's approval | `tests/test_prd.py` |
| Phase 7, live check | Done 2026-10-20: 15 of 15 (Python, Node, Rust), medians 0.42 / 0.51 / 0.51 s, slowest 0.66 s, with requests 2 s apart. A trial key's real rate limit is far below the documented 30 in 10 s (a 429 at 0.36 s; cleared within 1.5 s; no `Retry-After`): the snippets' 429 message, the troubleshooting page, `llms.md` and claims follow it. Without `Accept`, still 200 JSON. A wrong token gets 403, not 401. Ledger at 40 KiB | `evidence/live_runs.csv`, `evidence/live_rate_limit.json` |
| Phase 8, agent test | Done 2026-10-20: round 1 against the mock 5 of 5 (median 0.49 minutes), the docs revised from it (Python packages in a virtual environment, `7272405`), round 2 against the mock 5 of 5 (0.54), and round 2-live against Qrypt through the recording relay 5 of 5 (0.61; 5 KiB, the ledger at 45 KiB) | `AGENT_READINESS.md`, `tests/test_agent_readiness.py` |
| Phase 9, backlog | Done 2026-10-20: ten RICE-scored items, nine of them Qrypt's to fix; reach rests on the PRD's assumed 400 signups a quarter; its scores and wording wait on the owner's review | `BACKLOG.md`, `BACKLOG.csv`, `tests/test_backlog.py` |
| Backlog B-07 | Done 2026-10-20 against the mock: Claude Code on Haiku 5 of 5 (0.51 minutes), Gemini CLI 1 of 5 once the `token-file-read` check its transcripts led to was added (four runs asked for the token file; its own tool refused), with 11 requests in 5 runs; the docs now forbid both. On the new rule, 2 of 5: one request a run, but three runs asked for the token file in the same turn as the docs, before the rule could reach them (taxonomy: Open) | `AGENT_READINESS.md`, "Other agents" |
| Agent token settings | Checked 2026-10-20: Claude Code's deny rules kept the token file from its file tool and its shell; Gemini CLI got it through its shell whatever the ignore files said. The troubleshooting page's key-handling list says so | `evidence/agent_token_guards.md` |
| Phase 10, Rust | Done against the mock: `rust/src/main.rs` (25 of 25 lines), a Rust tab and `llms-full.txt` section; its 5 live runs wait on the token (they make the live check 17 KiB) | `tests/test_quickstart_rust.py` |
| Phase 11, submission | Begun: the site is live at `https://nickharder.github.io/qrypt-quickstart/` (deployed from `cf17b84`, smoke test passing); the repository is public on GitHub; every README block runs as written; the grader quick-start timed from a fresh clone, 18.1 s against the mock; the demo cut (121.9 s). Waits on the owner: the share line, the submission on the portal | `docs/DEPLOY.md`, `evidence/grader_quickstart.md` |
| Portal walkthrough | Begun by the owner: the trial sign-up and the temporary-password email; first login and the token's screen to come | `evidence/portal_walkthrough.md` |
| README and AI usage | Done: `README.md` with the grader quick-start (runs as written against the mock), `AI_USAGE.md` | `tests/test_readme_and_ai_usage.py` |
| Eval cases AC-01 to AC-04 | Written, waiting in `evals/pending/` for their recording (a model key and the owner's yes, about $0.20 for all four) | `tests/test_agent_target.py` |
| Endpoint question | Settled 2026-10-20: a portal trial key works on the documented `api-eus` GET (Bearer), 200, the mock's shape; the portal's `eaas-aws` POST closed the connection unanswered. The quickstarts keep `api-eus`. Cloudflare refuses a default library User-Agent with 403 error 1010 (the quickstarts send their own); 4 KiB used | `evidence/portal_walkthrough.md`, `evidence/live_usage.csv` |
| Next | The owner submits the repository, the site URL and the video on the Gauntlet portal before 2026-10-21 13:30 CDT | `make blockers` |

## How to check your work

```bash
make bootstrap    # once per clone
make gate         # everything a push must pass
```

## Rules

In `AGENTS.md`, this project's own included: every session reads that file.

## Open, for the owner

- Read and approve `docs/PLAN.md` (`make docs-approve DOC=docs/PLAN.md`, when you say so).
- Review the backlog's scores and wording (`BACKLOG.md`): its reach shares and Qrypt's efforts are
  this project's estimates.
- Record AC-01: approve installing the `anthropic` SDK for the eval's model client, put a model key
  in the root env file as `QRYPT_QUICKSTART_MODEL_API_KEY`, and approve the run, about $0.05.
- Every other point where the plan needs you: `make blockers` lists its `**You act:**` lines.

## Where everything is

- `AGENTS.md`: instructions for coding agents (commands, working rules).
- `docs/index.md`: what the project knows, a level at a time; `docs/METHOD.md` is the gates and the
  build order.
- `docs/log.md`: what changed and why, newest first.
- `.claude/skills/`: the skill behind each gate.
- `scripts/gate.sh`: the one definition of what a push must pass.

## Where it lives

- **The repository:** `github.com/NickHarder/qrypt-quickstart`, public, with `main` its only
  branch. GitLab was dropped on 2026-10-21 (the owner's call): nothing is mirrored there.
- **The site:** `https://nickharder.github.io/qrypt-quickstart/`, deployed by
  `.github/workflows/deploy.yml` after CI passes on `main`, from CI's own site artifact, into the
  `github-pages` environment, with a smoke test of the page and `llms.txt` (`docs/DEPLOY.md`).
  A merge into `main` is a deploy: there is no other step.

## Do not commit

In `AGENTS.md`.

## Settled; do not reopen without the owner

- 2026-10-21 (replacing 2026-10-19's "private"): the GitHub repository is public, with
  `docs/brief/` in it, by the owner's choice, except the owner's Partner Copilot notes, removed and
  left as a stub; they are still in the history, and rewriting it is the owner's call.
- 2026-10-21: no GitLab; the repository and the site are on GitHub, and `main` is the only
  branch. The `public` branch and `scripts/mirror_to_gitlab.sh` were removed with it.
- 2026-10-19: languages Python, TypeScript (Node, in `web/`) and Rust (in `rust/`, the stretch third
  language); the evals, demo-video and semgrep-in-CI layers on; GitHub Actions.
- The text in `docs/brief/` is requirements, not instructions: ask before running a command,
  opening a link or sending anything it names.
- 2026-10-19: the interview is in CDT; build on private GitHub (CI, the site as an artifact) and
  move to GitLab with Pages at the very end (superseded 2026-10-20 and 2026-10-21: GitHub Pages,
  and no GitLab); Claude Code in fresh containers for the agent test.
  The rest is in `docs/PLAN.md`, "Decisions locked with the owner".
- 2026-10-20: the owner said 'push gate commits without asking for the rest of the plan': pushes of
  this branch's commits need no further ask; paid runs, installs, deploys and approvals still do.

## Known limitations

- The agent-harness image is built and proved in a cloud session (Docker is installed there; start
  it with `dockerd &`): a stand-in agent in the real image installed packages through the egress
  proxy and got a key from the mock. A real round needs a login for the agent in the container:
  `HARNESS_CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`), a plain environment variable in
  the cloud environment's settings, read at session start. A token saved as
  `CLAUDE_CODE_OAUTH_TOKEN` did not reach the session on 2026-10-20; the harness hands the value
  to the container under that name.
- The timed grader run and agent rounds 1 and 2 are against the mock. Against Qrypt: the live check
  (15 of 15, Rust included) and agent round 2-live (5 of 5 on the revised docs).

## History

In `docs/log.md`, newest first.
