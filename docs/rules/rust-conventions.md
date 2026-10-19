---
type: Rule
title: Rust conventions
description: How names, single assignment, types, documentation, errors and suppressions are written and checked in this project's Rust, and the few idioms of Rust that the general rules let stand.
tags: [rust, conventions]
status: stable
generated: { by: ai-kit/v0.21.1 }
---
# Rust conventions

In `rust`, `make gate` checks most of this with three checks, on the toolchain
`rust-toolchain.toml` pins: `rust-format` (rustfmt), `rust-lints` (clippy, with the lints of
`Cargo.toml`'s `[lints]` table, warnings as errors) and `rust-unit` (`cargo test`). CI also runs
`cargo audit`. The rest is how code is written here.

## Names say what the thing is

- Use long and descriptive names: `unpaid_invoice_count`, not `n` or `cnt`. Types are `UpperCamelCase`
  and everything else `snake_case`, as the compiler asks.
- Include the unit in the name where there is one: `retry_delay_seconds`, or a `Duration` named for
  what it is (`retry_delay`).
- Do not use an abbreviation a newcomer would have to look up.
- Rust's own idioms stand, and are the only exceptions:
  - `self`;
  - `f` for the `Formatter` of a `Display` or `Debug` impl;
  - `e` or `err` for a matched error;
  - a one-letter index in a loop of at most two lines.

## Assign once

- Declare each intermediate value with its own name (`raw_rows`, then `valid_rows`), so every stage
  shows up, by name, in a debugger and in a stack trace.
- Rust lets a name be bound again (`let name = name.trim();`). Here it is not: clippy's
  `shadow_unrelated`, `shadow_reuse` and `shadow_same` are `deny` in `Cargo.toml`.
- Use `mut` only for a counter or an accumulator that a loop updates, named for what it holds.

## Type everything

- Name a type for each idea the code passes around (`struct CustomerId(String)`), rather than passing
  a bare `String` or `u64` through many functions.
- `unsafe` is forbidden (`unsafe_code = "forbid"`).

## Document as you go

- Every public item has a doc comment (`///`), and the crate has one (`//!`): `missing_docs` is
  `deny`. clippy's pedantic group asks for `# Errors` and `# Panics` sections where they apply.
- A comment says why, not what. The documentation changes in the same commit as the behavior.

## Errors

- Return `Result` for an error a caller could handle, with an error type that says what was being
  done. Add context where the error passes through.
- No `unwrap` or `expect` outside tests, unless a comment on the line says why it cannot fail.

## Tests

- A unit test lives in a `#[cfg(test)] mod tests` beside the code; a test of the public interface
  lives in `tests/`. Name a test for what it shows
  (`greets_a_person_by_name_without_the_spaces_around_it`).
- A test is written and seen to fail before the code that makes it pass.

## Suppressions

- To allow a lint for one item, write `#[expect(clippy::<lint>, reason = "<why>")]` on it. `expect`
  fails when the lint no longer fires, so a stale suppression does not linger; the reason is
  required.
- To change a lint for the whole crate, change `Cargo.toml`'s `[lints]` table and say why here.
