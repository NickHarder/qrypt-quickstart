/**
 * The quickstart site as a developer meets it: the page from a token to a key, the language tabs and
 * a copy, the troubleshooting page at the message a wrong token prints, and `llms.txt` for agents.
 *
 * It records the site as the builder writes it into build/site/ (`make e2e` builds it), opened from
 * disk, so the take needs no server and no network.
 */
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import type { Page } from "playwright";
import { defineTake } from "../src/capture/take";

const BUILT_SITE_DIRECTORY = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../../build/site",
);

/** A `file://` URL for a page of the built site. */
const siteUrl = (pageName: string): string =>
  pathToFileURL(path.join(BUILT_SITE_DIRECTORY, pageName)).href;

/** Scroll smoothly until the element sits a little below the top of the window, as a reader would. */
const scrollToNearTop = async (page: Page, selector: string): Promise<void> => {
  await page.evaluate((elementSelector) => {
    const element = document.querySelector(elementSelector);
    if (element !== null) {
      const top = element.getBoundingClientRect().top + window.scrollY - 60;
      window.scrollTo({ top, behavior: "smooth" });
    }
  }, selector);
  await page.waitForTimeout(1400);
};

export default defineTake({
  name: "quickstart",
  run: async ({ page, beat }) => {
    await page.goto(siteUrl("index.html"));
    await beat("landing", async () => {
      await page.waitForTimeout(1500);
      await scrollToNearTop(page, "#step-token");
      await page.waitForTimeout(1200);
    });
    await beat("tabs", async () => {
      await scrollToNearTop(page, "#step-run");
      await page.waitForTimeout(600);
      await page.locator("#tab-node").click();
      await page.waitForTimeout(900);
      await page.locator("#tab-rust").click();
      await page.waitForTimeout(900);
      await page.locator("#tab-python").click();
      await page.waitForTimeout(600);
      await page.getByRole("button", { name: "Copy the Python quickstart" }).click();
      await page.waitForTimeout(900);
    });
    await page.goto(siteUrl("troubleshooting.html"));
    await beat("troubleshooting", async () => {
      await page.waitForTimeout(600);
      await page.locator("#error-401").scrollIntoViewIfNeeded();
      await page.waitForTimeout(1500);
    });
    await page.goto(siteUrl("llms.txt"));
    // The browser shows plain text small; zoomed in as a reader would, so it can be read on video.
    await page.evaluate(() => {
      document.body.style.zoom = "1.7";
    });
    await beat("agents", async () => {
      await page.waitForTimeout(1500);
    });
  },
});
