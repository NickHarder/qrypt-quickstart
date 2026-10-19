import { describe, expect, it } from "vitest";
import type { Scene, Storyboard } from "../src/catalog/schemas";
import {
  KEY_PHRASE_FADE_SECONDS,
  LABEL_SECONDS,
  readingNeed,
  readingProblems,
  readingSeconds,
  SENTENCE_FLOOR_SECONDS,
  settledSeconds,
} from "../src/pipeline/reading";
import { parseStoryboard } from "../src/pipeline/storyboard";

const storyboardWith = (scenes: unknown[]): Storyboard =>
  parseStoryboard({ title: "Test", target_seconds: { min: 1, max: 600 }, scenes });

const sceneOf = (scene: unknown): Scene => storyboardWith([scene]).scenes[0] as Scene;

const TEN_WORDS = "one two three four five six seven eight nine ten";

describe("readingSeconds", () => {
  it("gives a label its fixed time, and a sentence 0.3 s a word with a floor", () => {
    expect(readingSeconds("Gate green")).toBe(LABEL_SECONDS);
    expect(readingSeconds("one two three")).toBe(LABEL_SECONDS);
    expect(readingSeconds("one two three four")).toBe(SENTENCE_FLOOR_SECONDS);
    expect(readingSeconds(TEN_WORDS)).toBeCloseTo(3.0, 5);
  });
});

describe("readingNeed", () => {
  it("adds up a title card's title and subtitle, settled when the subtitle is in", () => {
    const need = readingNeed(
      sceneOf({
        id: "open",
        component: "TitleCard",
        props: { title: "A title", subtitle: TEN_WORDS },
        lines: [],
        min_seconds: 5,
      }),
    );
    expect(need.readingSeconds).toBeCloseTo(LABEL_SECONDS + 3.0, 5);
    expect(need.settledSeconds).toBe(1.0);
  });

  it("settles metric cards when the last card is in", () => {
    const metric = {
      value: "4 s",
      label: "to the first answer",
      source: "evals",
      scope: "eval run",
    };
    const need = readingNeed(
      sceneOf({
        id: "numbers",
        component: "MetricCards",
        props: { metrics: [metric, metric, metric] },
        lines: [],
        min_seconds: 10,
      }),
    );
    expect(need.settledSeconds).toBeCloseTo(0.7 + 0.25 * 2, 5);
    expect(need.readingSeconds).toBeCloseTo(3 * readingSeconds("4 s to the first answer"), 5);
  });

  it("asks nothing of footage, code or a terminal, and settles them after a second", () => {
    const terminal = sceneOf({
      id: "gate",
      component: "Terminal",
      props: { command: "make gate", output_file: "docs/gate.txt" },
      lines: [],
      min_seconds: 4,
    });
    expect(readingNeed(terminal)).toEqual({ readingSeconds: 0, settledSeconds: 1.0 });
    expect(settledSeconds(terminal)).toBe(1.0);
  });
});

describe("readingProblems", () => {
  const titleCard = (subtitle: string, extra: Record<string, unknown> = {}) => ({
    id: "open",
    component: "TitleCard",
    props: { title: "A title", subtitle },
    lines: [{ key: "open", text: "Short line." }],
    ...extra,
  });

  it("names a scene whose text needs longer than it is on screen, and the min_seconds that would do", () => {
    const [problem, ...rest] = readingProblems(storyboardWith([titleCard(TEN_WORDS)]), () => 2.5);
    expect(rest).toEqual([]);
    expect(problem).toContain('scene "open": its text needs 3.8 s to read');
    expect(problem).toContain("whole on screen for 1.5 s");
    expect(problem).toContain("set min_seconds to 4.8 or more");
  });

  it("is satisfied once the scene is long enough", () => {
    expect(readingProblems(storyboardWith([titleCard(TEN_WORDS)]), () => 4.8)).toEqual([]);
  });

  it("is satisfied by a scene exactly as long as its text, though its sum is a hair over", () => {
    // Three labels: 0.8 + 0.8 + 0.8 adds up to 2.4000000000000004 s, and 2.9 less 0.5 is 2.4.
    const endCard = {
      id: "close",
      component: "EndCard",
      props: { title: "A title", links: ["docs/a.md", "docs/b.md"] },
      lines: [{ key: "close", text: "That is all." }],
    };
    expect(readingProblems(storyboardWith([endCard]), () => 2.9)).toEqual([]);
  });

  it("rounds the min_seconds it gives up, so that the advice is enough", () => {
    // Settled at 0.95 s, then two labels to read: 2.55 s in all, which to one decimal is 2.5.
    const metric = { value: "4", label: "s", source: "evals", scope: "eval run" };
    const cards = {
      id: "numbers",
      component: "MetricCards",
      props: { metrics: [metric, metric] },
      lines: [{ key: "numbers", text: "Two numbers." }],
    };
    const [problem] = readingProblems(storyboardWith([cards]), () => 1);
    expect(problem).toContain("set min_seconds to 2.6 or more");
    expect(readingProblems(storyboardWith([cards]), () => 2.6)).toEqual([]);
  });

  it("holds a key phrase to its own time, less its fades", () => {
    const recording = {
      id: "ask",
      component: "ScreenRecording",
      props: {
        take: "example",
        beat: "ask",
        key_phrases: [{ text: TEN_WORDS, at_seconds: 1, for_seconds: 2 }],
      },
      lines: [{ key: "ask", text: "A line." }],
    };
    const [problem] = readingProblems(storyboardWith([recording]), () => 30);
    expect(problem).toContain("the key phrase");
    expect(problem).toContain(`for_seconds of ${(3.0 + 2 * KEY_PHRASE_FADE_SECONDS).toFixed(1)}`);
    const longer = {
      ...recording,
      props: {
        ...recording.props,
        key_phrases: [{ text: TEN_WORDS, at_seconds: 1, for_seconds: 3.6 }],
      },
    };
    expect(readingProblems(storyboardWith([longer]), () => 30)).toEqual([]);
  });
});
