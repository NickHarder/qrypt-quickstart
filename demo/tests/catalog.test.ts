import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { catalogSchemaText } from "../src/pipeline/catalog";
import { mediaProvenanceProblems } from "../src/pipeline/honesty";
import { CATALOG_SCHEMA_FILE } from "../src/pipeline/paths";
import { parseStoryboard } from "../src/pipeline/storyboard";
import { exampleBrand } from "./fixtures";

const COMPONENTS = [
  "TitleCard",
  "EndCard",
  "ScreenRecording",
  "Statement",
  "CodeHighlight",
  "Terminal",
  "MetricCards",
  "Illustration",
];

describe("catalog.schema.json", () => {
  it("is the schema the code enforces", () => {
    expect(existsSync(CATALOG_SCHEMA_FILE)).toBe(true);
    expect(readFileSync(CATALOG_SCHEMA_FILE, "utf8")).toBe(catalogSchemaText());
  });

  it("names every component, and nothing a storyboard may not use", () => {
    const schemaText = catalogSchemaText();
    for (const component of COMPONENTS) {
      expect(schemaText).toContain(`"const": "${component}"`);
    }
    expect(schemaText.match(/"const": "[A-Z][A-Za-z]+"/g)).toHaveLength(COMPONENTS.length);
  });
});

describe("mediaProvenanceProblems", () => {
  const entry = { sha256: "b".repeat(64), bytes: 1 };
  const storyboard = parseStoryboard({
    title: "Test",
    target_seconds: { min: 1, max: 600 },
    scenes: [
      {
        id: "corridor",
        component: "Illustration",
        props: { file: "generated/corridor.mp4" },
        lines: [{ key: "a", text: "A line." }],
      },
    ],
  });

  it("passes an illustration the manifest lists as generated", () => {
    const manifest = { "generated/corridor.mp4": { ...entry, provenance: "generated" as const } };
    expect(mediaProvenanceProblems(storyboard, exampleBrand, manifest)).toEqual([]);
  });

  it("fails an illustration that is not listed at all", () => {
    expect(mediaProvenanceProblems(storyboard, exampleBrand, {})[0]).toContain(
      "not in media.lock.json",
    );
  });

  it("fails recorded footage dressed up as an illustration", () => {
    const manifest = { "generated/corridor.mp4": { ...entry, provenance: "recorded" as const } };
    expect(mediaProvenanceProblems(storyboard, exampleBrand, manifest)[0]).toContain(
      "ScreenRecording",
    );
  });

  it("fails music that is not listed as licensed", () => {
    const brandWithMusic = {
      ...exampleBrand,
      music: { file: "music/track.mp3", volume: 0.14, volume_under_voice: 0.04 },
    };
    const emptyStoryboard = parseStoryboard({
      title: "Test",
      target_seconds: { min: 1, max: 600 },
      scenes: [
        {
          id: "one",
          component: "Statement",
          props: { text: "One." },
          lines: [{ key: "a", text: "A." }],
        },
      ],
    });
    expect(mediaProvenanceProblems(emptyStoryboard, brandWithMusic, {})[0]).toContain("licensed");
    const manifest = { "music/track.mp3": { ...entry, provenance: "licensed" as const } };
    expect(mediaProvenanceProblems(emptyStoryboard, brandWithMusic, manifest)).toEqual([]);
  });
});
