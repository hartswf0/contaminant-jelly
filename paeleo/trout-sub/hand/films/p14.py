"""p14 · Tower · a crimson maple leaf sinks through painted glass.

Lineage: atmospheric multiplane cutout animation. Five sheets of glass are painted (in code, stroke by
stroke) with a murky river, stacked one by one on a wooden stand over a light box, and one real maple leaf
(a foraged photograph, cut out with a scalpel on the bench) is laid on a clear carrier sheet between them.
Then the same stack is seen through Turkey's porthole, and from the river side.

Rule (Seasonal Timer): the leaf falls as a clock falls: even beats, left, right, one notch lower per swing.

    python3 films/p14.py --stills 2 6 10 14 18 22 26 30
    python3 films/p14.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import *  # noqa
from kit_anim import contact, forage, load_audio  # noqa

SLUG = "p14"
D_PAINT = 1.9      # critic: time added on the bench so the top sheet's weed is painted in front of us
SECONDS = 32.0 + D_PAINT
T2 = 12.6 + D_PAINT          # cut: bench -> through the porthole
T3 = 22.2 + D_PAINT          # cut: the river side
SRC = HERE / "sources" / SLUG
CACHE = SRC / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
VER = "v2"

PW, PH = 1440, 900          # one sheet of glass, in paint pixels
MURK = np.array([34, 86, 88], np.float32)


# ------------------------------------------------------------------ helpers ---

def vnoise(shape, sx, sy=None, seed=0, octaves=1):
    """Smooth value noise in 0..1."""
    h, w = shape
    sy = sy or sx
    rs = np.random.RandomState(seed)
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw, gh = max(2, int(w / (sx / 2 ** o)) + 2), max(2, int(h / (sy / 2 ** o)) + 2)
        g = Image.fromarray((rs.rand(gh, gw) * 255).astype(np.uint8))
        out += amp * np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 255
        tot += amp
        amp *= 0.5
    return out / tot


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def cached(name, fn):
    p = CACHE / f"{name}_{VER}.png"
    if p.exists():
        return Image.open(p).copy()
    im = fn()
    im.save(p)
    return im


def catmull(pts, per=8):
    pts = [np.array(p, np.float32) for p in pts]
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return [tuple(map(float, p)) for p in out]


# ------------------------------------------------------- paint on glass ---
# A sheet is painted the way the glass was: a loaded brush, stroke after stroke. Each stroke is a few
# bristle tracks of slightly different colour and load; thin paint lets the light box through.

class Sheet:
    def __init__(self, seed, size=(PW, PH)):
        self.w, self.h = size
        self.col = Image.new("RGB", size, (0, 0, 0))
        self.cov = Image.new("RGB", size, (0, 0, 0))       # R: coverage, G: paint height
        self.dc = ImageDraw.Draw(self.col, "RGBA")
        self.dv = ImageDraw.Draw(self.cov, "RGBA")
        self.rs = np.random.RandomState(seed)

    def stroke(self, pts, color, width, load=0.85, bristles=None):
        """One brush stroke along pts."""
        rs = self.rs
        n = bristles or max(2, int(width / 4.5))
        pts = np.array(pts, np.float32)
        d = np.gradient(pts, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6)
        L = len(pts)
        for b in range(n):
            off = (b / max(1, n - 1) - 0.5) * width if n > 1 else 0.0
            off += rs.uniform(-0.6, 0.6)
            a0, a1 = int(rs.uniform(0, 0.12) * L), L - int(rs.uniform(0, 0.22) * L)   # bristles lift early
            p = pts[a0:max(a0 + 2, a1)] + nrm[a0:max(a0 + 2, a1)] * off
            jj = rs.uniform(-7, 7)
            c = tuple(int(np.clip(v + jj, 0, 255)) for v in color)
            al = int(255 * np.clip(load * rs.uniform(0.6, 1.1), 0, 1))
            wd = max(2, int(round(width / n * rs.uniform(1.5, 2.4))))
            nn = nrm[a0:max(a0 + 2, a1)]
            taper = np.sin(np.linspace(0.25, math.pi - 0.12, len(p)))[:, None] ** 0.5
            xy = [tuple(q) for q in (p + nn * wd / 2 * taper)] + [tuple(q) for q in (p - nn * wd / 2 * taper)[::-1]]
            self.dc.polygon(xy, fill=c + (al,))
            hgt = int(rs.uniform(60, 255))
            self.dv.polygon(xy, fill=(255, hgt, 0, al))

    def blob(self, x, y, rx, ry, ang, color, load=0.95):
        rs = self.rs
        pts = []
        for k in range(14):
            a = 2 * math.pi * k / 14
            r = rs.uniform(0.82, 1.08)
            px, py = rx * r * math.cos(a), ry * r * math.sin(a)
            pts.append((x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)))
        c = tuple(int(np.clip(v, 0, 255)) for v in color)
        self.dc.polygon(pts, fill=c + (int(255 * load),))
        self.dv.polygon(pts, fill=(255, int(rs.uniform(60, 255)), 0, int(255 * load)))

    def dab(self, x, y, ang, length, width, color, load=0.85, curve=0.0):
        n = max(3, int(length / 10))
        pts = []
        for k in range(n + 1):
            f = k / n - 0.5
            a = ang + curve * f
            pts.append((x + math.cos(ang) * length * f - math.sin(a) * curve * length * 0.12 * (f * f - 0.25) * 4,
                        y + math.sin(ang) * length * f + math.cos(a) * curve * length * 0.12 * (f * f - 0.25) * 4))
        self.stroke(pts, color, width, load)

    def fill_poly(self, pts, colfn, ang=0.0, wide=16, long=60, load=0.9, dens=1.0, angj=0.35, edge=True):
        """Fill a polygon with strokes. colfn(x, y) -> rgb."""
        rs = self.rs
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
        box = m.getbbox()
        if not box:
            return
        a = np.asarray(m)
        area = int((a > 0).sum())
        n = int(dens * area / (wide * long) * 3.2) + 3
        ys, xs = np.nonzero(a[box[1]:box[3], box[0]:box[2]])
        tmp = Sheet(int(rs.randint(1 << 30)), (self.w, self.h))
        if load >= 0.7:           # undercoat: the shape blocked in first with a full brush
            cy = (box[1] + box[3]) / 2
            for yy in range(box[1], box[3], 6):
                c = tuple(int(v) for v in colfn((box[0] + box[2]) / 2, yy))
                tmp.dc.rectangle([box[0], yy, box[2], yy + 6], fill=c + (255,))
            tmp.dv.rectangle(box, fill=(int(255 * min(1, load)), 90, 0, 255))
        idx = rs.randint(0, len(xs), n)
        for k in idx:
            x, y = xs[k] + box[0], ys[k] + box[1]
            tmp.dab(x, y, ang + rs.uniform(-angj, angj), long * rs.uniform(0.5, 1.2), wide * rs.uniform(0.6, 1.25),
                    colfn(x, y), load * rs.uniform(0.75, 1.0), curve=rs.uniform(-0.8, 0.8))
        # the brush stays inside the shape, with a slightly ragged painted edge
        mm = m.filter(ImageFilter.GaussianBlur(1.2))
        if edge:
            rag = to_img(vnoise((self.h, self.w), 9, seed=int(rs.randint(1 << 30))) * 255)
            mm = ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(2.5)).point(lambda v: min(255, v * 2)),
                                     rag.point(lambda v: 255 if v > 70 else int(v * 3.6)))
            mm = ImageChops.lighter(mm, m.filter(ImageFilter.MinFilter(7)))
        cv = np.asarray(tmp.cov, np.float32)
        al = to_img(cv[..., 0] * (np.asarray(mm, np.float32) / 255))
        self.col.paste(tmp.col, (0, 0), al)
        self.cov.paste(tmp.cov, (0, 0), al)
        self.dc = ImageDraw.Draw(self.col, "RGBA")
        self.dv = ImageDraw.Draw(self.cov, "RGBA")

    def finish(self, opaque=False, thin=0.0, relief=1.0):
        """-> RGBA: colour lit across the paint relief, alpha from how loaded the brush was."""
        col = np.asarray(self.col, np.float32)
        cv = np.asarray(self.cov, np.float32)
        cover = cv[..., 0] / 255
        hgt = np.asarray(to_img(cv[..., 1]).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
        gx = np.gradient(hgt, axis=1)
        gy = np.gradient(hgt, axis=0)
        lit = np.clip((-gx - gy) * 0.022 * relief, -0.16, 0.2)
        col = col * (1 + lit[..., None])
        streak = 0.82 + 0.18 * (hgt / 255)
        alpha = np.clip(cover * (1 - thin * (1 - streak)), 0, 1)
        if opaque:
            alpha[:] = 1
        out = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
        return Image.fromarray(out, "RGBA")


def grad(stops):
    """colour by height: stops [(y, rgb), ...] -> fn(x, y)."""
    ys = [s[0] for s in stops]
    cs = np.array([s[1] for s in stops], np.float32)

    def fn(x, y):
        return tuple(np.array([np.interp(y, ys, cs[:, k]) for k in range(3)]))
    return fn


def jit(fn, rs, amt=10, tint=(0, 0, 0)):
    def g(x, y):
        c = fn(x, y)
        j = rs.uniform(-amt, amt)
        return tuple(float(np.clip(v + j + t, 0, 255)) for v, t in zip(c, tint))
    return g


def blade_poly(x, y, length, width, lean, sway=0.0, n=9):
    """A water-weed blade from root (x, y) upward."""
    L, R = [], []
    for k in range(n + 1):
        f = k / n
        cx = x + lean * length * f * f + sway * math.sin(f * 3.0) * length * 0.1
        cy = y - length * f
        w = width * (1 - f) ** 0.7 * (0.55 + 0.45 * math.sin(math.pi * min(1, f * 1.6 + 0.15)))
        L.append((cx - w / 2, cy))
        R.append((cx + w / 2, cy))
    return L + R[::-1]


def mound(x0, x1, base, height, seed, n=10, skew=0.0):
    rs = np.random.RandomState(seed)
    top = []
    for k in range(n + 1):
        f = k / n
        yy = base - height * (math.sin(math.pi * f) ** 0.6) * rs.uniform(0.82, 1.0)
        top.append((lerp(x0, x1, f) + skew * height * math.sin(math.pi * f), yy))
    return catmull([(x0, base)] + top[1:-1] + [(x1, base)], 6) + [(x1, base + 40), (x0, base + 40)]


def paint_back():
    """Sheet 0: the painted board at the bottom of the stack: the light of the surface, falling off."""
    s = Sheet(1)
    rs = s.rs
    g = grad([(0, (188, 214, 176)), (150, (118, 176, 158)), (380, (52, 124, 122)), (640, (26, 78, 86)), (900, (14, 46, 58))])
    for k in range(2600):
        x, y = rs.uniform(-40, PW + 40), rs.uniform(-20, PH + 20)
        c = g(x, y)
        j = rs.uniform(-10, 10)
        s.dab(x, y, rs.uniform(-0.12, 0.12), rs.uniform(90, 260), rs.uniform(18, 44), tuple(v + j for v in c), 0.9, rs.uniform(-0.5, 0.5))
    # shafts of surface light, dragged down with a dry brush
    for k in range(9):
        x = rs.uniform(80, PW - 80)
        for q in range(26):
            y = rs.uniform(0, 520)
            f = 1 - y / 560
            s.dab(x + y * 0.22 + rs.uniform(-26, 26), y, 1.36 + rs.uniform(-0.05, 0.05), rs.uniform(120, 260), rs.uniform(8, 22),
                  (206, 226, 190), 0.16 * f, 0)
    # far bank: a darker band low down
    for k in range(500):
        x, y = rs.uniform(-40, PW + 40), rs.uniform(650, 900)
        s.dab(x, y, rs.uniform(-0.2, 0.2), rs.uniform(60, 160), rs.uniform(14, 30), (16 + rs.uniform(-5, 5), 50 + rs.uniform(-8, 8), 60 + rs.uniform(-8, 8)), 0.5)
    return s.finish(opaque=True, relief=0.8)


def paint_far():
    """Sheet 1: far boulders and thread-thin weed, thin paint."""
    s = Sheet(2)
    rs = s.rs
    base = 700
    for (x0, x1, h, sd) in [(-60, 330, 150, 1), (250, 560, 90, 2), (640, 900, 120, 3), (860, 1230, 190, 4), (1150, 1500, 120, 5)]:
        c = grad([(base - h, (60, 118, 112)), (base, (30, 78, 84))])
        s.fill_poly(mound(x0, x1, base, h, sd), jit(c, rs, 8), ang=0.25, wide=20, long=70, load=0.8)
    c = grad([(680, (34, 84, 88)), (900, (18, 56, 66))])
    top = [(x, 694 + 16 * math.sin(x / 170.0 + 1) + 9 * math.sin(x / 61.0)) for x in range(-20, PW + 40, 36)]
    s.fill_poly(top + [(PW + 20, PH), (-20, PH)], jit(c, rs, 7), ang=0.0, wide=22, long=110, load=0.85, edge=False)
    for k in range(34):
        x = rs.uniform(0, PW)
        ln = rs.uniform(120, 330)
        s.fill_poly(blade_poly(x, 705 + rs.uniform(-10, 30), ln, rs.uniform(7, 13), rs.uniform(-0.25, 0.25), rs.uniform(-1, 1)),
                    jit(grad([(300, (74, 132, 112)), (720, (36, 88, 84))]), rs, 9), ang=-1.57, wide=5, long=60, load=0.75, dens=1.6, angj=0.15, edge=False)
    return s.finish(thin=0.5)


def paint_mid():
    """Sheet 2: rocks with moss, a sunk branch, weed."""
    s = Sheet(3)
    rs = s.rs
    base = 760
    rock = grad([(480, (96, 128, 110)), (640, (58, 92, 90)), (780, (26, 58, 66))])
    for (x0, x1, h, sd, sk) in [(-80, 300, 250, 11, 0.1), (200, 470, 110, 12, 0), (980, 1300, 150, 13, -0.1), (1180, 1520, 290, 14, -0.12)]:
        pts = mound(x0, x1, base, h, sd, skew=sk)
        s.fill_poly(pts, jit(rock, rs, 10), ang=0.5, wide=24, long=64, load=0.95)
        # moss caps, stippled
        top = min(p[1] for p in pts)
        for q in range(int((x1 - x0) * 0.5)):
            x = rs.uniform(x0 + 30, x1 - 30)
            y = top + rs.uniform(0, 60) + abs(x - (x0 + x1) / 2) * 0.35
            s.dab(x, y, rs.uniform(-0.4, 0.4), rs.uniform(10, 26), rs.uniform(5, 10), (96 + rs.uniform(-14, 14), 134 + rs.uniform(-14, 14), 70 + rs.uniform(-10, 10)), 0.7)
    # a sunk branch: dry strokes, lighter along the top
    for pts, wd in (([(440, 748), (540, 716), (650, 700), (742, 664), (808, 610), (842, 548)], 13), ([(650, 700), (720, 712), (790, 736)], 7),
                    ([(742, 664), (736, 610), (752, 566)], 6), ([(808, 610), (850, 600), (884, 570)], 5)):
        c = catmull(pts, 8)
        s.stroke(c, (40, 54, 52), wd, 0.95)
        s.stroke([(x - 1, y - wd * 0.28) for x, y in c], (92, 106, 88), max(2, wd * 0.3), 0.7, bristles=2)
    bed = grad([(740, (44, 84, 80)), (900, (20, 50, 58))])
    top = [(x, 752 + 14 * math.sin(x / 150.0 + 2) + 8 * math.sin(x / 53.0)) for x in range(-20, PW + 40, 36)]
    s.fill_poly(top + [(PW + 20, PH), (-20, PH)], jit(bed, rs, 8), ang=0.0, wide=20, long=90, load=0.95, edge=False)
    for k in range(26):
        x = rs.choice([rs.uniform(0, 420), rs.uniform(980, PW)])
        ln = rs.uniform(170, 430)
        s.fill_poly(blade_poly(x, 770 + rs.uniform(-10, 30), ln, rs.uniform(12, 22), rs.uniform(-0.3, 0.3), rs.uniform(-1, 1)),
                    jit(grad([(300, (88, 140, 92)), (780, (30, 82, 70))]), rs, 10), ang=-1.57, wide=7, long=70, load=0.9, dens=1.7, angj=0.15, edge=False)
    return s.finish(thin=0.3)


def paint_near():
    """Sheet 3: the bed the tin sits on: pebbles, two stones, weed at the sides."""
    s = Sheet(4)
    rs = s.rs
    bed = grad([(780, (62, 92, 78)), (900, (30, 58, 56))])
    top = [(x, 800 + 14 * math.sin(x / 130.0) + 8 * math.sin(x / 47.0)) for x in range(-20, PW + 40, 40)]
    s.fill_poly(top + [(PW + 20, PH), (-20, PH)], jit(bed, rs, 9), ang=0.0, wide=22, long=80, load=1.0, edge=False)
    for k in range(520):       # pebbles: one loaded dab each, a lighter touch on top
        x, y = rs.uniform(0, PW), rs.uniform(806, 896)
        r = rs.uniform(7, 19) * (0.6 + (y - 800) / 160)
        c = np.array([(120, 116, 92), (86, 104, 96), (146, 128, 96), (70, 86, 84), (110, 96, 84)][rs.randint(5)], np.float32) * rs.uniform(0.7, 1.0)
        an = rs.uniform(-0.4, 0.4)
        s.blob(x + r * 0.12, y + r * 0.22, r * 1.05, r * 0.7, an, tuple(c * 0.45), 0.8)
        s.blob(x, y, r, r * 0.66, an, tuple(c))
        s.blob(x - r * 0.2, y - r * 0.2, r * 0.55, r * 0.25, an, tuple(np.minimum(255, c * 1.3 + 12)), 0.55)
    rock = grad([(600, (92, 112, 96)), (720, (62, 84, 80)), (830, (28, 52, 58))])
    for (x0, x1, h, sd) in [(-120, 190, 190, 21), (1290, 1560, 150, 22)]:
        s.fill_poly(mound(x0, x1, 812, h, sd), jit(rock, rs, 10), ang=0.6, wide=24, long=60, load=1.0)
    for k in range(22):
        x = rs.choice([rs.uniform(-10, 250), rs.uniform(1230, PW + 10)])
        ln = rs.uniform(200, 520)
        s.fill_poly(blade_poly(x, 815 + rs.uniform(-6, 30), ln, rs.uniform(16, 30), rs.uniform(-0.28, 0.28), rs.uniform(-1, 1)),
                    jit(grad([(300, (70, 128, 78)), (820, (22, 70, 58))]), rs, 10), ang=-1.57, wide=8, long=80, load=0.95, dens=1.8, angj=0.12, edge=False)
    return s.finish(thin=0.15)


def front_blades():
    """The weed blades of the front sheet: (left side?, root x, length, width, lean, sway), in the order they are painted."""
    rs = np.random.RandomState(55)
    out = []
    for k in range(30):
        side = rs.rand() < 0.5
        x = rs.uniform(-30, 250) if side else rs.uniform(PW - 250, PW + 30)
        out.append((side, x, rs.uniform(300, 760), rs.uniform(26, 50), (0.22 if side else -0.22) + rs.uniform(-0.2, 0.2), rs.uniform(-1, 1)))
    return out


def blade_axis(x, ln, lean, sway, f):
    """Centre line of blade_poly at fraction f of its length (paint px)."""
    return x + lean * ln * f * f + sway * math.sin(f * 3.0) * ln * 0.1, 910 - ln * f


def paint_front():
    """Sheet 4: nearest the lens: black-green weed at the edges, and a veil of thin murk."""
    s = Sheet(5)
    rs = s.rs
    for k in range(150):        # the veil: dry, thin, wide strokes
        x, y = rs.uniform(0, PW), rs.uniform(0, PH)
        s.dab(x, y, rs.uniform(-0.1, 0.25), rs.uniform(160, 420), rs.uniform(26, 60), (70 + rs.uniform(-10, 10), 118 + rs.uniform(-10, 10), 108 + rs.uniform(-10, 10)), 0.10)
    dark = grad([(200, (22, 62, 50)), (900, (6, 26, 28))])
    for (side, x, ln, wd, lean, sway) in front_blades():
        s.fill_poly(blade_poly(x, 910, ln, wd, lean, sway),
                    jit(dark, rs, 6), ang=-1.57, wide=10, long=90, load=1.0, dens=1.8, angj=0.12, edge=False)
    # an overhanging root, top left
    root = catmull([(-30, 60), (120, 90), (260, 60), (380, 120), (470, 100)], 8)
    s.stroke(root, (14, 38, 36), 30, 1.0)
    s.stroke(catmull([(260, 60), (300, 150), (290, 230)], 6), (14, 38, 36), 12, 1.0)
    s.stroke(catmull([(120, 90), (150, 170), (190, 210)], 6), (14, 38, 36), 9, 1.0)
    for (x0, x1, h, sd) in [(-140, 160, 120, 31), (1310, 1580, 100, 32)]:
        s.fill_poly(mound(x0, x1, 900, h, sd), jit(dark, rs, 6), ang=0.5, wide=24, long=60, load=1.0)
    return s.finish(thin=0.25)


PAINTERS = [paint_back, paint_far, paint_mid, paint_near, paint_front]

# ------------------------------------------------------------ the stack ---
# Six sheets. z is height above the board on the stand (bench units); the camera hangs HC above the board,
# so a sheet at z is seen at scale HC / (HC - z): that, and nothing else, is the parallax.
HC = 900.0
C = (W / 2, H / 2)
#            name     z     units per paint px
SHEETS = [("board", 0.0, 1.70), ("far", 55.0, 1.50), ("mid", 110.0, 1.30), ("carrier", 165.0, 1.25),
          ("near", 220.0, 1.15), ("front", 275.0, 1.20)]
PAINT_OF = {"board": 0, "far": 1, "mid": 2, "near": 3, "front": 4}
ZL = 165.0


def S(z):
    return HC / (HC - z)


def set_hc(v):
    """Raise or lower the camera over the stand."""
    global HC
    HC = v


def scr(X, Y, z, cam, F):
    s = F * S(z)
    return C[0] + s * (X - cam[0]), C[1] + s * (Y - cam[1])


def place(img, u, z, cam, F, off=(0.0, 0.0), size=(W, H), resample=Image.BILINEAR):
    """Project a sheet (paint image, u units per px, centred on the stack axis) to the screen."""
    a = 1.0 / (F * S(z) * u) * (img.width / PW)
    k = img.width / PW
    co = (a, 0, k * (PW / 2 + (cam[0] - off[0]) / u) - a * C[0], 0, a, k * (PH / 2 + (cam[1] - off[1]) / u) - a * C[1])
    return img.transform(size, Image.AFFINE, co, resample)


def premul_blur(im, r):
    if r <= 0:
        return im
    a = np.asarray(im, np.float32)
    al = a[..., 3:4] / 255
    pm = to_img(a[..., :3] * al).filter(ImageFilter.GaussianBlur(r))
    ab = Image.fromarray(a[..., 3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    pa = np.asarray(pm, np.float32)
    aa = np.asarray(ab, np.float32)[..., None]
    rgb = np.where(aa > 0.5, pa / np.maximum(aa / 255, 1e-3), pa)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), aa]).astype(np.uint8), "RGBA")


def hazed(im, haze, blur, dark=1.0):
    a = np.asarray(im, np.float32).copy()
    a[..., :3] = (a[..., :3] * (1 - haze) + MURK * haze) * dark
    return premul_blur(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), blur)


A = {}      # every built asset


def build_sheets():
    A["paint"] = [cached("sheet4b" if k == 4 else f"sheet{k}", fn) for k, fn in enumerate(PAINTERS)]
    for k, up in ((1, 96), (2, 64)):         # the far sheets sit higher in their frames: more to slide past
        im = A["paint"][k]
        new = Image.new("RGBA", im.size)
        new.paste(im, (0, -up))
        new.paste(im.crop((0, PH - up, PW, PH)).transpose(Image.FLIP_TOP_BOTTOM), (0, PH - up))
        A["paint"][k] = new
    hz = {"board": (0.10, 2.2, 1.0), "far": (0.40, 2.2, 1.0), "mid": (0.18, 0.9, 1.0), "near": (0.0, 0.0, 0.96), "front": (0.0, 4.5, 0.62)}
    A["river"] = {n: hazed(A["paint"][PAINT_OF[n]], *hz[n]) for n in PAINT_OF}
    A["shadow"] = {n: A["paint"][PAINT_OF[n]].getchannel("A").resize((PW // 4, PH // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
                   for n in ("far", "mid", "near", "front")}
    fog = vnoise((512, 1024), 220, 90, seed=41, octaves=3)
    for ax, n_ in ((1, 1024), (0, 512)):          # make it wrap without a seam
        wgt = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n_) / n_)
        wgt = wgt[None, :] if ax == 1 else wgt[:, None]
        fog = fog * wgt + np.roll(fog, n_ // 2, axis=ax) * (1 - wgt)
    fog = np.clip((fog - 0.38) * 2.4, 0, 1)
    A["fog"] = to_img(fog * 255).convert("L")
    # shafts of surface light
    sh = np.zeros((H, W + 400), np.float32)
    rs = np.random.RandomState(7)
    yy, xx = np.mgrid[0:H, 0:W + 400]
    for k in range(11):
        x0, wd, g = rs.uniform(0, W + 400), rs.uniform(14, 60), rs.uniform(0.3, 1.0)
        sh += g * np.exp(-((xx - x0 - yy * 0.28) / wd) ** 2)
    sh *= np.clip(1.15 - yy / (H * 0.95), 0, 1) ** 1.3
    A["shafts"] = [to_img(np.clip(sh, 0, 1) * 255).convert("L"),
                   to_img(vnoise((H, W + 400), 260, 600, seed=3, octaves=2) * 255).convert("L")]


# ------------------------------------------------------------ foraged pieces ---

def src_file(name):
    for n in (name, name.rsplit(".", 1)[0] + "_try." + name.rsplit(".", 1)[1]):
        if (SRC / n).exists():
            return SRC / n
    raise SystemExit(f"missing foraged file {name}: run the forage step")


def biggest(mask):
    from scipy import ndimage as ndi
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    return ndi.binary_fill_holes(m)


def build_leaf():
    """The photograph, and the leaf cut out of it."""
    ph = Image.open(src_file("leaf.jpg")).convert("RGB")
    a = np.asarray(ph, np.float32)
    paper = np.median(a[:12].reshape(-1, 3), axis=0)
    dist = np.abs(a - paper).sum(2)
    sat = a.max(2) - a.min(2)
    m = biggest(sat > 78)
    from scipy import ndimage as ndi
    m = ndi.binary_opening(m, iterations=1)
    m = biggest(m)
    al = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)).point(lambda v: 0 if v < 110 else min(255, (v - 110) * 4))
    box = al.getbbox()
    A["photo"] = ph
    A["photo_box"] = box
    leaf = ph.convert("RGBA")
    leaf.putalpha(al)
    A["leaf_full"] = leaf.crop(box)
    # the cut line: the contour, walked by the scalpel
    import cv2
    cs, _ = cv2.findContours((np.asarray(al) > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=len)[:, 0, :].astype(np.float32)
    k = int(np.argmax(c[:, 1]))          # start at the lowest point (the stem)
    c = np.roll(c, -k, axis=0)
    A["cut"] = c[::3]
    lw = 300
    A["leaf"] = A["leaf_full"].resize((lw, int(lw * A["leaf_full"].height / A["leaf_full"].width)), Image.LANCZOS)


def build_trout():
    im = Image.open(src_file("trout.png")).convert("RGB")
    a = np.asarray(im, np.float32)
    paper = np.median(np.concatenate([a[:20].reshape(-1, 3), a[-20:].reshape(-1, 3)]), axis=0)
    dist = np.abs(a - paper).sum(2)
    m = biggest(dist > 38)
    al = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 0 if v < 120 else min(255, (v - 120) * 4))
    box = al.getbbox()
    t = im.convert("RGBA")
    t.putalpha(al)
    t = t.crop(box)
    w = 420
    A["trout"] = t.resize((w, int(w * t.height / t.width)), Image.LANCZOS)


TURKEY_CUT = [(903, 128), (940, 112), (975, 95), (990, 40), (1003, 28), (1015, 70), (1060, 100), (1120, 140), (1140, 200), (1146, 270),
              (1158, 330), (1182, 390), (1198, 450), (1180, 500), (1100, 470), (1040, 450), (1030, 405), (1040, 350), (1015, 290),
              (1012, 230), (985, 185), (945, 160), (910, 140)]
WATTLE_CUT = [(1040, 345), (1090, 332), (1165, 360), (1174, 402), (1120, 424), (1060, 428), (1026, 405)]
TBOX = (890, 16, 1236, 510)


def build_turkey():
    im = Image.open(src_file("turkey.jpg")).convert("RGB")
    k = im.width / 1280.0

    def cut(poly):
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in catmull(poly + poly[:1], 5)], fill=255)
        a = np.asarray(im, np.float32)
        paper = np.array([233, 224, 200], np.float32)
        far = (np.abs(a - paper).sum(2) > 62) | (a.sum(2) < 520)
        from scipy import ndimage as ndi
        keep = biggest(ndi.binary_opening(far & (np.asarray(m) > 0), iterations=1))
        keep = ndi.binary_dilation(keep, iterations=1)
        m = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
        o = im.convert("RGBA")
        o.putalpha(m)
        return o.crop(tuple(int(v * k) for v in TBOX))
    A["turkey"] = cut(TURKEY_CUT)
    A["wattle"] = cut(WATTLE_CUT)
    A["tk"] = k


def turkey_img(wattle_deg=0.0, height=300):
    """Head and neck, with the wattle a separate piece on one pin."""
    base = A["turkey"].copy()
    k = A["tk"]
    pin = ((1085 - TBOX[0]) * k, (345 - TBOX[1]) * k)
    w = A["wattle"].rotate(wattle_deg, center=pin, resample=Image.BICUBIC)
    base.alpha_composite(w)
    return base.resize((int(height * base.width / base.height), height), Image.LANCZOS)


# ------------------------------------------------------------ handmade props ---

def brass_ring(r_in, r_out, bolts=6, pad=10, seed=0, bolt_r=None, start=-90.0):
    """A turned brass ring with a bevelled inner flange and hex bolts, lit from upper left."""
    R = int(r_out + pad)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    r = np.hypot(xx, yy)
    th = np.arctan2(yy, xx)
    wdt = r_out - r_in
    f = (r - r_in) / wdt                       # 0 inner edge .. 1 outer
    # height profile: inner bevel up, flat land, outer round-over
    hgt = np.where(f < 0.22, f / 0.22, np.where(f < 0.82, 1.0, np.sqrt(np.clip(1 - ((f - 0.82) / 0.18) ** 2, 0, 1))))
    dh = np.gradient(hgt, axis=1) * xx / (r + 1e-6) + np.gradient(hgt, axis=0) * yy / (r + 1e-6)
    lx, ly = -0.62, -0.78
    slope = dh * wdt * 0.9
    nx, ny = -slope * np.cos(th), -slope * np.sin(th)
    lit = 0.62 + 0.55 * (nx * lx + ny * ly) + 0.22 * (-(np.cos(th) * lx + np.sin(th) * ly)) * (f > 0.82)
    rs = np.random.RandomState(seed)
    turn = np.interp(r, np.arange(0, R * 1.5), rs.uniform(-1, 1, int(R * 1.5)))       # lathe marks
    turn = turn * 0.05 + 0.04 * np.sin(th * 2 + 0.7)
    tarn = (vnoise(r.shape, 40, seed=seed + 1, octaves=3) - 0.5) * 0.22
    base = np.array([190, 150, 66], np.float32)
    col = base[None, None] * (lit + turn + tarn)[..., None]
    col[..., 2] *= 0.9 + tarn
    al = np.clip(np.minimum(r - r_in, r_out - r) + 0.5, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([R - r_in - 1, R - r_in - 1, R + r_in + 1, R + r_in + 1], outline=(40, 28, 12, 200), width=max(1, int(wdt * 0.05)))
    d.ellipse([R - r_out, R - r_out, R + r_out, R + r_out], outline=(48, 34, 14, 170), width=1)
    br = bolt_r or wdt * 0.2
    rm = r_in + wdt * 0.55
    for b in range(bolts):
        a = math.radians(start + 360 * b / bolts)
        cx, cy = R + rm * math.cos(a), R + rm * math.sin(a)
        rot = rs.uniform(0, 1.0)
        hexa = [(cx + br * math.cos(rot + q * math.pi / 3), cy + br * math.sin(rot + q * math.pi / 3)) for q in range(6)]
        d.polygon([(x + br * 0.18, y + br * 0.26) for x, y in hexa], fill=(40, 26, 10, 150))
        d.polygon(hexa, fill=(168, 128, 52, 255), outline=(60, 42, 16, 255))
        for q in range(6):          # facets
            p0, p1 = hexa[q], hexa[(q + 1) % 6]
            mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
            l_ = (mx * lx + my * ly) / br
            c = tuple(int(np.clip(v * (0.8 + 0.5 * l_), 0, 255)) for v in (196, 154, 70))
            d.polygon([p0, p1, (cx + (p1[0] - cx) * 0.62, cy + (p1[1] - cy) * 0.62), (cx + (p0[0] - cx) * 0.62, cy + (p0[1] - cy) * 0.62)], fill=c + (255,))
        d.ellipse([cx - br * 0.6, cy - br * 0.6, cx + br * 0.6, cy + br * 0.6], fill=(206, 166, 82, 255), outline=(70, 50, 20, 220))
        d.line([(cx - br * 0.3, cy - br * 0.36), (cx + br * 0.1, cy - br * 0.46)], fill=(250, 232, 170, 220), width=max(1, int(br * 0.12)))
    return img


def steel_tex(w, h, seed, base=(142, 160, 166), ribs=0, rust=0.5):
    """Painted, dented, rusting tin plate."""
    rs = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    brush = vnoise((h, w), 90, 5, seed=seed, octaves=2) - 0.5
    blot = vnoise((h, w), 60, seed=seed + 1, octaves=3)
    a = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    a *= (1 + brush * 0.16)[..., None]
    if ribs:
        rib = np.sin(xx / ribs * 2 * math.pi)
        a *= (1 + 0.13 * rib)[..., None]
    r = np.clip((blot - (0.78 - rust * 0.3)) * 6, 0, 1)[..., None]
    a = a * (1 - r) + np.array([122, 74, 44], np.float32) * (0.8 + 0.4 * vnoise((h, w), 6, seed=seed + 2)[..., None]) * r
    return a


def build_tin():
    """Turkey's submersible: a bread-roll tin on its side, lid forward, one six-bolt brass porthole."""
    K = 2                                    # px per unit
    w, h = 400 * K, 190 * K
    pad = 70 * K
    Wd, Hd = w + 2 * pad, h + 2 * pad
    a = steel_tex(Wd, Hd, 5, ribs=15 * K, rust=0.42)
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    v = np.clip((yy - pad) / h, 0, 1)        # 0 top .. 1 bottom. A tin is a drum: a bright shoulder, a dark belly, light from the bed
    cyl = 0.40 + 0.86 * np.exp(-((v - 0.27) / 0.2) ** 2) + 0.2 * np.exp(-((v - 0.95) / 0.07) ** 2)
    dent = 1 - 0.22 * np.exp(-(((xx - pad - 300 * K) / (34 * K)) ** 2 + ((yy - pad - 150 * K) / (22 * K)) ** 2)) \
        + 0.16 * np.exp(-(((xx - pad - 292 * K) / (30 * K)) ** 2 + ((yy - pad - 138 * K) / (12 * K)) ** 2))
    a *= (cyl * dent)[..., None]
    # rust runs down from the seams
    rs = np.random.RandomState(8)
    for k in range(26):
        x0, y0, ln, wd = pad + rs.uniform(10, 390) * K, pad + rs.uniform(10, 90) * K, rs.uniform(30, 110) * K, rs.uniform(2, 6) * K
        st = np.exp(-((xx - x0) / wd) ** 2) * np.clip((yy - y0) / ln, 0, 1) * np.clip(1 - (yy - y0) / ln, 0, 1) * 2.4
        a = a * (1 - 0.5 * st[..., None]) + np.array([112, 64, 36], np.float32) * 0.5 * st[..., None]
    img = to_img(a).convert("RGBA")
    m = Image.new("L", (Wd, Hd), 0)
    md = ImageDraw.Draw(m)
    md.rounded_rectangle([pad, pad, pad + w, pad + h], radius=12 * K, fill=255)
    rims = [(pad - 2 * K, 13 * K), (pad + w - 11 * K, 13 * K)]
    for x, wd in rims:                         # rolled rims stand proud of the body
        md.rounded_rectangle([x, pad - 7 * K, x + wd, pad + h + 7 * K], radius=5 * K, fill=255)
    img.putalpha(m)
    d = ImageDraw.Draw(img, "RGBA")
    for x, wd in rims + [(pad + 74 * K, 7 * K)]:
        top, bot = (pad - 7 * K, pad + h + 7 * K) if wd > 8 * K else (pad + 2, pad + h - 2)
        for q in range(int(wd)):               # a bead: round in section
            f = q / wd
            l_ = 0.5 + 0.75 * math.sin(f * math.pi) ** 2 * (1.25 - f)
            for yy_ in range(0, 1):
                pass
            d.line([(x + q, top + 3 * K), (x + q, bot - 3 * K)], fill=tuple(int(min(255, c * l_)) for c in (176, 192, 196)) + (255,))
        d.line([(x + wd, top + 6 * K), (x + wd, bot - 6 * K)], fill=(22, 30, 36, 190), width=K)
    a2 = np.asarray(img, np.float32).copy()
    a2[..., :3] *= (0.5 + 0.7 * np.exp(-((v - 0.25) / 0.3) ** 2) + 0.15 * (v > 0.9))[..., None] * 0 + 1
    for k in range(9):                        # rivets along both rims
        y = pad + 14 * K + k * (h - 28 * K) / 8
        for x in (pad + 22 * K, pad + w - 20 * K, pad + 90 * K):
            d.ellipse([x - 4 * K, y - 3 * K, x + 5 * K, y + 5 * K], fill=(30, 40, 46, 150))
            d.ellipse([x - 4 * K, y - 4 * K, x + 4 * K, y + 4 * K], fill=(98, 112, 118, 255))
            d.ellipse([x - 3 * K, y - 4 * K, x + 1 * K, y], fill=(222, 230, 228, 255))
    d.line([(pad + 96 * K, pad + 118 * K), (pad + w - 14 * K, pad + 118 * K)], fill=(30, 40, 46, 150), width=K)      # the soldered side seam
    d.line([(pad + 96 * K, pad + 116 * K), (pad + w - 14 * K, pad + 116 * K)], fill=(226, 232, 230, 50), width=K)
    # the paper label, pasted on a little crooked, one corner lifting
    lab = Image.new("RGBA", (128 * K, 60 * K), (230, 216, 184, 255))
    ld = ImageDraw.Draw(lab)
    ld.rectangle([4 * K, 4 * K, 128 * K - 4 * K, 60 * K - 4 * K], outline=(124, 44, 40, 255), width=K)
    ld.text((64 * K, 25 * K), "ROLLS", font=font("serif", 29 * K), fill=(124, 44, 40, 255), anchor="mm")
    ld.text((64 * K, 47 * K), "ONE DOZEN · TROUT TOWN", font=font("mono", 6 * K), fill=(90, 60, 50, 255), anchor="mm")
    la = np.asarray(lab, np.float32).copy()
    ly_, lx_ = np.mgrid[0:60 * K, 0:128 * K].astype(np.float32)
    lv = (ly_ / (60 * K) * 190 * 0.3 + 0.36)
    la[..., :3] *= (0.8 + 0.24 * vnoise((60 * K, 128 * K), 30, seed=9, octaves=2))[..., None] * (0.72 + 0.5 * np.exp(-((ly_ / (60 * K) - 0.1) / 0.5) ** 2))[..., None]
    lab = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA").rotate(-3, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", lab.size, (10, 16, 20, 0))
    sh.putalpha(lab.getchannel("A").point(lambda q: int(q * 0.45)).filter(ImageFilter.GaussianBlur(2 * K)))
    img.alpha_composite(sh, (pad + 236 * K, pad + 30 * K))
    img.alpha_composite(lab, (pad + 234 * K, pad + 26 * K))
    img.putalpha(ImageChops.darker(img.getchannel("A"), m))
    d = ImageDraw.Draw(img, "RGBA")
    brass, bdark, bline = (176, 138, 60, 255), (128, 96, 40, 255), (56, 38, 14, 255)
    # lead keel
    for x0 in (112, 232):
        d.rounded_rectangle([pad + x0 * K, pad + h - 2 * K, pad + (x0 + 92) * K, pad + h + 17 * K], radius=5 * K, fill=(66, 74, 80, 255), outline=(26, 30, 34, 255), width=K)
        d.line([(pad + (x0 + 6) * K, pad + h + 2 * K), (pad + (x0 + 86) * K, pad + h + 2 * K)], fill=(128, 138, 142, 255), width=K)
        for bx in (x0 + 14, x0 + 78):
            d.ellipse([pad + bx * K - 3 * K, pad + h + 5 * K, pad + bx * K + 3 * K, pad + h + 11 * K], fill=brass, outline=bline)
    # hatch: a jar lid soldered on top, with a wire handle
    d.rounded_rectangle([pad + 176 * K, pad - 15 * K, pad + 262 * K, pad + 3 * K], radius=4 * K, fill=(150, 166, 172, 255), outline=(30, 40, 46, 255), width=K)
    d.line([(pad + 180 * K, pad - 10 * K), (pad + 258 * K, pad - 10 * K)], fill=(232, 238, 236, 255), width=K)
    for q in range(12):
        d.line([(pad + (181 + q * 7) * K, pad - 6 * K), (pad + (181 + q * 7) * K, pad + 1 * K)], fill=(70, 84, 90, 255), width=K)
    d.arc([pad + 196 * K, pad - 34 * K, pad + 242 * K, pad + 2 * K], 180, 360, fill=(60, 66, 70, 255), width=2 * K)
    # snorkel: a bent tin pipe aft
    d.line([(pad + 330 * K, pad + 2 * K), (pad + 330 * K, pad - 40 * K), (pad + 350 * K, pad - 52 * K)], fill=(60, 72, 78, 255), width=9 * K, joint="curve")
    d.line([(pad + 328 * K, pad + 2 * K), (pad + 328 * K, pad - 40 * K), (pad + 348 * K, pad - 53 * K)], fill=(168, 182, 186, 255), width=4 * K, joint="curve")
    d.ellipse([pad + 343 * K, pad - 62 * K, pad + 361 * K, pad - 44 * K], fill=brass, outline=bline)
    # rudder and shaft
    d.polygon([(pad + w - 4 * K, pad + 22 * K), (pad + w + 44 * K, pad - 16 * K), (pad + w + 50 * K, pad + 60 * K), (pad + w - 2 * K, pad + 70 * K)], fill=(124, 140, 146, 255), outline=(30, 40, 46, 255))
    d.line([(pad + w + 6 * K, pad + 28 * K), (pad + w + 42 * K, pad - 2 * K)], fill=(214, 224, 224, 200), width=K)
    d.rectangle([pad + w - 2 * K, pad + h / 2 + 22 * K, pad + w + 30 * K, pad + h / 2 + 34 * K], fill=bdark, outline=bline)
    d.ellipse([pad + w + 22 * K, pad + h / 2 + 16 * K, pad + w + 46 * K, pad + h / 2 + 40 * K], fill=brass, outline=bline)
    # lamp: a brass cowl on a bracket at the nose, low down, lens tilted up
    lx_, ly_ = pad + 1 * K, pad + h - 40 * K
    d.line([(pad + 4 * K, ly_ + 10 * K), (lx_ + 14 * K, ly_ + 6 * K)], fill=(50, 58, 62, 255), width=6 * K)
    body = [(lx_ + 30 * K, ly_ - 6 * K), (lx_ - 4 * K, ly_ - 26 * K), (lx_ - 20 * K, ly_ + 2 * K), (lx_ + 16 * K, ly_ + 22 * K)]
    d.polygon(body, fill=brass, outline=bline)
    d.polygon([body[0], body[1], (lx_ + 2 * K, ly_ - 18 * K), (lx_ + 28 * K, ly_ - 1 * K)], fill=(226, 190, 104, 255))
    d.polygon([(lx_ - 4 * K, ly_ - 26 * K), (lx_ - 20 * K, ly_ + 2 * K), (lx_ - 13 * K, ly_ + 5 * K), (lx_ + 3 * K, ly_ - 22 * K)], fill=(255, 232, 160, 255), outline=bline)
    A["tin"] = img
    A["tinK"] = K
    A["tin_pad"] = pad
    A["tin_size"] = (w, h)
    A["tin_port"] = (pad + 122 * K, pad + 92 * K)      # porthole centre in the sprite
    A["tin_lamp"] = (lx_ - 12 * K, ly_ - 12 * K)
    A["ring_small"] = brass_ring(40 * K, 58 * K, 6, pad=4, seed=3)
    b = Image.new("RGBA", (30 * K, 110 * K), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.ellipse([3 * K, 2 * K, 27 * K, 54 * K], fill=brass, outline=bline)
    bd.ellipse([8 * K, 6 * K, 18 * K, 40 * K], fill=(214, 178, 96, 255))
    bd.ellipse([3 * K, 56 * K, 27 * K, 108 * K], fill=bdark, outline=bline)
    A["prop"] = b


def tin_sprite(t, turkey_duck=0.0, wattle=0.0, lamp=1.0):
    """The tin for this frame: Turkey behind the glass, lamp lit, propeller idling."""
    K = A["tinK"]
    img = A["tin"].copy()
    px, py = A["tin_port"]
    r = 41 * K
    if "win_bg" not in A:
        yy, xx = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
        gl = np.exp(-(((xx - r * 1.2) / (r * 0.9)) ** 2 + ((yy - r * 0.2) / (r * 0.8)) ** 2))
        bg = np.array([40, 24, 14], np.float32)[None, None] * (1 - gl[..., None]) + np.array([232, 150, 60], np.float32)[None, None] * gl[..., None]
        A["win_bg"] = to_img(bg).convert("RGBA")
    win = A["win_bg"].copy()
    tk = turkey_img(wattle, int(150 * K))
    win.alpha_composite(tk, (int(r - tk.width * 0.42), int(r * 0.95 - tk.height * 0.27 + turkey_duck * K)))
    wd = ImageDraw.Draw(win, "RGBA")
    wd.ellipse([-r * 0.3, -r * 0.7, r * 1.2, r * 0.55], fill=(210, 240, 235, 30))
    msk = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(msk).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    img.paste(win, (int(px - r), int(py - r)), msk)
    rg = A["ring_small"]
    img.alpha_composite(rg, (int(px - rg.width / 2), int(py - rg.height / 2)))
    # propeller
    w, h = A["tin_size"]
    pad = A["tin_pad"]
    bl = A["prop"]
    sq = abs(math.cos(t * 5.0)) * 0.85 + 0.15
    b2 = bl.resize((max(2, int(bl.width)), max(2, int(bl.height * sq))), Image.BILINEAR)
    img.alpha_composite(b2, (int(pad + w + 30 * K), int(pad + h / 2 + 28 * K - b2.height / 2)))
    return img


# ------------------------------------------------------------ sprites in depth ---

def put(cv, spr, X, Y, z, cam, F, upp, rot=0.0, flip=False, alpha=1.0, squash=1.0, blur=0.0, tint=None):
    """Lay a cutout on the stack at (X, Y) units, height z. upp = units per sprite pixel."""
    sc = F * S(z) * upp
    w, h = max(2, int(spr.width * sc * squash)), max(2, int(spr.height * sc))
    im = spr.resize((w, h), Image.LANCZOS if sc < 1 else Image.BICUBIC)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if tint is not None:
        a = np.asarray(im, np.float32).copy()
        a[..., :3] = a[..., :3] * (1 - tint[1]) + np.array(tint[0], np.float32) * tint[1]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if blur:
        im = premul_blur(im, blur)
    if alpha < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = scr(X, Y, z, cam, F)
    cv.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)
    return x, y, im


def add_light(cv, layer_l, color, gain=1.0):
    """Additive light: L mask times colour."""
    r, g, b = [layer_l.point(lambda v, c=c: int(min(255, v * c / 255.0 * gain))) for c in color]
    return ImageChops.add(cv, Image.merge("RGB", (r, g, b)))


def flex(spr, phase, amp=10.0):
    """Bend a fish along its length: the tail swings, the head hardly moves (head at left)."""
    a = np.asarray(spr)
    h, w = a.shape[:2]
    x = np.arange(w) / w
    dy = (amp * (x ** 1.8) * np.sin(phase - 2.6 * x)).astype(np.int32)
    yy = np.arange(h)[:, None] - dy[None, :]
    ok = (yy >= 0) & (yy < h)
    out = a[np.clip(yy, 0, h - 1), np.arange(w)[None, :]]
    out[~ok] = 0
    return Image.fromarray(out, "RGBA")


class Spring:
    """Damped follower, stepped per frame: secondary motion for things that hang."""

    def __init__(self, f=1.6, zeta=0.25):
        self.w, self.z = 2 * math.pi * f, zeta

    def run(self, target, x0=None):
        x, v, out = (target[0] if x0 is None else x0), 0.0, []
        dt = 1.0 / FPS / 4
        for tg in target:
            for _ in range(4):
                acc = self.w * self.w * (tg - x) - 2 * self.z * self.w * v
                v += acc * dt
                x += v * dt
            out.append(x)
        return np.array(out)


# ------------------------------------------------------------ the leaf's clock ---
BEAT = 1.15            # seconds per swing: the Seasonal Timer


def leaf_clock(t, t0, x0, y0, notch, R=150.0, th_max=34.0):
    """Pendulum fall: even beats, left, right, and one notch lower at every turn.
    -> X, Y (units), angle (deg), beat index, phase 0..1."""
    x = max(0.0, (t - t0) / BEAT)
    n = int(x)
    u = x - n
    sign = 1 if n % 2 == 0 else -1
    th = math.radians(th_max) * math.cos(math.pi * u) * sign
    g = x + 0.5
    gn = int(g)
    step = smooth(clamp((g - gn - 0.28) / 0.44))
    py = y0 - R + notch * (gn - 1 + step)
    return x0 + R * math.sin(th), py + R * math.cos(th), math.degrees(th), n, u


def beam_gain(X, Y, apex, ang, half, length):
    """How far inside the lamp's cone a point is (0..1)."""
    dx, dy = X - apex[0], Y - apex[1]
    d = math.hypot(dx, dy)
    if d < 1 or d > length:
        return 0.0
    a = math.atan2(dy, dx) - ang
    a = (a + math.pi) % (2 * math.pi) - math.pi
    return clamp(1 - abs(a) / half) ** 0.7 * clamp(1.15 - d / length)


def beam_layer(apex_s, ang, half, length_s, gain):
    """Soft cone of lamplight in screen space, quarter size then enlarged."""
    q = 4
    m = Image.new("L", (W // q, H // q), 0)
    d = ImageDraw.Draw(m)
    ax, ay = apex_s[0] / q, apex_s[1] / q
    for k in range(5):
        hh = half * (1 - k * 0.14)
        L = length_s / q * (1 - k * 0.04)
        d.polygon([(ax, ay), (ax + L * math.cos(ang - hh), ay + L * math.sin(ang - hh)), (ax + L * math.cos(ang + hh), ay + L * math.sin(ang + hh))],
                  fill=int(255 * min(1.0, gain * (0.30 + 0.17 * k))))
    m = m.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    # fall-off along the beam
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = np.hypot(xx - apex_s[0], yy - apex_s[1]) / max(1.0, length_s)
    return to_img(np.asarray(m, np.float32) * np.clip(1.1 - dd, 0, 1) ** 1.2).convert("L")


MOTES = {}


def build_motes():
    rs = np.random.RandomState(77)
    for name, n in (("far", 70), ("mid", 90), ("near", 26)):
        MOTES[name] = dict(x=rs.uniform(-900, 900, n), y=rs.uniform(-600, 600, n), vx=rs.uniform(4, 16, n), vy=rs.uniform(2, 12, n),
                           ph=rs.uniform(0, 6.28, n), r=rs.uniform(0.8, 2.2, n), a=rs.uniform(0.25, 1.0, n))


def draw_motes(cv, name, t, z, cam, F, alpha, size=1.0, color=(214, 232, 206)):
    m = MOTES[name]
    d = ImageDraw.Draw(cv, "RGBA")
    x = (m["x"] + m["vx"] * t + 14 * np.sin(t * 0.6 + m["ph"]) + 900) % 1800 - 900
    y = (m["y"] + m["vy"] * t + 9 * np.sin(t * 0.45 + m["ph"] * 1.7) + 600) % 1200 - 600
    s = F * S(z)
    for k in range(len(x)):
        px, py = C[0] + s * (x[k] - cam[0]), C[1] + s * (y[k] - cam[1])
        if -5 < px < W + 5 and -5 < py < H + 5:
            r = m["r"][k] * size
            d.ellipse([px - r, py - r, px + r, py + r], fill=color + (int(255 * alpha * m["a"][k]),))


def fog_sheet(cv, t, k, cam, F, z, alpha, color=(96, 150, 140)):
    """A drifting veil between two sheets: the murk itself."""
    f = A["fog"]
    dx = int((t * (9 + 5 * k) + k * 300 + cam[0] * F * S(z) * 0.5)) % f.width
    dy = int((k * 170 + cam[1] * F * S(z) * 0.5 + 6 * math.sin(t * 0.3 + k))) % f.height
    m = ImageChops.offset(f, -dx, -dy).resize((W, int(W * f.height / f.width * 1.2)), Image.BILINEAR).crop((0, 0, W, H))
    m = m.point(lambda v: int(v * alpha))
    cv.paste(Image.new("RGB", (W, H), color), (0, 0), m)


def shafts(cv, t, cam, F, gain):
    a, b = A["shafts"]
    ox = int(clamp(200 + cam[0] * F * 0.5, 0, 400))
    m = ImageChops.multiply(a.crop((ox, 0, ox + W, H)), ImageChops.offset(b, int(t * 22) % b.width, 0).crop((0, 0, W, H)).point(lambda v: min(255, int(v * 1.7))))
    return add_light(cv, m, (150, 190, 150), gain)


def draw_leaf(cv, X, Y, z, ang, cam, F, lit=0.0, dark=0.0, scale=1.0, haze=0.0, blur=0.0, squash=1.0):
    """The cutout leaf. lit: how much lamp it is in (it glows like an ember); dark: silhouette before the lamp."""
    spr = A["leaf"]
    upp = 150.0 / spr.width * scale
    tint = None
    if haze > 0:
        tint = (tuple(MURK), haze)
    elif dark > 0:
        tint = ((30, 22, 30), dark * 0.55)
    x, y, im = put(cv, spr, X, Y, z, cam, F, upp, rot=ang, squash=squash, tint=tint, blur=blur)
    if lit > 0.02:
        al = im.getchannel("A")
        g = Image.new("L", (W, H), 0)
        g.paste(al, (int(x - im.width / 2), int(y - im.height / 2)))
        halo = g.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
        out = add_light(cv, halo, (255, 130, 40), 1.5 * lit)
        out = add_light(out, g, (150, 70, 8), 1.0 * lit)
        cv.paste(out)
    return x, y


# ------------------------------------------------------------ the river, through the stack ---

def river(t, cam, F, part, st):
    """One exposure through all six sheets. st: dict of everything that moves this frame."""
    R = A["river"]
    cv = place(R["board"], 1.70, 0.0, cam, F).convert("RGB")
    fog_sheet(cv, t, 0, cam, F, 30, 0.34)
    for lf in st.get("back_leaves", []):
        if lf["z"] < 55:
            draw_leaf(cv, lf["X"], lf["Y"], lf["z"], lf["ang"], cam, F, scale=lf["scale"], haze=lf["haze"], blur=lf["blur"])
    im = place(R["far"], 1.50, 55.0, cam, F)
    cv.paste(im, (0, 0), im)
    cv = shafts(cv, t, cam, F, 0.55)
    draw_motes(cv, "far", t, 80, cam, F, 0.35)
    for lf in st.get("back_leaves", []):
        if lf["z"] >= 55:
            draw_leaf(cv, lf["X"], lf["Y"], lf["z"], lf["ang"], cam, F, scale=lf["scale"], haze=lf["haze"], blur=lf["blur"])
    im = place(R["mid"], 1.30, 110.0, cam, F)
    cv.paste(im, (0, 0), im)
    fog_sheet(cv, t, 1, cam, F, 140, 0.26)
    # lamp
    bm = st.get("beam")
    if bm and bm["gain"] > 0:
        ap = scr(bm["apex"][0], bm["apex"][1], bm["z"], cam, F)
        layer = beam_layer(ap, bm["ang"], bm["half"], bm["length"] * F * S(bm["z"]), bm["gain"])
        cv = add_light(cv, layer, (255, 180, 84), 1.0)
    for tr in st.get("trout", []):
        if tr["z"] < ZL:
            draw_trout(cv, tr, t, cam, F)
    lf = st.get("leaf")
    if lf:
        # the flare: where the leaf has just been, burning in the lamp
        tr_ = lf.get("trail")
        if tr_:
            ov = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(ov)
            n = len(tr_)
            for k in range(n - 1):
                (x0, y0, g0), (x1, y1, g1) = tr_[k], tr_[k + 1]
                f = k / n
                p0, p1 = scr(x0, y0, ZL, cam, F), scr(x1, y1, ZL, cam, F)
                d.line([p0, p1], fill=int(255 * f ** 1.3 * (0.34 + 0.66 * g1)), width=max(2, int(2 + 9 * f)))
            ov = ov.filter(ImageFilter.GaussianBlur(2.6))
            cv = add_light(cv, ov, (255, 60, 24), 1.25)
            sub = ov.point(lambda v: int(v * 0.5))             # red, not white, where the lamp is already bright
            cv = ImageChops.subtract(cv, Image.merge("RGB", (Image.new("L", (W, H), 0), sub, sub)))
        draw_leaf(cv, lf["X"], lf["Y"], ZL, lf["ang"], cam, F, lit=lf.get("lit", 0), dark=lf.get("dark", 0), squash=lf.get("squash", 1.0))
    for tr in st.get("trout", []):
        if tr["z"] >= ZL:
            draw_trout(cv, tr, t, cam, F)
    tn = st.get("tin")
    if tn:
        put(cv, tn["img"], tn["X"], tn["Y"], tn["z"], cam, F, tn.get("upp_scale", 1.0) / A["tinK"], rot=tn.get("rot", 0))
    draw_motes(cv, "mid", t, 185, cam, F, 0.5, 1.3)
    for b in st.get("bubbles", []):
        x, y = scr(b[0], b[1], b[3], cam, F)
        r = b[2] * F
        d = ImageDraw.Draw(cv, "RGBA")
        d.ellipse([x - r, y - r, x + r, y + r], outline=(220, 240, 230, 150), width=1)
        d.ellipse([x - r * 0.5, y - r * 0.6, x - r * 0.1, y - r * 0.2], fill=(240, 250, 240, 170))
    im = place(R["near"], 1.15, 220.0, cam, F)
    cv.paste(im, (0, 0), im)
    im = place(R["front"], 1.20, 275.0, cam, F)
    cv.paste(im, (0, 0), im)
    draw_motes(cv, "near", t, 300, cam, F, 0.22, 4.0)
    return cv


def draw_trout(cv, tr, t, cam, F):
    spr = flex(A["trout"], tr["phase"], tr.get("amp", 9.0))
    put(cv, spr, tr["X"], tr["Y"], tr["z"], cam, F, tr["len"] / spr.width, rot=tr.get("rot", 0), flip=tr.get("flip", False),
        tint=((MURK[0], MURK[1], MURK[2]), tr.get("haze", 0.12)), blur=tr.get("blur", 0))


# ------------------------------------------------------------ part 1: the bench ---
UPPH = None            # units per photograph pixel
PHOTO_C = (1880.0, 300.0)       # where the photograph lies on the cutting mat
LEAF_REST = (-40.0, -235.0)     # where the leaf ends up on the carrier sheet
LAND = [0.3, 0.95, 1.6, 2.25, 2.9, 3.55]     # each sheet starts down at; lands 0.8 s later
T_MAT, T_CUT0, T_CUT1, T_GRIP, T_LIFT, T_CARRY, T_SLIDE, T_IN, T_PUSH = [v + D_PAINT for v in (6.1, 7.5, 9.55, 9.95, 10.45, 11.3, 11.3, 12.25, 11.9)]
T_P0, T_P1 = 4.75, T_MAT - 0.15       # the top sheet's left-hand weed is painted on the stand, blade by blade
PAINT_CAM = (-540.0, 120.0, 0.47)
POSTS = [(-1330, -860), (1330, -860), (-1330, 860), (1330, 860)]
BW = 2.0               # bench texture: units per px
BENCH_C = (700.0, 0.0)


def build_bench():
    global UPPH
    w, h = 2500, 1400
    grain = vnoise((h, w), 500, 5, seed=21, octaves=3) - 0.5
    wave = vnoise((h, w), 300, 60, seed=22, octaves=2) - 0.5
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    plank = np.floor((yy + 40) / 205.0)
    rs = np.random.RandomState(4)
    tone = rs.uniform(-0.09, 0.09, 12)[plank.astype(int) % 12]
    seam = np.abs(((yy + 40) % 205.0) - 2) < 2
    a = np.array([128, 88, 52], np.float32)[None, None] * (1 + grain * 0.42 + wave * 0.16 + tone)[..., None]
    a[seam] *= 0.5
    for k in range(5):          # knots
        cx, cy, r = rs.uniform(100, w - 100), rs.uniform(100, h - 100), rs.uniform(14, 30)
        d = np.hypot((xx - cx) / 1.8, yy - cy)
        a *= (1 - 0.5 * np.exp(-(d / r) ** 2))[..., None]
    A["wood"] = to_img(a)
    lw = A["leaf"].width
    UPPH = 150.0 / (A["photo_box"][2] - A["photo_box"][0])
    # tools, 2 px per unit, tip at the left end
    K = 2
    tw = Image.new("RGBA", (620 * K, 90 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(tw, "RGBA")
    cy = 45 * K
    for sgn in (-1, 1):
        pts = [(0, cy + sgn * 1), (150 * K, cy + sgn * 9 * K), (520 * K, cy + sgn * 22 * K), (616 * K, cy + sgn * 8 * K), (616 * K, cy + sgn * 2 * K), (520 * K, cy + sgn * 5 * K), (150 * K, cy + sgn * 3 * K)]
        d.polygon(pts, fill=(176, 184, 190, 255) if sgn < 0 else (140, 148, 156, 255), outline=(52, 58, 64, 255))
        d.line([(20 * K, cy + sgn * 3 * K), (500 * K, cy + sgn * 17 * K)], fill=(236, 240, 244, 200), width=K)
        for q in range(8):
            x = (330 + q * 14) * K
            d.line([(x, cy + sgn * 9 * K), (x, cy + sgn * 18 * K)], fill=(70, 76, 84, 220), width=K)
    A["tweezers"] = tw
    sc = Image.new("RGBA", (560 * K, 60 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(sc, "RGBA")
    cy = 30 * K
    d.polygon([(0, cy + 9 * K), (120 * K, cy - 11 * K), (150 * K, cy - 11 * K), (150 * K, cy + 9 * K)], fill=(214, 220, 226, 255), outline=(60, 66, 72, 255))
    d.line([(4 * K, cy + 8 * K), (146 * K, cy + 8 * K)], fill=(250, 252, 255, 255), width=K)
    d.rounded_rectangle([146 * K, cy - 12 * K, 556 * K, cy + 10 * K], radius=8 * K, fill=(150, 156, 164, 255), outline=(52, 58, 64, 255))
    d.line([(160 * K, cy - 7 * K), (540 * K, cy - 7 * K)], fill=(228, 232, 238, 220), width=K)
    for q in range(16):
        x = (200 + q * 12) * K
        d.line([(x, cy - 3 * K), (x + 6 * K, cy + 7 * K)], fill=(84, 90, 98, 230), width=K)
    A["scalpel"] = sc
    # warm bench lamp
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W * 0.42) / W, (yy - H * 0.4) / H)
    A["lamp"] = np.clip(1.12 - 0.85 * r ** 1.6, 0.35, 1.2)[..., None] * np.array([1.04, 1.0, 0.9], np.float32)


def keys(t, ks):
    """Eased interpolation through [(t, value-tuple), ...]."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            f = smooth((t - t0) / (t1 - t0))
            return tuple(lerp(a, b, f) for a, b in zip(v0, v1))
    return ks[-1][1]


CAM2_START = (-40.0, 40.0, 0.66)


def bench_cam(t):
    mx, my = PHOTO_C[0] + 10, PHOTO_C[1] + 6
    px_, py_, pf_ = PAINT_CAM
    ks = [(0.0, (640.0, 60.0, math.log(0.205))), (3.7, (560.0, 40.0, math.log(0.212))), (T_P0 - 0.05, (px_, py_, math.log(pf_))),
          (T_MAT, (px_ + 30, py_ - 20, math.log(pf_ * 1.06))), (T_MAT + 1.25, (mx, my, math.log(1.9))),
          (T_GRIP, (mx + 14, my - 8, math.log(2.0))), (T_CARRY, (820.0, -120.0, math.log(0.36))), (T_PUSH, (640.0, -150.0, math.log(0.40))),
          (T2, (CAM2_START[0], CAM2_START[1], math.log(CAM2_START[2])))]
    x, y, lf = keys(t, ks)
    return (x, y), math.exp(lf)


def photo_to_units(px, py):
    ph = A["photo"]
    return PHOTO_C[0] + (px - ph.width / 2) * UPPH, PHOTO_C[1] + (py - ph.height / 2) * UPPH


def leaf_home():
    b = A["photo_box"]
    return photo_to_units((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


TRK1 = {}


def build_track1():
    """Leaf on the bench: lifted by its stem, carried, slid in between the sheets. Per frame: X, Y, z, angle."""
    hx, hy = leaf_home()
    n = int(T2 * FPS) + 2
    X, Y, Z = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        t = i / FPS
        if t < T_GRIP:
            x, y, z = hx, hy, 0.0
        elif t < T_LIFT:
            f = ease(t, T_GRIP, T_LIFT)
            x, y, z = hx - 20 * f, hy - 30 * f, 330.0 * f
        elif t < T_SLIDE:
            f = ease(t, T_LIFT, T_SLIDE)
            x, y, z = lerp(hx - 20, 1180.0, f), lerp(hy - 30, LEAF_REST[1], f), lerp(330.0, ZL + 6, f ** 2.2)
        else:
            f = ease(t, T_SLIDE, T_IN)
            x, y, z = lerp(1180.0, LEAF_REST[0], f), LEAF_REST[1], lerp(ZL + 6, ZL, ramp(t, T_IN - 0.15, T_IN))
        X[i], Y[i], Z[i] = x, y, z
    vx = np.gradient(X) * FPS
    ang = Spring(1.5, 0.22).run(np.clip(vx * 0.022, -24, 24), 0.0)
    ang[: int(T_GRIP * FPS)] = 0
    ang *= np.array([1 - ramp(i / FPS, T_IN, T_IN + 0.5) for i in range(n)])
    TRK1.update(X=X, Y=Y, Z=Z, ang=ang)


def build_painting():
    """Schedule for painting the front sheet's left blades, and the masks that hide what is not painted yet."""
    bl = [b for b in front_blades() if b[0]]
    bl.sort(key=lambda b: b[1])                      # left to right, as a hand would work across the glass
    n = len(bl)
    dt = (T_P1 - T_P0) / n
    full = A["paint"][4]
    polys = [Image.new("L", (PW, PH), 0) for _ in bl]
    for m, (_, x, ln, wd, lean, sway) in zip(polys, bl):
        ImageDraw.Draw(m).polygon(blade_poly(x, 910, ln, wd + 6, lean, sway), fill=255)
    keep = Image.new("L", (PW, PH), 0)               # paint that is on the sheet when it arrives: the mound at the foot
    ImageDraw.Draw(keep).polygon(mound(-140, 160, 900, 120, 31), fill=255)
    A["painting"] = dict(blades=bl, dt=dt, polys=polys, keep=keep, alpha=full.getchannel("A"), n=n)
    spr = Image.new("RGBA", (1240, 120), (0, 0, 0, 0))          # the brush: 2 px per unit, tip at the left end
    d = ImageDraw.Draw(spr, "RGBA")
    cy = 60
    d.polygon([(0, cy), (40, cy - 13), (116, cy - 17), (116, cy + 17), (40, cy + 13)], fill=(16, 40, 34, 255), outline=(6, 18, 16, 255))
    for q in range(7):
        d.line([(6 + q * 3, cy - 2 + q * 0.3), (112, cy - 14 + q * 4.6)], fill=(38, 84, 66, 200), width=1)
    d.polygon([(112, cy - 19), (212, cy - 15), (212, cy + 15), (112, cy + 19)], fill=(196, 186, 160, 255), outline=(70, 62, 44, 255))
    d.line([(116, cy - 12), (208, cy - 10)], fill=(250, 246, 226, 230), width=3)
    for xx in (140, 186):
        d.line([(xx, cy - 17), (xx, cy + 17)], fill=(110, 100, 78, 255), width=2)
    d.polygon([(212, cy - 14), (760, cy - 19), (1180, cy - 10), (1236, cy), (1180, cy + 10), (760, cy + 19), (212, cy + 14)],
              fill=(132, 42, 30, 255), outline=(52, 16, 12, 255))
    d.line([(230, cy - 9), (1150, cy - 6)], fill=(214, 110, 84, 200), width=3)
    d.line([(230, cy + 10), (1150, cy + 6)], fill=(70, 20, 16, 200), width=4)
    A["brush"] = spr


def painting_state(t):
    """-> (alpha of the front sheet as painted so far, brush tip in paint px or None, brush lift 0..1)."""
    P = A["painting"]
    hide = Image.new("L", (PW, PH), 0)
    dh = ImageDraw.Draw(hide)
    show = Image.new("L", (PW, PH), 0)
    tip, lift = None, 1.0
    k_now = (t - T_P0) / P["dt"]
    for k, (b, m) in enumerate(zip(P["blades"], P["polys"])):
        _, x, ln, wd, lean, sway = b
        p = clamp((k_now - k) / 0.72)                # the stroke takes 72% of the slot; the rest is the lift across
        if p >= 1:
            show = ImageChops.lighter(show, m)
            continue
        hide = ImageChops.lighter(hide, m)
        if p > 0:
            yy = int(910 - ln * p)
            part = m.copy()
            ImageDraw.Draw(part).rectangle([0, 0, PW, yy], fill=0)
            ax_, ay_ = blade_axis(x, ln, lean, sway, p)          # the wet end of the stroke is round, like the brush
            rr = max(4.0, wd * 0.42 * (1 - p) ** 0.7)
            cap = Image.new("L", (PW, PH), 0)
            ImageDraw.Draw(cap).ellipse([ax_ - rr, ay_ - rr * 1.3, ax_ + rr, ay_ + rr * 0.6], fill=255)
            show = ImageChops.lighter(show, ImageChops.lighter(part, ImageChops.multiply(cap, m)))
    hide = ImageChops.subtract(ImageChops.subtract(hide, show), P["keep"])
    alpha = ImageChops.subtract(P["alpha"], hide.filter(ImageFilter.GaussianBlur(1.0)).point(lambda v: min(255, v * 2)))
    if T_P0 - 0.6 < t < T_P1 + 0.7:
        k = int(clamp(k_now, 0, P["n"] - 1e-3))
        _, x, ln, wd, lean, sway = P["blades"][k]
        u = k_now - k
        if k_now < 0:                                 # coming in from the bench
            f = ease(t, T_P0 - 0.6, T_P0)
            r0 = blade_axis(x, ln, lean, sway, 0.0)
            tip, lift = (r0[0] - (1 - f) * 500, r0[1] + (1 - f) * 260), 1 - f
        elif k_now >= P["n"]:                         # and away
            f = ease(t, T_P1, T_P1 + 0.7)
            e = blade_axis(x, ln, lean, sway, 1.0)
            tip, lift = (e[0] - f * 700, e[1] + f * 500), f
        elif u < 0.72:
            tip, lift = blade_axis(x, ln, lean, sway, u / 0.72), 0.0
        else:
            f = smooth((u - 0.72) / 0.28)
            e = blade_axis(x, ln, lean, sway, 1.0)
            if k + 1 < P["n"]:
                _, x2, ln2, _, lean2, sway2 = P["blades"][k + 1]
                r = blade_axis(x2, ln2, lean2, sway2, 0.0)
            else:
                r = e
            tip, lift = (lerp(e[0], r[0], f), lerp(e[1], r[1], f)), math.sin(f * math.pi)
    return alpha, tip, lift


def put_tool(cv, spr, tip, z, cam, F, rot, shadow=10.0):
    """A tool whose tip (left end, mid height of the sprite) touches tip=(X, Y)."""
    sc = F * S(z) * 0.5
    w, h = max(2, int(spr.width * sc)), max(2, int(spr.height * sc))
    im = spr.resize((w, h), Image.LANCZOS).rotate(rot, expand=True, resample=Image.BICUBIC)
    a = math.radians(rot)
    vx, vy = w / 2, 0.0                    # tip -> centre before rotation
    cx, cy = vx * math.cos(a) + vy * math.sin(a), -vx * math.sin(a) + vy * math.cos(a)
    x, y = scr(tip[0], tip[1], z, cam, F)
    pos = (int(x + cx - im.width / 2), int(y + cy - im.height / 2))
    if shadow:
        sh = Image.new("RGBA", im.size, (10, 8, 6, 0))
        sh.putalpha(im.getchannel("A").point(lambda v: int(v * 0.38)).filter(ImageFilter.GaussianBlur(float(max(1.0, shadow * F)))))
        cv.paste(sh, (int(pos[0] + shadow * F * 1.2), int(pos[1] + shadow * F * 1.6)), sh)
    cv.paste(im, pos, im)


def pane_rect(u, z, cam, F, off=(0, 0), margin=30.0):
    hw, hh = u * PW / 2 + margin, u * PH / 2 + margin
    x0, y0 = scr(off[0] - hw, off[1] - hh, z, cam, F)
    x1, y1 = scr(off[0] + hw, off[1] + hh, z, cam, F)
    return x0, y0, x1, y1


def bench(t, k_frame):
    cam, F = bench_cam(t)
    set_hc(lerp(1900.0, 900.0, ease(t, T_PUSH, T2 - 0.2)))
    # the bench top
    wood = A["wood"]
    a = 1.0 / (F * BW)
    co = (a, 0, wood.width / 2 + (cam[0] - BENCH_C[0]) / BW - a * C[0], 0, a, wood.height / 2 + (cam[1] - BENCH_C[1]) / BW - a * C[1])
    cv = wood.transform((W, H), Image.AFFINE, co, Image.BILINEAR)
    d = ImageDraw.Draw(cv, "RGBA")
    # cutting mat
    mx0, my0 = scr(PHOTO_C[0] - 300, PHOTO_C[1] - 230, 0, cam, F)
    mx1, my1 = scr(PHOTO_C[0] + 300, PHOTO_C[1] + 230, 0, cam, F)
    d.rectangle([mx0 + 5 * F, my0 + 7 * F, mx1 + 5 * F, my1 + 7 * F], fill=(20, 12, 6, 90))
    d.rectangle([mx0, my0, mx1, my1], fill=(46, 104, 84, 255), outline=(30, 70, 58, 255))
    for q in range(1, 30):
        x = mx0 + q * 20 * F
        if x < mx1:
            d.line([(x, my0), (x, my1)], fill=(120, 170, 140, 70 if q % 5 else 130), width=1)
    for q in range(1, 23):
        y = my0 + q * 20 * F
        if y < my1:
            d.line([(mx0, y), (mx1, y)], fill=(120, 170, 140, 70 if q % 5 else 130), width=1)
    # the photograph
    ph = A["photo"]
    pw, phh = ph.width * UPPH, ph.height * UPPH
    px0, py0 = scr(PHOTO_C[0] - pw / 2, PHOTO_C[1] - phh / 2, 0, cam, F)
    px1, py1 = scr(PHOTO_C[0] + pw / 2, PHOTO_C[1] + phh / 2, 0, cam, F)
    if px0 < W and py0 < H and px1 > 0 and py1 > 0:
        d.rectangle([px0 + 3 * F, py0 + 4 * F, px1 + 3 * F, py1 + 4 * F], fill=(10, 20, 14, 110))
        a = 1.0 / (F * UPPH)
        co = (a, 0, ph.width / 2 + (cam[0] - PHOTO_C[0]) / UPPH - a * C[0], 0, a, ph.height / 2 + (cam[1] - PHOTO_C[1]) / UPPH - a * C[1])
        pim = ph.convert("RGBA").transform((W, H), Image.AFFINE, co, Image.BICUBIC)
        cv.paste(pim, (0, 0), pim)
        d = ImageDraw.Draw(cv, "RGBA")
        d.rectangle([px0, py0, px1, py1], outline=(250, 250, 246, 255), width=max(1, int(5 * F)))
        cut = A["cut"]
        nc = len(cut)
        done = int(nc * ramp(t, T_CUT0, T_CUT1))
        pts = [scr(*photo_to_units(x, y), 0, cam, F) for x, y in cut[: max(0, done)]]
        if t >= T_GRIP and len(pts) > 2:           # the hole it leaves: the mat shows through
            d.polygon(pts, fill=(40, 94, 76, 255))
            d.line(pts + pts[:1], fill=(14, 40, 32, 200), width=max(1, int(1.6 * F)))
        elif len(pts) > 1:
            d.line(pts, fill=(30, 16, 22, 210), width=max(1, int(0.9 * F)))
        if T_CUT0 - 0.7 < t < T_CUT1 + 0.6:        # the scalpel
            fi = ease(t, T_CUT0 - 0.7, T_CUT0)
            fo = ease(t, T_CUT1, T_CUT1 + 0.6)
            q = cut[min(nc - 1, max(0, done - 1))] if done else cut[0]
            tip = photo_to_units(q[0], q[1])
            tip = (tip[0] + (1 - fi) * 260 + fo * 300, tip[1] + (1 - fi) * 120 + fo * 160)
            dq = cut[min(nc - 1, done + 6)] - cut[max(0, done - 6)]
            lean = 8 * math.sin(math.atan2(dq[1], dq[0]))
            put_tool(cv, A["scalpel"], tip, 0.0 + 30 * (1 - fi) + 30 * fo, cam, F, rot=-38 + lean, shadow=6 + 20 * (1 - fi + fo))
    d = ImageDraw.Draw(cv, "RGBA")
    # the stand: a base frame and four posts
    bx0, by0, bx1, by1 = pane_rect(1.70, 0, cam, F, margin=90)
    d.rectangle([bx0 + 14 * F, by0 + 20 * F, bx1 + 14 * F, by1 + 20 * F], fill=(12, 8, 4, 110))
    d.rectangle([bx0, by0, bx1, by1], fill=(74, 50, 30, 255), outline=(40, 26, 14, 255), width=2)
    ix0, iy0, ix1, iy1 = pane_rect(1.70, 0, cam, F, margin=30)
    d.rectangle([ix0, iy0, ix1, iy1], fill=(236, 232, 214, 255))            # the light box
    for (X0, Y0) in POSTS:
        base = [scr(X0 + sx * 38, Y0 + sy * 38, 0, cam, F) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        top = [scr(X0 + sx * 38, Y0 + sy * 38, 340, cam, F) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for q in range(4):
            d.polygon([base[q], base[(q + 1) % 4], top[(q + 1) % 4], top[q]], fill=(96 - q * 9, 66 - q * 7, 38 - q * 4, 255), outline=(44, 28, 14, 255))
    # the sheets, bottom to top
    li = min(len(TRK1["X"]) - 1, k_frame)
    lX, lY, lZ, lA = float(TRK1["X"][li]), float(TRK1["Y"][li]), float(TRK1["Z"][li]), float(TRK1["ang"][li])
    in_stack = t >= T_SLIDE
    stem = (4.0, 78.0)

    def leaf_and_tweezers():
        sh = scr(lX + lZ * 0.10 + 6, lY + lZ * 0.14 + 8, 0 if not in_stack else ZL, cam, F) if lZ > 1 or in_stack else None
        if sh and not in_stack:
            spr = A["leaf"]
            sc = F * 150.0 / spr.width
            im = spr.resize((max(2, int(spr.width * sc)), max(2, int(spr.height * sc))), Image.BILINEAR)
            sd = Image.new("RGBA", im.size, (8, 14, 10, 0))
            sd.putalpha(im.getchannel("A").point(lambda v: int(v * 0.42)).filter(ImageFilter.GaussianBlur(1 + lZ * F * 0.05)))
            cv.paste(sd, (int(sh[0] - im.width / 2), int(sh[1] - im.height / 2)), sd)
        if in_stack:                       # contact shadow on the carrier glass
            spr = A["leaf"]
            sc = F * S(ZL) * 150.0 / spr.width
            im = spr.resize((max(2, int(spr.width * sc)), max(2, int(spr.height * sc))), Image.BILINEAR).rotate(lA, expand=True)
            sd = Image.new("RGBA", im.size, (6, 16, 14, 0))
            sd.putalpha(im.getchannel("A").point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(2.5)))
            sx, sy = scr(lX, lY, ZL, cam, F)
            cv.paste(sd, (int(sx - im.width / 2 + 5 * F + 2), int(sy - im.height / 2 + 7 * F + 3)), sd)
        if t >= T_GRIP:
            draw_leaf(cv, lX, lY, lZ, lA, cam, F)
        if T_GRIP - 0.55 < t < T_IN + 0.8:
            fi = ease(t, T_GRIP - 0.55, T_GRIP - 0.1)
            fo = ease(t, T_IN + 0.1, T_IN + 0.8)
            a_ = math.radians(lA)
            tx = lX + stem[0] * math.cos(a_) + stem[1] * math.sin(a_) + (1 - fi) * 420 + fo * 1500
            ty = lY - stem[0] * math.sin(a_) + stem[1] * math.cos(a_) + (1 - fi) * 60 - fo * 40
            put_tool(cv, A["tweezers"], (tx, ty), lZ + 4 + 40 * (1 - fi), cam, F, rot=-7 + 5 * (1 - fi), shadow=0 if in_stack else 8 + lZ * 0.06)

    part_alpha, brush_tip, brush_lift = (painting_state(t) if t < T_P1 + 0.7 else (None, None, 1.0))
    if t >= T_P1:
        part_alpha = None
    for idx, (name, z, u) in enumerate(SHEETS):
        t0 = LAND[idx]
        if t < t0:
            continue
        f = ease(t, t0, t0 + 0.8)
        off = (-(1 - f) ** 1.6 * 3300.0, (1 - f) ** 2 * (-260 if idx % 2 else 220))
        zz = z + (1 - f) ** 1.2 * 230.0
        x0, y0, x1, y1 = pane_rect(u, zz, cam, F, off)
        if name in A["shadow"]:
            gap = 55.0 + (zz - z)
            shd = A["shadow"][name]
            if name == "front" and part_alpha is not None:
                shd = part_alpha.resize((PW // 4, PH // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
            shm = place(shd, u, max(0.0, z - 55.0), cam, F, (off[0] + gap * 0.5, off[1] + gap * 0.7))
            shm = shm.point(lambda v: int(v * 0.5 * (0.35 + 0.65 * f)))
            cv.paste(Image.new("RGB", (W, H), (8, 20, 22)), (0, 0), shm)
            d = ImageDraw.Draw(cv, "RGBA")
        if name == "board":
            d.rectangle([x0 + 10 * F, y0 + 14 * F, x1 + 10 * F, y1 + 14 * F], fill=(10, 8, 4, 90))
            im = place(A["paint"][0], u, zz, cam, F, off)
            cv.paste(im, (0, 0), im)
            d = ImageDraw.Draw(cv, "RGBA")
            d.rectangle([x0 + 30 * F, y0 + 30 * F, x1 - 30 * F, y1 - 30 * F], outline=(30, 40, 40, 255), width=1)
        else:
            d.rectangle([x0, y0, x1, y1], fill=(196, 236, 224, 15))
            if name != "carrier":
                pim = A["paint"][PAINT_OF[name]]
                if name == "front" and part_alpha is not None:
                    pim = pim.copy()
                    pim.putalpha(part_alpha)
                im = place(pim, u, zz, cam, F, off)
                cv.paste(im, (0, 0), im)
                d = ImageDraw.Draw(cv, "RGBA")
            # glare of the lamp on the glass: it slides as the camera moves, a different amount per sheet
            gx = x0 + (x1 - x0) * (0.26 + 0.11 * idx) - cam[0] * F * (0.2 + 0.05 * idx)
            for wdt, al in ((150 * F, 20), (40 * F, 26)):
                d.polygon([(gx, y0), (gx + wdt, y0), (gx + wdt - (y1 - y0) * 0.35, y1), (gx - (y1 - y0) * 0.35, y1)], fill=(255, 255, 250, al))
                gx += 210 * F
            d.rectangle([x0, y0, x1, y1], outline=(70, 156, 132, 150), width=max(3, int(14 * F)))
            d.rectangle([x0, y0, x1, y1], outline=(232, 250, 242, 235), width=1)
            d.line([(x0, y1), (x1, y1), (x1, y0)], fill=(30, 86, 74, 220), width=max(2, int(7 * F)))
            for cx_, cy_ in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):            # brass pegs it rests on
                d.ellipse([cx_ - 9 * F - 1, cy_ - 9 * F - 1, cx_ + 9 * F + 1, cy_ + 9 * F + 1], fill=(182, 142, 62, 255), outline=(60, 40, 14, 255))
        if name == "carrier" and in_stack:
            leaf_and_tweezers()
            d = ImageDraw.Draw(cv, "RGBA")
    for (X0, Y0) in POSTS:
        top = [scr(X0 + sx * 38, Y0 + sy * 38, 340, cam, F) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        d.polygon(top, fill=(150, 108, 66, 255), outline=(50, 32, 16, 255))
    if not in_stack:
        leaf_and_tweezers()
    if brush_tip is not None:                      # the brush, loaded with weed green, working on the top sheet
        uf = SHEETS[5][2]
        bt = ((brush_tip[0] - PW / 2) * uf, (brush_tip[1] - PH / 2) * uf)
        put_tool(cv, A["brush"], bt, SHEETS[5][1] + 2 + 70 * brush_lift, cam, F, rot=-52 + 6 * math.sin(t * 9.0) * (1 - brush_lift),
                 shadow=3 + 22 * brush_lift)
    # the bench lamp; it is turned down as the camera goes in
    dim = ease(t, T_PUSH + 0.2, T2 - 0.1)
    arr = np.asarray(cv, np.float32) * (A["lamp"] * (1 - dim) + dim)
    return to_img(arr), cam, F


# ------------------------------------------------------------ part 2: Turkey looks out ---
PC = (522, 256)        # porthole centre on screen
RG = 190               # glass radius
N2 = 54.0              # one notch, units
L2 = dict(x0=-124.0, y0=-196.0)


def build_port():
    """The inside wall of the tin, and the six-bolt porthole with its hinge, latch and the timer notches."""
    s = Sheet(61, (W, H))
    rs = s.rs
    for k in range(900):
        x, y = rs.uniform(-20, W + 20), rs.uniform(-20, H + 20)
        g = rs.uniform(-7, 7)
        s.dab(x, y, 1.57 + rs.uniform(-0.08, 0.08), rs.uniform(70, 190), rs.uniform(14, 30), (58 + g, 68 + g, 74 + g), 0.9, rs.uniform(-0.3, 0.3))
    wall = np.asarray(s.finish(opaque=True, relief=0.7).convert("RGB"), np.float32)
    wall *= (0.86 + 0.3 * vnoise((H, W), 160, seed=8, octaves=3))[..., None]
    rust = np.clip((vnoise((H, W), 50, seed=9, octaves=3) - 0.66) * 6, 0, 1)[..., None]
    wall = wall * (1 - rust * 0.6) + np.array([96, 58, 36], np.float32) * rust * 0.6
    img = to_img(wall)
    d = ImageDraw.Draw(img, "RGBA")
    for x in (118, 886):                    # plate seams with rivets
        d.line([(x, 0), (x, H)], fill=(20, 24, 28, 200), width=3)
        d.line([(x + 3, 0), (x + 3, H)], fill=(120, 132, 138, 90), width=1)
        for y in range(24, H, 48):
            for xx_ in (x - 16, x + 18):
                d.ellipse([xx_ - 6, y - 5, xx_ + 7, y + 8], fill=(18, 22, 26, 160))
                d.ellipse([xx_ - 6, y - 6, xx_ + 6, y + 6], fill=(78, 88, 94, 255))
                d.ellipse([xx_ - 4, y - 5, xx_ + 2, y + 1], fill=(132, 144, 148, 255))
    # light: an amber lamp overhead, dark corners
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.asarray(img, np.float32)
    glow = np.exp(-(((xx - 520) / 420) ** 2 + ((yy + 60) / 260) ** 2))
    a = a * (0.66 + 0.6 * glow)[..., None] + np.array([120, 70, 20], np.float32) * (glow * 0.28)[..., None]
    rr = np.hypot(xx - PC[0], yy - PC[1])
    a *= np.clip(0.55 + (rr - RG - 50) / 160, 0.55, 1.0)[..., None]          # shadow thrown round the ring
    A["wall"] = to_img(a)
    ring = brass_ring(RG, RG + 58, 6, pad=70, seed=1, start=-90)
    d = ImageDraw.Draw(ring, "RGBA")
    R = ring.width // 2
    # hinge (left) and latch (right)
    hx = R - RG - 58
    d.rounded_rectangle([hx - 44, R - 62, hx + 22, R + 62], radius=5, fill=(50, 50, 50, 255), outline=(16, 16, 16, 255), width=2)
    d.rectangle([hx - 18, R - 68, hx - 6, R + 68], fill=(84, 84, 82, 255), outline=(16, 16, 16, 255))
    d.line([(hx - 15, R - 64), (hx - 15, R + 64)], fill=(150, 150, 146, 255), width=2)
    for yy_ in (-44, 44):
        for xx_ in (-32, 10):
            d.ellipse([hx + xx_ - 5, R + yy_ - 5, hx + xx_ + 5, R + yy_ + 5], fill=(110, 110, 106, 255), outline=(14, 14, 14, 255))
    lx = R + RG + 58
    d.rounded_rectangle([lx - 20, R - 26, lx + 40, R + 26], radius=6, fill=(170, 132, 58, 255), outline=(60, 42, 16, 255), width=2)
    d.rounded_rectangle([lx - 46, R - 9, lx + 16, R + 9], radius=8, fill=(198, 158, 74, 255), outline=(60, 42, 16, 255), width=2)
    d.ellipse([lx + 12, R - 12, lx + 36, R + 12], fill=(210, 172, 86, 255), outline=(60, 42, 16, 255), width=2)
    d.line([(lx - 40, R - 4), (lx + 8, R - 4)], fill=(250, 226, 150, 200), width=2)
    # the timer: nine notches filed into the inner bevel, right-hand side
    for n in range(9):
        a_ = math.radians(-40 + n * 10)
        r0, r1 = RG + 3, RG + (15 if n % 4 else 20)
        d.line([(R + r0 * math.cos(a_), R + r0 * math.sin(a_)), (R + r1 * math.cos(a_), R + r1 * math.sin(a_))], fill=(40, 26, 8, 255), width=3)
        d.line([(R + r0 * math.cos(a_) + 1, R + r0 * math.sin(a_) + 2), (R + r1 * math.cos(a_) + 1, R + r1 * math.sin(a_) + 2)], fill=(250, 224, 150, 150), width=1)
    A["ring"] = ring
    sh = Image.new("RGBA", ring.size, (0, 0, 0, 0))
    sh.putalpha(ring.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.6)))
    A["ring_shadow"] = sh
    # glass: darker toward the rim, a wiped highlight upper left
    g = np.zeros((H, W, 4), np.float32)
    e = np.clip((rr - (RG - 46)) / 46, 0, 1) ** 2
    g[..., 3] = e * 150
    g[..., :3] = (6, 20, 22)
    hi = np.exp(-((rr - (RG - 26)) / 9) ** 2) * np.clip(-(xx - PC[0]) - (yy - PC[1]) * 1.3, 0, None) / (RG * 1.4)
    A["glass"] = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA")
    A["glass_hi"] = to_img(np.clip(hi, 0, 1) * 255).convert("L")
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([PC[0] - RG - 2, PC[1] - RG - 2, PC[0] + RG + 2, PC[1] + RG + 2], fill=255)
    A["hole"] = m


TRK2 = {}


def build_track2():
    n = int((SECONDS - T2) * FPS) + 3
    duck = np.zeros(n)
    for i in range(n):
        t = T2 + i / FPS
        x = (t - T2) / BEAT
        k = int(x)
        u = x - k
        duck[i] = min(k, 8) * 4.5 + 9 * math.exp(-u * 5) * (1 if k > 0 else 0) * math.sin(min(1.0, u * 6) * math.pi)
    TRK2["duck"] = Spring(2.2, 0.5).run(duck)
    TRK2["wattle"] = Spring(1.7, 0.16).run(np.gradient(TRK2["duck"]) * FPS * -0.9, 0.0)


def port_frame(t, k_frame):
    set_hc(900.0)
    i = min(len(TRK2["duck"]) - 1, max(0, k_frame - int(T2 * FPS)))
    X, Y, ang, n, u = leaf_clock(t, T2, L2["x0"], L2["y0"], N2)
    cam = (CAM2_START[0] + 26 * math.sin((t - T2) * 0.42), CAM2_START[1] + 70 * ease(t, T2 + 1.5, T3 - 0.5))
    F = CAM2_START[2] * (1 + 0.035 * ease(t, T2, T3))
    lamp = ease(t, T2 + 1.25, T2 + 1.5) * (0.9 + 0.1 * math.sin(t * 9) * math.sin(t * 2.3))
    apex = (-60.0, cam[1] + 330.0)
    bm = dict(apex=apex, z=ZL, ang=math.radians(-90 - 3), half=0.36, length=640.0, gain=lamp)
    lit = lamp * beam_gain(X, Y, apex, bm["ang"], bm["half"] * 1.25, bm["length"])
    st = dict(beam=bm, leaf=dict(X=X, Y=Y, ang=ang * 1.25, lit=lit, dark=1 - lamp, squash=1 - 0.2 * abs(math.sin(math.pi * u))),
              trout=[dict(X=128 + 8 * math.sin(t * 0.7), Y=cam[1] + 62 + 5 * math.sin(t * 0.9), z=186.0, len=190.0, phase=t * 5.0, amp=5,
                          flip=TROUT_FACES_RIGHT, rot=(-1 if TROUT_FACES_RIGHT else 1) * (4 + 5 * math.sin(t * 0.5)), haze=0.1)],
              bubbles=[(-150 + 30 * math.sin(q * 2.1 + t * 0.8), cam[1] + 260 - ((t * 60 + q * 97) % 520), 3 + (q % 3) * 1.6, 150.0) for q in range(7)])
    rv = river(t, cam, F, 2, st)
    cv = A["wall"].copy()
    hole = A["hole"]
    cv.paste(rv, (PC[0] - int(C[0]), PC[1] - int(C[1])), hole.crop((PC[0] - int(C[0]), PC[1] - int(C[1]), PC[0] - int(C[0]) + W, PC[1] - int(C[1]) + H)) if False else
             ImageChops.offset(hole, -(PC[0] - int(C[0])), -(PC[1] - int(C[1]))))
    # Turkey in the glass: his own reflection, low left
    tk = turkey_img(TRK2["wattle"][i], 250).transpose(Image.FLIP_LEFT_RIGHT)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    refl.alpha_composite(tk, (PC[0] - 180, int(PC[1] + 20 + TRK2["duck"][i] * 1.3)))
    ra = ImageChops.multiply(refl.getchannel("A"), hole).point(lambda v: int(v * (0.20 + 0.08 * lamp)))
    refl.putalpha(ra)
    refl = refl.filter(ImageFilter.GaussianBlur(1.3))
    cv.paste(refl, (0, 0), refl)
    cv.paste(A["glass"], (0, 0), A["glass"])
    cv = add_light(cv, A["glass_hi"], (230, 250, 240), 0.55)
    ring = A["ring"]
    pos = (PC[0] - ring.width // 2, PC[1] - ring.height // 2)
    cv.paste(A["ring_shadow"], (pos[0] + 8, pos[1] + 12), A["ring_shadow"])
    cv.paste(ring, pos, ring)
    d = ImageDraw.Draw(cv, "RGBA")
    # the notch the leaf has reached is lit
    for q in range(min(9, n + 1)):
        a_ = math.radians(-40 + q * 10)
        r_ = RG + 26
        x, y = PC[0] + r_ * math.cos(a_), PC[1] + r_ * math.sin(a_)
        on = q == min(8, n)
        rr_ = 5 if on else 3
        if on:
            d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(255, 170, 60, 70))
        d.ellipse([x - rr_, y - rr_, x + rr_, y + rr_], fill=(255, 196, 92, 255) if on else (150, 84, 30, 255), outline=(50, 30, 10, 255))
    # amber from the lamp reaches the ring's lower lip
    if lamp > 0:
        g = Image.new("L", (W // 4, H // 4), 0)
        ImageDraw.Draw(g).ellipse([(PC[0] - 150) // 4, (PC[1] + RG - 10) // 4, (PC[0] + 150) // 4, (PC[1] + RG + 90) // 4], fill=int(120 * lamp))
        cv = add_light(cv, g.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR), (255, 170, 70), 0.7)
    # Turkey himself, close to the lens, dark against the glass
    tk = turkey_img(TRK2["wattle"][i] * 1.2, 470).transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(tk, np.float32).copy()
    a[..., :3] = a[..., :3] * 0.26 + np.array([20, 13, 9], np.float32) * 0.5
    edge = np.asarray(tk.getchannel("A").filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    a[..., :3] += (np.array([255, 170, 80], np.float32) * ((1 - edge) * 0.55 * (0.4 + 0.6 * lamp)))[..., None].reshape(a.shape[0], a.shape[1], 1) * np.array([1, 0.66, 0.3], np.float32) if False else 0
    rim = (1 - edge)[..., None] * np.array([150, 96, 40], np.float32) * (0.35 + 0.65 * lamp)
    a[..., :3] += rim
    tk = premul_blur(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), 0.7)
    cv.paste(tk, (-58, int(150 + TRK2["duck"][i] * 2.2)), tk)
    return cv


# ------------------------------------------------------------ part 3: the trout look in ---
N3 = 84.0
L3 = dict(x0=-190.0, y0=-455.0)
TIN = (372.0, 168.0, 200.0)       # X, Y, z of the tin's centre
TIN_SCALE = 1.22
T_FLARE = None
TRK3 = {}
TROUT_FACES_RIGHT = False


def tin_lamp_units(t):
    K = A["tinK"]
    lx, ly = A["tin_lamp"]
    cx, cy = A["tin"].width / 2, A["tin"].height / 2
    bob = 6 * math.sin(t * 0.8)
    return TIN[0] + (lx - cx) / K * TIN_SCALE, TIN[1] + bob + (ly - cy) / K * TIN_SCALE


BEAM3 = dict(ang=math.radians(-154), half=0.27, length=820.0)


def build_track3():
    """Everything in the river shot, per frame, so that springs and the flare trail have a past."""
    global T_FLARE
    n = int((SECONDS - T3) * FPS) + 2
    L = []
    for i in range(n + 30):
        t = T3 + (i - 30) / FPS
        X, Y, ang, k, u = leaf_clock(max(T3, t), T3, L3["x0"], L3["y0"], N3)
        ap = tin_lamp_units(t)
        g = beam_gain(X, Y, ap, BEAM3["ang"], BEAM3["half"] * 1.15, BEAM3["length"])
        L.append((X, Y, ang, k, u, g))
    TRK3["leaf"] = L
    gs = [l[5] for l in L[30:]]
    T_FLARE = T3 + next((i for i, g in enumerate(gs) if g > 0.25), len(gs) - 1) / FPS
    # trout A: comes up from the weed to meet it. trout B: hangs under it, then bolts for the tin when it flares.
    ax, ay, ar = np.zeros(n), np.zeros(n), np.zeros(n)
    bx, by, br, bph = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    ph = 0.0
    for i in range(n):
        t = T3 + i / FPS
        X, Y = L[i + 30][0], L[i + 30][1]
        f = ease(t, T3 + 2.2, T3 + 7.4)
        tx, ty = X - 150, Y + 78                     # just under and behind the leaf, mouth to it
        ax[i] = lerp(-640.0, tx, f) + 10 * math.sin(t * 0.9) * (1 - f)
        ay[i] = lerp(372.0, ty, f ** 1.3)
        ar[i] = 30 * math.sin(f * math.pi) ** 0.8 + 16 * f
        fb = ease(t, T_FLARE + 0.05, T_FLARE + 0.75)
        bx[i] = lerp(60 + 12 * math.sin(t * 0.8), 640.0, fb)
        by[i] = lerp(-70 + 8 * math.sin(t * 1.1) + 60 * ease(t, T3, T3 + 3), 60.0, fb ** 1.5)
        br[i] = lerp(24 * ease(t, T3 + 0.5, T3 + 2.5), -16, fb)
        ph += (5.0 + 34 * math.sin(fb * math.pi)) / FPS
        bph[i] = ph
    TRK3.update(ax=ax, ay=Spring(1.2, 0.7).run(ay), ar=ar, bx=bx, by=by, br=br, bph=bph)
    rs = np.random.RandomState(12)
    TRK3["more"] = [dict(t0=T3 + 2.4 + q * 0.62 + rs.uniform(0, 0.2), x0=rs.uniform(-620, 520), y0=-520.0 + rs.uniform(-30, 30), z=[30.0, 85.0, 30.0, 130.0, 85.0, 30.0, 85.0, 130.0][q],
                         notch=rs.uniform(52, 70), rot0=rs.uniform(-40, 40), sc=rs.uniform(0.42, 0.66)) for q in range(8)]
    TRK3["tduck"] = Spring(2.0, 0.4).run(np.array([10.0 * ease(T3 + i / FPS, T_FLARE, T_FLARE + 0.3) for i in range(n)]))
    TRK3["twat"] = Spring(1.7, 0.16).run(np.gradient(TRK3["tduck"]) * FPS * -1.2, 0.0)


def river_frame(t, k_frame):
    set_hc(900.0)
    i = min(len(TRK3["ax"]) - 1, max(0, k_frame - int(T3 * FPS)))
    L = TRK3["leaf"]
    X, Y, ang, n, u, g = L[i + 30]
    cam = (30 * ease(t, T3, SECONDS) - 20, clamp(Y * 0.42 + 36, -118, 112))
    cam = (cam[0], -118 + (cam[1] + 118) * ease(t, T3 - 0.2, T3 + 2.5) if t < T3 + 2.5 else cam[1])
    F = 0.52
    ap = tin_lamp_units(t)
    bob = 6 * math.sin(t * 0.8)
    flick = 0.92 + 0.08 * math.sin(t * 11) * math.sin(t * 2.9)
    trail = [(L[j][0], L[j][1], L[j][5]) for j in range(i + 30 - 26, i + 31)]
    more = []
    for m in TRK3["more"]:
        if t > m["t0"]:
            x_, y_, a_, _, _ = leaf_clock(t, m["t0"], m["x0"], m["y0"], m["notch"], R=120.0)
            hz = {30.0: 0.62, 85.0: 0.42, 130.0: 0.2}[m["z"]]
            more.append(dict(X=x_, Y=y_, z=m["z"], ang=a_ + m["rot0"], scale=m["sc"], haze=hz, blur={30.0: 1.6, 85.0: 1.0, 130.0: 0.5}[m["z"]]))
    fr = TROUT_FACES_RIGHT
    st = dict(beam=dict(apex=ap, z=TIN[2], ang=BEAM3["ang"], half=BEAM3["half"], length=BEAM3["length"], gain=flick),
              leaf=dict(X=X, Y=Y, ang=ang * 1.25, lit=g * flick, trail=trail, squash=1 - 0.2 * abs(math.sin(math.pi * u))),
              back_leaves=more,
              trout=[dict(X=TRK3["ax"][i], Y=TRK3["ay"][i], z=158.0, len=250.0, phase=t * 5.5, amp=8, flip=not fr, rot=TRK3["ar"][i], haze=0.06),
                     dict(X=TRK3["bx"][i], Y=TRK3["by"][i], z=150.0, len=200.0, phase=TRK3["bph"][i], amp=7 + 9 * math.sin(ease(t, T_FLARE, T_FLARE + 0.75) * math.pi),
                          flip=not fr, rot=TRK3["br"][i], haze=0.2)],
              tin=dict(img=None, X=TIN[0], Y=TIN[1] + bob, z=TIN[2]),
              bubbles=[(TIN[0] + 150 + 20 * math.sin(q * 2.1 + t), TIN[1] - 110 - ((t * 70 + q * 83) % 520), 3 + (q % 3) * 2.0, TIN[2]) for q in range(6)])
    tin = tin_sprite(t, TRK3["tduck"][i], TRK3["twat"][i])
    w_ = int(tin.width * TIN_SCALE)
    st["tin"]["img"] = tin
    st["tin"]["upp_scale"] = TIN_SCALE
    return river(t, cam, F, 3, st)


# ------------------------------------------------------------ the film ---
CAPTIONS = [(T2 + 2.4, T2 + 5.5, "A spark, gone under the water?"),
            (T2 + 5.8, T3 - 0.4, "Or the calendar, ticking down to Thanksgiving?"),
            (T3 + 2.5, T3 + 5.6, "A feather, fallen out of the sky?"),
            (T3 + 5.9, SECONDS - 0.4, "Or a flare: is somebody up there in trouble?")]


def picture(t, ink):
    k = ink.i
    if t < T2:
        img, cam, F = bench(t, k)
        m = ease(t, T2 - 1.0, T2 - 0.05)            # murk gathers between the sheets as the lamp goes down
        if m > 0:
            lX, lY = TRK1["X"][min(len(TRK1["X"]) - 1, k)], TRK1["Y"][min(len(TRK1["X"]) - 1, k)]
            rv = river(t, cam, F, 1, dict(leaf=dict(X=lX, Y=lY, ang=0.0, dark=m)))
            img = Image.blend(img, rv, m)
    elif t < T3:
        img = port_frame(t, k)
    else:
        img = river_frame(t, k)
    ink.img = img.convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink._grain = False
    for a, b, s in CAPTIONS:
        if a <= t <= b:
            ink.caption(s, alpha=min(ramp(t, a, a + 0.3), 1 - ramp(t, b - 0.3, b)), size=29)


def build():
    build_sheets()
    build_leaf()
    build_trout()
    build_turkey()
    build_tin()
    build_bench()
    build_painting()
    build_track1()
    build_port()
    build_track2()
    build_motes()
    build_track3()


def main():
    film = Film(SLUG, SECONDS, boil=0, wobble=0)
    build()
    film.picture(picture)
    film.sound(sound)
    film.poster_at = T2 + 6.0
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        times = [float(x) for x in sys.argv[2:]]
        contact(SLUG, cols=3, scale=0.5, times=times or None)


def sound(mix):
    rs = np.random.RandomState(5)
    # the bench: a quiet room, glass on brass pegs, a blade through paper
    mix.room(0, T2 + 0.3, gain=0.022)
    for i, t0 in enumerate(LAND):
        at = t0 + 0.8
        mix.whoosh(t0 + 0.05, 0.75, gain=0.035, pan=-0.5)
        if i == 0:
            mix.thud(at - 0.03, freq=95, gain=0.4)
            mix.step(at, gain=0.2, surface="wood")
        else:
            for q, dt in enumerate((0.0, 0.035, 0.085)):        # four corners do not land together
                t_ = mix.t(0.5)
                f = 2300 + 260 * i + 410 * q
                sig = (np.sin(2 * np.pi * f * t_) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t_)) * np.exp(-t_ * 22)
                mix.add(sig, at + dt, 0.07 - 0.012 * q, pan=-0.4 + 0.4 * q)
            mix.thud(at, freq=120, gain=0.14)
    P = A["painting"]
    for k in range(P["n"]):                          # the brush on glass: a soft drag for every blade
        at = T_P0 + k * P["dt"]
        m_ = int(P["dt"] * 0.72 * RATE)
        tb = np.arange(m_) / RATE
        drag = mix.band(rs.normal(0, 1, m_), 500, 2600) * np.sin(np.pi * tb / tb[-1]) ** 0.6
        mix.add(drag, at, 0.045, pan=-0.35)
    n = int((T_CUT1 - T_CUT0) * RATE)
    tt = np.arange(n) / RATE
    cut = mix.band(rs.normal(0, 1, n), 2600, 8000) * (0.55 + 0.45 * np.sin(2 * np.pi * 1.7 * tt + 1) * np.sin(2 * np.pi * 0.6 * tt))
    cut *= np.minimum(1, np.minimum(tt / 0.1, (tt[-1] - tt) / 0.1))
    mix.add(cut, T_CUT0, 0.05, pan=0.3)
    mix.click(T_CUT1 + 0.05, gain=0.12, bright=5000)
    mix.click(T_GRIP, gain=0.16, bright=7000, seconds=0.02)
    mix.whoosh(T_SLIDE + 0.1, T_IN - T_SLIDE - 0.1, gain=0.03, pan=0.3)
    mix.click(T_IN, gain=0.1, bright=2500)
    mix.click(T_PUSH + 0.3, gain=0.2, bright=1800, seconds=0.05)        # the bench lamp is turned down
    # under water
    dur = SECONDS - T2 + 1.0
    mix.drone(T2 - 1.0, dur, freqs=(49, 73.5, 98, 147), gain=0.075, attack=1.2, release=1.0)
    x = mix.lowpass(mix.noise(dur, "brown"), 420) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * mix.t(dur)))
    mix.add(x * mix.env(len(x), 1.0, 0.01, 1.0, 0.8), T2 - 1.0, 0.16)
    for k in range(60):                              # bubbles
        at = rs.uniform(T2, SECONDS - 0.5)
        t_ = mix.t(0.09)
        f0 = rs.uniform(500, 1300)
        mix.add(np.sin(2 * np.pi * (f0 + 5200 * t_) * t_) * np.exp(-t_ * 38), at, rs.uniform(0.015, 0.05), pan=rs.uniform(-0.8, 0.8))
    mix.click(T2 + 1.25, gain=0.3, bright=2400, seconds=0.04)           # Turkey's lamp
    mix.note(T2 + 1.27, 196, 1.2, gain=0.035, wave="sine", decay=0.9, sustain=0.0)

    def tick(at, k, g, pan):
        f = 1480 if k % 2 == 0 else 1110                # tick, tock
        t_ = mix.t(0.12)
        sig = np.sin(2 * np.pi * f * t_) * np.exp(-t_ * 60) + 0.6 * np.sin(2 * np.pi * f * 0.5 * t_) * np.exp(-t_ * 40)
        mix.add(sig, at, g, pan)
        mix.click(at, gain=g * 0.9, bright=5200, seconds=0.02, pan=pan)

    k = 1
    while T2 + k * BEAT < T3 - 0.05:                  # the leaf's clock, heard from inside the tin
        at = T2 + k * BEAT
        tick(at, k, 0.2, 0.45 if k % 2 else -0.45)
        mix.thud(at + 0.09, freq=84, gain=0.16, seconds=0.2)            # Turkey swallows
        k += 1
    k = 1
    while T3 + k * BEAT < SECONDS - 0.1:              # the same clock from the river: further off
        at = T3 + k * BEAT
        tick(at, k, 0.085, -0.3 if k % 2 else -0.6)
        k += 1
    for m in TRK3["more"]:                            # the season arrives: more clocks start
        j = 1
        while m["t0"] + j * BEAT < SECONDS - 0.1:
            tick(m["t0"] + j * BEAT, j, 0.02, rs.uniform(-0.8, 0.8))
            j += 1
    # the flare
    fl = T_FLARE
    n = int(2.6 * RATE)
    tt = np.arange(n) / RATE
    hiss = mix.band(rs.normal(0, 1, n), 1800, 9000) * np.exp(-tt * 1.3) * np.minimum(1, tt / 0.12)
    mix.add(hiss, fl, 0.07, pan=-0.3)
    mix.bell(fl + 0.05, freq=1318, seconds=3.0, gain=0.07, pan=-0.3)
    mix.whoosh(fl + 0.1, 0.5, gain=0.12, pan=0.5)                       # a trout bolts
    mix.thud(fl + 0.32, freq=70, gain=0.2, pan=0.6)
    mix.reverb(0.22, 1.2)


if __name__ == "__main__":
    main()
