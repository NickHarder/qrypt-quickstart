# Honest film

A demo is evidence. A viewer takes what is on screen to be the product, and what is said to be true.
The pipeline enforces the first four rules; the rest are yours.

## Enforced by the checks

- **Product footage is recorded, never generated.** A `ScreenRecording` scene shows a take that
  `media.lock.json` lists as `recorded`. Nothing else may stand in for the product.
- **Anything generated is tagged.** An `Illustration` always shows a tag that says so, and its file
  must be listed as `generated` or `licensed`, with a note saying how it was made.
- **Every number has a source and a scope.** `MetricCards` shows both: where the number comes from,
  and whether it was measured on one user, under load, in an eval run or in production.
- **Code and output are read, not typed.** `CodeHighlight` and `Terminal` take their text from files
  in the repository when the cut is built.

## Grounded, or free

The line is between what the film asserts and how it says it. A name, a number, a capability, a
claim about the product, a quotation: grounded, in the repository, its documents, its measurements
or its screen, and shown as the source has it. A framing, a connective line, the order of the
scenes, a title that says what a scene is about: free, within the owner's wording. When a line you
want is not grounded, quote what the project does say; it is almost always better than the
invented version. Nothing secret leaves the plan: a key, a private name, an internal address or
an unreleased number stays out of every line and off every frame.

## Yours to keep

- **Quote a number only from its latest measurement on the version filmed.** If the number moved, the
  line, the card and any key phrase move with it.
- **Say what a number was measured on.** "Four seconds" for one user is not "four seconds" under load.
- **Never cut around a failure.** Do not splice a success from one take over a failure in another. If
  the product failed on camera, fix it and record again.
- **Do not fake a wait.** Footage may be sped up, at most four times. Anything on screen that measures
  time (a countdown, a timer, a clock) stays true to the clock.
- **Use only data that may be shown.** Synthetic or seeded data, never a real person's.
- **Say "checked" when it was checked and "verified" only when it was verified.** Do not round a claim
  up.
- **Keep secrets off screen.** Passwords, keys and tokens are not typed where the recording can see
  them.
