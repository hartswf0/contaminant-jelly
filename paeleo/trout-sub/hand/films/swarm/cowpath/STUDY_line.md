# STUDY · the graft in one continuous pencil line (animation-07, Foldès)

    python3 films/swarm/cowpath/study_line.py                 -> assets/films/cowpath-study-line.mp4
    python3 films/swarm/cowpath/study_line.py --check         -> measured invariants and topology warnings
    python3 films/swarm/cowpath/study_line.py --sheet OUT.png [t ...]   -> contact sheet (16 stills by default)
    python3 films/swarm/cowpath/study_line.py --still OUT.png t [cx cy factor]
    python3 films/swarm/cowpath/study_line.py --keys OUT.png  -> the key drawing set

Deliverable: `assets/films/cowpath-study-line.mp4`, 960x540, 24 fps, 12.0 s, 288 frames, h264 + aac, 0.6 MB,
picture and sound, no text on screen. Importing `study_line` renders nothing.

## What the SCION asked for

animation-07: "progressive transformation of drawn forms as narrative consequence. Every in-between should
sustain shape identity long enough for the change to be felt." Its primitives must stay first-class in the
project (key contour drawings, point correspondences, in-between fields, transformation pacing, discontinuity
markers, intervention frames), with at least one invariant tested numerically and one achievement judged only
by viewing. Its bar: reads in grayscale; no unintended topological flips; key recognitions persist at planned
frames; hand-authored exceptions override visibly bad interpolation. Its hard proof (a diner growing into his
furniture) was turned to this film: a shoot cut from a twig, carried, set in a cleft in an old stump, bound,
bursting into leaf, as one continuous pencil line.

## What was built

One open polyline of **777 points in every frame**, running from one edge of the paper to the other. There is
never a second stroke and nothing fades: every change is the line moving.

| time | what the line does |
|---|---|
| 0.0 to 0.95 | twig with a two-bud shoot on top; from 0.35 it leans toward the old stump (the want) |
| 0.95 to 1.64 | it strains; the twig under the shoot is drawn out into a thin neck that shuts: the cut. The shoot's square foot becomes a wedge point |
| 1.64 to 2.06 | the neck snaps back to a stub with a slanted cut (a damped spring); the shoot's point runs down the stub and it falls flat |
| 2.06 to 4.30 | the ground dips under it, then swells into a wave that stands it up and carries it to the stump; it leans back against the travel |
| 4.30 to 5.36 | the wave breaks on the root and runs up the bark as a bulge; the shoot rides it, slows, teeters at the corner of the rim, slips back, heaves over |
| 5.36 to 6.58 | it slides to the mouth of the cleft, which is too tight; three pushes (5.90, 6.06, 6.22), the old wood gives a step at each; it drops home (6.44) and the cleft closes on the wedge (6.58) |
| 6.92 to 8.16 | three loops of the stump's own contour are thrown across the union, bottom to top, then drawn tight (the stump top narrows) |
| 8.16 to 9.20 | the wait: the shoot sags. Nothing else moves |
| 9.20 to 11.3 | the upper bud opens first (spear, pause, unfold), the shoot straightens past upright, then six more leaves, quicker; the stem grows; the split heals over so cleft and wedge stop being two things |
| 11.3 to 12.0 | hold: seven leaves on the old stump, the cut stub still standing |

How the continuity is kept: the shoot is a 403-point stretch spliced into a 372-point base contour at a
**fractional point index that slides** (`attach_index`). Being carried is that slide: the shoot keeps its own
point correspondence (the same 403 points from twig to leaf), and only its place in the base is re-made each
frame. So the shoot never leaves the line, and is never joined to it by a thread.

Direction: the key drawings have the twig on the right; `MIRROR = True` flips x so the shoot travels left to
right, as the board requires. Stump proportions are `sets.STUMP_PROFILE` (copied, not imported, because sets.py
was still being written), plus one broken limb on the far side.

### The primitives, as data

| primitive | in the code | what it holds |
|---|---|---|
| Key contour drawing | `KeyContour`, `BASE_KEYS` (WHOLE, PINCH, STUB, OPEN1, OPEN2, OPEN, GRIP, BOUND, TIGHT, HEALED), `SHOOT_KEYS` (ON_TWIG, CUT, SPEAR, LEAF) | one polyline cut into named runs with fixed counts (`BASE_SCHEMA`, `SHOOT_SCHEMA`) |
| Point correspondence | `Correspondence`, `correspond(a, b)`, `CORRESPONDENCES`, `pair_by_landmarks` | index map between two keys, with a `check()` that reports order kept and travel |
| In-between field | `InBetweenField`, `SHOOT_FIELD` | per point: its group (stem, leaf 1..7, wedge) and the point it is anchored to, so a leaf opens on its own clock while riding a stem that is growing |
| Transformation pacing | `Pacing`, `T`, `POSE`, `WEDGE`, `STEM`, `LEAF_AT`, `BASE_TRACK` | hand-keyed tracks, an easing on every key; one event table read by picture, sound and checks |
| Discontinuity marker | `DiscontinuityMarker`, `MARKERS` | nine planned moments (cut, land, crash, corner, seat, three bands, heal); fast travel is allowed inside them and nowhere else |
| Intervention frame | `InterventionFrame`, `INTERVENTIONS` | seven hand-authored exceptions, each naming the bad in-between it replaces and the function that applies it (`twig_bend`, `ground_wave`, `bark_bulge`, `throw_loop`, the extra keys PINCH and OPEN1/2, the POSE tracks) |

## Functions other agents can import

`import study_line as L` (the folder must be on `sys.path`, as in study_shadow.py).

| call | what it gives |
|---|---|
| `g = L.graft_line(6.6, x=742, y=468, s=6.4, mirror=True)` | THE LINE at study time 6.6 s as a `GraftFrame`: `g.pts` (777x2 screen px), `g.tag` (run name of every point), `g.shoot` (slice), `g.leaves[k]` (slices, k = 1..7), `g.attach` (wedge point on screen), `g.lean`. (x, y) = ground under the middle of the stump |
| `L.draw_graft(ink, t, x=742, y=468, s=6.4)` | draws that line on a `kit.Ink` and returns the `GraftFrame` |
| `L.draw_line(ink, pts, heavy=slice(10, 60), width=2.3, heavy_width=3.1, waver=0.55, strength=1.0)` | any polyline as pencil: graphite over a fixed paper tooth, a fainter first pass, slow pressure along the line, wavering with the film's boil |
| `L.leaf_contours(12.0, 742, 468, 6.4)` | the seven leaves as seven 49-point contours, point 0 = stem end, point 24 = tip (the hand-over convention of sets.leaf_contour) |
| `L.leaf_run((0, 0), angle=-52, length=12.5, half_w=2.5)` | one leaf as an out-and-back run of a line |
| `A, B = L.pair_by_landmarks(line_a, line_b, [0, 40, 99], [0, 12, 57], [60, 60])` | two unrelated polylines put into point correspondence through shared landmarks (for example the paved path and the first pencil line) |
| `K = L.KeyContour.from_runs('MINE', [('a', 20), ('b', 30)], {'a': [...], 'b': [...]})` | a key drawing from named stretches |
| `c = L.correspond(K1, K2); c.check()` | the pairing of two keys with the same schema, and its measured facts |
| `f = L.InBetweenField(group, anchor); P = f.between(A, B, {0: 0.4, 3: 1.1})` | in-between two keys with a separate progress per group; progress past 1 overshoots |
| `L.Pacing('lean', [(0, 0), (0.8, -3, 'smooth'), (1.6, -6, 'in')]).at(1.2)` | a keyed track; eases: lin, smooth, in, out, hold, over |
| `L.throw_loop(run, 0.5)` | a closed loop of line half thrown across what it binds |
| `L.base_key('X', top='stub', hw=1.4, dp=6.5, bands=True, squeeze=1.0, split=0.0)` | a key drawing of ground, stump, cleft, twig |
| `L.shoot_key('Y', stage='spear', wedge=True)` | a key drawing of the shoot: 'bare', 'spear' or 'leaf' |
| `L.base_at(4.6)`, `L.shoot_local(10.0)`, `L.shoot_pose(4.6)`, `L.attach_index(4.6)` | the parts of the line at a time, in stump units |
| `L.sound(mix, t0=65.5, gain=1.0)` | the study's sound laid into a `kit.Mix` from t0 |
| `L.line_speed()` | mean travel of the line per frame (the pencil rasp follows it) |
| `L.crossings(pts)`, `L.classify(g)` | self-intersections of a polyline; topology warnings for a frame |
| `ok, lines = L.check(verbose=False)` | every measured invariant |
| `L.still(6.6, zoom=(740, 300, 2.0))`, `L.sheet('out.png', [1.0, 2.0])`, `L.key_sheet('keys.png')` | frames for looking at |

## Evidence

**MEASURED** (`--check`, final revision, all pass):
- 12 correspondences (9 base key pairs, 3 shoot key pairs), point order kept in each.
- 777 points in every one of 289 sampled times; longest single segment 5.34 units (no hidden thread).
- Outside the discontinuity markers no base point travels more than 1.57 units in one frame (limit 1.6).
- Shoot identity from the cut to the wait: similarity residual against key CUT 0.0000 units (squash and lean
  are in the pose, not the shape). Through the wilt 0.44 units. Wedge point unchanged from cut to heal.
- Seven leaves, 49 points each, tip at point 24, 9.5 to 12.5 units long.
- Topology: 0 unplanned crossings in 145 frames. Planned and counted separately: binding over the stump and
  shoot (up to 18), wedge against wood at the cut, the seat and the heal (up to 3).
- File: 12.000 s, 288 frames, 960x540, 24 fps, aac stereo. Sound levels by ffmpeg astats: peak -2.9 dB,
  overall RMS -31.7 dB, the wait (8.3 to 9.1) -42.8 dB against -34.9 dB for the leafing (9.2 to 11.2).

**STRUCTURAL**: one polyline by construction; picture, sound and checks read the same event table `T`.

**JUDGED, from stills only, by the builder**: four rounds of contact sheets (16 stills each) plus zoomed dense
sheets of the cut, the climb, the seat and the leafing, and one 16-still sheet pulled from the encoded mp4.
- Round 1: mechanism worked but everything was small, the buds crossed the stem, and the shoot travelled
  right to left. Fixed: scale 5 to 6.4, flipped, buds given a flat stem side, root and rim made uneven.
- Round 2: the check found the binding drew a chord across the stump, the bark bulge crossed the ground, the
  shoot was buried 12 units deep with its buds inside the stump, and the wedge cut through the rim on its way
  in. Fixed: loops thrown rather than paid out, bulge pinned at the root, cleft 6.5 deep, entry re-staged as
  three pushes at the mouth with the cleft opening a step at each.
- Round 3: the cut was three near-identical frames and did not read. Fixed: the twig is drawn out into a neck
  over 0.7 s, shuts, and snaps back. Landing moved clear of the stub, wilt made deeper, pencil pressure added.
- Round 4: sheet from the final render looked at; no further change.

**UNKNOWN / NOT DONE**:
- **Nobody watched it play.** Every judgement of acting and timing above is from stills and frame times.
- **Nobody heard it.** The sound is placed from the event table and checked only by level.
- **No independent critic has seen it.** The builder cannot award the pass (SCION law 9); this is a candidate.
- Foldès' Hunger was not inspected by anyone here; the bar used is the SCION's four conditions.
- The grayscale condition was not tested separately: the picture is graphite on cream and has no hue to lose.

## What is weak

1. **Nobody carries it.** The ground does. With no cow and no hand, "cut and carried" may read as "it broke
   off and surfed". The board's 2.6 has her cut and set it herself; this study proves the line method, not
   that staging.
2. **The cut has no blade.** A neck drawn thin and snapping reads as torn or pinched off, not cut.
3. **The fall slides down the stub** (the wedge point must stay on the line), so it looks more like slipping
   down a pole than dropping.
4. **The stump is plain.** One contour cannot hold rings, bark or hatching; `sets.stump_lines` has them as
   extra strokes, which would break the one-line rule. At 6.4 px per unit it is recognisably a stump with a
   split and a broken limb, no more.
5. **The binding reads as barrel hoops.** Each turn is a full flat loop, so the far side shows through. It is
   also thrown from the stump's own side, not wound from the path line as the board plans.
6. **The heal is small.** The split closing under the bands is a few pixels and may not be noticed.
7. **The wait is 1.0 s** (board 2.7 asks for 36 frames of nothing). The sag is the only acting in it.
8. **The leaves are much alike**, and the top three sit close together.
9. **The line is drawn with PIL lines at 2x**, softened and broken by a paper tooth. It is a fair pencil at
   playback size and looks like a fibre-tip when enlarged.
10. **Differences from sets.py to settle before act 2 is built:** the shoot here is 403 points (sets: 73) and
    grows from a twig, not from her pencil stub; the cleft is 6.5 units deep (sets: 12); timings are the
    study's 12 s, not the board's 65.5 to 74.5.
