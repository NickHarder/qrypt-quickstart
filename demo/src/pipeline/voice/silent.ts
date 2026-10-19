/**
 * The stand-in for machines with no voice at all (CI, Linux): a silent clip of the length the line
 * would roughly take to say. It lets timing, rendering and the checks run anywhere.
 */
import { writeSilentWav } from "../wav";
import { estimatedSpeechSeconds, FREE, type VoiceProvider, type VoiceRequest } from "./provider";

export const createSilentProvider = (): VoiceProvider => ({
  name: "silent",
  fingerprint: () => "silent:v1",
  dollarsPerTenSeconds: FREE,
  synthesize: async (request: VoiceRequest, outputFile: string): Promise<void> => {
    writeSilentWav(outputFile, estimatedSpeechSeconds(request.text));
  },
});
