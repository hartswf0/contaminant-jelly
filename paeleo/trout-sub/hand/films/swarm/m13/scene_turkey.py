"""m13 · scene_turkey · the first friend, A. (board beats A1 to A11, film seconds 32.0 to 56.5; this clock = film - 32).

A1   0.0 ..  2.0  the pilot's page has landed upside down; two teal hands turn it clockwise to face her; the pencil
                  dips at one fish, then the other                                                  (trace 23)
A2   2.0 ..  3.1  dive through the page's ring, into the tin, facing its back wall and the empty perch
A3   3.1 ..  4.4  the 180 degree turn to the right inside the tin; the brass porthole swings in
A4   4.4 ..  7.2  Turkey's seat, the long look out: the pilot's two fish hang on the glass in pencil and become two
                  trout in the river; the bell tips once; a red disc settles on it. No Turkey in his own view (23, 24)
A5   7.2 ..  8.2  back up out of the ring
A6   8.2 ..  8.9  the page flip: the eye goes down to the desk's edge, the sheet is turned, page 2 comes up
A7   8.9 .. 11.6  one firm capital; the point looks at both plates, goes to the dashed ring, stops, goes back to
                  look at the red button, returns and draws one small leaning oval                  (16, 17)
A8  11.6 .. 14.6  ending 1  `The` (a look up at the plate) `Dinner bell` with the D gone over / `to go off`
                                                                                                (18, 19, 20)
A9  14.8 .. 18.4  ending 2  `The dinner bell goes` to the column's edge; no room; stuck; back to the far left,
                  `of` in the margin, `and the fish go crazy` over the gutter                       (18, 21, 22)
A10 18.6 .. 21.6  ending 3  the point touches "crazy"; `The fish go quiet` / `and calm`; a wait; one dot, far off
                                                                                                (22, 25, 26)
A11 21.6 .. 24.5  pencil in the groove, the flat hand on the sheet, the sheet starts left

Every seat is a whole picture (the desk with sheet, hands and head from people.py; the tin's inside handmade here in
the c13 palette; Turkey's seat and the river from the c13 world) and every change of seat is a cam.py move. The desk
camera is one perspective camera (cam.tilt) whose tilt, zoom and aim are keyed; the hands are laid after it at
cam.tilt_point of the pencil tip, so the hand is always where the line is being written.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page1_done(), page2(t) (the sheet
images, 1520 x 1960; page2(SECONDS) is A.'s whole column), desk_frame(t) and frame(t) for the editor and the next
scene unit (frame(0.0) is the desk the pass lands on: page 1 upside down).
Test:  python3 films/swarm/m13/scene_turkey.py [out_dir] [t ...]     writes stills and a contact sheet.
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
sys.path.insert(0, str(FILMS / "swarm" / "c13"))
import world as Wd  # noqa: E402   (the c13 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

_spec = importlib.util.spec_from_file_location("c13_scene_turkey", FILMS / "swarm" / "c13" / "scene_turkey.py")
C13T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C13T)

W, H = 960, 540
key = cam.key

SECONDS = 24.5
CAPTIONS = [
    (14.6, 17.2, "The dinner bell to go off."),
    (18.4, 21.0, "The dinner bell goes off and the fish go crazy."),
    (21.6, 24.2, "The fish go quiet and calm."),
]

TEAL = "teal"
HAIR = "bun"
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


class _Pen:
    """The little the c13 world needs of an Ink to pencil the pilot's drawing onto any image."""

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")


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
        spec = importlib.util.spec_from_file_location("m13_scene_pilot", f)
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
    pg = P.sheet(SIZE, page=1, porthole=13)
    rb = B(1, "ring.in")
    c = _mid(rb)
    r = (rb[2] - rb[0]) / 2

    def rp(u, v):
        return (c[0] + u * r, c[1] + v * r)

    # the two ghosts in the ring (traces 2, 3), rubbed before the firm drawing went over
    P.graphite(pg, [_ell(*rp(-0.62, -0.28), 0.24 * r, 0.11 * r, -8)], 3.0, 0.8, 131)
    box = [rp(0.20, -0.10), rp(0.52, -0.16), rp(0.56, 0.04), rp(0.24, 0.10), rp(0.20, -0.10)]
    scr = [[rp(0.26 + 0.05 * k, -0.08 + 0.02 * (k % 2)), rp(0.29 + 0.05 * k, 0.02 - 0.02 * (k % 2))] for k in range(5)]
    P.graphite(pg, [box, [rp(0.36, 0.08), rp(0.42, 0.17), rp(0.46, 0.06)]] + scr, 3.0, 0.8, 132)
    a, b = rp(-0.90, -0.42), rp(-0.36, -0.14)
    P.rub_mark(pg, (a[0], a[1], b[0], b[1]), 0.85, 133)
    a, b = rp(0.16, -0.20), rp(0.60, 0.20)
    P.rub_mark(pg, (a[0], a[1], b[0], b[1]), 0.85, 134)
    Wd.pilot_drawing(_Pen(pg), 1.0, c, r)
    nb = B(1, "name.line")
    P.write_on(pg, (nb[0] + 10, nb[1] - 34, nb[2], nb[3] - 26), "S", 1.0, seed=130, weight=0.8, size=44)
    P.rub_mark(pg, (nb[0] - 30, nb[1] - 60, nb[0] + 230, nb[3] - 16), 0.9, 135)
    P.write_on(pg, (nb[0] + 16, nb[1], nb[2], nb[3]), "S", 1.0, seed=131, size=27)
    big = 0.56 * (B(1, "a1.1")[3] - B(1, "a1.1")[1])

    def line(name, text, seed, weight=1.0, x0=0.0):
        b = B(1, name)
        P.write_on(pg, (b[0] + x0, b[1], b[2], b[3]), text, 1.0, seed=seed, weight=weight, size=big)

    line("a1.1", "The trout.  The  trout   think's    the     sub      is       a", 132)
    line("a1.2", "Bell-ringer prank.", 133)
    line("a2.1", "freek out.", 134, 1.3)
    line("a2.1", "the", 135, 0.45, 420)
    line("a2.1", "sub.", 136, 0.4, 640)
    b = B(1, "a2.1")
    P.rub_mark(pg, (b[0] + 640, b[1], b[0] + 780, b[3] + 4), 0.4, 137)
    b = B(1, "a3.1")
    P.graphite(pg, [[(b[0] + 14, b[1] + 8), (b[0] + 40, b[1] + 7)]], 3.0, 1.0, 138)
    line("a3.1", "he is going to be turkey diner.", 138)
    return pg


# ---- page 2: A.'s column, in this module's time ----
def _letter_strokes(plan, idx):
    return [s for s, k in zip(plan.strokes, plan.letter) if k == idx]


def _u_letter_end(plan, idx):
    """Fraction of the line's time at which character idx is finished."""
    last = max(j for j, k in enumerate(plan.letter) if k == idx)
    n = -1
    for kind, a, b, p, q in plan.seg:
        if kind == "ink":
            n += 1
            if n == last:
                return b / plan.T
    return 1.0


def _along(pts, u):
    """The polyline as far as fraction u, and its tip."""
    if u <= 0:
        return [], pts[0]
    n = max(1, min(len(pts) - 1, int(round(u * (len(pts) - 1)))))
    return pts[:n + 1], pts[n]


# times (module seconds)
T_A = (9.0, 9.4)
T_OVAL = (11.22, 11.6)
T_THE = (12.0, 12.45)
T_D = (12.8, 13.0)
T_DOVER = (13.0, 13.28)
T_INNER = (13.28, 13.9)
T_B1B = (14.0, 14.6)
T_B2A = (14.85, 16.2)
T_STUCK = (16.2, 16.7)               # beyond the end of the line: no room
T_OF = (16.95, 17.2)
T_B2B = (17.3, 18.3)
T_YTAIL = (18.3, 18.4)
T_TOUCH = (18.6, 19.0)
T_B3A = (19.1, 20.2)
T_B3B = (20.3, 20.8)
T_WAIT = (20.8, 21.3)
T_DOT = (21.3, 21.42)

CW = B(2, "bolt1.1")[2] - B(2, "bolt1.1")[0]          # the column's width
XH = 0.63 * (B(2, "bolt1.1")[3] - B(2, "bolt1.1")[1])  # she writes high and large (trace 20)

TXT_THE = "The"
TXT_DIN = "Dinner   bell"
TXT_B1B = "to     go     off"
TXT_B2A = "The  dinner   bell   goes"
TXT_OF = "of"
TXT_B2B = "and    the   fish    go    crazy"
TXT_B3A = "The    fish    go     quiet"
TXT_B3B = "and     calm"


def _box(name, f0=0.0):
    b = B(2, name)
    return (b[0] + f0 * CW, b[1], b[2] + 400, b[3])


@lru_cache(None)
def _plans():
    nb = B(2, "name1.line")
    d = {
        "a": (P.write_plan((nb[0] + 26, nb[1], nb[2], nb[3]), "A", 140, XH * 1.3), 140, 1.3),
        "the": (P.write_plan(_box("bolt1.1", 0.12), TXT_THE, 141, XH), 141, 1.0),
        "din": (P.write_plan(_box("bolt1.1", 0.47), TXT_DIN, 142, XH), 142, 1.0),
        "b1b": (P.write_plan(_box("bolt1.2", 0.04), TXT_B1B, 143, XH * 0.92), 143, 1.0),
        "b2a": (P.write_plan(_box("bolt2.1", 0.07), TXT_B2A, 144, XH), 144, 1.0),
        "of": (P.write_plan(_box("bolt2.2", -0.125), TXT_OF, 145, XH * 0.92), 145, 1.0),
        "b2b": (P.write_plan(_box("bolt2.2", 0.015), TXT_B2B, 146, XH * 0.92), 146, 1.0),
        "b3a": (P.write_plan(_box("bolt3.1", 0.14), TXT_B3A, 147, XH), 147, 1.0),
        "b3b": (P.write_plan(_box("bolt3.2", 0.07), TXT_B3B, 148, XH * 0.92), 148, 1.0),
    }
    return d


def _write(img, name, u):
    plan, seed, weight = _plans()[name]
    done, x, y, down = plan.upto(u)
    P.graphite(img, done, max(1.2, plan.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed)
    return x, y, down


def _d_over():
    """The capital D gone over twice, each pass a little off the last (trace 18)."""
    plan = _plans()["din"][0]
    out = []
    for k, (dx, dy) in enumerate(((1.8, -1.2), (-1.4, 1.5))):
        for st in _letter_strokes(plan, 0):
            out += [(x + dx, y + dy) for x, y in st]
    return out


def _din_u(t):
    """`Dinner  bell` is one plan written in two goes: the D, then (after it is gone over) the rest."""
    ud = _u_letter_end(_plans()["din"][0], 0)
    if t < T_D[1]:
        return ud * ramp(t, *T_D)
    return lerp(ud, 1.0, ramp(t, *T_INNER))


def _ytail():
    """The tail of the y of "crazy", hanging down into the next friend's column (trace 22)."""
    plan = _plans()["b2b"][0]
    x, y = _letter_strokes(plan, len(TXT_B2B) - 1)[-1][-1]
    return [(x - 3 * k / 6 - 5 * math.sin(k / 6 * 1.4), y + 15 * k / 6) for k in range(7)]


def _oval():
    """One small, slightly leaning oval in the dashed ring: the button's shape, copied (trace 17)."""
    cx, cy = _mid(B(2, "draw1.circle"))
    return _ell(cx - 2, cy + 2, 13.5, 19.5, 14, -100, 285, 44)


def _dot_at():
    b = B(2, "bolt3.2")
    return (b[0] + 0.735 * CW, b[3] - 5)


def _it_a(img, t):
    if t > T_A[0]:
        _write(img, "a", ramp(t, *T_A))


def _it_oval(img, t):
    if t > T_OVAL[0]:
        pts, _ = _along(_oval(), ramp(t, *T_OVAL))
        P.graphite(img, [pts], 3.2, 1.0, 149)


def _it_the(img, t):
    if t > T_THE[0]:
        _write(img, "the", ramp(t, *T_THE))


def _it_din(img, t):
    if t > T_D[0]:
        _write(img, "din", _din_u(t))


def _it_dover(img, t):
    if t > T_DOVER[0]:
        pts, _ = _along(_d_over(), ramp(t, *T_DOVER))
        P.graphite(img, [pts], 3.6, 1.3, 142)


def _it_b1b(img, t):
    if t > T_B1B[0]:
        _write(img, "b1b", ramp(t, *T_B1B))


def _it_b2a(img, t):
    if t > T_B2A[0]:
        _write(img, "b2a", ramp(t, *T_B2A))


def _it_of(img, t):
    if t > T_OF[0]:
        _write(img, "of", ramp(t, *T_OF))


def _it_b2b(img, t):
    if t > T_B2B[0]:
        _write(img, "b2b", ramp(t, *T_B2B))


def _it_ytail(img, t):
    if t > T_YTAIL[0]:
        pts, _ = _along(_ytail(), ramp(t, *T_YTAIL))
        P.graphite(img, [pts], 3.4, 1.0, 146)


def _it_b3a(img, t):
    if t > T_B3A[0]:
        _write(img, "b3a", ramp(t, *T_B3A))


def _it_b3b(img, t):
    if t > T_B3B[0]:
        _write(img, "b3b", ramp(t, *T_B3B))


def _it_dot(img, t):
    if t > T_DOT[0]:
        x, y = _dot_at()
        P.graphite(img, [[(x - 1.2, y), (x + 1.2, y + 0.8)]], 5.0, 1.2, 150)


ITEMS = [(T_A[1], _it_a), (T_OVAL[1], _it_oval), (T_THE[1], _it_the), (T_INNER[1], _it_din), (T_DOVER[1], _it_dover),
         (T_B1B[1], _it_b1b), (T_B2A[1], _it_b2a), (T_OF[1], _it_of), (T_B2B[1], _it_b2b), (T_YTAIL[1], _it_ytail),
         (T_B3A[1], _it_b3a), (T_B3B[1], _it_b3b), (T_DOT[1], _it_dot)]
ITEMS.sort(key=lambda it: it[0])


@lru_cache(None)
def _base2(n):
    if n == 0:
        return P.sheet(SIZE, page=2, porthole=13)
    img = _base2(n - 1).copy()
    ITEMS[n - 1][1](img, 1e9)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS gives A.'s whole column."""
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
        return ls / 1.26 * 1.02 * k * lerp(1.0, 0.74, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=WOOD, shadow=0)


RING1 = _mid(B(1, "ring.in"))
#        tilt  log zoom        aim (sheet px)   held at (screen)
WIDE1 = (60.0, math.log(0.62), 760.0, 860.0, 480.0, 236.0)          # the pilot's page, the ring in the middle
RING = (58.0, math.log(0.80), RING1[0], RING1[1] + 40, 480.0, 238.0)
FLIP = (88.0, math.log(0.70), 760.0, 900.0, 480.0, 236.0)           # the eye down at the desk's edge
PICK = (50.0, math.log(1.50), 425.0, 640.0, 450.0, 250.0)           # zone 5: name, plates, the dashed ring
PICKUP = (50.0, math.log(1.50), 425.0, 800.0, 450.0, 262.0)
C8 = (42.0, math.log(1.55), 430.0, 870.0, 450.0, 262.0)             # ending 1
C8UP = (43.0, math.log(1.55), 420.0, 800.0, 450.0, 262.0)           # ... and the look up at the plate
C9A = (40.0, math.log(1.62), 400.0, 1000.0, 440.0, 262.0)           # ending 2: with the pencil along the line
C9B = (40.0, math.log(1.62), 600.0, 1000.0, 440.0, 262.0)           # ... to the column's edge, and stop
C9C = (40.0, math.log(1.62), 250.0, 1035.0, 440.0, 262.0)           # ... back past the start of the rule
C9D = (40.0, math.log(1.62), 560.0, 1040.0, 440.0, 262.0)
C10 = (40.0, math.log(1.50), 470.0, 1105.0, 440.0, 262.0)           # endings 2 and 3 together; then it does not move
WIDE2 = (58.0, math.log(0.66), 760.0, 900.0, 480.0, 236.0)
CAM_KEYS = [(0.0, WIDE1), (0.9, WIDE1), (1.9, RING), (8.2, RING), (8.55, FLIP), (8.9, PICK), (11.5, PICK), (11.95, C8),
            (12.45, C8), (12.62, C8UP), (12.72, C8UP), (12.9, C8), (14.55, C8), (15.0, C9A), (16.15, C9B), (16.7, C9B),
            (17.05, C9C), (17.35, C9C), (18.0, C9D), (18.6, C10), (21.6, C10), (23.2, WIDE2)]
SHAKE_KEYS = [(0.0, 2.5), (8.1, 2.5), (8.2, 0.0), (8.9, 0.0), (9.1, 2.2), (16.1, 2.2), (16.2, 0.0), (16.7, 0.0), (16.9, 2.2),
              (18.5, 2.2), (18.6, 0.0), (21.6, 0.0), (21.9, 2.0)]


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


def _head(fr, t, closeness, turn=0.0, tilt=0.0, x=236.0):
    if closeness > 0.97:
        return
    y = 590 + 330 * closeness
    P.head_back(fr, x, y, TEAL, 1.15, tilt=tilt, hair=HAIR, turn=turn, t=t)


def _focus(fr, at, r0=200.0, r1=560.0, blur=3.2):
    """Where the eye is: sharp round `at`, soft away from it (the close lens of A7)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - at[0], (yy - at[1]) * 1.5)
    m = np.clip((d - r0) / (r1 - r0), 0, 1)
    m = (m * m * (3 - 2 * m) * 255).astype(np.uint8)
    return Image.composite(fr.filter(ImageFilter.GaussianBlur(blur)), fr, Image.fromarray(m, "L"))


# ----------------------------------------------- where the pencil point is ---
PILOT_PL = Wd.PILOT_PLACES


def _ringpt(u, v):
    rb = B(1, "ring.in")
    r = (rb[2] - rb[0]) / 2
    return (RING1[0] + u * r, RING1[1] + v * r)


def _under(name, f, dy=10.0):
    """A point just under a box of page 2, a fraction f along it."""
    b = B(2, name)
    return (lerp(b[0], b[2], f), b[3] + dy)


def pen(t):
    """(sheet point, pose, lift) of A.'s pencil hand."""
    pl = {k: v[0] for k, v in _plans().items()}

    def wr(name, u):
        x, y, down = pl[name].tip(u)
        return (x, y), "write", 0 if down else 6

    if t < 8.55:                                   # page 1: one fish, then the other (she reads the fish, trace 23)
        f1, f2 = _ringpt(*PILOT_PL["fish1"]), _ringpt(*PILOT_PL["fish2"])
        p = key(t, [(1.15, (1180, 1330)), (1.42, f1), (1.62, f1), (1.82, f2), (2.1, f2), (7.3, f2), (8.2, (1040, 1260))])
        lf = key(t, [(1.15, 18), (1.4, 16), (1.5, 3), (1.6, 3), (1.7, 14), (1.84, 3), (1.98, 3), (2.3, 16)])
        return p, "hover", lf
    if t < T_A[0]:
        return key(t, [(8.55, (640, 560)), (T_A[0], pl["a"].start)]), "hover", key(t, [(8.8, 16), (T_A[0], 6)])
    if t < T_A[1]:
        return wr("a", ramp(t, *T_A))
    if t < T_OVAL[0]:                              # the plates, the ring, the button again, the ring
        ta = (B(2, "plate1a")[0] + 200, B(2, "plate1a")[3] - 8)
        tb = (B(2, "plate1b")[0] + 170, B(2, "plate1b")[3] - 8)
        bt = (B(2, "btn1b")[2] + 6, B(2, "btn1b")[3] + 2)
        ov = _oval()[0]
        hang = (ov[0] - 4, ov[1] + 2)
        p = key(t, [(T_A[1], pl["a"].end), (9.72, ta), (9.82, ta), (10.02, tb), (10.35, tb), (10.6, hang), (10.8, hang),
                    (10.98, bt), (11.1, bt), (T_OVAL[0], ov)])
        lf = key(t, [(T_A[1], 6), (9.6, 14), (9.72, 5), (9.82, 5), (9.92, 12), (10.02, 4), (10.35, 4), (10.45, 14),
                     (10.6, 9), (10.8, 9), (10.9, 16), (11.1, 16), (T_OVAL[0], 4)])
        return p, "hover", lf
    if t < T_OVAL[1]:
        _, p = _along(_oval(), ramp(t, *T_OVAL))
        return p, "write", 0
    if t < T_THE[0]:                               # down to ending 1: the point runs under the printed stem
        b = B(2, "bolt1")
        s0, s1 = (b[0] + 0.22 * CW, b[1] + 44), (b[0] + 0.56 * CW, b[1] + 44)
        p = key(t, [(T_OVAL[1], _oval()[-1]), (11.72, s0), (11.9, s1), (T_THE[0], pl["the"].start)])
        return p, "hover", key(t, [(T_OVAL[1], 4), (11.68, 14), (11.74, 8), (11.9, 8), (T_THE[0], 6)])
    if t < T_THE[1]:
        return wr("the", ramp(t, *T_THE))
    if t < T_D[0]:                                 # the look up at the plate: the pencil waits in the air
        p = key(t, [(T_THE[1], pl["the"].end), (12.58, pl["din"].start), (T_D[0], pl["din"].start)])
        return p, "hover", key(t, [(T_THE[1], 6), (12.55, 14), (12.72, 14), (T_D[0], 5)])
    if t < T_D[1]:
        return wr("din", _din_u(t))
    if t < T_DOVER[1]:
        _, p = _along(_d_over(), ramp(t, *T_DOVER))
        return p, "write", 0
    if t < T_INNER[1]:
        if t < T_INNER[0] + 0.06:
            x, y, _ = pl["din"].tip(_din_u(T_INNER[0] + 0.06))
            return key(t, [(T_INNER[0], _d_over()[-1]), (T_INNER[0] + 0.06, (x, y))]), "write", 6
        return wr("din", _din_u(t))
    if t < T_B1B[0]:
        return key(t, [(T_INNER[1], pl["din"].end), (T_B1B[0], pl["b1b"].start)]), "write", 7
    if t < T_B1B[1]:
        return wr("b1b", ramp(t, *T_B1B))
    if t < T_B2A[0]:
        return key(t, [(T_B1B[1], pl["b1b"].end), (T_B2A[0], pl["b2a"].start)]), "write", 8
    if t < T_B2A[1]:
        return wr("b2a", ramp(t, *T_B2A))
    if t < T_OF[0]:                                # beyond the end of the line there is no room; then the far left
        e = pl["b2a"].end
        far = (e[0] + 42, e[1] - 4)
        p = key(t, [(T_B2A[1], e), (T_B2A[1] + 0.12, far), (T_STUCK[1], far), (T_OF[0], pl["of"].start)])
        return p, "hover", key(t, [(T_B2A[1], 5), (T_B2A[1] + 0.12, 12), (T_STUCK[1], 12), (T_OF[0] - 0.04, 12), (T_OF[0], 5)])
    if t < T_OF[1]:
        return wr("of", ramp(t, *T_OF))
    if t < T_B2B[0]:
        return key(t, [(T_OF[1], pl["of"].end), (T_B2B[0], pl["b2b"].start)]), "write", 7
    if t < T_B2B[1]:
        return wr("b2b", ramp(t, *T_B2B))
    if t < T_YTAIL[1]:
        _, p = _along(_ytail(), ramp(t, *T_YTAIL))
        return p, "write", 0
    if t < T_B3A[0]:                               # she goes back and touches her own "crazy"
        i = TXT_B2B.index("crazy")
        cz = _letter_strokes(pl["b2b"], i + 1)[0][0]
        cz = (cz[0] + 4, B(2, "bolt2.2")[3] + 7)
        p = key(t, [(T_YTAIL[1], _ytail()[-1]), (18.56, (cz[0] + 40, cz[1] - 30)), (18.74, cz), (18.96, cz), (T_B3A[0], pl["b3a"].start)])
        return p, "hover", key(t, [(T_YTAIL[1], 3), (18.56, 14), (18.74, 2), (18.94, 2), (19.02, 12), (T_B3A[0], 5)])
    if t < T_B3A[1]:
        return wr("b3a", ramp(t, *T_B3A))
    if t < T_B3B[0]:
        return key(t, [(T_B3A[1], pl["b3a"].end), (T_B3B[0], pl["b3b"].start)]), "write", 8
    if t < T_B3B[1]:
        return wr("b3b", ramp(t, *T_B3B))
    dot = _dot_at()
    if t < T_DOT[0]:                               # lifts; a wait; then over to the right
        e = pl["b3b"].end
        up = (e[0] + 26, e[1] - 6)
        p = key(t, [(T_B3B[1], e), (T_B3B[1] + 0.14, up), (21.2, up), (T_DOT[0], dot)])
        return p, "hover", key(t, [(T_B3B[1], 5), (T_B3B[1] + 0.14, 15), (21.2, 15), (T_DOT[0] - 0.03, 9), (T_DOT[0], 3)])
    if t < T_DOT[1]:
        return dot, "write", 0
    return dot, "hover", key(t, [(T_DOT[1], 2), (21.75, 18)])


def _still_t(t):
    """The hand's own clock: it stops dead while she is stuck."""
    for a, b in (T_STUCK, T_WAIT):
        if a <= t < b:
            return a
    return t


# ------------------------------------------------------------ desk frames ---
def _left_hold(fr, v, t, p):
    P.hand(fr, *v.pt(p), pose="hold", tone=TEAL, scale=v.hs(p), flip=True, t=_still_t(t), arm=140)


def desk_frame(t):
    """A.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    cl = _closeness(v)
    if t < 1.2:                                   # the sheet arrived upside down: two flat hands turn it clockwise
        u = cam.smooth(ramp(t, 0.12, 1.12))
        ang = 180.0 + 180.0 * u
        fr = v.render(_desktop(page1_done(), angle=ang))
        w = math.radians(ang - 180.0)             # the left hand pushes its side away, the right draws its side in
        a = (SC[0] - 470 + 70 * math.sin(w), SC[1] + 330 - 520 * math.sin(w) * (1 - 0.45 * u))
        b = (SC[0] + 470 - 70 * math.sin(w), SC[1] - 60 + 520 * math.sin(w) * (1 - 0.45 * u))
        k = v.hs((760, 980), 1.0)
        P.hand(fr, *v.dpt(*a), pose="hold", tone=TEAL, scale=k, flip=True, t=t, arm=150)
        P.hand(fr, *v.dpt(*b), pose="hold", tone=TEAL, scale=k, t=t, arm=42)
        _head(fr, t, cl, tilt=10 * (1 - u), turn=0.2 * (1 - u))
        return fr
    if t < 8.2:                                   # the pencil over the two fish; and here she is found, hovering
        fr = v.render(_desktop(page1_done()))
        _left_hold(fr, v, t, (250, 1320))
        p, pose, lift = pen(t)
        P.hand(fr, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=t, lift=lift, arm=58)
        _head(fr, t, cl)
        return fr
    if t < 8.9:                                   # the page flip: down to the desk's edge, the sheet turned, back up
        first = t < 8.55
        lift = 26 * math.sin(math.pi * ramp(t, 8.2, 8.9))
        fr = v.render(_desktop(page1_done() if first else page2(t), lift=lift))
        e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
        P.hand(fr, e[0], e[1], pose="pass", tone=TEAL, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
        p, pose, lf = pen(t)
        P.hand(fr, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=t, lift=lf, arm=58)
        _head(fr, t, cl)
        return fr
    if t < 21.75:                                 # the pencil on page 2
        fr = v.render(_desktop(page2(t)))
        p, pose, lift = pen(t)
        if cl < 0.9:
            _left_hold(fr, v, t, (130, 1560))
        a = clamp((21.75 - t) / 0.15)
        P.hand(fr, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=_still_t(t), lift=lift,
               arm=key(t, [(9.4, 58), (9.7, 74), (11.6, 74), (11.9, 58)]), alpha=a)
        if 8.9 <= t < 11.6:                       # the close lens: the eye is on the button, then on the ring
            bt, rg = v.pt(_mid(B(2, "btn1b"))), v.pt(_mid(B(2, "draw1.circle")))
            nm = v.pt(_plans()["a"][0].start)
            at = key(t, [(9.0, nm), (9.45, nm), (9.85, bt), (10.35, bt), (10.6, rg), (10.8, rg), (10.98, bt), (11.1, bt), (11.25, rg)])
            fr = _focus(fr, at)
        look = math.sin(math.pi * ramp(t, 12.45, 12.82))
        _head(fr, t, cl, tilt=-5 * look)
        return fr
    # letting go: the pencil in the groove, the flat hand on the sheet, the sheet starts left
    dx = -150 * ease(t, 23.3, 24.6)
    fr = v.render(_desktop(page2(t), dx=dx))
    P.pencil(fr, *v.dpt(560, 108), angle=3, scale=v.hs((0, -200), 1.0))
    hp = key(t, [(21.75, (640, 1150)), (22.4, (640, 1560))])      # below her column, which stays in view
    a = clamp((t - 21.75) / 0.15)
    hx, hy = v.pt((hp[0] + dx, hp[1]))
    P.hand(fr, hx, hy, pose="hold", tone=TEAL, scale=v.hs(hp), t=t, arm=48, alpha=a,
           lift=key(t, [(21.75, 14), (22.3, 0)]))
    if _closeness(v) < 0.9:
        _left_hold(fr, v, t, (130 + dx * 0.3, 1560))
    _head(fr, t, cl)
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------- inside the tin (handmade) ---
PAL = Wd.PAL
PORT, R = Wd.PORT_C, Wd.PORT_R
T4 = 4.4


def _rivet(d, x, y, r=5):
    d.ellipse([x - r, y - r + 1, x + r + 2, y + r + 3], fill=(8, 6, 6, 170))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(92, 82, 70, 255), outline=(20, 16, 14, 255))
    d.ellipse([x - r + 1, y - r + 1, x, y], fill=(176, 158, 130, 255))


def _glow(a, x, y, rx, ry, col, k):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2))
    return a + np.array(col, np.float32) * g[..., None] * k


def _bar(d, x0, x1, y, r, base, hi):
    """A round bar lying across: dark underside, a lit line along the top."""
    for k in range(-r, r + 1):
        f = k / r
        c = tuple(int(lerp(hi[i], base[i] * 0.45, clamp((f + 0.75) / 1.75))) for i in range(3))
        d.line([x0, y + k, x1, y + k], fill=c + (255,))
    d.line([x0, y - r + 2, x1, y - r + 2], fill=tuple(min(255, int(v * 1.12)) for v in hi) + (255,), width=1)


def _feather(im, x, y, ang, length, col):
    lay = Image.new("RGBA", (length + 20, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pts = [(6, 20)] + [(6 + length * k / 10, 20 - 11 * math.sin(math.pi * (k / 10) ** 0.8)) for k in range(1, 10)] + [(6 + length, 20)] \
        + [(6 + length * k / 10, 20 + 9 * math.sin(math.pi * (k / 10) ** 0.8)) for k in range(9, 0, -1)]
    d.polygon(pts, fill=col + (255,))
    d.line([(2, 20), (6 + length, 20)], fill=(232, 222, 200, 255), width=2)
    for k in range(2, 10):
        xx = 6 + length * k / 10
        d.line([(xx, 20), (xx + 7, 12)], fill=(30, 22, 18, 120), width=1)
        d.line([(xx, 20), (xx + 7, 27)], fill=(30, 22, 18, 120), width=1)
    lay = lay.rotate(ang, Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", lay.size, (6, 4, 4, 0))
    sh.putalpha(lay.getchannel("A").filter(ImageFilter.GaussianBlur(3)).point(lambda q: int(q * 0.5)))
    im.paste(sh, (int(x - lay.width / 2 + 4), int(y - lay.height / 2 + 6)), sh)
    im.paste(lay, (int(x - lay.width / 2), int(y - lay.height / 2)), lay)


@lru_cache(None)
def tin_back():
    """Where the dive lands: the dark riveted back wall of the bread-roll tin, lamp-lit, and Turkey's perch seen
    from the seat side. No bird: we are where he sits."""
    a = Wd._steel(W, H, 31, PAL["wall"], ribs=64, rust=0.2)
    a = a * 0.62
    a = _glow(a, 250, 96, 330, 250, PAL["lamp"], 0.42)                 # the cabin lamp, up on the left
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a *= (1.0 - 0.55 * np.clip((yy - 380) / 200, 0, 1))[..., None]     # the floor end falls into the dark
    im = Wd._img(a).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for x in (176, 784):                                               # seams
        d.line([x, 0, x, H], fill=(14, 12, 10, 210), width=3)
        d.line([x + 3, 0, x + 3, H], fill=(128, 114, 96, 70), width=1)
        for y in range(24, H, 52):
            _rivet(d, x - 15, y)
            _rivet(d, x + 19, y)
    d.rectangle([0, 34, W, 46], fill=(16, 14, 12, 150))                # a rolled rim seam along the top
    d.line([0, 33, W, 33], fill=(150, 134, 110, 90), width=1)
    for x in range(40, W, 76):
        _rivet(d, x, 40, 4)
    # the lamp: a brass cage on a bracket
    lx, ly = 250, 92
    d.line([lx, 46, lx, ly - 30], fill=PAL["brass_dk"] + (255,), width=5)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([lx - 46, ly - 46, lx + 46, ly + 46], fill=PAL["lamp"] + (150,))
    halo = halo.filter(ImageFilter.GaussianBlur(16))
    im.paste(halo, (0, 0), halo)
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([lx - 19, ly - 24, lx + 19, ly + 22], fill=(255, 238, 190, 255), outline=PAL["brass_dk"] + (255,), width=2)
    for k in (-12, 0, 12):
        d.line([lx + k, ly - 24, lx + k, ly + 22], fill=PAL["brass"] + (255,), width=3)
    d.rectangle([lx - 22, ly - 31, lx + 22, ly - 23], fill=PAL["brass"] + (255,), outline=PAL["brass_dk"] + (255,))
    d.rectangle([lx - 22, ly + 20, lx + 22, ly + 27], fill=PAL["brass"] + (255,), outline=PAL["brass_dk"] + (255,))
    # the perch: a worn wooden bar on two brass brackets, a strap, the wood rubbed pale where he grips
    py = 352
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([246, py + 4, 744, py + 44], 14, fill=(4, 3, 3, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    im.paste(sh, (10, 12), sh)
    d = ImageDraw.Draw(im, "RGBA")
    for bx in (262, 698):
        d.polygon([(bx - 26, py - 64), (bx + 26, py - 64), (bx + 15, py + 22), (bx - 15, py + 22)], fill=PAL["brass_dk"] + (255,))
        d.polygon([(bx - 21, py - 60), (bx + 16, py - 60), (bx + 8, py + 18), (bx - 12, py + 18)], fill=PAL["brass"] + (255,))
        d.line([(bx - 19, py - 58), (bx - 11, py + 16)], fill=PAL["brass_hi"] + (200,), width=2)
        _rivet(d, bx - 8, py - 48, 4)
        _rivet(d, bx + 8, py - 48, 4)
    _bar(d, 232, 728, py, 17, PAL["twig"], PAL["twig_lt"])
    for gx in (418, 536):                                              # two pale places, a foot apart
        for k in range(-30, 31):
            al = int(120 * (1 - abs(k) / 30))
            d.line([gx + k, py - 15, gx + k, py + 4], fill=(226, 208, 176, al))
        for k in range(3):                                             # claw marks
            d.line([gx - 12 + 11 * k, py - 12, gx - 15 + 11 * k, py + 9], fill=(52, 34, 22, 190), width=2)
    for bx in (262, 698):                                              # the bar's ends in their rings
        d.ellipse([bx - 22, py - 21, bx + 22, py + 21], outline=PAL["brass_hi"] + (255,), width=5)
        d.ellipse([bx - 24, py - 23, bx + 24, py + 23], outline=PAL["brass_dk"] + (255,), width=2)
    _feather(im, 606, py + 104, 18, 74, (92, 62, 40))                  # what he leaves behind
    _feather(im, 372, py + 150, -30, 54, (120, 84, 52))
    return im


@lru_cache(None)
def tin_side():
    """The wall the turn passes: ribbed tin, a seam of rivets, an air pipe with its clips."""
    a = Wd._steel(W, H, 37, PAL["wall"], ribs=48, rust=0.3) * 0.5
    a = _glow(a, 0, 120, 420, 300, PAL["lamp"], 0.25)
    a = _glow(a, 960, 262, 300, 300, (60, 110, 104), 0.5)              # river light from the glass we are turning to
    im = Wd._img(a).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for y in (70, 470):
        d.line([0, y, W, y], fill=(12, 10, 10, 210), width=3)
        d.line([0, y + 3, W, y + 3], fill=(120, 108, 92, 70), width=1)
        for x in range(30, W, 58):
            _rivet(d, x, y - 14)
            _rivet(d, x, y + 18)
    _bar(d, 0, W, 196, 13, PAL["brass_dk"], PAL["brass_hi"])
    for x in (150, 480, 810):
        d.rectangle([x - 12, 174, x + 12, 218], fill=PAL["tin_dk"] + (255,), outline=(14, 12, 10, 255))
        _rivet(d, x, 181, 3)
        _rivet(d, x, 211, 3)
    return im


# ------------------------------------------------ Turkey's seat, looking out ---
FISH = (("fish1", 0.55, 1.30, 0.0), ("fish2", 1.00, 1.75, 1.7))       # group, fills from, to (s after arriving), phase
FISH_TO = ((402, 232), Wd.STAGE["fish2"])
BELL_TIP = (1.55, 2.45)
DISC = (1.95, 2.6)


def _bell_swing(u):
    return 15.0 * math.sin(math.pi * cam.smooth(ramp(u, *BELL_TIP)))


def _pencil_fish(im, group, c, alpha):
    """One of the pilot's fish as her own pencil lines, hanging on the glass on a sliver of the page's light."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Wd.pilot_drawing(_Pen(lay), {group: 1.0}, c, R, 1.0, (40, 40, 48))
    al = lay.getchannel("A")
    halo = al.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.6))
    paper = Image.new("RGBA", (W, H), (244, 240, 228, 0))
    paper.putalpha(halo.point(lambda q: int(q * 0.5 * alpha)))
    im.paste(paper, (0, 0), paper)
    if alpha < 1:
        lay.putalpha(al.point(lambda q: int(q * alpha)))
    im.paste(lay, (0, 0), lay)


def _fish(ink, t, u, i):
    g, t0, t1, ph = FISH[i]
    e = ease(u, t0, t1)
    home = Wd.ring_xy(*PILOT_PL[g])
    to = FISH_TO[i]
    cx, cy = lerp(home[0], to[0], e), lerp(home[1], to[1], e)
    bob = 4.0 * math.sin(t * 1.3 + ph) * e
    if e > 0:
        Wd.trout(ink, cx, cy + bob, length=lerp(PILOT_PL[g + "_len"] * R, 140.0, e), angle=PILOT_PL[g + "_angle"] * (1 - 0.5 * e),
                 phase=t * 6 + ph, amp=9.0 * e, lid=0.1, alpha=clamp(e * 1.25))
    if e < 1:
        _pencil_fish(ink.img, g, (PORT[0] + cx - home[0], PORT[1] + cy - home[1]), 1 - cam.smooth(clamp(e * 1.15)))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")


def view_out(t):
    """Turkey's seat: the brass porthole from where he sits, and what is outside it now. The pilot's drawing is
    outside. He is not in his own view: no reflection, no gauge (trace 24)."""
    u = max(t - T4, 0.0)
    ink = Ink(t, int(t * 24))
    Wd.seat_stage(ink, t, "back")
    sw = _bell_swing(u)
    cl = _bell_swing(u - 0.09) * 0.55
    co = _bell_swing(u - 0.22) * 1.25
    Wd.bell(ink, swing=sw, clapper=cl, cord=co, part="cord")
    Wd.seat_stage(ink, t, "front")
    _fish(ink, t, u, 0)                              # the upper one comes to rest behind the bell
    Wd.bell(ink, swing=sw, clapper=cl, cord=co, part="body", disc="circle" if u >= DISC[1] else None)
    if DISC[0] <= u < DISC[1]:                       # the red disc comes down through the water and settles on the dome
        f = ramp(u, *DISC)
        a = math.radians(sw)
        hx, hy = Wd.STAGE["bell_hang"]
        end = (hx + 104 * 0.56 * math.sin(a) - 4, hy + 104 * 0.56 * math.cos(a))
        e = cam.smooth(f)
        x = end[0] + 26 * (1 - e) * math.sin(f * 7.0)
        y = lerp(84.0, end[1], 1 - (1 - f) ** 2)
        Wd.button_disc(ink, "circle", x, y, r=9, alpha=clamp(f * 4))
    _fish(ink, t, u, 1)
    Wd.seat_frame(ink)
    return ink.img.convert("RGB")


def seat_frame(t):
    u = t - T4
    return cam.shoot([(view_out(t), 1.0)], x=key(t, [(T4, 0), (7.2, 10)]), y=key(t, [(T4, 0), (7.2, -5)]),
                     zoom=key(t, [(T4, 1.0), (7.2, 1.05)]), shake=1.5 * ramp(u, 0, 0.4), t=t, bg=(20, 22, 26))


# ------------------------------------------- the thoughts (the class film) ---
TH_AT = (830, 142, 110)
TH_LEFT = (166, 150, 110)


def _nothing(*a, **k):
    return None


_MUTE = ("turkey_reflection", "gauge", "bolt_mark", "badge", "bubbles", "bubble_on")


def _c13(tc):
    """The class film's staged ending at ITS module second tc, as she pictures it from Turkey's seat: the bell and
    the fish, through the brass ring. Turkey, his gauge, his bubbles, the bolt's die and the upper trout's speech
    bubble (the pilot's) are left out for this call; the world is put back afterwards."""
    ink = Ink(tc, int(tc * 24))
    saved = {n: getattr(Wd, n) for n in _MUTE}
    for n in _MUTE:
        setattr(Wd, n, _nothing)
    try:
        C13T.draw(tc, ink)
    finally:
        for n, f in saved.items():
            setattr(Wd, n, f)
    r = 240
    k = 16 / 9
    return ink.img.convert("RGB").crop((int(PORT[0] - r * k), PORT[1] - r, int(PORT[0] + r * k), PORT[1] + r)).resize((W, H), Image.BILINEAR)


# (opens, open, closing from, closed), class-film seconds at open and at close, wobble
TH1 = (13.2, 13.6, 14.3, 14.6)
TH2 = (17.0, 17.4, 18.1, 18.4)
TH3 = (19.0, 19.4, 20.2, 20.36, 20.75, 21.3, 21.6)


def _thoughts(fr, t):
    x, y, r = TH_AT
    if TH1[0] < t < TH1[3]:                           # ending 1: the knot pulled, the bell kicks right
        u = key(t, [(TH1[0], 0.0), (TH1[1], 1.0), (TH1[2], 1.0), (TH1[3], 0.0)])
        return cam.thought(fr, _c13(lerp(4.2, 5.7, ramp(t, TH1[0], TH1[3]))), x, y, r, u, wobble=0, t=t, dim=0.0)
    if TH2[0] < t < TH2[3]:                           # ending 2: the wheel of fish
        u = key(t, [(TH2[0], 0.0), (TH2[1], 1.0), (TH2[2], 1.0), (TH2[3], 0.0)])
        x, y, r = TH_LEFT                             # out over the desk, clear of the margin and the gutter
        return cam.thought(fr, _c13(lerp(10.6, 12.0, ramp(t, TH2[0], TH2[3]))), x, y, r, u, wobble=6, t=t, dim=0.0)
    if TH3[0] < t < TH3[6]:                           # ending 3: her own wheel, then the same fish gone still
        u = key(t, [(TH3[0], 0.0), (TH3[1], 1.0), (TH3[2], 1.0), (TH3[3], 0.15), (TH3[4], 1.0), (TH3[5], 1.0), (TH3[6], 0.0)])
        if t < TH3[3]:
            return cam.thought(fr, _c13(lerp(12.6, 13.9, ramp(t, TH3[0], TH3[3]))), x, y, r, u, wobble=5, t=t, dim=0.0)
        return cam.thought(fr, _c13(19.3), x, y, r, u, wobble=0, t=0, dim=0.0)
    return fr


# ------------------------------------------------------------------ draw ---
def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 1.3:                                       # the camera rolls level with the sheet as she turns it
        e = 1 - ease(t, 0.1, 1.25)
        return cam.shoot([(desk_frame(t), 1.0)], rot=-7 * e, zoom=1.0 + 0.06 * e, bg=WOOD)
    if t < 2.0:
        return desk_frame(t)
    if t < 3.1:                                       # down through the page's porthole
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), tin_back(), rx, ry, ramp(t, 2.0, 3.1), spin=30)
    if t < T4:                                        # and round, to the right, to look out
        return cam.turn(tin_back(), seat_frame(T4), ramp(t, 3.1, T4), axis="y", direction=1, side=tin_side())
    if t < 7.2:
        return seat_frame(t)
    if t < 8.2:
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat_frame(t), rx, ry, 1 - ramp(t, 7.2, 8.2))
    return _thoughts(desk_frame(t), t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() else FILMS / "stills" / "m13_scene_turkey"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.5, 0.9, 1.5, 1.9, 2.4, 2.8, 3.3, 3.75, 4.1, 4.5, 5.3, 6.0, 6.9, 7.5, 8.0, 8.4, 8.6, 9.3, 10.1,
              10.7, 11.5, 12.3, 12.65, 13.2, 13.8, 14.5, 15.6, 16.4, 17.1, 17.9, 18.8, 19.7, 20.5, 21.0, 21.5, 22.6, 24.3]
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
