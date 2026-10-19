/** The closing card: the title again, and where to find the work. */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { EndCardProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

export const EndCard = ({ title, links }: EndCardProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: brand.colors.background,
        justifyContent: "center",
        alignItems: "center",
        opacity: interpolate(frame, [0, 0.5 * fps], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
      }}
    >
      <h1
        style={{
          margin: 0,
          color: brand.colors.text,
          fontFamily: brand.fonts.heading,
          fontSize: 96,
          fontWeight: 700,
          textAlign: "center",
        }}
      >
        {title}
      </h1>
      <div style={{ marginTop: 48, display: "flex", flexDirection: "column", gap: 16 }}>
        {links.map((link) => (
          <p
            key={link}
            style={{
              margin: 0,
              color: brand.colors.accent,
              fontFamily: brand.fonts.mono,
              fontSize: 36,
              textAlign: "center",
            }}
          >
            {link}
          </p>
        ))}
      </div>
    </AbsoluteFill>
  );
};
