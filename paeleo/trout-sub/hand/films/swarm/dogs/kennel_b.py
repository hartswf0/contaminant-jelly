"""KENNEL B · the rest of the pack for THE DOGS OF TROUTTOWN.

Four makes of dog, each built by a different method, each from one animation
SCION read in full:

  retriever()   wooden pull-toy on hinges, parts that settle late   scion/animation-13.md
  sheepdog()    crepe paper on coil springs                         scion/animation-41.md
  bloodhound()  one continuous pencil line, key drawings in-betweened,
                a nose that pays out along a trail                  scion/animation-07.md
  terrier()     small stiff jointed card dog, forward kinematics,
                shot on twos                                        scion/animation-32.md

Every function draws onto a kit.py Ink (or a PIL image) at a place, size and
facing, and returns screen points (mouth, nose, body, bbox ...). Everything is
stateless: the drawing at time t depends only on t, so stills match the film.

    import sys; sys.path.insert(0, "films/swarm/dogs")
    import kennel_b as kb
    kb.retriever(ink, 300, 400, "carry", t, scale=0.8, carry="piece")

Run `python3 films/swarm/dogs/kennel_b.py` to render the sheets and run the
self-test. See KENNEL_B.md.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
TAU = 2 * math.pi
SILHOUETTE = (20, 17, 26)
WATER = (24, 120, 128)          # tint for dogs under the surface, as the lead dog uses

# No cream, no red: those belong to the lead dog alone.
COLORS = {
    # wooden retriever
    "wood": (226, 176, 66), "wood_dark": (150, 96, 44), "wood_far": (150, 112, 52),
    "walnut": (112, 70, 44), "wheel": (58, 84, 140), "wheel_far": (40, 56, 96),
    "hub": (232, 214, 170), "pin": (206, 170, 86), "string": (60, 52, 60), "bead": (70, 150, 150),
    # crepe sheepdog
    "crepe": (128, 142, 168), "crepe_lt": (158, 170, 192), "crepe_dk": (94, 106, 134),
    "white": (236, 240, 240), "white_dk": (198, 206, 214), "steel": (164, 170, 184),
    "steel_far": (104, 110, 128), "foot": (56, 60, 78),
    # pencil bloodhound
    "paper": (238, 234, 224), "graphite": (52, 50, 56),
    # card terrier
    "card": (170, 138, 100), "card_far": (126, 100, 72), "card_edge": (104, 78, 52),
    "flute": (140, 110, 78), "marker": (74, 54, 44),
    # shared
    "nose": (30, 24, 26), "eye": (26, 22, 24), "glint": (255, 250, 236),
    "film": (48, 42, 50), "frame": (236, 228, 206), "reel": (176, 186, 196), "reel_dark": (70, 76, 92),
    "page": (250, 246, 233), "pencil": (120, 104, 150), "crayon": (60, 120, 170), "crayon2": (224, 150, 60),
    "snag": (52, 66, 52), "snag2": (120, 96, 60), "part": (196, 150, 70),
    "bubble": (214, 240, 244),
}


# ------------------------------------------------------------------- maths ---

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, x):
    return a + (b - a) * x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease(t, a, b):
    if b == a:
        return 1.0 if t >= b else 0.0
    return smooth((t - a) / (b - a))


def bell(t, a, b, c, d):
    """0 before a, 1 between b and c, 0 after d."""
    return ease(t, a, b) * (1 - ease(t, c, d))


def _rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def _u(a, r=1.0):
    return (math.cos(a) * r, math.sin(a) * r)


def _h(n):
    """Deterministic hash to 0..1."""
    x = math.sin(n * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def _mix(c1, c2, x):
    return tuple(int(round(lerp(a, b, clamp(x)))) for a, b in zip(c1, c2))


def _arrive(t, v0, tau=0.32):
    """Distance covered by something that was moving at v0 and brakes to a stop from t = 0."""
    if t <= 0:
        return v0 * t
    if t < tau:
        return v0 * (t - t * t / (2 * tau))
    return v0 * tau / 2


def lift(t, start=0.9, top=80.0):
    """Dog units risen by a dog that has run out of breath (breath_out), t seconds in."""
    u = t - start
    if u <= 0:
        return 0.0
    ta = top / 90.0
    return 45.0 * u * u if u < ta else 45.0 * ta * ta + top * (u - ta)


# ----------------------------------------------------------- display list ---

class Sheet:
    """A dog's drawing as a list of shapes in dog units (x forward, y up)."""

    def __init__(self):
        self.ops = []
        self.pts = {}
        self.info = {}

    def poly(self, pts, fill, edge=None, ew=1.0, detail=False):
        self.ops.append(("poly", list(pts), fill, edge, ew, detail))

    def line(self, pts, col, w=1.5, detail=False):
        self.ops.append(("line", list(pts), col, None, w, detail))

    def dot(self, c, r, fill, edge=None, ew=1.0, detail=False):
        self.ops.append(("dot", [c], fill, edge, (r, ew), detail))

    def hole(self, c, r):
        self.ops.append(("hole", [c], None, None, (r, 0), False))

    def mark(self, name, p):
        self.pts[name] = p


def _bar(a, b, wa, wb, chamfer=0.0):
    """A plank from a to b, half-widths wa/2 and wb/2; chamfer > 0 cuts the corners (card)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    ha, hb = wa / 2, wb / 2
    c = chamfer
    if c <= 0:
        return [(a[0] + nx * ha, a[1] + ny * ha), (b[0] + nx * hb, b[1] + ny * hb),
                (b[0] - nx * hb, b[1] - ny * hb), (a[0] - nx * ha, a[1] - ny * ha)]
    return [(a[0] - ux * c * 0.3 + nx * ha * 0.55, a[1] - uy * c * 0.3 + ny * ha * 0.55),
            (a[0] + ux * c + nx * ha, a[1] + uy * c + ny * ha),
            (b[0] - ux * c + nx * hb, b[1] - uy * c + ny * hb),
            (b[0] + ux * c * 0.3 + nx * hb * 0.55, b[1] + uy * c * 0.3 + ny * hb * 0.55),
            (b[0] + ux * c * 0.3 - nx * hb * 0.55, b[1] + uy * c * 0.3 - ny * hb * 0.55),
            (b[0] - ux * c - nx * hb, b[1] - uy * c - ny * hb),
            (a[0] + ux * c - nx * ha, a[1] + uy * c - ny * ha),
            (a[0] - ux * c * 0.3 - nx * ha * 0.55, a[1] - uy * c * 0.3 - ny * ha * 0.55)]


def _round(c, rx, ry, n=18, a=0.0, wob=0.0, seed=0):
    out = []
    for i in range(n):
        th = TAU * i / n
        k = 1 + wob * (_h(seed * 31 + i) - 0.5)
        out.append(_add(c, _rot((rx * k * math.cos(th), ry * k * math.sin(th)), a)))
    return out


_tex_cache = {}


def _texture(material):
    """256x256 multiplicative grain per material."""
    if material not in _tex_cache:
        rs = np.random.RandomState({"wood": 3, "crepe": 5, "pencil": 7, "card": 9}.get(material, 1))
        g = rs.normal(0, 1, (256, 256)).astype(np.float32)
        fine = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 128 - 1
        xx = np.arange(256, dtype=np.float32)[None, :]
        yy = np.arange(256, dtype=np.float32)[:, None]
        if material == "wood":      # long grain
            tex = 1 + 0.045 * np.sin(yy * 0.85 + 3.0 * np.sin(xx * 0.045 + yy * 0.02)) + fine * 0.10
        elif material == "crepe":   # fine crinkle across the strips
            tex = 1 + 0.07 * np.sin(yy * 1.9 + 1.5 * np.sin(xx * 0.3)) + fine * 0.16
        elif material == "card":    # flutes showing through the liner
            tex = 1 + 0.05 * np.sin(xx * 1.55) + fine * 0.14
        else:                       # paper tooth under graphite
            tex = 1 + fine * 0.22
        _tex_cache[material] = tex.clip(0.82, 1.1)
    return _tex_cache[material]


def _composite(img, spr, ox, oy):
    if img.mode == "RGBA":
        box = (max(0, ox), max(0, oy), min(img.width, ox + spr.width), min(img.height, oy + spr.height))
        if box[2] <= box[0] or box[3] <= box[1]:
            return
        crop = spr.crop((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy))
        region = img.crop(box)
        region.alpha_composite(crop)
        img.paste(region, box[:2])
    else:
        img.paste(spr, (ox, oy), spr)


_RENDER_KEYS = ("silhouette", "color", "tint", "tint_amount", "alpha", "shadow", "rot", "clip", "ss")


def _split(kw):
    return {k: kw.pop(k) for k in _RENDER_KEYS if k in kw}


def _render(target, sheet, x, y, scale, facing, origin=(0.0, 0.0), material=None, silhouette=False, color=None,
            tint=None, tint_amount=0.0, alpha=1.0, shadow=None, rot=0.0, clip=None, ss=3):
    """Rasterise a Sheet, supersampled, and composite it. Returns the screen transform."""
    img = target.img if hasattr(target, "img") else target
    f = clamp(float(facing), -1.0, 1.0)
    if abs(f) < 0.06:
        f = 0.06 if f >= 0 else -0.06
    ca, sa = math.cos(rot), math.sin(rot)
    ox0, oy0 = origin

    def T(p):
        px, py = p[0] - ox0, p[1] - oy0
        return (x + f * scale * (px * ca - py * sa), y - scale * (px * sa + py * ca))

    if not sheet.ops:
        return T, (x, y, x, y)
    sil = color or SILHOUETTE
    if shadow is None:
        shadow = not silhouette
    ops = []
    xs, ys = [], []
    for kind, pts, fill, edge, w, detail in sheet.ops:
        if silhouette and detail:
            continue
        tp = [T(p) for p in pts]
        if kind == "dot":
            r = w[0] * scale
            xs += [tp[0][0] - r, tp[0][0] + r]
            ys += [tp[0][1] - r, tp[0][1] + r]
        elif kind == "hole":
            pass
        else:
            xs += [p[0] for p in tp]
            ys += [p[1] for p in tp]
        ops.append((kind, tp, fill, edge, w, detail))
    if not xs:
        return T, (x, y, x, y)
    pad = int(6 + 4 * scale)
    ox, oy = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    w_, h_ = int(math.ceil(max(xs))) - ox + pad, int(math.ceil(max(ys))) - oy + pad
    w_, h_ = min(w_, 4000), min(h_, 4000)
    spr = Image.new("RGBA", (w_ * ss, h_ * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)

    def C(c):
        if c is None:
            return None
        a = c[3] if len(c) == 4 else 255
        if silhouette:
            return tuple(sil) + (255,)
        c3 = tuple(c[:3])
        if tint is not None and tint_amount > 0:
            c3 = _mix(c3, tint, tint_amount)
        return c3 + (a,)

    def S(tp):
        return [((px - ox) * ss, (py - oy) * ss) for px, py in tp]

    for kind, tp, fill, edge, w, detail in ops:
        sp = S(tp)
        if kind == "poly":
            if fill is not None and len(sp) >= 3:
                d.polygon(sp, fill=C(fill))
            if edge is not None and not silhouette:
                d.line(sp + [sp[0]], fill=C(edge), width=max(1, int(round(w * scale * ss))), joint="curve")
        elif kind == "line":
            ww = max(1, int(round(w * scale * ss)))
            if silhouette:
                ww = max(ww, ss + 1)
            col = C(fill)
            if len(sp) >= 2:
                d.line(sp, fill=col, width=ww, joint="curve")
            if ww >= 3:
                r = ww / 2
                for px, py in (sp[0], sp[-1]):
                    d.ellipse([px - r, py - r, px + r, py + r], fill=col)
        elif kind == "dot":
            r = w[0] * scale * ss
            px, py = sp[0]
            d.ellipse([px - r, py - r, px + r, py + r], fill=C(fill),
                      outline=None if (edge is None or silhouette) else C(edge),
                      width=max(1, int(round(w[1] * scale * ss))))
        elif kind == "hole":
            r = w[0] * scale * ss
            px, py = sp[0]
            d.ellipse([px - r, py - r, px + r, py + r], fill=(0, 0, 0, 0))
    spr = spr.resize((w_, h_), Image.LANCZOS)
    if material and not silhouette:
        a = np.asarray(spr, np.float32).copy()
        tex = _texture(material)
        yy = (np.arange(h_) + oy - int(round(y))) % 256
        xx = (np.arange(w_) + ox - int(round(x))) % 256
        a[..., :3] *= tex[np.ix_(yy, xx)][..., None]
        spr = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    if clip is not None:
        x0, y0, x1, y1 = clip
        m = Image.new("L", (w_, h_), 0)
        ImageDraw.Draw(m).rectangle([(-1e5 if x0 is None else x0) - ox, (-1e5 if y0 is None else y0) - oy,
                                     (1e5 if x1 is None else x1) - ox - 1, (1e5 if y1 is None else y1) - oy - 1], fill=255)
        spr.putalpha(ImageChops.multiply(spr.getchannel("A"), m))
    if alpha < 1:
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    if shadow:
        al = spr.getchannel("A")
        off = (int(round(3 * scale)) + 1, int(round(4 * scale)) + 1)
        sh = ImageChops.offset(al, off[0], off[1]).filter(ImageFilter.GaussianBlur(1.2 + 1.6 * scale)).point(lambda v: int(v * 0.34))
        shl = Image.new("RGBA", spr.size, (10, 8, 22, 0))
        shl.putalpha(sh)
        _composite(img, shl, ox, oy)
    _composite(img, spr, ox, oy)
    if hasattr(target, "img") and hasattr(target, "d"):
        target.d = ImageDraw.Draw(target.img, "RGBA")
    return T, (ox + pad, oy + pad, ox + w_ - pad, oy + h_ - pad)


def _finish(target, sh, x, y, scale, facing, origin, material, R):
    T, bbox = _render(target, sh, x, y, scale, facing, origin=origin, material=material, **R)
    out = {k: T(v) for k, v in sh.pts.items()}
    out["bbox"] = bbox
    out.update(sh.info)
    return out


# ----------------------------------------------------- things in the mouth ---
THING_HALF = {"piece": (13.0, 16.0), "reel": (19.5, 19.5), "page": (13.0, 16.5), "fix": (11.0, 9.0), "part": (12.5, 12.5)}


def _thing(sh, kind, c, ang=0.0, s=1.0):
    """Draw a carried thing centred on c (dog units), tilted by ang."""
    K = COLORS

    def P(px, py):
        return _add(c, _rot((px * s, py * s), ang))

    if kind == "piece":         # one frame of film, the size of a book
        sh.poly([P(-13, -16), P(13, -16), P(13, 16), P(-13, 16)], K["film"], _mix(K["film"], (0, 0, 0), 0.4), 0.8)
        sh.poly([P(-7.5, -12), P(7.5, -12), P(7.5, 12), P(-7.5, 12)], K["frame"], None, 0, True)
        for i in range(5):
            yy = -12.5 + i * 6.2
            for xx in (-10.6, 10.6):
                sh.poly([P(xx - 1.4, yy - 1.6), P(xx + 1.4, yy - 1.6), P(xx + 1.4, yy + 1.6), P(xx - 1.4, yy + 1.6)], K["frame"], None, 0, True)
        # a child's drawing: a fish and a bell, in crayon
        sh.line([P(-5, 3), P(-1, 6), P(4, 3), P(-1, 0.5), P(-5, 3), P(-6.5, 5.5), P(-6.5, 0.8), P(-5, 3)], K["crayon"], 1.1 * s, True)
        sh.line([P(-2, -8), P(0, -3.5), P(2.5, -8), P(-2, -8)], K["crayon2"], 1.1 * s, True)
    elif kind == "reel":
        sh.poly([P(-3, -17), P(3, -18), P(5, -33), P(-1, -34)], K["film"], None)
        sh.poly(_round(c, 19.5 * s, 19.5 * s, 24), K["reel"], _mix(K["reel"], (30, 30, 50), 0.5), 0.9)
        for i in range(5):
            sh.hole(P(10.5 * math.cos(TAU * i / 5 + 0.3), 10.5 * math.sin(TAU * i / 5 + 0.3)), 4.3 * s)
        sh.dot(c, 3.4 * s, K["reel_dark"], None, 0, True)
    elif kind == "page":
        sh.poly([P(-13, -16.5), P(14, -16), P(13, 16.5), P(-12, 17), P(-14, 1)], K["page"], _mix(K["page"], (60, 50, 40), 0.35), 0.7)
        sh.line([P(-8, 9), P(8, 10)], K["pencil"], 1.3 * s, True)
        sh.line([P(-8, 3.5), P(5, 4.2)], K["pencil"], 1.3 * s, True)
        sh.poly(_round(P(0, -6), 5.5 * s, 4.2 * s, 9), K["crayon2"], None, 0, True)
    elif kind == "part":
        pts = []
        for i in range(28):
            th = TAU * i / 28 + ang
            rr = (12.5 if i % 4 in (0, 1) else 9.5) * s
            pts.append((c[0] + math.cos(th) * rr, c[1] + math.sin(th) * rr))
        sh.poly(pts, K["part"], _mix(K["part"], (40, 20, 0), 0.5), 0.9)
        sh.hole(c, 4.0 * s)
    else:                       # "fix": the snag that was fouling the hole, a knot of weed round a bent nail
        sh.line([P(-11, -6), P(-3, 2), P(6, 0), P(11, 7)], K["snag2"], 2.4 * s)
        sh.line([P(11, 7), P(9, 9.5)], K["snag2"], 2.4 * s)
        for k in range(3):
            sh.poly(_round(P(-2 + 3 * k, 0.5 - k), (6.5 - k) * s, (4.5 - 0.6 * k) * s, 9, ang + 0.5 * k, 0.5, k), None, K["snag"], 1.7 * s)
        sh.line([P(-5, -2), P(-8, -9), P(-5, -13)], K["snag"], 1.6 * s)
        sh.line([P(3, -2), P(5, -8)], K["snag"], 1.6 * s)


def draw_thing(target, kind, x, y, scale=1.0, angle=0.0, stand=True, **kw):
    """Draw a piece, reel, page, part or fix on its own. With stand=True, (x, y) is the
    middle of its bottom edge (it stands on the gravel or the sill); else its centre."""
    R = _split(kw)
    sh = Sheet()
    hy = THING_HALF.get(kind, (10, 10))[1]
    _thing(sh, kind, (0.0, hy if stand else 0.0), angle)
    R.setdefault("shadow", False)
    return _finish(target, sh, x, y, scale, 1, (0.0, 0.0), None, R)


def _bubble(sh, c, r):
    if r <= 0.3:
        return
    sh.poly(_round(c, r, r * 0.94, 20), COLORS["bubble"] + (70,), COLORS["bubble"], 0.9, True)
    sh.line([_add(c, _u(2.2, r * 0.62)), _add(c, _u(1.6, r * 0.66))], (255, 255, 255), max(0.8, r * 0.12), True)


def _breath_bubble(sh, mouth, t, t0=0.5, big=13.0):
    """The one big bubble a dog lets go of when its breath runs out, then a few small ones."""
    u = t - t0
    if u < 0:
        return
    g = ease(u, 0.0, 0.4)
    rise = max(0.0, u - 0.4)
    c = (mouth[0] + 6 * g + 4 * math.sin(rise * 5), mouth[1] + 3 * g + 90 * rise + 30 * rise * rise)
    _bubble(sh, c, big * g)
    for k in range(4):
        uk = u - 0.55 - 0.22 * k
        if uk > 0:
            _bubble(sh, (mouth[0] + 5 + 5 * math.sin(uk * 6 + k), mouth[1] + 4 + 70 * uk + 20 * uk * uk), 2.5 + 1.5 * _h(k))


# ------------------------------------------------- secondary dynamics core ---
# SCIONs 13 and 41: primary motion is authored; loose parts are spring-dampers
# driven by the acceleration and speed of the point they hang from. Nothing is
# stored between frames: the state at t is integrated from t - WINDOW, by which
# time any start-up transient has decayed.
WINDOW = 2.2
DT = 1.0 / 72.0
G = 980.0
_sim_cache = {}


def _simulate(prim, geom, specs, t):
    n = int(WINDOW / DT)
    S, V, hist = {}, {}, {}
    for i in range(-2, n + 1):
        ti = t - (n - i) * DT
        P = prim(ti)
        wet = P.get("water", 0)
        if i < 0:
            for sp in specs:
                r = sp["rest"](P)
                if sp["kind"] == "mass":
                    S[sp["key"] + "x"], S[sp["key"] + "y"] = r
                    V[sp["key"] + "x"] = V[sp["key"] + "y"] = 0.0
                else:
                    S[sp["key"]] = r
                    V[sp["key"]] = 0.0
        A = geom(P, S)
        X = P.get("X", 0.0)
        for sp in specs:
            key = sp["key"]
            ax, ay = A[key]
            ax += X
            hp = hist.get(key)
            if hp is None:
                hist[key] = (ax, ay, ax, ay)
                continue
            x1, y1, x2, y2 = hp
            hist[key] = (ax, ay, x1, y1)
            if i < 0:
                continue
            vx, vy = (ax - x1) / DT, (ay - y1) / DT
            acx, acy = (ax - 2 * x1 + x2) / (DT * DT), (ay - 2 * y1 + y2) / (DT * DT)
            q = sp["wet"] if (wet and "wet" in sp) else sp
            kind = sp["kind"]
            if kind == "mass":
                rx, ry = sp["rest"](P)
                for ax_, r_, a_, k_, c_ in (("x", rx, acx, q["kx"], q["cx"]), ("y", ry, acy, q["ky"], q["cy"])):
                    kk = key + ax_
                    acc = -k_ * (S[kk] - r_) - c_ * V[kk] - q["w"] * a_
                    V[kk] += acc * DT
                    S[kk] += V[kk] * DT
                    lim = q.get("lim")
                    if lim and abs(S[kk] - r_) > lim:
                        S[kk] = r_ + math.copysign(lim, S[kk] - r_)
                        V[kk] *= -0.2
                continue
            th, om = S[key], V[key]
            acc = -q["c"] * om
            if q["k"]:
                acc -= q["k"] * (th - sp["rest"](P))
            if kind == "pend":
                s_, c_ = math.sin(th), math.cos(th)
                acc += (q["w"] * (acx * s_ - acy * c_) - q["g"] * c_ + q["cd"] * (vx * s_ - vy * c_)) / q["L"]
            om += acc * DT
            th += om * DT
            lo, hi = sp.get("lo"), sp.get("hi")
            if lo is not None and th < lo:
                th, om = lo, -0.35 * om
            if hi is not None and th > hi:
                th, om = hi, -0.35 * om
            S[key], V[key] = th, om
    for k, v in V.items():
        S[k + "_v"] = v
    return S


def _secondary(tag, prim, geom, specs, t, okey):
    key = (tag, round(t * 2000), okey)
    if key not in _sim_cache:
        if len(_sim_cache) > 600:
            _sim_cache.clear()
        _sim_cache[key] = _simulate(prim, geom, specs, t)
    return _sim_cache[key]


def _okey(action, o):
    return (action,) + tuple(sorted((k, v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in o.items()))


def _pend(key, L, k=0.0, c=1.5, g=G, w=1.0, cd=0.6, rest=None, wet=None, lo=None, hi=None):
    sp = dict(kind="pend", key=key, L=L, k=k, c=c, g=g, w=w, cd=cd, rest=rest or (lambda P: -math.pi / 2), lo=lo, hi=hi)
    if wet:
        sp["wet"] = dict(L=L, k=k, c=c, g=g, w=w, cd=cd)
        sp["wet"].update(wet)
    return sp


# ============================================================== RETRIEVER ===
# SCION 13 (secondary motion for performed 2D figures). A wooden pull-toy: one
# block body on four wheels, a neck plank on a hinge, a head on a hinge, a jaw
# on a pin, one ear flap, a peg tail, and a bead on a string. The body is the
# performance (primary). Neck, head, jaw, ear, tail, bead and the carried thing
# are secondary rig links: inertial spring-dampers that start late and settle
# late, and then stop.
R_WHEEL = 14.0
RET_SIZE = {"big": 1.0, "mid": 0.82, "small": 0.64}
RET_SPEED = {"walk": 70.0, "carry": 60.0, "swim": 55.0}
_NECK0 = math.atan2(26.0, 10.0)
_TAIL0 = 2.07

_RET_SPECS = [
    _pend("neck", 28.0, k=60.0, c=3.4, g=0.0, w=2.4, cd=0.0, rest=lambda P: _NECK0 + P["pitch"] + P["neck"],
          wet=dict(c=6.0, w=0.3), lo=_NECK0 - 1.74),
    _pend("head", 22.0, k=90.0, c=4.2, g=0.0, w=0.6, cd=0.0, rest=lambda P: P["pitch"] + P["head"], wet=dict(c=8.0), lo=-0.78),
    dict(kind="follow", key="jaw", k=240.0, c=9.0, rest=lambda P: P["jaw"], lo=0.0),
    _pend("ear", 22.0, c=3.4, cd=0.6, wet=dict(g=-170.0, c=4.5, cd=5.0)),
    _pend("tail", 30.0, k=110.0, c=3.6, g=0.0, w=4.0, cd=0.0, rest=lambda P: P["tail"] + P["pitch"], wet=dict(c=7.0, cd=1.5)),
    _pend("bead", 17.0, c=2.8, cd=0.5, wet=dict(g=220.0, c=3.5, cd=6.0)),
    _pend("thing", 14.0, k=110.0, c=4.5, g=0.0, w=0.5, cd=0.0, rest=lambda P: math.pi / 2 + P["thing_a"], wet=dict(c=9.0)),
]


def _ret_prim(action, t, o):
    P = dict(X=0.0, by=0.0, pitch=0.0, neck=0.0, head=0.0, jaw=0.0, tail=_TAIL0, spin=0.0, water=0,
             thing_a=0.0, hold=1.0, pin=None, anchor="ground")
    carry = o.get("carry")
    look = o.get("look", 0.0)
    if action in ("walk", "carry"):
        v = o.get("speed", RET_SPEED["carry" if (action == "carry" or carry) else "walk"])
        P["X"] = v * t
        ph = P["X"] / R_WHEEL
        P["by"] = 0.9 * (1 - math.cos(ph)) / 2          # one wheel is not quite round
        P["pitch"] = 0.028 * math.sin(ph)
        if carry or action == "carry":
            P["head"], P["neck"], P["jaw"] = 0.34, 0.10, 0.12
    elif action == "wait":
        P["X"] = _arrive(t, o.get("arrive", RET_SPEED["walk"]))
        if carry:
            P["head"], P["neck"], P["jaw"] = 0.34, 0.10, 0.12
    elif action == "proud":
        P["head"], P["neck"], P["jaw"] = 0.42, 0.12, 0.12
        P["tail"] = _TAIL0 - 0.10 + 0.26 * math.tanh(5 * math.sin(TAU * 3.0 * t))      # the peg ticks
    elif action == "told":
        P["head"] = lerp(0.40, -0.30, ease(t, 0.25, 1.0))
        P["neck"] = lerp(0.12, -0.28, ease(t, 0.35, 1.1))
        P["tail"] = _TAIL0 + 0.85 * ease(t, 0.0, 0.5)                                    # the peg stops and drops
        P["jaw"] = 0.12 if carry else 0.0
    elif action == "set_down":
        P["X"] = _arrive(t, o.get("arrive", RET_SPEED["carry"]))
        down = bell(t, 0.30, 0.82, 1.18, 1.70)
        P["neck"] = lerp(0.10, -1.72, down)
        P["head"] = lerp(0.34, -0.72, down)
        P["jaw"] = 0.12 + 0.42 * bell(t, 0.95, 1.06, 1.35, 1.55) - 0.12 * ease(t, 1.5, 1.6)
        P["hold"] = 1.0 if t < 1.0 else 0.0
        P["tail"] = _TAIL0 + 0.22 * (bell(t, 1.9, 1.96, 2.04, 2.1) + bell(t, 2.2, 2.26, 2.34, 2.4))
        P["head"] += 0.25 * ease(t, 1.7, 2.0)
    elif action == "swim":
        P["anchor"], P["water"] = "body", 1
        P["X"] = o.get("speed", RET_SPEED["swim"]) * t
        P["by"] = 2.5 * math.sin(TAU * 0.8 * t)
        P["pitch"] = o.get("pitch", 0.0) + 0.05 * math.sin(TAU * 0.8 * t + 1.0)
        P["spin"] = -7.0 * t
        P["neck"] = 0.12
        P["head"] = 0.16 - 0.6 * o.get("pitch", 0.0) + (0.2 if carry else 0.0)
        P["jaw"] = 0.12 if carry else 0.0
    elif action == "breath_out":
        P["anchor"], P["water"] = "body", 1
        shake = bell(t, 0.0, 0.2, 0.42, 0.5)
        P["head"] = 0.07 * shake * math.sin(TAU * 6 * t) + 0.35 * ease(t, 0.6, 1.6)
        P["jaw"] = 0.6 * bell(t, 0.48, 0.56, 1.3, 2.0) + 0.1 * ease(t, 2.0, 2.2)
        P["pitch"] = 0.55 * ease(t, 0.7, 2.0)
        P["spin"] = 2.5 * max(0.0, t - 0.8) ** 1.3
        P["by"] = 2.0 * math.sin(TAU * 0.5 * t) * ease(t, 0.8, 1.5)
        P["hold"] = 0.0
    elif action == "surface":
        P["anchor"] = "pin"
        P["pitch"] = 0.95
        hgt = -8.0 + 20.0 * (1 - math.exp(-4.5 * max(0.0, t)) * math.cos(7.0 * max(0.0, t))) + 1.2 * math.sin(2.2 * t)
        P["pin"] = (0.0, hgt)
        P["head"] = -0.45
        P["neck"] = -0.1
        P["jaw"] = 0.14 + 0.42 * abs(math.sin(TAU * 1.5 * t)) * math.exp(-0.45 * max(0.0, t))
        P["spin"] = -3.0 * t
        P["hold"] = 0.0
    elif action == "warm":                   # wet on the bank beside a cow: rattles with cold, then stops and leans on her
        w = o.get("warm", 4.0)
        k = 1 - ease(t, 0.3 * w, w)
        shv = math.sin(TAU * 11 * t) * k
        P["X"] = 0.9 * shv + 7.0 * o.get("cow", 1) * ease(t, 0.2 * w, 0.7 * w)
        P["pitch"] = 0.012 * shv
        P["head"] = lerp(0.10, -0.42, k)
        P["neck"] = lerp(0.0, -0.30, k)
        P["tail"] = _TAIL0 + 0.85 * k + 0.2 * math.tanh(5 * math.sin(TAU * 2.5 * t)) * bell(t, w, w + 0.3, w + 1.5, w + 1.8)
    P["head"] += look
    if not carry:
        P["hold"] = 0.0
    return P


def _ret_geom(P, S):
    pitch = P["pitch"]

    def raw(p, off):
        q = _rot((p[0], p[1] - 40.0), pitch)
        return (q[0] + off[0], q[1] + 40.0 + P["by"] + off[1])

    def chain(off, S):
        B = raw((40.0, 58.0), off)
        pn = S.get("neck", _NECK0 + pitch + P["neck"])
        N = _add(B, _u(pn, 28.0))
        ah = S.get("head", pitch + P["head"])
        M = _add(N, _rot((40.0, -4.0), ah))
        return B, pn, N, ah, M

    off = (0.0, 0.0)
    if P["pin"] is not None:                 # pinned by the authored pose, so loose parts cannot drag the pin about
        M0 = chain(off, {})[4]
        off = (P["pin"][0] - M0[0], P["pin"][1] - M0[1])
    B, pn, N, ah, M = chain(off, S)
    return dict(neck=B, head=N, jaw=N, ear=_add(N, _rot((4.0, 15.0), ah)), tail=raw((-56.0, 56.0), off),
                bead=raw((56.0, 40.0), off), thing=M, _B=B, _N=N, _ah=ah, _M=M, _pn=pn, _off=off)


def _ret_thing_centre(M, phi, kind, ts):
    hx, hy = THING_HALF.get(kind, (12, 12))
    up, rt = _u(phi), _u(phi - math.pi / 2)
    return (M[0] + rt[0] * (hx + 1) * ts + up[0] * 2 * ts, M[1] + rt[1] * (hx + 1) * ts + up[1] * 2 * ts)


def _ret_build(sh, P, S, o, ksize):
    K = COLORS
    G_ = _ret_geom(P, S)
    off, pitch = G_["_off"], P["pitch"]
    carry = o.get("carry")

    def Bf(p):
        q = _rot((p[0], p[1] - 40.0), pitch)
        return (q[0] + off[0], q[1] + 40.0 + P["by"] + off[1])

    edge = _mix(K["wood"], (60, 30, 0), 0.55)
    wang = -P["X"] / R_WHEEL + P["spin"]

    def wheel(c, far):
        col = K["wheel_far"] if far else K["wheel"]
        sh.poly(_round(c, R_WHEEL, R_WHEEL, 22), col, _mix(col, (0, 0, 20), 0.5), 1.0)
        if not far:
            sh.dot(c, 4.6, K["hub"], _mix(K["hub"], (60, 40, 0), 0.5), 0.7, True)
            for k in range(3):
                sh.dot(_add(c, _u(wang + TAU * k / 3, 9.2)), 1.7 if k else 2.6, K["hub"], None, 0, True)

    # far wheels
    wheel(Bf((42.0, 16.0)), True)
    wheel(Bf((-30.0, 16.0)), True)
    # tail peg
    tp = G_["tail"]
    ta = S["tail"]
    tip = _add(tp, _u(ta, 30.0))
    sh.poly(_bar(tp, tip, 6.5, 5.0), K["walnut"], _mix(K["walnut"], (0, 0, 0), 0.4), 0.8)
    sh.dot(tip, 5.6, K["walnut"], _mix(K["walnut"], (0, 0, 0), 0.4), 0.8)
    # body block and axle blocks
    for blk in ([(24, 24), (46, 24), (43, 9), (27, 9)], [(-48, 24), (-26, 24), (-29, 9), (-45, 9)]):
        sh.poly([Bf(p) for p in blk], K["wood_dark"], _mix(K["wood_dark"], (0, 0, 0), 0.4), 0.8)
    body = [(-58, 26), (-62, 44), (-56, 60), (-36, 67), (6, 64), (32, 67), (50, 61), (57, 42), (53, 26), (36, 20), (-44, 20)]
    sh.poly([Bf(p) for p in body], K["wood"], edge, 1.1)
    for k, yy in enumerate((34.0, 46.0, 55.0)):      # grain
        sh.line([Bf((-50 + 4 * k, yy + 2 * math.sin(k))), Bf((-14, yy + 3 - k)), Bf((26, yy - 1 + k)), Bf((48 - 3 * k, yy + 1))],
                _mix(K["wood"], K["wood_dark"], 0.45), 0.7, True)
    # bead on its string
    bp = G_["bead"]
    bt = _add(bp, _u(S["bead"], 17.0))
    mid = _add(lerp2(bp, bt, 0.5), _u(S["bead"] - math.pi / 2, -clamp(S.get("bead_v", 0) * 1.2, -5, 5)))
    sh.line([bp, mid, bt], K["string"], 0.9, True)
    sh.dot(bt, 5.0, K["bead"], _mix(K["bead"], (0, 30, 40), 0.5), 0.8)
    sh.dot(bp, 2.0, K["pin"], None, 0, True)
    # neck plank
    B, N, ah = G_["_B"], G_["_N"], G_["_ah"]
    sh.poly(_bar(_add(B, _u(G_["_pn"], -6.0)), _add(N, _u(G_["_pn"], 5.0)), 24.0, 17.0), K["wood"], edge, 1.1)

    def Hf(p):
        return _add(N, _rot(p, ah))

    # jaw, then the thing, then the head over both
    jp = Hf((8.0, -5.0))
    ja = ah - S["jaw"]
    sh.poly([_add(jp, _rot(p, ja)) for p in [(-4, 2), (37, 2), (42, -2), (37, -7), (4, -9), (-5, -5)]], K["wood_dark"], _mix(K["wood_dark"], (0, 0, 0), 0.4), 0.9)
    M = G_["_M"]
    sh.mark("mouth", M)
    ts = o.get("thing_scale", 1.0) / (ksize * 1.25)
    if carry and (P["hold"] >= 0.5 or o.get("leave", True)):
        phi = S["thing"]
        c = _ret_thing_centre(M, phi, carry, ts)
        ang = phi - math.pi / 2
        if "_drop" in P:                         # set_down: the thing settles onto its spot, then stays
            dc, w = P["_drop"]
            c = lerp2(c, dc, w)
            ang *= (1 - w)
            sh.mark("thing", (dc[0], dc[1] - THING_HALF.get(carry, (12, 12))[1] * ts))
        _thing(sh, carry, c, ang, ts)
    head = [(-13, -7), (-13, 10), (-4, 19), (14, 20), (24, 13), (31, 10), (49, 10), (54, 5), (54, -3), (24, -5), (8, -10)]
    sh.poly([Hf(p) for p in head], K["wood"], edge, 1.1)
    sh.line([Hf((-6, 2)), Hf((12, 4)), Hf((30, 2))], _mix(K["wood"], K["wood_dark"], 0.45), 0.7, True)
    sh.dot(Hf((52.0, 4.5)), 4.3, K["nose"])
    sh.dot(Hf((15.0, 10.5)), 2.9, K["eye"], None, 0, True)
    sh.dot(Hf((15.8, 11.4)), 0.9, K["glint"], None, 0, True)
    # ear flap on its pin
    ep = G_["ear"]
    ea = S["ear"]
    ear = [(-3, -6), (6, -9.5), (18, -9.5), (27, -5), (30, 1), (26, 7), (14, 9), (4, 8), (-3, 5)]
    sh.poly([_add(ep, _rot(p, ea)) for p in ear], K["walnut"], _mix(K["walnut"], (0, 0, 0), 0.4), 0.9)
    for p in (ep, N, jp, tp, B):
        sh.dot(p, 2.1, K["pin"], _mix(K["pin"], (60, 30, 0), 0.6), 0.5, True)
    # near wheels
    wheel(Bf((35.0, 14.0)), False)
    wheel(Bf((-37.0, 14.0)), False)
    sh.mark("nose", Hf((54.0, 4.0)))
    sh.mark("head", Hf((10.0, 6.0)))
    sh.mark("eye", Hf((15.0, 10.5)))
    sh.mark("body", Bf((0.0, 40.0)))
    sh.mark("tail", tip)
    sh.mark("ear", _add(ep, _u(ea, 28.0)))
    sh.info["hold"] = bool(P["hold"] >= 0.5)
    if o.get("bubbles", True) and o.get("_action") == "breath_out":
        _breath_bubble(sh, M, o["_t"])


def lerp2(p, q, x):
    return (lerp(p[0], q[0], x), lerp(p[1], q[1], x))


def retriever(target, x, y, action="walk", t=0.0, scale=1.0, facing=1, size="big", carry=None, **kw):
    """Wooden pull-toy retriever. Actions: walk, carry, wait, set_down, proud, told,
    swim, breath_out, surface. size: 'big' | 'mid' | 'small' (or a number)."""
    R = _split(kw)
    o = dict(kw)
    o["carry"] = carry
    ks = RET_SIZE.get(size, size if isinstance(size, (int, float)) else 1.0)
    prim = lambda tt: _ret_prim(action, tt, o)                      # noqa: E731
    S = _secondary("ret", prim, _ret_geom, _RET_SPECS, t, _okey(action, o))
    P = prim(t)
    if action == "set_down" and carry:
        Pd = _ret_prim(action, 1.0, o)
        Gd = _ret_geom(Pd, {})
        ts = o.get("thing_scale", 1.0) / (ks * 1.25)
        P["_drop"] = ((Gd["_M"][0] + (THING_HALF[carry][0] + 1) * ts if carry in THING_HALF else Gd["_M"][0] + 12,
                       THING_HALF.get(carry, (12, 12))[1] * ts), ease(t, 0.84, 1.0))
    sh = Sheet()
    o["_action"], o["_t"] = action, t
    _ret_build(sh, P, S, o, ks)
    origin = (0.0, 40.0) if P["anchor"] == "body" else (0.0, 0.0)
    return _finish(target, sh, x, y, scale * ks * 1.25, facing, origin, "wood", R)


# =============================================================== SHEEPDOG ===
# SCION 41 (inertia and restraint). A crepe-paper dog on four coil springs.
# The feet are the performance. The body is a mass proxy sitting on the
# springs (it lurches on when the feet stop, and bounces); head, ears, tail
# and every strip of fringe are damped pendulums hung from that mass, each
# with its own length and damping. All energy decays when the feet stop.
SHP_SPEED = {"walk": 62.0, "run_line": 175.0, "swim": 50.0}
_SHP_SOCK = [(27.0, -15.0), (35.0, -13.0), (-31.0, -15.0), (-23.0, -13.0)]     # fn ff hn hf, from the body centre
_SHP_REST = [27.0, 35.0, -31.0, -23.0]
_SHP_PHASE = [0.0, 0.5, 0.5, 0.0]

_SHP_FRINGE = []
for _i in range(14):                                  # long under-row, rump to chest
    _fx = -45.0 + _i * 6.4
    _SHP_FRINGE.append(dict(key="f%02d" % _i, at=(_fx, 12.0 + 7.0 * math.sin((_i + 0.5) / 14 * math.pi)), L=30.0 + 9.0 * _h(_i + 3),
                            w=8.0 + 3.0 * _h(_i * 3 + 5), row=0, c=1.7 + 1.4 * _h(_i * 7 + 1), white=_fx > 14, lean=0.2 * (_h(_i * 13 + 2) - 0.5),
                            shade=_h(_i * 17 + 4)))
for _i in range(13):                                  # short top row
    _fx = -41.0 + _i * 6.3
    _SHP_FRINGE.append(dict(key="g%02d" % _i, at=(_fx, 19.0 + 6.0 * math.sin((_i + 0.5) / 13 * math.pi)), L=16.0 + 8.0 * _h(_i + 11),
                            w=7.5 + 3.0 * _h(_i * 3 + 9), row=1, c=2.2 + 1.4 * _h(_i * 5 + 2), white=_fx > 18, lean=0.24 * (_h(_i * 19 + 6) - 0.5),
                            shade=_h(_i * 23 + 8)))
_SHP_HEADF = [dict(key="h%d" % _i, at=at, L=L, w=7.5, c=2.4 + _h(_i)) for _i, (at, L) in
              enumerate([((-9.0, 16.0), 14.0), ((-3.0, 19.0), 16.0), ((3.0, 20.0), 18.0), ((9.0, 19.0), 18.0), ((14.5, 15.5), 16.0), ((19.0, 10.5), 12.0)])]
_SHP_EAR = dict(key="ear", at=(-10.0, 9.0), L=24.0, w=11.0, c=1.8)


def _shp_specs():
    specs = [dict(kind="mass", key="body", kx=70.0, cx=2.8, ky=210.0, cy=5.5, w=1.0, lim=24.0,
                  rest=lambda P: (P["tx"], P["ty"]), wet=dict(kx=40.0, cx=6.0, ky=60.0, cy=7.0, w=0.4, lim=24.0)),
             _pend("head", 17.0, k=70.0, c=3.4, g=0.0, w=0.7, cd=0.0, rest=lambda P: 0.45 + P["pitch"] + P["head"], wet=dict(c=7.0)),
             _pend("tail", 26.0, k=24.0, c=2.0, g=0.0, w=0.9, cd=1.5, rest=lambda P: P["tail"] + P["pitch"], wet=dict(k=6.0, c=4.0, cd=5.0))]
    for f in _SHP_FRINGE + _SHP_HEADF + [_SHP_EAR]:
        specs.append(_pend(f["key"], f["L"], c=f["c"], g=G * 0.5, cd=2.0, wet=dict(g=55.0, c=f["c"] + 2.5, cd=5.0)))
    return specs


_SHP_SPECS = _shp_specs()


def _foot(c, off, duty, stride, liftv, rest):
    u = (c + off) % 1.0
    A = stride * duty / 2
    if u < duty:
        return (rest + A * (1 - 2 * u / duty), 0.0)
    s = (u - duty) / (1 - duty)
    return (rest - A + 2 * A * smooth(s), liftv * math.sin(math.pi * s))


def _shp_prim(action, t, o):
    P = dict(X=0.0, tx=0.0, ty=0.0, pitch=0.0, head=0.0, tail=2.45, water=0, anchor="ground", feet=None,
             pin=None, hold=1.0, push=0.0)
    stride, liftv, duty = 40.0, 7.0, 0.6
    if action in ("walk", "carry"):
        P["X"] = o.get("speed", SHP_SPEED["walk"]) * t
    elif action in ("run_line", "run"):
        stride, liftv, duty = 74.0, 13.0, 0.45
        P["X"] = o.get("speed", SHP_SPEED["run_line"]) * t
        P["ty"], P["pitch"], P["head"], P["tail"] = -5.0, -0.07, -0.22, 2.9
    elif action == "wait":
        P["X"] = _arrive(t, o.get("arrive", SHP_SPEED["walk"]))
    elif action == "nudge":
        d = o.get("push", 14.0)
        P["push"] = d * ease(t, 0.78, 1.18)
        P["X"] = _arrive(t, o.get("arrive", SHP_SPEED["walk"])) + P["push"]
        low = bell(t, 0.36, 0.72, 1.2, 1.6)
        P["tx"], P["ty"], P["pitch"] = 9.0 * low, -9.0 * low, -0.20 * low
        P["head"] = -1.05 * low + 0.22 * bell(t, 1.6, 1.8, 2.3, 2.6)       # then it tips its head: is that straight?
    elif action == "warm":
        w = o.get("warm", 4.0)
        k = 1 - ease(t, 0.3 * w, w)
        shv = math.sin(TAU * 11 * t) * k
        stride, liftv = 14.0, 4.0
        P["X"] = 7.0 * o.get("cow", 1) * ease(t, 0.2 * w, 0.7 * w)
        P["tx"], P["ty"] = 2.2 * shv, -7.0 * k
        P["head"] = -0.55 * k
        P["tail"] = 2.45 + 1.2 * k
    c = P["X"] / stride + o.get("phase", 0.0)
    P["ty"] += 1.8 * math.cos(2 * TAU * c) if action in ("walk", "carry", "run_line", "run") else 0.0
    P["feet"] = [_foot(c, _SHP_PHASE[i], duty, stride, liftv, _SHP_REST[i]) for i in range(4)]
    if action == "swim":
        P["anchor"], P["water"] = "body", 1
        P["X"] = o.get("speed", SHP_SPEED["swim"]) * t
        P["pitch"] = o.get("pitch", 0.0) + 0.05 * math.sin(TAU * 0.7 * t)
        P["ty"] = 2.5 * math.sin(TAU * 0.7 * t + 0.6)
        P["head"] = 0.12 - 0.5 * o.get("pitch", 0.0)
        P["tail"] = 3.05
        P["feet"] = [(_SHP_SOCK[i][0] - 9.0 + 9.0 * math.sin(TAU * 1.3 * t + i * 1.7),
                      _SHP_SOCK[i][1] - 24.0 + 9.0 * math.cos(TAU * 1.3 * t + i * 1.7)) for i in range(4)]
    elif action == "breath_out":
        P["anchor"], P["water"] = "body", 1
        P["pitch"] = 0.5 * ease(t, 0.7, 2.0)
        P["head"] = 0.08 * bell(t, 0.0, 0.2, 0.42, 0.5) * math.sin(TAU * 6 * t) + 0.4 * ease(t, 0.5, 1.5)
        P["tail"] = lerp(3.05, 4.3, ease(t, 0.8, 2.0))
        limp = ease(t, 0.6, 1.6)
        P["feet"] = [(_SHP_SOCK[i][0] - 4.0 * limp + (1 - limp) * 6.0 * math.sin(TAU * 2.2 * t + i * 1.7),
                      _SHP_SOCK[i][1] - 24.0 - 9.0 * limp + (1 - limp) * 5.0 * math.cos(TAU * 2.2 * t + i * 1.7)) for i in range(4)]
        P["hold"] = 0.0
    elif action == "surface":
        P["anchor"] = "pin"
        P["pitch"] = 0.85
        tt = max(0.0, t)
        P["pin"] = (0.0, -10.0 + 22.0 * (1 - math.exp(-4.5 * tt) * math.cos(7.0 * tt)) + 1.2 * math.sin(2.2 * t))
        P["head"] = -0.55 + 0.10 * math.sin(TAU * 1.5 * t) * math.exp(-0.4 * tt)
        P["tail"] = 3.3
        P["feet"] = [(_SHP_SOCK[i][0] - 2.0 + 5.0 * math.sin(TAU * 1.6 * t + i * 1.7),
                      _SHP_SOCK[i][1] - 25.0 + 5.0 * math.cos(TAU * 1.6 * t + i * 1.7)) for i in range(4)]
        P["hold"] = 0.0
    P["head"] += o.get("look", 0.0)
    if not o.get("carry"):
        P["hold"] = 0.0
    return P


def _shp_geom(P, S):
    ox, oy = S.get("bodyx", P["tx"]), S.get("bodyy", P["ty"])
    pitch = P["pitch"] + 0.012 * (ox - P["tx"])
    base = (0.0, 0.0) if P["anchor"] != "ground" else (0.0, 56.0)

    def frame(off, S, ox, oy, pitch):
        C = (base[0] + ox + off[0], base[1] + oy + off[1])
        neck = _add(C, _rot((30.0, 8.0), pitch))
        ph = S.get("head", 0.45 + pitch + P["head"])
        Hc = _add(neck, _u(ph, 17.0))
        return C, neck, ph, Hc

    off = (0.0, 0.0)
    if P["pin"] is not None:
        H0 = frame(off, {}, P["tx"], P["ty"], P["pitch"])[3]
        off = (P["pin"][0] - H0[0], P["pin"][1] - H0[1] + 6.0)
    C, neck, ph, Hc = frame(off, S, ox, oy, pitch)
    ha = ph - 0.45
    A = dict(body=(0.0, 0.0), head=neck, tail=_add(C, _rot((-44.0, 8.0), pitch)), _C=C, _pitch=pitch, _Hc=Hc, _ha=ha, _off=off)
    for f in _SHP_FRINGE:
        A[f["key"]] = _add(C, _rot(f["at"], pitch))
    for f in _SHP_HEADF + [_SHP_EAR]:
        A[f["key"]] = _add(Hc, _rot(f["at"], ha))
    return A


def _strip(sh, a, phi, L, w, col, edge, seed, om=0.0, rest=-math.pi / 2):
    """One crepe strip hung from a, pointing along phi; it bends the way it is swinging."""
    d = (phi - rest + math.pi) % TAU - math.pi
    bend = clamp(-om * 0.05, -0.5, 0.5)
    b, e = rest + 0.7 * d + bend * 0.3, rest + 1.25 * d - bend
    p1 = _add(a, _u(b, L * 0.5))
    p2 = _add(p1, _u(e, L * 0.5))
    nb, ne = _u(b + math.pi / 2), _u(e + math.pi / 2)
    w0, w1, w2 = w / 2, w * 0.46, w * 0.36
    jag = 3.5 + 4.0 * _h(seed)
    pts = [(a[0] + nb[0] * w0, a[1] + nb[1] * w0), (p1[0] + nb[0] * w1, p1[1] + nb[1] * w1), (p2[0] + ne[0] * w2, p2[1] + ne[1] * w2),
           _add(p2, _u(e, jag)), (p2[0] - ne[0] * w2 * 0.2, p2[1] - ne[1] * w2 * 0.2), _add(_add(p2, _u(e, jag * 0.7)), (-ne[0] * w2 * 0.6, -ne[1] * w2 * 0.6)),
           (p2[0] - ne[0] * w2, p2[1] - ne[1] * w2), (p1[0] - nb[0] * w1, p1[1] - nb[1] * w1), (a[0] - nb[0] * w0, a[1] - nb[1] * w0)]
    sh.poly(pts, col, edge, 0.6)
    sh.line([_add(a, (nb[0] * w0 * 0.2, nb[1] * w0 * 0.2)), p1, p2], edge, 0.5, True)
    return p2


def _coil(sh, a, b, col, turns=5, amp=4.2, w=1.5):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = [a]
    n = turns * 2
    for k in range(1, n):
        f = k / n
        s = amp if k % 2 else -amp
        pts.append((a[0] + dx * f + nx * s, a[1] + dy * f + ny * s))
    pts.append(b)
    sh.line(pts, col, w)


def _shp_build(sh, P, S, o):
    K = COLORS
    A = _shp_geom(P, S)
    C, pitch, Hc, ha, off = A["_C"], A["_pitch"], A["_Hc"], A["_ha"], A["_off"]
    ground = P["anchor"] == "ground"

    def Bf(p):
        return _add(C, _rot(p, pitch))

    def footpt(i):
        fx, fy = P["feet"][i]
        return (fx, fy + 3.0) if ground else _add(C, _rot((fx, fy), pitch * 0.5))

    def leg(i, far):
        s, fpt = Bf(_SHP_SOCK[i]), footpt(i)
        _coil(sh, s, (fpt[0], fpt[1] + 1.0), K["steel_far"] if far else K["steel"], w=1.3 if far else 1.6)
        sh.poly(_round((fpt[0] + 2.0, fpt[1] - 0.5), 7.0, 3.6, 12), _mix(K["foot"], (0, 0, 0), 0.3) if far else K["foot"], None)

    leg(1, True)
    leg(3, True)
    # tail plume: three strips fanned from the rump
    tp = A["tail"]
    for k, (da, LL) in enumerate(((-0.28, 22.0), (0.26, 23.0), (0.0, 28.0))):
        _strip(sh, tp, S["tail"] + da, LL, 9.0, K["crepe"] if k < 2 else K["crepe_lt"], K["crepe_dk"], 40 + k, S.get("tail_v", 0), rest=S["tail"] + da - 0.25)
    sh.mark("tail", _add(tp, _u(S["tail"], 26.0)))
    # the body under the shag
    sh.poly([Bf(p) for p in _round((-6.0, 2.0), 42.0, 21.0, 22)], K["crepe_dk"], None)
    sh.poly([Bf(p) for p in _round((24.0, 2.0), 20.0, 21.0, 16)], K["white_dk"], None)
    leg(0, False)
    leg(2, False)
    edge_g, edge_w = K["crepe_dk"], _mix(K["white_dk"], K["crepe_dk"], 0.5)

    def fr(f):
        if f["white"]:
            col = _mix(K["white"], K["white_dk"], 0.7 * f["shade"])
        else:
            col = _mix(K["crepe_lt"], K["crepe_dk"], f["shade"] * 0.75 + (0.0 if f["row"] else 0.15))
        _strip(sh, A[f["key"]], S[f["key"]] + f["lean"], f["L"], f["w"], col, edge_w if f["white"] else edge_g, int(f["key"][1:]) + 30 * f["row"],
               S.get(f["key"] + "_v", 0))

    for f in _SHP_FRINGE:
        if f["row"] == 0:
            fr(f)
    # head: a white pom with a muzzle
    def Hf(p):
        return _add(Hc, _rot(p, ha))

    _strip(sh, Hf((-13.0, 7.0)), S["ear"] + 0.12, 22.0, 10.0, K["crepe_dk"], _mix(K["crepe_dk"], (0, 0, 0), 0.3), 71, S.get("ear_v", 0))
    sh.poly([Hf(p) for p in _round((1.0, 1.0), 21.0, 20.0, 20, 0, 0.10, 4)], K["white"], edge_w, 0.7)
    sh.poly([Hf(p) for p in _round((17.0, -7.0), 11.5, 8.5, 14)], K["white"], edge_w, 0.7)
    sh.poly([Hf(p) for p in _round((13.0, -5.0), 11.0, 7.5, 12)], K["white"], None)
    nose = Hf((27.5, -5.0))
    sh.dot(nose, 4.4, K["nose"])
    sh.dot(Hf((13.0, 2.0)), 2.6, K["eye"], None, 0, True)
    mouth = Hf((22.0, -13.0))
    carry = o.get("carry")
    if carry and P["hold"] >= 0.5:
        ts = o.get("thing_scale", 1.0) / 1.45
        hy = THING_HALF.get(carry, (12, 12))[1] * ts
        _thing(sh, carry, (mouth[0] + 3.0, mouth[1] - hy + 3.0), 0.12 * math.sin(S.get("head_v", 0) * 0.2), ts)
    for f in _SHP_FRINGE:
        if f["row"] == 1:
            fr(f)
    for f in _SHP_HEADF:
        _strip(sh, A[f["key"]], S[f["key"]], f["L"], f["w"], K["white"], edge_w, 50 + ord(f["key"][1]), S.get(f["key"] + "_v", 0))
    _strip(sh, A["ear"], S["ear"], _SHP_EAR["L"], _SHP_EAR["w"], K["crepe"], K["crepe_dk"], 70, S.get("ear_v", 0))
    sh.mark("nose", nose)
    sh.mark("mouth", mouth)
    sh.mark("head", Hc)
    sh.mark("body", C)
    sh.info["hold"] = bool(P["hold"] >= 0.5)
    sh.info["push_units"] = P["push"]
    if o.get("bubbles", True) and o.get("_action") == "breath_out":
        _breath_bubble(sh, mouth, o["_t"])


def sheepdog(target, x, y, action="walk", t=0.0, scale=1.0, facing=1, carry=None, **kw):
    """Crepe-paper sheepdog on springs. Actions: walk, run_line, nudge, wait, carry,
    swim, breath_out, surface."""
    R = _split(kw)
    o = dict(kw)
    o["carry"] = carry
    prim = lambda tt: _shp_prim(action, tt, o)                      # noqa: E731
    S = _secondary("shp", prim, _shp_geom, _SHP_SPECS, t, _okey(action, o))
    P = prim(t)
    sh = Sheet()
    o["_action"], o["_t"] = action, t
    _shp_build(sh, P, S, o)
    out = _finish(target, sh, x, y, scale * 1.45, facing, (0.0, 0.0), "crepe", R)
    out["push"] = out.pop("push_units") * scale * 1.45 * (1 if facing >= 0 else -1)
    return out


# ============================================================= BLOODHOUND ===
# SCION 07 (drawn metamorphosis). The hound is ONE pencil line: it starts as a
# curl for the eye, goes over the skull, down and up the long ear, along the
# back, out and back along the tail, down and up each leg, along the belly, up
# the throat, round the jowl, out to the nose and back to the brow. Each key
# drawing is that line with the same 300-odd points in the same order (point
# correspondence), and every frame is an in-between of two keys. The nose is
# the hand-authored exception: its part of the line can be paid out along a
# trail without the rest of the drawing moving.
HND_SPEED = {"walk": 50.0, "follow": 38.0, "carry": 44.0, "swim": 45.0}
_HND_STAND = dict(sh=(30.0, 78.0), hp=(-34.0, 74.0), H=(62.0, 100.0), ha=-0.12, ml=30.0,
                  fn=(34.0, 0.0), ff=(26.0, 0.0), hn=(-40.0, 0.0), hf=(-30.0, 0.0),
                  ear=-math.pi / 2, earL=46.0, tail=2.45, tailL=38.0, mo=0.0, puff=0.0, rot=0.0, ground=1.0, eye=1.0,
                  stretch=0.0)
_SEG_N = [14, 10, 24, 22, 16, 26, 18, 10, 18, 24, 14, 22, 22, 12, 22, 6]
_HND_RANGES = []
_k = 0
for _n in _SEG_N:
    _HND_RANGES.append((_k, _k + _n))
    _k += _n
HND_POINTS = _k


def _curve(ctrl, n):
    """Catmull-Rom through ctrl, resampled to n points evenly along its length."""
    if len(ctrl) == 2:
        return [lerp2(ctrl[0], ctrl[1], i / (n - 1)) for i in range(n)]
    pts = []
    m = len(ctrl)
    for i in range(m - 1):
        p0, p1, p2, p3 = ctrl[max(0, i - 1)], ctrl[i], ctrl[i + 1], ctrl[min(m - 1, i + 2)]
        for s in range(6):
            u = s / 6.0
            u2, u3 = u * u, u * u * u
            pts.append((0.5 * (2 * p1[0] + (p2[0] - p0[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (3 * p1[0] - p0[0] - 3 * p2[0] + p3[0]) * u3),
                        0.5 * (2 * p1[1] + (p2[1] - p0[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (3 * p1[1] - p0[1] - 3 * p2[1] + p3[1]) * u3)))
    pts.append(ctrl[-1])
    return _resample(pts, n)


def _resample(pts, n):
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = d[-1] or 1.0
    out, j = [], 0
    for i in range(n):
        s = tot * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        seg = d[j + 1] - d[j]
        out.append(lerp2(pts[j], pts[j + 1], (s - d[j]) / seg if seg > 0 else 0.0))
    return out


def _path_point(path, s):
    """Point and direction at arc length s along a polyline (extrapolates past the end)."""
    acc = 0.0
    for a, b in zip(path, path[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L > 0 and (acc + L >= s or b is path[-1]):
            u = (s - acc) / L
            return lerp2(a, b, u), math.atan2(b[1] - a[1], b[0] - a[0])
        acc += L
    return path[-1], 0.0


def _path_len(path):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))


def _hound_key(K, trail=None):
    """One key drawing: the whole line as HND_POINTS points, plus named landmarks."""
    sh_, hp, H, ha = K["sh"], K["hp"], K["H"], K["ha"]
    gr = K["ground"] > 0.5

    def Hf(px, py):
        return _add(H, _rot((px, py), ha))

    segs = []
    # 0 the eye: a curl
    E = Hf(6.0, 4.0)
    brow = Hf(10.5, 10.5)
    curl = [_add(E, _u(1.2 + 1.35 * TAU * i / 9 + ha, (0.7 + 3.0 * i / 9) * K["eye"])) for i in range(10)]
    segs.append(_curve(curl + [brow], _SEG_N[0]))
    # 1 skull
    er = Hf(-9.0, 3.0)
    segs.append(_curve([brow, Hf(1.0, 13.5), Hf(-9.0, 10.0), er], _SEG_N[1]))
    # 2 the long ear, a loop that hangs from the skull
    eu = _u(K["ear"])
    en = _u(K["ear"] + math.pi / 2)
    L = K["earL"]
    er2 = Hf(-12.0, -3.0)
    ear = [er, (er[0] + eu[0] * L * 0.45 + en[0] * 8, er[1] + eu[1] * L * 0.45 + en[1] * 8),
           (er[0] + eu[0] * L * 0.9 + en[0] * 6, er[1] + eu[1] * L * 0.9 + en[1] * 6),
           (er[0] + eu[0] * L, er[1] + eu[1] * L),
           (er[0] + eu[0] * L * 0.85 - en[0] * 6, er[1] + eu[1] * L * 0.85 - en[1] * 6),
           (er[0] + eu[0] * L * 0.4 - en[0] * 7, er[1] + eu[1] * L * 0.4 - en[1] * 7), er2]
    if gr:      # an ear that reaches the ground lies along it and drags
        ear = [(p[0] - 0.9 * max(0.0, 2.0 - p[1]), max(p[1], 1.6 + 0.25 * i)) for i, p in enumerate(ear)]
    segs.append(_curve(ear, _SEG_N[2]))
    # 3 neck, back
    mid = ((sh_[0] + hp[0]) / 2, (sh_[1] + hp[1]) / 2 - 3.0)
    tr = (hp[0] - 11.0, hp[1] - 3.0)
    segs.append(_curve([er2, (lerp(er2[0], sh_[0], 0.55), lerp(er2[1], sh_[1], 0.5) + 2.0), sh_, mid, (hp[0], hp[1] + 1.0), tr], _SEG_N[3]))
    # 4 tail, out and back
    tu, tn = _u(K["tail"]), _u(K["tail"] + math.pi / 2)
    TL = K["tailL"]
    tr2 = (tr[0] - 1.0, tr[1] - 7.0)
    tail = [tr, (tr[0] + tu[0] * TL * 0.5 + tn[0] * 3.5, tr[1] + tu[1] * TL * 0.5 + tn[1] * 3.5), (tr[0] + tu[0] * TL, tr[1] + tu[1] * TL),
            (tr[0] + tu[0] * TL * 0.5 - tn[0] * 1.5, tr[1] + tu[1] * TL * 0.5 - tn[1] * 1.5 - 3.0), tr2]
    if gr:
        tail = [(p[0], max(p[1], 1.5)) for p in tail]
    segs.append(_curve(tail, _SEG_N[4]))

    def leg(top_a, top_b, foot, wide, back, n, knee):
        r = clamp((top_a[1] - foot[1]) / 60.0, 0.25, 1.0)
        fx, fy = foot
        return _curve([top_a, (lerp(top_a[0], fx - back, 0.45) - 4.0 * r, lerp(top_a[1], fy, 0.42)), (fx - back, fy + 15.0 * r), (fx - wide, fy + 2.5),
                       (fx + 2.0, fy + 0.6), (fx + wide + 4.0, fy + 1.2), (fx + wide + 3.0, fy + 5.0), (fx + wide - 2.0, fy + 16.0 * r),
                       (lerp(top_b[0], fx + wide, 0.5) + knee * r, lerp(top_b[1], fy, 0.5)), top_b], n)

    g1 = (hp[0] + 9.0, hp[1] - 27.0)
    g2 = (hp[0] + 17.0, hp[1] - 28.0)
    segs.append(leg(tr2, g1, K["hn"], 4.5, 7.0, _SEG_N[5], 7.0))          # 5 hind near
    segs.append(leg(g1, g2, K["hf"], 3.5, 5.0, _SEG_N[6], 5.0))           # 6 hind far
    a1 = (sh_[0] - 13.0, sh_[1] - 37.0)
    a2 = (sh_[0] - 3.0, sh_[1] - 39.0)
    segs.append(_curve([g2, ((sh_[0] + hp[0]) / 2, (sh_[1] + hp[1]) / 2 - 35.0), a1], _SEG_N[7]))   # 7 belly
    segs.append(leg(a1, a2, K["ff"], 3.5, 2.0, _SEG_N[8], 0.0))           # 8 fore far
    c1 = (sh_[0] + 17.0, sh_[1] - 20.0)
    segs.append(leg(a2, c1, K["fn"], 4.5, 3.0, _SEG_N[9], 2.0))           # 9 fore near
    # 10 chest, throat, dewlap
    segs.append(_curve([c1, (sh_[0] + 21.0, sh_[1] - 5.0), Hf(-7.0, -15.0), Hf(-1.0, -19.0), Hf(5.0, -14.0)], _SEG_N[10]))
    # muzzle centre line: straight, or paid out along the trail
    base, tip0 = Hf(12.0, 0.0), Hf(12.0 + K["ml"], 0.0)
    path = [base, tip0]
    Lc = K["ml"]
    if trail and K["stretch"] > 0:
        path += list(trail)
        Lc = K["ml"] + K["stretch"] * _path_len([tip0] + list(trail))
    long_ = Lc > K["ml"] + 1.0

    def wid(s):
        return max(3.2 if long_ else 4.4, 8.6 - 0.15 * max(0.0, s - 4.0))

    def side(s, k):
        p, a = _path_point(path, s)
        return _add(p, _u(a + math.pi / 2, k))

    # 11 jowl and lower jaw: out to the chin, back to the corner of the mouth
    mo, puff = K["mo"], K["puff"]
    chin_s = min(K["ml"] - 3.0, Lc - 3.0)
    segs.append(_curve([Hf(5.0, -14.0), Hf(13.0, -20.0 - 12.0 * puff), Hf(22.0, -15.0 - 12.0 * puff - 6.0 * mo),
                        side(chin_s * 0.75, -wid(chin_s * 0.75) - 2.0 - 9.0 * mo), side(chin_s, -5.0 - 12.0 * mo),
                        side(chin_s - 3.0, -2.0 - 10.0 * mo), side(8.0, -2.0 - 2.0 * mo)], _SEG_N[11]))
    # 12 upper lip out to the nose
    n12 = _SEG_N[12]
    segs.append([side(lerp(8.0, Lc, i / (n12 - 1)), -min(2.2 + 2.5 * puff, wid(lerp(8.0, Lc, i / (n12 - 1))) * 0.6)) for i in range(n12)])
    # 13 the nose: a round loop on the end of the line
    pe, ae = _path_point(path, Lc)
    nc = _add(pe, _u(ae, 3.5))
    segs.append([_add(nc, _u(ae - 1.9 + (TAU * 0.78) * i / (_SEG_N[13] - 1), 5.0)) for i in range(_SEG_N[13])])
    # 14 top of the muzzle, back to the stop
    n14 = _SEG_N[14]
    segs.append([side(lerp(Lc - 1.0, 5.0, i / (n14 - 1)), wid(lerp(Lc - 1.0, 5.0, i / (n14 - 1))) * (0.62 + 0.38 * min(1.0, (Lc - lerp(Lc - 1.0, 5.0, i / (n14 - 1))) / 8.0)))
                 for i in range(n14)])
    # 15 the stop, ending where the eye began
    segs.append(_curve([segs[-1][-1], Hf(13.0, 10.5), Hf(11.0, 11.5)], _SEG_N[15]))
    pts = [p for s in segs for p in s]
    marks = [nc, side(min(K["ml"], Lc) - 2.0, -4.0 - 5.0 * mo), H, ((sh_[0] + hp[0]) / 2, (sh_[1] + hp[1]) / 2 - 16.0),
             (tr[0] + tu[0] * TL, tr[1] + tu[1] * TL), E]
    if K["rot"]:
        c = marks[3]
        pts = [_add(c, _rot((p[0] - c[0], p[1] - c[1]), K["rot"])) for p in pts]
        marks = [_add(c, _rot((p[0] - c[0], p[1] - c[1]), K["rot"])) for p in marks]
    return pts + marks


_HND_MARKS = ("nose", "mouth", "head", "body", "tail", "eye")


def _hk(**kw):
    K = dict(_HND_STAND)
    K.update(kw)
    return K


def _hnd_walk_key(i, n, stride, liftv, low=0.0, mo=0.0, level=0.0):
    """Key i of n round the walk cycle. low=1 puts the nose on the ground."""
    c = i / n
    feet = {}
    for name, off, rest in (("hn", 0.0, -40.0), ("fn", 0.25, 34.0), ("hf", 0.5, -30.0), ("ff", 0.75, 26.0)):
        feet[name] = _foot(c, off, 0.65, stride, liftv, rest)
    bob = 1.6 * math.cos(2 * TAU * c)
    sway = math.sin(TAU * c)
    Hs = (62.0 + 1.5 * sway, 100.0 + bob - 3.0 * level)
    Hl = (67.0 + 2.0 * sway, 35.5 + 0.8 * bob)
    return _hk(sh=(30.0, lerp(78.0, 71.0, low) + bob), hp=(-34.0, 74.0 - bob * 0.6),
               H=lerp2(Hs, Hl, low), ha=lerp(-0.12 + 0.05 * sway + 0.14 * level, -0.93, low), mo=mo,
               ear=-math.pi / 2 + 0.22 * math.sin(2 * TAU * c - 0.9) * (1 - low), tail=2.45 + 0.22 * sway - 0.5 * low, **feet)


def _hnd_swim_key(i, pitch=0.0, mo=0.0):
    a = TAU * i / 4
    return _hk(ground=0.0, sh=(30.0, 78.0), hp=(-34.0, 76.0), H=(64.0, 96.0 + 1.5 * math.sin(a)), ha=0.05, mo=mo,
               fn=(42.0 + 14.0 * math.cos(a), 36.0 + 8.0 * math.sin(a)), ff=(34.0 - 14.0 * math.cos(a), 38.0 - 8.0 * math.sin(a)),
               hn=(-52.0 + 10.0 * math.cos(a + 1.0), 38.0 + 7.0 * math.sin(a + 1.0)), hf=(-44.0 - 10.0 * math.cos(a + 1.0), 40.0 - 7.0 * math.sin(a + 1.0)),
               ear=math.pi - 0.45 + 0.12 * math.sin(a), tail=math.pi + 0.12 * math.cos(a), rot=pitch)


_HND_SIT = _hk(sh=(22.0, 77.0), hp=(-30.0, 40.0), H=(50.0, 104.0), ha=0.02, fn=(30.0, 0.0), ff=(23.0, 0.0),
               hn=(-14.0, 0.0), hf=(-6.0, 0.0), tail=math.pi + 0.05, ear=-math.pi / 2 - 0.05)
_HND_DOWN = _hk(sh=(30.0, 71.0), H=(67.0, 35.5), ha=-0.93, tail=1.95)


def _hnd_shape(action, t, o, trail=None):
    """The in-between for this moment: (points, X travelled, anchor, hold, water)."""
    carry = o.get("carry")
    info = dict(X=0.0, anchor="ground", hold=1.0 if carry else 0.0, water=0, pin=None)

    def tween(ka, kb, w, tr=None):
        A = _hound_key(ka, tr)
        if w <= 0:
            return A
        B = _hound_key(kb, tr)
        if w >= 1:
            return B
        return [lerp2(p, q, w) for p, q in zip(A, B)]

    def cycle(c, n, keyfn, tr=None):
        f = (c % 1.0) * n
        i = int(f)
        return tween(keyfn(i % n), keyfn((i + 1) % n), f - i, tr)

    if action in ("walk", "carry", "follow"):
        v = o.get("speed", HND_SPEED["carry" if (action == "walk" and carry) else action])
        info["X"] = v * t
        c = info["X"] / 56.0 + o.get("phase", 0.0)
        st = clamp(o.get("stretch", 0.0))
        if action == "follow":
            pts = cycle(c, 8, lambda i: dict(_hnd_walk_key(i, 8, 56.0, 7.0, low=1.0), stretch=st), trail)
        else:
            mo = 0.32 if carry else 0.0
            pts = cycle(c, 8, lambda i: _hnd_walk_key(i, 8, 56.0, 9.0, mo=mo, level=1.0 if carry else 0.0))
    elif action == "nose_down":
        st = clamp(o.get("stretch", 0.0))
        up = _hk(H=(60.0, 106.0), ha=0.22, ear=-math.pi / 2 - 0.25, tail=2.2)          # lifts and tests the air first
        down = dict(_HND_DOWN, stretch=st)
        sniff = dict(_HND_DOWN, H=(68.5, 37.0), ha=-0.88, stretch=st, tail=1.8)
        if t < 0.4:
            pts = tween(_HND_STAND, up, smooth(t / 0.4))
        elif t < 0.62:
            pts = _hound_key(up)
        elif t < 1.05:
            pts = tween(up, down, smooth((t - 0.62) / 0.43), trail)
        elif t < 2.0:                                                                  # three sniffs, then it knows
            u = (t - 1.05) / 0.95 * 3.0
            pts = tween(down, sniff, smooth(1 - abs((u % 1.0) * 2 - 1)), trail)
        else:
            pts = _hound_key(down, trail)
    elif action == "wait":
        w = smooth(t / 0.8) if o.get("sit", True) else 0.0
        pts = tween(_HND_STAND, _HND_SIT, w)
    elif action == "warm":
        w = o.get("warm", 4.0)
        k = 1 - ease(t, 0.3 * w, w)
        cold = _hk(sh=(28.0, 72.0), hp=(-32.0, 70.0), H=(56.0, 80.0), ha=-0.45, tail=3.9,
                   fn=(30.0, 0.0), ff=(24.0, 0.0), hn=(-34.0, 0.0), hf=(-26.0, 0.0))
        cold2 = dict(cold, sh=(29.8, 72.7), H=(58.0, 80.8), hp=(-30.4, 70.0))
        A = tween(cold, cold2, 0.5 + 0.5 * math.sin(TAU * 11 * t))
        if k >= 1:
            pts = A
        else:
            B = _hound_key(_HND_SIT)
            pts = [lerp2(p, q, 1 - k) for p, q in zip(A, B)]
    elif action == "swim":
        info.update(anchor="body", water=1, X=o.get("speed", HND_SPEED["swim"]) * t)
        pts = cycle(t * 1.1, 4, lambda i: _hnd_swim_key(i, o.get("pitch", 0.0), 0.32 if carry else 0.0))
    elif action == "breath_out":
        info.update(anchor="body", water=1, hold=0.0)
        k0 = _hnd_swim_key(0)
        k1 = dict(k0, puff=1.0, eye=1.5, ha=0.12)
        k2 = dict(k0, puff=0.2, mo=1.0, eye=1.3, ha=0.2)
        k3 = _hk(ground=0.0, sh=(30.0, 78.0), hp=(-34.0, 70.0), H=(62.0, 102.0), ha=0.5, mo=0.5, rot=0.55, eye=0.8,
                 fn=(38.0, 22.0), ff=(30.0, 24.0), hn=(-40.0, 18.0), hf=(-32.0, 20.0), ear=math.pi / 2 + 0.5, tail=math.pi + 0.9)
        if t < 0.5:
            pts = tween(k0, k1, smooth(t / 0.5))
        elif t < 0.62:
            pts = tween(k1, k2, smooth((t - 0.5) / 0.12))
        else:
            pts = tween(k2, k3, smooth((t - 0.62) / 1.3))
    elif action == "surface":
        tt = max(0.0, t)
        info.update(anchor="pin", hold=0.0,
                    pin=(0.0, -8.0 + 20.0 * (1 - math.exp(-4.5 * tt) * math.cos(7.0 * tt)) + 1.2 * math.sin(2.2 * t)))
        g = abs(math.sin(TAU * 1.5 * t)) * math.exp(-0.45 * tt)
        ka = _hk(ground=0.0, rot=0.95, H=(62.0, 100.0), ha=-0.55, mo=0.15, ear=-math.pi / 2 - 0.95, tail=math.pi + 0.3,
                 fn=(44.0, 40.0), ff=(36.0, 42.0), hn=(-44.0, 24.0), hf=(-36.0, 26.0))
        kb = dict(ka, mo=1.0, ha=-0.42, fn=(40.0, 46.0), ff=(40.0, 36.0), eye=1.4)
        pts = tween(ka, kb, g)
    else:
        pts = _hound_key(_HND_STAND)
    return pts, info


def _hnd_build(sh, pts, info, o, t):
    K = COLORS
    line, marks = pts[:HND_POINTS], dict(zip(_HND_MARKS, pts[HND_POINTS:]))
    if o.get("boil", True):                     # the line is redrawn eight times a second
        seed = int(math.floor(t * 8))
        line = [(p[0] + 0.55 * (_h(i * 3.1 + seed * 17.0) - 0.5), p[1] + 0.55 * (_h(i * 5.3 + seed * 29.0) - 0.5)) for i, p in enumerate(line)]
    Rg = _HND_RANGES
    fa = int(255 * clamp(o.get("fill", 0.86)))

    def seg(i):
        return line[Rg[i][0]:Rg[i][1]]

    if fa > 0:
        fill = K["paper"] + (fa,)
        for i in (4, 6, 8, 5, 9):                               # tail and legs, each its own closed loop
            sh.poly(seg(i), fill)
        sh.poly(seg(1) + seg(3) + [seg(5)[-1], seg(6)[-1]] + seg(7) + [seg(8)[-1], seg(9)[-1]] + seg(10) + seg(11)[:10], fill)   # trunk, neck, skull
        sh.poly(seg(11) + seg(12) + seg(13) + seg(14) + seg(15), fill)                                                               # muzzle and jaw
        sh.poly(seg(1)[-2:] + seg(14)[-6:] + seg(15) + seg(1), fill)
        sh.poly(seg(2), _mix(K["paper"], K["graphite"], 0.12) + (fa,))                                                              # the ear, a shade darker
    # the one line, pressed harder and lighter along its length
    n = len(line)
    i = 0
    w0 = o.get("line", 2.3)
    while i < n - 1:
        j = min(n, i + 4)
        k = 0.78 + 0.5 * _h(i * 0.77 + 2.0)
        sh.line(line[i:j], _mix(K["graphite"], K["paper"], 0.22 * _h(i * 1.3)), w0 * k)
        i = j - 1
    carry = o.get("carry")
    if carry and info["hold"] >= 0.5:
        ts = o.get("thing_scale", 1.0) / 1.15
        hy = THING_HALF.get(carry, (12, 12))[1] * ts
        _thing(sh, carry, (marks["mouth"][0] + 4.0, marks["mouth"][1] - hy + 4.0), 0.0, ts)
    for k, v in marks.items():
        sh.mark(k, v)
    sh.info["hold"] = bool(info["hold"] >= 0.5)
    if o.get("bubbles", True) and o.get("_action") == "breath_out":
        _breath_bubble(sh, marks["mouth"], t)


def bloodhound(target, x, y, action="walk", t=0.0, scale=1.0, facing=1, carry=None, trail=None, stretch=0.0, **kw):
    """Bloodhound drawn as one pencil line. Actions: walk, nose_down, follow, carry,
    wait, swim, breath_out, surface. `trail` is a list of SCREEN points starting near
    the nose; `stretch` 0..1 pays the nose out along it (nose_down and follow)."""
    R = _split(kw)
    o = dict(kw)
    o["carry"] = carry
    o["stretch"] = stretch
    f = 1 if facing >= 0 else -1
    scale = scale * 1.15
    rot = R.get("rot", 0.0)
    local = None
    if trail and stretch > 0:
        ca, sa = math.cos(-rot), math.sin(-rot)
        local = []
        for sx, sy in trail:
            px, py = (sx - x) / (f * scale), (y - sy) / scale
            local.append((px * ca - py * sa, px * sa + py * ca))
    pts, info = _hnd_shape(action, t, o, local)
    origin = (0.0, 0.0)
    if info["anchor"] == "body":
        origin = pts[HND_POINTS + 3]
    elif info["anchor"] == "pin":
        m = pts[HND_POINTS + 1]
        origin = (m[0] - info["pin"][0], m[1] - info["pin"][1])
    sh = Sheet()
    o["_action"] = action
    _hnd_build(sh, pts, info, o, t)
    return _finish(target, sh, x, y, scale, facing, origin, "pencil", R)


def scent_trail(target, pts, upto=1.0, color=None, alpha=150, r=1.3, gap=9.0):
    """The trail the bloodhound follows: faint pencil dashes along SCREEN points, drawn as
    far as `upto` (0..1). It is a mark on the gravel, not a label."""
    img = target.img if hasattr(target, "img") else target
    d = ImageDraw.Draw(img, "RGBA")
    col = tuple(color or COLORS["paper"]) + (alpha,)
    tot = _path_len(pts) * clamp(upto)
    s, k = 0.0, 0
    while s < tot:
        (px, py), a = _path_point(pts, s)
        px += 1.6 * (_h(k * 1.7) - 0.5)
        py += 1.6 * (_h(k * 2.9) - 0.5)
        dx, dy = math.cos(a) * 2.6, math.sin(a) * 2.6
        d.line([(px - dx, py - dy), (px + dx, py + dy)], fill=col, width=max(1, int(round(r * 1.4))))
        s += gap * (0.8 + 0.4 * _h(k))
        k += 1
    if hasattr(target, "d"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


# ================================================================ TERRIER ===
# SCION 32 (forward kinematics). A small stiff dog cut from corrugated card and
# pinned with paper fasteners. It is a joint tree: every part has a parent, a
# pivot offset in the parent's frame, a rest angle and a length, and a pose is
# only a set of joint angles plus the root. World transforms multiply down the
# tree; nothing is solved backwards. The thing in its mouth is a child of the
# head. Root motion while walking is read off the planted foot, so the walk
# does not slide. It is shot on twos, like a card puppet under a camera.
#            name      parent   offset        rest    length
_TER_TREE = [("root", None, (0.0, 0.0), 0.0, 38.0),
             ("neck", "root", (38.0, 4.0), 0.95, 13.0),
             ("head", "neck", (13.0, 0.0), -0.95, 24.0),
             ("jaw", "head", (6.0, -3.0), 0.0, 15.0),
             ("ear", "head", (1.0, 7.0), 1.25, 10.0),
             ("tail", "root", (-3.0, 6.0), 1.5, 22.0),
             ("fnu", "root", (34.0, -7.0), -1.75, 15.0), ("fnl", "fnu", (15.0, 0.0), 0.25, 15.0), ("fnp", "fnl", (15.0, 0.0), 1.45, 6.0),
             ("ffu", "root", (30.0, -7.0), -1.75, 15.0), ("ffl", "ffu", (15.0, 0.0), 0.25, 15.0), ("ffp", "ffl", (15.0, 0.0), 1.45, 6.0),
             ("hnu", "root", (2.0, -8.0), -1.35, 14.0), ("hnl", "hnu", (14.0, 0.0), -0.55, 16.0), ("hnp", "hnl", (16.0, 0.0), 1.75, 6.0),
             ("hfu", "root", (6.0, -8.0), -1.35, 14.0), ("hfl", "hfu", (14.0, 0.0), -0.55, 16.0), ("hfp", "hfl", (16.0, 0.0), 1.75, 6.0)]
TER_BONES = {n: L for n, _, _, _, L in _TER_TREE}
_TER_MOUTH = (23.0, -3.5)            # in the head's frame: where a carried thing is pinned
TER_RATE = 2.6                       # walk cycles per second
_PAW_H = 2.2


def _fk(pose):
    """Forward kinematics. pose: {'x','y','a'} for the root and joint-angle deltas by name.
    Returns {name: (origin, world angle, end point)}."""
    W = {}
    for name, parent, off, rest, L in _TER_TREE:
        if parent is None:
            o_, a = (pose.get("x", 0.0), pose.get("y", 0.0)), pose.get("a", 0.0)
        else:
            po, pa, _ = W[parent]
            o_ = _add(po, _rot(off, pa))
            a = pa + rest + pose.get(name, 0.0)
        W[name] = (o_, a, _add(o_, _u(a, L)))
    return W


_TER_HIND = [0.46]                   # hind swing; tuned once so hind and fore feet cover the same ground


def _ter_planted(c, pair):
    """Which paw of a pair is on the ground at cycle position c (by phase, not by height)."""
    a, b, off = ("fnp", "ffp", 0.0) if pair == "f" else ("hfp", "hnp", 0.0)
    return a if 0.25 <= (c + off) % 1.0 < 0.75 else b


def _ter_stride(pair, n=96):
    tot = 0.0
    for i in range(n):
        Wa, Wb = _fk(dict(_ter_walk_angles(i / n), x=0.0, y=0.0)), _fk(dict(_ter_walk_angles((i + 1) / n), x=0.0, y=0.0))
        foot = _ter_planted((i + 0.5) / n, pair)
        tot -= Wb[foot][0][0] - Wa[foot][0][0]
    return tot


def _ter_walk_angles(c):
    """Joint deltas at cycle position c: a stiff trot, diagonal pairs."""
    p = {}
    for pre, off, amp in (("fn", 0.0, 0.50), ("hf", 0.0, _TER_HIND[0]), ("ff", 0.5, 0.50), ("hn", 0.5, _TER_HIND[0])):
        u = (c + off) % 1.0
        sw = math.sin(TAU * u)                       # + is forward
        swing = max(0.0, math.cos(TAU * u))         # leg in the air, mid-swing, when > 0
        p[pre + "u"] = amp * sw + 0.25 * swing
        p[pre + "l"] = -0.75 * swing if pre[0] == "f" else 0.6 * swing
        p[pre + "p"] = -amp * sw * 0.6 + (0.5 * swing if pre[0] == "f" else -0.6 * swing)
    p["tail"] = 0.07 * (1 if (c * 2) % 1.0 < 0.5 else -1)
    p["neck"] = 0.04 * math.sin(2 * TAU * c)
    return p


def _ground_root(p):
    """Root height that puts the lowest paw joint on the ground."""
    W = _fk(dict(p, x=0.0, y=0.0))
    return -min(W[k][0][1] for k in ("fnp", "ffp", "hnp", "hfp")) + _PAW_H


_ter_table = None


def _ter_gait_table(n=96):
    """Root travel through one cycle, read off whichever forefoot is planted."""
    global _ter_table
    if _ter_table is None:
        lo, hi = 0.25, 0.8
        want = _ter_stride("f")
        for _ in range(30):                      # match the hind sweep to the fore sweep
            _TER_HIND[0] = (lo + hi) / 2
            if _ter_stride("h") < want:
                lo = _TER_HIND[0]
            else:
                hi = _TER_HIND[0]
        xs = [0.0]
        for i in range(n):
            Wa, Wb = _fk(dict(_ter_walk_angles(i / n), x=0.0, y=0.0)), _fk(dict(_ter_walk_angles((i + 1) / n), x=0.0, y=0.0))
            foot = _ter_planted((i + 0.5) / n, "f")
            xs.append(xs[-1] - (Wb[foot][0][0] - Wa[foot][0][0]))
        _ter_table = xs
    return _ter_table


def _ter_travel(c):
    tb = _ter_gait_table()
    n = len(tb) - 1
    whole = math.floor(c)
    f = (c - whole) * n
    i = min(n - 1, int(f))
    return whole * tb[-1] + lerp(tb[i], tb[i + 1], f - i)


def _twos(t):
    return math.floor(t * 12.0 + 1e-6) / 12.0


def _keys(t, keys):
    """Pose in-between over [(time, pose dict)], eased, joint angle by joint angle."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if t < tb:
            w = smooth((t - ta) / (tb - ta))
            return {k: lerp(a.get(k, 0.0), b.get(k, 0.0), w) for k in set(a) | set(b)}
    return dict(keys[-1][1])


_TER_SIT = dict(a=0.55, hnu=0.5, hnl=-1.75, hnp=0.85, hfu=0.5, hfl=-1.75, hfp=0.85,
                fnu=-0.42, fnl=-0.2, fnp=0.1, ffu=-0.36, ffl=-0.2, ffp=0.1, neck=-0.2, head=-0.3, tail=-0.45)
_TER_LIMP = dict(fnu=0.25, fnl=-0.3, ffu=0.1, ffl=-0.3, hnu=-0.5, hnl=0.5, hfu=-0.35, hfl=0.5)


def _ter_pose(action, t, o):
    """The pose (root + joint deltas) and bookkeeping for this moment."""
    carry = o.get("carry")
    info = dict(X=0.0, anchor="ground", hold=1.0 if carry else 0.0, water=0, pin=None, clip=False, stand=None)
    if o.get("twos", True):
        t = _twos(t)
    p = {}
    if action in ("walk", "carry"):
        c = t * o.get("rate", TER_RATE) + o.get("phase", 0.0)
        p = _ter_walk_angles(c)
        info["X"] = _ter_travel(c) - _ter_travel(o.get("phase", 0.0))
        if carry or action == "carry":
            p["neck"] = p.get("neck", 0.0) + 0.12
            p["head"] = 0.12
            p["jaw"] = -0.30
        p["y"] = _ground_root(p)
    elif action == "wait":
        w = smooth(t / 0.5) if o.get("sit", False) else 0.0
        p = {k: v * w for k, v in _TER_SIT.items()}
        if carry:
            p["jaw"] = -0.30
        p["ear"] = 0.5 * bell(t, 1.4, 1.5, 1.6, 1.75)                    # one ear flick, then nothing
        p["y"] = _ground_root(p) - 1.5 * w
    elif action == "warm":
        w = o.get("warm", 4.0)
        k = 1 - ease(t, 0.3 * w, w)
        s_ = (1 if int(round(t * 12)) % 2 else -1) * k
        cold = dict(a=0.05, neck=-0.35, head=-0.25, tail=2.0, ear=-0.5, fnu=0.12, ffu=0.12, hnu=-0.12, hfu=-0.12)
        p = {key: cold.get(key, 0.0) * k + _TER_SIT.get(key, 0.0) * (1 - k) for key in set(cold) | set(_TER_SIT)}
        p["a"] += 0.035 * s_
        p["x"] = 0.8 * s_
        p["y"] = _ground_root(p) - 1.5 * (1 - k)
    elif action == "dive":
        info["clip"] = True
        stand_y = _ground_root({})
        kick = 0.6 * math.sin(TAU * 5.0 * t) * bell(t, 0.5, 0.7, 1.2, 1.4)
        ks = [(0.0, dict(x=-56.0, y=stand_y)),
              (0.24, dict(x=-56.0, y=stand_y - 4.0, a=0.16, neck=-0.5, head=-0.3, fnu=0.4, fnl=-0.8, ffu=0.4, ffl=-0.8, hnu=-0.2, hnl=0.4, hfu=-0.2, hfl=0.4)),
              (0.52, dict(x=-30.0, y=stand_y + 12.0, a=-0.95, neck=-0.75, head=0.55, fnu=1.1, fnl=0.3, ffu=1.1, ffl=0.3, tail=0.95, hnu=-0.3, hfu=-0.3)),
              (0.85, dict(x=-9.0, y=27.0, a=-1.45, neck=-0.9, head=0.9, fnu=1.3, ffu=1.3, tail=1.45, hnu=0.3, hfu=-0.3)),
              (1.25, dict(x=0.0, y=3.0, a=-1.55, neck=-0.9, head=0.9, fnu=1.3, ffu=1.3, tail=1.55, hnu=0.2, hfu=-0.2)),
              (1.6, dict(x=0.0, y=-34.0, a=-1.55, neck=-0.9, head=0.9, fnu=1.3, ffu=1.3, tail=1.55))]
        if o.get("stay", False):                                        # the tail is left sticking out of the hole
            ks = ks[:4] + [(1.25, dict(ks[4][1], y=-9.0, hnu=-0.9, hfu=-0.9, hnl=0.9, hfl=0.9))]
        p = _keys(t, ks)
        p["hnu"] = p.get("hnu", 0.0) + kick
        p["hfu"] = p.get("hfu", 0.0) - kick
        if o.get("stay", False) and t > 1.25:
            p["tail"] = p.get("tail", 0.0) + 0.28 * math.sin(TAU * 2.5 * t)
    elif action == "come_up":
        info["clip"] = True
        stand_y = _ground_root({})
        jw = -0.30 if carry else 0.0
        ks = [(0.0, dict(x=0.0, y=-64.0, a=1.5, neck=-0.8, head=0.85, jaw=jw, tail=-1.5, fnu=0.6, ffu=0.6)),
              (0.30, dict(x=0.0, y=-26.0, a=1.5, neck=-0.8, head=0.85, jaw=jw, tail=-1.5, fnu=0.9, ffu=0.9)),
              (0.42, dict(x=0.0, y=-26.0, a=1.5, neck=-0.6, head=0.45, jaw=jw, tail=-1.5, fnu=0.9, ffu=0.9)),      # it looks about
              (0.72, dict(x=4.0, y=6.0, a=1.15, neck=-0.5, head=-0.1, jaw=jw, tail=-1.1, fnu=1.5, fnl=0.3, ffu=1.4, ffl=0.3, hnu=-0.4, hfu=-0.4)),
              (1.0, dict(x=34.0, y=stand_y + 13.0, a=0.3, jaw=jw, tail=-0.2, fnu=0.6, ffu=0.7, hnu=-0.7, hfu=-0.6, hnl=0.5, hfl=0.5)),
              (1.2, dict(x=56.0, y=stand_y - 3.5, a=-0.05, jaw=jw, neck=-0.2, fnu=0.25, fnl=-0.5, ffu=0.25, ffl=-0.5, hnu=-0.25, hnl=0.5, hfu=-0.25, hfl=0.5)),
              (1.4, dict(x=56.0, y=stand_y, jaw=jw, neck=0.22, head=0.2))]
        p = _keys(t, ks)
        p["tail"] = p.get("tail", 0.0) + 0.10 * math.sin(TAU * 6.0 * t) * bell(t, 1.4, 1.5, 2.0, 2.2)     # tail quivers: got it
        info["stand"] = (56.0, 0.0)
    elif action == "swim":
        info.update(anchor="body", water=1, X=o.get("speed", 46.0) * t)
        a = TAU * 1.8 * t
        p = dict(a=o.get("pitch", 0.0) + 0.05 * math.sin(a * 0.5), tail=-1.25, ear=-0.9, neck=-0.25, head=0.2 - 0.5 * o.get("pitch", 0.0),
                 fnu=0.75 + 0.55 * math.sin(a), fnl=-0.5 - 0.4 * math.cos(a), ffu=0.75 - 0.55 * math.sin(a), ffl=-0.5 + 0.4 * math.cos(a),
                 hnu=-0.75 + 0.45 * math.sin(a + 1.2), hnl=0.6, hfu=-0.75 - 0.45 * math.sin(a + 1.2), hfl=0.6, fnp=-0.9, ffp=-0.9, hnp=-1.2, hfp=-1.2)
        if carry:
            p["jaw"] = -0.30
    elif action == "breath_out":
        info.update(anchor="body", water=1, hold=0.0)
        w = ease(t, 0.62, 1.9)
        p = {k: v * w for k, v in _TER_LIMP.items()}
        for k in ("fnp", "ffp", "hnp", "hfp"):
            p[k] = -0.9 * w
        p["a"] = 0.6 * w
        p["head"] = 0.08 * bell(t, 0.0, 0.2, 0.42, 0.5) * math.sin(TAU * 6 * t) + 0.35 * w
        p["jaw"] = -0.7 * bell(t, 0.48, 0.56, 1.3, 2.0) - 0.12 * w
        p["tail"] = -1.6 * w
        p["ear"] = -0.8 * w
        if t < 0.6:                                                     # still holding on: paddling harder
            a = TAU * 3.0 * t
            p.update(fnu=0.75 + 0.5 * math.sin(a), ffu=0.75 - 0.5 * math.sin(a), fnl=-0.6, ffl=-0.6, hnu=-0.6, hfu=-0.6, hnl=0.5, hfl=0.5)
    elif action == "surface":
        tt = max(0.0, t)
        info.update(anchor="pin", hold=0.0,
                    pin=(0.0, -6.0 + 16.0 * (1 - math.exp(-4.5 * tt) * math.cos(7.0 * tt)) + 1.0 * math.sin(2.2 * t)))
        a = TAU * 2.2 * t
        p = dict(a=1.05, neck=-0.55, head=-0.25, jaw=-0.12 - 0.5 * abs(math.sin(TAU * 1.5 * t)) * math.exp(-0.45 * tt), tail=-1.0, ear=-0.5,
                 fnu=1.2 + 0.4 * math.sin(a), fnl=-0.5, ffu=1.2 - 0.4 * math.sin(a), ffl=-0.5, hnu=-0.4 + 0.3 * math.sin(a), hfu=-0.4 - 0.3 * math.sin(a))
    else:
        p["y"] = _ground_root(p)
    if "y" not in p:
        p.setdefault("y", 0.0)
    p["head"] = p.get("head", 0.0) + o.get("look", 0.0)
    return p, info


def _ter_build(sh, W, info, o, t):
    K = COLORS

    def card(pts, far=False, col=None):
        face = col or (K["card_far"] if far else K["card"])
        sh.poly([(q[0] + 1.3, q[1] - 1.7) for q in pts], K["card_edge"], None)          # the cut edge: card has thickness
        sh.poly(pts, face, _mix(face, K["card_edge"], 0.7), 0.6)

    def frame(name, pts):
        o_, a, _ = W[name]
        return [_add(o_, _rot(q, a)) for q in pts]

    def bone(name, wa, wb, far=False):
        o_, a, e = W[name]
        card(_bar(_add(o_, _u(a, -2.0)), _add(e, _u(a, 1.5)), wa, wb, 1.6), far)

    def leg(pre, far):
        bone(pre + "u", 7.5, 6.0, far)
        bone(pre + "l", 6.0, 4.8, far)
        card(frame(pre + "p", [(-2.5, 2.4), (7.5, 2.2), (8.5, -1.0), (7.0, -2.4), (-2.5, -2.4)]), far)

    leg("ff", True)
    leg("hf", True)
    bone("tail", 5.2, 3.4)
    card(frame("root", [(-7, 9), (16, 10), (41, 11), (47, 4), (45, -8), (30, -11), (4, -9), (-8, -2)]))
    for k in range(9):                                                                      # flutes
        xx = -3.0 + k * 5.6
        sh.line(frame("root", [(xx, 8.0), (xx + 1.0, -7.5)]), K["flute"], 0.55, True)
    sh.poly(frame("root", [(5, 9.6), (29, 10.6), (27, 3), (9, 2)]), K["marker"], None, 0, True)         # saddle, drawn on in marker
    bone("neck", 12.0, 10.0)
    card(frame("jaw", [(-3, 1.5), (15, 1.5), (16, -1.5), (13, -3.5), (-3, -3.5)]), True)
    ho, ha, _ = W["head"]
    mouth = _add(ho, _rot(_TER_MOUTH, ha))
    carry = o.get("carry")
    if carry and info["hold"] >= 0.5:
        ts = o.get("thing_scale", 1.0)
        hx, hy = THING_HALF.get(carry, (12, 12))
        if carry == "fix":
            _thing(sh, carry, _add(mouth, _rot((5.0 * ts, -5.0 * ts), ha)), ha, ts)
        else:
            _thing(sh, carry, _add(mouth, _rot(((hx - 2.0) * ts, 2.0 * ts), ha)), ha, ts)
    card(frame("head", [(-7, 8), (7, 9.5), (12, 6.5), (24, 6.5), (27, 3), (26, -3), (23, -8.5), (20, -4), (17, -9), (14, -4.5), (11, -8), (8, -4), (-6, -5)]))
    sh.line(frame("head", [(5.0, 6.8), (9.5, 5.0), (13.5, 6.2)]), K["marker"], 1.3, True)               # brow
    sh.dot(frame("head", [(9.5, 3.2)])[0], 1.7, K["eye"], None, 0, True)
    sh.poly(frame("head", [(23.5, 6.8), (27.6, 5.6), (27.8, 1.8), (24.0, 2.0)]), K["nose"], None)
    card(frame("ear", [(-2.5, -3.5), (10, -1), (4.5, 1.0), (7.5, 5.5), (-2.5, 4.0)]), col=K["marker"])
    leg("hn", False)
    leg("fn", False)
    for nm in ("neck", "head", "tail", "fnu", "fnl", "hnu", "hnl", "ear"):
        sh.dot(W[nm][0], 1.5, K["pin"], _mix(K["pin"], (60, 30, 0), 0.6), 0.4, True)
    sh.mark("mouth", mouth)
    sh.mark("nose", frame("head", [(27.0, 4.0)])[0])
    sh.mark("head", frame("head", [(8.0, 2.0)])[0])
    sh.mark("body", frame("root", [(19.0, 0.0)])[0])
    sh.mark("tail", W["tail"][2])
    sh.mark("eye", frame("head", [(9.5, 3.2)])[0])
    if info["stand"]:
        sh.mark("stand", info["stand"])
    sh.info["hold"] = bool(info["hold"] >= 0.5)
    if o.get("bubbles", True) and o.get("_action") == "breath_out":
        _breath_bubble(sh, mouth, t, big=9.0)


def terrier(target, x, y, action="walk", t=0.0, scale=1.0, facing=1, carry=None, **kw):
    """Small stiff jointed card terrier. Actions: walk, carry, wait (sit=True to sit),
    dive (stay=True leaves the tail out), come_up, swim, breath_out, surface.
    For dive and come_up, (x, y) is the mouth of the hole at ground level."""
    R = _split(kw)
    o = dict(kw)
    o["carry"] = carry
    p, info = _ter_pose(action, t, o)
    W = _fk(p)
    origin = (0.0, 0.0)
    if info["anchor"] == "body":
        origin = _add(W["root"][0], _rot((19.0, 0.0), W["root"][1]))
    elif info["anchor"] == "pin":
        ho, ha, _ = W["head"]
        m = _add(ho, _rot(_TER_MOUTH, ha))
        origin = (m[0] - info["pin"][0], m[1] - info["pin"][1])
    if info["clip"] and "clip" not in R:
        R["clip"] = (None, None, None, y + 1)
    sh = Sheet()
    o["_action"] = action
    _ter_build(sh, W, info, o, _twos(t) if o.get("twos", True) else t)
    return _finish(target, sh, x, y, scale, facing, origin, "card", R)


# ================================================================ helpers ===
UNIT = {"retriever": 1.25, "sheepdog": 1.45, "bloodhound": 1.15, "terrier": 1.0}
DOGS = {"retriever": retriever, "sheepdog": sheepdog, "bloodhound": bloodhound, "terrier": terrier}
ACTIONS = {
    "retriever": ("walk", "carry", "wait", "set_down", "proud", "told", "warm", "swim", "breath_out", "surface"),
    "sheepdog": ("walk", "run_line", "nudge", "wait", "carry", "warm", "swim", "breath_out", "surface"),
    "bloodhound": ("walk", "nose_down", "follow", "carry", "wait", "warm", "swim", "breath_out", "surface"),
    "terrier": ("walk", "carry", "wait", "dive", "come_up", "warm", "swim", "breath_out", "surface"),
}
DURATION = {("retriever", "set_down"): 2.5, ("retriever", "told"): 1.2, ("retriever", "wait"): 1.6,
            ("sheepdog", "nudge"): 2.6, ("sheepdog", "wait"): 1.8,
            ("bloodhound", "nose_down"): 2.0, ("bloodhound", "wait"): 0.8,
            ("terrier", "dive"): 1.6, ("terrier", "come_up"): 2.2, ("terrier", "wait"): 0.5}
for _d in DOGS:
    DURATION[(_d, "breath_out")] = 2.0
    DURATION[(_d, "warm")] = 4.0


def draw(dog, target, x, y, action="walk", t=0.0, **kw):
    """Call a dog by name: kb.draw('terrier', ink, x, y, 'dive', t)."""
    return DOGS[dog](target, x, y, action, t, **kw)


def travel(dog, action, t, **o):
    """Dog units covered along the ground (or through the water) by time t, so that
    x = x0 + facing * scale * travel(...) keeps wheels and planted feet from sliding.
    The result is in the lead dog's units (each make's own unit factor, and the retriever's
    size=, are already applied)."""
    if dog == "retriever":
        size = o.pop("size", "big")
        return _ret_prim(action, t, o)["X"] * UNIT[dog] * RET_SIZE.get(size, size if isinstance(size, (int, float)) else 1.0)
    if dog == "sheepdog":
        return _shp_prim(action, t, o)["X"] * UNIT[dog]
    if dog == "bloodhound":
        return (_hnd_shape(action, t, o)[1]["X"] if action in ("walk", "carry", "follow", "swim") else 0.0) * UNIT[dog]
    if dog == "terrier":
        return _ter_pose(action, t, o)[1]["X"]
    raise KeyError(dog)


# ================================================================== sheet ===

def _bg(w, h, kind):
    px = np.zeros((h, w, 3), np.float32)
    top, bot = {"dusk": ((58, 48, 98), (232, 150, 108)), "water": ((38, 132, 138), (14, 60, 78)),
                "sil": ((236, 230, 218), (236, 230, 218))}[kind]
    for c in range(3):
        px[..., c] = np.linspace(top[c], bot[c], h)[:, None]
    return Image.fromarray(px.astype(np.uint8))


_SHEET = {
    "retriever": [("walk", 0.55, {}), ("carry", 0.5, dict(carry="piece")), ("wait", 0.2, {}), ("set_down", 0.95, dict(carry="piece")),
                  ("proud", 0.4, dict(carry="reel")), ("told", 1.2, dict(carry="reel")), ("swim", 0.6, dict(carry="piece")),
                  ("breath_out", 1.1, {}), ("surface", 0.3, {}), ("warm", 0.4, {})],
    "sheepdog": [("walk", 0.5, {}), ("run_line", 0.5, {}), ("nudge", 0.95, {}), ("wait", 0.16, {}), ("carry", 0.5, dict(carry="reel")),
                 ("swim", 0.6, {}), ("breath_out", 1.1, {}), ("surface", 0.3, {}), ("warm", 0.4, {})],
    "bloodhound": [("walk", 0.5, {}), ("nose_down", 1.3, {}), ("follow", 0.6, dict(_trail=True)), ("carry", 0.5, dict(carry="piece")),
                   ("wait", 1.0, {}), ("swim", 0.6, {}), ("breath_out", 0.5, {}), ("surface", 0.3, {}), ("warm", 0.4, {})],
    "terrier": [("walk", 0.4, {}), ("carry", 0.4, dict(carry="fix")), ("wait", 1.0, dict(sit=True)), ("dive", 0.85, {}),
                ("come_up", 0.72, dict(carry="fix")), ("swim", 0.6, {}), ("breath_out", 1.1, {}), ("surface", 0.3, {}), ("warm", 0.4, {})],
}
_WET = ("swim", "breath_out", "dive", "come_up", "nudge", "follow", "nose_down")


def _cell(dog, action, t, opts, cw, ch, sil, scale, label=None):
    wet = action in _WET or (dog != "retriever" and action in ("walk", "wait", "carry") and False)
    kind = "sil" if sil else ("water" if (wet or action == "surface") else "dusk")
    cell = _bg(cw, ch, kind)
    d = ImageDraw.Draw(cell)
    gy = ch - 40
    opts = dict(opts)
    kw = {}
    if sil:
        kw["silhouette"] = True
    elif wet:
        kw.update(tint=WATER, tint_amount=0.3, shadow=False)
    x, y = cw * 0.42, gy
    if action in ("swim", "breath_out"):
        y = ch * 0.56
    elif action == "surface":
        y = ch * 0.42
        if not sil:
            d.rectangle([0, 0, cw, y], fill=(96, 78, 120))
        d.line([(0, y), (cw, y)], fill=(230, 244, 240) if not sil else (150, 150, 150), width=2)
        x = cw * 0.56
    elif action in ("dive", "come_up"):
        x = cw * 0.5
        d.line([(0, gy), (cw, gy)], fill=(40, 34, 48), width=2)
        d.ellipse([x - 20 * scale / 0.8, gy - 3, x + 20 * scale / 0.8, gy + 9], fill=(10, 24, 32) if not sil else (120, 116, 110))
    else:
        d.line([(0, gy), (cw, gy)], fill=(40, 34, 48) if not sil else (150, 146, 138), width=2)
    if opts.pop("_trail", False):
        tr = [(x + 92 * scale, gy - 2), (x + 130 * scale, gy - 3), (x + 175 * scale, gy - 2)]
        if not sil:
            scent_trail(cell, [(x + 80 * scale, gy - 2)] + tr + [(x + 260 * scale, gy - 2)])
        opts.update(trail=tr, stretch=0.8)
        x = cw * 0.26
    if action == "nudge":
        j0 = DOGS[dog](Image.new("RGB", (8, 8)), x, y, action, t, scale=scale, **opts)
        draw_thing(cell, "piece", x + 112 * scale + j0["push"], gy, scale, silhouette=sil, **({} if sil else dict(tint=WATER, tint_amount=0.3)))
    DOGS[dog](cell, x, y, action, t, scale=scale, **opts, **kw)
    ImageDraw.Draw(cell).text((6, 4), label or action, fill=(250, 246, 236) if not sil else (60, 56, 60))
    return cell


def _sheet(path=None):
    cw, ch = 250, 190
    rows = []
    for dog, cells in _SHEET.items():
        for sil in (False, True):
            row = Image.new("RGB", (cw * 10, ch), (236, 230, 218))
            for i, (action, t, opts) in enumerate(cells):
                sc = 0.8 if dog != "terrier" else 1.0
                row.paste(_cell(dog, action, t, opts, cw, ch, sil, sc, "%s · %s" % (dog, action)), (i * cw, 0))
            rows.append(row)
    sheet = Image.new("RGB", (cw * 10, ch * len(rows)), (236, 230, 218))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, i * ch))
    path = path or (HERE / "kennel_b_sheet.png")
    sheet.save(path)
    return path


def _filmstrip(name, dog, action, times, opts=None, cw=250, ch=190, scale=0.8):
    opts = opts or {}
    img = Image.new("RGB", (cw * len(times), ch))
    for i, t in enumerate(times):
        img.paste(_cell(dog, action, t, opts, cw, ch, False, scale, "%s %.2fs" % (action, t)), (i * cw, 0))
    p = HERE / ("kennel_b_strip_%s.png" % name)
    img.save(p)
    return p


def _standin_cow(img, x, y, s=1.0, facing=-1, head=0.0):
    """A flat stand-in cow for scale only (hooves at y, middle at x). The film's cows are the cow builder's."""
    d = ImageDraw.Draw(img, "RGBA")
    f = facing
    hide, patch, dark = (150, 96, 70), (236, 226, 208), (60, 40, 38)
    for lx in (-78, -58, 52, 72):
        d.rectangle([x + f * lx * s - 7 * s, y - 80 * s, x + f * lx * s + 7 * s, y], fill=dark if lx in (-58, 52) else hide)
    d.ellipse([x - 100 * s, y - 170 * s, x + 100 * s, y - 62 * s], fill=hide)
    d.ellipse([x - 40 * s, y - 160 * s, x + 30 * s, y - 100 * s], fill=patch)
    hx, hy = x + f * 118 * s, y - (118 - 60 * head) * s
    d.polygon([(x + f * 70 * s, y - 160 * s), (x + f * 96 * s, y - 100 * s), (hx, hy + 14 * s), (hx, hy - 30 * s)], fill=hide)
    d.ellipse([hx - 26 * s, hy - 34 * s, hx + 26 * s, hy + 34 * s], fill=hide)
    d.ellipse([hx + f * 6 * s - 15 * s, hy + 10 * s, hx + f * 6 * s + 15 * s, hy + 36 * s], fill=(214, 170, 160))
    d.line([(hx - f * 10 * s, hy - 30 * s), (hx - f * 22 * s, hy - 50 * s), (hx - f * 6 * s, hy - 60 * s)], fill=patch, width=max(2, int(5 * s)))
    d.line([(hx + f * 10 * s, hy - 30 * s), (hx + f * 20 * s, hy - 52 * s)], fill=patch, width=max(2, int(5 * s)))
    d.ellipse([hx - f * 8 * s - 3 * s, hy - 10 * s, hx - f * 8 * s + 3 * s, hy - 4 * s], fill=dark)
    d.ellipse([hx - f * 24 * s - 7 * s, hy + 34 * s, hx - f * 24 * s + 7 * s, hy + 50 * s], fill=(206, 170, 86))
    return (hx + f * 8 * s, hy + 30 * s)


def _cow_strip():
    """The eleven who ran out of breath, on the bank, with the cows round them (S5): three film-size frames."""
    W_, H_ = 960, 400
    times = (0.3, 2.4, 5.2)
    img = Image.new("RGB", (W_, H_ * len(times)))
    for i, t in enumerate(times):
        fr = _bg(W_, H_, "dusk")
        d = ImageDraw.Draw(fr)
        gy = 330
        d.rectangle([0, gy, W_, H_], fill=(86, 74, 78))
        _standin_cow(fr, 150, gy - 6, 0.95, 1, head=0.6)
        _standin_cow(fr, 800, gy - 6, 1.0, -1, head=0.75)
        _standin_cow(fr, 470, gy - 14, 0.9, -1, head=0.2)
        places = [("bloodhound", 300, gy + 12, 1, 0.62, 1), ("terrier", 420, gy + 30, 1, 0.9, -1),
                  ("sheepdog", 560, gy + 18, 1, 0.62, 1), ("retriever", 668, gy + 34, 1, 0.6, 1)]
        for dog, x, y, f, sc, cow in places:
            x += f * sc * travel(dog, "warm", t, cow=cow)
            DOGS[dog](fr, x, y, "warm", t, scale=sc, facing=f, cow=cow)
        img.paste(fr, (0, i * H_))
    p = HERE / "kennel_b_strip_cows.png"
    img.save(p)
    return p


def _selftest():
    out = []
    blank = Image.new("RGB", (64, 64))
    # every dog, every action, draws and returns a mouth
    for dog, acts in ACTIONS.items():
        for a in acts:
            for t in (0.0, 0.7, 2.4):
                j = DOGS[dog](blank, 32, 32, a, t, scale=0.3)
                assert "mouth" in j and "bbox" in j, (dog, a)
    out.append("MEASURED all %d dog/action pairs draw at t = 0, 0.7, 2.4" % sum(len(a) for a in ACTIONS.values()))
    # retriever: follow-through starts after the stop begins, and all of it has died away later
    o = dict(carry=None)
    prim = lambda tt: _ret_prim("wait", tt, o)                      # noqa: E731
    before = _simulate(prim, _ret_geom, _RET_SPECS, -0.02)
    during = _simulate(prim, _ret_geom, _RET_SPECS, 0.45)
    after = _simulate(prim, _ret_geom, _RET_SPECS, 2.4)
    sp = lambda S: max(abs(S[k + "_v"]) for k in ("neck", "ear", "tail", "bead"))      # noqa: E731
    assert sp(during) > 0.4 > 0.08 > sp(after), (sp(before), sp(during), sp(after))
    out.append("MEASURED retriever stop: loose-part speed %.2f rad/s rolling, %.2f at 0.45 s (after the body has stopped at 0.32 s), %.3f at 2.4 s" % (sp(before), sp(during), sp(after)))
    # sheepdog: planted feet do not slip; energy decays
    slip = 0.0
    for k in range(200):
        t0, t1 = k * 0.01, k * 0.01 + 0.01
        P0, P1 = _shp_prim("walk", t0, {}), _shp_prim("walk", t1, {})
        for i in range(4):
            if P0["feet"][i][1] == 0.0 and P1["feet"][i][1] == 0.0:
                slip = max(slip, abs((P1["feet"][i][0] + P1["X"]) - (P0["feet"][i][0] + P0["X"])))
    assert slip < 1e-6, slip
    prim = lambda tt: _shp_prim("wait", tt, {})                     # noqa: E731
    d_, a_ = _simulate(prim, _shp_geom, _SHP_SPECS, 0.4), _simulate(prim, _shp_geom, _SHP_SPECS, 2.6)
    e = lambda S: sum(abs(v) for k, v in S.items() if k.endswith("_v") and k[0] in "fg")       # noqa: E731
    assert e(d_) > 10 * e(a_), (e(d_), e(a_))
    out.append("MEASURED sheepdog: planted-foot slip %.1e units; fringe speed sum %.2f at 0.4 s, %.3f at 2.6 s; body lurch %.1f units" % (slip, e(d_), e(a_), max(abs(_simulate(prim, _shp_geom, _SHP_SPECS, 0.2 + 0.05 * k)["bodyx"]) for k in range(8))))
    # bloodhound: every drawing has the same points; the nose reaches the end of the trail
    for a in ACTIONS["bloodhound"]:
        for t in (0.0, 0.33, 0.9, 1.7):
            assert len(_hnd_shape(a, t, {})[0]) == HND_POINTS + len(_HND_MARKS)
    tr = [(100.0, 0.0), (160.0, 2.0), (240.0, 0.0)]
    nose = _hnd_shape("nose_down", 2.2, dict(stretch=1.0), tr)[0][HND_POINTS]
    assert math.hypot(nose[0] - 240.0, nose[1]) < 9.0, nose
    slip = 0.0
    for k in range(100):
        A, B = _hnd_walk_key(0, 8, 56.0, 9.0), _hnd_walk_key(1, 8, 56.0, 9.0)
        w0, w1 = k / 100.0, (k + 1) / 100.0
        x0 = lerp(A["hf"][0], B["hf"][0], w0) + 56.0 * w0 / 8
        x1 = lerp(A["hf"][0], B["hf"][0], w1) + 56.0 * w1 / 8
        slip = max(slip, abs(x1 - x0))
    out.append("MEASURED bloodhound: %d points in every drawing of every action; nose tip %.1f units from the trail's end at stretch 1; planted foot slip between keys %.1e" % (HND_POINTS, math.hypot(nose[0] - 240.0, nose[1]), slip))
    # terrier: bone lengths never change; the carried thing stays pinned to the head; the planted forefoot does not slide
    worst = 0.0
    for a in ACTIONS["terrier"]:
        for k in range(60):
            p, _ = _ter_pose(a, k * 0.05, dict(carry="fix", twos=False))
            W = _fk(p)
            for name, (o_, ang, e_) in W.items():
                worst = max(worst, abs(math.hypot(e_[0] - o_[0], e_[1] - o_[1]) - TER_BONES[name]))
            for name, parent, off, rest, L in _TER_TREE:
                if parent:
                    po, pa, _ = W[parent]
                    worst = max(worst, math.hypot(*(_add(po, _rot(off, pa))[i] - W[name][0][i] for i in (0, 1))))
    assert worst < 1e-9, worst
    slip = hslip = 0.0
    n = 96
    _ter_gait_table()
    for i in range(n):
        ca, cb = i / n, (i + 1) / n
        Wa = _fk(dict(_ter_walk_angles(ca), x=_ter_travel(ca), y=0.0))
        Wb = _fk(dict(_ter_walk_angles(cb), x=_ter_travel(cb), y=0.0))
        slip = max(slip, abs(Wb[_ter_planted((i + 0.5) / n, "f")][0][0] - Wa[_ter_planted((i + 0.5) / n, "f")][0][0]))
        hslip = max(hslip, abs(sum(Wb[_ter_planted((i + 0.5) / n, "h")][0][0] - Wa[_ter_planted((i + 0.5) / n, "h")][0][0] for _ in (0,))))
    assert slip < 1e-6, slip
    out.append("MEASURED terrier: bone length and pivot error %.1e over all actions; planted forefoot slip %.1e; worst hind foot slip %.2f units per 1/96 cycle (stride %.1f)" % (worst, slip, hslip, _ter_gait_table()[-1]))
    return out


if __name__ == "__main__":
    for line in _selftest():
        print(line)
    print("sheet ->", _sheet())
    for args in [("set_down", "retriever", "set_down", [0.0, 0.3, 0.6, 0.9, 1.1, 1.4, 1.8, 2.4], dict(carry="piece")),
                 ("stop", "retriever", "wait", [-0.1, 0.1, 0.25, 0.4, 0.55, 0.75, 1.0, 1.6], {}),
                 ("sizes", "retriever", "carry", [0.3], dict(carry="piece")),
                 ("nudge", "sheepdog", "nudge", [0.0, 0.2, 0.45, 0.75, 1.0, 1.25, 1.6, 2.2], {}),
                 ("run", "sheepdog", "run_line", [0.5, 0.56, 0.62, 0.68, 0.74, 0.8], {}),
                 ("nose", "bloodhound", "nose_down", [0.0, 0.4, 0.8, 1.05, 1.3, 2.0], {}),
                 ("dive", "terrier", "dive", [0.0, 0.25, 0.5, 0.67, 0.85, 1.1, 1.25, 1.6], {}),
                 ("comeup", "terrier", "come_up", [0.0, 0.3, 0.42, 0.72, 1.0, 1.2, 1.4, 2.0], dict(carry="fix")),
                 ("breath", "bloodhound", "breath_out", [0.0, 0.3, 0.5, 0.62, 0.9, 1.3, 1.9], {})]:
        print("strip ->", _filmstrip(*args))
    print("strip ->", _filmstrip("warm", "terrier", "warm", [0.2, 1.2, 2.2, 3.0, 4.0, 5.0], {}, scale=1.0))
    print("strip ->", _cow_strip())
