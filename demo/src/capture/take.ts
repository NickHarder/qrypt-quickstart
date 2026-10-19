/** What a take file exports. A take is the only product-specific code in the demo. */
import type { Page } from "playwright";

export type TakeContext = {
  page: Page;
  /**
   * Mark a beat: a stretch of the recording a scene can show. The action runs, then the page is held
   * until the lines of the scene that shows this beat would have been said, so the footage is never
   * shorter than its narration.
   */
  beat: (key: string, action: () => Promise<void>) => Promise<void>;
  /** A `file://` URL for a page of the example site that ships with the kit. */
  exampleSiteUrl: (relativePath: string) => string;
};

export type Take = {
  /** Lowercase, digits, hyphens and underscores: it names the video file. */
  name: string;
  run: (context: TakeContext) => Promise<void>;
};

export const defineTake = (take: Take): Take => take;
