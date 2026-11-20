"""m10 · scene_turkey · the first friend, M. (board part II, film seconds 32.0 to 57.5; this module's clock = film - 32).

T1   0.0 ..  0.5  the pass: whip left from the pilot's desk; the sheet lands sideways on the teal desk
T2   0.5 ..  3.0  a stranger's page: squared up, a finger on the firm jaw, the pale jaw, "freak out"; turned over
T3   3.0 ..  6.0  the pick: "M.", the point hangs over triangle, circle, triangle, circle (plates stay clean),
                  then the tall oval, copied from the button                                     (traces 16, 17)
T4   6.0 ..  7.1  dive through her own pencil oval, into the tin, facing its back wall
T5   7.1 ..  8.3  the 180 degree turn inside the tin: the glass swings in
T6   8.3 .. 11.5  Turkey's seat, looking out: the pilot's jaw hangs outside in pencil, talks on its one pin, becomes
                  the shell on the brick wall, and three trout come up to the glass and stay outside
T7  11.5 .. 12.5  back up out of the oval
T8  12.5 .. 15.0  bolt 1  `the trout to be` / `outsid`                                            (traces 18, 19)
T9  15.0 .. 17.0  stuck: camera locked; the point comes to rest on the "it" of "Pass it left again"   (trace 26)
T10 17.0 .. 19.6  bolt 2  `he dos not get beck`, off the end of its rule; the g gone round twice (20, 21, 22)
T11 19.8 .. 22.8  bolt 3  reads her own line, `the turkey gets` (tail on the y, g twice) / `bock`, vowel blotted
                                                                                           (22, 23, 24, 25)
T12 22.8 .. 25.5  letting go: pull back, teal hands on the edges, lift

Every seat is a whole picture (desk with sheet, hands and head from people.py; the tin and river from c10's world)
and every change of seat is a cam.py move. The desk camera is one real perspective camera (cam.tilt) whose tilt,
zoom and aim are keyed; the hands are laid after it at cam.tilt_point of the pencil tip.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page1_done() and page2(t) (the
written sheet images, 1520 x 1960) and desk_frame(t) for the editor and the next scene unit.
Test:  python3 films/swarm/m10/scene_turkey.py [out_dir] [t ...]     writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c10"))
import world as Wd  # noqa: E402   (the c10 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402

_spec = importlib.util.spec_from_file_location("c10_scene_turkey", FILMS / "swarm" / "c10" / "scene_turkey.py")
C10T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C10T)

W, H = 960, 540
ramp, ease, lerp, clamp = Wd.ramp, Wd.ease, Wd.lerp, Wd.clamp
key = cam.key

SECONDS = 25.5
CAPTIONS = [
    (15.0, 17.6, "The trout to be outside."),
    (19.6, 22.2, "He does not get back."),
    (22.8, 25.4, "The turkey gets back."),
]

TEAL, RUST = "teal", "rust"

# ------------------------------------------------------------ the sheet ---
S = 2                                   # the sheet is lettered at twice 760 x 980 so the close shots stay sharp
SIZE = (760 * S, 980 * S)
DESK_SIZE = (2300, 2500)                # the desktop plane the camera looks at
SC = (1150, 1280)                       # the sheet's centre on it
SO = (SC[0] - SIZE[0] // 2, SC[1] - SIZE[1] // 2)


def B(page, name):
    return P.where(page, name, SIZE)


def _mid(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def _xh(page, name, k):
    b = B(page, name)
    return k * (b[3] - b[1])


# ---- page 1, as the pilot left it (traces 1 to 15) ----
def _pilots_page():
    """The page exactly as the pilot's scene unit left it (scene_pilot.page1 at its last second), if that module
    is there; otherwise None and the page is lettered here from the board."""
    try:
        f = HERE / "scene_pilot.py"
        spec = importlib.util.spec_from_file_location("m10_scene_pilot", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        img = mod.page1(mod.SECONDS + 1.0).convert("RGB")
        return img if img.size == SIZE else img.resize(SIZE, Image.LANCZOS)
    except Exception:
        return None


@lru_cache(None)
def page1_done():
    got = _pilots_page()
    if got is not None:
        return got
    pg = P.sheet(SIZE, page=1, porthole=10)
    rb = B(1, "ring.in")
    cx, cy = _mid(rb)
    sc = (rb[2] - rb[0]) / 2 / 214.0
    Wd.pilot_drawing(pg, cx, cy, 1.0, sc, part="jaw")
    Wd.pilot_drawing(pg, cx, cy, 1.0, sc, part="outside", alpha=0.6)
    big = _xh(1, "a1.1", 0.80)

    def line(name, text, seed, x0=0, heavy=0.4):
        b = B(1, name)
        b = (b[0] + x0, b[1], b[2], b[3])
        P.write_on(pg, b, text, 1.0, seed=seed, weight=0.7, size=big)
        P.write_on(pg, b, text, heavy, seed=seed, weight=1.3, size=big)       # black at the left, pale by the right
        return b

    line("a1.1", "littlefrEnchfries.", 101)
    line("a1.2", "a new lockEd school", 102)
    line("a2.1", "freak out", 103)
    line("a3.1", "it is a Big container", 104)
    b = B(1, "a3.2")
    P.write_on(pg, b, "so", 1.0, seed=105, weight=1.2, size=big)
    P.write_on(pg, (b[0] + 150, b[1] + 10, b[2], b[3] + 6), "it", 1.0, seed=106, weight=0.8, size=big * 0.5)
    P.write_on(pg, (b[0] + 215, b[1], b[2], b[3]), "probibly takes it up", 1.0, seed=107, weight=0.75, size=big)
    return pg


# ---- page 2: M.'s column, in this module's time ----
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


def _loop(pts, turns, dx=1.6, dy=-1.2):
    """A letter's bowl gone round again `turns` times, each pass a little off the last."""
    out = []
    for k in range(turns):
        out += [(x + dx * (k + 1) * (1 if k % 2 == 0 else -0.7), y + dy * (k + 1) * (1 if k % 2 == 0 else -0.6)) for x, y in pts]
    return out


# times (module seconds)
T_M = (3.0, 3.5)
T_OVAL = (4.9, 6.0)
T_B1A = (12.6, 14.2)
T_B1B = (14.35, 15.0)
T_TICK = (16.0, 16.3)
T_B2 = (17.0, 19.2)
T_G1 = (19.2, 19.6)
T_B3A = (20.25, 20.9)         # the turkey
T_TAIL = (20.9, 21.05)
T_B3B = (21.05, 21.45)        # gets
T_G2 = (21.45, 21.6)
T_BOCK = (21.7, 22.2)
T_BLOT = (22.2, 22.8)

XH = None


def _sizes():
    global XH
    if XH is None:
        XH = _xh(2, "bolt1.1", 0.50)        # small, round, even
    return XH


def _box(name, x0=0.0, x1=None):
    b = B(2, name)
    return (b[0] + x0, b[1], b[2] if x1 is None else x1, b[3])


TXT_B1A, TXT_B1B = "the trout  to  be", "outsid"
TXT_B2 = "he  dos not  get beck"
TXT_B3A, TXT_B3B = "the turkey  gets", "bock"


@lru_cache(None)
def _plans():
    xh = _sizes()
    gut = B(2, "bolt4.1")[0] - 8                                   # the next column's left edge
    d = {
        "m": (P.write_plan(_box("name1.line", 14), "M.", 200, xh * 1.25), 200, 1.0),
        "b1a": (P.write_plan(_box("bolt1.1", 150), TXT_B1A, 201, xh), 201, 1.0),
        "b1b": (P.write_plan(_box("bolt1.2", 70), TXT_B1B, 202, xh * 0.92), 202, 0.7),
        "b2": (P.write_plan(_box("bolt2.1", 136, gut), TXT_B2, 203, xh * 1.2), 203, 1.0),
        "b3a": (P.write_plan(_box("bolt3.1", 130), TXT_B3A, 204, xh * 1.1), 204, 1.0),
        "b3b": (P.write_plan(_box("bolt3.2", 210), TXT_B3B, 205, xh * 1.1), 205, 1.0),
    }
    return d


def _write(img, name, u):
    plan, seed, weight = _plans()[name]
    done, x, y, down = plan.upto(u)
    P.graphite(img, done, max(1.2, plan.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed)
    return x, y, down


def _g_loop(name, text):
    plan = _plans()[name][0]
    i = text.index("g")
    return _loop(_letter_strokes(plan, i)[0], 2)


def _tail_pts():
    plan = _plans()["b3a"][0]
    i = TXT_B3A.index("y")
    x, y = _letter_strokes(plan, i)[-1][-1]
    x0 = _letter_strokes(plan, TXT_B3A.index("t", 4))[0][0][0]        # back as far as the t of turkey
    n = 14
    return [(lerp(x, x0 + 30, k / n), y + 3 + 5 * math.sin(k / n * math.pi) - 2 * k / n) for k in range(n + 1)]


def _blot_pts():
    plan = _plans()["b3b"][0]
    o = _letter_strokes(plan, TXT_B3B.index("o"))[0]
    xs = [p[0] for p in o]
    ys = [p[1] for p in o]
    stem = [(max(xs) + 1, min(ys) + 1), (max(xs) + 2, max(ys) + 2)]      # the stick that would make it an "a"
    return _loop(o, 2, 1.4, 1.0) + stem + _loop(o, 2, -1.8, -1.2) + stem[::-1] + _loop(o, 1, 0.6, 2.0)


def _tick_at():
    b = B(2, "pass2")
    return (b[0] + 0.213 * (b[2] - b[0]), b[1] + 0.50 * (b[3] - b[1]))


def _b3_u(t):
    """One plan for `the turkey  gets`, written in two goes with the tail between."""
    ua = _u_letter_end(_plans()["b3a"][0], TXT_B3A.index("y"))
    if t < T_B3A[1]:
        return ua * ramp(t, *T_B3A)
    return lerp(ua, 1.0, ramp(t, *T_B3B))


def _it_m(img, t):
    _write(img, "m", ramp(t, *T_M))


def _it_oval(img, t):
    u = ramp(t, *T_OVAL)
    if u > 0:
        cx, cy = _mid(B(2, "draw1.circle"))
        Wd.friend_mark(img, "circle", cx, cy + 2, u, OVAL_SC)


def _it_b1a(img, t):
    if t > T_B1A[0]:
        _write(img, "b1a", ramp(t, *T_B1A))


def _it_b1b(img, t):
    if t > T_B1B[0]:
        _write(img, "b1b", ramp(t, *T_B1B))


def _it_tick(img, t):
    if t > T_TICK[0]:
        x, y = _tick_at()
        pts, _ = _along([(x - 3, y + 9), (x, y), (x + 2, y - 12), (x + 5, y - 20)], ramp(t, T_TICK[0], T_TICK[0] + 0.12))
        P.graphite(img, [pts], 3.2, 1.3, 31)


def _it_b2(img, t):
    if t > T_B2[0]:
        _write(img, "b2", ramp(t, *T_B2))


def _it_g1(img, t):
    if t > T_G1[0]:
        pts, _ = _along(_g_loop("b2", TXT_B2), ramp(t, *T_G1))
        P.graphite(img, [pts], 3.4, 1.4, 41)


def _it_b3(img, t):
    if t > T_B3A[0]:
        _write(img, "b3a", _b3_u(t))


def _it_tail(img, t):
    if t > T_TAIL[0]:
        pts, _ = _along(_tail_pts(), ramp(t, *T_TAIL))
        P.graphite(img, [pts], 2.8, 1.0, 43)


def _it_g2(img, t):
    if t > T_G2[0]:
        pts, _ = _along(_g_loop("b3a", TXT_B3A), ramp(t, *T_G2))
        P.graphite(img, [pts], 3.4, 1.4, 45)


def _it_bock(img, t):
    if t > T_BOCK[0]:
        _write(img, "b3b", ramp(t, *T_BOCK))


def _it_blot(img, t):
    if t > T_BLOT[0]:
        pts, _ = _along(_blot_pts(), ramp(t, *T_BLOT))
        P.graphite(img, [pts], 4.0, 1.5, 47)


OVAL_SC = 1.3
ITEMS = [(T_M[1], _it_m), (T_OVAL[1], _it_oval), (T_B1A[1], _it_b1a), (T_B1B[1], _it_b1b), (T_TICK[1], _it_tick),
         (T_B2[1], _it_b2), (T_G1[1], _it_g1), (T_B3B[1], _it_b3), (T_TAIL[1] + 0.001, _it_tail), (T_G2[1], _it_g2),
         (T_BOCK[1], _it_bock), (T_BLOT[1], _it_blot)]
ITEMS.sort(key=lambda it: it[0])


@lru_cache(None)
def _base2(n):
    if n == 0:
        return P.sheet(SIZE, page=2, porthole=10)
    img = _base2(n - 1).copy()
    ITEMS[n - 1][1](img, 1e9)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS gives M.'s whole column."""
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
        return ls / 1.26 * 1.02 * k * lerp(1.0, 0.76, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=(86, 62, 44), shadow=0)


WIDE = (58.0, math.log(0.60), 760.0, 900.0, 480.0, 232.0)
PUSH = (56.0, math.log(0.70), 760.0, 960.0, 480.0, 238.0)
PICK = (50.0, math.log(1.42), 500.0, 640.0, 450.0, 250.0)
PICK2 = (50.0, math.log(1.52), 520.0, 650.0, 450.0, 250.0)
C8 = (38.0, math.log(1.66), 440.0, 1010.0, 460.0, 250.0)
C10 = (38.0, math.log(1.66), 520.0, 1010.0, 460.0, 250.0)
C11 = (38.0, math.log(1.66), 470.0, 1085.0, 460.0, 250.0)
CAM_KEYS = [(0.0, WIDE), (1.3, WIDE), (2.3, PUSH), (2.75, PUSH), (3.45, PICK), (6.0, PICK2), (11.7, PICK2), (12.7, C8),
            (17.9, C8), (19.1, C10), (19.7, C10), (20.3, C11), (22.9, C11), (23.9, WIDE)]
SHAKE_KEYS = [(0.0, 2.5), (14.8, 2.5), (15.0, 0.0), (17.0, 0.0), (17.25, 2.5)]


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


def _desktop(page, angle=0.0, squeeze=1.0, lift=0.0, dx=0.0):
    """The desk plane with the sheet on it. squeeze < 1: the sheet seen partly edge-on while it is turned over."""
    if angle == 0 and squeeze == 1.0 and lift == 0 and dx == 0:
        im = _desk_with_shadow().copy()
        im.paste(page, SO)
        return im
    im = _desk_plane().copy()
    if squeeze != 1.0:
        w = max(10, int(SIZE[0] * squeeze))
        page = page.resize((w, SIZE[1]), Image.BILINEAR)
    P.lay(im, page, SC[0] + dx, SC[1], angle, 1.0, lift=lift)
    return im


def _noise(t, k):
    return math.sin(t * 1.3 + k) * 0.6 + math.sin(t * 2.9 + 2 * k) * 0.4


def _head(fr, t, closeness, tone=TEAL, hair="braids", x=250.0, turn=0.0, tilt=0.0):
    if closeness > 0.97:
        return
    y = 585 + 330 * closeness
    P.head_back(fr, x, y, tone, 1.15, tilt=tilt, hair=hair, turn=turn, t=t)


def _closeness(v):
    return clamp((v.z * S - 0.62) / 0.7)


# ----------------------------------------------- where the pencil point is ---
def _pt(name):
    plan = _plans()[name][0]
    return plan.start


def _btn(name):
    return _mid(B(2, name))


def _oval_tip(u):
    cx, cy = _mid(B(2, "draw1.circle"))
    return Wd.friend_tip("circle", cx, cy + 2, u, OVAL_SC)


def pen(t):
    """(sheet point, pose, lift) of M.'s pencil hand from the pick onwards."""
    pl = _plans()
    if t < T_M[0]:
        return pl["m"][0].start, "hover", 16
    if t < T_M[1]:
        x, y, down = pl["m"][0].tip(ramp(t, *T_M))
        return (x, y), "write", 0 if down else 6
    if t < T_OVAL[0]:
        tri, cir = _btn("btn1a"), _btn("btn1b")
        ov = _oval_tip(0.0)[:2]
        p = key(t, [(3.5, pl["m"][0].end), (3.8, tri), (3.95, tri), (4.15, cir), (4.25, cir), (4.42, tri), (4.5, tri),
                    (4.66, cir), (4.76, cir), (4.9, ov)])
        return p, "hover", key(t, [(3.5, 6), (3.7, 16), (4.76, 16), (4.9, 6)])
    if t < T_OVAL[1]:
        x, y, down = _oval_tip(ramp(t, *T_OVAL))
        return (x, y), "write", 0 if down else 6
    if t < T_B1A[0]:
        ov = _oval_tip(1.0)[:2]
        p = key(t, [(11.7, ov), (12.6, pl["b1a"][0].start)])
        return p, "hover", key(t, [(6.0, 4), (6.3, 16), (12.4, 16), (12.6, 6)])
    if t < T_B1A[1]:
        x, y, down = pl["b1a"][0].tip(ramp(t, *T_B1A))
        return (x, y), "write", 0 if down else 6
    if t < T_B1B[0]:
        return key(t, [(T_B1A[1], pl["b1a"][0].end), (T_B1B[0], pl["b1b"][0].start)]), "write", 7
    if t < T_B1B[1]:
        x, y, down = pl["b1b"][0].tip(ramp(t, *T_B1B))
        return (x, y), "write", 0 if down else 6
    if t < T_B2[0]:                       # stuck: the point drifts down to the printed "it" and rests there
        s2 = pl["b2"][0].start
        tk = _tick_at()
        tk0 = (tk[0] - 3, tk[1] + 9)
        tk1 = (tk[0] + 5, tk[1] - 20)
        p = key(t, [(15.0, pl["b1b"][0].end), (15.35, s2), (15.6, s2), (16.0, tk0), (16.12, tk1), (16.3, tk1),
                    (16.5, tk1), (16.9, s2)])
        if T_TICK[0] <= t < T_TICK[1]:
            return p, "write", 0
        return p, "hover", key(t, [(15.0, 8), (15.3, 16), (15.85, 16), (16.0, 2), (16.3, 2), (16.5, 14), (16.85, 14), (17.0, 6)])
    if t < T_B2[1]:
        x, y, down = pl["b2"][0].tip(ramp(t, *T_B2))
        return (x, y), "write", 0 if down else 6
    if t < T_G1[1]:
        _, p = _along(_g_loop("b2", TXT_B2), ramp(t, *T_G1))
        return p, "write", 0
    if t < T_B3A[0]:                      # she reads her own line before turning it round
        g = _g_loop("b2", TXT_B2)[-1]
        b = pl["b2"][0]
        y = B(2, "bolt2.1")[3] + 12
        p = key(t, [(19.6, g), (19.78, b.start), (19.84, (b.start[0], y)), (20.12, (b.x_end, y)), (20.25, pl["b3a"][0].start)])
        return p, "write", 7
    if t < T_B3A[1]:
        x, y, down = pl["b3a"][0].tip(_b3_u(t))
        return (x, y), "write", 0 if down else 6
    if t < T_TAIL[1]:
        _, p = _along(_tail_pts(), ramp(t, *T_TAIL))
        return p, "write", 0
    if t < T_B3B[1]:
        u = _b3_u(t)
        x, y, down = pl["b3a"][0].tip(u)
        if t < T_B3B[0] + 0.1:           # coming back from the end of the tail
            f = ramp(t, T_B3B[0], T_B3B[0] + 0.1)
            a = _tail_pts()[-1]
            return (lerp(a[0], x, f), lerp(a[1], y, f)), "write", 7
        return (x, y), "write", 0 if down else 6
    if t < T_G2[1]:
        _, p = _along(_g_loop("b3a", TXT_B3A), ramp(t, *T_G2))
        return p, "write", 0
    if t < T_BOCK[0]:
        return key(t, [(T_G2[1], _g_loop("b3a", TXT_B3A)[-1]), (T_BOCK[0], pl["b3b"][0].start)]), "write", 7
    if t < T_BOCK[1]:
        x, y, down = pl["b3b"][0].tip(ramp(t, *T_BOCK))
        return (x, y), "write", 0 if down else 6
    if t < T_BLOT[1]:
        _, p = _along(_blot_pts(), ramp(t, *T_BLOT))
        return p, "write", 0
    e = _blot_pts()[-1]
    return e, "hover", key(t, [(22.8, 2), (23.1, 16)])


# ------------------------------------------------------------ desk frames ---
def _pass_hands(fr, v, t, tone, lift=0.0, dx=0.0, a=1.0):
    """Both hands on the sheet's left and right edges, thumbs on top."""
    yl, yr = 1150, 1250
    pl = v.dpt(SO[0] + dx + 6, SO[1] + yl)
    pr = v.dpt(SO[0] + dx + SIZE[0] - 6, SO[1] + yr)
    k = v.hs((0, yl), 1.0)
    P.hand(fr, pl[0] - lift * 0.2, pl[1] - lift * 0.6, pose="pass", tone=tone, scale=k, flip=True, t=t, arm=150, edge=90, alpha=a)
    P.hand(fr, pr[0] - lift * 0.2, pr[1] - lift * 0.6, pose="pass", tone=tone, scale=k, t=t, arm=35, edge=90, alpha=a)


@lru_cache(None)
def pilot_desk():
    """Where the pass comes from: the rust desk, page 1 finished, both hands starting the sheet left (the end of P11)."""
    v = View(WIDE[0], math.exp(WIDE[1]), WIDE[2:4], WIDE[4:6])
    fr = v.render(_desktop(page1_done(), lift=14, dx=-40))
    P.pencil(fr, *v.dpt(520, 110), angle=4, scale=v.hs((0, -200), 1.0))
    _pass_hands(fr, v, 0.0, RUST, lift=14, dx=-40)
    _head(fr, 0.0, 0.0, RUST, "short", x=300)
    return fr


def desk_frame(t):
    """M.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    cl = _closeness(v)
    if t < 1.3:                                   # the sheet arrived sideways; two hands square it
        u = ease(t, 0.55, 1.3)
        ang = 90 * (1 - u) - 4 * math.sin(math.pi * ramp(t, 1.0, 1.3)) * 0
        slide = 150 * (1 - ease(t, 0.0, 0.6))     # still sliding in from the right as we arrive
        dsk = _desktop(page1_done(), angle=ang, dx=slide)
        fr = v.render(dsk)
        M = P.Tm(SC[0] + slide, SC[1]) @ P.Rm(ang) @ P.Tm(-SIZE[0] / 2, -SIZE[1] / 2)
        w = math.radians(ang)                     # the two flat hands push it round: one goes up, one comes down
        a = (SO[0] + 330 + slide * 0.6 + 120 * math.sin(w), SO[1] + 760 + 330 * math.sin(w))
        b = (SO[0] + 1220 + slide * 0.6 - 60 * math.sin(w), SO[1] + 1500 - 420 * math.sin(w))
        k = v.hs((760, 900), 1.0)
        P.hand(fr, *v.dpt(*a), pose="hold", tone=TEAL, scale=k, flip=True, t=t, arm=150, angle=0)
        P.hand(fr, *v.dpt(*b), pose="hold", tone=TEAL, scale=k, t=t, arm=40)
        _head(fr, t, cl, tilt=14 * (1 - u), turn=0.25 * (1 - u))
        return fr
    if t < 2.4:                                   # a finger on the firm jaw, the pale one, "freak out"
        fr = v.render(_desktop(page1_done()))
        k = v.hs((760, 900), 1.0)
        P.hand(fr, *v.pt((330, 760)), pose="hold", tone=TEAL, scale=k, flip=True, t=t, arm=150)
        jaw, pale, fo = (770, 770), (1310, 790), (330, 1490)
        p = key(t, [(1.3, (1220, 1500)), (1.55, jaw), (1.75, jaw), (1.95, pale), (2.1, pale), (2.3, fo), (2.4, fo)])
        lf = key(t, [(1.3, 10), (1.55, 0), (1.75, 0), (1.85, 9), (1.95, 0), (2.1, 0), (2.2, 9), (2.3, 0)])
        P.hand(fr, *v.pt(p), pose="point", tone=TEAL, scale=k, t=t, arm=55, lift=lf)
        _head(fr, t, cl)
        return fr
    if t < 3.0:                                   # turned over: page 1 closes to an edge, page 2 opens
        u = ramp(t, 2.4, 3.0)
        c = math.cos(math.pi * cam.smooth(u))
        lift = 30 * math.sin(math.pi * u)
        pg = page1_done() if c > 0 else page2(t)
        fr = v.render(_desktop(pg, squeeze=max(abs(c), 0.012), lift=lift))
        k = v.hs((760, 900), 1.0)
        hw = SIZE[0] / 2 * max(abs(c), 0.012)
        for sgn, flip, arm in ((-1, True, 150), (1, False, 35)):
            e = v.dpt(SC[0] + sgn * (hw - 6) - lift * 0.2, SO[1] + 1200 - lift * 0.6)
            P.hand(fr, e[0], e[1], pose="pass", tone=TEAL, scale=k, flip=flip, t=t, arm=arm, edge=90)
        _head(fr, t, cl)
        return fr
    if t < 23.2:                                  # the pencil
        fr = v.render(_desktop(page2(t)))
        p, pose, lift = pen(t)
        if cl < 0.9 or t > 22.0 or t < 4.0:       # the other hand steadies the page when we can see that far
            hp = (150, 1620) if t > 12 else (120, 1500)
            P.hand(fr, *v.pt(hp), pose="hold", tone=TEAL, scale=v.hs(hp), flip=True, t=0.0 if 15 <= t < 17 else t, arm=140)
        a = clamp((23.2 - t) / 0.25)
        th = 15.0 if 15.0 <= t < 17.0 else t          # stuck: not even the grip works
        P.hand(fr, *v.pt(p), pose=pose, tone=TEAL, scale=v.hs(p), t=th, lift=lift,
               arm=key(t, [(3.45, 60), (3.7, 80), (4.7, 80), (4.95, 60)]), alpha=a)
        if a < 1:
            _pass_hands(fr, v, t, TEAL, a=1 - a)
        _head(fr, t, cl)
        return fr
    # letting go
    lift = 14 * ease(t, 24.3, 25.0)
    dx = -70 * ease(t, 24.6, 25.5)
    fr = v.render(_desktop(page2(t), lift=lift, dx=dx))
    P.pencil(fr, *v.dpt(520, 110), angle=4, scale=v.hs((0, -200), 1.0))
    _pass_hands(fr, v, t, TEAL, lift=lift, dx=dx)
    _head(fr, t, cl)
    return fr


def oval_xy(t):
    return view(t).pt(_mid(B(2, "draw1.circle")))


# ------------------------------------------------- Turkey's seat (c10 world) ---
PORT, R = Wd.PORT, Wd.PORT_R
PIN = (404, 318)                    # the jaw's back corner, and the shell's one pin
JK = 1.22                           # pencil-jaw scale (screen px per photograph px)
T6 = 8.3


@lru_cache(None)
def _wall_plain(flip):
    """The inside of the tin with no window in it: pressed ribs, riveted seams, the lamp's pool. The wall behind
    Turkey (and, mirrored and dimmer, the wall beside him). Built from the c10 cabin's own wall, left of its ring."""
    src = Image.new("RGB", (W, H), (20, 22, 26))
    Wd.cabin(src, 0.0)
    strip = src.crop((0, 0, 250, H))
    im = Image.new("RGB", (W, H))
    x, k = 0, 0
    while x < W:
        im.paste(strip if k % 2 == 0 else strip.transpose(Image.FLIP_LEFT_RIGHT), (x, 0))
        x += 250
        k += 1
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = Image.blend(im, Image.new("RGB", (W, H), (12, 12, 16)), 0.3)
    else:
        Wd.glow(im, 470, 40, 300, (255, 214, 150), 0.45)
        im = Image.blend(im, Image.new("RGB", (W, H), (12, 12, 16)), 0.12)
    return im


def tin_back():
    return _wall_plain(False)


def tin_side():
    return _wall_plain(True)


def _jaw_lines(u_draw, gape):
    """The pilot's firm jaw as screen polylines, hinged on its back corner: box top, side and teeth swing up, the
    three bottom lines swing down."""
    px, py = -107.0, 36.0
    out = []
    strokes = [s for s in Wd.PILOT_STROKES if s["part"] == "jaw"]
    n = len(strokes)
    for i, s in enumerate(strokes):
        f = clamp(u_draw * n - i)
        if f <= 0:
            break
        lower = i in (2, 3, 4)
        a = math.radians(gape * (0.55 if lower else -0.45))
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for x, y in cam_dense(s["pts"]):
            dx, dy = (x - px) * JK, (y - py) * JK
            pts.append((PIN[0] + dx * ca - dy * sa, PIN[1] + dx * sa + dy * ca))
        pts, _ = _along(pts, f)
        out.append((pts, s["weight"]))
    return out


def cam_dense(pts):
    return P.catmull([tuple(p) for p in pts], 6) if len(pts) > 2 else [tuple(p) for p in pts]


FLAPS = (1.0, 1.5)                  # seconds after T6: the jaw talks twice
X0, X1 = 1.35, 1.95                 # pencil lines thicken into the shell on the wall
TR_GO, TR_STOP = 2.0, 2.9
TROUT = [((790, 230, 0.22), (668, 150, 0.42), 0, 0.0),
         ((800, 330, 0.22), (676, 330, 0.52), 2, 1.3),
         ((780, 400, 0.20), (600, 396, 0.40), 1, 2.4)]


def _gape(u):
    g = 4.0
    for f in FLAPS:
        g += 30 * C10T._bump(u, f, f + 0.13, f + 0.46)
    g += 26 * C10T._bump(u, 2.95, 3.05, 3.3)
    return g


def _outside(im, T, u):
    """What is beyond the glass at u seconds into the look."""
    Wd.river(im, T, seed=0)
    x = ramp(u, X0, X1)
    g = _gape(u)
    if x > 0:
        solid = im.copy()
        Wd.brick_wall(solid, 236, 0, 250, 540, seed=2)
        xs = cam.smooth(x)                         # as it turns into the real thing it is over there, on the wall
        c = Wd.clam_pa(solid, lerp(PIN[0], 432, xs), lerp(PIN[1] - 30, 236, xs), lerp(1.2, 0.8, xs), g, T, split=0.5)
        im.paste(Image.blend(im, solid, cam.smooth(x)))
        mouth = c["mouth"]
    else:
        mouth = (PIN[0] + 300, PIN[1] - 90)
    if x < 1:
        k = 1 - cam.smooth(x)
        for pts, w in _jaw_lines(ramp(u, 0.0, 0.75), g * 1.1):
            P.graphite(im, [pts], 4.2 + 3.5 * w, (0.55 + 0.75 * w) * k, 7, color=(236, 238, 226))
    for f in FLAPS + (2.95,):
        if f < u < f + 0.9:
            Wd.sound_rings(im, mouth[0] - 10, mouth[1], u - f, direction=-8, n=3, r0=18, r1=190, arc=70,
                           strength=clamp(1.5 - 1.7 * (u - f)), rate=1.1, width=3.5)
    v = ease(u, TR_GO, TR_STOP)
    if u > TR_GO - 0.3:
        for i, (far, near, kind, ph) in enumerate(TROUT):
            xx, yy = lerp(far[0], near[0], v), lerp(far[1], near[1], v) + 14 * math.sin(math.pi * v) * (1 if i != 1 else -1)
            Wd.trout(im, xx, yy, lerp(far[2], near[2], v), T, kind=kind, pose="swim" if u < TR_STOP else "look", phase=ph,
                     gaze=(-2.0, 0.3), alpha=clamp((u - TR_GO + 0.3) / 0.3))
    Wd.river_plane(im, "front", T)


@lru_cache(None)
def _glass_mask():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([PORT[0] - R, PORT[1] - R, PORT[0] + R, PORT[1] + R], fill=255)
    return m


def view_out(t):
    """Turkey's seat: the brass porthole from where he sits, and what is outside it now."""
    u = t - T6
    im = Image.new("RGB", (W, H), (0, 0, 0))
    _outside(im, t, max(u, 0.0))
    Wd.cabin(im, t)
    Wd.air_gauge(im, 196, 418, 0.5, r=30, t=t)
    # his own reflection, low in the glass: beak going (the pilot wrote "freak out", and she has just read it)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Wd.turkey(lay, 452, 470, 0.86, "freak", t * 1.3, flip=True, shade=0.25, feathers=False, drop=False)
    a = lay.getchannel("A").point(lambda q: int(q * 0.38))
    lay.putalpha(Image.composite(a, Image.new("L", (W, H), 0), _glass_mask()))
    im.paste(lay, (0, 0), lay)
    return im


def seat_frame(t):
    u = t - T6
    return cam.shoot([(view_out(t), 1.0)], x=key(t, [(T6, 0), (11.5, 26)]), y=key(t, [(T6, 0), (11.5, -8)]),
                     zoom=key(t, [(T6, 1.0), (11.5, 1.08)]), shake=1.5 * ramp(u, 0, 0.4), t=t, bg=(20, 22, 26))


# -------------------------------------------------- the thought (bolt 2) ---
TH = (17.3, 19.0)
TH_AT = (806, 138, 100)


def _thought_inner(t):
    u = lerp(0.9, 2.9, ramp(t, TH[0] + 0.2, TH[1] - 0.1))
    im = Image.new("RGB", (W, H), (0, 0, 0))
    C10T._b2_out(im, t, u)
    r = 190
    return im.crop((PORT[0] - int(r * 16 / 9), PORT[1] - r, PORT[0] + int(r * 16 / 9), PORT[1] + r)).resize((W, H), Image.BILINEAR)


# ------------------------------------------------------------------ draw ---
def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 0.5:
        return cam.whip(pilot_desk(), desk_frame(t), ramp(t, 0.0, 0.5), direction=-1)
    if t < 1.5:
        return cam.shoot([(desk_frame(t), 1.0)], rot=9 * (1 - ease(t, 0.5, 1.4)), zoom=1.0 + 0.05 * (1 - ease(t, 0.5, 1.4)),
                         bg=(86, 62, 44))
    if t < 6.0:
        return desk_frame(t)
    if t < 7.1:
        ox, oy = oval_xy(t)
        return cam.dive(desk_frame(t), tin_back(), ox, oy, ramp(t, 6.0, 7.1), spin=30)
    if t < T6:
        return cam.turn(tin_back(), seat_frame(T6), ramp(t, 7.1, T6), axis="y", direction=1, side=tin_side())
    if t < 11.5:
        return seat_frame(t)
    if t < 12.5:
        ox, oy = oval_xy(t)
        return cam.dive(desk_frame(t), seat_frame(t), ox, oy, 1 - ramp(t, 11.5, 12.5))
    fr = desk_frame(t)
    if TH[0] < t < TH[1] + 0.3:
        u = key(t, [(TH[0], 0.0), (TH[0] + 0.45, 1.0), (TH[1] - 0.1, 1.0), (TH[1] + 0.3, 0.0)])
        if u > 0.01:
            fr = cam.thought(fr, _thought_inner(t), TH_AT[0], TH_AT[1], TH_AT[2], u, wobble=6, t=t, dim=0.0)
    return fr


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    from kit import Ink
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() else FILMS / "stills" / "m10_scene_turkey"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.2, 0.8, 1.7, 2.7, 3.4, 4.3, 5.6, 6.5, 7.6, 8.9, 9.8, 11.2, 12.0, 13.6, 14.9, 16.1, 18.4, 19.9, 21.0, 22.7, 24.9]
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
