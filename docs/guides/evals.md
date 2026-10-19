---
type: Guide
title: The eval suite
description: How to run the eval suite, what each file in evals/ is, and how a case is added, recorded and changed.
tags: [evals]
status: stable
generated: { by: ai-kit/v0.21.1 }
---

# Evals

The eval suite is the gate for anything a model produces. It runs on every push and every merge
request, costs $0, and needs no network: model calls are recorded once and replayed.

```bash
make gate-evals            # what the gate runs: the core tier, replayed, compared with the baseline
make evals                 # the same, with results.json, summary.md and junit.xml in evals/out/
make evals TIER=all        # every case, not only the core tier
```

## What is in `evals/`

| Path | What it is |
|---|---|
| `cases/<category>/<id>.yaml` | One case each. The `write-evals` skill has the schema and the rules. |
| `cassettes/<id>.json` | The recorded model exchanges for a case. |
| `thresholds.yaml` | What the gate requires, and the model id the recordings were made with. |
| `baseline.json` | What each case did on the last green run. |
| `prompt_manifest.json` | Each prompt's version and content hash. |

The code is in the Python package: `evals/` (runner, loader, scorers, recordings, reporters) and
`prompts/` (the versioned prompts). `evals/target.py` is the seam: the one file that calls the system
under test.

## What a case traces to

A case names what it protects and what it measures, by id:

```yaml
guards: [UC-02]         # the use cases in docs/USERS.md, or the findings in docs/AUDIT.md
metrics: [NS-01, DR-02] # the key metrics in docs/metrics/ that this case's verdict feeds
```

`make trace` prints the chain: the north star, the drivers and guardrails that support it, the use
cases, the cases under each, and their last verdicts. An id that is defined nowhere fails the gate.
What the trace does not reach yet (a use case with no case, a metric with no measurement) is a gap:
a note, until the floor for it is switched on under `trace:` in `thresholds.yaml`. The summary of a
run opens with the pass rate by metric, the north star first.

## A pass rate that can be checked

`make evals` leaves `evals/out/receipt.json` beside its results: the arguments the run was started
with, the results file, and its hash. `docs/computations/eval-pass-rate.md` is the sanctioned way to
get the pass rate, and `make attest` asks its attester whether a number is the one that run measured:

```bash
make evals
make attest C=docs/computations/eval-pass-rate.md CLAIMED=1.0 P="tier=core"
make attest C=docs/computations/eval-pass-rate.md CLAIMED=1.0 P="tier=core metric=NS-01"
```

A number that is not the measured one is refused, and so is a run of another tier, a results file
edited after the run, and a run on a prompt text that is not the pinned one;
`docs/computations/eval-pass-rate.md` lists every check. Write a pass rate into a document only
after it has been attested.

## Tiers

`tier: core` cases all must pass on every commit; a core case must be checkable from a recording.
`tier: scenario` cases (the default) run with `TIER=all`.

## What makes a run red

- A threshold in `thresholds.yaml` fails (exit 1).
- A case that passes in `baseline.json` fails now (exit 1). A change of wording alone is never a
  regression; only the verdict is compared.
- The suite cannot run: no cases, a bad case file, a missing recording (exit 2). An empty suite is an
  error, not a pass.

A red run prints the versions that were under test: the kit, the commit, the model, every prompt and
every skill. Every result file starts with the same block, and each case records the version and
content hash of the prompts it used.

## Prompts are versioned

A prompt is a Markdown file with a `name` and a `metadata.version`. Changing a prompt's text without
raising its version fails `tests/test_prompts_versioned.py`. After a deliberate change:

1. Raise `metadata.version` in the prompt file.
2. `make prompt-manifest`
3. Record the affected cases again (below): a recording is tied to the exact prompt text it was made
   with, so the old ones no longer answer.
4. `make evals-baseline` once the run is green, and commit all of it in one change.

## Recording costs money

Replay is free. `--mode record` and `--mode live` call the real model. Before either: say the dollar
estimate and get the owner's yes.

The kit ships no provider SDK. Wire the project's provider into `build_live_client` in
`evals/target.py`; until then, record and live exit 2 and say so. The provider's key goes on the
`QRYPT_QUICKSTART_MODEL_API_KEY` line of the `.env` at the repository root (`.env.example`
shows it), and the client
reads it from `Settings().model_api_key`. The two example cases and their
recordings were written by hand so that the gate has something real to replay from the first commit.
Replace them with the project's own.

## Adding a case

1. Write the case file first, with the `failure_mode` it guards against.
2. Record it (`--mode record`), or for the first slice write the recording by hand.
3. Run it and watch it fail for the right reason, then make it pass.
4. `make evals-baseline`, and commit the case, its recording and the baseline together.

Every reported bug becomes a `type: regression` case: write it, confirm it is red, fix the bug, confirm
it is green.

## Changing an expectation

Never change an expected output just to make a case pass. A core expectation changes only with a
`history` entry in the same change, so the reviewer sees the reason next to the diff.
