/**
 * The final voice: Gemini text-to-speech, one request per line.
 *
 * Every call is billed, so the client that makes the calls is only ever built after the owner has seen
 * the estimate and confirmed. The provider talks to a narrow `SpeechClient`, so the tests can stand in
 * for the API.
 */
import { writeFileSync } from "node:fs";
import { GoogleGenAI } from "@google/genai";
import { dollarsPerTenSeconds } from "./estimate";
import type { VoiceProvider, VoiceRequest } from "./provider";

/** The API answered without audio, or there is no key to call it with. */
export class GeminiVoiceError extends Error {}

export type SpeechRequest = { model: string; voice: string; style: string; text: string };

/** The one call this provider needs: text in, WAV bytes out. */
export type SpeechClient = { speak: (request: SpeechRequest) => Promise<Buffer> };

export type VoiceListing = { name: string; description: string };

/** The real client. The request is written against the SDK's own types, so a change in them fails here. */
export const createGeminiSpeechClient = (apiKey: string): SpeechClient => {
  const client = new GoogleGenAI({ apiKey });
  return {
    speak: async ({ model, voice, style, text }: SpeechRequest): Promise<Buffer> => {
      // A refused request (a key that does not work, a model that is not there, a quota) is said
      // in one line, as a voice error, rather than as the client's own stack.
      const interaction = await client.interactions
        .create({
          model,
          input: [
            {
              type: "user_input",
              content: [{ type: "text", text, annotations: [{ type: "speech_metadata", style }] }],
            },
          ],
          // Every later step reads the clip as WAV, so ask for WAV rather than take a default.
          response_format: { type: "audio", mime_type: "audio/wav" },
          generation_config: { speech_config: [{ voice }] },
        })
        .catch((error: unknown) => {
          throw new GeminiVoiceError(
            `Gemini refused the request for the line "${text.slice(0, 40)}": ` +
              `${error instanceof Error ? error.message.split("\n")[0] : String(error)}`,
          );
        });
      const encodedAudio = interaction.output_audio?.data;
      if (encodedAudio === undefined || encodedAudio === "") {
        throw new GeminiVoiceError(`Gemini returned no audio for the line "${text.slice(0, 60)}"`);
      }
      return Buffer.from(encodedAudio, "base64");
    },
  };
};

/** List voices from Gemini's voice library, for choosing one. Listing is not billed. */
export const listGeminiVoices = async (
  apiKey: string,
  search: string | undefined,
): Promise<VoiceListing[]> => {
  const client = new GoogleGenAI({ apiKey });
  const response = await client.voices.list(search === undefined ? {} : { search });
  return (response.voices ?? []).map((voice) => ({
    name: voice.display_name ?? "(unnamed)",
    description: [voice.gender, voice.accent, voice.description].filter(Boolean).join("; "),
  }));
};

export const createGeminiProvider = (
  speechClient: SpeechClient,
  model: string,
  voiceName: string,
): VoiceProvider => ({
  name: "gemini",
  fingerprint: () => `gemini:${model}:${voiceName}`,
  dollarsPerTenSeconds: (today: Date) => dollarsPerTenSeconds(model, today),
  synthesize: async (request: VoiceRequest, outputFile: string): Promise<void> => {
    const wavBytes = await speechClient.speak({
      model,
      voice: voiceName,
      style: request.style,
      text: request.text,
    });
    writeFileSync(outputFile, wavBytes);
  },
});

/** Read the API key from the environment; the repository's `.env` is loaded into it first. */
export const geminiApiKey = (environment: NodeJS.ProcessEnv): string => {
  const apiKey = environment.GEMINI_API_KEY;
  if (apiKey === undefined || apiKey.trim() === "") {
    throw new GeminiVoiceError(
      "GEMINI_API_KEY is not set. Create a key in Google AI Studio and put it in the .env at the " +
        "repository root (see .env.example). A Gemini app subscription does not include API access.",
    );
  }
  return apiKey.trim();
};
