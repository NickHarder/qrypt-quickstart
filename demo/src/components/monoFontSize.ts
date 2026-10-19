/**
 * The type size for a block of monospace lines: as large as fits the longest line in the width there
 * is, between a floor that is still readable in a 1080p video and the size the short lines get.
 */
const LARGEST_FONT_SIZE = 30;
const SMALLEST_FONT_SIZE = 22;
/** A monospace character is about this fraction of the font size wide. */
const CHARACTER_WIDTH_RATIO = 0.602;

export const monoFontSize = (lines: readonly string[], availableWidth: number): number => {
  const longestLineLength = Math.max(1, ...lines.map((line) => line.length));
  const sizeThatFits = Math.floor(availableWidth / (longestLineLength * CHARACTER_WIDTH_RATIO));
  return Math.max(SMALLEST_FONT_SIZE, Math.min(LARGEST_FONT_SIZE, sizeThatFits));
};
