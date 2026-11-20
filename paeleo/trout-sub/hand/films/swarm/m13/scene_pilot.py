"""m13 · scene_pilot · the pilot, S., fills in page 1 of Porthole Log 13 (board beats P1 to P11, 0.0 to 31.0 s).

The first try at the name rubbed out and written again, smaller; the slip looked at; a faint oval begun and rubbed
out; the upper fish; a dive through the drawn ring into the thought, where a second fish puts itself together, a
second speech bubble forms for it, wobbles and falls apart, and an empty bubble stays over the upper fish; back up;
the box rubbed out on the page and "haha verry funny" squeezed into the bubble that stayed; a whip to the slip's
big bell and back; the small bell, the weeds, the point hanging over the place where Turkey is in the slip's
picture, and leaving; the three lines in her own spelling with their true traces (two answers to one stem, the
sheet turned over to copy "Bell-ringer", words spaced out to fill the rule, "freek out." carried on from the stem
with its first letter gone over, the bar of a "T" that became "he", "turkey diner", and "the" and "sub." added
faintly afterwards, "sub." half rubbed); the sheet slid to the left.

Seats are full pictures: `_desk_frame(t)` (the desktop laid back by cam.tilt; hands and the back of the head from
people.py), `_thought(t)` (the c13 river with the drawing as pencil line), and the two small looks into a thought
(`_freak_inner`, `_dinner_inner`: Turkey's seat from the c13 world). Moves between them are cam.dive, cam.whip and
cam.thought; moves at the desk are one keyframed tilt camera (`_cam`). Nothing is cross-faded.

Exposes SECONDS, CAPTIONS, draw(t, ink); and for the other units page1(t) (the written sheet at film time t,
SZ = 1216 x 1568; page1(SECONDS) is the page as the pilot left it).

    python3 films/swarm/m13/scene_pilot.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
C13 = FILMS / "swarm" / "c13"
for p in (str(FILMS), str(C13)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402
from kit import Ink, FPS, clamp, lerp, ramp, smooth, ease  # noqa: E402

SECONDS = 31.0
CAPTIONS = [
    (22.0, 24.5, "The trout. The trout think the sub is a bell-ringer prank."),
    (24.8, 27.3, "Freak out."),
    (27.6, 30.1, "He is going to be turkey dinner."),
]

TONE = "rust"
HAIR = "braids"
W, H = 960, 540

# ------------------------------------------------------------------ the desktop (a picture bigger than the frame)
SZ = (1216, 1568)                       # the sheet, in desktop pixels
DW, DH = 2400, 2100                     # the desk top
PX, PY = 442, 250                       # the sheet's top-left corner on it
SLIP = (2020, 770)                      # the slip, to the right of the sheet
SLIP_S, SLIP_A = 2.2, 5.0
CLUE = "Bell Boulder arch with brass twig-bell"
XH = 21.0                               # her x-height


def B(name, page=1):
    return P.where(page, name, SZ)


def D(x, y):
    """page px -> desktop px"""
    return (PX + x, PY + y)


RING = B("ring.in")
RCX, RCY = (RING[0] + RING[2]) / 2, (RING[1] + RING[3]) / 2
RR = (RING[2] - RING[0]) / 2


def RP(u, v):
    """ring units (centre 0,0, inner radius 1) -> page px"""
    return (RCX + u * RR, RCY + v * RR)


class _Shim:
    """What world.pilot_drawing needs of an Ink: a `.d` to draw on."""
    def __init__(self, img):
        self.d = ImageDraw.Draw(img, "RGBA")


_DUMMY = _Shim(Image.new("RGB", (4, 4)))


# ------------------------------------------------------------------ what gets put on the page, and when
class Act:
    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1

    def u(self, t):
        return ramp(t, self.t0, self.t1)

    tip = None


class Write(Act):
    def __init__(self, t0, t1, box, text, seed, weight=1.0, size=XH):
        super().__init__(t0, t1)
        self.box, self.text, self.seed, self.weight, self.size = box, text, seed, weight, size
        self.plan = P.write_plan(box, text, seed, size)

    def draw(self, img, u):
        P.write_on(img, self.box, self.text, u, self.seed, self.weight, self.size)

    def tip(self, u):
        return self.plan.tip(u)


class Lines(Act):
    """Pencil polylines drawn in order (the faint oval, the box, go-overs, the bar)."""
    def __init__(self, t0, t1, lines, weight=1.0, width=2.6, seed=0):
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
            return tuple(self.lines[0][0]) + (False,)
        _, p = self._upto(min(u, 1.0))
        return (p[0], p[1], u < 1)


class Rub(Act):
    """The rubber going over a patch: the graphite under it stays as a ghost."""
    def __init__(self, t0, t1, box, strength=1.0, seed=0):
        super().__init__(t0, t1)
        self.box, self.strength, self.seed = box, strength, seed

    def draw(self, img, u):
        P.rub_mark(img, self.box, self.strength * u, self.seed)


def _letter_lines(plan, idx):
    return [s for s, l in zip(plan.strokes, plan.letter) if l == idx]


def _go_over(lines, passes, seed, jit=1.2):
    rs = random.Random(seed)
    out = []
    for _ in range(passes):
        for ln in lines:
            dx, dy = rs.uniform(-jit, jit), rs.uniform(-jit, jit)
            out.append([(x + dx + rs.uniform(-0.4, 0.4), y + dy + rs.uniform(-0.4, 0.4)) for x, y in ln])
    return out


def _spread(t0, t1, box, words, seed, weight=1.0, size=XH):
    """Words set down at their own places along the rule. words = [(text, fraction of the rule's width)]."""
    acts = []
    wd = box[2] - box[0]
    for i, (text, fx) in enumerate(words):
        bx = (box[0] + fx * wd, box[1], box[2] + 200, box[3])
        acts.append(Write(0, 0, bx, text, seed + i % 4, weight, size))
    air = [0.0] + [0.35 * abs(b.plan.start[0] - a.plan.end[0]) + 14 for a, b in zip(acts, acts[1:])]
    tot = sum(a.plan.T for a in acts) + sum(air)
    tt = t0
    for a, g in zip(acts, air):
        tt += (t1 - t0) * g / tot
        a.t0 = tt
        tt += (t1 - t0) * a.plan.T / tot
        a.t1 = tt
    return acts


def _rot(pts, c, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


def _wob(pts, seed, amt=0.006, per=5):
    """A child's line through ring-unit points: curved through them, not quite true."""
    rs = random.Random(seed)
    pts = Wd.catmull(pts, per) if len(pts) > 2 else pts
    return [(x + rs.gauss(0, amt), y + rs.gauss(0, amt)) for x, y in pts]


# the two things she rubbed out, in ring units
OVAL_C = (-0.72, -0.21)
OVAL_U = [_wob([(OVAL_C[0] + 0.19 * math.cos(a), OVAL_C[1] + 0.105 * math.sin(a) - 0.02 * math.cos(a))
                for a in np.linspace(0.3, 0.3 + 2 * math.pi * 1.04, 16)], 3)]
BOX_C = (0.47, -0.03)
_bx = [(-0.17, -0.105), (0.17, -0.115), (0.175, 0.10), (-0.165, 0.105)]
BOX_U = [
    _wob([_bx[0], (0.0, -0.118), _bx[1]], 11),
    _wob([_bx[1], (0.18, 0.0), _bx[2]], 12),
    _wob([_bx[2], (0.0, 0.112), _bx[3]], 13),
    _wob([_bx[3], (-0.175, 0.0), _bx[0]], 14),
    _wob([(-0.07, 0.105), (-0.085, 0.16), (-0.03, 0.215), (0.035, 0.19), (0.03, 0.105)], 15),      # the lobe, down to the lower fish
    _wob([(-0.125, -0.035), (-0.10, -0.075), (-0.075, -0.03), (-0.05, -0.07), (-0.02, -0.035), (0.01, -0.07), (0.04, -0.03),
          (0.07, -0.065), (0.10, -0.03)], 16, 0.004),                                               # marks nobody can read
    _wob([(-0.11, 0.05), (-0.08, 0.015), (-0.05, 0.05), (-0.02, 0.02), (0.02, 0.055), (0.05, 0.02), (0.085, 0.05)], 17, 0.004),
]
BOX_U = [_rot([(BOX_C[0] + x, BOX_C[1] + y) for x, y in ln], BOX_C, -13) for ln in BOX_U]


def _bbox(lines, pad=6):
    xs = [p[0] for ln in lines for p in ln]
    ys = [p[1] for ln in lines for p in ln]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


OVAL_P = [[RP(*p) for p in ln] for ln in OVAL_U]
BOX_P = [[RP(*p) for p in ln] for ln in BOX_U]
NL = B("name.line")
A11, A12, A21, A31 = B("a1.1"), B("a1.2"), B("a2.1"), B("a3.1")
Q1, Q2, Q3 = B("q1"), B("q2"), B("q3")
NAME_RUB = (NL[0] + 6, 204, NL[0] + 300, 245)


def _build():
    acts = []
    # P1: the first try at the name, too big and too high, is already there and already being rubbed
    acts.append(Write(-3.0, -2.0, (NL[0] + 22, NL[1] - 12, NL[2], NL[3] - 11), "S", 130, 1.0, 23))
    acts.append(Lines(-2.0, -1.5, [[(NL[0] + 62 + 34 * k + 9 * math.sin(k * 2.1 + j), 236 - 2.2 * k - 13 * (j % 2) - 5 * math.cos(k * 1.3))
                                    for j in range(5)] for k in range(6)], 0.36, 2.4, 131))          # what is left of the rest: not letters
    acts.append(Rub(-1.0, 1.5, NAME_RUB, 1.0, 132))
    acts.append(Write(1.95, 2.45, (NL[0] + 14, NL[1], NL[2], NL[3]), "S", 133, 1.1, 15))            # again: smaller, lower, on the line
    # P2: a faint oval at the left of the ring, rubbed out
    acts.append(Lines(4.2, 4.55, OVAL_P, 0.45, 2.6, 134))
    acts.append(Rub(4.6, 5.0, _bbox(OVAL_P), 0.9, 135))
    # P4/P5 (while we are in the thought): a second bubble, for the lower fish, with marks in it
    acts.append(Lines(9.45, 10.35, BOX_P, 0.9, 2.5, 136))
    # P6: rubbed out
    acts.append(Rub(11.6, 12.5, _bbox(BOX_P), 1.0, 137))

    # P8: line 1. Two answers to a stem with two questions; the words stand further and further apart.
    acts.append(Write(17.08, 17.9, (A11[0] + 8, A11[1], A11[2], A11[3]), "The trout.", 130))
    acts += _spread(19.75, 21.05, A11, [("The", 0.215), ("trout", 0.305), ("think's", 0.465), ("the", 0.635), ("sub", 0.765),
                                        ("is", 0.885), ("a", 0.955)], 131)
    acts.append(Write(21.12, 21.8, (A12[0] + 14, A12[1], A12[2], A12[3]), "Bell-ringer prank.", 135))

    # P9: line 2 carries on from the printed stem. Pressed; the first letter gone over.
    f = Write(22.8, 22.98, (A21[0] + 12, A21[1], A21[2], A21[3]), "f", 136, 1.3)
    acts.append(f)
    acts.append(Lines(23.0, 23.36, _go_over(f.plan.strokes, 2, 5), 1.3, 3.2, 9))
    acts.append(Write(23.42, 24.6, (f.plan.x_end + 1, A21[1], A21[2], A21[3]), "reek out.", 137, 1.3))

    # P10: line 3. A bar first, as if for a "T"; then "he" under it, and straight on.
    L3 = _spread(25.9, 27.5, A31, [("he", 0.012), ("is", 0.105), ("going", 0.20), ("to", 0.36), ("be", 0.455),
                                   ("turkey", 0.56), ("diner.", 0.765)], 138)
    h = _letter_lines(L3[0].plan, 0)
    hx, hy = min(p[0] for ln in h for p in ln), min(p[1] for ln in h for p in ln)
    acts.append(Lines(25.2, 25.36, [[(hx - 9, hy + 1.5), (hx + 1, hy + 0.5), (hx + 13, hy + 1)]], 1.0, 3.0, 21))
    acts += L3

    # P11: two words added afterwards, faintly; the second half rubbed
    the = Write(29.0, 29.3, (A21[0] + 0.335 * (A21[2] - A21[0]), A21[1], A21[2], A21[3]), "the", 139, 0.45)
    sub = Write(29.46, 29.82, (A21[0] + 0.525 * (A21[2] - A21[0]), A21[1], A21[2], A21[3]), "sub.", 134, 0.4)
    s0 = _letter_lines(sub.plan, 0)
    acts += [the, sub, Lines(29.82, 29.9, _go_over(s0, 1, 3, 1.6), 0.4, 2.6, 23)]                  # the s, doubled
    bb = _bbox(sub.plan.strokes, 3)
    acts.append(Rub(29.95, 30.3, bb, 0.42, 138))
    acts.sort(key=lambda a: a.t0)
    return acts, sub


ACTS, _SUB = _build()
SUB_BOX = _bbox(_SUB.plan.strokes, 3)

# the drawing itself (world.pilot_drawing): how much of each group is on the page at t
_F2 = [s for s in Wd.PILOT_STROKES if s["group"] == "fish2"]
_F2_BODY = sum(s["len"] for s in _F2[:7]) / sum(s["len"] for s in _F2)        # body, eye, smile, tail: before the hatching
_BB = [s for s in Wd.PILOT_STROKES if s["group"] == "bubble"]
_BB_OUT = sum(s["len"] for s in _BB[:2]) / sum(s["len"] for s in _BB)         # the outline and neck: before the words
DRAWN = {
    "fish1": [(5.05, 0.0), (7.0, 1.0)],
    "fish2": [(7.2, 0.0), (9.4, _F2_BODY), (10.4, _F2_BODY), (11.36, 1.0)],
    "bubble": [(12.95, 0.0), (13.42, _BB_OUT), (13.5, _BB_OUT), (14.38, 1.0)],
    "bell": [(15.62, 0.0), (15.95, 1.0)],
    "weed_r": [(15.98, 0.0), (16.14, 1.0)],
    "weed_l": [(16.17, 0.0), (16.4, 1.0)],
}
DRAW_WIN = [("fish1", 5.05, 7.0), ("fish2", 7.2, 9.4), ("fish2", 10.4, 11.36), ("bubble", 12.95, 13.42), ("bubble", 13.5, 14.38),
            ("bell", 15.62, 15.95), ("weed_r", 15.98, 16.14), ("weed_l", 16.17, 16.4)]


def _drawn(t):
    return {g: cam.key(t, k, "linear") for g, k in DRAWN.items()}


def _draw_tip(g, f):
    tip, down = Wd.pilot_drawing(_DUMMY, {g: max(f, 1e-4)}, (RCX, RCY), RR)
    return tip[0], tip[1], down and f < 1


_page_cache = {}
_PAGE2 = None


def page1(t):
    """The pilot's page as it stands at film time t: a fresh PIL image, SZ = 1216 x 1568 (use P.where(1, name, SZ))."""
    key = tuple(i for i, a in enumerate(ACTS) if t >= a.t1)
    if key not in _page_cache:
        if len(_page_cache) > 6:
            _page_cache.clear()
        img = P.sheet(SZ, page=1, porthole=13)
        for a in ACTS:
            if a.t1 <= t:
                a.draw(img, 1.0)
        _page_cache[key] = img
    img = _page_cache[key].copy()
    for a in ACTS:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    if t > 5.05:
        Wd.pilot_drawing(_Shim(img), _drawn(t), (RCX, RCY), RR)
    return img


def page2():
    """The back of the sheet as the pilot saw it: printed, empty."""
    global _PAGE2
    if _PAGE2 is None:
        _PAGE2 = P.sheet(SZ, page=2, porthole=13)
    return _PAGE2


# ------------------------------------------------------------------ where the pencil point is (page px)
ERASE = [  # (t0, t1, from, to): the rubber's path
    (0.0, 1.5, (NL[0] + 262, 222), (NL[0] + 96, 226)),
    (4.6, 5.0, RP(OVAL_C[0] - 0.1, OVAL_C[1]), RP(OVAL_C[0] + 0.1, OVAL_C[1])),
    (11.6, 12.5, RP(BOX_C[0] - 0.12, BOX_C[1] - 0.03), RP(BOX_C[0] + 0.1, BOX_C[1] + 0.06)),
    (29.95, 30.3, (SUB_BOX[0] + 12, (SUB_BOX[1] + SUB_BOX[3]) / 2), (SUB_BOX[2] - 10, (SUB_BOX[1] + SUB_BOX[3]) / 2)),
]
FLIP = (18.2, 18.46, 19.36, 19.66)                    # tilt up, page 2 from, page 1 again from, settled
PL2B = B("plate2b", 2)
OVER_RING = (RCX + 40, RCY + 30)
PAUSE = RP(-0.12, 0.62)                               # the bare paper low in the ring
AFTER_FREEK = (A21[0] + 0.335 * (A21[2] - A21[0]) - 6, A21[3] - 5)
AIR = [  # (t, (x, y) page px, lift)
    (3.1, OVER_RING, 18), (4.12, OVER_RING, 18),      # hovering over the empty ring while she looks at the slip
    (11.52, RP(0.93, 0.02), 16),                      # lifting off the lower fish's tail
    (12.64, (RCX + 520, RCY + 40), 24), (12.9, (RCX + 520, RCY + 40), 24),      # out of the way of the other hand
    (14.55, RP(0.3, -0.25), 18), (15.5, RP(0.3, -0.25), 18),                       # held while she looks
    (16.47, PAUSE, 16), (16.66, PAUSE, 16),           # over the place where Turkey is in the slip's picture; and leaves
    (16.78, (Q1[0] + 30, Q1[3] + 7), 7), (17.0, (386, Q1[3] + 7), 7), (17.05, (386, Q1[3] + 7), 7),   # under the stem to the first "?"
    (18.02, (A11[0] + 240, A11[3] - 5), 17), (FLIP[1], (A11[0] + 240, A11[3] - 5), 17),
    (19.4, (A11[0] + 240, A11[3] - 5), 17), (19.62, (A11[0] + 226, A11[3] - 5), 17),
    (22.06, (A21[0] + 14, A21[3] - 6), 17), (22.74, (A21[0] + 14, A21[3] - 6), 17),                   # stuck: 0.8 s
    (24.95, (Q3[0] + 30, Q3[3] + 7), 7), (25.12, (Q3[0] + 200, Q3[3] + 7), 7),                         # under the third stem
    (25.44, (A31[0] + 26, A31[1] + 2), 4), (25.84, (A31[0] + 26, A31[1] + 2), 4),                      # the hand stops
    (28.2, AFTER_FREEK, 17), (28.98, AFTER_FREEK, 17),                                                 # back up the page; 0.8 s
    (30.38, (SUB_BOX[2] + 10, SUB_BOX[3]), 12), (30.8, (1500, 1020), 34),                              # away, to lay the pencil down
]


def _pen_keys():
    keys = []
    for a in ACTS:
        if a.tip is not None and a.t0 >= 0:
            keys += [(a.t0, a.tip(0.0)[:2] + (7,)), (a.t1, a.tip(1.0)[:2] + (7,))]
    for g, t0, t1 in DRAW_WIN:
        f0, f1 = cam.key(t0, DRAWN[g], "linear"), cam.key(t1, DRAWN[g], "linear")
        keys += [(t0, _draw_tip(g, f0)[:2] + (7,)), (t1, _draw_tip(g, f1)[:2] + (7,))]
    for t0, t1, a, b in ERASE:
        keys += [(t0, tuple(a) + (5,)), (t1, tuple(b) + (5,))]
    keys += [(tt, tuple(p) + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    return keys


PEN_KEYS = _pen_keys()


def _pen(t):
    """(x, y, lift, pose) of the pencil point (or the rubber) on the page at t."""
    for t0, t1, a, b in ERASE:
        if t0 <= t < t1:
            k = 0.5 - 0.5 * math.cos(math.pi * 2.0 * ramp(t, t0, t1))       # across and back
            return lerp(a[0], b[0], k), lerp(a[1], b[1], k), 0, "erase"
    if FLIP[1] <= t < FLIP[2]:                                                # the back of the sheet: under the pink-square plate
        x, y, l = cam.key(t, [(FLIP[1], (PL2B[0] + 330, PL2B[3] + 60, 20)), (FLIP[1] + 0.3, (PL2B[0] + 262, PL2B[3] + 9, 6)),
                              (FLIP[2], (PL2B[0] + 270, PL2B[3] + 9, 6))])
        return x, y, l, "write"
    for a in ACTS:
        if a.tip is not None and a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return x, y, (0 if down else 5), "write"
    for g, t0, t1 in DRAW_WIN:
        if t0 <= t < t1:
            x, y, down = _draw_tip(g, cam.key(t, DRAWN[g], "linear"))
            return x, y, (0 if down else 5), "write"
    x, y, l = cam.key(t, PEN_KEYS, "smooth")
    return x, y, l, ("hover" if l >= 15 else "write")


# stuck: nothing moves (the hand's own time is held)
STILL = [(22.0, 22.8), (25.4, 25.88), (28.22, 29.0)]


def _held(t):
    for a, b in STILL:
        if a <= t < b:
            return a
    return None


# ------------------------------------------------------------------ the camera at the desk
# (deg, horizon, zoom, look x, look y [desktop px], at x, at y [screen px], head drop)
SCX, SCY = PX + SZ[0] / 2, PY + SZ[1] / 2
TOP = (0, 0.5, 0.80, SCX, PY + 330, 480, 270, 320)
SEAT = (62, 0.36, 0.50, SCX + 75, SCY, 480, 194, 0)
RINGSHOT = (52, 0.36, 1.2, PX + RCX + 30, PY + RCY, 440, 250, 230)
RINGCLOSE = (46, 0.36, 1.7, PX + RCX + 30, PY + RCY - 10, 450, 262, 430)
_M = P.Tm(*SLIP) @ P.Rm(SLIP_A) @ P.Sm(SLIP_S)
SLIP_PIC = P.apply(_M, (-62, -6))
SLIP_BELL = P.apply(_M, (-62, -22))
SLIPSHOT = (44, 0.36, 1.5, SLIP_PIC[0] + 110, SLIP_PIC[1], 480, 250, 430)
BELLSHOT = (32, 0.36, 2.3, SLIP_BELL[0], SLIP_BELL[1], 480, 262, 430)


def _close(px, py, sx=440, sy=300, zoom=0.80, deg=38):
    return (deg, 0.36, zoom, PX + px, PY + py, sx, sy, 430)


def _edge(c):
    return (88,) + c[1:]


C_A1 = _close(400, A11[3] - 16)
C_A1R = _close(800, A11[3] - 12)
C_A12 = _close(420, A12[3] - 12)
C_A2 = _close(400, A21[3] - 14)
C_P2 = (46, 0.36, 2.1, PX + PL2B[0] + 170, PY + PL2B[1] + 20, 400, 250, 430)
TWO = (42, 0.36, 0.64, PX + 560, PY + A31[1] - 34, 470, 262, 430)             # lines 2 and 3 together: P10 and P11
CAMKEYS = [
    (0.0, TOP),                                         # straight down on the desk
    (0.8, TOP),
    (2.4, SEAT, "smoother"),                            # settling back into the seat
    (2.55, SEAT),
    (3.2, RINGSHOT),                                    # already drifting down to the ring
    (3.62, SLIPSHOT),                                   # across to the slip ...
    (3.9, SLIPSHOT),
    (4.3, RINGSHOT),                                    # ... and back
    (11.5, RINGSHOT),
    (12.2, RINGCLOSE),                                  # push in on the ring
    (16.6, RINGCLOSE),
    (17.05, C_A1),                                      # down the page to zone 3
    (FLIP[0], C_A1),
    (FLIP[1] - 0.01, _edge(C_A1), "in"),                # the sheet comes up edge-on ...
    (FLIP[1], _edge(C_P2), "hold"),
    (FLIP[1] + 0.26, C_P2, "out"),                      # ... and it is the back
    (FLIP[2] - 0.16, C_P2),
    (FLIP[2] - 0.01, _edge(C_P2), "in"),
    (FLIP[2], _edge(C_A1), "hold"),
    (FLIP[3], C_A1, "out"),
    (19.9, C_A1),
    (21.05, C_A1R),                                     # along with the line as it is spaced out
    (21.4, C_A12),
    (21.8, C_A12),
    (22.0, C_A2),                                       # one question down; then still
    (24.8, C_A2),
    (25.15, TWO),
    (31.0, TWO),                                        # P11: the camera does not move
]
SHAKE = [(0.0, 0.0), (2.4, 3.0), (21.8, 2.5), (22.0, 0.0), (22.8, 0.0), (23.1, 2.0), (25.2, 1.5), (25.4, 0.0), (25.88, 0.0),
         (26.1, 1.5), (27.9, 1.5), (28.4, 0.0), (31.0, 0.0)]
SHOOT_ZOOM = 1.035


def _cam(t, shot=None):
    deg, hor, zoom, lx, ly, ax, ay, drop = shot or cam.key(t, CAMKEYS, "smooth")
    gx, gy = cam.tilt_point(lx, ly, deg, hor, zoom, 700, (0, 0), (DW, DH))
    return dict(deg=deg, hor=hor, zoom=zoom, shift=(ax - gx, ay - gy), drop=drop, shake=cam.key(t, SHAKE, "smooth"))


def _tp(c, dx, dy):
    """desktop px -> screen px (before the handheld shoot)."""
    return cam.tilt_point(dx, dy, c["deg"], c["hor"], c["zoom"], 700, c["shift"], (DW, DH))


def _mag(c, dx, dy):
    a, b = _tp(c, dx, dy), _tp(c, dx + 20, dy)
    return (b[0] - a[0]) / 20.0


def _final(x, y):
    return (W / 2 + (x - W / 2) * SHOOT_ZOOM, H / 2 + (y - H / 2) * SHOOT_ZOOM)


# ------------------------------------------------------------------ the desk top picture
_base = {}


def _slip_pic():
    im = Image.open(FILMS.parents[1] / "stills" / "p13.jpg").convert("RGB")
    return im.crop((36, 36, 604, 604))


def _desk_base(sheet):
    if sheet not in _base:
        im = Image.new("RGB", (DW, DH), P.DESK)
        P.desk(im)
        pic = _slip_pic()
        P.slip(im, SLIP[0], SLIP[1], 13, CLUE, SLIP_S, SLIP_A, picture=pic)
        n = int(108 * SLIP_S)                           # the picture again at the slip's own size, so it is sharp close to
        big = pic.resize((n, n), Image.LANCZOS).convert("RGBA").rotate(-SLIP_A, Image.BICUBIC, expand=True)
        im.paste(big, (int(SLIP_PIC[0] - big.size[0] / 2), int(SLIP_PIC[1] - big.size[1] / 2)), big)
        if sheet:
            P.lay(im, P.sheet(SZ, page=1, porthole=13), SCX, SCY)
        _base[sheet] = im.convert("RGBA")
    return _base[sheet]


def _sheet_dx(t):
    return -190 * ease(t, 30.62, 31.12)


def _brush(t):
    return ease(t, 12.56, 12.86)


def _desktop(t):
    dx = _sheet_dx(t)
    flipped = FLIP[1] <= t < FLIP[2]
    pg = page2() if flipped else page1(t)
    if dx == 0:
        im = _desk_base(True).copy()
        im.paste(pg, (PX, PY))
    else:
        im = _desk_base(False).copy()
        P.lay(im, pg, SCX + dx, SCY)
    if flipped or t >= FLIP[1]:
        if t >= 29.95:                                  # a few crumbs from "sub."
            x, y = D((SUB_BOX[0] + SUB_BOX[2]) / 2 + 14 + dx, SUB_BOX[3] + 16)
            P.eraser_crumbs(im, x, y, int(1 + 4 * ramp(t, 29.95, 30.3)), 9, 26, 1.3)
        return im
    # rubber crumbs: the name's (brushed off while she looks at the slip), the oval's and the box's
    if t < 4.0:
        n = int(3 + 11 * ramp(t, 0.0, 1.5))
        if t > 3.4:
            n = 0
        if n:
            P.eraser_crumbs(im, *D(NL[0] + 110, 266), n, 3, 70, 1.5)
    if t >= 4.6:
        b = _brush(t)
        n = int(1 + 4 * ramp(t, 4.6, 5.0))
        x, y = RP(OVAL_C[0] + 0.02, OVAL_C[1] + 0.2)
        P.eraser_crumbs(im, *D(x, y), n, 5, 26, 1.4)
    if t >= 11.6:
        b = _brush(t)
        n = int(2 + 12 * ramp(t, 11.6, 12.5))
        x, y = RP(BOX_C[0] + 0.02, BOX_C[1] + 0.22)
        P.eraser_crumbs(im, *D(x + 430 * b, y - 20 * b), n if b < 0.6 else max(5, int(n * (1.5 - b))), 7, 34 + 60 * b, 1.4)
    return im


# ------------------------------------------------------------------ the hands
def _hand_scale(c, dx, dy):
    return clamp(1.42 * _mag(c, dx, dy), 0.5, 2.0)


def _right_hand(fr, c, t):
    px, py, lift, pose = _pen(t)
    hold = _held(t)
    ht = t if hold is None else hold
    dx, dy = D(px + (_sheet_dx(t) if t < 30.4 else 0), py)
    s = _hand_scale(c, dx, dy)
    x, y = _tp(c, dx, dy)
    P.hand(fr, x, y, pose=pose, tone=TONE, scale=s, t=ht, lift=lift * s, arm=58)


LREST = (120, 760)


def _left_hand(fr, c, t):
    hold = _held(t)
    ht = t if hold is None else hold
    x, y, lift = cam.key(t, [
        (0.0, LREST + (0,)),
        (12.4, LREST + (0,)), (12.6, (RCX - 150, RCY + 40, 6)), (12.88, (RCX + 210, RCY + 30, 5)),        # the side of the hand: crumbs off
        (13.3, LREST + (0,)),
        (17.92, LREST + (0,)), (FLIP[0], (26, 1010, 8)), (FLIP[3], (26, 1010, 8)), (19.95, LREST + (0,)),   # takes the sheet by its edge
        (30.2, LREST + (0,)), (30.6, (250, 1425, 0)),                                                       # flat on the sheet: to slide it
    ])
    dx, dy = D(x + _sheet_dx(t), y)
    s = _hand_scale(c, dx, dy)
    P.hand(fr, *_tp(c, dx, dy), pose="hold", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=142)


def _head_layer(c, t):
    if c["drop"] >= 400:
        return None
    lay = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    look = ease(t, 3.25, 3.6) - ease(t, 3.9, 4.25)                           # to the slip, on her right, and back
    P.head_back(lay, 60 + 790, 60 + 640 + c["drop"], TONE, 1.05, tilt=6 * look, hair=HAIR, turn=0.75 * look, t=t)
    return lay


def _desk_frame(t, shot=None):
    """The pilot's seat at t: desk, sheet as written so far, slip, hands, the back of the head. A full 960x540 frame."""
    c = _cam(t, shot)
    fr = cam.tilt(_desktop(t), c["deg"], c["hor"], c["zoom"], 700, c["shift"], bg=(92, 66, 44), shadow=0)
    if c["deg"] < 80:
        _left_hand(fr, c, t)
        _right_hand(fr, c, t)
    layers = [(fr, 1.0)]
    head = _head_layer(c, t)
    if head is not None:
        layers.append((head, 0.62))
    # the rack: soft as the eye lands on the slip, sharp; soft as it comes back to the ring, sharp
    focus = cam.key(t, [(3.3, 1.0), (3.56, 0.72), (3.76, 1.0), (4.0, 1.0), (4.22, 0.74), (4.5, 1.0)])
    return cam.shoot(layers, zoom=SHOOT_ZOOM, focus=focus, aperture=6, shake=c["shake"], t=t)


# ------------------------------------------------------------------ the thought (inside the drawn ring)
PENCIL_LIGHT = (240, 240, 230)
T_C, T_S = (430, 292), 300.0                 # ring units -> the thought's frame
TM = 80


def _tx(pts, ang=0.0, off=(0, 0), pin=None):
    a = np.asarray(pts, np.float32)
    if pin is None:
        pin = (float(a[:, 0].mean()), float(a[:, 1].mean()))
    r = math.radians(ang)
    ca, sa = math.cos(r), math.sin(r)
    x, y = a[:, 0] - pin[0], a[:, 1] - pin[1]
    X = pin[0] + x * ca - y * sa
    Y = pin[1] + x * sa + y * ca
    return list(zip((TM + T_C[0] + X * T_S + off[0]).tolist(), (TM + T_C[1] + Y * T_S + off[1]).tolist()))


def _gline(lay, pts, width, weight, seed):
    if weight <= 0.03 or len(pts) < 2:
        return
    P.graphite(lay, [[(x + 2, y + 3) for x, y in pts]], width + 1.5, weight * 0.5, seed, (10, 40, 48))     # its shadow in the water
    P.graphite(lay, [pts], width, weight, seed, PENCIL_LIGHT)


def _part(pts, u):
    n = max(2, int(round(u * (len(pts) - 1))) + 1)
    return pts[:n]


_F1 = [s for s in Wd.PILOT_STROKES if s["group"] == "fish1"]
_water_cache = {}


def _water(t):
    k = int(t * 12)
    if k not in _water_cache:
        if len(_water_cache) > 4:
            _water_cache.clear()
        ink = Ink(t, int(t * FPS))
        Wd.river(ink, t)
        _water_cache[k] = ink.img.convert("RGB").resize((W + 180, H + 100), Image.BILINEAR).point(lambda v: int(v * 0.74))
    return _water_cache[k]


def _thought_lines(t):
    lay = Image.new("RGBA", (W + 2 * TM, H + 2 * TM), (0, 0, 0, 0))
    bob = 4 * math.sin(t * 1.7)
    # her upper fish hangs there
    for i, s in enumerate(_F1):
        _gline(lay, _tx(s["pts"], off=(0, bob)), 2.6 + 2.2 * s["weight"], 0.55 + 0.4 * s["weight"], i)
    # a second fish puts itself together, lower right (7.6 to 8.6)
    rs = random.Random(6)
    bob2 = 4 * math.sin(t * 1.5 + 1.4)
    for i, s in enumerate(_F2):
        ta = 7.62 + i * 0.045
        u = ease(t, ta, ta + 0.34)
        a0, dx0, dy0 = rs.uniform(-80, 80), rs.uniform(120, 520), rs.uniform(-260, 330)
        if u <= 0:
            continue
        _gline(lay, _tx(s["pts"], a0 * (1 - u), (dx0 * (1 - u), dy0 * (1 - u) + bob2 * u)), 2.6 + 2.2 * s["weight"],
               (0.55 + 0.4 * s["weight"]) * u, 30 + i)
    # a box with marks in it, its tail to the LOWER fish: it wobbles (9.15 to 9.6) and falls apart (9.6 to 10.2)
    rs = random.Random(9)
    wob = 0.0
    if 9.1 <= t < 9.62:
        k = (t - 9.1) / 0.52
        wob = 7.0 * math.sin(k * math.pi * 5) * (0.4 + 0.6 * k)
    for i, ln in enumerate(BOX_U):
        ta = 8.55 + i * 0.07
        u = ease(t, ta, ta + 0.3)
        a0, dx0, dy0 = rs.uniform(-60, 60), rs.uniform(-200, 380), rs.uniform(-330, -120)
        fa, fx, fy = rs.uniform(-70, 70), rs.uniform(-120, 200), rs.uniform(-60, 240)
        if u <= 0:
            continue
        fall = ramp(t, 9.6 + 0.04 * i, 10.2)
        gone = 1 - smooth(fall)
        if gone <= 0.02:
            continue
        pts = ln
        ang, off = a0 * (1 - u), (dx0 * (1 - u), dy0 * (1 - u) + bob2 * 0.5)
        if wob:
            pts = _rot(ln, BOX_C, wob * (1.0 if i < 5 else 1.5))
        if fall > 0:
            ang += fa * smooth(fall)
            off = (off[0] + fx * fall, off[1] + fy * fall * fall + 12 * math.sin(fall * 7 + i))
        _gline(lay, _tx(pts, ang, off), 4.0 if i < 5 else 3.0, 0.85 * u * gone, 50 + i)
    # an empty bubble forms over the UPPER fish, and stays. No words.
    for i, s in enumerate(_BB[:2]):
        u = ease(t, 9.75 + 0.42 * i, 10.2 + 0.25 * i)
        if u > 0:
            _gline(lay, _part(_tx(s["pts"], off=(0, bob), pin=(0, 0)), u), 4.6, 0.9, 70 + i)
    return lay


def _thought(t):
    """Inside the thought: open river, no brass, no tin; only what she is picturing, in pencil line. A full frame."""
    return cam.shoot([(_water(t), 3.0), (_thought_lines(t), 1.0)], x=cam.key(t, [(6.4, -14), (11.5, 26)], "linear"),
                     y=cam.key(t, [(6.4, 6), (11.5, -4)], "linear"), zoom=1.0,
                     dolly=cam.key(t, [(6.4, 0.0), (11.5, 0.08)], "linear"), shake=2, t=t, bg=(30, 70, 78))


# ---------------------------------------- the two looks into a thought while she writes (pictures, never words)
_spec = importlib.util.spec_from_file_location("c13_scene_pilot", str(C13 / "scene_pilot.py"))
C13P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C13P)


def _freak_inner(t):
    """Turkey behind his round glass, freaking out (line 2)."""
    ink = Ink(t, int(t * FPS))
    ink.fill(Wd.PAL["tin_dk"])
    Wd.tin_porthole(ink, (480, 270), 196, "freak", t, shake=3)
    return ink.img.convert("RGB")


def _dinner_inner(t):
    """From Turkey's seat: the brass bell coming down over his own reflection like a dish cover (the class film's A9)."""
    ink = Ink(t, int(t * FPS))
    C13P._seat(ink, 16.95 + (t - 26.2) * 1.15)
    im = ink.img.convert("RGB")
    return im.crop((480 - 284, 148, 480 + 284, 468)).resize((W, H), Image.LANCZOS)      # the bell and what is under it


# ------------------------------------------------------------------ the film
DIVE_IN = (6.4, 7.5)
DIVE_OUT = (10.5, 11.5)
WHIP_OUT = (14.4, 14.75)
WHIP_BACK = (15.25, 15.6)
TH2 = [(22.9, 0), (23.3, 1), (23.9, 1), (24.2, 0)]
TH3 = [(26.2, 0), (26.55, 1), (27.15, 1), (27.4, 0)]
TH_AT = (748, 176)


def _ring_on_screen(t):
    c = _cam(t)
    return _final(*_tp(c, PX + RCX, PY + RCY))


def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if DIVE_IN[0] <= t < DIVE_IN[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, ramp(t, *DIVE_IN), spin=40)
    if DIVE_IN[1] <= t < DIVE_OUT[0]:
        return _thought(t)
    if DIVE_OUT[0] <= t < DIVE_OUT[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, 1 - ramp(t, *DIVE_OUT))
    if WHIP_OUT[0] <= t < WHIP_OUT[1]:                   # eyes to the slip
        return cam.whip(_desk_frame(t), _desk_frame(t, BELLSHOT), ramp(t, *WHIP_OUT), direction=1)
    if WHIP_OUT[1] <= t < WHIP_BACK[0]:                  # the slip's big bell
        return _desk_frame(t, BELLSHOT)
    if WHIP_BACK[0] <= t < WHIP_BACK[1]:                 # and back
        return cam.whip(_desk_frame(t, BELLSHOT), _desk_frame(t), ramp(t, *WHIP_BACK), direction=-1)
    fr = _desk_frame(t)
    u = cam.key(t, TH2, "linear")
    if u > 0:
        fr = cam.thought(fr, _freak_inner(t), TH_AT[0], TH_AT[1], 120, u, wobble=5, t=t)
    u = cam.key(t, TH3, "linear")
    if u > 0:
        fr = cam.thought(fr, _dinner_inner(t), TH_AT[0], TH_AT[1], 120, u, wobble=2, t=t)
    return fr


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB") if fr.mode != "RGB" else fr)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m13_pilot.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.1, 1.2, 2.2, 3.0, 3.75, 4.8, 6.0, 6.7, 7.1, 7.8, 8.6, 9.3, 9.9, 10.4, 11.0, 12.0,
                                              12.7, 13.4, 14.3, 14.6, 15.0, 16.3, 16.55, 17.6, 18.35, 19.0, 20.4, 21.0, 21.7, 22.4,
                                              23.6, 24.7, 25.6, 26.8, 27.55, 28.6, 29.9, 30.2, 30.6, 30.95]
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
