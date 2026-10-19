import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  approvalProblems,
  approveScene,
  loadApprovals,
  reopenScene,
  sceneHash,
  UnknownSceneError,
} from "../src/pipeline/approval";
import { parseStoryboard, ValidationError } from "../src/pipeline/storyboard";

const storyboardWithLine = (text: string, subtitle = "Sub") =>
  parseStoryboard({
    title: "Test",
    target_seconds: { min: 1, max: 600 },
    scenes: [
      {
        id: "open",
        component: "TitleCard",
        props: { title: "Title", subtitle },
        lines: [{ key: "open", text }],
      },
      {
        id: "close",
        component: "EndCard",
        props: { title: "Title" },
        lines: [{ key: "close", text: "Bye." }],
      },
    ],
  });

const approvalsFile = (): string =>
  path.join(mkdtempSync(path.join(tmpdir(), "demo-approval-")), "approved.json");

describe("approved scenes", () => {
  const today = new Date("2026-10-02T12:00:00Z");

  it("pass while they stay as they were approved", () => {
    const file = approvalsFile();
    const storyboard = storyboardWithLine("The approved line.");
    approveScene(file, storyboard, "open", today);
    expect(loadApprovals(file).open?.approved_on).toBe("2026-10-02");
    expect(approvalProblems(storyboard, loadApprovals(file))).toEqual([]);
  });

  it("fail when a line is reworded", () => {
    const file = approvalsFile();
    approveScene(file, storyboardWithLine("The approved line."), "open", today);
    const [problem] = approvalProblems(storyboardWithLine("A reworded line."), loadApprovals(file));
    expect(problem).toContain('scene "open" was approved on 2026-10-02 and has changed since');
    expect(problem).toContain("make demo-reopen SCENE=open");
  });

  it("fail when a prop changes, and when the scene is removed", () => {
    const file = approvalsFile();
    approveScene(file, storyboardWithLine("Line.", "Before"), "open", today);
    expect(
      approvalProblems(storyboardWithLine("Line.", "After"), loadApprovals(file)),
    ).toHaveLength(1);
    const withoutOpen = parseStoryboard({
      title: "Test",
      target_seconds: { min: 1, max: 600 },
      scenes: [
        {
          id: "close",
          component: "EndCard",
          props: { title: "T" },
          lines: [{ key: "c", text: "Bye." }],
        },
      ],
    });
    expect(approvalProblems(withoutOpen, loadApprovals(file))[0]).toContain(
      "no longer in the storyboard",
    );
  });

  it("do not lock the scenes around them", () => {
    const file = approvalsFile();
    const before = storyboardWithLine("Stays.");
    approveScene(file, before, "close", today);
    expect(approvalProblems(storyboardWithLine("Changes freely."), loadApprovals(file))).toEqual(
      [],
    );
  });

  it("can be reopened by the owner, and then changed", () => {
    const file = approvalsFile();
    approveScene(file, storyboardWithLine("The approved line."), "open", today);
    expect(reopenScene(file, "open")).toBe(true);
    expect(reopenScene(file, "open")).toBe(false);
    expect(approvalProblems(storyboardWithLine("A new line."), loadApprovals(file))).toEqual([]);
  });

  it("cannot be given to a scene that does not exist", () => {
    expect(() =>
      approveScene(approvalsFile(), storyboardWithLine("Line."), "nowhere", today),
    ).toThrow(UnknownSceneError);
  });

  it("are refused with the file's name when the file is not JSON", () => {
    const damagedFile = approvalsFile();
    writeFileSync(damagedFile, "<<<<<<< HEAD\n");
    expect(() => loadApprovals(damagedFile)).toThrow(ValidationError);
  });

  it("hash the same whatever order the keys were written in", () => {
    const [scene] = storyboardWithLine("Line.").scenes;
    const reordered = {
      lines: scene?.lines,
      props: scene?.props,
      component: scene?.component,
      id: scene?.id,
    };
    expect(sceneHash(reordered as never)).toBe(sceneHash(scene as never));
  });
});
