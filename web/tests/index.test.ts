/** The starter's one function, held to what it promises. */
import { describe, expect, it } from "vitest";

import { greetingFor } from "../src/index.js";

describe("greetingFor", () => {
  it("greets a person by the name they give, without the spaces around it", () => {
    expect(greetingFor("  Ada ")).toBe("Hello, Ada.");
  });
});
