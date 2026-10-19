/**
 * The catalog as JSON Schema: the file an agent reads to learn what a storyboard may contain.
 *
 * It is generated from the Zod schemas, which are what the pipeline actually enforces, so the two
 * cannot disagree. The rules a schema cannot express (unique ids, unique line keys, a length for a
 * scene with no lines) are stated in its description.
 */
import { z } from "zod";
import { storyboardSchema } from "../catalog/schemas";

const CATALOG_DESCRIPTION =
  "A demo storyboard. Each scene names one catalog component and gives exactly the props that " +
  "component declares; anything else is rejected. Also enforced: scene ids are unique; line keys " +
  "are unique across the storyboard; a scene with no lines sets min_seconds. A scene lasts as long " +
  "as its lines take to say.";

export const catalogSchemaText = (): string => {
  const jsonSchema = z.toJSONSchema(storyboardSchema, { io: "input" });
  return `${JSON.stringify({ ...jsonSchema, description: CATALOG_DESCRIPTION }, null, 2)}\n`;
};
