# HERD.md · the cows of "The Dogs of Trouttown" (`films/swarm/dogs/herd.py`)

Seven cut-paper puppets: the lead cow (bent left horn, a bell on a strap), five plain cows, the calf. One dark
plum-brown card for the whole herd, a different map of dim bone patches on each, a hard paper edge under every
piece, an amber rim on the lamp side only. Handmade from code; nothing foraged; no lettering.

Look first (all in this folder; re-make them and run the checks with `python3 films/swarm/dogs/herd.py`):

| File | What it shows |
|---|---|
| `herd_sheet.png` | 21 poses in paper at dusk, and the same 21 as flat silhouettes |
| `herd_strip_walk.png`, `herd_strip_trot.png` | one cycle of the lead cow's walk and of the calf's trot, paper and silhouette |
| `herd_strip_file.png` | S1 on the real porch: the file down the path, through the gate, the nose touch with `dog.py`'s dog, the drink |
| `herd_strip_drink.png` | drinking, looking down into the water, the second cow waiting in the gate |
| `herd_strip_nosed_back.png` | S3: the calf starts after the dog; its mother noses it back |
| `herd_strip_turned.png` | S4: `kennel_a`'s herder gives her the eye; she turns off the pale path and crosses the dark grass |
| `herd_strip_ice.png` | S5: out on the ice, looks down, the hoof comes up, the stamp |
| `herd_strip_warm.png` | S5: standing round, steaming |
| `herd_strip_fold.png` | S6: front knees, the wait, the hind end, lying; the calf and the others asleep |

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import herd, porch, dog
```

## What came from the earlier cow film, and what did not

Imported from `films/swarm/cowpath/cast.py` (not edited): the rig and its joint limits (`cast.solve`), the
planted-hoof four-beat walk (`cast.walk`), the eases. Rebuilt here: the material (that film's cream cow would
have been the brightest thing on this porch, and only the dog may be cream); the crooked horn (there it was
crumpled flat over the brow and vanished in silhouette; here it rises and bends forward and down like a
finger); the bell (a real pendulum over the whole plan, not a sine); every pose below; lying down and getting
up; the calf's trot; aiming the muzzle at a world point; the route down the path and through the gate.
The set itself (hill, pale path, gate, bank, meadow) is already drawn by `porch.py`; `herd.py` does not draw
it again. It supplies the way over it (`herd.PATH` and the other routes), built from `porch.path_point` and the
board's numbers, so the cows stand on exactly what the porch paints.

## Conventions

- **World coordinates**, the board's. Every drawing call takes `oy` (camera offset; screen y = world y - oy).
- `(x, y)` is the ground under the middle of her barrel. `facing` 1 = looks right, -1 = left (a mirror, so
  the bent horn changes side with her; it reads from both).
- `herd.S` (0.738) is the size on the path strip: lead 104 px to the withers and 191 px muzzle to rump, the calf
  60 px to the withers at the same `s` (measured). On the hill multiply by `porch.path_point(u)[2]`, or let a
  `Route` do it.
- `who` is one of `herd.HERD = ('lead', 'second', 'mother', 'calf', 'fourth', 'fifth', 'sixth')`.
- A **pose** is a dict (cast's keys). Keys that start with `_` are messages to you: `_nose` (how far the
  muzzle has come to `nose_to`), `_breath` (0..1 while she breathes out), `_hit` (the stamp has landed),
  `_push` (how far the calf has been moved), `_face` (the head hangs steeply).
- Layers in `porch.scene`: cows on the path go in `cast['hill']`, cows in the gate, on the strip and in the
  meadow in `cast['strip']`, a cow on the ice in `cast['front']`. A `Walker` tells you which it is in.
- Cost: about 8 ms a cow at film size.

## Drawing

| Function | What it does | Example |
|---|---|---|
| `cow(ink, who, pose, x, y, s=herd.S, facing=1, oy=0, nose_to=None, turn=None, tilt=0, rim=None, far=0, flat=None, alpha=1, reflect=None, squash=1, shadow=0.45, only=None)` | Draws one animal. `nose_to` = a WORLD point her muzzle goes to (as far as the pose's `_nose`). `turn` 0..1 turns her round like the paper puppet she is (edge-on at 0.5; `facing` is the way she faced before). `rim` 0..1 amber on the lamp side (default by x: `rim_at`). `far` 0..1 hazes her toward the hill's violet. `flat=(r,g,b)` silhouette. `reflect=y` a dim reflection below that world line (ice). `shadow` the soft dark she stands on. `only='head'` draws just her head again (to lay it over a dog). Returns anchors in SCREEN px: `muzzle, mouth, eye, horn, ear, poll, throat, bell, withers, back, hook, rump, seat, belly, tail_tip, tail_head, hand, knee, hock, hooves{nf,ff,nh,fh}`, plus `facing, s, miss` (px the muzzle fell short), `breath, hit, who, violations`. | `a = herd.cow(ink, 'lead', herd.drink(t, 1), 515, 388, oy=oy, nose_to=(600, 400))` |
| `sprite(who, pose, s, facing, tilt, squash, rim, far, flat, tones, only)` | The cut-out as `(RGBA image, (ax, ay))`, for caching or post-processing. | `img, (ax, ay) = herd.sprite('calf', herd.sleep(t, 'calf'))` |
| `anchors(who, pose, x, y, s, facing, oy)` | The anchors without drawing. | `m = herd.anchors('lead', pose, 515, 388)['muzzle']` |
| `rim_at(x)` | How much lamp falls on a cow at world x. | `herd.rim_at(360)` |
| `reach(who='lead', drop=12, s=None, face=None)` | Px ahead of her middle at which she can put her muzzle down `drop` px below her hooves (12 = the water seen from the strip; negative = above the ground). | `x = 600 - herd.reach('lead')` (515: where she stands to drink at x = 600) |
| `aim(pose, who, target, amount=1, face=None)` | The pose with neck and head turned to bring the muzzle to `target` (cow units from her ground point). `cow(nose_to=)` calls it for you. Returns `(pose, miss)`. | `q, miss = herd.aim(herd.stand(t), 'lead', (120, -40))` |

## Poses (each returns a pose dict)

| Function | Reads as | Example |
|---|---|---|
| `stand(t, who, chew=1, alert=0)` | Waiting her turn: breathes, chews, an ear flicks, the tail swishes; every cow on her own clock. `chew=0`: she has stopped chewing (she has noticed). `alert` lifts the head, ears round. | `herd.cow(ink, 'second', herd.stand(t, 'second'), x, y)` |
| `notice(pose, amount)` | Modifier: jaw still, both ears to it, eye open. | `herd.notice(herd.stand(t, 'fifth'), 1.0)` |
| `look_down(t, p, who)` | On the bank looking into the water where she cannot go: fore hooves at the edge, head hung out, ears forward. `p` 0..1 lowers it. | `herd.cow(ink, 'lead', herd.look_down(t, 1), 515, 388, nose_to=(596, 372))` |
| `drink(t, p, who)` | Forelegs splayed, shoulders down, muzzle on the line, throat working. | `herd.cow(ink, 'lead', herd.drink(t, herd.clamp((t - 6.5) / 1.2)), 515, 388, nose_to=(600, 400))` |
| `nose_touch(tau, t=None, who)` | The S1 touch, on the dog's clock (`dog.nose_touch(tau)`): ears round and chewing stops 0..0.3, contact `NOSE_TOUCH['contact']` = 0.75, held still to 1.55, breath out at 1.6 (`_breath`), away by 2.6. The head hangs steeply so it comes down on the nose from above. | see "The nose touch" below |
| `smell(tau, who)` | The same for a reel held up to her (S6, 159.8): down 0..0.6, hold to 1.4, breath, up by 2.2. | `herd.cow(ink, 'lead', herd.smell(t - 159.8), 600, 388, facing=-1, nose_to=reel_xy)` |
| `yield_to(tau, who)` | The herder is in front of her: stops chewing, ears round, head up (0..0.3), holds (to 0.9), head swings away and she takes one step back (to 1.5). Then turn her and walk her off (`off_path`). | `herd.cow(ink, 'fourth', herd.yield_to(t - 94.4), x0, y0, s0 * herd.S, -1, oy)` |
| `nudge(tau, who='mother')` | The mother noses the calf back: head down and round to it (0..0.5), one slow shove (0.5..1.1), lifts away (1.3..2.0). | `herd.cow(ink, 'mother', herd.nudge(tau), 440, 388, nose_to=(calf_x + 30, 352))` |
| `calf_nosed(tau)` | The calf: looking after the dog; pushed at 0.5, legs catching up one at a time, ears down; looks round at her; gives in by 2.0. Move its x by `-16 * pose['_push']` (away from her head). | `cn = herd.calf_nosed(tau); herd.cow(ink, 'calf', cn, 520 - 16 * cn['_push'], 391)` |
| `calf_skid(p)` | The calf stops badly: fore legs braced, rump still coming, head thrown up (0..0.4), then sorts its legs out. | `herd.cow(ink, 'calf', herd.calf_skid(p), x, 388)` |
| `stamp(tau, who)` | On the ice: looks down and holds 0..0.7, the near fore leg comes up slowly to 1.2, hangs, lands at `herd.STAMP_HIT` = 1.38 in three frames with her front end behind it; the bell jumps and rings on; she watches. `stamp(tau - 1.7)` stamps again. `_hit` goes 0..1 at the landing. | `herd.cow(ink, 'lead', herd.stamp(t - 121.0), 606, 401, facing=-1, oy=oy, reflect=402)` |
| `warm(t, who, p=1)` | Standing round the wet dogs: head low over them, eyes half shut, flanks filling every 4 s, `_breath` on the way out. | `herd.cow(ink, w, herd.warm(t, w), x, y, nose_to=o['nose'])` |
| `fold_down(p, who)` | Lying down the way a cow does, `p` 0..1 over about 2 s: gathers her feet (0.12), front knees (0.45), waits with her rump in the air (0.62), the hind end sinks and rolls (0.86), a long breath (1). | `herd.cow(ink, 'lead', herd.fold_down((t - 173.0) / 2.0), 645, 388, facing=-1, oy=oy)` |
| `lie(t, who, chew=1, alert=0)` | Folded down, awake, chewing the cud. `fold_down(1)` is `lie` at rest. | `herd.cow(ink, 'lead', herd.lie(t), 645, 388, facing=-1, oy=oy)` |
| `sleep(t, who, p=1)` | Asleep: chin down on the ground (or on `nose_to`: the calf's chin on the wooden retriever), eye shut, a breath every 5 s. | `herd.cow(ink, 'calf', herd.sleep(t, 'calf'), 790, 384, facing=-1, oy=oy, nose_to=(752, 362))` |
| `get_up(p, who)` | Hind end first: the heave (0.15), rump up while still on her knees (0.5), a wait, one fore leg at a time (1). | `herd.cow(ink, 'lead', herd.get_up((t - 153.5) / 1.0), x, y)` |
| `step_pose(who, dist, slope=0, rest=0, t=0, carry=0, lift=1, gait='walk', chew=1, weight=1)` | The walk (or `gait='trot'`, calf only) after `dist` cow units; `rest` 0..1 brings her to a stand. Hooves that are down stay down. | `herd.cow(ink, 'lead', herd.step_pose('lead', x / herd.S), x, 388)` |
| `blend(p, q, x, who)`, `tween(p, q, x, ease, who)`, `with_(pose, **keys)` | Between two poses; a copy with keys replaced. Eases: `linear, inout, out, slow, slam, snap, anticip`. | `herd.tween(herd.stand(t), herd.look_down(t), u, 'slow')` |

## Going somewhere

| Thing | What it is | Example |
|---|---|---|
| `herd.PATH` | THE way: the pale path from the crest, through the gate (she turns round there over `herd.TURN` = 46 px, edge-on in the middle), the path strip, the meadow to x = 960. 957 px long. `herd.D_GATE` (322) is the gate. | `st = herd.PATH.at(d)` -> `x, y, s, facing, squash, slope, layer` |
| `d_at(x)` | The `d` on `PATH` for a world x on the strip or meadow (x >= 352). | `herd.d_at(515)` |
| `hill_spot(k)` | The `d` where the k-th cow of the queue waits: 0 in the gate, 1 behind her, and so on up the hill, the gaps closing as the path narrows. | `herd.PATH.at(herd.hill_spot(2))` |
| `Route(nodes, lean=1, layer=None)` | Any way a cow can go: nodes `(x, y, size)`; `.at(d)`, `.units(d, who)`, `.find(x, last=True)`, `.length`, `.turns`. | `r = herd.Route([(700, 386, 1), (860, 380, 1)])` |
| `path_route(end_x=960, u0=0)`, `path_nodes(u0, n)` | `PATH` rebuilt to stop elsewhere, or its hill part as nodes. | `herd.path_route(700)` |
| `off_path(u, to=(760, None), mid=None)` | S4: from the path at `u` across the dark grass to the meadow. She turns where she stood. | `r = herd.off_path(0.6, (770, None))` |
| `ice_route(x0=700, out=600, y=None)` | S5: from the meadow's edge down onto the ice and out to x = `out`. Walk `d` back down to bring her off backwards. | `ir = herd.ice_route(700, 606)` |
| `depth_scale(y)`, `meadow_y(x)` | Size on the hill face at world y; ground height on the bank. | `herd.depth_scale(330)` |
| `Plan(keys, ramp=0.7)` | `[(t, d)]` -> `plan(t) = (d, rest)`. Walks between different d, waits between equal d, eases to a stop. | `d, rest = herd.Plan([(0, 100), (4, 280), (9, 280)])(t)` |
| `Walker(who, route, keys, acts=(), gait='walk', carry=0, lift=1)` | One cow, her route, her evening. `.draw(ink, t, oy, layer=None, nose_to=None, **cow_args)` (returns the anchors plus `x, y, d, layer, rest`, or `None` if she is not in that layer now); `.state(t)`; `.bell_hits` (lead: the times the clapper strikes); `.hoof_falls(t0, t1)` -> `[(t, x, y, leg)]` for hoof sounds and rings. `acts=[(t0, t1, fn)]` plays `fn(t - t0)` while she stands. | below |
| `file_plan(n=7, t0=0, dog_nose=(548, 306), lead_to=None)` | The whole S1 file as `{who: Walker}`: lead through the gate about `t0 + 1.6`, stopped for the touch by `t0 + 3.4`, on at 5.6, drinking; the others closing up behind. | below |
| `stand_round(cx=790, who=HERD, y=None, spread=1)` | S5: where each stands round the wet dogs: `[dict(who, x, y, s, facing, back, nose)]`, furthest first. Draw the dogs after the `back=True` cows. | below |
| `Bell(throat, t0, t1)` | The pendulum itself (`.angle(t)`, `.hits`), if you drive a lead cow without a `Walker`. | `b = herd.Bell(lambda t: throat_xy(t), 0, 28)` |

Speed: `herd.SPEED` = 45 px a second on the strip (times `rel` on the hill). A cow never trots.

## Steam and breath

| Function | What it does | Example |
|---|---|---|
| `steam(ink, t, x, y, amount=1, width=70, height=64, seed=0, drift=6)` | Soft pale plumes rising from the SCREEN line y. | `herd.steam(ink, t, 760, 300, 0.8)` |
| `breath(ink, x, y, p, facing=1, size=1, down=0.25)` | One breath out at SCREEN (x, y), `p` 0..1. | `herd.breath(ink, *a['muzzle'], a['breath'], a['facing'])` |
| `steam_on(ink, t, a, amount=1, cold=1)` | Steam off the back of a cow just drawn (`a` = what `cow()` returned), and her breath when the pose breathes out. | `herd.steam_on(ink, t, herd.cow(ink, w, herd.warm(t, w), x, y))` |

## Worked examples

**S1, the file and the nose touch** (as in `herd_strip_file.png`):

```python
def dog_nose(t):                       # where the dog's nose is: draw the dog once on a scratch image
    return dog.draw_dog(Image.new("RGB", (960, 540)), dog.nose_touch(t - 3.0, height=herd.DOG_NOSE_UP),
                        470, 394, scale=0.6, facing=1)["nose"]
fp = herd.file_plan(dog_nose=dog_nose(3.9))
def nose(t):
    n = dog_nose(t)
    return (600, 400) if t > 5.8 else (n[0] + 10, n[1] - 3)
def hill(ink, t, oy):
    for w in reversed(herd.HERD): fp[w].draw(ink, t, oy, layer="hill")
def strip(ink, t, oy):
    for w in reversed(herd.HERD): fp[w].draw(ink, t, oy, layer="strip", nose_to=nose(t) if w == "lead" else None)
def sill(ink, t, oy):
    dog.draw_dog(ink, dog.nose_touch(t - 3.0, height=herd.DOG_NOSE_UP) if 3.0 <= t <= 5.8 else dog.watch(t), 470, 394 - oy, scale=0.6)
    if 3.0 < t < 5.8:                  # her head again, over the dog: she has lowered it over the sill
        a = fp["lead"].draw(ink, t, oy, nose_to=nose(t), only="head")
        herd.breath(ink, *a["muzzle"], a["breath"], a["facing"])
porch.scene(ink, t, oy, cast=dict(hill=hill, strip=strip, sill=sill))
for hit in fp["lead"].bell_hits: mix.bell(hit, freq=1150, seconds=0.5, gain=0.06)
```

**The nose touch, and why `height=herd.DOG_NOSE_UP`.** Both animals face right, so the noses can only meet one
above the other. With the dog's default `height=150` its nose is level with her poll and her head has to lie
along the dog's head: one hides the other. With the dog's nose at 100 dog units (60 px above the sill) her
head can hang nearly straight down beside it, and laid over the dog with `only='head'` both faces read.

**S4, turned aside:**

```python
x0, y0, s0 = porch.path_point(0.6)
r4 = herd.off_path(0.6, (770, None))
w4 = herd.Walker("fourth", r4, [(95.0, r4.find(x0, last=False)), (104.0, r4.length)])
# 94.4 .. 95.0 she plays herd.yield_to(t - 94.4) at (x0, y0, s0 * herd.S), facing -1; from 95.0: w4.draw(ink, t, oy, layer=...)
```

**S5, the ice:**

```python
ir = herd.ice_route(700, 606)
lead = herd.Walker("lead", ir, [(119.0, 0), (121.2, ir.length), (124.5, ir.length)], carry=16,
                   acts=[(121.3, 124.5, herd.stamp)])
a = lead.draw(ink, t, oy, reflect=402, rim=0.15)            # in cast["front"]
# porch: stamps=[(a["hooves"]["nf"][0], p)] from t = 121.3 + herd.STAMP_HIT
for o in herd.stand_round(760):                             # later: round the eleven
    a = herd.cow(ink, o["who"], herd.warm(t, o["who"]), o["x"], o["y"], o["s"], o["facing"], oy, nose_to=o["nose"], rim=0.1)
    herd.steam_on(ink, t, a)
```

## How she moves (what is built in, so you do not have to add it)

Four-beat walk with the hooves planted; shoulders sink when two legs share the load and ride up over the one
that carries; the head nods against the stride; the bell is a pendulum driven by her throat, so it arrives
late and is still swinging after she stops (23 degrees in the 0.7 s after a stop, measured). She stops by
easing off and shuffling her feet under her, and only then starts to chew. Down is front knees first; up is
hind end first. No lowered-horn threat, no kick, no run exists in this file.

## Checks (MEASURED by `herd.check()`, which raises on failure)

- joint limits and leg reach: 0 violations in 14 performances x 41 samples x lead, herd cow, calf.
- planted hooves on the strip, walk and trot: 0.0 px drift.
- sizes on the strip: lead 104.0 px to the withers, 190.7 px long; calf 59.7 px.
- muzzle to the water line from the strip: 0.49 px short; to a dog's nose 80 px up: 1.5 px short.
- `PATH` has exactly one turn (the gate), at d = 322.
- the bell: 3 strikes in a 3 s walk, still swinging after the stop.

## Honest limits

- JUDGED from stills only (the sheets above). Nobody has watched the walk, the fold-down, the stamp or the
  bell in motion. The first playback is the real test of weight and of timing.
- Side view only. A cow cannot turn her head toward or away from us; "turning" is the paper flip.
- On the hill the planted hooves creep up to about 3 px while she grows toward the gate (the path is depth,
  not ground). On the strip, the meadow and the ice they do not move.
- The cows on the path stand level on a path drawn steep; with the ground shadow they read as on it, but a
  critic should look at the queue at 0..6 s in motion.
- The nose touch works only with the dog's nose lowered (`DOG_NOSE_UP`); see above. The S1 builder owns
  that choice.
- `nudge` and `calf_nosed`: the calf is small and dark beside its mother; at film size it reads as "big head
  comes down in front of small animal, small animal goes back", not more. The calf's own trot after the dog
  (`Walker('calf', ..., gait='trot')`) and `calf_skid` exist but were only looked at on the sheet.
- The steam is a soft band above the backs; it has not been seen against the cold blue of the frozen scene.
- The herd does not darken with `dusk`; it is already the darkest thing on the bank.
- Not built here: a cow seen from below the surface (a muzzle, a hoof, a wobbling shape). That is a
  `porch.look_up` picture and belongs to whoever builds the F-TOWN shots; `anchors()` gives the muzzle and
  hoof positions to put it under.
