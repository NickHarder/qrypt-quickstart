/**
 * The free draft voice on Linux: espeak-ng, open source and offline. It sounds nothing like the final
 * voice, but it speaks every line, so timing and rendering are checked with words in them at $0.
 */
import { execFile } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { FREE, type VoiceProvider, type VoiceRequest } from "./provider";

const execFileAsync = promisify(execFile);

/** The voice espeak-ng reads English with, as in the United States. */
export const ESPEAK_VOICE = "en-us";

export class EspeakUnavailableError extends Error {}

const isMissingProgram = (error: unknown): boolean =>
  error instanceof Error && "code" in error && error.code === "ENOENT";

export const createEspeakProvider = (voiceName: string, wordsPerMinute: number): VoiceProvider => ({
  name: "espeak",
  fingerprint: () => `espeak:${voiceName}:${wordsPerMinute}`,
  dollarsPerTenSeconds: FREE,
  synthesize: async (request: VoiceRequest, outputFile: string): Promise<void> => {
    // The text goes in through a file, so a line that starts with a dash is not read as an option.
    const scratchDirectory = mkdtempSync(path.join(tmpdir(), "demo-espeak-"));
    const textFile = path.join(scratchDirectory, "line.txt");
    try {
      writeFileSync(textFile, request.text, "utf8");
      await execFileAsync("espeak-ng", [
        "-v",
        voiceName,
        "-s",
        String(wordsPerMinute),
        "-w",
        outputFile,
        "-f",
        textFile,
      ]);
    } catch (error) {
      if (isMissingProgram(error)) {
        throw new EspeakUnavailableError(
          "the draft voice on Linux is espeak-ng, which is not installed: " +
            "sudo apt-get install espeak-ng; or use --provider silent",
        );
      }
      throw error;
    } finally {
      rmSync(scratchDirectory, { recursive: true, force: true });
    }
  },
});
