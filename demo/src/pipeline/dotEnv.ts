/**
 * The project's `.env`: one file at the repository root holds every key, for every layer. The demo
 * reads its Gemini key from there, beside the Python service's settings.
 */
import { existsSync } from "node:fs";
import path from "node:path";

/** The name of the file at the repository root that holds the project's keys. */
export const DOT_ENV_FILE_NAME = ".env";

/**
 * Put the repository's `.env` into the environment, if there is one, so a key can live outside the
 * shell. A name the shell already set keeps its value.
 */
export const loadProjectDotEnv = (repositoryRoot: string): void => {
  const dotEnvFile = path.join(repositoryRoot, DOT_ENV_FILE_NAME);
  if (existsSync(dotEnvFile)) {
    process.loadEnvFile(dotEnvFile);
  }
};
