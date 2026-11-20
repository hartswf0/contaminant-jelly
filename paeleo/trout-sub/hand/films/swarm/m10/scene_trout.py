"""m10 · scene_trout · the next friend, S., fills in the right column of page 2 (board beats R1 to R12, film 57.5 to 81.5).

The sheet arrives upside down and is turned round in two pushes; "S."; the pencil hangs over the cross button, drops
to the square one and colours it in, round and round, until it is a dark disc (trace 27); a very small square in the
dashed circle (28). Then the journey: in through the dashed circle to Turkey's seat (where the last child left us),
OUT THROUGH THE GLASS into the river, a swing round, and a look back at the small tin with a small Turkey in it,
past three trout. Back up to the desk. Bolt 4 with its false start: "the", rubbed out, a glance across at how the
last child began, and begun again one word to the right (29, 30), "run." with its stop (31). Bolt 5: "thro"
climbing off the rule (32), "partty" and its "y" gone over (33). Bolt 6: bigger letters (35), "in / side" broken
where the line broke (34), the exclamation mark made last and hardest (36). Letting go.

Seats are full pictures: `desk_frame(t)` (desk plane laid back by cam.tilt, hands and head from people.py),
`view_out(t)` (Turkey's seat, c10 world), `open_water(t)`, `river_back_look(t)`. Moves between them are cam.whip,
cam.dive, cam.through_glass, cam.turn; nothing is cross-faded.

Exposes SECONDS, CAPTIONS, draw(t, ink), frame(t), and page2(t) (the sheet at this module's second t, 1520 x 1960;
t >= SECONDS gives the whole written page 2 for the ending). The geometry (sheet at 2 x 760 x 980 on a 2300 x 2500
desk plane, the wide view) is the same as scene_turkey.py's, and M.'s column is taken from scene_turkey.page2 when
that module can be loaded (else lettered here from the transcript), so the page carries its history.

    python3 films/swarm/m10/scene_trout.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
for _p in (str(FILMS), str(FILMS / "swarm" / "c10")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c10 world; not edited)

W, H = 960, 540
ramp, ease, lerp, clamp = Wd.ramp, Wd.ease, Wd.lerp, Wd.clamp
key = cam.key

SECONDS = 24.0
CAPTIONS = [
    (15.9, 18.5, "The trout to run."),
    (18.6, 21.2, "The trout to throw a dance party."),
    (21.3, 23.9, "The trout to come inside the sub!"),
]

PLUM, TEAL = "plum", "teal"
HAIR = "bun"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C10R = _load("c10_scene_trout", FILMS / "swarm" / "c10" / "scene_trout.py")     # the staged endings, for the thoughts
_ST = None


def _turkey_module():
    """The first friend's module (M.'s column, M.'s desk for the pass), if it can be loaded."""
    global _ST
    if _ST is None:
        try:
            _ST = _load("m10_scene_turkey", HERE / "scene_turkey.py")
        except Exception:
            _ST = False
    return _ST


# ------------------------------------------------------------------ the sheet on the desk plane
S = 2
SIZE = (760 * S, 980 * S)
DESK_SIZE = (2300, 2500)
SC = (1150, 1280)
SO = (SC[0] - SIZE[0] // 2, SC[1] - SIZE[1] // 2)
BG = (86, 62, 44)


def B(name):
    return P.where(2, name, SIZE)


def _mid(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def _m_column_here(pg):
    """M.'s column lettered from the transcript (only used when scene_turkey.py cannot be loaded)."""
    xh = 0.46 * (B("bolt1.1")[3] - B("bolt1.1")[1])
    P.write_on(pg, B("name1.line"), "M.", 1.0, seed=200, size=xh * 1.2)
    cx, cy = _mid(B("draw1.circle"))
    Wd.friend_mark(pg, "circle", cx, cy + 2, 1.0, 1.3)
    P.write_on(pg, B("bolt1.1"), "the trout to be", 1.0, seed=201, size=xh)
    P.write_on(pg, B("bolt1.2"), "outsid", 1.0, seed=202, weight=0.7, size=xh * 0.9)
    b = B("bolt2.1")
    P.write_on(pg, (b[0], b[1], B("bolt5.1")[0] - 4, b[3]), "he  dos not  get beck", 1.0, seed=203, size=xh * 1.15)
    P.write_on(pg, B("bolt3.1"), "the turkey gets", 1.0, seed=204, size=xh)
    b = B("bolt3.2")
    P.write_on(pg, (b[0] + 60, b[1], b[2], b[3]), "bock", 1.0, seed=205, size=xh)


@lru_cache(None)
def _page_base():
    """Page 2 as it reaches S.: printed, with the first friend's whole column."""
    st = _turkey_module()
    if st:
        try:
            pg = st.page2(1e6)
            if pg.size == SIZE:
                return pg.convert("RGB")
        except Exception:
            pass
    pg = P.sheet(SIZE, page=2, porthole=10)
    _m_column_here(pg)
    return pg


# ------------------------------------------------------------------ what S. puts on the page, and when
SLANT = 0.24            # S.'s letters lean (trace 38)


class Act:
    """One pull of work on the page: draw(img, u) lays it as far as u; tip(u) -> (x, y, down) in sheet px."""
    pose = "write"

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1

    def u(self, t):
        return ramp(t, self.t0, self.t1)


class Write(Act):
    def __init__(self, t0, t1, box, text, seed, weight=1.0, size=None):
        super().__init__(t0, t1)
        self.seed, self.weight = seed, weight
        self.plan = P.WritePlan(box, text, seed, size, SLANT)

    def draw(self, img, u):
        done = self.plan.upto(u)[0]
        P.graphite(img, done, max(1.2, self.plan.xh * 0.15) * (0.82 + 0.22 * self.weight), self.weight, self.seed)

    def tip(self, u):
        return self.plan.tip(u)


class Lines(Act):
    """Pencil polylines drawn in order (the coloured-in button, a go-over, the exclamation mark)."""
    def __init__(self, t0, t1, lines, weight=1.3, width=3.0, seed=0):
        super().__init__(t0, t1)
        self.lines, self.weight, self.width, self.seed = lines, weight, width, seed
        self.len = [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(ln, ln[1:])) + 4 for ln in lines]
        self.T = sum(self.len)

    def _upto(self, u):
        tt, done = u * self.T, []
        for ln, L in zip(self.lines, self.len):
            if tt >= L:
                done.append(ln)
                tt -= L
                continue
            n = max(1, int(round(tt / L * (len(ln) - 1))))
            done.append(ln[:n + 1])
            return done, ln[n]
        return done, self.lines[-1][-1]

    def draw(self, img, u):
        if u <= 0:
            return
        done, _ = self._upto(min(u, 1.0))
        P.graphite(img, done, self.width, self.weight, self.seed)

    def tip(self, u):
        if u <= 0:
            return self.lines[0][0] + (False,)
        _, p = self._upto(min(u, 1.0))
        return (p[0], p[1], u < 1)


class Mark(Act):
    """The very small lopsided square (traced strokes from the c10 world)."""
    def __init__(self, t0, t1, cx, cy, sc):
        super().__init__(t0, t1)
        self.c = (cx, cy, sc)

    def draw(self, img, u):
        if u > 0:
            Wd.friend_mark(img, "square", self.c[0], self.c[1], min(u, 1.0), self.c[2])

    def tip(self, u):
        return Wd.friend_tip("square", self.c[0], self.c[1], clamp(u), self.c[2])


class Rub(Act):
    """The false start rubbed out: the paper comes back scuffed and the word stays as a ghost."""
    pose = "erase"

    def __init__(self, t0, t1, box, seed=0):
        super().__init__(t0, t1)
        self.box, self.seed = box, seed

    def draw(self, img, u):
        P.rub_mark(img, self.box, min(1.0, u * 1.15), self.seed)

    def tip(self, u):
        x0, y0, x1, y1 = self.box
        f = 0.5 + 0.34 * math.sin(u * 2.4 * math.pi)                 # the rubber works along the word and back
        x, y = lerp(x0 + 8, x1 - 8, f), (y0 + y1) / 2 + 3
        if u > 0.84:                                                 # the last stroke brushes the crumbs away, up and right
            k = cam.smooth((u - 0.84) / 0.16)
            x, y = lerp(x, x1 + 70, k), lerp(y, y - 30, k)
        return (x, y, True)


def _letter_lines(plan, idx):
    return [s for s, l in zip(plan.strokes, plan.letter) if l == idx]


BTN = B("btn2b")
BTN_C = _mid(BTN)
BTN_R = (BTN[2] - BTN[0]) / 2
CROSS_C = _mid(B("btn2a"))
DC = _mid(B("draw2.circle"))
LH = B("bolt4.1")[3] - B("bolt4.1")[1]            # one ruled line
XH4, XH5, XH6 = 0.50 * LH, 0.56 * LH, 0.68 * LH    # the letters grow (trace 35)


def _scribble():
    """Round and round the square button, pressing, out past its edge."""
    rs = random.Random(27)
    cx, cy = BTN_C
    out = []
    for r0, r1, turns, ox, oy in ((2.0, BTN_R + 6.5, 6.5, 0.0, 0.0), (BTN_R + 5.0, 3.0, 5.0, 1.8, -1.2), (4.0, BTN_R + 3.0, 3.0, -1.5, 1.0)):
        n = int(turns * 26)
        ln = []
        ph = rs.uniform(0, 6.28)
        for k in range(n + 1):
            f = k / n
            a = ph + f * turns * 2 * math.pi
            r = lerp(r0, r1, f) * (1 + 0.10 * math.sin(a * 2.3 + ph)) + rs.uniform(-0.8, 0.8)
            ln.append((cx + ox + r * 1.04 * math.cos(a), cy + oy + r * 0.96 * math.sin(a)))
        out.append(ln)
    return out


def _build():
    acts = []
    n2 = B("name2.line")
    acts.append(Write(1.85, 2.3, (n2[0] + 14, n2[1], n2[2], n2[3]), "S.", 300, 1.05, XH4 * 1.35))
    acts.append(Lines(2.9, 5.1, _scribble(), weight=1.4, width=5.6, seed=27))                      # trace 27
    acts.append(Mark(5.35, 6.0, DC[0] + 13, DC[1] - 12, 1.2))                                      # trace 28

    b41, b42 = B("bolt4.1"), B("bolt4.2")
    false = Write(12.85, 13.2, (b41[0] + 6, b41[1], b41[2], b41[3]), "the", 310, 1.0, XH4)        # the false start
    acts.append(false)
    rub_box = (b41[0] + 2, b41[1] - 6, false.plan.x_end + 10, b41[3] + 9)
    acts.append(Rub(13.3, 14.0, rub_box, 3))                                                       # trace 29
    acts.append(Write(14.55, 15.5, (false.plan.x_end + 20, b41[1], b41[2], b41[3]), "the trout to", 311, 1.0, XH4))
    acts.append(Write(15.55, 15.9, (b42[0] + 4, b42[1], b42[2], b42[3]), "run.", 312, 1.0, XH4))   # trace 31

    b51, b52 = B("bolt5.1"), B("bolt5.2")
    a = Write(16.1, 17.0, (b51[0] + 8, b51[1], b51[2], b51[3]), "the trout to", 320, 1.0, XH5)
    x = a.plan.x_end + 0.62 * XH5
    th = Write(17.02, 17.2, (x, b51[1] - 0.26 * LH, b51[2] + 60, b51[3] - 0.26 * LH), "th", 321, 1.0, XH5)      # trace 32:
    ro = Write(17.2, 17.4, (th.plan.x_end - 2, b51[1] - 0.50 * LH, b51[2] + 90, b51[3] - 0.50 * LH), "ro", 322, 0.95, XH5)   # climbs
    acts += [a, th, ro]
    party = Write(17.45, 18.3, (b52[0] + 10, b52[1], b52[2], b52[3]), "a dance partty", 323, 1.0, XH5)
    acts.append(party)
    yl = _letter_lines(party.plan, len("a dance partty") - 1)
    rs = random.Random(33)
    over = [[(px + 1.6 + rs.uniform(-0.5, 0.5), py + 1.0 + rs.uniform(-0.5, 0.5)) for px, py in ln] for ln in yl[-1:]]
    acts.append(Lines(18.34, 18.6, over, weight=1.5, width=max(3.4, XH5 * 0.2), seed=34))         # trace 33

    b61, b62 = B("bolt6.1"), B("bolt6.2")
    acts.append(Write(18.85, 20.2, (b61[0] + 26, b61[1], b61[2] + 80, b61[3]), "the trout to come in", 330, 1.08, XH6))   # 34, 35
    side = Write(20.25, 20.86, (b62[0] + 16, b62[1], b62[2], b62[3]), "side the sub", 331, 1.08, XH6)
    acts.append(side)
    ex, base = side.plan.x_end + 0.22 * XH6, b62[3] - 0.07 * LH
    acts.append(Lines(20.9, 20.99, [[(ex + 5, base - 1.95 * XH6), (ex + 3.5, base - 1.2 * XH6), (ex + 2.2, base - 0.5 * XH6)]],
                      weight=1.5, width=XH6 * 0.2, seed=35))                                       # trace 36: one down-stroke,
    dot = [(ex + 1.2 + 1.6 * math.cos(q), base - 0.05 * XH6 + 1.6 * math.sin(q)) for q in np.linspace(0, 12.6, 16)]
    acts.append(Lines(21.04, 21.1, [dot], weight=1.6, width=XH6 * 0.24, seed=36))                  # then the dot, stabbed
    acts.sort(key=lambda q: q.t0)
    return acts, rub_box


ACTS, RUB_BOX = _build()
CRUMB_AT = ((RUB_BOX[0] + RUB_BOX[2]) / 2 + 6, RUB_BOX[3] + 4)
CRUMB_TO = (CRUMB_AT[0] + 250, CRUMB_AT[1] - 104)      # brushed up and right, into the white under "Draw the one you pick"
_page_cache = {}


def _crumbs(img, t):
    if t < 13.4:
        return
    n = int(round(lerp(1, 10, ramp(t, 13.4, 13.86))))
    f = ease(t, 13.87, 14.0)
    x, y = lerp(CRUMB_AT[0], CRUMB_TO[0], f), lerp(CRUMB_AT[1], CRUMB_TO[1], f)
    P.eraser_crumbs(img, x, y, n=n if f < 1 else 7, seed=5, spread=lerp(26, 40, f), scale=1.5)


def page2(t):
    """Page 2 as it stands at this module's second t: a fresh PIL image, 1520 x 1960 (use P.where(2, name, SIZE))."""
    done = sum(1 for a in ACTS if t >= a.t1)
    if done not in _page_cache:
        if len(_page_cache) > 6:
            _page_cache.clear()
        img = _page_base().copy()
        for a in ACTS:
            if a.t1 <= t:
                a.draw(img, 1.0)
        _page_cache[done] = img
    img = _page_cache[done].copy()
    for a in ACTS:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    _crumbs(img, t)
    return img


# ------------------------------------------------------------------ where the pencil point is (sheet px)
B41, B62 = B("bolt4.1"), B("bolt6.2")
WAIT = (DC[0] + 30, DC[1] + 96)                        # where the pencil hangs while she is away in the river
RESTART = (RUB_BOX[2] + 40, B41[3] - 4)                # over the line, after the rubbing out: not moving
AIR = [                                                # (t, (x, y), lift)
    (2.5, (CROSS_C[0] + 2, CROSS_C[1] + 2), 16),       # hangs over the cross button
    (2.64, (CROSS_C[0] + 3, CROSS_C[1] + 2), 16),
    (2.86, (BTN_C[0], BTN_C[1] - 4), 9),               # drops to the square one
    (5.22, (BTN_C[0] + 170, BTN_C[1] + 30), 15),
    (6.25, WAIT, 18),
    (12.6, WAIT, 18),
    (13.24, (RUB_BOX[2] - 30, B41[3] - 10), 9),        # stops
    (14.06, RESTART, 16),
    (14.5, RESTART, 16),
    (21.3, (B62[0] + 560, B62[3] + 26), 18),
]


def _pen(t):
    """((x, y), pose, lift, writing?) of the pencil point (or the rubber) on the sheet at t."""
    for a in ACTS:
        if a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return (x, y), a.pose, (0 if down else 6), True
    keys = [(a.t0, a.tip(0.0)[:2] + (7,)) for a in ACTS] + [(a.t1, a.tip(1.0)[:2] + (7,)) for a in ACTS]
    keys += [(tt, p + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    x, y, l = key(t, keys, "smooth")
    return (x, y), ("hover" if l >= 13 else "write"), l, False


# ------------------------------------------------------------------ the desk camera (as scene_turkey's)
F = 700.0
HOR = 0.36


class View:
    """The seat's eye on the desk plane: tilt, zoom (screen px per 760-page px at the aim), an aim point (sheet px)
    held at a screen point. Handheld drift is a shift of the whole view."""

    def __init__(self, deg, zoom, at, to, shake=0.0, t=0.0):
        self.deg, self.z = deg, zoom / S
        d = (SO[0] + at[0], SO[1] + at[1])
        p0 = cam.tilt_point(d[0], d[1], deg, HOR, self.z, F, (0, 0), DESK_SIZE)
        sx = shake * (math.sin(t * 2.1) + 0.5 * math.sin(t * 5.3 + 1.0)) * 0.8
        sy = shake * (math.cos(t * 1.7) + 0.5 * math.sin(t * 4.1 + 2.0)) * 0.6
        self.shift = (to[0] - p0[0] + sx, to[1] - p0[1] + sy)

    def dpt(self, x, y):                 # desk plane px -> screen
        return cam.tilt_point(x, y, self.deg, HOR, self.z, F, self.shift, DESK_SIZE)

    def pt(self, p):                     # sheet px -> screen
        return self.dpt(SO[0] + p[0], SO[1] + p[1])

    def ls(self, p):                     # screen px per 760-page px at that sheet point
        a = self.pt(p)
        b = self.pt((p[0] + 20, p[1]))
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 20 * S

    def hs(self, p, k=1.0):              # the hand's scale there (a little smaller as we lean in, so the words show)
        ls = self.ls(p)
        return ls / 1.26 * 1.02 * k * (lerp(1.0, 0.76, clamp((ls - 0.7) / 0.9)) - 0.13 * clamp((ls - 1.6) / 1.6))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, HOR, self.z, F, self.shift, bg=BG, shadow=0)


COLX = B("bolt4.1")[0]                                   # the right column's left edge
MCOL = B("bolt1.1")[0]                                   # the left column's
WIDE = (58.0, math.log(0.60), 760.0, 900.0, 480.0, 232.0)


def _shot(deg, scale, ax, ay, tx, ty):
    """A view whose scale AT THE AIM POINT is `scale` screen px per 760-page px (the plane is in perspective, so the
    lens zoom that gives it depends on where on the desk the aim is)."""
    z = scale
    for _ in range(4):
        z *= scale / View(deg, z, (ax, ay), (tx, ty)).ls((ax, ay))
    return (deg, math.log(z), ax, ay, tx, ty)


NAME = _shot(48.0, 1.9, COLX + 250.0, B("name2.line")[3] + 40, 440.0, 230.0)
BTNS = _shot(42.0, 3.3, BTN_C[0] + 70.0, (BTN_C[1] + CROSS_C[1]) / 2 + 6, 400.0, 236.0)          # the two buttons: a third of the frame
SQ = _shot(42.0, 2.7, DC[0] - 150.0, DC[1] - 12, 580.0, 232.0)
C4 = _shot(38.0, 2.7, COLX + 230.0, B41[3] + 4, 400.0, 286.0)
C4B = _shot(38.0, 2.7, COLX + 248.0, B41[3] + 14, 400.0, 286.0)
C4L = _shot(38.0, 2.7, MCOL + 230.0, B41[3] + 4, 400.0, 286.0)                                    # the glance at M.'s line
C5 = _shot(38.0, 2.7, COLX + 250.0, B("bolt5.1")[3] + 8, 400.0, 286.0)
C5B = _shot(38.0, 2.7, COLX + 262.0, B("bolt5.1")[3] + 20, 400.0, 286.0)
C6 = _shot(38.0, 2.95, COLX + 252.0, B("bolt6.1")[3] + 6, 400.0, 286.0)                           # a little nearer: the letters are bigger
C6B = _shot(38.0, 2.95, COLX + 262.0, B("bolt6.1")[3] + 22, 400.0, 286.0)
CAM_KEYS = [
    (0.0, WIDE), (1.5, WIDE), (2.05, NAME), (2.32, NAME), (2.95, BTNS), (5.12, BTNS), (5.6, SQ), (12.8, SQ),
    (13.25, C4), (14.0, C4), (14.19, C4L, "out"), (14.36, C4L), (14.52, C4, "smooth"), (15.5, C4B), (15.95, C4B),
    (16.4, C5), (17.4, C5B), (18.65, C5B), (19.15, C6), (20.2, C6B), (21.3, C6B), (22.25, WIDE), (24.0, WIDE),
]
SHAKE_KEYS = [(0.0, 0.0), (0.5, 0.0), (1.5, 2.5), (13.95, 2.5), (14.0, 0.0), (14.5, 0.0), (14.62, 2.5), (24.0, 2.5)]
STILL = (14.0, 14.5)                                     # the hand does not move while she looks across


def view(t):
    deg, lz, ax, ay, tx, ty = key(t, CAM_KEYS, "smoother")
    return View(deg, math.exp(lz), (ax, ay), (tx, ty), key(t, SHAKE_KEYS, "linear"), t)


def _closeness(v):
    return clamp((v.z * S - 0.62) / 0.7)


# ------------------------------------------------------------------ the desk top
GROOVE = (520, 110)                                      # where the pencil lies (desk plane px)


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
    if angle == 0 and lift == 0 and dx == 0:
        im = _desk_with_shadow().copy()
        im.paste(page, SO)
        return im
    im = _desk_plane().copy()
    P.lay(im, page, SC[0] + dx, SC[1], angle, 1.0, lift=lift)
    return im


def _head(fr, t, closeness, tone=PLUM, hair=HAIR, x=262.0, turn=0.0, tilt=0.0):
    if closeness > 0.97:
        return
    P.head_back(fr, x, 585 + 330 * closeness, tone, 1.15, tilt=tilt, hair=hair, turn=turn, t=t)


def _pass_hands(fr, v, t, tone, lift=0.0, dx=0.0):
    """Both hands on the sheet's left and right edges, thumbs on top."""
    yl, yr = 1150, 1250
    pl = v.dpt(SO[0] + dx + 6, SO[1] + yl)
    pr = v.dpt(SO[0] + dx + SIZE[0] - 6, SO[1] + yr)
    k = v.hs((0, yl), 1.0)
    P.hand(fr, pl[0] - lift * 0.2, pl[1] - lift * 0.6, pose="pass", tone=tone, scale=k, flip=True, t=t, arm=150, edge=90)
    P.hand(fr, pr[0] - lift * 0.2, pr[1] - lift * 0.6, pose="pass", tone=tone, scale=k, t=t, arm=35, edge=90)


@lru_cache(None)
def m_desk():
    """Where the pass comes from: the teal desk as scene_turkey leaves it (its own last frame when it can be had)."""
    st = _turkey_module()
    if st:
        try:
            fr = st.frame(st.SECONDS - 1e-3)
            if isinstance(fr, Image.Image):
                return cam.fit(fr)
        except Exception:
            pass
    v = View(WIDE[0], math.exp(WIDE[1]), WIDE[2:4], WIDE[4:6])
    fr = v.render(_desktop(_page_base(), lift=14, dx=-70))
    P.pencil(fr, *v.dpt(*GROOVE), angle=4, scale=v.hs((0, -200), 1.0))
    _pass_hands(fr, v, 0.0, TEAL, lift=14, dx=-70)
    _head(fr, 0.0, 0.0, TEAL, "braids", x=250)
    return fr


# the turn: the sheet lands upside down and is pushed round in two goes, one hand each
TURN = [(0.5, 180.0), (0.98, 92.0), (1.06, 88.0), (1.5, 0.0)]
LEFT_REST = (170, 1640)                                   # sheet px: the other hand steadies the page, low on the left


def _sheet_angle(t):
    return key(t, TURN, "smooth")


def _ride(p0, a0, ang, slide):
    """A desk-plane point that was at p0 (from the sheet's centre) when the sheet stood at a0, carried round to ang."""
    w = math.radians(ang - a0)
    return (SC[0] + slide + p0[0] * math.cos(w) - p0[1] * math.sin(w), SC[1] + p0[0] * math.sin(w) + p0[1] * math.cos(w))


def desk_frame(t):
    """S.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t)
    cl = _closeness(v)
    ht = STILL[0] if STILL[0] <= t < STILL[1] else t      # nothing breathes while she is stuck
    if t < 1.5:                                           # the sheet arrives upside down; two pushes turn it round
        ang = _sheet_angle(t)
        slide = 170 * (1 - ease(t, 0.0, 0.55))
        fr = v.render(_desktop(page2(t), angle=ang, dx=slide))
        k = v.hs((760, 900), 1.0)
        rest = (SO[0] + LEFT_REST[0], SO[1] + LEFT_REST[1])
        # left hand: comes down on the sheet, pushes it a quarter round (180 -> 90), lets go
        la = _ride((-330, 300), 180.0, max(ang, 90.0), slide)
        lp = key(t, [(0.0, (la[0] - 260, la[1] + 320)), (0.5, la), (1.02, la), (1.4, rest)]) if not (0.5 <= t <= 1.02) else la
        ll = key(t, [(0.0, 26), (0.45, 0), (1.02, 0), (1.2, 14), (1.45, 0)])
        P.hand(fr, *v.dpt(*lp), pose="hold", tone=PLUM, scale=k, flip=True, t=t, arm=146, lift=ll)
        # right hand: waits, then takes the second quarter (90 -> 0)
        ra = _ride((340, 40), 90.0, min(ang, 90.0), slide)
        rp = key(t, [(0.0, (ra[0] + 330, ra[1] + 420)), (0.95, ra)]) if t < 0.95 else ra
        rl = key(t, [(0.0, 30), (0.8, 22), (1.0, 0)])
        P.hand(fr, *v.dpt(*rp), pose="hold", tone=PLUM, scale=k, t=t, arm=42, lift=rl)
        P.pencil(fr, *v.dpt(*GROOVE), angle=4, scale=v.hs((0, -200), 1.0))
        u = ease(t, 0.5, 1.5)
        _head(fr, t, cl, tilt=-12 * (1 - u), turn=-0.3 * (1 - u))
        return fr
    if t < 21.3:                                          # the pencil
        fr = v.render(_desktop(page2(t)))
        if cl < 0.9:
            P.hand(fr, *v.pt(LEFT_REST), pose="hold", tone=PLUM, scale=v.hs(LEFT_REST), flip=True, t=ht, arm=140)
        if t < 1.85:                                      # takes the pencil out of the groove
            g = (GROOVE[0] - SO[0] + 150, GROOVE[1] - SO[1] + 40)
            start = (760 + 380, 980 + 330)
            p = key(t, [(1.5, start), (1.66, g), (1.85, ACTS[0].tip(0.0)[:2])])
            if t < 1.66:
                P.pencil(fr, *v.dpt(*GROOVE), angle=4, scale=v.hs((0, -200), 1.0))
                P.hand(fr, *v.pt(p), pose="point", tone=PLUM, scale=v.hs(p), t=t, arm=52, lift=12)
            else:
                P.hand(fr, *v.pt(p), pose="write", tone=PLUM, scale=v.hs(p), t=t, arm=60, lift=14)
        else:
            p, pose, lift, _ = _pen(t)
            P.hand(fr, *v.pt(p), pose=pose, tone=PLUM, scale=v.hs(p), t=ht, lift=lift, arm=60)
        turn = -0.45 * (ease(t, 14.0, 14.16) - ease(t, 14.36, 14.5))
        _head(fr, ht, cl, turn=turn)
        return fr
    # letting go: the pencil back in the groove, both hands to the edges, the sheet up and starting back to the pilot
    lift = 14 * ease(t, 23.0, 23.5)
    dx = 80 * ease(t, 23.3, 24.2)
    fr = v.render(_desktop(page2(t), lift=lift, dx=dx))
    if t < 22.1:                                          # carrying the pencil up
        P.hand(fr, *v.pt(LEFT_REST), pose="hold", tone=PLUM, scale=v.hs(LEFT_REST), flip=True, t=t, arm=140)
        g = (GROOVE[0] - SO[0] + 150, GROOVE[1] - SO[1] + 40)
        p = key(t, [(21.3, AIR[-1][1]), (22.1, g)])
        P.hand(fr, *v.pt(p), pose="write", tone=PLUM, scale=v.hs(p), t=t, arm=60, lift=16)
    else:
        P.pencil(fr, *v.dpt(*GROOVE), angle=4, scale=v.hs((0, -200), 1.0))
        if t < 22.8:
            a = ease(t, 22.1, 22.8)
            g = (GROOVE[0] - SO[0] + 150, GROOVE[1] - SO[1] + 40)
            k = v.hs((760, 900), 1.0)
            pr = (lerp(g[0], SIZE[0] - 6, a), lerp(g[1], 1250, a))
            plh = (lerp(LEFT_REST[0], 6, a), lerp(LEFT_REST[1], 1150, a))
            P.hand(fr, *v.pt(plh), pose="hold", tone=PLUM, scale=k, flip=True, t=t, arm=146, lift=12 * math.sin(math.pi * a))
            P.hand(fr, *v.pt(pr), pose="hold", tone=PLUM, scale=k, t=t, arm=40, lift=6 + 12 * math.sin(math.pi * a))
        else:
            _pass_hands(fr, v, t, PLUM, lift=lift, dx=dx)
    _head(fr, t, cl)
    return fr


def circle_xy(t):
    """The dashed circle on screen: the hole she goes in by, and comes back up out of."""
    return view(t).pt(_mid(B("draw2.circle")))


# ------------------------------------------------------------------ Turkey's seat, and the way out of it
PORT, R = Wd.PORT, Wd.PORT_R
OPEN_K = 1.2
TROUT3 = [(668, 150, 0.42, 0, 0.0), (676, 330, 0.52, 2, 1.3), (600, 396, 0.40, 1, 2.4)]     # where the last child left them


def _beyond(t):
    """What M. left beyond the glass: the shell on the brick wall, three trout holding a finger from the pane."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    Wd.river(im, t, seed=0)
    Wd.brick_wall(im, 236, 0, 250, 540, seed=2)
    Wd.clam_pa(im, 432, 236, 0.8, 4.0 + 1.4 * math.sin(t * 1.3), t, split=0.5)
    for x, y, s, kind, ph in TROUT3:
        Wd.trout(im, x, y, s, t, kind=kind, pose="look", phase=ph, gaze=(-2.0, 0.3))
    Wd.river_plane(im, "front", t)
    return im


def open_water(t):
    """The same water with no window round it: where we are once we are through the glass (the porthole's own
    middle is the middle of this picture)."""
    k = OPEN_K
    return _beyond(t).transform((W, H), Image.AFFINE, (1 / k, 0, PORT[0] - (W / 2) / k, 0, 1 / k, PORT[1] - (H / 2) / k), Image.BICUBIC)


@lru_cache(None)
def _glass_mask():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([PORT[0] - R, PORT[1] - R, PORT[0] + R, PORT[1] + R], fill=255)
    return m


def view_out(t):
    """Turkey's seat: the brass porthole from where he sits, the shell and the trout outside it, his reflection."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    im.paste(open_water(t), (PORT[0] - W // 2, PORT[1] - H // 2))       # exactly what through_glass shows in the hole
    Wd.cabin(im, t)
    Wd.air_gauge(im, 196, 418, 0.5, r=30, t=t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Wd.turkey(lay, 452, 470, 0.86, "freak", t * 1.3, flip=True, shade=0.25, feathers=False, drop=False)
    a = lay.getchannel("A").point(lambda q: int(q * 0.38))
    lay.putalpha(Image.composite(a, Image.new("L", (W, H), 0), _glass_mask()))
    im.paste(lay, (0, 0), lay)
    return im


# ------------------------------------------------------------------ the river, looking back
MX, MY = 110, 64                                           # layers are this much bigger than the frame all round
LW, LH_ = W + 2 * MX, H + 2 * MY
TIN_AT = (430, 286, 0.42)
SHELL = (742, 120, 0.82)                                   # the pin on the brick flat; the shell opens left, over the tin
T_NOSE, T_OPEN, T_SNAP = 9.9, 10.35, 10.72                 # one action: a trout noses in, the shell snaps, it flinches


def _shell_gape(t):
    if t < T_SNAP - 0.08:
        return 4.0 + 1.2 * math.sin(t * 1.3) + 30.0 * ease(t, T_OPEN, T_SNAP - 0.12)
    if t < T_SNAP:
        return 34.0 * (1 - ramp(t, T_SNAP - 0.08, T_SNAP) ** 2)
    return max(0.0, 5.0 * Wd.settle(t, T_SNAP, 1.0, 3.2, 7.0))


def _back_layers(t):
    """[(image, depth)] back to front: water, the brick flat with the shell, the small tin, three trout near us."""
    water = Image.new("RGB", (W, H), (0, 0, 0))
    Wd.river(water, t, seed=1)
    water = water.resize((LW, LH_), Image.BILINEAR)

    wall = Image.new("RGBA", (LW, LH_), (0, 0, 0, 0))
    Wd.brick_wall(wall, MX + 690, MY - 40, W - 690 + MX, 620, seed=2, flip=True)
    Wd.clam_pa(wall, MX + SHELL[0], MY + SHELL[1], SHELL[2], _shell_gape(t), t, flip=True, split=0.3)

    mid = Image.new("RGBA", (LW, LH_), (0, 0, 0, 0))
    x, y, s = TIN_AT
    fl = Wd.settle(t, T_SNAP, 1.0, 2.4, 4.0)
    Wd.tin(mid, MX + x, MY + y, s, t * 1.35, mood="freak", handle=1.0, tag=12.0 * fl, latch=0.0, dial=0.5)
    go = ease(t, T_NOSE, T_SNAP - 0.1)
    back = ease(t, T_SNAP, T_SNAP + 0.3)
    nx = lerp(646, 578, go) + 74 * back + 5 * fl
    ny = 196 + 10 * go - 16 * back
    Wd.trout(mid, MX + nx, MY + ny, 0.26, t, kind=3, pose="look" if t < T_SNAP else "swim", phase=0.7,
             pitch=-10 * go * (1 - back) + 14 * back * (1 - ease(t, T_SNAP + 0.5, T_SNAP + 1.0)), gaze=(-1.8, -0.6),
             jaw=12 if T_SNAP <= t < T_SNAP + 0.5 else None)

    near = Image.new("RGBA", (LW, LH_), (0, 0, 0, 0))
    jolt = 6 * fl
    Wd.trout(near, MX + 800 + jolt, MY + 470, 1.05, t, kind=2, pose="look", phase=1.3, pitch=6, gaze=(-2.0, -1.0), shade=0.22)
    Wd.trout(near, MX + 150 - jolt, MY + 500, 1.2, t, kind=0, flip=True, pose="look", phase=0.0, pitch=8, gaze=(2.0, -1.0), shade=0.26)
    Wd.trout(near, MX + 520, MY + 590, 0.9, t, kind=1, pose="look", phase=2.4, pitch=10, gaze=(-1.5, -2.0), shade=0.3)
    return [(water, 3.0), (wall, 1.22), (mid, 1.0), (near, 0.5)]


def river_back_look(t):
    """The trout's seat: out in the river, looking back past three trout at the small tin with a small Turkey in it."""
    return cam.shoot(_back_layers(t), x=key(t, [(9.4, 22), (11.9, -18)], "linear"), y=key(t, [(9.4, 6), (11.9, -4)], "linear"),
                     zoom=1.0, focus=key(t, [(9.4, 0.5), (9.7, 0.5), (10.3, 1.05)]), aperture=7, shake=2.0, t=t,
                     dolly=key(t, [(9.4, 0.0), (11.9, 0.06)], "linear"), bg=(20, 44, 52))


# ------------------------------------------------------------------ the small thoughts (pictures only)
TH5 = (16.4, 18.2)
TH6 = (19.1, 20.9)
TH_AT = (812, 124, 110)


def _crop(im, cx, cy, hh=202):
    hw = int(hh * 16 / 9)
    cx = clamp(cx, hw, W - hw)
    cy = clamp(cy, hh, H - hh)
    return im.crop((int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh))).resize((W, H), Image.BILINEAR)


def _thought5(t):
    """Trout going round the small tin in pairs (c10's staged bolt 5)."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    C10R._b5(im, t, lerp(0.7, 3.2, ramp(t, TH5[0], TH5[1])))
    return _crop(im, 400, 290, 262)


def _thought6(t):
    """The small tin's door swings on its hinge and the trout go in, one after another (c10's staged bolt 6)."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    C10R._b6(im, t, lerp(0.75, 3.3, ramp(t, TH6[0], TH6[1])))
    return _crop(im, C10R.PORT6[0] - 30, C10R.PORT6[1] - 6, 236)


# ------------------------------------------------------------------ the film
T_PASS = (0.0, 0.5)
T_IN = (6.1, 7.0)            # R4: in through the dashed circle
T_GLASS = (7.0, 8.2)         # R5: through the glass
T_SWING = (8.2, 9.4)         # R6: the swing round
T_LOOK = (9.4, 11.9)         # R7: looking back
T_UP = (11.9, 12.8)          # R8: back up


def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < T_PASS[1]:
        return cam.whip(m_desk(), desk_frame(t), ramp(t, *T_PASS), direction=-1)
    if t < T_IN[0] or t >= T_UP[1]:
        fr = desk_frame(t)
        if t < 1.6:                                       # the eye rights itself with the page
            e = 1 - ease(t, 0.5, 1.55)
            fr = cam.shoot([(fr, 1.0)], rot=-8 * e, zoom=1.0 + 0.05 * e, bg=BG)
        for (a, b), inner, wob in ((TH5, _thought5, 3), (TH6, _thought6, 3)):
            if a < t < b + 0.3:
                u = key(t, [(a, 0.0), (a + 0.45, 1.0), (b - 0.1, 1.0), (b + 0.3, 0.0)])
                if u > 0.01:
                    fr = cam.thought(fr, inner(t), TH_AT[0], TH_AT[1], TH_AT[2], u, wobble=wob, t=t, dim=0.0)
        return fr
    if t < T_IN[1]:
        cx, cy = circle_xy(t)
        return cam.dive(desk_frame(t), view_out(t), cx, cy, ramp(t, *T_IN))
    if t < T_GLASS[1]:
        return cam.through_glass(view_out(t), open_water(t), PORT[0], PORT[1], R, ramp(t, *T_GLASS))
    if t < T_SWING[1]:
        return cam.turn(open_water(t), river_back_look(max(t, T_LOOK[0])), ramp(t, *T_SWING), axis="y", direction=-1)
    if t < T_LOOK[1]:
        return river_back_look(t)
    cx, cy = circle_xy(t)
    return cam.dive(desk_frame(t), river_back_look(t), cx, cy, 1 - ramp(t, *T_UP))


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m10_trout.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.1, 0.3, 0.7, 1.2, 1.7, 2.2, 2.6, 3.4, 4.9, 5.9, 6.4, 6.8, 7.3, 7.8, 8.5, 8.9,
                                              9.5, 10.3, 10.8, 11.6, 12.3, 13.1, 13.7, 14.27, 15.2, 15.88, 17.3, 18.5, 19.8, 21.2, 22.5, 23.8]
    cols = 4
    tw, th = 480, 270
    sheet = Image.new("RGB", (cols * tw, ((len(ts) + cols - 1) // cols) * th), (20, 20, 24))
    t0 = time.time()
    for i, tt in enumerate(ts):
        fr = frame(tt).convert("RGB")
        cap = [c for a, b, c in CAPTIONS if a <= tt < b]
        d = ImageDraw.Draw(fr)
        d.rectangle([0, 0, 110, 24], fill=(0, 0, 0))
        d.text((6, 5), f"t={tt:.2f}", fill=(255, 255, 255))
        if cap:
            d.text((120, 5), cap[0], fill=(255, 255, 0))
        sheet.paste(fr.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(out, f"{(time.time() - t0) / len(ts):.2f} s/frame")
