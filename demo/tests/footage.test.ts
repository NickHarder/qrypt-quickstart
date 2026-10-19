import { describe, expect, it } from "vitest";
import type { BeatRow } from "../src/catalog/schemas";
import { FootageError, fitFootage, MAX_PLAYBACK_RATE, placeFootage } from "../src/pipeline/footage";
import { footageProvenanceProblems } from "../src/pipeline/honesty";
import { parseStoryboard } from "../src/pipeline/storyboard";
import { buildTimeline, FRAMES_PER_SECOND } from "../src/pipeline/timeline";
import { exampleBrand } from "./fixtures";

// A beat row names no file: what plays is the take's recording, the file the honesty check looks up.
const beatRows: BeatRow[] = [{ take: "tour", key: "open", start: 2, end: 8 }];

describe("fitFootage", () => {
  it("plays footage that fits in real time and holds its last frame for the rest", () => {
    expect(fitFootage(6, 10)).toEqual({ playbackRate: 1, playedSeconds: 6, holdSeconds: 4 });
  });

  it("speeds footage up just enough to fit a shorter scene", () => {
    expect(fitFootage(12, 6)).toEqual({ playbackRate: 2, playedSeconds: 6, holdSeconds: 0 });
  });

  it("never speeds footage up past the limit", () => {
    expect(fitFootage(MAX_PLAYBACK_RATE * 5, 5).playbackRate).toBe(MAX_PLAYBACK_RATE);
    expect(() => fitFootage(MAX_PLAYBACK_RATE * 5 + 1, 5)).toThrow(FootageError);
  });

  it("never slows footage down", () => {
    expect(fitFootage(1, 30).playbackRate).toBe(1);
  });
});

describe("placeFootage", () => {
  it("starts at the beat and holds when the scene is longer", () => {
    const placement = placeFootage("s", { take: "tour", beat: "open" }, beatRows, 300, 30);
    expect(placement).toEqual({
      video_file: "media/takes/tour.webm",
      source_start_frame: 60,
      playback_rate: 1,
      played_frames: 180,
      hold_frames: 120,
    });
  });

  it("applies the storyboard's trim before fitting", () => {
    const placement = placeFootage(
      "s",
      { take: "tour", beat: "open", trim: { head_seconds: 1, tail_seconds: 2 } },
      beatRows,
      90,
      30,
    );
    expect(placement.source_start_frame).toBe(90);
    expect(placement.played_frames).toBe(90);
    expect(placement.playback_rate).toBe(1);
  });

  it("names the scene when the beat was never recorded", () => {
    expect(() =>
      placeFootage("intro", { take: "tour", beat: "missing" }, beatRows, 150, 30),
    ).toThrow(/scene "intro".*has not been\s+recorded/s);
  });

  it("names the scene when a key phrase would come after it has ended", () => {
    const lateKeyPhrase = { text: "Too late", at_seconds: 12, for_seconds: 3 };
    expect(() =>
      placeFootage(
        "intro",
        { take: "tour", beat: "open", key_phrases: [lateKeyPhrase] },
        beatRows,
        300,
        30,
      ),
    ).toThrow(/scene "intro".*"Too late"/s);
  });

  it("names the scene when the footage cannot fit", () => {
    expect(() => placeFootage("intro", { take: "tour", beat: "open" }, beatRows, 30, 30)).toThrow(
      /scene "intro".*Trim the beat/s,
    );
  });
});

const recordingStoryboard = parseStoryboard({
  title: "Test",
  target_seconds: { min: 1, max: 600 },
  scenes: [
    {
      id: "tour",
      component: "ScreenRecording",
      props: { take: "tour", beat: "open" },
      lines: [{ key: "tour", text: "Here it is." }],
    },
  ],
});

describe("a ScreenRecording scene on the timeline", () => {
  it("carries its footage placement, sped up to fit a short line", () => {
    const voiced = new Map([
      ["tour", { audioFile: "media/voice/test/tour.wav", durationSeconds: 2.2 }],
    ]);
    const timeline = buildTimeline(recordingStoryboard, exampleBrand, voiced, "test", { beatRows });
    const [timedScene] = timeline.scenes;
    expect(timedScene?.duration_in_frames).toBe(3 * FRAMES_PER_SECOND);
    expect(timedScene?.footage?.playback_rate).toBeCloseTo(2, 5);
    expect(timedScene?.footage?.hold_frames).toBe(0);
  });
});

describe("a ScreenRecording scene of any length", () => {
  it("fills every frame of its scene with footage, played or held", () => {
    for (let lineMilliseconds = 1000; lineMilliseconds < 4000; lineMilliseconds += 7) {
      const voiced = new Map([
        [
          "tour",
          { audioFile: "media/voice/test/tour.wav", durationSeconds: lineMilliseconds / 1000 },
        ],
      ]);
      const timeline = buildTimeline(recordingStoryboard, exampleBrand, voiced, "test", {
        beatRows,
      });
      const [timedScene] = timeline.scenes;
      const footageFrames =
        (timedScene?.footage?.played_frames ?? 0) + (timedScene?.footage?.hold_frames ?? 0);
      expect(footageFrames, `a line of ${lineMilliseconds} ms`).toBe(
        timedScene?.duration_in_frames,
      );
    }
  });
});

describe("footageProvenanceProblems", () => {
  const entry = { sha256: "a".repeat(64), bytes: 1 };

  it("passes a take the manifest lists as recorded", () => {
    const manifest = { "takes/tour.webm": { ...entry, provenance: "recorded" as const } };
    expect(footageProvenanceProblems(recordingStoryboard, manifest)).toEqual([]);
  });

  it("fails a take that is not in the manifest", () => {
    expect(footageProvenanceProblems(recordingStoryboard, {})[0]).toContain("make demo-capture");
  });

  it("fails generated footage standing in for the product", () => {
    const manifest = { "takes/tour.webm": { ...entry, provenance: "generated" as const } };
    expect(footageProvenanceProblems(recordingStoryboard, manifest)[0]).toContain(
      "never generated",
    );
  });
});
