---
type: Executor
title: Run the eval suite from its recordings
description: How to run the eval suite so that a pass rate taken from it can be attested, and the receipt the run hands back.
tags: [evals, attested]
status: stable
generated: { by: ai-kit/v0.21.1 }
---

# When to use this

An attested computation whose computation is a run of the eval suite names this concept as its
`executor`, as [the eval pass rate](/computations/eval-pass-rate.md) does.

# Steps

1. From the repository root, run `make evals`, or `make evals TIER=all` for every case. Both replay
   recordings: no model is called and nothing is spent.
2. The run writes `evals/out/results.json` and, beside it, `evals/out/receipt.json`.
3. Change neither file. A number is attested against the receipt as the run wrote it:
   `make attest C=<the computation> CLAIMED=<the number> P="tier=core"`.

# The receipt

| Field | What it holds |
|---|---|
| `arguments` | The arguments the runner was started with, in order. |
| `results_file` | The results the run wrote. |
| `results_sha256` | The hash of that file as it was written. |

`evals/out/` is not committed. A receipt is the evidence of one run and not knowledge, so it is not
part of this bundle. A run that calls a model (`--mode record` or `--mode live`) is not this
computation: it costs money, needs the owner's yes, and attests nothing here.
