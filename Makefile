# The commands a reviewer needs. `make help` prints this header.
#
#   make tools         on Linux: the tools the gate needs that uv cannot install, at CI's versions. On a Mac, brew.
#   make bootstrap     once per clone: what the gate needs, the index of docs/, the git hooks. No API key needed.
#   make gate          everything a push must pass (scripts/kit.conf lists the groups). $0, offline.
#   make gate-lint     one group of the gate; also gate-tests, gate-evals and gate-secrets.
#   make docs-index    write the index files of the knowledge bundle in docs/ from its concepts.
#   make docs-status   where each document in docs/ stands: its status, who has checked it, its approval.
#   make docs-find [TYPE=] [STATUS=] [TAG=] [TIER=]   the documents in docs/ that match, one line each.
#   make look-ahead    before a pull request: what else may have to change with this branch. Notes, never red.
#   make skill-costs [S=<skill>]   what each skill's runs cost before, in tokens; with S, one skill's estimate.
#   make blockers [PLAN=<file>]    what blocks the work now, and where the plan will need the owner. Never red.
#   make kit-files [JSON=1] [DIFF=1]   which files the kit gave this project unchanged, and which are its own.
#   make checks        the project's own checks, in any language (scripts/checks.conf), which the gate runs.
#   make check C=<name>   run one of them.
#   make docs-approve DOC=<file>   record the owner's approval of a document as it now is. The owner's call.
#   make docs-reopen DOC=<file>    put an approved document back to draft. The owner's call.
#   make trace         the north star, what supports it, the use cases, the eval cases, and the gaps.
#   make attest C=<computation> CLAIMED=<value> [P="name=value ..."] [RECEIPT=<file>]   check a number against its run.
#   make kit-update    pull the kit's improvements into this project (copier update).
#
#   make evals [TIER=all]                   the eval suite, replayed from recordings ($0), with a report in evals/out/.
#   make evals-baseline                     after a green run of every case, record what the suite did.
#   make prompt-manifest                    after a deliberate prompt version bump, pin the new text.
#   make demo-bootstrap                     once per clone: the demo's Node packages and Remotion's browser.
#   make demo-check                         storyboard against the catalog, typecheck, lint, unit tests ($0).
#   make demo-capture [TAKE=<name>]         record the takes in demo/takes/ with Playwright; writes beats.json.
#   make demo-stills                        one still per scene settled and one at its end, before any render ($0).
#   make demo-draft [VOICE=silent]          Kokoro's free local voice (or say, espeak, silent), timeline, half-size render, checks ($0).
#   make demo-voice                         say what the final voice-over would cost, and send nothing.
#   make demo-voice CONFIRM=1               make the final voice-over (DEMO_VOICE_PROVIDER in .env; Gemini, PAID, needs its key; kokoro, free).
#   make demo-voices [SEARCH=<word>]        list the final voice's voices to choose from (Gemini needs the key; not billed).
#   make demo [VOICE=say]                   the finished cut at full size from the final voice, its poster frame, then the checks ($0).
#   make demo-approve SCENE=<id>            record the owner's approval of a scene; a later change to it fails demo-check.
#   make demo-reopen SCENE=<id>             unlock an approved scene, when the owner asks for a change.
#   make demo-assets                        check the media files against demo/media.lock.json.
#   make demo-record FILE= PROVENANCE= NOTE=  list a generated or licensed media file in demo/media.lock.json.
#
# The gate is defined in one place, scripts/gate.sh; the pre-push hook runs the same script.

include scripts/kit.conf

GATE := scripts/gate.sh

.PHONY: help tools bootstrap gate docs-index docs-status docs-find look-ahead skill-costs blockers kit-files checks check docs-approve docs-reopen trace attest kit-update

# The header is the comment this file opens with, down to the first line that is not a comment.
help:
	@awk '/^#/ { sub(/^# ?/, ""); print; next } { exit }' Makefile

# gitleaks for the secret scan, and oasdiff in an API project, into ~/.local/bin (scripts/install_tools.sh).
tools:
	@scripts/install_tools.sh gitleaks$(if $(filter 1,$(API_PROJECT)), oasdiff)

bootstrap:
	@scripts/bootstrap.sh

gate:
	@$(GATE)

# One group: `make gate-lint` runs `scripts/gate.sh --only lint`.
gate-lint gate-tests gate-evals gate-secrets:
	@$(GATE) --only $(@:gate-%=%)

# After a concept is added, removed, retitled or described anew; the gate fails on a stale index.
docs-index:
	@scripts/okf_bundle.py index docs

docs-status:
	@scripts/okf_bundle.py status docs

# What this branch changed, and the documents, tests, handoff and log that may have to change with it.
look-ahead:
	@scripts/look_ahead.py

# From the transcripts on this machine and .claude/skill-costs.jsonl; with S, the median of that
# skill's history, or its floor and "no history".
skill-costs:
	@scripts/skill_costs.py report $(S)

# The gate, git, the gate ladder, the documents and deliverables that wait on the owner, the handoff's
# open items; and each `**You act:**` line of docs/PLAN.md, or of the plan PLAN names.
blockers:
	@scripts/blockers.py $(if $(PLAN),--plan $(PLAN),)

# The kit rendered again at the version .copier-answers.yml records, compared with what git tracks:
# an audit skips the kit's files the project never changed.
kit-files:
	@scripts/kit_files.py $(if $(JSON),--json,) $(if $(DIFF),--diff,)

# The checks in scripts/checks.kit.conf and scripts/checks.conf; with C, run the one of that name.
checks:
	@$(GATE) --list-checks

check:
	@$(GATE) --check "$(C)"

# Every filter given must match: a type in any case, a status, one tag, a trust tier.
docs-find:
	@scripts/okf_bundle.py find docs $(if $(TYPE),--type "$(TYPE)") $(if $(STATUS),--status "$(STATUS)") $(if $(TAG),--tag "$(TAG)") $(if $(TIER),--tier "$(TIER)")

# The owner's calls. An approval is of the concept as it is now, its body and its fields; a later
# change to either shows in the gate.
docs-approve:
	@test -n "$(DOC)" || { echo "docs-approve: name the document: make docs-approve DOC=docs/AUDIT.md" >&2; exit 64; }
	@scripts/okf_bundle.py approve docs "$(DOC)" --by "human:$(OWNER_ID)"

docs-reopen:
	@test -n "$(DOC)" || { echo "docs-reopen: name the document: make docs-reopen DOC=docs/AUDIT.md" >&2; exit 64; }
	@scripts/okf_bundle.py reopen docs "$(DOC)"

# The trace reaches down to the eval cases and their last verdicts (evals/out/).
trace:
	@scripts/okf_bundle.py trace docs --evals evals

# Ask a computation's attester whether the receipt of a run backs a number. RECEIPT is where the
# run left its receipt; `make evals` leaves one in evals/out/.
attest:
	@test -n "$(C)" || { echo 'attest: name the computation and the number: make attest C=docs/computations/<name>.md CLAIMED=<value> P="tier=core"' >&2; exit 64; }
	@test -n "$(CLAIMED)" || { echo 'attest: say which number: make attest C=$(C) CLAIMED=<value>' >&2; exit 64; }
	@scripts/okf_bundle.py attest docs "$(C)" --receipt "$(or $(RECEIPT),evals/out/receipt.json)" --claimed "$(CLAIMED)" $(foreach parameter,$(P),--parameter $(parameter))

# With a terminal, a question that the new version adds is asked. Without one (an agent, a script)
# copier cannot ask, so the question takes its default, and this says so.
kit-update:
	@command -v copier >/dev/null 2>&1 || { echo "kit-update: copier is not installed. Install it with:  uv tool install copier" >&2; exit 3; }
	@if [ -t 0 ]; then \
		copier update --skip-answered; \
	else \
		echo "kit-update: no terminal, so a question this version adds takes its default. To answer it yourself, run in a terminal:  copier update"; \
		copier update --skip-answered --defaults; \
	fi

.PHONY: e2e
# The tracer bullet end to end: the mock, the quickstart, its line count, the site (scripts/e2e.sh).
e2e:
	@scripts/e2e.sh

.PHONY: evals evals-baseline prompt-manifest
EVALS_BIN := $(SERVICE_DIR)/.venv/bin/$(EVALS_COMMAND)

evals:
	@$(EVALS_BIN) --mode replay --tier $(or $(TIER),core) --compare-baseline --out evals/out

evals-baseline:
	@$(EVALS_BIN) --mode replay --tier all --write-baseline

prompt-manifest:
	@$(EVALS_BIN) --write-prompt-manifest



.PHONY: demo demo-bootstrap demo-check demo-capture demo-stills demo-draft demo-voice demo-voices demo-approve demo-reopen demo-assets demo-record
demo-bootstrap:
	@cd demo && npm ci
	@cd demo && npx remotion browser ensure
	@cd demo && npx playwright install ffmpeg

demo-check:
	@cd demo && npm run --silent demo -- validate
	@cd demo && npm run --silent typecheck
	@cd demo && npm run --silent lint
	@cd demo && npm run --silent test

demo-capture:
	@cd demo && npm run --silent demo -- capture $(if $(TAKE),--take $(TAKE),)

# Stills before a render: every scene once its text has settled, and at its end. Needs no voice.
demo-stills:
	@cd demo && npm run --silent demo -- stills

demo-draft:
	@cd demo && npm run --silent demo -- draft $(if $(VOICE),--provider $(VOICE),)

# Without CONFIRM=1 (and only 1: CONFIRM=0 is not a yes) this prints the estimate and sends nothing.
demo-voice:
	@cd demo && npm run --silent demo -- voice $(if $(filter 1,$(CONFIRM)),--confirm,)

demo-voices:
	@cd demo && npm run --silent demo -- voices $(if $(SEARCH),--search $(SEARCH),)

demo:
	@cd demo && npm run --silent demo -- render $(if $(VOICE),--provider $(VOICE),)

demo-approve:
	@cd demo && npm run --silent demo -- approve --scene "$(SCENE)"

demo-reopen:
	@cd demo && npm run --silent demo -- reopen --scene "$(SCENE)"

demo-assets:
	@cd demo && npm run --silent demo -- assets

demo-record:
	@cd demo && npm run --silent demo -- record --file "$(FILE)" --provenance "$(PROVENANCE)" --note "$(NOTE)"


.PHONY: lighthouse
# Lighthouse's mobile preset, 10 runs on the built site: evidence/lighthouse/ (RQ-20, RQ-21).
lighthouse:
	@$(SERVICE_DIR)/.venv/bin/python -m qrypt_quickstart.lighthouse_benchmark

.PHONY: grader-run
# Phase 11: the README's grader quick-start from a fresh clone, each command as written, timed, against
# the mock: evidence/grader_quickstart.md (RQ-35). It downloads the two pip packages; it calls no Qrypt.
grader-run:
	@$(SERVICE_DIR)/.venv/bin/python -m qrypt_quickstart.grader_run

.PHONY: live-check
# Phase 7, live: each snippet 5 times against Qrypt, and four probes; 12 KiB, ledger-guarded.
# Only with the owner's approval: it spends the owner's entropy (src/qrypt_quickstart/live_check.py).
live-check:
	@$(SERVICE_DIR)/.venv/bin/python -m qrypt_quickstart.live_check

.PHONY: agent-round
# Phase 8: one round of the agent-readiness test, ROUND=1 or 2, in a fresh container per run
# (build the image first: docker build -t qrypt-agent-harness agent-harness/). TARGET=mock (the
# default) or TARGET=live, which reaches Qrypt through the recording relay: 64 KiB a run at most,
# stopping at the ledger's 8,192 KiB. It runs Claude Code with the owner's login, and a live round
# spends the owner's entropy: only with the owner's approval. In a cloud session, whose only way out
# is an egress proxy: HARNESS_OPTIONS='--network host --extra-ca <the proxy's authority>'.
agent-round:
	@$(SERVICE_DIR)/.venv/bin/python -m qrypt_quickstart.agent_harness --round $(ROUND) --target $(or $(TARGET),mock) $(HARNESS_OPTIONS)
