"""S4 · THE PACK · film seconds 84.0 to 116.0 (local t = film - 84).

Built under scion/animation-41.md (secondary dynamics: inertia and restraint). Its primitives are real
data in this file, not a look:

    MATERIALS   mass, stiffness and damping per material (foliage, paper, felt, verdigris, fish, film)
    Track       one mass on one spring and one damper, stepped by a semi-implicit integrator at 240 Hz
    DRIVES      the primary pose impulses: what the principal action does to each secondary thing
    TRACKS      the secondary things themselves: the reeds and the moths in the howl, the bloodhound
                peeling up off the boards, the felt dog's ear, the school bell and the eight fish
                children in the wake of ten dogs
    Works       the strip of film pieces as a chain of masses in the creek's current, with collision
                boundaries (a stake, each neighbour, the sheepdog's nose as a moving wall)

The rule the SCION sets: a secondary thing answers AFTER the primary motion, and when the source stops
its energy runs out. check() (run under __main__ --check) asserts that numerically for every track;
it also asserts that no two pieces of the strip ever overlap, that the integrator agrees with itself at
half the step, and the board's counts and boundary positions. What can only be judged by looking is in
the builder's report, not here.

Staging is the board's (films/swarm/dogs/board.md, S4): F-PORCH locked wide for the howl, the
arrivals and the herder opening the way; ten dogs into the water in the same four frames; a crane
down through the line; then the town, one master with a slow push so that "at the same time" is one
frame, two inserts, and the pull back. Times in this file are FILM seconds unless a name says local.

Exposes SECONDS, draw(t, ink), sound(mix, at).
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kit                                   # noqa: E402
from kit import clamp, ramp, ease, lerp, smooth, W, H, FPS   # noqa: E402
import dog                                   # noqa: E402
import herd                                  # noqa: E402
import porch                                 # noqa: E402
import props                                 # noqa: E402
import town                                  # noqa: E402
import kennel_a as ka                        # noqa: E402
import kennel_b as kb                        # noqa: E402
import importlib.util as _ilu               # noqa: E402

_spec = _ilu.spec_from_file_location("dogs_sound", str(_HERE / "sound.py"))   # films/ has another module called sound
snd = sys.modules.get("dogs_sound")
if snd is None:
    snd = _ilu.module_from_spec(_spec)
    sys.modules["dogs_sound"] = snd
    _spec.loader.exec_module(snd)

SECONDS = 32.0
T0 = 84.0                                    # film second at local 0
T1 = T0 + SECONDS
TEAL = (24, 120, 128)
Cam = town.Cam
SILL_Y = 394.0
DS = 0.6                                     # the lead dog's scale
RS = 0.42                                    # retrievers, sheepdog, bloodhound
HS = 0.62                                    # the herding dog
GS = 0.84                                    # the wire digger
TS = 0.72                                    # the terrier
OLD = (425.0, 394.0, 0.78)                   # the old dog's place on the sill (board)


def bump(x):
    return math.sin(math.pi * clamp(x)) if 0 < x < 1 else 0.0


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


# ====================================================================== #
#  1 · SECONDARY DYNAMICS (scion/animation-41): springs, dampers, masses #
# ====================================================================== #

SUB = 240                                    # integrator steps a second

MATERIALS = {   # name: (mass, stiffness, damping, what it is here)
    "foliage":   (1.0, 121.0, 9.9, "reeds in air: springy, a clear overshoot, quiet in under a second"),
    "paper":     (0.3, 5.4, 2.3, "a moth: light, nearly all drag, comes back slowly"),
    "newsprint": (0.5, 98.0, 5.6, "a printed page lifted off a board: snaps up, overshoots, flutters twice"),
    "felt":      (1.0, 81.0, 6.3, "a felt ear: heavy and limp, arrives late, two soft bounces"),
    "verdigris": (2.0, 50.0, 5.0, "the school bell under water: a slow pendulum the water soon stops"),
    "fish":      (1.0, 36.0, 4.8, "a fish child in a wake: rocks back, rights itself"),
    "film":      (1.0, 0.0, 6.0, "a piece of film stood in the gravel: no spring at all, only drag and the current"),
    "film_tilt": (1.0, 60.0, 6.2, "the same piece leaning: it stands up again by itself"),
}


def zeta(material):
    m, k, c, _ = MATERIALS[material]
    return c / (2 * math.sqrt(k * m)) if k > 0 else float("inf")


class Track:
    """One degree of freedom: m x'' = F(t) - k (x - anchor(t)) - c x' , plus impulses.

    drive(f) is a force, anchor(f) a moving rest position, kicks = [(time, impulse)]. lo / hi are
    collision boundaries. Stepped once over the whole sequence by semi-implicit Euler at `sub` Hz
    and then only read, so a still at any time matches the film."""

    def __init__(self, name, material, drive=None, anchor=None, kicks=(), lo=None, hi=None, bounce=0.25,
                 x0=0.0, sub=SUB, t0=T0 - 1.0, t1=T1 + 1.0):
        self.name, self.material = name, material
        self.m, self.k, self.c, _ = MATERIALS[material]
        self.t0, self.sub = t0, sub
        self.kicks = sorted(kicks)
        self.drive, self.anchor = drive, anchor
        n = int((t1 - t0) * sub) + 1
        xs, vs = np.empty(n), np.empty(n)
        x, v, dt, ki = x0, 0.0, 1.0 / sub, 0
        for i in range(n):
            f = t0 + i * dt
            while ki < len(self.kicks) and self.kicks[ki][0] <= f:
                v += self.kicks[ki][1] / self.m
                ki += 1
            a = anchor(f) if anchor else 0.0
            F = drive(f) if drive else 0.0
            v += dt * (F - self.k * (x - a) - self.c * v) / self.m
            x += dt * v
            if lo is not None and x < lo:
                x, v = lo, -bounce * v
            if hi is not None and x > hi:
                x, v = hi, -bounce * v
            xs[i], vs[i] = x, v
        self.xs, self.vs = xs, vs

    def _at(self, arr, f):
        u = (f - self.t0) * self.sub
        i = int(clamp(u, 0, len(arr) - 2))
        return float(lerp(arr[i], arr[i + 1], clamp(u - i)))

    def x(self, f):
        return self._at(self.xs, f)

    def v(self, f):
        return self._at(self.vs, f)

    def energy(self, f):
        """Kinetic plus spring energy about where it is being held."""
        a = self.anchor(f) if self.anchor else 0.0
        F = self.drive(f) if self.drive else 0.0
        rest = a + (F / self.k if self.k else 0.0)
        return 0.5 * self.m * self.v(f) ** 2 + 0.5 * self.k * (self.x(f) - rest) ** 2

    def source_on(self, f, eps=1e-3):
        """Is the primary motion still feeding this track at f?"""
        dt = 1.0 / 48
        if self.drive and (abs(self.drive(f)) > eps or abs(self.drive(f) - self.drive(f - dt)) > eps):
            return True
        if self.anchor and abs(self.anchor(f) - self.anchor(f - dt)) > eps * 0.1:
            return True
        return any(abs(f - kt) <= 1.0 / 24 for kt, _ in self.kicks)

    def first_source(self):
        f = self.t0
        while f < T1 + 1:
            if self.source_on(f):
                return f
            f += 1.0 / 96
        return None

    def first_move(self, eps=1e-4):
        idx = np.nonzero(np.abs(self.vs) > eps)[0]
        return self.t0 + idx[0] / self.sub if len(idx) else None


# ---- the primary pose impulses (film seconds) -------------------------------------------------

T_HOWL = 86.0                                # dog.howl(f - T_HOWL): muzzle up by 86.9, down from 88.3
T_PEEL = 91.6                                # the bloodhound peels up off the boards
T_FELT = 92.8                                # the felt dog lifts its head
T_GO = 97.0                                  # ten dogs go
T_LINE = 98.3                                # the bright line passes the camera


def howl_env(f):
    """How hard the howl is leaning on the air: 0..1."""
    return ease(f, T_HOWL + 0.3, T_HOWL + 0.85) * (1 - ease(f, T_HOWL + 1.75, T_HOWL + 2.15))


def _reed_force(f):
    return MATERIALS["foliage"][1] * howl_env(f) * (1 + 0.05 * math.sin(2 * math.pi * 6.0 * f))


def _moth_force(f):
    return MATERIALS["paper"][1] * howl_env(f) * 1.6


def felt_lift(f):
    """The felt dog's head: 0 ear to the boards, 1 lifted. The primary pose its ear hangs from."""
    up = ease(f, T_FELT, T_FELT + 0.28)
    return up


WAKE = {}       # filled by _tracks(): when each dog's wake reaches the school


@lru_cache(maxsize=None)
def _tracks():
    """Every single-mass secondary thing in the sequence, stepped once."""
    tr = {}
    tr["reeds"] = Track("reeds", "foliage", drive=_reed_force, lo=-0.3, hi=1.6)
    tr["moths"] = Track("moths", "paper", drive=_moth_force, lo=0.0, hi=1.5)
    tr["peel"] = Track("peel", "newsprint", anchor=lambda f: 1.0 if f >= T_PEEL else 0.0, lo=0.0, hi=1.5)
    tr["felt_ear"] = Track("felt_ear", "felt", anchor=felt_lift, lo=-0.2, hi=1.6)
    # the wake of ten dogs coming down over the school: one push per dog as it passes the bell's height
    passes = []
    for name in PACK:
        tp = _pass_time(name, 640.0)
        if tp is not None:
            passes.append((tp, name))
    passes.sort()
    WAKE["passes"] = passes
    tr["bell"] = Track("bell", "verdigris", kicks=[(tp, 26.0 * (1 if i % 2 == 0 else -0.7)) for i, (tp, _) in enumerate(passes)],
                       lo=-34, hi=34)
    for k in range(8):
        sx = town.SEATS[k][0]
        kicks = [(tp + 0.25 + 0.0012 * abs(sx - 683) + 0.05 * k, 7.5 * (1 if (i + k) % 2 == 0 else -0.8))
                 for i, (tp, _) in enumerate(passes)]
        tr[f"kid{k}"] = Track(f"kid{k}", "fish", kicks=kicks, lo=-16, hi=16)
    return tr


def track(name):
    return _tracks()[name]


# ====================================================================== #
#  2 · THE CAMERA (data)                                                 #
# ====================================================================== #

SHOTS = [   # t0, t1 (film), name, kind, why the camera is there
    (84.0, 97.5, "A porch", "porch", "locked wide: the answer to the howl comes from the edges of the frame"),
    (97.5, 99.5, "B crane", "crane", "down through the line with ten bubble trails: the pack crosses together"),
    (99.5, 107.0, "C master", "master", "one frame holds every job: 'at the same time' can only be shown in one frame"),
    (107.0, 109.0, "D fence", "insert", "close on the herder at the gate: the pages are carried flat, not folded"),
    (109.0, 111.0, "E bubble", "insert", "close on the bloodhound and the child: the piece taken back to ask"),
    (111.0, 116.0, "F master", "master", "back to the one frame, then pulled back to the full town with the line on top"),
]
INSERT_CAM = {"D fence": Cam.look(556, 806, 3.1), "E bubble": Cam.look(680, 804, 2.7)}
PUSH_C = (480.0, 440.0)                      # the master's push is about this screen point


def shot_at(f):
    for s in SHOTS:
        if s[0] <= f < s[1]:
            return s
    return SHOTS[-1]


def crane_oy(f):
    return porch.crane(f, 97.5, 99.5, porch.F_PORCH, porch.F_TOWN)


def master_zoom(f):
    """A very slow push while every job runs (5% by 107, 10% by 113), then the pull back to the full town."""
    return 1.0 + 0.10 * ramp(f, 101.0, 113.0) * (1 - ease(f, 113.0, 115.4))


# ====================================================================== #
#  3 · SMALL TOOLS                                                       #
# ====================================================================== #

class Seg:
    __slots__ = ("kind", "a", "b", "p0", "p1", "facing", "kw")

    def __init__(self, kind, a, b, p0, p1, facing, kw):
        self.kind, self.a, self.b, self.p0, self.p1, self.facing, self.kw = kind, a, b, p0, p1, facing, kw


class Agenda:
    """A dog's work as a list of things done one after another: go somewhere, do something there."""

    def __init__(self, t0, start, speed, facing=1):
        self.t, self.pos, self.speed, self.facing = t0, tuple(start), speed, facing
        self.segs = []

    def go(self, xy, kind="go", speed=None, face=None, **kw):
        d = math.hypot(xy[0] - self.pos[0], xy[1] - self.pos[1])
        dur = max(0.04, d / (speed or self.speed))
        if face is None and abs(xy[0] - self.pos[0]) > 1.0:
            self.facing = 1 if xy[0] > self.pos[0] else -1
        elif face is not None:
            self.facing = face
        self.segs.append(Seg(kind, self.t, self.t + dur, self.pos, tuple(xy), self.facing, kw))
        self.t += dur
        self.pos = tuple(xy)
        return self

    def do(self, kind, dur, face=None, **kw):
        if face is not None:
            self.facing = face
        self.segs.append(Seg(kind, self.t, self.t + dur, self.pos, self.pos, self.facing, kw))
        self.t += dur
        return self

    def until(self, T, kind="wait", face=None, **kw):
        if T > self.t:
            self.do(kind, T - self.t, face=face, **kw)
        return self

    def at(self, f):
        """-> (seg, tau seconds into it, u 0..1, x, y)."""
        seg = self.segs[0]
        for s in self.segs:
            if s.a <= f:
                seg = s
            else:
                break
        tau = max(0.0, f - seg.a)
        u = clamp(tau / max(1e-6, seg.b - seg.a))
        return seg, tau, u, lerp(seg.p0[0], seg.p1[0], u), lerp(seg.p0[1], seg.p1[1], u)

    def find(self, kind, **match):
        for s in self.segs:
            if s.kind == kind and all(s.kw.get(k) == v for k, v in match.items()):
                return s
        return None

    def all(self, kind):
        return [s for s in self.segs if s.kind == kind]


def _redraw(ink):
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def with_halo(ink, fn, color=(206, 176, 226), alpha=150, grow=3):
    """Draw with fn(layer) and lay a thin pale edge round it first: a black cut-out on a dark hill needs one."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out = fn(layer)
    bb = layer.getbbox()
    if bb:
        box = (max(0, bb[0] - 4), max(0, bb[1] - 4), min(W, bb[2] + 4), min(H, bb[3] + 4))
        part = layer.crop(box)
        m = part.getchannel("A").filter(ImageFilter.MaxFilter(grow)).point(lambda v: int(v * alpha / 255))
        edge = Image.new("RGBA", part.size, tuple(color) + (0,))
        edge.putalpha(m)
        ink.img.paste(edge, box[:2], edge)
        ink.img.paste(part, box[:2], part)
        _redraw(ink)
    return out


def squashed(ink, fn, ground_y, sy):
    """Draw with fn(layer), then squash it toward the screen line ground_y by sy (a page lifted off a board)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out = fn(layer)
    bb = layer.getbbox()
    if bb:
        part = layer.crop(bb)
        hh = max(1, int(round((ground_y - bb[1]) * sy)) + (bb[3] - int(ground_y)))
        hh = max(2, hh)
        part = part.resize((part.width, hh), Image.BILINEAR)
        ink.img.paste(part, (bb[0], int(round(ground_y - (ground_y - bb[1]) * sy))), part)
        _redraw(ink)
    return out


def draw_hole(ink, cam, q, f):
    """One hole of town.HOLES, f 0..1 dug (town.dig_holes draws them only in index order; the pack does not
    dig in index order, so this is the same drawing for one hole)."""
    if f <= 0:
        return
    z = cam.zoom
    x, y, wd, side = town.HOLES[q]
    sx, sy = cam.xy(x, y)
    if not (-40 < sx < W + 40 and -20 < sy < H + 20):
        return
    a = wd / 2 * z * (0.45 + 0.55 * f)
    b = a * 0.40
    rs = random.Random(q * 7 + 1)
    hx = sx + side * a * 1.5
    hr, hh = a * 0.95 * f ** 0.6, b * 1.5 * f ** 0.6
    heap = [(hx - hr, sy + b * 0.5)] + [(hx + hr * math.cos(math.radians(ang)),
                                         sy + b * 0.5 - hh * math.sin(math.radians(ang)) * (0.85 + 0.3 * rs.random()))
                                        for ang in range(180, -1, -30)]
    ink.d.polygon([(px + 1.5 * z, py + 2 * z) for px, py in heap], fill=(6, 22, 24, 90))
    ink.d.polygon(heap, fill=(118, 138, 120, 255))
    ink.d.line(heap, fill=(20, 40, 40, 230), width=max(1, int(z)))
    for _ in range(4):
        px, py = hx + rs.uniform(-0.7, 0.7) * hr, sy + b * 0.4 - rs.uniform(0.1, 0.8) * hh
        r = rs.uniform(0.9, 1.9) * z
        ink.d.ellipse([px - r, py - r * 0.7, px + r, py + r * 0.7], fill=(166, 182, 160, 255), outline=(30, 50, 48, 255))
    ink.d.ellipse([sx - a * 1.2, sy - b * 1.3, sx + a * 1.2, sy + b * 1.25], fill=(132, 150, 130, 255), outline=(26, 46, 44, 255))
    ink.d.ellipse([sx - a, sy - b, sx + a, sy + b], fill=(6, 22, 26, 255))
    ink.d.chord([sx - a, sy - b, sx + a, sy + b], 10, 170, fill=(40, 70, 70, 255))
    ink.d.arc([sx - a, sy - b, sx + a, sy + b], 200, 340, fill=(2, 10, 12, 255), width=max(1, int(1.5 * z)))


def silt(ink, cam, wx, wy, age, size=1.0, seed=0):
    """A puff of silt off the bed: rises, spreads, thins. age in seconds."""
    if age <= 0 or age > 1.6:
        return
    z = cam.zoom
    rs = random.Random(seed)
    for q in range(7):
        ang = rs.uniform(-2.6, -0.5)
        sp = rs.uniform(10, 26) * size
        u = 1 - math.exp(-2.2 * age)
        px, py = cam.xy(wx + math.cos(ang) * sp * u, wy + math.sin(ang) * sp * u * 0.7 - 3)
        r = (4 + 9 * u) * size * z * rs.uniform(0.7, 1.2)
        a = int(120 * (1 - age / 1.6) ** 1.4)
        ink.d.ellipse([px - r, py - r * 0.6, px + r, py + r * 0.6], fill=(150, 168, 150, a))


# ---- the felt dog: cut here from two felt-coloured shapes (the board's instruction to the S4 builder) ----

FELT = (116, 140, 118)
FELT_DK = (78, 100, 92)
FELT_ST = (196, 208, 180)


def felt_dog(ink, x, y, s=1.0, facing=1, lift=0.0, ear=0.0, hop=0.0, rot=0.0, under=False, dim=0.0, paw=0.0):
    """A round felt dog, feet at (x, y). lift 0 = flat, ear to the ground; 1 = head lifted.
    ear = the ear's own state (it is a mass on a spring hung from the head: see TRACKS 'felt_ear').
    hop squashes the body (a waddle); rot turns the whole dog (a dive); paw 0..1 reaches one fore paw out."""
    ca, sa = math.cos(rot), math.sin(rot)

    def P(px, py):
        px *= facing
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)

    def blob(cx, cy, rx, ry, col, ang=0.0, n=22):
        pts = []
        c2, s2 = math.cos(ang), math.sin(ang)
        for k in range(n):
            a = 2 * math.pi * k / n
            ex, ey = rx * math.cos(a), ry * math.sin(a)
            pts.append(P(cx + ex * c2 - ey * s2, cy + ex * s2 + ey * c2))
        return pts, col

    def shade(c):
        c = kit.mix_color(c, TEAL, 0.32) if under else c
        return kit.mix_color(c, (40, 34, 60), dim)

    bh = 13 - 2.5 * hop
    body, _ = blob(0, -bh, 22 + 2.5 * hop, bh, FELT)
    hx, hy = 21 + 2 * lift, -8 - 15 * lift
    head, _ = blob(hx, hy, 10.5, 9.5, FELT)
    # the ear: flat on the ground ahead of the head when down; hung from the head and swinging when up
    ea = lerp(0.0, 1.25, clamp(ear, -0.2, 1.4))
    ex, ey = hx + 6 - 4 * lift, hy + 5 - 3 * lift
    ear_pts, _ = blob(ex + 9 * math.cos(ea), ey + 9 * math.sin(ea) * (1 if lift > 0.05 else 0.0) + (3 if lift <= 0.05 else 0),
                      10, 4.2, FELT_DK, ang=ea if lift > 0.05 else 0.0)
    tail, _ = blob(-23, -bh - 5, 4.5, 3.5, FELT_DK)
    d = ink.d
    d.polygon([(px + 1.5 * s, py + 2 * s) for px, py in body], fill=(10, 8, 20, 80))
    d.polygon(tail, fill=shade(FELT_DK) + (255,))
    for fx in (-12, 9):
        fp, _ = blob(fx + (6 * paw if fx > 0 else 0), -2.5, 5 + (2 * paw if fx > 0 else 0), 3, FELT_DK)
        d.polygon(fp, fill=shade(FELT_DK) + (255,))
    d.polygon(body, fill=shade(FELT) + (255,))
    d.polygon(head, fill=shade(FELT) + (255,))
    d.polygon(ear_pts, fill=shade(FELT_DK) + (255,))
    st = shade(FELT_ST)
    for pts in (body, head):                 # the stitching: a broken pale line just inside the edge
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        for k in range(0, len(pts), 2):
            a, b = pts[k], pts[(k + 1) % len(pts)]
            a = (lerp(cx, a[0], 0.84), lerp(cy, a[1], 0.84))
            b = (lerp(cx, b[0], 0.84), lerp(cy, b[1], 0.84))
            d.line([a, b], fill=st + (230,), width=max(1, int(round(1.1 * s))))
    e = P(hx + 4, hy - 2)
    d.ellipse([e[0] - 1.6 * s, e[1] - 1.6 * s, e[0] + 1.6 * s, e[1] + 1.6 * s], fill=(16, 14, 22, 255))
    nz = P(hx + 10.5, hy + 1)
    d.ellipse([nz[0] - 2 * s, nz[1] - 1.7 * s, nz[0] + 2 * s, nz[1] + 1.7 * s], fill=(30, 30, 40, 255))
    return {"nose": nz, "head": P(hx, hy), "paw": P(15 + 6 * paw, -2.5), "body": P(0, -bh)}


# ====================================================================== #
#  4 · THE PACK: who, where they wait, where they go in, where they work #
# ====================================================================== #

PACK = ("lead", "herder", "digger", "big", "mid", "small", "sheep", "blood", "terrier", "felt")

# where each stands at the waterline at 96.9 (world feet), where it breaks the line, and its place in town
SPOT = {
    "blood": (872.0, 381.0), "felt": (236.0, 395.0), "mid": (104.0, 391.0), "big": (152.0, 395.0),
    "small": (200.0, 395.0), "herder": (252.0, 372.0), "lead": (540.0, 394.0), "terrier": (630.0, 391.0),
    "digger": (704.0, 389.0), "sheep": (752.0, 387.0),
}
ENTRY = {"mid": 128.0, "big": 180.0, "small": 226.0, "felt": 262.0, "herder": 318.0,
         "lead": 588.0, "terrier": 644.0, "digger": 708.0, "sheep": 762.0, "blood": 884.0}
LAG = {"lead": 0, "herder": 1, "sheep": 1, "small": 1, "terrier": 2, "big": 2, "blood": 2, "digger": 3, "mid": 3, "felt": 3}   # frames after 97.0
LEAP = 0.30                                  # seconds in the air
BODY_H = {"lead": 34, "herder": 18, "digger": 20, "big": 22, "mid": 19, "small": 15, "sheep": 24, "blood": 24,
          "terrier": 18, "felt": 12}
PLACE = {   # world feet where each lands on the bed, and when (every dog scrabbles as it lands: one hole each)
    "lead": ((331.0, 815.0), 100.35), "herder": ((618.0, 861.0), 100.2), "digger": ((524.0, 818.0), 100.5),
    "big": ((534.0, 826.0), 99.95), "mid": ((459.0, 826.0), 99.85), "small": ((277.0, 826.0), 100.05),
    "sheep": ((752.0, 846.0), 100.7), "blood": ((660.0, 846.0), 100.8), "terrier": ((180.0, 846.0), 100.3),
    "felt": ((728.0, 850.0), 100.6),
}
LAND_HOLE = {"lead": 24, "blood": 21, "mid": 32, "big": 35, "small": 30, "terrier": 15, "digger": 34, "sheep": 28,
             "felt": 14, "herder": 29}


def t_go(name):
    return T_GO + LAG[name] / FPS


def dive(name, f):
    """After 97.0: where the dog is on its way from the waterline to its place in town.
    -> dict(phase 'air' | 'swim' | None, x, y (body middle, world), facing, pitch, u)."""
    tg = t_go(name)
    if f < tg:
        return None
    sx, sy = SPOT[name]
    ex = ENTRY[name]
    (px, py), ta = PLACE[name]
    hb = BODY_H[name]
    if f < tg + LEAP:
        u = (f - tg) / LEAP
        x = lerp(sx, ex, u ** 0.9)
        y = lerp(sy - hb, 406.0, u * u) - 30 * math.sin(math.pi * min(1.0, u * 1.15)) * (1 - 0.4 * u)
        return dict(phase="air", x=x, y=y, facing=1, pitch=lerp(0.35, -1.0, u), u=u)
    if f >= ta:
        return dict(phase=None, x=px, y=py, facing=1, pitch=0.0, u=1.0)
    u = (f - tg - LEAP) / (ta - tg - LEAP)
    v = 1 - (1 - u) ** 1.7                    # quick off the surface, slowing into the bed
    p0, p2 = (ex, 408.0), (px, py - hb)
    p1 = (lerp(ex, px, 0.22), lerp(408.0, py, 0.72))
    x = (1 - v) ** 2 * p0[0] + 2 * v * (1 - v) * p1[0] + v * v * p2[0]
    y = (1 - v) ** 2 * p0[1] + 2 * v * (1 - v) * p1[1] + v * v * p2[1]
    dx = 2 * (1 - v) * (p1[0] - p0[0]) + 2 * v * (p2[0] - p1[0])
    dy = 2 * (1 - v) * (p1[1] - p0[1]) + 2 * v * (p2[1] - p1[1])
    fac = 1 if dx >= 0 else -1
    pitch = -math.atan2(dy, abs(dx) + 1e-6) * (1 - ease(u, 0.8, 1.0))
    return dict(phase="swim", x=x, y=y, facing=fac, pitch=clamp(pitch, -0.85, 0.3), u=u)


def _pass_time(name, depth_y):
    """When this dog swims down past world depth_y (its wake reaches whatever hangs there)."""
    f = t_go(name) + LEAP
    while f < PLACE[name][1]:
        st = dive(name, f)
        if st and st["y"] >= depth_y:
            return f
        f += 1.0 / 48
    return None


def mouth_world(name, f):
    """Where a swimming dog's mouth is (for its bubble trail)."""
    st = dive(name, f)
    if not st:
        return (ENTRY[name], 410.0)
    return (st["x"] + st["facing"] * 14, st["y"] - 4)


# ====================================================================== #
#  5 · THE PORCH, 84.0 to 99.5: cows                                     #
# ====================================================================== #

T_YIELD = 94.4                               # the herder's eye is on the fourth cow; the hold runs to 95.0
T_TURN = 95.0                                # she steps off the pale path
T_MOTHER = 94.7                              # the mother follows the herd
T_NOSE = 93.12                               # the herder goes under the mother's nose
LEAD_X, SECOND_X = 806.0, 892.0
CALF_X = 408.0                               # pressed to her mother's near flank, clear of the dog


def _alert(f):
    """Every cow's head comes up at once with the howl, and stays up while it lasts."""
    return ease(f, T_HOWL + 0.2, T_HOWL + 0.5) * (1 - ease(f, 89.2, 90.4))


@lru_cache(maxsize=None)
def _cows():
    u4 = min((abs(porch.path_point(u / 400)[0] - herd.PATH.at(herd.hill_spot(0))["x"]), u / 400) for u in range(200, 401))[1]
    x0, y0, s0 = porch.path_point(u4)
    r4 = herd.off_path(u4, (842.0, None))
    w4 = herd.Walker("fourth", r4, [(T_TURN, r4.find(x0, last=False)), (T_TURN + (r4.length - r4.find(x0, last=False)) / 40.0, r4.length)])
    d1, d2 = herd.hill_spot(1), herd.hill_spot(2)
    d0 = herd.hill_spot(0)
    w5 = herd.Walker("fifth", herd.PATH, [(T0 - 1, d1), (T_TURN + 0.3, d1), (T_TURN + 5.4, d0)],
                     acts=[(T_HOWL + 0.2, 89.6, lambda tau: herd.stand(tau, "fifth", chew=0, alert=1))])
    w6 = herd.Walker("sixth", herd.PATH, [(T0 - 1, d2), (T_TURN + 0.9, d2), (T_TURN + 5.9, d1)],
                     acts=[(T_HOWL + 0.2, 89.6, lambda tau: herd.stand(tau, "sixth", chew=0, alert=1))])
    rm = herd.Route([(515.0, 388.0, 1.0), (740.0, porch.meadow_y(740.0), 1.0)])
    wm = herd.Walker("mother", rm, [(T_MOTHER, 0.0), (T_MOTHER + 4.6, rm.length)])
    rc = herd.Route([(CALF_X, 391.0, 1.0), (664.0, 388.5, 1.0)])
    wc = herd.Walker("calf", rc, [(T_MOTHER + 0.25, 0.0), (T_MOTHER + 1.75, rc.length)], gait="trot")
    ly = porch.meadow_y(LEAD_X)
    rl = herd.Route([(LEAD_X + 2.0, ly, 1.0), (LEAD_X, ly, 1.0)])

    def lead_act(tau):
        f = T0 - 1 + tau
        p = herd.stand(f, "lead", chew=0 if (_alert(f) > 0.05 or 90.9 < f < 93.6) else 1, alert=max(0.35, _alert(f)))
        if 90.9 <= f < 93.4:                 # the crepe dog has landed under her nose: she smells it
            p = herd.tween(p, herd.smell(f - 91.1, "lead"), ease(f, 90.9, 91.2) * (1 - ease(f, 93.1, 93.4)), "inout", "lead")
        if f > 97.8:
            p = herd.tween(p, herd.look_down(f, 1.0, "lead"), ease(f, 97.8, 99.0), "slow", "lead")
        return p

    wl = herd.Walker("lead", rl, [(T0 - 1, rl.length), (T1 + 1, rl.length)], acts=[(T0 - 1, T1 + 1, lead_act)])
    return dict(u4=u4, p4=(x0, y0, s0), w4=w4, w5=w5, w6=w6, wm=wm, wc=wc, wl=wl, d0=d0)


def fourth_spot():
    st = herd.PATH.at(herd.hill_spot(0))
    return st["x"], st["y"], st["s"]


def draw_hill_cows(ink, f, oy):
    c = _cows()
    c["w6"].draw(ink, f, oy, layer="hill")
    c["w5"].draw(ink, f, oy, layer="hill")
    if f < T_TURN:
        x, y, s = fourth_spot()
        if f < T_YIELD:
            notice = bump((f - 91.35) / 1.5)             # a small wooden dog has bumped her hoof
            p = herd.stand(f, "fourth", chew=0 if (_alert(f) > 0.05 or notice > 0.05) else 1, alert=_alert(f))
            if notice > 0:
                p = herd.tween(p, herd.look_down(f, 0.7, "fourth"), smooth(notice), "inout", "fourth")
        else:
            p = herd.yield_to(f - T_YIELD, "fourth")
        herd.cow(ink, "fourth", p, x, y, s, -1, oy)
    else:
        c["w4"].draw(ink, f, oy, layer="hill")


def calf_state(f):
    """-> (pose, x, y, facing, turn, squash)."""
    c = _cows()
    if f < T_MOTHER + 0.25:
        p = herd.stand(f, "calf", chew=0 if _alert(f) > 0.05 else 1, alert=max(0.4, _alert(f)))
        return p, CALF_X, 391.0, 1, None, 1.0
    if f < T_MOTHER + 1.75:
        st = c["wc"].state(f)
        return st["pose"], st["x"], st["y"], 1, None, 1.0
    x, y = 664.0, 388.5
    ts = T_MOTHER + 1.75
    if f < ts + 0.7:
        return herd.calf_skid(ramp(f, ts, ts + 0.7)), x, y, 1, ease(f, ts + 0.25, ts + 0.6), 1.0
    wet = bump((f - 97.22) / 0.5)
    p = herd.stand(f, "calf", chew=0, alert=1.0 - 0.6 * ease(f, 98.2, 99.2))
    if f > 98.0:
        p = herd.tween(p, herd.look_down(f, 1.0, "calf"), ease(f, 98.0, 99.3), "slow", "calf")
    return p, x, y, -1, None, 1.0 - 0.07 * wet


def draw_strip_cows(ink, f, oy, anchors=None):
    c = _cows()
    anchors = anchors if anchors is not None else {}
    # the second cow, far right
    p = herd.stand(f, "second", chew=0 if _alert(f) > 0.05 else 1, alert=_alert(f))
    if f > 97.9:
        p = herd.tween(p, herd.look_down(f, 1.0, "second"), ease(f, 97.9, 99.2), "slow", "second")
    herd.cow(ink, "second", p, SECOND_X, porch.meadow_y(SECOND_X), herd.S, -1, oy)
    # the fourth, once she is off the hill face
    if f >= T_TURN:
        c["w4"].draw(ink, f, oy, layer="strip")
    # the lead cow (a Walker so that her bell is the herd's own pendulum, driven by her throat)
    nose = None
    if 90.9 <= f < 93.4:
        nose = (SPOT["sheep"][0] - 14, SPOT["sheep"][1] - 44)
    elif f > 97.8:
        nose = (LEAD_X - herd.reach("lead"), 399.0)
    anchors["lead"] = c["wl"].draw(ink, f, oy, nose_to=nose)
    # the mother
    if f < T_MOTHER:
        up = max(_alert(f), ease(f, T_NOSE, T_NOSE + 0.22))
        drink = herd.drink(f, 1.0, "mother")
        if up > 0.001:
            p = herd.tween(drink, herd.stand(f, "mother", chew=0, alert=1), up, "inout", "mother")
            a = herd.cow(ink, "mother", p, 515.0, 388.0, herd.S, 1, oy, nose_to=(600, 400) if up < 0.5 else None)
        else:
            a = herd.cow(ink, "mother", drink, 515.0, 388.0, herd.S, 1, oy, nose_to=(600, 400))
    else:
        a = c["wm"].draw(ink, f, oy)
    anchors["mother"] = a
    # the calf
    p, x, y, fac, turn, sq = calf_state(f)
    nose = (x - herd.reach("calf") - 2, 399.5) if f > 98.0 else None
    kw = dict(turn=turn) if turn is not None else {}
    anchors["calf"] = herd.cow(ink, "calf", p, x, y, herd.S, fac, oy, nose_to=nose, squash=sq, **kw)
    return anchors


# ====================================================================== #
#  6 · THE PORCH: the person, the lead dog, the arrivals                 #
# ====================================================================== #

PEB_T = (90.9, 91.9, 92.8, 93.7, 95.25, 95.75, 96.2)      # seven more asks while the pack comes: 5 -> 12
PEB_KIND = "wwggw" + "gwggwgg"


def pebbles_at(f):
    n = 5 + sum(1 for tk in PEB_T if f >= tk)
    return PEB_KIND[:n]


@lru_cache(maxsize=None)
def _person_keys():
    keys = [(T0 - 1, "crouch"), (T0, "crouch"),
            (T_HOWL + 0.55, "crouch", {"at": (316, 360), "dur": 0.2}),          # the hand comes off the boards
            (88.9, "crouch", {"at": (316, 362)}),
            (90.2, "stand", {"x": 150, "dur": 1.1})]
    for k, tk in enumerate(PEB_T):
        px, py = porch.pebble_spot(5 + k)
        keys.append((tk - 0.3, "tap", {"at": (px, py - 16), "dur": 0.45}))
        keys.append((tk, "tap", {"at": (px, py - 2), "dur": 0.24}))
        keys.append((tk + 0.22, "tap", {"at": (px, py - 12), "dur": 0.2}))
    keys.append((97.3, "tap", {"at": (porch.pebble_spot(11)[0] + 8, porch.pebble_spot(11)[1] - 10)}))
    return keys


def person_q(f):
    return porch.act(f, _person_keys())


def lead_porch(f):
    """The lead dog above the water: -> (pose, x, facing, anchor)."""
    if f < 85.5:
        sit = dog.sit(9.0)
        low = dog.blend(sit, dog.ears_down(3.0), {"ears": 0.6, "head": 1.0, "tail": 0.5, "body": 0.3, "legs": 0.0})
        low["neck"], low["head"] = low["neck"] - 0.12, low["head"] - 0.1          # spent: the head hangs
        up = ease(f, 84.25, 85.0)
        p = dog.blend(low, sit, up)
        p = dog.over_shoulder(p, ease(f, 84.7, 85.4))        # the head goes round to the water
        return p, 470.0, -1, None
    if f < T_HOWL:
        u = ease(f, 85.5, 85.95)
        p = dog.blend(dog.over_shoulder(dog.sit(9.0), 1 - u), dog.stand(f), u)
        fac = lerp(-1, 1, ease(f, 85.55, 85.85))
        fac = math.copysign(max(0.1, abs(fac)), fac)
        return p, 470.0, fac, None
    if f < 89.0:
        return dog.howl(f - T_HOWL), 470.0, 1, None
    if f < 96.3:
        p = dog.watch(f)
        look = max(bump((f - 89.35) / 1.5), bump((f - 91.5) / 1.3), bump((f - 93.9) / 1.3) * 0.9)
        p = dog.over_shoulder(p, look)
        x = 470.0
        if 92.9 <= f < 93.5:                                  # steps aside: the old dog wants the dry boards
            dist = 70.0 * ramp(f, 92.9, 93.5)
            p = dog.trot(dist / (DS * 104 * 2.1))
            x = 470.0 + dist
        elif f >= 93.5:
            x = 540.0
        return p, x, 1, None
    if f < t_go("lead"):
        p = dog.watch(f)
        p = dog.over_shoulder(p, bump((f - 96.32) / 0.42))    # one look along the line
        crouch = ease(f, 96.7, 96.95)
        p = dog.blend(p, dog.dig(0.02), 0.55 * crouch)        # down in front: it is going
        return p, 540.0, 1, None
    return None


def draw_lead_porch(ink, f, oy):
    st = lead_porch(f)
    if st is None:
        return
    p, x, fac, _ = st
    dog.draw_dog(ink, p, x, SILL_Y - oy, scale=DS, facing=fac)


def _kb_swim(ink, fn, name, cam, st, f, **kw):
    sx, sy = cam.xy(st["x"], st["y"])
    under = st["y"] > 404
    return fn(ink, sx, sy, "swim", f * 1.3, scale=RS * cam.zoom, facing=st["facing"], pitch=st["pitch"],
              tint=kb.WATER if under else None, tint_amount=0.3 if under else 0.0, shadow=False, **kw)


# ---- each dog of the pack: one function for the whole sequence -----------------------------------------
#      each returns the layer it is in ('porch', 'sill', 'hill', 'strip', 'front', 'under') or draws there.

def retr_porch(name, f):
    """The three wooden retrievers above the water -> (x, y, action, tau, visible)."""
    start = {"big": 90.3, "mid": 90.48, "small": 90.62}[name]
    stop_x = SPOT[name][0]
    y = SPOT[name][1]
    speed = {"big": 250.0, "mid": 236.0, "small": 300.0}[name]
    x0 = -70.0
    if f < start:
        return None
    if name == "small":
        bump_x, tb = 322.0, start + (322.0 - x0) / speed       # on to the gate, into a hoof, and back
        if f < tb:
            x = x0 + speed * (f - start)
            return x, lerp(395, 391, ramp(x, 250, 322)), "walk", (x - x0), True
        back = (bump_x - stop_x) * (1 - math.exp(-(f - tb) * 2.6))  # knocked back, it rolls all the way home
        edge = 9.0 * ease(f, 96.35, 96.8)
        return bump_x - back + edge, lerp(391, y, ramp(f, tb, tb + 0.5)), "wait", f - tb, True
    ts = start + (stop_x - x0) / speed
    if f < ts:
        x = x0 + speed * (f - start)
        return x, y, "walk", (x - x0), True
    edge = 9.0 * ease(f, 96.35, 96.8)                          # up to the edge when the way stands open
    return stop_x + edge, y, "wait", f - ts, True


T_BUMP = 90.62 + (322.0 + 70.0) / 300.0


def draw_retriever(ink, name, f, cam, where):
    """where: 'sill' above the water, 'front' in the air, 'under' below."""
    dv = dive(name, f)
    z = cam.zoom
    if dv is None:
        if where != "sill":
            return
        st = retr_porch(name, f)
        if not st:
            return
        x, y, act, tau, _ = st
        sx, sy = cam.xy(x, y)
        if act == "walk":
            tt = tau / max(1e-6, RS * kb.travel("retriever", "walk", 1.0, size=name))
            kb.retriever(ink, sx, sy, "walk", tt, scale=RS * z, size=name)
        else:
            look = 0.0
            fac = 1
            if 96.3 <= f:
                look = 0.25 * ease(f, 96.3, 96.5)              # at the lead dog
            kb.retriever(ink, sx, sy, "wait", tau, scale=RS * z, size=name, facing=fac, look=look)
        return
    if dv["phase"] == "air":
        if where == "front":
            _kb_swim(ink, kb.retriever, name, cam, dv, f, size=name)
    elif dv["phase"] == "swim":
        if where == "under":
            _kb_swim(ink, kb.retriever, name, cam, dv, f, size=name)


def sheep_porch(f):
    """Blown in from the top right; lands on its feet. -> (x, y, action, tau, rot)."""
    a, b = 89.8, 90.7
    lx, ly = SPOT["sheep"]
    if f < a:
        return None
    if f < b:
        u = (f - a) / (b - a)
        x = lerp(1010.0, lx, 1 - (1 - u) ** 1.6)
        y = lerp(120.0, ly - 26, u ** 1.5) - 46 * math.sin(math.pi * u) + 14 * math.sin(u * 9.0) * (1 - u)
        rot = (-0.9 + 0.5 * math.sin(u * 8.0)) * (1 - u) ** 0.8
        return x, y, "air", f - a, rot
    return lx, ly, "wait", f - b, 0.0


def draw_sheep(ink, f, cam, where):
    dv = dive("sheep", f)
    z = cam.zoom
    if dv is None:
        if where != "sill":
            return
        st = sheep_porch(f)
        if not st:
            return
        x, y, act, tau, rot = st
        sx, sy = cam.xy(x, y)
        if act == "air":
            kb.sheepdog(ink, sx, sy, "swim", tau * 1.5, scale=RS * z, facing=-1, rot=rot, shadow=False)
        else:
            look = 0.3 * ease(f, 96.3, 96.5)
            kb.sheepdog(ink, sx, sy, "wait", tau, scale=RS * z, facing=-1, look=look)
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        _kb_swim(ink, kb.sheepdog, "sheep", cam, dv, f)


def draw_blood(ink, f, cam, where):
    dv = dive("blood", f)
    z = cam.zoom
    if dv is None:
        if where != "strip" or f < T_PEEL:
            return
        x, y = SPOT["blood"]
        sx, sy = cam.xy(x, y)
        peel = track("peel").x(f)

        def fn(layer):
            if f < 93.6:
                return kb.bloodhound(layer, sx, sy, "wait", 9.0, scale=RS * z, sit=False, shadow=False)
            if f < 96.3:
                return kb.bloodhound(layer, sx, sy, "nose_down", f - 93.6, scale=RS * z, shadow=False)
            return kb.bloodhound(layer, sx, sy, "wait", 9.0, scale=RS * z, sit=False, look=0.3, shadow=False)
        if abs(peel - 1.0) > 0.01 or f < T_PEEL + 1.4:
            squashed(ink, fn, sy, clamp(peel, 0.03, 1.5))
        else:
            fn(ink)
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        _kb_swim(ink, kb.bloodhound, "blood", cam, dv, f)


def draw_terrier_porch(ink, f, cam, where):
    dv = dive("terrier", f)
    z = cam.zoom
    x, y = SPOT["terrier"]
    if dv is None:
        if where != "sill" or f < 92.2:
            return
        hx, hy = cam.xy(x - 10, y + 1)
        if f < 94.4:
            kb.terrier(ink, hx, hy, "come_up", f - 92.2, scale=TS * z)
        else:
            sx, sy = cam.xy(x, y)
            # the hole it came out of stays in the bank
            ink.d.ellipse([hx - 9 * z, hy - 3 * z, hx + 9 * z, hy + 3 * z], fill=(20, 14, 26, 255))
            kb.terrier(ink, sx, sy, "wait", f - 94.4, scale=TS * z, facing=1 if f < 96.3 else -1)
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        sx, sy = cam.xy(dv["x"], dv["y"])
        under = dv["y"] > 404
        kb.terrier(ink, sx, sy, "swim", f, scale=TS * z, facing=dv["facing"], rot=-dv["pitch"] * dv["facing"],
                   tint=kb.WATER if under else None, tint_amount=0.3 if under else 0.0, shadow=False)


def draw_digger_porch(ink, f, cam, where):
    dv = dive("digger", f)
    z = cam.zoom
    x, y = SPOT["digger"]
    if dv is None:
        if where != "sill" or f < 91.0:
            return
        sx, sy = cam.xy(x, y)
        if f < 91.9:
            ka.digger(ink, sx, sy, GS * z, -1, "unbend", p=ramp(f, 91.0, 91.9))
        else:
            ka.digger(ink, sx, sy, GS * z, -1, "wait", look=14 * ease(f, 96.3, 96.5))
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        sx, sy = cam.xy(dv["x"], dv["y"])
        ka.digger(ink, sx, sy, GS * z, dv["facing"], "swim", t=f)


def felt_porch(f):
    """By the step all along. -> (x, y, lift, ear, hop)."""
    x, y = SPOT["felt"]
    lift = felt_lift(f)
    ear = track("felt_ear").x(f)
    hop = 0.0
    if 96.35 <= f < 96.8:
        hop = bump((f - 96.35) / 0.45)
        x += 8.0 * ease(f, 96.35, 96.8)
    elif f >= 96.8:
        x += 8.0
    return x, y, lift, ear, hop


def draw_felt_porch(ink, f, cam, where):
    dv = dive("felt", f)
    z = cam.zoom
    if dv is None:
        if where != "sill":
            return
        x, y, lift, ear, hop = felt_porch(f)
        sx, sy = cam.xy(x, y)
        felt_dog(ink, sx, sy, 1.0 * z, 1, lift=lift, ear=ear, hop=hop, dim=0.5 * (1 - ease(f, T_FELT - 0.1, T_FELT + 0.3)))
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        sx, sy = cam.xy(dv["x"], dv["y"])
        felt_dog(ink, sx, sy + 12 * z, 1.0 * z, dv["facing"], lift=1.0, ear=1.0 + 0.3 * math.sin(f * 9), rot=-dv["pitch"] * dv["facing"],
                 under=dv["y"] > 404)


# ---- the herding dog: out of the door's edge, the wide swing, the eye, the step ----

def _sky(x, up=0.0):
    return porch.hill_y(x) - up


SWING = [   # film time, world x, y, layer: out to the right under the mother's nose, up the bank, along the skyline
            # behind the last cow of the queue (the outrun), and down the dark hill face to the head of the line
    (92.78, 300.0, 393.5, "sill"), (93.2, 590.0, 396.0, "sill"), (93.32, 650.0, 386.0, "strip"), (93.46, 700.0, 340.0, "hill"),
    (93.62, 668.0, _sky(668.0), "hill"), (93.74, 610.0, _sky(610.0), "hill"), (93.88, 520.0, _sky(520.0), "hill"),
    (94.02, 420.0, _sky(420.0), "hill"), (94.14, 330.0, _sky(330.0), "hill"), (94.26, 268.0, 300.0, "hill"),
    (94.4, 252.0, 372.0, "sill"),
]
EYE_AT = (252.0, 372.0)                      # on the step, under the fourth cow's chin


def herder_porch(f):
    """-> dict(x, y, s, facing, action, t, p, layer, look) or None."""
    if f < 89.2:
        return None
    if f < 89.95:
        return dict(x=188.0, y=392.0, s=HS, facing=1, action="slide", p=ramp(f, 89.2, 89.95), layer="sill")
    if f < 91.25:
        u = ramp(f, 89.95, 91.25)
        return dict(x=lerp(188.0, 300.0, u), y=lerp(392.0, 393.5, u), s=HS, facing=1, action="walk", t=f, layer="sill")
    if f < SWING[0][0]:
        return dict(x=300.0, y=393.5, s=HS, facing=1, action="wait", t=f, layer="sill",
                    look=16 * ease(f, 92.4, 92.6))             # one look along the blocked line
    if f < 94.4:
        for (ta, xa, ya, la), (tb, xb, yb, lb) in zip(SWING, SWING[1:]):
            if ta <= f < tb:
                u = (f - ta) / (tb - ta)
                x, y = lerp(xa, xb, u), lerp(ya, yb, u)
                if lb == "sill" and la == "hill":
                    y -= 18 * math.sin(math.pi * u)             # the jump down onto the step
                depth = clamp((392.0 - y) / 150.0)
                return dict(x=x, y=y, s=HS * lerp(1.0, 0.55, depth), facing=1 if xb > xa else -1, action="flank", t=f,
                            layer=la)
    if f < 95.3:
        return dict(x=EYE_AT[0], y=EYE_AT[1], s=HS, facing=1, action="eye", p=ramp(f, 94.4, 94.62), layer="sill", look=0.0)
    if f < 96.3:
        return dict(x=EYE_AT[0], y=EYE_AT[1], s=HS, facing=1, action="down", p=ramp(f, 95.3, 95.9), layer="sill")
    return dict(x=EYE_AT[0], y=EYE_AT[1], s=HS, facing=1, action="wait", t=f, layer="sill", look=8.0)


def draw_herder_porch(ink, f, cam, where):
    dv = dive("herder", f)
    z = cam.zoom
    if dv is None:
        st = herder_porch(f)
        if not st or st["layer"] != where:
            return
        sx, sy = cam.xy(st["x"], st["y"])

        def fn(layer):
            return ka.herding_dog(layer, sx, sy, st["s"] * z, st["facing"], st["action"], t=st.get("t", f),
                                  p=st.get("p", 0.0), look=st.get("look", 0.0))
        with_halo(ink, fn, alpha=170 if st["layer"] == "hill" else 110)
        return
    if (dv["phase"] == "air" and where == "front") or (dv["phase"] == "swim" and where == "under"):
        sx, sy = cam.xy(dv["x"], dv["y"])
        with_halo(ink, lambda layer: ka.herding_dog(layer, sx, sy + 8 * z, HS * z, dv["facing"],
                                                     "flank" if dv["phase"] == "air" else "swim", t=f),
                  color=(150, 214, 206), alpha=120)


# ---- the old dog: through the door, last and slow ----

def old_dog_state(f):
    """-> (x, y, action, t, p, layer) or None. It never goes under."""
    X, Y, S = OLD
    if f < 91.5:
        return None
    if f < 91.95:
        return 112.0, 389.0, "wait", f, 0.0, "porch"
    if f < 93.55:
        u = ramp(f, 91.95, 93.55)
        x = lerp(112.0, X, u)
        y = lerp(389.0, Y, ease(x, 286, 340))
        return x, y, "walk", f - 91.95, 0.0, "porch" if x < 214 else "sill"
    if f < 94.4:
        return X, Y, "lie_down", f, ramp(f, 93.55, 94.4), "sill"
    wet = bump((f - 97.18) / 0.6)                              # ten splashes: it gets wet, and blinks
    if wet > 0:
        return X, Y, "lift_head", f, 0.35 * wet, "sill"
    return X, Y, "lie", f, 0.0, "sill"


def draw_old_dog(ink, f, oy, where):
    st = old_dog_state(f)
    if not st or st[5] != where:
        return
    x, y, act, t, p, _ = st
    eye = 0 if 97.2 < f < 97.55 else None
    ka.old_dog(ink, x, y - oy, OLD[2], 1, act, t=t, p=p, eye=eye)


def pile_spread(f):
    """The old dog shoulders the small wet pile along the board to lie down."""
    return 1.0 - 0.42 * ease(f, 93.1, 93.6)


# ====================================================================== #
#  7 · THE TOWN: the strip as a chain in the current, the works          #
# ====================================================================== #

LINE_Y = 876.0                               # where the row of pieces stands on the gravel, in the foreground at the right
XC0 = 868.0                                  # the middle of the first piece: it stands against the felt dog
PS = 0.8                                     # piece scale
PW = 26.0                                    # one piece, shoulder to shoulder
GAP = 10.0                                   # how far short of the row a retriever sets a piece down
STOCK = {"small": (238.0, 820.0, -1), "mid": (506.0, 822.0, 1), "big": (590.0, 822.0, 1)}   # pieces leaning at three lamps
RET_OFF = {"big": 54.0, "mid": 45.0, "small": 37.0}                                    # body middle to the piece in its mouth
LAMP_AT = {k: (STOCK[k][0] - STOCK[k][2] * (RET_OFF[k] + 2), 826.0) for k in STOCK}    # where each stands to take one
LANE = {"big": 866.0, "mid": 880.0, "small": 889.0}                                    # three lanes
RET_V = {"big": 50.0, "mid": 210.0, "small": 335.0}                                    # three speeds
RET_SET = {"big": 2.5, "mid": 1.7, "small": 1.5}
T_WORK = 100.2                               # the retrievers leave their lamps (the other jobs begin at 101.0)
T_TAKE, T_BACK = 106.6, 113.3                # the bloodhound's errand with one piece
WDT = 1.0 / 120
SHEEP_NOSE = 23.0                            # the sheepdog's nose ahead of its middle


def piece_x(s):
    """World x of a piece s px along the row from its first place (the row grows to the left, toward the lamps)."""
    return XC0 - s


def current(f, i):
    """The creek's push on piece i (px/s^2 on a unit mass): never the same on two pieces, which is what opens gaps."""
    gust = 0.55 + 0.45 * math.sin(0.5 * f + 0.6)
    return 9.5 * gust * (0.75 + 0.45 * math.sin(0.83 * f + 1.7 * i) + 0.3 * math.sin(1.9 * f + 0.6 * i))


def _toward(r, tx, ty, step):
    dx, dy = tx - r["x"], ty - r["y"]
    d = math.hypot(dx, dy)
    if d <= step:
        r["x"], r["y"] = tx, ty
        return True
    r["x"] += dx / d * step
    r["y"] += dy / d * step
    return False


class Works:
    """The row of pieces, the three retrievers and the sheepdog, stepped together once at 120 Hz from T_WORK.

    A piece is a mass with drag in the current (MATERIALS 'film': no spring). s is its distance along the
    row. The collision boundaries: the felt dog lying at the row's end (s >= 0), each neighbour
    (s[k+1] >= s[k] + PW) and, during a nudge, the sheepdog's nose as a moving wall (s + PW/2 <= wall)."""

    def __init__(self, t1=T1 + 0.6):
        m, _, c, _ = MATERIALS["film"]
        mt, kt, ct, _ = MATERIALS["film_tilt"]
        n = int((t1 - T_WORK) / WDT) + 1
        self.n = n
        self.pieces = []
        self.log_p = []                       # per step: [(s, tilt, standing, pending)]
        ret = {}
        for name in ("big", "mid", "small"):
            ret[name] = dict(phase="pick", tau=0.0, x=LAMP_AT[name][0], y=LAMP_AT[name][1], facing=1, piece=None)
        self.log_r = {k: [] for k in ret}
        sheep = dict(phase="idle", tau=0.0, x=PLACE["sheep"][0][0], y=PLACE["sheep"][0][1], wall0=None, d=0.0, last=T_WORK)
        self.log_s = []
        self.landings = []                    # (t, piece index, by)
        self.nudges = []                      # (t the nose meets the piece, travel px)
        self.t_take = self.t_back = None
        self.taken_piece = None
        took = False

        def standing():
            return [p for p in self.pieces if p["on"]]

        def end_s():
            ps = [p for p in self.pieces if p["on"] or p["pending"]]
            return max(p["s"] for p in ps) + PW if ps else -GAP

        for i in range(n):
            f = T_WORK + i * WDT
            # ---- the retrievers: take one at the lamp, down into the lane, along it, set it down at the row's end
            for name, r in ret.items():
                r["tau"] += WDT
                lx, ly = LAMP_AT[name]
                side = STOCK[name][2]
                step = RET_V[name] * WDT
                if r["phase"] == "pick":
                    r["facing"] = side if r["tau"] < 0.3 else 1
                    if r["tau"] >= 0.5:
                        r["phase"], r["tau"], r["facing"] = "carry", 0.0, 1
                elif r["phase"] == "carry":
                    tx = piece_x(end_s() + GAP) - RET_OFF[name]
                    if r["x"] < lx + 36 and abs(r["y"] - LANE[name]) > 0.5 and r["x"] < tx - 30:
                        _toward(r, lx + 40, LANE[name], step)
                    elif r["x"] < tx - 30:
                        _toward(r, tx - 30, LANE[name], step)
                    elif _toward(r, tx, LINE_Y, step):
                        r["phase"], r["tau"] = "set", 0.0
                        pc = dict(s=end_s() + GAP, v=0.0, th=0.0, w=0.0, on=False, pending=True, by=name, idx=len(self.pieces))
                        self.pieces.append(pc)
                        r["piece"] = pc
                elif r["phase"] == "set":
                    pc = r["piece"]
                    if pc["pending"] and r["tau"] >= 1.0:
                        pc["pending"], pc["on"] = False, True
                        pc["w"] = 2.2                         # it rocks as the jaw lets go
                        self.landings.append((f, pc["idx"], name))
                    if r["tau"] >= RET_SET[name]:
                        r["phase"], r["tau"], r["facing"] = "back", 0.0, -1
                elif r["phase"] == "back":
                    if r["x"] > lx + 40 + 1:
                        _toward(r, lx + 40, LANE[name], step * 1.25)
                    elif _toward(r, lx, ly, step * 1.25):
                        r["phase"], r["tau"] = "pick", 0.0
                self.log_r[name].append((r["x"], r["y"], r["phase"], r["tau"], r["facing"]))
            # ---- the bloodhound takes the newest piece, and brings it back
            if not took and len(self.landings) >= 2 and f >= max(T_TAKE, self.landings[1][0] + 1.2) and sheep["phase"] == "idle" \
                    and not any(p["pending"] for p in self.pieces):
                pc = max(standing(), key=lambda p: p["s"])
                pc["on"] = False
                self.taken_piece, self.t_take, took = pc, f, True
            if took and self.taken_piece is not None and f >= T_BACK:
                pc = self.taken_piece
                pc["s"], pc["v"], pc["w"], pc["on"] = end_s() + GAP, 0.0, 1.6, True
                self.t_back = f
                self.landings.append((f, pc["idx"], "blood"))
                self.taken_piece = None
            # ---- the sheepdog: behind the row's end; out round the end to put it straight; back again
            ps = sorted(standing(), key=lambda p: p["s"])
            sheep["tau"] += WDT
            wall = None
            last_s = ps[-1]["s"] if ps else -PW
            slack = last_s - PW * (len(ps) - 1) if ps else 0.0
            home = (piece_x(last_s) + 14.0, LINE_Y - 9.0)
            out = (piece_x(last_s) - PW / 2 - SHEEP_NOSE - 1.0, LINE_Y - 2.0)
            near = any((o["phase"] == "set" and o["tau"] < 1.3) or (o["phase"] == "carry" and o["x"] > out[0] - 70)
                       for k2, o in ret.items())
            if sheep["phase"] == "idle":
                sheep["move"] = not _toward(sheep, home[0], home[1], 70.0 * WDT)
                if ps and slack > 3.5 and not near and not sheep["move"] and f - sheep["last"] > 0.4 \
                        and not (T_BACK - 2.2 < f < T_BACK + 1.2) and not (f > T_TAKE - 2.1 and self.t_take is None):
                    sheep["phase"], sheep["tau"] = "out", 0.0
            elif sheep["phase"] == "out":
                if _toward(sheep, out[0], out[1], 110.0 * WDT):
                    sheep["phase"], sheep["tau"] = "nudge", 0.0
                    sheep["wall0"], sheep["d"] = last_s + PW / 2, slack
                    self.nudges.append((f + 0.78, slack))
            elif sheep["phase"] == "nudge":
                u = ease(sheep["tau"], 0.78, 1.18)
                if 0.72 <= sheep["tau"] <= 1.3:
                    wall = sheep["wall0"] - sheep["d"] * u
                if sheep["tau"] >= 2.0:
                    sheep["phase"], sheep["tau"], sheep["last"] = "idle", 0.0, f
            self.log_s.append((sheep["x"], sheep["y"], sheep["phase"], sheep["tau"], sheep.get("move", False), sheep["d"]))
            # ---- the pieces: the current and drag, then the collision boundaries
            for p in ps:
                F = current(f, p["idx"])
                p["v"] += WDT * (F - c * p["v"]) / m
                p["s"] += WDT * p["v"]
                p["w"] += WDT * (0.55 * F - kt * p["th"] - ct * p["w"]) / mt
                p["th"] += WDT * p["w"]
            if ps:
                if wall is not None and ps[-1]["s"] + PW / 2 > wall:      # the nose
                    ps[-1]["s"], ps[-1]["v"] = wall - PW / 2, min(ps[-1]["v"], 0.0)
                for k in range(len(ps) - 2, -1, -1):                      # pushed from the open end
                    if ps[k + 1]["s"] - ps[k]["s"] < PW:
                        ps[k]["s"] = ps[k + 1]["s"] - PW
                        ps[k]["v"] = min(ps[k]["v"], ps[k + 1]["v"])
                if ps[0]["s"] < 0.0:                                      # the felt dog does not move
                    ps[0]["s"], ps[0]["v"] = 0.0, max(0.0, ps[0]["v"])
                for k in range(len(ps) - 1):                              # and each held by the one before it
                    if ps[k + 1]["s"] - ps[k]["s"] < PW:
                        ps[k + 1]["s"] = ps[k]["s"] + PW
                        ps[k + 1]["v"] = max(ps[k + 1]["v"], ps[k]["v"])
            self.log_p.append([(p["s"], p["th"], p["on"], p["pending"]) for p in self.pieces])

    def _i(self, f):
        return int(clamp(round((f - T_WORK) / WDT), 0, self.n - 1))

    def pieces_at(self, f):
        """[(index, s, tilt)] of the pieces standing at f."""
        if f < T_WORK:
            return []
        return [(k, s, th) for k, (s, th, on, pend) in enumerate(self.log_p[self._i(f)]) if on]

    def retriever(self, name, f):
        return self.log_r[name][self._i(f)]

    def sheep(self, f):
        return self.log_s[self._i(f)]

    def count(self, f):
        return len(self.pieces_at(f))

    def gaps(self, f):
        xs = sorted(s for _, s, _ in self.pieces_at(f))
        return [b - a - PW for a, b in zip(xs, xs[1:])]

    def stock(self, name, f):
        """How many pieces still lean at this retriever's lamp."""
        n, prev = 0, None
        for (x, y, ph, tau, fac) in self.log_r[name][: self._i(f) + 1: 12]:
            if ph == "carry" and prev == "pick":
                n += 1
            prev = ph
        return max(0, 5 - n)


@lru_cache(maxsize=None)
def works():
    return Works()


SHELL_DELAY = 0.9                            # after a piece stands, the felt dog sends its shell
SHELL_Y = LINE_Y + 8.0
FELT_AT = (XC0 + PW / 2 + 23.0, LINE_Y + 2.0)        # flat at the row's end, ear to the gravel: the row stands against it


def shells_at(f):
    """The felt dog's small white shells, one for each piece: slid along the foot of the row with one paw, each
    coming to rest at its piece's true place (a mass with drag and nothing else: it stops because the water stops it).
    -> [(x, y, moving 0..1)]"""
    w = works()
    order = [tl for tl, idx, by in sorted(w.landings) if by != "blood"]
    out = []
    x_from = FELT_AT[0] - 26.0
    for k, tl in enumerate(order):
        ts = tl + SHELL_DELAY
        if f >= ts:
            u = 1 - math.exp(-3.4 * (f - ts))                 # v' = -c v: all drag
            if f - ts > 1.6:
                u = 1.0
            out.append((lerp(x_from, piece_x(PW * k), u), SHELL_Y, 1 - u))
    return out


def felt_town(f):
    """Flat at the row's end, ear to the gravel, never lifting its head. -> (x, y, paw 0..1)."""
    w = works()
    order = [tl for tl, idx, by in sorted(w.landings) if by != "blood"]
    paw = 0.0
    for tl in order:
        paw = max(paw, bump((f - (tl + SHELL_DELAY - 0.3)) / 0.6))       # one paw out and back: the shell goes
    return FELT_AT[0], FELT_AT[1], paw


# ---- agendas: the lead, the digger, the terrier, the herder, the bloodhound ----

def _hole_at(k, off=0.0, dy=2.0):
    x, y = town.hole_xy(k)
    return (x - off, y + dy)


@lru_cache(maxsize=None)
def lead_agenda():
    off = 40.0
    (px, py), ta = PLACE["lead"]
    A = Agenda(ta, (px, py), 135.0)
    A.do("land", 0.6, hole=24)
    A.go(_hole_at(39, off)).do("dig", 1.2, hole=39, face=1, find=True)           # digs: a part
    A.go((352.0, 812.0), kind="carry", speed=70.0).do("lay", 1.2, face=1)        # carries it to the foot of the board
    A.go((331.0, 829.0)).do("nose", 2.4, face=1, page=4)                         # looks
    A.go(_hole_at(12, off)).do("dig", 1.1, hole=12, face=1)
    A.go((360.0, 829.0)).do("nose", 2.2, face=1, page=5)
    A.go(_hole_at(19, off)).do("dig", 1.0, hole=19, face=1)
    A.go(_hole_at(27, off)).do("dig", 1.0, hole=27, face=1, find=True)
    A.go((356.0, 813.0), kind="carry", speed=70.0).do("lay", 1.2, face=1)
    A.go((303.0, 829.0))
    A.until(114.35, "wait", face=1)
    A.until(T1 + 2, "nose", face=1, page=3)
    return A


@lru_cache(maxsize=None)
def digger_agenda():
    (px, py), ta = PLACE["digger"]
    A = Agenda(ta, (px, py), 160.0)
    A.do("land", 0.5, hole=34)
    A.until(101.0, "wait", face=1)
    for k in (10, 36, 22):
        A.go(_hole_at(k, 16.0)).do("dig", 0.8, hole=k, face=1)
    for q, (bx, by) in enumerate(((594.0, 806.0), (486.0, 806.0), (502.0, 797.0), (578.0, 797.0))):
        A.go((bx - 21, by)).do("build", 1.0, face=1, post=q + 1)
    for k in (25, 11, 33):
        A.go(_hole_at(k, 16.0)).do("dig", 0.8, hole=k, face=1)
    A.go((540.0, 800.0))
    A.until(T1 + 2, "wait", face=1)
    return A


@lru_cache(maxsize=None)
def terrier_agenda():
    (px, py), ta = PLACE["terrier"]
    A = Agenda(ta, (px, py), 150.0)
    A.do("land", 0.45, hole=15)
    A.until(101.0, "wait", face=1)
    A.go(_hole_at(7, 0.0, 0.0)).do("down", 1.9, face=1, hole=7)                  # the one hole that is wrong
    A.do("up", 2.2, face=1, hole=7)
    for k in (16, 20, 31, 13, 38, 23, 17, 18, 37, 8, 9):
        A.go(_hole_at(k, 14.0)).do("dig", 0.48, hole=k, face=1)
    A.go(_hole_at(26, 0.0, 0.0)).do("dig_in", 0.6, hole=26, face=1)
    A.until(T1 + 2, "tail", face=1, hole=26)
    return A


CLASS_C = (683.0, 826.0)
GATE_X = 560.0
FIRST_ROUND, SECOND_ROUND = (0, 1, 2), (3, 4, 5)               # whose pages it gathers, before and after the gate


def _gather_xy(k):
    sx, sy = town.SEATS[k]
    return (sx - 58.0, sy + 12.0 if k < 4 else sy + 6.0)


@lru_cache(maxsize=None)
def herder_agenda():
    (px, py), ta = PLACE["herder"]
    A = Agenda(ta, (px, py), 150.0)
    A.do("land", 0.5, hole=29)
    A.until(101.0, "wait", face=1)
    A.do("circle", 1.75)
    for k in FIRST_ROUND:
        A.go(_gather_xy(k), speed=170.0)
        A.do("gather", 0.95, face=1, child=k)
    A.go((GATE_X + 26.0, 826.0), kind="carry", speed=110.0)
    A.until(107.45, "wait_pages", face=-1)
    A.go((GATE_X, 798.0), kind="edge", speed=22.0, face=-1)                      # edge-on through the gate: nothing bends
    A.go((534.0, 797.0), kind="carry", speed=60.0, face=-1)
    A.do("lay_pages", 0.8, face=-1)
    A.go((GATE_X, 798.0), speed=70.0)
    A.go((GATE_X + 10.0, 826.0), kind="edge", speed=30.0, face=1)
    for k in SECOND_ROUND:
        A.go(_gather_xy(k), speed=170.0)
        A.do("gather", 0.95, face=1, child=k)
    A.until(T1 + 2, "wait_pages", face=1)
    return A


def gather_time(k):
    """When the herder's jaws close on child k's page (None if it does not come for it in this sequence)."""
    s = herder_agenda().find("gather", child=k)
    return s.a + 0.42 * (s.b - s.a) if s else None


def herder_pages(f):
    """Pages against its chest at f."""
    n = sum(1 for k in FIRST_ROUND if f >= gather_time(k))
    lay = herder_agenda().find("lay_pages")
    if lay and f >= lay.a + 0.4:
        n = 0
    return n + sum(1 for k in SECOND_ROUND if f >= gather_time(k))


def pages_laid(f):
    lay = herder_agenda().find("lay_pages")
    return 3 if (lay and f >= lay.a + 0.4) else 0


KID_ASK = 1                                  # the child the bloodhound's trail leads to (its drawing: two fish and a bell)
KID_ASK2 = 5
T_BUBBLE = 109.5


@lru_cache(maxsize=None)
def blood_plan():
    """The bloodhound's errand, timed from the row: -> dict of times and places."""
    w = works()
    t_take = w.t_take
    i = w._i(t_take - WDT * 2)
    s1 = max(s_ for (s_, th, on, pend) in w.log_p[i] if on)
    px = piece_x(s1)                                              # the piece it takes: the newest, at the open end
    stand = (px - PW / 2 - 47.0 - 1.0, LINE_Y + 5.0)
    kx, ky = town.SEATS[KID_ASK]
    ask_at = (kx + 16.0 + 47.0 + 5.0, ky + 18.0)                  # nose at the child's desk, the child on its left
    trail = [(stand[0] - 30, LINE_Y + 2), (lerp(stand[0], ask_at[0], 0.5) - 47, LINE_Y - 6), (ask_at[0] - 47.0, ask_at[1] - 2)]
    j = w._i(w.t_back - WDT * 2)
    ends = [s_ for (s_, th, on, pend) in w.log_p[j] if on or pend]
    put_at = (piece_x(max(ends) + PW + GAP) - 47.0 - 1.0, LINE_Y + 5.0)
    # the second errand: it noses a piece where it stands in the row, and sets off again
    t2 = w.t_back + 0.9
    k2x, k2y = town.SEATS[KID_ASK2]
    j2 = w._i(t2)
    last = max(s_ for (s_, th, on, pend) in w.log_p[j2] if on)
    stand2 = (piece_x(last) - PW / 2 - 47.0 - 1.0, LINE_Y + 5.0)
    ask2 = (k2x + 16.0 + 47.0 + 5.0, k2y + 30.0)
    trail2 = [(stand2[0] - 30, LINE_Y + 2), (lerp(stand2[0], ask2[0], 0.5) - 47, LINE_Y - 12), (ask2[0] - 47.0, ask2[1] - 2)]
    return dict(t_take=t_take, t_back=w.t_back, piece_x=px, stand=stand, ask_at=ask_at, trail=trail, put_at=put_at,
                t2=t2, stand2=stand2, ask2=ask2, trail2=trail2)


@lru_cache(maxsize=None)
def blood_agenda():
    bp = blood_plan()
    (px, py), ta = PLACE["blood"]
    A = Agenda(ta, (px, py), 46.0)
    A.do("land", 0.5, hole=21)
    A.go((640.0, LINE_Y + 8.0), speed=60.0)
    A.until(bp["t_take"] - 2.6, "sit", face=1)
    A.go(bp["stand"], speed=90.0)
    A.until(bp["t_take"] - 1.3, "stand", face=1)
    A.do("sniff", 1.3, face=1)                                                   # nose down at the newest piece: it knows
    A.until(bp["t_take"] + 0.35, "hold", face=1)
    d = math.hypot(bp["ask_at"][0] - bp["stand"][0], bp["ask_at"][1] - bp["stand"][1])
    A.go(bp["ask_at"], kind="follow", speed=d / max(0.5, T_BUBBLE - 0.5 - A.t), face=-1)   # nose down, back along the scent
    A.until(111.0, "ask", face=-1)
    d = math.hypot(bp["put_at"][0] - bp["ask_at"][0], bp["put_at"][1] - bp["ask_at"][1])
    A.go(bp["put_at"], kind="carry_back", speed=d / max(0.4, bp["t_back"] - 0.9 - A.t), face=1)
    A.until(bp["t_back"] - 0.9, "hold", face=1)
    A.do("put", 1.3, face=1)
    A.go(bp["stand2"], speed=90.0, face=1)
    A.until(bp["t2"], "stand", face=1)
    A.do("sniff", 0.8, face=1)
    d = math.hypot(bp["ask2"][0] - bp["stand2"][0], bp["ask2"][1] - bp["stand2"][1])
    A.go(bp["ask2"], kind="follow2", speed=d / (2.0 * max(0.3, T1 - A.t)), face=-1)          # halfway along it at 116.0
    A.until(T1 + 3, "ask2", face=-1)
    return A


@lru_cache(maxsize=None)
def hole_times():
    """{hole index: (t0, t1)} for every hole dug in this sequence, from whoever digs it."""
    out = {}
    for name, ag in (("lead", lead_agenda()), ("digger", digger_agenda()), ("terrier", terrier_agenda()),
                     ("herder", herder_agenda()), ("blood", blood_agenda())):
        for s in ag.segs:
            if s.kind in ("dig", "land", "dig_in") and "hole" in s.kw and s.kw["hole"] >= 8:
                out[s.kw["hole"]] = (s.a + 0.05, s.b)
    for name in ("big", "mid", "small", "sheep", "felt"):
        ta = PLACE[name][1]
        out[LAND_HOLE[name]] = (ta - 0.05, ta + 0.5)
    return out


def holes_dug(f):
    return 8 + sum(1 for a, b in hole_times().values() if f >= b)


def murk(ink, cam, f):
    """Dark water coming up out of the one wrong hole, until the terrier has been down it."""
    A = terrier_agenda()
    down = A.find("down")
    stop = down.a + 1.3
    lvl = ease(f, 99.6, 100.4) * (1 - ease(f, stop, stop + 1.2))
    if lvl <= 0.01:
        return
    hx, hy = town.hole_xy(7)
    z = cam.zoom
    for q in range(14):
        ph = (f * 0.55 + q / 14.0) % 1.0
        wx = hx + 10 * math.sin(q * 2.3 + f * 1.2) * ph + 6 * ph
        wy = hy - 4 - 74 * ph
        sx, sy = cam.xy(wx, wy)
        r = (5 + 13 * ph) * z
        a = int(150 * lvl * (1 - ph) ** 0.8)
        ink.d.ellipse([sx - r, sy - r * 0.8, sx + r, sy + r * 0.8], fill=(22, 30, 40, a))


# ====================================================================== #
#  8 · THE TOWN: drawing                                                 #
# ====================================================================== #

UNDER = dict(tint=kb.WATER, tint_amount=0.3)
LEAD_UNDER = dict(tint=TEAL, tint_amount=0.3, shadow=False)


def kid_state(k, f):
    """One fish child -> dict of town.child keywords plus x, y."""
    sx, sy = town.SEATS[k]
    wake = track(f"kid{k}").x(f)
    st = dict(x=sx, y=sy, tilt=8.0 + wake, facing=1, arm=20.0, look=None, hold=None, mouth_open=0.0, swim=0.3)
    # the pack comes down: every face goes up, mouths round
    arrive = ease(f, 98.9, 99.5) * (1 - ease(f, 100.9, 101.6))
    if arrive > 0.02:
        near = min(PACK, key=lambda n: abs((dive(n, f) or {"x": 1e9})["x"] - sx) if dive(n, f) and dive(n, f)["phase"] == "swim" else 1e9)
        dv = dive(near, f)
        if dv and dv["phase"] == "swim":
            st["look"] = (dv["x"], dv["y"])
        else:
            st["look"] = (sx - 60, 560)
        st["mouth_open"] = 1.0 if arrive > 0.4 else 0.0
        st["tilt"] = lerp(st["tilt"], -12.0 + wake, arrive)
    elif f >= 100.9:
        seg, tau, u, hx, hy = herder_agenda().at(f)
        st["look"] = (hx, hy - 16)
    tg = gather_time(k)
    if tg is not None:
        t_out = 101.7 + 0.15 * k if k in FIRST_ROUND else 110.6 + 0.2 * k
        if t_out <= f < tg:
            st["hold"] = "page:" + town.CHILD_DRAWS[k]
            st["arm"] = 20 + 70 * ease(f, t_out, t_out + 0.5)
            st["facing"] = -1
        elif f >= tg:
            st["arm"] = 20 + 50 * (1 - ease(f, tg, tg + 0.6))
            st["facing"] = -1 if f < tg + 0.8 else 1
    if k == KID_ASK and T_BUBBLE - 1.2 <= f < 113.0:           # the bloodhound has come to ask
        st["facing"] = -1
        st["look"] = (sx - 40, sy - 4)
        st["mouth_open"] = 1.0 if T_BUBBLE <= f < T_BUBBLE + 1.2 else 0.0
    if k == 7:                                                 # the one who swims up to look at the calf
        up = ease(f, 104.0, 105.5) * (1 - ease(f, 107.6, 109.4))
        if up > 0.01:
            st["x"] = lerp(sx, 676.0, smooth(up))
            st["y"] = lerp(sy, 446.0, smooth(up)) + 3 * math.sin(f * 1.7)
            st["tilt"] = lerp(8.0, 34.0, up)
            st["facing"] = -1
            st["look"] = (660.0, 402.0)
            st["swim"] = 0.4 + 0.6 * bump((f - 104.0) / 1.5)
            st["arm"] = 20 + 90 * bump((f - 105.6) / 1.4)
    return st


def bubble_state(f):
    grow = ease(f, T_BUBBLE, T_BUBBLE + 1.0)
    prog = ramp(f, T_BUBBLE + 0.3, T_BUBBLE + 1.3)
    rise = 22 * ease(f, 111.6, 113.2)
    pop = ramp(f, 112.9, 113.2)
    return grow, prog, rise, pop


def draw_kids(ink, f, cam, calm=False):
    out = {}
    for k in (4, 5, 6, 7, 0, 1, 2, 3):
        st = dict(kid_state(k, f))
        x, y = st.pop("x"), st.pop("y")
        out[k] = town.child(ink, f, cam, k, x, y, **st)
    return out


def calf_dip(f):
    """How far the calf's muzzle is in the water, seen from below."""
    return 0.3 * ease(f, 98.6, 99.6) + 0.7 * ease(f, 104.6, 105.0) * (1 - ease(f, 106.2, 107.0))


def _fence_front(ink, cam):
    """The yard fence again, over somebody who is behind it."""
    z = cam.zoom
    fx = 520
    while fx <= 600:
        if not (546 < fx < 574):
            a, b = cam.xy(fx, town.BED_Y + 7), cam.xy(fx, town.BED_Y - 12)
            ink.d.line([a, b], fill=(214, 190, 140, 255), width=max(1, int(round(2.2 * z))))
            c = cam.xy(fx, town.BED_Y - 13)
            ink.d.ellipse([c[0] - 1.9 * z, c[1] - 1.9 * z, c[0] + 1.9 * z, c[1] + 1.9 * z], fill=(40, 30, 28, 255))
        fx += 7
    for s0, s1 in ((520, 546), (574, 602)):
        ink.d.line([cam.xy(s0, town.BED_Y - 5), cam.xy(s1, town.BED_Y - 5)], fill=(190, 166, 120, 255), width=max(1, int(round(1.2 * z))))


def _post(ink, cam, wx, wy, f_in=1.0, tall=17.0):
    z = cam.zoom
    a = cam.xy(wx, wy + 3)
    b = cam.xy(wx, wy - tall * (0.45 + 0.55 * (1 - f_in)) - tall * 0.0)
    ink.d.line([a, b], fill=(18, 30, 34, 255), width=max(2, int(round(4.4 * z))))
    ink.d.line([a, b], fill=(134, 110, 80, 255), width=max(1, int(round(2.8 * z))))
    ink.d.ellipse([b[0] - 2.4 * z, b[1] - 1.6 * z, b[0] + 2.4 * z, b[1] + 1.6 * z], fill=(170, 144, 104, 255), outline=(18, 30, 34, 255))


def _lead_town(ink, f, cam):
    dv = dive("lead", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        sx, sy = cam.xy(dv["x"], dv["y"])
        pose = dog.swim_down(f, steep=clamp(-dv["pitch"], 0.1, 0.9)) if dv["u"] < 0.8 else dog.swim(f)
        dog.draw_dog(ink, pose, sx, sy, scale=DS * z, facing=dv["facing"], **LEAD_UNDER)
        return
    A = lead_agenda()
    seg, tau, u, x, y = A.at(f)
    sx, sy = cam.xy(x, y)
    kind = seg.kind
    carry = None
    if kind == "land":
        pose = dog.blend(dog.dig(tau), dog.stand(f), ease(tau, 0.4, 0.6))
    elif kind == "go":
        pose = dog.trot(f)
    elif kind == "dig":
        pose = dog.dig(tau)
        if seg.kw.get("find") and u > 0.8:
            pose = dog.blend(pose, dog.holding(dog.stand(f), "part"), ease(u, 0.8, 1.0))
            carry = props.part_sprite("gear", t=f, **props.UNDER)
        dog.draw_bits(ink, dog.dig_spray(tau, water=True), sx, sy, DS * z, facing=seg.facing)
    elif kind == "carry":
        pose = dog.carry_part(f, gait="trot")
        carry = props.part_sprite("gear", t=f, **props.UNDER)
    elif kind == "lay":
        pose = dog.lay(tau)
        carry = props.part_sprite("gear", t=f, **props.UNDER) if tau < 0.62 else None
    elif kind == "nose":
        pose = dog.nose_page(min(tau, 2.2) if seg.b < T1 else min(tau, 1.9))
    else:
        pose = dog.stand(f)
    j = dog.draw_dog(ink, pose, sx, sy, scale=DS * z, facing=seg.facing, carry=carry, **LEAD_UNDER)
    return j


def _parts_laid(ink, f, cam):
    for q, s in enumerate(lead_agenda().all("lay")):
        if f >= s.a + 0.62:
            sx, sy = cam.xy(s.p0[0] + 40 + 14 * q, 806.0)
            props.part(ink, sx, sy, DS * cam.zoom, "gear" if q == 0 else "flange", mud=0.6, wet=1, weed=0.5, t=f, **props.UNDER)


def _digger_town(ink, f, cam):
    dv = dive("digger", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        sx, sy = cam.xy(dv["x"], dv["y"])
        ka.digger(ink, sx, sy, GS * z, dv["facing"], "swim", t=f)
        return
    seg, tau, u, x, y = digger_agenda().at(f)
    sx, sy = cam.xy(x, y)
    if seg.kind in ("dig", "land"):
        ka.digger(ink, sx, sy, GS * z, seg.facing, "dig", t=tau)
    elif seg.kind == "build":
        ka.digger(ink, sx, sy, GS * z, seg.facing, "build", t=f, p=u)
    elif seg.kind == "go":
        ka.digger(ink, sx, sy, GS * z, seg.facing, "walk", t=f)
    else:
        ka.digger(ink, sx, sy, GS * z, seg.facing, "wait")


def _posts(ink, f, cam, front):
    """The four corner posts of the making place, once the digger has driven each."""
    for s_ in digger_agenda().all("build"):
        if f < s_.b - 0.05:
            continue
        wx, wy = s_.p0[0] + 21 + 9, s_.p0[1]
        if (wy > 803) == front:
            _post(ink, cam, wx, wy, tall=15.0)


def _terrier_town(ink, f, cam):
    dv = dive("terrier", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        sx, sy = cam.xy(dv["x"], dv["y"])
        kb.terrier(ink, sx, sy, "swim", f, scale=TS * z, facing=dv["facing"], rot=-dv["pitch"] * dv["facing"], shadow=False, **UNDER)
        return
    seg, tau, u, x, y = terrier_agenda().at(f)
    sx, sy = cam.xy(x, y)
    k = seg.kind
    if k == "go":
        kb.terrier(ink, sx, sy, "walk", f, scale=TS * z, facing=seg.facing, carry="fix" if seg.a > 104 and seg.a < 106.2 else None, **UNDER)
    elif k == "down":
        kb.terrier(ink, sx, sy, "dive", tau, scale=TS * z, facing=seg.facing, **UNDER)
    elif k == "up":
        kb.terrier(ink, sx, sy, "come_up", tau, scale=TS * z, facing=seg.facing, carry="fix", **UNDER)
    elif k in ("dig", "land"):
        hx, hy = cam.xy(*town.hole_xy(seg.kw["hole"]))
        tt = 0.24 + 0.36 * bump(u)                              # head and shoulders into it and out again
        kb.terrier(ink, hx, hy, "dive", tt, scale=TS * z, facing=seg.facing, **UNDER)
    elif k == "dig_in":
        kb.terrier(ink, sx, sy, "dive", tau * 1.6, scale=TS * z, facing=seg.facing, stay=True, **UNDER)
    elif k == "tail":
        kb.terrier(ink, sx, sy, "dive", 1.6 + tau, scale=TS * z, facing=seg.facing, stay=True, **UNDER)
    else:
        kb.terrier(ink, sx, sy, "wait", tau, scale=TS * z, facing=seg.facing, **UNDER)


def herder_town(f):
    """-> dict(x, y, facing, action, t, p, pages, behind_class, behind_fence)."""
    A = herder_agenda()
    seg, tau, u, x, y = A.at(f)
    k = seg.kind
    pages = herder_pages(f)
    out = dict(x=x, y=y, facing=seg.facing, action="wait", t=f, p=0.0, pages=pages, behind=False, fence=False, size=1.0)
    if k == "circle":
        cx, cy = CLASS_C
        dur = seg.b - seg.a
        hx, hy, fac, behind, size = ka.herd_circle(cx, cy + 6, 112.0, 30.0, tau, period=dur, start=0.56)
        out.update(x=hx, y=hy, facing=fac, action="circle", behind=behind, size=size)
    elif k == "go":
        out.update(action="circle" if pages == 0 else "carry")
    elif k == "carry":
        out.update(action="carry")
    elif k == "gather":
        out.update(action="gather", p=u, pages=herder_pages(seg.a - 0.01))
    elif k == "edge":
        out.update(action="turn", p=0.5 * ease(u, 0.0, 0.22) * (1 - ease(u, 0.8, 1.0)))     # edge-on in the gap, then round again
    elif k == "lay_pages":
        out.update(action="gather", p=0.3 * bump(u))
    elif k in ("wait_pages", "wait", "land"):
        out.update(action="wait")
    out["fence"] = y < 803.0 and 500 < x < 610
    return out


def _herder_town(ink, f, cam, st=None):
    dv = dive("herder", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        sx, sy = cam.xy(dv["x"], dv["y"])
        with_halo(ink, lambda layer: ka.herding_dog(layer, sx, sy + 8 * z, HS * z, dv["facing"], "swim", t=f),
                  color=(150, 214, 206), alpha=120)
        return
    st = st or herder_town(f)
    sx, sy = cam.xy(st["x"], st["y"])
    with_halo(ink, lambda layer: ka.herding_dog(layer, sx, sy, HS * z * st["size"], st["facing"], st["action"], t=st["t"],
                                                 p=st["p"], pages=st["pages"]),
              color=(150, 214, 206), alpha=130)
    if st["fence"]:
        _fence_front(ink, cam)


def _page_stack(ink, f, cam):
    n = pages_laid(f)
    for q in range(n):
        sx, sy = cam.xy(520.0 + 3 * q, 796.0 - 2.2 * q)
        props.page(ink, sx, sy, 0.5 * cam.zoom, town.CHILD_DRAWS[q], flat=0.86, angle=-4 + 5 * q, **props.UNDER)


def _retriever_town(ink, name, f, cam):
    dv = dive(name, f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        _kb_swim(ink, kb.retriever, name, cam, dv, f, size=name)
        return
    side = STOCK[name][2]
    if f < T_WORK:
        (px, py), ta = PLACE[name]
        sx, sy = cam.xy(px, py)
        kb.retriever(ink, sx, sy, "wait", f - ta, scale=RS * z, size=name, facing=side,
                     carry="piece" if f > T_WORK - 0.25 else None, **UNDER)
        return
    x, y, ph, tau, fac = works().retriever(name, f)
    sx, sy = cam.xy(x, y)
    roll = f * RET_V[name] / (RS * 75.0 * kb.RET_SIZE[name])           # wheels turn as far as the ground goes by
    if ph == "pick":
        kb.retriever(ink, sx, sy, "wait", tau, scale=RS * z, size=name, facing=fac, arrive=0,
                     carry="piece" if tau > 0.25 else None, **UNDER)
    elif ph == "carry":
        kb.retriever(ink, sx, sy, "carry", roll, scale=RS * z, size=name, facing=1, carry="piece", **UNDER)
    elif ph == "set":
        kb.retriever(ink, sx, sy, "set_down", min(tau, 0.98) if tau < 1.0 else tau, scale=RS * z, size=name, facing=1,
                     carry="piece" if tau < 1.0 else None, **UNDER)
    else:
        kb.retriever(ink, sx, sy, "walk", roll, scale=RS * z, size=name, facing=-1, **UNDER)


def _sheep_town(ink, f, cam):
    dv = dive("sheep", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        _kb_swim(ink, kb.sheepdog, "sheep", cam, dv, f)
        return
    if f < T_WORK:
        (px, py), ta = PLACE["sheep"]
        sx, sy = cam.xy(px, py)
        kb.sheepdog(ink, sx, sy, "wait", f - ta, scale=RS * z, facing=1, **UNDER)
        return
    x, y, ph, tau, moving, d = works().sheep(f)
    sx, sy = cam.xy(x, y)
    if ph == "nudge":
        kb.sheepdog(ink, sx, sy, "nudge", tau, scale=RS * z, facing=1, push=d / (RS * kb.UNIT["sheepdog"]), **UNDER)
    elif ph == "out" or moving:
        kb.sheepdog(ink, sx, sy, "walk", f * 1.4, scale=RS * z, facing=-1 if ph == "out" else 1, **UNDER)
    else:
        kb.sheepdog(ink, sx, sy, "wait", 4.0 + tau, scale=RS * z, facing=1, **UNDER)


def blood_town(f):
    """-> dict for drawing the bloodhound in town."""
    A = blood_agenda()
    bp = blood_plan()
    seg, tau, u, x, y = A.at(f)
    k = seg.kind
    dist = math.hypot(x - seg.p0[0], y - seg.p0[1])
    st = dict(x=x, y=y, facing=seg.facing, action="wait", t=tau, carry=None, trail=None, upto=1.0, kw={})
    if k == "land":
        st.update(action="wait", t=tau, kw=dict(sit=False))
    elif k == "go":
        st.update(action="walk", t=dist / (RS * kb.travel("bloodhound", "walk", 1.0)))
    elif k == "sit":
        st.update(action="wait", t=tau)
    elif k == "stand":
        st.update(action="wait", t=9.0, kw=dict(sit=False))
    elif k == "sniff":
        st.update(action="nose_down", t=tau * (2.0 / (seg.b - seg.a)))
    elif k == "hold":
        st.update(action="wait", t=9.0, carry="piece", kw=dict(sit=False), trail=bp["trail"], upto=ease(tau, 0.0, 0.3))
    elif k == "follow":
        st.update(action="follow", t=dist / (RS * kb.travel("bloodhound", "follow", 1.0)), carry="piece", trail=bp["trail"])
    elif k == "ask":                                              # sits at the child's desk with the piece, and looks up
        st.update(action="wait", t=tau, carry="piece", kw=dict(look=0.45 * ease(f, T_BUBBLE, T_BUBBLE + 0.6)), trail=bp["trail"])
    elif k == "carry_back":
        st.update(action="carry", t=dist / (RS * kb.travel("bloodhound", "carry", 1.0)), carry="piece")
    elif k == "put":
        st.update(action="nose_down", t=0.4 + tau, carry="piece" if tau < 0.9 else None)
    elif k in ("follow2", "ask2"):
        st.update(action="follow", t=dist / (RS * kb.travel("bloodhound", "follow", 1.0)), trail=bp["trail2"])
    return st


def _blood_town(ink, f, cam):
    dv = dive("blood", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        _kb_swim(ink, kb.bloodhound, "blood", cam, dv, f)
        return
    st = blood_town(f)
    sx, sy = cam.xy(st["x"], st["y"])
    if st["trail"]:
        kb.scent_trail(ink, [cam.xy(*p) for p in st["trail"]], upto=st["upto"], r=1.3 * z, gap=9.0 * z)
    kb.bloodhound(ink, sx, sy, st["action"], st["t"], scale=RS * z, facing=st["facing"], carry=st["carry"], **UNDER, **st["kw"])


def _felt_town(ink, f, cam):
    dv = dive("felt", f)
    z = cam.zoom
    if dv and dv["phase"] == "swim":
        sx, sy = cam.xy(dv["x"], dv["y"])
        felt_dog(ink, sx, sy + 12 * z, z, dv["facing"], lift=1.0, ear=1.0 + 0.3 * math.sin(f * 9), rot=-dv["pitch"] * dv["facing"], under=True)
        return
    (px, py), ta = PLACE["felt"]
    t_home = ta + 1.9
    if f < t_home:                                               # waddles to the end of where the row will be, and lies down
        u = ease(f, ta + 0.3, t_home - 0.5)
        x, y = lerp(px, FELT_AT[0], u), lerp(py, FELT_AT[1], u)
        down = ease(f, t_home - 0.5, t_home)
        sx, sy = cam.xy(x, y)
        felt_dog(ink, sx, sy, z, 1 if u < 0.98 else -1, lift=1 - down, ear=1 - down, hop=abs(math.sin((f - ta) * 9.0)) * (1 - down) * (1 if 0 < u < 1 else 0), under=True)
        return
    x, y, paw = felt_town(f)
    sx, sy = cam.xy(x, y)
    felt_dog(ink, sx, sy, z, -1, lift=0.0, ear=0.0, paw=paw, under=True)


def _pieces(ink, f, cam):
    z = cam.zoom
    for (k, s_, th) in sorted(works().pieces_at(f), key=lambda p: p[1]):
        px, py = cam.xy(piece_x(s_), LINE_Y)
        kb.draw_thing(ink, "piece", px, py, PS * z, angle=clamp(-th, -0.3, 0.3), **UNDER)


def _shells(ink, f, cam):
    z = cam.zoom
    for (x, y, mv) in shells_at(f):
        sx, sy = cam.xy(x, y)
        r = 2.7 * z
        if mv > 0.05:                                            # a little silt behind it while it slides
            ink.d.ellipse([sx + 2 * z, sy - 2 * z, sx + (4 + 14 * mv) * z, sy + 2 * z], fill=(170, 186, 168, int(90 * mv)))
        ink.d.ellipse([sx - r, sy - r * 0.7, sx + r, sy + r * 0.7], fill=(236, 242, 232, 255), outline=(40, 70, 76, 255))
        ink.d.arc([sx - r * 0.6, sy - r * 0.4, sx + r * 0.6, sy + r * 0.5], 200, 340, fill=(150, 176, 170, 255))


def _lamp_stock(ink, f, cam):
    """Pieces of film leaning at the feet of three lamps: where the retrievers fetch them from."""
    z = cam.zoom
    w = works()
    for name in ("small", "mid", "big"):
        lx, ly, side = STOCK[name]
        n = w.stock(name, f) if f >= T_WORK else 5
        for q in range(n - 1, -1, -1):
            sx, sy = cam.xy(lx + side * 7 * q, ly - 1.2 * q)
            kb.draw_thing(ink, "piece", sx, sy, PS * z, angle=side * (0.2 + 0.03 * q), **UNDER)


def town_set(ink, f, cam, sky, calm=False):
    """Water, far town, street, and everything that lies on the bed. Returns the class anchors later."""
    bell = track("bell").x(f)
    town.back(ink, f, cam, sky=sky)
    town.street(ink, f, cam, bell=bell, holes=8, smudges=int(lerp(5, 30, ramp(f, 101.0, 116.0))))
    ht = hole_times()
    for q in sorted(ht, key=lambda q: town.HOLES[q][1]):
        a, b = ht[q]
        draw_hole(ink, cam, q, ramp(f, a, b))
    dg = digger_agenda()
    n_dug = sum(1 for s in dg.all("dig") if f >= s.b and s.kw["hole"] in (10, 34, 36))
    n_post = sum(1 for s in dg.all("build") if f >= s.b and s.kw["post"] >= 1)
    prog = (n_dug * 2 + min(2, n_post)) / 8.0
    cur = [s for s in dg.all("dig") if s.a <= f < s.b and s.kw["hole"] in (10, 34, 36)]
    if cur:
        prog += 2 / 8.0 * ramp(f, cur[0].a, cur[0].b)
    town.making_place(ink, cam, clamp(prog))
    _posts(ink, f, cam, front=False)
    _page_stack(ink, f, cam)
    _parts_laid(ink, f, cam)
    _lamp_stock(ink, f, cam)
    murk(ink, cam, f)


def town_cast(ink, f, cam):
    """Everybody on the bed, sorted by how near they stand."""
    todo = []
    look = None
    for nm in PACK:
        dv = dive(nm, f)
        if dv and dv["phase"] == "swim":
            look = (dv["x"], dv["y"])
            break
    if look is None:
        seg, tau, u, lx, ly = lead_agenda().at(f)
        look = (lx, ly - 20)
    town.townsfolk(ink, f, cam, look=look)
    hst = herder_town(f) if dive("herder", f) and dive("herder", f)["phase"] is None else None
    if hst and hst["behind"]:
        _herder_town(ink, f, cam, hst)
    town.school_class(ink, f, cam, skip=tuple(range(8)), look={"T": look})
    kids = draw_kids(ink, f, cam)
    grow, prog, rise, pop = bubble_state(f)
    if grow > 0 and pop < 1:
        town.bubble(ink, f, cam, kids[KID_ASK]["mouth"], "fish_bell", grow=grow, progress=prog, r=30, side=-1, pop=pop,
                    rise=rise, screen=True)
    if hst and not hst["behind"]:
        todo.append((hst["y"], lambda: _herder_town(ink, f, cam, hst)))
    elif hst is None:
        todo.append((900, lambda: _herder_town(ink, f, cam)))

    def ypos(nm, fallback):
        dv = dive(nm, f)
        return 2000 if (dv and dv["phase"] == "swim") else fallback

    todo.append((ypos("lead", lead_agenda().at(f)[4]), lambda: _lead_town(ink, f, cam)))
    todo.append((ypos("digger", digger_agenda().at(f)[4]), lambda: _digger_town(ink, f, cam)))
    todo.append((ypos("terrier", terrier_agenda().at(f)[4]), lambda: _terrier_town(ink, f, cam)))
    for nm in ("big", "mid", "small"):
        yy = works().retriever(nm, f)[1] if f >= T_WORK else PLACE[nm][0][1]
        todo.append((ypos(nm, yy), lambda nm=nm: _retriever_town(ink, nm, f, cam)))
    todo.append((ypos("sheep", works().sheep(f)[1] if f >= T_WORK else PLACE["sheep"][0][1]), lambda: _sheep_town(ink, f, cam)))
    todo.append((806.5, lambda: _posts(ink, f, cam, front=True)))
    todo.append((LINE_Y, lambda: _pieces(ink, f, cam)))
    todo.append((LINE_Y + 8, lambda: _shells(ink, f, cam)))
    todo.append((ypos("felt", LINE_Y + 2 if f > PLACE["felt"][1] + 1.9 else PLACE["felt"][0][1]), lambda: _felt_town(ink, f, cam)))
    todo.append((ypos("blood", blood_agenda().at(f)[4]), lambda: _blood_town(ink, f, cam)))
    for y, fn in sorted(todo, key=lambda q: q[0]):
        fn()
    # silt where a dog has just come down onto the bed, and where one is digging
    for nm in PACK:
        (px, py), ta = PLACE[nm]
        silt(ink, cam, px, py, f - ta, 1.0, seed=hash(nm) % 97)
    for q, (a, b) in hole_times().items():
        if a <= f < b + 0.6:
            hx, hy = town.hole_xy(q)
            silt(ink, cam, hx, hy, (f - a) % 0.7 + 0.1, 0.7, seed=q)


def _calf_from_below(ink, f, cam):
    dipv = calf_dip(f)
    if dipv > 0.02:
        town.touch(ink, f, cam, 660, "muzzle", dip=dipv)
    if 104.9 <= f < 106.6:                                       # it blows bubbles
        z = cam.zoom
        rs = random.Random(5)
        for q in range(12):
            t0 = 104.95 + rs.uniform(0, 1.1)
            age = f - t0
            if 0 < age < 0.8:
                wx = 660 + rs.uniform(-14, 14) + 4 * math.sin(age * 9 + q)
                wy = 404 + rs.uniform(4, 26) * (1 - age / 0.8) + 2
                sx, sy = cam.xy(wx, wy)
                r = rs.uniform(1.6, 4.2) * z
                ink.d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(226, 246, 238, 220), width=max(1, int(1.2 * z)))


# ====================================================================== #
#  9 · THE PICTURE                                                       #
# ====================================================================== #

_OVERRIDE = {}                               # the proof sheet swaps a track for another damping preset


def howl_push(f):
    """A small push toward the dog while it howls, and out again as the answer starts to come from the edges."""
    return 1.0 + 0.15 * ease(f, 84.7, 86.3) * (1 - ease(f, 88.45, 89.5))


def _rings(f):
    rings = []
    for k, tk in enumerate((T_HOWL + 0.45, T_HOWL + 0.95, T_HOWL + 1.45, T_HOWL + 1.95)):
        if f >= tk:
            rings.append(porch.ring(560, tk, 4.0 - 0.3 * k))
    k = 0
    while T0 - 3 + 1.9 * k < min(f, T_HOWL + 0.2):               # the mother drinking
        rings.append(porch.ring(602, T0 - 3 + 1.9 * k, 0.45))
        k += 1
    for name in PACK:
        tg = t_go(name) + LEAP * 0.85
        if f >= tg:
            rings.append(porch.ring(ENTRY[name], tg, 1.25 if name in ("lead", "big", "sheep", "blood") else 0.95))
            rings.append(porch.ring(ENTRY[name] + 6, tg + 0.3, 0.7))
    return rings


def _porch_frame(ink, f, oy):
    """Everything while the porch is in frame (84.0 to 99.5, the crane included) and, at oy 360, the master."""
    anchors = {}
    cam = Cam(oy=oy)
    in_town = oy > 20

    def hill(ink, t, oy):
        draw_hill_cows(ink, f, oy)
        draw_herder_porch(ink, f, cam, "hill")

    def strip(ink, t, oy):
        draw_strip_cows(ink, f, oy, anchors)
        draw_herder_porch(ink, f, cam, "strip")
        if f < 99.8:
            draw_blood(ink, f, cam, "strip")
        a = anchors.get("mother")
        if a and T_HOWL + 0.3 < f < T_HOWL + 3.0:               # her muzzle comes up dripping
            porch.drips(ink, f, oy, a["muzzle"][0], a["muzzle"][1] + oy, f - T_HOWL - 0.35, wet=0.9, width=14, floor=400)

    def on_porch(ink, t, oy):
        draw_old_dog(ink, f, oy, "porch")

    def sill(ink, t, oy):
        props.pile(ink, f, 312, 392 - oy, 5, s=0.6, born=[62.2, 71.5, 75.5, 80.8, 80.9], edge=404 - oy, floor=400 - oy,
                   spread=pile_spread(f))
        draw_old_dog(ink, f, oy, "sill")
        if f < 99.8:
            draw_felt_porch(ink, f, cam, "sill")
            for nm in ("mid", "big", "small"):
                draw_retriever(ink, nm, f, cam, "sill")
            draw_herder_porch(ink, f, cam, "sill")
            draw_lead_porch(ink, f, oy)
            draw_terrier_porch(ink, f, cam, "sill")
            draw_digger_porch(ink, f, cam, "sill")
            draw_sheep(ink, f, cam, "sill")
        if 97.1 < f < 99.0:                                     # wet through: the old dog, and the calf at the edge
            porch.drips(ink, f, oy, OLD[0] + 20, OLD[1] - 30, f - 97.15, wet=1.0, width=70, floor=392)
            porch.drips(ink, f, oy, 650, 352, f - 97.2, wet=0.8, width=30, floor=388)

    def under(ink, t, oy):
        if in_town:
            town_set(ink, f, cam, sky=False)
            town_cast(ink, f, cam)
            _calf_from_below(ink, f, cam)
        else:
            for nm in PACK:                                     # the moment after the splash, before the crane
                _draw_swimmer(ink, nm, f, cam)
        if f < 101.2:
            for q, nm in enumerate(PACK):
                tg = t_go(nm) + LEAP
                porch.bubbles(ink, f, oy, lambda te, nm=nm: mouth_world(nm, te), tg, PLACE[nm][1] - 0.1, rate=7.0, seed=3 + q, size=0.9)
                porch.bubbles(ink, f, oy, (ENTRY[nm], 440), tg - 0.05, tg + 0.9, rate=15.0, seed=40 + q, size=1.1)
        if in_town:
            town.front(ink, f, cam)

    def front(ink, t, oy):
        for nm in PACK:
            tg = t_go(nm) + LEAP * 0.85
            if f >= tg - LEAP:
                _draw_air(ink, nm, f, cam)
            if tg <= f < tg + 1.2:
                porch.splash(ink, f, oy, ENTRY[nm], f - tg, 1.2 if nm in ("lead", "big", "sheep", "blood") else 0.9, "in", seed=PACK.index(nm))

    q = person_q(f)
    hold = None
    for tk in PEB_T:
        if tk - 0.5 <= f < tk:
            hold = "pebble"
    lean = _OVERRIDE.get("reeds", track("reeds")).x(f)
    door = 0.62 + 0.3 * ease(f, 91.0, 91.5)
    porch.scene(ink, f, oy, cast=dict(hill=hill, strip=strip, porch=on_porch, sill=sill, under=under, front=front),
                q=q, door=door, hold_a=hold, hand_over_rail=f >= 90.3, radio_on=1.0, pebbles=pebbles_at(f),
                rings=_rings(f), reed_lean=clamp(lean, 0.0, 1.3), moth_scatter=clamp(track("moths").x(f), 0.0, 1.0),
                puddles=[(350, 0.7), (405, 0.5)], dusk=0.4)


def _draw_air(ink, nm, f, cam):
    dv = dive(nm, f)
    if not dv or dv["phase"] != "air":
        return
    if nm == "lead":
        sx, sy = cam.xy(dv["x"], dv["y"])
        dog.draw_dog(ink, dog.swim_down(f * 1.2, steep=clamp(-dv["pitch"] + 0.2, 0.05, 0.9)), sx, sy, scale=DS * cam.zoom, facing=1, shadow=False)
    elif nm in ("big", "mid", "small"):
        draw_retriever(ink, nm, f, cam, "front")
    elif nm == "sheep":
        draw_sheep(ink, f, cam, "front")
    elif nm == "blood":
        draw_blood(ink, f, cam, "front")
    elif nm == "terrier":
        draw_terrier_porch(ink, f, cam, "front")
    elif nm == "digger":
        draw_digger_porch(ink, f, cam, "front")
    elif nm == "felt":
        draw_felt_porch(ink, f, cam, "front")
    elif nm == "herder":
        draw_herder_porch(ink, f, cam, "front")


def _draw_swimmer(ink, nm, f, cam):
    dv = dive(nm, f)
    if not dv or dv["phase"] != "swim":
        return
    {"lead": lambda: _lead_town(ink, f, cam), "big": lambda: _retriever_town(ink, "big", f, cam),
     "mid": lambda: _retriever_town(ink, "mid", f, cam), "small": lambda: _retriever_town(ink, "small", f, cam),
     "sheep": lambda: _sheep_town(ink, f, cam), "blood": lambda: _blood_town(ink, f, cam),
     "terrier": lambda: _terrier_town(ink, f, cam), "digger": lambda: _digger_town(ink, f, cam),
     "felt": lambda: _felt_town(ink, f, cam), "herder": lambda: _herder_town(ink, f, cam)}[nm]()


def _insert_frame(ink, f, cam):
    town_set(ink, f, cam, sky=True)
    town_cast(ink, f, cam)
    town.front(ink, f, cam)


def draw(t, ink):
    """One full 960x540 frame of S4 at local time t (0..32)."""
    t = clamp(t, 0.0, SECONDS)
    f = T0 + t
    shot = shot_at(min(f, T1 - 1e-6))
    kind = shot[3]
    if kind == "porch":
        _porch_frame(ink, f, 0)
        z = howl_push(f)
        if z > 1.001:
            porch.push(ink, 505.0, 352.0, z)
    elif kind == "crane":
        _porch_frame(ink, f, crane_oy(f))
    elif kind == "master":
        _porch_frame(ink, f, porch.F_TOWN)
        z = master_zoom(f)
        if z > 1.001:
            porch.push(ink, PUSH_C[0], PUSH_C[1], z)
    else:
        _insert_frame(ink, f, INSERT_CAM[shot[2]])


# ====================================================================== #
#  10 · THE SOUND (laid with sound.py; nobody here has heard it)         #
# ====================================================================== #

def _pan(wx):
    return clamp((wx - 480.0) / 480.0, -1, 1) * 0.8


def sound(mix, at=0.0):
    """S4's sound into `mix`, the sequence starting at mix second `at`. Every contact is timed to the frame
    it lands on in THIS picture (the board's rule: the builder's frame wins and the sound moves)."""
    S = snd

    def A(f):
        return at + (f - T0)

    # rooms: above until the line passes the camera, then below
    S.above(mix, A(T0) - 0.1, T_LINE - T0 + 0.2, 1.0, 0.2, 0.2)
    S.hush(mix, A(T_LINE) - 0.1, T1 - T_LINE + 0.2, 1.0, 0.2, 0.2)
    S.crickets(mix, A(T0), 1.8, 3, gain=0.018, stop=[A(84.4), A(85.0), A(85.6)], fade_in=0.05)
    S.crickets(mix, A(88.9), 8.6, 1, gain=0.018)
    S.music_s4(mix, at)                                       # nothing above the water; the round from +17
    # the tired dog; the mother still drinking; it turns to the water
    S.drinking(mix, A(84.0), 2.2, pan=0.2)
    S.drip(mix, A(84.2), 3, 0.5)
    S.paws(mix, A(85.6), 2, 0.2, gain=0.09, pan=0.0, pan_to=0.05)
    S.howl(mix, A(T_HOWL + 0.3), 2.0, tail=0.45)              # the muzzle is up from +0.3; room gone by 88.75
    for hit in _cows()["wl"].bell_hits:                       # her head coming up: the bell is the herd's own pendulum
        if T0 < hit < T_LINE:
            S.cowbell(mix, A(hit), gain=0.045, pan=0.5)
    S.drip(mix, A(T_HOWL + 0.5), 4, 0.4, pan=0.2, on="water")  # the mother's muzzle
    # arrivals, each its own material, from every side
    S.paper_slide(mix, A(89.2), pan=-0.75)
    S.paws(mix, A(90.0), 5, 0.24, gain=0.07, pan=-0.7, pan_to=-0.35)
    S.flutter(mix, A(89.9), pan=0.8)
    S.paws(mix, A(90.7), 2, 0.12, gain=0.07, pan=0.6)         # it lands on its feet
    S.wheels(mix, A(90.3), 1.3, 1.0, pan=-0.9, pan_to=-0.45)
    S.wheels(mix, A(90.48), 1.25, 1.26, pan=-0.9, pan_to=-0.5)
    S.wheels(mix, A(90.62), 1.3, 1.5, pan=-0.9, pan_to=-0.3)
    S.nose_bump(mix, A(T_BUMP), gain=0.07, pan=-0.3)          # small wheels against a hoof
    S.wheels(mix, A(T_BUMP + 0.05), 0.4, 1.5, gain=0.04, pan=-0.3)
    S.wire_twang(mix, A(91.05), pan=0.45)
    S.page_peel(mix, A(T_PEEL), pan=0.75)
    S.pop(mix, A(92.2 + 0.3), pan=0.3)
    S.creak(mix, A(91.05), 0.5)                                # the door
    S.old_dog_down(mix, A(91.95), 4, gain=0.1, pan=snd.P_DOOR + 0.1)
    for k, tk in enumerate(PEB_T):
        S.pebble(mix, A(tk))
    # the herder opens the way
    S.patter(mix, A(SWING[0][0]), 1.6, pan=-0.3, pan_to=0.5)
    S.hooves(mix, A(T_TURN + 0.1), 5, 0.55, "grass", gain=0.1, pan=-0.2, pan_to=0.1)
    S.hooves(mix, A(T_MOTHER + 0.2), 5, 0.5, "wood", gain=0.09, pan=0.1, pan_to=0.4)
    S.calf(mix, A(T_MOTHER + 0.3), 9, 0.15, pan=0.0, pan_to=0.4)
    S.hooves(mix, A(T_TURN + 0.5), 4, 0.55, "earth", gain=0.06, pan=0.0)
    S.card_drag(mix, A(93.1), 0.5, pan=-0.15)                 # the pile shouldered along the board
    # ten dogs in the same four frames
    for nm in PACK:
        S.plunge(mix, A(t_go(nm) + LEAP * 0.85), 0.6 if nm in ("small", "terrier", "felt") else 0.9, gain=0.1, pan=_pan(ENTRY[nm]))
    S.drip(mix, A(97.5), 2, 0.3, pan=-0.1)                    # on the old dog
    S.drip(mix, A(97.6), 2, 0.3, pan=0.4)                     # on the calf
    for k, nm in enumerate(PACK):
        S.bubbles(mix, A(T_LINE + 0.1 + 0.05 * k), 3, 1.6, gain=0.03, pan=_pan(ENTRY[nm]))
    # down on the bed
    for nm in PACK:
        (px, py), ta = PLACE[nm]
        S.land(mix, A(ta), gain=0.06, pan=_pan(px))
    S.work(mix, A(T_WORK), T1 - T_WORK + 0.2, voices=7)
    for s in lead_agenda().all("dig") + digger_agenda().all("dig") + terrier_agenda().all("dig"):
        if s.a < T1:
            S.dig(mix, A(s.a), s.b - s.a, find="ring" if s.kw.get("find") else None, gain=0.07, pan=_pan(s.p0[0]))
    w = works()
    for (tl, idx, by) in w.landings:
        if tl < T1:
            S.set_down(mix, A(tl), gain=0.07, pan=_pan(XC0 - 90))
            if by != "blood":
                S.peg_tick(mix, A(tl + SHELL_DELAY), 1, gain=0.05, pan=_pan(XC0))      # a shell sent along the row
    for (tn, d) in w.nudges:
        S.nose_bump(mix, A(tn), gain=0.06, pan=_pan(XC0 - 100))
    for nm, pitch in (("big", 1.0), ("mid", 1.26), ("small", 1.5)):
        prev = None
        for i in range(0, w.n, 12):
            x, y, ph, tau, fac = w.log_r[nm][i]
            f = T_WORK + i * WDT
            if ph in ("carry", "back") and prev not in ("carry", "back") and f < T1 - 0.3:
                S.wheels(mix, A(f), 1.0, pitch, gain=0.04, pan=_pan(x), under=True)
            prev = ph
    S.fish_murmur(mix, A(99.3), 1.6, gain=0.03, pan=0.3)
    S.fish_murmur(mix, A(103.0), 2.0, gain=0.02, pan=0.3)
    S.bubbles(mix, A(105.0), 4, 0.6, gain=0.04, pan=0.4)      # the calf's nose in the water, at the very edge
    td = terrier_agenda().find("down")
    S.pop(mix, A(td.a + 0.5), pan=_pan(188))
    S.sniff(mix, A(blood_plan()["t_take"] - 1.2), 3, gain=0.05, pan=0.1, under=1500)
    S.bubble_picture(mix, A(T_BUBBLE), 2.0, gain=0.045, pan=0.3)
    S.fish_murmur(mix, A(111.0), 1.5, gain=0.02, pan=0.3)
    return mix


# ====================================================================== #
#  11 · CHECKS (MEASURED when this runs)                                 #
# ====================================================================== #

HOLDS = [   # film a, b, what must be still, which tracks must have run down
    (88.75, 89.0, "after the howl: only the dog's head coming down", ("reeds",)),
    (94.62, 95.0, "the herder's eye on the fourth cow", ("reeds", "peel", "felt_ear")),
]


def check(verbose=True):
    out = {}
    tr = _tracks()
    # 1 momentum response begins after the primary motion (never before it)
    for name, tk in tr.items():
        src, mv = tk.first_source(), tk.first_move()
        assert src is not None and mv is not None, name
        assert mv >= src - 1.0 / 96, (name, src, mv)
        out[f"lag_{name}"] = round(mv - src, 3)
    # 2 all energy decays when the sources stop
    for name, tk in tr.items():
        last = max(f for f in np.arange(T0 - 1, T1 + 0.9, 1 / 96) if tk.source_on(f))
        peak = max(tk.energy(f) for f in np.arange(T0 - 1, T1 + 0.9, 1 / 48)) or 1.0
        z = zeta(tk.material)
        w0 = math.sqrt(tk.k / tk.m)
        settle = 4.6 / (z * w0) + 0.3                         # 1 % envelope
        if last + settle < T1 + 0.9:
            e = tk.energy(last + settle)
            assert e < 0.02 * peak, (name, e, peak)
            out[f"decay_{name}"] = round(e / peak, 5)
    for a, b, what, names in HOLDS:
        for name in names:
            tk = tr[name]
            peak = max(abs(tk.v(f)) for f in np.arange(T0 - 1, T1, 1 / 48)) or 1.0
            v = max(abs(tk.v(f)) for f in np.arange(a, b, 1 / 48))
            assert v < 0.08 * peak, (what, name, v, peak)
    # 3 the integrator agrees with itself at twice the rate
    a = Track("reeds", "foliage", drive=_reed_force, lo=-0.3, hi=1.6)
    b = Track("reeds", "foliage", drive=_reed_force, lo=-0.3, hi=1.6, sub=SUB * 2)
    err = max(abs(a.x(f) - b.x(f)) for f in np.arange(85.5, 90.0, 1 / 24))
    assert err < 0.02, err
    out["integrator_err"] = round(err, 5)
    assert a.x(T_HOWL + 0.2) < 0.01 and max(a.x(f) for f in np.arange(86, 88, 1 / 24)) > 1.02      # it overshoots: foliage
    # 4 the strip: no interpenetration, the stake holds, pieces never lost
    w = works()
    worst = 0.0
    for i in range(0, w.n, 3):
        xs = sorted(x for (x, th, on, pend) in w.log_p[i] if on)
        if xs:
            assert xs[0] >= -1e-6
            for p, q in zip(xs, xs[1:]):
                worst = min(worst, q - p - PW)
    assert worst > -1e-6, worst
    out["strip_overlap_px"] = round(-worst, 6)
    out["landings"] = [(round(t, 2), by) for t, i, by in w.landings]
    out["nudges"] = [(round(t, 2), round(d, 1)) for t, d in w.nudges]
    out["pieces_at_116"] = w.count(T1)
    assert w.count(T1) == 8, w.count(T1)
    out["retrievers_at_116"] = {k: w.retriever(k, T1)[2] for k in ("big", "mid", "small")}
    out["max_gap_seen"] = round(max(max(w.gaps(f) or [0]) for f in np.arange(T_WORK, T1, 0.1)), 1)
    out["sheep_at_116"] = (round(w.sheep(T1)[0]), w.sheep(T1)[2])
    out["row_at_116_x"] = [round(piece_x(s_)) for _, s_, _ in sorted(w.pieces_at(T1), key=lambda q: q[1])]
    # 5 the board's counts
    assert len(PACK) == 10 and len(set(ENTRY.values())) == 10
    goes = [t_go(n) for n in PACK]
    assert max(goes) - min(goes) <= 3.0 / FPS + 1e-9          # the same four frames
    out["dive_frames"] = sorted(set(int(round((g - T_GO) * FPS)) for g in goes))
    ht = hole_times()
    assert sorted(ht) == list(range(8, 40)), sorted(ht)
    assert holes_dug(T1) == 40
    out["holes_at_116"] = holes_dug(T1)
    assert len(pebbles_at(T_GO)) == 12 and len(pebbles_at(T0)) == 5
    # 6 single file / fan
    xs = sorted(ENTRY.values())
    out["splash_span_px"] = xs[-1] - xs[0]
    # 7 no cow below the line: every cow anchor on the strip is on the bank
    im = Image.new("RGB", (W, H))
    for f in (84.0, 90.0, 96.0, 99.0, 105.0, 115.9):
        an = draw_strip_cows(kit.Ink(0, 0), f, 0)
        for who, a in an.items():
            if a:
                for leg, (hx, hy) in a["hooves"].items():
                    assert hy <= 400.5, (who, f, leg, hy)
    out["materials_zeta"] = {k: (round(zeta(k), 2) if MATERIALS[k][1] else None) for k in MATERIALS}
    if verbose:
        for k, v in out.items():
            print(f"  {k}: {v}")
    return out


# ====================================================================== #
#  12 · ALONE                                                            #
# ====================================================================== #

def end_state():
    """Where everything is at film second 116.0, for whoever builds on from here (world coordinates)."""
    w = works()

    def ag(a):
        seg, tau, u, x, y = a.at(T1)
        return dict(x=round(x, 1), y=round(y, 1), doing=seg.kind, facing=seg.facing)
    return dict(
        framing="F-TOWN (oy 360), zoom 1.0",
        lead=ag(lead_agenda()), digger=ag(digger_agenda()), terrier=ag(terrier_agenda()), herder=dict(ag(herder_agenda()), pages=herder_pages(T1)),
        bloodhound=dict(ag(blood_agenda()), trail=blood_plan()["trail2"]),
        retrievers={k: dict(x=round(w.retriever(k, T1)[0], 1), y=round(w.retriever(k, T1)[1], 1), doing=w.retriever(k, T1)[2]) for k in ("big", "mid", "small")},
        sheepdog=dict(x=round(w.sheep(T1)[0], 1), y=round(w.sheep(T1)[1], 1), doing=w.sheep(T1)[2]),
        felt_dog=dict(x=FELT_AT[0], y=FELT_AT[1], doing="flat at the row's end"),
        row=dict(y=LINE_Y, piece_scale=PS, xs=[round(piece_x(s_), 1) for _, s_, _ in sorted(w.pieces_at(T1), key=lambda q: q[1])],
                 shells=[(round(x, 1), y) for x, y, mv in shells_at(T1)]),
        holes=list(range(8)) + sorted(q for q, (a, b) in hole_times().items() if T1 >= b),
        making_place=dict(progress=1.0, posts=[(s_.p0[0] + 30, s_.p0[1]) for s_ in digger_agenda().all("build")], pages_laid=pages_laid(T1)),
        stock={k: (STOCK[k][0], STOCK[k][1], w.stock(k, T1)) for k in STOCK},
        pebbles=pebbles_at(T1), old_dog=OLD, pile_spread=pile_spread(T1),
        cows=dict(lead=(LEAD_X, "meadow, looking down into the water"), second=SECOND_X, calf=(664.0, "muzzle on the line at x 660"),
                  mother=740.0, fourth=round(_cows()["w4"].state(T1)["x"]), fifth=round(_cows()["w5"].state(T1)["x"]),
                  sixth=round(_cows()["w6"].state(T1)["x"])),
    )


class _Kinematic:
    """The no-secondary-motion alternative: the reeds copy the howl exactly, with no mass at all."""

    def x(self, f):
        return howl_env(f)


def proof(path):
    """The SCION's proof view: the same frames under four damping presets, side by side (a diagnostic, not film)."""
    presets = [("none", None), ("under", 2.2), ("built", MATERIALS["foliage"][2]), ("over", 60.0)]
    times = [86.45, 86.9, 87.5, 88.05, 88.3, 88.6, 88.9]
    cw, ch = 300, 150
    sh = Image.new("RGB", (cw * len(times), ch * len(presets)), (20, 20, 24))
    keep = MATERIALS["foliage"]
    for r, (name, c) in enumerate(presets):
        if c is None:
            _OVERRIDE["reeds"] = _Kinematic()
        else:
            MATERIALS["foliage"] = (keep[0], keep[1], c, keep[3])
            _OVERRIDE["reeds"] = Track("reeds", "foliage", drive=_reed_force, lo=-0.3, hi=1.6)
        for k, f in enumerate(times):
            ink = kit.Ink(f - T0, int(round((f - T0) * FPS)))
            ink.paper()
            _porch_frame(ink, f, 0)
            sh.paste(ink.finish().crop((600, 270, 900, 420)), (k * cw, r * ch))
    MATERIALS["foliage"] = keep
    _OVERRIDE.clear()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sh.save(path)
    return path


def still(f):
    ink = kit.Ink(f - T0, int(round((f - T0) * FPS)))
    ink.paper()
    draw(f - T0, ink)
    return ink.finish()


def sheet(times, path, cols=4, scale=0.5, crop=None):
    ims = []
    for f in times:
        im = still(f)
        if crop:
            im = im.crop(crop)
        ims.append(im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS))
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * w, rows * h), (20, 20, 24))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols) * w, (i // cols) * h))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sh.save(path)
    return path


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check()
        return
    if args and args[0] == "--proof":
        print(proof(args[1]))
        return
    if args and args[0] == "--state":
        import pprint
        pprint.pprint(end_state(), width=150)
        return
    if args and args[0] == "--stills":
        out = _HERE.parent.parent / "stills" / "dogs-s4"
        out.mkdir(parents=True, exist_ok=True)
        for a in args[1:]:
            f = float(a)
            still(f).save(out / f"{f:07.2f}.png")
        print("stills ->", out)
        return
    if args and args[0] == "--sheet":
        out = Path(args[1])
        cols = int(args[2])
        scale = float(args[3])
        print(sheet([float(a) for a in args[4:]], out, cols, scale))
        return
    check(verbose=False)
    film = kit.Film("dogs-s4", seconds=SECONDS)
    film.picture(draw)
    film.sound(lambda mix: sound(mix, 0.0))
    film.poster_at = 12.9
    film.render()


if __name__ == "__main__":
    main()
