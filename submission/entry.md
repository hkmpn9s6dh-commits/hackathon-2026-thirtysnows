# Thirty Years — Entry write-up

**Category:** 08 · Best Speculative Ad
**Brand:** Nongfu Spring 农夫山泉 · Changbai Snow (长白雪), a natural snow-mountain mineral water
**Length:** 30.00 s · 1920×1080 · 24 fps
**Status:** Speculative work. Not commissioned, not affiliated, not aired.

---

## The challenge

Changbai Snow comes from a cold spring inside the Changbai Mountains. The water fell as
snow, seeped into volcanic basalt, and travelled through the rock for **thirty to sixty
years** before it surfaced at a constant 7 °C. That number is on the brand's own product
page. It is also, in eight years of the brand's documentary-style films, a number that has
never been *seen*: every one of those films stays outside the mountain — snow, deer, forest,
four seasons, mist.

The product's entire value is a duration. The category's entire visual language is landscape.
So the brief we set ourselves was: **show the thirty years, not the mountain.**

## The idea

> **What you taste is snow from thirty years ago.**
> 你喝到的，是三十年前的雪。

One continuous descent. A snowflake lands on black basalt, melts, slips into a hairline
fissure, and falls — through wet rock, mineral veins, and near-total darkness — until it
surfaces as a spring at the snow line, where a bottle is already standing.

Eight shots, one direction of travel, two camera moves (a very slow push, a very slow pull).
No people, no voice-over, no music.

## Why this needed generative AI

The thirty years happen **inside the rock**. There is no light, no space, and no second
camera position in there. A traditional production would have to build the inside of a
mountain in CG — modelling, surfacing, lighting, a render farm — which is out of reach for a
solo maker, and would still look like a build.

Generation made the impossible shot the *cheapest* shot. The film is not "AI for speed";
it is AI as the only camera that can go where the idea lives. That is the territory this
category asks for: *beyond traditional production constraints*.

## Approach (and what is checkable)

The film is built like software, because a 30-second ad has no room for a shot that drifts.

- **One source file.** `film.py` holds the eight shots, the camera curves, three supers, the
  end card and ten sound cues. The edit decision list is generated from it, and a command
  fails the build if the document and the code disagree.
- **Seven stills, not seventy.** Seven generated keyframes carry the whole film. Motion is
  procedural: sub-pixel camera moves with smoothstep easing, a cold grade (+5.5 % blue,
  −3.5 % red), 0.75 % grain, 28 % vignette — identical on every rebuild.
- **Sound with no music.** Wind, rock, water and one 110 Hz bell, all synthesised from noise
  and modal partials in numpy. Loudness normalised to −14 LUFS, true peak −2.2 dBTP.
  Music would have made thirty years feel like thirty seconds.
- **Typography as the only "graphic".** Source Han Serif, three lines, 34 px, 8 % from the
  left edge, 77.5 % down. The end card holds the brand line and the AI disclosure.
- **25 assertions before a single frame was rendered.** Timeline adds to 30.000 s and 720
  frames; cuts are cuts; every super sits inside a 5 % safe area; the palette stays cold;
  no skin-tone region; every character exists in the bundled font; the same timestamp
  renders to the same bytes.
- **A fresh clone reproduces it.** `bash scripts/verify.sh` re-renders eight frames from the
  delivered file and requires ≥45 dB PSNR against a from-scratch render.

## Results

- 30.000 s, 1920×1080, 24 fps, H.264 + AAC, −14.1 LUFS, true peak −2.2 dBTP.
- 25 assertions green on the build machine and in a clean clone.
- Blind read by three models from three different families, with the author hidden:
  all three named the product category (bottled water) and the closing line.
- Zero external assets: 7 generated stills + code. No stock, no library music, no fonts
  redistributed (type is rasterised into the film).

## What we would do with a real commission

Shoot the first and last four seconds for real — a real ridge, a real spring, a real bottle —
and keep the descent generated. The collision of a real exterior with an impossible interior
is the version of this idea that belongs on television.

---

*Full build, documents and gate evidence: repository `hackathon-2026-thirtysnows`.*
