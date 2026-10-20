# Craft

How to make the cut worth watching, once it is honest. Adapted from the creative rules of `/brag`
(latent-spaces/brag, MIT License, Copyright (c) 2026 Shunit Haviv Hakimi), a skill for 20-second
launch videos, read 2026-10-20. Its rules for a short launch clip are kept where they hold for a
3-to-5-minute walkthrough, and changed where this project's rules differ:
[honest-film.md](honest-film.md) wins wherever the two disagree.

## The first seconds

- **The hook is planned first.** The first scene decides whether anyone keeps watching. Before the
  rest of the table, write what the first two seconds show, and why a stranger would stay.
- **Lead with the result, not the setup.** Open on the moment the product pays off (a success line,
  the finished screen), then go back to how a user gets there. The problem statement can be that
  opening's line.
- **Clear to a stranger.** After one viewing, someone who has never heard of the product knows what
  it does, who it is for and how to get it. Say that early; how it is built comes later, if at all.

## Every scene

- **Show the thing.** The product on screen is the product in use: a `ScreenRecording` of the real
  flow, a `Terminal` of the real command. Prefer the working product doing its job over a page
  describing it. `/brag` rebuilds a site's UI and animates it; here that is not allowed, because
  product footage is recorded, never generated.
- **Specific.** Every line and every card belongs to this project: its own words, its own numbers
  with their sources. A sentence that would fit any product ("streamline your workflow") is cut.
- **Alive, not slides.** Things that appear one by one, a cursor that moves, a command that runs,
  beat a static card. A card that must be static holds only as long as its reading time.
- **Readable.** Pace comes from cuts, not from pulling text away early. Text meant to be read stays
  settled for 0.3 s a word, counted from when the whole line is on screen; `make demo-check` holds
  this.
- **Funny only if it earns it.** Humor comes from the product's own absurdity, not from trying.

## Every frame

- **Any frame could be the poster.** Look at each still as if it were the thumbnail a stranger sees:
  nothing cut off, nothing colliding, no low contrast, nothing half-arrived.
- **Look at the moments between scenes too.** A cut between two busy layouts can flash a frame of
  both. If a still at a scene's last frame and the next scene's first frame look muddy together,
  end the scene on a calmer frame or let the next one build up from its background.

## Sound

- **One piece.** The music and anything else the viewer hears are mixed as one track: nothing harsh
  or spiky, the music under every spoken line (the pipeline ducks it), and repeated small sounds kept
  in the background.
- **Silence is a choice.** No music is better than music that fights the voice.
- **Licenses first.** A track or a sound goes in only with its license written beside it in
  `media.lock.json`. Public-domain (CC0) sounds are fine; a track whose terms are not written down is
  not used. `/brag`'s bundled music says its terms still need checking, so it is not used here.

## The share line

- **Propose one caption to post with the video:** one to three sentences, specific to this project,
  no "excited to share". It is the owner's wording: show it, take their notes, and write it to
  `demo/out/share-copy.txt` only once they say yes.
