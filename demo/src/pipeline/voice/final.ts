/**
 * The final voice: the one a finished cut is made with. Two ship: Gemini, which is paid, and Kokoro,
 * which is free and runs on this machine. `DEMO_VOICE_PROVIDER` in the repository's `.env` names one;
 * when it names none, the owner's rule applies: Gemini when `GEMINI_API_KEY` is set, Kokoro
 * otherwise, and Kokoro again when the key does not work. Another voice is a file beside
 * `gemini.ts` that makes a `VoiceProvider` with its own price, and one more entry below.
 */
import type { Brand } from "../../catalog/schemas";
import { createGeminiProvider, createGeminiSpeechClient, geminiApiKey } from "./gemini";
import { createKokoroProvider } from "./kokoro";
import type { VoiceProvider } from "./provider";

/** `DEMO_VOICE_PROVIDER` names something no entry below makes. */
export class FinalVoiceError extends Error {}

/** The reason a final clip is missing: it is made by the paid run, never on the way to a render. */
const MISSING_CLIP = "a final voice clip is missing; run `make demo-voice` first";

/** The same voice, reading its cache only: its clips are made by `make demo-voice`, never on the way to a render. */
const neverSynthesizing = (provider: VoiceProvider): VoiceProvider => ({
  ...provider,
  synthesize: () => Promise.reject(new FinalVoiceError(MISSING_CLIP)),
});

type FinalVoice = {
  /** The voice that reads its cache and never pays: `synthesize` throws. */
  cached: (brand: Brand) => VoiceProvider;
  /** The voice that makes each line: for a paid one, only after the owner has seen the cost and said yes. */
  paid: (brand: Brand, environment: NodeJS.ProcessEnv) => VoiceProvider;
};

const FINAL_VOICES = {
  gemini: {
    cached: (brand) =>
      createGeminiProvider(
        {
          speak: () => Promise.reject(new FinalVoiceError(MISSING_CLIP)),
        },
        brand.voice.model,
        brand.voice.name,
      ),
    paid: (brand, environment) =>
      createGeminiProvider(
        createGeminiSpeechClient(geminiApiKey(environment)),
        brand.voice.model,
        brand.voice.name,
      ),
  },
  kokoro: {
    cached: (brand) => neverSynthesizing(createKokoroProvider(brand.voice.kokoro_voice)),
    paid: (brand) => createKokoroProvider(brand.voice.kokoro_voice),
  },
} as const satisfies Record<string, FinalVoice>;

export type FinalVoiceName = keyof typeof FINAL_VOICES;

/** The free voice: the default without a Gemini key, and where a Gemini key fails. */
export const FREE_FINAL_VOICE: FinalVoiceName = "kokoro";

export const isFinalVoiceName = (name: string): name is FinalVoiceName =>
  Object.hasOwn(FINAL_VOICES, name);

/** Whether the repository's `.env` names the final voice, rather than leaving it to the rule. */
export const finalVoiceIsNamed = (environment: NodeJS.ProcessEnv): boolean =>
  (environment.DEMO_VOICE_PROVIDER?.trim() ?? "") !== "";

/**
 * The final voice `DEMO_VOICE_PROVIDER` names; when it names none, Gemini if `GEMINI_API_KEY` is
 * set and Kokoro if it is not.
 */
export const finalVoiceName = (environment: NodeJS.ProcessEnv): FinalVoiceName => {
  const byKey: FinalVoiceName =
    (environment.GEMINI_API_KEY?.trim() ?? "") === "" ? FREE_FINAL_VOICE : "gemini";
  const named = environment.DEMO_VOICE_PROVIDER?.trim() || byKey;
  if (!isFinalVoiceName(named)) {
    throw new FinalVoiceError(
      `DEMO_VOICE_PROVIDER is "${named}", and the final voices are: ${Object.keys(FINAL_VOICES).join(", ")}`,
    );
  }
  return named;
};

/** The voice's own name within its provider, as `brand.json` sets it: what a clip was read with. */
export const finalVoiceLabel = (voiceName: FinalVoiceName, brand: Brand): string =>
  voiceName === "kokoro" ? brand.voice.kokoro_voice : brand.voice.name;

export const cachedFinalVoice = (voiceName: FinalVoiceName, brand: Brand): VoiceProvider =>
  FINAL_VOICES[voiceName].cached(brand);

export const paidFinalVoice = (
  voiceName: FinalVoiceName,
  brand: Brand,
  environment: NodeJS.ProcessEnv,
): VoiceProvider => FINAL_VOICES[voiceName].paid(brand, environment);
