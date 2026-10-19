import { spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  AdvisoryError,
  advisoriesOf,
  EXIT_COULD_NOT_RUN,
  EXIT_FAILED,
  fixesOf,
  KNOWN_ADVISORIES_FILE,
  knownAdvisoriesOf,
  verdictOf,
} from "../src/pipeline/advisories";

/** A report in the shape `npm audit --json` gives (report version 2), with one advisory. */
const reportWith = (fixAvailable: unknown): unknown => ({
  auditReportVersion: 2,
  vulnerabilities: {
    "sprintf-js": {
      name: "sprintf-js",
      severity: "moderate",
      isDirect: false,
      via: [
        {
          source: 1241202,
          name: "sprintf-js",
          dependency: "sprintf-js",
          title: "sprintf-js vulnerable to denial of service",
          url: "https://github.com/advisories/GHSA-hp3w-g68c-fv3c",
          severity: "moderate",
          range: "<=1.1.3",
        },
      ],
      fixAvailable,
    },
    roarr: { name: "roarr", severity: "moderate", via: ["sprintf-js"], fixAvailable },
  },
  metadata: { vulnerabilities: { moderate: 2, total: 2 } },
});

const CLEAN_REPORT = { auditReportVersion: 2, vulnerabilities: {}, metadata: {} };

const knownList = (entries: unknown[]): string => JSON.stringify({ advisories: entries });

const KNOWN_SPRINTF = {
  id: "GHSA-hp3w-g68c-fv3c",
  package: "sprintf-js",
  known_since: "2026-10-11",
  why: "No version fixes it, and it only formats an installer's log lines.",
};

describe("advisoriesOf", () => {
  it("reads each advisory once, by its GitHub id, from the package it is in", () => {
    expect(advisoriesOf(reportWith(false))).toEqual([
      {
        id: "GHSA-hp3w-g68c-fv3c",
        package: "sprintf-js",
        severity: "moderate",
        title: "sprintf-js vulnerable to denial of service",
        url: "https://github.com/advisories/GHSA-hp3w-g68c-fv3c",
      },
    ]);
    expect(advisoriesOf(CLEAN_REPORT)).toEqual([]);
  });

  it("refuses what is not a report, such as npm's answer when the registry cannot be reached", () => {
    const offline = { error: { code: "ENOTFOUND", summary: "request to the registry failed" } };
    expect(() => advisoriesOf(offline)).toThrow(AdvisoryError);
    expect(() => advisoriesOf(offline)).toThrow(/request to the registry failed/);
    expect(() => advisoriesOf("not json")).toThrow(AdvisoryError);
  });
});

describe("knownAdvisoriesOf", () => {
  it("reads the committed list", () => {
    const text = readFileSync(KNOWN_ADVISORIES_FILE, "utf8");
    expect(() => knownAdvisoriesOf(text)).not.toThrow();
  });

  it("refuses an entry with no date, a date that is not one, or no reason", () => {
    expect(() => knownAdvisoriesOf(knownList([{ ...KNOWN_SPRINTF, known_since: "" }]))).toThrow(
      /known_since/,
    );
    expect(() =>
      knownAdvisoriesOf(knownList([{ ...KNOWN_SPRINTF, known_since: "2026-13-40" }])),
    ).toThrow(/known_since/);
    expect(() => knownAdvisoriesOf(knownList([{ ...KNOWN_SPRINTF, why: " " }]))).toThrow(/why/);
    expect(() => knownAdvisoriesOf(knownList([KNOWN_SPRINTF, KNOWN_SPRINTF]))).toThrow(/twice/);
  });
});

describe("verdictOf", () => {
  it("fails on an advisory the list does not hold, naming it and what to do", () => {
    const verdict = verdictOf(advisoriesOf(reportWith(false)), fixesOf(reportWith(false)), []);
    expect(verdict.failures).toHaveLength(1);
    expect(verdict.failures[0]).toContain("GHSA-hp3w-g68c-fv3c");
    expect(verdict.failures[0]).toContain("known-advisories.json");
  });

  it("passes an advisory the list holds, and says so with its date", () => {
    const known = knownAdvisoriesOf(knownList([KNOWN_SPRINTF]));
    const verdict = verdictOf(advisoriesOf(reportWith(false)), fixesOf(reportWith(false)), known);
    expect(verdict.failures).toEqual([]);
    expect(verdict.notes.join("\n")).toContain("known since 2026-10-11");
  });

  it("fails when a fix is available that is not a breaking change, even for a known advisory", () => {
    const known = knownAdvisoriesOf(knownList([KNOWN_SPRINTF]));
    const report = reportWith({ name: "roarr", version: "2.15.5", isSemVerMajor: false });
    const verdict = verdictOf(advisoriesOf(report), fixesOf(report), known);
    expect(verdict.failures.join("\n")).toContain("roarr 2.15.5");
    expect(
      verdictOf(advisoriesOf(reportWith(true)), fixesOf(reportWith(true)), known).failures,
    ).not.toEqual([]);
  });

  it("only notes a fix that is a breaking change, such as a downgrade npm proposes", () => {
    const known = knownAdvisoriesOf(knownList([KNOWN_SPRINTF]));
    const report = reportWith({ name: "kokoro-js", version: "1.2.0", isSemVerMajor: true });
    const verdict = verdictOf(advisoriesOf(report), fixesOf(report), known);
    expect(verdict.failures).toEqual([]);
    expect(verdict.notes.join("\n")).toContain("kokoro-js 1.2.0, a breaking change");
  });

  it("notes an entry that is no longer reported, so the list can shrink", () => {
    const known = knownAdvisoriesOf(knownList([KNOWN_SPRINTF]));
    const verdict = verdictOf([], [], known);
    expect(verdict.failures).toEqual([]);
    expect(verdict.notes.join("\n")).toContain("no longer reported");
  });
});

describe("the command", () => {
  const TSX = path.resolve("node_modules/.bin/tsx");
  const SCRIPT = path.resolve("src/pipeline/advisories.ts");

  /** Run the command with a stand-in `npm` that prints what it is given and exits as told. */
  const runWith = (printed: string, npmExit: number): { status: number | null; output: string } => {
    const folder = mkdtempSync(path.join(tmpdir(), "advisories-"));
    writeFileSync(path.join(folder, "report.json"), printed);
    writeFileSync(
      path.join(folder, "npm"),
      `#!/bin/sh\ncat "${path.join(folder, "report.json")}"\nexit ${npmExit}\n`,
    );
    chmodSync(path.join(folder, "npm"), 0o755);
    const done = spawnSync(TSX, [SCRIPT], {
      encoding: "utf8",
      env: { ...process.env, PATH: `${folder}${path.delimiter}${process.env.PATH ?? ""}` },
    });
    return { status: done.status, output: `${done.stdout}${done.stderr}` };
  };

  it("exits 0 on a clean report", () => {
    const done = runWith(JSON.stringify(CLEAN_REPORT), 0);
    expect(done.output).toContain("advisories: none reported");
    expect(done.status).toBe(0);
  });

  it("exits 1 on an advisory the list does not hold, whatever npm's own exit", () => {
    const done = runWith(JSON.stringify(reportWith(false)), 1);
    expect(done.output).toContain("GHSA-hp3w-g68c-fv3c");
    expect(done.status).toBe(EXIT_FAILED);
  });

  it("exits 3 when npm gives no report, which is never a pass", () => {
    const done = runWith(JSON.stringify({ error: { summary: "registry unreachable" } }), 1);
    expect(done.output).toContain("registry unreachable");
    expect(done.status).toBe(EXIT_COULD_NOT_RUN);
  });
});
