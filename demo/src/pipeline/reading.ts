/**
 * A viewer must be able to read what is on screen. The floor: 0.3 s a word and at least 1.2 s for a
 * sentence, 0.8 s for a label of up to three words, counted from the moment the whole text is in,
 * since a line may come in fast and then hold. A scene is as long as its narration, so a scene whose
 * text needs longer than that gets a line, a `min_seconds`, or less copy; never a faster viewer.
 */
import type { Scene, Storyboard } from "../catalog/schemas";

export const SECONDS_PER_WORD = 0.3;
export const SENTENCE_FLOOR_SECONDS = 1.2;
export const LABEL_SECONDS = 0.8;
const LABEL_WORDS_AT_MOST = 3;
/** A key phrase fades in and out over this long at each end of its time on screen. */
export const KEY_PHRASE_FADE_SECONDS = 0.3;

/**
 * When each component's text is whole on screen, in seconds after its scene starts. These follow the
 * components' own animations; a component that changes its timing changes its number here.
 */
const TITLE_SETTLED_SECONDS = 0.6;
const SUBTITLE_SETTLED_SECONDS = 1.0;
const STATEMENT_SETTLED_SECONDS = 0.5;
const DETAIL_SETTLED_SECONDS = 1.1;
const END_CARD_SETTLED_SECONDS = 0.5;
const FIRST_METRIC_SETTLED_SECONDS = 0.7;
const SECONDS_BETWEEN_METRICS = 0.25;
/** A scene with nothing to read settles once its first second has passed. */
const DEFAULT_SETTLED_SECONDS = 1.0;

const wordCount = (text: string): number => text.trim().split(/\s+/).filter(Boolean).length;

/** How long one piece of text takes to read: a label, or a sentence at the floor. */
export const readingSeconds = (text: string): number => {
  const words = wordCount(text);
  return words <= LABEL_WORDS_AT_MOST
    ? LABEL_SECONDS
    : Math.max(SENTENCE_FLOOR_SECONDS, words * SECONDS_PER_WORD);
};

/** What a scene asks a viewer to read, and when all of it is on screen. */
export type ReadingNeed = { readingSeconds: number; settledSeconds: number };

const total = (texts: readonly (string | undefined)[]): number =>
  texts.reduce<number>((sum, text) => sum + (text === undefined ? 0 : readingSeconds(text)), 0);

export const readingNeed = (scene: Scene): ReadingNeed => {
  switch (scene.component) {
    case "TitleCard":
      return {
        readingSeconds: total([scene.props.title, scene.props.subtitle]),
        settledSeconds:
          scene.props.subtitle === undefined ? TITLE_SETTLED_SECONDS : SUBTITLE_SETTLED_SECONDS,
      };
    case "Statement":
      return {
        readingSeconds: total([scene.props.text, scene.props.detail]),
        settledSeconds:
          scene.props.detail === undefined ? STATEMENT_SETTLED_SECONDS : DETAIL_SETTLED_SECONDS,
      };
    case "EndCard":
      return {
        readingSeconds: total([scene.props.title, ...scene.props.links]),
        settledSeconds: END_CARD_SETTLED_SECONDS,
      };
    case "MetricCards":
      return {
        readingSeconds: total([
          scene.props.title,
          ...scene.props.metrics.map((metric) => `${metric.value} ${metric.label}`),
        ]),
        settledSeconds:
          FIRST_METRIC_SETTLED_SECONDS + SECONDS_BETWEEN_METRICS * (scene.props.metrics.length - 1),
      };
    case "Illustration":
      return { readingSeconds: total([scene.props.caption]), settledSeconds: 0 };
    // Footage is watched, not read, and its key phrases are checked one by one below; code and a
    // terminal's output are paced by their components.
    default:
      return { readingSeconds: 0, settledSeconds: DEFAULT_SETTLED_SECONDS };
  }
};

/** When a scene's text is whole on screen: where a poster frame or a still is worth taking. */
/**
 * Seconds are added in tenths, which floating point holds only nearly: 0.8 + 0.8 + 0.8 is
 * 2.4000000000000004. A difference this small is that noise, not a scene too short to read.
 */
const SECONDS_NOISE = 1e-6;

const isLongEnough = (wholeSeconds: number, neededSeconds: number): boolean =>
  wholeSeconds + SECONDS_NOISE >= neededSeconds;

/** A length to advise, rounded up to the tenth, so that the advice given is always enough. */
const advisedSeconds = (seconds: number): string =>
  (Math.ceil(seconds * 10 - SECONDS_NOISE) / 10).toFixed(1);

export const settledSeconds = (scene: Scene): number =>
  Math.max(readingNeed(scene).settledSeconds, DEFAULT_SETTLED_SECONDS);

const keyPhraseProblems = (scene: Scene): string[] =>
  scene.component !== "ScreenRecording"
    ? []
    : scene.props.key_phrases.flatMap((phrase) => {
        const needed = readingSeconds(phrase.text);
        const wholeFor = phrase.for_seconds - 2 * KEY_PHRASE_FADE_SECONDS;
        return isLongEnough(wholeFor, needed)
          ? []
          : [
              `scene "${scene.id}": the key phrase "${phrase.text}" needs ${needed.toFixed(1)} s to ` +
                `read and is whole for ${Math.max(0, wholeFor).toFixed(1)} s of its ${phrase.for_seconds} s; ` +
                `give it for_seconds of ${advisedSeconds(needed + 2 * KEY_PHRASE_FADE_SECONDS)} or more`,
            ];
      });

/**
 * Every scene whose text cannot be read in the time it is whole on screen. `secondsOf` gives a
 * scene's length: estimated from its words before a draft, measured from its clips after one.
 */
export const readingProblems = (
  storyboard: Storyboard,
  secondsOf: (scene: Scene) => number,
): string[] =>
  storyboard.scenes.flatMap((scene) => {
    const need = readingNeed(scene);
    const wholeFor = secondsOf(scene) - need.settledSeconds;
    const textProblems =
      need.readingSeconds === 0 || isLongEnough(wholeFor, need.readingSeconds)
        ? []
        : [
            `scene "${scene.id}": its text needs ${need.readingSeconds.toFixed(1)} s to read and is ` +
              `whole on screen for ${Math.max(0, wholeFor).toFixed(1)} s; add a line, set min_seconds to ` +
              `${advisedSeconds(need.settledSeconds + need.readingSeconds)} or more, or cut copy`,
          ];
    return [...textProblems, ...keyPhraseProblems(scene)];
  });
