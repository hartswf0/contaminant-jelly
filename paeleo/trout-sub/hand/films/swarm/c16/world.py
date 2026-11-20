"""world.py · the shared pieces of class film c16 (porthole 16 · Aft · "Identical twin Turkey Sub waving back").

Everything here is HANDMADE in code, nothing is foraged: every creature and prop is a joint tree of
cut-paper pieces in poster colour (each piece its own sheet with fibre, a lit and a dark cut edge and a
shadow on the piece beneath), the brass and the tin wall are turned / pressed from their own height
profiles, and the pilot's drawing is a list of pencil strokes traced by eye from the child's sheet.
The cut-paper kit, Turkey's side view, the trout, the tin, the river and the table are the ones the class
film c10 set (same world); the rule (D = 12 frames), Turkey's rear and front drawings, the twin, the giant
three-headed monster, the two-headed tin monster and this sheet's pencil strokes are this film's own.

Every public function takes a `target` first: the kit's Ink, or any PIL image (RGB or RGBA).
See WORLD.md for the list, arguments, coordinates and example calls.

    python3 films/swarm/c16/world.py <out_dir>      # writes test stills of every piece
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

PORTHOLE = 16

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


# ------------------------------------------------- THE RULE: TEMPORAL DOUBLE ---
# Everything that moves in this film moves twice: once now, and once again exactly D frames later.
D = 12                  # frames; never tuned by eye
DT = D / FPS            # 0.5 s


def frame_of(t):
    return int(round(t * FPS))


def on_twos(t):
    """Snap a time to the film's 12 poses a second (shot on twos). D is even, so delays survive the snap."""
    return math.floor(t * FPS / 2 + 1e-6) * 2 / FPS


def delayed(fn, t, n=1):
    """Any driven value as it was n * D frames ago: delayed(f, t) == f(t - 0.5)."""
    return fn(t - n * DT)


def doubles(fn, t, n=2):
    """[fn(t), fn(t - DT), fn(t - 2 DT), ...]: a value and its late doubles (three heads: n=3)."""
    return [fn(t - k * DT) for k in range(n)]


def arrive(t, t0):
    """How far a thing that arrives at t0 has got: 0 = not yet, 1 = its pencil outline is there,
    2 = its painted double has landed on it (exactly D frames after the outline)."""
    return 0 if t < t0 else (1 if t < t0 + DT - 1e-6 else 2)


def _energy(e, t):
    return clamp(float(e(t)) if callable(e) else float(e), 0.0, 1.0)


def wave(t, energy=1.0, t0=0.0, beat=1.0):
    """Turkey's wave: how far the wing is raised, in wave-degrees (0 = at rest on the sill, 112 = as high as it goes),
    at time t. One wave per 1 / beat seconds, starting low at t0. `energy` (1.0 fresh .. 0.2 spent; a number or a
    function of time) lowers the reach. Pure function of t."""
    if t < t0:
        return 0.0
    e = _energy(energy, t)
    reach = lerp(22.0, 112.0, e)
    s = math.sin(2 * math.pi * (t - t0) * beat - math.pi / 2)
    return smooth(min(1.0, (t - t0) / 0.3)) * reach * (0.70 + 0.30 * s)


def twin_wave(t, energy=1.0, t0=0.0, beat=1.0):
    """The twin's wing: Turkey's angle read D frames back, mirrored. twin_wave(t) == -wave(t - DT), always."""
    return -wave(t - DT, energy, t0, beat)


def wave_pose(t, energy=1.0, t0=0.0, beat=1.0, twin=False):
    """Keyword arguments for turkey_back / turkey_front / tin: the driven wing and what hangs off it.
    wing = wave (or twin_wave when twin=True); tip, wattle, snood = follow-through, read from where the wing was
    a moment ago (the less energy, the longer the lag: a tired wave settles slowly). Use as
    `Wd.turkey_back(ink, 790, 420, 1.5, **Wd.wave_pose(t, e, 13.0))`."""
    tt = t - DT if twin else t
    e = _energy(energy, tt)
    a = wave(tt, energy, t0, beat)
    lag = lerp(0.22, 0.08, e)
    tip = clamp((wave(tt - lag, energy, t0, beat) - a) * lerp(1.0, 0.55, e), -34, 34)
    wat = clamp((wave(tt - 0.16, energy, t0, beat) - a) * 0.55, -26, 26)
    sn = clamp((wave(tt - 0.24, energy, t0, beat) - a) * 0.45, -22, 22)
    return {"wing": -a if twin else a, "tip": tip, "wattle": wat, "snood": sn, "mirror": bool(twin)}


def needle(t, drops=(), start=1.0, notch=1.0 / 6):
    """The air level at time t: `start`, less one notch for every time in `drops`. Each notch falls as two
    ticks D frames apart (the rule), and each tick overshoots and settles. The level never goes back up."""
    lv = start
    for td in drops:
        for k in range(2):
            dt = t - td - k * DT
            if dt >= 0:
                lv -= notch / 2 * (1 - math.exp(-13 * dt) * math.cos(2 * math.pi * 3.0 * dt))
    return lv


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


# ----------------------------------------------- Turkey, the other two drawings
# Turkey is three drawings on one shoulder pin (Turn Lab): the side view above, the REAR three-quarter view from
# his seat, and the FRONT view seen through a porthole. The waving wing is the same hinged cut in the last two.
WAVE_GAIN = 1.25        # screen degrees per wave-degree (wave 112 -> the wing 140 degrees up from hanging)


def _wave_wing(P, pin, sign, seed, shade=1.0):
    """The waving wing: one cut hanging straight down from `pin`, five primaries each on its own pin at its end.
    sign = +1: its leading edge is on the left (rear view), -1: on the right (front view)."""
    bronze = PAL["turkey_bronze"]
    px, py = pin

    def L_(x, y):
        return (px + sign * x, py + y)

    def deco(d, L, S):
        for k, y in enumerate(range(26, 104, 8)):       # barred secondaries
            d.line([L(*L_(4, y)), L(*L_(-30, y + 8))], fill=(238, 230, 208) if k % 2 else (36, 30, 28), width=4 * S)
        cov = catmull([L_(*p) for p in [(-12, -6), (12, -10), (26, 20), (24, 62), (10, 88), (-4, 60), (-14, 26)]], 8, closed=True)
        d.polygon([L(*p) for p in cov], fill=dk(bronze, 0.62 * shade))
        for row in range(8):
            for col in range(4):
                x, y = -8 + col * 10 + (row % 2) * 5, 2 + row * 11
                cx_, cy_ = L(*L_(x, y))
                d.pieslice([cx_ - 8 * S, cy_ - 8 * S, cx_ + 8 * S, cy_ + 8 * S], 0, 180, fill=dk(bronze, (0.5 + 0.05 * row) * shade), outline=(40, 28, 20), width=S)
    pts = [L_(*p) for p in [(-12, -8), (12, -12), (28, 18), (26, 66), (12, 104), (-22, 112), (-34, 84), (-26, 40), (-18, 10)]]
    P.add("wing", cut(pts, dk((92, 70, 50), shade), deco, per=7, seed=seed), pin, "body", 8)
    for k in range(5):                                  # primaries, fanned at the wrist
        base = L_(-22 + k * 9, 98)

        def fdeco(d, L, S, base=base):
            for j in range(6):
                yb = 8 + j * 8
                d.line([L(base[0] - 7, base[1] + yb), L(base[0] + 7, base[1] + yb + 2)], fill=(240, 232, 210), width=3 * S)
            d.line([L(base[0], base[1]), L(base[0], base[1] + 56)], fill=(20, 16, 14), width=S)
        fp = [(base[0] - 4, base[1] - 4), (base[0] - 8, base[1] + 24), (base[0] - 6, base[1] + 50), (base[0], base[1] + 62),
              (base[0] + 6, base[1] + 50), (base[0] + 8, base[1] + 24), (base[0] + 4, base[1] - 4)]
        P.add(f"tip{k}", cut(fp, dk((44, 36, 32), shade), fdeco, per=6, seed=seed + 1 + k), base, "wing", 7.5 + 0.05 * k)


def _wing_pose(pose, wing, tip, sign):
    a = abs(wing) * WAVE_GAIN
    pose["wing"] = sign * a
    op = clamp(a / 140.0)
    for k in range(5):
        pose[f"tip{k}"] = sign * ((k - 2) * lerp(-2.0, -11.0, op) + tip * (0.55 + 0.16 * k))


@lru_cache(None)
def _turkey_back():
    """Rear three-quarter view, in his seat. Design: shoulder pin (118, 205); he looks up and to the LEFT."""
    P = Puppet()
    side = _turkey()
    body, bronze, skin, red, dkred = PAL["turkey_body"], PAL["turkey_bronze"], PAL["turkey_skin"], PAL["turkey_red"], PAL["turkey_dkred"]
    # tail: seven barred feathers hanging down behind him from the rump (the side view's own cuts, re-pinned)
    for k in range(7):
        P.add(f"tf{k}", side.parts[f"tf{k + 1}"]["spr"], (228, 262), "body", 0.1 + 0.01 * (3 - abs(k - 3)))

    def far_deco(d, L, S):
        for k, y in enumerate(range(238, 330, 8)):
            d.line([L(262, y), L(288, y + 10)], fill=(238, 230, 208) if k % 2 else (36, 30, 28), width=4 * S)
    P.add("wing_far", cut([(246, 200), (272, 214), (290, 262), (294, 318), (276, 344), (256, 322), (246, 262)], dk((92, 70, 50), 0.78), far_deco, per=7, seed=151), (254, 208), "body", 1.2)

    def body_deco(d, L, S):
        rs = random.Random(9)
        for row in range(15):
            for col in range(15):
                x, y = 96 + col * 13 + (row % 2) * 6.5, 176 + row * 13
                c = (96 + rs.randint(-8, 8), 68 + rs.randint(-6, 6), 44) if row > 3 else (72, 96 + rs.randint(-6, 6), 74)
                d.pieslice([L(x - 10, y - 10), L(x + 10, y + 10)], 0, 180, fill=c, outline=(38, 26, 20), width=S)
                d.arc([L(x - 8, y - 4), L(x + 8, y + 9)], 20, 160, fill=bronze, width=S)
        d.line([L(*p) for p in catmull([(190, 176), (196, 240), (198, 300), (192, 372)], 8)], fill=(40, 28, 22), width=2 * S)      # the spine
    P.add("body", cut([(104, 250), (112, 196), (150, 166), (198, 160), (246, 180), (272, 236), (272, 300), (250, 356), (200, 380), (150, 372), (116, 326)],
                      body, body_deco, seed=152), (118, 205), None, 3)

    def neck_deco(d, L, S):
        for k in range(26):
            x, y = 132 + (k * 37) % 44, 96 + (k * 53) % 96
            d.ellipse([L(x - 6, y - 5), L(x + 6, y + 5)], fill=(218, 100, 88) if k % 3 else dkred)
        for k in range(7):                              # the hackle where the feathers start
            x = 138 + k * 9
            d.pieslice([L(x - 9, 168), L(x + 9, 190)], 180, 360, fill=(70, 92, 70), outline=(38, 26, 20), width=S)
    P.add("neck", cut([(142, 196), (134, 150), (128, 112), (138, 92), (166, 90), (176, 116), (186, 152), (206, 190)], red, neck_deco, seed=153), (172, 188), "body", 4)

    # head, drawing A ("glass"): the back of his head, a sliver of face, the beak past it
    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(126, 60), (146, 46), (172, 52), (176, 70), (150, 64)], 8, closed=True)], fill=(176, 200, 216))
        for k in range(14):
            x, y = 134 + (k * 29) % 40, 70 + (k * 17) % 26
            d.ellipse([L(x - 3.5, y - 3.5), L(x + 3.5, y + 3.5)], fill=(126, 154, 178))
        for k in range(6):                              # the red caruncles down the nape
            d.ellipse([L(160 - k * 2 - 5, 84 + k * 4 - 4), L(160 - k * 2 + 5, 84 + k * 4 + 4)], fill=(210, 92, 80))
    P.add("beakA", cut([(124, 70), (92, 84), (124, 86)], PAL["turkey_beak"], curve=False, seed=154), (124, 78), "headA", 4.6)
    P.add("snoodA", cut([(120, 60), (130, 62), (124, 84), (112, 104), (104, 98), (112, 80)], dkred, seed=155), (124, 62), "headA", 4.8)
    P.add("wattleA", cut([(124, 88), (140, 90), (140, 116), (128, 132), (118, 114)], red, seed=156), (130, 90), "headA", 4.7)
    P.add("headA", cut([(120, 80), (122, 58), (140, 44), (164, 46), (180, 62), (180, 86), (166, 102), (140, 104), (126, 96)], skin, head_deco, seed=157), (152, 100), "neck", 5)

    def eye_deco(d, L, S):
        d.ellipse([L(121, 62), L(131, 76)], fill=(246, 242, 228))
        d.ellipse([L(121.5, 66), L(126.5, 73)], fill=(20, 20, 22))
    P.add("eyeA", cut(circ(126, 69, 6.0, 20, 8.5), (120, 150, 176), eye_deco, curve=False, seed=158), (126, 69), "headA", 5.2)
    _wave_wing(P, (118, 205), +1, 160)
    return P


TB_PIN = (118, 205)


def turkey_back(target, x, y, scale=1.0, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, head="glass", t=0.0,
                shade=0.0, alpha=1.0, drop=True, lean=0.0):
    """Turkey from BEHIND, in his seat (rear three-quarter cut-paper drawing). (x, y) = his waving shoulder's pin.
    He sits to the right of the pin and looks up-left at the glass; mirror=True (or a negative wing) is the exact
    mirror image about the vertical through the pin (a turkey sitting to the left, wing rising to the right).
    wing = wave-degrees (see wave()); tip, wattle, snood = follow-through angles (see wave_pose()).
    head: "glass" = back of the head, looking out; "seat" = the profile drawing, turned to look at the seat beside
    him (two drawings swapped on the neck pivot; never tween them).
    Returns screen points: pin, wing_tip, head, neck, crown."""
    P = _turkey_back()
    mirror = (wing < 0) if mirror is None else mirror
    fx = -1.0 if mirror else 1.0
    s = math.sin
    pose = {"neck": 2.0 * s(t * 1.3) + lean, "headA": 2.5 * s(t * 0.9 + 1), "snoodA": 2 * s(t * 1.1) + snood, "wattleA": 3 * s(t * 1.7) + wattle,
            "wing_far": 1.5 * s(t * 1.2)}
    for k in range(7):
        pose[f"tf{k}"] = 180 + (k - 3) * 9.0 + 1.2 * s(t * 2.1 + k)
    _wing_pose(pose, wing, tip, +1)
    side = _turkey()
    skipA = ("headA", "beakA", "snoodA", "wattleA", "eyeA") if head == "seat" else ()

    def draw(layer, ox, oy):
        M = Tm(x + ox, y + oy) @ Sm(scale * fx, scale) @ Rm(lean * 0.3) @ Tm(-TB_PIN[0], -TB_PIN[1])
        ms = P.mats(pose, M)
        for n in P.order:
            if n in skipA:
                continue
            if n.startswith("tf"):                      # the side view's tail cuts, re-pinned at this rump, hanging down
                draw_sprite(layer, P.parts[n]["spr"], ms["body"] @ Tm(196, 344) @ Rm(pose[n]) @ Tm(-228, -262))
                continue
            if n == "tip0" and head == "seat":          # drawing B: the side view's own head pieces, pinned on this neck
                _side_head(layer, side, ms["neck"], t, wattle, snood)
            draw_sprite(layer, P.parts[n]["spr"], ms[n])
        return ms
    half = int(330 * scale + 20)
    ms = _group(target, x, y, half, draw, shade, alpha, (7 * scale, 10 * scale, 7 * scale, 0.34) if drop else None)

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    return {"pin": pt("body", TB_PIN), "wing_tip": pt("tip2", (118 - 4, 205 + 160)), "head": pt("neck", (150, 72)), "neck": pt("neck", (152, 100)),
            "crown": pt("neck", (150, 44))}


def _side_head(layer, side, Mneck, t, wattle, snood):
    """Drawing B of the head: the profile (the side view's head, beak, eye, snood, wattle), turned to the seat beside him."""
    s = math.sin
    ps = {"head": 0.0, "beak": 4.0, "beak2": -5.0, "snood": 2 * s(t * 1.1) + snood, "wattle": 3 * s(t * 1.7) + wattle,
          "eye": (0.0, 0.0, 0.0, 1.15, 1.15), "pupil": (0.0, -1.2, 1.2, 0.8, 0.8), "lid": (0.0, 0.0, -12.0)}
    M = Mneck @ Tm(150, 102) @ Rm(-24) @ Sm(1.0) @ Tm(-106, -112)
    ms = side.mats(ps, M)
    for n in side.order:
        if n in ("head", "wattle", "beak", "beak2", "eye", "pupil", "lid", "snood"):
            draw_sprite(layer, side.parts[n]["spr"], ms[n])


@lru_cache(None)
def _turkey_front():
    """Front view (seen through a porthole). Design: body centre (150, 235); waving shoulder pin (196, 204), on OUR right."""
    P = Puppet()
    side = _turkey()
    body, bronze, skin, red, dkred = PAL["turkey_body"], PAL["turkey_bronze"], PAL["turkey_skin"], PAL["turkey_red"], PAL["turkey_dkred"]
    for k in range(9):                                  # the fan, open behind him
        P.add(f"tf{k}", side.parts[f"tf{k}"]["spr"], (228, 262), "body", 0.1 + 0.01 * (4 - abs(k - 4)))

    def fold_deco(d, L, S):
        for k, y in enumerate(range(214, 296, 8)):
            d.line([L(96, y), L(76, y + 10)], fill=(238, 230, 208) if k % 2 else (36, 30, 28), width=4 * S)
    P.add("wing_far", cut([(104, 196), (84, 214), (72, 262), (76, 304), (96, 316), (108, 280), (112, 230)], dk((92, 70, 50), 0.9), fold_deco, per=7, seed=171), (104, 204), "body", 3.4)

    def body_deco(d, L, S):
        rs = random.Random(11)
        for row in range(13):
            for col in range(11):
                x, y = 92 + col * 12 + (row % 2) * 6, 172 + row * 12
                c = (60 + rs.randint(-6, 6), 44 + rs.randint(-5, 5), 34)
                d.pieslice([L(x - 9, y - 9), L(x + 9, y + 9)], 0, 180, fill=c, outline=(30, 22, 18), width=S)
                d.arc([L(x - 7, y - 3), L(x + 7, y + 8)], 20, 160, fill=dk(bronze, 0.8), width=S)
    P.add("body", cut([(92, 240), (100, 190), (126, 166), (150, 160), (174, 166), (200, 190), (208, 240), (196, 290), (150, 312), (104, 290)],
                      body, body_deco, seed=172), (150, 235), None, 3)
    P.add("beard", cut([(146, 222), (154, 222), (153, 270), (147, 270)], (26, 22, 20), curve=False, seed=173), (150, 223), "body", 3.6)

    def neck_deco(d, L, S):
        for k in range(22):
            x, y = 136 + (k * 37) % 28, 110 + (k * 53) % 70
            d.ellipse([L(x - 5, y - 4), L(x + 5, y + 4)], fill=(218, 100, 88) if k % 3 else dkred)
    P.add("neck", cut([(128, 192), (134, 150), (132, 116), (150, 106), (168, 116), (166, 150), (172, 192), (150, 200)], red, neck_deco, seed=174), (150, 190), "body", 4)

    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(132, 78), (150, 68), (168, 78), (160, 86), (140, 86)], 8, closed=True)], fill=(176, 200, 216))
        for k in range(10):
            x, y = 130 + (k * 29) % 40, 108 + (k * 17) % 10
            d.ellipse([L(x - 3, y - 3), L(x + 3, y + 3)], fill=(126, 154, 178))
    P.add("head", cut([(126, 100), (128, 82), (140, 70), (160, 70), (172, 82), (174, 100), (166, 118), (150, 124), (134, 118)], skin, head_deco, seed=175), (150, 120), "neck", 5)
    P.add("wattle", cut([(141, 118), (159, 118), (162, 140), (150, 158), (138, 140)], red, seed=176), (150, 120), "head", 5.2)
    P.add("beak", cut([(138, 99), (162, 99), (157, 118), (150, 132), (143, 118)], PAL["turkey_beak"], lambda d, L, S: d.line([L(150, 101), L(150, 126)], fill=dk(PAL["turkey_beak"], 0.7), width=S),
                      curve=False, seed=177), (150, 102), "head", 5.5)

    def eye(cx, seed, name):
        def eye_deco(d, L, S):
            d.ellipse([L(cx - 5.5, 90), L(cx + 5.5, 102)], fill=(246, 242, 228))
            d.ellipse([L(cx - 2.6, 92.5), L(cx + 2.6, 99.5)], fill=(20, 20, 22))
            d.ellipse([L(cx - 1.8, 93.2), L(cx - 0.4, 94.8)], fill=(240, 240, 232))
        P.add(name, cut(circ(cx, 96, 7.5, 20, 8.5), (120, 150, 176), eye_deco, curve=False, seed=seed), (cx, 96), "head", 6)
    eye(133, 178, "eyeL")
    eye(167, 179, "eyeR")
    P.add("snood", cut([(146, 90), (155, 90), (160, 106), (168, 130), (162, 140), (154, 118)], dkred, seed=180), (150, 92), "head", 6.4)
    _wave_wing(P, (196, 204), -1, 182)
    return P


TF_PIN = (196, 204)
TF_C = (150, 235)


def _front_pose(wing, tip, wattle, snood, t, fan=0.85):
    s = math.sin
    pose = {"neck": 1.5 * s(t * 1.3), "head": 2.5 * s(t * 0.9 + 1) - 0.03 * abs(wing), "snood": 2 * s(t * 1.1) + snood, "wattle": 3 * s(t * 1.7) + wattle,
            "beard": 3 * s(t * 1.9), "wing_far": 1.5 * s(t * 1.2)}
    for k in range(9):
        pose[f"tf{k}"] = (k - 4) * 21.0 * fan + 1.2 * s(t * 2.1 + k)
    _wing_pose(pose, wing, tip, -1)
    return pose


def _draw_front(layer, M, pose):
    P = _turkey_front()
    ms = P.mats(pose, M)
    for n in P.order:
        if n.startswith("tf"):          # the side view's tail cuts (cut about (228, 262)), re-pinned at this rump
            draw_sprite(layer, P.parts[n]["spr"], ms["body"] @ Tm(150, 222) @ Rm(pose[n]) @ Tm(-228, -262))
        else:
            draw_sprite(layer, P.parts[n]["spr"], ms[n])
    return ms


def turkey_front(target, x, y, scale=1.0, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, t=0.0, fan=0.85,
                 shade=0.0, alpha=1.0, drop=True):
    """Turkey from the FRONT (cut paper): fan open behind him, head on, one wing to wave. (x, y) = the waving
    shoulder's pin (the same pin as turkey_back: cut from one to the other on it). The wing is on OUR right and
    his body centre is 46 * scale to the left of the pin, 31 * scale below; mirror=True (or a negative wing) is
    the exact mirror image about the vertical through the pin: that is the twin.
    wing, tip, wattle, snood: as turkey_back (see wave_pose()). fan 0..1 = how far the tail is spread.
    At scale 1 he is about 300 wide (fan) and 260 tall. Returns screen points: pin, wing_tip, head, body."""
    mirror = (wing < 0) if mirror is None else mirror
    fx = -1.0 if mirror else 1.0
    pose = _front_pose(wing, tip, wattle, snood, t, fan)

    def draw(layer, ox, oy):
        return _draw_front(layer, Tm(x + ox, y + oy) @ Sm(scale * fx, scale) @ Tm(-TF_PIN[0], -TF_PIN[1]), pose)
    half = int(300 * scale + 20)
    ms = _group(target, x, y, half, draw, shade, alpha, (6 * scale, 9 * scale, 6 * scale, 0.30) if drop else None)

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - y))
    return {"pin": pt("body", TF_PIN), "wing_tip": pt("tip2", (196 + 4, 204 + 160)), "head": pt("head", (150, 96)), "body": pt("body", TF_C)}


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
PORT = (450, 236)       # default centre of the porthole seen from Turkey's seat
PORT_R = 186            # glass radius
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
    for k in range(13):         # six notches (and the half notches between them)
        a = math.radians(150 + 240 * k / 12)
        r0 = 0.66 if k % 2 == 0 else 0.80
        d.line([c + math.cos(a) * r * S * r0, c + math.sin(a) * r * S * r0, c + math.cos(a) * r * S * 0.88, c + math.sin(a) * r * S * 0.88], fill=(40, 34, 30, 255), width=S if k % 2 else 2 * S)
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
    a = math.radians(150 + 240 * clamp(level) + 0.8 * math.sin(t * 9))
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
    # the brass pipe on top (the air goes out here, a bubble at a time)
    P.add("pipe", compose([cut(rrect(301, 6, 315, 34, 3), PAL["brass"], curve=False, seed=421),
                           cut(rrect(297, -12, 331, 4, 5), lt(PAL["brass"], 1.1), curve=False, seed=422),
                           cut(rrect(297, 26, 319, 34, 2), PAL["brass_dark"], curve=False, seed=423)]), (308, 32), "lid", 2.85)
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
        for k in range(7):          # six notches
            a = math.radians(150 + 240 * k / 6)
            d.line([L(dc[0] + 10 * math.cos(a), dc[1] + 10 * math.sin(a)), L(dc[0] + 13.5 * math.cos(a), dc[1] + 13.5 * math.sin(a))], fill=(40, 34, 30), width=S)
    P.add("dial", cut(circ(dc[0], dc[1], 18), PAL["brass"], dial_deco, curve=False, seed=418), dc, "body", 4)
    P.add("needle", compose([cut([(dc[0] - 1.6, dc[1] + 4), (dc[0] + 1.6, dc[1] + 4), (dc[0] + 0.6, dc[1] - 13), (dc[0] - 0.6, dc[1] - 13)], (150, 34, 30), curve=False, seed=419, edge=0.3),
                             cut(circ(dc[0], dc[1], 2.6, 12), PAL["brass_dark"], curve=False, seed=420, edge=0.3)]), dc, "dial", 4.5)
    return P


def _tin_window(t, lamp, wing, tip, wattle, snood, mirror, occupants, wing2):
    """What shows in the tin's porthole from the river: the lamplit inside and Turkey, front view, behind the glass."""
    n = WIN_R * 2 + 4
    S = 2
    im = Image.new("RGBA", (n * S, n * S), tuple(int(v * (0.3 + 0.7 * lamp)) for v in (52, 40, 30)) + (255,))
    d = ImageDraw.Draw(im)
    for k in range(10):
        r = n * S * (0.75 - k * 0.06)
        c = tuple(int(v * (0.12 + 0.88 * lamp)) for v in (60 + k * 11, 44 + k * 7, 30 + k * 3))
        d.ellipse([n * S * 0.5 - r, n * S * 0.34 - r, n * S * 0.5 + r, n * S * 0.34 + r], fill=c + (255,))
    if occupants and lamp > 0.02:
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        fx = -1.0 if mirror else 1.0
        c = n * S / 2
        if occupants >= 2:          # "There is another turkey here": two of him in the one window, the second his mirror
            w2 = wing if wing2 is None else wing2
            _draw_front(lay, Tm(c - fx * 0.27 * n * S, n * S * 0.80) @ Sm(-fx * 0.30 * S, 0.30 * S) @ Tm(-TF_C[0], -TF_C[1]), _front_pose(w2, tip, wattle, snood, t - DT, 0.7))
            _draw_front(lay, Tm(c + fx * 0.20 * n * S, n * S * 0.80) @ Sm(fx * 0.30 * S, 0.30 * S) @ Tm(-TF_C[0], -TF_C[1]), _front_pose(wing, tip, wattle, snood, t, 0.7))
        else:
            _draw_front(lay, Tm(c - fx * 0.10 * n * S, n * S * 0.80) @ Sm(fx * 0.40 * S, 0.40 * S) @ Tm(-TF_C[0], -TF_C[1]), _front_pose(wing, tip, wattle, snood, t))
        if lamp < 1:
            a = lay.getchannel("A")
            lay = Image.blend(lay.convert("RGB"), Image.new("RGB", lay.size, (10, 8, 8)), clamp(1 - lamp) * 0.9).convert("RGBA")
            lay.putalpha(a)
        im.alpha_composite(lay)
    im = im.resize((n, n), Image.LANCZOS)
    m = Image.new("L", (n * 2, n * 2), 0)
    ImageDraw.Draw(m).ellipse([4, 4, n * 2 - 4, n * 2 - 4], fill=255)
    im.putalpha(m.resize((n, n), Image.LANCZOS))
    return Sprite(im, TIN_PORT[0] - n // 2, TIN_PORT[1] - n // 2)


def tin(target, x, y, scale=1.0, t=0.0, flip=False, wing=0.0, tip=0.0, wattle=0.0, snood=0.0, mirror=None, occupants=1, wing2=None,
        lamp=1.0, dial=None, pitch=0.0, lid_open=0.0, spin=None, shade=0.0, alpha=1.0, drop=True, door_open=0.0, latch=0.0):
    """Turkey's submersible from the river side: a riveted bread-roll tin with one round six-bolt brass porthole,
    body centre at (x, y). Design faces left (porthole forward); flip=True turns it round: THE TWIN is this same
    function with flip=True and the twin's wave (`**Wd.wave_pose(t, e, t0, twin=True)`).
    Turkey shows in the porthole, front view, lamplit: wing, tip, wattle, snood, mirror as turkey_front (a negative
    wing or mirror=True draws his mirror image). occupants: 1 = Turkey, 2 = two turkeys in the one window (wing2 =
    the second one's wing, default the same; it is drawn D frames behind), 0 = nobody. lamp 0..1: 0 = the window dark.
    dial: None = no dial; 0..1 = a small air dial (six notches) riveted to the side, needle at that level.
    Hinges, each on one visible pin: lid_open (degrees, the lid on the pin at the stern), door_open (degrees, the
    brass porthole door on its iron hinge), latch (0 shut .. 1 flipped up). spin = screw angle (default turns with
    t). pitch tilts the tin.
    Returns screen points: port (porthole centre), port_r (glass radius), pipe (the mouth of the brass pipe on top:
    let bubbles go from here), dial, bow, stern, top, keel, hatch, lid_tip, latch, door_edge."""
    P = _tin()
    fx = -1.0 if flip else 1.0
    spin = t * 300 if spin is None else spin
    mirror = (wing < 0) if mirror is None else mirror
    win = _tin_window(t, clamp(lamp), abs(wing), tip, wattle, snood, bool(mirror) != bool(flip), occupants, None if wing2 is None else abs(wing2))
    pose = {"lid": lid_open, "blade": (0.0, 0.0, 0.0, 1.0, math.cos(math.radians(spin)) * 0.9 + 0.1), "knob": 0.0,
            "door": (0.0, 0.0, 0.0, math.cos(math.radians(door_open)), 1.0), "latch": 90.0 * clamp(latch),
            "needle": lerp(-120, 120, clamp(dial or 0.0)) + (0.8 * math.sin(t * 9) if dial is not None else 0)}
    skip = ["tag", "handle"] + [n for n, v in (("dial", dial), ("needle", dial)) if v is None]

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
            "latch": pt("body", (TIN_PORT[0] + 72, 132)), "door_edge": pt("door", (TIN_PORT[0] + 64, 132)), "dial": pt("body", (236, 123)),
            "pipe": pt("lid", (325, -6))}


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


# ===================== THIS PORTHOLE'S SUBJECT: THE TWIN, AND WHO ELSE IS OUT THERE
# The twin tin is tin() itself with flip=True and the twin's wave (see tin and twin_wave). Below: the pilot's giant
# three-headed monster, the trout's two-headed tin monster, the pond's ripple, paired bubbles and paired trout.
def _frame_group(target, draw_fn, shade=0.0, alpha=1.0, drop=(7, 10, 8, 0.30), tint=(14, 18, 20)):
    """Like _group, but on a sheet the size of the target (for long things such as necks)."""
    img = _img(target)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    res = draw_fn(layer)
    if shade > 0:
        a = layer.getchannel("A")
        layer = Image.blend(layer.convert("RGB"), Image.new("RGB", layer.size, tint), clamp(shade)).convert("RGBA")
        layer.putalpha(a)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    if drop:
        _comp(target, shadow_of(layer.getchannel("A"), drop[2], drop[3] * alpha), (drop[0], drop[1]))
    _comp(target, layer, (0, 0))
    return res


MONSTER_KINDS = [      # three heads, one creature: the same hide, three different crests and eyes
    dict(hide=(86, 62, 104), belly=(222, 196, 150), crest=(214, 110, 62), eye=(238, 206, 96), spot=(150, 122, 170)),
    dict(hide=(78, 58, 100), belly=(226, 202, 160), crest=(206, 96, 70), eye=(232, 220, 120), spot=(140, 116, 166)),
    dict(hide=(94, 66, 108), belly=(216, 190, 146), crest=(222, 126, 58), eye=(244, 196, 84), spot=(158, 128, 172)),
]


@lru_cache(None)
def _monster_head(kind=0):
    """One head, facing LEFT. Design frame about 200 x 130; neck joint (pivot) at (168, 66); nose at (8, 66)."""
    pal = MONSTER_KINDS[kind % 3]
    seed = 500 + kind * 20
    rs = random.Random(seed)
    P = Puppet()

    def skull_deco(d, L, S):
        for row in range(7):
            for col in range(16):
                x, y = 70 + col * 8 + (row % 2) * 4, 26 + row * 9
                d.arc([L(x - 6, y - 6), L(x + 6, y + 6)], 20, 160, fill=dk(pal["hide"], 0.8), width=S)
        cheek = catmull([(92, 70), (120, 62), (146, 74), (138, 96), (104, 94)], 8, closed=True)
        d.polygon([L(*p) for p in cheek], fill=lt(pal["hide"], 1.18))
        for _ in range(26):
            x, y = rs.uniform(24, 176), rs.uniform(30, 64)
            r = rs.uniform(1.8, 3.6)
            d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=pal["spot"])
        d.ellipse([L(20, 54), L(27, 60)], fill=dk(pal["hide"], 0.45))            # nostril
        d.line([L(*p) for p in catmull([(12, 78), (50, 84), (100, 92), (140, 98)], 8)], fill=dk(pal["hide"], 0.5), width=2 * S)
    P.add("skull", cut([(8, 66), (22, 46), (60, 34), (104, 22), (146, 20), (176, 36), (188, 66), (176, 94), (146, 104), (100, 98), (50, 90), (14, 80)],
                       pal["hide"], skull_deco, seed=seed), (168, 66), None, 4)

    def teeth_deco(d, L, S):
        pass
    teeth = [(14, 78)]
    for k in range(11):
        x = 18 + k * 11
        teeth += [(x + 1, 80 + k * 1.4), (x + 5.5, 97 + k * 1.2), (x + 10, 81 + k * 1.4)]
    teeth += [(140, 96), (140, 88), (14, 72)]
    P.add("teeth", cut(teeth, (240, 234, 214), curve=False, seed=seed + 1), (146, 96), "skull", 3.5)

    def jaw_deco(d, L, S):
        for k in range(9):
            x = 34 + k * 12
            d.line([L(x, 92 + k * 1.2), L(x + 6, 116 - abs(k - 5) * 1.5)], fill=dk(pal["belly"], 0.82), width=S)
    P.add("jaw", cut([(16, 84), (56, 92), (104, 100), (150, 100), (156, 112), (132, 124), (84, 122), (40, 108)], pal["belly"], jaw_deco, seed=seed + 2), (148, 102), "skull", 3)
    for k in range(4):                                  # the crest: four spines, each on its own pin
        bx = 112 + k * 16
        P.add(f"crest{k}", cut([(bx - 7, 30), (bx + 4, -2 - 4 * (k % 2)), (bx + 16, 4), (bx + 9, 32)], pal["crest"],
                               lambda d, L, S, bx=bx: [d.line([L(bx + 1, 30), L(bx + 5 + j * 4, 4)], fill=dk(pal["crest"], 0.72), width=S) for j in range(3)],
                               per=5, seed=seed + 3 + k), (bx + 1, 30), "skull", 2 + 0.1 * k)

    def eye_deco(d, L, S):
        d.ellipse([L(107, 40), L(133, 66)], fill=pal["eye"])
        d.arc([L(107, 40), L(133, 66)], 200, 340, fill=lt(pal["eye"], 1.15), width=2 * S)
    P.add("eye", cut(circ(120, 53, 16), dk(pal["hide"], 0.6), eye_deco, curve=False, seed=seed + 8), (120, 53), "skull", 6)

    def pup_deco(d, L, S):
        d.ellipse([L(114.5, 47), L(117.5, 50)], fill=(244, 244, 236))
    P.add("pupil", cut(circ(118, 53, 6.5, 20, 9.5), (20, 18, 24), pup_deco, curve=False, seed=seed + 9, edge=0.4), (118, 53), "eye", 6.2)
    P.add("lid", cut([(102, 53), (106, 40), (120, 35), (134, 40), (138, 53)], dk(pal["hide"], 0.9), per=5, seed=seed + 10), (120, 38), "eye", 6.3)
    P.add("barbel", cut([(26, 82), (32, 82), (30, 104), (24, 124), (20, 122), (25, 102)], pal["crest"], seed=seed + 11), (29, 82), "skull", 2.5)
    return P


@lru_cache(None)
def _monster_link(kind=0):
    """One link of a neck: long axis along +x (towards the head), spine fin on +y, belly plates on -y. 76 x 60."""
    pal = MONSTER_KINDS[kind % 3]

    def deco(d, L, S):
        for row in range(5):
            for col in range(9):
                x, y = -34 + col * 9 + (row % 2) * 4.5, -6 + row * 8
                d.arc([L(x - 6, y - 6), L(x + 6, y + 6)], 110, 250, fill=dk(pal["hide"], 0.8), width=S)
        belly = catmull([(-38, -16), (-12, -19), (14, -19), (38, -16), (36, -27), (0, -31), (-36, -27)], 8, closed=True)
        d.polygon([L(*p) for p in belly], fill=pal["belly"])
        for k in range(6):
            d.line([L(-30 + k * 12, -17), L(-30 + k * 12, -29)], fill=dk(pal["belly"], 0.8), width=S)
        for k in range(5):
            x, y = -26 + (k * 37) % 56, 2 + (k * 23) % 18
            d.ellipse([L(x - 3, y - 3), L(x + 3, y + 3)], fill=pal["spot"])
    body = cut([(-40, 0), (-34, -22), (0, -30), (34, -22), (40, 0), (34, 22), (0, 29), (-34, 22)], pal["hide"], deco, seed=540 + kind)
    fin = cut([(-16, 22), (-6, 44), (14, 40), (18, 22)], pal["crest"], lambda d, L, S: [d.line([L(0, 24), L(-4 + j * 7, 40)], fill=dk(pal["crest"], 0.72), width=S) for j in range(3)],
              per=5, seed=560 + kind)
    return compose([fin, body])


def _neck_curve(base, head, bend):
    bx, by = base
    hx, hy = head
    L = math.hypot(hx - bx, hy - by) or 1.0
    nx, ny = -(hy - by) / L, (hx - bx) / L
    cx, cy = (bx + hx) / 2 + nx * bend * L, (by + hy) / 2 + ny * bend * L

    def at(u):
        x = (1 - u) ** 2 * bx + 2 * u * (1 - u) * cx + u * u * hx
        y = (1 - u) ** 2 * by + 2 * u * (1 - u) * cy + u * u * hy
        dx = 2 * (1 - u) * (cx - bx) + 2 * u * (hx - cx)
        dy = 2 * (1 - u) * (cy - by) + 2 * u * (hy - cy)
        return x, y, math.degrees(math.atan2(dy, dx))
    return at, L


def _draw_neck(layer, base, head, scale, bend, tilt, jaw, look, flip, kind, t, links, lid):
    at, L = _neck_curve(base, head, bend)
    link = _monster_link(kind)
    fy = -1.0 if flip else 1.0
    n = max(2, int(links))
    stretch = max(0.5, L / (n * 58.0 * scale))
    for k in range(n):
        u = (k + 0.5) / n
        x, y, a = at(u)
        s = scale * lerp(1.28, 0.86, u)
        draw_sprite(layer, link, Tm(x, y) @ Rm(a) @ Sm(s * max(1.0, stretch), s * fy))
    P = _monster_head(kind)
    s = math.sin
    fx = -1.0 if flip else 1.0
    pose = {"skull": -tilt, "jaw": -jaw, "pupil": (0.0, look[0], look[1]), "lid": (0.0, 0.0, lid), "barbel": 6 * s(t * 1.4 + kind) + tilt * 0.4}
    for k in range(4):
        pose[f"crest{k}"] = 5 * s(t * 1.6 + k * 0.8 + kind)
    M = Tm(head[0], head[1]) @ Sm(scale * fx, scale) @ Tm(-168, -66)
    return P.draw(layer, pose, M)


def monster_neck(target, base, head, scale=1.0, bend=0.25, tilt=0.0, jaw=4.0, look=(0.0, 0.0), flip=False, kind=0, t=0.0,
                 links=5, lid=-10.0, shade=0.0, alpha=1.0, drop=True):
    """One neck and head of the giant three-headed monster (cut paper: `links` overlapping neck links, then a head
    with a hinged jaw, an eye, four crest spines and a barbel). base = where the neck leaves the body (or the frame
    edge), head = where it joins the head: both screen points. The head faces LEFT (flip=True: right), reaching
    160 * scale beyond `head`, and is 110 * scale tall. bend = how far the neck bows sideways (fraction of its
    length; sign picks the side). tilt = degrees the nose dips (negative lifts it). jaw = degrees open.
    look = pupil offset (about -3..3). kind 0..2 = which of the three heads. lid: -10 open .. 0 half shut.
    Returns {"nose", "eye", "joint"} screen points."""
    def draw(layer):
        return _draw_neck(layer, base, head, scale, bend, tilt, jaw, look, flip, kind, t, links, lid)
    ms = _frame_group(target, draw, shade, alpha, (7 * scale, 10 * scale, 7 * scale, 0.30) if drop else None)
    return {"nose": apply(ms["skull"], (8, 66)), "eye": apply(ms["eye"], (120, 53)), "joint": tuple(head)}


def monster_idle(t, k=0, amp=1.0):
    """The monster's standing motion for head k (0, 1, 2): each head does what head 0 did k * D frames earlier.
    Returns {"dx", "dy", "tilt", "look"}: add dx, dy to the head's place."""
    tt = t - k * DT
    s = math.sin
    return {"dx": amp * 14 * s(tt * 0.9), "dy": amp * 9 * s(tt * 1.3 + 0.6), "tilt": amp * 5 * s(tt * 0.9 + 1.0), "look": (1.2 * s(tt * 0.9), 0.6)}


@lru_cache(None)
def _monster_body():
    """The bulk: a mound 620 x 330 (design), top of the back at (310, 20), neck roots along its shoulder."""
    pal = MONSTER_KINDS[0]
    rs = random.Random(580)

    def deco(d, L, S):
        for row in range(22):
            for col in range(44):
                x, y = 10 + col * 14 + (row % 2) * 7, 34 + row * 14
                d.arc([L(x - 10, y - 10), L(x + 10, y + 10)], 200, 340, fill=dk(pal["hide"], 0.8), width=S)
        belly = catmull([(150, 330), (190, 250), (260, 214), (360, 214), (430, 250), (470, 330)], 8, closed=True)
        d.polygon([L(*p) for p in belly], fill=pal["belly"])
        for k in range(8):
            y = 228 + k * 14
            d.line([L(190 - k * 4, y), L(430 + k * 4, y)], fill=dk(pal["belly"], 0.8), width=S)
        for _ in range(90):
            x, y = rs.uniform(30, 590), rs.uniform(40, 200)
            r = rs.uniform(2.5, 6)
            d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=pal["spot"])
    body = cut([(0, 330), (10, 220), (60, 120), (150, 50), (250, 22), (370, 22), (470, 50), (560, 120), (610, 220), (620, 330)], pal["hide"], deco, seed=581)
    fins = [cut([(250 + k * 34, 30), (262 + k * 34, -14 - 8 * (k % 2)), (290 + k * 34, 30)], pal["crest"], per=5, seed=583 + k) for k in range(4)]
    flipL = cut([(40, 210), (-40, 250), (-70, 310), (-20, 322), (40, 290), (80, 250)], dk(pal["hide"], 0.86), seed=590)
    flipR = cut([(580, 210), (660, 250), (690, 310), (640, 322), (580, 290), (540, 250)], dk(pal["hide"], 0.86), seed=591)
    return compose(fins + [flipL, flipR, body])


MONSTER_ROOTS = [(-150, -90), (0, -128), (150, -90)]     # where the three necks leave the body, from its centre, at scale 1


def monster(target, x, y, scale=1.0, t=0.0, heads=None, shade=0.0, alpha=1.0, drop=True, body=True):
    """The giant three-headed monster, whole (the river side sees it whole; from Turkey's seat use monster_neck
    three times, rising from below the glass). (x, y) = centre of its bulk, which is 620 x 330 times scale
    (x - 310s .. x + 310s, y - 150s .. y + 180s): put y low so the frame crops it. The three necks leave the
    shoulders at MONSTER_ROOTS (times scale) and by default rise about 250 * scale above them, swaying, each head
    doing what the one before did D frames earlier.
    heads = None, or a list of three dicts overriding any of: "at" (absolute screen point of the head joint),
    "tilt", "jaw", "look", "flip", "bend", "lid". body=False leaves the bulk out (necks only).
    Returns {"heads": [{"nose", "eye", "joint"} x 3], "roots": [(x, y) x 3]}."""
    if body:
        spr = _monster_body()

        def draw(layer):
            draw_sprite(layer, spr, Tm(x, y) @ Sm(scale) @ Tm(-310, -150))
        _frame_group(target, draw, shade, alpha, (9 * scale, 13 * scale, 10 * scale, 0.30) if drop else None)
    out, roots = [], []
    default = [(-250, -330, False, -0.18), (-30, -400, False, 0.12), (250, -330, True, 0.18)]
    for k in (1, 0, 2):                                 # the middle neck is furthest back
        idle = monster_idle(t, k)
        h = dict(heads[k]) if heads else {}
        rx, ry = x + MONSTER_ROOTS[k][0] * scale, y + MONSTER_ROOTS[k][1] * scale
        dx, dy, fl, bd = default[k]
        at = h.get("at", (x + dx * scale + idle["dx"] * scale, y + dy * scale + idle["dy"] * scale))
        res = monster_neck(target, (rx, ry), at, scale * 0.95, h.get("bend", bd), h.get("tilt", 14 + idle["tilt"]), h.get("jaw", 4.0), h.get("look", idle["look"]),
                           h.get("flip", fl), k, t, 5, h.get("lid", -10.0), shade, alpha, drop)
        out.append((k, res))
        roots.append((k, (rx, ry)))
    return {"heads": [r for _, r in sorted(out)], "roots": [r for _, r in sorted(roots)]}


# ------------------------------------------------ the two-headed tin monster
# Built in the tin's own design frame (see TIN_C) so that it fits the submarine exactly: its skirt is the tin's lid
# plus one wall thickness, its rivet row has the tin's own pitch, and seated its rolled rim sits on the tin's top seam.
TM_RIM = 84             # design y of the bottom of the rim when seated (the tin's seam rivets are at y = 90)


@lru_cache(None)
def _tin_monster():
    P = Puppet()
    tinc, lidc = PAL["tin"], PAL["tin_lid"]

    def skirt_deco(d, L, S):
        for k in range(46):                             # the pressed ribs, the tin's own pitch
            x = -18 + k * 9.8
            d.line([L(x, 16), L(x, 60)], fill=(150, 162, 158), width=S)
            d.line([L(x + 1.5, 16), L(x + 1.5, 60)], fill=(190, 200, 196), width=S)
        for yy in (12, 64):
            d.line([L(-24, yy), L(428, yy)], fill=PAL["tin_dark"], width=2 * S)
            d.line([L(-24, yy + 2.5), L(428, yy + 2.5)], fill=(222, 230, 226), width=S)
        for k in range(31):                             # rivets at 14.5: they land over the tin's own seam rivets
            x = 14 + (k - 2) * 14.5
            d.ellipse([L(x - 2.6, 68.4), L(x + 2.6, 73.6)], fill=(214, 222, 218), outline=(96, 106, 104))
        d.rectangle([L(-26, 77), L(430, 86)], fill=lt(lidc, 1.14))                 # the rolled rim
        d.line([L(-26, 77.5), L(430, 77.5)], fill=(236, 242, 238), width=S)
        d.line([L(-26, 83.5), L(430, 83.5)], fill=PAL["tin_dark"], width=2 * S)
        rs = random.Random(6)
        for k in range(34):                             # rust creeping in from the two ends
            x = rs.choice((-1, 1)) * (226 - abs(rs.gauss(0, 46))) + 202
            y = rs.uniform(20, 74)
            d.ellipse([L(x - 5, y - 3), L(x + 5, y + 3)], fill=PAL["rust"])
    P.add("under", cut(rrect(-18, 60, 422, TM_RIM + 3, 3), (22, 22, 26), curve=False, seed=601, edge=0.2), (202, 80), "skirt", 1)
    skirt = [(-10, 14), (-4, 6), (408, 6), (414, 14), (428, 76), (428, TM_RIM), (-24, TM_RIM), (-24, 76)]
    P.add("skirt", cut(skirt, lidc, skirt_deco, curve=False, seed=602, grain=0.11), (202, 40), None, 3)

    def head(name, cx, seed):
        cy = -82

        def collar_deco(d, L, S):
            for yy in (-20, -8):
                d.line([L(cx - 26, yy), L(cx + 26, yy)], fill=PAL["tin_dark"], width=S)
            for k in range(5):
                d.ellipse([L(cx - 22 + k * 11 - 2, 0), L(cx - 22 + k * 11 + 2, 4)], fill=(214, 222, 218), outline=(96, 106, 104))
        P.add(name + "_collar", cut(rrect(cx - 26, -34, cx + 26, 10, 4), dk(tinc, 0.90), collar_deco, curve=False, seed=seed), (cx, 6), "skirt", 2.4)

        def head_deco(d, L, S):
            for k in range(13):                         # pressed rings, like the bottom of a round tin
                r = 54 - k * 4
                d.ellipse([L(cx - r, cy - r), L(cx + r, cy + r)], outline=(160, 170, 166) if k % 2 else (198, 208, 204), width=S)
            for k in range(16):
                a = 2 * math.pi * k / 16
                x, y = cx + 49 * math.cos(a), cy + 49 * math.sin(a)
                d.ellipse([L(x - 2.4, y - 2.4), L(x + 2.4, y + 2.4)], fill=(214, 222, 218), outline=(96, 106, 104))
            for k in range(8):
                x, y = cx - 40 + (k * 53) % 80, cy + 26 + (k * 17) % 18
                d.ellipse([L(x - 4, y - 2.5), L(x + 4, y + 2.5)], fill=PAL["rust"])
        P.add(name, cut(circ(cx, cy, 56, 40), tinc, head_deco, curve=False, seed=seed + 1, grain=0.11), (cx, 6), name + "_collar", 2.6)
        # the one eye: a round brass-rimmed window with the lamp behind it
        ring = brass_ring(56, 84, bolts=6).resize((100, 100), Image.LANCZOS)        # glass r 28, ring to 42 (with pad)
        n = ring.size[0]
        eye = Image.new("RGBA", (n * 2, n * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(eye)
        c = n
        for k in range(8):
            r = 56 - k * 6
            d.ellipse([c - r, c - r, c + r, c + r], fill=(70 + k * 22, 52 + k * 18, 30 + k * 8, 255))
        d.arc([c - 44, c - 46, c + 44, c + 46], 196, 262, fill=(255, 255, 250, 170), width=6)
        eye = eye.resize((n, n), Image.LANCZOS)
        eye.alpha_composite(ring)
        P.add(name + "_eye", Sprite(eye, cx - n // 2, cy - n // 2), (cx, cy), name, 2.8)
        # a little brass funnel on top, as on the deck's picture of the twin
        P.add(name + "_pipe", compose([cut(rrect(cx - 7, cy - 78, cx + 7, cy - 50, 3), PAL["brass"], curve=False, seed=seed + 3),
                                       cut(rrect(cx - 13, cy - 86, cx + 13, cy - 74, 4), lt(PAL["brass"], 1.1), curve=False, seed=seed + 4)]), (cx, cy - 52), name, 2.5)
    head("headL", 96, 610)
    head("headR", 308, 620)
    return P


def tin_monster(target, x, y, scale=1.0, t=0.0, lift=0.0, nod=(0.0, 0.0), tilt=0.0, flip=False, port=None,
                shade=0.0, alpha=1.0, drop=True):
    """The two-headed tin monster: one skirt of pressed bread-roll tin, two round tin heads side by side on it, each
    with one round brass-rimmed window for an eye. It is cut to FIT THE SUBMARINE: give it the same (x, y, scale,
    flip) as the tin() it comes down over and lift=0 seats it flush, rim on the tin's top seam, its rivet row
    lined up over the tin's, covering lid and pipe. lift = screen px it hangs above that (300 = well clear).
    nod = (left, right) degrees each head leans on its collar (use settle() for the clink when it seats).
    tilt = degrees the whole thing rocks. port = the dict tin() returned: its brass porthole flange is laid back
    IN FRONT of the skirt (occlusion: the rim passes in front of the tin's shoulder and behind the porthole).
    Draw order: tin(...) first, then tin_monster(..., port=p).
    At scale 1: skirt 452 wide, x - 224 .. x + 228; rim bottom at y - 44 + ... (seated: 44 * scale above the tin's
    centre); heads reach 280 * scale above the tin's centre. Returns {"rim", "left_eye", "right_eye", "top"}."""
    P = _tin_monster()
    fx = -1.0 if flip else 1.0
    pose = {"skirt": tilt, "headL_collar": nod[0], "headR_collar": nod[1]}

    def draw(layer, ox, oy):
        M = Tm(x + ox, y + oy - lift) @ Sm(scale * fx, scale) @ Tm(-TIN_C[0], -TIN_C[1])
        return P.draw(layer, pose, M)
    half = int(330 * scale + 20)
    ms = _group(target, x, y - lift - 60 * scale, half, lambda layer, ox, oy: draw(layer, ox, oy + 0), shade, alpha, (8 * scale, 12 * scale, 8 * scale, 0.34) if drop else None)
    if port is not None:
        ring = brass_ring(WIN_R * 2, 64 * 2)
        n = int(round((64 + 16) * 2 * port["port_r"] / WIN_R))
        ring = ring.resize((n, n), Image.LANCZOS)
        _comp(target, ring, (port["port"][0] - n / 2, port["port"][1] - n / 2))

    hy = y - lift - 60 * scale

    def pt(part, p):
        q = apply(ms[part], p)
        return (q[0] - int(half - x), q[1] - int(half - hy))
    return {"rim": pt("skirt", (202, TM_RIM)), "left_eye": pt("headL", (96, -82)), "right_eye": pt("headR", (308, -82)), "top": pt("skirt", (202, 6))}


# ------------------------------------------------------ doubles in the water
def ripple(target, cx, cy, r, t, t0=0.0, amp=7.0, speed=150.0, life=2.4):
    """The pond mirror's one slow ripple: bends what is already drawn inside the disc (cx, cy, r) with a ring
    that spreads from the centre from time t0 and dies away after `life` seconds. Call it after the river and the
    actors behind the glass, before cabin(). amp = px of bend."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    img = _img(target)
    x0, y0, x1, y1 = max(0, int(cx - r)), max(0, int(cy - r)), min(img.size[0], int(cx + r)), min(img.size[1], int(cy + r))
    if x1 <= x0 or y1 <= y0:
        return
    a = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"))
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx + x0 - cx, yy + y0 - cy
    rr = np.hypot(dx, dy) + 1e-3
    front = dt * speed
    env = np.exp(-((rr - front) / 46.0) ** 2) * (1 - dt / life) * (rr < r)
    off = amp * env * np.sin((rr - front) / 9.0)
    sx = np.clip(xx + dx / rr * off, 0, w - 1).astype(np.int32)
    sy = np.clip(yy + dy / rr * off, 0, h - 1).astype(np.int32)
    out = a[sy, sx].astype(np.float32) + (env * 26 * np.sin((rr - front) / 9.0 + 1.2))[..., None]
    _img(target).paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), (x0, y0))
    if hasattr(target, "d") and hasattr(target, "img"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


def bubble(target, x, y, size=6.0, alpha=1.0):
    """One ring bubble centred at (x, y)."""
    S = 3
    n = int(size * 2 + 8)
    lay = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c, r = n * S / 2, size * S
    a = int(235 * clamp(alpha))
    d.ellipse([c - r, c - r, c + r, c + r], fill=(226, 244, 238, int(a * 0.22)), outline=(236, 248, 242, a), width=S + 1)
    d.arc([c - r * 0.62, c - r * 0.62, c + r * 0.62, c + r * 0.62], 190, 262, fill=(255, 255, 255, a), width=S + 1)
    _comp(target, lay.resize((n, n), Image.LANCZOS), (x - n / 2, y - n / 2))


def bubble_pair(target, x, y, t, t0, rise=170.0, size=6.0, drift=10.0, life=2.2, n=2, seed=0):
    """A bubble let go at (x, y) at time t0, and its double D frames behind it on the same wobbling path.
    n = 2 for a pair (4: two turkeys' worth). Nothing is drawn before t0 or after the bubbles have risen `rise` px."""
    for k in range(n):
        dt = t - t0 - k * DT
        if dt < 0 or dt > life:
            continue
        u = dt / life
        bx = x + drift * math.sin(dt * 4.2 + seed) + drift * 0.6 * u
        by = y - rise * (u ** 0.85)
        bubble(target, bx, by, size * (0.7 + 0.5 * u), min(1.0, u * 8) * min(1.0, (1 - u) * 4))


def trout_pair(target, path, t, scale=0.5, kinds=(0, 2), **kw):
    """Two brook trout on ONE path: the second is where the first was D frames ago. path(t) -> (x, y) or
    (x, y, pitch); keyword arguments go to trout() (flip, pose, gaze, shade ...). Returns [points, points]."""
    out = []
    for k in (1, 0):
        tt = t - k * DT
        p = path(tt)
        out.append(trout(target, p[0], p[1], scale, tt, kind=kinds[k], pitch=p[2] if len(p) > 2 else 0.0, phase=0.0, **kw))
    return out[::-1]


@lru_cache(None)
def _stage():
    a = np.array((244, 240, 228), np.float32)[None, None, :] * (1 + 0.016 * vnoise((H, W), 2.0, None, 901, 2) + 0.014 * vnoise((H, W), 200, None, 902, 2))[..., None]
    return to_img(a).convert("RGB")


def empty_stage(target):
    """A blank: an empty, evenly lit stage of plain paper filling the frame (nothing on it, by rule). Lay cabin()
    over it for a blank seen from Turkey's seat; put the bolt's die on it with die_at_bolt() or die()."""
    img = _img(target)
    if img.mode == "RGBA":
        img.alpha_composite(_stage().convert("RGBA"))
    else:
        img.paste(_stage(), (0, 0))
    if hasattr(target, "d") and hasattr(target, "img"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


def camera(target, cx, cy, zoom=1.0):
    """Push the camera in on what has been drawn so far: (cx, cy) moves to the frame centre and everything is
    enlarged by `zoom` (>= 1). Call it before the badge and the caption."""
    if abs(zoom - 1.0) < 1e-3 and abs(cx - W / 2) < 0.5 and abs(cy - H / 2) < 0.5:
        return
    img = _img(target)
    w, h = img.size
    k = 1.0 / max(zoom, 1.0)
    cx, cy = clamp(cx, w / 2 * k, w - w / 2 * k), clamp(cy, h / 2 * k, h - h / 2 * k)       # never look off the edge
    out = img.transform((w, h), Image.AFFINE, (k, 0, cx - w / 2 * k, 0, k, cy - h / 2 * k), resample=Image.BICUBIC)
    img.paste(out, (0, 0))
    if hasattr(target, "d") and hasattr(target, "img"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


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


def sheet_ring(target, cx, cy, scale=1.6, lit=(), empty=(), t=0.0, alpha=1.0):
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


# The pilot's drawing, traced by eye from the child's sheet. The tracing was done on an enlargement (4x) of the top of
# the ring; _U turns those tracing coordinates into "sheet units" measured from the ring's centre, in which the
# printed ring's inner radius is SHEET_R_IN (214), so pilot_drawing and sheet_ring share cx, cy and scale.
# The child drew small and high: everything sits in the top third of the ring and the rest stays empty.
def _U(pts):
    return [((x - 460.0) / 780.0 * SHEET_R_IN, (y - 924.0) / 780.0 * SHEET_R_IN) for x, y in pts]


def _scribble(cx, cy, r, turns, ph, seed):
    rs = random.Random(seed)
    out = []
    n = int(turns * 14)
    for k in range(n + 1):
        u = k / n
        a = ph + 2 * math.pi * turns * u
        rr = r * (0.18 + 0.82 * abs(math.sin(math.pi * (u * 1.5 + 0.1)))) * rs.uniform(0.8, 1.05)
        out.append((cx + rr * math.cos(a), cy + rr * 1.05 * math.sin(a)))
    return out


# (group, points, pencil weight 0..1, sharp corners?) in the child's order. Groups are timed by PILOT_TIMES.
_PILOT = [
    # 1 · the box: a leaning, not-quite-closed four-sided body, corners overshot
    ("box", [(352, 298), (340, 360), (322, 430), (305, 494)], 0.75, False),
    ("box", [(298, 486), (380, 500), (480, 518), (577, 535)], 0.75, False),
    ("box", [(573, 540), (552, 460), (528, 380), (505, 310)], 0.75, False),
    ("box", [(513, 323), (450, 316), (400, 308), (356, 300)], 0.70, False),
    # 2 · the dome on top, and the small mark inside it
    ("dome", [(361, 303), (356, 262), (372, 237), (420, 228), (470, 230), (498, 252), (507, 292), (503, 322)], 0.75, False),
    ("dome", [(405, 262), (409, 275), (413, 287)], 0.25, False),
    # 3 · the round window: a circle, scribbled dark, then scribbled again D frames later
    ("window", [(400, 361), (373, 371), (360, 400), (372, 431), (400, 443), (430, 433), (442, 402), (431, 372), (403, 361)], 0.8, False),
    ("scribble1", _scribble(401, 402, 34, 4.0, 0.4, 3), 1.0, False),
    ("scribble2", _scribble(401, 402, 36, 5.0, 2.3, 4), 1.0, False),
    # 4 · the little blocks on the left side
    ("blocks", [(292, 296), (344, 290), (350, 336), (292, 344), (290, 298)], 0.7, True),
    ("blocks", [(286, 346), (336, 340), (338, 376), (282, 380), (284, 348)], 0.6, True),
    ("blocks", [(254, 424), (302, 430), (318, 592), (240, 578), (252, 426)], 0.65, True),
    # 5 · the upright block on the right side and the little fin below it
    ("right", [(540, 366), (566, 362), (576, 446), (548, 452), (541, 368)], 0.7, True),
    ("right", [(558, 470), (600, 468), (628, 480), (636, 502), (622, 520), (596, 508), (566, 492)], 0.7, False),
    # 6 · faint: the long loose curves dropping from the box, the upright mark, the loose lines towards the turkey
    ("faint", [(255, 605), (300, 680), (350, 760), (400, 826)], 0.16, False),
    ("faint", [(452, 556), (400, 636), (424, 700), (440, 756), (406, 824)], 0.16, False),
    ("faint", [(168, 322), (200, 360), (232, 398), (250, 350), (268, 314), (286, 348)], 0.14, False),
    ("faint", [(690, 388), (700, 330), (716, 272), (722, 330), (730, 420), (748, 520), (770, 604)], 0.20, False),
    ("faint", [(690, 386), (712, 384), (736, 380)], 0.18, False),
    ("faint", [(580, 470), (640, 540), (720, 575), (800, 548), (850, 520), (880, 470)], 0.12, False),
    ("faint", [(742, 382), (800, 340), (850, 322)], 0.12, False),
    # 7 · lighter pressure: the turkey's head to the right, beak pointing LEFT at the box, eye, wattle, neck
    ("head", [(1150, 482), (1110, 500), (1076, 520), (1048, 545), (1012, 585)], 0.34, False),
    ("head", [(1012, 585), (950, 640), (890, 690)], 0.42, False),
    ("head", [(890, 692), (940, 668), (990, 672), (1036, 682)], 0.42, False),
    ("head", [(988, 628), (1000, 634), (1012, 640)], 0.34, False),
    ("head", _scribble(1080, 585, 11, 1.6, 0.0, 5), 0.34, False),
    ("head", [(990, 604), (994, 608), (990, 610)], 0.4, False),
    ("head", [(1034, 682), (1030, 702), (1002, 716), (1004, 758), (1040, 772)], 0.34, False),
    ("head", [(1040, 772), (1050, 830), (1100, 880), (1160, 894), (1200, 896)], 0.26, False),
]
PILOT_TIMES = {"box": (0.6, 1.8), "dome": (1.8, 2.5), "window": (2.5, 2.8), "scribble1": (2.8, 3.3), "scribble2": (3.3, 3.8),
               "blocks": (3.9, 4.8), "right": (4.8, 5.6), "faint": (5.6, 6.4), "head": (6.4, 8.6)}
PILOT_END = 8.6         # seconds: pilot_drawing's progress 1.0. scribble2 starts exactly D frames after scribble1.
_MARKS = {   # the friends' own marks (back of the sheet), in px from the mark's own centre
    # first friend: a triangle in three strokes, left side, right side, base; the sides do not quite meet at the top
    "triangle": [([(-15, 17), (-9, 4), (-3, -8), (2, -19)], 0.8, False), ([(6, -17), (11, -2), (15, 8), (19, 17)], 0.8, False), ([(-17, 18), (0, 20), (20, 17)], 0.8, False)],
    # next friend drew nothing: the choice itself is circled, one long wobbly loop that overlaps where it began
    "loop": [([(-150, -34), (-60, -44), (50, -46), (150, -40), (200, -26), (214, 2), (198, 30), (140, 42), (30, 46), (-90, 44), (-180, 38), (-212, 14),
               (-206, -18), (-170, -36), (-110, -42), (-40, -47)], 0.7, False)],
}
PILOT_STROKES = [dict(pts=_U(p), weight=w, sharp=s, part=g) for g, p, w, s in _PILOT]
PILOT_PARTS = ("box", "dome", "window", "scribble1", "scribble2", "blocks", "right", "faint", "head")


def pilot_progress(t):
    """Seconds since the pilot's page began -> pilot_drawing's progress (0..1). The strokes land on the board's
    schedule (PILOT_TIMES): box 0.6..1.8, dome ..2.5, window ..2.8, its scribble 2.8..3.3 and the scribble's double
    3.3..3.8 (D frames behind), blocks 3.9..4.8, right side ..5.6, faint curves ..6.4, the turkey's head ..8.6."""
    return clamp(t / PILOT_END)


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
    # when each stroke starts and how long it takes, in progress units
    start, dur = [0.0] * len(strokes), [0.0] * len(strokes)
    if part == "all":
        for g in PILOT_PARTS:
            idx = [k for k, s in enumerate(strokes) if s["part"] == g]
            t0, t1 = PILOT_TIMES[g]
            tot = sum(lens[k] for k in idx) + sum(hop[k] for k in idx[1:])
            p = t0
            for j, k in enumerate(idx):
                if j:
                    p += hop[k] / tot * (t1 - t0)
                start[k], dur[k] = p / PILOT_END, lens[k] / tot * (t1 - t0) / PILOT_END
                p += lens[k] / tot * (t1 - t0)
    else:
        tot = sum(lens) + sum(hop)
        p = 0.0
        for k in range(len(strokes)):
            p += hop[k] / tot
            start[k], dur[k] = p, lens[k] / tot
            p += lens[k] / tot
    allp = np.concatenate(dense)
    pad = 10
    x0, y0 = int(allp[:, 0].min()) - pad, int(allp[:, 1].min()) - pad
    w, h = int(allp[:, 0].max()) + pad - x0, int(allp[:, 1].max()) + pad - y0
    arr = np.full((h, w), 9.0, np.float32)
    alpha = np.zeros((h, w), np.float32)
    path = []
    for k, (s, d) in enumerate(zip(strokes, dense)):
        seg = np.hypot(*(d[1:] - d[:-1]).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        rate = dur[k] / max(cum[-1], 1e-6)
        nstep = max(2, int(cum[-1] / 0.7))
        ss = np.linspace(0, cum[-1], nstep)
        xs, ys = np.interp(ss, cum, d[:, 0]) - x0, np.interp(ss, cum, d[:, 1]) - y0
        a_im = Image.new("F", (w, h), 9.0)
        dd = ImageDraw.Draw(a_im)
        wd = (2.1 + 1.5 * s["weight"]) * max(sc, 0.6) + 0.5
        for j in range(nstep - 1, -1, -1):
            u = j / (nstep - 1)
            r = wd / 2 * (0.78 + 0.22 * math.sin(j * 0.21 + k)) * (0.6 + 0.4 * min(1, u * 12 + 0.3) * min(1, (1 - u) * 10 + 0.4))
            dd.ellipse([xs[j] - r, ys[j] - r, xs[j] + r, ys[j] + r], fill=float(start[k] + ss[j] * rate))
        A = np.asarray(a_im, np.float32)
        solid = (A < 8).astype(np.float32)
        soft = blur_arr(solid, 0.7)
        al = soft * (0.16 + 0.80 * s["weight"])
        new = (solid > 0) & (arr > 8)
        arr = np.where(new, A, arr)                     # graphite stays where it first landed ...
        fringe = (soft > 0.02) & (arr > 8)
        arr[fringe] = start[k] + dur[k]
        alpha = np.maximum(alpha, al)                   # ... and a second pass can only fill the gaps and darken
        for j in range(0, nstep, 3):
            path.append((start[k] + ss[j] * rate, float(xs[j] + x0), float(ys[j] + y0), True))
        path.append((start[k] + dur[k], float(xs[-1] + x0), float(ys[-1] + y0), False))
    tooth = 0.72 + 0.38 * vnoise((h, w), 1.5, None, 811) + 0.12 * vnoise((h, w), 9, None, 812)
    alpha = np.clip(alpha * tooth, 0, 1)
    return x0, y0, alpha, arr, path


def pilot_drawing(target, cx, cy, progress=1.0, scale=1.6, part="all", alpha=1.0):
    """The pilot's pencil drawing, drawn as far as `progress` (0..1), stroke by stroke in the child's order: a boxy
    sub with a dome, one round window scribbled dark, little blocks on its sides, faint loose curves, and a faint
    turkey head to its right with the beak pointing at the sub. (cx, cy) = centre of the sheet's ring; scale = screen
    px per sheet unit (ring glass radius = 214 * scale): use the same cx, cy, scale as sheet_ring.
    The drawing spans x -89..+203, y -200..-27 sheet units from the centre (the top third of the ring only).
    part: "all" (timed by pilot_progress), or one group on its own, drawn 0..1: box, dome, window, scribble1,
    scribble2, blocks, right, faint, head."""
    x0, y0, al, arr, _ = _pilot(int(round(scale * 100)), part)
    a = al * (arr <= progress) * alpha
    g = np.zeros(al.shape + (4,), np.uint8)
    g[..., :3] = PAL["graphite"]
    g[..., 3] = (a * 255).astype(np.uint8)
    _comp(target, Image.fromarray(g, "RGBA"), (cx + x0, cy + y0))


def pilot_tip(cx, cy, progress, scale=1.6, part="all"):
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
    """A friend's own pencil mark, centred at (cx, cy), drawn 0..1: kind "triangle" (first friend: left side, right
    side, base, not quite meeting at the top; 37 x 40 px times scale) or "loop" (next friend drew nothing and circled
    the choice: one long wobbly loop, 430 x 94 px times scale, overlapping where it began)."""
    pilot_drawing(target, cx, cy, progress, scale, part=kind)


def friend_tip(kind, cx, cy, progress, scale=1.6):
    """Pencil point for friend_mark: (x, y, down)."""
    return pilot_tip(cx, cy, progress, scale, part=kind)


def pencil_path(target, pts, weight=0.6, closed=False, seed=0, alpha=1.0, wobble=1.0, color=None):
    """A pencil line through screen points `pts` (a wobbling graphite line with the paper's tooth in it): the
    outline a thing arrives as before its painted double lands on it. color = None for graphite (on paper); over the
    dark cabin or the river pass CHALK, on brass pass DARK."""
    rs = random.Random(seed)
    P = [tuple(p) for p in pts]
    if closed:
        P = P + [P[0], P[1]]
    dense = catmull(P, 6) if len(P) > 2 else P
    ph1, ph2 = rs.uniform(0, 6.28), rs.uniform(0, 6.28)
    out = []
    s = 0.0
    for k, (x, y) in enumerate(dense):
        if k:
            s += math.hypot(x - dense[k - 1][0], y - dense[k - 1][1])
        out.append((x + wobble * 1.1 * math.sin(s / 23.0 + ph1), y + wobble * 1.1 * math.sin(s / 17.0 + ph2)))
    xs, ys = [p[0] for p in out], [p[1] for p in out]
    pad = 6
    x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
    w, h = int(max(xs)) + pad - x0, int(max(ys)) + pad - y0
    S = 2
    m = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m).line([((x - x0) * S, (y - y0) * S) for x, y in out], fill=255, width=int((2.0 + 1.3 * weight) * S), joint="curve")
    m = m.resize((w, h), Image.LANCZOS)
    a = np.asarray(m, np.float32) / 255 * (0.45 + 0.5 * weight) * alpha
    tooth = 0.72 + 0.38 * vnoise((h, w), 1.5, None, 811 + seed % 7) + 0.12 * vnoise((h, w), 9, None, 812)
    g = np.zeros((h, w, 4), np.uint8)
    g[..., :3] = color or PAL["graphite"]
    g[..., 3] = (np.clip(a * tooth * (1.5 if color else 1.0), 0, 1) * 255).astype(np.uint8)
    _comp(target, Image.fromarray(g, "RGBA"), (x0, y0))


CHALK = (238, 232, 214)     # a white pencil: outlines laid over the dark cabin or the river
DARK = (46, 34, 22)         # a soft dark pencil: outlines on brass


def ring_outline(target, cx, cy, r_in, r_out, bolts=True, seed=0, alpha=1.0, color=None):
    """The porthole as a pencil outline (two circles and six small bolt heads): what the brass ring arrives as,
    D frames before brass_ring / cabin lands on it. Same centre and radii as the ring it stands in for."""
    pencil_path(target, circ(cx, cy, r_in, 40), 0.6, True, seed, alpha, color=color)
    pencil_path(target, circ(cx, cy, r_out, 44), 0.6, True, seed + 1, alpha, color=color)
    if bolts:
        hr = (r_out - r_in) * 0.30
        for k in range(1, 7):
            bx, by = bolt_xy(k, cx, cy, r_in, r_out)
            pencil_path(target, [(bx + hr * math.cos(math.radians(60 * j + 17 * k)), by + hr * math.sin(math.radians(60 * j + 17 * k))) for j in range(6)],
                        0.5, True, seed + 2 + k, alpha, wobble=0.4, color=color)


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


CARD_SIZE = (640, 150)


def pick_card(target, kind, pick, initial, x=160, y=350, size=CARD_SIZE, paint=1.0, drawn=0.0, pressed=0.0, lit=0.0, color=None, who=None, outline_color=CHALK):
    """A friend's pick on a paper card, top-left corner at (x, y): the controller button `kind` on the left, the
    sheet's own printed option `pick` in type ("Pond mirror", "Two-headed tin monster"), the worksheet's dashed
    "draw the one you pick" ring on the right, and the friend's `initial` ("B.", "W.") small in the corner.
    paint: 0 = the card is only its pencil outline (card edge, button, the dashed ring); 1 = its painted double has
    landed, registering exactly (use `Wd.arrive(t, t0)`: 1 -> paint=0, 2 -> paint=1). The outline is in white pencil
    (outline_color=Wd.CHALK) because the card comes up over the dark cabin / the river; None = graphite.
    drawn 0..1 = the friend's own pencil mark: for kind "triangle" the three-stroke triangle in the dashed ring;
    for any other kind the long loop circling the lettering and the button (nothing was drawn in the ring).
    pressed 0..1 pushes the button in; lit 0..1 lights it. who = an optional small line above the option.
    Returns {"button": (x, y), "mark": (x, y), "mark_kind", "mark_scale", "box"}: pass mark, mark_kind and mark_scale
    to friend_tip() to put the pencil on the mark."""
    w, h = size
    bx, by, br = 76, h / 2, min(52, h / 2 - 20)
    mx, my = w - 82, h / 2
    mark_kind = "triangle" if kind == "triangle" else "loop"
    lx, ly = (w - 150) / 2 + 4, h / 2
    mark = (mx, my) if mark_kind == "triangle" else (lx, ly)
    mscale = 1.9 if mark_kind == "triangle" else (w - 176) / 430.0
    if paint < 1.0:
        a = 1.0 - clamp(paint)
        pencil_path(target, [(x + px, y + py) for px, py in rrect(2, 2, w - 2, h - 2, 12, 4)], 0.6, True, 21, a, wobble=0.8, color=outline_color)
        button(target, kind, x + bx, y + by, br, outline=True, alpha=a, color=outline_color)
        pencil_path(target, circ(x + mx, y + my, 52, 28), 0.35, True, 23, a, wobble=0.6, color=outline_color)
    if paint > 0.0:
        card = _card_stock(w, h, tuple(color or PAL["page"])).copy()
        d = ImageDraw.Draw(card)
        if who:
            d.text((bx + br + 26, 22), who, font=font("sans", 19), fill=PAL["ink"] + (255,))
        fs = 40
        while fs > 22 and font("serif", fs).getlength(pick) > (mx - 62) - (bx + br + 26):
            fs -= 2
        d.text((bx + br + 26, h / 2 + (8 if who else 0)), pick, font=font("serif", fs), fill=PAL["ink"] + (255,), anchor="lm")
        button(card, kind, bx, by, br, pressed, lit)
        for j in range(24):
            a0 = j * 15
            d.arc([mx - 52, my - 52, mx + 52, my + 52], a0, a0 + 8, fill=(120, 116, 112, 255), width=2)
        if initial:
            d.text((w - 16, h - 12), initial, font=font("sans", 17), fill=(96, 90, 84, 255), anchor="rs")
        if paint < 1.0:
            card.putalpha(card.getchannel("A").point(lambda v: int(v * clamp(paint))))
        _comp(target, shadow_of(card.getchannel("A"), 9, 0.42), (x + 7, y + 11))
        _comp(target, card, (x, y))
    if drawn > 0:
        friend_mark(target, mark_kind, x + mark[0], y + mark[1], drawn, mscale)
    return {"button": (x + bx, y + by), "mark": (x + mark[0], y + mark[1]), "mark_kind": mark_kind, "mark_scale": mscale, "box": (x, y, x + w, y + h)}


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


def button(target, kind, x, y, r=40, pressed=0.0, lit=0.0, outline=False, alpha=1.0, color=None):
    """One controller button, a domed arcade button centred at (x, y): kind = triangle (green), circle (red),
    cross (blue), square (pink), hexagon (amber). pressed 0..1 pushes it in; lit 0..1 puts a halo round it.
    outline=True draws only its pencil outline (the bezel circle and the symbol), the same size and place
    (color: None = graphite, or Wd.CHALK over a dark ground)."""
    r = int(r)
    if outline:
        pencil_path(target, circ(x, y, r, 30), 0.6, True, 31, alpha, wobble=0.6, color=color)
        pencil_path(target, circ(x, y, r * 0.78, 26), 0.4, True, 32, alpha, wobble=0.5, color=color)
        q = r * 0.34
        if kind == "triangle":
            shapes = [([(x + q * math.cos(math.radians(a)), y + q * 1.05 * math.sin(math.radians(a)) + q * 0.12) for a in (-90, 30, 150)], True)]
        elif kind == "circle":
            shapes = [(circ(x, y, q * 0.9, 16), True)]
        elif kind == "cross":
            shapes = [([(x - q * 0.78, y - q * 0.78), (x + q * 0.78, y + q * 0.78)], False), ([(x - q * 0.78, y + q * 0.78), (x + q * 0.78, y - q * 0.78)], False)]
        elif kind == "square":
            shapes = [([(x - q * 0.8, y - q * 0.8), (x + q * 0.8, y - q * 0.8), (x + q * 0.8, y + q * 0.8), (x - q * 0.8, y + q * 0.8)], True)]
        else:
            shapes = [([(x + q * math.cos(math.radians(60 * j)), y + q * math.sin(math.radians(60 * j))) for j in range(6)], True)]
        for k, (pts, closed) in enumerate(shapes):
            if closed:
                pts = [p for a, b in zip(pts, pts[1:] + pts[:1]) for p in (a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))]
            _straight_pencil(target, pts, closed, 0.7, 33 + k, alpha, color)
        return
    b = _button(kind, r, round(clamp(pressed) * 4) / 4)
    if lit > 0:
        glow(target, x, y, r * 1.9, lt(PAL[BUTTONS[kind]], 1.15), lit)
    _comp(target, shadow_of(b.getchannel("A"), max(2, r * 0.12), 0.5), (x - b.size[0] / 2 + r * 0.08, y - b.size[1] / 2 + r * 0.14))
    _comp(target, b, (x - b.size[0] / 2, y - b.size[1] / 2))


def _straight_pencil(target, pts, closed, weight, seed, alpha, color=None):
    """Pencil along straight runs (corners kept), one stroke per side."""
    P = list(pts) + ([pts[0]] if closed else [])
    for k, (a, b) in enumerate(zip(P, P[1:])):
        pencil_path(target, [a, b], weight, False, seed * 13 + k, alpha, wobble=0.3, color=color)


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


def die(target, n, x, y, size=44, angle=0.0, shadow=True, outline=False, alpha=1.0, color=None):
    """One face of an ivory die (n = 1..6) centred at (x, y); angle in degrees.
    outline=True draws only its pencil outline (rounded square and pips): the die before its painted double lands,
    and the way an UNWRITTEN bolt's die is shown at the end (color: None = graphite, Wd.CHALK on dark, Wd.DARK on brass)."""
    if outline:
        f = xf(angle, x, y)
        h = size / 2 - 1
        pencil_path(target, [f(px, py) for px, py in rrect(-h, -h, h, h, size * 0.2, 3)], 0.55, True, 40 + n, alpha, wobble=0.4, color=color)
        for k, (px, py) in enumerate(PIPS[int(n)]):
            cx, cy = f(px * size * 0.25, py * size * 0.25)
            pencil_path(target, circ(cx, cy, max(1.6, size * 0.06), 8), 0.8, True, 50 + k, alpha, wobble=0.0, color=color)
        return
    im = _die(int(n), int(size))
    if angle:
        im = im.rotate(-angle, Image.BICUBIC, expand=True)
    if shadow:
        _comp(target, shadow_of(im.getchannel("A"), max(2, size * 0.08), 0.5), (x - im.size[0] / 2 + size * 0.07, y - im.size[1] / 2 + size * 0.11))
    _comp(target, im, (x - im.size[0] / 2, y - im.size[1] / 2))


def die_at_bolt(target, n, port=None, r=None, size=40, lit=True, outline=False, t=0.0, ring_w=None):
    """Die face n sitting on bolt n of a porthole ring (bolt 1 at the top, then clockwise: 2 upper right, 3 lower
    right, 4 bottom, 5 lower left, 6 upper left). port, r = the glass centre and radius (default: the seat's
    porthole, PORT and PORT_R; from the river pass the tin's p["port"], p["port_r"] and ring_w = 17 * scale).
    lit=True puts the amber glow of a written ending under it; outline=True draws the die in outline only, in dark
    pencil on the brass (an unwritten bolt). Returns the bolt's (x, y)."""
    port = PORT if port is None else port
    r = PORT_R if r is None else r
    bx, by = bolt_xy(int(n), port[0], port[1], r, r + (RING_W if ring_w is None else ring_w))
    if lit and not outline:
        glow(target, bx, by, size * 1.5, (255, 186, 70), 0.85 + 0.15 * math.sin(t * 5 + n))
    die(target, n, bx, by, size, outline=outline, color=DARK if outline else None)
    return (bx, by)


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
def _cup_side(scale_q):
    """A leather dice cup standing upright, seen from the side, and the one die resting in its mouth, a corner up:
    edge-on, no face presented. Design: base centre (0, 0), cup 150 wide at the mouth, 170 tall."""
    sc = scale_q / 100.0
    leather = (120, 74, 44)

    def wall_deco(d, L, S):
        for k in range(24):                             # the stitched seam down the side
            y = -158 + k * 6.6
            d.line([L(-6 - y * 0.02, y), L(4 - y * 0.02, y + 3)], fill=(226, 200, 150), width=S)
        for yy in (-150, -22):
            d.line([L(-80, yy), L(80, yy)], fill=dk(leather, 0.7), width=2 * S)
            for k in range(26):
                x = -72 + k * 5.8
                d.line([L(x, yy + 5), L(x + 3, yy + 5)], fill=(226, 200, 150), width=S)
    wall = cut([(-75, -166), (75, -166), (60, 0), (-60, 0)], leather, wall_deco, curve=False, seed=881, grain=0.12)
    a = np.asarray(wall.img, np.float32).copy()             # turn it: a round cup under the lamp
    u = np.linspace(-1, 1, a.shape[1])[None, :]
    a[..., :3] *= (0.62 + 0.52 * np.exp(-((u + 0.38) / 0.42) ** 2) + 0.10 * np.exp(-((u - 0.86) / 0.12) ** 2))[..., None]
    wall = Sprite(to_img(a).convert("RGBA"), wall.ox, wall.oy)
    inside = cut(circ(0, -166, 75, 36, 17), (36, 22, 16), curve=False, seed=882, edge=0.3)
    lip = cut(circ(0, -166, 75, 36, 17)[:19][::-1] + circ(0, -160, 77, 36, 19)[:19], dk(leather, 1.15), curve=False, seed=883)
    foot = cut(rrect(-64, -4, 64, 8, 4), dk(leather, 0.7), curve=False, seed=884)
    # the die: a cube balanced on the back rim, one corner up; two faces seen edge-on and turned away, their pips
    # squashed to slivers and cut off by the lip, so that no number can be read
    c = (6, -182)
    top, left, right, low = (c[0] + 2, c[1] - 40), (c[0] - 34, c[1] - 6), (c[0] + 36, c[1] - 10), (c[0] - 2, c[1] + 30)

    def die_deco(d, L, S):
        d.polygon([L(*top), L(*right), L(*low), L(c[0] + 1, c[1] - 4)], fill=dk(PAL["ivory"], 0.84))
        d.line([L(*top), L(c[0] + 1, c[1] - 4), L(*low)], fill=dk(PAL["ivory"], 0.66), width=S)
        for (px, py) in ((-17, -8), (-10, 6)):
            d.ellipse([L(c[0] + px - 2.2, c[1] + py - 5), L(c[0] + px + 2.2, c[1] + py + 5)], fill=(30, 28, 30))
        for (px, py) in ((16, -12), (20, 4), (12, 0)):
            d.ellipse([L(c[0] + px - 1.8, c[1] + py - 4.6), L(c[0] + px + 1.8, c[1] + py + 4.6)], fill=(30, 28, 30))
    cube = cut([top, right, low, left], PAL["ivory"], die_deco, curve=False, seed=885)
    spr = compose([foot, inside, cube, wall, lip])
    if sc != 1.0:
        im = spr.img.resize((max(1, int(spr.img.size[0] * sc)), max(1, int(spr.img.size[1] * sc))), Image.LANCZOS)
        spr = Sprite(im, int(spr.ox * sc), int(spr.oy * sc))
    return spr


def die_cup_side(target, x, y, scale=1.0):
    """THE DIE IS STILL IN THE CUP: a leather dice cup standing upright with the one die resting in its mouth, a corner
    up, seen edge-on so that no face is presented. (x, y) = centre of the cup's base on the table; the cup is
    150 * scale wide and 185 * scale tall, the die's corner reaching 224 * scale above the base. It does not move."""
    spr = _cup_side(int(round(scale * 100)))
    _comp(target, shadow_of(spr.img.getchannel("A"), 9 * scale, 0.5), (x + spr.ox + 10 * scale, y + spr.oy + 10 * scale))
    _comp(target, spr.img, (x + spr.ox, y + spr.oy))


@lru_cache(None)
def _tag(text):
    f = font("serif", 19 * 3)
    tw = int(f.getlength(text) / 3) + 22
    return cut(rrect(0, 0, tw, 30, 5), (236, 228, 204), lambda d, L, S: d.text(L(tw / 2, 14.5), text, font=font("serif", 19 * S), fill=(52, 44, 38), anchor="mm"),
               curve=False, seed=861)


def bolt_tag(target, n, x=18, y=14, label=False):
    """The bolt's label for the top LEFT corner: die face n (1..6) and a paper tag reading Probable (1, 4),
    Plausible (2, 5) or Preposterous (3, 6). (x, y) = top-left corner."""
    die(target, n, x + 19, y + 19, 38)
    if label:
        draw_sprite(target, _tag(KIND[int(n)]), Tm(x + 48, y + 4), (1.5, 2.5, 2.0, 0.4))


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


def seat(target, t=0.0, wave_kw=None, twin_kw=None, level=1.0, heads=True, twin_lamp=1.0, twin_occupants=1, lit=(), ripple_t0=None, seed=0):
    """A whole SEAT frame in the standard layout, as a starting point (copy what you need from its body): the river
    through the glass, the three monster heads behind the twin tin, the cabin wall with the porthole (PORT, PORT_R),
    the air gauge lower left, Turkey's back lower right. wave_kw / twin_kw = wave_pose() dicts. Returns
    {"twin": tin points, "turkey": turkey_back points, "cabin": cabin dict, "heads": [...]}."""
    wave_kw = wave_kw or {}
    twin_kw = twin_kw or {"mirror": True}
    river(target, t, 0.0, seed)
    hs = []
    if heads:
        for k, (bx, hx, hy, fl, bd) in enumerate(SEAT_HEADS):
            idle = monster_idle(t, k)
            hs.append(monster_neck(target, (bx, 520), (hx + idle["dx"] * 0.5, hy + idle["dy"] * 0.5), SEAT_HEAD_SCALE, bd, 10 + idle["tilt"], 4, idle["look"], fl, k, t, shade=0.12))
    tw = tin(target, SEAT_TWIN[0], SEAT_TWIN[1] + 3 * math.sin(t * 1.1), SEAT_TWIN[2], t, flip=True, lamp=twin_lamp, occupants=twin_occupants, **twin_kw)
    river_plane(target, "front", t, 0.0, seed)
    if ripple_t0 is not None:
        ripple(target, PORT[0], PORT[1], PORT_R, t, ripple_t0)
    cb = cabin(target, t, lit=lit)
    air_gauge(target, SEAT_GAUGE[0], SEAT_GAUGE[1], level, SEAT_GAUGE[2], t)
    tk = turkey_back(target, SEAT_TURKEY[0], SEAT_TURKEY[1], SEAT_TURKEY[2], t=t, shade=0.16, **wave_kw)
    return {"twin": tw, "turkey": tk, "cabin": cb, "heads": hs}


SEAT_TWIN = (440, 296, 0.48)                # the twin tin through the glass: x, y, scale
SEAT_HEADS = [(340, 396, 156, False, -0.10), (452, 492, 112, False, 0.06), (566, 506, 190, True, 0.12)]     # neck root x, head joint x, y, flip, bend
SEAT_HEAD_SCALE = 0.72
SEAT_GAUGE = (104, 392, 50)                 # air gauge: x, y, r
SEAT_TURKEY = (748, 398, 1.45)              # Turkey's shoulder pin and scale
SEAT_OTHER = (212, 430, 1.45)               # bolt 3: the other turkey's shoulder pin (draw turkey_back with mirror=True)


# ====================================================================== test
def _sheet(images, cols, path, scale=0.5):
    w, h = int(W * scale), int(H * scale)
    rows = (len(images) + cols - 1) // cols
    sh = Image.new("RGB", (cols * (w + 6) + 6, rows * (h + 6) + 6), (60, 60, 60))
    for k, im in enumerate(images):
        sh.paste(im.resize((w, h), Image.LANCZOS), (6 + (k % cols) * (w + 6), 6 + (k // cols) * (h + 6)))
    sh.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/c16_world")
    out.mkdir(parents=True, exist_ok=True)
    which = sys.argv[2:] or ["table", "seat", "river", "ending", "parts"]
    from kit import Ink
    if "table" in which:
        frames = []
        for k, tt in enumerate((1.5, 3.2, 3.7, 5.2, 7.4, 9.0)):
            ink = Ink(tt, k)
            desk(ink, (40, -60, 930, 620))
            sheet_ring(ink, 400, 440, 1.6)
            p = pilot_progress(tt)
            pilot_drawing(ink, 400, 440, p, 1.6)
            tx, ty, down = pilot_tip(400, 440, p, 1.6)
            if tt < 8.6:
                pencil(ink, tx, ty, lift=0 if down else 14)
            badge(ink)
            frames.append(ink.finish())
        frames[-1].save(out / "table_full.png")
        _sheet(frames, 3, out / "table.png")
    if "seat" in which:
        frames = []
        en = lambda tt: lerp(1.0, 0.25, ramp(tt, 0, 8))
        for k in range(6):
            t = 0.4 + k * 1.3
            ink = Ink(t, k)
            wk = wave_pose(t, en) if k else {}
            tk = wave_pose(t, en, twin=True) if k else {"mirror": True}
            r = seat(ink, t, wk, tk, level=needle(t, (1.0, 2.0, 3.0, 4.0)), twin_lamp=0.0 if k == 0 else 1.0, twin_occupants=2 if k == 5 else 1,
                     lit=(3,) if k >= 4 else (), ripple_t0=2.4 if k == 2 else None)
            if k >= 4:
                turkey_back(ink, SEAT_OTHER[0], SEAT_OTHER[1], SEAT_OTHER[2], t=t - DT, shade=0.16, **{**wave_pose(t, en, twin=True), "mirror": True})
                die_at_bolt(ink, 3)
            if k == 3:
                c = pick_card(ink, "triangle", "Pond mirror", "B.", 160, 356, paint=1.0, drawn=0.7, pressed=1.0, lit=1.0)
                x_, y_, dn = friend_tip(c["mark_kind"], c["mark"][0], c["mark"][1], 0.7, c["mark_scale"])
                pencil(ink, x_, y_)
            if k == 1:
                pick_card(ink, "triangle", "Pond mirror", "B.", 160, 356, paint=0.0)
            bubble_pair(ink, 300, 300, t, 1.0 + k * 0.2, n=4 if k >= 4 else 2)
            badge(ink)
            if k in (0, 2, 4, 5):
                ink.caption(["A giant three-headed monster.", "", "Wave at his twin turkey.", "", "There is another turkey here.", "There is another turkey here."][k], size=27)
            frames.append(ink.finish())
        ink = Ink(0, 0)
        r = seat(ink, 5.0, wave_pose(5.0, 0.6), wave_pose(5.0, 0.6, twin=True), lit=(3,))
        turkey_back(ink, SEAT_OTHER[0], SEAT_OTHER[1], SEAT_OTHER[2], t=4.5, shade=0.16, **{**wave_pose(5.0, 0.6, twin=True), "mirror": True})
        frames.append(ink.finish())
        ink = Ink(0, 0)
        seat(ink, 5.0, {**wave_pose(5.0, 0.6), "head": "seat"}, wave_pose(5.0, 0.6, twin=True), lit=(3,), twin_occupants=2)
        turkey_back(ink, SEAT_OTHER[0], SEAT_OTHER[1], SEAT_OTHER[2], t=4.5, shade=0.16, **{**wave_pose(5.0, 0.6, twin=True), "mirror": True})
        camera(ink, 300, 330, 1.5)
        badge(ink)
        frames.append(ink.finish())
        ink = Ink(0, 0)
        empty_stage(ink)
        cabin(ink, 0)
        die_at_bolt(ink, 1, lit=False)
        ring_outline(ink, 760, 420, 60, 80, color=CHALK)
        badge(ink)
        frames.append(ink.finish())
        frames[4].save(out / "seat_full.png")
        frames[-2].save(out / "seat_full2.png")
        _sheet(frames, 3, out / "seat.png")
    if "river" in which:
        frames = []
        for k in range(6):
            t = 0.5 + k * 0.9
            ink = Ink(t, k)
            river(ink, t, 0.0, seed=1)
            monster(ink, 520, 470, 1.0, t, shade=0.18)
            e = 0.3
            p = tin(ink, 330, 330, 0.8, t, dial=needle(t, (1, 2, 3), 0.5), **wave_pose(t, e))
            tin(ink, 760, 300, 0.62, t, flip=True, **wave_pose(t, e, twin=True))
            lift = [None, 260, 120, 30, 0, 0][k]
            if lift is not None:
                tin_monster(ink, 330, 330, 0.8, t, lift=lift, nod=(6 * settle(t, 3.9), -6 * settle(t, 3.9 + DT)), port=p)
            trout_pair(ink, lambda tt: (700 - 30 * tt, 450 + 8 * math.sin(tt * 2), 4 * math.sin(tt * 2)), t, 0.5, pose="look")
            bubble_pair(ink, p["pipe"][0], p["pipe"][1], t, 0.3 + k * 0.8)
            river_plane(ink, "front", t, 0.0, seed=1)
            if k == 0:
                c = pick_card(ink, "cross", "Two-headed tin monster", "W.", 160, 356, drawn=0.8, pressed=1.0, lit=1.0)
                x_, y_, dn = friend_tip(c["mark_kind"], c["mark"][0], c["mark"][1], 0.8, c["mark_scale"])
                pencil(ink, x_, y_)
            if k == 1:
                pick_card(ink, "cross", "Two-headed tin monster", "W.", 160, 356, paint=0.0)
            if k >= 3:
                die_at_bolt(ink, 5, p["port"], p["port_r"], size=24, ring_w=17 * 0.8)
            bolt_tag(ink, 5)
            badge(ink)
            if k >= 3:
                ink.caption("Two-headed tin monster fits the submarine.", size=27)
            frames.append(ink.finish())
        frames[4].save(out / "river_full.png")
        frames[2].save(out / "river_full2.png")
        _sheet(frames, 3, out / "river.png")
    if "ending" in which:
        frames = []
        ink = Ink(0, 0)
        table(ink)
        ring = brass_ring(150, 196, fittings=True)
        _comp(ink, shadow_of(ring.getchannel("A"), 9, 0.6), (380 - ring.size[0] / 2 + 7, 262 - ring.size[1] / 2 + 11))
        ImageDraw.Draw(ink.img).ellipse([380 - 152, 262 - 152, 380 + 152, 262 + 152], fill=(14, 30, 30))
        _comp(ink, ring, (380 - ring.size[0] / 2, 262 - ring.size[1] / 2))
        for n in range(1, 7):
            die_at_bolt(ink, n, (380, 262), 150, size=38, lit=n in (3, 5), outline=n not in (3, 5), ring_w=46)
        die_cup_side(ink, 790, 470, 1.0)
        badge(ink)
        frames.append(ink.finish())
        frames[0].save(out / "ending_full.png")
        ink = Ink(0, 0)
        table(ink)
        page(ink, (60, 40, 900, 600))
        for k, kind in enumerate(BUTTONS):
            button(ink, kind, 150 + k * 150, 120, 44, pressed=1.0 if k == 1 else 0.0, lit=1.0 if k == 1 else 0.0)
            button(ink, kind, 150 + k * 150, 230, 44, outline=True)
        for n in range(1, 7):
            die(ink, n, 150 + (n - 1) * 100, 330, 56, angle=(n - 3) * 6)
            die(ink, n, 150 + (n - 1) * 100, 410, 56, angle=(n - 3) * 6, outline=True)
        controller(ink, 300, 490, 1.0, pressed="cross")
        die_cup(ink, 700, 470)
        bolt_tag(ink, 3)
        badge(ink)
        frames.append(ink.finish())
        ink = Ink(0, 0)
        empty_stage(ink)
        die(ink, 4, 480, 270, 80)
        badge(ink)
        frames.append(ink.finish())
        _sheet(frames, 3, out / "ending.png")
    if "parts" in which:
        frames = []
        for k, (a, e) in enumerate(((0, 1.0), (60, 1.0), (112, 1.0), (40, 0.3))):
            ink = Ink(0, 0)
            page(ink, (-20, -20, 980, 560))
            turkey_back(ink, 250, 230, 1.0, wing=a, tip=[0, 14, -10, 20][k], head="seat" if k == 3 else "glass")
            turkey_front(ink, 640, 250, 1.0, wing=a, tip=[0, 14, -10, 20][k], wattle=k * 5, mirror=k == 3)
            turkey(ink, 880, 380, 0.5, "calm", 0.0)
            badge(ink)
            frames.append(ink.finish())
        frames[2].save(out / "parts_full.png")
        ink = Ink(0, 0)
        river_back(ink, 0)
        for k in range(3):
            monster_neck(ink, (180 + k * 300, 560), (240 + k * 260, 200 + 40 * k), 1.0, [-0.2, 0.15, 0.3][k], [0, 20, -15][k], [4, 22, 10][k], flip=k == 2, kind=k)
        badge(ink)
        frames.append(ink.finish())
        frames[-1].save(out / "monster_full.png")
        ink = Ink(0, 0)
        river_back(ink, 0)
        p = tin(ink, 300, 400, 1.0, 0.0, dial=0.5, wing=90)
        tin_monster(ink, 300, 400, 1.0, 0, lift=0, port=p)
        tin(ink, 760, 150, 0.6, 0.0, flip=True, wing=-90, occupants=2)
        tin(ink, 760, 300, 0.6, 0.0, flip=True, lamp=0.0)
        tin_monster(ink, 740, 520, 0.5, 0, lift=40, nod=(8, -8))
        badge(ink)
        frames.append(ink.finish())
        frames[-1].save(out / "tin_full.png")
        _sheet(frames, 3, out / "parts.png")
    for f in range(0, 400):                              # the rule's invariant, for the critic
        tt = f / FPS
        assert abs(twin_wave(tt, 0.7, 1.0) + wave((f - D) / FPS, 0.7, 1.0)) < 1e-9
    print("wrote", out)
