"""m33 · scene_pilot · the pilot, L., fills in page 1 of Porthole Log 33 (board beats P1 to P7, 0.0 to 32.0 s).

Down into the seat; a look at the slip; the ring filled edge to edge with leaning bars (two never shaded, the middle
two gone over), the small careful fish behind its bar, the jagged lines; the pencil point along the two question
marks; up the page and a dive through the drawn ring into the thought, where her own strokes hang enormous, the
fish is sure for a moment (black card on lit teal) and is let go, and the camera backs out through the round pane
to find it in a hull lying on its side; back up; "A ship that" and, after a lift, "sunk", between the two rules;
"look in the windo w" with a look into the ring where Turkey is seen from OUTSIDE, "trying to" to the end of the
rule and "get out" in the next question's space; the pencil finding those two words on the end of question 3; the
long third answer in one take, off the rule, back and along the bottom of the page to the paper's edge; the full
stop; the hand staying; the left hand taking the sheet's edge.

Seats are full pictures: `_desk_frame(t)` (the desk top laid back by cam.tilt, hands and the back of the head from
people.py), `_thought(t)` (her strokes as a multiplane, then the hull seen through the pane) and `_window_inner(t)`
(the c33 tin's porthole from the river). Moves between them are cam.dive, cam.whip, cam.through_glass and
cam.thought; moves at the desk are one keyframed tilt camera (`_cam`). No move is a cross-fade.

Exposes SECONDS, CAPTIONS, draw(t, ink); and for the other units page1(t): the written sheet at scene time t
(SZ = 1216 x 1568, use P.where(1, name, SZ)); page1(SECONDS) is the page as the pilot left it.

    python3 films/swarm/m33/scene_pilot.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
C33 = FILMS / "swarm" / "c33"
for p in (str(FILMS), str(C33)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402
from kit import Ink, FPS, clamp, lerp, ramp, smooth, ease  # noqa: E402

SECONDS = 32.0
CAPTIONS = [
    (16.6, 19.1, "A ship that sunk."),
    (22.0, 24.6, "Look in the window, trying to get out."),
    (28.6, 32.0, "He could be freaking out, trying to get out, losing air, breathing heavy."),
]

TONE = "teal"
HAIR = "braids"
W, H = 960, 540

# ------------------------------------------------------------------ the desk top (a picture bigger than the frame)
SZ = (1216, 1568)                       # the sheet, in desk-top pixels
K = SZ[0] / 760.0
DW, DH = 2400, 2100                     # the desk top
PX, PY = 442, 250                       # the sheet's top-left corner on it
SLIP = (2010, 800)                      # the slip, to the right of the sheet
SLIP_S, SLIP_A = 2.2, 5.0
CLUE = "Velvet iris frame around culvert bar shadows"
XH = 19.5                               # her x-height: with capitals it fills the gap between the two rules


def B(name):
    return P.where(1, name, SZ)


def D(x, y):
    """page px -> desk-top px"""
    return (PX + x, PY + y)


RING = B("ring.in")
RCX, RCY = (RING[0] + RING[2]) / 2, (RING[1] + RING[3]) / 2
RR = (RING[2] - RING[0]) / 2


def RP(u, v):
    """ring units (centre 0,0, inner radius 1) -> page px"""
    return (RCX + u * RR, RCY + v * RR)


A11, A12, A21, A22, A31, A32 = B("a1.1"), B("a1.2"), B("a2.1"), B("a2.2"), B("a3.1"), B("a3.2")
Q1, Q2, Q3 = B("q1"), B("q2"), B("q3")
NL = B("name.line")
_BLANK = P.sheet(SZ, page=1, porthole=33)


def _stem(box):
    """(first, last) inked column of the printed stem in `box`, read off the printed sheet."""
    a = np.asarray(_BLANK.convert("L"))[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
    cols = np.nonzero((a < 120).any(axis=0))[0]
    return box[0] + float(cols[0]), box[0] + float(cols[-1])


Q1X0, Q1X1 = _stem(Q1)
Q2X0, Q2X1 = _stem(Q2)
Q3X0, Q3X1 = _stem(Q3)
_f = P._inter(700, 20)
_full = "1. Who is outside the glass? What do they think our sub is?"
Q1MID = Q1X0 + (Q1X1 - Q1X0) * _f.getlength("1. Who is outside the glass?") / _f.getlength(_full)


# ------------------------------------------------------------------ what gets put on the page, and when
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


class Path_(Act):
    """Pencil strokes drawn in order, each with its own width and weight, the point lifting between them."""

    def __init__(self, t0, t1, strokes, seed=0, air=0.45, beat=5.0):
        super().__init__(t0, t1)
        self.strokes, self.seed = strokes, seed            # [(pts, width, weight)]
        self.seg, T, prev = [], 0.0, None
        for i, (pts, wd, wt) in enumerate(strokes):
            if prev is not None:
                a = math.hypot(pts[0][0] - prev[0], pts[0][1] - prev[1]) * air + beat
                self.seg.append(("air", T, T + a, prev, pts[0], i))
                T += a
            L = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts, pts[1:])) + 3.0
            self.seg.append(("ink", T, T + L, pts, None, i))
            T += L
            prev = pts[-1]
        self.T = max(T, 1e-6)

    def _upto(self, u):
        if u >= 1:
            return len(self.strokes), None, tuple(self.strokes[-1][0][-1]) + (False,)
        tt = max(u, 0.0) * self.T
        for kind, a, b, p, q, i in self.seg:
            if tt >= b:
                continue
            f = (tt - a) / max(b - a, 1e-6)
            if kind == "air":
                f = f * f * (3 - 2 * f)
                return i, None, (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f, False)
            n = min(len(p) - 1, max(1, int(round(f * (len(p) - 1)))))
            return i, p[:n + 1], (p[n][0], p[n][1], True)
        return len(self.strokes), None, tuple(self.strokes[-1][0][-1]) + (False,)

    def draw(self, img, u):
        if u <= 0:
            return
        n, part, _ = self._upto(u)
        for i, (pts, wd, wt) in enumerate(self.strokes[:n]):
            P.graphite(img, [pts], wd, wt, self.seed + i)
        if part is not None and len(part) > 1:
            pts, wd, wt = self.strokes[n]
            P.graphite(img, [part], wd, wt, self.seed + n)

    def tip(self, u):
        return self._upto(u)[2]


def _smear_weight(alpha):
    """graphite() weight that gives about this opacity (for the side of the lead)."""
    return (alpha - 0.30) / 0.56


def _group(g, scale=None, to=RP, widen=1.0):
    """The class world's traced strokes for one group, as (pts, width, weight) on the page."""
    sc = (RR / 212.0) if scale is None else scale
    out = []
    for s in Wd.PILOT_STROKES:
        if s["group"] != g:
            continue
        pts = [to(u, v) for u, v in s["pts"]]
        if s.get("wide"):
            out.append((pts, s["wide"] * sc * 1.05, _smear_weight(0.13 + 0.42 * s["weight"])))
        else:
            out.append((pts, max(1.7, 2.3 * s["weight"] * sc) * widen, 0.25 + 0.75 * s["weight"]))
    return out


def _again(strokes, seed, jit=1.3, weight=1.25):
    """The same lines gone over once more (never rubbed)."""
    rs = random.Random(seed)
    out = []
    for pts, wd, wt in strokes:
        dx, dy = rs.uniform(-jit, jit), rs.uniform(-jit, jit)
        out.append(([(x + dx + rs.uniform(-0.4, 0.4), y + dy + rs.uniform(-0.4, 0.4)) for x, y in pts], wd, weight))
    return out


def _words(t0, t1, row, items, seed0, gap=0.55):
    """Words set down one by one at their own places. items = [(text, x, weight, x-height, dy)] in page px.
    A word never starts on top of the one before it. Time is shared out by pencil travel."""
    acts, prev_end = [], -1e9
    for i, (text, x, wt, xh, dy) in enumerate(items):
        if isinstance(x, tuple):                        # ("end", X): the word finishes at X
            x = x[1] - P.write_plan((0, row[1] + dy, 2400, row[3] + dy), text, seed0 + i % 5, xh).x_end
        x = max(x, prev_end + gap * xh)
        a = Write(0, 0, (x, row[1] + dy, x + 2400, row[3] + dy), text, seed0 + i % 5, wt, xh)
        prev_end = a.plan.x_end
        acts.append(a)
    air = [0.0] + [0.3 * abs(b.plan.start[0] - a.plan.end[0]) + 10 for a, b in zip(acts, acts[1:])]
    tot = sum(a.plan.T for a in acts) + sum(air)
    tt = t0
    for a, g in zip(acts, air):
        tt += (t1 - t0) * g / tot
        a.t0 = tt
        tt += (t1 - t0) * a.plan.T / tot
        a.t1 = tt
    return acts


def _letter(plan, idx):
    return [s for s, l in zip(plan.strokes, plan.letter) if l == idx]


RX0, RX1 = A12[0], A12[2]               # the printed rule's ends
RW = RX1 - RX0
BOT = (138 * K, 850 * K, 752 * K, 882 * K)            # the bottom row, on no rule


def _build():
    acts, mark = [], {}
    # ---- P2: the ring is filled. Bars left to right, 2 and 7 only outlined; the middle two gone over; fish; lines.
    bars = [_group("bar%d" % k) for k in range(1, 10)]
    paths = [Path_(0, 0, s, 400 + 20 * k, air=0.22, beat=3.0) for k, s in enumerate(bars)]
    tot = sum(p.T for p in paths) + 40.0 * 8
    tt = 2.8
    for p in paths:
        p.t0 = tt
        tt += (5.42 - 2.8) * p.T / tot
        p.t1 = tt
        tt += (5.42 - 2.8) * 40.0 / tot
    acts += paths
    acts.append(Path_(5.44, 5.78, _again(bars[3][:2], 1) + _again(bars[4][:2], 2), 600, air=0.22, beat=3.0))
    acts.append(Path_(6.12, 6.98, _group("fish", widen=1.1), 620, air=0.5, beat=9.0))
    acts.append(Path_(7.0, 7.2, _group("spots"), 660, air=0.3, beat=6.0))
    acts.append(Path_(7.24, 8.34, _group("cracks"), 680, air=0.3, beat=8.0))

    # ---- P5: line 1, between the two rules (a1.1 stays empty). "sunk" after a lift, lighter, a wider gap.
    L1 = _words(14.8, 15.9, A12, [("A", RX0 + 0.035 * RW, 1.1, XH, 0), ("ship", RX0 + 0.126 * RW, 1.1, XH, 0),
                                  ("that", RX0 + 0.24 * RW, 1.1, XH, 0)], 330)
    sunk = Write(16.2, 16.58, (L1[-1].plan.x_end + 0.72 * XH + 20 * K, A12[1], RX1, A12[3]), "sunk", 333, 0.75, XH)
    acts += L1 + [sunk]
    mark["sunk"] = sunk

    # ---- P6: line 2 carries on from the stem; "windo", the d gone over, a small raised w; fading; "get out" below.
    L2a = _words(17.1, 18.0, A22, [("look", RX0 + 0.035 * RW, 1.1, XH, 0), ("in", RX0 + 0.145 * RW, 1.1, XH, 0),
                                   ("the", RX0 + 0.256 * RW, 0.95, XH, 0)], 334)
    win = Write(18.0, 18.4, (RX0 + 0.395 * RW, A22[1], RX1, A22[3]), "win", 337, 0.85, XH)
    do = Write(18.95, 19.3, (win.plan.x_end - 0.2 * XH, A22[1], RX1, A22[3]), "do", 338, 0.85, XH)
    d = _letter(do.plan, 0)
    dbot = max(d[-1], key=lambda p: p[1])
    over = [(ln, 2.9, 1.0) for ln in d] + [([dbot, (dbot[0] + 1.5, dbot[1] + 6), (dbot[0] + 4, dbot[1] + 11)], 2.7, 0.9)]
    dgo = Path_(19.5, 19.64, _again(over[:-1], 4, 1.0, 1.0) + over[-1:], 700, air=0.3, beat=2.0)
    w = Write(19.68, 19.8, (do.plan.x_end + 10 * K, A22[1] - 5 * K, RX1, A22[3] - 5 * K), "w", 339, 0.8, XH * 0.7)
    L2b = _words(19.86, 20.8, A22, [("trying", RX0 + 0.677 * RW, 0.65, XH * 1.04, 0), ("to", RX0 + 0.945 * RW, 0.6, XH * 1.06, 0)], 331)
    gx = Q3X1 + 14 * K
    G2 = _words(21.2, 21.95, (gx, 770 * K, gx + 400, 797 * K), [("get", gx, 0.6, XH * 1.04, 0), ("out", gx + 7.4 * XH, 0.6, XH * 1.04, 0)], 335)
    acts += L2a + [win, do, dgo, w] + L2b + G2
    mark.update(win=win, do=do, w=w, to2=L2b[-1], get2=G2[0], out2=G2[-1])

    # ---- P7: line 3, the longest thing on the sheet: off the rule, back, along the bottom to the paper's edge.
    L3 = _words(22.85, 25.4, A32, [("He", 92 * K, 1.1, XH, 0), ("could", RX0 + 0.165 * RW, 1.1, XH, 0),
                                   ("be", RX0 + 0.30 * RW, 0.9, XH * 1.04, 0), ("freaking", RX0 + 0.365 * RW, 0.9, XH * 1.04, 0),
                                   ("out", RX0 + 0.66 * RW, 0.7, XH * 1.08, 0), ("trying", RX0 + 0.79 * RW, 0.7, XH * 1.08, 0),
                                   ("to", ("end", RX1 + 19), 0.7, XH * 1.08, -2)], 330)
    BH = XH * 1.2
    L4 = _words(25.7, 28.0, BOT, [("get", 236, 0.6, BH, 0), ("out", 352, 0.6, BH, 3), ("losing", 476, 0.55, BH, 7),
                                  ("air", 672, 0.55, BH, 11), ("breating", 790, 0.55, BH, 15)], 335, gap=0.9)
    hw = P.write_plan((0, 0, 2400, 40), "heavy", 332, BH).x_end
    hv = Write(28.0, 28.5, (SZ[0] - 16 - 9 - hw, BOT[1] + 15 + 12 * K, SZ[0] + 400, BOT[3] + 15 + 12 * K), "heavy", 332, 0.55, BH)
    sx, sy = hv.plan.x_end + 2, max(p[1] for s in hv.plan.strokes[:3] for p in s) - 1
    stop = Path_(28.5, 28.6, [([(sx, sy), (sx + 1.6, sy + 0.8), (sx + 0.4, sy + 1.6), (sx - 0.6, sy + 0.4), (sx + 1.0, sy + 0.2)], 4.4, 1.3)], 720)
    acts += L3 + L4 + [hv, stop]
    mark.update(he=L3[0], to3=L3[-1], get3=L4[0], breating=L4[-1], heavy=hv, stop=(sx, sy))
    acts.sort(key=lambda a: a.t1)
    return acts, mark


ACTS, MARK = _build()

_done_cache = {}


def _page_done(n):
    """The sheet with the first n acts (by finishing time) complete."""
    if n in _done_cache:
        return _done_cache[n]
    lower = [k for k in _done_cache if k < n]
    k0 = max(lower) if lower else 0
    img = (_done_cache[k0] if lower else _BLANK).copy()
    for a in ACTS[k0:n]:
        a.draw(img, 1.0)
    if len(_done_cache) > 10:
        for k in sorted(_done_cache)[:-4]:
            del _done_cache[k]
    _done_cache[n] = img
    return img


def page1(t):
    """The pilot's page as it stands at scene time t: a fresh PIL image, SZ = 1216 x 1568."""
    n = sum(1 for a in ACTS if a.t1 <= t)
    img = _page_done(n).copy()
    for a in ACTS[n:]:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    return img


# ------------------------------------------------------------------ where the pencil point is (page px)
OVER_RING = RP(0.45, 0.35)
RINGSIDE = RP(1.42, 0.95)                               # clear of the ring while the eyes are in it
QY = lambda q: q[3] + 9                                 # noqa: E731   just under a printed stem
_SK = MARK["sunk"].plan
_HV = MARK["stop"]
HANG = (RX1 + 34, A22[3] - 12)                          # off the end of the rule, in the air
REST = (_HV[0] + 5, _HV[1] - 4)
AIR = [  # (t, (x, y) page px, lift)
    (0.0, OVER_RING, 18), (2.62, OVER_RING, 18),
    (5.84, RP(0.72, 0.5), 17), (6.04, RP(0.72, 0.5), 17),                       # held while she looks at the slip again
    (8.6, (Q1X0 + 36, QY(Q1)), 7), (8.84, (Q1MID, QY(Q1)), 6), (8.98, (Q1MID, QY(Q1)), 6),      # the first "?"
    (9.26, (Q1X1, QY(Q1)), 6), (9.46, (Q1X1, QY(Q1)), 6),                                       # the second
    (9.62, (Q1X1 + 20, QY(Q1) + 10), 16), (9.92, RINGSIDE, 18), (14.5, RINGSIDE, 18),
    (14.68, (RX0 + 30, A11[3] - 8), 12),                                         # past the open first line ...
    (15.98, (_SK.start[0] - 10, _SK.start[1] - 6), 13), (16.16, (_SK.start[0] - 10, _SK.start[1] - 6), 13),   # lifts, waits
    (16.84, (Q2X1 - 70, QY(Q2)), 7), (17.02, (Q2X1 - 20, QY(Q2)), 7),            # rests under "does Turkey do?"
    (18.5, (MARK["win"].plan.x_end + 4, A22[3] - 8), 9), (18.9, (MARK["win"].plan.x_end + 4, A22[3] - 8), 9),
    (19.38, (MARK["do"].plan.x_end + 8, A22[3] - 10), 6),                        # back along the word
    (20.9, HANG, 14), (21.14, HANG, 14),                                         # off the end of the rule
    (22.1, (Q3X0 + 40, QY(Q3)), 7), (22.34, (Q3X1 - 6, QY(Q3)), 7), (22.5, (MARK["out2"].plan.x_end + 12, QY(Q3) + 4), 7),
    (22.66, (MARK["out2"].plan.x_end + 12, QY(Q3) + 4), 7),   # along the stem to her own words
    (25.55, (MARK["get3"].plan.start[0] + 200, BOT[1] - 8), 8),
    (28.7, REST, 8), (30.5, REST, 8), (31.1, (REST[0] - 40, REST[1] - 150), 22), (32.0, (REST[0] - 30, REST[1] - 160), 22),
]


def _pen_keys():
    keys = []
    for a in ACTS:
        keys += [(a.t0, a.tip(0.0)[:2] + (5,)), (a.t1, a.tip(1.0)[:2] + (5,))]
    keys += [(tt, tuple(p) + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    return keys


PEN_KEYS = _pen_keys()
_BY_T0 = sorted(ACTS, key=lambda a: a.t0)


def _pen(t):
    """(x, y, lift, pose) of the pencil point on the page at t."""
    for a in _BY_T0:
        if a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return x, y, (0 if down else 5), "write"
    x, y, l = cam.key(t, PEN_KEYS, "smooth")
    return x, y, l, ("hover" if l >= 12.5 else "write")


# stuck: the hand's own time is held and the camera does not shake
STILL = [(15.92, 16.2), (18.42, 18.94), (20.86, 21.18), (22.5, 22.68), (28.62, 30.4)]


def _held(t):
    for a, b in STILL:
        if a <= t < b:
            return a
    return None


# ------------------------------------------------------------------ the camera at the desk
# (deg, horizon, zoom, look x, look y [desk-top px], at x, at y [screen px], head drop)
SCX, SCY = PX + SZ[0] / 2, PY + SZ[1] / 2
TOP = (0, 0.5, 0.80, SCX, PY + 420, 480, 270, 330)
SEAT = (62, 0.36, 0.50, SCX + 75, SCY, 480, 194, 0)
RINGSHOT = (52, 0.36, 1.15, PX + RCX + 40, PY + RCY, 440, 250, 230)
RINGMID = (49, 0.36, 1.42, PX + RCX + 34, PY + RCY + 6, 446, 256, 380)
FISHSHOT = (46, 0.36, 1.72, PX + RCX + 70, PY + RCY + 20, 450, 262, 430)
RINGCLOSE = (46, 0.36, 1.5, PX + RCX + 30, PY + RCY, 450, 262, 430)
RINGDIVE = (50, 0.36, 1.2, PX + RCX + 20, PY + RCY, 452, 258, 430)
_M = P.Tm(*SLIP) @ P.Rm(SLIP_A) @ P.Sm(SLIP_S)
SLIP_PIC = P.apply(_M, (-62, -6))
SLIPSHOT = (44, 0.36, 1.45, SLIP_PIC[0] + 110, SLIP_PIC[1], 480, 250, 430)
SLIPFISH = (40, 0.36, 2.2, SLIP_PIC[0] + 14, SLIP_PIC[1] + 4, 480, 262, 430)


def _close(px, py, sx=440, sy=300, zoom=0.80, deg=38):
    return (deg, 0.36, zoom, PX + px, PY + py, sx, sy, 430)


C_Q1 = _close(Q1X0 + 430, Q1[3] + 16, 430, 262, 0.80)
C_A1 = _close(RX0 + 300, A12[3] - 30, 430, 292, 0.86)
C_A2 = _close(RX0 + 300, A22[3] - 30, 430, 292, 0.86)
C_RL = (50, 0.36, 0.60, PX + RCX + 40, PY + (RCY + A22[3]) / 2 + 60, 470, 262, 430)        # the ring above, line 2 below
C_A2R = _close(RX0 + 0.62 * RW, A22[3] - 30, 430, 292, 0.86)
C_A2E = _close(RX0 + 0.86 * RW, A22[3] - 30, 440, 292, 0.86)
C_GET = _close(Q3X1 + 150, Q3[3] - 20, 440, 290, 0.76)
C_Q3 = _close(Q3X0 + 380, Q3[3] + 2, 430, 280, 0.74)
C_L3A = _close(92 * K + 260, A32[3] - 34, 420, 280, 0.68)
C_L3B = _close(RX1 - 150, A32[3] - 34, 500, 280, 0.68)
C_B0 = _close(MARK["get3"].plan.start[0] + 220, BOT[3] - 50, 420, 270, 0.62)
C_B1 = _close(MARK["breating"].plan.x_end - 200, BOT[3] - 40, 470, 272, 0.62)
C_B2 = _close(SZ[0] - 250, BOT[3] - 30, 500, 272, 0.62)                                       # the paper's edge and the wood
ZONE3 = (44, 0.36, 0.52, PX + SZ[0] / 2 - 40, PY + (Q1[1] + BOT[3]) / 2 + 20, 480, 262, 430)
ZONE3L = (44, 0.36, 0.52, PX + SZ[0] / 2 - 330, PY + (Q1[1] + BOT[3]) / 2 + 20, 480, 262, 430)
WHIP_UP = (9.6, 9.9)
WHIP_L = (25.4, 25.7)
CAMKEYS = [
    (0.0, TOP),                                         # straight down on the desk
    (0.3, TOP),
    (2.0, SEAT, "smoother"),                            # down into the seat
    (2.38, SLIPSHOT),                                   # across to the slip ...
    (2.5, SLIPSHOT),
    (2.84, RINGSHOT),                                   # ... and back to the ring
    (5.78, RINGMID, "linear"),                          # a slow push the long strokes keep leaving
    (5.94, SLIPFISH),                                   # the fish in the slip's picture
    (6.02, SLIPFISH),
    (6.22, FISHSHOT),                                   # small and slow after all that speed
    (7.2, FISHSHOT),
    (8.4, RINGCLOSE),
    (8.86, C_Q1),                                       # down the page to the first question
    (WHIP_UP[1], C_Q1),
    (WHIP_UP[1], RINGDIVE, "hold"),                     # (the whip up the page is cam.whip, in frame())
    (14.5, RINGDIVE),
    (14.92, C_A1),                                      # settles on zone 3
    (16.6, C_A1),
    (17.1, C_A2),                                       # down one question
    (17.62, C_A2),
    (18.0, C_RL),                                       # the eyes go up to the ring
    (19.26, C_RL),
    (19.66, C_A2R),
    (19.9, C_A2R),
    (20.8, C_A2E, "linear"),
    (21.18, C_A2E),
    (21.5, C_GET),
    (22.0, C_GET),
    (22.4, C_Q3),                                       # down to question 3
    (22.68, C_Q3),
    (22.94, C_L3A),
    (WHIP_L[0], C_L3B, "linear"),                       # one take: the page slides left under the point
    (WHIP_L[1], C_B0, "hold"),                          # (the swing back is cam.whip)
    (28.0, C_B1, "linear"),
    (28.6, C_B2),
    (28.95, C_B2),
    (30.3, ZONE3, "smoother"),                          # back to all of zone 3
    (31.2, ZONE3),
    (32.0, ZONE3L, "in"),                               # starting to go with the sheet
]
SHAKE = [(0.0, 0.0), (2.0, 2.5), (9.5, 2.5), (9.9, 1.0), (14.5, 1.0), (15.0, 2.5), (15.88, 2.5), (15.94, 0.0), (16.2, 0.0), (16.4, 2.2),
         (18.3, 2.0), (18.44, 0.0), (18.94, 0.0), (19.2, 2.0), (20.76, 2.0), (20.86, 0.0), (21.18, 0.0), (21.4, 2.0), (22.36, 2.0),
         (22.5, 0.0), (22.68, 0.0), (22.9, 3.0), (28.5, 3.0), (28.62, 0.0), (29.0, 0.0), (29.4, 0.8), (30.4, 0.8), (31.0, 2.0)]
SHOOT_ZOOM = 1.035


def _cam(t, shot=None):
    deg, hor, zoom, lx, ly, ax, ay, drop = shot or cam.key(t, CAMKEYS, "smooth")
    gx, gy = cam.tilt_point(lx, ly, deg, hor, zoom, 700, (0, 0), (DW, DH))
    return dict(deg=deg, hor=hor, zoom=zoom, shift=(ax - gx, ay - gy), drop=drop, shake=cam.key(t, SHAKE, "smooth"))


def _tp(c, dx, dy):
    """desk-top px -> screen px (before the handheld shoot)."""
    return cam.tilt_point(dx, dy, c["deg"], c["hor"], c["zoom"], 700, c["shift"], (DW, DH))


def _mag(c, dx, dy):
    a, b = _tp(c, dx, dy), _tp(c, dx + 20, dy)
    return (b[0] - a[0]) / 20.0


def _final(x, y):
    return (W / 2 + (x - W / 2) * SHOOT_ZOOM, H / 2 + (y - H / 2) * SHOOT_ZOOM)


# ------------------------------------------------------------------ the desk top picture
_base = {}
_SLIP_PIC = None


def _slip_pic():
    """The slip's small picture, handmade: the class film's own stage (black bars, the spotted fish, the stone ring)."""
    global _SLIP_PIC
    if _SLIP_PIC is None:
        ink = Ink(1.3, 31)
        Wd.seat_scene(ink, 1.3, cross=False, fog_level=0.0, notches=8.0)
        c, r = Wd.PORT_C, Wd.RING_OUT + 4
        _SLIP_PIC = ink.img.convert("RGB").crop((c[0] - r, c[1] - r, c[0] + r, c[1] + r))
    return _SLIP_PIC


def _desk_base(sheet):
    if sheet not in _base:
        im = Image.new("RGB", (DW, DH), P.DESK)
        P.desk(im)
        pic = _slip_pic()
        P.slip(im, SLIP[0], SLIP[1], 33, CLUE, SLIP_S, SLIP_A, picture=pic)
        n = int(108 * SLIP_S)                           # the picture again at the slip's own size, so it is sharp close to
        big = pic.resize((n, n), Image.LANCZOS).convert("RGBA").rotate(-SLIP_A, Image.BICUBIC, expand=True)
        im.paste(big, (int(SLIP_PIC[0] - big.size[0] / 2), int(SLIP_PIC[1] - big.size[1] / 2)), big)
        if sheet:
            P.lay(im, _BLANK, SCX, SCY)
        _base[sheet] = im.convert("RGBA")
    return _base[sheet]


def _sheet_dx(t):
    return -80 * ease(t, 31.25, 32.0) ** 2


def _desktop(t):
    dx = _sheet_dx(t)
    pg = page1(t)
    if dx == 0:
        im = _desk_base(True).copy()
        im.paste(pg, (PX, PY))
    else:
        im = _desk_base(False).copy()
        P.lay(im, pg, SCX + dx, SCY, lift=5 * ramp(-dx, 0, 40))
    return im


# ------------------------------------------------------------------ the hands and the head
def _hand_scale(c, dx, dy):
    return clamp(1.26 * _mag(c, dx, dy), 0.45, 1.9)


def _right_hand(fr, c, t):
    px, py, lift, pose = _pen(t)
    hold = _held(t)
    ht = t if hold is None else hold
    dx, dy = D(px + _sheet_dx(t) * ramp(t, 0, 31.0), py)
    s = _hand_scale(c, dx, dy)
    x, y = _tp(c, dx, dy)
    P.hand(fr, x, y, pose=pose, tone=TONE, scale=s, t=ht, lift=lift * s, arm=58)


NAME_REST = (NL[0] + 170, (NL[1] + NL[3]) / 2 + 26)      # her left hand lies on the Pilot line, sleeve across it
EDGE = (10, A22[3] + 40)                                # the sheet's left edge, where she takes it
T_PASS = 31.0


def _left_hand(fr, c, t):
    hold = _held(t)
    ht = t if hold is None else hold
    x, y, lift = cam.key(t, [(0.0, NAME_REST + (0,)), (30.4, NAME_REST + (0,)), (30.7, (NAME_REST[0] - 120, 700, 14)),
                             (T_PASS, (EDGE[0] + 40, EDGE[1], 9)), (T_PASS + 0.12, EDGE + (0,))])
    dx, dy = D(x + _sheet_dx(t), y)
    s = _hand_scale(c, dx, dy)
    if t < T_PASS:
        P.hand(fr, *_tp(c, dx, dy), pose="hold", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=cam.key(t, [(30.4, 153), (T_PASS, 150)]))
    else:
        a, b = _tp(c, dx, dy - 60), _tp(c, dx, dy + 60)
        edge = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        P.hand(fr, *_tp(c, dx, dy), pose="pass", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=150, edge=edge)


def _head_layer(c, t):
    if c["drop"] >= 400:
        return None
    lay = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    look = ease(t, 2.02, 2.36) - ease(t, 2.5, 2.84)                             # to the slip, on her right, and back
    P.head_back(lay, 60 + 800, 60 + 560 + c["drop"], TONE, 1.05, tilt=6 * look, hair=HAIR, turn=0.75 * look, t=t)
    return lay


FOCUS = [(2.06, 1.0), (2.3, 0.70), (2.46, 1.0), (2.56, 1.0), (2.74, 0.72), (2.92, 1.0),
         (5.8, 1.0), (5.9, 0.72), (6.0, 1.0), (6.06, 1.0), (6.16, 0.74), (6.3, 1.0)]


def _desk_frame(t, shot=None):
    """The pilot's seat at t: desk, sheet as written so far, slip, hands, the back of the head. A full 960x540 frame."""
    c = _cam(t, shot)
    fr = cam.tilt(_desktop(t), c["deg"], c["hor"], c["zoom"], 700, c["shift"], bg=(92, 66, 44), shadow=0)
    _left_hand(fr, c, t)
    _right_hand(fr, c, t)
    layers = [(fr, 1.0)]
    head = _head_layer(c, t)
    if head is not None:
        layers.append((head, 0.62))
    return cam.shoot(layers, zoom=SHOOT_ZOOM, focus=cam.key(t, FOCUS), aperture=6, shake=c["shake"], t=t)


def _ring_on_screen(t, shot=None):
    c = _cam(t, shot)
    x, y = _final(*_tp(c, PX + RCX, PY + RCY))
    x1, _ = _final(*_tp(c, PX + RCX + RR, PY + RCY))
    return x, y, x1 - x


# ------------------------------------------------------------------ the thought (inside the drawn ring)
T_IN = (9.9, 10.9)
T_BACK = (12.5, 13.2)                   # backing out through the pane
T_OUT = (13.5, 14.5)
LW, LH = 1500, 1040                     # a stroke layer
T_R = 330.0                             # the ring's radius in there: enormous
PAPER_W = (250, 247, 239)


def TL(u, v):
    return (LW / 2 + u * T_R, LH / 2 + v * T_R)


_static = {}


def _stroke_layer(groups, seed):
    key = tuple(groups)
    if key not in _static:
        lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        for gi, g in enumerate(groups):
            for i, (pts, wd, wt) in enumerate(_group(g, T_R / 212.0, TL)):
                P.graphite(lay, [pts], wd, wt, seed + gi * 40 + i)
        _static[key] = lay
    return _static[key]


_FISH_T = _group("fish", T_R / 212.0, TL, 1.1) + _group("spots", T_R / 212.0, TL)
FISH_C = TL(*Wd.PILOT_PLACES["fish"])


def _fish_layer(t):
    """The fish: her pencil strokes; for a moment black card with its spots punched through; then let go."""
    sure = ease(t, 11.0, 11.3) - ease(t, 11.74, 12.0)
    go = ramp(t, 11.86, 12.6)
    lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    rs = random.Random(12)
    bob = 5 * math.sin(t * 1.9)
    for i, (pts, wd, wt) in enumerate(_FISH_T):
        ang, ox, oy = rs.uniform(-50, 50), rs.uniform(-240, 240), rs.uniform(-150, 190)
        k = smooth(clamp(go * 1.25 - 0.012 * i))
        wgt = wt * (1 - 0.8 * sure) * (1 - 0.9 * k)
        if wgt < 0.04:
            continue
        a = math.radians(ang * k)
        ca, sa = math.cos(a), math.sin(a)
        mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        q = [(mx + (x - mx) * ca - (y - my) * sa + ox * k, my + (x - mx) * sa + (y - my) * ca + oy * k + bob) for x, y in pts]
        P.graphite(lay, [q], wd, wgt, 60 + i)
    if sure > 0.02:
        spr = Wd.shadow_fish_sprite(int(Wd.PILOT_PLACES["fish_len"] * T_R * 0.97), tail=15 * math.sin(t * 5.0), fins=12 * math.sin(t * 5.0 - 1.0))
        spr = spr.rotate(Wd.PILOT_PLACES["fish_angle"], Image.BICUBIC, expand=True)
        if sure < 1:
            spr.putalpha(spr.getchannel("A").point(lambda v: int(v * sure)))
        lay.alpha_composite(spr, (int(FISH_C[0] + 0.07 * T_R - spr.width / 2), int(FISH_C[1] - 0.01 * T_R - spr.height / 2 + bob)))
    return lay, sure


_GLOW = None


def _ground(sure):
    global _GLOW
    if _GLOW is None:
        ink = Ink(0, 0)
        Wd.glow_ground(ink, c=(480, 270), r=int(T_R), cant=0.0)
        _GLOW = (Image.new("RGB", (1160, 652), PAPER_W), ink.img.convert("RGB").resize((1160, 652), Image.BILINEAR))
    if sure <= 0.004:
        return _GLOW[0]
    return Image.blend(_GLOW[0], _GLOW[1], clamp(sure))


def _strokes_world(t):
    """Her own strokes, enormous, on paper-white: the jagged lines nearest, the bars, the fish beyond."""
    fish, sure = _fish_layer(t)
    layers = [(_ground(sure), 4.0), (fish, 2.0), (_stroke_layer(["bar%d" % k for k in range(1, 10)], 100), 1.0),
              (_stroke_layer(["cracks"], 300), 0.6)]
    return cam.shoot(layers,
                     x=cam.key(t, [(9.9, 30), (11.3, 64), (11.8, 64), (12.5, 20), (13.2, 0)]), y=cam.key(t, [(9.9, 10), (11.3, 31), (11.8, 31), (12.5, 8), (13.2, 0)]),
                     zoom=cam.key(t, [(9.9, 0.86), (10.9, 1.0), (11.3, 1.5), (11.8, 1.6), (12.5, 1.05), (13.2, 0.78)]),
                     dolly=cam.key(t, [(10.6, 0.0), (12.5, 0.2, "linear"), (13.2, 0.0)]),
                     focus=cam.key(t, [(10.7, 2.0), (11.8, 2.0), (12.36, 0.6), (12.6, 0.6), (13.1, 1.0)]),
                     aperture=5.5, shake=cam.key(t, [(10.9, 2.0), (12.5, 2.0), (13.2, 0.0)]), t=t, bg=PAPER_W)


HULL_C, HULL_S = (500, 262), 1.36
_hull = {}


def _hull_parts():
    """The tin lying on its side, read off the class world's wreck as an outline (pencil chunks), and where its pane is."""
    if not _hull:
        ink = Ink(0, 0)
        ink.fill((255, 255, 255))
        tp = Wd.wreck(ink, 0.0, c=HULL_C, scale=HULL_S, mood=None, outline=1.0, weed_on=False)
        g = np.asarray(ink.img.convert("L"))
        mask = (g < 70).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        chunks = []
        rs = random.Random(5)
        for cnt in sorted(cs, key=cv2.contourArea, reverse=True)[:3]:
            if cv2.contourArea(cnt) < 900:
                continue
            pts = cnt[:, 0, :].astype(np.float32)
            pts = np.vstack([pts, pts[:1]])
            k = 9
            ker = np.ones(k) / k
            sm = np.stack([np.convolve(np.pad(pts[:, j], (k // 2, k // 2), mode="wrap"), ker, "valid") for j in (0, 1)], 1)[::5]
            n = max(2, len(sm) // 26)
            for q in np.array_split(sm, n):
                if len(q) > 1:
                    chunks.append([(float(x) + rs.gauss(0, 0.5), float(y) + rs.gauss(0, 0.5)) for x, y in q])
        _hull.update(tp=tp, chunks=chunks, bed=tp["nose"][1] + 44 * HULL_S)
    return _hull


def _hull_picture(t):
    """Backed out through the lines: they are on a round pane, the pane is in a hull, the hull puts itself together in
    pencil, lying over on a pencil line of river bed; then, sure of it, the dark hull against the lit teal."""
    hp = _hull_parts()
    (px, py), pr = hp["tp"]["port"], hp["tp"]["port_r"]
    im = Image.new("RGB", (W, H), PAPER_W)
    rs = random.Random(8)
    n = len(hp["chunks"])
    bed = [(40 + 44 * i + 3 * math.sin(i * 1.7), hp["bed"] + 4 * math.sin(i * 0.9) + 2 * math.sin(i * 2.3)) for i in range(21)]
    ub = ease(t, 12.72, 13.12)
    if ub > 0:
        P.graphite(im, [bed[:max(2, int(ub * len(bed)))]], 3.0, 0.7, 31)
    for i, ch in enumerate(hp["chunks"]):
        ta = 12.56 + 0.42 * ((i * 7) % n) / n
        u = ease(t, ta, ta + 0.26)
        ang, ox, oy = rs.uniform(-70, 70), rs.uniform(-260, 260), rs.uniform(-200, 200)
        if u <= 0:
            continue
        a = math.radians(ang * (1 - u))
        ca, sa = math.cos(a), math.sin(a)
        mx, my = sum(p[0] for p in ch) / len(ch), sum(p[1] for p in ch) / len(ch)
        q = [(mx + (x - mx) * ca - (y - my) * sa + ox * (1 - u), my + (x - mx) * sa + (y - my) * ca + oy * (1 - u)) for x, y in ch]
        P.graphite(im, [q], 3.2, 0.95 * u, 40 + i)
    sure = ease(t, 13.14, 13.34)
    if sure > 0:
        ink = Ink(t, int(t * FPS))
        Wd.glow_ground(ink, c=(int(px), int(py)), r=300)
        Wd.wreck(ink, t, c=HULL_C, scale=HULL_S, mood=None, outline=1.0, weed_on=False)
        im = Image.blend(im, ink.img.convert("RGB"), sure)
    # the pane's rim, in pencil, twice round
    for j in range(2):
        ring = [(px + (pr + 2 + 1.5 * math.sin(a * 3 + j)) * math.cos(a + j), py + (pr + 2 + 1.5 * math.cos(a * 2 + j)) * math.sin(a + j))
                for a in np.linspace(0, 2 * math.pi * 1.03, 44)]
        P.graphite(im, [ring], 3.4, 1.0 - 0.3 * j, 20 + j, color=None if sure < 0.5 else (228, 232, 224))
    return im, (px, py, pr)


def _thought(t):
    """Inside the thought at t. A full frame."""
    if t < T_BACK[0]:
        return _strokes_world(t)
    hull, (px, py, pr) = _hull_picture(t)
    u = 1 - cam.smooth(ramp(t, *T_BACK))
    return cam.through_glass(hull, _strokes_world(t), px, py, pr, u, far=0.5, tint=(214, 232, 230))


# ---------------------------------------- the look into the ring while she writes line 2 (a picture, never words)
TH2 = [(18.0, 0), (18.42, 1), (19.2, 1), (19.4, 0)]


def _window_inner(t):
    """Turkey seen from OUTSIDE: his black shape in the round window, beak to the pane, wings on the rim, shoving."""
    ink = Ink(t, int(t * FPS))
    ink.fill(Wd.PAL["tin_dk"])
    Wd.tin_porthole(ink, (480, 270), 214, "shove", t, shake=1.5 * Wd.shove(t))
    return ink.img.convert("RGB")


# ------------------------------------------------------------------ the film
def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if WHIP_UP[0] <= t < WHIP_UP[1]:                     # eyes up the page, from the question to the ring
        return cam.whip(_desk_frame(t, C_Q1), _desk_frame(t, RINGDIVE), ramp(t, *WHIP_UP), direction=-1, axis="y", blur=0.4)
    if T_IN[0] <= t < T_IN[1]:
        rx, ry, _ = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, ramp(t, *T_IN), spin=40)
    if T_IN[1] <= t < T_OUT[0]:
        return _thought(t)
    if T_OUT[0] <= t < T_OUT[1]:
        rx, ry, _ = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, 1 - ramp(t, *T_OUT))
    if WHIP_L[0] <= t < WHIP_L[1]:                       # off the end of the rule: back to the left, and lower
        return cam.whip(_desk_frame(t, C_L3B), _desk_frame(t, C_B0), ramp(t, *WHIP_L), direction=-1, blur=0.4, gap=0.3)
    fr = _desk_frame(t)
    u = cam.key(t, TH2, "linear")
    if u > 0:
        rx, ry, rr = _ring_on_screen(t)
        fr = cam.thought(fr, _window_inner(t), rx, ry, rr * 0.93, u, wobble=5, t=t, dim=0.09)
    return fr


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB") if fr.mode != "RGB" else fr)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m33_pilot.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.1, 1.0, 1.9, 2.42, 3.2, 4.4, 5.6, 5.98, 6.7, 7.8, 8.9, 9.4, 9.75, 10.2, 10.6, 11.0,
                                              11.5, 12.2, 12.7, 12.95, 13.4, 14.0, 14.7, 15.5, 16.05, 16.5, 17.6, 18.3, 18.8, 19.6,
                                              20.6, 21.0, 21.9, 22.5, 23.6, 25.3, 25.55, 26.8, 28.5, 29.6, 30.8, 31.9]
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
            d.rectangle([0, 472, 960, 516], outline=(255, 255, 0))
            d.text((120, 5), cap[0], fill=(255, 255, 0))
        sheet.paste(fr.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(out, f"{(time.time() - t0) / len(ts):.2f} s/frame")
