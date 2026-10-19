/**
 * Check that every color pair the components draw can be read.
 *
 * Text in a video is large, and a viewer cannot zoom or change the colors, so the bar is WCAG AAA for
 * large text: a contrast ratio of at least 4.5 to 1.
 */
import type { Brand } from "../catalog/schemas";

export const MIN_CONTRAST_RATIO = 4.5;

const channelLuminance = (channel: number): number => {
  const normalized = channel / 255;
  return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
};

export const relativeLuminance = (hexColor: string): number => {
  const red = Number.parseInt(hexColor.slice(1, 3), 16);
  const green = Number.parseInt(hexColor.slice(3, 5), 16);
  const blue = Number.parseInt(hexColor.slice(5, 7), 16);
  return (
    0.2126 * channelLuminance(red) +
    0.7152 * channelLuminance(green) +
    0.0722 * channelLuminance(blue)
  );
};

export const contrastRatio = (firstHexColor: string, secondHexColor: string): number => {
  const firstLuminance = relativeLuminance(firstHexColor);
  const secondLuminance = relativeLuminance(secondHexColor);
  const lighter = Math.max(firstLuminance, secondLuminance);
  const darker = Math.min(firstLuminance, secondLuminance);
  return (lighter + 0.05) / (darker + 0.05);
};

/** Every foreground and background the components put together. */
const drawnPairs = (brand: Brand): { foreground: string; background: string; label: string }[] => [
  {
    label: "text on background",
    foreground: brand.colors.text,
    background: brand.colors.background,
  },
  {
    label: "muted on background",
    foreground: brand.colors.muted,
    background: brand.colors.background,
  },
  {
    label: "accent on background",
    foreground: brand.colors.accent,
    background: brand.colors.background,
  },
  { label: "text on surface", foreground: brand.colors.text, background: brand.colors.surface },
  { label: "muted on surface", foreground: brand.colors.muted, background: brand.colors.surface },
  { label: "accent on surface", foreground: brand.colors.accent, background: brand.colors.surface },
];

/** Every pair that cannot be read comfortably; empty when all can. */
export const contrastProblems = (brand: Brand): string[] =>
  drawnPairs(brand)
    .map((pair) => ({ ...pair, ratio: contrastRatio(pair.foreground, pair.background) }))
    .filter((pair) => pair.ratio < MIN_CONTRAST_RATIO)
    .map(
      (pair) =>
        `brand.json: ${pair.label} (${pair.foreground} on ${pair.background}) has a contrast of ` +
        `${pair.ratio.toFixed(2)} to 1; at least ${MIN_CONTRAST_RATIO} to 1 is needed`,
    );
