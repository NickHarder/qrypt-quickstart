/**
 * The free local voice: Kokoro, an open-weight text-to-speech model of 82 million parameters, run on
 * this machine by kokoro-js. No key and no price. The first run downloads the model, about 90 MB,
 * into `~/.cache/kokoro-js`, or into `KOKORO_CACHE_DIR`. It is the draft voice everywhere, and the
 * final voice when the repository's `.env` names it.
 */
import { homedir } from "node:os";
import path from "node:path";
import type { KokoroTTS } from "kokoro-js";
import { FREE, type VoiceProvider, type VoiceRequest } from "./provider";

export const KOKORO_MODEL = "onnx-community/Kokoro-82M-v1.0-ONNX";
/** The eight-bit weights: the smallest download, with the same voices. */
const KOKORO_DTYPE = "q8";
/** The voice a project starts with; `make demo-voices` lists the others. */
export const KOKORO_DEFAULT_VOICE = "af_heart";

/** The model could not be loaded, or the voice named is not one of its. */
export class KokoroUnavailableError extends Error {}

type LoadedModel = KokoroTTS;

/** The model is loaded once for the process; a load that failed is forgotten, so the next call tries again. */
const modelCache: { loading?: Promise<LoadedModel> } = {};

export const kokoroCacheDirectory = (environment: NodeJS.ProcessEnv): string =>
  environment.KOKORO_CACHE_DIR ?? path.join(homedir(), ".cache", "kokoro-js");

const describe = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

/**
 * The libraries are loaded only here, when a line is to be spoken: importing them installs an
 * exception handler of their own in the process, which every other command is better without.
 */
const loadFresh = async (environment: NodeJS.ProcessEnv): Promise<LoadedModel> => {
  const [{ env }, { KokoroTTS: Kokoro }] = await Promise.all([
    import("@huggingface/transformers"),
    import("kokoro-js"),
  ]);
  env.cacheDir = kokoroCacheDirectory(environment);
  return Kokoro.from_pretrained(KOKORO_MODEL, { dtype: KOKORO_DTYPE, device: "cpu" });
};

const loadModel = (environment: NodeJS.ProcessEnv): Promise<LoadedModel> => {
  modelCache.loading ??= loadFresh(environment).catch((error: unknown) => {
    modelCache.loading = undefined;
    throw new KokoroUnavailableError(
      `the Kokoro model could not be loaded (${describe(error)}). The first run downloads it from ` +
        `Hugging Face into ${kokoroCacheDirectory(environment)}; check the network, or use ` +
        "--provider espeak, say or silent",
    );
  });
  return modelCache.loading;
};

const voiceIdOf = (model: LoadedModel, voiceName: string): keyof typeof model.voices => {
  if (!Object.hasOwn(model.voices, voiceName)) {
    throw new KokoroUnavailableError(
      `"${voiceName}" is not a Kokoro voice; the voices are ${Object.keys(model.voices).join(", ")}`,
    );
  }
  return voiceName as keyof typeof model.voices;
};

/** The names of every voice the model has, for `make demo-voices`. */
export const listKokoroVoices = async (
  environment: NodeJS.ProcessEnv = process.env,
): Promise<string[]> => Object.keys((await loadModel(environment)).voices);

export const createKokoroProvider = (
  voiceName: string,
  environment: NodeJS.ProcessEnv = process.env,
): VoiceProvider => ({
  name: "kokoro",
  fingerprint: () => `kokoro:${KOKORO_MODEL}:${KOKORO_DTYPE}:${voiceName}`,
  dollarsPerTenSeconds: FREE,
  synthesize: async (request: VoiceRequest, outputFile: string): Promise<void> => {
    const model = await loadModel(environment);
    const audio = await model.generate(request.text, { voice: voiceIdOf(model, voiceName) });
    await audio.save(outputFile);
  },
});
