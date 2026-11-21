# TOWN.md · Trouttown (`films/swarm/dogs/town.py`)

The town under the creek, in planes. You should not need to read the source.

Look before you use it. `python3 films/swarm/dogs/town.py` runs the self-test and writes:
`town_wide.png` (F-TOWN, everything), `town_school.png`, `town_board.png` (3.6x), `town_class.png` (bubbles),
`town_split_ice.png` (F-SPLIT under the ice, cold), `town_last.png` (F-LAST, children swum up to look at the door),
`town_lamps_coming_on.png` (lamps half on, all 374 holes), `town_pictures.png` (the five drawings, large).

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import town, dog

def frame(t, ink):                                   # kit.py Film picture function
    cam = town.F_TOWN
    town.back(ink, t, cam)                           # water, far town, back row, the surface and the lit door above it
    town.street(ink, t, cam, holes=3)                # gravel, diner, lamps, school, bell, notice board, holes
    kids = town.school_class(ink, t, cam, speak={0: ("jaw", 1.0)})     # the class; child 0 blows the jaw bubble
    x, y = cam.xy(410, 806)                          # world -> screen for YOUR cast
    dog.draw_dog(ink, dog.dig(t), x, y, scale=0.6 * cam.zoom, tint=(24, 120, 128), tint_amount=0.3, shadow=False)
    town.front(ink, t, cam)                          # near weed, motes
```

Draw order is always `back` → `street` → cast (yours and the fish) → `front` → `grade` (only if cold or night).
About 140 ms a frame at F-TOWN with the whole class; the first frame takes about 3 s (planes are cut once).

## What it is made of

| Piece | Made of |
|---|---|
| Water, hazed boulders, gravel bed, swaying weed | Foraged through `films/swarm/c13/world.py` (imported, not edited): its river planes, regraded to dusk teal |
| The peoplefish | Denton's 1896 brook trout (public domain, c13's cutout), stood on its tail; eye, fin-arm, satchels, hats, shawl are cut paper made here |
| Buildings, lamps, sign, fence, board, desks, slate, bell, holes, bubbles, pages, the surface, ice | Handmade in code |
| The drawings in bubbles and on pages | Redrawn from the pencil strokes other films traced by eye from the class sheets: `jaw` (c10), `fish_bell` (c13, its lettered bubble left out), `sub` (c16), `bowl_legs` (c25), `bars` (c33). No photograph is loaded. |

No lettering anywhere: the welcome sign is a painted fish jumping over a wave with a shell on top; the diner's sign
is a real spoon and fork; pages are drawings and scribble lines; the slate is a chalk picture.

## World and camera

World coordinates are the board's: x 0..960, y down, **surface y = 400, gravel y = 800**.

```python
town.Cam(oy=360, ox=0, zoom=1)     # screen = world shifted up by oy (the board's "offset"), sideways by ox, zoomed about frame centre
town.F_PORCH, town.F_SPLIT, town.F_TOWN, town.F_LAST          # Cam(0), Cam(250), Cam(360), Cam(150)
town.Cam.look(wx, wy, zoom)        # a camera centred on a world point:  town.Cam.look(425, 742, 3.6) is the board close-up
camA.mix(camB, f)                  # in-between camera (a crane, a push); ease f yourself: F_PORCH.mix(F_TOWN, ease(t, 22.0, 24.3))
cam.xy(wx, wy, depth=1.0)          # world -> screen. USE THIS to place dogs. Scale a dog by cam.zoom.
cam.world(sx, sy)                  # screen -> world
cam.surface()                      # screen y of the bright line
```
Every function below takes `cam` as a `Cam`, a number (the offset) or `None` (F-TOWN).

Planes and their depths (parallax; a 100 px pan moves them 30, 45, 72, 100, 130 px): water 0.3 · far town
(c13 boulders, hazed bottles and jars with pin lights) 0.45 · back row (tin stack, boot house, bottle tower, teapot
house, lantern jar) 0.72 · main street and all cast 1.0 · near weed and half the motes 1.3. Far planes also zoom
less. A veil of water colour lies between each pair. Nothing under water is ever drawn above the line.

Places (world): `SURFACE_Y 400`, `BED_Y 800`, `BOARD (380, 690, 470, 780)`, `SCHOOL (600, 600, 900, 800)`,
`YARD (520, 900)` fence with the gate gap at x 548..572, `MAKING (480, 770, 600, 800)`, `DINER (70, 700, 258, 802)`,
`SIGN_XY (30, 728)`, `BELL_HANG (750, 611)`, `SLATE_XY (798, 806)`, `TEACHER_XY (840, 812)`,
`LAMPS` = heads at (64, 275, 355, 490, 565, 930; y 728), `SEATS` = eight (x, y): front row (612, 652, 692, 732; 832),
back row (634, 674, 714, 754; 809), `HOLES` = 374 × (x, y, width, side).

## The set

| Function | What it draws | Example |
|---|---|---|
| `back(ink, t, cam, lamps=1.0, school=None, sky=True, door=1.0, ice=0.0, cracks=(), shatter=0.0, calm=False, night=0.0)` | Water, far town, back row, the door's amber light slanting down from the upper left, then `surface()`. `sky=True` paints what is above the line as seen from below (violet dusk, the lit door and lamp as a wobbling amber smear at upper left): use it in F-TOWN. **`sky=False` wherever a porch is drawn above the line** (F-SPLIT, F-LAST, cranes): draw your porch first, then call this; it only touches pixels from the line down. | `town.back(ink, t, town.F_TOWN, lamps=ramp(t, 24.5, 27.0))` |
| `street(ink, t, cam, lamps=1.0, school=None, bell=0.0, board=True, taken=(), smudges=0, holes=0, pull=None, calm=False, smoke=True)` | Gravel, welcome sign, diner (bubbles from its thimble chimney), six lamps, school, yard fence, the bell, the notice board, the holes. Returns `{'lamps': [screen heads], 'board': {'pages': {k: xy}, 'foot': xy}}`. | `town.street(ink, t, cam, bell=26 * math.sin(6 * (t - 28.5)) * math.exp(-(t - 28.5)), holes=2.4, smudges=1)` |
| `front(ink, t, cam, calm=False, weeds=True, motes=True)` | Near weed at the lower corners, drifting specks at two depths. Last. | `town.front(ink, t, cam)` |
| `grade(ink, cam, cold=0.0, night=0.0)` | A wash over everything under the line, cast included. `cold` 0..1: the warmth goes out (ice). `night` 0..1: darker and more violet, lamp-warm pixels stay bright (beat 5.4). Call after `front`. | `town.grade(ink, cam, cold=ease(t, 116.8, 118.0))` |
| `draw(ink, t, cam, cast=True, **kw)` | All of it in one call (back, street, class, townsfolk, front) for an empty establishing shot. | `town.draw(ink, t, town.F_TOWN, holes=8)` |
| `light_levels(lamps, school)` | What `lamps=` means. A number 0..1 brings the lights on **left to right** (lamp, diner, lamp, lamp, lamp, lamp, last lamp; school windows last); or a dict over `LIGHT_NAMES = (lamp0, diner, lamp1, lamp2, lamp3, lamp4, school, lamp5)`; or a list of six lamp levels. `school=` overrides the school windows. One lit window always has a small fish in it. | `town.back(ink, t, cam, lamps={"lamp2": 1, "lamp3": 1}, school=0)` |
| `surface(ink, t, cam, sky=True, door=1.0, ice=0.0, cracks=(), shatter=0.0, calm=False, night=0.0, glow=1.0)` | The line by itself (already called by `back`). `door` 0..1 dims the amber. `ice` 0..1 runs a white skin along the line from left to right. `cracks=[(world_x, 0..1)]` a star and a jagged crack growing both ways from a stamp. `shatter` 0..1 tips the floes, drops and clears them. `calm=True` stops the wobble dead. Returns the line's screen y. | `town.back(ink, t, cam, sky=False, ice=1, cracks=[(600, ramp(t, 122.0, 122.3)), (600, ramp(t, 122.6, 123.4))], shatter=ease(t, 123.4, 125.0), calm=t < 123.4)` |
| `touch(ink, t, cam, x, kind='muzzle', dip=1.0, calm=False)` | A land animal seen from below: only what breaks the line, with rings leaving along it. `kind` `'muzzle'` (cow's nose and lips) · `'hoof'` (one leg to the fetlock) · `'chin'`. Draw after `back`. A stand-in: if a kennel has a real cow-from-below, use that. | `town.touch(ink, t, cam, 600, "muzzle")` |
| `school_bell(ink, cam, swing=0.0)` | The bell alone (called by `street`). Verdigris, not brass: the cow's bell is the only brass. | `town.school_bell(ink, cam, 20)` |

Under the ice use `calm=True` on `back`, `street`, `front`, `school_class`, `townsfolk`, `fish`, `bubble` and build your
`Ink` with `boil=0`: then nothing in the town moves at all.

## Digging

| Function | What | Example |
|---|---|---|
| `dig_holes(ink, cam, count)` | The holes so far (also `street(holes=)`). `count` may be a fraction: 2.4 = two holes and the third 40% dug, its spoil heap growing. **Holes never fill in: never pass a smaller count than before.** Up to 374, the real number of digs. | `town.dig_holes(ink, cam, 2 + ramp(t, 35.0, 36.2))` |
| `hole_xy(k)` | World (x, y) of hole k, so the dog can stand over it before it exists. Holes 0, 1, 2 are at (318, 816), (362, 826), (410, 815): the board's first three digs. 3..39 cluster round the work; the rest cover the whole bed (none under the desks, the board's legs or the making place). | `x, y = cam.xy(*town.hole_xy(1))` |
| `thing(ink, cam, kind, x, y, angle=0, scale=1, screen=False)` | What the digging turns up, lying on the gravel: `'boot'`, `'spool'` (left at the foot of the board at 39.0, used at 137.0), `'pin'`. | `town.thing(ink, cam, "spool", 392, 806)` |
| `making_place(ink, cam, progress)` | What the digger builds at x 480..600: six flat stones set one by one, then two planks. 0..1. Returns its top (screen). | `town.making_place(ink, cam, ramp(t, 101, 110))` |

## The notice board and pages

| Function | What | Example |
|---|---|---|
| `notice_board(ink, t, cam, taken=(), smudges=0, pull=None, calm=False)` | A cigar-box lid on two twigs with a reed roof; six pinned pages swaying in the current: 0 jaw, 1 fish and bell, 2 boxy sub, 3 fish in a bowl with legs, 4 scribble, 5 bars. `taken` = pages gone (a paler patch and a pin hole stay). `smudges` 0..131 wet nose marks so far (they never dry). `pull=(k, 0..1)` page k coming off by a corner, its pin gone after 0.5. Also via `street(...)`. | `town.street(ink, t, cam, smudges=1, pull=(0, ramp(t, 51.3, 52.5)), taken=(0,) if t > 52.5 else ())` |
| `board_page_xy(k)` | World middle of page k. | `nose_target = cam.xy(*town.board_page_xy(0))` |
| `page(ink, cam, x, y, drawing='jaw', angle=0, size=26, sag=0, alpha=1, wet=0, smudge=0, screen=False, progress=1)` | One loose page anywhere (in a mouth, in a child's fin, on the sill). `size` = height in world px; `sag` 0..1 droops the far corner; `wet` 0..1 greys it. `screen=True` takes screen px (for the porch). | `town.page(ink, cam, j["mouth"][0], j["mouth"][1], "jaw", angle=8, size=30, sag=0.6, wet=1, screen=True)` |

## The drawings and the bubbles

| Function | What | Example |
|---|---|---|
| `picture(target, name, cx, cy, size, progress=1, color=(52,54,66), width=None, alpha=1, tidy=False, seed=0)` | One child's drawing as pencil strokes in a `size` px square at screen (cx, cy). `name`: `'jaw'` (zigzag teeth in a slanted box, the second jaw below it), `'fish_bell'`, `'sub'`, `'bowl_legs'`, `'bars'`; also `'jaw_only'`, `'scribble'`, `'scribble2'`. `progress` draws it stroke by stroke in the child's order. **`tidy=True` is the wrong version for the reel the person refuses: every stroke ruled straight, the second jaw gone.** `target` = Ink, ImageDraw or image. | `town.picture(ink, "jaw", 110, 280, 150, tidy=True, color=(60, 40, 20))` |
| `bubble(ink, t, cam, mouth, drawing='jaw', grow=1, progress=1, r=30, side=1, pop=0, rise=0, seed=0, calm=False, screen=False, alpha=1, tidy=False)` | A fish speaking: a bubble with a picture in it, never a word. `mouth` = world point, or a screen point with `screen=True` (`fish()['mouth']` is a screen point). `grow` blows it up from the mouth; `progress` draws the picture inside; `rise` world px floated up; `pop` 0..1 bursts it into drops. `r` world px. Returns its screen centre. | `town.bubble(ink, t, cam, kid["mouth"], "jaw", grow=ramp(t, 45.5, 47.0), pop=ramp(t, 52.5, 52.9), screen=True)` |

`town.DRAWINGS` is the five names; `town.CHILD_DRAWS[k]` is child k's own drawing (0 jaw, 1 fish_bell, 2 sub,
3 bowl_legs, 4 bars, 5 fish_bell, 6 jaw, 7 bars). The board's three: jaw (S2, S6), fish_bell (S4), bars (last shot).

## The peoplefish

```python
fish(ink, t, cam, x, y, kind='child', facing=1, tilt=0, arm=20, look=None, hold=None, seed=0, length=None,
     satchel=True, lid=0, swim=1, depth=1, alpha=1, calm=False, screen=False, mouth_open=0)
    -> {'mouth', 'eye', 'head', 'hand', 'centre', 'foot': screen points, 'length': screen px}
```
A trout standing on its tail. `(x, y)` is the world point the tail stands on (it turns about that point).
- `kind`: `'child'` (54 px; satchel; `seed` picks colour, size, cap or bow; **seed 0 is the jaw child, smallest, blue satchel**),
  `'teacher'` (98; spectacles, bun, lilac shawl), `'cook'` (white hat, apron), `'post'` (cap, bag), `'lady'` (hat with a
  weed feather), `'towns'` (hat, scarf).
- `facing` +1 right, -1 left. `tilt` degrees: 0 upright, 8 sitting forward, 38 swimming up and forward, 90 swimming
  flat, negative leaning back. `arm` degrees: 0 fin at its side, 90 pointing forward, 150 up; animate it to wave:
  `arm=120 + 30 * math.sin(t * 9)`.
- `look` = a WORLD point the eye looks at. `lid` 0..1 closes the eye. `mouth_open` 0..1.
- `hold`: `'pointer'`, `'chalk'`, `'page:jaw'` (any drawing name: the child holds its page out).
- `swim` 0..1 how hard the tail works. `depth` < 1 sends it back into the haze. `calm=True` freezes it.

| Function | What | Example |
|---|---|---|
| `child(ink, t, cam, k, x=None, y=None, **pose)` | Fish child k (0..7) anywhere; at its seat if x, y are left out. | `r = town.child(ink, t, cam, 0, 560, 760, facing=-1, tilt=30, arm=120 + 30 * math.sin(t * 9), look=(600, 400))` |
| `school_class(ink, t, cam, facing=1, look=None, tilt=8, speak=None, arm=None, skip=(), calm=False, teacher=True, slate_drawing='fish_bell', slate_progress=1, desks=True, lid=None)` | Slate, eight children at desks in two rows, teacher with pointer. Every keyword is one value for all or a dict `{child index: value}` (`'T'` = teacher). `speak={k: (drawing, grow[, progress[, pop]])}` blows bubbles. `skip` = children away from their desks (their desks stay; draw them with `child`). Default look: the slate. Returns `{k: fish points}`. | `town.school_class(ink, t, cam, look=(dog_wx, dog_wy), speak={0: ("jaw", ramp(t, 45.5, 47))}, arm={0: 120}, skip=(3,))` |
| `desk(ink, cam, x, y, seed=0)` | A matchbox tray on two dress pins, 32 × 25. Draw after the child behind it. | `town.desk(ink, cam, 624, 834, 0)` |
| `slate(ink, cam, drawing='fish_bell', progress=1, x=None, y=None)` | The teacher's slate on an easel of matches, a chalk picture on it. | `town.slate(ink, cam, "bars", ramp(t, 30, 33))` |
| `townsfolk(ink, t, cam, look=None, calm=False, who=None, wave=None)` | Cook in the diner's door, lady by the diner, postfish walking its round between the lamps, somebody in a hat by the last lamp. `look` = world point they all turn to. `who` = indices to draw. `wave={i: arm degrees}`. | `town.townsfolk(ink, t, cam, look=(dog_wx, dog_wy))` |

The last shot (F-LAST shows world y 150..690, so the yard is out of frame): swim the children up and turn them to
the door, as `town_last.png` does:
```python
door = (105, 300)
for k, (x, y) in enumerate(((330, 600), (392, 652), (452, 590), (520, 640), (585, 588), (650, 646), (712, 600), (790, 640))):
    r = town.child(ink, t, cam, k, x, y + 4 * math.sin(t * 1.3 + k), facing=-1, tilt=38, look=door, swim=0.5)
```

## Where this differs from the board (keep the module's numbers, as the board allows)

- Lamp heads are at y = 728, not 760 (a lamp shorter than a fish child read wrong); their light pools lie at y 780..820.
- The class sits at desks in the yard in front of the school (x 612..754), the slate at x 798, the teacher at x 840.
  The yard fence runs x 520..600 with the gate at 548..572, so "the yard gate" is left of the desks.
- The second jaw sits below the first inside the bubble, not beside it, so both fit a round bubble.
- `touch()` is a plain stand-in for cow parts seen from below.

## Checks

MEASURED by `_selftest()` (run with the stills): nearer planes move more for the same pan (30 < 45 < 72 < 100 < 130);
`xy`/`world` round-trip; the four framings put the surface at 400, 150, 40, 250; 374 holes, all in the gravel, none
under the desks, the first three at x 300..440; every drawing fits its unit box.
JUDGED by the builder from the eight stills and a six-frame sheet with the lead dog in it (crossing down, digging,
nosing a page at 2.6x): the town reads as a place with a street; the class reads as a class; the five drawings are
told apart at bubble size in the 2.5x shot. At F-TOWN a child is 54 px and a bubble 60 px: the drawing in it is
legible as "teeth" only in closer shots, so play beat 2.4 in the medium as the board says.
UNKNOWN: anything in motion. Only stills were looked at; no playback, no sound, no independent critic yet.
Weak spots: a fish's hat sits on its nose (it stands nose up); the engraved mouth cannot move (`mouth_open` adds a
small dark O); the back row softens above 3x; under 374 holes the gravel is nearly all pits.
