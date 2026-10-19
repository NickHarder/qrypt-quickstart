import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { BRAND_FILE, STORYBOARD_FILE } from "../src/pipeline/paths";
import { parseBrand, parseStoryboard, ValidationError } from "../src/pipeline/storyboard";

const validScene = {
  id: "open",
  component: "TitleCard",
  props: { title: "Title" },
  lines: [{ key: "open", text: "A line." }],
};
const storyboardOf = (scenes: unknown[]) => ({
  title: "Test",
  target_seconds: { min: 1, max: 300 },
  scenes,
});

const problemsOf = (rawStoryboard: unknown): string => {
  try {
    parseStoryboard(rawStoryboard);
  } catch (error) {
    if (error instanceof ValidationError) {
      return error.message;
    }
    throw error;
  }
  return "";
};

describe("the files a project ships", () => {
  it("has a storyboard that satisfies the catalog", () => {
    expect(() => parseStoryboard(JSON.parse(readFileSync(STORYBOARD_FILE, "utf8")))).not.toThrow();
  });

  it("has a brand that satisfies its schema", () => {
    expect(() => parseBrand(JSON.parse(readFileSync(BRAND_FILE, "utf8")))).not.toThrow();
  });
});

describe("parseStoryboard", () => {
  it("accepts a scene that uses a catalog component with its props", () => {
    expect(parseStoryboard(storyboardOf([validScene])).scenes).toHaveLength(1);
  });

  it("rejects a component that is not in the catalog", () => {
    const problems = problemsOf(storyboardOf([{ ...validScene, component: "SpinningLogo" }]));
    expect(problems).toContain("scenes.0.component");
  });

  it("rejects a prop the component does not declare", () => {
    const problems = problemsOf(
      storyboardOf([{ ...validScene, props: { title: "Title", sparkle: true } }]),
    );
    expect(problems).toContain("scenes.0.props");
    expect(problems).toContain("sparkle");
  });

  it("rejects a missing required prop", () => {
    expect(problemsOf(storyboardOf([{ ...validScene, props: {} }]))).toContain(
      "scenes.0.props.title",
    );
  });

  it("rejects two scenes with the same id and two lines with the same key", () => {
    const problems = problemsOf(storyboardOf([validScene, validScene]));
    expect(problems).toContain('scene id "open" is used more than once');
    expect(problems).toContain('line key "open" is used more than once');
  });

  it("rejects a scene with no lines and no length", () => {
    const problems = problemsOf(storyboardOf([{ ...validScene, lines: [] }]));
    expect(problems).toContain("needs min_seconds");
  });

  it("rejects an empty line and a key that is not a safe file name", () => {
    const problems = problemsOf(
      storyboardOf([{ ...validScene, lines: [{ key: "Bad Key!", text: "" }] }]),
    );
    expect(problems).toContain("scenes.0.lines.0.key");
    expect(problems).toContain("scenes.0.lines.0.text");
  });
});
