"""c25 · world unit · the shared pieces for the class film of porthole 25 (Lock, the trout in the upside-down fishbowl).

Everything every scene of this film uses. Foraged: Turkey (Audubon, plate 1 of The Birds of America) and the
brook trout (Denton, 1896), both cut out and hinged here. Handmade in code: the bowl-headed walking trout (cut
paper tunic, legs, arms, glass bowl with water, brass collar, built round the foraged trout), the lock wall, the
bread-roll tin, the brass porthole, river planes, the pilot's pencil drawing, buttons, dice, the die cup, the
gauge, the pick card, the card flip, the badge.

See WORLD.md for every function. Self-test:  python3 films/swarm/c25/world.py   (stills -> films/stills/c25_world/)
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

SRC = FILMS / "sources" / "c25"

# ------------------------------------------------------------------ palette ---

PAL = dict(
    table=(118, 86, 58), table_dk=(84, 58, 38), sheet=(246, 244, 238), sheet_edge=(214, 210, 200),
    print=(52, 50, 48), pencil=(96, 96, 104), pencil_soft=(138, 138, 146),
    water_top=(150, 196, 180), water_mid=(62, 128, 126), water_deep=(20, 60, 66), shaft=(226, 236, 190),
    stone=(124, 132, 120), stone_dk=(70, 80, 74), stone_lt=(170, 176, 160),
    moss=(96, 134, 62), moss_dk=(56, 92, 46), moss_lt=(150, 176, 84),
    weed=(60, 112, 70), weed_dk=(32, 74, 54), weed_lt=(126, 164, 92),
    timber=(98, 70, 46), timber_dk=(52, 36, 24), timber_lt=(156, 122, 84), iron=(44, 46, 50),
    brass=(190, 150, 66), brass_hi=(246, 220, 140), brass_dk=(112, 82, 34), brass_line=(56, 38, 14),
    tin=(142, 160, 166), tin_dk=(52, 62, 68), wall=(50, 44, 40),
    lamp=(255, 196, 92), amber=(232, 150, 60),
    skin=(104, 108, 64), skin_dk=(58, 64, 40), skin_spot=(214, 206, 150), fin=(216, 112, 52), fin_dk=(140, 60, 30),
    canvas=(182, 150, 104), canvas_dk=(120, 92, 60), glass=(206, 236, 236), bowl_water=(84, 168, 186),
    sky=(240, 232, 206), dust=(206, 182, 140), dry_ground=(196, 170, 128),
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
GROUND = 434               # the lock floor line the walker's feet stand on (seat and river side alike)
STAGE = dict(              # Turkey's seat, looking out through the glass
    walker=(476, 434), walker_h=306,          # exactly where the pilot drew it (walker's ground point, bowl top to ground)
    reflection=(352, 392), gauge=(112, 446),  # Turkey's reflection low left in the glass; the gauge low left on the wall
)
RIVER = dict(              # river side, looking in (mirror image: the walker goes left to right, the tin sits right)
    tin_c=(660, 318), tin_scale=0.9, walker=(236, 470), walker_h=300,
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
        raise SystemExit(f"missing foraged file {p}; see films/credits/c25.json")
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
    P.setdefault("wing_scale", 0.5)
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

    wk = 1.0 if part == "full" else float(P.pop("wing_scale", 0.5))      # the bust's wings are cut smaller; a shot may ask for bigger
    wing = _tpiece("wing", int(s1000 * wk))
    ws = int(s1000 * wk) / 1000.0
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


def turkey_reflection(ink, cx=None, cy=None, height=230, mood="panic", t=0.0, alpha=0.6, clip=(PORT_C, PORT_R), part="bust", **over):
    """Turkey's reflection lying on the inside of the glass (faces right, pale, see-through), clipped to the glass.
    Draw it after the river and before seat_frame. Default place is STAGE['reflection']."""
    cx = STAGE["reflection"][0] if cx is None else cx
    cy = STAGE["reflection"][1] if cy is None else cy
    spr, (ax, ay) = turkey_sprite(mood, t, height, part, **over)
    spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    ax = spr.width - ax
    a = np.asarray(spr, np.float32).copy()
    grey = a[..., :3].mean(axis=2, keepdims=True)
    a[..., :3] = (a[..., :3] * 0.6 + grey * 0.4) * 0.66 + np.array([250, 236, 190], np.float32) * 0.4   # lamp-pale, washed by the glass
    hh = a.shape[0]
    a[..., 3] *= np.clip((hh * 0.9 - np.arange(hh)) / (hh * 0.3), 0, 1)[:, None]         # a reflection thins out downward
    one = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(0.9))
    lay = Image.new("RGBA", (ink.w, ink.h), (0, 0, 0, 0))
    ghost = one.copy()                                    # thick glass gives a second, fainter image a little to one side
    ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * 0.38)))
    lay.paste(ghost, (int(cx - ax) + 9, int(cy - ay) - 5))
    lay.alpha_composite(one, (max(0, int(cx - ax)), max(0, int(cy - ay))),
                        (max(0, -int(cx - ax)), max(0, -int(cy - ay))))
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
# Traced by eye from the child's sheet on a 1500 px enlargement of the printed ring (inner circle centre 756,756,
# radius 544). These "design" coordinates are also the coordinates the cut-paper walker is built in, so the puppet
# lies exactly over the pencil drawing.

_DC, _DR = (756.0, 756.0), 544.0
BOWL_D = dict(c=(628.0, 596.0), rx=240.0, ry=186.0, cut=742.0)      # the glass bowl in design coordinates


def _c2n(pts):
    return [((x - _DC[0]) / _DR, (y - _DC[1]) / _DR) for x, y in pts]


def _bowl_project(p):
    """Nearest point of the bowl's outline (an ellipse cut flat at the mouth) for a design point."""
    B = BOWL_D
    a = math.atan2((p[1] - B["c"][1]) / B["ry"], (p[0] - B["c"][0]) / B["rx"])
    x, y = B["c"][0] + B["rx"] * math.cos(a), B["c"][1] + B["ry"] * math.sin(a)
    if y > B["cut"]:
        hw = B["rx"] * math.sqrt(max(0.0, 1 - ((B["cut"] - B["c"][1]) / B["ry"]) ** 2))
        x, y = clamp(p[0], B["c"][0] - hw, B["c"][0] + hw), B["cut"]
    return (x, y)


def _build_pilot():
    G = []

    def add(group, pts, weight=1.0, curve=True, per=5, to=None):
        if curve and len(pts) > 2:
            pts = catmull(pts, per)
        if to == "bowl":
            tgt = [_bowl_project(p) for p in pts]
        else:
            tgt = list(pts)
        G.append(dict(group=group, pts=_c2n(pts), to=_c2n(tgt), weight=weight))

    # 1 the fish body: one long flat lens, level, nose to the left, pressed hard
    add("fish", [(447, 690), (470, 655), (520, 628), (585, 607), (660, 599), (745, 600), (830, 598), (895, 594), (925, 584)], 2.1)
    add("fish", [(455, 726), (470, 742), (505, 755), (560, 752), (625, 744), (695, 728), (765, 710), (840, 692), (905, 682)], 2.1)
    add("fish", [(560, 632), (640, 618), (730, 616), (820, 614), (900, 606)], 1.5)          # the back, gone over again: shaded dark
    add("fish", [(600, 640), (690, 630), (790, 630), (880, 622)], 1.1)
    # 2 the tail: a forked flag tipped up, the upper lobe longer
    add("tail", [(925, 584), (935, 548), (927, 512), (938, 490), (956, 502), (966, 538), (990, 558), (1025, 560), (1040, 580),
                 (1022, 620), (992, 650), (958, 670), (905, 682)], 1.8)
    # 3 back fin, the dark mouth with its teeth ticks, the fin underneath
    add("fin_mouth", [(548, 622), (562, 575), (598, 543), (630, 546), (646, 572), (655, 596)], 1.7)
    add("fin_mouth", [(447, 690), (444, 706), (462, 713), (482, 708), (502, 717), (514, 712)], 2.8)
    add("fin_mouth", [(462, 713), (457, 735), (478, 746), (520, 752)], 2.4)
    for a_, b_ in (((470, 712), (473, 723)), ((484, 709), (487, 721)), ((497, 715), (499, 726))):
        add("fin_mouth", [a_, b_], 2.0, curve=False)
    add("fin_mouth", [(500, 650), (512, 660), (505, 668)], 0.9)
    add("fin_mouth", [(572, 754), (588, 772), (632, 773), (662, 755), (692, 722)], 1.2)
    # 4 the bowl: loose overlapping loops scribbled round and round behind the head, light pressure
    add("bowl", [(800, 690), (860, 662), (886, 610), (876, 540), (840, 480), (770, 442), (680, 426), (570, 432), (470, 466),
                 (400, 532), (376, 620), (388, 700), (440, 745)], 0.55, to="bowl")
    add("bowl", [(430, 712), (392, 640), (400, 560), (450, 490), (540, 448), (650, 438), (780, 458), (852, 520), (878, 600),
                 (850, 668)], 0.55, to="bowl")
    add("bowl", [(560, 545), (650, 520), (735, 555), (790, 620), (822, 690)], 0.45, to="bowl")
    add("bowl", [(385, 690), (372, 600), (410, 510), (500, 452), (600, 430)], 0.5, to="bowl")
    # 5 the body: a tall bean hanging from the middle of the fish
    add("body", [(597, 772), (600, 830), (614, 900), (640, 962), (672, 1010), (705, 1036), (760, 1046), (820, 1045), (852, 1030)], 0.85)
    add("body", [(832, 702), (842, 755), (834, 800), (846, 860), (852, 920), (850, 975), (858, 1010), (852, 1030)], 0.85)
    # 6 two arms on the right side, stacked, each ending in a squiggle hand (and one faint rubbed line on the left)
    add("arms", [(785, 786), (802, 775), (832, 790), (872, 820), (920, 850), (940, 872), (930, 900), (900, 906), (858, 880),
                 (812, 842), (786, 812), (785, 786)], 0.85)
    add("arms", [(832, 762), (872, 746), (908, 770), (920, 812), (915, 848)], 0.7)
    add("arms", [(842, 882), (850, 940), (880, 966), (920, 960), (946, 925), (962, 920), (976, 958), (966, 985), (1000, 994),
                 (1016, 1010), (992, 1030), (952, 1046), (930, 1040), (905, 1010)], 0.85)
    add("arms", [(602, 868), (545, 928), (526, 960), (546, 971), (582, 942), (626, 884)], 0.4)
    # 7 two walking legs: the left stepping forward with a flat foot, the right trailing with the foot turned out
    add("legs", [(700, 1040), (690, 1082), (670, 1110), (640, 1118), (596, 1114), (590, 1130), (620, 1160), (662, 1165), (700, 1150),
                 (720, 1100), (736, 1046)], 0.9)
    add("legs", [(800, 960), (790, 986), (810, 1022), (840, 1070), (850, 1120), (850, 1156), (826, 1165), (820, 1186), (850, 1196),
                 (890, 1186), (900, 1150), (895, 1100), (880, 1050), (862, 1012)], 0.9)
    rs = random.Random(25)                                  # a fixed hand-wobble: the child's line is not smooth
    for st in G:
        st["pts"] = [(x + rs.gauss(0, 0.0032), y + rs.gauss(0, 0.0032)) for x, y in st["pts"]]
        st["len"] = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(st["pts"], st["pts"][1:])) + 0.02
    return G


PILOT_STROKES = _build_pilot()          # [{group, pts, to, weight, len}] in ring units (centre 0,0, inner radius 1, y down)
PILOT_GROUPS = ["fish", "tail", "fin_mouth", "bowl", "body", "arms", "legs"]            # the order the pencil goes
PILOT_TIMES = {"fish": (0.1, 1.35), "tail": (1.45, 2.15), "fin_mouth": (2.25, 2.8), "bowl": (2.9, 4.2), "body": (4.3, 5.55),
               "arms": (5.65, 6.6), "legs": (6.7, 7.8)}                                 # the board's P1, in seconds
PILOT_PLACES = dict(        # where things sit in the drawing, ring units (use ring_xy)
    walker=(-0.0202, 0.8088), walker_h=1.4449,            # the cut-paper walker laid exactly over the pencil one
    fish=(-0.026, -0.199), fish_len=1.112, fish_angle=9.0,
    bowl=(-0.235, -0.294), bowl_rx=0.441, bowl_ry=0.342, body=(-0.05, 0.22),
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
    """The drawing as it stands t seconds into the pilot's page, timed as the board's P1 strokes 1 to 7 (PILOT_TIMES).
    Returns (tip_xy, pen_down) so the caller can lay pencil(ink, tip, lift=0 if pen_down else 1)."""
    done, cur = {}, None
    for g in PILOT_GROUPS:
        a, b = PILOT_TIMES[g]
        done[g] = ramp(t, a, b)
        if a <= t < b:
            cur = g
    tip, down = pilot_drawing(ink, done, c, r, alpha)
    if cur is None:                      # between groups the pencil travels, lifted, to the next start
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
    """The small flat mark a pick leaves behind (e.g. a green triangle left on the helmet): the button's shape, no well."""
    col = BUTTONS[kind]
    pts = [(x + px + 1, y + py + 2) for px, py in _glyph_pts(kind, r)]
    ink.d.polygon(pts, fill=(20, 10, 8, int(120 * alpha)))
    pts = [(x + px, y + py) for px, py in _glyph_pts(kind, r)]
    ink.d.polygon(pts, fill=col + (int(255 * alpha),), outline=mix_color(col, (0, 0, 0), 0.5) + (int(255 * alpha),))
    ink.d.line(pts[: max(2, len(pts) // 3)], fill=mix_color(col, (255, 255, 255), 0.55) + (int(220 * alpha),), width=max(1, int(r * 0.16)))


def badge(ink, n=25):
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


def bubbles(ink, origin, t, t0=0.0, n=7, rise=120.0, spread=16.0, size=6.0, sink=False, drop_at=None, alpha=1.0, clip_y=None):
    """A puff of n bubbles that left `origin` at time t0. Outside the tin they RISE (sink=False), wobbling, and fade
    over about 2 s. sink=True sends them DOWN instead (the rule: inside the bowl bubbles sink). drop_at = a time
    after which every bubble stops rising and falls like a pebble (bolt 3: it is not wet). clip_y = bubbles above
    this y are not drawn (the hem of the lifted river)."""
    tt = t - t0
    if tt <= 0:
        return
    rs = random.Random(int(t0 * 1000) + 3)
    sgn = 1.0 if sink else -1.0
    for k in range(n):
        ox, ph, sz, sp = rs.uniform(-1, 1), rs.uniform(0, 6.28), rs.uniform(0.5, 1.15), rs.uniform(0.75, 1.15)
        age = tt - k * 0.07
        if age <= 0:
            continue
        up = min(age, (drop_at - t0 - k * 0.07) if drop_at is not None else age)
        up = max(0.0, up)
        f = clamp(up / 2.0)
        x = origin[0] + ox * spread * (0.3 + f) + 5 * math.sin(ph + up * 5)
        y = origin[1] + sgn * rise * sp * (1 - (1 - f) ** 1.6)
        a = alpha * (1 - f) ** 0.5
        if drop_at is not None and t > drop_at:
            fall = t - max(drop_at, t0 + k * 0.07)
            y += 0.5 * 900 * fall * fall                       # a pebble
            a = alpha * clamp(1.4 - fall * 1.2)
        r = size * sz * (0.7 + 0.5 * f)
        if a <= 0.02 or (clip_y is not None and y < clip_y):
            continue
        ink.d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 240, 232, int(46 * a)), outline=(240, 250, 244, int(230 * a)), width=2)
        ink.d.arc([x - r * 0.6, y - r * 0.6, x + r * 0.3, y + r * 0.3], 180, 280, fill=(255, 255, 255, int(255 * a)), width=2)


@lru_cache(maxsize=8)
def _dust_spr(seed):
    rs = random.Random(seed)
    s = 64
    pts = [(s / 2 + math.cos(a) * s * 0.36 * rs.uniform(0.7, 1.1), s / 2 + math.sin(a) * s * 0.3 * rs.uniform(0.7, 1.1))
           for a in np.linspace(0, 2 * math.pi, 11)[:-1]]
    return _paper_piece((s, s), catmull(pts + pts[:1], 4), PAL["dust"], seed=seed + 60, edge=0.3, grain=0.2, shade=(0.2, 1.0, 0.25))


def dust(ink, x, y, age, size=1.0, toward=1.0):
    """A puff of dust raised by one footfall at (x, y): five small torn scraps of tan paper that hop up and
    back (toward = +1 drifts right, -1 left), spread and are gone in 0.7 s. age = seconds since the foot landed."""
    if age <= 0 or age > 0.7:
        return
    f = age / 0.7
    rs = random.Random(int(x * 7 + y))
    for k in range(5):
        dx = toward * (10 + 34 * rs.random()) * f ** 0.6 + rs.uniform(-8, 8)
        dy = -(14 + 26 * rs.random()) * math.sin(math.pi * min(1.0, f * 1.15)) * 0.9
        sc = size * (0.35 + 0.5 * f) * rs.uniform(0.7, 1.2)
        put(ink, _dust_spr(k), x + dx * size, y + dy * size - 4, angle=rs.uniform(0, 360) + f * 90, scale=sc, alpha=clamp(1.5 * (1 - f)))


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


def gauge(ink, notches=6.0, x=None, y=None, r=46, tremble=0.0, t=0.0):
    """The air gauge: a brass dial, ivory face, E at the left stop and F at the right, six ticks, one needle.
    notches 6 = FULL, 3 = half, 0 = EMPTY (the needle resting on the pin). Give it a float and ease it down one
    whole tick per wing-beat. Default place STAGE['gauge'] (low left on the tin wall beside the glass).
    tremble 0..1 shakes the needle."""
    x = STAGE["gauge"][0] if x is None else x
    y = STAGE["gauge"][1] if y is None else y
    N = 6
    ring = brass_ring(int(r * 0.8), int(r), 0, 6, 9)
    ink.d.ellipse([x - r + 4, y - r + 7, x + r + 8, y + r + 12], fill=(0, 0, 0, 110))
    ink.d.ellipse([x - r * 0.84, y - r * 0.84, x + r * 0.84, y + r * 0.84], fill=PAL["ivory"] + (255,))
    ink.d.pieslice([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], 135, 135 + 270 / N, fill=(206, 70, 56, 150))
    for k in range(N + 1):
        a = math.radians(135 + 270 * k / N)
        p0 = (x + math.cos(a) * r * 0.56, y + math.sin(a) * r * 0.56)
        p1 = (x + math.cos(a) * r * 0.76, y + math.sin(a) * r * 0.76)
        ink.d.line([p0, p1], fill=PAL["pip"] + (255,), width=3 if k % 3 == 0 else 2)
    if r >= 26:
        f = font("mono", max(9, int(r * 0.36)))
        for ox in (0, 1):                                                   # struck twice: bold enough to read from the seat
            ink.d.text((x - r * 0.3 + ox, y + r * 0.4), "E", font=f, fill=(170, 40, 34, 255), anchor="mm")
            ink.d.text((x + r * 0.3 + ox, y + r * 0.4), "F", font=f, fill=PAL["pip"] + (255,), anchor="mm")
        ink.d.text((x, y - r * 0.34), "AIR", font=font("mono", max(8, int(r * 0.2))), fill=PAL["pip"] + (255,), anchor="mm")
    a0 = math.radians(135 - 7)                                              # the pin the needle rests on when empty
    ink.d.ellipse([x + math.cos(a0) * r * 0.6 - 2.5, y + math.sin(a0) * r * 0.6 - 2.5, x + math.cos(a0) * r * 0.6 + 2.5, y + math.sin(a0) * r * 0.6 + 2.5],
                  fill=PAL["brass_line"] + (255,))
    a = math.radians(135 + 270 * clamp(notches / N) + tremble * 3 * math.sin(t * 37))
    tipn = (x + math.cos(a) * r * 0.66, y + math.sin(a) * r * 0.66)
    tail = (x - math.cos(a) * r * 0.16, y - math.sin(a) * r * 0.16)
    wd = max(2, int(r * 0.09))
    ink.d.line([(tail[0] + 2, tail[1] + 3), (tipn[0] + 2, tipn[1] + 3)], fill=(0, 0, 0, 80), width=wd)
    ink.d.line([tail, tipn], fill=(150, 30, 26, 255), width=wd)
    hb = max(2.5, r * 0.11)
    ink.d.ellipse([x - hb, y - hb, x + hb, y + hb], fill=PAL["brass"] + (255,), outline=PAL["brass_line"] + (255,))
    ink.paste(ring, (int(x - ring.width / 2), int(y - ring.height / 2)))
    ink.d.arc([x - r * 0.74, y - r * 0.74, x + r * 0.74, y + r * 0.74], 200, 250, fill=(255, 255, 255, 110), width=max(1, int(r * 0.06)))


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
    turkey=dict(title="Turkey thinks", rows=[("triangle", "Scuba helmet"), ("circle", "Dry-air bubble")]),
    trout=dict(title="The trout think", rows=[("cross", "Giant astronaut suit"), ("square", "Bird in a bottle")]),
)
CARD_W, CARD_H = 420, 230


def pick_card(ink, c=(480, 262), side="turkey", picked=None, press=0.0, mark=0.0, scribble=0.0, angle=-2.0, alpha=1.0, initial=None, lift=0.0):
    """The pick card, a piece of the worksheet laid over the picture: the title, the two choices each with its
    controller button, and the dashed "Draw the one you pick" ring. side 'turkey' (green triangle Scuba helmet /
    red circle Dry-air bubble) or 'trout' (blue cross Giant astronaut suit / pink square Bird in a bottle).
    picked = the kind that is chosen ('triangle' for K., 'cross' for N.) or None: nothing lights.
    press 0..1 sinks and lights the picked button; the other stays dull. mark 0..1 pencils the friend's own mark
    of the picked shape in the dashed ring (K.'s small leaning triangle, N.'s big cross). scribble 0..1 colours
    the picked button in with pencil (N. coloured the cross button in). initial = 'K.' printed small in the
    corner, or None. lift 0..1 raises the card (bigger shadow) for laying down and taking away.
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
        button(lay, kind, bx, by, r=17 * K, pressed=press if on else 0.0, lit=(0.35 + 0.65 * press) if on else 0.5)
        pos[kind] = (bx / K, by / K)
    rc = (368 * K, 186 * K)
    tipc = None
    if scribble > 0 and picked in pos:
        tipc = globals()["scribble_"](lay, (pos[picked][0] * K, pos[picked][1] * K), 17 * K, scribble, weight=0.7, alpha=0.4)
    if mark > 0 and picked:
        tp = friend_mark(lay, picked, rc, (16 if picked == "triangle" else 19) * K, mark, weight=1.5 if picked == "triangle" else 1.3)
        tipc = tp if (mark < 1 or tipc is None or scribble >= 1) else tipc
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


# --------------------------------------------- pencil morph, friend marks, rings ---

def _resample(pts, n):
    """n points evenly spaced by length along a polyline."""
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    tot = sum(seg) or 1.0
    out, k, acc = [], 0, 0.0
    for q in range(n):
        want = tot * q / (n - 1)
        while k < len(seg) - 1 and acc + seg[k] < want:
            acc += seg[k]
            k += 1
        f = clamp((want - acc) / max(seg[k], 1e-9))
        out.append(lerp2(pts[k], pts[k + 1], f))
    return out


def pilot_morph(ink, f, c=PORT_C, r=PORT_R, alpha=1.0, color=None):
    """The finished pencil drawing with its own lines moved, point for point, f = 0..1 of the way into the cut-paper
    walker's outlines (Foldes change): the scribbled loops tighten onto the one glass bowl, flat at the mouth; the
    other lines stay where the pieces will lie. f=0 is the drawing as drawn. Lay walker(parts=...) pieces under it."""
    sc = r / 212.0
    g = smooth(clamp(f))
    for s in PILOT_STROKES:
        pts = [ring_xy(*lerp2(a, b, g), c, r) for a, b in zip(s["pts"], s["to"])]
        _pencil_line(ink.d, pts, lerp(s["weight"], max(s["weight"], 0.9), g), sc, alpha, color)


def _mark_strokes(kind, size):
    """The friend's own pencil mark, as strokes round (0, 0): 'triangle' small and leaning (as K. drew it),
    'cross' two long crossing strokes (as N. drew it), 'circle', 'square', 'hexagon' for completeness."""
    rs = random.Random(hash(kind) % 97 if False else {"triangle": 3, "cross": 4, "circle": 5, "square": 6, "hexagon": 7}[kind])
    j = lambda v=0.06: rs.uniform(-v, v) * size
    if kind == "triangle":
        a, b, c_ = (0.05 * size + j(), -0.55 * size), (-0.5 * size, 0.42 * size + j()), (0.56 * size, 0.5 * size + j())
        return [catmull([a, lerp2(a, b, 0.5), b, lerp2(b, c_, 0.5), c_, lerp2(c_, a, 0.55), (a[0] + 0.05 * size, a[1] - 0.08 * size)], 4)]
    if kind == "cross":
        return [catmull([(-0.62 * size, -0.8 * size), (-0.1 * size + j(), -0.05 * size), (0.66 * size, 0.86 * size)], 5),
                catmull([(0.6 * size, -0.86 * size), (0.08 * size + j(), 0.0), (-0.66 * size, 0.8 * size)], 5)]
    n = {"circle": 28, "square": 4, "hexagon": 6}[kind]
    a0 = -math.pi / 2 + (math.pi / 4 if kind == "square" else 0)
    pts = [(size * 0.7 * math.cos(a0 + 2 * math.pi * q / n) + j(0.03), size * 0.7 * math.sin(a0 + 2 * math.pi * q / n) + j(0.03))
           for q in range(n + 1)]
    return [pts]


def friend_mark(ink, kind, c, size=26, done=1.0, weight=1.3, alpha=1.0, color=None, target=None):
    """The friend's pencil mark of the picked button drawn by hand at c: kind 'triangle' or 'cross' (others work).
    size = half its height in px. done 0..1 draws it progressively. Returns the pencil point (x, y) or None."""
    d = (target or ink).d
    strokes = [[(c[0] + x, c[1] + y) for x, y in st] for st in _mark_strokes(kind, size)]
    lens = [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(st, st[1:])) for st in strokes]
    want, tip = clamp(done) * sum(lens), None
    for st, ln in zip(strokes, lens):
        if want <= 0:
            break
        n = max(2, int(len(st) * clamp(want / ln)) + 1)
        _pencil_line(d, st[:n], weight, max(1.0, size / 20.0), alpha, color)
        tip = st[min(n, len(st)) - 1]
        want -= ln
    return tip


scribble_ = None


def scribble(ink, c, r=16, done=1.0, weight=1.0, alpha=0.9, target=None, seed=1):
    """A child's pencil colouring-in over a round thing of radius r at c (N. coloured in the cross button):
    one zigzag stroke, progressive with done 0..1. Returns the pencil point."""
    rs = random.Random(seed)
    pts, n = [], 15
    for q in range(n):
        y = -r + 2 * r * q / (n - 1)
        hw = math.sqrt(max(0.0, r * r - y * y)) * rs.uniform(0.8, 1.08)
        pts.append((c[0] + (hw if q % 2 else -hw), c[1] + y + rs.uniform(-1, 1)))
    k = max(2, int(len(pts) * clamp(done)))
    if done <= 0:
        return None
    _pencil_line((target or ink).d, pts[:k], weight, max(1.0, r / 14.0), alpha)
    return pts[k - 1]


scribble_ = scribble


def crayon_ring(ink, c, rx, ry=None, color=None, done=1.0, seed=0, width=5, alpha=1.0):
    """One hand-drawn coloured ring round something (the green ring round the helmet, the blue ring round the
    suit): a wobbly loop that overshoots its start, drawn progressively with done 0..1. Returns the crayon point."""
    ry = rx if ry is None else ry
    color = color or PAL["green"]
    rs = random.Random(seed + 11)
    ph, n = rs.uniform(0, 6.28), 72
    pts = []
    for q in range(int(n * 1.07 * clamp(done)) + 1):
        a = -2.2 + 2 * math.pi * q / n
        w = 1 + 0.035 * math.sin(a * 3 + ph) + 0.02 * math.sin(a * 7 + ph * 2) + 0.03 * q / n
        pts.append((c[0] + rx * w * math.cos(a), c[1] + ry * w * math.sin(a)))
    if len(pts) < 2:
        return None
    ink.d.line(pts, fill=tuple(color) + (int(215 * alpha),), width=width, joint="curve")
    ink.d.line([(x + 1.5, y + 1.2) for x, y in pts], fill=tuple(mix_color(color, (255, 255, 255), 0.35)) + (int(110 * alpha),), width=max(1, width // 2), joint="curve")
    return pts[-1]


_TIN_HALF = [(-200, 0), (-200, -65), (-170, -95), (170, -95), (200, -65), (200, 0)]
# The bottle lies on its side with the round porthole in its neck: the porthole is the bottle's mouth, and the lip
# stops at the porthole's own rim, so whoever stands outside the glass stays outside the bottle.
_BOTTLE_HALF = [(-134, 0), (-134, -64), (-120, -64), (-118, -57), (-36, -57), (-6, -68), (26, -94), (54, -112), (192, -112),
                (218, -92), (218, 0)]


def bottle_lines(ink, c=None, scale=None, f=1.0, flip=False, angle=0.0, alpha=1.0, color=(46, 44, 50), width=3, done=1.0):
    """The tin's outline redrawn in pencil as a bottle lying on its side (Foldes change, never a fade): f=0 the line
    hugs the tin's own outline, f=1 it is a bottle whose neck and lip run out past the lamp end, body round the
    tin. Use the same c, scale, flip, angle as tin(). done 0..1 draws the line progressively. The round porthole
    stays where it is: it is the thing that holds while tin becomes bottle. Returns {'neck': (x, y), 'base': (x, y)}."""
    c = RIVER["tin_c"] if c is None else c
    scale = RIVER["tin_scale"] if scale is None else scale
    g = smooth(clamp(f))
    n = 48
    a_, b_ = _resample(_TIN_HALF, n), _resample(catmull(_BOTTLE_HALF, 3), n)
    top = [lerp2(p, q, g) for p, q in zip(a_, b_)]
    loop = top + [(x, -y) for x, y in top[::-1]]
    rs = random.Random(8)
    an = math.radians(angle)

    def M(p):
        x, y = p[0] * scale * (-1 if flip else 1), p[1] * scale
        return (c[0] + x * math.cos(an) + y * math.sin(an), c[1] - x * math.sin(an) + y * math.cos(an))
    pts = [M((x + rs.uniform(-0.7, 0.7), y + rs.uniform(-0.7, 0.7))) for x, y in loop]
    pts = pts[: max(2, int(len(pts) * clamp(done)))]
    if g > 0 and done >= 1:                                     # the glass of it: a pale sheet inside the line, no more
        lay = ink.layer()
        lay.d.polygon(pts, fill=(226, 244, 238, int(58 * alpha * g)))
        ink.paste(lay.img)
    ink.d.line(pts, fill=tuple(color) + (int(215 * alpha),), width=width, joint="curve")
    ink.d.line([(x + 1.6, y + 1.2) for x, y in pts], fill=tuple(color) + (int(95 * alpha),), width=max(1, width - 2), joint="curve")
    ink.d.line([(x - 1, y - 1.5) for x, y in pts], fill=(232, 232, 236, int(70 * alpha)), width=1)      # graphite shines a little
    if g > 0.5 and done >= 1:                                   # the lip ring and the glass's one long shine
        k = (g - 0.5) * 2
        p0, p1 = M((-120, -57)), M((-120, 57))
        ink.d.line([p0, p1], fill=tuple(color) + (int(200 * alpha * k),), width=max(1, width - 1))
        s0, s1 = M((70, -98)), M((170, -98))
        ink.d.line([s0, s1], fill=tuple(color) + (int(120 * alpha * k),), width=max(1, width - 1))
    return dict(neck=M(lerp2((-200, 0), (-134, 0), g)), base=M(lerp2((200, 0), (218, 0), g)))


# ------------------------------------------ this porthole's subject: the walker ---
# The diner trout in its upside-down fishbowl, built to the pilot's drawing: the foraged brook trout lies level
# across the top like a hat brim; a glass bowl (mouth down on a brass collar, water INSIDE) round its head; a
# cut-paper tunic hangs from its middle; two arms on the tail side; two walking legs.

_WO = (300.0, 360.0)                    # design -> walker canvas offset
_WSIZE = (860, 900)
_WANCHOR = (745.0, 1196.0)              # design: the ground point under the body
_WHEIGHT = 786.0                        # design: bowl top to ground


def _spots(d, box, n, seed, scale=1.0):
    rs = random.Random(seed)
    for _ in range(n):
        x, y = rs.uniform(box[0], box[2]), rs.uniform(box[1], box[3])
        r = rs.uniform(2.0, 4.6) * scale
        if rs.random() < 0.18:
            d.ellipse([x - r * 1.5, y - r * 1.5, x + r * 1.5, y + r * 1.5], fill=(110, 150, 190, 150))
            d.ellipse([x - r * 0.8, y - r * 0.8, x + r * 0.8, y + r * 0.8], fill=(214, 70, 50, 255))
        else:
            d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=PAL["skin_spot"] + (210,))


@lru_cache(maxsize=16)
def _limb_spr(L, w0, w1, seed):
    """A limb segment of trout-skin paper pointing +x. Pivot = (pad, h/2)."""
    pad = int(max(w0, w1) / 2 + 6)
    w, h = int(L + 2 * pad), int(max(w0, w1) + 12)
    cy = h / 2
    top = [(pad + L * f, cy - lerp(w0, w1, f) / 2) for f in np.linspace(0, 1, 6)]
    capa = [(pad + L + (w1 / 2) * math.cos(a), cy + (w1 / 2) * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, 7)]
    bot = [(pad + L * f, cy + lerp(w0, w1, f) / 2) for f in np.linspace(1, 0, 6)]
    capb = [(pad + (w0 / 2) * math.cos(a), cy + (w0 / 2) * math.sin(a)) for a in np.linspace(math.pi / 2, 3 * math.pi / 2, 7)]
    spr = _paper_piece((w, h), top + capa + bot + capb, PAL["skin"], seed=seed, edge=0.16, grain=0.2, shade=(0.0, 1.0, 0.55))
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _spots(ImageDraw.Draw(lay), (pad, cy - w1 * 0.3, pad + L, cy + w1 * 0.1), int(L / 9), seed + 3)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), spr.getchannel("A")))
    spr.alpha_composite(lay)
    return spr, (pad, cy)


@lru_cache(maxsize=4)
def _fin_spr(kind):
    """A brook-trout fin of orange paper with its white leading edge: 'foot' (long, flat, toe to -x) or 'hand'
    (a small three-lobed squiggle, fingers to +x). Returns (sprite, pivot)."""
    if kind == "foot":
        w, h, piv = 150, 64, (118, 26)
        pts = [(piv[0] + 14, 10), (piv[0] - 26, 8), (60, 14), (22, 26), (6, 40), (14, 52), (50, 56), (100, 56), (piv[0] + 22, 54), (piv[0] + 26, 30)]
        lead = [(piv[0] - 26, 9), (60, 15), (22, 27), (7, 40)]
        rays = [((piv[0], 28), (16 + 6 * k, 44 + 2 * k)) for k in range(0, 14, 3)]
    else:
        w, h, piv = 96, 84, (16, 42)
        pts = [(8, 30), (34, 22), (58, 6), (74, 10), (66, 30), (88, 32), (90, 48), (68, 52), (78, 70), (62, 78), (40, 62), (10, 56)]
        lead = [(34, 22), (58, 7), (73, 10)]
        rays = [((18, 42), (66, 14)), ((18, 42), (84, 40)), ((18, 42), (68, 72))]
    spr = _paper_piece((w, h), catmull(pts + pts[:1], 4), PAL["fin"], seed=41 if kind == "foot" else 42, edge=0.2, grain=0.2, shade=(0.4, 1.0, 0.4))
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for a, b in rays:
        d.line([a, b], fill=PAL["fin_dk"] + (150,), width=2)
    d.line(catmull(lead, 4), fill=(20, 16, 12, 230), width=7)
    d.line([(x, y - 2) for x, y in catmull(lead, 4)], fill=(250, 246, 232, 255), width=4)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), spr.getchannel("A")))
    spr.alpha_composite(lay)
    return spr, piv


@lru_cache(maxsize=1)
def _tunic_spr():
    """The bean body as a waxed-canvas diving tunic: cut paper, shaded, stitched down the front, belted."""
    D = [(597, 770), (598, 830), (612, 900), (638, 962), (670, 1010), (705, 1037), (760, 1048), (820, 1046), (854, 1030), (860, 1008),
         (852, 975), (854, 920), (848, 860), (840, 800), (846, 752), (836, 700), (770, 708), (690, 728), (630, 744)]
    pts = [(x - _WO[0], y - _WO[1]) for x, y in D]
    spr = _paper_piece(_WSIZE, catmull(pts + pts[:1], 4), PAL["canvas"], seed=25, edge=0.2, grain=0.2, shade=(1.0, 0.5, 0.5))
    lay = Image.new("RGBA", _WSIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o = lambda x, y: (x - _WO[0], y - _WO[1])
    seam = catmull([o(700, 760), (o(706, 840)), o(724, 930), o(752, 1040)], 6)
    for a, b in list(zip(seam, seam[1:]))[::2]:
        d.line([a, b], fill=PAL["canvas_dk"] + (230,), width=3)
    for k, (x, y) in enumerate(((680, 800), (688, 866), (706, 932))):         # brass buttons
        px, py = o(x, y)
        d.ellipse([px - 9, py - 7, px + 11, py + 11], fill=(40, 28, 12, 120))
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=PAL["brass"] + (255,), outline=PAL["brass_line"] + (255,), width=2)
        d.ellipse([px - 5, py - 6, px + 1, py], fill=PAL["brass_hi"] + (255,))
    belt = catmull([o(628, 952), o(700, 990), o(780, 996), o(856, 968)], 6)
    d.line(belt, fill=PAL["leather_dk"] + (255,), width=24)
    d.line([(x, y - 2) for x, y in belt], fill=PAL["leather"] + (255,), width=16)
    bx, by = o(742, 994)
    d.rounded_rectangle([bx - 16, by - 15, bx + 16, by + 15], radius=4, fill=PAL["brass"] + (255,), outline=PAL["brass_line"] + (255,), width=3)
    d.rectangle([bx - 7, by - 7, bx + 7, by + 7], fill=PAL["leather_dk"] + (255,))
    for k in range(7):                                                       # folds: soft dark creases
        x0 = 640 + k * 28
        cr = catmull([o(x0, 800 + (k % 3) * 20), o(x0 + 8, 870), o(x0 + 2, 930)], 5)
        d.line(cr, fill=PAL["canvas_dk"] + (70,), width=3)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), spr.getchannel("A")))
    spr.alpha_composite(lay)
    return spr


_BL = dict(size=(540, 400), c=(270, 206), cut=206 + (BOWL_D["cut"] - BOWL_D["c"][1]))          # the bowl's own little canvas


@lru_cache(maxsize=1)
def _bowl_static():
    w, h = _BL["size"]
    cx, cy = _BL["c"]
    rx, ry, cut = BOWL_D["rx"], BOWL_D["ry"], _BL["cut"]
    K = 2
    m = Image.new("L", (w * K, h * K), 0)
    md = ImageDraw.Draw(m)
    md.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], fill=255)
    md.rectangle([0, cut * K, w * K, h * K], fill=0)
    m = m.resize((w, h), Image.LANCZOS)
    tint = Image.new("RGBA", (w, h), PAL["glass"] + (0,))
    tint.putalpha(m.point(lambda v: int(v * 0.2)))
    # the glass in front: a dark cut edge, an inner pale edge, a long crescent shine, a small window of light
    edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(9)))
    inner = ImageChops.subtract(m.filter(ImageFilter.MinFilter(9)), m.filter(ImageFilter.MinFilter(17)))
    front = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    front.paste(Image.new("RGBA", (w, h), (24, 64, 76, 255)), (0, 0), edge.point(lambda v: int(v * 0.8)))
    front.paste(Image.new("RGBA", (w, h), (236, 250, 250, 255)), (0, 0), inner.point(lambda v: int(v * 0.42)))
    sh = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sh)
    sd.arc([cx - rx * 0.86, cy - ry * 0.84, cx + rx * 0.86, cy + ry * 0.84], 188, 252, fill=235, width=17)
    sd.arc([cx - rx * 0.78, cy - ry * 0.74, cx + rx * 0.78, cy + ry * 0.74], 300, 330, fill=150, width=8)
    sd.polygon([(cx + rx * 0.44, cy - ry * 0.2), (cx + rx * 0.62, cy - ry * 0.12), (cx + rx * 0.6, cy + ry * 0.18), (cx + rx * 0.42, cy + ry * 0.1)], fill=96)
    sh = ImageChops.multiply(sh.filter(ImageFilter.GaussianBlur(2.2)), m)
    front.paste(Image.new("RGBA", (w, h), (255, 255, 255, 255)), (0, 0), sh)
    # the brass collar the mouth sits on: a turned band with a rolled lip and five bolts
    hw = rx * math.sqrt(max(0.0, 1 - ((BOWL_D["cut"] - BOWL_D["c"][1]) / ry) ** 2)) + 16
    cw, chh = int(hw * 2), 46
    yy, xx = np.mgrid[0:chh, 0:cw].astype(np.float32)
    v = yy / chh
    lit = 0.5 + 0.75 * np.exp(-((v - 0.24) / 0.16) ** 2) + 0.25 * np.exp(-((v - 0.8) / 0.1) ** 2) - 0.3 * (v > 0.9)
    lit = lit * (0.9 + 0.2 * (vnoise((chh, cw), 30, seed=9, octaves=2))) * (1.05 - 0.25 * np.abs(xx / cw - 0.35))
    col = np.array(PAL["brass"], np.float32)[None, None] * lit[..., None]
    band = _img(col).convert("RGBA")
    bm = Image.new("L", (cw, chh), 0)
    ImageDraw.Draw(bm).rounded_rectangle([0, 0, cw - 1, chh - 1], radius=12, fill=255)
    band.putalpha(bm)
    bd = ImageDraw.Draw(band)
    bd.rounded_rectangle([0, 0, cw - 1, chh - 1], radius=12, outline=PAL["brass_line"] + (255,), width=3)
    bd.line([8, chh * 0.52, cw - 8, chh * 0.52], fill=PAL["brass_line"] + (150,), width=2)
    for k in range(5):
        x = cw * (0.1 + 0.2 * k)
        bd.ellipse([x - 7, chh * 0.74 - 6, x + 9, chh * 0.74 + 9], fill=(40, 26, 10, 140))
        bd.ellipse([x - 7, chh * 0.74 - 7, x + 7, chh * 0.74 + 7], fill=(206, 166, 82, 255), outline=(60, 42, 16, 255), width=2)
        bd.ellipse([x - 4, chh * 0.74 - 5, x, chh * 0.74 - 1], fill=PAL["brass_hi"] + (255,))
    return dict(mask=m, tint=tint, front=front, collar=band, collar_xy=(int(cx - hw), int(cut - 8)))


def _bowl_layers(water, surf_deg, wave, bub_t):
    """(back, front) RGBA layers of the bowl on its own canvas: back = glass tint + the water inside it;
    front = a thin veil of the same water (laid over the fish's head), the level water line, sinking bubbles,
    the glass's edge and shine, the brass collar."""
    S = _bowl_static()
    w, h = _BL["size"]
    cx, cy = _BL["c"]
    top, cut = cy - BOWL_D["ry"], _BL["cut"]
    sy = cut - clamp(water) * (cut - top - 8)
    a = math.radians(surf_deg)
    ux, uy = math.cos(a), math.sin(a)
    n = 30
    line = []
    for q in range(n + 1):
        s = -330 + 660 * q / n
        bump = wave * 7 * math.sin(q * 0.9 + wave * 3.0)
        line.append((cx + ux * s + uy * bump, sy + uy * s - ux * bump))
    hm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(hm).polygon(line + [(line[-1][0] - uy * 900, line[-1][1] + ux * 900), (line[0][0] - uy * 900, line[0][1] + ux * 900)], fill=255)
    wm = ImageChops.multiply(hm, S["mask"])
    back = S["tint"].copy()
    grad = np.linspace(0.85, 1.12, h)[:, None, None] * np.array(PAL["bowl_water"], np.float32)[None, None, :] * np.ones((h, w, 1), np.float32)
    wat = _img(grad).convert("RGBA")
    wat.putalpha(wm.point(lambda v: int(v * 0.62)))
    back.alpha_composite(wat)
    front = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    veil = Image.new("RGBA", (w, h), PAL["bowl_water"] + (0,))
    veil.putalpha(wm.point(lambda v: int(v * 0.26)))
    front.alpha_composite(veil)
    sl = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sl)
    sd.line(line, fill=255, width=5)
    sd.line([(x - uy * 5, y + ux * 5) for x, y in line], fill=110, width=3)
    sl = ImageChops.multiply(sl, S["mask"])
    front.paste(Image.new("RGBA", (w, h), (240, 252, 250, 255)), (0, 0), sl)
    if bub_t is not None:                                             # the rule: bubbles inside the bowl SINK
        fd = ImageDraw.Draw(front)
        rs = random.Random(31)
        span = max(20.0, cut - sy - 40)
        for k in range(7):
            x0, sp, ph, r = rs.uniform(-0.62, 0.62), rs.uniform(26, 48), rs.uniform(0, 1), rs.uniform(4, 9)
            f = ((bub_t * sp / span) + ph) % 1.0
            y = sy + 14 + f * span
            x = cx + x0 * BOWL_D["rx"] * 0.8 + 6 * math.sin(bub_t * 3 + k)
            al = int(230 * math.sin(math.pi * f) ** 0.6)
            fd.ellipse([x - r, y - r, x + r, y + r], fill=(230, 248, 246, al // 5), outline=(244, 252, 250, al), width=3)
            fd.arc([x - r * 0.55, y - r * 0.55, x + r * 0.3, y + r * 0.3], 180, 280, fill=(255, 255, 255, al), width=2)
    front.alpha_composite(S["front"])
    front.alpha_composite(S["collar"], S["collar_xy"])
    return back, front


WALKER_PARTS = ("legs", "tunic", "bowl", "fish", "arms")
_SH = {}


def _pin_sh(cv, spr, pivot, target, deg, off=(4, 6), blur=4, strength=0.42):
    """_pin with the piece's own soft shadow under it, so overlapping cut pieces read as layers."""
    key = (id(spr), blur, strength)
    if key not in _SH:
        if len(_SH) > 200:
            _SH.clear()
        pad = blur * 3
        big = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
        big.paste(spr, (pad, pad))
        _SH[key] = (_shadow_of(big, blur, strength, (20, 16, 10)), pad, spr)
    sh, pad, _ = _SH[key]
    _pin(cv, sh, (pivot[0] + pad, pivot[1] + pad), (target[0] + off[0], target[1] + off[1]), deg)
    _pin(cv, spr, pivot, target, deg)


def walker(ink, x=None, y=None, height=None, step=0.0, flip=False, lean=0.0, parts=WALKER_PARTS, phase=0.0, amp=5.0, lid=0.0,
           eye_roll=None, water=0.86, slosh=0.0, wave=0.0, bowl_bubbles=None, bowl_shift=(0.0, 0.0), bowl_tilt=0.0, squash=0.0,
           hook=0.0, swing=0.0, bob=True, alpha=1.0, shadow=0.0, lift=0.0):
    """THIS PORTHOLE'S SUBJECT: the diner trout wearing the upside-down fishbowl, as the pilot drew it.
    (x, y) = the ground point under its body (default STAGE['walker']); height = bowl top to ground in px
    (default STAGE['walker_h']). Faces and walks LEFT (seat side); flip=True faces and walks RIGHT (river side).
    step = walk phase in strides (0 = the drawing's pose: near leg forward and flat, far leg trailing, toe turned);
    advance it to walk, e.g. step=t*1.1, and move x yourself (about 0.36*height px per stride). lean = degrees
    the whole figure tips forward (+). parts = which cut pieces to lay, any of WALKER_PARTS, for laying it down
    piece by piece. phase/amp swim the fish's tail (as trout); lid, eye_roll as trout.
    The bowl: water 0..1 = how full (it is full of WATER, 0.86 leaves a sliver at the top); the water line stays
    level with the world whatever lean or bowl_tilt; slosh = degrees the surface is tipped right now and wave 0..1
    a ripple on it (drive both from a Follower so it slops and settles); bowl_bubbles = a time: bubbles inside
    the bowl sink; bowl_shift (dx, dy) in px and bowl_tilt in degrees wriggle the helmet on its collar; squash 0..1
    presses the fish's nose flat against the inside of the glass (the bowl slides back to meet it).
    hook 0..1 raises the upper arm to hook its hand under the brass collar; swing = degrees the arms swing.
    bob=True keeps the lower foot on the ground. shadow 0..1 (use ~0.8 lying on the table, 0 in water), lift 0..1
    raises it off the table (the shadow parts). Returns screen points: {'bowl': centre, 'bowl_r': (rx, ry),
    'bowl_top', 'collar': where a hand hooks it, 'nose', 'eye', 'tail', 'hand': upper hand, 'hand2', 'feet':
    [near, far] (toe points), 'ground': [near, far] foot ground contact, 'top', 'body': tunic centre}."""
    x = STAGE["walker"][0] if x is None else x
    y = STAGE["walker"][1] if y is None else y
    height = STAGE["walker_h"] if height is None else height
    s = height / _WHEIGHT
    cv = Image.new("RGBA", _WSIZE, (0, 0, 0, 0))
    o = lambda p: (p[0] - _WO[0], p[1] - _WO[1])
    pt = {}
    # ---- legs (hip, thigh, shin, fin foot); forward is -x
    legs = []
    for k, (hip, Lt, Ls) in enumerate((((722, 1022), 78, 74), ((824, 988), 94, 92))):
        ph = 2 * math.pi * (step + 0.25 + 0.5 * k)
        th = math.radians(20 * math.sin(ph) + (2 if k == 0 else -4))
        bend = math.radians(10 + 30 * max(0.0, math.cos(ph)))
        knee = (hip[0] - Lt * math.sin(th), hip[1] + Lt * math.cos(th))
        a2 = th - bend
        ank = (knee[0] - Ls * math.sin(a2), knee[1] + Ls * math.cos(a2))
        pitch = 20 * max(0.0, -math.sin(ph)) + 14 * max(0.0, math.cos(ph))
        legs.append(dict(hip=hip, knee=knee, ank=ank, pitch=pitch, k=k))
    low = max(L["ank"][1] for L in legs) + 26
    dy = (_WANCHOR[1] - low) if bob else 0.0
    if "legs" in parts:
        for L in legs[::-1]:
            for (p0, p1, w0, w1, sd) in ((L["hip"], L["knee"], 44, 34, 50 + L["k"]), (L["knee"], L["ank"], 34, 24, 52 + L["k"])):
                spr, piv = _limb_spr(int(math.hypot(p1[0] - p0[0], p1[1] - p0[1])), w0, w1, sd)
                _pin_sh(cv, spr, piv, o((p0[0], p0[1] + dy)), -math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])))
            fs, fp = _fin_spr("foot")
            _pin_sh(cv, fs, fp, o((L["ank"][0], L["ank"][1] + dy)), L["pitch"])
    for L in legs:
        pa = math.radians(L["pitch"])
        pt.setdefault("feet", []).append((L["ank"][0] - 100 * math.cos(pa), L["ank"][1] + dy + 14 + 100 * math.sin(pa)))
        pt.setdefault("ground", []).append((L["ank"][0] - 40, L["ank"][1] + dy + 28))
    # ---- tunic
    if "tunic" in parts:
        _pin_sh(cv, _tunic_spr(), (0, 0), (0, int(round(dy))), 0.0, off=(5, 7), blur=5)
    # ---- bowl (back), fish, bowl (front)
    sq = clamp(squash)
    bsx, bsy = bowl_shift[0] + 30 * sq, bowl_shift[1]
    bc = (BOWL_D["c"][0] + bsx, BOWL_D["c"][1] + bsy + dy)
    world_tilt = bowl_tilt + (-lean if flip else lean)
    if "bowl" in parts:
        back, front = _bowl_layers(water, slosh + world_tilt, wave, bowl_bubbles)
        pivot = (_BL["c"][0], _BL["cut"])
        tgt = o((bc[0], bc[1] + (_BL["cut"] - _BL["c"][1])))
        _pin(cv, back, pivot, tgt, bowl_tilt)
    FL = 608
    fc = (742.0, 648.0 + dy)
    if "fish" in parts:
        fs = trout_sprite(FL, phase, amp, lid, eye_roll)
        if sq > 0:
            wl = int(FL * 0.075)
            nw = max(3, int(wl * (1 - 0.6 * sq)))
            f2 = Image.new("RGBA", fs.size, (0, 0, 0, 0))
            f2.paste(fs.crop((wl, 0, fs.width, fs.height)), (wl, 0))
            f2.alpha_composite(fs.crop((0, 0, wl, fs.height)).resize((nw, fs.height), Image.LANCZOS), (wl - nw, 0))
            fs = f2
        if sq > 0:
            _pin(cv, fs, (fs.width / 2, fs.height / 2), o(fc), 9.0)
        else:
            _pin_sh(cv, fs, (fs.width / 2, fs.height / 2), o(fc), 9.0, off=(4, 9), blur=6, strength=0.4)
    if "bowl" in parts:
        _pin(cv, front, pivot, tgt, bowl_tilt)
    # ---- arms (both on the tail side, in front)
    arms = []
    h = clamp(hook)
    for k, (sh, Lu, Lf, au, af, hu, hf) in enumerate((((800, 792), 66, 62, 36, 34, -16, -152), ((848, 890), 72, 78, 66, 14, 66, 14))):
        sw = swing * (1 if k == 0 else -0.7)
        au2, af2 = lerp(au, hu, smooth(h)) + sw, lerp(af, hf, smooth(h)) + sw * 1.4
        sh = (sh[0], sh[1] + dy)
        el = (sh[0] + Lu * math.cos(math.radians(au2)), sh[1] + Lu * math.sin(math.radians(au2)))
        hd = (el[0] + Lf * math.cos(math.radians(af2)), el[1] + Lf * math.sin(math.radians(af2)))
        arms.append((sh, el, hd, au2, af2, k))
    if "arms" in parts:
        for sh, el, hd, au2, af2, k in arms[::-1]:
            spr, piv = _limb_spr(int(math.hypot(el[0] - sh[0], el[1] - sh[1])), 40, 34, 60 + k)
            _pin_sh(cv, spr, piv, o(sh), -au2)
            spr, piv = _limb_spr(int(math.hypot(hd[0] - el[0], hd[1] - el[1])), 34, 26, 62 + k)
            _pin_sh(cv, spr, piv, o(el), -af2)
            hs, hp = _fin_spr("hand")
            _pin_sh(cv, hs, hp, o(hd), -af2 - (0 if k == 0 else 12))
    pt["hand"], pt["hand2"] = arms[0][2], arms[1][2]
    # ---- to the screen
    an = math.radians(lean if not flip else -lean)
    ax, ay = o(_WANCHOR)

    def M(p):
        vx, vy = (p[0] - _WANCHOR[0]) * s, (p[1] - _WANCHOR[1]) * s
        if flip:
            vx = -vx
        return (x + vx * math.cos(an) + vy * math.sin(an) - 5 * lift, y - vx * math.sin(an) + vy * math.cos(an) - 16 * lift)
    im = cv.resize((max(2, int(cv.width * s)), max(2, int(cv.height * s))), Image.LANCZOS)
    px, py = ax * s, ay * s
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        px = im.width - px
    deg = lean if not flip else -lean
    if abs(deg) > 0.05:
        r = im.rotate(deg, expand=True, resample=Image.BICUBIC)
        a = math.radians(deg)
        vx, vy = px - im.width / 2, py - im.height / 2
        px = r.width / 2 + vx * math.cos(a) + vy * math.sin(a)
        py = r.height / 2 - vx * math.sin(a) + vy * math.cos(a)
        im = r
    ox, oy = int(round(x - px - 5 * lift)), int(round(y - py - 16 * lift))
    if shadow > 0:
        ink.paste(_shadow_of(im, int(5 + 5 * lift), 0.55 * shadow * alpha), (ox + int(5 + 12 * lift), oy + int(7 + 20 * lift)))
    ink.paste(im, (ox, oy), alpha)
    B = BOWL_D
    out = dict(bowl=M(bc), bowl_r=(B["rx"] * s, B["ry"] * s), bowl_top=M((bc[0], bc[1] - B["ry"])), top=M((bc[0], bc[1] - B["ry"])),
               collar=M((bc[0] + 150, B["cut"] + bsy + dy + 6)), nose=M((447 + 22 * sq, 702 + dy)), eye=M((503, 668 + dy)),
               tail=M((1036, 578 + dy)), hand=M(pt["hand"]), hand2=M(pt["hand2"]), feet=[M(p) for p in pt["feet"]],
               ground=[M(p) for p in pt["ground"]], body=M((730, 880 + dy)))
    return out


# -------------------------------------------------------------------- the lock ---

@lru_cache(maxsize=1)
def _lock_neutral():
    """The lock chamber wall and floor in neutral daylight, RGB (W+240, H): coping stones along the top, courses
    of dressed stone blocks, an algae tide line, an iron ladder, a mooring ring, the heavy timber gate at the right
    with its iron straps, and a flagstone floor. Everything above the coping is left for sky or water (alpha 0)."""
    WW = W + 240
    rs = random.Random(250)
    base = np.ones((H, WW, 3), np.float32) * np.array((150, 146, 132), np.float32)
    tex = vnoise((H, WW), 90, seed=71, octaves=4) - 0.5
    fine = vnoise((H, WW), 5, seed=72) - 0.5
    tone = np.zeros((H, WW), np.float32)
    lines = Image.new("L", (WW, H), 0)
    bev = Image.new("L", (WW, H), 128)
    ld, bd = ImageDraw.Draw(lines), ImageDraw.Draw(bev)
    top, floor_y = 74, GROUND - 34
    y, row = top, 0
    while y < floor_y:
        ch = 30 if row == 0 else rs.choice((52, 58, 64))
        y1 = min(floor_y, y + ch)
        x = -rs.uniform(0, 120)
        while x < WW:
            bw = rs.uniform(150, 230) if row == 0 else rs.uniform(96, 186)
            x1 = x + bw
            tone[int(y):int(y1), max(0, int(x)):max(0, int(x1))] = rs.uniform(-0.13, 0.13) + (0.1 if row == 0 else 0)
            j = lambda: rs.uniform(-1.5, 1.5)
            ld.line([x1 + j(), y, x1 + j(), y1], fill=255, width=3)
            bd.line([x + 3, y + 4, x1 - 3, y + 4], fill=190, width=3)
            bd.line([x + 4, y + 3, x + 4, y1 - 3], fill=170, width=3)
            bd.line([x + 3, y1 - 3, x1 - 3, y1 - 3], fill=60, width=3)
            bd.line([x1 - 4, y + 3, x1 - 4, y1 - 3], fill=80, width=3)
            if rs.random() < 0.35:                                   # a chipped corner
                cxp, cyp = (x1 - 4, y1 - 3) if rs.random() < 0.5 else (x + 4, y1 - 3)
                ld.polygon([(cxp - 12, cyp + 3), (cxp + 12, cyp + 3), (cxp + rs.uniform(-6, 6), cyp - rs.uniform(8, 16))], fill=200)
            x = x1
        ld.line([(0, y1 + rs.uniform(-1, 1)), (WW, y1 + rs.uniform(-1, 1))], fill=255, width=3)
        y, row = y1, row + 1
    a = base * (1 + tex * 0.36 + fine * 0.1 + tone)[..., None]
    a *= (np.asarray(bev.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 128.0)[..., None] ** 0.6
    mort = np.asarray(lines.filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255
    a = a * (1 - mort * 0.62)
    yy, xx = np.mgrid[0:H, 0:WW].astype(np.float32)
    tide = 250 + 26 * vnoise((1, WW), 120, seed=73, octaves=3)[0][None, :]              # algae below the tide line
    alg = np.clip((yy - tide) / 26, 0, 1) * (0.55 + 0.45 * vnoise((H, WW), 34, seed=74, octaves=3))
    a = a * (1 - alg[..., None] * 0.5) + np.array((70, 104, 58), np.float32) * alg[..., None] * 0.5
    streak = np.clip(vnoise((H, WW), 14, 300, seed=75, octaves=2) - 0.62, 0, 1) * 2.2          # rust and wet streaks
    a = a * (1 - streak[..., None] * 0.35)
    # floor: flagstones, lighter, receding
    fl = np.ones((H, WW, 3), np.float32) * np.array((164, 158, 140), np.float32) * (1 + (vnoise((H, WW), 120, 30, seed=76, octaves=3) - 0.5) * 0.3)[..., None]
    fmask = (yy >= floor_y)[..., None]
    a = np.where(fmask, fl * (0.86 + 0.3 * (yy[..., None] - floor_y) / (H - floor_y)), a)
    img = _img(a).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    d.line([0, floor_y, WW, floor_y], fill=(40, 40, 34, 230), width=5)                      # the dark foot of the wall
    d.line([0, floor_y + 5, WW, floor_y + 5], fill=(230, 226, 206, 120), width=2)
    for k, fy in enumerate((floor_y + 26, floor_y + 62, floor_y + 112)):
        d.line([0, fy, WW, fy], fill=(70, 68, 58, 170), width=2)
        d.line([0, fy + 2, WW, fy + 2], fill=(226, 220, 200, 90), width=1)
        y_next = (floor_y + 62, floor_y + 112, H + 20)[k]
        for q in range(14):
            fx = q * 110 + (k % 2) * 55 + rs.uniform(-10, 10)
            d.line([fx, fy, fx + (fx - WW / 2) * 0.12, y_next], fill=(70, 68, 58, 150), width=2)
    # the iron ladder
    lx = 716
    for xx_ in (lx, lx + 52):
        d.line([xx_ + 4, top + 12, xx_ + 4, floor_y], fill=(10, 10, 10, 120), width=8)
        d.line([xx_, top + 6, xx_, floor_y - 2], fill=PAL["iron"] + (255,), width=7)
        d.line([xx_ - 2, top + 6, xx_ - 2, floor_y - 2], fill=(110, 112, 116, 255), width=2)
    for ry_ in range(top + 30, floor_y - 10, 34):
        d.line([lx, ry_ + 4, lx + 52, ry_ + 4], fill=(10, 10, 10, 110), width=6)
        d.line([lx, ry_, lx + 52, ry_], fill=PAL["iron"] + (255,), width=6)
        d.line([lx, ry_ - 2, lx + 52, ry_ - 2], fill=(120, 122, 126, 255), width=1)
    # a mooring ring
    mx, my = 452, 200
    d.ellipse([mx - 15, my - 15, mx + 15, my + 15], fill=(60, 60, 60, 255), outline=(20, 20, 20, 255), width=2)
    d.ellipse([mx - 20, my - 2, mx + 28, my + 54], outline=(8, 8, 8, 130), width=8)
    d.ellipse([mx - 24, my - 6, mx + 24, my + 50], outline=PAL["iron"] + (255,), width=8)
    d.arc([mx - 24, my - 6, mx + 24, my + 50], 180, 300, fill=(128, 130, 134, 255), width=2)
    # the timber gate, right: heavy planks of cut brown paper, iron straps, a sluice paddle
    gx0 = 800
    for k in range(8):
        px0 = gx0 + k * 50
        pts = [(px0 + rs.uniform(0, 3), top - 24), (px0 + 49, top - 24 + rs.uniform(-2, 2)), (px0 + 49, floor_y), (px0 + rs.uniform(0, 3), floor_y)]
        col = mix_color(PAL["timber"], PAL["timber_lt"], rs.uniform(0.0, 0.5))
        pc = _paper_piece((60, H), [(p[0] - px0 + 4, p[1]) for p in pts], col, seed=90 + k, edge=0.12, grain=0.3, shade=(1.0, 0.3, 0.3))
        g = (vnoise((H, 60), 4, 160, seed=95 + k, octaves=2) - 0.5)
        arr = np.asarray(pc, np.float32)
        arr[..., :3] *= (1 + g * 0.35)[..., None]
        pc = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        d.rectangle([px0 + 6, top - 20, px0 + 56, floor_y], fill=(0, 0, 0, 90))
        img.alpha_composite(pc, (int(px0 - 4), 0))
    d = ImageDraw.Draw(img, "RGBA")
    for sy_ in (top + 40, top + 170, floor_y - 60):
        d.rectangle([gx0 - 6, sy_ + 5, WW, sy_ + 31], fill=(0, 0, 0, 100))
        d.rectangle([gx0 - 6, sy_, WW, sy_ + 24], fill=PAL["iron"] + (255,))
        d.line([gx0 - 6, sy_ + 2, WW, sy_ + 2], fill=(118, 120, 126, 255), width=2)
        for q in range(9):
            bx = gx0 + 14 + q * 50
            d.ellipse([bx - 6, sy_ + 6, bx + 6, sy_ + 18], fill=(84, 86, 90, 255), outline=(10, 10, 10, 255))
            d.ellipse([bx - 3, sy_ + 8, bx + 1, sy_ + 12], fill=(170, 172, 176, 255))
    d.rectangle([gx0 - 14, top - 24, gx0 - 2, floor_y], fill=(34, 32, 30, 255))             # the gate's shadowed recess
    al = np.asarray(img.getchannel("A")).copy()
    edge = (top + 3 * np.sin(np.arange(WW) / 23.0)).astype(int)
    for xk in range(WW):
        if xk < gx0 - 14:
            al[:edge[xk], xk] = 0
        else:
            al[:top - 24, xk] = 0
    img.putalpha(Image.fromarray(al))
    return img


@lru_cache(maxsize=4)
def _seat_plate(kind):
    """Full-frame backdrop plates (W+240 wide for a little parallax): 'wet' = the lock seen through river water,
    'dry' = the same lock standing in plain dry daylight."""
    WW = W + 240
    wall = _lock_neutral()
    if kind == "wet":
        back = _river_planes()[0].resize((WW, H), Image.BICUBIC).convert("RGBA")
        a = np.asarray(wall, np.float32)
        wm = np.array(PAL["water_mid"], np.float32)
        a[..., :3] = a[..., :3] * 0.5 * np.array((0.7, 1.0, 0.98), np.float32) + wm * 0.5
        wet = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(0.9))
        out = back.copy()
        out.alpha_composite(wet)
        yy, xx = np.mgrid[0:H, 0:WW].astype(np.float32)                      # the light shafts fall across the wall too
        sh = np.zeros((H, WW), np.float32)
        for x0, wd, gain in ((210, 50, 0.5), (430, 34, 0.34), (650, 60, 0.42), (880, 40, 0.3), (1060, 50, 0.26)):
            sh += gain * np.exp(-(((xx - x0 - yy * 0.42) / wd) ** 2)) * np.clip(1.15 - yy / H * 1.2, 0, 1)
        o = np.asarray(out.convert("RGB"), np.float32) + np.array(PAL["shaft"], np.float32) * sh[..., None] * 0.3
        deep = np.clip((yy - 300) / 400, 0, 1)[..., None]
        o = o * (1 - deep * 0.35) + np.array(PAL["water_deep"], np.float32) * deep * 0.35
        return _img(o).convert("RGB")
    sky = np.ones((H, WW, 3), np.float32) * np.array(PAL["sky"], np.float32)
    sky *= (0.95 + 0.1 * vnoise((H, WW), 200, 60, seed=81, octaves=3))[..., None]
    out = _img(sky).convert("RGBA")
    a = np.asarray(wall, np.float32)
    a[..., :3] = a[..., :3] * np.array((1.12, 1.06, 0.94), np.float32)
    yy = np.mgrid[0:H, 0:WW][0].astype(np.float32)
    fm = (yy >= GROUND - 34)[..., None]
    a[..., :3] = np.where(fm, a[..., :3] * 0.5 + np.array(PAL["dry_ground"], np.float32) * 0.58, a[..., :3])
    out.alpha_composite(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"))
    return out.convert("RGB")


def ground_lines(ink, straight=0.0, t=0.0, y0=None, alpha=1.0, clip_y=0):
    """The hatching on the lock floor. straight=0: the river's wavy hatching (pale, drifting slowly with t);
    straight=1: flat dry ground lines in brown pencil. In between the same lines straighten, point for point
    (Foldes change, bolt 3). y0 = top row (default just under GROUND). Rows above clip_y are not drawn."""
    y0 = GROUND + 12 if y0 is None else y0
    g = smooth(clamp(straight))
    col = mix_color((208, 238, 228), (112, 88, 60), g)
    rs = random.Random(6)
    for row in range(6):
        y = y0 + row * (11 + row * 2.2)
        if y < clip_y:
            continue
        x, ph = -20 + rs.uniform(0, 60), rs.uniform(0, 6.28)
        while x < W + 20:
            ln = rs.uniform(70, 190)
            pts = [(x + q * ln / 12, y + (1 - g) * (5 + row) * math.sin((x + q * ln / 12) / (22 + row * 5) + ph + t * 1.2)) for q in range(13)]
            ink.d.line(pts, fill=col + (int((120 + 70 * g) * alpha),), width=2, joint="curve")
            x += ln + rs.uniform(18, 60)


def _motes(ink, t, calm=False, clip_y=None, y_off=0.0):
    rs = random.Random(77)
    tt = 0.0 if calm else t
    for k in range(70):
        x0, y0, sp, ph = rs.uniform(0, W), rs.uniform(0, H), rs.uniform(4, 14), rs.uniform(0, 6.28)
        x = (x0 + sp * tt) % W
        y = y0 + 5 * math.sin(ph + tt * 0.7) + y_off
        r = rs.uniform(0.8, 2.2)
        a = int(rs.uniform(50, 130))
        if clip_y is not None and y > clip_y:
            continue
        ink.d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 240, 214, a))


def seat_backdrop(ink, t=0.0, lift=0.0, straight=None, shift=0.0, calm=False):
    """What is outside the glass from Turkey's seat, filling the frame: the lock (stone wall, ladder, mooring
    ring, timber gate at the right, flagstone floor) under the river. Draw it first; then walker(), bubbles,
    turkey_reflection(), seat_frame().
    lift 0..1 raises the river off the lock like a blind (bolt 3): the wet picture slides up off the top with a
    batten hem along its lower edge and plain dry daylight is left below it; lift=1 is all dry. straight = how
    far the floor hatching has straightened into dry ground lines (default: follows lift). shift px slides the
    lock sideways. Returns the hem's y (H when nothing is lifted): things above it are still wet."""
    x0 = int(-120 + shift)
    lf = clamp(lift)
    hem = H
    if lf <= 0:
        ink.img.paste(_seat_plate("wet"), (x0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        _motes(ink, t, calm)
    else:
        ink.img.paste(_seat_plate("dry"), (x0, 0))
        hem = int(round((H + 26) * (1 - lf))) - 13
        if hem > 0:
            wet = _seat_plate("wet")
            ink.img.paste(wet.crop((0, H - hem, wet.width, H)), (x0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        if hem > 0:
            _motes(ink, t, calm, clip_y=hem, y_off=-(H - hem))
        for q in range(18):                                              # the hem's cast shadow, then the batten
            ink.d.line([0, hem + 13 + q, W, hem + 13 + q], fill=(30, 24, 14, int(90 * (1 - q / 18) ** 2)))
        ink.d.rectangle([0, hem, W, hem + 13], fill=PAL["timber"] + (255,))
        ink.d.line([0, hem + 2, W, hem + 2], fill=PAL["timber_lt"] + (255,), width=2)
        ink.d.line([0, hem + 12, W, hem + 12], fill=PAL["timber_dk"] + (255,), width=2)
    ground_lines(ink, lf if straight is None else straight, t)
    return hem


def river_backdrop(ink, t=0.0, shift=0.0, calm=False, lines=True):
    """The river side, looking in: the same lock under water in MIRROR IMAGE (the gate is now at the left),
    filling the frame. Then draw tin(), walker(flip=True), trout(flip=True), badge()."""
    pl = _seat_plate("wet").transpose(Image.FLIP_LEFT_RIGHT)
    ink.img.paste(pl, (int(-120 + shift), 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    _motes(ink, t, calm)
    if lines:
        ground_lines(ink, 0.0, t)


# ---------------------------------------------------- the card flip, the empty card ---

def card_flip(ink, new_img, f, ground=None):
    """THE CUT OF THIS FILM (rule: every move is a turn-over). The whole picture is a card turned over top to
    bottom about its horizontal middle: f 0..0.5 the old picture (what is on ink now) tips away to an edge,
    f 0.5..1 the next picture (new_img, a full-frame image, e.g. offscreen(ink).img) comes round from its back.
    8 frames: f = (t - t0) * 3. Draw the old scene on ink, the new on o = w.offscreen(ink), call this, then badge()."""
    f = clamp(f)
    if f <= 0:
        return
    if f >= 1:
        ink.img.paste(new_img.convert("RGB"), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        return
    old = ink.img.copy()
    src = old if f < 0.5 else new_img.convert("RGB")
    c = abs(math.cos(math.pi * smooth(f)))
    h = max(2, int(H * c))
    wd = int(W * (0.94 + 0.06 * c))
    card = src.resize((wd, h), Image.BILINEAR)
    shade = 0.45 + 0.55 * c
    card = Image.eval(card, lambda v: int(v * shade))
    bg = _table_img(False).copy()
    bg = Image.eval(bg, lambda v: int(v * 0.55))
    x, y = (W - wd) // 2, (H - h) // 2
    d = ImageDraw.Draw(bg, "RGBA")
    d.rectangle([x + 10, y + 14 + int(30 * (1 - c)), x + wd + 10, y + h + 14 + int(30 * (1 - c))], fill=(0, 0, 0, 110))
    bg.paste(card, (x, y))
    d.line([x, y, x + wd, y], fill=(250, 246, 236, 255), width=2)              # the card's cut edges catch the light
    d.line([x, y + h, x + wd, y + h], fill=(60, 50, 40, 255), width=3)
    ink.img.paste(bg, (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


@lru_cache(maxsize=1)
def _empty_card_img():
    img = _table_img(False).copy().convert("RGBA")
    img = Image.eval(img, lambda v: int(v * 0.8))
    cw, ch = 700, 400
    tex = np.ones((ch, cw, 3), np.float32) * np.array(PAL["sheet"], np.float32) * (0.95 + 0.07 * vnoise((ch, cw), 70, seed=18, octaves=3))[..., None]
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    tex *= (1.06 - 0.22 * np.hypot((xx - cw * 0.42) / cw, (yy - ch * 0.4) / ch))[..., None]         # lit from upper left
    card = _img(tex).convert("RGBA")
    m = Image.new("L", (cw, ch), 0)
    rs = random.Random(5)
    edge = [(x, rs.uniform(0, 2.5)) for x in range(0, cw + 1, 14)] + [(cw - rs.uniform(0, 2), y) for y in range(0, ch + 1, 14)] + \
           [(x, ch - rs.uniform(0, 2.5)) for x in range(cw, -1, -14)] + [(rs.uniform(0, 2), y) for y in range(ch, -1, -14)]
    ImageDraw.Draw(m).polygon(edge, fill=255)
    card.putalpha(m)
    card = card.rotate(1.4, expand=True, resample=Image.BICUBIC)
    x, y = (W - card.width) // 2, (H - card.height) // 2 + 6
    sh = _shadow_of(card, 10, 0.7, (16, 10, 4))
    img.alpha_composite(sh, (x + 9, y + 13))
    img.alpha_composite(card, (x, y))
    return img.convert("RGB")


def empty_card(ink):
    """A BLANK ending: an empty, lit card of the worksheet's paper lying on the table, cut edge and shadow, and
    nothing on it. Fills the frame. Add only bolt_die(ink, n) and badge(ink). Never put anything else on it."""
    ink.img.paste(_empty_card_img(), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


@lru_cache(maxsize=4)
def _hexbolt_spr(r):
    rg = brass_ring(int(r * 0.2), int(r * 2.2), 1, 6, 4, start=0.0)
    R = rg.width // 2
    bx = R + (r * 0.2 + r * 2.0 * 0.55)
    return rg.crop((int(bx - r), int(R - r), int(bx + r), int(R + r)))


def bolt_die(ink, n, c=(480, 268), lit=1.0, size=64, gap=26):
    """Bolt n by itself with its die face beside it (for the blank cards and for labelling a scene): a brass hex
    bolt on the left, die face n on the right, centred on c. lit 0..1 as bolt_mark (1 = warm glow, 0 = dead).
    Returns {'bolt': (x, y), 'die': (x, y)}."""
    bx, dx = c[0] - size * 0.5 - gap / 2, c[0] + size * 0.5 + gap / 2
    br = size * 0.46
    if lit > 0:
        g = Image.new("RGBA", (int(br * 5), int(br * 5)), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([br * 1.1, br * 1.1, br * 3.9, br * 3.9], fill=PAL["lamp"] + (int(170 * lit),))
        ink.paste(g.filter(ImageFilter.GaussianBlur(br * 0.5)), (int(bx - br * 2.5), int(c[1] - br * 2.5)))
    ink.d.ellipse([bx - br + 4, c[1] - br + 6, bx + br + 6, c[1] + br + 9], fill=(0, 0, 0, 90))
    sp = _hexbolt_spr(int(br))
    msk = Image.new("L", sp.size, 0)
    ImageDraw.Draw(msk).ellipse([1, 1, sp.width - 2, sp.height - 2], fill=255)
    sp = sp.copy()
    sp.putalpha(ImageChops.multiply(sp.getchannel("A"), msk))
    ink.d.ellipse([bx - br, c[1] - br, bx + br, c[1] + br], fill=PAL["brass_dk"] + (255,), outline=PAL["brass_line"] + (255,), width=2)
    ink.paste(sp, (int(bx - sp.width / 2), int(c[1] - sp.height / 2)))
    die_face(ink, n, dx, c[1], size, "ivory", lit=lit)
    return dict(bolt=(bx, c[1]), die=(dx, c[1]))


# ---------------------------------------------------------- ready-made stages ---

def seat_scene(ink, t=0.0, walker_kw=None, turkey_kw=None, notches=3.0, bolt=None, lift=0.0, frame=True):
    """One call for the standing shot from Turkey's seat, in the fixed layer order (back to front): lock and
    river -> the walker (water inside its bowl, fish, glass) -> Turkey's reflection on the porthole glass ->
    brass rim and tin wall -> gauge -> lit bolt and die. walker_kw / turkey_kw = dicts passed to walker() /
    turkey_reflection() (None = defaults; walker_kw=False leaves the walker out). notches = the gauge (6 full,
    3 half, 0 empty). bolt = n to light that bolt with its die. Returns (walker points or None, hem y)."""
    hem = seat_backdrop(ink, t, lift=lift)
    wp = None
    if walker_kw is not False:
        wp = walker(ink, **(walker_kw or {}))
    kw = dict(mood="panic", t=t)
    kw.update(turkey_kw or {})
    turkey_reflection(ink, **kw)
    if frame:
        seat_frame(ink)
        gauge(ink, notches, t=t)
        if bolt:
            bolt_mark(ink, bolt)
    return wp, hem


def river_scene(ink, t=0.0, tin_kw=None, walker_kw=None, notches=None):
    """One call for the standing shot from the river side (mirror image): lock under water -> the tin with Turkey
    behind its porthole glass -> the walker facing right. tin_kw / walker_kw = dicts for tin() / walker()
    (walker_kw=False leaves it out). notches = draw the small dial riveted on the tin's flank at that level.
    Returns (tin points, walker points or None)."""
    river_backdrop(ink, t)
    kw = dict(t=t, mood="panic")
    kw.update(tin_kw or {})
    tp = tin(ink, **kw)
    if notches is not None:
        gx, gy = tin_dial_xy(tp)
        gauge(ink, notches, gx, gy, r=max(14, int(tp["port_r"] * 0.62)), t=t)
    wp = None
    if walker_kw is not False:
        kw = dict(x=RIVER["walker"][0], y=RIVER["walker"][1], height=RIVER["walker_h"], flip=True)
        kw.update(walker_kw or {})
        wp = walker(ink, **kw)
    return tp, wp


def tin_dial_xy(tp):
    """Where the small air dial is riveted on the tin's flank, from tin()'s returned points: on the body, low, just
    tailward of the porthole (clear of the ROLLS label)."""
    px, py = tp["port"]
    tx, ty = tp["tail"]
    return (px + (tx - px) * 0.36, py + (ty - py) * 0.36 + tp["port_r"] * 1.05)


# ------------------------------------------------------------------ self-test ---

def _still(name, fn, t=1.0):
    out = FILMS / "stills" / "c25_world"
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


def _demo_morph(ink, t):
    table(ink)
    sheet_ring(ink)
    P = PILOT_PLACES
    x, y = ring_xy(*P["walker"])
    walker(ink, x, y, P["walker_h"] * PORT_R, parts=("legs", "tunic", "bowl"), shadow=0.8)
    walker(ink, x, y, P["walker_h"] * PORT_R, parts=("fish",), shadow=0.8, lift=0.8)
    pilot_morph(ink, 0.8)
    badge(ink)


def _demo_table_puppet(ink, t):
    table(ink)
    sheet_ring(ink)
    P = PILOT_PLACES
    walker(ink, *ring_xy(*P["walker"]), P["walker_h"] * PORT_R, shadow=0.8)
    badge(ink)


def _demo_seat(ink, t, lift=0.0, **wk):
    kw = dict(step=t * 1.1, bowl_bubbles=t, slosh=6 * math.sin(t * 5), wave=0.4)
    kw.update(wk)
    wp, hem = seat_scene(ink, t, kw, dict(mood="freak"), notches=3, bolt=1, lift=lift)
    bubbles(ink, (300, 250), t, t0=t - 0.9, clip_y=None)
    badge(ink)
    return wp


def _demo_dry(ink, t):
    hem = seat_backdrop(ink, t, lift=0.72)
    wp = walker(ink, step=t * 1.1, bowl_bubbles=t)
    dust(ink, *wp["ground"][0], age=0.25)
    dust(ink, wp["ground"][1][0], wp["ground"][1][1], age=0.5)
    bubbles(ink, (640, 330), t, t0=t - 1.2, drop_at=t - 0.25)
    turkey_reflection(ink, mood="flap", t=t)
    seat_frame(ink)
    gauge(ink, 2.2, t=t)
    bolt_mark(ink, 3)
    badge(ink)


def _demo_uncomfy(ink, t):
    wp, _ = seat_scene(ink, t, dict(x=470, height=330, y=452, hook=1.0, squash=1.0, bowl_tilt=-5, slosh=9, wave=0.8, bowl_bubbles=t, lid=0.45),
                       dict(mood="gasp"), notches=2, bolt=2)
    crayon_ring(ink, wp["bowl"], wp["bowl_r"][0] * 1.12, wp["bowl_r"][1] * 1.16, PAL["green"], 0.8)
    badge(ink)


def _demo_river(ink, t):
    tp, wp = river_scene(ink, t, dict(mood="freak"), dict(lean=8, bowl_bubbles=t), notches=3)
    bottle_lines(ink, f=1.0)
    bubbles(ink, (tp["port"][0] + 60, tp["port"][1] - 90), t, t0=t - 0.8)
    badge(ink)


def _demo_astronaut(ink, t):
    river_backdrop(ink, t)
    tp = tin(ink, (610, 250), 1.35, t, mood="freak", angle=4)
    gauge(ink, 2, *tin_dial_xy(tp), r=30, t=t)
    crayon_ring(ink, (610, 250), 330, 190, PAL["blue"], 1.0, seed=2, width=6)
    walker(ink, 150, 470, 150, flip=True, step=t * 1.3, bowl_bubbles=t)
    for k, (x, y) in enumerate(((300, 420), (250, 150), (420, 480))):
        trout(ink, x, y, 120, flip=True, phase=t * 6 + k, lid=0.0)
    badge(ink)


def _demo_turkeys(ink, t):
    ink.fill((226, 220, 204))
    for k, m in enumerate(TURKEY_MOODS):
        x, y = 110 + (k % 4) * 240, 110 + (k // 4) * 190
        turkey(ink, x, y, 150, m, t + k * 0.13, "bust", shadow=0.6)
        ink.label((x - 60, y + 80), m, 13, anchor="mm")
    turkey(ink, 830, 330, 150, "freak", t, "head", shadow=0.6)
    for k, m in enumerate(("calm", "wave", "panic", "gasp")):
        turkey(ink, 130 + k * 235, 455, 150, m, t, "full", shadow=0.6)
    badge(ink)


def _demo_props(ink, t):
    ink.fill((226, 220, 204))
    for k, kind in enumerate(BUTTONS):
        button(ink, kind, 70 + k * 90, 60, 26, pressed=0, lit=1)
        button(ink, kind, 70 + k * 90, 140, 26, pressed=1, lit=1)
        button(ink, kind, 70 + k * 90, 220, 26, pressed=0, lit=0)
        friend_mark(ink, kind, (70 + k * 90, 290), 20)
    for n in range(1, 7):
        die_face(ink, n, 540 + (n - 1) * 62, 60, 48)
        die_face(ink, n, 540 + (n - 1) * 62, 130, 48, lit=0)
        die_face(ink, n, 540 + (n - 1) * 62, 190, 30, "print")
    die_cup(ink, 880, 510, 150)
    for k, lv in enumerate((6, 3, 0)):
        gauge(ink, lv, 560 + k * 100, 290, 44)
    for k, (lid, roll, bu) in enumerate(((0, None, False), (0.45, None, False), (0, 120, True))):
        trout(ink, 130 + k * 190, 370, 170, phase=k, lid=lid, eye_roll=roll, belly_up=bu, flip=k == 1, shadow=0.7)
    pencil(ink, (600, 520), 40)
    bolt_die(ink, 5, (200, 470), lit=1.0)
    bolt_die(ink, 6, (420, 470), lit=0.0)
    for k in range(4):
        dust(ink, 660 + k * 50, 440, 0.1 + k * 0.17)
    badge(ink)


def _demo_card(ink, t):
    seat_backdrop(ink, t)
    pick_card(ink, (250, 140), "turkey", "triangle", press=1.0, mark=1.0, initial="K.")
    r = pick_card(ink, (700, 140), "trout", "cross", press=1.0, mark=0.7, scribble=1.0, initial="N.")
    pencil(ink, r["tip"], 50)
    pick_card(ink, (250, 400), "turkey", None)
    tin_porthole(ink, (720, 400), 105, "freak", t, shake=3)
    badge(ink)


def _demo_flip(ink, t, f=0.3):
    _demo_seat(ink, t)
    o = offscreen(ink)
    _demo_river(o, t)
    card_flip(ink, o.img, f)
    badge(ink)


def _demo_blank(ink, t):
    empty_card(ink)
    bolt_die(ink, 5)
    badge(ink)


def _demo_end(ink, t):
    table(ink, sheet=False)
    porthole_on_table(ink)
    for n in range(1, 7):
        bolt_mark(ink, n, lit=1.0 if n <= 4 else 0.0)
    die_cup(ink, 850, 505, 150)
    badge(ink)


def _demo_walk(ink, t):
    ink.fill((226, 220, 204))
    for k in range(5):
        walker(ink, 110 + k * 185, 250, 215, step=k / 5.0, shadow=0.6, slosh=8 * math.sin(k * 1.3), wave=0.5)
    walker(ink, 130, 520, 215, flip=True, lean=12, shadow=0.6)
    walker(ink, 340, 520, 215, hook=1, squash=1, bowl_tilt=-6, shadow=0.6)
    walker(ink, 560, 520, 215, lean=-10, water=0.5, slosh=12, bowl_bubbles=1.0, shadow=0.6)
    walker(ink, 790, 520, 215, parts=("legs", "tunic", "arms"), shadow=0.6)
    badge(ink)


if __name__ == "__main__":
    import time
    _t0 = time.time()
    _still("01_table_drawing_3s", _demo_table, 3.4)
    _still("02_table_drawing_done", _demo_table, 7.9)
    _still("03_table_morph", _demo_morph, 1.0)
    _still("04_table_puppet", _demo_table_puppet, 1.0)
    _still("05_seat", _demo_seat, 1.0)
    _still("06_seat_uncomfy", _demo_uncomfy, 1.3)
    _still("07_seat_dry", _demo_dry, 1.6)
    _still("08_river_side", _demo_river, 1.0)
    _still("09_river_astronaut", _demo_astronaut, 1.0)
    _still("10_turkeys", _demo_turkeys, 0.7)
    _still("11_props", _demo_props, 1.0)
    _still("12_cards", _demo_card, 1.0)
    _still("13_flip_a", lambda i, t: _demo_flip(i, t, 0.3), 1.0)
    _still("14_flip_b", lambda i, t: _demo_flip(i, t, 0.75), 1.0)
    _still("15_blank", _demo_blank, 1.0)
    _still("16_end", _demo_end, 1.0)
    _still("17_walker_sheet", _demo_walk, 1.0)
    print("all stills in %.1f s" % (time.time() - _t0))
