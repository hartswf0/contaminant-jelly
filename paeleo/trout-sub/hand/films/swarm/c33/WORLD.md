# WORLD.md · the shared pieces of class film c33 (porthole 33 · Salon · "Velvet iris frame around culvert bar shadows")

`films/swarm/c33/world.py`. **Foraged** (Wikimedia Commons, both public domain, recorded in `films/credits/c33.json`,
files in `films/sources/c33/`): Turkey (Audubon, plate 1 of *The Birds of America*) and the brook trout (Denton, 1896),
each cut out of its plate and hinged. The black shadow-theatre fish and the black Turkey are cut from the outlines of
those same two plates. **Handmade in code**: the nine card bars, the stone tunnel (16 separate torn-paper voussoirs,
ruled), the engraved teal ground, the cracks, the fog, the velvet iris, padlock, the orange curl, the house flats,
curtains, the culvert wall and its round picture of light, the tin, the brass porthole, river planes, the pilot's
pencil drawing (98 strokes traced by eye from the child's sheet), buttons, dice, die cup, gauge, pick cards, badge.

```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))        # films/swarm/c33
import world as Wd                                               # world.py puts films/ on sys.path itself (kit, kit_anim)
```
Self-test: `python3 films/swarm/c33/world.py [name-fragment ...]` writes stills to `films/stills/c33_world/` (01 to 19):
look at them first, they show every piece in use. The `_demo_*` functions at the foot of world.py are worked examples.

## Conventions
- Frame 960 x 540; x right, y down. Angles in degrees, **counter-clockwise** on screen (as PIL rotates).
- Every drawing function takes `ink` first: the kit's `Ink` (your `draw(t, ink)` argument). They draw in place, in
  call order (painter's order, back to front). Nothing clears the frame for you; `glow_ground`, `table`,
  `river_backdrop`, `empty_card` fill it.
- `t` is seconds; all motion is a pure function of `t`. Frames cost 0.03 to 0.12 s. First call of a piece builds and caches it.
- `ink.caption(text)` sits at y = 494 (band about y 470..516): keep the action above y 465.
- Places: `Wd.PORT_C = (480, 262)` centre of the glass and of the pencil ring; `Wd.PORT_R = 212` glass radius;
  `Wd.RING_OUT = 262` outer brass radius. `Wd.CANT = 8.0` degrees: the wreck's cant, never changed.
- **Ring units**: centre (0, 0), glass radius 1, y down. `Wd.ring_xy(u, v, c=PORT_C, r=PORT_R)` -> screen.
- Bolts: 1 at twelve o'clock, then clockwise (2 at two, 3 at four, 4 at six, 5 at eight, 6 at ten). `Wd.bolt_xy(n)`.
- `Wd.STAGE` (Turkey's seat): `reflection=(338, 404)`, `reflection_h=250`, `beak=(398, 330)`, `gauge=(856, 452)`,
  `fish=(521, 282)`, `fish_len=158`, `fish_angle=-17`.
- `Wd.RIVER` (river side): `tin_c=(214, 316)`, `tin_scale=0.8`, `bars_x=(520, 610)`, `wall_x=640`,
  `picture=(782, 236)`, `picture_r=150`, `bed_y=440`.
- `Wd.PAL`: palette dict. The law's five: `card` (black card), `teal_hi / teal / teal_dk / teal_ink` (the light),
  `brass`, `velvet / velvet_dk / velvet_hi`, `white` / `sheet`. The one extra colour: `cheeto`. Buttons: `green`,
  `red`, `blue`, `pink`, `hexamber` (`Wd.BUTTONS[kind]`). Also pencil, table, tin, lamp, ivory, badge etc.
- Lettering on screen is only: the two option names on each pick card, the initial "E.", the badge, the word under a
  die (`bolt_label`), "AIR" on the big gauge, and the tin's own "ROLLS" label. Nothing else, and never a child's word.

## The breath clock (the board: one clock for the whole film)
| Call | What |
|---|---|
| `Wd.BREATH_HZ` | 2.0 breaths a second. |
| `Wd.breath(t)` | 0..1: quick gasp in, slower sigh out. Fog pulse, beak, chest, movie flicker all use it already. |
| `Wd.breath_index(t)` | which breath (breath k starts at k / 2 s). Drop the gauge one notch at chosen breaths: `notches = 8 - sum(ease(t, tk, tk + 0.25) for tk in ticks)`. |
| `Wd.shove(t, every=1.0)` | 0..1: a sharp push at the start of every second, then a slump (use it for `shift` too). |

## Turkey (foraged plate, hinged; faces LEFT unless flip)
Moods (`Wd.TURKEY_MOODS`): `calm`, `wave`, `panic`, `freak`, `gasp`, `flap`, `frozen`, and this film's `shove` (both
wings up flat, shoving once a second, breathing between: **the default, he is at the glass in every beat**), `heavy`
(still, beak and chest pumping on the breath clock), `lunge` (neck out, wings high, beak wide). Any pose key can be
overridden by keyword: `neck, wattle, beak, eye, wing, ruff, shake, blur` (e.g. `wing=88, beak=30`).
| Call | What |
|---|---|
| `Wd.turkey(ink, cx, cy, height=300, mood="calm", t=0, part="bust", flip=False, alpha=1, shadow=0, angle=0, **over)` | The engraved plate itself. part `bust` (anchor mid neck; height = crest to breast), `head`, `full`. For the table or a close look; on Turkey's side of the glass use the reflection, on the river side the black shape. |
| `Wd.turkey_reflection(ink, cx=None, cy=None, height=None, mood="shove", t=0, alpha=0.8, clip=(PORT_C, PORT_R), **over)` | From his seat: his pale lamp-lit reflection low and left on the inside of the glass (default `STAGE['reflection']`), facing right, clipped to the glass. Move `cx, cy` to make him lunge up the pane. Draw after everything outside and before `fog`. |
| `Wd.turkey_shadow(ink, cx, cy, height=300, mood="shove", t=0, part="bust", flip=False, color=None, alpha=1, blur=0, angle=0, eye=True, **over)` | Turkey as flat black card: the hinged outline only, the eye punched through. `blur` > 0 for a thrown shadow. |
| `Wd.turkey_sprite(mood, t, height, part, **over)` -> `(RGBA, (ax, ay))`; `Wd.turkey_pose(mood, t)` -> dict | For your own compositing. |

Example: `Wd.turkey_reflection(ink, mood="lunge", t=t, cx=372, cy=372)`.

## The tin and its porthole
| Call | What |
|---|---|
| `Wd.seat_frame(ink, c=PORT_C, r=PORT_R)` | **Turkey's seat.** Covers everything except the round glass with the tin's dark riveted inside wall and the six-bolt brass ring, plus the glass's edge shadow and glare. Draw the outside scene full-frame first, then this. Nothing needs clipping to the glass: this hides the overspill. |
| `Wd.tin(ink, c=None, scale=None, t=0, mood=None, glow=1, angle=0, flip=False, shadow=0.7, beam=0, shake=0, alpha=1, dark=0, **over)` | The riveted bread-roll tin side on (body 400 x 190 at scale 1), nose and lamp LEFT (`flip=True`: right; the ROLLS label still reads). `mood` = Turkey's **black shape** in the window against his lamp (None = empty amber glass; `black=False` shows the plate). `dark` 0..1 = the whole tin as a dark hull shape. Returns `{'port', 'port_r', 'lamp', 'nose', 'tail'}` on screen. |
| `Wd.wreck(ink, t=0, c=None, scale=None, mood="shove", sink=0, puff=0, outline=0, glow=1, dial=None, weed_on=True, flip=True, **over)` | **"A ship that sunk."** The tin canted `CANT` degrees, nose (right) down in a mound of silt, a frond of weed on it, a slow thread of bubbles from its seam. `sink` px settles it further, `puff` 0..1 rolls mud off; `outline=1` makes it a dark hull against the light (P4); `dial=5.0` rivets the small air dial beside the porthole. Returns tin's points plus `'dial'`. Defaults put the porthole at about (276, 322), radius 33. |
| `Wd.tin_porthole(ink, c=PORT_C, r=150, mood="shove", t=0, glow=1, shake=0, angle=0, shadow=0.8, **over)` | Looking IN, close (P5): a riveted plate of the tin, the brass ring (glass radius r), amber lamp-light, Turkey's black shape filling the glass, the pilot's cracks mirrored in it. Grow `r` to push in (r=200 fills the frame); `shake` px rocks it. |
| `Wd.silt(ink, x, y, w=260, h=46, puff=0, t=0, seed=0, dark=0)` | A mound of silt, crest at (x, y). |
| `Wd.gauge(ink, notches=5.0, x=None, y=None, r=46, tremble=0, t=0, of=8)` | The air gauge: **8 notches**. 8 full, 5 where the pilot's page leaves it, never show 0. Default place `STAGE['gauge']` (low right). Small dial on the tin: `Wd.gauge(ink, n, *Wd.tin_dial_xy(tp), r=22)` (wreck's `dial=` does this). |
| `Wd.brass_ring(r_in, r_out, bolts=6)` -> RGBA | A turned brass ring if you need another. |

## The pilot's page (table)
| Call | What |
|---|---|
| `Wd.table(ink, sheet=True)` | Wooden table, with the worksheet paper under the ring at PORT_C. Fills the frame. |
| `Wd.sheet_ring(ink, c=PORT_C, r=PORT_R, alpha=1, lit=None)` | The printed ring: two thin circles and six small printed die faces. |
| `Wd.pilot_page(ink, t, c=PORT_C, r=PORT_R, alpha=1)` -> `(tip, pen_down)` | The drawing as it stands `t` seconds into the scene, timed to the board (`Wd.PILOT_TIMES`: bars 1.2 to 4.6, fish 4.7 to 5.85, spots to 6.35, cracks 6.5 to 7.6). Lay the pencil at the returned tip. |
| `Wd.pilot_drawing(ink, done=1.0, c, r, alpha=1, color=None)` -> `(tip, pen_down)` | The same, by fraction 0..1 of pencil travel, or a dict `{group: 0..1}`; groups `Wd.PILOT_GROUPS` = `bar1`..`bar9`, `fish`, `spots`, `cracks`. |
| `Wd.pencil(ink, tip, angle=52, lift=0, length=250, alpha=1)` | A real pencil with its shadow, point at `tip`; `lift` 0..1 raises it. |
| `Wd.porthole_on_table(ink, c=PORT_C, r=PORT_R, drawing=0.45, shadow=0.7)` | The brass ring laid over the page (P4: "the page is carried under the brass porthole"); `drawing` = pencil alpha. Use `table(ink, sheet=False)` under it. |
| `Wd.PILOT_STROKES` | `[{group, pts, weight, len, (wide)}]` in ring units, if you want the raw strokes. |

```python
Wd.table(ink); Wd.sheet_ring(ink)
tip, down = Wd.pilot_page(ink, t)                 # t = seconds from the start of scene_pilot
Wd.pencil(ink, tip, lift=0 if down else 1)
```
What was traced: the bars fan like a hand; bar 1 hugs the left edge; bars 4 and 5 are the dark pressed ones; 8 and 9
the widest, running out past the ring; **bars 2 and 7 are the two thin unshaded uprights**; the fish's outline stops
at bars 5 and 6 and starts again beyond them; nine spots; the cracks.

## The grating (the made thing) and the tunnel
Bars are numbered **1 to 9 left to right**. At the glass's mid height their centres are at x = 303, 323, 367, 412, 470
(bar 5, the centre one, in front of the fish), 540, 596, 623, 687. Leave out **bar 7** for the board's "gap where the
ninth should be, right of centre": the way through between bars 6 and 8 is then 80 px wide.
| Call | What |
|---|---|
| `Wd.bars(ink, only=None, c=PORT_C, r=PORT_R, style="card", slide=None, swing=None, shift=(0, 0), alpha=1, shadow=0.6, v0=-1.12, v1=1.12, color=None)` | The uprights, each its own cut piece. `only=[1,2,...]` picks bars. `style` `card` (black, Turkey's side), `iron` (ruled rusted iron), `shade` (soft shadow bands, colour `color`). `slide={7: f}` slides bar 7 down into place from above (0 out of sight, 1 seated). `swing={k: -1..1}` turns a bar like a gate leaf. Returns `{k: (x_top, x_mid, x_foot)}`. **Draw the fish before the bars.** |
| `Wd.bar_line(k, v, c=None, r=None)` | Bar k at ring height v: `(u, width)` in ring units, or with c, r `(x, width_px)` on screen. E.g. the slot between bars 5 and 6 at v: `(Wd.bar_line(5, v, PORT_C, PORT_R)[0] + Wd.bar_line(6, v, PORT_C, PORT_R)[0]) / 2`. |
| `Wd.crossbar(ink, c, r, v=None, style="card", cant=2, thick=0.05, shift=(0, 0), alpha=1)` -> `y_at(x)` | The one horizontal crossbar (ring height `PILOT_PLACES['crossbar_v']` = 0.60, screen y about 389). Draw before `bars`. `y_at(x)` gives its top edge: hang the padlock, lodge the curl there. (`alpha=0` just to get `y_at`.) |
| `Wd.gate(ink, open_=0, c, r, shift=(0, 0), alpha=1)` | Bolt 3: bars 5 and 6 as the two leaves of a front gate, a small **blank** brass nameplate on one and a letter slot on the other. Use with `bars(only=[1,2,3,4,7,8,9])`. Returns `{'gap': (x_l, x_r), 'plate', 'slot', 'bars'}`. |
| `Wd.stone_ring(ink, done=1.0, c=PORT_C, r=PORT_R, inner=0.80, outer=1.05, n=16, seed=4, shadow=0.7)` | The stone mouth round the bars: 16 separate voussoirs laid one by one clockwise from six o'clock as `done` goes 0 to 1, each sliding in from outside. Works at any c, r (T0: build it on the table round the pencilled circle, then at the porthole). |
| `Wd.tunnel(ink, c, r, hole=0.5, shift=(0, 0), scale=1)` | The tunnel's far plane: ruled coursed wall running back to a far round mouth of radius `hole * r`. `shift` for parallax, `scale` to push in. |
| `Wd.glow_ground(ink, c=PORT_C, r=PORT_R, cant=CANT, dim=1)` | The lit teal ground, engraved with horizontal ruled lines lying at the cant. Fills the frame. |

## The shadow fish, and the engraved trout
| Call | What |
|---|---|
| `Wd.shadow_fish(ink, cx=None, cy=None, length=None, angle=None, flip=False, jaw=0, tail=0, fins=0, t=None, alpha=1, color=None, pins=True)` | The spotted fish as black card (outline of the 1896 plate), spots **punched through** (whatever is behind shows), brass pins. Defaults: where and how the pilot drew it (`STAGE['fish']`, 158 long, nose down-left). Faces left; `flip` right. Pinned limits: `jaw` 0..22, `tail` -26..26, `fins` -30..30. Pass `t=` for an idle swim. No flex, no squash. |
| `Wd.shadow_fish_sprite(length, jaw, tail, fins, color, pins)` -> RGBA | For your own compositing. |
| `Wd.trout(ink, cx, cy, length=220, angle=0, flip=False, phase=0, amp=8, lid=0, eye_roll=None, belly_up=False, alpha=1, shadow=0)` | An engraved brook trout (river side: with its detail). Faces left. `phase` (radians) waves the tail. |
| `Wd.trout_audience(ink, t=0, settle=0, rows=((4, 420, 112), (5, 458, 132)), x0=330, x1=800, lid=0)` -> `[(x, y)]` | Two rows facing the wall, tails idling; `settle` 0..1 lowers them together. The last one returned (right end of the front row) is the spotted fish of the drawing. |
| `Wd.trout_on_circle(ink, c, r, clock_deg, length=150, **kw)` | A trout circling a centre clockwise (clock angle, 0 = twelve). |

## The glass: cracks, air, fog
| Call | What |
|---|---|
| `Wd.cracks(ink, c=PORT_C, r=PORT_R, alpha=1, mirror=False, width=None)` | The pilot's cracks, always the same places (`Wd.CRACKS`, ring units): the long jagged one with its branch, the low arc, two short ones at the right, two light ones from the top. `mirror=True` from the river side. They never spread. |
| `Wd.crack_points(c, r, mirror=False)` | The six leak points on screen. |
| `Wd.crack_bubbles(ink, t, c, r, strength=1, since=0, mirror=False, breaths=4)` | A bead of bubbles from every crack at every breath, rising. `since` = scene start time (no bubbles from earlier breaths). |
| `Wd.fog(ink, level=0.2, t=0, c, r, at=None, wipes=None, pulse=1)` | Breath on the inside of the glass, blooming from `STAGE['beak']`. `level`: 0.15 thin bloom, 0.5 half the glass, 0.9 nearly to the far cracks; each breath pulses on top. Raise `level` a little over each beat. `wipes=[(points, width_px), ...]` wipes clear streaks (the wing sliding down the pane). |
| `Wd.bubbles(ink, origin, t, t0=0, n=7, rise=120, spread=16, size=6, ...)` | A puff of n bubbles that left `origin` at `t0`. |

## The velvet iris (every scene change)
`Wd.iris(ink, f, c=PORT_C, r=PORT_R, leaves=9, twist=46)`: nine velvet-paper leaves, each tucked under the next, with
cut edges and shadows; `f` 0 = open (draws nothing), 1 = closed to a point. On Turkey's side call it just before
`seat_frame` (or pass `iris_f=` to `seat_scene`). To close the whole frame (table, river side) pass `r=600`.
```python
f = ease(t, a, a + 0.2) if t < a + 0.2 else 1 - ease(t, a + 0.2, a + 0.4)     # close, swap the scene at a + 0.2, open
```

## Bolt 1 and 2 props
| Call | What |
|---|---|
| `Wd.padlock(ink, x, y, size=30, swing=0, open_=0, alpha=1)` | Black card padlock hanging by its shackle top from (x, y); keyhole punched; `swing` degrees; `open_` 0..1. |
| `Wd.shadow_arm(ink, tip, root=None, width=30, bend=0.22, alpha=1)` | "Someone": a blunt two-piece black arm from the right edge of the glass to `tip`, pinned at the elbow. No head, no hand. Returns the elbow. |
| `Wd.cheeto(ink, x, y, size=26, angle=0, t=0, glow=1, fizz=1, alpha=1)` | **One** knobbly orange curl, about 1.8 * size long: glow round it, a collar of fine bubbles streaming up. No bag, no logo, no lettering: never add any. Draw after the fish (it is in front of the fish, behind the glass). |

## Bolt 3: the house (black card flats on planes)
| Call | What |
|---|---|
| `Wd.home(ink, push=0, lamp=0, c, r, planes=Wd.HOME_PLANES, alpha=1)` | Planes back to front: `light` (the lit ruled wall of the room, radius `home_hole(push) * r`, and the black floor), `far` (bed with pillow), `room` (clock, oval frame, kettle on its shelf, fringed lamp; `lamp` 0..1 lights it), `chair` (armchair), `sill` (mat). `push` 0 = small, deep in the far mouth; 1 = pushed right in (multiplane, nearest fastest). Call it twice with different `planes` to put the fish between. Returns `{'r', 'floor', 'bed', 'lamp', 'chair', 'mat'}` on screen (push 1: chair seat (472, 300), lamp (365, 293), bed (536, 321), mat (511, 423), floor y 361). |
| `Wd.home_hole(push)` | Pass to `tunnel(ink, hole=Wd.home_hole(push))` so the far mouth opens round the room. |
| `Wd.flat(ink, name, x, y, scale=1, flip=False, lit=0, alpha=1, angle=0)` | One flat by its floor point: `Wd.FLATS` = `armchair, lamp, clock, kettle, frame, bed, mat`. The portrait in the frame is too small to make out; nothing is lettered. |
| `Wd.curtains(ink, closed=0, c, r, span=0.8, alpha=1, glow=0)` | Two velvet curtains at the tunnel mouth: 0 tied back (brass ties), 1 drawn shut; `glow` 0..1 = the lamp shining through the closed cloth. |

```python
def behind(i):                                         # bolt 3, inside seat_scene's `behind` hook
    Wd.tunnel(i, hole=Wd.home_hole(push))
    h = Wd.home(i, push, lamp=lamp, planes=("light", "far", "room", "chair"))
    Wd.shadow_fish(i, h["chair"][0], h["chair"][1] - 14, 96, angle=0, t=t)
    Wd.home(i, push, planes=("sill",))
    Wd.curtains(i, closed, glow=closed * lamp)
    Wd.gate(i, gate_open)
Wd.seat_scene(ink, t, behind=behind, fish=False, tunnel_on=False, only=[1, 2, 3, 4, 7, 8, 9], notches=n, fog_level=fg, bolt=3)
```

## The river side
| Call | What |
|---|---|
| `Wd.river_backdrop(ink, t=0, shift=0, wall=True, dim=0)` | River planes (water, shafts, far boulders, gravel bed, motes), ruled over like an engraving, and the culvert wall on the right. Fills the frame. `dim` darkens the water. |
| `Wd.river(ink, t, planes=("back","far","bed","motes"), shift=0, calm=False)`, `Wd.weed(ink, x, base_y, height=160, lean=0, t=0, seed=0, ...)` | The raw planes and a clump of weed (put one in the foreground). |
| `Wd.culvert_wall(ink, x0=None, shift=0)` | The flat stone wall (from x 640): the screen. |
| `Wd.river_bars(ink, x0=None, x1=None, n=7, y0=20, y1=None, lean=5, shift=0)` | The culvert bars in iron, standing between tin and wall (x 520..610). |
| `Wd.light_cone(ink, src, c=None, r=None, strength=1, t=0)` | The porthole's cone of light from `src` to the round picture; dims with each breath. |
| `Wd.wall_picture(ink, t=0, c=None, r=None, show=True, mood="shove", dim=0, bar_shadows=True, turkey_h=None, **over)` | **"A movie."** The round picture of light on the wall (centre (782, 236), radius 150): Turkey's huge shadow, hinged and frantic, crossed by the bars' upright shadows; jerks and dims with every breath; `dim` 0..1 fades it. `show=False, bar_shadows=False` = lit and empty (a BLANK bolt). |

## Cards, buttons, dice, labels, ending
| Call | What |
|---|---|
| `Wd.pick_card(ink, c=(480, 262), side="turkey", picked=None, press=0, mark=0, scribble=0, angle=-2, alpha=1, initial=None, lift=0)` | 420 x 230 card. `side="turkey"`: green triangle "Theater curtain", red circle "Stone tunnel"; `side="trout"`: blue cross "Rivet-toothed monster jaw", pink square "Movie projector". `picked="circle"` / `"square"`; `scribble` 0..1 colours the picked button in with pencil; `press` sinks and lights it; `mark` 0..1 pencils the friend's small circle in the dashed ring (**turkey card only; keep `mark=0` on the trout card: nothing was drawn there**). `initial="E."`. Returns `{'ring', 'tip', 'buttons': {kind: (x, y)}}`: lay `Wd.pencil(ink, r['tip'])`. |
| `Wd.button(ink, kind, x, y, r=26, pressed=0, lit=1, alpha=1)` | One controller button: `triangle` green, `circle` red, `cross` blue, `square` pink, `hexagon` amber. `Wd.button_disc(ink, kind, x, y, r=10)` = the flat shape only. |
| `Wd.die_face(ink, n, x, y, size=44, style="ivory", lit=1, angle=0, alpha=1)` | Die face 1..6; `style="print"` = the worksheet's small printed face; `lit=0` grey and dead. |
| `Wd.bolt_label(ink, n, x=74, y=64, size=44, lit=1, word=True, alpha=1)` | The ending's label: die face n with the small word under it (1, 4 Probable; 2, 5 Plausible; 3, 6 Preposterous). Top left by default. `lit=0` for a blank. |
| `Wd.bolt_mark(ink, n, lit=1, die=True, c=PORT_C, r=PORT_R, size=30)` | Lights bolt n on a brass ring at c, r and sits its die on it (`lit=0`: dull, grey die). |
| `Wd.bolt_die(ink, n, c=(480, 268), lit=1, size=64, gap=26)` | A brass bolt with its die beside it, on its own. |
| `Wd.friend_mark(ink, kind, c, size=26, done=1)`, `Wd.round_scribble(ink, c, r=16, done=1)`, `Wd.scribble(ink, c, r=16, done=1)`, `Wd.crayon_ring(ink, c, rx, ry=None, color=None, done=1)` | Pencil marks drawn progressively: a small shape, round-and-round colouring in, zigzag colouring in, a hand-drawn ring. Each returns the pencil point. |
| `Wd.end_porthole(ink, c=PORT_C, r=PORT_R, shadow=0.7, faint=0.8, cant=0)` | The ending: brass ring square on, dark teal glass with the nine bars and cracks faint, nobody behind them. |
| `Wd.die_cup(ink, x, y, height=150, die=True, alpha=1, shadow=0.9)` | Leather cup, foot at (x, y), one die resting inside, not thrown. |
| `Wd.empty_card(ink)` | A blank lit card on the table (spare; the board's blanks use the empty lit wall instead). |
| `Wd.badge(ink, n=33)` | The number badge, top right. **Call it last, every frame.** |

```python
Wd.table(ink, sheet=False); Wd.end_porthole(ink, (480, 232), 180)             # the ending
for n in range(1, 7): Wd.bolt_mark(ink, n, lit=lit[n], c=(480, 232), r=180)   # 1..4 lit in turn, 5 and 6 at 0
Wd.die_cup(ink, 850, 510, 150); Wd.pencil(ink, (640, 500), 12, length=220); Wd.badge(ink)
```

## Ready-made stages (the ONE draw order, kept)
**Turkey's seat**: `Wd.seat_scene(ink, t, behind=None, front=None, only=None, slide=None, fish=True, fish_kw=None,
ring=1.0, tunnel_on=True, cross=True, turkey_kw=None, fog_level=0.2, wipes=None, notches=5.0, bolt=None,
leak_since=0.0, shift=(0, 0), iris_f=0.0, frame=True)` draws, back to front:
`glow_ground -> tunnel -> behind(ink) -> shadow fish -> crossbar -> bars -> front(ink) -> stone_ring ->
crack_bubbles -> cracks -> turkey_reflection -> fog -> iris -> seat_frame -> gauge -> bolt light + bolt_label`.
- `behind(ink)` / `front(ink)`: your callables for things behind the fish (the house) and things outside the glass in
  front of the bars (padlock, arm, curl). `only`, `slide` go to `bars`. `ring` = `stone_ring` done (0 before the pick).
- `turkey_kw` = dict for `turkey_reflection`; `fish_kw` = dict for `shadow_fish`; `fish=False` if you draw it yourself.
- `shift=(dx, dy)` rocks the outside planes (nearest most): e.g. `(3 * Wd.shove(t), 0)`.
- Returns `{'bars': {k: (x_top, x_mid, x_foot)}, 'cross': y_at}`. Then `Wd.badge(ink)` and your caption.
```python
def front(i):                                                    # bolt 1: the last bar goes in, the lock goes on
    y_at = Wd.crossbar(i, alpha=0.0)
    x7 = Wd.bar_line(7, 0.60, Wd.PORT_C, Wd.PORT_R)[0]
    Wd.shadow_arm(i, (x7 + 22, 170)); Wd.padlock(i, x7 + 2, y_at(x7) + 6, 26, swing=14 * math.sin(t * 6))
Wd.seat_scene(ink, t, front=front, slide={7: f}, notches=4.4, fog_level=0.3, bolt=1); Wd.badge(ink)
```
**River side**: `Wd.river_scene(ink, t, movie=True, audience=True, settle=0, dial=5.0, dim=0, mood="shove", cone=1,
tin_on=True, bolt=None, bar_shadows=True, darken=0.35)` draws `river_backdrop -> wall_picture -> wreck -> river_bars ->
light_cone -> trout_audience -> bolt_label` and returns `{'tin', 'trout', 'picture'}`. For a BLANK bolt:
`Wd.river_scene(ink, t, movie=False, audience=False, mood=None, bar_shadows=False, bolt=5)` (wall lit, nothing on it,
no Turkey shape, grey die). `Wd.offscreen(ink)` gives a second canvas if you need two scenes in one frame.

## Known limits (say so rather than work round them silently)
- The child drew seven shaded bars and some thin lines; the board counts nine. Bars 2 and 7 here are the two thin line
  pairs, given a card width of their own so the cage has nine uprights. The pilot drew no crossbar: it is the board's.
- `home` at `push` below about 0.3 is small (the room is 212 px across): the flats read best from push 0.6 up.
- Turkey's full-body silhouette (`part="full"`) is clumsy; use `bust` (the window, the wall) as the demos do.
- The audience trout are seen side on, facing the wall, not from behind.
- Both foraged plates are the same two the earlier films used; nothing new was foraged for the stone, bars or house.
