/**
 * Check a rendered file against what the timeline says it should be. A cut that is the wrong size,
 * the wrong length, or without the audio track its narration needs, fails here, not after it has
 * been uploaded.
 */
import { execFileSync } from "node:child_process";
import { closeSync, openSync, readSync, statSync } from "node:fs";
import type { Timeline } from "../catalog/schemas";
import { type Loudness, TARGET_LUFS } from "./finish";
import { timelineSeconds } from "./timeline";

export class ProbeError extends Error {}

type ProbedStream = {
  codec_type?: string;
  width?: number;
  height?: number;
  avg_frame_rate?: string;
  pix_fmt?: string;
};
type ProbeResult = { streams?: ProbedStream[]; format?: { duration?: string } };

/** How far the file's length may be from the timeline's: one frame of rounding and the encoder's tail. */
const DURATION_TOLERANCE_SECONDS = 0.25;

export const probe = (videoFile: string): ProbeResult => {
  try {
    const probeOutput = execFileSync(
      "ffprobe",
      ["-v", "error", "-print_format", "json", "-show_streams", "-show_format", videoFile],
      { encoding: "utf8" },
    );
    return JSON.parse(probeOutput) as ProbeResult;
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new ProbeError(`ffprobe could not read ${videoFile}: ${reason}`);
  }
};

/** Every way the file differs from the timeline; empty when it matches. */
export const verificationProblems = (
  probeResult: ProbeResult,
  timeline: Timeline,
  scale: number,
): string[] => {
  const problems: string[] = [];
  const videoStream = probeResult.streams?.find((stream) => stream.codec_type === "video");
  const audioStream = probeResult.streams?.find((stream) => stream.codec_type === "audio");

  if (videoStream === undefined) {
    problems.push("the file has no video stream");
  } else {
    const expectedWidth = Math.round(timeline.width * scale);
    const expectedHeight = Math.round(timeline.height * scale);
    if (videoStream.width !== expectedWidth || videoStream.height !== expectedHeight) {
      problems.push(
        `the picture is ${videoStream.width}x${videoStream.height}, expected ${expectedWidth}x${expectedHeight}`,
      );
    }
    const expectedFrameRate = `${timeline.frames_per_second}/1`;
    if (videoStream.avg_frame_rate !== expectedFrameRate) {
      problems.push(
        `the frame rate is ${videoStream.avg_frame_rate}, expected ${expectedFrameRate}`,
      );
    }
    if (videoStream.pix_fmt !== "yuv420p") {
      problems.push(
        `the pixel format is ${videoStream.pix_fmt}, expected yuv420p (what players expect)`,
      );
    }
  }

  const hasNarration = timeline.scenes.some((timedScene) => timedScene.cues.length > 0);
  if (hasNarration && audioStream === undefined) {
    problems.push("the timeline has narration but the file has no audio stream");
  }

  const fileSeconds = Number(probeResult.format?.duration);
  const expectedSeconds = timelineSeconds(timeline);
  if (!Number.isFinite(fileSeconds)) {
    problems.push("the file's length could not be read");
  } else if (Math.abs(fileSeconds - expectedSeconds) > DURATION_TOLERANCE_SECONDS) {
    problems.push(
      `the file is ${fileSeconds.toFixed(2)} s but the timeline is ${expectedSeconds.toFixed(2)} s`,
    );
  }
  return problems;
};

/** How far from the target the finished loudness may be, and the highest peak allowed. */
const LOUDNESS_TOLERANCE_LUFS = 1;
const MAX_TRUE_PEAK_DBTP = -1;

/**
 * True when the file's index (the `moov` box) comes before its media (`mdat`), so a player can start
 * before the whole file has arrived.
 */
export const startsFast = (videoFile: string): boolean => {
  const fileBytes = statSync(videoFile).size;
  const fileDescriptor = openSync(videoFile, "r");
  try {
    const boxHeader = Buffer.alloc(16);
    let boxOffset = 0;
    while (boxOffset + 8 <= fileBytes) {
      readSync(fileDescriptor, boxHeader, 0, 16, boxOffset);
      const boxType = boxHeader.toString("ascii", 4, 8);
      if (boxType === "moov") {
        return true;
      }
      if (boxType === "mdat") {
        return false;
      }
      const declaredBytes = boxHeader.readUInt32BE(0);
      // A size of 1 means the real size is the 64-bit number that follows; 0 means "to the end".
      const boxBytes = declaredBytes === 1 ? Number(boxHeader.readBigUInt64BE(8)) : declaredBytes;
      if (boxBytes < 8) {
        return false;
      }
      boxOffset += boxBytes;
    }
    return false;
  } finally {
    closeSync(fileDescriptor);
  }
};

/** Problems with a finished file beyond its picture and length: captions, loudness, fast start. */
export const finishedProblems = (
  probeResult: ProbeResult,
  videoFile: string,
  loudness: Loudness | undefined,
): string[] => {
  const problems: string[] = [];
  if (!probeResult.streams?.some((stream) => stream.codec_type === "subtitle")) {
    problems.push("the file has no caption track");
  }
  if (!startsFast(videoFile)) {
    problems.push("the file's index is at the end; it will not start playing until fully loaded");
  }
  if (loudness !== undefined) {
    if (Math.abs(loudness.integratedLufs - TARGET_LUFS) > LOUDNESS_TOLERANCE_LUFS) {
      problems.push(
        `the loudness is ${loudness.integratedLufs.toFixed(1)} LUFS; the target is ${TARGET_LUFS} LUFS`,
      );
    }
    if (loudness.truePeakDbtp > MAX_TRUE_PEAK_DBTP) {
      problems.push(
        `the true peak is ${loudness.truePeakDbtp.toFixed(1)} dBTP; it must stay at or under ${MAX_TRUE_PEAK_DBTP}`,
      );
    }
  }
  return problems;
};
