/**
 * Read and write WAV files without any external tool.
 *
 * Scene lengths come from the measured length of each narration clip, so this has to be exact: it
 * walks the RIFF chunks rather than assuming where the audio data starts.
 */
import { readFileSync, writeFileSync } from "node:fs";

/** A file that is not a PCM WAV this code can measure. */
export class WavFormatError extends Error {}

const RIFF_HEADER_BYTES = 12;
const CHUNK_HEADER_BYTES = 8;

type WavFormat = { bytesPerSecond: number };

/** Return how long the audio in a WAV buffer lasts, in seconds. */
export const wavDurationSeconds = (wavBytes: Buffer, fileLabel = "the WAV file"): number => {
  if (
    wavBytes.length < RIFF_HEADER_BYTES ||
    wavBytes.toString("ascii", 0, 4) !== "RIFF" ||
    wavBytes.toString("ascii", 8, 12) !== "WAVE"
  ) {
    throw new WavFormatError(`${fileLabel} is not a RIFF/WAVE file`);
  }

  let chunkOffset = RIFF_HEADER_BYTES;
  let format: WavFormat | undefined;
  while (chunkOffset + CHUNK_HEADER_BYTES <= wavBytes.length) {
    const chunkName = wavBytes.toString("ascii", chunkOffset, chunkOffset + 4);
    const declaredChunkBytes = wavBytes.readUInt32LE(chunkOffset + 4);
    const chunkDataOffset = chunkOffset + CHUNK_HEADER_BYTES;
    if (chunkName === "fmt ") {
      format = { bytesPerSecond: wavBytes.readUInt32LE(chunkDataOffset + 8) };
    }
    if (chunkName === "data") {
      if (format === undefined || format.bytesPerSecond === 0) {
        throw new WavFormatError(`${fileLabel} has audio data before a usable fmt chunk`);
      }
      // A streamed file may declare a size it never went back to fill in; trust what is really there.
      const bytesInFile = wavBytes.length - chunkDataOffset;
      const audioBytes = Math.min(declaredChunkBytes, bytesInFile) || bytesInFile;
      return audioBytes / format.bytesPerSecond;
    }
    // Chunks are padded to an even number of bytes.
    chunkOffset = chunkDataOffset + declaredChunkBytes + (declaredChunkBytes % 2);
  }
  throw new WavFormatError(`${fileLabel} has no data chunk`);
};

export const wavFileDurationSeconds = (wavFile: string): number =>
  wavDurationSeconds(readFileSync(wavFile), wavFile);

const SILENCE_SAMPLE_RATE = 24000;
const SILENCE_BYTES_PER_SAMPLE = 2;

/** Build a mono 16-bit WAV of pure silence, of the given length. */
export const silentWav = (durationSeconds: number): Buffer => {
  const sampleCount = Math.round(durationSeconds * SILENCE_SAMPLE_RATE);
  const audioBytes = sampleCount * SILENCE_BYTES_PER_SAMPLE;
  const header = Buffer.alloc(44);
  header.write("RIFF", 0, "ascii");
  header.writeUInt32LE(36 + audioBytes, 4);
  header.write("WAVE", 8, "ascii");
  header.write("fmt ", 12, "ascii");
  header.writeUInt32LE(16, 16); // fmt chunk size
  header.writeUInt16LE(1, 20); // PCM
  header.writeUInt16LE(1, 22); // mono
  header.writeUInt32LE(SILENCE_SAMPLE_RATE, 24);
  header.writeUInt32LE(SILENCE_SAMPLE_RATE * SILENCE_BYTES_PER_SAMPLE, 28); // bytes per second
  header.writeUInt16LE(SILENCE_BYTES_PER_SAMPLE, 32); // block align
  header.writeUInt16LE(16, 34); // bits per sample
  header.write("data", 36, "ascii");
  header.writeUInt32LE(audioBytes, 40);
  return Buffer.concat([header, Buffer.alloc(audioBytes)]);
};

export const writeSilentWav = (wavFile: string, durationSeconds: number): void => {
  writeFileSync(wavFile, silentWav(durationSeconds));
};
