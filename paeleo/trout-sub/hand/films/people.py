"""people.py · the children and their desk, as cut paper, for the five making films (mNN) to share.

Everything here is HANDMADE in code, nothing is foraged. The children are hands, sleeves and backs of heads cut
from poster paper (teal, rust, ochre, plum: never skin colours, never faces); every piece is its own sheet with
fibre, a lit and a dark cut edge and a shadow on the piece beneath (the technique of films/swarm/c16/world.py,
rebuilt here so this module depends only on the kit). The Porthole Log is redrawn from ../sheets/master-1.png,
master-2.png and ../sheets/steps.json; the children's writing is lettered stroke by stroke from a pencil alphabet.

Every drawing function takes `target` first: the kit's Ink, or any PIL image (RGB or RGBA) of any size.
See PEOPLE.md for the list, arguments, coordinates and example calls.

    python3 films/people.py            # writes test stills of every piece to films/stills/people/
"""
from __future__ import annotations

import json
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FILMS = Path(__file__).resolve().parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import W, H, font, clamp, lerp  # noqa: E402

ROOT = FILMS.parent.parent          # trout-sub/
STILLS = FILMS / "stills" / "people"

# ---------------------------------------------------------------- palette ---
PAPER = (250, 247, 239)             # the worksheet's paper
PRINT = (22, 41, 58)                # the worksheet's printing ink
GRAPHITE = (62, 62, 70)
DESK = (160, 122, 84)
FLOOR = (128, 144, 138)
CREAM = (238, 228, 204)

# One child = one tone. hand = the paper the hand, neck and ears are cut from; sleeve = jumper; cuff = its band;
# hair = the back of the head. None of these is a skin colour, by rule.
TONES = {
    "teal": dict(hand=(46, 142, 138), sleeve=(24, 80, 92), cuff=(232, 196, 96), hair=(18, 46, 58)),
    "rust": dict(hand=(206, 88, 46), sleeve=(118, 42, 30), cuff=(238, 226, 200), hair=(64, 26, 22)),
    "ochre": dict(hand=(226, 174, 50), sleeve=(146, 100, 22), cuff=(54, 92, 104), hair=(86, 58, 16)),
    "plum": dict(hand=(140, 72, 128), sleeve=(76, 34, 76), cuff=(226, 150, 96), hair=(40, 20, 46)),
}
TONE_NAMES = ("teal", "rust", "ochre", "plum")


def tone_of(tone):
    return TONES[tone] if isinstance(tone, str) else tone


# ------------------------------------------------------------------ basics ---
def _img(target):
    return target.img if hasattr(target, "img") else target


def _sync(target):
    if hasattr(target, "d") and hasattr(target, "img"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


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


def shadow_of(alpha_img, blur, strength, color=(10, 10, 14)):
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


def mixc(a, b, x):
    return tuple(int(round(lerp(p, q, x))) for p, q in zip(a[:3], b[:3]))


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


def Tm(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)


def Rm(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]], np.float64)


def Sm(sx, sy=None):
    return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], np.float64)


def apply(M, p):
    return (float(M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2]), float(M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2]))


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


def draw_sprite(target, spr, M, shadow=(2.0, 2.8, 1.5, 0.36), clip_shadow=False):
    """Lay a Sprite on the target under the affine M (design px -> target px), with its shadow.
    clip_shadow=True keeps the shadow on what is already drawn (pieces of one puppet on a clear layer)."""
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
        sx, sy = x0c + shadow[0] * sc, y0c + shadow[1] * sc
        if clip_shadow and layer.mode == "RGBA":
            tmp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            _comp(tmp, sh, (sx, sy))
            tmp.putalpha(ImageChops.multiply(tmp.getchannel("A"), layer.getchannel("A")))
            layer.alpha_composite(tmp)
        else:
            _comp(layer, sh, (sx, sy))
    _comp(layer, out, (x0c, y0c))


def _lay_group(target, layer, drop=(7, 10, 7, 0.34), alpha=1.0, shade=0.0):
    """Lay a whole puppet (drawn on its own clear layer the size of the target) down with one soft shadow."""
    if shade > 0:
        a = layer.getchannel("A")
        layer = Image.blend(layer.convert("RGB"), Image.new("RGB", layer.size, (14, 18, 22)), clamp(shade)).convert("RGBA")
        layer.putalpha(a)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    box = layer.getbbox()
    if box is None:
        return
    if drop:
        pad = int(drop[2] * 3 + 4)
        bx = (max(0, box[0] - pad), max(0, box[1] - pad), min(layer.size[0], box[2] + pad), min(layer.size[1], box[3] + pad))
        _comp(target, shadow_of(layer.crop(bx).getchannel("A"), drop[2], drop[3] * alpha), (bx[0] + drop[0] - MG, bx[1] + drop[1] - MG))
    _comp(target, layer.crop(box), (box[0] - MG, box[1] - MG))
    _sync(target)


MG = 64     # a puppet's own layer is this much larger than the target all round, so shadows do not stop at the frame


def _clear(target):
    w, h = _img(target).size
    return Image.new("RGBA", (w + 2 * MG, h + 2 * MG), (0, 0, 0, 0))


def _unmg(info):
    for k, v in list(info.items()):
        if isinstance(v, tuple) and len(v) == 2:
            info[k] = (v[0] - MG, v[1] - MG)
    return info


# ================================================================ THE PENCIL
PENCIL_LEN = 232.0


@lru_cache(None)
def _pencil():
    def body_deco(d, L, S):
        d.polygon([L(40, -7.5), L(190, -7.5), L(190, -2.5), L(40, -2.5)], fill=(250, 214, 96))
        d.polygon([L(40, 2.5), L(190, 2.5), L(190, 7.5), L(40, 7.5)], fill=(196, 150, 40))
        for x in (96, 99, 131):                                 # tooth marks: somebody chews this pencil
            d.line([L(x, -6), L(x + 2, -1)], fill=(170, 128, 36), width=S)
    body = cut([(40, -7.5), (190, -7.5), (190, 7.5), (40, 7.5)], (232, 186, 62), body_deco, curve=False, seed=821)

    def cone_deco(d, L, S):
        d.polygon([L(0, 0), L(12, -2.0), L(12, 2.0)], fill=(52, 50, 56))
        for k in range(3):
            d.line([L(13, -1.8 + k * 1.8), L(40, -6 + k * 6)], fill=(196, 160, 110), width=S)
    cone = cut([(0, 0), (40, -7.5), (40, 7.5)], (226, 192, 142), cone_deco, curve=False, seed=822)

    def fer_deco(d, L, S):
        for x in (194, 200, 206):
            d.line([L(x, -8), L(x, 8)], fill=(120, 124, 126), width=S)
    fer = cut([(190, -8), (211, -8), (211, 8), (190, 8)], (176, 180, 182), fer_deco, curve=False, seed=823)

    def rub_deco(d, L, S):
        d.ellipse([L(224, -5)[0], L(224, -5)[1], L(232, 5)[0], L(232, 5)[1]], fill=(196, 150, 150))   # worn, grey with graphite
    rub = cut(rrect(211, -7.5, 232, 7.5, 5), (226, 132, 138), rub_deco, curve=False, seed=824)
    return compose([rub, body, cone, fer])


def _pencil_M(x, y, angle, eraser_down=False, scale=1.0):
    if eraser_down:
        return Tm(x, y) @ Rm(angle) @ Sm(scale) @ Sm(-1, 1) @ Tm(-PENCIL_LEN, 0)
    return Tm(x, y) @ Rm(angle) @ Sm(scale)


def pencil(target, x, y, angle=-52.0, eraser_down=False, lift=0.0, scale=1.0):
    """A chewed yellow pencil on its own. Its touching end is at (x, y) and it lies away along `angle` degrees
    (0 = to the right, -52 = up and to the right). eraser_down=False: the point touches; True: the rubber touches.
    lift (px) raises it off the paper: the shadow slides away and softens. Returns the far end (x, y)."""
    tmp = _clear(target)
    M = Tm(MG, MG) @ _pencil_M(x - lift * 0.1, y - lift * 0.35, angle, eraser_down, scale)
    draw_sprite(tmp, _pencil(), M, None)
    _lay_group(target, tmp, (5 + lift * 0.5, 7 + lift * 0.9, 2.5 + lift * 0.12, 0.42 * (1 - min(0.5, lift / 120))))
    a = math.radians(angle)
    return (x + PENCIL_LEN * scale * math.cos(a), y + PENCIL_LEN * scale * math.sin(a))


@lru_cache(None)
def _crumb(k):
    rs = random.Random(900 + k)
    n = rs.randint(3, 5)
    L = rs.uniform(5, 11)
    pts = []
    for j in range(n):                                          # a little rolled worm of rubber
        f = j / (n - 1)
        pts.append((L * (f - 0.5), 2.2 * math.sin(f * 3.1 + rs.uniform(0, 2)) - 1.5 - rs.uniform(0, 0.6)))
    pts += [(p[0], p[1] + 3.0 + rs.uniform(0, 0.8)) for p in reversed(pts)]
    col = mixc((226, 132, 138), (120, 116, 122), rs.uniform(0.25, 0.7))
    return cut(pts, col, seed=910 + k, grain=0.12, edge=0.6)


def eraser_crumbs(target, x, y, n=12, seed=0, spread=34.0, scale=1.0):
    """n rubbings (little grey-pink rolls of rubber and graphite) scattered round (x, y). The same seed gives the
    same crumbs in the same order, so raise n over time to let them pile up; sweep them away by moving (x, y)."""
    rs = random.Random(seed * 131 + 7)
    for k in range(int(n)):
        a, r = rs.uniform(0, 6.283), spread * scale * (rs.random() ** 0.6)
        M = Tm(x + r * math.cos(a) * 1.5, y + r * math.sin(a) * 0.7) @ Rm(rs.uniform(0, 360)) @ Sm(scale * rs.uniform(0.7, 1.15))
        draw_sprite(target, _crumb(rs.randrange(9)), M, (0.8, 1.2, 0.8, 0.4))
    _sync(target)


def rub_mark(target, box, strength=1.0, seed=0, color=PAPER):
    """A rubbed-out patch over box = (x0, y0, x1, y1): the paper comes back scuffed and a shade greyer, and whatever
    was written there (draw it first) stays as a ghost of graphite. strength 0 = untouched .. 1 = rubbed as clean
    as a school rubber gets. The patch has soft uneven ends, the way the rubber went back and forth."""
    s = clamp(strength)
    if s <= 0:
        return
    img = _img(target)
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    pad = 8
    X0, Y0 = x0 - pad, y0 - pad
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    if w < 4 or h < 4:
        return
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = vnoise((h, w), 26, 7, 40 + seed, 2)
    n2 = vnoise((h, w), 3, None, 41 + seed)
    streak = vnoise((h, w), 60, 2.2, 42 + seed, 2)              # the rubber's back-and-forth, along the line
    ex = np.clip(np.minimum(xx - pad * 0.3, w - pad * 0.3 - xx) / (pad * 1.6) + n1 * 0.9, 0, 1)
    ey = np.clip(np.minimum(yy - pad * 0.3, h - pad * 0.3 - yy) / (pad * 1.3) + n1 * 0.7, 0, 1)
    m = ex * ey
    cover = m * (0.80 + 0.10 * streak + 0.05 * n2) * s          # never the whole way: the ghost stays
    grey = np.array(color, np.float32) * (1 - 0.045 * s) - 6 * s * (0.5 + 0.5 * streak)[..., None] - 3 * n2[..., None] * s
    patch = np.dstack([np.clip(grey, 0, 255), np.clip(cover, 0, 0.9) * 255]).astype(np.uint8)
    _comp(img, Image.fromarray(patch, "RGBA"), (X0, Y0))
    sm = np.zeros((h, w, 4), np.uint8)                          # the smear of graphite dragged along by the rubber
    sm[..., :3] = GRAPHITE
    sm[..., 3] = (np.clip(m * (0.5 + 0.5 * streak) * 0.10 * s, 0, 1) * 255).astype(np.uint8)
    _comp(img, Image.fromarray(sm, "RGBA"), (X0 + 3, Y0))
    _sync(target)


# ================================================================== THE HAND
# A right hand seen from above (the child's own eye). Two drawings share one arm:
#   the FLAT hand (back of the hand up, fingers on pins at the knuckles): hold, point, tap, pass, scratch, fist_chin;
#   the WRITING hand (resting on its little-finger edge, thumb side up, pencil through the web): write, hover, erase.
@lru_cache(None)
def _cap(L, w0, w1, color, seed):
    """One finger bone / arm piece: a tapered round-ended strip from (0, 0) to (L, 0)."""
    r0, r1 = w0 / 2.0, w1 / 2.0
    pts = [(r0 * math.cos(math.radians(a)), r0 * math.sin(math.radians(a))) for a in range(90, 271, 18)]
    pts += [(L + r1 * math.cos(math.radians(a)), r1 * math.sin(math.radians(a))) for a in range(-90, 91, 18)]
    return cut(pts, color, curve=False, seed=seed)


def _seg(layer, M, p, q, w0, w1, color, seed, sh=(1.2, 1.8, 1.3, 0.38)):
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    if d < 1.0:
        return
    L = max(2, int(round(d)))
    spr = _cap(L, int(round(w0)), int(round(w1)), tuple(color), seed)
    draw_sprite(layer, spr, M @ Tm(p[0], p[1]) @ Rm(math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))) @ Sm(d / L, 1.0), sh, clip_shadow=True)


@lru_cache(None)
def _nail(w, color):
    return cut(rrect(-w * 0.34, -w * 0.30, w * 0.30, w * 0.30, w * 0.26), lt(color, 1.2), curve=False, seed=77, edge=0.5)


def _finger(layer, M, pts, w, color, seed, nail=True, taper=0.93):
    """A finger on its pins: bones from the knuckle (pts[0]) to the tip, each lapping the one before."""
    ww = w
    last = None
    for k in range(len(pts) - 1):
        if math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) < 1.0:
            continue
        _seg(layer, M, pts[k], pts[k + 1], ww, ww * taper, color, seed + k)
        last = (pts[k], pts[k + 1], ww * taper)
        ww *= taper
    if nail and last and len(pts) >= 4 and math.hypot(pts[3][0] - pts[2][0], pts[3][1] - pts[2][1]) > 9:
        p, q, wn = last
        a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        draw_sprite(layer, _nail(int(round(wn)), tuple(color)), M @ Tm(q[0], q[1]) @ Rm(a), None)


def _chain(k, heading, lens, bend=0.0, fore=(1, 1, 1)):
    """Joint points of a finger in the flat-hand frame: heading in degrees, 0 = up the hand, + clockwise."""
    pts = [k]
    h = heading
    x, y = k
    for i, l in enumerate(lens):
        l = l * fore[i]
        a = math.radians(h)
        x, y = x + l * math.sin(a), y - l * math.cos(a)
        pts.append((x, y))
        h += bend
    return pts


@lru_cache(None)
def _sleeve(tone_key):
    tn = dict(tone_key)

    def deco(d, L, S):
        d.polygon([L(0, -44), L(30, -44), L(30, 44), L(0, 44)], fill=tn["cuff"])
        for k in range(-5, 6):                                  # rib of the cuff
            d.line([L(2, k * 7.6), L(28, k * 7.6)], fill=dk(tn["cuff"], 0.82), width=S)
        d.line([L(31, -44), L(31, 44)], fill=dk(tn["sleeve"], 0.7), width=2 * S)
        for x in range(90, 1400, 150):                          # folds of the jumper along the arm
            d.line([L(x, -30), L(x + 46, 34)], fill=dk(tn["sleeve"], 0.88), width=2 * S)
    return cut([(0, -34), (30, -37), (1400, -72), (1400, 72), (30, 37), (0, 34)], tn["sleeve"], deco, curve=False, seed=31)


def _wrist(layer, M, wrist, direction, tn, w=60):
    a = math.radians(direction)
    q = (wrist[0] + 44 * math.cos(a), wrist[1] + 44 * math.sin(a))
    _seg(layer, M, (wrist[0] - 12 * math.cos(a), wrist[1] - 12 * math.sin(a)), q, w, w, tn["hand"], 40, None)


def _arm(layer, M, wrist, direction, tn):
    """The wrist and the sleeved forearm, leaving `wrist` along `direction` (design degrees, 0 = +x) for 1400 px:
    long enough to leave any frame."""
    a = math.radians(direction)
    key = tuple(sorted((k, tuple(v)) for k, v in tn.items()))
    draw_sprite(layer, _sleeve(key), M @ Tm(wrist[0] + 16 * math.cos(a), wrist[1] + 16 * math.sin(a)) @ Rm(direction), (1.5, 2.2, 1.6, 0.4), clip_shadow=True)


# -- the flat hand: wrist at (0, 0), fingers up the page (-y), thumb on the left (a right hand, back up)
_F = dict(index=((-34, -84), (29, 22, 19), 25.0), middle=((-10, -91), (32, 25, 21), 25.0),
          ring=((15, -88), (29, 23, 19), 24.0), pinky=((38, -77), (23, 18, 16), 21.0))
_THUMB = ((-38, -30), (34, 28), 28.0)
_PALM = [(-31, 6), (-46, -26), (-49, -60), (-47, -88), (-28, -100), (-4, -104), (22, -101), (48, -90), (53, -56), (46, -22), (33, 6), (0, 11)]


@lru_cache(None)
def _palm(color):
    def deco(d, L, S):
        for x, y in ((-34, -80), (-10, -87), (15, -84), (38, -73)):     # the four knuckles, pressed in
            d.arc([L(x - 10, y - 4)[0], L(x - 10, y - 4)[1], L(x + 10, y + 12)[0], L(x + 10, y + 12)[1]], 25, 155, fill=dk(color, 0.86), width=int(1.5 * S))
    return cut(_PALM, color, deco, seed=21)


_FLAT = {
    #            index            middle           ring             pinky            thumb (heading, bend, fore)
    "hold": dict(index=(-11, -1, (1, 1, 1)), middle=(-2, 0, (1, 1, 1)), ring=(7, 1, (1, 1, 1)), pinky=(18, 3, (1, 1, 1)), thumb=(-62, 16, (1, 1)), base=-38, anchor=(0, -52)),
    "point": dict(index=(-8, 1, (1, 1, 1)), middle=(-3, 18, (0.74, 0.34, 0)), ring=(5, 18, (0.70, 0.32, 0)), pinky=(14, 18, (0.66, 0.30, 0)), thumb=(-12, 42, (0.8, 0.86)), base=-38, anchor="index"),
    "pass": dict(index=(-8, 0, (0.5, 0, 0)), middle=(-3, 0, (0.5, 0, 0)), ring=(5, 0, (0.5, 0, 0)), pinky=(14, 0, (0.5, 0, 0)), thumb=(2, 24, (0.95, 0.95)), base=-38, anchor=(-14, -66)),
    "scratch": dict(index=(-16, 14, (1, 0.6, 0.36)), middle=(-5, 8, (1, 0.6, 0.36)), ring=(7, -8, (1, 0.6, 0.36)), pinky=(20, -14, (1, 0.6, 0.36)), thumb=(-56, 22, (1, 0.9)), base=-30, anchor="claw"),
    "fist_chin": dict(index=(-4, 0, (0.46, 0, 0)), middle=(-1, 0, (0.46, 0, 0)), ring=(3, 0, (0.44, 0, 0)), pinky=(8, 0, (0.42, 0, 0)), thumb=(-6, 34, (0.9, 0.8)), base=-8, anchor=(-2, -117)),
}
_FLAT["tap"] = dict(_FLAT["point"])

# the direction (screen degrees, 0 = right, 90 = down) in which the forearm leaves at angle 0, unflipped
ARM_DIR = {"write": 38.0, "hover": 38.0, "erase": 38.0, "hold": 52.0, "point": 52.0, "tap": 52.0, "pass": 52.0, "scratch": 60.0, "fist_chin": 82.0}
POSES = tuple(ARM_DIR)


def aim(pose, arm, flip=False):
    """The `angle` to give hand() so the forearm leaves towards screen direction `arm` (degrees: 0 right, 90 straight
    down, 180 left, 270 up). aim('write', 90) = an arm coming straight up from the bottom edge."""
    return arm - ((180.0 - ARM_DIR[pose]) if flip else ARM_DIR[pose])


def _draw_flat(layer, M, pose, t, tn, lift=0.0, edge=None):
    P = dict(_FLAT[pose])
    col = tn["hand"]
    ch = {}
    live = {}
    for name in ("index", "middle", "ring", "pinky"):
        h, b, f = P[name]
        live[name] = [h, b, list(f)]
    th, tb, tf = P["thumb"]
    info = {"down": True}
    # -- natural movement
    if pose == "hold":
        for i, name in enumerate(("index", "middle", "ring", "pinky")):
            live[name][0] += 0.8 * math.sin(t * 1.1 + i * 0.9)
        th += 1.5 * math.sin(t * 0.8)
    elif pose == "point":
        live["index"][0] += 0.7 * math.sin(t * 1.3)
    elif pose == "tap":
        ph = (t * 3.1) % 1.0                                    # three taps a second: up slow, down fast, a rest on the wood
        up = math.sin(math.pi * clamp(ph / 0.62)) ** 1.5 if ph < 0.62 else 0.0
        live["index"][2] = [1.0, 1.0 - 0.16 * up, 1.0 - 0.5 * up]
        live["index"][0] += -5.0 * up
        lift = lift + 6.0 * up
        info["down"] = up < 0.08
    elif pose == "scratch":
        for i, name in enumerate(("index", "middle", "ring", "pinky")):
            s = 0.5 + 0.5 * math.sin(t * 13.0 - i * 0.7)        # the four fingers rake one after another
            live[name][2] = [1.0, 0.5 + 0.22 * s, 0.26 + 0.3 * s]
            live[name][1] += 4 * s
    elif pose == "fist_chin":
        M = M @ Tm(0, 1.6 * math.sin(t * 1.2)) @ Rm(0.8 * math.sin(t * 0.7))
    for name in ("index", "middle", "ring", "pinky"):
        k, lens, w = _F[name]
        h, b, f = live[name]
        ch[name] = _chain(k, h, lens, b, f)
    tk, tl, tw = _THUMB
    thumb = _chain(tk, th, tl, tb, tf)
    # -- anchor
    if P["anchor"] == "index":
        k, lens, w = _F["index"]
        full = _chain(k, P["index"][0], lens, P["index"][1], (1, 1, 1))
        anchor = full[-1]
    elif P["anchor"] == "claw":
        a, b = _chain(_F["index"][0], P["index"][0], _F["index"][1], P["index"][1], P["index"][2])[-1], _chain(_F["middle"][0], P["middle"][0], _F["middle"][1], P["middle"][1], P["middle"][2])[-1]
        anchor = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 6)
    else:
        anchor = P["anchor"]
    R = Rm(P["base"])
    M = M @ Tm(*[-v for v in apply(R, anchor)]) @ R
    if pose == "scratch":
        M = M @ Tm(0, 3.0 * math.sin(t * 13.0))
    if pose == "tap" and lift:
        M = M @ Rm(-0.5 * lift / 5.0)
    # -- pieces, back to front
    if pose in ("fist_chin",):
        _seg(layer, M, thumb[0], thumb[1], tw, tw * 0.94, col, 60)
    _wrist(layer, M, (0, 2), 90, tn)
    if pose in ("hold", "scratch"):
        _finger(layer, M, [thumb[0], thumb[1], thumb[2]], tw, col, 60, nail=False)
    draw_sprite(layer, _palm(tuple(col)), M, (1.2, 1.8, 1.3, 0.38), clip_shadow=True)
    order = ("pinky", "ring", "middle", "index")
    for name in order:
        k, lens, w = _F[name]
        if pose == "pass":
            continue
        _finger(layer, M, ch[name], w, col, 50 + 4 * order.index(name), nail=True)
    if pose == "pass":
        # the four fingers are under the sheet: cut the hand off along the sheet's edge, then lay the thumb over it
        c = apply(M, anchor)
        tipw = apply(M, (anchor[0], anchor[1] - 100))
        fx, fy = tipw[0] - c[0], tipw[1] - c[1]                 # the way the fingers go, on screen
        if edge is None:
            ex, ey = -fy, fx
        else:
            ex, ey = math.cos(math.radians(edge)), math.sin(math.radians(edge))
        nx, ny = -ey, ex
        if nx * fx + ny * fy < 0:
            nx, ny = -nx, -ny
        ln = math.hypot(ex, ey) or 1.0
        ex, ey, nx, ny = ex / ln * 3000, ey / ln * 3000, nx / ln * 3000, ny / ln * 3000
        hole = Image.new("L", layer.size, 0)
        ImageDraw.Draw(hole).polygon([(c[0] - ex, c[1] - ey), (c[0] + ex, c[1] + ey), (c[0] + ex + nx, c[1] + ey + ny), (c[0] - ex + nx, c[1] - ey + ny)], fill=255)
        layer.paste((0, 0, 0, 0), (0, 0), hole)
    _arm(layer, M, (0, 2), 90, tn)
    if pose in ("point", "tap", "pass", "fist_chin"):
        _finger(layer, M, [thumb[0], thumb[1], thumb[2]], tw, col, 60, nail=False)
        if pose in ("pass",):
            draw_sprite(layer, _nail(int(tw * 0.9), tuple(col)), M @ Tm(*thumb[2]) @ Rm(math.degrees(math.atan2(thumb[2][1] - thumb[1][1], thumb[2][0] - thumb[1][0]))), None)
    info["tip"] = apply(M, ch["index"][-1])
    info["wrist"] = apply(M, (0, 0))
    info["thumb"] = apply(M, thumb[-1])
    info["knuckles"] = apply(M, (0, -92))
    return info, lift


# -- the writing hand: pencil point at (0, 0), pencil lying away along PEN_A, forearm leaving to the lower right
PEN_A = -52.0
_W = dict(
    palm=[(76, -96), (108, -92), (140, -64), (160, -20), (168, 30), (158, 70), (134, 82), (110, 66), (92, 36), (82, 2), (72, -36), (66, -70)],
    wrist=(150, 52), arm=38.0,
    index=[(86, -84), (56, -72), (42, -54), (31, -39)],
    middle=[(74, -22), (48, -13), (25, -9)],
    ring=[(100, 4), (77, 13), (73, 27)],
    pinky=[(116, 34), (96, 44), (93, 57)],
    thumb=[(92, 6), (63, -11), (41, -27)],
)


@lru_cache(None)
def _wpalm(color):
    def deco(d, L, S):
        d.arc([L(104, -30)[0], L(104, -30)[1], L(150, 66)[0], L(150, 66)[1]], 110, 235, fill=dk(color, 0.88), width=int(1.4 * S))     # the fold of the heel
    return cut(_W["palm"], color, deco, seed=22)


def _draw_write(layer, M, pose, t, tn, lift=0.0):
    col = tn["hand"]
    info = {"down": pose != "hover"}
    wob = 0.0
    if pose == "write":
        # the fingers push the point about while the heel stays put: a small, quick, uneven working of the grip
        wob = 0.6 * math.sin(t * 23.0) + 0.4 * math.sin(t * 37.0 + 1.3)
        M = M @ Tm(140, 70) @ Rm(0.5 * wob) @ Tm(-140, -70)
    elif pose == "hover":
        M = M @ Tm(0.8 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3 + 1))          # held still; only breath moves it
    elif pose == "erase":
        s = math.sin(t * 2 * math.pi * 5.5)                                     # rubbing: five and a half strokes a second
        M = M @ Tm(7.0 * s, -2.0 * s) @ Tm(140, 70) @ Rm(1.0 * s) @ Tm(-140, -70)
        info["stroke"] = s
    f = 1.0 + 0.03 * wob

    def J(pts):
        return [pts[0]] + [(p[0] * f, p[1] * f) for p in pts[1:]]
    grip = 0.0 if pose != "erase" else 1.0
    idx, mid, thb = J(_W["index"]), J(_W["middle"]), J(_W["thumb"])
    if grip:                                                    # the pencil is turned round: gripped lower, fist tighter
        idx = [idx[0], (55, -70), (41, -51), (33, -35)]
        thb = [thb[0], (64, -9), (43, -24)]
    _wrist(layer, M, _W["wrist"], _W["arm"], tn)
    _finger(layer, M, _W["pinky"], 22, col, 50, nail=False)
    _finger(layer, M, _W["ring"], 25, col, 54, nail=False)
    _finger(layer, M, mid, 24, col, 58, nail=False)
    draw_sprite(layer, _wpalm(tuple(col)), M, (1.2, 1.8, 1.3, 0.38), clip_shadow=True)
    _arm(layer, M, _W["wrist"], _W["arm"], tn)
    draw_sprite(layer, _pencil(), M @ _pencil_M(0, 0, PEN_A, pose == "erase"), (1.5, 2.2, 1.4, 0.4), clip_shadow=True)
    _finger(layer, M, thb, 30, col, 60, nail=False)
    draw_sprite(layer, _nail(26, tuple(col)), M @ Tm(*thb[2]) @ Rm(math.degrees(math.atan2(thb[2][1] - thb[1][1], thb[2][0] - thb[1][0]))), None)
    _finger(layer, M, idx, 25, col, 64, nail=True)
    info["tip"] = apply(M, (0, 0))
    info["wrist"] = apply(M, _W["wrist"])
    a = math.radians(PEN_A)
    info["pencil_end"] = apply(M, (PENCIL_LEN * math.cos(a), PENCIL_LEN * math.sin(a)))
    info["knuckles"] = apply(M, (100, -40))
    return info, lift


def hand(target, x, y, angle=0.0, pose="write", tone="teal", scale=1.0, flip=False, t=0.0, lift=None, arm=None, edge=None, shade=0.0, alpha=1.0):
    """A jointed cut-paper hand with its sleeve and forearm running off the frame. See PEOPLE.md for each pose.

    (x, y) is the point the pose is about (pencil point, rubber, fingertip, palm, the sheet's edge, the top of the
    fist). angle turns the whole arm about (x, y), degrees clockwise; or pass arm= the screen direction the forearm
    should leave by (0 right, 90 down, 180 left). flip=True makes it a left hand. t (seconds) drives the pose's own
    small movement. lift (px) raises the hand off the page (hover defaults to 16). edge (pose "pass" only) = the
    screen direction, in degrees, of the sheet edge being gripped, so the fingers vanish under it exactly. Returns a dict of screen points:
    tip, wrist, knuckles, down (is it touching), and pencil_end for the pencil poses."""
    if pose not in ARM_DIR:
        raise ValueError(f"pose {pose!r}: use one of {POSES}")
    tn = tone_of(tone)
    if arm is not None:
        angle = aim(pose, arm, flip)
    if lift is None:
        lift = 16.0 if pose == "hover" else 0.0
    layer = _clear(target)
    M = Tm(MG + x - lift * 0.25, MG + y - lift * 0.8) @ Rm(angle) @ Sm(-scale if flip else scale, scale)
    if pose in ("write", "hover", "erase"):
        info, lift = _draw_write(layer, M, pose, t, tn, lift)
    else:
        info, lift = _draw_flat(layer, M, pose, t, tn, lift, edge)
    k = scale
    _lay_group(target, layer, ((5 + lift * 0.7) * k, (8 + lift * 1.1) * k, (5 + lift * 0.25) * k, 0.36 * (1 - min(0.4, lift / 90))), alpha, shade)
    info["lift"] = lift
    return _unmg(info)


# ================================================== THE BACK OF A CHILD'S HEAD
HAIRS = ("short", "bun", "braids", "curly")


@lru_cache(None)
def _head_parts(tone_key, hair):
    tn = dict(tone_key)
    hc = tn["hair"]
    P = {}

    def back_deco(d, L, S):
        d.line([L(0, 6), L(0, 300)], fill=dk(tn["sleeve"], 0.86), width=2 * S)             # the seam down the back
        for sx in (-1, 1):
            d.line([L(sx * 96, 26), L(sx * 104, 300)], fill=dk(tn["sleeve"], 0.86), width=2 * S)   # where the sleeves are set in
    P["back"] = cut([(-158, 300), (-156, 84), (-142, 46), (-112, 22), (-66, 6), (-30, -2), (30, -2), (66, 6), (112, 22), (142, 46), (156, 84), (158, 300)],
                    tn["sleeve"], back_deco, seed=101, per=6)

    def col_deco(d, L, S):
        for k in range(-5, 6):
            d.line([L(k * 7, -12), L(k * 7.6, 12)], fill=dk(tn["cuff"], 0.82), width=S)
    P["collar"] = cut([(-42, 2), (-30, -10), (0, -14), (30, -10), (42, 2), (30, 10), (0, 13), (-30, 10)], tn["cuff"], col_deco, seed=102)
    P["neck"] = cut(rrect(-25, -62, 25, 6, 12), tn["hand"], curve=False, seed=103)
    P["ear"] = cut(circ(0, 0, 10, 16, 17), tn["hand"], curve=False, seed=104)
    P["skull"] = cut(circ(0, -104, 62, 36, 72), tn["hand"], curve=False, seed=105)
    P["cheek"] = cut(circ(0, 0, 20, 20, 30), tn["hand"], curve=False, seed=106)

    def hair_deco(d, L, S):
        if hair == "braids":
            d.line([L(0, -176), L(1, -60)], fill=lt(tn["hand"], 1.0), width=int(2.4 * S))  # the parting
            for sx in (-1, 1):
                for k in range(7):
                    d.arc([L(sx * 4 - 70, -176 + k * 14)[0], L(0, -176 + k * 14)[1], L(sx * 4 + 70, 0)[0], L(0, -100 + k * 20)[1]],
                          (180 if sx > 0 else 270), (270 if sx > 0 else 360), fill=dk(hc, 0.72), width=S)
        elif hair == "bun":
            for k in range(-4, 5):                                                         # combed up to the bun
                d.line([L(k * 13, -40 - abs(k) * 3), L(k * 4, -168)], fill=lt(hc, 1.35), width=S)
        elif hair == "short":
            for k in range(9):                                                             # the crown's whorl
                a0 = k * 40
                d.arc([L(-26 - k * 4, -150 - k * 3)[0], L(0, -150 - k * 3)[1], L(34 + k * 4, 0)[0], L(0, -96 + k * 5)[1]], a0, a0 + 70, fill=lt(hc, 1.4), width=S)
    if hair == "short":
        pts = [(-66, -96), (-64, -140), (-40, -172), (0, -181), (40, -172), (64, -140), (66, -96), (60, -62), (48, -50), (36, -58), (22, -44), (8, -54), (-6, -42), (-20, -54), (-34, -46), (-48, -58), (-60, -62)]
        P["hair"] = cut(pts, hc, hair_deco, seed=110, per=5)
        P["tuft"] = cut([(-4, -176), (6, -196), (20, -200), (14, -188), (18, -174)], hc, seed=111)
    elif hair == "bun":
        P["hair"] = cut([(-66, -96), (-64, -140), (-40, -172), (0, -181), (40, -172), (64, -140), (66, -96), (58, -58), (30, -42), (0, -38), (-30, -42), (-58, -58)], hc, hair_deco, seed=112, per=5)

        def bun_deco(d, L, S):
            for k in range(5):
                d.arc([L(-30 + k * 5, -30 + k * 5)[0], L(0, -30 + k * 5)[1], L(30 - k * 5, 0)[0], L(0, 30 - k * 5)[1]], 200 + k * 30, 380 + k * 30, fill=lt(hc, 1.4), width=S)
        P["bun"] = cut(circ(0, 0, 31, 26, 28), hc, bun_deco, curve=False, seed=113)
        P["band"] = cut(rrect(-22, -6, 22, 6, 5), tn["cuff"], curve=False, seed=114)
    elif hair == "braids":
        P["hair"] = cut([(-67, -96), (-65, -140), (-40, -173), (0, -182), (40, -173), (65, -140), (67, -96), (62, -56), (34, -40), (0, -36), (-34, -40), (-62, -56)], hc, hair_deco, seed=115, per=5)
        P["plait"] = cut([(0, -13), (13, -3), (10, 9), (0, 14), (-10, 9), (-13, -3)], hc, seed=116)
        P["bead"] = cut(circ(0, 0, 8, 14), tn["cuff"], curve=False, seed=117)
        P["tail"] = cut([(-7, 0), (7, 0), (10, 16), (3, 26), (-6, 22), (-10, 12)], hc, seed=118)
    else:
        P["hair"] = cut(circ(0, -108, 66, 36, 74), hc, curve=False, seed=119)
        rs = random.Random(5)
        curls = []
        for k in range(46):
            a = rs.uniform(0, 6.283)
            r = rs.choice((1.0, 1.0, 0.72, 0.42, 0.15))
            curls.append((r * 70 * math.cos(a) * rs.uniform(0.92, 1.08), -110 + r * 78 * math.sin(a) * rs.uniform(0.92, 1.08), rs.uniform(13, 21), rs.random()))
        curls.sort(key=lambda c: -c[1] + 40 * c[3])
        P["curls"] = [(x, y, cut(circ(0, 0, r, 14), mixc(hc, lt(hc, 1.5), 0.5 * q), curve=False, seed=120 + i,)) for i, (x, y, r, q) in enumerate(curls)]
    return P


def head_back(target, x, y, tone="teal", scale=1.0, tilt=0.0, hair="short", turn=0.0, t=0.0, shade=0.0, alpha=1.0):
    """The back of a child's head and shoulders, for over-the-shoulder shots: jumper, collar, neck, ears and hair,
    cut from the child's tone. (x, y) is the nape of the neck, where the collar sits; at scale 1 the shoulders are
    316 wide and run 300 below it (let the frame crop them) and the crown is 182 above it.
    tilt (degrees, + clockwise) tips the head on the neck: a look up at the board is a small tilt with turn 0, a look
    at a neighbour is tilt 10..18 with turn 0.6..1 the same way. turn -1..1 swings the head left / right: the far ear
    goes behind the hair and a sliver of cheek (no features, ever) shows on the side it turns to.
    hair: short, bun, braids, curly. t gives breath and sways the braids.
    Returns {"crown", "head", "nape", "ear_l", "ear_r", "shoulder_l", "shoulder_r"} in screen points."""
    tn = tone_of(tone)
    key = tuple(sorted((k, tuple(v)) for k, v in tn.items()))
    P = _head_parts(key, hair)
    layer = _clear(target)
    br = 1.2 * math.sin(t * 1.5)
    M0 = Tm(MG + x, MG + y) @ Sm(scale)
    sh = (1.6, 2.4, 2.0, 0.36)
    draw_sprite(layer, P["back"], M0 @ Tm(0, br * 0.6), None)
    Mh = M0 @ Tm(0, -20 + br) @ Rm(tilt) @ Tm(turn * 7, 20)
    draw_sprite(layer, P["neck"], M0 @ Tm(0, br * 0.8) @ Tm(0, -20) @ Rm(tilt * 0.5) @ Tm(0, 20), sh, clip_shadow=True)
    draw_sprite(layer, P["collar"], M0 @ Tm(0, br * 0.6), sh, clip_shadow=True)
    for sx in (-1, 1):
        vis = 1.0 - max(0.0, -sx * turn)                        # turning right hides the left ear behind the hair
        if vis > 0.15:
            draw_sprite(layer, P["ear"], Mh @ Tm(sx * (61 - 10 * abs(turn)) - turn * 6, -92) @ Sm(0.5 + 0.5 * vis, 1.0), None)
    draw_sprite(layer, P["skull"], Mh, sh, clip_shadow=True)
    if abs(turn) > 0.25:
        sx = 1 if turn > 0 else -1
        draw_sprite(layer, P["cheek"], Mh @ Tm(sx * (44 + 12 * abs(turn)), -78), None)
    Mhair = Mh @ Tm(-turn * 9, 0)
    if hair == "braids":
        for sx in (-1, 1):
            sway = 5.0 * math.sin(t * 1.9 + sx) + tilt * 0.5
            px, py = sx * 46, -58
            a = 0.0
            for k in range(8):
                a += sway * 0.22
                Mp = Mhair @ Tm(px, py) @ Rm(a + (9 if k % 2 else -9) * sx)
                draw_sprite(layer, P["plait"], Mp @ Sm(1.0 - 0.035 * k), (1.0, 1.6, 1.2, 0.4), clip_shadow=True)
                px, py = px - 15 * math.sin(math.radians(a)), py + 15 * math.cos(math.radians(a))
            draw_sprite(layer, P["tail"], Mhair @ Tm(px, py + 4) @ Rm(a), (1.0, 1.6, 1.2, 0.4), clip_shadow=True)
            draw_sprite(layer, P["bead"], Mhair @ Tm(px, py) @ Rm(a), (1.0, 1.6, 1.2, 0.4), clip_shadow=True)
    if hair == "curly":
        draw_sprite(layer, P["hair"], Mhair, sh, clip_shadow=True)
        for cx, cy, spr in P["curls"]:
            draw_sprite(layer, spr, Mhair @ Tm(cx, cy), (0.8, 1.4, 1.0, 0.42), clip_shadow=True)
    else:
        draw_sprite(layer, P["hair"], Mhair, sh, clip_shadow=True)
    if hair == "short":
        draw_sprite(layer, P["tuft"], Mhair @ Tm(6, -178) @ Rm(4 * math.sin(t * 2.3)) @ Tm(-6, 178), sh, clip_shadow=True)
    if hair == "bun":
        draw_sprite(layer, P["bun"], Mhair @ Tm(0, -186), sh, clip_shadow=True)
        draw_sprite(layer, P["band"], Mhair @ Tm(0, -162), (1.0, 1.4, 1.0, 0.4), clip_shadow=True)
    k = scale
    _lay_group(target, layer, (8 * k, 12 * k, 9 * k, 0.34), alpha, shade)
    out = dict(crown=apply(Mh, (0, -180)), head=apply(Mh, (0, -104)), nape=apply(M0, (0, 0)), ear_l=apply(Mh, (-61, -92)), ear_r=apply(Mh, (61, -92)),
               shoulder_l=apply(M0, (-128, 40)), shoulder_r=apply(M0, (128, 40)))
    return _unmg(out)


# ============================================================== THE DESK TOP
def _sink(a, mask, depth=0.34):
    """Press a recess (mask 0..1, soft) into a lit surface: darker floor, shadowed upper wall, lit lower wall."""
    d = np.asarray(mask, np.float32) / 255
    a *= (1 - depth * d)[..., None]
    e = d - np.roll(np.roll(d, 3, axis=0), 2, axis=1)
    a -= (95 * np.clip(e, 0, 1))[..., None]
    a += (70 * np.clip(-e, 0, 1))[..., None]


@lru_cache(None)
def _desk(w, h):
    k = w / 960.0
    grain = vnoise((h, w), 520 * k, 4 * k, 1, 3)
    cloud = vnoise((h, w), 260 * k, 60 * k, 2, 2)
    fine = vnoise((h, w), 1.6, None, 3)
    a = np.array(DESK, np.float32)[None, None, :] * (1 + 0.085 * grain + 0.05 * cloud + 0.02 * fine)[..., None]
    a[..., 0] *= (1 + 0.03 * cloud)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))                 # scuffs: nine years of other children
    d = ImageDraw.Draw(ov)
    rs = random.Random(12)
    for _ in range(170):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        L, an = rs.uniform(6, 60) * k, rs.gauss(0, 0.5) + (math.pi / 2 if rs.random() < 0.15 else 0)
        c = (236, 214, 180, rs.randint(26, 80)) if rs.random() < 0.75 else (60, 40, 26, rs.randint(30, 90))
        d.line([(x, y), (x + L * math.cos(an), y + L * math.sin(an))], fill=c, width=1)
    for _ in range(5):                                           # a compass point went round here
        x, y, r = rs.uniform(0.1, 0.9) * w, rs.uniform(0.2, 0.9) * h, rs.uniform(18, 60) * k
        a0 = rs.uniform(0, 360)
        d.arc([x - r, y - r, x + r, y + r], a0, a0 + rs.uniform(60, 200), fill=(232, 208, 172, 70), width=1)
    for _ in range(40):                                          # dings
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        r = rs.uniform(0.8, 2.4) * k
        d.ellipse([x - r, y - r, x + r, y + r], fill=(52, 36, 24, rs.randint(40, 110)))
    x0, y0 = int(0.035 * w), int(0.80 * h)                       # what a name sticker leaves when it is picked off
    pts = [(x0, y0), (x0 + 150 * k, y0 - 4 * k), (x0 + 156 * k, y0 + 18 * k), (x0 + 120 * k, y0 + 44 * k), (x0 + 60 * k, y0 + 40 * k), (x0 + 4 * k, y0 + 46 * k)]
    d.polygon(pts, fill=(226, 212, 186, 54))
    gx = [(x0 + rs.uniform(0, 150) * k, y0 + rs.uniform(0, 40) * k) for _ in range(30)]
    for (px, py) in gx:
        d.ellipse([px - 3 * k, py - 2 * k, px + 3 * k, py + 2 * k], fill=(240, 232, 214, 70))
    ov = ov.filter(ImageFilter.GaussianBlur(0.5))
    oa = np.asarray(ov, np.float32)
    al = oa[..., 3:4] / 255
    a = a * (1 - al) + oa[..., :3] * al
    groove = (int(70 * k), int(22 * k), int(600 * k), int(46 * k))
    tray = (int(650 * k), int(12 * k), int(924 * k), int(66 * k))
    for box, r, depth in ((groove, 12 * k, 0.30), (tray, 14 * k, 0.40)):
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255)
        _sink(a, m.filter(ImageFilter.GaussianBlur(1.6 * k)), depth)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a *= (1.10 - 0.34 * np.clip(np.hypot((xx - 0.42 * w) / (0.80 * w), (yy - 0.36 * h) / (0.95 * h)), 0, 1.4) ** 1.6)[..., None]
    im = to_img(a).convert("RGB")
    # in the tray: a pencil stub and a block rubber, left there
    stub = compose([cut(rrect(60, -7.5, 78, 7.5, 5), (226, 132, 138), curve=False, seed=131), cut([(26, -7.5), (60, -7.5), (60, 7.5), (26, 7.5)], (84, 132, 110), curve=False, seed=132),
                    cut([(0, 0), (26, -7.5), (26, 7.5)], (226, 192, 142), lambda dd, L, S: dd.polygon([L(0, 0), L(9, -2), L(9, 2)], fill=(52, 50, 56)), curve=False, seed=133)])
    draw_sprite(im, stub, Tm(tray[0] + 150 * k, tray[1] + 36 * k) @ Rm(-4) @ Sm(k), (2, 3, 1.6, 0.45))
    rub = cut(rrect(-22, -13, 22, 13, 4), (232, 226, 214), lambda dd, L, S: dd.polygon([L(-22, -13), L(-4, -13), L(-10, 13), L(-22, 13)], fill=(92, 132, 168)), curve=False, seed=134)
    draw_sprite(im, rub, Tm(tray[0] + 60 * k, tray[1] + 28 * k) @ Rm(9) @ Sm(k), (2, 3, 1.6, 0.45))
    return im, groove, tray


def desk(target, t=0.0):
    """A school desk top filling the target (any size; laid out for 960 x 540 and scaled with the width): wood-grain
    laminate under one lamp, scuffed, with the pencil groove along the top (x 70..600, y 22..46) and the moulded
    pencil tray top right (x 650..924, y 12..66) holding a pencil stub and a block rubber. Paints over everything.
    t is accepted for symmetry; the desk does not move. Returns {"groove": box, "tray": box}."""
    img = _img(target)
    im, groove, tray = _desk(*img.size)
    if img.mode == "RGBA":
        img.alpha_composite(im.convert("RGBA"))
    else:
        img.paste(im, (0, 0))
    _sync(target)
    return {"groove": groove, "tray": tray}


@lru_cache(None)
def _desk_far():
    def deco(d, L, S):
        d.rounded_rectangle([L(-104, -70)[0], L(-104, -70)[1], L(30, -60)[0], L(30, -60)[1]], 5 * S, fill=dk(DESK, 0.62))            # groove
        d.rounded_rectangle([L(44, -72)[0], L(44, -72)[1], L(106, -56)[0], L(106, -56)[1]], 5 * S, fill=dk(DESK, 0.66))              # tray
        rs = random.Random(3)
        for _ in range(40):
            x, y = rs.uniform(-110, 110), rs.uniform(-50, 70)
            d.line([L(x, y), L(x + rs.uniform(8, 50), y + rs.uniform(-2, 2))], fill=lt(DESK, 1.1) if rs.random() < 0.6 else dk(DESK, 0.9), width=S)
    top = cut(rrect(-120, -80, 120, 80, 12), DESK, deco, curve=False, seed=141, grain=0.1)
    edge = cut(rrect(-120, -74, 120, 88, 12), dk(DESK, 0.55), curve=False, seed=142)
    return compose([edge, top], None)


def desk_far(target, box, angle=0.0):
    """A small desk seen from above, for the far shot: box = (x0, y0, x1, y1) is its top (design 240 x 160, groove and
    tray along the far edge, a dark front edge below). It casts a shadow on the floor. Returns its centre."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = (x1 - x0) / 240.0, (y1 - y0) / 160.0
    draw_sprite(target, _desk_far(), Tm(cx, cy) @ Rm(angle) @ Sm(sx, sy), (5, 9, 6, 0.42))
    _sync(target)
    return (cx, cy)


@lru_cache(None)
def _cup():
    def deco(d, L, S):
        d.ellipse([L(-27, -27)[0], L(-27, -27)[1], L(27, 27)[0], L(27, 27)[1]], fill=(96, 40, 34))            # the inside, in shadow
        d.ellipse([L(-21, -17)[0], L(-21, -17)[1], L(23, 27)[0], L(23, 27)[1]], fill=(128, 54, 44))           # its floor
    cup = cut(circ(0, 0, 34, 30), (196, 78, 58), deco, curve=False, seed=151)

    def die_deco(d, L, S):
        for px, py in ((-6, -6), (0, 0), (6, 6)):
            d.ellipse([L(px - 2.4, py - 2.4)[0], L(px - 2.4, py - 2.4)[1], L(px + 2.4, py + 2.4)[0], L(px + 2.4, py + 2.4)[1]], fill=PRINT)
    die = cut(rrect(-12, -12, 12, 12, 4), (246, 242, 230), die_deco, curve=False, seed=152)
    return cup, die


def cup(target, x, y, scale=1.0, die=True, t=0.0):
    """A paper cup seen from above with the die lying in the bottom of it, not yet thrown. (x, y) = the centre of
    the rim (radius 34 * scale). die=False: an empty cup. Returns (x, y)."""
    c, dsp = _cup()
    M = Tm(x, y) @ Sm(scale)
    draw_sprite(target, c, M, (4, 6, 4, 0.4))
    if die:
        draw_sprite(target, dsp, M @ Tm(2, 5) @ Rm(24), (1.5, 2, 1.5, 0.5))
    _sync(target)
    return (x, y)


# ============================================================ THE WHOLE ROOM
ROOM_ROWS, ROOM_COLS = 4, 5
HERO = (2, 2)           # (row, col) of the desk the film has been at: the one with the cup


@lru_cache(None)
def _floor(w, h):
    k = w / 960.0
    a = np.array(FLOOR, np.float32)[None, None, :] * (1 + 0.05 * vnoise((h, w), 3, None, 61, 2) + 0.05 * vnoise((h, w), 220 * k, None, 62, 2))[..., None]
    rs = np.random.RandomState(6)
    for _ in range(int(2600 * k * k)):                           # terrazzo chips
        x, y = rs.randint(0, w - 2), rs.randint(0, h - 2)
        a[y:y + rs.randint(1, 3), x:x + rs.randint(1, 3)] += rs.uniform(-40, 46)
    step = 96 * k
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    line = np.minimum((xx + 30 * k) % step, (yy + 20 * k) % step)
    a *= (1 - 0.16 * np.clip(1.6 - line, 0, 1))[..., None]
    sun = np.zeros((h, w), np.float32)                           # three windows' worth of afternoon on the floor
    lay = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(lay)
    for i in range(3):
        x0 = (120 + i * 300) * k
        d.polygon([(x0, -20 * k), (x0 + 150 * k, -20 * k), (x0 + 330 * k, 250 * k), (x0 + 150 * k, 250 * k)], fill=255)
    sun = np.asarray(lay.filter(ImageFilter.GaussianBlur(14 * k)), np.float32) / 255
    a *= (1 + 0.20 * sun)[..., None]
    a[..., 2] *= (1 - 0.06 * sun)
    a *= (1.04 - 0.22 * np.clip(np.hypot((xx - 0.45 * w) / w, (yy - 0.3 * h) / h), 0, 1.2) ** 1.5)[..., None]
    return to_img(a).convert("RGB")


@lru_cache(None)
def _mini_sheet(w=60, h=78):
    def deco(d, L, S):
        d.text(L(-w / 2 + 5, -h / 2 + 3), "Porthole Log", font=_inter(900, 5 * S), fill=PRINT)
        cx, cy = 0, -9
        for r, wd in ((19, 1.0), (15, 1.0)):
            d.ellipse([L(cx - r, cy - r)[0], L(cx - r, cy - r)[1], L(cx + r, cy + r)[0], L(cx + r, cy + r)[1]], outline=PRINT, width=int(wd * S))
        for kk in range(6):
            a = math.radians(-90 + 60 * kk)
            bx, by = cx + 17 * math.cos(a), cy + 17 * math.sin(a)
            d.rectangle([L(bx - 2.2, by - 2.2)[0], L(bx - 2.2, by - 2.2)[1], L(bx + 2.2, by + 2.2)[0], L(bx + 2.2, by + 2.2)[1]], fill=PAPER, outline=PRINT, width=max(1, S // 2))
        for yy in (17, 22, 27, 32):
            d.line([L(-w / 2 + 5, yy), L(w / 2 - 5, yy)], fill=(140, 151, 157), width=max(1, S // 2))
    return cut(rrect(-w / 2, -h / 2, w / 2, h / 2, 1), PAPER, deco, curve=False, seed=161, grain=0.03, edge=0.5)


@lru_cache(None)
def _kid_top(tone, hair):
    tn = TONES[tone]
    hc = tn["hair"]
    body = cut(circ(0, 0, 33, 26, 15), tn["sleeve"], curve=False, seed=171)
    head = [cut(circ(0, 0, 16, 22, 17), hc, curve=False, seed=172)]
    ears = [cut(circ(-16, 1, 4, 10), tn["hand"], curve=False, seed=173), cut(circ(16, 1, 4, 10), tn["hand"], curve=False, seed=174)]
    if hair == "bun":
        head.append(cut(circ(0, 6, 8, 14), lt(hc, 1.25), curve=False, seed=175))
        head.append(cut(rrect(-5, 0, 5, 3, 1), tn["cuff"], curve=False, seed=176))
    elif hair == "braids":
        for sx in (-1, 1):
            for k in range(4):
                head.insert(0, cut(circ(sx * (12 + k), 12 + k * 6, 4.2 - 0.4 * k, 10), hc, curve=False, seed=177 + k))
            head.insert(0, cut(circ(sx * 16, 38, 3, 8), tn["cuff"], curve=False, seed=181))
    elif hair == "curly":
        rs = random.Random(9)
        for k in range(14):
            a = k / 14 * 6.283
            head.append(cut(circ(17 * math.cos(a), 18 * math.sin(a), rs.uniform(4.5, 6.5), 10), mixc(hc, lt(hc, 1.5), rs.random() * 0.5), curve=False, seed=182 + k))
    else:
        head.append(cut([(-2, -8), (6, -10), (4, -2)], lt(hc, 1.5), seed=196))
    return body, compose(ears + head, (0.8, 1.2, 0.8, 0.4)), cut(circ(0, 0, 6.5, 12), tn["hand"], curve=False, seed=197)


def room_layout(size=(W, H)):
    """Where classroom() puts things, without drawing: {"desks": [(cx, cy, w, h, angle, row, col), ...], "hero": index,
    "cup": (x, y), "sheet": (x, y, angle) of the hero desk's sheet} for a target of `size`."""
    k = size[0] / 960.0
    rs = random.Random(44)
    desks = []
    for r in range(ROOM_ROWS):
        for c in range(ROOM_COLS):
            cx = (130 + 175 * c + rs.uniform(-9, 9)) * k
            cy = (70 + 128 * r + rs.uniform(-6, 6)) * k
            desks.append((cx, cy, 124 * k, 80 * k, rs.uniform(-3.5, 3.5), r, c))
    hero = HERO[0] * ROOM_COLS + HERO[1]
    hx, hy = desks[hero][0], desks[hero][1]
    return {"desks": desks, "hero": hero, "cup": (hx + 44 * k, hy - 12 * k), "sheet": (hx - 8 * k, hy + 4 * k, -4.0), "k": k}


_room_cache = {}


def classroom(target, t=0.0, sheets=None, cup_at="hero", children=True):
    """The whole room from above, filling the target (any size, laid out for 960 x 540): a terrazzo floor with window
    light, 4 rows of 5 desks, on each desk a small Porthole Log with its ring, a cut-paper child at each (jumper,
    back of the head, two sleeves and hands on the desk; four tones, four kinds of hair), and on the HERO desk
    (row 2, col 2, near the centre) a cup with the die still in it.
    sheets: None = every desk has the small printed sheet; or {desk index or (row, col): PIL image} to lay your own
    page (a sheet() you have written on) on those desks, scaled down. cup_at: "hero", a desk index, or None.
    t: heads nod and turn a little, a few hands write. Returns room_layout(size)."""
    img = _img(target)
    w, h = img.size
    lay_ = room_layout((w, h))
    k = lay_["k"]
    skey = None if not sheets else tuple(sorted((kk if isinstance(kk, int) else kk[0] * ROOM_COLS + kk[1], id(v)) for kk, v in sheets.items()))
    key = (w, h, skey, cup_at)
    if key not in _room_cache:
        base = _floor(w, h).copy()
        own = {} if not sheets else {(kk if isinstance(kk, int) else kk[0] * ROOM_COLS + kk[1]): v for kk, v in sheets.items()}
        rs = random.Random(45)
        for i, (cx, cy, dw, dh, an, r, c) in enumerate(lay_["desks"]):
            desk_far(base, (cx - dw / 2, cy - dh / 2, cx + dw / 2, cy + dh / 2), an)
            sa = rs.uniform(-11, 11)
            sx, sy = cx + rs.uniform(-14, 6) * k, cy + rs.uniform(2, 8) * k
            if i == lay_["hero"]:
                sx, sy, sa = lay_["sheet"]
            if i in own:
                im = own[i].convert("RGBA").resize((max(2, int(36 * k)), max(2, int(46 * k))), Image.LANCZOS)
                spr = Sprite(im, -im.size[0] // 2, -im.size[1] // 2)
                draw_sprite(base, spr, Tm(sx, sy) @ Rm(an + sa), (1.2, 1.8, 1.2, 0.4))
            else:
                draw_sprite(base, _mini_sheet(), Tm(sx, sy) @ Rm(an + sa) @ Sm(0.6 * k), (1.2, 1.8, 1.2, 0.4))
            ci = lay_["hero"] if cup_at == "hero" else cup_at
            if ci is not None and i == ci:
                cup(base, cx + 44 * k, cy - 12 * k, 0.30 * k)
        _room_cache.clear()
        _room_cache[key] = base
    base = _room_cache[key]
    if img.mode == "RGBA":
        img.alpha_composite(base.convert("RGBA"))
    else:
        img.paste(base, (0, 0))
    if children:
        rs = random.Random(46)
        for i, (cx, cy, dw, dh, an, r, c) in enumerate(lay_["desks"]):
            tone = TONE_NAMES[(r * 3 + c * 5 + (r * c) % 3) % 4]
            hair = HAIRS[(r + c * 3 + (i * 7) % 5) % 4]
            body, head, hnd = _kid_top(tone, hair)
            ph = rs.uniform(0, 6.283)
            writes = rs.random() < 0.45
            looks = rs.random() < 0.25
            nod = math.sin(t * 0.8 + ph)
            bx, by = cx + rs.uniform(-6, 6) * k, cy + dh / 2 + 16 * k
            layer = _clear(target)
            Mk = Tm(MG + bx, MG + by) @ Sm(k)
            col = tuple(TONES[tone]["sleeve"])
            hx1 = 16 + (3.0 * math.sin(t * 9 + ph) + 5 * math.sin(t * 0.9 + ph) if writes else 0)
            hy1 = -40 + (1.2 * math.sin(t * 14 + ph) if writes else 0)
            for (sx0, tx, ty) in ((-26, -18, -34), (26, hx1, hy1)):
                _seg(layer, Mk, (sx0, -2), (tx, ty), 12, 10, col, 198, None)
                draw_sprite(layer, hnd, Mk @ Tm(tx, ty - 3), None)
            draw_sprite(layer, body, Mk, (1, 1.5, 1.2, 0.4), clip_shadow=True)
            turn = (9 * math.sin(t * 0.5 + ph)) if looks else 0.0
            draw_sprite(layer, head, Mk @ Tm(turn * 0.25, -10 + 1.5 * nod) @ Rm(turn * 2 + 3 * math.sin(ph)), (1, 1.6, 1.4, 0.45), clip_shadow=True)
            _lay_group(target, layer, (3 * k, 5 * k, 3.5 * k, 0.4))
    _sync(target)
    return lay_


# ======================================================= THE PORTHOLE LOG PAGE
_INTER = {400: "Inter-Regular.otf", 600: "Inter-SemiBold.otf", 700: "Inter-Bold.otf", 900: "Inter-Black.otf"}
_INTER_DIR = Path("/usr/share/fonts/opentype/inter")
_fc = {}


def _inter(weight, px):
    """The sheet is set in Inter (as ../sheets/master.html); if Inter is not installed, the kit's sans stands in."""
    key = (weight, int(round(px)))
    if key not in _fc:
        p = _INTER_DIR / _INTER[weight]
        try:
            _fc[key] = ImageFont.truetype(str(p), key[1])
        except OSError:
            _fc[key] = font("sans", key[1])
    return _fc[key]


PT_W, PT_H = 612.0, 792.0           # the master is US Letter; every box below is in its points
SHEET_SIZE = (760, 980)
MASTER = dict(number=31, station="Galley B", clue="Dented bread-roll tin stamped WARM TO 375°F", rule="Thermal Inversion (SCION 51)",
              turkey=("Thanksgiving roasting pan", "Spare hull"), trout=("Heated minnow spa", "Floating toaster"))
BTN = {"triangle": (18, 144, 95), "circle": (214, 58, 58), "cross": (47, 111, 214), "square": (201, 70, 156)}
RING_C, RING_OUT, RING_IN, RING_MID = (306.0, 323.4), 116.3, 94.1, 105.2
_DIE_PIPS = {1: [(12, 12)], 2: [(7, 7), (17, 17)], 3: [(7, 7), (12, 12), (17, 17)], 4: [(7, 7), (17, 7), (7, 17), (17, 17)],
             5: [(7, 7), (17, 7), (12, 12), (7, 17), (17, 17)], 6: [(7, 6), (17, 6), (7, 12), (17, 12), (7, 18), (17, 18)]}


def _cap1(s):
    s = s.strip().rstrip("?").strip()
    return s[:1].upper() + s[1:]


@lru_cache(None)
def porthole_info(porthole=None):
    """What is printed on porthole NN's own sheet, from ../seeds.json: number, station, clue, rule and the two
    options each friend is offered. None = the master's own example (porthole 31)."""
    if porthole is None:
        return dict(MASTER)
    try:
        row = json.loads((ROOT / "seeds.json").read_text())[int(porthole) - 1]
    except (OSError, IndexError, ValueError):
        return dict(MASTER, number=porthole)
    station = row[0].split("·")[-1].strip()
    tk = [_cap1(x) for x in row[3].split(" or ")]
    tr = [_cap1(x) for x in row[4].split(" or ")]
    return dict(number=int(porthole), station=station, clue=row[1], rule=row[5].split(":")[0].strip(), turkey=tuple(tk[:2]), trout=tuple(tr[:2]))


@lru_cache(None)
def _steps():
    try:
        return {(s["page"], s["step"]): tuple(s["box"]) for s in json.loads((ROOT / "sheets" / "steps.json").read_text())}
    except OSError:
        return {}


def _boxes(page):
    """Every named box of a page, in points."""
    B = {name: box for (pg, name), box in _steps().items() if pg == page}
    if page == 1:
        B.setdefault("a1", (46.7, 517.9, 565.3, 557.6)); B.setdefault("a2", (46.7, 581.9, 565.3, 621.6)); B.setdefault("a3", (46.7, 645.9, 565.3, 685.6))
        B.setdefault("name", (46.7, 111, 237.1, 128.6)); B.setdefault("ring", (46.7, 200.1, 565.3, 446.7))
        B["name.line"] = (74.0, 106.0, 237.0, 127.5)
        for q in ("a1", "a2", "a3"):
            x0, y0, x1, y1 = B[q]
            mid = y0 + 19.84
            B[q + ".1"], B[q + ".2"] = (x0, y0, x1, mid), (x0, mid, x1, y1)
        cx, cy = RING_C
        B["ring.in"] = (cx - RING_IN, cy - RING_IN, cx + RING_IN, cy + RING_IN)
        B["ring.out"] = (cx - RING_OUT, cy - RING_OUT, cx + RING_OUT, cy + RING_OUT)
        for k in range(1, 7):
            a = math.radians(-90 + 60 * (k - 1))
            bx, by = cx + RING_MID * math.cos(a), cy + RING_MID * math.sin(a)
            B[f"die{k}"] = (bx - 10.7, by - 10.7, bx + 10.7, by + 10.7)
        B["margin.right"] = (430.0, 215.0, 570.0, 440.0)         # the white space beside the ring (second drawings land here)
        B["margin.left"] = (42.0, 215.0, 182.0, 440.0)
    else:
        for j, dx in ((1, 0.0), (2, 274.8)):
            B.setdefault(f"name{j}", (46.7 + dx, 191.1, 290.5 + dx, 208.7))
            B[f"name{j}.line"] = (80.0 + dx, 186.0, 290.5 + dx, 208.0)
            B[f"plate{j}a"] = (53.1 + dx, 234.1, 284.1 + dx, 255.7)
            B[f"plate{j}b"] = (53.1 + dx, 260.3, 284.1 + dx, 281.9)
            B[f"btn{j}a"] = (56.9 + dx, 236.4, 73.9 + dx, 253.4)
            B[f"btn{j}b"] = (56.9 + dx, 262.6, 73.9 + dx, 279.6)
            B[f"draw{j}.circle"] = (252.6 + dx, 285.8, 283.8 + dx, 317.0)
            for i in range(3):
                n = i + 1 + (0 if j == 1 else 3)
                y0 = 327.9 + 52.4 * i
                B.setdefault(f"bolt{n}", (46.7 + dx, y0, 290.5 + dx, y0 + 48.2))
                B[f"bolt{n}.die"] = (46.7 + dx, y0, 63.7 + dx, y0 + 17.0)
                B[f"bolt{n}.1"] = (46.7 + dx, y0 + 17.0, 290.5 + dx, y0 + 32.6)
                B[f"bolt{n}.2"] = (46.7 + dx, y0 + 32.6, 290.5 + dx, y0 + 48.2)
        B["rolled.line"] = (213.0, 556.0, 258.6, 576.0)
        for k in range(6):
            cx = 343.4 + 24.56 * k
            B[f"roll.die{k + 1}"] = (cx - 10.5, 557.7, cx + 10.5, 578.7)
        for q, y0 in (("ga", 648.4), ("ma", 707.9)):
            B.setdefault(q, (46.7, y0, 565.3, y0 + 35.2))
            B[q + ".1"], B[q + ".2"] = (46.7, y0, 565.3, y0 + 17.6), (46.7, y0 + 17.6, 565.3, y0 + 35.2)
    return B


def where(page, name, size=SHEET_SIZE):
    """The box (x0, y0, x1, y1), in pixels of a sheet(size, page) image, of a named part of the page. For a writing
    line the box is the space to write in and its bottom edge (y1) is the printed rule. Names: PEOPLE.md lists them;
    where(page, None) returns the whole dict."""
    kx, ky = size[0] / PT_W, size[1] / PT_H
    B = _boxes(page)
    if name is None:
        return {n: (b[0] * kx, b[1] * ky, b[2] * kx, b[3] * ky) for n, b in B.items()}
    if name not in B:
        raise KeyError(f"page {page} has no {name!r}; it has: {', '.join(sorted(B))}")
    b = B[name]
    return (b[0] * kx, b[1] * ky, b[2] * kx, b[3] * ky)


class _Press:
    """Prints on a page laid out in points."""

    def __init__(self, size, S=2):
        self.S = S
        self.w, self.h = size
        self.kx, self.ky = size[0] * S / PT_W, size[1] * S / PT_H
        self.img = Image.new("RGB", (size[0] * S, size[1] * S), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def X(self, x):
        return x * self.kx

    def Y(self, y):
        return y * self.ky

    def text(self, x, y, s, weight=700, pt=9.4, color=PRINT, anchor="lm", track=0.0):
        f = _inter(weight, pt * self.kx)
        if track:
            cx = self.X(x)
            for ch in s:
                self.d.text((cx, self.Y(y)), ch, font=f, fill=color, anchor=anchor)
                cx += f.getlength(ch) + track * self.kx
            return (cx / self.kx)
        self.d.text((self.X(x), self.Y(y)), s, font=f, fill=color, anchor=anchor)
        return x + f.getlength(s) / self.kx

    def rule(self, x0, x1, y, color=PRINT, pt=1.05):
        self.d.line([(self.X(x0), self.Y(y)), (self.X(x1), self.Y(y))], fill=color, width=max(1, int(round(pt * self.kx))))

    def die(self, cx, cy, n, size=17.0):
        u = size / 24.0
        x0, y0 = cx - size / 2, cy - size / 2
        self.d.rounded_rectangle([self.X(x0 + 1.5 * u), self.Y(y0 + 1.5 * u), self.X(x0 + 22.5 * u), self.Y(y0 + 22.5 * u)], 4.4 * u * self.kx,
                                 fill=(255, 255, 255), outline=PRINT, width=max(2, int(round(1.3 * u * self.kx))))
        r = 2.05 * u
        for px, py in _DIE_PIPS[n]:
            self.d.ellipse([self.X(x0 + px * u - r), self.Y(y0 + py * u - r), self.X(x0 + px * u + r), self.Y(y0 + py * u + r)], fill=PRINT)

    def button(self, cx, cy, kind, size=17.0):
        u = size / 24.0
        col = BTN[kind]
        wd = max(2, int(round(2.5 * u * self.kx)))
        self.d.ellipse([self.X(cx - 10.6 * u), self.Y(cy - 10.6 * u), self.X(cx + 10.6 * u), self.Y(cy + 10.6 * u)], fill=(255, 255, 255), outline=col, width=max(1, int(round(1.3 * u * self.kx))))

        def P(x, y):
            return (self.X(cx + (x - 12) * u), self.Y(cy + (y - 12) * u))
        if kind == "triangle":
            self.d.line([P(12, 6), P(17.8, 16.2), P(6.2, 16.2), P(12, 6), P(17.8, 16.2)], fill=col, width=wd, joint="curve")
        elif kind == "circle":
            self.d.ellipse([P(6.6, 6.6)[0], P(6.6, 6.6)[1], P(17.4, 17.4)[0], P(17.4, 17.4)[1]], outline=col, width=wd)
        elif kind == "cross":
            self.d.line([P(7.4, 7.4), P(16.6, 16.6)], fill=col, width=wd)
            self.d.line([P(16.6, 7.4), P(7.4, 16.6)], fill=col, width=wd)
        else:
            self.d.rounded_rectangle([P(7.2, 7.2)[0], P(7.2, 7.2)[1], P(16.8, 16.8)[0], P(16.8, 16.8)[1]], 1.2 * u * self.kx, outline=col, width=wd)

    def zone(self, x, y, n, title, who, x0=36.8, x1=575.2, rule_y=None):
        if rule_y is not None:
            self.rule(x0, x1, rule_y, PRINT, 1.05)
        self.text(x, y, str(n), 900, 16.5, (201, 92, 62), "mm")
        tx = self.text(x + 18.5, y, title, 900, 12.75, PRINT, "lm")
        self.text(tx + 13.5, y + 0.3, who, 700, 7.9, (95, 108, 112), "lm")

    def done(self):
        im = self.img.resize((self.w, self.h), Image.LANCZOS)
        a = np.asarray(im, np.float32)
        a *= (1 + 0.012 * vnoise((self.h, self.w), 2.0, None, 801, 2) + 0.014 * vnoise((self.h, self.w), 200, None, 802, 2))[..., None]
        return to_img(a).convert("RGB")


GREY_RULE = (140, 151, 157)
SOFT = (68, 82, 90)


@lru_cache(None)
def _sheet(size, page, porthole):
    info = porthole_info(porthole)
    p = _Press(size)
    B = _boxes(page)
    num = str(info["number"])
    p.text(36.8, 29.0, "PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE", 900, 6.4, (138, 90, 18), "lm", track=0.5)
    p.text(36.8, 47.3, "Porthole Log" if page == 1 else "Six bolts, six endings", 900, 18.75, PRINT, "lm")
    p.text(544.0, 46.0, num, 900, 30.0, PRINT, "mm")
    if page == 1:
        p.zone(58.0, 94.2, 1, "Your slip", "Pilot", rule_y=75.2)
        p.text(46.7, 121.8, "Pilot", 700, 9.4)
        p.rule(72.9, 237.0, 127.6, GREY_RULE, 1.0)
        p.text(254.1, 121.8, "Porthole #", 700, 9.4)
        p.text(313.0, 119.8, num, 900, 11.25)
        p.rule(307.0, 352.3, 127.6, GREY_RULE, 1.0)
        p.text(369.3, 121.8, "Station", 700, 9.4)
        p.text(413.3, 119.8, info["station"], 900, 11.25)
        p.rule(407.3, 464.3, 127.6, GREY_RULE, 1.0)
        p.text(46.7, 142.0, "Clue", 700, 9.4)
        clue_pt = 11.25
        f = _inter(900, clue_pt * p.kx)
        while f.getlength(info["clue"]) / p.kx > 264 and clue_pt > 7:
            clue_pt -= 0.4
            f = _inter(900, clue_pt * p.kx)
        cx = p.text(78.8, 140.2, info["clue"], 900, clue_pt)
        cend = max(cx + 5.5, 150.0)
        p.rule(73.5, cend, 148.6, GREY_RULE, 1.0)
        rx = min(cend + 19.5, 367.2) if cend < 340 else cend + 12
        rx = max(rx, cend + 12)
        tx = p.text(rx, 142.0, "Rule", 700, 9.4)
        rule_pt = 9.75
        f = _inter(900, rule_pt * p.kx)
        while tx + 12 + f.getlength(info["rule"]) / p.kx > 572 and rule_pt > 6.5:
            rule_pt -= 0.4
            f = _inter(900, rule_pt * p.kx)
        ex = p.text(tx + 12.0, 141.2, info["rule"], 900, rule_pt, (138, 90, 18))
        p.rule(tx + 6.0, ex + 5.5, 148.6, GREY_RULE, 1.0)
        p.zone(58.6, 183.5, 2, "Draw what Turkey sees", "Pilot", rule_y=164.4)
        cx, cy = RING_C
        for r in (RING_OUT, RING_IN):
            p.d.ellipse([p.X(cx - r), p.Y(cy - r), p.X(cx + r), p.Y(cy + r)], outline=PRINT, width=max(2, int(round(0.95 * p.kx))))
        for k in range(1, 7):
            b = B[f"die{k}"]
            p.die((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, k, 21.4)
        p.zone(58.6, 481.0, 3, "Write 3 things", "Pilot", rule_y=461.9)
        for q, n_, s in (("q1", "1.", "Who is outside the glass? What do they think our sub is?"), ("q2", "2.", "What one thing does Turkey do?"), ("q3", "3.", "How could this use up our air?")):
            y0 = {"q1": 499.6, "q2": 563.6, "q3": 627.6}[q]
            tx = p.text(46.7, y0 + 6.6, n_, 900, 10.9)
            p.text(tx + 2.6, y0 + 6.6, s, 700, 10.9)
            for ln in (y0 + 18.3 + 19.84, y0 + 18.3 + 39.7):
                p.rule(46.7, 565.3, ln, GREY_RULE, 0.8)
        p.text(46.7, 712.6, "← Pass your paper left", 900, 9.75)
        p.text(575.2, 767.6, "In the film TOURKEY TROUTTOWN", 700, 6.75, (95, 108, 112), "rm")
    else:
        p.zone(59.4, 92.8, 4, "Three kinds of endings", "Everyone", rule_y=74.6)
        for i, (word, l1, l2) in enumerate((("Probable", "what you", "expect"), ("Plausible", "strange, but it", "fits"), ("Preposterous", "a wild", "surprise!"))):
            x0 = 46.7 + 175.7 * i
            p.die(x0 + 15.1, 125.3, i + 1, 17.0)
            p.die(x0 + 35.3, 125.3, i + 4, 17.0)
            tx = p.text(x0 + 49.2, 125.5, word, 900, 9.75)
            p.text(tx + 5.2, 119.6, l1, 600, 8.6)
            p.text(tx + 5.2, 130.6, l2, 600, 8.6)
        for j, (dx, n_, title, who, tag, opts, kinds, back) in enumerate((
                (0.0, 5, "First friend", "Bolts 1, 2, 3", "Turkey thinks", info["turkey"], ("triangle", "circle"), "← Pass it left again"),
                (274.8, 6, "Next friend", "Bolts 4, 5, 6", "The trout think", info["trout"], ("cross", "square"), "→ Give it back to the pilot"))):
            p.zone(59.4 + dx, 174.0, n_, title, who, 36.8 + dx + (0.5 if j else 0), (299.5 if j == 0 else 575.2), rule_y=155.3)
            p.text(46.7 + dx, 202.2, "Name", 700, 9.4)
            p.rule(78.8 + dx, 290.5 + dx, 208.0, GREY_RULE, 1.0)
            p.text(53.1 + dx, 223.9, tag, 900, 9.4)
            for a, (opt, kind) in enumerate(zip(opts, kinds)):
                b = B[f"plate{j + 1}{'ab'[a]}"]
                p.d.rounded_rectangle([p.X(b[0]), p.Y(b[1]), p.X(b[2]), p.Y(b[3])], 7.4 * p.kx, outline=BTN[kind], width=max(2, int(round(1.2 * p.kx))))
                p.button(b[0] + 12.3, (b[1] + b[3]) / 2, kind, 17.0)
                pt = 9.75
                while _inter(700, pt * p.kx).getlength(opt) / p.kx > 196 and pt > 6.5:
                    pt -= 0.4
                p.text(b[0] + 26.9, (b[1] + b[3]) / 2, opt, 700, pt)
            p.text(53.1 + dx, 301.5, "Draw the one you pick", 700, 9.0)
            c = B[f"draw{j + 1}.circle"]
            ccx, ccy, cr = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2, (c[2] - c[0]) / 2
            for q in range(26):
                a0 = q * 360 / 26
                p.d.arc([p.X(ccx - cr), p.Y(ccy - cr), p.X(ccx + cr), p.Y(ccy + cr)], a0, a0 + 8.2, fill=GREY_RULE, width=max(2, int(round(0.95 * p.kx))))
            for i, (word, hint) in enumerate((("Probable", "What would you expect?"), ("Plausible", "Strange, but it fits."), ("Preposterous", "A wild surprise!"))):
                n = i + 1 + 3 * j
                y0 = 327.9 + 52.4 * i
                p.die(55.2 + dx, y0 + 8.3, n, 17.0)
                tx = p.text(68.2 + dx, y0 + 8.6, word, 900, 9.75)
                p.text(tx + 4.6, y0 + 8.2, hint, 600, 8.6, SOFT)
                p.rule(46.7 + dx, 290.5 + dx, y0 + 32.6, GREY_RULE, 0.8)
                p.rule(46.7 + dx, 290.5 + dx, y0 + 48.2, GREY_RULE, 0.8)
            p.text(57.0 + dx, 496.5, back, 900, 9.75)
        p.zone(58.6, 540.8, 7, "Roll", "Pilot", rule_y=522.2)
        p.text(46.7, 567.4, "Roll the die one time.", 700, 10.5)
        p.text(173.0, 569.6, "I rolled", 700, 10.5)
        p.rule(213.0, 258.6, 576.0, GREY_RULE, 1.0)
        p.text(278.5, 567.4, "or circle it", 700, 10.5)
        for k in range(6):
            p.die(343.4 + 24.56 * k, 568.2, k + 1, 21.0)
        p.zone(59.4, 611.4, 8, "Tell what happened", "Pilot", rule_y=592.7)
        for s, y0 in (("What do the trout tell the newspaper?", 630.1), ("Why did Turkey come to Trout Town?", 689.5)):
            p.text(46.7, y0 + 6.6, s, 700, 10.9)
            ly = y0 + 18.3
            p.rule(46.7, 565.3, ly + 17.6, GREY_RULE, 0.8)
            p.rule(46.7, 565.3, ly + 35.2, GREY_RULE, 0.8)
        p.text(575.2, 767.6, f"Porthole {num} · {info['station']}", 700, 6.75, (95, 108, 112), "rm")
    return p.done()


def sheet(size=SHEET_SIZE, page=1, porthole=None):
    """The printed Porthole Log page as a fresh PIL image (RGB) you may draw and write on: page 1 (the pilot's:
    slip line, the ring with its six die-face bolts, the three questions) or page 2 (three kinds of endings, the two
    friends' columns with their option buttons and three endings each, the roll, tell what happened).
    porthole=NN prints that porthole's own number, station, clue, rule and options (from ../seeds.json);
    None prints the master's example. Redrawn in code from ../sheets/master-1.png, master-2.png and steps.json."""
    return _sheet((int(size[0]), int(size[1])), int(page), porthole).copy()


def lay(target, img, x, y, angle=0.0, scale=1.0, lift=0.0, shadow=0.45):
    """Lay a page (or any image) on the desk with its centre at (x, y), turned `angle` degrees clockwise, enlarged by
    `scale`, with its shadow; lift (px) raises it (a sheet being passed). Returns a function f(sx, sy) -> (X, Y) that
    turns a point of the image (a where() corner, a write_on() tip) into its place on the target."""
    im = img.convert("RGBA")
    w, h = im.size
    if scale != 1.0:
        im = im.resize((max(2, int(round(w * scale))), max(2, int(round(h * scale)))), Image.LANCZOS)
    if angle:
        im = im.rotate(-angle, Image.BICUBIC, expand=True)
    px, py = x - im.size[0] / 2 - lift * 0.2, y - im.size[1] / 2 - lift * 0.6
    if shadow:
        _comp(target, shadow_of(im.getchannel("A"), 7 + lift * 0.3, shadow * (1 - min(0.5, lift / 160))), (px + 6 + lift * 0.6, py + 9 + lift))
    _comp(target, im, (px, py))
    _sync(target)
    M = Tm(x - lift * 0.2, y - lift * 0.6) @ Rm(angle) @ Sm(scale) @ Tm(-w / 2, -h / 2)
    return lambda sx, sy: apply(M, (sx, sy))


# ============================================================ A CHILD'S PENCIL
# The alphabet is built from strokes, the way a nine-year-old prints: ball and stick, each stroke its own pull of the
# pencil. Units: x-height = 1, baseline y = 0 (y up), ascenders to 1.9, capitals 1.75, descenders to -0.75.
# A list is a curved stroke, a tuple a straight-cornered one. (advance, [strokes]).
def _E(cx, cy, rx, ry, a0, a1, n=12):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def _glyphs():
    bowl = lambda cx: _E(cx, 0.5, 0.40, 0.5, 40, 400, 14)                      # noqa: E731
    G = {
        "a": (1.02, [bowl(0.44), ((0.84, 1.0), (0.84, 0.0))]),
        "b": (1.0, [((0.1, 1.9), (0.1, 0.0)), _E(0.5, 0.5, 0.40, 0.5, 150, 510, 14)]),
        "c": (0.9, [_E(0.48, 0.5, 0.40, 0.5, 50, 310, 12)]),
        "d": (1.05, [bowl(0.45), ((0.86, 1.9), (0.86, 0.0))]),
        "e": (0.95, [[(0.1, 0.52), (0.84, 0.52)] + _E(0.47, 0.5, 0.39, 0.5, 2, 305, 12)[1:]]),
        "f": (0.72, [[(0.74, 1.68), (0.56, 1.9), (0.38, 1.7), (0.35, 1.2), (0.35, 0.0)], ((0.05, 1.0), (0.66, 1.0))]),
        "g": (1.05, [bowl(0.45), [(0.86, 1.0), (0.86, -0.38), (0.66, -0.74), (0.36, -0.75), (0.14, -0.52)]]),
        "h": (0.95, [((0.1, 1.9), (0.1, 0.0)), [(0.1, 0.58), (0.3, 0.94), (0.55, 1.0), (0.74, 0.8), (0.77, 0.0)]]),
        "i": (0.42, [((0.16, 1.0), (0.16, 0.0)), ((0.15, 1.5), (0.19, 1.42))]),
        "j": (0.5, [[(0.3, 1.0), (0.3, -0.38), (0.16, -0.72), (-0.1, -0.62)], ((0.29, 1.5), (0.33, 1.42))]),
        "k": (0.86, [((0.1, 1.9), (0.1, 0.0)), ((0.72, 1.0), (0.12, 0.44)), ((0.32, 0.62), (0.76, 0.0))]),
        "l": (0.4, [((0.15, 1.9), (0.15, 0.0))]),
        "m": (1.25, [((0.1, 1.0), (0.1, 0.0)), [(0.1, 0.62), (0.28, 0.96), (0.5, 0.9), (0.56, 0.0)], [(0.56, 0.62), (0.75, 0.96), (0.97, 0.9), (1.02, 0.0)]]),
        "n": (0.95, [((0.1, 1.0), (0.1, 0.0)), [(0.1, 0.58), (0.3, 0.94), (0.55, 1.0), (0.73, 0.8), (0.76, 0.0)]]),
        "o": (0.96, [_E(0.47, 0.5, 0.40, 0.5, 80, 445, 14)]),
        "p": (1.0, [((0.1, 1.0), (0.1, -0.75)), _E(0.5, 0.5, 0.40, 0.5, 150, 510, 14)]),
        "q": (1.05, [bowl(0.45), ((0.86, 1.0), (0.86, -0.75))]),
        "r": (0.74, [((0.1, 1.0), (0.1, 0.0)), [(0.1, 0.56), (0.28, 0.9), (0.48, 1.0), (0.68, 0.88)]]),
        "s": (0.84, [[(0.7, 0.84), (0.5, 1.0), (0.26, 0.95), (0.15, 0.75), (0.3, 0.55), (0.55, 0.44), (0.7, 0.25), (0.55, 0.03), (0.3, 0.0), (0.1, 0.16)]]),
        "t": (0.74, [[(0.35, 1.62), (0.35, 0.22), (0.45, 0.03), (0.66, 0.06)], ((0.04, 1.0), (0.68, 1.0))]),
        "u": (0.96, [[(0.1, 1.0), (0.1, 0.3), (0.25, 0.03), (0.5, 0.02), (0.7, 0.25), (0.76, 1.0)], ((0.76, 1.0), (0.76, 0.0))]),
        "v": (0.84, [((0.05, 1.0), (0.4, 0.0), (0.76, 1.0))]),
        "w": (1.16, [((0.05, 1.0), (0.3, 0.0), (0.55, 0.8), (0.8, 0.0), (1.06, 1.0))]),
        "x": (0.84, [((0.08, 1.0), (0.75, 0.0)), ((0.75, 1.0), (0.08, 0.0))]),
        "y": (0.84, [((0.08, 1.0), (0.42, 0.06)), [(0.78, 1.0), (0.42, 0.06), (0.26, -0.5), (0.05, -0.72)]]),
        "z": (0.86, [((0.08, 1.0), (0.75, 1.0), (0.08, 0.0), (0.78, 0.0))]),
        "A": (1.14, [((0.05, 0.0), (0.55, 1.75), (1.05, 0.0)), ((0.25, 0.62), (0.86, 0.62))]),
        "B": (1.04, [((0.12, 1.75), (0.12, 0.0)), [(0.12, 1.75), (0.6, 1.72), (0.8, 1.35), (0.6, 0.96), (0.12, 0.92)], [(0.12, 0.92), (0.7, 0.88), (0.9, 0.45), (0.66, 0.03), (0.12, 0.0)]]),
        "C": (1.1, [_E(0.6, 0.875, 0.5, 0.875, 48, 312, 14)]),
        "D": (1.1, [((0.12, 1.75), (0.12, 0.0)), [(0.12, 1.75), (0.6, 1.64), (0.95, 0.9), (0.6, 0.1), (0.12, 0.0)]]),
        "E": (0.95, [((0.8, 1.75), (0.12, 1.75), (0.12, 0.0), (0.82, 0.0)), ((0.12, 0.9), (0.66, 0.9))]),
        "F": (0.9, [((0.8, 1.75), (0.12, 1.75), (0.12, 0.0)), ((0.12, 0.9), (0.62, 0.9))]),
        "G": (1.2, [_E(0.6, 0.875, 0.5, 0.875, 48, 330, 14) + [(1.06, 0.78), (0.66, 0.78)]]),
        "H": (1.1, [((0.12, 1.75), (0.12, 0.0)), ((0.92, 1.75), (0.92, 0.0)), ((0.12, 0.9), (0.92, 0.9))]),
        "I": (0.6, [((0.24, 1.75), (0.24, 0.0)), ((0.04, 1.75), (0.44, 1.75)), ((0.04, 0.0), (0.44, 0.0))]),
        "J": (0.9, [[(0.7, 1.75), (0.7, 0.4), (0.5, 0.02), (0.25, 0.02), (0.08, 0.36)]]),
        "K": (1.0, [((0.12, 1.75), (0.12, 0.0)), ((0.86, 1.75), (0.12, 0.74)), ((0.36, 1.02), (0.9, 0.0))]),
        "L": (0.86, [((0.12, 1.75), (0.12, 0.0), (0.78, 0.0))]),
        "M": (1.32, [((0.1, 0.0), (0.1, 1.75), (0.6, 0.5), (1.1, 1.75), (1.1, 0.0))]),
        "N": (1.12, [((0.1, 0.0), (0.1, 1.75), (0.9, 0.0), (0.9, 1.75))]),
        "O": (1.2, [_E(0.6, 0.875, 0.5, 0.875, 80, 445, 16)]),
        "P": (1.0, [((0.12, 1.75), (0.12, 0.0)), [(0.12, 1.75), (0.65, 1.7), (0.85, 1.3), (0.65, 0.88), (0.12, 0.85)]]),
        "Q": (1.2, [_E(0.6, 0.875, 0.5, 0.875, 80, 445, 16), ((0.7, 0.42), (1.1, -0.1))]),
        "R": (1.05, [((0.12, 1.75), (0.12, 0.0)), [(0.12, 1.75), (0.65, 1.7), (0.85, 1.3), (0.65, 0.88), (0.12, 0.85)], ((0.45, 0.85), (0.9, 0.0))]),
        "S": (1.0, [[(0.85, 1.5), (0.6, 1.75), (0.3, 1.68), (0.15, 1.35), (0.35, 1.0), (0.65, 0.8), (0.85, 0.45), (0.65, 0.05), (0.35, 0.0), (0.1, 0.26)]]),
        "T": (1.04, [((0.02, 1.75), (1.0, 1.75)), ((0.5, 1.75), (0.5, 0.0))]),
        "U": (1.06, [[(0.1, 1.75), (0.1, 0.5), (0.3, 0.05), (0.6, 0.03), (0.85, 0.5), (0.88, 1.75)]]),
        "V": (1.0, [((0.05, 1.75), (0.5, 0.0), (0.95, 1.75))]),
        "W": (1.46, [((0.05, 1.75), (0.36, 0.0), (0.7, 1.3), (1.05, 0.0), (1.36, 1.75))]),
        "X": (1.0, [((0.08, 1.75), (0.9, 0.0)), ((0.9, 1.75), (0.08, 0.0))]),
        "Y": (1.0, [((0.05, 1.75), (0.5, 0.85)), ((0.95, 1.75), (0.5, 0.85), (0.5, 0.0))]),
        "Z": (1.0, [((0.08, 1.75), (0.9, 1.75), (0.08, 0.0), (0.94, 0.0))]),
        "0": (1.0, [_E(0.5, 0.875, 0.4, 0.875, 80, 445, 16)]),
        "1": (0.7, [((0.12, 1.4), (0.4, 1.75), (0.4, 0.0))]),
        "2": (1.0, [[(0.12, 1.4), (0.35, 1.72), (0.68, 1.68), (0.8, 1.35), (0.6, 0.9), (0.1, 0.0)], ((0.1, 0.0), (0.88, 0.0))]),
        "3": (1.0, [[(0.12, 1.5), (0.4, 1.75), (0.72, 1.6), (0.72, 1.2), (0.42, 0.95)], [(0.42, 0.95), (0.8, 0.7), (0.8, 0.3), (0.5, 0.0), (0.1, 0.2)]]),
        "4": (1.0, [((0.62, 1.75), (0.08, 0.6), (0.9, 0.6)), ((0.66, 1.2), (0.66, 0.0))]),
        "5": (1.0, [((0.8, 1.75), (0.2, 1.75), (0.16, 1.0)), [(0.16, 1.0), (0.5, 1.12), (0.82, 0.8), (0.78, 0.3), (0.45, 0.0), (0.1, 0.2)]]),
        "6": (1.0, [[(0.75, 1.7), (0.4, 1.5), (0.15, 0.9), (0.14, 0.4), (0.4, 0.0), (0.72, 0.15), (0.8, 0.55), (0.55, 0.92), (0.18, 0.7)]]),
        "7": (0.96, [((0.08, 1.75), (0.86, 1.75), (0.36, 0.0))]),
        "8": (1.0, [[(0.5, 0.95), (0.2, 1.3), (0.3, 1.7), (0.6, 1.74), (0.78, 1.4), (0.5, 0.95), (0.16, 0.5), (0.3, 0.05), (0.66, 0.03), (0.84, 0.45), (0.5, 0.95)]]),
        "9": (1.0, [_E(0.46, 1.25, 0.34, 0.5, 20, 380, 12), ((0.8, 1.6), (0.78, 0.0))]),
        ".": (0.42, [((0.14, 0.02), (0.2, 0.1), (0.15, 0.08))]),
        ",": (0.42, [((0.2, 0.1), (0.18, -0.1), (0.06, -0.3))]),
        "!": (0.5, [((0.2, 1.75), (0.2, 0.5)), ((0.19, 0.03), (0.24, 0.1))]),
        "?": (0.9, [[(0.1, 1.4), (0.3, 1.72), (0.62, 1.7), (0.76, 1.35), (0.45, 0.9), (0.42, 0.5)], ((0.41, 0.03), (0.46, 0.1))]),
        "'": (0.34, [((0.18, 1.9), (0.13, 1.45))]),
        "’": (0.34, [((0.18, 1.9), (0.13, 1.45))]),
        '"': (0.56, [((0.14, 1.9), (0.12, 1.45)), ((0.38, 1.9), (0.36, 1.45))]),
        "-": (0.78, [((0.1, 0.62), (0.62, 0.62))]),
        ":": (0.42, [((0.15, 0.82), (0.2, 0.9)), ((0.15, 0.03), (0.2, 0.1))]),
        "(": (0.56, [[(0.42, 1.9), (0.14, 1.2), (0.14, 0.4), (0.42, -0.3)]]),
        ")": (0.56, [[(0.1, 1.9), (0.38, 1.2), (0.38, 0.4), (0.1, -0.3)]]),
        "/": (0.76, [((0.66, 1.9), (0.08, -0.2))]),
        "&": (1.1, [[(0.9, 0.0), (0.3, 1.2), (0.36, 1.66), (0.6, 1.7), (0.66, 1.3), (0.14, 0.5), (0.3, 0.03), (0.6, 0.1), (0.92, 0.7)]]),
        "+": (0.9, [((0.1, 0.62), (0.76, 0.62)), ((0.43, 0.95), (0.43, 0.28))]),
    }
    return G


_GLYPHS = _glyphs()
_plan_cache = {}


def _stroke_pts(st, per=5):
    if isinstance(st, tuple):
        out = []
        for a, b in zip(st, st[1:]):
            n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 8))
            out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
        return out + [st[-1]]
    return catmull(st, per)


class WritePlan:
    """One line of a child's writing, planned: .strokes (screen polylines), .tip(u) -> (x, y, down), .x_end."""

    def __init__(self, box, text, seed=0, size=None, slant=None):
        x0, y0, x1, y1 = [float(v) for v in box]
        bh, bw = y1 - y0, x1 - x0
        rs = random.Random(seed * 7919 + len(text) * 131 + sum(ord(c) * (i + 1) for i, c in enumerate(text)))
        xh = float(size) if size else 0.40 * bh
        gap, space = 0.20, 0.72
        total = sum((_GLYPHS.get(ch, _GLYPHS["o"])[0] + gap) if ch != " " else space for ch in text) * xh
        if total > bw * 0.98 and not size:
            xh *= max(0.74, bw * 0.98 / total)                 # squeezes up as the edge comes, then runs off it
        self.xh = xh
        base = y1 - 0.07 * bh - rs.uniform(0, 0.03) * bh
        slope = rs.uniform(-0.012, 0.016)
        ph = rs.uniform(0, 6.283)
        sl0 = rs.uniform(-0.03, 0.10) if slant is None else slant
        x = x0 + rs.uniform(0.15, 0.6) * xh
        self.strokes, self.letter = [], []
        word_dy = 0.0
        for i, ch in enumerate(text):
            if ch == " ":
                x += space * xh * rs.uniform(0.85, 1.3)
                word_dy = rs.uniform(-0.07, 0.07) * xh          # each word starts a touch higher or lower
                continue
            adv, strokes = _GLYPHS.get(ch, _GLYPHS["o"])
            sc = xh * rs.uniform(0.90, 1.12)
            rot = math.radians(rs.uniform(-4.5, 4.5))
            sl = sl0 + rs.uniform(-0.05, 0.05)
            dy = word_dy + rs.uniform(-0.06, 0.06) * xh + 0.07 * xh * math.sin(i * 0.55 + ph) + slope * (x - x0)
            ca, sa = math.cos(rot), math.sin(rot)
            p1, p2 = rs.uniform(0, 6.283), rs.uniform(0, 6.283)
            for st in strokes:
                pts = []
                for (gx, gy) in _stroke_pts(st):
                    gx2 = gx + sl * gy + 0.035 * math.sin(gy * 3.1 + p1)
                    gy2 = gy + 0.03 * math.sin(gx * 4.3 + p2)
                    px, py = gx2 * ca + gy2 * sa, -gx2 * sa + gy2 * ca
                    pts.append((x + px * sc, base + dy - py * sc))
                self.strokes.append(pts)
                self.letter.append(i)
            x += (adv + gap * rs.uniform(0.7, 1.5)) * sc
        self.x_end = x
        # timing: ink at full speed, air between strokes a little quicker, plus a beat for each lift
        self.seg = []
        T = 0.0
        prev = None
        for pts in self.strokes:
            if prev is not None:
                air = math.hypot(pts[0][0] - prev[0], pts[0][1] - prev[1]) * 0.55 + 0.5 * xh
                self.seg.append(("air", T, T + air, prev, pts[0]))
                T += air
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) + 0.25 * xh
            self.seg.append(("ink", T, T + L, pts, None))
            T += L
            prev = pts[-1]
        self.T = max(T, 1e-6)
        self.start = self.strokes[0][0] if self.strokes else (x0, base)
        self.end = prev if prev else (x0, base)

    def upto(self, u):
        """(the polylines written by fraction u, tip x, tip y, pencil down?)"""
        if u <= 0 or not self.seg:
            return [], self.start[0], self.start[1], False
        if u >= 1:
            return list(self.strokes), self.end[0], self.end[1], False
        tt = u * self.T
        done = []
        for kind, a, b, p, q in self.seg:
            if tt >= b:
                if kind == "ink":
                    done.append(p)
                continue
            f = (tt - a) / max(b - a, 1e-6)
            if kind == "air":
                f = f * f * (3 - 2 * f)
                return done, p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f, False
            n = min(len(p) - 1, max(1, int(round(f * (len(p) - 1)))))
            done.append(p[:n + 1])
            return done, p[n][0], p[n][1], True
        return done, self.end[0], self.end[1], False

    def tip(self, u):
        _, x, y, down = self.upto(u)
        return (x, y, down)

    def letters(self, u):
        """How many characters are finished at fraction u (for sound: one scratch a letter)."""
        done, _, _, _ = self.upto(u)
        return 0 if not done else self.letter[len(done) - 1] + 1


def write_plan(box, text, seed=0, size=None):
    key = (tuple(round(float(v), 2) for v in box), text, seed, size)
    if key not in _plan_cache:
        if len(_plan_cache) > 400:
            _plan_cache.clear()
        _plan_cache[key] = WritePlan(box, text, seed, size)
    return _plan_cache[key]


def graphite(target, lines, width=1.5, weight=1.0, seed=0, color=None):
    """Pencil lines (a list of screen polylines) with the paper's tooth in them. weight 1 = a firm child's line,
    0.45 = written faintly afterwards, 1.4 = pressed hard. Use it for drawings as well as for letters."""
    lines = [ln for ln in lines if len(ln) >= 1]
    if not lines:
        return
    img = _img(target)
    xs = [p[0] for ln in lines for p in ln]
    ys = [p[1] for ln in lines for p in ln]
    pad = int(width * 2 + 4)
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    x1, y1 = int(math.ceil(max(xs))) + pad, int(math.ceil(max(ys))) + pad
    x0, y0, x1, y1 = max(x0, -50), max(y0, -50), min(x1, img.size[0] + 50), min(y1, img.size[1] + 50)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return
    S = 3
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    rs = random.Random(seed + 5)
    wd = max(2, int(round(width * S)))
    for ln in lines:
        v = int(255 * rs.uniform(0.80, 1.0))
        pts = [((x - x0) * S, (y - y0) * S) for x, y in ln]
        if len(pts) > 1:
            d.line(pts, fill=v, width=wd, joint="curve")
        r = wd / 2
        for (px, py) in (pts[0], pts[-1]):
            d.ellipse([px - r, py - r, px + r, py + r], fill=v)
    m = m.resize((w, h), Image.LANCZOS)
    a = np.asarray(m, np.float32) / 255
    tooth = 0.80 + 0.36 * vnoise((h, w), 1.4, None, 811 + seed % 7) + 0.14 * vnoise((h, w), 11, None, 812 + seed % 5)
    a = np.clip(a * 1.25, 0, 1) * np.clip(tooth, 0.3, 1.2) * clamp(0.30 + 0.56 * weight, 0.1, 0.98)
    g = np.zeros((h, w, 4), np.uint8)
    g[..., :3] = color or mixc(GRAPHITE, (30, 30, 36), clamp(weight - 0.6))
    g[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    _comp(img, Image.fromarray(g, "RGBA"), (x0, y0))
    _sync(target)


def write_on(img, box, text, u=1.0, seed=0, weight=1.0, size=None, color=None):
    """Letter `text` in a child's pencil hand along the line `box` = (x0, y0, x1, y1) (a where() line: y1 is the
    printed rule), stroke by stroke up to fraction u (0..1 of the time the line takes, lifts between strokes
    included). The baseline wanders, the letters differ in size and lean, a long line squeezes up and then runs off
    the right edge. seed picks the child's hand for that line (the same seed always writes the same line);
    weight 1 = firm, 0.45 = faint (a word added afterwards), 1.3 = pressed. size = x-height in px (default 0.40 of
    the box height). Draws on img (a PIL image or an Ink) and returns the pencil tip (x, y) so a hand can follow it;
    write_tip(...) gives (x, y, down) without drawing."""
    plan = write_plan(box, text, seed, size)
    done, x, y, down = plan.upto(u)
    graphite(img, done, max(1.2, plan.xh * 0.15) * (0.82 + 0.22 * weight), weight, seed, color)
    return (x, y)


def write_tip(box, text, u, seed=0, size=None):
    """Where the pencil point is at fraction u of writing that line, and whether it is on the paper: (x, y, down).
    Between strokes the point travels through the air (down = False): lift the hand a few px then."""
    return write_plan(box, text, seed, size).tip(u)


# ================================================================== THE SLIP
_slip_cache = {}


def slip(target, x, y, n, clue, scale=1.0, angle=0.0, picture=None):
    """The small numbered slip the pilot was handed, as it sits on the desk: scissor-cut paper (260 x 150 at scale
    1) with the porthole number, a square picture space on the left (blank unless you pass picture= a PIL image, e.g.
    a frame of the porthole's own film) and the clue beside it. (x, y) = its centre. Returns the picture space's
    screen box (x0, y0, x1, y1) when angle is 0, else its centre."""
    key = (n, clue, id(picture) if picture is not None else None)
    if key not in _slip_cache:
        if len(_slip_cache) > 16:
            _slip_cache.clear()

        def deco(d, L, S):
            d.rounded_rectangle([L(-118, -62)[0], L(-118, -62)[1], L(-6, 50)[0], L(-6, 50)[1]], 6 * S, fill=(255, 255, 255), outline=GREY_RULE, width=int(1.2 * S))
            d.text(L(8, -68), str(n), font=_inter(900, 44 * S), fill=PRINT)
            d.text(L(8, -14), "Clue", font=_inter(700, 8 * S), fill=PRINT)
            words, lines, cur = str(clue).split(), [], ""
            f = _inter(700, 11.5 * S)
            for wd in words:
                if f.getlength((cur + " " + wd).strip()) > 112 * S and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            lines.append(cur)
            for i, ln in enumerate(lines[:4]):
                d.text(L(8, -3 + i * 14.5), ln, font=f, fill=PRINT)
        spr = cut([(-130, -74), (129, -76), (131, 73), (-128, 76)], PAPER, deco, curve=False, seed=201, grain=0.03, edge=0.6)   # cut by hand, not quite square
        if picture is not None:
            pic = picture.convert("RGB").resize((108, 108), Image.LANCZOS)
            spr.img.paste(pic, (-116 - spr.ox, -60 - spr.oy))
        _slip_cache[key] = spr
    M = Tm(x, y) @ Rm(angle) @ Sm(scale)
    draw_sprite(target, _slip_cache[key], M, (3, 5, 3, 0.42))
    _sync(target)
    if angle == 0:
        return (x - 118 * scale, y - 62 * scale, x - 6 * scale, y + 50 * scale)
    return apply(M, (-62, -6))


# ==================================================================== TESTS
def _grid(tiles, cols, size):
    rows = (len(tiles) + cols - 1) // cols
    out = Image.new("RGB", (cols * size[0], rows * size[1]), (30, 30, 34))
    for i, im in enumerate(tiles):
        out.paste(im.convert("RGB").resize(size, Image.LANCZOS), ((i % cols) * size[0], (i // cols) * size[1]))
    return out


def _tests(out=STILLS):
    out.mkdir(parents=True, exist_ok=True)
    # 1. every hand pose, three moments each, on a page on the desk
    tiles = []
    for i, pose in enumerate(POSES):
        for j, tt in enumerate((0.05, 0.13, 0.21)):
            fr = Image.new("RGB", (480, 360), DESK)
            desk(fr)
            pg = sheet(page=1, porthole=13)
            lay(fr, pg, 150, 300, -3, 0.8)
            x, y = (200, 190) if pose != "fist_chin" else (250, 120)
            hand(fr, x, y, pose=pose, tone=TONE_NAMES[i % 4], t=tt + i)
            d = ImageDraw.Draw(fr)
            d.line([x - 6, y, x + 6, y], fill=(255, 0, 0))
            d.line([x, y - 6, x, y + 6], fill=(255, 0, 0))
            d.text((6, 6), f"{pose}  t={tt}", fill=(255, 255, 255))
            tiles.append(fr)
    _grid(tiles, 6, (320, 240)).save(out / "hands.png")
    # 2. the pilot's page in close-up, the line being written with the hand following
    for k, u in enumerate((0.35, 0.8, 1.0)):
        fr = Image.new("RGB", (W, H), DESK)
        desk(fr)
        pg = sheet(page=1, porthole=13)
        write_on(pg, where(1, "a1.1"), "The trout. The trout think's the sub is a", 1.0, seed=3)
        write_on(pg, where(1, "a1.2"), "Bell-ringer Prank.", 1.0, seed=4)
        tip = write_on(pg, where(1, "a2.1"), "freek out.", min(1.0, u / 0.8), seed=5)
        if u >= 1.0:
            write_on(pg, where(1, "a2.1"), "                    the     sub.", 1.0, seed=6, weight=0.45)
            write_on(pg, where(1, "a3.1"), "he is going to be turkey diner.", 1.0, seed=7)
        f = lay(fr, pg, 480, 540 - 700 * 960 / 760.0 + 300, 0, 960 / 760.0)
        X, Y = f(*tip)
        if u < 1.0:
            hand(fr, X, Y, pose="write", tone="rust", t=u)
        else:
            hand(fr, X + 60, Y - 30, pose="hover", tone="rust", t=u)
        fr.save(out / f"writing_{k}.png")
    # 3. rubbing out
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    pg = sheet(page=2, porthole=10)
    b = where(2, "bolt2.1")
    write_on(pg, b, "he dos not get beck", 1.0, seed=9)
    rub_mark(pg, (b[0] + 96, b[1] - 2, b[0] + 190, b[3] + 3), 1.0, seed=1)
    write_on(pg, where(2, "bolt1.1"), "the trout to be outsid", 1.0, seed=8)
    write_on(pg, where(2, "name1.line"), "M.", 1.0, seed=2)
    f = lay(fr, pg, 760, 540 - 300 * 1.6 + 60, 2, 1.6)
    X, Y = f(b[0] + 150, b[3] - 6)
    eraser_crumbs(fr, X + 20, Y + 26, 16, seed=2)
    hand(fr, X, Y, pose="erase", tone="plum", t=0.3)
    slip(fr, 800, 440, 10, "Elementary brick: flapping Clam-Shell PA", 0.9, angle=8)
    pencil(fr, 620, 500, -8)
    fr.save(out / "rub.png")
    # 4. backs of heads
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    lay(fr, sheet(page=1, porthole=16), 480, 120, 0, 0.42)
    for i, (hr, tl, tu) in enumerate((("short", 0, 0), ("bun", -8, 0), ("braids", 14, 0.8), ("curly", -14, -0.9))):
        head_back(fr, 130 + 235 * i, 330, TONE_NAMES[i], 0.72, tl, hr, turn=tu, t=i)
    fr.save(out / "heads.png")
    # 5. over the shoulder: head, sheet, both hands
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    pg = sheet(page=1, porthole=16)
    f = lay(fr, pg, 470, 150, -4, 0.62)
    hand(fr, 300, 230, pose="hold", tone="ochre", flip=True, arm=118)
    hand(fr, *f(380, 560), pose="write", tone="ochre", arm=62)
    r = head_back(fr, 480, 470, "ochre", 1.15, tilt=-5, hair="braids", t=0.4)
    fr.save(out / "shoulder.png")
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    lay(fr, sheet(page=2, porthole=16), 470, 150, 3, 0.62)
    r = head_back(fr, 430, 500, "plum", 1.15, tilt=9, hair="curly", t=0.4)
    hand(fr, r["head"][0] + 58, r["head"][1] - 50, pose="scratch", tone="plum", arm=75, t=0.2)
    hand(fr, 760, 300, pose="fist_chin", tone="teal", t=0.2)
    fr.save(out / "scratch.png")
    # 6. the pass
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    pg = sheet(page=1, porthole=10)
    f = lay(fr, pg, 500, 300, -24, 0.6, lift=30)
    hand(fr, *f(760, 520), pose="pass", tone="rust", arm=20, lift=30, edge=90 - 24)
    hand(fr, *f(0, 420), pose="pass", tone="teal", arm=160, flip=True, lift=30, edge=90 - 24)
    fr.save(out / "pass.png")
    # 7. desk, room
    fr = Image.new("RGB", (W, H), DESK)
    desk(fr)
    cup(fr, 820, 300, 1.2)
    slip(fr, 240, 330, 13, "Bell Boulder arch with brass twig-bell")
    fr.save(out / "desk.png")
    fr = Image.new("RGB", (W, H), DESK)
    classroom(fr, 1.0)
    fr.save(out / "classroom.png")
    sheet(page=1, porthole=10).save(out / "sheet_p1_10.png")
    sheet(page=2, porthole=10).save(out / "sheet_p2_10.png")
    print("stills ->", out)


if __name__ == "__main__":
    _tests(Path(sys.argv[1]) if len(sys.argv) > 1 else STILLS)
