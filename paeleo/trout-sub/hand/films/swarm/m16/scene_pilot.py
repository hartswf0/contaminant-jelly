"""m16 · scene_pilot · the pilot fills in page 1 of Porthole Log 16 (board beats P1 to P9, 0.0 to 29.0 s).

The slip and the blank sheet on the desk; the sub copied from the slip piece by piece, small and high in the ring,
with looks across at the slip; the window scribbled black with nobody in it; a dive through the drawn ring into the
thought, where a faint turkey head puts itself together at the lower left (where the slip has it), will not hold,
slides across behind the sub and comes together again on the right, leaving three loose lines where they stopped;
back up; the head and the loose lines drawn faintly; the point crossing the empty two thirds of the ring and
leaving them empty; the finger stopping at each of the stem's two question marks and one line written
("threehead", then "ed", then "ed" gone over); eyes up to the printed clue and down; "wave athis twin", the hand
lifted, "turkey" set down higher and bigger; the point resting under the stem's "use up" and `useinguphisenergy`
in one unbroken string, "rgy" climbing and gone over; the sheet taken by its edge.

Seats are full pictures: `_desk_frame(t)` (the desk top laid back by cam.tilt, with the slip, the sheet as written
so far, both hands and the back of the head from people.py), `_thought(t)` (the pilot's own pencil sub hanging in
a few pencil lines of water) and two small looks into a thought (`_necks_inner`, `_wave_inner`, from the c16
world). Moves between them are cam.dive, cam.whip and cam.thought; moves at the desk are one keyframed tilt camera
(`_cam`). Nothing is cross-faded.

Exposes SECONDS, CAPTIONS, draw(t, ink); and for the other units page1(t) (the written sheet at film time t,
SZ = 1216 x 1568; page1(SECONDS) is the page as the pilot left it).

    python3 films/swarm/m16/scene_pilot.py <out.png> [t ...]     # contact sheet
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
C16 = FILMS / "swarm" / "c16"
for p in (str(FILMS), str(C16)):
    if p not in sys.path:
        sys.path.insert(0, p)

import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402
from kit import Ink, FPS, clamp, lerp, ramp, smooth, ease  # noqa: E402

SECONDS = 29.0
CAPTIONS = [
    (20.0, 22.5, "A giant three-headed monster."),
    (23.0, 25.5, "Wave at his twin turkey."),
    (26.2, 28.7, "Using up his energy."),
]

TONE = "ochre"
HAIR = "bun"
W, H = 960, 540

# ------------------------------------------------------------------ the desktop (a picture bigger than the frame)
SZ = (1216, 1568)                       # the sheet, in desktop pixels
DW, DH = 2400, 2100                     # the desk top
PX, PY = 442, 250                       # the sheet's top-left corner on it
SLIP = (2010, 640)                      # the slip, beside the sheet, upper right
SLIP_S, SLIP_A = 2.2, 5.0
CLUE = "Identical twin Turkey Sub waving back"
XH = 22.0                               # the pilot's x-height


def B(name, page=1):
    return P.where(page, name, SZ)


def D(x, y):
    """page px -> desktop px"""
    return (PX + x, PY + y)


RING = B("ring.in")
RCX, RCY = (RING[0] + RING[2]) / 2, (RING[1] + RING[3]) / 2
RR = (RING[2] - RING[0]) / 2
SC = round(RR / 214.0 * 100) / 100.0    # world.pilot_drawing's scale: screen px per sheet unit


def UP(u, v):
    """sheet units (from the ring's centre; the glass radius is 214) -> page px"""
    return (RCX + u * SC, RCY + v * SC)


def _raw(x, y):
    """world.py's tracing coordinates -> sheet units"""
    return ((x - 460.0) / 780.0 * 214.0, (y - 924.0) / 780.0 * 214.0)


WIN = UP(*_raw(401, 402))               # the round window
MID = (RCX - 6, RCY + 62)               # the bare paper in the lower part of the ring


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
    """Pencil polylines drawn in order (the going-over of letters already there)."""
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


A11, A12, A21, A31, A32 = B("a1.1"), B("a1.2"), B("a2.1"), B("a3.1"), B("a3.2")
Q1, Q2, Q3 = B("q1"), B("q2"), B("q3")
QM1, QM2 = (377, Q1[3] + 8), (700, Q1[3] + 8)          # under the stem's two question marks
USE_UP = (316, Q3[3] + 9)                              # under "use up" in the third stem
CLUE_PT = (394, 306)                                   # under "twin Turkey" in the printed clue
PASS_PT = (214, 1431)                                  # under "Pass your paper left"


def _sl0(seed, text):
    """The slant people.write_plan will give this text with this seed (its own first four draws)."""
    rs = random.Random(seed * 7919 + len(text) * 131 + sum(ord(c) * (i + 1) for i, c in enumerate(text)))
    rs.uniform(0, 1), rs.uniform(0, 1), rs.uniform(0, 1)
    return rs.uniform(-0.03, 0.10)


def _seed(text, want, seeds=range(160, 170)):
    """One hand along a line: the pilot's seed whose slant is nearest `want`."""
    return min(seeds, key=lambda k: abs(_sl0(k, text) - want))


def _after(prev, t0, t1, text, gap, dy0=0.0, dy1=0.0, size=XH, weight=1.0, box=None):
    """A Write that carries straight on from `prev` (a Write) with `gap` px of paper between."""
    sd = _seed(text, _sl0(prev.seed, prev.text))
    xp = max(p[0] for ln in prev.plan.strokes for p in ln)
    b = (xp, box[1] + dy0, box[2], box[3] + dy1)
    pl = P.write_plan(b, text, sd, size)
    x0 = min(p[0] for ln in pl.strokes for p in ln)
    return Write(t0, t1, (xp + (xp + gap - x0), b[1], b[2], b[3]), text, sd, weight, size)


def _build():
    acts = []
    # P7: line 1. "threehead" in one run with no gap, then "ed", then "ed" gone over, then "monster".
    a = Write(17.6, 18.74, (A11[0] + 10, A11[1], A11[2], A11[3]), "a giant threehead", 160)
    ed = _after(a, 18.8, 19.0, "ed", 0.2 * XH, box=A11)
    go = Lines(19.04, 19.32, _go_over(ed.plan.strokes, 1, 5), 1.3, 3.3, 9)
    mo = _after(ed, 19.42, 20.0, "monster", 0.8 * XH, box=A11)
    acts += [a, ed, go, mo]
    # P8: line 2 carries on from the stem. "at his" joined; the hand lifts; "turkey" higher, bigger, its y through the rule.
    w = Write(21.2, 22.2, (A21[0] + 12, A21[1], A21[2], A21[3]), "wave athis twin", 163)
    tk = _after(w, 22.5, 23.0, "turkey", 1.0 * XH, -10, -6, XH * 1.22, box=A21)
    acts += [w, tk]
    # P9: line 3, one string; the last three letters climb and are gone over.
    s = Write(24.0, 25.84, (A31[0] + 30, A31[1], A31[2], A31[3]), "useinguphisene", 165)
    r_ = _after(s, 25.84, 25.9, "r", 0.2 * XH, -4, -3, XH * 1.04, box=A31)
    g_ = _after(r_, 25.9, 25.97, "g", 0.2 * XH, -8, -7, XH * 1.1, box=A31)
    rgy = _after(g_, 25.97, 26.03, "y", 0.2 * XH, -12, -11, XH * 1.14, box=A31)
    go3 = Lines(26.04, 26.2, _go_over(r_.plan.strokes + g_.plan.strokes + rgy.plan.strokes, 1, 7), 1.3, 3.2, 11)
    acts += [s, r_, g_, rgy, go3]
    acts.sort(key=lambda x: x.t0)
    return acts, dict(a=a, ed=ed, mo=mo, w=w, tk=tk, s=s, rgy=rgy)


ACTS, _L = _build()

# the drawing itself (world.pilot_drawing, part by part): how much of each part is on the page at t
DRAWN = {
    "box": [(3.6, 0.0), (4.5, 1.0)],
    "dome": [(4.5, 0.0), (5.0, 1.0)],
    "blocks": [(5.6, 0.0), (6.15, 1.0)],
    "right": [(6.15, 0.0), (6.6, 1.0)],
    "window": [(6.6, 0.0), (6.9, 1.0)],
    "scribble1": [(6.9, 0.0), (7.4, 1.0)],
    "scribble2": [(7.4, 0.0), (7.95, 1.0)],          # the second going-round starts D frames after the first
    "head": [(13.6, 0.0), (14.4, 1.0)],
    "faint": [(14.4, 0.0), (14.8, 1.0)],
}
DRAW_WIN = [(g, k[0][0], k[-1][0]) for g, k in DRAWN.items()]


def _drawn(t):
    return {g: cam.key(t, k, "linear") for g, k in DRAWN.items()}


def _draw_tip(g, f):
    x, y, down = Wd.pilot_tip(RCX, RCY, clamp(f, 1e-4, 1.0), SC, part=g)
    return x, y, down and f < 1


_page_cache = {}


def page1(t):
    """The pilot's page as it stands at film time t: a fresh PIL image, SZ = 1216 x 1568 (use P.where(1, name, SZ))."""
    key = (tuple(i for i, a in enumerate(ACTS) if t >= a.t1), tuple(g for g, t0, t1 in DRAW_WIN if t >= t1))
    if key not in _page_cache:
        if len(_page_cache) > 6:
            _page_cache.clear()
        img = P.sheet(SZ, page=1, porthole=16)
        for g, t0, t1 in DRAW_WIN:
            if t >= t1:
                Wd.pilot_drawing(img, RCX, RCY, 1.0, SC, part=g)
        for a in ACTS:
            if a.t1 <= t:
                a.draw(img, 1.0)
        _page_cache[key] = img
    img = _page_cache[key].copy()
    for g, t0, t1 in DRAW_WIN:
        if t0 < t < t1:
            Wd.pilot_drawing(img, RCX, RCY, cam.key(t, DRAWN[g], "linear"), SC, part=g)
    for a in ACTS:
        if a.t0 <= t < a.t1:
            a.draw(img, a.u(t))
    return img


# ------------------------------------------------------------------ where the pencil point is (page px)
OVER_RING = (RCX - 30, RCY - 96)
AWAY = (RCX + 760, RCY + 620)
_E1 = _L["mo"].plan.end
_E2 = _L["w"].plan.end
_E3 = _L["rgy"].plan.end
_S2 = _L["w"].plan.start
POINT = [(16.02, 17.47), (27.62, 28.38)]              # the index finger; the pencil is laid in the groove
PASSING = (28.38, SECONDS + 1)                        # the right hand has the sheet by its edge
NOLIFT = (24.0, 26.2)                                 # line 3: the point hardly leaves the paper
AIR = [  # (t, (x, y) page px, lift)
    (0.0, OVER_RING, 18), (3.46, OVER_RING, 18),      # hovering over the empty ring; a look at the slip
    (5.06, (RCX + 24, RCY - 92), 16), (5.52, (RCX + 24, RCY - 92), 16),          # held while she looks again
    (8.02, (WIN[0] + 6, WIN[1] + 4), 8), (8.5, AWAY, 40),                        # the hand lifts out of frame
    (13.0, AWAY, 40), (13.52, UP(*_raw(1080, 440)), 12),                         # and is back when we are
    (14.84, UP(*_raw(700, 600)), 6), (15.12, MID, 6), (15.14, MID, 16), (15.42, MID, 16),   # over the empty part: stops
    (15.6, (MID[0] + 40, MID[1] + 60), 18), (15.98, (RCX + 420, 1080), 30),      # and goes away down the page
    (16.04, (60, Q1[3] + 40), 10), (16.24, (118, Q1[3] + 8), 0),                 # the finger, along the printed stem
    (16.56, QM1, 0), (16.8, QM1, 0),                                             # stops on the first question mark
    (17.08, QM2, 0), (17.36, QM2, 0),                                            # goes on; stops on the second
    (17.46, (QM2[0] - 200, A11[3] - 10), 14), (17.48, (A11[0] + 60, A11[3] - 8), 14),
    (20.02, (_E1[0] + 14, _E1[1] - 4), 16), (21.0, (_S2[0] + 10, _S2[1] - 6), 16),
    (22.36, (_E2[0] + 64, _E2[1] - 16), 14),                                     # the hand lifts clear, the heel moves right
    (23.06, (_L["tk"].plan.end[0] + 10, _L["tk"].plan.end[1] - 4), 9),
    (23.42, USE_UP, 3), (23.98, USE_UP, 3),                                      # the point rests under "use up"
    (26.42, (_E3[0] + 34, _E3[1] + 8), 16), (27.5, (_E3[0] + 34, _E3[1] + 8), 16),          # the hand rests
    (27.64, (PASS_PT[0] + 180, PASS_PT[1] + 50), 12), (27.84, PASS_PT, 0), (28.34, PASS_PT, 0),   # "Pass your paper left"
]


def _pen_keys():
    keys = []
    for a in ACTS:
        if a.tip is not None:
            keys += [(a.t0, a.tip(0.0)[:2] + (7,)), (a.t1, a.tip(1.0)[:2] + (7,))]
    for g, t0, t1 in DRAW_WIN:
        keys += [(t0, _draw_tip(g, 0.0)[:2] + (7,)), (t1, _draw_tip(g, 1.0)[:2] + (7,))]
    keys += [(tt, tuple(p) + (l,)) for tt, p, l in AIR]
    keys.sort(key=lambda k: k[0])
    return keys


PEN_KEYS = _pen_keys()


def _pen(t):
    """(x, y, lift, pose) of the pencil point (or the fingertip, or the thumb on the sheet's edge) on the page at t."""
    if t >= PASSING[0]:
        return SZ[0] - 2, 1150, 0, "pass"
    for a, b in POINT:
        if a <= t < b:
            x, y, l = cam.key(t, PEN_KEYS, "smooth")
            return x, y, l, "point"
    for a in ACTS:
        if a.tip is not None and a.t0 <= t < a.t1:
            x, y, down = a.tip(a.u(t))
            return x, y, (0 if down or NOLIFT[0] <= t < NOLIFT[1] else 5), "write"
    for g, t0, t1 in DRAW_WIN:
        if t0 <= t < t1:
            x, y, down = _draw_tip(g, cam.key(t, DRAWN[g], "linear"))
            return x, y, (0 if down else 5), "write"
    x, y, l = cam.key(t, PEN_KEYS, "smooth")
    return x, y, l, ("hover" if l >= 15 else "write")


# stopped: nothing moves (the hand's own time is held, and the camera's drift with it)
STILL = [(15.14, 15.42), (23.44, 23.98)]


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
TOP = (0, 0.5, 0.40, SCX + 330, PY + 600, 480, 270, 330)
SEAT = (62, 0.36, 0.50, SCX + 130, SCY - 40, 480, 196, 0)
RINGSHOT = (50, 0.36, 1.5, PX + RCX + 30, PY + RCY - 70, 450, 226, 300)
WINSHOT = (46, 0.36, 2.3, PX + WIN[0] + 30, PY + WIN[1] + 20, 440, 232, 430)
SLIPSHOT = (36, 0.36, 2.5, SLIP_PIC[0] + 40, SLIP_PIC[1], 480, 262, 430)


def _close(px, py, sx=440, sy=300, zoom=0.92, deg=38):
    return (deg, 0.36, zoom, PX + px, PY + py, sx, sy, 430)


C_Q1 = _close(470, Q1[3] + 16, 470, 250, 0.98)
C_A1 = _close(430, A11[3] - 14)
C_A1R = _close(620, A11[3] - 14)
CLUESHOT = _close(400, 290, 470, 236, 1.3, 12)
C_A2 = _close(300, A21[3] - 14)
C_A3 = _close(430, A31[3] - 16)
ZONE3 = (44, 0.36, 0.5, PX + 660, PY + 1290, 480, 250, 430)
GOING = (44, 0.36, 0.5, PX + 560, PY + 1290, 480, 250, 430)
CAMKEYS = [
    (0.0, TOP),                                         # straight down on the desk: the slip and the blank sheet
    (0.5, TOP),
    (2.5, SEAT, "smoother"),                            # coming down into the seat
    (2.62, SEAT),
    (3.1, SLIPSHOT),                                    # across to the slip ...
    (3.24, SLIPSHOT),
    (3.6, RINGSHOT),                                    # ... and back to the ring
    (6.6, RINGSHOT),
    (8.0, WINSHOT),                                     # the slow push-in on the window
    (10.0, WINSHOT),
    (10.5, RINGSHOT, "hold"),                           # (we are in the thought; the eye comes back to the whole ring)
    (15.6, RINGSHOT),
    (16.2, C_Q1),                                       # down the page to zone 3
    (17.3, C_Q1),
    (17.8, C_A1),
    (18.6, C_A1),
    (19.7, C_A1R),                                      # along with the line
    (20.3, C_A1R),
    (20.5, C_A2, "hold"),                               # (eyes up at the clue; they come down one question lower)
    (23.0, C_A2),
    (23.4, C_A3),                                       # one question down
    (26.2, C_A3),
    (27.5, ZONE3),                                      # easing back to the whole of zone 3
    (28.2, ZONE3),
    (29.0, GOING, "in"),                                # already going with the sheet
]
SHAKE = [(0.0, 0.0), (2.5, 2.5), (15.0, 2.0), (15.14, 0.0), (15.42, 0.0), (15.7, 2.0), (23.3, 2.0), (23.44, 0.0), (23.98, 0.0),
         (24.3, 2.0), (29.0, 2.0)]
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
    """The slip's small picture, handmade from the c16 world as the deck picture has it: the tin with its lit window
    and a turkey in it, a trout under it, a pale turkey head low on the left."""
    global _slip_im
    if _slip_im is None:
        ink = Ink(1.0, 24)
        Wd.river(ink, 1.0, 0.0, 0)
        Wd.tin(ink, 512, 232, 0.62, 1.0, **Wd.wave_pose(0.35, 1.0, 0.0))
        Wd.trout(ink, 566, 392, 0.62, 1.0, kind=0)
        ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        Wd.turkey(ghost, 318, 468, 0.95, "calm", 1.0, flip=True, drop=False)
        g = np.asarray(ghost, np.float32)
        g[..., :3] = g[..., :3] * 0.35 + np.array([188, 222, 206], np.float32) * 0.65      # pale, the colour of the glass
        g[..., 3] *= 0.46
        ink.img.paste(Image.fromarray(g.astype(np.uint8), "RGBA"), (0, 0), Image.fromarray(g[..., 3].astype(np.uint8)))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        Wd.river_plane(ink, "front", 1.0)
        _slip_im = ink.img.convert("RGB").crop((262, 40, 722, 500))
    return _slip_im


def _desk_base(sheet):
    if sheet not in _base:
        im = Image.new("RGB", (DW, DH), P.DESK)
        P.desk(im)
        pic = _slip_pic()
        P.slip(im, SLIP[0], SLIP[1], 16, CLUE, SLIP_S, SLIP_A, picture=pic)
        n = int(108 * SLIP_S)                           # the picture again at the slip's own size, so it is sharp close to
        big = pic.resize((n, n), Image.LANCZOS).convert("RGBA").rotate(-SLIP_A, Image.BICUBIC, expand=True)
        im.paste(big, (int(SLIP_PIC[0] - big.size[0] / 2), int(SLIP_PIC[1] - big.size[1] / 2)), big)
        if sheet:
            P.lay(im, P.sheet(SZ, page=1, porthole=16), SCX, SCY)
        _base[sheet] = im.convert("RGBA")
    return _base[sheet]


def _sheet_dx(t):
    return -170 * smooth(ramp(t, 28.5, 29.4))


def _desktop(t):
    dx = _sheet_dx(t)
    pg = page1(t)
    if dx == 0:
        im = _desk_base(True).copy()
        im.paste(pg, (PX, PY))
    else:
        im = _desk_base(False).copy()
        P.lay(im, pg, SCX + dx, SCY)
    return im


# ------------------------------------------------------------------ the hands and the head
def _hand_scale(c, dx, dy):
    return clamp(1.42 * _mag(c, dx, dy), 0.5, 2.0)


def _right_hand(fr, c, t, pen=None):
    px, py, lift, pose = pen or _pen(t)
    hold = _held(t)
    ht = t if hold is None else hold
    dx, dy = D(px + _sheet_dx(t), py)
    s = _hand_scale(c, dx, dy)
    x, y = _tp(c, dx, dy)
    if pose == "pass":
        P.hand(fr, x, y, pose="pass", tone=TONE, scale=s, t=ht, arm=62, edge=90)
    else:
        arm = cam.key(t, [(8.0, 80), (13.0, 80), (15.9, 80), (16.1, 58)]) if pose in ("write", "hover") else 58
        if pen is not None and pen[1] < 400:
            arm = 44                                    # up at the clue: the pencil stands steeper, clear of the print
        P.hand(fr, x, y, pose=pose, tone=TONE, scale=s, t=ht, lift=lift * s, arm=arm)


LREST = (640, 206)                                     # the left palm; its sleeve lies along the Pilot name line


def _left_hand(fr, c, t):
    hold = _held(t)
    ht = t if hold is None else hold
    x, y, lift = cam.key(t, [(0.0, LREST + (0,)), (28.05, LREST + (0,)), (28.5, (LREST[0] - 60, LREST[1] - 30, 20))])
    dx, dy = D(x + _sheet_dx(t) * 0.3, y)
    s = 0.7 * _hand_scale(c, dx, dy)
    P.hand(fr, *_tp(c, dx, dy), pose="hold", tone=TONE, scale=s, flip=True, t=ht, lift=lift * s, arm=180)


def _head_layer(c, t):
    if c["drop"] >= 400:
        return None
    lay = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    look = ease(t, 2.66, 3.0) - ease(t, 3.26, 3.56) + ease(t, 5.0, 5.2) - ease(t, 5.4, 5.6)      # to the slip, on the right, and back
    P.head_back(lay, 60 + 770, 60 + 650 + c["drop"], TONE, 1.05, tilt=6 * look, hair=HAIR, turn=0.75 * look, t=t)
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
    # the rack: soft as the eye lands on the slip, sharp; soft as it comes back to the ring, sharp
    focus = cam.key(t, [(2.7, 1.0), (2.96, 0.72), (3.2, 1.0), (3.3, 1.0), (3.5, 0.76), (3.72, 1.0)])
    return cam.shoot(layers, zoom=SHOOT_ZOOM, focus=focus, aperture=6, shake=c["shake"], t=t)


# ------------------------------------------------------------------ the thought (inside the drawn ring)
TM = 80                                  # the line layer is this much bigger than the frame all round
TS = 2.35                                # sheet units -> the thought's px
SUBC = _raw(440, 420)                    # the middle of the pencil sub, in sheet units
TCEN = (392, 214)                        # where that sits in the thought's frame
_ST = {g: [np.asarray(Wd._dense(s), np.float32) for s in Wd.PILOT_STROKES if s["part"] == g] for g in Wd.PILOT_PARTS}
_WT = {g: [s["weight"] for s in Wd.PILOT_STROKES if s["part"] == g] for g in Wd.PILOT_PARTS}
_HEAD = _ST["head"]
_HC = np.concatenate(_HEAD).mean(0)                                   # the head's own middle
_LEFT = [_ST["faint"][2], _ST["faint"][3], _ST["faint"][0]]           # the wedge, the tall spike, the long curve underneath
_NECK_BASE = np.asarray(_raw(1040, 836), np.float32)
A_AT = np.asarray((168.0, 408.0), np.float32)                         # lower left: where the slip has the pale head
_A_LEFT = [(-64, -70, 40), (60, -52, -70), (26, 92, 115)]             # the three loose lines, while they are part of it


def _tpt(a, off=(0.0, 0.0)):
    """sheet units (array n x 2) -> the thought layer's px"""
    return np.stack([TM + TCEN[0] + (a[:, 0] - SUBC[0]) * TS + off[0], TM + TCEN[1] + (a[:, 1] - SUBC[1]) * TS + off[1]], 1)


def _rot_arr(a, c, deg):
    r = math.radians(deg)
    ca, sa = math.cos(r), math.sin(r)
    x, y = a[:, 0] - c[0], a[:, 1] - c[1]
    return np.stack([c[0] + x * ca - y * sa, c[1] + x * sa + y * ca], 1)


def _gl(lay, pts, width, weight, seed):
    if weight <= 0.03 or len(pts) < 2:
        return
    P.graphite(lay, [[(float(x), float(y)) for x, y in pts]], width, weight, seed)


def _thought_lines(t):
    lay = Image.new("RGBA", (W + 2 * TM, H + 2 * TM), (0, 0, 0, 0))
    bob = 4.0 * math.sin(t * 1.7)
    # water, as a few pencil lines
    for k in range(6):
        y0 = TM + 60 + k * 86 + 18 * math.sin(k * 2.3)
        x0 = -40 + 130 * ((k * 37) % 7) / 7.0
        n = 26
        ln = [(x0 + j * (W + 2 * TM + 80) / n * (0.55 + 0.1 * (k % 3)),
               y0 + 7 * math.sin(j * 0.9 + k * 1.7 + t * 1.3) + 3 * math.sin(j * 2.3 + t * 0.7)) for j in range(n)]
        _gl(lay, ln, 2.4, 0.26, 40 + k)
    # the faint head: comes together lower left, will not hold, crosses behind the sub, comes together on the right
    rs = random.Random(16)
    hc_b = _tpt(_HC[None, :])[0]
    tipdeg = -7.0 * math.sin(math.pi * ramp(t, 12.3 + Wd.DT * 0.0, 12.76))            # D frames after it settles (11.8)
    nb = _tpt(_NECK_BASE[None, :])[0]
    items = []
    for i, st in enumerate(_HEAD):
        last = 11.25 + 0.07 * i + (0.3 if i in (4, 5) else 0.0)                         # the eye last
        items.append((st, None, 9.6 + 0.05 * i, 10.4 + 0.04 * i, min(last, 11.8), True))
    for j, st in enumerate(_LEFT):
        items.append((st, _A_LEFT[j], 9.72 + 0.09 * j, 10.42 + 0.05 * j, 11.05 + 0.12 * j, False))
    for i, (st, aoff, t_in, t_go, t_done, is_head) in enumerate(items):
        u = ease(t, t_in, t_in + 0.38)
        sx, sy, sr = rs.uniform(-260, 120), rs.uniform(-200, 260), rs.uniform(-110, 110)       # where it flies in from
        mx, my, mr = rs.uniform(-40, 60), rs.uniform(-30, 130), rs.uniform(-80, 80)            # how it strays on the way over
        if u <= 0:
            continue
        b = _tpt(st, (0, bob * 0.6))
        if aoff is None:                                 # the head as the slip has it: the other way round, on the left
            a = np.stack([2 * hc_b[0] - b[:, 0], b[:, 1]], 1) + (TM + A_AT - hc_b)[None, :]
        else:
            c0 = b.mean(0)
            a = _rot_arr(b, c0, aoff[2]) + (TM + A_AT + np.asarray(aoff[:2], np.float32) - c0)[None, :]
        v = ease(t, t_go, t_done)
        pts = a + (b - a) * v
        c = pts.mean(0)
        stray = math.sin(math.pi * v)
        pts = _rot_arr(pts, c, sr * (1 - u) + mr * stray) + np.asarray((sx * (1 - u) + mx * stray, sy * (1 - u) + my * stray), np.float32)
        if is_head and tipdeg:
            pts = _rot_arr(pts, nb, tipdeg)
        wgt = 0.5 * u * (1.0 - 0.35 * stray)
        _gl(lay, pts, 3.4, wgt, 60 + i)
    # the pilot's own sub, large now, hanging there; the window black, nobody in it
    wx, wy = _tpt(np.asarray([_raw(401, 402)], np.float32), (0, bob))[0]
    k = 0
    for g in ("box", "dome", "blocks", "right", "window"):
        for st, wt in zip(_ST[g], _WT[g]):
            _gl(lay, _tpt(st, (0, bob)), 4.6, 0.55 + 0.6 * wt, 80 + k)
            k += 1
    r = 37 * 214 / 780.0 * TS
    ImageDraw.Draw(lay).ellipse([wx - r, wy - r * 1.04, wx + r, wy + r * 1.04], fill=(40, 40, 46, 236))
    for g in ("scribble1", "scribble2"):
        for st in _ST[g]:
            _gl(lay, _tpt(st, (0, bob)), 5.0, 1.4, 90 + k)
            k += 1
    return lay


_bg_cache = {}


def _thought_bg(t):
    """Paper-white, going to river green only round the sub."""
    k = int(t * 12)
    if k not in _bg_cache:
        if len(_bg_cache) > 4:
            _bg_cache.clear()
        size = (W + 180, H + 100)
        ink = Ink(t, int(t * FPS))
        Wd.river_back(ink, t)
        riv = ink.img.convert("RGB").resize(size, Image.BILINEAR)
        riv = Image.blend(riv, Image.new("RGB", size, P.PAPER), 0.38)
        yy, xx = np.mgrid[0:size[1], 0:size[0]].astype(np.float32)
        cx, cy = size[0] / 2 + (TCEN[0] - W / 2) * 0.4, size[1] / 2 + (TCEN[1] - H / 2) * 0.4 + 10
        d = np.hypot((xx - cx) / 300.0, (yy - cy) / 200.0)
        m = np.clip(1.25 - d, 0, 1) ** 1.5
        m *= 0.86 + 0.14 * P.vnoise(size[::-1], 40, None, 5)
        _bg_cache[k] = Image.composite(riv, Image.new("RGB", size, P.PAPER), Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)))
    return _bg_cache[k]


TH = (9.1, 12.6)


def _thought(t):
    """Inside the thought: no brass, no tin; only what the pilot is picturing, in pencil line. A full frame."""
    return cam.shoot([(_thought_bg(t), 3.0), (_thought_lines(t), 1.0)], x=cam.key(t, [(8.0, -6), (13.6, 34)], "linear"),
                     y=cam.key(t, [(8.0, -10), (13.6, 12)], "linear"), zoom=1.0,
                     dolly=cam.key(t, [(8.6, 0.0), (12.8, 0.1)], "linear"), shake=2, t=t, bg=P.PAPER)


# ---------------------------------------- the two looks into a thought while the lines are written (pictures, never words)
def _outline(rgba, width=5, weight=0.8, seed=0):
    """A cut-paper piece as its pencil outline only."""
    a = rgba.getchannel("A")
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(width)), a.filter(ImageFilter.MinFilter(width)))
    inner = rgba.convert("L").filter(ImageFilter.GaussianBlur(1.2)).filter(ImageFilter.FIND_EDGES)
    inner = ImageChops.multiply(inner.point(lambda v: min(255, v * 5)), a.filter(ImageFilter.MinFilter(9)))
    m = np.maximum(np.asarray(edge, np.float32), np.asarray(inner, np.float32) * 0.5) / 255.0
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255.0
    m *= (0.74 + 0.4 * P.vnoise(m.shape, 1.6, None, 811 + seed)) * weight
    out = np.zeros(m.shape + (4,), np.uint8)
    out[..., :3] = P.GRAPHITE
    out[..., 3] = (np.clip(m, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


NK_S = 1.36                               # sheet units -> the neck thought's px
NK_C = (452, 420)
NK_T0 = 17.08
_NK = [  # (shape the neck grows from [raw tracing px], head joint [px], bend, flip)
    ((236, 372), (374, 150), -0.22, False),
    ((716, 330), (548, 96), 0.2, False),
    ((960, 560), (700, 176), 0.3, False),
]


def _nk(p):
    u, v = _raw(*p)
    return (NK_C[0] + (u - SUBC[0]) * NK_S, NK_C[1] + (v - SUBC[1]) * NK_S)


def _necks_inner(t):
    """The three faint shapes round the small dark-windowed sub, each growing a long neck, one after another,
    D frames apart, in pencil outline only. (It is not known that the faint shapes fed the answer: they are only there.)"""
    im = Image.new("RGB", (W, H), P.PAPER)
    for g in Wd.PILOT_PARTS:
        for st, wt in zip(_ST[g], _WT[g]):
            pts = np.stack([NK_C[0] + (st[:, 0] - SUBC[0]) * NK_S, NK_C[1] + (st[:, 1] - SUBC[1]) * NK_S], 1)
            faint = g in ("faint", "head")
            _gl(im, pts, 3.4 if faint else 4.4, 0.62 if faint else 1.0 + 0.4 * wt, 7)
    wx, wy = _nk((401, 402))
    ImageDraw.Draw(im, "RGBA").ellipse([wx - 8, wy - 8, wx + 8, wy + 8], fill=(40, 40, 46, 240))
    for k, (root, head, bend, flip) in enumerate(_NK):
        up = ease(t - k * Wd.DT, NK_T0, NK_T0 + 0.46)                    # neck k rises D frames after neck k - 1
        if up <= 0.02:
            continue
        bx, by = _nk(root)
        i = Wd.monster_idle(t, k)
        hx, hy = lerp(bx, head[0], up) + i["dx"] * 0.6 * up, lerp(by, head[1], up) + i["dy"] * 0.6 * up
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        Wd.monster_neck(lay, (bx, by), (hx, hy), 0.3 + 0.36 * up, bend * up, 8 + i["tilt"], 5, i["look"], flip, k, t, drop=False)
        im.paste(_outline(lay, 7, 0.95, k), (0, 0), _outline(lay, 7, 0.95, k))
    return im


WV_T0 = 21.56


def _wave_inner(t):
    """Turkey's wing going up, and half a second later a second wing answering, mirrored."""
    ink = Ink(t, int(t * FPS))
    ink.fill(P.PAPER)
    Wd.pencil_path(ink, [(480, 40), (476, 180), (483, 330), (479, 500)], 0.5, seed=3)       # the glass between them, a pencil line
    tt = Wd.on_twos(t)
    Wd.turkey_front(ink, 384, 304, 0.86, t=tt, **Wd.wave_pose(tt, 1.0, WV_T0, 1.7))
    Wd.turkey_front(ink, 576, 304, 0.86, t=tt - Wd.DT, **Wd.wave_pose(tt, 1.0, WV_T0, 1.7, twin=True))
    return ink.img.convert("RGB")


# ------------------------------------------------------------------ the film
DIVE_IN = (8.0, 9.1)
DIVE_OUT = (12.6, 13.6)
LOOK2 = (5.0, 5.24, 5.36, 5.6)                         # a quick look across at the slip: there, held, back
UP_CLUE = (20.0, 20.4)
DOWN_CLUE = (20.8, 21.2)
TH_NECKS = [(17.0, 0), (17.34, 1), (18.52, 1), (18.8, 0)]
TH_WAVE = [(21.4, 0), (21.66, 1), (22.62, 1), (22.86, 0)]
NECKS_AT = (792, 150)
WAVE_AT = (74, 262)


def _ring_on_screen(t):
    c = _cam(t)
    return _final(*_tp(c, PX + RCX, PY + RCY + 10))


def _pen_end1():
    return (_E1[0] + 14, _E1[1] - 4, 16, "hover")


def _pen_clue():
    return (CLUE_PT[0], CLUE_PT[1], 3, "write")


def frame(t):
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if LOOK2[0] <= t < LOOK2[1]:                         # eyes to the slip
        return cam.whip(_desk_frame(t), _desk_frame(t, SLIPSHOT), ramp(t, LOOK2[0], LOOK2[1]), direction=1, blur=0.4)
    if LOOK2[1] <= t < LOOK2[2]:
        return _desk_frame(t, SLIPSHOT)
    if LOOK2[2] <= t < LOOK2[3]:                         # and back
        return cam.whip(_desk_frame(t, SLIPSHOT), _desk_frame(t), ramp(t, LOOK2[2], LOOK2[3]), direction=-1, blur=0.4)
    if DIVE_IN[0] <= t < DIVE_IN[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, ramp(t, *DIVE_IN), spin=40)
    if DIVE_IN[1] <= t < DIVE_OUT[0]:
        return _thought(t)
    if DIVE_OUT[0] <= t < DIVE_OUT[1]:
        rx, ry = _ring_on_screen(t)
        return cam.dive(_desk_frame(t), _thought(t), rx, ry, 1 - ramp(t, *DIVE_OUT))
    if UP_CLUE[0] <= t < UP_CLUE[1]:                     # eyes up the page to the printed clue
        return cam.whip(_desk_frame(t, C_A1R, _pen_end1()), _desk_frame(t, CLUESHOT, _pen_clue()), ramp(t, *UP_CLUE),
                        direction=-1, axis="y")
    if UP_CLUE[1] <= t < DOWN_CLUE[0]:                   # the point under "twin Turkey"
        return _desk_frame(t, CLUESHOT, _pen_clue())
    if DOWN_CLUE[0] <= t < DOWN_CLUE[1]:                 # and down, one question lower
        return cam.whip(_desk_frame(t, CLUESHOT, _pen_clue()), _desk_frame(t), ramp(t, *DOWN_CLUE), direction=1, axis="y")
    fr = _desk_frame(t)
    u = cam.key(t, TH_NECKS, "linear")
    if u > 0:
        fr = cam.thought(fr, _necks_inner(t), NECKS_AT[0], NECKS_AT[1], 120, u, wobble=5, t=t)
    u = cam.key(t, TH_WAVE, "linear")
    if u > 0:
        fr = cam.thought(fr, _wave_inner(t), WAVE_AT[0], WAVE_AT[1], 96, u, wobble=0, t=t)
    return fr


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB") if fr.mode != "RGB" else fr)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


if __name__ == "__main__":
    import time
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/m16_pilot.png"
    ts = [float(a) for a in sys.argv[2:]] or [0.1, 1.4, 2.5, 3.15, 4.2, 5.12, 5.3, 6.4, 7.6, 8.3, 8.7, 9.4, 10.3, 10.8, 11.4, 12.1,
                                              12.5, 13.0, 13.4, 14.2, 15.3, 16.6, 17.2, 17.9, 18.4, 19.2, 19.95, 20.2, 20.6, 21.0,
                                              21.9, 22.3, 22.95, 23.7, 25.0, 26.15, 27.0, 27.9, 28.6, 28.95]
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
