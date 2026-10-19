/**
 * The example take. It records the small page in example-site/, so the whole pipeline can be tried
 * before there is a product to film. Replace it with takes of the real product.
 *
 * A take drives the product the way a person would, and wraps each stretch a scene will show in
 * `beat()`. Resetting the product before a take is this file's job too.
 */
import { defineTake } from "../src/capture/take";

export default defineTake({
  name: "example",
  run: async ({ page, beat, exampleSiteUrl }) => {
    await page.goto(exampleSiteUrl("index.html"));
    await beat("ask", async () => {
      await page
        .getByLabel("Question")
        .pressSequentially("What was the March invoice total?", { delay: 45 });
      await page.getByRole("button", { name: "Ask" }).click();
      await page.getByTestId("answer").waitFor();
    });
  },
});
