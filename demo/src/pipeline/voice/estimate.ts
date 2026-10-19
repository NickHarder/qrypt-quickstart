/**
 * What a final voice-over will cost, said before anything is spent. Each voice says its own price;
 * Gemini's comes from the table here.
 *
 * Prices are per 10 seconds of generated audio, from ai.google.dev/gemini-api/docs/pricing as read on
 * 2026-10-02. Google publishes a higher price from 2027-01-01; both are here. Check the page when the
 * numbers matter: this table is a courtesy, not a quote.
 */
import type { Line } from "../../catalog/schemas";
import { estimatedSpeechSeconds, type VoiceProvider } from "./provider";

type PricePeriod = { from: string; dollarsPerTenSeconds: number };

const PRICE_PERIODS_BY_MODEL: Record<string, PricePeriod[]> = {
  "gemini-3.8-flash-tts": [
    { from: "2026-01-01", dollarsPerTenSeconds: 0.00225 },
    { from: "2027-01-01", dollarsPerTenSeconds: 0.0045 },
  ],
  "gemini-3.8-flash-lite-tts": [
    { from: "2026-01-01", dollarsPerTenSeconds: 0.0015 },
    { from: "2027-01-01", dollarsPerTenSeconds: 0.003 },
  ],
};

export type VoiceEstimate = {
  lineCount: number;
  seconds: number;
  /** Undefined when the voice has no known price. */
  dollars: number | undefined;
};

export const dollarsPerTenSeconds = (model: string, today: Date): number | undefined => {
  const pricePeriods = PRICE_PERIODS_BY_MODEL[model];
  if (pricePeriods === undefined) {
    return undefined;
  }
  const todayIsoDate = today.toISOString().slice(0, 10);
  const periodsInForce = pricePeriods.filter((period) => period.from <= todayIsoDate);
  return periodsInForce.at(-1)?.dollarsPerTenSeconds;
};

export const estimateVoiceCost = (
  lines: readonly Line[],
  provider: VoiceProvider,
  today: Date,
): VoiceEstimate => {
  const seconds = lines.reduce((total, line) => total + estimatedSpeechSeconds(line.text), 0);
  const price = provider.dollarsPerTenSeconds(today);
  return {
    lineCount: lines.length,
    seconds,
    dollars: price === undefined ? undefined : (seconds / 10) * price,
  };
};

export const describeEstimate = (estimate: VoiceEstimate, model: string): string => {
  const cost =
    estimate.dollars === undefined
      ? `no price is known here for ${model}; check the pricing page`
      : `about $${estimate.dollars.toFixed(4)} with ${model}`;
  return `${estimate.lineCount} line(s) to voice, about ${estimate.seconds.toFixed(0)} s of audio: ${cost}`;
};

/**
 * A read far longer or shorter than its text suggests is usually wrong: the model spoke the
 * directions, or stopped early. These lines are listed for the owner to listen to; nothing is retried
 * automatically, because a retry costs money.
 */
export const isSuspectRead = (text: string, measuredSeconds: number): boolean => {
  const expectedSeconds = estimatedSpeechSeconds(text);
  return measuredSeconds > expectedSeconds * 2.5 || measuredSeconds < expectedSeconds * 0.4;
};
