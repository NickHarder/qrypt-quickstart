/**
 * Place every scene and every line in time. This is the one place timing is decided.
 *
 * The rule: audio first. A scene lasts as long as its lines take to say, so the picture never runs
 * out under the voice and the voice is never sped up to fit the picture.
 */
import type { BeatRow, Brand, Cue, Storyboard, TimedScene, Timeline } from "../catalog/schemas";
import type { SceneContent } from "./content";
import { placeFootage } from "./footage";
import { settledSeconds } from "./reading";

export const FRAMES_PER_SECOND = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

/** Silence before a line, unless the line sets its own. */
export const LINE_LEAD_SECONDS = 0.3;
/** Silence after a scene's last line, so the cut does not clip the end of a word. */
export const SCENE_TAIL_SECONDS = 0.5;

/** A storyboard line with no measured audio: the timeline cannot be built without it. */
export class MissingAudioError extends Error {}

/** How one line was voiced: where its clip is, and how long the clip really is. */
export type VoicedLine = { audioFile: string; durationSeconds: number };

/** What the timeline needs besides the words and the audio. */
export type TimelineSources = {
  /** The recorded beats, for ScreenRecording scenes. */
  beatRows?: readonly BeatRow[];
  /** What each scene shows from the repository: code lines, command output. */
  contentBySceneId?: ReadonlyMap<string, SceneContent>;
};

const secondsToFrames = (seconds: number): number => Math.ceil(seconds * FRAMES_PER_SECOND);

/**
 * The poster frame: the scene and second the storyboard names, or the first scene once its text has
 * settled; never past the end of its scene.
 */
export const posterFrameOf = (
  storyboard: Storyboard,
  timedScenes: readonly TimedScene[],
): number => {
  const named = storyboard.poster;
  const timedScene =
    named === undefined
      ? timedScenes[0]
      : timedScenes.find((candidate) => candidate.scene.id === named.scene);
  if (timedScene === undefined) {
    return 0;
  }
  const secondsIntoScene = named?.at_seconds ?? settledSeconds(timedScene.scene);
  const frameIntoScene = Math.min(
    timedScene.duration_in_frames - 1,
    Math.round(secondsIntoScene * FRAMES_PER_SECOND),
  );
  return timedScene.from_frame + Math.max(0, frameIntoScene);
};

export const buildTimeline = (
  storyboard: Storyboard,
  brand: Brand,
  voicedLinesByKey: ReadonlyMap<string, VoicedLine>,
  voiceProvider: string,
  sources: TimelineSources = {},
): Timeline => {
  const beatRows = sources.beatRows ?? [];
  let nextSceneStartFrame = 0;
  const timedScenes: TimedScene[] = storyboard.scenes.map((scene) => {
    // Each length is put in whole frames before it is added, so no line starts before the one before
    // it has ended, and the footage fills exactly the frames its scene has.
    let framesIntoScene = 0;
    const cues: Cue[] = scene.lines.map((line) => {
      const voicedLine = voicedLinesByKey.get(line.key);
      if (voicedLine === undefined) {
        throw new MissingAudioError(
          `line "${line.key}" in scene "${scene.id}" has no audio; voice it before building the timeline`,
        );
      }
      framesIntoScene += secondsToFrames(line.pause_before_seconds ?? LINE_LEAD_SECONDS);
      const cueStartFrame = framesIntoScene;
      const cueFrames = Math.max(1, secondsToFrames(voicedLine.durationSeconds));
      framesIntoScene += cueFrames;
      return {
        key: line.key,
        text: line.text,
        audio_file: voicedLine.audioFile,
        from_frame: cueStartFrame,
        duration_in_frames: cueFrames,
      };
    });
    const spokenFrames =
      scene.lines.length > 0 ? framesIntoScene + secondsToFrames(SCENE_TAIL_SECONDS) : 0;
    const sceneDurationInFrames = Math.max(
      1,
      spokenFrames,
      secondsToFrames(scene.min_seconds ?? 0),
    );
    const timedScene: TimedScene = {
      scene,
      from_frame: nextSceneStartFrame,
      duration_in_frames: sceneDurationInFrames,
      cues,
      ...(scene.component === "ScreenRecording"
        ? {
            footage: placeFootage(
              scene.id,
              scene.props,
              beatRows,
              sceneDurationInFrames,
              FRAMES_PER_SECOND,
            ),
          }
        : {}),
      ...(sources.contentBySceneId?.get(scene.id) ?? {}),
    };
    nextSceneStartFrame += sceneDurationInFrames;
    return timedScene;
  });

  return {
    title: storyboard.title,
    frames_per_second: FRAMES_PER_SECOND,
    width: WIDTH,
    height: HEIGHT,
    duration_in_frames: nextSceneStartFrame,
    voice_provider: voiceProvider,
    poster_frame: posterFrameOf(storyboard, timedScenes),
    brand,
    scenes: timedScenes,
  };
};

/**
 * How long a scene's narration takes, before any footage is fitted to it. Capture uses this to hold
 * each beat on screen until its lines would have been said.
 */
export const spokenSeconds = (
  lines: readonly { key: string; text: string; pause_before_seconds?: number | undefined }[],
  secondsForLine: (line: { key: string; text: string }) => number,
): number =>
  lines.length === 0
    ? 0
    : lines.reduce(
        (total, line) =>
          total + (line.pause_before_seconds ?? LINE_LEAD_SECONDS) + secondsForLine(line),
        SCENE_TAIL_SECONDS,
      );

export const timelineSeconds = (timeline: Timeline): number =>
  timeline.duration_in_frames / timeline.frames_per_second;

/** Problems with the cut's length against the storyboard's target; empty when it fits. */
export const lengthProblems = (storyboard: Storyboard, timeline: Timeline): string[] => {
  const totalSeconds = timelineSeconds(timeline);
  const { min, max } = storyboard.target_seconds;
  if (totalSeconds >= min && totalSeconds <= max) {
    return [];
  }
  const longestScenes = [...timeline.scenes]
    .sort((first, second) => second.duration_in_frames - first.duration_in_frames)
    .slice(0, 5)
    .map(
      (timedScene) =>
        `${timedScene.scene.id} (${(timedScene.duration_in_frames / timeline.frames_per_second).toFixed(1)} s)`,
    );
  const direction = totalSeconds > max ? "over" : "under";
  return [
    `the cut is ${totalSeconds.toFixed(1)} s, ${direction} the target of ${min} to ${max} s; ` +
      `the longest scenes are ${longestScenes.join(", ")}`,
  ];
};
