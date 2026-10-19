---
name: audit-codebase
description: Audits the system the project builds on (security, performance, architecture, data quality, compliance) with one sub-agent per area, then writes docs/AUDIT.md with reproducible findings and what each one changes in the plan. Use when producing or updating the audit hard gate, before any product code exists.
context: fork
agent: gate
background: false
metadata:
  version: "2.2.1"
---

# Audit the codebase (hard gate)

Produce `docs/AUDIT.md` before any product code exists. The audit covers what the project builds on:
an existing codebase, or, for a new project, the APIs, datasets, model providers and deploy target it
will depend on.

`docs/AUDIT.md` is a concept of the knowledge bundle and carries `type: Audit`. Each area's file,
`docs/audit/<area>.md`, is one too, with `type: Audit Area`, and the audit links to it.
The `write-okf-concept` skill has the rules for the frontmatter, the index and the log.

## On its own

An agent may start this skill without asking when `docs/METHOD.md` names it as the next gate and
`docs/PLAN.md` is committed, its inputs exist (where it would have to invent, it asks, as this
skill says), `make skill-costs S=audit-codebase` gives no estimate over the project's cap
(`SKILL_RUN_CAP_TOKENS` in `scripts/kit.conf`; a first run has none and goes; the hook before a
skill run checks it), and the
result is a draft under `docs/AUDIT.md` that the owner's approval still governs. Otherwise it asks
first, with the number. A second run, once its artifact exists, is the owner's to start: the hook
asks. A skill the owner calls by name runs as before.

It runs in a sub-agent of its own (`context: fork`, the `gate` agent), which reads the committed
documents and the brief, spawns one sub-agent per area, writes the draft and returns a summary.
Nothing of the conversation reaches it: what the audit needs must be in the repository.

## Scope: the project, not the kit's scaffold

A project made from the kit starts with a hundred or so files the kit wrote: scripts, skills, CI,
the Makefile, the scaffold. The kit's own tests and CI prove them at the version that rendered
them, and a flaw in one is the kit's to fix, once. Reading them in every area spends tokens and
finds nothing the plan can act on. So, before anything else:

1. Run `make kit-files JSON=1`. It renders the kit again at the version `.copier-answers.yml`
   records and sorts every tracked file: `unchanged` (a kit file as the kit wrote it), `changed`
   (a kit file the project edited), `removed`, and `own` (a file the kit did not write).
2. Give each area sub-agent the `own` files to read whole and the `changed` files to read as their
   diff (`make kit-files DIFF=1`). Never give it the `unchanged` files, and tell it not to open them.
   A lock file (`uv.lock`, `package-lock.json`, `Cargo.lock`, `go.sum` and the like) is checked
   with its language's audit tool (`pip-audit`, `npm audit`, `cargo audit`, `govulncheck`), never
   read whole: it is machine-written, long, and the tool reads it better.
3. In `docs/AUDIT.md`, one scope line says what was left out: the kit version, how many files were
   unchanged and skipped, and the commit of the project audited (`git rev-parse --short HEAD`).
4. When `make kit-files` exits 4 (the kit could not be rendered: its source cannot be reached), or
   3 (copier is not installed), audit every file and say so, with the reason, in the scope line.
   A run that cannot sort the files costs more tokens; it never covers less.
5. In the kit itself (`copier.yml` at the root, and `make kit-files` exits 2 saying so), there is no
   product to audit: stop and say so.

A new project whose only files are the kit's has no codebase of its own yet: the audit is then of
the APIs, datasets, model providers and deploy target, as above, without reading the scaffold.

## Evidence rule

A finding without a reproduction is not a finding. Each finding uses this template:

```markdown
### [AREA-NN] <short title>
- **Severity:** critical | high | medium | low | info
- **Location:** `path:line`, or the query or request
- **Reproduction:** the exact command or query that demonstrates it
- **Impact on the project:** what the product would get wrong, leak, or fail to do in time
- **Mitigation:** what a later phase must do, or an explicit deferral
```

A finding is a candidate until you have run its reproduction and read the real output.

## Parallel execution

Launch one sub-agent per area, each given the files in scope. Each writes `docs/audit/<area>.md`
using only evidence it verified against the running system and the files in scope. The default areas, and what each must answer:

- **Security** (`SEC`): authentication and authorization, data exposure, secrets in the repository,
  handling of sensitive data.
- **Performance** (`PERF`): where the system is slow, the shape and volume of the data, what bounds
  the product's latency.
- **Architecture** (`ARCH`): how the code is organized, where data lives, the integration points the
  product can use, and the ones that turn out not to exist.
- **Data quality** (`DQ`): null rates, orphans, duplicates, implausible values, date sanity. Start from
  a committed, re-runnable profile script (`docs/audit/data_profile.sql` or the equivalent).
- **Compliance** (`CMP`): audit logging, retention, and what it means to send this data to a model
  provider.

Drop an area that does not apply and say why in `docs/AUDIT.md`. Before launching, write each area's
required probes from the brief and from a first read of the code, phrased as things to confirm, not to
assume.

## Synthesis: `docs/AUDIT.md`

1. **Summary, about 500 words** (450 to 550; count them). The findings that matter most to the
   product. Not a dump.
2. **How this changes the plan.** A table: finding → the decision it forces. If a finding changes
   nothing, say so.
3. **One section per area**, as a table `| Id | Severity | Finding | Response |`, with a link to the
   full findings in `docs/audit/<area>.md`.
4. **Test-data defense**, when the project uses synthetic or seeded data: why it is safe, how it is
   reproduced (seed, script), which of its flaws become product failure modes, and what it cannot show.

## Acceptance

- [ ] `docs/AUDIT.md` is committed, carries `type: Audit`, and links each area's file
- [ ] Its scope line names the kit version, the unchanged kit files skipped and the commit audited,
      or says why every file was read
- [ ] `make docs-index` was run, and `docs/log.md` has the audit's entry
- [ ] The summary is 450 to 550 words
- [ ] Every finding has a location and a reproduction that was run
- [ ] The profile script is committed and was executed
- [ ] No product code exists yet
