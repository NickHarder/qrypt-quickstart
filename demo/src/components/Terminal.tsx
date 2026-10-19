/**
 * A command and its real output, revealed line by line. The output comes from a file the command
 * wrote when it was really run; nothing here is typed in by hand.
 */
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { TerminalProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";
import { monoFontSize } from "./monoFontSize";

/** The frame's width, less the padding around and inside the terminal window. */
const TERMINAL_TEXT_WIDTH = 1920 - 2 * 120 - 2 * 48;

type TerminalViewProps = TerminalProps & { sceneId: string; terminalLines: string[] | undefined };

/** The slowest the output is revealed; a long output is revealed faster so it finishes in time. */
const SECONDS_PER_LINE = 0.28;
/** The output is all on screen this long before the scene ends. */
const SETTLE_SECONDS = 1;

export const Terminal = ({ sceneId, command, terminalLines }: TerminalViewProps) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const brand = useBrand();
  if (terminalLines === undefined) {
    throw new Error(
      `scene "${sceneId}" is a Terminal whose output file was not read into the timeline`,
    );
  }
  const fontSize = monoFontSize([`$ ${command}`, ...terminalLines], TERMINAL_TEXT_WIDTH);
  const revealSeconds = Math.max(0.5, durationInFrames / fps - SETTLE_SECONDS - 0.6);
  const secondsPerLine = Math.min(
    SECONDS_PER_LINE,
    revealSeconds / Math.max(1, terminalLines.length),
  );
  const visibleLineCount = Math.max(0, Math.floor((frame / fps - 0.6) / secondsPerLine));

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.background, padding: "90px 120px" }}>
      <div
        style={{
          flex: 1,
          backgroundColor: brand.colors.surface,
          borderRadius: 16,
          padding: "40px 48px",
          fontFamily: brand.fonts.mono,
          fontSize,
          lineHeight: 1.45,
          whiteSpace: "pre-wrap",
          overflow: "hidden",
        }}
      >
        <div style={{ color: brand.colors.accent }}>$ {command}</div>
        {terminalLines.slice(0, visibleLineCount).map((terminalLine, lineIndex) => (
          // The lines of an output have no identity but their position.
          // biome-ignore lint/suspicious/noArrayIndexKey: an output's lines are identified by their order
          <div key={lineIndex} style={{ color: brand.colors.text }}>
            {terminalLine === "" ? " " : terminalLine}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
