import { describe, expect, it } from "vitest";
import { silentWav, WavFormatError, wavDurationSeconds } from "../src/pipeline/wav";

describe("wavDurationSeconds", () => {
  it("measures a clip to the sample", () => {
    expect(wavDurationSeconds(silentWav(2.5))).toBeCloseTo(2.5, 4);
    expect(wavDurationSeconds(silentWav(0.1))).toBeCloseTo(0.1, 4);
  });

  it("skips chunks that come before the audio data", () => {
    const plainWav = silentWav(1);
    const fillerChunk = Buffer.alloc(8 + 6);
    fillerChunk.write("FLLR", 0, "ascii");
    fillerChunk.writeUInt32LE(6, 4);
    const withFiller = Buffer.concat([
      plainWav.subarray(0, 36),
      fillerChunk,
      plainWav.subarray(36),
    ]);
    expect(wavDurationSeconds(withFiller)).toBeCloseTo(1, 4);
  });

  it("trusts the bytes that are really there when the declared size is wrong", () => {
    const streamedWav = Buffer.from(silentWav(1));
    streamedWav.writeUInt32LE(0xffffffff, 40);
    expect(wavDurationSeconds(streamedWav)).toBeCloseTo(1, 4);
  });

  it("refuses a file that is not a WAV", () => {
    expect(() => wavDurationSeconds(Buffer.from("not audio at all"))).toThrow(WavFormatError);
  });
});
