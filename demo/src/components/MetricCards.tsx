/** Up to four numbers. Each says what it was measured on and where it comes from, on screen. */
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import type { MetricCardsProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

export const MetricCards = ({ title, metrics }: MetricCardsProps) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const brand = useBrand();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: brand.colors.background,
        justifyContent: "center",
        padding: "0 120px",
      }}
    >
      {title === undefined ? null : (
        <h2
          style={{
            margin: "0 0 56px",
            color: brand.colors.text,
            fontFamily: brand.fonts.heading,
            fontSize: 64,
            fontWeight: 700,
          }}
        >
          {title}
        </h2>
      )}
      <div style={{ display: "flex", gap: 36 }}>
        {metrics.map((metric, metricIndex) => (
          <div
            key={metric.label}
            style={{
              flex: 1,
              backgroundColor: brand.colors.surface,
              borderRadius: 20,
              padding: "44px 40px",
              opacity: interpolate(
                frame,
                [(0.2 + 0.25 * metricIndex) * fps, (0.7 + 0.25 * metricIndex) * fps],
                [0, 1],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.bezier(0.16, 1, 0.3, 1),
                },
              ),
            }}
          >
            <div
              style={{
                color: brand.colors.accent,
                fontFamily: brand.fonts.heading,
                fontSize: 96,
                fontWeight: 700,
                lineHeight: 1,
              }}
            >
              {metric.value}
            </div>
            <div
              style={{
                marginTop: 20,
                color: brand.colors.text,
                fontFamily: brand.fonts.body,
                fontSize: 36,
                lineHeight: 1.25,
              }}
            >
              {metric.label}
            </div>
            <div
              style={{
                marginTop: 24,
                color: brand.colors.muted,
                fontFamily: brand.fonts.body,
                fontSize: 26,
                lineHeight: 1.3,
              }}
            >
              {metric.scope} · {metric.source}
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
