/**
 * Read what a scene shows from the repository: the lines of code, the output of a command.
 *
 * A storyboard names a file and a range; it never holds the text itself. So what the video shows is
 * what was in the repository when the cut was built, and it cannot quietly drift from the code.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import type { Scene } from "../catalog/schemas";

/**
 * A code excerpt or an output taller or wider than this does not fit a 1080p frame at a readable
 * size. The width is the line length the kit's own formatters allow; the components shrink their type
 * a little for the longest lines.
 */
export const MAX_CODE_LINES = 18;
export const MAX_TERMINAL_LINES = 18;
export const MAX_LINE_CHARACTERS = 100;

/** A scene names a file or a range that cannot be shown. */
export class ContentError extends Error {}

export type SceneContent = {
  code_lines?: { number: number; text: string }[];
  terminal_lines?: string[];
};

const readLines = (sceneId: string, repositoryRoot: string, relativeFile: string): string[] => {
  const filePath = path.join(repositoryRoot, relativeFile);
  if (!existsSync(filePath)) {
    throw new ContentError(`scene "${sceneId}" names ${relativeFile}, which does not exist`);
  }
  return readFileSync(filePath, "utf8").replace(/\n$/, "").split("\n");
};

const requireLinesFit = (sceneId: string, lines: readonly string[], fileLabel: string): void => {
  const tooLongIndex = lines.findIndex((line) => line.length > MAX_LINE_CHARACTERS);
  if (tooLongIndex !== -1) {
    throw new ContentError(
      `scene "${sceneId}": a line of ${fileLabel} is ${lines[tooLongIndex]?.length} characters; ` +
        `at most ${MAX_LINE_CHARACTERS} fit the frame. Show a narrower range`,
    );
  }
};

export const resolveSceneContent = (scene: Scene, repositoryRoot: string): SceneContent => {
  if (scene.component === "CodeHighlight") {
    const { file, from_line: fromLine, to_line: toLine, highlight } = scene.props;
    const fileLines = readLines(scene.id, repositoryRoot, file);
    if (fromLine > toLine || toLine > fileLines.length) {
      throw new ContentError(
        `scene "${scene.id}" shows lines ${fromLine} to ${toLine} of ${file}, which has ${fileLines.length} lines`,
      );
    }
    if (toLine - fromLine + 1 > MAX_CODE_LINES) {
      throw new ContentError(
        `scene "${scene.id}" shows ${toLine - fromLine + 1} lines of ${file}; at most ${MAX_CODE_LINES} fit the frame`,
      );
    }
    const strayHighlight = highlight.find(
      (lineNumber) => lineNumber < fromLine || lineNumber > toLine,
    );
    if (strayHighlight !== undefined) {
      throw new ContentError(
        `scene "${scene.id}" highlights line ${strayHighlight}, outside the lines it shows (${fromLine} to ${toLine})`,
      );
    }
    const shownLines = fileLines.slice(fromLine - 1, toLine);
    requireLinesFit(scene.id, shownLines, file);
    return {
      code_lines: shownLines.map((text, lineIndex) => ({ number: fromLine + lineIndex, text })),
    };
  }
  if (scene.component === "Terminal") {
    const { output_file: outputFile, from_line: fromLine, to_line: toLine } = scene.props;
    const outputLines = readLines(scene.id, repositoryRoot, outputFile);
    const shownLines = outputLines.slice((fromLine ?? 1) - 1, toLine ?? outputLines.length);
    if (shownLines.length === 0) {
      throw new ContentError(`scene "${scene.id}" shows no lines of ${outputFile}`);
    }
    if (shownLines.length > MAX_TERMINAL_LINES) {
      throw new ContentError(
        `scene "${scene.id}" shows ${shownLines.length} lines of ${outputFile}; at most ` +
          `${MAX_TERMINAL_LINES} fit the frame. Set from_line and to_line`,
      );
    }
    requireLinesFit(scene.id, shownLines, outputFile);
    return { terminal_lines: shownLines };
  }
  return {};
};
