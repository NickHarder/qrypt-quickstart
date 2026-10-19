---
type: Guide
title: The demo video
description: How to make the demo video from one storyboard, what each file in demo/ is, and what each step costs.
tags: [demo]
status: stable
generated: { by: ai-kit/v0.21.1 }
---

# Demo video

One storyboard, voiced line by line, rendered to a checked video. Run every command below from the
repository root.

```bash
make demo-bootstrap     # once per clone: Node packages, Remotion's browser, Playwright's recorder
make demo-capture       # record the takes (the example take records a page that ships in demo/)
make demo-stills        # one still per scene settled and one at its end, before any render; $0
make demo-draft         # Kokoro's free local voice, half size, all the checks; $0
```

It needs ffmpeg and ffprobe on the machine: `brew install ffmpeg` on a Mac, and on Linux
`scripts/install_tools.sh ffmpeg`, a pinned static build checked against its checksum. The first
draft downloads Kokoro's model, about 90 MB, into `~/.cache/kokoro-js` (or `KOKORO_CACHE_DIR`).
The draft is `demo/out/draft.mp4`, with its poster `draft.jpg`. With a coding agent, use the
`generate-demo` skill: it walks the whole process and stops where you have to decide.

## The files you edit, in `demo/`

| File | What it is |
|---|---|
| `storyboard.json` | The cut: an ordered list of scenes. Each names a catalog component, gives its props, and has the lines spoken over it. This is the only copy of the words. `poster` names the scene and second that is the thumbnail. |
| `brand.json` | Colors, fonts, the voice, and optionally music. |
| `takes/*.take.ts` | Playwright recordings of the product. The only code specific to this project. |

And the files the pipeline keeps, all committed: `beats.json` (where each recorded beat starts and
ends), `media.lock.json` (every media file's checksum and where it came from), `approved.json` (the
scenes you have approved), `catalog.schema.json` (what a scene may be, generated from the code).

Media itself (`public/media/`: takes, voice clips, generated clips, music) is not in git. Archive it
somewhere; `make demo-assets` says whether an archive matches the manifest.

## How timing works

Audio first. Each line becomes one voice clip, the clip is measured, and its scene lasts as long as its
lines take to say (0.3 s before each line, 0.5 s after the last). A recording longer than its scene
is sped up, at most four times; a shorter one holds its last frame. The voice is never sped up. A cut
outside `target_seconds` fails and names its longest scenes.

A viewer must be able to read what is on screen: 0.3 s a word and at least 1.2 s for a sentence,
0.8 s for a label, counted from when the whole text is in. `make demo-check` holds every scene to
that floor from its narration's estimated length, and a render holds it to the measured one; a scene
that fails gets a line, a `min_seconds`, or less copy. A key phrase over a recording is held to its
own `for_seconds`, less its fades.

## Stills and the poster

`make demo-stills` renders one still per scene once its text has settled and one at its end, into
`demo/out/stills/`, from a silent timeline: seconds, and no voice. Look at them for text that
overflows, elements that collide and low contrast before any render.

Every player and platform shows frame 0 as the thumbnail. The storyboard's `poster` names the
scene and the second whose settled frame that is (without it, the first scene a second in); the
composition draws that frame at frame 0, and every cut saves it beside itself as a JPEG
(`demo.jpg`, `draft.jpg`), the image to upload where a platform takes one.

## The catalog

`TitleCard`, `EndCard`, `Statement`, `ScreenRecording`, `CodeHighlight`, `Terminal`, `MetricCards`,
`Illustration`. `catalog.schema.json` describes each one and its props; `make demo-check` rejects
anything else, naming the scene.

`CodeHighlight` and `Terminal` read their text from files in the repository when the cut is built.
`MetricCards` needs a source and a scope for every number. `Illustration` always shows a tag, and its
file must be listed in the manifest (`make demo-record`).

## Voice

| Command | What happens | Cost |
|---|---|---|
| `make demo-draft` | Kokoro, a free voice that runs on this machine, reads every line; `VOICE=say` on a Mac, `VOICE=espeak` with espeak-ng, or `VOICE=silent` anywhere | $0 |
| `make demo-voice` | With Gemini: prints the seconds and dollars for the lines with no final clip, and sends nothing. With Kokoro: makes the clips, at once | $0 |
| `make demo-voice CONFIRM=1` | With Gemini: one request per line that needs it; unchanged lines are reused | what `make demo-voice` printed |
| `make demo-voices SEARCH=narrator` | Lists the final voice's voices; put your choice in `brand.json` (`voice.name` for Gemini, `voice.kokoro_voice` for Kokoro) | $0 |

The final voice is the one `DEMO_VOICE_PROVIDER` names in the `.env` at the repository root:
`gemini`, paid and behind `CONFIRM=1`, or `kokoro`, free and local, with 28 voices and the sound of
the draft. When it names none, the rule is: Gemini when `GEMINI_API_KEY` is set, Kokoro when it
is not; and when the key does not work, `make demo-voice CONFIRM=1` falls back to Kokoro, says
so, and tells you to render with `make demo VOICE=kokoro`. Each voice says its own price, so the
estimate follows the choice.
Another provider is a file beside `src/pipeline/voice/gemini.ts` that makes a `VoiceProvider`, and
one entry in `src/pipeline/voice/final.ts`.

Gemini's key goes on the `GEMINI_API_KEY` line of that `.env` (see `.env.example` there), beside
every other key the project uses. Create it in Google AI Studio; a Gemini app
subscription does not include API access. The price table in `src/pipeline/voice/estimate.ts` was read
on 2026-10-02; check the pricing page when it matters.

A clip is tied to its exact text, style, voice and model. Change one word and that line, and only that
line, needs a new clip.

## The finished cut

```bash
make demo               # full size, from the final voice; refuses if a line has no final clip
```

It writes `demo/out/demo.mp4`, `demo.srt` and the poster `demo.jpg`. Every cut is finished the same
way: audio normalised to -16 LUFS, captions as a track a viewer can switch on, the index at the
front of the file, the poster as frame 0. Then the checks: size, frame rate, color range, length
against the timeline and against `target_seconds`, the reading floor on every scene, caption track,
caption reading speed, loudness, true peak.

## Approving scenes

```bash
make demo-approve SCENE=open    # lock a scene you are happy with
make demo-reopen SCENE=open     # unlock it when you want it changed
```

A change to an approved scene fails `make demo-check` until it is reopened.

## Changing the catalog

A component lives in four places: its schema in `src/catalog/schemas.ts`, its file in
`src/components/`, its case in `src/catalog/registry.tsx`, and the generated `catalog.schema.json`
(`cd demo && npm run demo -- catalog`). Remotion publishes skills for coding agents; install them once,
globally: `npx skills add remotion-dev/skills -g`.

Remotion is free for an individual and for a company of up to three people; a larger company needs a
licence.

## Advisories

CI's demo job runs `npm run advisories` (`cd demo` first): npm's advisories against
`package-lock.json`, held to `known-advisories.json`. It fails on an advisory the list does not hold,
and on a fix npm can make without a breaking change. When one appears, update past it: a direct
dependency in `package.json`, a package inside another through its `overrides`, as sharp and
global-agent are. When no version fixes it yet, add it to the list with the date and why it stays,
and say so in the merge request. A breaking fix npm offers, a downgrade included, is only noted.
