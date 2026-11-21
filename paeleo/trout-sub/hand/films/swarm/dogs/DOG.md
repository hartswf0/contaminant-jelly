# DOG.md · the lead dog (`films/swarm/dogs/dog.py`)

A jointed cut-paper puppet: ribcage, loin, pelvis, neck, skull, muzzle, jaw on a pin, two ears (the near one
torn), red collar with a brass tag, tail, four legs of two bones each with a paw on a pin. Brass brads at
the joints. Descended from `paeleo/threshold` (`stage.js` puppet, `machine.js` mind). Built under
`scion/animation-48.md`: the dog is never ordered; it perceives, decides, then moves, and ears and tail
say so first.

Look before you use it: `dog_sheet.png` (every performance, colour over silhouette) and
`dog_strip_walk / trot / dig / swim / shake / howl / burst / no / sitlie.png`.
Regenerate with `python3 films/swarm/dogs/dog.py` (also runs the self-test).

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import dog

def frame(t, ink):                                   # kit.py Film picture function
    pose = dog.walk(t)
    x = 200 + dog.travel("walk", t) * 0.9            # feet do not slide
    j = dog.draw_dog(ink, pose, x, 400, scale=0.9, facing=1)
    # j["mouth"], j["nose"], j["fn.paw"] ... are screen points
```

## Conventions

- **Units.** One dog unit = one pixel at `scale=1.0`. Standing dog: 100 units to the withers, about 250 nose
  to tail tip, about 150 to the ear tips. `scale=0.8` suits a 960x540 two-shot; `1.6` a close shot.
- **Facing.** `facing=+1` faces right (toward the water), `-1` faces left (toward the door). A fraction
  between is the paper cut-out mid-flip.
- **Anchor.** Ground poses: `(x, y)` is the ground under the middle of the body. Swimming and `burst`:
  `(x, y)` is the middle of the body (the pose carries `"_anchor": "body"`). Force either with `anchor=`.
- **A pose is a flat dict of numbers**, so poses blend. Keys: `cx cy pitch arch twist` (trunk), `neck head
  jaw tongue eye look` (head; `look` 0..1 turns the head back over the shoulder), `ear ear_f` (near torn
  ear, far ear: 0 flat back, 0.7 neutral, 1 pricked, 1.2 hard forward), `tail curl wag`, `turn` (1, or -1
  flipped), `air`, `hold` (1 = the mouth has the thing), `sway`, and per leg `fn ff hn hf` + `x y a` (paw
  contact point and paw angle). Legs are solved by IK with joint limits: a paw that cannot reach falls short.
- **Time.** Every performance is `fn(t, **options)`, `t` in seconds since it began. Cycles loop; one-shots
  hold their last drawing after `dog.DURATION[name]`.

## Drawing

| Function | Arguments | Example |
|---|---|---|
| `draw_dog(target, pose, x, y, ...)` | `target` Ink or PIL image; `scale=1.0`; `facing=1`; `silhouette=False`; `color=None` (silhouette colour); `carry=None` \| `'page'` \| `'part'` \| `'reel'` \| a PIL image; `anchor=None`; `shadow=None` (paper shadow; on in colour); `tint=None, tint_amount=0` (push the colours toward e.g. creek teal); `alpha=1`; `colors={}` (override `dog.COLORS`); `build={}` (override `dog.BUILD` bone lengths, `head`, `ear`, `tail`); `brads=True`; `keep_collar=False` (red collar on a silhouette); `texture=True`; `ss=3`. Returns screen points `nose mouth eye head neck collar shoulder hip withers body tail_root tail_tip ear_tip fn.paw ff.paw hn.paw hf.paw fn.elbow fn.wrist hn.knee hn.hock`, `head_angle`, `bbox`. | `j = dog.draw_dog(ink, dog.watch(t), 620, 410, scale=0.9, facing=-1)` |
| `solve(pose, carry=None, build=None)` | Pose to rig: `{'parts': [(name, points, colour key, edged, holes)], 'joints': {...}}` in dog units, y up. For your own renderer. | `rig = dog.solve(dog.sit(2))` |
| `body_point(pose, x, y, scale=1, facing=1, anchor=None)` | Screen position of the middle of the body. | `bx, by = dog.body_point(dog.walk(t), x, y, 0.8)` |
| `blend(a, b, w)` | Pose a toward pose b. `w` a number, or `{'ears':..,'tail':..,'head':..,'body':..,'legs':..}`. | `p = dog.blend(dog.watch(t), dog.sit(9), 0.5)` |
| `draw_bits(target, bits, x, y, scale=1, facing=1, color=(206,232,240))` | Draws particles from `shake_drops` or `dig_spray` at the dog's anchor. | `dog.draw_bits(ink, dog.shake_drops(t), x, y, 0.9)` |

Underwater: `tint=(24, 120, 128), tint_amount=0.35, shadow=False`. Far dogs: `silhouette=True`.

## Performances

`dog.perform(name, t, **options)` calls any of these by name; `dog.PERFORMANCES` is the table.

| Function | What the dog does | Options | Example |
|---|---|---|---|
| `stand(t)` | Neutral, breathing. | | `dog.stand(t)` |
| `watch(t)` | Still, head up, ears pricked, weight a little back; the torn ear flicks every 3.9 s. | `alert=1.0` | `dog.watch(t)` |
| `back_away(t)` | Ears flat and tail tucked first (0.2 s), then low on its haunches, stepping backward, still facing you. | `rate` | `x = x0 + facing*s*dog.travel("back_away", t)` |
| `sit(t)` | Rump down first, lands, chest settles; then holds. | `settle=1.0` | `dog.sit(t - 12.0)` |
| `lie(t)` | Lies down across a sill: elbows first, then hips; at `settle+0.25` s the chin comes down on the paws. Put the sill under the anchor for half in, half out. | `rest=1.0` (0 keeps the head up), `settle=1.1` | `dog.lie(t - 170, rest=1)` |
| `walk(t)` | Four-beat walk, body dips over each landing foot, head nods late. 64 units per cycle. | `rate` (1.15 cycles/s), `phase` | `dog.walk(t)` |
| `trot(t)` | Diagonal pairs with bounce; ears and tail arrive late. 104 units per cycle. | `rate` (2.1), `phase` | `dog.trot(t)` |
| `wade(t)` | High careful steps down into water, head and tail held up. You draw the water over the legs. 50 units per cycle. | `depth=0.5`, `rate` | `dog.wade(t, depth=0.8)` |
| `swim(t)` | Dog paddle, body-anchored; forepaws pull in turn, hind legs kick, ears and tail stream. | `pitch=0` (<0 dives), `rate` (1.3), `effort=1` | `dog.swim(t, pitch=-0.2)` |
| `swim_down(t)` | The crossing down, nose first. | `steep=0.72`, `rate` | `dog.draw_dog(ink, dog.swim_down(t), x, y, facing=1)` |
| `swim_up(t)` | The crossing up, neck stretched to the light. Draw `facing=-1` to rise to the left. | `steep=0.85`, `rate` | `dog.draw_dog(ink, dog.carry_page(t, gait="swim_up"), x, y, facing=-1, carry="page")` |
| `wait_float(t)` | Holding still under the ice, hardly paddling, looking up. | `pitch=0.25` | `dog.wait_float(t)` |
| `dig(t)` | Tail up and ears forward first, chest down, rump up, forepaws raking in turn (fast pull, slower lifted reach), shoulders taking the jolt. | `rate` (3 strokes-pairs/s) | `dog.dig(t)` with `dog.dig_spray(t, water=True)` |
| `nose_page(t)` | Ears hard forward, leans in, sniffs (0.5-1.6 s), holds dead still (1.6-2.4 s), then ear flick, nod, tail: it has decided. 3.0 s. | `reach=1.0` (higher = nose higher) | `j = dog.draw_dog(ink, dog.nose_page(t), x, y); board_page_at = j["nose"]` |
| `take_page(t)` | Head tips, jaw opens slowly, reaches, closes soft, draws back. `pose["hold"]` is 0 until 0.95 s, then 1: `carry="page"` only shows once it is held. 1.8 s. | | `dog.draw_dog(ink, dog.take_page(t), x, y, carry="page")` |
| `carry_page(t)` | A gait with the head level and still. | `gait='walk'` \| `'trot'` \| `'stand'` \| `'swim'` \| `'swim_up'` \| `'swim_down'` \| `'wade'` + that gait's options | `dog.carry_page(t, gait="swim_up")` |
| `carry_part(t)` | Heavy: head low, dipping with each step. | `gait='walk'` | `dog.draw_dog(ink, dog.carry_part(t), x, y, carry="part")` |
| `carry_reel(t)` | Head high, tail high, proud. | `gait='trot'` | `dog.draw_dog(ink, dog.carry_reel(t), x, y, carry="reel")` |
| `holding(pose, kind)` | Modifier: opens the jaw for `'page'`, `'part'` or `'reel'` on any pose. | | `dog.holding(dog.sit(5), "reel")` |
| `burst(t)` | Up through the surface and down onto the bank: stretched and nose-up, ears pinned, legs gather, forefeet reach, deep landing, up to standing. Body-anchored; position it with `burst_path`. | `dur=1.1` | see below |
| `burst_path(t, start, land, scale, height=120, dur=1.1)` | `(x, y)` of the body during `burst(t)`: from `start` on the surface, over an arc, to standing on ground point `land`. Afterwards draw ground poses at `land`. | | `x, y = dog.burst_path(t, (700, 380), (560, 330), 0.9); dog.draw_dog(ink, dog.burst(t), x, y, 0.9, facing=-1)` |
| `shake(t)` | Braces (ears flat, head down, feet wide), then the shake runs from head to tail; the tail is still whipping when the head has stopped; last ear flick. 1.5 s. | `dur=1.5` | `dog.shake(t)` with `dog.shake_drops(t)` |
| `howl(t)` | Dips with ears back, then the front of the dog rises into it, muzzle to the sky, mouth round; holds with a tremor; comes down ears pricked, listening. 3.0 s. | `dur=3.0` | `dog.howl(t - 86.0)` |
| `ears_down(t)` | Told no: ears fall, then the tail, then the head; the body sags. After 1.1 s nothing moves. | | `dog.ears_down(t - 150)` |
| `turn_back(t)` | Ears flat, head goes round, the cut-out flips (`pose["turn"]` 1 to -1), then it sits, lies or stands with its back to you. 1.8 s. | `down='sit'` \| `'lie'` \| `None` | `dog.turn_back(t - 162, down="lie")` (the old dog) |
| `look_back(t)` | One ear turns, the head comes round and up, holds with ears pricked, turns back. | `hold=1.2` (`None`: stays looking) | `dog.look_back(t - 20, hold=None)` |
| `over_shoulder(pose, amount)` | Modifier: head back over the shoulder on any pose. | `amount` 0..1 | `dog.over_shoulder(dog.walk(t), 1.0)` |
| `lay(t)` | Head down, jaw lets go (`pose["hold"]` becomes 0 at 0.62 s: you draw the thing on the sill from then), head comes up to look at you. 1.4 s. | `low=1.0` (less for a higher sill) | `dog.draw_dog(ink, dog.lay(t), x, y, carry="reel")` |
| `pleased(t)` | Head high, mouth open, tail going hard enough to move the hips, forefeet treading. | | `dog.pleased(t)` |
| `paw_press(t)` | Lifts the near forepaw and presses it on a thing 30 units ahead, weight behind it (down at 0.45 s), holds, takes it back. 1.5 s. | | `j = dog.draw_dog(ink, dog.paw_press(t), x, y); print_at = j["fn.paw"]` |
| `tired(t)` | Legs apart, head hanging, panting with the tongue out, ribs working; the tail does nothing. | | `dog.tired(t)` |

Helpers: `travel(name, t, rate=None)` distance in dog units for `walk`, `trot`, `wade`, `back_away`
(negative) so that `x = x0 + facing * scale * travel(name, t)` keeps planted feet planted;
`shake_drops(t, n=54, seed=3, dur=1.5)` and `dig_spray(t, rate=None, seed=5, water=False)` return
`[(x, y, r, alpha)]` in dog units for `draw_bits`.

## Stringing performances together: `Score`

Stateless, so stills at any `t` match the film.

```python
score = dog.Score([
    (0.0,  "watch"),
    (4.0,  "back_away"),                 # the hand reaches
    (7.5,  "watch"),
    (14.0, "look_back", {"hold": None}), # looks at the water
    (17.0, "howl", {"blend": 0.4}),
])
score.draw(ink, t, x, y, scale=0.9, facing=-1)       # or: pose = score.pose(t)
name, since = score.cue_at(t)                        # which performance, and for how long
```

At every cue the ears change first (0.22 s before the cue time), then the tail (0.15 s before), then the
head, then the trunk with a small anticipation and overshoot; the feet go last. `blend` is the body's
change time in seconds (default 0.5). Do not blend across a ground pose and a body-anchored pose (wade to
swim, swim to burst): cut the score there and move `(x, y)` yourself; `body_point` gives the matching point.

## The decision machine: `DogMind`

A port of `threshold/machine.js`. You never move the dog; you change circumstances.

```python
m = dog.DogMind()                         # starts 3 m out on the porch, watching, trust 0.2
m.set(voice="call", hand="reach")         # the person speaks and reaches
m.step(1 / 24)                            # once per frame
m.state        # 'watch' | 'approach' | 'retreat' | 'lie_down' | 'refuse'
m.x, m.v, m.face, m.trust, m.pressure, m.threat, m.invite, m.reason

frames, events = dog.DogMind.run(
    [(1.0, {"voice": "call", "hand": "reach"}),
     (5.0, {"voice": "none", "hand": "none", "posture": "sit"}),
     (8.0, {"voice": "soft", "hand": "low", "door": "open"})], T=60)
f = frames[int(t * 24)]
pose = dog.DogMind.pose(f)                               # the state's performance, feet following f["x"]
screen_x = door_x + f["x"] * 100 * scale                 # 1 m = 100 dog units; door on the left
dog.draw_dog(ink, pose, screen_x, porch_y, scale, facing=-f["face"])
cues = dog.DogMind.cues(frames)                          # [(t, performance)] for a Score instead
```

| Member | Meaning |
|---|---|
| `DogMind(**over)` | New dog; override any field, e.g. `DogMind(x=2.0, trust=0.5)`. |
| `set(**circumstances)` | `posture` stand/sit, `place` doorway/beside, `door` ajar/open, `voice` call/soft/none, `hand` none/low/reach. |
| `perceive()` | `{px, dist, threat, invite, blocking, clear}`. |
| `decide(p)` | `(next_state, why)`: guards in priority order; danger interrupts a dwell, the rest wait. |
| `step(dt=1/24)` | Memory, trust, pressure, decision, then acceleration-limited movement. |
| `frame()` | Snapshot dict (`t state since x v face trust threat invite pressure heard world`). |
| `DogMind.run(timeline, T, dt=1/24, **init)` | `(frames, events)`. |
| `DogMind.cues(frames)` | Score cues, one per change of state. |
| `DogMind.pose(f)` | Pose for one frame. |
| `PERFORM` | watch→`watch`, approach→`walk`, retreat→`back_away`, lie_down→`lie`, refuse→`turn_back`. |

Calling and reaching builds pressure and the dog backs off, then turns its back; sitting, a low hand, a soft
voice and an open door build trust until it comes and lies across the sill. A dog that has refused warms
more slowly.

## What is checked, and how

- MEASURED (`_selftest`, run on every `python3 dog.py`): bone lengths hold to 1e-6 in every performance; a
  planted walking foot slips less than 0.01 units against `travel`; the machine retreats under call and
  reach, never approaches while pressed, and reaches `lie_down` once the person sits and waits.
- JUDGED by the builder from stills only (pose sheet and strips, colour and silhouette). Not watched at
  speed, not reviewed by an independent critic. Weakest reads: `lie` with the chin down merges into one
  low shape in silhouette (the ears still show); `back_away` hind legs overlap; the tear in the ear is
  clear at scale 0.8 and up, below that the two ears read as one ragged crest.
- UNKNOWN: how the easing feels in motion at 24 fps.
