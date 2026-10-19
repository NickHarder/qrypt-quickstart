/** Render the composition with Remotion's own command line, from the timeline the pipeline wrote. */
import { spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";
import { DEMO_DIRECTORY, ENTRY_POINT } from "./paths";

export class RenderError extends Error {}

export type RenderOptions = {
  timelineFile: string;
  outputFile: string;
  /** 1 is full size; a draft uses 0.5, which renders about four times faster. */
  scale: number;
};

export const renderVideo = ({ timelineFile, outputFile, scale }: RenderOptions): void => {
  mkdirSync(path.dirname(outputFile), { recursive: true });
  const remotionBinary = path.join(DEMO_DIRECTORY, "node_modules", ".bin", "remotion");
  const completed = spawnSync(
    remotionBinary,
    [
      "render",
      ENTRY_POINT,
      "Demo",
      outputFile,
      `--props=${timelineFile}`,
      `--scale=${scale}`,
      // Limited-range BT.709, tagged as such: what players and upload sites expect. The default
      // writes full-range color (yuvj420p), which some players show washed out.
      "--color-space=bt709",
      "--log=warn",
    ],
    { cwd: DEMO_DIRECTORY, stdio: "inherit" },
  );
  if (completed.error !== undefined) {
    throw new RenderError(
      `could not start Remotion (${completed.error.message}); run \`make demo-bootstrap\` first`,
    );
  }
  if (completed.status !== 0) {
    throw new RenderError(`the render failed (exit ${completed.status ?? "unknown"})`);
  }
};
