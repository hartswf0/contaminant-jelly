"""world.py · the shared pieces of class film c10 (porthole 10 · PA · "flapping Clam-Shell PA").

Everything here is HANDMADE in code, nothing is foraged: every creature and prop is a joint tree of
cut-paper pieces (each piece its own sheet with fibre, a lit and a dark cut edge and a shadow on the
piece beneath), the brass and the tin wall are turned / pressed from their own height profiles, and
the pilot's drawing is a list of pencil strokes traced by eye from the child's sheet.

Every public function takes a `target` first: the kit's Ink, or any PIL image (RGB or RGBA).
See WORLD.md for the list, arguments, coordinates and example calls.

    python3 films/swarm/c10/world.py <out_dir>      # writes test stills of every piece
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

FILMS = Path(__file__).resolve().parents[2]
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import W, H, FPS, font, clamp, ramp, smooth, ease, lerp  # noqa: E402
import kit_anim as KA  # noqa: E402

PORTHOLE = 10

# ---------------------------------------------------------------- palette ---
PAL = dict(
    paper=(243, 239, 228), page=(250, 247, 239), ink=(36, 32, 29), graphite=(58, 58, 66),
    table=(96, 72, 50),
    water_top=(98, 158, 140), water=(50, 112, 106), water_deep=(20, 62, 70),
    weed_far=(46, 98, 92), weed_mid=(70, 122, 84), weed_dark=(16, 44, 44),
    rock=(70, 98, 86), moss=(104, 132, 76), gravel=(64, 92, 78),
    brass=(188, 150, 70), brass_lit=(232, 202, 122), brass_dark=(104, 76, 30),
    tin=(176, 186, 182), tin_lid=(158, 170, 168), tin_dark=(110, 122, 120), rust=(150, 110, 78),
    cabin=(74, 60, 46), lamp=(255, 206, 130),
    turkey_body=(72, 52, 38), turkey_bronze=(186, 140, 76), turkey_skin=(150, 178, 196),
    turkey_red=(198, 72, 62), turkey_dkred=(150, 44, 44), turkey_beak=(222, 180, 88),
    trout_back=(62, 88, 92), trout_belly=(228, 152, 86), trout_fin=(196, 98, 58),
    brick=(152, 80, 62), mortar=(156, 148, 132),
    shell=(234, 226, 206), shell_rib=(196, 182, 156), nacre=(206, 216, 214),
    fry=(232, 186, 84), fry_dark=(190, 136, 48),
    green=(64, 160, 92), red=(206, 62, 54), blue=(62, 110, 196), pink=(236, 128, 170), amber=(232, 164, 48),
    ivory=(240, 234, 216), badge=(26, 26, 32), white=(250, 250, 246),
)
BUTTONS = {"triangle": "green", "circle": "red", "cross": "blue", "square": "pink", "hexagon": "amber"}
KIND = {1: "Probable", 2: "Plausible", 3: "Preposterous", 4: "Probable", 5: "Plausible", 6: "Preposterous"}


# ------------------------------------------------------------------ basics ---
def _img(target):
    return target.img if hasattr(target, "img") else target


def _comp(target, sp, xy):
    """Composite an RGBA sprite on an Ink / RGB / RGBA image; tolerant of hanging off the edge."""
    img = _img(target)
    x, y = int(round(xy[0])), int(round(xy[1]))
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(sp.size[0], img.size[0] - x), min(sp.size[1], img.size[1] - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0) + sp.size:
        sp = sp.crop((x0, y0, x1, y1))
    if img.mode == "RGBA":
        img.alpha_composite(sp, (x + x0, y + y0))
    else:
        img.paste(sp, (x + x0, y + y0), sp)


def vnoise(shape, sx, sy=None, seed=0, octaves=1):
    sy = sx if sy is None else sy
    h, w = shape
    rs = np.random.RandomState(seed)
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        fx, fy = max(1.0, sx / 2 ** o), max(1.0, sy / 2 ** o)
        g = rs.rand(int(h / fy) + 3, int(w / fx) + 3).astype(np.float32)
        out += amp * (np.asarray(Image.fromarray(g, "F").resize((w, h), Image.BICUBIC), np.float32) - 0.5) * 2
        tot += amp
        amp *= 0.5
    return out / tot


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def blur_arr(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255


def shadow_of(alpha_img, blur, strength, color=(8, 10, 12)):
    a = alpha_img.filter(ImageFilter.GaussianBlur(float(blur))).point(lambda v: int(v * float(strength)))
    sh = Image.new("RGBA", alpha_img.size, tuple(color) + (0,))
    sh.putalpha(a)
    return sh


def catmull(pts, per=10, closed=False):
    pts = [np.array(p, np.float32) for p in pts]
    if len(pts) == 2:
        return [tuple(pts[0] + (pts[1] - pts[0]) * k / per) for k in range(per + 1)]
    P = [pts[-1]] + pts + [pts[0], pts[1]] if closed else [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            u = k / per
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)))
    out.append(tuple(P[-2]))
    return out


def dk(c, f=0.72):
    return tuple(int(v * f) for v in c[:3])


def lt(c, f=1.22):
    return tuple(min(255, int(v * f)) for v in c[:3])


def rrect(x0, y0, x1, y1, r, n=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def circ(cx, cy, r, n=28, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def xf(ang, dx, dy):
    """A point mapper: rotate by ang degrees, then move by (dx, dy)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return lambda x, y: (dx + x * ca - y * sa, dy + x * sa + y * ca)


def Tm(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)


def Rm(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]], np.float64)


def Sm(sx, sy=None):
    return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], np.float64)


def apply(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return (float(v[0]), float(v[1]))


# --------------------------------------------------------------- cut paper ---
_FIBRE = None


def fibre_tex():
    global _FIBRE
    if _FIBRE is None:
        n = 900
        _FIBRE = (0.5 * vnoise((n, n), 1.6, None, 81) + 0.45 * vnoise((n, n), 22, 1.3, 82) + 0.35 * vnoise((n, n), 1.3, 18, 83)
                  + 0.5 * vnoise((n, n), 60, None, 84, 2)).astype(np.float32)
    return _FIBRE


class Sprite:
    def __init__(self, img, ox, oy):
        self.img, self.ox, self.oy = img, ox, oy
        self._half = None

    def pick(self, sc):
        if sc < 0.56 and min(self.img.size) >= 8:
            if self._half is None:
                self._half = self.img.resize((max(1, self.img.size[0] // 2), max(1, self.img.size[1] // 2)), Image.LANCZOS)
            return self._half, self.img.size[0] / self._half.size[0], self.img.size[1] / self._half.size[1]
        return self.img, 1.0, 1.0


def cut(pts, color, deco=None, curve=True, seed=0, per=8, grain=0.075, edge=1.0):
    """Cut one piece of coloured paper along pts (design coords). deco(d, L, S) may print on it."""
    P = catmull(pts, per, closed=True) if curve else [tuple(p) for p in pts]
    xs, ys = [p[0] for p in P], [p[1] for p in P]
    pad = 3
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    w, h = int(math.ceil(max(xs))) - x0 + pad, int(math.ceil(max(ys))) - y0 + pad
    S = 3
    m = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m).polygon([((x - x0) * S, (y - y0) * S) for x, y in P], fill=255)
    col = Image.new("RGB", (w * S, h * S), tuple(int(c) for c in color[:3]))
    if deco:
        deco(ImageDraw.Draw(col), lambda x, y: ((x - x0) * S, (y - y0) * S), S)
    m = m.resize((w, h), Image.LANCZOS)
    col = col.resize((w, h), Image.LANCZOS)
    a = np.asarray(col, np.float32).copy()
    al = np.asarray(m, np.float32) / 255
    F = fibre_tex()
    oy_, ox_ = ((seed * 131) % (900 - h) if h < 900 else 0), ((seed * 57) % (900 - w) if w < 900 else 0)
    fb = F[oy_:oy_ + h, ox_:ox_ + w]
    if fb.shape != (h, w):
        fb = np.resize(fb, (h, w))
    a *= (1 + grain * fb)[..., None]
    hl = np.clip(al - np.roll(al, (1, 1), (0, 1)), 0, 1)
    dkk = np.clip(al - np.roll(al, (-1, -1), (0, 1)), 0, 1)
    a += edge * (70 * hl - 60 * dkk)[..., None]
    out = np.dstack([np.clip(a, 0, 255), al * 255]).astype(np.uint8)
    return Sprite(Image.fromarray(out, "RGBA"), x0, y0)


def compose(sprites, shadow=(1.6, 2.2, 1.4, 0.34)):
    """Glue several cut pieces into one sprite (each casting on the ones below)."""
    x0 = min(s.ox for s in sprites) - 4
    y0 = min(s.oy for s in sprites) - 4
    x1 = max(s.ox + s.img.size[0] for s in sprites) + 6
    y1 = max(s.oy + s.img.size[1] for s in sprites) + 6
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    for k, s in enumerate(sprites):
        if k and shadow:
            sh = shadow_of(s.img.getchannel("A"), shadow[2], shadow[3])
            tmp = Image.new("RGBA", im.size, (0, 0, 0, 0))
            tmp.alpha_composite(sh, (int(s.ox - x0 + shadow[0]), int(s.oy - y0 + shadow[1])))
            tmp.putalpha(ImageChops.multiply(tmp.getchannel("A"), im.getchannel("A")))
            im.alpha_composite(tmp)
        im.alpha_composite(s.img, (s.ox - x0, s.oy - y0))
    return Sprite(im, x0, y0)


def draw_sprite(target, spr, M, shadow=(2.0, 2.8, 1.5, 0.36)):
    """Lay a Sprite on the target under the affine M (design px -> target px), with its shadow."""
    det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
    sc = math.sqrt(abs(det))
    if sc < 1e-3:
        return
    layer = _img(target)
    img, kx, ky = spr.pick(sc)
    w, h = img.size
    cs = M @ np.array([[spr.ox, spr.ox + w * kx, spr.ox + w * kx, spr.ox], [spr.oy, spr.oy, spr.oy + h * ky, spr.oy + h * ky], [1, 1, 1, 1]])
    x0, y0 = int(math.floor(cs[0].min())) - 1, int(math.floor(cs[1].min())) - 1
    x1, y1 = int(math.ceil(cs[0].max())) + 1, int(math.ceil(cs[1].max())) + 1
    x0c, y0c, x1c, y1c = max(x0, -40), max(y0, -40), min(x1, layer.size[0] + 40), min(y1, layer.size[1] + 40)
    if x1c <= x0c or y1c <= y0c:
        return
    Mi = np.linalg.inv(M)
    co = (Mi[0, 0] / kx, Mi[0, 1] / kx, (Mi[0, 0] * x0c + Mi[0, 1] * y0c + Mi[0, 2] - spr.ox) / kx,
          Mi[1, 0] / ky, Mi[1, 1] / ky, (Mi[1, 0] * x0c + Mi[1, 1] * y0c + Mi[1, 2] - spr.oy) / ky)
    out = img.transform((x1c - x0c, y1c - y0c), Image.AFFINE, co, resample=Image.BICUBIC)
    if shadow:
        sh = shadow_of(out.getchannel("A"), max(0.6, shadow[2] * sc), shadow[3])
        _comp(layer, sh, (x0c + shadow[0] * sc, y0c + shadow[1] * sc))
    _comp(layer, out, (x0c, y0c))


class Puppet:
    """A joint tree. Every part is cut in one shared design frame; a part turns about its pivot and
    carries its children with it. A pose maps part -> angle, or (angle, dx, dy[, sx, sy])."""

    def __init__(self):
        self.parts = {}
        self.order = []

    def add(self, name, spr, pivot=(0, 0), parent=None, z=0.0):
        self.parts[name] = dict(spr=spr, pivot=pivot, parent=parent, z=z)
        self.order = sorted(self.parts, key=lambda k: self.parts[k]["z"])

    def mats(self, pose, M_root):
        out = {}

        def get(name):
            if name in out:
                return out[name]
            p = self.parts[name]
            Mp = get(p["parent"]) if p["parent"] else M_root
            v = pose.get(name, 0.0)
            if not isinstance(v, tuple):
                v = (v,)
            dx, dy = (v[1], v[2]) if len(v) > 2 else (0.0, 0.0)
            sx, sy = (v[3], v[4]) if len(v) > 4 else (1.0, 1.0)
            px, py = p["pivot"]
            out[name] = Mp @ Tm(px + dx, py + dy) @ Rm(v[0]) @ Sm(sx, sy) @ Tm(-px, -py)
            return out[name]
        for n in self.parts:
            get(n)
        return out

    def draw(self, target, pose, M_root, sprites=None, skip=(), shadow=(2.0, 2.8, 1.5, 0.36)):
        ms = self.mats(pose, M_root)
        for n in self.order:
            if n in skip:
                continue
            spr = (sprites or {}).get(n) or self.parts[n]["spr"]
            if spr is not None:
                draw_sprite(target, spr, ms[n], shadow)
        return ms


def _group(target, x, y, half, draw_fn, shade=0.0, alpha=1.0, drop=(6, 9, 7, 0.30), tint=(14, 18, 20)):
    """Draw a whole puppet on its own sheet (so it can be shaded and cast one shadow), then lay it down.
    draw_fn(layer, ox, oy) draws with the origin shifted by (ox, oy)."""
    half = int(half)
    n = half * 2
    layer = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ox, oy = int(half - x), int(half - y)
    res = draw_fn(layer, ox, oy)
    if shade > 0:
        a = layer.getchannel("A")
        layer = Image.blend(layer.convert("RGB"), Image.new("RGB", layer.size, tint), clamp(shade)).convert("RGBA")
        layer.putalpha(a)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    if drop:
        _comp(target, shadow_of(layer.getchannel("A"), drop[2], drop[3] * alpha), (-ox + drop[0], -oy + drop[1]))
    _comp(target, layer, (-ox, -oy))
    return res


# ================================================================== TURKEY
# Design frame 320 x 400, facing LEFT. Body centre (175, 250). Feet at y ~ 392, crown at y ~ 60.
TURKEY_C = (175, 250)
MOODS = ("calm", "look", "freak", "panic", "wave", "slump", "gasp", "cheer")


@lru_cache(None)
def _turkey():
    P = Puppet()
    body, bronze = PAL["turkey_body"], PAL["turkey_bronze"]
    skin, red, dkred = PAL["turkey_skin"], PAL["turkey_red"], PAL["turkey_dkred"]
    # --- tail fan: nine barred feathers, each on its own pin at the rump
    T = xf(0, 228, 262)
    for k in range(9):
        def deco(d, L, S, k=k):
            for j in range(8):
                yb = -24 - j * 12
                d.line([L(*T(-22, yb)), L(*T(22, yb - 4))], fill=(44, 30, 22), width=2 * S)
            d.polygon([L(*T(-26, -116)), L(*T(26, -116)), L(*T(26, -134)), L(*T(-26, -134))], fill=(26, 20, 18))
            d.polygon([L(*T(-26, -134)), L(*T(26, -134)), L(*T(26, -162)), L(*T(-26, -162))], fill=(226, 200, 152))
            d.line([L(*T(0, 0)), L(*T(0, -150))], fill=(64, 42, 28), width=S)
        pts = [T(*p) for p in [(-8, 0), (-15, -70), (-21, -125), (-12, -151), (12, -151), (21, -125), (15, -70), (8, 0)]]
        P.add(f"tf{k}", cut(pts, (118, 80, 46), deco, per=6, seed=100 + k), (228, 262), "body", 0.1 + 0.01 * (4 - abs(k - 4)))

    # --- wings (the far one is the same cut, darker)
    def wing(dx, dy, shade, seed):
        Wg = xf(26, dx, dy)

        def deco(d, L, S):
            for k, x in enumerate(range(14, 156, 8)):      # barred flight feathers
                d.line([L(*Wg(x, 6)), L(*Wg(x - 8, 46))], fill=(238, 230, 208) if k % 2 else (36, 30, 28), width=4 * S)
            cov = catmull([Wg(*p) for p in [(-10, -16), (40, -26), (96, -18), (136, 4), (104, 14), (52, 14), (2, 12)]], 8, closed=True)
            d.polygon([L(*p) for p in cov], fill=dk(bronze, 0.62 * shade))
            for row in range(4):
                for col in range(10):
                    x, y = 6 + col * 14 + (row % 2) * 7, -18 + row * 9
                    d.pieslice([L(*Wg(x - 9, y - 9)), L(*Wg(x + 9, y + 9))], 20, 200, fill=dk(bronze, (0.5 + 0.08 * row) * shade), outline=(40, 28, 20), width=S)
            d.line([L(*p) for p in catmull([Wg(*p) for p in [(2, 12), (52, 15), (104, 15), (138, 6)]], 8)], fill=(30, 22, 18), width=2 * S)
        pts = [Wg(*p) for p in [(-10, -16), (40, -26), (96, -18), (136, 4), (150, 30), (124, 38), (86, 42), (40, 36), (2, 20)]]
        return cut(pts, dk((92, 70, 50), shade), deco, per=7, seed=seed)
    P.add("wing_far", wing(140, 214, 0.72, 121), (140, 214), "body", 1.2)
    P.add("wing", wing(150, 222, 1.0, 122), (150, 222), "body", 8)

    # --- legs
    def leg(hx, hy, seed, shade):
        Lg = xf(0, hx, hy)
        pts = [Lg(*p) for p in [(-4, 0), (4, 0), (4, 54), (15, 62), (14, 69), (2, 63), (-5, 66), (-27, 72), (-29, 66), (-5, 55)]]

        def deco(d, L, S):
            for j in range(7):
                d.line([L(*Lg(-4, 8 + j * 7)), L(*Lg(4, 8 + j * 7))], fill=dk((196, 134, 124), 0.8 * shade), width=S)
        return cut(pts, dk((196, 134, 124), shade), deco, curve=False, seed=seed)
    P.add("leg_far", leg(190, 322, 131, 0.75), (190, 322), "body", 1.5)
    P.add("leg", leg(152, 322, 132, 1.0), (152, 322), "body", 2)

    # --- body: an egg of layered feather scallops
    def body_deco(d, L, S):
        rs = random.Random(7)
        for row in range(13):
            for col in range(14):
                x, y = 88 + col * 14 + (row % 2) * 7, 172 + row * 13
                c = (92 + rs.randint(-8, 8), 66 + rs.randint(-6, 6), 44) if row > 2 else (70, 92, 70)
                d.pieslice([L(x - 10, y - 10), L(x + 10, y + 10)], 0, 180, fill=c, outline=(38, 26, 20), width=S)
                d.arc([L(x - 8, y - 4), L(x + 8, y + 9)], 20, 160, fill=bronze, width=S)
        breast = catmull([(96, 236), (112, 200), (140, 196), (150, 250), (146, 300), (120, 318), (104, 296)], 8, closed=True)
        d.polygon([L(*p) for p in breast], fill=(52, 38, 30))
        for row in range(9):
            for col in range(5):
                x, y = 104 + col * 11 + (row % 2) * 5, 206 + row * 13
                d.arc([L(x - 8, y - 6), L(x + 8, y + 8)], 20, 160, fill=(120, 88, 54), width=S)
    P.add("body", cut([(94, 238), (108, 192), (150, 166), (202, 170), (246, 200), (264, 250), (246, 300), (202, 330), (150, 332), (110, 306)],
                      body, body_deco, seed=110), TURKEY_C, None, 3)
    P.add("beard", cut([(117, 262), (126, 262), (125, 312), (115, 314)], (30, 24, 22), curve=False, seed=111), (121, 263), "body", 3.5)

    # --- neck and head
    def neck_deco(d, L, S):
        for k in range(30):
            x, y = 88 + (k * 37) % 50, 112 + (k * 53) % 112
            d.ellipse([L(x - 6, y - 5), L(x + 6, y + 5)], fill=(218, 100, 88) if k % 3 else dkred)
        d.line([L(*p) for p in catmull([(126, 140), (132, 186), (142, 226)], 8)], fill=dk(red, 0.7), width=2 * S)
    P.add("neck", cut([(98, 236), (88, 182), (84, 136), (92, 112), (118, 108), (126, 140), (132, 186), (144, 230)], red, neck_deco, seed=112), (120, 226), "body", 4)

    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(76, 76), (96, 64), (118, 70), (112, 80), (84, 84)], 8, closed=True)], fill=(176, 200, 216))
        for k in range(9):
            x, y = 104 + (k * 29) % 20, 94 + (k * 17) % 18
            d.ellipse([L(x - 3, y - 3), L(x + 3, y + 3)], fill=(126, 154, 178))
    P.add("head", cut([(72, 96), (76, 74), (94, 62), (116, 66), (126, 84), (122, 106), (104, 116), (84, 112)], skin, head_deco, seed=113), (106, 112), "neck", 5)
    P.add("wattle", cut([(84, 104), (104, 104), (110, 134), (98, 160), (82, 142)], red, seed=114), (94, 106), "head", 5.2)
    P.add("beak2", cut([(78, 98), (46, 103), (78, 107)], dk(PAL["turkey_beak"], 0.85), curve=False, seed=115), (78, 101), "head", 5.4)
    P.add("beak", cut([(76, 84), (38, 99), (78, 99)], PAL["turkey_beak"], curve=False, seed=116), (78, 92), "head", 5.6)

    def eye_deco(d, L, S):
        d.ellipse([L(91, 74), L(111, 94)], fill=(246, 242, 228))
    P.add("eye", cut(circ(101, 84, 12.5), (120, 150, 176), eye_deco, curve=False, seed=117), (101, 84), "head", 6)

    def pup_deco(d, L, S):
        d.ellipse([L(96.5, 81), L(99, 83.5)], fill=(244, 244, 236))
    P.add("pupil", cut(circ(99, 85, 6.0, 20), (20, 20, 22), pup_deco, curve=False, seed=118, edge=0.4), (99, 85), "eye", 6.2)
    P.add("lid", cut([(87, 85), (89, 73), (101, 69), (113, 73), (115, 85)], dk(skin, 0.9), per=5, seed=119), (101, 74), "eye", 6.3)
    P.add("snood", cut([(74, 72), (86, 70), (84, 92), (72, 122), (62, 118), (68, 92)], dkred, seed=120), (80, 74), "head", 6.6)
    return P


@lru_cache(None)
def _loose_feather():
    def deco(d, L, S):
        for j in range(5):
            d.line([L(-7, -8 - j * 7), L(7, -10 - j * 7)], fill=(44, 30, 22), width=2 * S)
        d.line([L(0, 0), L(0, -46)], fill=(230, 214, 180), width=S)
    return cut([(-2, 0), (-7, -20), (-8, -40), (0, -50), (8, -40), (7, -20), (2, 0)], (128, 90, 54), deco, per=6, seed=140)


def turkey_pose(mood="calm", t=0.0, look=(0.0, 0.0)):
    """Pose for a mood at time t. Returns (pose dict, (dx, dy, lean_degrees))."""
    s = math.sin
    tw = 2 * math.pi * t
    blink = 1.0 if (t * 0.37 + 0.2) % 1.0 < 0.04 else 0.0
    spread, wing, wing_far, neck, head, beak, snood, wattle = 0.30, 0.0, 0.0, 2.5 * s(t * 1.3), 3 * s(t * 0.9 + 1), 2.0, 2 * s(t * 1.1), 3 * s(t * 1.7)
    eye, pup, lid, legs, root = 1.0, 1.0, -11.0 + 11.0 * blink, (0.0, 0.0), (0.0, 1.5 * s(t * 1.6), 0.0)
    if mood == "look":
        neck, head, spread = -14 + 2 * s(t * 1.3), -8 + 3 * s(t * 0.9), 0.38
        root = (0, 1.5 * s(t * 1.6), -3)
    elif mood == "freak":       # wings beating out of step, fan snapped open, head whipping, beak wide
        wing = -96 + 44 * s(tw * 5.0)
        wing_far = -84 + 44 * s(tw * 5.0 + 2.2)
        spread = 1.0 + 0.06 * s(tw * 9)
        neck = -8 + 10 * s(tw * 2.6)
        head = 14 * s(tw * 5.2 + 1)
        beak, snood, wattle = 26 + 8 * s(tw * 6), 26 * s(tw * 5.2), 30 * s(tw * 5.2 - 1)
        eye, pup, lid = 1.28, 0.55, -14.0
        legs = (22 * s(tw * 4), -22 * s(tw * 4))
        root = (4 * s(tw * 7.3), -8 * abs(s(tw * 4)), 5 * s(tw * 2.6))
    elif mood == "panic":       # wings clapped over the head, shivering, eyes darting
        dart = 1 if int(t * 2.5) % 2 else -1
        wing = -150 + 5 * s(tw * 11)
        wing_far = -138 + 5 * s(tw * 11 + 1)
        spread = 0.8
        neck = 16 + 2 * s(tw * 11)
        head = 8 * dart + 2 * s(tw * 11)
        beak, snood, wattle = 9, 8 * s(tw * 11), 10 * s(tw * 11)
        eye, pup, lid = 1.2, 0.7, -14.0
        look = (2.2 * dart, 0.5)
        root = (2.0 * s(tw * 11), 10, 4)
    elif mood == "wave":
        wing = -112 + 26 * s(tw * 1.7)
        neck, head, beak = -6 + 2 * s(t * 1.3), -6 + 4 * s(tw * 1.7), 9
        spread = 0.5
    elif mood == "slump":
        neck, head, spread, wing, wing_far = 26, 16, 0.08, 10, 8
        lid, beak, wattle = -4.5, 0, 2 * s(t)
        root = (0, 10, 6)
    elif mood == "gasp":        # the air running out: slow wide breaths
        br = 0.5 + 0.5 * s(tw * 0.7)
        neck, head, beak = -12 * br + 6, -10 * br, 6 + 26 * br
        lid, spread = -6.5, 0.2
        wing, wing_far = -10 * br, -8 * br
        root = (0, 6 - 6 * br, 3)
    elif mood == "cheer":
        wing = -70 + 50 * s(tw * 2.0)
        wing_far = -70 + 50 * s(tw * 2.0 + math.pi)
        spread, beak = 0.85, 12
        head = 10 * s(tw * 2.0)
        legs = (14 * s(tw * 2.0), -14 * s(tw * 2.0))
        root = (0, -10 * abs(s(tw * 2.0)), 4 * s(tw * 2.0))
    pose = {"wing": wing, "wing_far": wing_far, "neck": neck, "head": head, "beak": beak * 0.45, "beak2": -beak * 0.55, "snood": snood, "wattle": wattle,
            "eye": (0.0, 0.0, 0.0, eye, eye), "pupil": (0.0, look[0], look[1], pup / eye, pup / eye), "lid": (0.0, 0.0, lid),
            "leg": legs[0], "leg_far": legs[1], "beard": 4 * s(t * 1.9) + root[2]}
    for k in range(9):
        pose[f"tf{k}"] = 38 + (k - 4) * lerp(4.5, 21.5, clamp(spread, 0, 1.1)) + (1.5 * s(t * 2.1 + k) if mood != "freak" else 4 * s(tw * 9 + k))
    return pose, root


def turkey(target, x, y, scale=1.0, mood="calm", t=0.0, flip=False, look=(0.0, 0.0), shade=0.0, alpha=1.0, feathers=None, pose=None, drop=True):
    """Turkey, cut paper, body centre at (x, y). Design faces left; flip=True faces right.
    mood: calm, look, freak, panic, wave, slump, gasp, cheer. `pose` (dict) overrides single joints.
    Returns screen points: head, beak, eye, wing_tip, feet, crown."""
    P = _turkey()
    ps, root = turkey_pose(mood, t, look)
    if pose:
        ps.update(pose)
    fx = -1.0 if flip else 1.0
    feathers = (mood == "freak") if feathers is None else feathers

    def draw(layer, ox, oy):
        M = Tm(x + ox + root[0] * scale, y + oy + root[1] * scale) @ Sm(scale * fx, scale) @ Rm(root[2]) @ Tm(-TURKEY_C[0], -TURKEY_C[1])
        ms = P.draw(layer, ps, M)
        if feathers:
            fs = _loose_feather()
            for k in range(6):
                u = (t * 0.55 + k * 0.173) % 1.0
                a = k * 1.05 + 0.4
                fxx = (math.cos(a) * (60 + 150 * u)) + 20 * math.sin(t * 3 + k)
                fyy = -120 * math.sin(math.pi * min(1, u * 1.4)) + 150 * u * u + math.sin(a) * 40
                Mf = Tm(x + ox + fxx * scale, y + oy + (fyy - 30) * scale) @ Rm(360 * u * (1 if k % 2 else -1) + k * 50) @ Sm(scale * (0.8 + 0.1 * k))
                draw_sprite(layer, fs, Mf)
        return ms
    half = int(290 * scale + 20)
    ms = _group(target, x, y, half, draw, shade, alpha, (6 * scale, 9 * scale, 6 * scale, 0.30) if drop else None)

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    return {"head": pt("head", (98, 90)), "beak": pt("beak", (40, 99)), "eye": pt("eye", (101, 84)), "wing_tip": pt("wing", xf(26, 150, 222)(146, 30)),
            "feet": pt("body", (165, 392)), "crown": pt("head", (96, 62))}


# =================================================================== TROUT
# Design frame faces LEFT, 296 x 150; anchor = body centre (120, 62); mouth at (5, 69).
TROUT_VARIANTS = [
    dict(back=(62, 88, 92), belly=(228, 152, 86), fin=(196, 98, 58), head=(54, 78, 84), spot=(226, 214, 160), cheek=(96, 122, 120), red=(206, 76, 60)),
    dict(back=(74, 96, 78), belly=(236, 176, 104), fin=(206, 116, 62), head=(64, 86, 72), spot=(232, 222, 170), cheek=(110, 130, 112), red=(210, 84, 64)),
    dict(back=(56, 76, 96), belly=(222, 138, 92), fin=(186, 88, 66), head=(48, 66, 88), spot=(220, 212, 176), cheek=(92, 112, 132), red=(200, 70, 70)),
    dict(back=(84, 98, 70), belly=(240, 190, 120), fin=(214, 130, 60), head=(72, 88, 62), spot=(236, 226, 168), cheek=(120, 132, 100), red=(212, 90, 60)),
]


@lru_cache(None)
def _trout(kind=0):
    pal = TROUT_VARIANTS[kind % len(TROUT_VARIANTS)]
    seed = 200 + kind * 20
    rs = random.Random(seed)
    body_pts = [(2, 63), (18, 41), (50, 25), (100, 14), (150, 16), (195, 30), (228, 47), (242, 55), (242, 71), (226, 81), (190, 97), (145, 107), (95, 105), (50, 93), (18, 79)]

    def body_deco(d, L, S):
        for row in range(11):
            for col in range(30):
                x, y = 60 + col * 7 + (row % 2) * 3.5, 10 + row * 9
                d.arc([L(x - 5, y - 5), L(x + 5, y + 5)], 20, 160, fill=dk(pal["back"], 0.86), width=S)
        belly = catmull([(20, 72), (60, 70), (110, 70), (160, 67), (205, 64), (246, 62), (246, 80), (226, 90), (190, 104), (145, 114), (95, 112), (50, 100), (10, 86)], 8, closed=True)
        d.polygon([L(*p) for p in belly], fill=pal["belly"])
        d.line([L(*p) for p in catmull([(20, 72), (60, 70), (110, 70), (160, 67), (205, 64), (246, 62)], 8)], fill=dk(pal["belly"], 0.8), width=S)
        for row in range(5):
            for col in range(30):
                x, y = 40 + col * 7 + (row % 2) * 3.5, 74 + row * 8
                d.arc([L(x - 5, y - 5), L(x + 5, y + 5)], 20, 160, fill=dk(pal["belly"], 0.9), width=S)
        for k in range(9):      # the brook trout's worm-track back
            x = 74 + k * 18 + rs.uniform(-4, 4)
            d.line([L(*p) for p in catmull([(x, 22 + rs.uniform(-3, 3)), (x + 8, 17), (x + 14, 24), (x + 22, 19)], 6)], fill=lt(pal["back"], 1.5), width=2 * S)
        for _ in range(44):
            x, y = rs.uniform(70, 238), rs.uniform(28, 66)
            r = rs.uniform(1.6, 3.4)
            if rs.random() < 0.28:
                d.ellipse([L(x - r - 1.6, y - r - 1.6), L(x + r + 1.6, y + r + 1.6)], fill=(90, 130, 170))
                d.ellipse([L(x - r * 0.7, y - r * 0.7), L(x + r * 0.7, y + r * 0.7)], fill=pal["red"])
            else:
                d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=pal["spot"])

    def rays(hx, hy, tips, col, lead=None):
        def deco(d, L, S):
            for (tx, ty) in tips:
                d.line([L(hx, hy), L(tx, ty)], fill=col, width=S)
            if lead:        # the brook trout's white-edged lower fins
                d.line([L(*lead[0]), L(*lead[1])], fill=(244, 240, 226), width=4 * S)
                d.line([L(lead[0][0] + 4, lead[0][1]), L(lead[1][0] + 4, lead[1][1])], fill=(30, 28, 28), width=2 * S)
        return deco
    fin = pal["fin"]
    P = Puppet()
    P.add("body", cut(body_pts, pal["back"], body_deco, seed=seed), (120, 62), None, 2)
    P.add("tail", cut([(226, 50), (262, 22), (294, 12), (282, 60), (296, 110), (262, 100), (226, 74)], dk(pal["back"], 1.1),
                      rays(230, 62, [(262 + k * 4, 16 + k * 11.5) for k in range(9)], dk(pal["back"], 0.7)), per=5, seed=seed + 1), (236, 62), "body", 0)
    P.add("dorsal", cut([(98, 20), (116, -16), (150, -22), (170, -4), (164, 22)], lt(pal["back"], 1.2),
                        rays(130, 24, [(112 + k * 9, -12 - (k % 3) * 3) for k in range(7)], dk(pal["back"], 0.7)), per=5, seed=seed + 2), (132, 20), "body", 1)
    P.add("adipose", cut([(198, 34), (210, 18), (222, 36)], dk(fin, 0.9), per=5, seed=seed + 3), (208, 34), "body", 1)
    P.add("anal", cut([(170, 98), (188, 128), (212, 120), (208, 90)], fin, rays(186, 100, [(186 + k * 6, 124 - k) for k in range(5)], dk(fin), ((171, 99), (188, 127))), per=5, seed=seed + 4), (188, 100), "body", 1)
    P.add("pelvic", cut([(118, 104), (126, 132), (152, 128), (148, 102)], fin, rays(132, 106, [(128 + k * 6, 128) for k in range(5)], dk(fin), ((119, 105), (126, 131))), per=5, seed=seed + 5), (132, 106), "body", 1)

    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(44, 60), (62, 52), (76, 66), (64, 84), (46, 80)], 8, closed=True)], fill=pal["cheek"])
        d.arc([L(40, 22), L(82, 98)], -62, 70, fill=dk(pal["head"], 0.6), width=2 * S)
        d.ellipse([L(11, 50), L(14, 53)], fill=dk(pal["head"], 0.5))
        d.polygon([L(*p) for p in catmull([(0, 70), (30, 72), (60, 86), (56, 100), (16, 84)], 8, closed=True)], fill=pal["belly"])
    P.add("head", cut([(2, 63), (18, 41), (50, 25), (66, 20), (78, 40), (82, 62), (74, 86), (57, 96), (48, 93), (18, 79)], pal["head"], head_deco, seed=seed + 7), (70, 58), "body", 4)
    P.add("jaw", cut([(3, 67), (22, 69), (40, 71), (46, 82), (24, 83), (7, 76)], lt(pal["belly"], 0.97), per=5, seed=seed + 8), (40, 74), "head", 5)

    def eye_deco(d, L, S):
        d.ellipse([L(27, 40), L(43, 56)], fill=(232, 222, 190))
    P.add("eye", cut(circ(35, 48, 10.5), (186, 150, 70), eye_deco, curve=False, seed=seed + 9), (35, 48), "head", 6)

    def pup_deco(d, L, S):
        d.ellipse([L(31.5, 44), L(34, 46.5)], fill=(240, 240, 230))
    P.add("pupil", cut(circ(34, 48, 5.2, 20), (22, 22, 24), pup_deco, curve=False, seed=seed + 10, edge=0.4), (34, 48), "eye", 7)
    P.add("pect", cut([(73, 82), (84, 77), (112, 92), (132, 110), (118, 124), (92, 110)], lt(fin, 1.08),
                      rays(78, 82, [(124 - k * 6, 116 - k * 2) for k in range(6)], dk(fin), ((75, 84), (94, 110))), per=5, seed=seed + 15), (79, 82), "body", 8)
    return P


def trout_pose(pose="swim", t=0.0, phase=0.0, gaze=(0.0, 0.0), jaw=None):
    """Joint angles for a named pose. Returns (pose dict, (dx, dy, extra_pitch))."""
    s = math.sin
    tw = 2 * math.pi * t
    wag, freq, point, jw, nod, root = 10.0, 1.5, 0.0, 3.0, 0.0, (0.0, 3 * s(t * 1.1 + phase), 2 * s(t * 0.9 + phase))
    if pose == "still":
        wag, freq = 3.0, 0.8
    elif pose == "look":
        wag, freq, jw, nod = 6.0, 1.2, 7.0, -4.0
    elif pose == "run":         # flat out: fast short strokes, fins pinned back, mouth open
        wag, freq, jw, nod = 26.0, 4.6, 12.0, 3.0
        point = -0.25
        root = (4 * s(tw * 4.6 + phase), 3 * s(tw * 2.3 + phase), 3 * s(tw * 4.6 + phase))
    elif pose == "dance":       # rocks on the beat, fin thrown up
        wag, freq, jw = 22.0, 2.0, 9.0
        point = 0.5 + 0.5 * s(tw * 2.0 + phase)
        nod = 8 * s(tw * 2.0 + phase)
        root = (10 * s(tw * 1.0 + phase), -12 * abs(s(tw * 2.0 + phase)), 20 * s(tw * 2.0 + phase))
    elif pose == "gasp":
        wag, freq, jw = 5.0, 1.0, 10 + 8 * s(tw * 1.2 + phase)
    elif pose == "point":
        point, jw = 1.0, 5.0
    if jaw is not None:
        jw = jaw
    w = s(tw * freq + phase)
    pd = {"tail": wag * w, "dorsal": 4 * s(tw * 0.7 + phase), "anal": 6 * s(tw * freq + phase - 0.8), "pelvic": 8 * s(tw * 1.1 + phase),
          "head": nod - wag * 0.12 * w, "jaw": -jw, "pupil": (0.0, gaze[0], gaze[1]),
          "pect": lerp(10 * s(tw * 2.2 + phase), -138 + 8 * s(tw * 3), point) if point >= 0 else 28 + 4 * s(tw * 4)}
    return pd, root


def trout(target, x, y, scale=0.6, t=0.0, kind=0, flip=False, pitch=0.0, pose="swim", phase=0.0, gaze=(0.0, 0.0), jaw=None,
          shade=0.0, alpha=1.0, drop=True):
    """A brook trout, body centre at (x, y). Design faces left; flip=True faces right. pitch lifts the nose.
    pose: swim, still, look, run, dance, gasp, point. kind 0..3 picks one of four individuals.
    Returns screen points: mouth, eye, tail."""
    P = _trout(kind)
    pd, root = trout_pose(pose, t, phase, gaze, jaw)
    fx = -1.0 if flip else 1.0

    def draw(layer, ox, oy):
        M = Tm(x + ox + root[0] * scale, y + oy + root[1] * scale) @ Rm((pitch + root[2]) * fx) @ Sm(scale * fx, scale) @ Tm(-120, -62)
        return P.draw(layer, pd, M)
    half = int(190 * scale + 16)
    ms = _group(target, x, y, half, draw, shade, alpha, (5 * scale, 8 * scale, 5 * scale, 0.28) if drop else None)

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    return {"mouth": pt("head", (5, 69)), "eye": pt("eye", (35, 48)), "tail": pt("tail", (290, 60))}


# =================================================================== BRASS
@lru_cache(None)
def brass_ring(r_in, r_out, bolts=6, start=-90.0, fittings=False):
    """A turned brass ring with hex bolts (bolt 1 at the top, numbered clockwise), lit from the upper left.
    Returns an RGBA image whose centre is the ring's centre."""
    S = 2
    pad = 16 + (int(r_out * 0.34) if fittings else 0)
    n = 2 * (r_out + pad)
    N = n * S
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    dx, dy = xx - N / 2 + 0.5, yy - N / 2 + 0.5
    rr = np.hypot(dx, dy) / S
    th = np.arctan2(dy, dx)
    u = (rr - r_in) / float(r_out - r_in)
    slope = np.where(u < 0.24, 1.0, np.where(u > 0.80, -1.0, 0.0)) * 0.72
    nx, ny = -slope * np.cos(th), -slope * np.sin(th)
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    diff = nx * -0.50 + ny * -0.68 + nz * 0.54
    lathe = 0.035 * np.sin(rr * 2.4) + 0.05 * vnoise((N, N), 3, None, 5)
    streak = np.abs(np.cos(th + 0.95)) ** 12
    shade = 0.50 + 0.72 * diff + lathe + np.where(slope == 0, 0.30 * streak, 0.12 * streak)
    col = np.array(PAL["brass"], np.float32)[None, None, :] * shade[..., None]
    col += np.clip(shade - 0.98, 0, 1)[..., None] * np.array([150, 150, 120], np.float32)
    # grime in the seam between ring and glass / wall
    col *= (1 - 0.35 * np.clip(1 - np.abs(u - 0.24) * 14, 0, 1) - 0.25 * np.clip(1 - np.abs(u - 0.80) * 14, 0, 1))[..., None]
    al = np.clip((rr - r_in) * S + 0.5, 0, 1) * np.clip((r_out - rr) * S + 0.5, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), "RGBA")
    if fittings:        # an iron hinge on the left and a brass dog on the right
        fl = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        d = ImageDraw.Draw(fl)
        c = N / 2
        hw, hh = r_out * 0.20 * S, r_out * 0.34 * S
        x0 = c - (r_out + r_out * 0.20) * S
        d.rounded_rectangle([x0, c - hh, x0 + hw * 2.3, c + hh], 5 * S, fill=(52, 50, 50, 255), outline=(24, 22, 22, 255), width=2 * S)
        d.rectangle([x0 + hw * 0.9, c - hh * 1.08, x0 + hw * 1.25, c + hh * 1.08], fill=(78, 76, 76, 255), outline=(24, 22, 22, 255), width=S)
        d.line([x0 + hw * 0.98, c - hh, x0 + hw * 0.98, c + hh], fill=(130, 128, 124, 255), width=S)
        for sy in (-0.62, 0.62):
            for sx in (0.42, 1.8):
                bx, by = x0 + hw * sx, c + hh * sy
                d.ellipse([bx - 5 * S, by - 5 * S, bx + 5 * S, by + 5 * S], fill=(96, 94, 92, 255), outline=(20, 20, 20, 255), width=S)
                d.line([bx - 3 * S, by - 2 * S, bx + 3 * S, by + 2 * S], fill=(26, 26, 26, 255), width=S)
        x1 = c + (r_out - r_out * 0.12) * S
        lw, lh = r_out * 0.36 * S, r_out * 0.11 * S
        d.rounded_rectangle([x1, c - lh, x1 + lw, c + lh], lh, fill=PAL["brass"] + (255,), outline=PAL["brass_dark"] + (255,), width=2 * S)
        d.line([x1 + lh, c - lh * 0.45, x1 + lw - lh, c - lh * 0.45], fill=PAL["brass_lit"] + (255,), width=2 * S)
        d.rounded_rectangle([x1 + lw * 0.52, c - lh * 2.4, x1 + lw * 0.80, c + lh * 2.4], lh * 0.8, fill=lt(PAL["brass"], 1.08) + (255,), outline=PAL["brass_dark"] + (255,), width=2 * S)
        d.ellipse([x1 + lw * 0.58, c - lh * 0.5, x1 + lw * 0.74, c + lh * 0.5], fill=PAL["brass_dark"] + (255,))
        sh = shadow_of(fl.getchannel("A"), 4 * S, 0.5)
        base = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        base.alpha_composite(sh, (3 * S, 5 * S))
        base.alpha_composite(fl)
        base.alpha_composite(im)
        im = base
    if bolts:
        bl = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        d = ImageDraw.Draw(bl)
        rm, hr = (r_in + r_out) / 2 * S, (r_out - r_in) * 0.30 * S
        for k in range(bolts):
            a = math.radians(start + 360.0 * k / bolts)
            bx, by = N / 2 + rm * math.cos(a), N / 2 + rm * math.sin(a)
            hexp = [(bx + hr * math.cos(math.radians(60 * j + 17 * k)), by + hr * math.sin(math.radians(60 * j + 17 * k))) for j in range(6)]
            d.polygon(hexp, fill=lt(PAL["brass"], 1.12) + (255,), outline=PAL["brass_dark"] + (255,))
            d.line(hexp + [hexp[0]], fill=PAL["brass_dark"] + (255,), width=max(2, S))
            d.ellipse([bx - hr * 0.62, by - hr * 0.62, bx + hr * 0.62, by + hr * 0.62], fill=PAL["brass"] + (255,), outline=dk(PAL["brass"], 0.7) + (255,), width=S)
            d.arc([bx - hr * 0.62, by - hr * 0.62, bx + hr * 0.62, by + hr * 0.62], 180, 280, fill=PAL["brass_lit"] + (255,), width=max(2, S))
            d.arc([bx - hr * 0.95, by - hr * 0.95, bx + hr * 0.95, by + hr * 0.95], 190, 265, fill=(250, 232, 170, 255), width=max(2, S))
        sh = shadow_of(bl.getchannel("A"), 2.5 * S, 0.6)
        tmp = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        tmp.alpha_composite(sh, (int(1.5 * S), int(2.5 * S)))
        tmp.putalpha(ImageChops.multiply(tmp.getchannel("A"), im.getchannel("A")))
        im.alpha_composite(tmp)
        im.alpha_composite(bl)
    return im.resize((n, n), Image.LANCZOS)


def bolt_xy(k, cx, cy, r_in, r_out):
    """Centre of bolt k (1..6; 1 at the top, clockwise) on a ring."""
    a = math.radians(-90 + 60 * (k - 1))
    rm = (r_in + r_out) / 2
    return (cx + rm * math.cos(a), cy + rm * math.sin(a))


@lru_cache(None)
def _halo(r, color, peak=200):
    n = int(r) * 2 + 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    f = np.clip(1 - np.hypot(xx - n / 2, yy - n / 2) / r, 0, 1) ** 1.8
    a = np.zeros((n, n, 4), np.uint8)
    a[..., :3] = color
    a[..., 3] = (f * peak).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def glow(target, x, y, r=40, color=(255, 206, 110), strength=1.0):
    """A soft halo of light centred at (x, y)."""
    if strength <= 0:
        return
    _comp(target, _halo(int(r), tuple(color), int(clamp(strength) * 210)), (x - int(r) - 1, y - int(r) - 1))


# =================================================== THE TIN, FROM INSIDE
PORT = (560, 246)       # default centre of the porthole seen from Turkey's seat
PORT_R = 178            # glass radius
RING_W = 46             # brass ring width


@lru_cache(None)
def _cabin(cx, cy, r):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.array(PAL["cabin"], np.float32)
    rib = np.sin(yy * (2 * math.pi / 26.0))                      # the pressed ribs of a bread tin
    shade = 1 + 0.16 * rib + 0.10 * np.clip(rib - 0.7, 0, 1) * 6 + 0.09 * vnoise((H, W), 260, 20, 301, 3) + 0.05 * vnoise((H, W), 2.5, None, 302)
    a = base[None, None, :] * shade[..., None]
    rust = np.clip(vnoise((H, W), 150, 60, 303, 3) - 0.18, 0, 1) * 1.6
    a = a * (1 - rust[..., None] * 0.55) + np.array([120, 70, 40], np.float32) * rust[..., None] * 0.55
    wall = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(wall)
    # flanges top and bottom, and two welded seams, each with its row of rivets
    for (y0, y1) in ((0, 30), (H - 34, H)):
        d.rectangle([0, y0, W, y1], fill=(92, 78, 62, 255))
        d.line([0, y1 if y0 == 0 else y0, W, y1 if y0 == 0 else y0], fill=(30, 22, 16, 255), width=3)
        d.line([0, (y1 - 2) if y0 == 0 else (y0 + 3), W, (y1 - 2) if y0 == 0 else (y0 + 3)], fill=(140, 122, 96, 255), width=1)
    seams = [cx - r - 150, cx + r + 138]
    for sx in seams:
        d.rectangle([sx - 15, 0, sx + 15, H], fill=(86, 72, 58, 255))
        d.line([sx - 15, 0, sx - 15, H], fill=(132, 114, 90, 255), width=1)
        d.line([sx + 15, 0, sx + 15, H], fill=(28, 20, 16, 255), width=2)

    def rivet(x, y, rr=5):
        d.ellipse([x - rr + 2, y - rr + 3, x + rr + 2, y + rr + 3], fill=(18, 12, 10, 150))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(112, 96, 76, 255), outline=(40, 30, 22, 255))
        d.ellipse([x - rr + 1, y - rr + 1, x, y], fill=(176, 156, 122, 255))
    for x in range(18, W, 38):
        rivet(x, 15)
        rivet(x, H - 17)
    for sx in seams:
        for y in range(52, H - 40, 34):
            rivet(sx, y)
    a = np.asarray(wall, np.float32).copy()
    pool = 1.30 - 0.95 * np.clip(np.hypot((xx - cx + 60) / 760, (yy - 60) / 520), 0, 1.3) ** 1.3    # the lamp, up over the glass
    a[..., :3] *= pool[..., None] * np.array([1.06, 0.98, 0.86], np.float32)
    hole = np.clip(np.hypot(xx - cx, yy - cy) - r - 1, 0, 1)
    a[..., 3] = hole * 255
    wall = to_img(a).convert("RGBA")
    ring = brass_ring(r, r + RING_W, fittings=True)
    off = (int(cx - ring.size[0] / 2), int(cy - ring.size[1] / 2))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _comp(sh, shadow_of(ring.getchannel("A"), 9, 0.62), (off[0] + 7, off[1] + 11))
    sh.putalpha(ImageChops.multiply(sh.getchannel("A"), wall.getchannel("A")))
    # the glass: thick, greenish, dark where it meets the ring, one long reflection
    n = 2 * r + 8
    gy, gx = np.mgrid[0:n, 0:n].astype(np.float32)
    gr = np.hypot(gx - n / 2, gy - n / 2)
    g = np.zeros((n, n, 4), np.float32)
    edge = np.clip((gr - r * 0.80) / (r * 0.20), 0, 1) ** 2
    g[..., :3] = np.array([10, 26, 26], np.float32)
    g[..., 3] = edge * 170 + 14
    g[..., 3] *= (gr <= r + 2)
    glass = to_img(g).convert("RGBA")
    refl = Image.new("L", (n * 2, n * 2), 0)
    rd = ImageDraw.Draw(refl)
    rd.arc([n * 0.18, n * 0.16, n * 1.82, n * 1.84], 200, 252, fill=150, width=int(r * 0.11))
    rd.arc([n * 0.34, n * 0.32, n * 1.66, n * 1.68], 206, 236, fill=90, width=int(r * 0.05))
    rd.arc([n * 0.14, n * 0.12, n * 1.86, n * 1.88], 28, 52, fill=70, width=int(r * 0.06))
    refl = refl.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.2))
    rl = Image.new("RGBA", (n, n), (236, 248, 240, 0))
    rl.putalpha(refl)
    glass.alpha_composite(rl)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _comp(out, glass, (cx - n // 2, cy - n // 2))
    out.alpha_composite(wall)
    out.alpha_composite(sh)
    _comp(out, ring, off)
    return out


def cabin(target, t=0.0, port=PORT, r=PORT_R, lit=(), dim=0.0):
    """The inside wall of the bread-roll tin with its brass porthole, laid OVER whatever has already been
    drawn (the river shows through the glass). lit = bolt numbers (1..6) that glow. dim 0..1 darkens the cabin
    (air running out). Returns {'port': (cx, cy), 'r': r, 'bolts': {k: (x, y)}}."""
    cx, cy = int(port[0]), int(port[1])
    sheet = _cabin(cx, cy, int(r))
    if dim > 0:
        a = sheet.getchannel("A")
        sheet = Image.blend(sheet.convert("RGB"), Image.new("RGB", sheet.size, (10, 10, 14)), clamp(dim) * 0.7).convert("RGBA")
        sheet.putalpha(a)
    _comp(target, sheet, (0, 0))
    bolts = {k: bolt_xy(k, cx, cy, r, r + RING_W) for k in range(1, 7)}
    for k in lit:
        f = 0.85 + 0.15 * math.sin(t * 5 + k)
        glow(target, bolts[k][0], bolts[k][1], 58, (255, 186, 70), f)
        glow(target, bolts[k][0], bolts[k][1], 30, (255, 214, 120), f)
        glow(target, bolts[k][0], bolts[k][1], 13, (255, 250, 220), 1.0)
    return {"port": (cx, cy), "r": r, "bolts": bolts}


@lru_cache(None)
def _gauge_face(r):
    S = 3
    n = (r + 12) * 2
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n * S / 2
    d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], fill=PAL["ivory"] + (255,))
    d.pieslice([c - r * S * 0.86, c - r * S * 0.86, c + r * S * 0.86, c + r * S * 0.86], 150, 205, fill=(206, 84, 70, 255))
    d.ellipse([c - r * S * 0.66, c - r * S * 0.66, c + r * S * 0.66, c + r * S * 0.66], fill=PAL["ivory"] + (255,))
    for k in range(13):
        a = math.radians(150 + 240 * k / 12)
        r0 = 0.70 if k % 3 == 0 else 0.78
        d.line([c + math.cos(a) * r * S * r0, c + math.sin(a) * r * S * r0, c + math.cos(a) * r * S * 0.88, c + math.sin(a) * r * S * 0.88], fill=(40, 34, 30, 255), width=S if k % 3 else 2 * S)
    f = font("mono", int(r * 0.30 * S))
    d.text((c, c + r * S * 0.42), "AIR", font=f, fill=(60, 50, 44, 255), anchor="mm")
    im = im.resize((n, n), Image.LANCZOS)
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= (1 + 0.05 * vnoise((n, n), 3, None, 311, 2) - 0.10 * np.linspace(0, 1, n)[:, None])[..., None]
    im = to_img(a).convert("RGBA")
    bez = brass_ring(r, r + 8, bolts=0)
    out = Image.new("RGBA", bez.size, (0, 0, 0, 0))
    o = (bez.size[0] - n) // 2
    out.alpha_composite(im, (o, o))
    out.alpha_composite(shadow_of(bez.getchannel("A"), 3, 0.5), (2, 3))
    out.putalpha(ImageChops.lighter(out.getchannel("A"), bez.getchannel("A")))
    out.alpha_composite(bez)
    return out


def air_gauge(target, x, y, level=1.0, r=34, t=0.0):
    """A brass AIR dial centred at (x, y). level 1 = full, 0 = empty (needle in the red). Needle trembles."""
    face = _gauge_face(int(r))
    _comp(target, shadow_of(face.getchannel("A"), 6, 0.5), (x - face.size[0] / 2 + 5, y - face.size[1] / 2 + 8))
    _comp(target, face, (x - face.size[0] / 2, y - face.size[1] / 2))
    a = math.radians(150 + 240 * clamp(level) + 2.5 * math.sin(t * 9) * (0.3 + 0.7 * (1 - clamp(level))))
    S = 3
    n = int(r) * 2 + 4
    nl = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(nl)
    c = n * S / 2
    d.line([c - math.cos(a) * r * S * 0.2, c - math.sin(a) * r * S * 0.2, c + math.cos(a) * r * S * 0.8, c + math.sin(a) * r * S * 0.8], fill=(150, 34, 30, 255), width=int(1.2 * S) + 1)
    d.ellipse([c - 4 * S, c - 4 * S, c + 4 * S, c + 4 * S], fill=PAL["brass_dark"] + (255,))
    nl = nl.resize((n, n), Image.LANCZOS)
    _comp(target, shadow_of(nl.getchannel("A"), 1.2, 0.5), (x - n / 2 + 1.5, y - n / 2 + 2.5))
    _comp(target, nl, (x - n / 2, y - n / 2))


# ============================================== THE TIN, FROM THE RIVER
# Design frame faces LEFT (porthole near the bow, screw at the stern), body 404 x 150; anchor = body centre (200, 130).
TIN_C = (200, 130)
TIN_PORT = (128, 132)
WIN_R = 47


@lru_cache(None)
def _tin():
    P = Puppet()
    tinc, lidc = PAL["tin"], PAL["tin_lid"]

    def body_deco(d, L, S):
        for y in (96, 150, 184):
            d.line([L(8, y), L(396, y)], fill=PAL["tin_dark"], width=2 * S)
            d.line([L(8, y + 2.5), L(396, y + 2.5)], fill=(222, 230, 226), width=S)
        for k in range(40):
            x = 10 + k * 9.8
            d.line([L(x, 100), L(x, 148)], fill=(164, 174, 170), width=S)
            d.line([L(x + 1.5, 100), L(x + 1.5, 148)], fill=(196, 206, 202), width=S)
        for k in range(40):     # rust at the seams
            x, y = (k * 97) % 400, 186 + (k * 13) % 16
            d.ellipse([L(x - 5, y - 3), L(x + 5, y + 3)], fill=PAL["rust"])
        for k in range(27):     # the riveted seams
            for y in (90, 190):
                x = 14 + k * 14.5
                d.ellipse([L(x - 2.6, y - 2.6), L(x + 2.6, y + 2.6)], fill=(214, 222, 218), outline=(96, 106, 104))
        for y in range(104, 150, 12):
            for x in (232, 244):
                d.ellipse([L(x - 2.2, y - 2.2), L(x + 2.2, y + 2.2)], fill=(214, 222, 218), outline=(96, 106, 104))
    P.add("mouth", cut(rrect(10, 58, 394, 78, 6), (26, 26, 28), curve=False, seed=401, edge=0.3), (200, 68), "body", 2.5)
    P.add("body", cut(rrect(0, 56, 404, 204, 30), tinc, body_deco, curve=False, seed=402, grain=0.11), TIN_C, None, 2)

    def lid_deco(d, L, S):
        d.line([L(-4, 70), L(408, 70)], fill=PAL["tin_dark"], width=2 * S)
        d.line([L(-4, 38), L(408, 38)], fill=(206, 214, 210), width=S)
        for k in range(21):
            x = 8 + k * 19.4
            d.ellipse([L(x - 2.5, 60), L(x + 2.5, 65)], fill=(214, 222, 218), outline=(96, 106, 104))
    P.add("lid", cut(rrect(-8, 30, 412, 76, 18), lidc, lid_deco, curve=False, seed=403, grain=0.11), (406, 70), "body", 3)
    P.add("knob", compose([cut(rrect(184, 16, 220, 32, 5), (120, 90, 50), curve=False, seed=404), cut(rrect(176, 6, 228, 20, 6), PAL["brass"], curve=False, seed=405)]), (202, 30), "lid", 2.9)
    P.add("pin", compose([cut(rrect(396, 60, 420, 84, 5), (70, 70, 72), curve=False, seed=406), cut(circ(408, 72, 6), PAL["brass"], curve=False, seed=407)]), (408, 72), "body", 3.2)

    def label_deco(d, L, S):
        d.rectangle([L(262, 106), L(366, 150)], outline=(150, 44, 40), width=2 * S)
        d.text(L(314, 128), "ROLLS", font=font("serif", 24 * S), fill=(120, 36, 34), anchor="mm")
    lab = cut(rrect(256, 100, 372, 156, 4), (236, 226, 198), label_deco, curve=False, seed=408)
    P.add("label", lab, (314, 128), "body", 3)
    P.label_flip = Sprite(lab.img.transpose(Image.FLIP_LEFT_RIGHT), 2 * 314 - (lab.ox + lab.img.size[0]), lab.oy)     # reads right when the tin faces right
    P.add("rudder", cut([(396, 100), (446, 76), (452, 130), (446, 184), (396, 160)], lidc, curve=False, seed=409), (400, 130), "body", 1)
    P.add("hub", cut(circ(452, 130, 9), PAL["brass"], curve=False, seed=410), (452, 130), "body", 4)
    P.add("blade", cut([(450, 130), (444, 96), (456, 70), (466, 96), (458, 130), (466, 164), (456, 190), (444, 164)], (206, 170, 86), per=5, seed=411), (452, 130), "body", 3.5)
    P.add("skid", cut(rrect(60, 200, 340, 214, 6), (120, 130, 128), curve=False, seed=412), (200, 206), "body", 1)
    P.add("window", None, TIN_PORT, "body", 5)
    # the porthole is a DOOR: brass ring and glass on one iron hinge at the left, a brass dog (latch) at the right
    hx = TIN_PORT[0] - 64

    def hinge_deco(d, L, S):
        d.ellipse([L(hx - 4, 128), L(hx + 4, 136)], fill=PAL["brass"], outline=(20, 20, 20), width=S)
        for yy in (118, 146):
            d.ellipse([L(hx - 8, yy - 2), L(hx - 4, yy + 2)], fill=(120, 118, 114))
    P.add("hinge", cut(rrect(hx - 13, 112, hx + 7, 152, 3), (58, 56, 56), hinge_deco, curve=False, seed=413), (hx, 132), "body", 5.5)
    ring = brass_ring(WIN_R * 2, 64 * 2).resize(((64 + 16) * 2, (64 + 16) * 2), Image.LANCZOS)
    n = ring.size[0]
    sheen = Image.new("RGBA", (n * 2, n * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheen)
    c = n
    d.ellipse([c - 94, c - 94, c + 94, c + 94], fill=(200, 236, 226, 26))
    d.arc([c - 78, c - 82, c + 78, c + 82], 196, 262, fill=(255, 255, 250, 160), width=8)
    d.arc([c - 62, c - 66, c + 62, c + 66], 20, 50, fill=(255, 255, 250, 80), width=6)
    door = sheen.resize((n, n), Image.LANCZOS)
    door.alpha_composite(ring)
    P.add("door", Sprite(door, TIN_PORT[0] - n // 2, TIN_PORT[1] - n // 2), (hx, 132), "body", 6)
    lx = TIN_PORT[0] + 72

    def latch_deco(d, L, S):
        d.line([L(lx - 20, 129.5), L(lx + 4, 129.5)], fill=PAL["brass_lit"], width=S)
        d.ellipse([L(lx - 3.5, 128.5), L(lx + 3.5, 135.5)], fill=PAL["brass_dark"])
    P.add("latch", cut(rrect(lx - 24, 126, lx + 8, 138, 5), lt(PAL["brass"], 1.08), latch_deco, curve=False, seed=414), (lx, 132), "body", 7)

    def tag_deco(d, L, S):
        d.line([L(lx, 134), L(lx + 1, 162)], fill=(120, 96, 70), width=S)
        d.ellipse([L(lx - 2, 164), L(lx + 3, 169)], fill=(90, 70, 50))
        for k in range(3):
            d.line([L(lx - 9, 176 + k * 6), L(lx + 10 - 5 * (k == 2), 175 + k * 6)], fill=(110, 60, 56), width=S)
    string = cut([(lx - 1, 134), (lx + 1, 134), (lx + 2, 162), (lx, 162)], (120, 96, 70), curve=False, seed=415, edge=0.3)
    tagp = cut([(lx - 8, 160), (lx + 9, 160), (lx + 14, 166), (lx + 14, 196), (lx - 13, 196), (lx - 13, 166)], (240, 226, 190), tag_deco, curve=False, seed=416)
    P.add("tag", compose([string, tagp]), (lx, 134), "body", 7.5)
    # a wire carrying handle on two rivets (the lunchbox reading)
    arch_o = catmull([(112, 36), (120, 6), (160, -12), (205, -16), (250, -12), (290, 6), (298, 36)], 8)
    arch_i = catmull([(290, 36), (283, 10), (248, -5), (205, -9), (162, -5), (127, 10), (120, 36)], 8)

    def handle_deco(d, L, S):
        for x in (116, 294):
            d.ellipse([L(x - 5, 29), L(x + 5, 39)], fill=PAL["brass"], outline=PAL["brass_dark"], width=S)
    P.add("handle", cut(arch_o + arch_i, (96, 100, 104), handle_deco, curve=False, seed=417), (205, 36), "lid", 2.8)
    # a small air dial riveted to the side
    dc = (236, 123)

    def dial_deco(d, L, S):
        d.ellipse([L(dc[0] - 14, dc[1] - 14), L(dc[0] + 14, dc[1] + 14)], fill=PAL["ivory"])
        d.pieslice([L(dc[0] - 13, dc[1] - 13), L(dc[0] + 13, dc[1] + 13)], 150, 200, fill=(206, 84, 70))
        d.ellipse([L(dc[0] - 9, dc[1] - 9), L(dc[0] + 9, dc[1] + 9)], fill=PAL["ivory"])
        for k in range(9):
            a = math.radians(150 + 240 * k / 8)
            d.line([L(dc[0] + 10 * math.cos(a), dc[1] + 10 * math.sin(a)), L(dc[0] + 13.5 * math.cos(a), dc[1] + 13.5 * math.sin(a))], fill=(40, 34, 30), width=S)
    P.add("dial", cut(circ(dc[0], dc[1], 18), PAL["brass"], dial_deco, curve=False, seed=418), dc, "body", 4)
    P.add("needle", compose([cut([(dc[0] - 1.6, dc[1] + 4), (dc[0] + 1.6, dc[1] + 4), (dc[0] + 0.6, dc[1] - 13), (dc[0] - 0.6, dc[1] - 13)], (150, 34, 30), curve=False, seed=419, edge=0.3),
                             cut(circ(dc[0], dc[1], 2.6, 12), PAL["brass_dark"], curve=False, seed=420, edge=0.3)]), dc, "dial", 4.5)
    return P


def _tin_window(mood, t, look, guests, lamp):
    """What shows in the tin's porthole from the river: the lamplit inside, Turkey, the glass."""
    n = WIN_R * 2 + 4
    S = 2
    im = Image.new("RGBA", (n * S, n * S), (52, 40, 30, 255))
    d = ImageDraw.Draw(im)
    for k in range(10):
        r = n * S * (0.75 - k * 0.06)
        c = tuple(int(v * (0.35 + 0.65 * lamp)) for v in (60 + k * 11, 44 + k * 7, 30 + k * 3))
        d.ellipse([n * S * 0.62 - r, n * S * 0.34 - r, n * S * 0.62 + r, n * S * 0.34 + r], fill=c + (255,))
    ps, root = turkey_pose(mood, t, look)
    M = Tm(n * S * 0.50 + root[0] * S * 0.4, n * S * 0.50 + root[1] * S * 0.4) @ Sm(0.41 * S) @ Rm(root[2]) @ Tm(-124, -128)
    # the near wing would hide his face in so small a window: it shows only when it is the point (wave, cheer)
    _turkey().draw(im, ps, M, skip=() if mood in ("wave", "cheer") else ("wing",), shadow=(2.0, 2.8, 1.5, 0.3))
    for g in range(guests):     # trout who have come inside, crowding the glass
        pd, _ = trout_pose("look", t, g * 2.1)
        gx, gy = [(0.74, 0.70), (0.36, 0.80), (0.66, 0.30)][g % 3]
        Mg = Tm(n * S * gx, n * S * gy + 3 * S * math.sin(t * 2 + g)) @ Rm(-8 + 16 * g) @ Sm(0.30 * S * (1 if g % 2 == 0 else -1), 0.30 * S) @ Tm(-120, -62)
        _trout(g + 1).draw(im, pd, Mg, shadow=(2.0, 2.8, 1.5, 0.3))
    im = im.resize((n, n), Image.LANCZOS)
    m = Image.new("L", (n * 2, n * 2), 0)
    ImageDraw.Draw(m).ellipse([4, 4, n * 2 - 4, n * 2 - 4], fill=255)
    im.putalpha(m.resize((n, n), Image.LANCZOS))
    return Sprite(im, TIN_PORT[0] - n // 2, TIN_PORT[1] - n // 2)


def tin(target, x, y, scale=1.0, t=0.0, mood="calm", flip=False, pitch=0.0, lid_open=0.0, spin=None, guests=0, lamp=1.0,
        look=(0.0, 0.0), shade=0.0, alpha=1.0, drop=True, door_open=0.0, latch=0.0, tag=None, handle=None, dial=None):
    """Turkey's submersible from the river side: a riveted bread-roll tin, body centre at (x, y).
    Design faces left (porthole forward); flip=True faces right. Turkey shows in the porthole in `mood`;
    guests = trout inside with him (0..3). Hinges, each on ONE visible pin:
      lid_open   degrees the lid swings up on the pin at the stern
      door_open  degrees (0..180) the brass porthole DOOR swings out on its iron hinge at the left of the ring
      latch      0 = the brass dog holds the door shut, 1 = flipped up
      tag        None = no tag; a number = a paper tag on a string tied to the latch, hanging at that angle (degrees)
      handle     None = no handle; 0..1 = a wire carrying handle folded flat .. swung up over the top
      dial       None = no dial; 0..1 = a small air dial riveted to the side, needle at that level (0 empty)
    Returns screen points: port (centre), port_r, hatch, bow, stern, top, lid_tip, keel, latch, door_edge, dial."""
    P = _tin()
    fx = -1.0 if flip else 1.0
    spin = t * 300 if spin is None else spin
    win = _tin_window(mood, t, look, guests, lamp)
    pose = {"lid": lid_open, "blade": (0.0, 0.0, 0.0, 1.0, math.cos(math.radians(spin)) * 0.9 + 0.1), "knob": 0.0,
            "door": (0.0, 0.0, 0.0, math.cos(math.radians(door_open)), 1.0), "latch": 90.0 * clamp(latch),
            "tag": tag or 0.0, "handle": (0.0, 0.0, 0.0, 1.0, lerp(0.16, 1.0, clamp(handle or 0.0))),
            "needle": lerp(-120, 120, clamp(dial or 0.0)) + (2.0 * math.sin(t * 9) if dial is not None else 0)}
    skip = [n for n, v in (("tag", tag), ("handle", handle), ("dial", dial), ("needle", dial)) if v is None]

    def draw(layer, ox, oy):
        M = Tm(x + ox, y + oy) @ Rm(pitch * fx) @ Sm(scale * fx, scale) @ Tm(-TIN_C[0], -TIN_C[1])
        return P.draw(layer, pose, M, sprites={"window": win, "label": P.label_flip} if flip else {"window": win}, skip=skip)
    half = int(290 * scale + 20)
    ms = _group(target, x, y, half, draw, shade, alpha, (8 * scale, 12 * scale, 8 * scale, 0.30) if drop else None)

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    return {"port": pt("body", TIN_PORT), "port_r": WIN_R * scale, "hatch": pt("body", (200, 60)), "bow": pt("body", (0, 130)),
            "stern": pt("body", (452, 130)), "top": pt("lid", (202, 6)), "lid_tip": pt("lid", (-8, 52)), "keel": pt("body", (200, 214)),
            "latch": pt("body", (TIN_PORT[0] + 72, 132)), "door_edge": pt("door", (TIN_PORT[0] + 64, 132)), "dial": pt("body", (236, 123))}


# =================================================================== RIVER
RIVER_PAR = dict(back=0.06, far=0.25, mid=0.5, bed=1.0, front=1.8)
CAM_MAX = 160


def make_rock(seed, w, h, base=None, moss=None):
    base, moss = base or PAL["rock"], moss or PAL["moss"]
    rs = random.Random(seed)
    n = 11
    pts = []
    for k in range(n):
        a = math.pi + math.pi * k / (n - 1)
        r = 1 + rs.uniform(-0.14, 0.14)
        pts.append((w / 2 + math.cos(a) * w / 2 * r, h + math.sin(a) * h * r))
    pts += [(w + 6, h + 14), (-6, h + 14)]

    def deco(d, L, S):
        for _ in range(5):
            x, y = rs.uniform(0, w), rs.uniform(h * 0.3, h)
            d.line([L(x, y), L(x + rs.uniform(-30, 30), y + rs.uniform(8, 40))], fill=dk(base, 0.7), width=S)
        for _ in range(26):
            x, y = rs.uniform(0, w), rs.uniform(0, h)
            r = rs.uniform(2, 7)
            d.ellipse([L(x - r, y - r * 0.7), L(x + r, y + r * 0.7)], fill=tuple(int(c * rs.uniform(0.82, 1.14)) for c in base))
    rock = cut(pts, base, deco, per=6, seed=seed)
    mp = []
    m = 9
    for k in range(m):
        a = math.pi * 1.10 + math.pi * 0.80 * k / (m - 1)
        mp.append((w / 2 + math.cos(a) * w / 2 * 0.97, h + math.sin(a) * h * 0.97))
    x_r, x_l = mp[-1][0], mp[0][0]
    for k in range(1, 7):
        mp.append((x_r + (x_l - x_r) * k / 7, h * (0.50 + 0.14 * math.sin(k * 2.3 + seed) + rs.uniform(-0.06, 0.06))))

    def mdeco(d, L, S):
        for _ in range(40):
            x, y = rs.uniform(0, w), rs.uniform(0, h * 0.7)
            r = rs.uniform(1.5, 4)
            d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=tuple(min(255, int(c * rs.uniform(0.8, 1.25))) for c in moss))
    return compose([rock, cut(mp, moss, mdeco, per=5, seed=seed + 1)])


@lru_cache(None)
def _blade(seed, length, width, color):
    """One weed blade in three hinged paper segments, growing up from (0, 0)."""
    rs = random.Random(seed)
    P = Puppet()
    seg = length / 3
    parent = None
    for k in range(3):
        y0, y1 = -k * seg + 5, -(k + 1) * seg - 3
        w0, w1 = width * (1 - k * 0.27), width * (1 - (k + 1) * 0.27) if k < 2 else 1.5
        bend = rs.uniform(-0.25, 0.25) * width
        col = tuple(min(255, int(c * (0.9 + 0.09 * k))) for c in color)

        def deco(d, L, S, y0=y0, y1=y1, col=col):
            d.line([L(0, y0), L(0, y1)], fill=dk(col, 0.78), width=S)
        spr = cut([(-w0 / 2, y0), (-(w0 + w1) / 4 + bend, (y0 + y1) / 2), (-w1 / 2, y1), (w1 / 2, y1), ((w0 + w1) / 4 + bend, (y0 + y1) / 2), (w0 / 2, y0)], col, deco, per=5, seed=seed + k)
        P.add(f"s{k}", spr, (0, -k * seg), parent, k)
        parent = f"s{k}"
    return P


def weed(target, x, y, length=220, width=20, t=0.0, seed=0, color=None, lean=0.0, scale=1.0):
    """One swaying weed blade (three hinged paper segments) rooted at (x, y)."""
    color = tuple(color or PAL["weed_mid"])
    P = _blade(int(seed), int(length), int(width), color)
    rs = random.Random(seed)
    ph, fr = rs.uniform(0, 6.28), rs.uniform(0.5, 0.8)
    w = 2 * math.pi * fr * 0.5 * t + ph
    P.draw(target, {"s0": lean + 4 * math.sin(w), "s1": 9 * math.sin(w - 0.8) + lean * 0.4, "s2": 13 * math.sin(w - 1.6)}, Tm(x, y) @ Sm(scale))


def _bed_sprite(w, h, seed, color):
    rs = random.Random(seed)
    top = [(x, 26 + 14 * math.sin(x * 0.011 + seed) + rs.uniform(-6, 6)) for x in range(-20, w + 60, 60)]

    def deco(d, L, S):
        for _ in range(int(w * h / 420)):
            x, y = rs.uniform(0, w), rs.uniform(30, h)
            r = rs.uniform(2, 9)
            c = rs.choice([(92, 112, 92), (52, 74, 66), (110, 118, 96), (78, 96, 100), (126, 120, 92)])
            d.ellipse([L(x - r, y - r * 0.6), L(x + r, y + r * 0.6)], fill=c)
            d.arc([L(x - r, y - r * 0.6), L(x + r, y + r * 0.6)], 200, 320, fill=tuple(min(255, v + 40) for v in c), width=S)
    return cut(top + [(w + 40, h + 10), (-20, h + 10)], color, deco, per=4, seed=seed)


@lru_cache(None)
def _water():
    h, w = H, W + 80
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top, bot = np.array(PAL["water_top"], np.float32), np.array(PAL["water_deep"], np.float32)
    a = top[None, None, :] * (1 - yy[..., None] ** 0.8) + bot[None, None, :] * (yy[..., None] ** 0.8)
    a = np.repeat(a, w, axis=1)
    a *= (1 + 0.07 * vnoise((h, w), 420, 9, 91, 3) + 0.05 * vnoise((h, w), 160, None, 92, 2) + 0.025 * fibre_tex()[:h, :w] if w <= 900 else
          1 + 0.07 * vnoise((h, w), 420, 9, 91, 3) + 0.05 * vnoise((h, w), 160, None, 92, 2))[..., None]
    hs, ws = H, 1900
    y, x = np.mgrid[0:hs, 0:ws].astype(np.float32)
    rs = np.random.RandomState(4)
    line = np.interp(np.arange(3000), np.arange(0, 3000, 70), rs.rand(43))
    line = np.clip((line - 0.45) * 3.2, 0, 1)
    sh = line[np.clip((x + 0.52 * y).astype(int), 0, 2999)] * np.clip(1 - y / 620, 0, 1) ** 1.3
    return to_img(a).convert("RGB"), Image.fromarray((blur_arr(sh, 7) * 255).astype(np.uint8), "L")


def river_back(target, t=0.0, cam=0.0, shafts=0.42):
    """The water itself, top-lit, with slow shafts of light. Fills the frame."""
    water, shaft = _water()
    img = _img(target)
    off = int(clamp(40 + cam * RIVER_PAR["back"], 0, 80))
    w = water.crop((off, 0, off + img.size[0], img.size[1]))
    if img.mode == "RGBA":
        img.alpha_composite(w.convert("RGBA"))
    else:
        img.paste(w, (0, 0))
    if shafts > 0:
        o1 = int(140 + 60 * math.sin(t * 0.23) + t * 5) % 900
        o2 = int(380 - t * 7 + 40 * math.sin(t * 0.31)) % 900
        a = ImageChops.screen(shaft.crop((o1, 0, o1 + W, H)), shaft.crop((o2, 0, o2 + W, H)).point(lambda v: int(v * 0.6)))
        lay = Image.new("RGBA", (W, H), (206, 236, 214, 0))
        lay.putalpha(a.point(lambda v: int(v * shafts)))
        _comp(target, lay, (0, 0))


@lru_cache(None)
def _river_layer(name, seed=0):
    par = RIVER_PAR[name]
    LW = W + int(2 * CAM_MAX * par) + 40
    rs = random.Random(seed * 31 + {"far": 1, "mid": 2, "bed": 3, "front": 4}[name])
    layer = Image.new("RGBA", (LW, H), (0, 0, 0, 0))

    def blades(xs, base, ln, wd, col, lean=0.0):
        for x in xs:
            c = tuple(int(v * rs.uniform(0.85, 1.15)) for v in col)
            P = _blade(rs.randint(0, 9999), int(ln * rs.uniform(0.7, 1.15)), int(wd * rs.uniform(0.8, 1.2)), c)
            le = lean + rs.uniform(-9, 9)
            P.draw(layer, {"s0": le, "s1": le * 0.6 + rs.uniform(-8, 8), "s2": rs.uniform(-12, 12)}, Tm(x + rs.uniform(-8, 8), base + rs.uniform(-6, 10)))
    haze, blur = 0.0, 0.0
    if name == "far":
        x = -80
        while x < LW:
            w = rs.randint(320, 480)
            draw_sprite(layer, make_rock(rs.randint(0, 999), w, rs.randint(150, 230), (40, 82, 82), (50, 98, 88)), Tm(x, 440 - rs.randint(170, 240)))
            x += w - rs.randint(20, 140)
        blades(range(10, LW, 46), 430, 240, 16, PAL["weed_far"])
        haze, blur = 0.58, 1.8
    elif name == "mid":
        x = -60
        while x < LW:
            w = rs.randint(200, 300)
            draw_sprite(layer, make_rock(rs.randint(0, 999), w, rs.randint(100, 160), (62, 92, 84), (92, 126, 78)), Tm(x, 470 - rs.randint(120, 170)))
            x += w + rs.randint(120, 320)
        xs = []
        x = 20
        while x < LW:
            xs += [x + k * 26 for k in range(rs.randint(2, 5))]
            x += rs.randint(220, 380)
        blades(xs, 462, 300, 22, PAL["weed_mid"])
        haze, blur = 0.30, 0.8
    elif name == "bed":
        draw_sprite(layer, _bed_sprite(LW + 40, 150, 3 + seed, PAL["gravel"]), Tm(-20, 418))
        x = rs.randint(20, 200)
        while x < LW:
            w = rs.randint(84, 180)
            draw_sprite(layer, make_rock(rs.randint(0, 999), w, int(w * rs.uniform(0.42, 0.52)), (70, 98, 86), (104, 134, 76)), Tm(x, 458 - int(w * 0.5)))
            x += w + rs.randint(150, 330)
        haze = 0.08
    else:       # the nearest plane keeps to the edges of the frame (at cam 0) so it never hides the actors
        o = (LW - W) // 2
        xs = [o - 70 + k * 36 for k in range(rs.randint(3, 4))] + [o + W - 60 + k * 36 for k in range(rs.randint(3, 4))]
        xs += [o - 520 + k * 36 for k in range(3)] + [o + W + 420 + k * 36 for k in range(3)]
        blades(xs, 600, 430, 46, PAL["weed_dark"])
        for x in (o - 230, o + W - 110, o - 760, o + W + 520):
            draw_sprite(layer, make_rock(rs.randint(0, 999), 330, 120, (18, 46, 46), (24, 58, 52)), Tm(x, 452))
        blur = 4.0
    if blur:
        layer = layer.convert("RGBa").filter(ImageFilter.GaussianBlur(blur)).convert("RGBA")
    if haze:
        al = layer.getchannel("A")
        layer = Image.blend(layer.convert("RGB"), Image.new("RGB", layer.size, PAL["water"]), haze).convert("RGBA")
        layer.putalpha(al)
    if name in ("mid", "bed"):      # each plane casts on the water behind it
        base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        base.alpha_composite(shadow_of(layer.getchannel("A"), 7, 0.24), (6, 9))
        base.alpha_composite(layer)
        layer = base
    return layer


def river_plane(target, name, t=0.0, cam=0.0, seed=0, dy=0.0):
    """One paper plane of the river: name = far, mid, bed or front. cam = camera x (about -160..160);
    nearer planes slide further (parallax 0.25, 0.5, 1.0, 1.8). seed picks another stretch of river."""
    layer = _river_layer(name, int(seed))
    par = RIVER_PAR[name]
    x = -(layer.size[0] - W) / 2 - clamp(cam, -CAM_MAX, CAM_MAX) * par
    if name == "front":
        x += 6 * math.sin(t * 0.6)
    _comp(target, layer, (x, dy))
    if name == "bed":       # a few living blades rooted in the gravel
        rs = random.Random(seed * 7 + 5)
        for k in range(7):
            wx = rs.uniform(0, layer.size[0])
            weed(target, wx + x, 448 + dy + rs.uniform(-6, 10), rs.randint(120, 230), rs.randint(14, 22), t, seed * 20 + k,
                 tuple(int(v * rs.uniform(0.85, 1.15)) for v in PAL["weed_mid"]), rs.uniform(-6, 6))


def river(target, t=0.0, cam=0.0, seed=0, shafts=0.42):
    """The whole river behind the actors: water, far, mid and bed planes. Follow with river_plane(.., 'front')."""
    river_back(target, t, cam, shafts)
    for name in ("far", "mid", "bed"):
        river_plane(target, name, t, cam, seed)


def bubbles(target, x, y, t=0.0, n=8, seed=0, rise=140, spread=26, size=5.0, rate=0.5):
    """A string of ring bubbles rising from (x, y); loops for ever."""
    img = _img(target)
    rs = random.Random(seed)
    S = 2
    box = int(spread * 2 + size * 6 + 20), int(rise + size * 6 + 20)
    lay = Image.new("RGBA", (box[0] * S, box[1] * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(n):
        u = (t * rate * rs.uniform(0.7, 1.3) + rs.random()) % 1.0
        r = size * rs.uniform(0.5, 1.3) * (0.6 + 0.6 * u)
        bx = box[0] / 2 + rs.uniform(-1, 1) * spread * u + 4 * math.sin(t * 3 + k * 1.7)
        by = box[1] - 10 - size * 3 - rise * u
        a = int(230 * min(1, u * 6) * min(1, (1 - u) * 4))
        d.ellipse([(bx - r) * S, (by - r) * S, (bx + r) * S, (by + r) * S], fill=(226, 244, 238, int(a * 0.22)), outline=(236, 248, 242, a), width=S)
        d.arc([(bx - r * 0.6) * S, (by - r * 0.6) * S, (bx + r * 0.6) * S, (by + r * 0.6) * S], 190, 260, fill=(255, 255, 255, a), width=S)
    _comp(img, lay.resize(box, Image.LANCZOS), (x - box[0] / 2, y - box[1] + 10 + size * 3))


# ================================== THIS PORTHOLE'S SUBJECT: THE CLAM-SHELL PA
@lru_cache(None)
def _brick_wall(w, h, seed, ragged):
    rs = random.Random(seed)
    bw, bh, mo = 46, 21, 3
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rows = h // bh + 1
    edge = [w - rs.randint(0, 70) if ragged else w for _ in range(rows + 1)]
    for r in range(rows):
        y = r * bh
        lim = min(edge[r], edge[r + 1] + 30)
        x = -(bw // 2) if r % 2 else 0
        d.rectangle([0, y * S, lim * S, (y + bh) * S], fill=PAL["mortar"] + (255,))
        while x < lim:
            x1 = min(x + bw - mo, lim - (rs.randint(0, 14) if ragged else 0))
            if x1 - x > 8:
                f = rs.uniform(0.78, 1.14)
                c = tuple(int(v * f) for v in (PAL["brick"] if rs.random() > 0.14 else (112, 62, 56)))
                d.rectangle([x * S, (y + 1) * S, x1 * S, (y + bh - mo + 1) * S], fill=c + (255,))
                d.line([x * S, (y + 1) * S, x1 * S, (y + 1) * S], fill=lt(c, 1.25) + (255,), width=S)
                d.line([x * S, (y + bh - mo + 1) * S, x1 * S, (y + bh - mo + 1) * S], fill=dk(c, 0.62) + (255,), width=S)
                d.line([x1 * S, (y + 1) * S, x1 * S, (y + bh - mo + 1) * S], fill=dk(c, 0.7) + (255,), width=S)
            x += bw
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32).copy()
    tex = 1 + 0.10 * vnoise((h, w), 3, None, seed + 1, 2) + 0.10 * vnoise((h, w), 120, None, seed + 2, 3)
    a[..., :3] *= tex[..., None]
    moss = np.clip(vnoise((h, w), 110, 70, seed + 3, 3) * 1.6 + np.linspace(-0.5, 0.45, h)[:, None] - 0.05, 0, 1)
    moss *= (vnoise((h, w), 4, None, seed + 4) > -0.25)
    a[..., :3] = a[..., :3] * (1 - moss[..., None] * 0.8) + np.array([92, 124, 70], np.float32) * moss[..., None] * 0.8
    a[..., :3] *= np.array([0.84, 0.98, 0.94], np.float32)        # under water
    al = a[..., 3] / 255
    a[..., :3] += (60 * np.clip(al - np.roll(al, (1, 1), (0, 1)), 0, 1) - 60 * np.clip(al - np.roll(al, (-1, -1), (0, 1)), 0, 1))[..., None]
    return to_img(a).convert("RGBA")


def brick_wall(target, x=0, y=0, w=330, h=540, seed=0, ragged=True, flip=False, shadow=True):
    """The elementary school's brick wall, mossy, under water. Top-left corner at (x, y); the ragged broken edge is
    on the right (flip=True puts it on the left)."""
    im = _brick_wall(int(w), int(h), int(seed), bool(ragged))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if shadow:
        _comp(target, shadow_of(im.getchannel("A"), 9, 0.34), (x + (-10 if flip else 10), y + 12))
    _comp(target, im, (x, y))


def _valve(sign, seed):
    """One valve of the clam shell (sign -1 upper, +1 lower), hinge at (0, 0), opening to the right:
    a deep half-dome with a scalloped margin, radial ribs from the umbo and growth rings."""
    umbo = (14.0, 8.0)
    margin = []
    for k in range(73):
        ph = math.pi * k / 72
        bump = 1 + 0.022 * math.cos(ph * 34)
        x = 118 - 126 * math.cos(ph)
        y = 8 + 92 * (math.sin(ph) ** 0.72) * (1 - 0.10 * math.cos(ph))
        margin.append((umbo[0] + (x - umbo[0]) * bump, umbo[1] + (y - umbo[1]) * bump))
    inner = [(206, 9), (120, 11), (40, 8)]
    pts = [(px, sign * py) for px, py in margin + inner]

    def at(f):
        return [(umbo[0] + (px - umbo[0]) * f, sign * (umbo[1] + (py - umbo[1]) * f)) for px, py in margin]

    def deco(d, L, S):
        for f, c in ((1.0, PAL["shell"]), (0.86, lt(PAL["shell"], 1.04)), (0.62, dk(PAL["shell"], 0.95)), (0.40, dk(PAL["shell"], 0.90))):   # bands of growth
            d.polygon([L(*p) for p in at(f)] + [L(umbo[0], sign * umbo[1])], fill=c)
        for k in range(2, 72, 4):                                # ribs fanning from the umbo, one to each scallop
            d.line([L(umbo[0], sign * umbo[1]), L(margin[k][0], sign * margin[k][1])], fill=PAL["shell_rib"], width=S)
        for f in (0.40, 0.62, 0.86):
            d.line([L(*p) for p in at(f)], fill=dk(PAL["shell_rib"], 0.92), width=S)
        d.line([L(*p) for p in at(0.985)], fill=dk(PAL["shell_rib"], 0.85), width=S)
        for k in range(8):                                       # the dome turns away toward the commissure
            yb = 9 + k * 2.2
            d.line([L(30, sign * yb), L(232, sign * yb)], fill=dk(PAL["shell"], 0.80 + 0.02 * k), width=3 * S)
    shell = cut(pts, PAL["shell"], deco, curve=False, seed=seed, grain=0.09)
    nac = [(240, 8), (206, 9), (120, 11), (60, 9), (90, 20), (150, 25), (210, 19)]

    def ndeco(d, L, S):
        d.line([L(*p) for p in catmull([(92, sign * 18), (150, sign * 22), (208, sign * 17), (234, sign * 10)], 8)], fill=(236, 240, 236), width=2 * S)
    lip = cut([(px, sign * py) for px, py in nac], PAL["nacre"], ndeco, per=6, seed=seed + 1)
    return compose([shell, lip])


@lru_cache(None)
def _clam():
    P = Puppet()

    def plate_deco(d, L, S):
        for bx, by in ((-18, -30), (-18, 30), (4, -30), (4, 30)):
            d.ellipse([L(bx - 4, by - 4), L(bx + 4, by + 4)], fill=(110, 108, 104), outline=(20, 20, 20), width=S)
    P.add("plate", cut(rrect(-30, -42, 14, 42, 6), (58, 56, 56), plate_deco, curve=False, seed=501), (0, 0), None, 0)

    def horn_deco(d, L, S):
        d.line([L(12, -2), L(150, -4)], fill=PAL["brass_lit"], width=2 * S)
        for x in (150, 162, 174):
            d.line([L(x, -6 - (x - 150) * 0.55), L(x, 6 + (x - 150) * 0.55)], fill=PAL["brass_dark"], width=S)
        d.ellipse([L(180, -20), L(194, 20)], fill=(48, 36, 20))
    P.add("horn", cut([(8, -5), (120, -5), (150, -8), (186, -24), (194, 0), (186, 24), (150, 8), (120, 5), (8, 5)], PAL["brass"], horn_deco, per=6, seed=502), (0, 0), "plate", 1)
    P.add("upper", _valve(-1, 510), (0, 0), "plate", 2)
    P.add("lower", _valve(1, 520), (0, 0), "plate", 3)

    def knob_deco(d, L, S):
        d.ellipse([L(-9, -9), L(9, 9)], fill=lt(PAL["brass"], 1.1), outline=PAL["brass_dark"], width=S)
        d.arc([L(-12, -12), L(12, 12)], 190, 270, fill=(250, 232, 170), width=2 * S)
        d.line([L(-6, -3), L(6, 3)], fill=PAL["brass_dark"], width=2 * S)
    P.add("knob", cut(circ(0, 0, 15), PAL["brass"], knob_deco, curve=False, seed=503), (0, 0), "plate", 4)
    return P


def flap(t, rate=2.0, wide=38.0, rest=3.0):
    """Gape angle (degrees) of a flapping clam shell: snaps open, falls shut, `rate` times a second."""
    u = (t * rate) % 1.0
    return rest + wide * (smooth(ramp(u, 0.0, 0.18)) * (1 - smooth(ramp(u, 0.30, 0.95))))


def clam_pa(target, x, y, scale=1.0, gape=6.0, t=0.0, flip=False, split=1.0, shade=0.0, alpha=1.0):
    """The clam-shell PA loudspeaker: two ribbed valves on ONE brass pin at (x, y) (bolt it to the brick wall),
    opening to the right (flip=True: to the left) over a brass horn. gape = opening in degrees.
    split = share of the gape taken by the lower valve, the jaw (1.0 = only the jaw swings: the Single Hinge rule).
    Returns screen points: hinge, mouth (between the lips), lip_upper, lip_lower."""
    P = _clam()
    fx = -1.0 if flip else 1.0
    pose = {"lower": gape * split, "upper": -gape * (1 - split)}

    def draw(layer, ox, oy):
        return P.draw(layer, pose, Tm(x + ox, y + oy) @ Sm(scale * fx, scale))
    half = int(270 * scale + 20)
    ms = _group(target, x, y, half, draw, shade, alpha, (7 * scale, 10 * scale, 7 * scale, 0.32))

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    lu, ll = pt("upper", (244, -8)), pt("lower", (244, 8))
    return {"hinge": (x, y), "mouth": ((lu[0] + ll[0]) / 2, (lu[1] + ll[1]) / 2), "lip_upper": lu, "lip_lower": ll}


def sound_rings(target, x, y, t=0.0, direction=0.0, n=4, r0=24, r1=250, arc=64, color=(240, 248, 240), strength=1.0, rate=0.8, width=3.0):
    """Arcs of sound spreading from (x, y) toward `direction` (degrees; 0 = right, 180 = left)."""
    if strength <= 0:
        return
    S = 2
    box = int(r1) * 2 + 12
    lay = Image.new("RGBA", (box * S, box * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = box * S / 2
    for k in range(n):
        u = (t * rate + k / n) % 1.0
        r = lerp(r0, r1, u) * S
        a = int(235 * strength * min(1, u * 5) * (1 - u) ** 1.2)
        if a > 2:
            d.arc([c - r, c - r, c + r, c + r], direction - arc / 2, direction + arc / 2, fill=tuple(color) + (a,), width=int(width * S * (1.2 - 0.5 * u)))
    _comp(target, lay.resize((box, box), Image.LANCZOS), (x - box / 2, y - box / 2))


# ------------------------------------------------- the pilot's own things ---
@lru_cache(None)
def _fry(seed):
    rs = random.Random(seed)
    ln, wd = rs.randint(54, 92), rs.randint(11, 15)
    bend = rs.uniform(-7, 7)
    left, right = [], []
    n = ln // 6
    for k in range(n + 1):
        yy = -ln / 2 + ln * k / n
        bx = bend * math.sin(math.pi * k / n)
        z = 2.2 if k % 2 else -0.6                    # the crinkle cut
        left.append((bx - wd / 2 - z, yy))
        right.append((bx + wd / 2 + z, yy))
    pts = left + right[::-1]

    def deco(d, L, S):
        for k in range(n + 1):
            yy = -ln / 2 + ln * k / n
            bx = bend * math.sin(math.pi * k / n)
            if k % 2:
                d.line([L(bx - wd / 2, yy), L(bx + wd / 2, yy)], fill=PAL["fry_dark"], width=S)
        d.line([L(bend * math.sin(math.pi * k / n) - wd * 0.18, -ln / 2 + ln * k / n) for k in range(n + 1)], fill=lt(PAL["fry"], 1.12), width=2 * S)
        for _ in range(7):                             # salt
            sx, sy = rs.uniform(-wd / 3, wd / 3), rs.uniform(-ln / 2 + 4, ln / 2 - 4)
            d.rectangle([L(sx + bend * 0.5, sy), L(sx + bend * 0.5 + 1.2, sy + 1.2)], fill=(252, 250, 240))
        d.polygon([L(*p) for p in [left[0], right[0], (right[0][0], right[0][1] + 5), (left[0][0], left[0][1] + 5)]], fill=(176, 116, 44))
    return cut(pts, tuple(int(v * rs.uniform(0.92, 1.06)) for v in PAL["fry"]), deco, curve=False, seed=600 + seed)


def fry(target, x, y, scale=1.0, angle=0.0, seed=0, shadow=True):
    """One little crinkle-cut french fry, cut paper, centred at (x, y). angle 0 = standing upright."""
    draw_sprite(target, _fry(int(seed) % 12), Tm(x, y) @ Rm(angle) @ Sm(scale), (2.0, 2.8, 1.5, 0.36) if shadow else None)


def fries(target, x, y, t=0.0, n=9, spread=(150, 80), scale=0.7, seed=0, lean=18.0, jitter=1.0):
    """A little school of french fries drifting about (x, y): each bobs and tips on its own.
    Returns the list of their centres."""
    rs = random.Random(seed)
    out = []
    for k in range(n):
        ux, uy = rs.uniform(-1, 1), rs.uniform(-1, 1)
        ph, fr = rs.uniform(0, 6.28), rs.uniform(0.6, 1.2)
        fx_ = x + ux * spread[0] + 7 * jitter * math.sin(t * fr + ph)
        fy_ = y + uy * spread[1] + 9 * jitter * math.sin(t * fr * 1.3 + ph * 2)
        fry(target, fx_, fy_, scale * rs.uniform(0.8, 1.15), lean + rs.uniform(-30, 30) + 14 * jitter * math.sin(t * fr * 1.7 + ph), seed * 5 + k)
        out.append((fx_, fy_))
    return out


@lru_cache(None)
def _padlock():
    P = Puppet()

    def body_deco(d, L, S):
        d.rounded_rectangle([L(-30, 6), L(30, 50)], 6 * S, outline=PAL["brass_dark"], width=2 * S)
        d.line([L(-26, 8), L(26, 8)], fill=PAL["brass_lit"], width=2 * S)
        d.ellipse([L(-7, 16), L(7, 30)], fill=(40, 30, 16))
        d.polygon([L(-4, 26), L(4, 26), L(6, 42), L(-6, 42)], fill=(40, 30, 16))
    P.add("body", cut(rrect(-34, 0, 34, 54, 8), PAL["brass"], body_deco, curve=False, seed=701, grain=0.10), (0, 27), None, 2)
    out = [(22, 4), (22, -22), (12, -40), (0, -44), (-12, -40), (-22, -22), (-22, -4)]
    inn = [(-13, -4), (-13, -20), (-7, -31), (0, -34), (7, -31), (13, -20), (13, 4)]

    def sh_deco(d, L, S):
        d.line([L(*p) for p in catmull([(18, 0), (18, -22), (9, -37), (0, -40)], 6)], fill=(214, 218, 220), width=2 * S)
    P.add("shackle", cut(out + inn, (150, 156, 160), sh_deco, curve=False, seed=702), (17.5, 2), "body", 1)
    return P


def padlock(target, x, y, scale=1.0, open_deg=0.0, swing=0.0):
    """A brass padlock, top of its body at (x, y); the steel shackle rises above. open_deg swings the shackle
    open on its ONE leg (Single Hinge). swing tilts the whole lock about (x, y)."""
    P = _padlock()

    def draw(layer, ox, oy):
        return P.draw(layer, {"shackle": (open_deg, 0, -6 if open_deg else 0)}, Tm(x + ox, y + oy) @ Rm(swing) @ Sm(scale))
    _group(target, x, y, int(90 * scale + 14), draw, drop=(4 * scale, 6 * scale, 4 * scale, 0.32))


def confetti(target, t=0.0, n=70, seed=0, box=(0, 0, W, H), fall=40.0):
    """Cut-paper confetti tumbling down through `box` (x0, y0, x1, y1), looping. For a dance party."""
    rs = random.Random(seed)
    x0, y0, x1, y1 = box
    S = 2
    lay = Image.new("RGBA", (int(x1 - x0) * S, int(y1 - y0) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cols = [PAL["green"], PAL["red"], PAL["blue"], PAL["pink"], PAL["amber"], PAL["ivory"]]
    for k in range(n):
        px = rs.uniform(0, x1 - x0)
        sp = rs.uniform(0.6, 1.4)
        py = (rs.uniform(0, y1 - y0) + t * fall * sp) % (y1 - y0)
        px += 14 * math.sin(t * sp * 2 + k)
        a = t * 3 * sp + k
        w, h = rs.uniform(4, 8), rs.uniform(2.5, 5)
        hh = h * abs(math.cos(a * 1.3)) + 0.8
        ca, sa = math.cos(a), math.sin(a)
        c = cols[k % len(cols)]
        quad = [(px + (ux * ca - uy * sa), py + (ux * sa + uy * ca)) for ux, uy in ((-w, -hh), (w, -hh), (w, hh), (-w, hh))]
        d.polygon([(qx * S + 2 * S, qy * S + 3 * S) for qx, qy in quad], fill=(8, 10, 12, 70))
        d.polygon([(qx * S, qy * S) for qx, qy in quad], fill=c + (255,))
    _comp(target, lay.resize((int(x1 - x0), int(y1 - y0)), Image.LANCZOS), (x0, y0))


@lru_cache(None)
def _note(kind):
    col = (236, 240, 232)
    head = cut(circ(0, 0, 9, 20, 7), col, curve=False, seed=710)
    stem = cut([(6, 0), (9, 0), (9, -40), (6, -40)], col, curve=False, seed=711)
    flag = cut([(9, -40), (24, -30), (22, -18), (18, -26), (9, -30)], col, per=5, seed=712)
    if kind == 0:
        return compose([head, stem, flag])
    head2 = cut(circ(30, -6, 9, 20, 7), col, curve=False, seed=713)
    stem2 = cut([(36, -6), (39, -6), (39, -46), (36, -46)], col, curve=False, seed=714)
    beam = cut([(6, -40), (39, -46), (39, -38), (6, -32)], col, curve=False, seed=715)
    return compose([head, stem, head2, stem2, beam])


def music_note(target, x, y, scale=1.0, angle=0.0, kind=0):
    """A cut-paper music note (kind 0 = single, 1 = a beamed pair), note head at (x, y)."""
    draw_sprite(target, _note(kind % 2), Tm(x, y) @ Rm(angle) @ Sm(scale))


# ============================================ THE TABLE, THE SHEET, THE PENCIL
@lru_cache(None)
def _table():
    h, w = H, W
    grain = vnoise((h, w), 420, 5, 1, 3)
    rings = np.sin((vnoise((h, w), 900, 40, 2, 2) * 9 + np.linspace(0, 40, h)[:, None]) * 2.2)
    a = np.array(PAL["table"], np.float32)[None, None, :] * (1 + 0.10 * grain[..., None] + 0.05 * rings[..., None])
    for y in (60, 186, 320, 452):
        a[y - 1:y + 1] *= 0.55
        a[y + 1:y + 3] *= 1.12
    rs = np.random.RandomState(5)
    for _ in range(90):
        x, y = rs.randint(0, w), rs.randint(0, h)
        a[y:y + rs.randint(1, 3), x:x + rs.randint(1, 4)] += rs.uniform(10, 50)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a *= (1.12 - 0.42 * np.clip(np.hypot((xx - 410) / 750, (yy - 215) / 500), 0, 1.4) ** 1.6)[..., None]
    return to_img(a).convert("RGB")


def table(target):
    """The wooden table under one lamp. Fills the frame."""
    img = _img(target)
    if img.mode == "RGBA":
        img.alpha_composite(_table().convert("RGBA"))
    else:
        img.paste(_table(), (0, 0))


@lru_cache(None)
def _page(w, h):
    a = np.array(PAL["page"], np.float32)[None, None, :] * (1 + 0.022 * vnoise((h, w), 2.0, None, 801, 2) + 0.03 * vnoise((h, w), 180, None, 802, 3)
                                                             + 0.012 * fibre_tex()[:h, :w] if (h <= 900 and w <= 900) else
                                                             1 + 0.022 * vnoise((h, w), 2.0, None, 801, 2) + 0.03 * vnoise((h, w), 180, None, 802, 3))[..., None]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a *= (1.03 - 0.10 * np.clip(np.hypot((xx - w * 0.3) / w, (yy - h * 0.35) / h), 0, 1))[..., None]
    im = to_img(a).convert("RGBA")
    return im


PAGE_BOX = (150, -40, 1010, 600)


def page(target, box=PAGE_BOX, angle=0.0):
    """A sheet of worksheet paper lying on the table, box = (x0, y0, x1, y1), with its shadow. Blank: print
    the ring on it with sheet_ring and draw on it with pilot_drawing / pencil_line."""
    x0, y0, x1, y1 = [int(v) for v in box]
    im = _page(x1 - x0, y1 - y0)
    if angle:
        im = im.rotate(angle, Image.BICUBIC, expand=True)
    _comp(target, shadow_of(im.getchannel("A"), 10, 0.45), (x0 + 8, y0 + 12))
    _comp(target, im, (x0, y0))


def desk(target, box=PAGE_BOX):
    """table() + page() in one call."""
    table(target)
    page(target, box)


# The printed porthole ring of the worksheet, in the child's sheet's own proportions.
# Units below are photograph pixels measured from the ring's centre; `scale` turns them into screen pixels.
SHEET_R_IN, SHEET_R_OUT = 214.0, 264.0
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


def sheet_ring(target, cx, cy, scale=0.8, lit=(), empty=(), t=0.0, alpha=1.0):
    """The worksheet's printed porthole: two thin circles and six little dice for bolts (1 at the top, clockwise).
    lit = bolt numbers glowing amber (written endings); empty = bolts shown as an empty dashed box (unwritten).
    Returns {k: (x, y)} bolt centres."""
    S = 2
    ro = SHEET_R_OUT * scale
    n = int(ro * 2 + 90 * scale + 60)
    lay = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = n * S / 2
    ink = (44, 42, 44, int(235 * alpha))
    for r in (SHEET_R_IN * scale, ro):
        d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], outline=ink, width=max(2, int(1.6 * S * scale + 1)))
    pos = {}
    hb = 21 * scale
    for k in range(1, 7):
        bx, by = bolt_xy(k, 0, 0, SHEET_R_IN * scale, ro)
        pos[k] = (cx + bx, cy + by)
        X, Y = c + bx * S, c + by * S
        fill = (255, 226, 150, int(255 * alpha)) if k in lit else (250, 247, 239, int(255 * alpha))
        if k in empty:
            d.rounded_rectangle([X - hb * S, Y - hb * S, X + hb * S, Y + hb * S], 5 * scale * S, fill=(250, 247, 239, int(255 * alpha)))
            for j in range(12):
                a0 = j * 30
                d.arc([X - hb * S * 1.1, Y - hb * S * 1.1, X + hb * S * 1.1, Y + hb * S * 1.1], a0, a0 + 16, fill=(120, 116, 112, int(235 * alpha)), width=max(2, int(S * scale + 1)))
            continue
        d.rounded_rectangle([X - hb * S, Y - hb * S, X + hb * S, Y + hb * S], 5 * scale * S, fill=fill, outline=ink, width=max(2, int(1.8 * S * scale + 1)))
        for (px, py) in PIPS[k]:
            pr = 3.4 * scale * S
            d.ellipse([X + px * hb * 0.52 * S - pr, Y + py * hb * 0.52 * S - pr, X + px * hb * 0.52 * S + pr, Y + py * hb * 0.52 * S + pr], fill=ink)
    for k in lit:
        glow(target, pos[k][0], pos[k][1], 46 * scale + 14, (255, 190, 70), 0.8 + 0.12 * math.sin(t * 4 + k))
    _comp(target, lay.resize((n, n), Image.LANCZOS), (cx - n / 2, cy - n / 2))
    return pos


# The pilot's drawing, traced by eye from the child's sheet: photograph pixels from the ring's centre (752, 772).
_RC = (752.0, 772.0)
_JAW = [    # (points, pencil weight 0..1, sharp corners?)   the slanted box, then the row of teeth
    ([(632, 666), (670, 650), (720, 635), (780, 628), (848, 622)], 0.55, False),
    ([(670, 650), (660, 683), (648, 717), (645, 760), (652, 800), (660, 822)], 0.55, False),
    ([(645, 808), (717, 790), (793, 767), (860, 742), (873, 743)], 0.45, False),
    ([(660, 798), (747, 783), (847, 760), (910, 753)], 0.40, False),
    ([(645, 808), (710, 802), (773, 780), (887, 752)], 0.45, False),
    ([(625, 661), (657, 705), (690, 737), (717, 782)], 1.0, False),
    ([(717, 782), (712, 747), (712, 717), (722, 695)], 0.6, False),
    ([(670, 649), (710, 695), (733, 707), (773, 757)], 1.0, False),
    ([(722, 634), (722, 660), (727, 693)], 0.6, False),
    ([(722, 634), (760, 670), (787, 693), (835, 753)], 1.0, False),
    ([(773, 757), (768, 707), (780, 690), (777, 643), (780, 628)], 0.6, False),
    ([(780, 628), (823, 675), (873, 743)], 1.0, False),
    ([(818, 618), (817, 643), (827, 670), (817, 683), (823, 720), (835, 753)], 0.6, False),
]
_OUT = [    # the second, looser jaw drawn outside the ring to the right
    ([(1107, 673), (1210, 670), (1273, 663), (1350, 660), (1397, 657)], 0.45, False),
    ([(1110, 675), (1137, 737), (1152, 660), (1195, 735), (1207, 668), (1247, 717), (1268, 728), (1273, 665), (1307, 710), (1343, 743),
      (1346, 677), (1350, 660), (1400, 720), (1413, 663)], 0.9, True),
    ([(1140, 807), (1148, 730), (1207, 810), (1203, 760), (1220, 737), (1267, 785), (1265, 743), (1280, 723), (1347, 788), (1370, 725),
      (1413, 770), (1440, 813)], 0.9, True),
    ([(1137, 810), (1170, 802), (1213, 787), (1293, 795), (1353, 800), (1423, 793)], 0.4, False),
]
_MARKS = {   # the friends' own drawn picks (back of the sheet), in photograph px from the mark's own centre
    "circle": [([(6, -20), (-6, -21), (-13, -10), (-14, 6), (-9, 18), (1, 21), (11, 14), (14, 0), (12, -12), (9, -16)], 0.8, False)],     # a tall oval, not quite shut
    "square": [([(-12, -9), (13, -11), (14, 8), (-13, 10), (-12, -8)], 0.8, True)],                                                   # a small square, a little lopsided
}
PILOT_STROKES = [dict(pts=[(x - _RC[0], y - _RC[1]) for x, y in p], weight=w, sharp=s, part="jaw") for p, w, s in _JAW] + \
                [dict(pts=[(x - _RC[0], y - _RC[1]) for x, y in p], weight=w, sharp=s, part="outside") for p, w, s in _OUT]
JAW_SHARE = 0.56        # of progress 0..1 with part="all", the first 56% draws the jaw in the ring


def _dense(st):
    rs = random.Random(int(st["pts"][0][0] * 7 + st["pts"][0][1]))
    pts = st["pts"]
    if not st["sharp"]:
        return catmull(pts, 10)
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):      # straight runs that bow a little, corners kept
        L = math.hypot(bx - ax, by - ay) or 1
        k = rs.gauss(0, 0.03) * L
        for j in range(8):
            u = j / 8
            out.append((ax + (bx - ax) * u - (by - ay) / L * k * math.sin(math.pi * u), ay + (by - ay) * u + (bx - ax) / L * k * math.sin(math.pi * u)))
    out.append(pts[-1])
    return out


@lru_cache(None)
def _pilot(scale_q, part):
    """Pencil mask for the drawing at a scale: (x0, y0, alpha, arrival, path) where arrival is the progress
    (0..1) at which each grain of graphite lands and path = [(p, x, y, down)] for the pencil tip."""
    sc = scale_q / 100.0
    if part in _MARKS:
        strokes = [dict(pts=p, weight=w, sharp=sh, part=part) for p, w, sh in _MARKS[part]]
    else:
        strokes = [s for s in PILOT_STROKES if part == "all" or s["part"] == part]
    dense = [np.array(_dense(s), np.float32) * sc for s in strokes]
    lens = [float(np.hypot(*(d[1:] - d[:-1]).T).sum()) for d in dense]
    hop = [0.0] + [float(np.hypot(*(dense[k][0] - dense[k - 1][-1]))) * 0.5 + 18 * sc for k in range(1, len(dense))]
    if part == "all":       # the jaw takes JAW_SHARE of the time, the outside one the rest
        nj = sum(1 for s in strokes if s["part"] == "jaw")
        tj = sum(lens[:nj]) + sum(hop[:nj])
        to = sum(lens[nj:]) + sum(hop[nj:])
        rate = [JAW_SHARE / tj] * nj + [(1 - JAW_SHARE) / to] * (len(strokes) - nj)
    else:
        rate = [1.0 / (sum(lens) + sum(hop))] * len(strokes)
    allp = np.concatenate(dense)
    pad = 10
    x0, y0 = int(allp[:, 0].min()) - pad, int(allp[:, 1].min()) - pad
    w, h = int(allp[:, 0].max()) + pad - x0, int(allp[:, 1].max()) + pad - y0
    arr = np.full((h, w), 9.0, np.float32)
    alpha = np.zeros((h, w), np.float32)
    path = []
    p = 0.0
    for k, (s, d) in enumerate(zip(strokes, dense)):
        p += hop[k] * rate[k]
        seg = np.hypot(*(d[1:] - d[:-1]).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        nstep = max(2, int(cum[-1] / 0.7))
        ss = np.linspace(0, cum[-1], nstep)
        xs, ys = np.interp(ss, cum, d[:, 0]) - x0, np.interp(ss, cum, d[:, 1]) - y0
        a_im = Image.new("F", (w, h), 9.0)
        dd = ImageDraw.Draw(a_im)
        wd = (2.1 + 1.5 * s["weight"]) * sc + 0.5
        for j in range(nstep - 1, -1, -1):
            u = j / (nstep - 1)
            r = wd / 2 * (0.78 + 0.22 * math.sin(j * 0.21 + k)) * (0.6 + 0.4 * min(1, u * 12 + 0.3) * min(1, (1 - u) * 10 + 0.4))
            dd.ellipse([xs[j] - r, ys[j] - r, xs[j] + r, ys[j] + r], fill=float(p + ss[j] * rate[k]))
        A = np.asarray(a_im, np.float32)
        solid = (A < 8).astype(np.float32)
        soft = blur_arr(solid, 0.7)
        al = soft * (0.50 + 0.45 * s["weight"])
        arr = np.where(solid > 0, np.minimum(arr, A), arr)
        fringe = (soft > 0.02) & (arr > 8)
        arr[fringe] = p + cum[-1] * rate[k]
        alpha = np.maximum(alpha, al)
        for j in range(0, nstep, 3):
            path.append((p + ss[j] * rate[k], float(xs[j] + x0), float(ys[j] + y0), True))
        p += cum[-1] * rate[k]
        path.append((p, float(xs[-1] + x0), float(ys[-1] + y0), False))
    tooth = 0.72 + 0.38 * vnoise((h, w), 1.5, None, 811) + 0.12 * vnoise((h, w), 9, None, 812)
    alpha = np.clip(alpha * tooth, 0, 1)
    return x0, y0, alpha, arr, path


def pilot_drawing(target, cx, cy, progress=1.0, scale=0.8, part="all", alpha=1.0):
    """The pilot's pencil drawing, drawn as far as `progress` (0..1), stroke by stroke in the child's order.
    (cx, cy) = centre of the sheet's porthole ring; scale = screen px per photograph px (ring glass radius =
    214 * scale). part: "all" (the jaw in the ring, then the looser jaw outside to the right, which reaches
    from 355 to 690 photograph px right of centre), "jaw" or "outside"."""
    x0, y0, al, arr, _ = _pilot(int(round(scale * 100)), part)
    a = al * (arr <= progress) * alpha
    g = np.zeros(al.shape + (4,), np.uint8)
    g[..., :3] = PAL["graphite"]
    g[..., 3] = (a * 255).astype(np.uint8)
    _comp(target, Image.fromarray(g, "RGBA"), (cx + x0, cy + y0))


def pilot_tip(cx, cy, progress, scale=0.8, part="all"):
    """Where the pencil point is at `progress`: (x, y, down). down is False while it hops between strokes."""
    path = _pilot(int(round(scale * 100)), part)[4]
    if progress <= path[0][0]:
        return (cx + path[0][1], cy + path[0][2], False)
    for (p0, xa, ya, d0), (p1, xb, yb, d1) in zip(path, path[1:]):
        if p0 <= progress <= p1:
            u = (progress - p0) / (p1 - p0) if p1 > p0 else 0
            return (cx + lerp(xa, xb, u), cy + lerp(ya, yb, u), bool(d0))
    return (cx + path[-1][1], cy + path[-1][2], False)


def friend_mark(target, kind, cx, cy, progress=1.0, scale=1.6):
    """The friend's own pencil drawing of the pick, centred at (cx, cy): kind "circle" (first friend: a tall oval not
    quite shut) or "square" (next friend: a small lopsided square). About 28 x 42 / 27 x 21 px times scale."""
    pilot_drawing(target, cx, cy, progress, scale, part=kind)


def friend_tip(kind, cx, cy, progress, scale=1.6):
    """Pencil point for friend_mark: (x, y, down)."""
    return pilot_tip(cx, cy, progress, scale, part=kind)


@lru_cache(None)
def _pencil():
    def body_deco(d, L, S):
        d.polygon([L(44, -7.5), L(214, -7.5), L(214, -2.5), L(44, -2.5)], fill=(250, 214, 96))
        d.polygon([L(44, 2.5), L(214, 2.5), L(214, 7.5), L(44, 7.5)], fill=(196, 150, 40))
        d.text(L(150, 0), "No. 2", font=font("mono", 7 * S), fill=(90, 70, 20), anchor="mm")
    body = cut([(44, -7.5), (214, -7.5), (214, 7.5), (44, 7.5)], (232, 186, 62), body_deco, curve=False, seed=821)

    def cone_deco(d, L, S):
        d.polygon([L(0, 0), L(13, -2.2), L(13, 2.2)], fill=(52, 50, 56))
        for k in range(3):
            d.line([L(14, -2 + k * 2), L(44, -6 + k * 6)], fill=(196, 160, 110), width=S)
    cone = cut([(0, 0), (44, -7.5), (44, 7.5)], (226, 192, 142), cone_deco, curve=False, seed=822)

    def fer_deco(d, L, S):
        for x in (218, 224, 230):
            d.line([L(x, -8), L(x, 8)], fill=(120, 124, 126), width=S)
    fer = cut([(214, -8), (236, -8), (236, 8), (214, 8)], (176, 180, 182), fer_deco, curve=False, seed=823)
    rub = cut(rrect(236, -7.5, 258, 7.5, 4), (226, 132, 138), curve=False, seed=824)
    return compose([rub, body, cone, fer])


def pencil(target, x, y, angle=-52.0, lift=0.0, scale=1.0):
    """A yellow pencil with its point at (x, y), lying away along `angle` degrees (-52 = up and to the right).
    lift (px) raises it off the paper: the shadow slides away and softens."""
    sp = _pencil()
    M = Tm(x - lift * 0.1, y - lift * 0.35) @ Rm(angle) @ Sm(scale)
    img = _img(target)
    tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_sprite(tmp, sp, M, None)
    _comp(target, shadow_of(tmp.getchannel("A"), 2.5 + lift * 0.12, 0.42 * (1 - min(0.5, lift / 120))), (5 + lift * 0.5, 7 + lift * 0.9))
    _comp(target, tmp, (0, 0))


def pencil_line(target, xy, text, size=30, progress=1.0, width=None, seed=0, color=None):
    """A line of the child's words written in pencil (kit_anim.hand_text), letters appearing with progress 0..1.
    Returns the y under the last line."""
    n = int(round(len(text) * clamp(progress)))
    if n <= 0:
        return xy[1]
    return KA.hand_text(target if hasattr(target, "paste") and hasattr(target, "img") else _InkShim(target), xy, text[:n], size, color or PAL["graphite"], width, seed)


class _InkShim:
    """Lets kit_anim.hand_text write on a bare PIL image."""

    def __init__(self, img):
        self.img = img

    def paste(self, im, xy=(0, 0), alpha=1.0):
        im = im.convert("RGBA")
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        _comp(self.img, im, xy)


# =========================================== HINGED CARDS, BRADS, SPRINGS
def settle(t, t0, amp=1.0, freq=2.2, damp=4.5):
    """Secondary motion: what a loose thing does after its parent stops at t0. A damped swing that starts at
    `amp` and is at rest inside about a second: amp * exp(-damp * dt) * cos(2 pi freq dt). 0 before t0."""
    dt = t - t0
    if dt < 0:
        return 0.0
    return amp * math.exp(-damp * dt) * math.cos(2 * math.pi * freq * dt)


@lru_cache(None)
def _brad(r):
    S = 3
    n = (r + 3) * 2
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n * S / 2
    d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], fill=PAL["brass"] + (255,), outline=PAL["brass_dark"] + (255,), width=S)
    d.ellipse([c - r * S * 0.62, c - r * S * 0.66, c + r * S * 0.30, c + r * S * 0.26], fill=lt(PAL["brass"], 1.22) + (255,))
    d.ellipse([c - r * S * 0.42, c - r * S * 0.50, c - r * S * 0.02, c - r * S * 0.10], fill=(255, 244, 200, 255))
    return im.resize((n, n), Image.LANCZOS)


def brad(target, x, y, r=7):
    """A brass paper fastener (the visible pin of a hinge), domed head centred at (x, y)."""
    b = _brad(int(r))
    _comp(target, shadow_of(b.getchannel("A"), 1.5, 0.5), (x - b.size[0] / 2 + 1.5, y - b.size[1] / 2 + 2.5))
    _comp(target, b, (x - b.size[0] / 2, y - b.size[1] / 2))


def swing_card(target, img, pin, angle=0.0, at=None, pinned=True, shadow=0.42):
    """Lay a flat card (any PIL image: a pick card, or a whole 960 x 540 scene) turned about ONE pin.
    pin = the pin's place on the card (card px); at = where that pin sits on screen (default: the same place);
    angle in degrees, clockwise, 0 = square to the frame. A brass brad marks the pin."""
    at = pin if at is None else at
    card = img.convert("RGBA")
    M = Tm(at[0], at[1]) @ Rm(angle) @ Tm(-pin[0], -pin[1])
    timg = _img(target)
    if abs(angle) < 0.01 and at == pin and card.size == timg.size:
        out = card
    else:
        Mi = np.linalg.inv(M)
        out = card.transform(timg.size, Image.AFFINE, (Mi[0, 0], Mi[0, 1], Mi[0, 2], Mi[1, 0], Mi[1, 1], Mi[1, 2]), resample=Image.BICUBIC)
    if shadow:
        _comp(target, shadow_of(out.getchannel("A"), 9, shadow), (7, 11))
    _comp(target, out, (0, 0))
    if pinned:
        brad(target, at[0], at[1], 7)


@lru_cache(None)
def _card_stock(w, h, color):
    sp = cut(rrect(0, 0, w, h, 10), color, curve=False, seed=871, grain=0.06)
    return sp.img.crop((3, 3, 3 + w, 3 + h))


def pick_card(target, kind, who, pick, initial, angle=0.0, pin_at=(250, 150), size=(460, 240), drawn=1.0, pressed=1.0, lit=1.0, color=None):
    """The pick, on a card that flips up about a brad in its top-left corner: the controller button `kind` (pressed
    in and lit), `who` (e.g. "Turkey thinks") and `pick` (e.g. "Morning intercom") in type, the friend's own
    pencil mark (friend_mark, drawn to `drawn` 0..1) and the friend's `initial` (e.g. "M.").
    pin_at = screen position of the corner brad; angle 0 = card square, -100 or so = swung away out of sight.
    Returns the card's size."""
    w, h = size
    card = _card_stock(w, h, tuple(color or PAL["page"])).copy()
    d = ImageDraw.Draw(card)
    d.text((34, 26), who, font=font("sans", 22), fill=PAL["ink"] + (255,))
    d.text((34, 58), pick, font=font("serif", 40), fill=PAL["ink"] + (255,))
    button(card, kind, 104, h - 84, 52, pressed, lit)
    # the dashed ring the worksheet prints for "Draw the one you pick", and the friend's pencil in it
    mx, my = w - 120, h - 92
    for j in range(24):
        a0 = j * 15
        d.arc([mx - 56, my - 56, mx + 56, my + 56], a0, a0 + 8, fill=(120, 116, 112, 255), width=2)
    friend_mark(card, kind, mx, my, drawn, 1.9)
    if initial and drawn >= 1.0:
        pencil_line(card, (mx + 30, my + 40), initial, 22, 1.0, seed=3)
    swing_card(target, card, (16, 16), angle, pin_at)
    return size


def feather(target, x, y, scale=1.0, angle=0.0):
    """One loose barred turkey feather (50 long at scale 1), quill end at (x, y), pointing up at angle 0."""
    draw_sprite(target, _loose_feather(), Tm(x, y) @ Rm(angle) @ Sm(scale))


@lru_cache(None)
def _plank(w, thick, seed):
    def deco(d, L, S):
        rs = random.Random(seed)
        for k in range(9):
            y = rs.uniform(2, thick - 2)
            d.line([L(*p) for p in catmull([(x, y + rs.uniform(-1.5, 1.5)) for x in range(0, w + 60, 60)], 4)], fill=dk((150, 110, 70), rs.uniform(0.78, 0.95)), width=S)
        d.line([L(0, thick - 2), L(w, thick - 2)], fill=dk((150, 110, 70), 0.6), width=2 * S)
    return cut([(0, 0), (w, 0), (w, thick), (0, thick)], (150, 110, 70), deco, curve=False, seed=seed, grain=0.10)


def plank(target, x0, y, x1, thick=26, seed=0):
    """A wooden shelf board from (x0, y) to (x1, y), `thick` deep below y (for the kitchen shelf of tins)."""
    draw_sprite(target, _plank(int(x1 - x0), int(thick), int(seed)), Tm(x0, y), (3, 6, 5, 0.4))


# ================================================ BUTTONS, DICE, TAGS, BADGE
def _symbol(d, kind, cx, cy, r, color, width):
    if kind == "triangle":
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * 1.05 * math.sin(math.radians(a)) + r * 0.12) for a in (-90, 30, 150)]
        d.line(pts + [pts[0], pts[1]], fill=color, width=width, joint="curve")
    elif kind == "circle":
        d.ellipse([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], outline=color, width=width)
    elif kind == "cross":
        k = r * 0.78
        d.line([cx - k, cy - k, cx + k, cy + k], fill=color, width=width)
        d.line([cx - k, cy + k, cx + k, cy - k], fill=color, width=width)
    elif kind == "square":
        k = r * 0.80
        d.line([(cx - k, cy - k), (cx + k, cy - k), (cx + k, cy + k), (cx - k, cy + k), (cx - k, cy - k), (cx + k, cy - k)], fill=color, width=width, joint="curve")
    elif kind == "hexagon":
        pts = [(cx + r * math.cos(math.radians(60 * j)), cy + r * math.sin(math.radians(60 * j))) for j in range(6)]
        d.line(pts + [pts[0], pts[1]], fill=color, width=width, joint="curve")
    else:
        raise ValueError(kind)


@lru_cache(None)
def _button(kind, r, pressed):
    col = np.array(PAL[BUTTONS[kind]], np.float32)
    S = 2
    n = (r + 6) * 2
    N = n * S
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    dx, dy = (xx - N / 2 + 0.5) / (r * S), (yy - N / 2 + 0.5) / (r * S)
    rr = np.hypot(dx, dy)
    out = np.zeros((N, N, 4), np.float32)
    # the bezel: a dark turned collar
    th = np.arctan2(dy, dx)
    bz = (rr <= 1.0) & (rr > 0.80)
    bshade = 0.55 + 0.5 * (-np.cos(th) * -0.5 + -np.sin(th) * 0.7) * np.where(rr > 0.9, 1, -1)
    out[..., :3] = np.array([44, 42, 46], np.float32)[None, None, :] * np.clip(bshade, 0.25, 1.6)[..., None]
    out[..., 3] = np.clip((1.0 - rr) * r * S + 0.5, 0, 1) * 255
    # the dome
    off = 0.035 * pressed
    ddx, ddy = dx, dy - off
    dr = np.hypot(ddx, ddy) / 0.78
    dome = dr <= 1.0
    nz = np.sqrt(np.clip(1 - (dr * 0.86) ** 2, 0, 1))
    diff = np.clip(ddx / 0.78 * 0.86 * -0.45 + ddy / 0.78 * 0.86 * -0.62 + nz * 0.64, 0, 1)
    shade = (0.50 + 0.72 * diff) * (1 - 0.22 * pressed)
    spec = np.clip(1 - np.hypot(ddx / 0.78 + 0.36, ddy / 0.78 + 0.44) / 0.34, 0, 1) ** 2 * (1 - 0.5 * pressed)
    dcol = col[None, None, :] * shade[..., None] + spec[..., None] * 150
    m = np.clip((1.0 - dr) * 0.78 * r * S + 0.5, 0, 1)[..., None]
    out[..., :3] = out[..., :3] * (1 - m) + dcol * m
    im = to_img(out).convert("RGBA")
    d = ImageDraw.Draw(im)
    cy = N / 2 + off * r * S
    wdt = max(2, int(r * S * 0.085))
    _symbol(d, kind, N / 2 + S * 0.8, cy + S * 1.2, r * S * 0.34, tuple(int(v * 0.45) for v in col) + (190,), wdt)
    _symbol(d, kind, N / 2, cy, r * S * 0.34, (255, 252, 244, 255), wdt)
    return im.resize((n, n), Image.LANCZOS)


def button(target, kind, x, y, r=40, pressed=0.0, lit=0.0):
    """One controller button, a domed arcade button centred at (x, y): kind = triangle (green), circle (red),
    cross (blue), square (pink), hexagon (amber). pressed 0..1 pushes it in; lit 0..1 puts a halo round it."""
    r = int(r)
    b = _button(kind, r, round(clamp(pressed) * 4) / 4)
    if lit > 0:
        glow(target, x, y, r * 1.9, lt(PAL[BUTTONS[kind]], 1.15), lit)
    _comp(target, shadow_of(b.getchannel("A"), max(2, r * 0.12), 0.5), (x - b.size[0] / 2 + r * 0.08, y - b.size[1] / 2 + r * 0.14))
    _comp(target, b, (x - b.size[0] / 2, y - b.size[1] / 2))


@lru_cache(None)
def _console(scale_q):
    sc = scale_q / 100.0
    w, h = int(330 * sc), int(84 * sc)
    plate = cut(rrect(0, 0, w, h, 14 * sc), (70, 62, 54), lambda d, L, S: [d.ellipse([L(x - 3, y - 3), L(x + 3, y + 3)], fill=(150, 136, 110), outline=(30, 24, 20))
                                                                           for x in (10 * sc, w - 10 * sc) for y in (10 * sc, h - 10 * sc)], curve=False, seed=831, grain=0.12)
    return plate


def controller(target, x, y, scale=1.0, pressed=None, press=1.0, lit=1.0):
    """The five-button controller: a riveted plate centred at (x, y) carrying triangle, circle, cross, square,
    hexagon from left to right. pressed = the kind being pushed (press 0..1 how far, lit 0..1 its halo).
    Returns {kind: (x, y)} button centres."""
    plate = _console(int(round(scale * 100)))
    w, h = plate.img.size[0] - 6, plate.img.size[1] - 6
    draw_sprite(target, plate, Tm(x - w / 2, y - h / 2), (3, 5, 4, 0.4))
    pos = {}
    for k, kind in enumerate(BUTTONS):
        bx = x + (k - 2) * 62 * scale
        pos[kind] = (bx, y)
        on = kind == pressed
        button(target, kind, bx, y, 26 * scale, press if on else 0.0, lit if on else 0.0)
    return pos


@lru_cache(None)
def _die(n, size):
    S = 3
    N = size * S
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    rad = 0.20 * N
    qx, qy = np.abs(xx - N / 2 + 0.5) - (N / 2 - rad), np.abs(yy - N / 2 + 0.5) - (N / 2 - rad)
    dist = np.hypot(np.clip(qx, 0, None), np.clip(qy, 0, None)) + np.minimum(np.maximum(qx, qy), 0) - rad     # signed distance to the rounded square
    bev = np.clip(-dist / (0.10 * N), 0, 1)
    gx, gy = np.gradient(bev)
    shade = 0.94 + 2.2 * (-gx * 0.62 - gy * 0.45) * N / 30 + 0.02 * vnoise((N, N), 4, None, 841)
    a = np.zeros((N, N, 4), np.float32)
    a[..., :3] = np.array(PAL["ivory"], np.float32)[None, None, :] * np.clip(shade, 0.55, 1.12)[..., None]
    a[..., 3] = np.clip(-dist + 0.5, 0, 1) * 255
    im = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(im)
    pr = N * 0.085
    for (px, py) in PIPS[n]:
        X, Y = N / 2 + px * N * 0.25, N / 2 + py * N * 0.25
        d.ellipse([X - pr, Y - pr, X + pr, Y + pr], fill=(30, 28, 30, 255))
        d.arc([X - pr, Y - pr, X + pr, Y + pr], 20, 110, fill=(150, 144, 132, 255), width=max(1, S // 2 + 1))
    return im.resize((size, size), Image.LANCZOS)


def die(target, n, x, y, size=44, angle=0.0, shadow=True):
    """One face of an ivory die (n = 1..6) centred at (x, y); angle in degrees."""
    im = _die(int(n), int(size))
    if angle:
        im = im.rotate(-angle, Image.BICUBIC, expand=True)
    if shadow:
        _comp(target, shadow_of(im.getchannel("A"), max(2, size * 0.08), 0.5), (x - im.size[0] / 2 + size * 0.07, y - im.size[1] / 2 + size * 0.11))
    _comp(target, im, (x - im.size[0] / 2, y - im.size[1] / 2))


@lru_cache(None)
def _cup(r):
    S = 2
    n = (r + 8) * 2
    N = n * S
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    rr = np.hypot(xx - N / 2, yy - N / 2) / (r * S)
    th = np.arctan2(yy - N / 2, xx - N / 2)
    a = np.zeros((N, N, 4), np.float32)
    leather = np.array([120, 74, 44], np.float32)
    rim = (rr > 0.80)
    lightdir = -np.cos(th) * -0.5 + -np.sin(th) * 0.7
    shade = np.where(rim, 0.85 + 0.35 * lightdir * np.where(rr > 0.9, 1, -1), 0.30 + 0.30 * np.clip(rr / 0.8, 0, 1) ** 2 - 0.18 * lightdir * np.clip(rr / 0.8, 0, 1))
    shade = shade * (1 + 0.10 * vnoise((N, N), 5, None, 851, 2))
    a[..., :3] = leather[None, None, :] * shade[..., None]
    a[..., 3] = np.clip((1 - rr) * r * S + 0.5, 0, 1) * 255
    im = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(im)
    for k in range(40):     # the stitching round the rim
        an = 2 * math.pi * k / 40
        r0 = r * S * 0.90
        d.line([N / 2 + math.cos(an) * r0, N / 2 + math.sin(an) * r0, N / 2 + math.cos(an + 0.07) * r0, N / 2 + math.sin(an + 0.07) * r0], fill=(226, 200, 150, 255), width=S + 1)
    return im.resize((n, n), Image.LANCZOS)


def die_cup(target, x, y, r=62, n=5, t=0.0, rattle=0.0):
    """A leather dice cup seen from above, centred at (x, y), with the die lying inside it: not yet thrown.
    n = the face that shows; rattle 0..1 makes the die jitter in the cup."""
    cup = _cup(int(r))
    _comp(target, shadow_of(cup.getchannel("A"), 9, 0.5), (x - cup.size[0] / 2 + 7, y - cup.size[1] / 2 + 10))
    _comp(target, cup, (x - cup.size[0] / 2, y - cup.size[1] / 2))
    jx, jy = rattle * 4 * math.sin(t * 31), rattle * 4 * math.sin(t * 27 + 1)
    die(target, n, x + 2 + jx, y + 3 + jy, int(r * 0.72), 18 + rattle * 20 * math.sin(t * 23))


@lru_cache(None)
def _tag(text):
    f = font("serif", 29 * 3)
    tw = int(f.getlength(text) / 3) + 30
    return cut(rrect(0, 0, tw, 44, 7), (236, 228, 204), lambda d, L, S: d.text(L(tw / 2, 21.5), text, font=font("serif", 29 * S), fill=(52, 44, 38), anchor="mm"),
               curve=False, seed=861)


def bolt_tag(target, n, x=18, y=14, alpha=1.0):
    """The bolt's label for the top LEFT corner: die face n (1..6) and a paper tag reading Probable (1, 4),
    Plausible (2, 5) or Preposterous (3, 6). (x, y) = top-left corner."""
    die(target, n, x + 27, y + 27, 54)
    draw_sprite(target, _tag(KIND[int(n)]), Tm(x + 66, y + 5), (1.5, 2.5, 2.0, 0.4))


@lru_cache(None)
def _badge(n):
    S = 3
    w, h = 80, 50
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], 12 * S, fill=PAL["badge"] + (238,))
    d.text((w * S / 2, h * S / 2 - S), str(n), font=font("sans", 30 * S), fill=PAL["white"] + (255,), anchor="mm")
    return im.resize((w, h), Image.LANCZOS)


def badge(target, n=PORTHOLE, x=None, y=14):
    """The porthole number, white on a dark rounded badge, in the top RIGHT corner. Call it last, every frame."""
    b = _badge(int(n))
    img = _img(target)
    _comp(target, b, (img.size[0] - b.size[0] - 14 if x is None else x, y))


# ====================================================================== test
def _sheet(images, cols, path, scale=0.5):
    w, h = int(W * scale), int(H * scale)
    rows = (len(images) + cols - 1) // cols
    sh = Image.new("RGB", (cols * (w + 6) + 6, rows * (h + 6) + 6), (60, 60, 60))
    for k, im in enumerate(images):
        sh.paste(im.resize((w, h), Image.LANCZOS), (6 + (k % cols) * (w + 6), 6 + (k // cols) * (h + 6)))
    sh.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/c10_world")
    out.mkdir(parents=True, exist_ok=True)
    from kit import Ink
    frames = []
    for k, p in enumerate((0.15, 0.4, 0.56, 0.8, 1.0)):
        ink = Ink(k, k)
        desk(ink)
        sheet_ring(ink, 400, 262, 0.8)
        pilot_drawing(ink, 400, 262, p, 0.8)
        tx, ty, down = pilot_tip(400, 262, p, 0.8)
        pencil(ink, tx, ty, lift=0 if down else 14)
        badge(ink)
        frames.append(ink.finish())
    ink = Ink(0, 0)
    table(ink)
    page(ink, (60, 40, 900, 600))
    for k, kind in enumerate(BUTTONS):
        button(ink, kind, 150 + k * 150, 150, 44, pressed=1.0 if k == 1 else 0.0, lit=1.0 if k == 1 else 0.0)
    for n in range(1, 7):
        die(ink, n, 150 + (n - 1) * 100, 290, 56, angle=(n - 3) * 6)
    controller(ink, 300, 420, 1.0, pressed="square")
    die_cup(ink, 620, 420)
    bolt_tag(ink, 3)
    pencil_line(ink, (480, 380), "freak out", 30)
    badge(ink)
    frames.append(ink.finish())
    for k, a in enumerate((-70, 0)):
        ink = Ink(0, 0)
        cabin(ink, 0, dim=0.3)
        pick_card(ink, "circle" if k == 0 else "square", "Turkey thinks" if k == 0 else "The trout think", "Morning intercom" if k == 0 else "Confiscated lunchbox",
                  "M." if k == 0 else "S.", angle=a, drawn=0.6 + 0.4 * k)
        plank(ink, 0, 500, 300)
        feather(ink, 820, 300, 1.4, 30 + 20 * settle(0.2, 0.0))
        brad(ink, 900, 480)
        badge(ink)
        frames.append(ink.finish())
    _sheet(frames, 3, out / "table.png")
    frames = []
    for k, mood in enumerate(MOODS):
        ink = Ink(1.0 + k * 0.21, k)
        river(ink, 1.0 + k, seed=0)
        brick_wall(ink, 0, 0, 300, 540)
        g = flap(1.0 + k * 0.21)
        c = clam_pa(ink, 262, 200, 0.9, g)
        sound_rings(ink, c["mouth"][0], c["mouth"][1], k * 0.21, strength=1.0)
        trout(ink, 640, 360, 0.55, k * 0.3, kind=k % 4, pose=["swim", "look", "run", "dance"][k % 4], flip=k % 2 == 0)
        fries(ink, 700, 180, k * 0.4, seed=1)
        river_plane(ink, "front", k)
        cabin(ink, k, lit=tuple(range(1, k % 7 + 1)), dim=0.6 if mood == "gasp" else 0)
        air_gauge(ink, 880, 150, 1 - k / 7, 34, k)
        turkey(ink, 150, 470, 1.7, mood, 1.0 + k * 0.21, flip=True, shade=0.2)
        bolt_tag(ink, k % 6 + 1)
        badge(ink)
        ink.caption("The trout to be outside.", size=27)
        frames.append(ink.finish())
    _sheet(frames, 3, out / "cabin.png")
    frames = []
    for k in range(6):
        ink = Ink(k * 0.37, k)
        cam = -120 + 48 * k
        river(ink, k * 0.37, cam, seed=1)
        brick_wall(ink, 640 - cam, 0, 340, 540, seed=2, flip=True)
        c = clam_pa(ink, 700 - cam, 150, 0.8, flap(k * 0.37), flip=True, split=[1.0, 1.0, 0.5][k % 3])
        sound_rings(ink, c["mouth"][0], c["mouth"][1], k * 0.37, direction=180)
        p = tin(ink, 330, 250, 0.95, k * 0.37, mood=MOODS[(k + 2) % len(MOODS)], lid_open=[0, 0, 20, 55, 70, 0][k], guests=[0, 0, 0, 0, 2, 3][k], flip=k == 5,
                door_open=[0, 0, 0, 70, 150, 0][k], latch=[0, 0, 1, 1, 1, 0][k], tag=8 * math.sin(k) if k else None, handle=[None, 0, 0.5, 1, 1, 1][k], dial=1 - k / 5)
        padlock(ink, p["bow"][0] - 4, p["bow"][1] + 2, 0.6, open_deg=[0, 0, 0, 40, 40, 0][k], swing=6 * math.sin(k))
        for j in range(3):
            trout(ink, 160 + j * 200, 430 - 40 * j, 0.5, k * 0.37, kind=j + 1, flip=True, pose=["look", "run", "dance", "swim", "gasp", "point"][(k + j) % 6], phase=j)
        fries(ink, 560, 430, k * 0.37, n=7, seed=3)
        bubbles(ink, p["top"][0], p["top"][1], k * 0.37)
        if k >= 3:
            confetti(ink, k * 0.37)
            music_note(ink, 480, 120, 1.0, 10, k % 2)
        river_plane(ink, "front", k * 0.37, cam, seed=1)
        bolt_tag(ink, k + 1)
        badge(ink)
        frames.append(ink.finish())
    _sheet(frames, 3, out / "river.png")
    ink = Ink(0, 0)
    desk(ink, (120, -40, 1010, 600))
    sheet_ring(ink, 400, 270, 0.9, lit=(1, 2, 3, 4, 5, 6))
    sheet_ring(ink, 800, 150, 0.35, lit=(1, 2), empty=(4, 5, 6))
    pilot_drawing(ink, 400, 270, 1.0, 0.9, part="jaw")
    die_cup(ink, 70, 440, 58)
    badge(ink)
    ink.finish().save(out / "ending.png")
    print("wrote", out)
