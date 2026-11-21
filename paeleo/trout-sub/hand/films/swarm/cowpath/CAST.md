# CAST: the cow of "Don't Pave the Cow Paths"

`films/swarm/cowpath/cast.py`. One jointed side-view puppet, three materials, three animals.
Look first: `films/stills/cowpath_cast/` has `pose_sheet.png` (every pose, silhouette), `pose_sheet_line.png`
(the same in pencil), `walk_strip.png` (12 frames of the cycle), `walk_world.png` (walking over a hill, with
herd cow, calf, tired cow), `materials.png` (3 styles x 3 kinds, down to 0.18 scale), `act_strip.png`
(an eased performance). Regenerate with `python3 films/swarm/cowpath/cast.py` (also runs the measured checks).

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))   # films/swarm/cowpath
import cast
```

## The three things you choose on every call

| argument | values | meaning |
|---|---|---|
| `style` | `'shadow'` | ACT 1. Black card (`cast.BLACK`), the eye is a hole. `color=` changes the card, `far=0.15` lightens the far legs. |
| | `'line'` | ACT 2. Graphite outline (`cast.GRAPHITE`), hidden lines removed, near-leg tops ghosted like underdrawing, grey bell, grey hooves. `seed=` redraws the hand tremor (change it 6 to 8 times a second for a boil), `wobble=0.9`, `width=2.3` px, `line=` colour, `paper=` fill colour inside her (pass `paper=None` for no fill), `grain=False` for a clean line. |
| | `'paper'` | ACT 3. Cream and brown cut paper with soft drop shadows, brass bell, pink udder. `pins=True` shows the brass brads. |
| `kind` | `'lead'` | THE cow. Her **left horn is crooked** (crumpled forward over the brow; the other stands up) and a **bell** hangs under her neck. Facing right, the crooked horn is the far one. |
| | `'herd'` | plain herd cow: two matching horns, no bell, tan with brown patches in paper. |
| | `'calf'` | short body, long thin legs, no horns, no bell, no udder. Drawn at 0.56 of a cow **at the same `s`**, so use one `s` for a whole herd. |
| `facing` | `1`, `-1` | looks right / left (a mirror). |

Units: `s` is pixels per cow unit. The lead is 141 units at the withers and about 250 nose to tail, so at
`s=0.8` she is 113 px tall and 200 px long. `(x, y)` is always **the ground under the middle of her barrel**.
Cost per cow at s=0.8: shadow 6 ms, line 28 ms, paper 85 ms.

## Drawing

### `place(ink, pose, x, y, s=1.0, facing=1, style='shadow', tilt=0.0, alpha=1.0, kind='lead', **opts)`
Draws the animal. `ink` is the kit's `Ink` or a PIL image. `tilt` (degrees) leans the whole puppet.
`opts`: `color, paper, line, width, pins, far, seed, wobble, grain`. Returns the **anchors** (screen px):

`muzzle, mouth, eye, horn` (tip of the good horn), `ear, poll, throat` (where the bell strap hangs), `bell,
withers, back, hook` (hip bone), `rump, seat, belly, tail_tip, tail_head, hand` (near fore hoof), `hand_far,
knee, hock, hooves` (`{'nf','ff','nh','fh'}`: near/far fore/hind), `violations` (joint limits that had to be
clamped; should be `[]`).

```python
a = cast.place(ink, cast.POSES['graze'], 300, 430, s=0.8, style='shadow')
grass_x, grass_y = a['muzzle']
```

### `walk_on(ink, x, ground, s=1.0, facing=1, style='shadow', lift=1.0, carry=0.0, phase=0.0, over=None, kind='lead', weight=1.0, **opts)`
Walks the animal. **You only move `x`.** `ground` is a function `px -> px` (or a number). The cycle phase
comes from `x`, so every hoof that is down stays on the same pixel of ground until it is picked up, on any
hill. Returns the anchors. `ink=None` returns anchors without drawing.

- speed: one cycle is `cast.cycle_px(s, kind)` px (76.8 px for the lead at s=0.8). A plodding cow takes
  about 1.4 s per cycle, so move her about `68 * s` px per second. Slower reads heavier.
- `phase` 0..1 offsets one animal from the next (give each herd member a different one).
- `carry=25` hangs the head: a tired cow. `lift` scales how high hooves are picked up. `weight` scales the
  sink and the nod.
- `over=dict(neck=-20, ear=30)` replaces pose keys after the walk is solved (look up while walking).

```python
hill = lambda px: 400 + 30 * math.sin(px / 180)
for i, ph in enumerate((0.0, 0.37, 0.71)):
    cast.walk_on(ink, 200 + 55 * t - 150 * i, hill, s=0.6, phase=ph, kind='lead' if i == 0 else 'herd')
cast.walk_on(ink, 120 + 55 * t, hill, s=0.6, kind='calf', phase=0.2)
```

What the walk does (the weight): a hoof lands with the leg straight out ahead (contact); with two legs of a
pair sharing the load the shoulders, then the hips, sink (down); she is carried up and over the single stiff
leg while the other swings through (pass, up). Withers travel 8.4 units, the muzzle 19. The head nods against
the stride (lowest when the shoulders are highest); the bell peaks a quarter beat after the head; udder and
tail later still.

### `footfalls(x0, x1, s=1.0, facing=1, phase=0.0, kind='lead')`
`[(x_of_her_middle_px, leg, hoof_x_px), ...]` for every hoof that lands while she walks `x0 -> x1` with
`walk_on`. For hoof sounds, dust, and wearing the path exactly where hooves fell.

```python
for xm, leg, hx in cast.footfalls(100, 700, s=0.8):
    t_hit = (xm - 100) / speed          # your own x(t) inverted
```

### `walk(dist, ground=None, lift=1.0, carry=0.0, stride=None, kind='lead', weight=1.0)`
The walk as a pose, in cow units (`dist` = units travelled; one cycle = `cast.STRIDE` = 96 for a cow).
Use it when you want to blend a walk into a pose: `cast.blend(cast.walk(d), cast.POSES['graze'], x)`.
Pass the same `kind` to `walk()` and to `place()`.

### `sprite(pose, s, facing, style, tilt, kind=..., **opts)` -> `(RGBA image, (ax, ay))`
The cutout itself; paste its top-left at `(x - ax, y - ay)`. For caching or post-processing.

### `anchors(pose, x, y, s, facing, tilt, kind)`
The anchors without drawing.

### `parts(pose, x, y, s, facing, tilt, kind)` -> `[(name, polygon_px), ...]` back to front
The cut pieces themselves (`tail, fh_upper, fh_lower, ff_upper, ff_lower, crump, barrel, hip, udder, nh_upper,
nh_lower, shoulder, neck, bell, jaw, head, horn, ear, nf_upper, nf_lower`). Same point count in every pose,
so pieces can be morphed or flown apart.

### `outline(pose, s=1.0, facing=1, n=240, tilt=0.0, kind='lead')` -> `n` points
Her whole silhouette as ONE closed line, evenly spaced, starting at the muzzle and running over the head and
back first, relative to her ground point. For the ACT 1 to ACT 2 hand-over and the line transformations: pair
it point for point with any other n-point contour and interpolate. About 0.2 s per call: cache it.

```python
pts = cast.outline(cast.POSES['stand'], 0.8, n=240)
ink.line([(x + px, y + py) for px, py in pts + pts[:1]], cast.GRAPHITE, 2)
```

## Poses

A pose is a dict. `cast.POSES[name]`:

| name | reads as |
|---|---|
| `stand` | neutral |
| `graze` | head down in the grass, one fore hoof forward |
| `look_up` | head up and level, ears forward: she has noticed something |
| `startle` | thrown back on the hocks, fore legs braced, head high, eye wide, tail up |
| `slump` | standing, spent: back sagged, head hung, ears down |
| `sit` | upright on a stool, both fore hooves on the desk |
| `desk_slump` | face down on the desk, fore legs slid out, eye shut |

Functions that return seated poses (all on the same stool and desk, so they blend without sliding):

| call | reads as |
|---|---|
| `draw_pose(u, reach=0.0, press=1.0)` | drawing. `u` 0..1 moves the pencil hoof across the sheet, `press` 0 lifts it, `reach` 0..1 leans in. Pencil point = `a['hand']`. |
| `hold_pose(u=1.0, judge=0.0)` | holds the drawing up in both hooves. `u` 0 = on the desk, 1 = up at her face. `judge` -1 = pulls back, eye narrowed, ear dropped (doubts it); +1 = face pushed in, eye wide (loves it). |
| `sheet_quad(a, s=1.0, facing=1, w=46.0, h=58.0, lean=0.12)` | the four corners `[bottom-near, bottom-far, top-far, top-near]` of the held sheet from `hold_pose` anchors, cheated a quarter turn to camera. Draw your drawing into it, after the cow. |
| `stamp_pose(u)` | approves her own work. 0 = hoof on desk, 0.5 = hoof raised overhead while the head goes down to aim, 1 = slammed. About 0.5 s up, 3 frames down. Stamp = `a['hand']`. |
| `drown_pose(u)` | going under paper. 0 = sitting, 0.6 = chin up, hooves off the desk, 1 = muzzle to the sky, one leg reaching up. You draw the paper: at u=1 fill to `cast.PAPER_LINE` (150 units above the floor). |

`stool_and_desk(ink, x, y, s=1.0, facing=1, style='shadow', color=None, line=None, paper=PAPER, width=2.0)`
draws the stool and desk for a seated cow at the same `(x, y, s, facing)`. **Draw it before the cow.** Returns
`{'top': (x0, x1, y), 'sheet': (cx, y), 'stool': (x, y)}`. Constants in cow units: `DESK_Y=-110`,
`DESK_X=(28, 140)`, `STOOL_Y=-47`, `STOOL_X=-52`.

```python
y, s = 470, 1.3
desk = cast.stool_and_desk(ink, 330, y, s, style='line')
a = cast.place(ink, cast.hold_pose(1.0, judge=-1), 330, y, s, style='line', seed=int(t * 8))
q = cast.sheet_quad(a, s)
ink.poly(q, fill=(250, 246, 236), color=cast.GRAPHITE, width=2)
```

### Pose keys (if you make your own with `with_`)
`dx, dy` (body shift, cow units, y down), `pitch` (-80..30), `shoulder` (-12..12), `hip` (-30..14), `neck`
(-65..82), `head` (-48..62), `jaw` (0..28, open), `ear` (-55..60, + pricks forward), `udder`, `bell` (-70..70),
`eye` (0 shut, 1 open, up to 2 = wide with the white showing), `tail` (three angles from hanging, + lifts to
the rear), and four legs `nf, ff, nh, fh`, each either `('ik', x, y)` = put the hoof at that point (cow units;
`y=0` is the ground) or `('fk', upper, knee)` = joint angles. **Positive always lowers the nose end**; leg
angles are from straight down, positive = hoof forward. The knee folds the hoof back only, the hock forward
only. Limits are in `cast.LIMITS` and are enforced (clamped, and reported in `violations`).

`with_(pose, **keys)` copies a pose with keys replaced: `cast.with_(cast.POSES['graze'], jaw=12, ear=20)`.

## Moving between poses

### `blend(p, q, x)`
The pose `x` of the way from `p` to `q`. Planted hooves stay planted; everything else turns on its pin.

### `tween(p, q, x, ease='inout')`
`blend` with a named ease. `cast.EASES`: `linear`; `inout` (gentle both ends); `out` (jumps off, settles: a
reaction); `slow` (heavy start); `slam` (hangs, then falls: the stamp coming down, a collapse); `snap`
(overshoots by a tenth and comes back); `anticip` (draws back first).

### `Act(keys, kind='lead', bell=True)` then `.pose(t)`
A performance on a timeline. `keys` are `(seconds, pose_or_name, ease_into_this_key='inout')`. A hold is the
same pose twice. The bell is simulated as a damped pendulum driven by how her throat moves, so it lags every
move and keeps swinging after she stops. `act.bell_hits` lists the times the clapper strikes (for the Mix).

```python
act = cast.Act([(0.0, 'graze'), (1.2, 'graze'), (1.5, 'look_up', 'snap'), (3.0, 'look_up'),
                (3.25, 'startle', 'out'), (4.0, 'startle'), (5.2, 'stand')])
a = cast.place(ink, act.pose(t), 300, 430, s=0.8)
for hit in act.bell_hits: mix.bell(hit, freq=1150, seconds=0.5, gain=0.08)

desk = cast.Act([(0.0, cast.draw_pose(0.2)), (0.6, cast.draw_pose(0.9, 0.5)), (1.0, cast.hold_pose(1, 0)),
                 (1.8, cast.hold_pose(1, -1), 'slow'), (2.4, cast.hold_pose(1, -1)), (2.6, cast.hold_pose(0)),
                 (3.1, cast.stamp_pose(0.5), 'slow'), (3.22, cast.stamp_pose(1.0), 'slam')])
```

(`stamp_pose` and `drown_pose` are curved inside, so for the smoothest result call them directly with your own
`u(t)` instead of keying only their ends.)

## Checks (MEASURED, by `cast.check()`, which raises on failure)
- contact drift of planted hooves over two cycles, all three kinds, flat and hill: 0.0 units.
- joint limits: no clamp needed in any of the 32 named poses, any blend between the standing poses, any walk frame.
- attachment: every limb pin lies inside the piece it hangs from in every pose and walk frame.
- walk bob (lead): withers 8.4, hip 2.8, muzzle 19 units.

## Honest limits
- JUDGED from stills only (pose sheets, 12-frame strip, onion skin): nobody has watched the walk or the Act in
  playback. The first scene render is the real test of weight and of the bell.
- Side view only. `facing=-1` is a mirror, so the crooked horn changes side with her.
- The calf and the herd cow cannot sit at the desk (the seated poses are cut for the lead).
- A raised hoof cannot go above her own horns when seated (reach 96 units from the shoulder); `stamp_pose`
  lowers the head instead.
- `drown_pose(1)` is a tangle by design; if it must read at small size, stop at about 0.7.
- The pencil style at `s` below about 0.35 is a small scribble; the shadow and paper styles read down to 0.18.
