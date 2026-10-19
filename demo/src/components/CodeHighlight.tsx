/** An excerpt of a real file, with some lines marked. The lines are read by the pipeline, not typed here. */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { CodeHighlightProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";
import { monoFontSize } from "./monoFontSize";

/** The frame's width, less the padding around the block and the line-number column. */
const CODE_TEXT_WIDTH = 1920 - 2 * 120 - 2 * 36 - 126 - 8;

type CodeHighlightViewProps = CodeHighlightProps & {
  sceneId: string;
  codeLines: { number: number; text: string }[] | undefined;
};

export const CodeHighlight = ({ sceneId, file, highlight, codeLines }: CodeHighlightViewProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();
  if (codeLines === undefined) {
    throw new Error(
      `scene "${sceneId}" is a CodeHighlight whose file was not read into the timeline`,
    );
  }
  const highlightedNumbers = new Set(highlight);
  const fontSize = monoFontSize(
    codeLines.map((codeLine) => codeLine.text),
    CODE_TEXT_WIDTH,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.background, padding: "90px 120px" }}>
      <p
        style={{
          margin: "0 0 28px",
          color: brand.colors.muted,
          fontFamily: brand.fonts.mono,
          fontSize: 30,
        }}
      >
        {file}
      </p>
      <div
        style={{
          flex: 1,
          backgroundColor: brand.colors.surface,
          borderRadius: 16,
          padding: "32px 0",
          overflow: "hidden",
        }}
      >
        {codeLines.map((codeLine) => {
          const isHighlighted = highlightedNumbers.has(codeLine.number);
          return (
            <div
              key={codeLine.number}
              style={{
                display: "flex",
                padding: "0 36px",
                fontFamily: brand.fonts.mono,
                fontSize,
                lineHeight: 1.5,
                whiteSpace: "pre",
                borderLeft: `8px solid ${isHighlighted ? brand.colors.accent : "transparent"}`,
                backgroundColor: isHighlighted ? `${brand.colors.accent}26` : "transparent",
                opacity:
                  highlightedNumbers.size === 0 || isHighlighted
                    ? 1
                    : interpolate(frame, [0.6 * fps, 1.2 * fps], [1, 0.55], {
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                      }),
              }}
            >
              <span
                style={{
                  width: 90,
                  color: brand.colors.muted,
                  textAlign: "right",
                  marginRight: 36,
                }}
              >
                {codeLine.number}
              </span>
              <span style={{ color: brand.colors.text }}>{codeLine.text}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
