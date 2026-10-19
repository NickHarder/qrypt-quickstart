---
name: generate-demo
description: Makes the project's demo video from one storyboard. It answers a rubric about the product, proposes the story, writes demo/storyboard.json against the component catalog, records the product, checks stills, renders a free draft, and once the owner has approved the scenes and the cost, makes the final voice-over and the finished cut with its poster frame. Use when the owner asks for a demo video, a walkthrough video or a re-cut of one, in a project that has the demo layer (a demo/ directory).
disable-model-invocation: true
metadata:
  version: "1.1.0"
---

# Make the demo video

The video is built from `demo/storyboard.json`. Nothing else holds the words or the order of the cut.

If there is no `demo/` directory, the layer is off: say so, and that `copier update` with `enable_demo`
turns it on. If `demo/node_modules` is missing, run `make demo-bootstrap` first.

## Who decides what

The owner decides the story, the wording, the pacing and the look. You propose, build and check.

- Show what exists, take the owner's notes, restate them in a line or two, and change only what they
  confirmed. One scene at a time.
- Do not write taglines, key phrases or rewordings the owner did not ask for. A stand-in is labeled
  as a stand-in.
- These three commands are the owner's calls. Run one only when the owner has said to, in this
  conversation: `make demo-approve`, `make demo-reopen`, `make demo-voice CONFIRM=1`.
- State a hard limit (the length the brief asks for, a claim with no measurement behind it, the cost
  of a re-record) as a fact, not as a decision.

## Read first

- `demo/catalog.schema.json`: every component a scene may use, and its props. Nothing else is allowed.
- `demo/brand.json`: colors, fonts, the voice.
- What the brief requires of the video (its length, what it must show), from `docs/DELIVERABLES.md` or the
  brief itself.
- [references/story-shapes.md](references/story-shapes.md): the orders, lengths and pacing that have worked.
- [references/honest-film.md](references/honest-film.md), before writing any line that states a number
  or showing anything that is not a recording.
- [references/remotion.md](references/remotion.md), only when a component has to change.

## Steps

1. **Requirements.** Find the required length and the list of things the video must show. Set
   `target_seconds` from the length.
2. **Propose the story.** Before proposing, answer the rubric in writing, from the repository and the
   brief, not from imagination: what the product is, in one sentence; who it is for; the one beat of
   it in use (entry, the action, the result) that the recording must show; the strongest measured
   number, with its source; the visual hook, the one screen worth a still; the shortest satisfying
   length within the brief. Then a table: scene, component, what is on screen, the line, estimated
   seconds (words divided by 2.5), and the reading time of its text (0.3 s a word, 0.8 s a label).
   Total it, and name the pacing option from the story shapes. Write no files yet. Wait for the
   owner's yes or notes.
3. **Write the storyboard.** One scene per row of the agreed table. Name the poster: the scene and
   second whose settled frame is the thumbnail every player shows (`poster` in the storyboard;
   without it, the first scene a second in). Then `make demo-check`, which also holds every scene's
   text to its reading time: a scene that fails gets a line, a `min_seconds`, or less copy.
4. **Record the product.** Each `ScreenRecording` scene shows one beat of a take in `demo/takes/`.
   Write or adjust the take, one `beat()` per scene. Record on the development stack, never on
   production. If recording makes the product call a paid model, say the dollar estimate and get a yes.
   Then `make demo-capture`.
5. **Gather what the other scenes show.** For a `Terminal` scene, run the real command and save its
   output to a file in the repository. For `MetricCards`, take each number from its latest measurement
   and name the source.
6. **Draft, after the stills.** `make demo-stills` (free, seconds): one still per scene settled and
   one at its end, in `demo/out/stills/`. Look at every one for text that overflows, elements that
   collide and low contrast, and fix the storyboard before any render. Then `make demo-draft`
   (free): Kokoro reads every line on this machine. Give the owner `demo/out/draft.mp4`, the
   poster `demo/out/draft.jpg` and the length of each scene from `demo/work/timeline.json`. Say
   that the voice is a stand-in unless Kokoro is the final voice too.
7. **Review, one scene at a time.** When the owner approves a scene, and only then:
   `make demo-approve SCENE=<id>`. An approved scene is locked; if the owner asks to change one,
   `make demo-reopen SCENE=<id>` first.
8. **Final voice.** The voice `DEMO_VOICE_PROVIDER` names in the `.env`; unnamed, Gemini when
   `GEMINI_API_KEY` is set and Kokoro when it is not. With Gemini, `make demo-voice` prints the
   seconds and the dollars and sends nothing; tell the owner both, and on their yes run
   `make demo-voice CONFIRM=1`; if the key does not work it falls back to Kokoro and says so. With
   Kokoro, free and local, `make demo-voice` makes the clips at once. If it names reads that are far
   too long or too short, the owner listens to those clips before anything else.
9. **Finished cut.** `make demo`. Every check must pass. Report the length, the loudness and the
   paths: `demo/out/demo.mp4`, with `demo.srt` and the poster `demo.jpg` beside it; frame 0 of the
   cut is the poster.
10. **Hand back.** The owner publishes. Then put the link where the brief wants it, and commit
    `storyboard.json`, `beats.json`, `media.lock.json` and `approved.json`. The media under
    `demo/public/media/` is not in git: remind the owner to archive it.

## Acceptance

- [ ] Every item the brief requires is in a scene
- [ ] `make demo-check`, `make demo-assets` and the checks at the end of `make demo` pass
- [ ] The cut is inside `target_seconds`, and every scene's text can be read in its time
- [ ] The stills were looked at before the draft, and the poster is a settled frame
- [ ] Every scene the owner approved is still as approved
- [ ] No number is on screen or in a line without a measurement and a source
- [ ] Nothing paid ran without the owner's yes to a stated amount
