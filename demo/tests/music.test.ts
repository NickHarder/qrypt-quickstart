import { describe, expect, it } from "vitest";
import { musicVolumeAtFrame } from "../src/music";

const FPS = 30;
const levels = { volume: 0.2, volumeUnderVoice: 0.05 };
const windows = [{ startFrame: 300, endFrame: 450 }];
const TOTAL_FRAMES = 1800;

const volumeAt = (frame: number): number =>
  musicVolumeAtFrame(frame, windows, levels, FPS, TOTAL_FRAMES);

describe("musicVolumeAtFrame", () => {
  it("plays at full level away from any line", () => {
    expect(volumeAt(150)).toBeCloseTo(0.2, 5);
    expect(volumeAt(900)).toBeCloseTo(0.2, 5);
  });

  it("drops under a spoken line", () => {
    expect(volumeAt(300)).toBeCloseTo(0.05, 5);
    expect(volumeAt(375)).toBeCloseTo(0.05, 5);
    expect(volumeAt(450)).toBeCloseTo(0.05, 5);
  });

  it("ramps down before a line and back up after it", () => {
    const halfwayDown = volumeAt(294);
    expect(halfwayDown).toBeGreaterThan(0.05);
    expect(halfwayDown).toBeLessThan(0.2);
    expect(volumeAt(456)).toBeCloseTo(halfwayDown, 5);
  });

  it("fades in at the start and out at the end", () => {
    expect(volumeAt(0)).toBe(0);
    expect(volumeAt(22)).toBeLessThan(0.2);
    expect(volumeAt(TOTAL_FRAMES)).toBe(0);
    expect(volumeAt(TOTAL_FRAMES - 45)).toBeCloseTo(0.1, 5);
  });
});
