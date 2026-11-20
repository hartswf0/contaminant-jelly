"""m16 · scene_trout · the next friend, W. (board beats W1 to W9, film seconds 55.0 to 78.0; this clock = film - 55).

W1   0.0 ..  1.6  a small `W` on the name line; the point lifts and goes a long way right; the eye is already
                  drifting down to the plates                                                            (trace 26)
W2   1.6 ..  4.2  the point hangs between the two plates, then goes round the whole of "Two-headed tin monster",
                  button and all, in one slow wobbling loop that overshoots its start; it goes to the dashed ring,
                  hangs over it, and leaves it empty                                                     (27)
W3   4.2 ..  6.8  Probable: THE HAND DOES NOT WRITE. Camera locked. Late, the lifted point drifts down to the next
                  printed stem and stops under its last word, "fits."                                    (28, 30)
W4   6.8 ..  8.4  the sheet is turned to the front; down through the ring, into Turkey's seat, facing the glass
W5   8.4 ..  9.6  OUT THROUGH THE GLASS: the brass rim goes past the frame edges; the pilot's page, which was all
                  there was outside, gives way to water. We are out, facing away from the tin
W6   9.6 .. 10.8  THE SWING ROUND, to the left: the tin comes into frame, small
W7  10.8 .. 13.8  the river, looking back. The small tin, a very small Turkey waving in its window; two trout near
                  us, the second on the first one's path twelve frames behind. A second tin head comes together
                  above the tin in pencil outline only, then its double twelve frames later; the outline lowers
                  onto the tin and sits rim on rim with one small bounce: it fits. It never takes colour  (29, 27)
W8a 13.8 .. 15.9  back in through the small tin's porthole; up out of the ring; the sheet turned over again
W8  15.9 .. 20.4  the left index finger comes down on the circled plate and stays; the point touches the printed
                  "fits." once; `two   headed   tin`, each letter alone, "tin" climbing; `monster  fits  the`
                  and then `submarine`, smaller and closer, past the end of the rule and over the margin  (29, 30, 31)
W9  20.4 .. 23.0  Preposterous: THE HAND DOES NOT WRITE. Camera locked. The pencil is laid on the desk beside the
                  sheet and the hand flattens on the page                                                (32)

Every seat is a whole picture: the desk (the sheet as written so far, laid back by cam.tilt, with both hands and the
back of the head from people.py), Turkey's seat and the river (the c16 world). Every change of seat is a cam.py
move (dive, through_glass, turn); the page turns are the desk camera going down to the desk's edge. Nothing is
cross-faded. In W5 the paper outside the glass gives way to water as the lens goes through: that is the picture
taking colour (the board: a thought is pencil first), under a real through_glass move.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); and for the editor page2(t) (the sheet,
1520 x 1960; page2(SECONDS) is the page as W. left it), desk_frame(t), frame(t).
B.'s column and the pilot's front come from scene_turkey.py (page2, page1_done) so the three modules show one sheet.

    python3 films/swarm/m16/scene_trout.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
for _p in (str(FILMS), str(FILMS / "swarm" / "c16")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c16 world; not edited)
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

W, H = 960, 540
key = cam.key

SECONDS = 23.0
CAPTIONS = [
    (20.4, 23.0, "Two-headed tin monster fits the submarine."),
]

TEAL = "teal"
HAIR = "short"
WOOD = (86, 62, 44)

# ------------------------------------------------------------ the sheet ---
S = 2
SIZE = (760 * S, 980 * S)
DESK_SIZE = (2300, 2500)
SC = (1150, 1280)
SO = (SC[0] - SIZE[0] // 2, SC[1] - SIZE[1] // 2)


def B(page, name):
    return P.where(page, name, SIZE)


def _mid(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


RING1 = _mid(B(1, "ring.in"))
RING_SC = (B(1, "ring.in")[2] - B(1, "ring.in")[0]) / 2 / 214.0


@lru_cache(None)
def _turkey_unit():
    """The first friend's scene unit, for the sheet as B. left it. None if it is not there."""
    try:
        f = HERE / "scene_turkey.py"
        spec = importlib.util.spec_from_file_location("m16_scene_turkey", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


@lru_cache(None)
def page1_done():
    """The pilot's front, finished."""
    st = _turkey_unit()
    try:
        img = st.page1_done().convert("RGB")
        return img if img.size == SIZE else img.resize(SIZE, Image.LANCZOS)
    except Exception:
        pg = P.sheet(SIZE, page=1, porthole=16)
        Wd.pilot_drawing(pg, RING1[0], RING1[1], 1.0, RING_SC)
        return pg


@lru_cache(None)
def _page2_b():
    """Page 2 as B. passed it on: a green B, a triangle, a ghost, one stray a, one sentence."""
    st = _turkey_unit()
    try:
        img = st.page2(st.SECONDS + 1.0).convert("RGB")
        return img if img.size == SIZE else img.resize(SIZE, Image.LANCZOS)
    except Exception:
        return P.sheet(SIZE, page=2, porthole=16)


class Line:
    """Pencil strokes with their timing (ink at pencil speed, air between strokes): upto(u), tip(u)."""

    def __init__(self, strokes, xh=20.0, air=0.55):
        self.strokes = [list(s) for s in strokes if len(s) >= 2]
        self.xh = xh
        self.seg = []
        T = 0.0
        prev = None
        for pts in self.strokes:
            if prev is not None:
                a = math.hypot(pts[0][0] - prev[0], pts[0][1] - prev[1]) * air + 0.5 * xh
                self.seg.append(("air", T, T + a, prev, pts[0]))
                T += a
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) + 0.25 * xh
            self.seg.append(("ink", T, T + L, pts, None))
            T += L
            prev = pts[-1]
        self.T = max(T, 1e-6)
        self.start = self.strokes[0][0]
        self.end = prev
        self.x_end = max(p[0] for s in self.strokes for p in s)

    def upto(self, u):
        if u <= 0:
            return [], self.start[0], self.start[1], False
        if u >= 1:
            return list(self.strokes), self.end[0], self.end[1], False
        tt = u * self.T
        done = []
        for kind, a, b, p, q in self.seg:
            if tt >= b:
                if kind == "ink":
                    done.append(p)
                continue
            f = (tt - a) / max(b - a, 1e-6)
            if kind == "air":
                f = f * f * (3 - 2 * f)
                return done, p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f, False
            n = min(len(p) - 1, max(1, int(round(f * (len(p) - 1)))))
            done.append(p[:n + 1])
            return done, p[n][0], p[n][1], True
        return done, self.end[0], self.end[1], False

    def tip(self, u):
        _, x, y, down = self.upto(u)
        return x, y, down


LH = B(2, "bolt5.1")[3] - B(2, "bolt5.1")[1]          # one ruled line's height
XH = 0.52 * LH                                        # W.'s letters


def _spaced(word, x0, x1, line, seed, xh, climb=0.0, sink=0.0):
    """One word, every letter made alone and standing apart (trace 31): each letter is planned by itself in the
    child's pencil alphabet (people.py) at its own place between x0 and x1. climb = rise per px along the word."""
    b = B(2, line)
    pitch = (x1 - x0) / len(word)
    strokes = []
    for i, ch in enumerate(word):
        xa = x0 + i * pitch
        pl = P.WritePlan((xa, b[1], xa + 300, b[3]), ch, seed * 31 + i, xh)
        for st in pl.strokes:
            strokes.append([(x, y - climb * (x - x0) + sink) for x, y in st])
    return Line(strokes, xh, air=0.8)


def _loop():
    """One pencil loop round the whole printed plate, button and all (trace 27): it starts at the left end, goes
    along the top, bulges round the right end, comes back along the bottom and overshoots its start, so the line
    is double at the left for a little way."""
    b = B(2, "plate2a")
    cx, cy = (b[0] + b[2]) / 2 + 8, (b[1] + b[3]) / 2
    a, h = (b[2] - b[0]) / 2 + 26, (b[3] - b[1]) / 2 + 13
    rs = random.Random(27)
    ph = [rs.uniform(0, 6.28) for _ in range(3)]
    pts = []
    n = 150
    for k in range(n + 1):
        f = k / n
        th = math.radians(180 + 398 * f)               # from the left end, over the top, round, and 38 degrees past
        c, s = math.cos(th), math.sin(th)
        # a squarish oval (superellipse) that swells at the right end
        ex = 0.38
        x = math.copysign(abs(c) ** ex, c)
        y = math.copysign(abs(s) ** (ex * 1.9), s)
        swell = 1.0 + 0.045 * max(0.0, c) ** 2
        wob = 3.0 * math.sin(f * 17 + ph[0]) + 2.0 * math.sin(f * 41 + ph[1])
        drift = 7.0 * f * (1 if f > 0.9 else 0.35)     # the second time past the start it runs a little outside
        yy = cy + y * (h * swell + wob + drift) + 5.0 * math.sin(f * 6.3 + ph[2]) + 5 * max(0.0, c) ** 3
        xx = cx + x * (a + wob * 0.6 + drift) + 16 * max(0.0, c) ** 4
        pts.append((xx, yy))
    return Line([pts], 20.0)


FITS = (1128.0, 989.0)                                 # under the printed "fits." in the Plausible stem
# (name, t0, t1, weight)
T_W = (0.3, 0.78)
T_LOOP = (2.2, 3.4)
WORDS = [("two", 16.5, 16.8), ("headed", 16.92, 17.44), ("tin", 17.56, 17.9),
         ("monster", 18.0, 18.72), ("fits", 18.84, 19.2), ("the", 19.32, 19.58), ("submarine", 19.72, 20.4)]


@lru_cache(None)
def _plans():
    d = {}
    nb = B(2, "name2.line")
    pl = P.WritePlan((nb[0] + 58, nb[1] + 6, nb[2], nb[3]), "W", 180, 17.0)
    d["W"] = Line(pl.strokes, pl.xh)
    d["loop"] = _loop()
    edge = SIZE[0] - 6                                 # the paper's edge, less 6 px
    d["two"] = _spaced("two", 832, 928, "bolt5.1", 181, XH)
    d["headed"] = _spaced("headed", 1034, 1262, "bolt5.1", 182, XH)
    d["tin"] = _spaced("tin", 1340, 1428, "bolt5.1", 183, XH, climb=0.16, sink=-5)
    d["monster"] = _spaced("monster", 806, 1034, "bolt5.2", 184, XH * 0.96)
    d["fits"] = _spaced("fits", 1066, 1156, "bolt5.2", 185, XH * 0.94)
    d["the"] = _spaced("the", 1206, 1292, "bolt5.2", 186, XH * 0.92)
    d["submarine"] = _spaced("submarine", 1326, edge - 4, "bolt5.2", 187, XH * 0.68, climb=0.02, sink=-1)
    return d


WEIGHT = {"W": 1.0, "loop": 1.0}


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt = WEIGHT.get(name, 1.0)
    wd = 3.0 if name == "loop" else max(1.3, ln.xh * 0.155) * (0.82 + 0.22 * wt)
    P.graphite(img, done, wd, wt, 180 + len(name))
    return x, y, down


def _it(name, t0, t1):
    def fn(img, t):
        if t > t0:
            _write(img, name, ramp(t, t0, t1))
    return t1, fn


ITEMS = [_it("W", *T_W), _it("loop", *T_LOOP)] + [_it(n, a, b) for n, a, b in WORDS]


@lru_cache(None)
def _base2(n):
    if n == 0:
        return _page2_b()
    img = _base2(n - 1).copy()
    ITEMS[n - 1][1](img, 1e9)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS is the page as W. left it."""
    n = 0
    while n < len(ITEMS) and ITEMS[n][0] <= t:
        n += 1
    img = _base2(n).copy()
    for _, fn in ITEMS[n:]:
        fn(img, t)
    return img


# ------------------------------------------------------- the desk camera ---
F = 700.0
HOR = 0.36


class View:
    """The seat's eye on the desktop plane: tilt, zoom (screen px per 760-page px at the aim), aim point (sheet px)
    held at a screen point. Handheld drift is a shift of the whole view."""

    def __init__(self, deg, zoom, at, to, shake=0.0, t=0.0):
        self.deg, self.z = deg, zoom / S
        d = (SO[0] + at[0], SO[1] + at[1])
        p0 = cam.tilt_point(d[0], d[1], deg, HOR, self.z, F, (0, 0), DESK_SIZE)
        sx = shake * (math.sin(t * 2.1) + 0.5 * math.sin(t * 5.3 + 1.0)) * 0.8
        sy = shake * (math.cos(t * 1.7) + 0.5 * math.sin(t * 4.1 + 2.0)) * 0.6
        self.shift = (to[0] - p0[0] + sx, to[1] - p0[1] + sy)

    def dpt(self, x, y):
        return cam.tilt_point(x, y, self.deg, HOR, self.z, F, self.shift, DESK_SIZE)

    def pt(self, p):
        return self.dpt(SO[0] + p[0], SO[1] + p[1])

    def ls(self, p):
        a = self.pt(p)
        b = self.pt((p[0] + 20, p[1]))
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 20 * S

    def hs(self, p, k=1.0):
        ls = self.ls(p)
        return ls / 1.26 * 0.86 * k * lerp(1.0, 0.72, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=WOOD, shadow=0)


#        tilt  log zoom        aim (sheet px)    held at (screen)
NAME = (44.0, math.log(2.6), 1080.0, 500.0, 440.0, 250.0)           # zone 6: the name line
PLATE = (44.0, math.log(2.1), 1130.0, 660.0, 470.0, 270.0)          # the two plates and the dashed ring
B4 = (42.0, math.log(2.1), 1110.0, 910.0, 470.0, 250.0)             # Probable's two lines, and the stem under them
FLIP = (88.0, math.log(0.70), 760.0, 900.0, 480.0, 236.0)           # the eye down at the desk's edge
RING = (58.0, math.log(0.78), 760.0, 900.0, 480.0, 250.0)           # the front: the ring in the middle
B5 = (42.0, math.log(2.2), 1160.0, 960.0, 470.0, 290.0)             # the circled plate above, the middle box below
B5R = (40.0, math.log(2.5), 1400.0, 1034.0, 420.0, 290.0)           # off the end of the rule, to the paper's edge
B6 = (42.0, math.log(2.1), 1190.0, 1130.0, 430.0, 270.0)            # Preposterous, the paper's edge, a strip of desk
CAM_KEYS = [(0.0, NAME), (0.95, NAME), (1.75, PLATE), (4.2, PLATE), (4.7, B4), (6.8, B4), (7.1, FLIP), (7.4, RING),
            (15.5, RING), (15.7, FLIP), (16.15, B5), (18.7, B5), (20.25, B5R), (20.4, B5R), (20.9, B6), (23.0, B6)]
SHAKE_KEYS = [(0.0, 2.2), (4.2, 2.2), (4.7, 0.0), (6.8, 0.0), (7.4, 0.0), (15.9, 0.0), (16.3, 2.0), (20.4, 2.0),
              (20.9, 0.0), (23.0, 0.0)]
STILL = [(4.7, 6.8), (20.9, 23.0)]                                  # stuck means still


def view(t):
    deg, lz, ax, ay, tx, ty = key(t, CAM_KEYS, "smoother")
    return View(deg, math.exp(lz), (ax, ay), (tx, ty), key(t, SHAKE_KEYS, "linear"), t)


@lru_cache(None)
def _desk_plane():
    im = Image.new("RGB", DESK_SIZE, P.DESK)
    P.desk(im)
    return im


@lru_cache(None)
def _desk_with_shadow():
    im = _desk_plane().copy()
    P.lay(im, Image.new("RGB", SIZE, P.PAPER), SC[0], SC[1])
    return im


def _desktop(page, lift=0.0):
    if lift == 0:
        im = _desk_with_shadow().copy()
        im.paste(page, SO)
        return im
    im = _desk_plane().copy()
    P.lay(im, page, SC[0], SC[1], 0.0, 1.0, lift=lift)
    return im


def _closeness(v):
    return clamp((v.z * S - 0.62) / 0.7)


# ----------------------------------------------- where the pencil point is ---
BETWEEN = (1130.0, 640.0)                              # between the two plates
RING2 = _mid(B(2, "draw2.circle"))
OVER4 = (B(2, "bolt4.1")[0] + 150, B(2, "bolt4.1")[3] - 5)
OVER6 = (B(2, "bolt6.1")[0] + 150, B(2, "bolt6.1")[3] - 5)
AWAY = (1750.0, 1700.0)
LAID = (SIZE[0] + 70.0, 1010.0)                        # where the pencil is laid, on the desk beside the sheet
PALM = (1250.0, 1300.0)                                # where the hand then lies flat on the page
T_LAY = 22.4
T_FLIP1 = 7.1
T_FLIP2 = 15.7


def _acts():
    pl = _plans()
    return [("W",) + T_W, ("loop",) + T_LOOP] + [(n, a, b) for n, a, b in WORDS], pl


def _air():
    pl = _plans()
    e = lambda n: pl[n].end
    s = lambda n: pl[n].start
    k = [
        (0.0, (s("W")[0] - 6, s("W")[1] - 4), 14), (T_W[0], s("W"), 3),
        (T_W[1], e("W"), 3), (1.0, (e("W")[0] + 60, e("W")[1] - 10), 16),          # the point lifts ...
        (1.36, (e("W")[0] + 150, B(2, "name2.line")[3] - 20), 8),                   # ... and comes down a long way right
        (1.6, (e("W")[0] + 152, B(2, "name2.line")[3] - 18), 7),
        (1.95, BETWEEN, 15), (2.1, BETWEEN, 15),                                    # hangs between the two plates
        (T_LOOP[0], s("loop"), 3), (T_LOOP[1], e("loop"), 3),
        (3.72, RING2, 15), (4.08, RING2, 15),                                       # over the dashed ring; leaves it
        (4.7, OVER4, 16), (6.0, OVER4, 16),                                         # Probable: it does not come down
        (6.4, FITS, 15), (6.8, FITS, 15),                                           # the lifted point under "fits."
        (7.3, AWAY, 30),
        (15.9, AWAY, 30), (16.22, (FITS[0] + 10, FITS[1] + 8), 12), (16.3, FITS, 0), (16.36, FITS, 0),      # touches "fits." once
    ]
    prev = None
    for n, a, b in WORDS:
        k += [(a, s(n), 4), (b, e(n), 4)]
        if prev is not None:                           # higher between words
            pe, ps = e(prev[0]), s(n)
            k.append(((prev[2] + a) / 2, ((pe[0] + ps[0]) / 2, (pe[1] + ps[1]) / 2 - 6), 15))
        prev = (n, a, b)
    es = e("submarine")
    k += [(20.56, (es[0] + 4, es[1] - 12), 14), (20.95, OVER6, 16), (22.12, OVER6, 16),               # Preposterous
          (T_LAY, LAID, 4)]
    k.sort(key=lambda q: q[0])
    return [(t, (p[0], p[1], l)) for t, p, l in k]


AIR = _air()


def pen(t):
    """(sheet point, pose, lift) of W.'s right hand."""
    pl = _plans()
    if t >= T_LAY:                                     # the pencil is on the desk; the hand flattens on the page
        p = key(t, [(T_LAY, LAID), (22.8, PALM)], "smooth")
        return p, "hold", key(t, [(T_LAY, 12), (22.62, 9), (22.84, 0)])
    for n, a, b in [("W",) + T_W, ("loop",) + T_LOOP] + WORDS:
        if a <= t < b:
            x, y, down = pl[n].tip(ramp(t, a, b))
            return (x, y), "write", (0 if down else 9)
    x, y, l = key(t, AIR, "smooth")
    return (x, y), ("hover" if l >= 14.5 else "write"), l


def _hand_t(t):
    for a, b in STILL:
        if a <= t < b:
            return a
    return t


def _breath(t):
    return 0.5 - 0.5 * math.cos(t * 1.9)


# ------------------------------------------------------------ desk frames ---
ARM_KEYS = [(0.0, 58), (19.5, 58), (19.9, 80), (20.5, 80), (20.9, 60)]
FINGER = (905.0, 622.0)                                # the left index finger, on the circled plate


def _right(fr, v, t):
    p, pose, lift = pen(t)
    if pose == "hold":
        P.hand(fr, *v.pt(p), pose="hold", tone=TEAL, scale=v.hs(p), t=_hand_t(T_LAY), lift=lift, arm=62)
        return
    if pose == "hover":
        lift = lift + 1.2 * _breath(t)                # breath only
    P.hand(fr, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=_hand_t(t), lift=lift, arm=key(t, ARM_KEYS))


def _left(fr, v, t, cl):
    if 15.9 <= t:                                      # the finger on the plate; it does not leave until the last letter
        p = key(t, [(15.9, (560, 900)), (16.3, FINGER), (20.45, FINGER), (20.9, (500, 1500))], "smooth")
        lf = key(t, [(15.9, 16), (16.24, 6), (16.34, 0), (20.42, 0), (20.6, 12), (20.9, 8)])
        if t < 20.9:
            P.hand(fr, *v.pt(p), pose="point", tone=TEAL, scale=v.hs(p), flip=True, t=_hand_t(t), lift=lf, arm=150)
        return
    if cl < 0.9:
        P.hand(fr, *v.pt((150, 1620)), pose="hold", tone=TEAL, scale=v.hs((150, 1620)), flip=True, t=t, arm=140)


HEAD_UP = [(0.0, 1.0), (1.2, 1.0), (1.9, 0.0), (4.15, 0.0), (4.7, 1.0), (6.7, 1.0), (6.8, 1.0),
           (20.4, 0.0), (20.9, 1.0), (23.0, 1.0)]


def _head(fr, t, cl, dy=0.0):
    if cl > 0.97:                                      # close work: only the top of the head, low in the frame
        rise = key(t, HEAD_UP, "smooth") if (t < 6.8 or t > 16.0) else 0.0
        if rise > 0.01:
            P.head_back(fr, 250, 880 - 205 * rise + 2.0 * _breath(t), TEAL, 1.15, hair=HAIR, t=_hand_t(t))
        return
    P.head_back(fr, 250, 590 + 330 * cl + dy, TEAL, 1.15, hair=HAIR, t=_hand_t(t))


def desk_frame(t):
    """W.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    cl = _closeness(v)
    flipping = (6.8 <= t < 7.4) or (15.5 <= t < 15.95)
    if flipping:                                       # the page turn: down to the desk's edge, the sheet turned, back up
        if t < 8:
            front = t >= T_FLIP1
            lift = 26 * math.sin(math.pi * ramp(t, 6.8, 7.4))
        else:
            front = t < T_FLIP2
            lift = 26 * math.sin(math.pi * ramp(t, 15.5, 15.95))
        fr = v.render(_desktop(page1_done() if front else page2(t), lift=lift))
        e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
        P.hand(fr, e[0], e[1], pose="pass", tone=TEAL, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    if 7.4 <= t < 15.5:                                # the front, while we are away in the tin and the river
        fr = v.render(_desktop(page1_done()))
        P.hand(fr, *v.pt((240, 1400)), pose="hold", tone=TEAL, scale=v.hs((240, 1400)), flip=True, t=t, arm=140)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    desk = _desktop(page2(t))
    if t >= T_LAY:                                     # the pencil, laid down beside the sheet
        P.pencil(desk, SO[0] + LAID[0], SO[1] + LAID[1], angle=-72, scale=2.3)
    fr = v.render(desk)
    _left(fr, v, t, cl)
    _right(fr, v, t)
    _head(fr, t, cl)
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------ Turkey's seat, looking out ---
PAL = Wd.PAL
PORT, R = Wd.PORT, Wd.PORT_R
PSC = R / 214.0
T_WAVE = 7.9                                          # Turkey's wing goes up as we land beside him


@lru_cache(None)
def _outside():
    """What is outside the glass, from Turkey's seat, before W. has gone out there: the pilot's page. Paper, the
    pencil sub small and high, its window black, the faint head; a few pencil lines of water. (As in T3.)"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.array(PAL["page"], np.float32)[None, None, :] * (0.97 + 0.03 * Wd.vnoise((H, W), 3, None, 77))[..., None]
    a *= (1.0 - 0.10 * np.clip((yy - 300) / 240, 0, 1))[..., None]
    im = Wd.to_img(a).convert("RGB")
    rs = random.Random(5)
    for k in range(7):
        y = PORT[1] + 40 + 20 * k + rs.uniform(-5, 5)
        x0 = PORT[0] - 170 + rs.uniform(0, 120)
        n = rs.randint(5, 9)
        pts = [(x0 + 22 * j, y + 4 * math.sin(j * 1.3 + k)) for j in range(n)]
        Wd.pencil_path(im, pts, weight=0.32, seed=40 + k)
    Wd.pilot_drawing(im, PORT[0], PORT[1], 1.0, PSC)
    return im


def seat(t):
    """Turkey's seat: the brass porthole from where he sits, his back at lower right, the gauge; outside the glass,
    the pilot's page."""
    g = Wd.on_twos(t)
    ink = Ink(t, int(t * 24))
    ink.img.paste(_outside())
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.cabin(ink, g)
    Wd.air_gauge(ink, Wd.SEAT_GAUGE[0], Wd.SEAT_GAUGE[1], 1.0, Wd.SEAT_GAUGE[2], g)
    Wd.turkey_back(ink, Wd.SEAT_TURKEY[0], Wd.SEAT_TURKEY[1], Wd.SEAT_TURKEY[2], t=g, shade=0.16, **Wd.wave_pose(g, 1.0, T_WAVE))
    return ink.img.convert("RGB")


# ---------------------------------------------------------------- the river ---
_riv = {}


def open_water(t):
    """Out, and facing away from the tin: open green water, weed, light shafts. No tin."""
    k = int(t * 12)
    if k not in _riv:
        if len(_riv) > 3:
            _riv.clear()
        g = k / 12.0
        ink = Ink(g, int(g * 24))
        Wd.river(ink, g, -40.0, 0, shafts=0.5)
        Wd.river_plane(ink, "front", g, -40.0, 0)
        _riv[k] = ink.img.convert("RGB")
    return _riv[k]


@lru_cache(None)
def _noise():
    return Wd.vnoise((H, W), 60, None, 91, 2)


@lru_cache(None)
def _page_far():
    """The pilot's page as through_glass shows it in the window at u = 0 (the glass's middle at the frame's middle)."""
    im = Image.new("RGB", (W, H), PAL["page"])
    im.paste(_outside(), (W // 2 - PORT[0], H // 2 - PORT[1]))
    return im


def _beyond(t, u):
    """What is beyond the glass while the lens goes through it: the page gives way to the water, from the middle
    outward, with a torn edge. At u = 0 it is the page the seat shows; by u = 0.8 it is all river."""
    wat = open_water(t)
    rad = -90 + 900 * cam.smooth(ramp(u, 0.04, 0.8))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - W / 2, yy - H / 2)
    m = np.clip((rad - d + 110 * (_noise() - 0.5)) / 46.0, 0, 1)
    return Image.composite(wat, _page_far(), Image.fromarray((m * 255).astype(np.uint8)))


TIN = (372, 268, 0.52)                                # the bread-roll tin, small, centre-left
T_TWAVE = 11.0
T_HEAD = 11.4                                         # the pencil head; its double D frames later
T_LOWER = (12.4, 13.0)
HOVER_LIFT = 54.0
PM = 60                                               # margin of the outline layer


def _outline(rgba, width=5, weight=0.9, seed=0, color=None):
    """A cut-paper piece as its pencil outline only."""
    a = rgba.getchannel("A")
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(width)), a.filter(ImageFilter.MinFilter(width)))
    inner = rgba.convert("L").filter(ImageFilter.GaussianBlur(1.0)).filter(ImageFilter.FIND_EDGES)
    inner = ImageChops.multiply(inner.point(lambda v: min(255, v * 4)), a.filter(ImageFilter.MinFilter(7)))
    m = np.maximum(np.asarray(edge, np.float32), np.asarray(inner, np.float32) * 0.55) / 255.0
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255.0
    m *= (0.74 + 0.4 * P.vnoise(m.shape, 1.6, None, 811 + seed)) * weight
    out = np.zeros(m.shape + (4,), np.uint8)
    out[..., :3] = color or P.GRAPHITE
    out[..., 3] = (np.clip(m, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


@lru_cache(None)
def _monster_lines():
    """The two-headed tin monster, cut to fit this tin, as pencil outline only (it is never painted): the chalk
    line and a soft dark line under it so it reads on the water. Returned with the x of the gap between its heads."""
    BIG = 3
    lay = Image.new("RGBA", (W * BIG, H * BIG), (0, 0, 0, 0))
    r = Wd.tin_monster(lay, TIN[0] * BIG, TIN[1] * BIG, TIN[2] * BIG, 0.0, lift=0.0, drop=False)
    ol = _outline(lay, 13, 1.0, 3, Wd.CHALK).resize((W, H), Image.LANCZOS)
    ol.putalpha(ol.getchannel("A").point(lambda v: min(255, int(v * 1.5))))
    full = Image.new("RGBA", (W, H + PM), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (20, 40, 36, 0))
    sh.putalpha(ol.getchannel("A").filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: min(255, int(v * 0.9))))
    full.paste(sh, (1, PM + 2), sh)
    full.alpha_composite(ol, (0, PM))
    split = (r["left_eye"][0] + r["right_eye"][0]) / 2 / BIG
    top = ol.getbbox()[1]
    return full, split, top


def _reveal(t0, t, y_top, y_bot):
    """The line draws itself up from the rim: (alpha mask row values) for a part that begins at t0."""
    u = ramp(t, t0, t0 + 0.46)
    yy = np.arange(H + PM, dtype=np.float32)[:, None]
    edge = lerp(y_bot + 10, y_top - 14, u) + PM
    return np.clip((yy - edge) / 9.0, 0, 1)


def _pencil_head(ink, t):
    """A second tin head comes together above the tin in pencil outline: one head (with the skirt), then its double
    twelve frames later; then the outline lowers onto the tin and sits rim on rim with one small bounce."""
    if t < T_HEAD:
        return
    full, split, top = _monster_lines()
    bot = TIN[1] - 46 * TIN[2] + 16
    a = np.asarray(full, np.float32).copy()
    xx = np.arange(W, dtype=np.float32)[None, :]
    left = np.clip((split - xx) / 3.0 + 0.5, 0, 1)
    m = _reveal(T_HEAD, t, top, bot) * left + _reveal(T_HEAD + Wd.DT, t, top, bot) * (1 - left)
    thin = 1.0 - 0.62 * ease(t, 13.4, 13.9)                                        # already thinning
    a[..., 3] *= m * thin
    lift = HOVER_LIFT * (1 - ease(t, *T_LOWER)) - 7 * Wd.settle(t, T_LOWER[1], 1.0, 3.0, 6.0)
    lift += 3.0 * math.sin(t * 2.4) * (1 - ease(t, *T_LOWER))
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    Wd._comp(ink, im, (0, int(round(-PM - max(lift, -4)))))


def _trout_path(tt):
    return (1100 - 172 * (tt - 10.6), 440 + 20 * math.sin(tt * 2.2), -4 + 3 * math.sin(tt * 1.3))


_rv = {}


def river_pic(t):
    """The river, looking back: the bread-roll tin, small, its porthole lit and a very small Turkey waving in it;
    the pencil head; two trout near us, dark, looking where we look. Returns (picture, the tin's port, its radius)."""
    k = int(round(t * 24))
    if k in _rv:
        return _rv[k]
    if len(_rv) > 2:
        _rv.clear()
    g = Wd.on_twos(t)
    ink = Ink(t, int(t * 24))
    Wd.river(ink, g, 0.0, 1)
    p = Wd.tin(ink, TIN[0], TIN[1], TIN[2], g, **Wd.wave_pose(g, 1.0, T_TWAVE))
    _pencil_head(ink, t)
    Wd.trout_pair(ink, _trout_path, g, 0.86, kinds=(0, 2), pose="look", shade=0.5, gaze=(-2, -2))
    Wd.river_plane(ink, "front", g, 0.0, 1)
    _rv[k] = (ink.img.convert("RGB"), p["port"], p["port_r"])
    return _rv[k]


def _river_cam(t):
    return dict(x=key(t, [(10.8, 0.0), (13.8, -46.0)], "linear"), y=key(t, [(10.8, 0.0), (13.8, -6.0)], "linear"),
                zoom=key(t, [(10.8, 1.03), (13.8, 1.22)], "linear"))


def river_shot(t):
    pic, port, pr = river_pic(t)
    c = _river_cam(t)
    fr = cam.shoot([(pic, 1.0)], shake=key(t, [(10.8, 0.0), (11.3, 2.0), (13.4, 2.0), (13.8, 0.0)]), t=t, bg=(30, 60, 54), **c)
    x, y = cam.shoot_point(port[0], port[1], (W, H), 1.0, **c)
    return fr, (x, y), pr * c["zoom"]


# ------------------------------------------------------------------ the film ---
DIVE_IN = (7.4, 8.4)
GLASS_OUT = (8.4, 9.6)
SWING = (9.6, 10.8)
LOOK = (10.8, 13.8)
GLASS_IN = (13.8, 14.8)
DIVE_OUT = (14.8, 15.5)


def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if DIVE_IN[0] <= t < DIVE_IN[1]:                    # down through the page's ring into Turkey's seat
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat(t), rx, ry, ramp(t, *DIVE_IN), spin=30)
    if GLASS_OUT[0] <= t < GLASS_OUT[1]:                # out through the glass
        u = ramp(t, *GLASS_OUT)
        return cam.through_glass(seat(t), _beyond(t, u), PORT[0], PORT[1], R, u, far=0.45)
    if SWING[0] <= t < SWING[1]:                        # and round, to the left, to look back
        return cam.turn(open_water(t), river_shot(t)[0], ramp(t, *SWING), axis="y", direction=-1)
    if LOOK[0] <= t < LOOK[1]:
        return river_shot(t)[0]
    if GLASS_IN[0] <= t < GLASS_IN[1]:                  # back in through the small tin's porthole
        fr, (px, py), pr = river_shot(t)
        return cam.through_glass(fr, seat(t), px, py, pr, ramp(t, *GLASS_IN), far=0.45)
    if DIVE_OUT[0] <= t < DIVE_OUT[1]:                  # and up out of the ring
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat(t), rx, ry, 1 - ramp(t, *DIVE_OUT))
    return desk_frame(t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m16_trout.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.0, 0.6, 1.3, 1.9, 2.8, 3.4, 3.9, 4.5, 5.5, 6.6, 7.0, 7.25, 7.7, 8.1, 8.5, 8.9,
                                              9.3, 9.8, 10.2, 10.6, 11.0, 11.7, 12.2, 12.8, 13.3, 13.7, 14.1, 14.6, 15.0,
                                              15.4, 15.75, 16.3, 16.75, 17.4, 17.9, 18.6, 19.2, 19.9, 20.38, 20.7, 21.5,
                                              22.3, 22.5, 22.95]
    cols = 4
    tw, th = 480, 270
    sheet = Image.new("RGB", (cols * tw, ((len(ts) + cols - 1) // cols) * th), (20, 20, 24))
    t0 = time.time()
    for i, tt in enumerate(ts):
        fr = frame(tt).convert("RGB")
        d = ImageDraw.Draw(fr)
        d.rectangle([0, 0, 110, 24], fill=(0, 0, 0))
        d.text((6, 5), f"t={tt:.2f}", fill=(255, 255, 255))
        for a, b, c in CAPTIONS:
            if a <= tt < b:
                d.text((120, 5), c, fill=(255, 255, 0))
        sheet.paste(fr.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(out, f"{(time.time() - t0) / len(ts):.2f} s/frame")
