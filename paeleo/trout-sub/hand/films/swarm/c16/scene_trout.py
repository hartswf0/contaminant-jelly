"""c16 · scene_trout · The trout think (board part C, 32.0 to 44.2 s of the film). All from the RIVER side.

C0  0.0 ..  3.0  the pick: blue cross, "Two-headed tin monster", W.; W. drew nothing: one wobbly pencil loop round the
                 choice; the button presses. Behind: the tin with Turkey waving low in its porthole, the twin tin facing
                 it and answering late, the giant three-headed monster whole for the first time, two trout.
C1  3.0 ..  4.2  bolt 4, Probable: BLANK      die face 4 at 6 o'clock on the porthole's brass rim, an empty lit stage
C2  4.2 .. 11.0  bolt 5, Plausible: "Two-headed tin monster fits the submarine."   the two-headed tin thing comes down
                 over the submarine the way one bread-roll tin stacks into the next: skirt in front of the shoulder,
                 behind the porthole flange, rim on rim, one small bounce, a ring of bubbles; Turkey still waving
C3 11.0 .. 12.2  bolt 6, Preposterous: BLANK  die face 6 at 10 o'clock, the same empty lit stage

Times inside this file are FILM seconds (G = t + T0) so the wave, the needle and the bubbles carry straight on from
scene_turkey (the wave started at 13.0, one a second; energy stood at 0.40 and the needle at 3/6 at 32.0).

The rule (Temporal Double, D = 12 frames; every delay is Wd.DT, none tuned by eye): the twin's wing is Turkey's D
frames back, mirrored; the card and each die face arrive as a pencil outline and the painted double lands D frames
later; each needle drop is two ticks D apart; every bubble has its double; the three heads do everything one after
another, D apart; the second trout is on the first one's path D frames behind (its arrival is the "second look" at
the seating); the tin monster's two heads nod D apart when it seats. Cut paper is shot on twos.

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink). Captions are NOT drawn here.
Test:  python3 films/swarm/c16/scene_trout.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

SECONDS = 12.2
CAPTIONS = [
    (4.8, 10.5, "Two-headed tin monster fits the submarine."),
]

T0 = 32.0                                   # this module's start in film seconds
T_C1, T_C2, T_C3, T_END = 35.0, 36.2, 43.0, 44.2
WAVE_T0 = 13.0                              # scene_pilot's wave: Turkey's peaks at x.5, the late ones at x.0

# ------------------------------------------------------------- layout ---
SUB = (318, 282, 0.8)                       # Turkey's tin, centre-left; flip=True: its porthole faces the twin
TWIN = (772, 262, 0.58)                     # the twin tin, facing it
MON = (540, 452, 1.0)                       # the giant three-headed monster's bulk, behind everything
RING = (480, 262, 112, 152)                 # a blank's porthole rim, face on: centre, glass radius, outer radius

# ------------------------------------------------------------------ C0 ---
T_CARD = 32.3                               # card outline; its painted double lands D frames later
T_MARK = (33.0, 34.0)                       # W.'s loop, once round the lettering and the button
T_PRESS = 34.2
CARD = (40, 372)

# ------------------------------------------------------------------ C2 ---
CAM_PORT = 2.3                              # bolt 5 opens close on the porthole (as the blank left it) ...
T_OUT = (36.5, 37.5)                        # ... and eases back to the whole river side
T_DROP = (37.3, 39.0)                       # the two-headed tin monster comes down
T_SEAT = T_DROP[1]                          # rims meet; the second look is at T_SEAT + DT
T_LOOK = 39.3                               # head 0 turns down to the stack; heads 1, 2 follow D, 2 D later
T_IN = (40.3, 41.4)                         # a slow push toward the seam: rim on rim
CAM_SEAM = (400, 262, 1.15)

PEAKS = (32.5, 33.5, 34.5) + tuple(36.5 + k for k in range(6))       # Turkey's wave peaks while he is in view (the last
                                                                     # drop's late tick has settled before the beat ends)
HEADS_AT = ((190, 72), (612, 58), None)     # head joints: clear of where the two tin heads will sit, so all three count
NOTCH = (2.0 / 6) / len(PEAKS)              # 3/6 at 32.0 -> exactly 1/6 after bolt 5


def energy(tt):
    """0.40 where scene_turkey left it; barely off the sill by bolt 5. Only ever goes down."""
    return lerp(lerp(0.40, 0.33, ease(tt, 32.0, 36.2)), 0.2, ease(tt, 36.2, 42.6))


def level(tt):
    return Wd.needle(tt, PEAKS, 3.0 / 6, NOTCH)


def _trout_path(tt):
    """The pair's path: in from the right, then holding on a slow loop; at the seating they dart in for a look
    (the second trout makes the same dart D frames later: the second look)."""
    a = ease(tt, 32.0, 33.2)
    look = ease(tt, T_SEAT - 0.1, T_SEAT + 0.5)
    ph = tt * 3.6
    x = lerp(1040, 826, a) + 66 * math.cos(ph) - 96 * look
    y = 400 + 28 * math.sin(ph) - 6 * look
    return (x, y, 5 * math.sin(ph) - 9 * look)


def _heads(g, tilts=(0, 0, 0)):
    """The giant's three heads, each doing what the one before did D frames earlier; tilts = extra nose-down degrees."""
    out = []
    for k in range(3):
        i = Wd.monster_idle(g, k)
        h = {"tilt": 14 + i["tilt"] + tilts[k], "look": (i["look"][0], i["look"][1] + 2.5 * tilts[k] / 26)}
        if HEADS_AT[k]:
            h["at"] = (HEADS_AT[k][0] + i["dx"], HEADS_AT[k][1] + i["dy"] + 0.5 * tilts[k])
        out.append(h)
    return out


def _river(g, ink, tilts=(0, 0, 0), drop=None, die5=0):
    """The river side: water, the whole monster, the twin, Turkey's tin (and what comes down over it), the trout."""
    Wd.river(ink, g, 0.0, 1)
    Wd.monster(ink, MON[0], MON[1], MON[2], g, heads=_heads(g, tilts), shade=0.18)
    tw = Wd.tin(ink, TWIN[0], TWIN[1] + 3 * math.sin(g * 1.1), TWIN[2], g, **Wd.wave_pose(g, energy, WAVE_T0, twin=True))
    p = Wd.tin(ink, SUB[0], SUB[1], SUB[2], g, flip=True, dial=level(g), **Wd.wave_pose(g, energy, WAVE_T0))
    if drop is not None:
        Wd.tin_monster(ink, SUB[0], SUB[1], SUB[2], g, lift=max(0.0, drop), flip=True, port=p,
                       nod=(6 * Wd.settle(g, T_SEAT), -6 * Wd.settle(g, T_SEAT + Wd.DT)))
    if die5:
        Wd.die_at_bolt(ink, 5, p["port"], p["port_r"], size=32, lit=die5 == 2, outline=die5 == 1, t=g, ring_w=17 * SUB[2])
    for n, tp in enumerate(PEAKS + (31.5, 31.0)):
        Wd.bubble_pair(ink, p["pipe"][0], p["pipe"][1], g, tp, rise=150, size=5.5, drift=8, life=2.0, seed=20 + n)
        Wd.bubble_pair(ink, tw["pipe"][0], tw["pipe"][1], g, tp + Wd.DT, rise=120, size=4.2, drift=6, life=1.8, seed=40 + n)
    if drop is not None:                                        # the ring of bubbles when the rims meet
        ry = SUB[1] - 46 * SUB[2]
        for n, fx in enumerate((-222, -150, -60, 40, 130, 222)):
            Wd.bubble_pair(ink, SUB[0] + fx * SUB[2], ry, g, T_SEAT, rise=110 + 14 * (n % 3), size=5.0, drift=12, life=1.5, seed=60 + n)
    Wd.trout_pair(ink, _trout_path, g, 0.42, pose="look")
    Wd.river_plane(ink, "front", g, 0.0, 1)
    return p


def _pick(G, ink):
    g = Wd.on_twos(G)
    _river(g, ink)
    s = Wd.arrive(G, T_CARD)
    if s:
        d = ramp(G, *T_MARK)
        c = Wd.pick_card(ink, "cross", "Two-headed tin monster", "W.", CARD[0], CARD[1], paint=0.0 if s == 1 else 1.0, drawn=d,
                         pressed=ease(G, T_PRESS, T_PRESS + 0.15) * (1 - 0.6 * ease(G, T_PRESS + 0.35, T_PRESS + 0.6)),
                         lit=ease(G, T_PRESS, T_PRESS + 0.3))
        if T_MARK[0] - 0.35 < G < T_MARK[1] + 0.4:
            x, y, down = Wd.friend_tip(c["mark_kind"], c["mark"][0], c["mark"][1], d, c["mark_scale"])
            off = (1 - ease(G, T_MARK[0] - 0.35, T_MARK[0])) + ease(G, T_MARK[1], T_MARK[1] + 0.4)
            Wd.pencil(ink, x + 330 * off, y + 240 * off, lift=0 if (down and off == 0) else 12)


def _blank(G, ink, n, t_in):
    """An unwritten bolt: the porthole's brass rim face on, its die face on that bolt (outline, then its painted
    double), and nothing at all through the glass or round it."""
    Wd.empty_stage(ink)
    cx, cy, ri, ro = RING
    ring = Wd.brass_ring(ri, ro)
    Wd._comp(ink, Wd.shadow_of(ring.getchannel("A"), 9, 0.45), (cx - ring.width / 2 + 6, cy - ring.height / 2 + 10))
    Wd._comp(ink, ring, (cx - ring.width / 2, cy - ring.height / 2))
    Wd.die_at_bolt(ink, n, (cx, cy), ri, size=50, lit=False, outline=Wd.arrive(G, t_in) == 1, ring_w=ro - ri)


def _bolt5(G, ink):
    g = Wd.on_twos(G)
    lift = 330 * (1 - ease(g, *T_DROP)) - 10 * Wd.settle(g, T_SEAT, 1.0, 3.0, 6.0)          # down, one small bounce
    tl = Wd.doubles(lambda tt: 26 * ease(tt, T_LOOK, T_LOOK + 0.6), g, 3)                   # heads look down in turn
    p = _river(g, ink, tilts=tl,
               drop=lift if g >= T_DROP[0] - 0.2 else None, die5=Wd.arrive(G, T_C2))
    u = 1 - ease(G, *T_OUT)
    v = ease(G, *T_IN)
    cx = lerp(lerp(W / 2, p["port"][0], u), CAM_SEAM[0], v)
    cy = lerp(lerp(H / 2, p["port"][1], u), CAM_SEAM[1], v)
    Wd.camera(ink, cx, cy, lerp(1.0, CAM_PORT, u) * lerp(1.0, CAM_SEAM[2], v))


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    G = t + T0
    if G < T_C1:
        _pick(G, ink)
    elif G < T_C2:
        _blank(G, ink, 4, T_C1)
    elif G < T_C3:
        _bolt5(G, ink)
    else:
        _blank(G, ink, 6, T_C3)
    Wd.badge(ink)


if __name__ == "__main__":
    from kit import Film

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else Path("/tmp/c16_scene_trout")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in args[1:]] or [0.0, 0.4, 0.9, 1.5, 2.1, 2.5, 2.9, 3.1, 3.8, 4.3, 4.6, 4.9,
                                             5.3, 5.8, 6.3, 6.7, 7.0, 7.3, 7.6, 8.2, 9.0, 10.0, 10.9, 11.6]
    captions = "--captions" in sys.argv
    film = Film("c16_scene_trout", SECONDS)

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
    assert abs(level(T_C3) - 1.0 / 6) < 0.004 and abs(level(T0) - 3.0 / 6) < 1e-9
    for f in range(int(T0 * 24), int(T_END * 24)):              # the board's invariant, frame by frame
        assert abs(Wd.twin_wave(f / 24, energy, WAVE_T0) + Wd.wave((f - Wd.D) / 24, energy, WAVE_T0)) < 1e-9
    print("wrote", out / "sheet.png")
