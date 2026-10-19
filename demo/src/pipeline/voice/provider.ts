/**
 * What every voice has in common: it turns one line of text into one WAV file, and says what that
 * costs. A voice is one file beside this one; `final.ts` names the paid ones a finished cut can use.
 */

export type VoiceRequest = {
  /** The line's key; the clip is saved under this name. */
  key: string;
  text: string;
  /** Delivery direction. The draft voices ignore it. */
  style: string;
};

export interface VoiceProvider {
  /** Used in file paths and in the timeline, so a draft clip is never mistaken for a final one. */
  readonly name: string;
  /** Everything about this voice that changes how a line sounds. Part of each clip's cache hash. */
  fingerprint(): string;
  /** Write the spoken line to `outputFile` as a WAV. */
  synthesize(request: VoiceRequest, outputFile: string): Promise<void>;
  /** What ten seconds of audio cost on a date, in dollars: 0 when free, undefined when unknown. */
  dollarsPerTenSeconds(today: Date): number | undefined;
}

/** The price of every voice that costs nothing. */
export const FREE = (): number => 0;

/** The voices that cost nothing, by `name`: their clips can always be made again. */
export const FREE_VOICE_NAMES: readonly string[] = ["kokoro", "say", "espeak", "silent"];

/** Roughly how long a line takes to say, for the silent stand-in and for cost estimates. */
export const WORDS_PER_SECOND = 2.5;

export const estimatedSpeechSeconds = (text: string): number => {
  const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
  return wordCount / WORDS_PER_SECOND + 0.4;
};
