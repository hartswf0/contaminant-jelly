"""p03 · Room 4 chalkboard listing HOOK MONSTER.

Hand film for porthole #03 (Starbd). Lineage: a classroom chalkboard, so the film is a chalkboard:
a slate slab framed in wood on the bench, lettered one chalk stroke at a time, then stood on the
riverbed and washed. The rule is a lipogram shown as washed chalk: a cloth takes letters out and
what is left has to be read again (HOOK MONSTER -> HOOK M  STER -> OK M  STER).

SCION methods really used:
  32 Forward Kinematics   - every trout, Turkey and the tin are joint trees of cut-paper pieces
                            (assert: hinge points stay fixed in the parent frame).
  41 Secondary Dynamics   - satchels, Turkey's wattle, the cloth and the tin's hook are damped
                            pendulums driven by their parent's acceleration (assert: energy decays).
  44 Multiplane Parallax  - the river is six paper planes with their own parallax ratio, haze and
                            focus (assert: nearer planes move more).

Run:  python3 films/p03.py            (render)
      python3 films/p03.py --stills 2 6 10 ...
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import Film, W, H, FPS, RATE, PAGE, INK, clamp, ramp, smooth, ease, lerp, font  # noqa: E402
import kit_anim as KA  # noqa: E402

SLUG = "p03"
SECONDS = 34.0
T_RIVER = 15.5     # cut: bench -> through the porthole
T_TROUT = 24.6     # cut: the river side
NF = int(SECONDS * FPS) + 2
SRC = Path(__file__).resolve().parent / "sources" / SLUG

# ------------------------------------------------------------------ noise ---


def vnoise(shape, sx, sy=None, seed=0, octaves=1):
    """Value noise in -1..1 (random lattice, bicubic), sx/sy = feature size in px."""
    sy = sx if sy is None else sy
    h, w = shape
    rs = np.random.RandomState(seed)
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        fx, fy = max(1.0, sx / 2 ** o), max(1.0, sy / 2 ** o)
        g = rs.rand(int(h / fy) + 3, int(w / fx) + 3).astype(np.float32)
        im = Image.fromarray(g, "F").resize((w, h), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32) - 0.5) * 2
        tot += amp
        amp *= 0.5
    return out / tot


def blur_arr(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / 255


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def shadow_of(alpha_img, blur, strength):
    """Black RGBA whose alpha is the blurred alpha of a sprite."""
    a = alpha_img.filter(ImageFilter.GaussianBlur(float(blur))).point(lambda v: int(v * float(strength)))
    sh = Image.new("RGBA", alpha_img.size, (8, 10, 12, 0))
    sh.putalpha(a)
    return sh


def catmull(pts, per=10, closed=False):
    pts = [np.array(p, np.float32) for p in pts]
    if len(pts) == 2:
        return [tuple(pts[0] + (pts[1] - pts[0]) * k / per) for k in range(per + 1)]
    if closed:
        P = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            u = k / per
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)))
    out.append(tuple(P[-2]))
    return out


def resample(pts, step):
    """Polyline -> points every `step` px, with cumulative length."""
    p = np.array(pts, np.float32)
    seg = np.hypot(*(p[1:] - p[:-1]).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = float(cum[-1])
    n = max(2, int(L / step) + 1)
    s = np.linspace(0, L, n)
    return np.stack([np.interp(s, cum, p[:, 0]), np.interp(s, cum, p[:, 1])], 1), L


# ===================================================================== BENCH
# World for part 1 is the bench seen from straight above at 2x (1920x1080).
WW, WH = 1920, 1080
BX, BY, BW, BH = 210, 110, 1500, 860         # board outer
RW = 64                                        # rail width
SX, SY, SW, SH = BX + RW, BY + RW, BW - 2 * RW, BH - 2 * RW   # slate that shows
CHALK = np.array([240, 238, 228], np.float32)


def make_table():
    """Bench of dark planks under one lamp."""
    h, w = WH, WW
    grain = vnoise((h, w), 420, 5, 1, 3)
    rings = np.sin((vnoise((h, w), 900, 40, 2, 2) * 9 + np.linspace(0, 40, h)[:, None]) * 2.2)
    base = np.array([96, 72, 50], np.float32)
    a = base[None, None, :] * (1 + 0.10 * grain[..., None] + 0.05 * rings[..., None])
    # plank seams
    for y in (118, 372, 640, 905):
        a[y - 2:y + 2] *= 0.55
        a[y + 2:y + 4] *= 1.12
        k = (y * 7) % 5
        a[:, :, :] *= 1.0
        a[y - 60:y, :, :] *= (1 + 0.02 * (k - 2))
    # old chalk dust and knocks
    dust = np.clip(vnoise((h, w), 260, None, 3, 3) - 0.25, 0, 1)
    a += dust[..., None] * 34
    rs = np.random.RandomState(5)
    for _ in range(260):
        x, y = rs.randint(0, w), rs.randint(0, h)
        a[y:y + rs.randint(1, 3), x:x + rs.randint(1, 4)] += rs.uniform(10, 50)
    # lamp pool from upper left
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pool = 1.12 - 0.42 * np.clip(np.hypot((xx - 820) / 1500, (yy - 430) / 1000), 0, 1.4) ** 1.6
    return a * pool[..., None]


def make_slate():
    """The slab: split slate, dusty, with the haze of old wipes. Returns float RGB (SH+40, SW+40)."""
    h, w = SH + 40, SW + 40
    base = np.array([42, 54, 51], np.float32)
    mott = vnoise((h, w), 240, 150, 11, 4)
    cleave = vnoise((h, w), 700, 14, 12, 1)            # the slab's long cleavage figure
    tooth = vnoise((h, w), 2.2, None, 13, 2)
    a = base[None, None, :] * (1 + 0.16 * mott[..., None] + 0.07 * cleave[..., None] + 0.07 * tooth[..., None])
    # old wipes: broad pale arcs of dried chalk water
    haze = np.clip(vnoise((h, w), 520, 70, 14, 3) * 0.9 + 0.15, 0, 1) * np.clip(vnoise((h, w), 300, None, 15, 2) + 0.55, 0, 1)
    streak = vnoise((h, w), 900, 9, 16, 1) * 0.5 + 0.5
    dusty = haze * (0.55 + 0.45 * streak)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.clip(1 - np.minimum(np.minimum(xx, w - xx), np.minimum(yy, h - yy)) / 110, 0, 1) ** 2   # dust lodges by the frame
    # sweeps of the felt rubber: broad curved bands of pushed dust
    sw = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sw)
    rq = random.Random(19)
    for _ in range(22):
        x, y = rq.uniform(-100, w), rq.uniform(0, h)
        ln, bend, ang = rq.uniform(260, 620), rq.uniform(-120, 120), rq.gauss(0.0, 0.35)
        pts = [(x + math.cos(ang) * ln * k / 8 - math.sin(ang) * bend * math.sin(math.pi * k / 8), y + math.sin(ang) * ln * k / 8 + math.cos(ang) * bend * math.sin(math.pi * k / 8)) for k in range(9)]
        sd.line(pts, fill=rq.randint(50, 120), width=rq.randint(70, 120), joint="curve")
    sweeps = blur_arr(np.asarray(sw, np.float32) / 255, 9) * (0.6 + 0.4 * vnoise((h, w), 500, 8, 18, 1))
    dusty = np.clip(dusty * 0.8 + edge * 0.6 + sweeps * 0.85, 0, 1) * (0.75 + 0.25 * (tooth > -0.2))
    a += dusty[..., None] * np.array([52, 54, 50], np.float32)
    # scratches and pits
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    rs = random.Random(17)
    for _ in range(46):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        ang = rs.gauss(0.1, 0.5)
        ln = rs.uniform(30, 220)
        d.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=rs.randint(30, 90), width=1)
    for _ in range(500):
        x, y = rs.uniform(0, w), rs.uniform(0, h)
        d.point((x, y), fill=rs.randint(40, 130))
    a += (np.asarray(im, np.float32) / 255)[..., None] * 60
    return a


def make_wood(length, width, seed, base=(168, 122, 74)):
    """One planed rail, grain along its length. float RGB (width, length)."""
    h, w = width, length
    fig = vnoise((h, w), 600, 26, seed, 2)
    rings = np.sin((fig * 6 + np.linspace(0, 5.5, h)[:, None]) * 3.1 + seed)
    fine = vnoise((h, w), 90, 1.6, seed + 1, 2)
    pores = (vnoise((h, w), 26, 1.2, seed + 2) > 0.62).astype(np.float32)
    a = np.array(base, np.float32)[None, None, :] * (1 + 0.11 * rings[..., None] + 0.10 * fine[..., None] - 0.12 * pores[..., None])
    a[..., 2] *= 1 - 0.06 * rings
    # planed bevels: lit outer arris, dark inner rebate against the slate
    prof = np.ones(h, np.float32)
    prof[:5] = np.linspace(1.28, 1.05, 5)
    prof[-9:] = np.linspace(0.96, 0.5, 9)
    prof[5:12] *= 1.04
    a *= prof[:, None, None]
    # handling: dull scuffs and chalky finger marks
    scuff = np.clip(vnoise((h, w), 130, 22, seed + 3, 2) - 0.35, 0, 1)
    a += scuff[..., None] * 38
    return a


def rail_sprite(which):
    """Mitred rail as RGBA at world scale, with its board offset. which: top/bottom/left/right."""
    if which in ("top", "bottom"):
        a = make_wood(BW, RW, {"top": 21, "bottom": 22}[which])
        m = Image.new("L", (BW, RW), 0)
        ImageDraw.Draw(m).polygon([(0, 0), (BW, 0), (BW - RW, RW), (RW, RW)], fill=255)
        im = to_img(a)
        if which == "bottom":
            a2 = make_wood(BW, RW, 22)
            # chalk dust settles on the lower rail
            a2 += np.clip(vnoise((RW, BW), 160, 12, 31, 2) + 0.1, 0, 1)[..., None] * 30
            im = to_img(a2).transpose(Image.FLIP_TOP_BOTTOM)
            m = m.transpose(Image.FLIP_TOP_BOTTOM)
        im.putalpha(m)
        return im, (0, 0 if which == "top" else BH - RW)
    a = make_wood(BH, RW, {"left": 23, "right": 24}[which])
    im = to_img(a)
    m = Image.new("L", (BH, RW), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (BH, 0), (BH - RW, RW), (RW, RW)], fill=255)
    im.putalpha(m)
    im = im.transpose(Image.ROTATE_90) if which == "left" else im.transpose(Image.ROTATE_270)
    return im, (0 if which == "left" else BW - RW, 0)


def make_plate():
    """ROOM 4: a stamped brass plate with two screws."""
    w, h = 190, 44
    S = 3
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], 7 * S, fill=(186, 150, 74, 255), outline=(92, 66, 26, 255), width=2 * S)
    d.rounded_rectangle([4 * S, 4 * S, w * S - 4 * S, h * S - 4 * S], 4 * S, outline=(222, 194, 122, 255), width=S)
    f = font("serif", 30 * S)
    d.text((w * S / 2 + S, h * S / 2 + S), "ROOM 4", font=f, fill=(238, 214, 150, 255), anchor="mm")
    d.text((w * S / 2, h * S / 2), "ROOM 4", font=f, fill=(70, 48, 20, 255), anchor="mm")
    for x in (13, w - 13):
        d.ellipse([(x - 5) * S, (h / 2 - 5) * S, (x + 5) * S, (h / 2 + 5) * S], fill=(150, 118, 56, 255), outline=(80, 58, 24, 255), width=S)
        d.line([(x - 3) * S, (h / 2 - 2) * S, (x + 3) * S, (h / 2 + 2) * S], fill=(70, 50, 22, 255), width=S)
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, np.float32).copy()
    br = vnoise((h, w), 60, 1.5, 41, 2)
    a[..., :3] *= (1 + 0.10 * br[..., None]) * np.linspace(1.12, 0.9, h)[:, None, None]
    return to_img(a).convert("RGBA")


def chalk_stick_sprite(length=128, dia=24, tint=(244, 242, 232)):
    """A stick of chalk seen from above, lit from the upper left; tip at the left end."""
    S = 3
    w, h = (length + 16) * S, (dia + 16) * S
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cy = h / 2
    r = dia * S / 2
    v = (yy - cy) / r
    body = (np.abs(v) <= 1) & (xx >= 8 * S) & (xx <= (8 + length) * S)
    # worn, rounded writing end
    tipx = (xx - 8 * S) / (10 * S)
    taper = np.clip(tipx, 0, 1) ** 0.5
    body &= np.abs(v) <= np.maximum(taper, 0.0) + 0.001
    shade = 0.80 + 0.26 * np.sqrt(np.clip(1 - v * v, 0, 1)) - 0.10 * v
    shade *= 1 + 0.03 * vnoise((h, w), 5, None, 51, 2)
    shade *= np.where(tipx < 1.2, 0.93 + 0.07 * np.clip(tipx / 1.2, 0, 1), 1)
    a = np.zeros((h, w, 4), np.float32)
    a[..., :3] = np.array(tint, np.float32)[None, None, :] * shade[..., None]
    a[..., 3] = body * 255
    # flat far end
    endx = (8 + length) * S
    cap = ((xx - endx) / (4.5 * S)) ** 2 + v ** 2 <= 1
    a[cap, :3] = np.array(tint, np.float32) * 0.82
    a[cap, 3] = 255
    return to_img(a).convert("RGBA").resize((length + 16, dia + 16), Image.LANCZOS), (8, (dia + 16) / 2)


# ------------------------------------------------------------ chalk letters ---
LET = {
    "H": (0.60, [[(0, 0), (0, 1)], [(.60, 0), (.60, 1)], [(0, .5), (.60, .5)]]),
    "O": (0.70, [[(.36, 0), (.10, .14), (0, .5), (.12, .88), (.35, 1), (.60, .86), (.70, .5), (.58, .12), (.33, -.01)]]),
    "K": (0.60, [[(0, 0), (0, 1)], [(.58, 0), (.02, .58)], [(.20, .42), (.62, 1)]]),
    "M": (0.82, [[(0, 1), (0, 0)], [(0, 0), (.41, .74)], [(.41, .74), (.82, 0)], [(.82, 0), (.82, 1)]]),
    "N": (0.62, [[(0, 1), (0, 0)], [(0, 0), (.62, 1)], [(.62, 1), (.62, 0)]]),
    "S": (0.56, [[(.54, .13), (.32, 0), (.08, .12), (.07, .34), (.30, .49), (.52, .66), (.50, .88), (.28, 1), (.02, .86)]]),
    "T": (0.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "E": (0.54, [[(0, 0), (0, 1)], [(0, 0), (.52, 0)], [(0, .5), (.44, .5)], [(0, 1), (.54, 1)]]),
    "R": (0.60, [[(0, 1), (0, 0)], [(0, 0), (.38, .01), (.56, .13), (.56, .36), (.38, .5), (0, .5)], [(.24, .5), (.62, 1)]]),
}
LINES = [("HOOK", 150, 120, 205, 0.24), ("MONSTER", 96, 420, 158, 0.21)]   # word, x, y, cap height, gap (slate coords)
LETTER_BOX = {}     # (line, index) -> world bbox
STROKES = []        # dicts: pts (world), width, press, group, t0, t1


def build_strokes():
    rs = random.Random(303)
    for li, (word, x0, y0, cap, gap) in enumerate(LINES):
        x = x0
        for ci, ch in enumerate(word):
            wd, strokes = LET[ch]
            rot = rs.gauss(0, 0.022)
            sc = 1 + rs.gauss(0, 0.03)
            dy = rs.gauss(0, 5) + ci * (2.0 if li == 0 else -1.2)
            ca, sa = math.cos(rot), math.sin(rot)
            xs, ys = [], []
            for st in strokes:
                pts = []
                for (u, v) in st:
                    px, py = (u - wd / 2) * cap * sc, (v - 0.5) * cap * sc
                    px, py = px * ca - py * sa - (v - 0.5) * cap * 0.05, px * sa + py * ca    # slight backhand lean
                    pts.append((SX + x + wd * cap / 2 + px + rs.gauss(0, 2.2), SY + y0 + cap / 2 + dy + py + rs.gauss(0, 2.2)))
                if len(pts) == 2:      # a drawn straight line bows a little
                    (ax, ay), (bx, by) = pts
                    L = math.hypot(bx - ax, by - ay)
                    k = rs.gauss(0, 0.018) * L
                    pts = [pts[0], ((ax + bx) / 2 - (by - ay) / L * k, (ay + by) / 2 + (bx - ax) / L * k), pts[1]]
                dense = catmull(pts, 12, closed=False)
                STROKES.append(dict(pts=dense, width=17 if li == 0 else 15, press=rs.uniform(0.0, 0.16), group=("L", li, ci)))
                xs += [p[0] for p in dense]
                ys += [p[1] for p in dense]
            LETTER_BOX[(li, ci)] = (min(xs), min(ys), max(xs), max(ys))
            x += (wd + gap) * cap
    # underline flourish
    ux0, uy = SX + 92, SY + 420 + 158 + 46
    STROKES.append(dict(pts=catmull([(ux0, uy + 6), (ux0 + 260, uy - 4), (ux0 + 540, uy + 8), (ux0 + 800, uy - 8)], 14), width=13, press=0.05, group=("U",)))
    # the monster, beside the words
    ox, oy = SX + 992, SY + 66

    def sk(pts, width=11, press=0.08, closed=False, per=12):
        jit = [(ox + px + rs.gauss(0, 1.6), oy + py + rs.gauss(0, 1.6)) for px, py in pts]
        STROKES.append(dict(pts=catmull(jit, per, closed), width=width, press=press, group=("S",)))

    sk([(226, 0), (220, 30), (224, 62)], 8)                                                         # the line
    sk([(224, 62), (203, 72), (200, 92), (222, 106), (244, 92), (242, 72), (222, 61)], 10)          # the eye of the hook
    sk([(222, 106), (224, 220), (226, 330), (224, 410), (204, 486), (154, 528), (98, 514), (62, 462), (54, 400), (60, 344)], 15, 0.14)   # shank and bend
    sk([(60, 344), (76, 372), (98, 396)], 12, 0.12)                                                 # barb
    sk([(98, 396), (72, 392)], 10)
    sk([(222, 132), (188, 110), (146, 110), (114, 134), (104, 166)], 12, 0.1)                       # skull
    sk([(104, 160), (38, 192), (108, 202)], 11, 0.1)                                                # beak
    sk([(108, 202), (122, 240), (164, 268), (222, 274)], 12, 0.1)                                   # throat
    sk([(160, 138), (148, 128), (134, 138), (138, 156), (154, 160), (162, 148), (158, 136)], 8)     # eye
    sk([(146, 143), (150, 148), (146, 150), (150, 145)], 9, 0.2, per=4)                             # pupil
    sk([(150, 110), (160, 60), (174, 104), (190, 48), (202, 108), (216, 70), (220, 118)], 9)        # crest
    sk([(110, 204), (94, 250), (116, 262), (126, 238)], 9)                                          # wattle
    sk([(228, 292), (308, 300), (342, 352), (300, 340), (230, 336)], 10)                            # three flight feathers
    sk([(230, 338), (298, 352), (322, 404), (284, 388), (230, 380)], 10)
    sk([(230, 382), (282, 402), (296, 446), (262, 430), (228, 424)], 10)
    sk([(246, 306), (304, 330), (262, 350), (300, 380), (252, 396), (276, 424)], 40, -0.34)         # side of the chalk
    # timing: letters 3.6 -> 10.2, sketch 10.6 -> 14.2
    def lay(ix, a, b):
        dur, gaps = [], []
        for k, i in enumerate(ix):
            s = STROKES[i]
            _, L = resample(s["pts"], 3)
            s["len"] = L
            dur.append(0.10 + L / 1300)
            nxt = STROKES[ix[k + 1]] if k + 1 < len(ix) else None
            gaps.append(0 if nxt is None else (0.10 if nxt["group"] == s["group"] else 0.17 if nxt["group"][:2] == s["group"][:2] else 0.38))
        tot = sum(dur) + sum(gaps)
        f = (b - a) / tot
        t = a
        for k, i in enumerate(ix):
            STROKES[i]["t0"], STROKES[i]["t1"] = t, t + dur[k] * f
            t += (dur[k] + gaps[k]) * f
    nl = sum(1 for s in STROKES if s["group"][0] in "LU")
    lay(list(range(nl)), 3.6, 10.2)
    lay(list(range(nl, len(STROKES))), 10.65, 14.2)


TOOTH = None
STROKE_MASK = []     # per stroke: (x0, y0, alpha crop, arrival crop)


def build_chalk():
    """Every stroke as chalk dragged over the slate's tooth, with the time each grain lands."""
    global TOOTH
    TOOTH = (0.55 * vnoise((WH, WW), 1.6, None, 71) + 0.3 * vnoise((WH, WW), 3.5, None, 72) + 0.35 * vnoise((WH, WW), 14, 5, 73))
    rs = random.Random(9)
    for s in STROKES:
        p, L = resample(s["pts"], 2.0)
        wd = s["width"]
        pad = int(wd) + 14
        x0, y0 = int(p[:, 0].min()) - pad, int(p[:, 1].min()) - pad
        x1, y1 = int(p[:, 0].max()) + pad, int(p[:, 1].max()) + pad
        w, h = x1 - x0, y1 - y0
        arr = Image.new("F", (w, h), 1e9)
        d = ImageDraw.Draw(arr)
        n = len(p)
        dirs = np.gradient(p, axis=0)
        for k in range(n - 1, -1, -1):
            u = k / max(1, n - 1)
            # the chalk's flat end: wider across some directions than others, swelling and thinning
            ang = math.atan2(dirs[k, 1], dirs[k, 0])
            r = wd / 2 * (0.80 + 0.22 * abs(math.sin(ang - 0.9)) + 0.07 * math.sin(k * 0.13 + L))
            r *= 0.72 + 0.28 * min(1, u * 9 + 0.35) * min(1, (1 - u) * 7 + 0.5)
            x, y = p[k, 0] - x0, p[k, 1] - y0
            d.ellipse([x - r, y - r, x + r, y + r], fill=float(s["t0"] + u * (s["t1"] - s["t0"])))
        A = np.asarray(arr, np.float32)
        solid = (A < 1e8).astype(np.float32)
        soft = blur_arr(solid, 1.1)
        core = blur_arr(solid, wd * 0.30)
        g = TOOTH[y0:y1, x0:x1]
        # lanes: the stick's own ridges leave lines along the stroke; approximate with stretched noise
        lane = vnoise((h, w), 30, 2.2, rs.randint(0, 9999)) if abs(p[-1, 0] - p[0, 0]) > abs(p[-1, 1] - p[0, 1]) else vnoise((h, w), 2.2, 30, rs.randint(0, 9999))
        dens = g * 0.95 + core * 1.25 + lane * 0.30 + s["press"] - 0.52
        alpha = np.clip(dens * 2.6, 0, 1) * soft
        if wd > 30:      # side of the stick: a thin scumble
            alpha *= 0.55
        # arrival for soft fringe pixels = nearest solid arrival (max filter of negative)
        Ar = np.where(A < 1e8, A, s["t1"])
        # crumbs knocked off where the stick first touches
        for _ in range(5):
            cx, cy = p[0, 0] - x0 + rs.gauss(0, wd * 0.9), p[0, 1] - y0 + rs.gauss(0, wd * 0.9)
            if 1 <= cx < w - 2 and 1 <= cy < h - 2:
                alpha[int(cy):int(cy) + rs.randint(1, 2), int(cx):int(cx) + rs.randint(1, 3)] = rs.uniform(0.5, 0.95)
                Ar[int(cy):int(cy) + 2, int(cx):int(cx) + 3] = s["t0"]
        STROKE_MASK.append((x0, y0, alpha.astype(np.float32), Ar.astype(np.float32)))


_chalk_cache = {"n": -1, "fin": None}


def chalk_alpha(t):
    """Chalk on the board at time t (world-size float array 0..1), including settled dust."""
    n = sum(1 for s in STROKES if s["t1"] <= t)
    c = _chalk_cache
    if c["n"] != n:
        fin = np.zeros((WH, WW), np.float32)
        for k in range(len(STROKES)):
            if STROKES[k]["t1"] <= t:
                x0, y0, al, _ = STROKE_MASK[k]
                v = fin[y0:y0 + al.shape[0], x0:x0 + al.shape[1]]
                np.maximum(v, al, out=v)
        if n:
            dust = blur_arr(fin, 9) * 0.16 + blur_arr(fin, 26) * 0.10
            fin = np.maximum(fin, dust * (0.6 + 0.4 * (TOOTH > 0)))
        c["n"], c["fin"] = n, fin
    out = c["fin"]
    live = [k for k, s in enumerate(STROKES) if s["t0"] <= t < s["t1"]]
    if live:
        out = out.copy()
        for k in live:
            x0, y0, al, ar = STROKE_MASK[k]
            v = out[y0:y0 + al.shape[0], x0:x0 + al.shape[1]]
            np.maximum(v, al * (ar <= t), out=v)
    return out


# ------------------------------------------------------------- bench scene ---
B = {}


def build_bench():
    B["table"] = make_table()
    slate = make_slate()
    B["slate"] = slate
    B["rails"] = {k: rail_sprite(k) for k in ("top", "bottom", "left", "right")}
    B["plate"] = make_plate()
    B["stick"], B["stick_piv"] = chalk_stick_sprite()
    B["props"] = make_props()
    # the finished empty board in the world (what the chalk goes onto)
    world = bench_world(99.0)
    B["base"] = np.asarray(world, np.float32)
    # the board alone (for the river), as float RGB
    B["board"] = B["base"][BY:BY + BH, BX:BX + BW].copy()


def make_props():
    """Things on the bench: a tray of chalk, a saucer of water with the cloth, a felt rubber."""
    out = []
    # tray of chalks
    S = 2
    im = Image.new("RGBA", (170 * S, 150 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([4 * S, 4 * S, 166 * S, 146 * S], fill=(205, 186, 150, 255), outline=(120, 100, 70, 255), width=2 * S)
    d.rectangle([12 * S, 12 * S, 158 * S, 138 * S], fill=(150, 130, 98, 255))
    for k, col in enumerate([(244, 242, 232), (240, 236, 224), (236, 214, 150), (232, 238, 228), (226, 180, 170)]):
        y = (20 + k * 23) * S
        ln = (130 - (k * 37) % 40) * S
        d.rounded_rectangle([18 * S, y, 18 * S + ln, y + 19 * S], 6 * S, fill=col + (255,))
        d.line([18 * S + 6, y + 15 * S, 18 * S + ln - 6, y + 15 * S], fill=tuple(int(c * 0.82) for c in col) + (255,), width=3 * S)
        d.line([18 * S + 6, y + 4 * S, 18 * S + ln - 6, y + 4 * S], fill=(255, 255, 250, 255), width=2 * S)
    im = im.resize((170, 150), Image.LANCZOS)
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= (1 + 0.06 * vnoise((150, 170), 4, None, 61, 2))[..., None]
    out.append((to_img(a).convert("RGBA").rotate(4, Image.BICUBIC, expand=True), (1726, 18 + 0)))
    # the dishcloth, folded, damp
    g = to_img(gingham(150, 132, 3, wet=0.25)).convert("RGBA")
    g2 = to_img(gingham(150, 70, 4, wet=0.1) * 1.06).convert("RGBA")
    fold = Image.new("RGBA", (158, 140), (0, 0, 0, 0))
    fold.alpha_composite(g, (4, 4))
    fold.alpha_composite(shadow_of(g2.getchannel("A"), 3, 0.5), (6, 70))
    fold.alpha_composite(g2, (2, 62))
    out.append((fold.rotate(-7, Image.BICUBIC, expand=True), (1738, 820)))
    # the felt rubber
    fb = Image.new("RGBA", (72 * 2, 170 * 2), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fb)
    fd.rounded_rectangle([0, 0, 143, 339], 14, fill=(64, 62, 66, 255))
    fd.rounded_rectangle([14, 10, 129, 329], 10, fill=(150, 108, 66, 255), outline=(96, 66, 38, 255), width=4)
    for k in range(6):
        fd.line([14, 50 + k * 48, 129, 50 + k * 48], fill=(40, 40, 44, 255), width=5)
    fb = fb.resize((72, 170), Image.LANCZOS)
    fa = np.asarray(fb, np.float32).copy()
    fa[..., :3] *= (1 + 0.09 * vnoise((170, 72), 3, None, 62, 2))[..., None]
    fa[..., :3] += np.clip(vnoise((170, 72), 40, None, 63, 2), 0, 1)[..., None] * 60
    out.append((to_img(fa).convert("RGBA").rotate(12, Image.BICUBIC, expand=True), (64, 720)))
    return out


def gingham(w, h, seed=0, wet=0.0):
    """A square of checked dishcloth as float RGB."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = ((xx // 9) % 2)
    cy = ((yy // 9) % 2)
    base = np.array([226, 222, 208], np.float32)
    blue = np.array([66, 108, 150], np.float32)
    k = (cx + cy) / 2
    a = base[None, None, :] * (1 - k[..., None]) + blue[None, None, :] * k[..., None]
    weave = 0.5 * np.sin(xx * 2.1) * np.sin(yy * 2.1)
    a *= (1 + 0.05 * weave + 0.08 * vnoise((h, w), 30, None, seed, 2))[..., None]
    a *= 1 - 0.3 * wet
    return a


def paste_shadowed(world, sprite, xy, lift=0.0, blur=7, strength=0.5):
    off = (10 + lift * 0.55, 14 + lift * 0.9)
    sh = shadow_of(sprite.getchannel("A"), blur + lift * 0.18, strength * (1 - min(0.5, lift / 260)))
    world.alpha_composite(sh, (int(xy[0] + off[0]), int(xy[1] + off[1]))) if _inside(world, sh, xy, off) else _clip_paste(world, sh, (xy[0] + off[0], xy[1] + off[1]))
    _clip_paste(world, sprite, xy)


def _inside(world, sp, xy, off=(0, 0)):
    x, y = int(xy[0] + off[0]), int(xy[1] + off[1])
    return x >= 0 and y >= 0 and x + sp.size[0] <= world.size[0] and y + sp.size[1] <= world.size[1]


def _clip_paste(world, sp, xy):
    """alpha_composite that tolerates sprites hanging off the canvas."""
    x, y = int(round(xy[0])), int(round(xy[1]))
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(sp.size[0], world.size[0] - x), min(sp.size[1], world.size[1] - y)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (0, 0) + sp.size:
        sp = sp.crop((x0, y0, x1, y1))
    world.alpha_composite(sp, (x + x0, y + y0))


def twos(t):
    return math.floor(t * 12) / 12


RAIL_T = {"top": (0.95, (0, -520)), "left": (1.45, (-560, 0)), "right": (1.95, (560, 0)), "bottom": (2.45, (0, 520))}


def bench_world(t):
    """The bench at time t, before any chalk: slab slid in, four rails laid, plate dropped. RGBA world."""
    world = to_img(B["table"]).convert("RGBA")
    for sp, xy in B["props"]:
        paste_shadowed(world, sp, xy, 0, 6, 0.45)
    tt = twos(t)
    # the slab
    f = ease(tt, 0.0, 0.7)
    slab = to_img(B["slate"]).convert("RGBA")
    sx = lerp(-1500, SX - 20, f)
    lift = (1 - f) * 20
    paste_shadowed(world, slab, (sx, SY - 20 - lift * 0.2), lift, 5, 0.5)
    for k in ("top", "left", "right", "bottom"):
        t0, (dx, dy) = RAIL_T[k]
        f = ease(tt, t0, t0 + 0.42)
        if tt < t0:
            continue
        sp, (rx, ry) = B["rails"][k]
        lift = (1 - f) * 70
        paste_shadowed(world, sp, (BX + rx + dx * (1 - f), BY + ry + dy * (1 - f) - lift * 0.3), lift, 6, 0.5)
    if tt >= 2.95:
        f = ease(tt, 2.95, 3.25)
        lift = (1 - f) * 90
        pl = B["plate"]
        paste_shadowed(world, pl, (BX + BW / 2 - pl.size[0] / 2 + (1 - f) * 60, BY + 10 - (1 - f) * 150), lift, 3, 0.55)
    return world.convert("RGB")


REST = (1810, 330)         # where the chalk lies on the bench
_tip = {}


def tip_at(t):
    """Chalk tip: (x, y, height off the board, writing?)."""
    first, last = STROKES[0], STROKES[-1]
    if t < 3.05:
        return REST + (0.0, False)
    prev = None
    for s in STROKES:
        if s["t0"] <= t < s["t1"]:
            p, _ = resample(s["pts"], 3)
            u = (t - s["t0"]) / (s["t1"] - s["t0"])
            k = min(len(p) - 1, int(u * (len(p) - 1)))
            return (float(p[k, 0]), float(p[k, 1]), 0.0, True)
        if t < s["t0"]:
            a = prev["pts"][-1] if prev else REST
            ta = prev["t1"] if prev else 3.05
            f = smooth(ramp(t, ta, s["t0"]))
            d = math.hypot(s["pts"][0][0] - a[0], s["pts"][0][1] - a[1])
            hgt = math.sin(math.pi * ramp(t, ta, s["t0"])) * min(70, 14 + d * 0.12)
            return (lerp(a[0], s["pts"][0][0], f), lerp(a[1], s["pts"][0][1], f), hgt, False)
        prev = s
    f = smooth(ramp(t, last["t1"], last["t1"] + 0.9))
    a = last["pts"][-1]
    return (lerp(a[0], REST[0], f), lerp(a[1], REST[1], f), math.sin(math.pi * ramp(t, last["t1"], last["t1"] + 0.9)) * 60, False)


CAM = None


def build_cam():
    """Bench camera: wide while the board is built, close on the chalk, then back."""
    global CAM
    n = int(T_RIVER * FPS) + 2
    tips = np.array([tip_at(k / FPS)[:2] for k in range(n)], np.float32)
    win = int(1.6 * FPS)
    ker = np.hanning(win * 2 + 1)
    ker /= ker.sum()
    pad = np.pad(tips, ((win, win), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, 0], ker, "valid"), np.convolve(pad[:, 1], ker, "valid")], 1)
    CAM = np.zeros((n, 3), np.float32)
    for k in range(n):
        t = k / FPS
        close = ease(t, 3.25, 4.3) * (1 - ease(t, 14.15, 15.3))
        sc = lerp(0.5, 0.86, close)
        cx = lerp(WW / 2, sm[k, 0] * 0.8 + 0.2 * (SX + SW * 0.42), close)
        cy = lerp(WH / 2, sm[k, 1] * 0.12 + 0.88 * (SY + SH * 0.49), close)
        hw, hh = W / sc / 2, H / sc / 2
        CAM[k] = (min(max(cx, hw), WW - hw), min(max(cy, hh), WH - hh), sc)


def bench_frame(t, ink):
    k = min(len(CAM) - 1, int(round(t * FPS)))
    cx, cy, sc = (float(v) for v in CAM[k])
    hw, hh = W / sc / 2, H / sc / 2
    x0, y0 = int(cx - hw), int(cy - hh)
    x1, y1 = min(WW, x0 + int(round(hw * 2))), min(WH, y0 + int(round(hh * 2)))
    if t < 3.3:
        base = np.asarray(bench_world(t), np.float32)[y0:y1, x0:x1]
        img = to_img(base)
    else:
        a = chalk_alpha(t)[y0:y1, x0:x1, None] * 0.93
        img = to_img(B["base"][y0:y1, x0:x1] * (1 - a) + CHALK * a)
    img = img.resize((W, H), Image.LANCZOS).convert("RGBA")
    # the stick and its shadow
    tx, ty, hgt, down = tip_at(t)
    px, py = (tx - x0) * sc, (ty - y0) * sc
    ang = 52 + 7 * math.sin(tx * 0.011 + ty * 0.017) - (0 if hgt else 4) + (38 * (1 - ramp(t, 3.05, 3.5)) if t < 3.6 else 0) + 38 * ramp(t, 14.4, 15.0)
    st = B["stick"]
    s2 = st.resize((max(2, int(st.size[0] * sc * 1.12)), max(2, int(st.size[1] * sc * 1.12))), Image.LANCZOS)
    pv = (B["stick_piv"][0] * sc * 1.12, B["stick_piv"][1] * sc * 1.12)
    big = Image.new("RGBA", (s2.size[0] * 2 + 8, s2.size[0] * 2 + 8), (0, 0, 0, 0))
    c = big.size[0] // 2
    big.alpha_composite(s2, (int(c - pv[0]), int(c - pv[1])))
    rot = big.rotate(ang, Image.BICUBIC)
    lift = hgt * sc
    sh = shadow_of(rot.getchannel("A"), 2.5 + lift * 0.10, 0.5 * (1 - min(0.55, lift / 130)))
    _clip_paste(img, sh, (px - c + 5 + lift * 0.5, py - c + 7 + lift * 0.9))
    _clip_paste(img, rot, (px - c - lift * 0.10, py - c - lift * 0.35))
    ink.img = img.convert("RGB")
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.vignette(0.22)


# ================================================================ CUT PAPER
# Everything in the river is cut paper: each piece is its own sheet with fibre, a cut edge that
# shows the paper's core, and a shadow on whatever lies beneath it. Pieces hang on a joint tree.
FIBRE = None


def fibre_tex():
    global FIBRE
    if FIBRE is None:
        n = 900
        f = 0.5 * vnoise((n, n), 1.6, None, 81) + 0.45 * vnoise((n, n), 22, 1.3, 82) + 0.35 * vnoise((n, n), 1.3, 18, 83) + 0.5 * vnoise((n, n), 60, None, 84, 2)
        FIBRE = f.astype(np.float32)
    return FIBRE


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
    """Cut one piece of coloured paper along pts (design coords)."""
    P = catmull(pts, per, closed=True) if curve else [tuple(p) for p in pts]
    xs, ys = [p[0] for p in P], [p[1] for p in P]
    pad = 3
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    w, h = int(math.ceil(max(xs))) - x0 + pad, int(math.ceil(max(ys))) - y0 + pad
    S = 3
    m = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m).polygon([((x - x0) * S, (y - y0) * S) for x, y in P], fill=255)
    col = Image.new("RGB", (w * S, h * S), tuple(int(c) for c in color))
    if deco:
        deco(ImageDraw.Draw(col), lambda x, y: ((x - x0) * S, (y - y0) * S), S)
    m = m.resize((w, h), Image.LANCZOS)
    col = col.resize((w, h), Image.LANCZOS)
    a = np.asarray(col, np.float32).copy()
    al = np.asarray(m, np.float32) / 255
    F = fibre_tex()
    oy_, ox_ = (seed * 131) % (900 - h) if h < 900 else 0, (seed * 57) % (900 - w) if w < 900 else 0
    fb = F[oy_:oy_ + h, ox_:ox_ + w]
    if fb.shape != (h, w):
        fb = np.resize(fb, (h, w))
    a *= (1 + grain * fb)[..., None]
    hl = np.clip(al - np.roll(al, (1, 1), (0, 1)), 0, 1)
    dk = np.clip(al - np.roll(al, (-1, -1), (0, 1)), 0, 1)
    a += edge * (70 * hl - 60 * dk)[..., None]
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
            # only where there is paper beneath
            under = im.getchannel("A")
            tmp = Image.new("RGBA", im.size, (0, 0, 0, 0))
            tmp.alpha_composite(sh, (int(s.ox - x0 + shadow[0]), int(s.oy - y0 + shadow[1])))
            tmp.putalpha(ImageChops.multiply(tmp.getchannel("A"), under))
            im.alpha_composite(tmp)
        im.alpha_composite(s.img, (s.ox - x0, s.oy - y0))
    return Sprite(im, x0, y0)


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
    v = M @ np.array([p[0], p[1], 1.0])
    return (float(v[0]), float(v[1]))


def draw_sprite(layer, spr, M, shadow=(2.0, 2.8, 1.5, 0.36)):
    """Lay a sprite on an RGBA layer under the affine M (design -> layer px)."""
    det = M[0, 0] * M[1, 1] - M[0, 1] * M[1, 0]
    sc = math.sqrt(abs(det))
    if sc < 1e-3:
        return
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
        _clip_paste(layer, sh, (x0c + shadow[0] * sc, y0c + shadow[1] * sc))
    _clip_paste(layer, out, (x0c, y0c))


class Puppet:
    """A joint tree. Every part is drawn in one shared design frame; a part turns about its pivot
    and carries its children with it (forward kinematics)."""

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
            ang = v[0]
            dx, dy = (v[1], v[2]) if len(v) > 2 else (0.0, 0.0)
            sx, sy = (v[3], v[4]) if len(v) > 4 else (1.0, 1.0)
            px, py = p["pivot"]
            out[name] = Mp @ Tm(px + dx, py + dy) @ Rm(ang) @ Sm(sx, sy) @ Tm(-px, -py)
            return out[name]
        for n in self.parts:
            get(n)
        return out

    def draw(self, layer, pose, M_root, sprites=None, skip=()):
        ms = self.mats(pose, M_root)
        for n in self.order:
            if n in skip:
                continue
            spr = (sprites or {}).get(n) or self.parts[n]["spr"]
            if spr is not None:
                draw_sprite(layer, spr, ms[n])
        return ms


# ------------------------------------------------------------------ trout ---
TROUT_PAL = {
    "rainbow": dict(back=(98, 124, 86), belly=(228, 216, 190), stripe=(204, 118, 120), fin=(158, 146, 100), head=(84, 110, 84), spot=(34, 44, 36),
                    cheek=(198, 122, 118), satchel=(140, 62, 46), flap=(112, 44, 36)),
    "brown": dict(back=(150, 114, 62), belly=(236, 208, 150), stripe=None, fin=(184, 142, 78), head=(132, 98, 54), spot=(60, 36, 22),
                  cheek=(214, 170, 96), satchel=(70, 96, 122), flap=(50, 70, 96), red=(178, 58, 44)),
    "brook": dict(back=(62, 88, 92), belly=(228, 152, 86), stripe=None, fin=(196, 98, 58), head=(54, 78, 84), spot=(226, 214, 160),
                  cheek=(96, 122, 120), satchel=(176, 128, 64), flap=(140, 96, 44), red=(206, 76, 60)),
}
MOUTH = (5, 69)


def make_trout(kind, seed=1):
    pal = TROUT_PAL[kind]
    rs = random.Random(seed)
    dk = lambda c, f=0.72: tuple(int(v * f) for v in c)  # noqa: E731
    lt = lambda c, f=1.22: tuple(min(255, int(v * f)) for v in c)  # noqa: E731
    body_pts = [(2, 63), (18, 41), (50, 25), (100, 14), (150, 16), (195, 30), (228, 47), (242, 55), (242, 71), (226, 81), (190, 97), (145, 107), (95, 105), (50, 93), (18, 79)]

    def body_deco(d, L, S):
        # scales: rows of small arcs
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
        if pal["stripe"]:
            band = catmull([(58, 60), (110, 58), (170, 56), (244, 57), (244, 65), (170, 67), (110, 70), (58, 71)], 8, closed=True)
            d.polygon([L(*p) for p in band], fill=pal["stripe"])
            d.line([L(*p) for p in catmull([(58, 71), (110, 70), (170, 67), (244, 65)], 8)], fill=dk(pal["stripe"], 0.75), width=S)
        for _ in range(64 if kind != "brook" else 40):
            x, y = rs.uniform(70, 238), rs.uniform(16, 66 if kind != "rainbow" else 56)
            r = rs.uniform(1.6, 3.6)
            if kind == "brown" and rs.random() < 0.25:
                d.ellipse([L(x - r - 2, y - r - 2), L(x + r + 2, y + r + 2)], fill=lt(pal["belly"], 1.0))
                d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=pal["red"])
            elif kind == "brook" and rs.random() < 0.2:
                d.ellipse([L(x - r - 1.5, y - r - 1.5), L(x + r + 1.5, y + r + 1.5)], fill=(90, 130, 170))
                d.ellipse([L(x - r * 0.7, y - r * 0.7), L(x + r * 0.7, y + r * 0.7)], fill=pal["red"])
            else:
                d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=pal["spot"])

    def rays(hx, hy, tips, col):
        def deco(d, L, S):
            for (tx, ty) in tips:
                d.line([L(hx, hy), L(tx, ty)], fill=col, width=S)
        return deco

    fin = pal["fin"]
    P = Puppet()
    P.add("body", cut(body_pts, pal["back"], body_deco, seed=seed), (120, 62), None, 2)
    tail_pts = [(226, 50), (262, 22), (294, 12), (282, 60), (296, 110), (262, 100), (226, 74)]
    P.add("tail", cut(tail_pts, fin, rays(230, 62, [(262 + k * 4, 16 + k * 11.5) for k in range(9)], dk(fin)), per=5, seed=seed + 1), (236, 62), "body", 0)
    P.add("dorsal", cut([(98, 20), (116, -16), (150, -22), (170, -4), (164, 22)], fin, rays(130, 24, [(112 + k * 9, -12 - (k % 3) * 3) for k in range(7)], dk(fin)), per=5, seed=seed + 2), (132, 20), "body", 1)
    P.add("adipose", cut([(198, 34), (210, 18), (222, 36)], dk(fin, 0.9), per=5, seed=seed + 3), (208, 34), "body", 1)
    P.add("anal", cut([(170, 98), (188, 128), (212, 120), (208, 90)], fin, rays(186, 100, [(186 + k * 6, 124 - k) for k in range(5)], dk(fin)), per=5, seed=seed + 4), (188, 100), "body", 1)
    P.add("pelvic", cut([(118, 104), (126, 132), (152, 128), (148, 102)], fin, rays(132, 106, [(128 + k * 6, 128) for k in range(5)], dk(fin)), per=5, seed=seed + 5), (132, 106), "body", 1)
    P.add("strap", cut([(93, 12), (104, 11), (113, 58), (109, 108), (98, 108), (102, 58)], dk(pal["flap"], 0.8), per=5, seed=seed + 6), (104, 58), "body", 3)

    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(44, 60), (62, 52), (76, 66), (64, 84), (46, 80)], 8, closed=True)], fill=pal["cheek"])
        d.arc([L(40, 22), L(82, 98)], -62, 70, fill=dk(pal["head"], 0.6), width=2 * S)
        d.ellipse([L(11, 50), L(14, 53)], fill=dk(pal["head"], 0.5))
        d.polygon([L(*p) for p in catmull([(0, 70), (30, 72), (60, 86), (56, 100), (16, 84)], 8, closed=True)], fill=pal["belly"])
    head_pts = [(2, 63), (18, 41), (50, 25), (66, 20), (78, 40), (82, 62), (74, 86), (57, 96), (48, 93), (18, 79)]
    P.add("head", cut(head_pts, pal["head"], head_deco, seed=seed + 7), (70, 58), "body", 4)
    P.add("jaw", cut([(3, 67), (22, 69), (40, 71), (46, 82), (24, 83), (7, 76)], lt(pal["belly"], 0.97), per=5, seed=seed + 8), (40, 74), "head", 5)

    def eye_deco(d, L, S):
        d.ellipse([L(27, 40), L(43, 56)], fill=(232, 222, 190))
    P.add("eye", cut(circ(35, 48, 10.5), (186, 150, 70), eye_deco, curve=False, seed=seed + 9), (35, 48), "head", 6)

    def pup_deco(d, L, S):
        d.ellipse([L(31.5, 44), L(34, 46.5)], fill=(240, 240, 230))
    P.add("pupil", cut(circ(34, 48, 5.2, 20), (22, 22, 24), pup_deco, curve=False, seed=seed + 10, edge=0.4), (34, 48), "eye", 7)
    # satchel: bag, flap, buckle, with a reed pen sticking out
    def stitch(d, L, S):
        for k in range(11):
            d.line([L(86 + k * 4.6, 60), L(88 + k * 4.6, 60)], fill=lt(pal["flap"], 1.6), width=S)
        d.line([L(84, 77), L(110, 86), L(136, 77)], fill=dk(pal["flap"], 0.7), width=S)
    bag = cut(rrect(82, 56, 138, 102, 7), pal["satchel"], curve=False, seed=seed + 11)
    flap = cut([(79, 54), (141, 54), (141, 74), (126, 84), (110, 88), (94, 84), (79, 74)], pal["flap"], stitch, per=6, seed=seed + 12)
    buckle = cut(rrect(105, 82, 116, 94, 2), (196, 160, 80), curve=False, seed=seed + 13)
    pen = cut([(124, 58), (130, 30), (134, 31), (129, 58)], (214, 188, 110), curve=False, seed=seed + 14)
    P.add("satchel", compose([pen, bag, flap, buckle]), (106, 54), "body", 6.5)
    P.add("pect", cut([(73, 82), (84, 77), (112, 92), (132, 110), (118, 124), (92, 110)], lt(fin, 1.08), rays(78, 82, [(124 - k * 6, 116 - k * 2) for k in range(6)], dk(fin)), per=5, seed=seed + 15), (79, 82), "body", 8)
    return P


def trout_pose(t, wag=12.0, freq=1.6, phase=0.0, point=0.0, jaw=0.0, gaze=(0, 0), satchel=0.0, nod=0.0):
    w = math.sin(2 * math.pi * freq * t + phase)
    return {
        "tail": wag * w,
        "dorsal": 4 * math.sin(2 * math.pi * 0.7 * t + phase),
        "anal": 6 * math.sin(2 * math.pi * freq * t + phase - 0.8),
        "pelvic": 8 * math.sin(2 * math.pi * 1.1 * t + phase),
        "head": nod - wag * 0.12 * w,
        "jaw": -jaw,
        "pupil": (0.0, gaze[0], gaze[1]),
        "satchel": satchel,
        "pect": lerp(10 * math.sin(2 * math.pi * 2.2 * t + phase), -138 + 8 * math.sin(2 * math.pi * 3 * t), point),
    }


def root_M(x, y, pitch=0.0, scale=1.0, flip=1.0, anchor=(120, 62)):
    """Design faces left. flip=-1 faces right; pitch lifts the nose either way."""
    return Tm(x, y) @ Rm(pitch * (1 if flip >= 0 else -1)) @ Sm(scale * flip, scale) @ Tm(-anchor[0], -anchor[1])


# ----------------------------------------------------------------- Turkey ---
def make_turkey():
    P = Puppet()
    skin, red, dkred = (150, 178, 196), (198, 72, 62), (150, 44, 44)

    def feath(d, L, S):
        for row in range(4):
            for col in range(9):
                x, y = 74 + col * 17 + (row % 2) * 8, 196 + row * 16
                d.pieslice([L(x - 12, y - 12), L(x + 12, y + 12)], 0, 180, fill=(92, 66, 44), outline=(40, 28, 20), width=S)
                d.arc([L(x - 9, y - 6), L(x + 9, y + 10)], 20, 160, fill=(176, 130, 70), width=S)
    P.add("collar", cut([(66, 300), (70, 214), (96, 190), (140, 182), (184, 190), (208, 216), (214, 300)], (58, 42, 32), feath, per=6, seed=1), (140, 240), None, 0)

    def neck_deco(d, L, S):
        for k in range(26):
            x, y = 104 + (k * 37) % 62, 128 + (k * 53) % 90
            d.ellipse([L(x - 7, y - 6), L(x + 7, y + 6)], fill=(214, 96, 84) if k % 3 else dkred)
    P.add("neck", cut([(102, 226), (94, 170), (100, 120), (128, 100), (160, 110), (174, 160), (178, 226)], red, neck_deco, seed=2), (138, 210), "collar", 1)

    def head_deco(d, L, S):
        d.polygon([L(*p) for p in catmull([(96, 60), (130, 50), (166, 62), (150, 74), (112, 72)], 8, closed=True)], fill=(170, 196, 212))
        for k in range(9):
            x, y = 140 + (k * 29) % 34, 96 + (k * 17) % 26
            d.ellipse([L(x - 3, y - 3), L(x + 3, y + 3)], fill=(128, 156, 178))
    P.add("head", cut([(84, 96), (88, 66), (112, 48), (144, 48), (168, 68), (172, 100), (160, 128), (128, 138), (98, 124)], skin, head_deco, seed=3), (136, 124), "neck", 2)
    P.add("beak2", cut([(92, 106), (52, 112), (92, 118)], (190, 150, 70), curve=False, seed=4), (92, 110), "head", 2.5)
    P.add("beak", cut([(90, 86), (38, 108), (94, 110)], (222, 180, 88), curve=False, seed=5), (92, 98), "head", 3)
    P.add("wattle", cut([(96, 112), (122, 110), (128, 150), (112, 182), (94, 162)], red, seed=6), (108, 116), "head", 2.8)
    P.add("snood", cut([(86, 76), (100, 74), (96, 102), (80, 140), (68, 136), (78, 102)], dkred, seed=7), (93, 78), "head", 4)

    def eye_deco(d, L, S):
        d.ellipse([L(111, 75), L(127, 91)], fill=(240, 236, 220))
    P.add("eye", cut(circ(119, 83, 11), (120, 150, 176), eye_deco, curve=False, seed=8), (119, 83), "head", 5)
    P.add("pupil", cut(circ(117, 84, 5.4, 20), (20, 20, 22), curve=False, seed=9, edge=0.4), (117, 84), "eye", 6)
    P.add("lid", cut([(107, 82), (112, 73), (126, 73), (131, 82)], (126, 156, 180), per=5, seed=10), (119, 74), "eye", 7)
    return P


def turkey_pose(t, wattle=0.0, snood=0.0, lean=0.0, gaze=(0, 0)):
    blink = 1.0 if (t * 0.37 + 0.2) % 1.0 < 0.035 else 0.0
    return {"neck": lean + 2.5 * math.sin(t * 1.3), "head": lean * 0.6 + 3 * math.sin(t * 0.9 + 1), "wattle": wattle, "snood": snood,
            "pupil": (0.0, gaze[0], gaze[1]), "lid": (0.0, 0.0, 9.0 * blink - 9.0 * (1 - blink) * 0.0 - (0 if blink else 7.5)), "beak2": 3 + 3 * math.sin(t * 2.1)}


# -------------------------------------------------------------------- tin ---
def foil(color, seed):
    def deco(d, L, S):
        pass
    return deco


def make_tin():
    """Turkey's submersible: a bread-roll tin with a lid, one round six-bolt brass porthole, a screw and a hook."""
    P = Puppet()
    tinc, lidc = (176, 186, 182), (158, 170, 168)

    def body_deco(d, L, S):
        for y in (96, 150, 184):
            d.line([L(8, y), L(396, y)], fill=(120, 132, 130), width=2 * S)
            d.line([L(8, y + 2.5), L(396, y + 2.5)], fill=(222, 230, 226), width=S)
        for k in range(40):
            x = 10 + k * 9.8
            d.line([L(x, 100), L(x, 148)], fill=(164, 174, 170), width=S)
        # rust at the seams
        for k in range(40):
            x, y = (k * 97) % 400, 186 + (k * 13) % 16
            d.ellipse([L(x - 5, y - 3), L(x + 5, y + 3)], fill=(150, 110, 78))
    P.add("body", cut(rrect(0, 56, 404, 204, 30), tinc, body_deco, curve=False, seed=21, grain=0.11), (200, 130), None, 2)

    def lid_deco(d, L, S):
        d.line([L(-4, 70), L(408, 70)], fill=(110, 122, 120), width=2 * S)
        for k in range(21):
            x = 8 + k * 19.4
            d.ellipse([L(x - 2.5, 60), L(x + 2.5, 65)], fill=(214, 222, 218), outline=(96, 106, 104))
    P.add("lid", cut(rrect(-8, 30, 412, 76, 18), lidc, lid_deco, curve=False, seed=22, grain=0.11), (200, 50), "body", 3)
    P.add("knob", compose([cut(rrect(184, 16, 220, 32, 5), (120, 90, 50), curve=False, seed=23), cut(rrect(176, 6, 228, 20, 6), (196, 160, 80), curve=False, seed=24)]), (202, 30), "lid", 2.5)

    def label_deco(d, L, S):
        d.rectangle([L(262, 106), L(366, 150)], outline=(150, 44, 40), width=2 * S)
        f = font("serif", 24 * S)
        d.text(L(314, 128), "ROLLS", font=f, fill=(120, 36, 34), anchor="mm")
    P.add("label", cut(rrect(256, 100, 372, 156, 4), (236, 226, 198), label_deco, curve=False, seed=25), (314, 128), "body", 3)
    # rudder and screw at the stern (right)
    P.add("rudder", cut([(396, 100), (446, 76), (452, 130), (446, 184), (396, 160)], lidc, curve=False, seed=26), (400, 130), "body", 1)
    P.add("hub", cut(circ(452, 130, 9), (196, 160, 80), curve=False, seed=27), (452, 130), "body", 4)
    P.add("blade", cut([(450, 130), (444, 96), (456, 70), (466, 96), (458, 130), (466, 164), (456, 190), (444, 164)], (206, 170, 86), per=5, seed=28), (452, 130), "body", 3.5)
    # keel skids
    P.add("skid", cut(rrect(60, 200, 340, 214, 6), (120, 130, 128), curve=False, seed=29), (200, 206), "body", 1)
    # the hook on its chain

    def chain_deco(d, L, S):
        for k in range(9):
            y = 208 + k * 8
            d.ellipse([L(196, y), L(204, y + 9)], outline=(70, 60, 40), width=S)
    P.add("chain1", cut(rrect(196, 206, 204, 282, 3), (150, 128, 76), chain_deco, curve=False, seed=30), (200, 208), "body", 0.5)

    def chain_deco2(d, L, S):
        for k in range(7):
            y = 278 + k * 8
            d.ellipse([L(196, y), L(204, y + 9)], outline=(70, 60, 40), width=S)
    P.add("chain2", cut(rrect(196, 276, 204, 336, 3), (150, 128, 76), chain_deco2, curve=False, seed=31), (200, 280), "chain1", 0.4)
    hook_out = catmull([(200, 330), (201, 372), (192, 398), (170, 408), (150, 396), (144, 372), (148, 356)], 8)
    left, right = [], []
    for k, (x, y) in enumerate(hook_out):
        a, b = hook_out[max(0, k - 1)], hook_out[min(len(hook_out) - 1, k + 1)]
        nx, ny = -(b[1] - a[1]), (b[0] - a[0])
        L_ = math.hypot(nx, ny) or 1
        wd = 5.5 * (1 - 0.75 * max(0, k / len(hook_out) - 0.8) / 0.2)
        left.append((x + nx / L_ * wd, y + ny / L_ * wd))
        right.append((x - nx / L_ * wd, y - ny / L_ * wd))
    hk = cut(left + right[::-1], (206, 170, 86), curve=False, seed=32)
    barb = cut([(148, 356), (164, 372), (152, 372)], (206, 170, 86), curve=False, seed=33)
    ring = cut(circ(200, 334, 8), (206, 170, 86), lambda d, L, S: d.ellipse([L(196.5, 330.5), L(203.5, 337.5)], fill=(60, 80, 78)), curve=False, seed=34)
    P.add("hook", compose([hk, barb, ring]), (200, 332), "chain2", 0.3)
    # porthole: window (dynamic) and brass ring with six bolts
    P.add("window", None, (128, 132), "body", 5)

    def ring_deco(d, L, S):
        d.ellipse([L(128 - 47, 132 - 47), L(128 + 47, 132 + 47)], fill=(60, 60, 60))
        d.ellipse([L(128 - 62, 132 - 62), L(128 + 62, 132 + 62)], outline=(226, 196, 120), width=2 * S)
        d.ellipse([L(128 - 50, 132 - 50), L(128 + 50, 132 + 50)], outline=(120, 90, 40), width=2 * S)
    ringm = cut(circ(128, 132, 64, 60), (192, 154, 76), ring_deco, curve=False, seed=35, grain=0.10)
    # punch the hole
    a = np.asarray(ringm.img).copy()
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    rr = np.hypot(xx + ringm.ox - 128 + 0.5, yy + ringm.oy - 132 + 0.5)
    a[..., 3] = (a[..., 3] * np.clip(rr - 47, 0, 1)).astype(np.uint8)
    pieces = [Sprite(Image.fromarray(a, "RGBA"), ringm.ox, ringm.oy)]
    for k in range(6):
        an = math.radians(90 + 60 * k)
        bx, by = 128 + 55.5 * math.cos(an), 132 + 55.5 * math.sin(an)
        pieces.append(cut([(bx + 6.5 * math.cos(math.radians(60 * j + 15 * k)), by + 6.5 * math.sin(math.radians(60 * j + 15 * k))) for j in range(6)], (222, 186, 100), curve=False, seed=40 + k))
    P.add("ring", compose(pieces, shadow=(1.2, 1.8, 1.0, 0.45)), (128, 132), "body", 6)
    return P


WIN_R = 48


def tin_window(turkey, pose, lean=0.0):
    """What shows in the tin's porthole: lamplit inside, Turkey's head, glass."""
    n = WIN_R * 2 + 4
    S = 2
    im = Image.new("RGBA", (n * S, n * S), (52, 40, 30, 255))
    d = ImageDraw.Draw(im)
    for k in range(10):
        r = n * S * (0.75 - k * 0.06)
        d.ellipse([n * S * 0.62 - r, n * S * 0.36 - r, n * S * 0.62 + r, n * S * 0.36 + r], fill=(60 + k * 9, 44 + k * 6, 30 + k * 3, 255))
    M = Tm(n * S * 0.50 + lean * S, n * S * 0.56) @ Sm(0.62 * S) @ Tm(-128, -110)
    turkey.draw(im, pose, M)
    d = ImageDraw.Draw(im)
    d.arc([10 * S, 8 * S, (n - 10) * S, (n - 8) * S], 196, 262, fill=(255, 255, 250, 150), width=4 * S)
    d.arc([18 * S, 16 * S, (n - 18) * S, (n - 16) * S], 20, 50, fill=(255, 255, 250, 70), width=3 * S)
    im = im.resize((n, n), Image.LANCZOS)
    m = Image.new("L", (n * 2, n * 2), 0)
    ImageDraw.Draw(m).ellipse([4, 4, n * 2 - 4, n * 2 - 4], fill=255)
    im.putalpha(m.resize((n, n), Image.LANCZOS))
    return Sprite(im, 128 - n // 2, 132 - n // 2)


# ---------------------------------------------------------------- scenery ---
def make_rock(seed, w, h, base=(74, 96, 84), moss=(104, 132, 76)):
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
            d.line([L(x, y), L(x + rs.uniform(-30, 30), y + rs.uniform(8, 40))], fill=tuple(int(c * 0.7) for c in base), width=S)
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
        x = x_r + (x_l - x_r) * k / 7
        mp.append((x, h * (0.50 + 0.14 * math.sin(k * 2.3 + seed) + rs.uniform(-0.06, 0.06))))

    def mdeco(d, L, S):
        for _ in range(40):
            x, y = rs.uniform(0, w), rs.uniform(0, h * 0.7)
            r = rs.uniform(1.5, 4)
            d.ellipse([L(x - r, y - r), L(x + r, y + r)], fill=tuple(min(255, int(c * rs.uniform(0.8, 1.25))) for c in moss))
    return compose([rock, cut(mp, moss, mdeco, per=5, seed=seed + 1)])


def make_blade(seed, length, width, color):
    """One weed blade in three hinged paper segments. Returns a Puppet growing up from (0,0)."""
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
            d.line([L(0, y0), L(0, y1)], fill=tuple(int(c * 0.78) for c in col), width=S)
        spr = cut([(-w0 / 2, y0), (-(w0 + w1) / 4 + bend, (y0 + y1) / 2), (-w1 / 2, y1), (w1 / 2, y1), ((w0 + w1) / 4 + bend, (y0 + y1) / 2), (w0 / 2, y0)], col, deco, per=5, seed=seed + k)
        P.add(f"s{k}", spr, (0, -k * seg), parent, k)
        parent = f"s{k}"
    return P


def make_bed(w, h, seed, color=(64, 92, 78)):
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


def make_minnow(seed, color=(40, 78, 78)):
    return cut([(0, 6), (10, 0), (26, 3), (34, 6), (44, 0), (42, 7), (44, 13), (34, 8), (24, 11), (10, 12)], color, per=4, seed=seed, edge=0.5)


def make_cloth():
    """The wet dishcloth: a checked square held by one corner."""
    def deco(d, L, S):
        for k in range(-2, 12):
            d.line([L(-40 + k * 10, 0), L(-40 + k * 10 + 30, 90)], fill=(70, 104, 140), width=3 * S)
        for k in range(0, 10):
            d.line([L(-50, 6 + k * 10), L(60, -8 + k * 10)], fill=(70, 104, 140), width=3 * S)
        for k in range(-2, 12):
            for j in range(0, 10):
                pass
    return cut([(0, 0), (22, 10), (40, 30), (34, 58), (18, 78), (-6, 84), (-26, 70), (-30, 44), (-18, 18)], (204, 206, 196), deco, per=6, seed=77)

# =================================================================== RIVER
WATER = (50, 112, 106)
R = {}
WIPES = []


def hbox(a, n):
    """Box blur along x (a smear in the direction the cloth travels)."""
    c = np.cumsum(np.pad(a, ((0, 0), (n, n)), mode="edge"), axis=1)
    return (c[:, 2 * n:] - c[:, :-2 * n]) / (2 * n)


def build_wipes():
    """The lipogram: which letters the wet cloth takes, and when each grain goes."""
    full = chalk_alpha(99.0).copy()
    R["full"] = full
    for name, letters, (a1, b1, a2, b2), seed in (("w1", [(1, 1), (1, 2)], (17.3, 18.3, 18.5, 19.4), 5), ("w2", [(0, 0), (0, 1)], (26.3, 27.3, 27.5, 28.4), 9)):
        bx = [LETTER_BOX[k] for k in letters]
        x0, y0 = int(min(b[0] for b in bx)) - 22, int(min(b[1] for b in bx)) - 30
        x1, y1 = int(max(b[2] for b in bx)) + 22, int(max(b[3] for b in bx)) + 30
        M = 54
        C = full[y0 - M:y1 + M, x0 - M:x1 + M]
        hh, ww = C.shape
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
        rect = ((xx >= M) & (xx < ww - M) & (yy >= M) & (yy < hh - M)).astype(np.float32)
        band = ((blur_arr(rect, 16) + 0.34 * vnoise((hh, ww), 30, None, seed)) > 0.5).astype(np.float32)
        band = blur_arr(band, 1.6)
        d = vnoise((hh, ww), 46, 12, seed + 1) * 30
        u = np.clip((xx - M + d) / (ww - 2 * M), -0.2, 1.2)
        streak = (vnoise((hh, ww), 220, 3.5, seed + 2, 2) * 0.5 + 0.5)
        smear = 0.40 * hbox(C, 34) + 0.16 * C * (TOOTH[y0 - M:y1 + M, x0 - M:x1 + M] > 0.1)
        ghost = 0.085 * blur_arr(C, 2.6) + 0.09 * hbox(C, 80) * streak + 0.05 * streak
        WIPES.append(dict(name=name, box=(x0, y0, x1, y1), M=M, C=C, band=band, arr1=a1 + u * (b1 - a1), arr2=a2 + (1 - u) * (b2 - a2),
                          smear=smear.astype(np.float32), ghost=ghost.astype(np.float32), t=(a1, b1, a2, b2)))


def river_chalk(t):
    out = R["full"]
    copied = False
    for wp in WIPES:
        a1, b1, a2, b2 = wp["t"]
        if t < a1 - 0.2:
            continue
        if not copied:
            out = out.copy()
            copied = True
        m1 = wp["band"] * (wp["arr1"] <= t)
        m2 = wp["band"] * (wp["arr2"] <= t)
        st = wp["C"] * (1 - m1) + wp["smear"] * m1 * (1 - m2) + wp["ghost"] * m2
        x0, y0, x1, y1 = wp["box"]
        M = wp["M"]
        out[y0 - M:y1 + M, x0 - M:x1 + M] = st
    return out


def wipe_key(t):
    k = []
    for wp in WIPES:
        a1, b1, a2, b2 = wp["t"]
        k.append(0 if t < a1 - 0.2 else 2 if t > b2 + 0.3 else ("live", t))
    return tuple(k)


def cloth_world(wp, t):
    """Where the cloth is on the board during a wipe (world px)."""
    a1, b1, a2, b2 = wp["t"]
    x0, y0, x1, y1 = wp["box"]
    if t <= b1:
        u = ramp(t, a1, b1)
    elif t <= a2:
        u = 1.0
    else:
        u = 1 - ramp(t, a2, b2)
    ph = (t - a1) * 2 * math.pi * 2.4
    amp = 0.30 * (y1 - y0) * (1 if a1 <= t <= b2 else 0) * (0 if b1 < t < a2 else 1)
    return (lerp(x0 + 6, x1 - 6, u), (y0 + y1) / 2 + amp * math.sin(ph))


_board_cache = {}


def board_img(t):
    """The framed board with its chalk as it stands in the river (full-res RGB, water-tinted)."""
    key = wipe_key(t)
    if _board_cache.get("key") != key:
        a = river_chalk(t)[BY:BY + BH, BX:BX + BW, None] * 0.95
        arr = (B["board"] * (1 - a) + CHALK * a) * np.array([0.80, 0.97, 0.93], np.float32)
        _board_cache["key"], _board_cache["img"] = key, to_img(arr)
    return _board_cache["img"]


# ----------------------------------------------------------- camera, planes ---
PLANES = {1: dict(par=0.30, haze=0.60, blur=2.0, sh=None),
          2: dict(par=0.62, haze=0.32, blur=0.9, sh=(5, 8, 7, 0.22)),
          3: dict(par=1.00, haze=0.10, blur=0, sh=(7, 11, 8, 0.30)),
          4: dict(par=1.22, haze=0.03, blur=0, sh=(9, 14, 8, 0.30)),
          5: dict(par=1.95, haze=0.0, blur=4.5, sh=None)}
CEN = {2: (480.0, 262.0), 3: (480.0, 270.0)}
BOARD = {2: dict(c=(480, 236), w=430, rot=-1.5), 3: dict(c=(318, 250), w=500, rot=-2.5)}


def board_M(part):
    """World board px -> stage."""
    b = BOARD[part]
    return Tm(*b["c"]) @ Rm(b["rot"]) @ Sm(b["w"] / BW) @ Tm(-(BX + BW / 2), -(BY + BH / 2))


def camera(part, t):
    if part == 2:
        z = lerp(0.95, 1.12, ease(t, T_RIVER + 0.2, 17.5)) + 0.05 * ramp(t, 20, T_TROUT)
        tgt = apply(board_M(2), (SX + 520, SY + 400))
        f = ease(t, T_RIVER + 0.2, 17.5)
        F = (lerp(480, 474, f), lerp(250, 262, f))
        dx = 12 * math.sin(0.55 * (t - T_RIVER)) + 4 * math.sin(1.3 * t)
        dy = 3 * math.sin(0.8 * t)
    else:
        z = lerp(1.0, 1.06, ramp(t, T_TROUT, SECONDS))
        F = (lerp(470, 498, ramp(t, T_TROUT, SECONDS)), 268)
        dx = lerp(-22, 22, ramp(t, T_TROUT, SECONDS))
        dy = 2 * math.sin(0.7 * t)
    return dict(part=part, z=z, F=F, dx=dx, dy=dy)


def cam_M(cam, par):
    cx, cy = CEN[cam["part"]]
    fx, fy = cam["F"]
    return Tm(cx - cam["dx"] * par, cy - cam["dy"] * par) @ Sm(cam["z"] ** par) @ Tm(-(cx + (fx - cx) * par), -(cy + (fy - cy) * par))


def build_water():
    h, w = 760, 1300
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top, bot = np.array([98, 158, 140], np.float32), np.array([20, 62, 70], np.float32)
    a = top[None, None, :] * (1 - yy[..., None] ** 0.8) + bot[None, None, :] * (yy[..., None] ** 0.8)
    a = np.repeat(a, w, axis=1)
    a *= (1 + 0.07 * vnoise((h, w), 420, 9, 91, 3) + 0.05 * vnoise((h, w), 160, None, 92, 2) + 0.03 * fibre_tex()[:h, :np.newaxis].repeat(1, 1)[:, :1].repeat(w, 1))[..., None] if False else (1 + 0.07 * vnoise((h, w), 420, 9, 91, 3) + 0.05 * vnoise((h, w), 160, None, 92, 2))[..., None]
    R["water"] = to_img(a)
    # shafts of light: sheared bands
    hs, ws = 760, 1700
    y, x = np.mgrid[0:hs, 0:ws].astype(np.float32)
    rs = np.random.RandomState(4)
    line = np.interp(np.arange(3000), np.arange(0, 3000, 70), rs.rand(43))
    line = np.clip((line - 0.45) * 3.2, 0, 1)
    sh = line[np.clip((x + 0.52 * y).astype(int), 0, 2999)] * np.clip(1 - y / 620, 0, 1) ** 1.3
    R["shaft"] = Image.fromarray((blur_arr(sh, 7) * 255).astype(np.uint8), "L")


def light_shafts(canvas, t, strength):
    s = R["shaft"]
    o1 = int(140 + 60 * math.sin(t * 0.23) + t * 5)
    o2 = int(380 - t * 7 + 40 * math.sin(t * 0.31))
    a = ImageChops.screen(s.crop((o1, 0, o1 + W, H)), s.crop((o2, 60, o2 + W, 60 + H)).point(lambda v: int(v * 0.6)))
    lay = Image.new("RGBA", (W, H), (206, 236, 214, 0))
    lay.putalpha(a.point(lambda v: int(v * strength)))
    canvas.alpha_composite(lay)


SCN = {}


def build_scene():
    R["trout"] = {"mon": make_trout("rainbow", 1), "p1": make_trout("brown", 21), "p2": make_trout("brook", 41), "p3": make_trout("brown", 61)}
    R["turkey"] = make_turkey()
    R["tin"] = make_tin()
    R["cloth"] = make_cloth()
    R["minnow"] = [make_minnow(k, (38 + k * 3, 80, 80)) for k in range(3)]
    for part in (2, 3):
        rs = random.Random(part * 17)
        it = {1: [], 2: [], 3: [], 4: [], 5: []}
        far, mid, dark = (46, 98, 92), (70, 122, 84), (16, 44, 44)

        def weeds(plane, xs, base, ln, wd, col, lean=0.0):
            for x in xs:
                c = tuple(int(v * rs.uniform(0.85, 1.15)) for v in col)
                L = ln * rs.uniform(0.7, 1.15)
                it[plane].append(("weed", make_blade(rs.randint(0, 9999), L, wd * rs.uniform(0.8, 1.2), c), (x + rs.uniform(-8, 8), base + rs.uniform(-6, 10)),
                                  rs.uniform(0, 6.28), lean + rs.uniform(-7, 7), rs.uniform(0.5, 0.8)))
        if part == 2:
            it[1] += [("spr", make_rock(101, 430, 190, (40, 82, 82), (50, 98, 88)), (120, 250)), ("spr", make_rock(102, 380, 160, (44, 86, 84), (54, 104, 90)), (520, 280))]
            weeds(1, range(250, 740, 44), 420, 230, 16, far)
            it[2] += [("spr", make_rock(103, 220, 120, (62, 92, 84), (92, 126, 78)), (196, 330)), ("spr", make_rock(104, 250, 110, (58, 88, 82), (88, 122, 76)), (610, 345))]
            weeds(2, [246, 268, 292, 318, 652, 676, 704, 730], 455, 300, 22, mid)
            it[3] += [("spr", make_bed(1160, 220, 3), (-100, 398)), ("board",),
                      ("spr", make_rock(105, 130, 62, (70, 98, 86), (104, 134, 76)), (232, 372)), ("spr", make_rock(106, 160, 70, (66, 94, 84), (100, 130, 74)), (612, 372)),
                      ("spr", make_rock(107, 84, 40, (78, 102, 90), (110, 138, 80)), (420, 398))]
            weeds(5, [252, 282, 690, 722], 560, 300, 40, dark)
        else:
            it[1] += [("spr", make_rock(111, 480, 210, (40, 82, 82), (50, 98, 88)), (-120, 230)), ("spr", make_rock(112, 420, 170, (44, 86, 84), (54, 104, 90)), (330, 270)),
                      ("spr", make_rock(113, 460, 230, (38, 80, 80), (48, 96, 86)), (700, 220))]
            weeds(1, range(10, 960, 52), 428, 250, 16, far)
            it[2] += [("spr", make_rock(114, 280, 150, (62, 92, 84), (92, 126, 78)), (-70, 310)), ("spr", make_rock(115, 300, 120, (58, 88, 82), (88, 122, 76)), (560, 350)),
                      ("spr", make_rock(116, 240, 160, (60, 90, 84), (90, 124, 76)), (830, 300))]
            weeds(2, [14, 40, 70, 100, 590, 620, 652, 684, 716, 880, 910, 940], 462, 320, 22, mid)
            it[3] += [("spr", make_bed(1200, 200, 5), (-110, 412)), ("board",),
                      ("spr", make_rock(117, 150, 70, (70, 98, 86), (104, 134, 76)), (34, 386)), ("spr", make_rock(118, 180, 84, (66, 94, 84), (100, 130, 74)), (498, 388)),
                      ("spr", make_rock(119, 90, 44, (78, 102, 90), (110, 138, 80)), (300, 420))]
            it[4] += [("spr", make_bed(1300, 120, 7, (52, 78, 70)), (-160, 496)), ("spr", make_rock(120, 170, 90, (60, 88, 80), (96, 128, 74)), (800, 452))]
            weeds(5, [-34, -8, 962, 990], 600, 430, 46, dark)
            it[5] += [("spr", make_rock(121, 330, 120, (18, 46, 46), (24, 58, 52)), (-200, 480))]
        SCN[part] = it


def draw_item(layer, item, M, t):
    kind = item[0]
    if kind == "spr":
        draw_sprite(layer, item[1], M @ Tm(*item[2]))
    elif kind == "weed":
        _, pup, (x, y), ph, lean, fr = item
        w = 2 * math.pi * fr * 0.5 * t + ph
        pup.draw(layer, {"s0": lean + 4 * math.sin(w), "s1": 9 * math.sin(w - 0.8) + lean * 0.4, "s2": 13 * math.sin(w - 1.6)}, M @ Tm(x, y))


def plane_out(canvas, layer, pl):
    if pl["blur"]:
        layer = layer.convert("RGBa").filter(ImageFilter.GaussianBlur(pl["blur"])).convert("RGBA")
    if pl["sh"]:
        sh = shadow_of(layer.getchannel("A"), pl["sh"][2], pl["sh"][3])
        _clip_paste(canvas, sh, (pl["sh"][0], pl["sh"][1]))
    if pl["haze"]:
        al = layer.getchannel("A")
        layer = Image.blend(layer.convert("RGB"), Image.new("RGB", layer.size, WATER), pl["haze"]).convert("RGBA")
        layer.putalpha(al)
    canvas.alpha_composite(layer)


# -------------------------------------------------- tracks and dynamics ---
F0 = int(T_RIVER * FPS)
TRK = {}        # name -> list over frames of dict


def eo(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def mon_mouth(part, t):
    wp = WIPES[0] if part == 2 else WIPES[1]
    a1, b1, a2, b2 = wp["t"]
    BM = board_M(part)
    if part == 2:
        start, rest, t_in, t_out = (700, 452), (668, 300), T_RIVER + 0.3, 20.4
    else:
        start, rest, t_in, t_out = (452, 452), (196, 424), T_TROUT + 0.2, 29.9
    if t < a1:
        f = ease(t, t_in, a1)
        p = apply(BM, cloth_world(wp, a1))
        return (lerp(start[0], p[0], f), lerp(start[1], p[1], f) - 26 * math.sin(math.pi * f))
    if t <= b2:
        return apply(BM, cloth_world(wp, t))
    f = ease(t, b2 + 0.1, t_out)
    p = apply(BM, cloth_world(wp, b2))
    return (lerp(p[0], rest[0], f), lerp(p[1], rest[1], f) + 3 * math.sin(1.2 * t) * f)


def track(name, t):
    """Root of each puppet at time t: x, y, pitch, scale, flip, plus pose extras."""
    part = 2 if t < T_TROUT else 3
    bob = lambda a, w, ph=0.0: a * math.sin(w * t + ph)  # noqa: E731
    d = dict(wag=10.0, freq=1.5, point=0.0, jaw=0.0, gaze=(0.0, 0.0), flip=1.0, nod=0.0, show=True)
    if name == "mon":
        wp = WIPES[0] if part == 2 else WIPES[1]
        a1, b1, a2, b2 = wp["t"]
        busy = a1 - 0.3 <= t <= b2 + 0.1
        d.update(scale=0.66 if part == 2 else 0.70, pitch=lerp(24, 10, ease(t, b2, b2 + 1.2)), wag=20 if busy else 12, freq=2.6 if busy else 1.5, jaw=5, mouth=mon_mouth(part, t))
        if part == 3:
            d["flip"] = lerp(1, -1, ease(t, 30.0, 30.35))
            d["pitch"] = lerp(24, 16, ease(t, b2, b2 + 1.2))
            d["gaze"] = (2.0 * ramp(t, 30.2, 30.6), -1.5 * ramp(t, 30.2, 30.6))
    elif name == "p1":
        if part == 2:
            e = ease(t, 19.6, 20.5)
            d.update(x=566 - 18 * e + bob(2, 0.8), y=392 - 10 * e + bob(4, 1.1), pitch=14 + 4 * e + bob(2, 0.9), scale=0.62, point=0.92 if t < 19.5 else 1.0, wag=10 + 14 * e * (1 - ease(t, 20.5, 21.5)),
                     gaze=(-1.5, -2.0), jaw=6 * e)
        else:
            e = ease(t, 29.4, 32.6)
            d.update(x=lerp(600, 624, e) + bob(2, 0.8), y=lerp(404, 306, e) + bob(4, 1.1), pitch=lerp(16, 36, e) + bob(2, 0.9), scale=0.66, flip=-1.0, point=ease(t, 31.6, 32.3),
                     wag=10 + 12 * math.sin(math.pi * e), gaze=(-2.0, -2.2), jaw=4)
    elif name == "p2":
        if part == 2:
            e = ease(t, 19.5, 20.6)
            d.update(x=520 + 30 * e + bob(2, 0.7, 1), y=428 + 10 * e + bob(3, 1.3, 2), pitch=8 - 14 * e + bob(2, 1.0), scale=0.52, wag=9 + 16 * math.sin(math.pi * e), jaw=14 * e, gaze=(-2, -1.5), nod=-6 * e)
        else:
            e = eo(ramp(t, 26.9, 27.9))
            d.update(x=506 - 70 * e + bob(2, 0.7, 1), y=432 + 16 * e + bob(3, 1.3, 2), pitch=12 - 2 * e + bob(2, 1.0), scale=0.56, flip=-1.0, wag=9 + 18 * math.sin(math.pi * e), jaw=14 * e, gaze=(-2.2, -2.0),
                     nod=-5 * e)
    elif name == "p3":
        d.update(x=852 + bob(2, 0.6), y=462 + bob(3, 1.0, 1) - 14 * ease(t, 28.5, 30), pitch=26 + bob(2, 0.8), scale=0.42, flip=1.0, gaze=(-1, -2.4), wag=8, show=part == 3)
    elif name == "tin":
        e = eo(ramp(t, T_TROUT - 0.2, 27.8))
        e2 = ease(t, 30.0, 33.0)
        d.update(x=lerp(1210, 768, e) - 22 * e2 + bob(3, 0.5), y=158 + 10 * e + 8 * e2 + bob(5, 0.9), pitch=lerp(-7, -2, e) + bob(1.2, 0.7), scale=0.74, speed=(1 - e) * 1.0 + 0.12, show=part == 3)
    return d


def pendulum(ax, f=1.4, zeta=0.22, gain=0.05, kick=0.0):
    """Damped pendulum (deg) driven by the parent's sideways acceleration, 4 substeps a frame."""
    k = (2 * math.pi * f) ** 2
    c = 2 * zeta * math.sqrt(k)
    th, om = kick, 0.0
    out = []
    dt = 1 / FPS / 4
    for a in ax:
        for _ in range(4):
            om += (-k * th - c * om + gain * k * a) * dt
            th += om * dt
        out.append(th)
    return out


def build_tracks():
    names = ("mon", "p1", "p2", "p3", "tin")
    for nm in names:
        TRK[nm] = {}
    for part, (fa, fb) in ((2, (F0, int(T_TROUT * FPS))), (3, (int(T_TROUT * FPS), NF))):
        for nm in names:
            rows = [track(nm, k / FPS) for k in range(fa, fb)]
            xs = np.array([r["mouth"][0] if "mouth" in r else r["x"] for r in rows])
            ax = np.zeros(len(xs))
            ax[1:-1] = (xs[2:] - 2 * xs[1:-1] + xs[:-2]) * FPS * FPS
            ax = np.clip(ax, -1400, 1400)
            if nm == "tin":
                th1 = pendulum(ax, 0.75, 0.10, 0.045, kick=16.0)
                th2 = pendulum(ax, 1.25, 0.14, 0.07, kick=-10.0)
                wat = pendulum(ax, 1.6, 0.2, 0.06, kick=8.0)
                for r, a, b, c in zip(rows, th1, th2, wat):
                    r["sw"] = (a, b, c)
                # the hook is the last thing still moving: its energy must decay once the tin has stopped
                assert max(abs(v) for v in th1[-24:]) < max(abs(v) for v in th1[:72]) + 1e-6
            else:
                sat = pendulum(ax, 1.5, 0.2, 0.035)
                clo = pendulum(ax, 1.0, 0.3, 0.06)
                for r, a, b in zip(rows, sat, clo):
                    r["sw"] = (a, b)
            for k, r in enumerate(rows):
                TRK[nm][fa + k] = r
    # forward kinematics invariant: a child's hinge stays put in its parent's frame whatever the pose
    P = R["trout"]["mon"]
    ms = P.mats(trout_pose(1.234, wag=30, point=1, jaw=20, satchel=40), root_M(100, 100, 20, 0.7, -1))
    for child in ("tail", "pect", "satchel", "jaw"):
        piv = P.parts[child]["pivot"]
        a, b = apply(ms[child], piv), apply(ms[P.parts[child]["parent"]], piv)
        assert abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6
    # multiplane invariant: nearer planes move more for the same camera shift
    c0, c1 = dict(part=3, z=1.0, F=CEN[3], dx=0, dy=0), dict(part=3, z=1.0, F=CEN[3], dx=10, dy=0)
    sh = [abs(apply(cam_M(c1, PLANES[k]["par"]), (100, 100))[0] - apply(cam_M(c0, PLANES[k]["par"]), (100, 100))[0]) for k in (1, 2, 3, 4, 5)]
    assert all(b > a for a, b in zip(sh, sh[1:]))


def draw_trout(layer, name, t, M_cam):
    k = min(max(int(round(t * FPS)), F0), NF - 1)
    r = TRK[name][k]
    if not r["show"] or abs(r["flip"]) < 0.06:
        return None
    P = R["trout"][name]
    sgn = 1 if r["flip"] >= 0 else -1
    sat = sgn * r["sw"][0] - r["pitch"] * 0.7
    pose = trout_pose(t, r["wag"], r["freq"], hash(name) % 7, r["point"], r["jaw"], r["gaze"], sat, r["nod"])
    if "mouth" in r:
        M0 = root_M(0, 0, r["pitch"], r["scale"], r["flip"])
        m = apply(M0, MOUTH)
        M = Tm(r["mouth"][0] - m[0], r["mouth"][1] - m[1]) @ M0
    else:
        M = root_M(r["x"], r["y"], r["pitch"], r["scale"], r["flip"])
    ms = P.draw(layer, pose, M_cam @ M)
    if name == "mon":
        cl = sgn * r["sw"][1] - r["pitch"] * 0.8 + 14 * math.sin(t * 9) * (1 if r["wag"] > 15 else 0.15)
        draw_sprite(layer, R["cloth"], ms["jaw"] @ Tm(*MOUTH) @ Rm(cl) @ Sm(1.25))
    return ms


def draw_tin(layer, t, M_cam, cam):
    k = min(max(int(round(t * FPS)), F0), NF - 1)
    r = TRK["tin"][k]
    if not r["show"]:
        return
    lean = 9 * ease(t, 28.2, 29.6)
    tp = turkey_pose(t, wattle=r["sw"][2] + 6 * math.sin(t * 2.3), snood=-r["sw"][2] * 0.8 + 5 * math.sin(t * 1.9), lean=-lean * 0.8, gaze=(-1.5, 2.0 * ease(t, 28.2, 29.6)))
    win = tin_window(R["turkey"], tp, lean=-lean * 0.6)
    spin = t * 9 * (0.5 + r["speed"] * 2)
    pose = {"chain1": r["sw"][0] + r["pitch"], "chain2": r["sw"][1] * 0.8, "hook": r["sw"][1] * 0.6, "blade": (0.0, 0.0, 0.0, 1.0, math.cos(spin)), "rudder": 5 * math.sin(t * 1.1)}
    R["tin"].draw(layer, pose, M_cam @ Tm(r["x"], r["y"]) @ Rm(r["pitch"]) @ Sm(r["scale"]) @ Tm(-200, -130), sprites={"window": win})


# ----------------------------------------------------------- chalk cloud ---
PUFFS = []


def build_puffs():
    rs = random.Random(12)
    for part, wp in ((2, WIPES[0]), (3, WIPES[1])):
        a1, b1, a2, b2 = wp["t"]
        BM = board_M(part)
        t = a1
        while t < b2:
            if not (b1 < t < a2):
                x, y = apply(BM, cloth_world(wp, t))
                PUFFS.append(dict(part=part, t=t, x=x + rs.uniform(-8, 8), y=y + rs.uniform(-14, 14), vx=rs.uniform(4, 22), vy=rs.uniform(-30, -10), r=rs.uniform(7, 15),
                                  life=rs.uniform(2.2, 4.2), ph=rs.uniform(0, 6.28), a=rs.uniform(0.5, 1.0) * (1.0 if t < b1 else 0.6)))
            t += 0.035


def chalk_cloud(canvas, part, t, M):
    q = 4
    im = Image.new("L", (W // q, H // q), 0)
    d = ImageDraw.Draw(im)
    acc = np.zeros((H // q, W // q), np.float32)
    any_ = False
    for p in PUFFS:
        age = t - p["t"]
        if p["part"] != part or age < 0 or age > p["life"]:
            continue
        any_ = True
        u = age / p["life"]
        x = p["x"] + p["vx"] * age + 6 * math.sin(age * 1.7 + p["ph"])
        y = p["y"] + p["vy"] * (1 - math.exp(-age * 0.8)) / 0.8 + 4 * math.sin(age * 1.3 + p["ph"])
        sx, sy = apply(M, (x, y))
        r = p["r"] * (1 + 2.2 * u) * math.sqrt(abs(M[0, 0]))
        v = p["a"] * (1 - u) ** 1.5 * min(1, age * 6)
        im.paste(0, (0, 0) + im.size)
        d.ellipse([(sx - r) / q, (sy - r) / q, (sx + r) / q, (sy + r) / q], fill=int(255 * min(1, v * 0.5)))
        acc += np.asarray(im, np.float32) / 255
    if not any_:
        return
    a = Image.fromarray((np.clip(1 - np.exp(-acc * 1.1), 0, 1) * 200).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(2.2)).resize((W, H), Image.BICUBIC)
    lay = Image.new("RGBA", (W, H), (232, 236, 224, 0))
    lay.putalpha(a)
    canvas.alpha_composite(lay)


def specks(canvas, t, M, seed, n, alpha):
    d = ImageDraw.Draw(canvas, "RGBA")
    rs = random.Random(seed)
    for _ in range(n):
        x0, y0, ph, sp = rs.uniform(-100, 1060), rs.uniform(0, 540), rs.uniform(0, 6.28), rs.uniform(3, 10)
        x = (x0 + sp * t * 1.5 + 8 * math.sin(t * 0.6 + ph)) % 1160 - 100
        y = (y0 - sp * t * 0.4 + 5 * math.sin(t * 0.8 + ph)) % 540
        sx, sy = apply(M, (x, y))
        r = rs.uniform(0.6, 1.6)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(220, 236, 220, int(alpha * rs.uniform(0.4, 1))))


def bubbles(canvas, t, M, src, seed, rate=5.0):
    """Rings of air rising from a point that moves (src(t) -> stage xy)."""
    d = ImageDraw.Draw(canvas, "RGBA")
    k0 = int(t * rate)
    for k in range(k0 - int(3.2 * rate), k0 + 1):
        rs = random.Random(seed * 1000 + k)
        tb = k / rate + rs.uniform(0, 0.15)
        age = t - tb
        if age < 0 or age > 3.0 or tb < T_RIVER:
            continue
        p = src(tb)
        if p is None:
            continue
        x = p[0] + rs.uniform(-6, 6) + 7 * math.sin(age * 3 + k)
        y = p[1] - 26 * age - 14 * age * age
        r = rs.uniform(1.6, 4.6) * (1 + 0.2 * age)
        sx, sy = apply(M, (x, y))
        a = int(190 * (1 - age / 3.0))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(214, 238, 226, a), width=1)
        d.ellipse([sx - r * 0.5, sy - r * 0.6, sx - r * 0.1, sy - r * 0.2], fill=(240, 250, 244, a))


# ------------------------------------------------------------ river scene ---
def river_scene(part, t):
    cam = camera(part, t)
    cx, cy = CEN[part]
    wb = R["water"]
    ox, oy = int(170 + cam["dx"] * 0.08 + (cam["F"][0] - cx) * 0.08), int(110 + (cam["F"][1] - cy) * 0.08)
    canvas = wb.crop((ox, oy, ox + W, oy + H)).convert("RGBA")
    it = SCN[part]
    for pk in (1, 2, 3, 4, 5):
        pl = PLANES[pk]
        M = cam_M(cam, pl["par"])
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if pk == 1:      # a far school crossing
            for k in range(9):
                x = (980 - (t - T_RIVER) * 16 - k * 37 - (k % 3) * 22) % 1300 - 160
                y = 120 + 30 * math.sin(k * 1.9) + 6 * math.sin(t * 1.2 + k)
                draw_sprite(layer, R["minnow"][k % 3], M @ Tm(x, y) @ Rm(4 * math.sin(t * 5 + k)) @ Sm(0.9), shadow=None)
        for item in it[pk]:
            if item[0] == "board":
                b = BOARD[part]
                bw = b["w"] * M[0, 0]
                img = board_img(t).resize((int(bw), int(bw * BH / BW)), Image.LANCZOS).convert("RGBA")
                spr = Sprite(img, 0, 0)
                Mb = M @ Tm(*b["c"]) @ Rm(b["rot"]) @ Sm(1 / M[0, 0]) @ Tm(-img.size[0] / 2, -img.size[1] / 2)
                draw_sprite(layer, spr, Mb, shadow=(6, 9, 7, 0.45))
            else:
                draw_item(layer, item, M, t)
        if pk == 3:
            draw_trout(layer, "mon", t, M)
            if part == 3:
                draw_tin(layer, t, M, cam)
        if pk == 4:
            for nm in ("p2", "p3", "p1"):
                draw_trout(layer, nm, t, M)
        plane_out(canvas, layer, pl)
        if pk == 1:
            light_shafts(canvas, t, 0.30)
        if pk == 2:
            specks(canvas, t, M, 5, 50, 90)
        if pk == 3:
            chalk_cloud(canvas, part, t, cam_M(cam, 1.06))
            if part == 3:
                r = TRK["tin"]
                bubbles(canvas, t, M, lambda tb: (TRK["tin"][min(NF - 1, max(F0, int(tb * FPS)))]["x"] + 180, TRK["tin"][min(NF - 1, max(F0, int(tb * FPS)))]["y"]) if tb >= T_TROUT else None, 3, 7.0)
        if pk == 4:
            specks(canvas, t, M, 8, 40, 130)
            light_shafts(canvas, t, 0.10)
    return canvas


# ------------------------------------------------- inside the tin (part 2) ---
GC, GR, GRO = (480, 262), 225, 274


def build_port():
    """The inside wall of the tin and the brass ring of its one porthole, six bolts, hinge and dog."""
    S = 2
    w, h = W * S, H * S
    cx, cy = GC[0] * S, GC[1] * S
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx - cx, yy - cy) / S
    th = np.arctan2(yy - cy, xx - cx)
    # wall: tinned sheet seen from inside, pressed ribs, solder and rust
    rib = np.sin(yy / S / 46 * 2 * math.pi)
    wall = np.array([64, 68, 66], np.float32)[None, None, :] * (1 + 0.20 * rib + 0.10 * vnoise((h, w), 500, 4, 201, 2) + 0.08 * vnoise((h, w), 90, None, 202, 2))[..., None]
    rust = np.clip(vnoise((h, w), 150, None, 203, 3) - 0.3, 0, 1)
    wall += rust[..., None] * np.array([70, 26, -6], np.float32)
    lamp = np.clip(1.25 - np.hypot((xx / S - 880) / 620, (yy / S - 40) / 520), 0.35, 1.2)
    wall *= lamp[..., None] * np.array([1.08, 0.98, 0.84], np.float32)
    wall *= np.clip((r - GRO) / 40, 0.45, 1)[..., None]            # the ring's own shadow on the wall
    # ring
    u = np.clip((r - GR) / (GRO - GR), 0, 1)
    prof = smooth_arr(u / 0.22) * smooth_arr((1 - u) / 0.2)
    dpr = np.gradient(prof, axis=1) * np.cos(th) + np.gradient(prof, axis=0) * np.sin(th)       # radial slope (per px)
    dpr = dpr * (GRO - GR) * S / 7.0
    Lx, Ly = -0.64, -0.77
    lam = -dpr * (np.cos(th) * Lx + np.sin(th) * Ly)
    brush = vnoise((h, w), 3, None, 204)       # replaced below by a polar-brushed field
    pol = vnoise((700, 2400), 60, 1.6, 205, 2)
    brush = pol[np.clip(((r - GR + 20) * 6).astype(int), 0, 699), ((th + math.pi) / (2 * math.pi) * 2399).astype(int)]
    tarn = vnoise((h, w), 120, None, 206, 3)
    brass = np.array([192, 150, 70], np.float32)[None, None, :] * (0.80 + 0.75 * lam + 0.10 * brush + 0.10 * tarn)[..., None]
    brass += np.clip(lam, 0, 1)[..., None] ** 3 * 150
    brass += np.clip(-tarn - 0.25, 0, 1)[..., None] * np.array([-40, 10, 10], np.float32)
    gasket = (u < 0.07)
    brass[gasket] = np.array([26, 24, 22], np.float32)
    ring = ((r >= GR) & (r <= GRO)).astype(np.float32)
    ring_soft = np.clip((r - GR) * S + 0.5, 0, 1) * np.clip((GRO - r) * S + 0.5, 0, 1)
    img = wall * (1 - ring_soft[..., None]) + brass * ring_soft[..., None]
    alpha = np.clip((r - GR) * S + 0.5, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(img, 0, 255), alpha * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    # hinge (left) and dog (right): iron and brass, behind the bolts
    hx = cx - (GRO + 4) * S
    d.rounded_rectangle([hx - 60 * S, cy - 58 * S, hx + 26 * S, cy + 58 * S], 6 * S, fill=(40, 40, 42, 255), outline=(18, 18, 20, 255), width=2 * S)
    d.rounded_rectangle([hx - 6 * S, cy - 70 * S, hx + 8 * S, cy + 70 * S], 6 * S, fill=(70, 70, 72, 255), outline=(18, 18, 20, 255), width=2 * S)
    d.line([hx - 2 * S, cy - 64 * S, hx - 2 * S, cy + 64 * S], fill=(120, 122, 120, 255), width=2 * S)
    for yy_ in (-40, 0, 40):
        d.ellipse([hx - 44 * S, cy + (yy_ - 7) * S, hx - 30 * S, cy + (yy_ + 7) * S], fill=(84, 84, 86, 255), outline=(14, 14, 16, 255), width=S)
        d.line([hx - 41 * S, cy + (yy_ - 3) * S, hx - 33 * S, cy + (yy_ + 3) * S], fill=(20, 20, 22, 255), width=S)
    lx = cx + (GRO - 6) * S
    d.rounded_rectangle([lx, cy - 22 * S, lx + 74 * S, cy + 22 * S], 8 * S, fill=(176, 138, 62, 255), outline=(70, 50, 20, 255), width=2 * S)
    d.line([lx + 6 * S, cy - 16 * S, lx + 66 * S, cy - 16 * S], fill=(232, 204, 130, 255), width=2 * S)
    d.ellipse([lx + 34 * S, cy - 30 * S, lx + 94 * S, cy + 30 * S], fill=(150, 116, 50, 255), outline=(60, 44, 18, 255), width=2 * S)
    d.ellipse([lx + 42 * S, cy - 22 * S, lx + 86 * S, cy + 22 * S], fill=(198, 160, 80, 255), outline=(232, 204, 130, 255), width=S)
    d.rounded_rectangle([lx + 58 * S, cy - 44 * S, lx + 70 * S, cy + 44 * S], 5 * S, fill=(184, 146, 68, 255), outline=(60, 44, 18, 255), width=2 * S)
    # six hex bolts
    rb = (GR + GRO) / 2 + 2
    for k in range(6):
        a = math.radians(90 + 60 * k)
        bx, by = cx + rb * S * math.cos(a), cy + rb * S * math.sin(a)
        d.ellipse([bx - 15 * S + 5 * S, by - 15 * S + 7 * S, bx + 17 * S + 5 * S, by + 17 * S + 7 * S], fill=(30, 22, 8, 110))
        hexp = [(bx + 16 * S * math.cos(math.radians(60 * j + 11 * k)), by + 16 * S * math.sin(math.radians(60 * j + 11 * k))) for j in range(6)]
        d.polygon(hexp, fill=(150, 114, 48, 255), outline=(60, 42, 14, 255))
        for j in range(6):
            aj = math.radians(60 * j + 11 * k + 30)
            lit = max(0.0, -(math.cos(aj) * 0.64 + math.sin(aj) * 0.77))
            c = tuple(int(v * (0.62 + 0.7 * lit)) for v in (198, 158, 76)) + (255,)
            d.polygon([hexp[j], hexp[(j + 1) % 6], (bx + 10.5 * S * math.cos(math.radians(60 * (j + 1) + 11 * k)), by + 10.5 * S * math.sin(math.radians(60 * (j + 1) + 11 * k))),
                       (bx + 10.5 * S * math.cos(math.radians(60 * j + 11 * k)), by + 10.5 * S * math.sin(math.radians(60 * j + 11 * k)))], fill=c)
        d.polygon([(bx + 10.5 * S * math.cos(math.radians(60 * j + 11 * k)), by + 10.5 * S * math.sin(math.radians(60 * j + 11 * k))) for j in range(6)], fill=(206, 168, 86, 255))
        d.arc([bx - 8 * S, by - 8 * S, bx + 8 * S, by + 8 * S], 180, 300, fill=(244, 222, 160, 255), width=2 * S)
    # a depth gauge on the wall
    gx, gy, gr = 862 * S, 170 * S, 50 * S
    d.ellipse([gx - gr + 6 * S, gy - gr + 9 * S, gx + gr + 6 * S, gy + gr + 9 * S], fill=(10, 8, 6, 120))
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(168, 130, 60, 255), outline=(66, 46, 18, 255), width=2 * S)
    d.ellipse([gx - gr + 8 * S, gy - gr + 8 * S, gx + gr - 8 * S, gy + gr - 8 * S], fill=(226, 218, 190, 255), outline=(90, 66, 30, 255), width=S)
    for k in range(13):
        a = math.radians(150 + k * 20)
        r0 = gr - (20 if k % 3 == 0 else 15) * S
        d.line([gx + r0 * math.cos(a), gy + r0 * math.sin(a), gx + (gr - 11 * S) * math.cos(a), gy + (gr - 11 * S) * math.sin(a)], fill=(50, 40, 30, 255), width=(2 if k % 3 == 0 else 1) * S)
    d.text((gx, gy + 20 * S), "FATHOMS", font=font("mono", 7 * S), fill=(70, 56, 40, 255), anchor="mm")
    # rivets along the wall seams
    for x in list(range(30, 200, 42)) + list(range(790, 960, 42)):
        for y in (20, 520):
            d.ellipse([(x - 5) * S, (y - 5) * S, (x + 5) * S, (y + 5) * S], fill=(96, 100, 98, 255), outline=(30, 32, 32, 255), width=S)
            d.arc([(x - 4) * S, (y - 4) * S, (x + 4) * S, (y + 4) * S], 180, 290, fill=(180, 184, 180, 255), width=S)
    im = im.resize((W, H), Image.LANCZOS)
    a = np.asarray(im, np.float32).copy()
    a[..., :3] *= (1 + 0.035 * vnoise((H, W), 1.5, None, 207))[..., None]
    R["port"] = to_img(a).convert("RGBA")
    # glass: thick edge, a long highlight
    y2, x2 = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.hypot(x2 - GC[0], y2 - GC[1])
    edge = np.clip((rr - GR * 0.80) / (GR * 0.20), 0, 1) ** 2 * 0.62
    g = np.zeros((H, W, 4), np.float32)
    g[..., :3] = np.array([10, 30, 30], np.float32)
    g[..., 3] = edge * 255
    gl = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA")
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.arc([GC[0] - GR + 22, GC[1] - GR + 22, GC[0] + GR - 22, GC[1] + GR - 22], 200, 255, fill=(255, 255, 248, 105), width=9)
    hd.arc([GC[0] - GR + 44, GC[1] - GR + 44, GC[0] + GR - 44, GC[1] + GR - 44], 208, 232, fill=(255, 255, 248, 60), width=5)
    hd.arc([GC[0] - GR + 20, GC[1] - GR + 20, GC[0] + GR - 20, GC[1] + GR - 20], 28, 58, fill=(255, 255, 248, 40), width=6)
    gl.alpha_composite(hl.filter(ImageFilter.GaussianBlur(2.5)))
    R["glass"] = gl
    m = Image.new("L", (W * 2, H * 2), 0)
    ImageDraw.Draw(m).ellipse([(GC[0] - GR - 1) * 2, (GC[1] - GR - 1) * 2, (GC[0] + GR + 1) * 2, (GC[1] + GR + 1) * 2], fill=255)
    R["gmask"] = m.resize((W, H), Image.LANCZOS)


def smooth_arr(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def turkey_front(t):
    """Turkey at the glass, seen from behind its shoulder: a dark, soft, near shape."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sway = 5 * math.sin(t * 0.9)
    lean = 6 * ease(t, 17.0, 18.5) + 2 * math.sin(t * 0.6)
    pose = turkey_pose(t, wattle=10 * math.sin(t * 1.7 + 1) + sway, snood=8 * math.sin(t * 1.4), lean=-lean, gaze=(1.5, -0.5))
    M = Tm(120 + lean * 2.5, 470 + 4 * math.sin(t * 1.1)) @ Sm(-2.5, 2.5) @ Tm(-128, -140)
    R["turkey"].draw(lay, pose, M)
    a = np.asarray(lay, np.float32).copy()
    a[..., :3] = a[..., :3] * np.array([0.26, 0.21, 0.21], np.float32) + np.array([3, 8, 9], np.float32)
    return to_img(a).convert("RGBa").filter(ImageFilter.GaussianBlur(2.4)).convert("RGBA")


def turkey_reflection(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pose = turkey_pose(t, wattle=8 * math.sin(t * 1.7 + 1), snood=6 * math.sin(t * 1.4), lean=0, gaze=(-1.5, -0.5))
    R["turkey"].draw(lay, pose, Tm(360, 420 + 3 * math.sin(t * 1.1)) @ Sm(1.25) @ Tm(-128, -140))
    lay = lay.filter(ImageFilter.GaussianBlur(1.6))
    lay.putalpha(ImageChops.multiply(lay.getchannel("A").point(lambda v: int(v * 0.16)), R["gmask"]))
    return lay


def caption(ink, s, t, a, b):
    al = min(ramp(t, a, a + 0.35), 1 - ramp(t, b - 0.35, b))
    if al > 0:
        ink.caption(s, alpha=al, size=25)


CAP2 = "Mister Hook, the famous guest speaker? Or the Monster, most wanted?"
CAP3 = "OK, mister: are you our new class pet? Or the Hook Monster?"


def river_frame(t, ink):
    if t < T_TROUT:
        scene = river_scene(2, t)
        out = R["port"].copy()
        base = Image.new("RGBA", (W, H), (20, 40, 40, 255))
        scene.alpha_composite(R["glass"])
        scene.alpha_composite(turkey_reflection(t))
        base.paste(scene, (0, 0), R["gmask"])
        base.alpha_composite(out)
        base.alpha_composite(turkey_front(t))
        ink.img = base.convert("RGB")
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        na = math.radians(196 + 4 * math.sin(t * 2.1) + 2 * math.sin(t * 7.3) + 10 * ease(t, T_RIVER, 17.5))
        ink.d.line([862 - 8 * math.cos(na), 170 - 8 * math.sin(na), 862 + 30 * math.cos(na), 170 + 30 * math.sin(na)], fill=(120, 30, 26, 255), width=3)
        ink.d.ellipse([858, 166, 866, 174], fill=(60, 44, 20, 255))
        caption(ink, CAP2, t, 19.7, 24.3)
    else:
        scene = river_scene(3, t)
        ink.img = scene.convert("RGB")
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        ink.vignette(0.3)
        caption(ink, CAP3, t, 28.9, 33.7)
    # soft joins
    f = max(1 - ramp(t, T_RIVER, T_RIVER + 0.3), 0) if t < T_TROUT else max(1 - ramp(t, T_TROUT, T_TROUT + 0.25), 0)
    if f > 0:
        ink.d.rectangle([0, 0, W, H], fill=(8, 14, 16, int(255 * f)))


def build_river():
    build_wipes()
    build_water()
    build_scene()
    build_tracks()
    build_puffs()
    build_port()


def picture(t, ink):
    if t < T_RIVER:
        bench_frame(t, ink)
    else:
        river_frame(t, ink)


def chalk_events():
    """Cut the foraged chalk recording into its own strokes (onset to next onset)."""
    f = SRC / "chalk.ogg"
    if not f.exists():
        return []
    a = KA.load_audio(f)
    n = RATE // 100
    rms = np.sqrt(np.convolve(a * a, np.ones(n) / n, "same"))[::n]
    ev, quiet = [], 10
    for k in range(len(rms)):
        if rms[k] > 0.035 and quiet >= 5:
            ev.append(k * n)
            quiet = 0
        elif rms[k] < 0.014:
            quiet += 1
    out = []
    for k, on in enumerate(ev):
        end = min(ev[k + 1] if k + 1 < len(ev) else len(a), on + int(0.55 * RATE))
        seg = a[max(0, on - 300):end].copy()
        if len(seg) < 0.08 * RATE:
            continue
        seg /= (np.abs(seg).max() + 1e-9)
        out.append(seg)
    return out


def sound(mix):
    rs = np.random.RandomState(7)
    # ---- the bench
    mix.room(0, T_RIVER + 0.2, gain=0.012)
    sl = mix.band(mix.noise(0.75), 120, 1500) * np.hanning(int(0.75 * RATE)) ** 0.5
    mix.add(sl, 0.0, 0.10, -0.4)
    mix.thud(0.70, 58, 0.40, -0.1)
    for k, (t0, _) in RAIL_T.items():
        mix.whoosh(t0, 0.4, 0.035, {"left": -0.6, "right": 0.6}.get(k, 0.0))
        mix.thud(t0 + 0.41, 110 + 20 * rs.rand(), 0.32, {"left": -0.6, "right": 0.6}.get(k, 0.0), 0.22)
        mix.step(t0 + 0.42, 0.34, {"left": -0.6, "right": 0.6}.get(k, 0.0), "wood")
    mix.click(3.26, 0.22, 0.0, 8000, 0.02)
    mix.bell(3.26, 2600, 0.35, 0.035)
    mix.click(3.08, 0.10, 0.6, 5000, 0.02)
    ev = chalk_events()
    for k, s in enumerate(STROKES):
        dur = s["t1"] - s["t0"]
        pan = clamp((s["pts"][0][0] - WW / 2) / 900, -0.6, 0.6)
        if ev:
            parts = [(s["t0"] - 0.008, 1.0)] + ([(s["t0"] + dur * 0.55, 0.55)] if dur > 0.27 else [])
            for j, (at, g) in enumerate(parts):
                seg = ev[(k * 2 + j * 7) % len(ev)]
                m = min(len(seg), int((dur * (1.0 if not j else 0.5) + 0.20) * RATE))
                seg = seg[:m] * np.linspace(1, 0, m) ** 0.6
                mix.add(seg, at, 0.42 * g * (0.8 if s["width"] < 12 else 1.0), pan)
        else:
            m = int((dur + 0.05) * RATE)
            x = mix.band(mix.noise(dur + 0.05), 1800, 7000) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 43 * mix.t(dur + 0.05)))) * np.hanning(m) ** 0.4
            mix.add(x, s["t0"], 0.10, pan)
            mix.click(s["t0"], 0.14, pan, 6000)
    mix.click(15.02, 0.16, 0.6, 3500, 0.03)
    # ---- the river, heard through the tin and then from the water
    mix.bell(T_RIVER + 0.05, 392, 3.2, 0.13)
    n = SECONDS - T_RIVER
    bed = mix.lowpass(mix.noise(n, "brown"), 420) * mix.env(int(n * RATE), 0.5, 0.01, 1.0, 1.2)
    mix.add(bed, T_RIVER, 0.16)
    mix.water(T_TROUT, SECONDS - T_TROUT, 0.035)
    mix.drone(T_RIVER, T_TROUT - T_RIVER + 0.4, (49, 73.5, 98), 0.07, 0.0, 0.6, 0.8)
    mix.drone(T_TROUT, SECONDS - T_TROUT, (55, 82.5, 123.5), 0.045, 0.0, 0.8, 1.5)
    # the tin's screw: a putter that slows as it comes to rest
    t = T_RIVER
    while t < SECONDS - 0.3:
        if t < T_TROUT:
            g, step = 0.10, 0.105
        else:
            sp = TRK["tin"][min(NF - 1, int(t * FPS))]["speed"]
            g, step = 0.05 + 0.11 * sp, 0.20 - 0.10 * sp
        mix.thud(t, 82, g, 0.0 if t < T_TROUT else 0.5, 0.12)
        t += step
    # the wet cloth on slate
    for part, wp in ((2, WIPES[0]), (3, WIPES[1])):
        a1, b1, a2, b2 = wp["t"]
        for (a, b, g) in ((a1, b1, 1.0), (a2, b2, 0.75)):
            d = b - a
            tt = mix.t(d)
            x = mix.band(mix.noise(d), 500, 2600) * (0.25 + 0.75 * np.abs(np.sin(2 * np.pi * 2.4 * tt))) * np.hanning(len(tt)) ** 0.3
            sq = np.sin(2 * np.pi * np.cumsum(880 + 260 * np.sin(2 * np.pi * 4.8 * tt)) / RATE) * np.abs(np.sin(2 * np.pi * 2.4 * tt)) ** 6
            mix.add(x * 0.9 + sq * 0.10, a, 0.085 * g, -0.2 if part == 3 else 0.0)
    # air: the class gasps in bubbles
    for (t0, cnt, pan) in ((19.6, 9, 0.2), (27.0, 11, 0.1), (31.8, 6, 0.2), (25.2, 5, 0.5)):
        for k in range(cnt):
            tb = t0 + k * 0.09 + rs.uniform(0, 0.05)
            f0 = rs.uniform(500, 1100)
            tt = mix.t(0.07)
            mix.add(np.sin(2 * np.pi * (f0 + 5000 * tt) * tt) * np.exp(-tt * 45), tb, 0.06, pan + rs.uniform(-0.2, 0.2))
    # the chain settles
    for t0 in (27.9, 28.6, 29.5):
        mix.click(t0, 0.05, 0.4, 6500, 0.015)
    # the questions arrive on two plucked notes
    for (t0, fa, fb) in ((19.7, 196.0, 261.6), (28.9, 174.6, 233.1)):
        mix.pluck(t0, fa, 1.6, 0.10, -0.1)
        mix.pluck(t0 + 0.28, fb, 1.8, 0.09, 0.1)
    mix.reverb(0.10, 0.8)


def main():
    build_strokes()
    build_chalk()
    build_bench()
    build_cam()
    build_river()
    film = Film(SLUG, SECONDS, boil=0, wobble=0.6, seed=3)
    film.poster_at = 13.9
    film.picture(picture)
    film.sound(sound)
    KA.run(film)


if __name__ == "__main__":
    main()
