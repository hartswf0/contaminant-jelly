# WORLD.md · the shared pieces of class film c10 (porthole 10 · PA · "flapping Clam-Shell PA")

`films/swarm/c10/world.py`. Everything is HANDMADE in code; nothing is foraged (`films/credits/c10.json` is an
empty list; add to it only if you forage). Creatures and props are joint trees of cut-paper pieces (fibre, lit and
dark cut edges, a shadow on the piece beneath); the brass and the tin wall are turned / pressed from height profiles;
the pilot's drawing is 17 pencil strokes traced by eye from the child's sheet (the friends' two marks likewise).

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))        # films/swarm/c10
import world as Wd                                               # world.py puts films/ on sys.path itself (kit, kit_anim)
```

## Conventions
- Frame is 960 x 540; x right, y down; angles in degrees, positive = clockwise on screen.
- Every function takes `target` first: the kit's `Ink` (your `draw(t, ink)` argument) or any PIL image (RGB/RGBA).
  They draw in place, in call order (painter's order: draw back to front). Nothing clears the frame for you.
- `t` is seconds; all motion is a pure function of `t` (pass your scene's local time). Idle motion is built in.
- Creatures are designed facing LEFT; `flip=True` faces them right.
- Cost: about 0.1 s for a full frame (river + cabin + Turkey + trout). First call of each piece builds and caches it.
- Do not use `ink.paper()` after drawing. `ink.caption(text, size=27)` sits at y = 494; keep that band clear.
- Bolt numbering everywhere (sheet, cabin ring): 1 top, 2 upper right, 3 lower right, 4 bottom, 5 lower left,
  6 upper left. Die 1/4 = Probable, 2/5 = Plausible, 3/6 = Preposterous (`Wd.KIND[n]`).

## Palette
`Wd.PAL` (dict of RGB): paper, page, ink, graphite, table, water_top, water, water_deep, weed_far, weed_mid,
weed_dark, rock, moss, gravel, brass, brass_lit, brass_dark, tin, tin_lid, tin_dark, rust, cabin, lamp, turkey_*,
trout_*, brick, mortar, shell, shell_rib, nacre, fry, fry_dark, green, red, blue, pink, amber, ivory, badge, white.
`Wd.BUTTONS` = {triangle: green, circle: red, cross: blue, square: pink, hexagon: amber}. Helpers `Wd.dk(c, f)`,
`Wd.lt(c, f)` darken / lighten.

## Turkey
`turkey(target, x, y, scale=1.0, mood="calm", t=0.0, flip=False, look=(0,0), shade=0.0, alpha=1.0, feathers=None, pose=None, drop=True)`
- (x, y) = centre of his body. At scale 1 he is about 190 wide (fan shut) to 300 (fan open): crown 190 above the
  centre, feet 142 below, beak tip 137 to the left, tail to 130 right. Full-body cut-paper wild turkey: nine barred
  tail feathers each on its own pin, two wings, legs, neck, head, two-part beak, snood, wattle, eye, lid, beard.
- Hinged parts keep their pins: the lower mandible (`beak2`) turns on one pin under the upper (`beak`); wattle and
  snood hang from theirs; each tail feather has its own pin at the rump.
- `mood` (list in `Wd.MOODS`):
  - `calm` breathing, blinking, fan nearly shut
  - `look` neck craned forward to peer
  - `freak` THE PILOT'S WORD: wings beating out of step, fan snapped open, head whipping, beak wide, eyes huge,
    legs kicking, body hopping, loose feathers flying (turn those off with `feathers=False`)
  - `panic` wings clapped over the head, shivering, eyes darting side to side
  - `wave` near wing raised and waving
  - `slump` neck down, lid half shut
  - `gasp` slow wide breaths, beak opening (air running out)
  - `cheer` wings pumping alternately, hopping
- `look=(dx, dy)` moves the pupil (about -2.5..2.5). `shade` 0..1 darkens him (0.2 suits the lamplit cabin).
  `pose={"wing": -120, "beak": 10, ...}` overrides single joints (wing, wing_far, neck, head, beak, beak2, snood,
  wattle, leg, leg_far, tf0..tf8; negative wing angle = raised).
- Returns screen points `{"head", "beak", "eye", "wing_tip", "feet", "crown"}`.
- In his seat (inside view): `Wd.turkey(ink, 150, 470, 1.7, "freak", t, flip=True, shade=0.2)` puts him large in the
  lower left, facing the porthole, cropped by the frame. Draw him AFTER `cabin()`.
- `turkey_pose(mood, t, look)` returns `(pose, (dx, dy, lean))` if you need the raw joint angles.

## The tin from inside (Turkey's seat)
`cabin(target, t=0.0, port=(560, 246), r=178, lit=(), dim=0.0)` -> `{"port": (cx, cy), "r": r, "bolts": {1..6: (x, y)}}`
- Lays the tin's inside wall (pressed ribs, rust, riveted flanges and seams, lamp from above) OVER what you have
  already drawn, with a round hole: the river you drew first shows through thick greenish glass with a reflection.
  The brass ring (46 wide, so outer radius 224) carries six hex bolts, an iron hinge on the left and a brass dog on
  the right. Defaults `Wd.PORT`, `Wd.PORT_R`, `Wd.RING_W`.
- With the defaults the glass is the disc centre (560, 246) radius 178: stage the scene inside x 382..738, y 68..424.
- `lit=(1, 2)` makes those bolts glow amber. `dim` 0..1 darkens the cabin.
- Order for a Turkey-side frame: `river(...)`, your actors, `river_plane(.., "front")`, `cabin(...)`, `air_gauge(...)`,
  `turkey(...)`, `bolt_tag(...)`, `badge(...)`, `ink.caption(...)`.

`air_gauge(target, x, y, level=1.0, r=34, t=0.0)`: brass AIR dial centred at (x, y); level 1 = full, 0 = needle in
the red; the needle trembles more as it empties. Good spot beside the default porthole: (880, 150).

`brass_ring(r_in, r_out, bolts=6, start=-90.0, fittings=False)` -> RGBA image centred on the ring (paste with
`Wd._comp(target, img, (cx - img.width / 2, cy - img.height / 2))`). `bolt_xy(k, cx, cy, r_in, r_out)` -> bolt centre.
`glow(target, x, y, r=40, color=(255, 206, 110), strength=1.0)`: a soft halo.

## The tin from the river side
`tin(target, x, y, scale=1.0, t=0.0, mood="calm", flip=False, pitch=0.0, lid_open=0.0, spin=None, guests=0, lamp=1.0, look=(0,0), shade=0.0, alpha=1.0, drop=True, door_open=0.0, latch=0.0, tag=None, handle=None, dial=None)`
- (x, y) = centre of the tin's body. At scale 1: body 404 x 148 (x-200..x+204, y-74..y+74), lid and knob up to
  y-124, rudder and screw to x+266, skid to y+84. Bow (and the porthole) on the LEFT; `flip=True` turns it round
  (the ROLLS label still reads correctly).
- The round six-bolt brass porthole is centred 72 left and 2 below the body centre, glass radius 47 * scale (ring
  to 64 * scale). Turkey is seen in it, lamplit, in `mood` (same moods as `turkey`; his near wing is left out in the
  window so his face reads, except for wave and cheer). `guests=1..3` puts that many trout INSIDE with him, behind
  the glass and in front of Turkey ("The trout to come inside the sub!").
- Hinges, each on one visible pin (board's hinge list):
  - `door_open` degrees 0..180: the brass porthole door (ring + glass) swings out on its iron hinge at the LEFT of
    the ring, leaving the open round hole.
  - `latch` 0..1: the brass dog at the right of the ring; 0 holds the door shut, 1 is flipped up.
  - `lid_open` degrees 0..~80: the lid swings up on the pin at the stern, showing the dark mouth.
  - `tag`: None = none; a number = a paper tag on a string tied to the latch, hanging at that angle in degrees
    (swing it with `8 * Wd.settle(t, t_snap)`). `handle`: None = none; 0..1 = a wire carrying handle folded flat ..
    swung up over the top (the lunchbox reading). `dial`: None = none; 0..1 = a small air dial riveted to the side
    between porthole and label, needle at that level (0 = empty, in the red).
- `spin` = screw angle in degrees (default turns with t). `lamp` 0..1 dims the light inside. `pitch` tilts the tin.
- Returns screen points `{"port", "port_r", "hatch", "bow", "stern", "top", "lid_tip", "keel", "latch", "door_edge", "dial"}`
  (`port` = porthole centre; `hatch` = middle of the mouth under the lid; `bow` = nose; `latch` = the latch pin;
  `door_edge` = the free edge of the door).
- Example: `p = Wd.tin(ink, 520, 250, 1.5, t, mood="freak", door_open=120, latch=1, tag=6, handle=1.0, dial=0.5, guests=1)`.

## Brook trout
`trout(target, x, y, scale=0.6, t=0.0, kind=0, flip=False, pitch=0.0, pose="swim", phase=0.0, gaze=(0,0), jaw=None, shade=0.0, alpha=1.0, drop=True)`
- (x, y) = centre of the body. At scale 1 the fish is 296 long, 150 tall (nose 120 left of centre, tail 176 right).
- `kind` 0..3 = four individuals (different backs and bellies). `phase` de-syncs fish from each other.
- `pose`: `swim`, `still`, `look` (mouth a little open), `run` (flat out: fast short tail strokes, fins pinned,
  mouth open, body shaking; you move x yourself), `dance` (rocks on the beat, fin thrown up, bobbing), `gasp`,
  `point` (pectoral fin stuck out forward).
- `pitch` lifts the nose; `gaze=(dx, dy)` moves the pupil; `jaw` (degrees) overrides the mouth.
- Returns `{"mouth", "eye", "tail"}`.
- Example: `Wd.trout(ink, 300, 330, 0.7, t, kind=2, flip=True, pose="dance", phase=1.0)`.

## River planes
- `river(target, t=0.0, cam=0.0, seed=0, shafts=0.42)`: everything behind the actors: water with moving light
  shafts, then the far, mid and bed paper planes. The gravel bed's top edge is near y = 440.
- `river_plane(target, name, t=0.0, cam=0.0, seed=0, dy=0.0)`: one plane, name in `far`, `mid`, `bed`, `front`.
  Draw `front` (dark, soft weeds and rocks at the frame edges) AFTER the actors.
- `river_back(target, t, cam, shafts)`: just the water.
- `cam` is the camera x, about -160..160; planes slide by parallax 0.25 / 0.5 / 1.0 / 1.8 (`Wd.RIVER_PAR`), so pan
  by animating `cam` and move your actors by `-cam` yourself. `seed` gives a different stretch of river (use 0 for
  Turkey's side, 1 for the trout's side, to tell the two views apart).
- `weed(target, x, y, length=220, width=20, t=0.0, seed=0, color=None, lean=0.0, scale=1.0)`: one swaying blade
  (three hinged segments) rooted at (x, y).
- `bubbles(target, x, y, t=0.0, n=8, seed=0, rise=140, spread=26, size=5.0, rate=0.5)`: ring bubbles rising from (x, y).
- `make_rock(seed, w, h)` -> Sprite; lay it with `Wd.draw_sprite(target, spr, Wd.Tm(x, y))` (top-left at x, y).

## This porthole's subject: the clam-shell PA on the school's brick wall
- `brick_wall(target, x=0, y=0, w=330, h=540, seed=0, ragged=True, flip=False, shadow=True)`: the elementary
  school's mossy brick wall, top-left at (x, y); the broken ragged edge is on the right (`flip=True`: on the left).
- `clam_pa(target, x, y, scale=1.0, gape=6.0, t=0.0, flip=False, split=1.0, shade=0.0, alpha=1.0)`
  -> `{"hinge", "mouth", "lip_upper", "lip_lower"}`
  - Two ribbed clam valves on ONE brass pin at (x, y), bolted by an iron plate to the wall, opening to the RIGHT
    over a brass horn (`flip=True`: to the left). At scale 1 the shell reaches 258 px from the pin and each valve
    is 100 tall. `gape` = opening in degrees (0 shut .. 45 wide).
  - THE RULE (Single Hinge, SCION 13: jaw pivot): everything turns about that one pin. `split=1.0` (default) swings
    only the lower valve, the jaw; 0.5 opens both evenly; 0 only the upper.
  - `flap(t, rate=2.0, wide=38.0, rest=3.0)` -> a gape angle that snaps open and falls shut `rate` times a second:
    `c = Wd.clam_pa(ink, 262, 200, 0.9, Wd.flap(t))`.
- `sound_rings(target, x, y, t=0.0, direction=0.0, n=4, r0=24, r1=250, arc=64, color=(240,248,240), strength=1.0, rate=0.8, width=3.0)`:
  arcs of sound spreading from (x, y); direction 0 = right, 180 = left. Start them at `c["mouth"]`.
- The pilot's own things:
  - `fry(target, x, y, scale=1.0, angle=0.0, seed=0, shadow=True)`: one little crinkle-cut french fry (54..92 long
    at scale 1), centred at (x, y), upright at angle 0. Twelve different cuts by seed.
  - `fries(target, x, y, t=0.0, n=9, spread=(150, 80), scale=0.7, seed=0, lean=18.0, jitter=1.0)` -> list of centres:
    a little school of them bobbing about (x, y). ("Little french fries" are who the pilot says is outside.)
  - `padlock(target, x, y, scale=1.0, open_deg=0.0, swing=0.0)`: brass padlock, top of its body at (x, y), 68 x 54 at
    scale 1 with the steel shackle 44 above; `open_deg` swings the shackle open on its one leg ("a new locked
    school"); `swing` tilts the whole lock about (x, y).
  - `confetti(target, t=0.0, n=70, seed=0, box=(0, 0, 960, 540), fall=40.0)` and
    `music_note(target, x, y, scale=1.0, angle=0.0, kind=0)` (kind 1 = beamed pair) for the dance party.

## The table, the sheet, the pilot's drawing
- `table(target)`: the wooden table, fills the frame. `page(target, box=(150, -40, 1010, 600), angle=0.0)`: a blank
  sheet of paper with its shadow. `desk(target, box=Wd.PAGE_BOX)` = both.
- `sheet_ring(target, cx, cy, scale=0.8, lit=(), empty=(), t=0.0, alpha=1.0)` -> `{1..6: (x, y)}`: the worksheet's
  printed porthole, two thin circles (radii 214 and 264 times scale) with six little dice as bolts.
  `lit` = bolts glowing amber (written endings); `empty` = bolts shown as an empty dashed box (unwritten; on this
  sheet all six are written). For the ending: `Wd.sheet_ring(ink, 400, 270, 0.9, lit=(1, 2, 3, 4, 5, 6))`.
- `pilot_drawing(target, cx, cy, progress=1.0, scale=0.8, part="all", alpha=1.0)`: the child's pencil drawing, drawn
  as far as `progress` 0..1, grain by grain along each stroke in order. (cx, cy) = the ring's centre; `scale` =
  screen px per photograph px (use the same cx, cy, scale as `sheet_ring`).
  - `part="jaw"`: 13 strokes inside the ring: the slanted box (top line, left side, three bottom lines) and the row
    of zigzag teeth. It spans x -127..+158, y -154..+50 photograph px from the centre.
  - `part="outside"`: 4 strokes: the second, looser jaw to the right of the ring, x +355..+688, y -115..+41.
  - `part="all"`: both; the jaw takes progress 0..0.56 (`Wd.JAW_SHARE`), the outside one 0.56..1. At scale 0.8 with
    cx = 400 the outside jaw reaches x = 950, so keep cx <= 400 at that scale (or scale 0.75).
  - `Wd.PILOT_STROKES`: the raw list, dicts with `pts` (photograph px from the ring centre), `weight` 0..1,
    `sharp`, `part`.
- `pilot_tip(cx, cy, progress, scale=0.8, part="all")` -> `(x, y, down)`: where the pencil point is; `down` is False
  while it hops between strokes.
- `pencil(target, x, y, angle=-52.0, lift=0.0, scale=1.0)`: a yellow pencil (258 long) with its point at (x, y),
  lying up and to the right; `lift` raises it (shadow slides away).
- `pencil_line(target, xy, text, size=30, progress=1.0, width=None, seed=0, color=None)` -> y under the last line:
  the child's words written in pencil, letter by letter with `progress`; wraps at `width`.

```python
P = Wd.ramp(t, 0.6, 9.0)                       # drawing time
Wd.desk(ink); Wd.sheet_ring(ink, 400, 262, 0.8)
Wd.pilot_drawing(ink, 400, 262, P, 0.8)
x, y, down = Wd.pilot_tip(400, 262, P, 0.8)
Wd.pencil(ink, x, y, lift=0 if down else 14)
Wd.badge(ink)
```

## Hinged cards, brads, springs (the board's "everything turns about one visible pin")
- `settle(t, t0, amp=1.0, freq=2.2, damp=4.5)` -> number: secondary motion. A damped swing that starts at `amp`
  when the parent stops at `t0` and is at rest inside about a second (0 before t0). Add it to any angle:
  `tag=10 * Wd.settle(t, 36.2)`, `pose={"wattle": 30 * Wd.settle(t, 2.0)}`, a fry's `angle`.
- `brad(target, x, y, r=7)`: a brass paper fastener, the visible pin of a hinge.
- `swing_card(target, img, pin, angle=0.0, at=None, pinned=True, shadow=0.42)`: lay any flat PIL image (a card, or a
  whole 960 x 540 scene rendered to its own image) turned about ONE pin. `pin` = the pin's place on the card;
  `at` = where that pin is on screen (default the same); angle clockwise, 0 = square. Draws the brad. A scene
  change: render the new scene to `img = Image.new("RGB", (960, 540))` with the same world calls, then
  `Wd.swing_card(ink, img, (0, 0), angle=-90 * (1 - Wd.ease(t, a, b)))` swings it in from above about the top-left
  corner (about 20 ms extra per frame).
- `pick_card(target, kind, who, pick, initial, angle=0.0, pin_at=(250, 150), size=(460, 240), drawn=1.0, pressed=1.0, lit=1.0, color=None)`:
  the friend's pick on a card that flips up about a brad in its top-left corner (`pin_at` on screen): the
  controller button `kind` pressed and lit, `who` and `pick` in type, the worksheet's dashed ring with the friend's
  own pencil mark drawn to `drawn` 0..1, and the initial once the mark is done. angle 0 = square; about -100 =
  swung away. `Wd.pick_card(ink, "circle", "Turkey thinks", "Morning intercom", "M.", angle=-100 * (1 - Wd.ease(t, 0.2, 0.8)), drawn=Wd.ramp(t, 0.9, 1.6))`
  and for the next friend `("square", "The trout think", "Confiscated lunchbox", "S.")`.
- `friend_mark(target, kind, cx, cy, progress=1.0, scale=1.6)`: just the friend's pencil mark, traced from the back
  of the sheet: `circle` = a tall oval not quite shut (28 x 42 px times scale), `square` = a small lopsided square
  (27 x 21). `friend_tip(kind, cx, cy, progress, scale=1.6)` -> `(x, y, down)` for the pencil.
- `feather(target, x, y, scale=1.0, angle=0.0)`: one loose barred turkey feather (50 long), quill end at (x, y).
- `plank(target, x0, y, x1, thick=26, seed=0)`: a wooden shelf board (for a kitchen shelf of tins; a tin at
  scale s sits on it with its body centre 84 * s above y).

## Buttons, dice, tags, badge
- `button(target, kind, x, y, r=40, pressed=0.0, lit=0.0)`: one domed controller button centred at (x, y):
  `triangle` green, `circle` red, `cross` blue, `square` pink, `hexagon` amber. `pressed` 0..1 pushes it in,
  `lit` 0..1 gives it a halo. This sheet's picks: first friend `circle` ("Morning intercom"), next friend `square`
  ("Confiscated lunchbox").
- `controller(target, x, y, scale=1.0, pressed=None, press=1.0, lit=1.0)` -> `{kind: (x, y)}`: all five on a
  riveted plate 330 x 84 centred at (x, y), in the order triangle, circle, cross, square, hexagon.
- `die(target, n, x, y, size=44, angle=0.0, shadow=True)`: ivory die face n (1..6) centred at (x, y).
- `die_cup(target, x, y, r=62, n=5, t=0.0, rattle=0.0)`: leather dice cup from above with the die still in it
  (the unthrown die of the ending); `rattle` 0..1 jitters the die.
- `bolt_tag(target, n, x=18, y=14)`: for the top LEFT corner: die face n and a paper tag reading Probable /
  Plausible / Preposterous.
- `badge(target, n=10, x=None, y=14)`: the porthole number, white on a dark rounded badge, top RIGHT corner
  (occupies x 866..946, y 14..64). Call it last, every frame.

## Lower-level kit (if you need a piece of your own)
`cut(pts, color, deco=None, curve=True, seed=0)` -> Sprite cut from paper along design-coordinate points (`deco(d, L, S)`
prints on it: `d` = ImageDraw, `L(x, y)` maps design coords, `S` = supersample); `compose([sprites])` glues pieces;
`draw_sprite(target, spr, M, shadow=(dx, dy, blur, strength))` lays one under an affine `M` built from
`Tm(x, y) @ Rm(deg) @ Sm(sx, sy)`; `Puppet()` with `.add(name, spr, pivot, parent, z)` and `.draw(target, pose, M)` is
the joint tree; `apply(M, p)` maps a point; `shadow_of(alpha, blur, strength)`; `rrect`, `circ`, `catmull`, `xf`.
Re-exported from the kit: `W, H, FPS, clamp, ramp, smooth, ease, lerp, font`, and `Wd.KA` = kit_anim.

## Test
`python3 films/swarm/c10/world.py <out_dir>` writes contact sheets `table.png`, `cabin.png`, `river.png`, `ending.png`
exercising every function.
