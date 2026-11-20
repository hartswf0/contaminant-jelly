"""c16 · scene_pilot · the pilot's page (board part A, 0.0 to 20.0 s of the film).

A1  0.0 ..  9.5  the child's drawing is made in pencil, stroke by stroke, on the table (no caption)
A2  9.5 .. 13.0  "A giant three-headed monster."   three heads rise behind the twin tin, one after another
A3 13.0 .. 16.5  "Wave at his twin turkey."        Turkey waves; the identical turkey waves back D frames late
A4 16.5 .. 20.0  "Using up his energy."            each wave drops the air needle; the wave gets lower and slower

Everything comes from world.py (handmade cut paper and pencil strokes); nothing is foraged here.
The porthole's rule (Temporal Double, D = 12 frames): every delay below is Wd.DT, never tuned by eye. The window
scribble is doubled inside world.pilot_drawing; the pencil ring arrives D frames before its brass double; head k
rises k * D frames after head 0; the twin's wing is Turkey's wing D frames back, mirrored; every needle drop is
two ticks D frames apart; every bubble has a double D frames behind it. The cut-paper beats are shot on twos.

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink). Captions are NOT drawn here.
Test:  python3 films/swarm/c16/scene_pilot.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

SECONDS = 20.0
T_A2, T_A3, T_A4 = 9.5, 13.0, 16.5
CAPTIONS = [
    (9.5, 13.0, "A giant three-headed monster."),
    (13.0, 16.5, "Wave at his twin turkey."),
    (16.5, 20.0, "Using up his energy."),
]

# ------------------------------------------------------------------ A1 ---
RING = (400, 440, 1.6)                      # sheet ring centre and scale on the table (WORLD.md's framing)
UNIT = 214 * RING[2]                        # one ring-radius in screen px
BOX = (RING[0] - 0.07 * UNIT, RING[1] - 0.64 * UNIT)        # the child's boxy sub on the table
# The camera goes down into the ring so that the pencil sub lands exactly where the twin tin will hang and is as
# wide as it (the child's box is 0.40 ring-radii wide; the twin tin is 404 * scale wide).
ZOOM_IN = (404 * Wd.SEAT_TWIN[2]) / (0.40 * UNIT)
T_PUSH = (8.7, 9.5)                         # the push-in, after the pencil has left
T_RIM = T_A2                                # the pencil ring is drawn; its brass double lands D frames later
T_PAINT = T_RIM + Wd.DT

# ------------------------------------------------------------ A2 .. A4 ---
T_HEADS = T_PAINT + 0.2                     # head 0 starts to rise; heads 1, 2 follow D and 2 D frames later
RISE = 1.0
WAVE_T0 = T_A3                              # the first wave starts low here; one wave a second, peaks at +0.5
DROPS = (17.0, 18.0, 19.0)                  # the wave peaks of A4: the needle drops on each (two ticks, D apart)
NOTCH = (1.0 / 6) / len(DROPS)              # ... and ends the beat at exactly 5/6
CAM_A3 = (548, 292, 1.45)
CAM_A4 = (400, 322, 1.2)
PEAKS = (13.5, 14.5, 15.5) + DROPS + (19.5,)


def energy(tt):
    """Fresh through A3; waving spends it through A4 (wing only to shoulder height by the third wave)."""
    return lerp(1.0, 0.6, ease(tt, T_A4 + 0.2, 19.2))


def level(t):
    return Wd.needle(t, DROPS, 1.0, NOTCH)


def _table(t, ink):
    cx, cy, sc = RING
    Wd.desk(ink, (40, -60, 930, 620))
    Wd.sheet_ring(ink, cx, cy, sc)
    P = Wd.pilot_progress(t)
    Wd.pilot_drawing(ink, cx, cy, P, sc)
    if 0.25 < t < 9.0:
        x, y, down = Wd.pilot_tip(cx, cy, P, sc)
        if t < 0.6:                                             # comes in from the lower right
            u = 1 - ease(t, 0.25, 0.6)
            x, y, down = x + 420 * u, y + 330 * u, False
        if t > Wd.PILOT_END:                                    # lifts and leaves the way it came
            u = ease(t, Wd.PILOT_END, 9.0)
            x, y, down = x + 520 * u, y + 400 * u, False
        Wd.pencil(ink, x, y, lift=0 if down else 14)
    z = lerp(1.0, ZOOM_IN, ease(t, *T_PUSH))
    if z > 1.001:
        u = (z - 1.0) / (ZOOM_IN - 1.0)
        bx, by = lerp(BOX[0], Wd.SEAT_TWIN[0], u), lerp(BOX[1], Wd.SEAT_TWIN[1], u)     # where the box is on screen
        Wd.camera(ink, BOX[0] - (bx - W / 2) / z, BOX[1] - (by - H / 2) / z, z)


def _seat(t, ink):
    """SEAT frame: copied from world.seat so the heads can rise and the bubbles can pass behind the glass."""
    tt = Wd.on_twos(t)
    waving = tt >= WAVE_T0
    wk = Wd.wave_pose(tt, energy, WAVE_T0) if waving else {}
    tk = Wd.wave_pose(tt, energy, WAVE_T0, twin=True) if waving else {"mirror": True}
    Wd.river(ink, tt, 0.0, 0)
    for k, (bx, hx, hy, fl, bd) in enumerate(Wd.SEAT_HEADS):
        up = ease(tt - k * Wd.DT, T_HEADS, T_HEADS + RISE)       # head k: what head 0 did k * D frames ago
        if up <= 0:
            continue
        i = Wd.monster_idle(tt, k)
        nod = 9 * Wd.settle(tt - k * Wd.DT, T_HEADS + RISE, 1.0, 1.6, 3.0)
        Wd.monster_neck(ink, (bx, 520), (hx + i["dx"] * 0.5, lerp(hy + 300, hy, up) + i["dy"] * 0.5), Wd.SEAT_HEAD_SCALE, bd,
                        10 + i["tilt"] + nod, 4 + 5 * ease(tt - k * Wd.DT, T_HEADS + 0.7, T_HEADS + 1.1) * (1 - ease(tt - k * Wd.DT, T_HEADS + 1.5, T_HEADS + 2.0)),
                        i["look"], fl, k, tt, shade=0.12)
    tw = Wd.tin(ink, Wd.SEAT_TWIN[0], Wd.SEAT_TWIN[1] + 3 * math.sin(tt * 1.1), Wd.SEAT_TWIN[2], tt, flip=True,
                lamp=ease(tt, T_A3, T_A3 + 0.4), **tk)
    Wd.river_plane(ink, "front", tt, 0.0, 0)
    for n, tp in enumerate(PEAKS):                               # a bubble on each wave, and its double behind it
        Wd.bubble_pair(ink, 596, 404, tt, tp, rise=330, size=9, drift=9, life=2.4, seed=n)              # ours, past the glass
        Wd.bubble_pair(ink, tw["pipe"][0], tw["pipe"][1], tt, tp + Wd.DT, rise=120, size=4.5, drift=5, life=1.8, seed=n + 9)   # the twin's, D frames late
    Wd.cabin(ink, tt)
    Wd.air_gauge(ink, Wd.SEAT_GAUGE[0], Wd.SEAT_GAUGE[1], level(tt), Wd.SEAT_GAUGE[2], tt)
    Wd.turkey_back(ink, Wd.SEAT_TURKEY[0], Wd.SEAT_TURKEY[1], Wd.SEAT_TURKEY[2], t=tt, shade=0.16, **wk)
    p3, p4 = ease(t, T_A3, T_A3 + 0.7), ease(t, T_A4, T_A4 + 0.8)
    if p3 > 0:
        # A3: in on the glass, so the wing at the rim and the twin in its little window share the frame;
        # A4: across to the lower left, so the gauge is large with the wing and the twin still in frame.
        cx, cy, z = lerp(W / 2, CAM_A3[0], p3), lerp(H / 2, CAM_A3[1], p3), lerp(1.0, CAM_A3[2], p3)
        Wd.camera(ink, lerp(cx, CAM_A4[0], p4), lerp(cy, CAM_A4[1], p4), lerp(z, CAM_A4[2], p4))


def _pencil_seat(t, ink):
    """T_RIM .. T_PAINT: the camera is down in the ring; the pencil ring that the brass rim will land on."""
    _table(T_PUSH[1], ink)
    Wd.ring_outline(ink, Wd.PORT[0], Wd.PORT[1], Wd.PORT_R, Wd.PORT_R + Wd.RING_W, seed=3)


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    s = Wd.arrive(t, T_RIM)
    if s == 0:
        _table(t, ink)
    elif s == 1:
        _pencil_seat(t, ink)
    else:
        _seat(t, ink)
    Wd.badge(ink)


if __name__ == "__main__":
    from kit import Film

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else Path("/tmp/c16_scene_pilot")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in args[1:]] or [0.4, 1.3, 2.4, 3.1, 3.7, 4.5, 5.4, 6.2, 7.6, 8.5, 9.1, 9.6,
                                             10.1, 10.9, 11.6, 12.6, 13.5, 14.0, 15.5, 16.0, 17.0, 18.0, 19.0, 19.9]
    captions = "--captions" in sys.argv
    film = Film("c16_scene_pilot", SECONDS)

    def frame(t, ink):
        draw(t, ink)
        if captions:
            for a, b, text in CAPTIONS:
                if a <= t < b:
                    ink.caption(text, size=27)
    film.picture(frame)
    frames = []
    for tt in times:
        im = film.frame(int(round(tt * film.fps)))
        im.save(out / f"{tt:06.2f}.png")
        frames.append(im)
    Wd._sheet(frames, 4, out / "sheet.png", scale=0.5)
    print("wrote", out / "sheet.png")
