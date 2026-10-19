/**
 * How loud the music is at each frame: lowered under every spoken line, with short ramps, and faded
 * in at the start and out at the end. The curve is computed from the timeline, so it always follows
 * the narration exactly.
 */
import type { Timeline } from "./catalog/schemas";

const RAMP_SECONDS = 0.4;
const FADE_IN_SECONDS = 1.5;
const FADE_OUT_SECONDS = 3;

export type FrameWindow = { startFrame: number; endFrame: number };

/** When each line is being said, in frames from the start of the video. */
export const narrationWindows = (timeline: Timeline): FrameWindow[] =>
  timeline.scenes.flatMap((timedScene) =>
    timedScene.cues.map((cue) => ({
      startFrame: timedScene.from_frame + cue.from_frame,
      endFrame: timedScene.from_frame + cue.from_frame + cue.duration_in_frames,
    })),
  );

export type MusicLevels = { volume: number; volumeUnderVoice: number };

export const musicVolumeAtFrame = (
  frame: number,
  windows: readonly FrameWindow[],
  levels: MusicLevels,
  framesPerSecond: number,
  totalFrames: number,
): number => {
  const rampFrames = RAMP_SECONDS * framesPerSecond;
  // 1 while a line is spoken, 0 well away from any line, and in between on the ramps around a line.
  const voicePresence = windows.reduce((strongestPresence, window) => {
    const framesOutside = Math.max(window.startFrame - frame, frame - window.endFrame, 0);
    return Math.max(strongestPresence, 1 - Math.min(1, framesOutside / rampFrames));
  }, 0);
  const levelForVoice = levels.volume + (levels.volumeUnderVoice - levels.volume) * voicePresence;
  const fadeIn = Math.min(1, frame / (FADE_IN_SECONDS * framesPerSecond));
  const fadeOut = Math.min(1, (totalFrames - frame) / (FADE_OUT_SECONDS * framesPerSecond));
  return Math.max(0, levelForVoice * fadeIn * Math.max(0, fadeOut));
};
