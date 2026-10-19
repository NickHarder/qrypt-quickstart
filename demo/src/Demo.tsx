/**
 * The composition: every scene at its place in time, with its narration. All timing comes from the
 * timeline. At frame 0 the poster scene is drawn over the opening, at its settled moment, so the
 * thumbnail any player takes from the first frame is the one the storyboard chose.
 */
import { Audio } from "@remotion/media";
import { AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { renderScene } from "./catalog/registry";
import type { Timeline } from "./catalog/schemas";
import { BrandProvider } from "./components/BrandContext";
import { musicVolumeAtFrame, narrationWindows } from "./music";
import { posterSceneOf } from "./poster";

export const Demo = (timeline: Timeline) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const poster = frame === 0 ? posterSceneOf(timeline) : undefined;
  const music = timeline.brand.music;
  const spokenWindows = narrationWindows(timeline);

  return (
    <BrandProvider value={timeline.brand}>
      <AbsoluteFill style={{ backgroundColor: timeline.brand.colors.background }}>
        {timeline.scenes.map((timedScene) => (
          <Sequence
            key={timedScene.scene.id}
            name={timedScene.scene.id}
            from={timedScene.from_frame}
            durationInFrames={timedScene.duration_in_frames}
            premountFor={fps}
          >
            {renderScene(timedScene)}
            {timedScene.cues.map((cue) => (
              <Audio
                key={cue.key}
                name={cue.key}
                src={staticFile(cue.audio_file)}
                from={cue.from_frame}
                premountFor={fps}
              />
            ))}
          </Sequence>
        ))}
        {poster === undefined ? null : (
          <Sequence
            name="poster"
            from={-poster.frameIntoScene}
            durationInFrames={poster.frameIntoScene + 1}
          >
            {renderScene(poster.timedScene)}
          </Sequence>
        )}
        {music === undefined ? null : (
          <Audio
            name="music"
            src={staticFile(`media/${music.file}`)}
            loop
            loopVolumeCurveBehavior="extend"
            volume={(frame) =>
              musicVolumeAtFrame(
                frame,
                spokenWindows,
                { volume: music.volume, volumeUnderVoice: music.volume_under_voice },
                timeline.frames_per_second,
                timeline.duration_in_frames,
              )
            }
          />
        )}
      </AbsoluteFill>
    </BrandProvider>
  );
};
