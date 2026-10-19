import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { assetProblems, loadManifest, recordMedia } from "../src/pipeline/manifest";

const scratch = (): { mediaDirectory: string; manifestFile: string } => {
  const directory = mkdtempSync(path.join(tmpdir(), "demo-manifest-"));
  const mediaDirectory = path.join(directory, "media");
  mkdirSync(path.join(mediaDirectory, "takes"), { recursive: true });
  return { mediaDirectory, manifestFile: path.join(directory, "media.lock.json") };
};

describe("the media manifest", () => {
  it("records a file's checksum and provenance, and then agrees with the disk", () => {
    const { mediaDirectory, manifestFile } = scratch();
    writeFileSync(path.join(mediaDirectory, "takes", "tour.webm"), "footage");
    recordMedia(manifestFile, mediaDirectory, "takes/tour.webm", "recorded");
    const manifest = loadManifest(manifestFile);
    expect(manifest["takes/tour.webm"]?.provenance).toBe("recorded");
    expect(manifest["takes/tour.webm"]?.bytes).toBe(7);
    expect(assetProblems(manifest, mediaDirectory)).toEqual([]);
  });

  it("reports a missing file, a changed file and an unlisted file", () => {
    const { mediaDirectory, manifestFile } = scratch();
    writeFileSync(path.join(mediaDirectory, "takes", "kept.webm"), "one");
    writeFileSync(path.join(mediaDirectory, "takes", "gone.webm"), "two");
    recordMedia(manifestFile, mediaDirectory, "takes/kept.webm", "recorded");
    recordMedia(manifestFile, mediaDirectory, "takes/gone.webm", "recorded");
    const manifest = loadManifest(manifestFile);
    writeFileSync(path.join(mediaDirectory, "takes", "kept.webm"), "edited");
    writeFileSync(path.join(mediaDirectory, "takes", "gone.webm"), "");
    writeFileSync(path.join(mediaDirectory, "takes", "stray.webm"), "three");
    const problems = assetProblems(
      { ...manifest, "takes/absent.webm": manifest["takes/gone.webm"] as never },
      mediaDirectory,
    );
    expect(problems.some((problem) => problem.startsWith("CHANGED takes/kept.webm"))).toBe(true);
    expect(problems.some((problem) => problem.startsWith("MISSING takes/absent.webm"))).toBe(true);
    expect(problems.some((problem) => problem.startsWith("UNLISTED takes/stray.webm"))).toBe(true);
  });

  it("asks for the final voice's index to be listed: without it every line is paid for again", () => {
    const { mediaDirectory } = scratch();
    mkdirSync(path.join(mediaDirectory, "voice", "gemini"), { recursive: true });
    writeFileSync(path.join(mediaDirectory, "voice", "gemini", "index.json"), "{}");
    expect(assetProblems({}, mediaDirectory)).toEqual([
      expect.stringMatching(/^UNLISTED voice\/gemini\/index\.json/),
    ]);
  });

  it("does not ask for draft voice clips to be listed: they can always be made again", () => {
    const { mediaDirectory } = scratch();
    for (const freeVoice of ["kokoro", "say", "espeak", "silent"]) {
      mkdirSync(path.join(mediaDirectory, "voice", freeVoice), { recursive: true });
      writeFileSync(path.join(mediaDirectory, "voice", freeVoice, "open.wav"), "draft");
      writeFileSync(path.join(mediaDirectory, "voice", freeVoice, "index.json"), "{}");
    }
    expect(assetProblems({}, mediaDirectory)).toEqual([]);
  });
});
