"""p44 · Rotor · a spinning black-and-white disc with a sentence set in a spiral.

Lineage: the spinning lettered optical disc. Handmade here: a card disc on an iron banding wheel is inked
with one spiral band (a flat brush on a rule, the wheel turning under it), then with three eccentric rings
(the disc re-pinned off centre for each, a ruling pen held still). An original sentence is then set in
cut-paper letters, one at a time, from both ends of the spiral toward the middle, because the sentence is a
palindrome: NOW TRAP A POOL · ROTOR · LOOP A PART WON. Twelve brass tacks go round the rim.
Then the disc turns in the river: seen through Turkey's porthole, and from the river side.

Rule (Rotating Type & Depth): the type only rotates; the depth is made by the eye. Turned one way the
spiral drains toward the hub, turned the other it pours out; at 2 turns a second the twelve tacks stand
still against the 24 frames a second while the letters blur away.

    python3 films/p44.py --stills 2 6 10 14 18 22 26 30
    python3 films/p44.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import *  # noqa
from kit_anim import contact  # noqa

SLUG = "p44"
SECONDS = 34.0
T2 = 15.3          # cut: bench -> through the porthole
T3 = 24.7          # cut: the river side
SRC = HERE / "sources" / SLUG
CACHE = SRC / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
VER = "v1"
MURK = np.array([30, 84, 84], np.float32)


# ---------------------------------------------------------------- helpers ---
# (vnoise .. Spring are the shared porthole-film helpers, as written for p14: value noise, the Denton trout
#  and Audubon turkey cutouts, the turned brass ring, the bread-roll tin.)

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


def rgba(arr, alpha):
    return Image.fromarray(np.dstack([np.clip(arr, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8), "RGBA")


def drop(cv, layer, off=(6, 9), blur=4.0, alpha=0.42):
    """Paste an RGBA layer with the shadow it throws on what is under it."""
    sh = Image.new("RGBA", layer.size, (8, 6, 4, 0))
    sh.putalpha(layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha)))
    cv.paste(sh, (int(off[0]), int(off[1])), sh)
    cv.paste(layer, (0, 0), layer)


# ============================================================ the sentence ===
TEXT = "NOW TRAP A POOL · ROTOR · LOOP A PART WON"
assert TEXT == TEXT[::-1], "the sentence must read the same from the hub as from the rim, spaces included"
PIECES = [ch for ch in TEXT if ch != " "]
NPC = len(PIECES)                                  # 31 pieces of paper
ORDER = []                                         # set from both ends of the spiral toward the middle
for _i in range(NPC // 2):
    ORDER += [_i, NPC - 1 - _i]
ORDER.append(NPC // 2)
assert all(PIECES[a] == PIECES[b] for a, b in zip(ORDER[0:-1:2], ORDER[1::2]))

# ---- the disc, radius 1
R0C, R1C, PHI_END = 0.86, 0.45, 3 * math.pi         # spiral band centreline: rim end, hub end, 1.5 turns
PITCH = (R0C - R1C) / (PHI_END / (2 * math.pi))
BW = 0.175                                         # band width
RINGS = [(0.022, 0.29), (0.044, 0.215), (0.066, 0.14)]     # (how far off centre, radius)
RING_W = 0.04
TACK_R, TACK_N = 0.968, 12
CAP = 0.104                                        # cap height of the letters
RT = 430                                           # disc radius in texture pixels
CT = RT + 14
DT = 2 * CT
WR = 1.09                                          # the iron wheel under it
WC = int(RT * WR) + 22
WT = 2 * WC
FONT_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
TWO_PI = 2 * math.pi


def spiral_r(phi):
    return R0C - PITCH * phi / TWO_PI


def polar(r, phi):
    """phi clockwise from the top."""
    return (r * math.sin(phi), -r * math.cos(phi))


D = {}          # disc arrays


def build_disc():
    yy, xx = np.mgrid[0:DT, 0:DT].astype(np.float32)
    x, y = (xx - CT) / RT, (yy - CT) / RT
    r = np.hypot(x, y)
    phi = np.mod(np.arctan2(x, -y), TWO_PI)
    rs = np.random.RandomState(4)
    wob = (vnoise((DT, DT), 30, seed=3, octaves=2) - 0.5) * 0.012
    bris = np.convolve(rs.uniform(0, 1, 72), [0.2, 0.6, 0.2], "same")
    A_ = np.zeros((DT, DT), np.float32)
    P = np.zeros_like(A_)
    Dn = np.zeros_like(A_)
    for k in (-1, 0, 1):
        pk = phi + TWO_PI * k
        pc = np.clip(pk, 0, PHI_END)
        d = r - spiral_r(pc)
        ex = np.maximum(0, np.maximum(-pk, pk - PHI_END)) * r
        hw = BW / 2 * (1 + 0.03 * np.sin(pk * 5.3 + 1) + 0.018 * np.sin(pk * 13.1))
        a = np.clip((hw - np.hypot(d, ex * 1.25) - wob) * RT / 1.4 + 0.5, 0, 1)
        a[(pk < -0.6) | (pk > PHI_END + 0.6)] = 0
        b = a > A_
        A_, P, Dn = np.where(b, a, A_), np.where(b, pk, P), np.where(b, d / hw, Dn)
    bt = np.interp((np.clip(Dn, -1, 1) + 1) / 2 * 71, np.arange(72), bris).astype(np.float32)
    along = vnoise((DT, DT), 9, seed=5)
    dry = np.clip((P - (PHI_END - 1.1)) / 1.1, 0, 1) ** 1.5              # the brush runs dry at the hub end
    A_ = A_ * (1 - dry * np.clip((bt - 0.42) * 5 + (along - 0.5) * 2.2, 0, 1) * 0.9)
    D["ink_a"] = A_
    D["ink_p"] = P
    D["ink_pe"] = P + (bt - 0.5) * 0.07                                   # a ragged leading edge, bristle by bristle
    tone = 21 + 15 * bt + 10 * (along - 0.5)
    D["ink_rgb"] = tone[..., None] * np.array([1.0, 0.97, 1.06], np.float32)
    D["ink_spec"] = np.exp(-((Dn - 0.15) / 0.4) ** 2) * (0.55 + 0.9 * bt)
    D["ring_a"], D["ring_ang"] = [], []
    for e, rad in RINGS:
        dx, dy = x, y + e
        dj = np.abs(np.hypot(dx, dy) - rad)
        D["ring_a"].append(np.clip((RING_W / 2 - dj - wob * 0.35) * RT / 1.3 + 0.5, 0, 1))
        D["ring_ang"].append(np.mod(np.arctan2(dx, -dy), TWO_PI))
    fib = vnoise((DT, DT), 3, seed=7)
    mot = vnoise((DT, DT), 110, seed=8, octaves=3)
    pap = np.array([238, 231, 210], np.float32)[None, None] * (0.925 + 0.05 * fib + 0.085 * mot)[..., None]
    pap *= (1 - 0.22 * np.clip((r - 0.984) / 0.016, 0, 1))[..., None]
    pa = np.clip((1 - r) * RT + 0.5, 0, 1)
    D["paper"] = pap * pa[..., None]
    D["pa"] = pa
    D["halo"] = np.maximum(pa, np.clip(1 - (r - 1) * RT / 12, 0, 1) ** 2 * 0.5 * (r >= 1))
    # ---- the letters: cut paper
    f = ImageFont.truetype(FONT_B, 100)
    hb = f.getbbox("H")
    f = ImageFont.truetype(FONT_B, int(round(100 * CAP * RT / (hb[3] - hb[1]))))
    hb = f.getbbox("H")
    cap_px = hb[3] - hb[1]
    rs = np.random.RandomState(12)
    glyph = {}
    for ch in sorted(set(PIECES)):
        if ch == "·":
            dd = int(cap_px * 0.36)
            m = Image.new("L", (dd + 12, cap_px + 12), 0)
            ImageDraw.Draw(m).ellipse([6, 6 + (cap_px - dd) // 2, 6 + dd, 6 + (cap_px - dd) // 2 + dd], fill=255)
        else:
            bb = f.getbbox(ch)
            m = Image.new("L", (bb[2] - bb[0] + 12, cap_px + 12), 0)
            ImageDraw.Draw(m).text((6 - bb[0], 6 - hb[1]), ch, font=f, fill=255)
        glyph[ch] = m
    widths = [(glyph[ch].width - 12) / RT if ch != " " else 0.06 for ch in TEXT]
    ph = np.linspace(0, PHI_END, 6000)
    seg = np.hypot(spiral_r(ph), PITCH / TWO_PI)
    s = np.concatenate([[0], np.cumsum((seg[1:] + seg[:-1]) / 2 * np.diff(ph))])
    sa, sb = np.interp(0.11, ph, s), np.interp(PHI_END - 0.11, ph, s)
    gap = ((sb - sa) - sum(widths)) / (len(TEXT) - 1)
    D["letters"] = []
    pos = sa
    for ch, w in zip(TEXT, widths):
        c = pos + w / 2
        pos += w + gap
        if ch == " ":
            continue
        p = float(np.interp(c, s, ph))
        rr = spiral_r(p) + rs.uniform(-0.005, 0.005)
        rot = p + math.atan(PITCH / (TWO_PI * rr)) + math.radians(rs.uniform(-2.4, 2.4))
        m = glyph[ch]
        tone = rs.uniform(0.95, 1.03)
        fibre = vnoise((m.height, m.width), 3, seed=int(rs.randint(1e6)))
        inner = np.asarray(m.filter(ImageFilter.MinFilter(3)), np.float32) / 255
        col = np.array([243, 237, 219], np.float32)[None, None] * (tone * (0.9 + 0.08 * fibre + 0.06 * inner))[..., None]
        up = rgba(col, np.asarray(m, np.float32) / 255)
        D["letters"].append(dict(ch=ch, phi=p, r=rr, rot=rot, up=up, xy=polar(rr, p)))
    assert len(D["letters"]) == NPC
    D["gap"] = gap
    D["phi_mid"] = D["letters"][NPC // 2]["phi"]          # the middle T: the sentence turns round here
    t0 = (math.degrees(D["phi_mid"]) + 15) % 30           # tacks sit either side of it
    D["tack0"] = math.radians(t0 + 30 * round((75 - t0) / 30))
    for L in D["letters"]:
        im = L["up"].rotate(-math.degrees(L["rot"]), expand=True, resample=Image.BICUBIC)
        L["im"] = im
        L["at"] = (int(round(CT + L["xy"][0] * RT - im.width / 2)), int(round(CT + L["xy"][1] * RT - im.height / 2)))
    # ---- brass: tacks and the hub pin (rotation-proof little domes)
    def dome(rad, col=(214, 174, 86)):
        n = int(rad * 2 + 8)
        yy_, xx_ = np.mgrid[0:n, 0:n].astype(np.float32)
        q = np.hypot(xx_ - n / 2, yy_ - n / 2) / rad
        l_ = np.clip(1.12 - 0.62 * q ** 2 + 0.5 * np.exp(-(q / 0.33) ** 2), 0, 1.6)
        c = np.array(col, np.float32)[None, None] * l_[..., None]
        c[(q > 0.86)] *= 0.55
        sh = np.clip(1 - (q - 1) * rad / 3.0, 0, 1) * 0.55 * (q >= 1)
        a = np.maximum(np.clip((1 - q) * rad + 0.5, 0, 1), sh)
        c[q >= 1] = 10
        return rgba(c, a)
    D["tack"] = dome(0.019 * RT)
    D["hub"] = dome(0.034 * RT)
    D["pin"] = dome(0.016 * RT)


def disc_img(phi_now=None, wetphi=0.0, rings=((1, 0), (1, 0), (1, 0)), letters=0, tacks=0, hub=False, halo=True):
    """The disc as it stands: how far the spiral is inked, each ring (fraction, start angle), paper letters, tacks."""
    col = D["paper"]
    if phi_now is None:
        rev = D["ink_a"]
        inkc = D["ink_rgb"]
    else:
        rev = D["ink_a"] * np.clip((phi_now - D["ink_pe"]) / 0.03, 0, 1)
        wet = np.clip(1 - (wetphi - D["ink_p"]) / 2.6, 0, 1) ** 1.5
        inkc = D["ink_rgb"] + (D["ink_spec"] * wet)[..., None] * np.array([64, 74, 92], np.float32)
    col = col * (1 - rev[..., None]) + inkc * rev[..., None]
    for j, (q, a0) in enumerate(rings):
        if q <= 0:
            continue
        a = D["ring_a"][j]
        if q < 1:
            rel = np.mod(D["ring_ang"][j] - a0, TWO_PI)
            a = a * np.clip((q * TWO_PI - rel) / 0.03, 0, 1)
            wet = np.clip(1 - (q * TWO_PI - rel) / 2.2, 0, 1)
            col = col * (1 - a[..., None]) + (np.array([24, 23, 27], np.float32) + wet[..., None] * np.array([70, 80, 96], np.float32)) * a[..., None]
        else:
            col = col * (1 - a[..., None]) + np.array([24, 23, 27], np.float32) * a[..., None]
    img = rgba(col, D["halo"] if halo else D["pa"])
    d = ImageDraw.Draw(img, "RGBA")
    nh = sum(1 for q, _ in rings if q > 0)
    for e, _ in [(0.0, 0)] + RINGS[:nh]:                 # the pin holes each centre left
        d.ellipse([CT - 2.2, CT + (-e) * RT - 2.2, CT + 2.2, CT + (-e) * RT + 2.2], fill=(70, 60, 48, 230))
    for m in ORDER[:letters]:
        L = D["letters"][m]
        img.alpha_composite(L["im"], L["at"])
    tk = D["tack"]
    for k in range(tacks):
        px, py = polar(TACK_R, D["tack0"] + math.radians(30 * k))
        img.alpha_composite(tk, (int(CT + px * RT - tk.width / 2), int(CT + py * RT - tk.height / 2)))
    if hub:
        img.alpha_composite(D["hub"], (CT - D["hub"].width // 2, CT - D["hub"].height // 2))
    return img


def build_wheel():
    yy, xx = np.mgrid[0:WT, 0:WT].astype(np.float32)
    r = np.hypot(xx - WC, yy - WC) / RT
    rs = np.random.RandomState(31)
    lathe = np.interp(r * RT, np.arange(0, WT), np.convolve(rs.uniform(-1, 1, WT), [0.3, 0.4, 0.3], "same"))
    base = 70 + 13 * lathe + 16 * (vnoise((WT, WT), 70, seed=32, octaves=3) - 0.5)
    base += 34 * np.clip((r - (WR - 0.022)) / 0.022, 0, 1) * (r < WR)           # the turned bevel at the edge
    col = base[..., None] * np.array([0.96, 1.0, 1.04], np.float32)
    rust = np.clip((vnoise((WT, WT), 36, seed=33, octaves=3) - 0.68) * 7, 0, 1)[..., None]
    col = col * (1 - rust * 0.55) + np.array([110, 68, 42], np.float32) * rust * 0.55
    img = rgba(col, np.clip((WR - r) * RT + 0.5, 0, 1))
    d = ImageDraw.Draw(img, "RGBA")
    for k in range(3):                                     # chalk marks at the rim, so the turning shows
        a = math.radians(20 + 120 * k)
        for q in (-0.012, 0.0, 0.012) if k == 0 else (0.0,):
            p0, p1 = polar(1.022 * RT, a + q), polar(1.078 * RT, a + q)
            d.line([(WC + p0[0], WC + p0[1]), (WC + p1[0], WC + p1[1])], fill=(226, 224, 210, 220), width=4)
    D["wheel"] = img


# ================================================================ the bench ===
DC = (318, 272)        # the wheel's axis on screen
RB = 205               # the disc's radius on the bench
KB = RB / RT
PHI_B = math.radians(50)                 # where the rule crosses: the tool's station, clockwise from the top
UB = (math.sin(PHI_B), -math.cos(PHI_B))  # along the rule, outward
VB = (math.cos(PHI_B), math.sin(PHI_B))   # along the tool's handle
T_DOWN, T_UP = 0.5, 3.8
W1 = PHI_END / (T_UP - T_DOWN)           # wheel speed while the spiral is inked, rad/s
W2 = TWO_PI / 0.7                        # and for the rings: one turn each
RING_T = [(4.5, 5.2), (5.4, 6.1), (6.3, 7.0)]
T_SET = 7.5                              # the first letter
T_TACK = 13.25
TACK_DT = 0.14
T_FLICK = T_TACK + TACK_N * TACK_DT + 0.02
TRAY = (706, 38, 814, 492)
DISH = (612, 150)
REST = (652, 418)
WRIST = (1090, 700)
M = {}                 # tracks for the making


def build_making():
    dt = 1 / 480
    ts = np.arange(0, 7.0 + dt, dt)
    w = np.interp(ts, [0, 3.9, 4.4, 7.0], [W1, W1, W2, W2])
    rho = PHI_B - (np.cumsum(w) * dt - np.interp(T_DOWN, ts, np.cumsum(w) * dt))
    M["ts"], M["rho"] = ts, rho
    r7 = rho[-1]
    M["r7"], M["r8"] = r7, TWO_PI * math.floor((r7 - 1.3) / TWO_PI)
    durs = [0.5, 0.5, 0.3, 0.3, 0.3, 0.3] + [0.14] * (NPC - 6)
    M["set_a"] = np.concatenate([[T_SET], T_SET + np.cumsum(durs)[:-1]])
    M["set_d"] = np.array(durs)
    assert M["set_a"][-1] + durs[-1] < T_TACK
    # the galley: the pairs side by side, in the order they are set
    M["tray"] = {}
    for n, m in enumerate(ORDER):
        row = n // 2
        cx = (TRAY[0] + TRAY[2]) / 2 + (0 if m == NPC // 2 else (-23 if n % 2 == 0 else 23))
        M["tray"][m] = (cx, TRAY[1] + 22 + row * 27.4)
    for L in D["letters"]:
        L["bench"] = L["up"].resize((max(2, int(L["up"].width * KB)), max(2, int(L["up"].height * KB))), Image.LANCZOS)
        L["slot"] = (DC[0] + L["xy"][0] * RB, DC[1] + L["xy"][1] * RB)


def rho_at(t):
    """How far the wheel has turned (clockwise positive)."""
    if t <= 7.0:
        return float(np.interp(t, M["ts"], M["rho"]))
    if t < T_SET:
        u = (t - 7.0) / 0.5
        h00, h10, h01 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2
        return h00 * M["r7"] + h10 * (-W2 * 0.5) + h01 * M["r8"]
    if t < T_TACK:
        return 0.0
    if t < T_FLICK:
        k = min(TACK_N - 1, int((t - T_TACK) / TACK_DT))
        u = (t - T_TACK) / TACK_DT - k
        return -(math.pi / 6) * (k - 1 + smooth(u / 0.5)) if k >= 1 else 0.0
    u = t - T_FLICK
    return -(math.pi / 6) * (TACK_N - 1) - (math.pi * 0.5 * u * u / 0.25 if u < 0.25 else math.pi * (0.125 + (u - 0.25)))


def ecc_at(t):
    e = [0.0] + [r_[0] for r_ in RINGS]
    return (e[1] * ease(t, 3.9, 4.4) + (e[2] - e[1]) * ease(t, 5.2, 5.4) + (e[3] - e[2]) * ease(t, 6.1, 6.3)) * (1 - ease(t, 7.02, 7.4))


def stick_at(t):
    """Tip of the pick-up stick, how far it is lifted, and the piece it carries (index, or 'tack')."""
    if t < 7.0:
        return None
    if t < T_SET:
        return lerp2((1000, 600), REST, ease(t, 7.0, T_SET)), 1.0, None
    if t < T_TACK:
        n = int(np.searchsorted(M["set_a"], t, side="right") - 1)
        m = ORDER[n]
        u = (t - M["set_a"][n]) / M["set_d"][n]
        prev = D["letters"][ORDER[n - 1]]["slot"] if n else REST
        tray, slot = M["tray"][m], D["letters"][m]["slot"]
        if u < 0.3:
            return lerp2(prev, tray, smooth(u / 0.3)), math.sin(math.pi * u / 0.3), None
        if u < 0.4:
            return tray, 0.0, None
        if u < 0.8:
            f = smooth((u - 0.4) / 0.4)
            return lerp2(tray, slot, f), math.sin(math.pi * f), (m, f)
        return slot, 0.0, None
    st = (DC[0] + TACK_R * RB * math.sin(D["tack0"]), DC[1] - TACK_R * RB * math.cos(D["tack0"]))
    if t < T_FLICK:
        k = min(TACK_N - 1, int((t - T_TACK) / TACK_DT))
        u = (t - T_TACK) / TACK_DT - k
        if u < 0.12:
            return DISH, 0.0, None
        if u < 0.55:
            f = smooth((u - 0.12) / 0.43)
            return lerp2(DISH, st, f), math.sin(math.pi * f), "tack"
        if u < 0.8:
            return st, 0.0, None
        f = smooth((u - 0.8) / 0.2)
        return lerp2(st, DISH, f), math.sin(math.pi * f), None
    u = t - T_FLICK
    p0 = (DC[0] + RB * 1.0 * math.sin(2.0), DC[1] - RB * 1.0 * math.cos(2.0))
    p1 = (DC[0] + RB * 1.02 * math.sin(1.1), DC[1] - RB * 1.02 * math.cos(1.1))
    if u < 0.08:
        return lerp2(DISH, p0, smooth(u / 0.08)), 0.5, None
    f = smooth((u - 0.08) / 0.17)
    return lerp2(p0, lerp2(p1, (700, 60), ease(u, 0.25, 0.6)), f), 0.3 * ease(u, 0.2, 0.5), None


def letters_set(t):
    if t < T_SET:
        return 0
    return int(np.sum(M["set_a"] + 0.8 * M["set_d"] <= t))


def letters_picked(t):
    return int(np.sum(M["set_a"] + 0.4 * M["set_d"] <= t)) if t >= T_SET else 0


def tacks_set(t):
    return int(np.clip(math.floor((t - T_TACK) / TACK_DT + 0.45), 0, TACK_N)) if t >= T_TACK else 0


def build_bench():
    rs = np.random.RandomState(40)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = vnoise((H, W), 420, 5, seed=21, octaves=3)
    g2 = vnoise((H, W), 60, 2, seed=22, octaves=2)
    plank = np.floor(yy / 152)
    tone = 0.9 + 0.14 * np.sin(plank * 2.3 + 1.0)
    a = np.array([164, 122, 78], np.float32)[None, None] * (tone * (0.74 + 0.36 * g + 0.12 * g2 + 0.03 * np.sin(yy * 1.9 + g * 40)))[..., None]
    fine = vnoise((H, W), 240, 1.4, seed=23) - 0.5
    a *= (1 + 0.16 * fine)[..., None]
    a[..., 2] *= 0.93
    seam = np.exp(-((np.mod(yy, 152) - 150) / 0.9) ** 2)
    a *= (1 - 0.6 * seam)[..., None]
    for _ in range(5):                                      # knots
        kx, ky, kr = rs.uniform(0, W), rs.uniform(0, H), rs.uniform(7, 16)
        q = np.hypot((xx - kx) / 1.9, yy - ky) / kr
        a *= (1 - 0.34 * np.exp(-q ** 2) + 0.08 * np.exp(-((q - 1.5) / 0.4) ** 2))[..., None]
    img = to_img(a).convert("RGB")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, "RGBA")
    # the galley: a baize-lined tray
    x0, y0, x1, y1 = TRAY
    d.rounded_rectangle([x0 - 9, y0 - 9, x1 + 9, y1 + 9], radius=4, fill=(92, 62, 38, 255), outline=(44, 28, 16, 255), width=2)
    bz = np.array([44, 78, 64], np.float32)[None, None] * (0.82 + 0.3 * vnoise((y1 - y0, x1 - x0), 3, seed=41) * vnoise((y1 - y0, x1 - x0), 40, seed=42))[..., None]
    lay.paste(to_img(bz), (x0, y0))
    d = ImageDraw.Draw(lay, "RGBA")
    d.line([(x0, y0), (x1, y0)], fill=(16, 26, 22, 255), width=4)
    d.line([(x0, y0), (x0, y1)], fill=(16, 26, 22, 255), width=3)
    d.line([((x0 + x1) / 2, y0 + 6), ((x0 + x1) / 2, y1 - 36)], fill=(226, 220, 196, 60), width=1)
    # the ink pot
    px, py = 890, 96
    d.ellipse([px - 44, py - 44, px + 44, py + 44], fill=(70, 74, 78, 255), outline=(20, 22, 24, 255), width=2)
    d.ellipse([px - 33, py - 33, px + 33, py + 33], fill=(10, 10, 14, 255))
    d.chord([px - 30, py - 30, px + 30, py + 30], 195, 300, fill=(64, 72, 92, 255))
    d.ellipse([px - 27, py - 25, px + 31, py + 33], fill=(10, 10, 14, 255))
    d.arc([px - 41, py - 41, px + 41, py + 41], 180, 300, fill=(190, 196, 200, 255), width=3)
    # the dish of tacks
    px, py = DISH
    d.ellipse([px - 27, py - 27, px + 27, py + 27], fill=(150, 114, 50, 255), outline=(52, 36, 14, 255), width=2)
    d.ellipse([px - 21, py - 21, px + 21, py + 21], fill=(92, 66, 28, 255))
    d.arc([px - 25, py - 25, px + 25, py + 25], 170, 300, fill=(240, 212, 140, 255), width=2)
    for _ in range(26):
        ang, rr = rs.uniform(0, 6.28), 17 * math.sqrt(rs.uniform(0, 1))
        tx, ty = px + rr * math.cos(ang), py + rr * math.sin(ang)
        d.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=(206, 166, 80, 255), outline=(60, 42, 16, 255))
        d.ellipse([tx - 2, ty - 3, tx + 1, ty], fill=(252, 232, 170, 255))
    # the plan, in pencil, pinned by the pot
    note = Image.new("RGBA", (128, 150), (232, 226, 206, 255))
    na = np.asarray(note, np.float32).copy()
    na[..., :3] *= (0.93 + 0.09 * vnoise((150, 128), 30, seed=44, octaves=2))[..., None]
    note = Image.fromarray(na.astype(np.uint8), "RGBA")
    nk = Ink(0, 0, (128, 150))
    nk.img = note
    nk.d = ImageDraw.Draw(note, "RGBA")
    from kit_anim import hand_text
    yq = 12
    for line in ("now trap", "a pool ·", "rotor", "· loop a", "part won"):
        hand_text(nk, (12 + (22 if line == "rotor" else 0), yq), line, size=17, color=(70, 70, 82), seed=len(line) + yq)
        yq += 24
    nd = ImageDraw.Draw(nk.img, "RGBA")
    nd.arc([84, 20, 118, 126], -70, 70, fill=(140, 60, 50, 220), width=2)
    nd.polygon([(101, 20), (112, 21), (106, 30)], fill=(140, 60, 50, 220))
    nd.polygon([(101, 126), (112, 125), (106, 116)], fill=(140, 60, 50, 220))
    note = nk.img.rotate(4, expand=True, resample=Image.BICUBIC)
    lay.alpha_composite(note, (828, 176))
    d = ImageDraw.Draw(lay, "RGBA")
    d.ellipse([886, 180, 898, 192], fill=(196, 60, 50, 255), outline=(70, 20, 16, 255))
    # the wheel's shadow, then everything that stands on the bench
    sh = Image.new("L", (W, H), 0)
    ws = WC * KB
    ImageDraw.Draw(sh).ellipse([DC[0] - RB * WR + 9, DC[1] - RB * WR + 13, DC[0] + RB * WR + 9, DC[1] + RB * WR + 13], fill=150)
    img.paste(Image.new("RGB", (W, H), (14, 9, 5)), (0, 0), sh.filter(ImageFilter.GaussianBlur(9)))
    drop(img, lay, off=(5, 8), blur=5, alpha=0.5)
    M["bench"] = img
    lx = np.exp(-(((xx - 300) / 620) ** 2 + ((yy - 190) / 430) ** 2))
    M["light"] = to_img((0.6 + 0.48 * lx)[..., None] * np.array([255, 249, 236], np.float32)[None, None])


def quad(p, a0, b0, a1, b1, axis_a=VB, axis_b=UB):
    """Corners of a strip in a tool's own frame: a along its length, b across."""
    def P(a, b):
        return (p[0] + axis_a[0] * a + axis_b[0] * b, p[1] + axis_a[1] * a + axis_b[1] * b)
    return [P(a0, -b0), P(a0, b0), P(a1, b1), P(a1, -b1)]


def draw_rule_tool(cv, t):
    """The steel rule across the wheel, its brass carriage, and the brush or the ruling pen clamped in it."""
    slide = 520 * ((1 - ease(t, 0.0, 0.45)) + ease(t, 3.85, 4.15) - ease(t, 4.15, 4.45) + ease(t, 7.0, 7.4))
    if slide >= 519:
        return
    brush = t < 4.15
    if brush:
        rc = spiral_r(np.clip(W1 * (t - T_DOWN), 0, PHI_END))
        down = T_DOWN <= t <= T_UP
    else:
        r1, r2, r3 = [r_[1] for r_ in RINGS]
        rc = r1 + (r2 - r1) * ease(t, 5.2, 5.4) + (r3 - r2) * ease(t, 6.1, 6.3)
        down = any(a <= t <= b for a, b in RING_T)
    lift = 0.0 if down else 1.0
    tip = (DC[0] + UB[0] * (rc * RB + slide) - VB[0] * 3 * lift, DC[1] + UB[1] * (rc * RB + slide) - VB[1] * 3 * lift)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, "RGBA")
    if brush:
        hw = BW * RB / 2
        d.polygon(quad(tip, -4, hw, 26, hw - 2), fill=(26, 24, 26, 255))
        for q in range(-4, 5):
            d.line([quad(tip, 2, 0, 26, 0)[0][0] + UB[0] * q * hw / 5, quad(tip, 2, 0, 26, 0)[0][1] + UB[1] * q * hw / 5,
                    quad(tip, 2, 0, 26, 0)[2][0] + UB[0] * q * hw / 5.4, quad(tip, 2, 0, 26, 0)[2][1] + UB[1] * q * hw / 5.4], fill=(58, 54, 56, 255), width=1)
        d.polygon(quad(tip, 26, hw - 2, 54, 12), fill=(172, 178, 182, 255), outline=(40, 44, 48, 255))
        d.line(quad(tip, 30, hw - 9, 52, 6)[0:4:3], fill=(240, 244, 244, 255), width=3)
        d.polygon(quad(tip, 54, 11, 250, 5), fill=(146, 44, 34, 255), outline=(50, 14, 10, 255))
        d.line(quad(tip, 58, 6, 244, 2.5)[0:4:3], fill=(232, 150, 120, 255), width=2)
    else:
        d.polygon(quad(tip, 0, 0.8, 34, 3.4), fill=(200, 206, 210, 255), outline=(36, 40, 44, 255))
        d.line(quad(tip, 0, 0, 34, 0)[0:4:3], fill=(30, 30, 34, 255), width=1)
        cq = quad(tip, 20, 0, 20, 0)[0]
        d.ellipse([cq[0] - 4, cq[1] - 4, cq[0] + 4, cq[1] + 4], fill=(206, 166, 80, 255), outline=(60, 42, 16, 255))
        d.polygon(quad(tip, 34, 4.5, 230, 3.5), fill=(34, 34, 40, 255), outline=(8, 8, 10, 255))
        d.line(quad(tip, 40, 2, 224, 1.5)[0:4:3], fill=(120, 124, 134, 255), width=1)
    # the rule, parallel to the radius, through the carriage
    ca = 40.0
    c0 = (DC[0] + VB[0] * ca + UB[0] * slide, DC[1] + VB[1] * ca + UB[1] * slide)
    rule = quad(c0, -70, 9, 900, 9, axis_a=UB, axis_b=VB)
    d.polygon(rule, fill=(158, 166, 172, 255), outline=(40, 46, 52, 255))
    d.line([rule[0], rule[3]], fill=(236, 240, 242, 255), width=2)
    for q in range(-6, 90):
        e0 = quad(c0, q * 10, 9, q * 10, 9, axis_a=UB, axis_b=VB)
        ln = 8 if q % 5 == 0 else 4
        d.line([e0[1], (e0[1][0] - VB[0] * ln, e0[1][1] - VB[1] * ln)], fill=(50, 56, 62, 255), width=1)
    cc = (tip[0] + VB[0] * ca + VB[0] * 3 * lift, tip[1] + VB[1] * ca + VB[1] * 3 * lift)
    blk = quad(cc, -15, 21, 15, 21)
    d.polygon(blk, fill=(188, 148, 66, 255), outline=(60, 42, 16, 255))
    d.line([blk[0], blk[3]], fill=(250, 226, 150, 255), width=2)
    d.ellipse([cc[0] - 9, cc[1] - 9, cc[0] + 9, cc[1] + 9], fill=(214, 176, 90, 255), outline=(60, 42, 16, 255), width=2)
    d.line([(cc[0] - 6, cc[1] - 3), (cc[0] + 6, cc[1] + 3)], fill=(70, 50, 20, 255), width=2)
    drop(cv, lay, off=(5 + 4 * lift, 8 + 6 * lift), blur=3.5 + 2 * lift, alpha=0.45)


def draw_stick(cv, tip, lift):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, "RGBA")
    tip = (tip[0] - 2 * lift, tip[1] - 5 * lift)
    dx, dy = WRIST[0] - tip[0], WRIST[1] - tip[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    far = (tip[0] + ux * ln, tip[1] + uy * ln)
    d.polygon([(tip[0] + nx * 2.2, tip[1] + ny * 2.2), (tip[0] - nx * 2.2, tip[1] - ny * 2.2), (far[0] - nx * 8, far[1] - ny * 8), (far[0] + nx * 8, far[1] + ny * 8)],
              fill=(212, 178, 122, 255), outline=(84, 60, 34, 255))
    d.line([(tip[0] + ux * 16 - nx * 1.2, tip[1] + uy * 16 - ny * 1.2), (far[0] - nx * 4, far[1] - ny * 4)], fill=(246, 226, 180, 255), width=2)
    d.polygon([(tip[0] + nx * 2.6, tip[1] + ny * 2.6), (tip[0] - nx * 2.6, tip[1] - ny * 2.6), (tip[0] + ux * 15 - nx * 3.2, tip[1] + uy * 15 - ny * 3.2), (tip[0] + ux * 15 + nx * 3.2, tip[1] + uy * 15 + ny * 3.2)],
              fill=(120, 44, 40, 255))
    d.ellipse([tip[0] - 3.4, tip[1] - 3.4, tip[0] + 3.4, tip[1] + 3.4], fill=(120, 44, 40, 255))
    drop(cv, lay, off=(5 + 8 * lift, 8 + 12 * lift), blur=3 + 3 * lift, alpha=0.4)


_bcache = {}


def bench(t):
    cv = M["bench"].copy()
    rho = rho_at(t)
    nl, nt = letters_set(t), tacks_set(t)
    if t < T_SET:
        phi_now = float(np.clip(W1 * (t - T_DOWN) + 0.06 + 3 * max(0.0, t - T_UP), -1, PHI_END + 2))
        rings = tuple((float(np.clip((t - a) / (b - a), 0, 1)), (PHI_B - rho_at(a)) % TWO_PI) for a, b in RING_T)
        key = None
        disc = disc_img(phi_now, W1 * (t - T_DOWN), rings)
    else:
        key = (nl, nt, round(rho, 4))
        disc = None
    if key is None or _bcache.get("key") != key:
        if disc is None:
            dk = (nl, nt)
            if _bcache.get("dk") != dk:
                _bcache["dk"], _bcache["disc"] = dk, disc_img(letters=nl, tacks=nt)
            disc = _bcache["disc"]
        tex = D["wheel"].copy()
        tex.alpha_composite(disc, (WC - CT, WC - CT + int(round(ecc_at(t) * RT))))
        tex = tex.rotate(-math.degrees(rho), resample=Image.BICUBIC)
        ws = int(round(WC * KB))
        _bcache["key"], _bcache["tex"] = key, tex.resize((2 * ws, 2 * ws), Image.LANCZOS)
    tex = _bcache["tex"]
    cv.paste(tex, (DC[0] - tex.width // 2, DC[1] - tex.height // 2), tex)
    d = ImageDraw.Draw(cv, "RGBA")
    # the pin the disc turns on
    pin = D["pin"].resize((13, 13), Image.LANCZOS) if "pin_s" not in D else D["pin_s"]
    D["pin_s"] = pin
    cv.paste(pin, (DC[0] - 6, DC[1] - 6), pin)
    # the galley
    npk = letters_picked(t)
    for n, m in enumerate(ORDER):
        if n >= npk:
            L = D["letters"][m]
            x, y = M["tray"][m]
            cv.paste(L["bench"], (int(x - L["bench"].width / 2), int(y - L["bench"].height / 2)), L["bench"])
    draw_rule_tool(cv, t)
    st = stick_at(t)
    if st:
        tip, lift, carry = st
        if isinstance(carry, tuple):
            m, f = carry
            L = D["letters"][m]
            ang = ((L["rot"] + math.pi) % TWO_PI - math.pi) * f
            im = L["bench"].rotate(-math.degrees(ang), expand=True, resample=Image.BICUBIC)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lay.paste(im, (int(tip[0] - im.width / 2 - 2 * lift), int(tip[1] - im.height / 2 - 5 * lift)))
            drop(cv, lay, off=(3 + 6 * lift, 4 + 9 * lift), blur=2 + 2 * lift, alpha=0.4)
        elif carry == "tack":
            tk = D["tack"].resize((11, 11), Image.LANCZOS)
            cv.paste(tk, (int(tip[0] - 5 - 2 * lift), int(tip[1] - 5 - 5 * lift)), tk)
        draw_stick(cv, tip, lift)
    return ImageChops.multiply(cv, M["light"])


# ============================================================ the spin ===
SUB = 16                # samples per frame: the shutter is open for half of them
S = {}
K2 = [(0, -0.5), (0.9, -0.5), (2.0, -1.0), (3.5, -1.0), (4.5, -2.0), (5.9, -2.0), (7.5, 0.5), (20, 0.5)]     # turns per second, clockwise +
K3 = [(0, 0.5), (0.4, 0.5), (1.6, 2.0), (3.4, 2.0)]


def keyed(x, keys):
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if x <= b:
            return lerp(va, vb, smooth((x - a) / (b - a)))
    return keys[-1][1]


def run_flapper(th, om):
    """The reed on the post: every tack that passes knocks it; it is a spring and rings down. Returns (deflection, hits)."""
    dt = 1 / (FPS * SUB)
    n = np.floor((np.degrees(th + D["tack0"])) / 30)
    x = v = 0.0
    w0, z = TWO_PI * 9, 0.22
    out, hits = np.zeros(len(th)), []
    for i in range(len(th)):
        if i and n[i] != n[i - 1]:
            sgn = 1.0 if n[i] > n[i - 1] else -1.0
            v += sgn * (7 + 5 * min(1.5, abs(om[i])))
            hits.append((i * dt, abs(om[i])))
        v += (-w0 * w0 * x - 2 * z * w0 * v) * dt
        x = float(np.clip(x + v * dt, -0.55, 0.55))
        out[i] = x
    return out, hits


def build_spin():
    dt = 1 / (FPS * SUB)
    n2 = int((T3 - T2) * FPS * SUB) + 4 * SUB
    om2 = np.array([keyed(i * dt, K2) for i in range(n2)])
    S["om2"], S["th2"] = om2, np.cumsum(om2) * TWO_PI * dt
    n3 = int((SECONDS - T3) * FPS * SUB) + 4 * SUB
    pm = D["phi_mid"]

    def run3(th0):
        om3, th3 = np.zeros(n3), np.zeros(n3)
        th, om, mode, v, target = th0, 0.5, 0, 0.0, 0.0
        for i in range(n3):
            tau = i * dt
            if tau <= 3.4:
                om = keyed(tau, K3)
            elif mode == 0:                      # nobody drives it now: friction and the reed run it down
                om -= (0.16 + 0.42 * om) * dt
                if om <= 0.035:
                    mode, v = 1, om * TWO_PI
                    target = math.radians(30) * round(math.degrees(th + pm) / 30 + 0.2) - pm      # the reed between two tacks
                    S["stop3"] = tau
            if mode == 1:                        # the reed seats itself: the wheel rocks and settles
                w0, z = TWO_PI * 1.9, 0.3
                v += (-w0 * w0 * (th - target) - 2 * z * w0 * v) * dt
                om = v / TWO_PI
            th += om * TWO_PI * dt
            om3[i], th3[i] = om, th
        return om3, th3, target
    _, _, tg = run3(0.0)
    om3, th3, tg = run3((-pm - tg) % TWO_PI)          # start it so that it comes to rest with the middle T under the reed
    assert abs(((tg + pm + math.pi) % TWO_PI) - math.pi) < 1e-6
    S["om3"], S["th3"] = om3, th3
    S["fl2"], S["hit2"] = run_flapper(S["th2"], om2)
    S["fl3"], S["hit3"] = run_flapper(th3, om3)
    # the invariant: at 2 turns a second a tack moves exactly one tack-spacing per frame
    i0 = int(5.2 * FPS * SUB)
    step = math.degrees(S["th2"][i0 + SUB] - S["th2"][i0])
    assert abs(abs(step) - 30.0) < 1e-6, step


def spun(sprite, thetas):
    """The disc as the camera's open shutter sees it: the average of where it was."""
    if abs(thetas[-1] - thetas[0]) < math.radians(1.2):
        return sprite.rotate(-math.degrees(thetas[0]), resample=Image.BICUBIC)
    acc = None
    for th in thetas:
        a = np.asarray(sprite.rotate(-math.degrees(th), resample=Image.BICUBIC), np.float32)
        acc = a if acc is None else acc + a
    acc /= len(thetas)
    acc[..., 3] = np.asarray(sprite.getchannel("A"), np.float32)
    return Image.fromarray(acc.astype(np.uint8), "RGBA")


# ============================================================ river things ===

def paint_river(seed, bed_y, far=18):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = yy / H
    stops = [(0.0, (176, 212, 182)), (0.22, (92, 158, 140)), (0.55, (40, 104, 100)), (1.0, (14, 50, 56))]
    col = np.stack([np.interp(v, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)], -1).astype(np.float32)
    col *= (0.86 + 0.28 * vnoise((H, W), 300, 200, seed=seed, octaves=3))[..., None]
    rip = vnoise((H, W), 150, 7, seed=seed + 1, octaves=2) - 0.5
    col += (rip * 90 * np.clip(1 - v * 2.6, 0, 1) ** 1.5)[..., None]
    img = to_img(col).convert("RGB")
    rs = np.random.RandomState(seed + 2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, "RGBA")
    for k in range(4):                                      # far banks
        x0 = rs.uniform(-100, W - 200)
        pts = [(x0, bed_y + 30)] + [(x0 + q * 60, bed_y - rs.uniform(10, 60) * math.sin(math.pi * q / 8) - 6) for q in range(9)] + [(x0 + 480, bed_y + 30)]
        d.polygon(pts, fill=(24, 70, 70, 150))
    for k in range(far):
        x = rs.uniform(0, W)
        g = rs.uniform(-8, 8)
        d.polygon(blade_poly(x, bed_y + 14, rs.uniform(110, 290), rs.uniform(7, 15), rs.uniform(-0.25, 0.25), rs.uniform(-1, 1)), fill=(22 + int(g), 66 + int(g), 60 + int(g), 190))
    lay = premul_blur(lay, 3.2)
    img.paste(lay, (0, 0), lay)
    # the bed: silt and pebbles
    bed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bed, "RGBA")
    top = [(x, bed_y + 9 * math.sin(x / 83.0 + seed) + 5 * math.sin(x / 31.0)) for x in range(-10, W + 20, 10)]
    d.polygon(top + [(W + 10, H + 5), (-10, H + 5)], fill=(52, 70, 58, 255))
    for k in range(260):
        x, y = rs.uniform(0, W), rs.uniform(bed_y + 4, H + 8)
        f = (y - bed_y) / max(1, H - bed_y)
        rx = rs.uniform(5, 13) * (0.7 + 0.9 * f)
        ry = rx * rs.uniform(0.45, 0.7)
        g = rs.uniform(-14, 14)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(int(70 + g), int(86 + g), int(74 + g * 0.6), 255), outline=(26, 40, 38, 255))
        d.chord([x - rx + 1, y - ry + 1, x + rx - 1, y + ry * 0.4], 180, 360, fill=(int(112 + g), int(132 + g), int(110 + g), 255))
    ba = np.asarray(bed, np.float32).copy()
    ba[..., :3] *= np.clip(1.05 - 0.55 * np.clip((yy - bed_y) / max(1, H - bed_y), 0, 1), 0, 2)[..., None]
    bed = Image.fromarray(np.clip(ba, 0, 255).astype(np.uint8), "RGBA")
    img.paste(bed, (0, 0), bed)
    return img


def paint_shafts(seed):
    rs = np.random.RandomState(seed)
    out = []
    for q in range(2):
        m = Image.new("L", (W // 2, H // 2), 0)
        d = ImageDraw.Draw(m)
        for k in range(6):
            x = rs.uniform(-60, W // 2)
            wd = rs.uniform(14, 46)
            d.polygon([(x, -5), (x + wd, -5), (x + wd * 1.7 + 95, H // 2), (x + 95 - wd * 0.3, H // 2)], fill=int(rs.uniform(50, 110)))
        m = m.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)
        fade = Image.fromarray((np.clip(1.15 - np.mgrid[0:H, 0:W][0] / H * 1.1, 0, 1) * 255).astype(np.uint8))
        out.append(ImageChops.multiply(m, fade))
    return out


def plank(length, wd, seed, moss=0.5, base=(116, 86, 54)):
    """A length of sawn timber that has stood in the river: grain, a lit edge, algae creeping up from the foot."""
    length, wd = int(length), int(wd)
    g = vnoise((length, wd), 2.5, 120, seed=seed, octaves=2)
    g2 = vnoise((length, wd), 9, 30, seed=seed + 1)
    yy, xx = np.mgrid[0:length, 0:wd].astype(np.float32)
    u = xx / max(1, wd - 1)
    a = np.array(base, np.float32)[None, None] * (0.66 + 0.5 * g + 0.2 * g2)[..., None]
    a *= (1.22 - 0.55 * u)[..., None]                                     # light from the left
    al = np.clip((vnoise((length, wd), 26, 60, seed=seed + 2, octaves=2) - 0.78 + moss * (yy / length) ** 2 * 0.8) * 5, 0, 1)[..., None]
    a = a * (1 - al * 0.75) + np.array([58, 96, 52], np.float32) * (0.7 + 0.5 * g[..., None]) * al * 0.75
    img = to_img(a).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, wd - 1, length - 1], outline=(32, 22, 14, 255))
    d.line([(1, 1), (1, length - 2)], fill=(206, 176, 126, 255))
    return img


def iron(w, h, seed):
    w, h = int(w), int(h)
    a = np.array([78, 70, 66], np.float32)[None, None] * (0.7 + 0.6 * vnoise((h, w), 14, seed=seed, octaves=2))[..., None]
    r = np.clip((vnoise((h, w), 9, seed=seed + 1, octaves=2) - 0.45) * 4, 0, 1)[..., None]
    a = a * (1 - r * 0.7) + np.array([138, 80, 44], np.float32) * r * 0.7
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    a *= (1.25 - 0.6 * yy / h)[..., None]
    return to_img(a).convert("RGBA")


def bolt(d, cx, cy, r, rot=0.3):
    hexa = [(cx + r * math.cos(rot + q * math.pi / 3), cy + r * math.sin(rot + q * math.pi / 3)) for q in range(6)]
    d.polygon([(x + r * 0.2, y + r * 0.3) for x, y in hexa], fill=(10, 10, 10, 150))
    d.polygon(hexa, fill=(96, 76, 62, 255), outline=(24, 18, 14, 255))
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=(132, 100, 76, 255), outline=(30, 22, 16, 255))
    d.ellipse([cx - r * 0.4, cy - r * 0.5, cx, cy - r * 0.1], fill=(206, 180, 150, 255))


def build_stand(R, seed):
    """The A-frame the disc turns on: a post behind, two legs and an iron strap in front."""
    sw, sh = int(2.6 * R), int(3.7 * R)
    ox, oy = sw // 2, int(1.55 * R)
    post = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    p = plank(1.5 * R, 0.14 * R, seed, moss=0.1, base=(96, 72, 48))
    post.alpha_composite(p, (ox - p.width // 2, oy - int(1.38 * R)))
    ir = iron(0.2 * R, 0.13 * R, seed + 5)
    post.alpha_composite(ir, (ox - ir.width // 2, oy - int(1.27 * R)))
    d = ImageDraw.Draw(post, "RGBA")
    d.rectangle([ox - ir.width // 2, oy - int(1.27 * R), ox + ir.width // 2, oy - int(1.27 * R) + ir.height], outline=(20, 16, 12, 255))
    front = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    ang = math.degrees(math.atan2(0.62, 2.05))
    ln = math.hypot(0.62, 2.05) * R + 0.2 * R
    for sgn, sd in ((-1, 1), (1, 2)):
        p = plank(ln, 0.165 * R, seed + sd, moss=0.42)
        pr = p.rotate(sgn * ang, expand=True, resample=Image.BICUBIC)       # the left leg's foot goes left
        mx, my = ox + sgn * 0.31 * R, oy + (-0.1 + 2.05 / 2) * R
        front.alpha_composite(pr, (int(mx - pr.width / 2), int(my - pr.height / 2)))
    st = iron(0.86 * R, 0.13 * R, seed + 7)
    sy = oy + int(0.86 * R)
    front.alpha_composite(st, (ox - st.width // 2, sy))
    d = ImageDraw.Draw(front, "RGBA")
    d.rectangle([ox - st.width // 2, sy, ox + st.width // 2, sy + st.height], outline=(20, 14, 10, 255))
    for bx in (-0.3, 0.3):
        bolt(d, ox + bx * R, sy + st.height / 2, 0.042 * R, rot=bx)
    hr = 0.125 * R
    hp = iron(2 * hr, 2 * hr, seed + 9)
    m = Image.new("L", hp.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, hp.width - 1, hp.height - 1], fill=255)
    hp.putalpha(m)
    front.alpha_composite(hp, (int(ox - hr), int(oy - hr)))
    d = ImageDraw.Draw(front, "RGBA")
    d.ellipse([ox - hr, oy - hr, ox + hr, oy + hr], outline=(18, 12, 8, 255), width=2)
    bolt(d, ox, oy, 0.07 * R, rot=0.2)
    # what the stand and the light do to the face of the disc
    n = int(2 * R + 4)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    q = np.hypot(xx - n / 2, yy - n / 2) / R
    shade = np.clip(0.30 * ((xx - n / 2) * 0.5 + (yy - n / 2) * 0.85) / R + 0.12, 0, 0.5)
    legs = front.crop((ox - n // 2 - int(0.05 * R), oy - n // 2 - int(0.07 * R), ox - n // 2 - int(0.05 * R) + n, oy - n // 2 - int(0.07 * R) + n))
    ls = np.asarray(legs.getchannel("A").filter(ImageFilter.GaussianBlur(max(1.5, R * 0.03))), np.float32) / 255 * 0.5
    al = np.clip(shade + ls, 0, 0.8) * (q <= 1)
    sh_img = rgba(np.zeros((n, n, 3), np.float32) + np.array([4, 16, 18], np.float32), al)
    return dict(post=post, front=front, org=(ox, oy), shade=sh_img, R=R)


def underwater(im, haze=0.08, dark=1.0, blur=0.0):
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= np.array([0.86, 0.98, 0.95], np.float32)
    a[..., :3] = (a[..., :3] * (1 - haze) + MURK * haze) * dark
    return premul_blur(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), blur)


def put(cv, spr, cx, cy, rot=0.0, flip=False, width=None):
    if width:
        spr = spr.resize((int(width), max(2, int(width * spr.height / spr.width))), Image.LANCZOS)
    if flip:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        spr = spr.rotate(rot, expand=True, resample=Image.BICUBIC)
    cv.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)


def draw_disc(cv, key, cx, cy, thetas, fl, back=True):
    """Post, the turning disc, the light on its face, legs, hub and the reed that the tacks knock."""
    st, spr = A[key + "_stand"], A[key + "_disc"]
    R = st["R"]
    ox, oy = st["org"]
    cv.paste(st["post"], (int(cx - ox), int(cy - oy)), st["post"])
    im = spun(spr, thetas)
    cv.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)
    sh = st["shade"]
    cv.paste(sh, (int(cx - sh.width / 2), int(cy - sh.height / 2)), sh)
    cv.paste(st["front"], (int(cx - ox), int(cy - oy)), st["front"])
    d = ImageDraw.Draw(cv, "RGBA")
    pv = (cx, cy - 1.2 * R)
    ln = 0.25 * R
    ca, sa = math.cos(fl), math.sin(fl)

    def P(a, b):            # a down the reed, b across; the reed swings clockwise for fl > 0 (tip goes right)
        return (pv[0] + a * sa + b * ca, pv[1] + a * ca - b * sa)
    d.polygon([P(0, -0.034 * R), P(0, 0.034 * R), P(ln, 0.016 * R), P(ln, -0.016 * R)], fill=(222, 198, 136, 255), outline=(60, 44, 20, 255))
    d.line([P(0.02 * R, -0.012 * R), P(ln * 0.9, -0.004 * R)], fill=(250, 236, 190, 255), width=1)
    d.ellipse([pv[0] - 0.03 * R, pv[1] - 0.03 * R, pv[0] + 0.03 * R, pv[1] + 0.03 * R], fill=(190, 150, 70, 255), outline=(50, 34, 12, 255))


MOTES = []


def build_motes(n=84, seed=9):
    rs = np.random.RandomState(seed)
    for _ in range(n):
        MOTES.append((rs.uniform(0, TWO_PI), rs.uniform(0, 1), rs.uniform(0.8, 2.3), rs.uniform(0.35, 1.0), rs.uniform(0.6, 1.4), rs.uniform(0, 6.28)))


def draw_motes(cv, cx, cy, R, th, om, t, lo=0.5, hi=3.3, alpha=1.0, big=1.0, streak=0.16):
    """Silt in the water. It goes round with the disc, and inward when the spiral drains, outward when it pours."""
    d = ImageDraw.Draw(cv, "RGBA")
    span = math.log(hi / lo)
    for a0, l0, sz, al, gain, ph in MOTES:
        pts = []
        for dth in (0.0, -om * streak * gain):
            thx = th + dth
            f = (l0 + 0.022 * thx * gain) % 1.0
            r = lo * math.exp(span * f) * R
            a = a0 + 0.42 * thx * gain / (0.6 + r / R)
            pts.append((cx + r * math.sin(a) + 5 * math.sin(t * 0.6 + ph), cy - r * math.cos(a) * 0.92 + 4 * math.sin(t * 0.47 + ph * 2), f))
        f = pts[0][2]
        fade = min(1.0, f / 0.12, (1 - f) / 0.12)
        sz = sz * big
        c = (214, 236, 212, int(255 * al * alpha * fade))
        if math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]) > 2.0:
            d.line([pts[0][:2], pts[1][:2]], fill=c, width=max(1, int(sz)))
        else:
            x, y = pts[0][:2]
            d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=c)


def draw_blades(cv, blades, t, push=0.0, color=(8, 34, 34)):
    d = ImageDraw.Draw(cv, "RGBA")
    for x, y, ln, wd, lean, ph in blades:
        sway = 0.6 * math.sin(t * 0.9 + ph) + push
        g = int(10 * math.sin(ph * 3))
        d.polygon(blade_poly(x, y, ln, wd, lean + 0.05 * sway, sway), fill=(color[0] + g // 2, color[1] + g, color[2] + g, 255))


def bubble(d, x, y, r, a=1.0):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 244, 236, int(34 * a)), outline=(226, 248, 240, int(190 * a)))
    d.ellipse([x - r * 0.55, y - r * 0.6, x - r * 0.1, y - r * 0.15], fill=(255, 255, 255, int(200 * a)))


# ====================================================== part 2: Turkey looks out ===
PC = (548, 248)
RG = 196
R2 = 132


def build_port():
    a = steel_tex(W, H, 61, base=(62, 72, 78), rust=0.5)
    img = to_img(a)
    d = ImageDraw.Draw(img, "RGBA")
    for x in (118, 902):
        d.line([(x, 0), (x, H)], fill=(20, 24, 28, 200), width=3)
        d.line([(x + 3, 0), (x + 3, H)], fill=(120, 132, 138, 90), width=1)
        for y in range(24, H, 48):
            for xx_ in (x - 16, x + 18):
                d.ellipse([xx_ - 6, y - 5, xx_ + 7, y + 8], fill=(18, 22, 26, 160))
                d.ellipse([xx_ - 6, y - 6, xx_ + 6, y + 6], fill=(78, 88, 94, 255))
                d.ellipse([xx_ - 4, y - 5, xx_ + 2, y + 1], fill=(132, 144, 148, 255))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.asarray(img, np.float32)
    glow = np.exp(-(((xx - 540) / 430) ** 2 + ((yy + 60) / 270) ** 2))
    a = a * (0.6 + 0.62 * glow)[..., None] + np.array([120, 70, 20], np.float32) * (glow * 0.26)[..., None]
    rr = np.hypot(xx - PC[0], yy - PC[1])
    a *= np.clip(0.5 + (rr - RG - 50) / 150, 0.5, 1.0)[..., None]
    A["wall"] = to_img(a)
    ring = brass_ring(RG, RG + 56, 6, pad=74, seed=1, start=-90)
    d = ImageDraw.Draw(ring, "RGBA")
    R = ring.width // 2
    hx = R - RG - 56
    d.rounded_rectangle([hx - 46, R - 64, hx + 22, R + 64], radius=5, fill=(50, 50, 50, 255), outline=(16, 16, 16, 255), width=2)
    d.rectangle([hx - 18, R - 70, hx - 6, R + 70], fill=(84, 84, 82, 255), outline=(16, 16, 16, 255))
    d.line([(hx - 15, R - 66), (hx - 15, R + 66)], fill=(150, 150, 146, 255), width=2)
    for yy_ in (-46, 46):
        for xx_ in (-33, 10):
            d.ellipse([hx + xx_ - 5, R + yy_ - 5, hx + xx_ + 5, R + yy_ + 5], fill=(110, 110, 106, 255), outline=(14, 14, 14, 255))
    lx = R + RG + 56
    d.rounded_rectangle([lx - 20, R - 26, lx + 40, R + 26], radius=6, fill=(170, 132, 58, 255), outline=(60, 42, 16, 255), width=2)
    d.rounded_rectangle([lx - 46, R - 9, lx + 16, R + 9], radius=8, fill=(198, 158, 74, 255), outline=(60, 42, 16, 255), width=2)
    d.ellipse([lx + 12, R - 12, lx + 36, R + 12], fill=(210, 172, 86, 255), outline=(60, 42, 16, 255), width=2)
    d.line([(lx - 40, R - 4), (lx + 8, R - 4)], fill=(250, 226, 150, 200), width=2)
    A["ring"] = ring
    sh = Image.new("RGBA", ring.size, (0, 0, 0, 0))
    sh.putalpha(ring.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.6)))
    A["ring_shadow"] = sh
    g = np.zeros((H, W, 4), np.float32)
    g[..., 3] = np.clip((rr - (RG - 46)) / 46, 0, 1) ** 2 * 150
    g[..., :3] = (6, 20, 22)
    hi = np.exp(-((rr - (RG - 26)) / 9) ** 2) * np.clip(-(xx - PC[0]) - (yy - PC[1]) * 1.3, 0, None) / (RG * 1.4)
    A["glass"] = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA")
    A["glass_hi"] = to_img(np.clip(hi, 0, 1) * 255).convert("L")
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([PC[0] - RG - 2, PC[1] - RG - 2, PC[0] + RG + 2, PC[1] + RG + 2], fill=255)
    A["hole"] = m
    A["riv2"] = paint_river(70, PC[1] + RG - 52, far=22)
    A["shaft2"] = paint_shafts(71)
    A["p2_stand"] = build_stand(R2, 80)
    A["p2_stand"]["post"] = underwater(A["p2_stand"]["post"], 0.22, 0.9)
    A["p2_stand"]["front"] = underwater(A["p2_stand"]["front"], 0.06)
    fin = disc_img(letters=NPC, tacks=TACK_N, hub=True, halo=False)
    A["final"] = fin
    A["p2_disc"] = underwater(fin.resize((2 * R2 + 6, 2 * R2 + 6), Image.LANCZOS), 0.07)
    A["trout2"] = underwater(A["trout"].resize((158, int(158 * A["trout"].height / A["trout"].width)), Image.LANCZOS), 0.1)
    rs = np.random.RandomState(72)
    A["blades2"] = [(PC[0] + sx * rs.uniform(110, 205), PC[1] + RG + 10, rs.uniform(120, 250), rs.uniform(9, 17), -sx * rs.uniform(0.05, 0.3), rs.uniform(0, 6.28))
                    for sx in (-1, -1, -1, 1, 1, 1, 1)]
    n = int((T3 - T2) * FPS) + 3
    om = S["om2"][::SUB][:n]
    pull = np.array([ease(i / FPS, 0.9, 6.2) * (1 - 0.45 * ease(i / FPS, 7.3, 9.2)) for i in range(n)])
    S["pull2"] = Spring(0.7, 0.8).run(pull)
    S["wattle2"] = Spring(1.6, 0.2).run(-om * 7.0, 0.0)


def port_frame(t, k):
    tau = t - T2
    i = max(0, k - int(round(T2 * FPS)))
    j = i * SUB
    ths, om, fl = S["th2"][j:j + SUB // 2], S["om2"][j], S["fl2"][j]
    par = (7 * math.sin(0.5 * tau), 4 * math.sin(0.37 * tau + 1))
    cx, cy = PC[0] - 36 + par[0], PC[1] - 16 + par[1]
    rv = ImageChops.offset(A["riv2"], int(par[0] * 0.4), 0)
    sh = Image.blend(A["shaft2"][0], A["shaft2"][1], 0.5 + 0.5 * math.sin(tau * 0.8))
    rv = add_light(rv, sh, (210, 240, 200), 0.75)
    draw_motes(rv, cx, cy, R2, ths[0], om, t, alpha=1.0, big=1.5, streak=0.3)      # the silt must be seen to go down the drain
    draw_disc(rv, "p2", cx, cy, ths, fl)
    # the trout: nose toward the hub, coming closer, its head going round a little with the thing
    p = S["pull2"][min(i, len(S["pull2"]) - 1)]
    slow = 1 - min(1.0, abs(om) / 1.6)
    nod = (5 * math.sin(ths[0]) * (0.4 + 0.6 * slow), -5 * math.cos(ths[0]) * (0.4 + 0.6 * slow))
    tw = A["trout2"].width
    tx = PC[0] + 112 - 84 * p + tw / 2 + nod[0]
    ty = cy - 58 + 30 * p + nod[1]
    tr = flex(A["trout2"], t * (2.2 + 2.0 * (1 - p)), 5 - 2 * p)
    put(rv, tr, tx, ty, rot=10 + 6 * p + 2 * math.sin(tau * 0.7))
    d = ImageDraw.Draw(rv, "RGBA")
    for q in range(9):                                      # its breath, taken by the turning water
        age = (tau * 0.5 + q * 0.37) % 1.6
        bx, by = tx - tw / 2 - 6 - 26 * age * (0.4 + p), ty - 4 - 48 * age + 8 * math.sin(q + age * 5)
        bubble(d, bx, by, 2 + (q % 3), a=1 - age / 1.6)
    draw_blades(rv, A["blades2"], t, push=-0.5 * om)
    cv = A["wall"].copy()
    cv.paste(rv, (0, 0), A["hole"])
    tk = turkey_img(S["wattle2"][min(i, len(S["wattle2"]) - 1)], 250).transpose(Image.FLIP_LEFT_RIGHT)
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    refl.alpha_composite(tk, (PC[0] - 190, PC[1] + 26))
    refl.putalpha(ImageChops.multiply(refl.getchannel("A"), A["hole"]).point(lambda v: int(v * 0.2)))
    refl = refl.filter(ImageFilter.GaussianBlur(1.3))
    cv.paste(refl, (0, 0), refl)
    cv.paste(A["glass"], (0, 0), A["glass"])
    cv = add_light(cv, A["glass_hi"], (230, 250, 240), 0.55)
    ring = A["ring"]
    pos = (PC[0] - ring.width // 2, PC[1] - ring.height // 2)
    cv.paste(A["ring_shadow"], (pos[0] + 8, pos[1] + 12), A["ring_shadow"])
    cv.paste(ring, pos, ring)
    # Turkey himself, close to the lens, dark against the glass; he leans as the thing draws him
    lean = S["pull2"][min(i, len(S["pull2"]) - 1)]
    tk = turkey_img(S["wattle2"][min(i, len(S["wattle2"]) - 1)] * 1.2, 470).transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(tk, np.float32).copy()
    a[..., :3] = a[..., :3] * 0.27 + np.array([20, 13, 9], np.float32) * 0.5
    edge = np.asarray(tk.getchannel("A").filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    a[..., :3] += (1 - edge)[..., None] * np.array([120, 150, 120], np.float32) * 0.8
    tk = premul_blur(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), 0.7)
    cv.paste(tk, (int(-66 + 26 * lean + 3 * math.sin(ths[0]) * slow), int(150 + 3 * math.cos(ths[0]) * slow)), tk)
    return cv


# ===================================================== part 3: the trout look in ===
DC3 = (336, 224)
R3 = 146
TIN3 = (752, 378, 0.40)
LAUNDRY_TACK = 3


def build_riverside():
    A["riv3"] = paint_river(90, 446, far=26)
    A["shaft3"] = paint_shafts(91)
    A["p3_stand"] = build_stand(R3, 84)
    A["p3_stand"]["post"] = underwater(A["p3_stand"]["post"], 0.2, 0.9)
    A["p3_stand"]["front"] = underwater(A["p3_stand"]["front"], 0.05)
    A["p3_disc"] = underwater(A["final"].resize((2 * R3 + 6, 2 * R3 + 6), Image.LANCZOS), 0.05)
    tr = A["trout"]
    A["troutA"] = underwater(tr.resize((292, int(292 * tr.height / tr.width)), Image.LANCZOS), 0.03)
    A["troutB"] = underwater(tr.resize((236, int(236 * tr.height / tr.width)), Image.LANCZOS), 0.06)
    A["troutC"] = underwater(tr.resize((150, int(150 * tr.height / tr.width)), Image.LANCZOS), 0.5, 0.95, blur=1.2)
    rs = np.random.RandomState(92)
    A["blades3"] = [(x, H + 16, rs.uniform(170, 400), rs.uniform(13, 26), ln, rs.uniform(0, 6.28))
                    for x, ln in ((-8, 0.16), (26, 0.3), (58, 0.08), (906, -0.2), (936, -0.07), (962, -0.3), (884, -0.4))]
    n = int((SECONDS - T3) * FPS) + 3
    om = S["om3"][::SUB][:n]
    S["wattle3"] = Spring(1.6, 0.2).run(om * 6.0, 0.0)
    S["fling3"] = np.clip(Spring(1.1, 0.55).run(np.clip(np.abs(om) / 1.1, 0, 1)), 0, 1)
    S["crane3"] = Spring(1.0, 0.7).run(np.array([ease(i / FPS, 3.6, 7.6) for i in range(n)]))
    S["froth"] = [(rs.uniform(0.3, 5.6), rs.uniform(0, TWO_PI), rs.uniform(2.0, 7.5), rs.uniform(0.6, 1.3), rs.uniform(0, 6.28)) for _ in range(260)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    A["vig3"] = to_img((np.clip(1.06 - 0.5 * (np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) ** 2.4), 0.3, 1)[..., None] * np.ones((1, 1, 3), np.float32)) * 255)
    g = np.exp(-(((xx - (TIN3[0] - 66)) / 70) ** 2 + ((yy - TIN3[1]) / 60) ** 2))
    A["tin_glow"] = to_img(g * 255).convert("L")


def river_frame(t, k):
    tau = t - T3
    i = max(0, k - int(round(T3 * FPS)))
    j = i * SUB
    ths, om, fl = S["th3"][j:j + SUB // 2], S["om3"][j], S["fl3"][j]
    th = ths[0]
    cx, cy = DC3
    cv = A["riv3"].copy()
    sh = Image.blend(A["shaft3"][0], A["shaft3"][1], 0.5 + 0.5 * math.sin(tau * 0.7 + 1))
    cv = add_light(cv, sh, (214, 242, 204), 0.8)
    # a far trout goes by behind the wheel
    put(cv, flex(A["troutC"], t * 4, 4), 860 - 44 * tau, 92 + 6 * math.sin(tau * 0.8), rot=3)
    draw_motes(cv, cx, cy, R3, th, om, t, alpha=0.6)
    # the tin, Turkey at his porthole
    sx, sy, sc = TIN3
    wi = min(i, len(S["wattle3"]) - 1)
    tin = tin_sprite(t, turkey_duck=2 * math.sin(tau * 0.9), wattle=S["wattle3"][wi])
    tin = tin.resize((int(tin.width * sc), int(tin.height * sc)), Image.LANCZOS)
    tin = underwater(tin, 0.03)
    cv.paste(tin, (int(sx - tin.width / 2), int(sy - tin.height / 2 + 2 * math.sin(tau * 0.6))), tin)
    cv = add_light(cv, A["tin_glow"], (255, 176, 80), 0.22)
    draw_disc(cv, "p3", cx, cy, ths, fl)
    d = ImageDraw.Draw(cv, "RGBA")
    # something caught on a tack goes round with it: weed, or a sock
    wi2 = min(i, len(S["fling3"]) - 1)
    spd, sgn = S["fling3"][wi2], (1.0 if om >= 0 else -1.0)
    a_t = D["tack0"] + math.radians(30 * LAUNDRY_TACK) + th
    ax, ay = cx + TACK_R * R3 * math.sin(a_t), cy - TACK_R * R3 * math.cos(a_t)
    pts = []
    for n_ in range(25):
        s_ = n_ / 24 * 0.95 * R3
        a = a_t - sgn * s_ / (1.02 * R3)                      # flung: it trails round the rim, a little outside it
        r = (TACK_R + 0.09 * (s_ / R3) ** 0.7) * R3
        fx, fy = cx + r * math.sin(a), cy - r * math.cos(a)
        hx_, hy_ = ax + 7 * math.sin(t * 1.3 + n_ * 0.3) * (n_ / 24), ay + s_ * 0.82     # limp: it hangs from the tack
        pts.append((lerp(hx_, fx, spd), lerp(hy_, fy, spd) + 3 * math.sin(t * 9 + n_ * 0.9) * spd * (n_ / 24)))
    for q in range(len(pts) - 1):
        wd = 13 - 5 * q / 24
        d.line([pts[q], pts[q + 1]], fill=(30, 58, 30, 255), width=int(wd + 3))
    for q in range(len(pts) - 1):
        wd = 13 - 5 * q / 24
        d.line([pts[q], pts[q + 1]], fill=(74, 112, 56, 255) if (q // 3) % 2 else (168, 182, 128, 255), width=int(wd))     # banded: weed, or a striped sock
    d.line(pts[1:-2], fill=(170, 196, 112, 255), width=1)
    # froth thrown off the rim while it is fast
    for b0, a0, rad, gain, ph in S["froth"]:
        age = tau - b0
        if age < 0 or age > 3.0:
            continue
        ob = S["om3"][int(b0 * FPS * SUB)]
        if ob < 1.0:
            continue
        v = ob * TWO_PI * R3 * 0.45 * gain
        tx_, ty_ = math.cos(a0), math.sin(a0)                 # tangent at the place it left
        fly = (1 - math.exp(-2.6 * age)) / 2.6
        x = cx + R3 * math.sin(a0) + tx_ * v * fly + 6 * math.sin(age * 4 + ph)
        y = cy - R3 * math.cos(a0) + ty_ * v * fly - (16 * age + 14 * age * age) * gain
        bubble(d, x, y, rad * (0.6 + 0.4 * min(1, age * 3)), a=min(1, (3.0 - age) / 1.0))
    # the two who came to see
    cr = S["crane3"][min(i, len(S["crane3"]) - 1)]
    slow = 1 - min(1.0, abs(om) / 1.6)
    nod = (6 * math.sin(th) * (0.35 + 0.65 * slow), -6 * math.cos(th) * (0.35 + 0.65 * slow))
    put(cv, flex(A["troutB"], t * 3.1 + 1, 5), 588 - 26 * cr + nod[0], 214 + 8 * cr + nod[1] + 3 * math.sin(tau * 0.9), rot=5 + 3 * cr)
    put(cv, flex(A["troutA"], t * 2.6, 6), 138 + 24 * cr + nod[0], 396 - 12 * cr + nod[1] + 3 * math.sin(tau * 0.8 + 2), rot=17 + 5 * cr, flip=True)
    draw_blades(cv, A["blades3"], t, push=0.35 * om, color=(6, 30, 30))
    return ImageChops.multiply(cv, A["vig3"])


# One reading at a time, each over the action that argues for it: fast and draining / slow and legible;
# spun up and clicking / running down with the froth and the thing on the tack.
CAPTIONS = [(T2 + 1.7, T2 + 5.5, "A turbine, drinking the river down a whirlpool?"),
            (T2 + 6.0, T3 - 0.3, "Or a trap that hypnotises, and I am staring?"),
            (T3 + 0.9, T3 + 4.5, "The pie-prize wheel from the diner: who wins the slice?"),
            (T3 + 5.0, SECONDS - 0.4, "Or a washing machine, and whose sock?")]
assert all(b - a >= 2.5 for a, b, _ in CAPTIONS) and all(CAPTIONS[q][1] < CAPTIONS[q + 1][0] for q in range(3))


def picture(t, ink):
    k = ink.i
    if t < T2:
        img = bench(t)
    elif t < T3:
        img = port_frame(t, k)
    else:
        img = river_frame(t, k)
    ink.img = img.convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink._grain = False
    for a, b, s in CAPTIONS:
        if a <= t <= b:
            ink.caption(s, alpha=min(ramp(t, a, a + 0.35), 1 - ramp(t, b - 0.35, b)), size=27)


def build():
    build_disc()
    build_wheel()
    build_making()
    build_bench()
    build_trout()
    build_turkey()
    build_tin()
    build_spin()
    build_motes()
    build_port()
    build_riverside()


NOTE = {"N": 392.0, "O": 523.25, "W": 587.33, "T": 659.25, "R": 440.0, "A": 349.23, "P": 293.66, "L": 783.99, "·": 196.0}


def ratchet_clicks():
    """Single clicks cut from the foraged ratchet recording (CC0), if it is there."""
    f = next((SRC / n for n in ("ratchet.ogg", "ratchet.mp3") if (SRC / n).exists()), None)
    if f is None:
        return []
    from kit_anim import load_audio
    a = load_audio(f)
    env = np.convolve(np.abs(a), np.ones(200) / 200, "same")
    thr = env.max() * 0.35
    out, k = [], 0
    while k < len(a) - 4000 and len(out) < 24:
        if env[k] > thr:
            st = max(0, k - 150)
            c = a[st:st + 2600].copy()
            c *= np.exp(-np.arange(len(c)) / 900.0)
            out.append(c / (np.abs(c).max() + 1e-9))
            k += 3200
        else:
            k += 20
    return out


def sound(mix):
    rs = np.random.RandomState(7)
    mix.room(0, T2 + 0.2, gain=0.02)
    # the wheel: a bearing hum that follows its speed
    ts = np.arange(0, T2, 0.005)
    w = np.abs(np.gradient(np.array([rho_at(x) for x in ts]), 0.005))
    w = np.convolve(np.clip(w, 0, 12), np.ones(20) / 20, "same")
    n = int(T2 * RATE)
    wa = np.interp(np.arange(n) / RATE, ts, w)
    ph = np.cumsum(TWO_PI * (34 + 7.5 * wa)) / RATE
    amp = np.clip(wa / 4, 0, 1.6)
    mix.add((np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3.01 * ph)) * amp, 0, 0.05)
    mix.add(mix.lowpass(rs.normal(0, 1, n), 300) * amp, 0, 0.22)
    # the brush: a long wet stroke, thinning as it runs dry
    nb = int((T_UP - T_DOWN) * RATE)
    tb = np.arange(nb) / RATE
    br = mix.band(rs.normal(0, 1, nb), 900, 5200) * (0.7 + 0.3 * np.sin(TWO_PI * 3.1 * tb) * np.sin(TWO_PI * 0.7 * tb))
    br *= np.minimum(1, np.minimum(tb / 0.12, (tb[-1] - tb) / 0.25)) * (1 - 0.35 * tb / tb[-1])
    mix.add(br, T_DOWN, 0.085, pan=0.2)
    mix.thud(T_DOWN, freq=150, gain=0.12, seconds=0.12)
    for a_, b_ in RING_T:                                   # the ruling pen: a thin scratch, once round
        nr = int((b_ - a_) * RATE)
        tr = np.arange(nr) / RATE
        sc = mix.band(rs.normal(0, 1, nr), 3200, 9000) * np.minimum(1, np.minimum(tr / 0.04, (tr[-1] - tr) / 0.06)) * (0.75 + 0.25 * np.sin(TWO_PI * 11 * tr))
        mix.add(sc, a_, 0.05, pan=0.1)
        mix.click(a_ - 0.12, gain=0.14, bright=2600, seconds=0.04)          # the disc is re-pinned
    for at in (0.02, 3.86, 4.16, 7.02):
        mix.whoosh(at, 0.36, gain=0.03, pan=0.5)
    # the letters: each kind of letter has its note, so the pairs sound twice and the tune closes on itself
    for n_, m in enumerate(ORDER):
        ch = PIECES[m]
        a_, d_ = M["set_a"][n_], M["set_d"][n_]
        pan = float(np.clip((D["letters"][m]["slot"][0] - DC[0]) / 300, -0.8, 0.8))
        mix.click(a_ + 0.36 * d_, gain=0.05, bright=6500, seconds=0.015, pan=0.6)
        mix.click(a_ + 0.8 * d_, gain=0.2, bright=2600, seconds=0.03, pan=pan)
        mix.pluck(a_ + 0.8 * d_, NOTE[ch], seconds=0.7, gain=0.2, pan=pan)
    for k in range(TACK_N):
        at = T_TACK + (k + 0.57) * TACK_DT
        t_ = mix.t(0.09)
        f = 2900 + 60 * k
        mix.add(np.sin(TWO_PI * f * t_) * np.exp(-t_ * 70) + 0.5 * np.sin(TWO_PI * f * 1.52 * t_) * np.exp(-t_ * 90), at, 0.09, pan=0.3)
        mix.thud(at, freq=170, gain=0.16, seconds=0.1, pan=0.3)
    mix.whoosh(T_FLICK + 0.05, 0.3, gain=0.09, pan=0.3)
    clicks = ratchet_clicks()

    def rotor(at, om, th, gain, lp):
        n_ = int(len(om) / (FPS * SUB) * RATE)
        x = np.arange(n_) / RATE * (FPS * SUB)
        o = np.interp(x, np.arange(len(om)), om)
        thx = np.interp(x, np.arange(len(th)), th)
        ph_ = np.cumsum(TWO_PI * (44 + 50 * np.abs(o))) / RATE
        sig = (np.sin(ph_) + 0.4 * np.sin(2 * ph_) + 0.2 * np.sin(3 * ph_)) * np.clip(np.abs(o) / 2, 0, 1) ** 0.8 * (1 + 0.28 * np.sin(thx))
        sw = mix.band(rs.normal(0, 1, n_), 200, lp) * np.clip(np.abs(o) / 2, 0, 1) ** 1.5 * (0.6 + 0.4 * np.sin(thx * 3))
        mix.add(sig, at, gain)
        mix.add(sw, at, gain * 0.9)

    def tick(at, speed, gain, bright, k):
        if clicks:
            c = clicks[k % len(clicks)]
            if bright < 2000:
                c = mix.lowpass(c, bright)
            mix.add(c, at, gain * 1.6, pan=-0.25)
        else:
            mix.click(at, gain=gain, bright=bright, seconds=0.025, pan=-0.25)
            t_ = mix.t(0.05)
            mix.add(np.sin(TWO_PI * 900 * t_) * np.exp(-t_ * 90), at, gain * 0.5, pan=-0.25)

    # inside the tin: everything muffled by the plate
    dur2 = T3 - T2
    mix.drone(T2, dur2 + 0.3, freqs=(49, 73.5, 98), gain=0.05, attack=0.6, release=0.5)
    x = mix.lowpass(mix.noise(dur2 + 0.3, "brown"), 380) * (0.6 + 0.4 * np.sin(TWO_PI * 0.13 * mix.t(dur2 + 0.3)))
    mix.add(x * mix.env(len(x), 0.5, 0.01, 1.0, 0.4), T2, 0.15)
    n2 = int(dur2 * FPS * SUB)
    rotor(T2, S["om2"][:n2], S["th2"][:n2], 0.085, 900)
    for k, (ht, sp) in enumerate(S["hit2"]):
        if ht < dur2:
            tick(T2 + ht, sp, 0.05 / (1 + 1.2 * sp), 1500, k)
    # out in the river
    dur3 = SECONDS - T3
    mix.water(T3, dur3, gain=0.035)
    x = mix.lowpass(mix.noise(dur3, "brown"), 700) * (0.6 + 0.4 * np.sin(TWO_PI * 0.11 * mix.t(dur3)))
    mix.add(x * mix.env(len(x), 0.3, 0.01, 1.0, 0.6), T3, 0.11)
    n3 = int(dur3 * FPS * SUB)
    rotor(T3, S["om3"][:n3], S["th3"][:n3], 0.08, 2600)
    for k, (ht, sp) in enumerate(S["hit3"]):
        if ht < dur3:
            tick(T3 + ht, sp, 0.2 / (1 + 1.0 * sp), 6000, k)
    for b0, a0, rad, gain, ph_ in S["froth"]:
        if S["om3"][int(b0 * FPS * SUB)] >= 1.0:
            t_ = mix.t(0.08)
            f0 = 500 + 2200 / rad
            mix.add(np.sin(TWO_PI * (f0 + 5000 * t_) * t_) * np.exp(-t_ * 40), T3 + b0, 0.02 * gain, pan=rs.uniform(-0.7, 0.5))
    stop = T3 + S["stop3"] + 0.75
    mix.bell(stop, freq=1568, seconds=2.2, gain=0.12, pan=-0.2)      # a diner's counter bell, or the end of the cycle
    mix.reverb(0.16, 1.0)


def main():
    film = Film(SLUG, SECONDS, boil=0, wobble=0)
    build()
    film.picture(picture)
    film.sound(sound)
    film.poster_at = T2 + 8.75
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        times = [float(x) for x in sys.argv[2:]]
        contact(SLUG, cols=3, scale=0.5, times=times or None)


if __name__ == "__main__":
    main()
