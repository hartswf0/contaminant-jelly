# STUDY: shadow theatre (animation-02), the moment a cow path is made

`films/swarm/cowpath/study_shadow.py` renders `assets/films/cowpath-study-shadow.mp4`
(12.0 s, 960x540, 24 fps, on 2s = 12 drawings a second, h264 + aac, 0.5 MB, no text on screen).
The kit also writes a poster, `assets/films/cowpath-study-shadow.webp`.

    python3 films/swarm/cowpath/study_shadow.py                 # the film
    python3 films/swarm/cowpath/study_shadow.py --check         # the measured invariants
    python3 films/swarm/cowpath/study_shadow.py --sheet OUT.png [--bw] [t0 t1]   # 16 stills on one sheet
    python3 films/swarm/cowpath/study_shadow.py --xsheet        # the exposure sheet as text

## What the SCION asked for

animation-02 (articulated shadow theatre): make emotional action legible through contour, positive and
negative space and precisely limited articulation; never rescue weak action with internal texture. Keep
as first-class data: backlit shapes, pinned joints, joint-angle limits, foreground/midground shadows,
replacement profiles, contact planes, exposure sheets. Hard proof: a small figure at a gate hesitates,
offers to another, then chooses; in silhouette at 12 fps, with purposeful sound. Bar: limbs do not detach,
shadows do not merge into blobs, the point of support stays stable, relationships read with all colour
removed. At least one numeric invariant and one judged-by-viewing achievement. An independent critic.

## What was built (the hard proof, turned to this film)

One shot, no camera move. The lead (crooked horn, bell) comes along the old cart track on the crest to a
five-bar gate. Beats, with the drawing numbers of the sheet (12 a second):

| drawings | beat |
|---|---|
| 0-13 | walks in, head coming up; halts by stepping, head out over the top bar |
| 13-17 | **hold**: she wants the far side (pale hill and trees beyond) |
| 17-28 | puts a fore hoof on the second bar; the leaf sags on its pins; she tests it; takes the hoof off |
| 28-34 | leans her chest in; the gate swings to its chain (12 degrees) and stops; she shoves again |
| 34-40 | the gate springs back; she is thrown up and back and takes a pace back |
| 41-50 | turns her head back over her shoulder (replacement profile) and calls |
| 50-66 | **hold**: she waits. The calf lifts its head, answers, trots up, stops under her flank |
| 66-76 | head front; once more over the gate (hold); then her nose goes down along the foot of the fence |
| 76-81 | **hold**: the choice |
| 81-144 | she steps off and goes round the end post; the calf follows; two herd cows, who never try the gate, follow |

Behind every hoof on the detour the amber tissue of the hill wears thin and light comes through: by the last
drawing there is a bright bent track round the end of the fence with four animals strung along it.

The stage is planes: lit screen, a pale far hill (`far`), the fence and gate in brown card (`mid`), the
animals in black (`actor`), black grass at the bottom (`fore`). The floor is drawn oblique (one unit toward
us = 1 px right, 0.32 px down), so "round the near end of the fence" is a dip in the walked line.

### The SCION's primitives, as data in the code

| primitive | in `study_shadow.py` |
|---|---|
| Backlit character shapes | `BacklitShape(name, plane, depth, polys, strokes)`; the fence is 8 of them (`gate_shapes`). The cow's cut pieces are `cast.parts`. |
| Pinned joints | `PinnedJoint(name, pin, limit, value, hits)`; the gate has two: `gate_hinge`, `gate_sag`. The cow's pins are cast.py's. |
| Joint-angle limits | `JointLimit(lo, hi)`: `GATE_SWING = (-4, 12)` degrees, `GATE_SAG = (0, 3)` px; cow limits are `cast.LIMITS`. The hinge's `hits` list (when it reached a stop) is what places the gate's clack in the sound. |
| Foreground/midground shadows | `ShadowPlane(name, order, tone, soft)`, `PLANES` = far, mid, actor, fore. |
| Replacement profiles | `ReplacementProfile(name, turn, pieces, drop)`, `PROFILES` = front, toward, back: the head pieces re-set about the poll. |
| Contact planes | `ContactPlane`: floor <-> screen, the walked line `y(x)`, and every footfall kept (`prints`) to wear the tissue. |
| Exposure sheets | `ExposureSheet` `X`: 24 fps on 2s, levels lead / calf / herd / gate, named cells with holds. All timing in the performance and the sound is read from it (`X.at`, `_tk`). |

## Functions other agents can import

```python
import sys; sys.path.insert(0, 'films/swarm/cowpath')
import study_shadow as ss, cast
```

Stage
- `ss.backlit_stage(size=(960, 540), lamp=(0.66, 0.40))` -> RGB image: the lit amber screen with the far plane.
  `img = ss.backlit_stage()`
- `ss.lay_tissue(stage, wear=None)` -> RGB: the hill as tissue over the light, thinned where `wear` (float HxW, 0..1) is high.
  `img = ss.lay_tissue(ss.backlit_stage(), floor.wear(t))`
- `ss.ridge(x)` -> screen y of the crest. `ss.tissue_mask()` -> the two tissue sheets as float arrays.
- `ss.foreground(img)`: black grass and thistles on the nearest plane, drawn onto `img`.
- `ss.draw_shape(img, shape)`: paste one `BacklitShape`, antialiased, in its plane's tone.

Gate
- `ss.gate_shapes(swing=0.0, sag=0.0)` -> list of `BacklitShape` (hinge post, leaf in two halves, latch post, stub rails and posts).
  `for sh in ss.gate_shapes(swing=8.0): ss.draw_shape(img, sh)`
- `ss.new_gate()` -> `{'hinge': PinnedJoint, 'sag': PinnedJoint}`; `g['hinge'].set(14.0, when=2.5)` returns 12.0 and records `(2.5, 'hi')`.
- `ss.gate_point(a, h, swing, sag)` -> screen px of a point on the leaf; `ss.gate_bar_x(h, swing)` -> where the leaf crosses the path.

Puppets (all on top of cast.py, at this study's scale `ss.S = 0.56`)
- `ss.place_cow(img, pose, x, y, kind='lead', profile='front')` -> anchors (+ `'mask_box'`). `profile='back'` is the head turned over the shoulder.
  `a = ss.place_cow(img, ss.CALL, 316, 380, 'lead', 'back')`
- `ss.cut_cow(pose, kind, profile)` -> `(RGBA, (ax, ay), eye)`: the card itself.
- `ss.step_blend(p, q, u, order=('nh','nf','fh','ff'), lift=13)` -> pose: from p to q with the hooves **stepping**, one leg at a time, not sliding. For halting out of a walk, a pace back, stepping off.
  `pose = ss.step_blend(walk_pose, cast.POSES['look_up'], u)`
- `ss.shift_pose(p, units)` -> the same picture held from a point `units` further back (to change where a puppet is held without a jump).
- `ss.walk_pose(kind, x, ground, phase=0, stride_k=1.0, lift=1, carry=0, weight=1, over=None)` -> `(pose, y)`: cast's walk with a stride that can be lengthened (`stride_k=1.5` for the calf: fewer, longer steps).
  `pose, y = ss.walk_pose('calf', x, floor.y, phase=0.2, stride_k=1.5)`
- `ss.reach_fix(pose, kind)` -> pose: sinks the body until every planted hoof is within the leg's length (needed on any ground steeper than about 1 in 6; without it cast clamps the leg and the hoof leaves its mark).
- `ss.footfalls(kind, x0, x1, phase=0, stride_k=1.0)` -> `[(x_of_middle_at_landing, leg, hoof_x)]` matching `walk_pose`.
- `ss.travel(t, t0, x0, [(until, speed), ...])` -> x: a walker's position with eased speed changes.
- Lead poses: `ss.WANT, HOOF_RISE, HOOF_ON, HOOF_TEST, LEAN, STRAIN, PUT_BACK, REGARD, BACKWARD, CALL, WAIT, STILL_WANTS, ALONG, ALONG_FAR`.

Floor and sheet
- `ss.ContactPlane(knots, soften=22)`: `.y(x)`, `.gz(x)`, `.project(gx, gz, h)`, `.unproject(x, y)`, `.tread(t, x, strength, radius)`, `.wear(t)`, `.old_path()`.
  `floor = ss.ContactPlane(ss.ROUTE); floor.tread(7.2, 410.0); w = floor.wear(8.0)`
- `ss.ExposureSheet(fps=24, on=2, seconds=12)`: `.level(name, [(cell, first_drawing, hold), ...])`, `.drawing(frame)`, `.time(d)`, `.cell(level, d)`, `.at(level, name)`, `.t(level, name)`, `.text()`.
- `ss.study()` -> the one `Study`; `ss.study().drawing(d)` -> drawing d (0..143) as an RGB image; `.cast_at(d)`, `.gate_at(d)`.

Sound (kit `Mix`)
- `ss.low(mix, at, f0=150, seconds=0.9, gain=0.16, pan=0, fall=0.82)`: a cow's call (`f0=430, seconds=0.32` is the calf).
- `ss.gate_clack(mix, at, gain=0.3, pan=0, chain=True)`: wood on its stop and the chain after it.
- `ss.hoof(mix, at, x, who='lead', gain=1.0)`: one hoof on turf, panned by screen x.

Looking and measuring
- `ss.contact_sheet(path, times=None, bw=False)`: 16 stamped stills (stamps on the sheet only).
- `ss.two_tone(img)`: every pixel black or white, the SCION's colour-removed test.
- `ss.check()` -> dict; raises if an invariant fails.

## Evidence

MEASURED (`--check`, on the delivered revision, all 144 drawings):
- gate hinge stays in [-4, 12] degrees; reaches the chain at 2.50, 2.58, 2.75 s and the post at 3.00, 3.08 s.
- cow joint limits: 0 clamps in any puppet in any drawing (after `reach_fix`).
- overlap between any two animals' cards: 0 px in every drawing.
- no animal's standing fore leg crosses the fence line at the fence's depths (0 events).
- planted hoof drift between successive drawings: max 1.76 px over 1390 samples (the test counts a hoof as
  planted when it is on the ground in both drawings and moved under 6 px; the residue is the calf on the
  curved part of the line).
- 144 drawings in 12 s; ffprobe: 960x540, 24 fps, 12.000 s, aac audio present, mean -26 dB, peak -6 dB.

JUDGED, by the builder, from stills only (three 16-still sheets, five strips of consecutive drawings at
full size, one sheet pulled from the encoded mp4):
- hoof on the bar, the lean with the gate at its chain, the throw back, the head turned back calling, the
  calf arriving, the nose going down the fence, and the bent bright track with the file of animals on it
  each read as single drawings.

NOT DONE / UNKNOWN:
- **No independent critic has seen this.** I had no way to start one. The SCION forbids the builder
  awarding the pass, so this study has no verdict: it is a candidate waiting for a fresh reader.
- **Nobody watched it play.** Timing (the holds of 4, 16 and 5 drawings, the calf's trot, the 76 px/s walk)
  is reasoned from the sheet and from strips, not seen at speed.
- **Nobody heard it.** The sound is placed from the numbers (footfalls, the hinge's own stop record, the
  bell pendulum of `cast.Act`); only its levels were measured.
- No Reiniger film was inspected. The bar used was the SCION's own list.

## Rounds of look and fix

1. First sheet: animals on the detour pitched 27 degrees as if diving (floor too steep on screen); her head
   was lost among the bars in the lean and in the look along the fence; herd cut off at the frame edge.
   Fixed: flatter floor (0.5 -> 0.32), the lean re-posed with the head out over the top bar in clear light,
   the gate now puts her back a full pace (44 px) so her lowered head clears the hinge post, left side re-laid.
2. `--check` failed: legs clamped on the slope (hooves off their marks), the route cut through the fence
   stub, hooves slid when grazers lifted their heads. Fixed: `reach_fix`, route re-cut along the fence, the
   head-up poses keep the grazing hoof marks, the braced pose keeps the standing marks.
3. Strips of the detour: with strict depth sorting the stub rails crossed her body and she read as walking
   through the fence. Fixed by the method itself: the fence is one plane, wholly behind every actor. Wear
   strengthened until the new track reads; herd slowed so it no longer runs into the calf (26 px overlap -> 0).
4. The choice was 3 drawings long. Re-timed: a second look over the gate (hold), then the nose down the
   fence and a 5-drawing hold; walk-in shortened to pay for it; calf started nearer so it trots, not scurries.

## What is weak

- **The 1-bit test fails for the detour.** In `--bw` the brown fence and the black cow are one blob while
  she passes in front of it, and the worn track (a mid-tone) disappears. "Going round" depends on the brown
  mid-plane and the bright track. In grey it reads; in pure black and white it does not.
- For about 6 drawings (88-94) she walks in front of the gate at nearly its own level before the line has
  dropped; it can be taken for walking through it.
- The floor's oblique drawing makes flat ground look like a slope: the animals pitch about 15 degrees down
  and up on the detour, so "the easy way" looks like a dip, not level ground.
- The 'toward' profile (one drawing each way) is just a narrowed head; a properly cut front face would be better.
  The 'back' head sits a little low on the neck.
- Looking "along the fence" is only a lowered head beside the hinge post. A side-view puppet cannot point
  its nose toward us, where the fence end really is.
- The herd reach only the top of the new track by 12.0 s; the last cow has not yet turned onto it.
- The animals are small (lead 79 px tall) and the lower third of the frame is empty tissue.
- The encoded film is duller than the stills (grain, vignette, crf 28): the track is fainter there.
- The bell rings about ten times during the standing performance, more than the board's "only when her
  head changes direction" intends.
- The calf's lengthened stride and the walk speed above cast's "plodding" figure are untested in playback.
