"""c16 · scene_turkey · Turkey thinks (board part B, 20.0 to 32.0 s of the film). All from Turkey's SEAT.

B0  0.0 ..  3.0  the pick: green triangle, "Pond mirror", B.; B.'s own triangle pencilled; the button presses; one ripple
B1  3.0 ..  4.2  bolt 1, Probable: BLANK      die face 1 at 12 o'clock, an empty lit stage through the glass (no outline first)
B2  4.2 ..  5.4  bolt 2, Plausible: BLANK     die face 2 at 2 o'clock, the same empty lit stage
B3  5.4 .. 12.0  bolt 3, Preposterous: "There is another turkey here."   the answering wing comes up INSIDE the tin,
                 in front of the brass rim; Turkey's head turns to the seat beside him; the camera eases back to
                 two backs at one porthole; the pond shows two turkeys in its window, D frames late

Times inside this file are FILM seconds (G = t + T0) so that the wave, the needle and the bubbles carry straight on
from scene_pilot (the wave started at 13.0 and has one beat a second; the needle stood at 5/6 at 20.0).

The rule (Temporal Double, D = 12 frames; every delay is Wd.DT, none tuned by eye): the twin's wing is Turkey's D
frames back, mirrored; the other turkey in the seat waves on that same late beat; the card and each die face arrive
as a pencil outline and their painted double lands D frames later; each needle drop is two ticks D apart; each
bubble has its double; the three heads tilt one after another, D frames apart; the pond's second turkey shows D
frames after the one in here. Cut paper is shot on twos.

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink). Captions are NOT drawn here.
Test:  python3 films/swarm/c16/scene_turkey.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

SECONDS = 12.0
CAPTIONS = [
    (6.0, 11.5, "There is another turkey here."),
]

T0 = 20.0                                   # this module's start in film seconds
T_B1, T_B2, T_B3, T_END = 23.0, 24.2, 25.4, 32.0
WAVE_T0 = 13.0                              # scene_pilot's wave: one a second, Turkey's peaks at x.5, the late ones at x.0

# ------------------------------------------------------------------ B0 ---
CAM_IN = (400, 322, 1.2)                    # where scene_pilot left the camera (its CAM_A4)
T_BACK = (20.0, 20.7)                       # ease back to the whole seat
T_CARD = 20.3                               # card outline; its painted double lands D frames later
T_MARK = (21.0, 22.0)                       # B.'s triangle: left side, right side, base
T_PRESS = 22.2
T_RIPPLE = T_PRESS + 0.1                    # the pond takes one slow ripple

# ------------------------------------------------------------------ B3 ---
CAM_B3 = (596, 296, 1.32)                   # in on the glass and Turkey: the seat beside him is out of frame
T_OTHER = 26.55                             # the other turkey's wing starts up, to peak on the LATE beat (27.0)
T_HEAD = 27.25                              # Turkey's head: glass drawing -> seat drawing (swapped, never tweened)
T_EASE = (27.5, 28.9)                       # the camera eases back: two backs, one porthole
T_TWO = 27.0 + Wd.DT                        # the pond's window shows two turkeys, D frames after the wing in here
OTHER = (318, 424, Wd.SEAT_OTHER[2])       # the other turkey's shoulder pin: nearer the glass than Wd.SEAT_OTHER, so the gauge stays in view
LIFT = 52                                   # both turkeys sit this much higher at bolt 3, so the low waves clear the caption
T_TILT = 28.3                               # head 0 tilts to look at the second one; heads 1, 2 follow D, 2 D later
SOLO = (20.5, 21.5, 22.5, 25.5, 26.5, 27.5)                 # Turkey's wave peaks while he is the only one waving
DUO = (28.5, 29.5, 30.5)                                    # ... and once there are two: two drops a wave
DROPS = SOLO + tuple(x for tp in DUO for x in (tp, tp + Wd.DT))
NOTCH = (2.0 / 6) / len(DROPS)              # 5/6 at 20.0 -> exactly 3/6 after bolt 3
PEAKS = ((19.0, 5), (19.5, 6)) + tuple((tp, 7 + n) for n, tp in enumerate(SOLO + DUO + (31.5,)))     # (time, seed); the first two are scene_pilot's, still rising


def energy(tt):
    """0.6 where scene_pilot left it; shoulder height and tiring by bolt 3. Only ever goes down."""
    return lerp(lerp(0.6, 0.52, ease(tt, 20.0, 25.4)), 0.40, ease(tt, 25.4, 31.6))


def level(tt):
    return Wd.needle(tt, DROPS, 5.0 / 6, NOTCH)


def _outside(g, ink, occupants=1, tilts=(0, 0, 0), ripples=()):
    """What is beyond the glass: river, the three heads on their necks, the twin tin answering D frames late."""
    Wd.river(ink, g, 0.0, 0)
    for k, (bx, hx, hy, fl, bd) in enumerate(Wd.SEAT_HEADS):
        i = Wd.monster_idle(g, k)
        Wd.monster_neck(ink, (bx, 520), (hx + i["dx"] * 0.5, hy + i["dy"] * 0.5 + tilts[k] * 0.5), Wd.SEAT_HEAD_SCALE, bd,
                        10 + i["tilt"] + tilts[k], 4 + tilts[k] * 0.3, i["look"], fl, k, g, shade=0.12)
    tk = Wd.wave_pose(g, energy, WAVE_T0, twin=True)
    tw = Wd.tin(ink, Wd.SEAT_TWIN[0], Wd.SEAT_TWIN[1] + 3 * math.sin(g * 1.1), Wd.SEAT_TWIN[2], g, flip=True,
                occupants=occupants, **tk)
    Wd.river_plane(ink, "front", g, 0.0, 0)
    for tp, sd in PEAKS:
        four = 4 if tp in DUO or tp > DUO[0] else 2             # two turkeys' worth once there are two
        Wd.bubble_pair(ink, 596, 404, g, tp, rise=330, size=9, drift=9, life=2.4, n=four, seed=sd)
        Wd.bubble_pair(ink, tw["pipe"][0], tw["pipe"][1], g, tp + Wd.DT, rise=120, size=4.5, drift=5, life=1.8, n=four, seed=sd + 9)
    for t0, amp in ripples:
        Wd.ripple(ink, Wd.PORT[0], Wd.PORT[1], Wd.PORT_R, g, t0, amp=amp)


def _pick(G, ink):
    g = Wd.on_twos(G)
    _outside(g, ink, ripples=((T_RIPPLE, 7.0),))
    Wd.cabin(ink, g)
    Wd.air_gauge(ink, Wd.SEAT_GAUGE[0], Wd.SEAT_GAUGE[1], level(g), Wd.SEAT_GAUGE[2], g)
    Wd.turkey_back(ink, Wd.SEAT_TURKEY[0], Wd.SEAT_TURKEY[1], Wd.SEAT_TURKEY[2], t=g, shade=0.16, **Wd.wave_pose(g, energy, WAVE_T0))
    u = ease(G, *T_BACK)
    Wd.camera(ink, lerp(CAM_IN[0], W / 2, u), lerp(CAM_IN[1], H / 2, u), lerp(CAM_IN[2], 1.0, u))
    s = Wd.arrive(G, T_CARD)
    if s:
        d = ramp(G, *T_MARK)
        c = Wd.pick_card(ink, "triangle", "Pond mirror", "B.", 160, 366, paint=0.0 if s == 1 else 1.0, drawn=d,
                         pressed=ease(G, T_PRESS, T_PRESS + 0.15) * (1 - 0.6 * ease(G, T_PRESS + 0.35, T_PRESS + 0.6)),
                         lit=ease(G, T_PRESS, T_PRESS + 0.3))
        if T_MARK[0] - 0.35 < G < T_MARK[1] + 0.4:
            x, y, down = Wd.friend_tip(c["mark_kind"], c["mark"][0], c["mark"][1], d, c["mark_scale"])
            a = 1 - ease(G, T_MARK[0] - 0.35, T_MARK[0])        # in from the lower right ...
            b = ease(G, T_MARK[1], T_MARK[1] + 0.4)             # ... and away again
            off = a + b
            Wd.pencil(ink, x + 330 * off, y + 240 * off, lift=0 if (down and off == 0) else 12)


def _blank(G, ink, n, t_in):
    """An unwritten bolt: its die face on the rim, and nothing through the glass. A blank has no double: the die
    face is there, painted and unlit, from the first frame, so it reads for the whole of its second."""
    Wd.empty_stage(ink)
    Wd.cabin(ink, Wd.on_twos(G))
    Wd.die_at_bolt(ink, n, size=46, lit=False, outline=False)


def _bolt3(G, ink):
    g = Wd.on_twos(G)
    two = g >= T_OTHER
    tl = [16 * ease(g - k * Wd.DT, T_TILT, T_TILT + 0.6) for k in range(3)]                 # heads tilt in turn, D apart
    shim = tuple((T_B3 - 1.0 + 1.3 * k, 2.6) for k in range(7))                             # the pond mirror, rippling slightly
    _outside(g, ink, occupants=2 if g >= T_TWO else 1, tilts=tl, ripples=shim)
    Wd.cabin(ink, g, lit=(3,) if Wd.arrive(G, T_B3) == 2 else ())
    Wd.air_gauge(ink, Wd.SEAT_GAUGE[0], Wd.SEAT_GAUGE[1], level(g), Wd.SEAT_GAUGE[2], g)
    if two:
        # The same cut-out as Turkey, mirrored, on the late beat: its wing crosses IN FRONT of the brass rim and its
        # drop shadow is the contact shadow on the brass and on the gauge. It slides in along the seat as it waves.
        sl = 1 - ease(g, T_OTHER, T_OTHER + 0.9)                # in from the lower left, wing first
        ok = {**Wd.wave_pose(g, energy, WAVE_T0, twin=True), "mirror": True}
        Wd.turkey_back(ink, OTHER[0] - 230 * sl, OTHER[1] - LIFT + 90 * sl, OTHER[2], t=g - Wd.DT, shade=0.16, **ok)
    Wd.turkey_back(ink, Wd.SEAT_TURKEY[0], Wd.SEAT_TURKEY[1] - LIFT, Wd.SEAT_TURKEY[2], t=g, shade=0.16,
                   head="seat" if g >= T_HEAD else "glass", **Wd.wave_pose(g, energy, WAVE_T0))
    s = Wd.arrive(G, T_B3)
    bx, by = Wd.die_at_bolt(ink, 3, size=46, lit=s == 2, outline=s == 1, t=g)
    if s == 1:                                                  # the same outline gone over once more, so it holds on the brass
        Wd.die(ink, 3, bx + 1, by + 1, 46, outline=True, color=Wd.DARK)
    u = ease(G, *T_EASE)
    Wd.camera(ink, lerp(CAM_B3[0], W / 2, u), lerp(CAM_B3[1], H / 2, u), lerp(CAM_B3[2], 1.0, u))


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    G = t + T0
    if G < T_B1:
        _pick(G, ink)
    elif G < T_B2:
        _blank(G, ink, 1, T_B1)
    elif G < T_B3:
        _blank(G, ink, 2, T_B2)
    else:
        _bolt3(G, ink)
    Wd.badge(ink)


if __name__ == "__main__":
    from kit import Film

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else Path("/tmp/c16_scene_turkey")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in args[1:]] or [0.0, 0.4, 0.9, 1.5, 2.1, 2.4, 2.9, 3.1, 3.8, 4.3, 5.0, 5.5,
                                             6.0, 6.5, 6.8, 7.0, 7.3, 7.9, 8.5, 9.0, 9.5, 10.0, 11.0, 11.9]
    captions = "--captions" in sys.argv
    film = Film("c16_scene_turkey", SECONDS)

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
    assert abs(level(T_END) - 3.0 / 6) < 0.004 and abs(level(T0) - 5.0 / 6) < 1e-9
    for f in range(int(T0 * 24), int(T_END * 24)):              # the board's invariant, frame by frame
        assert abs(Wd.twin_wave(f / 24, energy, WAVE_T0) + Wd.wave((f - Wd.D) / 24, energy, WAVE_T0)) < 1e-9
    print("wrote", out / "sheet.png")
