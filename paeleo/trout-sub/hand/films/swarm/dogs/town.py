"""TROUTTOWN · the town under the creek, for THE DOGS OF TROUTTOWN.

Everything is laid in planes (scion/animation-44, animation-05): far water, hazed far town, the back row of
houses, main street with its gravel, the cast (yours and the peoplefish), near weed and motes. Each plane has a
depth; the camera (a `Cam`) moves them by different amounts, and distance is carried by haze, not by blur alone.

What is foraged, what is handmade
- Foraged (through films/swarm/c13/world.py, imported, not edited): the river's painted water plane, its hazed
  boulder plane, its gravel bed, the torn-paper weed, and Denton's 1896 brook trout (public domain), which the
  peoplefish are cut from.
- Handmade here: every building (sunk things), the lamps, the notice board and its pages, the desks, the bubbles,
  the holes, the surface seen from below, the fishes' eyes, fins, satchels and hats.
- The children's drawings in the bubbles and on the pages are redrawn from the pencil strokes that five earlier
  films traced by eye from the class sheets (c10 the jaw, c13 the fish and the bell, c16 the boxy sub, c25 the
  fish in a bowl with legs, c33 the bars). No photograph is loaded. No lettering is drawn anywhere.

World coordinates are the director's board's: x 0..960, y down, the surface at y = 400, the gravel at y = 800.
See TOWN.md for every function. `python3 films/swarm/dogs/town.py` writes the test stills town_*.png.
"""

from __future__ import annotations

import importlib.util
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
FILMS = _HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import Ink, W, H, FPS, clamp, ramp, smooth, ease, lerp, lerp2, mix_color  # noqa: E402


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


w = _load("c13_world_for_town", FILMS / "swarm" / "c13" / "world.py")      # river planes, weed, trout

# ------------------------------------------------------------------ places ---

SURFACE_Y = 400            # the bright line
BED_Y = 800                # where feet, tails and buildings stand
DOOR_X = (40, 170)         # the lit door above, as seen up through the surface
LAMP_ABOVE_X = 205         # the porch lamp above
BOARD = (380, 690, 470, 780)          # the notice board's panel
SCHOOL = (600, 600, 900, 800)         # the school with its bell on top
YARD = (520, 900)                     # the fenced yard in front of the school (gate at x 548..572)
MAKING = (480, 770, 600, 800)         # the making place the digger builds
DINER = (70, 700, 258, 802)
SIGN_XY = (30, 728)                   # the welcome sign's plank (no lettering)
LAMPS = [(64, 728), (275, 728), (355, 728), (490, 728), (565, 728), (930, 728)]   # lamp heads, left to right
BELL_HANG = (750, 611)                # where the school bell hangs
SLATE_XY = (798, 806)                 # the teacher's slate on its easel (foot)
TEACHER_XY = (840, 812)
SEATS = [(612, 832), (652, 832), (692, 832), (732, 832),      # front row, child 0 is the jaw child (blue satchel)
         (634, 809), (674, 809), (714, 809), (754, 809)]      # back row
DRAWINGS = ("jaw", "fish_bell", "sub", "bowl_legs", "bars")
CHILD_DRAWS = ("jaw", "fish_bell", "sub", "bowl_legs", "bars", "fish_bell", "jaw", "bars")

WATER = (30, 86, 94)       # the dusk creek's middle colour, used for haze
LINE = (14, 30, 34)
AMBER = (255, 186, 92)
GRADE = (0.62, 0.80, 0.84)             # daylight paper -> dusk under water


# ------------------------------------------------------------------ camera ---

class Cam:
    """Where the camera is. screen = world shifted up by `oy` (the board's "offset"), sideways by `ox`,
    then zoomed about the middle of the frame. Cam(360) is F-TOWN; Cam(250) F-SPLIT; Cam(150) F-LAST; Cam(0) F-PORCH.
    Planes with depth < 1 move and zoom less (parallax); depth > 1 more."""

    def __init__(self, oy=360.0, ox=0.0, zoom=1.0):
        self.oy, self.ox, self.zoom = float(oy), float(ox), float(zoom)

    @staticmethod
    def look(wx, wy, zoom=1.0):
        """A camera centred on world point (wx, wy)."""
        return Cam(wy - H / 2, wx - W / 2, zoom)

    def mix(self, other, f):
        o = as_cam(other)
        return Cam(lerp(self.oy, o.oy, f), lerp(self.ox, o.ox, f), math.exp(lerp(math.log(self.zoom), math.log(o.zoom), f)))

    def s(self, depth=1.0):
        return max(0.15, 1 + (self.zoom - 1) * depth)

    def centre(self, depth=1.0):
        ky = 1 - (1 - depth) * 0.35
        return (W / 2 + self.ox * depth, 630 + (self.oy - 360) * ky)

    def xy(self, wx, wy, depth=1.0):
        """World point -> screen point."""
        cx, cy = self.centre(depth)
        z = self.s(depth)
        return ((wx - cx) * z + W / 2, (wy - cy) * z + H / 2)

    def world(self, sx, sy, depth=1.0):
        cx, cy = self.centre(depth)
        z = self.s(depth)
        return ((sx - W / 2) / z + cx, (sy - H / 2) / z + cy)

    def surface(self):
        """Screen y of the surface line."""
        return self.xy(0, SURFACE_Y)[1]


def as_cam(c):
    if isinstance(c, Cam):
        return c
    if c is None:
        return Cam(360)
    if isinstance(c, (int, float)):
        return Cam(c)
    return Cam(*c)


F_PORCH, F_SPLIT, F_TOWN, F_LAST = Cam(0), Cam(250), Cam(360), Cam(150)


# ----------------------------------------------------------------- cutting ---

class _Cut:
    """A sheet at k pixels per world unit to cut a plane from."""

    def __init__(self, x0, y0, x1, y1, k=2, seed=1):
        self.x0, self.y0, self.k = x0, y0, k
        self.img = Image.new("RGBA", (int((x1 - x0) * k), int((y1 - y0) * k)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.rs = random.Random(seed)

    def P(self, p):
        return ((p[0] - self.x0) * self.k, (p[1] - self.y0) * self.k)

    def _hand(self, pts, wob, closed=True):
        out = []
        seq = list(pts) + ([pts[0]] if closed else [])
        for (xa, ya), (xb, yb) in zip(seq, seq[1:]):
            n = max(1, int(math.hypot(xb - xa, yb - ya) / 7))
            for q in range(n):
                f = q / n
                j = 0 if q == 0 else wob
                out.append(self.P((xa + (xb - xa) * f + self.rs.uniform(-j, j), ya + (yb - ya) * f + self.rs.uniform(-j, j))))
        if not closed:
            out.append(self.P(seq[-1]))
        return out

    def poly(self, pts, fill=None, line=LINE, width=1.3, wob=0.55):
        pp = self._hand(pts, wob)
        if fill is not None:
            self.d.polygon(pp, fill=_rgba(fill))
        if line is not None and width:
            self.d.line(pp + [pp[0]], fill=_rgba(line), width=max(1, int(round(width * self.k))), joint="curve")

    def rect(self, x0, y0, x1, y1, fill=None, line=LINE, width=1.3, wob=0.55):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, line, width, wob)

    def ell(self, cx, cy, rx, ry, fill=None, line=LINE, width=1.3, a0=0, a1=360, wob=0.35):
        n = max(10, int((rx + ry) * 0.6))
        pts = [(cx + rx * math.cos(math.radians(lerp(a0, a1, q / n))), cy + ry * math.sin(math.radians(lerp(a0, a1, q / n)))) for q in range(n + 1)]
        if a1 - a0 >= 360:
            self.poly(pts[:-1], fill, line, width, wob)
        else:
            if fill is not None:
                self.d.polygon([self.P(p) for p in pts], fill=_rgba(fill))
            if line is not None:
                self.line(pts, line, width)

    def line(self, pts, col=LINE, width=1.3, wob=0.4):
        pp = self._hand(pts, wob, closed=False)
        self.d.line(pp, fill=_rgba(col), width=max(1, int(round(width * self.k))), joint="curve")

    def dot(self, x, y, r, col):
        px, py = self.P((x, y))
        r *= self.k
        self.d.ellipse([px - r, py - r, px + r, py + r], fill=_rgba(col))

    def plane(self):
        return (self.img, (self.x0, self.y0), self.k)


def _rgba(c):
    return tuple(int(v) for v in c) if len(c) == 4 else tuple(int(v) for v in c) + (255,)


def _paperize(img, seed=0, grain=0.15, grade=GRADE, haze=0.0, haze_col=WATER):
    """Give a cut sheet the tooth of painted paper, then sink it into the dusk water."""
    a = np.asarray(img, np.float32).copy()
    h, ww = a.shape[:2]
    n = w.vnoise((h, ww), 46, seed=seed, octaves=3) - 0.5
    fib = w.vnoise((h, ww), 5, seed=seed + 3) - 0.5
    a[..., :3] *= (1 + n * grain * 2 + fib * 0.07)[..., None]
    a[..., :3] *= np.array(grade, np.float32)
    if haze:
        a[..., :3] = a[..., :3] * (1 - haze) + np.array(haze_col, np.float32) * haze
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def _blit(ink, plane, cam, depth=1.0, alpha=1.0, clip_top=None):
    """Lay a plane through the camera. Sub-pixel exact (the source box is a float box)."""
    img, (wx0, wy0), k = plane
    z = cam.s(depth)
    cx, cy = cam.centre(depth)
    sx0 = (wx0 - cx) * z + W / 2
    sy0 = (wy0 - cy) * z + H / 2
    sx1 = sx0 + img.width / k * z
    sy1 = sy0 + img.height / k * z
    top = 0 if clip_top is None else max(0, int(math.ceil(clip_top)))
    dx0, dy0 = max(0, int(math.floor(sx0))), max(top, int(math.floor(sy0)))
    dx1, dy1 = min(W, int(math.ceil(sx1))), min(H, int(math.ceil(sy1)))
    if dx1 <= dx0 or dy1 <= dy0:
        return
    f = k / z
    box = (clamp((dx0 - sx0) * f, 0, img.width - 1), clamp((dy0 - sy0) * f, 0, img.height - 1),
           clamp((dx1 - sx0) * f, 1, img.width), clamp((dy1 - sy0) * f, 1, img.height))
    reg = img.resize((dx1 - dx0, dy1 - dy0), Image.BILINEAR, box=box)
    if reg.mode == "RGBA":
        m = reg.getchannel("A")
        if alpha < 1:
            m = m.point(lambda v: int(v * alpha))
        ink.img.paste(reg, (dx0, dy0), m)
    elif alpha < 1:
        ink.img.paste(reg, (dx0, dy0), Image.new("L", reg.size, int(255 * alpha)))
    else:
        ink.img.paste(reg, (dx0, dy0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _layer(size):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    return im, ImageDraw.Draw(im, "RGBA")


@lru_cache(maxsize=32)
def _glow(r, col=AMBER, power=2.0):
    r = max(2, int(r))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
    d = np.clip(1 - np.hypot(xx, yy) / r, 0, 1) ** power
    a = np.zeros((2 * r + 1, 2 * r + 1, 4), np.float32)
    a[..., :3] = np.array(col, np.float32)
    a[..., 3] = d * 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def _put_glow(ink, x, y, r, alpha=1.0, col=AMBER, power=2.0):
    if alpha <= 0.01 or r < 2:
        return
    g = _glow(int(r), col, power)
    m = g.getchannel("A").point(lambda v: int(v * clamp(alpha)))
    ink.img.paste(g, (int(x - g.width / 2), int(y - g.height / 2)), m)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------- the planes ---

_P = {}


def _planes():
    if _P:
        return _P
    back, far, bed = w._river_planes()
    g = np.array(GRADE, np.float32) * np.array((0.86, 0.94, 0.98), np.float32)
    # water: the river's painted plane, stretched over the tall town and sunk into dusk
    wa = np.asarray(back.resize((1600, 760), Image.BICUBIC), np.float32) * g
    yy = np.linspace(0, 1, 760, dtype=np.float32)[:, None, None]
    wa = wa * (1.06 - 0.34 * yy) + np.array((26, 14, 46), np.float32) * (0.22 * (1 - yy))        # a little violet near the top
    _P["water"] = (w._img(wa).convert("RGB"), (-320, 396), 1)
    # far: the river's hazed boulders and weed, with a far quarter of the town on them
    fa = np.asarray(far, np.float32).copy()
    fa[..., :3] = fa[..., :3] * g * 0.92 + np.array(WATER, np.float32) * 0.10
    fimg = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8), "RGBA")
    fc = _Cut(-120, 330, 1080, 870, k=1, seed=5)
    fl = _Cut(-120, 330, 1080, 870, k=1, seed=6)
    rs = random.Random(12)
    col = mix_color((30, 62, 70), WATER, 0.45)
    for q in range(15):
        x = -90 + q * 80 + rs.uniform(-20, 20)
        ht, wd = rs.uniform(70, 190), rs.uniform(26, 50)
        base = 790 + rs.uniform(-10, 14)
        kind = q % 4
        if kind == 0:        # a bottle
            fc.poly([(x, base), (x, base - ht * 0.7), (x + wd * 0.3, base - ht * 0.85), (x + wd * 0.3, base - ht), (x + wd * 0.7, base - ht),
                     (x + wd * 0.7, base - ht * 0.85), (x + wd, base - ht * 0.7), (x + wd, base)], col, None)
        elif kind == 1:      # a tin with a pitched lid
            fc.poly([(x, base), (x, base - ht * 0.6), (x + wd / 2, base - ht * 0.82), (x + wd, base - ht * 0.6), (x + wd, base)], col, None)
        elif kind == 2:      # a jar
            fc.ell(x + wd / 2, base - ht * 0.36, wd * 0.6, ht * 0.4, col, None)
            fc.rect(x + wd * 0.2, base - ht * 0.8, x + wd * 0.8, base - ht * 0.6, col, None)
        else:                # a kettle
            fc.ell(x + wd / 2, base - ht * 0.3, wd * 0.7, ht * 0.34, col, None)
            fc.line([(x + wd, base - ht * 0.4), (x + wd * 1.5, base - ht * 0.66)], col, 5)
        for _ in range(rs.randint(1, 3)):
            lx, ly = x + rs.uniform(0.25, 0.75) * wd, base - rs.uniform(0.45, 0.7) * ht
            fl.rect(lx - 2, ly - 3, lx + 2, ly + 2, (255, 200, 120, 210), None)
    fimg.alpha_composite(fc.img.filter(ImageFilter.GaussianBlur(1.4)))
    _P["far"] = (fimg, (-120, 330), 1)
    fli = fl.img.filter(ImageFilter.GaussianBlur(1.0))
    halo = fl.img.filter(ImageFilter.GaussianBlur(7))
    halo.putalpha(halo.getchannel("A").point(lambda v: min(255, v * 3)))
    halo.alpha_composite(fli)
    _P["far_lit"] = (halo, (-120, 330), 1)
    # the door's light, slanting down into the town from the upper left
    sh = np.zeros((560, 900), np.float32)
    yy, xx = np.mgrid[0:560, 0:900].astype(np.float32)
    for x0, wd, gain in ((150, 70, 1.0), (262, 26, 0.8), (60, 34, 0.45)):
        sh += gain * np.exp(-(((xx - x0 - yy * 0.62) / (wd + yy * 0.10)) ** 2))
    sh *= np.clip(1 - yy / 520, 0, 1) ** 1.4 * (0.75 + 0.5 * w.vnoise((560, 900), 26, 220, seed=9))
    sa = np.zeros((560, 900, 4), np.float32)
    sa[..., :3] = np.array((255, 196, 110), np.float32)
    sa[..., 3] = np.clip(sh, 0, 1) * 84
    _P["shaft"] = (Image.fromarray(sa.astype(np.uint8), "RGBA"), (-40, 400), 1)
    _build_mid()
    _build_street(bed)
    return _P


def _window(c, cl, x0, y0, x1, y1, arch=False, cross=True):
    """An unlit window on sheet c and its lit pane on sheet cl."""
    c.rect(x0, y0, x1, y1, (26, 46, 54), LINE, 1.2, wob=0.3)
    cl.rect(x0 + 0.8, y0 + 0.8, x1 - 0.8, y1 - 0.8, (255, 206, 120), None, wob=0.2)
    cl.rect(x0 + 0.8, y0 + 0.8, x1 - 0.8, lerp(y0, y1, 0.4), (255, 232, 170), None, wob=0.2)
    if cross:
        for cc in (c, cl):
            cc.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], LINE if cc is c else (120, 70, 30), 0.9, wob=0.1)
            cc.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], LINE if cc is c else (120, 70, 30), 0.9, wob=0.1)


def _build_mid():
    """The back row: houses made of bigger sunk things, hazed."""
    X0, Y0, X1, Y1 = -200, 520, 1160, 830
    c = _Cut(X0, Y0, X1, Y1, k=2, seed=21)
    cl = _Cut(X0, Y0, X1, Y1, k=2, seed=22)
    base = 800
    # a stack of tins, far left
    for q, (x, wd, ht, col) in enumerate(((-150, 70, 60, (150, 150, 140)), (-140, 54, 50, (170, 120, 90)), (-132, 40, 40, (140, 160, 150)))):
        y1 = base - sum(h for _, _, h, _ in ((-150, 70, 60, 0), (-140, 54, 50, 0), (-132, 40, 40, 0))[:q])
        c.rect(x, y1 - ht, x + wd, y1, col, LINE, 1.2)
        for r in range(1, 4):
            c.line([(x, y1 - ht * r / 4), (x + wd, y1 - ht * r / 4)], mix_color(col, LINE, 0.4), 0.8)
        _window(c, cl, x + wd / 2 - 6, y1 - ht * 0.7, x + wd / 2 + 6, y1 - ht * 0.3, cross=False)
    # an old boot, toe to the right, with a door in the heel and a stove pipe
    bx = 96
    boot = [(bx, base), (bx, base - 150), (bx + 8, base - 160), (bx + 70, base - 160), (bx + 78, base - 150), (bx + 80, base - 70),
            (bx + 120, base - 58), (bx + 158, base - 40), (bx + 166, base - 16), (bx + 160, base)]
    c.poly(boot, (120, 86, 60), LINE, 1.5)
    c.poly([(bx - 4, base), (bx - 4, base - 10), (bx + 168, base - 10), (bx + 166, base)], (70, 52, 40), LINE, 1.2)
    for q in range(5):
        c.dot(bx + 62, base - 140 + q * 15, 2.2, (40, 30, 24))
        c.line([(bx + 50, base - 140 + q * 15), (bx + 72, base - 136 + q * 15)], (200, 180, 140), 0.9)
    _window(c, cl, bx + 14, base - 132, bx + 40, base - 104)
    _window(c, cl, bx + 14, base - 86, bx + 40, base - 58)
    _window(c, cl, bx + 100, base - 44, bx + 122, base - 22)
    c.rect(bx + 50, base - 44, bx + 70, base - 10, (60, 44, 34), LINE, 1.2)
    c.rect(bx + 22, base - 178, bx + 34, base - 158, (90, 100, 100), LINE, 1.1)
    # a bottle standing: a tower with a cork roof
    tx = 300
    c.poly([(tx, base), (tx, base - 130), (tx + 12, base - 152), (tx + 12, base - 196), (tx + 34, base - 196), (tx + 34, base - 152),
            (tx + 46, base - 130), (tx + 46, base)], (96, 150, 128), LINE, 1.4)
    c.rect(tx + 9, base - 214, tx + 37, base - 196, (176, 140, 96), LINE, 1.2)
    c.line([(tx + 8, base - 120), (tx + 8, base - 20)], (190, 226, 208), 1.4)
    for q in range(4):
        _window(c, cl, tx + 15, base - 122 + q * 30, tx + 31, base - 104 + q * 30, cross=False)
    # a teapot: round house, the spout a chimney
    px, py = 536, base - 46
    c.line([(px + 46, py - 8), (px + 76, py - 30), (px + 84, py - 54)], (178, 92, 78), 9)
    c.line([(px + 46, py - 8), (px + 76, py - 30), (px + 84, py - 54)], LINE, 1.0)
    c.ell(px, py, 54, 46, (188, 98, 84), LINE, 1.5)
    c.ell(px - 62, py - 2, 16, 22, None, LINE, 4.0, a0=70, a1=290)
    c.ell(px, py - 46, 24, 8, (160, 80, 70), LINE, 1.2)
    c.dot(px, py - 56, 5, (120, 60, 54))
    for q in (-1, 1):
        _window(c, cl, px + q * 26 - 9, py - 16, px + q * 26 + 9, py + 6)
    c.poly([(px - 9, base), (px - 9, py + 16), (px, py + 8), (px + 9, py + 16), (px + 9, base)], (90, 50, 44), LINE, 1.1)
    # behind the school, right: a tall lantern jar and a tin can on its side
    jx = 968
    c.poly([(jx, base), (jx, base - 120), (jx + 10, base - 136), (jx + 50, base - 136), (jx + 60, base - 120), (jx + 60, base)], (130, 170, 160), LINE, 1.4)
    c.rect(jx + 6, base - 150, jx + 54, base - 136, (150, 150, 140), LINE, 1.2)
    for q in range(3):
        _window(c, cl, jx + 12, base - 112 + q * 36, jx + 28, base - 90 + q * 36)
        _window(c, cl, jx + 34, base - 112 + q * 36, jx + 50, base - 90 + q * 36)
    c.rect(1050, base - 56, 1150, base, (156, 150, 130), LINE, 1.3)
    _window(c, cl, 1066, base - 40, 1086, base - 16)
    # the tall weed between the houses (flat cut shapes on this plane; the swaying weed is nearer)
    rs = random.Random(3)
    for x in (20, 60, 240, 382, 560, 600, 880, 930):
        for q in range(3):
            ln, lean = rs.uniform(70, 150), rs.uniform(-18, 18)
            bx0 = x + q * 9
            c.poly([(bx0 - 4, base), (bx0 + lean * 0.5 - 3, base - ln * 0.6), (bx0 + lean, base - ln), (bx0 + lean * 0.5 + 4, base - ln * 0.55), (bx0 + 5, base)],
                   mix_color((46, 96, 64), (28, 60, 50), rs.random()), None)
    c.rect(X0, base - 3, X1, Y1, (58, 76, 66), None)
    img = _paperize(c.img, seed=31, grain=0.14, haze=0.34)
    _P["mid"] = (img.filter(ImageFilter.GaussianBlur(0.7)), (X0, Y0), 2)
    lit = cl.img
    halo = lit.filter(ImageFilter.GaussianBlur(9))
    halo.putalpha(halo.getchannel("A").point(lambda v: int(v * 0.55)))
    halo.alpha_composite(lit)
    halo.putalpha(halo.getchannel("A").point(lambda v: int(v * 0.8)))
    _P["mid_lit"] = (halo, (X0, Y0), 2)


SX0, SY0, SX1, SY1 = -140, 580, 1100, 980
SK = 3                     # pixels per world unit of the street plane (close shots go to 3.6x)


def _lamp_post(c, cl, x, hy):
    """A bent reed with a little jar hung from it. Head (the jar) centred at (x + 12, hy)."""
    post = w.catmull([(x, BED_Y + 4), (x - 1, BED_Y - 40), (x + 1, hy - 4), (x + 5, hy - 13), (x + 11, hy - 15), (x + 12, hy - 8)], 6)
    c.line(post, (16, 34, 32), 3.4, wob=0.2)
    c.line(post, (70, 110, 86), 1.2, wob=0.2)
    c.ell(x, BED_Y + 4, 7, 3.2, (84, 96, 88), LINE, 1.0)
    for q in (0.3, 0.62):
        py = lerp(BED_Y, hy, q)
        c.line([(x - 2.4, py), (x + 2.4, py)], (16, 34, 32), 1.4, wob=0)
    jx = x + 12
    c.rect(jx - 4.5, hy - 8, jx + 4.5, hy - 5, (120, 126, 118), LINE, 0.9, wob=0.2)
    c.poly([(jx - 6, hy - 5), (jx + 6, hy - 5), (jx + 7, hy + 7), (jx, hy + 10), (jx - 7, hy + 7)], (90, 132, 128), LINE, 1.0, wob=0.3)
    cl.poly([(jx - 6, hy - 5), (jx + 6, hy - 5), (jx + 7, hy + 7), (jx, hy + 10), (jx - 7, hy + 7)], (255, 214, 130), (120, 80, 30), 0.9, wob=0.3)
    cl.dot(jx, hy + 2, 3.6, (255, 250, 220))


def _build_street(bed):
    c = _Cut(SX0, SY0, SX1, SY1, k=SK, seed=41)
    cl = {}         # light name -> lit sheet

    def L(name):
        if name not in cl:
            cl[name] = _Cut(SX0, SY0, SX1, SY1, k=SK, seed=50 + len(cl))
        return cl[name]

    # ---- the gravel: the river's own bed, laid twice (far lip and near floor)
    b2 = bed.resize((bed.width * SK, bed.height * SK), Image.BICUBIC)
    c.rect(SX0, BED_Y + 20, SX1, SY1, (70, 88, 76), None, wob=0)
    c.img.alpha_composite(b2, (int((-120 - SX0) * SK), int((752 - SY0) * SK)))
    near = bed.transpose(Image.FLIP_LEFT_RIGHT).resize((int(bed.width * 1.45 * SK), int(bed.height * 1.45 * SK)), Image.BICUBIC)
    c.img.alpha_composite(near, (int((-200 - SX0) * SK), int((806 - SY0) * SK)))
    c.d = ImageDraw.Draw(c.img, "RGBA")
    # main street: a ribbon of smaller, paler, trodden gravel along the buildings' feet
    rs = random.Random(8)
    for q in range(520):
        x, y = rs.uniform(SX0, SX1), BED_Y + 3 + rs.uniform(0, 1) ** 1.6 * 22
        r = rs.uniform(1.2, 3.2)
        col = mix_color((120, 134, 118), (176, 180, 158), rs.random())
        c.d.ellipse([c.P((x - r, y - r * 0.6)), c.P((x + r, y + r * 0.6))], fill=_rgba(col), outline=(40, 56, 52, 200))

    # ---- the welcome sign: a driftwood plank on a stick, a painted fish jumping, a shell. No lettering.
    sx, sy = SIGN_XY
    c.line([(sx + 2, BED_Y + 5), (sx + 1, sy + 14)], (72, 54, 40), 4.5)
    c.line([(sx + 2, BED_Y + 5), (sx + 1, sy + 14)], (150, 124, 92), 1.4)
    plank = [(sx - 34, sy - 15), (sx + 36, sy - 19), (sx + 38, sy + 15), (sx - 33, sy + 18)]
    c.poly(plank, (206, 182, 140), LINE, 1.5)
    for q in (-6, 6):
        c.line([(sx - 30, sy + q), (sx + 34, sy + q - 2)], (160, 134, 98), 0.7)
    fishp = w.catmull([(sx - 20, sy + 4), (sx - 8, sy - 9), (sx + 8, sy - 10), (sx + 18, sy - 2), (sx + 8, sy + 4), (sx - 8, sy + 3), (sx - 20, sy + 4)], 5)
    c.poly(fishp, (58, 128, 150), (24, 60, 80), 0.9, wob=0.2)
    c.poly([(sx - 19, sy + 3), (sx - 28, sy - 4), (sx - 27, sy + 10)], (58, 128, 150), (24, 60, 80), 0.9, wob=0.2)
    c.dot(sx + 11, sy - 4, 1.5, (250, 246, 230))
    c.line(w.catmull([(sx - 28, sy + 12), (sx - 16, sy + 9), (sx - 4, sy + 12), (sx + 8, sy + 9), (sx + 20, sy + 12), (sx + 32, sy + 9)], 4), (232, 240, 228), 1.3, wob=0.1)
    for q in range(7):                           # scallop shell on top
        a = math.radians(200 + q * 23.3)
        c.line([(sx, sy - 16), (sx + 15 * math.cos(a), sy - 16 + 13 * math.sin(a))], (236, 214, 196), 2.2, wob=0.1)
    c.ell(sx, sy - 16, 15, 13, None, (120, 90, 80), 1.0, a0=196, a1=344)
    for q, colr in enumerate(((206, 70, 60), (240, 200, 90), (70, 130, 190), (236, 236, 220), (206, 70, 60))):   # bunting to the diner
        f = (q + 0.5) / 5
        fx, fy = lerp(sx + 36, 86, f), lerp(sy - 17, 722, f) + 9 * math.sin(math.pi * f)
        c.poly([(fx - 4, fy), (fx + 4, fy), (fx, fy + 9)], colr, LINE, 0.7, wob=0.2)
    c.line([(lerp(sx + 36, 86, f / 10), lerp(sy - 17, 722, f / 10) + 9 * math.sin(math.pi * f / 10)) for f in range(11)], LINE, 0.8, wob=0.1)

    # ---- the diner: a sunk lunch tin. Red enamel box, cream domed lid, a wire handle, a spoon and fork for a sign.
    dx0, dy0, dx1, dy1 = DINER
    lid = [(dx0 - 4, 744)] + [(lerp(dx0 - 4, dx1 + 4, q / 16), 744 - 30 * math.sin(math.pi * q / 16) ** 0.7) for q in range(1, 16)] + [(dx1 + 4, 744)]
    c.ell((dx0 + dx1) / 2, 716, 30, 17, None, (60, 66, 66), 2.4, a0=180, a1=360)       # handle
    c.poly(lid, (228, 216, 184), LINE, 1.5)
    c.line([(dx0 + 10, 738), (dx1 - 10, 738)], (176, 160, 130), 1.0)
    c.rect(dx0, 744, dx1, dy1, (184, 66, 54), LINE, 1.5)
    c.rect(dx0, 786, dx1, 793, (232, 220, 190), LINE, 0.8)
    c.line([(dx0 + 3, 748), (dx0 + 3, 798)], (232, 130, 110), 1.2)
    for q in range(12):                         # scalloped awning, striped
        ax = dx0 + 4 + q * 15
        c.poly([(ax, 744), (ax + 15, 744), (ax + 15, 750), (ax + 7.5, 755), (ax, 750)], (236, 226, 200) if q % 2 else (150, 46, 40), LINE, 0.7, wob=0.2)
    for q in range(5):
        wx = dx0 + 12 + q * 30
        _window(c, L("diner"), wx, 759, wx + 23, 781, cross=False)
        if q in (1, 3):                         # somebody at the counter
            L("diner").poly([(wx + 7, 781), (wx + 8, 768), (wx + 12, 764), (wx + 16, 768), (wx + 17, 781)], (110, 66, 30), None, wob=0.2)
    c.rect(dx1 - 26, 760, dx1 - 8, dy1, (110, 44, 40), LINE, 1.2)
    _window(c, L("diner"), dx1 - 23, 764, dx1 - 11, 776, cross=False)
    c.rect(dx1 - 30, dy1 - 1, dx1 - 4, dy1 + 4, (140, 150, 140), LINE, 0.9)
    for q, (bx, by) in enumerate(((dx0 + 20, 757), (dx0 + 66, 757), (dx0 + 112, 757), (dx0 + 158, 757))):   # a string of bulbs
        L("diner").dot(bx, by, 2.2, (255, 240, 190))
    # the sign: a real spoon and fork standing on the lid
    sxn = dx0 + 38
    c.line([(sxn, 728), (sxn - 5, 694)], (176, 182, 178), 2.6)
    c.ell(sxn - 7, 684, 6.5, 10, (190, 196, 192), LINE, 1.0)
    c.line([(sxn + 15, 726), (sxn + 19, 690)], (176, 182, 178), 2.6)
    for q in (-3.6, 0, 3.6):
        c.line([(sxn + 19 + q, 692), (sxn + 20 + q, 676)], (176, 182, 178), 1.5, wob=0.1)
    # thimble chimney
    c.poly([(dx1 - 54, 726), (dx1 - 51, 704), (dx1 - 37, 704), (dx1 - 34, 729)], (150, 156, 148), LINE, 1.2)
    for q in range(9):
        c.dot(dx1 - 50 + (q % 3) * 6, 710 + (q // 3) * 6, 0.9, (90, 96, 92))

    # ---- the school: a fruit crate with an upturned toy boat for a roof and a belfry of matches
    x0, _, x1, _ = SCHOOL
    bx0, bx1 = x0 + 12, x1 - 12
    c.rect(bx0, 694, bx1, BED_Y + 3, (190, 152, 100), LINE, 1.6)
    for q in range(1, 6):
        c.line([(bx0, 694 + q * 18), (bx1, 694 + q * 18)], (132, 100, 64), 0.9)
    for xq in (bx0 + 5, bx1 - 5, 806):
        c.rect(xq - 4, 694, xq + 4, BED_Y + 3, (206, 170, 118), LINE, 1.0)
    for q in range(8):
        c.dot(bx0 + 5 + (q % 2) * (bx1 - bx0 - 10), 704 + (q // 2) * 28, 1.2, (60, 50, 40))
    # hull roof: bow to the left, keel up
    hull = w.catmull([(x0 - 6, 696), (x0 + 6, 676), (x0 + 60, 654), (x0 + 150, 641), (x1 - 60, 646), (x1 - 8, 664), (x1 + 4, 696)], 6)
    c.poly(hull + [(x1 + 4, 700), (x0 - 6, 700)], (156, 70, 52), LINE, 1.6, wob=0.3)
    c.poly([(x0 - 6, 692), (x1 + 4, 692), (x1 + 4, 701), (x0 - 6, 701)], (232, 226, 204), LINE, 1.0)
    for q in range(1, 4):
        c.line(w.catmull([(x0 + 2 + q * 4, 690 - q * 9), (x0 + 70, 664 - q * 4 + 6), (x0 + 150, 652 - q * 3 + 8), (x1 - 50, 656 - q * 3 + 8), (x1 - 4 - q * 3, 690 - q * 8)], 5),
               (110, 46, 36), 0.8, wob=0.2)
    c.line([(x0 + 40, 648), (x1 - 46, 641)], (96, 40, 32), 2.6)                       # keel
    # belfry: two matches, a beam, a bottle cap
    hx, hy = BELL_HANG
    for q in (-13, 13):
        c.line([(hx + q, 646), (hx + q, 610)], (214, 190, 140), 3.0, wob=0.15)
        c.line([(hx + q, 646), (hx + q, 610)], LINE, 0.7, wob=0.15)
    c.line([(hx - 16, 610), (hx + 16, 610)], (214, 190, 140), 3.0, wob=0.15)
    cap = [(hx - 19, 608)] + [(hx - 19 + q * 3.8, 608 + (1.6 if q % 2 else 0)) for q in range(1, 10)] + [(hx + 19, 608), (hx + 14, 600), (hx - 14, 600)]
    c.poly(cap, (110, 140, 150), LINE, 1.1, wob=0.15)
    c.line([(hx - 12, 603), (hx + 12, 603)], (190, 214, 216), 0.9)
    # a pennant on the stern
    c.line([(x1 - 22, 662), (x1 - 22, 628)], (214, 190, 140), 1.8)
    c.poly([(x1 - 22, 628), (x1 - 2, 634), (x1 - 22, 641)], (236, 196, 80), LINE, 0.8, wob=0.2)
    # windows and door
    for q, wx in enumerate((630, 690, 750)):
        c.rect(wx - 4, 712, wx + 38, 770, (224, 222, 204), LINE, 1.0)
        _window(c, L("school"), wx, 716, wx + 34, 766)
        c.rect(wx - 6, 770, wx + 40, 774, (224, 222, 204), LINE, 0.9)
    L("school").poly(w.catmull([(699, 766), (700, 752), (706, 744), (713, 748), (716, 758), (714, 766)], 4), (110, 66, 30), None, wob=0.1)   # one small fish at a window
    L("school").dot(709, 751, 1.3, (255, 240, 200))
    door = [(822, BED_Y + 3), (822, 748)] + [(843 + 21 * math.cos(math.radians(a)), 748 + 18 * math.sin(math.radians(a))) for a in range(180, 361, 20)] + [(864, BED_Y + 3)]
    c.poly(door, (70, 116, 150), LINE, 1.4)
    c.line([(843, 734), (843, BED_Y + 2)], (40, 70, 96), 0.9)
    c.dot(838, 772, 1.6, (220, 220, 200))
    _window(c, L("school"), 832, 742, 854, 754, cross=False)
    c.rect(816, BED_Y + 1, 870, BED_Y + 6, (150, 156, 146), LINE, 0.9)
    # the yard fence: burnt matches, with a gate gap
    fx = YARD[0]
    while fx <= 600:
        if not (546 < fx < 574):
            c.line([(fx, BED_Y + 7), (fx, BED_Y - 12)], (214, 190, 140), 2.2, wob=0.15)
            c.dot(fx, BED_Y - 13, 1.9, (40, 30, 28))
        fx += 7
    for seg in ((YARD[0], 546), (574, 602)):
        c.line([(seg[0], BED_Y - 5), (seg[1], BED_Y - 5)], (190, 166, 120), 1.2, wob=0.1)
    for fx in (903, 910, 917):
        c.line([(fx, BED_Y + 7), (fx, BED_Y - 12)], (214, 190, 140), 2.2, wob=0.15)
        c.dot(fx, BED_Y - 13, 1.9, (40, 30, 28))

    # ---- the lamps
    for q, (lx, ly) in enumerate(LAMPS):
        _lamp_post(c, L(f"lamp{q}"), lx - 12, ly)

    # pebbles tucked against the feet of things so they sit in the gravel
    for q in range(160):
        x = rs.choice([rs.uniform(dx0 - 6, dx1 + 6), rs.uniform(x0 + 6, x1 - 6), rs.uniform(-10, 60)])
        y = BED_Y + rs.uniform(0, 6)
        r = rs.uniform(1.6, 4.0)
        col = mix_color((92, 108, 96), (160, 168, 150), rs.random())
        c.d.ellipse([c.P((x - r, y - r * 0.6)), c.P((x + r, y + r * 0.6))], fill=_rgba(col), outline=(30, 46, 44, 220))

    base = _paperize(c.img, seed=47, grain=0.12)
    _P["street"] = (base, (SX0, SY0), SK)
    lights = []
    order = {"lamp0": 64, "diner": 164, "lamp1": 275, "lamp2": 355, "lamp3": 490, "lamp4": 565, "school": 750, "lamp5": 930}
    for name, sheet in cl.items():
        lit = sheet.img
        # the light that falls on the gravel and the wall near each light
        pool = Image.new("L", lit.size, 0)
        pd = ImageDraw.Draw(pool)
        if name.startswith("lamp"):
            lx, ly = LAMPS[int(name[4:])]
            px, py = sheet.P((lx, BED_Y + 12))
            pd.ellipse([px - 55 * SK, py - 13 * SK, px + 55 * SK, py + 17 * SK], fill=110)
        elif name == "diner":
            px0, py0 = sheet.P((dx0 - 10, BED_Y + 2))
            px1, py1 = sheet.P((dx1 + 20, BED_Y + 26))
            pd.ellipse([px0, py0, px1, py1 + 10 * SK], fill=90)
        else:
            px0, py0 = sheet.P((610, BED_Y + 4))
            px1, py1 = sheet.P((890, BED_Y + 34))
            pd.ellipse([px0, py0, px1, py1 + 10 * SK], fill=80)
        pool = pool.filter(ImageFilter.GaussianBlur(11 * SK))
        street_a = np.asarray(base.getchannel("A"), np.float32) / 255
        pa = np.asarray(pool, np.float32) * street_a
        pl = np.zeros(pa.shape + (4,), np.float32)
        pl[..., :3] = np.array((255, 190, 110), np.float32)
        pl[..., 3] = pa
        out = Image.fromarray(pl.astype(np.uint8), "RGBA")
        halo = lit.filter(ImageFilter.GaussianBlur(2.5 * SK))
        halo.putalpha(halo.getchannel("A").point(lambda v: int(v * 0.6)))
        out.alpha_composite(halo)
        out.alpha_composite(lit)
        bb = out.getbbox()
        if bb:
            lights.append((name, order.get(name, 500), out.crop(bb), (bb[0], bb[1])))
    lights.sort(key=lambda r: r[1])
    _P["street_lights"] = lights


LIGHT_NAMES = ("lamp0", "diner", "lamp1", "lamp2", "lamp3", "lamp4", "school", "lamp5")


def light_levels(lamps=1.0, school=None):
    """lamps: 0..1 = the town's lights coming on from left to right (lamp, diner, lamp, lamp, lamp, lamp, last lamp),
    or a dict {name: 0..1} over LIGHT_NAMES, or a list of six lamp levels. school: the school windows (default: follow
    `lamps`, last). Returns {name: 0..1}."""
    if isinstance(lamps, dict):
        lv = {n: clamp(float(lamps.get(n, 0.0))) for n in LIGHT_NAMES}
    elif isinstance(lamps, (list, tuple)):
        lv = {f"lamp{q}": clamp(float(v)) for q, v in enumerate(lamps)}
        lv["diner"] = lv.get("lamp0", 0.0)
        lv["school"] = 0.0
    else:
        seq = ("lamp0", "diner", "lamp1", "lamp2", "lamp3", "lamp4", "lamp5")
        lv = {n: smooth(clamp(float(lamps) * (len(seq) + 1.5) - q, 0, 1)) for q, n in enumerate(seq)}
        lv["school"] = smooth(clamp(float(lamps) * 4 - 3))
    if school is not None:
        lv["school"] = clamp(float(school))
    for n in LIGHT_NAMES:
        lv.setdefault(n, 0.0)
    return lv


@lru_cache(maxsize=6)
def _street_lit(key):
    P = _planes()
    img = P["street"][0].copy()
    for (name, _, spr, off), q in zip(P["street_lights"], key):
        if q > 0:
            m = spr.getchannel("A")
            if q < 12:
                m = m.point(lambda v, q=q: int(v * q / 12))
            img.paste(spr, off, m)
    return img


# --------------------------------------------------- the surface from below ---

def _wave(wx, t, calm=False):
    tt = 0.0 if calm else t
    return 2.2 * np.sin(wx * 0.021 + tt * 1.7) + 1.3 * np.sin(wx * 0.057 - tt * 2.3) + 0.7 * np.sin(wx * 0.13 + tt * 3.1)


def surface(ink, t, cam=None, sky=True, door=1.0, ice=0.0, cracks=(), shatter=0.0, calm=False, night=0.0, glow=1.0):
    """The surface seen from below: a bright wobbling line across the whole frame, and (sky=True) above it the dusk
    and the lit door, bent and wobbling as things are when you look up through water. Pass sky=False where a porch is
    drawn above the line (F-SPLIT, the cranes). door 0..1 = how warm the amber smear is. ice 0..1 runs a white skin
    along the line from left to right; cracks = [(world_x, 0..1)] jagged cracks growing out from a stamp; shatter 0..1
    breaks the skin into floes that tip and clear. calm=True stops the wobble dead (under the ice). night 0..1."""
    cam = as_cam(cam)
    ys = cam.surface()
    z = cam.zoom
    if ys < -40 or ys > H + 40:
        return ys
    xs = np.arange(W, dtype=np.float32)
    wxs = (xs - W / 2) / z + cam.centre()[0]
    tt = 0.0 if calm else t
    if sky and ys > 0:
        h = int(min(H, math.ceil(ys + 6)))
        yy = np.arange(h, dtype=np.float32)[:, None]
        d = np.clip(ys - yy, 0, None) / z                          # world px above the line
        wob = (9 * np.sin(d * 0.33 + tt * 2.1 + wxs[None, :] * 0.013) + 5 * np.sin(d * 0.8 - tt * 1.4 + wxs[None, :] * 0.031)) * (0.35 + d / 16)
        u = wxs[None, :] + wob
        f = np.exp(-d / 34)
        far_c = np.array(mix_color((50, 40, 92), (22, 18, 50), night), np.float32)
        near_c = np.array(mix_color((126, 108, 168), (70, 62, 120), night), np.float32)
        col = far_c[None, None, :] * (1 - f[..., None]) + near_c[None, None, :] * f[..., None]
        col = col * np.ones((1, W, 1), np.float32)
        bands = 0.5 + 0.5 * np.sin(d * 0.9 + 2.2 * np.sin(wxs[None, :] * 0.02 + tt) + tt * 1.2)
        col *= (0.86 + 0.26 * bands)[..., None]
        dc = (DOOR_X[0] + DOOR_X[1]) / 2
        g_door = np.exp(-(((u - dc) / 74) ** 2)) * (0.55 + 0.45 * bands)
        g_lamp = np.exp(-(((u - LAMP_ABOVE_X) / 20) ** 2))
        warm = (0.80 * g_door + 0.75 * g_lamp) * door * (0.45 + 0.55 * f)
        col = col * (1 - np.clip(warm, 0, 1)[..., None] * 0.8) + np.array(AMBER, np.float32) * np.clip(warm, 0, 1.3)[..., None]
        col[..., 0] += 40 * g_lamp * door
        ink.img.paste(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB"), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    # the light under the line
    wav = _wave(wxs, t, calm) * z
    line = [(float(x), float(ys + wav[int(x)])) for x in range(0, W, 6)] + [(W, float(ys + wav[-1]))]
    lay, ld = _layer((W, H))
    under = int(46 * z)
    for q in range(under):
        a = int(70 * glow * (1 - q / under) ** 2.2 * (1 - 0.5 * night))
        if a > 0:
            ld.line([(0, ys + 2 + q), (W, ys + 2 + q)], fill=(190, 226, 214, a), width=1)
    # the amber of the door lies along the underside too
    if door > 0.02:
        dx = cam.xy((DOOR_X[0] + DOOR_X[1]) / 2, SURFACE_Y)[0]
        lx = cam.xy(LAMP_ABOVE_X, SURFACE_Y)[0]
        for q in range(int(30 * z)):
            a = (1 - q / (30 * z)) ** 2 * door
            sh = 5 * math.sin(tt * 1.6 + q * 0.3)
            ld.line([(dx - 96 * z + sh, ys + 2 + q), (dx + 110 * z + sh, ys + 2 + q)], fill=AMBER + (int(54 * a),), width=1)
            ld.line([(lx - 20 * z + sh, ys + 2 + q), (lx + 20 * z + sh, ys + 2 + q)], fill=(255, 214, 140, int(90 * a)), width=1)
    ld.line(line, fill=(190, 232, 220, 70), width=max(3, int(9 * z)))
    ld.line(line, fill=(236, 250, 238, 235), width=max(2, int(round(3 * z))))
    rs = random.Random(4)
    for q in range(26):                                             # glints that ride the line
        gx = (rs.uniform(-200, 1160) + (0 if calm else t) * rs.uniform(6, 16)) % 1360 - 200
        sx, _ = cam.xy(gx, SURFACE_Y)
        if 0 <= sx < W:
            ln = rs.uniform(6, 22) * z
            yv = ys + wav[int(sx)]
            ld.line([(sx - ln / 2, yv), (sx + ln / 2, yv)], fill=(255, 255, 250, 255), width=max(2, int(round(4 * z))))
    ink.img.paste(lay, (0, 0), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if ice > 0.001 and shatter < 0.999:
        _ice(ink, t, cam, ys, ice, cracks, shatter, sky)
    return ys


def _ice(ink, t, cam, ys, ice, cracks, shatter, sky):
    z = cam.zoom
    edge_w = lerp(-260, 1260, ice)
    rs = random.Random(91)
    lay, ld = _layer((W, H))
    # floes: the skin in pieces between fixed joints, so that it can break where it was always going to break
    joints = [-260]
    while joints[-1] < 1260:
        joints.append(joints[-1] + rs.uniform(34, 92))
    th = 10 * z
    for a, b in zip(joints, joints[1:]):
        if a >= edge_w:
            break
        b = min(b, edge_w)
        k = rs.random()
        sa, sb = cam.xy(a, SURFACE_Y)[0], cam.xy(b, SURFACE_Y)[0]
        if sb < -40 or sa > W + 40:
            rs.random(), rs.random(), rs.random()
            continue
        tip = (rs.uniform(-1, 1) * 16 * shatter)
        drop = shatter ** 1.5 * rs.uniform(4, 30) * z
        gap = shatter * 5 * z
        al = int(238 * (1 - shatter) ** 0.8)
        y0, y1 = ys - 3 * z + drop - tip, ys - 3 * z + drop + tip
        lower = [(lerp(sa + gap, sb - gap, f), lerp(y0, y1, f) + th * (0.75 + 0.5 * math.sin(k * 9 + f * 5)) ) for f in (0, 0.25, 0.5, 0.75, 1)]
        poly = [(sa + gap, y0), (sb - gap, y1)] + lower[::-1]
        ld.polygon(poly, fill=(214, 230, 238, al))
        ld.line([(sa + gap, y0), (sb - gap, y1)], fill=(250, 254, 255, al), width=max(2, int(2.5 * z)))
        ld.line(lower, fill=(128, 172, 190, al), width=max(1, int(1.5 * z)))
        ld.line([(lerp(sa, sb, 0.2), lerp(y0, y1, 0.2) + th * 0.3), (lerp(sa, sb, 0.6), lerp(y0, y1, 0.6) + th * 0.42)], fill=(255, 255, 255, int(al * 0.7)), width=1)
    if sky and ys > 0 and shatter < 1:                            # the skin dulls what is above it
        se = cam.xy(edge_w, SURFACE_Y)[0]
        if se > 0:
            ld.rectangle([0, 0, min(W, se), ys - 3 * z], fill=(196, 208, 222, int(120 * (1 - shatter))))
    for wx, f in cracks:
        if f <= 0:
            continue
        cx = cam.xy(wx, SURFACE_Y)[0]
        cr = random.Random(int(wx) * 13 + 5)
        al = int(255 * (1 - shatter) ** 0.5)
        for sgn in (-1, 1):
            x, y = cx, ys + 1 * z
            pts = [(x, y)]
            reach = f * 520 * z
            while abs(x - cx) < reach:
                x += sgn * cr.uniform(10, 26) * z
                y = ys + cr.uniform(-1, 7) * z
                pts.append((x, y))
                if cr.random() < 0.4:
                    ld.line([(x, y), (x + sgn * cr.uniform(2, 8) * z, ys + th * cr.uniform(0.6, 1.3))], fill=(40, 84, 110, al), width=max(1, int(1.4 * z)))
            ld.line(pts, fill=(40, 84, 110, al), width=max(2, int(2 * z)))
            ld.line([(px, py - 1.5 * z) for px, py in pts], fill=(255, 255, 255, al), width=max(1, int(z)))
        for q in range(9):                                        # the star where the hoof came down
            a = math.radians(200 + q * 17.5 + cr.uniform(-6, 6))
            ln = (8 + 16 * clamp(f * 4)) * z * cr.uniform(0.6, 1.2)
            ld.line([(cx, ys), (cx + ln * math.cos(a) * 1.6, ys - ln * math.sin(a) * 0.5 + 2 * z)], fill=(255, 255, 255, al), width=max(1, int(1.6 * z)))
    ink.img.paste(lay, (0, 0), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def touch(ink, t, cam, x, kind="muzzle", dip=1.0, calm=False, color=(44, 30, 38)):
    """What a land animal looks like from below: only the part that breaks the line. kind 'muzzle' (a cow's nose and
    lips, with rings), 'hoof' (one leg to the fetlock), 'chin'. x is world x; dip 0..1 how far in. Draw after
    surface()."""
    cam = as_cam(cam)
    z = cam.zoom
    sx, ys = cam.xy(x, SURFACE_Y)
    tt = 0.0 if calm else t
    ys += float(_wave(np.array([x], np.float32), t, calm)[0]) * z
    wob = math.sin(tt * 2.3 + x) * 1.5 * z
    lay, ld = _layer((W, H))
    if kind == "hoof":
        dp = 26 * z * dip
        pts = [(sx - 7 * z + wob, ys - 4), (sx + 7 * z + wob, ys - 4), (sx + 8 * z - wob, ys + dp * 0.7), (sx + 10 * z - wob, ys + dp),
               (sx - 9 * z - wob, ys + dp), (sx - 7 * z - wob, ys + dp * 0.7)]
        ld.polygon(pts, fill=color + (240,))
        ld.line([(sx - 9 * z - wob, ys + dp * 0.72), (sx + 9 * z - wob, ys + dp * 0.72)], fill=(96, 84, 80, 255), width=max(1, int(1.5 * z)))
        ld.line([(sx - wob, ys + dp * 0.74), (sx - wob, ys + dp)], fill=(14, 10, 12, 255), width=max(1, int(1.2 * z)))
    else:
        dp = (16 if kind == "muzzle" else 9) * z * dip
        hw = (15 if kind == "muzzle" else 11) * z
        pts = [(sx - hw * 1.15 + wob, ys - 5)] + [(sx + hw * math.cos(math.radians(a)) - wob * 0.5, ys + dp * math.sin(math.radians(a))) for a in range(180, -1, -15)] + [(sx + hw * 1.15 + wob, ys - 5)]
        ld.polygon(pts, fill=color + (240,))
        if kind == "muzzle":
            ld.polygon([(sx + hw * math.cos(math.radians(a)) * 0.82 - wob * 0.5, ys + dp * (0.42 + 0.56 * math.sin(math.radians(a)))) for a in range(0, 181, 15)],
                       fill=(150, 126, 122, 235))
            for q in (-1, 1):
                ld.ellipse([sx + q * hw * 0.36 - 2.2 * z, ys + dp * 0.6 - 1.6 * z, sx + q * hw * 0.36 + 2.2 * z, ys + dp * 0.6 + 1.6 * z], fill=(24, 14, 18, 255))
    for q in range(3):                                           # rings leaving along the line
        ph = (tt * 0.7 + q / 3) % 1
        r = (16 + 60 * ph) * z
        a = int(200 * (1 - ph))
        for sgn in (-1, 1):
            ld.line([(sx + sgn * r, ys - 1), (sx + sgn * (r + 9 * z), ys - 1)], fill=(255, 255, 250, a), width=max(2, int(3 * z)))
    ink.img.paste(lay, (0, 0), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    return (sx, ys + dp)


# ----------------------------------------------------------- the set calls ---

def back(ink, t, cam=None, lamps=1.0, school=None, sky=True, door=1.0, ice=0.0, cracks=(), shatter=0.0, calm=False, night=0.0):
    """Everything behind main street: the water, the far town, the back row of houses, and the surface seen from
    below (with the lit door wobbling above it when sky=True). Call first."""
    cam = as_cam(cam)
    P = _planes()
    lv = light_levels(lamps, school)
    town_on = sum(lv[n] for n in LIGHT_NAMES) / len(LIGHT_NAMES)
    ys = cam.surface()
    top = max(0, ys - 4)
    if top < H:
        ink.d.rectangle([0, top, W, H], fill=(12, 44, 52, 255))
        _blit(ink, P["water"], cam, 0.3, clip_top=top)
        _blit(ink, P["far"], cam, 0.45, clip_top=top)
        _blit(ink, P["far_lit"], cam, 0.45, alpha=town_on * (0.75 + 0.2 * night), clip_top=top)
        ink.d.rectangle([0, top, W, H], fill=WATER + (34,))
        _blit(ink, P["mid"], cam, 0.72, clip_top=top)
        _blit(ink, P["mid_lit"], cam, 0.72, alpha=town_on, clip_top=top)
        ink.d.rectangle([0, top, W, H], fill=WATER + (26,))
        if door > 0.02 and ice < 0.5:
            sway = 0.0 if calm else 6 * math.sin(t * 0.7)
            img, (ox_, oy_), k_ = P["shaft"]
            _blit(ink, (img, (ox_ + sway, oy_), k_), cam, 1.0, alpha=door * (1 - 2 * ice) * (0.8 + 0.2 * math.sin(t * 1.9)), clip_top=top)
    surface(ink, t, cam, sky=sky, door=door, ice=ice, cracks=cracks, shatter=shatter, calm=calm, night=night)


def street(ink, t, cam=None, lamps=1.0, school=None, bell=0.0, board=True, taken=(), smudges=0, holes=0, pull=None,
           calm=False, smoke=True):
    """Main street: gravel, welcome sign, diner, lamps, the school and its bell, the yard fence, the notice board
    and the holes dug so far. Call after back() and before the cast. bell = the school bell's swing in degrees.
    taken / smudges / pull go to notice_board(); holes to dig_holes(). Returns {'lamps': [screen heads], 'board': ...}."""
    cam = as_cam(cam)
    P = _planes()
    lv = light_levels(lamps, school)
    key = tuple(int(round(lv[name] * 12)) for name, _, _, _ in P["street_lights"])
    top = max(0, cam.surface() + 2)
    _blit(ink, (_street_lit(key), (SX0, SY0), SK), cam, 1.0, clip_top=top)
    z = cam.zoom
    heads = []
    tt = 0.0 if calm else t
    for q, (lx, ly) in enumerate(LAMPS):
        sx, sy = cam.xy(lx, ly + 2)
        heads.append((sx, sy))
        a = lv[f"lamp{q}"]
        if a > 0.02 and -80 < sx < W + 80:
            fl = 0.9 + 0.1 * math.sin(tt * 5.3 + q * 2.1) * math.sin(tt * 1.7 + q)
            _put_glow(ink, sx, sy, 62 * z, 0.42 * a * fl, AMBER, 2.2)
            _put_glow(ink, sx, sy, 15 * z, 0.85 * a * fl, (255, 244, 206), 1.6)
    if smoke and not calm:                                       # the diner's chimney cooks in bubbles
        for q in range(5):
            ph = (t * 0.33 + q / 5) % 1
            bx, by = cam.xy(DINER[2] - 44 + 7 * math.sin(ph * 6 + q), 702 - ph * 70)
            r = (1.6 + 3.2 * ph) * z
            ink.d.ellipse([bx - r, by - r, bx + r, by + r], outline=(226, 244, 236, int(210 * (1 - ph))), width=max(1, int(1.3 * z)))
    school_bell(ink, cam, bell)
    if holes:
        dig_holes(ink, cam, holes)
    out = {"lamps": heads}
    if board:
        out["board"] = notice_board(ink, t, cam, taken=taken, smudges=smudges, pull=pull, calm=calm)
    return out


def front(ink, t, cam=None, calm=False, weeds=True, motes=True):
    """What is nearer than the cast: weed at the frame's lower corners and drifting specks at two depths. Call last
    (before grade()). calm=True stops both dead (under the ice)."""
    cam = as_cam(cam)
    tt = 0.0 if calm else t
    ys = cam.surface()
    if motes:
        rs = random.Random(77)
        for q in range(90):
            dp = 0.7 if q % 3 else 1.35
            x0, y0, sp, ph = rs.uniform(-200, 1160), rs.uniform(SURFACE_Y + 8, 960), rs.uniform(3, 12), rs.uniform(0, 6.28)
            wx = (x0 + sp * tt + 200) % 1360 - 200
            wy = y0 + 5 * math.sin(ph + tt * 0.7)
            sx, sy = cam.xy(wx, wy, dp)
            if sy < ys + 4 or not (0 <= sx < W and 0 <= sy < H):
                rs.random(), rs.random()
                continue
            r = rs.uniform(0.7, 1.9) * cam.s(dp)
            ink.d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(214, 236, 214, int(rs.uniform(40, 120))))
    if weeds:
        dp = 1.3
        zz = cam.s(dp)
        for q, (wx, wy, ht, n) in enumerate(((-36, 938, 170, 6), (26, 950, 120, 4), (1000, 944, 190, 6), (952, 956, 110, 4))):
            sx, sy = cam.xy(wx, wy, dp)
            if sy - ht * zz < H and -200 < sx < W + 200:
                w.weed(ink, sx, sy, height=ht * zz, lean=(8 if q < 2 else -10), t=tt * 0.8, seed=40 + q, n=n, spread=40 * zz,
                       sway=0 if calm else 1.0, dark=0.75)


def grade(ink, cam=None, cold=0.0, night=0.0):
    """A wash over everything under the surface, after the cast is drawn. cold 0..1: the warmth goes out of the water
    (the ice). night 0..1: later, darker and more violet, while anything lamp-warm stays bright."""
    if cold <= 0.001 and night <= 0.001:
        return
    cam = as_cam(cam)
    top = int(clamp(cam.surface() + 4, 0, H))
    if top >= H:
        return
    a = np.asarray(ink.img, np.float32)
    reg = a[top:]
    if cold > 0:
        lum = reg.mean(2, keepdims=True)
        tgt = lum * np.array((0.80, 0.92, 1.06), np.float32) + np.array((10, 14, 22), np.float32)
        reg = reg + (tgt - reg) * (0.72 * cold)
    if night > 0:
        warm = np.clip((reg[..., 0] - reg[..., 2]) / 90.0, 0, 1)[..., None]
        dark = reg * np.array((0.66, 0.66, 0.84), np.float32)
        reg = reg + (dark - reg) * night * (1 - warm)
    out = a.copy()
    out[top:] = reg
    ink.img.paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB"), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def draw(ink, t, cam=None, cast=True, **kw):
    """The whole town in one call (back, street, the class, front), for a quick look or an empty establishing shot.
    Keywords go to back(), street() and school_class() by name."""
    cam = as_cam(cam)
    bk = {k: kw[k] for k in ("lamps", "school", "sky", "door", "ice", "cracks", "shatter", "calm", "night") if k in kw}
    stt = {k: kw[k] for k in ("lamps", "school", "bell", "board", "taken", "smudges", "holes", "pull", "calm") if k in kw}
    cl = {k: kw[k] for k in ("facing", "look", "tilt", "speak", "arm", "skip", "calm") if k in kw}
    back(ink, t, cam, **bk)
    out = street(ink, t, cam, **stt)
    if cast:
        out["class"] = school_class(ink, t, cam, **cl)
        townsfolk(ink, t, cam, calm=kw.get("calm", False))
    front(ink, t, cam, calm=kw.get("calm", False))
    return out


# ------------------------------------------------------------ small things ---

def school_bell(ink, cam=None, swing=0.0):
    """The school bell under its bottle cap: verdigris, not brass (the cow's bell is the only brass). swing in
    degrees, positive to the right. Drive it with a decaying sine: 26 * sin(6 * tau) * exp(-tau)."""
    cam = as_cam(cam)
    z = cam.zoom
    hx, hy = cam.xy(*BELL_HANG)
    if not (-60 < hx < W + 60 and -60 < hy < H + 60):
        return (hx, hy)
    a = math.radians(swing)

    def R(px, py):
        return (hx + (px * math.cos(a) - py * math.sin(a)) * z, hy + (px * math.sin(a) + py * math.cos(a)) * z)

    body = [R(-3, 2), R(3, 2), R(6, 8), R(8, 18), R(10.5, 22), R(-10.5, 22), R(-8, 18), R(-6, 8)]
    ink.d.line([R(0, -1), R(0, 3)], fill=LINE + (255,), width=max(1, int(1.6 * z)))
    ink.d.polygon(body, fill=(86, 134, 122, 255))
    ink.d.line(body + body[:1], fill=LINE + (255,), width=max(1, int(1.3 * z)))
    ink.d.line([R(-7.5, 17), R(7.5, 17)], fill=(150, 196, 180, 255), width=max(1, int(z)))
    ink.d.line([R(-4, 6), R(-6.5, 16)], fill=(160, 206, 190, 255), width=max(1, int(1.2 * z)))
    ca = math.radians(swing * 1.7)
    cx, cy = R(0, 14)
    bx, by = cx + math.sin(ca - a) * 0 + 11 * z * math.sin(ca), cy + 11 * z * math.cos(ca)
    ink.d.line([(cx, cy), (bx, by)], fill=LINE + (255,), width=max(1, int(1.2 * z)))
    ink.d.ellipse([bx - 2.4 * z, by - 2.4 * z, bx + 2.4 * z, by + 2.4 * z], fill=(40, 60, 58, 255))
    return (hx, hy)


# ---- the holes

def _hole_table():
    rs = random.Random(374)
    out = [(318, 816, 26, -1), (362, 826, 28, 1), (410, 815, 26, -1)]        # the first three, where the board sets the first digs
    tries = 0
    while len(out) < 374 and tries < 40000:
        tries += 1
        k = len(out)
        if k < 40:
            x = clamp(rs.gauss(430, 150), 20, 940)
            y = BED_Y + 10 + rs.uniform(0, 1) ** 1.2 * 60
        else:
            x = rs.uniform(14, 946)
            y = BED_Y + 9 + rs.uniform(0, 1) ** 0.85 * 86
        if 596 < x < 850 and y < 842:          # the desks and the school's feet
            continue
        if 372 < x < 478 and y < 811:          # the board's legs
            continue
        if 478 < x < 602 and y < 812:          # the making place
            continue
        if any(abs(x - lx) < 12 for lx, _ in [(p[0] - 12, 0) for p in LAMPS]) and y < 812:
            continue
        wd = (12 if k >= 40 else 20) + (y - BED_Y) * 0.10 + rs.uniform(-2, 3)
        if any(abs(x - ox) < (wd + ow) * 0.48 and abs(y - oy) < 5.5 for ox, oy, ow, _ in out):
            continue
        out.append((x, y, wd, rs.choice((-1, 1))))
    return out


HOLES = _hole_table()


def hole_xy(k):
    """World (x, y) of the middle of hole number k (0-based), so a dog can be stood over it before it exists."""
    x, y, _, _ = HOLES[int(clamp(k, 0, len(HOLES) - 1))]
    return (x, y)


def dig_holes(ink, cam=None, count=0.0):
    """The holes dug so far. count may be a fraction: 2.4 = two holes and the third 40% dug. Holes never fill in:
    always pass a count at least as big as last frame's. Up to 374 (the real number of digs)."""
    cam = as_cam(cam)
    z = cam.zoom
    n = int(min(len(HOLES), math.ceil(count)))
    items = sorted(range(n), key=lambda q: HOLES[q][1])
    for q in items:
        x, y, wd, side = HOLES[q]
        f = clamp(count - q)
        sx, sy = cam.xy(x, y)
        if not (-40 < sx < W + 40 and -20 < sy < H + 20):
            continue
        a = wd / 2 * z * (0.45 + 0.55 * f)
        b = a * 0.40
        rs = random.Random(q * 7 + 1)
        # the spoil thrown out behind
        hx = sx + side * a * 1.5
        hr, hh = a * 0.95 * f ** 0.6, b * 1.5 * f ** 0.6
        heap = [(hx - hr, sy + b * 0.5)] + [(hx + hr * math.cos(math.radians(ang)), sy + b * 0.5 - hh * math.sin(math.radians(ang)) * (0.85 + 0.3 * rs.random())) for ang in range(180, -1, -30)]
        ink.d.polygon([(px + 1.5 * z, py + 2 * z) for px, py in heap], fill=(6, 22, 24, 90))
        ink.d.polygon(heap, fill=(118, 138, 120, 255))
        ink.d.line(heap, fill=(20, 40, 40, 230), width=max(1, int(z)))
        for _ in range(4):
            px, py = hx + rs.uniform(-0.7, 0.7) * hr, sy + b * 0.4 - rs.uniform(0.1, 0.8) * hh
            r = rs.uniform(0.9, 1.9) * z
            ink.d.ellipse([px - r, py - r * 0.7, px + r, py + r * 0.7], fill=(166, 182, 160, 255), outline=(30, 50, 48, 255))
        # the pit
        ink.d.ellipse([sx - a * 1.2, sy - b * 1.3, sx + a * 1.2, sy + b * 1.25], fill=(132, 150, 130, 255), outline=(26, 46, 44, 255))
        ink.d.ellipse([sx - a, sy - b, sx + a, sy + b], fill=(6, 22, 26, 255))
        ink.d.chord([sx - a, sy - b, sx + a, sy + b], 10, 170, fill=(40, 70, 70, 255))
        ink.d.arc([sx - a, sy - b, sx + a, sy + b], 200, 340, fill=(2, 10, 12, 255), width=max(1, int(1.5 * z)))


def making_place(ink, cam=None, progress=1.0):
    """The place the digger builds for the others to stand in (x 480..600 on the gravel): flat stones set one by one,
    then two planks laid across them. progress 0..1."""
    cam = as_cam(cam)
    z = cam.zoom
    x0, _, x1, y1 = MAKING
    n = 6
    rs = random.Random(66)
    for q in range(n):
        f = clamp(progress * (n + 2) - q)
        cx = lerp(x0 + 10, x1 - 10, q / (n - 1))
        rx, ry = rs.uniform(10, 13), rs.uniform(5, 6.5)
        if f <= 0:
            continue
        sx, sy = cam.xy(cx, y1 + 8 - 3 * smooth(f) + 10 * (1 - smooth(f)))
        col = mix_color((104, 120, 112), (140, 150, 136), rs.random())
        ink.d.ellipse([sx - rx * z, sy - ry * z + 2 * z, sx + rx * z, sy + ry * z + 3 * z], fill=(6, 22, 24, 110))
        ink.d.ellipse([sx - rx * z, sy - ry * z, sx + rx * z, sy + ry * z], fill=col + (255,), outline=LINE + (255,), width=max(1, int(1.2 * z)))
        ink.d.arc([sx - rx * z * 0.8, sy - ry * z * 0.8, sx + rx * z * 0.4, sy + ry * z * 0.2], 190, 300, fill=(190, 204, 188, 255), width=max(1, int(z)))
    for q in range(2):
        f = smooth(clamp(progress * (n + 2) - n - q * 0.8))
        if f <= 0:
            continue
        ax, ay = cam.xy(x0 + 2, y1 - 2 - q * 5 - 30 * (1 - f))
        bx, by = cam.xy(x1 - 2, y1 - 4 - q * 5 - 30 * (1 - f))
        th = 4.2 * z
        ink.d.polygon([(ax, ay), (bx, by), (bx, by + th), (ax, ay + th)], fill=(156, 128, 92, 255))
        ink.d.line([(ax, ay), (bx, by), (bx, by + th), (ax, ay + th), (ax, ay)], fill=LINE + (255,), width=max(1, int(1.2 * z)))
        ink.d.line([(ax + 4 * z, ay + th * 0.5), (bx - 4 * z, by + th * 0.5)], fill=(110, 88, 62, 255), width=1)
    return cam.xy((x0 + x1) / 2, y1 - 10)


# ------------------------------------------------- the children's drawings ---

_DRAW = {}


def _drawings():
    """Stroke lists redrawn from the earlier films' traced pencil strokes, each fitted to a unit box.
    {name: [(pts Nx2 in -0.5..0.5, weight, cumulative_start, cumulative_end)]}"""
    if _DRAW:
        return _DRAW
    sw = FILMS / "swarm"

    def fit(strokes, pad=0.0):
        allp = np.concatenate([p for p, _ in strokes])
        lo, hi = allp.min(0), allp.max(0)
        sc = 1.0 / max(hi[0] - lo[0], hi[1] - lo[1])
        mid = (lo + hi) / 2
        out, tot = [], 0.0
        for p, wt in strokes:
            q = (p - mid) * sc * (1 - pad)
            ln = float(np.hypot(*np.diff(q, axis=0).T).sum()) + 1e-4
            out.append([q, wt, tot, tot + ln])
            tot += ln
        return [(q, wt, a / tot, b / tot) for q, wt, a, b in out]

    def curve(pts, sharp=False):
        pts = [tuple(map(float, p)) for p in pts]
        if sharp or len(pts) < 3:
            return np.array(pts, np.float32)
        return np.array(w.catmull(pts, 5), np.float32)

    # c10 · the jaw: zigzag teeth in a slanted box, and the second jaw outside the ring (brought closer so both fit)
    m = _load("c10_world_for_town", sw / "c10" / "world.py")
    st = []
    jaw = [s for s in m.PILOT_STROKES if s["part"] == "jaw"]
    outs = [s for s in m.PILOT_STROKES if s["part"] != "jaw"]
    jx0, jx1 = min(p[0] for s in jaw for p in s["pts"]), max(p[0] for s in jaw for p in s["pts"])
    jy1 = max(p[1] for s in jaw for p in s["pts"])
    ox0 = min(p[0] for s in outs for p in s["pts"])
    oy0 = min(p[1] for s in outs for p in s["pts"])
    shift, drop = (jx0 + (jx1 - jx0) * 0.42) - ox0, (jy1 + 26) - oy0
    for s in jaw:
        st.append((curve(s["pts"], s.get("sharp")), s["weight"]))
    for s in outs:
        st.append((curve([(x + shift, y + drop) for x, y in s["pts"]], s.get("sharp")), s["weight"]))
    _DRAW["jaw"] = fit(st)
    _DRAW["jaw_only"] = fit([(curve(s["pts"], s.get("sharp")), s["weight"]) for s in jaw])
    # c13 · the fish and the bell (the lettered bubble is left out: no words)
    st = [(curve(s["pts"]), s["weight"]) for s in w.PILOT_STROKES if s["group"] in ("fish1", "bell", "fish2", "weed_r", "weed_l")]
    _DRAW["fish_bell"] = fit(st)
    # c16 · the boxy sub (the faint guide lines and the turkey's head are left out)
    m = _load("c16_world_for_town", sw / "c16" / "world.py")
    st = [(curve(s["pts"], s.get("sharp")), s["weight"]) for s in m.PILOT_STROKES if s["part"] in ("box", "dome", "window", "scribble1", "blocks", "right")]
    _DRAW["sub"] = fit(st)
    # c25 · the fish in a bowl with legs
    m = _load("c25_world_for_town", sw / "c25" / "world.py")
    _DRAW["bowl_legs"] = fit([(curve(s["pts"]), s["weight"]) for s in m.PILOT_STROKES])
    # c33 · the bars across the window, the fish behind them
    m = _load("c33_world_for_town", sw / "c33" / "world.py")
    _DRAW["bars"] = fit([(curve(s["pts"]), s["weight"]) for s in m.PILOT_STROKES if s["group"] != "cracks"])
    # a child's scribble line, for the pages that are not drawings (no letters: loops and a zigzag)
    rs = random.Random(2)
    for name, rows in (("scribble", 4), ("scribble2", 3)):
        st = []
        for r in range(rows):
            pts, x = [], -0.45
            while x < 0.42 - rs.uniform(0, 0.25):
                pts.append((x, r / rows - 0.4 + rs.uniform(-0.035, 0.035)))
                x += rs.uniform(0.03, 0.07)
            st.append((curve(pts), 0.6))
        _DRAW[name] = fit(st, pad=0.05)
    return _DRAW


def picture(target, name, cx, cy, size, progress=1.0, color=(52, 54, 66), width=None, alpha=1.0, tidy=False, seed=0):
    """One of the children's drawings, redrawn as pencil strokes, centred at screen (cx, cy) and fitted in a square
    `size` px across. name: 'jaw' | 'fish_bell' | 'sub' | 'bowl_legs' | 'bars' | 'jaw_only' | 'scribble' | 'scribble2'.
    progress 0..1 draws it stroke by stroke in the child's order. tidy=True is the WRONG version for the reel the
    person refuses: every stroke ruled straight and the second jaw gone. target is an Ink, an ImageDraw or an image."""
    d = target.d if isinstance(target, Ink) else (target if hasattr(target, "line") else ImageDraw.Draw(target, "RGBA"))
    D = _drawings()
    if tidy and name == "jaw":
        name = "jaw_only"
    strokes = D[name]
    base_w = width if width is not None else max(1.0, size * 0.028)
    rs = random.Random(seed * 17 + len(name))
    for pts, wt, a, b in strokes:
        if progress <= a:
            break
        f = clamp((progress - a) / max(1e-6, b - a))
        n = max(2, int(math.ceil(len(pts) * f)))
        p = pts[:n]
        if tidy:
            p = np.array([p[0], p[-1]], np.float32) if len(p) < 12 else p[:: max(1, len(p) // 3)]
            jit = 0.0
        else:
            jit = size * 0.004
        xy = [(cx + float(x) * size + rs.uniform(-jit, jit), cy + float(y) * size + rs.uniform(-jit, jit)) for x, y in p]
        if len(xy) < 2:
            continue
        al = int(255 * alpha * clamp(0.5 + 0.7 * wt))
        d.line(xy, fill=tuple(color[:3]) + (al,), width=max(1, int(round(base_w * (0.6 + 0.6 * wt)))), joint="curve")


def page(ink, cam, x, y, drawing="jaw", angle=0.0, size=26.0, sag=0.0, alpha=1.0, wet=0.0, smudge=0, screen=False, progress=1.0):
    """One loose page from the class: cream paper with a child's drawing on it, centred at world (x, y) (or screen
    px with screen=True). size = its height in world px; angle degrees counter-clockwise; sag 0..1 lets a wet page
    droop at the far corner; wet 0..1 darkens it; smudge = how many wet nose marks are on it. Returns its screen centre."""
    cam = as_cam(cam)
    z = 1.0 if screen else cam.zoom
    sx, sy = (x, y) if screen else cam.xy(x, y)
    hh = size * z / 2
    hw = hh * 0.8
    ss = 3
    S = int((hh * 2 + 10) * ss * 1.5)
    im, d = _layer((S, S))
    c = S / 2
    pts = [(c - hw * ss, c - hh * ss), (c + hw * ss, c - hh * ss), (c + hw * ss * (1 - 0.1 * sag), c + hh * ss * (1 + 0.16 * sag)), (c - hw * ss, c + hh * ss)]
    paper = mix_color((238, 232, 208), (176, 186, 170), wet * 0.7)
    d.polygon([(px + 2 * ss, py + 2.4 * ss) for px, py in pts], fill=(6, 20, 24, 90))
    d.polygon(pts, fill=paper + (255,))
    d.line(pts + pts[:1], fill=(60, 64, 60, 255), width=max(1, int(0.9 * ss)))
    picture(d, drawing, c, c - hh * ss * 0.04, hw * ss * 1.62, progress=progress, width=max(ss * 0.8, hw * ss * 0.05), seed=3)
    rs = random.Random(sum(map(ord, drawing)) + 5)
    if smudge:
        wetl, wd_ = _layer((S, S))
        for _ in range(int(smudge)):
            mx, my = c + rs.uniform(-0.6, 0.6) * hw * ss, c + rs.uniform(-0.6, 0.7) * hh * ss
            r = hw * ss * 0.16
            wd_.ellipse([mx - r, my - r * 0.8, mx + r, my + r * 0.8], fill=(110, 140, 138, 96), outline=(84, 118, 120, 150))
        im.alpha_composite(wetl)
    im = im.rotate(angle, resample=Image.BICUBIC).resize((S // ss, S // ss), Image.LANCZOS)
    ink.paste(im, (sx - im.width / 2, sy - im.height / 2), alpha)
    return (sx, sy)


# ---- the notice board

_BOARD_PAGES = [   # (dx, dy from the panel's top-left, angle, drawing, pin colour)
    (17, 22, 5, "jaw", (206, 60, 54)), (45, 20, -4, "fish_bell", (240, 200, 80)), (73, 23, 3, "sub", (70, 130, 200)),
    (16, 62, -3, "bowl_legs", (240, 200, 80)), (44, 65, 6, "scribble", (236, 236, 226)), (73, 63, -5, "bars", (206, 60, 54)),
]


def board_page_xy(k):
    """World (x, y) of the middle of page k on the notice board (0..5): 0 the jaw, 1 the fish and the bell, 2 the
    boxy sub, 3 the fish in a bowl with legs, 4 a page of scribble, 5 the bars."""
    dx, dy = _BOARD_PAGES[k][0], _BOARD_PAGES[k][1]
    return (BOARD[0] + dx, BOARD[1] + dy)


def notice_board(ink, t, cam=None, taken=(), smudges=0, pull=None, calm=False):
    """The notice board: the lid of a cigar box on two twigs, six of the class's pages pinned to it (drawings and
    scribble, no letters). taken = indices of pages that have gone (a paler patch and a pin hole stay).
    smudges = how many wet nose marks there are so far (0..131; each look leaves one, they never dry).
    pull = (k, 0..1): page k being drawn off by one corner. Returns {'pages': {k: screen xy}, 'foot': screen xy}."""
    cam = as_cam(cam)
    z = cam.zoom
    x0, y0, x1, y1 = BOARD
    a, b = cam.xy(x0, y0), cam.xy(x1, y1)
    out = {"pages": {}, "foot": cam.xy(x0 + 12, BED_Y + 4)}
    if b[0] < -60 or a[0] > W + 60 or b[1] < -80 or a[1] > H + 60:
        return out
    lw = max(1, int(round(1.4 * z)))
    for lx in (x0 + 7, x1 - 7):                                    # the legs
        p, q = cam.xy(lx, y0 + 4), cam.xy(lx + (1 if lx < 420 else -1), BED_Y + 5)
        ink.d.line([p, q], fill=(34, 30, 26, 255), width=max(2, int(5 * z)))
        ink.d.line([p, q], fill=(104, 84, 60, 255), width=max(1, int(3 * z)))
    ink.d.rectangle([a[0] - 3 * z, a[1] - 3 * z, b[0] + 3 * z, b[1] + 3 * z], fill=(78, 56, 40, 255), outline=LINE + (255,), width=lw)
    ink.d.rectangle([a[0], a[1], b[0], b[1]], fill=(128, 100, 70, 255), outline=(40, 30, 24, 255), width=max(1, int(z)))
    rs = random.Random(9)
    for _ in range(40):                                            # cork fleck
        fx, fy = lerp(a[0], b[0], rs.random()), lerp(a[1], b[1], rs.random())
        ink.d.ellipse([fx - z, fy - 0.6 * z, fx + z, fy + 0.6 * z], fill=(98, 76, 52, 255))
    top = [cam.xy(x0 - 8, y0 - 3), cam.xy((x0 + x1) / 2, y0 - 12), cam.xy(x1 + 8, y0 - 3)]   # a little roof: a split reed
    ink.d.polygon(top, fill=(58, 92, 70, 255))
    ink.d.line(top + top[:1], fill=LINE + (255,), width=lw)
    tt = 0.0 if calm else t
    marks = _smudge_table()
    for k, (dx, dy, ang, name, pin) in enumerate(_BOARD_PAGES):
        wx, wy = x0 + dx, y0 + dy
        sx, sy = cam.xy(wx, wy)
        out["pages"][k] = (sx, sy)
        if k in taken:
            hw, hh = 10.4 * z, 13 * z
            ink.d.rectangle([sx - hw, sy - hh, sx + hw, sy + hh], fill=(146, 118, 84, 255))
            ink.d.ellipse([sx - z, sy - hh + 2 * z, sx + z, sy - hh + 4 * z], fill=(40, 28, 20, 255))
            continue
        f = pull[1] if pull and pull[0] == k else 0.0
        sway = 1.6 * math.sin(tt * 1.3 + k * 1.7)
        n = sum(1 for m in marks[: int(smudges)] if m == k)
        page(ink, cam, wx - 7 * f, wy + 9 * f, name, angle=ang + sway + 24 * f, size=26, sag=0.3 + 0.5 * f, smudge=min(n, 9))
        if f < 0.5:
            px, py = cam.xy(wx + math.sin(math.radians(ang)) * 11, wy - 11)
            ink.d.ellipse([px - 1.9 * z, py - 1.9 * z, px + 1.9 * z, py + 1.9 * z], fill=pin + (255,), outline=LINE + (255,))
    return out


@lru_cache(maxsize=1)
def _smudge_table():
    rs = random.Random(131)
    return [rs.randrange(6) for _ in range(131)]


# ----------------------------------------------------------- the peoplefish ---

_PROF_F = (3, 8, 13, 20, 30, 40, 50, 60, 70)                      # measured off the engraving (fins left out)
_PROF_BACK = (0.45, 0.412, 0.387, 0.347, 0.294, 0.274, 0.27, 0.30, 0.367)
_PROF_BELLY = (0.618, 0.683, 0.711, 0.744, 0.776, 0.751, 0.75, 0.74, 0.70)
SATCHELS = [(52, 104, 196), (200, 64, 56), (236, 196, 70), (70, 150, 96), (226, 132, 60), (226, 130, 170), (130, 96, 170), (232, 228, 214)]
FISH_LEN = dict(child=54, teacher=98, cook=88, towns=82, post=80, lady=84)


def fish(ink, t, cam, x, y, kind="child", facing=1, tilt=0.0, arm=20.0, look=None, hold=None, seed=0, length=None,
         satchel=True, lid=0.0, swim=1.0, depth=1.0, alpha=1.0, calm=False, screen=False, mouth_open=0.0):
    """One of the peoplefish: a brook trout standing on its tail like a person, with a cut-paper eye, a fin for an
    arm, and whatever it wears. (x, y) is the world point its tail stands on (screen px with screen=True).
    kind: 'child' (satchel; seed picks its colour and size, seed 0 is the jaw child with the blue satchel),
          'teacher' (spectacles, shawl, a reed pointer), 'cook' (white hat, apron), 'post' (cap and bag),
          'lady' (hat with a weed feather), 'towns' (scarf).
    facing +1 right / -1 left. tilt degrees: 0 upright, 20 leaning forward over a desk, 90 swimming flat, negative
    leaning back to look up. arm degrees: 0 fin down at its side, 90 pointing forward, 150 up (waving: animate it).
    look = a WORLD point the eye looks at (None: straight ahead). hold = None | 'pointer' | 'page:<drawing>' | 'chalk'.
    lid 0..1 closes the eye (blink, sleep). swim 0..1 how hard the tail works. depth < 1 sends it back into the haze.
    Returns screen points {'mouth', 'eye', 'head', 'hand', 'centre', 'foot'} and 'length' (screen px)."""
    cam = as_cam(cam)
    z = 1.0 if screen else cam.s(depth)
    sx, sy = (x, y) if screen else cam.xy(x, y, depth)
    rs = random.Random(seed * 31 + sum(map(ord, kind)) % 97)
    L0 = length or FISH_LEN.get(kind, 80) * (1.0 if kind != "child" else (0.86 if seed == 0 else rs.uniform(0.92, 1.1)))
    Ls = L0 * z
    if sx < -Ls * 1.6 or sx > W + Ls * 1.6 or sy < -Ls * 0.6 or sy > H + Ls * 1.6:
        return {k: (sx, sy) for k in ("mouth", "eye", "head", "hand", "centre", "foot")} | {"length": Ls}
    ss = 2
    Lq = max(48, int(math.ceil(Ls * ss / 8.0)) * 8)                  # build length (cached by the trout cutter)
    k = Ls * ss / Lq                                                 # final scale
    tt = 0.0 if calm else t
    ph = tt * (3.2 + 2.0 * swim) + seed * 1.3
    spr0 = w.trout_sprite(Lq, ph, (4.0 + 9.0 * swim) * (0 if calm else 1), 0.0)
    body = spr0.transpose(Image.TRANSPOSE)                           # head up, belly to the right
    B = w._trout_base()
    bh = int(Lq * B["img"].height / B["img"].width)
    pad = int(Lq * 0.12)
    Wc, Hc = int(Lq * 1.9), int(Lq * 1.62)
    im, d = _layer((Wc, Hc))
    ox, top = Wc // 2 - body.width // 2, int(Lq * 0.36)
    eye = (ox + B["eye"][1] * bh + pad, top + B["eye"][0] * Lq)
    u = Lq / 100.0                                                   # one percent of the fish
    lw = max(1, int(round(u * 1.5)))
    bx0 = ox + pad

    def bk(f):                                                       # the back's edge at f percent down the fish
        return bx0 + bh * float(np.interp(f, _PROF_F, _PROF_BACK))

    def bl(f):                                                       # the belly's edge
        return bx0 + bh * float(np.interp(f, _PROF_F, _PROF_BELLY))

    cxb = bx0 + bh * 0.535
    back_x, belly_x = bk(30), bl(30)
    # ---- behind the body: satchel / bag
    scol = SATCHELS[seed % len(SATCHELS)]
    if (kind == "child" and satchel) or kind == "post":
        bx, by = bk(46) + 1 * u, top + 46 * u
        bw_, bh_ = (15 * u, 19 * u) if kind == "child" else (16 * u, 22 * u)
        col = scol if kind == "child" else (150, 112, 70)
        d.rounded_rectangle([bx - bw_, by - bh_ / 2, bx + 5 * u, by + bh_ / 2], radius=3 * u, fill=col + (255,), outline=LINE + (255,), width=lw)
        d.line([(bx - bw_, by - bh_ * 0.12), (bx + 3 * u, by - bh_ * 0.12)], fill=mix_color(col, LINE, 0.55) + (255,), width=lw)
        d.ellipse([bx - bw_ * 0.5 - 1.6 * u, by - 0.2 * u, bx - bw_ * 0.5 + 1.6 * u, by + 3 * u], fill=(240, 226, 170, 255), outline=LINE + (255,))
    im.alpha_composite(body, (ox, top))
    d = ImageDraw.Draw(im, "RGBA")
    # ---- on the body
    if (kind == "child" and satchel) or kind == "post":
        d.line([(bk(40) + 1 * u, top + 40 * u), (bl(22) - 1 * u, top + 22 * u)], fill=mix_color(scol if kind == "child" else (150, 112, 70), LINE, 0.35) + (255,), width=max(2, int(2.6 * u)))
    if kind == "teacher":                                            # a lilac shawl with a fringe
        sh = [(bk(21) - 1 * u, top + 21 * u), (bl(21) + 1 * u, top + 22 * u), (bl(31) + 2 * u, top + 32 * u), (cxb, top + 39 * u), (bk(31) - 2.5 * u, top + 32 * u)]
        d.polygon(sh, fill=(164, 132, 188, 255))
        d.line(sh + sh[:1], fill=LINE + (255,), width=lw)
        for q in range(7):
            fx = lerp(bk(31) - 2.5 * u, bl(31) + 2 * u, q / 6)
            fy = top + (32 + 7 * math.sin(math.pi * q / 6)) * u
            d.line([(fx, fy), (fx, fy + 4 * u)], fill=(120, 92, 150, 255), width=max(1, int(u)))
    if kind == "cook":                                               # an apron
        ap = [(cxb - 3 * u, top + 30 * u), (bl(30) + 1.5 * u, top + 30 * u), (bl(62) + 1.5 * u, top + 63 * u), (cxb - 5 * u, top + 60 * u)]
        d.polygon(ap, fill=(238, 234, 220, 255))
        d.line(ap + ap[:1], fill=LINE + (255,), width=lw)
        d.line([(bk(31), top + 31 * u), (cxb - 3 * u, top + 30 * u)], fill=(238, 234, 220, 255), width=max(1, int(1.6 * u)))
    if kind in ("towns", "lady", "post"):                            # a scarf
        col = [(206, 70, 60), (70, 130, 190), (236, 196, 70)][seed % 3]
        d.polygon([(bk(27), top + 26 * u), (bk(27) - 7 * u, top + 41 * u), (bk(27) - 2 * u, top + 43 * u), (bk(27) + 4 * u, top + 28 * u)], fill=col + (255,), outline=LINE + (255,))
        d.polygon([(bk(21) - 1 * u, top + 21 * u), (bl(21) + 1 * u, top + 22.5 * u), (bl(27) + 1 * u, top + 28.5 * u), (bk(27) - 1 * u, top + 27 * u)], fill=col + (255,), outline=LINE + (255,))
    # ---- the eye: cut paper, big enough to act with
    er = 5.6 * u
    lx_, ly_ = 1.0, 0.0
    if look is not None:
        # direction to the looked-at point in the fish's own frame (undo facing and tilt)
        ex_w = sx + facing * 0
        vx, vy = (cam.xy(look[0], look[1])[0] - sx) * facing, cam.xy(look[0], look[1])[1] - (sy - Ls * 0.85)
        a = math.radians(-tilt)
        vx, vy = vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)
        n = math.hypot(vx, vy) or 1.0
        lx_, ly_ = vx / n, vy / n
    d.ellipse([eye[0] - er, eye[1] - er, eye[0] + er, eye[1] + er], fill=(250, 246, 232, 255), outline=LINE + (255,), width=lw)
    pr = er * 0.52
    px, py = eye[0] + lx_ * er * 0.42, eye[1] + ly_ * er * 0.42
    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(16, 14, 14, 255))
    d.ellipse([px - pr * 0.45, py - pr * 0.6, px - pr * 0.05, py - pr * 0.2], fill=(255, 255, 255, 255))
    if lid > 0.02:
        m = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(m)
        md.ellipse([eye[0] - er, eye[1] - er, eye[0] + er, eye[1] + er], fill=255)
        md.rectangle([eye[0] - er - 2, eye[1] - er + 2 * er * lid, eye[0] + er + 2, eye[1] + er + 2], fill=0)
        im.paste(Image.new("RGBA", im.size, (150, 132, 84, 255)), (0, 0), m)
        d = ImageDraw.Draw(im, "RGBA")
        yl = eye[1] - er + 2 * er * lid
        hwid = math.sqrt(max(0.0, er * er - (yl - eye[1]) ** 2))
        d.line([(eye[0] - hwid, yl), (eye[0] + hwid, yl)], fill=LINE + (255,), width=lw)
    mouth = (bl(3) - 1.0 * u, top + 3.5 * u)
    if mouth_open > 0.02:
        mr = 2.6 * u * mouth_open
        d.ellipse([mouth[0] - mr, mouth[1] - mr * 1.2, mouth[0] + mr, mouth[1] + mr * 1.2], fill=(40, 16, 20, 255), outline=LINE + (255,))
    head_top = (cxb, top)
    # ---- what is on its head
    if kind == "teacher":
        d.ellipse([eye[0] - er * 1.5, eye[1] - er * 1.5, eye[0] + er * 1.5, eye[1] + er * 1.5], outline=(30, 26, 24, 255), width=max(2, int(1.8 * u)))
        d.line([(eye[0] - er * 1.5, eye[1] - 1 * u), (bk(14) + 1 * u, eye[1] + 2 * u)], fill=(30, 26, 24, 255), width=max(1, int(1.4 * u)))
        d.ellipse([bk(8) - 8 * u, top + 3 * u, bk(8) + 3 * u, top + 13 * u], fill=(96, 92, 100, 255), outline=LINE + (255,), width=lw)    # a bun
        d.line([(bk(8) - 10 * u, top + 12 * u), (bk(8) + 3 * u, top + 2 * u)], fill=(226, 190, 90, 255), width=max(1, int(1.4 * u)))
    elif kind == "cook":
        hat = [(cxb - 8 * u, top + 5 * u), (cxb - 9 * u, top - 5 * u), (cxb - 13 * u, top - 11 * u), (cxb - 8 * u, top - 18 * u), (cxb, top - 15 * u),
               (cxb + 7 * u, top - 19 * u), (cxb + 12 * u, top - 11 * u), (cxb + 8 * u, top - 5 * u), (cxb + 7 * u, top + 4 * u)]
        d.polygon(hat, fill=(244, 240, 228, 255))
        d.line(hat + hat[:1], fill=LINE + (255,), width=lw)
        d.line([(cxb - 8.5 * u, top - 1 * u), (cxb + 7.5 * u, top - 2 * u)], fill=(170, 170, 160, 255), width=max(1, int(u)))
    elif kind == "post":
        d.polygon([(cxb - 8 * u, top + 5 * u), (cxb - 7 * u, top - 4 * u), (cxb + 6 * u, top - 5 * u), (cxb + 8 * u, top + 4 * u)], fill=(46, 66, 110, 255), outline=LINE + (255,))
        d.polygon([(cxb + 7 * u, top + 1 * u), (cxb + 17 * u, top + 5 * u), (cxb + 8 * u, top + 5.5 * u)], fill=(24, 30, 50, 255), outline=LINE + (255,))
    elif kind == "lady":
        d.ellipse([cxb - 15 * u, top - 1 * u, cxb + 14 * u, top + 7 * u], fill=(190, 110, 130, 255), outline=LINE + (255,), width=lw)
        d.ellipse([cxb - 7 * u, top - 9 * u, cxb + 6 * u, top + 4 * u], fill=(206, 126, 146, 255), outline=LINE + (255,), width=lw)
        d.line([(cxb - 3 * u, top - 6 * u), (cxb - 11 * u, top - 19 * u), (cxb - 18 * u, top - 21 * u)], fill=(70, 140, 84, 255), width=max(2, int(2.2 * u)))
    elif kind == "towns":
        d.polygon([(cxb - 12 * u, top + 5 * u), (cxb + 11 * u, top + 4 * u), (cxb + 6 * u, top + 1 * u), (cxb + 5.5 * u, top - 9 * u), (cxb - 6.5 * u, top - 9 * u),
                   (cxb - 7 * u, top + 2 * u)], fill=(60, 56, 58, 255), outline=LINE + (255,))
    elif kind == "child" and seed % 3 == 1:
        col = SATCHELS[(seed + 3) % len(SATCHELS)]
        d.pieslice([cxb - 8 * u, top - 4 * u, cxb + 8 * u, top + 12 * u], 180, 360, fill=col + (255,), outline=LINE + (255,))
        d.ellipse([cxb - 2 * u, top - 7 * u, cxb + 2 * u, top - 3 * u], fill=(250, 246, 232, 255), outline=LINE + (255,))
    elif kind == "child" and seed % 3 == 2:                          # a bow
        for sg in (-1, 1):
            d.polygon([(bk(8) + 1 * u, top + 7 * u), (bk(8) + sg * 3 * u - 6 * u, top + 7 * u + sg * 7 * u), (bk(8) - 8 * u, top + 7 * u - sg * 1 * u)],
                      fill=(226, 90, 110, 255), outline=LINE + (255,))
    # ---- the fin that is an arm
    shx, shy = bl(31) - 3 * u, top + 31 * u
    a = math.radians(arm)
    ax, ay = math.sin(a), math.cos(a)                                # 0 = down, 90 = forward (right)
    nx, ny = ay, -ax
    fl = 24 * u
    fin = [(shx - nx * 2 * u, shy - ny * 2 * u), (shx + ax * fl * 0.5 - nx * 6.5 * u, shy + ay * fl * 0.5 - ny * 6.5 * u), (shx + ax * fl, shy + ay * fl),
           (shx + ax * fl * 0.62 + nx * 5 * u, shy + ay * fl * 0.62 + ny * 5 * u), (shx + nx * 3 * u, shy + ny * 3 * u)]
    hand = (shx + ax * fl * 0.92, shy + ay * fl * 0.92)
    tip = None
    if hold == "pointer":
        tip = (hand[0] + ax * 62 * u, hand[1] + ay * 62 * u)
        d.line([(shx + ax * fl * 0.5, shy + ay * fl * 0.5), tip], fill=(50, 40, 30, 255), width=max(2, int(2.6 * u)))
        d.line([(shx + ax * fl * 0.5, shy + ay * fl * 0.5), tip], fill=(200, 176, 120, 255), width=max(1, int(1.3 * u)))
    elif hold == "chalk":
        tip = (hand[0] + ax * 7 * u, hand[1] + ay * 7 * u)
        d.line([hand, tip], fill=(250, 250, 244, 255), width=max(2, int(3 * u)))
    elif hold and hold.startswith("page"):
        nm = hold.split(":")[1] if ":" in hold else "scribble"
        pc = (hand[0] + ax * 12 * u, hand[1] + ay * 12 * u)
        pw, phh = 13 * u, 16 * u
        d.rectangle([pc[0] - pw, pc[1] - phh, pc[0] + pw, pc[1] + phh], fill=(238, 232, 208, 255), outline=(60, 64, 60, 255), width=lw)
        picture(d, nm, pc[0], pc[1], pw * 1.7, width=max(1.0, u * 1.3))
        tip = pc
    d.polygon(fin, fill=(214, 120, 66, 255))
    d.line(fin + fin[:1], fill=LINE + (255,), width=lw)
    d.line([fin[0], fin[1], fin[2]], fill=(248, 240, 224, 255), width=max(1, int(1.6 * u)))
    foot = (cxb, top + Lq * 0.97)
    centre = (cxb, top + Lq * 0.5)
    # ---- sink it into the water, then turn, flip, size and lay it
    arr = np.asarray(im, np.float32).copy()
    hz = clamp((1 - depth) * 0.9)
    arr[..., :3] = arr[..., :3] * np.array((0.80, 0.93, 0.95), np.float32) * (1 - hz) + np.array(WATER, np.float32) * hz
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    sway = 0.0 if calm else 2.2 * math.sin(tt * 1.1 + seed * 2.3)
    ang = tilt + sway
    bb = im.getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bb)
    rot = im.rotate(-ang, expand=True, resample=Image.BILINEAR)
    ra = math.radians(ang)

    def T(p):
        vx, vy = p[0] - foot[0], p[1] - foot[1]
        rx, ry = vx * math.cos(ra) - vy * math.sin(ra), vx * math.sin(ra) + vy * math.cos(ra)
        return (sx + facing * rx * k / ss, sy + ry * k / ss)

    vx, vy = foot[0] - bb[0] - im.width / 2, foot[1] - bb[1] - im.height / 2
    pvx, pvy = rot.width / 2 + vx * math.cos(ra) - vy * math.sin(ra), rot.height / 2 + vx * math.sin(ra) + vy * math.cos(ra)
    if facing < 0:
        rot = rot.transpose(Image.FLIP_LEFT_RIGHT)
        pvx = rot.width - pvx
    f = k / ss
    out = rot.resize((max(2, int(round(rot.width * f))), max(2, int(round(rot.height * f)))), Image.LANCZOS)
    ink.paste(out, (sx - pvx * f, sy - pvy * f), alpha)
    return {"mouth": T(mouth), "eye": T(eye), "head": T(head_top), "hand": T(tip or hand), "centre": T(centre), "foot": (sx, sy), "length": Ls}


def desk(ink, cam, x, y, seed=0):
    """A school desk: a matchbox tray on two dress pins. Foot at world (x, y); draw it AFTER the child that sits
    behind it. 32 wide, 25 high."""
    cam = as_cam(cam)
    z = cam.zoom
    sx, sy = cam.xy(x, y)
    if not (-40 < sx < W + 40 and -40 < sy < H + 40):
        return (sx, sy)
    lw = max(1, int(round(1.2 * z)))
    col = [(70, 112, 170), (190, 150, 70), (170, 80, 66), (90, 140, 110)][seed % 4]
    for lx in (-11, 11):
        ink.d.line([(sx + lx * z, sy - 14 * z), (sx + lx * z, sy + 1 * z)], fill=LINE + (255,), width=max(2, int(2.6 * z)))
        ink.d.line([(sx + lx * z, sy - 14 * z), (sx + lx * z, sy + 1 * z)], fill=(168, 174, 166, 255), width=max(1, int(1.2 * z)))
        ink.d.ellipse([sx + lx * z - 2.2 * z, sy - 0.8 * z, sx + lx * z + 2.2 * z, sy + 2.4 * z], fill=(190, 196, 186, 255), outline=LINE + (255,))
    box = [(sx - 15 * z, sy - 25 * z), (sx + 16 * z, sy - 22 * z), (sx + 16 * z, sy - 12 * z), (sx - 15 * z, sy - 12 * z)]
    ink.d.polygon([(px + 2 * z, py + 2.5 * z) for px, py in box], fill=(6, 20, 24, 80))
    ink.d.polygon(box, fill=(150, 120, 84, 255))
    ink.d.polygon([(sx - 15 * z, sy - 25 * z), (sx - 8 * z, sy - 24.3 * z), (sx - 8 * z, sy - 12 * z), (sx - 15 * z, sy - 12 * z)], fill=mix_color(col, (60, 80, 80), 0.35) + (255,))
    ink.d.line(box + box[:1], fill=LINE + (255,), width=lw)
    ink.d.line([(sx - 16 * z, sy - 25.6 * z), (sx + 17 * z, sy - 22.4 * z)], fill=(196, 170, 124, 255), width=max(1, int(1.8 * z)))
    return (sx, sy)


def slate(ink, cam=None, drawing="fish_bell", progress=1.0, x=None, y=None):
    """The teacher's slate on its easel (a roofing slate on three matches), with a chalk picture on it: no letters.
    progress 0..1 chalks the picture on. Foot at world (x, y), default SLATE_XY."""
    cam = as_cam(cam)
    z = cam.zoom
    x, y = (SLATE_XY[0] if x is None else x), (SLATE_XY[1] if y is None else y)
    sx, sy = cam.xy(x, y)
    lw = max(1, int(round(1.3 * z)))
    for lx, tx in ((-13, -9), (13, 9), (2, 0)):
        ink.d.line([(sx + lx * z, sy), (sx + tx * z, sy - 46 * z)], fill=(40, 32, 26, 255), width=max(2, int(3.4 * z)))
        ink.d.line([(sx + lx * z, sy), (sx + tx * z, sy - 46 * z)], fill=(206, 182, 132, 255), width=max(1, int(1.6 * z)))
    box = [(sx - 19 * z, sy - 48 * z), (sx + 20 * z, sy - 50 * z), (sx + 21 * z, sy - 17 * z), (sx - 18 * z, sy - 15 * z)]
    ink.d.polygon(box, fill=(44, 58, 64, 255))
    ink.d.line(box + box[:1], fill=(170, 150, 110, 255), width=max(2, int(2.4 * z)))
    ink.d.line(box + box[:1], fill=LINE + (255,), width=1)
    picture(ink, drawing, sx + 1 * z, sy - 32.5 * z, 29 * z, progress=progress, color=(236, 238, 226), width=max(1.0, 1.1 * z), seed=5)
    return (sx, sy - 32 * z)


def _per(v, k, default):
    if isinstance(v, dict):
        return v.get(k, default)
    if isinstance(v, (list, tuple)) and len(v) > k and not (len(v) == 2 and all(isinstance(q, (int, float)) for q in v)):
        return v[k]
    return default if v is None else v


def school_class(ink, t, cam=None, facing=1, look=None, tilt=8.0, speak=None, arm=None, skip=(), calm=False,
                 teacher=True, slate_drawing="fish_bell", slate_progress=1.0, desks=True, lid=None):
    """The fish class at their desks in the yard, the teacher and the slate. Eight children: SEATS[k], child 0 is
    the jaw child (smallest, blue satchel, front row left). Every keyword may be one value for all, or a dict
    {child index: value} ('T' is the teacher):
      facing +1 (toward the teacher, right) / -1;  look = a WORLD point to look at (default: the slate);
      tilt degrees (8 = sitting forward; -25 = leaning back to look up at the door);  arm degrees (150 = fin up);
      lid 0..1;  speak = {k: (drawing, grow 0..1[, progress 0..1[, pop 0..1]])} blows that child's bubble.
    skip = children who are not at their desks (draw them yourself with child()). Returns {k: fish() points}."""
    cam = as_cam(cam)
    out = {}
    look_d = look
    if slate_drawing:
        slate(ink, cam, slate_drawing, slate_progress)
    order = [4, 5, 6, 7, 0, 1, 2, 3]
    spoken = []
    for k in order:
        x, y = SEATS[k]
        if k in skip:
            if desks:
                desk(ink, cam, x + 12, y + 2, k)
            continue
        fc = _per(facing, k, 1)
        lk = _per(look_d, k, None) if isinstance(look_d, dict) else look_d
        if lk is None:
            lk = (SLATE_XY[0], SLATE_XY[1] - 34)
        tl = _per(tilt, k, 8.0)
        ar = _per(arm, k, 16.0 + 6 * math.sin((0 if calm else t) * 0.9 + k))
        ld = _per(lid, k, _blink(t, k, calm))
        sp = speak.get(k) if speak else None
        out[k] = child(ink, t, cam, k, x, y, facing=fc, tilt=tl, arm=ar, look=lk, lid=ld, calm=calm, swim=0.25,
                       mouth_open=1.0 if sp and sp[1] > 0.05 else 0.0)
        if desks:
            desk(ink, cam, x + 12 * fc, y + 2, k)
        if sp:
            spoken.append((k, sp, fc))
    if teacher:
        tx, ty = TEACHER_XY
        sp = speak.get("T") if speak else None
        out["T"] = fish(ink, t, cam, tx, ty, "teacher", facing=_per(facing, "T", -1), tilt=_per(tilt, "T", 4.0),
                        arm=_per(arm, "T", 62 + 5 * math.sin((0 if calm else t) * 1.2)), hold="pointer",
                        look=_per(look_d, "T", SEATS[1]) if isinstance(look_d, dict) else (look_d or SEATS[1]), lid=_per(lid, "T", _blink(t, 11, calm)),
                        calm=calm, swim=0.2, mouth_open=1.0 if sp and sp[1] > 0.05 else 0.0)
        if sp:
            spoken.append(("T", sp, -1))
    for k, sp, fc in spoken:
        bubble(ink, t, cam, out[k]["mouth"], sp[0], grow=sp[1], progress=sp[2] if len(sp) > 2 else 1.0, pop=sp[3] if len(sp) > 3 else 0.0,
               side=fc, seed=k if k != "T" else 9, r=30 if k != "T" else 36, calm=calm, screen=True)
    return out


def _blink(t, k, calm=False):
    if calm:
        return 0.0
    ph = (t * 0.23 + k * 0.37) % 1.0
    return 1.0 if ph > 0.965 else 0.0


def child(ink, t, cam, k, x=None, y=None, **pose):
    """Fish child number k (0..7), anywhere: at world (x, y), or at its seat if they are left out. Keywords as
    fish(): facing, tilt, arm, look, hold, lid, swim, depth, calm, mouth_open. Child 0 is the jaw child.
    Its drawing is CHILD_DRAWS[k]."""
    if x is None:
        x, y = SEATS[k]
    return fish(ink, t, cam, x, y, "child", seed=k, **pose)


TOWNSFOLK = [   # (kind, x, y, facing, seed, depth)
    ("cook", 248, 804, 1, 0, 1.0), ("lady", 138, 812, 1, 1, 1.0), ("post", 306, 802, -1, 2, 1.0), ("towns", 906, 814, -1, 3, 1.0),
]


def townsfolk(ink, t, cam=None, look=None, calm=False, who=None, wave=None):
    """A few townsfolk on main street: the cook in the diner's door, a lady with a hat by the diner, the postfish
    going along behind the notice board, somebody in a hat by the last lamp. look = a WORLD point they all turn to
    (None: they mind their business). who = indices to draw (default all). wave = {index: arm degrees}.
    Returns [fish() points]."""
    cam = as_cam(cam)
    out = []
    tt = 0.0 if calm else t
    for q, (kind, x, y, fc, seed, dp) in enumerate(TOWNSFOLK):
        if who is not None and q not in who:
            out.append(None)
            continue
        if kind == "post":
            x = x + 26 * math.sin(tt * 0.21)                      # walking its round, a little
            fc = -1 if math.cos(tt * 0.21) < 0 else 1
        if look is not None:
            fc = 1 if look[0] >= x else -1
        ar = (wave or {}).get(q, 14 + 8 * math.sin(tt * 0.8 + q * 2))
        out.append(fish(ink, t, cam, x, y, kind, facing=fc, tilt=3.0, arm=ar, look=look, seed=seed, depth=dp, calm=calm,
                        swim=0.2, lid=_blink(t, q + 20, calm)))
    return out


# --------------------------------------------------------------- bubbles ---

def bubble(ink, t, cam, mouth, drawing="jaw", grow=1.0, progress=1.0, r=30.0, side=1, pop=0.0, rise=0.0, seed=0,
           calm=False, screen=False, alpha=1.0, tidy=False):
    """A fish speaking: a bubble with a picture in it, never a word. mouth = where it comes from (WORLD point, or a
    screen point with screen=True: fish()['mouth'] is a screen point). drawing = a name for picture(). grow 0..1
    blows it up from the mouth; progress 0..1 draws the picture stroke by stroke inside it; rise = world px it has
    floated up since; pop 0..1 bursts it. r = radius in world px. side +1 right of the mouth / -1 left.
    calm=True holds it dead still (under the ice). Returns the bubble's screen centre."""
    cam = as_cam(cam)
    z = cam.zoom
    mx, my = mouth if screen else cam.xy(*mouth)
    g = smooth(clamp(grow))
    if g <= 0.01:
        return (mx, my)
    tt = 0.0 if calm else t
    R = r * z * (0.25 + 0.75 * g)
    bob = 0.0 if calm else 2.0 * z * math.sin(tt * 1.6 + seed)
    cx = mx + side * (R * 0.7 + 8 * z) * g + 3 * z * math.sin(tt * 0.9 + seed * 2)
    cy = my - (R + 12 * z) * g - rise * z + bob
    # the little ones that lead from the mouth
    for q, f in enumerate((0.16, 0.42, 0.7)):
        if g < f * 0.8 or pop > 0.3:
            continue
        bx, by = lerp(mx, cx - side * R * 0.5, f), lerp(my - 2 * z, cy + R * 0.75, f) + (0 if calm else 1.5 * z * math.sin(tt * 3 + q))
        br = (1.8 + q * 1.6) * z
        ink.d.ellipse([bx - br, by - br, bx + br, by + br], fill=(220, 240, 232, 60), outline=(240, 250, 244, int(230 * alpha)), width=max(1, int(1.4 * z)))
    if pop >= 1:
        return (cx, cy)
    if pop > 0:                                                    # burst: the skin goes to drops flying outward
        rs = random.Random(seed + 3)
        for q in range(14):
            a = q / 14 * 2 * math.pi + rs.uniform(-0.2, 0.2)
            rr = R * (1 + pop * rs.uniform(0.3, 0.9))
            dr = (2.2 * (1 - pop) + 0.6) * z
            ink.d.ellipse([cx + rr * math.cos(a) - dr, cy + rr * math.sin(a) - dr, cx + rr * math.cos(a) + dr, cy + rr * math.sin(a) + dr],
                          fill=(236, 250, 244, int(230 * (1 - pop) * alpha)))
        if pop > 0.35:
            return (cx, cy)
    ss = 3
    S = int((R * 2 + 14) * ss)
    im, d = _layer((S, S))
    c = S / 2
    n = 48
    rim = []
    for q in range(n):
        a = q / n * 2 * math.pi
        wob = 1 + 0.02 * math.sin(3 * a + tt * 2.2 + seed) + 0.012 * math.sin(5 * a - tt * 3.1)
        rim.append((c + R * ss * wob * math.cos(a), c + R * ss * wob * math.sin(a)))
    d.polygon(rim, fill=(234, 240, 226, int(238 * (1 - pop))))
    d.line(rim + rim[:1], fill=(250, 255, 250, 255), width=max(2, int(1.9 * ss * max(0.8, z ** 0.5))))
    d.arc([c - R * ss * 0.86, c - R * ss * 0.86, c + R * ss * 0.86, c + R * ss * 0.86], 20, 80, fill=(120, 170, 170, 150), width=max(2, int(1.6 * ss)))
    if g > 0.55:
        picture(d, drawing, c, c + R * ss * 0.04, R * ss * 1.34, progress=progress, width=max(ss * 1.0, R * ss * 0.05), tidy=tidy, seed=seed)
    d.arc([c - R * ss * 0.8, c - R * ss * 0.8, c + R * ss * 0.8, c + R * ss * 0.8], 200, 262, fill=(255, 255, 255, 235), width=max(2, int(2.4 * ss)))
    d.ellipse([c - R * ss * 0.62, c - R * ss * 0.3, c - R * ss * 0.54, c - R * ss * 0.22], fill=(255, 255, 255, 235))
    im = im.resize((S // ss, S // ss), Image.LANCZOS)
    ink.paste(im, (cx - im.width / 2, cy - im.height / 2), alpha)
    return (cx, cy)


def thing(ink, cam, kind, x, y, angle=0.0, scale=1.0, screen=False):
    """What the digging turns up, lying on the gravel at world (x, y): 'boot' (an old boot, set politely aside),
    'spool' (the empty film spool the reel is wound on, much later), 'pin' (the board pin the dog lets fall)."""
    cam = as_cam(cam)
    z = (1.0 if screen else cam.zoom) * scale
    sx, sy = (x, y) if screen else cam.xy(x, y)
    a = math.radians(angle)

    def R(px, py):
        return (sx + (px * math.cos(a) + py * math.sin(a)) * z, sy + (-px * math.sin(a) + py * math.cos(a)) * z)

    lw = max(1, int(round(1.3 * z)))
    if kind == "boot":
        pts = [R(-13, 0), R(-13, -24), R(-11, -27), R(0, -27), R(1, -12), R(9, -10), R(16, -6), R(17, 0)]
        ink.d.polygon([(px + 2 * z, py + 2 * z) for px, py in pts], fill=(6, 20, 24, 90))
        ink.d.polygon(pts, fill=(84, 66, 50, 255))
        ink.d.line(pts + pts[:1], fill=LINE + (255,), width=lw)
        ink.d.line([R(-14, 0), R(18, 0)], fill=(40, 30, 24, 255), width=max(2, int(2.4 * z)))
        for q in range(3):
            ink.d.line([R(-3, -22 + q * 5), R(1, -21 + q * 5)], fill=(200, 184, 150, 255), width=max(1, int(z)))
        ink.d.line([R(2, -12), R(6, -20), R(3, -24)], fill=(200, 184, 150, 255), width=max(1, int(z)))
    elif kind == "spool":
        for dx in (-5, 5):
            c0 = R(dx, -9)
            ink.d.ellipse([c0[0] - 4 * z, c0[1] - 9 * z, c0[0] + 4 * z, c0[1] + 9 * z], fill=(150, 158, 156, 255), outline=LINE + (255,), width=lw)
            ink.d.ellipse([c0[0] - 1.3 * z, c0[1] - 2.6 * z, c0[0] + 1.3 * z, c0[1] + 2.6 * z], fill=(30, 46, 48, 255))
            if dx < 0:
                ink.d.polygon([R(-5, -12), R(5, -12), R(5, -6), R(-5, -6)], fill=(104, 112, 112, 255), outline=LINE + (255,))
    else:
        ink.d.line([R(0, 0), R(0, -7)], fill=(190, 196, 190, 255), width=max(1, int(1.2 * z)))
        c0 = R(0, -8)
        ink.d.ellipse([c0[0] - 2.2 * z, c0[1] - 2.2 * z, c0[0] + 2.2 * z, c0[1] + 2.2 * z], fill=(206, 60, 54, 255), outline=LINE + (255,))
    return (sx, sy)


# ----------------------------------------------------------------- stills ---

def _still(name, fn, t=1.0, boil=8):
    ink = Ink(t, int(t * FPS), (W, H), boil=boil)
    ink.paper()
    fn(ink, t)
    out = _HERE / f"town_{name}.png"
    ink.finish().save(out)
    print("wrote", out)


def _demo_wide(ink, t):
    cam = F_TOWN
    back(ink, t, cam)
    o = street(ink, t, cam, holes=3, smudges=1)
    making_place(ink, cam, 1.0)
    thing(ink, cam, "boot", 346, 842, 8)
    thing(ink, cam, "spool", 392, 806)
    school_class(ink, t, cam, speak={0: ("jaw", 1.0)})
    townsfolk(ink, t, cam)
    touch(ink, t, cam, 600, "muzzle")
    front(ink, t, cam)


def _demo_school(ink, t):
    cam = Cam.look(735, 716, 2.0)
    back(ink, t, cam)
    street(ink, t, cam, bell=22 * math.sin(t * 6))
    school_class(ink, t, cam, arm={3: 150})
    townsfolk(ink, t, cam)
    front(ink, t, cam)


def _demo_board(ink, t):
    cam = Cam.look(425, 742, 3.6)
    back(ink, t, cam)
    street(ink, t, cam, smudges=14, taken=(4,), pull=(0, 0.35))
    thing(ink, cam, "spool", 392, 806)
    front(ink, t, cam)


def _demo_class(ink, t):
    cam = Cam.look(716, 768, 2.5)
    back(ink, t, cam)
    street(ink, t, cam)
    school_class(ink, t, cam, speak={0: ("jaw", 1.0), 6: ("sub", 1.0, 0.7), 3: ("bowl_legs", 0.75)}, arm={0: 120, 3: 100, 5: 150})
    front(ink, t, cam)


def _demo_split(ink, t):
    cam = F_SPLIT
    ink.d.rectangle([0, 0, W, H], fill=(58, 46, 96, 255))
    back(ink, t, cam, sky=False, ice=1.0, cracks=[(600, 0.5)], calm=True)
    street(ink, t, cam, holes=40, calm=True)
    school_class(ink, t, cam, calm=True, look=(600, 400), tilt=-14)
    front(ink, t, cam, calm=True)
    touch(ink, t, cam, 600, "hoof", calm=True)
    grade(ink, cam, cold=1.0)


def _demo_last(ink, t):
    cam = F_LAST
    ink.d.rectangle([0, 0, W, H], fill=(40, 32, 76, 255))
    back(ink, t, cam, sky=False, night=0.6)
    door = (105, 300)
    street(ink, t, cam)
    for k, (x, y) in enumerate(((330, 600), (392, 652), (452, 590), (520, 640), (585, 588), (650, 646), (712, 600), (790, 640))):
        r = child(ink, t, cam, k, x, y + 4 * math.sin(t * 1.3 + k), facing=-1, tilt=38, look=door, arm=150 if k == 2 else 30, swim=0.5)
        if k == 6:
            bubble(ink, t, cam, r["mouth"], "bars", side=-1, screen=True, r=26)
    front(ink, t, cam)
    grade(ink, cam, night=0.6)


def _demo_dark(ink, t):
    cam = F_TOWN
    back(ink, t, cam, lamps=0.45)
    street(ink, t, cam, lamps=0.45, holes=374, smudges=131)
    front(ink, t, cam)


def _demo_pictures(ink, t):
    ink.d.rectangle([0, 0, W, H], fill=(22, 70, 78, 255))
    for q, nm in enumerate(DRAWINGS):
        bubble(ink, t, Cam(360), (60 + q * 185, 250), nm, r=78, seed=q, screen=True)
        page(ink, Cam(360), 110 + q * 185, 420, nm, angle=(-4, 3, -2, 5, -3)[q], size=150, screen=True, smudge=q)
    bubble(ink, t, Cam(360), (800, 520), "jaw", r=40, seed=3, screen=True, tidy=True, side=-1)


def _selftest():
    """MEASURED checks the representation supports (run with the stills)."""
    a, b = Cam(360, 0), Cam(360, 100)
    shifts = [a.xy(500, 700, d)[0] - b.xy(500, 700, d)[0] for d in (0.3, 0.45, 0.72, 1.0, 1.3)]
    assert all(x < y for x, y in zip(shifts, shifts[1:])), shifts              # nearer planes move more
    for cam in (F_PORCH, F_SPLIT, F_TOWN, F_LAST, Cam.look(425, 742, 3.6)):
        wx, wy = cam.world(*cam.xy(321.5, 654.25))
        assert abs(wx - 321.5) < 1e-6 and abs(wy - 654.25) < 1e-6
    assert (F_PORCH.surface(), F_SPLIT.surface(), F_TOWN.surface(), F_LAST.surface()) == (400, 150, 40, 250)
    assert len(HOLES) == 374 and all(300 <= hole_xy(k)[0] <= 440 for k in range(3))
    assert all(y > BED_Y for _, y, _, _ in HOLES)                              # every hole is in the gravel
    assert not any(596 < x < 850 and y < 842 for x, y, _, _ in HOLES)          # none under the desks
    D = _drawings()
    assert all(n in D for n in DRAWINGS)
    for n in D:
        pts = np.concatenate([p for p, _, _, _ in D[n]])
        assert np.abs(pts).max() <= 0.5001, n                                  # each drawing fits its unit box
    print("town self-test passed:", "parallax shifts for a 100 px pan", [round(v, 1) for v in shifts])


if __name__ == "__main__":
    _selftest()
    _still("wide", _demo_wide, 1.0)
    _still("school", _demo_school, 1.3)
    _still("board", _demo_board, 2.0)
    _still("class", _demo_class, 2.4)
    _still("split_ice", _demo_split, 3.0, boil=0)
    _still("last", _demo_last, 4.0)
    _still("lamps_coming_on", _demo_dark, 5.0)
    _still("pictures", _demo_pictures, 1.0)
