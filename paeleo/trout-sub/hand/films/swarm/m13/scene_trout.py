"""m13 · scene_trout · the next friend, M. (board beats M1 to M10, film seconds 57.5 to 79.0; this clock = film - 57.5).

M1   0.0 ..  2.3  the sheet has landed a quarter turn round; two plum hands square it up clockwise; one large
                  lower-case letter on the name line, and the hand goes on to the right while the eye drops (trace 28)
M2   2.3 ..  6.1  the pencil point reads: "The trout think", one plate, the other, back, and hangs between the two
                  for a full second; over the dashed ring, in and out; across to the neighbour's column and back;
                  lightly under "but it fits", and off the end                                 (traces 29, 30, 32)
M3   6.1 ..  6.9  the page flip, to find the pilot's picture
M4   6.9 ..  8.0  dive through the ring into Turkey's seat, already facing out (a smaller, wider porthole)
M5   8.0 ..  9.4  out THROUGH THE GLASS: the two trout slide past either side, the arch goes over, open water
M6   9.4 .. 10.7  the 180 degree turn to the right, in the water
M7  10.7 .. 13.5  the river looking back: the tin, small, a small Turkey in it; two buttons hang near the lens,
                  unlit; neither lights; no trout (we are where they would be); nothing comes      (29, 31)
M8  13.5 .. 14.6  back in through the small tin's porthole
M9  14.6 .. 16.1  up out of the ring to the desk; the page flip back to page 2
M10 16.1 .. 21.5  NOTHING MOVES BUT HER: the camera is dead still. The pencil hangs over the first empty line;
                  once it sinks until it almost touches, and comes up; then the hand opens and lies flat   (31)

There are no captions: she wrote no ending. The scene is the not-writing.

Every seat is a whole picture and every change of seat is a cam.py move (dive, through_glass, turn, tilt). The
desk, its camera (View), the sheet images and Turkey's seat are the first friend's (scene_turkey.py), so the two
desks and the two looks out of the tin join; what is new here is the way out through the glass and the river side.

Exposes SECONDS, CAPTIONS (empty), draw(t, ink); also page2(t) (the sheet, 1520 x 1960; page2(SECONDS) is the
page as the film leaves it), desk_frame(t) and frame(t) for the editor (frame(0.0) is the desk the pass lands on:
page 2 a quarter turn round).
Test:  python3 films/swarm/m13/scene_trout.py [out_dir] [t ...]     writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c13"))
import world as Wd  # noqa: E402   (the c13 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

_spec = importlib.util.spec_from_file_location("m13_scene_turkey", HERE / "scene_turkey.py")
T = importlib.util.module_from_spec(_spec)          # the first friend's desk, sheet and seat (not edited)
_spec.loader.exec_module(T)

W, H = 960, 540
key = cam.key

SECONDS = 21.5
CAPTIONS = []                                        # she wrote nothing; nothing is said

PLUM = "plum"
HAIR = "curly"
WOOD = T.WOOD
S, SIZE, SC, SO = T.S, T.SIZE, T.SC, T.SO
B = T.B
_mid = T._mid

# ------------------------------------------------------------ the sheet ---
T_M = (1.30, 1.72)                    # the one letter
T_ON = (1.72, 2.30)                   # the hand goes on to the right; the eye has already dropped
T_HANG = (3.70, 4.70)                 # between the two plates, touching neither
T_SAG = (5.90, 6.02)                  # the light line under "but it fits"
T_DASH = (6.04, 6.08)                 # and the flick after "fits."
T_FLIP1 = (6.1, 6.9)
T_DIVE = (6.9, 8.0)
T_GLASS = (8.0, 9.4)
T_TURN = (9.4, 10.7)
T_RIVER = (10.7, 13.5)
T_IN = (13.5, 14.6)
T_UP = (14.6, 15.5)
T_FLIP2 = (15.5, 16.1)
T_STILL = 16.1
T_SINK = (18.5, 19.1, 19.35, 19.95)   # down, nearly touching, held, up again
T_FLAT = 20.7                         # the hand opens and lies flat


@lru_cache(None)
def _m_plan():
    nb = B(2, "name2.line")
    return P.write_plan((nb[0] + 26, nb[1], nb[2], nb[3]), "m", 150, T.XH * 1.2)


def _sag():
    """A faint sagging line under the printed words "but it fits" (trace 30)."""
    return [(1068 + 94 * k / 14, 979 + 1.5 * k / 14 + 7.5 * math.sin(math.pi * (k / 14) ** 0.9)) for k in range(15)]


def _dash():
    return [(1172.0, 966.0), (1180.0, 964.5), (1188.0, 963.5)]


def _it_m(img, t):
    if t > T_M[0]:
        plan = _m_plan()
        done, x, y, down = plan.upto(ramp(t, *T_M))
        P.graphite(img, done, max(1.2, plan.xh * 0.15) * 1.04, 1.0, 150)


def _it_sag(img, t):
    if t > T_SAG[0]:
        pts, _ = T._along(_sag(), ramp(t, *T_SAG))
        P.graphite(img, [pts], 3.0, 0.45, 151)


def _it_dash(img, t):
    if t > T_DASH[0]:
        pts, _ = T._along(_dash(), ramp(t, *T_DASH))
        P.graphite(img, [pts], 3.0, 0.45, 152)


ITEMS = [(T_M[1], _it_m), (T_SAG[1], _it_sag), (T_DASH[1], _it_dash)]


@lru_cache(None)
def _base2(n):
    if n == 0:
        return T.page2(1e9)                        # A.'s whole column, as she left it
    img = _base2(n - 1).copy()
    ITEMS[n - 1][1](img, 1e9)
    return img


def page2(t):
    """Page 2 at module second t (1520 x 1960). Do not draw on what comes back. t >= SECONDS: as the film leaves it:
    the left column full, the right column one letter, one faint curve and a dash."""
    n = 0
    while n < len(ITEMS) and ITEMS[n][0] <= t:
        n += 1
    if all(t <= fn_t0 for fn_t0 in (T_M[0], T_SAG[0], T_DASH[0])[n:]):
        return _base2(n)
    img = _base2(n).copy()
    for _, fn in ITEMS[n:]:
        fn(img, t)
    return img


# ------------------------------------------------------- the desk camera ---
View = T.View
RING1 = T.RING1
#        tilt  log zoom        aim (sheet px)   held at (screen)
WIDE = (60.0, math.log(0.62), 760.0, 900.0, 480.0, 236.0)            # the sheet as it lands
NAME = (50.0, math.log(1.45), 1080.0, 560.0, 450.0, 262.0)           # zone 6: the name line
DOWN = (46.0, math.log(1.55), 1100.0, 1120.0, 450.0, 300.0)          # the eye has dropped; the name is out of the top
C2A = (44.0, math.log(1.55), 1010.0, 640.0, 440.0, 262.0)            # "The trout think"
C2B = (44.0, math.log(1.55), 1080.0, 680.0, 440.0, 262.0)            # the two plates
C2R = (44.0, math.log(1.55), 1200.0, 760.0, 440.0, 262.0)            # the dashed ring
C2N = (44.0, math.log(1.50), 860.0, 930.0, 440.0, 262.0)             # the neighbour's column
C2S = (42.0, math.log(1.62), 1080.0, 990.0, 440.0, 262.0)            # "Strange, but it fits."
STILL = (46.0, math.log(1.42), 1040.0, 1050.0, 500.0, 236.0)         # the six empty lines; then it does not move
CAM_KEYS = [(0.0, WIDE), (0.95, WIDE), (1.3, NAME), (1.64, NAME), (2.0, DOWN), (2.26, DOWN), (2.52, C2A), (2.8, C2A),
            (2.98, C2B), (4.7, C2B), (4.92, C2R), (5.05, C2R), (5.3, C2N), (5.65, C2N), (5.85, C2S), (6.1, C2S),
            (6.45, T.FLIP), (6.9, T.RING), (15.5, T.RING), (15.8, T.FLIP), (T_STILL, STILL)]
SHAKE_KEYS = [(0.0, 2.5), (3.6, 2.5), (3.7, 0.0), (4.7, 0.0), (4.85, 2.2), (6.0, 2.2), (6.1, 0.0), (6.9, 0.0), (7.0, 2.0),
              (15.4, 2.0), (15.5, 0.0)]


def view(t):
    if t >= T_STILL:                                 # M10: one fixed eye, no handheld drift, to the last frame
        deg, lz, ax, ay, tx, ty = STILL
        return View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0, 0.0)
    deg, lz, ax, ay, tx, ty = key(t, CAM_KEYS, "smoother")
    return View(deg, math.exp(lz), (ax, ay), (tx, ty), key(t, SHAKE_KEYS, "linear"), t)


HEAD_Y = [(0.0, 600.0), (0.95, 600.0), (1.3, 960.0), (6.1, 960.0), (6.45, 628.0), (6.9, 646.0), (15.5, 646.0), (15.8, 628.0),
          (T_STILL, 712.0)]


def _head(fr, t, tilt=0.0, turn=0.0):
    y = key(t, HEAD_Y, "smoother")
    if y > 900:
        return
    P.head_back(fr, 232.0, y, PLUM, 1.15, tilt=tilt, hair=HAIR, turn=turn, t=t)


def _focus(fr, at, k=1.0, r0=190.0, r1=540.0, blur=3.2):
    """Where the eye is: sharp round `at`, soft away from it."""
    if k < 0.04:
        return fr
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - at[0], (yy - at[1]) * 1.5)
    m = np.clip((d - r0) / (r1 - r0), 0, 1)
    m = (m * m * (3 - 2 * m) * 255).astype(np.uint8)
    return Image.composite(fr.filter(ImageFilter.GaussianBlur(blur * k)), fr, Image.fromarray(m, "L"))


# ----------------------------------------------- where the pencil point is ---
REST = (1130.0, 1330.0)                               # where the pencil waits while she is away in the river
LINE4 = (B(2, "bolt4.1")[0] + 16.0, B(2, "bolt4.1")[3] - 7.0)     # the start of the first empty line
FLAT = (1180.0, 1215.0)                               # where the open hand comes to lie


def pen(t):
    """(sheet point, pose, lift) of M.'s pencil hand. None before she takes the pencil up."""
    pl = _m_plan()
    if t < 1.0:
        return None
    if t < T_M[0]:
        return key(t, [(1.0, (1290, 760)), (T_M[0], pl.start)]), "hover", key(t, [(1.0, 18), (T_M[0], 5)])
    if t < T_M[1]:
        x, y, down = pl.tip(ramp(t, *T_M))
        return (x, y), "write", 0 if down else 6
    if t < T_ON[1]:                                # she goes on writing to the right, rising off the line (trace 28)
        e = ramp(t, *T_ON)
        x0, y0 = pl.end
        return (x0 + 22 + 170 * e, y0 - 4 - 26 * e + 5 * math.sin(e * 19)), "write", 0 if int(e * 9) % 3 else 5
    tt0, tt1 = (824.0, 580.0), (988.0, 580.0)       # under "The trout think"
    pa = (1016.0, 634.0)                            # under "Polite ferry customer"
    pb = (990.0, 699.0)                             # under "Bell-ringer prank"
    mid = (1094.0, 640.0)                           # the gap between the two plates
    rc = _mid(B(2, "draw2.circle"))
    rin, rout = (rc[0] - 6, rc[1] + 8), (rc[0] - 64, rc[1] + 36)
    ov = _mid(B(2, "draw1.circle"))
    ov = (ov[0] + 16, ov[1] + 20)                   # the neighbour's oval
    cz = (792.0, 1066.0)                            # the neighbour's "crazy", over the gutter
    st0 = (980.0, 982.0)                            # under "Strange,"
    sag, dash = _sag(), _dash()
    if t < T_SAG[0]:
        p = key(t, [(T_ON[1], (pl.end[0] + 192, pl.end[1] - 30)), (2.5, tt0), (2.8, tt1, "linear"), (2.95, pa), (3.1, pa),
                    (3.25, pb), (3.4, pb), (3.55, pa), (T_HANG[0], mid), (T_HANG[1], mid), (4.92, rin), (4.99, rin),
                    (5.07, rout), (5.3, ov), (5.4, ov), (5.55, cz), (5.65, cz), (5.8, st0), (T_SAG[0], sag[0], "linear")])
        lf = key(t, [(T_ON[1], 5), (2.4, 15), (2.5, 5), (2.8, 5), (2.87, 11), (2.95, 4), (3.1, 4), (3.18, 11), (3.25, 4),
                     (3.4, 4), (3.47, 11), (3.55, 4), (3.62, 9), (T_HANG[0], 12), (T_HANG[1], 12), (4.8, 15), (4.92, 12),
                     (4.97, 4), (5.0, 4), (5.07, 15), (5.3, 9), (5.4, 9), (5.48, 15), (5.55, 8), (5.65, 8), (5.72, 15),
                     (5.8, 5), (T_SAG[0], 1)])
        return p, "hover", lf
    if t < T_SAG[1]:
        _, p = T._along(sag, ramp(t, *T_SAG))
        return p, "write", 0
    if t < T_DASH[0]:
        return key(t, [(T_SAG[1], sag[-1]), (T_DASH[0], dash[0])]), "write", 5
    if t < T_DASH[1]:
        _, p = T._along(dash, ramp(t, *T_DASH))
        return p, "write", 0
    if t < T_FLIP2[0]:                             # off the end; and the pencil waits in the air while she is away
        p = key(t, [(T_DASH[1], dash[-1]), (6.14, (dash[-1][0] + 46, dash[-1][1] - 14), "out"), (6.6, REST)])
        return p, "hover", key(t, [(T_DASH[1], 1), (6.14, 15), (6.6, 17)])
    if t < T_FLAT:                                 # found hovering; then over the first empty line, and it stays there
        p = key(t, [(T_FLIP2[0], REST), (T_STILL, LINE4)])
        lf = key(t, [(T_FLIP2[0], 17), (T_STILL, 16), (T_SINK[0], 16), (T_SINK[1], 2.5), (T_SINK[2], 2.5), (T_SINK[3], 16)])
        return p, "hover", lf
    return FLAT, "hold", 0


def _hand_t(t):
    """The hand's own clock: it stops dead while the point hangs between the two plates."""
    if T_HANG[0] <= t < T_HANG[1]:
        return T_HANG[0]
    if t >= T_STILL:                                 # M10: the pencil does not move (but for the one sinking)
        return T_STILL
    return t


# ------------------------------------------------------------ desk frames ---
def _left_hold(fr, v, t, p):
    P.hand(fr, *v.pt(p), pose="hold", tone=PLUM, scale=v.hs(p), flip=True, t=_hand_t(t), arm=140)


def _flip(fr_view, t, t0, t1, first, second):
    """The page flip: the eye goes down to the desk's edge, the left hand turns the sheet, the other page comes up."""
    v = fr_view
    half = (t0 + t1) / 2
    lift = 26 * math.sin(math.pi * ramp(t, t0, t1))
    fr = v.render(T._desktop(first if t < half else second, lift=lift))
    e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
    P.hand(fr, e[0], e[1], pose="pass", tone=PLUM, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
    return fr


def desk_frame(t):
    """M.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    if t < 1.0:                                    # the sheet arrived a quarter turn round: two flat hands square it
        u = cam.smooth(ramp(t, 0.1, 0.95))
        ang = 270.0 + 90.0 * u
        fr = v.render(T._desktop(page2(t), angle=ang))
        s = math.sin(math.pi * u)
        a = (SC[0] - 520 + 60 * s, SC[1] + 300 - 330 * s)
        b = (SC[0] + 520 - 60 * s, SC[1] - 40 + 330 * s)
        k = v.hs((760, 980), 1.0)
        P.hand(fr, *v.dpt(*a), pose="hold", tone=PLUM, scale=k, flip=True, t=t, arm=150)
        P.hand(fr, *v.dpt(*b), pose="hold", tone=PLUM, scale=k, t=t, arm=42)
        _head(fr, t, tilt=8 * (1 - u), turn=0.2 * (1 - u))
        return fr
    p, pose, lift = pen(t)
    if t < T_FLIP1[0]:                             # the name; then the pencil point reads
        fr = v.render(T._desktop(page2(t)))
        arm = key(t, [(1.0, 60), (T_ON[1], 60), (2.5, 66), (4.7, 66), (4.92, 60), (5.07, 62), (5.3, 70), (5.65, 70), (5.85, 62)])
        P.hand(fr, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=_hand_t(t), lift=lift, arm=arm)
        if t >= T_ON[1]:
            fr = _focus(fr, v.pt(p), ramp(t, T_ON[1], 2.6))
        _head(fr, t)
        return fr
    if t < T_FLIP1[1]:                             # she turns the sheet over to find the pilot's picture
        fr = _flip(v, t, T_FLIP1[0], T_FLIP1[1], page2(t), T.page1_done())
        P.hand(fr, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=t, lift=lift, arm=60)
        fr = _focus(fr, v.pt(p), 1 - ramp(t, T_FLIP1[0], T_FLIP1[0] + 0.2))
        _head(fr, t)
        return fr
    if t < T_FLIP2[0]:                             # page 1 lies there while she is away
        fr = v.render(T._desktop(T.page1_done()))
        _left_hold(fr, v, t, (250, 1320))
        P.hand(fr, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=t, lift=lift, arm=58)
        _head(fr, t)
        return fr
    if t < T_STILL:                                # and back over to page 2
        fr = _flip(v, t, T_FLIP2[0], T_FLIP2[1], T.page1_done(), page2(t))
        P.hand(fr, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=t, lift=lift, arm=key(t, [(T_FLIP2[0], 60), (T_STILL, 68)]))
        _head(fr, t)
        return fr
    # M10. The camera does not move. Six empty lines.
    fr = v.render(T._desktop(page2(t)))
    _left_hold(fr, v, t, (150, 1330))
    f = clamp((t - T_FLAT) / 0.2)
    if f > 0:                                      # the pencil put down; the hand open and flat on the page
        P.pencil(fr, *v.pt((1395, 1240)), angle=-64, scale=v.hs((1395, 1240), 1.0), lift=6 * (1 - f))
    if f < 1:
        q, _, lf = pen(min(t, T_FLAT - 1e-3))
        P.hand(fr, *v.pt(q), pose="hover", tone=PLUM, scale=v.hs(q), t=_hand_t(t), lift=lf + 10 * f, arm=68, alpha=1 - f)
    if f > 0:
        P.hand(fr, *v.pt(FLAT), pose="hold", tone=PLUM, scale=v.hs(FLAT), t=_hand_t(t), arm=56, alpha=f, lift=12 * (1 - f))
    _head(fr, t)
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------ Turkey's seat, smaller ---
PORT = Wd.PORT_C
R_SEAT = 130                                          # a wider seat shot: more wall, a smaller glass
FAR = (2.0 * R_SEAT / H) / (R_SEAT / Wd.PORT_R)       # so the glass shows the stage whole, as A. left it
OFF = (0.0, float(H / 2 - PORT[1]))                   # the stage's centre (PORT_C) on the lens's axis
FISH = (("fish1", 0.0, -1.0), ("fish2", 1.7, 1.0))    # group, phase, the side it leaves by


def _rgb_ink(t):
    return Ink(t, int(t * 24))


@lru_cache(None)
def seat_inside():
    """The inside of the tin round a smaller glass: the dark riveted wall and the six-bolt brass ring."""
    ink = _rgb_ink(0.0)
    ink.fill((60, 120, 116))
    Wd.seat_frame(ink, PORT, R_SEAT)
    return ink.img.convert("RGB")


@lru_cache(None)
def _set_layer():
    """Everything that stands between the tin and open water (arch, twig, the bell with A.'s red disc, weed), cut
    out from the river behind it."""
    a = _rgb_ink(0.0)
    Wd.river(a, 0.0, calm=True)
    b = _rgb_ink(0.0)
    Wd.seat_stage(b, 0.0, "back", calm=True)
    Wd.bell(b, part="cord")
    Wd.seat_stage(b, 0.0, "front", calm=True)
    Wd.bell(b, part="body", disc="circle")
    ia, ib = a.img.convert("RGB"), b.img.convert("RGB")
    d = np.asarray(ImageChops.difference(ia, ib)).max(axis=2)
    m = Image.fromarray(((d > 5) * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = ib.convert("RGBA")
    out.putalpha(m)
    return out


def _water(t):
    ink = _rgb_ink(t)
    Wd.river(ink, t)
    return ink.img.convert("RGB")


def outside(t, d=0.0):
    """What is beyond Turkey's glass, with the lens `d` deep into it: at 0 the stage as the first friend left it (the
    arch, the bell with its red disc, the two trout in their drawing places); the trout swell and slide out either
    side as we come level with them (d near 1); the arch goes over and round (d near 2); then open water."""
    up = 178.0 * cam.smooth(d / 1.6)                 # the lens sinks a little as it goes: we pass UNDER the bell
    fr = cam.shoot([(_water(t), 4.0, OFF), (_set_layer(), 2.0, (0.0, OFF[1] - up))], dolly=d, bg=Wd.PAL["water_mid"])
    if d < 0.81:
        ink = _rgb_ink(t)
        ink.img.paste(fr)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        s = 1.0 / (1.0 - d)
        for g, ph, side in FISH:
            x0, y0 = Wd.STAGE[g]
            x = 480 + (x0 - 480) * s + side * 165 * (s - 1)
            y = 270 + (y0 + OFF[1] - up - 270 + 4.0 * math.sin(t * 1.3 + ph)) * s
            Wd.trout(ink, x, y, length=150.0 * s, angle=T.PILOT_PL[g + "_angle"] * 0.5, phase=t * 6 + ph, amp=9.0, lid=0.1)
        fr = ink.img.convert("RGB")
    return fr


def seat_view(t):
    """Turkey's seat as M. finds it: the first friend left the camera turned to the glass."""
    return cam.through_glass(seat_inside(), outside(t), PORT[0], PORT[1], R_SEAT, 0.0, far=FAR)


def _depth(u):
    return 2.12 * (0.35 * u + 0.65 * u * u)


# ------------------------------------------------- the river looking back ---
BTN_X = (236.0, 152.0)                                # the blue cross
BTN_S = (806.0, 318.0)                                # the pink square


@lru_cache(None)
def tin_points():
    ink = _rgb_ink(0.0)
    Wd.river_stage(ink, 0.0, "back")
    return Wd.river_stage(ink, 0.0, "front", mood="freak")


def river_back(t):
    """Where the trout are. The arch's foot, the still bell, the bread-roll tin low and small, its brass porthole
    towards us, a small Turkey behind the amber glass (freaking out, as the pilot's page says). No trout: we are
    where they would be. Two buttons hang in the water near the lens, unlit."""
    ink = _rgb_ink(t)
    Wd.river_stage(ink, t, "back", calm=True)
    Wd.river_stage(ink, t, "front", mood="freak", calm=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for kind, (x, y) in (("cross", BTN_X), ("square", BTN_S)):
        Wd.button(_ButtonInk(lay), kind, x, y, r=34, lit=0.0)
    sh = Image.new("RGBA", (W, H), (6, 20, 22, 0))
    sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda q: int(q * 0.45)))
    ink.img.paste(sh, (10, 16), sh)
    ink.img.paste(lay, (0, 0), lay)
    return ink.img.convert("RGB")


class _ButtonInk:
    """The little of an Ink the world's put() needs, on a transparent sheet."""

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")
        self.w, self.h = img.size

    def paste(self, img, xy=(0, 0), alpha=1.0):
        img = img.convert("RGBA")
        if alpha < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        x, y = int(xy[0]), int(xy[1])
        box = (max(0, -x), max(0, -y), min(img.width, self.img.width - x), min(img.height, self.img.height - y))
        if box[2] > box[0] and box[3] > box[1]:
            self.img.alpha_composite(img.crop(box), (x + box[0], y + box[1]))
        self.d = ImageDraw.Draw(self.img, "RGBA")


def _back_in(t, u):
    """From the river in through the small tin's porthole. The lit pane (and the small bird behind it) thins as the
    lens meets it, and what is beyond comes clear."""
    pts = tin_points()
    cx, cy = pts["port"]
    r = pts["port_r"]
    riv = river_back(t)
    fr = cam.through_glass(riv, seat_view(t), cx, cy, r, u, far=0.5, tint=Wd.PAL["amber"])
    k = 1 - cam.smooth(u / 0.55)
    if k <= 0 or u <= 0:
        return fr if u > 0 else riv
    reach = max(math.hypot(W / 2, H / 2) * 1.12 / r, 1.5)
    s = reach ** (u ** 1.15)
    frac = (s - 1) / (reach - 1)
    px, py = cx + (W / 2 - cx) * frac, cy + (H / 2 - cy) * frac
    big = riv.transform((W, H), Image.AFFINE, (1 / s, 0, cx - px / s, 0, 1 / s, cy - py / s), Image.BICUBIC)
    m = Image.new("L", (W, H), 0)
    rr = r * s * 0.99
    ImageDraw.Draw(m).ellipse([px - rr, py - rr, px + rr, py + rr], fill=int(255 * k))
    fr = fr.convert("RGB")
    fr.paste(big, (0, 0), m.filter(ImageFilter.GaussianBlur(1.2)))
    return fr


# ------------------------------------------------------------------ draw ---
def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 1.15:                                      # the camera rolls level with the sheet as she squares it
        e = 1 - ease(t, 0.08, 1.1)
        return cam.shoot([(desk_frame(t), 1.0)], rot=-6 * e, zoom=1.0 + 0.05 * e, bg=WOOD)
    if t < T_DIVE[0]:
        return desk_frame(t)
    if t < T_DIVE[1]:                                 # down through the ring; we land already facing the glass
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat_view(t), rx, ry, ramp(t, *T_DIVE), spin=30)
    if t < T_GLASS[1]:                                # out through the glass
        u = ramp(t, *T_GLASS)
        return cam.through_glass(seat_inside(), outside(t, _depth(u)), PORT[0], PORT[1], R_SEAT, u, far=FAR)
    if t < T_TURN[1]:                                 # and round, to the right, in the water
        return cam.turn(outside(t, _depth(1.0)), river_back(t), ramp(t, *T_TURN), axis="y", direction=1)
    if t < T_RIVER[1]:                                # the river looking back. Nothing comes.
        return river_back(t)
    if t < T_IN[1]:
        return _back_in(t, ramp(t, *T_IN))
    if t < T_UP[1]:                                   # up out of the ring, to the desk
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat_view(t), rx, ry, 1 - ramp(t, *T_UP))
    return desk_frame(t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() else FILMS / "stills" / "m13_scene_trout"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    if not ts:
        ts = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.3, 2.7, 3.0, 3.3, 3.9, 4.5, 4.95, 5.35, 5.6, 5.98, 6.09, 6.3, 6.6, 6.9,
              7.3, 7.7, 8.0, 8.4, 8.8, 9.1, 9.35, 9.7, 10.05, 10.4, 10.7, 12.0, 13.4, 13.7, 14.0, 14.3, 14.6, 14.9,
              15.3, 15.6, 15.9, 16.1, 17.5, 18.5, 19.2, 20.0, 20.8, 21.4]
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for t in ts:
        ink = Ink(t, int(t * 24))
        draw(t, ink)
        im = ink.img.convert("RGB")
        im.save(out / f"{t:06.2f}.png")
        ImageDraw.Draw(im).text((8, 6), f"{t:.2f}", fill=(255, 255, 0))
        tiles.append(im.resize((480, 270), Image.LANCZOS))
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 24))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
    sheet.save(out / "sheet.png")
    print("stills ->", out)


if __name__ == "__main__":
    _test([a for a in sys.argv[1:]])
