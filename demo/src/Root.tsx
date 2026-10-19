/**
 * Registers the one composition. Its length, size and frame rate come from the timeline passed as
 * props (`--props=work/timeline.json`), which the pipeline computes from the measured audio.
 */
import type { CalculateMetadataFunction } from "remotion";
import { Composition } from "remotion";
import { type Timeline, timelineSchema } from "./catalog/schemas";
import { Demo } from "./Demo";
import { placeholderTimeline } from "./placeholderTimeline";

const calculateMetadata: CalculateMetadataFunction<Timeline> = ({ props }) => ({
  durationInFrames: props.duration_in_frames,
  fps: props.frames_per_second,
  width: props.width,
  height: props.height,
});

export const Root = () => (
  <Composition
    id="Demo"
    component={Demo}
    schema={timelineSchema}
    defaultProps={placeholderTimeline}
    calculateMetadata={calculateMetadata}
    durationInFrames={placeholderTimeline.duration_in_frames}
    fps={placeholderTimeline.frames_per_second}
    width={placeholderTimeline.width}
    height={placeholderTimeline.height}
  />
);
