# PEOPLE.md · the children and their desk, as cut paper (shared by the five making films, mNN)

`films/people.py`. Everything is HANDMADE in code; nothing is foraged, so it adds nothing to any credits file.
The children are hands, sleeves and backs of heads cut from poster paper in four tones (teal, rust, ochre, plum:
never skin colours, never faces). Each piece is its own sheet with fibre, a lit and a dark cut edge and a shadow on
the piece beneath (the technique of `films/swarm/c16/world.py`, rebuilt here so this module needs only `kit.py`).
The Porthole Log is redrawn from `../sheets/master-1.png`, `master-2.png` and `../sheets/steps.json`; the children's
writing is lettered stroke by stroke from a pencil alphabet (no font is roughened, no photograph is pasted).

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))    # films/  (from films/swarm/mNN/scene_x.py)
import people as P
```
`python3 films/people.py` writes test stills of every piece to `films/stills/people/` (look at `hands.png`,
`writing_0..2.png`, `rub.png`, `heads.png`, `shoulder.png`, `scratch.png`, `pass.png`, `desk.png`, `classroom.png`,
`sheet_p1_NN.png`, `sheet_p2_NN.png`, `page2_close.png`).

## Conventions
- x right, y down; angles in degrees, positive = clockwise on screen; directions: 0 right, 90 down, 180 left, 270 up.
- Every drawing function takes `target` first: the kit's `Ink` or any PIL image (RGB or RGBA) of ANY size, so you can
  draw a desk plane larger than the frame and let `cam.py` look at it. They draw in place, in call order (painter's
  order, back to front). Nothing clears the frame except `desk()` and `classroom()`, which paint over everything.
- `t` is seconds; all motion is a pure function of `t`.
- Costs, per call at 960 x 540: hand 0.09 s, head_back 0.05 s, desk 0.01 s (0.2 s the first time), sheet 0.01 s
  (0.25 s the first time), write_on a few ms a line, lay 0.03 s, classroom 0.2 s (0.45 s the first time).
- `ink.caption` sits at y 472..516: keep the pencil point out of it.

## The children
`P.TONES[name]` = `{"hand", "sleeve", "cuff", "hair"}` (RGB) for `teal`, `rust`, `ochre`, `plum` (`P.TONE_NAMES`).
One child = one tone everywhere (hand, sleeve, head). Give the pilot, the first friend and the next friend three
different tones and keep them for the whole film. A `tone` argument is a name or your own dict of those four keys
(no skin colours).

## hand
`hand(target, x, y, angle=0, pose="write", tone="teal", scale=1, flip=False, t=0, lift=None, arm=None, edge=None, shade=0, alpha=1)`
-> `{"tip", "wrist", "knuckles", "down", "lift"}` (+ `"pencil_end"` for pencil poses, `"thumb"` for the flat ones,
`"stroke"` -1..1 for erase), all screen points.

A right hand seen from above (the child's own eye), jointed at every knuckle, with its wrist, ribbed cuff and
sleeved forearm running 1400 px off the frame. `flip=True` makes it a left hand (mirror image). At scale 1 the hand
is about 110 across the palm; a sheet laid at scale 1.26 (filling a 960 frame) suits hand scale 1 to 1.3.

| pose | (x, y) is | what moves with `t` | forearm leaves towards (angle 0) |
|---|---|---|---|
| `write` | the pencil point, on the paper | the grip works the point (quick, uneven, the heel stays put) | 38 (lower right) |
| `hover` | the spot on the paper under the lifted point (`lift` 16) | nothing but breath: held still | 38 |
| `erase` | the rubber: the pencil is turned round | rubs 5.5 strokes a second, 14 px end to end; `info["stroke"]` | 38 |
| `point` | the tip of the index finger | a slight tremor | 52 |
| `tap` | where the index finger lands | three taps a second: up slow, down fast, a rest; `info["down"]` is True on the wood | 52 |
| `hold` | the middle of the palm, flat on the page | fingers spread and close a hair | 52 |
| `pass` | a point on the sheet's edge, under the thumb | still | 52 |
| `scratch` | where the fingertips rake (put it on the hair) | the four fingers rake one after another, 2 a second | 60 |
| `fist_chin` | the top of the fist (where a chin would rest) | a slow sag and return | 82 (almost straight down) |

- Turning it: `angle` turns the whole arm about (x, y). Easier: `arm=` the screen direction the forearm should LEAVE
  by, e.g. `arm=90` straight down to the bottom edge (the child whose eye we are), `arm=270` up to the top edge (a
  child across the desk), `arm=0` off to the right. `P.aim(pose, arm, flip)` gives the angle. A left hand's natural
  `arm` is 100..150, a right hand's 30..80.
- The writing hand lies to the right of the point and covers the line above it to the right, as a real one does; it
  never covers what it has just written. `arm=55..65` drops it lower and shows more of the page.
- `lift` (px) raises any pose off the page: it shifts up-left and its shadow slides away and softens. Use `hover`
  for the long stuck moments, and `write` with `lift=6` for the air travel between strokes (see `write_tip`).
- `pass`: the four fingers are under the sheet, so the hand is cut off along the sheet's edge and the thumb lies on
  top. Draw the sheet first. Pass `edge=` the screen direction of that edge (for a sheet laid at angle A: its left
  and right edges run at 90 + A, top and bottom at A). Giver and taker: one unflipped, one `flip=True`.
- `shade` 0..1 darkens it (a hand in the dark of a thought), `alpha` fades it.
```python
tip = P.write_on(pg, P.where(1, "a2.1"), "freek out.", u, seed=5)       # pg = P.sheet(...), u = 0..1
f = P.lay(ink, pg, 480, 110, 0, 960 / 760)                               # page on the desk; f maps page px -> screen
x, y, down = P.write_tip(P.where(1, "a2.1"), "freek out.", u, seed=5)
P.hand(ink, *f(x, y), pose="write", tone="rust", t=t, lift=0 if down else 6)
P.hand(ink, 300, 260, pose="hold", tone="rust", flip=True, arm=120, t=t)   # the other hand steadies the page
```

## pencil, crumbs, rubbing out
- `pencil(target, x, y, angle=-52, eraser_down=False, lift=0, scale=1)` -> far end (x, y). A chewed yellow pencil on
  its own, 232 long. Its touching end is at (x, y) and it lies away along `angle`; `eraser_down=True` puts the rubber
  at (x, y) instead of the point. Lying in the groove: `P.pencil(ink, 120, 34, 0)`.
- `eraser_crumbs(target, x, y, n=12, seed=0, spread=34, scale=1)`: n little grey-pink rolls of rubber round (x, y).
  Same seed = same crumbs in the same order: raise n over time to let them pile up; brush them off by moving (x, y).
- `rub_mark(target, box, strength=1, seed=0, color=P.PAPER)`: a rubbed-out patch over `box` (x0, y0, x1, y1). Write
  the words first, then rub: the paper comes back scuffed and a shade greyer and the words stay as a ghost of
  graphite. strength 0..1 (ramp it up while the `erase` hand works), soft uneven ends. Then write over it.
- `graphite(target, lines, width=1.5, weight=1, seed=0, color=None)`: pencil lines (a list of screen polylines) with
  the paper's tooth, for drawings in the ring or the margin. weight 0.45 faint, 1 firm, 1.4 pressed.

## head_back
`head_back(target, x, y, tone="teal", scale=1, tilt=0, hair="short", turn=0, t=0, shade=0, alpha=1)`
-> `{"crown", "head", "nape", "ear_l", "ear_r", "shoulder_l", "shoulder_r"}`.
- The back of a child's head and shoulders: jumper (the tone's sleeve colour, so it joins the arms), ribbed collar,
  neck, ears, hair. (x, y) = the nape, where the collar sits. At scale 1 the shoulders are 316 wide and run 300 below
  (let the frame crop them); the crown is 182 above. Over-the-shoulder: `P.head_back(ink, 480, 470, "ochre", 1.15)`.
- `hair`: `short` (a tuft at the crown), `bun` (with its band), `braids` (two plaits on pins, swaying with `t`),
  `curly` (46 separate curls).
- `tilt` tips the head on the neck; `turn` -1..1 swings it left / right: the far ear goes behind the hair and a
  sliver of cheek shows (no features, ever). Looking up at the board: `tilt=-4, turn=0`. Looking at the neighbour on
  the right: `tilt=12, turn=0.8`. Animate both with `kit.ease`.
- Draw it AFTER the desk, sheet and writing hand (it is nearest the camera), and a `scratch` hand after it:
  `r = P.head_back(...); P.hand(ink, r["head"][0] + 58, r["head"][1] - 50, pose="scratch", tone=..., arm=75, t=t)`.

## desk, desk_far, cup, classroom
- `desk(target, t=0)` -> `{"groove": box, "tray": box}`. A school desk top filling the target: wood-grain laminate
  under one lamp, scuffs, dings, compass scratches, the ghost of a name sticker, the pencil groove along the top
  (x 70..600, y 22..46 at 960 wide) and the moulded tray top right (x 650..924, y 12..66) with a pencil stub and a
  block rubber in it. Scales with the target's width. It does not move.
- `desk_far(target, box, angle=0)` -> centre. One small desk from above (groove and tray along the far edge, dark
  front edge), with its shadow on the floor. `box` is its top; made for about 124 x 80.
- `cup(target, x, y, scale=1, die=True, t=0)`: a paper cup from above, rim radius 34 * scale, the die lying in the
  bottom of it showing three: not thrown. `die=False` for the empty cup.
- `classroom(target, t=0, sheets=None, cup_at="hero", children=True)` -> layout dict. The whole room from above:
  terrazzo floor with three windows' light, 4 rows of 5 desks, a small Porthole Log with its ring on every desk, a
  cut-paper child at each (jumper, back of the head, two sleeves with hands on the desk; four tones, four hairs),
  and the cup with the die on the HERO desk (`P.HERO` = row 2, col 2, just below the middle of the frame). Heads nod
  and some turn, some hands write, with `t`. `sheets={(row, col) or index: PIL image}` lays your own written page
  on those desks. `children=False` for the empty room.
- `room_layout(size)` -> `{"desks": [(cx, cy, w, h, angle, row, col)], "hero": index, "cup": (x, y), "sheet":
  (x, y, angle), "k"}` without drawing: aim the pull-back at `desks[hero]`.

## The Porthole Log
`sheet(size=(760, 980), page=1, porthole=None)` -> a fresh RGB PIL image of the printed page, to draw and write on.
- Page 1: header and number, zone 1 (Pilot line, Porthole #, Station, Clue, Rule), zone 2 (the ring with six
  die-face bolts: 1 top, then clockwise), zone 3 (the three questions with two ruled lines each), "Pass your paper
  left". Page 2: zone 4 (Probable / Plausible / Preposterous with their dice), zones 5 and 6 (each friend's Name, the
  two option plates with their buttons: green triangle and red circle for Turkey, blue cross and pink square for the
  trout, the dashed circle to draw the pick in, three endings with two ruled lines each), zone 7 (roll), zone 8.
- `porthole=NN` prints that porthole's own number, station, clue, rule and four options from `../seeds.json`
  (`P.porthole_info(NN)`); `None` prints the master's example (31, Galley B). All printed words are legible when the
  sheet fills a 960 frame (scale 1.26). For a closer shot ask for a larger size (e.g. `(1520, 1960)`) rather than
  enlarging: `where` and `write_on` follow the size.
- The page-1 footer omits the film time the master prints (it differs per porthole and is not in seeds.json).

`where(page, name, size=(760, 980))` -> `(x0, y0, x1, y1)` in that image's pixels. `where(page, None)` -> all of them.
- Names from steps.json, page 1: `name number station clue ring q1 a1 q2 a2 q3 a3 pass1`; page 2: `k1 k2 k3 name1
  pick1 pick1-plates draw1 bolt1 bolt2 bolt3 pass2 name2 pick2 pick2-plates draw2 bolt4 bolt5 bolt6 pass3 roll rolled
  circle gq ga mq ma`.
- Writing lines (the box is the space to write in; its bottom edge is the printed rule): `name.line`; `a1.1 a1.2
  a2.1 a2.2 a3.1 a3.2`; `name1.line name2.line`; `bolt1.1 bolt1.2` .. `bolt6.1 bolt6.2`; `rolled.line`; `ga.1 ga.2
  ma.1 ma.2`.
- Things to point at, circle or colour in: `ring.in`, `ring.out`, `die1`..`die6` (the ring's bolts), `margin.left`,
  `margin.right` (white space beside the ring, where a second drawing goes); `plate1a plate1b plate2a plate2b` (the
  option plates), `btn1a btn1b btn2a btn2b` (their round buttons), `draw1.circle draw2.circle`, `bolt1.die`..
  `bolt6.die`, `roll.die1`..`roll.die6`.

`lay(target, img, x, y, angle=0, scale=1, lift=0, shadow=0.45)` -> `f(sx, sy) -> (X, Y)`. Lays a page (any image)
on the desk, centre (x, y), with its shadow; `lift` raises it for a pass. `f` turns a page point (a `where` corner,
a `write_on` tip) into its place on the target. Upside down for the next child: `angle=180`.

## A child's pencil hand
`write_on(img, box, text, u=1, seed=0, weight=1, size=None, color=None)` -> the pencil tip `(x, y)`.
- Letters `text` along the line `box` stroke by stroke up to fraction `u` (0..1 of the time the line takes, lifts
  between strokes included). Ball-and-stick print: the baseline wanders, each word starts a touch higher or lower,
  letters differ in size and lean, a long line squeezes up (to 74 %) and then runs off the right edge. There is no
  wrapping: put the rest on the `.2` line yourself, as the child did.
- `img` is the sheet image (write before `lay`) or the Ink. `box` is a `where` line, or any box.
- `seed` picks the hand for that line: the same seed always writes the same line, so call it every frame with a
  rising `u`. Give each child their own run of seeds. `weight` 1 firm, 0.45 faint (a word added afterwards), 1.3
  pressed. `size` = x-height in px (default 0.40 of the box height; capitals and tall letters are 1.75 to 1.9 x that).
- Alphabet: a-z, A-Z, 0-9 and `. , ! ? ' " - : ( ) / & +`. To start a word part-way along a line, pad with spaces
  (`"            the sub."`) or pass a box that starts there.
- Tested at 960 wide with the sheet filling the frame: "freek out." and "he is going to be turkey diner." read
  clearly (`films/stills/people/writing_2.png`), as do the two-line bolt answers on page 2 (`page2_close.png`).
- `write_tip(box, text, u, seed=0, size=None)` -> `(x, y, down)` without drawing: `down` is False while the point
  travels between strokes. `write_plan(box, text, seed, size)` -> the plan: `.strokes` (polylines), `.upto(u)`,
  `.letters(u)` (characters finished, for one scratch of sound a letter), `.x_end` (where the line stopped), `.xh`.
- A false start, rubbed out and written again:
```python
b = P.where(2, "bolt2.1")
P.write_on(pg, b, "he dos not", ramp(t, 3.0, 5.0), seed=9)                    # written
P.rub_mark(pg, (b[0] + 40, b[1] - 2, b[0] + 120, b[3] + 3), ramp(t, 6.0, 7.2))   # rubbed (erase hand over it)
P.write_on(pg, (b[0] + 44, b[1], b[2], b[3]), "dos not get beck", ramp(t, 8.0, 10.5), seed=10)
```
  (`ramp` here is the kit's: `from kit import ramp, ease`; write `ramp(t, a, b)`.)

## slip
`slip(target, x, y, n, clue, scale=1, angle=0, picture=None)`: the small numbered slip the pilot was handed, lying
on the desk: hand-cut paper 260 x 150 at scale 1, the porthole number, the clue, and a square picture space on the
left (blank; pass `picture=` a PIL image, e.g. a frame of the porthole's film or `../stills/pNN.jpg`, to fill it).
(x, y) = its centre. Returns the picture space's screen box (angle 0) or its centre.

## What is still weak
- The hand is two drawings (flat hand; writing hand), not a rig that turns over: there is no palm-up view and no
  in-between from `hold` to `write`. Cut between poses or cross them in a few frames with `lift`.
- The forearm is straight to the edge of the frame: there is no elbow.
- `head_back` has no neck-turn beyond `turn` +-1 (a child never looks round at the camera, by rule).
- `classroom` is laid out flat from straight above; the children are tops and backs of heads at that scale.
