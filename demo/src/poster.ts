/**
 * The poster frame: the one still every player and platform shows before the video plays. Frame 0
 * of the cut is it, so a thumbnail taken anywhere shows the moment the storyboard chose, and not a
 * fade. Shared by the composition, which draws it, and the pipeline, which names it.
 */
import type { TimedScene, Timeline } from "./catalog/schemas";

export type PosterScene = { timedScene: TimedScene; frameIntoScene: number };

/** The scene the poster frame falls in, and how far into that scene it is. */
export const posterSceneOf = (timeline: Timeline): PosterScene | undefined => {
  const timedScene = timeline.scenes.find(
    (candidate) =>
      candidate.from_frame <= timeline.poster_frame &&
      timeline.poster_frame < candidate.from_frame + candidate.duration_in_frames,
  );
  return timedScene === undefined
    ? undefined
    : { timedScene, frameIntoScene: timeline.poster_frame - timedScene.from_frame };
};
