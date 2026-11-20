"""m10 · scene_pilot · the pilot fills in page 1 of Porthole Log 10 (board beats P1 to P11, 0.0 to 32.0 s).

The slip and the blank sheet on the desk; reading; the first jaw drawn in the ring; a dive through the drawn ring
into the thought, where the jaw puts itself together wrongly, falls apart and comes back as two rows on one pin;
back up; the second jaw outside the ring; the three lines in the child's own spelling with their true traces
(letters two rules tall over the printed questions, no gaps, pressure fading, the capital E, the round full stop,
the "w" gone over, a rule left clean, the long stuck hold, the blacked-in "B", the reworked "so", the small "it"
squeezed in, "probibly"); letting go.

Seats are full pictures: `_desk_frame(t)` (the desktop laid back by cam.tilt, hands and head from people.py) and
`_thought(t)` (the c10 river with the drawing as pencil line). Moves between them are cam.dive / cam.blink; moves
at the desk are one keyframed tilt camera (`_cam`). Nothing is cross-faded.

Exposes SECONDS, CAPTIONS, draw(t, ink), and page1(t) (the written sheet at film time t, for the other units).

    python3 films/swarm/m10/scene_pilot.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
for p in (str(FILMS), str(FILMS / "swarm" / "c10")):
    if p not in sys.path:
        sys.path.insert(0, p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402
from kit import clamp, lerp, ramp, smooth, ease  # noqa: E402

SECONDS = 32.0
CAPTIONS = [
    (18.6, 21.2, "Little french fries. A new locked school."),
    (21.3, 23.9, "Freak out."),
    (29.4, 32.0, "It is a big container, so it probably takes it up."),
]

TONE = "rust"
W, H = 960, 540

# ------------------------------------------------------------------ the desktop (a picture bigger than the frame)
SZ = (1216, 1568)                       # the sheet, in desktop pixels
KS = SZ[0] / 760.0
DW, DH = 2100, 2100                     # the desk top
PX, PY = 442, 250                       # the sheet's top-left corner on it
SLIP = (1846, 800)                      # the slip, to the right of the sheet
SLIP_S = 1.3
GROOVE = (820, 76)                      # where the pencil lies in the groove (its point)
INFO = P.porthole_info(10)
CLUE = "Elementary brick: flapping Clam-Shell PA"


def B(name):
    return P.where(1, name, SZ)


def D(x, y):
    """page px -> desktop px"""
    return (PX + x, PY + y)


RING = B("ring.in")
RCX, RCY = (RING[0] + RING[2]) / 2, (RING[1] + RING[3]) / 2
RSC = round((RING[2] - RING[0]) / 2 / 214.0, 2)          # screen px per photograph px for Wd.pilot_drawing
XH = 37.0                                                  # the pilot's x-height: tall letters are two rules high


# ------------------------------------------------------------------ what gets put on the page, and when
class Act:
    """One pull of work on the page: draw(img, u) lays it as far as u; tip(u) -> (x, y, down) in page px."""
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
    """Pencil polylines drawn in order (go-overs, the round full stop)."""
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


class Jaw(Act):
    """The child's own drawing (traced strokes from the c10 world), with a remapped clock."""
    def __init__(self, t0, t1, part, alpha=1.0, remap=None):
        super().__init__(t0, t1)
        self.part, self.alpha, self.remap = part, alpha, remap

    def prog(self, u):
        return cam.key(u, self.remap, "linear") if self.remap else u

    def draw(self, img, u):
        if u > 0:
            Wd.pilot_drawing(img, RCX, RCY, self.prog(u) if u < 1 else 1.0, RSC, self.part, self.alpha)

    def tip(self, u):
        return Wd.pilot_tip(RCX, RCY, self.prog(u), RSC, self.part)


def _letter_lines(plan, idx):
    return [s for s, l in zip(plan.strokes, plan.letter) if l == idx]


def _go_over(lines, passes, seed, jit=1.6, shrink=()):
    """The same strokes again and again, a little off each time; `shrink` adds smaller loops inside (a bowl filled)."""
    rs = random.Random(seed)
    out = []
    for k in range(passes):
        for ln in lines:
            dx, dy = rs.uniform(-jit, jit), rs.uniform(-jit, jit)
            out.append([(x + dx + rs.uniform(-0.5, 0.5), y + dy + rs.uniform(-0.5, 0.5)) for x, y in ln])
    for f in shrink:
        for ln in lines:
            cx, cy = sum(p[0] for p in ln) / len(ln), sum(p[1] for p in ln) / len(ln)
            out.append([(cx + (x - cx) * f + rs.uniform(-0.8, 0.8), cy + (y - cy) * f + rs.uniform(-0.8, 0.8)) for x, y in ln])
    return out


def _chunks(t0, t1, box, parts, seed, joined=False, size=XH):
    """A line written as several pulls with falling weight. parts = [(text, weight[, dy[, size]])]."""
    acts, x = [], box[0]
    for i, pt in enumerate(parts):
        text, weight = pt[0], pt[1]
        dy = pt[2] if len(pt) > 2 else 0
        sz = pt[3] if len(pt) > 3 else size
        bx = (x, box[1] + dy, box[2], box[3] + dy)
        a = Write(0, 0, bx, text, seed + i, weight, sz)
        acts.append(a)
        x = a.plan.x_end + (0 if joined else 0.62 * sz) - 0.3 * sz
    tot = sum(a.plan.T for a in acts)
    tt = t0
    for a in acts:
        a.t0 = tt
        tt += (t1 - t0) * a.plan.T / tot
        a.t1 = tt
    return acts


def _build():
    acts = []
    # P2: the firm jaw in the ring. The box first (the bottom line three times), then the teeth, slower and pressed.
    path = Wd._pilot(int(round(RSC * 100)), "jaw")[4]
    ends = [p for p, _, _, down in path if not down]
    p_box = ends[4] + 0.004                              # progress when the box (5 strokes) is done
    acts.append(Jaw(3.0, 5.7, "jaw", remap=[(0, 0), (0.40, p_box), (0.46, p_box + 0.012), (1, 1)]))
    # P6: the second jaw, outside the ring, quick and light
    acts.append(Jaw(11.5, 12.85, "outside", alpha=0.62))

    # P7: line 1. One breath, no gaps; black on the left, pale on the right; a capital E in the middle of a word.
    a11, a12 = B("a1.1"), B("a1.2")
    L1 = _chunks(14.4, 16.25, (a11[0] + 26, a11[1], a11[2], a11[3] + 2), [("little", 1.35), ("frEnch", 1.0), ("fries", 0.62)], 101, joined=True)
    acts += L1
    ex, by = L1[-1].plan.x_end + 12, a11[3] - 9
    stop = [[(ex + 7.5 * math.cos(a), by + 7.0 * math.sin(a)) for a in np.linspace(-1.2, 2 * math.pi * 2 - 0.6, 40)]]
    acts.append(Lines(16.3, 16.6, stop, weight=0.8, width=2.6, seed=7))               # the fat round full stop
    L2 = _chunks(16.8, 18.2, (a12[0] + 30, a12[1] + 13, a12[2], a12[3] + 13),
                 [("a", 1.35), ("new", 1.3), ("lockEd", 0.95), ("school", 0.55)], 111)
    acts += L2
    wl = _letter_lines(L2[1].plan, 2)
    acts.append(Lines(18.24, 18.6, _go_over(wl, 3, 5, 1.8), weight=1.45, width=4.2, seed=9))   # the "w" gone over

    # P8: line 2. Two words. The f hangs a rule below the line.
    a21 = B("a2.1")
    f = Write(19.0, 19.22, (a21[0] + 22, a21[1] + 22, a21[2], a21[3] + 22), "f", 121, 1.3, XH * 1.25)
    L3 = _chunks(19.22, 20.6, (f.plan.x_end + 2, a21[1] + 3, a21[2], a21[3] + 3), [("reak", 1.15), ("out", 0.8)], 122)
    acts += [f] + L3

    # P10: line 3. The hard one.
    a31, a32 = B("a3.1"), B("a3.2")
    L4 = _chunks(26.5, 27.5, (a31[0] + 30, a31[1] + 4, a31[2], a31[3] + 4),
                 [("it", 1.35), ("is", 1.3), ("a", 1.25), ("Big", 1.2), ("container", 0.6)], 131)
    acts += L4
    bl = _letter_lines(L4[3].plan, 0)
    acts.append(Lines(27.55, 28.0, _go_over(bl, 4, 11, 2.2) + _go_over(bl[1:], 1, 12, 1.0, shrink=(0.72, 0.45, 0.2)),
                      weight=1.5, width=5.2, seed=13))                                # the B, round and round
    so = Write(28.02, 28.14, (a32[0] + 28, a32[1] + 6, a32[2], a32[3] + 6), "so", 141, 0.9, XH * 0.95)
    acts.append(so)
    acts.append(Lines(28.16, 28.33, _go_over(so.plan.strokes, 1, 15, 2.6), weight=0.85, width=3.4, seed=16))   # "so" reworked
    gap0 = so.plan.x_end + 8
    L5 = _chunks(28.37, 28.9, (gap0 + 46, a32[1] + 6, a32[2] + 60, a32[3] + 6),
                 [("probibly", 1.0), ("takes", 0.78), ("it", 0.6), ("up", 0.5)], 151, size=XH * 0.95)
    acts += L5
    acts.append(Write(29.14, 29.4, (gap0, a32[1] + 12, gap0 + 60, a32[3] + 12), "it", 161, 0.85, XH * 0.52))   # the small "it"
    acts.sort(key=lambda a: a.t0)
    return acts


ACTS = _build()
_page_cache = {}


def page1(t):
    """The pilot's page as it stands at film time t: a fresh PIL image, SZ = 1216 x 1568 (use P.where(1, name, SZ))."""
    done = sum(1 for a in ACTS if t >= a.t1)
    if done not in _page_cache:
        if len(_page_cache) > 6:
            _page_cache.clear()
        img = P.sheet(SZ, page=1, porthole=10)
        for a in ACTS:
            if a.t1 <= t:
                a.draw(img, 1.0)
        _page_cache[done] = img
    img = _page_cache[done].copy()
    for a in ACTS:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    return img


# ------------------------------------------------------------------ where the pencil point is (page px)
Q1 = B("q1")
A22, A31 = B("a2.2"), B("a3.1")
A32 = B("a3.2")
STUCK = (A31[0] + 40, A31[3] - 4)                          # the start of the third answer's first rule
# air travel: (t, (x, y) page px, lift)
AIR = [
    (2.78, (GROOVE[0] - PX + 250, GROOVE[1] - PY + 30), 26),
    (5.95, (RCX + 140, RCY + 110), 22),                     # the pencil lifts and stays lifted
    (11.15, (RCX + 140, RCY + 110), 22),
    (13.1, (RCX + 520, RCY + 60), 16),
    (13.8, (Q1[0] + 40, Q1[3] + 9), 7),                     # runs along under the first question
    (14.3, (Q1[0] + 800, Q1[3] + 10), 7),
    (20.85, (A22[0] + 60, A22[3] - 4), 16),                 # hangs over the clean second rule
    (21.3, (A22[0] + 64, A22[3] - 4), 16),
    (21.9, STUCK, 16),                                      # STUCK
    (26.0, STUCK, 16),
    (26.3, STUCK, 16),
    (28.95, (A32[0] + 1000, A32[3] - 6), 7),                # back along the line
    (29.1, (A32[0] + 150, A32[3] - 2), 7),
    (29.55, (A32[0] + 230, A32[3] + 30), 18),
]


def _pen(t):
    """(x, y, lift, writing?) of the pencil point on the page at t."""
    for a in ACTS:
        if a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return x, y, (0 if down else 6), True
    keys = [(a.t0, a.tip(0.0)[:2] + (8,)) for a in ACTS] + [(a.t1, a.tip(1.0)[:2] + (8,)) for a in ACTS]
    keys += [(tt, p + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    x, y, l = cam.key(t, keys, "smooth")
    return x, y, l, False


# ------------------------------------------------------------------ the camera at the desk
# (deg, horizon, zoom, look x, look y [desktop px], at x, at y [screen px], head drop, shake)
DESK = (58, 0.36, 0.50, DW / 2 + 75, DH / 2, 480, 194, 0, 2.5)


def _close(px, py, sx=440, sy=300, zoom=0.80, deg=38, shake=2.5):
    return (deg, 0.36, zoom, PX + px, PY + py, sx, sy, 420, shake)


_RINGSHOT = (50, 0.36, 0.84, PX + RCX, PY + RCY, 430, 236, 150, 2.5)
_MARGIN = (50, 0.36, 0.84, PX + RCX + 190, PY + RCY, 430, 236, 150, 2.5)
A11, A21 = B("a1.1"), B("a2.1")
CAMKEYS = [
    (0.0, (0, 0.5, 0.80, PX + SZ[0] / 2, PY + 760, 480, 270, 300, 0.0)),      # flat-on: the blank Porthole Log
    (2.3, DESK, "smoother"),                                                   # sitting down into the seat
    (2.7, DESK),
    (5.6, _RINGSHOT),                                                          # slow push to the ring
    (11.1, _RINGSHOT),
    (11.7, _MARGIN),                                                           # pan right: the margin
    (13.0, _MARGIN),
    (13.8, _close(430, A11[3] - 20)),                                          # nose to the paper at zone 3
    (14.4, _close(430, A11[3] - 20)),
    (16.3, _close(760, A11[3] - 10)),                                          # along with the line
    (16.9, _close(440, A11[3] + 16)),
    (18.2, _close(700, A11[3] + 24)),
    (18.6, _close(520, A11[3] + 24), "smooth"),
    (18.8, _close(520, A11[3] + 24)),
    (19.2, _close(430, A21[3] - 6)),                                           # slide down one question
    (21.4, _close(470, A21[3] + 6)),
    (21.9, DESK[:8] + (0.0,), "smoother"),                                     # pull back; then LOCKED
    (26.25, DESK[:8] + (0.0,)),
    (26.26, _close(470, A31[3] - 10, shake=0.6), "hold"),                      # (the eyes open on the close shot)
    (27.5, _close(620, A31[3] - 6)),
    (28.0, _close(500, A31[3] + 10)),
    (28.9, _close(760, A31[3] + 22)),
    (29.4, _close(470, A31[3] + 22)),
    (30.2, DESK, "smoother"),                                                  # pull back and let go
    (32.0, DESK),
]
SHOOT_ZOOM = 1.035


def _cam(t):
    deg, hor, zoom, lx, ly, ax, ay, drop, shake = cam.key(t, CAMKEYS, "smooth")
    gx, gy = cam.tilt_point(lx, ly, deg, hor, zoom, 700, (0, 0), (DW, DH))
    return dict(deg=deg, hor=hor, zoom=zoom, shift=(ax - gx, ay - gy), drop=drop, shake=shake)


def _tp(c, dx, dy):
    """desktop px -> screen px (before the handheld shoot)."""
    return cam.tilt_point(dx, dy, c["deg"], c["hor"], c["zoom"], 700, c["shift"], (DW, DH))


def _mag(c, dx, dy):
    a, b = _tp(c, dx, dy), _tp(c, dx + 20, dy)
    return (b[0] - a[0]) / 20.0


def _final(x, y):
    return (W / 2 + (x - W / 2) * SHOOT_ZOOM, H / 2 + (y - H / 2) * SHOOT_ZOOM)


# ------------------------------------------------------------------ the desk top picture
_PIC = None
_base = {}


def _slip_pic():
    global _PIC
    if _PIC is None:
        im = Image.open(FILMS.parents[1] / "stills" / "p10.jpg").convert("RGB")
        _PIC = im.crop((70, 70, 570, 570))
    return _PIC


def _desk_base(pencil, sheet):
    key = (pencil, sheet)
    if key not in _base:
        im = Image.new("RGB", (DW, DH), P.DESK)
        P.desk(im)
        P.slip(im, SLIP[0], SLIP[1], 10, CLUE, SLIP_S, 7, picture=_slip_pic())
        if pencil:
            P.pencil(im, GROOVE[0], GROOVE[1], 0, scale=1.9)
        if sheet:
            P.lay(im, P.sheet(SZ, page=1, porthole=10), PX + SZ[0] / 2, PY + SZ[1] / 2)
        _base[key] = im.convert("RGBA")
    return _base[key]


def _sheet_move(t):
    """(dx, lift) of the sheet as it is let go (P11)."""
    return (-150 * ease(t, 31.3, 32.4), 14 * ease(t, 31.0, 31.5))


def _desktop(t):
    in_groove = t < 2.62 or t >= 30.25
    sx, lift = _sheet_move(t)
    pg = page1(t)
    if lift <= 0 and sx == 0:
        im = _desk_base(in_groove, True).copy()
        im.paste(pg, (PX, PY))
    else:
        im = _desk_base(in_groove, False).copy()
        P.lay(im, pg, PX + SZ[0] / 2 + sx, PY + SZ[1] / 2, 0, 1.0, lift=lift)
    return im


# ------------------------------------------------------------------ the hands
def _hand_scale(c, dx, dy):
    return clamp(1.42 * _mag(c, dx, dy), 0.55, 1.5)


def _edge_dir(c, x0, y0, x1, y1):
    a, b = _tp(c, x0, y0), _tp(c, x1, y1)
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _right_hand(fr, c, t, still):
    ht = 21.9 if still else t
    if t < 2.62:                                           # P1: the finger on the slip, twice; then up for the pencil
        sp = (SLIP[0] - 96, SLIP[1] + 6)
        x, y, lift = cam.key(t, [(0.5, (1950, 2500, 30)), (1.25, sp + (0,), "out"), (1.55, sp + (0,)), (1.75, (sp[0] + 30, sp[1] + 50, 20)),
                                 (2.0, (sp[0] + 4, sp[1] - 6, 0)), (2.25, (sp[0] + 4, sp[1] - 6, 0)), (2.62, (GROOVE[0] + 250, GROOVE[1] + 30, 14))])
        s = _hand_scale(c, x, y)
        P.hand(fr, *_tp(c, x, y), pose="point", tone=TONE, scale=s, t=t, lift=lift * s, arm=74)
        return
    sx, slift = _sheet_move(t)
    if t >= 30.25:                                         # P11: the pencil is in the groove; take the sheet's right edge
        ex, ey = PX + SZ[0] - 8 + sx, PY + 800
        if t < 30.95:
            x, y, lift = cam.key(t, [(30.25, (GROOVE[0] + 250, GROOVE[1] + 40, 16)), (30.95, (ex, ey, 10))])
            s = _hand_scale(c, x, y)
            P.hand(fr, *_tp(c, x, y), pose="point", tone=TONE, scale=s, t=t, lift=lift * s, arm=66)
        else:
            s = _hand_scale(c, ex, ey)
            hx, hy = _tp(c, ex, ey)
            P.hand(fr, hx, hy - slift * 0.5, pose="pass", tone=TONE, scale=s, t=t, arm=48,
                   edge=_edge_dir(c, ex, ey - 100, ex, ey + 100))
        return
    if t >= 29.55:                                         # carrying the pencil up to the groove
        x0, y0 = D(A32[0] + 230, A32[3] + 30)
        x, y, lift = cam.key(t, [(29.55, (x0, y0, 18)), (30.25, (GROOVE[0] + 250, GROOVE[1] + 30, 14))])
        s = _hand_scale(c, x, y)
        P.hand(fr, *_tp(c, x, y), pose="write", tone=TONE, scale=s, t=t, lift=lift * s, arm=58)
        return
    px, py, lift, writing = _pen(t)
    dx, dy = D(px, py)
    s = _hand_scale(c, dx, dy)
    hov = (not writing) and lift >= 15
    if 25.45 <= t < 25.8:                                  # the one small movement allowed in the hold: a dip, no mark
        lift = 16 - 9 * math.sin(math.pi * ramp(t, 25.45, 25.8))
    x, y = _tp(c, dx, dy)
    if hov:
        P.hand(fr, x, y, pose="hover", tone=TONE, scale=s, t=ht, lift=lift * s, arm=58)
    else:
        P.hand(fr, x, y, pose="write", tone=TONE, scale=s, t=t, lift=lift * s, arm=58)


def _left_hand(fr, c, t, still):
    ht = 21.9 if still else t
    sx, slift = _sheet_move(t)
    rest = D(120, 730)
    if t < 30.5:
        x, y, lift = cam.key(t, [(1.5, (rest[0] - 500, rest[1] + 900, 24)), (2.5, rest + (0,), "out")])
        s = _hand_scale(c, x, y)
        P.hand(fr, *_tp(c, x, y), pose="hold", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=146)
        return
    ex, ey = PX + 8 + sx, PY + 800
    if t < 30.95:
        x, y, lift = cam.key(t, [(30.5, rest + (0,)), (30.7, (rest[0] - 60, rest[1] + 120, 12)), (30.95, (ex, ey, 8))])
        s = _hand_scale(c, x, y)
        P.hand(fr, *_tp(c, x, y), pose="hold", tone=TONE, scale=s, flip=True, t=t, lift=lift * s, arm=140)
    else:
        s = _hand_scale(c, ex, ey)
        hx, hy = _tp(c, ex, ey)
        P.hand(fr, hx, hy - slift * 0.5, pose="pass", tone=TONE, scale=s, flip=True, t=t, arm=138,
               edge=_edge_dir(c, ex, ey - 100, ex, ey + 100))


def _head_layer(c, t, still):
    lay = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    if c["drop"] >= 400:
        return None
    turn = 0.5 * (ease(t, 23.6, 24.0) - ease(t, 24.8, 25.2)) + 0.35 * (ease(t, 0.9, 1.3) - ease(t, 2.2, 2.6))
    tilt = 5 * (ease(t, 23.6, 24.0) - ease(t, 24.8, 25.2))
    P.head_back(lay, 60 + 770, 60 + 632 + c["drop"], TONE, 1.2, tilt=tilt, hair="short", turn=turn, t=21.9 if still else t)
    return lay


def _desk_frame(t):
    """The pilot's seat at t: desk, sheet as written so far, slip, hands, the back of the head. A full 960x540 frame."""
    c = _cam(t)
    still = 21.9 <= t < 26.25
    fr = cam.tilt(_desktop(t), c["deg"], c["hor"], c["zoom"], 700, c["shift"], bg=(92, 66, 44), shadow=0)
    _left_hand(fr, c, t, still)
    _right_hand(fr, c, t, still)
    layers = [(fr, 1.0)]
    head = _head_layer(c, t, still)
    if head is not None:
        layers.append((head, 0.62))
    focus = cam.key(t, [(2.3, 1.0), (2.7, 0.66), (3.5, 1.0)]) if 2.3 < t < 3.5 else 1.0
    return cam.shoot(layers, zoom=SHOOT_ZOOM, focus=focus, aperture=5, shake=c["shake"], t=t)


# ------------------------------------------------------------------ the thought (inside the drawn ring)
PENCIL_LIGHT = (232, 232, 222)
_JAWS = [np.array(Wd._dense(s), np.float32) for s in Wd.PILOT_STROKES if s["part"] == "jaw"]
_OUTS = [np.array(Wd._dense(s), np.float32) for s in Wd.PILOT_STROKES if s["part"] == "outside"]
_JW = [s["weight"] for s in Wd.PILOT_STROKES if s["part"] == "jaw"]
_water_cache = {}


def _water(t, dim=0.62):
    k = int(t * 12)
    if k not in _water_cache:
        if len(_water_cache) > 4:
            _water_cache.clear()
        im = Image.new("RGB", (W + 160, H + 90), (0, 0, 0))
        w = Image.new("RGB", (W, H))
        Wd.river_back(w, t, 0, 0.3)
        im.paste(w.resize(im.size, Image.BILINEAR))
        _water_cache[k] = im.point(lambda v: int(v * dim))
    return _water_cache[k]


def _xf(pts, sc, org, ang=0.0, pin=(0, 0), off=(0, 0)):
    """photograph px (from the ring's centre) -> screen: turned by ang about pin (photo px), scaled, moved."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    x, y = pts[:, 0] - pin[0], pts[:, 1] - pin[1]
    X = pin[0] + x * ca - y * sa
    Y = pin[1] + x * sa + y * ca
    return list(zip((org[0] + X * sc + off[0]).tolist(), (org[1] + Y * sc + off[1]).tolist()))


def _pin(lay, x, y, r=9, weight=1.0):
    P.graphite(lay, [[(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(0, 6.9, 22)]], 2.6, weight, 3, PENCIL_LIGHT)
    P.graphite(lay, [[(x - 2, y), (x + 2, y)]], 3.2, weight, 4, PENCIL_LIGHT)


J_SC, J_ORG = 1.85, (452, 372)           # the first jaw, standing in the water
J_PIN = (-107, 36)                       # its back corner
O_SC, O_ORG = 1.75, (-430, 300)          # the two rows (photo x 355..688 -> screen 190..775)
O_PIN = (352, -32)


def _thought_parts(t):
    """Pencil-line layer (RGBA, frame size + margin) of what is being pictured at t, and the clam behind it."""
    M = 80
    lay = Image.new("RGBA", (W + 2 * M, H + 2 * M), (0, 0, 0, 0))
    org = (J_ORG[0] + M, J_ORG[1] + M)
    rs = random.Random(4)
    clam = None
    if t < 9.3:
        # the strokes fly in one at a time and lock (7.1 to 7.9); it tries its one hinge and cannot (7.9 to 8.3);
        # it falls apart (8.3 to 9.0)
        rattle = 0.0
        if 7.9 <= t < 8.35:
            k = (t - 7.9) / 0.45
            rattle = 3.2 * math.sin(k * math.pi * 6) * (1 - 0.5 * k)
        for i, pts in enumerate(_JAWS):
            ta = 7.12 + i * 0.05
            u = ease(t, ta, ta + 0.26)
            ang0, dx0, dy0 = rs.uniform(-70, 70), rs.uniform(-420, 420), rs.uniform(-330, 240)
            if u <= 0:
                continue
            ang = ang0 * (1 - u)
            off = (dx0 * (1 - u), dy0 * (1 - u))
            fall = ramp(t, 8.3 + 0.03 * (i % 4), 9.05)
            gone = 1.0
            teeth = i >= 5
            fa, fx, fy = rs.uniform(-55, 55), rs.uniform(-60, 60), rs.uniform(90, 210)
            da, ddx, ddy = rs.uniform(-18, 18), rs.uniform(-1, 1), rs.uniform(-1, 0.3)
            if fall > 0:
                if teeth:                                   # the teeth drop out of the box and hang
                    g = fall * fall
                    ang += fa * smooth(fall)
                    off = (off[0] + fx * fall, off[1] + fy * g + 10 * math.sin(fall * 9 + i) * (1 - fall))
                else:                                       # the box lines drift off
                    ang += da * fall
                    off = (off[0] + ddx * 260 * fall, off[1] + ddy * 200 * fall)
                    gone = 1 - smooth(fall)
            if teeth:
                gone = 1 - ease(t, 8.95, 9.3)
                ang += rattle * (1.0 if i % 2 else 0.6)
            if gone <= 0.02:
                continue
            pin = J_PIN if rattle else (float(pts[:, 0].mean()), float(pts[:, 1].mean()))
            P.graphite(lay, [_xf(pts, J_SC, org, ang, pin, off)], 3.4 + 2.4 * _JW[i], (0.5 + 0.6 * _JW[i]) * u * gone, i, PENCIL_LIGHT)
        if 7.85 <= t < 8.5:
            _pin(lay, org[0] + J_PIN[0] * J_SC, org[1] + J_PIN[1] * J_SC, 10, 1 - ease(t, 8.3, 8.5))
    if t >= 8.95:
        # the loose zigzags come back as two rows on one pin; this one opens and shuts, twice
        org2 = (O_ORG[0] + M, O_ORG[1] + M)
        gape = 0.0
        if 9.42 <= t < 10.06:
            k = ((t - 9.42) / 0.32) % 1.0
            gape = 30 * math.sin(math.pi * min(1.0, k * 1.15)) ** 0.8
        px, py = org2[0] + O_PIN[0] * O_SC, org2[1] + O_PIN[1] * O_SC
        for i, pts in enumerate(_OUTS):
            ta = 8.98 + (0, 0.05, 0.12, 0.18)[i]
            u = ease(t, ta, ta + 0.3)
            if u <= 0:
                continue
            ang0, dy0 = rs.uniform(-40, 40), rs.uniform(120, 260)
            upper = i < 2
            ang = ang0 * (1 - u) + (-gape * 0.62 if upper else gape * 0.38)
            pin = O_PIN if u >= 1 else (float(pts[:, 0].mean()), float(pts[:, 1].mean()))
            P.graphite(lay, [_xf(pts, O_SC, org2, ang, pin, (0, dy0 * (1 - u)))], 4.2 if i in (1, 2) else 3.0,
                       (0.62 if i in (1, 2) else 0.4) * u, 20 + i, PENCIL_LIGHT)
        _pin(lay, px, py, 11, 0.8 * ease(t, 9.25, 9.42))
        a = 0.25 * (ease(t, 9.36, 9.5) - ease(t, 9.98, 10.08))
        if a > 0.01:                                       # what the small picture on the slip was, faintly, for two flaps
            clam = Image.new("RGBA", lay.size, (0, 0, 0, 0))
            Wd.clam_pa(clam, px, py + 6, 2.35, gape=max(2.0, gape), t=t, split=0.38, alpha=1.0)
            clam.putalpha(clam.getchannel("A").point(lambda v: int(v * a)))
    return lay, clam


def _thought(t):
    """Inside the thought: dark river, no tin, no Turkey; only the picture, in pencil line. A full frame."""
    lay, clam = _thought_parts(t)
    layers = [(_water(t), 3.0)]
    if clam is not None:
        layers.append((clam, 1.25))
    layers.append((lay, 1.0))
    return cam.shoot(layers, x=cam.key(t, [(7.0, -6), (10.2, 30)], "linear"), y=0, zoom=1.0,
                     dolly=cam.key(t, [(7.0, 0.0), (10.2, 0.07)], "linear"), bg=(20, 44, 52))


# the small thought over the desk while line 1 is written: the pale zigzags snap into little crinkle-cut pieces
def _fries_thought(t):
    im = _water(t, 0.7).resize((W, H), Image.BILINEAR)
    u = ramp(t, 14.7, 16.3)
    snap = ease(t, 15.05, 15.35)
    rs = random.Random(8)
    sc, org = 1.9, (-500, 330)
    for i in (1, 2):
        pts = _OUTS[i]
        n = len(pts)
        pieces = 6
        for k in range(pieces):
            seg = pts[int(k * n / pieces): int((k + 1) * n / pieces) + 1]
            cx, cy = float(seg[:, 0].mean()), float(seg[:, 1].mean())
            dx, dy, da = rs.uniform(-50, 50), rs.uniform(-70, 70), rs.uniform(-80, 80)
            ph = rs.uniform(0, 6.28)
            drift = (dx * snap + 14 * math.sin(t * 1.6 + ph) * snap, dy * snap + 10 * math.sin(t * 2.1 + ph * 2) * snap)
            fry_a = ease(t, 15.2, 15.7)
            sx, sy = org[0] + cx * sc + drift[0], org[1] + cy * sc + drift[1]
            if fry_a < 1:
                P.graphite(im, [_xf(seg, sc, org, da * snap, (cx, cy), drift)], 5.0, 0.8 * (1 - fry_a), 30 + k + i * 9, PENCIL_LIGHT)
            if fry_a > 0:
                tile = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
                Wd.fry(tile, 110, 110, 1.15, 90 + da * snap + 10 * math.sin(t * 1.9 + ph), seed=k + i * 5)
                if fry_a < 1:
                    tile.putalpha(tile.getchannel("A").point(lambda v: int(v * fry_a)))
                im.paste(tile, (int(sx - 110), int(sy - 110)), tile)
    return im


# ------------------------------------------------------------------ the film
DIVE_IN = (6.0, 7.1)
DIVE_OUT = (10.1, 11.1)


def _ring_on_screen(t):
    c = _cam(t)
    return _final(*_tp(c, PX + RCX, PY + RCY))


def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < DIVE_IN[0] or t >= DIVE_OUT[1]:
        fr = _desk_frame(t)
        if 26.0 <= t < 26.5:                                # the blink: shut on the stuck desk, open on the close shot
            wide = _desk_frame(25.99) if t < 26.25 else fr
            fr = cam.blink(wide, ramp(t, 26.0, 26.5), to=_desk_frame(max(t, 26.26)))
        tu = cam.key(t, [(14.6, 0), (15.0, 1), (16.05, 1), (16.4, 0)], "linear")
        if tu > 0:
            fr = cam.thought(fr, _fries_thought(t), 806, 128, 95, tu, wobble=5, t=t, dim=0)
        return fr
    if t < DIVE_IN[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, ramp(t, *DIVE_IN), spin=40)
    if t < DIVE_OUT[0]:
        return _thought(t)
    rx, ry = _ring_on_screen(t)
    return cam.dive(_desk_frame(t), _thought(t), rx, ry, 1 - ramp(t, *DIVE_OUT))


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB") if fr.mode != "RGB" else fr)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m10_pilot.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.2, 1.4, 2.4, 4.0, 5.4, 6.4, 6.8, 7.7, 8.2, 8.7, 9.7, 10.5, 12.4, 13.4, 15.4, 16.5,
                                              18.4, 20.2, 21.0, 21.6, 23.0, 24.2, 26.1, 26.3, 27.3, 27.9, 28.7, 29.35, 30.0, 30.9, 31.4, 31.9]
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
