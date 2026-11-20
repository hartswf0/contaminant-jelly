# cam.py · the camera rig for the making films

`films/cam.py` turns finished pictures into camera moves. Every function takes PIL images (RGB or RGBA,
normally 960x540; other sizes are scaled to cover, except where a bigger picture is the point) and
returns **one 960x540 RGB frame**. Do not edit it; import it.

```python
import sys; sys.path.insert(0, "films")
import cam
from PIL import ImageDraw

def draw(t, ink):
    frame = cam.dive(desk_picture(t), thought_picture(t), 300, 260, cam.key(t, [(4.0, 0), (5.2, 1)], "linear"))
    ink.img.paste(frame)                       # hand the frame to the kit
    ink.d = ImageDraw.Draw(ink.img, "RGBA")    # ...and keep drawing on top (captions, badge)
```

Rules that hold for all of it:

- **Pure.** No randomness, no state. The same inputs give the same frame, so stills and the full render agree.
- **Fast.** 10 to 90 ms a call on this machine (table at the end). Painting the input pictures will cost you more.
- **u is linear time, 0 to 1.** Each move eases itself (and smears by its own speed), so feed it
  `key(t, [(start, 0), (end, 1)], "linear")`. At `u <= 0` you get exactly the first picture and at `u >= 1`
  exactly the second, so a move cuts cleanly against the still shots either side of it.
- **Give a move enough frames.** A dive or a turn wants 0.8 to 1.4 s; a whip 0.3 to 0.5 s; a rise 2 s or more.
- The pictures you pass can change every frame (a hand still writing while the camera dives). Nothing is cached.
- Needs `cv2`, `numpy`, `PIL` (all installed).

Test strips for everything below are in `films/stills/cam/` (`python3 films/cam.py` remakes them and prints
timings). Look at them before you plan a shot.

---

## shoot(layers, x=0, y=0, zoom=1, rot=0, focus=None, shake=0, t=0, dolly=0, aperture=7, bg=PAPER)

The multiplane. `layers` is a list of `(image, depth)` from back to front; an optional third item `(ox, oy)`
shifts that layer's centre. Images may be any size and RGBA. With everything at its default each layer is
drawn 1:1, centred.

- `depth` 1 is the plane the camera is "on" (moves pixel for pixel). 3 is far (moves a third as much).
  0.5 is foreground (moves twice as much).
- `x, y` where the camera looks, in depth-1 pixels from centre. `zoom` is the lens (all layers alike).
  `rot` is roll in degrees (picture turns clockwise).
- `dolly` moves the camera body INTO the scene by that much depth: near layers swell faster than far ones, and
  a layer the camera has passed is gone. `dolly=0.9` with the sheet at depth 1 is a nose away from the paper.
- `focus` is the depth held sharp; other layers blur by `aperture * |depth - focus|` px. Rack it with `key`.
- `shake` handheld drift in px at depth 1, driven by `t` (seconds). 2 to 4 is a child's eye; 0 when stuck.

```python
# over the shoulder: far wall, desk, the sheet, and a sleeve close to the lens; focus pulls from sleeve to sheet
layers = [(room, 4.0), (desk_big, 1.6), (sheet_rgba, 1.0), (sleeve_rgba, 0.5)]
frame = cam.shoot(layers, x=cam.key(t, [(0, -260), (3, 240)]), y=40, zoom=1.1, rot=-4,
                  focus=cam.key(t, [(0, 0.5), (1.5, 1.0)]), shake=3, t=t)
```
Strips: `shoot_pan_rack.png`, `shoot_dolly.png`.

### shoot_point(px, py, size, depth, x=0, y=0, zoom=1, rot=0, dolly=0, off=(0, 0))
Where pixel `(px, py)` of a layer image of `size` at `depth` lands on screen for the same camera numbers
(shake not included). Use it to keep a pencil tip, drawn on a nearer layer, on the line it is drawing.

```python
tip = cam.shoot_point(412, 180, sheet_rgba.size, 1.0, x=cx, y=40, zoom=1.1, rot=-4)
```

## tilt(img, deg, horizon=0.5, zoom=1.0, f=900, shift=(0, 0), bg=DESK, shadow=0.35)

Lays a flat picture back in true perspective (a plane hinged about the picture's own centre line, seen by a
lens of focal length `f` px). This is the sheet on the desk seen from the seat.

- `deg` 0 flat-on (a 960x540 picture comes back unchanged); 45 leaning over; 60 to 65 sitting back; 70 nearly
  edge-on.
- `horizon` the eye line as a fraction of frame height. The picture's centre sits on it, and the sheet
  flattens towards it as `deg` goes to 90. 0.35 puts the sheet up the frame with room below for a hand.
- `zoom` size of the sheet. `f` 500 is a wide lens right over the page (steep convergence), 1600 is flat.
- `bg` a colour, a 960x540 picture, or `None` to get the sheet alone as a 960x540 **RGBA** image (to use as a
  `shoot` layer, or to put a cut-paper hand between sheet and lens yourself).
- `img` may be RGBA and bigger than the frame (a whole desktop): it is not scaled down, it covers more desk.

```python
seat = cam.tilt(page, cam.key(t, [(0, 0), (1.5, 62)]), horizon=0.36, zoom=0.85, f=700, bg=wood)
```
Strips: `tilt.png` (0 to 70 degrees), `tilt_seat.png` (a big desk, wide lens, coming down into the seat).

### tilt_point(px, py, deg, horizon=0.5, zoom=1.0, f=900, shift=(0, 0), size=(960, 540))
Where pixel `(px, py)` of the flat picture lands on screen after `tilt` with the same numbers. This is how the
hand finds the word it is writing, and how you find the drawn ring to dive into.

```python
ring_x, ring_y = cam.tilt_point(480, 250, 62, horizon=0.36, zoom=0.85, f=700, size=page.size)
```

## dive(a, b, cx, cy, u, spin=0, power=16)

Fly from picture `a` into the point `(cx, cy)` and arrive in picture `b`. `a` swells `power` times and streaks
outward from the point, the point drifts to the middle of the frame as you lean in, and `b` opens out of the
point (small and whole at first, in a soft-edged disc) until it is the frame. `spin` is degrees of roll on the
way in; `b` lands upright. 0 is a push, 90 to 180 is falling into the page.

```python
u = cam.key(t, [(6.0, 0), (7.1, 1)], "linear")
frame = cam.dive(seat, thought_world, ring_x, ring_y, u, spin=40)      # into the drawn ring
frame = cam.dive(seat, thought_world, ring_x, ring_y, 1 - u2)          # ...and back up to the desk
```
The return trip is the same call with `1 - u`. Strips: `dive.png`, `dive_spin.png`.

## turn(a, b, u, axis='y', direction=1, side=None, blur=1.0)

The camera turns round 180 degrees. It stands in the middle of a square room: `a` is the wall in front, `b` the
wall behind, and a 90 degree lens pans across the wall between. `a` is foreshortened as it swings away, the
room's corner crosses the frame, the middle smears with the speed of the turn, and `b` swings in foreshortened
from the other side.

- `axis='y'` looks round sideways; `axis='x'` tips forward and over (down at the page, then up and out).
- `direction` 1 turns right (or down), -1 the other way.
- `side` a 960x540 picture for the wall you pass (the riveted inside of the tin, a row of desks). Default is a
  dim smear from `a`'s edge colours to `b`'s.

```python
# the first friend: landed inside the tin facing the back wall, turn round to look out through the glass
frame = cam.turn(tin_back_wall, view_out_of_porthole, u, side=tin_side_wall)
# the next friend: out in the river, swing round to look back at the small tin
frame = cam.turn(open_water, tin_seen_from_river, u, direction=-1)
```
Strips: `turn_y.png`, `turn_x_side.png`.

## whip(a, b, u, direction=1, axis='x', blur=1.0, gap=0.6)

Whip pan. `a` and `b` stand side by side with `gap` frame-widths of nothing between (their facing edge colours,
smeared). The frame leaves `a` slowly, tears across, settles on `b`; each frame is smeared by how far the lens
moved, so the middle is pure streak. `direction` 1 pans right/down, -1 left/up. `axis='y'` is eyes up from the
desk to the board, or down again. `blur=0.4` is only a quick pan.

```python
frame = cam.whip(pilot_desk, friend_desk, cam.key(t, [(20.0, 0), (20.45, 1)], "linear"))   # the pass
```
For a pass where the new child first sees the sheet upside down, make `friend_desk` with the sheet rotated
(or run `shoot(..., rot=180)` on it) and whip to that; then un-rotate with `shoot` while they work it out.
Strips: `whip.png`, `whip_up.png`.

## rise(a, b, u, box=(x0, y0, x1, y1), tip=26, sway=5)

Crane up and away. `b` is the wide picture (the whole room) and `box` is where `a` (one desk) belongs in it. At
`u=0` the frame is exactly `a`; as the camera lifts, `a` shrinks to its place with `b` spreading round it
rigidly, as one picture. On the way the camera tips back (`tip` degrees at the middle) and rolls (`sway`), then
levels. At `u=1` the frame is exactly `b`, so **paint `a` small into `b` at `box` yourself** or the desk blinks
out on the last frame. Keep `box` about 16:9.

```python
box = (380, 300, 540, 390)
room = whole_room(t); room.paste(desks.resize((160, 90)), box[:2])
frame = cam.rise(desks, room, cam.key(t, [(84, 0), (88, 1)], "linear"), box=box)
```
Strip: `rise.png`.

## through_glass(inside, outside, cx, cy, r, u, far=0.45, tint=(196, 226, 226))

Push through a round window. `inside` is a picture with a round window at `(cx, cy)`, radius `r` (paint the
brass rim there yourself); `outside` is what is beyond. The inside swells about the window until the rim has
passed the frame edges, while the far-off outside hardly grows until the end. The hole carries a pane: a faint
tint, a sliding shine, the rim's shadow, all thinning as the lens goes through. At `u=1` the frame is `outside`.

- From `u=0` the hole shows `outside`, so use it from a shot where that is already what is in the window.
- `far` smaller means farther: at the start only the middle `far` of the outside's height shows in the window.
- `tint=None` for an open hole (the drawn ring on the page has no glass).
- Works both ways: out of the tin into the river, or from the river in through the porthole of the small tin.

```python
frame = cam.through_glass(tin_inside, river, 480, 265, 212, u)                 # Turkey's seat -> the river
frame = cam.through_glass(river_with_tin, tin_inside, 700, 180, 60, u)          # the trout's side -> back in
```
Strips: `through_glass.png` (big window), `through_glass_small.png` (small window in a corner).

## blink(img, u, to=None, lid=LID, shut=0.12)

An eyelid closing and opening. `u` 0 to 0.5 the curved, out-of-focus lids come together (upper one further)
while the picture dims and softens; it is dark round 0.5; 0.5 to 1 they open. `to` is a second picture to open
the eyes ON. Hold `u` at 0.5 for as long as the eyes stay shut.

```python
u = cam.key(t, [(9.0, 0), (9.25, 0.5), (10.4, 0.5), (10.7, 1)], "linear")      # shut, hold 1.15 s, open
frame = cam.blink(seat, u, to=what_she_pictures)
```
Strips: `blink.png`, `blink_to.png`.

## thought(desk, inner, cx, cy, r, u, wobble=0, t=0, dim=0.16, ring=GRAPHITE)

The `inner` picture seen in a soft-edged, pencil-ringed opening over the `desk` picture, growing from a point
at `(cx, cy)` to radius `r` (a small overshoot, then it settles). The middle of `inner` is shown, scaled so its
height fits the ring. The ring is two passes of a not-quite-round graphite line with skips, drawn round as the
thought opens. The desk dims a little under it.

- Run `u` back down and the thought closes. A thought that falls apart: take `u` to 1, then to 0.15, then up
  again with a different `inner`.
- `wobble` px of unsteadiness in the ring (0 calm; 4 to 8 for a child who is not sure).
- `t` seconds: the ring re-draws 8 times a second (a boiling line). Leave 0 for a still ring.
- To go all the way in, follow with `dive(thought_frame, inner, cx, cy, u)`.

```python
u = cam.key(t, [(12, 0), (12.8, 1), (14.5, 1), (14.9, 0.15), (15.6, 1)])
frame = cam.thought(seat, staged_ending(t), 620, 210, 130, u, wobble=6, t=t)
```
Strips: `thought.png`, `thought_wobble.png`.

## key(t, [(time, value), ...], ease='smooth')

Keyframes for any number or (nested) tuple. Holds the first value before the first key and the last after the
last. `ease`: `'linear'`, `'smooth'`, `'smoother'`, `'in'`, `'out'`, `'hold'` (stay on the earlier value until
the next key: the stuck pencil), `'back'` (overshoot and settle), or any function 0..1 -> 0..1. A key may carry
its own ease as a third item, used for the segment that arrives at it.

```python
x      = cam.key(t, [(0, -200), (3, 120), (6, 120), (6.4, 400, "in")])
pos    = cam.key(t, [(0, (100, 400)), (2, (480, 260))], "out")                 # tuples work
u_move = cam.key(t, [(10.0, 0), (11.2, 1)], "linear")                           # what the moves want
```

## Small helpers

- `cam.fit(img, bg=PAPER)` any PIL image to a 960x540 RGB PIL image (RGBA laid on `bg`, other sizes cover-cropped).
- `cam.smooth(x)` smoothstep, clamped.
- `cam.W, cam.H` 960, 540. `cam.DESK`, `cam.PAPER`, `cam.GRAPHITE`, `cam.LID` colours.

## Chaining moves (the three journeys)

```python
# pilot: seat -> into the ring -> back out
seat = cam.tilt(page, 62, horizon=0.36, zoom=0.85, f=700, bg=wood)
rx, ry = cam.tilt_point(480, 250, 62, horizon=0.36, zoom=0.85, f=700, size=page.size)
f = cam.dive(seat, pictured, rx, ry, u_in)            # then hold on `pictured`, then
f = cam.dive(seat, pictured, rx, ry, 1 - u_out)

# first friend: into the ring, land in the tin facing the back, turn round, look out
f = cam.dive(seat, tin_back, rx, ry, u1, spin=30)
f = cam.turn(tin_back, tin_front_with_porthole, u2, side=tin_side)
# (a long look out; the pilot's drawing is now outside the glass)

# next friend: out through the glass, swing round in the water, look back at the small tin
f = cam.through_glass(tin_front_with_porthole, open_water, 480, 265, 212, u3)
f = cam.turn(open_water, river_with_small_tin, u4, direction=-1)
# back: in through the small tin's porthole, then up out of the page
f = cam.through_glass(river_with_small_tin, tin_front_with_porthole, tin_x, tin_y, tin_r, u5)
```
Hold the camera dead still (no `shake`, no move) while a child is stuck; let it go when the thought does.

## Timings (ms per 960x540 frame, this machine)

| call | ms | call | ms |
|---|---|---|---|
| shoot, 4 layers, rack focus, shake | 80 | whip | 10 to 20 |
| shoot, 3 layers, dolly | 55 | rise | 25 |
| tilt, frame-sized picture | 30 | through_glass | 40 to 50 |
| tilt, 1920x1080 picture | 70 | blink | 25 |
| dive | 40 to 50 | thought | 15 |
| turn | 40 | key | ~0 |

## Known limits

- `turn`'s default side wall is only a smear; pass `side=` when the turn is slow enough to see it.
- `through_glass` with a window that already fills half the frame: the outside is nearly full size from the
  start, so the move is all rim. Start from a wider shot (smaller `r`) for a longer journey.
- `dive` far into `a` shows `a` at up to 16 times: it is a streak of its colours by then, not detail.
- `tilt` beyond about 75 degrees is clamped at 89 and looks like a line; that is what edge-on is.
- The streaks are averaged exposures: on thin black lines over white, at the very start of a move, faint
  repeats can be seen in a still. They do not read in motion.
