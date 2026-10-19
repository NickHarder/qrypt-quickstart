/**
 * Voice every line of a storyboard, one clip per line, and measure each clip.
 *
 * A clip is made again only when its text, its style or the voice changed: each one is stored with a
 * hash of those three. So a second run costs nothing, and a rewrite of one line pays for one line.
 * The index is written after every line, so a run that stops part-way never pays twice for a clip.
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import type { Brand, Line, Storyboard } from "../../catalog/schemas";
import type { VoicedLine } from "../timeline";
import { wavFileDurationSeconds } from "../wav";
import type { VoiceProvider } from "./provider";

type VoiceIndex = Record<string, { hash: string; seconds: number }>;

export type VoiceRun = {
  voicedLinesByKey: Map<string, VoicedLine>;
  /** Keys synthesized in this run; the rest came from the cache. */
  synthesizedKeys: string[];
};

const allLines = (storyboard: Storyboard): Line[] =>
  storyboard.scenes.flatMap((scene) => scene.lines);

/** The hash that decides whether an existing clip still matches its line. */
export const lineHash = (provider: VoiceProvider, line: Line, defaultStyle: string): string =>
  createHash("sha256")
    .update(JSON.stringify([provider.fingerprint(), line.text, line.style ?? defaultStyle]))
    .digest("hex");

const readIndex = (indexFile: string): VoiceIndex =>
  existsSync(indexFile) ? (JSON.parse(readFileSync(indexFile, "utf8")) as VoiceIndex) : {};

/** The lines that have no current clip for this provider: what a run would have to synthesize. */
export const linesNeedingVoice = (
  storyboard: Storyboard,
  brand: Brand,
  provider: VoiceProvider,
  mediaDirectory: string,
): Line[] => {
  const providerDirectory = path.join(mediaDirectory, "voice", provider.name);
  const index = readIndex(path.join(providerDirectory, "index.json"));
  return allLines(storyboard).filter((line) => {
    const clipFile = path.join(providerDirectory, `${line.key}.wav`);
    return (
      index[line.key]?.hash !== lineHash(provider, line, brand.voice.style) || !existsSync(clipFile)
    );
  });
};

export const voiceLines = async (
  storyboard: Storyboard,
  brand: Brand,
  provider: VoiceProvider,
  mediaDirectory: string,
): Promise<VoiceRun> => {
  const providerDirectory = path.join(mediaDirectory, "voice", provider.name);
  mkdirSync(providerDirectory, { recursive: true });
  const indexFile = path.join(providerDirectory, "index.json");
  const index = readIndex(indexFile);
  const staleKeys = new Set(
    linesNeedingVoice(storyboard, brand, provider, mediaDirectory).map((line) => line.key),
  );

  const voicedLinesByKey = new Map<string, VoicedLine>();
  const synthesizedKeys: string[] = [];
  for (const line of allLines(storyboard)) {
    const clipFile = path.join(providerDirectory, `${line.key}.wav`);
    if (staleKeys.has(line.key)) {
      await provider.synthesize(
        { key: line.key, text: line.text, style: line.style ?? brand.voice.style },
        clipFile,
      );
      synthesizedKeys.push(line.key);
    }
    const durationSeconds = wavFileDurationSeconds(clipFile);
    index[line.key] = {
      hash: lineHash(provider, line, brand.voice.style),
      seconds: durationSeconds,
    };
    writeFileSync(indexFile, `${JSON.stringify(index, null, 2)}\n`, "utf8");
    voicedLinesByKey.set(line.key, {
      // As `staticFile()` wants it: relative to public/, with forward slashes.
      audioFile: `media/voice/${provider.name}/${line.key}.wav`,
      durationSeconds,
    });
  }
  return { voicedLinesByKey, synthesizedKeys };
};
