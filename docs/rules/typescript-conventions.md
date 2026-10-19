---
type: Rule
title: TypeScript conventions
description: How names, single assignment, types, documentation, errors and suppressions are written and checked in this project's TypeScript.
tags: [typescript, conventions]
status: stable
generated: { by: ai-kit/v0.21.1 }
---
# TypeScript conventions

In `web`, `make gate` checks most of this (`tsc` in strict mode, Biome, vitest: the
checks `ts-types`, `ts-lint` and `ts-unit`).
In `demo/`, `make demo-check` checks most of this (`tsc` in strict mode, Biome, vitest).
The rest is how code is written here, wherever the TypeScript is.

## Names say what the thing is

- Use long and descriptive names: `sceneDurationInFrames`, not `dur` or `n`.
- Include the unit in the name where there is one: `holdSeconds`, `playedFrames`.
- Do not use an abbreviation a newcomer would have to look up. The exceptions are a one-letter index
  in a two-line loop and a standard symbol in a formula.
- A function is named for what it does (`buildTimeline`), a boolean reads as a question (`isSilent`),
  a collection is plural. A component is PascalCase and its file has the same name.

## Assign once

- Declare with `const`. Create a new name for each intermediate value instead of overwriting one, so
  every stage shows up, by name, in a debugger and in a stack trace.
- Never reassign a parameter, and never reuse a name. The exception is a counter or an accumulator
  that a loop updates, declared with `let` and named for what it accumulates.
- Biome enforces `useConst` and `noParameterAssign`.

## Types

- `strict` and `noUncheckedIndexedAccess` are on. No `any`, and no `!` to silence a possible
  `undefined`: narrow with a check instead.
- Data that crosses a boundary (a file, an API, the render's props) is parsed with a Zod
  `strictObject`, and its type is inferred from that schema. Never hand-write a type a schema
  already describes.
- A `switch` over a union ends with a `never` check, so a new member does not compile until it is
  handled.

## Documentation

- A doc comment (`/** ... */`) at the top of every file, saying what it is for, and on every exported
  function, type and constant.
- A comment says why, not what. No commented-out code.
- When behavior changes, its doc comment and the document that describes it change in the same commit.

## Errors

- Throw a named subclass of `Error` whose message says what to do next. Never swallow an error.
  The exception is a loop that must survive one bad item: catch the error there, log which item
  failed, count it, and go on. Biome enforces `noEmptyBlockStatements` and `useThrowOnlyError`.

## Suppressions

- Fix a finding rather than silence it. A suppression names its rule and gives its reason:
  `// biome-ignore lint/<group>/<rule>: <why>`. `@ts-ignore` is an error (Biome `noTsIgnore`).
