"""m25 · scene_turkey · the first friend, K. (board beats K1 to K12, film seconds 35.6 to 59.6; this clock = film - 35.6).

K1   0.0 ..  1.6  the pilot's page has landed upside down; two teal hands walk it round the right way up while the
                  eye sinks back into the seat
K2   1.6 ..  2.8  the index finger reads: under `panit`, under `by paniting`, up to the printed word "air"   (trace 20)
K3   2.8 ..  3.9  dive through the page's ring into the tin, facing its riveted back wall
K4   3.9 ..  5.2  the 180 degree turn, to the right, round to the glass
K5   5.2 ..  7.8  Turkey's seat, looking out: the pilot's drawing stands in the lock in pencil, its lines move into
                  the walker; Turkey's reflection panics; one wing-beat, one puff, the gauge 3 -> 2       (trace 20)
K6   7.8 ..  8.8  back up out of the ring
K7   8.8 ..  9.4  the sheet is turned over
K8   9.4 .. 12.0  a small k; the point over "Scuba helmet", over "Dry-air bubble", back beside the triangle button;
                  a small leaning triangle in the dashed ring                                             (17, 18)
K9  12.0 .. 14.8  `the air run out.` hard against the left end, no pause; a calm thought ring              (19, 20)
K10 14.8 .. 18.4  a small faint `a` high off the rule; the pencil up and not moving; then `little uncomfy`;
                  the thought opens, falls in, opens again                                                (21, 22)
K11 18.4 .. 22.4  eyes whip up to the plate she did not pick, and down; `it is not wet.`                  (23, 24)
K12 22.4 .. 24.0  the eye eases back to her whole column; the hand lifts off                              (25)

Nobody on this sheet used the rubber: there is no erase pose and no rub mark here.

Every seat is a whole picture (the desk with sheet, hands and head from people.py; the tin's inside handmade here;
Turkey's seat and the staged endings from the c25 world) and every change of seat is a cam.py move. The desk camera
is one perspective camera (cam.tilt) whose tilt, zoom and aim are keyed; the hands are laid after it at
cam.tilt_point of the pencil tip, so the hand is always where the line is being written.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page1_done(), page2(t) (the sheet
images, 1520 x 1960; page2(SECONDS) is K.'s whole column), desk_frame(t) and frame(t) (no badge) for the editor and
the next scene unit. frame(0.0) is the desk the pass lands on: page 1, front up, upside down.
Test:  python3 films/swarm/m25/scene_turkey.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c25"))
import world as w  # noqa: E402   (the c25 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

_spec = importlib.util.spec_from_file_location("c25_scene_turkey", FILMS / "swarm" / "c25" / "scene_turkey.py")
C25T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C25T)

W, H = 960, 540
key = cam.key

SECONDS = 24.0
CAPTIONS = [
    (14.3, 16.9, "The air runs out."),
    (18.1, 20.7, "A little uncomfy."),
    (21.3, 23.9, "It is not wet."),
]

TEAL = "teal"
HAIR = "braids"
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


class _Tgt:
    """A PIL image dressed as the thing the c25 world draws on (it only wants .d)."""

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")


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


def _lettered(box, text, seed, xh, sink=0.0, slant=None, fix=None):
    """A line in the child's pencil alphabet (people.py), as a Line. sink drops the whole line by that many px;
    fix(strokes, letter) may move strokes about (the far-up dot, the tailed stop)."""
    plan = P.WritePlan(box, text, seed, xh, slant)
    strokes = [[(x, y + sink) for x, y in st] for st in plan.strokes]
    letter = list(plan.letter)
    if fix:
        strokes = fix(strokes, letter)
    ln = Line(strokes, plan.xh)
    ln.letter = letter
    ln.x_end = max(ln.x_end, plan.x_end)
    return ln


# ---- page 1, as the pilot left it (traces 1 to 15) ----
def _pilots_page():
    """The page exactly as the pilot's scene unit left it, if that module is there and offers it; otherwise None
    and the page is lettered here from the board."""
    try:
        f = HERE / "scene_pilot.py"
        if not f.exists():
            return None
        spec = importlib.util.spec_from_file_location("m25_scene_pilot", f)
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


def _own_page1():
    """The pilot's finished front, lettered here from the board (used only if the pilot's module cannot give it)."""
    pg = P.sheet(SIZE, page=1, porthole=25)
    tg = _Tgt(pg)
    w.pilot_drawing(tg, 1.0, RING1, RING_R)
    u = lambda a, b: (RING1[0] + a * RING_R, RING1[1] + b * RING_R)
    P.graphite(pg, [[u(0.30, 0.44), u(0.40, 0.40), u(0.44, 0.47), u(0.50, 0.44), u(0.52, 0.52), u(0.42, 0.56), u(0.32, 0.52)]],
               2.2, 0.5, 251)                                       # the second, lighter tail (trace 4)
    bh = B(1, "a1.1")[3] - B(1, "a1.1")[1]
    xh = 0.46 * bh
    rw = B(1, "a1.1")[2] - B(1, "a1.1")[0]

    def put(ln, weight=1.0, seed=250):
        P.graphite(pg, ln.strokes, max(1.3, ln.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed)

    def over(ln, idx, seed, n=2):
        for k in range(n):
            ov = [[(x + 1.3 * (k + 1), y - 0.9 * (k + 1)) for x, y in st] for st, q in zip(ln.strokes, ln.letter) if q in idx]
            P.graphite(pg, ov, max(1.3, ln.xh * 0.15) * 1.25, 1.4, seed + k)

    nb = B(1, "name.line")
    put(_lettered((nb[0] + 30, nb[1], nb[2], nb[3]), "M", 250, 0.5 * (nb[3] - nb[1]), slant=0.3), 0.7)
    b = B(1, "a1.1")
    l1 = _lettered((b[0] + rw * 0.125, b[1], b[2], b[3]), "a trout", 251, xh)
    put(l1)
    l1b = _lettered((l1.x_end + 1.6 * xh, b[1], b[2] + 200, b[3]), "and the", 252, xh * 0.8)
    put(l1b)
    l1c = _lettered((l1b.x_end + 1.0 * xh, b[1], b[2] + 200, b[3]), "trout think it", 253, xh)
    put(l1c)
    x = min(l1c.x_end + 0.7 * xh, b[2] - 34)
    P.graphite(pg, [[(x, b[3] - 9), (x + 9, b[3] - 15), (x + 17, b[3] - 9), (x + 26, b[3] - 13)]], 2.6, 1.0, 254)   # the flattened a
    b = B(1, "a1.2")
    l2 = _lettered((b[0] + rw * 0.09, b[1], b[2], b[3]), "Bird in a bottle.", 255, xh)
    put(l2)
    over(l2, (0, 10), 256)
    b = B(1, "a2.1")
    put(_lettered((b[0] + rw * 0.25, b[1], b[2], b[3]), "panit", 257, xh * 1.25))
    b = B(1, "a3.1")
    l3 = _lettered((b[0] + 6, b[1], b[2], b[3]), "by", 258, xh * 1.15)
    put(l3, 1.3)
    over(l3, (0, 1), 259, 3)
    put(_lettered((l3.x_end + 1.0 * xh, b[1], b[2], b[3]), "paniting", 257, xh), 0.9)
    return pg


@lru_cache(None)
def page1_done():
    got = _pilots_page()
    return got if got is not None else _own_page1()


RW1 = B(1, "a1.1")[2] - B(1, "a1.1")[0]
PANIT_A = (B(1, "a2.1")[0] + 0.22 * RW1, B(1, "a2.1")[3] + 18)
PANIT_B = (B(1, "a2.1")[0] + 0.44 * RW1, B(1, "a2.1")[3] + 18)
BY_A = (B(1, "a3.1")[0] + 0.01 * RW1, B(1, "a3.1")[3] + 18)
BY_B = (B(1, "a3.1")[0] + 0.33 * RW1, B(1, "a3.1")[3] + 18)
AIR = (B(1, "q3")[0] + 404, B(1, "q3")[3] + 12)          # under the printed word "air" in the third stem

# ---- page 2: K.'s column, in this module's time ----
CW = B(2, "bolt1.1")[2] - B(2, "bolt1.1")[0]          # the column's width
LH = B(2, "bolt1.1")[3] - B(2, "bolt1.1")[1]          # one ruled line's height
XH = 0.50 * LH                                        # small, on the rule

# times (module seconds)
T_K = (9.5, 10.0)
T_TRI = (11.0, 11.9)
T_L1 = (12.2, 14.2)                 # the air run out.
T_A = (15.0, 15.4)                  # a
T_STUCK = (15.4, 16.2)              # pencil up, not moving
T_L2 = (16.2, 17.0)                 # little
T_L2B = (17.08, 18.0)               # uncomfy
T_L3 = (19.9, 21.25)                # it is not wet.
T_WHIP = (18.6, 19.0, 19.5, 19.9)   # up to the plates, held, and down


def _triangle():
    """The button's triangle, as she drew it in the dashed ring: small, leaning, a third of the ring wide; the left
    side down, the bottom side pressed, the right side back up and crossing a little past the top (trace 18)."""
    cx, cy = _mid(B(2, "draw1.circle"))
    cx -= 2
    cy += 3
    top, bl, br = (cx + 5, cy - 15), (cx - 12, cy + 11), (cx + 15, cy + 13)
    left = [top, (cx - 4, cy - 2), bl]
    base = [bl, (cx + 1, cy + 13), br]
    right = [br, (cx + 10, cy), (cx + 3, cy - 17), (cx + 1, cy - 20)]
    again = [(br[0] - 1, br[1] + 1), (cx + 1, cy + 14), (bl[0] + 1, bl[1] + 1)]
    return Line([left, base, again, right], 16.0)


def _fix_l3(strokes, letter):
    """The dot of the first i is put far up, against the printed word above; the full stop has a tail (trace 24)."""
    first = [k for k, q in enumerate(letter) if q == 0]
    if len(first) > 1:
        k = min(first, key=lambda j: sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(strokes[j], strokes[j][1:])))
        strokes[k] = [(x + 2, y - 1.15 * XH) for x, y in strokes[k]]
    x, y = strokes[-1][-1]
    strokes[-1] = list(strokes[-1]) + [(x + 0.5, y + 3), (x - 2.5, y + 8), (x - 5, y + 11)]
    return strokes


@lru_cache(None)
def _plans():
    d = {}
    nb = B(2, "name1.line")
    d["k"] = _lettered((nb[0] + 16, nb[1], nb[2], nb[3]), "k", 260, 0.40 * (nb[3] - nb[1]), slant=0.0)
    d["tri"] = _triangle()
    b = B(2, "bolt1.1")
    d["l1"] = _lettered((b[0] - 2, b[1], b[2], b[3]), "the air run out.", 261, XH, slant=0.02)
    b = B(2, "bolt2.1")
    d["a"] = _lettered((b[0] + 0.105 * CW, b[1], b[2], b[3]), "a", 262, XH * 0.82, sink=-0.34 * LH)
    d["l2"] = _lettered((b[0] + 0.19 * CW, b[1], b[2], b[3]), "little", 263, XH, slant=0.30)
    d["l2b"] = _lettered((d["l2"].x_end + 0.75 * XH, b[1], b[2] + 300, b[3]), "uncomfy", 264, XH, slant=0.05)
    b = B(2, "bolt3.1")
    d["l3"] = _lettered((b[0] + 0.075 * CW, b[1], b[2], b[3]), "it is not wet.", 265, XH, slant=0.04, fix=_fix_l3)
    return d


WEIGHT = {"k": 1.1, "tri": 1.0, "l1": 1.0, "a": 0.5, "l2": 1.05, "l2b": 1.05, "l3": 1.0}
SPANS = {"k": T_K, "tri": T_TRI, "l1": T_L1, "a": T_A, "l2": T_L2, "l2b": T_L2B, "l3": T_L3}
ORDER = ["k", "tri", "l1", "a", "l2", "l2b", "l3"]


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt = WEIGHT[name]
    wd = max(1.5, ln.xh * 0.135) * (0.82 + 0.22 * wt)          # a sharp pencil: a fine line
    if name == "tri":
        P.graphite(img, [s for k, s in enumerate(done) if k != 2], wd, wt, 266)
        P.graphite(img, [s for k, s in enumerate(done) if k == 2], wd * 1.2, 1.35, 267)      # the bottom side, pressed
    else:
        P.graphite(img, done, wd, wt, 260 + ORDER.index(name))
    return x, y, down


@lru_cache(None)
def _base2(n):
    if n == 0:
        return P.sheet(SIZE, page=2, porthole=25)
    img = _base2(n - 1).copy()
    _write(img, ORDER[n - 1], 1.0)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS gives K.'s whole column."""
    n = 0
    while n < len(ORDER) and SPANS[ORDER[n]][1] <= t:
        n += 1
    img = _base2(n).copy()
    for name in ORDER[n:]:
        a, b = SPANS[name]
        if t > a:
            _write(img, name, ramp(t, a, b))
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
        return ls / 1.26 * 0.94 * k * lerp(1.0, 0.70, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=WOOD, shadow=0)


def _aim(page, name, fx, dy=0.0):
    b = B(page, name)
    return (lerp(b[0], b[2], fx), b[3] + dy)


#        tilt  log zoom        aim (sheet px)   held at (screen)
ABOVE = (16.0, math.log(0.50), 760.0, 980.0, 480.0, 262.0)          # where the pass lands: nearly flat above the sheet
WIDE1 = (60.0, math.log(0.62), 760.0, 860.0, 480.0, 236.0)          # the seat: the pilot's page, the ring in the middle
READ = (54.0, math.log(1.02), 600.0, 1540.0, 440.0, 250.0)          # the pilot's three answers
RING = (58.0, math.log(0.80), 760.0, 900.0, 480.0, 250.0)           # the ring, to fall into
FLIPV = (88.0, math.log(0.70), 760.0, 900.0, 480.0, 236.0)          # the eye down at the desk's edge
NAME = (50.0, math.log(1.5), 440.0, 500.0, 450.0, 235.0)            # zone 5: the name line ...
PICK = (50.0, math.log(1.5), 450.0, 680.0, 450.0, 250.0)            # ... the plates and the dashed ring
RINGV = (48.0, math.log(1.75), 590.0, 730.0, 520.0, 262.0)          # ... close on the dashed ring
L1 = (46.0, math.log(1.6), 330.0, _aim(2, "bolt1.1", 0, -8)[1], 360.0, 300.0)
L2 = (46.0, math.log(1.6), 350.0, _aim(2, "bolt2.1", 0, -8)[1], 360.0, 300.0)
L3 = (46.0, math.log(1.6), 340.0, _aim(2, "bolt3.1", 0, -8)[1], 360.0, 300.0)
PLATES = (40.0, math.log(2.7), 430.0, 664.0, 480.0, 270.0)         # eyes up: the two plates
WIDE2 = (54.0, math.log(1.08), 440.0, 860.0, 470.0, 268.0)           # K.'s whole column
CAM_KEYS = [(0.0, ABOVE), (0.35, ABOVE), (1.5, WIDE1), (1.65, WIDE1), (2.2, READ), (2.75, READ), (3.2, RING), (8.8, RING),
            (9.1, FLIPV), (9.4, NAME), (10.0, NAME), (10.5, PICK), (10.85, PICK), (11.15, RINGV), (11.95, RINGV),
            (12.25, L1), (14.6, L1), (14.95, L2), (18.1, L2), (18.55, L3), (22.4, L3), (23.5, WIDE2)]
SHAKE_KEYS = [(0.0, 0.0), (1.5, 2.0), (8.7, 2.0), (8.8, 0.0), (9.4, 0.0), (9.6, 2.0), (15.3, 2.0), (15.4, 0.0), (16.2, 0.0),
              (16.4, 2.0), (18.5, 2.0), (18.6, 0.0), (19.9, 0.0), (20.1, 2.0), (22.4, 2.0), (23.4, 0.6)]


def view(t, shot=None):
    deg, lz, ax, ay, tx, ty = shot or key(t, CAM_KEYS, "smoother")
    return View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0 if shot else key(t, SHAKE_KEYS, "linear"), t)


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


def _desktop(page, angle=0.0, lift=0.0):
    """The desk plane with the sheet on it."""
    if angle % 360 == 0 and lift == 0:
        im = _desk_with_shadow().copy()
        im.paste(page, SO)
        return im
    im = _desk_plane().copy()
    P.lay(im, page, SC[0], SC[1], angle, 1.0, lift=lift)
    return im


def _closeness(v):
    return clamp((v.z * S - 0.62) / 0.7)


def _head(fr, t, closeness, turn=0.0, tilt=0.0, x=150.0, dy=0.0):
    if closeness > 0.97:
        return
    y = 590 + 330 * closeness + dy
    P.head_back(fr, x, y, TEAL, 1.15, tilt=tilt, hair=HAIR, turn=turn, t=t)


# ----------------------------------------------- where the pencil point is ---
AWAY1 = (1330.0, 1700.0)
AWAY2 = (1010.0, 1500.0)
T_TURNED = 1.45                                     # the sheet is the right way up


def _plate_pts():
    a, b = B(2, "plate1a"), B(2, "plate1b")
    ta = (a[0] + 250, a[3] - 4)                     # over "Scuba helmet"
    tb = (b[0] + 270, b[3] - 4)                     # over "Dry-air bubble"
    bt = (B(2, "btn1a")[2] + 14, B(2, "btn1a")[3] - 6)      # beside the triangle button, not touching it
    return ta, tb, bt


def pen(t):
    """(sheet point, pose, lift) of K.'s right hand from the moment the sheet is the right way up."""
    pl = _plans()

    def wr(name):
        x, y, down = pl[name].tip(ramp(t, *SPANS[name]))
        return (x, y), "write", 0 if down else 6

    if t < 9.1:                                    # page 1: the index finger reads the pilot's page (trace 20)
        p = key(t, [(T_TURNED, AWAY1), (1.85, PANIT_A), (2.1, PANIT_B), (2.25, BY_A), (2.5, BY_B), (2.78, AIR),
                    (8.5, AIR), (9.1, AWAY1)])
        lf = key(t, [(T_TURNED, 16), (1.8, 5), (1.86, 0), (2.1, 0), (2.17, 7), (2.25, 0), (2.5, 0), (2.62, 8), (2.78, 0),
                     (8.5, 0), (8.8, 14)])
        return p, "point", lf
    if t < T_K[0]:
        return key(t, [(9.1, (760, 700)), (T_K[0], pl["k"].start)]), "hover", key(t, [(9.1, 18), (T_K[0], 5)])
    if t < T_K[1]:
        return wr("k")
    if t < T_TRI[0]:                               # pencil up: over one plate, over the other, back to the first
        ta, tb, bt = _plate_pts()
        p = key(t, [(T_K[1], pl["k"].end), (10.3, ta), (10.42, ta), (10.58, tb), (10.7, tb), (10.84, bt), (10.9, bt),
                    (T_TRI[0], pl["tri"].start)])
        lf = key(t, [(T_K[1], 5), (10.15, 14), (10.3, 9), (10.9, 9), (10.95, 12), (T_TRI[0], 4)])
        return p, "hover", lf
    if t < T_TRI[1]:
        return wr("tri")
    if t < T_L1[0]:
        return key(t, [(T_TRI[1], pl["tri"].end), (T_L1[0], pl["l1"].start)]), "hover", key(t, [(T_TRI[1], 4), (12.05, 14), (T_L1[0], 5)])
    if t < T_L1[1]:
        return wr("l1")
    if t < T_A[0]:
        return key(t, [(T_L1[1], pl["l1"].end), (T_A[0], pl["a"].start)]), "hover", key(t, [(T_L1[1], 3), (14.6, 13), (T_A[0], 5)])
    if t < T_A[1]:
        return wr("a")
    if t < T_L2[0]:                                # pencil up, not moving (trace 21)
        e = pl["a"].end
        up = (e[0] + 20, e[1] + 6)
        p = key(t, [(T_A[1], e), (T_STUCK[0], up), (T_STUCK[1] - 0.14, up), (T_L2[0], pl["l2"].start)])
        return p, "hover", key(t, [(T_A[1], 3), (T_STUCK[0], 13), (T_STUCK[1] - 0.14, 13), (T_L2[0], 4)])
    if t < T_L2[1]:
        return wr("l2")
    if t < T_L2B[0]:
        return key(t, [(T_L2[1], pl["l2"].end), (T_L2B[0], pl["l2b"].start)]), "write", 7
    if t < T_L2B[1]:
        return wr("l2b")
    if t < T_L3[0]:                                # down to the third rule; it waits there while her eyes go up
        s = pl["l3"].start
        p = key(t, [(T_L2B[1], pl["l2b"].end), (18.5, (s[0] + 4, s[1] + 2)), (19.75, (s[0] + 4, s[1] + 2)), (T_L3[0], s)])
        return p, "hover", key(t, [(T_L2B[1], 3), (18.3, 13), (18.5, 10), (19.75, 10), (T_L3[0], 4)])
    if t < T_L3[1]:
        return wr("l3")
    p = key(t, [(T_L3[1], pl["l3"].end), (22.5, AWAY2)])           # the hand lifts off and stays off
    return p, "hover", key(t, [(T_L3[1], 2), (21.9, 18)])


def _still_t(t):
    """The hand's own clock: it stops dead while she is stuck, and while her eyes are on the plates."""
    if T_STUCK[0] <= t < T_STUCK[1] - 0.14:
        return T_STUCK[0]
    if 18.5 <= t < 19.75:
        return 18.5
    return t


# ------------------------------------------------------------ desk frames ---
def _left_hold(fr, v, t, p):
    P.hand(fr, *v.pt(p), pose="hold", tone=TEAL, scale=v.hs(p), flip=True, t=t, arm=140)


def _right(target, v, t):
    p, pose, lift = pen(t)
    arm = 60 if pose == "point" else key(t, [(10.0, 58), (10.3, 70), (11.9, 70), (12.2, 58)])
    P.hand(target, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=_still_t(t), lift=lift, arm=arm)


def _turn_angle(t):
    return 180.0 * (1 - cam.smooth(ramp(t, 0.4, 1.4)))


def _walk(fr, v, t):
    """Two hands walk the sheet round: each lies flat on the paper, goes a quarter turn with it, lifts and takes a
    new hold. The right pushes its side away, the left draws its side in."""
    u = ramp(t, 0.4, 1.4)
    rest = cam.smooth(ramp(t, 1.4, T_TURNED + 0.1))
    for flip, ph0, a0, a1, arm in ((False, 0.0, 62.0, -18.0, 62), (True, 0.25, 215.0, 128.0, 132)):
        q = (u * 2 + ph0 * 2) % 1.0 if 0 < u < 1 else (0.0 if u <= 0 else 0.0)
        if u >= 1:
            q = 0.0
        if q < 0.8:
            ang = lerp(a0, a1, q / 0.8)
            lift = 0.0
        else:                                             # the hand comes back for a new hold
            ang = lerp(a1, a0, cam.smooth((q - 0.8) / 0.2))
            lift = 12 * math.sin(math.pi * (q - 0.8) / 0.2)
        r = 640.0
        x = SC[0] + r * math.cos(math.radians(ang))
        y = SC[1] + 80 + r * 1.05 * math.sin(math.radians(ang))
        if flip:                                          # the left hand settles flat on the page
            hx, hy = SO[0] + 120, SO[1] + 1880
            x, y = lerp(x, hx, rest), lerp(y, hy, rest)
        elif rest > 0:
            x, y = lerp(x, SO[0] + AWAY1[0], rest), lerp(y, SO[1] + AWAY1[1], rest)
            lift = 14 * rest
        P.hand(fr, *v.dpt(x, y), pose="hold", tone=TEAL, scale=v.hs((760, 1300)), flip=flip, t=t, arm=arm, lift=lift or None)


def _rack(fr, at, amount, radius=230.0):
    """A shallow lens: sharp round the screen point `at`, soft away from it."""
    if amount <= 0.01:
        return fr
    soft = fr.filter(ImageFilter.GaussianBlur(2.6 * amount))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - at[0], (yy - at[1]) * 1.25)
    m = np.clip((d - radius * 0.55) / radius, 0, 1)
    return Image.composite(soft, fr, Image.fromarray((m * 255).astype(np.uint8), "L"))


def desk_frame(t, shot=None):
    """K.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t, shot)
    cl = _closeness(v)
    if t < T_TURNED + 0.1:                          # the sheet arrived upside down: two hands walk it round
        ang = _turn_angle(t)
        fr = v.render(_desktop(page1_done(), angle=ang))
        _walk(fr, v, t)
        sway = math.sin(math.pi * ramp(t, 0.4, 1.4))
        _head(fr, t, cl, tilt=-7 * sway, turn=-0.25 * sway, dy=120 * (1 - ease(t, 0.3, 1.3)))
        return fr
    if t < 8.8:                                   # the finger on the pilot's page
        fr = v.render(_desktop(page1_done()))
        _left_hold(fr, v, t, (120, 1880))
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    if t < 9.4:                                   # the page flip: down to the desk's edge, the sheet turned, back up
        first = t < 9.1
        lift = 26 * math.sin(math.pi * ramp(t, 8.8, 9.4))
        fr = v.render(_desktop(page1_done() if first else page2(t), lift=lift))
        e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
        P.hand(fr, e[0], e[1], pose="pass", tone=TEAL, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    # page 2
    fr = v.render(_desktop(page2(t)))
    if shot is None:
        a = key(t, [(10.0, 0.0), (10.3, 1.0), (11.9, 1.0), (12.2, 0.0)])        # the lens goes from the button to the ring
        if a > 0.01:
            at = key(t, [(10.3, _mid(B(2, "btn1a"))), (10.85, _mid(B(2, "btn1a"))), (11.2, _mid(B(2, "draw1.circle")))])
            fr = _rack(fr, v.pt(at), a)
    if cl < 0.9 or t > 22.6:
        _left_hold(fr, v, t, (150, 1620))
    _right(fr, v, t)
    _head(fr, t, cl)
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------- inside the tin (handmade) ---
PAL = w.PAL
T_DIVE = (2.8, 3.9)
T_TURN = (3.9, 5.2)
T_SEAT = (5.2, 7.8)
T_UP = (7.8, 8.8)
BEAT = 6.45                                        # the one counted wing-beat: a puff, a tick


def _rivet(d, x, y, r=5):
    d.ellipse([x - r + 2, y - r + 3, x + r + 2, y + r + 3], fill=(8, 6, 6, 150))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(96, 86, 74, 255), outline=(22, 18, 16, 255))
    d.ellipse([x - r + 1, y - r + 1, x, y], fill=(168, 150, 124, 255))


def _wall(seed, seams, k, lamp=None, light=None):
    """The inside of the bread-roll tin: pressed ribs, a little rust, flanges top and bottom, riveted seams."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array(PAL["wall"], np.float32) * 1.9
    rib = np.sin(yy * (2 * math.pi / 64.0))
    shade = 1 + 0.15 * rib + 0.09 * P.vnoise((H, W), 260, 20, seed, 3) + 0.05 * P.vnoise((H, W), 2.5, None, seed + 1)
    a = base[None, None, :] * shade[..., None]
    rust = np.clip(P.vnoise((H, W), 150, 60, seed + 2, 3) - 0.16, 0, 1) * 1.5
    a = a * (1 - rust[..., None] * 0.5) + np.array([112, 66, 40], np.float32) * rust[..., None] * 0.5
    wall = P.to_img(a).convert("RGBA")
    d = ImageDraw.Draw(wall)
    for (y0, y1) in ((0, 30), (H - 34, H)):
        d.rectangle([0, y0, W, y1], fill=(84, 76, 66, 255))
        d.line([0, y1 if y0 == 0 else y0, W, y1 if y0 == 0 else y0], fill=(16, 13, 11, 255), width=3)
    for sx in seams:
        d.rectangle([sx - 15, 0, sx + 15, H], fill=(78, 70, 60, 255))
        d.line([sx - 15, 0, sx - 15, H], fill=(128, 114, 96, 255), width=1)
        d.line([sx + 15, 0, sx + 15, H], fill=(14, 12, 10, 255), width=2)
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
        a = a * (1 + 1.6 * s * g[..., None]) + np.array(PAL["lamp"], np.float32) * g[..., None] * 0.24 * s
    if light:
        lx, col, s = light
        g = np.exp(-(((xx - lx) / 300) ** 2 + ((yy - 250) / 330) ** 2))
        a = a + np.array(col, np.float32) * g[..., None] * s
    return P.to_img(a).convert("RGB")


def _bar(d, x0, x1, y, r, base, hi):
    for k in range(-r, r + 1):
        f = k / r
        c = tuple(int(lerp(hi[i], base[i] * 0.45, clamp((f + 0.75) / 1.75))) for i in range(3))
        d.line([x0, y + k, x1, y + k], fill=c + (255,))


def _pipe(im, xs):
    d = ImageDraw.Draw(im, "RGBA")
    _bar(d, 0, W, 132, 11, tuple(int(c * 0.5) for c in PAL["brass_dk"]), tuple(int(c * 0.62) for c in PAL["brass"]))
    for x in xs:
        d.rectangle([x - 11, 112, x + 11, 152], fill=(40, 36, 32, 255), outline=(10, 9, 8, 255))
        _rivet(d, x, 119, 3)
        _rivet(d, x, 145, 3)


@lru_cache(None)
def tin_back():
    """Where the dive lands: the dark riveted back wall of the bread-roll tin, close, amber-lit from one side.
    Facing the wrong way: there is no window here, only a shut stowage hatch and the air pipe."""
    im = _wall(531, (188, 772), 0.42, lamp=(150, 80, 1.0))
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    a = np.asarray(im, np.float32) * (1.0 - 0.5 * np.clip((yy - 360) / 200, 0, 1))[..., None]
    im = P.to_img(a).convert("RGB")
    _pipe(im, (120, 480, 840))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([352, 214, 612, 426], 16, fill=(4, 3, 3, 190))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    im.paste(sh, (6, 9), sh)
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([352, 214, 612, 426], 16, fill=(50, 46, 42, 255), outline=(12, 10, 9, 255), width=3)
    d.line([360, 218, 604, 218], fill=(120, 108, 92, 150), width=2)
    for x in range(372, 600, 36):
        _rivet(d, x, 230, 4)
        _rivet(d, x, 410, 4)
    for y in (262, 378):
        d.rectangle([336, y - 13, 372, y + 13], fill=(62, 56, 48, 255), outline=(12, 10, 8, 255))
        _rivet(d, 346, y, 3)
        _rivet(d, 362, y, 3)
    d.ellipse([560, 302, 596, 338], outline=tuple(int(c * 0.6) for c in PAL["brass"]) + (255,), width=5)
    d.ellipse([572, 296, 584, 308], fill=(36, 30, 26, 255))
    return im


@lru_cache(None)
def tin_side():
    """The wall the turn passes: ribbed tin, two seams, the air pipe, and the river's green light coming round."""
    im = _wall(541, (300, 660), 0.38, light=(960, (40, 92, 84), 0.7))
    _pipe(im, (150, 480, 810))
    return im


# ------------------------------------------------ Turkey's seat, looking out ---
PP = w.PILOT_PLACES
WALK_AT = w.ring_xy(*PP["walker"])
WALK_H = PP["walker_h"] * w.PORT_R
REFL = dict(C25T.REFL)
PALE = (238, 236, 224)
_SLIDE = {"legs": (0, 1), "tunic": (1, 0.2), "bowl": (-0.3, -1), "fish": (-1, -0.1), "arms": (1, -0.2)}


def _wing(t):
    return max(8 + 5 * abs(math.sin(t * 15)), 96 * math.sin(math.pi * clamp((t - BEAT) / 0.5)))


def view_out(t):
    """Turkey's seat: the brass porthole from where he sits. Outside, in the lock, stands the pilot's drawing itself,
    in pale pencil line; its lines move into the walker. Low left on the glass, Turkey's reflection: the pilot wrote
    panic. One counted wing-beat: a puff of bubbles, and the gauge drops a tick."""
    ink = Ink(t, int(t * 24))
    w.seat_backdrop(ink, t)
    f = ease(t, 6.0, 7.0)
    if f > 0:                                      # the cut pieces slide in under the lines that have become them
        for k, part in enumerate(("legs", "tunic", "bowl", "fish", "arms")):
            a = ease(t, 6.15 + 0.14 * k, 6.65 + 0.14 * k)
            if a > 0:
                dx, dy = _SLIDE[part]
                o = 150 * (1 - a) ** 2
                w.walker(ink, WALK_AT[0] + dx * o, WALK_AT[1] + dy * o, WALK_H, parts=(part,), alpha=min(1.0, a * 2.5),
                         bowl_bubbles=t, phase=t * 3, amp=3 * a)
    la = 1 - ease(t, 7.0, 7.5)
    if la > 0:
        w.pilot_morph(ink, f, alpha=la, color=PALE)
        w.pilot_morph(ink, f, c=(w.PORT_C[0] + 1, w.PORT_C[1] + 1), alpha=0.5 * la, color=PALE)
    w.bubbles(ink, C25T.PUFF, t, t0=BEAT + 0.2, n=7, size=9.0, rise=190, spread=22, alpha=1 - ramp(t - BEAT - 0.2, 0.75, 1.25))
    w.turkey_reflection(ink, mood="panic", t=t, wing=_wing(t), **REFL)
    w.seat_frame(ink)
    C25T._gauge(ink, 3.0 - cam.key(t, [(BEAT + 0.2, 0.0), (BEAT + 0.3, 1.15), (BEAT + 0.5, 1.0)]), t)
    return ink.img.convert("RGB")


def seat_frame(t):
    br = 0.5 - 0.5 * math.cos((t - T_SEAT[0]) * 1.9)              # breath only
    return cam.shoot([(view_out(t), 1.0)], zoom=1.0 + 0.006 * br, y=-1.5 * br, bg=(14, 16, 18))


# ------------------------------------------- the thoughts (the class film) ---
TH_AT = (706, 178, 122)
_MUTE = ("badge", "bolt_mark")


def _nothing(*a, **k):
    return (0, 0)


def _c25(fn, u, cx, cy, r):
    """A staged ending of the class film at ITS scene second u, as K. pictures it: the square round (cx, cy) of
    half-side r fills the thought. The badge and the bolt's die are left out; the world is put back afterwards."""
    ink = Ink(u, int(u * 24))
    saved = {n: getattr(w, n) for n in _MUTE}
    for n in _MUTE:
        setattr(w, n, _nothing)
    try:
        fn(ink, u)
    finally:
        for n, f in saved.items():
            setattr(w, n, f)
    k = 16 / 9
    im = ink.img.convert("RGB")
    box = (int(cx - r * k), int(cy - r), int(cx + r * k), int(cy + r))
    big = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (14, 16, 18))
    big.paste(im, (-box[0], -box[1]))
    return big.resize((W, H), Image.BILINEAR)


def _thoughts(fr, t):
    x, y, r = TH_AT
    if 12.4 < t < 14.8:                           # bolt 1: a calm ring; she is sure
        u = key(t, [(12.4, 0.0), (12.9, 1.0), (14.3, 1.0), (14.8, 0.0)])
        inner = _c25(C25T.scene_runs_out, lerp(0.5, 3.9, ramp(t, 12.4, 14.8)), 262, 322, 214)
        return cam.thought(fr, inner, x, y, r, u, wobble=0, t=0, dim=0.0)
    if 15.6 < t < 18.4:                           # bolt 2: it opens, falls in, and opens again on something else
        u = key(t, [(15.6, 0.0), (16.0, 1.0), (16.2, 0.15), (16.6, 1.0), (17.9, 1.0), (18.4, 0.0)])
        if t < 16.2:                              # first try: only the bowl on its collar, close; nothing happens
            inner = _c25(C25T.scene_uncomfy, 0.0, 452, 236, 132)
        else:
            inner = _c25(C25T.scene_uncomfy, lerp(0.35, 3.3, ramp(t, 16.2, 18.4)), 486, 272, 232)
        return cam.thought(fr, inner, x, y, r, u, wobble=7, t=t, dim=0.0)
    if 19.8 < t < 22.4:                           # bolt 3: the river lifts off like a blind
        u = key(t, [(19.8, 0.0), (20.3, 1.0), (21.9, 1.0), (22.4, 0.0)])
        inner = _c25(C25T.scene_not_wet, lerp(0.3, 3.6, ramp(t, 19.8, 22.4)), 480, 262, 262)
        return cam.thought(fr, inner, x, y, r, u, wobble=3, t=t, dim=0.0)
    return fr


# ------------------------------------------------------------------ draw ---
def frame(t):
    """The 960 x 540 picture at module second t, without the badge."""
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 1.6:                                       # the eye rolls a little with the turning sheet, and settles
        e = math.sin(math.pi * ramp(t, 0.3, 1.5))
        return cam.shoot([(desk_frame(t), 1.0)], rot=-7 * e, zoom=1.0 + 0.05 * e, bg=WOOD)
    if t < T_DIVE[0]:
        return desk_frame(t)
    if t < T_DIVE[1]:                                 # down through the page's porthole
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), tin_back(), rx, ry, ramp(t, *T_DIVE), spin=30)
    if t < T_TURN[1]:                                 # and round, to the right, to look out
        return cam.turn(tin_back(), seat_frame(T_TURN[1]), ramp(t, *T_TURN), axis="y", direction=1, side=tin_side())
    if t < T_SEAT[1]:
        return seat_frame(t)
    if t < T_UP[1]:                                   # back up out of the ring
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat_frame(t), rx, ry, 1 - ramp(t, *T_UP))
    a, b, c, d = T_WHIP
    if a <= t < d:                                    # eyes up to the plate she did not pick, and down again
        if t < b:
            return cam.whip(desk_frame(t), desk_frame(t, PLATES), ramp(t, a, b), direction=-1, axis="y", blur=0.4)
        if t < c:
            return desk_frame(t, PLATES)
        return cam.whip(desk_frame(t, PLATES), desk_frame(t), ramp(t, c, d), direction=1, axis="y", blur=0.4)
    return _thoughts(desk_frame(t), t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    w.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() and not argv[0].startswith("--") else FILMS / "stills" / "m25_scene_turkey"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.6, 0.9, 1.2, 1.55, 1.95, 2.4, 2.78, 3.1, 3.4, 3.7, 4.1, 4.5, 4.9, 5.4, 6.2, 6.6, 6.9, 7.6, 8.1,
              8.5, 9.0, 9.25, 9.8, 10.4, 10.65, 11.5, 12.1, 13.0, 14.1, 14.5, 15.3, 15.9, 16.2, 17.0, 18.05, 18.8,
              19.2, 19.7, 20.6, 21.4, 22.0, 23.0, 23.9]
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
