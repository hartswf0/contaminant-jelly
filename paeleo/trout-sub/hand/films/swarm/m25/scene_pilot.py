"""m25 · scene_pilot · M., the pilot, fills in page 1 of Porthole Log 25 (board beats P1 to P14, 0.0 to 34.6 s).

Down into the seat over the blank sheet and the slip; one light capital on the name line; eyes to the slip's small
picture and back; the light drawing (a bowl gone round and round, a bean, an arm stub, an arm and a lump, two
walking legs, the small low tail) with the bowl left empty; a dive through the drawn ring into the thought, where a
fishbowl the right way up with a fish circling in it turns over, comes down on the body's shoulders, and the fish,
too long for it now, lies level across it; back up; the fish pressed hard over the light loops, with a tail of its
own; down the page; line 1 in two goes ("a trout", a look back at the stem's second question, "and the trout think
it" and a flattened "a"); the sheet turned over to the trout's plates and back; "Bird in a bottle." with the B and
the b gone over, while a thought ring shows the tin from the river side redrawn as a bottle; the point under "one
thing" and one word, "panit"; a short dead-still stuck; "by" gone over and over; a look up at his own "panit";
"paniting"; the whole front from nearly above and the pencil laid in the groove.

Nobody rubs anything out in this film: the corrections are pressure.

Seats are full pictures: `_desk_frame(t)` (the desk top laid back by cam.tilt, with the slip, the sheet as written
so far, both hands and the back of the head from people.py), `_thought(t)` (his own pencil lines, pale, standing in
the lock's water from the c25 world) and one look into a thought (`_bottle_inner`, the c25 river side). Moves
between them are cam.dive and cam.thought; moves at the desk are one keyframed tilt camera (`_cam`) and cam.shoot;
the sheet itself is turned over on the desk (`_turned`). Nothing is cross-faded.

Exposes SECONDS, CAPTIONS, draw(t, ink); and for the other units page1(t) (the written front at film time t,
SZ = 1216 x 1568; page1(SECONDS) is the page as M. left it) and frame(t) (the 960x540 picture without the badge).

    python3 films/swarm/m25/scene_pilot.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
C25 = FILMS / "swarm" / "c25"
for p in (str(FILMS), str(C25)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as w  # noqa: E402
from kit import Ink, FPS, clamp, lerp, ramp, smooth, ease  # noqa: E402

SECONDS = 34.6
CAPTIONS = [
    (24.4, 26.9, "A trout, and the trout think it is a bird in a bottle."),
    (27.0, 29.6, "Panic."),
    (32.0, 34.6, "By panicking."),
]

TONE = "ochre"
HAIR = "short"
W, H = 960, 540

# ------------------------------------------------------------------ the desktop (a picture bigger than the frame)
SZ = (1216, 1568)                       # the sheet, in desktop pixels
DW, DH = 2500, 2100                     # the desk top
PX, PY = 880, 250                       # the sheet's top-left corner on it
SLIP = (470, 700)                       # the slip, left of the sheet
SLIP_S, SLIP_A = 2.2, -5.0
CLUE = "Diner Trout wearing inverted fishbowl"
XH = 17.0                               # the pilot's x-height


def B(name, page=1):
    return P.where(page, name, SZ)


def D(x, y):
    """page px -> desktop px"""
    return (PX + x, PY + y)


RING = B("ring.in")
RCX, RCY = (RING[0] + RING[2]) / 2, (RING[1] + RING[3]) / 2
RR = (RING[2] - RING[0]) / 2


def UP(u, v):
    """ring units (the drawing's own: centre 0,0, inner radius 1) -> page px"""
    return (RCX + u * RR, RCY + v * RR)


# ------------------------------------------------------------------ the drawing, part by part (traces 2 to 5)
def _strokes(group, idx=None):
    ss = [s for s in w.PILOT_STROKES if s["group"] == group]
    return [ss[i] for i in idx] if idx is not None else ss


# (name, strokes, graphite weight, width) in the order the photograph suggests: everything light first, the fish last
PARTS = {
    "bowl": (_strokes("bowl"), 0.42, 1.7),
    "body": (_strokes("body"), 0.6, 1.9),
    "arms": (_strokes("arms", [3, 0, 1]), 0.55, 1.8),           # the faint stub on the left, then the arm and the lump
    "legs": (_strokes("legs"), 0.62, 1.9),
    "lowtail": (_strokes("arms", [2]), 0.5, 1.8),               # the small scalloped tail low on the right, as on the slip
    "fish": (_strokes("fish"), 1.3, 2.9),
    "tail": (_strokes("tail"), 1.3, 2.8),
    "fin_mouth": (_strokes("fin_mouth"), 1.42, 2.9),
}
DRAWN = {
    "bowl": [(3.8, 0.0), (5.3, 1.0)],
    "body": [(5.36, 0.0), (6.1, 1.0)],
    "arms": [(6.14, 0.0), (6.66, 1.0)],
    "legs": [(6.7, 0.0), (7.2, 1.0)],
    "lowtail": [(7.26, 0.0), (7.8, 1.0)],
    "fish": [(13.2, 0.0), (14.4, 1.0)],
    "tail": [(14.44, 0.0), (14.9, 1.0)],
    "fin_mouth": [(14.94, 0.0), (15.5, 1.0)],
}
DRAW_WIN = [(g, k[0][0], k[-1][0]) for g, k in DRAWN.items()]
_PART_PTS = {g: [[UP(u, v) for u, v in s["pts"]] for s in ss] for g, (ss, _, _) in PARTS.items()}
_PART_LEN = {g: [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(ln, ln[1:])) + 6 for ln in lns] for g, lns in _PART_PTS.items()}


def _part_upto(g, f):
    """(the polylines of part g drawn by fraction f, tip x, tip y, pencil down?)"""
    lns, L = _PART_PTS[g], _PART_LEN[g]
    if f <= 0:
        return [], lns[0][0][0], lns[0][0][1], False
    tt, done = f * sum(L), []
    for ln, l in zip(lns, L):
        if tt >= l:
            done.append(ln)
            tt -= l
            continue
        n = max(1, int(round(tt / (l - 6) * (len(ln) - 1))))
        if n >= len(ln) - 1:                             # the little beat while the point lifts to the next stroke
            done.append(ln)
            return done, ln[-1][0], ln[-1][1], False
        done.append(ln[:n + 1])
        return done, ln[n][0], ln[n][1], True
    return done, lns[-1][-1][0], lns[-1][-1][1], False


def _draw_part(img, g, f):
    done, _, _, _ = _part_upto(g, f)
    if done:
        P.graphite(img, done, PARTS[g][2], PARTS[g][1], 25 + len(g))


# ------------------------------------------------------------------ what gets written, and when
class Act:
    tip = None

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1

    def u(self, t):
        return ramp(t, self.t0, self.t1)


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
    """Pencil polylines drawn in order (the going-over of letters already there; the flattened last letter)."""
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


def _go_over(lines, passes, seed, jit=1.0):
    rs = random.Random(seed)
    out = []
    for _ in range(passes):
        for ln in lines:
            dx, dy = rs.uniform(-jit, jit), rs.uniform(-jit, jit)
            out.append([(x + dx + rs.uniform(-0.4, 0.4), y + dy + rs.uniform(-0.4, 0.4)) for x, y in ln])
    return out


NAME = B("name.line")
A11, A12, A21, A31 = B("a1.1"), B("a1.2"), B("a2.1"), B("a3.1")
Q1, Q2, Q3 = B("q1"), B("q2"), B("q3")
RX0, RX1 = A11[0], A11[2]               # the printed rule, end to end
RW = RX1 - RX0
QM1, QM2 = (497, Q1[3] + 8), (700, Q1[3] + 8)          # under the stem's two question marks
ONE_A, ONE_B = (182, Q2[3] + 8), (282, Q2[3] + 8)      # under "one thing" in the second stem
PLATE_B = (700, 606)                                   # page 2: under the capital B of the plate "Bird in a bottle"


def _sl0(seed, text):
    """The slant people.write_plan will give this text with this seed (its own first four draws)."""
    rs = random.Random(seed * 7919 + len(text) * 131 + sum(ord(c) * (i + 1) for i, c in enumerate(text)))
    rs.uniform(0, 1), rs.uniform(0, 1), rs.uniform(0, 1)
    return rs.uniform(-0.03, 0.10)


def _seed(text, want=0.03, seeds=range(250, 260)):
    """One hand down the page: M.'s seed (250 to 259) whose slant for this text is nearest `want`."""
    return min(seeds, key=lambda k: abs(_sl0(k, text) - want))


def _at(t0, t1, x, box, text, weight=1.0, size=XH, dy=0.0, want=0.03):
    """A Write whose first stroke starts at page x on the line `box`."""
    sd = _seed(text, want)
    b = (x, box[1] + dy, box[2] + 400, box[3] + dy)
    pl = P.write_plan(b, text, sd, size)
    x0 = min(p[0] for ln in pl.strokes for p in ln)
    return Write(t0, t1, (x + (x - x0), b[1], b[2], b[3]), text, sd, weight, size)


def _xmax(a):
    return max(p[0] for ln in a.plan.strokes for p in ln)


def _build():
    acts = []
    # P1: the name. One wide open capital, light and slanted, and no more (trace 1).
    m = _at(0.8, 1.8, NAME[0] + 26, NAME, "M", 0.7, XH * 1.05, want=0.10)
    acts.append(m)
    # P9: line 1 in two goes. "a trout" stands a little apart; "and the" smaller and tighter; no "is"; the last
    # "a" a low squiggle flattened against the end of the rule (traces 7, 8, 9).
    a = _at(16.8, 17.7, RX0 + 0.125 * RW, A11, "a trout")
    b = _at(18.4, 18.9, RX0 + 0.315 * RW, A11, "and the", 1.0, XH * 0.8, dy=1)
    c = _at(18.95, 19.4, RX0 + 0.5 * RW, A11, "trout")
    d = _at(19.45, 19.92, RX0 + 0.665 * RW, A11, "think")
    e = _at(19.97, 20.14, RX0 + 0.83 * RW, A11, "it")
    y = A11[3] - 0.09 * (A11[3] - A11[1]) - 3
    x = RX0 + 0.925 * RW
    sq = Lines(20.2, 20.38, [[(x, y - 4), (x + 9, y - 8), (x + 20, y - 6), (x + 29, y - 1), (x + 41, y - 2), (x + 52, y - 6), (x + 60, y - 5)]],
               0.95, 2.6, 251)
    acts += [a, b, c, d, e, sq]
    # P11: "Bird in a bottle." The plate's capital B, gone over; the letters after it crowded; the b a dark knot.
    Bc = _at(21.7, 22.1, RX0 + 0.1 * RW, A12, "B", 1.0, XH * 0.94, dy=2)
    Bo = Lines(22.12, 22.58, _go_over(Bc.plan.strokes, 1, 3, 1.3), 1.4, 3.4, 252)
    ird = _at(22.62, 23.38, _xmax(Bc) + 0.3 * XH, A12, "ird in a", 1.0, XH * 0.9, dy=2)
    bb = _at(23.42, 23.56, _xmax(ird) + 0.9 * XH, A12, "b", 1.0, XH * 0.94, dy=2)
    bo = Lines(23.57, 23.8, _go_over(bb.plan.strokes, 2, 4, 1.1), 1.4, 3.3, 253)
    ot = _at(23.83, 24.32, _xmax(bb) + 0.25 * XH, A12, "ottle.", 1.0, XH * 0.94, dy=2)
    acts += [Bc, Bo, ird, bb, bo, ot]
    # P12: one thing: one word, a quarter of the way in, bigger (trace 12).
    pn = _at(25.4, 26.74, RX0 + 0.245 * RW, A21, "panit", 1.0, XH * 1.3)
    acts.append(pn)
    # P13: "by" at the very start of the rule, then gone over, and over again, the y's tail dragged under the rule;
    # then his own word from the line above with "ing" on it, lighter and quick (traces 11, 13).
    by = _at(28.8, 29.58, RX0 + 5, A31, "by", 1.05, XH * 1.3)
    st = by.plan.strokes
    stem = [(px - 5, py - 7) for px, py in st[0]]
    ex, ey = max((p for ln in st for p in ln), key=lambda q: q[1])
    drag = [(ex + 2, ey - 3), (ex - 4, ey + 6), (ex - 15, ey + 11), (ex - 30, ey + 12)]
    g1 = Lines(29.64, 30.1, [stem] + _go_over(st, 1, 5, 1.5), 1.4, 3.6, 254)
    g2 = Lines(30.14, 30.58, _go_over(st, 1, 6, 1.8) + [drag], 1.45, 3.8, 255)
    pg = _at(31.12, 31.96, _xmax(by) + 1.1 * XH, A31, "paniting", 0.86, XH * 1.02)
    acts += [by, g1, g2, pg]
    acts.sort(key=lambda z: z.t0)
    return acts, dict(m=m, a=a, e=e, sq=sq, Bc=Bc, ot=ot, pn=pn, by=by, pg=pg)


ACTS, _L = _build()

_page_cache = {}


def page1(t):
    """The pilot's page as it stands at film time t: a fresh PIL image, SZ = 1216 x 1568 (use P.where(1, name, SZ))."""
    key = (tuple(i for i, a in enumerate(ACTS) if t >= a.t1), tuple(g for g, t0, t1 in DRAW_WIN if t >= t1))
    if key not in _page_cache:
        if len(_page_cache) > 6:
            _page_cache.clear()
        img = P.sheet(SZ, page=1, porthole=25)
        for g, t0, t1 in DRAW_WIN:
            if t >= t1:
                _draw_part(img, g, 1.0)
        for a in ACTS:
            if a.t1 <= t:
                a.draw(img, 1.0)
        _page_cache[key] = img
    img = _page_cache[key].copy()
    for g, t0, t1 in DRAW_WIN:
        if t0 < t < t1:
            _draw_part(img, g, cam.key(t, DRAWN[g], "linear"))
    for a in ACTS:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    return img


_page2 = None


def _back():
    global _page2
    if _page2 is None:
        _page2 = P.sheet(SZ, page=2, porthole=25)          # print only: nobody has written there yet
    return _page2


# ------------------------------------------------------------------ where the pencil point is (page px)
OVER_BOWL = UP(-0.2, -0.36)
AWAY = (RCX + 560, RCY + 520)
GROOVE = (PX + 430, 88)                                # desktop px: where the pencil ends up lying
_E = {k: v.plan.end if isinstance(v, Write) else v.lines[-1][-1] for k, v in _L.items()}
_S = {k: v.plan.start if isinstance(v, Write) else v.lines[0][0] for k, v in _L.items()}
A3_START = (RX0 + 14, A31[3] - 8)
FLIP = (20.4, 20.64, 20.86, 21.2, 21.4, 21.6)            # front going, back coming, held on the plates, and the same back
LAID = 33.2                                            # the pencil is in the groove from here; the hand is empty
AIR = [  # (t, (x, y) page px, lift)
    (0.0, (NAME[0] + 150, NAME[3] + 40), 22), (0.62, (_S["m"][0] + 8, _S["m"][1] - 4), 14),
    (1.96, (NAME[0] + 150, NAME[3] + 70), 18),                                     # off the name line at once
    (2.5, (OVER_BOWL[0] + 40, OVER_BOWL[1] + 30), 18), (3.62, (OVER_BOWL[0] + 40, OVER_BOWL[1] + 30), 18),   # over the empty ring
    (7.92, OVER_BOWL, 16), (8.04, OVER_BOWL, 16), (8.5, AWAY, 40),                 # lifts, stays over the bowl; then out of the way
    (12.7, AWAY, 40), (13.14, (UP(-0.5, -0.12)[0], UP(-0.5, -0.12)[1]), 12),       # and is back when we are
    (15.62, UP(0.2, -0.12), 18), (15.8, UP(0.2, -0.12), 18),                       # the hand lifts; hold
    (16.06, (150, Q1[3] + 12), 8), (16.5, QM1, 3), (16.72, QM1, 3),                # along the printed stem: stops under the first ?
    (17.8, (_E["a"][0] + 12, _E["a"][1] - 4), 10),
    (18.02, QM2, 3), (18.26, QM2, 3),                                              # back up: the SECOND question
    (20.42, (_E["sq"][0] + 6, _E["sq"][1] - 4), 14),
    (20.5, (900, 1000), 46), (20.8, (860, 760), 46),                              # clear of the sheet while it turns
    (20.98, PLATE_B, 3), (21.2, PLATE_B, 3),                                      # the point under the plate's capital B
    (21.3, (760, 800), 46), (21.5, (500, 1010), 40),
    (24.42, (_E["ot"][0] + 10, _E["ot"][1] - 4), 12),
    (24.66, ONE_A, 3), (25.04, ONE_B, 3), (25.24, ONE_B, 3),                       # the point runs under "one thing" and stops
    (26.84, (_E["pn"][0] + 14, _E["pn"][1] - 6), 14),
    (27.0, A3_START, 16), (28.7, A3_START, 16),                                    # stuck: over the left end of the third rule
    (30.66, (_E["by"][0] + 10, _E["by"][1] - 8), 10),
    (30.86, (_S["pn"][0] + 30, A21[3] + 9), 3), (31.02, (_S["pn"][0] + 30, A21[3] + 9), 3),   # up one answer: under his own "panit"
    (32.1, (_E["pg"][0] + 16, _E["pg"][1] - 6), 14), (32.3, (_E["pg"][0] + 16, _E["pg"][1] - 6), 14),
    (LAID - 0.02, (GROOVE[0] - PX + 4, GROOVE[1] - PY + 4), 4),                    # up the page to the groove: the pencil is laid down
    (LAID, (GROOVE[0] - PX + 150, GROOVE[1] - PY + 200), 6),
    (34.0, (SZ[0] + 60, 760), 0),                                                  # the empty hand comes to rest beside the sheet
]


def _pen_keys():
    keys = []
    for a in ACTS:
        keys += [(a.t0, a.tip(0.0)[:2] + (7,)), (a.t1, a.tip(1.0)[:2] + (7,))]
    for g, t0, t1 in DRAW_WIN:
        keys += [(t0, _part_upto(g, 0.0)[1:3] + (7,)), (t1, _part_upto(g, 1.0)[1:3] + (7,))]
    keys += [(tt, tuple(p) + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    return keys


PEN_KEYS = _pen_keys()


def _pen(t):
    """(x, y, lift, pose) of the pencil point (or the palm of the empty hand) on the page at t."""
    if t >= LAID:
        x, y, l = cam.key(t, PEN_KEYS, "smooth")
        return x, y, l, "hold"
    for a in ACTS:
        if a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return x, y, (0 if down else 5), "write"
    for g, t0, t1 in DRAW_WIN:
        if t0 <= t < t1:
            _, x, y, down = _part_upto(g, cam.key(t, DRAWN[g], "linear"))
            return x, y, (0 if down else 5), "write"
    x, y, l = cam.key(t, PEN_KEYS, "smooth")
    return x, y, l, ("hover" if l >= 15 else "write")


# stopped: nothing moves (the hand's own time is held, and the camera's drift with it)
STILL = [(15.64, 15.8), (27.0, 28.76)]


def _held(t):
    for a, b in STILL:
        if a <= t < b:
            return a
    return None


# ------------------------------------------------------------------ the camera at the desk
# (deg, horizon, zoom, look x, look y [desktop px], at x, at y [screen px], head drop)
SCX, SCY = PX + SZ[0] / 2, PY + SZ[1] / 2
_M = P.Tm(*SLIP) @ P.Rm(SLIP_A) @ P.Sm(SLIP_S)
SLIP_PIC = P.apply(_M, (-62, -6))
TOP = (0, 0.5, 0.66, PX + 470, PY + 330, 480, 270, 330)
SEAT = (62, 0.36, 0.50, SCX - 170, SCY - 40, 480, 196, 0)
SLIPSHOT = (40, 0.36, 1.75, SLIP_PIC[0] + 90, SLIP_PIC[1] + 10, 480, 262, 430)
RINGSHOT = (50, 0.36, 1.45, PX + RCX + 20, PY + RCY - 20, 450, 236, 300)
RING2 = (48, 0.36, 1.95, PX + RCX + 16, PY + RCY - 26, 450, 240, 420)       # the slow dolly towards the ring
RING3 = (47, 0.36, 2.2, PX + RCX + 10, PY + RCY - 40, 450, 240, 430)        # and the slight push while the fish goes on


def _close(px, py, sx=440, sy=290, zoom=1.2, deg=38):
    return (deg, 0.36, zoom, PX + px, PY + py, sx, sy, 430)


C_Q1 = _close(470, Q1[3] + 18, 470, 250, 0.88)
C_A1 = _close(330, A11[3] - 12, 400, 286, 0.9)
C_A1R = _close(900, A11[3] - 12, 500, 286, 0.9)
C_PLATE = _close(860, 520, 470, 262, 1.7, 34)
C_A12 = _close(360, A12[3] - 12, 380, 330, 0.9)
C_23 = _close(400, 1236, 450, 262, 0.8)                # the second and third questions together: held from 25.0 to 32.0
C_23UP = _close(400, 1214, 450, 262, 0.8)
WHOLE = (20, 0.47, 0.31, SCX - 40, SCY + 10, 480, 246, 430)       # the third answer clears the caption band
CAMKEYS = [
    (0.0, TOP),                                         # flat above the printed sheet: the number, the clue
    (0.3, TOP),
    (2.6, SEAT, "smoother"),                            # sinking back into the seat
    (2.66, SEAT),
    (3.02, SLIPSHOT),                                   # eyes to the slip ...
    (3.3, SLIPSHOT),
    (3.8, RINGSHOT),                                    # ... and back to the empty ring
    (4.0, RINGSHOT),
    (8.0, RING2, "linear"),                             # the slow dolly while the light drawing is made
    (14.2, RING2),
    (15.5, RING3),                                      # a slight push
    (15.8, RING3),
    (16.24, C_Q1, "hold"),                              # (eyes down the page to the first question: see frame())
    (16.66, C_Q1),
    (17.0, C_A1),
    (18.3, C_A1),
    (20.3, C_A1R, "linear"),                            # tracking right with the pencil
    (20.42, C_A1R),
    (20.86, C_PLATE),                                   # the sheet turns over: the trout's two plates
    (21.2, C_PLATE),
    (21.62, C_A12),                                     # and back, on the second rule
    (24.4, C_A12),
    (25.0, C_23),                                       # down one question
    (30.62, C_23),
    (30.9, C_23UP),                                     # the eye goes up to "panit" with the point
    (31.04, C_23UP),
    (31.3, C_23),
    (32.0, C_23),
    (33.7, WHOLE, "smoother"),                          # up, to nearly above: the whole front
    (34.6, WHOLE),
]
SHAKE = [(0.0, 0.0), (2.6, 2.0), (15.5, 2.0), (15.64, 0.0), (15.8, 0.0), (16.0, 2.0), (26.8, 2.0), (27.0, 0.0), (28.76, 0.0),
         (29.0, 2.0), (32.0, 2.0), (33.7, 0.6), (34.6, 0.6)]
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
_slip_im = None


def _slip_pic():
    """The slip's small picture, handmade from the c25 world as the deck picture has it: the trout in its upside-down
    bowl walking through the lock, tail low on the right."""
    global _slip_im
    if _slip_im is None:
        ink = Ink(1.0, 24)
        w.seat_backdrop(ink, 1.0, calm=True)
        w.walker(ink, 492, 448, 330, step=0.0, water=0.86)
        _slip_im = ink.img.convert("RGB").crop((262, 66, 702, 506))
    return _slip_im


def _desk_base(sheet):
    if sheet not in _base:
        im = Image.new("RGB", (DW, DH), P.DESK)
        P.desk(im)
        pic = _slip_pic()
        P.slip(im, SLIP[0], SLIP[1], 25, CLUE, SLIP_S, SLIP_A, picture=pic)
        n = int(108 * SLIP_S)                           # the picture again at the slip's own size, so it is sharp close to
        big = pic.resize((n, n), Image.LANCZOS).convert("RGBA").rotate(-SLIP_A, Image.BICUBIC, expand=True)
        im.paste(big, (int(SLIP_PIC[0] - big.size[0] / 2), int(SLIP_PIC[1] - big.size[1] / 2)), big)
        if sheet:
            P.lay(im, P.sheet(SZ, page=1, porthole=25), SCX, SCY)
        _base[sheet] = im.convert("RGBA")
    return _base[sheet]


def _turn_deg(t):
    """How far the sheet has been turned over: 0 front up, 180 back up, 360 front up again."""
    a, b, c, d, e, f = FLIP
    return cam.key(t, [(a, 0.0), (b, 90.0, "in"), (c, 180.0, "out"), (d, 180.0), (e, 270.0, "in"), (f, 360.0, "out")])


def _turned(im, pg, deg):
    """The sheet being turned over on the desk about its long middle: one edge comes up towards the lens (and so looks
    longer), the sheet narrows to its own thickness, and the other side comes down."""
    r = math.radians(deg)
    cs, sn = math.cos(r), math.sin(r)
    hw, hh = SZ[0] / 2 * max(abs(cs), 0.006), SZ[1] / 2
    up = 0.13 * abs(sn)                                  # the raised edge is nearer the eye
    lft, rgt = (1 + up, 1 - 0.5 * up) if (sn > 0) == (cs > 0) else (1 - 0.5 * up, 1 + up)
    rise = 70 * abs(sn)                                  # and the whole sheet is off the desk a little
    cx, cy = SCX, SCY - rise * 0.35
    quad = np.float32([(cx - hw, cy - hh * lft), (cx + hw, cy - hh * rgt), (cx + hw, cy + hh * rgt), (cx - hw, cy + hh * lft)])
    x0, y0 = int(quad[:, 0].min()) - 60, int(quad[:, 1].min()) - 60
    x1, y1 = int(quad[:, 0].max()) + 90, int(quad[:, 1].max()) + 110
    src = np.float32([(0, 0), (SZ[0], 0), (SZ[0], SZ[1]), (0, SZ[1])])
    Mx = cv2.getPerspectiveTransform(src, quad - np.float32([x0, y0]))
    arr = np.asarray(pg.convert("RGB"), np.float32) * (1.0 - 0.22 * abs(sn))      # it turns out of the lamp
    out = cv2.warpPerspective(arr.astype(np.uint8), Mx, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA if hw < 300 else cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.full((SZ[1], SZ[0]), 255, np.uint8), Mx, (x1 - x0, y1 - y0))
    sh = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(10 + 0.3 * rise))
    off = (int(10 + 0.7 * rise), int(12 + 0.9 * rise))
    im.paste((30, 22, 16), (x0 + off[0], y0 + off[1]), sh.point(lambda v: int(v * 0.42)))
    im.paste(Image.fromarray(out), (x0, y0), Image.fromarray(mask))


def _desktop(t):
    deg = _turn_deg(t)
    if deg in (0.0, 360.0):
        im = _desk_base(True).copy()
        im.paste(page1(t), (PX, PY))
    elif deg == 180.0:
        im = _desk_base(True).copy()
        im.paste(_back(), (PX, PY))
    else:
        im = _desk_base(False).copy()
        _turned(im, page1(t) if math.cos(math.radians(deg)) > 0 else _back(), deg)
    if t >= LAID:
        P.pencil(im, GROOVE[0], GROOVE[1], 0, scale=1.25)
    return im


# ------------------------------------------------------------------ the hands and the head
def _hand_scale(c, dx, dy):
    return clamp(1.25 * _mag(c, dx, dy), 0.42, 2.2)


def _right_hand(fr, c, t, pen=None):
    px, py, lift, pose = pen or _pen(t)
    hold = _held(t)
    ht = t if hold is None else hold
    dx, dy = D(px, py)
    s = _hand_scale(c, dx, dy)
    x, y = _tp(c, dx, dy)
    if pose == "hold":
        P.hand(fr, x, y, pose="hold", tone=TONE, scale=s, t=ht, lift=lift * s, arm=70)
        return
    arm = cam.key(t, [(1.9, 58), (2.6, 78), (8.0, 78), (13.0, 46), (15.9, 46), (16.2, 58), (20.4, 58), (20.7, 84), (21.2, 84),
                       (21.5, 58), (32.2, 58), (33.0, 74)])
    P.hand(fr, x, y, pose=pose, tone=TONE, scale=s, t=ht, lift=lift * s, arm=arm)


LREST = (0, 1352)                                    # the left palm, flat, on the sheet's lower left corner


def _left_hand(fr, c, t):
    hold = _held(t)
    ht = t if hold is None else hold
    x, y, lift = cam.key(t, [(0.0, LREST + (0,)), (20.2, LREST + (0,)), (20.42, (-70, 1180, 26)),      # it takes the edge and turns the sheet
                             (21.5, (-70, 1180, 26)), (21.7, LREST + (0,))])
    dx, dy = D(x, y)
    s = 0.74 * _hand_scale(c, dx, dy)
    P.hand(fr, *_tp(c, dx, dy), pose="hold", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=142)


def _head_layer(c, t):
    if c["drop"] >= 400:
        return None
    lay = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    look = ease(t, 2.62, 2.96) - ease(t, 3.32, 3.7)      # to the slip, on the left, and back
    P.head_back(lay, 60 + 700, 60 + 590 + c["drop"], TONE, 1.05, tilt=-6 * look, hair=HAIR, turn=-0.7 * look, t=t)
    return lay


def _desk_frame(t, shot=None, pen=None):
    """The pilot's seat at t: desk, slip, the sheet as written so far, hands, the back of the head. A full 960x540 frame."""
    c = _cam(t, shot)
    fr = cam.tilt(_desktop(t), c["deg"], c["hor"], c["zoom"], 700, c["shift"], bg=(92, 66, 44), shadow=0)
    _left_hand(fr, c, t)
    _right_hand(fr, c, t, pen)
    layers = [(fr, 1.0)]
    head = _head_layer(c, t)
    if head is not None:
        layers.append((head, 0.62))
    # the rack: soft as the eye lands on the slip, sharp; soft as it comes back to the ring, sharp; and down the page
    focus = cam.key(t, [(2.7, 1.0), (2.9, 0.74), (3.12, 1.0), (3.36, 1.0), (3.58, 0.76), (3.84, 1.0)])
    return cam.shoot(layers, zoom=SHOOT_ZOOM, focus=focus, aperture=6, shake=c["shake"], t=t)


# ------------------------------------------------------------------ the thought (inside the drawn ring)
TM = 90                                  # the line layer is this much bigger than the frame all round
TS = 300.0                               # ring units -> the thought's px
T0 = (-0.05, 0.1)                        # this point of the drawing ...
TC = (474, 284)                          # ... sits here in the thought's frame
PALE = (242, 238, 226)
BOWL_C = (w.PILOT_PLACES["bowl"][0], -0.33)             # where the turned-over bowl ends up: on the shoulders
BOWL_UP = (BOWL_C[0], -0.47)                            # where it floats while it is still the right way up
BRX, BRY = 0.4, 0.31
_FISH = [np.asarray(s["pts"], np.float32) for g in ("fish", "tail", "fin_mouth") for s in _strokes(g)]
_FISH_W = [s["weight"] for g in ("fish", "tail", "fin_mouth") for s in _strokes(g)]
_fa = np.concatenate(_FISH)
FISH_C = ((_fa[:, 0].min() + _fa[:, 0].max()) / 2, (_fa[:, 1].min() + _fa[:, 1].max()) / 2)
FISH_S = 0.4                             # how big the fish is while a bowl can still hold it
T_TURN = (10.2, 11.0)
T_LIE = (11.0, 11.8)


def _tpx(a, off=(0.0, 0.0)):
    """ring units (array n x 2) -> the thought layer's px"""
    a = np.asarray(a, np.float32)
    return np.stack([TM + TC[0] + (a[:, 0] - T0[0]) * TS + off[0], TM + TC[1] + (a[:, 1] - T0[1]) * TS + off[1]], 1)


def _gl(lay, pts, width, weight, seed, color=PALE):
    if weight <= 0.03 or len(pts) < 2:
        return
    P.graphite(lay, [[(float(x), float(y)) for x, y in pts]], width, weight, seed, color)


def _bowl_local():
    """A fishbowl in its own units (mouth at the top): the round body, the two lips, the rim."""
    a0 = math.radians(-90 + 36)
    body = [(BRX * math.cos(a0 + k * math.radians(288) / 44), BRY * math.sin(a0 + k * math.radians(288) / 44)) for k in range(45)]
    ym = body[0][1]
    xm = body[0][0]
    lip_r = [body[0], (xm + 0.02, ym - 0.03), (xm + 0.05, ym - 0.05)]
    lip_l = [body[-1], (-xm - 0.02, ym - 0.03), (-xm - 0.05, ym - 0.05)]
    rim = [((xm + 0.05) * math.cos(k * math.pi / 14), ym - 0.05 + 0.026 * math.sin(k * math.pi / 14)) for k in range(29)]
    return [body, lip_r, lip_l, rim]


_BOWL = [np.asarray(s, np.float32) for s in _bowl_local()]


def _rot(a, deg, c=(0.0, 0.0)):
    r = math.radians(deg)
    ca, sa = math.cos(r), math.sin(r)
    x, y = a[:, 0] - c[0], a[:, 1] - c[1]
    return np.stack([c[0] + x * ca - y * sa, c[1] + x * sa + y * ca], 1)


def _thought_lines(t):
    lay = Image.new("RGBA", (W + 2 * TM, H + 2 * TM), (0, 0, 0, 0))
    bob = 3.0 * math.sin(t * 1.6)
    off = (0.0, bob)
    k = 0
    # his own lines, large: the loops he went round and round, and the walking body, standing
    for g, wt, wd in (("bowl", 0.34, 3.2), ("body", 0.62, 4.0), ("arms", 0.56, 3.8), ("lowtail", 0.52, 3.8), ("legs", 0.64, 4.0)):
        for s in PARTS[g][0]:
            _gl(lay, _tpx(s["pts"], off), wd, wt, 40 + k)
            k += 1
    # the fishbowl: the right way up; then it turns over and comes down on the shoulders, mouth down
    turn = ease(t, *T_TURN)
    bc = (lerp(BOWL_UP[0], BOWL_C[0], turn), lerp(BOWL_UP[1], BOWL_C[1], turn) - 0.05 * math.sin(math.pi * turn))
    seen = ease(t, 8.9, 9.5)
    for i, s in enumerate(_BOWL):
        pts = _rot(s, 180.0 * turn) + np.float32(bc)
        _gl(lay, _tpx(pts, off), 4.4, 0.95 * seen, 60 + i)
    # the water in it stays level, and stays in
    wy = bc[1] - 0.46 * BRY
    hw = BRX * 0.86
    slosh = 0.035 * math.sin(math.pi * turn) * math.sin(t * 9.0) + 0.012 * math.sin(t * 2.2)
    for j, (dy, f) in enumerate(((0.0, 1.0), (0.09, 0.34), (0.2, 0.22))):
        n = 22
        ln = [(bc[0] + (-hw * f + (j * 0.07) + 2 * hw * f * q / n),
               wy + dy + slosh * (2 * q / n - 1) + 0.008 * math.sin(q * 1.1 + t * 3.0 + j)) for q in range(n + 1)]
        _gl(lay, _tpx(ln, off), 3.0, (0.6 if j == 0 else 0.4) * seen, 70 + j)
    # the fish: round and round inside the bowl; then too long for it, level across it, nose out one side, tail out the other
    lie = ease(t, *T_LIE)
    ph = math.radians(-90.0 - 172.0 * (t - T_LIE[0])) if t < T_LIE[0] else math.radians(-90.0)
    hx, hy = math.sin(ph), -math.cos(ph)                 # which way it is going
    cx, cy = bc[0] + 0.17 * math.cos(ph), bc[1] + 0.03 + 0.1 * math.sin(ph)
    sx = clamp(-hx * 3.0, -1.0, 1.0)                      # it turns about, as a fish seen from the side does
    if abs(sx) < 0.12:
        sx = 0.12 if sx >= 0 else -0.12
    tilt = -24.0 * hy * (1 if sx > 0 else -1) * (1 - lie)
    sc = lerp(FISH_S, 1.0, lie)
    px, py = lerp(cx, FISH_C[0], lie), lerp(cy, FISH_C[1], lie)
    for i, (st, wt) in enumerate(zip(_FISH, _FISH_W)):
        loc = (st - np.float32(FISH_C)) * np.float32((sx * sc, sc))
        pts = _rot(loc, tilt) + np.float32((px, py))
        _gl(lay, _tpx(pts, off), lerp(3.0, 5.2, lie), seen * lerp(0.7, 0.9 + 0.2 * min(wt, 2.4), lie), 80 + i)
    return lay


_bg_cache = {}


def _thought_bg(t):
    """The water he is picturing it in: the lock's own, grey-green and soft."""
    k = int(t * 12)
    if k not in _bg_cache:
        if len(_bg_cache) > 4:
            _bg_cache.clear()
        ink = Ink(t, int(t * FPS))
        w.river_backdrop(ink, t, calm=True, lines=False)
        im = ink.img.convert("RGB").resize((W + 200, H + 112), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
        _bg_cache[k] = Image.blend(im, Image.new("RGB", im.size, (62, 92, 92)), 0.5)
    return _bg_cache[k]


def _thought(t):
    """Inside the thought: no brass, no tin, no Turkey: only what M. is picturing, in his own pencil line. A full frame."""
    roll = 12.0 * math.sin(math.pi * ramp(t, *T_TURN))    # the camera rolls with the bowl and back
    return cam.shoot([(_thought_bg(t), 3.0), (_thought_lines(t), 1.0)], x=cam.key(t, [(8.0, -26), (13.2, 30)], "linear"),
                     y=cam.key(t, [(8.0, -6), (13.2, 8)], "linear"), zoom=1.0, rot=roll,
                     dolly=cam.key(t, [(8.6, 0.0), (12.6, 0.08)], "linear"), shake=1, t=t, bg=(62, 92, 92))


# ---------------------------------------- the look into a thought while "Bird in a bottle." is written (a picture, never words)
TH_BOTTLE = [(22.4, 0), (22.8, 1), (24.0, 1), (24.4, 0)]
BOTTLE_AT = (744, 150)


def _bottle_inner(t):
    """The river side, looking back: the tin, and its outline redrawn in pencil as a bottle on its side, the bird in it."""
    ink = Ink(t, int(t * FPS))
    c, s = (500, 276), 0.84
    w.river_scene(ink, t, dict(c=c, scale=s), False)
    f = ease(t, 22.7, 23.6)
    w.bottle_lines(ink, c=c, scale=s, f=f, color=(244, 240, 228), width=4, alpha=ease(t, 22.5, 22.8))
    return ink.img.convert("RGB")


# ------------------------------------------------------------------ the film
DIVE_IN = (8.0, 9.0)
DIVE_OUT = (12.2, 13.2)
DOWN = (15.8, 16.24)


def _ring_on_screen(t):
    c = _cam(t)
    return _final(*_tp(c, PX + RCX - 0.2 * RR, PY + RCY - 0.3 * RR))        # the middle of the empty bowl


def frame(t):
    """The picture at scene time t, 960 x 540 RGB (no badge, no caption)."""
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if DIVE_IN[0] <= t < DIVE_IN[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, ramp(t, *DIVE_IN), spin=40)
    if DIVE_IN[1] <= t < DIVE_OUT[0]:
        return _thought(t)
    if DIVE_OUT[0] <= t < DIVE_OUT[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, 1 - ramp(t, *DIVE_OUT))
    if DOWN[0] <= t < DOWN[1]:                           # eyes down the page, from the ring to the first question
        return cam.whip(_desk_frame(t, RING3), _desk_frame(t, C_Q1), ramp(t, *DOWN), direction=1, axis="y", blur=0.5, gap=0.3)
    fr = _desk_frame(t)
    u = cam.key(t, TH_BOTTLE, "linear")
    if u > 0:
        fr = cam.thought(fr, _bottle_inner(t), BOTTLE_AT[0], BOTTLE_AT[1], 120, u, wobble=5, t=t)
    return fr


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB") if fr.mode != "RGB" else fr)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m25_pilot.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.1, 1.3, 2.5, 3.15, 4.6, 6.4, 7.7, 8.3, 8.7, 9.6, 10.6, 11.2, 12.0, 12.6, 13.0, 14.0,
                                              15.4, 16.5, 17.4, 18.15, 19.3, 20.36, 20.52, 20.7, 21.0, 21.5, 22.3, 23.0, 23.7, 24.3,
                                              25.1, 26.2, 27.5, 28.6, 29.5, 30.5, 30.95, 31.8, 32.8, 34.4]
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
