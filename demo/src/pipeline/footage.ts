/**
 * Fit a recorded beat into its scene.
 *
 * The scene's length is set by its narration. The footage is made to fit that, by these rules:
 * - footage shorter than the scene plays in real time, and its last frame is held;
 * - footage longer than the scene is sped up, at most MAX_PLAYBACK_RATE;
 * - footage too long even for that is an error: trim the beat, split the scene, or say more.
 * The voice is never sped up, and footage is never slowed down.
 */
import { z } from "zod";
import {
  type BeatRow,
  beatRowSchema,
  type FootagePlacement,
  type KeyPhrase,
  type ScreenRecordingProps,
} from "../catalog/schemas";
import { loadKeptFile } from "./storyboard";

/** Past this, sped-up footage stops reading as the product and starts reading as a blur. */
export const MAX_PLAYBACK_RATE = 4;

/** A beat that cannot be fitted into its scene, or that was never recorded. */
export class FootageError extends Error {}

export type FootageFit = { playbackRate: number; playedSeconds: number; holdSeconds: number };

export const fitFootage = (footageSeconds: number, sceneSeconds: number): FootageFit => {
  if (footageSeconds <= sceneSeconds) {
    return {
      playbackRate: 1,
      playedSeconds: footageSeconds,
      holdSeconds: sceneSeconds - footageSeconds,
    };
  }
  const playbackRate = footageSeconds / sceneSeconds;
  if (playbackRate > MAX_PLAYBACK_RATE) {
    const shortestSceneSeconds = footageSeconds / MAX_PLAYBACK_RATE;
    throw new FootageError(
      `the footage is ${footageSeconds.toFixed(1)} s for a ${sceneSeconds.toFixed(1)} s scene; ` +
        `even at ${MAX_PLAYBACK_RATE}x it needs ${shortestSceneSeconds.toFixed(1)} s. ` +
        "Trim the beat, split the scene, or give it more to say",
    );
  }
  return { playbackRate, playedSeconds: sceneSeconds, holdSeconds: 0 };
};

export const loadBeatRows = (beatsFile: string): BeatRow[] =>
  loadKeptFile(beatsFile, z.array(beatRowSchema), []);

/**
 * Place the beat a ScreenRecording scene names into a scene of the given number of frames. What plays
 * is the take's own recording, the file the honesty check looks up, so nothing else can stand in for it.
 */
export const placeFootage = (
  sceneId: string,
  props: Pick<ScreenRecordingProps, "take" | "beat" | "trim"> & {
    key_phrases?: readonly KeyPhrase[];
  },
  beatRows: readonly BeatRow[],
  sceneFrames: number,
  framesPerSecond: number,
): FootagePlacement => {
  const sceneSeconds = sceneFrames / framesPerSecond;
  const beatRow = beatRows.find((row) => row.take === props.take && row.key === props.beat);
  if (beatRow === undefined) {
    throw new FootageError(
      `scene "${sceneId}" shows beat "${props.beat}" of take "${props.take}", which has not been ` +
        "recorded; run `make demo-capture`",
    );
  }
  const sourceStartSeconds = beatRow.start + (props.trim?.head_seconds ?? 0);
  const sourceEndSeconds = beatRow.end - (props.trim?.tail_seconds ?? 0);
  const footageSeconds = sourceEndSeconds - sourceStartSeconds;
  if (footageSeconds <= 0) {
    throw new FootageError(
      `scene "${sceneId}" trims beat "${props.beat}" of take "${props.take}" down to nothing`,
    );
  }
  let fit: FootageFit;
  try {
    fit = fitFootage(footageSeconds, sceneSeconds);
  } catch (error) {
    if (error instanceof FootageError) {
      throw new FootageError(`scene "${sceneId}": ${error.message}`);
    }
    throw error;
  }
  const lateKeyPhrase = props.key_phrases?.find(
    (keyPhrase) => Math.round(keyPhrase.at_seconds * framesPerSecond) >= sceneFrames,
  );
  if (lateKeyPhrase !== undefined) {
    throw new FootageError(
      `scene "${sceneId}" shows the key phrase "${lateKeyPhrase.text}" at ` +
        `${lateKeyPhrase.at_seconds} s, after the scene has ended at ${sceneSeconds.toFixed(1)} s`,
    );
  }
  const playedFrames = Math.min(
    sceneFrames,
    Math.max(1, Math.round(fit.playedSeconds * framesPerSecond)),
  );
  return {
    video_file: `media/takes/${props.take}.webm`,
    source_start_frame: Math.round(sourceStartSeconds * framesPerSecond),
    playback_rate: fit.playbackRate,
    played_frames: playedFrames,
    hold_frames: sceneFrames - playedFrames,
  };
};
