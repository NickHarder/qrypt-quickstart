import { existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parseStoryboard } from "../src/pipeline/storyboard";
import { createEspeakProvider } from "../src/pipeline/voice/espeak";
import {
  dollarsPerTenSeconds,
  estimateVoiceCost,
  isSuspectRead,
} from "../src/pipeline/voice/estimate";
import {
  cachedFinalVoice,
  FinalVoiceError,
  finalVoiceIsNamed,
  finalVoiceName,
  paidFinalVoice,
} from "../src/pipeline/voice/final";
import {
  createGeminiProvider,
  GeminiVoiceError,
  geminiApiKey,
  type SpeechClient,
  type SpeechRequest,
} from "../src/pipeline/voice/gemini";
import { createKokoroProvider } from "../src/pipeline/voice/kokoro";
import { createSayProvider } from "../src/pipeline/voice/say";
import { createSilentProvider } from "../src/pipeline/voice/silent";
import { linesNeedingVoice, voiceLines } from "../src/pipeline/voice/voiceLines";
import { silentWav } from "../src/pipeline/wav";
import { exampleBrand } from "./fixtures";

const storyboardWithLines = (lines: unknown[]) =>
  parseStoryboard({
    title: "Test",
    target_seconds: { min: 1, max: 600 },
    scenes: [{ id: "one", component: "TitleCard", props: { title: "One" }, lines }],
  });

/** Stands in for the Gemini API: remembers every request and answers with two seconds of silence. */
const recordingSpeechClient = (): { client: SpeechClient; requests: SpeechRequest[] } => {
  const requests: SpeechRequest[] = [];
  return {
    requests,
    client: {
      speak: async (request) => {
        requests.push(request);
        return silentWav(2);
      },
    },
  };
};

const scratchMedia = (): string => mkdtempSync(path.join(tmpdir(), "demo-voice-"));

describe("the Gemini provider", () => {
  it("sends one request per line with the model, the voice, the style and the exact text", async () => {
    const { client, requests } = recordingSpeechClient();
    const provider = createGeminiProvider(client, "gemini-3.8-flash-tts", "Kore");
    const storyboard = storyboardWithLines([
      { key: "a", text: "First line." },
      { key: "b", text: "Second line.", style: "slower, with weight" },
    ]);
    const mediaDirectory = scratchMedia();
    const voiceRun = await voiceLines(storyboard, exampleBrand, provider, mediaDirectory);

    expect(requests).toEqual([
      {
        model: "gemini-3.8-flash-tts",
        voice: "Kore",
        style: exampleBrand.voice.style,
        text: "First line.",
      },
      {
        model: "gemini-3.8-flash-tts",
        voice: "Kore",
        style: "slower, with weight",
        text: "Second line.",
      },
    ]);
    expect(voiceRun.synthesizedKeys).toEqual(["a", "b"]);
    expect(voiceRun.voicedLinesByKey.get("a")?.audioFile).toBe("media/voice/gemini/a.wav");
    expect(voiceRun.voicedLinesByKey.get("a")?.durationSeconds).toBeCloseTo(2, 3);
    expect(existsSync(path.join(mediaDirectory, "voice", "gemini", "b.wav"))).toBe(true);
  });

  it("pays for a line once: a second run sends nothing", async () => {
    const { client, requests } = recordingSpeechClient();
    const provider = createGeminiProvider(client, "gemini-3.8-flash-tts", "Kore");
    const storyboard = storyboardWithLines([{ key: "a", text: "Only line." }]);
    const mediaDirectory = scratchMedia();
    await voiceLines(storyboard, exampleBrand, provider, mediaDirectory);
    const secondRun = await voiceLines(storyboard, exampleBrand, provider, mediaDirectory);
    expect(requests).toHaveLength(1);
    expect(secondRun.synthesizedKeys).toEqual([]);
  });

  it("keeps what a run paid for when a later line fails", async () => {
    const { client, requests } = recordingSpeechClient();
    const failingOnTheLastLine: SpeechClient = {
      speak: async (request) => {
        if (request.text === "Third line.") {
          throw new GeminiVoiceError("the API stopped answering");
        }
        return client.speak(request);
      },
    };
    const storyboard = storyboardWithLines([
      { key: "a", text: "First line." },
      { key: "b", text: "Second line." },
      { key: "c", text: "Third line." },
    ]);
    const mediaDirectory = scratchMedia();
    await expect(
      voiceLines(
        storyboard,
        exampleBrand,
        createGeminiProvider(failingOnTheLastLine, "m", "Kore"),
        mediaDirectory,
      ),
    ).rejects.toThrow(GeminiVoiceError);
    const secondRun = await voiceLines(
      storyboard,
      exampleBrand,
      createGeminiProvider(client, "m", "Kore"),
      mediaDirectory,
    );
    expect(secondRun.synthesizedKeys).toEqual(["c"]);
    expect(requests.map((request) => request.text)).toEqual([
      "First line.",
      "Second line.",
      "Third line.",
    ]);
  });

  it("voices again only the line whose text changed", async () => {
    const { client, requests } = recordingSpeechClient();
    const provider = createGeminiProvider(client, "gemini-3.8-flash-tts", "Kore");
    const mediaDirectory = scratchMedia();
    const before = storyboardWithLines([
      { key: "a", text: "Stays the same." },
      { key: "b", text: "Will change." },
    ]);
    await voiceLines(before, exampleBrand, provider, mediaDirectory);
    const after = storyboardWithLines([
      { key: "a", text: "Stays the same." },
      { key: "b", text: "Has changed." },
    ]);
    expect(
      linesNeedingVoice(after, exampleBrand, provider, mediaDirectory).map((line) => line.key),
    ).toEqual(["b"]);
    await voiceLines(after, exampleBrand, provider, mediaDirectory);
    expect(requests.map((request) => request.text)).toEqual([
      "Stays the same.",
      "Will change.",
      "Has changed.",
    ]);
  });

  it("voices every line again when the voice changes", async () => {
    const { client } = recordingSpeechClient();
    const mediaDirectory = scratchMedia();
    const storyboard = storyboardWithLines([{ key: "a", text: "A line." }]);
    await voiceLines(
      storyboard,
      exampleBrand,
      createGeminiProvider(client, "m", "Kore"),
      mediaDirectory,
    );
    const otherVoice = createGeminiProvider(client, "m", "Puck");
    expect(linesNeedingVoice(storyboard, exampleBrand, otherVoice, mediaDirectory)).toHaveLength(1);
  });

  it("keeps draft clips and final clips apart", async () => {
    const mediaDirectory = scratchMedia();
    const storyboard = storyboardWithLines([{ key: "a", text: "A line." }]);
    await voiceLines(storyboard, exampleBrand, createSilentProvider(), mediaDirectory);
    const { client } = recordingSpeechClient();
    const gemini = createGeminiProvider(client, "m", "Kore");
    // A draft clip never counts as a final one.
    expect(linesNeedingVoice(storyboard, exampleBrand, gemini, mediaDirectory)).toHaveLength(1);
  });

  it("says how to get a key when there is none", () => {
    expect(() => geminiApiKey({})).toThrow(GeminiVoiceError);
    expect(() => geminiApiKey({ GEMINI_API_KEY: "  " })).toThrow(/Google AI Studio/);
    expect(geminiApiKey({ GEMINI_API_KEY: " abc " })).toBe("abc");
  });
});

describe("pronunciations", () => {
  it("sends the voice the spoken form of a word, whole words only, and keeps the line as written", async () => {
    const { client, requests } = recordingSpeechClient();
    const provider = createGeminiProvider(client, "gemini-3.8-flash-tts", "Orus");
    const brand = {
      ...exampleBrand,
      voice: { ...exampleBrand.voice, pronunciations: { Qrypt: "Crypt" } },
    };
    const storyboard = storyboardWithLines([
      { key: "a", text: "Qrypt's API, and Qrypt quantum entropy, not Qrypts or qrypt.com." },
    ]);
    await voiceLines(storyboard, brand, provider, scratchMedia());
    expect(requests[0]?.text).toBe(
      "Crypt's API, and Crypt quantum entropy, not Qrypts or qrypt.com.",
    );
    expect(storyboard.scenes[0]?.lines[0]?.text).toContain("Qrypt's API");
  });

  it("voices a line again when its pronunciation changes", async () => {
    const { client, requests } = recordingSpeechClient();
    const provider = createGeminiProvider(client, "gemini-3.8-flash-tts", "Orus");
    const storyboard = storyboardWithLines([{ key: "a", text: "Qrypt." }]);
    const mediaDirectory = scratchMedia();
    await voiceLines(storyboard, exampleBrand, provider, mediaDirectory);
    const respelled = {
      ...exampleBrand,
      voice: { ...exampleBrand.voice, pronunciations: { Qrypt: "Crypt" } },
    };
    const secondRun = await voiceLines(storyboard, respelled, provider, mediaDirectory);
    expect(secondRun.synthesizedKeys).toEqual(["a"]);
    expect(requests.map((request) => request.text)).toEqual(["Qrypt.", "Crypt."]);
  });
});

describe("the cost estimate", () => {
  const lines =
    storyboardWithLines([{ key: "a", text: "one two three four five six seven eight nine ten" }])
      .scenes[0]?.lines ?? [];

  it("prices audio by the published rate for the date", () => {
    expect(dollarsPerTenSeconds("gemini-3.8-flash-tts", new Date("2026-10-02"))).toBe(0.00225);
    expect(dollarsPerTenSeconds("gemini-3.8-flash-tts", new Date("2027-01-01"))).toBe(0.0045);
    expect(dollarsPerTenSeconds("gemini-3.8-flash-lite-tts", new Date("2026-10-02"))).toBe(0.0015);
  });

  const geminiWith = (model: string) =>
    createGeminiProvider(recordingSpeechClient().client, model, "Kore");

  it("estimates seconds from the words and dollars from the voice's own price", () => {
    const estimate = estimateVoiceCost(
      lines,
      geminiWith("gemini-3.8-flash-tts"),
      new Date("2026-10-02"),
    );
    expect(estimate.lineCount).toBe(1);
    expect(estimate.seconds).toBeCloseTo(4.4, 5);
    expect(estimate.dollars).toBeCloseTo(0.00099, 5);
  });

  it("does not invent a price for a model it has no price for", () => {
    expect(
      estimateVoiceCost(lines, geminiWith("some-new-model"), new Date("2026-10-02")).dollars,
    ).toBeUndefined();
  });

  it("prices every free voice at nothing", () => {
    for (const provider of [
      createSilentProvider(),
      createSayProvider("Samantha", 180),
      createEspeakProvider("en-us", 180),
      createKokoroProvider("af_heart"),
    ]) {
      expect(estimateVoiceCost(lines, provider, new Date("2026-10-02")).dollars).toBe(0);
    }
  });

  it("flags a read that is far too long or far too short for its text", () => {
    const text = "one two three four five six seven eight nine ten";
    expect(isSuspectRead(text, 4.5)).toBe(false);
    expect(isSuspectRead(text, 15)).toBe(true);
    expect(isSuspectRead(text, 1)).toBe(true);
  });
});

describe("the espeak-ng draft voice", () => {
  it("keeps its clips apart from the other voices, and changes them when its settings change", () => {
    const provider = createEspeakProvider("en-us", 180);
    expect(provider.name).toBe("espeak");
    expect(provider.fingerprint()).not.toBe(createEspeakProvider("en-us", 160).fingerprint());
    expect(provider.fingerprint()).not.toBe(createEspeakProvider("en-gb", 180).fingerprint());
  });
});

describe("the Kokoro voice", () => {
  it("keeps its clips apart from the other voices, and changes them when the voice changes", () => {
    const provider = createKokoroProvider("af_heart");
    expect(provider.name).toBe("kokoro");
    expect(provider.fingerprint()).toContain("af_heart");
    expect(provider.fingerprint()).not.toBe(createKokoroProvider("bm_george").fingerprint());
  });
});

describe("the final voice", () => {
  it("is the one DEMO_VOICE_PROVIDER names", () => {
    expect(finalVoiceName({ DEMO_VOICE_PROVIDER: "gemini" })).toBe("gemini");
    expect(finalVoiceName({ DEMO_VOICE_PROVIDER: "kokoro", GEMINI_API_KEY: "key" })).toBe("kokoro");
    expect(finalVoiceIsNamed({ DEMO_VOICE_PROVIDER: "kokoro" })).toBe(true);
  });

  it("is Gemini when a key is set and Kokoro when none is, where nothing is named", () => {
    expect(finalVoiceName({})).toBe("kokoro");
    expect(finalVoiceName({ DEMO_VOICE_PROVIDER: " ", GEMINI_API_KEY: " " })).toBe("kokoro");
    expect(finalVoiceName({ GEMINI_API_KEY: "key" })).toBe("gemini");
    expect(finalVoiceIsNamed({ GEMINI_API_KEY: "key" })).toBe(false);
  });

  it("refuses a voice nobody has wired in, and says which ones there are", () => {
    expect(() => finalVoiceName({ DEMO_VOICE_PROVIDER: "elevenlabs" })).toThrow(FinalVoiceError);
    expect(() => finalVoiceName({ DEMO_VOICE_PROVIDER: "elevenlabs" })).toThrow(/gemini, kokoro/);
  });

  it("reads Kokoro's cache the same way, and makes its clips without a key or a price", async () => {
    const cached = cachedFinalVoice("kokoro", exampleBrand);
    expect(cached.name).toBe("kokoro");
    expect(cached.dollarsPerTenSeconds(new Date())).toBe(0);
    await expect(
      cached.synthesize(
        { key: "a", text: "A line.", style: "" },
        path.join(scratchMedia(), "a.wav"),
      ),
    ).rejects.toThrow(/make demo-voice/);
    expect(paidFinalVoice("kokoro", exampleBrand, {}).fingerprint()).toBe(cached.fingerprint());
  });

  it("reads its cache without a key, and never pays from it", async () => {
    const provider = cachedFinalVoice("gemini", exampleBrand);
    expect(provider.name).toBe("gemini");
    await expect(
      provider.synthesize(
        { key: "a", text: "A line.", style: "" },
        path.join(scratchMedia(), "a.wav"),
      ),
    ).rejects.toThrow(/make demo-voice/);
  });

  it("needs its key before it can pay for a line", () => {
    expect(() => paidFinalVoice("gemini", exampleBrand, {})).toThrow(GeminiVoiceError);
    expect(paidFinalVoice("gemini", exampleBrand, { GEMINI_API_KEY: "key" }).name).toBe("gemini");
  });
});
