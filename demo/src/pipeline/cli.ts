/**
 * The demo pipeline's command line. From the demo directory:
 *
 *     npm run demo -- validate                    check storyboard.json and brand.json against the catalog
 *     npm run demo -- catalog                     write catalog.schema.json from the catalog
 *     npm run demo -- capture [--take <name>]     record the takes with Playwright; writes beats.json
 *     npm run demo -- stills                      one still per scene settled and one at its end, from a silent timeline ($0)
 *     npm run demo -- draft [--provider silent]   draft voice, timeline, half-size render, checks ($0)
 *     npm run demo -- voice                       say what the final voice-over would cost, and stop
 *     npm run demo -- voice --confirm             make the final voice-over (PAID)
 *     npm run demo -- voices [--search <word>]    list the final voice's voices to choose from
 *     npm run demo -- render [--provider say]     full-size render from the final voice, then checks ($0)
 *     npm run demo -- approve --scene <id>        record the owner's approval of a scene; it is then locked
 *     npm run demo -- reopen --scene <id>         unlock an approved scene, when the owner asks for a change
 *     npm run demo -- assets                      check the media files against media.lock.json
 *     npm run demo -- record --file <path under public/media> --provenance generated|licensed --note "<how it was made>"
 *                                                 list a generated or licensed media file in media.lock.json
 *
 * The draft voice is Kokoro, free and local, on every machine; `say`, `espeak` and `silent` can be named
 * instead. The final voice is the one `DEMO_VOICE_PROVIDER` in the repository's `.env` names; when it
 * names none, Gemini if `GEMINI_API_KEY` is set and Kokoro if it is not, or if the key does not work.
 *
 * Exit 0: done. Exit 1: a check failed; what failed is printed. Exit 2: it could not run.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import { CaptureError, captureTake, loadTakes } from "../capture/harness";
import {
  type Brand,
  provenanceSchema,
  type Scene,
  type Storyboard,
  type Timeline,
} from "../catalog/schemas";
import { posterSceneOf } from "../poster";
import {
  approvalProblems,
  approveScene,
  loadApprovals,
  reopenScene,
  UnknownSceneError,
} from "./approval";
import { captionCues, captionProblems, toSrt } from "./captions";
import { catalogSchemaText } from "./catalog";
import { ContentError, resolveSceneContent } from "./content";
import { contrastProblems } from "./contrast";
import { loadProjectDotEnv } from "./dotEnv";
import { extractPoster, FinishError, finishVideo, isSilent, measureLoudness } from "./finish";
import { FootageError, loadBeatRows } from "./footage";
import { honestyProblems } from "./honesty";
import { assetProblems, loadManifest, recordMedia } from "./manifest";
import {
  APPROVALS_FILE,
  BEATS_FILE,
  BRAND_FILE,
  CATALOG_SCHEMA_FILE,
  EXAMPLE_SITE_DIRECTORY,
  MANIFEST_FILE,
  MEDIA_DIRECTORY,
  OUTPUT_DIRECTORY,
  REPOSITORY_ROOT,
  STORYBOARD_FILE,
  TAKES_DIRECTORY,
  TIMELINE_FILE,
  WORK_DIRECTORY,
} from "./paths";
import { readingProblems } from "./reading";
import { RenderError, renderVideo } from "./render";
import { renderStills, StillsError } from "./stills";
import { loadBrand, loadStoryboard, ValidationError } from "./storyboard";
import {
  buildTimeline,
  lengthProblems,
  MissingAudioError,
  spokenSeconds,
  timelineSeconds,
} from "./timeline";
import { finishedProblems, ProbeError, probe, verificationProblems } from "./verify";
import { createEspeakProvider, ESPEAK_VOICE, EspeakUnavailableError } from "./voice/espeak";
import { describeEstimate, estimateVoiceCost, isSuspectRead } from "./voice/estimate";
import {
  cachedFinalVoice,
  FinalVoiceError,
  type FinalVoiceName,
  FREE_FINAL_VOICE,
  finalVoiceIsNamed,
  finalVoiceLabel,
  finalVoiceName,
  isFinalVoiceName,
  paidFinalVoice,
} from "./voice/final";
import { GeminiVoiceError, geminiApiKey, listGeminiVoices } from "./voice/gemini";
import { createKokoroProvider, KokoroUnavailableError, listKokoroVoices } from "./voice/kokoro";
import { estimatedSpeechSeconds, type VoiceProvider } from "./voice/provider";
import { createSayProvider, SayUnavailableError } from "./voice/say";
import { createSilentProvider } from "./voice/silent";
import { linesNeedingVoice, type VoiceRun, voiceLines } from "./voice/voiceLines";
import { WavFormatError } from "./wav";

const EXIT_OK = 0;
const EXIT_CHECK_FAILED = 1;
const EXIT_COULD_NOT_RUN = 2;

const DRAFT_SCALE = 0.5;
const FULL_SCALE = 1;
/** The free voice a draft is made with when none is named: Kokoro, on every machine. */
const DRAFT_VOICE = "kokoro";

/** A command line this tool does not understand. */
class UsageError extends Error {}

const loadInputs = (): { storyboard: Storyboard; brand: Brand } => ({
  storyboard: loadStoryboard(STORYBOARD_FILE),
  brand: loadBrand(BRAND_FILE),
});

/** A voice that costs nothing: a draft voice, or silence where there is no voice at all. */
const freeProviderNamed = (providerName: string, brand: Brand): VoiceProvider => {
  switch (providerName) {
    case "kokoro":
      return createKokoroProvider(brand.voice.kokoro_voice);
    case "say":
      return createSayProvider(brand.voice.draft_voice, brand.voice.draft_words_per_minute);
    case "espeak":
      return createEspeakProvider(ESPEAK_VOICE, brand.voice.draft_words_per_minute);
    case "silent":
      return createSilentProvider();
    default:
      throw new UsageError(
        `unknown free voice "${providerName}"; use kokoro, say, espeak or silent`,
      );
  }
};

/** The final voice the repository's `.env` names, read after the `.env` is loaded. */
const configuredFinalVoice = (): FinalVoiceName => {
  loadProjectDotEnv(REPOSITORY_ROOT);
  return finalVoiceName(process.env);
};

const reportProblems = (problems: readonly string[]): number => {
  for (const problem of problems) {
    console.error(`FAIL ${problem}`);
  }
  return problems.length > 0 ? EXIT_CHECK_FAILED : EXIT_OK;
};

/** Voice every line with the provider, build the timeline from the measured clips, and write it. */
const prepareTimeline = async (
  storyboard: Storyboard,
  brand: Brand,
  provider: VoiceProvider,
): Promise<Timeline> => {
  const voiceRun = await voiceLines(storyboard, brand, provider, MEDIA_DIRECTORY);
  const reusedCount = voiceRun.voicedLinesByKey.size - voiceRun.synthesizedKeys.length;
  console.log(
    `voice (${provider.name}): ${voiceRun.synthesizedKeys.length} line(s) voiced, ${reusedCount} reused`,
  );
  const timeline = buildTimeline(storyboard, brand, voiceRun.voicedLinesByKey, provider.name, {
    beatRows: loadBeatRows(BEATS_FILE),
    contentBySceneId: new Map(
      storyboard.scenes.map((scene) => [scene.id, resolveSceneContent(scene, REPOSITORY_ROOT)]),
    ),
  });
  mkdirSync(WORK_DIRECTORY, { recursive: true });
  writeFileSync(TIMELINE_FILE, `${JSON.stringify(timeline, null, 2)}\n`, "utf8");
  console.log(
    `timeline: ${timeline.scenes.length} scene(s), ${timelineSeconds(timeline).toFixed(1)} s, ` +
      `written to ${path.relative(process.cwd(), TIMELINE_FILE)}`,
  );
  return timeline;
};

/**
 * Render the timeline, finish the file (loudness, captions, fast start), and check the result.
 * Returns the problems that fail the cut, and notes that do not.
 */
const renderAndVerify = (
  storyboard: Storyboard,
  timeline: Timeline,
  outputFile: string,
  scale: number,
  isFinalVoice: boolean,
): { problems: string[]; notes: string[] } => {
  const renderedFile = path.join(WORK_DIRECTORY, "render.mp4");
  renderVideo({ timelineFile: TIMELINE_FILE, outputFile: renderedFile, scale });

  const cues = captionCues(timeline);
  const captionsFile = outputFile.replace(/\.mp4$/, ".srt");
  mkdirSync(path.dirname(outputFile), { recursive: true });
  writeFileSync(captionsFile, toSrt(cues), "utf8");
  const loudnessBefore = finishVideo({ renderedFile, captionsFile, outputFile });
  const loudnessAfter = isSilent(loudnessBefore) ? undefined : measureLoudness(outputFile);
  const posterFile = outputFile.replace(/\.mp4$/, ".jpg");
  extractPoster(outputFile, posterFile);

  const probeResult = probe(outputFile);
  // A stand-in voice reads at its own pace, so how fast its captions run says nothing about the
  // final cut: note it, and fail only on the final voice.
  const captionIssues = captionProblems(cues);
  return {
    problems: [
      ...verificationProblems(probeResult, timeline, scale),
      ...finishedProblems(probeResult, outputFile, loudnessAfter),
      ...lengthProblems(storyboard, timeline),
      ...readingProblems(storyboard, measuredSceneSeconds(timeline)),
      ...(isFinalVoice ? captionIssues : []),
    ],
    notes: [
      ...(isFinalVoice ? [] : captionIssues),
      loudnessAfter === undefined
        ? "the audio is silent, so loudness was not normalised"
        : `loudness ${loudnessBefore.integratedLufs.toFixed(1)} LUFS before, ` +
          `${loudnessAfter.integratedLufs.toFixed(1)} LUFS after`,
      `captions: ${cues.length}, in ${path.relative(process.cwd(), captionsFile)} and as a track in the file`,
      describePoster(timeline, posterFile),
    ],
  };
};

/** A scene's length once its clips are measured, by scene. */
const measuredSceneSeconds =
  (timeline: Timeline): ((scene: Scene) => number) =>
  (scene) => {
    const timedScene = timeline.scenes.find((candidate) => candidate.scene.id === scene.id);
    return timedScene === undefined
      ? 0
      : timedScene.duration_in_frames / timeline.frames_per_second;
  };

/** A scene's length estimated from its words, before any clip exists. */
const estimatedSceneSeconds = (scene: Scene): number =>
  Math.max(
    spokenSeconds(scene.lines, (line) => estimatedSpeechSeconds(line.text)),
    scene.min_seconds ?? 0,
  );

const describePoster = (timeline: Timeline, posterFile: string): string => {
  const poster = posterSceneOf(timeline);
  const moment =
    poster === undefined
      ? ""
      : ` (scene "${poster.timedScene.scene.id}" at ${(poster.frameIntoScene / timeline.frames_per_second).toFixed(1)} s)`;
  return `poster: ${path.relative(process.cwd(), posterFile)}, frame 0 of the cut${moment}`;
};

const printNotes = (notes: readonly string[]): void => {
  for (const note of notes) {
    console.log(`note: ${note}`);
  }
};

const runValidate = (): number => {
  const { storyboard, brand } = loadInputs();
  const problems = [
    ...contrastProblems(brand),
    ...approvalProblems(storyboard, loadApprovals(APPROVALS_FILE)),
    ...readingProblems(storyboard, estimatedSceneSeconds),
  ];
  if (problems.length > 0) {
    return reportProblems(problems);
  }
  const lineCount = storyboard.scenes.reduce((total, scene) => total + scene.lines.length, 0);
  console.log(`storyboard: ${storyboard.scenes.length} scene(s), ${lineCount} line(s); valid`);
  return EXIT_OK;
};

/**
 * How long each beat of a take must stay on screen: as long as the lines of the scene that shows it
 * take to say. A line already voiced as a draft is measured; any other is estimated.
 */
const holdSecondsForTake = (storyboard: Storyboard, takeName: string): Map<string, number> => {
  const draftIndexFile = path.join(MEDIA_DIRECTORY, "voice", DRAFT_VOICE, "index.json");
  const draftIndex = existsSync(draftIndexFile)
    ? (JSON.parse(readFileSync(draftIndexFile, "utf8")) as Record<string, { seconds: number }>)
    : {};
  const holdSecondsByBeat = new Map<string, number>();
  for (const scene of storyboard.scenes) {
    if (scene.component === "ScreenRecording" && scene.props.take === takeName) {
      const narrationSeconds = spokenSeconds(
        scene.lines,
        (line) => draftIndex[line.key]?.seconds ?? estimatedSpeechSeconds(line.text),
      );
      holdSecondsByBeat.set(scene.props.beat, Math.max(narrationSeconds, scene.min_seconds ?? 0));
    }
  }
  return holdSecondsByBeat;
};

const runCapture = async (onlyTake: string | undefined): Promise<number> => {
  const { storyboard } = loadInputs();
  const allTakes = await loadTakes(TAKES_DIRECTORY);
  const takes =
    onlyTake === undefined ? allTakes : allTakes.filter((take) => take.name === onlyTake);
  if (takes.length === 0) {
    throw new UsageError(
      onlyTake === undefined
        ? "there are no takes; add one under takes/ (see takes/example.take.ts)"
        : `there is no take named "${onlyTake}"`,
    );
  }
  for (const take of takes) {
    await captureTake(take, {
      mediaDirectory: MEDIA_DIRECTORY,
      beatsFile: BEATS_FILE,
      manifestFile: MANIFEST_FILE,
      exampleSiteDirectory: EXAMPLE_SITE_DIRECTORY,
      holdSecondsByBeat: holdSecondsForTake(storyboard, take.name),
    });
  }
  console.log("capture: beats.json and media.lock.json are updated; commit them");
  return EXIT_OK;
};

const runDraft = async (providerName: string): Promise<number> => {
  const { storyboard, brand } = loadInputs();
  const provenanceProblems = honestyProblems(storyboard, brand, loadManifest(MANIFEST_FILE));
  if (provenanceProblems.length > 0) {
    return reportProblems(provenanceProblems);
  }
  const provider = freeProviderNamed(providerName, brand);
  const timeline = await prepareTimeline(storyboard, brand, provider);
  const draftFile = path.join(OUTPUT_DIRECTORY, "draft.mp4");
  const { problems, notes } = renderAndVerify(storyboard, timeline, draftFile, DRAFT_SCALE, false);
  printNotes(notes);
  if (problems.length > 0) {
    return reportProblems(problems);
  }
  console.log(
    `draft: ${path.relative(process.cwd(), draftFile)} (${timelineSeconds(timeline).toFixed(1)} s, ` +
      `${provider.name} voice, half size). This is a draft: the voice is a stand-in.`,
  );
  return EXIT_OK;
};

/**
 * Make the clips with the final voice. When Gemini was chosen by its key alone, not named, and the
 * key does not work, the owner's rule falls back to Kokoro and says so.
 */
const voiceWithTheRule = async (
  storyboard: Storyboard,
  brand: Brand,
  finalVoice: FinalVoiceName,
): Promise<{ voice: FinalVoiceName; voiceRun: VoiceRun }> => {
  const provider = paidFinalVoice(finalVoice, brand, process.env);
  try {
    return {
      voice: finalVoice,
      voiceRun: await voiceLines(storyboard, brand, provider, MEDIA_DIRECTORY),
    };
  } catch (error) {
    const keyFailed =
      finalVoice === "gemini" &&
      !finalVoiceIsNamed(process.env) &&
      error instanceof GeminiVoiceError;
    if (!keyFailed) {
      throw error;
    }
    console.log(
      `voice: Gemini's key did not work (${error.message}); falling back to ${FREE_FINAL_VOICE}, ` +
        "the free voice. Name DEMO_VOICE_PROVIDER=gemini in the .env to insist on Gemini",
    );
    const freeProvider = paidFinalVoice(FREE_FINAL_VOICE, brand, process.env);
    return {
      voice: FREE_FINAL_VOICE,
      voiceRun: await voiceLines(storyboard, brand, freeProvider, MEDIA_DIRECTORY),
    };
  }
};

/** Without --confirm: the estimate, and nothing else. With it: the paid voice-over. */
const runVoice = async (confirmed: boolean): Promise<number> => {
  const { storyboard, brand } = loadInputs();
  const finalVoice = configuredFinalVoice();
  const cachedProvider = cachedFinalVoice(finalVoice, brand);
  const linesToVoice = linesNeedingVoice(storyboard, brand, cachedProvider, MEDIA_DIRECTORY);
  if (linesToVoice.length === 0) {
    console.log("voice: every line already has its final voice clip; nothing to pay for");
    return EXIT_OK;
  }
  const estimate = estimateVoiceCost(linesToVoice, cachedProvider, new Date());
  if (estimate.dollars === 0) {
    console.log(
      `voice: ${finalVoice} is free and runs on this machine; making ${linesToVoice.length} clip(s), ` +
        `about ${estimate.seconds.toFixed(0)} s of audio`,
    );
  } else {
    console.log(`voice: ${describeEstimate(estimate, `${finalVoice} (${brand.voice.model})`)}`);
    if (!confirmed) {
      console.log(
        "voice: nothing was sent. To make the voice-over, run:  make demo-voice CONFIRM=1",
      );
      return EXIT_OK;
    }
  }

  const { voice: usedVoice, voiceRun } = await voiceWithTheRule(storyboard, brand, finalVoice);
  // Every final clip and their index, so the manifest stays whole after a run that stopped part-way.
  for (const lineKey of voiceRun.voicedLinesByKey.keys()) {
    recordMedia(MANIFEST_FILE, MEDIA_DIRECTORY, `voice/${usedVoice}/${lineKey}.wav`, "voice");
  }
  recordMedia(MANIFEST_FILE, MEDIA_DIRECTORY, `voice/${usedVoice}/index.json`, "voice");
  console.log(
    `voice (${usedVoice}, ${finalVoiceLabel(usedVoice, brand)}): ${voiceRun.synthesizedKeys.length} line(s) voiced; ` +
      "media.lock.json is updated, commit it",
  );
  if (usedVoice !== finalVoice) {
    console.log(
      `voice: the clips are ${usedVoice}'s; render with \`make demo VOICE=${usedVoice}\`, or set ` +
        `DEMO_VOICE_PROVIDER=${usedVoice} in the .env at the repository root`,
    );
  }
  const suspectKeys = linesToVoice
    .filter((line) =>
      isSuspectRead(line.text, voiceRun.voicedLinesByKey.get(line.key)?.durationSeconds ?? 0),
    )
    .map((line) => line.key);
  if (suspectKeys.length > 0) {
    return reportProblems([
      `these reads are far longer or shorter than their text: ${suspectKeys.join(", ")}. ` +
        `Listen to them in public/media/voice/${usedVoice}/ before rendering; a read can stray from its text`,
    ]);
  }
  return EXIT_OK;
};

const runVoices = async (search: string | undefined): Promise<number> => {
  const finalVoice = configuredFinalVoice();
  if (finalVoice === "kokoro") {
    const kokoroVoices = (await listKokoroVoices()).filter(
      (voice) => search === undefined || voice.includes(search),
    );
    for (const voice of kokoroVoices) {
      console.log(voice);
    }
    console.log(
      `voices: ${kokoroVoices.length} listed. Set the one you choose as voice.kokoro_voice in brand.json.`,
    );
    return EXIT_OK;
  }
  const voices = await listGeminiVoices(geminiApiKey(process.env), search);
  for (const voice of voices) {
    console.log(`${voice.name}\t${voice.description}`);
  }
  console.log(
    `voices: ${voices.length} listed. Set the one you choose as voice.name in brand.json.`,
  );
  return EXIT_OK;
};

/** One still per scene once its text has settled, and one at its end, from a silent timeline. */
const runStills = async (): Promise<number> => {
  const { storyboard, brand } = loadInputs();
  const provenanceProblems = honestyProblems(storyboard, brand, loadManifest(MANIFEST_FILE));
  if (provenanceProblems.length > 0) {
    return reportProblems(provenanceProblems);
  }
  const timeline = await prepareTimeline(storyboard, brand, createSilentProvider());
  const stillsDirectory = path.join(OUTPUT_DIRECTORY, "stills");
  const stills = await renderStills(timeline, stillsDirectory, (still) => {
    console.log(`still: ${path.relative(process.cwd(), still.file)} (frame ${still.frame})`);
  });
  console.log(
    `stills: ${stills.length} in ${path.relative(process.cwd(), stillsDirectory)}; ` +
      "look at each for overflow, a collision and low contrast before a render",
  );
  return EXIT_OK;
};

/** The finished cut, at full size. It uses the final voice clips as they are; it never pays for any. */
const runRender = async (namedProvider: string | undefined): Promise<number> => {
  const { storyboard, brand } = loadInputs();
  const provenanceProblems = honestyProblems(storyboard, brand, loadManifest(MANIFEST_FILE));
  if (provenanceProblems.length > 0) {
    return reportProblems(provenanceProblems);
  }
  const finalVoice =
    namedProvider !== undefined && isFinalVoiceName(namedProvider)
      ? namedProvider
      : configuredFinalVoice();
  const usesFinalVoice = namedProvider === undefined || namedProvider === finalVoice;
  const provider = usesFinalVoice
    ? cachedFinalVoice(finalVoice, brand)
    : freeProviderNamed(namedProvider, brand);
  if (usesFinalVoice) {
    const unvoicedLines = linesNeedingVoice(storyboard, brand, provider, MEDIA_DIRECTORY);
    if (unvoicedLines.length > 0) {
      return reportProblems([
        `${unvoicedLines.length} line(s) have no final voice clip, or changed since theirs was made: ` +
          `${unvoicedLines.map((line) => line.key).join(", ")}. Run \`make demo-voice\` for the cost`,
      ]);
    }
  }
  const timeline = await prepareTimeline(storyboard, brand, provider);
  const outputFile = path.join(
    OUTPUT_DIRECTORY,
    usesFinalVoice ? "demo.mp4" : `demo-${provider.name}.mp4`,
  );
  const { problems, notes } = renderAndVerify(
    storyboard,
    timeline,
    outputFile,
    FULL_SCALE,
    usesFinalVoice,
  );
  printNotes(notes);
  if (problems.length > 0) {
    return reportProblems(problems);
  }
  const voiceNote = usesFinalVoice
    ? "final voice"
    : `${provider.name} voice: a stand-in, not the final`;
  console.log(
    `render: ${path.relative(process.cwd(), outputFile)} ` +
      `(${timelineSeconds(timeline).toFixed(1)} s, ${voiceNote})`,
  );
  return EXIT_OK;
};

/** Write the catalog as JSON Schema. `tests/catalog.test.ts` fails while the committed file is stale. */
const runCatalog = (): number => {
  writeFileSync(CATALOG_SCHEMA_FILE, catalogSchemaText(), "utf8");
  console.log(`catalog: wrote ${path.relative(process.cwd(), CATALOG_SCHEMA_FILE)}`);
  return EXIT_OK;
};

const runAssets = (): number => {
  const manifest = loadManifest(MANIFEST_FILE);
  const problems = assetProblems(manifest, MEDIA_DIRECTORY);
  if (problems.length > 0) {
    return reportProblems(problems);
  }
  console.log(`assets: ${Object.keys(manifest).length} media file(s) match media.lock.json`);
  return EXIT_OK;
};

/** The owner's approval of one scene, or the lifting of it. An agent runs these only when told to. */
const runApprove = (sceneId: string | undefined): number => {
  if (sceneId === undefined) {
    throw new UsageError("approve needs --scene <id>");
  }
  approveScene(APPROVALS_FILE, loadInputs().storyboard, sceneId, new Date());
  console.log(`approve: scene "${sceneId}" is approved and locked; commit approved.json`);
  return EXIT_OK;
};

const runReopen = (sceneId: string | undefined): number => {
  if (sceneId === undefined) {
    throw new UsageError("reopen needs --scene <id>");
  }
  const wasApproved = reopenScene(APPROVALS_FILE, sceneId);
  console.log(
    wasApproved
      ? `reopen: scene "${sceneId}" is open for changes; commit approved.json`
      : `reopen: scene "${sceneId}" was not approved; nothing to do`,
  );
  return EXIT_OK;
};

/** List a generated or licensed file in the manifest. Recordings and voice clips list themselves. */
const runRecord = (
  file: string | undefined,
  provenanceName: string | undefined,
  note: string | undefined,
): number => {
  const provenance = provenanceSchema.safeParse(provenanceName);
  if (!file || !provenance.success || note === undefined || note.trim() === "") {
    throw new UsageError(
      'record needs --file <path under public/media>, --provenance generated|licensed and --note "<how it was made, or its licence>"',
    );
  }
  if (provenance.data !== "generated" && provenance.data !== "licensed") {
    throw new UsageError(
      "only generated and licensed files are listed by hand; capture lists recordings and voice lists its clips",
    );
  }
  if (!existsSync(path.join(MEDIA_DIRECTORY, file))) {
    throw new UsageError(`there is no file at public/media/${file}`);
  }
  recordMedia(MANIFEST_FILE, MEDIA_DIRECTORY, file, provenance.data, note.trim());
  console.log(`record: ${file} is listed in media.lock.json as ${provenance.data}; commit it`);
  return EXIT_OK;
};

const main = async (): Promise<number> => {
  const { positionals, values } = parseArgs({
    allowPositionals: true,
    options: {
      provider: { type: "string" },
      take: { type: "string" },
      confirm: { type: "boolean", default: false },
      file: { type: "string" },
      provenance: { type: "string" },
      note: { type: "string" },
      scene: { type: "string" },
      search: { type: "string" },
    },
  });
  const [command] = positionals;
  switch (command) {
    case "validate":
      return runValidate();
    case "catalog":
      return runCatalog();
    case "capture":
      return runCapture(values.take);
    case "stills":
      return runStills();
    case "draft":
      return runDraft(values.provider ?? DRAFT_VOICE);
    case "voice":
      return runVoice(values.confirm);
    case "voices":
      return runVoices(values.search);
    case "render":
      return runRender(values.provider);
    case "approve":
      return runApprove(values.scene);
    case "reopen":
      return runReopen(values.scene);
    case "assets":
      return runAssets();
    case "record":
      return runRecord(values.file, values.provenance, values.note);
    default:
      throw new UsageError(
        `unknown command "${command ?? ""}"; use validate, catalog, capture, stills, draft, voice, voices, render, approve, reopen, assets or record`,
      );
  }
};

main().then(
  (exitCode) => {
    process.exitCode = exitCode;
  },
  (error: unknown) => {
    if (
      error instanceof ValidationError ||
      error instanceof MissingAudioError ||
      error instanceof ContentError ||
      error instanceof FootageError
    ) {
      console.error(`FAIL ${error.message}`);
      process.exitCode = EXIT_CHECK_FAILED;
      return;
    }
    if (
      error instanceof UsageError ||
      error instanceof UnknownSceneError ||
      error instanceof RenderError ||
      error instanceof FinishError ||
      error instanceof ProbeError ||
      error instanceof CaptureError ||
      error instanceof GeminiVoiceError ||
      error instanceof FinalVoiceError ||
      error instanceof SayUnavailableError ||
      error instanceof EspeakUnavailableError ||
      error instanceof KokoroUnavailableError ||
      error instanceof StillsError ||
      error instanceof WavFormatError
    ) {
      console.error(`demo: ${error.message}`);
      process.exitCode = EXIT_COULD_NOT_RUN;
      return;
    }
    throw error;
  },
);
