# KENNEL B · four more makes of dog

Module: `films/swarm/dogs/kennel_b.py`. Sheet of every dog in every action, in colour and as a black
silhouette: `kennel_b_sheet.png`. Strips: `kennel_b_strip_set_down / stop / sizes / nudge / run / nose /
dive / comeup / breath / warm / cows.png`. Re-make them and run the numeric checks with
`python3 films/swarm/dogs/kennel_b.py`.

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import kennel_b as kb
```

| Dog | Made as | SCION read and worked by | Job in Trouttown |
|---|---|---|---|
| `retriever` (three sizes) | wooden pull-toy on wheels; neck, head, jaw, ear, peg tail and a bead on a string are hinged and settle late | `scion/animation-13.md` | each carries one piece, at the same time |
| `sheepdog` | crepe-paper strips on four coil springs; the body is a mass on the springs, every strip its own damped pendulum | `scion/animation-41.md` | walks the pieces into one line |
| `bloodhound` | ONE pencil line, 280 points in the same order in every key drawing, each frame an in-between; the nose is the hand-authored exception and pays out along a trail | `scion/animation-07.md` | sniffs a piece back to where it came from |
| `terrier` | small stiff corrugated-card dog, a joint tree solved forward only, shot on twos | `scion/animation-32.md` | goes down the one hole that is wrong |

None is cream or red (those are the lead dog's). Nothing is lettered.

## Shared convention

`dog(target, x, y, action="walk", t=0.0, scale=1.0, facing=1, carry=None, **options)`

| Argument | Meaning |
|---|---|
| `target` | a `kit.Ink`, an `ink.layer()`, or a PIL image |
| `x, y` | SCREEN point. On the ground: the ground under the middle of the dog. `swim`, `breath_out`: the middle of the body. `surface`: a point on the waterline (the mouth bobs up through it). Terrier `dive` / `come_up`: the mouth of the hole |
| `t` | seconds since the action began. Everything is stateless: the drawing depends only on `t` |
| `scale` | `1.0` gives: retriever 229 px long (big), sheepdog 216, bloodhound 205, terrier 82. The sheet uses 0.8 (terrier 1.0) |
| `facing` | `+1` nose right, `-1` nose left |
| `carry` | `"piece"` (one frame of film with a child's drawing), `"reel"`, `"page"`, `"part"`, `"fix"`, or `None` |
| `look` | radians added to the head angle (positive = up): `look=0.6` to look up at a cow on the bank or her hooves on the ice |
| render options | `silhouette=True`, `color=`, `tint=kb.WATER, tint_amount=0.3` (under water), `alpha=`, `shadow=False`, `rot=` (radians, whole dog), `clip=(x0, y0, x1, y1)` (screen box, `None` for open sides) |

Every call returns SCREEN anchors: `mouth`, `nose`, `head`, `body`, `tail`, `bbox`, and `hold` (True while the
thing is still in the mouth). Most also return `eye`.

Moving a dog without sliding: `x = x0 + facing * scale * kb.travel(dog, action, t, **options)`.
At scale 1 that is 75 px/s for a retriever carrying, 254 for the sheepdog's `run_line`, 44 for the
bloodhound's `follow`, about 151 for the terrier's walk.
Rising after `breath_out`: `y = y0 - scale * kb.lift(t)` (nothing for 0.9 s, then up, faster).
`kb.draw("terrier", ink, x, y, "dive", t)` calls a dog by name. `kb.ACTIONS[dog]` lists its actions and
`kb.DURATION[(dog, action)]` the length of the one-shots.

## 1 · `retriever` · the wooden pull-toy

`kb.retriever(target, x, y, action, t, scale=1.0, facing=1, size="big", carry=None)`; `size` is `"big"`,
`"mid"`, `"small"` or a number: the three retrievers are the same toy in three sizes.

| Action | What it does | Example |
|---|---|---|
| `walk` | rolls; one wheel is not quite round, so the ear and bead keep time | `kb.retriever(ink, x0 + 0.7 * kb.travel("retriever", "walk", t), 440, "walk", t, scale=0.7)` |
| `carry` | rolls with the piece held high and level | `kb.retriever(ink, x, 440, "carry", t, scale=0.7, size="mid", carry="piece")` |
| `wait` | brakes to a stop in 0.32 s; neck nods on, ear, tail and bead swing and settle, then nothing moves. `arrive=0` for already still | `kb.retriever(ink, 520, 440, "wait", t - 101.0, scale=0.7, carry="piece")` |
| `set_down` | stops, neck folds down (0.3..0.8 s), jaw opens and the piece stands on the gravel (1.0), head comes up, two tail ticks (1.9, 2.2). 2.5 s. The piece stays drawn; its foot is returned as `thing` | `a = kb.retriever(ink, 520, 440, "set_down", t - 102.0, scale=0.7, carry="piece")` |
| `proud` | holds the reel up, the peg tail ticking | `kb.retriever(ink, 400, 394, "proud", t, scale=0.7, facing=-1, carry="reel")` |
| `told` | the old dog turned its back: tail peg drops, head and neck sink (1.2 s) | `kb.retriever(ink, 400, 394, "told", t - 168.0, scale=0.7, facing=-1, carry="reel")` |
| `swim` | wheels spin free, ear floats up, bead trails. `pitch=` radians (negative = nose down) | `kb.retriever(ink, x, y, "swim", t, scale=0.7, carry="piece", pitch=-0.5, tint=kb.WATER, tint_amount=0.3)` |
| `breath_out` | head shakes (0..0.5), one big bubble leaves the open jaw (0.5), it tips nose up and drifts (2 s); the piece is let go | `kb.retriever(ink, x, y - 0.7 * kb.lift(t - 131.0), "breath_out", t - 131.0, scale=0.7)` |
| `surface` | bobs up through the waterline, gulping, the bob dying away | `kb.retriever(ink, 640, 300, "surface", t - 133.0, scale=0.7)` |
| `warm` | WITH THE COWS (S5): wet on the bank, it rattles with cold, head and tail down; over `warm=4.0` s the rattle dies, it rolls 7 units toward the cow (`cow=+1` she is at its nose end, `-1` at its tail end), head comes up, three tail ticks | `kb.retriever(ink, x0 + 0.6 * kb.travel("retriever", "warm", t - 134.0, cow=1), 364, "warm", t - 134.0, scale=0.6, cow=1)` |

For the last shot (the calf asleep against a wooden retriever): `kb.retriever(ink, x, y, "wait", t, arrive=0)`
and lay the calf's head on `a["body"]`; the toy does not move at all, which is the point.

## 2 · `sheepdog` · crepe paper on springs

`kb.sheepdog(target, x, y, action, t, scale=1.0, facing=1, carry=None)`

| Action | What it does | Example |
|---|---|---|
| `walk` | feet step, the body rides the springs, the fringe swings behind the step | `kb.sheepdog(ink, x, 440, "walk", t, scale=0.7)` |
| `run_line` | flat out along the row of pieces, low, fringe streaming back | `kb.sheepdog(ink, x0 + 0.7 * kb.travel("sheepdog", "run_line", t), 440, "run_line", t, scale=0.7)` |
| `nudge` | stops, lowers its nose to a piece (0.36..0.72 s), pushes it `push=14` units (0.78..1.18), then tips its head to see if the row is straight. 2.6 s. Returns `push` in px: add it to the piece's x | `a = kb.sheepdog(ink, 500, 440, "nudge", t - 104.0, scale=0.7); kb.draw_thing(ink, "piece", 578 + a["push"], 440, 0.7)` |
| `wait` | stops; the body lurches on over the feet and bounces, the fringe settles strip by strip | `kb.sheepdog(ink, 500, 440, "wait", t - 106.0, scale=0.7)` |
| `carry` | walks with a thing hung from the mouth | `kb.sheepdog(ink, x, 440, "carry", t, scale=0.7, carry="reel")` |
| `swim` | paddles; the fringe lies back along the body | `kb.sheepdog(ink, x, y, "swim", t, scale=0.7, tint=kb.WATER, tint_amount=0.3)` |
| `breath_out` | bubble, legs go limp, tips up | `kb.sheepdog(ink, x, y - 0.7 * kb.lift(t0), "breath_out", t0, scale=0.7)` |
| `surface` | bobs at the waterline | `kb.sheepdog(ink, 560, 300, "surface", t0, scale=0.7)` |
| `warm` | WITH THE COWS: crouched and trembling on its springs, every strip shivering; it steps toward her, rises, and the paper hangs still | `kb.sheepdog(ink, x0 + 0.62 * kb.travel("sheepdog", "warm", t0, cow=1), 348, "warm", t0, scale=0.62, cow=1)` |

## 3 · `bloodhound` · one pencil line

`kb.bloodhound(target, x, y, action, t, scale=1.0, facing=1, carry=None, trail=None, stretch=0.0)`

`trail` is a list of SCREEN points starting just ahead of the nose; `stretch` 0..1 pays the nose out along
it while the rest of the drawing stays put. `kb.scent_trail(ink, pts, upto=1.0)` draws the faint pencil
dashes on the gravel that it follows (a mark, not a label). Options: `boil=False` stops the line being
redrawn 8 times a second; `fill=0` leaves it a bare line you can see through.

| Action | What it does | Example |
|---|---|---|
| `walk` | long low walk, ear swinging | `kb.bloodhound(ink, x, 440, "walk", t, scale=0.7)` |
| `nose_down` | lifts and tests the air (0..0.6 s), drops its nose to the gravel (1.05), three sniffs, then holds: it knows (2.0) | `kb.bloodhound(ink, 300, 440, "nose_down", t - 103.0, scale=0.7)` |
| `follow` | walks nose-down along the trail, ears dragging; with `trail` and `stretch` the nose runs on ahead to where the piece came from | `tr = [(390, 438), (470, 436), (560, 438)]; kb.scent_trail(ink, tr); kb.bloodhound(ink, x, 440, "follow", t, scale=0.7, trail=tr, stretch=ramp(t, 108, 110))` |
| `carry` | walks with the thing held level | `kb.bloodhound(ink, x, 440, "carry", t, scale=0.7, carry="piece")` |
| `wait` | sits (0.8 s). `sit=False` stands | `kb.bloodhound(ink, 300, 440, "wait", t0, scale=0.7)` |
| `swim` | paddles, ear and tail streaming | `kb.bloodhound(ink, x, y, "swim", t, scale=0.7, pitch=-0.4, tint=kb.WATER, tint_amount=0.3)` |
| `breath_out` | jowls puff (0..0.5), the bubble goes (0.62), the whole line goes slack and tips up | `kb.bloodhound(ink, x, y - 0.7 * kb.lift(t0), "breath_out", t0, scale=0.7)` |
| `surface` | bobs at the waterline, mouth open | `kb.bloodhound(ink, 500, 300, "surface", t0, scale=0.7)` |
| `warm` | WITH THE COWS: hunched, tail tucked, the line trembling; then it sits up straight beside her | `kb.bloodhound(ink, 300, 342, "warm", t0, scale=0.62, cow=1)` |

Under the ice (S5) the same nose can go up instead of along: give `nose_down` a `trail` that climbs to the
lead cow's hoof on the ice and raise `stretch` as she stamps.

## 4 · `terrier` · small stiff card dog

`kb.terrier(target, x, y, action, t, scale=1.0, facing=1, carry=None)`. `twos=False` turns off the
12-drawings-a-second exposure.

| Action | What it does | Example |
|---|---|---|
| `walk` | stiff trot; the root is read off the planted forefoot, so it does not slide | `kb.terrier(ink, x0 + kb.travel("terrier", "walk", t), 440, "walk", t)` |
| `carry` | trots with the fix in its teeth | `kb.terrier(ink, x, 440, "carry", t, carry="fix")` |
| `wait` | stands; one ear flick at 1.5 s. `sit=True` sits | `kb.terrier(ink, 600, 440, "wait", t0, sit=True)` |
| `dive` | (x, y) is the hole. Crouches (0.24 s), goes in head first (0.5..0.85), hind legs kick, gone (1.6). `stay=True` leaves the tail out, wagging | `kb.terrier(ink, 640, 452, "dive", t - 110.0)` |
| `come_up` | head out of the hole (0.3), looks about (0.42), scrambles out (0.72..1.2), stands with the fix, tail quivering (1.4..2.2). Returns `stand`: where to draw it next | `a = kb.terrier(ink, 640, 452, "come_up", t - 112.0, carry="fix")` |
| `swim` | fast stiff paddle | `kb.terrier(ink, x, y, "swim", t, tint=kb.WATER, tint_amount=0.3)` |
| `breath_out` | paddles harder (0..0.6), small bubble, goes limp | `kb.terrier(ink, x, y - kb.lift(t0), "breath_out", t0)` |
| `surface` | bobs at the waterline, paddling | `kb.terrier(ink, 700, 300, "surface", t0)` |
| `warm` | WITH THE COWS: stands shaking on twos, head and tail down; then sits, ears up, under her chin | `kb.terrier(ink, 420, 360, "warm", t0, scale=0.9, cow=-1)` |

## Things

`kb.draw_thing(target, kind, x, y, scale=1.0, angle=0.0, stand=True)` draws a `piece`, `reel`, `page`, `part`
or `fix` by itself; with `stand=True`, (x, y) is the middle of its bottom edge.

## The cows, and what these four do about them

| Seq | Moment | Calls |
|---|---|---|
| S4 | the pack goes under while the herd watches from the bank | any dog `walk` to the waterline then `swim` with `pitch=-0.5`; a glance back at the calf on the edge is `look=0.5` with `facing` toward the bank |
| S5 | the lead cow walks out onto the ice above them | `swim` at `speed=0` with `look=0.7`; the bloodhound's nose paid up toward her hoof (above) |
| S5 | eleven run out of breath and come up; the cows stand round them, steaming | `breath_out` with `kb.lift`, then `surface`, then `warm` on the bank with `cow=+1/-1` toward the nearest cow. See `kennel_b_strip_cows.png` (the cows in it are flat stand-ins, `_standin_cow`, for scale only) |
| S6 | the calf asleep against a wooden retriever | `retriever(..., "wait", t, arrive=0)`; rest the calf on `a["body"]` |

## Evidence

- MEASURED (printed by the module's self-test): all 37 dog/action pairs draw; retriever loose parts are
  still at 0.01 rad/s while rolling, moving at 3.30 rad/s at 0.45 s (the body stopped at 0.32 s) and 0.066 at
  2.4 s; sheepdog planted-foot slip 1e-14 units and fringe speed falling from 48.8 to 0.000; bloodhound has
  280 points in every drawing of every action and its nose ends 3.5 units from the trail's end at stretch 1;
  terrier bone-length and pivot error 1e-14, planted forefoot slip 3e-14.
- JUDGED from stills only (the sheet and the strips, looked at by the builder): the four read as four
  different makes in silhouette; `set_down`, `dive`, `come_up` and `nudge` read in order without labels.
- JUDGED, weak: in `warm` the retriever's and sheepdog's cold and warm poses differ little in a still; the
  difference is the shiver, which only playback shows. The bloodhound and terrier change pose clearly.
- UNKNOWN: any of it in motion at 24 fps (no playback was watched); how the dogs sit against the cow
  builder's real cows and the world's ground line (no cow module was in this folder when this was drawn);
  an independent critic's verdict (none has looked yet; the builder does not award the pass).
