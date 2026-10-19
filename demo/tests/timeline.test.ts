import { describe, expect, it } from "vitest";
import type { Brand, Storyboard } from "../src/catalog/schemas";
import { parseStoryboard } from "../src/pipeline/storyboard";
import {
  buildTimeline,
  FRAMES_PER_SECOND,
  LINE_LEAD_SECONDS,
  lengthProblems,
  MissingAudioError,
  SCENE_TAIL_SECONDS,
  type VoicedLine,
} from "../src/pipeline/timeline";
import { exampleBrand } from "./fixtures";

const storyboardWith = (scenes: unknown[], targetSeconds = { min: 1, max: 600 }): Storyboard =>
  parseStoryboard({ title: "Test", target_seconds: targetSeconds, scenes });

const titleScene = (id: string, lines: unknown[], extra: Record<string, unknown> = {}) => ({
  id,
  component: "TitleCard",
  props: { title: id },
  lines,
  ...extra,
});

const voiced = (entries: Record<string, number>): Map<string, VoicedLine> =>
  new Map(
    Object.entries(entries).map(([key, durationSeconds]) => [
      key,
      { audioFile: `media/voice/test/${key}.wav`, durationSeconds },
    ]),
  );

const brand: Brand = exampleBrand;

describe("buildTimeline", () => {
  it("makes a scene exactly as long as its line takes to say, plus the lead and the tail", () => {
    const storyboard = storyboardWith([titleScene("one", [{ key: "a", text: "Hello there." }])]);
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 2.0 }), "test");
    const expectedSeconds = LINE_LEAD_SECONDS + 2.0 + SCENE_TAIL_SECONDS;
    expect(timeline.scenes[0]?.duration_in_frames).toBe(
      Math.ceil(expectedSeconds * FRAMES_PER_SECOND),
    );
    expect(timeline.scenes[0]?.cues[0]?.from_frame).toBe(
      Math.ceil(LINE_LEAD_SECONDS * FRAMES_PER_SECOND),
    );
    expect(timeline.duration_in_frames).toBe(timeline.scenes[0]?.duration_in_frames);
  });

  it("never starts a line before the one before it has ended", () => {
    const storyboard = storyboardWith([
      titleScene("one", [
        { key: "a", text: "First.", pause_before_seconds: 0 },
        { key: "b", text: "Second.", pause_before_seconds: 0 },
        { key: "c", text: "Third.", pause_before_seconds: 0 },
      ]),
    ]);
    const timeline = buildTimeline(
      storyboard,
      brand,
      voiced({ a: 3.01, b: 3.01, c: 3.01 }),
      "test",
    );
    const cues = timeline.scenes[0]?.cues ?? [];
    for (const [cueIndex, cue] of cues.slice(1).entries()) {
      const cueBefore = cues[cueIndex];
      expect(cue.from_frame).toBeGreaterThanOrEqual(
        (cueBefore?.from_frame ?? 0) + (cueBefore?.duration_in_frames ?? 0),
      );
    }
  });

  it("places scenes one after another and lines one after another", () => {
    const storyboard = storyboardWith([
      titleScene("one", [
        { key: "a", text: "First." },
        { key: "b", text: "Second." },
      ]),
      titleScene("two", [{ key: "c", text: "Third." }]),
    ]);
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 1.0, b: 2.0, c: 1.5 }), "test");
    const [firstScene, secondScene] = timeline.scenes;
    expect(firstScene?.from_frame).toBe(0);
    expect(secondScene?.from_frame).toBe(firstScene?.duration_in_frames);
    const [firstCue, secondCue] = firstScene?.cues ?? [];
    // The second line starts after the first has finished and its own lead-in has passed.
    expect(secondCue?.from_frame).toBe(
      Math.ceil((LINE_LEAD_SECONDS + 1.0 + LINE_LEAD_SECONDS) * FRAMES_PER_SECOND),
    );
    expect(firstCue?.audio_file).toBe("media/voice/test/a.wav");
    expect(timeline.duration_in_frames).toBe(
      (firstScene?.duration_in_frames ?? 0) + (secondScene?.duration_in_frames ?? 0),
    );
  });

  it("uses a line's own pause instead of the standard lead-in", () => {
    const storyboard = storyboardWith([
      titleScene("one", [{ key: "a", text: "After a beat.", pause_before_seconds: 2 }]),
    ]);
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 1.0 }), "test");
    expect(timeline.scenes[0]?.cues[0]?.from_frame).toBe(2 * FRAMES_PER_SECOND);
  });

  it("holds a scene for min_seconds when its lines are shorter, and gives a silent scene a length", () => {
    const storyboard = storyboardWith([
      titleScene("held", [{ key: "a", text: "Short." }], { min_seconds: 10 }),
      titleScene("silent", [], { min_seconds: 3 }),
    ]);
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 1.0 }), "test");
    expect(timeline.scenes[0]?.duration_in_frames).toBe(10 * FRAMES_PER_SECOND);
    expect(timeline.scenes[1]?.duration_in_frames).toBe(3 * FRAMES_PER_SECOND);
    expect(timeline.scenes[1]?.cues).toEqual([]);
  });

  it("refuses to build a timeline when a line has no audio", () => {
    const storyboard = storyboardWith([titleScene("one", [{ key: "a", text: "Unvoiced." }])]);
    expect(() => buildTimeline(storyboard, brand, voiced({}), "test")).toThrow(MissingAudioError);
  });
});

describe("lengthProblems", () => {
  const storyboard = storyboardWith(
    [
      titleScene("long", [{ key: "a", text: "Long." }]),
      titleScene("short", [{ key: "b", text: "Short." }]),
    ],
    { min: 5, max: 10 },
  );

  it("is empty when the cut is inside its target", () => {
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 4, b: 1 }), "test");
    expect(lengthProblems(storyboard, timeline)).toEqual([]);
  });

  it("names the longest scenes when the cut is over", () => {
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 20, b: 1 }), "test");
    const [problem] = lengthProblems(storyboard, timeline);
    expect(problem).toContain("over the target");
    expect(problem?.indexOf("long (")).toBeLessThan(problem?.indexOf("short (") ?? -1);
  });

  it("says so when the cut is under", () => {
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 0.5, b: 0.5 }), "test");
    expect(lengthProblems(storyboard, timeline)[0]).toContain("under the target");
  });
});

describe("the poster frame", () => {
  const two = [
    titleScene("one", [{ key: "a", text: "Hello there." }]),
    titleScene("two", [{ key: "b", text: "And again." }]),
  ];

  it("is the first scene a second in, once its text has settled, when the storyboard names none", () => {
    const timeline = buildTimeline(storyboardWith(two), brand, voiced({ a: 2.0, b: 2.0 }), "test");
    expect(timeline.poster_frame).toBe(Math.round(1.0 * FRAMES_PER_SECOND));
  });

  it("is the scene and second the storyboard names", () => {
    const storyboard = parseStoryboard({
      title: "Test",
      target_seconds: { min: 1, max: 600 },
      scenes: two,
      poster: { scene: "two", at_seconds: 1.0 },
    });
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 2.0, b: 2.0 }), "test");
    const second = timeline.scenes[1];
    expect(timeline.poster_frame).toBe((second?.from_frame ?? 0) + FRAMES_PER_SECOND);
  });

  it("never falls past the end of its scene", () => {
    const storyboard = parseStoryboard({
      title: "Test",
      target_seconds: { min: 1, max: 600 },
      scenes: two,
      poster: { scene: "one", at_seconds: 60 },
    });
    const timeline = buildTimeline(storyboard, brand, voiced({ a: 2.0, b: 2.0 }), "test");
    const first = timeline.scenes[0];
    expect(timeline.poster_frame).toBe((first?.duration_in_frames ?? 1) - 1);
  });

  it("refuses a poster in a scene the storyboard does not have", () => {
    expect(() =>
      parseStoryboard({
        title: "Test",
        target_seconds: { min: 1, max: 600 },
        scenes: two,
        poster: { scene: "three", at_seconds: 1 },
      }),
    ).toThrow(/poster names scene "three"/);
  });
});
