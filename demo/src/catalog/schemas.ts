/**
 * The catalog: the contract between whoever writes a storyboard and the components that render it.
 *
 * A storyboard may use only the components listed here, with exactly the props each one declares.
 * `catalog.schema.json` is generated from this file; nothing else describes what a scene may hold.
 */
import { z } from "zod";

/** Identifiers used in file names and as lookup keys: lowercase, digits, hyphen and underscore. */
const identifierSchema = z
  .string()
  .regex(/^[a-z0-9][a-z0-9_-]*$/, "use lowercase letters, digits, hyphens and underscores");

const hexColorSchema = z.string().regex(/^#[0-9A-Fa-f]{6}$/, "use a six-digit hex color");

/** One spoken line. Its measured audio length is what sets the length of its scene. */
export const lineSchema = z.strictObject({
  key: identifierSchema,
  text: z.string().min(1),
  /** Delivery direction for the final voice, for example "warm, a little slower". */
  style: z.string().min(1).optional(),
  /** Silence before the line, in seconds. Defaults to the standard lead-in. */
  pause_before_seconds: z.number().min(0).max(5).optional(),
});

export const titleCardPropsSchema = z
  .strictObject({
    title: z.string().min(1),
    subtitle: z.string().min(1).optional(),
  })
  .describe("The opening card: the title, and optionally one line under it.");

export const endCardPropsSchema = z
  .strictObject({
    title: z.string().min(1),
    /** Where to find the work: a URL, a repository path, a document name. */
    links: z.array(z.string().min(1)).max(4).default([]),
  })
  .describe("The closing card: the title again, and up to four places to find the work.");

/** Words put on screen over a recording, at a moment of the scene. */
export const keyPhraseSchema = z.strictObject({
  text: z.string().min(1).max(60),
  /** Seconds after the scene starts. */
  at_seconds: z.number().min(0),
  for_seconds: z.number().positive().max(10).default(3),
});

export const screenRecordingPropsSchema = z
  .strictObject({
    /** The take, as named in its file under takes/. */
    take: identifierSchema,
    /** The beat of that take to show, as named in the take's `beat()` call. */
    beat: identifierSchema,
    /** Seconds to cut from the start and the end of the beat. */
    trim: z
      .strictObject({
        head_seconds: z.number().min(0).default(0),
        tail_seconds: z.number().min(0).default(0),
      })
      .optional(),
    /** Up to three phrases shown over the recording. */
    key_phrases: z.array(keyPhraseSchema).max(3).default([]),
  })
  .describe(
    "A beat of a real Playwright recording of the product. `take` and `beat` name a beat in beats.json; the take must be recorded first. Product footage is never generated.",
  );

/** A path inside the repository, written from its root: no leading slash and no `..`. */
const repositoryPathSchema = z
  .string()
  .min(1)
  .refine(
    (value) => !value.startsWith("/") && !value.split("/").includes(".."),
    "give a path from the repository root, without a leading slash or ..",
  );

/** A media file under public/media/, such as generated/corridor.mp4. */
const mediaPathSchema = z
  .string()
  .min(1)
  .refine(
    (value) => !value.startsWith("/") && !value.split("/").includes(".."),
    "give a path under public/media/, without a leading slash or ..",
  );

export const statementPropsSchema = z
  .strictObject({
    text: z.string().min(1).max(160),
    /** A smaller line under the statement. */
    detail: z.string().min(1).max(200).optional(),
  })
  .describe("One large sentence: the claim a viewer should leave with.");

export const codeHighlightPropsSchema = z
  .strictObject({
    /** The file is read when the timeline is built, so the video shows the code as it is. */
    file: repositoryPathSchema,
    from_line: z.number().int().positive(),
    to_line: z.number().int().positive(),
    /** Line numbers to mark, within the range shown. */
    highlight: z.array(z.number().int().positive()).default([]),
  })
  .describe(
    "An excerpt of a real file in the repository, read when the cut is built, with some lines marked. At most 18 lines of at most 100 characters.",
  );

export const terminalPropsSchema = z
  .strictObject({
    /** The command as it was typed. */
    command: z.string().min(1).max(120),
    /** A file holding the command's real output, captured by running it. It is never typed in here. */
    output_file: repositoryPathSchema,
    from_line: z.number().int().positive().optional(),
    to_line: z.number().int().positive().optional(),
  })
  .describe(
    "A command and its real output, revealed line by line. The output is read from a file the command wrote when it was run; it is never typed into the storyboard. At most 18 lines.",
  );

/** What a number was measured on. A viewer reads "4 seconds" very differently for each. */
export const metricScopeSchema = z.enum(["one user", "load test", "eval run", "production"]);

export const metricCardsPropsSchema = z
  .strictObject({
    title: z.string().min(1).max(80).optional(),
    metrics: z
      .array(
        z.strictObject({
          value: z.string().min(1).max(16),
          label: z.string().min(1).max(60),
          /** Where the number comes from: a document and section, a results file, a dashboard panel. */
          source: z.string().min(1).max(80),
          scope: metricScopeSchema,
        }),
      )
      .min(1)
      .max(4),
  })
  .describe(
    "One to four numbers. Each must say what it was measured on (scope) and where it comes from (source); both are shown on screen.",
  );

export const illustrationPropsSchema = z
  .strictObject({
    /** A generated or licensed still or clip under public/media/. It is always shown with a tag. */
    file: mediaPathSchema,
    caption: z.string().min(1).max(120).optional(),
  })
  .describe(
    "A generated or licensed still or clip, for a moment the product cannot show. It is always drawn with a tag that says illustration, and must be listed in media.lock.json.",
  );

/** Fields every scene has, whatever its component. */
const sceneFields = {
  id: identifierSchema,
  lines: z.array(lineSchema),
  /** The scene lasts at least this long. Required for a scene with no lines. */
  min_seconds: z.number().positive().max(120).optional(),
};

export const sceneSchema = z.discriminatedUnion("component", [
  z.strictObject({
    ...sceneFields,
    component: z.literal("TitleCard"),
    props: titleCardPropsSchema,
  }),
  z.strictObject({ ...sceneFields, component: z.literal("EndCard"), props: endCardPropsSchema }),
  z.strictObject({
    ...sceneFields,
    component: z.literal("ScreenRecording"),
    props: screenRecordingPropsSchema,
  }),
  z.strictObject({
    ...sceneFields,
    component: z.literal("Statement"),
    props: statementPropsSchema,
  }),
  z.strictObject({
    ...sceneFields,
    component: z.literal("CodeHighlight"),
    props: codeHighlightPropsSchema,
  }),
  z.strictObject({ ...sceneFields, component: z.literal("Terminal"), props: terminalPropsSchema }),
  z.strictObject({
    ...sceneFields,
    component: z.literal("MetricCards"),
    props: metricCardsPropsSchema,
  }),
  z.strictObject({
    ...sceneFields,
    component: z.literal("Illustration"),
    props: illustrationPropsSchema,
  }),
]);

export const storyboardSchema = z
  .strictObject({
    title: z.string().min(1),
    /** The finished cut must be this long; the briefs so far have asked for 3 to 5 minutes. */
    target_seconds: z.strictObject({ min: z.number().positive(), max: z.number().positive() }),
    scenes: z.array(sceneSchema).min(1),
    /**
     * The frame every player shows before the video plays: a scene and a second into it, at a settled
     * moment. Frame 0 of the cut is this frame, and it is saved beside the cut as a JPEG. Without it,
     * the first scene once its text has settled.
     */
    poster: z.strictObject({ scene: identifierSchema, at_seconds: z.number().min(0) }).optional(),
  })
  .superRefine((storyboard, context) => {
    const seenSceneIds = new Set<string>();
    const seenLineKeys = new Set<string>();
    for (const [sceneIndex, scene] of storyboard.scenes.entries()) {
      if (seenSceneIds.has(scene.id)) {
        context.addIssue({
          code: "custom",
          path: ["scenes", sceneIndex, "id"],
          message: `scene id "${scene.id}" is used more than once`,
        });
      }
      seenSceneIds.add(scene.id);
      if (scene.lines.length === 0 && scene.min_seconds === undefined) {
        context.addIssue({
          code: "custom",
          path: ["scenes", sceneIndex],
          message: `scene "${scene.id}" has no lines, so it needs min_seconds to have a length`,
        });
      }
      for (const [lineIndex, line] of scene.lines.entries()) {
        if (seenLineKeys.has(line.key)) {
          context.addIssue({
            code: "custom",
            path: ["scenes", sceneIndex, "lines", lineIndex, "key"],
            message: `line key "${line.key}" is used more than once`,
          });
        }
        seenLineKeys.add(line.key);
      }
    }
    if (storyboard.poster !== undefined && !seenSceneIds.has(storyboard.poster.scene)) {
      context.addIssue({
        code: "custom",
        path: ["poster", "scene"],
        message: `poster names scene "${storyboard.poster.scene}", which the storyboard does not have`,
      });
    }
    if (storyboard.target_seconds.min > storyboard.target_seconds.max) {
      context.addIssue({
        code: "custom",
        path: ["target_seconds"],
        message: "target_seconds.min is greater than target_seconds.max",
      });
    }
  });

export const brandSchema = z.strictObject({
  colors: z.strictObject({
    background: hexColorSchema,
    surface: hexColorSchema,
    text: hexColorSchema,
    muted: hexColorSchema,
    accent: hexColorSchema,
  }),
  fonts: z.strictObject({
    heading: z.string().min(1),
    body: z.string().min(1),
    mono: z.string().min(1),
  }),
  voice: z.strictObject({
    /** The final voice: a Gemini voice name. */
    name: z.string().min(1),
    /** The Gemini text-to-speech model. */
    model: z.string().min(1).default("gemini-3.8-flash-tts"),
    /** The default delivery direction; a line's own style replaces it. */
    style: z.string().min(1),
    /** The free draft voice: a macOS `say` voice. */
    draft_voice: z.string().min(1),
    draft_words_per_minute: z.number().int().min(90).max(300),
    /** The Kokoro voice: the free draft voice everywhere, and the final voice when `.env` names kokoro. */
    kokoro_voice: z.string().min(1).default("af_heart"),
    /**
     * How the voice says a word the captions spell another way, whole words only, case kept:
     * `{"Qrypt": "Crypt"}`. Only the text sent to the voice changes; captions and screens do not.
     */
    pronunciations: z.record(z.string().min(1), z.string().min(1)).optional(),
  }),
  /** Background music. The file must be listed in media.lock.json as licensed. */
  music: z
    .strictObject({
      file: mediaPathSchema,
      /** Volume between lines, 0 to 1. */
      volume: z.number().min(0).max(1).default(0.14),
      /** Volume under a spoken line, 0 to 1. */
      volume_under_voice: z.number().min(0).max(1).default(0.04),
    })
    .optional(),
});

/** One line placed in time, relative to the start of its scene. */
export const cueSchema = z.strictObject({
  key: identifierSchema,
  text: z.string(),
  /** Path under public/, as `staticFile()` expects it. */
  audio_file: z.string().min(1),
  from_frame: z.number().int().min(0),
  duration_in_frames: z.number().int().positive(),
});

/** One beat of a recorded take: where it starts and ends in the take's video, in seconds. */
export const beatRowSchema = z.strictObject({
  take: identifierSchema,
  key: identifierSchema,
  start: z.number().min(0),
  end: z.number().positive(),
});

/** How a recorded beat is fitted into its scene. */
export const footagePlacementSchema = z.strictObject({
  video_file: z.string().min(1),
  /** Where in the take the beat starts, in frames at the composition's frame rate. */
  source_start_frame: z.number().int().min(0),
  /** 1 is real time. Footage is only ever sped up, and never past the limit in the fit rules. */
  playback_rate: z.number().min(1),
  /** Frames of the scene during which the footage plays. */
  played_frames: z.number().int().positive(),
  /** Frames at the end of the scene during which the last frame is held. */
  hold_frames: z.number().int().min(0),
});

export const timedSceneSchema = z.strictObject({
  scene: sceneSchema,
  from_frame: z.number().int().min(0),
  duration_in_frames: z.number().int().positive(),
  cues: z.array(cueSchema),
  /** Present for a scene that shows recorded footage. */
  footage: footagePlacementSchema.optional(),
  /** Present for a CodeHighlight scene: the lines as they were in the file when the timeline was built. */
  code_lines: z.array(z.strictObject({ number: z.number().int(), text: z.string() })).optional(),
  /** Present for a Terminal scene: the captured output, line by line. */
  terminal_lines: z.array(z.string()).optional(),
});

/** Where a media file came from. Product footage is always `recorded`; nothing else may stand in for it. */
export const provenanceSchema = z.enum(["recorded", "voice", "generated", "licensed"]);

/** `media.lock.json`: every media file the cut needs, by its path under public/media/. */
export const mediaManifestSchema = z.record(
  z.string(),
  z.strictObject({
    sha256: z.string().regex(/^[0-9a-f]{64}$/),
    bytes: z.number().int().min(0),
    provenance: provenanceSchema,
    /** For a generated or licensed file: the prompt, the source or the licence. */
    note: z.string().min(1).optional(),
  }),
);

/** Everything the composition needs: the scenes placed in time, and the brand. It is the render's props. */
export const timelineSchema = z.strictObject({
  title: z.string(),
  frames_per_second: z.number().int().positive(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  duration_in_frames: z.number().int().positive(),
  voice_provider: z.string().min(1),
  /** The frame of the cut that is its poster; the composition draws it at frame 0. */
  poster_frame: z.number().int().min(0),
  brand: brandSchema,
  scenes: z.array(timedSceneSchema).min(1),
});

export type Line = z.infer<typeof lineSchema>;
export type Scene = z.infer<typeof sceneSchema>;
export type Storyboard = z.infer<typeof storyboardSchema>;
export type Brand = z.infer<typeof brandSchema>;
export type Cue = z.infer<typeof cueSchema>;
export type TimedScene = z.infer<typeof timedSceneSchema>;
export type Timeline = z.infer<typeof timelineSchema>;
export type BeatRow = z.infer<typeof beatRowSchema>;
export type FootagePlacement = z.infer<typeof footagePlacementSchema>;
export type MediaManifest = z.infer<typeof mediaManifestSchema>;
export type Provenance = z.infer<typeof provenanceSchema>;
export type CodeHighlightProps = z.infer<typeof codeHighlightPropsSchema>;
export type IllustrationProps = z.infer<typeof illustrationPropsSchema>;
export type KeyPhrase = z.infer<typeof keyPhraseSchema>;
export type MetricCardsProps = z.infer<typeof metricCardsPropsSchema>;
export type ScreenRecordingProps = z.infer<typeof screenRecordingPropsSchema>;
export type StatementProps = z.infer<typeof statementPropsSchema>;
export type TerminalProps = z.infer<typeof terminalPropsSchema>;
export type TitleCardProps = z.infer<typeof titleCardPropsSchema>;
export type EndCardProps = z.infer<typeof endCardPropsSchema>;
