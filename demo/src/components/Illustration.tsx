/**
 * A generated or licensed still or clip, for a moment the product itself cannot show. It always
 * carries a tag saying what it is: there is no prop to turn the tag off.
 */
import { Video } from "@remotion/media";
import { AbsoluteFill, Img, staticFile, useVideoConfig } from "remotion";
import type { IllustrationProps } from "../catalog/schemas";
import { useBrand } from "./BrandContext";

const VIDEO_EXTENSIONS = [".mp4", ".webm", ".mov"];

export const Illustration = ({ file, caption }: IllustrationProps) => {
  const { fps } = useVideoConfig();
  const brand = useBrand();
  const source = staticFile(`media/${file}`);
  const isVideo = VIDEO_EXTENSIONS.some((extension) => file.toLowerCase().endsWith(extension));

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.background }}>
      {isVideo ? (
        <Video
          src={source}
          muted
          loop
          premountFor={fps}
          style={{ width: "100%", height: "100%" }}
          objectFit="cover"
        />
      ) : (
        <Img src={source} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <div
        style={{
          position: "absolute",
          top: 48,
          right: 48,
          padding: "10px 22px",
          borderRadius: 999,
          backgroundColor: "rgba(0, 0, 0, 0.72)",
          color: "#FFFFFF",
          fontFamily: brand.fonts.body,
          fontSize: 28,
          letterSpacing: 1,
        }}
      >
        illustration
      </div>
      {caption === undefined ? null : (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            padding: "36px 80px",
            backgroundColor: "rgba(0, 0, 0, 0.72)",
            color: "#FFFFFF",
            fontFamily: brand.fonts.body,
            fontSize: 40,
          }}
        >
          {caption}
        </div>
      )}
    </AbsoluteFill>
  );
};
