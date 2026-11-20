# c25 · WORLD · the shared pieces (porthole 25 · Lock · the trout in the upside-down fishbowl)

World unit. Everything is in `films/swarm/c25/world.py`. You should not need to read its source.

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))          # films/swarm/c25  (the editor: films/swarm/c25 from films/)
import world as w
from kit import Ink, W, H, FPS, clamp, ramp, ease, smooth, lerp, lerp2      # world.py puts films/ on sys.path
```

- Frame is 960x540, 24 fps. All coordinates are screen pixels, y down, unless a line says "ring units".
- Every draw function takes the kit's `ink` first and draws straight onto it, in call order (later calls are in front).
- `angle=` on a cutout is degrees **counter-clockwise** on screen (PIL's sense).
- Nothing moves by itself except what takes `t`. Pass `t` = your scene time. Nothing here boils.
- Cost: `walker` is about 80 ms a frame, a whole seat or river shot about 90 ms. Sprites are cached; first use of a piece takes a second or two.
- Test stills: `python3 films/swarm/c25/world.py` writes `films/stills/c25_world/01..17_*.png`. The `_demo_*` functions
  at the bottom of world.py are worked examples of whole shots (`_demo_seat`, `_demo_uncomfy`, `_demo_dry`,
  `_demo_river`, `_demo_astronaut`, `_demo_card`, `_demo_flip`, `_demo_blank`, `_demo_end`).

## What is foraged, what is handmade

| Piece | Made of |
|---|---|
| Turkey | Foraged: Audubon, *The Birds of America* plate 1 (Wikimedia Commons, public domain), cut into head-and-neck, lower beak, wattle, body, wing, and hinged. The white staring eye and the raised neck feathers are cut paper. |
| Trout | Foraged: Denton's 1896 brook trout plate (Wikimedia Commons, public domain), cut out, flexed; cut-paper eyelid. |
| The walker (this porthole's subject) | The same foraged trout lying across the top; everything else handmade cut paper with its own shadow per piece: glass bowl with water inside, brass collar, canvas tunic with belt and buttons, trout-skin arms and legs, orange fin hands and feet. |
| Everything else | Handmade in code: lock wall, ladder, mooring ring, timber gate, flagstones, river plates, the tin, brass ring, pencil drawing, pencil, buttons, dice, die cup, gauge, pick card, empty card, badge. |

Credits: `films/credits/c25.json`. Source files: `films/sources/c25/` (git-ignored). The class photographs are not
loaded by anything. **There is no hand**: pieces are laid by sliding them in with `lift=` and `shadow=`, or with the pencil.

## Standard places

```python
w.PORT_C = (480, 262)      # centre of the round glass in every porthole shot AND of the printed ring on the table
w.PORT_R = 212             # glass radius = inner radius of the printed ring
w.RING_OUT = 262           # outer radius of the brass ring / printed ring
w.GROUND = 434             # the lock floor line the walker's feet stand on
w.STAGE = dict(walker=(476, 434), walker_h=306,       # exactly where and how big the pilot drew it
               reflection=(352, 392), gauge=(112, 446))   # Turkey's reflection low left in the glass; gauge low left on the tin wall
w.RIVER = dict(tin_c=(660, 318), tin_scale=0.9, walker=(236, 470), walker_h=300)
```

Bolts (centres on the brass ring at PORT_C; `w.bolt_xy(n)`): 1 (480, 22) · 2 (687, 142) · 3 (687, 382) · 4 (480, 502) · 5 (273, 382) · 6 (273, 142).
The glass shows x 268..692, y 50..474. In the seat the lock's mooring ring is at about (332, 200), the ladder at
x 596..648, the timber gate from x 680 rightwards. On the river side everything is mirrored (gate at the left, x under 280).

## Palette

`w.PAL` is a dict of RGB tuples: `table, table_dk, sheet, sheet_edge, print, pencil, pencil_soft, water_top, water_mid,
water_deep, shaft, stone, stone_dk, stone_lt, moss, moss_dk, moss_lt, weed, weed_dk, weed_lt, timber, timber_dk,
timber_lt, iron, brass, brass_hi, brass_dk, brass_line, tin, tin_dk, wall, lamp, amber, skin, skin_dk, skin_spot, fin,
fin_dk, canvas, canvas_dk, glass, bowl_water, sky, dust, dry_ground, green, red, blue, pink, hexamber, ivory, pip,
leather, leather_dk, badge, white, unlit`.
`w.BUTTONS = {'triangle': green, 'circle': red, 'cross': blue, 'square': pink, 'hexagon': amber}`.

## Helpers

| Function | What it does |
|---|---|
| `put(ink, spr, cx, cy, angle=0, scale=1, flip=False, alpha=1, shadow=0, shadow_off=(5,7), shadow_blur=5)` | Lay any RGBA cutout with its centre at (cx, cy). `shadow` 0..1 = soft contact shadow; grow `shadow_off` to lift a piece. |
| `offscreen(ink)` | A second full-frame `Ink` for the same frame. Draw the next scene on it, pass `.img` to `card_flip`. |
| `Follower(target_fn, seconds, f=1.6, zeta=0.25, x0=None)` then `.at(t)` | Spring-damper follower for **secondary dynamics**. Build once at module level, read per frame. `zeta` 0.15 rings on, 1.0 settles dead. With the driver still it is at rest inside 1 s at `f=1.6, zeta=0.35`. |
| `ring_xy(u, v, c=PORT_C, r=PORT_R)` | Ring units (the drawing's coordinates: centre 0,0, inner radius 1) to screen. |
| `bolt_xy(n, c=PORT_C, r=None)`, `clock_xy(c, r, clock_deg)` | Centre of bolt n (1 at twelve, then clockwise); a point on a circle (0 = twelve, clockwise). |
| `vnoise, catmull` | value noise (h, w); a smooth curve through points. |

Slopping water (use this pattern for the bowl after every step and every flip):
```python
def _kick(t): return 9.0 * math.sin(2 * math.pi * 1.1 * t) if walking(t) else 0.0     # the driver
SLOSH = w.Follower(_kick, SECONDS, f=1.5, zeta=0.3)                                   # module level
w.walker(ink, step=t * 1.1, slosh=SLOSH.at(t), wave=clamp(abs(SLOSH.at(t)) / 8))
```

## THE WALKER: this porthole's subject

The diner trout wearing the upside-down fishbowl, built to the pilot's drawing and not to the deck picture: the fish
lies level across the top like a hat brim, nose a little down; the glass bowl is round its head, mouth down on a
brass collar, **water inside**; a canvas tunic (the bean) hangs from the fish's middle; both arms are on the tail
side; two walking legs with flat orange fin feet.

```python
walker(ink, x=None, y=None, height=None, step=0.0, flip=False, lean=0.0, parts=WALKER_PARTS, phase=0.0, amp=5.0,
       lid=0.0, eye_roll=None, water=0.86, slosh=0.0, wave=0.0, bowl_bubbles=None, bowl_shift=(0, 0), bowl_tilt=0.0,
       squash=0.0, hook=0.0, swing=0.0, bob=True, alpha=1.0, shadow=0.0, lift=0.0) -> dict of screen points
```
- `(x, y)` = the **ground point under its body** (default `STAGE['walker']`); `height` = bowl top to ground, px
  (default 306). Its width is about 0.95 x height: nose 0.38 h left of x, tail tip 0.37 h right of x.
- Faces and walks **left** (Turkey's seat: right to left). `flip=True` faces and walks **right** (river side). That is rule 2.
- `step` = walk phase in strides. 0 is the drawing's pose (near leg forward and flat, far leg trailing, toe turned).
  To walk: `step = t * 1.1` and move x yourself, about `0.36 * height` px per stride (leftwards unless flipped).
  A foot lands at `step` = 0.25 + n (near foot) and 0.75 + n (far foot): put `dust` there.
- `lean` = degrees the whole figure tips forward (P2's lean-in: `lean=10`). The water line stays level with the world.
- `parts` = any of `w.WALKER_PARTS = ('legs', 'tunic', 'bowl', 'fish', 'arms')`, to lay it down piece by piece.
- `phase`, `amp` swim the fish's tail (`phase=t*4, amp=5` trailing the walk); `lid` 0..1 a flat eyelid (0.45 unamused);
  `eye_roll` degrees = a white rolling eye.
- The bowl: `water` 0..1 how full (0.86 = full of water with a sliver at the top); `slosh` = degrees the surface is
  tipped right now, `wave` 0..1 a ripple on it; `bowl_bubbles=t` = bubbles inside the bowl that **sink** (rule 4);
  `bowl_shift=(dx, dy)` (design px, about 2.6 x screen px at height 306) and `bowl_tilt` degrees wriggle the helmet
  on its collar; `squash` 0..1 presses the fish's nose flat against the inside of the glass (the bowl slides back to meet it).
- `hook` 0..1 raises the upper arm so its hand hooks under the brass collar (bolt 2). `swing` = degrees both arms swing.
- `shadow` 0..1: about 0.8 lying on the table, 0 in the water. `lift` 0..1 raises it off the table.
- Returns screen points: `bowl` (centre), `bowl_r` (rx, ry), `bowl_top`, `top`, `collar` (where the hand hooks),
  `nose`, `eye`, `tail`, `hand` (upper), `hand2` (lower), `feet` [near, far] (toe tips), `ground` [near, far] (where each
  foot meets the floor), `body` (tunic centre).

Examples:
```python
wp = w.walker(ink, step=t * 1.1, bowl_bubbles=t, slosh=SLOSH.at(t))                       # seat, walking on the spot
wp = w.walker(ink, 236, 470, 300, flip=True, lean=10 * ease(t, 1.0, 1.8))                  # river side, leaning in (P2)
wp = w.walker(ink, hook=h, squash=h, bowl_shift=(8 * math.sin(t * 9) * h, 0), bowl_tilt=-5 * h)   # bolt 2
w.crayon_ring(ink, wp['bowl'], wp['bowl_r'][0] * 1.12, wp['bowl_r'][1] * 1.16, w.PAL['green'], done)   # T0: the helmet ringed green
w.dust(ink, *wp['ground'][0], age=t - t_land)                                               # bolt 3
```

## Turkey

Moods: `w.TURKEY_MOODS = ('calm', 'wave', 'panic', 'freak', 'gasp', 'flap', 'frozen')`.

| Mood | What moves |
|---|---|
| `calm` | slow nod, wattle sways, beak shut, plain engraved eye, wings folded |
| `wave` | one wing up and waving, beak a little open |
| `panic` | white eye, beak chattering, wattle swinging, wings half up, neck feathers half raised, small shake. **This film's default** (it is what `turkey_reflection`, `seat_scene`, `river_scene` use). |
| `freak` | white ringed eye, beak hinged wide, wattle thrown side to side, neck feathers up, both wings beating, whole bird shaking |
| `gasp` | neck stretched back, beak at its widest, wings held up (the twist in the low roof, bolt 2) |
| `flap` | as freak, wings so fast they leave ghost copies |
| `frozen` | rigid, wings shut, a fast small tremble |

The board wants **counted wing-beats** (a puff of bubbles and one gauge tick on each beat, nothing between). Drive the
wings yourself with the `wing` override and keep the rest of `panic`:
```python
BEATS = [0.5, 1.4, 2.3]                                             # your beat times
def wing(t): return max([90 * math.sin(math.pi * clamp((t - b) / 0.5)) for b in BEATS] + [8])
w.turkey_reflection(ink, mood='panic', t=t, wing=wing(t))
for b in BEATS: w.bubbles(ink, (300, 250), t, t0=b + 0.2, n=6)
w.gauge(ink, 6 - sum(ease(t, b + 0.2, b + 0.45) for b in BEATS))    # one whole tick per beat
```

```python
turkey(ink, cx, cy, height=300, mood='calm', t=0.0, part='bust', flip=False, alpha=1.0, shadow=0.0, angle=0.0, **over)
turkey_sprite(mood='calm', t=0.0, height=300, part='bust', **over) -> (RGBA image, (ax, ay))
turkey_pose(mood, t) -> dict of the pose keys
turkey_reflection(ink, cx=None, cy=None, height=230, mood='panic', t=0.0, alpha=0.6, clip=(PORT_C, PORT_R), part='bust', **over)
```
- `turkey` faces **left**; `flip=True` faces right. `part='bust'` (head, neck, shoulders; wings show when raised): anchor
  = middle of head-and-neck, `height` = crest to the cut. `part='head'`: anchor = the head. `part='full'` (whole bird,
  tail fan and all): anchor = body centre, `height` = crest to tail tip.
- `**over` overrides any pose key for this frame: `neck` (deg), `wattle` (deg; drive it from a `Follower` so it lags the
  beat), `beak` (deg open, 0..31), `eye` (0 engraved, 1 white), `wing` (deg raised, 0..100; under 4 = folded), `ruff`
  (0..1), `shake` (px), `blur` (1 = ghost wings).
- `turkey_reflection` = Turkey's reflection lying on the inside of the porthole glass from his seat: faces right,
  lamp-pale, see-through, clipped to the glass. Default place `STAGE['reflection']`, low left as in the deck picture.
  Call it after the outside world and the walker and **before** `seat_frame`. It overlaps the walker's near leg at the
  default places; move the walker right (x 500 to 540) or pass `part='head'` if a shot needs the legs clear.

## Trout (plain brook trout, for bolt 4's escort)

```python
trout(ink, cx, cy, length=220, angle=0.0, flip=False, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False, alpha=1.0, shadow=0.0)
trout_sprite(length=220, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False) -> RGBA facing left
```
Faces **left**; `flip=True` faces right. `angle` counter-clockwise. `phase` (radians) swims the tail (`t*6` cruising);
`amp` = bend (0 = rigid). `lid` 0..1 lowers a flat eyelid; **leave it 0 for bolt 4 (eyes open)**. The eye is the
engraving's: it looks nowhere in particular, which is what bolt 4 needs. `belly_up=True` turns it over.
Example: `w.trout(ink, 300 + 40 * t, 420, 120, flip=True, phase=t * 6 + k)`.

## The pilot's page (table)

```python
table(ink, sheet=True)                       # wooden boards + the worksheet paper under the ring. Fills the frame.
sheet_ring(ink, c=PORT_C, r=PORT_R, alpha=1.0, lit=None)      # the printed double circle with six little die faces
pilot_page(ink, t, c=PORT_C, r=PORT_R, alpha=1.0) -> (tip_xy, pen_down)     # the drawing t seconds in, on the board's P1 timing
pilot_drawing(ink, done=1.0, c=PORT_C, r=PORT_R, alpha=1.0, color=None) -> (tip_xy, pen_down)
pilot_morph(ink, f, c=PORT_C, r=PORT_R, alpha=1.0, color=None)             # Foldes change: the lines move into the puppet
pencil(ink, tip, angle=52.0, lift=0.0, length=250, alpha=1.0)   # a cut-card pencil with shadow; point at `tip`
```
- `pilot_page` is the one call for P1 strokes 1 to 7. It returns where the pencil point is and whether it is down:
  ```python
  w.table(ink); w.sheet_ring(ink)
  tip, down = w.pilot_page(ink, t)
  w.pencil(ink, tip, lift=0 if down else 1)
  ```
  `w.PILOT_TIMES = {'fish': (0.1, 1.35), 'tail': (1.45, 2.15), 'fin_mouth': (2.25, 2.8), 'bowl': (2.9, 4.2),
  'body': (4.3, 5.55), 'arms': (5.65, 6.6), 'legs': (6.7, 7.8)}`. Between groups the pencil travels lifted. After 7.8 s
  the drawing is whole: move the pencil out of frame yourself and stop calling `pencil`.
- `pilot_drawing(done=...)` for your own timing: `done` is 0..1 of the whole drawing by pencil travel, or a dict
  `{group: 0..1}` with `w.PILOT_GROUPS = ['fish', 'tail', 'fin_mouth', 'bowl', 'body', 'arms', 'legs']`. `alpha=0.45`
  gives the faint drawing of the ending.
- The drawing is traced by eye from the child's sheet (`w.PILOT_STROKES`: list of `{group, pts, to, weight, len}`,
  points in ring units): a firm, dark, flat fish with forked tail tipped up, a back-fin bump, a pressed-hard mouth
  with three teeth ticks, a fin underneath; four light scribbled loops for the bowl behind the head; the bean body;
  two stacked arms on the right ending in squiggle hands (and one faint rubbed line on the left); two walking legs.
  It leans a little, sits left of centre and high, has a fixed wobble and does not shimmer.
- **P1 step 9, the Foldes change** (8.4 to 10.0 s). `pilot_morph(ink, f)` draws the finished drawing with its lines
  moved point for point: the four loose loops tighten onto the one bowl outline, flat at the mouth; the other lines
  hold where the cut pieces will lie. The walker placed with `PILOT_PLACES` lies exactly under the lines:
  ```python
  P = w.PILOT_PLACES
  x, y = w.ring_xy(*P['walker']); hgt = P['walker_h'] * w.PORT_R            # (475.7, 433.5), 306
  w.table(ink); w.sheet_ring(ink)
  for k, part in enumerate(('legs', 'tunic', 'bowl', 'fish', 'arms')):       # each piece slides in under the pencil lines
      a = ease(t, 8.5 + k * 0.22, 8.9 + k * 0.22)
      if a > 0: w.walker(ink, x, y, hgt, parts=(part,), shadow=0.8, lift=1 - a, alpha=min(1, a * 3))
  w.pilot_morph(ink, ease(t, 8.4, 9.4), alpha=1 - ease(t, 9.4, 9.9))          # lines move, then are covered: not a cross-fade
  ```
  `PILOT_PLACES` also has `fish=(-0.026, -0.199), fish_len=1.112, fish_angle=9`, `bowl=(-0.235, -0.294), bowl_rx,
  bowl_ry`, `body=(-0.05, 0.22)` in ring units.

## The lock, the river and the dry day

```python
seat_backdrop(ink, t=0.0, lift=0.0, straight=None, shift=0.0, calm=False) -> hem_y
river_backdrop(ink, t=0.0, shift=0.0, calm=False, lines=True)
ground_lines(ink, straight=0.0, t=0.0, y0=None, alpha=1.0, clip_y=0)
bubbles(ink, origin, t, t0=0.0, n=7, rise=120.0, spread=16.0, size=6.0, sink=False, drop_at=None, alpha=1.0, clip_y=None)
dust(ink, x, y, age, size=1.0, toward=1.0)
river(ink, t=0.0, planes=('back', 'far', 'bed', 'motes'), shift=0.0, calm=False)      # the plain river planes, if wanted
weed(ink, x, base_y, height=160, lean=0.0, t=0.0, seed=0, n=5, spread=34, sway=1.0, dark=0.0, alpha=1.0)
```
- `seat_backdrop` = what is outside the glass from Turkey's seat, full frame: the lock chamber (coping, courses of
  dressed stone with an algae line, an iron mooring ring, an iron ladder, the heavy timber gate at the right, a
  flagstone floor with its foot line at y 400) under river water with light shafts, drifting motes and pale wavy
  floor hatching. Draw it first.
  **`lift` 0..1 is bolt 3's blind**: the wet picture slides up off the top with a wooden batten along its lower
  edge, and the same lock is left standing in plain dry daylight below. `lift=1` is all dry. The floor hatching
  straightens point for point into brown dry ground lines as it goes (`straight`, default = `lift`; that is the
  Foldes change of B3). Returns the batten's y (540 when nothing is lifted): above it is still wet.
  B3: `hem = w.seat_backdrop(ink, t, lift=ease(t, 0.8, 2.6))`.
- `river_backdrop` = the river side: the same lock under water in **mirror image**, full frame.
- `bubbles`: a puff that left `origin` at `t0` and **rises** (Turkey's panic bubbles, outside the tin), gone in 2 s.
  `sink=True` sends them down. `drop_at=T`: from time T every bubble stops and falls like a pebble (bolt 3).
  `clip_y=hem` hides bubbles above the hem. Bubbles inside the bowl are the walker's `bowl_bubbles`.
  One puff per wing-beat: `w.bubbles(ink, (300, 250), t, t0=beat + 0.2, n=6)`; B1's last puff `n=1`, then none.
  From the seat let them leave near the left rim of the glass, about (300, 250); from the river side from the tin's
  top seam, `(tp['port'][0] + 60, tp['port'][1] - 90)` at default scale.
- `dust(x, y, age)`: five torn scraps of tan paper kicked up by one footfall, gone in 0.7 s. `toward=+1` drifts right
  (behind a walker going left). Only when dry.
- `weed`: torn-paper ribbon weed rooted at (x, base_y), if a shot wants some; `lean` degrees right, `sway=0` still.

### Ready-made shots (fixed layer order = the occlusion rule)

```python
seat_scene(ink, t=0.0, walker_kw=None, turkey_kw=None, notches=3.0, bolt=None, lift=0.0, frame=True) -> (walker points, hem_y)
river_scene(ink, t=0.0, tin_kw=None, walker_kw=None, notches=None) -> (tin points, walker points)
tin_dial_xy(tin_points) -> (x, y)
```
- `seat_scene` draws, back to front: lock and river, the walker (tunic, water inside the bowl, fish, glass),
  Turkey's reflection on the porthole glass, brass rim and tin wall, gauge, the lit bolt with its die.
  `walker_kw` / `turkey_kw` are dicts for `walker` / `turkey_reflection` (`walker_kw=False` = no walker).
  `frame=False` stops after the reflection so you can add things inside the glass, then call `seat_frame`, `gauge`,
  `bolt_mark` yourself.
  `wp, hem = w.seat_scene(ink, t, dict(step=t * 1.1, bowl_bubbles=t), dict(wing=wing(t)), notches=n, bolt=1); w.badge(ink)`
- `river_scene` draws: the lock under water (mirrored), the tin with Turkey behind its porthole glass, the walker
  facing right at `RIVER['walker']`. `notches=3` adds the small dial riveted on the tin's flank (`tin_dial_xy`).
  `tp, wp = w.river_scene(ink, t, dict(wing=wing(t)), dict(lean=10), notches=6)`
- By hand, the seat order is: `seat_backdrop` → `walker` → `bubbles` → `turkey_reflection` → `seat_frame` → `gauge`,
  `bolt_mark`, pick card → `badge`. The river order is: `river_backdrop` → `tin` → `gauge` on the flank → trout and
  `walker(flip=True)` → `bubbles` → `badge`. For bolt 4 keep every fish clear of the porthole glass (`tp['port']`, `tp['port_r']`).

## The tin

```python
tin(ink, c=None, scale=None, t=0.0, mood=None, glow=1.0, angle=0.0, flip=False, shadow=0.7, beam=0.0, shake=0.0, alpha=1.0, **over)
    -> {'port': (x, y), 'port_r': r, 'lamp': (x, y), 'nose': (x, y), 'tail': (x, y)}
tin_porthole(ink, c=PORT_C, r=150, mood='freak', t=0.0, glow=1.0, shake=0.0, angle=0.0, shadow=0.8, **over) -> (x, y)
bottle_lines(ink, c=None, scale=None, f=1.0, flip=False, angle=0.0, alpha=1.0, color=(240, 236, 224), width=3, done=1.0)
    -> {'neck': (x, y), 'base': (x, y)}
```
- `tin`: the riveted bread-roll tin side on: corrugated drum with rolled rims, rivets, a pasted ROLLS label, keel,
  hatch, snorkel, rudder, propeller, a lamp at the nose and the round six-bolt brass porthole. `c` = middle of the body
  (default `RIVER['tin_c']`); `scale` 1.0 = body 400x190 px (default 0.9). Nose points **left** (`flip=True` right).
  `mood='panic'` shows Turkey behind the glass (`**over` as for `turkey`, e.g. `wing=`); `mood=None` = empty amber glass.
  `angle` counter-clockwise; `shake` px rattles it. Bolt 4's giant suit: `w.tin(ink, (610, 250), 1.35, t, mood='panic', angle=4 * math.sin(t * 0.5), wing=wing(t))`
  with the walker at height 150 and trout of length 120 beside it.
- `tin_porthole`: looking **in**, close: a riveted plate, the brass ring (glass radius `r`), amber light, Turkey
  filling the glass. `w.tin_porthole(ink, (480, 262), 150, 'panic', t, wing=wing(t))`.
- `bottle_lines` (P2): the tin's outline redrawn in pale pencil as a bottle lying on its side, by moving the same
  line: `f=0` hugs the tin, `f=1` is a bottle with its neck and lip running out past the lamp end. Give it the same
  `c, scale, flip, angle` as the tin. The round porthole does not move: it is what holds while tin reads as bottle.
  `w.bottle_lines(ink, f=ease(t, 1.2, 2.2) - ease(t, 3.4, 4.2), alpha=ease(t, 1.0, 1.3) - ease(t, 4.2, 4.4))`
- R0: ring the tin in blue: `w.crayon_ring(ink, tp_centre, 330 * s, 190 * s, w.PAL['blue'], done, seed=2, width=6)` (s = scale / 1.35).

## Seat frame, gauge, bolts

```python
seat_frame(ink, c=PORT_C, r=PORT_R)
gauge(ink, notches=6.0, x=None, y=None, r=46, tremble=0.0, t=0.0)
bolt_mark(ink, n, lit=1.0, die=True, c=PORT_C, r=PORT_R, size=30, style='ivory') -> (x, y)
bolt_die(ink, n, c=(480, 268), lit=1.0, size=64, gap=26) -> {'bolt': (x, y), 'die': (x, y)}
brass_ring(r_in, r_out, bolts=6, pad=10, seed=0, start=-90.0) -> RGBA
porthole_on_table(ink, c=PORT_C, r=PORT_R, drawing=0.45, shadow=0.7)
```
- `seat_frame`: covers everything except the round glass with the tin's dark riveted inside wall, the six-bolt
  brass ring, the glass's edge shadow and glare.
- `gauge`: brass dial, ivory face, **E** left, **F** right, six ticks, red under one tick, a pin for the needle to
  rest on. **`notches` 6 = FULL, 3 = half, 0 = EMPTY.** One whole tick per wing-beat; give it a float and ease it
  (overshoot with a `Follower`, `f=3, zeta=0.35`, for the needle that goes one too far and comes back). Default place
  `STAGE['gauge']` (low left on the wall). On the tin's flank: `w.gauge(ink, n, *w.tin_dial_xy(tp), r=20)` (the letters
  drop out under r 26). `tremble=1` shakes the needle.
  Every ending starts from **3** (half): P4 goes 6 → 3; B1 3 → 0; B2, B3, B4 lose one tick.
- `bolt_mark(n, lit=1)`: bolt n on the brass ring glows warm and its die face sits on it; `lit=0` = no glow, die
  grey and dead (an unwritten ending); `die=False` = glow only. Works on `seat_frame` and `porthole_on_table`.
  Bolt 1 sits at the very top of the frame (y 22): its die is cut by the frame edge a little; that is expected.
- `bolt_die(n)`: one brass hex bolt with die face n beside it, anywhere (the blank cards; bolt 4 on the river side,
  e.g. `w.bolt_die(ink, 4, (120, 60), size=44)`).
- `porthole_on_table`: the ending's porthole lying flat on the table with a paper disc in it and the pilot's drawing
  faint (`drawing=0` for none, then draw a small `walker` and `turkey_reflection(clip=(c, r))` inside it yourself).
  Draw `table(ink, sheet=False)` first. Ending:
  ```python
  w.table(ink, sheet=False); w.porthole_on_table(ink)
  for n in range(1, 7): w.bolt_mark(ink, n, lit=ease(t, 0.5 + 0.4 * n, 0.8 + 0.4 * n) if n <= 4 else 0.0)
  w.die_cup(ink, 850, 505, 150); w.badge(ink)
  ```

## The cut: a card turned over

```python
card_flip(ink, new_img, f)          # f 0..1
empty_card(ink)
```
- `card_flip` is **the only cut in this film** (rule 1). The whole picture is a card turned over top to bottom about
  its horizontal middle: to `f=0.5` the old picture tips away to an edge, then the next comes round. 8 frames:
  `f = (t - t0) * 3`. Draw the old scene on `ink` (without the badge), the new one on `o = w.offscreen(ink)`, then:
  ```python
  f = (t - T_CUT) * 3
  if 0 < f < 1:
      o = w.offscreen(ink); draw_next(o, t); w.card_flip(ink, o.img, f)
  w.badge(ink)
  ```
- `empty_card`: a blank ending. An empty lit card of the worksheet's paper on the table, cut edge and shadow.
  `w.empty_card(ink); w.bolt_die(ink, 5); w.badge(ink)` and nothing else, ever.

## Buttons, dice, marks, card, cup, badge

```python
button(ink, kind, x, y, r=26, pressed=0.0, lit=1.0, alpha=1.0)      # 'triangle' green, 'circle' red, 'cross' blue, 'square' pink, 'hexagon' amber
button_disc(ink, kind, x, y, r=10, alpha=1.0)                       # a small flat mark of the button's shape
die_face(ink, n, x, y, size=44, style='ivory', lit=1.0, angle=0.0, alpha=1.0)      # n 1..6; 'ivory' or 'print'; lit 0 = grey and dead
friend_mark(ink, kind, c, size=26, done=1.0, weight=1.3, alpha=1.0, color=None) -> pencil point
scribble(ink, c, r=16, done=1.0, weight=1.0, alpha=0.9) -> pencil point
crayon_ring(ink, c, rx, ry=None, color=None, done=1.0, seed=0, width=5, alpha=1.0) -> crayon point
pick_card(ink, c=(480, 262), side='turkey', picked=None, press=0.0, mark=0.0, scribble=0.0, angle=-2.0, alpha=1.0, initial=None, lift=0.0)
    -> {'ring': (x, y), 'tip': (x, y) or None, 'buttons': {kind: (x, y)}}
die_cup(ink, x, y, height=150, die=True, alpha=1.0, shadow=0.9)
badge(ink, n=25)
```
- `button`: the coloured cap is the shape, moulded with a bevel, in a dark round well of radius about 1.3 r.
  `pressed` 0..1 sinks it; `lit` 0..1 (0 dull, 1 glowing). Buttons and dice are never flipped or mirrored (rule 6).
- `die_face`: 1 Probable, 2 Plausible, 3 Preposterous; 4, 5, 6 the same for the trout's bolts.
- `friend_mark`: the friend's own pencil mark drawn by hand, progressive with `done`: `'triangle'` small and leaning
  (as K. drew it), `'cross'` two long crossing strokes (as N. drew it). `size` = half its height.
- `scribble`: a child's zigzag colouring-in over a round thing (N. coloured the cross button in).
- `crayon_ring`: one wobbly hand-drawn coloured loop that overshoots its start (green round the helmet, blue round the suit).
- `pick_card`: a torn piece of the worksheet, 420x230 px, centre `c`: title, the two choices each in its pill with its
  button, "Draw the one you pick" and the dashed ring. `side='turkey'`: green triangle "Scuba helmet", red circle
  "Dry-air bubble". `side='trout'`: blue cross "Giant astronaut suit", pink square "Bird in a bottle".
  `picked` + `press` 0..1 sinks and lights that button, the other stays dull. `mark` 0..1 pencils the friend's mark
  in the dashed ring; `scribble` 0..1 colours the picked button in. `initial='K.'` prints the initial small in the
  corner. `lift` 0..1 raises the card. Returns screen positions; `'tip'` is the pencil point for `w.pencil(ink, r['tip'], 50)`.
  T0: `r = w.pick_card(ink, (730, 130), 'turkey', 'triangle', press=pr, mark=mk, initial='K.')   # the bowl stays visible at the left`
  R0: `r = w.pick_card(ink, (250, 130), 'trout', 'cross', press=pr, mark=mk, scribble=sc, initial='N.')   # the tin stays visible at the right`
  Keep the card off the middle of the glass so the ringed helmet (or tin) shows behind it.
- `die_cup`: leather cup, stitched, foot at (x, y); one die rests inside, a corner over the lip. It has no thrown state.
- `badge`: "25", white on a dark rounded badge, top right. **Call it last in every frame, after any `card_flip`.**

## Things to know

- Names: first initials only (`initial=`). The pilot's name is drawn nowhere.
- Mirror rule: seat = walker faces left, Turkey is a reflection low left; river = `flip=True`, Turkey is behind the tin's glass.
- Bolt 4 is `unsure`: nothing here aims an eye at anything; do not add a target.
- Weak spots, honestly: the walker's fish passes out through the side of the glass (it is a collage, as in the
  child's drawing, not a sealed helmet); the squashed nose is subtle at seat size, so sell bolt 2 with `hook`,
  `bowl_shift` and the slop; the walk is a plain two-pose swing; the hooked hand is orange on brass and small;
  Turkey's reflection is busy when the wings are low; the wet lock wall is quiet (it reads as green stone, no more);
  the card flip is a squash with shading, not true perspective; there is no hand.
