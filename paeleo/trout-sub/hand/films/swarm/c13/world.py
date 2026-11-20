"""c13 · world unit · the shared pieces for the class film of porthole 13 (Arch, the twig-bell).

Everything every scene of this film uses. Foraged: Turkey (Audubon, plate 1 of The Birds of America) and the
brook trout (Denton, 1896), both cut out and hinged here. Handmade in code: the bread-roll tin, the brass
porthole, the boulder arch, twig, bell, clapper and cord, weed, river planes, the pilot's pencil drawing,
buttons, dice, the die cup, the gauge, the pick card, the badge.

See WORLD.md for every function. Self-test:  python3 films/swarm/c13/world.py   (stills -> films/stills/c13_world/)
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
FILMS = _HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import Ink, W, H, FPS, font, clamp, ramp, smooth, ease, lerp, lerp2, mix_color  # noqa: E402

SRC = FILMS / "sources" / "c13"

# ------------------------------------------------------------------ palette ---

PAL = dict(
    table=(118, 86, 58), table_dk=(84, 58, 38), sheet=(246, 244, 238), sheet_edge=(214, 210, 200),
    print=(52, 50, 48), pencil=(96, 96, 104), pencil_soft=(138, 138, 146),
    water_top=(150, 196, 180), water_mid=(62, 128, 126), water_deep=(20, 60, 66), shaft=(226, 236, 190),
    stone=(124, 132, 120), stone_dk=(70, 80, 74), stone_lt=(170, 176, 160),
    moss=(96, 134, 62), moss_dk=(56, 92, 46), moss_lt=(150, 176, 84),
    weed=(60, 112, 70), weed_dk=(32, 74, 54), weed_lt=(126, 164, 92),
    twig=(98, 70, 46), twig_dk=(52, 36, 24), twig_lt=(156, 122, 84),
    brass=(190, 150, 66), brass_hi=(246, 220, 140), brass_dk=(112, 82, 34), brass_line=(56, 38, 14),
    tin=(142, 160, 166), tin_dk=(52, 62, 68), wall=(50, 44, 40),
    lamp=(255, 196, 92), amber=(232, 150, 60), cord=(196, 170, 120), cord_dk=(110, 86, 52),
    green=(52, 158, 84), red=(206, 52, 46), blue=(48, 104, 196), pink=(232, 120, 164), hexamber=(236, 160, 40),
    ivory=(240, 232, 208), pip=(40, 34, 30), leather=(122, 74, 44), leather_dk=(70, 40, 24),
    badge=(28, 28, 34), white=(250, 248, 242), unlit=(92, 86, 78),
)
BUTTONS = {"triangle": PAL["green"], "circle": PAL["red"], "cross": PAL["blue"], "square": PAL["pink"],
           "hexagon": PAL["hexamber"]}

# standard places (screen pixels). Scene units should use these so shots join.
PORT_C = (480, 262)        # centre of the round glass in every porthole shot and of the pencil ring on the table
PORT_R = 212               # radius of the glass / inner radius of the pencil ring
RING_OUT = 262             # outer radius of the brass ring / printed ring
STAGE = dict(              # Turkey's-seat stage, inside the glass
    arch_c=(480, 478), arch_w=500, bell_hang=(480, 150), bell_scale=1.0,
    twelve=(480, 118), nine=(318, 262), fish1=(432, 236), fish2=(566, 318),
    reflection=(368, 386), gauge=(820, 440),
)
RIVER = dict(              # river-side stage (bolts 4 to 6): the tin low, the arch foot and the bell above
    tin_c=(430, 404), tin_scale=0.82, arch_c=(560, 470), arch_w=560, bell_hang=(560, 104), bell_scale=1.1,
)


# ------------------------------------------------------------------ helpers ---

def vnoise(shape, sx, sy=None, seed=0, octaves=1):
    """Smooth value noise in 0..1, shape (h, w)."""
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


def _img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


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


def _shadow_of(spr, blur=5, strength=0.5, color=(8, 12, 16)):
    sh = Image.new("RGBA", spr.size, color + (0,))
    sh.putalpha(spr.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * strength)))
    return sh


def put(ink, spr, cx, cy, angle=0.0, scale=1.0, flip=False, alpha=1.0, shadow=0.0, shadow_off=(5, 7), shadow_blur=5):
    """Lay a cutout (RGBA) with its centre at (cx, cy). angle in degrees, counter-clockwise on screen.
    shadow 0..1 lays a soft contact shadow under it, displaced by shadow_off. Returns the pasted image."""
    im = spr
    if scale != 1.0:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.LANCZOS if scale < 1 else Image.BICUBIC)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if angle:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    if shadow > 0:
        pad = int(shadow_blur * 3)
        big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        big.paste(im, (pad, pad))
        ink.paste(_shadow_of(big, shadow_blur, 0.55 * shadow * alpha), (x - pad + shadow_off[0], y - pad + shadow_off[1]))
    ink.paste(im, (x, y), alpha)
    return im


def _pin(canvas, spr, pivot, target, deg):
    """Paste spr on canvas rotated deg (CCW on screen) about its own point `pivot`, so the pivot lands on `target`."""
    if abs(deg) < 0.05:
        canvas.alpha_composite(spr, (int(round(target[0] - pivot[0])), int(round(target[1] - pivot[1])))) if _fits(canvas, spr, target, pivot) \
            else _paste_clip(canvas, spr, (int(round(target[0] - pivot[0])), int(round(target[1] - pivot[1]))))
        return
    r = spr.rotate(deg, expand=True, resample=Image.BICUBIC)
    a = math.radians(deg)
    vx, vy = pivot[0] - spr.width / 2, pivot[1] - spr.height / 2
    px = r.width / 2 + vx * math.cos(a) + vy * math.sin(a)
    py = r.height / 2 - vx * math.sin(a) + vy * math.cos(a)
    _paste_clip(canvas, r, (int(round(target[0] - px)), int(round(target[1] - py))))


def _fits(canvas, spr, target, pivot):
    x, y = int(round(target[0] - pivot[0])), int(round(target[1] - pivot[1]))
    return x >= 0 and y >= 0 and x + spr.width <= canvas.width and y + spr.height <= canvas.height


def _paste_clip(canvas, spr, xy):
    x, y = xy
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(canvas.width, x + spr.width), min(canvas.height, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return
    canvas.alpha_composite(spr.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def offscreen(ink):
    """A second full canvas for the same frame (for the next scene behind a sweep). Draw on it, pass .img on."""
    o = Ink(ink.t, ink.i, (ink.w, ink.h), wobble=ink.wobble)
    o.rng = random.Random(ink.i * 31 + 7)
    return o


class Follower:
    """Spring-damper follower (secondary dynamics). target_fn(t) -> value; .at(t) is the lagging value.
    f = natural frequency in Hz, zeta = damping (0.15 rings a long time, 1.0 settles dead)."""

    def __init__(self, target_fn, seconds, f=1.6, zeta=0.25, x0=None):
        n = int(seconds * FPS) + 2
        w = 2 * math.pi * f
        x = target_fn(0.0) if x0 is None else x0
        v, out = 0.0, []
        dt = 1.0 / FPS / 6
        for k in range(n):
            tg = target_fn(k / FPS)
            for _ in range(6):
                v += (w * w * (tg - x) - 2 * zeta * w * v) * dt
                x += v * dt
            out.append(x)
        self.x = np.array(out)

    def at(self, t):
        k = clamp(t * FPS, 0, len(self.x) - 1.001)
        i = int(k)
        return float(self.x[i] + (self.x[i + 1] - self.x[i]) * (k - i))


def _paper_piece(size, pts, color, seed=0, edge=0.22, grain=0.16, shade=None):
    """A torn piece of coloured paper: textured, a paler fibre edge, optional shade gradient (dx, dy, amount)."""
    w, h = size
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.8))
    n = vnoise((h, w), 26, seed=seed, octaves=3) - 0.5
    fib = vnoise((h, w), 3, seed=seed + 5) - 0.5
    a = np.ones((h, w, 3), np.float32) * np.array(color, np.float32)
    a *= (1 + n * grain * 2 + fib * 0.08)[..., None]
    if shade:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = (xx / w - 0.5) * shade[0] + (yy / h - 0.5) * shade[1]
        a *= (1 - g * shade[2])[..., None]
    inner = np.asarray(m.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    rim = np.clip(np.asarray(m, np.float32) / 255 - inner, 0, 1)
    a = a * (1 - rim[..., None] * edge * 2.2) + 255 * rim[..., None] * edge * 2.2
    out = _img(a).convert("RGBA")
    out.putalpha(m)
    return out


# ------------------------------------------------------------- foraged cuts ---

def _biggest(mask):
    from scipy import ndimage as ndi
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    return ndi.binary_fill_holes(lab == (1 + int(np.argmax(sizes))))


def _src(name):
    p = SRC / name
    if not p.exists():
        raise SystemExit(f"missing foraged file {p}; see films/credits/c13.json")
    return Image.open(p).convert("RGB")


# Turkey: polygons in the pixels of the 1280-wide plate
_T_HEAD = [(903, 128), (940, 112), (975, 95), (990, 40), (1003, 28), (1015, 70), (1060, 100), (1120, 140), (1140, 200), (1146, 270),
           (1158, 330), (1182, 390), (1198, 450), (1180, 500), (1100, 470), (1040, 450), (1030, 405), (1040, 350), (1015, 290),
           (1012, 230), (985, 185), (945, 160), (910, 140)]
_T_WATTLE = [(1040, 345), (1090, 332), (1165, 360), (1174, 402), (1120, 424), (1060, 428), (1026, 405)]
_T_MAND = [(904, 136), (944, 137), (992, 159), (989, 168), (952, 156), (918, 146)]
_T_BODY = [(1160, 330), (1195, 480), (1205, 640), (1200, 800), (1180, 930), (1120, 1060), (1040, 1160), (930, 1240), (800, 1290),
           (700, 1310), (560, 1300), (520, 1300), (480, 1500), (420, 1640), (280, 1700), (120, 1690), (30, 1600), (60, 1450),
           (170, 1280), (250, 1150), (330, 1010), (430, 860), (560, 720), (700, 600), (820, 510), (940, 440), (1040, 400)]
_T_WING = [(300, 1000), (560, 880), (900, 1010), (960, 1150), (760, 1290), (300, 1290), (260, 1260)]
_T_BOX = dict(head=(880, 10, 1240, 520), wattle=(1010, 320, 1190, 440), mand=(896, 128, 1000, 176),
              body=(10, 310, 1230, 1720), wing=(240, 860, 980, 1310))
_T_EYE = (1025, 155)
_T_HINGE = (990, 162)
_T_WPIN = (1085, 345)
_T_NECK = (1105, 455)
_T = {}


def _turkey_pieces():
    if _T:
        return _T
    im = _src("turkey.jpg")
    k = im.width / 1280.0
    a = np.asarray(im, np.float32)
    paper = np.array([233, 224, 200], np.float32)
    far = (np.abs(a - paper).sum(2) > 62) | (a.sum(2) < 520)
    from scipy import ndimage as ndi

    def cut(name, poly, smooth_poly=True, thresh=True):
        m = Image.new("L", im.size, 0)
        pp = catmull(poly + poly[:1], 5) if smooth_poly else poly
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in pp], fill=255)
        keep = np.asarray(m) > 0
        if thresh:
            keep = _biggest(ndi.binary_opening(far & keep, iterations=1))
            keep = ndi.binary_dilation(keep, iterations=1)
        mm = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
        o = im.convert("RGBA")
        o.putalpha(mm)
        return o.crop(tuple(int(v * k) for v in _T_BOX[name]))

    head = cut("head", _T_HEAD)
    # the lower mandible is its own hinged piece: take it off the head
    hm = Image.new("L", im.size, 0)
    ImageDraw.Draw(hm).polygon([(x * k, y * k) for x, y in [(896, 137), (946, 139), (990, 161), (984, 176), (896, 160)]], fill=255)
    hm = hm.crop(tuple(int(v * k) for v in _T_BOX["head"]))
    head.putalpha(ImageChops.subtract(head.getchannel("A"), hm))
    _T.update(head=head, wattle=cut("wattle", _T_WATTLE), mand=cut("mand", _T_MAND, smooth_poly=False),
              body=cut("body", _T_BODY), wing=cut("wing", _T_WING), k=k)
    return _T


@lru_cache(maxsize=64)
def _tpiece(name, s1000):
    p = _turkey_pieces()[name]
    s = s1000 / 1000.0 / _turkey_pieces()["k"]
    return p.resize((max(2, int(p.width * s)), max(2, int(p.height * s))), Image.LANCZOS)


TURKEY_MOODS = ("calm", "wave", "panic", "freak", "gasp", "flap", "frozen")


def turkey_pose(mood="calm", t=0.0):
    """The hinge angles for a mood at time t. Keys: neck, wattle, beak, eye, wing, ruff, shake, blur."""
    s, c = math.sin, math.cos
    if mood == "calm":
        return dict(neck=2 * s(0.8 * t), wattle=4 * s(1.3 * t), beak=0, eye=0, wing=0, ruff=0, shake=0, blur=0)
    if mood == "wave":
        return dict(neck=3 * s(2 * t), wattle=6 * s(3 * t), beak=5, eye=0, wing=58 + 24 * s(7 * t), ruff=0, shake=0, blur=0)
    if mood == "panic":
        return dict(neck=-5 + 5 * s(9 * t), wattle=18 * s(11 * t), beak=13 + 6 * s(13 * t), eye=1, wing=34 + 28 * abs(s(10 * t)),
                    ruff=0.55, shake=1.5, blur=0)
    if mood == "freak":
        return dict(neck=8 * s(14 * t), wattle=38 * s(12 * t - 1), beak=24 + 6 * s(17 * t), eye=1, wing=60 + 34 * s(22 * t),
                    ruff=1, shake=3.2, blur=0)
    if mood == "gasp":
        return dict(neck=-9 + 1.5 * s(6 * t), wattle=10 * s(5 * t), beak=31, eye=1, wing=72 + 4 * s(9 * t), ruff=1, shake=0.8, blur=0)
    if mood == "flap":
        return dict(neck=6 * s(15 * t), wattle=34 * s(13 * t), beak=26 + 5 * s(19 * t), eye=1, wing=62 + 40 * s(40 * t),
                    ruff=1, shake=3.6, blur=1)
    if mood == "frozen":
        return dict(neck=0.8 * s(52 * t), wattle=3.5 * s(46 * t), beak=11, eye=1, wing=0, ruff=1, shake=1.1, blur=0)
    raise ValueError(mood)


_T_PARTS = dict(             # src window (x0, y0, x1, y1), anchor (src), span used for `height`
    full=((-330, -260, 1560, 1790), (640, 900), 1670.0),
    bust=((380, -230, 1700, 860), (1050, 330), 700.0),
    head=((760, -150, 1380, 620), (1050, 260), 480.0),
)


def turkey_sprite(mood="calm", t=0.0, height=300, part="bust", **over):
    """Turkey as a cutout facing LEFT. Returns (RGBA image, (ax, ay)) where (ax, ay) is the anchor inside the
    image: body centre for part='full', the middle of head-and-neck for 'bust', the head for 'head'.
    `height` is the bird's pixel height (crest to tail tip for full, crest to breast for bust, crest to wattle
    for head). Any pose key (neck, wattle, beak, eye, wing, ruff, shake, blur) can be overridden by keyword."""
    P = turkey_pose(mood, t)
    P.update(over)
    win, anchor, span = _T_PARTS[part]
    s = height / span
    s1000 = int(round(s * 1000))
    s = s1000 / 1000.0
    cw, ch = int((win[2] - win[0]) * s), int((win[3] - win[1]) * s)
    cv = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    def S(p):
        return ((p[0] - win[0]) * s, (p[1] - win[1]) * s)

    def L(name, p):
        b = _T_BOX[name]
        return ((p[0] - b[0]) * s, (p[1] - b[1]) * s)

    wing = _tpiece("wing", s1000 if part == "full" else int(s1000 * 0.5))
    ws = s if part == "full" else s * 0.5
    wroot = ((930 - 240) * ws, (1100 - 860) * ws)                    # the wing's shoulder end, in the wing piece
    wflip = wing.transpose(Image.FLIP_LEFT_RIGHT)
    wroot_f = (wflip.width - wroot[0], wroot[1])
    near_root, far_root = ((930, 1100), (1150, 760)) if part == "full" else ((900, 610), (1190, 560))
    ang = P["wing"]

    def lay_wing(far, a, alpha=1.0):
        spr = wflip if far else wing
        if alpha < 1:
            spr = spr.copy()
            spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
        _pin(cv, spr, wroot_f if far else wroot, S(far_root if far else near_root), a if far else -a)

    if part != "head":
        if P["blur"]:
            for da in (-34, -17, 17, 34):
                lay_wing(True, ang + da, 0.33)
        if ang > 4:
            lay_wing(True, ang)
        body = _tpiece("body", s1000)
        if part == "bust":                                   # the bust is cut off the plate along a curve under the shoulders
            body = body.copy()
            bx0, by0 = _T_BOX["body"][:2]
            cutp = [(0, 0), (1300, 0), (1300, 640), (1215, 700), (1120, 742), (1000, 752), (880, 730), (780, 690), (690, 700), (0, 700)]
            mk = Image.new("L", body.size, 0)
            ImageDraw.Draw(mk).polygon([((x - bx0) * s, (y - by0) * s) for x, y in catmull(cutp[3:9], 5)] +
                                       [((x - bx0) * s, (y - by0) * s) for x, y in (cutp[9], cutp[0], cutp[1], cutp[2])], fill=255)
            body.putalpha(ImageChops.multiply(body.getchannel("A"), mk))
        _paste_clip(cv, body, tuple(int(v) for v in S(_T_BOX["body"][:2])))
    # the ruff: cut-paper neck feathers that stand up
    d = ImageDraw.Draw(cv, "RGBA")
    na = math.radians(P["neck"])
    npv = S(_T_NECK)

    def rot_neck(p):                                                  # src point carried by the neck's rotation
        x, y = S(p)
        dx, dy = x - npv[0], y - npv[1]
        return (npv[0] + dx * math.cos(na) + dy * math.sin(na), npv[1] - dx * math.sin(na) + dy * math.cos(na))

    if P["ruff"] > 0.02:
        rr = P["ruff"]
        for q in range(7):
            f = q / 6
            base = rot_neck((1128 + 52 * f, 210 + 250 * f))
            a = math.radians(lerp(-62, 28, f) + 9 * math.sin(t * 31 + q * 1.7) * rr)
            ln = (70 + 46 * math.sin(f * math.pi)) * s * rr
            wd = 15 * s
            tip = (base[0] + ln * math.cos(a), base[1] + ln * math.sin(a))
            nx, ny = -math.sin(a) * wd, math.cos(a) * wd
            mid = (base[0] + ln * 0.45 * math.cos(a), base[1] + ln * 0.45 * math.sin(a))
            poly = [(base[0] - nx * 0.5, base[1] - ny * 0.5), (mid[0] - nx, mid[1] - ny), tip, (mid[0] + nx, mid[1] + ny),
                    (base[0] + nx * 0.5, base[1] + ny * 0.5)]
            d.polygon([(x + 2 * s + 1, y + 3 * s + 1) for x, y in poly], fill=(14, 10, 8, 120))
            d.polygon(poly, fill=(66, 44, 26, 255), outline=(26, 16, 10, 255))
            d.line([mid[0] - nx, mid[1] - ny, tip[0], tip[1]], fill=(186, 138, 56, 255), width=max(1, int(2.4 * s)))
            d.line([base, tip], fill=(24, 14, 8, 255), width=max(1, int(1.2 * s)))
    # head and neck, with beak, eye and wattle worked on the head piece itself
    head = _tpiece("head", s1000).copy()
    hd = ImageDraw.Draw(head, "RGBA")
    beak = P["beak"]
    hinge = L("head", _T_HINGE)
    mand = _tpiece("mand", s1000)
    mh = ((_T_HINGE[0] - _T_BOX["mand"][0]) * s, (_T_HINGE[1] - _T_BOX["mand"][1]) * s)
    if beak > 0.5:
        b = math.radians(beak)
        tipu = L("head", (912, 139))
        dx, dy = (906 - _T_HINGE[0]) * s, (140 - _T_HINGE[1]) * s
        tipl = (hinge[0] + dx * math.cos(b) + dy * math.sin(b), hinge[1] + (-dx) * math.sin(b) + dy * math.cos(b))
        hd.polygon([hinge, tipu, ((tipu[0] + tipl[0]) / 2 + 9 * s, (tipu[1] + tipl[1]) / 2), tipl], fill=(92, 22, 26, 255))
        hd.polygon([hinge, ((tipu[0] + tipl[0]) / 2 + 16 * s, (tipu[1] + tipl[1]) / 2 + 2 * s), tipl], fill=(196, 96, 92, 255))
    _pin(head, mand, mh, hinge, beak)
    if P["eye"] > 0:
        ex, ey = L("head", _T_EYE)
        r = 21 * s * (0.8 + 0.2 * P["eye"])
        hd.ellipse([ex - r - 1.5 * s, ey - r - 1.5 * s, ex + r + 1.5 * s, ey + r + 1.5 * s], fill=(20, 16, 14, 255))
        hd.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(250, 246, 232, 255))
        pr = 6.5 * s
        hd.ellipse([ex - pr - 3 * s, ey - pr, ex + pr - 3 * s, ey + pr], fill=(16, 12, 10, 255))
        hd.ellipse([ex - 6 * s, ey - 5 * s, ex - 3.5 * s, ey - 2.5 * s], fill=(255, 255, 255, 255))
    wat = _tpiece("wattle", s1000)
    wp = ((_T_WPIN[0] - _T_BOX["wattle"][0]) * s, (_T_WPIN[1] - _T_BOX["wattle"][1]) * s)
    _pin(head, wat, wp, L("head", _T_WPIN), P["wattle"])
    _pin(cv, head, L("head", _T_NECK), npv, P["neck"])
    if part != "head":
        if P["blur"]:
            for da in (-34, -17, 17, 34):
                lay_wing(False, ang + da, 0.33)
        if ang > 4:
            lay_wing(False, ang)
    ax, ay = S(anchor)
    sh = P["shake"] * max(0.4, s * 2)
    return cv, (ax - sh * math.sin(47 * t), ay - sh * 0.7 * math.cos(53 * t))


def turkey(ink, cx, cy, height=300, mood="calm", t=0.0, part="bust", flip=False, alpha=1.0, shadow=0.0, angle=0.0, **over):
    """Draw Turkey with his anchor at (cx, cy). Faces left unless flip. See turkey_sprite."""
    spr, (ax, ay) = turkey_sprite(mood, t, height, part, **over)
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        ax = spr.width - ax
    ox, oy = spr.width / 2 - ax, spr.height / 2 - ay
    if angle:
        a = math.radians(angle)
        ox, oy = ox * math.cos(a) + oy * math.sin(a), -ox * math.sin(a) + oy * math.cos(a)
    put(ink, spr, cx + ox, cy + oy, angle=angle, alpha=alpha, shadow=shadow)


def turkey_reflection(ink, cx=None, cy=None, height=250, mood="freak", t=0.0, alpha=0.6, clip=(PORT_C, PORT_R), part="bust", **over):
    """Turkey's reflection lying on the inside of the glass (faces right, pale, see-through), clipped to the glass.
    Draw it after the river and before seat_frame. Default place is STAGE['reflection']."""
    cx = STAGE["reflection"][0] if cx is None else cx
    cy = STAGE["reflection"][1] if cy is None else cy
    spr, (ax, ay) = turkey_sprite(mood, t, height, part, **over)
    spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    ax = spr.width - ax
    a = np.asarray(spr, np.float32).copy()
    a[..., :3] = a[..., :3] * 0.72 + np.array([244, 226, 170], np.float32) * 0.34        # lamp-lit, washed by the glass
    hh = a.shape[0]
    a[..., 3] *= np.clip((hh * 0.9 - np.arange(hh)) / (hh * 0.3), 0, 1)[:, None]         # a reflection thins out downward
    lay = Image.new("RGBA", (ink.w, ink.h), (0, 0, 0, 0))
    lay.paste(_img(a).convert("RGBA") if False else Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), (int(cx - ax), int(cy - ay)))
    if clip:
        (px, py), r = clip
        m = Image.new("L", (ink.w, ink.h), 0)
        ImageDraw.Draw(m).ellipse([px - r, py - r, px + r, py + r], fill=255)
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m))
    ink.paste(lay, (0, 0), alpha)


# Trout
_TR = {}


def _trout_base():
    if _TR:
        return _TR
    im = _src("trout.png")
    a = np.asarray(im, np.float32)
    paper = np.median(np.concatenate([a[:20].reshape(-1, 3), a[-20:].reshape(-1, 3)]), axis=0)
    m = _biggest(np.abs(a - paper).sum(2) > 38)
    al = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 0 if v < 120 else min(255, (v - 120) * 4))
    box = al.getbbox()
    t = im.convert("RGBA")
    t.putalpha(al)
    k = im.width / 960.0
    _TR.update(img=t.crop(box), eye=((127 * k - box[0]) / (box[2] - box[0]), (324 * k - box[1]) / (box[3] - box[1])),
               eye_r=13.5 * k / (box[2] - box[0]))
    return _TR


def _flex(spr, phase, amp):
    a = np.asarray(spr)
    h, w = a.shape[:2]
    x = np.arange(w) / w
    dy = (amp * (x ** 1.8) * np.sin(phase - 2.6 * x)).astype(np.int32)
    yy = np.arange(h)[:, None] - dy[None, :]
    ok = (yy >= 0) & (yy < h)
    out = a[np.clip(yy, 0, h - 1), np.arange(w)[None, :]]
    out[~ok] = 0
    return Image.fromarray(out, "RGBA")


@lru_cache(maxsize=256)
def _trout_cached(length, phase_q, amp_q, lid_q, roll_q, belly):
    B = _trout_base()
    src = B["img"]
    pad = int(length * 0.12)
    w = length
    h = int(w * src.height / src.width)
    im = Image.new("RGBA", (w, h + 2 * pad), (0, 0, 0, 0))
    im.paste(src.resize((w, h), Image.LANCZOS), (0, pad))
    d = ImageDraw.Draw(im, "RGBA")
    ex, ey, er = B["eye"][0] * w, B["eye"][1] * h + pad, max(2.0, B["eye_r"] * w)
    if roll_q is not None:
        d.ellipse([ex - er * 1.25, ey - er * 1.25, ex + er * 1.25, ey + er * 1.25], fill=(246, 242, 226, 255), outline=(24, 20, 14, 255))
        a = math.radians(roll_q)
        px, py = ex + er * 0.55 * math.sin(a), ey - er * 0.55 * math.cos(a)
        d.ellipse([px - er * 0.5, py - er * 0.5, px + er * 0.5, py + er * 0.5], fill=(14, 12, 10, 255))
    if lid_q > 0:
        lid = lid_q / 10.0
        r = er * 1.22
        m = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(m)
        md.ellipse([ex - r, ey - r, ex + r, ey + r], fill=255)
        md.rectangle([ex - r - 2, ey - r + 2 * r * lid, ex + r + 2, ey + r + 2], fill=0)
        im.paste(Image.new("RGBA", im.size, (88, 86, 54, 255)), (0, 0), m)
        d = ImageDraw.Draw(im, "RGBA")
        yl = ey - r + 2 * r * lid
        hw = math.sqrt(max(0.0, r * r - (yl - ey) ** 2))
        d.line([ex - hw, yl, ex + hw, yl], fill=(24, 22, 14, 255), width=max(1, int(er * 0.3)))     # the flat, fed-up lid edge
    if amp_q:
        im = _flex(im, phase_q / 16.0 * 2 * math.pi, amp_q * length / 420.0)
    if belly:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im


def trout_sprite(length=220, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False):
    """One brook trout as a cutout facing LEFT, `length` px long. phase (radians) and amp bend the tail (amp 0 = rigid).
    lid 0..1 lowers a flat cut-paper eyelid (0.45 = unamused, 0.8 = dozing). eye_roll = degrees (0 up, clockwise)
    swaps in a white rolling eye. belly_up turns it over."""
    ph = int(round((phase % (2 * math.pi)) / (2 * math.pi) * 16)) % 16
    roll = None if eye_roll is None else int(round(eye_roll / 15.0) * 15) % 360
    return _trout_cached(int(length), ph, int(round(amp)), int(round(clamp(lid) * 10)), roll, bool(belly_up))


def trout(ink, cx, cy, length=220, angle=0.0, flip=False, phase=0.0, amp=8.0, lid=0.0, eye_roll=None, belly_up=False,
          alpha=1.0, shadow=0.0):
    """Draw a trout centred at (cx, cy). Faces left; flip=True faces right. angle degrees counter-clockwise."""
    spr = trout_sprite(length, phase, amp, lid, eye_roll, belly_up)
    put(ink, spr, cx, cy, angle=angle, flip=flip, alpha=alpha, shadow=shadow, shadow_off=(4, 6), shadow_blur=4)


def clock_xy(c, r, clock_deg):
    """Point on a circle by clock angle: 0 = twelve o'clock, 90 = three, increasing CLOCKWISE."""
    a = math.radians(clock_deg)
    return (c[0] + r * math.sin(a), c[1] - r * math.cos(a))


def trout_on_circle(ink, c, r, clock_deg, length=150, **kw):
    """A trout travelling CLOCKWISE round centre c at radius r, now at clock angle clock_deg (0 = twelve o'clock).
    It heads along the tangent, the right way up for its direction (unless belly_up). Returns its (x, y)."""
    x, y = clock_xy(c, r, clock_deg)
    a = math.radians(clock_deg)
    dx, dy = math.cos(a), math.sin(a)                 # clockwise tangent, screen coords
    phi = math.degrees(math.atan2(dy, dx))
    if dx >= 0:
        trout(ink, x, y, length, angle=-phi, flip=True, **kw)
    else:
        trout(ink, x, y, length, angle=-(phi - 180), flip=False, **kw)
    return x, y


# -------------------------------------------------------------- the pencil page ---

_LET = {
    "h": [[(0, 0), (0.02, 1)], [(0.02, 0.62), (0.2, 0.45), (0.38, 0.56), (0.4, 1)]],
    "a": [[(0.4, 0.55), (0.2, 0.45), (0.03, 0.65), (0.05, 0.92), (0.22, 1), (0.4, 0.8), (0.4, 0.5), (0.43, 1)]],
    "v": [[(0, 0.45), (0.2, 1), (0.4, 0.45)]],
    "e": [[(0.03, 0.75), (0.38, 0.7), (0.33, 0.5), (0.15, 0.45), (0.02, 0.7), (0.1, 0.97), (0.38, 0.95)]],
    "r": [[(0.02, 0.45), (0.04, 1)], [(0.04, 0.66), (0.18, 0.47), (0.36, 0.5)]],
    "y": [[(0, 0.45), (0.2, 0.95)], [(0.4, 0.45), (0.2, 0.95), (0.05, 1.4)]],
    "f": [[(0.4, 0.1), (0.25, 0), (0.15, 0.2), (0.15, 1)], [(0, 0.5), (0.35, 0.48)]],
    "u": [[(0, 0.45), (0.03, 0.85), (0.18, 1), (0.36, 0.8), (0.38, 0.45), (0.4, 1)]],
    "n": [[(0.02, 0.45), (0.03, 1)], [(0.03, 0.66), (0.2, 0.45), (0.37, 0.58), (0.4, 1)]],
}


def _word(word, x, y, size, slope=-0.1, seed=0):
    """Pencil strokes for a word. (x, y) = left end of the baseline top; size = letter height. Units: any."""
    rs = random.Random(seed)
    out, cx = [], x
    for ch in word:
        sc = size * rs.uniform(0.88, 1.1)
        dy = rs.uniform(-0.06, 0.06) * size + (cx - x) * slope
        for st in _LET[ch]:
            out.append([(cx + px * sc * 0.95 + py * sc * 0.08, y + dy + py * sc) for px, py in st])
        cx += sc * 0.56
    return out


def _c2n(pts):                 # traced in the pixels of a 1500x1400 enlargement of the ring -> ring units (inner radius = 1)
    return [((x - 735) / 560.0, (y - 705) / 560.0) for x, y in pts]


def _build_pilot():
    G = []

    def add(group, pts, weight=1.0, curve=True, per=5):
        pts = _c2n(pts)
        if curve and len(pts) > 2:
            pts = catmull(pts, per)
        G.append(dict(group=group, pts=pts, weight=weight))

    # the upper fish
    add("fish1", [(455, 592), (462, 545), (505, 502), (590, 478), (680, 470), (760, 488), (818, 512), (872, 548), (935, 602)], 1.25)
    add("fish1", [(457, 596), (500, 622), (562, 652), (632, 672), (702, 663), (772, 630), (832, 580), (868, 548)], 1.25)
    add("fish1", [(498, 518), (478, 506), (458, 522), (462, 546), (484, 552)], 1.0)
    add("fish1", [(520, 566), (508, 547), (488, 550), (480, 570), (492, 588), (512, 584), (520, 566)], 1.1)
    add("fish1", [(498, 566), (503, 572), (498, 574), (496, 568)], 1.5)
    add("fish1", [(462, 598), (480, 611), (506, 607)], 1.0)
    add("fish1", [(816, 514), (866, 482), (916, 456), (928, 520), (936, 602)], 1.2)
    for k, (a_, b_) in enumerate([((846, 512), (922, 470)), ((856, 530), (926, 500)), ((866, 546), (930, 535)), ((880, 560), (932, 572)),
                                  ((900, 480), (912, 590))]):
        add("fish1", [a_, b_], 0.75, curve=False)
    # the bubble and its words
    add("bubble", [(522, 398), (462, 372), (432, 318), (452, 262), (520, 228), (610, 220), (672, 248), (692, 300), (668, 352),
                   (610, 388), (588, 402)], 0.95)
    add("bubble", [(522, 398), (528, 440), (520, 462), (540, 474), (562, 462), (560, 430), (588, 402)], 0.95)
    for wd, x, y, sz, sd in (("haha", 488, 262, 40, 1), ("verry", 452, 314, 38, 2), ("funny", 478, 366, 40, 3)):
        for st in _word(wd, x, y, sz, slope=-0.07, seed=sd):
            G.append(dict(group="bubble", pts=_c2n(st) if False else [((px - 735) / 560.0, (py - 705) / 560.0) for px, py in st], weight=0.9))
    # the bell and its twig
    add("bell", [(820, 332), (812, 266), (836, 265), (842, 330)], 1.0)
    add("bell", [(868, 348), (872, 326), (890, 322), (896, 340), (884, 352)], 0.9)
    add("bell", [(852, 366), (880, 350), (906, 366), (906, 394), (936, 402), (926, 416), (860, 420), (810, 418), (804, 404), (832, 396),
                 (836, 372), (852, 366)], 1.1)
    add("bell", [(872, 420), (866, 438), (860, 452)], 1.0)
    add("bell", [(842, 330), (890, 308), (940, 300), (990, 330), (1040, 352), (1092, 356), (1152, 350)], 0.9)
    add("bell", [(896, 340), (950, 330), (1000, 360), (1050, 386), (1100, 380), (1162, 360)], 0.9)
    # weed at the right rim
    add("weed_r", [(1252, 822), (1200, 830), (1232, 850), (1150, 870), (1192, 890), (1130, 910), (1162, 930), (1116, 950), (1150, 975),
                   (1106, 1000), (1132, 1022), (1150, 1056)], 0.85)
    # the lower fish
    add("fish2", [(786, 926), (814, 880), (860, 840), (930, 800), (1010, 770), (1090, 756), (1160, 752)], 1.2)
    add("fish2", [(786, 926), (830, 946), (900, 951), (970, 945), (1040, 915), (1100, 860), (1140, 800), (1162, 760)], 1.2)
    add("fish2", [(848, 850), (832, 824), (814, 838), (820, 858), (838, 862)], 1.0)
    add("fish2", [(874, 880), (862, 864), (844, 866), (838, 884), (850, 898), (868, 896), (874, 880)], 1.1)
    add("fish2", [(854, 880), (858, 885), (853, 887)], 1.5)
    add("fish2", [(800, 915), (815, 926), (833, 918)], 1.0)
    add("fish2", [(1160, 752), (1176, 700), (1214, 672), (1226, 722), (1234, 776), (1192, 778), (1162, 766)], 1.15)
    for a_, b_ in [((1172, 748), (1210, 690)), ((1182, 762), (1222, 720)), ((1196, 772), (1230, 756))]:
        add("fish2", [a_, b_], 0.75, curve=False)
    for a_, b_ in [((900, 832), (1000, 792)), ((960, 818), (1070, 778)), ((1030, 800), (1140, 768)), ((1000, 932), (1080, 880)),
                   ((1040, 900), (1110, 840))]:
        add("fish2", [a_, b_], 0.6, curve=False)
    # weed at the lower left
    add("weed_l", [(300, 1076), (304, 1000), (344, 986), (358, 908), (384, 900), (394, 960), (414, 906), (434, 950), (454, 916),
                   (474, 966), (500, 926), (520, 986), (544, 946), (560, 990), (580, 950), (572, 1000), (552, 1010)], 0.85, per=6)
    add("weed_l", [(552, 1010), (546, 1060), (556, 1110), (540, 1150), (548, 1202)], 0.75)
    # a fixed hand-wobble: the child's line is not smooth
    rs = random.Random(13)
    for st in G:
        st["pts"] = [(x + rs.gauss(0, 0.0035), y + rs.gauss(0, 0.0035)) for x, y in st["pts"]]
        st["len"] = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(st["pts"], st["pts"][1:])) + 0.02
    return G


PILOT_STROKES = _build_pilot()          # [{group, pts (ring units: centre 0,0, inner radius 1, y down), weight, len}]
PILOT_GROUPS = ["fish1", "bubble", "bell", "weed_r", "fish2", "weed_l"]          # the order the pencil goes: clockwise
PILOT_TIMES = {"fish1": (0.15, 2.2), "bubble": (2.3, 4.0), "bell": (4.1, 5.4), "weed_r": (5.5, 6.2), "fish2": (6.3, 8.0),
               "weed_l": (8.1, 8.75)}                                           # the board's A1 to A6, in seconds
PILOT_PLACES = dict(        # where things sit in the drawing, ring units (multiply by r, add the centre)
    fish1=(-0.07, -0.24), fish1_len=0.86, fish1_angle=-4.0,
    fish2=(0.49, 0.24), fish2_len=0.80, fish2_angle=20.0,
    bubble=(-0.31, -0.69), bubble_tail=(-0.35, -0.42), bell=(0.24, -0.60), bell_top=(0.16, -0.78),
    weed_r=(0.80, 0.40), weed_l=(-0.48, 0.52),
)


def ring_xy(u, v, c=PORT_C, r=PORT_R):
    """Ring units -> screen."""
    return (c[0] + u * r, c[1] + v * r)


def _pencil_line(d, pts, weight, sc, alpha=1.0, color=None):
    col = color or PAL["pencil"]
    w = max(1, int(round(1.9 * weight * sc)))
    a = int(clamp(175 + 45 * weight, 0, 245) * alpha)
    d.line(pts, fill=col + (a,), width=w, joint="curve")
    if weight >= 1.0 and len(pts) > 1:                        # a second, lighter pass: graphite is never one clean line
        d.line([(x + 0.7 * sc, y + 0.5 * sc) for x, y in pts], fill=col + (int(a * 0.35),), width=1)


def pilot_drawing(ink, done=1.0, c=PORT_C, r=PORT_R, alpha=1.0, color=None):
    """The pilot's pencil drawing inside the ring. `done` is 0..1 of the whole drawing (by pencil travel), or a
    dict {group: 0..1}. Returns (tip_xy, pen_down): where the pencil point is now (None before the first stroke)."""
    sc = r / 212.0
    tip, down = None, False
    if not isinstance(done, dict):
        tot = sum(s["len"] for s in PILOT_STROKES)
        want, acc, fr = done * tot, 0.0, {}
        per = {}
        for s in PILOT_STROKES:
            per.setdefault(s["group"], 0.0)
            per[s["group"]] += s["len"]
        for g in PILOT_GROUPS:
            fr[g] = clamp((want - acc) / per[g])
            acc += per[g]
        done = fr
    for g in PILOT_GROUPS:
        f = done.get(g, 0.0)
        if f <= 0:
            continue
        strokes = [s for s in PILOT_STROKES if s["group"] == g]
        want = f * sum(s["len"] for s in strokes)
        for s in strokes:
            if want <= 0:
                break
            pts = [ring_xy(u, v, c, r) for u, v in s["pts"]]
            if want >= s["len"]:
                _pencil_line(ink.d, pts, s["weight"], sc, alpha, color)
                tip, down = pts[-1], False
            else:
                go, acc, out = want / s["len"] * (s["len"] - 0.02), 0.0, [pts[0]]
                for (u0, v0), (u1, v1), p1 in zip(s["pts"], s["pts"][1:], pts[1:]):
                    seg = math.hypot(u1 - u0, v1 - v0)
                    if acc + seg >= go:
                        k = (go - acc) / max(seg, 1e-9)
                        out.append(lerp2(out[-1], p1, clamp(k)))
                        break
                    out.append(p1)
                    acc += seg
                if len(out) > 1:
                    _pencil_line(ink.d, out, s["weight"], sc, alpha, color)
                tip, down = out[-1], True
            want -= s["len"]
    return tip, down


def pilot_page(ink, t, c=PORT_C, r=PORT_R, alpha=1.0):
    """The drawing as it stands t seconds into the pilot's page, timed as the board's A1 to A6 (PILOT_TIMES).
    Returns (tip_xy, pen_down) so the caller can lay pencil(ink, tip, lift=0 if pen_down else 1)."""
    done, cur = {}, None
    for g in PILOT_GROUPS:
        a, b = PILOT_TIMES[g]
        done[g] = ramp(t, a, b)
        if a <= t < b:
            cur = g
    tip, down = pilot_drawing(ink, done, c, r, alpha)
    if cur is None:                      # between groups the pencil travels, lifted, to the next start (clockwise order)
        down = False
        nxt = [g for g in PILOT_GROUPS if PILOT_TIMES[g][0] > t]
        prev = [g for g in PILOT_GROUPS if PILOT_TIMES[g][1] <= t]
        if nxt:
            g = nxt[0]
            start = ring_xy(*[s for s in PILOT_STROKES if s["group"] == g][0]["pts"][0], c, r)
            if prev:
                a = PILOT_TIMES[prev[-1]][1]
                tip = lerp2(tip, start, ease(t, a, PILOT_TIMES[g][0]))
            else:
                tip = start
    return tip, down


@lru_cache(maxsize=4)
def _pencil_spr(length):
    L, wd = length, max(8, int(length * 0.055))
    im = Image.new("RGBA", (L, wd * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    y0, y1 = wd, wd * 2
    cone = int(L * 0.12)
    d.polygon([(0, (y0 + y1) / 2), (cone, y0), (cone, y1)], fill=(226, 196, 150, 255), outline=(120, 96, 66, 255))
    d.polygon([(0, (y0 + y1) / 2), (cone * 0.3, (y0 + y1) / 2 - wd * 0.15), (cone * 0.3, (y0 + y1) / 2 + wd * 0.15)], fill=(52, 52, 58, 255))
    for k, col in enumerate([(232, 178, 44), (246, 204, 70), (206, 150, 30)]):          # three faces of the hexagon
        d.rectangle([cone, y0 + k * wd / 3, L * 0.86, y0 + (k + 1) * wd / 3], fill=col + (255,))
    d.line([cone, y0, L * 0.86, y0], fill=(120, 84, 16, 255))
    d.line([cone, y1, L * 0.86, y1], fill=(120, 84, 16, 255))
    for q in range(4):
        x = cone + q * 1.2
        d.line([x, y0 + (q % 2) * wd / 3, x + 3, y0 + ((q + 1) % 3) * wd / 3], fill=(226, 196, 150, 255))
    d.rectangle([L * 0.86, y0 - 1, L * 0.93, y1 + 1], fill=(170, 176, 180, 255), outline=(90, 96, 100, 255))
    for q in range(3):
        x = L * 0.87 + q * L * 0.02
        d.line([x, y0 - 1, x, y1 + 1], fill=(108, 114, 118, 255))
    d.rounded_rectangle([L * 0.93, y0, L - 1, y1], radius=wd // 3, fill=(214, 122, 120, 255), outline=(140, 70, 70, 255))
    d.line([L * 0.2, y0 + wd * 0.2, L * 0.84, y0 + wd * 0.2], fill=(255, 236, 150, 200))
    return im


def pencil(ink, tip, angle=52.0, lift=0.0, length=250, alpha=1.0):
    """A real pencil (cut card, with its shadow) whose point is at `tip`. angle = degrees the barrel rises to the
    right of the point (52 is a right-hander's slant). lift 0..1 raises it off the paper (the shadow parts)."""
    if tip is None:
        return
    spr = _pencil_spr(int(length))
    a = math.radians(angle)
    lx, ly = tip[0] - 4 * lift, tip[1] - 14 * lift
    cx, cy = lx + math.cos(a) * length / 2, ly - math.sin(a) * length / 2
    put(ink, spr, cx, cy, angle=angle, alpha=alpha, shadow=0.8, shadow_off=(int(5 + 12 * lift), int(6 + 16 * lift)), shadow_blur=3 + int(4 * lift))


# --------------------------------------------------------------- dice, buttons ---

_PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
         5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


@lru_cache(maxsize=128)
def _die_spr(n, size, style, lit_q):
    lit = lit_q / 10.0
    pad = max(3, size // 6)
    S = size + 2 * pad
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    box = [pad, pad, pad + size, pad + size]
    rad = size * 0.2
    if style == "print":                       # the small printed face on the worksheet's ring
        col = mix_color((186, 184, 178), PAL["print"], lit)
        d.rounded_rectangle(box, radius=rad, fill=mix_color((236, 234, 228), PAL["sheet"], lit) + (255,), outline=col + (255,), width=max(1, size // 16))
        pr = size * 0.085
        pipc = col
    else:                                      # an ivory die face with weight
        base = mix_color((112, 106, 96), PAL["ivory"], lit)
        d.rounded_rectangle([box[0] + size * 0.05, box[1] + size * 0.09, box[2] + size * 0.05, box[3] + size * 0.09], radius=rad, fill=(10, 8, 6, 110))
        d.rounded_rectangle(box, radius=rad, fill=tuple(int(v * 0.78) for v in base) + (255,))
        d.rounded_rectangle([box[0], box[1], box[2] - size * 0.05, box[3] - size * 0.06], radius=rad, fill=base + (255,))
        d.rounded_rectangle([box[0] + size * 0.07, box[1] + size * 0.06, box[2] - size * 0.2, box[1] + size * 0.2], radius=size * 0.07,
                            fill=(255, 255, 255, int(70 * lit + 20)))
        d.rounded_rectangle(box, radius=rad, outline=(40, 30, 20, 255), width=max(1, size // 22))
        pr = size * 0.095
        pipc = mix_color((60, 56, 50), PAL["pip"], lit)
    cx, cy, g = pad + size / 2, pad + size / 2, size * 0.27
    for px, py in _PIPS[n]:
        x, y = cx + px * g, cy + py * g
        if style != "print":
            d.ellipse([x - pr, y - pr - size * 0.012, x + pr, y + pr - size * 0.012], fill=(255, 255, 255, 90))
        d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=pipc + (255,))
    return im


def die_face(ink, n, x, y, size=44, style="ivory", lit=1.0, angle=0.0, alpha=1.0):
    """Die face n (1..6) centred at (x, y). style 'ivory' (a real die face) or 'print' (the worksheet's little
    printed face). lit 0..1: 1 = bright, 0 = grey and dead (an unwritten bolt)."""
    put(ink, _die_spr(int(n), int(size), style, int(round(clamp(lit) * 10))), x, y, angle=angle, alpha=alpha)


def _glyph_pts(kind, r):
    if kind == "triangle":
        return [(r * math.sin(a), -r * math.cos(a) + r * 0.1) for a in (0, 2 * math.pi / 3, 4 * math.pi / 3)]
    if kind == "square":
        q = r * 0.78
        return [(-q, -q), (q, -q), (q, q), (-q, q)]
    if kind == "hexagon":
        return [(r * math.cos(math.pi / 6 + k * math.pi / 3), r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    if kind == "circle":
        return [(r * 0.92 * math.cos(k * math.pi / 18), r * 0.92 * math.sin(k * math.pi / 18)) for k in range(36)]
    if kind == "cross":
        a, b = r * 0.95, r * 0.3
        pts = [(-b, -a), (b, -a), (b, -b), (a, -b), (a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b)]
        c, s = math.cos(math.pi / 4), math.sin(math.pi / 4)
        return [(x * c - y * s, x * s + y * c) for x, y in pts]
    raise ValueError(kind)


@lru_cache(maxsize=128)
def _button_spr(kind, r, press_q, lit_q):
    press, lit = press_q / 10.0, lit_q / 10.0
    K = 3
    R = r * K
    S = int(R * 2.9)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    c = S / 2
    col = BUTTONS[kind]
    colour = mix_color(mix_color(col, (96, 92, 88), 0.72), col, lit)
    hi = mix_color(colour, (255, 255, 255), 0.45 + 0.25 * lit)
    lo = mix_color(colour, (0, 0, 0), 0.45)
    # the socket in the controller: a dark well with a lit lower lip
    d.ellipse([c - R * 1.3, c - R * 1.3 + R * 0.06, c + R * 1.3, c + R * 1.3 + R * 0.06], fill=(196, 190, 178, 255))
    d.ellipse([c - R * 1.3, c - R * 1.3, c + R * 1.3, c + R * 1.3], fill=(34, 32, 34, 255))
    d.ellipse([c - R * 1.2, c - R * 1.14, c + R * 1.2, c + R * 1.26], fill=(58, 54, 56, 255))
    d.ellipse([c - R * 1.16, c - R * 1.16, c + R * 1.16, c + R * 1.16], fill=(22, 20, 22, 255))
    rise = R * 0.2 * (1 - press)                # how far the cap stands out of the well
    pts = _glyph_pts(kind, R * 0.86)
    d.polygon([(c + x + rise * 0.5, c + y + rise * 1.2) for x, y in pts], fill=(0, 0, 0, 170))            # cast shadow
    for q in range(int(rise) + 1):                                                                           # the cap's side wall
        d.polygon([(c + x, c + y - q + rise * 0.4) for x, y in pts], fill=lo + (255,))
    top = [(c + x, c + y - rise * 0.6) for x, y in pts]
    d.polygon(top, fill=colour + (255,))
    # bevel: a light edge up-left, a dark edge down-right
    n = len(top)
    for i in range(n):
        p0, p1 = top[i], top[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2 - c, (p0[1] + p1[1]) / 2 - c
        l_ = -(mx * 0.6 + my * 0.8) / (R * 0.86)
        d.line([p0, p1], fill=(hi if l_ > 0 else lo) + (int(120 + 135 * min(1, abs(l_))),), width=max(2, int(R * 0.09)))
    if lit > 0.5:
        g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(g).polygon(top, fill=hi + (int(120 * (lit - 0.5) * 2),))
        g = g.filter(ImageFilter.GaussianBlur(R * 0.22))
        im.alpha_composite(g)
        d = ImageDraw.Draw(im, "RGBA")
        d.polygon([(c + (x - c) * 0.5 - R * 0.12, c + (y - c) * 0.5 - R * 0.2) for x, y in top], fill=(255, 255, 255, 46))
    return im.resize((S // K, S // K), Image.LANCZOS)


def button(ink, kind, x, y, r=26, pressed=0.0, lit=1.0, alpha=1.0):
    """One controller button centred at (x, y): kind 'triangle' (green), 'circle' (red), 'cross' (blue),
    'square' (pink) or 'hexagon' (amber). The coloured cap IS the shape, standing in a dark round well.
    pressed 0..1 sinks it; lit 0..1 (0 = dull and grey, 1 = glowing). r = the well's radius is about 1.3 r."""
    put(ink, _button_spr(kind, int(r), int(round(clamp(pressed) * 10)), int(round(clamp(lit) * 10))), x, y, alpha=alpha)


def button_disc(ink, kind, x, y, r=10, alpha=1.0):
    """The small flat mark a pick leaves behind (the red disc that stays on the bell): the button's shape, no well."""
    col = BUTTONS[kind]
    pts = [(x + px + 1, y + py + 2) for px, py in _glyph_pts(kind, r)]
    ink.d.polygon(pts, fill=(20, 10, 8, int(120 * alpha)))
    pts = [(x + px, y + py) for px, py in _glyph_pts(kind, r)]
    ink.d.polygon(pts, fill=col + (int(255 * alpha),), outline=mix_color(col, (0, 0, 0), 0.5) + (int(255 * alpha),))
    ink.d.line(pts[: max(2, len(pts) // 3)], fill=mix_color(col, (255, 255, 255), 0.55) + (int(220 * alpha),), width=max(1, int(r * 0.16)))


def badge(ink, n=13):
    """The porthole number, white on a dark rounded badge, top right corner. Call it last, every frame."""
    x1, y0 = ink.w - 18, 16
    x0, y1 = x1 - 62, y0 + 40
    ink.d.rounded_rectangle([x0 + 2, y0 + 3, x1 + 2, y1 + 3], radius=11, fill=(0, 0, 0, 70))
    ink.d.rounded_rectangle([x0, y0, x1, y1], radius=11, fill=PAL["badge"] + (255,), outline=(70, 70, 80, 255), width=1)
    ink.d.text(((x0 + x1) / 2, (y0 + y1) / 2 - 1), str(n), font=font("sans", 25), fill=PAL["white"] + (255,), anchor="mm")


# ------------------------------------------------------------------ the table ---

@lru_cache(maxsize=2)
def _table_img(with_sheet):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    grain = vnoise((H, W), 420, 7, seed=3, octaves=3) - 0.5
    slow = vnoise((H, W), 300, 120, seed=4, octaves=2) - 0.5
    a = np.ones((H, W, 3), np.float32) * np.array(PAL["table"], np.float32)
    a *= (1 + grain * 0.5 + slow * 0.3)[..., None]
    for x in (318, 652):                                   # the joints between boards
        a[:, x - 1:x + 1] *= 0.6
        a[:, x + 1:x + 3] *= 1.08
    a *= (1.12 - 0.3 * np.hypot((xx - 420) / 700, (yy - 200) / 500))[..., None]
    img = _img(a).convert("RGB")
    if with_sheet:
        sw, sh = 640, 600
        sheet = np.ones((sh, sw, 3), np.float32) * np.array(PAL["sheet"], np.float32)
        sheet *= (0.97 + 0.05 * vnoise((sh, sw), 60, seed=8, octaves=3))[..., None]
        sp = _img(sheet).convert("RGBA").rotate(-1.6, expand=True, resample=Image.BICUBIC)
        shd = _shadow_of(sp, 9, 0.6, (20, 12, 6))
        img = img.convert("RGBA")
        x, y = PORT_C[0] - sp.width // 2, PORT_C[1] - sp.height // 2 + 8
        img.alpha_composite(shd, (x + 7, y + 10)) if False else img.paste(shd, (x + 7, y + 10), shd)
        img.paste(sp, (x, y), sp)
        img = img.convert("RGB")
    return img


def table(ink, sheet=True):
    """The work table: wooden boards and (sheet=True) the worksheet paper lying under the ring at PORT_C.
    Fills the frame. Follow with sheet_ring(ink) to print the ring on the paper."""
    ink.img.paste(_table_img(bool(sheet)), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def bolt_xy(n, c=PORT_C, r=None):
    """Centre of bolt n (1..6): 1 at twelve o'clock, then clockwise (2 at two, 3 at four, 4 at six, 5 at eight,
    6 at ten o'clock). r defaults to the middle of the brass ring."""
    r = (PORT_R + (RING_OUT - PORT_R) * 0.55) if r is None else r
    return clock_xy(c, r, (n - 1) * 60)


def sheet_ring(ink, c=PORT_C, r=PORT_R, alpha=1.0, lit=None):
    """The worksheet's printed ring: a thin double circle (inner radius r) with the six little die faces at
    the six bolt places. lit = optional {n: 0..1} to grey out faces."""
    ro = r * RING_OUT / PORT_R
    col = PAL["print"] + (int(230 * alpha),)
    for rr in (r, ro):
        ink.d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=col, width=2)
    size = int(r * 0.19)
    for n in range(1, 7):
        x, y = clock_xy(c, (r + ro) / 2, (n - 1) * 60)
        die_face(ink, n, x, y, size, "print", 1.0 if lit is None else lit.get(n, 1.0), alpha=alpha)


# --------------------------------------------------------------------- river ---

@lru_cache(maxsize=1)
def _river_planes():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = yy / H
    top, mid, deep = (np.array(PAL[k], np.float32) for k in ("water_top", "water_mid", "water_deep"))
    g = np.where(v[..., None] < 0.45, top + (mid - top) * (v[..., None] / 0.45), mid + (deep - mid) * ((v[..., None] - 0.45) / 0.55))
    wash = vnoise((H, W), 240, 60, seed=21, octaves=3) - 0.5            # brushed, horizontal: painted paper, not a gradient
    blot = vnoise((H, W), 70, seed=22, octaves=3) - 0.5
    g = g * (1 + wash * 0.34 + blot * 0.12)[..., None]
    sh = np.zeros((H, W), np.float32)                                   # light shafts leaning in from upper left
    for x0, wd, gain in ((150, 46, 0.5), (330, 30, 0.34), (520, 58, 0.42), (720, 36, 0.3), (880, 50, 0.26)):
        sh += gain * np.exp(-(((xx - x0 - yy * 0.42) / wd) ** 2)) * np.clip(1.1 - v * 1.25, 0, 1)
    sh *= 0.6 + 0.8 * vnoise((H, W), 30, 200, seed=23)
    g = g + np.array(PAL["shaft"], np.float32) * sh[..., None] * 0.36
    back = _img(g).convert("RGB")
    # far plane: hazed boulders and weed, cut paper seen through water
    far = Image.new("RGBA", (W + 240, H), (0, 0, 0, 0))
    rs = random.Random(5)
    for k in range(9):
        x = -40 + k * 150 + rs.uniform(-30, 30)
        wd, ht = rs.uniform(150, 260), rs.uniform(60, 150)
        pts = [(x + wd * (0.5 + 0.5 * math.cos(a)) + rs.uniform(-8, 8), 470 - ht * math.sin(a) * rs.uniform(0.85, 1.1)) for a in np.linspace(0, math.pi, 12)]
        pts += [(x + wd, 560), (x, 560)]
        pc = _paper_piece(far.size, pts, mix_color(PAL["stone_dk"], PAL["water_mid"], 0.55), seed=40 + k, edge=0.08, grain=0.2)
        far.alpha_composite(pc)
        if k % 2 == 0:
            for q in range(4):
                bx = x + wd * rs.uniform(0.2, 0.8)
                ln = rs.uniform(90, 190)
                lean = rs.uniform(-18, 18)
                bl = [(bx - 7, 470 - ht * 0.7), (bx + lean * 0.5 - 4, 470 - ht * 0.7 - ln * 0.6), (bx + lean, 470 - ht * 0.7 - ln),
                      (bx + lean * 0.5 + 5, 470 - ht * 0.7 - ln * 0.55), (bx + 7, 470 - ht * 0.7)]
                far.alpha_composite(_paper_piece(far.size, catmull(bl + bl[:1], 4), mix_color(PAL["weed_dk"], PAL["water_mid"], 0.5), seed=80 + k * 5 + q, edge=0.06))
    far = far.filter(ImageFilter.GaussianBlur(1.6))
    # bed: gravel floor, pebbles as overlapping pieces
    bed = Image.new("RGBA", (W + 240, 150), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bed, "RGBA")
    n = vnoise((150, W + 240), 80, 20, seed=31, octaves=3)
    edge = (38 + 26 * vnoise((1, W + 240), 160, seed=32, octaves=2)[0]).astype(int)
    ba = np.ones((150, W + 240, 3), np.float32) * np.array((66, 84, 74), np.float32) * (0.75 + 0.5 * n[..., None])
    al = (np.arange(150)[:, None] > edge[None, :]) * 255
    bed = Image.fromarray(np.dstack([np.clip(ba, 0, 255), al]).astype(np.uint8), "RGBA")
    bd = ImageDraw.Draw(bed, "RGBA")
    for k in range(260):
        x, y = rs.uniform(0, W + 240), rs.uniform(42, 150)
        rx = rs.uniform(6, 22) * (0.6 + y / 150)
        ry = rx * rs.uniform(0.45, 0.7)
        col = mix_color(PAL["stone_dk"], PAL["stone_lt"], rs.uniform(0.1, 0.8))
        col = mix_color(col, PAL["water_deep"], 0.35)
        bd.ellipse([x - rx + 2, y - ry + 3, x + rx + 2, y + ry + 3], fill=(8, 20, 22, 120))
        bd.ellipse([x - rx, y - ry, x + rx, y + ry], fill=col + (255,), outline=(14, 30, 30, 200))
        bd.arc([x - rx * 0.8, y - ry * 0.8, x + rx * 0.5, y + ry * 0.3], 190, 300, fill=mix_color(col, (230, 240, 220), 0.45) + (200,), width=1)
    return back, far, bed


def river(ink, t=0.0, planes=("back", "far", "bed", "motes"), shift=0.0, calm=False):
    """The river as background planes of painted and cut paper, filling the frame: 'back' (water and light shafts),
    'far' (hazed boulders and weed), 'bed' (gravel floor along the bottom), 'motes' (drifting specks).
    shift moves the far planes sideways in px (parallax). calm=True stops the motes dead (bolt 3)."""
    back, far, bed = _river_planes()
    if "back" in planes:
        ink.img.paste(back, (0, 0))
    if "far" in planes:
        ink.img.paste(far, (int(-120 + shift * 0.35), 0), far)
    if "bed" in planes:
        ink.img.paste(bed, (int(-120 + shift * 0.8), H - 150), bed)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if "motes" in planes:
        rs = random.Random(77)
        tt = 0.0 if calm else t
        for k in range(70):
            x0, y0, sp, ph = rs.uniform(0, W), rs.uniform(0, H), rs.uniform(4, 14), rs.uniform(0, 6.28)
            x = (x0 + sp * tt) % W
            y = y0 + 5 * math.sin(ph + tt * 0.7)
            r = rs.uniform(0.8, 2.2)
            ink.d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 240, 214, int(rs.uniform(50, 130))))


def weed(ink, x, base_y, height=160, lean=0.0, t=0.0, seed=0, n=5, spread=34, sway=1.0, dark=0.0, alpha=1.0):
    """A clump of torn-paper ribbon weed rooted at (x, base_y). lean in degrees, positive = to the RIGHT
    (drive it from a Follower of the current). sway 0 stops its own idle movement dead. dark 0..1 for far clumps."""
    rs = random.Random(seed * 131 + 9)
    blades = []
    for k in range(n):
        bx = x + (k - (n - 1) / 2) * spread / max(1, n - 1) * 2 + rs.uniform(-4, 4)
        ln = height * rs.uniform(0.6, 1.0)
        wd = rs.uniform(7, 13) * (height / 160) ** 0.5
        own = rs.uniform(-9, 9)
        ph = rs.uniform(0, 6.28)
        blades.append((bx, ln, wd, own, ph, rs.random()))
    blades.sort(key=lambda b: b[5])
    for bx, ln, wd, own, ph, shade in blades:
        a = math.radians(lean + own)
        pts_l, pts_r, mid = [], [], []
        m = 10
        for q in range(m + 1):
            f = q / m
            bend = a * f ** 1.4 + math.radians(6) * sway * math.sin(t * 1.4 + ph + f * 3.0) * f
            cx = bx + math.sin(bend) * ln * f + 5 * math.sin(f * 7 + ph) * f * (1 if not sway else 1)
            cy = base_y - math.cos(bend) * ln * f
            w_ = wd * (1 - f ** 2.2) * (0.75 + 0.25 * math.sin(f * 9 + ph))
            pts_l.append((cx - w_ / 2, cy))
            pts_r.append((cx + w_ / 2, cy))
            mid.append((cx, cy))
        poly = pts_l + pts_r[::-1]
        col = mix_color(mix_color(PAL["weed_dk"], PAL["weed"], shade), PAL["water_deep"], dark * 0.6)
        A = int(255 * alpha)
        ink.d.polygon([(px + 3, py + 3) for px, py in poly], fill=(6, 22, 20, int(90 * alpha)))
        ink.d.polygon(poly, fill=col + (A,))
        ink.d.line(pts_l, fill=mix_color(col, PAL["weed_lt"], 0.75 - dark * 0.4) + (A,), width=2)      # the torn, paler edge
        ink.d.line(pts_r, fill=mix_color(col, (0, 20, 16), 0.5) + (A,), width=1)
        ink.d.line(mid, fill=mix_color(col, (0, 20, 16), 0.3) + (int(150 * alpha),), width=1)


def ripple_rings(ink, c, radii, alpha=1.0, squash=0.42, color=(236, 246, 232), width=3):
    """Rings of ripples leaving the bell mouth at c. radii = list of px radii (grow them in time; shrink them to
    take the sound back). Rings are flattened ellipses (squash) with a bright upper and a dark lower lip."""
    for r in radii:
        if r <= 1:
            continue
        a = alpha * clamp(1.25 - r / 520.0)
        if a <= 0:
            continue
        box = [c[0] - r, c[1] - r * squash, c[0] + r, c[1] + r * squash]
        ink.d.ellipse([box[0], box[1] + 3, box[2], box[3] + 3], outline=(8, 40, 44, int(90 * a)), width=width + 1)
        ink.d.ellipse([box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2], outline=color + (int(50 * a),), width=width + 4)
        ink.d.ellipse(box, outline=color + (int(150 * a),), width=width)


def bubbles(ink, origin, t, t0=0.0, n=7, rise=120.0, curl=70.0, size=6.0, frozen_at=None, alpha=1.0):
    """A string of bubbles that left `origin` at time t0 and climbs on a CLOCKWISE curl (up, then over to the right).
    frozen_at = a time after which they hang where they are (bolt 3)."""
    tt = (frozen_at if frozen_at is not None and t > frozen_at else t) - t0
    if tt <= 0:
        return
    rs = random.Random(int(t0 * 1000) + 3)
    for k in range(n):
        age = tt - k * 0.09
        if age <= 0:
            continue
        f = clamp(age / 2.2)
        th = f * math.pi * 0.75                               # clockwise from "going up"
        x = origin[0] + curl * (1 - math.cos(th)) + rs.uniform(-4, 4)
        y = origin[1] - rise * math.sin(th) * (0.6 + 0.4 * f) - rise * 0.35 * f
        r = size * rs.uniform(0.5, 1.15) * (0.7 + 0.5 * f)
        a = alpha * (1 - f) ** 0.5
        if a <= 0.02:
            continue
        ink.d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 240, 232, int(46 * a)), outline=(240, 250, 244, int(230 * a)), width=2)
        ink.d.arc([x - r * 0.6, y - r * 0.6, x + r * 0.3, y + r * 0.3], 180, 280, fill=(255, 255, 255, int(255 * a)), width=2)


# --------------------------------------------------------- the arch and its bell ---

_ARCH_DESIGN = (520, 420)        # design pixels: feet on the bottom edge, crown near the top


@lru_cache(maxsize=8)
def _arch_parts(width):
    """left pillar, lintel, right pillar: boulders of torn green-grey paper, each its own piece with its own
    light, hatching and shadow, capped with torn moss."""
    dw, dh = _ARCH_DESIGN
    K = 2
    Wd, Hd = int(dw * K), int(dh * K)
    rs = random.Random(29)
    cx, cy = dw / 2, dh + 26
    N = 11
    rad = [66, 58, 52, 56, 50, 60, 51, 55, 52, 59, 68]
    stones = []
    for i in range(N):
        a = math.pi * (1 - (i + 0.15 + 0.7 * (i / (N - 1))) / (N - 0.15))
        a = math.pi * (1 - i / (N - 1)) * 0.94 + math.pi * 0.03
        r = rad[i]
        px = cx + math.cos(a) * 196 + rs.uniform(-5, 5)
        py = cy - math.sin(a) * 322 + rs.uniform(-5, 5)
        pts = []
        m = 11
        rot = rs.uniform(0, 6.28)
        for q in range(m):
            th = rot + 2 * math.pi * q / m
            rr = r * rs.uniform(0.84, 1.12) * (1.0 + 0.1 * math.cos(2 * (th - a)))
            pts.append((px + rr * math.cos(th), py + rr * math.sin(th) * 0.9))
        stones.append(dict(i=i, c=(px, py), r=r, a=a, pts=catmull(pts + pts[:1], 5)))
    groups = (("left", (0, 1, 2, 3)), ("lintel", (4, 6, 5)), ("right", (10, 9, 8, 7)))
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    parts = {}
    for name, idx in groups:
        im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
        for i in idx:
            st = stones[i]
            pts = [(x * K, y * K) for x, y in st["pts"]]
            px, py, r = st["c"][0] * K, st["c"][1] * K, st["r"] * K
            col = mix_color(PAL["stone"], (PAL["stone_dk"], PAL["stone_lt"], (120, 118, 100))[i % 3], 0.25 + 0.25 * rs.random())
            pc = _paper_piece((Wd, Hd), pts, col, seed=100 + i, edge=0.22, grain=0.2)
            a = np.asarray(pc, np.float32).copy()
            lx, ly = (xx - px) / r, (yy - py) / r
            light = 1.0 - 0.34 * (lx * 0.55 + ly * 0.85)                      # lit from upper left, like the brass
            light -= 0.3 * np.clip(np.hypot(lx - 0.2, ly - 0.3) - 0.62, 0, 1)     # the under-side falls away
            speck = (vnoise((Hd, Wd), 5, seed=200 + i) > 0.72) * 0.09
            a[..., :3] *= (light - speck)[..., None]
            pc = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
            # engraver's hatching on the shaded side, cut with the piece
            hl = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
            hd_ = ImageDraw.Draw(hl)
            for q in range(-12, 13):
                o = q * 5 * K
                hd_.line([px + o - r, py + o * 0.2 + r * 1.2, px + o + r, py + o * 0.2 - r * 0.8], fill=(30, 40, 36, 90), width=max(1, K // 2))
            hm = Image.new("L", (Wd, Hd), 0)
            ImageDraw.Draw(hm).ellipse([px - r * 0.2, py + r * 0.05, px + r * 1.3, py + r * 1.3], fill=255)
            hm = ImageChops.multiply(hm.filter(ImageFilter.GaussianBlur(r * 0.12)), pc.getchannel("A"))
            hl.putalpha(ImageChops.multiply(hl.getchannel("A"), hm))
            im.alpha_composite(_shadow_of(pc, 5 * K, 0.7, (8, 18, 16)), (int(3 * K), int(6 * K)))
            im.alpha_composite(pc)
            im.alpha_composite(hl)
            d = ImageDraw.Draw(im, "RGBA")
            p0 = pts[rs.randrange(len(pts))]                                   # one crack
            mid = (lerp(p0[0], px, 0.6) + rs.uniform(-8, 8) * K, lerp(p0[1], py, 0.6) + rs.uniform(-8, 8) * K)
            d.line([p0, lerp2(p0, mid, 0.6), mid, (mid[0] + rs.uniform(-12, 12) * K, mid[1] + rs.uniform(4, 14) * K)], fill=(38, 46, 42, 130), width=max(1, K // 2))
            # moss: torn green paper over the stone's upper, outer shoulder
            ox, oy = math.cos(st["a"]) * 0.75, -math.sin(st["a"]) * 0.6 - 0.75
            on = math.hypot(ox, oy)
            ox, oy = ox / on, oy / on
            amt = 0.5 if i in (0, 10) else 0.9
            capo = [(x, y) for x, y in pts if ((x - px) * ox + (y - py) * oy) / r > 0.3]
            if len(capo) > 4:
                capo.sort(key=lambda p: math.atan2(p[1] - py, p[0] - px) - math.atan2(oy, ox) if abs(math.atan2(p[1] - py, p[0] - px) - math.atan2(oy, ox)) < math.pi
                          else (math.atan2(p[1] - py, p[0] - px) - math.atan2(oy, ox) + 2 * math.pi) % (2 * math.pi) - (2 * math.pi if (math.atan2(p[1] - py, p[0] - px) - math.atan2(oy, ox)) > 0 else 0))
                outer = [(px + (x - px) * 1.07, py + (y - py) * 1.07) for x, y in capo[::3]]
                inner = []
                for q, (x, y) in enumerate(outer[::-1]):
                    dep = (0.42 + 0.18 * math.sin(q * 1.9 + i) + 0.1 * rs.random()) * amt
                    inner.append((x - ox * r * dep + (px - x) * 0.12, y - oy * r * dep + (py - y) * 0.12))
                mc = mix_color(PAL["moss"], (PAL["moss_dk"], PAL["moss_lt"])[i % 2], rs.uniform(0.15, 0.5))
                mp = _paper_piece((Wd, Hd), catmull(outer + inner + outer[:1], 4), mc, seed=300 + i, edge=0.2, grain=0.34)
                im.alpha_composite(_shadow_of(mp, 2 * K, 0.6, (10, 24, 12)), (int(K), int(3 * K)))
                im.alpha_composite(mp)
                d = ImageDraw.Draw(im, "RGBA")
                for q in range(18):                                            # tufts
                    x, y = outer[rs.randrange(len(outer))]
                    x, y = x - ox * rs.uniform(0, 14) * K + rs.uniform(-8, 8) * K, y - oy * rs.uniform(0, 14) * K
                    d.line([x, y, x + rs.uniform(-3, 3) * K, y - rs.uniform(3, 7) * K], fill=PAL["moss_lt"] + (200,), width=max(1, K // 2))
        sc = width / dw / K
        parts[name] = im.resize((max(2, int(Wd * sc)), max(2, int(Hd * sc))), Image.LANCZOS)
    return parts


def arch(ink, c=None, width=None, part="all", alpha=1.0, dark=0.0):
    """Bell Boulder arch: boulders of torn green-grey paper with moss. c = (x of the middle, y of the feet),
    width = outer width in px (height is 0.81 of that). part: 'all', or 'left', 'lintel', 'right' separately so a
    trout can pass BEHIND the right pillar and IN FRONT of the left (draw right, trout, then left).
    Defaults are STAGE['arch_c'], STAGE['arch_w']. Returns {'crown': (x, y) under the keystone, 'top': y}."""
    c = STAGE["arch_c"] if c is None else c
    width = STAGE["arch_w"] if width is None else width
    P = _arch_parts(int(width))
    names = ("left", "right", "lintel") if part == "all" else (part,)
    for nme in names:
        im = P[nme]
        if dark:
            a = np.asarray(im, np.float32).copy()
            a[..., :3] = a[..., :3] * (1 - dark) + np.array(PAL["water_deep"], np.float32) * dark
            im = Image.fromarray(a.astype(np.uint8), "RGBA")
        ink.paste(im, (int(c[0] - im.width / 2), int(c[1] - im.height)), alpha)
    s = width / _ARCH_DESIGN[0]
    return {"crown": (c[0], c[1] - (420 - 170) * s), "top": c[1] - (420 - 60) * s}


def twig(ink, hang=None, span=150, scale=1.0, alpha=1.0):
    """The forked twig the bell hangs from, lying across under the arch's crown. `hang` is the point on the twig
    where the bell's loop sits (default STAGE['bell_hang']); the twig reaches `span` px to each side."""
    hx, hy = STAGE["bell_hang"] if hang is None else hang
    s = scale
    A = int(255 * alpha)
    main = catmull([(hx - span, hy - 26 * s), (hx - span * 0.6, hy - 8 * s), (hx - span * 0.2, hy + 1 * s), (hx, hy - 2 * s),
                    (hx + span * 0.35, hy - 10 * s), (hx + span * 0.7, hy - 4 * s), (hx + span, hy - 22 * s)], 6)
    fork = catmull([(hx + span * 0.3, hy - 9 * s), (hx + span * 0.5, hy - 30 * s), (hx + span * 0.62, hy - 52 * s)], 5)
    fork2 = catmull([(hx - span * 0.45, hy - 4 * s), (hx - span * 0.55, hy + 16 * s), (hx - span * 0.72, hy + 24 * s)], 5)
    for pts, w0, w1 in ((fork, 7, 3), (fork2, 6, 2), (main, 11, 6)):
        n = len(pts)
        ink.d.line([(x + 2, y + 4) for x, y in pts], fill=(8, 22, 20, int(110 * alpha)), width=int(w0 * s))
        for k in range(n - 1):
            w_ = max(2, int(lerp(w0, w1, abs(k / n - 0.5) * 2 if pts is main else k / n) * s))
            ink.d.line([pts[k], pts[k + 1]], fill=PAL["twig_dk"] + (A,), width=w_ + 2)
        for k in range(n - 1):
            w_ = max(1, int(lerp(w0, w1, abs(k / n - 0.5) * 2 if pts is main else k / n) * s))
            ink.d.line([pts[k], pts[k + 1]], fill=PAL["twig"] + (A,), width=w_)
        ink.d.line([(x, y - w0 * s * 0.25) for x, y in pts], fill=PAL["twig_lt"] + (int(170 * alpha),), width=max(1, int(1.5 * s)))
        for k in range(3, n - 2, 5):
            x, y = pts[k]
            ink.d.line([x - 2 * s, y - 3 * s, x + 1 * s, y + 3 * s], fill=PAL["twig_dk"] + (int(200 * alpha),), width=1)


@lru_cache(maxsize=8)
def _bell_spr(hq):
    """The brass bell, cut from foil-coloured card: (image, pivot=top of the loop, mouth y)."""
    K = 2
    h = hq * K
    w = int(h * 1.02)
    pad = int(h * 0.16)
    Wd, Hd = w + 2 * pad, h + 2 * pad
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    top = pad + h * 0.2                                       # the crown loop takes the first fifth
    v = np.clip((yy - top) / (h * 0.8), 0, 1)
    half = (0.20 + 0.16 * v + 0.14 * v ** 2 + 0.5 * v ** 6) * w / 2 * 1.02
    sh = np.where(v < 0.16, np.sqrt(np.clip(1 - (1 - v / 0.16) ** 2, 0, 1)), 1.0)
    half = half * (0.35 + 0.65 * sh)
    u = (xx - Wd / 2) / np.maximum(half, 1)
    inside = (np.abs(u) <= 1) & (yy >= top) & (yy <= top + h * 0.8)
    lit = 0.34 + 0.78 * np.exp(-((u + 0.38) / 0.36) ** 2) + 0.2 * np.exp(-((u - 0.72) / 0.16) ** 2)
    lit *= 1 - 0.3 * np.clip(np.abs(u) - 0.8, 0, 1) / 0.2
    lit += 0.25 * np.clip((v - 0.86) / 0.14, 0, 1) * np.exp(-((u + 0.3) / 0.6) ** 2)         # the flare catches light
    for vb, wdth, amt in ((0.80, 0.012, -0.3), (0.83, 0.012, 0.22), (0.3, 0.01, -0.2), (0.33, 0.01, 0.16)):
        lit += amt * np.exp(-((v - vb) / wdth) ** 2)                                        # turned bands
    tarn = (vnoise((Hd, Wd), 34, seed=6, octaves=3) - 0.5) * 0.26 + (vnoise((Hd, Wd), 4, 60, seed=7) - 0.5) * 0.08
    col = np.array([206, 160, 68], np.float32)[None, None] * (lit + tarn)[..., None]
    col[..., 2] *= 0.82
    col[..., 0] = np.minimum(255, col[..., 0] * 1.04)
    al = inside.astype(np.float32) * 255
    img = Image.fromarray(np.dstack([np.clip(col, 0, 255), al]).astype(np.uint8), "RGBA")
    am = img.getchannel("A").filter(ImageFilter.GaussianBlur(0.9)).point(lambda q: 0 if q < 100 else min(255, (q - 100) * 4))
    img.putalpha(am)
    d = ImageDraw.Draw(img, "RGBA")
    cxm, ym = Wd / 2, top + h * 0.8
    hw = half[int(min(Hd - 1, ym - 2)), 0]
    out = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    od = ImageDraw.Draw(out, "RGBA")
    # the mouth: a dark ellipse seen a little from below, with a bright lip
    od.ellipse([cxm - hw, ym - h * 0.05, cxm + hw, ym + h * 0.05], fill=(58, 38, 14, 255), outline=PAL["brass_line"] + (255,), width=K)
    od.ellipse([cxm - hw * 0.86, ym - h * 0.03, cxm + hw * 0.86, ym + h * 0.045], fill=(28, 18, 8, 255))
    out.alpha_composite(img)
    od = ImageDraw.Draw(out, "RGBA")
    od.arc([cxm - hw, ym - h * 0.05, cxm + hw, ym + h * 0.05], 20, 160, fill=(250, 226, 150, 255), width=max(2, int(1.6 * K)))
    od.arc([cxm - hw, ym - h * 0.05, cxm + hw, ym + h * 0.05], 20, 160, fill=PAL["brass_line"] + (120,), width=1)
    # outline of the cut card
    edge = ImageChops.subtract(am.filter(ImageFilter.MaxFilter(3)), am.filter(ImageFilter.MinFilter(3)))
    out.paste(Image.new("RGBA", (Wd, Hd), PAL["brass_line"] + (255,)), (0, 0), edge.point(lambda q: int(q * 0.8)))
    od = ImageDraw.Draw(out, "RGBA")
    # crown: a strap loop
    lw = h * 0.085
    od.ellipse([cxm - lw, pad + h * 0.02, cxm + lw, pad + h * 0.25], outline=PAL["brass_line"] + (255,), width=int(4.4 * K))
    od.ellipse([cxm - lw, pad + h * 0.02, cxm + lw, pad + h * 0.25], outline=(184, 142, 60, 255), width=int(2.8 * K))
    od.arc([cxm - lw, pad + h * 0.02, cxm + lw, pad + h * 0.25], 180, 280, fill=(248, 222, 146, 255), width=int(1.4 * K))
    od.rounded_rectangle([cxm - lw * 1.5, top - h * 0.01, cxm + lw * 1.5, top + h * 0.05], radius=2 * K, fill=(170, 130, 54, 255), outline=PAL["brass_line"] + (255,))
    od.line([cxm - lw * 1.2, top + h * 0.012, cxm + lw * 0.3, top + h * 0.012], fill=(250, 226, 150, 255), width=K)
    s = 1.0 / K
    small = out.resize((int(Wd * s), int(Hd * s)), Image.LANCZOS)
    return small, (Wd / 2 * s, (pad + h * 0.03) * s), (pad + h) * s - (pad + h * 0.03) * s


def bell(ink, hang=None, scale=1.0, swing=0.0, clapper=None, cord=None, part="all", disc=None, flash=0.0, alpha=1.0,
         cord_len=92, hoist=0.0):
    """The brass twig-bell hanging from `hang` (default STAGE['bell_hang']). All angles in degrees from plumb,
    positive = to the RIGHT. swing = the bell; clapper = the clapper's own angle (default: follows the bell);
    cord = the angle of the knotted cord's free end (default: follows the clapper). Drive clapper and cord from
    Followers so they arrive late. part 'cord' (clapper, cord, knot: draw these first), 'body' (the bell itself)
    or 'all'. disc = a button kind ('circle') pinned on the bell. flash 0..1 brightens it at a strike.
    hoist 0..1 shortens the cord (wound round the twig).
    Returns {'mouth', 'clapper', 'knot', 'pivot', 'strike' (-1 left wall, +1 right wall, 0 none), 'half' (mouth half-width)}."""
    hx, hy = STAGE["bell_hang"] if hang is None else hang
    hq = int(round(104 * scale / 4)) * 4
    spr, piv, Lm = _bell_spr(hq)
    clapper = swing if clapper is None else clapper
    cord = clapper if cord is None else cord
    a = math.radians(swing)
    mouth = (hx + Lm * math.sin(a), hy + Lm * math.cos(a))
    half = hq * 0.5
    cp = (hx + Lm * 0.34 * math.sin(a), hy + Lm * 0.34 * math.cos(a))          # clapper pivot, inside the dome
    ca = math.radians(clapper)
    cl = Lm * 0.72
    ball = (cp[0] + cl * math.sin(ca), cp[1] + cl * math.cos(ca))
    rel = clapper - swing
    strike = 1 if rel > 21 else (-1 if rel < -21 else 0)
    n = 7
    ln = cord_len * scale * (1 - 0.7 * clamp(hoist))
    pts = [ball]
    for k in range(1, n + 1):
        f = k / n
        ang = math.radians(lerp(clapper, cord, f ** 0.8))
        pts.append((pts[-1][0] + ln / n * math.sin(ang), pts[-1][1] + ln / n * math.cos(ang)))
    knot = pts[-2]
    A = int(255 * alpha)
    if part in ("all", "cord"):
        s = scale
        ink.d.line([cp, ball], fill=PAL["brass_line"] + (A,), width=max(2, int(5 * s)))
        ink.d.line([cp, ball], fill=(150, 112, 46, A), width=max(1, int(3 * s)))
        ink.d.line(pts, fill=PAL["cord_dk"] + (A,), width=max(2, int(5 * s)), joint="curve")
        ink.d.line(pts, fill=PAL["cord"] + (A,), width=max(1, int(3 * s)), joint="curve")
        for k in range(len(pts) - 1):                      # the rope's twist
            p, q = pts[k], pts[k + 1]
            for f in (0.25, 0.75):
                m = lerp2(p, q, f)
                ink.d.line([m[0] - 2 * s, m[1] - 1.5 * s, m[0] + 2 * s, m[1] + 1.5 * s], fill=PAL["cord_dk"] + (int(200 * alpha),), width=1)
        kr = 5.5 * s
        ink.d.ellipse([knot[0] - kr, knot[1] - kr * 0.9, knot[0] + kr, knot[1] + kr * 0.9], fill=PAL["cord"] + (A,), outline=PAL["cord_dk"] + (A,), width=max(1, int(1.5 * s)))
        ink.d.arc([knot[0] - kr * 0.6, knot[1] - kr * 0.6, knot[0] + kr * 0.6, knot[1] + kr * 0.6], 200, 20, fill=PAL["cord_dk"] + (A,), width=1)
        end = pts[-1]
        for dx in (-3, 0, 3):                              # the frayed end
            ink.d.line([end[0], end[1], end[0] + dx * s, end[1] + 7 * s], fill=PAL["cord"] + (A,), width=1)
        br = 7.5 * s
        ink.d.ellipse([ball[0] - br, ball[1] - br, ball[0] + br, ball[1] + br], fill=(168, 126, 50, A), outline=PAL["brass_line"] + (A,), width=max(1, int(1.5 * s)))
        ink.d.ellipse([ball[0] - br * 0.6, ball[1] - br * 0.7, ball[0], ball[1] - br * 0.1], fill=(250, 226, 150, int(230 * alpha)))
    if part in ("all", "body"):
        im = spr
        if flash > 0:
            arr = np.asarray(im, np.float32).copy()
            arr[..., :3] = np.minimum(255, arr[..., :3] * (1 + 0.45 * flash) + 40 * flash)
            im = Image.fromarray(arr.astype(np.uint8), "RGBA")
        lay = Image.new("RGBA", (im.width * 2, im.height * 2), (0, 0, 0, 0))
        tgt = (lay.width / 2, lay.height * 0.3)
        _pin(lay, im, piv, tgt, swing)
        ox, oy = int(round(hx - tgt[0])), int(round(hy - tgt[1]))
        ink.paste(_shadow_of(lay, 5, 0.42 * alpha, (6, 26, 28)), (ox + 6, oy + 9))
        ink.paste(lay, (ox, oy), alpha)
        if disc:
            dp = (hx + Lm * 0.56 * math.sin(a) - 4 * scale, hy + Lm * 0.56 * math.cos(a))
            button_disc(ink, disc, dp[0], dp[1], r=9 * scale * (1 + 0.25 * flash), alpha=alpha)
    return dict(mouth=mouth, clapper=ball, knot=knot, pivot=(hx, hy), strike=strike, half=half)


def speech_bubble(ink, tail, scale=1.0, angle=0.0, alpha=1.0, shadow=0.6):
    """The pilot's pencilled bubble "haha / verry / funny" as a cut-paper piece, to pin above the upper trout.
    `tail` = the screen point where the bubble's neck ends (the trout's head). scale 1 = 150 px wide."""
    spr, tp = _bubble_spr(int(round(150 * scale)))
    ox, oy = spr.width / 2 - tp[0], spr.height / 2 - tp[1]
    a = math.radians(angle)
    ox, oy = ox * math.cos(a) + oy * math.sin(a), -ox * math.sin(a) + oy * math.cos(a)
    put(ink, spr, tail[0] + ox, tail[1] + oy, angle=angle, alpha=alpha, shadow=shadow, shadow_off=(3, 5), shadow_blur=3)


@lru_cache(maxsize=8)
def _bubble_spr(width):
    K = 2
    strokes = [s for s in PILOT_STROKES if s["group"] == "bubble"]
    xs = [p[0] for s in strokes for p in s["pts"]]
    ys = [p[1] for s in strokes for p in s["pts"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = width * K / (x1 - x0)
    pad = 10 * K
    Wd, Hd = int((x1 - x0) * sc + 2 * pad), int((y1 - y0) * sc + 2 * pad)

    def T(p):
        return ((p[0] - x0) * sc + pad, (p[1] - y0) * sc + pad)
    outline = [T(p) for p in strokes[0]["pts"]] + [T(p) for p in strokes[1]["pts"][::-1]]
    m = Image.new("L", (Wd, Hd), 0)
    md = ImageDraw.Draw(m)
    md.polygon(outline, fill=255)
    m = m.filter(ImageFilter.MaxFilter(2 * int(2.5 * K) + 1)).filter(ImageFilter.GaussianBlur(K * 0.7))      # cut a little outside the line
    tex = np.ones((Hd, Wd, 3), np.float32) * np.array(PAL["sheet"], np.float32) * (0.96 + 0.06 * vnoise((Hd, Wd), 30, seed=3, octaves=2))[..., None]
    im = _img(tex).convert("RGBA")
    im.putalpha(m)
    d = ImageDraw.Draw(im, "RGBA")
    for s in strokes:
        _pencil_line(d, [T(p) for p in s["pts"]], s["weight"] * 1.1, K * width / 122.0)
    tp = T(strokes[1]["pts"][len(strokes[1]["pts"]) // 2])
    return im.resize((Wd // K, Hd // K), Image.LANCZOS), (tp[0] / K, tp[1] / K)


# ------------------------------------------------------------- brass and tin ---

@lru_cache(maxsize=8)
def brass_ring(r_in, r_out, bolts=6, pad=10, seed=0, start=-90.0):
    """A turned brass ring (RGBA, side 2*(r_out+pad)+1) with a bevelled inner flange and six hex bolts, lit from
    upper left. Bolt 1 is at twelve o'clock, the rest clockwise."""
    R = int(r_out + pad)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    r = np.hypot(xx, yy)
    th = np.arctan2(yy, xx)
    wdt = r_out - r_in
    f = (r - r_in) / wdt
    hgt = np.where(f < 0.22, f / 0.22, np.where(f < 0.82, 1.0, np.sqrt(np.clip(1 - ((f - 0.82) / 0.18) ** 2, 0, 1))))
    dh = np.gradient(hgt, axis=1) * xx / (r + 1e-6) + np.gradient(hgt, axis=0) * yy / (r + 1e-6)
    lx, ly = -0.62, -0.78
    slope = dh * wdt * 0.9
    nx, ny = -slope * np.cos(th), -slope * np.sin(th)
    lit = 0.62 + 0.55 * (nx * lx + ny * ly) + 0.22 * (-(np.cos(th) * lx + np.sin(th) * ly)) * (f > 0.82)
    rs = np.random.RandomState(seed)
    turn = np.interp(r, np.arange(int(R * 1.5)), rs.uniform(-1, 1, int(R * 1.5))) * 0.05 + 0.04 * np.sin(th * 2 + 0.7)
    tarn = (vnoise(r.shape, 40, seed=seed + 1, octaves=3) - 0.5) * 0.22
    col = np.array(PAL["brass"], np.float32)[None, None] * (lit + turn + tarn)[..., None]
    col[..., 2] *= 0.9 + tarn
    al = np.clip(np.minimum(r - r_in, r_out - r) + 0.5, 0, 1)
    img = Image.fromarray(np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([R - r_in - 1, R - r_in - 1, R + r_in + 1, R + r_in + 1], outline=(40, 28, 12, 200), width=max(1, int(wdt * 0.05)))
    d.ellipse([R - r_out, R - r_out, R + r_out, R + r_out], outline=(48, 34, 14, 170), width=1)
    br = wdt * 0.2
    rm = r_in + wdt * 0.55
    for b in range(bolts):
        a = math.radians(start + 360 * b / bolts)
        cx, cy = R + rm * math.cos(a), R + rm * math.sin(a)
        rot = rs.uniform(0, 1.0)
        hexa = [(cx + br * math.cos(rot + q * math.pi / 3), cy + br * math.sin(rot + q * math.pi / 3)) for q in range(6)]
        d.polygon([(x + br * 0.18, y + br * 0.26) for x, y in hexa], fill=(40, 26, 10, 150))
        d.polygon(hexa, fill=(168, 128, 52, 255), outline=(60, 42, 16, 255))
        for q in range(6):
            p0, p1 = hexa[q], hexa[(q + 1) % 6]
            mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
            l_ = (mx * lx + my * ly) / br
            c = tuple(int(np.clip(v * (0.8 + 0.5 * l_), 0, 255)) for v in (196, 154, 70))
            d.polygon([p0, p1, (cx + (p1[0] - cx) * 0.62, cy + (p1[1] - cy) * 0.62), (cx + (p0[0] - cx) * 0.62, cy + (p0[1] - cy) * 0.62)], fill=c + (255,))
        d.ellipse([cx - br * 0.6, cy - br * 0.6, cx + br * 0.6, cy + br * 0.6], fill=(206, 166, 82, 255), outline=(70, 50, 20, 220))
        d.line([(cx - br * 0.3, cy - br * 0.36), (cx + br * 0.1, cy - br * 0.46)], fill=(250, 232, 170, 220), width=max(1, int(br * 0.12)))
    return img


def _steel(w, h, seed, base, ribs=0, rust=0.5):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    brush = vnoise((h, w), 90, 5, seed=seed, octaves=2) - 0.5
    blot = vnoise((h, w), 60, seed=seed + 1, octaves=3)
    a = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    a *= (1 + brush * 0.16)[..., None]
    if ribs:
        a *= (1 + 0.13 * np.sin(xx / ribs * 2 * math.pi))[..., None]
    r = np.clip((blot - (0.78 - rust * 0.3)) * 6, 0, 1)[..., None]
    return a * (1 - r) + np.array([122, 74, 44], np.float32) * (0.8 + 0.4 * vnoise((h, w), 6, seed=seed + 2)[..., None]) * r


@lru_cache(maxsize=4)
def _seat_overlay(c, r):
    """The inside of the tin round the glass: dark ribbed plate, rivets, lamp-warm near the ring; a hole for the glass."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = _steel(W, H, 17, PAL["wall"], ribs=64, rust=0.12)
    dist = np.hypot(xx - c[0], yy - c[1])
    warm = np.exp(-((dist - r) / 150.0) ** 2)                     # river light spilling in round the ring
    a = a * (0.5 + 0.75 * warm[..., None]) + np.array([30, 54, 50], np.float32) * warm[..., None] * 0.5
    a *= (1.05 - 0.5 * np.clip((dist - r) / 520, 0, 1))[..., None]
    lampg = np.exp(-(((xx - 880) / 210) ** 2 + ((yy - 500) / 170) ** 2))        # the seat lamp, low right (where the gauge is)
    a += np.array(PAL["lamp"], np.float32) * lampg[..., None] * 0.2
    img = _img(a).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for x in (64, 896):                                           # seams with rivets
        d.line([x, 0, x, H], fill=(14, 12, 10, 200), width=3)
        d.line([x + 3, 0, x + 3, H], fill=(120, 108, 92, 70), width=1)
        for y in range(26, H, 54):
            for dx in (-16, 18):
                d.ellipse([x + dx - 5, y - 4, x + dx + 7, y + 8], fill=(8, 6, 6, 170))
                d.ellipse([x + dx - 5, y - 5, x + dx + 5, y + 5], fill=(86, 76, 66, 255), outline=(20, 16, 14, 255))
                d.ellipse([x + dx - 4, y - 4, x + dx, y], fill=(170, 152, 126, 255))
    ro = r * RING_OUT / PORT_R
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).ellipse([c[0] - ro - 4, c[1] - ro, c[0] + ro + 16, c[1] + ro + 22], fill=190)
    img.paste(Image.new("RGBA", (W, H), (6, 4, 4, 255)), (0, 0), sh.filter(ImageFilter.GaussianBlur(12)))
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=0)
    img.putalpha(hole.filter(ImageFilter.GaussianBlur(0.8)))
    # the glass: thickness shadow just inside the flange, and two glare streaks
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ga = np.clip((dist - (r - 26)) / 26, 0, 1) ** 2 * (dist <= r) * 150
    gl = Image.fromarray(np.dstack([np.full((H, W), 6), np.full((H, W), 22), np.full((H, W), 24), ga]).astype(np.uint8), "RGBA")
    g2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g2)
    gd.arc([c[0] - r * 0.9, c[1] - r * 0.9, c[0] + r * 0.9, c[1] + r * 0.9], 196, 262, fill=(240, 252, 244, 90), width=int(r * 0.05))
    gd.arc([c[0] - r * 0.78, c[1] - r * 0.78, c[0] + r * 0.78, c[1] + r * 0.78], 204, 236, fill=(240, 252, 244, 60), width=int(r * 0.025))
    gd.arc([c[0] - r * 0.92, c[1] - r * 0.92, c[0] + r * 0.92, c[1] + r * 0.92], 30, 62, fill=(240, 252, 244, 40), width=int(r * 0.03))
    gl.alpha_composite(g2.filter(ImageFilter.GaussianBlur(2.5)))
    out = Image.alpha_composite(gl, img)
    ring = brass_ring(int(r), int(ro), 6, 10, 3)
    out.alpha_composite(ring, (int(c[0] - ring.width / 2), int(c[1] - ring.height / 2)))
    return out


def seat_frame(ink, c=PORT_C, r=PORT_R):
    """Turkey's seat: everything round the glass. Draw the river scene full-frame first (and turkey_reflection),
    then call this: it covers all but the round glass (centre c, radius r) with the tin's dark riveted inside wall
    and the six-bolt brass porthole, and lays the glass's edge shadow and glare. Then gauge(), bolt marks, badge."""
    ink.paste(_seat_overlay(tuple(c), int(r)), (0, 0))


def bolt_mark(ink, n, lit=1.0, die=True, c=PORT_C, r=PORT_R, size=30, style="ivory"):
    """Light bolt n (1..6, clockwise from twelve) on a brass porthole at c, and sit its die face ON that bolt.
    lit 0..1: 1 = written (warm glow round a bright die), 0 = unwritten (no glow, the die grey and dead).
    die=False lights the bolt only. Returns the bolt's (x, y)."""
    ro = r * RING_OUT / PORT_R
    x, y = clock_xy(c, r + (ro - r) * 0.55, (n - 1) * 60)
    if lit > 0:
        g = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse([22, 22, 98, 98], fill=PAL["lamp"] + (int(200 * lit),))
        gd.ellipse([40, 40, 80, 80], fill=(255, 244, 200, int(240 * lit)))
        ink.paste(g.filter(ImageFilter.GaussianBlur(9)), (int(x - 60), int(y - 60)))
        br = (ro - r) * 0.13
        ink.d.ellipse([x - br, y - br, x + br, y + br], fill=(255, 240, 190, int(255 * lit)))
    if die:
        die_face(ink, n, x, y, size, style, lit=lit)
    return x, y


def gauge(ink, notches=8.0, x=None, y=None, r=46, tremble=0.0, t=0.0):
    """The air gauge: a brass dial with 8 notches and one needle. notches 8 = full, 0 = empty (give it a float and
    ease it so the needle falls). Default place STAGE['gauge'] (low right inside the seat). tremble shakes the needle."""
    x = STAGE["gauge"][0] if x is None else x
    y = STAGE["gauge"][1] if y is None else y
    ring = brass_ring(int(r * 0.8), int(r), 0, 6, 9)
    ink.d.ellipse([x - r + 4, y - r + 7, x + r + 8, y + r + 12], fill=(0, 0, 0, 110))
    ink.d.ellipse([x - r * 0.84, y - r * 0.84, x + r * 0.84, y + r * 0.84], fill=PAL["ivory"] + (255,))
    ink.d.pieslice([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], 135, 135 + 270 * 2 / 8, fill=(206, 70, 56, 150))
    for k in range(9):
        a = math.radians(135 + 270 * k / 8)
        p0 = (x + math.cos(a) * r * 0.56, y + math.sin(a) * r * 0.56)
        p1 = (x + math.cos(a) * r * 0.76, y + math.sin(a) * r * 0.76)
        ink.d.line([p0, p1], fill=PAL["pip"] + (255,), width=3 if k % 4 == 0 else 2)
    ink.d.text((x, y + r * 0.42), "AIR", font=font("mono", max(9, int(r * 0.24))), fill=PAL["pip"] + (255,), anchor="mm")
    a = math.radians(135 + 270 * clamp(notches / 8.0) + tremble * 3 * math.sin(t * 37))
    tipn = (x + math.cos(a) * r * 0.66, y + math.sin(a) * r * 0.66)
    tail = (x - math.cos(a) * r * 0.16, y - math.sin(a) * r * 0.16)
    ink.d.line([(tail[0] + 2, tail[1] + 3), (tipn[0] + 2, tipn[1] + 3)], fill=(0, 0, 0, 80), width=4)
    ink.d.line([tail, tipn], fill=(150, 30, 26, 255), width=4)
    ink.d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=PAL["brass"] + (255,), outline=PAL["brass_line"] + (255,))
    ink.paste(ring, (int(x - ring.width / 2), int(y - ring.height / 2)))
    ink.d.arc([x - r * 0.74, y - r * 0.74, x + r * 0.74, y + r * 0.74], 200, 250, fill=(255, 255, 255, 110), width=3)


def sweep(ink, new_img, f, c=PORT_C, arm=True, length=None):
    """Scene change by Clockwise Etiquette: a brass arm pinned at c sweeps once round, clockwise from twelve
    o'clock, like a clock hand, and the next scene (new_img, a full-frame PIL image, e.g. offscreen(ink).img after
    you draw on it) is revealed behind it. f = 0..1. Call after the old scene is drawn."""
    f = clamp(f)
    if f <= 0:
        return
    if f >= 1:
        ink.img.paste(new_img.convert("RGB"), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        return
    R = int(math.hypot(ink.w, ink.h))
    m = Image.new("L", (ink.w, ink.h), 0)
    ImageDraw.Draw(m).pieslice([c[0] - R, c[1] - R, c[0] + R, c[1] + R], -90, -90 + 360 * f, fill=255)
    ink.img.paste(new_img.convert("RGB"), (0, 0), m)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if arm:
        brass_arm(ink, c, 360 * f, length or R)


def brass_arm(ink, c, clock_deg, length=620):
    """The sweeping brass arm alone: pinned at c, pointing at clock angle clock_deg (0 = twelve, clockwise)."""
    a = math.radians(clock_deg)
    ux, uy = math.sin(a), -math.cos(a)
    nx, ny = -uy, ux
    w0, w1 = 13, 6
    tip = (c[0] + ux * length, c[1] + uy * length)
    back = (c[0] - ux * 30, c[1] - uy * 30)
    poly = [(back[0] + nx * w0, back[1] + ny * w0), (tip[0] + nx * w1, tip[1] + ny * w1), (tip[0] - nx * w1, tip[1] - ny * w1),
            (back[0] - nx * w0, back[1] - ny * w0)]
    ink.d.polygon([(x - nx * 10 + 3, y - ny * 10 + 5) for x, y in poly], fill=(0, 0, 0, 80))          # shadow trails behind the arm
    ink.d.polygon(poly, fill=PAL["brass"] + (255,), outline=PAL["brass_line"] + (255,))
    ink.d.line([(back[0] + nx * w0 * 0.45, back[1] + ny * w0 * 0.45), (tip[0] + nx * w1 * 0.45, tip[1] + ny * w1 * 0.45)], fill=PAL["brass_hi"] + (230,), width=3)
    ink.d.line([(back[0] - nx * w0 * 0.6, back[1] - ny * w0 * 0.6), (tip[0] - nx * w1 * 0.6, tip[1] - ny * w1 * 0.6)], fill=PAL["brass_dk"] + (230,), width=3)
    for rr, col in ((22, PAL["brass_dk"]), (17, PAL["brass"]), (8, PAL["brass_line"]), (5, PAL["brass_hi"])):
        ink.d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=col + (255,), outline=PAL["brass_line"] + (255,))


# the tin, side on (river side and on the table)
_TIN = {}


def _build_tin():
    if _TIN:
        return _TIN
    K = 2
    w, h = 400 * K, 190 * K
    pad = 70 * K
    Wd, Hd = w + 2 * pad, h + 2 * pad
    a = _steel(Wd, Hd, 5, PAL["tin"], ribs=15 * K, rust=0.42)
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    v = np.clip((yy - pad) / h, 0, 1)
    cyl = 0.40 + 0.86 * np.exp(-((v - 0.27) / 0.2) ** 2) + 0.2 * np.exp(-((v - 0.95) / 0.07) ** 2)      # a drum: bright shoulder, dark belly
    dent = 1 - 0.22 * np.exp(-(((xx - pad - 300 * K) / (34 * K)) ** 2 + ((yy - pad - 150 * K) / (22 * K)) ** 2)) \
        + 0.16 * np.exp(-(((xx - pad - 292 * K) / (30 * K)) ** 2 + ((yy - pad - 138 * K) / (12 * K)) ** 2))
    a *= (cyl * dent)[..., None]
    rs = np.random.RandomState(8)
    for k in range(26):                                     # rust runs
        x0, y0, ln, wd = pad + rs.uniform(10, 390) * K, pad + rs.uniform(10, 90) * K, rs.uniform(30, 110) * K, rs.uniform(2, 6) * K
        st = np.exp(-((xx - x0) / wd) ** 2) * np.clip((yy - y0) / ln, 0, 1) * np.clip(1 - (yy - y0) / ln, 0, 1) * 2.4
        a = a * (1 - 0.5 * st[..., None]) + np.array([112, 64, 36], np.float32) * 0.5 * st[..., None]
    img = _img(a).convert("RGBA")
    m = Image.new("L", (Wd, Hd), 0)
    md = ImageDraw.Draw(m)
    md.rounded_rectangle([pad, pad, pad + w, pad + h], radius=12 * K, fill=255)
    rims = [(pad - 2 * K, 13 * K), (pad + w - 11 * K, 13 * K)]
    for x, wd in rims:
        md.rounded_rectangle([x, pad - 7 * K, x + wd, pad + h + 7 * K], radius=5 * K, fill=255)
    img.putalpha(m)
    d = ImageDraw.Draw(img, "RGBA")
    for x, wd in rims + [(pad + 74 * K, 7 * K)]:            # rolled beads
        top, bot = (pad - 7 * K, pad + h + 7 * K) if wd > 8 * K else (pad + 2, pad + h - 2)
        for q in range(int(wd)):
            f = q / wd
            l_ = 0.5 + 0.75 * math.sin(f * math.pi) ** 2 * (1.25 - f)
            d.line([(x + q, top + 3 * K), (x + q, bot - 3 * K)], fill=tuple(int(min(255, c * l_)) for c in (176, 192, 196)) + (255,))
        d.line([(x + wd, top + 6 * K), (x + wd, bot - 6 * K)], fill=(22, 30, 36, 190), width=K)
    for k in range(9):                                      # rivets
        y = pad + 14 * K + k * (h - 28 * K) / 8
        for x in (pad + 22 * K, pad + w - 20 * K, pad + 90 * K):
            d.ellipse([x - 4 * K, y - 3 * K, x + 5 * K, y + 5 * K], fill=(30, 40, 46, 150))
            d.ellipse([x - 4 * K, y - 4 * K, x + 4 * K, y + 4 * K], fill=(98, 112, 118, 255))
            d.ellipse([x - 3 * K, y - 4 * K, x + 1 * K, y], fill=(222, 230, 228, 255))
    for k in range(14):                                     # a second row along the top and bottom seams
        x = pad + 104 * K + k * (w - 130 * K) / 13
        for y in (pad + 9 * K, pad + h - 9 * K):
            d.ellipse([x - 3 * K, y - 2 * K, x + 4 * K, y + 4 * K], fill=(30, 40, 46, 150))
            d.ellipse([x - 3 * K, y - 3 * K, x + 3 * K, y + 3 * K], fill=(98, 112, 118, 255))
            d.ellipse([x - 2 * K, y - 3 * K, x + 1 * K, y], fill=(222, 230, 228, 255))
    d.line([(pad + 96 * K, pad + 118 * K), (pad + w - 14 * K, pad + 118 * K)], fill=(30, 40, 46, 150), width=K)
    d.line([(pad + 96 * K, pad + 116 * K), (pad + w - 14 * K, pad + 116 * K)], fill=(226, 232, 230, 50), width=K)
    lab = Image.new("RGBA", (128 * K, 60 * K), (230, 216, 184, 255))        # the paper label
    ld = ImageDraw.Draw(lab)
    ld.rectangle([4 * K, 4 * K, 128 * K - 4 * K, 60 * K - 4 * K], outline=(124, 44, 40, 255), width=K)
    ld.text((64 * K, 25 * K), "ROLLS", font=font("serif", 29 * K), fill=(124, 44, 40, 255), anchor="mm")
    ld.text((64 * K, 47 * K), "ONE DOZEN · TROUT TOWN", font=font("mono", 6 * K), fill=(90, 60, 50, 255), anchor="mm")
    la = np.asarray(lab, np.float32).copy()
    ly_, lx_ = np.mgrid[0:60 * K, 0:128 * K].astype(np.float32)
    la[..., :3] *= (0.8 + 0.24 * vnoise((60 * K, 128 * K), 30, seed=9, octaves=2))[..., None] * (0.72 + 0.5 * np.exp(-((ly_ / (60 * K) - 0.1) / 0.5) ** 2))[..., None]
    lab = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA").rotate(-3, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(_shadow_of(lab, 2 * K, 0.45, (10, 16, 20)), (pad + 236 * K, pad + 30 * K))
    img.alpha_composite(lab, (pad + 234 * K, pad + 26 * K))
    img.putalpha(ImageChops.darker(img.getchannel("A"), m))
    d = ImageDraw.Draw(img, "RGBA")
    brass, bdark, bline = PAL["brass"] + (255,), PAL["brass_dk"] + (255,), PAL["brass_line"] + (255,)
    for x0 in (112, 232):                                   # lead keel
        d.rounded_rectangle([pad + x0 * K, pad + h - 2 * K, pad + (x0 + 92) * K, pad + h + 17 * K], radius=5 * K, fill=(66, 74, 80, 255), outline=(26, 30, 34, 255), width=K)
        d.line([(pad + (x0 + 6) * K, pad + h + 2 * K), (pad + (x0 + 86) * K, pad + h + 2 * K)], fill=(128, 138, 142, 255), width=K)
        for bx in (x0 + 14, x0 + 78):
            d.ellipse([pad + bx * K - 3 * K, pad + h + 5 * K, pad + bx * K + 3 * K, pad + h + 11 * K], fill=brass, outline=bline)
    d.rounded_rectangle([pad + 176 * K, pad - 15 * K, pad + 262 * K, pad + 3 * K], radius=4 * K, fill=(150, 166, 172, 255), outline=(30, 40, 46, 255), width=K)    # hatch
    d.line([(pad + 180 * K, pad - 10 * K), (pad + 258 * K, pad - 10 * K)], fill=(232, 238, 236, 255), width=K)
    for q in range(12):
        d.line([(pad + (181 + q * 7) * K, pad - 6 * K), (pad + (181 + q * 7) * K, pad + 1 * K)], fill=(70, 84, 90, 255), width=K)
    d.arc([pad + 196 * K, pad - 34 * K, pad + 242 * K, pad + 2 * K], 180, 360, fill=(60, 66, 70, 255), width=2 * K)
    d.line([(pad + 330 * K, pad + 2 * K), (pad + 330 * K, pad - 40 * K), (pad + 350 * K, pad - 52 * K)], fill=(60, 72, 78, 255), width=9 * K, joint="curve")   # snorkel
    d.line([(pad + 328 * K, pad + 2 * K), (pad + 328 * K, pad - 40 * K), (pad + 348 * K, pad - 53 * K)], fill=(168, 182, 186, 255), width=4 * K, joint="curve")
    d.ellipse([pad + 343 * K, pad - 62 * K, pad + 361 * K, pad - 44 * K], fill=brass, outline=bline)
    d.polygon([(pad + w - 4 * K, pad + 22 * K), (pad + w + 44 * K, pad - 16 * K), (pad + w + 50 * K, pad + 60 * K), (pad + w - 2 * K, pad + 70 * K)], fill=(124, 140, 146, 255), outline=(30, 40, 46, 255))
    d.line([(pad + w + 6 * K, pad + 28 * K), (pad + w + 42 * K, pad - 2 * K)], fill=(214, 224, 224, 200), width=K)
    d.rectangle([pad + w - 2 * K, pad + h / 2 + 22 * K, pad + w + 30 * K, pad + h / 2 + 34 * K], fill=bdark, outline=bline)
    d.ellipse([pad + w + 22 * K, pad + h / 2 + 16 * K, pad + w + 46 * K, pad + h / 2 + 40 * K], fill=brass, outline=bline)
    lx_, ly_ = pad + 1 * K, pad + h - 40 * K                 # lamp cowl at the nose, lens tilted up
    d.line([(pad + 4 * K, ly_ + 10 * K), (lx_ + 14 * K, ly_ + 6 * K)], fill=(50, 58, 62, 255), width=6 * K)
    body = [(lx_ + 30 * K, ly_ - 6 * K), (lx_ - 4 * K, ly_ - 26 * K), (lx_ - 20 * K, ly_ + 2 * K), (lx_ + 16 * K, ly_ + 22 * K)]
    d.polygon(body, fill=brass, outline=bline)
    d.polygon([body[0], body[1], (lx_ + 2 * K, ly_ - 18 * K), (lx_ + 28 * K, ly_ - 1 * K)], fill=(226, 190, 104, 255))
    d.polygon([(lx_ - 4 * K, ly_ - 26 * K), (lx_ - 20 * K, ly_ + 2 * K), (lx_ - 13 * K, ly_ + 5 * K), (lx_ + 3 * K, ly_ - 22 * K)], fill=(255, 232, 160, 255), outline=bline)
    b = Image.new("RGBA", (30 * K, 110 * K), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.ellipse([3 * K, 2 * K, 27 * K, 54 * K], fill=brass, outline=bline)
    bd.ellipse([8 * K, 6 * K, 18 * K, 40 * K], fill=(214, 178, 96, 255))
    bd.ellipse([3 * K, 56 * K, 27 * K, 108 * K], fill=bdark, outline=bline)
    r = 41 * K
    y2, x2 = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    gl = np.exp(-(((x2 - r * 1.2) / (r * 0.9)) ** 2 + ((y2 - r * 0.2) / (r * 0.8)) ** 2))
    bg = np.array([40, 24, 14], np.float32)[None, None] * (1 - gl[..., None]) + np.array(PAL["amber"], np.float32)[None, None] * gl[..., None]
    _TIN.update(img=img, K=K, pad=pad, size=(w, h), port=(pad + 122 * K, pad + 92 * K), lamp=(lx_ - 12 * K, ly_ - 12 * K),
                ring=brass_ring(40 * K, 58 * K, 6, 4, 3), prop=b, win=_img(bg).convert("RGBA"), r=r)
    return _TIN


def tin_sprite(t=0.0, mood=None, glow=1.0, **over):
    """The bread-roll tin side on, nose (lamp) to the LEFT, as an RGBA image 1080x660 (use tin() to place it).
    mood = a Turkey mood to show him behind the porthole glass, or None for the glass glowing amber and empty.
    glow 0..1 = the lamp-light inside."""
    T = _build_tin()
    K = T["K"]
    img = T["img"].copy()
    px, py = T["port"]
    r = T["r"]
    win = T["win"].copy()
    if glow < 1:
        win = Image.blend(Image.new("RGBA", win.size, (22, 16, 12, 255)), win, clamp(glow))
    if mood:
        spr, (ax, ay) = turkey_sprite(mood, t, int(r * 2.0), "bust", **over)
        _paste_clip(win, spr, (int(r * 1.0 - ax), int(r * 1.0 - ay)))
    win = win.convert("RGB")
    wd = ImageDraw.Draw(win, "RGBA")
    wd.ellipse([-r * 0.3, -r * 0.7, r * 1.2, r * 0.55], fill=(210, 240, 235, 30))
    msk = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(msk).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    img.paste(win, (int(px - r), int(py - r)), msk)
    rg = T["ring"]
    img.alpha_composite(rg, (int(px - rg.width / 2), int(py - rg.height / 2)))
    w, h = T["size"]
    pad = T["pad"]
    bl = T["prop"]
    sq = abs(math.cos(t * 5.0)) * 0.85 + 0.15
    b2 = bl.resize((bl.width, max(2, int(bl.height * sq))), Image.BILINEAR)
    img.alpha_composite(b2, (int(pad + w + 30 * K), int(pad + h / 2 + 28 * K - b2.height / 2)))
    return img


def tin(ink, c=None, scale=None, t=0.0, mood=None, glow=1.0, angle=0.0, flip=False, shadow=0.7, beam=0.0, shake=0.0, alpha=1.0, **over):
    """Draw the riveted bread-roll tin with the middle of its body at c (default RIVER['tin_c']), nose and lamp to
    the left (flip=True: to the right). scale 1.0 = body 400 px long, 190 high (default RIVER['tin_scale']).
    mood = Turkey behind the glass (None = empty amber glass). angle degrees counter-clockwise (90 = nose down,
    -90 = nose up). beam 0..1 draws the lamp's cone of light. shake px rattles it.
    Returns {'port': porthole centre, 'port_r': glass radius, 'lamp': lens point, 'nose', 'tail'} on screen."""
    c = RIVER["tin_c"] if c is None else c
    scale = RIVER["tin_scale"] if scale is None else scale
    T = _build_tin()
    K = T["K"]
    spr = tin_sprite(t, mood, glow, **over)
    s = scale / K
    cx = c[0] + shake * math.sin(t * 61)
    cy = c[1] + shake * 0.6 * math.cos(t * 67)

    def M(p):                                   # sprite pixel -> screen
        x, y = (p[0] - spr.width / 2) * s, (p[1] - spr.height / 2) * s
        if flip:
            x = -x
        a = math.radians(angle)
        return (cx + x * math.cos(a) + y * math.sin(a), cy - x * math.sin(a) + y * math.cos(a))
    pad, (w, h) = T["pad"], T["size"]
    out = dict(port=M(T["port"]), port_r=41 * K * s, lamp=M(T["lamp"]), nose=M((pad, pad + h / 2)), tail=M((pad + w, pad + h / 2)))
    if beam > 0:
        lp = out["lamp"]
        d0 = M((T["lamp"][0] - 100, T["lamp"][1] - 150))
        ux, uy = d0[0] - lp[0], d0[1] - lp[1]
        n = math.hypot(ux, uy)
        ux, uy = ux / n, uy / n
        L = 520 * scale
        lay = Image.new("RGBA", (ink.w, ink.h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for wdt, al in ((0.34, 46), (0.22, 60), (0.1, 70)):
            ld.polygon([lp, (lp[0] + ux * L - uy * L * wdt, lp[1] + uy * L + ux * L * wdt), (lp[0] + ux * L + uy * L * wdt, lp[1] + uy * L - ux * L * wdt)],
                       fill=PAL["lamp"] + (int(al * beam),))
        ink.paste(lay.filter(ImageFilter.GaussianBlur(7)), (0, 0))
    put(ink, spr, cx, cy, angle=angle, scale=s, flip=flip, alpha=alpha, shadow=shadow, shadow_off=(8, 12), shadow_blur=8)
    return out


@lru_cache(maxsize=4)
def _tin_plate(r):
    S = int(r * 3.4)
    a = _steel(S, S, 25, PAL["tin"], ribs=int(r * 0.42), rust=0.45)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    a *= (0.62 + 0.6 * np.exp(-(((yy / S) - 0.26) / 0.3) ** 2))[..., None]
    img = _img(a).convert("RGBA")
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle([4, 4, S - 5, S - 5], radius=int(r * 0.2), fill=255)
    img.putalpha(m)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([4, 4, S - 5, S - 5], radius=int(r * 0.2), outline=(26, 34, 40, 255), width=3)
    step = S / 11
    rv = max(3, int(r * 0.045))
    for k in range(1, 11):
        for (x, y) in ((k * step, step * 0.45), (k * step, S - step * 0.45), (step * 0.45, k * step), (S - step * 0.45, k * step)):
            d.ellipse([x - rv, y - rv + 2, x + rv + 2, y + rv + 3], fill=(24, 32, 38, 160))
            d.ellipse([x - rv, y - rv, x + rv, y + rv], fill=(98, 112, 118, 255))
            d.ellipse([x - rv * 0.7, y - rv, x + rv * 0.2, y - rv * 0.1], fill=(226, 232, 230, 255))
    return img


def tin_porthole(ink, c=PORT_C, r=150, mood="freak", t=0.0, glow=1.0, shake=0.0, angle=0.0, shadow=0.8, **over):
    """Looking IN through the tin's porthole from outside, close: a riveted plate of the tin, the six-bolt brass
    ring (glass radius r), amber lamp-light inside and Turkey filling the round glass. shake px rattles the plate
    (rivets and all). Returns the glass centre on screen."""
    r = int(r)
    plate = _tin_plate(r).copy()
    S = plate.width
    win = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    y2, x2 = np.mgrid[0:2 * r, 0:2 * r].astype(np.float32)
    gl = np.exp(-(((x2 - r * 1.25) / (r * 1.0)) ** 2 + ((y2 - r * 0.3) / (r * 0.9)) ** 2)) * glow
    bg = np.array([36, 22, 14], np.float32)[None, None] * (1 - gl[..., None]) + np.array(PAL["amber"], np.float32)[None, None] * gl[..., None]
    win = _img(bg).convert("RGBA")
    if mood:
        spr, (ax, ay) = turkey_sprite(mood, t, int(r * 2.0), "bust", **over)
        _paste_clip(win, spr, (int(r * 1.0 - ax), int(r * 1.0 - ay)))
    edge = np.clip((np.hypot(x2 - r, y2 - r) - (r - r * 0.14)) / (r * 0.14), 0, 1) ** 2 * 170
    win.alpha_composite(Image.fromarray(np.dstack([np.zeros((2 * r, 2 * r, 3)), edge]).astype(np.uint8), "RGBA"))
    win = win.convert("RGB")
    wd = ImageDraw.Draw(win, "RGBA")
    wd.ellipse([-r * 0.3, -r * 0.75, r * 1.2, r * 0.5], fill=(210, 240, 235, 26))
    wd.arc([r * 0.1, r * 0.1, r * 1.9, r * 1.9], 200, 250, fill=(240, 252, 244, 110), width=max(2, int(r * 0.045)))
    msk = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(msk).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    plate.paste(win, (S // 2 - r, S // 2 - r), msk)
    ring = brass_ring(r, int(r * RING_OUT / PORT_R), 6, 6, 3)
    plate.alpha_composite(ring, (S // 2 - ring.width // 2, S // 2 - ring.height // 2))
    cx = c[0] + shake * math.sin(t * 61)
    cy = c[1] + shake * 0.6 * math.cos(t * 67)
    put(ink, plate, cx, cy, angle=angle + (shake * 0.25 * math.sin(t * 43) if shake else 0), shadow=shadow, shadow_off=(9, 13), shadow_blur=9)
    return cx, cy


# ------------------------------------------------------ pick card, die cup ---

PICKS = dict(
    turkey=dict(title="Turkey thinks", rows=[("triangle", "Tripwire alarm"), ("circle", "Dinner bell")]),
    trout=dict(title="The trout think", rows=[("cross", "Polite ferry customer"), ("square", "Bell-ringer prank")]),
)
CARD_W, CARD_H = 420, 230


def pick_card(ink, c=(480, 262), side="turkey", picked=None, press=0.0, loop=0.0, angle=-2.0, alpha=1.0, initial=None, lift=0.0):
    """The pick card, a piece of the worksheet laid on the glass: the title, the two choices each with its
    controller button, and the dashed "Draw the one you pick" ring. side 'turkey' (green triangle Tripwire alarm /
    red circle Dinner bell) or 'trout' (blue cross Polite ferry customer / pink square Bell-ringer prank).
    picked = the kind that is chosen (e.g. 'circle') or None: nothing lights (a blank pick stays blank).
    press 0..1 sinks and lights the picked button; the other stays dull. loop 0..1 pencils the friend's own
    wobbly circle, CLOCKWISE, in the dashed ring. initial = 'A.' printed small in the corner, or None.
    lift 0..1 raises the card off the glass (bigger shadow) for laying down and taking away.
    Returns {'ring': centre of the dashed ring, 'tip': pencil point (or None), 'buttons': {kind: (x, y)}} on screen."""
    P = PICKS[side]
    K = 2
    cw, ch = CARD_W * K, CARD_H * K
    key = (side, initial)
    base = _card_base(side, initial)
    im = base.copy()
    lay = Ink(ink.t, ink.i, (cw, ch))
    lay.img = im
    lay.d = ImageDraw.Draw(im, "RGBA")
    pos = {}
    for k, (kind, label) in enumerate(P["rows"]):
        bx, by = 52 * K, (78 + k * 56) * K
        on = picked == kind
        button(lay, kind, bx, by, r=17 * K, pressed=press if on else 0.0, lit=(0.35 + 0.65 * press) if on else 0.15)
        pos[kind] = (bx / K, by / K)
    rc = (368 * K, 186 * K)
    tipc = None
    if loop > 0:
        rs = random.Random(4)
        n = 40
        pts = []
        for q in range(int(n * clamp(loop) * 1.06) + 1):
            a = -math.pi / 2 + 0.3 + 2 * math.pi * q / n                 # clockwise on screen (y down)
            rr = (13.5 + 2.0 * math.sin(q * 0.5) + rs.uniform(-0.5, 0.5)) * K
            pts.append((rc[0] + rr * 0.92 * math.cos(a), rc[1] + rr * 1.08 * math.sin(a)))
        if len(pts) > 1:
            _pencil_line(lay.d, pts, 1.3, K * 1.2)
        tipc = pts[-1]
    im = lay.img
    a = math.radians(angle)

    def M(p):
        x, y = p[0] - CARD_W / 2, p[1] - CARD_H / 2
        return (c[0] + x * math.cos(a) + y * math.sin(a) - 6 * lift, c[1] - x * math.sin(a) + y * math.cos(a) - 18 * lift)
    put(ink, im, c[0] - 6 * lift, c[1] - 18 * lift, angle=angle, scale=1 / K, alpha=alpha, shadow=0.75,
        shadow_off=(int(5 + 14 * lift), int(7 + 22 * lift)), shadow_blur=int(5 + 6 * lift))
    return dict(ring=M((rc[0] / K, rc[1] / K)), tip=M((tipc[0] / K, tipc[1] / K)) if tipc else None, buttons={k_: M(v) for k_, v in pos.items()})


@lru_cache(maxsize=8)
def _card_base(side, initial):
    P = PICKS[side]
    K = 2
    cw, ch = CARD_W * K, CARD_H * K
    tex = np.ones((ch, cw, 3), np.float32) * np.array(PAL["sheet"], np.float32) * (0.96 + 0.06 * vnoise((ch, cw), 50, seed=12, octaves=3))[..., None]
    im = _img(tex).convert("RGBA")
    m = Image.new("L", (cw, ch), 0)
    rs = random.Random(2)
    edge = [(rs.uniform(0, 3) * K, y) for y in range(0, ch, 12)]                                   # the torn left edge
    ImageDraw.Draw(m).polygon(edge + [(0, ch), (cw, ch), (cw, 0), (0, 0)], fill=255)
    ImageDraw.Draw(m).polygon([(0, 0)] + edge + [(0, ch)], fill=0)
    im.putalpha(m)
    d = ImageDraw.Draw(im, "RGBA")
    ink_c = PAL["print"] + (255,)
    d.text((26 * K, 26 * K), P["title"], font=font("sans", 19 * K), fill=ink_c, anchor="lm")
    if initial:
        d.text((cw - 26 * K, 26 * K), initial, font=font("mono", 13 * K), fill=(120, 116, 110, 255), anchor="rm")
    d.line([26 * K, 44 * K, cw - 26 * K, 44 * K], fill=(190, 186, 178, 255), width=K)
    for k, (kind, label) in enumerate(P["rows"]):
        y = (78 + k * 56) * K
        d.rounded_rectangle([22 * K, y - 24 * K, cw - 22 * K, y + 24 * K], radius=12 * K, outline=(96, 94, 90, 255), width=K)
        d.text((88 * K, y), label, font=font("sans", 20 * K), fill=ink_c, anchor="lm")
    d.text((26 * K, 186 * K), "Draw the one you pick", font=font("sans", 15 * K), fill=ink_c, anchor="lm")
    rc, rr = (368 * K, 186 * K), 25 * K
    for q in range(28):
        if q % 2 == 0:
            d.arc([rc[0] - rr, rc[1] - rr, rc[0] + rr, rc[1] + rr], q * 360 / 28, (q + 1) * 360 / 28, fill=(120, 118, 112, 255), width=K)
    return im


@lru_cache(maxsize=4)
def _cup_spr(hq, show_die):
    K = 2
    h = hq * K
    w = int(h * 0.86)
    pad = int(h * 0.2)
    Wd, Hd = w + 2 * pad, h + 2 * pad
    yy, xx = np.mgrid[0:Hd, 0:Wd].astype(np.float32)
    v = np.clip((yy - pad) / h, 0, 1)
    half = (0.5 - 0.09 * v) * w                                # tapers to the foot
    u = (xx - Wd / 2) / half
    body = (np.abs(u) <= 1) & (yy >= pad + h * 0.12) & (yy <= pad + h * 0.97 + np.sqrt(np.clip(1 - u ** 2, 0, 1)) * h * 0.05)
    lit = 0.5 + 0.6 * np.exp(-((u + 0.45) / 0.4) ** 2) - 0.22 * np.clip(u - 0.3, 0, 1)
    grain = (vnoise((Hd, Wd), 8, seed=41, octaves=2) - 0.5) * 0.22 + (vnoise((Hd, Wd), 60, seed=42, octaves=2) - 0.5) * 0.2
    col = np.array(PAL["leather"], np.float32)[None, None] * (lit + grain)[..., None]
    img = Image.fromarray(np.dstack([np.clip(col, 0, 255), body * 255]).astype(np.uint8), "RGBA")
    out = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(out, "RGBA")
    cx, ty, ry = Wd / 2, pad + h * 0.12, h * 0.1
    rx = w * 0.5
    # the mouth of the cup, seen from above: back wall, dark inside
    d.ellipse([cx - rx, ty - ry, cx + rx, ty + ry], fill=PAL["leather_dk"] + (255,), outline=(30, 16, 8, 255), width=K)
    d.ellipse([cx - rx * 0.93, ty - ry * 0.8, cx + rx * 0.93, ty + ry * 0.95], fill=(34, 18, 10, 255))
    if show_die:                                               # the die at rest inside, seen over the lip
        s = int(w * 0.36)
        die = _die_spr(4, s, "ivory", 8).rotate(-14, expand=True, resample=Image.BICUBIC)
        die = die.resize((die.width, int(die.height * 0.62)), Image.LANCZOS)
        out.alpha_composite(die, (int(cx - die.width * 0.42), int(ty - die.height * 0.42)))
        d = ImageDraw.Draw(out, "RGBA")
    front = img.copy()
    fm = Image.new("L", (Wd, Hd), 0)
    ImageDraw.Draw(fm).ellipse([cx - rx, ty - ry, cx + rx, ty + ry], fill=255)
    al = np.asarray(front.getchannel("A")).copy()
    # the front wall hides what is below the lip's near edge
    ell_low = ty + ry * np.sqrt(np.clip(1 - ((xx - cx) / rx) ** 2, 0, 1))
    al = np.where(yy >= ell_low, al, 0).astype(np.uint8)
    front.putalpha(Image.fromarray(al))
    out.alpha_composite(front)
    d = ImageDraw.Draw(out, "RGBA")
    d.arc([cx - rx, ty - ry, cx + rx, ty + ry], 0, 180, fill=(226, 190, 150, 255), width=int(2.5 * K))           # the near lip
    d.arc([cx - rx, ty - ry + 3 * K, cx + rx, ty + ry + 3 * K], 0, 180, fill=(40, 20, 10, 200), width=K)
    for q in range(22):                                        # saddle stitching under the lip and along the seam
        a = math.radians(8 + q * 164 / 21)
        x, y = cx + rx * 0.99 * math.cos(a), ty + ry * math.sin(a) + 9 * K
        d.line([x - 2 * K, y, x + 2 * K, y + 1], fill=(236, 220, 186, 255), width=K)
    for q in range(12):
        y = pad + h * (0.24 + q * 0.058)
        x = cx + w * 0.16 - (y - pad) / h * w * 0.02
        d.line([x, y, x + 1, y + 4 * K], fill=(236, 220, 186, 255), width=K)
    d.line([cx + w * 0.14, pad + h * 0.2, cx + w * 0.115, pad + h * 0.96], fill=(50, 26, 14, 200), width=K)
    d.arc([cx - half[int(pad + h * 0.9), 0], pad + h * 0.86, cx + half[int(pad + h * 0.9), 0], pad + h * 0.98], 10, 170, fill=(50, 26, 14, 220), width=2 * K)
    return out.resize((Wd // K, Hd // K), Image.LANCZOS)


def die_cup(ink, x, y, height=150, die=True, alpha=1.0, shadow=0.9):
    """A leather die cup standing upright with its foot at (x, y), `height` px tall; die=True shows the one die
    resting inside, seen over the lip. It does not move: this is the die that has not been thrown."""
    spr = _cup_spr(int(height), bool(die))
    pad = spr.height * 0.2 / 1.4
    ink.d.ellipse([x - height * 0.42, y - height * 0.07, x + height * 0.62, y + height * 0.1], fill=(0, 0, 0, int(80 * shadow * alpha)))
    put(ink, spr, x, y - spr.height / 2 + pad, alpha=alpha, shadow=shadow * 0.6, shadow_off=(10, 6), shadow_blur=7)


def porthole_on_table(ink, c=PORT_C, r=PORT_R, drawing=0.45, shadow=0.7):
    """The ending's porthole: the brass six-bolt ring lying front-on on the table at c, a disc of the worksheet
    paper inside it with the pilot's drawing faint on it (drawing = its alpha, 0 for none). Draw table(ink,
    sheet=False) first; then bolt_mark() each bolt, die_cup(), badge()."""
    ro = int(r * RING_OUT / PORT_R)
    rg = brass_ring(int(r), ro, 6, 10, 3)
    ink.paste(_shadow_of(rg, 9, shadow, (20, 12, 6)), (int(c[0] - rg.width / 2 + 9), int(c[1] - rg.height / 2 + 13)))
    ink.d.ellipse([c[0] - r - 1, c[1] - r - 1, c[0] + r + 1, c[1] + r + 1], fill=PAL["sheet"] + (255,))
    if drawing > 0:
        pilot_drawing(ink, 1.0, c, r, alpha=drawing)
    ink.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(60, 50, 40, 90), width=5)
    ink.paste(rg, (int(c[0] - rg.width / 2), int(c[1] - rg.height / 2)))


# ---------------------------------------------------------- ready-made stages ---

def seat_stage(ink, t=0.0, layer="back", calm=False, weed_lean=0.0):
    """The standing set seen from Turkey's seat, in two calls so trout can go between:
    layer='back': river, far weed, the arch's RIGHT pillar and lintel, the twig.   (then your trout that pass behind)
    layer='front': the arch's LEFT pillar and the near weed.                        (then bell(), reflection, seat_frame())
    weed_lean degrees to the right; calm=True stops every idle movement dead."""
    sw = 0.0 if calm else 1.0
    if layer == "back":
        river(ink, t, calm=calm)
        weed(ink, 250, 470, 200, weed_lean * 0.6, t, seed=3, n=4, sway=sw, dark=0.55)
        weed(ink, 716, 474, 170, weed_lean * 0.6, t, seed=4, n=4, sway=sw, dark=0.55)
        arch(ink, part="right")
        arch(ink, part="lintel")
        twig(ink)
    else:
        arch(ink, part="left")
        weed(ink, 336, 482, 120, weed_lean, t, seed=1, n=5, sway=sw)
        weed(ink, 642, 486, 150, weed_lean, t, seed=2, n=6, sway=sw)


def river_stage(ink, t=0.0, layer="back", glow=1.0, mood=None, calm=True):
    """The river-side set for bolts 4 to 6: layer='back' draws river, arch, twig and the still bell; layer='front'
    draws the tin (porthole facing us, glass glowing amber, nobody visible unless mood is given) and the near weed
    in front of it. Returns the tin's points (see tin()) from the 'front' call."""
    R = RIVER
    if layer == "back":
        river(ink, t, calm=calm)
        weed(ink, 180, 470, 210, 0, t, seed=6, n=4, sway=0 if calm else 1, dark=0.5)
        arch(ink, R["arch_c"], R["arch_w"])
        twig(ink, R["bell_hang"], span=170, scale=1.1)
        bell(ink, R["bell_hang"], R["bell_scale"])
        return None
    out = tin(ink, t=t, mood=mood, glow=glow)
    weed(ink, 250, 520, 150, 0, t, seed=7, n=5, sway=0 if calm else 1)
    weed(ink, 742, 528, 190, 0, t, seed=8, n=6, sway=0 if calm else 1)
    return out


# ------------------------------------------------------------------ self-test ---

def _still(name, fn, t=1.0):
    out = FILMS / "stills" / "c13_world"
    out.mkdir(parents=True, exist_ok=True)
    ink = Ink(t, int(t * FPS))
    ink.paper()
    fn(ink, t)
    ink.finish().save(out / f"{name}.png")
    print("still ->", out / f"{name}.png")


def _demo_table(ink, t):
    table(ink)
    sheet_ring(ink)
    tip, down = pilot_page(ink, t)
    pencil(ink, tip, lift=0 if down else 1)
    badge(ink)


def _demo_table_pieces(ink, t):
    table(ink)
    sheet_ring(ink)
    pilot_drawing(ink, 1.0, alpha=0.8)
    P = PILOT_PLACES
    trout(ink, *ring_xy(*P["fish1"]), length=P["fish1_len"] * PORT_R, angle=P["fish1_angle"], lid=0.45, shadow=0.8)
    trout(ink, *ring_xy(*P["fish2"]), length=P["fish2_len"] * PORT_R, angle=P["fish2_angle"], lid=0.45, shadow=0.8)
    bell(ink, ring_xy(*P["bell_top"]), 0.55, swing=14, clapper=-8, cord=4)
    tin(ink, (480, 420), 0.42, t, mood="freak", angle=-90, beam=0.8)
    badge(ink)


def _demo_seat(ink, t, mood="freak", calm=False):
    seat_stage(ink, t, "back", calm=calm)
    trout_on_circle(ink, PORT_C, 150, 75, 130, phase=t * 6)
    b = bell(ink, swing=16, clapper=-10, cord=-22, part="cord")
    trout(ink, *STAGE["fish2"], length=170, angle=18, lid=0.45, phase=t * 3)
    seat_stage(ink, t, "front", calm=calm)
    bell(ink, swing=16, clapper=-10, cord=-22, part="body", disc="circle")
    trout(ink, *STAGE["fish1"], length=180, angle=-4, lid=0.45, phase=t * 3)
    speech_bubble(ink, (STAGE["fish1"][0] - 70, STAGE["fish1"][1] - 30), 0.8)
    ripple_rings(ink, b["mouth"], [40, 90, 150])
    turkey_reflection(ink, mood=mood, t=t)
    bubbles(ink, (STAGE["reflection"][0] + 40, STAGE["reflection"][1] - 70), t, t0=t - 1.0)
    seat_frame(ink)
    gauge(ink, 5)
    for n in (1, 2, 3):
        bolt_mark(ink, n, lit=1.0 if n == 1 else 0.0)
    badge(ink)


def _demo_river(ink, t):
    river_stage(ink, t, "back")
    river_stage(ink, t, "front")
    badge(ink)


def _demo_turkeys(ink, t):
    ink.fill((226, 220, 204))
    for k, m in enumerate(TURKEY_MOODS):
        x, y = 110 + (k % 4) * 240, 110 + (k // 4) * 190
        turkey(ink, x, y, 150, m, t + k * 0.13, "bust", shadow=0.6)
        ink.label((x - 60, y + 80), m, 13, anchor="mm")
    turkey(ink, 830, 330, 150, "freak", t, "head", shadow=0.6)
    for k, m in enumerate(("calm", "wave", "freak", "gasp")):
        turkey(ink, 130 + k * 235, 455, 150, m, t, "full", shadow=0.6)
    badge(ink)


def _demo_props(ink, t):
    ink.fill((226, 220, 204))
    for k, kind in enumerate(BUTTONS):
        button(ink, kind, 70 + k * 90, 60, 26, pressed=0, lit=1)
        button(ink, kind, 70 + k * 90, 140, 26, pressed=1, lit=1)
        button(ink, kind, 70 + k * 90, 220, 26, pressed=0, lit=0)
        button_disc(ink, kind, 70 + k * 90, 275, 10)
    for n in range(1, 7):
        die_face(ink, n, 540 + (n - 1) * 62, 60, 48)
        die_face(ink, n, 540 + (n - 1) * 62, 130, 48, lit=0)
        die_face(ink, n, 540 + (n - 1) * 62, 190, 30, "print")
    die_cup(ink, 860, 500, 170)
    gauge(ink, 5, 720, 300, 50)
    for k, (lid, roll, bu) in enumerate(((0, None, False), (0.45, None, False), (0.8, None, False), (0, 120, True))):
        trout(ink, 130 + k * 190, 350, 170, phase=k, lid=lid, eye_roll=roll, belly_up=bu, shadow=0.7)
    speech_bubble(ink, (120, 520), 1.0)
    bell(ink, (330, 400), 1.0, swing=0)
    bell(ink, (480, 400), 1.0, swing=24, clapper=-6, cord=-30, disc="circle", flash=1)
    pencil(ink, (600, 520), 40)
    brass_arm(ink, (700, 470), 60, 150)
    badge(ink)


def _demo_card(ink, t):
    river(ink, t)
    pick_card(ink, (250, 150), "turkey", "circle", press=1.0, loop=1.0, initial="A.")
    pick_card(ink, (700, 150), "trout", None, initial="M.")
    r = pick_card(ink, (250, 400), "turkey", "circle", press=0.3, loop=0.5, lift=0.0)
    pencil(ink, r["tip"], 50)
    tin_porthole(ink, (720, 390), 105, "freak", t, shake=3)
    badge(ink)


def _demo_sweep(ink, t):
    _demo_seat(ink, t)
    o = offscreen(ink)
    _demo_river(o, t)
    sweep(ink, o.img, 0.36)
    badge(ink)


def _demo_wheel(ink, t):
    seat_stage(ink, t, "back", weed_lean=40)
    b = bell(ink, swing=-20, clapper=8, cord=30, hoist=0.6, part="cord")
    seat_stage(ink, t, "front", weed_lean=40)
    bell(ink, swing=-20, clapper=8, cord=30, hoist=0.6, part="body", disc="circle", flash=0.6)
    for k in range(7):
        trout_on_circle(ink, PORT_C, 168, k * 360 / 7 + t * 200, 118, phase=t * 14 + k, amp=12,
                        belly_up=(k in (2, 5)), eye_roll=(t * 500 + k * 60) if k % 2 else None)
    ripple_rings(ink, b["mouth"], [30, 70, 110, 160, 220])
    turkey_reflection(ink, mood="flap", t=t)
    seat_frame(ink)
    gauge(ink, 3.4, tremble=1, t=t)
    bolt_mark(ink, 2)
    badge(ink)


def _demo_end(ink, t):
    table(ink, sheet=False)
    porthole_on_table(ink)
    for n in range(1, 7):
        bolt_mark(ink, n, lit=1.0 if n <= 3 else 0.0)
    die_cup(ink, 850, 505, 150)
    badge(ink)


if __name__ == "__main__":
    _still("01_table_drawing_3s", _demo_table, 3.0)
    _still("02_table_drawing_done", _demo_table, 8.9)
    _still("03_table_pieces", _demo_table_pieces, 1.0)
    _still("04_seat_freak", _demo_seat, 1.0)
    _still("05_seat_frozen", lambda i, t: _demo_seat(i, t, "frozen", True), 1.3)
    _still("06_river_side", _demo_river, 1.0)
    _still("07_turkeys", _demo_turkeys, 0.7)
    _still("08_props", _demo_props, 1.0)
    _still("09_card_and_porthole", _demo_card, 1.0)
    _still("10_sweep", _demo_sweep, 1.0)
    _still("11_end", _demo_end, 1.0)
    _still("12_wheel", _demo_wheel, 1.0)
