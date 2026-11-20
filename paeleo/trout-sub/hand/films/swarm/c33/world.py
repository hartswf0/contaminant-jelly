"""c33 · world unit · the shared pieces for the class film of porthole 33 (Salon, "Velvet iris frame around culvert
bar shadows": tall bars across the whole glass, one spotted fish behind them, cracks in the glass).

Everything every scene of this film uses. Foraged: Turkey (Audubon, plate 1 of The Birds of America) and the brook
trout (Denton, 1896), both cut out and hinged here; the black shadow-theatre fish and the black Turkey are cut from
the outlines of those same two plates. Handmade in code: the nine card bars, the stone tunnel (torn-paper voussoirs,
ruled), the engraved teal ground, the cracks, the fog, the velvet iris, the padlock, the orange curl, the house
flats, the culvert wall and its round picture of light, the bread-roll tin, the brass porthole, river planes, the
pilot's pencil drawing, buttons, dice, the die cup, the gauge, the pick cards, the badge.

See WORLD.md for every function. Self-test:  python3 films/swarm/c33/world.py   (stills -> films/stills/c33_world/)
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

SRC = FILMS / "sources" / "c33"

# ------------------------------------------------------------------ palette ---
# The board's law: black card, the teal light, brass, the velvet red and paper white. One thing has its own
# colour: the orange curl (PAL['cheeto']). The river side adds the engraved plates' own colours.

PAL = dict(
    table=(118, 86, 58), table_dk=(84, 58, 38), sheet=(246, 244, 238), sheet_edge=(214, 210, 200),
    print=(52, 50, 48), pencil=(96, 96, 104), pencil_soft=(138, 138, 146),
    card=(13, 14, 17), card_edge=(52, 96, 96),
    teal_hi=(168, 244, 226), teal=(44, 172, 162), teal_dk=(8, 50, 56), teal_ink=(4, 26, 30),
    velvet=(122, 22, 38), velvet_dk=(54, 8, 18), velvet_hi=(186, 58, 70),
    cheeto=(244, 122, 22), cheeto_hi=(255, 196, 76), cheeto_dk=(190, 62, 10),
    water_top=(150, 196, 180), water_mid=(62, 128, 126), water_deep=(20, 60, 66), shaft=(226, 236, 190),
    stone=(124, 132, 120), stone_dk=(70, 80, 74), stone_lt=(170, 176, 160),
    weed=(60, 112, 70), weed_dk=(32, 74, 54), weed_lt=(126, 164, 92),
    iron=(44, 46, 50), silt=(92, 98, 80),
    brass=(190, 150, 66), brass_hi=(246, 220, 140), brass_dk=(112, 82, 34), brass_line=(56, 38, 14),
    tin=(142, 160, 166), tin_dk=(52, 62, 68), wall=(50, 44, 40),
    lamp=(255, 196, 92), amber=(232, 150, 60),
    green=(52, 158, 84), red=(206, 52, 46), blue=(48, 104, 196), pink=(232, 120, 164), hexamber=(236, 160, 40),
    ivory=(240, 232, 208), pip=(40, 34, 30), leather=(122, 74, 44), leather_dk=(70, 40, 24),
    badge=(28, 28, 34), white=(250, 248, 242), unlit=(92, 86, 78),
)
BUTTONS = {"triangle": PAL["green"], "circle": PAL["red"], "cross": PAL["blue"], "square": PAL["pink"],
           "hexagon": PAL["hexamber"]}
KINDS = {1: "Probable", 2: "Plausible", 3: "Preposterous", 4: "Probable", 5: "Plausible", 6: "Preposterous"}

# standard places (screen pixels). Scene units should use these so shots join.
PORT_C = (480, 262)        # centre of the round glass in every porthole shot and of the pencil ring on the table
PORT_R = 212               # radius of the glass / inner radius of the pencil ring
RING_OUT = 262             # outer radius of the brass ring / printed ring
CANT = 8.0                 # the wreck's cant in degrees: never changes after P4
BREATH_HZ = 2.0            # Turkey's heavy breathing: the one clock fog, crack bubbles and gauge ticks hang off
STAGE = dict(              # Turkey's seat, looking out through the glass
    reflection=(338, 404), reflection_h=250,  # Turkey's reflection low and left in the glass
    beak=(398, 330),                          # about where his beak meets the pane (the fog blooms from here)
    gauge=(856, 452),                         # the air gauge low right on the tin wall
    fish=(521, 282), fish_len=158, fish_angle=-17.0,   # the spotted fish where the pilot drew it
)
RIVER = dict(              # river side, looking in: tin left (nose right, down in the silt), bars middle, wall right
    tin_c=(214, 316), tin_scale=0.8, bars_x=(520, 610), wall_x=640, picture=(782, 236), picture_r=150, bed_y=440,
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
        raise SystemExit(f"missing foraged file {p}; see films/credits/c33.json")
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
    wing = cut("wing", _T_WING)
    wa = wing.getchannel("A")                                   # the wing's far edge is cut into feather fingers
    wdr = ImageDraw.Draw(wa)
    bx0, by0 = _T_BOX["wing"][:2]
    for q, (yc, dep) in enumerate(((1012, 110), (1062, 150), (1112, 170), (1162, 165), (1212, 140), (1258, 100))):
        wdr.polygon([((236 - bx0) * k, (yc - 15 - by0) * k), ((300 + dep - bx0) * k, (yc + 4 - by0) * k), ((236 - bx0) * k, (yc + 17 - by0) * k)], fill=0)
    wdr.polygon([((236 - bx0) * k, (860 - by0) * k), ((560 - bx0) * k, (860 - by0) * k), ((236 - bx0) * k, (1020 - by0) * k)], fill=0)
    wing.putalpha(wa.filter(ImageFilter.GaussianBlur(0.6)))
    _T.update(head=head, wattle=cut("wattle", _T_WATTLE), mand=cut("mand", _T_MAND, smooth_poly=False),
              body=cut("body", _T_BODY), wing=wing, k=k)
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


def turkey_reflection(ink, cx=None, cy=None, height=None, mood="shove", t=0.0, alpha=0.8, clip=(PORT_C, PORT_R), part="bust", **over):
    """Turkey's reflection lying on the inside of the glass (faces right, pale, see-through), clipped to the glass.
    Draw it after the river and before seat_frame. Default place is STAGE['reflection']."""
    cx = STAGE["reflection"][0] if cx is None else cx
    cy = STAGE["reflection"][1] if cy is None else cy
    height = STAGE["reflection_h"] if height is None else height
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
                _pencil_line(ink.d, pts, s["weight"], sc, alpha, color, s.get("wide"))
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
                    _pencil_line(ink.d, out, s["weight"], sc, alpha, color, s.get("wide"))
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


def badge(ink, n=33):
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
        f = font("mono", max(8, int(r * 0.24)))
        ink.d.text((x - r * 0.3, y + r * 0.36), "E", font=f, fill=(170, 40, 34, 255), anchor="mm")
        ink.d.text((x + r * 0.3, y + r * 0.36), "F", font=f, fill=PAL["pip"] + (255,), anchor="mm")
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
        spr, (ax, ay) = _window_turkey(mood, t, int(r * 2.0), **over)
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


def tin(ink, c=None, scale=None, t=0.0, mood=None, glow=1.0, angle=0.0, flip=False, shadow=0.7, beam=0.0, shake=0.0, alpha=1.0, dark=0.0, **over):
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
    if dark > 0:                                # the hull as a dark shape against the light
        hull = Image.new("RGBA", spr.size, (6, 22, 26, 0))
        hull.putalpha(spr.getchannel("A"))
        spr = Image.blend(spr, hull, clamp(dark))
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
    if flip:                                    # the paper label is turned back so its lettering still reads
        lb = (pad + 230 * K, pad + 20 * K, pad + 370 * K, pad + 96 * K)
        spr.paste(spr.crop(lb).transpose(Image.FLIP_LEFT_RIGHT), lb[:2])
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
        spr, (ax, ay) = _window_turkey(mood, t, int(r * 2.0), **over)
        _paste_clip(win, spr, (int(r * 1.0 - ax), int(r * 1.0 - ay)))
    edge = np.clip((np.hypot(x2 - r, y2 - r) - (r - r * 0.14)) / (r * 0.14), 0, 1) ** 2 * 170
    win.alpha_composite(Image.fromarray(np.dstack([np.zeros((2 * r, 2 * r, 3)), edge]).astype(np.uint8), "RGBA"))
    win = win.convert("RGB")
    wd = ImageDraw.Draw(win, "RGBA")
    wd.ellipse([-r * 0.3, -r * 0.75, r * 1.2, r * 0.5], fill=(210, 240, 235, 26))
    wd.arc([r * 0.1, r * 0.1, r * 1.9, r * 1.9], 200, 250, fill=(240, 252, 244, 110), width=max(2, int(r * 0.045)))
    hold = Ink(t, 0, (2 * r, 2 * r))
    hold.img, hold.d = win, wd
    cracks(hold, (r, r), r, mirror=True)                      # the same cracks, seen from the other side
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
        button(lay, kind, bx, by, r=17 * K, pressed=press if on else 0.0, lit=(0.35 + 0.65 * press) if on else 0.15)
        pos[kind] = (bx / K, by / K)
    rc = (368 * K, 186 * K)
    tipc = None
    if scribble > 0 and picked in pos:
        tipc = globals()["scribble_"](lay, (pos[picked][0] * K, pos[picked][1] * K), 17 * K, scribble, weight=1.1)
    if mark > 0 and picked:
        tp = friend_mark(lay, picked, rc, (9 if picked == "triangle" else 19) * K, mark, weight=1.3)
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




# ====================================================================== c33 ===
# Everything below is this film's own.

# ------------------------------------------------------------- breath clock ---

def breath(t):
    """Turkey's heavy breathing, 0..1: BREATH_HZ breaths a second, a quick gasp in (0 -> 1 in the first third of the
    beat) and a slower sigh out. Fog, crack bubbles, gauge ticks and the movie's flicker all hang off this clock."""
    x = (t * BREATH_HZ) % 1.0
    return math.sin(0.5 * math.pi * x / 0.32) ** 2 if x < 0.32 else math.cos(0.5 * math.pi * (x - 0.32) / 0.68) ** 2


def breath_index(t):
    """Which breath we are in (0, 1, 2 ...): breath k starts at k / BREATH_HZ seconds."""
    return int(math.floor(t * BREATH_HZ))


def shove(t, every=1.0):
    """A shove against the glass, 0..1: a sharp push at the start of each `every` seconds, then a slump."""
    x = (t / every) % 1.0
    return math.sin(math.pi * min(1.0, x / 0.4)) ** 2 if x < 0.4 else 0.0


_pose_c25 = turkey_pose
TURKEY_MOODS = TURKEY_MOODS + ("shove", "heavy", "lunge")


def turkey_pose(mood="calm", t=0.0):   # noqa: F811
    """The hinge angles for a mood at time t. Keys: neck, wattle, beak, eye, wing, ruff, shake, blur.
    This film's own moods: 'shove' (both wings flat up on the rim, shoving once a second, breathing between),
    'heavy' (still, chest and beak pumping on the breath clock), 'lunge' (neck out, wings high, beak wide)."""
    s = math.sin
    b = breath(t)
    if mood == "shove":
        p = shove(t)
        return dict(neck=-4 - 7 * p + 2 * b, wattle=16 * s(9 * t) * (0.4 + p), beak=6 + 20 * b, eye=1, wing=74 + 14 * p - 5 * b,
                    ruff=0.6 + 0.4 * b, shake=0.6 + 2.2 * p, blur=0)
    if mood == "heavy":
        return dict(neck=-2 + 5 * b, wattle=12 * s(2 * math.pi * BREATH_HZ * t - 1.2), beak=5 + 25 * b, eye=1, wing=70 - 7 * b,
                    ruff=0.5 + 0.5 * b, shake=0.5 + 0.8 * b, blur=0)
    if mood == "lunge":
        return dict(neck=-14 + 3 * s(11 * t), wattle=30 * s(10 * t), beak=30, eye=1, wing=88 + 6 * s(16 * t), ruff=1, shake=2.4, blur=0)
    return _pose_c25(mood, t)


def _silhouette(spr, color=None, eye=True):
    """A cutout turned into black card: same outline, flat colour; the white of the eye is punched through."""
    color = color or PAL["card"]
    a = np.asarray(spr)
    al = a[..., 3].astype(np.float32)
    if eye:
        white = (a[..., :3].min(2) > 222) & (a[..., 3] > 200)
        if white.any():
            wm = np.asarray(Image.fromarray((white * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
            al = al * (1 - wm)
    out = np.zeros(a.shape, np.uint8)
    out[..., :3] = color
    out[..., 3] = np.clip(al, 0, 255)
    return Image.fromarray(out, "RGBA")


def _window_turkey(mood, t, height, black=True, **over):
    """Turkey for the tin's window seen from the river: the black shape against his lamp (black=False: the plate)."""
    spr, anchor = turkey_sprite(mood, t, height, "bust", **over)
    return (_silhouette(spr) if black else spr), anchor


def turkey_shadow(ink, cx, cy, height=300, mood="shove", t=0.0, part="bust", flip=False, color=None, alpha=1.0, blur=0.0,
                  angle=0.0, eye=True, **over):
    """Turkey as a flat black shape (shadow theatre): the hinged Audubon cutout in its pose, filled with one colour,
    read by its outline alone, the eye punched through. Anchor and arguments as turkey(). blur > 0 softens it
    (a shadow thrown on a wall). Faces left unless flip."""
    spr, (ax, ay) = turkey_sprite(mood, t, height, part, **over)
    spr = _silhouette(spr, color, eye)
    if blur > 0:
        spr = spr.filter(ImageFilter.GaussianBlur(blur))
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        ax = spr.width - ax
    ox, oy = spr.width / 2 - ax, spr.height / 2 - ay
    if angle:
        a = math.radians(angle)
        ox, oy = ox * math.cos(a) + oy * math.sin(a), -ox * math.sin(a) + oy * math.cos(a)
    put(ink, spr, cx + ox, cy + oy, angle=angle, alpha=alpha)


# ------------------------------------------------------------ the pencil page ---
# Traced by eye from the child's sheet on a 1560 px enlargement of the printed ring (inner circle centre 780,790,
# radius 556). Ring units: centre (0, 0), inner radius 1, y down.

_DC, _DR = (780.0, 790.0), 556.0


def _n(p):
    return ((p[0] - _DC[0]) / _DR, (p[1] - _DC[1]) / _DR)


# the nine bars, left to right: centre line (top, middle, foot) in tracing pixels, width at top and foot, pencil
# pressure, shaded or not. Bars 2 and 7 are the two thin unshaded uprights; 8 and 9 the widest, running out past the ring.
_BARS_PX = [
    dict(line=[(322, 468), (316, 800), (328, 1128)], w=(44, 48), press=0.85, fill=1.0),
    dict(line=[(397, 398), (380, 640), (352, 1034)], w=(13, 13), press=0.5, fill=0.0),
    dict(line=[(472, 328), (484, 800), (498, 1252)], w=(44, 54), press=0.8, fill=0.9),
    dict(line=[(580, 294), (602, 800), (624, 1306)], w=(42, 62), press=1.05, fill=1.25),
    dict(line=[(728, 246), (753, 800), (781, 1320)], w=(33, 40), press=1.25, fill=1.5),
    dict(line=[(862, 246), (940, 800), (1012, 1252)], w=(44, 60), press=0.9, fill=1.0),
    dict(line=[(950, 262), (1046, 580), (1127, 1012)], w=(13, 13), press=0.45, fill=0.0),
    dict(line=[(1012, 268), (1132, 700), (1236, 1096)], w=(72, 60), press=1.0, fill=1.6),
    dict(line=[(1130, 300), (1236, 560), (1330, 806)], w=(62, 50), press=1.0, fill=1.6),
]
BARS = [dict(line=[_n(p) for p in b["line"]], w=(b["w"][0] / _DR, b["w"][1] / _DR), press=b["press"], fill=b["fill"]) for b in _BARS_PX]

# the cracks the pilot drew, as polylines in ring units: the long jagged one from upper left to the centre, its
# short branch dropping back, the long shallow arc low across the glass, two short ones at the right edge, and two
# light ones running down from the top.
CRACKS = [[_n(p) for p in pl] for pl in (
    [(498, 470), (560, 458), (628, 452), (712, 462), (756, 488), (800, 512), (846, 538), (886, 566)],
    [(886, 566), (858, 606), (830, 650), (802, 684), (770, 722), (712, 752), (650, 775)],
    [(350, 1032), (440, 1090), (560, 1124), (700, 1136), (880, 1132), (1040, 1112), (1190, 1040), (1290, 962)],
    [(1190, 556), (1250, 566), (1302, 572)],
    [(1312, 790), (1300, 850), (1336, 822)],
    [(662, 258), (652, 340), (638, 400), (626, 452)],
    [(770, 250), (818, 330), (850, 372), (885, 420)],
)]
CRACK_LEAKS = [_n(p) for p in ((628, 452), (886, 566), (650, 775), (560, 1124), (1040, 1112), (1250, 566))]   # where the air gets out


def ring_xy(u, v, c=PORT_C, r=PORT_R):
    """Ring units -> screen."""
    return (c[0] + u * r, c[1] + v * r)


def bar_line(k, v, c=None, r=None):
    """Bar k (1..9) at ring height v (-1 top .. 1 bottom): returns (u_centre, width) in ring units, or, if c and r
    are given, (x_centre, width) in screen pixels at screen height c[1] + v * r. Works beyond the ring (the card
    bars run on past the glass)."""
    b = BARS[k - 1]
    (u0, v0), (u1, v1), (u2, v2) = b["line"]
    if v <= v1:
        f = (v - v0) / (v1 - v0)
        u = u0 + (u1 - u0) * f
    else:
        f = (v - v1) / (v2 - v1)
        u = u1 + (u2 - u1) * f
    g = clamp((v - v0) / (v2 - v0))
    wd = b["w"][0] + (b["w"][1] - b["w"][0]) * g
    if c is not None:
        return (c[0] + u * r, wd * r)
    return (u, wd)


def _build_pilot():
    G = []
    rs = random.Random(33)

    def add(group, pts, weight=1.0, curve=True, per=5):
        pts = [_n(p) for p in pts]
        if curve and len(pts) > 2:
            pts = catmull(pts, per)
        G.append(dict(group=group, pts=pts, weight=weight))

    # the bars: two long downstrokes close together, not parallel, then quick side-of-the-lead scribble between
    for k, b in enumerate(_BARS_PX, 1):
        (x0, y0), (x1, y1), (x2, y2) = b["line"]
        w0, w1 = b["w"]
        wm = (w0 + w1) / 2
        g = "bar%d" % k
        for sgn in (-1, 1):
            add(g, [(x0 + sgn * w0 / 2 + rs.uniform(-3, 3), y0 + rs.uniform(-10, 10)), (lerp(x0, x1, 0.5) + sgn * w0 / 2 + rs.uniform(-4, 4), lerp(y0, y1, 0.5)),
                    (x1 + sgn * wm / 2 + rs.uniform(-4, 4), y1), (lerp(x1, x2, 0.5) + sgn * w1 / 2 + rs.uniform(-4, 4), lerp(y1, y2, 0.5)),
                    (x2 + sgn * w1 / 2 + rs.uniform(-3, 3), y2 + rs.uniform(-10, 14))], b["press"])
        if b["fill"] > 0:                                           # shading: the side of the lead, then quick strokes along the bar
            def at(f, off):
                if f < 0.5:
                    x, y, w_ = lerp(x0, x1, f * 2), lerp(y0, y1, f * 2), lerp(w0, wm, f * 2)
                else:
                    x, y, w_ = lerp(x1, x2, f * 2 - 1), lerp(y1, y2, f * 2 - 1), lerp(wm, w1, f * 2 - 1)
                return (x + off * w_ * 0.5, y)
            G.append(dict(group=g, pts=[_n(at(i / 12, rs.uniform(-0.08, 0.08))) for i in range(13)], weight=0.2 * b["fill"],
                          wide=wm / _DR * 212 * 0.72))
            for q in range(int(3 + 3 * b["fill"])):
                f0 = rs.uniform(0.0, 0.5)
                f1 = min(1.0, f0 + rs.uniform(0.25, 0.6))
                off = rs.uniform(-0.7, 0.7)
                n = 7
                add(g, [(lambda p: (p[0] + rs.uniform(-2.5, 2.5), p[1]))(at(lerp(f0, f1, i / n), off + rs.uniform(-0.12, 0.12))) for i in range(n + 1)],
                    rs.uniform(0.3, 0.55) * min(1.3, b["fill"]), curve=False)
    # the fish, small, right of centre and a little below the middle, nose down to the left. Drawn after the bars,
    # so its outline stops at the bar in front of it and starts again on the other side.
    top = [(688, 880), (705, 855), (740, 825), (790, 795), (850, 765), (905, 748), (940, 748), (985, 765), (1040, 772)]
    bot = [(688, 880), (700, 905), (740, 906), (800, 896), (860, 880), (920, 850), (975, 812), (1040, 790)]
    for line in (top, bot):
        dense = catmull(line, 8)
        run = []
        for p in dense:
            u, v = _n(p)
            hid = False
            for kb in (5, 6):
                ub, wb = bar_line(kb, v)
                if abs(u - ub) < wb / 2:
                    hid = True
            if hid:
                if len(run) > 1:
                    G.append(dict(group="fish", pts=[_n(q) for q in run], weight=1.1))
                run = []
            else:
                run.append(p)
        if len(run) > 1:
            G.append(dict(group="fish", pts=[_n(q) for q in run], weight=1.1))
    add("fish", [(1040, 772), (1046, 745), (1054, 720), (1062, 742), (1068, 758), (1086, 778), (1106, 796), (1072, 800), (1040, 790)], 1.1, per=3)
    add("fish", [(775, 808), (830, 770), (872, 748), (926, 752), (868, 772), (812, 794), (775, 808)], 1.3, per=3)      # the dark fin on top
    add("fish", [(790, 800), (850, 766), (910, 756)], 1.2)
    add("fish", [(800, 896), (814, 913), (840, 888)], 0.9)
    add("fish", [(709, 870), (715, 869), (716, 875), (710, 876), (709, 870)], 1.5, curve=False)                          # the eye
    for (x, y) in ((800, 810), (822, 814), (846, 801), (880, 822), (906, 792), (926, 806), (872, 842), (842, 838), (815, 846)):
        add("spots", [(x - 3, y - 1), (x + 3, y + 2), (x - 1, y + 3)], 1.25, curve=False)
    # the cracks, fast and light, zigzag
    for pl in CRACKS:
        G.append(dict(group="cracks", pts=list(pl), weight=0.6))
    add("cracks", [(270, 680), (255, 760), (266, 830), (232, 890)], 0.45)                 # the squiggle at the left edge
    add("cracks", [(1040, 1000), (1078, 1040), (1110, 992)], 0.4)
    for st in G:
        st["pts"] = [(x + rs.gauss(0, 0.0028), y + rs.gauss(0, 0.0028)) for x, y in st["pts"]]
        st["len"] = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(st["pts"], st["pts"][1:])) + 0.02
    return G


PILOT_STROKES = _build_pilot()          # [{group, pts, weight, len}] in ring units (centre 0,0, inner radius 1, y down)
PILOT_GROUPS = ["bar%d" % k for k in range(1, 10)] + ["fish", "spots", "cracks"]      # the order the pencil goes
PILOT_TIMES = dict(bar1=(1.2, 1.52), bar2=(1.6, 1.78), bar3=(1.88, 2.22), bar4=(2.32, 2.7), bar5=(2.8, 3.2), bar6=(3.3, 3.62),
                   bar7=(3.7, 3.86), bar8=(3.94, 4.26), bar9=(4.32, 4.6), fish=(4.7, 5.85), spots=(5.9, 6.35),
                   cracks=(6.5, 7.6))                                                  # the board's P1 to P3, in seconds
PILOT_PLACES = dict(        # where things sit in the drawing, ring units (use ring_xy)
    fish=(0.194, 0.094), fish_len=0.75, fish_angle=-17.0,       # centre of the fish, nose to tail, nose down-left
    fish_nose=(-0.165, 0.162), fish_tail=(0.585, 0.01),
    crossbar_v=0.60,                                           # where the card crossbar runs (the pilot drew none)
)


def _pencil_line(d, pts, weight, sc, alpha=1.0, color=None, wide=None):
    col = color or PAL["pencil"]
    if wide:                                                  # the side of the lead: a broad, pale smear
        d.line(pts, fill=col + (int(clamp(150 * weight, 0, 120) * alpha),), width=max(2, int(round(wide * sc))), joint="curve")
        return
    w = max(1, int(round(1.9 * weight * sc)))
    a = int(clamp(60 + 135 * weight, 0, 245) * alpha)
    d.line(pts, fill=col + (a,), width=w, joint="curve")
    if weight >= 1.0 and len(pts) > 1:                        # a second, lighter pass: graphite is never one clean line
        d.line([(x + 0.7 * sc, y + 0.5 * sc) for x, y in pts], fill=col + (int(a * 0.35),), width=1)


# ------------------------------------------------------------- the teal light ---

@lru_cache(maxsize=8)
def _ground_img(c, r, cant_q, dim_q):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dim = dim_q / 20.0
    d = np.hypot(xx - c[0], (yy - (c[1] - 0.04 * r)) * 1.08) / r
    lum = np.clip(1.04 * np.exp(-(d / 0.6) ** 2) + 0.10 + 0.05 * (vnoise((H, W), 90, seed=61, octaves=2) - 0.5), 0, 1) * dim
    a = math.radians(cant_q)
    yr = (yy - c[1]) * math.cos(a) + (xx - c[0]) * math.sin(a)
    wav = 1.8 * np.sin(xx / 41.0 + yr / 70.0) + 3.0 * (vnoise((H, W), 140, 30, seed=62) - 0.5)
    ph = ((yr + wav) / 5.0) % 1.0
    thick = 0.16 + 0.66 * (1 - lum)                                  # an engraver's line: heavier where it is darker
    line = np.clip((thick - np.abs(ph - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    hi, dk, ik = (np.array(PAL[k], np.float32) for k in ("teal_hi", "teal_dk", "teal_ink"))
    mid = np.array(PAL["teal"], np.float32)
    l3 = lum[..., None]
    base = np.where(l3 < 0.5, dk + (mid - dk) * (l3 / 0.5), mid + (hi - mid) * ((l3 - 0.5) / 0.5))
    out = base * (1 - line[..., None] * 0.7) + ik * line[..., None] * 0.7
    return _img(out).convert("RGB")


def glow_ground(ink, c=PORT_C, r=PORT_R, cant=CANT, dim=1.0):
    """The lit ground behind everything on Turkey's side: the teal light, brightest behind the middle of the glass,
    engraved with fine horizontal ruled lines (heavier where darker) that lie at the wreck's cant. Fills the frame.
    dim 0..1 turns the light down."""
    ink.img.paste(_ground_img((int(c[0]), int(c[1])), int(r), int(round(cant)), int(round(clamp(dim) * 20))), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _wedge(c, r0, r1, a0, a1, jit=0.0, rs=None, n=7):
    rs = rs or random.Random(0)
    j = lambda: rs.uniform(-jit, jit)
    pts = [(c[0] + (r1 + j()) * math.cos(lerp(a0, a1, q / n)), c[1] + (r1 + j()) * math.sin(lerp(a0, a1, q / n))) for q in range(n + 1)]
    pts += [(c[0] + (r0 + j()) * math.cos(lerp(a1, a0, q / n)), c[1] + (r0 + j()) * math.sin(lerp(a1, a0, q / n))) for q in range(n + 1)]
    return pts


@lru_cache(maxsize=6)
def _stones(r, r0f, r1f, n, seed):
    """n separate torn-paper voussoirs for a ring: list of (RGBA sprite on a (2R, 2R) canvas, mid angle)."""
    R = int(r * r1f + 14)
    S = 2 * R
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rad = np.hypot(xx - R, yy - R)
    rs = random.Random(seed)
    grain = vnoise((S, S), 22, seed=seed + 1, octaves=3) - 0.5
    ruled = np.clip((0.42 - np.abs(((rad + 1.5 * np.sin(np.arctan2(yy - R, xx - R) * 9)) / 4.4) % 1.0 - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    out = []
    for k in range(n):
        a0 = 2 * math.pi * (k + 0.03 + rs.uniform(0, 0.03)) / n + math.pi / 2
        a1 = 2 * math.pi * (k + 0.97 - rs.uniform(0, 0.03)) / n + math.pi / 2
        r0 = r * r0f + rs.uniform(-0.02, 0.025) * r
        r1 = r * r1f + rs.uniform(-2, 6)
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).polygon(_wedge((R, R), r0, r1, a0, a1, 1.6, rs), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(0.7))
        tone = rs.uniform(0.75, 1.2)
        col = np.array((52, 70, 72), np.float32) * tone * (1 + grain[..., None] * 0.5)
        f = np.clip((rad - r0) / max(1.0, r1 - r0), 0, 1)
        col = col * (1.25 - 0.6 * f[..., None])                                         # lit from the tunnel's light, inside out
        col = col * (1 - 0.62 * ruled[..., None]) + np.array(PAL["teal_ink"], np.float32) * 0.62 * ruled[..., None]
        ma = np.asarray(m, np.float32) / 255
        inner = np.asarray(m.filter(ImageFilter.MinFilter(5)), np.float32) / 255
        rim = np.clip(ma - inner, 0, 1) * (f < 0.5)
        col = col * (1 - rim[..., None] * 0.75) + np.array(PAL["teal_hi"], np.float32) * rim[..., None] * 0.6
        sp = Image.fromarray(np.dstack([np.clip(col, 0, 255), ma * 255]).astype(np.uint8), "RGBA")
        box = sp.getbbox()
        out.append((sp.crop(box), box[0] - R, box[1] - R, (a0 + a1) / 2))
    return out


def stone_ring(ink, done=1.0, c=PORT_C, r=PORT_R, inner=0.80, outer=1.05, n=16, seed=4, shadow=0.7):
    """The stone mouth of the tunnel round the bars: n separate torn-paper voussoirs, ruled along the curve, lit on
    their inner edge, laid one by one clockwise from six o'clock. done 0..1 = how much of the ring is built (the
    stone being laid slides in from outside the glass on its own plane). The ring covers ring radii inner..outer of
    r (outer runs under the brass). Returns the number of stones in place."""
    st = _stones(int(r), float(inner), float(outer), int(n), int(seed))
    want = clamp(done) * n
    for k, (sp, ox, oy, am) in enumerate(st):
        f = clamp(want - k)
        if f <= 0:
            break
        off = (1 - smooth(f)) * r * 0.42
        x, y = int(c[0] + ox + off * math.cos(am)), int(c[1] + oy + off * math.sin(am))
        if shadow > 0:
            ink.paste(_shadow_of(sp, 4, 0.5 * shadow, (0, 10, 12)), (x - 4, y + 5))
        ink.paste(sp, (x, y))
    return int(want)


@lru_cache(maxsize=6)
def _tunnel_img(r, hole_q):
    R = int(r * 1.12)
    S = 2 * R
    hole = hole_q / 100.0
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rad = np.hypot(xx - R, yy - R) / r
    th = np.arctan2(yy - R, xx - R)
    f = np.clip((rad - hole) / (1.0 - hole), 0, 1)                           # 0 at the far mouth, 1 at the glass
    lum = (1 - f) ** 1.5 * 0.55 + 0.05
    course = np.floor(f * 6)
    joint = np.abs(((th / (2 * math.pi) * 18 + course * 0.5) % 1.0) - 0.5) < 0.035        # stone joints, staggered by course
    bed = np.abs((f * 6) % 1.0 - 0.5) > 0.44
    ruled = np.clip((0.2 + 0.55 * (1 - lum) - np.abs(((rad * r + 1.2 * np.sin(th * 7)) / 4.0) % 1.0 - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    dk, mid, ik = (np.array(PAL[k], np.float32) for k in ("teal_dk", "teal", "teal_ink"))
    base = dk * 0.75 + (mid - dk * 0.75) * lum[..., None]
    base = base * (1 - 0.6 * ruled[..., None]) + ik * 0.6 * ruled[..., None]
    base = base * (1 - 0.7 * (joint | bed)[..., None])
    al = np.clip((rad - hole) * r / 2.0, 0, 1) * 255
    img = Image.fromarray(np.dstack([np.clip(base, 0, 255), al]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    rh = hole * r
    d.ellipse([R - rh - 2, R - rh - 2, R + rh + 2, R + rh + 2], outline=PAL["teal_hi"] + (150,), width=2)     # the far mouth's lit lip
    return img


def tunnel(ink, c=PORT_C, r=PORT_R, hole=0.5, shift=(0.0, 0.0), scale=1.0):
    """The far plane of the stone tunnel: its ruled, coursed wall running away from the glass to a far round mouth
    (radius hole * r) through which the lit ground shows. Lay it over glow_ground. shift (dx, dy) slides the plane
    (parallax); scale > 1 pushes in (bolt 3)."""
    img = _tunnel_img(int(r), int(round(hole * 100)))
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.BILINEAR)
    ink.paste(img, (int(c[0] + shift[0] - img.width / 2), int(c[1] + shift[1] - img.height / 2)))


# -------------------------------------------------------------------- the bars ---

def _bar_poly(k, c, r, v0=-1.12, v1=1.12, steps=12, min_w=0.036, rs=None, dx=0.0, squeeze=1.0):
    L, Rr = [], []
    for q in range(steps + 1):
        v = lerp(v0, v1, q / steps)
        u, wd = bar_line(k, v)
        wd = max(wd, min_w) * squeeze
        j = (rs.uniform(-0.004, 0.004) if rs else 0.0)                    # card cut by hand: a little out of true
        L.append((c[0] + (u - wd / 2 + j) * r + dx, c[1] + v * r))
        Rr.append((c[0] + (u + wd / 2 + j) * r + dx, c[1] + v * r))
    return L, Rr


def bars(ink, only=None, c=PORT_C, r=PORT_R, style="card", slide=None, swing=None, shift=(0.0, 0.0), alpha=1.0, shadow=0.6,
         v0=-1.12, v1=1.12, color=None):
    """The grating: the nine upright bars the pilot drew, each its own cut piece on its own layer, fanning like a
    hand (not upright, not parallel), numbered 1..9 left to right. only = which bars to draw (default all nine), in
    the order given. style 'card' = black card with a faint lit edge (Turkey's side); 'iron' = rusted iron with
    ruled lines (river side); 'shade' = the bars' shadows as soft dark bands (colour = color or teal ink).
    slide = {k: 0..1}: bar k is slid down into place from above the glass (0 = out of sight, 1 = seated).
    swing = {k: -1..1}: bar k swings like a gate leaf, toward its left (negative) or right (positive) neighbour,
    narrowing as it turns edge-on. shift slides the whole plane. v0, v1 = where the bars start and end (ring units).
    Draw the fish BEFORE the bars: the bars are in front of it. Returns {k: (x_top, x_mid, x_foot)} on screen."""
    only = list(range(1, 10)) if only is None else list(only)
    slide = slide or {}
    swing = swing or {}
    cc = (c[0] + shift[0], c[1] + shift[1])
    out = {}
    for k in only:
        rs = random.Random(330 + k)
        f = smooth(clamp(slide.get(k, 1.0)))
        dy = -(1 - f) * 2.3 * r
        sw = swing.get(k, 0.0)
        dx = sw * 0.11 * r
        L, Rr = _bar_poly(k, (cc[0], cc[1] + dy), r, v0, v1, rs=rs, dx=dx, squeeze=1 - 0.6 * abs(sw))
        poly = L + Rr[::-1]
        A = int(255 * alpha)
        if style == "shade":
            col = color or PAL["teal_ink"]
            ink.d.polygon(poly, fill=col + (int(150 * alpha),))
            ink.d.line(L, fill=col + (int(70 * alpha),), width=3)
            ink.d.line(Rr, fill=col + (int(70 * alpha),), width=3)
        elif style == "iron":
            ink.d.polygon([(x + 5, y + 4) for x, y in poly], fill=(4, 16, 18, int(90 * shadow * alpha)))
            base = (58, 56, 54)
            ink.d.polygon(poly, fill=base + (A,))
            n = max(2, int((Rr[0][0] - L[0][0]) / 3))
            for q in range(1, n):                                           # ruled along the bar, darker to the right
                g = q / n
                pl = [lerp2(a, b, g) for a, b in zip(L, Rr)]
                col = mix_color((150, 140, 124), (16, 14, 14), g ** 0.7)
                ink.d.line(pl, fill=col + (int(A * 0.8),), width=1)
            for q in range(5):                                              # rust blooms
                i = rs.randrange(1, len(L) - 1)
                p = lerp2(L[i], Rr[i], rs.uniform(0.2, 0.8))
                rr = rs.uniform(2, 5)
                ink.d.ellipse([p[0] - rr, p[1] - rr * 1.8, p[0] + rr, p[1] + rr * 1.8], fill=(126, 72, 40, int(150 * alpha)))
            ink.d.line(L, fill=(196, 190, 170, int(200 * alpha)), width=1)
            ink.d.line(Rr, fill=(10, 10, 10, A), width=2)
        else:
            if shadow > 0:
                ink.d.polygon([(x + 4, y + 3) for x, y in poly], fill=PAL["teal_ink"] + (int(110 * shadow * alpha),))
            ink.d.polygon(poly, fill=(color or PAL["card"]) + (A,))
            ink.d.line(L, fill=PAL["card_edge"] + (int(150 * alpha),), width=1)       # the cut edge catches the light
        mid = len(L) // 2
        out[k] = ((L[0][0] + Rr[0][0]) / 2, (L[mid][0] + Rr[mid][0]) / 2, (L[-1][0] + Rr[-1][0]) / 2)
    return out


def crossbar(ink, c=PORT_C, r=PORT_R, v=None, style="card", cant=2.0, thick=0.05, shift=(0.0, 0.0), alpha=1.0):
    """The one horizontal crossbar the uprights are fixed to (the padlock hangs on it, the curl lodges on it), at
    ring height v (default PILOT_PLACES['crossbar_v']). Draw it BEFORE bars(). Returns a function y_at(x) giving the
    crossbar's top edge on screen."""
    v = PILOT_PLACES["crossbar_v"] if v is None else v
    cx, cy = c[0] + shift[0], c[1] + shift[1] + v * r
    s = math.tan(math.radians(cant))
    h = thick * r
    x0, x1 = cx - 1.2 * r, cx + 1.2 * r
    poly = [(x0, cy + (x0 - cx) * s - h / 2), (x1, cy + (x1 - cx) * s - h / 2), (x1, cy + (x1 - cx) * s + h / 2), (x0, cy + (x0 - cx) * s + h / 2)]
    A = int(255 * alpha)
    if style == "iron":
        ink.d.polygon([(x + 4, y + 4) for x, y in poly], fill=(4, 16, 18, int(80 * alpha)))
        ink.d.polygon(poly, fill=(52, 50, 48, A))
        ink.d.line(poly[:2], fill=(180, 172, 150, int(210 * alpha)), width=1)
        ink.d.line(poly[2:], fill=(8, 8, 8, A), width=2)
    else:
        ink.d.polygon([(x + 3, y + 3) for x, y in poly], fill=PAL["teal_ink"] + (int(70 * alpha),))
        ink.d.polygon(poly, fill=PAL["card"] + (A,))
        ink.d.line(poly[:2], fill=PAL["card_edge"] + (int(150 * alpha),), width=1)
    return lambda x: cy + (x - cx) * s - h / 2


# ---------------------------------------------------------- the shadow fish ---

_FISH = {}


def _fish_parts(L):
    if L in _FISH:
        return _FISH[L]
    src = _trout_base()["img"].getchannel("A")
    h = int(L * src.height / src.width)
    al = src.resize((L, h), Image.LANCZOS).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(al)
    cols = lambda x: np.nonzero(a[:, int(clamp(x, 0, L - 1))] > 128)[0]

    def piece(mask_poly):
        m = Image.new("L", (L, h), 0)
        ImageDraw.Draw(m).polygon(mask_poly, fill=255)
        p = Image.new("RGBA", (L, h), (0, 0, 0, 0))
        p.putalpha(ImageChops.multiply(al, m))
        return p

    xt = 0.77 * L                                                   # the tail's pin
    ct = cols(xt)
    pin_t = (xt, float(ct.mean()) if len(ct) else h / 2)
    tail = piece([(xt - 0.03 * L, 0), (L, 0), (L, h), (xt - 0.03 * L, h)])
    cs = cols(0.02 * L)
    ym = float(cs.mean()) + 0.12 * (cs.max() - cs.min()) if len(cs) else h * 0.5
    pin_j = (0.135 * L, ym + 0.015 * h)
    jaw = piece([(0, ym), pin_j, (0.15 * L, h), (0, h)])
    body = piece([(0, 0), (xt + 0.02 * L, 0), (xt + 0.02 * L, h), (0.15 * L, h), pin_j, (0, ym)])
    # the spots are holes punched through the black paper
    safe = np.asarray(al.filter(ImageFilter.MinFilter(max(3, int(L * 0.05)) | 1)))
    rs = random.Random(7)
    holes = []
    tries = 0
    while len(holes) < 15 and tries < 600:
        tries += 1
        x, y = rs.uniform(0.2, 0.74) * L, rs.uniform(0.2, 0.8) * h
        rr = rs.uniform(0.011, 0.02) * L
        if safe[int(y), int(x)] > 200 and all(math.hypot(x - hx, y - hy) > (rr + hr) * 1.7 for hx, hy, hr in holes):
            holes.append((x, y, rr))
    bd = ImageDraw.Draw(body)
    bm = body.getchannel("A")
    hd = ImageDraw.Draw(bm)
    for x, y, rr in holes:
        hd.ellipse([x - rr, y - rr * 0.85, x + rr, y + rr * 0.85], fill=0)
    body.putalpha(bm)
    # two extra fins, each a cut leaf on its own pin
    def fin(w, hh):
        p = Image.new("RGBA", (int(w), int(hh)), (0, 0, 0, 0))
        ImageDraw.Draw(p).polygon(catmull([(w * 0.1, 0), (w * 0.5, hh * 0.12), (w * 0.95, hh * 0.75), (w * 0.7, hh), (w * 0.3, hh * 0.6), (w * 0.1, 0)], 5), fill=(0, 0, 0, 255))
        return p
    cb1, cb2 = cols(0.27 * L), cols(0.52 * L)
    fins = [(fin(0.12 * L, 0.3 * h), (0.27 * L, float(cb1.max()) - 0.06 * h if len(cb1) else h * 0.7)),
            (fin(0.1 * L, 0.26 * h), (0.52 * L, float(cb2.max()) - 0.07 * h if len(cb2) else h * 0.7))]
    _FISH[L] = dict(h=h, body=body, tail=tail, jaw=jaw, pin_t=pin_t, pin_j=pin_j, fins=fins)
    return _FISH[L]


@lru_cache(maxsize=256)
def _shadow_fish_cached(L, jaw_q, tail_q, fin_q, color, pins):
    P = _fish_parts(L)
    pad = int(L * 0.2)
    cv = Image.new("RGBA", (L + 2 * pad, P["h"] + 2 * pad), (0, 0, 0, 0))
    o = lambda p: (p[0] + pad, p[1] + pad)
    for fs, fp in P["fins"]:
        _pin(cv, fs, (fs.width * 0.1, 0), o(fp), fin_q)
    _pin(cv, P["tail"], P["pin_t"], o(P["pin_t"]), tail_q)
    _pin(cv, P["jaw"], P["pin_j"], o(P["pin_j"]), jaw_q)
    cv.alpha_composite(P["body"], (pad, pad))
    out = Image.new("RGBA", cv.size, tuple(color) + (0,))
    out.putalpha(cv.getchannel("A"))
    if pins:
        d = ImageDraw.Draw(out)
        pr = max(1.4, L * 0.011)
        for p in [P["pin_t"], P["pin_j"]] + [fp for _, fp in P["fins"]]:
            x, y = o(p)
            d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=PAL["brass"] + (255,))
    return out


def shadow_fish_sprite(length=158, jaw=0.0, tail=0.0, fins=0.0, color=None, pins=True):
    """The spotted fish as shadow theatre: black card cut to the outline of the 1896 brook trout plate, facing LEFT,
    `length` px long; its spots are holes punched through the card. Pinned pieces, each with a limit: jaw
    (0..22 degrees, opens downward), tail (-26..26), two fins (-30..30). No squash, no flex. RGBA cutout."""
    return _shadow_fish_cached(int(length), int(round(-clamp(jaw, 0, 22))), int(round(clamp(tail, -26, 26))),
                               int(round(clamp(fins, -30, 30) / 2) * 2), tuple(color or PAL["card"]), bool(pins))


def shadow_fish(ink, cx=None, cy=None, length=None, angle=None, flip=False, jaw=0.0, tail=0.0, fins=0.0, t=None, alpha=1.0,
                color=None, pins=True):
    """Draw the shadow fish centred at (cx, cy) (default: where the pilot drew it, STAGE['fish'], nose down-left).
    Faces left; flip=True faces right. angle degrees counter-clockwise. Give t instead of tail/fins for an idle
    swim (tail and fins rock on their pins). The punched spots show whatever is behind it. Draw it BEFORE bars()."""
    cx = STAGE["fish"][0] if cx is None else cx
    cy = STAGE["fish"][1] if cy is None else cy
    length = STAGE["fish_len"] if length is None else length
    angle = STAGE["fish_angle"] if angle is None else angle
    if t is not None:
        tail = 16 * math.sin(t * 5.0)
        fins = 14 * math.sin(t * 5.0 - 1.0)
    put(ink, shadow_fish_sprite(length, jaw, tail, fins, color, pins), cx, cy, angle=angle, flip=flip, alpha=alpha)


# ----------------------------------------------------- the glass: cracks, fog ---

def crack_points(c=PORT_C, r=PORT_R, mirror=False):
    """The six places on the cracks where the air gets out, on screen (mirror=True: seen from the river side)."""
    return [ring_xy(-u if mirror else u, v, c, r) for u, v in CRACK_LEAKS]


def cracks(ink, c=PORT_C, r=PORT_R, alpha=1.0, mirror=False, width=None):
    """The cracks the pilot drew, in the glass, always in the same places: a bright hairline with a dark twin (a
    crack catches the light). They never spread. Draw after everything outside the glass and before the fog.
    mirror=True flips them left to right (the same glass seen from the river side)."""
    w = width or max(1, int(round(r / 140.0)))
    rs = random.Random(9)
    for pl in CRACKS:
        pts = [ring_xy((-u if mirror else u) + rs.uniform(-0.004, 0.004), v + rs.uniform(-0.004, 0.004), c, r) for u, v in pl]
        ink.d.line([(x + w, y + w) for x, y in pts], fill=(0, 20, 24, int(150 * alpha)), width=w, joint="curve")
        ink.d.line(pts, fill=(236, 252, 246, int(215 * alpha)), width=w, joint="curve")
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):                       # little splinter ticks at the bends
            if rs.random() < 0.5:
                a = math.atan2(y1 - y0, x1 - x0) + rs.choice((-1, 1)) * 1.1
                ln = rs.uniform(0.02, 0.05) * r
                ink.d.line([x1, y1, x1 + ln * math.cos(a), y1 + ln * math.sin(a)], fill=(236, 252, 246, int(130 * alpha)), width=1)


def crack_bubbles(ink, t, c=PORT_C, r=PORT_R, strength=1.0, since=0.0, mirror=False, breaths=4):
    """The air leaving: with every breath (breath k starts at k / BREATH_HZ) a bead of small bubbles leaves each
    crack and rises. They are OUTSIDE the glass: draw after bars() and before cracks() and the fog.
    since = no bubbles from breaths before this time. strength scales how many."""
    k1 = breath_index(t)
    pts = crack_points(c, r, mirror)
    for k in range(max(0, k1 - breaths), k1 + 1):
        t0 = k / BREATH_HZ + 0.12
        if t0 < since:
            continue
        for q, p in enumerate(pts):
            bubbles(ink, p, t, t0=t0 + q * 0.03, n=max(1, int(round(3 * strength))), rise=0.42 * r, spread=0.03 * r, size=max(2.0, r / 62.0))


@lru_cache(maxsize=2)
def _fog_noise(S):
    return vnoise((S, S), 34, seed=71, octaves=3), vnoise((S, S), 5, seed=72, octaves=2)


def fog(ink, level=0.2, t=0.0, c=PORT_C, r=PORT_R, at=None, wipes=None, pulse=1.0):
    """Turkey's breath on the INSIDE of the glass: a white bloom spreading from where his beak meets the pane
    (at, default STAGE['beak']), beaded like condensation. level 0..1 = how far the glass has whitened (0.15 a
    thin bloom, 0.5 half the glass, 0.9 nearly to the cracks at the far side); each breath adds a pulse on top
    (pulse 0 turns that off). wipes = [(points, width_px), ...]: streaks wiped clear through the fog (a wing sliding
    down the pane). It is in front of everything outside: draw it after cracks() and turkey_reflection(), before
    seat_frame()."""
    r = int(r)
    at = STAGE["beak"] if at is None else at
    S = 2 * r + 2
    x0, y0 = int(c[0] - r - 1), int(c[1] - r - 1)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    lv = clamp(level) + 0.06 * pulse * breath(t)
    d = np.hypot(xx - (at[0] - x0), yy - (at[1] - y0)) / r
    reach = 0.16 + 1.25 * lv
    n1, n2 = _fog_noise(S)
    a = np.clip((reach - d * (0.8 + 0.45 * n1)) / 0.55, 0, 1) ** 1.2
    a *= (0.86 + 0.22 * n2) * (0.36 + 0.36 * min(1.0, lv * 1.4))
    a *= (np.hypot(xx - r - 1, yy - r - 1) <= r)
    al = Image.fromarray(np.clip(a * 235, 0, 255).astype(np.uint8))
    if wipes:
        wm = Image.new("L", (S, S), 0)
        wd = ImageDraw.Draw(wm)
        for pts, wid in wipes:
            pp = [(x - x0, y - y0) for x, y in pts]
            if len(pp) > 1:
                wd.line(pp, fill=255, width=int(wid), joint="curve")
                for x, y in (pp[0], pp[-1]):
                    wd.ellipse([x - wid / 2, y - wid / 2, x + wid / 2, y + wid / 2], fill=255)
        wm = wm.filter(ImageFilter.GaussianBlur(3))
        al = ImageChops.multiply(al, wm.point(lambda v: 255 - int(v * 0.9)))
    lay = Image.new("RGBA", (S, S), (236, 246, 244, 0))
    lay.putalpha(al)
    ink.paste(lay, (x0, y0))


def gauge(ink, notches=5.0, x=None, y=None, r=46, tremble=0.0, t=0.0, of=8):   # noqa: F811
    """The air gauge: a brass dial, ivory face, eight notches, one needle. notches 8 = FULL, 5 = where the pilot's
    page leaves it, 0 = EMPTY (never show 0: "could be"). Give it a float and ease it down one whole notch at a
    breath. Default place STAGE['gauge'] (low right on the tin wall beside the glass). For the small dial riveted
    on the tin's flank use gauge(ink, n, *tin_dial_xy(tp), r=24). tremble 0..1 shakes the needle."""
    x = STAGE["gauge"][0] if x is None else x
    y = STAGE["gauge"][1] if y is None else y
    N = of
    ring = brass_ring(int(r * 0.8), int(r), 0, 6, 9)
    ink.d.ellipse([x - r + 4, y - r + 7, x + r + 8, y + r + 12], fill=(0, 0, 0, 110))
    ink.d.ellipse([x - r * 0.84, y - r * 0.84, x + r * 0.84, y + r * 0.84], fill=PAL["ivory"] + (255,))
    ink.d.pieslice([x - r * 0.7, y - r * 0.7, x + r * 0.7, y + r * 0.7], 135, 135 + 270 * 2 / N, fill=(206, 70, 56, 150))
    for k in range(N + 1):
        a = math.radians(135 + 270 * k / N)
        p0 = (x + math.cos(a) * r * 0.56, y + math.sin(a) * r * 0.56)
        p1 = (x + math.cos(a) * r * 0.76, y + math.sin(a) * r * 0.76)
        ink.d.line([p0, p1], fill=PAL["pip"] + (255,), width=3 if k % 4 == 0 else 2)
    if r >= 34:
        ink.d.text((x, y + r * 0.42), "AIR", font=font("mono", max(8, int(r * 0.22))), fill=PAL["pip"] + (255,), anchor="mm")
    a0 = math.radians(135 - 7)
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


# ------------------------------------------------------------- the velvet iris ---

@lru_cache(maxsize=1)
def _velvet():
    nap = vnoise((H, W), 3, 9, seed=81) - 0.5
    slow = vnoise((H, W), 110, seed=82, octaves=3) - 0.5
    a = np.ones((H, W, 3), np.float32) * np.array(PAL["velvet"], np.float32)
    a *= (1 + nap * 0.34 + slow * 0.5)[..., None]
    return _img(a).convert("RGB")


def iris(ink, f, c=PORT_C, r=PORT_R, leaves=9, twist=46.0):
    """The velvet iris of the clue: a ring of dark red velvet-paper leaves that closes to a point over the glass and
    opens on the next scene. f = 0 fully open (nothing drawn), 1 = closed. One iris move per scene change, about
    0.4 s: close with f = ease(t, a, a + 0.2), swap the scene, open with f = 1 - ease(t, a + 0.2, a + 0.4).
    It lives inside the circle (c, r): on Turkey's side draw it just before seat_frame(); to close the whole frame
    (table, river side) pass r=600. Each leaf is its own piece with a cut edge and a shadow on the leaf beneath."""
    f = clamp(f)
    if f <= 0.001:
        return
    R = r + 2
    ap = R * (1 - smooth(f)) * math.cos(math.pi / leaves)                    # apothem of the open polygon
    x0, y0 = max(0, int(c[0] - R - 2)), max(0, int(c[1] - R - 2))
    x1, y1 = min(ink.w, int(c[0] + R + 3)), min(ink.h, int(c[1] + R + 3))
    box = (x0, y0, x1, y1)
    size = (x1 - x0, y1 - y0)
    region = ink.img.crop(box).convert("RGB")
    orig = region.copy()
    tex = _velvet().crop(box)
    disc = Image.new("L", size, 0)
    ImageDraw.Draw(disc).ellipse([c[0] - R - x0, c[1] - R - y0, c[0] + R - x0, c[1] + R - y0], fill=255)
    cx, cy = c[0] - x0, c[1] - y0
    BIG = 2.4 * R + 400
    rot = math.radians(twist * f - 90 + 180.0 / leaves)
    def half(k, a_):
        th = rot + 2 * math.pi * k / leaves
        nx, ny = math.cos(th), math.sin(th)
        tx, ty = -ny, nx
        p0 = (cx + nx * a_ + tx * BIG, cy + ny * a_ + ty * BIG)
        p1 = (cx + nx * a_ - tx * BIG, cy + ny * a_ - ty * BIG)
        return [p0, p1, (p1[0] + nx * BIG, p1[1] + ny * BIG), (p0[0] + nx * BIG, p0[1] + ny * BIG)]

    def mask(k, a_):
        m_ = Image.new("L", size, 0)
        ImageDraw.Draw(m_).polygon(half(k, a_), fill=255)
        return m_
    d = ImageDraw.Draw(region, "RGBA")
    for k in range(leaves):                                         # the leaves' shadow on the scene in the opening
        for q, al in ((9, 30), (5, 44), (2, 60)):
            d.polygon(half(k, ap - q), fill=(10, 0, 4, al))
    for k in range(leaves):                                         # each leaf is tucked under the next one round
        th = rot + 2 * math.pi * k / leaves
        nxt = ImageChops.invert(mask(k + 1, ap))
        m = ImageChops.multiply(mask(k, ap), nxt)
        sheen = 0.74 + 0.4 * (0.5 + 0.5 * math.cos(th + 2.2))
        region.paste(Image.eval(tex, lambda v, s_=sheen: int(min(255, v * s_))), (0, 0), m)
        for q, al in ((12, 50), (7, 70), (3, 90)):                  # the next leaf's shadow on this one
            sm = ImageChops.multiply(ImageChops.multiply(mask(k + 1, ap - q), m), Image.new("L", size, al))
            region.paste((14, 0, 6), (0, 0), sm)
        em = Image.new("L", size, 0)                                # this leaf's cut edge, pale where the nap is sheared
        e = half(k, ap)
        ImageDraw.Draw(em).line([e[0], e[1]], fill=200, width=3)
        region.paste(PAL["velvet_hi"], (0, 0), ImageChops.multiply(em, m))
    out = Image.composite(region, orig, disc.filter(ImageFilter.GaussianBlur(0.8)))
    ink.img.paste(out, (x0, y0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# -------------------------------------------------- padlock, the arm, the curl ---

@lru_cache(maxsize=32)
def _padlock_spr(size, open_q):
    K = 3
    s = size * K
    w, hgt = int(s * 1.5), int(s * 2.3)
    m = Image.new("L", (w, hgt), 0)
    d = ImageDraw.Draw(m)
    cx = w / 2
    sw = s * 0.2
    lift = s * 0.22 * open_q / 10.0
    d.arc([cx - s * 0.36, s * 0.1 - lift, cx + s * 0.36, s * 0.86 - lift], 180, 360, fill=255, width=int(sw))        # the shackle
    d.rectangle([cx - s * 0.36, s * 0.46 - lift, cx - s * 0.36 + sw - 1, s * 1.0], fill=255)
    d.rectangle([cx + s * 0.36 - sw + 1, s * 0.46 - lift, cx + s * 0.36, s * (1.0 if open_q < 5 else 0.72) - lift], fill=255)
    d.rounded_rectangle([cx - s * 0.56, s * 0.95, cx + s * 0.56, s * 1.92], radius=s * 0.13, fill=255)               # the body
    d.ellipse([cx - s * 0.12, s * 1.22, cx + s * 0.12, s * 1.46], fill=0)                                            # the keyhole: light comes through
    d.polygon([(cx - s * 0.06, s * 1.4), (cx + s * 0.06, s * 1.4), (cx + s * 0.1, s * 1.68), (cx - s * 0.1, s * 1.68)], fill=0)
    out = Image.new("RGBA", (w, hgt), PAL["card"] + (0,))
    out.putalpha(m)
    od = ImageDraw.Draw(out)
    for x in (cx - s * 0.42, cx + s * 0.42):
        od.ellipse([x - s * 0.045, s * 1.06 - s * 0.045, x + s * 0.045, s * 1.06 + s * 0.045], fill=PAL["brass"] + (255,))
    return out.resize((w // K, hgt // K), Image.LANCZOS)


def padlock(ink, x, y, size=30, swing=0.0, open_=0.0, alpha=1.0):
    """A padlock as black card (keyhole punched through, two brass pins) hanging by the top of its shackle from the
    point (x, y) (put that on the crossbar: y = y_at(x) + a little). size = the body's width is about 1.1 * size,
    the whole lock 2.1 * size tall. swing = degrees it swings about (x, y); open_ 0..1 lifts the shackle open."""
    spr = _padlock_spr(int(size), int(round(clamp(open_) * 10)))
    lay = Image.new("RGBA", (ink.w, ink.h), (0, 0, 0, 0))
    _pin(lay, spr, (spr.width / 2, size * 0.16), (x, y), swing)
    ink.paste(lay, (0, 0), alpha)


def shadow_arm(ink, tip, root=None, width=30, bend=0.22, alpha=1.0):
    """'Someone': an arm's length of black shape reaching in from the edge of the glass, no head, no hand we could
    name. Two cut pieces pinned at the elbow, the fore-end blunt. tip = where the blunt end is; root = where it
    leaves the frame (default: off the right edge of the glass, a little above tip). bend 0..0.5 = how much the
    elbow sags. Returns the elbow point."""
    root = (PORT_C[0] + PORT_R + 60, tip[1] - 46) if root is None else root
    mid = lerp2(root, tip, 0.5)
    dx, dy = tip[0] - root[0], tip[1] - root[1]
    ln = math.hypot(dx, dy) or 1.0
    el = (mid[0] - dy / ln * ln * bend * 0.5, mid[1] + abs(dx) / ln * ln * bend)
    A = int(255 * alpha)

    def limb(p, q, w0, w1):
        ux, uy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(ux, uy) or 1.0
        px, py = -uy / n, ux / n
        poly = [(p[0] + px * w0 / 2, p[1] + py * w0 / 2), (q[0] + px * w1 / 2, q[1] + py * w1 / 2), (q[0] - px * w1 / 2, q[1] - py * w1 / 2),
                (p[0] - px * w0 / 2, p[1] - py * w0 / 2)]
        ink.d.polygon([(x + 4, y + 3) for x, y in poly], fill=PAL["teal_ink"] + (int(80 * alpha),))
        ink.d.polygon(poly, fill=PAL["card"] + (A,))
        ink.d.ellipse([q[0] - w1 / 2, q[1] - w1 / 2, q[0] + w1 / 2, q[1] + w1 / 2], fill=PAL["card"] + (A,))
    limb(root, el, width * 1.25, width)
    limb(el, tip, width, width * 0.8)
    ink.d.ellipse([el[0] - 2.5, el[1] - 2.5, el[0] + 2.5, el[1] + 2.5], fill=PAL["brass"] + (A,))
    return el


@lru_cache(maxsize=8)
def _cheeto_spr(size):
    K = 3
    s = size * K
    S = int(s * 2.2)
    rs = random.Random(12)
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    blobs = []
    for q in range(11):                                          # a knobbly curl: lumps strung along a bent line
        f = q / 10
        a = lerp(-0.9, 0.95, f)
        x = S / 2 + s * 0.78 * math.sin(a) + rs.uniform(-0.03, 0.03) * s
        y = S / 2 + s * 0.36 * (1 - math.cos(a * 1.25)) * 1.5 - s * 0.2 + rs.uniform(-0.03, 0.03) * s
        rr = s * (0.2 + 0.07 * math.sin(f * math.pi)) * rs.uniform(0.82, 1.12)
        blobs.append((x, y, rr))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(K * 0.6)).point(lambda v: 255 if v > 120 else 0).filter(ImageFilter.GaussianBlur(K * 0.4))
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    n = vnoise((S, S), 7, seed=13, octaves=2) - 0.5
    col = np.ones((S, S, 3), np.float32) * np.array(PAL["cheeto"], np.float32)
    lit = np.zeros((S, S), np.float32)
    for x, y, rr in blobs:                                       # each lump is lit on its upper left, dark below
        g = np.exp(-(((xx - x + rr * 0.35) / (rr * 0.8)) ** 2 + ((yy - y + rr * 0.4) / (rr * 0.8)) ** 2))
        lit = np.maximum(lit, g)
        sh = np.exp(-(((xx - x - rr * 0.3) / (rr * 0.9)) ** 2 + ((yy - y - rr * 0.55) / (rr * 0.6)) ** 2))
        col -= sh[..., None] * 16
    col = col * (1 + n[..., None] * 0.34) + (np.array(PAL["cheeto_hi"], np.float32) - col) * (lit[..., None] * 0.6)
    speck = vnoise((S, S), 2.2, seed=14) > 0.8                    # the red dust on it
    col = np.where(speck[..., None], col * 0.6 + np.array(PAL["cheeto_dk"], np.float32) * 0.4, col)
    ma = np.asarray(m, np.float32) / 255
    inner = np.asarray(m.filter(ImageFilter.MinFilter(2 * K + 1)), np.float32) / 255
    col = col * (1 - 0.4 * np.clip(ma - inner, 0, 1)[..., None])
    out = Image.fromarray(np.dstack([np.clip(col, 0, 255), ma * 255]).astype(np.uint8), "RGBA")
    return out.resize((S // K, S // K), Image.LANCZOS)


def cheeto(ink, x, y, size=26, angle=0.0, t=0.0, glow=1.0, fizz=1.0, alpha=1.0):
    """The hot Cheeto: ONE small knobbly orange curl (a plain cheese curl: no bag, no logo, no lettering), the only
    thing in the black world with its own colour. Centred at (x, y), about 1.8 * size long. It is hot: glow 0..1
    lays an orange glow round it, fizz 0..1 a collar of fine bubbles streaming up off it. angle degrees CCW.
    Draw it after the fish and before or between bars() calls (it is outside the glass, in front of the fish)."""
    if glow > 0:
        g = Image.new("RGBA", (int(size * 6), int(size * 6)), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse([size * 1.3, size * 1.7, size * 4.7, size * 4.3], fill=PAL["cheeto"] + (int(120 * glow),))
        gd.ellipse([size * 2.1, size * 2.3, size * 3.9, size * 3.7], fill=PAL["cheeto_hi"] + (int(150 * glow),))
        ink.paste(g.filter(ImageFilter.GaussianBlur(size * 0.55)), (int(x - size * 3), int(y - size * 3)), alpha * (0.85 + 0.15 * math.sin(t * 23)))
    if fizz > 0:
        rs = random.Random(5)
        for q in range(int(26 * fizz)):
            ph, sp, ox = rs.random(), rs.uniform(0.9, 1.6), rs.uniform(-1, 1)
            age = (t * sp + ph) % 1.0
            bx = x + ox * size * (0.85 + 0.5 * age) + 2.5 * math.sin(age * 9 + q)
            by = y - size * 0.1 - age * size * 2.6
            br = max(1.0, size * 0.07 * (0.6 + age))
            a = int(230 * (1 - age) ** 0.7 * alpha)
            ink.d.ellipse([bx - br, by - br, bx + br, by + br], outline=(236, 252, 246, a), width=1)
    put(ink, _cheeto_spr(int(size)), x, y, angle=angle, alpha=alpha)


# ------------------------------------------------------------ the house flats ---
# Black card, cut out, with the light let through where a thing is hollow. Unit coordinates: x right, y DOWN from
# the flat's floor point (0, 0); about 100 units = the armchair's height.

def _f_poly(d, pts, s, o, fill=255):
    d.polygon([(o[0] + x * s, o[1] + y * s) for x, y in pts], fill=fill)


def _flat_mask(name, s):
    Wc, Hc = int(260 * s), int(230 * s)
    m = Image.new("L", (Wc, Hc), 0)
    d = ImageDraw.Draw(m)
    o = (Wc / 2, Hc - 12 * s)
    P = lambda pts, fill=255: _f_poly(d, pts, s, o, fill)
    E = lambda x0, y0, x1, y1, fill=255: d.ellipse([o[0] + x0 * s, o[1] + y0 * s, o[0] + x1 * s, o[1] + y1 * s], fill=fill)
    if name == "armchair":                                           # side on: tall buttoned back, rolled arm, fat cushion, turned feet
        P(catmull([(-44, -14), (-50, -60), (-52, -100), (-44, -118), (-28, -120), (-18, -108), (-14, -78), (-10, -58), (20, -58), (26, -68),
                   (42, -70), (52, -60), (52, -44), (46, -38), (48, -14), (-44, -14)], 5))
        P(catmull([(-12, -50), (-8, -62), (30, -62), (44, -52), (44, -40), (-10, -40), (-12, -50)], 4))                       # the cushion
        P([(-40, -14), (-30, -14), (-33, 0), (-39, 0)])
        P([(34, -14), (44, -14), (42, 0), (36, 0)])
        E(-42, -4, -30, 4)
        E(34, -4, 46, 4)
        for q in range(3):                                           # three buttons punched in the back
            E(-37 + q * 2.5, -100 + q * 20, -32 + q * 2.5, -95 + q * 20, 0)
        d.line([o[0] - 8 * s, o[1] - 39 * s, o[0] + 45 * s, o[1] - 39 * s], fill=0, width=max(1, int(1.6 * s)))                   # the slit under the cushion
    elif name == "lamp":
        P([(-26, -86), (26, -86), (15, -124), (-15, -124)])                                   # the shade
        for q in range(9):                                                                  # its fringe, cut tick by tick
            x = -25 + q * 6.2
            P([(x, -86), (x + 3.4, -86), (x + 1.7, -75)])
        P([(-2.5, -86), (2.5, -86), (2.5, -10), (-2.5, -10)])
        P(catmull([(-16, 0), (-14, -8), (-4, -13), (4, -13), (14, -8), (16, 0), (-16, 0)], 3))
        E(-6, -56, 6, -42)
    elif name == "clock":
        E(-26, -64, 26, -12)
        E(-20, -58, 20, -18, 0)                                                              # the face is cut out
        P([(-1.6, -39), (1.6, -39), (1.6, -55), (-1.6, -55)])
        P([(-1.4, -37), (-1.4, -40), (13, -32), (12, -29)])
        E(-3, -41, 3, -35)
        for q in range(12):
            a = q * math.pi / 6
            x, y = 17.5 * math.sin(a), -38 - 17.5 * math.cos(a)
            E(x - 1.5, y - 1.5, x + 1.5, y + 1.5)
        P([(-4, -12), (4, -12), (2, 0), (-2, 0)])                                              # pendulum
        E(-6, -4, 6, 8)
    elif name == "kettle":
        P(catmull([(-26, 0), (-30, -22), (-22, -42), (-8, -48), (8, -48), (22, -42), (30, -22), (26, 0), (-26, 0)], 4))
        P([(-8, -48), (8, -48), (5, -54), (-5, -54)])
        E(-4, -60, 4, -52)
        P(catmull([(24, -30), (40, -40), (50, -52), (54, -50), (46, -34), (30, -18)], 3))        # spout
        d.arc([o[0] - 46 * s, o[1] - 50 * s, o[0] - 14 * s, o[1] - 6 * s], 100, 260, fill=255, width=max(2, int(5 * s)))   # handle
    elif name == "frame":
        E(-22, -62, 22, -6)
        E(-16, -55, 16, -13, 0)
        E(-7, -44, 7, -30)                                                                  # a portrait too small to make out
        P(catmull([(-13, -15), (-11, -26), (0, -30), (11, -26), (13, -15), (-13, -15)], 3))
        P([(-1, -62), (1, -62), (6, -74), (-6, -74)])
    elif name == "bed":
        P([(-90, 0), (-90, -70), (-82, -78), (-74, -70), (-74, -34), (84, -34), (84, -50), (92, -56), (98, -50), (98, 0), (88, 0), (88, -12),
           (-78, -12), (-78, 0)])
        P(catmull([(-72, -34), (-70, -52), (-52, -58), (-34, -52), (-32, -34), (-72, -34)], 4))    # the pillow
        P(catmull([(-30, -34), (-10, -46), (30, -48), (70, -44), (84, -34), (-30, -34)], 4))        # the quilt
        for q in range(4):
            P([(-20 + q * 26, -40), (-14 + q * 26, -40), (-17 + q * 26, -35)], 0)
    elif name == "mat":
        P([(-58, 0), (58, 0), (50, -9), (-50, -9)])
        for q in range(12):
            P([(-58 + q * 10.2, 0), (-55 + q * 10.2, 0), (-57.5 + q * 10.2, 5)])
        for q in range(7):
            P([(-38 + q * 12, -6.5), (-32 + q * 12, -6.5), (-33 + q * 12, -3), (-39 + q * 12, -3)], 0)
    else:
        raise ValueError(name)
    return m, o


FLATS = ("armchair", "lamp", "clock", "kettle", "frame", "bed", "mat")


@lru_cache(maxsize=64)
def _flat_spr(name, s100):
    K = 3
    m, o = _flat_mask(name, s100 / 100.0 * K)
    m = m.resize((m.width // K, m.height // K), Image.LANCZOS)
    out = Image.new("RGBA", m.size, PAL["card"] + (0,))
    out.putalpha(m)
    return out, (o[0] / K, o[1] / K)


def flat(ink, name, x, y, scale=1.0, flip=False, lit=0.0, alpha=1.0, angle=0.0):
    """One piece of the house as a black card flat with its floor point at (x, y): name in FLATS ('armchair',
    'lamp', 'clock', 'kettle', 'frame', 'bed', 'mat'). scale 1.0 = the armchair about 116 px tall. Hollows (the
    clock face, the chair's seat, the frame) are cut out: the light shows through. lit 0..1 (the lamp): a warm
    paper-white glow under the shade. No lettering on anything."""
    spr, (ox, oy) = _flat_spr(name, int(round(scale * 100)))
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        ox = spr.width - ox
    if lit > 0 and name == "lamp":
        gs = int(190 * scale)
        g = Image.new("RGBA", (gs, gs), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.ellipse([gs * 0.14, gs * 0.2, gs * 0.86, gs * 0.92], fill=(255, 240, 196, int(120 * lit)))
        gd.ellipse([gs * 0.34, gs * 0.36, gs * 0.66, gs * 0.7], fill=(255, 250, 226, int(215 * lit)))
        ink.paste(g.filter(ImageFilter.GaussianBlur(gs * 0.1)), (int(x - gs / 2), int(y - 70 * scale - gs / 2)), alpha)
    put(ink, spr, x + spr.width / 2 - ox, y + spr.height / 2 - oy, alpha=alpha, angle=angle)


def curtains(ink, closed=0.0, c=PORT_C, r=PORT_R, span=0.8, alpha=1.0, glow=0.0):
    """The two velvet curtains at the tunnel mouth. closed 0 = tied back at the sides (as in the deck picture),
    1 = drawn shut across the mouth. span = the mouth's radius as a fraction of r. glow 0..1 = a lamp shining
    through the closed cloth. Each curtain is one cut velvet piece with its folds; brass tie-backs while open."""
    R = span * r
    k = smooth(clamp(closed))
    S = int(2 * R + 4)
    x0, y0 = int(c[0] - R - 2), int(c[1] - R - 2)
    tex = _velvet().crop((0, 0, S, S)) if S <= H else _velvet().resize((S, S))
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cx = cy = R + 2
    for sgn in (-1, 1):
        top_in = lerp(0.2, 0.0, k)                                  # inner edge at the top, as a fraction of R from centre
        tie = lerp(0.74, -0.03, k)
        bot = lerp(0.66, -0.02, k)
        inner = catmull([(top_in, -1.05), (lerp(top_in, tie, 0.55), -0.45), (tie, 0.18), (lerp(tie, bot, 0.5) + 0.05 * (1 - k), 0.6), (bot, 1.05)], 6)
        outer = [(1.1, 1.05), (1.1, -1.05)]
        m = Image.new("L", (S, S), 0)
        poly = [(cx + sgn * u * R, cy + v * R) for u, v in inner] + [(cx + sgn * u * R, cy + v * R) for u, v in outer]
        ImageDraw.Draw(m).polygon(poly, fill=255)
        a = np.asarray(tex, np.float32).copy()
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        u = np.abs(xx - cx) / R
        innx = np.interp((yy[:, 0] - cy) / R, [p[1] for p in inner], [p[0] for p in inner])[:, None]
        g = np.clip((u - innx) / np.maximum(0.05, 1.05 - innx), 0, 1)          # 0 at the inner edge, 1 at the wall
        nf = 5 + 3 * k
        fold = 0.5 + 0.5 * np.cos(g * nf * 2 * math.pi + 0.6)                   # hanging folds
        a *= (0.45 + 0.85 * fold ** 1.5)[..., None]
        if glow > 0:
            gl = np.exp(-(((xx - cx) / (R * 0.5)) ** 2 + ((yy - cy - R * 0.1) / (R * 0.55)) ** 2)) * glow
            a = a * (1 + 0.9 * gl[..., None]) + np.array([90, 40, 16], np.float32) * gl[..., None]
        piece = _img(a).convert("RGBA")
        piece.putalpha(m.filter(ImageFilter.GaussianBlur(0.7)))
        lay.alpha_composite(piece)
        d = ImageDraw.Draw(lay, "RGBA")
        d.line([(cx + sgn * u_ * R, cy + v_ * R) for u_, v_ in inner], fill=PAL["velvet_hi"] + (200,), width=2)
        if k < 0.6:                                                             # the tie-back
            tx, ty = cx + sgn * (tie + 0.02) * R, cy + 0.18 * R
            d.line([tx, ty, cx + sgn * 1.02 * R, ty - 0.05 * R], fill=PAL["brass"] + (int(255 * (1 - k / 0.6)),), width=max(2, int(R * 0.03)))
    disc = Image.new("L", (S, S), 0)
    ImageDraw.Draw(disc).ellipse([2, 2, S - 3, S - 3], fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), disc))
    ink.paste(lay, (x0, y0), alpha)


def gate(ink, open_=0.0, c=PORT_C, r=PORT_R, shift=(0.0, 0.0), alpha=1.0):
    """The front gate of bolt 3: bars 5 and 6 are its two leaves. open_ 0 = shut (they are just bars 5 and 6, with
    a small BLANK nameplate hung on bar 5 and a letter slot plate on bar 6); 1 = swung open, each leaf turned
    edge-on toward its neighbour. Draw it in place of bars(only=[5, 6]). Returns {'gap': (x_left, x_right) of the
    way through at the crossbar's height, 'plate': centre of the nameplate, 'slot': centre of the letter slot}."""
    f = smooth(clamp(open_))
    out = bars(ink, [5, 6], c, r, swing={5: -f, 6: f}, shift=shift, alpha=alpha)
    v = 0.1
    x5, w5 = bar_line(5, v, c, r)
    x6, w6 = bar_line(6, v, c, r)
    x5 += shift[0] - f * 0.11 * r
    x6 += shift[0] + f * 0.11 * r
    y = c[1] + shift[1] + v * r
    A = int(255 * alpha)
    sq = 1 - 0.75 * f
    pw, ph = 0.2 * r * sq, 0.085 * r
    px = x5 + w5 / 2 + pw / 2 - 2
    ink.d.rectangle([px - pw / 2, y - ph / 2, px + pw / 2, y + ph / 2], fill=PAL["card"] + (A,))
    ink.d.rectangle([px - pw / 2 + 3 * sq, y - ph / 2 + 3, px + pw / 2 - 3 * sq, y + ph / 2 - 3], fill=PAL["brass"] + (A,))       # a blank brass plate: no name
    ink.d.line([px - pw / 2 + 3 * sq, y - ph / 2 + 3, px + pw / 2 - 3 * sq, y - ph / 2 + 3], fill=PAL["brass_hi"] + (A,), width=1)
    sx, sy = x6 - w6 / 2 - pw / 2 + 2, y + 0.2 * r
    ink.d.rectangle([sx - pw / 2, sy - ph / 2, sx + pw / 2, sy + ph / 2], fill=PAL["card"] + (A,))
    ink.d.rectangle([sx - pw / 2 + 4 * sq, sy - 2, sx + pw / 2 - 4 * sq, sy + 2], fill=PAL["teal_hi"] + (int(A * 0.9),))             # the slot: light through it
    return dict(gap=(x5 + w5 / 2, x6 - w6 / 2), plate=(px, y), slot=(sx, sy), bars=out)


HOME_PLANES = ("far", "room", "chair", "sill")


def home(ink, push=0.0, lamp=0.0, c=PORT_C, r=PORT_R, planes=HOME_PLANES, alpha=1.0):
    """'That's his home': the house behind the bars, as black card flats on four planes that part as the camera
    pushes in (multiplane: nearest fastest). push 0 = seen from the glass (small, deep in the tunnel), 1 = pushed
    right in. Planes, back to front: 'far' (the bed with its pillow at the very back), 'room' (clock and oval frame
    on the wall, kettle, the fringed lamp; lamp 0..1 lights it), 'chair' (the armchair), 'sill' (the mat on the
    stone sill). Draw planes in separate calls to put the fish between them. Lay it over glow_ground + tunnel,
    before curtains(), gate() and bars(). Returns anchors on screen: {'bed', 'lamp', 'chair' (the seat), 'mat',
    'floor' (y of the room floor), 'scale' {plane: scale}}."""
    p = smooth(clamp(push))
    out = dict(scale={})

    def P(depth, u, v):                       # depth 0 far .. 1 near: where a point of that plane lands, and its scale
        s = lerp(0.34, 1.0, depth) * (1 + p * lerp(0.35, 1.55, depth))
        return (c[0] + u * r * s, c[1] + (v * s + 0.1 * (1 - depth) * (1 - p)) * r), s
    if "far" in planes:
        (x, y), s = P(0.0, 0.0, 0.5)
        flat(ink, "bed", x, y, 0.62 * s * r / 212.0, alpha=alpha)
        out["bed"] = (x, y - 26 * s * r / 212.0)
        out["scale"]["far"] = s
    if "room" in planes:
        (x, y), s = P(0.35, 0.0, 0.5)
        k = 0.7 * s * r / 212.0
        flat(ink, "clock", x - 0.16 * r * s, y - 0.5 * r * s, k, alpha=alpha)
        flat(ink, "frame", x + 0.2 * r * s, y - 0.55 * r * s, k, alpha=alpha)
        flat(ink, "kettle", x + 0.5 * r * s, y, k * 0.8, alpha=alpha)
        flat(ink, "lamp", x - 0.52 * r * s, y, k, lit=lamp, alpha=alpha)
        out["lamp"] = (x - 0.52 * r * s, y - 70 * k)
        out["floor"] = y
        out["scale"]["room"] = s
    if "chair" in planes:
        (x, y), s = P(0.62, 0.12, 0.5)
        k = 0.78 * s * r / 212.0
        flat(ink, "armchair", x, y, k, alpha=alpha)
        out["chair"] = (x, y - 62 * k)
        out["scale"]["chair"] = s
    if "sill" in planes:
        (x, y), s = P(1.0, 0.06, 0.72)
        flat(ink, "mat", x, y, 0.9 * s * r / 212.0, alpha=alpha)
        out["mat"] = (x, y - 6)
        out["scale"]["sill"] = s
    return out


# ------------------------------------------------------------ the river side ---

@lru_cache(maxsize=1)
def _ruling():
    """Fine horizontal ruled lines to lay over the painted river planes, so the river side is an engraving too."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ph = ((yy + 1.6 * np.sin(xx / 53.0 + yy / 40.0)) / 4.0) % 1.0
    line = np.clip((0.34 - np.abs(ph - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    al = line * (60 + 70 * yy / H)
    return Image.fromarray(np.dstack([np.full((H, W), 6), np.full((H, W), 34), np.full((H, W), 40), al]).astype(np.uint8), "RGBA")


@lru_cache(maxsize=2)
def _wall_img(x0):
    wd = W - x0 + 40
    yy, xx = np.mgrid[0:H, 0:wd].astype(np.float32)
    a = np.ones((H, wd, 3), np.float32) * np.array((104, 122, 116), np.float32)
    a *= (0.8 + 0.5 * vnoise((H, wd), 60, seed=91, octaves=3))[..., None]
    rs = random.Random(8)
    bh = 58
    blocks = np.zeros((H, wd), np.float32)
    joint = np.zeros((H, wd), bool)
    for row in range(-1, H // bh + 2):
        y = row * bh + 6
        x = -rs.uniform(0, 90)
        while x < wd:
            bw = rs.uniform(86, 150)
            tone = rs.uniform(-0.14, 0.14)
            xa, xb, ya, yb = int(max(0, x)), int(min(wd, x + bw)), int(max(0, y)), int(min(H, y + bh))
            if xb > xa and yb > ya:
                blocks[ya:yb, xa:xb] = tone
                joint[ya:min(H, ya + 3), xa:xb] = True
                joint[ya:yb, xa:min(wd, xa + 3)] = True
            x += bw
    a *= (1 + blocks)[..., None]
    ph = ((yy + 1.2 * np.sin(xx / 31.0)) / 3.6) % 1.0                               # ruled, as an engraver shades a flat wall
    line = np.clip((0.36 - np.abs(ph - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    a = a * (1 - 0.34 * line[..., None]) + np.array((20, 40, 44), np.float32) * 0.34 * line[..., None]
    a[joint] *= 0.42
    lite = np.roll(joint, 3, axis=0) & ~joint
    a[lite] = a[lite] * 0.6 + np.array((190, 206, 192), np.float32) * 0.4
    a *= (1.06 - 0.5 * (yy / H) ** 2)[..., None]
    edge = 8 + 10 * vnoise((H, 1), 50, seed=92)[:, 0]
    al = np.clip((xx - edge[:, None]) / 2.0, 0, 1) * 255
    img = Image.fromarray(np.dstack([np.clip(a, 0, 255), al]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(H):                                                              # the wall's own lit edge
        d.point((int(edge[y]) + 1, y), fill=(206, 222, 206, 220))
    return img


def culvert_wall(ink, x0=None, shift=0.0):
    """The flat stone wall of the culvert on the right of the river-side stage (from x0, default RIVER['wall_x'],
    to the frame edge): coursed blocks, ruled like an engraving, a soft shadow at its near edge. The screen."""
    x0 = RIVER["wall_x"] if x0 is None else x0
    img = _wall_img(int(x0))
    ink.paste(_shadow_of(img, 12, 0.5, (0, 14, 16)), (int(x0 + shift - 18), 6))
    ink.paste(img, (int(x0 + shift), 0))


def river_backdrop(ink, t=0.0, shift=0.0, wall=True, dim=0.0):
    """The river-side stage, empty: the river's painted and cut-paper planes (water, light shafts, far boulders,
    gravel bed, motes), ruled over like an engraving, and (wall=True) the culvert wall on the right. Fills the
    frame. dim 0..1 darkens the water (so a projector's light shows)."""
    river(ink, t, shift=shift)
    ink.paste(_ruling(), (0, 0))
    if dim > 0:
        ink.d.rectangle([0, 0, ink.w, ink.h], fill=(4, 22, 26, int(170 * clamp(dim))))
    if wall:
        culvert_wall(ink, shift=shift * 0.5)


def light_cone(ink, src, c=None, r=None, strength=1.0, t=0.0):
    """The cone of lamp light the tin's porthole throws: from src (the porthole's centre on screen) widening to the
    round picture (centre c, radius r; defaults RIVER['picture']). Soft, pale, with ruled streaks along it; it
    dims a little with every heavy breath (pass t). Draw it after the tin and the bars, before the audience."""
    c = RIVER["picture"] if c is None else c
    r = RIVER["picture_r"] if r is None else r
    k = strength * (1 - 0.22 * breath(t))
    dx, dy = c[0] - src[0], c[1] - src[1]
    n = math.hypot(dx, dy) or 1.0
    px, py = -dy / n, dx / n
    lay = Image.new("RGBA", (ink.w, ink.h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a, b = (src[0] + px * 14, src[1] + py * 14), (src[0] - px * 14, src[1] - py * 14)
    d.polygon([a, (c[0] + px * r, c[1] + py * r), (c[0] - px * r, c[1] - py * r), b], fill=(236, 248, 226, int(58 * k)))
    d.polygon([a, (c[0] + px * r * 0.6, c[1] + py * r * 0.6), (c[0] - px * r * 0.6, c[1] - py * r * 0.6), b], fill=(244, 252, 236, int(40 * k)))
    lay = lay.filter(ImageFilter.GaussianBlur(5))
    d = ImageDraw.Draw(lay)
    for q in range(-6, 7):
        g = q / 6.5
        d.line([src[0] + px * 12 * g, src[1] + py * 12 * g, c[0] + px * r * g, c[1] + py * r * g], fill=(250, 255, 244, int(26 * k)), width=1)
    ink.paste(lay, (0, 0))


def wall_picture(ink, t=0.0, c=None, r=None, show=True, mood="shove", dim=0.0, bar_shadows=True, turkey_h=None, **over):
    """'A movie': the round picture of light on the culvert wall. show=True throws Turkey's huge frantic shadow in
    it (his hinged outline in `mood`, soft at the edge, facing left as he does in the window) crossed by the bars'
    upright shadows; show=False is the empty lit picture for a BLANK bolt (pass bar_shadows=False for nothing at
    all on it). It jerks and dims with every heavy breath, as a hand-cranked film does. dim 0..1 = how much the
    picture has faded by the end. Any turkey pose key can be overridden. Returns (c, r)."""
    c = RIVER["picture"] if c is None else c
    r = int(RIVER["picture_r"] if r is None else r)
    k = (1 - clamp(dim) * 0.5) * (1 - 0.2 * breath(t))
    S = 2 * r + 40
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    rad = np.hypot(xx - S / 2, yy - S / 2) / r
    al = np.clip((1.0 - rad) / 0.07, 0, 1) * (0.9 - 0.25 * rad ** 2) * 255 * k
    lit = Image.fromarray(np.dstack([np.full((S, S), 236), np.full((S, S), 246), np.full((S, S), 222), al]).astype(np.uint8), "RGBA")
    lay.alpha_composite(lit)
    disc = Image.fromarray(np.clip((1.0 - rad) / 0.05, 0, 1) * 255).convert("L")
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hold = Ink(t, 0, (S, S))
    hold.img, hold.d = sh, ImageDraw.Draw(sh, "RGBA")
    jerk = 2.0 * math.sin(breath_index(t) * 2.4)                                 # the picture sits a hair differently each breath
    if show:
        th = turkey_h or r * 1.75
        turkey_shadow(hold, S / 2 + r * 0.16 + jerk, S / 2 + r * 0.22, th, mood, t, "bust", color=(14, 26, 30), blur=max(1.0, r / 60.0), **over)
        sh = hold.img
    if bar_shadows:
        hold.img, hold.d = sh, ImageDraw.Draw(sh, "RGBA")
        bars(hold, [2, 4, 5, 6, 8], (S / 2 + jerk, S / 2), r * 1.02, style="shade", color=(14, 30, 34), alpha=0.8 if show else 0.55)
        sh = hold.img.filter(ImageFilter.GaussianBlur(0.8))
    sh.putalpha(ImageChops.multiply(sh.getchannel("A"), disc).point(lambda v: int(v * (0.86 * k + 0.1))))
    lay.alpha_composite(sh)
    ink.paste(lay, (int(c[0] - S / 2), int(c[1] - S / 2)))
    return c, r


def river_bars(ink, x0=None, x1=None, n=7, y0=20, y1=None, lean=5.0, shift=0.0):
    """The culvert bars standing in the river between the tin and the wall (river side: rusted iron with their
    detail, ruled): n uprights between x0 and x1 (defaults RIVER['bars_x']) from y0 down into the bed at y1, seen
    nearly edge-on, with two crossbars. They stand between the porthole's light and the wall."""
    x0 = RIVER["bars_x"][0] if x0 is None else x0
    x1 = RIVER["bars_x"][1] if x1 is None else x1
    y1 = RIVER["bed_y"] + 14 if y1 is None else y1
    rs = random.Random(21)
    for cy in (y0 + (y1 - y0) * 0.24, y0 + (y1 - y0) * 0.74):
        ink.d.polygon([(x0 - 10 + shift, cy - 4), (x1 + 10 + shift, cy - 9), (x1 + 10 + shift, cy - 1), (x0 - 10 + shift, cy + 4)], fill=(44, 42, 42, 255))
        ink.d.line([(x0 - 10 + shift, cy - 4), (x1 + 10 + shift, cy - 9)], fill=(170, 164, 144, 220), width=1)
    for q in range(n):
        f = q / (n - 1)
        x = lerp(x0, x1, f) + shift + rs.uniform(-2, 2)
        wd = lerp(11, 8, f)
        ln = lean * (f - 0.5) * 2 + rs.uniform(-2, 2)
        poly = [(x - wd / 2 - ln, y0), (x + wd / 2 - ln, y0), (x + wd / 2 + ln, y1), (x - wd / 2 + ln, y1)]
        ink.d.polygon([(px + 5, py + 3) for px, py in poly], fill=(4, 18, 20, 80))
        ink.d.polygon(poly, fill=(56, 54, 52, 255))
        for g in (0.3, 0.55, 0.8):
            ink.d.line([lerp2(poly[0], poly[1], g), lerp2(poly[3], poly[2], g)], fill=mix_color((150, 142, 124), (18, 16, 16), g) + (210,), width=1)
        ink.d.line([poly[0], poly[3]], fill=(206, 200, 178, 230), width=1)
        ink.d.line([poly[1], poly[2]], fill=(8, 8, 8, 255), width=1)
        for _ in range(3):
            yy_ = rs.uniform(y0 + 20, y1 - 20)
            ink.d.ellipse([x - 3, yy_ - 6, x + 3, yy_ + 6], fill=(126, 72, 40, 150))


def trout_audience(ink, t=0.0, settle=0.0, rows=((4, 420, 112), (5, 458, 132)), x0=330, x1=800, lid=0.0):
    """The audience: two rows of engraved brook trout low in the frame, all facing the wall (right), tails idling.
    rows = ((count, y, length), ...) back row first. settle 0..1 lowers them all together a little (they settle to
    watch). The spotted fish of the drawing is the LAST one returned (the right end of the front row).
    Returns [(x, y), ...] of every trout, back row first."""
    out = []
    for ri, (n, y, ln) in enumerate(rows):
        for q in range(n):
            x = lerp(x0, x1, (q + (0.5 if n < 5 else 0.0)) / 4.0) + 8 * math.sin(q * 2.3 + ri)
            yy_ = y + 9 * smooth(clamp(settle)) + 3 * math.sin(t * 1.3 + q * 1.7 + ri) * (1 - 0.7 * settle)
            trout(ink, x, yy_, ln, flip=True, phase=t * 3.2 + q * 1.1 + ri * 2, amp=5 + 2 * (q % 2), lid=lid, shadow=0.6,
                  angle=3 * math.sin(q * 1.9 + ri))
            out.append((x, yy_))
    return out


@lru_cache(maxsize=8)
def _silt_spr(w, h, seed, dark_q):
    rs = random.Random(seed + 3)
    S = (w + 40, h + 30)
    top = [(20 + w * q / 12.0 + rs.uniform(-5, 5), 12 + h - h * (math.sin(math.pi * q / 12.0) ** 0.7) * rs.uniform(0.82, 1.08)) for q in range(13)]
    pts = catmull(top, 5) + [(w + 40, h + 30), (0, h + 30)]
    col = mix_color(PAL["silt"], (8, 26, 30), dark_q / 10.0)
    sp = _paper_piece(S, pts, col, seed=seed + 50, edge=0.2 * (1 - dark_q / 10.0) + 0.04, grain=0.2, shade=(0.3, 1.0, 0.35))
    a = np.asarray(sp, np.float32).copy()
    yy, xx = np.mgrid[0:S[1], 0:S[0]].astype(np.float32)
    ph = ((yy + 0.04 * (xx - S[0] / 2) ** 2 / max(1, w) * 2 + 1.5 * np.sin(xx / 17.0)) / 4.2) % 1.0       # ruled along the mound's curve
    line = np.clip((0.36 - np.abs(ph - 0.5) * 2) / 0.3 + 0.5, 0, 1)
    a[..., :3] *= (1 - 0.4 * line)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def silt(ink, x, y, w=260, h=46, puff=0.0, t=0.0, seed=0, dark=0.0):
    """A mound of river silt (one torn-paper piece, ruled along its curve) with its crest at (x, y): what the
    wreck's nose is dug into. puff 0..1 rolls a slow cloud of mud off it (P4: the tin settles). dark 0..1 turns it
    to a dark shape for the outline shot."""
    sp = _silt_spr(int(w), int(h), int(seed), int(round(clamp(dark) * 10)))
    ink.paste(_shadow_of(sp, 5, 0.45, (0, 12, 14)), (int(x - sp.width / 2 + 3), int(y - 12 - 6)))
    ink.paste(sp, (int(x - sp.width / 2), int(y - 12)))
    if puff > 0:
        rs = random.Random(seed + 9)
        col = mix_color((168, 172, 140), (20, 60, 62), dark)
        for q in range(11):
            a = rs.uniform(0.15, math.pi - 0.15)
            f = clamp(puff * rs.uniform(0.75, 1.25))
            px, py = x + math.cos(a) * w * 0.6 * f + rs.uniform(-16, 16), y + h * 0.25 - math.sin(a) * 54 * f
            rr = (9 + 24 * f) * rs.uniform(0.7, 1.2)
            ink.d.ellipse([px - rr, py - rr * 0.7, px + rr, py + rr * 0.7], fill=col + (int(110 * (1 - f) ** 0.6),))


def wreck(ink, t=0.0, c=None, scale=None, mood="shove", sink=0.0, puff=0.0, outline=0.0, glow=1.0, dial=None, weed_on=True, flip=True, **over):
    """'A ship that sunk': the bread-roll tin lying like a wreck, canted CANT degrees, nose down in the silt, a frond
    of weed already on it, a slow thread of bubbles from its seam. It never sits level and never moves off.
    c = middle of the body (default RIVER['tin_c']); flip=True puts the nose to the RIGHT (the default stage).
    mood = Turkey's black shape in the round window (None = empty lit glass). sink = px it has settled further
    into the silt; puff 0..1 = the mud rolling off as it settles. outline 0..1 turns the whole tin into a dark
    hull shape against the light (P4: read as a sunk ship by its outline). dial = notches to show on the small air
    dial riveted beside the porthole (None = no dial). Returns tin()'s points plus 'dial': (x, y)."""
    c = RIVER["tin_c"] if c is None else c
    scale = RIVER["tin_scale"] if scale is None else scale
    cc = (c[0], c[1] + sink)
    ang = -CANT if flip else CANT
    tp = tin(ink, cc, scale, t, mood=mood, glow=glow, angle=ang, flip=flip, shadow=0.7, dark=outline, **over)
    nx, ny = tp["nose"]
    if weed_on:
        tx, ty = tp["tail"]
        wx, wy = lerp(nx, tx, 0.62), lerp(ny, ty, 0.62) - 96 * scale
        weed(ink, wx, wy + 6, 120 * scale, lean=16 * math.sin(t * 0.7), t=t, seed=3, n=4, spread=22, dark=0.9 * outline + 0.1)
        bubbles(ink, (lerp(nx, tx, 0.42), lerp(ny, ty, 0.42) - 98 * scale), t, t0=math.floor(t / 1.4) * 1.4, n=3, rise=90, size=3.5)
    silt(ink, nx + (-6 if flip else 6) * scale, ny + 14 * scale - sink * 0.5, 300 * scale, 78 * scale, puff, t, seed=2, dark=outline)
    tp["dial"] = tin_dial_xy(tp)
    if dial is not None:
        gauge(ink, dial, *tp["dial"], r=int(27 * scale), t=t)
    return tp


def tin_dial_xy(tp):
    """Where the small air dial is riveted on the tin's flank, from tin()'s returned points: low on the body, just
    tailward of the porthole."""
    px, py = tp["port"]
    tx, ty = tp["tail"]
    return (px + (tx - px) * 0.38, py + (ty - py) * 0.38 + tp["port_r"] * 1.0)


# ------------------------------------------------------- cards, labels, ending ---

PICKS = dict(
    turkey=dict(title="Turkey thinks", rows=[("triangle", "Theater curtain"), ("circle", "Stone tunnel")]),
    trout=dict(title="The trout think", rows=[("cross", "Rivet-toothed monster jaw"), ("square", "Movie projector")]),
)


def bolt_label(ink, n, x=74, y=64, size=44, lit=1.0, word=True, alpha=1.0):
    """The label an ending carries: die face n (ivory) centred at (x, y) with the small word under it (1 and 4
    Probable, 2 and 5 Plausible, 3 and 6 Preposterous) on a dark plate. Default place: top left corner.
    lit=0 for a BLANK bolt (grey die, grey word)."""
    die_face(ink, n, x, y, size, "ivory", lit=lit, alpha=alpha)
    if word:
        s = KINDS[n]
        f = font("mono", 13)
        tw = ink.d.textlength(s, font=f)
        ink.d.rounded_rectangle([x - tw / 2 - 8, y + size * 0.62, x + tw / 2 + 8, y + size * 0.62 + 22], radius=6, fill=PAL["badge"] + (int(225 * alpha),))
        ink.d.text((x, y + size * 0.62 + 11), s, font=f, fill=mix_color((150, 146, 140), PAL["white"], lit) + (int(255 * alpha),), anchor="mm")


def round_scribble(ink, c, r=16, done=1.0, weight=1.2, alpha=0.95, turns=5.0, seed=2):
    """A child colouring in a round button with the pencil, round and round, dark (E. coloured the circle in):
    one spiral stroke from the rim inward, progressive with done 0..1. Returns the pencil point."""
    if done <= 0:
        return None
    rs = random.Random(seed)
    n = int(turns * 26)
    pts = []
    for q in range(int(n * clamp(done)) + 1):
        f = q / n
        a = f * turns * 2 * math.pi - 1.0
        rr = r * (1.02 - 0.86 * f) * (1 + 0.06 * math.sin(a * 2.3 + seed) + rs.uniform(-0.03, 0.03))
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    if len(pts) > 1:
        _pencil_line(ink.d, pts, weight, max(1.0, r / 14.0), alpha)
    return pts[-1]


def end_porthole(ink, c=PORT_C, r=PORT_R, shadow=0.7, faint=0.8, cant=0.0):
    """The ending's porthole: the brass six-bolt ring alone, square on, its glass dark teal with the nine bars and
    the cracks faint in it and no one behind them. On the table: table(ink, sheet=False) first; then bolt_mark()
    each bolt (1 to 4 lit, 5 and 6 with lit=0), die_cup(), pencil(), badge()."""
    r = int(r)
    ro = int(r * RING_OUT / PORT_R)
    S = 2 * r + 2
    lay = Ink(0.0, 0, (ink.w, ink.h))
    glow_ground(lay, c, r, cant, dim=0.62)
    bars(lay, None, c, r, alpha=faint, shadow=0.0)
    cracks(lay, c, r, alpha=faint)
    m = Image.new("L", (ink.w, ink.h), 0)
    ImageDraw.Draw(m).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    rg = brass_ring(r, ro, 6, 10, 3)
    ink.paste(_shadow_of(rg, 9, shadow, (20, 12, 6)), (int(c[0] - rg.width / 2 + 9), int(c[1] - rg.height / 2 + 13)))
    ink.img.paste(lay.img, (0, 0), m)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(4, 20, 22, 150), width=max(4, r // 14))
    ink.d.arc([c[0] - r * 0.86, c[1] - r * 0.86, c[0] + r * 0.86, c[1] + r * 0.86], 200, 256, fill=(240, 252, 244, 70), width=max(2, int(r * 0.04)))
    ink.paste(rg, (int(c[0] - rg.width / 2), int(c[1] - rg.height / 2)))


# ---------------------------------------------------------- ready-made stages ---

def seat_scene(ink, t=0.0, behind=None, front=None, only=None, slide=None, fish=True, fish_kw=None, ring=1.0, tunnel_on=True,
               cross=True, turkey_kw=None, fog_level=0.2, wipes=None, notches=5.0, bolt=None, leak_since=0.0, shift=(0.0, 0.0),
               iris_f=0.0, frame=True):
    """Turkey's seat, looking out, in the ONE draw order this film keeps (back to front):
      glow_ground -> tunnel -> behind(ink) -> shadow fish -> crossbar -> bars -> front(ink) -> stone_ring ->
      crack_bubbles -> cracks -> turkey_reflection -> fog -> iris -> seat_frame -> gauge -> bolt_label.
    behind / front = your own callables drawing things behind the fish (the house) or in front of the bars and
    outside the glass (the padlock, the arm, the curl). only / slide go to bars(). fish=False leaves the fish out
    (draw it yourself in `behind`); fish_kw overrides shadow_fish arguments. ring = stone_ring's done (0 = no stone
    mouth yet). turkey_kw = arguments for turkey_reflection (default mood 'shove'); None still draws him: he is at
    the glass in every beat. fog_level, wipes -> fog(). notches -> gauge(). bolt = n draws bolt_label(n) top left
    and lights that bolt on the ring. shift slides the outside planes (the tin rocks: nearest most). iris_f -> iris().
    Returns {'bars': {k: (x_top, x_mid, x_foot)}, 'cross': y_at(x) or None}."""
    sx, sy = shift
    glow_ground(ink)
    if tunnel_on:
        tunnel(ink, shift=(sx * 0.3, sy * 0.3))
    if behind:
        behind(ink)
    if fish:
        kw = dict(t=t)
        kw.update(fish_kw or {})
        kw.setdefault("cx", STAGE["fish"][0] + sx * 0.55)
        kw.setdefault("cy", STAGE["fish"][1] + sy * 0.55)
        shadow_fish(ink, **kw)
    y_at = crossbar(ink, shift=(sx * 0.8, sy * 0.8)) if cross else None
    bx = bars(ink, only, slide=slide, shift=(sx * 0.8, sy * 0.8))
    if front:
        front(ink)
    if ring > 0:
        stone_ring(ink, ring, c=(PORT_C[0] + sx, PORT_C[1] + sy))
    crack_bubbles(ink, t, since=leak_since)
    cracks(ink)
    tk = dict(mood="shove", t=t)
    tk.update(turkey_kw or {})
    turkey_reflection(ink, **tk)
    fog(ink, fog_level, t, wipes=wipes)
    if iris_f > 0:
        iris(ink, iris_f)
    if frame:
        seat_frame(ink)
        gauge(ink, notches, t=t, tremble=0.5 * breath(t))
        if bolt:
            bolt_mark(ink, bolt, die=False)
            bolt_label(ink, bolt)
    return dict(bars=bx, cross=y_at)


def river_scene(ink, t=0.0, movie=True, audience=True, settle=0.0, dial=5.0, dim=0.0, mood="shove", cone=1.0, tin_on=True, bolt=None,
                bar_shadows=True, darken=0.35):
    """The river side, looking in, in one draw order: river_backdrop (with the culvert wall) -> wall_picture ->
    wreck (the canted tin, Turkey's black shape in its window, the dial) -> river_bars -> light_cone ->
    trout_audience -> bolt_label. movie=False leaves the round picture lit and empty; audience=False, tin_on=False
    and bar_shadows=False strip the stage for a BLANK bolt (light only). dim -> wall_picture's fade. dial = notches.
    Returns {'tin': wreck()'s points or None, 'trout': [(x, y) ...], 'picture': (c, r)}."""
    river_backdrop(ink, t, dim=darken)
    pic = wall_picture(ink, t, show=movie, mood=mood, dim=dim, bar_shadows=bar_shadows) if cone > 0 else (RIVER["picture"], RIVER["picture_r"])
    tp = wreck(ink, t, mood=mood, dial=dial) if tin_on else None
    if tin_on or bar_shadows:
        river_bars(ink)
    if cone > 0:
        src = tp["port"] if tp else (RIVER["tin_c"][0] + 60, RIVER["tin_c"][1])
        light_cone(ink, src, strength=cone, t=t)
    tr = trout_audience(ink, t, settle) if audience else []
    if bolt:
        bolt_label(ink, bolt, lit=1.0 if movie else 0.0)
    return dict(tin=tp, trout=tr, picture=pic)


# ------------------------------------------------------------------ self-test ---

def _still(name, fn, t=1.0):
    out = FILMS / "stills" / "c33_world"
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


def _demo_seat(ink, t):
    seat_scene(ink, t, notches=5 - 0.5, fog_level=0.22, bolt=None)
    badge(ink)


def _demo_trapped(ink, t):
    def front(i):
        y_at = crossbar(i, alpha=0.0)
        x7 = bar_line(7, PILOT_PLACES["crossbar_v"], PORT_C, PORT_R)[0]
        shadow_arm(i, (x7 + 22, 170))
        padlock(i, x7 + 2, y_at(x7) + 6, 26, swing=14 * math.sin(t * 6))
    seat_scene(ink, t, front=front, slide={7: 0.72}, notches=4.4, fog_level=0.3, bolt=1)
    badge(ink)


def _demo_cheeto(ink, t):
    def front(i):
        x = (bar_line(5, 0.2, PORT_C, PORT_R)[0] + bar_line(6, 0.2, PORT_C, PORT_R)[0]) / 2
        cheeto(i, x, PORT_C[1] + 0.2 * PORT_R, 24, angle=20, t=t)
    wipe = [([(430, 150), (455, 230), (486, 300)], 44)]
    seat_scene(ink, t, front=front, notches=3.4, fog_level=0.5, wipes=wipe, bolt=2, turkey_kw=dict(mood="lunge", cx=372, cy=372))
    badge(ink)


def _demo_home(ink, t, push=0.75, cur=0.0):
    def behind(i):
        home(i, push, lamp=1.0, planes=("far", "room"))
        shadow_fish(i, 520, 300, 120, angle=0, t=t)
        home(i, push, planes=("chair", "sill"))
        curtains(i, cur, glow=cur)
        gate(i, 0.9)
    seat_scene(ink, t, behind=behind, fish=False, only=[1, 2, 3, 4, 7, 8, 9], notches=2.3, fog_level=0.72, bolt=3, shift=(0, 0))
    badge(ink)


def _demo_iris(ink, t, f=0.55):
    seat_scene(ink, t, iris_f=f)
    badge(ink)


def _demo_river(ink, t):
    river_scene(ink, t, settle=1.0, dial=4.4, bolt=4)
    badge(ink)


def _demo_blank(ink, t):
    river_scene(ink, t, movie=False, audience=False, mood=None, bar_shadows=False, bolt=5)
    badge(ink)


def _demo_wreck(ink, t):
    glow_ground(ink, (480, 230), 330, 0)
    shadow_fish(ink, 700, 190, 130, angle=8, flip=True, t=t)
    wreck(ink, t, (430, 330), 1.15, mood=None, outline=1.0, puff=0.5, glow=0.25)
    bars(ink, [7, 8, 9], (700, 262), 300)
    badge(ink)


def _demo_window(ink, t):
    river_backdrop(ink, t, wall=False)
    tin_porthole(ink, (480, 262), 200, "shove", t, shake=2)
    badge(ink)


def _demo_turkeys(ink, t):
    ink.fill((226, 220, 204))
    moods = ("calm", "wave", "panic", "freak", "shove", "heavy", "lunge")
    for k, m in enumerate(moods):
        x, y = 100 + (k % 4) * 240, 110 + (k // 4) * 190
        turkey(ink, x, y, 150, m, t + k * 0.13, "bust", shadow=0.6)
        ink.label((x - 60, y + 80), m, 13, anchor="mm")
    turkey_shadow(ink, 830, 300, 150, "shove", t, "bust")
    turkey_shadow(ink, 120, 455, 150, "lunge", t, "full")
    turkey(ink, 360, 455, 150, "calm", t, "full", shadow=0.6)
    turkey(ink, 600, 455, 150, "freak", t, "full", shadow=0.6)
    turkey_shadow(ink, 830, 455, 130, "heavy", t, "head")
    badge(ink)


def _demo_props(ink, t):
    ink.fill((226, 220, 204))
    for k, kind in enumerate(BUTTONS):
        button(ink, kind, 60 + k * 84, 56, 24, pressed=0, lit=1)
        button(ink, kind, 60 + k * 84, 128, 24, pressed=1, lit=1)
        button(ink, kind, 60 + k * 84, 200, 24, pressed=0, lit=0)
    for n in range(1, 7):
        die_face(ink, n, 500 + (n - 1) * 60, 50, 46)
        die_face(ink, n, 500 + (n - 1) * 60, 112, 46, lit=0)
        die_face(ink, n, 500 + (n - 1) * 60, 168, 28, "print")
    bolt_label(ink, 2, 900, 150)
    for k, lv in enumerate((8, 5, 1)):
        gauge(ink, lv, 500 + k * 96, 250, 42)
    ink.d.rectangle([30, 250, 440, 540], fill=PAL["teal"] + (255,))
    for k, (jw, tl) in enumerate(((0, 0), (22, 20), (8, -24))):
        shadow_fish(ink, 130 + k * 140, 300, 130, angle=0, jaw=jw, tail=tl, fins=tl, flip=k == 2)
    padlock(ink, 70, 350, 30)
    padlock(ink, 140, 350, 30, swing=20, open_=1)
    cheeto(ink, 250, 400, 30, t=t)
    cheeto(ink, 360, 400, 18, angle=60, t=t, glow=0.4)
    shadow_arm(ink, (300, 500), root=(450, 470))
    for k, name in enumerate(FLATS):
        flat(ink, name, 520 + (k % 4) * 110, 400 + (k // 4) * 130, 0.8, lit=1.0)
    trout(ink, 130, 480, 170, phase=1.0, shadow=0.7)
    die_cup(ink, 900, 525, 130)
    pencil(ink, (760, 330), 40, length=180)
    badge(ink)


def _demo_cards(ink, t):
    table(ink, sheet=False)
    r1 = pick_card(ink, (250, 140), "turkey", "circle", press=1.0, mark=1.0, initial="E.")
    round_scribble(ink, r1["buttons"]["circle"], 17, 0.8)
    r2 = pick_card(ink, (700, 150), "trout", "square", press=1.0, mark=0.0, scribble=0.7, initial="E.")
    pencil(ink, r2["tip"], 50)
    pick_card(ink, (250, 400), "trout", None)
    stone_ring(ink, 0.6, (700, 400), 120)
    badge(ink)


def _demo_end(ink, t):
    table(ink, sheet=False)
    end_porthole(ink, (480, 232), 180)
    for n in range(1, 7):
        bolt_mark(ink, n, lit=1.0 if n <= 4 else 0.0, c=(480, 232), r=180)
    die_cup(ink, 850, 510, 150)
    pencil(ink, (640, 500), 12, lift=0.0, length=220)
    badge(ink)


def _demo_page_port(ink, t):
    table(ink, sheet=False)
    porthole_on_table(ink, drawing=1.0)
    iris(ink, 0.35)
    badge(ink)


if __name__ == "__main__":
    import time
    _t0 = time.time()
    want = sys.argv[1:]
    demos = [("01_table_drawing_3s", _demo_table, 3.4), ("02_table_fish", _demo_table, 5.6), ("03_table_done", _demo_table, 7.9),
             ("04_page_under_porthole", _demo_page_port, 1.0), ("05_wreck_outline", _demo_wreck, 1.1), ("06_window_shove", _demo_window, 1.15),
             ("07_seat", _demo_seat, 1.2), ("08_seat_trapped", _demo_trapped, 1.1), ("09_seat_cheeto", _demo_cheeto, 1.3),
             ("10_seat_home", _demo_home, 1.2), ("11_seat_home_curtains", lambda i, t: _demo_home(i, t, 1.0, 1.0), 1.2),
             ("12_iris", _demo_iris, 1.0), ("13_iris_nearly_shut", lambda i, t: _demo_iris(i, t, 0.9), 1.0),
             ("14_river_movie", _demo_river, 1.15), ("15_river_blank", _demo_blank, 1.0), ("16_turkeys", _demo_turkeys, 0.7),
             ("17_props", _demo_props, 1.0), ("18_cards", _demo_cards, 1.0), ("19_end", _demo_end, 1.0)]
    for name, fn, tt in demos:
        if not want or any(w in name for w in want):
            _still(name, fn, tt)
    print("stills in %.1f s" % (time.time() - _t0))
