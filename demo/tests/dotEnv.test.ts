import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadProjectDotEnv } from "../src/pipeline/dotEnv";

/** A fresh directory standing in for a repository root, holding the given `.env` text if any. */
const repositoryRootWith = (dotEnvText: string | undefined): string => {
  const repositoryRoot = mkdtempSync(path.join(tmpdir(), "demo-dot-env-"));
  if (dotEnvText !== undefined) {
    writeFileSync(path.join(repositoryRoot, ".env"), dotEnvText);
  }
  return repositoryRoot;
};

describe("loadProjectDotEnv", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("puts the names in the repository's .env into the environment", () => {
    const repositoryRoot = repositoryRootWith(
      "# Another layer's setting shares the file.\nDEMO_PROJECT_LOG_LEVEL=INFO\nDOT_ENV_TEST_FROM_FILE=from-the-file\n",
    );
    loadProjectDotEnv(repositoryRoot);
    expect(process.env.DOT_ENV_TEST_FROM_FILE).toBe("from-the-file");
  });

  it("keeps a value the shell already set", () => {
    vi.stubEnv("DOT_ENV_TEST_FROM_SHELL", "from-the-shell");
    loadProjectDotEnv(repositoryRootWith("DOT_ENV_TEST_FROM_SHELL=from-the-file\n"));
    expect(process.env.DOT_ENV_TEST_FROM_SHELL).toBe("from-the-shell");
  });

  it("does nothing when the repository has no .env", () => {
    expect(() => loadProjectDotEnv(repositoryRootWith(undefined))).not.toThrow();
  });
});
