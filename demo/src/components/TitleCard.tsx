/** The opening card: the title, and one line under it. */
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { TitleCardProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

export const TitleCard = ({ title, subtitle }: TitleCardProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: brand.colors.background,
        justifyContent: "center",
        padding: "0 160px",
      }}
    >
      <h1
        style={{
          margin: 0,
          color: brand.colors.text,
          fontFamily: brand.fonts.heading,
          fontSize: 112,
          fontWeight: 700,
          lineHeight: 1.05,
          opacity: interpolate(frame, [0, 0.6 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [0, 0.6 * fps], ["0px 24px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {title}
      </h1>
      {subtitle === undefined ? null : (
        <p
          style={{
            margin: "36px 0 0",
            color: brand.colors.muted,
            fontFamily: brand.fonts.body,
            fontSize: 44,
            lineHeight: 1.3,
            maxWidth: 1300,
            opacity: interpolate(frame, [0.4 * fps, 1.0 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {subtitle}
        </p>
      )}
      <div
        style={{
          position: "absolute",
          left: 160,
          bottom: 120,
          height: 8,
          backgroundColor: brand.colors.accent,
          width: interpolate(frame, [0.2 * fps, 1.0 * fps], [0, 240], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      />
    </AbsoluteFill>
  );
};
