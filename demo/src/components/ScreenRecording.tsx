/**
 * A beat of a real recording of the product. The pipeline decides how it is fitted to the scene
 * (where it starts, how fast it plays, how long its last frame is held); this only draws that, and
 * any key phrases the storyboard puts over it.
 */
import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  Freeze,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { FootagePlacement, KeyPhrase } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

type ScreenRecordingViewProps = {
  sceneId: string;
  /** Missing only if the timeline was built without the footage step, which the pipeline does not allow. */
  footage: FootagePlacement | undefined;
  keyPhrases: KeyPhrase[];
};

const KeyPhrasePill = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const brand = useBrand();
  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        bottom: 150,
        padding: "20px 36px",
        borderRadius: 16,
        backgroundColor: brand.colors.background,
        borderLeft: `10px solid ${brand.colors.accent}`,
        color: brand.colors.text,
        fontFamily: brand.fonts.heading,
        fontSize: 52,
        fontWeight: 700,
        opacity: interpolate(
          frame,
          [0, 0.3 * fps, durationInFrames - 0.3 * fps, durationInFrames],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        ),
      }}
    >
      {text}
    </div>
  );
};

export const ScreenRecording = ({ sceneId, footage, keyPhrases }: ScreenRecordingViewProps) => {
  const { fps } = useVideoConfig();
  const brand = useBrand();
  if (footage === undefined) {
    throw new Error(
      `scene "${sceneId}" is a ScreenRecording with no footage placed on the timeline`,
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.background }}>
      <Sequence name={`${sceneId} footage`} durationInFrames={footage.played_frames}>
        <Video
          src={staticFile(footage.video_file)}
          trimBefore={footage.source_start_frame}
          playbackRate={footage.playback_rate}
          muted
          premountFor={fps}
          style={{ width: "100%", height: "100%" }}
          objectFit="contain"
        />
      </Sequence>
      {footage.hold_frames === 0 ? null : (
        <Sequence name={`${sceneId} hold`} from={footage.played_frames}>
          {/* The narration is longer than the footage: hold the last frame rather than cut away. */}
          <Freeze frame={Math.max(0, footage.played_frames - 1)}>
            <Video
              src={staticFile(footage.video_file)}
              trimBefore={footage.source_start_frame}
              playbackRate={footage.playback_rate}
              muted
              style={{ width: "100%", height: "100%" }}
              objectFit="contain"
            />
          </Freeze>
        </Sequence>
      )}
      {keyPhrases.map((keyPhrase) => (
        <Sequence
          key={`${keyPhrase.at_seconds}-${keyPhrase.text}`}
          name={`phrase: ${keyPhrase.text}`}
          from={Math.round(keyPhrase.at_seconds * fps)}
          durationInFrames={Math.max(1, Math.round(keyPhrase.for_seconds * fps))}
        >
          <KeyPhrasePill text={keyPhrase.text} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
