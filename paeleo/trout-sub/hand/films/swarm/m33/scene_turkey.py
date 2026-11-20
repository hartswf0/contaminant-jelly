"""m33 · scene_turkey · the first friend, E. (board beats T1 to T8, film seconds 33.0 to 56.0; this clock = film - 33).

T1   0.0 ..  1.4  the pilot's page has landed sideways; two rust hands turn it square. The index finger reads: the
                  fish behind its bar; along line 2 to `to` at the end of the rule, nothing after it, it hunts and
                  finds `get out` below; along line 3 the same thing at the same word            (traces 6, 18)
T2   1.4 ..  2.4  dive through the page's drawn ring; we land inside the tin facing its riveted back wall
T3   2.4 ..  3.6  the 180 degree turn, to the right, round to the glass
     3.6 ..  5.8  Turkey's seat, dead level, breath only: outside the glass is the pilot's page, pencil bars edge
                  to edge on paper-white, the pencil fish behind its bar (it drifts a hand's width and back); low
                  left his own pale reflection shoving once a second, each breath fogging the pane (6, 12, 19)
T4   5.8 ..  6.8  back up out of the ring;  6.8 .. 7.3 the sheet is turned over (the eye down at the desk's edge)
T5   7.3 ..  9.9  a quick slanted E; the point passes the triangle and stops on the circle; the button scribbled
                  black, one flick out; in the dashed ring a light loop, a look, the firm oval over it, a dash;
                  a small calm thought: a round dark mouth with the pencil bars in it, stones sliding in (21, 22, 23)
T6   9.9 .. 12.2  eyes up to zone 4: the point lands on the die-1 face and slides off down and left to the paper's
                  edge (the faint line and dots); down; `some one trapped him` on the FIRST rule     (24, 25, 26)
T7  12.2 .. 16.6  `trying to save`; then the hand and the camera stop for 1.8 s, the point standing in the left
                  margin (the firm mark). A boiling thought over the gap: Turkey's seat, two pencil beginnings
                  that come to nothing, then the orange curl, and the reflection lunges. `a hot`, then `cheeto` on
                  the second rule, its fourth letter gone over to a blot                             (27, 28)
T8  16.6 .. 23.0  the point touches the margin again, lightly; a calm thought: the pencil fish behind the pencil
                  bars turns once and stays, black card on lit teal while she is sure; `thats his home`, the last
                  e flicking away; the eye eases back to her whole column; the finger finds "Pass it left again"
                  and the left hand takes the sheet's edge                                   (25, 28, 29, 30)

Nobody on this sheet rubbed anything out: there is no erase pose and no rub mark here.

Every seat is a whole picture (the desk with sheet, hands and head from people.py; the tin's inside handmade here;
Turkey's seat from the c33 world with the pilot's own pencil strokes outside the glass) and every change of seat is
a cam.py move. The desk camera is one perspective camera (cam.tilt) whose tilt, zoom and aim are keyed; the hands
are laid after it at cam.tilt_point of the pencil tip, so the hand is always where the line is being written.

Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page1_done(), page2(t) (the sheet
images, 1520 x 1960; page2(SECONDS) is E.'s whole column), desk_frame(t) and frame(t) (no badge) for the editor and
the next scene unit. frame(0.0) is the desk the pass lands on: page 1, front up, sideways.
Test:  python3 films/swarm/m33/scene_turkey.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
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
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c33"))
import world as Wd  # noqa: E402   (the c33 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402

W, H = 960, 540
key = cam.key

SECONDS = 23.0
CAPTIONS = [
    (12.2, 14.7, "Someone trapped him."),
    (16.6, 19.1, "Trying to save a hot Cheeto."),
    (19.3, 21.9, "That's his home."),
]

RUST = "rust"
HAIR = "short"
WOOD = (86, 62, 44)

# ------------------------------------------------------------ the sheet ---
S = 2                                   # lettered at twice 760 x 980 so the close shots stay sharp
SIZE = (760 * S, 980 * S)
DESK_SIZE = (2300, 2500)                # the desktop plane the camera looks at
SC = (1150, 1280)                       # the sheet's centre on it
SO = (SC[0] - SIZE[0] // 2, SC[1] - SIZE[1] // 2)


def B(page, name):
    return P.where(page, name, SIZE)


def s2(*v):
    """Board numbers (760 x 980 page px) -> this sheet's px."""
    return tuple(x * S for x in v)


def _mid(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


RING1 = _mid(B(1, "ring.in"))
RING_R = (B(1, "ring.in")[2] - B(1, "ring.in")[0]) / 2


class Line:
    """Pencil strokes with their timing (ink at pencil speed, air between strokes): upto(u), tip(u)."""

    def __init__(self, strokes, xh=20.0, letter=None):
        keep = [k for k, s in enumerate(strokes) if len(s) >= 2]
        self.strokes = [list(strokes[k]) for k in keep]
        self.letter = [letter[k] for k in keep] if letter else [0] * len(keep)
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

    def part(self, idx):
        """The strokes of the letters in idx, as a Line of their own."""
        ks = [k for k, q in enumerate(self.letter) if q in idx]
        return Line([self.strokes[k] for k in ks], self.xh, [self.letter[k] for k in ks])


def _lettered(box, text, seed, xh, sink=0.0, slant=None, fix=None):
    """A line in the child's pencil alphabet (people.py), as a Line."""
    plan = P.WritePlan(box, text, seed, xh, slant)
    strokes = [[(x, y + sink) for x, y in st] for st in plan.strokes]
    if fix:
        strokes = fix(strokes, list(plan.letter))
    ln = Line(strokes, plan.xh, list(plan.letter))
    ln.x_end = max(ln.x_end, plan.x_end)
    return ln


# ------------------------------------------- the pilot's pencil, anywhere ---
def _joined_fish():
    """The fish's outline with the gaps the bars cut in it closed up (for where the fish moves behind the bars and
    the bars themselves do the cutting)."""
    fish = [s for s in Wd.PILOT_STROKES if s["group"] == "fish"]
    out = []
    for s in fish:
        pts = list(s["pts"])
        if out and s["weight"] == out[-1]["weight"] == 1.1 and math.hypot(pts[0][0] - out[-1]["pts"][-1][0],
                                                                             pts[0][1] - out[-1]["pts"][-1][1]) < 0.14:
            out[-1]["pts"] = out[-1]["pts"] + pts
        else:
            out.append(dict(s, pts=pts))
    return out


def _pilot_onto(img, c, r, groups=None, joined=False, boost=1.0):
    """The pilot's drawing in graphite (the strokes of the class world, ring units) on any image, in the order the
    pencil went: bars, fish, spots, the jagged lines."""
    k = r / 212.0
    for g in Wd.PILOT_GROUPS:
        if groups is not None and g not in groups:
            continue
        strokes = _joined_fish() if (g == "fish" and joined) else [s for s in Wd.PILOT_STROKES if s["group"] == g]
        for n, s in enumerate(strokes):
            pts = [(c[0] + u * r, c[1] + v * r) for u, v in s["pts"]]
            if s.get("wide"):                              # the side of the lead: a broad pale smear
                P.graphite(img, [pts], s["wide"] * k * 0.9, 0.10 + 0.5 * s["weight"], 331 + n)
            else:
                P.graphite(img, [pts], max(1.2, 1.9 * k * (0.7 + 0.4 * s["weight"])), min(1.45, s["weight"] * boost), 331 + n)


# ---- page 1, as the pilot left it (traces 1 to 19) ----
def _pilots_page():
    """The page exactly as the pilot's scene unit left it, if that module is there and offers it; otherwise None
    and the page is lettered here from the board."""
    try:
        f = HERE / "scene_pilot.py"
        if not f.exists():
            return None
        spec = importlib.util.spec_from_file_location("m33_scene_pilot", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "page1_done"):
            img = mod.page1_done()
        elif hasattr(mod, "page1"):
            img = mod.page1(mod.SECONDS + 1.0)
        else:
            return None
        img = img.convert("RGB")
        return img if img.size == SIZE else img.resize(SIZE, Image.LANCZOS)
    except Exception:
        return None


def _own_page1():
    """The pilot's finished front, lettered here from the board (used only if the pilot's module cannot give it)."""
    pg = P.sheet(SIZE, page=1, porthole=33)
    _pilot_onto(pg, RING1, RING_R)
    b1, b2, b3 = B(1, "a1.2"), B(1, "a2.2"), B(1, "a3.2")
    xh = 0.50 * (b1[3] - b1[1])
    rw = b1[2] - b1[0]

    def put(box, text, seed, weight, size=xh, sink=0.0):
        ln = _lettered(box, text, seed, size, sink=sink)
        P.graphite(pg, ln.strokes, max(1.3, ln.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed)
        return ln

    # 1: between the rules, one answer, `sunk` after a lift and lighter (traces 9, 10, 11)
    a = put((b1[0] + 0.03 * rw, b1[1], b1[2], b1[3]), "A ship that", 330, 1.1)
    put((a.x_end + 0.72 * xh + 20 * S, b1[1], b1[2], b1[3]), "sunk", 331, 0.75)
    # 2: carries on from the stem; spread out to the end of the rule; windo w; get out beside question 3 (12 to 16)
    put((b2[0] + 0.03 * rw, b2[1], b2[2], b2[3]), "look in", 332, 1.1)
    put((b2[0] + 0.27 * rw, b2[1], b2[2], b2[3]), "the", 333, 0.95)
    wd = put((b2[0] + 0.40 * rw, b2[1], b2[2], b2[3]), "windo", 334, 0.85)
    d = wd.part((3,))
    P.graphite(pg, [[(x + 1.5, y + 1) for x, y in st] for st in d.strokes], max(1.3, xh * 0.15), 1.2, 335)
    tail = d.strokes[-1][-1]
    P.graphite(pg, [[tail, (tail[0] + 1, tail[1] + 0.45 * xh)]], max(1.3, xh * 0.15), 1.0, 335)
    put((wd.x_end + 10 * S, b2[1] - 5 * S, b2[2], b2[3] - 5 * S), "w", 336, 0.8, size=0.7 * xh)
    put((b2[0] + 0.66 * rw, b2[1], b2[2], b2[3]), "trying", 337, 0.65)
    put((b2[2] - 2.1 * xh, b2[1], b2[2] + 60, b2[3]), "to", 338, 0.6)
    put(s2(262, 770, 400, 797), "get out", 339, 0.6)
    # 3: the longest thing on the sheet, and it runs out of everything (17, 18, 19)
    put((92 * S, b3[1], b3[2], b3[3]), "He could", 330, 1.1)
    put((b3[0] + 0.30 * rw, b3[1], b3[2], b3[3]), "be freaking", 331, 0.9)
    put((b3[0] + 0.66 * rw, b3[1], b3[2], b3[3]), "out trying", 332, 0.7)
    put((b3[2] - 1.0 * xh, b3[1], b3[2] + 80, b3[3]), "to", 338, 0.7)
    row = s2(138, 850, 752, 882)
    big = xh * 1.25
    put((row[0], row[1], row[2], row[3]), "get out", 333, 0.6, size=big)
    put((316 * S, row[1], row[2], row[3]), "losing", 334, 0.55, size=big, sink=3 * S)
    put((430 * S, row[1], row[2], row[3]), "air", 335, 0.55, size=big, sink=5 * S)
    put((506 * S, row[1], row[2], row[3]), "breating", 336, 0.55, size=big, sink=7 * S)
    hv = put((640 * S, row[1], row[2] + 60, row[3]), "heavy", 337, 0.55, size=big, sink=19 * S)
    x, y = min(hv.x_end + 4, 750 * S - 6), row[3] + 19 * S - 0.07 * (row[3] - row[1])
    P.graphite(pg, [[(x, y - 2), (x + 2, y), (x, y + 1), (x + 1, y - 1)]], 3.4, 1.2, 338)
    return pg


@lru_cache(None)
def page1_done():
    got = _pilots_page()
    return got if got is not None else _own_page1()


# where the reading finger goes on the pilot's page (sheet px; from the board's placings)
_A2, _A3 = B(1, "a2.2"), B(1, "a3.2")
FISH_AT = (RING1[0] + 0.19 * RING_R, RING1[1] + 0.20 * RING_R)
L2_A = (_A2[0] + 30 * S, _A2[3] + 9 * S)
L2_TO = (_A2[2] - 4 * S, _A2[3] + 9 * S)                 # `to`, at the end of the rule
L2_LOST = (_A2[2] + 10 * S, _A2[3] + 16 * S)             # past it: nothing there
GET1 = (330 * S, 797 * S + 8 * S)                        # `get out`, beside the printed question 3
L3_A = (100 * S, _A3[3] + 9 * S)
L3_TO = (_A3[2] + 6 * S, _A3[3] + 9 * S)                 # `to`, past the end of the rule
L3_LOST = (_A3[2] + 14 * S, _A3[3] + 18 * S)
GET2 = (200 * S, 882 * S + 10 * S)                       # `get out` again, on no line at all

# ---- page 2: E.'s column, in this module's time ----
CW = B(2, "bolt1.1")[2] - B(2, "bolt1.1")[0]          # the column's width
LH = B(2, "bolt1.1")[3] - B(2, "bolt1.1")[1]          # one ruled line's height
XH = 0.54 * LH                                        # quick, sharp, leaning
SLANT = 0.24
MARGIN_X = 40 * S

# times (module seconds)
T_E = (7.35, 7.7)
T_BTN = (8.1, 9.0)
T_LOOP = (9.02, 9.24)
T_OVAL = (9.46, 9.78)
T_DASH = (9.8, 9.88)
T_PTR = (10.14, 10.42)
T_DOTS = (10.42, 10.52)
T_L1 = (10.8, 12.2)                 # some one trapped him
T_L2 = (12.5, 13.4)                 # trying to save
T_STUCK = (13.4, 15.2)              # the gap: the hand and the camera stop
T_M1 = (13.62, 13.76)               # the firm mark in the margin
T_HOT = (15.34, 15.7)               # a hot
T_CHEE = (15.8, 16.12)              # chee
T_BLOT = (16.13, 16.34)             # the fourth letter, gone over
T_TO = (16.36, 16.58)               # to
T_M2 = (17.0, 17.1)                 # the faint mark
T_L3 = (17.4, 19.2)                 # thats his home


def _button_scribble():
    """Round and round inside the red-circle button, pressed, 14 turns, one flick out at the upper right (22)."""
    b = B(2, "btn1b")
    cx, cy = _mid(b)
    rb = (b[2] - b[0]) / 2 * 0.86
    rs = random.Random(342)
    pts = []
    n = 14 * 22
    ph = rs.uniform(0, 6.28)
    for k in range(n + 1):
        a = 2 * math.pi * k / 22
        f = k / n
        rr = rb * (0.30 + 0.62 * (0.5 + 0.5 * math.sin(f * 17.0 + ph)) + 0.06 * rs.uniform(-1, 1))
        pts.append((cx + rr * math.cos(a) * 1.02, cy + rr * math.sin(a) * 0.98))
    a = -0.85
    pts += [(cx + rb * 0.9 * math.cos(a), cy + rb * 0.9 * math.sin(a)), (cx + rb * 1.5, cy - rb * 1.25), (cx + rb * 1.9, cy - rb * 1.75)]
    return Line([pts], 14.0)


def _ell(cx, cy, rx, ry, a0, turns, n=30, lean=0.0, wob=0.0, seed=0):
    rs = random.Random(seed)
    out = []
    for k in range(n + 1):
        a = a0 + 2 * math.pi * turns * k / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x - lean * y + wob * rs.uniform(-1, 1), cy + y + wob * rs.uniform(-1, 1)))
    return out


OVAL_C = (_mid(B(2, "draw1.circle"))[0] + 1 * S, _mid(B(2, "draw1.circle"))[1] + 0.5 * S)


def _fix_home(strokes, letter):
    """The last e flicks away to the right (trace 29)."""
    x, y = strokes[-1][-1]
    strokes[-1] = list(strokes[-1]) + [(x + 5 * S, y - 1.0 * S), (x + 10 * S, y - 3.0 * S), (x + 14 * S, y - 5.5 * S)]
    return strokes


@lru_cache(None)
def _plans():
    d = {}
    nb = B(2, "name1.line")
    d["E"] = _lettered((nb[0] + 10 * S, nb[1], nb[2], nb[3]), "E", 340, 0.46 * (nb[3] - nb[1]), slant=0.34)
    d["btn"] = _button_scribble()
    cx, cy = OVAL_C
    d["loop"] = Line([_ell(cx - 0.5 * S, cy + 0.5 * S, 4.6 * S, 7.6 * S, -1.9, 1.04, lean=0.06, wob=0.5, seed=1)], 14.0)
    d["oval"] = Line([_ell(cx, cy, 6.5 * S, 10.0 * S, -1.7, 1.06, lean=0.05, wob=0.4, seed=2)], 14.0)
    d["dash"] = Line([[(cx - 12.5 * S, cy + 9 * S), (cx - 9 * S, cy + 12.5 * S), (cx - 6.5 * S, cy + 14.5 * S)]], 14.0)
    k1 = B(2, "k1")
    die = (k1[0] + 22 * S, k1[1] + 8 * S)                     # the upper right corner of the die-1 face
    a, e = (die[0] + 6 * S, die[1] - 7 * S), (3 * S, 215 * S)
    d["ptr"] = Line([[(lerp(a[0], e[0], f) + 3 * math.sin(f * 7), lerp(a[1], e[1], f) + 2.5 * math.sin(f * 11 + 1)) for f in
                      [k / 24 for k in range(25)]]], 14.0)
    d["dots"] = Line([[(x * S, y * S), (x * S + 1.5, y * S + 1.5)] for x, y in ((11, 204), (17, 211), (8, 219))], 10.0)
    b = B(2, "bolt1.1")
    d["l1"] = _lettered((b[0] + 4 * S, b[1], b[2] + 200, b[3]), "some one trapped him", 343, XH, slant=SLANT)
    b = B(2, "bolt2.1")
    d["l2"] = _lettered((b[0] + 4 * S, b[1], b[2] + 200, b[3]), "trying to save", 344, XH, slant=SLANT)
    d["hot"] = _lettered((d["l2"].x_end + 44 * S, b[1], b[2] + 300, b[3]), "a hot", 345, XH, slant=SLANT)
    b2 = B(2, "bolt2.2")
    full = _lettered((b2[0] + 6 * S, b2[1], b2[2], b2[3]), "cheeto", 346, XH, slant=SLANT)
    d["chee"] = full.part((0, 1, 2, 3))
    e4 = full.part((3,))
    d["blot"] = Line([[(x + 1.2 * k - 1.0, y - 0.9 * k + 0.6) for x, y in st] for k in range(3) for st in e4.strokes], XH)
    d["to"] = full.part((4, 5))
    d["m1"] = Line([[(MARGIN_X, b2[3] - 9 * S), (MARGIN_X + 0.8, b2[3] - 4.5 * S), (MARGIN_X - 0.6, b2[3])]], 12.0)
    b3 = B(2, "bolt3.2")
    d["m2"] = Line([[(MARGIN_X - 2 * S, b3[3] - 9 * S), (MARGIN_X - 2 * S - 1.2, b3[3] - 4 * S), (MARGIN_X - 2 * S, b3[3])]], 12.0)
    b = B(2, "bolt3.1")
    d["l3"] = _lettered((b[0] + 8 * S, b[1], b[2] + 200, b[3]), "thats his home", 347, XH, slant=SLANT, fix=_fix_home)
    return d


#            weight, width factor
STYLE = {"E": (1.2, 1.0), "btn": (1.45, 1.9), "loop": (0.45, 0.9), "oval": (1.3, 1.25), "dash": (0.4, 0.9), "ptr": (0.4, 0.8),
         "dots": (0.7, 1.5), "l1": (1.2, 1.0), "l2": (1.2, 1.0), "m1": (1.2, 1.1), "hot": (1.2, 1.0), "chee": (1.2, 1.0),
         "blot": (1.4, 1.35), "to": (1.2, 1.0), "m2": (0.6, 1.0), "l3": (1.15, 1.0)}
SPANS = {"E": T_E, "btn": T_BTN, "loop": T_LOOP, "oval": T_OVAL, "dash": T_DASH, "ptr": T_PTR, "dots": T_DOTS, "l1": T_L1,
         "l2": T_L2, "m1": T_M1, "hot": T_HOT, "chee": T_CHEE, "blot": T_BLOT, "to": T_TO, "m2": T_M2, "l3": T_L3}
ORDER = ["E", "btn", "loop", "oval", "dash", "ptr", "dots", "l1", "l2", "m1", "hot", "chee", "blot", "to", "m2", "l3"]


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt, wf = STYLE[name]
    wd = max(1.5, ln.xh * 0.135) * (0.82 + 0.22 * wt) * wf          # a sharp pencil: a fine dark line
    P.graphite(img, done, wd, wt, 340 + ORDER.index(name) % 10)
    if name == "btn" and done:                                       # pressed: gone over as it goes
        P.graphite(img, [[(px + 1.2, py + 0.8) for px, py in done[0]]], wd, 1.4, 349)
    return x, y, down


@lru_cache(None)
def _base2(n):
    if n == 0:
        return P.sheet(SIZE, page=2, porthole=33)
    img = _base2(n - 1).copy()
    _write(img, ORDER[n - 1], 1.0)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960). t >= SECONDS gives E.'s whole column."""
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


def _ry(page, name, dy=0.0):
    return B(page, name)[3] + dy * S


#        tilt  log zoom        aim (sheet px)            held at (screen)
LAND = (18.0, math.log(0.52), 760.0, 980.0, 480.0, 262.0)             # where the pass lands: nearly flat above the sheet
READ1 = (56.0, math.log(0.80), 760.0, 1250.0, 480.0, 262.0)           # the seat: the ring above, the three answers below
FLIPV = (88.0, math.log(0.70), 400.0, 500.0, 430.0, 240.0)
FLIP2 = (82.0, math.log(1.5), 400.0, 500.0, 480.0, 240.0)               # ... still nearly edge-on, already close            # the eye down at the desk's edge
NAME = (50.0, math.log(1.5), 400.0, 500.0, 430.0, 240.0)              # zone 5: the name line ...
PICK = (50.0, math.log(1.5), 400.0, 660.0, 430.0, 250.0)              # ... the plates and their buttons
RINGV = (48.0, math.log(1.7), 560.0, 740.0, 470.0, 280.0)             # ... the dashed ring
K1V = (44.0, math.log(1.45), 260.0, 340.0, 420.0, 230.0)              # eyes up: zone 4, the die-1 face
L1 = (46.0, math.log(1.5), 400.0, _ry(2, "bolt1.1", -4), 430.0, 300.0)
L2 = (46.0, math.log(1.5), 400.0, _ry(2, "bolt2.1", 2), 430.0, 300.0)
L3 = (46.0, math.log(1.5), 400.0, _ry(2, "bolt3.1", 0), 430.0, 300.0)
WIDE2 = (54.0, math.log(1.06), 430.0, 880.0, 600.0, 262.0)            # E.'s whole column
CAM_KEYS = [(0.0, LAND), (0.62, READ1), (6.8, READ1), (7.05, FLIPV), (7.13, FLIP2), (7.3, NAME), (7.6, NAME), (8.05, PICK), (8.95, PICK),
            (9.15, RINGV), (9.9, RINGV), (10.2, K1V), (10.5, K1V), (10.8, L1), (12.2, L1), (12.5, L2), (16.6, L2),
            (16.9, L3), (19.2, L3), (21.2, WIDE2), (23.0, WIDE2)]
SHAKE_KEYS = [(0.0, 0.0), (0.7, 2.0), (6.7, 2.0), (6.8, 0.0), (7.3, 0.0), (7.5, 2.0), (13.3, 2.0), (13.4, 0.0), (15.2, 0.0),
              (15.45, 2.0), (19.4, 2.0), (21.2, 1.0), (23.0, 1.0)]


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
    P.head_back(fr, x, y, RUST, 1.15, tilt=tilt, hair=HAIR, turn=turn, t=t)


# ----------------------------------------------- where the hands are ---
T_SQUARE = 0.55                                     # the sheet is square on
AWAY1 = (1330.0, 1720.0)
AWAY2 = (640.0, 1360.0)
PASS_AT = (B(2, "pass2")[0] + 60 * S, B(2, "pass2")[3] + 2 * S)        # under "Pass it left again"


def _turn_angle(t):
    return 90.0 * (1 - cam.smooth(ramp(t, 0.06, T_SQUARE)))


def _on_sheet(p, ang):
    """A sheet point -> desktop px while the sheet lies turned by ang (clockwise) about its centre."""
    x, y = p[0] - SIZE[0] / 2, p[1] - SIZE[1] / 2
    a = math.radians(ang)
    return (SC[0] + x * math.cos(a) - y * math.sin(a), SC[1] + x * math.sin(a) + y * math.cos(a))


def pen(t):
    """(sheet point, pose, lift) of E.'s right hand."""
    pl = _plans()

    def wr(name):
        x, y, down = pl[name].tip(ramp(t, *SPANS[name]))
        return (x, y), "write", 0 if down else 6

    def go(a, ta, b, tb, hi=12, lo_a=4, lo_b=4, pose="hover"):
        f = cam.smooth(ramp(t, ta, tb))
        return (lerp(a[0], b[0], f), lerp(a[1], b[1], f)), pose, lerp(lo_a, lo_b, f) + hi * math.sin(math.pi * f)

    if t < 6.95:                                   # page 1: the index finger reads the pilot's page (traces 6, 18)
        p = key(t, [(T_SQUARE, AWAY1), (0.72, FISH_AT), (0.80, FISH_AT), (0.90, L2_A), (1.08, L2_TO), (1.13, L2_TO),
                    (1.19, L2_LOST), (1.24, L2_LOST), (1.34, GET1), (1.42, GET1), (1.52, L3_A), (1.70, L3_TO), (1.75, L3_TO),
                    (1.81, L3_LOST), (1.86, L3_LOST), (1.98, GET2), (6.6, GET2), (6.95, AWAY1)])
        lf = key(t, [(T_SQUARE, 16), (0.70, 3), (0.72, 0), (0.80, 0), (0.85, 8), (0.90, 0), (1.13, 0), (1.19, 5), (1.24, 5),
                     (1.29, 9), (1.34, 0), (1.42, 0), (1.47, 8), (1.52, 0), (1.75, 0), (1.81, 5), (1.86, 5), (1.92, 9),
                     (1.98, 0), (6.6, 0), (6.9, 14)])
        return p, "point", lf
    if t < T_E[0]:
        return go((760.0, 760.0), 6.95, pl["E"].start, T_E[0], 10, 16, 5)
    if t < T_E[1]:
        return wr("E")
    if t < T_BTN[0]:                               # over "Theater curtain" and its triangle without touching; the circle
        ta = (B(2, "plate1a")[0] + 150 * S, B(2, "plate1a")[3] - 4 * S)
        tri = (_mid(B(2, "btn1a"))[0] + 6 * S, _mid(B(2, "btn1a"))[1] + 2 * S)
        p = key(t, [(T_E[1], pl["E"].end), (7.86, ta), (7.98, tri), (8.03, tri), (T_BTN[0], pl["btn"].start)])
        return p, "hover", key(t, [(T_E[1], 5), (7.78, 13), (7.86, 10), (8.03, 10), (T_BTN[0], 3)])
    if t < T_BTN[1]:
        return wr("btn")
    if t < T_LOOP[0]:
        return go(pl["btn"].end, T_BTN[1], pl["loop"].start, T_LOOP[0], 6, 2, 2)
    if t < T_LOOP[1]:
        return wr("loop")
    if t < T_OVAL[0]:                              # a look: the point up off the paper, beside what it made
        e, s = pl["loop"].end, pl["oval"].start
        up = (e[0] + 14 * S, e[1] + 6 * S)
        p = key(t, [(T_LOOP[1], e), (9.32, up), (9.40, up), (T_OVAL[0], s)])
        return p, "hover", key(t, [(T_LOOP[1], 2), (9.32, 13), (9.40, 13), (T_OVAL[0], 3)])
    if t < T_OVAL[1]:
        return wr("oval")
    if t < T_DASH[0]:
        return go(pl["oval"].end, T_OVAL[1], pl["dash"].start, T_DASH[0], 2, 2, 2, "write")
    if t < T_DASH[1]:
        return wr("dash")
    if t < T_PTR[0]:                               # up to zone 4; the point comes down on the die-1 face
        p = key(t, [(T_DASH[1], pl["dash"].end), (10.04, pl["ptr"].start), (T_PTR[0], pl["ptr"].start)])
        return p, "hover", key(t, [(T_DASH[1], 3), (9.96, 15), (10.04, 4), (10.07, 0), (T_PTR[0], 0)])
    if t < T_PTR[1]:
        return wr("ptr")
    if t < T_DOTS[1]:
        return wr("dots")
    if t < T_L1[0]:
        return go(pl["dots"].end, T_DOTS[1], pl["l1"].start, T_L1[0], 12, 3, 4)
    if t < T_L1[1]:
        return wr("l1")
    if t < T_L2[0]:
        return go(pl["l1"].end, T_L1[1], pl["l2"].start, T_L2[0], 10, 3, 4)
    if t < T_L2[1]:
        return wr("l2")
    if t < T_M1[0]:                                # it stops; the point goes to the left margin
        return go(pl["l2"].end, T_L2[1], pl["m1"].start, T_M1[0], 9, 2, 1)
    if t < T_M1[1]:
        return wr("m1")
    if t < T_STUCK[1]:                             # and stands there, on the paper (trace 28)
        return pl["m1"].end, "write", 0
    if t < T_HOT[0]:                               # across the gap it left
        return go(pl["m1"].end, T_STUCK[1], pl["hot"].start, T_HOT[0], 8, 0, 3, "write")
    if t < T_HOT[1]:
        return wr("hot")
    if t < T_CHEE[0]:
        return go(pl["hot"].end, T_HOT[1], pl["chee"].start, T_CHEE[0], 8, 3, 3, "write")
    if t < T_CHEE[1]:
        return wr("chee")
    if t < T_BLOT[0]:
        return pl["chee"].end, "write", 2
    if t < T_BLOT[1]:
        return wr("blot")
    if t < T_TO[0]:
        return go(pl["blot"].end, T_BLOT[1], pl["to"].start, T_TO[0], 2, 2, 2, "write")
    if t < T_TO[1]:
        return wr("to")
    if t < T_M2[0]:                                # down, and out to the margin again, lower
        return go(pl["to"].end, T_TO[1], pl["m2"].start, T_M2[0], 9, 3, 1)
    if t < T_M2[1]:
        return wr("m2")
    if t < T_L3[0]:
        e = pl["m2"].end
        p = key(t, [(T_M2[1], e), (17.24, e), (T_L3[0], pl["l3"].start)])
        return p, "hover", key(t, [(T_M2[1], 0), (17.14, 5), (17.24, 5), (17.33, 11), (T_L3[0], 3)])
    if t < T_L3[1]:
        return wr("l3")
    if t < 21.5:                                   # the hand rests beside what it wrote
        e = pl["l3"].end
        rest = (e[0] + 30 * S, e[1] + 26 * S)
        return key(t, [(T_L3[1], e), (19.9, rest)]), "hover", key(t, [(T_L3[1], 2), (19.9, 14)])
    e = pl["l3"].end                               # the finger finds "Pass it left again"
    rest = (e[0] + 30 * S, e[1] + 26 * S)
    p = key(t, [(21.5, rest), (22.1, PASS_AT), (22.6, (PASS_AT[0] + 46 * S, PASS_AT[1]))])
    return p, "point", key(t, [(21.5, 14), (22.0, 5), (22.1, 0)])


def _still_t(t):
    """The hand's own clock: it stops dead while she is stuck."""
    if T_M1[1] <= t < T_STUCK[1]:
        return T_M1[1]
    if T_M2[1] <= t < 17.24:
        return T_M2[1]
    if T_L3[1] + 0.7 <= t < 21.5:
        return T_L3[1] + 0.7
    return t


# ------------------------------------------------------------ desk frames ---
def _left_hold(fr, v, t, p, lift=None):
    P.hand(fr, *v.pt(p), pose="hold", tone=RUST, scale=v.hs(p), flip=True, t=t, arm=140, lift=lift)


def _right(target, v, t):
    p, pose, lift = pen(t)
    arm = 60 if pose == "point" else key(t, [(7.7, 58), (8.0, 68), (9.9, 68), (10.2, 58)])
    P.hand(target, *v.pt(p), pose=pose, tone=RUST, scale=v.hs(p), t=_still_t(t), lift=lift, arm=arm)


HOLD1 = (120.0, 1880.0)             # the left hand's place on the pilot's page
HOLD2 = (230.0, 1700.0)             # ... and on page 2
RIDE_R = (1400.0, 1560.0)           # where the right hand lies on the sheet while it is turned


def _turning(fr, v, t):
    """Two hands turn the sideways sheet square: each lies flat on the paper and goes round with it."""
    ang = _turn_angle(t)
    lx, ly = _on_sheet(HOLD1, ang)
    P.hand(fr, *v.dpt(lx, ly), pose="hold", tone=RUST, scale=v.hs(HOLD1), flip=True, t=t, arm=140 + 0.35 * ang)
    rx, ry = _on_sheet(RIDE_R, ang)
    f = cam.smooth(ramp(t, T_SQUARE - 0.12, T_SQUARE + 0.02))
    if f < 1:
        P.hand(fr, *v.dpt(rx, ry), pose="hold", tone=RUST, scale=v.hs(RIDE_R), t=t, arm=58 + 0.25 * ang, lift=10 * f or None)
    else:
        _right(fr, v, t)


def desk_frame(t, shot=None):
    """E.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t, shot)
    cl = _closeness(v)
    if t < T_SQUARE:                              # the sheet arrived sideways: the hands turn it square
        fr = v.render(_desktop(page1_done(), angle=_turn_angle(t)))
        _turning(fr, v, t)
        sway = math.sin(math.pi * ramp(t, 0.0, T_SQUARE))
        _head(fr, t, cl, tilt=6 * sway, turn=0.2 * sway, dy=110 * (1 - ease(t, 0.1, 0.62)))
        return fr
    if t < 6.8:                                   # the finger on the pilot's page
        fr = v.render(_desktop(page1_done()))
        _left_hold(fr, v, t, HOLD1)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    if t < 7.3:                                   # the page flip: down to the desk's edge, the sheet turned, back up
        first = t < 7.05
        lift = 26 * math.sin(math.pi * ramp(t, 6.8, 7.3))
        fr = v.render(_desktop(page1_done() if first else page2(t), lift=lift))
        e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1180 - lift * 0.6)
        P.hand(fr, e[0], e[1], pose="pass", tone=RUST, scale=v.hs((0, 1180)), flip=True, t=t, arm=150, edge=90)
        _right(fr, v, t)
        _head(fr, t, cl)
        return fr
    # page 2
    lift = 7 * ease(t, 22.55, 23.0)                # the sheet begins to come up in the left hand
    fr = v.render(_desktop(page2(t), lift=lift))
    if t >= 22.3:                                  # the left hand takes the sheet's edge
        f = cam.smooth(ramp(t, 22.3, 22.6))
        if f < 1:
            p = (lerp(HOLD2[0], 40.0, f), lerp(HOLD2[1], 1340.0, f))
            _left_hold(fr, v, t, p, lift=12 * math.sin(math.pi * f) or None)
        else:
            e = v.dpt(SO[0] + 6 - lift * 0.2, SO[1] + 1340 - lift * 0.6)
            P.hand(fr, e[0], e[1], pose="pass", tone=RUST, scale=v.hs((0, 1340)), flip=True, t=t, arm=150, edge=90)
    elif cl < 0.9:
        _left_hold(fr, v, t, HOLD2)
    _right(fr, v, t)
    _head(fr, t, cl, tilt=-3 * math.sin(math.pi * ramp(t, 9.24, 9.46)))
    return fr


def ring_xy(t):
    return view(t).pt(RING1)


# ------------------------------------------------- inside the tin (handmade) ---
PAL = Wd.PAL
T_DIVE = (1.4, 2.4)
T_TURN = (2.4, 3.6)
T_SEAT = (3.6, 5.8)
T_UP = (5.8, 6.8)


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
    im = _wall(331, (188, 772), 0.42, lamp=(820, 440, 0.9))
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    a = np.asarray(im, np.float32) * (1.0 - 0.35 * np.clip((yy - 380) / 200, 0, 1))[..., None]
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
    """The wall the turn passes: ribbed tin, two seams, the air pipe, and the page's white light coming round."""
    im = _wall(341, (300, 660), 0.38, light=(960, (96, 96, 88), 0.8))
    _pipe(im, (150, 480, 810))
    return im


# ------------------------------------------------ Turkey's seat, looking out ---
PC, PR = Wd.PORT_C, Wd.PORT_R
PAPER = P.PAPER


@lru_cache(None)
def _paper_ground():
    """Paper-white beyond the glass: the page itself, with a little of its tooth and a soft fall-off to the rim."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - PC[0], yy - PC[1]) / PR
    sh = 1.0 - 0.07 * np.clip(d - 0.55, 0, 1) - 0.02 * P.vnoise((H, W), 3.0, None, 337)
    return P.to_img(np.array(PAPER, np.float32)[None, None, :] * sh[..., None]).convert("RGB")


@lru_cache(None)
def _bars_layer(boost=1.0):
    """The pencil bars and the jagged lines, on white (laid over the fish with the darker of the two)."""
    im = Image.new("RGB", (W, H), (255, 255, 255))
    _pilot_onto(im, PC, PR, groups=["bar%d" % k for k in range(1, 10)] + ["cracks"], boost=boost)
    return im


@lru_cache(None)
def _fish_layer():
    im = Image.new("RGB", (W, H), (255, 255, 255))
    _pilot_onto(im, PC, PR, groups=["fish", "spots"], joined=True)
    return im


@lru_cache(None)
def _bar_mask():
    """Bars 5 and 6 as the paper between their two lines: the fish's outline stops at them (trace 6)."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for k in (5, 6):
        left, right = [], []
        for i in range(25):
            v = -1.12 + 2.24 * i / 24
            x, wd = Wd.bar_line(k, v, PC, PR)
            y = PC[1] + v * PR
            left.append((x - wd / 2 + 1, y))
            right.append((x + wd / 2 - 1, y))
        d.polygon(left + right[::-1], fill=255)
    return m


def outside(dx=0.0, dy=0.0, extra=None):
    """What is beyond the glass: the pilot's page. Pencil bars edge to edge, the small pencil fish behind them
    (moved by dx, dy and still cut by its bar), the jagged lines over all. extra(img) may pencil more in."""
    fish = _fish_layer()
    if dx or dy:
        fish = ImageChops.offset(fish, int(round(dx)), int(round(dy)))
    fish = fish.copy()
    fish.paste((255, 255, 255), (0, 0), _bar_mask())
    im = ImageChops.multiply(_paper_ground(), ImageChops.darker(fish, _bars_layer()))
    if extra:
        extra(im)
    return im


def _fish_drift(t):
    """At 4.6 (film 37.6) the pencil fish drifts a hand's width along behind the bars, and back."""
    f = math.sin(math.pi * cam.smooth(ramp(t, 4.55, 5.6)))
    a = math.radians(17.0)
    return (-46 * f * math.cos(a), 46 * f * math.sin(a))


def view_out(t, mood="shove", refl=None, extra=None, front=None, fog=None, drift=None):
    """Turkey's seat: the brass porthole from where he sits, the gauge low right at 5. Outside the glass is the
    pilot's page. Low on the left his own pale reflection, shoving once a second; each breath fogs the pane."""
    ink = Ink(t, int(t * 24))
    dx, dy = drift if drift is not None else _fish_drift(t)
    ink.img.paste(outside(dx, dy, extra))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if front:
        front(ink)
    # a soft shade of him on the white first, so the pale reflection reads against paper
    kw = dict(mood=mood, t=t)
    kw.update(refl or {})
    sh = Ink(t, int(t * 24))
    sh.img = Image.new("RGB", (W, H), (255, 255, 255))
    sh.d = ImageDraw.Draw(sh.img, "RGBA")
    Wd.turkey_shadow(sh, kw.get("cx", Wd.STAGE["reflection"][0]) + 62, kw.get("cy", Wd.STAGE["reflection"][1]) - 12,
                     kw.get("height", Wd.STAGE["reflection_h"]), mood=mood, t=t, flip=True, color=(120, 128, 126), eye=False)
    shade = sh.img.filter(ImageFilter.GaussianBlur(7))
    shade = Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), shade, 0.55)
    ink.img.paste(ImageChops.multiply(ink.img, shade))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.turkey_reflection(ink, **kw)
    Wd.fog(ink, fog if fog is not None else 0.2 + 0.05 * ramp(t, T_SEAT[0], T_SEAT[1]), t)
    Wd.seat_frame(ink)
    Wd.gauge(ink, 5.0, t=t, tremble=0.5 * Wd.breath(t))
    return ink.img.convert("RGB")


def seat_frame(t):
    br = Wd.breath(t)                                             # dead level: breath only
    return cam.shoot([(view_out(t), 1.0)], zoom=1.0 + 0.005 * br, y=-1.2 * br, bg=(14, 16, 18))


# ------------------------------------------------------------ the thoughts ---
def _zoomed(img, cx, cy, k):
    """The picture pushed in k times about (cx, cy)."""
    w, h = W / k, H / k
    x0 = clamp(cx - w / 2, 0, W - w)
    y0 = clamp(cy - h / 2, 0, H - h)
    return img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


@lru_cache(None)
def _mouth_base():
    """A round dark mouth shaded in with the side of the lead, the pilot's pencil bars standing in it."""
    im = Image.new("RGB", (W, H), PAPER)
    rs = random.Random(23)
    r = PR * 0.80
    lines = []
    for k in range(-26, 27):
        y = PC[1] + k * r / 26
        half = math.sqrt(max(0.0, r * r - (y - PC[1]) ** 2))
        if half > 4:
            lines.append([(PC[0] - half + rs.uniform(0, 9), y + rs.uniform(-2, 2)), (PC[0] + rs.uniform(-30, 30), y + rs.uniform(-3, 3)),
                          (PC[0] + half - rs.uniform(0, 9), y + rs.uniform(-2, 2))])
    P.graphite(im, lines, 5.0, 0.5, 23)
    P.graphite(im, [[(PC[0] + (r - 2) * math.cos(a / 20), PC[1] + (r - 2) * math.sin(a / 20)) for a in range(0, 131)]], 3.0, 1.2, 24)
    bars = Image.new("RGB", (W, H), (255, 255, 255))
    _pilot_onto(bars, PC, PR, groups=["bar%d" % k for k in range(1, 10)], boost=1.7)
    hole = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hole).ellipse([PC[0] - r, PC[1] - r, PC[0] + r, PC[1] + r], fill=255)
    bars.paste((255, 255, 255), (0, 0), ImageChops.invert(hole))            # the bars stand in the mouth
    return ImageChops.darker(im, bars)


def mouth(t, done):
    """T5's thought: is the oval the button, or a tunnel's mouth seen from the front? Stones slide in round it."""
    ink = Ink(t, int(t * 24))
    ink.img.paste(_mouth_base())
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if done > 0:
        Wd.stone_ring(ink, done)
    return ink.img.convert("RGB")


def _scrap(seed, c, r):
    """A small beginning in pencil that is not yet anything: three short strokes."""
    rs = random.Random(seed)
    out = []
    for k in range(3):
        a0 = rs.uniform(0, 6.28)
        cx, cy = c[0] + rs.uniform(-0.5, 0.5) * r, c[1] + rs.uniform(-0.4, 0.4) * r
        rr = r * rs.uniform(0.35, 0.7)
        sweep = rs.uniform(1.6, 3.4)
        out.append([(cx + rr * math.cos(a0 + sweep * i / 9), cy + 0.7 * rr * math.sin(a0 + sweep * i / 9)) for i in range(10)])
    return out


CURL_AT = (506.0, 214.0)                  # between the fifth and sixth bars, out beyond them
T_CURL = 14.8


def gap_thought(t):
    """T7's thought, in Turkey's seat: something small begins in pencil beyond the bars and does not become
    anything, twice; then the curl is there, orange, and the reflection lunges up the pane after it."""
    def extra(im):
        for seed, c, (a, b) in ((51, (610.0, 190.0), (14.0, 14.4)), (52, (384.0, 318.0), (14.4, 14.8))):
            if a <= t < b:
                u = (t - a) / (b - a)
                grow = clamp(u / 0.45)
                go = clamp((u - 0.5) / 0.5)
                cx, cy = c
                lines = []
                for k, st in enumerate(_scrap(seed, c, 34.0)):
                    n = max(2, int(len(st) * clamp(grow * 3 - k)))
                    if grow * 3 - k <= 0:
                        continue
                    mx = sum(p[0] for p in st) / len(st) - cx
                    my = sum(p[1] for p in st) / len(st) - cy
                    lines.append([(x + mx * 1.6 * go + 10 * go * (k - 1), y + my * 1.6 * go - 14 * go) for x, y in st[:n]])
                if lines:
                    P.graphite(im, lines, 2.6, 1.0 - 0.8 * go, seed)

    def front(ink):
        if t >= T_CURL:
            a = ease(t, T_CURL, T_CURL + 0.12)
            Wd.cheeto(ink, CURL_AT[0], CURL_AT[1] + 10 * ease(t, T_CURL, 15.2), 30, angle=18 + 20 * math.sin(t * 3), t=t, alpha=a)

    lunge = ease(t, T_CURL + 0.05, T_CURL + 0.3)
    refl = dict(cx=lerp(Wd.STAGE["reflection"][0], 384, lunge), cy=lerp(Wd.STAGE["reflection"][1], 352, lunge))
    im = view_out(t, mood="lunge" if lunge > 0.05 else "shove", refl=refl, extra=extra, front=front, fog=0.26, drift=(0, 0))
    return _zoomed(im, PC[0], PC[1] - 4, 1.32)


T_SURE = 17.34


def home_thought(t):
    """T8's thought: the pencil fish behind the pencil bars is not trying to get out. It turns once, slowly, and
    stays; for that moment it and the bars are black card on lit teal."""
    fx, fy = Wd.STAGE["fish"]
    if t < T_SURE:
        im = outside(-5 * math.sin((t - 16.9) * 2.2), 0)
    else:
        ink = Ink(t, int(t * 24))
        Wd.glow_ground(ink)
        c = math.cos(math.pi * cam.smooth(ramp(t, T_SURE + 0.04, T_SURE + 0.6)))
        spr = Wd.shadow_fish_sprite(Wd.STAGE["fish_len"], tail=14 * math.sin(t * 5))
        w0 = max(3, int(spr.width * abs(c)))
        spr = spr.resize((w0, spr.height), Image.BILINEAR)
        if c < 0:
            spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        Wd.put(ink, spr, fx, fy, angle=Wd.STAGE["fish_angle"] * (1 if c >= 0 else -1) * abs(c))
        Wd.bars(ink)
        im = ink.img.convert("RGB")
    return _zoomed(im, fx - 6, fy - 4, 1.7)


def _thoughts(fr, t):
    if 9.2 < t < 9.9:                             # T5: as the oval closes; calm
        v = view(t)
        x, y = v.pt(OVAL_C)
        u = key(t, [(9.2, 0.0), (9.5, 1.0), (9.76, 1.0), (9.9, 0.0)])
        return cam.thought(fr, mouth(t, ease(t, 9.42, 9.78)), x - 100, y - 100, 70, u, wobble=0, t=0, dim=0.0)
    if 13.6 < t < T_STUCK[1]:                     # T7: over the gap on the line; boiling
        v = view(T_STUCK[0] + 0.5)
        pl = _plans()
        gx, gy = v.pt(((pl["l2"].x_end + pl["hot"].start[0]) / 2, B(2, "bolt2.1")[3]))
        u = key(t, [(13.6, 0.0), (13.95, 1.0), (15.04, 1.0), (15.2, 0.0)])
        return cam.thought(fr, gap_thought(t), gx + 170, gy - 140, 110, u, wobble=7, t=t, dim=0.0)
    if 16.9 < t < 18.0:                           # T8: calm; she is sure
        u = key(t, [(16.9, 0.0), (17.2, 1.0), (17.86, 1.0), (18.0, 0.0)])
        return cam.thought(fr, home_thought(t), 640, 168, 90, u, wobble=0, t=0, dim=0.0)
    return fr


# ------------------------------------------------------------------ draw ---
def frame(t):
    """The 960 x 540 picture at module second t, without the badge."""
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 0.62:                                      # the eye rolls a little with the turning sheet, and settles
        e = math.sin(math.pi * ramp(t, 0.0, 0.62))
        return cam.shoot([(desk_frame(t), 1.0)], rot=5 * e, zoom=1.0 + 0.04 * e, bg=WOOD)
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
    return _thoughts(desk_frame(t), t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def _test(argv):
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() and not argv[0].startswith("--") else FILMS / "stills" / "m33_scene_turkey"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.25, 0.45, 0.75, 1.0, 1.2, 1.36, 1.6, 1.9, 2.2, 2.6, 3.0, 3.3, 3.8, 4.6, 5.1, 5.7, 6.1, 6.5, 6.9, 7.1,
              7.5, 7.9, 8.5, 9.0, 9.4, 9.7, 10.1, 10.45, 11.4, 12.2, 13.0, 13.5, 13.9, 14.2, 14.6, 15.0, 15.5, 16.0, 16.5,
              17.05, 17.3, 17.6, 18.5, 19.2, 20.5, 21.6, 22.2, 22.9]
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
