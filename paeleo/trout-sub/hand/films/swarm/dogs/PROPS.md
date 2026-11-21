# PROPS.md · the things (`films/swarm/dogs/props.py`)

What a dog digs up, carries, lays on the sill, stacks, or breathes out. Handmade from code, except the
faces of the reels, which are real frames of this project's own films (cut with ffmpeg, cached at 320x180
under `films/swarm/dogs/frames/`, 53 files, 740 KB). No type, no labels, no counters on anything.

Look before you use it: `props_sheet.png` (everything, close and at film size, on dusk boards and in creek
water), `props_reels.png` (every reel with the frame it holds; the numbers on that sheet are a look-up for
builders and are not film), `props_strip_pile.png`, `props_strip_breath.png`, `props_strip_ice.png`,
`props_strip_drip.png`. Regenerate with `python3 films/swarm/dogs/props.py` (also runs the self-test;
`--frames` re-cuts the frames from the films).

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import dog, props

def on_sill(ink, t, oy):                                    # a porch.scene cast callback
    props.pile(ink, t, 312, 392 - oy, 3, s=0.6, born=[62.2, 71.5, 75.5], edge=404 - oy, floor=400 - oy)
    dog.draw_dog(ink, dog.carry_reel(t), 500, 394 - oy, scale=0.6, facing=-1,
                 carry=props.reel_sprite(props.REEL_LEAD, tail=0.7, wet=1))
```

## Conventions

- **Screen pixels.** Every `(x, y)` is a screen point; subtract the camera's `oy` yourself, as with the dogs.
- **`s` is the dog's scale.** `s=0.6` beside a dog drawn at `scale=0.6` (the porch two-shot), `1.6` close.
  At `s=1` a reel lid is 48 px across, a page 40 x 52, a part about 30, a paw print 15, a lantern 44 tall.
- **`ink`** is a `kit.Ink` or a PIL image. Nothing here boils: props hold still unless you move them.
- **Under water** pass `tint=props.TEAL, tint_amount=0.35` (or `**props.UNDER`), the same as the dogs.
- **In a dog's mouth.** `dog.draw_dog(..., carry=<image>)` pastes an image with the middle of its top
  edge at the mouth and scales it by the dog's scale. So build `*_sprite(...)` at `s=1.0` and let the dog
  scale it. A sprite shows only once `pose["hold"] >= 0.5` (dog.py's rule).
- **Order.** Draw a thing after what it rests on and before what covers it. `glow` and `lantern(halo=...)`
  light what is already drawn, so call them after the set and before the carrier.

## Functions

| Function | What it draws | Example call |
|---|---|---|
| `reel(ink, n, x, y, s=1, tilt=1, angle=0, wet=0, paw=False, half=False, loop=1, tail=0, sway=0, lit=1, face=True, alpha=1, tint=None, tint_amount=0)` | A film can centred at (x, y). The lid shows ONE real frame of reel `n` (0..52, see the list below). `tilt` 1 = lid to us, 0.3 = lying nearly flat, the can's wall showing. `paw` = a pale muddy paw print on the lid. `half=True` = the one-sided reel: film wound on one flange and a loose `loop` hanging out. `tail` 0..1 = a leader of film hanging out, moved by `sway`. `lit` < 1 dims the picture away from the lamp. | `props.reel(ink, props.REEL_LEAD, 380, 378, 0.6, tilt=0.6, paw=True)` |
| `reel_sprite(n, s=1, tilt=1, angle=0, **reel options)` | The same can as an RGBA image for the dog's mouth, gripped by the top of its rim. | `dog.draw_dog(ink, dog.carry_reel(t), x, y, 0.6, carry=props.reel_sprite(13, tail=0.7, wet=1))` |
| `reel_stack(ink, ns, x, y, s=1, lean=0, seed=0, wet=0, paws=(), top_tilt=None, lit=1, alpha=1, tint=None, tint_amount=0)` | Cans stacked, bottom first, bottom can standing on (x, y). Each lies nearly flat, the stack leans `lean` px per can, the top one is tipped so its frame shows. Returns `[(x, y, n)]`. | `props.reel_stack(ink, [3, 14, 22], 340, 392, 0.6, lean=1.2, paws={22})` |
| `reel_piles(ink, x0, x1, y, count=53, s=0.42, seed=0, first=0, paws=11, lit=1, wet=0, alpha=1)` | The reels of the last shot: `count` cans in six leaning piles of unequal height (9, 12, 7, 11, 8, 6) between x0 and x1. A growing `count` grows the same piles, one can at a time, never in rotation. The last `paws` laid carry a paw print. Asserts the count; returns every can. 53 cans cost about 60 ms a frame at `s=0.42`. | `props.reel_piles(ink, 228, 395, 392 - oy, 53)` |
| `film_strip(ink, n, a, b, sag=10, s=1, lit=0, alpha=1)` | A length of film pulled out of reel `n` from point a to point b, hanging with slack; each frame on it takes its colour from the real frame; `lit` = the lamp behind it. Returns the middle of the strip. | `props.film_strip(ink, props.REEL_LEAD, hand, (236, 262), sag=6, s=0.7, lit=1)` |
| `thrown_frame(ink, n, box, level=1, color=(255,214,150), soft=2, image=None)` | The lamp throwing reel n's frame onto the door planks as light (the planks show through; a pencilled page is thickened so it carries). `box` = where on the door; the frame keeps 16:9 inside it. `image=` throws your own picture instead (the tidy wrong drawing). | `props.thrown_frame(ink, props.REEL_TEETH, (44, 190, 168, 300), porch.ease(t, 176.0, 177.0))` |
| `frame(n)` | The real frame itself, RGB 320x180. | `im = props.frame(props.REEL_COW)` |
| `reel_title(n)` | Which film reel n holds, in words (for the record, never on screen). | `props.reel_title(17)` |
| `build_frames(force=False, which=None)` | Cuts the frames out of the films with ffmpeg into `frames/`. Runs by itself the first time a frame is missing. | `props.build_frames()` |
| `part(ink, x, y, s=1, kind="gear", angle=0, mud=1, wet=1, weed=1, t=0, drip=None, floor=None, alpha=1, tint=None, tint_amount=0)` | A part from the gravel: `'gear' \| 'spool' \| 'flange' \| 'crank' \| 'lens' \| 'strip'`, with clods of mud, a strand of weed that swings with `t`, and a shine. `drip=<time it left the water>` makes it drip for four seconds, down to `floor`. | `props.part(ink, mx, my + 8, 0.6, "gear", t=t, drip=59.2, floor=392)` |
| `part_sprite(kind="gear", s=1, angle=0, mud=1, wet=1, weed=1, t=0, tint=None, tint_amount=0)` | The part for the dog's mouth. | `dog.draw_dog(ink, dog.carry_part(t), x, y, 0.6, carry=props.part_sprite("flange", t=t))` |
| `drips(ink, t, x, y, t0, width=20, floor=None, s=1, life=4, seed=0, color=..., heavy=1)` | Water running off a thing that came up at `t0`: fast, then drop by drop, gone after `life` s; a tick where each lands on `floor`. Pass the thing's current position; drops fall from where it is. | `props.drips(ink, t, 452, 372, 59.2, floor=392, s=0.6)` |
| `page(ink, x, y, s=1, drawing="jaw", blank=False, angle=0, flat=0, wet=0, paw=False, smudge=0, progress=1, tidy=False, lines=2, alpha=1, tint=None, tint_amount=0)` | A child's page: the printed ring with its four small squares, the child's drawing inside it (`'jaw' \| 'fish_bell' \| 'sub' \| 'bowl_legs' \| 'bars'`, the same redrawn strokes as `town.picture`), two lines with a pencilled scribble (loops, no letters). It is a stiff plane with four straight edges and never bends: `flat` 0 = it faces us, 1 = lying flat, seen nearly edge on. `paw` = a paw print in the corner; `smudge` = wet nose marks; `progress` < 1 = half drawn; `tidy` = the ruled-straight wrong version. | `props.page(ink, 330, 386, 0.6, "jaw", flat=0.72, angle=-6, paw=True)` |
| `blank_page(ink, x, y, s=1, **page options)` | The same page with nothing drawn: the ring and the empty lines are still printed. | `props.blank_page(ink, x, y, 0.6, flat=0.8)` |
| `page_sprite(drawing="jaw", s=1, blank=False, flat=0, angle=0, wet=0, paw=False, smudge=0, progress=1, tidy=False, lines=2, tint=None, tint_amount=0)` | The page for the dog's mouth. `flat=0.82` rides level under the muzzle (carried flat); `flat=0` hangs by its top edge. Rigid either way. | `dog.draw_dog(ink, dog.carry_page(t, gait="swim_up"), x, y, 0.6, facing=-1, carry=props.page_sprite("jaw", flat=0.82, **props.UNDER))` |
| `paw_print(ink, x, y, s=1, angle=0, wet=1, color=None, alpha=1, tint=None, tint_amount=0)` | A pad and four toes, toes up at angle 0. `wet` 1 = just pressed (dark, a shine), 0 = dried pale; it stays. | `props.paw_print(ink, 352, 388, 0.5, angle=-12, wet=props.clamp(1 - (t - 62.2) / 6))` |
| `lantern(ink, x, y, s=1, t=0, lit=1, swing=0, halo=1, under=True, seed=0, alpha=1, tint=None, tint_amount=0)` | A storm lantern hanging from (x, y), the top of its wire handle. The flame flickers with `t`; `swing` = degrees off plumb; `halo` = the light it throws on what is already drawn (wider and softer under water, with motes). Returns the flame's point. | `props.lantern(ink, mx, my, 0.6, t, swing=8 * math.sin(t * 3))` |
| `lantern_sprite(s=1, t=0, lit=1, swing=0, seed=0, tint=None, tint_amount=0)` | The lantern for the dog's mouth; no halo. Call `glow` at the mouth + (0, 27 s) first. | `dog.draw_dog(ink, dog.swim(t), x, y, 0.6, carry=props.lantern_sprite(t=t))` |
| `glow(ink, x, y, r, color=AMBER, level=1)` | Light added round a point; it brightens what is there and never greys it. | `props.glow(ink, j["mouth"][0], j["mouth"][1] + 16, 80, (255, 214, 140), 0.6)` |
| `pile(ink, t, x, y, count, s=0.6, born=None, wet=1, edge=None, floor=None, spread=1, lit=1, alpha=1)` | The pile on the sill: small, wet, growing. (x, y) = the board under its left end; `count` 0..12 things in the order of `props.PILE`: the child's page (paw print), the first reel (paw print), the one-sided reel with its loop, a strip, a flange, then a second row. `born` = when each was laid: it lands and settles for a third of a second, drips for four seconds over `edge` down to `floor`, and the water under the pile widens. Five things are 103 px wide at `s=0.6`. Returns `[(x, y, kind)]`. | `props.pile(ink, t, 312, 392, 5, born=[62.2, 71.5, 75.5, 79.0, 82.0], edge=404, floor=400)` |
| `puddle(ink, x, y, w, level=1, t=0, color=..., alpha=1)` | Standing water on a board. | `props.puddle(ink, 455, 393, 40, 0.8, t)` |
| `picture_bubble(ink, t, x, y, r=30, drawing="jaw", n=None, grow=1, progress=1, pop=0, tidy=False, calm=False, seed=0, tail=None, alpha=1)` | A bubble with a picture inside, centred at (x, y): a child's drawing, or with `n=` the real frame of that reel. `grow` blows it up, `progress` draws the drawing stroke by stroke, `pop` bursts it, `calm` stills its skin (under the ice), `tail=(mouth)` leads three small bubbles back to a mouth. (`town.bubble` is the fish-mouth version in town coordinates; this one is free-standing.) | `props.picture_bubble(ink, t, 760, 300 - 20 * (t - 146), 30, "jaw", tail=fish_mouth)` |
| `breath(ink, t, x, y, t0, t_out, s=1, seed=0, facing=1, ceiling=None, release=None, surface=None, heavy=1, alpha=1, at=None)` | Breath bubbles that run out. From `t0` they leave the muzzle at (x, y) in twos and threes, big; then singly, smaller, further apart; then a long wait; then at `t_out` one last small bubble, alone; then none. `ceiling` = the y of the underside of the ice: they stop there, flatten and stay until `release` (the ice breaking), when they all go. `surface` = the y of the line: each ends in a small ring. `at` = a function time -> muzzle point if the dog moves. Returns the air left, 1..0. | `air = props.breath(ink, t, j["nose"][0], j["nose"][1], 126.0, 131.0, s=0.6, seed=k, surface=400 - oy)` |
| `breath_left(t, t0, t_out)` | The air left, 1..0, without drawing (to time the dog's going up). | `if props.breath_left(t, 126, 131) <= 0: ...` |
| `ice_sheet(ink, t, x0, x1, y, thick=12, freeze=1, crack=0, breakup=0, stamps=(), hooves=(), origin=None, view="below", seed=0, alpha=1)` | A sheet of ice from x0 to x1 with its top on the line y. `freeze` 0..1 grows it outward from `origin` (default x0) with needles of frost running ahead. `hooves=[(x, weight)]` = the lead cow standing on it, a dark shape pressed on the sheet from below. `stamps=[(x, p)]` = a white star where a hoof comes down. `crack` runs the crack out from the first stamp and splits it into plates; `breakup` tips the plates, drifts them apart and sinks them. `view` `'below'` or `'side'`. Returns the y of its underside (use it as `breath(ceiling=...)`). (`porch.surface(freeze=...)` is the porch-side ice along the line; this one is for the town framings and close shots.) | `under = props.ice_sheet(ink, t, 300, 960, 400 - oy, 12, freeze=porch.ease(t, 118, 119.5), hooves=[(600, 1), (640, 1)], stamps=[(640, porch.ease(t, 122.0, 122.15))], crack=porch.ease(t, 122.6, 123.0), breakup=porch.ease(t, 123.0, 124.5))` |

Names: `props.REELS` (the table below), `props.N_REELS` (53), `props.PILE`, `props.PART_KINDS`,
`props.DRAWINGS`, `props.UNDER`, `props.TEAL`, `props.AMBER`, and the reels the board names:
`REEL_FIRST = 0` (the first can, S3 70.0), `REEL_HALF = 1` (the one-sided one, S3 75.5),
`REEL_LEAD = 12` (the lead dog's finished reel that the person refuses: class film 10),
`REEL_TEETH = 17` and `REEL_RETRIEVER = 17` (class film 10 at the child's own page: the wobbly teeth in
the ring and the second jaw outside it; the frame thrown on the door at 177 and the retriever's reel
after it is changed), `REEL_COW = 51` (the cow-path one the sheepdog holds up to the lead cow at 159.8:
a hill with a pale path).

## Which real film each reel shows

In the order of `scion/WHAT_WE_MADE.md`. The file is under `assets/`; the time is the second the frame
was cut at. A long film fills more than one reel. Items 1, 2 and 3 of that record (the 55 porthole films,
the first Tourkey Trouttown, the stick-figure explainer that was thrown out) are not in `assets/`, so no
reel is claimed for them; item 8 (the proposal and the outline) and item 12 (this film) are not films.

| n | File | At | What shows on the lid |
|---|---|---|---|
| 0 | films/p01.mp4 | 16.0 s | Porthole 01, the scissors film: the boot seen through the brass porthole |
| 1 | films/p03.mp4 | 17.0 s | Porthole 03, the chalk film: HOOK MONSTER on the slate, in the porthole |
| 2 | films/p14.mp4 | 17.0 s | Porthole 14, the scalpel film: the red leaf and the trout in the porthole |
| 3 | films/p35.mp4 | 17.0 s | Porthole 35, the pins film: the pinned photographs under green water |
| 4 | films/p44.mp4 | 17.0 s | Porthole 44, the pen film: the spiral disc in the porthole |
| 5 | voiced/p01.mp4 | 27.0 s | Porthole 01 with the voice: the boot standing in the river, the sub below |
| 6 | voiced/p03.mp4 | 30.0 s | Porthole 03 with the voice: the slate in the river |
| 7 | voiced/p14.mp4 | 30.0 s | Porthole 14 with the voice: the leaf, the trout and the sub in the river |
| 8 | voiced/p35.mp4 | 30.0 s | Porthole 35 with the voice: a trout swims past the pinned photographs |
| 9 | voiced/p44.mp4 | 26.0 s | Porthole 44 with the voice: the disc on its stand in the river |
| 10 | nobody-is-holding-the-chalk.mp4 | 182.0 s | Nobody Is Holding the Chalk, reel one: the slate in the river |
| 11 | nobody-is-holding-the-chalk.mp4 | 128.0 s | Nobody Is Holding the Chalk, reel two: the spiral disc on the desk |
| 12 | films/c10.mp4 | 13.0 s | Class film 10: Turkey in the porthole, the locked school |
| 13 | films/c13.mp4 | 26.0 s | Class film 13: two fish and the dinner bell |
| 14 | films/c16.mp4 | 20.0 s | Class film 16: the three-headed monster |
| 15 | films/c25.mp4 | 26.0 s | Class film 25: the fish with arms and legs, painting |
| 16 | films/c33.mp4 | 35.0 s | Class film 33: the bars across the window, a movie |
| 17 | voiced/c10.mp4 | 7.6 s | Class film 10 with the voice: the child's page, zigzag teeth in the ring, the second jaw outside |
| 18 | voiced/c13.mp4 | 6.0 s | Class film 13 with the voice: the child's page, two fish and a bell |
| 19 | voiced/c16.mp4 | 6.0 s | Class film 16 with the voice: the child's page, the boxy sub |
| 20 | voiced/c25.mp4 | 6.0 s | Class film 25 with the voice: the child's page, the fish across a bowl |
| 21 | voiced/c33.mp4 | 7.0 s | Class film 33 with the voice: the child's page, the tall bars |
| 22 | how-to-play-the-porthole-game.mp4 | 165.0 s | How to Play the Porthole Game, reel one: the fish and the bell |
| 23 | how-to-play-the-porthole-game.mp4 | 53.0 s | How to Play the Porthole Game, reel two: the pilot draws what is outside |
| 24 | how-to-play-the-porthole-game.mp4 | 355.0 s | How to Play the Porthole Game, reel three: the bars |
| 25 | films/m10.mp4 | 11.0 s | Making film 10: a cut-paper hand draws the zigzag teeth |
| 26 | films/m13.mp4 | 11.0 s | Making film 13: the two fish coming up out of the page |
| 27 | films/m16.mp4 | 11.0 s | Making film 16: the boxy sub coming up out of the page |
| 28 | films/m25.mp4 | 11.0 s | Making film 25: the fish with legs coming up out of the page |
| 29 | films/m33.mp4 | 11.0 s | Making film 33: the bars and the fish coming up out of the page |
| 30 | voiced/m10.mp4 | 69.0 s | Making film 10 with the voice: out into the river, the sub and the shell |
| 31 | voiced/m13.mp4 | 22.0 s | Making film 13 with the voice: an orange paper hand writes the sentence |
| 32 | voiced/m16.mp4 | 68.0 s | Making film 16 with the voice: out into the river |
| 33 | voiced/m25.mp4 | 70.0 s | Making film 25 with the voice: the sub's brass door in the river |
| 34 | voiced/m33.mp4 | 68.0 s | Making film 33 with the voice: the sub's lamp on the bars |
| 35 | tourkey-trouttown-the-class-plays.mp4 | 252.0 s | The Class Plays, reel one: the trout in the porthole |
| 36 | tourkey-trouttown-the-class-plays.mp4 | 380.0 s | The Class Plays, reel two: a paper hand at the page |
| 37 | tourkey-trouttown-the-class-plays.mp4 | 507.0 s | The Class Plays, reel three: the three-headed monster in the porthole |
| 38 | tourkey-trouttown-the-class-plays.mp4 | 634.0 s | The Class Plays, reel four: a wall of small cards |
| 39 | tourkey-trouttown-the-class-plays.mp4 | 760.0 s | The Class Plays, reel five: a paper hand writes under the bars |
| 40 | how-a-language-model-makes-a-film.mp4 | 106.0 s | How a Language Model Makes a Film: the porthole the judge looked at |
| 41 | who-held-the-chalk.mp4 | 110.0 s | Who Held the Chalk: the pinned photographs that were foraged |
| 42 | what-is-a-scion.mp4 | 56.0 s | What Is a SCION?, reel one: the river built in planes |
| 43 | what-is-a-scion.mp4 | 180.0 s | What Is a SCION?, reel two: the swarm at its desks |
| 44 | dont-pave-the-cow-paths.mp4 | 285.0 s | Don't Pave the Cow Paths, reel one: the cows in single file on the bank |
| 45 | dont-pave-the-cow-paths.mp4 | 98.0 s | Don't Pave the Cow Paths, reel two: the scion, a shoot cut from one tree |
| 46 | behind-the-chat.mp4 | 150.0 s | Behind the Chat: the conversation as a scrolling log |
| 47 | behind-the-chat-dogs.mp4 | 26.0 s | Behind the Chat, with Dogs: the porch at dusk, the lit door |
| 48 | films/cowpath-study-line.mp4 | 11.0 s | Cow-path study, the line: the stump that sprouts |
| 49 | films/cowpath-study-refuse.mp4 | 5.0 s | Cow-path study, the refusal: the cow on the bank above the trout |
| 50 | films/cowpath-study-shadow.mp4 | 6.0 s | Cow-path study, the shadow: cows at the gate at dusk |
| 51 | films/cowpath-act1.mp4 | 22.0 s | Cow-path cartoon, act one: the hill and the pale path the cows wore |
| 52 | films/cowpath-act-desk.mp4 | 18.0 s | Cow-path cartoon, the desk: the cow at the drawing desk |

## What was checked, and what was not

- MEASURED (asserts in `_selftest`, run on every `python3 films/swarm/dogs/props.py`): 53 reels; each
  film's reels sit together, in the order above; `reel_piles(..., 53)` draws 53 cans, each a different
  reel; `pile` draws as many things as asked; the breath plan ends with one bubble at `t_out` after a gap
  of more than 0.9 s and draws nothing at all afterwards; every sprite is RGBA and not empty.
- JUDGED from stills by the builder only (no critic has passed any of this): on `props_sheet.png` and in
  four stills composed with the real `porch.scene` and the real lead dog at scale 0.6, the reel reads as a
  can with a picture on its lid, the page as a stiff sheet in the mouth, the pile as a small wet row on the
  sill, the 53 cans as six leaning stacks, the thrown frame as the ring with the teeth and the second jaw.
- Known limits. At film size (`s=0.6`, a 29 px lid) a reel's frame is a patch of colour and shape, not a
  readable picture; the frame is only really seen close, or thrown on the door. A leader of film (`tail`)
  on a carried reel is mostly cut off by the dog's muzzle. Reel 46 holds a film that is itself an
  interface (the scrolling log); it is one can among 53 and should not be the one held to the lamp.
  What reels 36, 38 and 39 show was read off a thumbnail; the words for them above are approximate.
- UNKNOWN: everything in motion. Only stills and strips were rendered; nothing was played at speed.
  The boundary between `porch.surface` ice and `ice_sheet` in one frame was not tried.
