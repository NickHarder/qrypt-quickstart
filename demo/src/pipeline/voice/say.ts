/** The free draft voice on a Mac: `say`. It costs nothing, so timing and rendering are checked with it first. */
import { execFile } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { FREE, type VoiceProvider, type VoiceRequest } from "./provider";

const execFileAsync = promisify(execFile);

export class SayUnavailableError extends Error {}

export const createSayProvider = (voiceName: string, wordsPerMinute: number): VoiceProvider => ({
  name: "say",
  fingerprint: () => `say:${voiceName}:${wordsPerMinute}`,
  dollarsPerTenSeconds: FREE,
  synthesize: async (request: VoiceRequest, outputFile: string): Promise<void> => {
    if (process.platform !== "darwin") {
      throw new SayUnavailableError(
        "`say` is macOS's voice, which this machine does not have; use --provider espeak or silent",
      );
    }
    // The text goes in through a file, so a line that starts with a dash is not read as an option.
    const scratchDirectory = mkdtempSync(path.join(tmpdir(), "demo-say-"));
    const textFile = path.join(scratchDirectory, "line.txt");
    try {
      writeFileSync(textFile, request.text, "utf8");
      await execFileAsync("say", [
        "-v",
        voiceName,
        "-r",
        String(wordsPerMinute),
        "--file-format=WAVE",
        "--data-format=LEI16@24000",
        "-o",
        outputFile,
        "-f",
        textFile,
      ]);
    } finally {
      rmSync(scratchDirectory, { recursive: true, force: true });
    }
  },
});
