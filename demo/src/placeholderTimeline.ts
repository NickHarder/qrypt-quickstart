/**
 * What the Studio shows before a real timeline exists. A render always passes its own timeline with
 * `--props`, so this is never what ends up in a video.
 */
import type { Timeline } from "./catalog/schemas";

export const placeholderTimeline: Timeline = {
  title: "No timeline yet",
  frames_per_second: 30,
  width: 1920,
  height: 1080,
  duration_in_frames: 90,
  voice_provider: "none",
  poster_frame: 0,
  brand: {
    colors: {
      background: "#0B1220",
      surface: "#152033",
      text: "#F5F7FA",
      muted: "#B8C2D1",
      accent: "#7CC4FF",
    },
    fonts: {
      heading: "Helvetica, Arial, sans-serif",
      body: "Helvetica, Arial, sans-serif",
      mono: "Menlo, monospace",
    },
    voice: {
      name: "Kore",
      model: "gemini-3.8-flash-tts",
      style: "calm and clear",
      draft_voice: "Samantha",
      draft_words_per_minute: 178,
      kokoro_voice: "af_heart",
    },
  },
  scenes: [
    {
      scene: {
        id: "placeholder",
        component: "TitleCard",
        props: {
          title: "No timeline yet",
          subtitle: "Run `make demo-draft`, then open the Studio with work/timeline.json as props.",
        },
        lines: [],
        min_seconds: 3,
      },
      from_frame: 0,
      duration_in_frames: 90,
      cues: [],
    },
  ],
};
