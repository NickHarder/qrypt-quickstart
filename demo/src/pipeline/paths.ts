/** Where the demo's files live, relative to the demo directory. */
import path from "node:path";
import { fileURLToPath } from "node:url";

/** The demo directory: the one that holds storyboard.json and package.json. */
export const DEMO_DIRECTORY = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
);

/** The repository the demo is about: scenes name its files from here. */
export const REPOSITORY_ROOT = path.resolve(DEMO_DIRECTORY, "..");

export const STORYBOARD_FILE = path.join(DEMO_DIRECTORY, "storyboard.json");
export const BRAND_FILE = path.join(DEMO_DIRECTORY, "brand.json");
/** The scenes the owner has approved, by content hash. Committed. */
export const APPROVALS_FILE = path.join(DEMO_DIRECTORY, "approved.json");
/** The catalog as JSON Schema, generated from the Zod schemas. Committed; a test fails when it is stale. */
export const CATALOG_SCHEMA_FILE = path.join(DEMO_DIRECTORY, "catalog.schema.json");
/** Where each recorded beat starts and ends in its take. Written by capture; committed. */
export const BEATS_FILE = path.join(DEMO_DIRECTORY, "beats.json");
/** Every media file's checksum and provenance. Committed; the media itself is not. */
export const MANIFEST_FILE = path.join(DEMO_DIRECTORY, "media.lock.json");
/** This project's Playwright takes. */
export const TAKES_DIRECTORY = path.join(DEMO_DIRECTORY, "takes");
/** The small static page the example take records. */
export const EXAMPLE_SITE_DIRECTORY = path.join(DEMO_DIRECTORY, "example-site");

/** Remotion serves files from here; `staticFile()` paths are relative to it. */
export const PUBLIC_DIRECTORY = path.join(DEMO_DIRECTORY, "public");

/** Media is under public/ so the render can load it, and is kept out of git. */
export const MEDIA_DIRECTORY = path.join(PUBLIC_DIRECTORY, "media");

/** Intermediate files: the timeline, logs. Safe to delete. */
export const WORK_DIRECTORY = path.join(DEMO_DIRECTORY, "work");
export const TIMELINE_FILE = path.join(WORK_DIRECTORY, "timeline.json");

/** Finished and draft cuts. */
export const OUTPUT_DIRECTORY = path.join(DEMO_DIRECTORY, "out");

/** The Remotion entry point. */
export const ENTRY_POINT = path.join(DEMO_DIRECTORY, "src", "index.ts");
