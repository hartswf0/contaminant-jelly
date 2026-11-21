"""porch.py · the porch at dusk and the waterline, in cut paper, for THE DOGS OF TROUTTOWN.

World coordinates are the board's (films/swarm/dogs/board.md): x 0..960, y down, the surface at
y = 400, the door at x 40..170 / y 150..392, the lamp at (205, 140), the porch floor at y = 392, the
step at x 215..300, the sill at x 300..560, the gate posts at x 304 and 346, the path strip behind the
sill at y = 388, the meadow from x = 640.  Every drawing function takes

    (ink, t, oy=0, ...)

where `ink` is a kit.Ink (or a PIL image), `t` is seconds and `oy` is the camera offset: screen y =
world y - oy (F-PORCH 0, F-LAST 150, F-SPLIT 250, F-TOWN 360).  The sky alone moves slower than the
world (parallax), so a crane from porch to water has depth.

Layers, back to front (scene() draws them in this order and calls your cast in between):

    sky  water  hill  [cast: hill]  bank  [cast: strip]  house  lamp  [cast: porch]  person
    sill  radio  [cast: sill]  rail  light  moths  [cast: under]  surface  reeds(front)  [cast: front]

Everything is handmade here: polygons cut with a wobbling knife, one hard paper shadow under each
piece, an amber rim on the lamp side.  No photographs, no type.

Run `python3 films/swarm/dogs/porch.py [out_dir]` to render stills of every state.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from kit import W, H, clamp, lerp, smooth, ease, ramp, mix_color  # noqa: E402

# ------------------------------------------------------------ the contract ---

SURFACE = 400
FLOOR = 392
DOOR = (40, 150, 170, 392)
WALL_END = 215
LAMP = (205, 140)
RAIL_Y = 300
STEP = (215, 372, 300, 392)
RADIO = (285, 366)
SILL = (300, 392, 560, 404)
SILL_WET = 430
GATE = (304, 346, 330)
STRIP_Y = 388
MEADOW_X = 640
DOG_SPOT = (470, 394)
F_PORCH, F_LAST, F_SPLIT, F_TOWN = 0, 150, 250, 360

AMBER = (255, 188, 98)
FINGER = 9.0      # how far the water stands up over the wet half of the sill (surface there is y = 391)
TEAL = (24, 120, 128)
LINE = (226, 248, 238)
SS = 2


def meadow_y(x):
    """Ground height of the right bank (388 at x = 640 rising to 376 at x = 960)."""
    return lerp(388, 376, clamp((x - 640) / 320.0))


def hill_y(x):
    """Crest line of the hill behind the house."""
    pts = [(-10, 268), (230, 250), (400, 228), (560, 215), (660, 252), (780, 330), (960, 350), (1000, 352)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x <= x1:
            return lerp(y0, y1, smooth(clamp((x - x0) / (x1 - x0))))
    return pts[-1][1]


PATH = [(600, 222), (540, 246), (470, 280), (420, 306), (380, 330), (346, 356), (326, 384)]


def path_point(u):
    """Point on the cow path, u 0 (crest) .. 1 (the gate), and the cow scale there."""
    u = clamp(u) * (len(PATH) - 1)
    k = min(int(u), len(PATH) - 2)
    f = u - k
    p0, p1, p2, p3 = PATH[max(k - 1, 0)], PATH[k], PATH[k + 1], PATH[min(k + 2, len(PATH) - 1)]

    def cr(a, b, c, d):
        return 0.5 * (2 * b + (c - a) * f + (2 * a - 5 * b + 4 * c - d) * f * f + (3 * b - a - 3 * c + d) * f ** 3)

    x, y = cr(p0[0], p1[0], p2[0], p3[0]), cr(p0[1], p1[1], p2[1], p3[1])
    return x, y, lerp(0.25, 0.9, clamp((y - 222) / (384 - 222.0)) ** 1.15)


def crane(t, t0, t1, oy0, oy1):
    """Eased camera offset for a crossing: crane(t, 22.0, 24.0, F_PORCH, F_TOWN)."""
    return lerp(oy0, oy1, ease(t, t0, t1))


# ---------------------------------------------------------------- helpers ---

def _h(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def _img(target):
    return target.img if hasattr(target, "img") else target


def _refresh(target):
    if hasattr(target, "img"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


def _paste(target, layer, x, y):
    _img(target).paste(layer, (int(round(x)), int(round(y))), layer)
    _refresh(target)


def _cut(pts, amt=0.8, seed=0, step=16):
    """Re-cut a polygon with a slightly unsteady knife."""
    out = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        m = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(m):
            f = k / m
            s = seed * 13.7 + i * 3.1 + k * 1.7
            out.append((x0 + (x1 - x0) * f + (_h(s) - 0.5) * 2 * amt, y0 + (y1 - y0) * f + (_h(s + 9.3) - 0.5) * 2 * amt))
    return out


def _capsule(a, b, wa, wb, n=6):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = []
    for k in range(n + 1):
        th = ang + math.pi / 2 + math.pi * k / n
        pts.append((a[0] + wa * math.cos(th), a[1] + wa * math.sin(th)))
    for k in range(n + 1):
        th = ang - math.pi / 2 + math.pi * k / n
        pts.append((b[0] + wb * math.cos(th), b[1] + wb * math.sin(th)))
    return pts


def _oval(cx, cy, rx, ry, n=20, a=0.0):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + rx * math.cos(2 * math.pi * k / n) * ca - ry * math.sin(2 * math.pi * k / n) * sa,
             cy + rx * math.cos(2 * math.pi * k / n) * sa + ry * math.sin(2 * math.pi * k / n) * ca) for k in range(n)]


class Sheet:
    """A transparent sheet in world coordinates, drawn at SS x and pasted back at 1 x."""

    def __init__(self, x0, y0, w, h, ss=SS):
        self.x0, self.y0, self.w, self.h, self.ss = x0, y0, int(w), int(h), ss
        self.img = Image.new("RGBA", (self.w * ss, self.h * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, pts):
        s = self.ss
        return [((x - self.x0) * s, (y - self.y0) * s) for x, y in pts]

    def poly(self, pts, fill, shadow=0, cut=0.0, seed=0, rim=None, rim_d=(1.5, -1.0)):
        """A paper piece.  `shadow` is the alpha of a hard shadow 2 px down-right; `rim` a lit edge colour."""
        if cut:
            pts = _cut(pts, cut, seed)
        if shadow:
            self.blend([(x + 2.2, y + 2.6) for x, y in pts], (18, 10, 30, int(shadow)))
        if rim is not None:
            self.blend([(x + rim_d[0], y + rim_d[1]) for x, y in pts], tuple(rim) + (255,) if len(rim) == 3 else rim)
        if len(fill) == 4 and fill[3] < 255:
            self.blend(pts, fill)
        else:
            self.d.polygon(self.P(pts), fill=tuple(fill[:3]) + (255,))

    def blend(self, pts, rgba):
        q = self.P(pts)
        xs, ys = [p[0] for p in q], [p[1] for p in q]
        x0, y0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1)
        x1, y1 = min(self.img.size[0], int(max(xs)) + 2), min(self.img.size[1], int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            return
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in q], fill=rgba[3] if len(rgba) == 4 else 255)
        lay = Image.new("RGBA", m.size, tuple(rgba[:3]) + (0,))
        lay.putalpha(m)
        self.img.alpha_composite(lay, (x0, y0))
        self.d = ImageDraw.Draw(self.img)

    def line(self, pts, fill, width=1.0):
        if len(fill) == 4 and fill[3] < 255:
            # translucent stroke as thin quads
            for a, b in zip(pts, pts[1:]):
                self.blend(_capsule(a, b, width / 2, width / 2, 2), fill)
        else:
            self.d.line(self.P(pts), fill=tuple(fill[:3]) + (255,), width=max(1, int(round(width * self.ss))), joint="curve")

    def rect(self, x0, y0, x1, y1, fill, **kw):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, **kw)

    def done(self, grain=0.0, seed=1):
        img = self.img.resize((self.w, self.h), Image.LANCZOS)
        if grain:
            a = np.asarray(img, np.float32).copy()
            rs = np.random.RandomState(seed)
            lo = rs.normal(0, 1, (self.h // 6 + 2, self.w // 6 + 2)).astype(np.float32)
            lo = np.asarray(Image.fromarray(lo).resize((self.w, self.h), Image.BICUBIC))
            fi = rs.normal(0, 1, (self.h, self.w)).astype(np.float32)
            a[..., :3] = np.clip(a[..., :3] * (1 + grain * (0.6 * lo + 0.4 * fi))[..., None], 0, 255)
            img = Image.fromarray(a.astype(np.uint8), "RGBA")
        return img

    def onto(self, target, oy=0, grain=0.0, seed=1, ox=0):
        _paste(target, self.done(grain, seed), self.x0 - ox, self.y0 - oy)


def _clip_below(img, y):
    """Nothing of the land is drawn below the waterline."""
    a = np.asarray(img).copy()
    a[int(y):, :, 3] = 0
    return Image.fromarray(a, "RGBA")


_cache = {}


def _cached(key, make):
    if key not in _cache:
        if len(_cache) > 90:
            _cache.pop(next(iter(_cache)))
        _cache[key] = make()
    return _cache[key]


def _dim(c, dusk, k=0.2):
    """Night coming on: every outdoor colour loses about a fifth by dusk = 1, toward violet."""
    return mix_color(c, (30, 22, 60), k * clamp(dusk) * 1.6)


def _q(v, n=10):
    return round(clamp(v) * n) / n


# -------------------------------------------------------------------- sky ---

SKY_K = 0.5   # the sky moves half as far as the world when the camera cranes
MOON = (468, 86)
_STARS = [(612, 44), (742, 120), (86, 52), (836, 62), (540, 150), (300, 36), (908, 150), (672, 196), (392, 110),
          (250, 96), (780, 30), (930, 44), (160, 20), (706, 70)]


def _sky_plate(dusk):
    def make():
        hh = 760
        stops = [(0, (44, 34, 92)), (120, (78, 54, 122)), (215, (142, 84, 132)), (290, (214, 122, 112)),
                 (350, (244, 168, 108)), (420, (250, 196, 132)), (hh, (250, 196, 132))]
        col = np.zeros((hh, 3), np.float32)
        for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
            for y in range(y0, y1):
                col[y] = [lerp(a, b, smooth((y - y0) / (y1 - y0))) for a, b in zip(c0, c1)]
        col = col * (1 - 0.22 * dusk) + np.array([24, 18, 62], np.float32) * 0.22 * dusk
        img = Image.fromarray(np.repeat(col[:, None, :], W, 1).clip(0, 255).astype(np.uint8)).convert("RGBA")
        sh = Sheet(0, 0, W, 440)
        # long thin clouds, cut from pink and plum paper
        for k, (cx, cy, ln, th, c) in enumerate([(700, 176, 300, 9, (190, 104, 132)), (330, 204, 250, 7, (206, 118, 126)),
                                                 (840, 232, 220, 8, (226, 134, 116)), (150, 150, 200, 6, (150, 86, 134)),
                                                 (560, 128, 160, 5, (128, 76, 130))]):
            pts = [(cx - ln / 2, cy)] + [(cx - ln / 2 + ln * j / 9, cy - th * (0.5 + 0.8 * _h(k * 9 + j)) * math.sin(math.pi * j / 9) ** 0.5) for j in range(1, 9)]
            pts += [(cx + ln / 2, cy)] + [(cx + ln / 2 - ln * j / 7, cy + th * 0.45 * math.sin(math.pi * j / 7)) for j in range(1, 7)]
            sh.poly(pts, _dim(c, dusk) + (210,), cut=0.5, seed=k)
        # the moon: a pale paper disc, a slice missing, a ring of thin light
        mx, my = MOON
        for r, a in ((46, 16), (36, 22), (28, 30)):
            sh.blend(_oval(mx, my, r, r, 36), (250, 226, 200, a))
        sh.poly(_oval(mx, my, 20, 20, 40), (252, 240, 214), shadow=50, cut=0.3, seed=4)
        sh.blend(_oval(mx + 7, my - 5, 17, 17, 36), (236, 214, 196, 150))
        sh.blend(_oval(mx - 6, my + 5, 4, 3, 12), (226, 204, 190, 150))
        sh.blend(_oval(mx + 2, my - 8, 2.4, 2, 10), (226, 204, 190, 150))
        # the far bank: two pale ridges and a line of trees a long way off, lighter than anything near
        far = [(-10, 330)] + [(x, 318 - 16 * math.sin(x / 170.0 + 1) - 7 * math.sin(x / 61.0)) for x in range(0, 1000, 40)] + [(980, 440), (-10, 440)]
        sh.poly(far, _dim((176, 108, 140), dusk), cut=0.6, seed=7)
        trees = [(-10, 344)]
        for x in range(0, 990, 9):
            trees.append((x, 338 - 10 * abs(math.sin(x / 23.0)) - 9 * _h(x) - 8 * math.sin(x / 200.0)))
        trees += [(980, 440), (-10, 440)]
        sh.poly(trees, _dim((138, 86, 132), dusk), shadow=30)
        sh.blend([(600, 356), (960, 348), (960, 352), (640, 359)], (250, 210, 160, 120))   # far water, catching the sky
        img.alpha_composite(sh.done(0.035, 3), (0, 0))
        return img.convert("RGB")
    return _cached(("sky", dusk), make)


def sky(ink, t, oy=0, dusk=0.0, stars=0.0):
    """Violet sky, moon, clouds, far bank.  dusk 0..1 darkens it by a fifth; stars 0..1 lets them out."""
    plate = _sky_plate(_q(dusk, 20))
    y0 = int(round(oy * SKY_K))
    _img(ink).paste(plate.crop((0, y0, W, y0 + H)), (0, 0))
    _refresh(ink)
    n = int(round(clamp(stars) * len(_STARS)))
    if n:
        d = ImageDraw.Draw(_img(ink), "RGBA")
        for k, (x, y) in enumerate(_STARS[:n]):
            tw = 0.65 + 0.35 * math.sin(t * (1.3 + 0.4 * k) + k * 2.1)
            y -= y0
            a = int(230 * tw)
            d.polygon([(x, y - 3.2), (x + 1, y - 1), (x + 3.2, y), (x + 1, y + 1), (x, y + 3.2), (x - 1, y + 1), (x - 3.2, y), (x - 1, y - 1)],
                      fill=(255, 244, 214, a))
        _refresh(ink)


# ------------------------------------------------------------------- hill ---

HILL = (92, 66, 118)
PALE = (212, 180, 164)


def _hill_plate(dusk):
    def make():
        sh = Sheet(0, 180, W, 240)
        crest = [(x, hill_y(x)) for x in range(-10, 1000, 14)]
        sh.poly(crest + [(1000, 420), (-10, 420)], _dim(HILL, dusk), shadow=70, cut=0.7, seed=2, rim=_dim((150, 98, 140), dusk), rim_d=(0, -1.6))
        # a second, nearer fold of the hill, darker: the slope has a shape
        fold = [(x, hill_y(x) + 34 + 20 * math.sin(x / 130.0) + 0.06 * (x - 200)) for x in range(200, 1000, 18)]
        sh.poly(fold + [(1000, 420), (200, 420)], _dim((78, 56, 106), dusk), shadow=40, cut=0.6, seed=5)
        low = [(x, 352 + 9 * math.sin(x / 90.0 + 2) + 0.02 * (x - 500)) for x in range(330, 1000, 18)]
        sh.poly(low + [(1000, 420), (330, 420)], _dim((66, 48, 96), dusk), shadow=40, cut=0.6, seed=6)
        # dark tufts, so the slope has grass; nothing on the hill is pale except the path
        for k in range(150):
            x = 225 + _h(k * 3.3) * 740
            top = hill_y(x) + 8
            y = top + _h(k * 7.1) ** 0.8 * (392 - top)
            s = lerp(0.45, 1.25, clamp((y - 220) / 170.0))
            c = _dim(mix_color((58, 40, 88), (104, 76, 126), _h(k * 1.9)), dusk)
            sh.poly([(x - 4 * s, y), (x - 2.4 * s, y - 6 * s), (x - 0.8 * s, y - 1.5 * s), (x + 0.6 * s, y - 8 * s), (x + 2 * s, y - 1.5 * s), (x + 4 * s, y - 5 * s), (x + 4.6 * s, y)], c)
        # fence posts on the skyline and one leaning tree: the pasture has an edge
        for k, x in enumerate(range(610, 780, 26)):
            y = hill_y(x)
            sh.poly([(x - 1.2, y + 3), (x - 0.8, y - 9 - 2 * _h(k)), (x + 1.2, y - 9), (x + 1.4, y + 3)], _dim((60, 42, 86), dusk))
        sh.line([(x, hill_y(x) - 6) for x in range(610, 770, 26)], _dim((60, 42, 86), dusk) + (255,), 0.8)
        tx, ty = 846, hill_y(846)
        sh.poly([(tx - 3, ty + 6), (tx - 1, ty - 22), (tx + 5, ty - 46), (tx + 8, ty - 45), (tx + 4, ty - 20), (tx + 4, ty + 6)], _dim((52, 36, 78), dusk))
        for k, (dx, dy, r) in enumerate([(12, -58, 19), (-6, -50, 14), (26, -46, 13), (8, -72, 12), (30, -62, 10)]):
            sh.poly(_oval(tx + dx, ty + dy, r, r * 0.8, 14), _dim((58, 40, 88) if k % 2 else (70, 50, 100), dusk), shadow=40, cut=1.0, seed=k)
        # the worn path: pale because of hooves, one cow wide, widening as it comes down
        left, right = [], []
        for k in range(61):
            u = k / 60.0
            x, y, s = path_point(u)
            x2, y2, _ = path_point(min(1, u + 0.02))
            dx, dy = x2 - x, y2 - y
            ln = math.hypot(dx, dy) or 1
            w = 3.5 + 17 * s + 1.2 * math.sin(k * 1.7)
            left.append((x - dy / ln * w, y + dx / ln * w * 0.55))
            right.append((x + dy / ln * w, y - dx / ln * w * 0.55))
        sh.poly(left + right[::-1], _dim((150, 118, 132), dusk), cut=0.5, seed=8)
        sh.poly([lerp2(a, b, 0.16) for a, b in zip(left, right)] + [lerp2(a, b, 0.84) for a, b in zip(left, right)][::-1], _dim(PALE, dusk), cut=0.4, seed=9)
        for k in range(46):                                           # hoof dints along it
            u = _h(k * 5.7)
            x, y, s = path_point(u)
            x += (_h(k * 2.3) - 0.5) * 22 * s
            sh.blend(_oval(x, y + (_h(k) - 0.5) * 5 * s, 2.6 * s + 0.6, 1.3 * s + 0.4, 8), _dim((170, 136, 140), dusk) + (200,))
        return _clip_below(sh.done(0.05, 11), SURFACE - 180)
    return _cached(("hill", dusk), make)


def lerp2(p, q, x):
    return (lerp(p[0], q[0], x), lerp(p[1], q[1], x))


def hill(ink, t, oy=0, dusk=0.0):
    """The hill behind the house, with the one pale cow path coming down it to the gate."""
    if 420 - oy <= 0:
        return
    _paste(ink, _hill_plate(_q(dusk)), 0, 180 - oy)


# ------------------------------------------------------------------- bank ---

def _bank_plate(dusk):
    def make():
        sh = Sheet(0, 300, W, 112)
        earth, grass = _dim((70, 50, 84), dusk), _dim((60, 66, 92), dusk)
        # the bank behind the water: path strip (y 388) and the meadow rising to the right
        top = [(205, 378)] + [(x, STRIP_Y - 11 + 1.2 * math.sin(x / 31.0)) for x in range(230, 640, 20)] + \
              [(x, meadow_y(x) - 9 + 2 * math.sin(x / 27.0)) for x in range(640, 1000, 20)]
        sh.poly(top + [(1000, 404), (205, 404)], earth, shadow=80, cut=0.6, seed=3, rim=_dim((128, 92, 124), dusk), rim_d=(0, -1.4))
        mead = [(628, 398)] + [(x, meadow_y(x) - 12 + 2.5 * math.sin(x / 19.0)) for x in range(640, 1000, 14)] + [(1000, 404), (628, 404)]
        sh.poly(mead, grass, cut=0.6, seed=4)
        for k in range(120):                                          # meadow grass: blades of two greens
            x = 636 + _h(k * 2.9) * 330
            y = meadow_y(x) - 10 + _h(k * 4.1) * 22
            s = 0.7 + 0.8 * _h(k * 1.3)
            c = _dim(mix_color((52, 60, 90), (96, 108, 116), _h(k * 6.3)), dusk)
            sh.poly([(x - 3 * s, y), (x - 2 * s, y - 7 * s), (x - 0.4 * s, y - 1), (x + 0.8 * s, y - 9 * s), (x + 2 * s, y - 1), (x + 3.6 * s, y - 6 * s), (x + 4 * s, y)], c)
        # the last stretch of the path: pale, flat, one cow wide, from the gate to the drinking place
        strip = [(318, 381)] + [(x, STRIP_Y - 8 + 0.8 * math.sin(x / 23.0)) for x in range(336, 640, 16)] + [(646, 386)] + \
                [(x, STRIP_Y + 1.5 + 0.8 * math.sin(x / 17.0 + 1)) for x in range(632, 320, -16)] + [(314, 390)]
        sh.poly(strip, _dim((150, 118, 132), dusk), cut=0.5, seed=5)
        sh.poly([(x, lerp(y, STRIP_Y - 3.5, 0.3)) for x, y in strip], _dim(PALE, dusk), cut=0.4, seed=6)
        for k in range(26):
            x = 330 + _h(k * 3.7) * 300
            sh.blend(_oval(x, STRIP_Y - 3.5 + (_h(k * 1.1) - 0.5) * 5, 3.4, 1.3, 8), _dim((170, 136, 140), dusk) + (210,))
        # the one gate: two weathered posts, one rail swung open and tied back long ago
        wood, wood_d = _dim((120, 92, 100), dusk), _dim((76, 56, 76), dusk)
        rim = mix_color(wood, AMBER, 0.45)
        sh.poly([(346, 344), (384, 334), (385, 339), (347, 350)], wood_d, shadow=60, cut=0.4, seed=1)       # the rail, folded back
        sh.poly([(346, 362), (384, 352), (385, 357), (347, 368)], wood_d, shadow=60, cut=0.4, seed=2)
        sh.poly([(382, 328), (388, 327), (389, 386), (383, 386)], wood_d, shadow=60, cut=0.3, seed=3)       # the stake it is tied to
        sh.line([(380, 340), (391, 337), (392, 343), (381, 345), (380, 340)], _dim((196, 170, 140), dusk) + (255,), 1.0)
        for k, x in enumerate((GATE[0], GATE[1])):
            sh.poly([(x - 5, 392), (x - 4.4, GATE[2] + 2), (x - 1, GATE[2] - 3), (x + 4, GATE[2] + 1), (x + 5, 392)], wood, shadow=90, cut=0.5, seed=10 + k,
                    rim=rim, rim_d=(-1.4, -0.6))
            sh.line([(x - 1, GATE[2] + 8), (x - 0.4, 386)], wood_d + (255,), 0.7)
            sh.poly([(x - 6, 394), (x - 9, 389), (x - 4, 390), (x, 386), (x + 4, 390), (x + 9, 388), (x + 7, 394)], _dim((58, 46, 82), dusk))
        return _clip_below(sh.done(0.05, 21), SURFACE - 300)
    return _cached(("bank", dusk), make)


def bank(ink, t, oy=0, dusk=0.0):
    """The bank behind the water: the gate, the path strip the drinking cow stands on, the meadow."""
    if 412 - oy <= 0:
        return
    _paste(ink, _bank_plate(_q(dusk)), 0, 300 - oy)


# ------------------------------------------------------------------ house ---

WALL = (98, 84, 128)
TRIM = (168, 150, 168)
PLANK = (132, 92, 76)
INSIDE = (255, 206, 120)


def _boards(sh, x0, x1, y0, y1, c, n, dusk, seed=0):
    """A wooden face cut as separate boards, each a hair different."""
    for k in range(n):
        a, b = lerp(x0, x1, k / n), lerp(x0, x1, (k + 1) / n)
        cc = _dim(mix_color(c, (60, 44, 70), 0.22 * _h(seed + k * 3.1)), dusk)
        sh.poly([(a + 0.5, y0), (b - 0.5, y0), (b - 0.5, y1), (a + 0.5, y1)], cc)


def _house_plate(dusk):
    def make():
        sh = Sheet(0, 0, 330, 480)
        wall = _dim(WALL, dusk)
        # the wall: clapboards, each a strip with its own shadow line
        sh.poly([(-4, 40), (WALL_END, 40), (WALL_END, 384), (-4, 384)], wall, shadow=110)
        for k in range(24):
            y = 62 + k * 14
            c = _dim(mix_color(WALL, (70, 58, 104) if k % 2 else (112, 96, 140), 0.25 + 0.3 * _h(k)), dusk)
            sh.poly([(-4, y), (WALL_END - 8, y + 0.6 * math.sin(k)), (WALL_END - 8, y + 12.4), (-4, y + 12.4)], c)
            sh.blend([(-4, y + 12.2), (WALL_END - 8, y + 12.2), (WALL_END - 8, y + 14), (-4, y + 14)], (36, 26, 66, 120))
        sh.poly([(WALL_END - 9, 40), (WALL_END, 40), (WALL_END, 384), (WALL_END - 9, 384)], _dim((126, 110, 146), dusk), shadow=70,
                rim=mix_color(wall, AMBER, 0.6), rim_d=(1.2, 0))                                   # corner board, lamp side lit
        # the roof: a dark eave with shingles, hanging out over the porch
        sh.poly([(-4, 8), (238, 26), (262, 58), (-4, 50)], _dim((52, 40, 82), dusk), shadow=120, cut=0.5, seed=2)
        for k in range(15):
            x = -2 + k * 17.5
            sh.poly([(x, 12 + k * 1.2), (x + 15, 13 + k * 1.2), (x + 17, 33 + k * 1.3), (x + 2, 31 + k * 1.3)],
                    _dim(mix_color((66, 50, 98), (44, 34, 72), _h(k * 2.3)), dusk))
        sh.poly([(-4, 46), (258, 54), (262, 62), (-4, 56)], _dim((140, 120, 150), dusk), shadow=90, rim=mix_color(TRIM, AMBER, 0.5), rim_d=(0, 1.2))
        # door casing and the transom over it
        x0, y0, x1, y1 = DOOR
        trim = _dim(TRIM, dusk)
        sh.poly([(x0 - 9, 104), (x1 + 9, 104), (x1 + 9, y1 - 8), (x0 - 9, y1 - 8)], trim, shadow=110, cut=0.3, seed=5,
                rim=mix_color(TRIM, AMBER, 0.55), rim_d=(1.4, 0))
        sh.poly([(x0 - 13, 98), (x1 + 13, 98), (x1 + 12, 106), (x0 - 12, 106)], _dim((186, 166, 180), dusk), shadow=90)
        sh.rect(x0, 112, x1, 142, (60, 36, 40))                                                     # transom hole (lit by house())
        sh.rect(x0, y0, x1, y1 - 8, (40, 26, 36))                                                   # the doorway hole
        # sidelight window, right of the door, under the lamp
        sh.poly([(177, 190), (207, 190), (207, 292), (177, 292)], trim, shadow=90, rim=mix_color(TRIM, AMBER, 0.55), rim_d=(1.2, 0))
        sh.rect(181, 194, 203, 286, (60, 36, 40))
        sh.poly([(174, 290), (210, 290), (210, 296), (174, 296)], _dim((186, 166, 180), dusk), shadow=80)
        # the porch deck: boards running away from us, then the front edge, then the dark under it
        deck_top, deck_front = (128, 104, 120), (96, 76, 98)
        sh.poly([(-4, 380), (300, 380), (300, FLOOR), (-4, FLOOR)], _dim(deck_top, dusk), shadow=0)
        for k in range(22):
            xa, xb = -4 + k * 14, -4 + (k + 1) * 14
            sh.poly([(xa + 2.5, 380), (xb + 1.5, 380), (xb - 0.6, FLOOR), (xa + 0.6, FLOOR)],
                    _dim(mix_color(deck_top, (86, 68, 96), 0.5 * _h(k * 1.7)), dusk))
        sh.poly([(-4, FLOOR), (300, FLOOR), (300, 404), (-4, 404)], _dim(deck_front, dusk), shadow=120,
                rim=_dim((170, 146, 150), dusk), rim_d=(0, -1.2))
        for k in range(0, 300, 46):
            sh.line([(k + 20, FLOOR + 2), (k + 20, 404)], _dim((60, 46, 76), dusk) + (255,), 0.8)
        # the step: a box on the porch's right end, top lit, front face in shadow
        sx0, sy0, sx1, sy1 = STEP
        sh.poly([(sx0 + 3, sy0 - 7), (sx1 - 3, sy0 - 7), (sx1, sy0), (sx0, sy0)], _dim((164, 134, 136), dusk), shadow=0)
        sh.poly([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)], _dim((112, 88, 106), dusk), shadow=110, cut=0.3, seed=9,
                rim=mix_color((164, 134, 136), AMBER, 0.5), rim_d=(0, -1.3))
        sh.line([(sx0 + 2, sy0 + 10), (sx1 - 2, sy0 + 10.6)], _dim((74, 56, 84), dusk) + (255,), 0.8)
        for x in (sx0 + 8, sx1 - 8):
            sh.poly(_oval(x, sy0 + 5, 1.2, 1.2, 8), _dim((60, 46, 76), dusk))
        return sh.done(0.045, 31)
    return _cached(("house", dusk), make)


def _piles(sh, xs, dusk, y0=404, y1=474):
    """Legs of the porch and the sill going down into the creek, lost in the water after a few hand-widths."""
    for k, x in enumerate(xs):
        for j in range(10):
            a, b = lerp(y0, y1, j / 10), lerp(y0, y1, (j + 1) / 10) + 0.5
            w = 4.2 - 0.12 * j
            sh.blend([(x - w, a), (x + w, a), (x + w - 0.1, b), (x - w + 0.1, b)], _dim((40, 60, 84), dusk) + (int(215 * (1 - j / 10) ** 1.3),))


def _door_geometry(door):
    """The leaf swings inward on its left edge.  Returns (free-edge x, top inset, bottom inset)."""
    a = math.radians(80) * clamp(door) ** 0.7
    x0, y0, x1, y1 = DOOR
    return x0 + (x1 - x0) * math.cos(a), 13 * math.sin(a), 9 * math.sin(a)


def house(ink, t, oy=0, door=0.25, dusk=0.0, inside=1.0):
    """Wall, roof, door (door 0 shut .. 0.25 ajar .. 1 open, lamp-yellow room behind it), transom,
    sidelight window, deck and step.  `inside` 0..1 is how lit the room is."""
    if 480 - oy <= 0:
        return None
    dq = _q(dusk)
    _paste(ink, _house_plate(dq), 0, -oy)
    x0, y0, x1, y1 = DOOR
    y1 -= 8                                         # the threshold is the back of the deck
    sh = Sheet(30, 100, 190, 300)
    lit = mix_color((70, 44, 50), INSIDE, inside)
    fl = 0.94 + 0.06 * math.sin(t * 7.3) * math.sin(t * 2.9)
    for (a, b, c, d) in ((x0 + 2, 114, x1 - 2, 140), (183, 196, 201, 284)):                         # the lit glass
        sh.rect(a, b, c, d, mix_color((70, 44, 50), (255, 214, 128), inside * fl))
    for k in (1, 2):
        xm = lerp(x0, x1, k / 3)
        sh.rect(xm - 1.5, 112, xm + 1.5, 142, _dim(TRIM, dq))
    sh.rect(181, 238, 203, 241, _dim(TRIM, dq))
    sh.rect(190.6, 194, 193.4, 286, _dim(TRIM, dq))
    sh.blend([(183, 196), (190, 196), (188, 230), (183, 236)], (214, 120, 96, 170))               # a curtain, drawn back
    sh.blend([(201, 196), (194, 196), (196, 230), (201, 236)], (214, 120, 96, 170))
    fx, ti, bi = _door_geometry(door)
    if door > 0.004:
        # the room: warm wall, a floor going back, a coat on a hook and the edge of a table (a life indoors)
        sh.rect(x0, y0, x1, y1, lit)
        sh.blend([(x0, y0), (x1, y0), (x1, y0 + 46), (x0, y0 + 30)], (255, 236, 170, int(120 * inside)))
        sh.poly([(x0, y1 - 26), (x1, y1 - 30), (x1, y1), (x0, y1)], mix_color((84, 50, 48), (214, 150, 86), inside))
        for k in range(1, 6):
            xa = lerp(x0, x1, k / 6)
            sh.line([(lerp(xa, 105, 0.25), y1 - 28), (xa, y1)], mix_color((60, 36, 40), (170, 110, 70), inside) + (255,), 0.8)
        sh.poly([(120, 214), (170, 211), (170, 217), (121, 220)], mix_color((70, 44, 50), (176, 112, 72), inside), shadow=40)      # a shelf, two jars
        sh.poly([(128, 198), (138, 198), (139, 214), (127, 214)], mix_color((70, 44, 50), (206, 140, 84), inside))
        sh.poly([(146, 203), (157, 203), (157, 213), (146, 213)], mix_color((70, 44, 50), (160, 100, 70), inside))
        sh.poly([(118, 300), (170, 296), (170, 304), (120, 308)], mix_color((70, 44, 50), (168, 104, 70), inside), shadow=40)
        sh.poly([(124, 308), (129, 308), (128, y1 - 16), (124, y1 - 16)], mix_color((70, 44, 50), (150, 92, 64), inside))
    # the leaf, seen thinner as it swings in; planks, a brace, a latch
    leaf = [(x0, y0), (fx, y0 + ti), (fx, y1 - bi), (x0, y1)]
    shade = clamp(door) * 0.45
    sh.poly(leaf, _dim(mix_color(PLANK, (52, 34, 44), shade), dq), shadow=110 if door > 0.02 else 0)
    n = 6
    for k in range(n):
        a, b = k / n, (k + 1) / n
        xa, xb = lerp(x0, fx, a), lerp(x0, fx, b)
        c = _dim(mix_color(mix_color(PLANK, (104, 68, 62), _h(k * 2.7)), (52, 34, 44), shade), dq)
        sh.poly([(xa + 0.5, y0 + ti * a + 1), (xb - 0.5, y0 + ti * b + 1), (xb - 0.5, y1 - bi * b - 1), (xa + 0.5, y1 - bi * a - 1)], c)
    brace = _dim(mix_color((110, 74, 66), (46, 30, 40), shade), dq)
    for yy in (0.16, 0.56, 0.9):
        ya = lerp(y0, y1, yy)
        sh.poly([(x0 + 2, ya), (fx - 2, lerp(y0 + ti, y1 - bi, yy)), (fx - 2, lerp(y0 + ti, y1 - bi, yy) + 9), (x0 + 2, ya + 9)], brace, shadow=40)
    kx = lerp(x0, fx, 0.88)
    ky = lerp(y0, y1, 0.56) + 22
    sh.poly(_oval(kx, ky, 3.2, 3.2, 10), (196, 150, 70), shadow=70)
    if door > 0.02:
        sh.blend([(fx, y0 + ti), (fx + 2.2, y0 + ti), (fx + 2.2, y1 - bi), (fx, y1 - bi)], (255, 226, 150, 230))   # the lit edge of the leaf
        # light falling out across the boards
        g = (x1 - fx)
        sh.blend([(fx, y1), (x1, y1), (x1 + 16 + g * 0.35, FLOOR + 1), (fx - 4 + g * 0.1, FLOOR + 1)], (255, 214, 130, int(150 * inside)))
    sh.onto(ink, oy)
    return {"gap": (fx, x1), "leaf": leaf}


# ------------------------------------------------------------------- lamp ---

def lamp(ink, t, oy=0, at=None, level=1.0, bracket=True):
    """The amber lantern.  at=None hangs it on its bracket right of the door; give `at` (world x, y of
    its top ring) when the person carries it."""
    x, y = at or (LAMP[0], LAMP[1] - 12)
    if y - oy > H + 30 or y - oy < -60:
        return LAMP
    sh = Sheet(x - 40, y - 26, 80, 70)
    iron = (44, 32, 52)
    if at is None and bracket:
        sh.poly([(WALL_END - 3, y - 14), (x + 2, y - 12), (x + 2, y - 9), (WALL_END - 3, y - 4)], iron, shadow=90)
        sh.line([(WALL_END - 2, y - 2), (x - 6, y - 10)], iron + (255,), 1.2)
    fl = level * (0.9 + 0.1 * math.sin(t * 9.1) * math.sin(t * 3.7 + 1))
    sh.line([(x, y - 10), (x, y)], iron + (255,), 1.0)
    sh.poly([(x - 9, y + 4), (x, y - 2), (x + 9, y + 4)], iron, shadow=90)
    glass = mix_color((84, 58, 62), (255, 226, 150), clamp(fl))
    sh.poly([(x - 7, y + 4), (x + 7, y + 4), (x + 5.5, y + 22), (x - 5.5, y + 22)], glass)
    sh.poly(_oval(x, y + 14, 2.6, 5 * fl + 0.5, 10), mix_color(glass, (255, 252, 226), fl))
    sh.line([(x - 7, y + 4), (x - 5.5, y + 22)], iron + (255,), 1.0)
    sh.line([(x + 7, y + 4), (x + 5.5, y + 22)], iron + (255,), 1.0)
    sh.poly([(x - 7, y + 22), (x + 7, y + 22), (x + 5, y + 26), (x - 5, y + 26)], iron)
    sh.onto(ink, oy)
    return (x, y + 12)


def _glow_map(cx, cy, pool, key):
    def make():
        yy, xx = np.mgrid[0:430, 0:W].astype(np.float32)
        d = np.hypot(xx - cx, (yy - cy) * 1.05)
        g = 0.85 * np.exp(-(d / 26.0) ** 2) + 0.42 * np.exp(-(d / 95.0) ** 2) + 0.16 * np.exp(-(d / 230.0) ** 2)
        if pool:
            # the pool on the boards: along the deck and the sill as far as x = 560
            fall = np.clip((575 - xx) / 380.0, 0, 1) ** 0.8 * np.clip((xx - 60) / 120.0, 0, 1)
            g += 0.6 * np.exp(-((yy - 390) / 10.0) ** 2) * fall
            g += 0.16 * np.exp(-((yy - 330) / 52.0) ** 2) * np.clip((500 - xx) / 300.0, 0, 1) * np.clip((xx - 150) / 60.0, 0, 1)
        return np.clip(g, 0, 1)
    return _cached(("glow", key), make)


def _door_map(door):
    def make():
        fx, _, _ = _door_geometry(door)
        yy, xx = np.mgrid[0:430, 0:W].astype(np.float32)
        gap = DOOR[2] - fx
        cx = (fx + DOOR[2]) / 2
        g = 0.34 * np.exp(-((xx - cx) / (gap * 0.5 + 34)) ** 2 - ((yy - 285) / 120.0) ** 2)
        g += 0.3 * np.exp(-((yy - 389) / 8.0) ** 2) * np.exp(-((xx - cx - 22) / (gap * 0.6 + 40)) ** 2)
        g += 0.2 * np.exp(-((xx - 105) / 60.0) ** 2 - ((yy - 126) / 16.0) ** 2) + 0.16 * np.exp(-((xx - 192) / 16.0) ** 2 - ((yy - 240) / 50.0) ** 2)
        return np.clip(g * min(1.0, 0.25 + gap / 60.0), 0, 1)
    return _cached(("doorglow", door), make)


def light(ink, t, oy=0, lamp_level=1.0, door=0.25, inside=1.0, lamp_at=None, radio_on=0.0, cold=0.0):
    """The only warm light: lamp halo, its pool on the boards as far as x = 560, the spill from the door
    and windows, the radio dial.  Draw it AFTER the cast above the water so it lies on them too."""
    oy = int(round(oy))
    top = SURFACE + 6 - oy
    if top <= 0:
        return
    img = _img(ink)
    rows = int(min(H, top))
    fl = lamp_level * (0.93 + 0.07 * math.sin(t * 9.1) * math.sin(t * 3.7 + 1))
    if lamp_at is None:
        g = _glow_map(LAMP[0], LAMP[1], True, "lamp") * fl
    else:
        g = _glow_map(int(lamp_at[0] / 8) * 8, int(lamp_at[1] / 8) * 8, False, ("carried", int(lamp_at[0] / 8), int(lamp_at[1] / 8))) * fl
    g = g + _door_map(round(clamp(door) * 50) / 50) * inside
    if radio_on > 0:
        yy, xx = np.ogrid[0:430, 0:W]
        g = g + radio_on * 0.3 * np.exp(-(((xx - RADIO[0]) / 16.0) ** 2 + ((yy - RADIO[1] + 8) / 14.0) ** 2))
    g = np.clip(g[oy:oy + rows], 0, 1) * (1 - 0.35 * cold)
    if g.shape[0] == 0:
        return
    a = np.asarray(img.crop((0, 0, W, g.shape[0])).convert("RGB"), np.float32) / 255.0
    amber = np.array(AMBER, np.float32) / 255.0
    out = 1 - (1 - a) * (1 - g[..., None] * amber * 0.82)
    out = out * (1 + 0.25 * g[..., None] * (amber - 0.5))
    img.paste(Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8)), (0, 0))
    _refresh(ink)


def moths(ink, t, oy=0, scatter=0.0, n=4, at=None):
    """Paper moths round the lamp.  scatter 0..1 blows them outward (the howl)."""
    cx, cy = at or LAMP
    d = ImageDraw.Draw(_img(ink), "RGBA")
    for k in range(n):
        r = 16 + 9 * k + 6 * math.sin(t * 1.3 + k) + 150 * scatter * (0.6 + 0.4 * _h(k))
        a = t * (2.2 + 0.5 * k) * (1 if k % 2 else -1) + k * 1.9
        x, y = cx + r * math.cos(a), cy + 4 + r * 0.6 * math.sin(a * 1.3) - oy
        f = abs(math.sin(t * 21 + k * 2))
        for s in (-1, 1):
            d.polygon([(x, y), (x + s * 4.5, y - 3.5 * f - 1), (x + s * 5, y + 2 * f)], fill=(255, 238, 200, 235))
        d.ellipse([x - 0.9, y - 1.6, x + 0.9, y + 1.6], fill=(120, 90, 80, 255))
    _refresh(ink)


# ------------------------------------------------------------------- sill ---

def _sill_plate(dusk):
    def make():
        x0, y0, x1, y1 = SILL
        sh = Sheet(280, 372, 300, 110)
        _piles(sh, (314, 432, 548), dusk)
        dry_top, dry_face = (206, 164, 132), (138, 102, 100)
        wet_top, wet_face = (122, 112, 122), (74, 78, 100)
        # top of the board (we see a hand's width of it), dry then wet
        sh.blend([(x0 - 2, y0 - 7), (x1 + 2, y0 - 7), (x1 + 4, y0 - 4), (x0 - 2, y0 - 4)], (26, 16, 44, 150))       # its shadow on the bank
        sh.poly([(x0 + 3, y0 - 6), (SILL_WET + 2, y0 - 6), (SILL_WET, y0 + 4), (x0, y0 + 4)], _dim(dry_top, dusk), shadow=0)
        sh.poly([(SILL_WET + 2, y0 - 6), (x1 - 3, y0 - 6), (x1, y0 + 4), (SILL_WET, y0 + 4)], _dim(wet_top, dusk), shadow=0)
        sh.poly([(x0, y0 + 4), (SILL_WET, y0 + 4), (SILL_WET, y1 + 3), (x0, y1 + 3)], _dim(dry_face, dusk), shadow=120, cut=0.3, seed=1,
                rim=_dim((232, 196, 160), dusk), rim_d=(0, -1.3))
        sh.poly([(SILL_WET, y0 + 4), (x1, y0 + 4), (x1, y1 + 3), (SILL_WET, y1 + 3)], _dim(wet_face, dusk), shadow=120, cut=0.3, seed=2,
                rim=_dim((150, 170, 180), dusk), rim_d=(0, -1.3))
        sh.blend([(x0, y1 + 1), (SILL_WET, y1 + 1), (SILL_WET, y1 + 4), (x0, y1 + 4)], (20, 40, 70, 150))            # wet foot of the dry half
        sh.poly([(x1, y0 + 4), (x1 - 3, y0 - 4), (x1 + 1, y0 - 3), (x1 + 3, y0 + 5), (x1 + 2, y1), (x1, y1)], _dim((50, 60, 86), dusk))   # end grain
        for k in range(9):                                               # grain and nail heads
            x = x0 + 14 + k * 28 + 6 * _h(k)
            sh.line([(x, y0 + 6.5 + 2 * _h(k * 3)), (x + 16 + 8 * _h(k * 5), y0 + 7 + 2 * _h(k * 7))], _dim((84, 64, 86), dusk) + (255,), 0.6)
        for x in (x0 + 8, 366, SILL_WET - 6, 494, x1 - 9):
            sh.poly(_oval(x, y0, 1.1, 0.8, 8), _dim((66, 50, 76), dusk))
        return sh.done(0.05, 41)
    return _cached(("sill", dusk), make)


def sill(ink, t, oy=0, dusk=0.0, puddles=()):
    """The one long board at the waterline, dry to x = 430 and wet beyond.  puddles: [(x, size 0..1)]
    are dark wet patches a dripping dog leaves on the dry half."""
    if 482 - oy <= 0:
        return
    _paste(ink, _sill_plate(_q(dusk)), 280, 372 - oy)
    if puddles:
        d = ImageDraw.Draw(_img(ink), "RGBA")
        for x, s in puddles:
            if s <= 0:
                continue
            w = 10 + 22 * s
            d.ellipse([x - w, FLOOR - 3.2 - oy, x + w, FLOOR + 3.4 - oy], fill=(60, 62, 92, int(150 * min(1, s * 2))))
            d.line([(x - w * 0.5, FLOOR - 1 - oy), (x + w * 0.3, FLOOR - 1.4 - oy)], fill=(232, 220, 200, int(120 * min(1, s * 2))), width=1)
        _refresh(ink)


def porch_legs(ink, t, oy=0, dusk=0.0):
    """The porch's legs going down into the creek (drawn by scene() right after the water)."""
    if 480 - oy <= 0:
        return
    img = _cached(("legs", _q(dusk)), lambda: (lambda sh: (_piles(sh, (26, 148, 270), _q(dusk), 402, 478), sh.done())[1])(Sheet(0, 396, 300, 90)))
    _paste(ink, img, 0, 396 - oy)


# ------------------------------------------------------------------ radio ---

def radio(ink, t, oy=0, x=None, y=None, on=0.0, tilt=0.0, dusk=0.0):
    """The small radio.  (x, y) is the middle of its base: default on the step.  `on` 0..1 lights the dial.
    For a radio carried by its handle pass the hand point as (x, y + 22)."""
    x = RADIO[0] if x is None else x
    y = (STEP[1] - 6) if y is None else y
    sh = Sheet(x - 30, y - 50, 60, 60)
    ca, sa = math.cos(tilt), math.sin(tilt)

    def R(px, py):
        px, py = px * 1.25, py * 1.25
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    body, dark = _dim((96, 132, 122), dusk), _dim((48, 52, 76), dusk)
    sh.line([R(-8, -17), R(-7, -23), R(7, -23), R(8, -17)], dark + (255,), 1.6)                     # handle
    sh.line([R(9, -17), R(17, -40)], _dim((170, 170, 180), dusk) + (255,), 0.9)                      # aerial
    sh.poly(_oval(*R(17, -40), 1.3, 1.3, 8), _dim((200, 200, 206), dusk))
    sh.poly([R(-12, -17), R(12, -17), R(13, 0), R(-13, 0)], body, shadow=110, cut=0.3, seed=3, rim=mix_color(body, AMBER, 0.6), rim_d=(-1.2, -0.6))
    sh.poly([R(-10, -14), R(1, -14), R(1, -3), R(-10, -3)], dark)                                   # the grille
    for k in range(4):
        sh.line([R(-9, -12.5 + k * 2.8), R(0, -12.5 + k * 2.8)], _dim((120, 132, 140), dusk) + (255,), 0.6)
    dial = mix_color((70, 60, 70), (255, 214, 120), clamp(on) * (0.9 + 0.1 * math.sin(t * 5)))
    sh.poly(_oval(*R(7, -9), 3.6, 3.6, 12), dial)
    sh.line([R(7, -9), R(7 + 3 * math.cos(t * 0.4), -9 + 3 * math.sin(t * 0.4))], dark + (255,), 0.7)
    sh.poly(_oval(*R(7, -3), 1.2, 1.2, 8), dark)
    sh.onto(ink, oy)
    return {"handle": R(0, -23), "grille": R(-5, -9)}


# ------------------------------------------------------------------- rail ---

def _rail_plate(dusk):
    def make():
        sh = Sheet(0, 280, 310, 120)
        post, bar = _dim((66, 54, 96), dusk), _dim((52, 42, 82), dusk)
        rim = mix_color(post, AMBER, 0.5)
        for k in range(8):                                               # thin balusters: you see the door through them
            x = 46 + k * 22
            sh.poly([(x - 1.3, RAIL_Y + 4), (x + 1.3, RAIL_Y + 4), (x + 1.3, 376), (x - 1.3, 376)], bar)
        sh.poly([(22, 374), (212, 374), (212, 379), (22, 379)], bar, shadow=60)
        for k, x in enumerate((24, 213)):
            w = 4.5
            sh.poly([(x - w, RAIL_Y - 2), (x + w, RAIL_Y - 2), (x + w, 392), (x - w, 392)], post, shadow=110,
                    cut=0.3, seed=k, rim=rim, rim_d=(1.3 if x < LAMP[0] else -1.3, 0))
            sh.poly([(x - w - 2, RAIL_Y - 8), (x + w + 2, RAIL_Y - 8), (x + w + 1, RAIL_Y - 3), (x - w - 1, RAIL_Y - 3)], post, shadow=60)
        sh.poly([(18, RAIL_Y - 4), (224, RAIL_Y - 4), (224, RAIL_Y + 4), (18, RAIL_Y + 4)], _dim((84, 68, 112), dusk), shadow=120, cut=0.3, seed=7,
                rim=mix_color((84, 68, 112), AMBER, 0.6), rim_d=(0, -1.3))
        return sh.done(0.045, 51)
    return _cached(("rail", dusk), make)


def pebble_spot(k):
    """World point where pebble number k (0-based) sits on the rail: two rows of fifteen."""
    return (36 + (k % 15) * 12 + (6 if k >= 15 else 0), RAIL_Y - 7 - (5 if k >= 15 else 0))


def rail(ink, t, oy=0, dusk=0.0, pebbles=""):
    """The front rail (drawn over the person).  pebbles: a string or list, one mark per ask in order,
    'w' white (the same four words) or 'g' grey; they sit on the rail in two rows."""
    if 400 - oy <= 0:
        return
    _paste(ink, _rail_plate(_q(dusk)), 0, 280 - oy)
    if pebbles:
        d = ImageDraw.Draw(_img(ink), "RGBA")
        for k, c in enumerate(pebbles):
            x, y = pebble_spot(k)
            y -= oy
            col = (236, 228, 214) if c == "w" else (128, 118, 138)
            r = 3.3 + 0.9 * _h(k * 3.1)
            d.ellipse([x - r + 1, y - r * 0.7 + 1.5, x + r + 1, y + r * 0.7 + 1.5], fill=(20, 12, 34, 110))
            d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=col + (255,))
            d.ellipse([x - r * 0.5, y - r * 0.55, x + r * 0.2, y - r * 0.1], fill=(255, 250, 240, 120))
        _refresh(ink)


# ----------------------------------------------------------------- person ---

_L = dict(thigh=46.0, shin=44.0, torso=62.0, neck=7.0, upper=34.0, fore=31.0)
P_COL = dict(coat=(92, 136, 150), coat_far=(60, 94, 112), legs=(62, 52, 86), legs_far=(46, 38, 68), skin=(214, 158, 118),
             hair=(74, 46, 44), shoe=(40, 32, 50))

_BASE = dict(x=118.0, y=float(FLOOR), hip=92.0, lean=3.0, head=0.0, turn=0.0, ua=6.0, fa=12.0, ub=-5.0, fb=4.0,
             ta=4.0, sa=0.0, tb=-6.0, sb=-2.0, legk=1.0, foot=0.0, facing=1.0)


def _arm_ik(pose, target, which="a"):
    """Set arm angles so the hand lands on a world point (or as near as the arm reaches)."""
    f = pose["facing"]
    hx, hy = pose["x"], pose["y"] - pose["hip"]
    ln = math.radians(pose["lean"])
    sx, sy = hx + f * _L["torso"] * math.sin(ln), hy - _L["torso"] * math.cos(ln)
    if which == "b":
        sx -= f * 3
    dx, dy = (target[0] - sx) * f, target[1] - sy
    l1, l2 = _L["upper"], _L["fore"] + 7
    d = min(max(math.hypot(dx, dy), abs(l1 - l2) + 1), l1 + l2 - 0.5)
    base = math.atan2(dx, dy)                               # angle from straight down toward facing
    c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    a1 = base - math.acos(c)                                # elbow hangs back and down
    ex, ey = l1 * math.sin(a1), l1 * math.cos(a1)
    a2 = math.atan2(dx * d / max(math.hypot(dx, dy), 1e-6) - ex, dy * d / max(math.hypot(dx, dy), 1e-6) - ey)
    pose["u" + which], pose["f" + which] = math.degrees(a1), math.degrees(a2)
    return pose


def pose(name="stand", p=1.0, t=0.0, x=None, at=None, at_b=None, standing=False):
    """A named pose of the person as a flat dict of numbers (poses blend).

    stand      in the doorway, waiting, radio hand low
    call       leans out, chin up, a hand beside the mouth (speaking; nothing is lettered)
    tap        hand on the rail; p 0..1 lifts and drops it (one tap); `at` moves the hand
    reach      a step out, the arm held low toward the dog; p is how far it comes
    sit        seated on the step beside the door, knees up, hand on knee; p taps the foot
    set_radio  seated, the far arm reaching down to where the radio goes (p 0..1)
    hold_up    holds a length of film up to the lamp (standing=True for the standing version)
    offer      seated, leaning, a low open hand held out and kept there
    crouch     down off the step beside the pile, a hand flat on the boards at x = 330
    kneel      on the porch edge holding the lantern out over the ice
    """
    q = dict(_BASE)
    br = 0.6 * math.sin(t * 1.5)
    if name == "stand":
        q.update(lean=3 + br * 0.4)
    elif name == "call":
        q.update(x=126, lean=3 + 9 * p, head=-13 * p, turn=0.5 * p, ta=10, sa=2, tb=-9)
        _arm_ik(q, lerp2((138, 300), (153 + 2 * math.sin(t * 8) * p, 214), p))
    elif name == "tap":
        q.update(x=132, lean=7, head=6, ta=7, tb=-7)
        tx, ty = at or (184, RAIL_Y - 5)
        _arm_ik(q, (tx, ty - 12 * (1 - p)))
    elif name == "reach":
        q.update(x=lerp(150, 212, p), lean=6 + 22 * p, hip=92 - 9 * p, head=4 + 8 * p, ta=6 + 26 * p, sa=-2 - 8 * p, tb=-8 - 20 * p, sb=-14 * p, turn=0.3)
        tx, ty = at or (318, 318)
        _arm_ik(q, lerp2((q["x"] + 20, 330), (tx, ty), p))
        q.update(ub=-12 * p, fb=-4 * p)
    elif name in ("sit", "set_radio", "offer", "hold_up") and not (name == "hold_up" and standing):
        q.update(x=229, hip=31, lean=13 + br * 0.5, head=4, ta=102, sa=-3, tb=94, sb=-6, legk=0.7)
        knee = (q["x"] + 34, q["y"] - q["hip"] - 8)
        _arm_ik(q, (knee[0] + 1, knee[1] - 5))
        _arm_ik(q, (knee[0] - 12, knee[1] + 1), "b")
        if name == "sit":
            q["foot"] = -22 * p
        elif name == "set_radio":
            q.update(lean=13 + 15 * p, head=4 + 10 * p)
            _arm_ik(q, lerp2((knee[0] - 12, knee[1] + 1), at or (RADIO[0], RADIO[1] - 22), smooth(p)), "b")
        elif name == "offer":
            q.update(lean=13 + 21 * p, head=10 * p, turn=0.3 * p)
            _arm_ik(q, lerp2((knee[0] + 1, knee[1] - 5), at or (312, 368), smooth(p)))
        elif name == "hold_up":
            q.update(lean=13 - 12 * p, head=-20 * p, turn=-0.85 * p)
            _arm_ik(q, lerp2((knee[0] + 1, knee[1] - 5), at or (216, 238), smooth(p)))
            _arm_ik(q, lerp2((knee[0] - 12, knee[1] + 1), at_b or (268, 250), smooth(p)), "b")
    elif name == "hold_up":
        q.update(x=196, lean=-2 * p, head=-16 * p, turn=-0.85 * p)
        _arm_ik(q, lerp2((206, 300), at or (206, 182), smooth(p)))
        _arm_ik(q, lerp2((200, 300), at_b or (250, 196), smooth(p)), "b")
    elif name == "crouch":
        q.update(x=270, hip=37, lean=50, head=-18, ta=80, sa=-20, tb=95, sb=-30, turn=0.25, foot=0)
        _arm_ik(q, at or (330, FLOOR - 4))
        _arm_ik(q, (q["x"] + 30, q["y"] - 44), "b")
    elif name == "kneel":
        q.update(x=262, hip=47, lean=26, head=10, ta=18, sa=-86, tb=30, sb=-84, foot=60)
        _arm_ik(q, at or (338, 316))
        _arm_ik(q, (q["x"] + 26, q["y"] - 20), "b")
    else:
        raise ValueError(name)
    if x is not None:
        dx = x - q["x"]
        q["x"] = x
        if dx and name not in ("stand",):
            pass
    return q


def blend(a, b, w):
    """Pose a toward pose b by w (0..1)."""
    w = clamp(w)
    return {k: lerp(a[k], b[k], w) for k in a}


def shake_head(q, t, shakes=2, dur=1.0):
    """Modifier: the head turns away and back, `shakes` times in `dur` seconds from t = 0.  No."""
    if 0 <= t <= dur:
        q = dict(q)
        env = math.sin(math.pi * t / dur) ** 0.5
        q["turn"] = q["turn"] - 0.95 * env * (0.5 - 0.5 * math.cos(2 * math.pi * shakes * t / dur)) * 1.6 + 0.35 * env
        q["head"] = q["head"] + 3 * env
    return q


def act(t, keys):
    """A performance from keys [(time, name, {options})]: each pose is reached AT its time, after an
    eased move of options['dur'] seconds (default 0.7).  Other options go to pose()."""
    cur = None
    for time, name, *rest in keys:
        o = dict(rest[0]) if rest else {}
        dur = o.pop("dur", 0.7)
        nxt = pose(name, t=t, **o)
        cur = nxt if cur is None else blend(cur, nxt, ease(t, time - dur, time))
    return cur


def _film(sh, a, b, sag=10.0, frames=5):
    """A length of film between two points, hanging a little, amber where the lamp comes through."""
    n = 14
    pts = [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n) + sag * math.sin(math.pi * k / n)) for k in range(n + 1)]
    ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    nx, ny = -(b[1] - a[1]) / ln * 5.2, (b[0] - a[0]) / ln * 5.2
    sh.poly([(x + nx, y + ny) for x, y in pts] + [(x - nx, y - ny) for x, y in pts[::-1]], (44, 30, 40), shadow=60)
    for k in range(frames):
        f0, f1 = (k + 0.12) / frames, (k + 0.88) / frames
        i0, i1 = pts[int(f0 * n)], pts[min(n, int(f1 * n) + 1)]
        sh.poly([(i0[0] + nx * 0.6, i0[1] + ny * 0.6), (i1[0] + nx * 0.6, i1[1] + ny * 0.6), (i1[0] - nx * 0.6, i1[1] - ny * 0.6), (i0[0] - nx * 0.6, i0[1] - ny * 0.6)],
                (255, 204, 120))


def person(ink, t, oy=0, q=None, hold_a=None, hold_b=None, part="all", dusk=0.0, lamp_at=None, shadow=True):
    """Draw the person (a cut-paper figure seen from behind the shoulder: hair, a bun, no face).

    q        a pose dict from pose() / act() / blend()
    hold_a   near hand: None | 'film' (a length held up between both hands) | 'lantern' | 'pebble' | 'reel'
    hold_b   far hand:  None | 'radio'
    part     'all', 'body' (everything but the near arm) or 'arm' (the near arm only): draw 'body', then
             rail(), then 'arm', when the hand is on the rail.
    Returns screen points: hand_a hand_b head shoulder hip knee foot bbox.
    """
    q = q or pose("stand", t=t)
    f = 1 if q["facing"] >= 0 else -1
    lx, ly = lamp_at or LAMP
    hx, hy = q["x"], q["y"] - q["hip"]

    def D(a, ln, o=(0, 0)):
        r = math.radians(a)
        return (o[0] + f * ln * math.sin(r), o[1] + ln * math.cos(r))

    hipp = (hx, hy)
    sh_pt = (hx + f * _L["torso"] * math.sin(math.radians(q["lean"])), hy - _L["torso"] * math.cos(math.radians(q["lean"])))
    ha = math.radians(q["lean"] * 0.6 + q["head"])
    neck_top = (sh_pt[0] + f * _L["neck"] * math.sin(ha), sh_pt[1] - _L["neck"] * math.cos(ha))
    hc = (neck_top[0] + f * 14 * math.sin(ha), neck_top[1] - 14 * math.cos(ha))
    legs = []
    for th, sn, off in ((q["tb"], q["sb"], -3), (q["ta"], q["sa"], 3)):
        h0 = (hx + off * 0.6 * f, hy)
        k = D(th, _L["thigh"] * q["legk"], h0)
        a = D(sn, _L["shin"], k)
        legs.append((h0, k, a))
    arms = []
    for u, fo, off in ((q["ub"], q["fb"], -3), (q["ua"], q["fa"], 2)):
        s0 = (sh_pt[0] + off * f, sh_pt[1] + 5)
        e = D(u, _L["upper"], s0)
        wr = D(fo, _L["fore"], e)
        hd = D(fo, _L["fore"] + 7, e)
        arms.append((s0, e, wr, hd))

    sh = Sheet(hx - 150, hy - 190, 330, 330)
    c = {k: _dim(v, dusk, 0.12) for k, v in P_COL.items()}

    def rimdir(pt):
        dx, dy = lx - pt[0], ly - pt[1]
        n = math.hypot(dx, dy) or 1
        return (dx / n * 1.7, dy / n * 1.7)

    def piece(pts, col, at, k=0.6, cut=0.0, seed=0):
        sh.poly(pts, col, rim=mix_color(col, AMBER, k), rim_d=rimdir(at), cut=cut, seed=seed)

    def leg(i, far):
        h0, k, a = legs[i]
        col = c["legs_far"] if far else c["legs"]
        piece(_capsule(h0, k, 9.5, 7.5), col, k)
        piece(_capsule(k, a, 7.2, 5.2), col, a)
        fa_ = math.radians(q["foot"] if not far else q["foot"] * 0.3)
        toe = (a[0] + f * 15 * math.cos(fa_), a[1] + 3 + 15 * math.sin(fa_))
        heel = (a[0] - f * 5, a[1] + 4)
        piece(_capsule(heel, toe, 4.4, 3.4), c["shoe"], toe, 0.4)
        return a

    def arm(i, far):
        s0, e, wr, hd = arms[i]
        col = c["coat_far"] if far else c["coat"]
        piece(_capsule(s0, e, 7.2, 6.0), col, e)
        piece(_capsule(e, wr, 6.0, 4.6), col, wr)
        piece(_oval(hd[0], hd[1], 5.4, 4.6, 12, math.radians(-q["fa" if not far else "fb"]) * f), _dim(c["skin"], 0.5 if far else 0), hd, 0.5)

    if part in ("all", "body"):
        arm(0, True)
        leg(0, True)
        # trunk: a cardigan with a hem, wider at the hips
        back = _capsule((hipp[0], hipp[1] + 2), (sh_pt[0], sh_pt[1] + 5), 17.5, 16.5, 7)
        piece(back, c["coat"], sh_pt, 0.55, cut=0.5, seed=3)
        sh.poly(_capsule((hipp[0] - f * 2, hipp[1] + 8), (hipp[0] + f * 3, hipp[1] + 9), 16, 16, 6), c["coat"])
        sh.blend(_capsule((lerp(hipp[0], sh_pt[0], 0.2) - f * 7, lerp(hipp[1], sh_pt[1], 0.2)),
                          (lerp(hipp[0], sh_pt[0], 0.85) - f * 8, lerp(hipp[1], sh_pt[1], 0.85)), 5, 5, 4), (30, 40, 70, 90))
        leg(1, False)
        # neck, head, hair, bun: the back of a head, turned a little or a lot
        piece(_capsule(sh_pt, neck_top, 5.5, 5.0), _dim(c["skin"], 0.3), neck_top, 0.4)
        tr = clamp(q["turn"], -1.2, 1.2)
        piece(_oval(hc[0], hc[1], 12.5, 15, 22, ha * f), c["skin"], hc, 0.5)
        if tr > -0.55:
            nx = hc[0] + f * (12.2 + 1.2 * tr)
            sh.poly([(nx - f * 2, hc[1] - 3), (nx + f * (2 + 1.5 * max(tr, 0)), hc[1] + 2), (nx - f * 2, hc[1] + 4.5)], c["skin"])
        back_shift = 4.6 + 4.2 * tr
        sh.poly(_oval(hc[0] - f * back_shift, hc[1] - 1.2, 13.6, 15.6, 22, ha * f), c["hair"], cut=0.5, seed=5)
        sh.poly(_oval(hc[0] - f * 1.5, hc[1] - 8, 13.2, 9, 18, ha * f), c["hair"], cut=0.4, seed=6)
        bun = (hc[0] - f * (10 + 2.5 * tr), hc[1] - 13)
        piece(_oval(bun[0], bun[1], 7.2, 6.4, 14), c["hair"], bun, 0.35, cut=0.4, seed=7)
        if tr > -0.3:
            sh.poly(_oval(hc[0] + f * (1.5 + 3.5 * tr), hc[1] + 2, 2.6, 3.8, 10), _dim(c["skin"], 0.5))
        sh.blend(_oval(hc[0] - f * back_shift - f * 3, hc[1] - 2, 5, 9, 12), (40, 24, 30, 90))
    if part in ("all", "arm"):
        arm(1, False)
        if hold_a == "film":
            _film(sh, arms[1][3], arms[0][3])

    img = sh.done(0.04, 61)
    if shadow and part != "arm":
        a = img.getchannel("A").filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.42))
        shd = Image.new("RGBA", img.size, (16, 8, 30, 0))
        shd.putalpha(a)
        _paste(ink, shd, sh.x0 - 5 * f, sh.y0 + 4 - oy)
        d = ImageDraw.Draw(_img(ink), "RGBA")
        fx = (legs[0][2][0] + legs[1][2][0]) / 2
        d.ellipse([fx - 30, q["y"] - 3 - oy, fx + 34, q["y"] + 5 - oy], fill=(16, 8, 30, 80))
    _paste(ink, img, sh.x0, sh.y0 - oy)
    ha_pt, hb_pt = arms[1][3], arms[0][3]
    if part in ("all", "body") and hold_b == "radio":
        radio(ink, t, oy, hb_pt[0], hb_pt[1] + 30, dusk=dusk)
    if part in ("all", "arm"):
        if hold_a == "lantern":
            lamp(ink, t, oy, at=(ha_pt[0], ha_pt[1] + 2))
        elif hold_a in ("pebble", "reel"):
            d = ImageDraw.Draw(_img(ink), "RGBA")
            r = 3.4 if hold_a == "pebble" else 9
            col = (236, 228, 214) if hold_a == "pebble" else (150, 150, 164)
            d.ellipse([ha_pt[0] - r, ha_pt[1] - r - oy, ha_pt[0] + r, ha_pt[1] + r - oy], fill=col + (255,), outline=(60, 50, 70, 255))
            _refresh(ink)

    def S(pt):
        return (pt[0], pt[1] - oy)

    return {"hand_a": S(ha_pt), "hand_b": S(hb_pt), "head": S(hc), "shoulder": S(sh_pt), "hip": S(hipp), "knee": S(legs[1][1]),
            "foot": S(legs[1][2]), "bbox": (sh.x0, sh.y0 - oy, sh.x0 + sh.w, sh.y0 + sh.h - oy)}


def projection(ink, t, oy=0, image=None, amount=1.0, box=(48, 168, 164, 300)):
    """What the lamp throws through a held-up frame of film onto the door planks: a warm soft-edged
    rectangle, with `image` (a PIL picture of the frame, dark lines on light) inside it if given."""
    if amount <= 0:
        return
    x0, y0, x1, y1 = box
    w, h = int(x1 - x0), int(y1 - y0)
    m = Image.new("L", (w + 24, h + 24), 0)
    ImageDraw.Draw(m).polygon([(12, 14), (w + 10, 12), (w + 12, h + 10), (13, h + 12)], fill=int(205 * clamp(amount)))
    m = m.filter(ImageFilter.GaussianBlur(3.5))
    lay = Image.new("RGBA", m.size, (255, 222, 150, 0))
    if image is not None:
        pic = image.convert("L").resize((w - 12, h - 12), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.7))
        a = np.asarray(pic, np.float32) / 255.0
        rgb = np.zeros((h - 12, w - 12, 3), np.float32)
        for k, (lo, hi) in enumerate(zip((98, 54, 44), (255, 222, 150))):
            rgb[..., k] = lerp(lo, hi, 1) * a + lo * (1 - a)
        lay.paste(Image.fromarray(rgb.astype(np.uint8)), (18, 18))
    dd = ImageDraw.Draw(lay)
    for k in range(7):                                                  # sprocket holes: it is a frame of film
        yy = 20 + k * (h - 16) / 6.5
        for xx in (14, w + 4):
            dd.rectangle([xx, yy, xx + 5, yy + 8], fill=(120, 70, 56, 255))
    wob = 1.2 * math.sin(t * 2.3)
    lay.putalpha(m)
    _paste(ink, lay, x0 - 12 + wob, y0 - 12 - oy + 0.6 * math.sin(t * 3.1))


# ------------------------------------------------------------------ water ---

def _water_column():
    def make():
        stops = [(0, (84, 178, 172)), (26, (48, 148, 150)), (120, (26, 116, 128)), (300, (16, 80, 100)), (460, (12, 58, 82)), (700, (10, 46, 70))]
        col = np.zeros((700, 3), np.float32)
        for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
            for y in range(y0, y1):
                col[y] = [lerp(a, b, (y - y0) / (y1 - y0)) for a, b in zip(c0, c1)]
        return col
    return _cached("watercol", make)


def _smear():
    def make():
        m = Image.new("L", (460, 150), 0)
        d = ImageDraw.Draw(m)
        d.ellipse([60, -26, 320, 30], fill=225)                                                    # the door and the lamp, smeared by the water
        d.polygon([(110, 0), (190, 0), (176, 70), (150, 74)], fill=120)
        d.polygon([(200, 0), (262, 0), (246, 92), (230, 96)], fill=150)
        m = m.filter(ImageFilter.GaussianBlur(15))
        lay = Image.new("RGBA", m.size, AMBER + (0,))
        lay.putalpha(m)
        return lay
    return _cached("smear", make)


def water(ink, t, oy=0, dusk=0.0, cold=0.0, lamp_level=1.0, shafts=1.0):
    """The body of the creek below the surface line: teal, lighter near the top, the lit door an amber
    smear at the upper left, slow shafts of light.  cold 0..1 greys it (the freeze).  Draw it early; the
    town and the swimmers go on top; surface() goes on top of them."""
    oy = int(round(oy))
    top = SURFACE - oy
    if top >= H:
        return
    y0 = int(max(0, top))
    col = _water_column()[int(y0 + oy - SURFACE): int(H + oy - SURFACE)]
    col = col * (1 - 0.16 * dusk)
    if cold > 0:
        g = col.mean(1, keepdims=True)
        col = lerp(col, g * 0.9 + np.array([40, 52, 66], np.float32), 0.75 * cold)
    img = _img(ink)
    img.paste(Image.fromarray(np.repeat(col[:, None, :], W, 1).clip(0, 255).astype(np.uint8)), (0, y0))
    # shafts: long thin wedges of paler paper hanging from the line, swinging slowly
    if shafts > 0:
        lay = Image.new("L", (W // 4, (H - y0) // 4 + 1), 0)
        d = ImageDraw.Draw(lay)
        for k in range(7):
            x = (90 + k * 137 + 40 * math.sin(t * 0.21 + k * 1.7)) / 4
            w = (16 + 12 * _h(k)) / 4
            sl = (60 + 30 * math.sin(t * 0.17 + k)) / 4
            ln = (230 + 120 * _h(k * 3)) / 4
            y = (top - y0) / 4.0
            d.polygon([(x - w, y), (x + w, y), (x + w * 1.3 + sl, y + ln * 0.7), (x + sl * 1.3, y + ln), (x - w * 0.3 + sl, y + ln * 0.7)], fill=int((24 + 16 * _h(k * 5)) * shafts * (1 - 0.7 * cold)))
        lay = lay.filter(ImageFilter.GaussianBlur(3.2)).resize((W, H - y0), Image.BILINEAR)
        pale = Image.new("RGBA", lay.size, (190, 236, 220, 0))
        pale.putalpha(lay)
        img.paste(pale, (0, y0), pale)
    a = lamp_level * (1 - 0.8 * cold) * (0.92 + 0.08 * math.sin(t * 1.9))
    if a > 0.02 and top > -150:
        sm = _smear()
        if a < 0.99:
            sm = sm.copy()
            sm.putalpha(sm.getchannel("A").point(lambda v: int(v * a)))
        img.paste(sm, (int(-10 + 3 * math.sin(t * 0.8)), int(top)), sm)
    _refresh(ink)


def wobble(ink, t, y0, y1, amp=2.5, wave=26.0, speed=2.2, tint=None, amount=0.0):
    """Push a band of the finished picture (screen rows y0..y1) sideways in slow waves, and tint it:
    what a thing looks like through moving water."""
    img = _img(ink)
    y0, y1 = int(max(0, y0)), int(min(H, y1))
    if y1 <= y0:
        return
    a = np.asarray(img.crop((0, y0, W, y1)).convert("RGB"))
    ys = np.arange(y0, y1)[:, None]
    xs = np.arange(W)[None, :]
    sx = np.clip(xs + amp * np.sin(ys / wave * 6.283 + t * speed) + amp * 0.5 * np.sin(xs / 90.0 + ys / 11.0 - t * speed * 1.3), 0, W - 1).astype(np.int32)
    out = np.take_along_axis(a, sx[..., None].repeat(3, 2), axis=1)
    if tint is not None and amount > 0:
        out = (out * (1 - amount) + np.array(tint, np.float32) * amount).astype(np.uint8)
    img.paste(Image.fromarray(out), (0, y0))
    _refresh(ink)


def look_down(ink, t, oy=0, amp=2.2, depth=140):
    """Seen from above: everything under the line (down to `depth` px below it) swims a little."""
    s = SURFACE - oy
    wobble(ink, t, s + 3, s + 3 + depth, amp, 34.0, 1.8)


def look_up(ink, t, oy=0, amp=2.2, haze=0.3, height=60):
    """Seen from below: the strip of the dry world just above the line (legs, hooves, the sill, the
    door) bends and goes teal.  Call it after the above-water cast and before surface()."""
    s = SURFACE - oy
    wobble(ink, t, s - height, s - 2, amp, 46.0, 2.6, tint=(60, 150, 150), amount=haze)


def ring(x, t0, size=1.0):
    """A ring on the water born at world x, time t0.  Pass a list of these to surface(rings=...)."""
    return (x, t0, size)


def _ice_plates():
    xs, x = [], -20.0
    k = 0
    while x < W + 20:
        w = 52 + 54 * _h(k * 4.3)
        xs.append((x, x + w))
        x += w
        k += 1
    return xs


def ice_plates():
    """World x ranges of the plates the ice breaks into (so a hoof can find the plate under it)."""
    return _ice_plates()


def surface(ink, t, oy=0, rings=(), radio_on=0.0, freeze=0.0, stamps=(), crack=0.0, breakup=0.0,
            lamp_level=1.0, cold=0.0, calm=0.0, dusk=0.0):
    """The surface: the bright line, the film of water over the wet half of the sill, glints, rings.

    rings     [(x, t0, size)]: each spreads from x for about 2.4 s x size (a dog going in, a drip, the howl
              with size 3 or 4)
    radio_on  0..1: the radio's grille throws small steady rings from x = 300
    freeze    0..1: a white skin runs along the line from the left
    stamps    [(x, p)]: a white star in the ice at x, p 0..1 as it opens
    crack     0..1: the crack runs the whole width from the first stamp
    breakup   0..1: the ice goes into plates that tip, drift and sink; at 1 the water is clear
    calm      0..1: stills the line (use 1 under the ice)
    Draw it AFTER everything that is in or under the water."""
    s = SURFACE - oy
    if s < -40 or s > H + 30:
        return
    sh = Sheet(0, SURFACE - 34, W, 62)
    calm = max(calm, freeze * (1 - breakup))
    live = 1 - calm
    bumps = []
    rl = list(rings)
    if radio_on > 0:
        per = 0.9
        k0 = int(t / per)
        rl += [(SILL[0] + 2, (k0 - j) * per, 0.55 * radio_on) for j in range(3)]
    for x, t0, size in rl:
        age = t - t0
        life = 2.4 * max(size, 0.5) ** 0.5
        if 0 <= age < life:
            bumps.append((x, age, size, life))

    def yline(x):
        y = SURFACE + live * (1.1 * math.sin(x / 37.0 + t * 1.7) + 0.7 * math.sin(x / 13.0 - t * 2.3))
        if SILL_WET - 4 <= x <= SILL[2] + 22:            # the finger of creek that lies an inch deep over the wet half of the sill
            y -= FINGER * smooth(clamp((SILL[2] + 22 - x) / 22.0)) * (1 - 0.6 * live * 0)
        for bx, age, size, life in bumps:
            r = 20 + 95 * age * (0.6 + 0.4 * size)
            d = abs(x - bx) - r
            if abs(d) < 26:
                y -= (4.2 * size ** 0.6) * (1 - age / life) * math.cos(d / 26 * math.pi / 2) ** 2 * math.cos(d / 5.0)
        return y

    pts = [(x, yline(x)) for x in range(SILL_WET - 4, W + 6, 6)]          # the line the cast crosses: from the sill rightward
    left = [(x, yline(x)) for x in range(-2, SILL[0] + 3, 6)]            # and its dim run under the porch
    ice_a = clamp(freeze) * (1 - breakup) if breakup >= 1 else clamp(freeze)
    front = W * clamp(freeze) * 1.04
    # the glow just under the line, and the line itself (dim where the porch shades it)
    lc = mix_color(_dim(LINE, dusk, 0.1), (200, 214, 226), cold)
    lap = 2.5 * math.sin(t * 1.3) * live
    over = [(SILL_WET - 6 + lap, SURFACE + 7)] + [p for p in pts if p[0] <= SILL[2] + 24] + [(SILL[2] + 24, SURFACE + 7)]
    sh.blend(over, (70, 168, 170, 118))                                 # the inch of water over the board: you see the wood through it
    right = [p for p in pts if p[0] >= SILL[2] + 2]
    for run in (left, right):
        sh.blend(run + [(run[-1][0], SURFACE + 13), (run[0][0], SURFACE + 13)], (150, 226, 214, int(74 * (1 - 0.5 * cold))))
        sh.blend(run + [(run[-1][0], SURFACE + 6), (run[0][0], SURFACE + 6)], (196, 244, 232, int(96 * (1 - 0.5 * cold))))
    sh.poly([(x, y - 1.5) for x, y in pts] + [(x, y + 1.5) for x, y in pts[::-1]], lc)
    sh.poly([(x, y - 1.2) for x, y in left] + [(x, y + 1.2) for x, y in left[::-1]], lc)
    sh.blend(_oval(SILL_WET - 5 + lap, pts[0][1] + 0.5, 5, 1.8, 10), lc + (220,))                                    # where it laps onto the dry wood
    sh.blend([(-2, SURFACE - 3), (296, SURFACE - 3), (300, SURFACE + 14), (-2, SURFACE + 14)], (22, 30, 66, 120))     # the porch's shadow
    # glints: short white cuts that slide; amber ones where the lamp lies on the water
    for k in range(34):
        gx = (k * 67.3 + t * (9 + 5 * _h(k)) * (1 if k % 2 else -1) * live) % (W + 40) - 20
        ln = 5 + 12 * _h(k * 2.1)
        on = 0.5 + 0.5 * math.sin(t * (1.1 + _h(k)) + k)
        if on < 0.25 and live > 0.2:
            continue
        col = mix_color((255, 255, 250), AMBER, clamp((640 - gx) / 340.0) * lamp_level * (1 - cold))
        y = yline(gx) + 3.4 + 4 * _h(k * 3.7)
        sh.blend([(gx - ln, y), (gx, y - 0.9), (gx + ln, y), (gx, y + 0.9)], col + (int(200 * (0.4 + 0.6 * on) * (1 - 0.6 * ice_a)),))
    # rings, seen a little from above: flat ovals opening on the line
    for bx, age, size, life in bumps:
        for j in range(2 + (size > 1.5)):
            a2 = age - j * 0.22
            if a2 <= 0:
                continue
            r = 8 + 95 * a2 * (0.6 + 0.4 * size)
            al = int(230 * (1 - a2 / life) ** 1.4)
            if al <= 4:
                continue
            ry = min(9.0, 2.2 + r * 0.045)
            arc = [(bx + r * math.cos(th), SURFACE - 1 - ry * math.sin(th)) for th in [math.pi * i / 16 for i in range(17)]]
            sh.line(arc, (236, 252, 244, al), 1.1)
            sh.line([(bx - r, SURFACE + 2.5 + ry * 0.5), (bx - r * 0.3, SURFACE + 2.5 + ry * 0.9), (bx + r * 0.3, SURFACE + 2.5 + ry * 0.9), (bx + r, SURFACE + 2.5 + ry * 0.5)],
                    (236, 252, 244, int(al * 0.6)), 0.9)
    # the ice: a slab with a frosted top and a lumpy underside, cut into plates
    if freeze > 0 and breakup < 1:
        b = clamp(breakup)
        cx0 = stamps[0][0] if stamps else 610
        for k, (xa, xb) in enumerate(_ice_plates()):
            xb2 = min(xb, front)
            if xb2 <= xa:
                continue
            gap = 1.2 + 9 * b
            xm = (xa + xb2) / 2
            tip = math.radians((_h(k * 3.3) - 0.5) * 44 * b + 5 * b * math.sin(t * 2.2 + k))
            drop = 30 * b * b * (0.5 + _h(k * 7.7)) + 1.5 * b * math.sin(t * 3 + k)
            al = int(240 * (1 - b) ** 0.7 * clamp(0.3 + (front - xa) / 30.0))
            hw = (xb2 - xa) / 2 - gap / 2 * (1 if b > 0 or crack > 0.02 and abs(xm - cx0) < crack * W else 0)
            if hw <= 1 or al <= 3:
                continue

            if SILL[0] - 2 < xm < SILL_WET - 6:
                xa2 = xa
                if xb2 > SILL_WET - 4:                                  # only the part of this plate that is over water
                    xa2 = SILL_WET - 4
                    xm, hw = (xa2 + xb2) / 2, (xb2 - xa2) / 2
                else:
                    continue

            def R(px, py, xm=xm, tip=tip, drop=drop):
                yl = SURFACE - (FINGER * smooth(clamp((SILL[2] + 22 - (xm + px)) / 22.0)) if SILL_WET - 4 <= xm + px <= SILL[2] + 22 else 0) * (1 - b)
                return (xm + px * math.cos(tip) - py * math.sin(tip), yl + drop + px * math.sin(tip) + py * math.cos(tip))

            n = max(2, int(hw / 6))
            topl = [R(-hw + 2 * hw * j / n, -5.0) for j in range(n + 1)]
            under = [R(hw - 2 * hw * j / n, 6.5 + 2.4 * _h(k * 5 + j)) for j in range(n + 1)]
            sh.blend(topl + under, (198, 222, 238, al))
            sh.blend(topl + [R(hw - 2 * hw * j / n, -1.8) for j in range(n + 1)], (252, 253, 255, al))
            for j in range(3):
                fx_ = -hw + 2 * hw * _h(k * 9 + j)
                sh.line([R(fx_, -1.0), R(fx_ + 5 + 6 * _h(j + k), 5.0)], (240, 248, 253, int(al * 0.8)), 0.7)
        if front < W:
            sh.blend([(front - 26, SURFACE - 4), (front, SURFACE - 2.5), (front + 16, SURFACE), (front, SURFACE + 3), (front - 26, SURFACE + 5)], (250, 252, 255, 150))
        # stars where she stamps, and the crack that runs from them
        for sx, p in stamps:
            if p <= 0 or b >= 0.9:
                continue
            for j in range(9):
                a = math.pi * (j + 0.5) / 9
                ln = (9 + 16 * _h(j * 2.3 + sx)) * clamp(p)
                e = (sx + ln * math.cos(a) * 1.5, SURFACE - 1 - ln * 0.42 * math.sin(a))
                m = lerp2((sx, SURFACE - 1), e, 0.55)
                sh.line([(sx, SURFACE - 1), (m[0] + 2 * (_h(j) - 0.5), m[1] - 1.5), e], (255, 255, 255, int(255 * (1 - b))), 1.3)
            sh.line([(sx - 3, SURFACE - 3.4), (sx + 1, SURFACE + 1), (sx - 2, SURFACE + 5.5)], (40, 80, 110, int(230 * (1 - b))), 1.0)
        if crack > 0 and b < 0.9:
            for sgn in (-1, 1):
                reach = crack * W
                cp = [(cx0, SURFACE - 3)]
                n = int(reach / 14)
                for j in range(1, n + 1):
                    cp.append((cx0 + sgn * j * 14, SURFACE - 3 + 6.5 * _h(j * 1.9 + sgn) + (0 if j % 2 else 1.5)))
                if len(cp) > 1:
                    sh.line(cp, (36, 78, 108, int(235 * (1 - b))), 1.0)
                    sh.line([(x, y - 1.2) for x, y in cp], (255, 255, 255, int(200 * (1 - b))), 0.7)
    sh.onto(ink, oy)


def splash(ink, t, oy=0, x=600, age=0.0, size=1.0, kind="in", lamp_level=1.0, seed=0):
    """A dog through the surface at world x.  age = seconds since it happened.  kind 'in' (a crown that
    falls outward) or 'out' (a column thrown up, then rain).  Lasts about 1.1 s.  Pair it with a ring()."""
    if age < 0 or age > 1.2:
        return
    sh = Sheet(x - 130, SURFACE - 150, 260, 176)
    up = 1.0 if kind == "in" else 1.45
    # the crown: two leaning leaves of water
    if age < 0.42:
        g = math.sin(math.pi * age / 0.42)
        for sgn in (-1, 1):
            w, hgt = (12 + 26 * age / 0.42) * size, (30 if kind == "in" else 52) * g * size
            sh.blend([(x + sgn * 3, SURFACE), (x + sgn * w * 0.6, SURFACE - hgt * 0.7), (x + sgn * (w + 6), SURFACE - hgt), (x + sgn * (w + 3), SURFACE - hgt * 0.4),
                      (x + sgn * (w + 12), SURFACE)], (214, 244, 238, 215))
        if kind == "out":
            sh.blend([(x - 7 * size, SURFACE), (x - 3, SURFACE - 62 * g * size), (x + 4, SURFACE - 58 * g * size), (x + 8 * size, SURFACE)], (230, 250, 244, 225))
    grav = 620.0
    for k in range(int(18 * size ** 0.5) + 4):
        a = math.radians(lerp(-66, 66, _h(seed + k * 1.31)))
        v = (130 + 190 * _h(seed + k * 2.77)) * up * size ** 0.4
        px = x + v * math.sin(a) * age
        py = SURFACE - 2 - v * math.cos(a) * age + 0.5 * grav * age * age
        if py > SURFACE + 1:
            continue
        r = (1.6 + 2.6 * _h(seed + k * 5.1)) * (0.8 + 0.2 * size)
        vx, vy = v * math.sin(a), -v * math.cos(a) + grav * age
        n = math.hypot(vx, vy) or 1
        warm = clamp(1 - math.hypot(px - LAMP[0], py - LAMP[1]) / 420.0) * lamp_level
        col = mix_color((226, 248, 244), (255, 214, 140), warm)
        sh.poly([(px - vx / n * r * 2.2, py - vy / n * r * 2.2), (px + vy / n * r, py - vx / n * r), (px + vx / n * r * 1.1, py + vy / n * r * 1.1), (px - vy / n * r, py + vx / n * r)],
                col, shadow=40)
    if age < 0.7:                                                       # foam on the line
        for k in range(7):
            fx = x + (k - 3) * 9 * size * (0.6 + age) + 3 * _h(k)
            sh.blend(_oval(fx, SURFACE - 0.5, 4.5 * (1 - age / 0.7) + 1, 2.0, 8), (246, 255, 250, int(220 * (1 - age / 0.7))))
    sh.onto(ink, oy)


def drips(ink, t, oy=0, x=470, y=360, age=0.0, wet=1.0, width=30.0, floor=None, seed=0):
    """Water running off a wet dog: drops fall from around (x, y) (its belly or chin) to the boards or
    the surface.  age = seconds since it left the water; wet 0..1 is how soaked.  Thins out over 4 s."""
    if age < 0 or age > 5:
        return
    floor = floor if floor is not None else (FLOOR - 1 if x < SILL[2] else SURFACE)
    d = ImageDraw.Draw(_img(ink), "RGBA")
    n = int(9 * wet)
    for k in range(n):
        per = 0.35 + 0.5 * _h(seed + k * 3.3) + 0.22 * age
        ph = (age + _h(seed + k * 7.7) * per) % per
        if age - ph < 0 or _h(seed + k + int((age - ph) * 10)) > math.exp(-age / 2.2):
            continue
        dx = x + (_h(seed + k * 1.9) - 0.5) * width
        fall = 0.5 * 620 * ph * ph
        yy = y + fall
        if yy < floor:
            ys = yy - oy
            d.polygon([(dx, ys - 5), (dx + 1.5, ys), (dx, ys + 2), (dx - 1.5, ys)], fill=(214, 240, 240, 235))
        elif yy < floor + 26:
            a = int(200 * (1 - (yy - floor) / 26.0))
            r = 2 + (yy - floor) * 0.3
            d.arc([dx - r, floor - 1.4 - oy - r * 0.2, dx + r, floor - 1.4 - oy + r * 0.2], 180, 360, fill=(236, 250, 246, a))
    _refresh(ink)


def bubbles(ink, t, oy=0, source=(600, 520), t0=0.0, t1=None, rate=7.0, seed=0, size=1.0, hang=None):
    """A trail of bubbles from a swimmer up to the line.  source: a world point, or a function
    time -> (x, y) (give the dog's mouth as it moves).  Bubbles are let go from t0 to t1, `rate` a second.
    hang: a time; after it every bubble stays exactly where it was (under the ice)."""
    now = t if hang is None else min(t, hang)
    end = now if t1 is None else min(now, t1)
    d = ImageDraw.Draw(_img(ink), "RGBA")
    k = 0
    while True:
        te = t0 + k / rate
        if te > end:
            break
        age = now - te
        sx, sy = source(te) if callable(source) else source
        v = 46 + 30 * _h(seed + k * 2.3)
        y = sy - v * age - 9 * age * age
        x = sx + (5 + 4 * _h(seed + k)) * math.sin(age * (3 + _h(seed + k * 1.7)) + k) + (_h(seed + k * 4.1) - 0.5) * 8
        r = (1.6 + 3.2 * _h(seed + k * 5.9)) * size * min(1.0, 0.5 + age)
        k += 1
        if y < SURFACE + 2 + r:
            pop = (SURFACE + 2 + r - y) / v
            if hang is not None and t > hang:
                y = SURFACE + 3 + r                                     # flattened against the ice
                d.ellipse([x - r * 1.3, y - oy - r * 0.7, x + r * 1.3, y - oy + r * 0.7], outline=(226, 248, 244, 230), fill=(190, 232, 228, 70))
            elif pop < 0.3:
                rr = r + 22 * pop
                d.arc([x - rr, SURFACE - oy - 2.4, x + rr, SURFACE - oy + 2.4], 180, 360, fill=(240, 252, 248, int(220 * (1 - pop / 0.3))))
            continue
        sy_ = y - oy
        if sy_ < -8 or sy_ > H + 8:
            continue
        d.ellipse([x - r, sy_ - r, x + r, sy_ + r], outline=(226, 248, 244, 235), fill=(190, 232, 228, 60), width=1)
        d.ellipse([x - r * 0.55, sy_ - r * 0.6, x - r * 0.1, sy_ - r * 0.15], fill=(255, 255, 255, 220))
    _refresh(ink)


def spray(ink, t, oy=0, x=470, y=350, age=0.0, power=1.0, dur=1.2, seed=0, lamp_level=1.0):
    """The shake: drops flung off a dog at (x, y) in every direction for `dur` seconds, the ones that
    reach the lamp's light turning amber.  (dog.shake_drops does the drops close to the dog; this is the
    far spray that reaches the porch, the cow and the lamp.)"""
    if age < 0 or age > dur + 0.9:
        return
    d = ImageDraw.Draw(_img(ink), "RGBA")
    for k in range(int(46 * power)):
        born = _h(seed + k * 1.7) * dur
        a = age - born
        if a < 0 or a > 0.9:
            continue
        ang = _h(seed + k * 3.1) * math.pi * 2
        v = (120 + 230 * _h(seed + k * 6.3)) * power ** 0.5
        px = x + math.cos(ang) * v * a
        py = y - 6 - abs(math.sin(ang)) * v * 0.8 * a + 0.5 * 560 * a * a
        if py > (FLOOR if px < SILL[2] else SURFACE):
            continue
        warm = clamp(1 - math.hypot(px - LAMP[0], py - LAMP[1]) / 300.0) * lamp_level
        col = mix_color((224, 246, 244), (255, 206, 120), warm)
        r = 1.2 + 1.8 * _h(seed + k * 9.9)
        vx, vy = math.cos(ang) * v, -abs(math.sin(ang)) * v * 0.8 + 560 * a
        n = math.hypot(vx, vy) or 1
        d.line([(px - vx / n * r * 3, py - oy - vy / n * r * 3), (px, py - oy)], fill=col + (int(230 * (1 - a / 0.9)),), width=max(1, int(r)))
        d.ellipse([px - r, py - oy - r, px + r, py - oy + r], fill=col + (int(255 * (1 - a / 0.9) ** 0.5),))
    _refresh(ink)


# ------------------------------------------------------------------ reeds ---

_REEDS_BACK = [(642 + k * 5.4 + 6 * _h(k * 1.3), 46 + 34 * _h(k * 2.9), k) for k in range(12)] + \
              [(906 + k * 6.0, 34 + 24 * _h(k * 3.9 + 4), 40 + k) for k in range(7)]
_REEDS_FRONT = [(878 + k * 7.5 + 5 * _h(k * 1.9 + 7), 62 + 44 * _h(k * 2.3 + 9), 80 + k) for k in range(11)] + \
               [(700 + k * 6.5, 30 + 22 * _h(k * 1.1 + 2), 120 + k) for k in range(5)]


def reeds(ink, t, oy=0, lean=0.0, front=False, dusk=0.0):
    """Reeds at the water's edge.  front=False: the clump at the meadow's edge (x 640..700) and one far
    right, drawn behind the cast.  front=True: tall blades in the near water at the right, drawn last.
    lean 0..1 bends them away from the dog (the howl).  x 560..640 is kept clear: that is where a dog goes in."""
    if SURFACE - oy < -20 or SURFACE - 130 - oy > H:
        return
    sh = Sheet(620, SURFACE - 130, 350, 150)
    for x, hgt, k in (_REEDS_FRONT if front else _REEDS_BACK):
        base = (SURFACE + 6) if front else (meadow_y(x) + 8 if x < 720 else SURFACE - 1)
        sway = 0.10 * math.sin(t * (0.9 + 0.3 * _h(k)) + k) + 0.05 * math.sin(t * 2.3 + k * 2) + 0.75 * lean * (0.7 + 0.3 * _h(k * 5))
        col = _dim(mix_color((40, 52, 76), (88, 104, 100), _h(k * 4.7)) if not front else mix_color((26, 34, 60), (52, 66, 84), _h(k * 4.7)), dusk)
        spine = [(x + hgt * (j / 6.0) ** 2 * sway, base - hgt * j / 6.0) for j in range(7)]
        w = 2.6 if front else 2.0
        sh.poly([(px - w * (1 - j / 6.5), py) for j, (px, py) in enumerate(spine)] + [(px + w * (1 - j / 6.5), py) for j, (px, py) in list(enumerate(spine))[::-1]],
                col, shadow=40 if front else 0)
        if k % 3 == 0:                                                   # a cattail head
            a, b = spine[4], spine[5]
            sh.poly(_capsule(a, b, 2.8, 2.6, 4), _dim((92, 56, 60) if not front else (58, 36, 52), dusk), rim=_dim((180, 120, 96), dusk), rim_d=(-1.0, -0.4))
        elif k % 3 == 1:                                                 # a bent leaf
            a = spine[3]
            sh.poly([(a[0], a[1]), (a[0] + 16 + 14 * sway, a[1] - 9), (a[0] + 26 + 22 * sway, a[1] + 3), (a[0] + 15 + 12 * sway, a[1] - 5)], col)
    sh.onto(ink, oy)


# ------------------------------------------------------------------ scene ---

def push(target, cx, cy, zoom):
    """A push-in on the finished frame: zoom about screen point (cx, cy), which stays where it is.
    Use after everything (cast included) is drawn: ink.img = porch.push(ink, 470, 380, 1.6)."""
    img = _img(target)
    if zoom <= 1.001:
        return img
    w, h = W / zoom, H / zoom
    x0 = clamp(cx - cx / zoom, 0, W - w)
    y0 = clamp(cy - cy / zoom, 0, H - h)
    out = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
    if hasattr(target, "img"):
        target.img = out
        _refresh(target)
    return out


def scene(ink, t, oy=0, cast=None, *, dusk=0.0, stars=0.0, door=0.25, inside=1.0, lamp_level=1.0, lamp_at=None,
          q=None, hold_a=None, hold_b=None, hand_over_rail=False, show_person=True,
          radio_at="step", radio_on=0.0, pebbles="", puddles=(),
          rings=(), freeze=0.0, stamps=(), crack=0.0, breakup=0.0, cold=None,
          reed_lean=0.0, moth_scatter=0.0, thrown=None, thrown_amount=0.0, from_below=None):
    """Everything in this file, in the right order, with your cast called in between.

    cast: {'hill': fn, 'strip': fn, 'porch': fn, 'sill': fn, 'under': fn, 'front': fn}; each fn(ink, t, oy)
          draws at that depth (cows on the path; cows on the strip and the meadow; whoever comes through the
          door; dogs and things on the sill; swimmers and the town; anything over the water line).
    radio_at: 'step' | None (carried: pass hold_b='radio') | (x, y)
    thrown: a PIL picture the lamp throws on the door; thrown_amount 0..1
    from_below: None = decide from oy (true when the line is in the top third of the frame)
    Returns the person's screen points (or None)."""
    cast = cast or {}
    oy = int(round(oy))            # whole pixels: the cut edges stay crisp while the camera cranes
    cold = (clamp(freeze) * (1 - clamp(breakup))) if cold is None else cold

    def call(k):
        if k in cast and cast[k]:
            cast[k](ink, t, oy)

    below = (SURFACE - oy < 90) if from_below is None else from_below
    sky(ink, t, oy, dusk, stars)
    water(ink, t, oy, dusk, cold, lamp_level)
    porch_legs(ink, t, oy, dusk)
    hill(ink, t, oy, dusk)
    call("hill")
    bank(ink, t, oy, dusk)
    reeds(ink, t, oy, reed_lean, False, dusk)
    call("strip")
    house(ink, t, oy, door, dusk, inside)
    if thrown_amount > 0:
        projection(ink, t, oy, thrown, thrown_amount)
    if lamp_at is None:
        lamp(ink, t, oy, level=lamp_level)
    call("porch")
    if radio_at == "step":
        radio(ink, t, oy, on=radio_on, dusk=dusk)
    elif radio_at:
        radio(ink, t, oy, radio_at[0], radio_at[1], on=radio_on, dusk=dusk)
    pts = None
    if show_person:
        pts = person(ink, t, oy, q, hold_a, hold_b, "body" if hand_over_rail else "all", dusk, lamp_at)
    sill(ink, t, oy, dusk, puddles)
    call("sill")
    rail(ink, t, oy, dusk, pebbles)
    if show_person and hand_over_rail:
        a = person(ink, t, oy, q, hold_a, None, "arm", dusk, lamp_at)
        pts.update(hand_a=a["hand_a"])
    light(ink, t, oy, lamp_level, door, inside, lamp_at, radio_on, cold)
    if lamp_at is None:
        moths(ink, t, oy, moth_scatter)
    if below:
        look_up(ink, t, oy)
    call("under")
    surface(ink, t, oy, rings, radio_on, freeze, stamps, crack, breakup, lamp_level, cold, dusk=dusk)
    reeds(ink, t, oy, reed_lean, True, dusk)
    call("front")
    return pts


# ----------------------------------------------------------------- stills ---

def _still(name, out, t=3.0, oy=0, zoom=None, after=None, **kw):
    from kit import Ink
    ink = Ink(t, int(t * 24))
    ink.paper()
    pts = scene(ink, t, oy, **kw)
    if after:
        after(ink, t, oy, pts)
    if zoom:
        push(ink, *zoom)
    img = ink.finish()
    img.save(Path(out) / f"{name}.png")
    return img


def stills(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    S = lambda n, **kw: _still(n, out, **kw)
    S("01_stand_ajar", q=pose("stand"), hold_b="radio", radio_at=None, door=0.7)
    S("02_call", q=pose("call"), hold_b="radio", radio_at=None, door=0.5)
    S("03_tap", q=pose("tap"), hold_b="radio", radio_at=None, door=0.5, hand_over_rail=True, pebbles="w")
    S("04_reach", q=pose("reach"), hold_b="radio", radio_at=None, door=0.6, pebbles="w")
    S("05_sit_radio", q=pose("sit"), radio_on=1.0, pebbles="w", door=0.3)
    S("06_set_radio", q=pose("set_radio"), radio_at=None, hold_b="radio", pebbles="w", door=0.3)
    S("07_hold_up", q=pose("hold_up"), hold_a="film", radio_on=1.0, pebbles="wwgwg", door=0.12, thrown_amount=1.0, dusk=0.3)
    S("08_shake_head", t=0.5, q=shake_head(pose("hold_up", standing=True), 0.35), hold_a="film", radio_on=1.0, door=0.1, thrown_amount=1.0, dusk=0.8)
    S("09_offer", q=pose("offer"), radio_on=1.0, pebbles="wwgwg", puddles=[(350, 0.8), (400, 0.5)])
    S("10_crouch", q=pose("crouch"), radio_on=1.0, pebbles="wwgwg", puddles=[(350, 0.8), (400, 0.5)])
    S("11_door_shut_night", show_person=False, door=0.0, dusk=1.0, stars=1.0)
    S("12_door_open", show_person=False, door=1.0)
    S("13_splash_in", q=pose("sit"), radio_on=1, rings=[ring(600, 2.8)], after=lambda ink, t, oy, p: splash(ink, t, oy, 600, 0.2))
    S("14_splash_out_spray", q=pose("sit"), radio_on=1, rings=[ring(590, 2.2, 1.3), ring(470, 2.6, 0.5)], puddles=[(455, 0.9)],
      after=lambda ink, t, oy, p: (splash(ink, t, oy, 590, 0.8, kind="out"), spray(ink, t, oy, 455, 356, 0.7), drips(ink, t, oy, 455, 366, 0.6)))
    S("15_howl_rings", q=pose("crouch"), radio_on=1, rings=[ring(560, 1.6, 4), ring(560, 2.1, 4), ring(560, 2.6, 4)], reed_lean=1.0, moth_scatter=1.0)
    S("16_split", oy=F_SPLIT, q=pose("sit"), radio_on=1,
      after=lambda ink, t, oy, p: bubbles(ink, t, oy, lambda te: (420 + 40 * te, 560 - 20 * te), 0.0))
    S("17_town_from_below", oy=F_TOWN, q=pose("sit"), radio_on=1, rings=[ring(600, 2.2)],
      after=lambda ink, t, oy, p: bubbles(ink, t, oy, (590, 560), 0.0))
    S("18_freezing", oy=F_SPLIT, q=pose("kneel"), hold_a="lantern", lamp_at=(338, 330), freeze=0.6)
    S("19_frozen_stamp", oy=F_SPLIT, q=pose("kneel"), hold_a="lantern", lamp_at=(338, 330), freeze=1.0, stamps=[(610, 1.0)], crack=0.5)
    S("20_breakup", oy=F_SPLIT, q=pose("kneel"), hold_a="lantern", lamp_at=(338, 330), freeze=1.0, stamps=[(610, 1.0)], crack=1.0, breakup=0.5)
    S("21_frozen_porch", q=pose("kneel"), hold_a="lantern", lamp_at=(338, 330), freeze=1.0, stamps=[(610, 0.7)], crack=0.2)
    S("22_last", oy=F_LAST, q=pose("hold_up"), hold_a="film", radio_on=1, door=0.2, dusk=1.0, stars=0.5, thrown_amount=1.0, pebbles="w" * 16 + "g" * 14)
    S("23_medium_on_sill", q=pose("sit", p=1), radio_on=1, zoom=(470, 392, 1.8))
    print("stills ->", out)


if __name__ == "__main__":
    import tempfile
    stills(sys.argv[1] if len(sys.argv) > 1 else Path(tempfile.gettempdir()) / "porch_stills")
