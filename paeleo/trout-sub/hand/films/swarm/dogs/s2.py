"""S2 · TROUTTOWN · film seconds 28.0 to 58.0 (local t = film - 28).

Built under scion/animation-05.md (atmospheric multiplane): depth, obscurity and reveal carry the feeling.
The primitives of that SCION are real data here, not a look:

    PLANES      the glass planes and their z distances (what parallax and focus are computed from)
    SHOTS       the camera: one eased move per shot, with the reason it is there
    FOCUS       the focus / exposure schedule: which z is sharp, how wide the aperture is, how warm the door is
    ATMOS       what the water is doing as an actor: suspend, obscure, reveal, lure
    SILT        the fog field: puffs with a birth, a place, a strength; half behind the dog, half in front
    DRESS       foreground occluders per shot (dark out-of-focus weed on near glass)
    heard()     depth audio: a sound's pan and level come from where its source is on screen and in z

Numerical invariants are asserted by check() (run under __main__): parallax grows with z in every moving shot;
the fog is not a uniform overlay; holes never fill in; the holds are dead still; the boundary frames are where
the board puts them. What can only be judged by looking is said in the report, not here.

Exposes SECONDS, draw(t, ink), sound(mix, at).
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kit                                   # noqa: E402
from kit import clamp, ramp, ease, lerp, smooth, W, H, FPS   # noqa: E402
import dog                                   # noqa: E402
import herd                                  # noqa: E402
import porch                                 # noqa: E402
import props                                 # noqa: E402
import town                                  # noqa: E402
import importlib.util as _ilu               # noqa: E402

_spec = _ilu.spec_from_file_location("dogs_sound", str(_HERE / "sound.py"))   # films/ has another module called sound
snd = _ilu.module_from_spec(_spec)
sys.modules.setdefault("dogs_sound", snd)
_spec.loader.exec_module(snd)

SECONDS = 30.0
T0 = 28.0                                    # film second at local 0
DS = 0.6                                     # the lead dog's scale in world px per dog unit
GY = 814.0                                   # where the dog's feet stand on the gravel
TEAL = (24, 120, 128)
Cam = town.Cam


def bump(x):
    return math.sin(math.pi * clamp(x)) if 0 < x < 1 else 0.0


# ====================================================================== #
#  THE MULTIPLANE: planes, camera, focus, atmosphere (data)              #
# ====================================================================== #

PLANES = [   # name, z (1.0 = the street and every actor), what is on the glass
    ("water", 0.30, "the creek's body and its light"),
    ("far", 0.45, "far town: hazed bottles and jars"),
    ("backrow", 0.72, "tin stack, boot house, bottle tower"),
    ("silt_back", 0.96, "the half of the silt that is behind the dog"),
    ("street", 1.00, "gravel, board, school, the class, the dog"),
    ("silt_front", 1.08, "the half of the silt that is in front of the dog"),
    ("weed", 1.30, "town.front's weed and motes"),
    ("near_a", 1.80, "dark weed on near glass"),
    ("near_b", 2.30, "darker weed on the nearest glass"),
]
Z = {n: z for n, z, _ in PLANES}

# One eased move per shot. kind 'town' = under water; 'split' = the line across the frame.
SHOTS = [   # t0, t1, name, kind, camera at start, camera at end, (move t0, move t1), why the camera is there
    (0.0, 5.0, "A wide", "town", Cam(360, 0, 1.0), Cam.look(338, 704, 1.42), (0.5, 4.7),
     "the whole street once, so that a town is what the dog lands in; then a slow push to where dog and class meet"),
    (5.0, 11.0, "B dig", "town", Cam.look(372, 768, 2.3), Cam.look(424, 760, 2.3), (6.9, 9.0),
     "the film's most repeated verb shown once, large; the camera backs with the dog from hole to hole"),
    (11.0, 17.0, "C board", "town", Cam.look(432, 756, 2.25), Cam.look(412, 722, 4.0), (13.7, 14.7),
     "the look: push through the near weed until only nose and page are left"),
    (17.0, 22.5, "D bubble", "town", Cam.look(505, 748, 2.15), Cam.look(512, 744, 2.3), (17.5, 22.0),
     "two-shot: dog left, child and its drawing right; the board behind the dog's shoulder"),
    (22.5, 25.5, "E page", "town", Cam.look(414, 734, 3.2), Cam.look(420, 752, 2.9), (24.4, 25.3),
     "close enough to see that the page is taken by one corner and stays flat"),
    (25.5, 28.5, "F split", "split", Cam(250, 0, 1.0), Cam(250, 0, 1.0), (25.6, 27.2),
     "the only framing that holds the cow, the line and the town at once"),
    (28.5, 30.0, "G up", "town", Cam(360, 0, 1.0), Cam(360, 0, 1.0), (28.5, 30.0),
     "wide again: where the dog is going, and who watches it go"),
]

# Focus and exposure. aperture 0 = everything sharp. blur(z) grows with distance from the focus plane.
# air: 0 = the lens is focused under the line, 1 = above it (only the split shot racks it).
# door: how much amber comes down from the lit door (the lure).
FOCUS = [   # t, focus z, aperture, air, door
    (0.0, 1.0, 0.0, 0.0, 1.0), (1.2, 1.0, 0.18, 0.0, 0.85), (5.0, 1.0, 0.18, 0.0, 0.60),
    (5.0, 1.0, 0.55, 0.0, 0.55), (11.0, 1.0, 0.55, 0.0, 0.55),
    (11.0, 1.0, 0.55, 0.0, 0.5), (13.7, 1.0, 0.55, 0.0, 0.5), (14.7, 1.0, 1.25, 0.0, 0.5), (17.0, 1.0, 1.25, 0.0, 0.5),
    (17.0, 1.0, 0.65, 0.0, 0.5), (22.5, 1.0, 0.65, 0.0, 0.5),
    (22.5, 1.0, 1.0, 0.0, 0.55), (25.5, 1.0, 0.9, 0.0, 0.6),
    (25.5, 1.0, 0.5, 0.0, 0.8), (25.75, 1.0, 0.5, 0.0, 0.8), (26.05, 1.0, 0.5, 1.0, 0.8),      # rack: dog -> cow
    (27.2, 1.0, 0.5, 1.0, 0.85), (27.7, 1.0, 0.5, 0.5, 0.9), (28.5, 1.0, 0.5, 0.5, 0.95),      # both faces at the line
    (28.5, 1.0, 0.12, 0.0, 1.0), (29.4, 1.0, 0.0, 0.0, 1.0), (30.0, 1.0, 0.0, 0.0, 1.0),
]

# The water as an actor. Each state changes what somebody does.
ATMOS = [   # t0, t1, state, what it does to the picture, whose decision it changes
    (3.0, 4.6, "obscure", "silt from the landing hides the dog's feet", "the class stops: something has landed"),
    (6.0, 9.4, "obscure", "each dig throws silt; the third hides the hole and the dog's head", "the dog digs blind, by nose"),
    (9.4, 10.6, "reveal", "the silt streams off and thins: a spool", "the dog has a part and looks for where it goes"),
    (15.0, 16.5, "suspend", "the motes stop; only the page lifts", "the dog holds dead still: it knows something"),
    (21.0, 22.3, "suspend", "the motes stop round the bubble", "the dog looks at the wobble"),
    (25.5, 30.0, "lure", "the door's amber comes down the water", "the dog goes up toward it"),
]


def _key(table, t, col):
    """Piecewise-linear read of one column of a keyed table (repeated times make a cut)."""
    prev = table[0]
    for row in table:
        if row[0] > t:
            a, b = prev, row
            if b[0] == a[0]:
                return b[col]
            return lerp(a[col], b[col], (t - a[0]) / (b[0] - a[0]))
        prev = row
    return prev[col]


def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]


def cam_at(t):
    s = shot_at(t)
    return s[4].mix(s[5], ease(t, *s[6]))


def blur_px(z, t):
    """Defocus of a plane at depth z, in screen px."""
    zf, ap = _key(FOCUS, t, 1), _key(FOCUS, t, 2)
    return 4.0 * ap * abs(z - zf) / (z * zf)


def atmos(t):
    return [a[2] for a in ATMOS if a[0] <= t < a[1]]


# ====================================================================== #
#  THE FOG FIELD                                                         #
# ====================================================================== #

SILT = []       # (t0, world x, world y, amount, seed)


def _silt_sources():
    if SILT:
        return SILT
    out = [(3.0, 430, 816, 0.8, 1), (3.05, 400, 818, 0.7, 2), (3.05, 460, 818, 0.7, 3)]
    for k, (a, b, amt) in enumerate(((6.02, 6.6, 0.4), (7.42, 7.82, 0.45), (8.95, 9.45, 1.5))):
        hx, hy = town.hole_xy(k)
        n = int((b - a) / 0.1) + 1
        for q in range(n):
            out.append((a + q * 0.1, hx + 10 * math.sin(q * 2.3), hy - 4, amt, 10 + k * 20 + q))
    hx, hy = town.hole_xy(2)
    for q in range(6):                                   # the spool coming up through it, silt streaming off
        out.append((9.5 + q * 0.07, hx + 2 * q, hy - 6 - 5 * q, 0.3, 90 + q))
    SILT.extend(out)
    return SILT


_NOISE = None


def _noise():
    global _NOISE
    if _NOISE is None:
        _NOISE = town.w.vnoise((270, 480), 26, seed=5, octaves=2).astype(np.float32)
    return _NOISE


def silt_field(t, cam, front):
    """The silt as a scalar field 0..1 on a quarter-size grid. `front` picks the half of the puffs that are nearer
    than the dog. Every puff swells, drifts with the current, rises a little and thins; the whole is broken up by
    slow noise, so it is never one flat veil."""
    gw, gh = W // 4, H // 4
    f = np.zeros((gh, gw), np.float32)
    depth = Z["silt_front"] if front else Z["silt_back"]
    z = cam.s(depth)
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    any_ = False
    for t0, wx, wy, amt, seed in _silt_sources():
        age = t - t0
        if age <= 0 or age > 4.2:
            continue
        rs = random.Random(seed)
        for q in range(4):
            mine = rs.random() < 0.4
            ang, sp = rs.uniform(math.pi * 0.05, math.pi * 0.95), rs.uniform(8, 26)
            if mine != front:
                continue
            k = 1 - math.exp(-age * 2.2)
            bx = wx + math.cos(ang) * sp * k * 1.5 + 9 * age            # the current runs to the right
            by = wy - math.sin(ang) * sp * k * 0.45 - 3 * age
            r = (9 + 17 * math.sqrt(age)) * z / 4
            a = amt * (1 - math.exp(-age * 9)) * math.exp(-age / 0.95) * 0.8
            if a < 0.01:
                continue
            sx, sy = cam.xy(bx, by, depth)
            sx, sy = sx / 4, sy / 4
            if sx < -3 * r or sx > gw + 3 * r or sy < -3 * r or sy > gh + 3 * r:
                continue
            f += a * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2 * 2.6) / (2 * r * r))
            any_ = True
    if not any_:
        return None
    n = _noise()
    ox, oy_ = int(t * 9) % 240, int(t * 4 + (60 if front else 0)) % 135
    f *= 0.45 + 1.1 * n[oy_:oy_ + gh, ox:ox + gw]
    return np.clip(f, 0, 0.78)


def draw_silt(ink, t, cam, front):
    f = silt_field(t, cam, front)
    if f is None:
        return
    m = Image.fromarray((f * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC)
    col = (126, 136, 110) if front else (104, 122, 104)
    ink.img.paste(Image.new("RGB", (W, H), col), (0, 0), m)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ====================================================================== #
#  FOREGROUND GLASS                                                      #
# ====================================================================== #

# Per shot: (screen x at the shot's first frame, screen y of the root, height px, plane, seed, lean, blades)
DRESS = {
    "A wide": [(730, 830, 230, "near_b", 5, -9, 2)],
    "B dig": [(20, 600, 560, "near_a", 7, 6, 2), (1500, 610, 470, "near_b", 9, -8, 2)],
    "C board": [(40, 610, 600, "near_a", 11, 8, 2), (962, 620, 600, "near_b", 13, -10, 2)],
    "D bubble": [(0, 600, 520, "near_b", 17, 6, 2), (972, 610, 430, "near_a", 19, -8, 2)],
    "E page": [(0, 620, 600, "near_b", 21, 9, 2)],
}


def occluder_xy(shot, k, cam):
    """Where occluder k of a shot is on screen under camera `cam` (parallax by its plane's z)."""
    sx0, sy0, ht, plane, seed, lean, n = DRESS[shot[2]][k]
    wx, wy = shot[4].world(sx0, sy0, Z[plane])
    return cam.xy(wx, wy, Z[plane])


def _blade(d, sx, sy, ht, lean, wd, t, seed, col):
    """One broad ribbon of weed on near glass: a tapered, bent strip."""
    n = 14
    left, right = [], []
    for q in range(n + 1):
        u = q / n
        bend = lean * u * u * ht * 0.012 + math.sin(t * 0.9 + seed + u * 2.2) * 9 * u * u
        x = sx + bend + math.sin(u * 5 + seed) * wd * 0.25
        y = sy - ht * u
        w_ = wd * (1 - u) ** 0.7 * (0.75 + 0.25 * math.sin(u * 7 + seed * 2))
        left.append((x - w_ / 2, y))
        right.append((x + w_ / 2, y))
    d.polygon(left + right[::-1], fill=col)


def draw_dress(ink, t, shot, cam):
    items = DRESS.get(shot[2])
    if not items:
        return
    for plane in ("near_a", "near_b"):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        hit = False
        col = (10, 34, 40, 236) if plane == "near_a" else (5, 20, 26, 246)     # near glass is in shadow
        for k, (sx0, sy0, ht, pl, seed, lean, n) in enumerate(items):
            if pl != plane:
                continue
            sx, sy = occluder_xy(shot, k, cam)
            zz = cam.s(Z[pl]) / shot[4].s(Z[pl])
            if -300 < sx < W + 300:
                rs = random.Random(seed)
                for q in range(n):
                    _blade(d, sx + (q - (n - 1) / 2) * 44 * zz + rs.uniform(-8, 8), sy, ht * zz * rs.uniform(0.55, 1.0),
                           lean + rs.uniform(-5, 5), rs.uniform(44, 70) * zz, t, seed + q * 1.7, col)
                hit = True
        if not hit:
            continue
        lay = lay.filter(ImageFilter.GaussianBlur(2.6 + blur_px(Z[plane], t) * 1.6))
        ink.img.paste(lay, (0, 0), lay)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _blur_rows(ink, y0, y1, r):
    y0, y1 = int(clamp(y0, 0, H)), int(clamp(y1, 0, H))
    if r < 0.45 or y1 - y0 < 4:
        return
    reg = ink.img.crop((0, y0, W, y1)).filter(ImageFilter.GaussianBlur(r))
    ink.img.paste(reg, (0, y0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ====================================================================== #
#  THINGS                                                                #
# ====================================================================== #

class _Shim:
    def __init__(self, size):
        self.img = Image.new("RGBA", size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img, "RGBA")


def _tinted(im, amount=0.3):
    a = np.asarray(im, np.float32).copy()
    a[..., :3] = a[..., :3] * (1 - amount) + np.array(TEAL, np.float32) * amount
    return Image.fromarray(a.astype(np.uint8), "RGBA")


@lru_cache(maxsize=8)
def thing_sprite(kind):
    """A town thing as an image for the dog's mouth (dog.draw_dog scales it by the dog's scale)."""
    k = 3.0
    if kind == "boot":
        sh = _Shim((int(40 * k), int(34 * k)))
        town.thing(sh, None, "boot", 18 * k, 30 * k, angle=0, scale=k, screen=True)
    elif kind == "spool":
        sh = _Shim((int(24 * k), int(24 * k)))
        town.thing(sh, None, "spool", 12 * k, 21 * k, angle=0, scale=k, screen=True)
    else:
        sh = _Shim((int(10 * k), int(14 * k)))
        town.thing(sh, None, "pin", 5 * k, 12 * k, angle=0, scale=k, screen=True)
    im = sh.img.resize((int(sh.img.width / k / DS), int(sh.img.height / k / DS)), Image.LANCZOS)
    return _tinted(im, 0.22)


@lru_cache(maxsize=2)
def page_sprite():
    return props.page_sprite("jaw", flat=0.42, tint=props.TEAL, tint_amount=0.14)


@lru_cache(maxsize=64)
def _probe(key):
    """Where the nose, mouth and near forepaw are for a pose, in world px relative to the anchor (facing right)."""
    pose = _PROBE_POSES[key]()
    im = Image.new("RGB", (700, 560))
    j = dog.draw_dog(im, pose, 350, 420, scale=1.0, facing=1, shadow=False, texture=False, ss=1)
    return {k: ((j[k][0] - 350) * DS, (j[k][1] - 420) * DS) for k in ("nose", "mouth", "fn.paw", "ff.paw")}


# ====================================================================== #
#  THE DOG                                                               #
# ====================================================================== #

HOLE = [town.hole_xy(k) for k in range(3)]


def _with(p, **kw):
    q = dict(p)
    q.update(kw)
    return q


def rear(tn, up=1.0, reach=1.0, lift=0.0):
    """Front paws on the board's frame, nose to a page. tn is nose_page's own clock."""
    p = dog.nose_page(tn, reach=reach)
    u = smooth(clamp(up))
    p["pitch"] += (0.30 + 0.10 * lift) * u
    p["cy"] += 5.0 * u
    p["cx"] -= 4.0 * u
    p["fnx"], p["fny"] = lerp(p["fnx"], 60, u), 52 * u
    p["ffx"], p["ffy"] = lerp(p["ffx"], 70, u), 55 * u
    p["hnx"], p["hfx"] = lerp(p["hnx"], -50, u), lerp(p["hfx"], -35, u)
    p["neck"] += 0.10 * lift
    return p


def _sniff_walk(tau, rate=1.5, back=False):
    p = dog.walk(-tau if back else tau, rate=rate)
    p["neck"], p["head"] = 0.06, -0.56 + 0.05 * math.sin(tau * 31)
    p["ear"], p["ear_f"] = 1.0, 1.05
    p["tail"], p["wag"] = 0.55, 0.25 * math.sin(tau * 9)
    return p


def _dig_rest(k=0.0):
    """The digging crouch held still, head in the hole (k 0) or lifted to look at what it has (k 1)."""
    p = dog.dig(0.36)
    p["fnx"], p["fny"], p["ffx"], p["ffy"] = 62.0, 0.0, 76.0, 0.0
    p["wag"] = 0.0
    p["neck"] = lerp(-0.02, 0.5, k)
    p["head"] = lerp(-0.72, -0.1, k)
    p["pitch"] = lerp(-0.33, -0.12, k)
    p["cy"] = lerp(73, 80, k)
    p["tail"] = lerp(0.7, 0.9, k)
    return p


_PROBE_POSES = {
    "dig": lambda: _dig_rest(0.0),
    "lay": lambda: dog.lay(0.62),
    "rear": lambda: rear(2.0, 1.0, REACH_PAGE),
    "rear_pin": lambda: rear(2.0, 1.0, REACH_PAGE, 1.0),
    "sit": lambda: dog.sit(3.0),
}

PAGE0 = town.board_page_xy(0)                       # world middle of the jaw page
NOSE_AT = (PAGE0[0] + 3.0, PAGE0[1] + 5.0)          # where the nose goes on it
PIN_AT = (PAGE0[0] + 1.0, PAGE0[1] - 11.0)
REACH_PAGE = 1.0


def _solve_reach():
    """Find the nose_page reach that puts the reared dog's nose at the page's height."""
    global REACH_PAGE
    want = NOSE_AT[1] - GY
    best = (1e9, 1.0)
    for q in range(13):
        REACH_PAGE = 0.5 + 0.1 * q
        _probe.cache_clear()
        err = abs(_probe("rear")["nose"][1] - want)
        if err < best[0]:
            best = (err, REACH_PAGE)
    REACH_PAGE = best[1]
    _probe.cache_clear()
    return best


_solve_reach()
XA = [HOLE[k][0] + _probe("dig")["fn.paw"][0] + 3 for k in range(3)]     # anchors for the three digs, facing left
X_BOARD = NOSE_AT[0] + _probe("rear")["nose"][0]                         # anchor at the board, facing left
SPOOL_AT = (X_BOARD - _probe("lay")["mouth"][0] + 2, 808.0)              # where the spool is set down
SPOOL_END = (town.BOARD[0] + 14.0, 808.0)                                # nosed against the board's leg
BOOT_AT = (XA[1] - 86.0, 842.0)
LAND = (430.0, GY)
SIT_X = 436.0
KID0_AT = (514.0, 811.0)
BUBBLE_R = 30.0

DIG = [   # start of dig(), rake from, rake to, hole
    (5.72, 6.02, 6.6, 0), (7.14, 7.42, 7.82, 1), (8.72, 8.95, 9.45, 2),
]


def holes_at(t):
    """How many holes there are (a fraction = one being dug). Never decreases."""
    n = 0.0
    for _, a, b, k in DIG:
        n += ramp(t, a, b)
    return n


def _land_body():
    return dog.body_point(dog.stand(0), LAND[0], LAND[1], DS)


def dog_state(t):
    """Everything about the lead dog at local time t, in WORLD coordinates.
    Returns dict(x, y, pose, facing, carry, anchor, bits)."""
    out = dict(carry=None, anchor=None, bits=None, facing=1)
    bx, by = _land_body()
    # ---- A: down to the gravel
    if t < 2.6:
        u = 1 - (1 - t / 2.6) ** 1.7
        p0, c, p1 = (300.0, 530.0), (372.0, 610.0), (bx - 4, by - 26)
        x = (1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * c[0] + u * u * p1[0]
        y = (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * c[1] + u * u * p1[1]
        pose = dog.blend(dog.swim_down(t + 0.4, steep=0.72), dog.swim(t + 0.4, effort=0.7), ease(t, 1.5, 2.5))
        out.update(x=x, y=y, pose=pose, anchor="body")
        return out
    if t < 3.0:
        u = ease(t, 2.6, 3.0)
        pose = dog.blend(dog.swim(t + 0.4, effort=0.5), _with(dog.stand(t), ear=0.2, ear_f=0.25, tail=0.6), u)
        pose["_anchor"] = "body"
        out.update(x=lerp(bx - 4, bx, u), y=lerp(by - 26, by, u * u), pose=pose, anchor="body")
        return out
    if t < 4.85:
        s = t - 3.0
        sq = (s / 0.08) if s < 0.08 else math.exp(-(s - 0.08) * 6.5) * math.cos((s - 0.08) * 10)
        pose = dog.stand(t)
        pose["cy"] -= 21 * sq
        pose["fnx"] += 13 * max(sq, 0)
        pose["ffx"] += 13 * max(sq, 0)
        pose["hnx"] -= 12 * max(sq, 0)
        pose["hfx"] -= 12 * max(sq, 0)
        pose["ear"] = lerp(0.2, 0.74, ease(s, 0.05, 0.6)) + 0.5 * bump(s / 0.3)
        pose["ear_f"] = lerp(0.25, 0.74, ease(s, 0.1, 0.7)) + 0.4 * bump((s - 0.05) / 0.3)
        pose["tail"] = lerp(0.6, 0.2, ease(s, 0.1, 0.8))
        if 0.55 <= s:                                   # it looks round at who is behind it
            lb = dog.look_back(s - 0.55, hold=0.55)
            pose = dog.blend(pose, lb, ease(s, 0.55, 0.75) * (1 - ease(s, 1.45, 1.6)))
        w_ = ease(t, 4.5, 4.8)                           # nose goes down: it has smelled something
        pose = dog.blend(pose, _sniff_walk(0.0), w_)
        f = lerp(1.0, -1.0, ease(t, 4.62, 4.78))
        if abs(f) < 0.12:
            f = 0.12 if f >= 0 else -0.12
        out.update(x=LAND[0], y=LAND[1], pose=pose, facing=f)
        return out
    out["facing"] = -1
    # ---- B: the three digs (facing left, backing from hole to hole)
    if t < 11.0:
        if t < DIG[0][0]:
            tau = t - 4.85
            dur = DIG[0][0] - 4.85
            rate = (LAND[0] - XA[0]) / DS / 64.0 / dur
            x = LAND[0] - DS * dog.travel("walk", tau, rate=rate)
            out.update(x=x, y=GY, pose=_sniff_walk(tau, rate))
            return out
        for k, (d0, a, b, _) in enumerate(DIG):
            nxt = DIG[k + 1][0] if k < 2 else 11.0
            if t < nxt:
                break
        tau = t - d0
        x = XA[k]
        stop = b - d0
        pose = dog.dig(min(tau, stop))
        bits = dog.dig_spray(tau, water=True) if tau < stop + 1.0 else None
        if bits and tau > stop:
            bits = [q for q in bits if True]
        carry = None
        if k == 0:
            # nothing: it looks in, one ear cocked; then backs to the next place
            look = _with(_dig_rest(0.0), ear=1.2, ear_f=0.3, head=-0.8)
            pose = dog.blend(pose, look, ease(t, b, b + 0.14))
            g = ease(t, 6.98, 7.14)
            if g > 0:
                pose = dog.blend(pose, _sniff_walk(t - 6.98, 2.4, back=True), g)
                x = lerp(XA[0], XA[1], g)
        elif k == 1:
            # the boot: head in, comes up with it, regards it, sets it aside
            up = ease(t, 7.95, 8.1)
            have = _with(_dig_rest(up), ear=lerp(1.05, 1.2, up), ear_f=lerp(1.05, 0.35, up), jaw=0.16)
            pose = dog.blend(pose, have, ease(t, b, b + 0.12))
            aside = ease(t, 8.3, 8.52)
            if aside > 0:
                put = _with(_dig_rest(0.0), neck=0.16, head=-0.5, pitch=-0.2, cy=77, jaw=0.16, ear=0.9, ear_f=0.9)
                pose = dog.blend(pose, put, aside)
            if b + 0.1 <= t < 8.52:
                carry = thing_sprite("boot")
                pose["hold"] = 1.0
            done = ease(t, 8.52, 8.62)
            if done > 0:
                pose = dog.blend(pose, _with(_dig_rest(0.6), jaw=0.0), done)
            g = ease(t, 8.58, 8.74)
            if g > 0:
                pose = dog.blend(pose, _sniff_walk(t - 8.58, 2.4, back=True), g)
                x = lerp(XA[1], XA[2], g)
        else:
            # the spool: head deep in the silt, a tug that does not give, a harder one that does
            tug1, tug2 = bump((t - 9.45) / 0.16), ease(t, 9.6, 9.84)
            deep = _with(_dig_rest(0.0), head=-0.86, neck=-0.1, cy=70 - 3 * tug1, jaw=0.14)
            pose = dog.blend(pose, deep, ease(t, b, b + 0.1))
            upk = tug2 * (1 + 0.12 * bump((t - 9.7) / 0.5))
            have = _with(_dig_rest(min(upk, 1.12)), jaw=0.14, ear=1.1, ear_f=1.1, tail=1.0)
            pose = dog.blend(pose, have, tug2)
            if t >= 9.6:
                carry = thing_sprite("spool")
                pose["hold"] = 1.0
                st = dog.carry_part(t, gait="stand")
                st = _with(st, wag=0.5 * math.sin(t * 13), tail=0.85, ear=1.05, ear_f=1.05)
                pose = dog.blend(pose, st, ease(t, 9.9, 10.3))
                lk = ease(t, 10.35, 10.7)                 # it looks up at the board: ears first
                pose = dog.blend(pose, _with(dog.look_up(st, 0.75), ear=1.2, ear_f=1.2, wag=0.0, tail=0.5), lk)
                pose["hold"] = 1.0
        out.update(x=x, y=GY, pose=pose, bits=(bits, x), carry=carry)
        return out
    # ---- C: to the board; the spool down; the nose to the page
    if t < 17.0:
        if t < 11.7:
            g = ease(t, 11.05, 11.65)
            x = lerp(XA[2], X_BOARD, g)
            p = dog.carry_part(t - 11.05, gait="walk") if 0 < g < 1 else dog.carry_part(t, gait="stand")
            out.update(x=x, y=GY, pose=_with(p, hold=1.0), carry=thing_sprite("spool"))
            return out
        if t < 12.95:
            p = dog.lay(t - 11.7)
            out.update(x=X_BOARD, y=GY, pose=p, carry=thing_sprite("spool") if p.get("hold", 1) >= 0.5 else None)
            return out
        lk = ease(t, 12.95, 13.25)
        up = ease(t, 13.3, 13.85)
        if t < 15.0:
            tn = lerp(0.0, 1.7, clamp((t - 13.3) / 1.7))
        elif t < 16.5:
            tn = 2.0                                           # THE HOLD: nothing of the dog moves
        else:
            tn = lerp(2.3, 3.0, (t - 16.5) / 0.5)
        if t < 13.3:
            p = _with(dog.look_up(dog.stand(t), 0.7 * lk), ear=lerp(0.72, 1.15, lk), ear_f=lerp(0.72, 1.18, lk))
        else:
            p = dog.blend(_with(dog.look_up(dog.stand(13.3), 0.7), ear=1.15, ear_f=1.18), rear(tn, 1.0, REACH_PAGE), up)
        if t >= 16.5:                                          # head off the page and round toward the school
            p = dog.over_shoulder(p, ease(t, 16.62, 16.98) * 0.9)
        out.update(x=X_BOARD, y=GY, pose=p)
        return out
    # ---- D: the child and its drawing
    if t < 22.5:
        s = dog.sit(t - 17.15) if t > 17.15 else dog.stand(t)
        s = dog.look_up(s, 0.22 * ease(t, 18.0, 18.5))
        s["ear"], s["ear_f"] = lerp(s["ear"], 1.18, ease(t, 17.7, 17.9)), lerp(s["ear_f"], 1.2, ease(t, 17.75, 18.0))
        back = ease(t, 19.3, 19.75) * (1 - ease(t, 20.3, 20.75))      # bubble -> board page -> bubble
        s = dog.over_shoulder(s, back * 0.8)
        if t >= 21.0:                                           # THE HOLD on the wobble
            h = dog.look_up(dog.sit(5.0), 0.22)
            h["ear"], h["ear_f"] = 1.18, 1.2
            s = h
            fl = bump((t - 22.3) / 0.2)                         # the teacher nods; one ear answers
            s["ear"] -= 0.45 * fl
            s["tail"] = s.get("tail", 0.15) + 0.2 * ease(t, 22.3, 22.5)
        out.update(x=SIT_X, y=GY, pose=s, facing=1)
        return out
    # ---- E: the pin, then the page by one corner; the spool nosed to the leg
    if t < 25.5:
        if t < 24.55:
            pin = ease(t, 22.55, 22.95)
            p = rear(2.0, 1.0, REACH_PAGE, pin * (1 - ease(t, 23.35, 23.7)))
            p["jaw"] = 0.1 * pin * (1 - ease(t, 23.3, 23.4)) + 0.2 * ease(t, 23.5, 23.9) * (1 - 0.5 * ease(t, 24.0, 24.2))
            p["head"] -= 0.12 * bump((t - 23.0) / 0.3)          # the small pull that takes the pin out
            p["head"] -= 0.10 * ease(t, 23.6, 24.0)             # head tips to the page's corner
            p["cx"] += 5 * ease(t, 24.15, 24.5)                 # draws back, slowly: the page is soft
            p["ear"], p["ear_f"] = 1.1, 1.12
            carry = page_sprite() if t >= 24.5 else None
            p["hold"] = 1.0
            out.update(x=X_BOARD, y=GY, pose=p, carry=carry)
            return out
        dn = ease(t, 24.55, 24.95)
        p = dog.blend(rear(2.0, 1.0, REACH_PAGE), dog.carry_page(t, gait="stand"), dn)
        nose = ease(t, 24.95, 25.2) * (1 - ease(t, 25.36, 25.5))
        p = dog.blend(p, _with(dog.carry_page(t, gait="stand"), neck=0.02, head=-0.5, pitch=-0.16, cy=78, cx=6), nose)
        p["hold"] = 1.0
        out.update(x=X_BOARD, y=GY, pose=p, carry=page_sprite())
        return out
    # ---- F, G: up, with the page
    b0 = dog.body_point(dog.stand(0), X_BOARD, GY, DS, facing=-1)
    pts = [(25.5, b0[0], b0[1] - 4), (26.2, b0[0] - 3, b0[1] - 34), (28.5, 450.0, 612.0), (30.0, 430.0, 550.0)]
    for (ta, xa, ya), (tb, xb, yb) in zip(pts, pts[1:]):
        if t <= tb:
            u = (t - ta) / (tb - ta)
            if ta == 25.5:
                u = u * u
            x, y = lerp(xa, xb, u), lerp(ya, yb, u)
            break
    else:
        x, y = pts[-1][1], pts[-1][2]
    p = dog.carry_page(t, gait="swim_up", steep=lerp(0.5, 0.78, ease(t, 28.3, 29.2)))
    if t < 26.3:
        st = dog.carry_page(t, gait="stand")
        st["_anchor"] = "body"
        p = dog.blend(st, p, ease(t, 25.5, 26.2))
        p["_anchor"] = "body"
    lk = ease(t, 27.25, 27.7) * (1 - ease(t, 28.9, 29.4))        # it looks up at her as it passes
    p = dog.over_shoulder(dog.look_up(p, 0.6 * lk), 0.75 * lk)
    p["hold"] = 1.0
    out.update(x=x, y=y, pose=p, facing=-1, carry=page_sprite(), anchor="body")
    return out


def draw_dog(ink, t, cam, st=None):
    st = st or dog_state(t)
    sx, sy = cam.xy(st["x"], st["y"])
    sc = DS * cam.zoom
    if st["bits"] and st["bits"][0]:
        bx, _ = cam.xy(st["bits"][1], GY)
        dog.draw_bits(ink, st["bits"][0], bx, sy, sc, facing=-1, color=(150, 160, 136))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    j = dog.draw_dog(ink, st["pose"], sx, sy, scale=sc, facing=st["facing"], carry=st["carry"], anchor=st["anchor"],
                     tint=TEAL, tint_amount=0.26, shadow=False, ss=2 if sc > 1.6 else 3)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    return j


def dog_head_world(t):
    st = dog_state(t)
    return (st["x"] + 40 * (1 if st["facing"] > 0 else -1), st["y"] - (50 if st["anchor"] != "body" else 0))


# ====================================================================== #
#  THE PEOPLEFISH                                                        #
# ====================================================================== #

LINE_KIDS = [5, 3, 6, 1, 4, 7, 2, 0]         # the class in file behind the teacher; the jaw child is last
FENCE = {k: (668 - 15.0 * i, 808 + (4 if i % 2 else -5)) for i, k in enumerate(LINE_KIDS)}
FENCE[0] = (556.0, 810.0)
TEACHER_FENCE = (696.0, 812.0)
WAVER = 2                                     # yellow satchel


def _lead_x(t):
    if t < 0.2:
        return -40.0
    if t <= 3.0:
        return -40 + 108 * (t - 0.2)
    return -40 + 108 * 2.8 + 108 * 0.16 * (1 - math.exp(-(t - 3.0) / 0.16))


def head_tilt(t):
    """The class's heads going over together as they watch the digging."""
    return (10 * bump((t - 6.55) / 0.9) - 9 * bump((t - 8.0) / 0.7) + 12 * ease(t, 9.75, 10.1) * (1 - ease(t, 10.8, 11.0)))


def kid_state(i, t):
    """Line position i (0 = teacher, 1..8 = children) in shots A to D -> dict(x, y, facing, tilt, swim, look_dog)."""
    gap = 31 - 3.5 * ease(t, 3.0, 3.7)
    x = _lead_x(t) - i * gap
    tilt, facing, look_dog = 10.0, 1, t > 2.9 + 0.05 * i
    if i == 8:                                           # the straggler, looking at the diner, walks into the next one
        x += 15 * ease(t, 3.0, 4.0) - 13 * ease(t, 4.0, 4.3)
        look_dog = t > 4.15
        tilt += -14 * bump((t - 4.0) / 0.45)
    if i == 7:
        x += 5 * bump((t - 4.0) / 0.4)
        tilt += 17 * bump((t - 4.0) / 0.4)
    y = 808 + 2.2 * math.sin(t * 7.5 + i * 1.9) * (1 - ease(t, 3.0, 3.4))
    if t < 3.0:
        tilt = 13 + 4 * math.sin(t * 7.5 + i * 1.9)
    # the teacher walks them on to the yard, behind the digging
    s0 = 4.45 + 0.07 * i
    tx, ty = TEACHER_FENCE if i == 0 else FENCE[LINE_KIDS[i - 1]]
    if t > s0:
        run = 175 * (t - s0) * ease(t, s0, s0 + 0.35)
        if x + run < tx:
            x += run
            tilt = 30 + 4 * math.sin(t * 11 + i)
            y = 806 + 2.5 * math.sin(t * 11 + i)
            return dict(x=x, y=y, facing=1, tilt=tilt, swim=1.0, look_dog=True, there=False)
        arr = s0 + (tx - x) / 175 + 0.2
        x, y = tx, ty
        facing = -1
        tilt = 6 + head_tilt(t) * (1 if i else 0.4) + 14 * (1 - ease(t, arr, arr + 0.4))
        if i == 0:
            tilt += 24 * bump((t - 22.26) / 0.26)             # the teacher nods once
        return dict(x=x, y=y, facing=facing, tilt=tilt, swim=0.4, look_dog=True, there=True)
    return dict(x=x, y=y, facing=facing, tilt=tilt, swim=1.0 if t < 3.0 else 0.4, look_dog=look_dog, there=False)


def kid0_state(t):
    """The jaw child in shot D: over the fence to the dog, the bubble, the pointing."""
    fx, fy = FENCE[0]
    u = ease(t, 16.9, 17.6)
    x = lerp(fx, KID0_AT[0], u)
    y = lerp(fy, KID0_AT[1], u) - 30 * math.sin(math.pi * u)
    tilt = 48 * math.sin(math.pi * u) * (1 if u < 1 else 0)
    arm = 30.0
    arm = lerp(arm, 152, ease(t, 19.0, 19.3))                     # this,
    arm = lerp(arm, 4, ease(t, 19.75, 20.05))                     # is mine
    tilt -= 9 * bump((t - 19.8) / 0.6)
    arm = lerp(arm, 96, ease(t, 20.6, 21.0))                      # holds it out, and holds it still
    return dict(x=x, y=y, tilt=tilt, arm=arm)


def bubble_state(t):
    grow = ramp(t, 17.6, 19.0)
    prog = ramp(t, 17.95, 19.35)
    rise = 26 * ease(t, 23.3, 24.6) + 30 * ramp(t, 24.6, 25.0)
    pop = ramp(t, 24.62, 24.95)
    return grow, prog, rise, pop


def waver_state(t):
    sx, sy = town.SEATS[WAVER]
    u = ease(t, 25.6, 27.25)
    x = lerp(sx, 596.0, u) + 16 * math.sin(math.pi * u)
    y = lerp(sy - 8, 474.0, u) + 2.5 * math.sin(t * 2.4)
    tilt = 40 * math.sin(math.pi * clamp(u * 1.02)) * (1 - ease(t, 27.0, 27.3))
    wav = ease(t, 27.25, 27.4) * (1 - ease(t, 28.05, 28.25))
    arm = 30 + 96 * ease(t, 27.2, 27.4) + 34 * math.sin(t * 10) * wav
    tilt += 9 * math.sin(t * 10 + 0.6) * wav                     # it waves with all of itself
    return dict(x=x, y=y, tilt=tilt, arm=arm)


# ====================================================================== #
#  THE COW (above the line, and what of her comes through it)            #
# ====================================================================== #

COW_X = 600 - herd.reach("lead")


def cow_state(t):
    """The lead cow at the drinking place in the split shot -> dict(pose, x, tilt, nose_to, leg, eye)."""
    ld = herd.look_down(t, 1.0, "lead")
    step = ease(t, 25.85, 26.15)
    plunge = ease(t, 26.15, 26.24)
    back = ease(t, 26.26, 26.7)
    pose = dict(ld)
    fx = lerp(60, 97, step) + 3 * plunge
    fy = 6 * step + 12 * plunge
    fx = lerp(fx, 50, back)
    fy = lerp(fy, 0, back) - 24 * bump((t - 26.26) / 0.44)
    pose["nf"] = ("ik", fx, fy)
    tilt = 4 * step + 7 * plunge - 15 * ease(t, 26.26, 26.5) + 4 * ease(t, 26.5, 27.0)
    x = COW_X + 4 * step - 15 * back + 11 * ease(t, 27.0, 27.5)
    alert = herd.with_(herd.stand(t, "lead", chew=0, alert=1), eye=1.7)
    up = ease(t, 26.24, 26.42)
    down = ease(t, 27.0, 27.5)
    if up > 0:
        pose = herd.tween(pose, herd.with_(alert, nf=pose["nf"]), up, "out", "lead")
    if down > 0:
        pose = herd.tween(pose, herd.drink(t, 1.0, "lead"), down, "slow", "lead")
    pose = dict(pose)
    if t > 27.6:
        e = pose.get("ear", 0.0)
        if isinstance(e, (int, float)):
            pose["ear"] = e + 16 * bump((t - 27.72) / 0.28) + 9 * ease(t, 27.9, 28.0)
    nose_amt = (1 - up) + down
    nose_to = (598.0, 376.0) if t < 26.3 else (600.0, 401.0)
    pose["_nose"] = clamp(nose_amt)
    # how far her leg has gone through the line, in world px (the board: to the knee)
    leg = 18 * ease(t, 25.98, 26.15) + 38 * plunge
    leg *= 1 - ease(t, 26.28, 26.52)
    return dict(pose=pose, x=x, tilt=tilt, nose_to=nose_to, leg=leg)


def muzzle_dip(t):
    """How far her muzzle is in the water, seen from below, in the under-water shots (0..1)."""
    if t < 5.0:
        return 1.0 - 0.12 * bump(t / 1.8) - 0.1 * bump((t - 2.6) / 2.0)
    return 1.0


def draw_leg_below(ink, t, cam, wx, depth):
    """Her foreleg come down through the line: a shin and a hoof, dark, wobbling, with nothing under it."""
    if depth < 1:
        return
    z = cam.zoom
    sx, ys = cam.xy(wx, town.SURFACE_Y)
    d = depth * z
    wob = math.sin(t * 19) * 1.6 * z
    col = (38, 40, 50)
    pts = [(sx - 8 * z, ys - 2), (sx + 8 * z, ys - 2), (sx + 6.5 * z + wob, ys + d * 0.72), (sx + 11 * z + wob, ys + d),
           (sx - 9 * z + wob, ys + d), (sx - 6.5 * z + wob, ys + d * 0.72)]
    ink.d.polygon(pts, fill=col + (255,))
    ink.d.line([(sx - 7 * z + wob, ys + d * 0.76), (sx + 8 * z + wob, ys + d * 0.76)], fill=(96, 96, 96, 255), width=max(1, int(1.6 * z)))
    ink.d.line([(sx + wob + z, ys + d * 0.78), (sx + wob + z, ys + d)], fill=(12, 12, 16, 255), width=max(1, int(1.2 * z)))
    rs = random.Random(int(t * 12))
    for q in range(16):                                   # the air she took down with her
        bx = sx + rs.uniform(-22, 24) * z
        by = ys + rs.uniform(2, d + 14)
        r = rs.uniform(1.6, 5.0) * z
        ink.d.ellipse([bx - r, by - r, bx + r, by + r], outline=(226, 246, 238, 210), width=max(1, int(1.2 * z)))


def draw_blown(ink, t, cam, t0, wx=600.0):
    """She blows into the water: a string of fat bubbles that go down a little, wobble, and come back up."""
    z = cam.zoom
    ys = cam.surface()
    for q in range(9):
        a = t - t0 - q * 0.07
        if a <= 0 or a > 1.5:
            continue
        down = 34 * (1 - math.exp(-a * 5)) - 22 * max(0.0, a - 0.45) ** 1.4 * 2.2
        if down < 0:
            continue
        bx = cam.xy(wx + (q - 3) * 4.5 + 5 * math.sin(a * 9 + q), 0)[0]
        by = ys + 5 * z + down * z
        r = (4.5 + 3.6 * ((q * 37) % 5) / 4) * z * (0.6 + 0.4 * clamp(a * 5))
        ink.d.ellipse([bx - r, by - r, bx + r, by + r], fill=(200, 236, 226, 46), outline=(232, 250, 242, 235), width=max(1, int(1.5 * z)))
        ink.d.arc([bx - r * 0.6, by - r * 0.6, bx + r * 0.2, by + r * 0.2], 180, 270, fill=(255, 255, 255, 230), width=max(1, int(1.2 * z)))


# ====================================================================== #
#  DRAWING A FRAME                                                       #
# ====================================================================== #

def _smudge(ink, cam, a=1.0):
    sx, sy = cam.xy(*NOSE_AT)
    z = cam.zoom
    r = 3.4 * z
    lay = Image.new("RGBA", (int(r * 4) + 4, int(r * 4) + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = lay.width / 2
    d.ellipse([c - r, c - r * 0.82, c + r, c + r * 0.82], fill=(96, 132, 134, int(120 * a)), outline=(70, 108, 112, int(190 * a)), width=max(1, int(0.5 * z)))
    d.ellipse([c - r * 0.5, c - r * 0.5, c - r * 0.1, c - r * 0.22], fill=(214, 236, 230, int(150 * a)))
    ink.img.paste(lay, (int(sx - c), int(sy - c)), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _trail(ink, t, cam):
    """The bubble trail the dog left coming down from the line at x = 590 (S1's last frame carries it)."""
    if t > 3.2:
        return
    z = cam.zoom
    ys = cam.surface()
    for q in range(16):
        u = (q + 0.5) / 16
        ta = -2.2 * (1 - u)                                      # when the dog was there (before our first frame)
        wx = lerp(590, 300, u ** 1.15) + 5 * math.sin(q * 2.1 + t * 3)
        wy = lerp(404, 530, u ** 1.3) - 34 * (t - ta) * 0.5
        sx, sy = cam.xy(wx, wy)
        if sy < ys + 3:
            continue
        r = (1.5 + (q * 7 % 4) * 0.7) * z
        a = int(230 * clamp(1 - (t - ta) / 4.6))
        if a > 8:
            ink.d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(226, 246, 238, a), width=max(1, int(1.2 * z)))


def _pin_xy(t):
    """The pin, let fall: it goes down slowly, tumbling, and lies on the gravel."""
    a = t - 23.32
    if a < 0:
        return None
    fall = min(1.0, a / 1.25)
    x = PIN_AT[0] - 9 * fall + 5 * math.sin(a * 7) * (1 - fall)
    y = lerp(PIN_AT[1] + 4, 812.0, fall ** 1.25)
    ang = 200 * a if fall < 1 else 74
    return x, y, ang


def _class_walking(ink, t, cam, look):
    order = sorted(range(9), key=lambda i: kid_state(i, t)["y"])
    for i in order:
        s = kid_state(i, t)
        if s["x"] < -40:
            continue
        lk = look if s["look_dog"] else (150, 716)
        if i == 0:
            town.fish(ink, t, cam, s["x"], s["y"] + 4, kind="teacher", facing=s["facing"], tilt=s["tilt"] * 0.6,
                      arm=62 if not s["there"] else 30, look=lk, hold="pointer", swim=s["swim"])
        else:
            k = LINE_KIDS[i - 1]
            if k == 0 and t >= 16.9:
                continue
            town.child(ink, t, cam, k, s["x"], s["y"], facing=s["facing"], tilt=s["tilt"], look=lk, swim=s["swim"],
                       arm=24 + (40 * bump((t - 4.0) / 0.5) if i == 8 else 0))


def _town_frame(ink, t, shot, cam):
    name = shot[2]
    st = dog_state(t)
    dogw = dog_head_world(t)
    door = _key(FOCUS, t, 4)
    states = atmos(t)
    still = "suspend" in states
    # --- far glass
    bell = 0.0
    if 0.45 < t < 2.4:
        bell = 24 * math.sin(7.2 * (t - 0.45)) * math.exp(-(t - 0.45) * 1.1)
    town.back(ink, t, cam, door=door)
    if cam.surface() > -30:
        town.touch(ink, t, cam, 600, "muzzle", dip=muzzle_dip(t))
    _blur_rows(ink, cam.surface() + 8 * cam.zoom, H, blur_px(0.55, t))
    # --- the street glass
    pull, taken = None, ()
    if t >= 24.5:
        taken = (0,)
    elif t >= 23.0:
        pull = (0, 0.5 * ease(t, 23.0, 23.3) + 0.5 * ease(t, 23.55, 24.5))
    wide = name in ("A wide", "G up")
    town.street(ink, t, cam, bell=bell, holes=holes_at(t), smudges=1 if (wide and t > 15) else 0, pull=pull, taken=taken)
    if 15.0 <= t < 24.5 and not wide:
        _smudge(ink, cam, 1.0)
    if t >= 8.5:
        town.thing(ink, cam, "boot", BOOT_AT[0], BOOT_AT[1], 8)
    if t >= 11.7 + 0.62:
        k = ease(t, 25.0, 25.3)
        town.thing(ink, cam, "spool", lerp(SPOOL_AT[0], SPOOL_END[0], k), lerp(SPOOL_AT[1], SPOOL_END[1], k))
    pin = _pin_xy(t)
    if pin:
        town.thing(ink, cam, "pin", pin[0], pin[1], pin[2])
    draw_silt(ink, t, cam, front=False)
    # --- the cast
    town.townsfolk(ink, t, cam, look=dogw)
    if t < 17.0:
        _class_walking(ink, t, cam, dogw)
    elif t < 22.5:
        _class_walking(ink, t, cam, dogw)
    elif t < 25.5:
        pass
    else:
        town.school_class(ink, t, cam, look=dogw, tilt=-8, skip=(WAVER,),
                          arm={0: 124 + 30 * math.sin(t * 9) if t > 28.6 else 24})
    if 16.9 <= t < 25.5:
        ks = kid0_state(t)
        grow, prog, rise, pop = bubble_state(t)
        r = town.child(ink, t, cam, 0, ks["x"], ks["y"], facing=-1 if t > 17.3 else -1, tilt=ks["tilt"], arm=ks["arm"],
                       look=(dogw if t < 23 else NOSE_AT), swim=0.25 if t > 17.6 else 1.0, mouth_open=1.0 if 17.6 < t < 19.0 else 0.0)
        if grow > 0 and pop < 1:
            town.bubble(ink, t, cam, r["mouth"], "jaw", grow=grow, progress=prog, r=BUBBLE_R, side=1, pop=pop, rise=rise,
                        screen=True, calm=still)
    if t >= 25.5:
        ws = waver_state(t)
        town.child(ink, t, cam, WAVER, ws["x"], ws["y"], facing=1, tilt=ws["tilt"], arm=ws["arm"], look=(604, 396), swim=0.6)
    j = draw_dog(ink, t, cam, st)
    if 22.95 <= t < 23.32:                                       # the pin in its front teeth
        px, py = j["mouth"]
        z = cam.zoom
        ink.d.line([(px, py), (px - 5 * z, py - 3 * z)], fill=(190, 196, 190, 255), width=max(1, int(1.2 * z)))
        ink.d.ellipse([px - 7.2 * z, py - 5.2 * z, px - 2.8 * z, py - 0.8 * z], fill=(206, 60, 54, 255), outline=(14, 30, 34, 255))
    _trail(ink, t, cam)
    # --- near glass
    draw_silt(ink, t, cam, front=True)
    town.front(ink, t, cam, calm=still)
    draw_dress(ink, t, shot, cam)
    return j


def _split_frame(ink, t, shot, cam):
    oy = 250
    cs = cow_state(t)
    st = dog_state(t)
    dogw = (st["x"], st["y"])
    anchors = {}

    def hill(ink, t, oy):
        for k, who in enumerate(("second", "mother", "calf", "fourth", "fifth", "sixth")):
            pl = herd.PATH.at(herd.hill_spot(k))
            if pl["layer"] == "hill":
                herd.cow(ink, who, herd.stand(t, who), pl["x"], pl["y"], pl["s"] * herd.S if pl["s"] < 2 else pl["s"],
                         pl["facing"], oy, far=0.15 * k)

    def strip(ink, t, oy):
        pl = herd.PATH.at(herd.hill_spot(0))
        if pl["layer"] != "hill":
            herd.cow(ink, "second", herd.stand(t, "second"), pl["x"], pl["y"], pl["s"] * herd.S if pl["s"] < 2 else pl["s"],
                     pl["facing"], oy)
        anchors["lead"] = herd.cow(ink, "lead", cs["pose"], cs["x"], 388, facing=1, oy=oy, nose_to=cs["nose_to"], tilt=cs["tilt"])

    def under(ink, t, oy):
        air = _key(FOCUS, t, 3)
        _blur_rows(ink, 0, cam.surface() - 2, (1 - air) * 1.7)          # the bank, when the lens is on the dog
        town.back(ink, t, cam, sky=False, door=_key(FOCUS, t, 4))
        town.street(ink, t, cam, holes=3, taken=(0,))
        town.thing(ink, cam, "boot", BOOT_AT[0], BOOT_AT[1], 8)
        town.thing(ink, cam, "spool", *SPOOL_END)
        town.thing(ink, cam, "pin", *_pin_xy(t)[:2], 74)
        town.townsfolk(ink, t, cam, look=(600, 400))
        town.school_class(ink, t, cam, look=(600, 400) if t > 26.2 else dogw, tilt=-8, skip=(WAVER,))
        ws = waver_state(t)
        town.child(ink, t, cam, WAVER, ws["x"], ws["y"], facing=1, tilt=ws["tilt"], arm=ws["arm"], look=(604, 392), swim=0.6)
        draw_dog(ink, t, cam, st)
        a = anchors.get("lead")
        hx = (a["hooves"]["nf"][0] if a else 590)
        draw_leg_below(ink, t, cam, hx, cs["leg"])
        draw_blown(ink, t, cam, 27.42)
        town.front(ink, t, cam)
        _blur_rows(ink, cam.surface() + 3, H, air * 1.3)                 # the town, when the lens is on the cow

    def front(ink, t, oy):
        a = anchors.get("lead")
        hx = (a["hooves"]["nf"][0] if a else 590)
        porch.splash(ink, t, oy, hx, t - 26.17, 1.25, "in")

    rings = [porch.ring(590, 26.17, 1.6), porch.ring(600, 27.42, 0.8), porch.ring(600, 22.0 - T0 + 0.0, 0.5)]
    porch.scene(ink, t, oy, cast=dict(hill=hill, strip=strip, under=under, front=front),
                q=porch.pose("sit", p=0.5 + 0.5 * math.sin(t * 2.2)), door=0.25, radio_on=1.0, pebbles="w", rings=rings)
    zoom = 1 + 0.5 * ease(t, *shot[6])
    if zoom > 1.001:
        porch.push(ink, 585, 150, zoom)


def draw(t, ink):
    """One full 960x540 frame of S2 at local time t (0..30)."""
    t = clamp(t, 0.0, SECONDS)
    shot = shot_at(min(t, SECONDS - 1e-6))
    cam = cam_at(t)
    if shot[3] == "split":
        _split_frame(ink, t, shot, cam)
    else:
        _town_frame(ink, t, shot, cam)
    v = 0.22 * ease(t, 0.0, 1.5) * (1 - ease(t, 28.6, 29.8))        # none at the two ends: the neighbours have none
    if v > 0.01:
        ink.vignette(round(v, 2))


# ====================================================================== #
#  SOUND (depth audio)                                                   #
# ====================================================================== #

def heard(t, wx, wy, z=1.0):
    """Depth audio: where a source at world (wx, wy) on plane z is for the ear, which is where the camera is.
    Returns (gain factor, pan, under): pan from its screen x, level from the shot's scale and its distance from
    the middle of frame, `under` = how it is filtered (True: through the whole depth of water; a number: a
    cut-off in Hz for something close to the lens under water; False: in air)."""
    shot = shot_at(t)
    cam = cam_at(t)
    sx, sy = cam.xy(wx, wy, z)
    pan = clamp((sx - W / 2) / (W / 2), -1, 1) * 0.75
    near = clamp(cam.zoom / 2.3, 0.45, 1.5) ** 0.5
    off = math.hypot((sx - W / 2) / W, (sy - H / 2) / H)
    gain = near * clamp(1.15 - 0.6 * off, 0.4, 1.15)
    above = wy < town.SURFACE_Y
    if shot[3] == "split":
        under = False if above else True
        gain *= 0.85
    else:
        under = True if above else (1500 if cam.zoom > 1.8 else True)
    return gain, pan, under


def sound(mix, at=0.0):
    """Lay S2's sound into `mix` with local 0 at `at` seconds. All times below are local."""
    def A(t):
        return at + t

    # the rooms: below; both at half in the split shot; below again
    snd.hush(mix, A(-0.1), 25.6, 1.0, 0.2, 0.2)
    snd.hush(mix, A(25.4), 3.2, 0.5, 0.2, 0.2)
    snd.above(mix, A(25.4), 3.2, 0.5, 0.2, 0.2)
    snd.hush(mix, A(28.4), 1.7, 1.0, 0.2, 0.2)
    snd.music_s2(mix, t0=at)                                   # the school bell twice; one lamp answers at the end
    # the class
    g, p, u = heard(1.4, 60, 780)
    snd.fish_murmur(mix, A(1.2), 1.8, gain=0.03 * g, pan=p)
    g, p, u = heard(3.0, *LAND)
    snd.land(mix, A(3.0), pan=p)
    snd.nose_bump(mix, A(4.0), pan=heard(4.0, 60, 800)[1])     # the last child into the one in front
    snd.sniff(mix, A(5.1), 3, gain=0.05, pan=heard(5.1, 400, 810)[1], under=1500)
    # three digs: nothing; the boot; the spool
    for k, (d0, a, b, _) in enumerate(DIG):
        g, p, u = heard(a, *HOLE[k])
        snd.dig(mix, A(a), b - a, find=(None, "thud", "ring")[k], gain=0.14 * g, pan=p, under=u)
    g, p, u = heard(8.5, *BOOT_AT)
    snd.set_down(mix, A(8.5), pan=p)
    snd.bubbles(mix, A(9.7), 4, 0.6, gain=0.04, pan=heard(9.7, *HOLE[2])[1])
    # the board
    g, p, u = heard(12.32, *SPOOL_AT)
    snd.set_down(mix, A(12.32), pan=p)
    snd.sniff(mix, A(14.1), 2, gain=0.05 * heard(14.1, *NOSE_AT)[0], pan=heard(14.1, *NOSE_AT)[1], under=1500)
    snd.sniff(mix, A(14.6), 2, gain=0.04, pan=heard(14.6, *NOSE_AT)[1], under=1500)
    snd.duck(mix, A(15.0), A(16.5), 0.6)                       # the hold: the room itself drops
    # the drawing
    g, p, u = heard(17.6, *KID0_AT)
    snd.bubble_picture(mix, A(17.6), 1.5, pan=p)
    snd.fish_murmur(mix, A(19.75), 0.8, gain=0.02, pan=p)
    # the page
    g, p, u = heard(23.0, *PIN_AT)
    snd.page_taken(mix, A(23.0), pan=p)
    snd.bubbles(mix, A(24.62), 3, 0.35, gain=0.05, pan=heard(24.62, KID0_AT[0], 700)[1])
    snd.set_down(mix, A(25.1), gain=0.05, pan=heard(25.1, *SPOOL_END)[1])
    # the cow who cannot follow
    g, p, u = heard(26.17, 590, 396)
    snd.plunge(mix, A(26.17), 1.6, gain=0.3, pan=p)
    snd.cowbell(mix, A(26.22), 3, 0.2, gain=0.07, pan=p, hard=True)
    snd.hooves(mix, A(26.42), 3, 0.2, "wood", gain=0.09, pan=p)
    snd.moo(mix, A(26.75), 0.7, pan=p)
    snd.bubbles(mix, A(27.42), 6, 0.8, low=True, gain=0.07, pan=p)
    snd.cowbell(mix, A(27.3), 1, gain=0.04, pan=p)
    # up
    snd.bubbles(mix, A(28.7), 5, 1.2, gain=0.03, pan=heard(29.0, 440, 600)[1])
    return mix


# ====================================================================== #
#  CHECKS                                                                #
# ====================================================================== #

def _pose_diff(a, b):
    return max(abs(a[k] - b[k]) for k in a if isinstance(a[k], (int, float)) and k in b)


def check():
    out = []
    # 1 · parallax respects depth: in every shot whose camera moves, a nearer plane moves at least as far on screen
    for s in SHOTS:
        if s[3] != "town":
            continue
        a, b = s[4], s[5]
        if (a.ox, a.oy, a.zoom) == (b.ox, b.oy, b.zoom):
            continue
        mags, pans = [], []
        for name, z, _ in PLANES:
            mags.append(b.s(z) / a.s(z))                                  # how much the plane grows in the move
            ca, cb = a.centre(z), b.centre(z)
            pans.append(math.hypot(cb[0] - ca[0], cb[1] - ca[1]) * b.s(z))   # how far the plane slides, in screen px
        grow = b.zoom >= a.zoom
        assert all((m2 >= m1 - 1e-9) if grow else (m2 <= m1 + 1e-9) for m1, m2 in zip(mags, mags[1:])), (s[2], mags)
        assert all(p2 >= p1 - 1e-6 for p1, p2 in zip(pans, pans[1:])), (s[2], pans)
        out.append(f"MEASURED parallax {s[2]}: slide " + " <= ".join(f"{m:.0f}" for m in pans) + " px; growth "
                   + " <= ".join(f"{m:.2f}" for m in mags) + " for z " + ", ".join(str(z) for _, z, _ in PLANES))
    # 2 · the planes are stacked in z order and focus blur grows away from the focus plane
    zs = [z for _, z, _ in PLANES]
    assert zs == sorted(zs)
    assert blur_px(0.45, 15.5) > blur_px(0.72, 15.5) > blur_px(1.0, 15.5) == 0 < blur_px(1.8, 15.5) < blur_px(2.3, 15.5)
    out.append(f"MEASURED defocus at the hold (t 15.5): far {blur_px(0.45, 15.5):.1f} px, back row {blur_px(0.72, 15.5):.1f}, "
               f"street 0, near glass {blur_px(1.8, 15.5):.1f} and {blur_px(2.3, 15.5):.1f}")
    # 3 · the fog is a field, not an overlay: it is uneven, and the two halves differ
    cam = cam_at(9.4)
    fb, ff = silt_field(9.4, cam, False), silt_field(9.4, cam, True)
    assert fb is not None and ff is not None
    for f in (fb, ff):
        on = f[f > 0.02]
        assert on.size > 200 and on.std() / on.mean() > 0.35 and (f > 0.02).mean() < 0.6
    assert np.abs(fb - ff).max() > 0.1
    assert silt_field(16.0, cam_at(16.0), True) is None or silt_field(16.0, cam_at(16.0), True).max() < 0.02
    out.append(f"MEASURED silt at t 9.4: covers {100 * (ff > 0.02).mean():.0f}% of frame (front), peak {ff.max():.2f}, "
               f"unevenness (sd/mean) {ff[ff > 0.02].std() / ff[ff > 0.02].mean():.2f}; gone by t 16")
    # 4 · holes never fill in; three at the end
    hs = [holes_at(k / 24) for k in range(int(SECONDS * 24) + 1)]
    assert all(b >= a for a, b in zip(hs, hs[1:])) and hs[-1] == 3.0 and hs[0] == 0.0
    out.append("MEASURED holes: 0 at 28.0, never fewer than before, 3 from 37.45")
    # 5 · the holds: nothing of the dog moves
    for a, b, what in ((15.0, 16.5, "nose on the page (43.0-44.5)"), (21.0, 22.28, "on the wobble (49.0-50.3)")):
        sa = dog_state(a + 0.02)
        for q in range(1, 12):
            sb = dog_state(lerp(a + 0.02, b - 0.02, q / 11))
            assert _pose_diff(sa["pose"], sb["pose"]) < 1e-9 and sa["x"] == sb["x"], what
        out.append(f"MEASURED hold {what}: dog pose identical over {b - a:.2f} s")
    # 6 · boundary frames
    c0 = cam_at(0.0)
    s0 = dog_state(0.0)
    assert (c0.oy, c0.ox, c0.zoom) == (360, 0, 1) and c0.xy(s0["x"], s0["y"]) == (300.0, 170.0)
    c1 = cam_at(SECONDS)
    s1 = dog_state(SECONDS)
    assert (c1.oy, c1.ox, c1.zoom) == (360, 0, 1) and c1.xy(s1["x"], s1["y"]) == (430.0, 190.0) and s1["facing"] == -1
    out.append("MEASURED boundaries: F-TOWN at both ends; dog body at screen (300, 170) at 28.0 and (430, 190) at 58.0, heading up-left")
    # 7 · no cow under the line beyond one leg: the cow is drawn by porch.scene before the water, which repaints
    # everything below the line; only draw_leg_below and town.touch put any of her there
    assert max(cow_state(25.5 + k / 24)["leg"] for k in range(72)) <= 58
    out.append("STRUCTURAL no cow below the line except a muzzle (town.touch) and one foreleg, at most 56 px deep (to the knee)")
    # 8 · every time the dog goes into the gravel we see what it has: nothing (it looks in), a boot, a spool
    assert dog_state(8.2)["carry"] is not None and dog_state(9.9)["carry"] is not None and dog_state(29.0)["carry"] is not None
    out.append("MEASURED carried: boot at t 8.2, spool at t 9.9, the page from t 24.5 to the end")
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    for line in check():
        print(line)
    if args and args[0] == "--check":
        sys.exit(0)
    if args and args[0] == "--stills":
        out = Path(args[1])
        out.mkdir(parents=True, exist_ok=True)
        for a in args[2:]:
            t = float(a)
            k = int(round(t * FPS))
            ink = kit.Ink(k / FPS, k, (W, H), boil=8, wobble=1.2, seed=2)
            ink.paper()
            draw(k / FPS, ink)
            ink.finish().save(out / f"{t:06.2f}.png")
        print("stills ->", out)
        sys.exit(0)
    film = kit.Film("dogs-s2", seconds=SECONDS, seed=2)
    film.picture(draw)
    film.sound(lambda mix: sound(mix, 0.0))
    film.render()
