/**
 * Captions, cut from the words of each line and the time the line really takes.
 *
 * The rules are the ones readers need: at most two lines of 42 characters, on screen for at least
 * 1.2 seconds, and never faster than 17 characters a second. A caption may stay up a little after its
 * line ends, but never into the next line.
 */
import type { Timeline } from "../catalog/schemas";

export const MAX_CAPTION_LINES = 2;
export const MAX_CHARACTERS_PER_LINE = 42;
export const MIN_CAPTION_SECONDS = 1.2;
export const MAX_CHARACTERS_PER_SECOND = 17;
/** A caption ends at least this long before the next line starts. */
const GAP_BEFORE_NEXT_LINE_SECONDS = 0.2;
/** How long a line's captions may stay up after the line has been said. */
const MAX_LINGER_SECONDS = 1.5;

const MAX_CAPTION_CHARACTERS = MAX_CAPTION_LINES * MAX_CHARACTERS_PER_LINE;

export type CaptionCue = { startSeconds: number; endSeconds: number; lines: string[] };

/** True when the text can be laid out on at most two lines without either running long. */
const fitsOneCaption = (captionText: string): boolean => {
  if (captionText.length <= MAX_CHARACTERS_PER_LINE) {
    return true;
  }
  if (captionText.length > MAX_CAPTION_CHARACTERS) {
    return false;
  }
  const words = captionText.split(" ");
  return words.some(
    (_, splitIndex) =>
      splitIndex > 0 &&
      words.slice(0, splitIndex).join(" ").length <= MAX_CHARACTERS_PER_LINE &&
      words.slice(splitIndex).join(" ").length <= MAX_CHARACTERS_PER_LINE,
  );
};

/**
 * Even out the last two captions of a sentence broken word by word, so its last words are not left
 * alone on screen for less than the minimum time: their words are split where both captions fit and
 * their lengths are closest.
 */
const balanceLastTwoCaptions = (sentenceCaptions: string[]): string[] => {
  if (sentenceCaptions.length < 2) {
    return sentenceCaptions;
  }
  const earlierCaptions = sentenceCaptions.slice(0, -2);
  const lastTwoWords = sentenceCaptions.slice(-2).join(" ").split(" ");
  const candidateSplits = lastTwoWords
    .map((_, splitIndex) => ({
      first: lastTwoWords.slice(0, splitIndex).join(" "),
      second: lastTwoWords.slice(splitIndex).join(" "),
    }))
    .filter(
      (split) =>
        split.first !== "" &&
        split.second !== "" &&
        fitsOneCaption(split.first) &&
        fitsOneCaption(split.second),
    );
  const mostEvenSplit = candidateSplits.reduce<{ first: string; second: string } | undefined>(
    (best, split) =>
      best === undefined ||
      Math.abs(split.first.length - split.second.length) <
        Math.abs(best.first.length - best.second.length)
        ? split
        : best,
    undefined,
  );
  return mostEvenSplit === undefined
    ? sentenceCaptions
    : [...earlierCaptions, mostEvenSplit.first, mostEvenSplit.second];
};

/**
 * Break a line into captions. Whole sentences are kept together and share a caption while they fit,
 * so a two-word sentence is not flashed on its own; a sentence too long for one caption is broken
 * between words.
 */
export const splitIntoCaptionTexts = (text: string): string[] => {
  // A sentence ends at `.`, `!` or `?` (and any closing quote or bracket) where a space follows, so
  // "$0.02", "Node.js" and "example.com" stay whole.
  const sentences = text
    .split(/(?<=[.!?]["')\]]*)\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  const captionTexts: string[] = [];
  let currentCaption = "";
  const startNewCaption = (firstText: string): void => {
    if (currentCaption !== "") {
      captionTexts.push(currentCaption);
    }
    currentCaption = firstText;
  };
  for (const sentence of sentences) {
    const withSentence = currentCaption === "" ? sentence : `${currentCaption} ${sentence}`;
    if (fitsOneCaption(withSentence)) {
      currentCaption = withSentence;
    } else if (fitsOneCaption(sentence)) {
      startNewCaption(sentence);
    } else {
      // The sentence alone is too long: fill captions word by word, then even out the last two.
      startNewCaption("");
      const firstCaptionOfSentence = captionTexts.length;
      for (const word of sentence.split(/\s+/)) {
        const withWord = currentCaption === "" ? word : `${currentCaption} ${word}`;
        if (fitsOneCaption(withWord) || currentCaption === "") {
          currentCaption = withWord;
        } else {
          startNewCaption(word);
        }
      }
      const sentenceCaptions = [...captionTexts.splice(firstCaptionOfSentence), currentCaption];
      const balancedCaptions = balanceLastTwoCaptions(sentenceCaptions);
      captionTexts.push(...balancedCaptions.slice(0, -1));
      currentCaption = balancedCaptions.at(-1) ?? "";
    }
  }
  return currentCaption === "" ? captionTexts : [...captionTexts, currentCaption];
};

/** Lay a caption's text out on at most two lines, as evenly as the words allow. */
export const wrapCaption = (captionText: string): string[] => {
  if (captionText.length <= MAX_CHARACTERS_PER_LINE) {
    return [captionText];
  }
  const words = captionText.split(" ");
  let bestSplitIndex = 1;
  let smallestDifference = Number.POSITIVE_INFINITY;
  for (let splitIndex = 1; splitIndex < words.length; splitIndex += 1) {
    const firstLine = words.slice(0, splitIndex).join(" ");
    const secondLine = words.slice(splitIndex).join(" ");
    const fits =
      firstLine.length <= MAX_CHARACTERS_PER_LINE && secondLine.length <= MAX_CHARACTERS_PER_LINE;
    const difference = Math.abs(firstLine.length - secondLine.length);
    if (fits && difference < smallestDifference) {
      bestSplitIndex = splitIndex;
      smallestDifference = difference;
    }
  }
  return [words.slice(0, bestSplitIndex).join(" "), words.slice(bestSplitIndex).join(" ")];
};

/** Every caption of the cut, in order, in seconds from the start of the video. */
export const captionCues = (timeline: Timeline): CaptionCue[] => {
  const framesPerSecond = timeline.frames_per_second;
  const spokenLines = timeline.scenes.flatMap((timedScene) =>
    timedScene.cues.map((cue) => ({
      text: cue.text,
      startSeconds: (timedScene.from_frame + cue.from_frame) / framesPerSecond,
      endSeconds:
        (timedScene.from_frame + cue.from_frame + cue.duration_in_frames) / framesPerSecond,
    })),
  );
  const videoEndSeconds = timeline.duration_in_frames / framesPerSecond;

  return spokenLines.flatMap((spokenLine, lineIndex) => {
    const nextLineStartSeconds = spokenLines[lineIndex + 1]?.startSeconds ?? videoEndSeconds;
    // The line's captions share a window: from when it starts to a little after it ends, and never
    // into the next line.
    const windowEndSeconds = Math.max(
      spokenLine.endSeconds,
      Math.min(
        nextLineStartSeconds - GAP_BEFORE_NEXT_LINE_SECONDS,
        spokenLine.endSeconds + MAX_LINGER_SECONDS,
      ),
    );
    const windowSeconds = windowEndSeconds - spokenLine.startSeconds;
    const captionTexts = splitIntoCaptionTexts(spokenLine.text);
    const totalCharacters = captionTexts.reduce(
      (total, captionText) => total + captionText.length,
      0,
    );

    let captionStartSeconds = spokenLine.startSeconds;
    return captionTexts.map((captionText) => {
      // Each caption gets the share of the window that its share of the characters earns.
      const captionEndSeconds =
        captionStartSeconds + windowSeconds * (captionText.length / totalCharacters);
      const cue: CaptionCue = {
        startSeconds: captionStartSeconds,
        endSeconds: captionEndSeconds,
        lines: wrapCaption(captionText),
      };
      captionStartSeconds = captionEndSeconds;
      return cue;
    });
  });
};

/** Every caption that breaks a reading rule; empty when all can be read. */
export const captionProblems = (cues: readonly CaptionCue[]): string[] =>
  cues.flatMap((cue, cueIndex) => {
    const label = `caption ${cueIndex + 1} ("${cue.lines.join(" / ").slice(0, 40)}")`;
    const seconds = cue.endSeconds - cue.startSeconds;
    const characterCount = cue.lines.join(" ").length;
    const previousCue = cues[cueIndex - 1];
    return [
      ...(cue.lines.length > MAX_CAPTION_LINES ? [`${label} has ${cue.lines.length} lines`] : []),
      ...cue.lines
        .filter((line) => line.length > MAX_CHARACTERS_PER_LINE)
        .map((line) => `${label} has a line of ${line.length} characters`),
      ...(seconds < MIN_CAPTION_SECONDS - 0.001
        ? [
            `${label} is on screen for ${seconds.toFixed(2)} s; the minimum is ${MIN_CAPTION_SECONDS} s`,
          ]
        : []),
      ...(characterCount / seconds > MAX_CHARACTERS_PER_SECOND + 0.001
        ? [
            `${label} runs at ${(characterCount / seconds).toFixed(1)} characters a second; ` +
              `the limit is ${MAX_CHARACTERS_PER_SECOND}. The line is spoken too fast to read: slow it or shorten it`,
          ]
        : []),
      ...(previousCue !== undefined && cue.startSeconds < previousCue.endSeconds - 0.001
        ? [`${label} starts before the caption before it has ended`]
        : []),
    ];
  });

const srtTimestamp = (seconds: number): string => {
  const totalMilliseconds = Math.round(seconds * 1000);
  const hours = Math.floor(totalMilliseconds / 3_600_000);
  const minutes = Math.floor((totalMilliseconds % 3_600_000) / 60_000);
  const wholeSeconds = Math.floor((totalMilliseconds % 60_000) / 1000);
  const milliseconds = totalMilliseconds % 1000;
  const padded = (value: number, width: number): string => String(value).padStart(width, "0");
  return `${padded(hours, 2)}:${padded(minutes, 2)}:${padded(wholeSeconds, 2)},${padded(milliseconds, 3)}`;
};

export const toSrt = (cues: readonly CaptionCue[]): string =>
  cues
    .map(
      (cue, cueIndex) =>
        `${cueIndex + 1}\n${srtTimestamp(cue.startSeconds)} --> ${srtTimestamp(cue.endSeconds)}\n` +
        `${cue.lines.join("\n")}\n`,
    )
    .join("\n");
