# SETS.md · the sets of "Don't Pave the Cow Paths"

`films/swarm/cowpath/sets.py`. Three kits, one per material. Everything is drawn from code onto the kit's
`Ink`; nothing is foraged. No function keeps state: same arguments, same picture.

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))      # films/swarm/cowpath
    import sets

`python3 films/swarm/cowpath/sets.py` writes 26 stills to `films/stills/cowpath_sets/` (6 s).

**What was checked, and how.** JUDGED on stills only (I looked at every still, fixed, re-rendered three times):
no playback was rendered, so nothing here is claimed about how the motion reads. MEASURED: the smooth path
passes through all 21 board points (0.0 px off), crosses itself exactly once (the loop), is 981 px long;
`STUMP_PROFILE` is 46 wide; seven leaf sites; the shoot contour has the same 73 points as a pencil stub and
as a shoot; cost per frame is about 130 ms for the full act 1 stage with town and roller, 55 ms for the desk
set, 46 ms for the graft. UNKNOWN: how the tissue fibre and the pencil boil behave after x264 at crf 28.

Units are screen pixels at 960x540, y down, angles in degrees. `t` is film time (things that move by
themselves); a 0..1 argument is something done to the piece.

---

## ACT 1 · the shadow stage (amber backlight, tissue, black card)

The hill is a sheet of tissue facing us. Worn places let the lamp through; paving is black card over them.

### Constants

| name | value | what |
|---|---|---|
| `PATH_PTS` | 21 points | the board's control points, unchanged |
| `PATH` | 201 points | **the canonical crooked path** (Catmull-Rom through `PATH_PTS`): sag under the tree, bulge over the boulder, the loop by the bog |
| `PATH_LEN` | 981 | its length in px |
| `STRAIGHT` | `[(120,170),(840,455)]` | where she first aimed |
| `TREE` `BOULDER` `BOG` | (331,253) (500,329) (718,409) | tree foot, boulder middle, bog middle |
| `CREST` `WATER_EDGE` `FAR_GRASS` | (120,170) (840,455) (936,452) | path ends; root of the tall grass on the far bank |
| `LAMP` | (604,84) | where the lamp (the sun) stands when fully up |
| `STUMP_PROFILE`, `STUMP_H`, `STUMP_CUT` | 12 points, 22, 2 points | the stump's contour at s=1, origin on the ground under its middle: 46 wide, one flat cut, two root flares. Act 2 draws the same list (`stump_lines`) |
| `TOWN` | 13 dicts | house sites `{x, y, s, kind, u, side, facing}` from the crest down; `CHURCH` is the 14th building |
| `RIDGE`, `FAR1`, `FAR2`, `NEAR_BANK`, `FAR_BANK`, `FOOT` | polylines | the cut edges of the sheets |
| `BLACK`, `GRAPHITE`, `LIGHT` | colours | card, pencil, bare light |

### Path helpers

    x, y, heading = sets.path_at(0.5)            # point and heading (deg, + = downhill) at half way
    u = sets.path_u(cow_x, cow_y)                # nearest fraction of the path to a point
    st = sets.path_stroke()                      # the path as a pencil Stroke: act 2's first line
    y = sets.ridge_y(400)                        # the hill's top edge at x

### The whole stage, in order

    a = sets.stage_back(ink, t, lamp=1.0, lamp_xy=sets.LAMP, worn=0.6, wear=1.0, prints=[], paved=0.0,
                        tree_fall=0.0, boulder_broken=0.0, bog_fill=0.0)
    sets.town(ink, t, grow=0.4)                  # then your cows (cast.place / cast.walk_on)
    sets.stage_front(ink, t)                     # the black foot of the hill, lower left (title is cut through it)
    sets.handover(ink, u)                        # only for 34.0 to 36.0

`stage_back` arguments: `lamp` 0..1 (0 = black), `lamp_xy` (bring it up from about y=330 to `LAMP`),
`white` 0..1 (screen whitens to cream), `worn` 0..1 how far down the path the wear has reached, `wear` 0..1
how thin it is worn (0.35 a faint track, 1 the bright cut), `worn_width` (9), `prints` hoof prints
`[(x, y[, heading]), ...]` (take them from `cast.footfalls`), `paved` 0..1 how far the setts have been laid,
`tree_fall` 0 standing .. 1 lying, `None` = only the stump, `tree_carry=(dx, dy)`, `boulder_broken` 0 .. 1,
`None` = gone, `bog_fill` 0 .. 1, `calm` 0..1 stills the water. Returns the tree's anchors.

### Pieces (each can be called by itself)

| call | what it draws |
|---|---|
| `sets.backlight(ink, t, lamp=1.0, lamp_xy=sets.LAMP, white=0.0)` | sky: the lit screen with the lamp showing as a pale disc. `sets.backlight_array(...)` is the same as a float array |
| `sets.hills(ink, t, lamp=1, worn=0.5, wear=1, worn_width=9, prints=[(300,250,40)], bog=1, sheets=1)` | backlight + two far hill planes + far bank + THE hill with its wear and the bog's dark patch; water left bare and bright. `sheets` toward 0 thins every sheet away |
| `sets.worn_mask(worn=1.0, width=9, prints=())` | the wear as a 0..1 array (if you need to light something through it) |
| `sets.water(ink, t, calm=0.0)` | ripples sliding down the strip, a ring where the path meets it, reeds on the near bank, the tall grass on the far bank swaying with `t` |
| `sets.paved_path(ink, paved=0.6, width=9, kerb=1, joints=1, color=sets.BLACK)` | black band to fraction `paved`, a hair of light on each kerb, setts in bond. Returns the end point (put the roller there) |
| `sets.tree(ink, t, fall=0.0, x=331, y=253, s=1, carry=(0,0))` | the tree, light through gaps in its crown, pinned at the cut; `fall` 1 = lying 112 degrees over to the right. Returns `{'top','tip','cut'}` |
| `sets.stump(ink, x=331, y=253, s=1)` | the stump alone |
| `sets.boulder(ink, x=500, y=329, s=1, broken=0.0)` | the boulder with one crack; `broken` slumps it into three pieces |
| `sets.bog(ink, t, fill=0.0)` | the bog's sliver of standing water and its reeds |
| `sets.foreground(ink, t)` | black card foot of the hill with grass |
| `sets.house(ink, x, y, s=1, rise=1, roof=1, kind='cottage', lit=0, facing=1)` | one house, base centre at (x, y). `rise` tips the wall up; `roof` 0..0.4 two flaps stand up out of the wall, 0.4..1 they fold in to the ridge, chimney pops last. kinds: `cottage`, `tall`, `long`, `barn`. `lit` puts lamplight in the windows |
| `sets.spire(ink, x, y, s=1, rise=1, roof=1, lit=0)` | the church; the spire telescopes up with `roof` |
| `sets.town(ink, t, grow=0.5, lit=0.0)` | all 13 houses then the church, unfolding in order from the crest. `grow` is 0..1 for the row, or a list of 14 values to time each one (0..0.5 wall, 0.5..1 roof). Returns the sites with `ridge` |
| `sets.fence(ink, u0=0.20, u1=0.30, side=-1, offset=10, post=1.0, rail=1.0, posts=4)` | a fence along the path's edge, default round the stump on the side of the straight way. `post` pushes posts up one after another, `rail` runs the rails out |
| `sets.steam_roller(ink, x, y, s=0.5, t=t, roll=sets.PATH_LEN*u, tilt=heading, smoke=1)` | the steam roller on pins: spoked rear wheel, front roll, flywheel and crank all turn by `roll` (px travelled), puffs of grey tissue from the chimney. Returns `{'front','rear','chimney','seat'}` |
| `sets.hand_roller(ink, x, y, s=1, roll=px, tilt=heading, handle=38)` | drum and T handle; returns `{'grip'}` |
| `sets.cart(ink, x, y, s=1, roll=px, tilt=0, tip=0.0, load=1.0)` | two-wheel tip cart; `tip` sheds the `load`. Returns `{'shaft','tail'}` |
| `sets.handover(ink, u)` | call LAST. 0..0.45 everything sinks to black, only the kerb hairs show the band; 0.45..1 the black whitens to cream, the band thins 9 px to 3 px and turns graphite. At 1 the frame equals `paper_ground` + `pencil(path_stroke())` |
| `sets.Card()` | scissors for your own black card: `.poly(pts)`, `.disc(c, r)`, `.line(pts, width)`, `.hole(pts)`, `.hole_disc(c, r)`, then `.paste(ink, alpha)` |

Paving with the roller on the path:

    u = ramp(t, 27.5, 33.0)
    x, y, hd = sets.path_at(u)
    sets.stage_back(ink, t, worn=1, paved=u, tree_fall=None, boulder_broken=None, bog_fill=1)
    sets.town(ink, t, 1.0, lit=0.6)
    sets.steam_roller(ink, x, y, 0.5, t, roll=sets.PATH_LEN * u, tilt=hd)

Staging notes. Downhill houses keep their roofs 12 px under the path. Uphill houses stand on the brow of
the hill against the sky, 66 to 90 px above the path, because a cow at `s=0.55` is about 80 px tall and
swallowed anything nearer (seen in `check_a1_with_cows.png`); on the bulge her back still meets their
doorsteps. Houses are always on the outside of a detour, so nothing stands on `STRAIGHT`. The board asks
for a hand roller and a barrow; the contract asked for a steam roller: both `steam_roller` and
`hand_roller` exist, and `cart` serves as the barrow.

---

## ACT 2 · the desk (pencil line on cream paper)

Every piece is a **list of `Stroke`s**: a `Stroke` is a plain list of `(x, y)` with `.w` (weight), `.tone`
(darkness) and `.fill` (a closed shape that hides what is behind it). Concatenate lists and draw them with
`pencil`; they can be drawn on, morphed and transformed.

### Line tools

| call | what |
|---|---|
| `sets.pencil(ink, lines, progress=1.0, width=1.7, alpha=1, boil=6, wob=0.7, seed=0)` | THE renderer. `progress` 0..1 draws the list ON in order by length; returns where the pencil point is. `boil` = redraws per second |
| `sets.paper_ground(ink, t, warm=0.0)` | the cream sheet (call first) |
| `sets.Stroke(pts, w=1, tone=1, fill=False)` | make a stroke |
| `sets.resample(pts, n)`, `sets.upto(pts, u)`, `sets.polylen(pts)` | n even points; the first fraction; length |
| `sets.morph(a, b, u, n=None)` | one polyline into another, point for point |
| `sets.morph_lines(A, B, u, n=64)` | two lists, stroke for stroke |
| `sets.transform(lines, dx=0, dy=0, s=1, angle=0, about=(0,0))` | scale, turn, shift a stroke or a list |
| `sets.hatch(poly, gap=5, angle=45, w=0.55, tone=0.5)` | pencil hatching inside a polygon, as strokes |
| `sets.catmull(pts, per=12)` | smooth curve through points |

### The set for a seated cow

    cast.place(...) uses (x, y, s) = (300, 470, 1.0); the desk is built round the same numbers:

    sets.paper_ground(ink, t)
    A = sets.desk_set(ink, 300, 470, 1.0, t=t, progress=1.0, pile=22, blanks=12, hours=10.4,
                      stamp_at=None, stamp_lift=0, stamp_squash=0, pull=0.0, brush=True,
                      lamp_on=1.0, lamp_reach=0.0, mess=0.5)
    sets.pencil(ink, sets.on_sheet(A['sheet'], sets.path_stroke()), width=1.0)    # the path line on her paper
    cast.place(ink, cast.draw_pose(0.6, 0.5, 1.0), 300, 470, s=1.0, style='line') # the cow, after the set

`desk_set` draws floor, stool, desk, lamp, pot, board, sheet, peg bar, camera lever, ink pad, stamp, blank
paper, out-tray (on the floor to the right, with `pile` sheets) and clock, with one `pencil` call, and returns
`desk_layout` plus `'tip'`. `sets.desk_set_lines(...)` gives the same strokes without drawing them.
Do not also call `cast.stool_and_desk`: this desk's front edge is where cast puts its desk top (cow x + 28 s,
110 s above her floor), so her hooves land on it, and `stool_lines` is cast's stool.

`sets.desk_layout(x, y, s)` returns screen points: `desk` (floor under the desk's near left corner),
`board`, `sheet` (4 corners), `top_y`, `floor`, `pot`, `lever`, `pad`, `stamp` (touch-down on the pad),
`mark` (touch-down on the sheet for her hoofprint), `lamp`, `blank`, `out_tray`, `stack`, `clock`, `right`.

### Pieces

| call (A = `sets.desk_layout(300, 470, 1.0)`) | what |
|---|---|
| `sets.desk_lines(*A['desk'], s)` | the desk, three-quarter view: top, apron, drawer, four legs, stretchers, shadow hatching |
| `sets.floor_lines(*A['desk'], s)` | broken floor line and the cast shadow under the desk |
| `sets.stool_lines(300, 470, s)` | the stool, placed by the COW's x, y |
| `sets.board_lines(*A['board'], s)` | the tilted drawing board with the disc window |
| `sets.sheet_lines(*A['board'], s, lift=0.0)` | the sheet on the pegs, three punched holes; `lift` curls its far edge up (flipping) |
| `sets.sheet_quad(*A['board'], s)` / `sets.on_sheet(quad, pts, box=(0,0,960,540))` | the sheet's corners / lay a drawing made in `box` onto it |
| `sets.pegbar_lines(*A['board'], s)` | peg bar: round peg between two flat ones (draw after the sheet) |
| `sets.lamp_lines(*A['lamp'], s, t, reach=0.0, on=1.0, nod=0.0)` | sprung desk lamp; `reach` folds the arms, `nod` tips the shade, `on` draws rays. `sets.lamp_anchor(...)` gives joints and mouth |
| `sets.stack_lines(*A['stack'], s, n=40, mess=0.3, lean=0.0, th=2.2)` | **the pile that grows**: `n` sheets (a float; 50 = desk height, 125 = over her head), each a closed filled stroke. `mess` 0 squared .. 1 thrown; `lean` drifts it over |
| `sets.stack_top(*A['stack'], s, n=40)` | middle of the top sheet (where the next one lands) |
| `sets.stack_contour(*A['stack'], s, n=110, pts=120, mess=1.0)` | the pile's outer edge as ONE 120-point polyline: the heap that settles into `ground_with_stump` |
| `sets.tray_lines(*A['out_tray'], s, n=6)` | a paper tray with a thumb notch and `n` sheets (use it for in-tray and out-tray) |
| `sets.stamp_lines(x, y, s, lift=0, tilt=0, squash=0)` | the rubber stamp; (x, y) = where the die touches down |
| `sets.pad_lines(*A['pad'], s, open_=1.0)` | the ink pad, lid hinged open |
| `sets.hoofprint_lines(x, y, s=0.55, angle=20, ink_=1.0)` | her approval mark: a cloven print, hatched dark |
| `sets.clock_lines(*A['clock'], s, hours=9.5, t=t)` | wall clock; run `hours` fast to make time go; the pendulum swings with `t` |
| `sets.pot_lines(*A['pot'], s, brush=True)` | paint pot, brush standing in it (`brush=False` when it is in her mouth) |
| `sets.brush_lines(x, y, s, angle=0)` | a loose brush, bristle tip at (x, y) |
| `sets.lever_lines(*A['lever'], s, pull=0.0)` | the camera: post, shutter box whose eye shuts at the bottom of the pull, lever. `sets.lever_anchor(...)['grip']` is where her hooves go |

Drawing the set on, and the pile climbing:

    sets.desk_set(ink, 300, 470, 1.0, t, progress=ramp(t, 37.5, 39.0))
    sets.pencil(ink, sets.stack_lines(*A['stack'], 1.0, n=lerp(50, 128, ramp(t, 61.0, 64.6)), mess=1.0, lean=0.12))

---

## THE ORCHARD · the graft (pencil)

    A = sets.graft_set(ink, 480, 470, s=5.0, t=t, cleft=1, shoot=1, knuckle=1, buds=1, set_=1, wound=1, leaves=1)

(x, y) = the ground under the middle of the stump. `cleft` 0..1 the split opens; `shoot` 0 = none, else its
growth from pencil stub (just above 0) to shoot (1); `knuckle` 0 straight pencil .. 1 knuckled shoot; `buds`
0..1; `set_` 0 = wedge held 40 units above the cleft, 1 = home (the cleft grips it); `wound` 0..1 the binding
goes on, three turns; `leaves` 0..1 the seven leaves open in order, upper bud first. Returns
`{'cleft','rim','cut','bind','wedge','sites'}`. `sets.graft_lines(...)` gives the strokes.

| call | what |
|---|---|
| `sets.stump_lines(x, y, s=4, cleft=0.0, grip=0.0)` | the old rootstock: `STUMP_PROFILE` (first stroke) plus cut rim, rings, bark, roots, grass. `grip` closes the cleft on the wedge |
| `sets.stump_anchor(x, y, s, cleft=1)` | `cleft` (where the wedge point goes), `rim`, `cut`, `bind` |
| `sets.ground_with_stump(x, y, s=4, slope=0.05, pts=120)` | ONE 120-point polyline: ground, up and over the stump, ground. The target of the heap: `sets.morph(sets.stack_contour(...), sets.ground_with_stump(...), u, 120)` |
| `sets.knife_lines(x, y, s=2, angle=14)` | the grafting knife, (x, y) = blade point |
| `sets.shaving_lines(x, y, s=2, curl=1.0)` | the one shaving that curls off the cut |
| `sets.shoot_lines(x, y, s=4, angle=-82, grow=1, knuckle=1, buds=1)` | the scion. (x, y) = **the wedge point, which never moves: it is the pencil point**. `grow=0, knuckle=0, buds=0` IS her pencil stub. The first stroke is a 73-point closed contour at every setting |
| `sets.shoot_anchor(x, y, s, angle, grow, knuckle)` | `wedge`, `neck`, `tip`, `buds` |
| `sets.binding_path(x, y, s=4, turns=3, n=120)` | the binding as ONE 120-point helix with a tail: what the crooked path line winds into, `sets.morph(sets.path_stroke(), sets.binding_path(...), u, 120)` |
| `sets.binding_lines(x, y, s=4, wound=0.6)` | the binding as seen: the near half of each turn as a filled band, then tail and knot |
| `sets.leaf_contour(x, y, s=4, angle=-60, open_=1, n=48, curl=0)` | one leaf as one closed contour of 49 points. **Point 0 is the stem end, point 24 the tip**: stem becomes tail, tip becomes nose in the hand-over to act 3 |
| `sets.leaf_lines(x, y, s=4, angle=-60, open_=0.7, curl=0.2)` | the contour plus midrib and veins; `open_` 0 = a shut sliver just out of the bud |
| `sets.leaf_sites(x, y, s, angle, grow=1, knuckle=1)` | the SEVEN leaves of the shoot at wedge point (x, y): `[{x, y, angle, length, width, order}]` |

The pencil becoming the shoot (wedge fixed):

    wedge = A['cleft']
    sets.pencil(ink, sets.shoot_lines(*wedge, 5.0, grow=g, knuckle=g, buds=clamp(g * 1.5 - 0.5)))

---

## Stills (films/stills/cowpath_sets/)

`a1_01` bare hill · `a1_02` lamp rising · `a1_03` prints · `a1_04` worn · `a1_05` town growing, tree falling ·
`a1_06` town and fence · `a1_07` paving with the roller · `a1_08` paved · `a1_09_handover_0..3` ·
`a1_10` machines · `a1_11` houses, spire, tree, boulder · `a2_01` desk · `a2_02` desk drawing on ·
`a2_03` desk busy (path on the sheet, hoofprint, pile) · `a2_04` pile over her head with its contour in red ·
`a2_05` stamp, pad, hoofprints, clock, pot, brush, lever, trays · `a2_06` lamp and board · `or_01` graft stages,
pencil to shoot, knife, shaving, leaf opening · `or_02` heap contour settling into ground and stump ·
`or_03` the graft in leaf · `check_a1_with_cows`, `check_a2_with_cow` (with `cast.py` as it stood when rendered).

## Known limits

- Stills only; no motion of any piece has been watched.
- Uphill houses meet the backs of cows walking the bulge of the path (see staging notes).
- The far grass is partly cut by the right edge of the frame.
- The hill is the board's tissue sheet with the path across its face, not a hill whose skyline is the path:
  the path has a closed loop, which a skyline cannot have.
- `handover` cross-fades the 3 px card band into the pencil stroke over its last quarter: the two are the same
  polyline (`PATH`), but the pencil's tooth appears during that fade.
- A stroke's paper fill arrives as its own contour is drawn, so during a draw-on a shape hides what is behind it
  slightly before it is complete.
