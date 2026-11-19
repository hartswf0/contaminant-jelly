"""p01 · Bow · Giant Size 11 Rubber Boot blocking beam.

Lineage: comic cutout collage. Rule: Silhouette (SCION 02), backlit shadow.

Foraged (Wikimedia Commons, see credits/p01.json): a lithographed rubber-boot advertisement,
a Denton brook trout plate, an Everdingen etching (stones), Audubon's wild turkey (Turkey's
head), an 1880 scissors cut. Everything is cut with straight scissor facets, hinged with pins
and laid on a light table. Handmade: the bread-roll tin, the brass porthole, pins, tissue water.

Three parts: 1 the boot is cut out and the scene laid on the glass under top light;
2 the lamp under the glass comes on and Turkey looks out through the porthole;
3 the trout look in from the river side.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit_anim import *  # noqa
import cv2

SLUG = "p01"
SRC = HERE / "sources" / SLUG
SECONDS = 31.0
P2, P3 = 11.0, 21.0          # part boundaries
rs = np.random.RandomState(7)

CAPTIONS = [
    (1.2, 4.6, "A rubber boot, cut out of an old Boston Rubber Shoe Co. poster."),
    (14.6, 19.6, "Turkey: Shipwreck? Giant's foot? Or a tunnel?"),
    (23.2, 28.6, "Trout: Is its sole a torch, or is a crab biting its toe?"),
]
for a, b, _ in CAPTIONS:
    assert b - a >= 2.5
for (a, b, _), (c, d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert c > b

ANKLE_LIMIT = 26.0           # degrees, the pinned joint cannot fold further


def ankle(rel):
    return max(-ANKLE_LIMIT, min(ANKLE_LIMIT, rel))


# ------------------------------------------------------------------ cutting ---

def poly_to_mask(size, pts, ss=3):
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return m.resize(size, Image.LANCZOS)


def facet(mask, grow=4, eps=2.2):
    """Grow a mask by a paper margin and re-cut it with straight scissor facets."""
    a = (np.asarray(mask) > 127).astype(np.uint8)
    if grow:
        a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
    cs, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    ap = cv2.approxPolyDP(c, eps, True)[:, 0, :]
    return [(float(x), float(y)) for x, y in ap]


def paper_edge(rgb, mask, core=(244, 238, 224)):
    """The white core of the paper shows along a cut: lighten a thin rim, darken the far side."""
    a = np.asarray(mask, np.float32) / 255
    er = cv2.erode(a, np.ones((3, 3), np.uint8))
    rim = np.clip(a - er, 0, 1)[..., None]
    sh = np.roll(np.roll(a, -2, 0), -2, 1)
    lo = np.clip(a - sh, 0, 1)[..., None] * 0.35          # lower-right edge in shade
    out = np.asarray(rgb, np.float32)
    out = out * (1 - rim * 0.8) + np.array(core, np.float32) * rim * 0.8
    out = out * (1 - lo)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


class Piece:
    """A cut piece of paper with a pin point. Knows its top-lit face and its backlit shadow."""

    def __init__(self, rgba, pivot, name=""):
        self.im = rgba
        self.pivot = pivot
        self.name = name
        a = np.asarray(rgba, np.float32)
        d = a[..., :3] * 0.13 + np.array([8, 13, 14], np.float32)
        self.dark = Image.fromarray(np.dstack([d, a[..., 3]]).clip(0, 255).astype(np.uint8), "RGBA")
        self._c = {}

    def get(self, ang=0.0, s=1.0, flip=False, dark=False):
        key = (round(ang, 1), round(s, 3), flip, dark)
        if key in self._c:
            return self._c[key]
        im = self.dark if dark else self.im
        px, py = self.pivot
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            px = im.width - px
        w, h = max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))
        sc = im.resize((w, h), Image.LANCZOS if s < 1 else Image.BICUBIC)
        a = math.radians(ang)
        vx, vy = px * s - w / 2, py * s - h / 2
        if abs(ang) > 0.05:
            sc = sc.rotate(-ang, expand=True, resample=Image.BICUBIC)
        rx, ry = vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)
        out = (sc, (sc.width / 2 + rx, sc.height / 2 + ry))
        if len(self._c) > 160:
            self._c.clear()
        self._c[key] = out
        return out


def cut_piece(src, mask, pivot, name="", edge=True):
    """Cut `mask` (L image, source size) out of src; pivot in source coords."""
    box = mask.getbbox()
    rgb = src.crop(box)
    m = mask.crop(box)
    if edge:
        rgb = paper_edge(rgb, m)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(m)
    return Piece(rgba, (pivot[0] - box[0], pivot[1] - box[1]), name)


# ------------------------------------------------------------- the forage ---

BOOT_SRC = Image.open(SRC / "boot.jpg").convert("RGB")
BK = BOOT_SRC.width / 960.0                      # coordinates below were read off the 960 px file
BOOT_POLY = [(320, 458), (371, 443), (372, 420), (385, 405), (400, 402), (412, 415), (415, 436), (466, 422),
             (462, 530), (458, 615), (458, 680), (462, 720), (475, 740), (510, 760), (550, 770), (572, 780),
             (581, 792), (577, 804), (560, 814), (520, 821), (455, 817), (416, 813), (416, 841), (360, 841),
             (357, 820), (358, 790), (355, 760), (344, 705), (332, 650), (325, 580)]
BOOT_PIN = (398, 712)
POSTER_BOX = (252, 388, 612, 862)
WS = 1.25                                        # world scale of the boot paper


def _S(p):
    return (p[0] * BK, p[1] * BK)


def build_boot():
    size = BOOT_SRC.size
    raw = poly_to_mask(size, [_S(p) for p in BOOT_POLY], ss=2)
    poly = facet(raw, grow=int(round(4 * BK)), eps=2.0 * BK)
    whole = poly_to_mask(size, poly)
    yy, xx = np.mgrid[0:size[1], 0:size[0]].astype(np.float32)
    # the ankle snip: a slightly slanted line through the pin
    line = (yy - BOOT_PIN[1] * BK) - 0.07 * (xx - BOOT_PIN[0] * BK)
    w = np.asarray(whole, np.float32)
    ov = 20 * BK
    r = np.hypot(xx - BOOT_PIN[0] * BK, yy - BOOT_PIN[1] * BK)
    tab = r < 66 * BK                                  # round tab around the pin keeps the joint closed
    leg = w * ((line < ov * 0.4) | (tab & (line < ov * 2.2)))
    foot = w * ((line > -ov * 0.4) | (tab & (line > -ov * 2.2)))
    pin = _S(BOOT_PIN)
    P = {}
    P["whole"] = cut_piece(BOOT_SRC, whole, pin, "boot")
    P["leg"] = cut_piece(BOOT_SRC, Image.fromarray(leg.astype(np.uint8)), pin, "leg")
    P["foot"] = cut_piece(BOOT_SRC, Image.fromarray(foot.astype(np.uint8)), pin, "foot")
    return P, poly


BOOT, BOOT_CUT = build_boot()
BS = WS / BK                                     # piece pixels -> world


def build_poster():
    box = tuple(int(v * BK) for v in POSTER_BOX)
    im = BOOT_SRC.crop(box)
    hole = poly_to_mask(BOOT_SRC.size, BOOT_CUT).crop(box)
    # a ragged tear along the poster crop, so the sheet is a sheet
    w, h = im.size
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    r = np.random.RandomState(3)
    for x in range(0, w, 7):
        d.rectangle([x, 0, x + 7, r.randint(0, 5)], fill=0)
        d.rectangle([x, h - r.randint(1, 6), x + 7, h], fill=0)
    for y in range(0, h, 7):
        d.rectangle([0, y, r.randint(0, 5), y + 7], fill=0)
        d.rectangle([w - r.randint(1, 6), y, w, y + 7], fill=0)
    return im, m, hole, box


POSTER_IM, POSTER_M, POSTER_HOLE, POSTER_PXBOX = build_poster()
CUT_PATH = [(x - POSTER_PXBOX[0], y - POSTER_PXBOX[1]) for x, y in BOOT_CUT]
# start the cut at the heel so the scissors come in from the bottom edge
_k0 = max(range(len(CUT_PATH)), key=lambda k: CUT_PATH[k][1] - 0.3 * CUT_PATH[k][0])
CUT_PATH = CUT_PATH[_k0:] + CUT_PATH[:_k0] + [CUT_PATH[_k0]]
_seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(CUT_PATH, CUT_PATH[1:])]
CUT_LEN = sum(_seg)


def path_at(f):
    """Point and tangent angle (deg) at fraction f of the cut."""
    d = clamp(f) * CUT_LEN
    for (a, b), L in zip(zip(CUT_PATH, CUT_PATH[1:]), _seg):
        if d <= L or (a, b) == (CUT_PATH[-2], CUT_PATH[-1]):
            u = clamp(d / max(L, 1e-6))
            return (lerp(a[0], b[0], u), lerp(a[1], b[1], u)), math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        d -= L
    return CUT_PATH[-1], 0.0


def path_prefix(f):
    d = clamp(f) * CUT_LEN
    out = [CUT_PATH[0]]
    for (a, b), L in zip(zip(CUT_PATH, CUT_PATH[1:]), _seg):
        if d <= L:
            u = d / max(L, 1e-6)
            out.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u)))
            return out
        out.append(b)
        d -= L
    return out


_poster_cache = {}


def poster_piece(f, holed):
    """The poster sheet with the slit cut so far (or, once the boot is out, with its hole)."""
    key = (round(f, 3), holed)
    if key in _poster_cache:
        return _poster_cache[key]
    im = POSTER_IM.copy()
    m = POSTER_M.copy()
    if holed:
        m = ImageChops.subtract(m, POSTER_HOLE)
        im = paper_edge(im, m)
    elif f > 0:
        pts = path_prefix(f)
        if len(pts) > 1:
            d = ImageDraw.Draw(im)
            d.line(pts, fill=(52, 42, 34), width=max(2, int(2.2 * BK)), joint="curve")
            d.line([(x - 1, y - 1) for x, y in pts], fill=(244, 238, 224), width=1)
    rgba = im.convert("RGBA")
    rgba.putalpha(m)
    p = Piece(rgba, (im.width / 2, im.height / 2), "poster")
    if len(_poster_cache) > 4:
        _poster_cache.clear()
    _poster_cache[key] = p
    return p


def build_trout():
    src = Image.open(SRC / "trout.jpg").convert("RGB")
    a = np.asarray(src, np.float32)
    bg = np.median(a[:40, :200].reshape(-1, 3), 0)
    diff = np.abs(a - bg).sum(2)
    m = (diff > 46).astype(np.uint8)
    m[400:, :] = 0                                   # the lettering and signature stay on the plate
    m[300:, :170] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == k).astype(np.uint8) * 255
    poly = facet(Image.fromarray(m), grow=5, eps=2.6)
    whole = np.asarray(poly_to_mask(src.size, poly), np.float32)
    xx = np.mgrid[0:src.size[1], 0:src.size[0]][1].astype(np.float32)
    pin = (792, 215)
    body = whole * (xx < pin[0] + 22)
    tail = whole * (xx > pin[0] - 22)
    return (cut_piece(src, Image.fromarray(body.astype(np.uint8)), pin, "trout-body"),
            cut_piece(src, Image.fromarray(tail.astype(np.uint8)), pin, "trout-tail"))


TROUT_BODY, TROUT_TAIL = build_trout()

ROCK_POLYS = {
    "point": [(598, 397), (612, 345), (632, 300), (655, 278), (688, 268), (702, 290), (696, 330), (684, 362), (692, 396), (650, 406)],
    "low": [(283, 492), (298, 466), (338, 452), (380, 456), (420, 449), (452, 440), (492, 446), (504, 482), (470, 502), (300, 503)],
    "mound": [(556, 442), (600, 426), (660, 419), (702, 430), (760, 424), (822, 430), (842, 456), (800, 471), (700, 472), (600, 470)],
    "crag": [(740, 302), (758, 250), (790, 219), (832, 214), (862, 236), (882, 270), (902, 300), (896, 332), (850, 334), (800, 337), (748, 332)],
    "turf": [(58, 422), (150, 404), (258, 394), (332, 410), (334, 470), (282, 502), (58, 506)],
}


def build_rocks():
    src = Image.open(SRC / "rocks.jpg").convert("RGB")
    out = {}
    for k, pts in ROCK_POLYS.items():
        m = poly_to_mask(src.size, pts)
        box = m.getbbox()
        out[k] = cut_piece(src, m, ((box[0] + box[2]) / 2, box[3]), k)   # pivot: bottom centre
    return out


ROCK = build_rocks()

TURKEY_POLY = [(678, 100), (700, 86), (742, 82), (750, 60), (770, 66), (792, 76), (816, 94), (832, 130), (836, 198),
               (852, 240), (884, 276), (892, 345), (880, 430), (776, 430), (780, 340), (790, 300), (780, 250),
               (768, 208), (762, 180), (748, 160), (732, 140), (700, 118), (682, 108)]


def build_turkey():
    src = Image.open(SRC / "turkey.jpg").convert("RGB")
    m = poly_to_mask(src.size, TURKEY_POLY)
    return cut_piece(src, m, (800, 430), "turkey")


TURKEY = build_turkey()


def build_scissors():
    g = Image.open(SRC / "scissors.png").convert("L")
    k = 2
    g = g.resize((g.width * k, g.height * k), Image.BICUBIC)
    a = np.asarray(g)
    ink_ = (a < 150).astype(np.uint8)
    walls = cv2.dilate(ink_, np.ones((3, 3), np.uint8))
    free = (1 - walls).astype(np.uint8)
    pad = np.pad(free, 1, constant_values=1)
    n, lab = cv2.connectedComponents(pad, connectivity=4)
    outside = lab == lab[0, 0]
    solid = (~outside[1:-1, 1:-1]).astype(np.uint8)
    # finger holes are really holes
    n2, lab2, st2, cen = cv2.connectedComponentsWithStats(free, connectivity=4)
    for i in range(1, n2):
        if lab2[0, 0] != i and cen[i][0] < 112 * k and st2[i, cv2.CC_STAT_AREA] > 300 * k * k:
            solid[lab2 == i] = 0
    solid = cv2.dilate(solid, np.ones((3, 3), np.uint8))
    h, w = solid.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) / k
    px, py = 232.0, 95.0
    left = xx < px
    bl = np.interp(xx, [0, 100, 150, 190, 232], [80, 82, 84, 93, 95])       # boundary left of the screw
    br = np.interp(xx, [232, 320, 500], [92, 87, 60])                        # boundary right of it
    upper = np.where(left, yy < bl, yy < br)
    disc = np.hypot(xx - px, yy - py) < 13
    A = solid * (np.where(left, upper, ~upper) | disc)     # upper handle + lower blade
    B = solid * (np.where(left, ~upper, upper) | disc)     # lower handles + upper blade
    rgb = Image.merge("RGB", [g, g, g])
    tint = Image.new("RGB", rgb.size, (238, 232, 216))
    rgb = ImageChops.multiply(rgb, tint)
    pa = cut_piece(rgb, Image.fromarray(A * 255), (px * k, py * k), "scA")
    pb = cut_piece(rgb, Image.fromarray(B * 255), (px * k, py * k), "scB")
    return pa, pb, k


SC_A, SC_B, SC_K = build_scissors()


# ------------------------------------------------------------- handmade ---

def noise_tex(size, blur, seed, amp=1.0):
    r = np.random.RandomState(seed)
    n = r.normal(0, 1, (size[1], size[0])).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), blur)
    n /= (np.abs(n).max() + 1e-6)
    return n * amp


def make_ring(R=260):
    """Brass porthole ring, turned and brushed, six hex bolts."""
    S = 2
    n = 2 * (R + 12) * S
    c = n / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - c) / S, (yy - c) / S
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    rin, rout = 0.775 * R, R
    brush = np.interp((th + np.pi) / (2 * np.pi) * 1440, np.arange(1441), np.r_[noise_tex((1440, 1), 3, 5)[0], 0])
    ring_n = np.sin(r * 1.7) * 0.03                                  # lathe rings
    nx, ny = dx / (r + 1e-6), dy / (r + 1e-6)
    lit = -(nx * 0.55 + ny * 0.83)                                   # light from upper left
    prof = np.zeros_like(r)
    prof += np.clip((r - (rout - 0.07 * R)) / (0.07 * R), 0, 1) * 1.0          # outer bevel falls away
    prof -= np.clip(((rin + 0.07 * R) - r) / (0.07 * R), 0, 1) * 1.0           # inner lip falls in
    shade = 1.0 + 0.10 * brush + ring_n + 0.42 * lit * prof + 0.08 * lit
    groove = np.exp(-((r - (rin + 0.105 * R)) / (0.012 * R)) ** 2) * 0.35
    shade -= groove
    base = np.array([186, 146, 66], np.float32)
    rgb = base[None, None, :] * shade[..., None]
    rgb[..., 2] *= 0.9 + 0.1 * np.clip(shade, 0, 2)
    a = np.clip((rout - r) * S, 0, 1) * np.clip((r - rin) * S, 0, 1)
    img = Image.fromarray(np.dstack([rgb.clip(0, 255), a * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    br = 0.066 * R * S
    for k in range(6):
        an = math.radians(30 + 60 * k)
        bx, by = c + math.cos(an) * 0.888 * R * S, c + math.sin(an) * 0.888 * R * S
        d.ellipse([bx - br * 1.15 + 3 * S, by - br * 1.15 + 5 * S, bx + br * 1.15 + 3 * S, by + br * 1.15 + 5 * S], fill=(60, 40, 14, 150))
        rot = an + 0.26
        hexp = [(bx + br * math.cos(rot + j * math.pi / 3), by + br * math.sin(rot + j * math.pi / 3)) for j in range(6)]
        for j in range(6):
            p, q = hexp[j], hexp[(j + 1) % 6]
            mid = rot + (j + 0.5) * math.pi / 3
            l_ = -(math.cos(mid) * 0.55 + math.sin(mid) * 0.83)
            v = 1.0 + 0.4 * l_
            d.polygon([(bx, by), p, q], fill=(int(clamp(200 * v, 0, 255)), int(clamp(158 * v, 0, 255)), int(clamp(74 * v, 0, 255)), 255))
        d.line(hexp + [hexp[0]], fill=(84, 58, 20, 255), width=S)
        d.ellipse([bx - br * 0.42, by - br * 0.42, bx + br * 0.42, by + br * 0.42], fill=(214, 176, 92, 255), outline=(96, 68, 24, 255), width=S)
        d.ellipse([bx - br * 0.3, by - br * 0.34, bx - br * 0.02, by - br * 0.06], fill=(246, 222, 150, 220))
    img = img.resize((n // S, n // S), Image.LANCZOS)
    return Piece(img, (img.width / 2, img.height / 2), "ring")


RING = make_ring()
RING_R = 260.0


def make_tin():
    """The bread-roll tin: cut tinplate, a rolled lid, ribs, a paper label, a lamp at the bow."""
    S = 3
    Wd, Hd = 290, 150
    im = Image.new("RGBA", (Wd * S, Hd * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")

    def R(x0, y0, x1, y1, r, fill, outline=None, width=1):
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill, outline=outline, width=width * S)

    tin, dk, lt = (170, 172, 164, 255), (96, 98, 94, 255), (222, 224, 214, 255)
    # propeller (stern, left)
    for an in (-70, 0, 70):
        a = math.radians(an)
        cx, cy = 24, 84
        d.polygon([(cx * S, cy * S), ((cx - 10 * math.cos(a) + 6 * math.sin(a)) * S, (cy - 22 * math.sin(a) - 4) * S),
                   ((cx - 4 * math.cos(a)) * S, (cy - 26 * math.sin(a)) * S), ((cx + 4) * S, (cy - 14 * math.sin(a)) * S)], fill=(150, 116, 52, 255), outline=(70, 50, 20, 255))
    R(20, 78, 34, 90, 3, (176, 138, 62, 255), (70, 50, 20, 255))
    # skids
    R(52, 120, 96, 130, 3, dk)
    R(176, 120, 220, 130, 3, dk)
    # body
    R(30, 40, 246, 124, 20, tin, (70, 72, 68, 255), 1)
    for x in range(40, 240, 9):                              # pressed ribs
        d.line([(x * S, 62 * S), (x * S, 116 * S)], fill=(120, 122, 116, 255), width=S)
        d.line([((x + 2) * S, 62 * S), ((x + 2) * S, 116 * S)], fill=(214, 216, 206, 255), width=S)
    # rolled lid
    R(24, 30, 252, 54, 10, (188, 190, 180, 255), (70, 72, 68, 255), 1)
    d.line([(34 * S, 37 * S), (242 * S, 37 * S)], fill=lt, width=2 * S)
    d.line([(30 * S, 50 * S), (246 * S, 50 * S)], fill=dk, width=S)
    for x in range(40, 244, 17):
        d.ellipse([(x - 2) * S, 42 * S, (x + 2) * S, 46 * S], fill=(120, 122, 116, 255), outline=(60, 60, 58, 255))
    # hatch tube on top
    R(110, 16, 150, 34, 5, (176, 178, 170, 255), (70, 72, 68, 255))
    R(104, 12, 156, 20, 4, (176, 138, 62, 255), (70, 50, 20, 255))
    # paper label
    R(44, 66, 122, 112, 2, (238, 226, 196, 255), (128, 40, 40, 255), 1)
    f1 = ImageFont.truetype(str(FONTS / "instrument-serif.woff2"), 15 * S)
    f2 = ImageFont.truetype(str(FONTS / "ibm-plex-mono.woff2"), 6 * S)
    d.text((83 * S, 79 * S), "BREAD", font=f1, fill=(128, 40, 40, 255), anchor="mm")
    d.text((83 * S, 94 * S), "ROLLS", font=f1, fill=(128, 40, 40, 255), anchor="mm")
    d.text((83 * S, 106 * S), "TROUT TOWN · 1 DOZ", font=f2, fill=(70, 60, 50, 255), anchor="mm")
    # lamp bracket and housing (bow, right)
    R(244, 88, 262, 94, 2, dk)
    R(256, 78, 276, 104, 4, (176, 138, 62, 255), (70, 50, 20, 255))
    d.ellipse([272 * S, 79 * S, 282 * S, 103 * S], fill=(250, 196, 92, 255), outline=(70, 50, 20, 255), width=S)
    # tarnish
    a = np.asarray(im, np.float32)
    n = noise_tex(im.size, 9, 21)[..., None]
    a[..., :3] *= 1 + 0.10 * n
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA").resize((Wd, Hd), Image.LANCZOS)
    return Piece(im, (138, 130), "tin")


TIN = make_tin()
TIN_PORT = (182 - 138, 86 - 130)      # porthole centre relative to the tin pivot
TIN_LAMP = (282 - 138, 91 - 130)      # lamp lens relative to the pivot
TIN_PORT_R = 27.0


def make_window():
    """What shows in the tin's porthole: a lit cabin disc with Turkey's head in it."""
    n = 120
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([4, 4, n - 4, n - 4], fill=(246, 214, 140, 255))
    d.ellipse([18, 10, n - 30, n - 44], fill=(255, 238, 190, 120))
    t, (px, py) = TURKEY.get(0, 0.30)
    lay = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    lay.paste(t, (int(74 - px), int(124 - py)), t)
    m = Image.new("L", (n, n), 0)
    ImageDraw.Draw(m).ellipse([4, 4, n - 4, n - 4], fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m))
    im.alpha_composite(lay)
    return Piece(im, (n / 2, n / 2), "window")


WINDOW = make_window()


def make_pin(r=9):
    S = 4
    n = (2 * r + 6) * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    c = n / 2
    d.ellipse([c - r * S, c - r * S, c + r * S, c + r * S], fill=(184, 144, 62, 255), outline=(78, 56, 20, 255), width=S)
    d.ellipse([c - r * S * 0.6, c - r * S * 0.7, c + r * S * 0.1, c - r * S * 0.05], fill=(246, 222, 150, 230))
    d.line([(c - r * S * 0.5, c + r * S * 0.1), (c + r * S * 0.5, c + r * S * 0.1)], fill=(96, 68, 24, 255), width=S)
    return Piece(im.resize((n // S, n // S), Image.LANCZOS), (n / S / 2, n / S / 2), "pin")


PIN = make_pin()

GELS = [  # name, colour (transmission), world polygon top edge y, seed
    ("far", (0.50, 0.86, 0.80), -160, 1),
    ("mid", (0.64, 0.90, 0.74), 150, 2),
    ("near", (0.58, 0.80, 0.74), 330, 3),
]
WORLD_BOX = (-240, -160, 1200, 700)


def make_gel(col, top, seed):
    """A sheet of tissue: torn top edge, fibres, slightly uneven dye."""
    x0, y0, x1, y1 = WORLD_BOX
    w, h = x1 - x0, y1 - top
    r = np.random.RandomState(seed)
    edge = cv2.GaussianBlur(r.normal(0, 1, (1, w)).astype(np.float32), (0, 0), 28)[0]
    edge = edge / np.abs(edge).max() * 26 + cv2.GaussianBlur(r.normal(0, 1, (1, w)).astype(np.float32), (0, 0), 2)[0] * 5
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    a = np.clip((yy - 30 - edge[None, :]) / 2.0, 0, 1)
    dye = 1 + 0.07 * noise_tex((w, h), 30, seed + 40) + 0.05 * noise_tex((w, h), 1.2, seed + 50)
    a = np.clip(a * dye, 0, 1.15)
    return dict(alpha=a.astype(np.float32), col=np.array(col, np.float32), top=top, x0=x0, w=w, h=h)


GEL = {n: make_gel(c, t, s) for n, c, t, s in GELS}


def make_table():
    x0, y0, x1, y1 = WORLD_BOX
    w, h = x1 - x0, y1 - y0
    base = np.empty((h, w, 3), np.float32)
    base[:] = (224, 221, 208)
    n = noise_tex((w, h), 40, 61)[..., None] * 7 + noise_tex((w, h), 1.0, 62)[..., None] * 4
    base += n
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    r = np.random.RandomState(5)
    for _ in range(26):                               # old knife scratches in the glass
        x, y = r.randint(0, w), r.randint(0, h)
        a = r.uniform(0, 3.14)
        L = r.randint(30, 160)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=(180, 176, 164, 150), width=1)
    for x in range(120, w, 240):                      # pencil registration crosses
        for y in range(120, h, 240):
            d.line([(x - 9, y), (x + 9, y)], fill=(120, 116, 108, 150), width=1)
            d.line([(x, y - 9), (x, y + 9)], fill=(120, 116, 108, 150), width=1)
    return im


TABLE = make_table()


def make_wall():
    """Inside of the tin around the porthole (part 2): ribbed tinplate, riveted seam."""
    a = np.empty((H, W, 3), np.float32)
    a[:] = (92, 90, 82)
    xx = np.mgrid[0:H, 0:W][1].astype(np.float32)
    rib = np.sin(xx / 46.0 * 2 * np.pi)
    a *= (1 + 0.22 * rib)[..., None]
    a += noise_tex((W, H), 2.0, 71)[..., None] * 6 + noise_tex((W, H), 50, 72)[..., None] * 10
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    for y in (26, 514):
        d.line([(0, y + 12), (W, y + 12)], fill=(40, 40, 36, 255), width=2)
        for x in range(18, W, 46):
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(150, 148, 136, 255), outline=(40, 40, 36, 255))
            d.ellipse([x - 4, y - 5, x, y - 1], fill=(214, 212, 196, 255))
    return np.asarray(im, np.float32) / 255


WALL = make_wall()

# ---------------------------------------------------------------- staging ---

CAM = [1.0, 480.0, 270.0]


def to_screen(wx, wy):
    z, cx, cy = CAM
    return ((wx - cx) * z + W / 2, (wy - cy) * z + H / 2)


def place(piece, wx, wy, ang=0.0, s=1.0, lift=2.0, kind="opaque", flip=False, stage="near", occ=True):
    return dict(piece=piece, w=(wx, wy), ang=ang, s=s, lift=lift, kind=kind, flip=flip, stage=stage, occ=occ)


def _blit(item, dark=False):
    z = CAM[0]
    im, (px, py) = item["piece"].get(item["ang"], item["s"] * z, item["flip"], dark)
    sx, sy = to_screen(*item["w"])
    return im, int(round(sx - px)), int(round(sy - py))


_table_cache = {}


def table_view():
    key = tuple(round(v, 3) for v in CAM)
    if key not in _table_cache:
        z, cx, cy = CAM
        x0, y0 = WORLD_BOX[0], WORLD_BOX[1]
        box = (cx - W / 2 / z - x0, cy - H / 2 / z - y0, cx + W / 2 / z - x0, cy + H / 2 / z - y0)
        if len(_table_cache) > 3:
            _table_cache.clear()
        _table_cache[key] = TABLE.resize((W, H), Image.BICUBIC, box=box)
    return _table_cache[key]


_gel_cache = {}


def gel_view(name):
    """Coverage of a tissue sheet on screen for the current camera."""
    key = (name,) + tuple(round(v, 3) for v in CAM)
    if key not in _gel_cache:
        g = GEL[name]
        z, cx, cy = CAM
        M = np.array([[1 / z, 0, cx - W / 2 / z - g["x0"]], [0, 1 / z, cy - H / 2 / z - g["top"]]], np.float32)
        a = cv2.warpAffine(g["alpha"], M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderValue=0)
        if len(_gel_cache) > 8:
            _gel_cache.clear()
        _gel_cache[key] = a
    return _gel_cache[key]


def toplit(items, light=1.0):
    """The table under the top lamp: paper faces, cut edges, drop shadows."""
    canvas = table_view().copy().convert("RGB")
    z = CAM[0]
    for it in items:
        if it["kind"] == "gel":
            g = GEL[it["name"]]
            a = gel_view(it["name"]) * it.get("amt", 1.0)
            if it.get("dy"):
                a = np.roll(a, int(it["dy"] * z), 0)
                if it["dy"] < 0:
                    a[int(it["dy"] * z):, :] = 0
            sh = np.clip(np.roll(a, int(3 * z), 0) - a, 0, 1) * 0.25          # the torn edge casts a little shadow
            arr = np.asarray(canvas, np.float32)
            arr *= (1 - sh[..., None])
            tis = (g["col"] * 0.45 + 0.55) * 255
            k = np.clip(a, 0, 1)[..., None] * 0.62
            arr = arr * (1 - k) + tis[None, None, :] * k
            canvas = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
            continue
        im, x, y = _blit(it)
        lift = it["lift"] * z
        sh = im.getchannel("A").filter(ImageFilter.GaussianBlur(1.5 + lift * 0.45))
        sh = sh.point(lambda v: int(v * 0.42))
        canvas.paste((30, 24, 18), (int(x + 2 + lift * 0.8), int(y + 3 + lift * 1.2)), sh)
        canvas.paste(im, (x, y), im)
    if light < 1:
        canvas = Image.eval(canvas, lambda v: int(v * light))
    return np.asarray(canvas, np.float32) / 255


AMBER = np.array([1.0, 0.60, 0.16], np.float32)
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_RAY = noise_tex((1440, 1), 4, 91)[0]
_FIBRE = 1 + 0.035 * noise_tex((W, H), 0.8, 92)[..., None] + 0.03 * noise_tex((W, H), 14, 93)[..., None]
_MOTES = np.random.RandomState(12).uniform(0, 1, (150, 4))


def shadow_of(occ, L):
    """Shadow volume of an occluder mask from a point lamp: polar unwrap, running max, wrap back."""
    R = 1150.0
    pol = cv2.warpPolar(occ, (575, 1440), (float(L[0]), float(L[1])), R, cv2.WARP_POLAR_LINEAR | cv2.INTER_LINEAR)
    pol = np.maximum.accumulate(pol, axis=1)
    sh = cv2.warpPolar(pol, (W, H), (float(L[0]), float(L[1])), R, cv2.WARP_POLAR_LINEAR | cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR)
    return cv2.GaussianBlur(sh, (0, 0), 1.6)


STATS = {}


def backlit(items, lamp, beam_dir, beam_amt=1.0, half=17.0, t=0.0, glass=1.0):
    """The same table with the top light off and the lamp under the glass on.
    Tissue passes colour, paper stops light, the amber gel beam is occluded by whatever stands in it."""
    z = CAM[0]
    F = np.empty((H, W, 3), np.float32)
    F[:] = (1.0, 0.985, 0.93)
    r = np.hypot((_XX - W / 2) / W, (_YY - H * 0.36) / H)
    F *= (1.08 - 0.75 * r ** 1.4)[..., None] * glass
    sil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    occ = Image.new("L", (W, H), 0)
    emis = []
    far_done = False

    def add_beam(F):
        L = to_screen(*lamp)
        o = np.asarray(occ, np.float32) / 255
        ang = np.arctan2(_YY - L[1], _XX - L[0])
        dist = np.hypot(_XX - L[0], _YY - L[1])
        diff = np.abs((ang - math.radians(beam_dir) + np.pi) % (2 * np.pi) - np.pi)
        hf = math.radians(half)
        cone = np.clip((hf - diff) / (hf * 0.5), 0, 1)
        cone = cone * cone * (3 - 2 * cone)
        ray = np.interp((ang + np.pi) / (2 * np.pi) * 1439, np.arange(1440), _RAY)
        fall = 1.0 / (1.0 + (dist / (360.0 * z)) ** 1.5)
        sh = shadow_of(o, L)
        beam = cone * fall * (0.8 + 0.3 * ray) * (1 - sh)
        hot = np.exp(-(dist / (15.0 * z)) ** 2) * 1.6
        STATS["beam"] = beam
        STATS["shadow"] = sh
        # motes: bits of silt that only show where the light reaches
        dots = Image.new("L", (W, H), 0)
        dd = ImageDraw.Draw(dots)
        for mx, my, ph, sz in _MOTES:
            wx = 300 + mx * 640 + 9 * math.sin(t * 0.5 + ph * 6.3)
            wy = 150 + my * 330 - ((t * 5 + ph * 90) % 60) * 0.25
            sx, sy = to_screen(wx, wy)
            rr = (0.7 + sz * 1.3) * z
            dd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=int(150 + 100 * sz))
        dots = np.asarray(dots.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
        light = (beam * 0.95 + hot + dots * beam * 1.6) * beam_amt
        F = F + light[..., None] * AMBER[None, None, :]
        return F, beam * beam_amt

    beam = None
    for it in items:
        if it["stage"] == "near" and not far_done:
            # flush the far silhouettes, then light the water
            a = np.asarray(sil, np.float32) / 255
            F = F * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
            sil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            # occluders are gathered from the near items below, so add the beam after them
            far_done = True
        if it["kind"] == "gel":
            if sil.getbbox():
                a = np.asarray(sil, np.float32) / 255
                F = F * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
                sil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            g = GEL[it["name"]]
            a = gel_view(it["name"])[..., None] * it.get("amt", 1.0)
            F = F * (1 - a * (1 - g["col"][None, None, :]))
            continue
        if it["kind"] == "emissive":
            emis.append(it)
            continue
        im, x, y = _blit(it, dark=True)
        sil.paste(im, (x, y), im)
        if it["occ"] and it["stage"] == "near":
            occ.paste(255, (x, y), im.getchannel("A"))
    F, beam = add_beam(F)
    a = np.asarray(sil, np.float32) / 255
    al = a[..., 3]
    # paper is not perfectly opaque: a breath of the light behind it comes through, and edges catch it
    glowmap = cv2.GaussianBlur(beam, (0, 0), 5 * z)
    rim = np.clip(cv2.GaussianBlur(beam * (1 - al), (0, 0), 1.8) * 2.2, 0, 1) * al
    body = a[..., :3] * (1.0 + 2.2 * glowmap[..., None]) + AMBER[None, None, :] * (0.10 * glowmap[..., None])
    F = F * (1 - al[..., None]) + body * al[..., None]
    F += rim[..., None] * AMBER[None, None, :] * 0.85
    for it in emis:
        im, x, y = _blit(it)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lay.paste(im, (x, y), im)
        e = np.asarray(lay, np.float32) / 255
        F = F * (1 - e[..., 3:]) + e[..., :3] * e[..., 3:] * it.get("amt", 1.0)
        halo = cv2.GaussianBlur(e[..., 3], (0, 0), 7 * z) * 0.35 * it.get("amt", 1.0)
        F += halo[..., None] * AMBER[None, None, :]
    F *= _FIBRE
    bloom = cv2.GaussianBlur(np.clip(F - 0.78, 0, None), (0, 0), 9)
    F = F + bloom * 0.7
    return F


def tone(F):
    F = np.clip(F, 0, None)
    F = 1 - np.exp(-F * 1.55)            # shoulder, so the lamp burns without clipping flat
    return F


# ------------------------------------------------------------- the world ---

GROUND = 474.0
PIN_STAND = (612.0, GROUND - (842 - BOOT_PIN[1]) * WS + 2)      # ankle pin when the boot stands
TIN_X = 168.0
LAMP = (TIN_X + TIN_LAMP[0], GROUND + TIN_LAMP[1])


def boot_items(pin, leg_ang, rel, lift=3.0, pinned=True, whole=False, split=0.0):
    """Forward kinematics: the pin is the root, the leg hangs from it, the foot turns on it."""
    rel = ankle(rel)
    out = []
    if whole:
        return [place(BOOT["whole"], pin[0], pin[1], leg_ang, BS, lift, flip=True)]
    out.append(place(BOOT["foot"], pin[0] - split * 0.3, pin[1] + split, leg_ang + rel, BS, lift, flip=True))
    out.append(place(BOOT["leg"], pin[0], pin[1] - split, leg_ang, BS, lift + 1, flip=True))
    if pinned:
        out.append(place(PIN, pin[0], pin[1], 0, 1.0, lift + 2, occ=False))
    return out


def trout_items(x, y, s, t, lift=3.0, wag=1.0, ang=0.0, ph=0.0):
    w = 15 * wag * math.sin(t * 5.2 + ph)
    a = math.radians(ang)
    # body pivot is the tail pin; the pin sits behind the body centre
    return [place(TROUT_TAIL, x, y, ang + w, s, lift),
            place(TROUT_BODY, x, y, ang - w * 0.12, s, lift + 1),
            place(PIN, x, y, 0, 0.55, lift + 2, occ=False)]


def bed_items(f=1.0, lift=2.0):
    """River bed, cut from the etching. f<1 while the stones are still sliding in from below."""
    dy = (1 - f) * 260
    out = [
        place(ROCK["crag"], 905, GROUND + 6 + dy * 1.2, 0, 1.5, lift, stage="far", occ=False),
        place(ROCK["point"], 60, GROUND + 4 + dy * 1.1, 0, 1.55, lift, stage="far", occ=False, flip=True),
    ]
    return out


def bed_front(f=1.0, lift=2.5):
    dy = (1 - f) * 260
    return [
        place(ROCK["turf"], 150, GROUND + 78 + dy, 0, 1.75, lift),
        place(ROCK["mound"], 560, GROUND + 66 + dy * 1.15, 0, 1.75, lift),
        place(ROCK["low"], 900, GROUND + 70 + dy * 0.9, 0, 1.7, lift),
        place(ROCK["low"], 395, GROUND + 92 + dy * 1.3, 0, 1.25, lift + 1, flip=True),
    ]


def tin_items(x, y=GROUND, lift=3.0, ring=1.0, ring_drop=0.0, window=True, lamp_on=0.0):
    out = [place(TIN, x, y, 0, 1.0, lift, occ=False)]
    if window:
        out.append(place(WINDOW, x + TIN_PORT[0], y + TIN_PORT[1], 0, TIN_PORT_R * 2 / 112, lift, kind="emissive" if lamp_on > 0 else "opaque", occ=False))
        out[-1]["amt"] = lamp_on
    if ring > 0:
        out.append(place(RING, x + TIN_PORT[0], y + TIN_PORT[1] - ring_drop, 0, (TIN_PORT_R / 0.775) / RING_R, lift + 1 + ring_drop * 0.2, occ=False))
    return out


def scissor_items(tipx, tipy, ang, open_, lift=7.0, s=0.34):
    """The crotch of the blades sits on (tipx, tipy); the screw is behind it along the heading."""
    s = s / SC_K * 2
    back = 62 * SC_K * s
    a = math.radians(ang)
    px, py = tipx - back * math.cos(a), tipy - back * math.sin(a)
    close = (1 - open_) * 7.5
    return [place(SC_B, px, py, ang + 7 + close, s, lift, occ=False),
            place(SC_A, px, py, ang + 7 - close, s, lift + 1, occ=False)]


# -------------------------------------------------------------- timeline ---

CUT0, CUT1 = 0.9, 4.5
POSTER_C = (410.0, 262.0)
POSTER_S = WS / BK


def poster_world(pt):
    """Poster pixel -> world."""
    return (POSTER_C[0] + (pt[0] - POSTER_IM.width / 2) * POSTER_S, POSTER_C[1] + (pt[1] - POSTER_IM.height / 2) * POSTER_S)


# where the boot paper sits while it is still in the poster. The poster is not flipped, so the
# cut boot points right; it is turned over (flipped) as it is carried to its place.
PIN_IN_POSTER = poster_world((BOOT_PIN[0] * BK - POSTER_PXBOX[0], BOOT_PIN[1] * BK - POSTER_PXBOX[1]))
SNIPS = []


def part1(t):
    items = []
    # camera: wide over the poster, then in to the scene
    k = ease(t, 5.0, 6.3)
    CAM[0], CAM[1], CAM[2] = lerp(0.84, 1.0, k), lerp(500, 480, k), lerp(262, 270, k)
    f = ramp(t, CUT0, CUT1)
    f = int(f * 40) / 40.0 if f < 1 else 1.0
    lifted = ease(t, 4.6, 5.3)
    away = ease(t, 5.0, 6.2)
    turned = t >= 5.3
    # the scene pieces that slide in underneath
    g1, g2, g3 = ease(t, 7.4, 8.0), ease(t, 7.7, 8.3), ease(t, 8.0, 8.6)
    for name, g in (("far", g1), ("mid", g2)):
        if g > 0:
            items.append(dict(kind="gel", name=name, amt=1.0, dy=-(1 - g) * 700, stage="far"))
    bf = ease(t, 8.3, 9.1)
    if bf > 0:
        items += bed_items(bf)
    if g3 > 0:
        items.append(dict(kind="gel", name="near", amt=1.0, dy=-(1 - g3) * 700, stage="far"))
    # poster
    if away < 1:
        px = POSTER_C[0] - away * 900
        pp = poster_piece(f, t >= 4.6)
        items.append(place(pp, px, POSTER_C[1] + away * 40, -away * 14, POSTER_S, 1.5, occ=False))
    # boot
    if t < 4.6:
        pass                                                   # still part of the sheet
    else:
        go = ease(t, 5.3, 6.4)
        pin = lerp2(PIN_IN_POSTER, (560, 330), go)
        pin = (pin[0], pin[1] - 26 * math.sin(math.pi * lifted) * (1 if t < 5.3 else 0))
        snipped = t >= 6.9
        pinned = t >= 7.25
        rel = 0.0
        if pinned:
            rel = 22 * math.exp(-(t - 7.3) * 1.6) * math.sin((t - 7.3) * 9.0) if t < 9.4 else 0.0
        stand = ease(t, 8.9, 9.7)
        pin = lerp2(pin, (PIN_STAND[0], PIN_STAND[1] - 150), stand)
        if not snipped:
            it = place(BOOT["whole"], pin[0], pin[1], lerp(0, -4, go), BS, 3 + 9 * math.sin(math.pi * clamp(lifted)) if t < 5.3 else 4, flip=turned)
            items.append(it)
        else:
            sp = 7 * (1 - ease(t, 7.05, 7.3))
            its = boot_items(pin, lerp(-4, 0, stand), rel, lift=4, pinned=pinned, split=sp)
            if pinned and t < 7.45:                             # the pin drops in
                its[-1]["w"] = (pin[0], pin[1] - (1 - ramp(t, 7.25, 7.45)) * 60)
                its[-1]["lift"] = 6 + (1 - ramp(t, 7.25, 7.45)) * 20
            items += its
    # bed front, tin, trout
    if bf > 0:
        items += bed_front(bf)
    tn = ease(t, 8.6, 9.3)
    if tn > 0:
        rd = ease(t, 9.3, 9.6)
        items += tin_items(TIN_X - (1 - tn) * 420, ring=1.0 if t >= 9.3 else 0, ring_drop=(1 - rd) * 70)
    tr = ease(t, 9.0, 9.9)
    if tr > 0:
        items += trout_items(815 + (1 - tr) * 400, 318, 0.235, t, wag=0.4 + 0.6 * (1 - tr))
        items += trout_items(775 + (1 - ease(t, 9.2, 10.0)) * 430, 420, 0.165, t, wag=0.4, ph=1.7)
    # scissors
    if t < CUT0:
        p0 = poster_world(CUT_PATH[0])
        e = ease(t, 0.15, CUT0)
        items += scissor_items(lerp(p0[0] - 30, p0[0], e), lerp(p0[1] + 330, p0[1], e), -80, 1.0)
    elif t < CUT1 + 0.1:
        pt, ang = path_at(f)
        wpt = poster_world(pt)
        op = 0.5 + 0.5 * math.cos(f * 40 * math.pi)             # one snip per step of the cut
        # smooth the heading so the scissors do not spin at every facet
        a2 = path_at(min(1, f + 0.03))[1]
        a1 = path_at(max(0, f - 0.03))[1]
        dd = ((a2 - a1 + 180) % 360) - 180
        items += scissor_items(wpt[0], wpt[1], a1 + dd * 0.5, op)
    elif t < 5.4:
        pt, ang = path_at(1.0)
        wpt = poster_world(pt)
        e = ease(t, CUT1 + 0.1, 5.3)
        items += scissor_items(wpt[0] + e * 520, wpt[1] + e * 200, ang - 40 * e, 1.0)
    elif 6.45 < t < 7.2:
        # the ankle snip
        e = ramp(t, 6.5, 6.95)
        x = lerp(560 + 150, 560 - 60, e)
        op = 0.5 + 0.5 * math.cos(e * 6 * math.pi)
        out = ease(t, 6.95, 7.2)
        items += scissor_items(x + out * 300, 330 + 4 + out * 260, 180 + 4 - out * 30, op)
    return items


def scene_items(t, pin, leg_ang, rel, tin_x, trout=True, lamp_on=1.0, trout_dx=0.0):
    items = [dict(kind="gel", name="far", amt=1.0, stage="far"),
             dict(kind="gel", name="mid", amt=1.0, stage="far")]
    items += bed_items()
    items.append(dict(kind="gel", name="near", amt=1.0, stage="far"))
    items += boot_items(pin, leg_ang, rel)
    items += bed_front()
    items += tin_items(tin_x, lamp_on=lamp_on)
    if trout:
        items += trout_items(815 + trout_dx, 318 + 5 * math.sin(t * 0.9), 0.235, t, wag=0.55)
        items += trout_items(775 + trout_dx * 1.3, 420 + 4 * math.sin(t * 1.1 + 1), 0.165, t, wag=0.5, ph=1.7)
    return items


def boot_pose2(u):
    """Part 2: the boot comes down into the beam. u = seconds since the part began."""
    land = 3.3
    if u < 1.6:
        return (PIN_STAND[0] + 16, -260.0), 5.0, 18.0
    if u < land:
        k = ramp(u, 1.6, land)
        k = k * k                                         # it falls, it is not placed
        return (PIN_STAND[0] + 16 * (1 - k), lerp(-260, PIN_STAND[1], k)), 5.0 * (1 - k), 18.0
    v = u - land
    rel = 18 * math.exp(-v * 5.5) * math.cos(v * 13)      # toe slaps down and settles
    sway = 3.2 * math.exp(-v * 1.6) * math.sin(v * 5.0)   # the shaft keeps going a little
    return (PIN_STAND[0], PIN_STAND[1] + 2.5 * math.exp(-v * 7)), sway, rel


LIFTS = [(1.6, 4.1), (6.0, 7.6)]          # part 3: when the boot is off the bed (seconds into the part)


def boot_pose3(u):
    up = 0.0
    for a, b in LIFTS:
        up = max(up, ease(u, a, a + 0.55) * (1 - ramp(u, b, b + 0.22) ** 2))
    v = min([u - (b + 0.22) for a, b in LIFTS if u >= b + 0.22] or [99])
    rel = 15 * up + (12 * math.exp(-v * 6) * math.cos(v * 13) if v < 3 else 0)
    sway = -3.5 * up + (2.5 * math.exp(-v * 1.8) * math.sin(v * 5) if v < 3 else 0)
    return (PIN_STAND[0] + 6 * up, PIN_STAND[1] - 50 * up), sway, rel, up


def tin_pose3(u):
    """The tin scuttles sideways under the lifted toe, in steps, like a crab."""
    x = TIN_X
    for a, b in LIFTS:
        k = ramp(u, a + 0.35, a + 1.2) * (1 - ramp(u, b - 0.45, b + 0.05))
        x += int(k * 5) / 5 * 58
    return x


def silt(u0, x, y, n=16, seed=0):
    """Scraps kicked up on landing."""
    r = np.random.RandomState(seed)
    out = []
    for i in range(n):
        vx, vy = r.uniform(-70, 70), r.uniform(-130, -40)
        g = 150
        px = x + r.uniform(-60, 60) + vx * u0
        py = y + vy * u0 + 0.5 * g * u0 * u0
        if py < GROUND + 6 and u0 > 0:
            out.append((px, py, 1.5 + r.uniform(0, 2.5)))
    return out


def draw_silt(F, pts, beam=None):
    if not pts:
        return F
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    z = CAM[0]
    for x, y, r_ in pts:
        sx, sy = to_screen(x, y)
        d.polygon([(sx - r_ * z, sy), (sx, sy - r_ * z * 0.8), (sx + r_ * z, sy + 1), (sx, sy + r_ * z)], fill=255)
    a = np.asarray(lay, np.float32)[..., None] / 255
    col = np.array([0.05, 0.07, 0.07], np.float32)
    return F * (1 - a) + col * a


def porthole_view(F, t):
    """Part 2 foreground: the tin's inside wall, the brass ring, Turkey's head, all lit only by
    what comes in through the glass."""
    cx, cy, R = 470.0, 258.0, 206.0
    r = np.hypot(_XX - cx, _YY - cy)
    inside = np.clip((R - r) / 1.5, 0, 1)
    # glass: a soft reflection arc and a darker edge
    F = F * (0.55 + 0.45 * np.clip((R - r) / 46.0, 0, 1) ** 0.6)[..., None]
    arc = np.exp(-((r - R * 0.86) / 5.0) ** 2) * np.clip(-((_XX - cx) * 0.6 + (_YY - cy) * 0.8) / R, 0, 1) ** 2
    F = F + arc[..., None] * 0.20
    spill = cv2.GaussianBlur((F * inside[..., None]).astype(np.float32), (0, 0), 46)
    spill_near = cv2.GaussianBlur((F * inside[..., None]).astype(np.float32), (0, 0), 14)
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ring, (px, py) = RING.get(0, (R / 0.775) / RING_R)
    # ring shadow on the wall
    sh = ring.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.7))
    wall = WALL.copy()
    shl = Image.new("L", (W, H), 0)
    shl.paste(sh, (int(cx - px + 5), int(cy - py + 9)))
    wall *= (1 - np.asarray(shl, np.float32)[..., None] / 255 * 0.8)
    fg.paste(ring, (int(cx - px), int(cy - py)), ring)
    # Turkey, bottom right, looking out
    bob = 5 * math.sin(t * 1.3) + (10 * math.exp(-(t - (P2 + 3.3)) * 3) * math.sin((t - P2 - 3.3) * 14) if t > P2 + 3.3 else 0)
    tk, (tx, ty) = TURKEY.get(-8 + 3 * math.sin(t * 0.8), 1.0)
    tpos = (int(770 - tx), int(590 + bob - ty))
    tsh = tk.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.6))
    fg.paste((6, 5, 4), (tpos[0] - 12, tpos[1] + 10), tsh)
    fg.paste(tk, tpos, tk)
    f = np.asarray(fg, np.float32) / 255
    al = f[..., 3:]
    lightfg = 0.07 + spill * 1.25 + spill_near * 0.75
    out_wall = wall * (0.035 + spill * 0.95)
    outside = out_wall * (1 - al) + f[..., :3] * lightfg * al
    k = inside[..., None]
    comp = F * k + outside * (1 - k)
    # the ring and Turkey overlap the glass
    comp = comp * (1 - al) + f[..., :3] * lightfg * al
    return comp


_last = {}


def compose(t):
    tq = math.floor(t * 12 + 1e-6) / 12.0              # shot on twos, like a rostrum cutout
    if _last.get("tq") == tq:
        return _last["img"]
    if tq < P2:
        items = part1(tq)
        A = toplit(items)
        k = ease(tq, 9.9, 10.7)                         # top light down, lamp under the glass up
        if k > 0:
            B = tone(backlit(items_for_backlit(items), LAMP, -6, beam_amt=ease(tq, 10.2, 10.8), t=tq))
            A = A * (1 - k) * (1 - 0.5 * k) + B * k
        img = A
    elif tq < P3:
        u = tq - P2
        CAM[0], CAM[1], CAM[2] = 1.5, 438.0, 392.0
        pin, la, rel = boot_pose2(u)
        items = scene_items(tq, pin, la, rel, TIN_X, trout=False)
        sweep = -8 + (10 * math.sin((u - 5.2) * 1.15) if u > 5.2 else 0) * ease(u, 5.2, 6.0)
        F = backlit(items, LAMP, sweep, beam_amt=1.0, half=19, t=tq)
        F = draw_silt(F, silt(u - 3.3, 520, GROUND, seed=1) if u > 3.3 else [])
        F = tone(F)
        img = porthole_view(F, tq)
    else:
        u = tq - P3
        CAM[0], CAM[1], CAM[2] = 1.08, 490.0, 292.0
        pin, la, rel, up = boot_pose3(u)
        tx = tin_pose3(u)
        items = scene_items(tq, pin, la, rel, tx, trout=True, trout_dx=(1 - ease(u, 0.0, 1.4)) * 260 - 14 * up)
        lamp = (tx + TIN_LAMP[0], GROUND + TIN_LAMP[1])
        F = backlit(items, lamp, -3 + 5 * up, beam_amt=1.0 + 0.25 * up, half=18, t=tq)
        pts = []
        for a, b in LIFTS:
            if u > b + 0.22:
                pts += silt(u - b - 0.22, 520, GROUND, seed=int(a * 10))
        F = draw_silt(F, pts)
        img = tone(F)
        # a soft dark surround so the eye stays on the table
        rr = np.hypot((_XX - W / 2) / (W / 2), (_YY - H / 2) / (H / 2))
        img = img * (1 - 0.35 * np.clip(rr - 0.75, 0, 1) ** 1.5)[..., None]
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    _last["tq"], _last["img"] = tq, out
    return out


def items_for_backlit(items):
    """Part 1 hands its top-lit list to the backlit table: the same pieces, the same places."""
    out = []
    for it in items:
        it = dict(it)
        if it["kind"] == "gel":
            it.pop("dy", None)
        if it.get("piece") is WINDOW:
            it["kind"] = "emissive"
            it["amt"] = 1.0
        out.append(it)
    return out


film = Film(SLUG, seconds=SECONDS, boil=0, wobble=0, seed=1)
film.poster_at = 17.0


@film.picture
def frame(t, ink):
    ink.img = compose(t).copy()
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink._grain = True
    for a, b, s in CAPTIONS:
        if a <= t < b:
            al = min(ramp(t, a, a + 0.3), 1 - ramp(t, b - 0.3, b))
            ink.caption(s, alpha=al, size=25)
    if t < 0.4:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - t / 0.4))))
    if t > SECONDS - 0.6:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * ramp(t, SECONDS - 0.6, SECONDS))))


@film.sound
def sound(mix):
    mix.room(0, P2 + 0.2, gain=0.016)
    # scissors: one snip per step of the cut
    for k in range(40):
        ts = CUT0 + (CUT1 - CUT0) * (k + 0.5) / 40
        mix.click(ts, gain=0.20, bright=7000, seconds=0.035, pan=-0.2)
        mix.click(ts + 0.03, gain=0.10, bright=3000, seconds=0.05, pan=-0.2)
    mix.whoosh(4.6, 0.5, gain=0.05)                    # the boot lifts out
    mix.whoosh(5.1, 0.9, gain=0.06, pan=-0.5)          # the sheet is pulled away
    mix.thud(6.4, freq=120, gain=0.14, seconds=0.12)   # boot laid down
    for k in range(3):
        mix.click(6.58 + k * 0.15, gain=0.22, bright=7000, seconds=0.035)
    mix.click(7.45, gain=0.3, bright=2500, seconds=0.05)   # pin
    mix.note(7.45, 1320, 0.12, gain=0.06)
    for k, ts in enumerate((7.4, 7.7, 8.0)):
        mix.whoosh(ts, 0.6, gain=0.035, pan=0.3 - 0.3 * k)   # tissue
    mix.thud(9.05, freq=90, gain=0.16, seconds=0.2)    # stones
    mix.thud(9.3, freq=150, gain=0.12, seconds=0.12, pan=-0.5)   # tin
    mix.click(9.6, gain=0.28, bright=5000, seconds=0.04, pan=-0.5)   # ring
    mix.note(9.6, 1760, 0.3, gain=0.05, pan=-0.5)
    mix.whoosh(9.4, 0.6, gain=0.04, pan=0.6)           # trout slide in
    mix.click(10.0, gain=0.35, bright=1800, seconds=0.06)  # the switch
    mix.thud(10.02, freq=60, gain=0.2, seconds=0.25)
    mix.drone(10.1, SECONDS - 10.1, freqs=(55, 110.4, 165.3), gain=0.035, attack=0.8, release=1.0)
    # under water from the lamp on
    w = mix.lowpass(mix.noise(SECONDS - 10.2, "brown"), 420)
    w *= mix.env(len(w), 1.0, 0.01, 1.0, 1.0)
    mix.add(w, 10.2, 0.10)
    r2 = np.random.RandomState(4)
    for _ in range(26):                                # bubbles
        tb = r2.uniform(11.0, SECONDS - 1)
        f0 = r2.uniform(500, 1100)
        tt = mix.t(0.09)
        mix.add(np.sin(2 * np.pi * (f0 + 2600 * tt) * tt) * np.exp(-tt * 45), tb, 0.03, r2.uniform(-0.7, 0.7))
    # part 2: the boot arrives
    mix.whoosh(P2 + 2.3, 1.1, gain=0.07)
    mix.thud(P2 + 3.3, freq=48, gain=0.75, seconds=0.7)
    mix.thud(P2 + 3.42, freq=85, gain=0.3, seconds=0.3)
    mix.bell(P2 + 3.7, freq=196, seconds=4.0, gain=0.05)
    mix.murmur(14.6, 2.2, gain=0.05, pitch=210, pan=0.4, seed=3)        # Turkey wonders
    # part 3: lifts and landings, the tin scuttling
    for a, b in LIFTS:
        mix.whoosh(P3 + a, 0.6, gain=0.06)
        mix.bell(P3 + a + 0.45, freq=660, seconds=2.2, gain=0.045, pan=0.4)   # light under the sole
        for k in range(5):
            mix.click(P3 + a + 0.35 + k * 0.17, gain=0.16, bright=2600, seconds=0.04, pan=-0.4)
            mix.click(P3 + b - 0.45 + k * 0.1, gain=0.14, bright=2600, seconds=0.04, pan=-0.4)
        mix.thud(P3 + b + 0.22, freq=50, gain=0.6, seconds=0.6)
    mix.murmur(23.2, 2.4, gain=0.04, pitch=320, pan=0.6, seed=8)        # the trout confer
    mix.reverb(0.18, 1.3)


if __name__ == "__main__":
    run(film)
