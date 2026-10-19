/**
 * Stills before a render: one frame of every scene once its text has settled, and its last frame,
 * so overflow, a collision and low contrast are seen in seconds, not after a full render. The
 * composition is bundled once and each still is rendered from the same bundle.
 */
import { mkdirSync } from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import type { TimedScene, Timeline } from "../catalog/schemas";
import { ENTRY_POINT } from "./paths";
import { settledSeconds } from "./reading";

export class StillsError extends Error {}

/** The composition registered in `Root.tsx`. */
const COMPOSITION_ID = "Demo";

export type Still = {
  file: string;
  /** The frame of the whole cut. */
  frame: number;
  sceneId: string;
  moment: "settled" | "last";
};

const padded = (index: number): string => String(index + 1).padStart(2, "0");

const stillsOfScene = (
  timedScene: TimedScene,
  index: number,
  framesPerSecond: number,
  outputDirectory: string,
): Still[] => {
  const lastFrameIntoScene = timedScene.duration_in_frames - 1;
  const settledFrameIntoScene = Math.min(
    lastFrameIntoScene,
    Math.round(settledSeconds(timedScene.scene) * framesPerSecond),
  );
  const fileFor = (moment: Still["moment"]): string =>
    path.join(outputDirectory, `${padded(index)}-${timedScene.scene.id}-${moment}.png`);
  return [
    {
      file: fileFor("settled"),
      frame: timedScene.from_frame + settledFrameIntoScene,
      sceneId: timedScene.scene.id,
      moment: "settled",
    },
    {
      file: fileFor("last"),
      frame: timedScene.from_frame + lastFrameIntoScene,
      sceneId: timedScene.scene.id,
      moment: "last",
    },
  ];
};

/** The stills a timeline calls for, in the order of the cut. */
export const stillsOf = (timeline: Timeline, outputDirectory: string): Still[] =>
  timeline.scenes.flatMap((timedScene, index) =>
    stillsOfScene(timedScene, index, timeline.frames_per_second, outputDirectory),
  );

/** Render every still into the directory, and return them. */
export const renderStills = async (
  timeline: Timeline,
  outputDirectory: string,
  onRendered: (still: Still) => void,
): Promise<Still[]> => {
  mkdirSync(outputDirectory, { recursive: true });
  const stills = stillsOf(timeline, outputDirectory);
  const serveUrl = await bundle({ entryPoint: ENTRY_POINT }).catch((error: unknown) => {
    throw new StillsError(
      `could not bundle the composition (${error instanceof Error ? error.message : String(error)})`,
    );
  });
  const composition = await selectComposition({
    serveUrl,
    id: COMPOSITION_ID,
    inputProps: timeline,
  });
  await stills.reduce<Promise<void>>(
    (previous, still) =>
      previous.then(async () => {
        await renderStill({
          composition,
          serveUrl,
          output: still.file,
          frame: still.frame,
          inputProps: timeline,
          imageFormat: "png",
        });
        onRendered(still);
      }),
    Promise.resolve(),
  );
  return stills;
};
