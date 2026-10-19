/**
 * Approved scenes are locked.
 *
 * The owner makes the creative calls, one scene at a time. Once a scene is approved, its hash is
 * recorded in `approved.json`; if the scene changes afterwards, the check fails until the owner reopens
 * it. So an approved line or shot cannot be reworded or re-timed in passing.
 */
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";
import { z } from "zod";
import type { Scene, Storyboard } from "../catalog/schemas";
import { loadKeptFile } from "./storyboard";

const approvalsSchema = z.record(
  z.string(),
  z.strictObject({
    hash: z.string().regex(/^[0-9a-f]{64}$/),
    approved_on: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  }),
);

export type Approvals = z.infer<typeof approvalsSchema>;

/** A scene id that is not in the storyboard. */
export class UnknownSceneError extends Error {}

/** JSON with object keys in a fixed order, so the same scene always hashes the same. */
const canonicalJson = (value: unknown): string => {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const sortedEntries = Object.entries(value)
      .filter(([, entryValue]) => entryValue !== undefined)
      .sort(([firstKey], [secondKey]) => firstKey.localeCompare(secondKey))
      .map(([key, entryValue]) => `${JSON.stringify(key)}:${canonicalJson(entryValue)}`);
    return `{${sortedEntries.join(",")}}`;
  }
  return JSON.stringify(value);
};

/** Everything about a scene that the owner approved: its component, its props and its lines. */
export const sceneHash = (scene: Scene): string =>
  createHash("sha256").update(canonicalJson(scene)).digest("hex");

export const loadApprovals = (approvalsFile: string): Approvals =>
  loadKeptFile(approvalsFile, approvalsSchema, {});

const saveApprovals = (approvalsFile: string, approvals: Approvals): void => {
  const sortedApprovals = Object.fromEntries(
    Object.entries(approvals).sort(([firstId], [secondId]) => firstId.localeCompare(secondId)),
  );
  writeFileSync(approvalsFile, `${JSON.stringify(sortedApprovals, null, 2)}\n`, "utf8");
};

/** Record the owner's approval of a scene as it is now. */
export const approveScene = (
  approvalsFile: string,
  storyboard: Storyboard,
  sceneId: string,
  today: Date,
): void => {
  const scene = storyboard.scenes.find((candidate) => candidate.id === sceneId);
  if (scene === undefined) {
    throw new UnknownSceneError(`there is no scene "${sceneId}" in the storyboard`);
  }
  saveApprovals(approvalsFile, {
    ...loadApprovals(approvalsFile),
    [sceneId]: { hash: sceneHash(scene), approved_on: today.toISOString().slice(0, 10) },
  });
};

/** Remove a scene's approval, so it can be changed. Returns false when it was not approved. */
export const reopenScene = (approvalsFile: string, sceneId: string): boolean => {
  const { [sceneId]: removedApproval, ...remainingApprovals } = loadApprovals(approvalsFile);
  if (removedApproval === undefined) {
    return false;
  }
  saveApprovals(approvalsFile, remainingApprovals);
  return true;
};

/** Every approved scene that has changed or gone; empty when all are as approved. */
export const approvalProblems = (storyboard: Storyboard, approvals: Approvals): string[] =>
  Object.entries(approvals).flatMap(([sceneId, approval]) => {
    const scene = storyboard.scenes.find((candidate) => candidate.id === sceneId);
    if (scene === undefined) {
      return [
        `scene "${sceneId}" was approved on ${approval.approved_on} and is no longer in the storyboard. ` +
          `If the owner asked for that, reopen it:  make demo-reopen SCENE=${sceneId}`,
      ];
    }
    return sceneHash(scene) === approval.hash
      ? []
      : [
          `scene "${sceneId}" was approved on ${approval.approved_on} and has changed since. ` +
            `Put it back, or if the owner asked for the change, reopen it:  make demo-reopen SCENE=${sceneId}`,
        ];
  });
