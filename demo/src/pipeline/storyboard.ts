/**
 * Read and validate the pipeline's JSON: the two files a person edits, the storyboard and the brand,
 * and the files the pipeline keeps beside them.
 */
import { existsSync, readFileSync } from "node:fs";
import type { z } from "zod";
import { type Brand, brandSchema, type Storyboard, storyboardSchema } from "../catalog/schemas";

/** A file that does not satisfy its schema. The message names each problem and where it is. */
export class ValidationError extends Error {}

const describeIssues = (fileLabel: string, error: z.ZodError): string => {
  const issueLines = error.issues.map((issue) => {
    const location = issue.path.length > 0 ? issue.path.join(".") : "(top level)";
    return `  ${location}: ${issue.message}`;
  });
  return [`${fileLabel} is not valid:`, ...issueLines].join("\n");
};

/** Parse a storyboard from already-loaded JSON; throws ValidationError naming every problem. */
export const parseStoryboard = (
  rawStoryboard: unknown,
  fileLabel = "storyboard.json",
): Storyboard => {
  const parsed = storyboardSchema.safeParse(rawStoryboard);
  if (!parsed.success) {
    throw new ValidationError(describeIssues(fileLabel, parsed.error));
  }
  return parsed.data;
};

/** Parse a brand from already-loaded JSON; throws ValidationError naming every problem. */
export const parseBrand = (rawBrand: unknown, fileLabel = "brand.json"): Brand => {
  const parsed = brandSchema.safeParse(rawBrand);
  if (!parsed.success) {
    throw new ValidationError(describeIssues(fileLabel, parsed.error));
  }
  return parsed.data;
};

const readJsonFile = (filePath: string): unknown => {
  try {
    return JSON.parse(readFileSync(filePath, "utf8"));
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new ValidationError(`${filePath} could not be read as JSON: ${reason}`);
  }
};

/**
 * Read a file the pipeline keeps (the approvals, the media manifest, the beats), or `whenMissing`
 * while there is none yet. Throws ValidationError naming the file when it is not what it should be.
 */
export const loadKeptFile = <Kept>(
  keptFile: string,
  schema: z.ZodType<Kept>,
  whenMissing: Kept,
): Kept => {
  if (!existsSync(keptFile)) {
    return whenMissing;
  }
  const parsed = schema.safeParse(readJsonFile(keptFile));
  if (!parsed.success) {
    throw new ValidationError(describeIssues(keptFile, parsed.error));
  }
  return parsed.data;
};

export const loadStoryboard = (storyboardFile: string): Storyboard =>
  parseStoryboard(readJsonFile(storyboardFile), storyboardFile);

export const loadBrand = (brandFile: string): Brand =>
  parseBrand(readJsonFile(brandFile), brandFile);
