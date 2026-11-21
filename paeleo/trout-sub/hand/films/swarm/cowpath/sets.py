"""sets.py: the sets of "Don't Pave the Cow Paths". Three kits of pieces, one per material.

    ACT 1  shadow theatre   backlight(), hills(), water(), paved_path(), tree(), stump(), boulder(), bog(),
                            house(), town(), fence(), steam_roller(), hand_roller(), cart(), foreground(),
                            stage_back() / stage_front() (the whole stage in the right order), handover()
    ACT 2  pencil on paper  every piece is a list of Stroke polylines: desk_lines(), stool_lines(),
                            board_lines(), pegbar_lines(), sheet_lines(), lamp_lines(), stack_lines(),
                            tray_lines(), stamp_lines(), pad_lines(), hoofprint_lines(), clock_lines(),
                            pot_lines(), lever_lines(), floor_lines(); desk_layout() says where each sits,
                            desk_set() draws them all, pencil() is the one renderer (it can draw a list ON)
    ORCHARD (pencil)        stump_lines(), ground_with_stump(), knife_lines(), shaving_lines(), shoot_lines(),
                            binding_path() / binding_lines(), leaf_contour() / leaf_lines(), leaf_sites(),
                            graft_set()
    line tools              Stroke, resample(), upto(), polylen(), morph(), morph_lines(), transform(), hatch()

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))      # films/swarm/cowpath
    import sets

Units are screen pixels at 960x540 unless a function says otherwise; y is down; angles are degrees.
Every function draws onto the kit's Ink and takes the film time `t` where anything moves by itself, and a
0..1 progress where something is done TO it. Nothing here keeps state: the same arguments give the same
picture. `python3 films/swarm/cowpath/sets.py` writes stills of every piece to films/stills/cowpath_sets/.
SETS.md lists every function with an example call.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import PAPER, W, H, FPS, clamp, lerp, smooth, ease  # noqa: E402

BLACK = (20, 16, 14)            # the card of the shadow theatre (same as cast.BLACK)
GRAPHITE = (58, 56, 60)         # the pencil of act 2 (same as cast.GRAPHITE)
LIGHT = (255, 238, 186)         # light let straight through: kerb hairs, lit windows

# =========================================================================== line tools ===


class Stroke(list):
    """A polyline: a plain list of (x, y), plus how the pencil should treat it.

    w     relative line weight (1 = a contour, 0.5 = hatching)
    tone  relative darkness (1 = full graphite)
    fill  True: a closed shape that hides what is behind it (filled with paper before it is drawn)"""

    def __init__(self, pts=(), w=1.0, tone=1.0, fill=False):
        super().__init__((float(p[0]), float(p[1])) for p in pts)
        self.w, self.tone, self.fill = w, tone, fill

    def like(self, pts):
        return Stroke(pts, self.w, self.tone, self.fill)


def _S(pts, w=1.0, tone=1.0, fill=False, close=False):
    pts = list(pts)
    if close or fill:
        pts = pts + [pts[0]]
    return Stroke(pts, w, tone, fill)


def polylen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def resample(pts, n):
    """n points evenly spaced by arc length along a polyline (first and last kept)."""
    pts = [tuple(p) for p in pts]
    if len(pts) == 1 or n <= 1:
        return [pts[0]] * max(1, n)
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    if total <= 1e-9:
        return [pts[0]] * n
    out, k, acc = [], 0, 0.0
    for i in range(n):
        d = total * i / (n - 1)
        while k < len(seg) - 1 and acc + seg[k] < d:
            acc += seg[k]
            k += 1
        f = clamp((d - acc) / seg[k]) if seg[k] > 0 else 0.0
        a, b = pts[k], pts[k + 1]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def upto(pts, u):
    """The first fraction u (by length) of a polyline."""
    u = clamp(u)
    if u >= 1:
        return list(pts)
    target, acc, out = polylen(pts) * u, 0.0, [tuple(pts[0])]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + d >= target:
            f = (target - acc) / d if d > 0 else 0
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            return out
        out.append(tuple(b))
        acc += d
    return out


def morph(a, b, u, n=None):
    """One polyline turning into another, point for point. Both are resampled to n points (default: the
    longer one's count, at least 48) and blended. u=0 is a, u=1 is b. Returns a Stroke."""
    n = n or max(len(a), len(b), 48)
    pa, pb = resample(a, n), resample(b, n)
    st = Stroke([(lerp(p[0], q[0], u), lerp(p[1], q[1], u)) for p, q in zip(pa, pb)])
    sa = a if isinstance(a, Stroke) else Stroke(a)
    sb = b if isinstance(b, Stroke) else Stroke(b)
    st.w, st.tone = lerp(sa.w, sb.w, u), lerp(sa.tone, sb.tone, u)
    st.fill = sa.fill if u < 0.5 else sb.fill
    return st


def morph_lines(A, B, u, n=64):
    """Two lists of strokes, paired in order. Where one list is longer, its extra strokes grow out of (or
    shrink into) the last point of the other list's last stroke."""
    out = []
    for k in range(max(len(A), len(B))):
        a = A[k] if k < len(A) else [A[-1][-1]] * 2
        b = B[k] if k < len(B) else [B[-1][-1]] * 2
        out.append(morph(a, b, u, n))
    return out


def transform(lines, dx=0.0, dy=0.0, s=1.0, angle=0.0, about=(0.0, 0.0)):
    """Scale and turn strokes about a point, then shift them. Takes one Stroke or a list."""
    single = isinstance(lines, Stroke) or (len(lines) > 0 and isinstance(lines[0][0], (int, float)))
    L = [lines] if single else lines
    c, sn = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    out = []
    for st in L:
        pts = [(about[0] + ((x - about[0]) * c - (y - about[1]) * sn) * s + dx,
                about[1] + ((x - about[0]) * sn + (y - about[1]) * c) * s + dy) for x, y in st]
        out.append(st.like(pts) if isinstance(st, Stroke) else Stroke(pts))
    return out[0] if single else out


def hatch(poly, gap=5.0, angle=45.0, w=0.55, tone=0.5, seed=0, ragged=0.25):
    """Pencil hatching inside a polygon, as strokes (so it can be drawn on and transformed like any line)."""
    c, sn = math.cos(math.radians(-angle)), math.sin(math.radians(-angle))
    rp = [(x * c - y * sn, x * sn + y * c) for x, y in poly]
    if rp[0] != rp[-1]:
        rp.append(rp[0])
    y0, y1 = min(p[1] for p in rp), max(p[1] for p in rp)
    rng = random.Random(seed * 131 + 7)
    out, y, flip = [], y0 + gap * 0.5, False
    while y < y1:
        xs = []
        for (ax, ay), (bx, by) in zip(rp, rp[1:]):
            if (ay <= y < by) or (by <= y < ay):
                xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            if b - a < 1.5:
                continue
            a += rng.uniform(0, ragged) * min(gap * 2, (b - a) * 0.3)
            b -= rng.uniform(0, ragged) * min(gap * 2, (b - a) * 0.3)
            seg = [(a, y), (b, y + rng.uniform(-0.4, 0.4))]
            if flip:
                seg.reverse()
            out.append(Stroke([(px * c + py * sn, -px * sn + py * c) for px, py in seg], w, tone))
        y += gap * rng.uniform(0.85, 1.15)
        flip = not flip
    return out


def catmull(pts, per=12):
    """A smooth open curve through the points (uniform Catmull-Rom), `per` points per span."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            u = k / per
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def _ell(cx, cy, rx, ry, a0=0.0, a1=360.0, n=28, rot=0.0):
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for k in range(n + 1):
        a = math.radians(lerp(a0, a1, k / n))
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * c - y * sn, cy + x * sn + y * c))
    return out


# ------------------------------------------------------------------ the pencil ---

_tooth = None


def _paper_tooth():
    """The tooth of the paper: what makes a graphite line break up. One fixed sheet."""
    global _tooth
    if _tooth is None:
        rs = np.random.RandomState(5)
        a = rs.uniform(0, 1, (H, W)).astype(np.float32)
        b = np.asarray(Image.fromarray((rs.uniform(0, 1, (H // 2, W // 2)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                       np.float32) / 255
        _tooth = np.clip(0.62 + 0.38 * (0.55 * a + 0.45 * b) * 1.5, 0.5, 1.0)
    return _tooth


def pencil(ink, lines, progress=1.0, color=GRAPHITE, width=1.7, alpha=1.0, boil=6, wob=0.7, seed=0, paper=PAPER,
           fills=True, grain=True):
    """Draw strokes in graphite. THE renderer for act 2 and the orchard.

    lines     a Stroke or a list of Strokes (plain point lists work too)
    progress  0..1: the list is drawn ON in order, by length; 1 = all of it. A filled shape's paper comes in
              as its own contour is drawn.
    boil      redraws per second (the line is re-wobbled that often); 0 = dead still
    wob       how far the hand wanders off true, px
    Returns the point the pencil is at (the end of what has been drawn), or None if nothing is drawn."""
    if not lines:
        return None
    if isinstance(lines, Stroke) or isinstance(lines[0][0], (int, float)):
        lines = [lines]
    lines = [st for st in lines if len(st) >= 2]
    if not lines or progress <= 0 or alpha <= 0:
        return None
    lens = [max(polylen(st), 1e-6) for st in lines]
    target = clamp(progress) * sum(lens)
    step = int(ink.i * boil / FPS) if boil else 0
    xs = [p[0] for st in lines for p in st]
    ys = [p[1] for st in lines for p in st]
    pad = 6
    x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
    x1, y1 = min(ink.w, int(max(xs)) + pad + 1), min(ink.h, int(max(ys)) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    SS = 2
    lay = Image.new('RGBA', ((x1 - x0) * SS, (y1 - y0) * SS), tuple(color[:3]) + (0,))
    d = ImageDraw.Draw(lay)
    acc, tip = 0.0, None
    pcol = tuple(paper[:3])
    for k, (st, ln) in enumerate(zip(lines, lens)):
        if acc >= target:
            break
        f = min(1.0, (target - acc) / ln)
        acc += ln
        w_, tone, fill = getattr(st, 'w', 1.0), getattr(st, 'tone', 1.0), getattr(st, 'fill', False)
        rng = random.Random((seed * 977 + k) * 7919 + step)
        ph = [rng.uniform(0, 6.283) for _ in range(4)]
        n = max(2, int(ln / 3.0) + 1)
        pts = resample(st, n)
        amp = wob * min(1.0, ln / 30.0)
        wp = []
        for i, (x, y) in enumerate(pts):
            sarc = ln * i / (n - 1)
            ox = amp * (math.sin(sarc * 0.045 + ph[0]) + 0.5 * math.sin(sarc * 0.13 + ph[1])) / 1.5
            oy = amp * (math.sin(sarc * 0.05 + ph[2]) + 0.5 * math.sin(sarc * 0.11 + ph[3])) / 1.5
            wp.append(((x + ox - x0) * SS, (y + oy - y0) * SS))
        if fill and fills and len(wp) >= 3:
            d.polygon(wp, fill=pcol + (int(255 * smooth(f)),))
        m = max(2, int(round((n - 1) * f)) + 1)
        cut = wp[:m]
        lw = max(1, int(round(SS * width * w_)))
        a_base = 255 * alpha * tone
        chunk = 7
        for c0 in range(0, len(cut) - 1, chunk):
            seg = cut[c0:c0 + chunk + 1]
            press = 0.82 + 0.18 * math.sin(c0 * 0.9 + ph[0] * 3)
            d.line(seg, fill=tuple(color[:3]) + (int(clamp(a_base * press, 0, 255)),), width=lw, joint='curve')
        tip = (cut[-1][0] / SS + x0, cut[-1][1] / SS + y0)
    lay = lay.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    if grain:
        arr = np.asarray(lay, np.float32).copy()
        dark = arr[..., :3].sum(-1) < 420
        tooth = _paper_tooth()[y0:y1, x0:x1]
        arr[..., 3] = np.where(dark, arr[..., 3] * tooth, arr[..., 3])
        lay = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
    ink.img.paste(lay, (x0, y0), lay)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    return tip


def paper_ground(ink, t=0.0, color=PAPER, warm=0.0):
    """The sheet act 2 is drawn on: cream, a shade deeper toward the corners. `warm` 0..1 leans it back
    toward the amber of act 1 (for the first frames after the hand-over)."""
    yy, xx = _grid()
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    base = np.array(color, np.float32)[None, None, :] * (1 - 0.05 * np.clip(r - 0.5, 0, None))[..., None]
    if warm > 0:
        base = base * (1 - warm) + backlight_array(1.0) * warm
    _put(ink, base)
    ink._grain = True


# =========================================================================== ACT 1 · the shadow stage ===

# The crooked path. Control points are the board's; PATH is the smooth curve every act uses.
PATH_PTS = [(120, 170), (240, 214), (292, 246), (330, 284), (374, 290), (410, 278),
            (452, 290), (486, 292), (520, 296), (556, 318), (596, 352),
            (640, 368), (680, 384), (698, 410), (678, 436), (646, 428), (642, 400),
            (668, 380), (716, 382), (770, 420), (840, 455)]
PATH = catmull(PATH_PTS, 10)                     # 201 points, crest to water, with the sag, the bulge, the loop
STRAIGHT = [(120, 170), (840, 455)]              # where she first aimed
PATH_LEN = polylen(PATH)

TREE = (331.0, 253.0)        # the foot of the tree (and of the stump after it)
BOULDER = (500.0, 329.0)     # the middle of the boulder
BOG = (718.0, 409.0)         # the middle of the bog
WATER_EDGE = (840.0, 455.0)  # where the path meets the water
FAR_GRASS = (936.0, 452.0)   # the root of the tuft on the far bank: what she wants
LAMP = (604.0, 84.0)         # where the lamp stands behind the screen when it is fully up
CREST = (120.0, 170.0)

RIDGE = [(-20, 206), (40, 181), (120, 168), (200, 172), (300, 190), (420, 214), (560, 250), (700, 300),
         (820, 345), (900, 372), (980, 392)]                      # the top edge of the hill sheet
FAR1 = [(-20, 330), (120, 290), (250, 235), (330, 205), (420, 176), (520, 150), (610, 136), (700, 142), (800, 168), (880, 200), (980, 222)]
FAR2 = [(-20, 150), (60, 128), (150, 118), (250, 132), (360, 160), (470, 150), (560, 120), (680, 96), (790, 104),
        (900, 132), (980, 150)]
NEAR_BANK = [(980, 384), (916, 400), (872, 424), (848, 452), (836, 488), (830, 560)]
FAR_BANK = [(980, 420), (942, 434), (917, 458), (906, 494), (903, 560)]
FOOT = [(-20, 414), (60, 424), (150, 442), (240, 468), (320, 498), (390, 526), (440, 560)]   # black card, lower left

# The stump, in set pixels at s=1, origin under its middle on the ground: left root flare, the flat cut,
# right root flare. 46 wide. Act 2 draws this same profile in line (stump_lines).
STUMP_PROFILE = [(-20, 0), (-16.5, -1.6), (-13.4, -5.5), (-11.8, -11), (-11.2, -17), (-11, -22),
                 (11, -22), (11.3, -17), (12, -11), (14, -5.5), (18.5, -1.8), (26, 0)]
STUMP_H = 22.0
STUMP_CUT = ((-11.0, -22.0), (11.0, -22.0))      # the two ends of the flat cut

T_FAR2 = (0.95, 0.88, 0.77)      # how much light each tissue lets through, r g b
T_FAR1 = (0.88, 0.77, 0.60)
T_BANK = (0.80, 0.64, 0.43)
T_HILL = (0.69, 0.50, 0.30)

_grid_cache = None


def _grid():
    global _grid_cache
    if _grid_cache is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        _grid_cache = (yy, xx)
    return _grid_cache


def _put(ink, arr):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
    ink.img.paste(im, (0, 0))
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


def _get(ink):
    return np.asarray(ink.img.convert('RGB'), np.float32).copy()


def path_at(u):
    """Where the path is at fraction u of its length: (x, y, heading in degrees, 0 = due right, + = downhill)."""
    u = clamp(u)
    target, acc = PATH_LEN * u, 0.0
    for a, b in zip(PATH, PATH[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + d >= target or b is PATH[-1]:
            f = clamp((target - acc) / d) if d > 0 else 0
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])))
        acc += d
    return PATH[-1] + (0.0,)


def path_u(x, y):
    """The fraction of the path nearest to a screen point (use it to turn a walker's place into `worn=`)."""
    best, bu, acc = 1e18, 0.0, 0.0
    for a, b in zip(PATH, PATH[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        f = clamp(((x - a[0]) * (b[0] - a[0]) + (y - a[1]) * (b[1] - a[1])) / (d * d)) if d > 0 else 0
        px, py = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        dd = (px - x) ** 2 + (py - y) ** 2
        if dd < best:
            best, bu = dd, (acc + d * f) / PATH_LEN
        acc += d
    return bu


def path_stroke(u=1.0):
    """The path as a pencil Stroke (the first line of act 2 is exactly this)."""
    return Stroke(upto(PATH, u), w=1.75, tone=1.0)


def ridge_y(x):
    """Height of the hill's top edge at x."""
    for a, b in zip(RIDGE, RIDGE[1:]):
        if a[0] <= x <= b[0]:
            return lerp(a[1], b[1], (x - a[0]) / (b[0] - a[0]))
    return RIDGE[-1][1]


# ------------------------------------------------------------------ light and tissue ---

_bl_cache = {}


def backlight_array(lamp=1.0, lamp_xy=LAMP, white=0.0):
    """The lit screen as a float array (H, W, 3). See backlight()."""
    key = (round(lamp, 4), round(lamp_xy[0], 1), round(lamp_xy[1], 1), round(white, 4))
    if _bl_cache.get('key') == key:
        return _bl_cache['arr'].copy()
    yy, xx = _grid()
    u = (yy / H)[..., None]
    base = np.array((250, 214, 142), np.float32) * (1 - u) + np.array((228, 150, 76), np.float32) * u
    lx, ly = lamp_xy
    r2 = ((xx - lx) / 340.0) ** 2 + ((yy - ly) / 250.0) ** 2
    glow = np.exp(-r2 * 1.5)[..., None]
    base = base + (np.array((255, 240, 200), np.float32) - base) * 0.62 * glow
    base = base * (0.80 + 0.20 * np.exp(-r2 * 0.30))[..., None]
    rr = np.hypot(xx - lx, yy - ly)
    core = np.clip((30.0 - rr) / 2.5, 0, 1)[..., None]
    halo = np.clip(1 - rr / 78.0, 0, 1)[..., None] ** 2
    base = base + (np.array((255, 252, 236), np.float32) - base) * np.clip(0.5 * halo + core, 0, 1)
    lv = clamp(lamp)
    base = base * (np.array((0.05 + 0.95 * lv, 0.03 + 0.97 * lv ** 1.25, 0.02 + 0.98 * lv ** 1.7), np.float32))
    if white > 0:
        base = base * (1 - white) + np.array(PAPER, np.float32) * white
    _bl_cache['key'], _bl_cache['arr'] = key, base
    return base.copy()


def backlight(ink, t=0.0, lamp=1.0, lamp_xy=LAMP, white=0.0):
    """The sky of the shadow theatre: a paper screen lit from behind, amber, with the lamp itself showing as
    a pale disc (it is the sun). lamp 0..1 is how far it is turned up (0 = black); lamp_xy is where it
    stands (bring it up from below the hill); white 0..1 whitens the screen to the cream paper of act 2."""
    _put(ink, backlight_array(lamp, lamp_xy, white))
    ink._grain = True


_masks = {}


def _mask(name):
    """A tissue sheet's shape as a float array 0..1, cut once and kept."""
    if name in _masks:
        return _masks[name]
    SS = 2
    im = Image.new('L', (W * SS, H * SS), 0)
    d = ImageDraw.Draw(im)

    def P(pts):
        return [(x * SS, y * SS) for x, y in pts]
    if name == 'hill':
        d.polygon(P(catmull(RIDGE, 8) + [(980, 560), (-20, 560)]), fill=255)
        d.polygon(P(catmull(NEAR_BANK, 8) + [(980, 560), (980, 384)]), fill=0)
    elif name == 'bank':
        d.polygon(P(catmull(FAR_BANK, 8) + [(980, 560), (980, 420)]), fill=255)
    elif name == 'far1':
        d.polygon(P(catmull(FAR1, 8) + [(980, 560), (-20, 560)]), fill=255)
    elif name == 'far2':
        d.polygon(P(catmull(FAR2, 8) + [(980, 560), (-20, 560)]), fill=255)
    elif name == 'water':
        d.polygon(P(catmull(NEAR_BANK, 8) + catmull(FAR_BANK, 8)[::-1]), fill=255)
    elif name == 'bog':
        d.polygon(P(_ell(BOG[0], BOG[1], 19, 7.5, rot=10) + []), fill=255)
    im = im.resize((W, H), Image.LANCZOS)
    if name == 'bog':
        im = im.filter(ImageFilter.GaussianBlur(1.6))
    m = np.asarray(im, np.float32) / 255.0
    _masks[name] = m
    return m


_fibre = None


def _tissue_fibre():
    """Tissue is not even: long soft fibres and a faint mottle, fixed in the sheet."""
    global _fibre
    if _fibre is None:
        rs = np.random.RandomState(23)
        a = Image.fromarray((rs.uniform(0, 255, (H // 3, W // 12))).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        b = Image.fromarray((rs.uniform(0, 255, (H // 14, W // 14))).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        f = (np.asarray(a, np.float32) / 255 - 0.5) * 0.7 + (np.asarray(b, np.float32) / 255 - 0.5) * 1.3
        _fibre = f
    return _fibre


def _rim(m):
    """A darker hair just inside a cut edge, where the tissue is doubled over its frame."""
    im = Image.fromarray((m * 255).astype(np.uint8))
    inner = np.asarray(im.filter(ImageFilter.MinFilter(5)), np.float32) / 255.0
    return np.clip(m - inner, 0, 1)


def worn_mask(worn=1.0, width=9.0, prints=(), start=0.0):
    """Where the tissue is worn thin, 0..1: the path from fraction `start` to `worn` as a soft band, plus
    hoof prints [(x, y) or (x, y, heading_deg), ...] as small cloven marks."""
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    if worn > start:
        n0, n1 = int(start * (len(PATH) - 1)), None
        pts = upto(PATH, worn)[n0:n1]
        if len(pts) >= 2:
            wd = max(1, int(round(width)))
            d.line(pts, fill=255, width=wd, joint='curve')
            r = wd / 2
            for x, y in (pts[0], pts[-1]):
                d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for p in prints:
        x, y = p[0], p[1]
        a = math.radians(p[2]) if len(p) > 2 else 0.4
        c, sn = math.cos(a), math.sin(a)
        for side in (-1, 1):
            cx, cy = x - sn * side * 1.5, y + c * side * 1.5
            pts = [(cx + c * ex - sn * ey, cy + sn * ex + c * ey) for ex, ey in ((-2.8, -1.1 * side), (2.4, -1.2 * side), (3.2, 0.4 * side), (-2.6, 0.9 * side))]
            d.polygon(pts, fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(0.9)), np.float32) / 255.0


def hills(ink, t=0.0, lamp=1.0, lamp_xy=LAMP, white=0.0, worn=0.0, wear=1.0, worn_width=9.0, prints=(), bog=1.0,
          sheets=1.0, worn_start=0.0):
    """Backlight plus every tissue plane: two far hills, the far bank, and THE hill, whose worn places let the
    light through. This is the whole ground of act 1 in one call.

    worn        0..1: how far down the path the wear has reached (crest = 0, water = 1)
    wear        0..1: how thin the tissue is worn there (0.35 = a faint track, 1 = bright cut)
    worn_width  px; the board's band is 9
    prints      hoof prints [(x, y[, heading_deg]), ...]: small bright cloven marks (before the track joins up)
    bog         1 = the bog is there (a doubled, darker patch with a sliver of standing water), 0 = filled in
    sheets      1 = tissue as normal; toward 0 every sheet thins away (leaves the bare screen)"""
    a = backlight_array(lamp, lamp_xy, white)
    fib = _tissue_fibre()
    wm = worn_mask(worn, worn_width, prints, worn_start) * clamp(wear) if (worn > 0 or prints) else None
    for name, tint, fk in (('far2', T_FAR2, 0.5), ('far1', T_FAR1, 0.8), ('bank', T_BANK, 1.0), ('hill', T_HILL, 1.0)):
        if ('dens', name) not in _masks:
            m = _mask(name)
            dens = m * (1.0 + 0.085 * fk * fib) + 0.16 * _rim(m)
            if name in ('far1', 'far2'):
                dens = dens * (1 - _mask('hill')) * (1 - _mask('bank'))    # the near sheets are dense enough to hide them
            if name == 'far2':
                dens = dens * (1 - 0.8 * _mask('far1'))
            _masks[('dens', name)] = dens
        dens = _masks[('dens', name)]
        if name == 'hill':
            if bog > 0:
                bm = _mask('bog')
                dens = dens + 0.55 * bog * bm
            if wm is not None:
                dens = dens * (1 - 0.93 * wm)
        dens = np.clip(dens * sheets, 0, 1.6)[..., None]
        a = a * (1 - dens * (1 - np.array(tint, np.float32)))
        a = np.clip(a, 0, 255)
    lv = clamp(lamp)
    lit = np.array(LIGHT, np.float32) * np.array((0.05 + 0.95 * lv, 0.03 + 0.97 * lv ** 1.25, 0.02 + 0.98 * lv ** 1.7), np.float32)
    lit = lit * (1 - white) + np.array(PAPER, np.float32) * white
    if wm is not None:                                                    # worn tissue glows: the lamp is right behind it
        a = a + (lit - a) * (0.62 * wm * _mask('hill') * sheets)[..., None]
    a = a + (lit - a) * (0.78 * _mask('water') * sheets)[..., None]       # nothing at all between us and the lamp here
    _put(ink, a)
    ink._grain = True


# ------------------------------------------------------------------ black card ---

class Card:
    """Black card cut with scissors: collect shapes in screen pixels, then paste them, antialiased.
    hole() cuts light back through whatever has been added so far."""

    def __init__(self, ss=3):
        self.ops, self.ss = [], ss

    def poly(self, pts, fill=BLACK, alpha=255):
        if len(pts) >= 3:
            self.ops.append(('p', [(float(x), float(y)) for x, y in pts], tuple(fill[:3]) + (int(alpha),)))
        return self

    def disc(self, c, r, fill=BLACK, alpha=255):
        return self.poly(_ell(c[0], c[1], r, r, n=max(14, int(r * 1.6))), fill, alpha)

    def line(self, pts, width=2.0, fill=BLACK, alpha=255):
        if len(pts) >= 2:
            self.ops.append(('l', [(float(x), float(y)) for x, y in pts], tuple(fill[:3]) + (int(alpha),), float(width)))
        return self

    def hole(self, pts):
        return self.poly(pts, (0, 0, 0), 0)

    def hole_disc(self, c, r):
        return self.disc(c, r, (0, 0, 0), 0)

    def paste(self, ink, alpha=1.0):
        if not self.ops or alpha <= 0:
            return
        xs = [p[0] for op in self.ops for p in op[1]]
        ys = [p[1] for op in self.ops for p in op[1]]
        pad = 6
        x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
        x1, y1 = min(ink.w, int(max(xs)) + pad + 1), min(ink.h, int(max(ys)) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            return
        S = self.ss
        im = Image.new('RGBA', ((x1 - x0) * S, (y1 - y0) * S), BLACK + (0,))
        d = ImageDraw.Draw(im)
        for op in self.ops:
            pts = [((x - x0) * S, (y - y0) * S) for x, y in op[1]]
            col = op[2] if op[2][3] > 0 else BLACK + (0,)
            if op[0] == 'p':
                d.polygon(pts, fill=col)
            else:
                wd = max(1, int(round(op[3] * S)))
                d.line(pts, fill=col, width=wd, joint='curve')
                r = wd / 2
                for x, y in (pts[0], pts[-1]):
                    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        im = im.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        if alpha < 1:
            im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
        ink.img.paste(im, (x0, y0), im)
        ink.d = ImageDraw.Draw(ink.img, 'RGBA')


def _tf(pts, x, y, s=1.0, ang=0.0, flip=1, pivot=(0.0, 0.0)):
    """Local card units -> screen: turn by ang about `pivot` (local), scale, mirror, move to (x, y)."""
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    for px, py in pts:
        dx, dy = px - pivot[0], py - pivot[1]
        rx, ry = pivot[0] + dx * c - dy * sn, pivot[1] + dx * sn + dy * c
        out.append((x + flip * s * rx, y + s * ry))
    return out


def _blade(card, x, y, h, lean, w=2.4, bend=0.5, fill=BLACK):
    """One blade of grass or a reed: rooted at (x, y), h tall, its tip `lean` px to the side."""
    L, R = [], []
    n = 7
    for k in range(n + 1):
        u = k / n
        cx, cy = x + lean * (u ** (1 + bend)), y - h * u
        hw = w * 0.5 * (1 - u) ** 0.8
        L.append((cx - hw, cy))
        R.append((cx + hw, cy))
    card.poly(L + R[::-1], fill)


def _tuft(card, x, y, n, h, spread, t=0.0, seed=0, w=2.4, heads=0):
    rng = random.Random(seed)
    for k in range(n):
        f = (k + 0.5) / n - 0.5
        hh = h * rng.uniform(0.55, 1.0) * (1 - 0.5 * abs(f))
        sway = 0.06 * hh * math.sin(t * 1.3 + k * 1.7 + seed)
        lean = f * spread * rng.uniform(0.7, 1.3) + sway
        bx = x + f * spread * 0.45
        _blade(card, bx, y + rng.uniform(0, 2), hh, lean, w * rng.uniform(0.8, 1.2), rng.uniform(0.3, 0.9))
        if heads and k % max(1, n // heads) == 0:
            tx, ty = bx + lean, y - hh
            card.poly(_ell(tx, ty + 3, 1.7, 5.5, n=10, rot=math.degrees(math.atan2(lean, hh)) * 0.7))


def water(ink, t=0.0, lamp=1.0, calm=0.0):
    """The bright strip at lower right: bare screen with dark ripples sliding on it, reeds on the near bank,
    and on the far bank the tall grass she wants (FAR_GRASS), which leans in the air. calm 1 stills the ripples."""
    c = Card()
    near, far = catmull(NEAR_BANK, 8), catmull(FAR_BANK, 8)
    rng = random.Random(41)
    for k in range(22):
        v = (k + rng.random()) / 22
        i = int(lerp(3, len(near) - 5, v))
        a, b = near[i], far[min(len(far) - 1, i)]
        ph = (t * (0.07 + 0.05 * rng.random()) * (1 - calm) + rng.random()) % 1.0
        u = lerp(0.12, 0.88, rng.random())
        mx, my = lerp(a[0], b[0], u), lerp(a[1], b[1], u) + 10 * ph             # they slide down the frame: it flows toward us
        half = (b[0] - a[0]) * rng.uniform(0.07, 0.17) * (0.5 + 0.5 * math.sin(math.pi * ph))
        if half > 1.5:
            c.line([(mx - half, my + 0.9), (mx - half * 0.3, my - 0.7), (mx + half * 0.4, my + 0.5), (mx + half, my - 0.4)], 1.2,
                   (88, 56, 28), int(215 * math.sin(math.pi * ph)))
    for k in range(2):                                                          # a ring where the path meets the water
        ph = (t * 0.45 + k * 0.5) % 1.0
        c.line(_ell(WATER_EDGE[0] + 22, WATER_EDGE[1] + 8, 4 + 13 * ph, 1.4 + 4 * ph, 200, 520, n=20), 1.0, (88, 56, 28), int(170 * (1 - ph) * (1 - calm)))
    for k, (bx, by, n, hh) in enumerate(((852, 448, 5, 30), (840, 478, 6, 24), (866, 430, 4, 20), (834, 512, 5, 22))):
        _tuft(c, bx, by + 2, n, hh, 16, t, seed=60 + k, w=2.2, heads=2 if k < 2 else 0)
    _tuft(c, FAR_GRASS[0], FAR_GRASS[1], 15, 84, 60, t, seed=7, w=3.6, heads=5)
    _tuft(c, FAR_GRASS[0] - 8, FAR_GRASS[1] + 22, 9, 50, 38, t, seed=9, w=3.0, heads=3)
    _tuft(c, FAR_GRASS[0] - 20, FAR_GRASS[1] + 52, 7, 34, 28, t, seed=11, w=2.6, heads=2)
    c.paste(ink)


def paved_path(ink, paved=1.0, width=9.0, lamp=1.0, kerb=1.0, joints=1.0, color=BLACK, start=0.0, alpha=1.0):
    """Black setts laid over the light from the crest down to fraction `paved` of the path: a black band with
    a hair of light left on each kerb and faint joints across it.

    kerb    0..1 brightness of the two hairs of light (they are what keeps the band readable on black)
    joints  0..1 the joints between setts; set 0 as the band thins to a line in the hand-over
    width   px (9 = the board's band; 3 = the graphite line it ends as)"""
    if paved <= start:
        return None
    n0 = int(start * (len(PATH) - 1))
    pts = upto(PATH, paved)[n0:]
    if len(pts) < 2:
        return None
    if kerb > 0 and lamp > 0:
        k = Card(ss=2)
        k.line(pts, width + 3.2, tuple(int(v * (0.25 + 0.75 * lamp)) for v in LIGHT), int(255 * clamp(kerb) * alpha))
        k.paste(ink)
    c = Card()
    c.line(pts, width, color, int(255 * alpha))
    if joints > 0 and width >= 5:
        acc, nxt = 0.0, 4.0
        col = tuple(int(v * 0.55 * (0.25 + 0.75 * lamp)) for v in LIGHT)
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            while acc + d >= nxt and d > 0:
                f = (nxt - acc) / d
                x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
                hw = width * 0.36
                odd = int(nxt / 4.0) % 2
                c.line([(x - nx * hw * (1 - odd), y - ny * hw * (1 - odd)), (x + nx * hw * odd, y + ny * hw * odd)], 0.7, col,
                       int(105 * joints * alpha))                         # setts in bond: a joint from one kerb, then the other
                nxt += 4.0
            acc += d
    c.paste(ink)
    return pts[-1]


# ---- the tree, and what is left of it

_CROWN = None


def _tree_upper():
    """The tree above the cut, in local units (origin at the foot, y up is negative): trunk, limbs, crown,
    and the gaps of light in the crown."""
    global _CROWN
    if _CROWN is None:
        trunk = [(-11, -22), (-8.4, -38), (-6.6, -60), (-6.0, -86), (-10, -102), (-22, -116), (-19.5, -118.5), (-5, -108),
                 (-2, -128), (2, -128), (4.4, -106), (19, -117), (21.5, -114.5), (8, -98), (7, -70), (8.6, -42), (11, -22)]
        crown = []
        for (cx, cy, rx, ry, lobes, ph) in ((4, -136, 40, 30, 7, 0.6), (-25, -119, 23, 18, 5, 1.9), (28, -116, 22, 17, 5, 0.2),
                                            (-6, -160, 25, 17, 5, 2.6), (22, -152, 20, 15, 5, 1.1)):
            blob = []
            for k in range(60):
                a = 2 * math.pi * k / 60
                r = 1 + 0.12 * math.sin(lobes * a + ph) + 0.05 * math.sin((2 * lobes + 1) * a + 2 * ph)
                blob.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
            crown.append(blob)
        rng = random.Random(3)
        holes = []
        for cx, cy, rx, ry, rot in ((-13, -124, 7, 3.0, 35), (16, -126, 6.5, 2.8, -40), (2, -142, 5.5, 2.6, 80), (-27, -112, 4.6, 2.2, -20),
                                    (30, -110, 5, 2.4, 25), (12, -160, 4.5, 2.2, -50), (-12, -158, 4.6, 2.2, 40), (-2, -170, 3.4, 1.8, 10),
                                    (26, -146, 4, 2, 60), (-30, -128, 3.6, 1.8, 70), (-8, -108, 3.4, 1.6, 0), (38, -122, 3, 1.6, -30)):
            holes.append(_ell(cx, cy, rx, ry, n=12, rot=rot + rng.uniform(-8, 8)))
        _CROWN = (trunk, crown, holes)
    return _CROWN


def stump(ink, x=TREE[0], y=TREE[1], s=1.0, alpha=1.0):
    """What is left of the tree: black card, one flat cut, two root flares (STUMP_PROFILE). Foot at (x, y)."""
    c = Card()
    c.poly(_tf(STUMP_PROFILE, x, y, s))
    c.paste(ink, alpha)
    return dict(cut=(_tf([STUMP_CUT[0]], x, y, s)[0], _tf([STUMP_CUT[1]], x, y, s)[0]), top=(x, y - STUMP_H * s))


def tree(ink, t=0.0, fall=0.0, x=TREE[0], y=TREE[1], s=1.0, carry=(0.0, 0.0), alpha=1.0, upper=True):
    """The tree: black card, tall, with light through the gaps in its crown. It stands on the stump profile and
    is pinned at the right-hand end of the cut, so it can be felled.

    fall    0 = standing, 1 = lying down the slope to the right (112 degrees over). Ease it yourself.
    carry   (dx, dy): shift the felled part (cart it off)
    upper   False = draw only the stump
    t       the crown breathes a little while it stands
    Returns {'top': crown top, 'tip': where the crown's far end is, 'cut': the stump's cut ends}."""
    a = stump(ink, x, y, s, alpha)
    if not upper:
        return a
    trunk, crown, holes = _tree_upper()
    pivot = (11.0, -22.0)
    ang = 112.0 * clamp(fall) + (1 - clamp(fall * 6)) * 0.8 * math.sin(t * 0.9)
    c = Card()
    ox, oy = x + carry[0], y + carry[1]
    c.poly(_tf(trunk, ox, oy, s, ang, 1, pivot))
    for blob in crown:
        c.poly(_tf(blob, ox, oy, s, ang, 1, pivot))
    for hpts in holes:
        c.hole(_tf(hpts, ox, oy, s, ang, 1, pivot))
    c.poly(_tf([(-1.5, -110), (1.5, -110), (1.0, -172), (-1.0, -172)], ox, oy, s, ang, 1, pivot))       # limbs across the gaps
    c.poly(_tf([(0, -126), (-30, -132), (-30, -134), (0, -129.5)], ox, oy, s, ang, 1, pivot))
    c.poly(_tf([(0, -124), (34, -124), (34, -126), (0, -127.5)], ox, oy, s, ang, 1, pivot))
    c.poly(_tf([(0, -140), (-15, -162), (-13.4, -163), (1.6, -143)], ox, oy, s, ang, 1, pivot))
    c.poly(_tf([(0, -138), (27, -150), (27.6, -148.2), (1, -135)], ox, oy, s, ang, 1, pivot))
    c.paste(ink, alpha)
    a['top'] = _tf([(0, -178)], ox, oy, s, ang, 1, pivot)[0]
    a['tip'] = a['top']
    return a


_BOULDER = [(-23, 10), (-25, 0), (-21, -9), (-12, -15), (-2, -18), (9, -16), (17, -10), (23, -1), (24, 9), (14, 12), (-8, 13)]


def boulder(ink, x=BOULDER[0], y=BOULDER[1], s=1.0, broken=0.0, alpha=1.0):
    """The boulder: a lump of black card with one bright crack. broken 0..1 splits it into three pieces that
    slump apart (cart them off by fading alpha or simply stop drawing it)."""
    b = clamp(broken)
    c = Card()
    if b <= 0:
        c.poly(_tf(_BOULDER, x, y, s))
        c.hole(_tf([(-3, -17.5), (-1.5, -9), (-4, -3), (-3.2, -3), (-0.4, -9), (-1.8, -17.5)], x, y, s))
    else:
        parts = (([(-23, 10), (-25, 0), (-21, -9), (-12, -15), (-4, -17.5), (-2.5, -8), (-6, 12)], (-9, 1.5), -14),
                 ([(-1, -18), (9, -16), (17, -10), (10, -2), (0, -5), (-1.5, -9)], (5, 9), 20),
                 ([(-4, 13), (-1, -3), (10, 0), (18, -8), (23, -1), (24, 9), (14, 12)], (10, 3), 9))
        for pts, (dx, dy), rot in parts:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            c.poly(_tf(pts, x + dx * b * s, y + dy * b * s, s, rot * b, 1, (cx, cy)))
    c.paste(ink, alpha)


def bog(ink, t=0.0, x=BOG[0], y=BOG[1], fill=0.0, alpha=1.0):
    """The reeds round the bog and the sliver of standing water in it. (Its dark doubled tissue is part of
    hills(bog=...).) fill 0..1: as it is filled in, the water closes and the reeds go under."""
    f = clamp(fill)
    c = Card()
    if f < 1:
        c.poly(_ell(x + 1, y + 0.5, 11 * (1 - f), 2.6 * (1 - f), n=18, rot=10), LIGHT, int(235 * (1 - f)))
        for k, (dx, dy, n, hh) in enumerate(((-19, 2, 4, 20), (17, 5, 4, 17), (-6, 8, 3, 12), (8, -6, 3, 15), (-13, -5, 3, 14))):
            _tuft(c, x + dx, y + dy, n, hh * (1 - f), 11, t, seed=20 + k, w=2.0, heads=1 if k < 2 else 0)
    c.paste(ink, alpha)


def foreground(ink, t=0.0, alpha=1.0):
    """The black foot of the hill across the lower left (the title is cut through it), fringed with grass."""
    c = Card()
    pts = catmull(FOOT, 8)
    c.poly(pts + [(440, 560), (-20, 560)])
    for k in range(13):
        i = int(lerp(3, len(pts) - 6, k / 12))
        _tuft(c, pts[i][0], pts[i][1] + 2, 4 + k % 3, 13 + 7 * ((k * 5) % 3), 14, t, seed=80 + k, w=2.2)
    c.paste(ink, alpha)


# ---- the town

HOUSE_KINDS = dict(
    cottage=dict(w=38, h=22, pitch=42, chim=0.26, win=((-9, -12), (9, -12)), door=0),
    tall=dict(w=26, h=38, pitch=52, chim=-0.24, win=((0, -27), (-6, -12)), door=6),
    long=dict(w=56, h=20, pitch=34, chim=0.3, win=((-18, -11), (-4, -11), (18, -11)), door=8),
    barn=dict(w=46, h=26, pitch=30, chim=None, win=((0, -34),), door=0),
)


def house(ink, x, y, s=1.0, rise=1.0, roof=1.0, kind='cottage', facing=1, lit=0.0, lamp=1.0, seed=0, alpha=1.0):
    """One house of black card on pins, base centre at (x, y).

    rise   0..1: the wall card tips up from flat (0 = nothing, 1 = standing)
    roof   0..1: two hinged roof flaps stand up out of the wall top (0..0.4), then fold in to meet at the
           ridge (0.4..1); the chimney pops in the last fifth
    kind   'cottage', 'tall', 'long', 'barn'
    lit    0..1: lamplight in the windows (0 = plain cut holes, the hill shows through)
    Returns {'ridge': (x, y) of the roof top, 'eaves': y of the wall top}."""
    K = HOUSE_KINDS[kind]
    w, h, pitch = K['w'], K['h'] * clamp(rise), K['pitch']
    if rise <= 0:
        return dict(ridge=(x, y), eaves=y)
    r = clamp(roof)
    c = Card()
    c.poly(_tf([(-w / 2, 0), (-w / 2, -h), (w / 2, -h), (w / 2, 0)], x, y, s, 0, facing))
    e = w / 2 + 3
    Lf = e / math.cos(math.radians(pitch))
    grow_, fold = clamp(r / 0.4), smooth(clamp((r - 0.4) / 0.6))        # the flaps stand up out of the wall, then fold in
    a = math.radians(lerp(90.0, pitch, fold))
    Lf = Lf * grow_
    tipL = (-e + Lf * math.cos(a), -h - Lf * math.sin(a))
    tipR = (e - Lf * math.cos(a), -h - Lf * math.sin(a))
    if r > 0:
        c.poly(_tf([(-w / 2, -h), (min(tipL[0], 0), tipL[1]), (max(tipR[0], 0), tipR[1]), (w / 2, -h)], x, y, s, 0, facing))
        for eave, tip in (((-e, -h), tipL), ((e, -h), tipR)):
            c.line(_tf([eave, tip], x, y, s, 0, facing), 3.0 * s)
        ch = K['chim']
        if ch is not None and r > 0.8:
            cx = ch * w
            top_at = -h - (e - abs(cx)) * math.tan(math.radians(pitch)) + 2
            up = 9 * clamp((r - 0.8) / 0.2)
            c.poly(_tf([(cx - 2.6, top_at + 5), (cx - 2.6, top_at - up), (cx + 2.6, top_at - up), (cx + 2.6, top_at + 5)], x, y, s, 0, facing))
            c.poly(_tf([(cx - 3.6, top_at - up), (cx - 3.6, top_at - up - 1.6), (cx + 3.6, top_at - up - 1.6), (cx + 3.6, top_at - up)], x, y, s, 0, facing))
    if rise > 0.92:
        glow = tuple(int(v * (0.25 + 0.75 * lamp)) for v in LIGHT)
        for wx, wy in K['win']:
            if wy < -K['h']:
                if r < 1:
                    continue
            q = _tf([(wx - 2.8, wy - 3.4), (wx + 2.8, wy - 3.4), (wx + 2.8, wy + 3.4), (wx - 2.8, wy + 3.4)], x, y, s, 0, facing)
            c.hole(q)
            if lit > 0:
                c.poly(q, glow, int(255 * clamp(lit)))
            c.line(_tf([(wx, wy - 3.4), (wx, wy + 3.4)], x, y, s, 0, facing), 0.8 * s)
            c.line(_tf([(wx - 2.8, wy), (wx + 2.8, wy)], x, y, s, 0, facing), 0.8 * s)
        dx = K['door']
        if kind == 'barn':
            c.hole(_tf([(-8, 0), (-8, -15), (8, -15), (8, 0)], x, y, s, 0, facing))
            c.line(_tf([(-8, -15), (8, 0)], x, y, s, 0, facing), 1.0 * s)
            c.line(_tf([(8, -15), (-8, 0)], x, y, s, 0, facing), 1.0 * s)
        else:
            c.hole(_tf([(dx - 3, 0), (dx - 3, -9), (dx - 1.5, -11), (dx + 1.5, -11), (dx + 3, -9), (dx + 3, 0)], x, y, s, 0, facing))
    if 0 < r < 1 or (rise < 1):
        for px, py in ((-e, -h), (e, -h)):                                   # the pins show while it is moving
            c.hole_disc(_tf([(px + (2 if px < 0 else -2), py + 1.5)], x, y, s, 0, facing)[0], 1.1 * s)
    c.paste(ink, alpha)
    return dict(ridge=(x, y - s * (h + Lf * math.sin(a))), eaves=y - s * h)


def spire(ink, x, y, s=1.0, rise=1.0, roof=1.0, lit=0.0, lamp=1.0, facing=1, alpha=1.0):
    """The church, base centre at (x, y): a nave, a tower, and the spire, which telescopes up out of the tower
    as `roof` goes 0..1 (it is the last thing the town puts up). Returns {'tip': (x, y)}."""
    rs, r = clamp(rise), clamp(roof)
    if rs <= 0:
        return dict(tip=(x, y))
    c = Card()
    nh, th = 24 * rs, 50 * rs
    c.poly(_tf([(-34, 0), (-34, -nh), (8, -nh), (8, 0)], x, y, s, 0, facing))
    c.poly(_tf([(-37, -nh), (-13, -nh - 17 * r), (11, -nh)], x, y, s, 0, facing))
    c.poly(_tf([(8, 0), (8, -th), (26, -th), (26, 0)], x, y, s, 0, facing))
    sp = 46 * r
    c.poly(_tf([(6, -th), (17, -th - sp), (28, -th)], x, y, s, 0, facing))
    if r > 0.9:
        k = clamp((r - 0.9) / 0.1)
        c.line(_tf([(17, -th - sp), (17, -th - sp - 8 * k)], x, y, s, 0, facing), 1.3 * s)
        c.disc(_tf([(17, -th - sp - 8 * k)], x, y, s, 0, facing)[0], 1.9 * s * k)
    if rs > 0.92:
        glow = tuple(int(v * (0.25 + 0.75 * lamp)) for v in LIGHT)
        for q in ([(13, -34), (13, -42), (17, -46), (21, -42), (21, -34)],
                  [(-27, -6), (-27, -15), (-24, -18), (-21, -15), (-21, -6)], [(-12, -6), (-12, -15), (-9, -18), (-6, -15), (-6, -6)],
                  [(14, 0), (14, -10), (17, -13), (20, -10), (20, 0)]):
            qq = _tf(q, x, y, s, 0, facing)
            c.hole(qq)
            if lit > 0:
                c.poly(qq, glow, int(255 * clamp(lit)))
    c.paste(ink, alpha)
    return dict(tip=_tf([(17, -th - sp - 8)], x, y, s, 0, facing)[0])


def _town_sites():
    """Where the houses stand: along the path from the crest down, always on the OUTSIDE of each detour, so
    the straight way stays empty. (u along the path, side: -1 = uphill of the path, +1 = downhill, kind, s).
    Downhill houses keep their roofs 12 px under the path; uphill houses stand on the brow of the hill (66 to
    90 px above the path), against the sky, so a cow at s=0.55 on the path passes in front of light, not card."""
    spec = [(0.05, 1, 'cottage', 0.86), (0.118, 1, 'tall', 0.84), (0.185, 1, 'long', 0.92), (0.255, 1, 'cottage', 0.98),
            (0.315, 1, 'tall', 0.96), (0.385, -1, 'cottage', 0.9), (0.435, -1, 'long', 0.9), (0.495, -1, 'tall', 0.94),
            (0.545, -1, 'barn', 0.96), (0.60, -1, 'cottage', 0.94), (0.705, 1, 'long', 1.0),
            (0.895, -1, 'tall', 0.98), (0.945, -1, 'cottage', 1.0)]
    out = []
    for k, (u, side, kind, s) in enumerate(spec):
        px, py, hd = path_at(u)
        K = HOUSE_KINDS[kind]
        tall = s * (K['h'] + (K['w'] / 2 + 3) * math.tan(math.radians(K['pitch'])) + 10)
        if side < 0:
            x, y = px, ridge_y(px) + 9                           # on the brow of the hill, a cow's height back from the path
        else:
            x, y = px, py + tall + 12
        out.append(dict(x=round(x, 1), y=round(y, 1), s=s, kind=kind, u=u, side=side, facing=1 if k % 2 else -1, seed=k))
    return out


TOWN = _town_sites()
CHURCH = dict(x=700.0, y=318.0, s=1.0)          # high on the hill above the loop: its spire breaks the skyline


def town(ink, t=0.0, grow=1.0, lit=0.0, lamp=1.0, alpha=1.0, church=True):
    """The whole town, unfolding one house after another from the crest down, the church and its spire last.

    grow  0..1 for the whole row (each house takes about a seventh of it: walls tip up, then the roof lifts),
          OR a list of per-house values 0..1 (len(TOWN) houses, then the church) to time them yourself;
          within one house 0..0.5 is the wall rising and 0.5..1 the roof.
    Returns the list of sites with 'ridge' added (for chimney smoke, birds, etc.)."""
    n = len(TOWN) + 1
    if isinstance(grow, (int, float)):
        g = [clamp((grow * (n + 2.2) - k) / 3.2) for k in range(n)]
    else:
        g = list(grow) + [0.0] * (n - len(grow))
    out = []
    order = sorted(range(len(TOWN)), key=lambda k: TOWN[k]['y'])
    if church and g[-1] > 0:
        spire(ink, CHURCH['x'], CHURCH['y'], CHURCH['s'], rise=_bounce(g[-1] / 0.4), roof=clamp((g[-1] - 0.4) / 0.6), lit=lit, lamp=lamp, alpha=alpha)
    for k in order:
        site = TOWN[k]
        if g[k] <= 0:
            continue
        a = house(ink, site['x'], site['y'], site['s'], rise=_bounce(g[k] / 0.5), roof=clamp((g[k] - 0.5) / 0.5), kind=site['kind'],
                  facing=site['facing'], lit=lit, lamp=lamp, seed=site['seed'], alpha=alpha)
        out.append(dict(site, **a))
    return out


def _bounce(u):
    """0..1 with a small overshoot at the end: a card tipping up and settling."""
    u = clamp(u)
    return 1 + 1.6 * (u - 1) ** 3 + 0.6 * (u - 1) ** 2 if u < 1 else 1.0


def fence(ink, u0=0.20, u1=0.30, side=-1, offset=10.0, s=1.0, post=1.0, rail=1.0, posts=4, alpha=1.0):
    """A fence along the edge of the path, from fraction u0 to u1 of it, shutting the path off from the open
    ground beside it. The default is the stretch round the stump, on the side of the straight way.

    side    -1 = the uphill side of the path, +1 = the downhill side;  offset = px from the path's middle
    post    0..1 pushes the posts up out of the ground, the first (nearest the crest) first
    rail    0..1 runs the two rails out along the posts, from the first post
    Returns the post tops [(x, y), ...] that are up."""
    c = Card()
    feet = []
    for k in range(posts):
        px, py, hd = path_at(lerp(u0, u1, k / max(1, posts - 1)))
        nx, ny = -math.sin(math.radians(hd)), math.cos(math.radians(hd))
        if (ny > 0) != (side > 0):
            nx, ny = -nx, -ny
        feet.append((px + nx * offset, py + ny * offset))
    tops = []
    for k, (bx, by) in enumerate(feet):
        up = clamp(post * (posts * 0.5 + 0.5) - k * 0.5)
        if up <= 0:
            break
        hh = 22 * s * _bounce(up)
        c.poly([(bx - 2.2 * s, by), (bx - 2.2 * s, by - hh), (bx, by - hh - 3 * s), (bx + 2.2 * s, by - hh), (bx + 2.2 * s, by)])
        tops.append((bx, by - hh))
    if rail > 0 and len(feet) >= 2:
        line = upto(feet, clamp(rail))
        for dy in (7, 15):
            c.line([(x, y - dy * s) for x, y in line], 2.2 * s)
    c.paste(ink, alpha)
    return tops


# ---- machines and carts, on pins

def _wheel(c, cx, cy, r, turn, spokes=6, rim=0.2, hub=0.2, s=1.0):
    """A spoked wheel: a disc with the gaps between the spokes cut out, turned by `turn` degrees."""
    c.disc((cx, cy), r)
    r0, r1 = r * (hub + 0.1), r * (1 - rim)
    for k in range(spokes):
        a0 = turn + 360.0 * k / spokes + 180.0 / spokes * 0.36
        a1 = turn + 360.0 * (k + 1) / spokes - 180.0 / spokes * 0.36
        pts = [(cx + r1 * math.cos(math.radians(lerp(a0, a1, j / 6))), cy + r1 * math.sin(math.radians(lerp(a0, a1, j / 6)))) for j in range(7)]
        pts += [(cx + r0 * math.cos(math.radians(lerp(a1, a0, j / 3))), cy + r0 * math.sin(math.radians(lerp(a1, a0, j / 3)))) for j in range(4)]
        c.hole(pts)
    c.hole_disc((cx, cy), max(0.9, r * 0.07))


def steam_roller(ink, x, y, s=1.0, t=0.0, roll=0.0, tilt=0.0, facing=1, smoke=1.0, alpha=1.0, driver=True):
    """The steam roller, black card on pins. (x, y) is the ground under the middle of the machine; it is about
    150 units long and 112 high at s=1.

    roll    px travelled along the ground: the big wheel, the front roll and the flywheel turn by it, so they
            never slide (pass the distance along the path, e.g. sets.PATH_LEN * u)
    tilt    degrees: the lie of the ground (path_at(u)[2])
    smoke   0..1: puffs of grey tissue from the chimney, timed by t
    Returns {'front': where the front roll touches the ground, 'rear': rear wheel contact, 'chimney': its top}."""
    d = roll / max(s, 1e-6)
    R, r = 31.0, 20.0
    rear, front = (-34.0, -R), (50.0, -r)
    c = Card()

    def T(pts):
        return _tf(pts, x, y, s, tilt * facing, facing)
    bob = 0.6 * math.sin(t * 9.0)
    c.poly(T([(-16, -66 + bob), (60, -66 + bob), (66, -60 + bob), (66, -44 + bob), (60, -38 + bob), (-16, -38 + bob)]))          # boiler
    c.poly(T([(-60, -70 + bob), (-14, -70 + bob), (-14, -30), (-60, -30)]))                                                    # firebox and bunker
    c.poly(T([(46, -66 + bob), (45, -96 + bob), (41.5, -104 + bob), (58.5, -104 + bob), (55, -96 + bob), (54, -66 + bob)]))      # chimney
    c.poly(T([(38, -100 + bob), (38, -103 + bob), (62, -103 + bob), (62, -100 + bob)]))
    c.poly(T([(16, -66 + bob), (17, -76 + bob), (27, -76 + bob), (28, -66 + bob)]))                                            # dome
    c.poly(T([(-66, -112 + bob), (30, -112 + bob), (34, -108 + bob), (-70, -108 + bob)]))                                      # canopy
    for px in (-62, -18, 26):
        c.poly(T([(px - 1.1, -108 + bob), (px + 1.1, -108 + bob), (px + 1.1, -66 + bob), (px - 1.1, -66 + bob)]))
    c.poly(T([(58, -62 + bob), (64, -62 + bob), (56, -22), (44, -22)]))                                                        # fork to the front roll
    c.poly(T([(64, -50 + bob), (76, -44), (76, -40), (64, -44 + bob)]))
    if driver:
        c.disc(T([(-36, -92 + bob)])[0], 5.2 * s)
        c.poly(T([(-43, -70 + bob), (-42, -84 + bob), (-36, -88 + bob), (-30, -84 + bob), (-27, -70 + bob)]))
        c.line(T([(-31, -80 + bob), (-20, -74 + bob)]), 2.4 * s)
        c.poly(T([(-43, -96.5 + bob), (-29, -96.5 + bob), (-31, -98.5 + bob), (-33, -101 + bob), (-40, -101 + bob), (-41, -98.5 + bob)]))
    c.line(T([(-20, -74 + bob), (-14, -62 + bob)]), 1.6 * s)                                                                    # steering column
    fw = T([(2, -70 + bob)])[0]
    c2 = Card()
    turn = math.degrees(d / R)
    cr = T([rear])[0]
    _wheel(c2, cr[0], cr[1], R * s, turn * facing + tilt, spokes=8, rim=0.2, hub=0.2)
    cf = T([front])[0]
    c2.disc(cf, r * s)
    tf_ = math.degrees(d / r) * facing + tilt
    for k in range(3):
        a = math.radians(tf_ + 120 * k)
        c2.hole_disc((cf[0] + 11.5 * s * math.cos(a), cf[1] + 11.5 * s * math.sin(a)), 3.0 * s)
    c2.hole_disc(cf, 1.3 * s)
    _wheel(c2, fw[0], fw[1], 11.5 * s, math.degrees(d / 6.0) * facing, spokes=4, rim=0.22, hub=0.24)
    rod_a = math.radians(turn * facing + tilt)                                                                                 # connecting rod
    crank = (cr[0] + 13 * s * math.cos(rod_a), cr[1] + 13 * s * math.sin(rod_a))
    c2.line([crank, T([(30, -52 + bob)])[0]], 1.8 * s)
    top = T([(50, -104 + bob)])[0]
    if smoke > 0:
        puffs = Card(ss=2)
        for k in range(6):
            age = ((t * 1.25 + k / 6.0) % 1.0)
            px = top[0] - facing * (8 + 34 * age) * s + 5 * s * math.sin(age * 5 + k)
            py = top[1] - (10 + 52 * age ** 0.8) * s
            puffs.disc((px, py), (4.5 + 12 * age) * s, (92, 66, 44), int(150 * smoke * (1 - age) ** 1.2))
        puffs.paste(ink, alpha)
    c.paste(ink, alpha)
    c2.paste(ink, alpha)
    return dict(front=T([(50, 0)])[0], rear=T([(-34, 0)])[0], chimney=top, seat=T([(-36, -70)])[0])


def hand_roller(ink, x, y, s=1.0, roll=0.0, tilt=0.0, facing=1, handle=38.0, alpha=1.0):
    """A hand roller: a drum on the ground at (x, y) and a long T handle trailing back and up at `handle`
    degrees. roll = px travelled. Returns {'grip': where the hands go}."""
    c = Card()
    R = 11.0

    def T(pts):
        return _tf(pts, x, y, s, tilt * facing, facing)
    cc = T([(0, -R)])[0]
    c.disc(cc, R * s)
    a0 = math.degrees(roll / max(s, 1e-6) / R) * facing + tilt
    for k in range(3):
        a = math.radians(a0 + 120 * k)
        c.hole_disc((cc[0] + 6 * s * math.cos(a), cc[1] + 6 * s * math.sin(a)), 1.8 * s)
    ha = math.radians(handle)
    grip = (-52 * math.cos(ha), -R - 52 * math.sin(ha))
    c.line(T([(0, -R), grip]), 2.2 * s)
    nx, ny = math.sin(ha), -math.cos(ha)
    c.line(T([(grip[0] - 6 * nx, grip[1] - 6 * ny), (grip[0] + 6 * nx, grip[1] + 6 * ny)]), 2.6 * s)
    c.paste(ink, alpha)
    return dict(grip=T([grip])[0])


def cart(ink, x, y, s=1.0, roll=0.0, tilt=0.0, facing=1, tip=0.0, load=0.0, alpha=1.0):
    """A two-wheeled tip cart, wheel on the ground at (x, y), shafts forward. tip 0..1 tips the bed up at the
    front to shed its load backwards; load 0..1 heaps it (earth, stone, a log's worth). roll = px travelled.
    Returns {'shaft': where it is pulled from, 'tail': where the load falls}."""
    c = Card()
    R = 14.0

    def T(pts, ang=0.0, piv=(0, 0)):
        return _tf(_tf(pts, 0, 0, 1, ang, 1, piv), x, y, s, tilt * facing, facing)
    ang = -34.0 * clamp(tip)
    piv = (-4, -R - 3)
    c.poly(T([(-30, -R - 3), (-34, -R - 20), (30, -R - 20), (26, -R - 3)], ang, piv))
    if load > 0:
        lv = clamp(load) * (1 - 0.8 * clamp(tip))
        c.poly(T([(-32, -R - 19), (-22, -R - 20 - 13 * lv), (-6, -R - 20 - 19 * lv), (10, -R - 20 - 15 * lv), (28, -R - 19)], ang, piv))
    c.line(T([(24, -R - 5), (62, -R - 2)]), 2.2 * s)
    c.line(T([(-2, -R - 3), (-2, -R)]), 3 * s)
    c2 = Card()
    cc = T([(0, -R)])[0]
    _wheel(c2, cc[0], cc[1], R * s, math.degrees(roll / max(s, 1e-6) / R) * facing + tilt, spokes=6, rim=0.22, hub=0.22)
    c.paste(ink, alpha)
    c2.paste(ink, alpha)
    return dict(shaft=T([(62, -R - 2)])[0], tail=T([(-34, -R - 4)], ang, piv)[0])


# ---- the whole stage, in order

def stage_back(ink, t=0.0, lamp=1.0, lamp_xy=LAMP, white=0.0, worn=0.0, wear=1.0, worn_width=9.0, prints=(), paved=0.0,
               tree_fall=0.0, tree_carry=(0.0, 0.0), boulder_broken=0.0, bog_fill=0.0, sheets=1.0, calm=0.0):
    """Everything BEHIND the actors, in the right order: light, tissue hills (with the wear), water and far
    grass, paving, bog, boulder, tree. Then draw the town and the cows, then stage_front().

    tree_fall       0 standing .. 1 lying; None = carted away (only the stump is left)
    boulder_broken  0 whole .. 1 in pieces; None = carted away
    bog_fill        0 = bog, 1 = filled in
    (the rest as in hills() and paved_path())"""
    kerb_extra = 3.2 if paved > 0 else 0.0
    hills(ink, t, lamp, lamp_xy, white, worn=max(worn, 0.0), wear=wear, worn_width=worn_width + 0 * kerb_extra, prints=prints,
          bog=1 - clamp(bog_fill), sheets=sheets)
    water(ink, t, lamp, calm)
    if paved > 0:
        paved_path(ink, paved, worn_width, lamp)
    bog(ink, t, fill=bog_fill)
    if boulder_broken is not None:
        boulder(ink, broken=boulder_broken)
    if tree_fall is None:
        a = stump(ink)
    else:
        a = tree(ink, t, tree_fall, carry=tree_carry)
    return a


def stage_front(ink, t=0.0):
    """Everything IN FRONT of the actors: the black foot of the hill."""
    foreground(ink, t)


def handover(ink, u, width=9.0):
    """The hand-over to act 2, applied AFTER the stage and the actors are drawn. u 0..1:
    0 .. 0.45  everything sinks into black; only the two kerb hairs still show where the band is
    0.45 .. 1  the black whitens to the cream paper while the band stays dark, thins from 9 px to a 3 px line
               and turns from card to graphite. At u=1 the frame is paper_ground() + pencil(path_stroke())."""
    u = clamp(u)
    if u <= 0:
        return
    A, B = smooth(u / 0.45), smooth((u - 0.45) / 0.55)
    arr = _get(ink) * (1 - A)
    arr = arr + (np.array(PAPER, np.float32)[None, None, :] * (1 - 0.05 * np.clip(_r_corner() - 0.5, 0, None))[..., None] - arr) * B
    _put(ink, arr)
    wd = lerp(width, 3.0, B)
    col = tuple(int(lerp(a, b, B)) for a, b in zip(BLACK, GRAPHITE))
    k = clamp(1 - B * 1.6)
    paved_path(ink, 1.0, wd, lamp=1.0, kerb=k * (0.35 + 0.65 * A) if A > 0 else 0, joints=0.0, color=col, alpha=1 - smooth((B - 0.75) / 0.25))
    if B > 0.75:
        pencil(ink, path_stroke(), alpha=smooth((B - 0.75) / 0.25), boil=0, wob=0.0)


def _r_corner():
    yy, xx = _grid()
    return np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))


# =========================================================================== ACT 2 · the desk, in line ===
#
# The desk is drawn three-quarter from the front: x runs along the desk, "depth" goes away from us (up and to
# the right on the page), h is height above the floor. One unit is one pixel at s=1.
# The origin of the desk is the FLOOR UNDER ITS NEAR LEFT CORNER. desk_layout() puts that corner where
# cast.stool_and_desk puts its desk (cow x + 28 s, top 110 s above her floor), so the seated cow's hooves land
# on this desk's front edge.

DEPTH = (0.42, 0.50)     # one unit of depth moves a point this far right and this far up on the page
DESK_W, DESK_D, DESK_H = 330.0, 78.0, 110.0


def _ob(ox, oy, s):
    """The three-quarter projection for a piece whose origin is at (ox, oy)."""
    def P(u, dep=0.0, hh=0.0):
        return (ox + s * (u + DEPTH[0] * dep), oy - s * (hh + DEPTH[1] * dep))
    return P


def desk_lines(x, y, s=1.0, w=DESK_W, d=DESK_D, h=DESK_H, drawer=True):
    """The desk itself. (x, y) = the floor under its near left corner. Returns strokes, back to front."""
    P = _ob(x, y, s)
    L = []
    for u0 in (8, w - 16):                                             # far legs
        L.append(_S([P(u0, d, h - 8), P(u0, d, 0), P(u0 + 8, d, 0), P(u0 + 8, d, h - 8)], 0.9, 0.8))
    L.append(_S([P(16, d, 22), P(w - 16, d, 22)], 0.7, 0.6))           # far stretcher
    L.append(_S([P(w, 0, h - 8), P(w, d, h - 8), P(w, d, h), P(w, 0, h)], 1.0, 1.0, fill=True))     # right edge of the top
    L.append(_S([P(0, 0, h), P(w, 0, h), P(w, d, h), P(0, d, h)], 1.15, 1.0, fill=True))            # the top
    L.append(_S([P(0, 0, h), P(0, 0, h - 8), P(w, 0, h - 8), P(w, 0, h)], 1.1, 1.0, fill=True))     # front edge of the top
    L.append(_S([P(10, 0, h - 8), P(10, 0, h - 30), P(w - 10, 0, h - 30), P(w - 10, 0, h - 8)], 0.9, 0.9, fill=True))  # apron
    if drawer:
        L.append(_S([P(w - 150, 0, h - 12), P(w - 150, 0, h - 27), P(w - 40, 0, h - 27), P(w - 40, 0, h - 12)], 0.7, 0.8, close=True))
        L.append(_S(_ell(*P(w - 95, 0, h - 19.5), 3.2 * s, 3.2 * s, n=12), 0.8, 0.9))
    for u0 in (8, w - 18):                                             # near legs
        L.append(_S([P(u0, 0, h - 30), P(u0, 0, 0), P(u0 + 10, 0, 0), P(u0 + 10, 0, h - 30)], 1.1, 1.0, fill=True))
    L.append(_S([P(18, 0, 24), P(w - 18, 0, 24)], 0.8, 0.8))           # near stretcher
    L.append(_S([P(18, 0, 19), P(w - 18, 0, 19)], 0.8, 0.8))
    L += hatch([P(12, 0, h - 9), P(w - 12, 0, h - 9), P(w - 12, 0, h - 15), P(12, 0, h - 15)], 4.2 * s, 62, 0.5, 0.42, seed=1)   # shadow under the top
    L += hatch([P(w, 2, h - 7.5), P(w, d - 2, h - 7.5), P(w, d - 2, h - 0.5), P(w, 2, h - 0.5)], 3.2 * s, 80, 0.5, 0.5, seed=2)
    return L


def floor_lines(x, y, s=1.0, x0=None, x1=None, w=DESK_W, d=DESK_D):
    """The floor line the desk and stool stand on (broken, as a hand draws it), and the cast shadow under the
    desk. (x, y) as for desk_lines; x0, x1 = how far the line runs (screen x)."""
    P = _ob(x, y, s)
    x0 = x - 330 * s if x0 is None else x0
    x1 = x + (w + 190) * s if x1 is None else x1
    L, rng, cx = [], random.Random(4), x0
    while cx < x1:
        ln = rng.uniform(70, 190) * s
        L.append(Stroke([(cx, y + rng.uniform(-0.6, 0.6)), (min(x1, cx + ln), y + rng.uniform(-0.6, 0.6))], 1.0, 0.9))
        cx += ln + rng.uniform(5, 16) * s
    L += hatch([P(16, 4, 0), P(w - 6, 4, 0), P(w + 4, d + 6, 0), P(26, d + 6, 0)], 6.5 * s, 12, 0.5, 0.36, seed=3)
    return L


def stool_lines(x, y, s=1.0):
    """The stool, placed by THE COW's (x, y, s): the same seat cast.stool_and_desk draws (seat 47 units up,
    centred 52 units behind her origin), in line with a little depth."""
    P = _ob(x - 52 * s, y, s)
    L = []
    for u0, dep in ((-18, 16), (14, 16)):
        L.append(_S([P(u0, dep, 40), P(u0, dep, 0), P(u0 + 4, dep, 0), P(u0 + 4, dep, 40)], 0.8, 0.75))
    L.append(_S([P(-24, 0, 47), P(24, 0, 47), P(24, 20, 47), P(-24, 20, 47)], 1.0, 1.0, fill=True))
    L.append(_S([P(-24, 0, 47), P(-24, 0, 41), P(24, 0, 41), P(24, 0, 47)], 1.0, 1.0, fill=True))
    L.append(_S([P(24, 0, 41), P(24, 20, 41), P(24, 20, 47)], 0.9, 0.9))
    for u0 in (-21, 16):
        L.append(_S([P(u0, 0, 41), P(u0 - 1.5, 0, 0), P(u0 + 3.5, 0, 0), P(u0 + 5, 0, 41)], 1.0, 1.0, fill=True))
    L.append(_S([P(-17, 0, 18), P(17, 0, 18)], 0.8, 0.8))
    L.append(_S([P(-17, 0, 14.5), P(17, 0, 14.5)], 0.8, 0.8))
    return L


def board_lines(x, y, s=1.0, w=128.0, d=64.0, rise=15.0):
    """The drawing board: a shallow wedge lying on the desk, tipped up at the back, with the round window of an
    animation disc in it. (x, y) = its near left corner on the desk top (screen)."""
    P = _ob(x, y, s)
    L = [_S([P(0, 0, 0), P(0, 0, 3), P(0, d, rise), P(0, d, 0)], 0.9, 0.9, fill=True),
         _S([P(w, 0, 0), P(w, 0, 3), P(w, d, rise), P(w, d, 0)], 0.9, 0.9, fill=True),
         _S([P(0, 0, 3), P(w, 0, 3), P(w, d, rise), P(0, d, rise)], 1.1, 1.0, fill=True),
         _S([P(0, 0, 0), P(0, 0, 3), P(w, 0, 3), P(w, 0, 0)], 1.0, 1.0, fill=True)]
    cx, cy = P(w / 2, d / 2, (3 + rise) / 2)
    L.append(_S([(cx + s * (54 * math.cos(a) + DEPTH[0] * 27 * math.sin(a)), cy - s * (DEPTH[1] * 27 * math.sin(a) + 0.09 * 27 * math.sin(a)))
                 for a in [2 * math.pi * k / 40 for k in range(41)]], 0.7, 0.55))
    L += hatch([P(w, 2, 1), P(w, d - 2, 1), P(w, d - 2, rise - 2), P(w, 2, 2.5)], 3.4 * s, 75, 0.5, 0.45, seed=5)
    return L


def sheet_quad(x, y, s=1.0, w=104.0, d=52.0, inset=(12.0, 8.0), rise=15.0, board_d=64.0):
    """The four corners of the sheet lying on the board [near-left, near-right, far-right, far-left], for the
    board whose near left corner is (x, y). Map a drawing's unit square onto it with on_sheet()."""
    P = _ob(x, y, s)

    def hh(dep):
        return 3 + (rise - 3) * dep / board_d + 0.6
    d0, d1 = inset[1], inset[1] + d
    return [P(inset[0], d0, hh(d0)), P(inset[0] + w, d0, hh(d0)), P(inset[0] + w, d1, hh(d1)), P(inset[0], d1, hh(d1))]


def on_sheet(quad, pts, box=(0.0, 0.0, W, H)):
    """Lay a drawing made in a rectangle `box` (x0, y0, x1, y1; default the whole 960x540 frame) onto a sheet
    quad from sheet_quad(): this is how the path line of act 1 settles onto her paper. Takes a Stroke/points."""
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = quad
    out = []
    for x, y in pts:
        u = (x - box[0]) / (box[2] - box[0])
        v = 1 - (y - box[1]) / (box[3] - box[1])
        nx, ny = lerp(ax, bx, u), lerp(ay, by, u)
        fx, fy = lerp(dx, cx, u), lerp(dy, cy, u)
        out.append((lerp(nx, fx, v), lerp(ny, fy, v)))
    return pts.like(out) if isinstance(pts, Stroke) else Stroke(out)


def sheet_lines(x, y, s=1.0, lift=0.0, **kw):
    """The sheet on the pegs, with its three punched holes. lift 0..1 curls its far edge up off the board (as
    when she flips it). (x, y) = the board's near left corner."""
    q = sheet_quad(x, y, s, **kw)
    if lift > 0:
        up = 46 * s * clamp(lift)
        q = [q[0], q[1], (q[2][0] - 10 * s * lift, q[2][1] - up), (q[3][0] - 10 * s * lift, q[3][1] - up)]
    L = [_S(q, 1.0, 1.0, fill=True)]
    for f, kind in ((0.22, 'slot'), (0.5, 'round'), (0.78, 'slot')):
        cx, cy = lerp(q[0][0], q[1][0], f) + 3.0 * s, lerp(q[0][1], q[1][1], f) - 4.2 * s
        if kind == 'round':
            L.append(_S(_ell(cx, cy, 2.3 * s, 1.5 * s, n=10), 0.7, 0.9))
        else:
            L.append(_S([(cx - 5 * s, cy - 1.2 * s), (cx + 5 * s, cy - 1.2 * s), (cx + 5 * s, cy + 1.2 * s), (cx - 5 * s, cy + 1.2 * s)], 0.7, 0.9, close=True))
    return L


def pegbar_lines(x, y, s=1.0, w=92.0, **kw):
    """The peg bar: a thin strip along the near edge of the board with a round peg between two flat ones.
    (x, y) = the board's near left corner. Draw it AFTER the sheet (the pegs come up through the holes)."""
    q = sheet_quad(x, y, s, **kw)
    ax, ay = lerp(q[0][0], q[1][0], 0.06), lerp(q[0][1], q[1][1], 0.06)
    bx, by = lerp(q[0][0], q[1][0], 0.94), lerp(q[0][1], q[1][1], 0.94)
    ox, oy = 3.0 * s, -4.2 * s
    L = [_S([(ax + ox * 0.2, ay - 1.2 * s), (bx + ox * 0.2, by - 1.2 * s), (bx + ox * 1.9, by - 7.6 * s), (ax + ox * 1.9, ay - 7.6 * s)], 0.8, 0.85, close=True)]
    for f, kind in ((0.22, 'slot'), (0.5, 'round'), (0.78, 'slot')):
        cx, cy = lerp(q[0][0], q[1][0], f) + ox, lerp(q[0][1], q[1][1], f) + oy
        if kind == 'round':
            L.append(_S(_ell(cx, cy - 1.6 * s, 1.9 * s, 1.2 * s, n=10), 1.0, 1.0, fill=True))
            L.append(_S([(cx - 1.9 * s, cy - 1.6 * s), (cx - 1.9 * s, cy), (cx + 1.9 * s, cy), (cx + 1.9 * s, cy - 1.6 * s)], 0.9, 1.0))
        else:
            L.append(_S([(cx - 4.4 * s, cy - 2.6 * s), (cx + 4.4 * s, cy - 2.6 * s), (cx + 4.4 * s, cy + 0.4 * s), (cx - 4.4 * s, cy + 0.4 * s)], 0.9, 1.0, fill=True))
    return L


def lamp_lines(x, y, s=1.0, t=0.0, reach=0.0, on=1.0, nod=0.0):
    """The desk lamp: a round foot at (x, y) on the desk top, two sprung arms, a cone shade looking down and to
    the left at the board.

    reach  -1..1 folds the arms (the shade goes up and back, or down and forward)
    nod    degrees: tips the shade (it can look at her, or hang its head)
    on     0..1: pencil rays under the shade and a hatched pool edge
    Returns strokes; lamp_anchor() gives the shade's mouth."""
    A = lamp_anchor(x, y, s, reach, nod)
    L = []
    L.append(_S(_ell(x, y, 17 * s, 5.2 * s, n=22), 1.0, 1.0, fill=True))
    L.append(_S(_ell(x, y - 3 * s, 15 * s, 4.5 * s, n=22), 0.9, 1.0, fill=True))
    L.append(_S([(x - 15 * s, y - 3 * s), (x - 17 * s, y)], 0.8, 0.9))
    L.append(_S([(x + 15 * s, y - 3 * s), (x + 17 * s, y)], 0.8, 0.9))
    j0, j1, j2 = A['foot'], A['elbow'], A['wrist']
    for (a, b), off in (((j0, j1), 2.6), ((j1, j2), 2.4)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln * off * s, dx / ln * off * s
        L.append(Stroke([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)], 1.0, 1.0))
        L.append(Stroke([(a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny)], 1.0, 1.0))
        m0, m1 = (lerp(a[0], b[0], 0.18), lerp(a[1], b[1], 0.18)), (lerp(a[0], b[0], 0.62), lerp(a[1], b[1], 0.62))
        zig = []
        for k in range(13):
            f = k / 12
            sg = (1 if k % 2 else -1) * 0.75
            zig.append((lerp(m0[0], m1[0], f) + nx * sg, lerp(m0[1], m1[1], f) + ny * sg))
        L.append(Stroke(zig, 0.6, 0.7))                                # the spring
    for j in (j1, j2):
        L.append(_S(_ell(j[0], j[1], 3.6 * s, 3.6 * s, n=12), 0.9, 1.0, fill=True))
    L.append(_S(A['shade'], 1.1, 1.0, fill=True))
    L.append(_S(A['mouth_ellipse'], 0.9, 1.0, fill=True))
    L.append(_S(A['cap'], 0.9, 1.0, fill=True))
    L += hatch(A['shade'], 3.0 * s, A['angle'] + 80, 0.5, 0.5, seed=8)[::2]
    if on > 0:
        mx, my = A['mouth']
        ax = math.radians(A['angle'])
        for k in range(7):
            sp = (k - 3) * 0.17
            c, sn = math.cos(ax + sp), math.sin(ax + sp)
            r0, r1 = 22 * s, (46 + 16 * ((k * 3) % 4) / 3 + 4 * math.sin(t * 2.2 + k)) * s
            st = Stroke([(mx + c * r0, my + sn * r0), (mx + c * r1, my + sn * r1)], 0.55, 0.42 * clamp(on))
            L.append(st)
    return L


def lamp_anchor(x, y, s=1.0, reach=0.0, nod=0.0):
    """Joints of the lamp for the same arguments as lamp_lines: foot, elbow, wrist, the middle of the shade's
    mouth, its direction in degrees, and the shade's outline."""
    foot = (x, y - 3 * s)
    a1 = math.radians(-78 + 16 * reach)
    elbow = (foot[0] + 92 * s * math.cos(a1), foot[1] + 92 * s * math.sin(a1))
    a2 = math.radians(-165 - 24 * reach)
    wrist = (elbow[0] + 78 * s * math.cos(a2), elbow[1] + 78 * s * math.sin(a2))
    ang = 118 + 14 * reach + nod                    # the way the shade looks (down and to the left)
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    px, py = -sn, c

    def Q(along, across):
        return (wrist[0] + s * (c * along + px * across), wrist[1] + s * (sn * along + py * across))
    shade = [Q(-4, -7), Q(4, -9), Q(30, -23), Q(30, 23), Q(4, 9), Q(-4, 7)]
    mouth = Q(30, 0)
    me = [(mouth[0] + s * (px * 23 * math.cos(a) + c * 6 * math.sin(a)), mouth[1] + s * (py * 23 * math.cos(a) + sn * 6 * math.sin(a)))
          for a in [2 * math.pi * k / 24 for k in range(25)]]
    cap = [Q(-4, -7), Q(-11, -5), Q(-11, 5), Q(-4, 7)]
    return dict(foot=foot, elbow=elbow, wrist=wrist, mouth=mouth, angle=ang, shade=shade, mouth_ellipse=me, cap=cap)


def _sheet_offsets(n, mess, seed, w, d):
    rng = random.Random(seed * 53 + 11)
    out = []
    for k in range(int(math.ceil(n))):
        late = clamp(k / 40.0)                       # sheets land worse the higher the pile
        m = mess * (0.25 + 0.75 * late)
        out.append((rng.gauss(0, 1) * 9 * m + rng.uniform(-1, 1) * 0.8, rng.gauss(0, 1) * 7 * m + rng.uniform(-1, 1) * 0.8,
                    rng.gauss(0, 1) * 0.22 * m, rng.random()))
    return out


def stack_lines(x, y, s=1.0, n=10.0, w=104.0, d=52.0, th=2.2, mess=0.3, seed=0, lean=0.0):
    """A pile of drawings that can grow. (x, y) = the near left corner of the bottom sheet (screen).

    n      how many sheets (a float: the top sheet of 7.5 is half way down onto the pile). 50 sheets stand
           110 px at s=1: desk height.
    th     thickness of one sheet as drawn, px at s=1
    mess   0 = a squared ream, 1 = thrown: sheets land skewed and shifted, worse the higher the pile goes
    lean   px of sideways drift per sheet (the pile starts to go over)
    Each sheet is one closed, paper-filled Stroke, bottom to top, so the pile hides its own back edges and
    morph_lines() can take one pile to another sheet for sheet. stack_contour() is its outer edge."""
    P = _ob(x, y, s)
    L = []
    offs = _sheet_offsets(n, mess, seed, w, d)
    for k, (ox, od, skew, r) in enumerate(offs):
        land = clamp(n - k)                           # 0..1 for the sheet still coming down
        hh = k * th + (1 - smooth(land)) * 60
        ux = ox + lean * k
        q = [P(ux, od - skew * w * 0.5, hh), P(ux + w, od + skew * w * 0.5, hh), P(ux + w + skew * 6, od + d + skew * w * 0.5, hh),
             P(ux + skew * 6, od + d - skew * w * 0.5, hh)]
        top = k >= len(offs) - 1
        st = _S(q, 1.0 if top else 0.62, 1.0 if top else (0.5 + 0.3 * r), fill=True)
        L.append(st)
    return L


def stack_top(x, y, s=1.0, n=10.0, th=2.2, lean=0.0, w=104.0, d=52.0):
    """Screen point of the middle of the top sheet of a stack (where the next sheet lands, where a hoof stamps)."""
    P = _ob(x, y, s)
    return P(w / 2 + lean * n, d / 2, n * th)


def stack_contour(x, y, s=1.0, n=10.0, pts=120, **kw):
    """The outer edge of the pile as ONE open polyline of `pts` points: from the floor at its left, up the left
    side, across the top, down the right side to the floor. This is the heap that settles, point for point,
    into ground_with_stump()."""
    L = stack_lines(x, y, s, n, **kw)
    if not L:
        return Stroke([(x, y)] * pts)
    left = [(min(st[0][0], st[3][0]), st[0][1]) for st in L]
    right = [(max(st[1][0], st[2][0]), st[1][1]) for st in L]
    topq = L[-1]
    raw = [(left[0][0], y)] + left + [topq[3], topq[2]] + right[::-1] + [(right[0][0], y)]
    return Stroke(resample(raw, pts), 1.2, 1.0)


def tray_lines(x, y, s=1.0, w=112.0, d=58.0, wall=15.0, n=0.0, th=2.2, mess=0.2, seed=1):
    """A paper tray (in-tray or out-tray): a shallow open box with a thumb notch in its front wall, and `n`
    sheets in it. (x, y) = its near left corner on whatever it stands on. Past about 7 sheets the pile rises
    out of the tray."""
    P = _ob(x, y, s)
    L = [_S([P(0, d, 0), P(0, d, wall), P(w, d, wall), P(w, d, 0)], 0.8, 0.8, fill=True),          # back wall
         _S([P(0, 0, 0), P(0, 0, wall), P(0, d, wall), P(0, d, 0)], 0.9, 0.9, fill=True)]          # left wall
    L += hatch([P(2, d, 1), P(w - 2, d, 1), P(w - 2, d, wall - 1), P(2, d, wall - 1)], 3.4 * s, 70, 0.5, 0.4, seed=seed + 20)
    if n > 0:
        L += stack_lines(P(4, 3, 1)[0], P(4, 3, 1)[1], s, n, w - 8, d - 6, th, mess, seed)
    L.append(_S([P(w, 0, 0), P(w, 0, wall), P(w, d, wall), P(w, d, 0)], 1.0, 1.0, fill=n < wall / th))   # right wall
    notch = [P(0, 0, 0), P(0, 0, wall), P(w * 0.36, 0, wall)]
    notch += [P(w * 0.5 + w * 0.14 * math.cos(a), 0, wall - 9 * math.sin(a)) for a in [math.pi - math.pi * k / 10 for k in range(11)]]
    notch += [P(w * 0.64, 0, wall), P(w, 0, wall), P(w, 0, 0)]
    L.append(_S(notch, 1.1, 1.0, fill=True))                                                       # front wall
    return L


def stamp_lines(x, y, s=1.0, lift=0.0, tilt=0.0, squash=0.0):
    """The rubber stamp: a turned wooden handle on a block, the rubber die under it. (x, y) = where the middle
    of the die touches down. lift = px it is held above that; tilt = degrees; squash 0..1 = pressed hard (the
    die spreads and the handle sinks 2 px). Returns strokes."""
    q = clamp(squash)

    def T(pts):
        return _tf(pts, x, y - lift * s + 2 * q * s, s, tilt, 1, (0, 0))
    hw = 15 + 1.5 * q
    L = [_S(T([(-hw + 1, 0), (-hw, -5 + 2 * q), (hw + 8, -5 + 2 * q - 4), (hw + 9, -4)]), 0.8, 0.9, fill=True),          # die (side going back)
         _S(T([(-hw, 0), (-hw, -5 + 2 * q), (hw, -5 + 2 * q), (hw, 0)]), 1.0, 1.0, fill=True),
         _S(T([(-17, -5 + 2 * q), (-17, -16), (-9, -21), (25, -21), (25, -9), (17, -5 + 2 * q)]), 1.0, 1.0, fill=True),  # block
         _S(T([(-17, -16), (17, -16), (25, -21)]), 0.8, 0.9), _S(T([(17, -16), (17, -5 + 2 * q)]), 0.8, 0.9)]
    handle = [(-5, -18), (-4.4, -24), (-7, -29), (-3.4, -33), (-3.6, -39), (-8.6, -44), (-9.8, -51), (-6, -57), (0, -59),
              (6, -57), (9.8, -51), (8.6, -44), (3.6, -39), (3.4, -33), (7, -29), (4.4, -24), (5, -18)]
    L.append(_S(T([(p[0] + 4, p[1]) for p in handle]), 1.1, 1.0, fill=True))
    L.append(_S(T([(4 - 6.4, -29), (4 + 6.4, -29)]), 0.6, 0.7))
    L += [st for st in hatch(T([(6, -57), (13.8, -51), (12.6, -44), (8, -40), (7, -46), (9, -51)]), 2.4 * s, 60 + tilt, 0.5, 0.55, seed=9)]
    return L


def pad_lines(x, y, s=1.0, open_=1.0):
    """The ink pad: a flat tin, its lid hinged open behind it. (x, y) = near left corner. open_ 0..1."""
    P = _ob(x, y, s)
    w, d = 50, 30
    L = [_S([P(0, 0, 0), P(0, 0, 5), P(w, 0, 5), P(w, 0, 0)], 1.0, 1.0, fill=True),
         _S([P(w, 0, 0), P(w, 0, 5), P(w, d, 5), P(w, d, 0)], 0.9, 0.9, fill=True),
         _S([P(0, 0, 5), P(w, 0, 5), P(w, d, 5), P(0, d, 5)], 1.0, 1.0, fill=True)]
    inner = [P(4, 3, 5), P(w - 4, 3, 5), P(w - 4, d - 3, 5), P(4, d - 3, 5)]
    L.append(_S(inner, 0.7, 0.9, close=True))
    L += hatch(inner, 2.3 * s, 28, 0.6, 0.75, seed=10)
    L += hatch(inner, 2.9 * s, -40, 0.5, 0.5, seed=12)
    if open_ > 0:
        up = 30 * clamp(open_)
        L.insert(0, _S([P(0, d, 5), P(w, d, 5), P(w, d + 6 * (1 - open_), 5 + up), P(0, d + 6 * (1 - open_), 5 + up)], 0.9, 0.9, fill=True))
    return L


def hoofprint_lines(x, y, s=1.0, angle=0.0, ink_=1.0):
    """Her approval mark: a cloven hoofprint, two half-moons, hatched dark. Centred on (x, y), toes toward
    `angle` degrees - 90 (0 = toes up). ink_ 0..1 = how well the pad was inked (the hatching thins)."""
    half = [(1.5, -11.5), (3.8, -13), (7.4, -9.5), (9.6, -2.5), (9.2, 4.5), (6.2, 9.4), (2.8, 10), (1.5, 7)]
    L = []
    for side in (1, -1):
        pts = _tf([(px * side, py) for px, py in half], x, y, s, angle, 1)
        L.append(_S(pts, 1.0, 1.0, close=True))
        hs = hatch(pts, 1.9 * s, 35 + angle, 0.75, 0.85, seed=14 + side)
        L += hs if ink_ >= 1 else hs[::2 if ink_ > 0.5 else 3]
    return L


def clock_lines(x, y, s=1.0, hours=9.0, t=0.0, r=42.0, swing=14.0, pendulum=True):
    """The wall clock, centre (x, y). hours is a float (9.5 = half past nine): run it fast to make time go.
    The pendulum swings by itself with t (period 1.2 s), `swing` degrees each way.
    Order of strokes: nail and case, rim, ticks, hands, pendulum."""
    R = r * s
    L = [_S([(x - 2 * s, y - R - 15 * s), (x + 2 * s, y - R - 15 * s), (x, y - R - 9 * s)], 0.8, 0.9, close=True),
         Stroke([(x, y - R - 9 * s), (x, y - R)], 0.7, 0.8)]
    if pendulum:
        bx0, bx1, by1 = x - 13 * s, x + 13 * s, y + R + 54 * s
        L.append(_S([(bx0, y + R * 0.8), (bx0, by1), (bx1, by1), (bx1, y + R * 0.8)], 0.9, 0.9, fill=True))
        a = math.radians(swing * math.sin(2 * math.pi * t / 1.2))
        px, py = x + math.sin(a) * (R + 40 * s), y + math.cos(a) * (R + 40 * s)
        L.append(Stroke([(x + math.sin(a) * R * 0.9, y + math.cos(a) * R * 0.9), (px, py)], 0.8, 0.9))
        L.append(_S(_ell(px, py, 6.5 * s, 6.5 * s, n=14), 1.0, 1.0, fill=True))
        L += hatch(_ell(px, py, 6 * s, 6 * s, n=14), 2.2 * s, 50, 0.5, 0.6, seed=15)
    L.append(_S(_ell(x, y, R, R, n=44), 1.25, 1.0, fill=True))
    L.append(_S(_ell(x, y, R * 0.9, R * 0.9, n=40), 0.7, 0.8))
    cres = _ell(x, y, R * 0.89, R * 0.89, 20, 120, n=14) + _ell(x - 3 * s, y - 4 * s, R * 0.84, R * 0.84, 120, 20, n=14)
    L += hatch(cres, 2.6 * s, 45, 0.5, 0.42, seed=16)
    for k in range(12):
        a = 2 * math.pi * k / 12
        r0 = 0.72 if k % 3 == 0 else 0.8
        L.append(Stroke([(x + math.sin(a) * R * r0, y - math.cos(a) * R * r0), (x + math.sin(a) * R * 0.87, y - math.cos(a) * R * 0.87)],
                        1.1 if k % 3 == 0 else 0.7, 0.95))
    ha = 2 * math.pi * (hours % 12) / 12
    ma = 2 * math.pi * (hours % 1)
    hx, hy = math.sin(ha), -math.cos(ha)
    L.append(_S([(x - hy * 2.4 * s - hx * 5 * s, y + hx * 2.4 * s - hy * 5 * s), (x + hx * R * 0.5, y + hy * R * 0.5),
                 (x + hy * 2.4 * s - hx * 5 * s, y - hx * 2.4 * s - hy * 5 * s)], 1.1, 1.0, close=True))
    L.append(Stroke([(x - math.sin(ma) * 7 * s, y + math.cos(ma) * 7 * s), (x + math.sin(ma) * R * 0.76, y - math.cos(ma) * R * 0.76)], 1.3, 1.0))
    L.append(_S(_ell(x, y, 2.6 * s, 2.6 * s, n=10), 1.0, 1.0, fill=True))
    return L


def pot_lines(x, y, s=1.0, brush=True, lean=24.0, level=0.6):
    """The paint pot (a jar) with a brush standing in it. (x, y) = the middle of its base on the desk.
    brush=False when the brush is in her mouth; lean = the brush's angle off upright, degrees."""
    rx, ry, hh = 12 * s, 3.8 * s, 27 * s
    L = []
    body = [(x - rx, y - hh)] + _ell(x, y, rx, ry, 180, 0, n=14) + [(x + rx, y - hh)]
    L.append(_S(body + _ell(x, y - hh, rx, ry, 0, 180, n=12), 1.0, 1.0, fill=True))
    if brush:
        a = math.radians(lean)
        bx, by = x + 2 * s, y - 6 * s
        tx, ty = bx + math.sin(a) * 74 * s, by - math.cos(a) * 74 * s
        nx, ny = math.cos(a) * 1.7 * s, math.sin(a) * 1.7 * s
        L.append(_S([(bx - nx, by - ny), (tx - nx * 0.6, ty - ny * 0.6), (tx + nx * 0.6, ty + ny * 0.6), (bx + nx, by + ny)], 0.9, 1.0, fill=True))
    L.append(_S(_ell(x, y - hh, rx, ry, n=20), 1.0, 1.0, fill=not brush))
    lv = y - hh * clamp(level)
    L.append(_S(_ell(x, lv, rx * 0.97, ry * 0.95, 20, 160, n=10), 0.6, 0.6))
    L.append(_S(body, 1.0, 1.0))
    L += hatch([(x + rx * 0.35, lv), (x + rx * 0.95, lv - ry * 0.4), (x + rx * 0.95, y - ry * 0.6), (x + rx * 0.35, y + ry * 0.7)], 2.5 * s, 80, 0.5, 0.5, seed=17)
    return L


def brush_lines(x, y, s=1.0, angle=0.0, wet=1.0):
    """A loose brush, bristle tip at (x, y), handle running off at `angle` degrees (0 = handle to the right).
    For when she carries it in her mouth."""
    pts = [(0, 0), (5, -2.6), (13, -2.9), (15, -2.2), (22, -2.2), (22.6, -1.6), (86, -1.1), (88, 0), (86, 1.1), (22.6, 1.6),
           (22, 2.2), (15, 2.2), (13, 2.9), (5, 2.6)]
    L = [_S(_tf(pts, x, y, s, angle), 1.0, 1.0, fill=True),
         _S(_tf([(15, -2.2), (15, 2.2)], x, y, s, angle), 0.7, 0.9), _S(_tf([(22, -2.2), (22, 2.2)], x, y, s, angle), 0.7, 0.9)]
    if wet > 0:
        L += hatch(_tf([(0, 0), (5, -2.6), (13, -2.9), (13, 2.9), (5, 2.6)], x, y, s, angle), 1.6 * s, angle + 8, 0.6, 0.8 * wet, seed=18)
    return L


def lever_lines(x, y, s=1.0, pull=0.0):
    """The camera: a post on the desk with a lever on it, and a little shutter box at the top of the post.
    (x, y) = the foot of the post. pull 0..1 brings the lever from up-and-back down toward her.
    lever_anchor() gives the grip."""
    A = lever_anchor(x, y, s, pull)
    px, top = x, y - 70 * s
    L = [_S(_ell(x, y, 13 * s, 4 * s, n=18), 1.0, 1.0, fill=True),
         _S([(px - 3.2 * s, y - 1 * s), (px - 3.2 * s, top), (px + 3.2 * s, top), (px + 3.2 * s, y - 1 * s)], 1.0, 1.0, fill=True),
         _S([(px - 15 * s, top), (px - 15 * s, top - 20 * s), (px + 15 * s, top - 20 * s), (px + 15 * s, top)], 1.0, 1.0, fill=True),
         _S([(px + 15 * s, top), (px + 21 * s, top - 6 * s), (px + 21 * s, top - 26 * s), (px + 15 * s, top - 20 * s)], 0.8, 0.9, fill=True),
         _S([(px - 15 * s, top - 20 * s), (px - 9 * s, top - 26 * s), (px + 21 * s, top - 26 * s)], 0.8, 0.9)]
    op = 5.5 * s * (1 - 0.85 * clamp((pull - 0.8) / 0.2))                 # the shutter: an eye that closes at the bottom of the pull
    L.append(_S(_ell(px - 2 * s, top - 10 * s, 6.5 * s, max(0.6, op), n=16), 0.9, 1.0, close=True))
    if op > 2:
        L += hatch(_ell(px - 2 * s, top - 10 * s, 6 * s, op * 0.9, n=16), 1.8 * s, 30, 0.55, 0.8, seed=19)
    piv, grip = A['pivot'], A['grip']
    dx, dy = grip[0] - piv[0], grip[1] - piv[1]
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln * 2.0 * s, dx / ln * 2.0 * s
    L.append(_S([(piv[0] + nx, piv[1] + ny), (grip[0] + nx * 0.7, grip[1] + ny * 0.7), (grip[0] - nx * 0.7, grip[1] - ny * 0.7), (piv[0] - nx, piv[1] - ny)], 1.0, 1.0, fill=True))
    L.append(_S(_ell(grip[0], grip[1], 5.2 * s, 5.2 * s, n=14), 1.1, 1.0, fill=True))
    L.append(_S(_ell(piv[0], piv[1], 3.4 * s, 3.4 * s, n=12), 1.0, 1.0, fill=True))
    return L


def lever_anchor(x, y, s=1.0, pull=0.0):
    piv = (x, y - 46 * s)
    a = math.radians(lerp(-128, -196, smooth(pull)))
    return dict(pivot=piv, grip=(piv[0] + 50 * s * math.cos(a), piv[1] + 50 * s * math.sin(a)))


def desk_layout(x, y, s=1.0):
    """Where every piece of the desk set sits, for a seated cow placed at (x, y, s) with cast (facing right).
    Returns screen points to hand to the *_lines functions:

      desk      floor under the desk's near left corner         board   near left corner of the drawing board
      sheet     the sheet's four corners (see on_sheet)         top_y   the desk top's front edge (her hooves)
      pot, lever, pad, stamp (touch-down on the pad), mark (touch-down on the sheet), lamp,
      blank (the blank paper waiting on the desk: the in-tray)
      out_tray  on the floor to the right of the desk           stack   on the floor beyond it (the pile)
      clock     on the wall, upper right                        floor   y of the floor"""
    dx, dy = x + 28 * s, y
    P = _ob(dx, dy, s)
    b = P(4, 5, DESK_H)
    q = sheet_quad(b[0], b[1], s)
    pad = P(204, 8, DESK_H)
    padP = _ob(pad[0], pad[1], s)
    return dict(desk=(dx, dy), board=b, sheet=q, top_y=y - DESK_H * s, floor=y,
                pot=P(150, 58, DESK_H), lever=P(172, 30, DESK_H), pad=pad, stamp=padP(25, 15, 5),
                mark=(lerp(q[0][0], q[2][0], 0.82), lerp(q[0][1], q[2][1], 0.3)),
                lamp=P(308, 62, DESK_H), blank=P(264, 6, DESK_H),
                out_tray=(dx + (DESK_W + 44) * s, y), stack=(dx + (DESK_W + 44 + 4) * s, y - 1 * s),
                clock=(dx + (DESK_W + 96) * s, y - 318 * s),
                right=dx + DESK_W * s)


def desk_set(ink, x, y, s=1.0, t=0.0, progress=1.0, pile=0.0, blanks=12.0, hours=9.0, stamp_lift=0.0, stamp_at=None,
             stamp_squash=0.0, pull=0.0, brush=True, lamp_on=1.0, lamp_reach=0.0, mess=0.3, sheet=True, stool=True,
             clock=True, alpha=1.0, **pencil_kw):
    """The whole desk set for a cow seated at (x, y, s), drawn in the right order with one pencil() call.

    progress  0..1: the set draws itself ON (floor, stool, desk, board and sheet, pot, lever, pad and stamp,
              blank paper, lamp, out-tray, clock), contour by contour
    pile      sheets in the out-tray on the floor (a float; 50 = desk height, 125 = over her head)
    blanks    sheets of blank paper waiting on the desk (the in-tray)
    hours     the wall clock
    stamp_at  None = the stamp rests on its pad; or a screen point it is over (e.g. layout['mark'])
    stamp_lift / stamp_squash, pull (camera lever), brush (False = it is in her mouth), lamp_on, lamp_reach
    Returns desk_layout(x, y, s) plus 'tip': where the pencil is while progress < 1.
    Draw the cow AFTER this (she sits in front of the desk's left end) or build your own order from the
    *_lines functions (each returns a list of strokes; concatenate and pencil())."""
    A = desk_layout(x, y, s)
    L = desk_set_lines(x, y, s, t, pile, blanks, hours, stamp_lift, stamp_at, stamp_squash, pull, brush, lamp_on, lamp_reach,
                       mess, sheet, stool, clock)
    A['tip'] = pencil(ink, L, progress, alpha=alpha, **pencil_kw)
    return A


def desk_set_lines(x, y, s=1.0, t=0.0, pile=0.0, blanks=12.0, hours=9.0, stamp_lift=0.0, stamp_at=None, stamp_squash=0.0,
                   pull=0.0, brush=True, lamp_on=1.0, lamp_reach=0.0, mess=0.3, sheet=True, stool=True, clock=True):
    """The strokes desk_set() draws, in order, as one list (to morph, transform, or draw on yourself)."""
    A = desk_layout(x, y, s)
    L = []
    L += floor_lines(*A['desk'], s)
    if stool:
        L += stool_lines(x, y, s)
    L += desk_lines(*A['desk'], s)
    L += lamp_lines(*A['lamp'], s, t, lamp_reach, lamp_on)
    L += pot_lines(*A['pot'], s, brush)
    L += board_lines(*A['board'], s)
    if sheet:
        L += sheet_lines(*A['board'], s)
    L += pegbar_lines(*A['board'], s)
    L += lever_lines(*A['lever'], s, pull)
    L += pad_lines(*A['pad'], s)
    sx, sy = stamp_at if stamp_at is not None else A['stamp']
    L += stamp_lines(sx, sy, s, stamp_lift, 0.0, stamp_squash)
    if blanks > 0:
        L += stack_lines(*A['blank'], s, blanks, 58, 40, 1.6, 0.05, 5)
    L += tray_lines(*A['out_tray'], s, n=pile, mess=mess)
    if clock:
        L += clock_lines(*A['clock'], s, hours, t)
    return L


# =========================================================================== THE ORCHARD · in line ===

def stump_lines(x, y, s=1.0, cleft=0.0, grip=0.0, rings=True, roots=True):
    """The old rootstock: the stump of act 1 (STUMP_PROFILE, same proportions) drawn in pencil. (x, y) = the
    ground under its middle; at s=1 it is 46 wide and 22 high, so use s of 3 to 5 in act 2.

    cleft  0..1 opens a split down from the middle of the cut (to 12 units deep, 5 wide at the top)
    grip   0..1: the cleft closes back on the wedge set in it (the stump line gives 2 px and holds)
    The FIRST stroke is the profile (the contour that came from the heap); bark, rings and roots follow."""
    c = clamp(cleft)
    hw = (2.5 * c) * (1 - 0.45 * clamp(grip)) + 0.0
    dp = 12.0 * c
    prof = list(STUMP_PROFILE[:6])
    if c > 0:
        prof += [(-hw - 0.6 * grip, -22 - 0.5 * grip), (0, -22 + dp), (hw + 0.6 * grip, -22 - 0.5 * grip)]
    prof += list(STUMP_PROFILE[6:])
    L = [_S(_tf(prof, x, y, s), 1.25, 1.0)]
    L[0].fill = False
    if rings:
        L.append(_S(_tf(_ell(0, -22, 11, 2.3, 180, 360, n=16), x, y, s), 0.8, 0.8))             # the far rim of the cut
        for k, rr in enumerate((7.6, 4.4)):
            arc = _ell(0.6, -22.2, rr, rr * 0.2, 200 + 14 * k, 338 - 10 * k, n=10)
            L.append(_S(_tf(arc, x, y, s), 0.5, 0.55))
        if c > 0:
            L.append(_S(_tf([(0, -22 + dp), (0.3, -22 + dp + 5 * c), (-0.2, -22 + dp + 9 * c)], x, y, s), 0.6, 0.7))   # the split runs on as a crack
    bark = [[(-7.5, -19), (-7.9, -13), (-8.6, -8)], [(-3, -18.5), (-3.4, -10), (-4.6, -4), (-8, -1.5)],
            [(3.6, -19), (4.0, -12), (5.4, -6), (9, -2.5)], [(8.2, -18), (8.6, -12)], [(0.6, -7), (0.4, -2)],
            [(-1.8, -14), (-2.2, -12.5), (-1.4, -11.4), (-0.6, -12.8), (-1.8, -14)]]
    for b in bark:
        L.append(_S(_tf(b, x, y, s), 0.6, 0.7))
    L += hatch(_tf([(4, -21), (11, -21), (12, -11), (14, -5.5), (18.5, -1.8), (8, -1.2), (6.4, -8)], x, y, s), 1.5 * s, 68, 0.5, 0.5, seed=31)
    if roots:
        for r in ([(-20, 0), (-27, 1.6), (-34, 1.2)], [(26, 0), (33, 1.8), (41, 1.2)], [(-9, -1), (-12, 2.4)], [(12, -1), (15, 2.8), (20, 3)]):
            L.append(_S(_tf(r, x, y, s), 0.8, 0.85))
        for gx in (-31, -25, 31, 37, 45):
            L.append(_S(_tf([(gx, 1.5), (gx - 1.2, -3.2)], x, y, s), 0.5, 0.7))
            L.append(_S(_tf([(gx + 1.2, 1.5), (gx + 2.2, -2.4)], x, y, s), 0.5, 0.7))
    return L


def stump_anchor(x, y, s=1.0, cleft=1.0):
    """Screen points on the stump: 'cleft' = the bottom of the split (where the wedge tip goes), 'rim' = the
    middle of the cut, 'cut' = its two ends, 'bind' = the middle of the trunk 6 units under the cut."""
    return dict(cleft=(x, y - s * (22 - 12 * clamp(cleft))), rim=(x, y - 22 * s), cut=((x - 11 * s, y - 22 * s), (x + 11 * s, y - 22 * s)),
                bind=(x, y - 16 * s))


def ground_with_stump(x, y, s=1.0, x0=-40.0, x1=1000.0, slope=0.0, pts=120, cleft=0.0):
    """One open polyline of `pts` points: the ground line coming in from the left, up and over the stump's
    profile at (x, y), and on to the right; `slope` px of fall per px (0.13 = the lie of the act 1 hill at
    the tree). This is what the heap's contour (stack_contour) settles into, point for point."""
    prof = _tf(STUMP_PROFILE if cleft <= 0 else STUMP_PROFILE[:6] + [(-2.5 * cleft, -22), (0, -22 + 12 * cleft), (2.5 * cleft, -22)]
               + STUMP_PROFILE[6:], x, y, s)
    left = [(x0, y + (x0 - x) * slope), (prof[0][0] - 60 * s, y + (prof[0][0] - 60 * s - x) * slope * 0.9 + 1.5 * s)]
    right = [(prof[-1][0] + 70 * s, y + (prof[-1][0] + 70 * s - x) * slope * 0.9 + 1.5 * s), (x1, y + (x1 - x) * slope)]
    return Stroke(resample(left + prof + right, pts), 1.25, 1.0)


def knife_lines(x, y, s=1.0, angle=0.0):
    """The grafting knife. (x, y) = the point of the blade; the knife lies back from it along `angle` degrees
    (0 = handle to the right, edge downward). About 92 units long at s=1."""
    blade = [(0, 0), (10, -5.4), (24, -7.4), (40, -7.6), (40, 1.8), (22, 2.4), (8, 1.6)]
    handle = [(40, -8.4), (46, -9.2), (72, -8.4), (86, -9.4), (92, -4), (88, 3.4), (72, 3.6), (46, 3.2), (40, 2.6)]
    L = [_S(_tf(blade, x, y, s, angle), 1.0, 1.0, fill=True), _S(_tf(handle, x, y, s, angle), 1.1, 1.0, fill=True),
         _S(_tf([(4, 0.2), (22, 0.2), (39, -0.4)], x, y, s, angle), 0.5, 0.7),
         _S(_tf([(46, -9.2), (46, 3.2)], x, y, s, angle), 0.7, 0.9)]
    for rx in (56, 76):
        L.append(_S(_tf(_ell(rx, -2.6, 1.7, 1.7, n=8), x, y, s, angle), 0.7, 0.9))
    L += hatch(_tf([(48, 0), (88, 0.4), (88, 3.2), (72, 3.4), (48, 3)], x, y, s, angle), 1.8 * s, angle + 70, 0.5, 0.55, seed=33)
    return L


def shaving_lines(x, y, s=1.0, curl=1.0, angle=-30.0):
    """The one shaving that curls off the cut: a spiral ribbon starting at (x, y). curl 0..1 grows it."""
    n = max(2, int(40 * clamp(curl)))
    a_, b_ = [], []
    for k in range(n + 1):
        th = k / 40 * 1.9 * 2 * math.pi
        r = 1.6 + 0.9 * th
        px, py = r * math.cos(th) - 2.0, r * math.sin(th)
        a_.append((px, py))
        b_.append((px * 1.0 + 1.8, py - 2.4))
    return [_S(_tf(a_, x, y, s, angle), 0.8, 0.95), _S(_tf(b_, x, y, s, angle), 0.6, 0.7)]


def shoot_lines(x, y, s=1.0, angle=-82.0, grow=1.0, knuckle=1.0, buds=1.0, length=64.0, stub=26.0, n=72):
    """The scion: a cut shoot with a wedge at its lower end and two buds. It BEGINS as her pencil stub.

    (x, y)   the point of the wedge. It never moves and never changes: it is the pencil point and it is the
             scion's wedge. The shoot runs from it along `angle` (degrees; -90 = straight up).
    grow     0 = the pencil stub (`stub` units long), 1 = the shoot (`length` units)
    knuckle  0 = straight sided, 1 = knuckled at its two nodes
    buds     0..1 swells the two buds (lower one on the right, upper one on the left)
    The first stroke is the contour: closed, n points, the SAME point count at every grow/knuckle, starting
    at the wedge point and going up the left side, so pencil and shoot morph point for point."""
    Ln = lerp(stub, length, clamp(grow))
    k_ = clamp(knuckle)
    nodes = (0.50, 0.88)

    def half(u):                                    # half width at u along the stick (0 = wedge point)
        d = u * Ln
        wd = 3.1 * min(1.0, d / 13.0) ** 0.85       # the wedge: 13 units long, then the full stick
        for nd in nodes:
            wd += 1.1 * k_ * math.exp(-((u - nd) * Ln / 2.6) ** 2)
        return wd
    m = n // 2
    left, right = [], []
    for i in range(m):
        u = i / (m - 1)
        bend = 2.2 * k_ * math.sin(u * math.pi * 1.5) * (Ln / length)
        left.append((u * Ln, -half(u) + bend))
        right.append((u * Ln + (1.6 * k_ if i == m - 1 else 0), half(u) + bend))
    contour = left + right[::-1]
    L = [_S(_tf(contour, x, y, s, angle), 1.15, 1.0, fill=True)]
    L.append(_S(_tf([(2, 0), (13, -0.4)], x, y, s, angle), 0.5, 0.6 * (1 - 0.5 * k_)))           # the facet of the wedge
    if k_ < 0.6:                                                                                  # the pencil's painted collar
        L.append(_S(_tf([(13.5, -3.0), (14.6, -1), (13.6, 1), (14.6, 3.0)], x, y, s, angle), 0.6, 0.8 * (1 - k_ / 0.6)))
    if k_ > 0.2:
        for nd in nodes:
            d = nd * Ln
            bend = 2.2 * k_ * math.sin(nd * math.pi * 1.5) * (Ln / length)
            L.append(_S(_tf([(d - 0.6, -half(nd) + bend + 0.8), (d + 0.4, bend), (d - 0.6, half(nd) + bend - 0.8)], x, y, s, angle), 0.5, 0.65 * k_))
    b_ = clamp(buds)
    if b_ > 0:
        for nd, side in zip(nodes, (1, -1)):
            d = nd * Ln
            bend = 2.2 * k_ * math.sin(nd * math.pi * 1.5) * (Ln / length)
            base = half(nd) * side + bend
            bud = [(d - 1.5, base), (d + 1.2 * b_, base + side * 3.3 * b_), (d + 5.6 * b_, base + side * 4.4 * b_), (d + 4.2 * b_, base + side * 1.3 * b_), (d + 3.0, base)]
            L.append(_S(_tf(bud, x, y, s, angle), 0.9, 1.0, fill=True))
    return L


def shoot_anchor(x, y, s=1.0, angle=-82.0, grow=1.0, knuckle=1.0, length=64.0, stub=26.0):
    """Screen points on the shoot for the same arguments: 'tip' (top end), 'buds' [(x, y, outward_deg), lower,
    upper], 'wedge' (the point), 'neck' (13 units up, where the wedge ends and the binding begins)."""
    Ln = lerp(stub, length, clamp(grow))
    k_ = clamp(knuckle)
    out = dict(wedge=(x, y), neck=_tf([(13, 0)], x, y, s, angle)[0], tip=_tf([(Ln, 2.2 * k_ * math.sin(math.pi * 1.5) * (Ln / length))], x, y, s, angle)[0])
    buds = []
    for nd, side in zip((0.50, 0.88), (1, -1)):
        bend = 2.2 * k_ * math.sin(nd * math.pi * 1.5) * (Ln / length)
        p = _tf([(nd * Ln + 4, (3.1 + 1.1 * k_) * side + bend + side * 3)], x, y, s, angle)[0]
        buds.append((p[0], p[1], angle + side * 62))
    out['buds'] = buds
    return out


def binding_path(x, y, s=1.0, width=23.4, turns=3.0, pitch=2.7, n=120, tail=9.0):
    """The binding as ONE polyline of n points: `turns` turns of a flat helix wound downward round a join that
    is `width` units across, its middle at (x, y) at the top turn, ending in a loose tail. This is what the
    crooked path line winds into (morph(path_stroke(), binding_path(...), u)). Points on the far side of the
    stem are included (binding_lines() leaves them out)."""
    pts = []
    m = n - 8
    for k in range(m):
        th = 2 * math.pi * turns * k / (m - 1)
        pts.append((x + s * (width / 2) * -math.cos(th), y + s * (pitch * th / (2 * math.pi) + 1.0 * math.sin(th))))
    ex, ey = pts[-1]
    for k in range(1, 9):
        f = k / 8
        pts.append((ex - s * tail * f * 0.55, ey + s * (tail * f - 5 * math.sin(f * math.pi))))
    return Stroke(pts, 1.1, 1.0)


def binding_lines(x, y, s=1.0, width=23.4, turns=3.0, pitch=2.7, wound=1.0, tail=9.0, band=1.7):
    """The binding as it is seen: only the near half of each turn (a row of slanted bands across the stem),
    then the tail. wound 0..1 = how much of it has been wound on. (x, y) = middle of the top turn.
    Each band is a thin closed, filled strip, so it covers the bark it crosses."""
    L = []
    w_ = clamp(wound)
    total = turns * 2 * math.pi
    lim = total * min(1.0, w_ / 0.9)
    k = 0
    while True:
        a0, a1 = 2 * math.pi * k, 2 * math.pi * k + math.pi          # the near half turn: left edge to right edge
        if a0 >= lim:
            break
        a1 = min(a1, lim)
        top, bot = [], []
        for j in range(9):
            th = lerp(a0, a1, j / 8)
            px = x + s * (width / 2) * -math.cos(th)
            py = y + s * (pitch * th / (2 * math.pi) + 1.0 * math.sin(th - a0))
            top.append((px, py - band * s / 2))
            bot.append((px, py + band * s / 2))
        L.append(_S(top + bot[::-1], 0.9, 1.0, fill=True))
        k += 1
        if k > 40:
            break
    if w_ > 0.9:
        f = (w_ - 0.9) / 0.1
        ex, ey = x + s * width / 2 * -math.cos(total), y + s * pitch * turns
        tl = [(ex - s * tail * g * 0.55 * f, ey + s * (tail * g - 5 * math.sin(g * math.pi)) * f) for g in [j / 8 for j in range(9)]]
        L.append(Stroke(tl, 1.0, 1.0))
        L.append(_S(_ell(ex, ey + 1 * s, 2.2 * s, 1.6 * s, n=10), 0.9, 1.0, fill=True))
    return L


def leaf_contour(x, y, s=1.0, angle=-60.0, open_=1.0, length=30.0, width=12.5, n=48, curl=0.0):
    """One leaf as a single closed contour of n+1 points (first = last). (x, y) = the stem end.
    POINT 0 IS THE STEM END, POINT n/2 IS THE TIP: for the hand-over, stem becomes tail and tip becomes nose.

    angle  the way it points, degrees (-90 = up)
    open_  0 = a folded sliver just out of the bud (short and shut), 1 = open
    curl   -1..1 bends it along its length (a leaf letting go, a leaf in a current)"""
    o = clamp(open_)
    Ln = length * (0.3 + 0.7 * smooth(o))
    wd = width * (0.1 + 0.9 * smooth(clamp((o - 0.15) / 0.85)))
    m = n // 2
    up, dn = [], []
    for i in range(m + 1):
        u = i / m
        prof = (math.sin(math.pi * u ** 0.82) ** 0.9) * (1 - 0.22 * u)
        prof = prof if u > 0.07 else prof * 0.0 + 0.075 * (u / 0.07)                    # the stalk
        bend = curl * Ln * 0.28 * u * u
        up.append((u * Ln, -prof * wd * 0.5 + bend))
        dn.append((u * Ln, prof * wd * 0.55 + bend))
    pts = up + dn[-2::-1]
    return Stroke(_tf(pts, x, y, s, angle), 1.0, 1.0, fill=True)


def leaf_lines(x, y, s=1.0, angle=-60.0, open_=1.0, length=30.0, width=12.5, n=48, curl=0.0, veins=True):
    """A leaf: its contour (leaf_contour, the first stroke) plus midrib and side veins once it is open."""
    c = leaf_contour(x, y, s, angle, open_, length, width, n, curl)
    L = [c]
    o = clamp(open_)
    Ln = length * (0.3 + 0.7 * smooth(o))
    mid = [(u * Ln, curl * Ln * 0.28 * u * u) for u in [k / 10 for k in range(1, 10)]]
    L.append(_S(_tf(mid, x, y, s, angle), 0.6, 0.8))
    if veins and o > 0.6:
        wd = width * (0.1 + 0.9 * smooth(clamp((o - 0.15) / 0.85)))
        for u in (0.3, 0.46, 0.62, 0.78):
            prof = (math.sin(math.pi * u ** 0.82) ** 0.9) * (1 - 0.22 * u)
            for side in (-1, 1):
                b0 = (u * Ln, curl * Ln * 0.28 * u * u)
                b1 = (u * Ln + Ln * 0.1, b0[1] + side * prof * wd * 0.36)
                L.append(_S(_tf([b0, b1], x, y, s, angle), 0.45, 0.55 * clamp((o - 0.6) / 0.4)))
    return L


def leaf_sites(x, y, s=1.0, angle=-82.0, **shoot_kw):
    """The SEVEN leaves of the grafted shoot, for a shoot drawn with shoot_lines(x, y, s, angle, ...): four on
    the upper bud, three on the lower. Returns [dict(x, y, angle, length, width, order)], order 0..6 = the
    order they open (upper bud first)."""
    A = shoot_anchor(x, y, s, angle, **shoot_kw)
    (lx, ly, la), (ux, uy, ua) = A['buds']
    tx, ty = A['tip']
    out = []
    for k, (da, ln, wd) in enumerate(((-6, 34, 14), (46, 30, 12.5), (-52, 28, 12), (96, 25, 11))):
        out.append(dict(x=lerp(ux, tx, 0.35 + 0.1 * k), y=lerp(uy, ty, 0.35 + 0.1 * k), angle=ua + 28 + da, length=ln, width=wd, order=k))
    for k, (da, ln, wd) in enumerate(((2, 32, 13.5), (-44, 26, 11.5), (50, 27, 11.5))):
        out.append(dict(x=lx, y=ly, angle=la - 14 + da, length=ln, width=wd, order=4 + k))
    return out


def graft_lines(x, y, s=1.0, t=0.0, cleft=1.0, shoot=1.0, knuckle=1.0, buds=1.0, set_=1.0, wound=1.0, leaves=1.0,
                angle=-82.0, ground=True, slope=0.0):
    """The strokes of graft_set(), in drawing order, as one list."""
    A = stump_anchor(x, y, s, cleft)
    L = []
    if ground:
        gx0, gx1 = x - 150 * s, x + 170 * s
        L.append(Stroke([(gx0, y + (gx0 - x) * slope + 1.5 * s), (x - 36 * s, y + 1.4 * s)], 1.2, 1.0))
        L.append(Stroke([(x + 43 * s, y + 1.4 * s), (gx1, y + (gx1 - x) * slope + 1.5 * s)], 1.2, 1.0))
    grip = clamp(set_) if shoot > 0 else 0.0
    L += stump_lines(x, y, s, cleft, grip)
    if shoot > 0:
        wx, wy = A['cleft']
        wy -= (1 - clamp(set_)) * 40 * s                              # set_ 0: held 40 units above; 1: home in the cleft
        L += shoot_lines(wx, wy, s, angle, shoot, knuckle, buds)
        if wound > 0:
            L += binding_lines(x, y - 20.6 * s, s, 23.4, 3.0, 2.7, wound, tail=9.0, band=1.7)
        if leaves > 0:
            for site in leaf_sites(wx, wy, s, angle, grow=shoot, knuckle=knuckle):
                o = clamp(leaves * 2.6 - site['order'] * 0.26)
                if o > 0:
                    flut = 2.5 * math.sin(t * 1.6 + site['order'] * 1.9) * o
                    L += leaf_lines(site['x'], site['y'], s, site['angle'] + flut, o, site['length'], site['width'],
                                    curl=0.25 * math.sin(site['order'] * 2.1))
    return L


def graft_set(ink, x, y, s=4.0, t=0.0, cleft=1.0, shoot=1.0, knuckle=1.0, buds=1.0, set_=1.0, wound=1.0, leaves=1.0,
              angle=-82.0, ground=True, slope=0.0, progress=1.0, **pencil_kw):
    """The whole graft at (x, y) = the ground under the middle of the stump, in pencil.

    cleft    0..1 the split in the stump opens          shoot   0 = no shoot; else its `grow` (0+ stub .. 1 shoot)
    knuckle  0..1 pencil stub -> knuckled shoot         buds    0..1
    set_     0 = the wedge is held 40 units above the cleft, 1 = set home (the cleft grips it)
    wound    0..1 the binding goes on, three turns      leaves  0..1 the seven leaves open in order
    Returns {'cleft', 'rim', 'cut', 'bind', 'sites': the seven leaf sites, 'wedge': where the wedge point is}."""
    L = graft_lines(x, y, s, t, cleft, shoot, knuckle, buds, set_, wound, leaves, angle, ground, slope)
    pencil(ink, L, progress, **pencil_kw)
    A = stump_anchor(x, y, s, cleft)
    wx, wy = A['cleft'][0], A['cleft'][1] - (1 - clamp(set_)) * 40 * s
    A['wedge'] = (wx, wy)
    A['sites'] = leaf_sites(wx, wy, s, angle, grow=shoot, knuckle=knuckle) if shoot > 0 else []
    return A


# =========================================================================== stills ===

def _ink(k=0, color=PAPER):
    from kit import Ink
    ink = Ink(k / FPS, k, (W, H), boil=8, wobble=1.2, seed=0)
    ink.paper(color)
    return ink


def _stills():
    out = FILMS / 'stills' / 'cowpath_sets'
    out.mkdir(parents=True, exist_ok=True)

    def save(ink, name):
        ink.finish().save(out / name)
        print('  ', name)

    # --- act 1
    ink = _ink()
    stage_back(ink, 2.5)
    stage_front(ink, 2.5)
    save(ink, 'a1_01_bare_hill.png')

    ink = _ink(30)
    stage_back(ink, 1.0, lamp=0.35, lamp_xy=(LAMP[0], 330))
    stage_front(ink, 1.0)
    save(ink, 'a1_02_lamp_rising.png')

    ink = _ink(60)
    pr = [path_at(u)[:3] for u in [k / 60 for k in range(2, 60)]]
    stage_back(ink, 14.0, prints=pr)
    stage_front(ink, 14.0)
    save(ink, 'a1_03_prints.png')

    ink = _ink(90)
    stage_back(ink, 19.0, worn=1.0, wear=1.0)
    stage_front(ink, 19.0)
    save(ink, 'a1_04_worn.png')

    ink = _ink(120)
    stage_back(ink, 22.0, worn=1.0, tree_fall=0.55)
    town(ink, 22.0, grow=0.5)
    stage_front(ink, 22.0)
    save(ink, 'a1_05_town_growing_tree_falling.png')

    ink = _ink(150)
    stage_back(ink, 27.0, worn=1.0, tree_fall=None, boulder_broken=None, bog_fill=1.0)
    town(ink, 27.0, grow=1.0, lit=0.0)
    fence(ink, post=1, rail=0.7)
    stage_front(ink, 27.0)
    save(ink, 'a1_06_town_fence.png')

    ink = _ink(180)
    u = 0.56
    stage_back(ink, 30.0, worn=1.0, paved=u, tree_fall=None, boulder_broken=None, bog_fill=1.0)
    town(ink, 30.0, grow=1.0, lit=0.6)
    px, py, hd = path_at(u)
    steam_roller(ink, px, py, 0.5, 30.0, roll=PATH_LEN * u, tilt=hd)
    stage_front(ink, 30.0)
    save(ink, 'a1_07_paving.png')

    ink = _ink(200)
    stage_back(ink, 33.0, worn=1.0, paved=1.0, tree_fall=None, boulder_broken=None, bog_fill=1.0)
    town(ink, 33.0, grow=1.0, lit=1.0)
    stage_front(ink, 33.0)
    save(ink, 'a1_08_paved.png')

    for k, hu in enumerate((0.3, 0.6, 0.85, 1.0)):
        ink = _ink(210 + k)
        stage_back(ink, 34.0, worn=1.0, paved=1.0, tree_fall=None, boulder_broken=None, bog_fill=1.0)
        town(ink, 34.0, grow=1.0, lit=1.0)
        stage_front(ink, 34.0)
        handover(ink, hu)
        save(ink, 'a1_09_handover_%d.png' % k)

    # the machines and props, big
    ink = _ink(5)
    backlight(ink, lamp_xy=(480, 200))
    ink.d.rectangle([0, 400, W, H], fill=BLACK + (255,))
    steam_roller(ink, 250, 400, 2.2, 0.4, roll=130.0)
    hand_roller(ink, 560, 400, 2.0, roll=40)
    cart(ink, 760, 400, 2.0, roll=20, load=1.0)
    cart(ink, 760, 250, 1.4, roll=50, load=1.0, tip=1.0)
    save(ink, 'a1_10_machines.png')

    ink = _ink(6)
    backlight(ink, lamp_xy=(480, 200))
    ink.d.rectangle([0, 430, W, H], fill=BLACK + (255,))
    for k, (kind, r1, r2) in enumerate((('cottage', 0.5, 0), ('cottage', 1, 0.0), ('cottage', 1, 0.5), ('cottage', 1, 1), ('tall', 1, 1), ('long', 1, 1), ('barn', 1, 1))):
        house(ink, 70 + k * 108, 430, 2.0, rise=r1, roof=r2, kind=kind, lit=1.0 if k > 3 else 0)
    spire(ink, 860, 430, 2.0, 1, 1, lit=1)
    for k, r in enumerate((0.0, 0.5, 1.0)):
        spire(ink, 120 + k * 150, 200, 1.2, 1, r)
    tree(ink, 0, 0, 620, 210, 1.15)
    tree(ink, 0, 0.6, 760, 210, 1.15)
    boulder(ink, 880, 190, 1.5)
    boulder(ink, 880, 250, 1.5, broken=1)
    save(ink, 'a1_11_houses_tree.png')

    # --- act 2
    cx, cy = 300, 470
    ink = _ink(0)
    paper_ground(ink)
    desk_set(ink, cx, cy, 1.0, t=0.3, pile=3, hours=9.2)
    save(ink, 'a2_01_desk.png')
    for k, pr_ in enumerate((0.25, 0.6)):
        ink = _ink(10 + k)
        paper_ground(ink)
        desk_set(ink, cx, cy, 1.0, t=0.3, pile=0, progress=pr_)
        save(ink, 'a2_02_desk_drawing_on_%d.png' % k)
    ink = _ink(20)
    paper_ground(ink)
    A = desk_set(ink, cx, cy, 1.0, t=7.1, pile=58, hours=11.7, mess=0.8, stamp_at=None, pull=1.0, brush=False, blanks=3)
    pencil(ink, on_sheet(A['sheet'], path_stroke()), width=1.0)
    pencil(ink, hoofprint_lines(A['mark'][0], A['mark'][1], 0.55, 20))
    save(ink, 'a2_03_desk_busy.png')
    ink = _ink(30)
    paper_ground(ink)
    A = desk_layout(cx, cy, 1.0)
    pencil(ink, floor_lines(*A['desk']) + desk_lines(*A['desk']))
    pencil(ink, stack_lines(A['stack'][0] - 30, A['stack'][1], 1.0, 128, mess=1.0, lean=0.12))
    pencil(ink, stack_contour(A['stack'][0] - 30, A['stack'][1], 1.0, 128, mess=1.0, lean=0.12), color=(150, 60, 50), width=1.2)
    save(ink, 'a2_04_pile_over_her_head.png')

    ink = _ink(40)
    paper_ground(ink)
    pencil(ink, stamp_lines(110, 200, 2.6, lift=0))
    pencil(ink, stamp_lines(260, 200, 2.6, lift=14, tilt=-14))
    pencil(ink, stamp_lines(400, 200, 2.6, squash=1))
    pencil(ink, pad_lines(40, 330, 2.4))
    pencil(ink, hoofprint_lines(250, 310, 2.6, 15))
    pencil(ink, hoofprint_lines(350, 310, 2.6, -10, ink_=0.4))
    pencil(ink, clock_lines(560, 150, 2.0, 3.6, t=0.3))
    pencil(ink, pot_lines(720, 250, 2.4))
    pencil(ink, brush_lines(690, 330, 2.0, -12))
    pencil(ink, lever_lines(860, 300, 1.9, 0.0))
    pencil(ink, lever_lines(860, 520, 1.9, 1.0))
    pencil(ink, tray_lines(420, 500, 1.5, n=4))
    pencil(ink, tray_lines(640, 500, 1.5, n=16, mess=0.7))
    save(ink, 'a2_05_pieces.png')

    ink = _ink(50)
    paper_ground(ink)
    pencil(ink, lamp_lines(150, 440, 2.0, 0.2, 0.0))
    pencil(ink, lamp_lines(420, 440, 2.0, 0.2, -0.8, on=0))
    pencil(ink, lamp_lines(700, 440, 2.0, 0.2, 0.9, nod=-20))
    b = (560, 250)
    pencil(ink, board_lines(*b, 2.0) + sheet_lines(*b, 2.0) + pegbar_lines(*b, 2.0))
    save(ink, 'a2_06_lamp_board.png')

    # --- orchard
    ink = _ink(60)
    paper_ground(ink)
    for k, (cl, sh, kn, bd, st, wn, lv) in enumerate(((0, 0, 0, 0, 0, 0, 0), (1, 0.0001, 0, 0, 0, 0, 0), (1, 1, 1, 1, 0.4, 0, 0), (1, 1, 1, 1, 1, 0.6, 0), (1, 1, 1, 1, 1, 1, 1))):
        graft_set(ink, 100 + k * 190, 470, 3.0, t=1.0, cleft=cl, shoot=sh, knuckle=kn, buds=bd, set_=st, wound=wn, leaves=lv)
    for k, g in enumerate((0, 0.33, 0.66, 1.0)):
        pencil(ink, shoot_lines(70 + k * 60, 200, 2.4, -82, grow=g, knuckle=g, buds=clamp(g * 1.5 - 0.5)))
    pencil(ink, knife_lines(330, 120, 2.2, 14))
    pencil(ink, shaving_lines(340, 200, 2.2, 1.0))
    for k, o in enumerate((0.0, 0.3, 0.6, 1.0)):
        pencil(ink, leaf_lines(600 + k * 70, 210, 2.6, -70, o))
    pencil(ink, leaf_lines(880, 120, 2.6, 30, 1.0, curl=0.7))
    save(ink, 'or_01_graft_stages.png')

    ink = _ink(70)
    paper_ground(ink)
    a = stack_contour(520, 480, 1.0, 110, mess=1.0, lean=0.1)
    b2 = ground_with_stump(560, 420, 4.0, slope=0.05)
    for k, u in enumerate((0.0, 0.35, 0.7, 1.0)):
        pencil(ink, transform(morph(a, b2, u, 120), dx=0, dy=-0), alpha=0.35 + 0.65 * (k == 3 or k == 0), seed=k)
    save(ink, 'or_02_heap_to_stump.png')

    ink = _ink(80)
    paper_ground(ink)
    A = graft_set(ink, 480, 470, 5.0, t=2.0)
    save(ink, 'or_03_graft_in_leaf.png')
    # --- with the cow (cast.py is another builder's; skipped if it has moved on)
    try:
        import cast
        ink = _ink(90)
        stage_back(ink, 26.0, worn=1.0, tree_fall=None, boulder_broken=None, bog_fill=1.0)
        town(ink, 26.0, grow=1.0)
        fence(ink, post=0.4, rail=0.0)
        for u_, kind in ((0.19, 'lead'), (0.47, 'herd'), (0.9, 'herd')):
            px, py, hd = path_at(u_)
            cast.place(ink, cast.POSES['stand'], px, py, s=0.55, style='shadow', tilt=hd * 0.5, kind=kind)
        stage_front(ink, 26.0)
        save(ink, 'check_a1_with_cows.png')
        ink = _ink(91)
        paper_ground(ink)
        A = desk_set(ink, 300, 470, 1.0, t=1.0, pile=22, hours=10.4, mess=0.5)
        pencil(ink, on_sheet(A['sheet'], path_stroke()), width=1.0)
        cast.place(ink, cast.draw_pose(0.6, 0.5, 1.0), 300, 470, s=1.0, style='line')
        save(ink, 'check_a2_with_cow.png')
    except Exception as e:                                                    # noqa: BLE001
        print('   (no check with the cast: %r)' % (e,))
    print('stills ->', out)


if __name__ == '__main__':
    _stills()
