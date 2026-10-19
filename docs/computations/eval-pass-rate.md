---
type: Attested Computation
title: The eval pass rate
description: The share of eval cases that pass when the suite is replayed from its recordings, for one tier and, when asked, for the cases that feed one metric.
tags: [evals, attested]
status: stable
generated: { by: ai-kit/v0.21.1 }
runtime: shell
parameters:
  - { name: tier, type: string, required: true }
  - { name: metric, type: string, required: false }
executor:
  resource: /references/executors/run-evals.md
  receipt: [arguments, results_file, results_sha256]
attester:
  resource: /references/attesters/eval_results.py
---

# Computation

    qrypt-quickstart-evals --mode replay --tier {tier} --compare-baseline --out evals/out

`make evals TIER=<tier>` runs exactly this. It replays recordings, so it costs nothing and calls no
model. `tier` is `core` or `all`. `metric`, when given, is the id of a key metric, and the rate is
then taken over the cases that feed it.

# What the attester checks

[The attester](/references/attesters/eval_results.py) reads the receipt that
[the run](/references/executors/run-evals.md) wrote, and refuses the number unless:

1. the arguments the runner was given are the computation above with `tier` filled in, and nothing
   more;
2. `results.json` is, byte for byte, the file the receipt was written for;
3. the run was a replay, and every prompt it used has the text pinned in
   `evals/prompt_manifest.json`;
4. when a `metric` is given, at least one case of the run feeds it;
5. the claimed rate is the share of passing cases, counted again from `results.json`.

`make attest` refuses more before it asks the attester, such as a parameter the contract does not
declare. The `write-okf-concept` skill lists all of it (`references/attested-computation.md`).

# How to use it

    make evals
    make attest C=docs/computations/eval-pass-rate.md CLAIMED=1.0 P="tier=core"

A key metric that this rate measures links here from its own concept, and states a value only after
`make attest` has accepted exactly that value.
