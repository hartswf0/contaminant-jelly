"""STUDY (SCION law 3, animation-02 hard proof): the moment a cow path is made.

A small cow reaches a gate on the path, wants the far side, tries it, is put back, waits for a calf,
then chooses to go round the end of the fence. The others follow, and the tissue of the hill wears thin
where their hooves fell. Backlit shadow theatre, silhouette only, 12 drawings a second, no words.

    python3 films/swarm/cowpath/study_shadow.py            -> assets/films/cowpath-study-shadow.mp4
    python3 films/swarm/cowpath/study_shadow.py --check    -> the measured invariants
    python3 films/swarm/cowpath/study_shadow.py --sheet OUT.png [--bw] [t0 t1]   -> 16-still contact sheet
    python3 films/swarm/cowpath/study_shadow.py --xsheet   -> the exposure sheet as text

The native primitives of animation-02 are kept as data, by name:
    BacklitShape, PinnedJoint, JointLimit, ShadowPlane, ReplacementProfile, ContactPlane, ExposureSheet.
The cow puppet itself (cut pieces, pins, limits) is cast.py; this file adds the hinged gate, the stage,
the turned-head replacement profiles, the floor that keeps what touched it, and the sheet that times it.
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
import cast

W, H = kit.W, kit.H
SLUG = 'cowpath-study-shadow'
SECONDS = 12.0
S = 0.56                    # pixels per cow unit: the lead is 79 px at the withers
SS = 3                      # supersampling of everything cut here

# ----------------------------------------------------------------- primitives ---


@dataclass(frozen=True)
class ShadowPlane:
    """One sheet between the lamp and the screen. `order` is back to front; `tone` is the shadow it throws
    (nearer the screen = blacker); `soft` is its edge blur in px (further from the screen = softer)."""
    name: str
    order: int
    tone: tuple
    soft: float = 0.0


PLANES = dict(
    far=ShadowPlane('far', 0, (196, 140, 74), 1.6),        # a hill a long way behind the screen: pale, soft
    mid=ShadowPlane('mid', 1, (74, 44, 24), 0.0),          # the fence and the gate: brown card, so a black cow reads against it
    actor=ShadowPlane('actor', 2, cast.BLACK, 0.0),        # the animals, on the glass
    fore=ShadowPlane('fore', 3, (12, 9, 8), 0.8),          # grass at the bottom of the frame, nearest us
)


@dataclass(frozen=True)
class JointLimit:
    lo: float
    hi: float

    def clamp(self, v):
        """-> (value inside the limit, which stop it hit: 'lo', 'hi' or None)."""
        if v <= self.lo:
            return self.lo, 'lo'
        if v >= self.hi:
            return self.hi, 'hi'
        return v, None


@dataclass
class PinnedJoint:
    """A pin with a limit. `set()` clamps and remembers every time a stop was hit (the gate's chain)."""
    name: str
    pin: tuple                       # where the pin is (floor coordinates gx, gz for the gate)
    limit: JointLimit
    value: float = 0.0
    hits: list = field(default_factory=list)

    def set(self, v, when=None):
        self.value, stop = self.limit.clamp(v)
        if stop and when is not None:
            self.hits.append((when, stop))
        return self.value


@dataclass
class BacklitShape:
    """A piece of cut card: polygons and strokes in screen px, on a plane, at a depth gz on the floor
    (bigger gz = nearer us = pasted later)."""
    name: str
    plane: str
    depth: float
    polys: list = field(default_factory=list)            # [[(x, y), ...], ...]
    strokes: list = field(default_factory=list)          # [((x0, y0), (x1, y1), width_px), ...]


@dataclass(frozen=True)
class ReplacementProfile:
    """A swapped head. Reiniger cut a second head for a turned head; here the same pieces are re-set about
    the poll: turn=1 the profile as cut, about 0.3 the face coming round to us, -1 looking back over her
    shoulder. `drop` lowers the swapped head (cow units) so it sits on the neck."""
    name: str
    turn: float
    pieces: tuple = ('jaw', 'head', 'horn', 'crump', 'ear')
    drop: float = 0.0


PROFILES = dict(
    front=ReplacementProfile('front', 1.0),
    toward=ReplacementProfile('toward', 0.34, drop=2.0),
    back=ReplacementProfile('back', -1.0, drop=3.0),
)


@dataclass(frozen=True)
class Cell:
    name: str
    d0: int                 # first drawing
    d1: int                 # one past the last drawing
    hold: bool = False      # a held drawing: nothing of this level changes


class ExposureSheet:
    """The dope sheet. 24 frames a second, each drawing exposed for `on` frames (2 = twelve drawings a
    second). Every level (a puppet) is a row of named cells; the performance reads its times from here."""

    def __init__(self, fps=24, on=2, seconds=SECONDS):
        self.fps, self.on = fps, on
        self.n = int(round(seconds * fps / on))
        self.levels = {}

    def level(self, name, cells):
        """cells: [(name, first_drawing, hold=False), ...]; each runs to the next one's start."""
        out = []
        for i, c in enumerate(cells):
            d1 = cells[i + 1][1] if i + 1 < len(cells) else self.n
            out.append(Cell(c[0], c[1], d1, bool(c[2]) if len(c) > 2 else False))
        self.levels[name] = out
        return self

    def drawing(self, frame):
        return min(self.n - 1, frame // self.on)

    def time(self, d):
        return d * self.on / self.fps

    def cell(self, level, d):
        for c in self.levels[level]:
            if c.d0 <= d < c.d1:
                return c
        return self.levels[level][-1]

    def at(self, level, name):
        """(first drawing, one past last) of a named cell."""
        for c in self.levels[level]:
            if c.name == name:
                return c.d0, c.d1
        raise KeyError((level, name))

    def t(self, level, name):
        d0, d1 = self.at(level, name)
        return self.time(d0), self.time(d1)

    def text(self):
        names = list(self.levels)
        rows = ['draw  time  ' + ''.join(f'{n:<16}' for n in names)]
        last = {n: None for n in names}
        for d in range(self.n):
            cs = [self.cell(n, d) for n in names]
            if any(c.d0 == d for c in cs):
                rows.append(f'{d:4d} {self.time(d):5.2f}  ' + ''.join(
                    f"{(c.name + (' (hold)' if c.hold else '')) if c.d0 == d else '  |':<16}" for c in cs))
        return '\n'.join(rows)


# ----------------------------------------------------------------- the floor ---

Y0 = 380.0                  # the hoof line of the old path (gz = 0)
SKEW, FORE = 1.0, 0.32      # the floor is drawn oblique: one unit toward us goes 1 px right and 0.32 px down
GX0 = 424.0                 # the fence stands on gx = GX0, from the crest toward us
FENCE_GZ = (-34.0, 100.0)    # hinge post ... end post


class ContactPlane:
    """The ground. Floor coordinates (gx along the path, gz toward us) <-> screen px; the line the animals
    walk (`y(x)`: screen y of the ground under screen x); and what contact leaves behind: every footfall is
    kept, and the tissue wears thin there."""

    def __init__(self, knots, soften=22):
        self.knots = knots
        xs = np.arange(-200, W + 400)
        ys = np.interp(xs, [k[0] for k in knots], [k[1] for k in knots])
        k = np.hanning(2 * soften + 1)
        ys = np.convolve(np.pad(ys, soften, mode='edge'), k / k.sum(), 'valid')
        self._xs, self._ys = xs, ys
        self.prints = []            # (time, x, y, strength, radius)
        self.passes = []            # (function t -> x of the animal's middle, x_from, strength)

    @staticmethod
    def project(gx, gz, h=0.0):
        return (gx + SKEW * gz, Y0 + FORE * gz - h)

    @staticmethod
    def unproject(x, y):
        gz = (y - Y0) / FORE
        return (x - SKEW * gz, gz)

    def y(self, x):
        return float(np.interp(x, self._xs, self._ys))

    def gz(self, x):
        return (self.y(x) - Y0) / FORE

    def old_path(self, strength=0.3):
        """The path that was there before the film: straight along the crest and through the gate."""
        if getattr(self, '_old', None) is None:
            im = Image.new('L', (W, H), 0)
            d = ImageDraw.Draw(im)
            rs = np.random.RandomState(3)
            x = -10.0
            while x < W + 10:                                  # two ruts, broken, as a cart leaves them
                ln = rs.uniform(18, 60)
                for dy in (-1.0, 5.0):
                    if rs.rand() < 0.85:
                        d.line([(x, Y0 + dy + rs.uniform(-0.6, 0.6)), (x + ln, Y0 + dy + rs.uniform(-0.6, 0.6))], fill=255, width=2)
                x += ln + rs.uniform(3, 12)
            self._old = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), np.float32) * (strength / 255.0)
        return self._old

    def tread(self, t, x, strength=0.3, radius=4.0):
        self.prints.append((t, x, self.y(x) + 1.0, strength, radius))

    def wear(self, t):
        """How thin the tissue is worn at time t: float array HxW, 0 = untouched, 1 = worn through."""
        im = Image.new('L', (W, H), 0)
        acc = self.old_path().copy()
        for xf, x_from, strength in self.passes:               # the band every passing body tramples
            x1 = xf(t) - 30
            if x1 <= x_from + 2:
                continue
            im.paste(0, (0, 0, W, H))
            pts = [(x, self.y(x) + 1.5) for x in np.arange(x_from, x1, 4.0)]
            if len(pts) > 1:
                ImageDraw.Draw(im).line(pts, fill=255, width=7, joint='curve')
                acc += np.asarray(im, np.float32) * (strength / 255.0)
        im.paste(0, (0, 0, W, H))
        d = ImageDraw.Draw(im)
        pr = np.zeros((H, W), np.float32)
        for (tp, x, y, strength, r) in self.prints:
            if tp <= t:
                im.paste(0, (0, 0, W, H))
                d.ellipse([x - r, y - r * 0.45, x + r, y + r * 0.45], fill=255)
                x0, x1, y0, y1 = int(x - r - 2), int(x + r + 3), int(y - r), int(y + r + 1)
                x0, y0 = max(0, x0), max(0, y0)
                pr[y0:y1, x0:x1] += np.asarray(im, np.float32)[y0:y1, x0:x1] * (strength / 255.0)
        acc += pr
        acc = np.asarray(Image.fromarray(np.clip(acc, 0, 1) * 255).convert('L').filter(ImageFilter.GaussianBlur(1.1)),
                         np.float32) / 255.0
        return acc


# the walked line, in screen px. Flat along the old path; then down ALONG the fence (the fence runs
# 1 px right per 0.32 px down, and so does she, keeping her chest on the near side of it); round the
# end post; and back up to the old line beyond.
X_GATE = GX0 - 64.0         # where she stands when she first reaches the gate
X_BACK = X_GATE - 44.0      # where the gate puts her back to; everyone leaves the old path from here
ROUTE = [(-300, Y0), (X_BACK + 22, Y0), (GX0 + 66, Y0 + FORE * 128), (GX0 + 160, Y0 + FORE * 138), (GX0 + 330, Y0), (1400, Y0)]
OLD_PATH = [(-300, Y0), (1400, Y0)]


# ----------------------------------------------------------------- the stage ---

_stage_cache = {}


def ridge(x):
    """The crest of the hill (screen y): the old path runs 18 px in front of it."""
    return 362.0 + 3.0 * math.sin(x / 170.0 + 0.6) + 2.0 * math.sin(x / 61.0)


def backlit_stage(size=(W, H), lamp=(0.66, 0.40)):
    """The lit screen: amber, brightest where the lamp stands behind it. Returns an RGB image (cached)."""
    key = ('stage', size, lamp)
    if key not in _stage_cache:
        w, h = size
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot((xx - lamp[0] * w) / (w * 0.62), (yy - lamp[1] * h) / (h * 0.78))
        g = np.clip(1 - r, 0, 1) ** 1.4
        top, low = np.array([232, 176, 96], np.float32), np.array([255, 236, 190], np.float32)
        a = top[None, None, :] * (1 - g[..., None]) + low[None, None, :] * g[..., None]
        a *= (1 - 0.10 * (yy / h))[..., None]
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        # the far plane: a pale hill and a clump of trees beyond the gate, where she wants to be
        pl = PLANES['far']
        m = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(m)
        pts = [(x * 2, (352 - 34 * math.exp(-((x - 820) / 170.0) ** 2) - 10 * math.exp(-((x - 600) / 90.0) ** 2)) * 2)
               for x in range(430, w + 8, 6)]
        d.polygon([(430 * 2, 372 * 2)] + pts + [(w * 2, 372 * 2)], fill=255)
        for cx, cy, rr in ((842, 304, 15), (858, 298, 18), (874, 306, 13), (700, 336, 7), (710, 333, 9)):
            d.ellipse([(cx - rr) * 2, (cy - rr) * 2, (cx + rr) * 2, (cy + rr) * 2], fill=255)
        for cx in (848, 866):
            d.rectangle([(cx - 1.5) * 2, 306 * 2, (cx + 1.5) * 2, 326 * 2], fill=255)
        m = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(pl.soft))
        im.paste(Image.new('RGB', size, pl.tone), (0, 0), m.point(lambda v: int(v * 0.62)))
        _stage_cache[key] = im
    return _stage_cache[key].copy()


def tissue_mask(size=(W, H)):
    """How much tissue lies over the light at each pixel (float HxW): one sheet for the hill, a second
    sheet lower down. 0 above the crest."""
    key = ('tissue', size)
    if key not in _stage_cache:
        w, h = size
        m1 = Image.new('L', (w * 2, h * 2), 0)
        ImageDraw.Draw(m1).polygon([(0, h * 2)] + [(x * 2, ridge(x) * 2) for x in range(0, w + 8, 4)] + [(w * 2, h * 2)], fill=255)
        m2 = Image.new('L', (w * 2, h * 2), 0)
        ImageDraw.Draw(m2).polygon([(0, h * 2)] + [(x * 2, (486 + 9 * math.sin(x / 140.0 + 2.0) + 0.012 * (x - 300)) * 2)
                                                  for x in range(0, w + 8, 4)] + [(w * 2, h * 2)], fill=255)
        a = np.asarray(m1.resize((w, h), Image.LANCZOS), np.float32) / 255.0
        b = np.asarray(m2.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255.0
        _stage_cache[key] = (a, b)
    return _stage_cache[key]


TISSUE = np.array([0.80, 0.66, 0.50], np.float32)       # what one sheet of amber tissue lets through
TISSUE2 = np.array([0.80, 0.70, 0.58], np.float32)


def lay_tissue(stage, wear=None):
    """The hill: tissue over the lit screen, thinned where `wear` (float HxW 0..1) says hooves have been.
    stage: RGB image from backlit_stage(). Returns an RGB image."""
    a, b = tissue_mask(stage.size)
    px = np.asarray(stage, np.float32)
    dens = a if wear is None else a * (1.0 - 0.9 * np.clip(wear, 0, 1))
    px = px * (1.0 - dens[..., None] * (1.0 - TISSUE[None, None, :]))
    px = px * (1.0 - b[..., None] * (1.0 - TISSUE2[None, None, :]))
    return Image.fromarray(px.clip(0, 255).astype(np.uint8))


def foreground(img):
    """Black grass and a thistle at the bottom corners, on the plane nearest us. Draws onto img."""
    key = 'fore'
    if key not in _stage_cache:
        pl = PLANES['fore']
        m = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(m)
        rs = np.random.RandomState(5)
        for x0, x1, base, tall in ((-10, 250, 548, 46), (700, 975, 550, 58)):
            for _ in range(int((x1 - x0) / 5)):
                x = rs.uniform(x0, x1)
                edge = min(x - x0, x1 - x) / (x1 - x0)
                hgt = tall * (0.35 + 0.65 * rs.rand()) * (0.4 + 1.6 * edge)
                lean = rs.uniform(-0.5, 0.5) * hgt
                d.polygon([((x - 3) * 2, base * 2), ((x + 3) * 2, base * 2), ((x + lean) * 2, (base - hgt) * 2)], fill=255)
        for bx, top in ((842, 462), (880, 478)):                 # thistles
            d.line([(bx * 2, 545 * 2), ((bx + 3) * 2, top * 2)], fill=255, width=6)
            for k in range(9):
                an = -math.pi / 2 + (k - 4) * 0.33
                d.line([((bx + 3) * 2, top * 2), ((bx + 3 + 11 * math.cos(an)) * 2, (top + 11 * math.sin(an)) * 2)], fill=255, width=4)
            d.ellipse([(bx - 3) * 2, (top - 1) * 2, (bx + 9) * 2, (top + 10) * 2], fill=255)
        m = m.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(pl.soft))
        _stage_cache[key] = (Image.new('RGB', (W, H), pl.tone), m)
    col, m = _stage_cache[key]
    img.paste(col, (0, 0), m)


# ----------------------------------------------------------------- the gate ---

GATE_LEN = 70.0
GATE_BARS = (9.0, 20.0, 31.0, 42.0, 54.0)                 # heights of the five bars, px
GATE_SWING = JointLimit(-4.0, 12.0)                       # degrees: the chain lets it go 12 one way, the post stops it at -4
GATE_SAG = JointLimit(0.0, 3.0)                           # px the latch end drops under a weight (play in the hinge)


def new_gate():
    """The gate's two joints: the hinge (on the crest post) and the sag of the leaf on its pins."""
    return dict(hinge=PinnedJoint('gate_hinge', (GX0, FENCE_GZ[0]), GATE_SWING),
                sag=PinnedJoint('gate_sag', (GX0, FENCE_GZ[0]), GATE_SAG))


def gate_point(a, h, swing=0.0, sag=0.0):
    """Screen px of the point `a` px along the leaf from the hinge and `h` px up it, at a hinge angle."""
    th = math.radians(swing)
    gx = GX0 + a * math.sin(th)
    gz = FENCE_GZ[0] + a * math.cos(th)
    x, y = ContactPlane.project(gx, gz, h)
    return (x, y + sag * a / GATE_LEN)


def gate_bar_x(h, swing=0.0, gz=0.0):
    """Screen x of the leaf where it crosses floor depth gz (where a cow on the old path meets it)."""
    a = (gz - FENCE_GZ[0]) / max(0.2, math.cos(math.radians(swing)))
    return gate_point(a, h, swing)[0]


def gate_shapes(swing=0.0, sag=0.0):
    """The fence and its gate as BacklitShapes on the 'mid' plane, each with its floor depth, ready to be
    sorted among the animals. swing (degrees) and sag (px) are the gate's two joint values."""
    P = ContactPlane.project
    out = []

    def post(name, gz, w, h, lean=0.0, cap=True):
        x, y = P(GX0, gz)
        top = (x + lean, y - h)
        poly = [(x - w / 2, y + 1), (x + w / 2, y + 1), (top[0] + w / 2, top[1]), (top[0] - w / 2, top[1])]
        if cap:
            poly = poly[:2] + [(top[0] + w / 2, top[1]), (top[0], top[1] - w * 0.7), (top[0] - w / 2, top[1])]
        out.append(BacklitShape(name, 'mid', gz, polys=[poly]))

    post('hinge_post', FENCE_GZ[0], 9, 66)
    a_s = clamp((0.0 - FENCE_GZ[0]) / math.cos(math.radians(swing)), 4, GATE_LEN - 4)      # where the leaf crosses the path
    G = lambda a, h: gate_point(a, h, swing, sag)
    for name, a0, a1, depth in (('leaf_far', 0.0, a_s, -17.0), ('leaf_near', a_s, GATE_LEN, 17.0)):
        st = [(G(a0, hh), G(a1, hh), 3.4 if hh == GATE_BARS[-1] else 2.6) for hh in GATE_BARS]
        b0, b1 = GATE_BARS[0], GATE_BARS[-1]
        st.append((G(a0, lerp(b0, b1, a0 / GATE_LEN)), G(a1, lerp(b0, b1, a1 / GATE_LEN)), 2.2))    # the brace
        if a0 == 0.0:
            st.append((G(1.5, 5), G(1.5, 57), 3.2))
        else:
            st.append((G(GATE_LEN - 1.5, 5), G(GATE_LEN - 1.5, 57), 3.2))
        out.append(BacklitShape(name, 'mid', depth, strokes=st))
    post('latch_post', 38.0, 7, 61)
    for name, g0, g1 in (('stub_a', 38.0, 69.0), ('stub_b', 69.0, FENCE_GZ[1])):
        st = []
        for hh, droop in ((17.0, 1.5), (35.0, 2.5)):
            p0, pm, p1 = P(GX0, g0, hh), P(GX0, (g0 + g1) / 2, hh - droop), P(GX0, g1, hh)
            st += [(p0, pm, 2.4), (pm, p1, 2.4)]
        out.append(BacklitShape(name, 'mid', (g0 + g1) / 2, strokes=st))
    post('stub_post', 69.0, 5, 45, cap=False)
    post('end_post', FENCE_GZ[1], 6.5, 52, lean=4.0)
    return out


def draw_shape(img, shape):
    """Paste one BacklitShape onto an RGB image, antialiased, in its plane's tone."""
    pts = [q for poly in shape.polys for q in poly] + [q for s in shape.strokes for q in s[:2]]
    if not pts:
        return
    x0, y0 = int(min(q[0] for q in pts)) - 4, int(min(q[1] for q in pts)) - 4
    x1, y1 = int(max(q[0] for q in pts)) + 5, int(max(q[1] for q in pts)) + 5
    m = Image.new('L', ((x1 - x0) * SS, (y1 - y0) * SS), 0)
    d = ImageDraw.Draw(m)
    O = lambda q: ((q[0] - x0) * SS, (q[1] - y0) * SS)
    for poly in shape.polys:
        d.polygon([O(q) for q in poly], fill=255)
    for p, q, wd in shape.strokes:
        d.line([O(p), O(q)], fill=255, width=max(1, int(round(wd * SS))))
        r = wd * SS / 2
        for c in (O(p), O(q)):
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    m = m.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    pl = PLANES[shape.plane]
    if pl.soft:
        m = m.filter(ImageFilter.GaussianBlur(pl.soft))
    img.paste(Image.new('RGB', m.size, pl.tone), (x0, y0), m)


# ----------------------------------------------------------------- the puppets ---

def cut_cow(pose, kind='lead', profile='front', color=None):
    """The animal as one black card (RGBA) and its anchor, like cast.sprite(style='shadow'), but with a
    ReplacementProfile for the head: 'front' (as cut), 'toward' (coming round), 'back' (over her shoulder).
    Returns (image, (ax, ay), eye_xy_in_cow_units)."""
    prof = PROFILES[profile] if isinstance(profile, str) else profile
    if prof.turn == 1.0:
        im, an = cast.sprite(pose, S, 1, 'shadow', kind=kind, color=color)
        return im, an, None
    sol = cast.solve(pose, kind)
    R = sol['rig']
    sc = S * R.size * SS
    axis = sol['anchors']['poll'][0] - 5.0

    def swap(q):
        return (axis + prof.turn * (q[0] - axis), q[1] + prof.drop)

    polys = []
    for n, poly, _tone in sol['parts']:
        polys.append([swap(q) for q in poly] if n in prof.pieces else list(poly))
    xs = [q[0] * sc for poly in polys for q in poly]
    ys = [q[1] * sc for poly in polys for q in poly]
    pad = 7 * SS
    x0, y0 = math.floor(min(xs)) - pad, math.floor(min(ys)) - pad
    wd, ht = int(max(xs) - x0) + pad, int(max(ys) - y0) + pad
    wd, ht = wd + (-wd) % SS, ht + (-ht) % SS
    m = Image.new('L', (wd, ht), 0)
    d = ImageDraw.Draw(m)
    for poly in polys:
        d.polygon([(q[0] * sc - x0, q[1] * sc - y0) for q in poly], fill=255)
    if sol['clapper']:
        (cx, cy), cr = sol['clapper']
        d.ellipse([cx * sc - x0 - cr * sc, cy * sc - y0 - cr * sc, cx * sc - x0 + cr * sc, cy * sc - y0 + cr * sc], fill=255)
    eye_c, eye_open, eye_r = sol['eye']
    ex, ey = swap(eye_c)
    if eye_open > 0.05:                                    # the eye is a hole in the card; it narrows as the face turns
        k = 1.0 if eye_open <= 1 else eye_open ** 0.6
        rx = eye_r * sc * k * max(0.55, abs(prof.turn))
        ry = eye_r * sc * k * min(eye_open, 1.0)
        d.ellipse([ex * sc - x0 - rx, ey * sc - y0 - ry, ex * sc - x0 + rx, ey * sc - y0 + ry], fill=0)
    img = Image.new('RGBA', (wd, ht), tuple(color or cast.BLACK) + (0,))
    img.putalpha(m)
    img = img.resize((wd // SS, ht // SS), Image.LANCZOS)
    return img, (-x0 / SS, -y0 / SS), (ex, ey)


def place_cow(img, pose, x, y, kind='lead', profile='front', color=None):
    """Stand the animal's ground point on (x, y) of an RGB/RGBA image, at this study's scale. Returns the
    anchors (cast.place's), plus 'mask_box': (alpha image, (left, top)) for overlap measurement."""
    im, (ax, ay), _ = cut_cow(pose, kind, profile, color)
    xy = (int(round(x - ax)), int(round(y - ay)))
    if img is not None:
        img.paste(im, xy, im)
    a = cast.anchors(pose, xy[0] + ax, xy[1] + ay, S, 1, 0.0, kind)
    a['mask_box'] = (im.getchannel('A'), xy)
    return a


def shift_pose(p, units):
    """The same pose seen from a placement point `units` cow units further back: body and planted hooves
    move forward by that much, so the picture is unchanged. For changing where a puppet is held."""
    q = dict(p)
    q['dx'] = p.get('dx', 0.0) + units
    for leg in cast.LEGS:
        v = p[leg]
        if v[0] == 'ik':
            q[leg] = ('ik', v[1] + units, v[2])
    return q


def step_blend(p, q, u, order=('nh', 'nf', 'fh', 'ff'), lift=13.0, kind='lead'):
    """Pose u (0..1) of the way from p to q where the hooves STEP instead of sliding: each leg in turn is
    picked up, carried and set down in its own share of the time; the body eases across. For coming to a
    halt out of a walk, being put back a pace, and stepping off again."""
    u = clamp(u)
    out = cast.blend(p, q, smooth(u))
    n = len(order)
    share = 1.0 / (0.55 * n + 0.45)
    for i, leg in enumerate(order):
        a, b = p[leg], q[leg]
        if a[0] != 'ik' or b[0] != 'ik':
            continue
        w = clamp((u - i * 0.55 * share) / share)
        e = smooth(w)
        moved = math.hypot(b[1] - a[1], b[2] - a[2])
        up = lift * min(1.0, moved / 14.0) * math.sin(math.pi * w) ** 1.2 if 0 < w < 1 else 0.0
        out[leg] = ('ik', lerp(a[1], b[1], e), lerp(a[2], b[2], e) - up)
    return out


def walk_pose(kind, x, ground, phase=0.0, stride_k=1.0, lift=1.0, carry=0.0, weight=1.0, over=None):
    """cast.walk_on's pose (not drawn) with a stride that can be lengthened (`stride_k`: the calf at 1.5
    takes fewer, longer steps). ground: function px -> px. Returns (pose, y_of_ground_under_her)."""
    R = cast.Rig.of(kind)
    sc = S * R.size
    stride = R.stride * stride_k
    y0 = ground(x)
    rel = lambda xr: (ground(x + xr * sc) - y0) / sc
    pose = cast.walk(x / sc + phase * stride, ground=rel, lift=lift, carry=carry, stride=stride, kind=kind, weight=weight)
    if over:
        pose.update(over)
    return pose, y0


def reach_fix(pose, kind='lead'):
    """If a planted hoof is further than the leg is long (a steep bit of ground, a body pitched up), let the
    body sink until it reaches, as a cow gives at the knee: no hoof is ever left hanging off its mark.
    Returns the pose (a copy if it had to change)."""
    for _ in range(8):
        over = [v[1] - v[2] for v in cast.solve(pose, kind)['violations'] if 'reach' in v[0]]
        if not over:
            break
        pose = dict(pose)
        pose['dy'] = pose.get('dy', 0.0) + max(over) + 0.4
    return pose


def footfalls(kind, x0, x1, phase=0.0, stride_k=1.0):
    """[(x of her middle when the hoof lands, leg, hoof x), ...] for walk_pose() between x0 and x1 (px)."""
    R = cast.Rig.of(kind)
    sc = S * R.size
    stride = R.stride * stride_k
    d0, d1 = x0 / sc + phase * stride, x1 / sc + phase * stride
    out = []
    for name in cast.LEGS:
        fore = name[1] == 'f'
        rest = (R.PIN['fore'][0] + (2 if name[0] == 'n' else cast.FAR_DX + 2)) if fore else \
               (R.PIN['hind'][0] - (4 if name[0] == 'n' else -cast.FAR_DX + 4))
        n = math.floor(d0 / stride - cast.OFFSET[name]) - 1
        while True:
            d = (n + cast.OFFSET[name]) * stride
            if d > d1:
                break
            if d >= d0:
                down = d + rest + stride * cast.DUTY / 2
                out.append(((d - phase * stride) * sc, name, (down - phase * stride) * sc))
            n += 1
    return sorted(out)


def travel(t, t0, x0, legs):
    """Where a walker is at time t: starts from x0 at t0 and follows `legs` = [(until_time, speed px/s), ...]
    with a 0.35 s ease between speeds (and from rest)."""
    if t <= t0:
        return x0
    x, tp, vp = x0, t0, 0.0
    for until, v in legs:
        te = min(t, until)
        if te > tp:
            tau = te - tp
            ramp_t = 0.35
            if tau < ramp_t:                       # easing from vp to v
                x += vp * tau + (v - vp) * (tau * tau / (2 * ramp_t))
            else:
                x += vp * ramp_t + (v - vp) * ramp_t / 2 + v * (tau - ramp_t)
        if t <= until:
            return x
        tp, vp = until, v
    return x


# ----------------------------------------------------------------- the sheet ---

X = ExposureSheet()
X.level('lead', [
    ('walk_in', 0), ('halt', 8), ('want', 13, True), ('hoof_up', 17), ('hoof_on', 21, True), ('hoof_off', 25),
    ('lean', 28), ('strain', 31), ('put_back', 34), ('regard', 40, True), ('turn_back', 41), ('call', 43),
    ('wait', 50, True), ('turn_front', 66), ('look_gate', 68, True), ('look_along', 73), ('choose', 76, True),
    ('step_off', 81), ('go_round', 84)])
X.level('calf', [('graze', 0, True), ('hears', 45), ('comes', 48), ('arrives', 66), ('looks_up', 69, True),
                 ('step_off', 87), ('follows', 89)])
X.level('herd', [('graze', 0, True), ('heads_up', 58), ('step_off', 62), ('follow', 65)])
X.level('gate', [('still', 0), ('sags', 21), ('lifts', 25), ('swings', 29), ('on_chain', 31), ('springs', 34), ('still_again', 47)])

LEAD_SPEED = 76.0
CALF_K = 1.5                # the calf's stride, lengthened: fewer, longer steps
CALF_X0, CALF_X1 = 130.0, X_BACK - 105.0
HERD_X0 = (4.0, -160.0)
HERD_PHASE = (0.37, 0.81)

# ---- the lead's poses (cow units; + lowers the nose end; hooves are 'ik' targets on the floor)
_P = cast.POSES
BAR_U = (GX0 - X_GATE) / S          # the gate's distance ahead of her, in cow units, when she stands at X_GATE
WANT = cast.with_(_P['look_up'], dx=5.0, neck=-27.0, head=12.0, ear=34.0, eye=1.3, tail=(8.0, 12.0, 10.0))
HOOF_RISE = cast.with_(_P['stand'], dx=1.0, pitch=-2.5, neck=-6.0, head=30.0, ear=12.0, nf=('ik', 84.0, -50.0))
HOOF_ON = cast.with_(_P['stand'], dx=7.0, pitch=-5.0, dy=-1.0, neck=-16.0, head=24.0, ear=24.0, eye=1.2,
                     nf=('ik', BAR_U - 3.0, -(GATE_BARS[1] + 1.5) / S), tail=(14.0, 16.0, 6.0))
HOOF_TEST = cast.with_(HOOF_ON, dx=11.0, pitch=-6.5, neck=-22.0, head=30.0)
STAND_NEAR = cast.with_(_P['stand'], neck=-8.0, head=14.0, ear=10.0)
LEAN = cast.with_(_P['stand'], dx=19.0, dy=3.0, pitch=3.5, shoulder=5.0, neck=-20.0, head=4.0, ear=-26.0, eye=0.7,
                  tail=(34.0, 22.0, -8.0))        # chest to the bars, head out over the top one, in clear light
STRAIN = cast.with_(LEAN, dx=25.0, dy=5.0, pitch=5.0, neck=-13.0, head=12.0, ear=-40.0, eye=0.45, tail=(52.0, 30.0, -20.0))
_BACK_U = (X_GATE - X_BACK) / S     # one pace back
PUT_BACK = cast.with_(_P['startle'], dx=-10.0, dy=8.0, pitch=-7.0, neck=-46.0, head=-4.0, ear=46.0, eye=1.8, jaw=5.0,
                      nf=_P['stand']['nf'], ff=_P['stand']['ff'], nh=_P['stand']['nh'], fh=_P['stand']['fh'])     # braced on the same four marks
REGARD = cast.with_(_P['stand'], dy=1.0, neck=-18.0, head=16.0, ear=22.0, eye=1.2, tail=(4.0, 6.0, 8.0))
BACKWARD = cast.with_(_P['stand'], dy=1.0, pitch=-1.0, neck=-44.0, head=2.0, ear=20.0, eye=1.2)
CALL = cast.with_(BACKWARD, neck=-54.0, head=-14.0, jaw=22.0, ear=-10.0, tail=(18.0, 10.0, 0.0))
WAIT = cast.with_(BACKWARD, neck=-40.0, head=6.0, ear=30.0)
WAIT_DOWN = cast.with_(BACKWARD, neck=-30.0, head=16.0, ear=34.0)       # her look follows the calf in
STILL_WANTS = cast.with_(_P['stand'], dx=4.0, dy=1.0, neck=-31.0, head=9.0, ear=36.0, eye=1.3, tail=(6.0, 10.0, 10.0))
ALONG = cast.with_(_P['stand'], dy=2.0, pitch=2.0, neck=36.0, head=26.0, ear=30.0, eye=1.3, tail=(6.0, 10.0, 10.0))
ALONG_FAR = cast.with_(ALONG, dx=3.0, neck=31.0, head=18.0, ear=38.0)      # her nose stays clear of the hinge post


def _tk(level, name, frac=0.0):
    d0, d1 = X.at(level, name)
    return X.time(d0) + frac * (X.time(d1) - X.time(d0))


def _lead_acts():
    """The standing performance as two cast.Act timelines: at the gate (held at X_GATE), and after the gate
    has put her back a pace (held at X_BACK). The Acts also swing the bell as a pendulum."""
    a = cast.Act([
        (_tk('lead', 'want'), WANT), (_tk('lead', 'hoof_up'), WANT),
        (_tk('lead', 'hoof_up', 0.55), HOOF_RISE, 'slow'), (_tk('lead', 'hoof_on'), HOOF_ON, 'out'),
        (_tk('lead', 'hoof_on', 0.5), HOOF_TEST, 'slow'), (_tk('lead', 'hoof_off'), HOOF_TEST),
        (_tk('lead', 'hoof_off', 0.45), HOOF_RISE, 'out'), (_tk('lead', 'lean'), STAND_NEAR, 'inout'),
        (_tk('lead', 'strain'), LEAN, 'slow'), (_tk('lead', 'put_back'), STRAIN, 'slow'),
    ])
    b = cast.Act([
        (_tk('lead', 'regard'), REGARD), (_tk('lead', 'turn_back'), REGARD),
        (_tk('lead', 'call'), BACKWARD, 'out'), (_tk('lead', 'call', 0.3), CALL, 'out'), (_tk('lead', 'call', 0.85), CALL),
        (_tk('lead', 'wait'), WAIT, 'inout'), (_tk('calf', 'comes', 0.3), WAIT),
        (_tk('calf', 'arrives'), WAIT_DOWN, 'inout'), (_tk('lead', 'turn_front'), WAIT_DOWN),
        (_tk('lead', 'look_gate'), REGARD, 'out'), (_tk('lead', 'look_gate', 0.4), STILL_WANTS, 'out'),
        (_tk('lead', 'look_along'), STILL_WANTS),                          # once more over the gate: she still wants it
        (_tk('lead', 'choose'), ALONG, 'slow'), (_tk('lead', 'choose', 0.5), ALONG_FAR, 'inout'),
        (_tk('lead', 'step_off'), ALONG_FAR),                              # and then down, along the fence, to where it ends
    ])
    return a, b


class Study:
    """Everything that is decided once: the floor, the gate, the Acts, and every footfall."""

    def __init__(self):
        self.floor = ContactPlane(ROUTE)
        self.flat = lambda x: Y0
        self.gate = new_gate()
        self.act_a, self.act_b = _lead_acts()
        self._swing, self._sag = {}, {}
        for d in range(X.n):
            self._gate_at(d)
        self.steps = []              # (time, x, who, leg) for the sound
        self._schedule()

    # ---- the gate's two joints, driven by what she does to it
    def _gate_at(self, d):
        t = X.time(d)
        on0, on1 = X.at('lead', 'hoof_on')
        sw0, _ = X.at('gate', 'swings')
        ch0, ch1 = X.at('gate', 'on_chain')
        sp0, _ = X.at('gate', 'springs')
        sag, swing = 0.0, 0.0
        if on0 <= d < on1:
            sag = (2.0, 3.4, 2.4, 3.4)[min(3, d - on0)]             # her weight comes on, and she tests it
            swing = (1.2, 0.0, 0.8, 0.0)[min(3, d - on0)]
        elif on1 <= d < on1 + 3:
            swing = (-1.6, 1.0, -0.4)[d - on1]                        # let go: it shivers
        if sw0 <= d < ch0:
            swing = lerp(3.0, 13.5, (d - sw0 + 1) / (ch0 - sw0))      # her chest takes it round to the chain
        elif ch0 <= d < ch1:
            swing = (13.0, 11.0, 13.0)[min(2, d - ch0)]               # on the chain: she shoves again
        elif d >= sp0:
            tau = (d - sp0) / 12.0
            swing = 12.0 * math.exp(-2.6 * tau) * math.cos(2 * math.pi * 2.3 * tau + 0.35)   # it comes back at her
            if abs(swing) < 0.25:
                swing = 0.0
        self._swing[d] = self.gate['hinge'].set(swing, t)
        self._sag[d] = self.gate['sag'].set(sag, t)

    def gate_at(self, d):
        return self._swing[d], self._sag[d]

    # ---- where everyone is
    def lead_x(self, t):
        t0 = _tk('lead', 'go_round')
        return travel(t, t0, X_BACK, [(99.0, LEAD_SPEED)])

    def calf_x(self, t):
        c0, c1 = _tk('calf', 'comes'), _tk('calf', 'arrives')
        if t < _tk('calf', 'follows'):
            v = (CALF_X1 - CALF_X0) / (c1 - c0 - 0.35)
            return min(CALF_X1, travel(t, c0, CALF_X0, [(c1 - 0.2, v), (99.0, 0.0)]))
        return travel(t, _tk('calf', 'follows'), CALF_X1, [(99.0, LEAD_SPEED * 0.99)])

    def herd_x(self, i, t):
        t0 = _tk('herd', 'follow') + 0.25 * i
        return travel(t, t0, HERD_X0[i], [(_tk('calf', 'follows') + 0.4, 46.0), (99.0, 74.0)])

    def _schedule(self):
        """Every footfall of every walk, with its time: for the worn path and for the sound."""
        fl = self.floor

        def lay(who, kind, xf, x0, x1, t0, t1, phase, k, strength, radius, ground):
            falls = footfalls(kind, x0, x1, phase, k)
            ts = np.arange(t0, t1 + 0.02, 1 / 48.0)
            xs = np.array([xf(tt) for tt in ts])
            for xm, leg, hx in falls:
                i = int(np.searchsorted(xs, xm))
                if i >= len(ts) or xs[-1] < xm:
                    continue
                tt = float(ts[i])
                self.steps.append((tt, hx, who, leg))
                if ground is fl.y and hx > X_BACK:
                    fl.tread(tt, hx, strength, radius)

        g0 = _tk('lead', 'go_round')
        lay('lead', 'lead', lambda t: X_GATE - 56.0 * (_tk('lead', 'halt') - t) if t < _tk('lead', 'halt') else X_GATE,
            X_GATE - 60, X_GATE - 1, 0.0, _tk('lead', 'halt'), 0.0, 1.0, 0, 0, self.flat)
        lay('lead', 'lead', self.lead_x, X_BACK + 1, 1100, g0, SECONDS, 0.0, 1.0, 0.34, 4.2, fl.y)
        lay('calf', 'calf', self.calf_x, CALF_X0 + 1, CALF_X1 - 1, _tk('calf', 'comes'), _tk('calf', 'arrives'), 0.2, CALF_K, 0, 0, self.flat)
        lay('calf', 'calf', self.calf_x, CALF_X1 + 1, 1100, _tk('calf', 'follows'), SECONDS, 0.2, CALF_K, 0.2, 2.8, fl.y)
        for i in (0, 1):
            lay('herd', 'herd', lambda t, i=i: self.herd_x(i, t), HERD_X0[i] + 1, 1100, _tk('herd', 'follow'), SECONDS,
                HERD_PHASE[i], 1.0, 0.34, 4.2, fl.y)
        x_off = X_BACK + 8.0
        fl.passes = [(self.lead_x, x_off, 0.36), (self.calf_x, x_off, 0.2),
                     (lambda t: self.herd_x(0, t), x_off, 0.3), (lambda t: self.herd_x(1, t), x_off, 0.3)]
        self.steps.sort()

    # ---- the puppets' state at a drawing: (kind, pose, x, y, profile)
    def lead(self, d):
        t = X.time(d)
        c = X.cell('lead', d)
        fl = self.floor
        if c.name == 'walk_in':
            x = X_GATE - 56.0 * (_tk('lead', 'halt') - t)
            look = smooth((d - 2) / 6.0)                               # her head comes up as the gate nears
            pose, y = walk_pose('lead', x, self.flat, over=None)
            pose['neck'] = lerp(pose['neck'], -20.0, look)
            pose['ear'] = lerp(pose['ear'], 28.0, look)
            return ('lead', pose, x, y, 'front')
        if c.name == 'halt':
            pw, y = walk_pose('lead', X_GATE, self.flat)
            pw['neck'], pw['ear'] = -20.0, 28.0
            return ('lead', step_blend(pw, WANT, (d - c.d0 + 1) / (c.d1 - c.d0)), X_GATE, Y0, 'front')
        if d < X.at('lead', 'put_back')[0]:
            return ('lead', self.act_a.pose(t), X_GATE, Y0, 'front')
        if c.name == 'put_back':                                       # thrown back, then a pace back, held at X_BACK
            u = (d - c.d0 + 1) / (c.d1 - c.d0)
            p0 = shift_pose(self.act_a.pose(_tk('lead', 'put_back')), _BACK_U)
            if u <= 0.4:
                return ('lead', cast.tween(p0, shift_pose(PUT_BACK, _BACK_U), u / 0.4, 'out'), X_BACK, Y0, 'front')
            return ('lead', step_blend(shift_pose(PUT_BACK, _BACK_U), REGARD, (u - 0.4) / 0.6, order=('nf', 'nh', 'ff', 'fh')),
                    X_BACK, Y0, 'front')
        if d < X.at('lead', 'step_off')[0]:
            prof = 'front'
            tb0, _ = X.at('lead', 'turn_back')
            tf0, tf1 = X.at('lead', 'turn_front')
            if d == tb0 or d == tf0:
                prof = 'toward'
            elif tb0 < d < tf0:
                prof = 'back'
            pose = self.act_b.pose(t)
            w0, w1 = X.at('lead', 'wait')
            k = d - (w0 + 7)                                           # one switch of the tail while she waits
            if 0 <= k < 5:
                sw = (26.0, 58.0, 30.0, -14.0, 4.0)[k]
                pose['tail'] = (pose['tail'][0] + sw * 0.5, pose['tail'][1] + sw, pose['tail'][2] + sw * 1.3)
            return ('lead', pose, X_BACK, Y0, prof)
        if c.name == 'step_off':
            pw, y = walk_pose('lead', X_BACK, fl.y)
            return ('lead', step_blend(self.act_b.pose(_tk('lead', 'step_off')), pw, (d - c.d0 + 1) / (c.d1 - c.d0 + 1),
                                       order=('nf', 'nh', 'ff', 'fh')), X_BACK, fl.y(X_BACK), 'front')
        x = self.lead_x(t)
        pose, y = walk_pose('lead', x, fl.y)
        return ('lead', pose, x, y, 'front')

    def calf(self, d):
        t = X.time(d)
        c = X.cell('calf', d)
        fl = self.floor
        graze = cast.with_(_P['graze'], ear=4.0)
        up = cast.with_(_P['look_up'], neck=-34.0, ear=40.0, nf=graze['nf'], ff=graze['ff'])     # head up, hooves where they were
        at_her = cast.with_(_P['look_up'], neck=-44.0, head=-6.0, ear=30.0, tail=(30.0, 20.0, 0.0))
        if c.name == 'graze':
            nib = 3.0 * math.sin(d * 0.9)                              # it is eating: the only thing it moves
            return ('calf', cast.with_(graze, jaw=6.0 + nib, head=graze['head'] + (2.0 if d % 7 < 3 else 0.0)), CALF_X0, Y0, 'front')
        if c.name == 'hears':
            return ('calf', cast.tween(graze, up, (d - c.d0 + 1) / (c.d1 - c.d0), 'out'), CALF_X0, Y0, 'front')
        if c.name == 'comes':
            x = self.calf_x(t)
            pw, y = walk_pose('calf', x, self.flat, phase=0.2, stride_k=CALF_K, lift=1.25)
            u = (d - c.d0 + 1) / 3.0
            if u < 1:
                return ('calf', step_blend(up, pw, u, kind='calf', lift=9.0), x, y, 'front')
            return ('calf', pw, x, y, 'front')
        if c.name == 'arrives':
            pw, y = walk_pose('calf', CALF_X1, self.flat, phase=0.2, stride_k=CALF_K)
            return ('calf', step_blend(pw, at_her, (d - c.d0 + 1) / (c.d1 - c.d0), lift=8.0), CALF_X1, Y0, 'front')
        if c.name == 'looks_up':
            wag = (0.0, 26.0, -8.0, 22.0, 0.0)[min(4, max(0, d - c.d0))]
            p = cast.with_(at_her, tail=(30.0 + wag, 20.0 + wag, wag))
            # when she looks along the fence, so does the calf
            la = X.at('lead', 'look_along')[0] + 3
            if d >= la:
                p = cast.tween(p, cast.with_(_P['look_up'], neck=-10.0, head=10.0, ear=34.0), (d - la + 1) / 3.0, 'inout')
            return ('calf', p, CALF_X1, Y0, 'front')
        if c.name == 'step_off':
            pw, y = walk_pose('calf', CALF_X1, fl.y, phase=0.2, stride_k=CALF_K)
            p = cast.with_(_P['look_up'], neck=-10.0, head=10.0, ear=34.0)
            return ('calf', step_blend(p, pw, (d - c.d0 + 1) / (c.d1 - c.d0 + 1), lift=8.0), CALF_X1, Y0, 'front')
        x = self.calf_x(t)
        pose, y = walk_pose('calf', x, fl.y, phase=0.2, stride_k=CALF_K, lift=1.15)
        return ('calf', pose, x, y, 'front')

    def herd(self, i, d):
        t = X.time(d)
        fl = self.floor
        dd = d - 3 * i                                               # the second one does everything a beat later
        c = X.cell('herd', max(0, dd))
        graze = cast.with_(_P['graze'], jaw=6.0 + 3.0 * math.sin(d * 0.8 + i))
        up = cast.with_(_P['look_up'], neck=-24.0, ear=36.0, nf=graze['nf'], ff=graze['ff'])
        x0 = HERD_X0[i]
        if c.name == 'graze':
            return ('herd', graze, x0, Y0, 'front')
        if c.name == 'heads_up':
            return ('herd', cast.tween(cast.with_(_P['graze']), up, (dd - c.d0 + 1) / (c.d1 - c.d0), 'out'), x0, Y0, 'front')
        if c.name == 'step_off':
            pw, y = walk_pose('herd', x0, fl.y, phase=HERD_PHASE[i])
            return ('herd', step_blend(up, pw, (dd - c.d0 + 1) / (c.d1 - c.d0 + 1)), x0, Y0, 'front')
        x = self.herd_x(i, t)
        pose, y = walk_pose('herd', x, fl.y, phase=HERD_PHASE[i], carry=6.0)
        return ('herd', pose, x, y, 'front')

    def cast_at(self, d):
        out = []
        for kind, pose, x, y, prof in (self.herd(1, d), self.herd(0, d), self.calf(d), self.lead(d)):
            out.append((kind, reach_fix(pose, kind), x, y, prof))
        return out

    # ---- one drawing
    def drawing(self, d, measure=None):
        """Drawing number d (0 .. X.n-1) as an RGB image. `measure` (a dict) is filled with anchors and
        masks for the checks."""
        t = X.time(d)
        img = lay_tissue(backlit_stage(), self.floor.wear(t))
        swing, sag = self.gate_at(d)
        # planes first (the whole fence is the 'mid' plane, behind every actor), then depth within a plane
        items = [(sh.depth - 1000.0, 0, sh) for sh in gate_shapes(swing, sag)]
        for who in self.cast_at(d):
            kind, pose, x, y, prof = who
            if x < -130 or x > W + 130:
                continue
            items.append(((y - Y0) / FORE, 1, who))
        items.sort(key=lambda it: (it[0], it[1]))
        for _depth, is_cow, it in items:
            if is_cow:
                kind, pose, x, y, prof = it
                a = place_cow(img, pose, x, y, kind, prof)
                if measure is not None:
                    measure.setdefault('cows', []).append((kind, x, y, a))
            else:
                draw_shape(img, it)
        foreground(img)
        return img


_STUDY = None


def study():
    """The one Study (built on first use)."""
    global _STUDY
    if _STUDY is None:
        _STUDY = Study()
    return _STUDY


# ----------------------------------------------------------------- sound ---

def low(mix, at, f0=150.0, seconds=0.9, gain=0.16, pan=0.0, fall=0.82):
    """A cow's call, built from a buzz through two formants: rises a little, then falls to `fall` of its
    pitch. f0 150 = the cow; f0 430, seconds 0.35 = the calf's answer."""
    t = mix.t(seconds)
    u = t / seconds
    f = f0 * (0.9 + 0.22 * np.sin(np.pi * np.clip(u * 1.6, 0, 1)) ** 2) * (1 - (1 - fall) * u ** 2)
    ph = 2 * np.pi * np.cumsum(f) / mix.rate
    buzz = sum(np.sin(k * ph) / k for k in range(1, 24))
    y = mix.band(buzz, f0 * 1.6, f0 * 3.4) + 0.6 * mix.band(buzz, f0 * 5.5, f0 * 8.5) + 0.35 * mix.band(buzz, 0, f0 * 1.5)
    y *= mix.env(len(y), 0.12, 0.05, 0.9, 0.3)
    mix.add(y / (np.abs(y).max() + 1e-9), at, gain, pan)


def gate_clack(mix, at, gain=0.3, pan=0.0, chain=True):
    """Wood against its stop, and (chain=True) the chain shaking after it."""
    mix.thud(at, freq=170, gain=gain, pan=pan, seconds=0.16)
    mix.click(at, gain=gain * 0.9, pan=pan, bright=2600, seconds=0.04)
    if chain:
        for k, dt in enumerate((0.05, 0.10, 0.17, 0.26)):
            mix.click(at + dt, gain=gain * 0.45 * (0.8 ** k), pan=pan, bright=7000, seconds=0.02)


def hoof(mix, at, x, who='lead', gain=1.0):
    """One hoof on turf: a low soft knock, lighter and higher for the calf, panned by screen x."""
    pan = clamp((x - W / 2) / (W / 2), -0.8, 0.8)
    if who == 'calf':
        mix.thud(at, freq=150, gain=0.05 * gain, pan=pan, seconds=0.08)
        mix.step(at, gain=0.035 * gain, pan=pan, surface='wood')
    else:
        mix.thud(at, freq=84, gain=0.11 * gain, pan=pan, seconds=0.16)
        mix.step(at, gain=0.05 * gain, pan=pan, surface='stone')


def sound(mix):
    st = study()
    pan_gate = clamp((GX0 - W / 2) / (W / 2), -1, 1)
    mix.wind(0.0, SECONDS, gain=0.045)
    for tt, hx, who, leg in st.steps:
        hoof(mix, tt, hx, who, gain=0.8 if who == 'herd' else 1.0)
    # her hoof on the bar, and off it
    mix.step(_tk('lead', 'hoof_on'), gain=0.16, pan=pan_gate, surface='wood')
    mix.click(_tk('lead', 'hoof_on') + 1 / 12, gain=0.08, pan=pan_gate, bright=6000, seconds=0.02)
    mix.click(_tk('lead', 'hoof_on') + 3 / 12, gain=0.08, pan=pan_gate, bright=6000, seconds=0.02)
    mix.click(_tk('lead', 'hoof_off'), gain=0.10, pan=pan_gate, bright=5000, seconds=0.03)
    hoof(mix, _tk('lead', 'lean') - 1 / 12, X_GATE + 35, 'lead')
    # the gate reaching its stops (taken from the hinge joint's own record)
    for when, stop in st.gate['hinge'].hits:
        gate_clack(mix, when, gain=0.34 if stop == 'hi' else 0.26, pan=pan_gate, chain=True)
    # the pace back
    for k in range(4):
        hoof(mix, _tk('lead', 'put_back', 0.4) + k * 0.07, X_BACK, 'lead', gain=1.1)
    # the bell: only when her head changes direction (the Acts' pendulum says when)
    last = -9.0
    for hit in sorted(st.act_a.bell_hits + st.act_b.bell_hits):
        if hit - last > 0.16 and hit < _tk('lead', 'step_off'):
            mix.bell(hit, freq=1180, seconds=0.5, gain=0.06, pan=-0.25)
            last = hit
    # she calls; the calf answers
    low(mix, _tk('lead', 'call', 0.2), f0=150, seconds=0.85, gain=0.17, pan=-0.3)
    low(mix, _tk('calf', 'hears', 0.5), f0=430, seconds=0.32, gain=0.09, pan=-0.8, fall=0.9)
    mix.bell(_tk('lead', 'go_round') + 0.1, freq=1180, seconds=0.6, gain=0.07, pan=-0.2)
    mix.reverb(0.12, 0.8)


# ----------------------------------------------------------------- film ---

_last = {}


def frame(t, ink):
    d = X.drawing(ink.i)
    if _last.get('d') != d:
        _last['d'], _last['img'] = d, study().drawing(d)
    ink.img.paste(_last['img'], (0, 0))
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    ink.vignette(0.22)


def build():
    film = Film(SLUG, seconds=SECONDS, boil=0)
    film.poster_at = _tk('lead', 'wait', 0.6)
    film.picture(frame)
    film.sound(sound)
    return film


# ----------------------------------------------------------------- looking, and measuring ---

def two_tone(img, cut=112):
    """The silhouette read test: every pixel black or white ("relationships read with all colour removed")."""
    return img.convert('L').point(lambda v: 255 if v > cut else 0).convert('RGB')


def contact_sheet(path, times=None, bw=False, cols=4, scale=0.5):
    """16 stills (or `times`, seconds) on one sheet, each stamped with its time and drawing number.
    The stamps are on the sheet only, never in the film."""
    st = study()
    times = times or [SECONDS * (i + 0.5) / 16 for i in range(16)]
    w, h = int(W * scale), int(H * scale)
    rows = (len(times) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w, rows * h), (20, 16, 14))
    for i, t in enumerate(times):
        d = X.drawing(int(t * 24))
        im = st.drawing(d)
        if bw:
            im = two_tone(im)
        im = im.resize((w, h), Image.LANCZOS)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 96, 13], fill=(255, 255, 255))
        dr.text((3, 1), f'{t:5.2f}s  d{d}', fill=(0, 0, 0))
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(path)
    return path


def check(verbose=True):
    """The MEASURED invariants (raises AssertionError on failure). Returns the numbers."""
    st = study()
    out = {}
    # 1. joint limits: the gate's hinge and sag never leave their limits; every puppet, every drawing, no clamp
    sw = [st.gate_at(d)[0] for d in range(X.n)]
    sg = [st.gate_at(d)[1] for d in range(X.n)]
    assert GATE_SWING.lo <= min(sw) and max(sw) <= GATE_SWING.hi
    assert GATE_SAG.lo <= min(sg) and max(sg) <= GATE_SAG.hi
    out['gate_swing_range'] = (round(min(sw), 2), round(max(sw), 2))
    out['gate_stops_hit'] = [(round(t, 2), s) for t, s in st.gate['hinge'].hits]
    viol, overlap, blobs = [], 0, []
    track = {}
    through = []
    for d in range(X.n):
        m = {}
        st.drawing(d, m)
        cows = m.get('cows', [])
        for kind, x, y, a in cows:
            if a['violations']:
                viol.append((d, kind, a['violations']))
        # 2. shadows of different animals never merge: overlapping pixels between any two animals
        for i in range(len(cows)):
            for j in range(i + 1, len(cows)):
                (ma, (ax, ay)), (mb, (bx, by)) = cows[i][3]['mask_box'], cows[j][3]['mask_box']
                x0, y0 = max(ax, bx), max(ay, by)
                x1, y1 = min(ax + ma.size[0], bx + mb.size[0]), min(ay + ma.size[1], by + mb.size[1])
                if x1 > x0 and y1 > y0:
                    A = np.asarray(ma.crop((x0 - ax, y0 - ay, x1 - ax, y1 - ay)), np.float32) / 255
                    B = np.asarray(mb.crop((x0 - bx, y0 - by, x1 - bx, y1 - by)), np.float32) / 255
                    n = float((A * B).sum())
                    if n > 0.5:
                        overlap = max(overlap, n)
                        blobs.append((d, cows[i][0], cows[j][0], round(n)))
        # 3. nobody walks through the fence: on the fence's depths, the animal's chest is on the near side
        for kind, x, y, a in cows:
            gz = (y - Y0) / FORE
            chest = a['hooves']['ff'][0] + 8.0                       # the front of her standing fore leg (the near one may be on the bar)
            rump = a['hooves']['nh'][0] - 8.0
            if FENCE_GZ[0] <= gz <= FENCE_GZ[1]:
                fence_x = GX0 + SKEW * gz
                if rump < fence_x < chest:
                    through.append((d, kind, round(chest - fence_x, 1)))
        for idx, (kind, x, y, a) in enumerate(cows):
            track.setdefault((kind, idx), []).append((d, x, a['hooves']))
    assert not viol, viol[:5]
    out['puppet_limit_violations'] = 0
    out['max_overlap_px_between_animals'] = round(overlap)
    out['overlap_events'] = blobs[:8]
    out['through_fence'] = through[:8]
    assert not through, through[:5]
    # 4. the point of support stays put: a hoof that is on the ground in two successive drawings has not moved
    drift = 0.0
    planted = 0
    for key, rows in track.items():
        for (d0, x0, h0), (d1, x1, h1) in zip(rows, rows[1:]):
            if d1 != d0 + 1:
                continue
            for leg in cast.LEGS:
                (ax, ay), (bx, by) = h0[leg], h1[leg]
                on_a = abs(ay - st.floor.y(ax)) < 0.8 or abs(ay - Y0) < 0.8
                on_b = abs(by - st.floor.y(bx)) < 0.8 or abs(by - Y0) < 0.8
                if on_a and on_b and abs(bx - ax) < 6.0:               # a 6 px move in 1/12 s is a step, not a slide
                    drift = max(drift, abs(bx - ax))
                    planted += 1
    out['planted_hoof_drift_px_max'] = round(drift, 2)
    out['planted_hoof_samples'] = planted
    # 5. exposure: no more than 12 different drawings in any second
    out['drawings'] = X.n
    out['drawings_per_second'] = X.fps / X.on
    assert X.fps / X.on == 12
    if verbose:
        for k, v in out.items():
            print(f'{k}: {v}')
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--check':
        check()
    elif args and args[0] == '--xsheet':
        print(X.text())
    elif args and args[0] == '--sheet':
        rest = [a for a in args[2:] if a != '--bw']
        times = None
        if len(rest) == 2:
            t0, t1 = float(rest[0]), float(rest[1])
            times = [t0 + (t1 - t0) * i / 15 for i in range(16)]
        print(contact_sheet(args[1], times, bw='--bw' in args))
    else:
        build().render()
