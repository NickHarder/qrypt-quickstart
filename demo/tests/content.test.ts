import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { Scene } from "../src/catalog/schemas";
import { ContentError, MAX_CODE_LINES, resolveSceneContent } from "../src/pipeline/content";
import { parseStoryboard } from "../src/pipeline/storyboard";

const repositoryWith = (files: Record<string, string>): string => {
  const repositoryRoot = mkdtempSync(path.join(tmpdir(), "demo-content-"));
  for (const [relativeFile, text] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(repositoryRoot, relativeFile)), { recursive: true });
    writeFileSync(path.join(repositoryRoot, relativeFile), text);
  }
  return repositoryRoot;
};

const sceneOf = (component: string, props: unknown): Scene => {
  const storyboard = parseStoryboard({
    title: "Test",
    target_seconds: { min: 1, max: 600 },
    scenes: [{ id: "shown", component, props, lines: [{ key: "a", text: "A line." }] }],
  });
  return storyboard.scenes[0] as Scene;
};

const tenLines = `${Array.from({ length: 10 }, (_, index) => `line ${index + 1}`).join("\n")}\n`;

describe("a CodeHighlight scene", () => {
  it("shows the lines of the file as they are, with their numbers", () => {
    const repositoryRoot = repositoryWith({ "src/app.py": tenLines });
    const scene = sceneOf("CodeHighlight", {
      file: "src/app.py",
      from_line: 3,
      to_line: 5,
      highlight: [4],
    });
    expect(resolveSceneContent(scene, repositoryRoot).code_lines).toEqual([
      { number: 3, text: "line 3" },
      { number: 4, text: "line 4" },
      { number: 5, text: "line 5" },
    ]);
  });

  it("fails when the file or the range does not exist", () => {
    const repositoryRoot = repositoryWith({ "src/app.py": tenLines });
    const missingFile = sceneOf("CodeHighlight", { file: "src/gone.py", from_line: 1, to_line: 2 });
    expect(() => resolveSceneContent(missingFile, repositoryRoot)).toThrow(/does not exist/);
    const pastTheEnd = sceneOf("CodeHighlight", { file: "src/app.py", from_line: 8, to_line: 12 });
    expect(() => resolveSceneContent(pastTheEnd, repositoryRoot)).toThrow(/has 10 lines/);
  });

  it("fails when the excerpt would not fit the frame or highlights a line it does not show", () => {
    const longFile = `${Array.from({ length: 60 }, (_, index) => `x = ${index}`).join("\n")}\n`;
    const repositoryRoot = repositoryWith({
      "big.py": longFile,
      "wide.py": `${"x".repeat(200)}\n`,
    });
    const tooTall = sceneOf("CodeHighlight", {
      file: "big.py",
      from_line: 1,
      to_line: MAX_CODE_LINES + 1,
    });
    expect(() => resolveSceneContent(tooTall, repositoryRoot)).toThrow(ContentError);
    const tooWide = sceneOf("CodeHighlight", { file: "wide.py", from_line: 1, to_line: 1 });
    expect(() => resolveSceneContent(tooWide, repositoryRoot)).toThrow(/characters/);
    const strayHighlight = sceneOf("CodeHighlight", {
      file: "big.py",
      from_line: 1,
      to_line: 5,
      highlight: [9],
    });
    expect(() => resolveSceneContent(strayHighlight, repositoryRoot)).toThrow(/outside the lines/);
  });

  it("cannot name a file outside the repository", () => {
    expect(() =>
      sceneOf("CodeHighlight", { file: "../secrets.txt", from_line: 1, to_line: 1 }),
    ).toThrow(/repository root/);
    expect(() =>
      sceneOf("CodeHighlight", { file: "/etc/hosts", from_line: 1, to_line: 1 }),
    ).toThrow();
  });
});

describe("a Terminal scene", () => {
  it("shows the captured output, or the range of it that is asked for", () => {
    const repositoryRoot = repositoryWith({ "docs/gate-output.txt": tenLines });
    const whole = sceneOf("Terminal", {
      command: "make gate",
      output_file: "docs/gate-output.txt",
    });
    expect(resolveSceneContent(whole, repositoryRoot).terminal_lines).toHaveLength(10);
    const tail = sceneOf("Terminal", {
      command: "make gate",
      output_file: "docs/gate-output.txt",
      from_line: 9,
    });
    expect(resolveSceneContent(tail, repositoryRoot).terminal_lines).toEqual(["line 9", "line 10"]);
  });

  it("fails when there is no captured output to show", () => {
    const scene = sceneOf("Terminal", {
      command: "make gate",
      output_file: "docs/never-captured.txt",
    });
    expect(() => resolveSceneContent(scene, repositoryWith({}))).toThrow(/does not exist/);
  });
});

describe("scenes with nothing to read", () => {
  it("resolve to nothing", () => {
    expect(
      resolveSceneContent(sceneOf("Statement", { text: "One claim." }), repositoryWith({})),
    ).toEqual({});
  });
});

describe("MetricCards", () => {
  it("rejects a number with no source or no scope", () => {
    const metric = { value: "4 s", label: "to a first answer" };
    expect(() => sceneOf("MetricCards", { metrics: [metric] })).toThrow(/source/);
    expect(() =>
      sceneOf("MetricCards", { metrics: [{ ...metric, source: "docs/LOAD_TEST.md" }] }),
    ).toThrow(/scope/);
    expect(() =>
      sceneOf("MetricCards", {
        metrics: [{ ...metric, source: "docs/LOAD_TEST.md", scope: "one user" }],
      }),
    ).not.toThrow();
  });
});
