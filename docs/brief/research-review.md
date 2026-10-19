---
type: Review
title: What to check in the research before building on it
description: Where the research blueprint and the screenshots disagree with the brief, which of their claims are unverified, and what is wrong in their sample code, for kickoff to settle.
tags: [brief, research, review]
status: draft
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-19T23:45:00Z }
sources:
  - id: assessment
    resource: assessment-text.md
    title: The assessment's full text
  - id: blueprint
    resource: research-blueprint.md
    title: The research blueprint
  - id: screenshots
    resource: screenshots.md
    title: The five design screenshots
---

# Why this exists

[The blueprint](research-blueprint.md) and [the screenshots](screenshots.md) were drafted by an AI
research tool. The brief scores "Accuracy & safety of content" and asks how many AI-drafted claims
had to be corrected, so this list is the start of that count. It was written in the setup session
on 2026-10-19 from reading alone: nothing here was run, and no Qrypt page was opened.[^assessment]

# Where they disagree with the brief (the brief wins)

| # | What the research says | What the brief says | Where |
|---|---|---|---|
| D1 | Missing `Accept` gives a 401 (screenshot 1) or a 400/406 (screenshot 3, and the blueprint's mock) | The error table names no status for a missing `Accept`; 401 is a bad or expired token | Screenshots 1 and 3; blueprint block 3 |
| D2 | The key is read from `process.env.QRYPT_TOKEN` (screenshot 3) | The token is `QRYPT_API_KEY`, in `.env` | Screenshot 3 |
| D3 | `byte_count: 64` and `"64kb"` (screenshot 3) | `size` is an integer count of KiB, 1 to 512; the snippet asks for 1 | Screenshot 3 |
| D4 | Backlog item 2 of screenshot 5 ships "SDK snippets" in PowerShell and cURL | The quickstart is two of Python, Node, Go, Rust or C++; "no full SDK" is the suggested tradeoff | Screenshot 5 |
| D5 | Stage 3's event is `api_entropy_200_first` joined on `account_id + token_hash` (screenshot 4) against `api_entropy_request_completed` joined on `token_id_hash` (blueprint) | One spec an engineer can build from without a question | Screenshot 4; blueprint block 7 |
| D6 | Effort in months (screenshot 5) against person-weeks (blueprint) | RICE "or equivalent", with evidence | Screenshot 5; blueprint block 7 |
| D7 | Round 2 will "typically" be 5/5 with a median under 2 minutes | ≥ 4/5, measured and logged in both rounds | Blueprint block 6 |
| D8 | The backlog's evidence column cites Round 2 results before any run | Ten items drawn from the agent-readiness findings | Blueprint block 7, item 2 |

D7 and D8 are predictions written as results. A number goes into a deliverable only after the run
that produces it.

# Claims to check against a source before they reach the site or the PRD

- The `Accept` header is missing from the docs' curl, Python and PowerShell examples. The
  [partner notes](partner-notes.md) say so too; open docs.qrypt.com/eaas/ and record what it shows.
- `docs.qrypt.com/llms.txt` returns 404 (October 2026).
- `size` defaults to 1; the brief gives the range 1 to 512, not the default.
- The randomness is tested continuously against NIST SP 800-22, under ESV certificate E246.
- The portal "frequently fails to load or blocks self-service signups": the partner notes report
  one failed load, which is one observation.
- Lighthouse added an "Agentic Browsing" `llms.txt` audit in May 2026.
- qseed injects 48 bytes through `C_SeedRandom`; rng-tools feeds `/dev/random`.
- The 45-minute baseline and the 25% activation are the brief's own assumptions: call them that.
- "Captures over 90% of the TTFK reduction" and "6 to 8 engineering weeks" for SDKs have no source.
- The figures on industry benchmarks (Stripe, Twilio, Vercel, ReadMe) have no source.

# Problems in the sample code (read, not run)

| # | Problem | Snippet |
|---|---|---|
| C1 | Not every network failure is caught. A timeout or a refused connection (`URLError`) gives a stack trace, which the brief rules out | Python |
| C2 | A `fetch` that fails on the network throws before `res.ok` is read: a stack trace again | Node |
| C3 | Every `unwrap()` on the body panics with a backtrace hint; a 200 with an unexpected body is not handled | Rust |
| C4 | The `.env` reader keeps `#` comment lines and does not strip `export ` | Rust |
| C5 | The `.env` reader would fail on a line with a leading space before `#`, and strips quotes and spaces from inside the token's ends | Python, Node |
| C6 | The Rust crate needs `ureq` 2.x (`.set`, `into_json`, `Error::Status`); ureq 3 changed all three, so the version must be pinned | Rust |
| C7 | `set_var` is `unsafe` from the Rust 2024 edition; the kit's Rust layer forbids `unsafe` | Rust |
| C8 | `assert` is skipped under `python -O`; the check should not rest on it | Python |
| C9 | Their line counts (21, 23, 22) were not measured; a count against "≤ 25 excluding comments and imports" is a check the CI should run | All |
| C10 | The kit's own conventions (long names, assign once, types) differ from the snippets' style. A snippet the user copies is held to the brief's 25 lines, so kickoff decides whether `snippets/` is exempt from the kit's rules, and records why | All |

# The layout question for kickoff

The blueprint puts `PRD.md`, `AGENT_READINESS.md`, `BACKLOG.md` and the claims table at the
repository's root. The kit keeps knowledge in `docs/` and allows a Markdown file outside it only
when a tool reads it there (`docs/references/outside-the-bundle.md`). The brief names the files but
not their place, so kickoff chooses: concepts under `docs/` with the brief's names, or root files
added to the outside list, with the reason.

[^assessment]: The assessment's full text
