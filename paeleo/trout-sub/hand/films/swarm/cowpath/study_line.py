"""STUDY (SCION law 3, animation-07 hard proof): the graft, in ONE continuous pencil line.

A shoot at the top of a twig leans toward an old stump. The line pinches shut under it (the cut), the twig
springs back, the shoot drops, the ground line swells into a wave and carries it to the stump, the wave
breaks up the bark and the shoot rides it to the rim, teeters, tips over, sticks in the cleft, is let in,
is bound by three turns that the stump's own contour throws round itself, waits, and bursts into seven leaves.
There is never a second stroke: every frame is one open polyline of the same number of points, running from
the left edge of the paper to the right. Nothing dissolves; every change is the line moving.

    python3 films/swarm/cowpath/study_line.py                 -> assets/films/cowpath-study-line.mp4
    python3 films/swarm/cowpath/study_line.py --check         -> the measured invariants and topology warnings
    python3 films/swarm/cowpath/study_line.py --sheet OUT.png [t ...]     -> contact sheet (16 stills by default)
    python3 films/swarm/cowpath/study_line.py --still OUT.png t [zoom]    -> one frame, optionally enlarged
    python3 films/swarm/cowpath/study_line.py --keys OUT.png  -> the key drawing set, one key per cell

The native primitives of animation-07 (Foldes, drawn metamorphosis) are kept as data, by name:
    KeyContour            a key drawing: one polyline cut into named runs with fixed point counts
    Correspondence        the point-for-point pairing of two keys (run by run), checkable
    InBetweenField        per-point progress: which group a point belongs to, what it is anchored to
    Pacing                transformation pacing: a hand-keyed track with an easing on every key
    DiscontinuityMarker   a moment when the line's meaning changes (the cut, a corner, the seat, the heal)
    InterventionFrame     a hand-authored exception that overrides the plain in-between where it looks bad
Coordinates: "stump units" (the stump of sets.STUMP_PROFILE is 46 wide, 22 high), origin on the ground under
the middle of the stump, y down. Screen = origin + s * unit; the study uses s = 6.4 px and
flips x (MIRROR), because in this film everything that is wanted lies to the right. Time base: seconds, 24 fps.
Importing this module renders nothing.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
for _p in (str(FILMS), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import kit
from kit import Film, clamp, lerp, smooth

W, H = kit.W, kit.H
FPS = kit.FPS
SLUG = 'cowpath-study-line'
SECONDS = 12.0
ORIGIN = (742.0, 468.0)     # screen position of the ground under the middle of the stump
SCALE = 6.4                 # px per stump unit
MIRROR = True               # the key drawings have the twig on the right; the film travels left to right, so they are flipped
GRAPHITE = (62, 60, 62)

# The stump is the film's stump (act 1 fells the tree, act 2 draws what is left). Same numbers as
# sets.STUMP_PROFILE; copied so that this study does not import a file another agent is still writing.
STUMP_PROFILE = [(-20, 0), (-16.5, -1.6), (-13.4, -5.5), (-11.8, -11), (-11.2, -17), (-11, -22),
                 (11, -22), (11.3, -17), (12, -11), (14, -5.5), (18.5, -1.8), (26, 0)]
RIM = -22.0                 # y of the flat cut
CLEFT_DEPTH = 6.5
WEDGE_H = 4.5               # the scion's wedge: 4.5 units long, 1 unit half-width at its shoulder
TWIG_X = 80.0
TWIG_H = 30.0
BAND_Y = (-13.6, -16.4, -19.2)      # the three turns of the binding, bottom to top


# ================================================================ primitives ===

def resample(pts, n):
    """n points evenly spaced along a polyline (a run of zero length gives n copies of its point)."""
    p = np.asarray(pts, float)
    if len(p) == 1:
        return np.repeat(p, n, 0)
    d = np.hypot(*np.diff(p, axis=0).T)
    c = np.concatenate([[0.0], np.cumsum(d)])
    if c[-1] < 1e-9:
        return np.repeat(p[:1], n, 0)
    u = np.linspace(0, c[-1], n)
    return np.stack([np.interp(u, c, p[:, 0]), np.interp(u, c, p[:, 1])], 1)


@dataclass
class KeyContour:
    """A key drawing. `pts` is ONE polyline; `runs` names its stretches: run -> (first index, one past last).
    Two keys with the same schema (same runs, same counts) are in point correspondence by construction."""
    name: str
    pts: np.ndarray
    runs: dict

    @classmethod
    def from_runs(cls, name, schema, lines):
        """schema = [(run, n), ...] in drawing order; lines = {run: polyline}. Each run is resampled to n."""
        out, runs, i = [], {}, 0
        for run, n in schema:
            out.append(resample(lines[run], n))
            runs[run] = (i, i + n)
            i += n
        return cls(name, np.concatenate(out), runs)

    def run(self, name):
        a, b = self.runs[name]
        return self.pts[a:b]

    def schema(self):
        return [(r, b - a) for r, (a, b) in self.runs.items()]


@dataclass
class Correspondence:
    """Point i of key `a` becomes point `index[i]` of key `b`. Built run by run from the landmarks the two keys
    share; `check()` returns the measured facts a critic can ask for (never a judgement)."""
    a: KeyContour
    b: KeyContour
    index: np.ndarray

    def check(self):
        d = np.hypot(*(self.b.pts[self.index] - self.a.pts).T)
        return dict(pair=f'{self.a.name}->{self.b.name}', points=len(self.index),
                    order_kept=bool(np.all(np.diff(self.index) > 0)), moved=int((d > 1e-6).sum()),
                    max_travel=float(d.max()), mean_travel=float(d.mean()))


def correspond(a, b):
    """The correspondence of two keys that share a schema. Raises if a landmark run is missing or miscounted."""
    if a.schema() != b.schema():
        raise ValueError(f'{a.name} and {b.name} do not share a schema: no point correspondence')
    return Correspondence(a, b, np.arange(len(a.pts)))


def pair_by_landmarks(line_a, line_b, marks_a, marks_b, counts):
    """Put two unrelated polylines into point correspondence. marks_* are the vertex indices of the landmarks
    that mean the same thing in both (first and last vertex included); counts = points to give each stretch.
    Returns (A, B) arrays of equal length. Use it to pair, say, the paved path with the first pencil line."""
    if len(marks_a) != len(marks_b) or len(counts) != len(marks_a) - 1:
        raise ValueError('landmarks must pair one to one')
    A, B = [], []
    for k, n in enumerate(counts):
        A.append(resample(line_a[marks_a[k]:marks_a[k + 1] + 1], n))
        B.append(resample(line_b[marks_b[k]:marks_b[k + 1] + 1], n))
    return np.concatenate(A), np.concatenate(B)


@dataclass
class InBetweenField:
    """Who moves when. group[i] = which part point i belongs to (0 = the carrier, e.g. a stem); anchor[i] = the
    index of the point it rides on (-1 = none). A part's own shape is in-betweened relative to its anchor with
    its own progress, while the anchor is carried by group 0: a leaf can open late on a stem that is growing."""
    group: np.ndarray
    anchor: np.ndarray

    def between(self, A, B, progress):
        """A, B: (N,2) keys. progress: {group: e}; e may run past 1 (overshoot) or be absent (= group 0's)."""
        e0 = progress.get(0, 0.0)
        out = A + (B - A) * e0
        for g in np.unique(self.group):
            if g == 0:
                continue
            m = self.group == g
            e = progress.get(int(g), e0)
            anc = self.anchor[m]
            if np.all(anc < 0):
                out[m] = A[m] + (B[m] - A[m]) * e
            else:
                ra, rb = A[m] - A[anc], B[m] - B[anc]
                out[m] = out[anc] + ra + (rb - ra) * e
        return out


EASES = {
    'lin': lambda u: u,
    'smooth': smooth,
    'in': lambda u: u * u,
    'out': lambda u: 1 - (1 - u) ** 2,
    'hold': lambda u: 0.0 if u < 1 else 1.0,
    'over': lambda u: 1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2,      # runs about 9% past, comes back
}


@dataclass
class Pacing:
    """Transformation pacing: a hand-keyed track. keys = [(t, value)] or [(t, value, ease)]; the ease belongs
    to the arrival at that key. `at(t)` holds before the first key and after the last."""
    name: str
    keys: list

    def at(self, t):
        k = self.keys
        if t <= k[0][0]:
            return k[0][1]
        for a, b in zip(k, k[1:]):
            if t <= b[0]:
                u = (t - a[0]) / max(1e-9, b[0] - a[0])
                return a[1] + (b[1] - a[1]) * EASES[b[2] if len(b) > 2 else 'smooth'](clamp(u))
        return k[-1][1]


@dataclass(frozen=True)
class DiscontinuityMarker:
    """A planned moment at which the line's reading changes. Fast travel is allowed inside [t0, t1] and
    nowhere else: --check holds every other frame to the quiet limit."""
    name: str
    t0: float
    t1: float
    what: str


@dataclass(frozen=True)
class InterventionFrame:
    """A hand-authored exception: between t0 and t1 the named thing is NOT the plain in-between of two keys.
    `why` records the bad interpolation it replaces. The code that applies it is the function named in `by`."""
    name: str
    t0: float
    t1: float
    why: str
    by: str


# ================================================================== timing =====
# One table of event times (seconds). Picture, sound and --check all read it.

T = dict(
    lean=0.35, strain=0.95, pinch=1.50, cut=1.64, free=1.70, land=2.06, rest=2.46,
    crash=4.30, corner=4.96, slip=5.13, over=5.36, edge=5.72, stuck=5.84,
    drop=6.32, seat=6.44, grip=6.58,
    band=((6.92, 7.22), (7.28, 7.58), (7.64, 7.92)), tight=(7.98, 8.16),
    wait=(8.16, 9.20), bud=9.20, heal=(9.5, 11.1), end=SECONDS,
)
PUSH = (5.90, 6.06, 6.22)        # three pushes at the mouth of the cleft; it opens a step at each
# leaf k (1..7, bottom left = 1, then alternating, 7 = the tip) starts to open at LEAF_AT[k]: upper bud first
LEAF_AT = {4: 9.20, 3: 9.62, 2: 9.96, 1: 10.20, 5: 10.40, 6: 10.56, 7: 10.70}
LEAF_SPEAR, LEAF_PAUSE, LEAF_OPEN = 0.25, 0.08, 0.34

MARKERS = [
    DiscontinuityMarker('cut', T['pinch'], T['free'] + 0.06, 'the contour pinches shut under the shoot; the twig is now a stub'),
    DiscontinuityMarker('land', T['land'] - 0.05, T['land'] + 0.12, 'the wedge point leaves the stub and meets the ground'),
    DiscontinuityMarker('crash', T['crash'] - 0.05, T['crash'] + 0.12, 'the wave breaks on the root; the ride turns upward'),
    DiscontinuityMarker('corner', T['slip'], T['over'] + 0.05, 'the point passes the corner of the rim'),
    DiscontinuityMarker('seat', T['stuck'], T['grip'], 'three pushes open the cleft; the wedge goes home and the cleft closes on it'),
    DiscontinuityMarker('band 1', *T['band'][0], 'a loop of the stump contour is thrown round the union'),
    DiscontinuityMarker('band 2', *T['band'][1], 'second turn'),
    DiscontinuityMarker('band 3', *T['band'][2], 'third turn'),
    DiscontinuityMarker('heal', *T['heal'], 'the split closes: cleft and wedge stop being two things'),
]

INTERVENTIONS = [
    InterventionFrame('pinch key', T['pinch'], T['free'], 'whole twig -> stub in-betweened directly is a dissolve of the join; '
                      'an extra key pinches the contour shut first, held 1 frame', 'BASE_TRACK (key PINCH)'),
    InterventionFrame('twig spring', T['cut'], 3.4, 'a keyed stub would just stand; the release is a damped spring', 'twig_bend'),
    InterventionFrame('ground wave', T['land'], T['crash'] + 0.25, 'the carrier is a travelling displacement of the ground run, '
                      'not a key: a key pair would raise and lower the whole ground at once', 'ground_wave'),
    InterventionFrame('bark bulge', T['crash'] - 0.1, T['over'], 'the wave continues up the stump side as a travelling bulge', 'bark_bulge'),
    InterventionFrame('band draw-on', T['band'][0][0], T['band'][2][1], 'collapsed loop -> full loop in-betweened point for point '
                      'inflates like a balloon; instead each loop is paid out along its own path', 'draw_on'),
    InterventionFrame('stuck', T['stuck'], T['drop'], 'hand-keyed pushes (squash) and rocking at the mouth of a cleft that is too tight; '
                      'three extra keys OPEN1, OPEN2, OPEN let it give a step per push', 'POSE tracks, BASE_TRACK'),
    InterventionFrame('wilt', T['wait'][0], 9.9, 'the wait is acted by a hand-keyed sag of the shoot, then a recovery past straight', 'POSE tracks'),
]


# ============================================================ key drawings =====

BASE_SCHEMA = [('ground_L', 16), ('stump_L0', 24), ('band1', 30), ('stump_L1', 4), ('band2', 30), ('stump_L2', 4),
               ('band3', 30), ('stump_L3', 4), ('top_L', 12), ('cleft_L', 8), ('cleft_R', 8), ('top_R', 12),
               ('stump_R', 44), ('ground_M', 60), ('twig_L', 30), ('twig_R', 44), ('ground_R', 12)]
BAND_RUNS = ('band1', 'band2', 'band3')


def _side_x(y, right):
    """x of the stump's left or right contour at height y (y <= 0)."""
    pr = STUMP_PROFILE[6:] if right else STUMP_PROFILE[:6][::-1]
    ys = [p[1] for p in pr]
    xs = [p[0] for p in pr]
    return float(np.interp(y, ys, xs))


def _cut_at(poly, y):
    """Split a polyline that climbs (y decreasing) at height y: (below, above), both including the cut point."""
    out = [poly[0]]
    for a, b in zip(poly, poly[1:]):
        if a[1] >= y > b[1]:
            f = (a[1] - y) / (a[1] - b[1])
            c = (a[0] + (b[0] - a[0]) * f, y)
            return out + [c], [c] + poly[poly.index(b):]
        out.append(b)
    return out, [poly[-1]]


def _band(y, on):
    """One turn of the binding as a run: leaves the left contour, crosses the front, comes back round behind."""
    xl, xr = _side_x(y, False) - 0.7, _side_x(y, True) + 0.7
    if not on:
        return [(xl + 0.7, y)]
    cx, rx, ry = (xl + xr) / 2, (xr - xl) / 2, 0.85
    pts = [(xl + 0.7, y)]
    for k in range(41):
        a = math.pi - 2 * math.pi * k / 40           # front first (sin > 0 is down = near)
        pts.append((cx + rx * math.cos(a), y + ry * math.sin(a) + 0.5 * math.sin(a / 2) ** 2 * 0))
    pts.append((xl + 0.7, y))
    return pts


def base_key(name, top='open', hw=1.6, dp=CLEFT_DEPTH, bands=False, squeeze=0.0, split=0.0):
    """A key drawing of everything but the shoot: ground, old stump with its cleft, ground, twig, ground.

    top     'open' (the shoot continues the twig), 'pinch' (the contour shut under it), 'stub' (a slanted cut)
    hw, dp  half-width of the cleft at the rim, and its depth
    bands   the three turns of binding are in the drawing
    squeeze the bound stump top drawn in by the binding (0..1)
    split   half-distance between the two points at the bottom of the cleft: 0 = a split, 1 = healed over"""
    L = {}
    L['ground_L'] = [(-74, 0.9), (-52, 0.2), (-38, 0.9), (-33, 0.5), (-30, -1.0), (-26.5, 0.3), (-23.5, -0.7), (-20, 0)]   # a root shows
    left = list(STUMP_PROFILE[:3]) + [(-16.6, -8.2), (-17.4, -10.4), (-15.3, -10.6), (-12.2, -9.6)] + list(STUMP_PROFILE[3:6])   # a broken limb
    p0, rest = _cut_at(left, BAND_Y[0])
    p1, rest = _cut_at(rest, BAND_Y[1])
    p2, p3 = _cut_at(rest, BAND_Y[2])
    L['stump_L0'], L['stump_L1'], L['stump_L2'], L['stump_L3'] = p0, p1, p2, p3
    for k, r in enumerate(BAND_RUNS):
        L[r] = _band(BAND_Y[k], bands)
    L['top_L'] = [(-11, RIM), (-7.5, RIM - 0.7), (-4, RIM + 0.1), (-hw, RIM)]
    L['cleft_L'] = [(-hw, RIM), (-split, RIM + dp)]
    L['cleft_R'] = [(split, RIM + dp), (hw, RIM)]
    L['top_R'] = [(hw, RIM), (5.0, RIM + 0.45), (8.5, RIM - 0.25), (11, RIM)]
    L['stump_R'] = list(STUMP_PROFILE[6:])
    L['ground_M'] = [(26, 0), (29.5, -0.8), (32.5, 0.4), (35.5, -0.5), (40, 0.6), (56, 0.2), (70, 0.6), (TWIG_X - 1.3, 0)]
    tl, tr = {'open': ((-1.0, -TWIG_H), (1.0, -TWIG_H)), 'pinch': ((0.0, -TWIG_H - 0.3), (0.0, -TWIG_H - 0.3)),
              'stub': ((-1.0, -TWIG_H - 0.5), (1.0, -TWIG_H + 1.0))}[top]
    cx = lambda h: TWIG_X + 0.9 * math.sin(h / TWIG_H * 2.6)          # the twig is not ruled
    L['twig_L'] = [(cx(h) - lerp(1.3, 1.0, h / TWIG_H), -h) for h in np.linspace(0, TWIG_H - 2, 8)] + [(cx(TWIG_H) + tl[0], tl[1])]
    down = [(cx(h) + lerp(1.3, 1.0, h / TWIG_H), -h) for h in np.linspace(TWIG_H - 2, 0, 12)]
    spur = [(cx(15) + 1.15, -15.0), (cx(15) + 4.2, -19.5), (cx(15) + 5.4, -22.6), (cx(15) + 4.9, -19.2), (cx(15) + 1.2, -13.4)]
    L['twig_R'] = [(cx(TWIG_H) + tr[0], tr[1])] + [p for p in down if -p[1] > 15.2] + spur + [p for p in down if -p[1] < 13.2]
    L['ground_R'] = [(TWIG_X + 1.3, 0), (100, 0.6), (122, 0.1), (140, 0.8)]
    key = KeyContour.from_runs(name, BASE_SCHEMA, L)
    if squeeze:
        a, b = key.runs['stump_L0'][0], key.runs['stump_R'][1]
        p = key.pts[a:b]
        f = np.array([smooth((-11.5 - y) / 5.0) for y in p[:, 1]])
        p[:, 0] *= 1 - 0.07 * squeeze * f
    return key


BASE_KEYS = dict(
    WHOLE=base_key('WHOLE', 'open', hw=0.7),
    PINCH=base_key('PINCH', 'pinch', hw=0.7),
    STUB=base_key('STUB', 'stub', hw=0.7),
    OPEN1=base_key('OPEN1', 'stub', hw=1.4),                           # the old wood gives, a push at a time
    OPEN2=base_key('OPEN2', 'stub', hw=2.2),
    OPEN=base_key('OPEN', 'stub', hw=3.0),
    GRIP=base_key('GRIP', 'stub', hw=CLEFT_DEPTH / WEDGE_H),          # the cleft walls lie on the wedge
    BOUND=base_key('BOUND', 'stub', hw=CLEFT_DEPTH / WEDGE_H, bands=True),
    TIGHT=base_key('TIGHT', 'stub', hw=CLEFT_DEPTH / WEDGE_H, bands=True, squeeze=1.0),
    HEALED=base_key('HEALED', 'stub', hw=1.0, dp=0.0, bands=True, squeeze=1.0, split=1.0),
)
BASE_TRACK = [  # (t, key, ease into it): the registered morph sequence of the base
    (0.0, 'WHOLE'), (T['pinch'], 'WHOLE'), (T['cut'] - 0.04, 'PINCH', 'in'), (T['cut'], 'PINCH'), (T['free'] + 0.04, 'STUB', 'out'),
    (PUSH[0], 'STUB'), (PUSH[0] + 0.07, 'OPEN1', 'out'), (PUSH[1], 'OPEN1'), (PUSH[1] + 0.07, 'OPEN2', 'out'),
    (PUSH[2], 'OPEN2'), (PUSH[2] + 0.07, 'OPEN', 'out'), (T['seat'], 'OPEN'), (T['grip'], 'GRIP', 'in'),
    (T['band'][0][0], 'GRIP'), (T['band'][0][0] + 0.01, 'BOUND', 'hold'), (T['tight'][0], 'BOUND'), (T['tight'][1], 'TIGHT', 'out'),
    (T['heal'][0], 'TIGHT'), (T['heal'][1], 'HEALED', 'smooth'),
]

# ---- the shoot (the scion): one closed-looking stretch of the same line, in its own coordinates.
# Origin = the wedge point, which never changes shape once cut. Up is -y.

SHOOT_SCHEMA = [('wedgeL', 6), ('stemL0', 6), ('leaf1', 49), ('stemL1', 6), ('leaf3', 49), ('stemL2', 6), ('leaf5', 49),
                ('stemL3', 6), ('leaf7', 49), ('stemR3', 4), ('leaf6', 49), ('stemR2', 6), ('leaf4', 49), ('stemR1', 6),
                ('leaf2', 49), ('stemR0', 8), ('wedgeR', 6)]
SITE_FRAC = {1: 0.275, 2: 0.40, 3: 0.55, 4: 0.675, 5: 0.80, 6: 0.90}        # height of each leaf site / stem height
LEAF_ANGLE = {1: -64, 2: 60, 3: -52, 4: 48, 5: -40, 6: 34, 7: -5}           # degrees from straight up, - = left
LEAF_LEN = {1: 10.5, 2: 11.0, 3: 12.5, 4: 12.0, 5: 11.0, 6: 9.5, 7: 11.5}
LEAF_N = 49                                                                  # point 0 = stem end, point 24 = tip


def leaf_run(site, angle, length, half_w, n=LEAF_N, base=0.0, petiole=0.12, inner=1.0):
    """One leaf as a run of the line: out along one edge to the tip (point (n-1)/2), back along the other.
    `base` spreads the two ends (the tip leaf sits on the whole width of the stem)."""
    a = math.radians(angle)
    d = np.array([math.sin(a), -math.cos(a)])
    nr = np.array([math.cos(a), math.sin(a)])
    half = (n - 1) // 2
    out = []
    for j in range(n):
        f = j / half if j <= half else (n - 1 - j) / half
        sgn = -1.0 if j <= half else 1.0
        g = clamp((f - petiole) / (1 - petiole))
        w = half_w * math.sin(math.pi * g ** 0.8) ** 0.85 if g > 0 else 0.0
        if (j > half) == (angle <= 0):
            w *= inner                      # a bud lies against the stem: its stem-side edge is flat
        p = np.asarray(site, float) + d * (f * length) + nr * (sgn * w) + np.array([sgn * base * (1 - f), 0.0])
        out.append(tuple(p))
    return out


def shoot_key(name, stage='bare', wedge=True):
    """A key drawing of the shoot. stage: 'bare' (two buds and a pointed tip), 'spear' (every leaf out but
    still folded, stem half grown), 'leaf' (seven leaves open). wedge=False gives the square foot it has while
    it is still part of the twig."""
    Hs = {'bare': 20.0, 'spear': 23.5, 'leaf': 27.0}[stage]
    sway = {'bare': 0.0, 'spear': 0.5, 'leaf': 1.0}[stage]

    def cx(h):
        return (0.38 * math.sin(h * 18.0 / Hs) + 0.9 * sway * math.sin(h / Hs * 1.9)) * smooth((h - WEDGE_H) / 4.0)

    def hw(h):
        return lerp(1.0, 0.55, clamp(h / Hs))

    def side(h, sgn):
        return (cx(h) + sgn * hw(h), -h)

    def stem(h0, h1, sgn):
        return [side(h, sgn) for h in np.linspace(h0, h1, 5)]

    def leaf(k):
        if k == 7:
            site, base = (cx(Hs), -Hs), 0.55
        else:
            sgn = -1 if k % 2 else 1
            site, base = side(SITE_FRAC[k] * Hs, sgn), 0.0
        ang, ln = LEAF_ANGLE[k], LEAF_LEN[k]
        if stage == 'bare':
            if k == 7:
                return leaf_run(site, 0, 2.6, 0.0, base=base, petiole=0.0)
            if k in (3, 4):
                return leaf_run(site, ang * 0.62, 2.7, 1.0, petiole=0.0, inner=0.0)       # the two buds
            return [site]                                                       # not there yet
        if stage == 'spear':
            return leaf_run(site, ang * 0.5, ln * 0.62, ln * 0.035, base=base)
        return leaf_run(site, ang, ln, ln * 0.2, base=base)

    hs = {k: SITE_FRAC[k] * Hs for k in SITE_FRAC}
    foot = (0.0, 0.0) if wedge else None
    L = {
        'wedgeL': [foot or (-1.0, 0.0), (-1.0, -WEDGE_H)],
        'stemL0': stem(WEDGE_H, hs[1], -1), 'leaf1': leaf(1),
        'stemL1': stem(hs[1], hs[3], -1), 'leaf3': leaf(3),
        'stemL2': stem(hs[3], hs[5], -1), 'leaf5': leaf(5),
        'stemL3': stem(hs[5], Hs, -1), 'leaf7': leaf(7),
        'stemR3': stem(Hs, hs[6], 1), 'leaf6': leaf(6),
        'stemR2': stem(hs[6], hs[4], 1), 'leaf4': leaf(4),
        'stemR1': stem(hs[4], hs[2], 1), 'leaf2': leaf(2),
        'stemR0': stem(hs[2], WEDGE_H, 1),
        'wedgeR': [(1.0, -WEDGE_H), foot or (1.0, 0.0)],
    }
    return KeyContour.from_runs(name, SHOOT_SCHEMA, L)


SHOOT_KEYS = dict(
    ON_TWIG=shoot_key('ON_TWIG', 'bare', wedge=False),
    CUT=shoot_key('CUT', 'bare'),
    SPEAR=shoot_key('SPEAR', 'spear'),
    LEAF=shoot_key('LEAF', 'leaf'),
)
WEDGE_GROUP = 8


def _shoot_field():
    k = SHOOT_KEYS['CUT']
    g = np.zeros(len(k.pts), int)
    anc = np.full(len(k.pts), -1, int)
    for n in range(1, 8):
        a, b = k.runs[f'leaf{n}']
        g[a:b] = n
        anc[a:b] = a
        g[a], anc[a] = 0, -1                      # the stem end of each leaf belongs to the stem
        if n != 7:
            g[b - 1], anc[b - 1] = 0, -1
    for r in ('wedgeL', 'wedgeR'):
        a, b = k.runs[r]
        g[a:b] = WEDGE_GROUP
    return InBetweenField(g, anc)


SHOOT_FIELD = _shoot_field()
N_BASE = len(BASE_KEYS['WHOLE'].pts)
N_SHOOT = len(SHOOT_KEYS['CUT'].pts)
N_LINE = N_BASE + N_SHOOT + 2

# every pair the film in-betweens, as checkable Correspondences
CORRESPONDENCES = [correspond(BASE_KEYS[a[1]], BASE_KEYS[b[1]]) for a, b in zip(BASE_TRACK, BASE_TRACK[1:]) if a[1] != b[1]] + \
                  [correspond(SHOOT_KEYS[a], SHOOT_KEYS[b]) for a, b in (('ON_TWIG', 'CUT'), ('CUT', 'SPEAR'), ('SPEAR', 'LEAF'))]


# ================================================================ pacing =======

def twig_bend(t):
    """Sideways travel of the twig's top, in units (- = toward the stump). Keyed lean and strain, then the
    released stub is a damped spring (an InterventionFrame: nobody keys a spring)."""
    if t < T['cut']:
        return Pacing('lean', [(0, 0), (T['lean'], 0), (0.82, -3.2, 'smooth'), (T['strain'], -2.7, 'smooth'),
                               (T['pinch'], -5.4, 'smooth'), (T['cut'], -6.2, 'in')]).at(t)
    u = t - T['cut']
    return -6.2 * math.exp(-3.4 * u) * math.cos(2 * math.pi * 2.5 * u)


POSE = dict(   # the shoot's pose once it is free: lean in degrees (+ = to the right), squash, and droop
    lean=Pacing('lean', [(T['cut'], -22), (T['land'], -40, 'lin'), (T['land'] + 0.08, -52, 'out'), (2.30, -6, 'smooth'),
                         (T['rest'], 7, 'smooth'), (2.75, 19, 'smooth'), (3.6, 12), (4.24, 10), (T['crash'] + 0.07, -13, 'out'),
                         (4.50, 34, 'smooth'), (T['corner'], 40), (T['slip'], 50, 'smooth'), (T['over'], 24, 'smooth'),
                         (5.46, 12), (5.56, 14), (T['edge'], -10, 'out'), (T['stuck'], -2),
                         (PUSH[0], 6, 'lin'), (5.98, -7, 'lin'), (PUSH[1], 7, 'lin'), (6.14, -7, 'lin'), (PUSH[2], 6, 'lin'),
                         (T['drop'], -5, 'lin'), (T['seat'], -2, 'in'), (6.52, -4.5, 'out'), (6.63, 2.6), (6.76, -1.2), (6.9, 0),
                         (T['wait'][0] + 0.1, 0), (9.0, 2.5), (9.22, 2.5), (9.62, -1.2), (9.9, 0)]),
    squash=Pacing('squash', [(T['land'], 1), (T['land'] + 0.07, 0.78, 'out'), (2.30, 1.07), (T['rest'], 1),
                             (T['crash'], 1), (T['crash'] + 0.08, 0.86, 'out'), (4.55, 1.06), (4.9, 1),
                             (T['stuck'], 1), (PUSH[0], 0.88, 'in'), (5.98, 1.02), (PUSH[1], 0.87, 'in'), (6.14, 1.02), (PUSH[2], 0.87, 'in'),
                             (T['drop'], 1.0), (T['seat'], 1.07, 'in'),
                             (6.5, 0.95, 'out'), (6.62, 1.0), (T['tight'][0], 1), (T['tight'][1] - 0.05, 1.04, 'out'),
                             (T['tight'][1] + 0.12, 1), (9.0, 0.97), (9.22, 0.97), (9.62, 1.03), (9.9, 1)]),
    droop=Pacing('droop', [(T['wait'][0] + 0.1, 0), (9.0, 3.4), (9.22, 3.4), (9.64, -0.8), (9.92, 0)]),
)
WEDGE = Pacing('wedge', [(T['pinch'], 0), (T['cut'] - 0.04, 1, 'in'), (T['heal'][0], 1), (T['heal'][1], 0, 'smooth')])
STEM = Pacing('stem', [(9.5, 0), (10.25, 1, 'smooth'), (11.15, 2, 'smooth')])     # bare -> spear height -> full height


def leaf_open(k, t):
    """Progress of leaf k: 0 bud, 1 spear (out but folded), 2 open. The unfolding runs past 2 and settles."""
    t0 = LEAF_AT[k]
    if t <= t0:
        return 0.0
    if t < t0 + LEAF_SPEAR:
        return smooth((t - t0) / LEAF_SPEAR)
    t1 = t0 + LEAF_SPEAR + LEAF_PAUSE
    if t < t1:
        return 1.0
    return 1.0 + EASES['over'](clamp((t - t1) / LEAF_OPEN))


def band_progress(k, t):
    a, b = T['band'][k]
    return smooth(clamp((t - a) / (b - a)))


def draw_on(run, p):
    """InterventionFrame 'band draw-on': a run paid out along its own path. p = 0 all points on the first one,
    p = 1 the run as drawn. In between the line goes out as far as p and comes back ALONG ITSELF to where it
    started (a retrace: the pencil going back over its own mark), so the line stays one line and no chord is
    drawn across the loop. (Point for point, a loop growing from a dot inflates like a balloon; this one is thrown.)"""
    n = len(run)
    u = np.linspace(0, 1, n)
    ur = max(p, 0.8)
    g = np.where(u <= p, u, np.where(u <= ur, p, p * (1 - u) / max(1e-9, 1 - ur)))
    j = g * (n - 1)
    lo = np.floor(j).astype(int)
    hi = np.minimum(lo + 1, n - 1)
    f = (j - lo)[:, None]
    return run[lo] * (1 - f) + run[hi] * f


def ground_wave(t):
    """(centre x, height, half-width) of the swell that carries the shoot, or None. The carrier is a travelling
    displacement of the ground run."""
    if t < T['land'] or t > T['crash'] + 0.25:
        return None
    if t < T['rest']:
        x = lerp(TWIG_X - 1.3, 73.0, EASES['out'](clamp((t - T['land']) / 0.28)))
        amp = Pacing('dip', [(T['land'], 0), (T['land'] + 0.07, -1.5, 'out'), (2.3, 0.6), (T['rest'], 2.2)]).at(t)
        return x, amp, 6.0
    u = clamp((t - T['rest']) / (T['crash'] - T['rest']))
    x = 73.0 - 46.3 * u ** 1.45
    amp = Pacing('swell', [(T['rest'], 2.2), (3.3, 6.2), (4.1, 5.4), (T['crash'], 4.2), (T['crash'] + 0.25, 0, 'out')]).at(t)
    return x, amp, 6.5


def climb(t):
    """How far up the stump's right side the wedge point is: 0 at the root, 1 at the corner of the rim."""
    return Pacing('climb', [(T['crash'], 0), (T['corner'], 0.93, 'out'), (T['slip'], 0.885, 'smooth'), (T['over'], 1.0, 'in')]).at(t)


def bark_bulge(t):
    """(height y, size) of the bulge that runs up the bark under the shoot, or None."""
    if t < T['crash'] - 0.1 or t > T['over']:
        return None
    q = climb(t)
    y = RIM * q
    size = 2.4 * smooth((t - T['crash'] + 0.1) / 0.2) * (1 - smooth((q - 0.55) / 0.4))
    return y, size


# ============================================================== the line =======

def base_at(t):
    """The base contour at time t in units: the in-between of the two keys around t, then the interventions."""
    keys = BASE_TRACK
    a = b = keys[-1]
    u = 1.0
    for k0, k1 in zip(keys, keys[1:]):
        if t <= k1[0]:
            a, b = k0, k1
            u = EASES[k1[2] if len(k1) > 2 else 'smooth'](clamp((t - k0[0]) / max(1e-9, k1[0] - k0[0])))
            break
    A, B = BASE_KEYS[a[1]], BASE_KEYS[b[1]]
    P = A.pts + (B.pts - A.pts) * u
    R = A.runs
    # binding: paid out, never inflated
    for k, r in enumerate(BAND_RUNS):
        i0, i1 = R[r]
        src = P[i0:i1] if (a[1] in ('BOUND', 'TIGHT', 'HEALED') and b[1] in ('BOUND', 'TIGHT', 'HEALED')) else BASE_KEYS['BOUND'].pts[i0:i1]
        P[i0:i1] = draw_on(src, band_progress(k, t))
    # the twig leans, strains, and springs back
    bend = twig_bend(t)
    for r in ('twig_L', 'twig_R'):
        i0, i1 = R[r]
        h = np.clip(-P[i0:i1, 1] / TWIG_H, 0, 1.1)
        P[i0:i1, 0] += bend * h ** 2
        P[i0:i1, 1] += abs(bend) * 0.09 * h ** 2
    # the ground swells and carries
    wv = ground_wave(t)
    if wv:
        xc, amp, wd = wv
        i0, i1 = R['ground_M']
        x = P[i0:i1, 0]
        pin = np.clip((x - 26.0) / 3.5, 0, 1) * np.clip((TWIG_X - 1.3 - x) / 3.5, 0, 1)
        P[i0:i1, 1] -= amp * np.exp(-((x - xc) / wd) ** 2) * pin
    bg = bark_bulge(t)
    if bg:
        yc, size = bg
        i0, i1 = R['stump_R']
        foot = np.array([smooth(-yy / 5.0) for yy in P[i0:i1, 1]])          # the root does not move
        P[i0:i1, 0] += size * foot * np.exp(-((P[i0:i1, 1] - yc) / 3.6) ** 2)
    return P


def attach_index(t):
    """Where on the base the shoot stands, as a fractional point index. This is the slide: the correspondence of
    the shoot to the base is re-made every frame, and that re-making is the carrying."""
    R = BASE_KEYS['WHOLE'].runs
    top = R['twig_L'][1] - 0.5
    if t < T['cut']:
        return top
    if t < T['land']:
        u = (t - T['cut']) / (T['land'] - T['cut'])
        return lerp(top, R['twig_L'][0], u * u)
    if t < T['crash']:
        g0, g1 = R['ground_M']
        xs = BASE_KEYS['STUB'].pts[g0:g1, 0]
        return g0 + float(np.interp(ground_wave(t)[0], xs, np.arange(g1 - g0)))
    s0, s1 = R['stump_R']
    if t < T['over']:
        return s0 + (1 - climb(t)) * (s1 - 1 - s0)
    r0, r1 = R['top_R']
    if t < T['drop']:
        return r0 + (1 - smooth(clamp((t - T['over']) / (T['edge'] - T['over'])))) * (r1 - 1 - r0)
    c0, c1 = R['cleft_R']
    f = Pacing('into the cleft', [(T['drop'], 1.0), (T['seat'], 0.0, 'in')]).at(t)
    return (c0 - 0.5) + f * (c1 - 1 - c0 + 0.5)


def shoot_local(t):
    """The shoot in its own coordinates at time t: the in-between of its keys under SHOOT_FIELD."""
    K = SHOOT_KEYS
    prog = {0: STEM.at(t)}
    for k in range(1, 8):
        prog[k] = leaf_open(k, t)
    def stage(lo):                 # progress within CUT->SPEAR (lo=0) or SPEAR->LEAF (lo=1) for each group
        return {g: (clamp(e - lo) if lo == 0 else max(0.0, e - lo)) for g, e in prog.items()}
    P = SHOOT_FIELD.between(K['CUT'].pts.copy(), K['SPEAR'].pts, stage(0))
    # second leg: add what SPEAR->LEAF contributes (groups past 1 only)
    Q = SHOOT_FIELD.between(K['SPEAR'].pts.copy(), K['LEAF'].pts, stage(1))
    P = P + (Q - K['SPEAR'].pts)
    w = WEDGE.at(t)
    m = SHOOT_FIELD.group == WEDGE_GROUP
    P[m] = K['ON_TWIG'].pts[m] + (K['CUT'].pts[m] - K['ON_TWIG'].pts[m]) * w
    droop = POSE['droop'].at(t)
    if droop:
        h = np.clip((-P[:, 1] - WEDGE_H) / 20.0, 0, None)
        P[:, 0] += droop * h ** 2
        P[:, 1] += abs(droop) * 0.25 * h ** 2
    return P


def shoot_pose(t, base=None):
    """(attach point in units, lean in radians, (sx, sy)) of the shoot at time t."""
    P = base_at(t) if base is None else base
    s = attach_index(t)
    i = int(math.floor(s))
    f = s - i
    A = P[i] * (1 - f) + P[min(i + 1, len(P) - 1)] * f
    if t < T['cut']:
        lean = math.atan2(2 * twig_bend(t), TWIG_H)
        sy = 1.0
    else:
        lean = math.radians(POSE['lean'].at(t))
        sy = POSE['squash'].at(t)
    return A, lean, (1 / math.sqrt(sy), sy)


@dataclass
class GraftFrame:
    """One frame of the line, in screen px. `pts` is the whole line; `tag` names the run of every point;
    `shoot` and `leaves[k]` are slices into it (leaf point 0 = stem end, point 24 = tip)."""
    t: float
    pts: np.ndarray
    tag: np.ndarray
    shoot: slice
    leaves: dict
    attach: tuple
    lean: float
    local: np.ndarray = field(repr=False, default=None)


_TAGS = None


def _tags(i):
    global _TAGS
    if _TAGS is None:
        b = np.empty(N_BASE, object)
        for r, (a, c) in BASE_KEYS['WHOLE'].runs.items():
            b[a:c] = r
        s = np.empty(N_SHOOT, object)
        for r, (a, c) in SHOOT_KEYS['CUT'].runs.items():
            s[a:c] = 'shoot:' + r
        _TAGS = (b, s)
    b, s = _TAGS
    return np.concatenate([b[:i + 1], ['shoot:join'], s, ['shoot:join'], b[i + 1:]])


def graft_line(t, x=ORIGIN[0], y=ORIGIN[1], s=SCALE, mirror=MIRROR):
    """THE LINE at time t (0..12 s of the study): one open polyline of N_LINE points, left edge to right edge.
    (x, y) = screen position of the ground under the middle of the stump, s = px per unit. mirror=True puts the
    twig on the left and the stump on the right (the film's direction); the line then runs right to left."""
    t = clamp(t, 0.0, SECONDS)
    B = base_at(t)
    A, lean, (sx, sy) = shoot_pose(t, B)
    L = shoot_local(t)
    ca, sa = math.cos(lean), math.sin(lean)
    X, Y = L[:, 0] * sx, L[:, 1] * sy
    S = np.stack([A[0] + X * ca - Y * sa, A[1] + X * sa + Y * ca], 1)
    o = 1.0 - WEDGE.at(t)                      # 1 = the shoot's foot is open to the base (one stem), 0 = it stands on a point
    j0, j1 = A + (S[0] - A) * o, A + (S[-1] - A) * o
    i = int(math.floor(attach_index(t)))
    pts = np.concatenate([B[:i + 1], [j0], S, [j1], B[i + 1:]])
    pts = pts * np.array([-s if mirror else s, s]) + np.array([x, y])
    a0 = i + 2
    leaves = {}
    for k in range(1, 8):
        r0, r1 = SHOOT_KEYS['CUT'].runs[f'leaf{k}']
        leaves[k] = slice(a0 + r0, a0 + r1)
    return GraftFrame(t, pts, _tags(i), slice(a0, a0 + N_SHOOT), leaves, (x + A[0] * (-s if mirror else s), A[1] * s + y), -lean if mirror else lean, L)


def leaf_contours(t=SECONDS, x=ORIGIN[0], y=ORIGIN[1], s=SCALE, mirror=MIRROR):
    """The seven leaves at time t as seven 49-point contours in screen px, bottom to top (1..7). Point 0 is the
    stem end and point 24 the tip: what act 2 hands to act 3 (stem becomes tail, tip becomes nose)."""
    g = graft_line(t, x, y, s, mirror)
    return [g.pts[g.leaves[k]].copy() for k in range(1, 8)]


# ================================================================ drawing ======

_tooth = None


def _paper_tooth():
    global _tooth
    if _tooth is None:
        rs = np.random.RandomState(5)
        a = rs.uniform(0, 1, (H, W)).astype(np.float32)
        b = np.asarray(Image.fromarray((rs.uniform(0, 1, (H // 3 + 1, W // 3 + 1)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
        _tooth = 0.62 + 0.26 * a + 0.12 * b               # the paper does not move, so the tooth does not either
    return _tooth


def _waver(n, rng, amount, every=7):
    """Slow sideways wander of a hand along a line: n offsets, reseeded with the boil."""
    m = n // every + 3
    kx = np.array([rng.gauss(0, amount) for _ in range(m)])
    ky = np.array([rng.gauss(0, amount) for _ in range(m)])
    u = np.arange(n) / every
    return np.stack([np.interp(u, np.arange(m), kx), np.interp(u, np.arange(m), ky)], 1)


def draw_line(ink, pts, heavy=None, width=2.3, heavy_width=3.1, color=GRAPHITE, waver=0.55, strength=1.0):
    """Draw one polyline as a pencil line on ink (a kit.Ink): graphite laid over the paper's tooth, with a
    fainter first pass under it, wavering with the film's boil. `heavy` = a slice drawn with more pressure."""
    pts = np.asarray(pts, float)
    n = len(pts)
    SS = 2
    layer = Image.new('L', (ink.w * SS, ink.h * SS), 0)
    d = ImageDraw.Draw(layer)
    ghost = pts + _waver(n, ink.rng, waver * 1.5)
    main = pts + _waver(n, ink.rng, waver)
    d.line([tuple(p) for p in ghost * SS], fill=88, width=max(1, int(round(width * SS * 0.55))), joint='curve')
    d.line([tuple(p) for p in main * SS], fill=205, width=max(1, int(round(width * SS))), joint='curve')
    if heavy is not None:
        d.line([tuple(p) for p in main[heavy] * SS], fill=240, width=max(1, int(round(heavy_width * SS))), joint='curve')
    layer = layer.filter(ImageFilter.GaussianBlur(0.9)).resize((ink.w, ink.h), Image.LANCZOS)
    a = np.asarray(layer, np.float32) / 255.0
    if (ink.w, ink.h) == (W, H):
        a = a * _paper_tooth()
    a = np.clip(a * 1.25 * strength, 0, 1)[..., None]
    img = np.asarray(ink.img.convert('RGB'), np.float32)
    img = img * (1 - a) + np.array(color, np.float32) * a
    ink.img = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


def draw_graft(ink, t, x=ORIGIN[0], y=ORIGIN[1], s=SCALE, strength=1.0, mirror=MIRROR):
    """Draw the study's line at study time t (0..12) onto ink. Returns the GraftFrame (anchors for staging)."""
    g = graft_line(t, x, y, s, mirror)
    draw_line(ink, g.pts, heavy=g.shoot, strength=strength)
    return g


def picture(t, ink):
    ink.paper(kit.PAPER)
    draw_graft(ink, t)


# ================================================================== sound ======
# Nobody on this production can hear. Everything below is placed by the event table; none of it was listened to.

NOTE = dict(D4=293.66, E4=329.63, Fs4=369.99, A4=440.0, B4=493.88, D5=587.33, E5=659.25, Fs5=739.99, A5=880.0, B5=987.77, D6=1174.66)


def line_speed(fps=FPS):
    """Mean travel of the line's points per frame (units), one value per frame: what the pencil sound follows."""
    n = int(SECONDS * fps)
    out = np.zeros(n)
    prev = graft_line(0.0, 0, 0, 1, False).pts
    for k in range(1, n):
        cur = graft_line(k / fps, 0, 0, 1, False).pts
        out[k] = np.hypot(*(cur - prev).T).mean()
        prev = cur
    return out


def sound(mix, t0=0.0, gain=1.0):
    """The study's sound laid into a kit.Mix starting at t0: pencil rasp that follows the line's speed, and one
    sound per event. The wait (8.16 to 9.20) is declared near-silence: wind only."""
    g = gain
    px = -1.0 if MIRROR else 1.0          # pans were written for the unflipped drawing
    mix.wind(t0, SECONDS, gain=0.022 * g)
    sp = line_speed()
    env = np.interp(np.arange(int(SECONDS * mix.rate)) / mix.rate, np.arange(len(sp)) / FPS, np.clip(sp / 0.35, 0, 1) ** 0.7)
    rasp = mix.band(mix.noise(SECONDS), 1800, 6500) * env
    mix.add(rasp, t0, 0.05 * g)
    # the lean and the strain: fibres ticking, closer together
    tk, gap = T['strain'], 0.11
    while tk < T['cut'] - 0.03:
        mix.click(t0 + tk, gain=0.07 * g, pan=px * 0.45, bright=2600, seconds=0.02)
        gap *= 0.84
        tk += max(0.03, gap)
    mix.click(t0 + T['cut'], gain=0.42 * g, pan=px * 0.45, bright=7000, seconds=0.05)            # the cut: the one hard sound
    mix.pluck(t0 + T['cut'] + 0.02, 196.0, seconds=0.9, gain=0.10 * g, pan=px * 0.5)             # the stub springs
    mix.thud(t0 + T['land'], freq=95, gain=0.22 * g, pan=px * 0.4, seconds=0.25)
    dur = T['crash'] - T['rest']
    swell = mix.band(mix.noise(dur, 'brown'), 60, 900) * np.linspace(0.15, 1.0, int(dur * mix.rate)) ** 1.6
    half = len(swell) // 2
    mix.add(swell[:half], t0 + T['rest'], 0.16 * g, pan=px * 0.3)
    mix.add(swell[half:], t0 + T['rest'] + dur / 2, 0.16 * g, pan=px * -0.15)
    mix.thud(t0 + T['crash'], freq=62, gain=0.34 * g, pan=px * -0.25)
    mix.whoosh(t0 + T['crash'], seconds=0.6, gain=0.07 * g, pan=px * -0.3)
    mix.click(t0 + T['corner'] + 0.02, gain=0.08 * g, pan=px * -0.3, bright=1800)                # teeter
    mix.click(t0 + T['slip'], gain=0.07 * g, pan=px * -0.3, bright=1500)
    mix.step(t0 + T['over'], gain=0.14 * g, pan=px * -0.35, surface='wood')
    mix.step(t0 + T['stuck'], gain=0.16 * g, pan=px * -0.4, surface='wood')                     # too tight
    for tw in PUSH:
        mix.click(t0 + tw, gain=0.06 * g, pan=px * -0.4, bright=1400, seconds=0.025)
    mix.thud(t0 + T['seat'], freq=120, gain=0.26 * g, pan=px * -0.4, seconds=0.22)               # home
    mix.step(t0 + T['seat'], gain=0.18 * g, pan=px * -0.4, surface='wood')
    mix.click(t0 + T['grip'], gain=0.10 * g, pan=px * -0.4, bright=2200)
    for k, name in enumerate(('D4', 'E4', 'Fs4')):                                          # three turns, three notes
        a, b = T['band'][k]
        mix.whoosh(t0 + a, seconds=b - a, gain=0.035 * g, pan=px * -0.4)
        mix.pluck(t0 + b - 0.02, NOTE[name], seconds=1.1, gain=0.13 * g, pan=px * -0.4)
    mix.click(t0 + T['tight'][0] + 0.05, gain=0.09 * g, pan=px * -0.4, bright=1200, seconds=0.06)
    mix.pluck(t0 + T['bud'] + 0.05, NOTE['A4'], seconds=1.0, gain=0.07 * g, pan=px * -0.4)        # the bud: the first sound after the wait
    for k, name in zip((4, 3, 2, 1, 5, 6, 7), ('B4', 'D5', 'E5', 'Fs5', 'A5', 'B5', 'D6')):
        mix.pluck(t0 + LEAF_AT[k] + LEAF_SPEAR + LEAF_PAUSE + 0.04, NOTE[name], seconds=0.9, gain=0.085 * g, pan=px * -0.4 + 0.05 * (k % 3))
    mix.pluck(t0 + 11.3, NOTE['D4'] / 2, seconds=0.7, gain=0.06 * g, pan=px * -0.3)
    mix.reverb(0.12, 0.8)


# ================================================================== checks =====

def crossings(pts, tag=None):
    """Proper self-intersections of a polyline: list of (i, j) segment indices. With `tag`, each is classed."""
    P = np.asarray(pts, float)
    a, b = P[:-1], P[1:]
    keep = np.hypot(*(b - a).T) > 1e-6
    idx = np.nonzero(keep)[0]
    a, b = a[keep], b[keep]
    d = b - a

    def cross(u, v):
        return u[..., 0] * v[..., 1] - u[..., 1] * v[..., 0]

    out = []
    n = len(a)
    for i in range(n - 2):
        j = np.arange(i + 2, n)
        c, e = a[j], b[j]
        o1 = cross(d[i], c - a[i])
        o2 = cross(d[i], e - a[i])
        o3 = cross(d[j], a[i] - c)
        o4 = cross(d[j], b[i] - c)
        eps = 1e-7
        hit = (o1 * o2 < -eps) & (o3 * o4 < -eps)
        for jj in j[hit]:
            out.append((int(idx[i]), int(idx[jj])))
    return out


def classify(g):
    """Topology warnings for one GraftFrame: {'binding': n, 'union': n, 'unintended': [(tag, tag), ...]}.
    The binding is meant to cross what it binds, and a wedge driven into a cleft touches its walls; anything
    else crossing anything else is a flip nobody planned."""
    res = dict(binding=0, union=0, unintended=[])
    for i, j in crossings(g.pts):
        a, b = str(g.tag[i]), str(g.tag[j])
        both = a + ' ' + b
        wedge = 'wedge' in both or 'join' in both
        if 'band' in both:
            res['binding'] += 1
        elif g.t >= T['seat'] - 0.05 and (('shoot' in both and 'cleft' in both) or (wedge and 'top_' in both)
                                           or ('cleft' in both and 'top_' in both and g.t >= T['heal'][0])):
            res['union'] += 1                     # the wedge in the wood, and the wood closing over it
        elif wedge and 'twig' in both and T['pinch'] <= g.t <= T['free'] + 0.05:
            res['union'] += 1                     # the contour pinching shut through the foot of the shoot: the cut
        else:
            res['unintended'].append((a, b))
    return res


def _procrustes(A, B):
    """RMS distance (units) between two point sets after the best rotation, translation and uniform scale."""
    a, b = A - A.mean(0), B - B.mean(0)
    na, nb = np.sqrt((a ** 2).sum()), np.sqrt((b ** 2).sum())
    a, b = a / na, b / nb
    u, s, vt = np.linalg.svd(a.T @ b)
    return float(np.sqrt(max(0.0, 1 - s.sum() ** 2)) * nb / math.sqrt(len(A)))


def check(verbose=True):
    """The numerically testable invariants (MEASURED). Returns (ok, lines). Nothing here judges how it looks."""
    out, ok = [], True
    frames = [graft_line(k / FPS, 0, 0, 1, False) for k in range(int(SECONDS * FPS) + 1)]

    def rep(name, passed, detail):
        nonlocal ok
        ok = ok and passed
        out.append(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")

    for c in CORRESPONDENCES:
        r = c.check()
        rep(f"correspondence {r['pair']}", r['order_kept'], f"{r['points']} points, order kept, {r['moved']} move, furthest {r['max_travel']:.1f} u")
    rep('one line, same points', all(len(f.pts) == N_LINE for f in frames), f'{N_LINE} points in every one of {len(frames)} frames')
    gap = max(float(np.hypot(*np.diff(f.pts, axis=0).T).max()) for f in frames)
    rep('no hidden jump along the line', gap < 9.0, f'longest single segment {gap:.2f} u (limit 9; the straight ground has the longest)')
    # quiet outside the markers: the base contour never lurches
    worst, where = 0.0, 0.0
    for k in range(1, len(frames)):
        t = k / FPS
        if any(m.t0 - 1 / FPS <= t <= m.t1 + 1 / FPS for m in MARKERS):
            continue
        pa, pb = base_at((k - 1) / FPS), base_at(t)
        dmax = float(np.hypot(*(pb - pa).T).max())
        if dmax > worst:
            worst, where = dmax, t
    rep('base quiet outside discontinuity markers', worst < 1.6, f'largest one-frame travel of a base point {worst:.2f} u at {where:.2f} s (limit 1.6)')
    # shape identity of the shoot from the cut to the bud: same drawing, only posed
    ref = SHOOT_KEYS['CUT'].pts
    idw, idt = 0.0, 0.0
    for k in range(int(T['free'] * FPS) + 1, int(T['wait'][0] * FPS)):
        r = _procrustes(ref, frames[k].local)
        if r > idw:
            idw, idt = r, k / FPS
    rep('shoot identity, cut to wait', idw < 0.05, f'worst similarity residual vs key CUT {idw:.4f} u at {idt:.2f} s (squash is applied in the pose, not the shape)')
    wd = max(_procrustes(ref, frames[k].local) for k in range(int(T['wait'][0] * FPS), int(T['bud'] * FPS)))
    rep('shoot identity through the wilt', wd < 0.8, f'worst residual {wd:.3f} u (the droop bends it; limit 0.8)')
    # wedge unchanged from cut to heal
    wm = SHOOT_FIELD.group == WEDGE_GROUP
    wv = max(float(np.abs(frames[k].local[wm] - ref[wm]).max()) for k in range(int(T['cut'] * FPS) + 1, int(T['heal'][0] * FPS)))
    rep('wedge point unchanged, cut to heal', wv < 1e-9, f'max deviation {wv:.2e} u')
    # leaves
    lf = leaf_contours(SECONDS, 0, 0, 1, False)
    tips = [float(np.hypot(*(c[24] - c[0]))) for c in lf]
    rep('seven leaves, 49 points, tip at 24', len(lf) == 7 and all(len(c) == 49 for c in lf) and min(tips) > 8,
        'lengths ' + ' '.join(f'{x:.1f}' for x in tips) + ' u')
    # topology
    bad, bind, union = [], 0, 0
    for k in range(0, len(frames), 2):
        r = classify(frames[k])
        bind, union = max(bind, r['binding']), max(union, r['union'])
        if r['unintended']:
            bad.append((k / FPS, r['unintended'][:3]))
    rep('no unintended topological flips', not bad, f'0 unplanned crossings in {len(frames[::2])} frames; binding crossings up to {bind}, wedge/cleft contacts up to {union}'
        if not bad else f'{len(bad)} frames with unplanned crossings')
    for t, pairs in bad[:40]:
        out.append(f'      TOPOLOGY WARNING {t:5.2f} s  ' + '; '.join(f'{a} x {b}' for a, b in pairs))
    if verbose:
        print('\n'.join(out))
    return ok, out


# ================================================================== sheets =====

SHEET_TIMES = [0.2, 0.85, 1.55, 1.75, 2.12, 3.0, 4.0, 4.6, 5.1, 5.6, 6.1, 6.6, 7.4, 8.9, 9.9, 11.8]


def still(t, zoom=None):
    """The frame at time t as a PIL image. zoom = (cx, cy, factor) enlarges around a screen point."""
    k = int(round(t * FPS))
    ink = kit.Ink(k / FPS, k, (W, H), 8, 1.2, 0)
    ink.paper()
    picture(k / FPS, ink)
    img = ink.finish()
    if zoom:
        cx, cy, f = zoom
        w, h = W / f, H / f
        x0, y0 = clamp(cx - w / 2, 0, W - w), clamp(cy - h / 2, 0, H - h)
        img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.LANCZOS)
    return img


def sheet(path, times=None, cols=4, bw=False, zoom=None):
    times = times or SHEET_TIMES
    rows = (len(times) + cols - 1) // cols
    cw, ch = 480, 270
    out = Image.new('RGB', (cols * cw, rows * ch), (255, 255, 255))
    for n, t in enumerate(times):
        im = still(t, zoom).resize((cw - 4, ch - 4), Image.LANCZOS)
        if bw:
            im = im.convert('L').convert('RGB')
        out.paste(im, ((n % cols) * cw + 2, (n // cols) * ch + 2))
        ImageDraw.Draw(out).text(((n % cols) * cw + 8, (n // cols) * ch + 6), f'{t:.2f}', fill=(150, 40, 40))   # label on the sheet only
    out.save(path)
    return path


def key_sheet(path):
    """The key drawing set: each base key with the shoot key that goes with it, plain, no in-betweening."""
    pairs = [('WHOLE', 'ON_TWIG'), ('PINCH', 'CUT'), ('STUB', 'CUT'), ('OPEN', 'CUT'), ('GRIP', 'CUT'), ('BOUND', 'CUT'), ('TIGHT', 'SPEAR'), ('HEALED', 'LEAF')]
    cw, ch = 480, 270
    out = Image.new('RGB', (4 * cw, 2 * ch), kit.PAPER)
    d = ImageDraw.Draw(out)
    for n, (b, sk) in enumerate(pairs):
        ox, oy, s = (n % 4) * cw + 150, (n // 4) * ch + 215, 2.5
        B, R = BASE_KEYS[b], BASE_KEYS[b].runs
        d.line([(ox + p[0] * s, oy + p[1] * s) for p in B.pts], fill=GRAPHITE, width=2)
        on_twig = b in ('WHOLE', 'PINCH')
        i = (R['twig_L'][1] - 1) if on_twig else (R['cleft_L'][1] - 1)
        A = (B.pts[i] + B.pts[i + 1]) / 2
        if b == 'STUB':
            A = A + np.array([-30.0, -16.0])
        d.line([(ox + (A[0] + p[0]) * s, oy + (A[1] + p[1]) * s) for p in SHOOT_KEYS[sk].pts], fill=(120, 40, 50), width=2)
        d.text((n % 4 * cw + 8, n // 4 * ch + 6), f'{b} + {sk}', fill=(150, 40, 40))
    out.save(path)
    return path


# =================================================================== main ======

def build():
    film = Film(SLUG, SECONDS, boil=8, wobble=1.2, seed=7)
    film.picture(picture)
    film.sound(sound)
    film.poster_at = 11.6
    return film


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--check':
        sys.exit(0 if check()[0] else 1)
    elif a and a[0] == '--sheet':
        ts = [float(x) for x in a[2:] if not x.startswith('--')]
        print(sheet(a[1], ts or None, bw='--bw' in a))
    elif a and a[0] == '--still':
        z = (float(a[3]), float(a[4]), float(a[5])) if len(a) > 5 else None
        still(float(a[2]), z).save(a[1])
        print(a[1])
    elif a and a[0] == '--keys':
        print(key_sheet(a[1]))
    else:
        build().render()
