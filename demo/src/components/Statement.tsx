/** One sentence, large. For the claim a viewer should leave with. */
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { StatementProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

export const Statement = ({ text, detail }: StatementProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: brand.colors.background,
        justifyContent: "center",
        padding: "0 180px",
      }}
    >
      <p
        style={{
          margin: 0,
          color: brand.colors.text,
          fontFamily: brand.fonts.heading,
          fontSize: 84,
          fontWeight: 700,
          lineHeight: 1.15,
          opacity: interpolate(frame, [0, 0.5 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {text}
      </p>
      {detail === undefined ? null : (
        <p
          style={{
            margin: "40px 0 0",
            color: brand.colors.muted,
            fontFamily: brand.fonts.body,
            fontSize: 40,
            lineHeight: 1.35,
            opacity: interpolate(frame, [0.5 * fps, 1.1 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {detail}
        </p>
      )}
    </AbsoluteFill>
  );
};
