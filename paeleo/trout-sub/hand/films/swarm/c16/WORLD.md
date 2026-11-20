# WORLD.md · the shared pieces of class film c16 (porthole 16 · Aft · "Identical twin Turkey Sub waving back")

`films/swarm/c16/world.py`. Everything is HANDMADE in code; nothing is foraged (`films/credits/c16.json` is an empty
list and there is no `films/sources/c16/`; add to both only if you forage). Creatures and props are joint trees of
cut-paper pieces in poster colour (fibre, a lit and a dark cut edge, a shadow on the piece beneath); the brass and
the tin wall are turned / pressed from height profiles; the pilot's drawing is 29 pencil strokes traced by eye from
the child's sheet (the friends' two marks likewise). The cut-paper kit, Turkey's side view, the trout, the tin, the
river and the table are the ones c10 set (same world); the rule, Turkey's rear and front drawings, the twin, both
monsters and the pencil strokes are this film's.

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))        # films/swarm/c16
import world as Wd                                               # world.py puts films/ on sys.path itself (kit, kit_anim)
```

## Conventions
- Frame 960 x 540; x right, y down; angles in degrees, positive = clockwise on screen.
- Every drawing function takes `target` first: the kit's `Ink` (your `draw(t, ink)` argument) or any PIL image.
  They draw in place, in call order (painter's order, back to front). Nothing clears the frame for you.
- `t` is seconds; all motion is a pure function of `t`. To shoot on twos pass `Wd.on_twos(t)`.
- About 0.25 s for a full frame. The first call of each piece builds and caches it.
- `ink.caption(text, size=27)` sits at y = 494 (band y 472..516): keep it clear. Do not call `ink.paper()` after drawing.
- Bolts everywhere: 1 top (12 o'clock), 2 upper right, 3 lower right, 4 bottom, 5 lower left, 6 upper left.
- Lettering: the board allows only the two option names on the pick cards, the initials B. and W., and the badge.
  Nothing in world.py letters anything else unless you ask it to (`bolt_tag(label=True)`, `pick_card(who=...)`: don't).

## Palette
`Wd.PAL` (dict of RGB): paper, page, ink, graphite, table, water_top, water, water_deep, weed_far, weed_mid, weed_dark,
rock, moss, gravel, brass, brass_lit, brass_dark, tin, tin_lid, tin_dark, rust, cabin, lamp, turkey_body, turkey_bronze,
turkey_skin, turkey_red, turkey_dkred, turkey_beak, trout_back, trout_belly, trout_fin, green, red, blue, pink, amber,
ivory, badge, white. `Wd.MONSTER_KINDS[k]` = the monster's hide, belly, crest, eye, spot (plum hide, buff belly, orange
crest). `Wd.BUTTONS` = {triangle: green, circle: red, cross: blue, square: pink, hexagon: amber}. `Wd.CHALK` (white
pencil for outlines over dark), `Wd.DARK` (dark pencil on brass). `Wd.dk(c, f)`, `Wd.lt(c, f)` darken / lighten.

## THE RULE: Temporal Double (D = 12 frames)
`Wd.D = 12`, `Wd.DT = 0.5` (seconds). Never tune it by eye; use these helpers.
- `on_twos(t)` -> t snapped to 12 poses a second. `frame_of(t)` -> frame number.
- `delayed(fn, t, n=1)` -> `fn(t - n * 0.5)`: any driven value as it was n doubles ago.
- `doubles(fn, t, n=2)` -> `[fn(t), fn(t - 0.5), ...]` (three heads: `n=3`).
- `arrive(t, t0)` -> 0 not yet, 1 pencil outline only (for exactly D frames), 2 painted double has landed. Use it for the
  pick cards, die faces and the brass rim: `s = Wd.arrive(t, 20.2); if s: Wd.pick_card(..., paint=0.0 if s == 1 else 1.0)`.
- `wave(t, energy=1.0, t0=0.0, beat=1.0)` -> Turkey's wing, in wave-degrees: 0 at rest, up to 112 (energy 1.0), 44 (energy
  0.25); it swings between 40 % and 100 % of its reach once per `1 / beat` seconds from `t0`. `energy` is a number or a
  function of time (1.0 fresh .. 0.2 spent).
- `twin_wave(t, energy, t0, beat)` -> `-wave(t - DT, ...)`. The invariant `twin_wave(f) == -wave(f - 12)` holds exactly
  (asserted in the test). A NEGATIVE wing draws the mirror image.
- `wave_pose(t, energy=1.0, t0=0.0, beat=1.0, twin=False)` -> `{"wing", "tip", "wattle", "snood", "mirror"}`: the driven
  wing plus the follow-through that hangs off it (tip feathers, wattle, snood lag behind; the less energy, the longer the
  lag). Splat it into `turkey_back`, `turkey_front` or `tin`:
  `Wd.turkey_back(ink, *Wd.SEAT_TURKEY, **Wd.wave_pose(t, energy, 13.0))`;
  the twin: `Wd.tin(ink, x, y, s, t, flip=True, **Wd.wave_pose(t, energy, 13.0, twin=True))`.
- `needle(t, drops=(), start=1.0, notch=1/6)` -> air level: `start` less one notch per time in `drops`; each notch falls as
  two ticks D frames apart, each overshooting and settling. Never rises. `Wd.air_gauge(ink, 104, 392, Wd.needle(t, (13.5, 14.5, 15.5)), 50)`.
- `settle(t, t0, amp=1.0, freq=2.2, damp=4.5)` -> a damped swing starting at `amp` at `t0` (0 before): the clink when
  something seats, a nod, a wobble.
- `monster_idle(t, k)` -> head k's standing sway `{"dx", "dy", "tilt", "look"}`: head k does what head 0 did k * D frames ago.
- `bubble_pair`, `trout_pair` (below) carry the rule for bubbles and trout.

## Turkey: three drawings on one shoulder pin (Turn Lab)
All three are cut-paper wild turkeys. `wing` is always wave-degrees; `mirror=True` (or a negative wing) is the exact
mirror image about the vertical line through (x, y).

`turkey_back(target, x, y, scale=1.0, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, head="glass", t=0.0, shade=0.0, alpha=1.0, drop=True, lean=0.0)`
- REAR three-quarter view, in his seat. (x, y) = the waving shoulder's pin. At scale 1 his back runs from the pin to
  155 right and 175 below, his crown is 160 above and 30 right, the tail hangs to 300 below (let the frame crop it);
  the wing is 175 long: at wing 0 it hangs down, at 112 it is up and to the LEFT (140 degrees from hanging).
- `head="glass"`: the back of his head, a sliver of face, looking out. `head="seat"`: the profile drawing, turned to
  the seat beside him (two drawings swapped on the neck pivot: switch, hold, never tween).
- `tip` fans / drags the five primaries (each on its own pin); `wattle`, `snood` swing those; `lean` tips the neck.
- Returns `{"pin", "wing_tip", "head", "neck", "crown"}`.
- Seat: `Wd.turkey_back(ink, 748, 398, 1.45, shade=0.16, t=t, **Wd.wave_pose(t, e, t0))` (`Wd.SEAT_TURKEY`).
  The other turkey of bolt 3, lower left, wing crossing in FRONT of the brass rim (draw it after `cabin()` and
  `air_gauge()`; its drop shadow is the contact shadow on brass and gauge):
  `Wd.turkey_back(ink, 212, 430, 1.45, shade=0.16, t=t - Wd.DT, **{**Wd.wave_pose(t, e, t0, twin=True), "mirror": True})` (`Wd.SEAT_OTHER`).

`turkey_front(target, x, y, scale=1.0, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, t=0.0, fan=0.85, shade=0.0, alpha=1.0, drop=True)`
- FRONT view: fan open behind him, head on, beak, snood, wattle, one folded wing and the waving wing on OUR right.
  (x, y) = the waving shoulder's pin (the same pin as `turkey_back`: cut from one to the other on it). Body centre is
  46 * scale left and 31 * scale below the pin; about 300 wide and 260 tall at scale 1. Returns `{"pin", "wing_tip", "head", "body"}`.
- Inside a tin's porthole you do not call this: `tin()` draws him there.

`turkey(target, x, y, scale=1.0, mood="calm", t=0.0, flip=False, look=(0,0), shade=0.0, alpha=1.0, feathers=None, pose=None, drop=True)`
- The SIDE view (c10's), body centre at (x, y), facing left (`flip=True` right). Moods: calm, look, freak, panic, wave,
  slump, gasp, cheer. `pose={"wing": -120, ...}` overrides joints. Kept for completeness; this film's board uses the
  other two.

## The tin from inside (Turkey's seat)
`cabin(target, t=0.0, port=(450, 236), r=186, lit=(), dim=0.0)` -> `{"port", "r", "bolts": {1..6: (x, y)}}`
- Lays the tin's inside wall (pressed ribs, rust, riveted seams, lamp) OVER what is already drawn, with a round hole:
  what you drew first shows through thick glass. The brass ring is 46 wide (outer radius 232) with six hex bolts, an
  iron hinge left, a brass dog right. Defaults `Wd.PORT`, `Wd.PORT_R`, `Wd.RING_W`. Glass: x 264..636, y 50..422.
- `lit=(3,)` makes those bolts glow amber. `dim` 0..1 darkens the cabin.
- `air_gauge(target, x, y, level=1.0, r=34, t=0.0)`: brass AIR dial, six notches (level k/6 sits on a long tick);
  level 1 = full. Seat position `Wd.SEAT_GAUGE` = (104, 392, 50).
- `brass_ring(r_in, r_out, bolts=6, start=-90.0, fittings=False)` -> RGBA image centred on the ring; lay it with
  `Wd._comp(target, img, (cx - img.width / 2, cy - img.height / 2))`. `bolt_xy(k, cx, cy, r_in, r_out)` -> bolt centre.
- `ring_outline(target, cx, cy, r_in, r_out, bolts=True, seed=0, alpha=1.0, color=None)`: the ring as a pencil outline
  (the pencil ring that becomes the brass rim D frames later): `Wd.ring_outline(ink, 450, 236, 186, 232)`.
- `glow(target, x, y, r=40, color=(255, 206, 110), strength=1.0)`: a soft halo.

`seat(target, t=0.0, wave_kw=None, twin_kw=None, level=1.0, heads=True, twin_lamp=1.0, twin_occupants=1, lit=(), ripple_t0=None, seed=0)`
-> `{"twin", "turkey", "cabin", "heads"}`: a whole SEAT frame in the standard layout (river, three monster heads on
their necks behind the twin tin, front weeds, optional ripple, cabin, gauge lower left, Turkey's back lower right).
Use it as is, or copy its eleven lines and change them. Layout constants: `SEAT_TWIN = (440, 296, 0.48)`,
`SEAT_HEADS` (neck root x, head joint x, y, flip, bend) with `SEAT_HEAD_SCALE = 0.72`, `SEAT_GAUGE`, `SEAT_TURKEY`,
`SEAT_OTHER`.
```python
e = lambda tt: Wd.lerp(1.0, 0.8, Wd.ramp(tt, 13, 20))
Wd.seat(ink, t, Wd.wave_pose(t, e, 13.0), Wd.wave_pose(t, e, 13.0, twin=True), level=Wd.needle(t, (17.0, 18.0)), twin_lamp=Wd.ease(t, 13.0, 13.4))
Wd.badge(ink); ink.caption("Wave at his twin turkey.", size=27)
```
Draw order if you build it yourself: `river`, `monster_neck` x 3, `tin(flip=True)`, `river_plane(.., "front")`,
`ripple`, `cabin`, `air_gauge`, `turkey_back`, the other turkey, `die_at_bolt`, `pick_card`, `camera`, `badge`, caption.

## The tin from the river side (and THE TWIN)
`tin(target, x, y, scale=1.0, t=0.0, flip=False, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, occupants=1, wing2=None, lamp=1.0, dial=None, pitch=0.0, lid_open=0.0, spin=None, shade=0.0, alpha=1.0, drop=True, door_open=0.0, latch=0.0)`
- A riveted bread-roll tin, body centre (x, y). At scale 1: body 404 x 148 (x-200..x+204, y-74..y+74), lid, knob and brass
  pipe up to y-142, rudder and screw to x+266, skid to y+84. The round six-bolt brass porthole is 72 left and 2 below
  the centre, glass radius 47 * scale, ring to 64 * scale. `flip=True` turns the tin round (porthole on the right; the
  ROLLS label still reads). For two tins face to face: left one `flip=True`, right one `flip=False`.
- Turkey shows in the porthole, FRONT view, lamplit, waving: `wing, tip, wattle, snood, mirror` as `turkey_front`.
  THE TWIN is the same call with the twin's wave: `Wd.tin(ink, 760, 300, 0.62, t, **Wd.wave_pose(t, e, t0, twin=True))`.
- `occupants`: 1 Turkey, 2 = two turkeys in the one window (bolt 3's reflection; the second is drawn D frames behind;
  `wing2` its wing), 0 nobody. `lamp` 0..1: 0 = the round window dark (A2), fade it up for A3.
- `dial`: None, or 0..1 = a small six-notch air dial riveted to the side (use `Wd.needle(...)`).
- Hinges on visible pins: `lid_open` (degrees), `door_open` (degrees, the porthole door), `latch` (0..1). `spin` = screw
  angle (default turns with t). `pitch` tilts the tin.
- Returns `{"port", "port_r", "pipe", "dial", "bow", "stern", "top", "keel", "hatch", "lid_tip", "latch", "door_edge"}`.
  `pipe` = the mouth of the brass pipe on the lid: let bubbles go from there.

## Brook trout
`trout(target, x, y, scale=0.6, t=0.0, kind=0, flip=False, pitch=0.0, pose="swim", phase=0.0, gaze=(0,0), jaw=None, shade=0.0, alpha=1.0, drop=True)`
- Body centre (x, y); at scale 1 the fish is 296 long, 150 tall (nose 120 left of centre, tail 176 right). Faces left;
  `flip=True` right. `kind` 0..3 = four individuals. `pose`: swim, still, look, run, dance, gasp, point. `pitch` lifts
  the nose; `gaze` moves the pupil; `jaw` opens the mouth. Returns `{"mouth", "eye", "tail"}`.

`trout_pair(target, path, t, scale=0.5, kinds=(0, 2), **kw)` -> two trout on ONE path, the second where the first was D
frames ago. `path(t)` -> `(x, y)` or `(x, y, pitch)`; make it move at least 150 px a second or hold them apart with a
curve, or the two overlap. `Wd.trout_pair(ink, lambda tt: (860 - 190 * Wd.ease(tt, 32, 34), 440 + 10 * math.sin(tt * 2)), t, 0.5, pose="look")`.

## River planes
- `river(target, t=0.0, cam=0.0, seed=0, shafts=0.42)`: water with moving light shafts, then far, mid and bed planes
  (gravel bed top near y = 440). `seed=0` for Turkey's side, `seed=1` for the trout's side.
- `river_plane(target, name, t=0.0, cam=0.0, seed=0, dy=0.0)`: one plane: far, mid, bed, front. Draw `front` (dark soft
  weeds at the frame edges) AFTER the actors. `river_back(target, t, cam, shafts)`: just the water.
- `cam` = camera x, about -160..160 (parallax `Wd.RIVER_PAR`).
- `weed(target, x, y, length=220, width=20, t=0.0, seed=0, color=None, lean=0.0, scale=1.0)`: one swaying blade.
- `make_rock(seed, w, h)` -> Sprite; `Wd.draw_sprite(target, spr, Wd.Tm(x, y))`.
- `bubble(target, x, y, size=6.0, alpha=1.0)`: one ring bubble.
- `bubble_pair(target, x, y, t, t0, rise=170, size=6, drift=10, life=2.2, n=2, seed=0)`: a bubble let go at (x, y) at
  `t0` and its double D frames behind on the same path; `n=4` for two turkeys' worth. One call per wave:
  `for tw in (13.5, 14.5, 15.5): Wd.bubble_pair(ink, p["pipe"][0], p["pipe"][1], t, tw)`.
- `bubbles(target, x, y, t, n=8, seed=0, rise=140, spread=26, size=5.0, rate=0.5)`: a looping string (not rule-bound; avoid).
- `ripple(target, cx, cy, r, t, t0=0.0, amp=7.0, speed=150.0, life=2.4)`: the pond mirror's one slow ripple: bends what
  is already drawn inside the disc with a ring spreading from the centre from `t0`. Call after the actors behind the
  glass and before `cabin()`: `Wd.ripple(ink, 450, 236, 186, t, 22.4)`. For a standing shimmer (bolt 3) call it again
  with later `t0`s and a small `amp`.

## This porthole's subject
### The giant three-headed monster (the pilot's "who is outside")
Plum cut-paper hide with scales and spots, buff belly plates, orange spines; each head has a hinged jaw with teeth, an
eye with a lid, four crest spines on pins and a barbel.

`monster_neck(target, base, head, scale=1.0, bend=0.25, tilt=0.0, jaw=4.0, look=(0,0), flip=False, kind=0, t=0.0, links=5, lid=-10.0, shade=0.0, alpha=1.0, drop=True)`
-> `{"nose", "eye", "joint"}`
- One neck (five overlapping links) and head. `base` = where the neck starts (the body, or below the frame), `head` =
  where it joins the head: screen points. The head faces LEFT (`flip=True` right), reaches 160 * scale beyond `head`
  and is 110 * scale tall. `bend` bows the neck sideways (fraction of its length, sign picks the side). `tilt` = degrees
  the nose dips (negative lifts). `jaw` = degrees open. `look` = pupil offset (-3..3). `kind` 0..2 = which head.
- From Turkey's seat (parts only, rising from below the glass, one after another):
```python
for k, (bx, hx, hy, fl, bd) in enumerate(Wd.SEAT_HEADS):
    up = Wd.ease(t - k * Wd.DT, 9.8, 11.0)                      # head k rises D frames after head k-1
    i = Wd.monster_idle(t, k)
    Wd.monster_neck(ink, (bx, 520), (hx + i["dx"] * 0.5, Wd.lerp(560, hy, up) + i["dy"] * 0.5), 0.72, bd, 10 + i["tilt"], 4, i["look"], fl, k, t, shade=0.12)
```
`monster(target, x, y, scale=1.0, t=0.0, heads=None, shade=0.0, alpha=1.0, drop=True, body=True)` -> `{"heads": [...], "roots": [...]}`
- The whole thing, for the river side. (x, y) = centre of its bulk (620 x 330 times scale: x-310s..x+310s,
  y-150s..y+180s; put y low so the frame crops it). Necks leave the shoulders at `Wd.MONSTER_ROOTS` and rise about
  250 * scale, swaying, each head D frames behind the last. `heads` = None or three dicts overriding `at` (absolute
  head joint), `tilt`, `jaw`, `look`, `flip`, `bend`, `lid`. To turn the three heads one after another:
  `tl = Wd.doubles(lambda tt: 30 * Wd.ease(tt, 37.0, 37.6), t, 3); Wd.monster(ink, 520, 470, 1.0, t, heads=[{"tilt": 14 + a} for a in tl], shade=0.18)`.

### The two-headed tin monster (the trout's pick; bolt 5)
`tin_monster(target, x, y, scale=1.0, t=0.0, lift=0.0, nod=(0.0, 0.0), tilt=0.0, flip=False, port=None, shade=0.0, alpha=1.0, drop=True)`
-> `{"rim", "left_eye", "right_eye", "top"}`
- One skirt of pressed bread-roll tin, two round tin heads on collars, each with one brass-rimmed lamplit window for an
  eye and a little brass funnel. It is cut in the tin's own design frame to FIT THE SUBMARINE: give it the same
  `(x, y, scale, flip)` as the `tin()` it comes down over; `lift=0` seats it flush (rolled rim on the tin's top seam,
  46 * scale above the tin's centre; its rivet row directly over the tin's, same pitch; lid, knob and pipe inside it).
  `lift` = screen px above seated (300 = clear of the frame top at scale 0.8). Skirt 452 * scale wide; heads reach
  268 * scale above the tin's centre when seated.
- `port=p` (the dict `tin()` returned) lays the tin's brass porthole flange back IN FRONT of the skirt: the rim passes
  in front of the tin's shoulder and behind the porthole. `nod=(left, right)` leans the heads on their collars.
```python
p = Wd.tin(ink, 330, 330, 0.8, t, dial=lvl, **Wd.wave_pose(t, e, t0))
drop_ = lambda tt: 300 * (1 - Wd.ease(tt, 37.2, 39.0)) - 10 * Wd.settle(tt, 39.0, 1.0, 3.0, 6.0)     # down, one small bounce
Wd.tin_monster(ink, 330, 330, 0.8, t, lift=max(0.0, drop_(t)), nod=(5 * Wd.settle(t, 39.0), -5 * Wd.settle(t, 39.0 + Wd.DT)), port=p)
```
### Blanks, camera
- `empty_stage(target)`: an empty, evenly lit stage of plain paper filling the frame. Seat blank: `Wd.empty_stage(ink);
  Wd.cabin(ink, t); Wd.die_at_bolt(ink, 1, lit=False); Wd.badge(ink)`. River blank: `Wd.empty_stage(ink); Wd.die(ink, 4, 480, 270, 80)`.
- `camera(target, cx, cy, zoom=1.0)`: push in on everything drawn so far: (cx, cy) goes to the frame centre, enlarged by
  `zoom` (it never looks off the edge). Call before the badge and caption. A4: `Wd.camera(ink, 330, 320, Wd.lerp(1.0, 1.35, Wd.ease(t, 16.5, 17.3)))`.

## The table, the sheet, the pilot's drawing
- `table(target)`: the wooden table, fills the frame. `page(target, box=(150, -40, 1010, 600), angle=0.0)`: a blank sheet
  with its shadow. `desk(target, box)` = both.
- `sheet_ring(target, cx, cy, scale=1.6, lit=(), empty=(), t=0.0, alpha=1.0)` -> `{1..6: (x, y)}`: the worksheet's printed
  porthole: two thin circles (radii 214 and 264 times scale) and six little dice in the band. `lit` = bolts glowing
  amber; `empty` = bolts shown as an empty dashed box.
- `pilot_drawing(target, cx, cy, progress=1.0, scale=1.6, part="all", alpha=1.0)`: the child's pencil drawing, drawn as far
  as `progress`, grain by grain along each stroke in the child's order: the leaning box, the dome, the round window
  (circle, scribbled dark, scribbled AGAIN starting exactly D frames later), three little blocks on the left, an
  upright block and a fin on the right, faint loose curves, and the faint turkey head to the right, beak pointing at
  the box. Same (cx, cy, scale) as `sheet_ring`. It spans x -89..+203, y -200..-27 sheet units from the ring's centre
  (the top third only: at scale 1.6 with the centre at (400, 440) it sits in x 258..725, y 120..397).
  `part`: "all", or one group drawn 0..1: box, dome, window, scribble1, scribble2, blocks, right, faint, head.
- `pilot_progress(t)` -> progress for `part="all"` from seconds since the scene began, on the board's schedule
  (`Wd.PILOT_TIMES`: box 0.6..1.8, dome ..2.5, window ..2.8, scribble 2.8..3.3, its double 3.3..3.8, blocks 3.9..4.8,
  right ..5.6, faint ..6.4, head 6.4..8.6; `Wd.PILOT_END = 8.6`).
- `pilot_tip(cx, cy, progress, scale=1.6, part="all")` -> `(x, y, down)`: the pencil point; `down` False between strokes.
- `pencil(target, x, y, angle=-52.0, lift=0.0, scale=1.0)`: a yellow pencil (258 long), point at (x, y), lying up and to
  the right; `lift` raises it.
- `Wd.PILOT_STROKES`: the raw list (dicts `pts` in sheet units, `weight`, `sharp`, `part`).
```python
P = Wd.pilot_progress(t)                                    # t = seconds from the scene's start
Wd.desk(ink, (40, -60, 930, 620)); Wd.sheet_ring(ink, 400, 440, 1.6)
Wd.pilot_drawing(ink, 400, 440, P, 1.6)
x, y, down = Wd.pilot_tip(400, 440, P, 1.6)
if 0.3 < t < 8.9: Wd.pencil(ink, x, y, lift=0 if down else 14)
Wd.badge(ink)
```
- `pencil_path(target, pts, weight=0.6, closed=False, seed=0, alpha=1.0, wobble=1.0, color=None)`: any pencil line through
  screen points (the outline a thing arrives as). `color=None` graphite, `Wd.CHALK` over dark, `Wd.DARK` on brass.
- `pencil_line(target, xy, text, size=30, progress=1.0, width=None, seed=0, color=None)`: words in pencil handwriting
  (not needed by the board: the children's words are captions).

## Pick cards and the friends' marks
`pick_card(target, kind, pick, initial, x=160, y=350, size=(640, 150), paint=1.0, drawn=0.0, pressed=0.0, lit=0.0, color=None, who=None, outline_color=Wd.CHALK)`
-> `{"button", "mark", "mark_kind", "mark_scale", "box"}`
- A paper card, top-left at (x, y): the controller button on the left, the option in type, the worksheet's dashed
  "draw the one you pick" ring on the right, the initial small in the corner.
- `paint=0.0`: only its outline in white pencil (card edge, button, ring). `paint=1.0`: the painted card, registering
  exactly on the outline. Drive it with `arrive`.
- `drawn` 0..1: the friend's own pencil mark. kind "triangle" -> B.'s triangle in the dashed ring (left side, right side,
  base, not meeting at the top). Any other kind -> W.'s long wobbly loop round the lettering and the button (W. drew
  nothing in the ring). `pressed` pushes the button in, `lit` lights it.
```python
s = Wd.arrive(t, 20.3)
if s:
    c = Wd.pick_card(ink, "triangle", "Pond mirror", "B.", 160, 356, paint=0.0 if s == 1 else 1.0,
                     drawn=Wd.ramp(t, 21.0, 22.0), pressed=Wd.ease(t, 22.2, 22.4), lit=Wd.ease(t, 22.2, 22.5))
    if 20.9 < t < 22.1:
        x, y, down = Wd.friend_tip(c["mark_kind"], c["mark"][0], c["mark"][1], Wd.ramp(t, 21.0, 22.0), c["mark_scale"])
        Wd.pencil(ink, x, y, lift=0 if down else 12)
# next friend: Wd.pick_card(ink, "cross", "Two-headed tin monster", "W.", 160, 356, ...)
```
- `friend_mark(target, kind, cx, cy, progress=1.0, scale=1.6)`: just the mark: "triangle" (37 x 40 px times scale) or
  "loop" (430 x 94). `friend_tip(kind, cx, cy, progress, scale)` -> `(x, y, down)`.
- `swing_card(target, img, pin, angle=0.0, at=None, pinned=True, shadow=0.42)`, `brad(target, x, y, r=7)`: a card turned
  about one brass pin (c10's; available, not asked for by this board).

## Buttons, dice, cup, badge
- `button(target, kind, x, y, r=40, pressed=0.0, lit=0.0, outline=False, alpha=1.0, color=None)`: a domed controller
  button: triangle (green), circle (red), cross (blue), square (pink), hexagon (amber). `outline=True` = its pencil
  outline only, same place and size.
- `controller(target, x, y, scale=1.0, pressed=None, press=1.0, lit=1.0)` -> `{kind: (x, y)}`: all five on a riveted
  plate 330 x 84 centred at (x, y).
- `die(target, n, x, y, size=44, angle=0.0, shadow=True, outline=False, alpha=1.0, color=None)`: ivory die face n centred
  at (x, y). `outline=True` = pencil outline only (before its double lands; an unwritten bolt at the end).
- `die_at_bolt(target, n, port=None, r=None, size=40, lit=True, outline=False, t=0.0, ring_w=None)` -> `(x, y)`: die face n on
  bolt n of a porthole ring. Defaults = the seat's porthole. From the river: `Wd.die_at_bolt(ink, 5, p["port"], p["port_r"], size=24, ring_w=17 * scale)`.
  `lit` = amber glow (a written ending); `outline=True` = dark pencil outline on the brass (unwritten).
- The ending's six bolts, 3 and 5 lit, on a face-on ring:
```python
Wd.table(ink); ring = Wd.brass_ring(150, 196, fittings=True)
Wd._comp(ink, Wd.shadow_of(ring.getchannel("A"), 9, 0.6), (380 - ring.width / 2 + 7, 262 - ring.height / 2 + 11))
ImageDraw.Draw(ink.img).ellipse([228, 110, 532, 414], fill=(14, 30, 30))            # the glass, dark and still
Wd._comp(ink, ring, (380 - ring.width / 2, 262 - ring.height / 2))
for n in range(1, 7):
    if t >= 44.4 + 0.5 * (n - 1):
        Wd.die_at_bolt(ink, n, (380, 262), 150, size=38, lit=n in (3, 5), outline=n not in (3, 5), ring_w=46)
Wd.die_cup_side(ink, 790, 470)
```
- `die_cup_side(target, x, y, scale=1.0)`: THE DIE IS STILL IN THE CUP: a leather cup standing upright, the die resting in
  its mouth with a corner up, edge-on, no face presented. (x, y) = centre of the cup's base; 150 * scale wide, the
  die's corner 224 * scale above the base. It does not move and has no double.
- `die_cup(target, x, y, r=62, n=5, t=0.0, rattle=0.0)`: the cup from above with a face showing (c10's; the board wants
  no face shown, so prefer `die_cup_side`).
- `bolt_tag(target, n, x=18, y=14, label=False)`: die face n for the top LEFT corner (label=True adds a lettered tag: don't).
- `badge(target, n=16, x=None, y=14)`: the porthole number, white on a dark rounded badge, top RIGHT (x 866..946,
  y 14..64). Call it last, every frame.

## Lower-level kit (if you need a piece of your own)
`cut(pts, color, deco=None, curve=True, seed=0)` -> Sprite cut from paper along design-coordinate points; `compose([...])`
glues pieces; `draw_sprite(target, spr, M, shadow=(dx, dy, blur, strength))` lays one under an affine built from
`Tm(x, y) @ Rm(deg) @ Sm(sx, sy)`; `Puppet()` with `.add(name, spr, pivot, parent, z)` and `.draw(target, pose, M)` is the
joint tree; `apply(M, p)`; `shadow_of(alpha, blur, strength)`; `rrect`, `circ`, `catmull`, `xf`; `feather(target, x, y,
scale, angle)` one loose turkey feather; `plank(target, x0, y, x1)`. Re-exported: `W, H, FPS, clamp, ramp, smooth, ease,
lerp, font`, and `Wd.KA` = kit_anim.

## Known limits (for the scene units and the critic)
- The twin tin is drawn by mirroring the whole tin, so its brass is lit from the other side: true to a mirror image.
- Turkey's rear and front drawings share the wing cut but not a 3D shape: cut between them on the shoulder pin, never tween.
- Seen through the seat's glass the three heads are smaller than the tin's length so that all three can be counted;
  raise `SEAT_HEAD_SCALE` (and move `SEAT_HEADS`) if you want them to crowd the glass.
- Pencil outlines are graphite by default and vanish on dark grounds: pass `color=Wd.CHALK` (or `Wd.DARK` on brass).

## Test
`python3 films/swarm/c16/world.py <out_dir> [table seat river ending parts]` writes contact sheets `table.png`, `seat.png`,
`river.png`, `ending.png`, `parts.png` (and a few full frames) exercising every function, and asserts the rule's invariant.
