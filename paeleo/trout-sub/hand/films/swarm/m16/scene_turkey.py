"""m16 · scene_turkey · the first friend, B. (board beats T1 to T10, film seconds 30.0 to 54.0; this clock = film - 30).

T1   0.0 ..  1.8  the pilot's page has landed a little askew; the plum left hand squares it; the right index finger
                  goes to the black window, to the faint head, and runs under `wave athis twin turkey`   (trace 25)
T2   1.8 ..  2.9  dive through the page's ring, into the tin, facing its riveted back wall
T3   2.9 ..  6.3  the 180 degree turn to the right; then, level, the look out from Turkey's seat: outside the glass
                  is the pilot's page (the pencil sub small and high, its window black, the faint head). Turkey
                  raises his wing; twelve frames later a pencil wing answers out of the black window  (3, 4, 25)
T4   6.3 ..  8.0  back up out of the ring; the sheet is turned over
T5   8.0 ..  9.8  a large firm green B; the point dips at both plates and at the triangle button; a triangle is
                  drawn in the dashed ring, its top left corner open                                (17, 18, 19)
T6   9.8 .. 11.8  two full lines are written with the lens on the sleeve: the page is a blur         (20)
T7  11.8 .. 13.8  the pencil turns round; both lines are rubbed out; the crumbs are brushed off; one small green
                  `a` is left under the second rule                                                  (20, 21)
T8  13.8 .. 17.8  THE LONG STILL HOLD: the point hangs over the first Plausible line and does not come down (22)
T9  17.8 .. 19.0  the hand goes down to Preposterous; a thought opens over the gutter: a second wing on OUR side
                  of the brass rim (the class film's bolt 3, small, a second of it)                  (25)
T10 19.0 .. 24.0  `there is`, a word's width of empty line, a small `a`, a stop, `another` bigger and climbing past
                  the rule; `turkey here` with the y looped down; a full stop pressed twice; the hand goes away;
                  the eye eases back to B.'s whole column; the finger finds "Pass it left again"     (23, 24)

Every seat is a whole picture (the desk with sheet, hands and head from people.py; the tin's inside handmade here
on the c16 world's recipe; Turkey's seat from the c16 world) and every change of seat is a cam.py move. The desk
camera is one perspective camera (cam.tilt) whose tilt, zoom and aim are keyed; the hands are laid after it at
cam.tilt_point of the pencil tip, so the hand is always where the line is being written.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page1_done(), page2(t) (the sheet
images, 1520 x 1960; page2(SECONDS) is B.'s whole column), desk_frame(t) and frame(t) for the editor and the next
scene unit (frame(0.0) is the desk the pass lands on: page 1, 12 degrees askew).
Test:  python3 films/swarm/m16/scene_turkey.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c16"))
import world as Wd  # noqa: E402   (the c16 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

_spec = importlib.util.spec_from_file_location("c16_scene_turkey", FILMS / "swarm" / "c16" / "scene_turkey.py")
C16T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C16T)

W, H = 960, 540
key = cam.key

SECONDS = 24.0
CAPTIONS = [
    (21.5, 24.0, "There is another turkey here."),
]

PLUM = "plum"
HAIR = "curly"
GREEN = (62, 118, 84)                   # B.'s coloured pencil (trace 17)
WOOD = (86, 62, 44)

# ------------------------------------------------------------ the sheet ---
S = 2                                   # lettered at twice 760 x 980 so the close shots stay sharp
SIZE = (760 * S, 980 * S)
DESK_SIZE = (2300, 2500)                # the desktop plane the camera looks at
SC = (1150, 1280)                       # the sheet's centre on it
SO = (SC[0] - SIZE[0] // 2, SC[1] - SIZE[1] // 2)


def B(page, name):
    return P.where(page, name, SIZE)


def _mid(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


RING1 = _mid(B(1, "ring.in"))
RING_R = (B(1, "ring.in")[2] - B(1, "ring.in")[0]) / 2
RING_SC = RING_R / 214.0                # sheet px per unit of the c16 world's pilot drawing
WINDOW = (RING1[0] - 16 * RING_SC, RING1[1] - 143 * RING_SC)        # the black window (trace 3)
FAINT_HEAD = (RING1[0] + 138 * RING_SC, RING1[1] - 92 * RING_SC)    # the faint turkey head (trace 4)


class Line:
    """Pencil strokes with their timing (ink at pencil speed, air between strokes): upto(u), tip(u)."""

    def __init__(self, strokes, xh=20.0):
        self.strokes = [list(s) for s in strokes if len(s) >= 2]
        self.xh = xh
        self.seg = []
        T = 0.0
        prev = None
        for pts in self.strokes:
            if prev is not None:
                air = math.hypot(pts[0][0] - prev[0], pts[0][1] - prev[1]) * 0.55 + 0.5 * xh
                self.seg.append(("air", T, T + air, prev, pts[0]))
                T += air
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


def _lettered(box, text, seed, xh, climb=0.0, sink=0.0):
    """A line in the child's pencil alphabet (people.py), as a Line. climb = how much the line rises per px along
    it (a word that climbs); sink drops the whole line by that many px."""
    plan = P.WritePlan(box, text, seed, xh)
    x0 = box[0]
    strokes = [[(x, y - climb * (x - x0) + sink) for x, y in st] for st in plan.strokes]
    ln = Line(strokes, plan.xh)
    ln.letter = list(plan.letter)
    return ln


def _ell(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=360.0, n=40):
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for k in range(n + 1):
        a = math.radians(lerp(a0, a1, k / n))
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


# ---- page 1, as the pilot left it (traces 1 to 15) ----
def _pilots_page():
    """The page exactly as the pilot's scene unit left it, if that module is there and offers it; otherwise None
    and the page is lettered here from the board."""
    try:
        f = HERE / "scene_pilot.py"
        if not f.exists():
            return None
        spec = importlib.util.spec_from_file_location("m16_scene_pilot", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "page1_done"):
            img = mod.page1_done()
        else:
            img = mod.page1(mod.SECONDS + 1.0)
        img = img.convert("RGB")
        return img if img.size == SIZE else img.resize(SIZE, Image.LANCZOS)
    except Exception:
        return None


@lru_cache(None)
def page1_done():
    got = _pilots_page()
    if got is not None:
        return got
    pg = P.sheet(SIZE, page=1, porthole=16)
    Wd.pilot_drawing(pg, RING1[0], RING1[1], 1.0, RING_SC)        # small and high; the window black; the faint head
    bh = B(1, "a1.1")[3] - B(1, "a1.1")[1]
    xh = 0.50 * bh

    def put(ln, weight=1.0, seed=160):
        P.graphite(pg, ln.strokes, max(1.2, ln.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed)

    b = B(1, "a1.1")
    l1 = _lettered((b[0] + 6, b[1], b[2], b[3]), "a giant threeheaded monster", 160, xh)
    put(l1, 1.0, 160)
    i = "a giant threeheaded monster".index("headed") + 4          # the "ed", gone over (trace 9)
    over = [[(x + 1.2, y - 0.8) for x, y in st] for st, k in zip(l1.strokes, l1.letter) if k in (i, i + 1)]
    P.graphite(pg, over, max(1.2, xh * 0.15) * 1.15, 1.3, 161)
    b = B(1, "a2.1")
    l2 = _lettered((b[0] + 2, b[1], b[2], b[3]), "wave athis twin", 162, xh)
    put(l2, 1.0, 162)
    l2b = _lettered((l2.x_end + 0.9 * xh, b[1], b[2], b[3]), "turkey", 163, xh * 1.25, climb=-0.05, sink=-12)
    put(l2b, 1.0, 163)                                             # starts high, larger, drops through the rule (11)
    b = B(1, "a3.1")
    l3 = _lettered((b[0] + 30, b[1], b[2], b[3]), "useinguphisenergy", 164, xh * 1.05, climb=0.02)
    put(l3, 1.0, 164)
    n = len("useinguphisenergy")
    over = [[(x + 1.0, y - 1.0) for x, y in st] for st, k in zip(l3.strokes, l3.letter) if k >= n - 3]
    P.graphite(pg, over, max(1.2, xh * 0.15) * 1.1, 1.25, 165)     # "rgy" gone over (trace 13)
    return pg


A2_UNDER = (B(1, "a2.1")[0] + 20, B(1, "a2.1")[3] + 16)
A2_UNDER_END = (B(1, "a2.1")[0] + 0.58 * (B(1, "a2.1")[2] - B(1, "a2.1")[0]), B(1, "a2.1")[3] + 16)

# ---- page 2: B.'s column, in this module's time ----
CW = B(2, "bolt1.1")[2] - B(2, "bolt1.1")[0]          # the column's width
LH = B(2, "bolt1.1")[3] - B(2, "bolt1.1")[1]          # one ruled line's height
XH = 0.56 * LH

# times (module seconds)
T_B = (8.0, 8.5)
T_TRI = (9.0, 9.8)
T_G1 = (9.98, 10.78)
T_G2 = (10.88, 11.52)
T_STRAY = (11.6, 11.74)
T_R1 = (12.0, 12.65)
T_R2 = (12.75, 13.3)
T_BRUSH = (13.4, 13.62)
T_HOLD = (13.8, 17.8)
T_SIGH = (16.0, 16.9)
T_W1 = (19.0, 19.6)                 # there is
T_WA = (19.72, 19.87)               # a
T_STOP = (19.9, 20.2)               # the point stops over the line
T_W2 = (20.2, 20.75)                # another
T_W3 = (20.85, 21.13)               # turkey
T_YT = (21.13, 21.21)               # the y's loop
T_W4 = (21.24, 21.41)               # here
T_DOT = (21.42, 21.5)               # the full stop, pressed and pressed again


def _col(name, f0=0.0, f1=1.6):
    b = B(2, name)
    return (b[0] + f0 * CW, b[1], b[0] + f1 * CW, b[3])


def _ghost(name, seed, tall_first):
    """A line of green marks of letter height, sticks and loops and humps in word-like runs: something written,
    which is never read (trace 20). Not letters."""
    b = B(2, name)
    rs = random.Random(seed)
    base = b[3] - 3
    x = b[0] + 10
    out = []
    first = True
    while x < b[2] - 26:
        for _ in range(rs.randint(2, 6)):
            if x > b[2] - 14:
                break
            h = XH * rs.uniform(0.85, 1.1)
            k = rs.random()
            dy = rs.uniform(-2, 2)
            if first and tall_first:
                out.append([(x + 5, base - 1.62 * XH), (x + 3, base - XH), (x + 2, base)])
                out.append(_ell(x + 9, base - 0.5 * h, 0.36 * h, 0.5 * h, 0, -80, 80, 14))
                x += 0.9 * XH
                first = False
                continue
            if k < 0.26:                                   # a stick, sometimes tall or hanging
                top = base - h * (1.55 if rs.random() < 0.4 else 1.0)
                bot = base + (0.6 * h if rs.random() < 0.2 else 0)
                sl = rs.uniform(-2, 3)
                out.append([(x + sl, top + dy), (x + sl * 0.4, (top + bot) / 2 + dy), (x, bot + dy)])
                x += 0.42 * XH
            elif k < 0.62:                                 # a loop that does not quite close
                a0 = rs.uniform(20, 70)
                out.append(_ell(x + 0.36 * h, base - 0.5 * h + dy, 0.34 * h, 0.48 * h, rs.uniform(-12, 12), a0, a0 + rs.uniform(250, 330), 20))
                x += 0.86 * XH
            else:                                          # a hump or two
                n = rs.choice((1, 1, 2))
                pts = [(x, base - h + dy), (x, base + dy)]
                for j in range(n):
                    x1 = x + 0.5 * h
                    pts += [(x + 0.08 * h, base - 0.75 * h + dy), (x + 0.28 * h, base - h + dy), (x1, base - 0.7 * h + dy), (x1, base + dy)]
                    x = x1
                out.append(pts)
                x += 0.3 * XH
        x += XH * rs.uniform(0.7, 1.2)
        first = False
    return Line(out, XH)


def _triangle():
    """The button's triangle, copied into the dashed ring: left side, right side, the base pressed; the two sides do
    not quite meet at the top left (trace 19)."""
    cx, cy = _mid(B(2, "draw1.circle"))
    left = [(cx - 3, cy - 21), (cx - 9, cy - 2), (cx - 14, cy + 16)]
    right = [(cx + 3, cy - 23), (cx + 9, cy - 3), (cx + 15, cy + 17)]
    base = [(cx - 16, cy + 17), (cx, cy + 18), (cx + 17, cy + 17)]
    return Line([left, right, base, [(cx + 16, cy + 18), (cx, cy + 19), (cx - 15, cy + 18)]], 20.0)


@lru_cache(None)
def _plans():
    nb = B(2, "name1.line")
    d = {}
    d["B"] = _lettered((nb[0] + 22, nb[1], nb[2], nb[3]), "B", 170, XH * 1.6)
    d["tri"] = _triangle()
    d["g1"] = _ghost("bolt1.1", 171, True)
    d["g2"] = _ghost("bolt1.2", 172, False)
    sb = B(2, "bolt2")
    d["stray"] = _lettered((sb[0] + 142, sb[1] - 15, sb[0] + 200, sb[1] + 9), "a", 173, 12.0)
    d["w1"] = _lettered(_col("bolt3.1", 0.10), "there is", 174, XH)
    xa = d["w1"].x_end + 6.0 * XH                              # a gap wide enough for a word (trace 23)
    b = B(2, "bolt3.1")
    d["wa"] = _lettered((xa, b[1], xa + 200, b[3]), "a", 175, XH * 0.85)
    d["w2"] = _lettered((d["wa"].x_end + 0.8 * XH, b[1], b[2] + 500, b[3]), "another", 176, XH * 1.36, climb=0.085)
    d["w3"] = _lettered(_col("bolt3.2", 0.03), "turkey", 177, XH)
    d["w4"] = _lettered((d["w3"].x_end + 1.6 * XH, B(2, "bolt3.2")[1], b[2] + 300, B(2, "bolt3.2")[3]), "here", 178, XH)
    x, y = [st for st, k in zip(d["w3"].strokes, d["w3"].letter) if k == 5][-1][-1]
    tail = [(x - 2.0 * k - 9 * math.sin(k / 9 * 2.6), y + 4.6 * k) for k in range(8)]         # down into "Pass it left again"
    ex, ey = tail[-1]
    tail += [(ex - 9, ey + 5), (ex - 14, ey - 1), (ex - 6, ey - 10), (ex + 8, ey - 20), (ex + 22, ey - 30)]
    d["yt"] = Line([tail], XH)
    return d


WEIGHT = {"B": 1.25, "tri": 1.05, "g1": 0.95, "g2": 0.95, "stray": 0.9, "w1": 1.0, "wa": 0.9, "w2": 1.05, "w3": 1.0,
          "w4": 1.0, "yt": 1.0}


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt = WEIGHT[name]
    P.graphite(img, done, max(1.3, ln.xh * 0.155) * (0.82 + 0.22 * wt), wt, 170 + len(name), GREEN)
    return x, y, down


def _dot_at():
    e = _plans()["w4"].end
    return (e[0] + 0.55 * XH, B(2, "bolt3.2")[3] - 4)


RUB_N = 6


def _rub_boxes(name):
    b = B(2, name)
    w = (b[2] - b[0] + 10) / RUB_N
    return [(b[0] - 6 + k * w - 14, b[1] + 1, b[0] - 6 + (k + 1) * w + 14, b[3] - 2) for k in range(RUB_N)]


def _rub(img, name, t, span, seed):
    for k, box in enumerate(_rub_boxes(name)):
        a = lerp(span[0], span[1], k / RUB_N)
        b_ = lerp(span[0], span[1], (k + 1.25) / RUB_N)
        P.rub_mark(img, box, ramp(t, a, b_), seed + k, P.PAPER)
        P.rub_mark(img, box, 0.45 * ramp(t, lerp(a, b_, 0.5), b_ + 0.08), seed + 40 + k, P.PAPER)      # back over it


def _it(name, span):
    def fn(img, t):
        if t > span[0]:
            _write(img, name, ramp(t, *span))
    return span[1], fn


def _it_rub(name, span, seed):
    def fn(img, t):
        if t > span[0]:
            _rub(img, name, t, span, seed)
    return span[1] + 0.2, fn


def _it_tri_base(img, t):
    pass


def _it_dot(img, t):
    if t > T_DOT[0]:
        x, y = _dot_at()
        P.graphite(img, [[(x - 1.4, y - 0.6), (x + 1.4, y + 0.8)]], 6.0, 1.3, 179, GREEN)
        if t > T_DOT[0] + 0.045:                          # ... and pressed again (trace 24)
            P.graphite(img, [[(x - 0.4, y - 1.2), (x + 1.8, y + 0.4)]], 6.4, 1.4, 178, GREEN)


# In PAINT order (the stray `a` lies over the rubbed patch: the rubber did not touch it).
ITEMS = [_it("B", T_B), _it("tri", T_TRI), _it("g1", T_G1), _it("g2", T_G2), _it_rub("bolt1.1", T_R1, 300),
         _it_rub("bolt1.2", T_R2, 320), _it("stray", T_STRAY), _it("w1", T_W1), _it("wa", T_WA), _it("w2", T_W2),
         _it("w3", T_W3), _it("yt", T_YT), _it("w4", T_W4), (T_DOT[1], _it_dot)]


@lru_cache(None)
def _base2(n):
    if n == 0:
        return P.sheet(SIZE, page=2, porthole=16)
    img = _base2(n - 1).copy()
    ITEMS[n - 1][1](img, 1e9)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS gives B.'s whole column."""
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

    def dpt(self, x, y):                 # desktop px -> screen
        return cam.tilt_point(x, y, self.deg, HOR, self.z, F, self.shift, DESK_SIZE)

    def pt(self, p):                     # sheet px -> screen
        return self.dpt(SO[0] + p[0], SO[1] + p[1])

    def ls(self, p):                     # screen px per 760-page px at that sheet point
        a = self.pt(p)
        b = self.pt((p[0] + 20, p[1]))
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 20 * S

    def hs(self, p, k=1.0):              # the hand's scale there (a little smaller as we lean in, so the words show)
        ls = self.ls(p)
        return ls / 1.26 * 1.02 * k * lerp(1.0, 0.72, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=WOOD, shadow=0)


#        tilt  log zoom        aim (sheet px)   held at (screen)
WIDE1 = (60.0, math.log(0.62), 760.0, 860.0, 480.0, 236.0)          # the pilot's page, the ring in the middle
RING = (58.0, math.log(0.78), 760.0, 900.0, 480.0, 250.0)           # the ring and the three written lines under it
FLIP = (88.0, math.log(0.70), 760.0, 900.0, 480.0, 236.0)           # the eye down at the desk's edge
NAME = (50.0, math.log(1.45), 440.0, 520.0, 450.0, 235.0)           # zone 5: the name line ...
PICK = (50.0, math.log(1.45), 440.0, 680.0, 450.0, 250.0)           # ... the plates and the dashed ring
C6 = (46.0, math.log(1.45), 430.0, 880.0, 440.0, 240.0)             # ending 1: both ruled lines
C8 = (46.0, math.log(1.30), 430.0, 950.0, 450.0, 236.0)             # endings 1 and 2: where nothing happens
C9 = (44.0, math.log(1.42), 470.0, 1120.0, 400.0, 300.0)            # ending 3, with room over the gutter
C10A = (42.0, math.log(1.6), 330.0, 1135.0, 420.0, 268.0)           # with the point along the line
C10M = (42.0, math.log(1.6), 500.0, 1132.0, 440.0, 268.0)           # ... where it stops
C10B = (42.0, math.log(1.6), 700.0, 1130.0, 470.0, 268.0)           # ... past the end of the rule, into the gutter
C10C = (42.0, math.log(1.6), 380.0, 1160.0, 430.0, 262.0)           # the second line
WIDE2 = (56.0, math.log(1.0), 440.0, 900.0, 480.0, 214.0)          # B.'s whole column
CAM_KEYS = [(0.0, WIDE1), (0.7, WIDE1), (1.7, RING), (7.3, RING), (7.65, FLIP), (8.0, NAME), (8.45, NAME), (8.95, PICK),
            (9.75, PICK), (10.05, C6), (11.9, C6), (12.5, C8), (17.8, C8), (18.4, C9), (19.0, C9), (19.25, C10A),
            (19.55, C10A), (19.9, C10M), (20.22, C10M), (20.7, C10B), (20.82, C10B), (21.1, C10C), (21.6, C10C), (23.0, WIDE2)]
SHAKE_KEYS = [(0.0, 2.5), (7.2, 2.5), (7.3, 0.0), (8.0, 0.0), (8.2, 2.0), (12.6, 2.0), (13.2, 0.0), (17.8, 0.0), (18.1, 2.2),
              (19.9, 2.2), (19.95, 0.6), (20.2, 0.6), (20.3, 2.2)]


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


def _desktop(page, angle=0.0, lift=0.0, dx=0.0):
    """The desk plane with the sheet on it."""
    if angle % 360 == 0 and lift == 0 and dx == 0:
        im = _desk_with_shadow().copy()
        im.paste(page, SO)
        return im
    im = _desk_plane().copy()
    P.lay(im, page, SC[0] + dx, SC[1], angle, 1.0, lift=lift)
    return im


def _closeness(v):
    return clamp((v.z * S - 0.62) / 0.7)


def _head(fr, t, closeness, turn=0.0, tilt=0.0, x=130.0, dy=0.0):
    if closeness > 0.97:
        return
    y = 590 + 330 * closeness + dy
    P.head_back(fr, x, y, PLUM, 1.15, tilt=tilt, hair=HAIR, turn=turn, t=t)


# ----------------------------------------------- where the pencil point is ---
HOVER = (B(2, "bolt2.1")[0] + 0.60 * CW, B(2, "bolt2.1")[3] - 5)          # over the first empty Plausible line
PASS2 = (B(2, "pass2")[0] + 150, B(2, "pass2")[3] - 8)
AWAY = (980.0, 1560.0)


def _under(name, f, dy=6.0):
    b = B(2, name)
    return (lerp(b[0], b[2], f), b[3] + dy)


def _rubber(t):
    """The rubber's place while it works along line 1, then line 2."""
    b1, b2 = B(2, "bolt1.1"), B(2, "bolt1.2")
    if t < T_R1[1]:
        return (lerp(b1[0] + 8, b1[2] - 6, ramp(t, *T_R1)), b1[3] - 12)
    if t < T_R2[0]:
        return key(t, [(T_R1[1], (b1[2] - 6, b1[3] - 12)), (T_R2[0], (b2[0] + 8, b2[3] - 12))])
    return (lerp(b2[0] + 8, b2[2] - 6, ramp(t, *T_R2)), b2[3] - 12)


def pen(t):
    """(sheet point, pose, lift) of B.'s right hand."""
    pl = _plans()

    def wr(name, span):
        x, y, down = pl[name].tip(ramp(t, *span))
        return (x, y), "write", 0 if down else 6

    if t < 7.65:                                   # page 1: the index finger reads somebody else's page (trace 25)
        p = key(t, [(0.55, (1330, 1560)), (0.95, WINDOW), (1.12, WINDOW), (1.3, FAINT_HEAD), (1.42, FAINT_HEAD),
                    (1.62, A2_UNDER), (2.1, A2_UNDER_END), (6.5, A2_UNDER_END), (7.3, (1200, 1500)), (7.65, (1100, 1300))])
        lf = key(t, [(0.55, 14), (0.9, 6), (0.97, 0), (1.12, 0), (1.2, 7), (1.3, 0), (1.42, 0), (1.52, 6), (1.62, 0), (2.1, 0), (6.5, 0), (7.0, 14)])
        return p, "point", lf
    if t < T_B[0]:
        return key(t, [(7.65, (700, 640)), (T_B[0], pl["B"].start)]), "hover", key(t, [(7.65, 18), (T_B[0], 6)])
    if t < T_B[1]:
        return wr("B", T_B)
    if t < T_TRI[0]:                               # the point dips at each plate, comes back to the triangle button
        ta = (B(2, "plate1a")[0] + 190, B(2, "plate1a")[3] - 8)
        tb = (B(2, "plate1b")[0] + 250, B(2, "plate1b")[3] - 8)
        bt = (B(2, "btn1a")[2] + 6, B(2, "btn1a")[3] + 2)
        p = key(t, [(T_B[1], pl["B"].end), (8.62, ta), (8.7, ta), (8.8, tb), (8.86, tb), (8.95, bt), (8.98, bt), (T_TRI[0], pl["tri"].start)])
        lf = key(t, [(T_B[1], 6), (8.56, 14), (8.63, 4), (8.7, 4), (8.75, 12), (8.8, 4), (8.86, 4), (8.9, 12), (8.95, 5), (8.98, 12), (T_TRI[0], 4)])
        return p, "hover", lf
    if t < T_TRI[1]:
        return wr("tri", T_TRI)
    if t < T_G1[0]:
        return key(t, [(T_TRI[1], pl["tri"].end), (T_G1[0], pl["g1"].start)]), "write", key(t, [(T_TRI[1], 4), (9.88, 14), (T_G1[0], 5)])
    if t < T_G1[1]:
        return wr("g1", T_G1)
    if t < T_G2[0]:
        return key(t, [(T_G1[1], pl["g1"].end), (T_G2[0], pl["g2"].start)]), "write", 8
    if t < T_G2[1]:
        return wr("g2", T_G2)
    if t < T_STRAY[0]:
        return key(t, [(T_G2[1], pl["g2"].end), (T_STRAY[0], pl["stray"].start)]), "write", 9
    if t < T_STRAY[1]:
        return wr("stray", T_STRAY)
    if t < T_R1[0]:                                # the pencil lifts, and is turned round
        p = key(t, [(T_STRAY[1], pl["stray"].end), (T_R1[0], _rubber(T_R1[0]))])
        return p, ("write" if t < 11.86 else "erase"), key(t, [(T_STRAY[1], 3), (11.86, 16), (T_R1[0], 0)])
    if t < T_R2[1]:
        return _rubber(t), "erase", (5 if T_R1[1] < t < T_R2[0] else 0)
    if t < T_BRUSH[0]:
        return _rubber(T_R2[1]), ("erase" if t < 13.35 else "hover"), key(t, [(T_R2[1], 2), (13.35, 16), (T_BRUSH[0], 5)])
    if t < T_HOLD[0]:                              # the side of the hand brushes the crumbs off to the right
        e = _rubber(T_R2[1])
        p = key(t, [(T_BRUSH[0], (e[0] - 120, e[1] + 6)), (T_BRUSH[1], (e[0] + 150, e[1] - 4)), (T_HOLD[0], HOVER)])
        return p, "hover", key(t, [(T_BRUSH[0], 5), (T_BRUSH[1], 5), (T_HOLD[0], 16)])
    if t < T_HOLD[1]:                              # it does not come down (trace 22)
        sigh = math.sin(math.pi * ramp(t, *T_SIGH)) ** 2
        return HOVER, "hover", 16 + 5 * sigh
    if t < T_W1[0]:
        p = key(t, [(T_HOLD[1], HOVER), (18.5, pl["w1"].start), (T_W1[0], pl["w1"].start)])
        return p, "hover", key(t, [(T_HOLD[1], 16), (18.5, 13), (18.8, 13), (T_W1[0], 3)])
    if t < T_W1[1]:
        return wr("w1", T_W1)
    if t < T_WA[0]:                                # over a word's width of empty line
        return key(t, [(T_W1[1], pl["w1"].end), (T_WA[0], pl["wa"].start)]), "write", 9
    if t < T_WA[1]:
        return wr("wa", T_WA)
    if t < T_W2[0]:                                # it stops
        e = pl["wa"].end
        up = (e[0] + 14, e[1] - 3)
        p = key(t, [(T_WA[1], e), (T_STOP[0], up), (T_STOP[1] - 0.06, up), (T_W2[0], pl["w2"].start)])
        return p, "hover", key(t, [(T_WA[1], 3), (T_STOP[0], 11), (T_STOP[1] - 0.06, 11), (T_W2[0], 3)])
    if t < T_W2[1]:
        return wr("w2", T_W2)
    if t < T_W3[0]:
        return key(t, [(T_W2[1], pl["w2"].end), (T_W3[0], pl["w3"].start)]), "write", 10
    if t < T_W3[1]:
        return wr("w3", T_W3)
    if t < T_YT[1]:
        return wr("yt", T_YT)
    if t < T_W4[0]:
        return key(t, [(T_YT[1], pl["yt"].end), (T_W4[0], pl["w4"].start)]), "write", 8
    if t < T_W4[1]:
        return wr("w4", T_W4)
    dot = _dot_at()
    if t < T_DOT[0]:
        return key(t, [(T_W4[1], pl["w4"].end), (T_DOT[0], dot)]), "write", 4
    if t < T_DOT[1]:
        return dot, "write", (0 if (t - T_DOT[0]) < 0.03 or (t - T_DOT[0]) > 0.05 else 3)
    if t < 22.6:                                   # the hand lifts away and stays away
        p = key(t, [(T_DOT[1], dot), (22.1, AWAY)])
        return p, "hover", key(t, [(T_DOT[1], 2), (21.8, 18)])
    p = key(t, [(22.6, (AWAY[0] - 60, AWAY[1] - 40)), (23.35, PASS2)])      # the finger finds "Pass it left again"
    return p, "point", key(t, [(22.6, 14), (23.25, 5), (23.4, 0)])


def _still_t(t):
    """The hand's own clock: it stops dead while she is stuck."""
    if T_STOP[0] <= t < T_STOP[1] - 0.06:
        return T_STOP[0]
    return t


def _crumbs(desk, t):
    """The rubber's crumbs: piling up behind it, then swept off to the right (drawn on the desktop plane)."""
    if not (T_R1[0] + 0.1 < t < T_HOLD[0] - 0.08):
        return
    n = int(round(14 * ramp(t, T_R1[0] + 0.1, T_R2[1])))
    b1, b2 = B(2, "bolt1.1"), B(2, "bolt1.2")
    sw = cam.smooth(ramp(t, T_BRUSH[0] + 0.03, T_BRUSH[1] + 0.08))
    dx = 900 * sw * sw
    P.eraser_crumbs(desk, SO[0] + lerp(b1[0], b1[2], 0.38) + dx, SO[1] + b1[3] + 6 - 20 * sw, n=(n + 1) // 2, seed=31, spread=110 - 50 * sw, scale=1.5)
    P.eraser_crumbs(desk, SO[0] + lerp(b2[0], b2[2], 0.62) + dx * 1.1, SO[1] + b2[3] + 8 - 30 * sw, n=n // 2, seed=32, spread=120 - 60 * sw, scale=1.5)


# ------------------------------------------------------------ desk frames ---
def _left_hold(fr, v, t, p):
    P.hand(fr, *v.pt(p), pose="hold", tone=PLUM, scale=v.hs(p), flip=True, t=t, arm=140)


ARM_KEYS = [(8.0, 58), (8.5, 58), (8.7, 72), (9.8, 72), (10.0, 58)]


def _right(target, v, t, alpha=1.0):
    p, pose, lift = pen(t)
    arm = key(t, ARM_KEYS) if pose != "point" else 60
    P.hand(target, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=_still_t(t), lift=lift, arm=arm, alpha=alpha)


def desk_frame(t):
    """B.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    cl = _closeness(v)
    if t < 0.9:                                   # the sheet arrived 12 degrees askew: the left hand squares it
        u = cam.smooth(ramp(t, 0.1, 0.8))
        ang = 12.0 * (1 - u)
        fr = v.render(_desktop(page1_done(), angle=ang))
        w = math.radians(ang)
        a = (SC[0] - 570 + 60 * math.sin(w), SC[1] + 780 - 560 * math.sin(w))     # its palm rides the sheet's left side
        P.hand(fr, *v.dpt(*a), pose="hold", tone=PLUM, scale=v.hs((190, 1760)), flip=True, t=t, arm=140)
        _right(fr, v, t)
        _head(fr, t, cl, tilt=5 * (1 - u), turn=0.15 * (1 - u))
        return fr
    if t < 7.3:                                   # the finger on the pilot's page
        fr = v.render(_desktop(page1_done()))
        _left_hold(fr, v, t, (190, 1760))
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    if t < 8.0:                                   # the page flip: down to the desk's edge, the sheet turned, back up
        first = t < 7.65
        lift = 26 * math.sin(math.pi * ramp(t, 7.3, 8.0))
        fr = v.render(_desktop(page1_done() if first else page2(t), lift=lift))
        e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
        P.hand(fr, e[0], e[1], pose="pass", tone=PLUM, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    # page 2
    desk = _desktop(page2(t))
    _crumbs(desk, t)
    a_rack = key(t, [(9.8, 0.0), (10.15, 1.0), (11.8, 1.0), (12.3, 0.0)], "smooth")
    if a_rack > 0.002:                            # T6: the lens is on the sleeve; the page is a blur (trace 20)
        base = v.render(desk)
        near = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _right(near, v, t)
        return cam.shoot([(base, 1.0), (near, 0.5)], focus=0.5, aperture=24 * a_rack, bg=WOOD)
    fr = v.render(desk)
    if cl < 0.9 or t > 22.0:
        _left_hold(fr, v, t, (150, 1620))
    _right(fr, v, t)
    if T_HOLD[0] - 0.6 < t < T_HOLD[1] + 0.6:     # the top of her head, low in the frame, while nothing is written
        sigh = math.sin(math.pi * ramp(t, *T_SIGH)) ** 2
        rise = cam.smooth(ramp(t, T_HOLD[0] - 0.6, T_HOLD[0])) * (1 - cam.smooth(ramp(t, T_HOLD[1], T_HOLD[1] + 0.6)))
        P.head_back(fr, 230, 880 - 196 * rise + 5 * sigh, PLUM, 1.15, tilt=2 * sigh, hair=HAIR, t=t)
    else:
        _head(fr, t, cl)
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------- inside the tin (handmade) ---
PAL = Wd.PAL
PORT, R = Wd.PORT, Wd.PORT_R
T_TURN = (2.9, 4.1)
T_WAVE = 4.6


def _rivet(d, x, y, r=5):
    d.ellipse([x - r + 2, y - r + 3, x + r + 2, y + r + 3], fill=(18, 12, 10, 150))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(112, 96, 76, 255), outline=(40, 30, 22, 255))
    d.ellipse([x - r + 1, y - r + 1, x, y], fill=(176, 156, 122, 255))


def _wall(seed, seams, k, lamp=None, light=None):
    """The inside of the bread-roll tin on the c16 world's recipe: pressed ribs, rust, flanges, welded seams."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array(PAL["cabin"], np.float32)
    rib = np.sin(yy * (2 * math.pi / 26.0))
    shade = 1 + 0.16 * rib + 0.10 * np.clip(rib - 0.7, 0, 1) * 6 + 0.09 * Wd.vnoise((H, W), 260, 20, seed, 3) + 0.05 * Wd.vnoise((H, W), 2.5, None, seed + 1)
    a = base[None, None, :] * shade[..., None]
    rust = np.clip(Wd.vnoise((H, W), 150, 60, seed + 2, 3) - 0.14, 0, 1) * 1.6
    a = a * (1 - rust[..., None] * 0.55) + np.array([120, 70, 40], np.float32) * rust[..., None] * 0.55
    wall = Wd.to_img(a).convert("RGBA")
    d = ImageDraw.Draw(wall)
    for (y0, y1) in ((0, 30), (H - 34, H)):
        d.rectangle([0, y0, W, y1], fill=(92, 78, 62, 255))
        d.line([0, y1 if y0 == 0 else y0, W, y1 if y0 == 0 else y0], fill=(30, 22, 16, 255), width=3)
    for sx in seams:
        d.rectangle([sx - 15, 0, sx + 15, H], fill=(86, 72, 58, 255))
        d.line([sx - 15, 0, sx - 15, H], fill=(132, 114, 90, 255), width=1)
        d.line([sx + 15, 0, sx + 15, H], fill=(28, 20, 16, 255), width=2)
    for x in range(18, W, 38):
        _rivet(d, x, 15)
        _rivet(d, x, H - 17)
    for sx in seams:
        for y in range(52, H - 40, 34):
            _rivet(d, sx, y)
    a = np.asarray(wall.convert("RGB"), np.float32) * k
    if lamp:
        lx, ly, s = lamp
        g = np.exp(-(((xx - lx) / 330) ** 2 + ((yy - ly) / 260) ** 2))
        a = a * (1 + 1.5 * s * g[..., None]) + np.array(PAL["lamp"], np.float32) * g[..., None] * 0.22 * s
    if light:
        lx, col, s = light
        g = np.exp(-(((xx - lx) / 300) ** 2 + ((yy - 250) / 330) ** 2))
        a = a + np.array(col, np.float32) * g[..., None] * s
    return Wd.to_img(a).convert("RGB")


def _bar(d, x0, x1, y, r, base, hi):
    for k in range(-r, r + 1):
        f = k / r
        c = tuple(int(lerp(hi[i], base[i] * 0.45, clamp((f + 0.75) / 1.75))) for i in range(3))
        d.line([x0, y + k, x1, y + k], fill=c + (255,))


@lru_cache(None)
def tin_back():
    """Where the dive lands: the dark riveted back wall of the bread-roll tin, close, lamp-lit from the side.
    Facing the wrong way: there is no window here, only a stowage hatch and an air pipe."""
    im = _wall(331, (188, 772), 0.40, lamp=(160, 70, 1.0))
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    a = np.asarray(im, np.float32) * (1.0 - 0.5 * np.clip((yy - 360) / 200, 0, 1))[..., None]
    im = Wd.to_img(a).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    _bar(d, 0, W, 132, 11, tuple(int(c * 0.55) for c in PAL["brass_dark"]), tuple(int(c * 0.6) for c in PAL["brass"]))
    for x in (120, 480, 840):
        d.rectangle([x - 11, 112, x + 11, 152], fill=(44, 36, 30, 255), outline=(12, 10, 8, 255))
        _rivet(d, x, 119, 3)
        _rivet(d, x, 145, 3)
    # a square stowage hatch, shut: a plate on the plates, two hinges, a ring-pull
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([352, 214, 612, 426], 16, fill=(4, 3, 3, 190))
    im.paste(sh.filter(ImageFilter.GaussianBlur(8)), (6, 9), sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([352, 214, 612, 426], 16, fill=(58, 49, 40, 255), outline=(16, 12, 10, 255), width=3)
    d.line([358, 218, 606, 218], fill=(124, 108, 86, 150), width=2)
    for x in range(372, 600, 36):
        _rivet(d, x, 230, 4)
        _rivet(d, x, 410, 4)
    for y in (262, 378):
        d.rectangle([336, y - 13, 372, y + 13], fill=(70, 58, 46, 255), outline=(14, 10, 8, 255))
        _rivet(d, 346, y, 3)
        _rivet(d, 362, y, 3)
    d.ellipse([560, 302, 596, 338], outline=tuple(int(c * 0.6) for c in PAL["brass"]) + (255,), width=5)
    d.ellipse([572, 296, 584, 308], fill=(40, 32, 26, 255))
    return im


@lru_cache(None)
def tin_side():
    """The wall the turn passes: ribbed tin, a seam, the air pipe, and the page's pale light coming round."""
    im = _wall(341, (300, 660), 0.36, light=(960, (150, 146, 128), 0.55))
    d = ImageDraw.Draw(im, "RGBA")
    _bar(d, 0, W, 132, 11, tuple(int(c * 0.55) for c in PAL["brass_dark"]), tuple(int(c * 0.6) for c in PAL["brass"]))
    for x in (150, 480, 810):
        d.rectangle([x - 11, 112, x + 11, 152], fill=(44, 36, 30, 255), outline=(12, 10, 8, 255))
        _rivet(d, x, 119, 3)
        _rivet(d, x, 145, 3)
    return im


# ------------------------------------------------ Turkey's seat, looking out ---
PSC = R / 214.0                                    # the pilot's drawing in the glass, as it was in the ring
WIN = (PORT[0] - 16 * PSC, PORT[1] - 143 * PSC)   # its black window


@lru_cache(None)
def _outside():
    """What is outside the glass: the pilot's page. Paper, the pencil sub small and high, its window black, the
    faint head to its right, the three faint lines; and a few pencil lines of water. No colour: nobody is sure."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.array(PAL["page"], np.float32)[None, None, :] * (0.97 + 0.03 * Wd.vnoise((H, W), 3, None, 77))[..., None]
    a *= (1.0 - 0.10 * np.clip((yy - 300) / 240, 0, 1))[..., None]
    im = Wd.to_img(a).convert("RGB")
    rs = random.Random(5)
    for k in range(7):                             # water: loose pencil lines, low in the glass
        y = PORT[1] + 40 + 20 * k + rs.uniform(-5, 5)
        x0 = PORT[0] - 170 + rs.uniform(0, 120)
        n = rs.randint(5, 9)
        pts = [(x0 + 22 * j, y + 4 * math.sin(j * 1.3 + k)) for j in range(n)]
        Wd.pencil_path(im, pts, weight=0.32, seed=40 + k)
    Wd.pilot_drawing(im, PORT[0], PORT[1], 1.0, PSC)
    return im


def _pencil_wing(im, m, seed):
    """The answer out of the black window: only a wing, in pencil. m = wave-degrees (0 hidden .. 112 up)."""
    if m < 1.0:
        return
    th = math.radians(m / 112.0 * 140.0)
    L = 62.0 * clamp(m / 34.0)
    dx, dy = math.sin(th), math.cos(th)            # hanging down at 0, swinging up to the right
    nx, ny = dy, -dx

    def at(u, s):
        return (WIN[0] + dx * L * u + nx * s, WIN[1] + dy * L * u + ny * s)

    out = [at(0.0, 0), at(0.25, 9), at(0.6, 12), at(0.9, 8), at(1.0, 0), at(0.86, -5), at(0.55, -7), at(0.2, -5), at(0.0, 0)]
    Wd.pencil_path(im, out, weight=0.85, seed=seed)
    for u in (0.5, 0.68, 0.84):                    # three primaries
        Wd.pencil_path(im, [at(u, 10), at(u + 0.2, 19 - 14 * (u - 0.5))], weight=0.7, seed=seed + int(u * 10))


def view_out(t):
    """Turkey's seat: the brass porthole from where he sits, his back at lower right, the gauge; and outside the
    glass, the pilot's page."""
    g = Wd.on_twos(t)
    ink = Ink(t, int(t * 24))
    ink.img.paste(_outside())
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    _pencil_wing(ink.img, -Wd.twin_wave(g, 1.0, T_WAVE), int(g * 4))        # twelve frames late (the rule)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.cabin(ink, g)
    Wd.air_gauge(ink, Wd.SEAT_GAUGE[0], Wd.SEAT_GAUGE[1], 1.0, Wd.SEAT_GAUGE[2], g)
    Wd.turkey_back(ink, Wd.SEAT_TURKEY[0], Wd.SEAT_TURKEY[1], Wd.SEAT_TURKEY[2], t=g, shade=0.16, **Wd.wave_pose(g, 1.0, T_WAVE))
    return ink.img.convert("RGB")


def seat_frame(t):
    br = 0.5 - 0.5 * math.cos((t - T_TURN[1]) * 1.9)              # breath only
    return cam.shoot([(view_out(t), 1.0)], zoom=1.0 + 0.006 * br, y=-1.5 * br, bg=(20, 22, 26))


# ------------------------------------------- the thought (the class film) ---
TH_AT = (706, 196, 124)
TH = (17.95, 18.35, 18.8, 19.02)
_MUTE = ("badge", "die_at_bolt", "die")


def _nothing(*a, **k):
    return (0, 0)


def _c16(tc):
    """The class film's staged ending (its bolt 3) at ITS module second tc, as B. pictures it: a second wing, the
    same cut-out as Turkey's, on our side of the brass rim. The badge and the bolt's die are left out for this
    call; the world is put back afterwards."""
    ink = Ink(tc, int(tc * 24))
    saved = {n: getattr(Wd, n) for n in _MUTE}
    for n in _MUTE:
        setattr(Wd, n, _nothing)
    try:
        C16T.draw(tc, ink)
    finally:
        for n, f in saved.items():
            setattr(Wd, n, f)
    cx, cy, r = 430, 300, 240
    k = 16 / 9
    return ink.img.convert("RGB").crop((int(cx - r * k), cy - r, int(cx + r * k), cy + r)).resize((W, H), Image.BILINEAR)


def _thoughts(fr, t):
    if TH[0] < t < TH[3]:
        u = key(t, [(TH[0], 0.0), (TH[1], 1.0), (TH[2], 1.0), (TH[3], 0.0)])
        x, y, r = TH_AT
        return cam.thought(fr, _c16(lerp(8.35, 9.6, ramp(t, TH[0], TH[3]))), x, y, r, u, wobble=3, t=t, dim=0.0)
    return fr


# ------------------------------------------------------------------ draw ---
def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 1.0:                                       # the camera rolls level as she squares the sheet
        e = 1 - ease(t, 0.1, 0.9)
        return cam.shoot([(desk_frame(t), 1.0)], rot=5 * e, zoom=1.0 + 0.07 * e, bg=WOOD)
    if t < 1.8:
        return desk_frame(t)
    if t < T_TURN[0]:                                 # down through the page's porthole
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), tin_back(), rx, ry, ramp(t, 1.8, T_TURN[0]), spin=30)
    if t < T_TURN[1]:                                 # and round, to the right, to look out
        return cam.turn(tin_back(), seat_frame(T_TURN[1]), ramp(t, *T_TURN), axis="y", direction=1, side=tin_side())
    if t < 6.3:
        return seat_frame(t)
    if t < 7.3:                                       # back up out of the ring
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat_frame(t), rx, ry, 1 - ramp(t, 6.3, 7.3))
    return _thoughts(desk_frame(t), t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() and not argv[0].startswith("--") else FILMS / "stills" / "m16_scene_turkey"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.5, 1.05, 1.35, 1.75, 2.1, 2.5, 2.8, 3.2, 3.5, 3.9, 4.3, 5.0, 5.4, 6.0, 6.6, 7.0, 7.5, 7.8, 8.3,
              8.75, 9.4, 9.9, 10.6, 11.5, 12.1, 12.9, 13.5, 14.0, 16.4, 17.7, 18.5, 19.3, 19.8, 20.1, 20.7, 21.2,
              21.6, 22.5, 23.9]
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
