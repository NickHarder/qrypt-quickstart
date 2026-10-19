import type { Brand } from "../src/catalog/schemas";

export const exampleBrand: Brand = {
  colors: {
    background: "#0B1220",
    surface: "#152033",
    text: "#F5F7FA",
    muted: "#B8C2D1",
    accent: "#7CC4FF",
  },
  fonts: { heading: "Helvetica", body: "Helvetica", mono: "Menlo" },
  voice: {
    name: "Kore",
    model: "gemini-3.8-flash-tts",
    style: "calm",
    draft_voice: "Samantha",
    draft_words_per_minute: 178,
    kokoro_voice: "af_heart",
  },
};
