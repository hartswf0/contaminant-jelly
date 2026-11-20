"""m25 · scene_trout · the next friend, N. (board beats N1 to N11, film seconds 60.6 to 84.1; this clock = film - 60.6).

N1   0.0 ..  1.5  the sheet has landed back up and a quarter turn round; one rust hand swings it square while the
                  eye sinks into the seat; one tall thick N on the name line                              (trace 27)
N2   1.5 ..  4.0  hard in on the blue-cross button: he colours it in, round and round, until the cross nearly
                  goes; then two long light strokes in the dashed ring, the rising one running out of it  (28, 29)
N3   4.0 ..  4.9  dive into the coloured-in button; we arrive in Turkey's seat already facing out         (33)
N4   4.9 ..  6.0  out through the glass into the lock
N5   6.0 ..  7.2  the swing round in the water, to the left
N6   7.2 .. 10.4  the river looking back: the tin small and far, a small Turkey beating in it; it comes up to
                  giant, is ringed once in blue; three plain fish come in nose-on, swing level and swim next
                  to it. Nothing they could be looking at is in frame                                     (33, 34)
N7  10.4 .. 11.4  back in through the tin's small round glass
N8  11.4 .. 12.3  up out of the button, to the desk, over ending 4
N9  12.3 .. 16.5  `the fish swim next` up among the printed words, the rule through the letters; underneath and on
                  its tails `to astronat looking th`, on past the end of the rule; the eye reaches the paper's edge
                  and stops; the pencil goes on out of frame                              (27, 30, 31, 32, 35)
N10 16.5 .. 17.3  back along his own line to the die of ending 5, slowing to nothing
N11 17.3 .. 23.5  THE LONG STILL HOLD. The hand rests at the start of ending 5 with the point up. It does not
                  write. Once the point comes down and goes back up. Once the head turns left and comes back.  (37)

Nobody on this sheet used the rubber: no erase pose, no rub mark. What the fish are looking at is never shown.

Every seat is a whole picture (the desk with sheet, hand and head from people.py; Turkey's seat, the lock and the
river from the c25 world) and every change of seat is a cam.py move. The desk machinery (the sheet at twice size,
the perspective desk camera, the stroke timing) is the first friend's, imported from scene_turkey.py in this folder
so that the two desks and K.'s finished column join exactly.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page2(t) (the sheet image, 1520 x
1960; page2(SECONDS) is the back as it was left), desk_frame(t) and frame(t) (no badge) for the editor.
frame(0.0) is the desk the pass lands on: page 2, back up, a quarter turn clockwise, seen from nearly above.
Test:  python3 films/swarm/m25/scene_trout.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c25"))
import world as w  # noqa: E402   (the c25 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

_spec = importlib.util.spec_from_file_location("m25_scene_turkey", HERE / "scene_turkey.py")
KT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(KT)

W, H = 960, 540
key = cam.key

SECONDS = 23.5
CAPTIONS = [
    (16.5, 19.1, "The fish swim next to the astronaut, looking..."),
]

RUST = "rust"
HAIR = "curly"
WOOD = KT.WOOD
S, SIZE, SC, SO = KT.S, KT.SIZE, KT.SC, KT.SO
B, _mid, Line, _lettered, View = KT.B, KT._mid, KT.Line, KT._lettered, KT.View

# ---------------------------------------------------------------- times ---
T_SWING = (0.1, 0.7)                 # the sheet swung square
T_N = (0.78, 1.4)                    # N
T_SCR = (1.65, 2.9)                  # the button coloured in
T_X = (3.15, 3.85)                   # the X
T_DIVE = (4.0, 4.9)
T_GLASS = (4.9, 6.0)
T_TURN = (6.0, 7.2)
T_RIVER = (7.2, 10.4)
T_IN = (10.4, 11.4)
T_UP = (11.4, 12.3)
T_L4A = (12.4, 14.0)                 # the fish swim next
T_L4B = (14.22, 16.1)                # to astronat looking th
T_OFF = (16.1, 16.5)                 # the pencil goes on, out of frame
T_BACK = (16.5, 17.3)
T_STILL = 17.3
T_DIP = (19.7, 20.0, 20.2, 20.7)     # the point comes down to 4 px, and goes back up
T_LOOK = (21.5, 21.95, 22.45, 23.0)  # the head turns left towards K.'s column, and comes back

# ---------------------------------------------------- N.'s marks on page 2 ---
LH = B(2, "bolt4.1")[3] - B(2, "bolt4.1")[1]          # one ruled line's height (38 at this size)
XH = 0.84 * LH                                        # twice K.'s letters: a blunt pencil and a big hand
EDGE_X = SIZE[0]                                      # the paper's right edge
BTN = _mid(B(2, "btn2a"))
BTN_R = (B(2, "btn2a")[2] - B(2, "btn2a")[0]) / 2
XR = _mid(B(2, "draw2.circle"))
HOVER5 = (B(2, "bolt5.1")[0] + 66.0, B(2, "bolt5.1")[3] + 12.0)       # over the start of ending 5's first rule


def _scribble():
    """The button coloured in: round and round, the pencil never leaving it, until the printed cross nearly goes."""
    cx, cy = BTN
    pts = []
    n = 230
    for i in range(n):
        f = i / (n - 1)
        a = f * 2 * math.pi * 10.5 + 0.6
        rad = BTN_R * (0.22 + 0.62 * abs(math.sin(f * 9.4 + 0.5)) + 0.10 * math.sin(a * 0.37))
        pts.append((cx + rad * 1.04 * math.cos(a) + 1.2 * math.sin(i * 1.7), cy + rad * 0.96 * math.sin(a) + 1.2 * math.cos(i * 2.3)))
    return Line([pts[:80], pts[79:156], pts[155:]], 4.0)


def _cross():
    """Two long light strokes; the one rising to the right carries on past the dashed line (trace 29)."""
    cx, cy = XR
    fall = [(cx - 25, cy - 30), (cx - 8, cy - 9), (cx + 9, cy + 12), (cx + 25, cy + 31)]
    rise = [(cx - 27, cy + 30), (cx - 6, cy + 6), (cx + 14, cy - 15), (cx + 31, cy - 33), (cx + 44, cy - 49)]
    sm = lambda st: [tuple(p) for p in P.catmull(st, 8)]
    return Line([sm(fall), sm(rise)], 30.0)


def _spread(ln, x0, x_to):
    """A big hand: the letters are spaced out along the line so that it ends at x_to."""
    k = (x_to - x0) / max(ln.x_end - x0, 1.0)
    out = Line([[(x0 + (x - x0) * k, y) for x, y in st] for st in ln.strokes], ln.xh)
    out.letter = ln.letter
    return out


@lru_cache(None)
def _plans():
    d = {}
    nb = B(2, "name2.line")
    d["N"] = _lettered((nb[0] + 26, nb[1], nb[2], nb[3]), "N", 270, 0.86 * (nb[3] - nb[1]), slant=0.10)
    d["scr"] = _scribble()
    d["x"] = _cross()
    b = B(2, "bolt4.1")
    # up among the printed "What would you expect?": the rule runs through the letters, not under them (trace 30)
    a = _lettered((b[0] + 6, b[1] - 34, b[2] + 400, b[3]), "the fish swim next", 271, XH, sink=9.0, slant=0.04)
    d["l4a"] = _spread(a, a.start[0], b[2] - 8)
    b = B(2, "bolt4.2")
    # on top of the first row's tails, begun left of the rule, on past its end for the edge of the sheet (31, 35)
    a = _lettered((b[0] - 16, b[1] - 30, b[2] + 600, b[3]), "to astronat looking th", 272, XH * 0.92, sink=5.0, slant=0.06)
    d["l4b"] = _spread(a, a.start[0], EDGE_X - 10)
    return d


WEIGHT = {"N": 1.05, "scr": 1.35, "x": 0.62, "l4a": 0.9, "l4b": 0.9}
SPANS = {"N": T_N, "scr": T_SCR, "x": T_X, "l4a": T_L4A, "l4b": T_L4B}
ORDER = ["N", "scr", "x", "l4a", "l4b"]


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt = WEIGHT[name]
    if name == "scr":
        P.graphite(img, done, 4.6, wt, 273)
        P.graphite(img, [[(px + 1.5, py + 1.0) for px, py in st] for st in done], 3.6, 1.2, 274)
    elif name == "x":
        P.graphite(img, done, 4.2, wt, 275)
    else:
        P.graphite(img, done, max(2.0, ln.xh * 0.165), wt, 270 + ORDER.index(name))       # blunt: a broad soft line
    return x, y, down


@lru_cache(None)
def _base(n):
    if n == 0:
        return KT.page2(KT.SECONDS + 1.0).convert("RGB")           # K.'s whole column, as she left it
    img = _base(n - 1).copy()
    _write(img, ORDER[n - 1], 1.0)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS: the back of the sheet as it was left."""
    n = 0
    while n < len(ORDER) and SPANS[ORDER[n]][1] <= t:
        n += 1
    img = _base(n).copy()
    for name in ORDER[n:]:
        a, b = SPANS[name]
        if t > a:
            _write(img, name, ramp(t, a, b))
    return img


# ------------------------------------------------------- the desk camera ---
def _shot(deg, zoom, ax, ay, tx, ty):
    return (float(deg), math.log(zoom), float(ax), float(ay), float(tx), float(ty))


Y4 = B(2, "bolt4.1")[3]
ABOVE = _shot(16, 0.50, 760, 980, 480, 262)             # where the pass lands: nearly flat above the sheet
NAME = _shot(50, 1.55, 1040, 500, 450, 235)             # zone 6: the name line
BTNV = _shot(46, 2.9, BTN[0] + 10, BTN[1], 400, 250)         # hard in on the blue-cross button
XV = _shot(46, 2.1, XR[0] - 60, XR[1], 470, 255)        # the dashed ring
HOLE = _shot(50, 1.5, 1060, 690, 480, 262)              # plate, button and ring together: where we go in and come out
L4S = _shot(46, 2.5, 880, Y4 - 2, 300, 292)            # ending 4, the start of the rule
L4M = _shot(46, 2.5, 1130, Y4 - 2, 520, 292)           # ... along it
L4S2 = _shot(46, 2.5, 860, Y4 + 26, 300, 292)           # the second row, begun left of the rule
EDGE = _shot(46, 2.5, 1180, Y4 + 26, 520, 292)          # the paper's edge at the frame's edge
STILL = _shot(52, 1.7, 1010, 1010, 500, 226)           # ending 5: the die, two empty rules; ending 6 below
CAM_KEYS = [(0.0, ABOVE), (0.12, ABOVE), (0.85, NAME), (1.42, NAME), (1.8, BTNV), (2.95, BTNV), (3.25, XV), (3.8, XV),
            (4.02, HOLE), (11.4, HOLE), (12.3, L4S), (12.5, L4S), (13.95, L4M), (14.05, L4M), (14.3, L4S2), (14.45, L4S2),
            (15.65, EDGE), (16.5, EDGE), (17.3, STILL), (SECONDS, STILL)]
SHAKE_KEYS = [(0.0, 0.0), (0.9, 2.0), (3.9, 2.0), (4.0, 1.0), (12.3, 1.0), (12.5, 3.0), (15.6, 3.0), (15.75, 0.5), (16.5, 0.5),
              (16.9, 0.0), (SECONDS, 0.0)]


def view(t, shot=None):
    deg, lz, ax, ay, tx, ty = shot or key(t, CAM_KEYS, "smoother")
    return View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0 if shot else key(t, SHAKE_KEYS, "linear"), t)


def _head(fr, t):
    """Rust shoulders, curly hair: nearer the page than the other two sat. Out of frame when the eye is right down
    on the paper; in frame, and still, for the long hold."""
    y = key(t, [(0.0, 760), (0.2, 760), (0.9, 640), (1.45, 640), (1.9, 800), (16.5, 800), (17.3, 652), (SECONDS, 652)])
    if y > 770:
        return
    a, b, c, d = T_LOOK
    look = key(t, [(a, 0.0), (b, 1.0), (c, 1.0), (d, 0.0)])
    P.head_back(fr, 176 - 10 * look, y, RUST, 1.2, tilt=-9 * look, hair=HAIR, turn=-0.7 * look, t=min(t, T_STILL))


# ----------------------------------------------- where the pencil point is ---
AWAY = (1500.0, 1560.0)
REST = (1150.0, 760.0)                               # where the pencil waits while he is away in the river
GONE = (1780.0, 936.0)                               # past the paper's edge, out of the right of frame


def pen(t):
    """(sheet point, pose, lift) of N.'s right hand."""
    pl = _plans()

    def wr(name):
        x, y, down = pl[name].tip(ramp(t, *SPANS[name]))
        return (x, y), "write", 0 if down else 6

    if t < T_N[0]:
        return key(t, [(0.0, AWAY), (0.25, AWAY), (T_N[0], pl["N"].start)]), "hover", key(t, [(0.3, 20), (T_N[0], 5)])
    if t < T_N[1]:
        return wr("N")
    if t < T_SCR[0]:
        return key(t, [(T_N[1], pl["N"].end), (T_SCR[0], pl["scr"].start)]), "hover", key(t, [(T_N[1], 4), (1.52, 15), (T_SCR[0], 4)])
    if t < T_SCR[1]:
        (x, y), pose, _ = wr("scr")
        return (x, y), pose, 0                       # pressing: the point does not leave the button
    if t < T_X[0]:
        return key(t, [(T_SCR[1], pl["scr"].end), (T_X[0], pl["x"].start)]), "hover", key(t, [(T_SCR[1], 3), (3.02, 15), (T_X[0], 4)])
    if t < T_X[1]:
        return wr("x")
    if t < T_L4A[0]:                                 # the pencil up, waiting, while he is away
        p = key(t, [(T_X[1], pl["x"].end), (4.0, REST), (T_UP[0], REST), (T_L4A[0], pl["l4a"].start)])
        return p, "hover", key(t, [(T_X[1], 3), (4.0, 16), (T_UP[1], 14), (T_L4A[0], 5)])
    if t < T_L4A[1]:
        return wr("l4a")
    if t < T_L4B[0]:                                 # back to the left, underneath, without a pause
        return key(t, [(T_L4A[1], pl["l4a"].end), (T_L4B[0], pl["l4b"].start)]), "write", 8
    if t < T_L4B[1]:
        return wr("l4b")
    if t < T_OFF[1]:                                 # the pencil and the last strokes go on out of the right of frame
        e = pl["l4b"].end
        p = key(t, [(T_L4B[1], e), (T_OFF[1], GONE)], "linear")
        return (p[0], p[1] + 5 * math.sin(t * 38)), "write", 3 + 3 * math.sin(t * 23)
    if t < T_STILL:                                  # back along his own line; the heel comes down at ending 5
        return key(t, [(T_BACK[0], GONE), (T_STILL - 0.08, HOVER5)], "out"), "hover", key(t, [(T_BACK[0], 22), (T_STILL - 0.08, 16)])
    a, b, c, d = T_DIP                               # it does not write
    return HOVER5, "hover", key(t, [(a, 16), (b, 4), (c, 4), (d, 16)])


def _right(target, v, t):
    p, pose, lift = pen(t)
    tt = t
    if T_X[1] + 0.15 <= t < T_UP[0]:
        tt = 4.0
    if t >= T_STILL - 0.08:
        tt = T_STILL                                 # the hand's own clock stops
    arm = key(t, [(1.45, 60), (1.75, 68), (3.9, 68), (4.1, 60), (16.5, 60), (17.2, 74)])
    P.hand(target, *v.pt(p), pose=pose, tone=RUST, scale=v.hs(p, 1.08), t=tt, lift=lift, arm=arm)


def _swing_angle(t):
    return 90.0 * (1 - cam.smooth(ramp(t, *T_SWING)))


def _left(fr, v, t):
    """One hand swings the sheet square: flat on the paper's left side, it goes the quarter turn with it and stays."""
    ang = math.radians(_swing_angle(t))
    lx, ly = 60.0, 600.0                                         # where it lies, from the sheet's middle
    x = SC[0] + lx * math.cos(ang) - ly * math.sin(ang)
    y = SC[1] + lx * math.sin(ang) + ly * math.cos(ang)
    P.hand(fr, *v.dpt(x, y), pose="hold", tone=RUST, scale=v.hs((200, 1540), 1.08), flip=True, t=min(t, 1.5),
           arm=112 + 0.3 * _swing_angle(t))


def desk_frame(t, shot=None):
    """N.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t, shot)
    pg = page2(t)
    if t < T_SWING[1] + 0.02:
        fr = v.render(KT._desktop(pg, angle=_swing_angle(t)))
    else:
        fr = v.render(KT._desktop(pg))
    if shot is None:
        a = key(t, [(1.5, 0.0), (1.8, 1.0), (3.8, 1.0), (4.0, 0.0)])            # a short lens, hard in on the button
        if a > 0.01:
            at = key(t, [(2.95, BTN), (3.25, XR)])
            fr = KT._rack(fr, v.pt(at), a, 190.0)
    if t < 1.9:
        _left(fr, v, t)
    _right(fr, v, t)
    _head(fr, t)
    return fr


def button_xy(t):
    return view(t).pt(BTN)


# ------------------------------------------------ Turkey's seat, facing out ---
PORT, PR = w.PORT_C, w.PORT_R
WALK_AT, WALK_H = KT.WALK_AT, KT.WALK_H
REFL = dict(KT.REFL)
NEAR = 1.3                                           # how much nearer the lock is once the lens is through the glass
FAR = 2 * PR / (H * NEAR)                            # so that the glass at u = 0 shows the lock at Turkey's size
SEAT_BEATS = [4.45, 5.25, 11.75]
RIVER_BEATS = [7.75, 9.35]


def _wing(t, beats, rest=9.0):
    v = rest + 5 * abs(math.sin(t * 15))
    for b in beats:
        v = max(v, 96 * math.sin(math.pi * clamp((t - b) / 0.5)))
    return v


def _ink(t):
    return Ink(t, int(t * 24))


@lru_cache(None)
def seat_inside():
    """The tin's inside wall with its brass ring and the gauge where K.'s look left it (two ticks). The glass is
    filled in: cam.through_glass cuts it."""
    ink = _ink(0.0)
    ink.fill((60, 118, 112))
    w.seat_frame(ink)
    KT.C25T._gauge(ink, 2.0, 0.0)
    return ink.img.convert("RGB")


def lock_out(t, k=0.0):
    """What is beyond Turkey's glass, with the lens `k` (0..1) of the way through it: the lock under water and the
    walker standing in it, as K. left them. Turkey's reflection lies on the pane and slides off it as we go
    through. The picture is NEAR times Turkey's size: once outside, we are that much nearer."""
    ink = _ink(t)
    w.seat_backdrop(ink, t)
    w.walker(ink, WALK_AT[0], WALK_AT[1], WALK_H, bowl_bubbles=t, phase=t * 3, amp=3)
    for b in SEAT_BEATS:
        if t > b + 0.2:
            w.bubbles(ink, KT.C25T.PUFF, t, t0=b + 0.2, n=6, size=8.0, rise=180, spread=20, alpha=(1 - ramp(t - b - 0.2, 0.7, 1.2)) * (1 - k))
    al = REFL["alpha"] * (1 - cam.smooth(k / 0.45))
    if al > 0.01:
        kw = dict(REFL, alpha=al, cx=REFL["cx"] - 150 * k * k, cy=REFL["cy"] + 40 * k * k)
        w.turkey_reflection(ink, mood="panic", t=t, wing=_wing(t, SEAT_BEATS), **kw)
    im = ink.img.convert("RGB")
    return im.transform((W, H), Image.AFFINE, (1 / NEAR, 0, PORT[0] - (W / 2) / NEAR, 0, 1 / NEAR, PORT[1] - (H / 2) / NEAR),
                        Image.BICUBIC)


def seat_view(t):
    """Turkey's seat, already facing out (K.'s view): the lock, the walker, Turkey's reflection beating."""
    return cam.through_glass(seat_inside(), lock_out(t, 0.0), PORT[0], PORT[1], PR, 0.0, far=FAR)


# --------------------------------------------------- the river looking back ---
#        where each fish ends beside the suit (x, y), its length, phase, when it comes
FISH = [((246, 150), 128, 0.0, 8.55),
        ((214, 262), 142, 2.1, 8.8),
        ((262, 372), 128, 4.0, 9.05)]


def _tin_at(t):
    g = cam.smooth(ramp(t, 7.6, 8.8))
    s = lerp(0.6, 1.35, g)
    c = (lerp(668, 632, g) + 6 * math.sin(t * 0.7 + 1.0) * g, lerp(318, 240, g) + 8 * math.sin(t * 0.9) * g)
    ang = g * (2.0 + 3.5 * math.sin(t * 0.55 + 0.4))
    return c, s, ang, g


def river(t):
    """Where the fish are. The lock in mirror image; the bread-roll tin, small and far at first with a small Turkey
    beating behind its small round glass; then it comes up to giant, hanging, a little tilted, ringed once in blue:
    riveted shell, round visor. Three plain fish come in nose-on to it, swing level and swim next to it. The lens is
    beside them and a little apart. Nothing they could be looking at is here. Returns (picture, tin points)."""
    ink = _ink(t)
    c, s, ang, g = _tin_at(t)
    pace = cam.smooth(ramp(t, 9.2, 10.2))
    w.river_backdrop(ink, t, shift=60 - 26 * pace * (t - 9.2) - 20 * g)
    beat = max([0.0] + [math.sin(math.pi * clamp((t - b) / 0.5)) for b in RIVER_BEATS])
    tp = w.tin(ink, c, s, t, mood="panic", angle=ang, wing=_wing(t, RIVER_BEATS, 24.0), shake=3.5 * beat * s)
    done = ramp(t, 8.55, 9.35)
    if done > 0:
        ca = math.radians(ang)
        k = s / 1.35
        w.crayon_ring(ink, (c[0] + 10 * math.cos(ca), c[1] - 10 * math.sin(ca)), 318 * k, 190 * k, w.PAL["blue"], done,
                      seed=2, width=7, alpha=0.85)
    for b in RIVER_BEATS:
        if t > b + 0.2:
            o = (tp["port"][0] + 60 * s, tp["port"][1] - 96 * s)
            w.bubbles(ink, o, t, t0=b + 0.2, n=7, size=6.0 + 6.0 * s, rise=150, spread=22, alpha=1 - ramp(t - b - 0.2, 0.8, 1.3))
    dx, dy = c[0] - 632, c[1] - 240
    for (ex, ey), ln, ph, t0 in FISH:
        u = ramp(t, t0, t0 + 1.15)
        if u <= 0:
            continue
        e = cam.smooth(u)
        sx, sy = -130.0, 270.0 + (ey - 262) * 0.25                 # in from the left, heading for the suit's nose
        mx, my = ex - 70, lerp(sy, ey, 0.35)
        x = (1 - e) ** 2 * sx + 2 * e * (1 - e) * mx + e * e * ex
        y = (1 - e) ** 2 * sy + 2 * e * (1 - e) * my + e * e * ey
        tx_ = 2 * (1 - e) * (mx - sx) + 2 * e * (ex - mx)
        ty_ = 2 * (1 - e) * (my - sy) + 2 * e * (ey - my)
        head = -math.degrees(math.atan2(ty_, max(tx_, 1e-3))) * (1 - cam.smooth(ramp(u, 0.7, 1.0)))
        bob = 1.0 * e
        x += (dx * 0.8 + 5 * math.sin(t * 1.3 + ph)) * bob
        y += (dy * 0.8 + 6 * math.sin(t * 1.1 + ph * 1.7)) * bob
        w.trout(ink, x, y, ln, angle=head + 2.5 * math.sin(t * 1.1 + ph * 1.7 + 1.2) * e, flip=True, phase=t * 6 + ph,
                amp=9, lid=0.0)
    return ink.img.convert("RGB"), tp


def river_frame(t):
    e = math.sin(math.pi * ramp(t, *T_RIVER)) ** 0.5 if T_RIVER[0] < t < T_RIVER[1] else 0.0
    im, tp = river(t)
    if e <= 0:
        return im
    return cam.shoot([(im, 1.0)], x=10 * e * math.sin((t - T_RIVER[0]) * 0.8), zoom=1.0 + 0.03 * e, shake=1.0 * e, t=t,
                     bg=w.PAL["water_mid"])


def _back_in(t, u):
    """From the river in through the tin's round glass. The lit pane (and the bird behind it) thins as the lens
    meets it, and Turkey's own view comes clear beyond."""
    riv, tp = river(t)
    cx, cy = tp["port"]
    r = tp["port_r"]
    if u <= 0:
        return riv
    fr = cam.through_glass(riv, seat_view(t), cx, cy, r, u, far=0.5, tint=w.PAL["amber"])
    k = 1 - cam.smooth(u / 0.55)
    if k <= 0:
        return fr
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
_hold = {}


def _held(t):
    """The long hold: nothing moves, so the picture is the same picture (the one dip and the one look apart)."""
    a, d = T_DIP[0], T_DIP[3]
    la, ld = T_LOOK[0], T_LOOK[3]
    if a <= t < d or la <= t < ld:
        return desk_frame(t)
    if "f" not in _hold:
        _hold["f"] = desk_frame(T_STILL)
    return _hold["f"].copy()


def frame(t):
    """The 960 x 540 picture at module second t, without the badge."""
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 0.9:                                       # the eye rolls a little with the swinging sheet, and settles
        e = math.sin(math.pi * ramp(t, 0.05, 0.9))
        return cam.shoot([(desk_frame(t), 1.0)], rot=5 * e, zoom=1.0 + 0.04 * e, bg=WOOD)
    if t < T_DIVE[0]:
        return desk_frame(t)
    if t < T_DIVE[1]:                                 # into the coloured-in button
        bx, by = button_xy(t)
        return cam.dive(desk_frame(t), seat_view(t), bx, by, ramp(t, *T_DIVE), spin=30)
    if t < T_GLASS[1]:                                # out through the glass
        u = ramp(t, *T_GLASS)
        return cam.through_glass(seat_inside(), lock_out(t, u), PORT[0], PORT[1], PR, u, far=FAR)
    if t < T_TURN[1]:                                 # and round, to the left, in the water
        return cam.turn(lock_out(t, 1.0), river_frame(t), ramp(t, *T_TURN), axis="y", direction=-1)
    if t < T_RIVER[1]:                                # the river looking back
        return river_frame(t)
    if t < T_IN[1]:                                   # in through the small round glass
        return _back_in(t, ramp(t, *T_IN))
    if t < T_UP[1]:                                   # and up out of the button
        bx, by = button_xy(t)
        return cam.dive(desk_frame(t), seat_view(t), bx, by, 1 - ramp(t, *T_UP))
    if t < T_STILL:
        return desk_frame(t)
    return _held(t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    w.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() and not argv[0].startswith("--") else FILMS / "stills" / "m25_scene_trout"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.3, 0.5, 0.75, 1.1, 1.4, 1.7, 2.2, 2.85, 3.3, 3.8, 4.15, 4.4, 4.7, 5.0, 5.4, 5.8, 6.2, 6.6, 7.0,
              7.3, 8.0, 8.6, 9.2, 9.8, 10.3, 10.6, 10.9, 11.2, 11.6, 12.0, 12.6, 13.3, 13.95, 14.6, 15.3, 16.05, 16.3,
              16.8, 17.2, 18.5, 19.95, 21.0, 22.2]
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for t in ts:
        ink = Ink(t, int(t * 24))
        draw(t, ink)
        if caps:
            for a, b, s in CAPTIONS:
                if a <= t < b:
                    ink.caption(s)
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
