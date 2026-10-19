# Changing or adding a component

Read this only when the catalog itself has to change. A storyboard never needs it.

## The four places a component lives

1. `demo/src/catalog/schemas.ts`: its props as a `z.strictObject`, with a `.describe()` that says
   what it shows, and its entry in `sceneSchema`.
2. `demo/src/components/<Name>.tsx`: the component.
3. `demo/src/catalog/registry.tsx`: its case in `renderScene`. The switch is exhaustive, so a
   component missing here does not compile.
4. `demo/catalog.schema.json`: regenerate it with `npm run demo -- catalog` (in `demo/`).

Then `make demo-check`, and a draft that uses the new component.

## Remotion's own guidance

Remotion publishes skills for coding agents. Install them once, for every project, outside this
repository. The kit's skill check holds what is in `.claude/skills/` to the kit's own format, and
skips only a folder that `.claude/skills/THIRD_PARTY` lists:

```bash
npx skills add remotion-dev/skills -g
```

Use `remotion-markup` when writing a component, `remotion-multimedia` for video and audio handling,
`remotion-captions` for captions, `remotion-docs` to search the documentation. If they are not
installed, any documentation page is served as Markdown when `.md` is added to its URL:

- https://www.remotion.dev/docs/the-fundamentals.md
- https://www.remotion.dev/docs/schemas.md
- https://www.remotion.dev/docs/dynamic-metadata.md
- https://www.remotion.dev/docs/sequence.md
- https://www.remotion.dev/docs/cli/render.md

Fetch the page before using an API you have not used in this project; do not rely on memory.

## Rules that are easy to get wrong

- Animate from `useCurrentFrame()` with `interpolate()`. CSS transitions and animations do not render.
- Take `fps` from `useVideoConfig()`; never hard-code a frame rate in a component.
- Use `<Video>` and `<Audio>` from `@remotion/media`, files through `staticFile()`, and
  `premountFor={fps}` on timed media.
- A component draws; it does not decide timing. How long a scene lasts, where footage starts and how
  fast it plays all come from the timeline (`demo/src/pipeline/timeline.ts`).
- Colors and fonts come from `useBrand()`. A new color pair must clear the contrast check in
  `demo/src/pipeline/contrast.ts`.
- Remotion is free for an individual and for a company of up to three people; a larger company needs
  a licence.
