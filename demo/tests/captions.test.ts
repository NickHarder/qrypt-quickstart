import { describe, expect, it } from "vitest";
import type { Timeline } from "../src/catalog/schemas";
import {
  captionCues,
  captionProblems,
  MAX_CHARACTERS_PER_LINE,
  splitIntoCaptionTexts,
  toSrt,
  wrapCaption,
} from "../src/pipeline/captions";
import { contrastProblems, contrastRatio } from "../src/pipeline/contrast";
import { exampleBrand } from "./fixtures";

const FPS = 30;

/** A timeline of one scene whose lines are given as [text, start seconds, length seconds]. */
const timelineOf = (lines: [string, number, number][], totalSeconds: number): Timeline => ({
  title: "Test",
  frames_per_second: FPS,
  width: 1920,
  height: 1080,
  duration_in_frames: totalSeconds * FPS,
  voice_provider: "test",
  poster_frame: 0,
  brand: exampleBrand,
  scenes: [
    {
      scene: { id: "one", component: "TitleCard", props: { title: "One" }, lines: [] },
      from_frame: 0,
      duration_in_frames: totalSeconds * FPS,
      cues: lines.map(([text, startSeconds, lengthSeconds], index) => ({
        key: `line-${index}`,
        text,
        audio_file: `media/voice/test/line-${index}.wav`,
        from_frame: startSeconds * FPS,
        duration_in_frames: lengthSeconds * FPS,
      })),
    },
  ],
});

describe("splitIntoCaptionTexts", () => {
  it("keeps a short line as one caption", () => {
    expect(splitIntoCaptionTexts("Ask for a total.")).toEqual(["Ask for a total."]);
  });

  it("ends a sentence only where a space follows: a price, a version and an address stay whole", () => {
    expect(splitIntoCaptionTexts("It costs $0.02 on Node.js. See example.com.")).toEqual([
      "It costs $0.02 on Node.js. See example.com.",
    ]);
  });

  it("keeps short sentences together, so none is flashed on its own", () => {
    expect(
      splitIntoCaptionTexts("The same order. One page. Every card live from the server."),
    ).toEqual(["The same order. One page. Every card live from the server."]);
  });

  it("starts a new caption at a sentence end when the next sentence does not fit", () => {
    expect(
      splitIntoCaptionTexts(
        "Her documents, where the system files them. Open one: the page itself, checked to be hers.",
      ),
    ).toEqual([
      "Her documents, where the system files them.",
      "Open one: the page itself, checked to be hers.",
    ]);
  });

  it("splits a long sentence between words, never past two lines' worth", () => {
    const longSentence =
      "The answer quotes the invoice exactly as it was written and names the page it came from every time.";
    const pieces = splitIntoCaptionTexts(longSentence);
    expect(pieces.length).toBeGreaterThan(1);
    expect(pieces.join(" ")).toBe(longSentence);
    for (const piece of pieces) {
      expect(piece.length).toBeLessThanOrEqual(2 * MAX_CHARACTERS_PER_LINE);
    }
  });

  // The final cut failed on these two lines: filling word by word left "shown." and "KiB." alone,
  // on screen for under the 1.2 s minimum. The last two pieces are balanced instead.
  it.each([
    "One request to Qrypt, one AES-256 key, proven with AES-GCM, and the key never shown.",
    "For AI coding agents, llms.txt carries the same rules: no SDK, both headers, size in KiB.",
  ])("leaves no word alone at the end of a long sentence: %s", (longSentence) => {
    const pieces = splitIntoCaptionTexts(longSentence);
    expect(pieces.join(" ")).toBe(longSentence);
    const lastPiece = pieces.at(-1) ?? "";
    expect(lastPiece.split(" ").length).toBeGreaterThan(2);
    for (const piece of pieces) {
      expect(piece.length).toBeLessThanOrEqual(2 * MAX_CHARACTERS_PER_LINE);
    }
  });
});

describe("wrapCaption", () => {
  it("leaves a short caption on one line", () => {
    expect(wrapCaption("Short enough.")).toEqual(["Short enough."]);
  });

  it("wraps onto two balanced lines that each fit", () => {
    const lines = wrapCaption("The answer quotes the invoice exactly as it was written.");
    expect(lines).toHaveLength(2);
    for (const line of lines) {
      expect(line.length).toBeLessThanOrEqual(MAX_CHARACTERS_PER_LINE);
    }
  });
});

describe("captionCues", () => {
  it("starts a caption when its line starts and ends it before the next line", () => {
    const cues = captionCues(
      timelineOf(
        [
          ["First line here.", 1, 2],
          ["Second line here.", 4, 2],
        ],
        8,
      ),
    );
    expect(cues).toHaveLength(2);
    expect(cues[0]?.startSeconds).toBe(1);
    expect(cues[0]?.endSeconds).toBeLessThanOrEqual(3.8);
    expect(cues[1]?.startSeconds).toBe(4);
    expect(captionProblems(cues)).toEqual([]);
  });

  it("gives each caption of a line a share of the time by its length, in order", () => {
    const longLine =
      "The first sentence of this line is clearly the longer of the two. The second is short, but too long to join it.";
    const cues = captionCues(timelineOf([[longLine, 0, 8]], 12));
    expect(cues).toHaveLength(2);
    expect(cues.map((cue) => cue.lines.join(" ")).join(" ")).toBe(longLine);
    expect(cues[0]?.endSeconds).toBe(cues[1]?.startSeconds);
    expect((cues[0]?.endSeconds ?? 0) - (cues[0]?.startSeconds ?? 0)).toBeGreaterThan(
      (cues[1]?.endSeconds ?? 0) - (cues[1]?.startSeconds ?? 0),
    );
    expect(captionProblems(cues)).toEqual([]);
  });

  it("writes captions as SRT", () => {
    const srt = toSrt(captionCues(timelineOf([["Hello there.", 1.5, 2]], 5)));
    expect(srt).toContain("1\n00:00:01,500 --> ");
    expect(srt).toContain("\nHello there.\n");
  });
});

describe("captionProblems", () => {
  it("flags a caption that goes by too fast to read", () => {
    const [problem] = captionProblems([
      {
        startSeconds: 0,
        endSeconds: 1.3,
        lines: ["This caption has far too many characters", "to read in so little time."],
      },
    ]);
    expect(problem).toContain("characters a second");
  });

  it("flags a caption that is not up for long enough, and one that overlaps", () => {
    const problems = captionProblems([
      { startSeconds: 0, endSeconds: 2, lines: ["Fine."] },
      { startSeconds: 1.5, endSeconds: 2, lines: ["Short."] },
    ]);
    expect(problems.some((problem) => problem.includes("the minimum is"))).toBe(true);
    expect(problems.some((problem) => problem.includes("starts before"))).toBe(true);
  });
});

describe("contrast", () => {
  it("computes the WCAG ratio", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 1);
    expect(contrastRatio("#777777", "#777777")).toBeCloseTo(1, 5);
  });

  it("passes the brand that ships with the kit", () => {
    expect(contrastProblems(exampleBrand)).toEqual([]);
  });

  it("names a pair that cannot be read", () => {
    const dimBrand = { ...exampleBrand, colors: { ...exampleBrand.colors, muted: "#22304A" } };
    const problems = contrastProblems(dimBrand);
    expect(problems.some((problem) => problem.includes("muted on background"))).toBe(true);
  });
});
