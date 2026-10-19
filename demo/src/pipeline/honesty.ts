/**
 * The honest-film rules, as checks.
 *
 * A demo is evidence. What it shows of the product must be the product, so these fail a cut that
 * would show something else in its place.
 */
import type { Brand, MediaManifest, Storyboard } from "../catalog/schemas";

/** Every ScreenRecording scene must show a take that the manifest lists as recorded footage. */
export const footageProvenanceProblems = (
  storyboard: Storyboard,
  manifest: MediaManifest,
): string[] =>
  storyboard.scenes.flatMap((scene) => {
    if (scene.component !== "ScreenRecording") {
      return [];
    }
    const manifestPath = `takes/${scene.props.take}.webm`;
    const manifestEntry = manifest[manifestPath];
    if (manifestEntry === undefined) {
      return [
        `scene "${scene.id}" shows take "${scene.props.take}", which is not in media.lock.json; ` +
          "record it with `make demo-capture`",
      ];
    }
    return manifestEntry.provenance === "recorded"
      ? []
      : [
          `scene "${scene.id}" shows take "${scene.props.take}", listed as ${manifestEntry.provenance}; ` +
            "product footage must be recorded, never generated",
        ];
  });

/**
 * An Illustration must be a file the manifest lists as generated or licensed, and music must be
 * licensed. So nothing made by a model, and nothing someone else owns, is in a cut without a record
 * of what it is and where it came from.
 */
export const mediaProvenanceProblems = (
  storyboard: Storyboard,
  brand: Brand,
  manifest: MediaManifest,
): string[] => {
  const illustrationProblems = storyboard.scenes.flatMap((scene) => {
    if (scene.component !== "Illustration") {
      return [];
    }
    const manifestEntry = manifest[scene.props.file];
    if (manifestEntry === undefined) {
      return [
        `scene "${scene.id}" shows ${scene.props.file}, which is not in media.lock.json; ` +
          "list it with its provenance and a note saying how it was made",
      ];
    }
    return manifestEntry.provenance === "generated" || manifestEntry.provenance === "licensed"
      ? []
      : [
          `scene "${scene.id}" is an Illustration of ${scene.props.file}, listed as ` +
            `${manifestEntry.provenance}; show recorded footage with ScreenRecording instead`,
        ];
  });
  const musicFile = brand.music?.file;
  const musicProblems =
    musicFile === undefined || manifest[musicFile]?.provenance === "licensed"
      ? []
      : [
          `brand.json names the music ${musicFile}, which media.lock.json does not list as licensed; ` +
            "list it with a note naming the licence",
        ];
  return [...illustrationProblems, ...musicProblems];
};

/** Every honest-film rule that is checked against the manifest. */
export const honestyProblems = (
  storyboard: Storyboard,
  brand: Brand,
  manifest: MediaManifest,
): string[] => [
  ...footageProvenanceProblems(storyboard, manifest),
  ...mediaProvenanceProblems(storyboard, brand, manifest),
];
