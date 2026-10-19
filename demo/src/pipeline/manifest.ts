/**
 * The media manifest, `media.lock.json`.
 *
 * Media stays out of git: takes, voice clips, generated clips and music are large and binary. The
 * manifest is what is committed in their place: each file's checksum, its size, and where it came
 * from. A cut can be rebuilt from an archive of the media, and the manifest says whether the archive
 * is the right one.
 */
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { type MediaManifest, mediaManifestSchema, type Provenance } from "../catalog/schemas";
import { loadKeptFile } from "./storyboard";
import { FREE_VOICE_NAMES } from "./voice/provider";

export const loadManifest = (manifestFile: string): MediaManifest =>
  loadKeptFile(manifestFile, mediaManifestSchema, {});

const fileSha256 = (filePath: string): string =>
  createHash("sha256").update(readFileSync(filePath)).digest("hex");

/** Record a media file (a path under the media directory) in the manifest, replacing any earlier entry. */
export const recordMedia = (
  manifestFile: string,
  mediaDirectory: string,
  relativePath: string,
  provenance: Provenance,
  note?: string,
): void => {
  const mediaFile = path.join(mediaDirectory, relativePath);
  const manifest = loadManifest(manifestFile);
  const updatedManifest: MediaManifest = {
    ...manifest,
    [relativePath]: {
      sha256: fileSha256(mediaFile),
      bytes: statSync(mediaFile).size,
      provenance,
      ...(note === undefined ? {} : { note }),
    },
  };
  const sortedManifest = Object.fromEntries(
    Object.entries(updatedManifest).sort(([firstPath], [secondPath]) =>
      firstPath.localeCompare(secondPath),
    ),
  );
  writeFileSync(manifestFile, `${JSON.stringify(sortedManifest, null, 2)}\n`, "utf8");
};

/**
 * Draft voice clips can always be made again, so they are not listed. The final voice's index is:
 * without it, every line counts as new and is paid for again.
 */
const isRegenerable = (relativePath: string): boolean =>
  FREE_VOICE_NAMES.some((voiceName) => relativePath.startsWith(`voice/${voiceName}/`)) ||
  path.basename(relativePath) === ".DS_Store";

const filesUnder = (directory: string, prefix = ""): string[] =>
  existsSync(directory)
    ? readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
        const relativePath = prefix === "" ? entry.name : `${prefix}/${entry.name}`;
        return entry.isDirectory()
          ? filesUnder(path.join(directory, entry.name), relativePath)
          : [relativePath];
      })
    : [];

/** Every way the media on disk differs from the manifest; empty when they agree. */
export const assetProblems = (manifest: MediaManifest, mediaDirectory: string): string[] => {
  const listedProblems = Object.entries(manifest).flatMap(([relativePath, entry]) => {
    const mediaFile = path.join(mediaDirectory, relativePath);
    if (!existsSync(mediaFile)) {
      return [`MISSING ${relativePath} (${entry.provenance}); restore it from the media archive`];
    }
    return fileSha256(mediaFile) === entry.sha256
      ? []
      : [`CHANGED ${relativePath}: it is not the file the manifest lists`];
  });
  const unlistedProblems = filesUnder(mediaDirectory)
    .filter((relativePath) => !isRegenerable(relativePath) && manifest[relativePath] === undefined)
    .map(
      (relativePath) =>
        `UNLISTED ${relativePath}: add it to media.lock.json, saying where it came from`,
    );
  return [...listedProblems, ...unlistedProblems];
};
