# KENNEL A · three pack dogs, three ways of making

Module: `films/swarm/dogs/kennel_a.py`. Sheets (every dog, every action, on dusk and on creek teal):
`kennel_a_sheet_herder.png`, `kennel_a_sheet_digger.png`, `kennel_a_sheet_old_dog.png` in this folder.
Re-make them and run the numeric checks with `python3 films/swarm/dogs/kennel_a.py`
(`--check` for the checks alone).

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import kennel_a as ka
```

## Shared convention (all three dogs)

| Argument | Meaning |
|---|---|
| `ink` | a `kit.Ink` (RGB frame or an `ink.layer()`), or a PIL image |
| `x, y` | SCREEN position of the ground point under the middle of the dog. For `action="swim"` it is the middle of the belly |
| `s` | size. `s=1`: herder and digger about 95 px long; old dog about 185 px standing, 195 px lying. The board's sill place (x 350..500) wants the old dog at `s=0.78` |
| `facing` | `+1` nose right, `-1` nose left |
| `action` | see each dog |
| `t` | seconds; drives cycles |
| `p` | 0..1; drives one-shot actions |
| `look` | degrees the head is raised (ice beat: `look=45`) |

Every call returns SCREEN anchors: `mouth`, `nose`, `head`, `eye`, `tail`, `back`, `bbox`, plus the ones
listed below. Put a reel, a piece or a post in the mouth at `anchors["mouth"]`.
No dog here is cream or red, and nothing is lettered. Pass black for the colour arguments to get the
silhouette test.

## 1 · `herding_dog` · black articulated shadow puppet (scion/animation-02.md)

Flat black card pieces (torso, neck, head, jaw, two ears, two-piece tail, four two-piece legs) pinned at
joints with angle limits (`HERDER_LIMITS`), cut with rounded scissors, a cut-out eye you can see the water
through, exposed on twos (12 poses a second, `exposure=`). No inner drawing: contour only.

`herding_dog(ink, x, y, s=1.0, facing=1, action="wait", t=0.0, p=0.0, look=0.0, pages=0, color=(14,13,20), page_color=(226,233,226), page_line=(70,84,96), exposure=12)`

| Action | Driven by | What it does | Example |
|---|---|---|---|
| `wait` | `t` | stands held; one ear turns now and then | `ka.herding_dog(ink, 240, 392, 0.9, 1, "wait", t=t)` |
| `walk` | `t` | four-beat walk | `ka.herding_dog(ink, x, 392, 0.9, 1, "walk", t=t)` |
| `circle` | `t` | the low collie crouch at a trot: the herding move | `x, y, f, behind, size = ka.herd_circle(700, 430, 120, 26, t, period=6); ka.herding_dog(ink, x, y, 0.8 * size, f, "circle", t=t)` |
| `gather` | `p` | reaches (0..0.34), takes the page (0.42), tucks it under the chin (0.52..1). `pages` = already held | `a = ka.herding_dog(ink, 610, 440, 0.9, 1, "gather", p=p, pages=3)`; offer the page at `a["reach"]` until p = 0.42 |
| `carry` | `t` | walks with `pages` flat pages hanging from the mouth; rigid, never bent | `ka.herding_dog(ink, x, 440, 0.9, -1, "carry", t=t, pages=6)` |
| `swim` | `t` | paddles, ears streaming; `pages=1` swims with a page | `ka.herding_dog(ink, x, y, 0.9, -1, "swim", t=t)` |
| `turn` | `p` | the flat card turns over, edge-on halfway (for passing the fence sideways, or turning round) | `ka.herding_dog(ink, 560, 440, 0.9, 1, "turn", p=p)` |
| `slide` | `p` | comes up off the ground like a shadow leaving a wall (arrival, 89.2) | `ka.herding_dog(ink, 150, 392, 0.9, 1, "slide", p=p)` |

Extra anchors: `reach` (where the next page must be offered), `chest`, `paws`, `pages` (count held).
`herd_circle(cx, cy, rx, ry, t, period=6.0, start=0.0)` returns `(x, y, facing, behind, size)`; draw the
dog before the fish class when `behind` is True.

## 2 · `digger` · constraint-drawn wire dog (scion/animation-08.md)

Sixteen points and their wires. An action states only relationships: four paw pins (hard), and a wanted
rump, shoulder and nose (soft). A relaxation solver finds the rest every frame; a knee that lands on the
wrong side is mirrored. It draws as a light wire over a dark one, with the points shown, and you can see
through it. No boil: it is ruled, not hand-drawn.

`digger(ink, x, y, s=1.0, facing=1, action="wait", t=0.0, p=0.0, look=0.0, wire=(224,232,238), shade=(22,26,40), point=(255,255,255), gravel=(168,160,138), post=True, post_color=(126,104,78), spray=True)`

| Action | Driven by | What it does | Example |
|---|---|---|---|
| `wait` | | stands | `ka.digger(ink, 760, 394, 0.9, -1, "wait")` |
| `walk` | `t` | walk | `ka.digger(ink, x, 440, 0.9, 1, "walk", t=t)` |
| `swim` | `t` | paddle | `ka.digger(ink, x, y, 0.9, 1, "swim", t=t)` |
| `dig` | `t` | play-bow, fore paws scoop in turn (3 scoops a second each), gravel thrown back between the hind legs | `a = ka.digger(ink, 500, 440, 0.9, 1, "dig", t=t)`; the hole belongs at `a["hole"]` |
| `heave` | `p` (and `t` for the tremble) | grips something in the bed (0..0.2), leans back and strains (0.2..0.75), it comes out and is held high (0.75..1) | `a = ka.digger(ink, 520, 440, 0.9, 1, "heave", t=t, p=p)`; draw the thing at `a["mouth"]`, rooted at `a["grip"]` while `a["out"] == 0` |
| `build` | `p` | rears and drives a post in with three blows (p = 0.22, 0.47, 0.72), then one paw holds it | `a = ka.digger(ink, 500, 440, 0.9, 1, "build", t=t, p=p)`; `post=False` to draw your own at `a["post"]` (top) and `a["post_foot"]` |
| `unbend` | `p` | one reed of wire unbends into the dog (arrival, 91.0) | `ka.digger(ink, 820, 394, 0.9, -1, "unbend", p=p)` |

Extra anchors: `paws`, `residual` (worst wire-length error as a fraction), `solved`
(`residual <= DIGGER_TOLERANCE`, 1 %). `unbend` is a declared exception: mid-way the wire is not at length.

## 3 · `old_dog` · engraved print, cut out and hinged (scion/animation-50.md, animation-01.md)

Foraged: Thomas Bewick, "The Newfoundland Dog", wood engraving, A General History of Quadrupeds.
Public domain, Wikimedia Commons `File:Bewicks-newfoundland.jpg`; credit in `films/credits/dogs.json`;
the scan is at `films/sources/dogs/kennel_a/bewick-newfoundland.jpg` (git-ignored: if it is missing the
module hatches the same cut pieces by hand and returns `foraged: False`; re-download from the credit URL).
Sourced: the engraving. Invented: the cuts (`_CUT`), the pins, every pose and movement, and a strip of
neck fur under the head borrowed from the mane. At rest the pieces reassemble the print.

`old_dog(ink, x, y, s=1.0, facing=1, action="lie", t=0.0, p=0.0, look=0.0, paper=(186,182,174), ink_color=(34,32,38), verso=False, eye=None, exposure=8)`

`facing` is the way it faces BEFORE it turns; `turn_back`, `back`, `look_over` and `let_pass` draw it the
other way round by themselves, about the same `x`.

| Action | Driven by | What it does | Example |
|---|---|---|---|
| `lie` | | lies across the sill, chin on its paws | `ka.old_dog(ink, 425, 394, 0.78, 1, "lie")` |
| `lift_head` | `p` | the head comes up off the paws | `ka.old_dog(ink, 425, 394, 0.78, 1, "lift_head", p=p)` |
| `look` | `p` | the long look: head up, still; one slow blink at p 0.42..0.6 | `ka.old_dog(ink, 425, 394, 0.78, 1, "look", p=p)` |
| `turn_back` | `p` | gets up front end first (0..0.17), back end (0.17..0.30), turns in three slow steps (0.30..0.68), lies down rear first with its back turned and its tail laid out behind (0.68..1) | `a = ka.old_dog(ink, 425, 394, 0.78, 1, "turn_back", p=ramp(t, 165.5, 168.0))`; the tail lies at `a["place"]` |
| `back` | | lying with its back turned (the hold after the turn) | `ka.old_dog(ink, 425, 394, 0.78, 1, "back")` |
| `look_over` | `p` | head up (0..0.4) and turned to look over its shoulder (0.4..0.62) | `ka.old_dog(ink, 425, 394, 0.78, 1, "look_over", p=p)` |
| `let_pass` | `p` | still looking back: tail lifted off the place (0..0.45), hindquarters tucked aside (0.3..0.75), head forward and down, eyes closed (0.7..1) | `ka.old_dog(ink, 425, 394, 0.78, 1, "let_pass", p=p)` |
| `turn_round` | `p` | `turn_back` undone: turns round again to face the first way | `ka.old_dog(ink, 425, 394, 0.78, 1, "turn_round", p=p)` |
| `rise` / `lie_down` | `p` | lying to standing, and back (arrival, 93.2..95.0) | `ka.old_dog(ink, 425, 394, 0.78, 1, "lie_down", p=p)` |
| `wait` | | stands (the print as Bewick cut it) | `ka.old_dog(ink, 120, 392, 0.78, 1, "wait")` |
| `walk` | `t` | stiff slow walk, legs swinging on their pins | `ka.old_dog(ink, x, 392, 0.78, 1, "walk", t=t)` |
| `swim` | `t` | paddles | `ka.old_dog(ink, x, y, 0.78, 1, "swim", t=t)` |

Options: `paper` and `ink_color` are the card and the printing ink (dim both for dusk; frost = lighter
paper). `eye=0` forces the eye shut. `verso=True` shows the unprinted side of the card when its back is
turned (a kept branch, not the default: it reads as a blank dog, see the last row of the sheet).
Extra anchors: `chin`, `rump`, `place` (where a reel would be laid behind it), `turned`, `foraged`.

The defining passage (board 6.5), in its calls:

```python
X, Y, S = 425, 394, 0.78
if   t < 162.5: ka.old_dog(ink, X, Y, S, 1, "lie")
elif t < 164.0: ka.old_dog(ink, X, Y, S, 1, "lift_head", p=ramp(t, 162.5, 164.0))
elif t < 165.5: ka.old_dog(ink, X, Y, S, 1, "look", p=0.0)                    # the hold: nothing moves
elif t < 168.0: ka.old_dog(ink, X, Y, S, 1, "turn_back", p=ramp(t, 165.5, 168.0))
elif t < 171.9: ka.old_dog(ink, X, Y, S, 1, "back")
elif t < 172.4: ka.old_dog(ink, X, Y, S, 1, "look_over", p=ramp(t, 171.9, 172.4))
else:           ka.old_dog(ink, X, Y, S, 1, "let_pass", p=ramp(t, 172.4, 173.0))
```

## Evidence

MEASURED (by `selfcheck()`, run on this revision):
- herder: no joint leaves its limits in any action; every planted paw reaches its contact (worst miss 0.0 units).
- digger: worst wire-length residual 0.078 % (tolerance 1 %); pinned paws drift 0.0.
- old dog: at rest the hinge matrices are the identity and the cut pieces reproduce the scan inside the
  dog (mean absolute difference 0.59 grey levels of 255 over 53,551 pixels; the difference is the shaded
  cut edge).
- cost per call at film size: herder about 5 ms, digger about 9 ms, old dog about 40 ms for a new pose
  and near nothing for a repeated one (cached).

STRUCTURAL: the three dogs share no drawing code: filled card polygons, solved wires, a transformed scan.

JUDGED, by the builder only, from stills (the three sheets, enlarged crops, and one 960x540 mock with a
black-silhouette version). No playback was watched and no independent critic has looked. In stills the
three read as three makes and the old dog is the largest and lowest shape.

UNKNOWN / weak, for the critic:
- No motion has been watched. The herder's twos, the old dog's 8 poses a second in `walk` and `swim`, and
  the dig rhythm are untested at speed.
- The old dog's blink and closed eye are about 2 px at `s=0.78`; they will only read in a closer framing.
- `look_over` flips the head piece about the neck pin. It reads as "looking back" in stills; at speed the
  flip may pop.
- The lying old dog's tail keeps Bewick's curl, so "tail across the place" is a curl on the boards, not a
  straight tail.
- The digger's fore paws overlap when it stands; standing still it can read as a trestle from far away.
- In `carry` the herder's head is bowed over the pages and loses some of its profile.
- The board asks for the old dog's head at x = 350 "facing right" with the tail at x = 500; those disagree.
  `facing` covers either; the example above uses nose toward the water.
