/**
 * Finish a rendered cut: bring the audio to the target loudness, add the captions as a track a viewer
 * can switch on, and put the index at the front of the file so it starts playing before it has fully
 * loaded. The picture is copied, not encoded again.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import path from "node:path";

/** Integrated loudness for speech-led video on the web, and the ceiling that keeps peaks from clipping. */
export const TARGET_LUFS = -16;
export const TARGET_TRUE_PEAK_DBTP = -1.5;
const TARGET_LOUDNESS_RANGE = 11;
/** Below this the track is treated as silence: there is nothing to normalise. */
const SILENCE_LUFS = -60;

export class FinishError extends Error {}

export type Loudness = { integratedLufs: number; truePeakDbtp: number };

type LoudnormMeasurement = {
  input_i: string;
  input_tp: string;
  input_lra: string;
  input_thresh: string;
  target_offset: string;
};

const runFfmpeg = (ffmpegArguments: string[]): string => {
  const completed = spawnSync("ffmpeg", ["-hide_banner", "-nostdin", "-y", ...ffmpegArguments], {
    encoding: "utf8",
  });
  if (completed.error !== undefined) {
    throw new FinishError(`could not start ffmpeg: ${completed.error.message}`);
  }
  if (completed.status !== 0) {
    throw new FinishError(`ffmpeg failed:\n${completed.stderr.split("\n").slice(-12).join("\n")}`);
  }
  return completed.stderr;
};

const loudnormFilter = `loudnorm=I=${TARGET_LUFS}:TP=${TARGET_TRUE_PEAK_DBTP}:LRA=${TARGET_LOUDNESS_RANGE}`;

/** The poster: frame 0 of a finished cut as a JPEG, the still every platform's thumbnail shows. */
export const extractPoster = (videoFile: string, posterFile: string): void => {
  runFfmpeg(["-i", videoFile, "-frames:v", "1", "-q:v", "2", posterFile]);
};

/** Measure a file's audio the way the normaliser does. */
const measure = (mediaFile: string): LoudnormMeasurement => {
  const ffmpegLog = runFfmpeg([
    "-i",
    mediaFile,
    "-vn",
    "-af",
    `${loudnormFilter}:print_format=json`,
    "-f",
    "null",
    "-",
  ]);
  const measurementJson = ffmpegLog.slice(
    ffmpegLog.lastIndexOf("{"),
    ffmpegLog.lastIndexOf("}") + 1,
  );
  try {
    return JSON.parse(measurementJson) as LoudnormMeasurement;
  } catch {
    throw new FinishError(`could not read the loudness measurement of ${mediaFile}`);
  }
};

export const measureLoudness = (mediaFile: string): Loudness => {
  const measurement = measure(mediaFile);
  return {
    integratedLufs: Number(measurement.input_i),
    truePeakDbtp: Number(measurement.input_tp),
  };
};

export const isSilent = (loudness: Loudness): boolean =>
  !Number.isFinite(loudness.integratedLufs) || loudness.integratedLufs < SILENCE_LUFS;

export type FinishOptions = { renderedFile: string; captionsFile: string; outputFile: string };

/** Normalise, add the caption track, and write the finished file. Returns the loudness before. */
export const finishVideo = ({
  renderedFile,
  captionsFile,
  outputFile,
}: FinishOptions): Loudness => {
  mkdirSync(path.dirname(outputFile), { recursive: true });
  const measurement = measure(renderedFile);
  const before: Loudness = {
    integratedLufs: Number(measurement.input_i),
    truePeakDbtp: Number(measurement.input_tp),
  };
  // Two passes: the second is told what the first measured, so the gain is one steady change and not
  // a compressor riding the level.
  const audioFilter = isSilent(before)
    ? "anull"
    : `${loudnormFilter}:measured_I=${measurement.input_i}:measured_TP=${measurement.input_tp}` +
      `:measured_LRA=${measurement.input_lra}:measured_thresh=${measurement.input_thresh}` +
      `:offset=${measurement.target_offset}:linear=true`;
  runFfmpeg([
    "-i",
    renderedFile,
    "-i",
    captionsFile,
    "-map",
    "0:v:0",
    "-map",
    "0:a:0",
    "-map",
    "1:0",
    "-c:v",
    "copy",
    "-af",
    audioFilter,
    "-c:a",
    "aac",
    "-b:a",
    "160k",
    "-ar",
    "48000",
    "-c:s",
    "mov_text",
    "-metadata:s:s:0",
    "language=eng",
    "-movflags",
    "+faststart",
    outputFile,
  ]);
  return before;
};
