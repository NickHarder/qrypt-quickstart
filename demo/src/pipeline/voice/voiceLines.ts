/**
 * Voice every line of a storyboard, one clip per line, and measure each clip.
 *
 * A clip is made again only when its spoken text, its style or the voice changed: each one is stored
 * with a hash of those three. The spoken text is the line with the brand's pronunciations applied. So a second run costs nothing, and a rewrite of one line pays for one line.
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

const escapedForRegExp = (text: string): string => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** The line as the voice should say it: each word the brand respells, replaced as a whole word. */
export const spokenText = (text: string, brand: Brand): string =>
  Object.entries(brand.voice.pronunciations ?? {}).reduce(
    (spoken, [written, said]) =>
      spoken.replace(new RegExp(`\\b${escapedForRegExp(written)}\\b`, "g"), said),
    text,
  );

/** The hash that decides whether an existing clip still matches its line. */
export const lineHash = (provider: VoiceProvider, line: Line, brand: Brand): string =>
  createHash("sha256")
    .update(
      JSON.stringify([
        provider.fingerprint(),
        spokenText(line.text, brand),
        line.style ?? brand.voice.style,
      ]),
    )
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
    return index[line.key]?.hash !== lineHash(provider, line, brand) || !existsSync(clipFile);
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
        {
          key: line.key,
          text: spokenText(line.text, brand),
          style: line.style ?? brand.voice.style,
        },
        clipFile,
      );
      synthesizedKeys.push(line.key);
    }
    const durationSeconds = wavFileDurationSeconds(clipFile);
    index[line.key] = {
      hash: lineHash(provider, line, brand),
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
