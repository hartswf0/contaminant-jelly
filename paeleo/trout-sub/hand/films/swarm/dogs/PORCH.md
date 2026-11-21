# PORCH.md · the porch at dusk and the waterline (`films/swarm/dogs/porch.py`)

Cut paper with depth: every piece is a polygon cut with a slightly unsteady knife, with one hard paper
shadow under it and an amber rim on the lamp side. Handmade from code; nothing foraged, no type, no
interface. Coordinates are the board's world coordinates (`board.md`, "Shared staging contract").

Look before you use it: `python3 films/swarm/dogs/porch.py <out_dir>` renders 23 stills, one per state
(default `<tmp>/porch_stills`). About 0.11 s a frame for the whole set at F-PORCH.

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import porch, dog

def frame(t, ink):                                   # kit.py Film picture function
    oy = porch.crane(t, 22.0, 24.0, porch.F_PORCH, porch.F_TOWN)      # camera offset, eased
    q = porch.act(t, [(0, "stand"), (6.8, "call"), (9.2, "reach", {"dur": 1.2}), (12.5, "sit", {"dur": 1.5})])
    def on_sill(ink, t, oy):                         # your cast, in world coordinates minus oy
        dog.draw_dog(ink, dog.watch(t), 470, 394 - oy, scale=0.6, facing=1)
    porch.scene(ink, t, oy, cast={"sill": on_sill}, q=q, door=0.6, radio_on=1.0 if t > 14.4 else 0,
                rings=[porch.ring(600, 22.0)])
    porch.splash(ink, t, oy, 600, t - 22.0)
```

## Conventions

- **Every drawing function is `(ink, t, oy=0, ...)`.** `ink` is a `kit.Ink` (or a PIL image), `t` seconds,
  `oy` the camera offset: screen y = world y − oy. `F_PORCH = 0`, `F_LAST = 150`, `F_SPLIT = 250`,
  `F_TOWN = 360`. `scene()` rounds `oy` to whole pixels; if you call layers yourself, pass an int.
- **x never moves.** The camera cranes; a push-in is `porch.push()` on the finished frame.
- **Depth.** The sky moves half as far as the world (`SKY_K = 0.5`), so in a crane the moon and the far
  bank sink slower than the hill. Everything else is on the board's plane.
- **Progress arguments are 0..1** (`door`, `freeze`, `breakup`, `crack`, `dusk`, `stars`, `lean`, pose `p`).
  **Ages are seconds since the event** (`splash(age=)`, `drips(age=)`, `spray(age=)`); rings and bubbles take
  the birth time and work the age out from `t`.
- **Dusk.** `dusk` 0 (S1) .. 1 (S6) darkens sky and land by about a fifth. Plates are cached per tenth.
- Constants: `SURFACE 400`, `FLOOR 392`, `DOOR (40,150,170,392)`, `WALL_END 215`, `LAMP (205,140)`,
  `RAIL_Y 300`, `STEP (215,372,300,392)`, `RADIO (285,366)`, `SILL (300,392,560,404)`, `SILL_WET 430`,
  `GATE (304,346,330)`, `STRIP_Y 388`, `MEADOW_X 640`, `DOG_SPOT (470,394)`, `MOON (468,86)`, `FINGER 9`.

## Layers, back to front

`scene()` draws exactly this order. If you compose by hand, keep it.

| # | Layer | Then your cast |
|---|---|---|
| 1 | `sky` | |
| 2 | `water` (the body of the creek, below the line), `porch_legs` | |
| 3 | `hill` (with the pale cow path) | `cast["hill"]`: cows on the path |
| 4 | `bank` (gate, path strip, meadow), `reeds(front=False)` | `cast["strip"]`: cows in the gate, on the strip, in the meadow |
| 5 | `house` (wall, roof, door, windows, deck, step), `projection`, `lamp` | `cast["porch"]`: whoever comes through the door |
| 6 | `radio`, `person`, `sill` | `cast["sill"]`: dogs and things on the sill and the boards |
| 7 | `rail` (+ the person's near arm again if `hand_over_rail`) | |
| 8 | `light`, `moths` | `cast["under"]`: the town, swimmers, bubbles |
| 9 | `surface` (line, water over the wet sill, rings, ice), `reeds(front=True)` | `cast["front"]` |

`light` is drawn after the dry-land cast on purpose: the lamp lies on the dogs and cows too.
`surface` is drawn after the swimmers on purpose: a dog standing on the wet half has its feet under it.

## Functions

| Function | What it draws / returns | Example |
|---|---|---|
| `scene(ink, t, oy=0, cast=None, *, dusk=0, stars=0, door=0.25, inside=1, lamp_level=1, lamp_at=None, q=None, hold_a=None, hold_b=None, hand_over_rail=False, show_person=True, radio_at="step", radio_on=0, pebbles="", puddles=(), rings=(), freeze=0, stamps=(), crack=0, breakup=0, cold=None, reed_lean=0, moth_scatter=0, thrown=None, thrown_amount=0, from_below=None)` | Everything, in order, with `cast` callbacks `fn(ink, t, oy)` in between. `radio_at`: `"step"`, `None` (carried), or `(x, y)`. `from_below=None` turns `look_up` on when the line is within 90 px of the top. Returns the person's screen points. | `porch.scene(ink, t, 0, cast={"strip": cows, "sill": dogs}, q=porch.pose("sit"), radio_on=1, pebbles="wgw")` |
| `sky(ink, t, oy=0, dusk=0, stars=0)` | Violet to amber sky, paper moon with a halo, cut clouds, the far bank (two pale ridges, a tree line, far water). `stars` 0..1 lets 0..14 out (0.07 = one star). | `porch.sky(ink, t, oy, dusk=0.6, stars=0.07)` |
| `hill(ink, t, oy=0, dusk=0)` | The hill behind the house, three folds, dark tufts, fence posts and one tree on the skyline, and the one pale path from the crest to the gate. | `porch.hill(ink, t, oy)` |
| `path_point(u)` | `(x, y, cow_scale)` on the path, u 0 crest .. 1 gate. Scale 0.25 at the crest, 0.9 in the gate. | `x, y, s = porch.path_point(0.4)` |
| `hill_y(x)`, `meadow_y(x)` | Height of the skyline; ground height of the meadow (388 at x 640 to 376 at x 960). | `y = porch.meadow_y(700)` |
| `bank(ink, t, oy=0, dusk=0)` | The bank behind the water: gate (posts at x 304 and 346, the rail folded back and tied to a stake), the pale path strip (hooves at y 388, x 346..640), the meadow with grass. Nothing of the land is drawn below y 400. | `porch.bank(ink, t, oy)` |
| `house(ink, t, oy=0, door=0.25, dusk=0, inside=1)` | Clapboard wall, shingled eave, door casing, transom (lit), sidelight window (lit, curtains), deck boards, step. `door` 0 shut, 0.25 ajar, 1 open; the leaf swings INWARD on its left edge and the lit room shows on the right (floor, table, shelf); light falls out across the deck. `inside` 0..1 is how lit the room is. Returns `{"gap": (x0, x1), "leaf": [...]}` in world coordinates. | `porch.house(ink, t, oy, door=porch.ease(t, 93.2, 94.0))` |
| `lamp(ink, t, oy=0, at=None, level=1, bracket=True)` | The lantern. `at=None`: on its bracket at (205,140). `at=(x, y)`: carried, hanging from that world point. Returns the flame point. | `porch.lamp(ink, t, oy, level=0.8)` |
| `light(ink, t, oy=0, lamp_level=1, door=0.25, inside=1, lamp_at=None, radio_on=0, cold=0)` | The only warm light, screened over what is already drawn above the line: lamp halo, its pool along the boards to x 560, door and window spill, the radio dial. `lamp_at` moves the source (the person holding the lamp out over the ice). | `porch.light(ink, t, oy, door=0.6)` |
| `moths(ink, t, oy=0, scatter=0, n=4, at=None)` | Paper moths round the lamp. `scatter` 0..1 blows them outward (the howl). | `porch.moths(ink, t, oy, scatter=porch.ease(t, 86.2, 86.8))` |
| `sill(ink, t, oy=0, dusk=0, puddles=())` | The one long board, x 300..560: dry warm wood to x 430, wet grey wood beyond, legs into the water. `puddles=[(x, size 0..1)]` are wet patches on the dry half. A dog lies ACROSS it at y 394; "half in, half out" is across x 430. | `porch.sill(ink, t, oy, puddles=[(455, 0.8)])` |
| `porch_legs(ink, t, oy=0, dusk=0)` | The porch's legs going down into the creek and fading. | `porch.porch_legs(ink, t, oy)` |
| `radio(ink, t, oy=0, x=None, y=None, on=0, tilt=0, dusk=0)` | The radio; `(x, y)` is the middle of its base (default: on the step). `on` lights the dial. Returns `handle` and `grille` world points. | `porch.radio(ink, t, oy, on=porch.ease(t, 14.0, 14.4))` |
| `rail(ink, t, oy=0, dusk=0, pebbles="")` | The front rail and balusters (drawn OVER the person) and the pebbles on it: one character per ask, `"w"` white or `"g"` grey, two rows of fifteen. | `porch.rail(ink, t, oy, pebbles="wwgwg")` |
| `pebble_spot(k)` | World point of pebble k, for a hand setting it down. | `x, y = porch.pebble_spot(3)` |
| `pose(name, p=1, t=0, x=None, at=None, at_b=None, standing=False)` | A named pose of the person as a flat dict (see below). `at` is a world point for the near hand, `at_b` for the far hand. | `q = porch.pose("reach", p=0.7, at=(330, 330))` |
| `blend(a, b, w)` | Pose a toward pose b. | `q = porch.blend(porch.pose("sit"), porch.pose("offer"), 0.5)` |
| `act(t, keys)` | A performance: `keys = [(time, name, {options})]`; each pose is reached AT its time after an eased move of `options["dur"]` seconds (default 0.7); other options go to `pose()`. | `q = porch.act(t, [(0, "stand"), (11.0, "stand", {"x": 205}), (12.5, "sit", {"dur": 1.5})])` |
| `shake_head(q, t, shakes=2, dur=1.0)` | Modifier: the head turns away and back, twice. `t` is seconds since it began. | `q = porch.shake_head(q, t - 148.0, 2, 1.0)` |
| `person(ink, t, oy=0, q=None, hold_a=None, hold_b=None, part="all", dusk=0, lamp_at=None, shadow=True)` | The person: a cut-paper figure seen from behind the shoulder, hair in a bun, no face. `hold_a` (near hand): `"film"` (a length held between both hands), `"lantern"`, `"pebble"`, `"reel"` (a plain grey can; draw your own real reel at the returned hand instead). `hold_b` (far hand): `"radio"`. `part="body"` then `rail()` then `part="arm"` puts the hand over the rail. Returns screen points `hand_a hand_b head shoulder hip knee foot bbox`. | `pts = porch.person(ink, t, oy, q, hold_a="film")` |
| `projection(ink, t, oy=0, image=None, amount=1, box=(48,168,164,300))` | What the lamp throws through the held frame onto the door planks: a warm soft rectangle with sprocket holes, and `image` (PIL, dark lines on light: the redrawn teeth) inside it. | `porch.projection(ink, t, oy, teeth_img, porch.ease(t, 145.6, 146.0))` |
| `water(ink, t, oy=0, dusk=0, cold=0, lamp_level=1, shafts=1)` | The body of the creek below y 400, full width: teal, lighter near the line, slow shafts, and the lit door as an amber smear at the upper left. `cold` 0..1 greys it and puts the amber out. Draw it before the town and the swimmers. | `porch.water(ink, t, 360, cold=porch.ease(t, 116.8, 118.0))` |
| `surface(ink, t, oy=0, rings=(), radio_on=0, freeze=0, stamps=(), crack=0, breakup=0, lamp_level=1, cold=0, calm=0, dusk=0)` | The bright line (from the sill rightward; dim under the porch), the inch of water standing over the wet half of the sill (the line there is at y 391), glints (amber near the lamp), rings. Ice: `freeze` 0..1 runs a white slab along the line from the left; `stamps=[(x, p)]` white stars where a hoof lands; `crack` 0..1 runs the crack out from the first stamp; `breakup` 0..1 tips the plates, sinks them and clears the water. `calm=1` stills the line. Draw it last. | `porch.surface(ink, t, oy, freeze=1, stamps=[(610, porch.ease(t, 122.0, 122.15))], crack=porch.ease(t, 122.6, 123.0), breakup=porch.ease(t, 123.0, 124.5))` |
| `ring(x, t0, size=1)` | A ring born at world x at time t0, for `surface(rings=[...])`. Size 0.5 a drip, 1 a dog, 3 to 4 the howl (reaches the right edge). | `rings=[porch.ring(600, 22.0), porch.ring(560, 86.2, 4)]` |
| `ice_plates()` | World x ranges of the plates the ice breaks into, so a hoof can find the plate under it. | `for x0, x1 in porch.ice_plates(): ...` |
| `splash(ink, t, oy=0, x=600, age=0, size=1, kind="in", lamp_level=1, seed=0)` | A dog through the surface: `"in"` a crown falling outward, `"out"` a column thrown up. 1.1 s. Drops near the lamp turn amber. Pair with a `ring`. | `porch.splash(ink, t, oy, 590, t - 59.2, 1.2, "out")` |
| `drips(ink, t, oy=0, x=470, y=360, age=0, wet=1, width=30, floor=None, seed=0)` | Water running off a wet dog from around world (x, y) down to the boards or the line; thins out over 4 s. | `porch.drips(ink, t, oy, 455, 366, t - 60.0)` |
| `spray(ink, t, oy=0, x=470, y=350, age=0, power=1, dur=1.2, seed=0, lamp_level=1)` | The far spray of a shake, flung in every direction, amber where it reaches the lamp. (`dog.shake_drops` is the close spray.) | `porch.spray(ink, t, oy, 455, 356, t - 60.0, power=1.4)` |
| `bubbles(ink, t, oy=0, source=(600,520), t0=0, t1=None, rate=7, seed=0, size=1, hang=None)` | A bubble trail up to the line, where each pops into a small arc. `source` is a world point or `fn(time) -> (x, y)` (the swimmer's mouth). `hang=time` freezes every bubble where it was (under the ice; those at the top flatten against it). | `porch.bubbles(ink, t, oy, lambda te: dog_mouth(te), 22.0, 28.0, hang=118.0)` |
| `reeds(ink, t, oy=0, lean=0, front=False, dusk=0)` | Reeds and cattails. `front=False`: the clump at the meadow's edge (x 640..700) and one at the far right. `front=True`: tall dark blades in the near water at the right. `lean` 0..1 bends them away (the howl). x 560..640 stays clear: that is where a dog goes in. | `porch.reeds(ink, t, oy, lean=porch.ease(t, 86.2, 86.9), front=True)` |
| `look_down(ink, t, oy=0, amp=2.2, depth=140)` | Seen from above: what is under the line swims a little. Call after the swimmers are drawn. | `porch.look_down(ink, t, 0)` |
| `look_up(ink, t, oy=0, amp=2.2, haze=0.3, height=60)` | Seen from below: the strip of dry world above the line (legs, hooves, sill, door) bends and goes teal. Call after the dry cast, before `surface`. | `porch.look_up(ink, t, 360)` |
| `wobble(ink, t, y0, y1, amp=2.5, wave=26, speed=2.2, tint=None, amount=0)` | The tool under both: pushes screen rows y0..y1 sideways in slow waves and tints them. | `porch.wobble(ink, t, 0, 38, 2, 40, tint=(60,150,150), amount=0.3)` |
| `crane(t, t0, t1, oy0, oy1)` | Eased camera offset for a crossing. | `oy = porch.crane(t, 58.0, 60.0, porch.F_TOWN, porch.F_PORCH)` |
| `push(ink, cx, cy, zoom)` | A push-in on the finished frame about screen point (cx, cy). Holds up to about 1.8. | `porch.push(ink, 470, 380, 1 + 0.6 * porch.ease(t, 15.5, 16.8))` |
| `stills(out_dir)` | Renders every state below to PNG. | `porch.stills("/tmp/porch_stills")` |

## The person's poses

`pose(name)`; all face right (toward the water) and blend into each other.

| Name | What it is | `p` | Default place |
|---|---|---|---|
| `stand` | In the doorway, waiting. Use `hold_b="radio"`. Open the door to 0.6 or more so the figure stands against the lit room. | | x 118 |
| `call` | Leans out, chin up, a hand beside the mouth: speaking. | how far into it | x 126 |
| `tap` | Hand on the rail at `at` (default (184, 295)). Use `hand_over_rail=True`. | 1 = hand down, 0 = lifted 12 px. Four taps: `p = 1 - bump` at 6.3, 6.6, 6.9, 7.4 | x 132 |
| `reach` | A step out, weight forward, the arm held low toward the dog, `at` default (318, 318). | how far the hand has come | x 150 to 212 |
| `sit` | Seated on the step beside the door, knees up, hand on knee. | lifts the tapping foot | x 229 |
| `set_radio` | Seated, the far arm reaching down to where the radio goes. Draw `hold_b="radio"` and `radio_at=None` until it is down, then `radio_at="step"`. | 0 knee .. 1 at the step | x 229 |
| `hold_up` | A length of film held up between both hands toward the lamp, head tipped back (`hold_a="film"`). `standing=True` for the standing version at x 196. | 0 lap .. 1 up | x 229 |
| `offer` | Seated, leaning, a low open hand held out at `at` (default (312, 368)) and kept there. | how far out | x 229 |
| `crouch` | Down off the step, one hand flat on the boards at `at` (default (330, 388)). The S3 "something quiet" pose. | | x 270 |
| `kneel` | On the porch edge, arm out at `at` (default (338, 316)); `hold_a="lantern"` and pass the same point to `scene(lamp_at=...)` so the light moves with it. | | x 262 |

## Stills (what was looked at)

`01_stand_ajar 02_call 03_tap 04_reach 05_sit_radio 06_set_radio 07_hold_up 08_shake_head 09_offer
10_crouch 11_door_shut_night 12_door_open 13_splash_in 14_splash_out_spray 15_howl_rings 16_split
17_town_from_below 18_freezing 19_frozen_stamp 20_breakup 21_frozen_porch 22_last 23_medium_on_sill`

## Integration note: where this differs from the board, and what is not known

- **The rail stops at x = 224, not 290** (STRUCTURAL). Carried on to 290 it stood in front of the seated
  person, the step and the radio and hid all three. Pebbles sit at x 36..210 in two rows of fifteen.
- **The sill is drawn 10 px deep on top (y 386..396) with its face to y 407**, so it reads as a board and
  not a line; feet still stand at y 394. The pale path strip is drawn at y 380..390 so the two do not
  merge; hooves at y 388 are on it.
- **The water over the wet half** is drawn as the surface line climbing to y 391 between x 426 and 582
  (`FINGER = 9`), with the board visible through it. Elsewhere the line is at y 400. In front of the dry
  half there is no line: the board's foot stands in the water.
- **The door threshold is at y 384** (the back of the deck); the floor line for feet is 392.
- **Radio colour is green-grey**, not red or cream, so only the lead dog carries those.
- The person is JUDGED readable in ten poses from stills and one twelve-frame strip of `act()` with the
  real lead dog at scale 0.6 on the sill. Motion at speed is UNKNOWN: no playback was rendered. The head
  shake is the least certain: it is carried by the hair line, the bun and the nose bump crossing the head.
- No independent critic has seen any of this. Nothing here is passed.
