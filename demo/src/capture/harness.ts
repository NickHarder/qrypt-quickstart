/**
 * Record takes of the real product with Playwright, and log where each beat starts and ends.
 *
 * It drives the Chrome already installed on the machine. Each take runs in a fresh browser context at
 * the composition's size, and its video is saved as a media file with provenance `recorded`.
 */
import { mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";
import type { BeatRow } from "../catalog/schemas";
import { loadBeatRows } from "../pipeline/footage";
import { recordMedia } from "../pipeline/manifest";
import { HEIGHT, WIDTH } from "../pipeline/timeline";
import type { Take } from "./take";

export class CaptureError extends Error {}

const TAKE_FILE_SUFFIX = ".take.ts";

export const loadTakes = async (takesDirectory: string): Promise<Take[]> => {
  const takeFiles = readdirSync(takesDirectory)
    .filter((fileName) => fileName.endsWith(TAKE_FILE_SUFFIX))
    .sort();
  const takes: Take[] = [];
  for (const takeFile of takeFiles) {
    const takeModule = (await import(pathToFileURL(path.join(takesDirectory, takeFile)).href)) as {
      default?: Take;
    };
    if (takeModule.default === undefined) {
      throw new CaptureError(`${takeFile} has no default export; export one with defineTake()`);
    }
    takes.push(takeModule.default);
  }
  return takes;
};

export type CaptureOptions = {
  mediaDirectory: string;
  beatsFile: string;
  manifestFile: string;
  exampleSiteDirectory: string;
  /** How long each beat must stay on screen, by beat key, so its narration fits. */
  holdSecondsByBeat: ReadonlyMap<string, number>;
};

/** Record one take, and return the beats it marked. */
export const recordTake = async (take: Take, options: CaptureOptions): Promise<BeatRow[]> => {
  const scratchDirectory = mkdtempSync(path.join(tmpdir(), "demo-capture-"));
  const beatRows: BeatRow[] = [];
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  try {
    const context = await browser.newContext({
      viewport: { width: WIDTH, height: HEIGHT },
      deviceScaleFactor: 1,
      recordVideo: { dir: scratchDirectory, size: { width: WIDTH, height: HEIGHT } },
    });
    const page = await context.newPage();
    const recordingStartedAt = performance.now();
    const secondsIntoRecording = (): number => (performance.now() - recordingStartedAt) / 1000;

    await take.run({
      page,
      exampleSiteUrl: (relativePath) =>
        pathToFileURL(path.join(options.exampleSiteDirectory, relativePath)).href,
      beat: async (key, action) => {
        const beatStartSeconds = secondsIntoRecording();
        await action();
        const neededSeconds = options.holdSecondsByBeat.get(key) ?? 0;
        const elapsedSeconds = secondsIntoRecording() - beatStartSeconds;
        if (elapsedSeconds < neededSeconds) {
          // Hold the shot until the line would have been said.
          await page.waitForTimeout((neededSeconds - elapsedSeconds) * 1000);
        }
        beatRows.push({
          take: take.name,
          key,
          start: Number(beatStartSeconds.toFixed(3)),
          end: Number(secondsIntoRecording().toFixed(3)),
        });
      },
    });

    const recordedVideo = page.video();
    await context.close(); // The video file is complete only once the context is closed.
    if (recordedVideo === null) {
      throw new CaptureError(`take "${take.name}" produced no video`);
    }
    const takesDirectory = path.join(options.mediaDirectory, "takes");
    mkdirSync(takesDirectory, { recursive: true });
    // Copied, not moved: the temporary folder can be on another file system (a tmpfs /tmp).
    await recordedVideo.saveAs(path.join(takesDirectory, `${take.name}.webm`));
  } finally {
    await browser.close();
    rmSync(scratchDirectory, { recursive: true, force: true });
  }
  if (beatRows.length === 0) {
    throw new CaptureError(`take "${take.name}" marked no beats; wrap its steps in beat()`);
  }
  return beatRows;
};

/** Record one take and keep what it marked: its beats in beats.json, its video in the manifest. */
export const captureTake = async (take: Take, options: CaptureOptions): Promise<void> => {
  const newBeatRows = await recordTake(take, options);
  const keptBeatRows = loadBeatRows(options.beatsFile).filter((row) => row.take !== take.name);
  writeFileSync(
    options.beatsFile,
    `${JSON.stringify([...keptBeatRows, ...newBeatRows], null, 2)}\n`,
    "utf8",
  );
  recordMedia(options.manifestFile, options.mediaDirectory, `takes/${take.name}.webm`, "recorded");
  const beatSummary = newBeatRows
    .map((row) => `${row.key} ${(row.end - row.start).toFixed(1)} s`)
    .join(", ");
  console.log(`capture: ${take.name} recorded (${beatSummary})`);
};
