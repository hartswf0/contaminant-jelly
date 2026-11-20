# c13 · WORLD · the shared pieces (porthole 13 · Arch · the twig-bell)

World unit. Everything is in `films/swarm/c13/world.py`. You should not need to read its source.

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))          # films/swarm/c13
import world as w
from kit import Ink, W, H, FPS, clamp, ramp, ease, smooth, lerp, lerp2      # world.py puts films/ on sys.path
```

- Frame is 960x540. All coordinates are screen pixels, y down, unless a line says "ring units".
- Every `draw` function takes the kit's `ink` first and draws straight onto it, in call order (later calls are in front).
- **Angles.** `angle=` on a cutout is degrees **counter-clockwise** on screen (PIL's sense). "Clock angles"
  (`clock_xy`, `trout_on_circle`, `brass_arm`, bolts) are degrees **clockwise from twelve o'clock**. Bell, clapper,
  cord and weed lean are degrees from plumb, **positive = to the right**.
- Nothing here boils or shimmers by itself except what takes `t`. Pass `t` = your scene time.
- Cost: a full seat shot is about 30 ms a frame. Sprites are cached; first use of a piece takes a second or two.
- Look at the test stills: `python3 films/swarm/c13/world.py` writes `films/stills/c13_world/01..12_*.png`
  (the functions `_demo_*` at the bottom of world.py are worked examples of whole shots).

## What is foraged, what is handmade

| Piece | Made of |
|---|---|
| Turkey | Foraged: Audubon, *The Birds of America* plate 1 (Commons, public domain), cut into head-and-neck, lower beak, wattle, body, wing, and hinged. The white staring eye and the raised neck feathers are cut paper added here. |
| Trout | Foraged: Denton's 1896 brook trout plate (Commons, public domain), cut out, flexed; cut-paper eyelid. |
| Everything else | Handmade in code: tin, brass ring, arch boulders and moss (torn paper), twig, bell, clapper, cord, weed, river planes, the pencil drawing, pencil, buttons, dice, die cup, gauge, pick card, brass arm, badge. |

Credits are in `films/credits/c13.json`; the two source files are in `films/sources/c13/`.
**There is no hand.** Pieces are laid by sliding them in with their shadow (`put(..., shadow=)`, `lift=`) or
nudged with the pencil's eraser end. Do not draw a hand.

## Standard places (use these so the shots join)

```python
w.PORT_C = (480, 262)      # centre of the round glass in every porthole shot AND of the pencil ring on the table
w.PORT_R = 212             # glass radius = inner radius of the printed ring
w.RING_OUT = 262           # outer radius of the brass ring / printed ring (it touches the top of the frame)
w.STAGE = dict(arch_c=(480, 478), arch_w=500, bell_hang=(480, 150), bell_scale=1.0,
               twelve=(480, 118), nine=(318, 262),            # the turn place under the bell, the waiting place
               fish1=(432, 236), fish2=(566, 318),            # the two leads, placed as in the pilot's drawing
               reflection=(368, 386), gauge=(820, 440))       # Turkey's reflection low left; gauge low right in the seat
w.RIVER = dict(tin_c=(430, 404), tin_scale=0.82, arch_c=(560, 470), arch_w=560, bell_hang=(560, 104), bell_scale=1.1)
```

With the bell at rest at `STAGE['bell_hang']`: mouth (480, 251), clapper ball (480, 257), knot (480, 336).
Bolts (centres on the brass ring at PORT_C): 1 (480, 22) · 2 (687, 142) · 3 (687, 382) · 4 (480, 502) · 5 (273, 382) · 6 (273, 142).

## Palette

`w.PAL` is a dict of RGB tuples: `table, table_dk, sheet, sheet_edge, print, pencil, pencil_soft, water_top,
water_mid, water_deep, shaft, stone, stone_dk, stone_lt, moss, moss_dk, moss_lt, weed, weed_dk, weed_lt, twig,
twig_dk, twig_lt, brass, brass_hi, brass_dk, brass_line, tin, tin_dk, wall, lamp, amber, cord, cord_dk, green, red,
blue, pink, hexamber, ivory, pip, leather, leather_dk, badge, white, unlit`.
`w.BUTTONS = {'triangle': green, 'circle': red, 'cross': blue, 'square': pink, 'hexagon': amber}`.

## Helpers

| Function | What it does |
|---|---|
| `put(ink, spr, cx, cy, angle=0, scale=1, flip=False, alpha=1, shadow=0, shadow_off=(5,7), shadow_blur=5)` | Lay any RGBA cutout with its centre at (cx, cy). `shadow` 0..1 puts a soft contact shadow under it; grow `shadow_off` to lift a piece off the table. |
| `offscreen(ink)` | A second full-frame `Ink` for the same frame. Draw the next scene on it, pass `.img` to `sweep`. |
| `Follower(target_fn, seconds, f=1.6, zeta=0.25, x0=None)` then `.at(t)` | Spring-damper follower for secondary dynamics. Build once at module level: `clap = w.Follower(lambda t: bell_angle(t), SECONDS, f=2.2, zeta=0.18)`; per frame `clap.at(t)`. zeta 0.15 rings on, 1.0 settles dead (bolt 3). |
| `clock_xy(c, r, clock_deg)` | Point on a circle, 0 = twelve o'clock, clockwise. |
| `ring_xy(u, v, c=PORT_C, r=PORT_R)` | Ring units (the drawing's own coordinates: centre 0,0, inner radius 1) to screen. |
| `bolt_xy(n, c=PORT_C, r=None)` | Centre of bolt n (1 at twelve, then clockwise: 2 at two, 3 at four, 4 at six, 5 at eight, 6 at ten). |
| `vnoise, catmull` | value noise (h, w) and a smooth curve through points, if you need them. |

## Turkey

Moods: `w.TURKEY_MOODS = ('calm', 'wave', 'panic', 'freak', 'gasp', 'flap', 'frozen')`.

| Mood | What moves |
|---|---|
| `calm` | slow nod, wattle sways, beak shut, plain engraved eye, wings folded |
| `wave` | one wing up and waving, beak a little open |
| `panic` | white eye, beak chattering, wattle swinging, wings half up, neck feathers half raised, small shake |
| `freak` | white ringed eye, beak hinged wide, wattle thrown side to side, neck feathers up, both wings beating, whole bird shaking. **The board's default: he is in this in every beat.** |
| `gasp` | neck stretched back, beak at its widest, wings held up, a held breath (pair it with `bubbles`) |
| `flap` | as freak, wings so fast they leave ghost copies (a blur of wings) |
| `frozen` | rigid: wings shut, beak part open, white eye, neck feathers up, a fast small tremble. Still freaking. |

There is no way to make the freak moods look calm: that is the point of bolt 3.

```python
turkey(ink, cx, cy, height=300, mood='calm', t=0.0, part='bust', flip=False, alpha=1.0, shadow=0.0, angle=0.0, **over)
```
- Faces **left**; `flip=True` faces right. (cx, cy) is his anchor: `part='bust'` (head, neck, shoulders, cut off the
  plate under the shoulders; wings appear at the sides when raised) anchor = middle of head-and-neck, `height` =
  crest to the cut; `part='head'` (head, neck, wattle only) anchor = the head, `height` = crest to wattle;
  `part='full'` (the whole bird, tail and all) anchor = body centre, `height` = crest to tail tip.
- `**over` overrides any pose key for this frame: `neck` (deg), `wattle` (deg, drive it from a `Follower`), `beak`
  (deg open, 0..31), `eye` (0 engraved, 1 white and staring), `wing` (deg raised, 0..100; under 4 = folded),
  `ruff` (0..1 neck feathers up), `shake` (px), `blur` (1 = ghost wings).
- Example: `w.turkey(ink, 480, 300, 260, 'freak', t, 'bust', shadow=0.6)`; a slow wattle: `w.turkey(ink, 200, 300, 200, 'gasp', t, wattle=wat.at(t))`.

```python
turkey_sprite(mood='calm', t=0.0, height=300, part='bust', **over) -> (RGBA image, (ax, ay))    # anchor inside the image
turkey_pose(mood, t) -> dict of the pose keys
turkey_reflection(ink, cx=None, cy=None, height=250, mood='freak', t=0.0, alpha=0.6, clip=(PORT_C, PORT_R), part='bust', **over)
```
`turkey_reflection` is Turkey's reflection lying on the inside of the glass from his seat: faces right, lamp-pale,
see-through, thinning downward, clipped to the glass. Default place `STAGE['reflection']` (low left). Call it after
the river scene and **before** `seat_frame`. Example: `w.turkey_reflection(ink, mood='frozen', t=t)`.
To hang the bell over him like a dish cover, put the bell's `hang` about 235 px above the reflection's (cx, cy), or
move the reflection under the bell: `w.turkey_reflection(ink, 480, 400, 230, 'freak', t)`.

## Trout

```python
trout(ink, cx, cy, length=220, angle=0.0, flip=False, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False, alpha=1.0, shadow=0.0)
trout_sprite(length=220, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False) -> RGBA facing left
trout_on_circle(ink, c, r, clock_deg, length=150, **same keywords as trout except angle and flip) -> (x, y)
```
- Faces **left**; `flip=True` faces right. `angle` counter-clockwise (positive tips the nose DOWN when facing left;
  the drawing's lower fish is `angle=20`).
- `phase` (radians) swims the tail: `phase=t*6` cruising, `t*14` crazy; `amp` is the bend in px at length 420
  (`amp=0` is a rigid, perfectly still fish).
- `lid` 0..1 lowers a flat cut-paper eyelid: **0.45 is the unamused, fed-up look the pilot's frame asks for**
  (use it whenever a trout looks at the tin); 0.8 is dozing calm (bolt 3). The engraved mouth cannot be changed:
  the lid carries the mood.
- `eye_roll` = degrees (0 up, clockwise): a white eye with the pupil rolled there (animate `eye_roll=t*500` for
  crazy). `belly_up=True` turns the fish over.
- `trout_on_circle` puts a trout on the clockwise circuit round `c` at clock angle `clock_deg`, heading along the
  clockwise tangent and the right way up for its direction. **Only ever increase `clock_deg`.**
  Example (the wheel of bolt 2): `for k in range(7): w.trout_on_circle(ink, w.PORT_C, 168, k*360/7 + lap(t), 118, phase=t*14+k, amp=12, belly_up=k in (2, 5))`.
- On the table give it `shadow=0.8`; in the water `shadow=0`.

## The pilot's page (table)

```python
table(ink, sheet=True)                       # wooden boards + the worksheet paper under the ring. Fills the frame.
sheet_ring(ink, c=PORT_C, r=PORT_R, alpha=1.0, lit=None)      # the printed double circle with six little die faces (lit={n: 0..1} greys some)
pilot_page(ink, t, c=PORT_C, r=PORT_R, alpha=1.0) -> (tip_xy, pen_down)     # the drawing t seconds in, on the board's A1-A6 timing
pilot_drawing(ink, done=1.0, c=PORT_C, r=PORT_R, alpha=1.0, color=None) -> (tip_xy, pen_down)
pencil(ink, tip, angle=52.0, lift=0.0, length=250, alpha=1.0)   # a cut-card pencil with shadow; point at `tip`
```
- `pilot_page` is the one call for A1 to A6. It draws exactly as much as has been drawn by time `t` and returns
  where the pencil point is and whether it is on the paper:
  ```python
  w.table(ink); w.sheet_ring(ink)
  tip, down = w.pilot_page(ink, t)
  w.pencil(ink, tip, lift=0 if down else 1)
  ```
  `w.PILOT_TIMES = {'fish1': (0.15, 2.2), 'bubble': (2.3, 4.0), 'bell': (4.1, 5.4), 'weed_r': (5.5, 6.2), 'fish2': (6.3, 8.0), 'weed_l': (8.1, 8.75)}`.
  Between groups the pencil travels lifted to the next start. After 8.75 s the drawing is whole; move the pencil
  out of frame yourself (clockwise) and stop calling `pencil`.
- `pilot_drawing(done=...)` for your own timing: `done` is 0..1 of the whole drawing by pencil travel, or a dict
  `{group: 0..1}` with groups `w.PILOT_GROUPS = ['fish1', 'bubble', 'bell', 'weed_r', 'fish2', 'weed_l']` (clockwise
  order). `alpha=0.45` gives the faint drawing of the ending.
- The drawing is traced by eye from the child's sheet as pencil strokes (`w.PILOT_STROKES`: list of
  `{group, pts, weight, len}`, pts in ring units): upper fish facing left with ringed eye, smile and hatched
  triangle tail; the lumpy bubble lettered "haha / verry / funny" stroke by stroke; the tiny bell and its wavy twig
  to the rim; the spring of weed at the right rim; the slimmer nose-down lower fish with fan tail and back shading;
  the scalloped weed with one thin stem. It keeps a fixed hand-wobble and does not shimmer.
- `w.PILOT_PLACES` (ring units; use `ring_xy`) says where to lay cut pieces exactly over the pencil ones:
  `fish1=(-0.07,-0.24), fish1_len=0.86, fish1_angle=-4`, `fish2=(0.49,0.24), fish2_len=0.80, fish2_angle=20`,
  `bubble, bubble_tail=(-0.35,-0.42), bell=(0.24,-0.60), bell_top=(0.16,-0.78), weed_r, weed_l`. Lengths times `PORT_R`.
  ```python
  P = w.PILOT_PLACES
  w.trout(ink, *w.ring_xy(*P['fish1']), length=P['fish1_len']*w.PORT_R, angle=P['fish1_angle'], lid=0.45, shadow=0.8)
  w.bell(ink, w.ring_xy(*P['bell_top']), 0.55)
  ```
- `speech_bubble(ink, tail, scale=1.0, angle=0.0, alpha=1.0, shadow=0.6)`: the same pencilled bubble as a
  cut-paper piece to pin above the upper trout wherever it goes (the words are the child's: "haha verry funny").
  `tail` = the point where the bubble's neck ends (just above the trout's head); scale 1 = 150 px wide.
  Example: `w.speech_bubble(ink, (x - 70, y - 30), 0.8)` for an upper trout of length 180 centred at (x, y).

## The tin

```python
tin(ink, c=None, scale=None, t=0.0, mood=None, glow=1.0, angle=0.0, flip=False, shadow=0.7, beam=0.0, shake=0.0, alpha=1.0, **over)
    -> {'port': (x, y), 'port_r': r, 'lamp': (x, y), 'nose': (x, y), 'tail': (x, y)}
```
The riveted bread-roll tin side on (river side, and small on the table): corrugated tin drum with rolled rims,
rivets, a pasted ROLLS label, lead keel, jar-lid hatch, snorkel, rudder, propeller, a brass lamp at the nose and
the round six-bolt brass porthole. `c` = middle of the body (default `RIVER['tin_c']`); `scale` 1.0 = body 400x190
px (default 0.82). Nose and lamp point **left** (`flip=True` right). `angle` counter-clockwise: -90 stands it nose
up (lamp up, as on the table at six o'clock). `mood=None` = the glass glows amber and nobody is seen (the blank
bolts); `mood='freak'` shows Turkey behind the glass. `glow` 0..1 lamp-light inside. `beam` 0..1 draws the lamp's
cone of light up and forward from the lens. `shake` px rattles it. Returns screen points.
Example (table, A7): `w.tin(ink, (480, 420), 0.42, t, mood='freak', angle=-90, beam=0.8)`.
`tin_sprite(t, mood, glow, **over)` returns the 1080x660 RGBA if you need to move it yourself.

```python
tin_porthole(ink, c=PORT_C, r=150, mood='freak', t=0.0, glow=1.0, shake=0.0, angle=0.0, shadow=0.8, **over) -> (x, y)
```
Looking **in** from outside, close (A8): a riveted plate of the tin, the brass ring (glass radius `r`), amber light,
Turkey filling the round glass. `shake` rattles plate, rivets and all. Example: `w.tin_porthole(ink, (480, 262), 150, 'freak', t, shake=3)`.

```python
seat_frame(ink, c=PORT_C, r=PORT_R)
```
**Turkey's seat.** Draw the outside world full-frame first, then call this: it covers everything except the round
glass with the tin's dark riveted inside wall, the six-bolt brass ring, the glass's edge shadow and glare. Order:
river scene → `turkey_reflection` → `seat_frame` → `gauge`, `bolt_mark`, pick card → `badge`.

```python
brass_ring(r_in, r_out, bolts=6, pad=10, seed=0, start=-90.0) -> RGBA      # the turned brass ring by itself (paste at centre - size/2)
porthole_on_table(ink, c=PORT_C, r=PORT_R, drawing=0.45, shadow=0.7)       # the ending: ring lying on the table, paper disc, faint drawing
gauge(ink, notches=8.0, x=None, y=None, r=46, tremble=0.0, t=0.0)          # air gauge, 8 notches; pass a float and ease it down
bolt_mark(ink, n, lit=1.0, die=True, c=PORT_C, r=PORT_R, size=30, style='ivory') -> (x, y)
```
- `gauge`: brass dial, ivory face, red zone under 2, one needle. Default place `STAGE['gauge']`. The needle falls
  when you ease `notches` (e.g. `5 - w.ease(t, 2.0, 2.6)`). `tremble=1` shakes it.
- `bolt_mark(n, lit=1)`: bolt n glows warm and its die face sits on it (a written ending). `lit=0`: no glow, the
  die grey and dead (an unwritten ending). `die=False`: glow only. Works on `seat_frame` and `porthole_on_table`.
  Ending: `for n in range(1, 7): w.bolt_mark(ink, n, lit=1.0 if n <= 3 else 0.0)` (fade `lit` in one bolt at a time, clockwise).

## The river and this porthole's subject

```python
river(ink, t=0.0, planes=('back', 'far', 'bed', 'motes'), shift=0.0, calm=False)
weed(ink, x, base_y, height=160, lean=0.0, t=0.0, seed=0, n=5, spread=34, sway=1.0, dark=0.0, alpha=1.0)
arch(ink, c=None, width=None, part='all', alpha=1.0, dark=0.0) -> {'crown': (x, y), 'top': y}
twig(ink, hang=None, span=150, scale=1.0, alpha=1.0)
bell(ink, hang=None, scale=1.0, swing=0.0, clapper=None, cord=None, part='all', disc=None, flash=0.0, alpha=1.0, cord_len=92, hoist=0.0)
    -> {'mouth', 'clapper', 'knot', 'pivot', 'strike', 'half'}
ripple_rings(ink, c, radii, alpha=1.0, squash=0.42, color=(236, 246, 232), width=3)
bubbles(ink, origin, t, t0=0.0, n=7, rise=120.0, curl=70.0, size=6.0, frozen_at=None, alpha=1.0)
```
- `river`: background planes of painted and cut paper filling the frame: `'back'` water with light shafts, `'far'`
  hazed boulders and weed, `'bed'` the gravel floor, `'motes'` drifting specks. `shift` px slides the far planes
  (parallax). `calm=True` stops the motes dead.
- `weed`: a clump of torn-paper ribbon rooted at (x, base_y). `lean` degrees to the right (drive it from a
  `Follower` of the trout's current; 60+ lays it flat). `sway=0` kills its own idle movement (bolt 3: dead still).
  `dark` 0..1 for far clumps. Same `seed` = same clump.
- `arch`: Bell Boulder arch, eleven boulders of torn green-grey paper, each lit, hatched and shadowed, with torn
  moss on the shoulders. `c` = (middle x, feet y), `width` = outer width (height about 0.8 of it). Defaults are the
  seat stage. `part='left' | 'lintel' | 'right'` draws one piece so a trout can pass **behind the right pillar and
  in front of the left** (draw `right`, the trout, then `left`). `dark` 0..1 sinks it into the water colour.
- `twig`: the forked twig the bell hangs from, lying across under the crown; `hang` = where the bell's loop sits.
- `bell`: the brass bell (cut brass card with turned bands, crown loop, dark mouth), its clapper and the knotted
  cord that hangs from the clapper. `hang` = the loop's top. `swing` = the bell; `clapper` = the clapper's own angle
  (default: rides with the bell); `cord` = the angle of the cord's free end (default: follows the clapper).
  **Secondary dynamics:** drive `swing` from your action and `clapper`, `cord` from `Follower`s of it so they arrive
  late: `clap = w.Follower(swing_fn, SECONDS, f=2.4, zeta=0.2)`, `cord = w.Follower(swing_fn, SECONDS, f=1.1, zeta=0.15)`.
  The return's `'strike'` is -1 / +1 on the frame the clapper is against the left / right wall (clapper more than
  21 degrees off the bell): ring your ripple and flash off that. `flash` 0..1 brightens the bell at a strike.
  `disc='circle'` pins the red pick disc on the dome (it stays for bolts 1 to 3). `hoist` 0..1 shortens the cord
  (wound round the twig, bolt 2). `part='cord'` draws only clapper, cord and knot; `part='body'` only the bell: use
  the two calls with a trout between them so it passes behind the cord. Returns screen points: `'mouth'` (centre
  of the mouth), `'clapper'` (the ball), `'knot'` (where a trout takes it in its mouth), `'half'` (mouth half-width).
  "Swings out to the right first" = start `swing` positive.
  Example: `b = w.bell(ink, swing=18, clapper=clap.at(t), cord=cord.at(t), disc='circle', flash=fl)`.
- `ripple_rings`: flattened rings leaving the bell mouth: `w.ripple_rings(ink, b['mouth'], [r0 + 180*(t - ts) for ts in strikes if t > ts])`.
  Shrink the radii to take the sound back into the bell (bolt 3).
- `bubbles`: a string of bubbles that left `origin` at `t0`, climbing on a **clockwise curl** (up, then over to the
  right), fading over about 2.2 s. `frozen_at=T` makes them hang where they were at time T (bolt 3).

### Ready-made sets

```python
seat_stage(ink, t=0.0, layer='back', calm=False, weed_lean=0.0)
river_stage(ink, t=0.0, layer='back', glow=1.0, mood=None, calm=True) -> tin points from the 'front' call
```
`seat_stage` is the standing set from Turkey's seat in two layers so trout can go between:
```python
w.seat_stage(ink, t, 'back')                 # river, far weed, arch RIGHT pillar + lintel, twig
# ... trout that are behind the left pillar / behind the cord ...
b = w.bell(ink, swing=sw, clapper=cl, cord=co, part='cord')
# ... trout in front of the cord ...
w.seat_stage(ink, t, 'front')                # arch LEFT pillar, near weed
w.bell(ink, swing=sw, clapper=cl, cord=co, part='body', disc='circle')
# ... the lead trout, speech_bubble, ripple_rings ...
w.turkey_reflection(ink, mood='freak', t=t); w.bubbles(ink, (408, 316), t, t0)
w.seat_frame(ink); w.gauge(ink, 5); w.bolt_mark(ink, 1); w.badge(ink)
```
`calm=True` stops every idle movement (motes, weed sway). `weed_lean` leans all the weed.
`river_stage` is the river side for the blank bolts 4 to 6: `'back'` = river, arch, twig, the still bell;
`'front'` = the tin low in frame with its porthole facing us, glass glowing amber, nobody visible (`mood=None`),
near weed in front of the tin. Nothing in it moves when `calm=True` (the default). For a blank bolt:
```python
w.river_stage(ink, t, 'back'); w.river_stage(ink, t, 'front'); w.die_face(ink, 4, 480, 60, 54); w.badge(ink)
```

## Scene change: the clockwise sweep

```python
sweep(ink, new_img, f, c=PORT_C, arm=True, length=None)       # f 0..1
brass_arm(ink, c, clock_deg, length=620)
```
A brass arm pinned at `c` sweeps once round clockwise from twelve o'clock like a clock hand and the next scene is
behind it. Draw the old scene on `ink`, the new one on `o = w.offscreen(ink)`, then `w.sweep(ink, o.img, f)`, then
`badge`. It never goes back the other way.

## Buttons, dice, card, cup, badge

```python
button(ink, kind, x, y, r=26, pressed=0.0, lit=1.0, alpha=1.0)      # kind: 'triangle' green, 'circle' red, 'cross' blue, 'square' pink, 'hexagon' amber
button_disc(ink, kind, x, y, r=10, alpha=1.0)                       # the small flat mark a pick leaves behind
die_face(ink, n, x, y, size=44, style='ivory', lit=1.0, angle=0.0, alpha=1.0)      # n 1..6; style 'ivory' or 'print'; lit 0 = grey and dead
pick_card(ink, c=(480, 262), side='turkey', picked=None, press=0.0, loop=0.0, angle=-2.0, alpha=1.0, initial=None, lift=0.0)
    -> {'ring': (x, y), 'tip': (x, y) or None, 'buttons': {kind: (x, y)}}
die_cup(ink, x, y, height=150, die=True, alpha=1.0, shadow=0.9)
badge(ink, n=13)
```
- `button`: the coloured cap **is** the shape, moulded with a bevel, standing in a dark round well of radius about
  1.3 r. `pressed` 0..1 sinks it; `lit` 0..1 (0 dull grey, 1 glowing).
- `die_face`: 1 Probable, 2 Plausible, 3 Preposterous for bolts 1 to 3 and 4, 5, 6 for bolts 4 to 6 (the sheet prints
  them that way round the ring). `'print'` is the worksheet's small printed face.
- `pick_card`: a torn piece of the worksheet, 420x230 px, centre `c`: title, the two choices each in its pill with
  its button, "Draw the one you pick" and the dashed ring. `side='turkey'`: green triangle "Tripwire alarm", red
  circle "Dinner bell". `side='trout'`: blue cross "Polite ferry customer", pink square "Bell-ringer prank".
  `picked='circle'` with `press` 0..1 sinks and lights that button; the other stays dull. **`picked=None` lights
  nothing and the ring stays empty: that is the blank pick.** `loop` 0..1 pencils the friend's own wobbly circle,
  clockwise, in the dashed ring; the return's `'tip'` is the pencil point for `w.pencil(ink, r['tip'], 50)`.
  `initial='A.'` prints the first initial small in the corner (or leave None). `lift` 0..1 raises the card (laying
  down, taking away). Returns screen positions of the ring and buttons.
  B0: `r = w.pick_card(ink, side='turkey', picked='circle', press=pr, loop=lp, initial='A.')`.
  C0: `w.pick_card(ink, side='trout', picked=None, initial='M.')`.
- `die_cup`: leather cup, stitched, standing with its foot at (x, y); one die rests inside, seen over the lip. It
  has no thrown state on purpose.
- `badge`: "13", white on a dark rounded badge, top right. **Call it last in every frame.**

## Things to know

- Names: first initials only (`initial=`). The pilot's name is never drawn anywhere.
- The class photographs are not used by any function; nothing here loads them.
- Weak spots, honestly: the trout's mouth is the engraving's and cannot be flattened (the eyelid does that job);
  Turkey's raised neck feathers are plain cut paper beside an engraving; the reflection is busy when the wings are
  low (pass `part='head'` to `turkey_reflection` if a shot needs it cleaner); no hand exists.
