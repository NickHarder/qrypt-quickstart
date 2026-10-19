/**
 * The demo layer's known advisories: what `npm audit` reports against `package-lock.json`, held to
 * `known-advisories.json`, a committed list in which each advisory that stays has the date it was
 * accepted and why.
 *
 *     npm run advisories                  (a project's CI runs it in its demo job)
 *     node src/pipeline/advisories.ts     (the same, without the packages installed: Node 22.18 or later)
 *
 * It fails on an advisory the list does not hold, and on a fix npm can make without a breaking
 * change, even for one the list holds. A fix npm offers only as a breaking change, a downgrade
 * included, is noted for a person to read. A listed advisory no longer reported is noted, so the
 * list shrinks. Its imports are Node's own, so it runs before the packages are installed.
 *
 * Exit 0: every advisory reported is on the list and none has a plain fix. Exit 1: one is not, or
 * one has. Exit 3: npm gave no report (the registry could not be reached, the list cannot be read),
 * which is never a pass.
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const EXIT_CLEAN = 0;
export const EXIT_FAILED = 1;
export const EXIT_COULD_NOT_RUN = 3;

/** The demo layer's folder: two levels above this file. */
const DEMO_DIRECTORY = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
export const KNOWN_ADVISORIES_FILE = path.join(DEMO_DIRECTORY, "known-advisories.json");
const LIST_NAME = "known-advisories.json";
/** npm's report of a large lockfile runs to a few megabytes. */
const LARGEST_REPORT_BYTES = 64 * 1024 * 1024;
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

/** The report or the list could not be read: there is no verdict, and that is not a pass. */
export class AdvisoryError extends Error {}

/** One advisory npm reports, by its GitHub id. */
export type Advisory = {
  id: string;
  package: string;
  severity: string;
  title: string;
  url: string;
};

/** What npm offers for one vulnerable package: an update, and whether it is a breaking change. */
export type Fix = { vulnerablePackage: string; update: string; breaking: boolean };

/** An advisory accepted into the list: the date it was, and why it stays. */
export type KnownAdvisory = { id: string; package: string; known_since: string; why: string };

export type Verdict = { failures: string[]; notes: string[] };

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const textOf = (value: unknown): string => (typeof value === "string" ? value : "");

/** The vulnerable packages of a report, or the reason it is no report. */
const vulnerabilitiesOf = (report: unknown): Record<string, unknown>[] => {
  if (!isRecord(report) || !isRecord(report.vulnerabilities)) {
    const error = isRecord(report) && isRecord(report.error) ? report.error : {};
    const reason = textOf(error.summary) || textOf(error.message) || "it is not npm's audit report";
    throw new AdvisoryError(`npm audit gave no report: ${reason}`);
  }
  return Object.values(report.vulnerabilities).filter(isRecord);
};

/** Every advisory the report names, once each, in the order of their ids. */
export const advisoriesOf = (report: unknown): Advisory[] => {
  const byId = new Map<string, Advisory>();
  for (const vulnerability of vulnerabilitiesOf(report)) {
    const causes = Array.isArray(vulnerability.via) ? vulnerability.via : [];
    for (const cause of causes.filter(isRecord)) {
      const url = textOf(cause.url);
      const id = url.split("/").pop() || `npm-${String(cause.source)}`;
      byId.set(id, {
        id,
        package: textOf(cause.name) || textOf(vulnerability.name),
        severity: textOf(cause.severity),
        title: textOf(cause.title),
        url,
      });
    }
  }
  return [...byId.values()].sort((first, second) => first.id.localeCompare(second.id));
};

/** What npm offers for each vulnerable package that it can fix. */
export const fixesOf = (report: unknown): Fix[] =>
  vulnerabilitiesOf(report).flatMap((vulnerability): Fix[] => {
    const offered = vulnerability.fixAvailable;
    const vulnerablePackage = textOf(vulnerability.name);
    if (offered === true) {
      return [{ vulnerablePackage, update: "npm audit fix", breaking: false }];
    }
    if (!isRecord(offered)) {
      return [];
    }
    const update = `${textOf(offered.name)} ${textOf(offered.version)}`;
    return [{ vulnerablePackage, update, breaking: offered.isSemVerMajor === true }];
  });

/** A date written as 2026-10-11 that the calendar has: not 2026-13-40. */
const isRealDate = (text: string): boolean => {
  const date = new Date(`${text}T00:00:00Z`);
  return (
    DATE_PATTERN.test(text) && !Number.isNaN(date.getTime()) && date.toISOString().startsWith(text)
  );
};

const knownAdvisoryOf = (entry: unknown, index: number): KnownAdvisory => {
  const where = `${LIST_NAME}, entry ${index + 1}`;
  if (!isRecord(entry)) {
    throw new AdvisoryError(`${where}: not an object`);
  }
  for (const field of ["id", "package", "why"] as const) {
    if (textOf(entry[field]).trim() === "") {
      throw new AdvisoryError(`${where}: \`${field}\` is missing or empty`);
    }
  }
  const knownSince = textOf(entry.known_since);
  if (!isRealDate(knownSince)) {
    throw new AdvisoryError(`${where}: \`known_since\` must be a date, such as 2026-10-11`);
  }
  return {
    id: textOf(entry.id),
    package: textOf(entry.package),
    known_since: knownSince,
    why: textOf(entry.why),
  };
};

/** The list's entries, each checked: an id, a package, a real date and a reason. */
export const knownAdvisoriesOf = (listText: string): KnownAdvisory[] => {
  let parsed: unknown;
  try {
    parsed = JSON.parse(listText);
  } catch (error) {
    throw new AdvisoryError(`${LIST_NAME} is not JSON: ${String(error)}`);
  }
  const entries = isRecord(parsed) && Array.isArray(parsed.advisories) ? parsed.advisories : null;
  if (entries === null) {
    throw new AdvisoryError(`${LIST_NAME} must hold an \`advisories\` list`);
  }
  const known = entries.map(knownAdvisoryOf);
  const ids = known.map((entry) => entry.id);
  const twice = ids.filter((id, index) => ids.indexOf(id) !== index);
  if (twice.length > 0) {
    throw new AdvisoryError(`${LIST_NAME} names ${twice.join(", ")} twice`);
  }
  return known;
};

/** The failures and the notes: unlisted advisories and plain fixes fail; the rest is said. */
export const verdictOf = (
  advisories: Advisory[],
  fixes: Fix[],
  known: KnownAdvisory[],
): Verdict => {
  const knownById = new Map(known.map((entry) => [entry.id, entry]));
  const reportedIds = new Set(advisories.map((advisory) => advisory.id));
  const unlisted = advisories
    .filter((advisory) => !knownById.has(advisory.id))
    .map(
      (advisory) =>
        `${advisory.id} (${advisory.severity}) in ${advisory.package}: ${advisory.title}. ` +
        `${advisory.url}. Update past it (an \`overrides\` entry in package.json reaches a ` +
        `package inside another), or list it in ${LIST_NAME} with today's date and why it stays`,
    );
  const plainFixes = fixes
    .filter((fix) => !fix.breaking)
    .map(
      (fix) =>
        `${fix.update} fixes ${fix.vulnerablePackage}, and it is not a breaking change: take it`,
    );
  const breakingFixes = fixes
    .filter((fix) => fix.breaking)
    .map(
      (fix) =>
        `npm offers ${fix.update}, a breaking change, for ${fix.vulnerablePackage}: read it ` +
        "before taking it",
    );
  const stillKnown = advisories
    .filter((advisory) => knownById.has(advisory.id))
    .map((advisory) => {
      const entry = knownById.get(advisory.id) as KnownAdvisory;
      return `${advisory.id} in ${advisory.package}, known since ${entry.known_since}: ${entry.why}`;
    });
  const gone = known
    .filter((entry) => !reportedIds.has(entry.id))
    .map((entry) => `${entry.id} is listed but no longer reported: take it off ${LIST_NAME}`);
  return {
    failures: [...unlisted, ...[...new Set(plainFixes)]],
    notes: [...stillKnown, ...[...new Set(breakingFixes)], ...gone],
  };
};

/** Run `npm audit` against the lockfile alone, and return what it printed, parsed. */
export const auditReport = (demoDirectory: string): unknown => {
  const done = spawnSync("npm", ["audit", "--package-lock-only", "--json"], {
    cwd: demoDirectory,
    encoding: "utf8",
    maxBuffer: LARGEST_REPORT_BYTES,
  });
  if (done.error !== undefined) {
    throw new AdvisoryError(`npm could not be run: ${done.error.message}`);
  }
  try {
    return JSON.parse(done.stdout);
  } catch {
    throw new AdvisoryError(`npm audit printed no report: ${done.stderr.trim() || done.stdout}`);
  }
};

/** Check the lockfile against the list and print the verdict; return the exit code. */
export const main = (): number => {
  try {
    const report = auditReport(DEMO_DIRECTORY);
    const advisories = advisoriesOf(report);
    const known = knownAdvisoriesOf(readFileSync(KNOWN_ADVISORIES_FILE, "utf8"));
    const verdict = verdictOf(advisories, fixesOf(report), known);
    for (const note of verdict.notes) {
      console.log(`note: ${note}`);
    }
    for (const failure of verdict.failures) {
      console.error(`advisories: ${failure}`);
    }
    if (verdict.failures.length > 0) {
      console.error(`advisories: ${verdict.failures.length} to act on`);
      return EXIT_FAILED;
    }
    console.log(
      advisories.length === 0
        ? "advisories: none reported"
        : `advisories: ${advisories.length} reported, each known and without a plain fix`,
    );
    return EXIT_CLEAN;
  } catch (error) {
    if (error instanceof AdvisoryError) {
      console.error(`advisories: ${error.message}`);
      return EXIT_COULD_NOT_RUN;
    }
    throw error;
  }
};

const startedAsCommand =
  process.argv[1] !== undefined &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (startedAsCommand) {
  process.exitCode = main();
}
