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

REPAIR (SCION law 10), after an independent critic who saw only the picture: the cow and the dog were stacked in
one frame for three seconds and never dealt with each other. Cause: the board gave the cow one shot (F-SPLIT, both
small, 400 px apart) and gave the dog nothing to do with her. Now there are two close two-shots AT THE LINE
(_line_frame): before the dog goes down to the town her forefoot comes through the line after it, finds no bottom,
and the dog turns back up and puts its nose to her muzzle; and when it comes up with the page it holds the page
under her nose, she breathes on it, lifts her head and chews again. EDIT is the cut; performances stay on the
story clock. The time came out of the digs (cut to the three attempts, a new angle each, less silt over the dog),
the two holds, and the old split shot. Not changed, and why: the jaw drawing in the bubble (the film's contract:
S3 and S6 use the same strokes) and town.py's notice board.

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

# One eased move per shot, on the STORY clock (the clock every performance below is written on).
SHOTS = [   # t0, t1, name, kind, camera at start, camera at end, (move t0, move t1), why the camera is there
    (0.0, 5.0, "A wide", "town", Cam(360, 0, 1.0), Cam.look(338, 704, 1.42), (1.6, 4.7),
     "the whole street once, so that a town is what the dog lands in; then a slow push to where dog and class meet"),
    (5.0, 7.2, "B1 dig", "town", Cam.look(372, 768, 2.3), Cam.look(378, 768, 2.3), (5.2, 6.8),
     "the film's most repeated verb, large: the first try, which finds nothing"),
    (7.2, 8.75, "B2 boot", "town", Cam.look(388, 780, 2.9), Cam.look(392, 778, 2.9), (7.3, 8.5),
     "a new angle for a new try: close on the head, the hole and what comes out of it"),
    (8.75, 11.0, "B3 spool", "town", Cam.look(428, 764, 2.3), Cam.look(434, 757, 2.3), (9.4, 10.4),
     "the third try from further round, so the board the dog will look up at is already behind it"),
    (11.0, 17.0, "C board", "town", Cam.look(432, 756, 2.25), Cam.look(412, 722, 4.0), (13.7, 14.7),
     "the look: push through the near weed until only nose and page are left"),
    (17.0, 22.5, "D bubble", "town", Cam.look(505, 748, 2.15), Cam.look(512, 744, 2.3), (17.5, 22.0),
     "two-shot: dog left, child and its drawing right; the board behind the dog's shoulder"),
    (22.5, 25.5, "E page", "town", Cam.look(414, 734, 3.2), Cam.look(420, 752, 2.9), (24.4, 25.3),
     "close enough to see that the page is taken by one corner and stays flat"),
]

# THE EDIT. The film clock (0..30) is cut from the story clock and from the two LINE shots, which have clocks of
# their own. A repairer's cut (law 10): the critic found cow and dog stacked in one frame for three seconds and
# never dealing with each other, so the cow's beat is no longer one shot near the end. It is two close two-shots
# AT THE LINE, one before the dog goes down to the town and one when it comes back up with the page, and the
# time for them is taken out of the digs (cut to the attempts), the two holds and the walk between shots.
EDIT = [   # film t0, film t1, kind, story clock at t0
    (0.00, 0.40, "town", 0.00),      # the boundary frame; the dog hears her and looks up
    (0.40, 5.40, "line1", 0.0),      # WEAVE 1: the hoof that finds no bottom; the dog comes back; noses at the line
    (5.40, 8.70, "town", 1.50),      # A: down to the gravel, the class
    (8.70, 10.50, "town", 5.05),     # B1: nothing
    (10.50, 11.76, "town", 7.30),    # B2: the boot
    (11.76, 13.31, "town", 8.90),    # B3: the spool
    (13.31, 18.16, "town", 11.05),   # C: the board, the look, the hold
    (18.16, 18.64, "town", 16.50),   #    the head comes off the page
    (18.64, 22.84, "town", 17.10),   # D: the child and its drawing
    (22.84, 25.69, "town", 22.10),   #    the nod; E: the pin, the page
    (25.69, 29.30, "line2", 0.0),    # WEAVE 2: the dog shows her what it found
    (29.30, 30.00, "end", 0.0),      # F-TOWN: the boundary frame
]


def seg_at(t):
    for e in EDIT:
        if e[0] <= t < e[1]:
            return e
    return EDIT[-1]


def story(t):
    """Film time -> story clock (only meaningful in 'town' segments)."""
    e = seg_at(t)
    return e[3] + (t - e[0])


def when(tau):
    """Story clock -> film time. A moment that was cut out lands on the next thing that was kept."""
    best = None
    for t0, t1, kind, s0 in EDIT:
        if kind != "town":
            continue
        if s0 <= tau <= s0 + (t1 - t0):
            return t0 + (tau - s0)
        if s0 > tau and (best is None or s0 < best[1]):
            best = (t0, s0)
    return best[0] if best else SECONDS


# Focus and exposure. aperture 0 = everything sharp. blur(z) grows with distance from the focus plane.
# air: 0 = the lens is focused under the line, 1 = above it (only the split shot racks it).
# door: how much amber comes down from the lit door (the lure).
FOCUS = [   # t, focus z, aperture, air, door
    (0.0, 1.0, 0.0, 0.0, 1.0), (1.2, 1.0, 0.18, 0.0, 0.85), (5.0, 1.0, 0.18, 0.0, 0.60),
    (5.0, 1.0, 0.55, 0.0, 0.55), (11.0, 1.0, 0.55, 0.0, 0.55),
    (11.0, 1.0, 0.55, 0.0, 0.5), (13.7, 1.0, 0.55, 0.0, 0.5), (14.7, 1.0, 1.25, 0.0, 0.5), (17.0, 1.0, 1.25, 0.0, 0.5),
    (17.0, 1.0, 0.65, 0.0, 0.5), (22.5, 1.0, 0.65, 0.0, 0.5),
    (22.5, 1.0, 1.0, 0.0, 0.55), (25.5, 1.0, 0.9, 0.0, 0.6),
    (25.5, 1.0, 0.12, 0.0, 1.0), (26.0, 1.0, 0.0, 0.0, 1.0), (30.0, 1.0, 0.0, 0.0, 1.0),      # the last wide
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
    for k, (a, b, amt) in enumerate(((6.02, 6.6, 0.4), (7.42, 7.82, 0.45), (8.95, 9.45, 0.62))):
        hx, hy = town.hole_xy(k)
        n = int((b - a) / 0.1) + 1
        for q in range(n):
            out.append((a + q * 0.1, hx + 10 * math.sin(q * 2.3), hy - 4, amt, 10 + k * 20 + q))
    hx, hy = town.hole_xy(2)
    for q in range(6):                                   # the spool coming up through it, silt streaming off
        out.append((9.5 + q * 0.07, hx + 2 * q, hy - 6 - 5 * q, 0.22, 90 + q))
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
    "B1 dig": [(20, 600, 560, "near_a", 7, 6, 2), (1500, 610, 470, "near_b", 9, -8, 2)],
    "B2 boot": [(978, 620, 520, "near_b", 8, -7, 2)],
    "B3 spool": [(10, 610, 520, "near_a", 6, 7, 2)],
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

DIVE0 = (566.0, 512.0)                              # where the dive from her nose comes into the wide

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
    if t < 1.0:                                           # the boundary frame, and the half second after it
        u = 1 - (1 - t / 2.6) ** 1.7
        p0, c, p1 = (300.0, 530.0), (372.0, 610.0), (bx - 4, by - 26)
        x = (1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * c[0] + u * u * p1[0]
        y = (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * c[1] + u * u * p1[1]
        pose = dog.swim_down(t + 0.4, steep=0.72)
        hear = ease(t, 0.06, 0.34)                        # her bell, overhead: one ear, then the head comes up
        pose = dog.blend(pose, dog.look_up(dog.swim(t + 0.4, pitch=-0.2, effort=0.4), 0.8), hear)
        pose["ear"] = lerp(pose["ear"], 1.1, ease(t, 0.04, 0.2))
        pose["_anchor"] = "body"
        out.update(x=x - 10 * hear, y=y - 6 * hear, pose=pose, anchor="body")
        return out
    out["facing"] = -1                                    # it comes down from her, at the right, and lands facing the class
    if t < 2.6:
        u = smooth(clamp((t - 1.25) / 1.35)) ** 0.85
        p0, c, p1 = DIVE0, (500.0, 700.0), (bx + 4, by - 26)
        x = (1 - u) ** 2 * p0[0] + 2 * u * (1 - u) * c[0] + u * u * p1[0]
        y = (1 - u) ** 2 * p0[1] + 2 * u * (1 - u) * c[1] + u * u * p1[1]
        pose = dog.blend(dog.swim_down(t + 0.4, steep=0.9), dog.swim(t + 0.4, effort=0.7), ease(t, 2.0, 2.6))
        pose["_anchor"] = "body"
        out.update(x=x, y=y, pose=pose, anchor="body")
        return out
    if t < 3.0:
        u = ease(t, 2.6, 3.0)
        pose = dog.blend(dog.swim(t + 0.4, effort=0.5), _with(dog.stand(t), ear=0.2, ear_f=0.25, tail=0.6), u)
        pose["_anchor"] = "body"
        out.update(x=lerp(bx + 4, bx, u), y=lerp(by - 26, by, u * u), pose=pose, anchor="body")
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
        seen = ease(s, 0.5, 0.75) * (1 - ease(s, 1.4, 1.6))      # the class, in front of it: head up, ears at them
        pose["neck"] += 0.16 * seen
        pose["head"] += 0.10 * seen
        pose["ear"] += 0.4 * seen
        pose["ear_f"] += 0.42 * seen
        pose["wag"] = 0.3 * math.sin(s * 11) * seen
        w_ = ease(t, 4.5, 4.8)                           # nose goes down: it has smelled something
        pose = dog.blend(pose, _sniff_walk(0.0), w_)
        out.update(x=LAND[0], y=LAND[1], pose=pose)
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
    # ---- after E the story clock stops: WEAVE 2 and the last wide have their own states (dog_line2, dog_end)
    p = dog.carry_page(t, gait="stand")
    p["hold"] = 1.0
    out.update(x=X_BOARD, y=GY, pose=p, carry=page_sprite())
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


# ====================================================================== #
#  THE TWO WEAVES AT THE LINE                                            #
# ====================================================================== #
#
# One locked framing, used twice, so the second time rhymes with the first: the lead cow whole on the bank in
# the upper half, the line across the middle, and the dog under her nose in the lower half, both of them large.
# The porch above the line is porch.scene at F-SPLIT enlarged (it is behind her and out of focus, as far glass
# should be); she, the water, the dog and the fish are drawn sharp at the shot's own scale.

LZ = 1.75                                     # the shot's scale
LBX, LBY = 282.0, 268.0                       # world point at the frame's top-left corner
LINE_CAM = Cam(LBY + (H / 2) / LZ - H / 2, LBX + (W / 2) / LZ - W / 2, LZ)
COW_X = 600 - herd.reach("lead")
MUZZLE = (600.0, 402.0)                       # where her muzzle meets the line
NOSE1 = (596.0, 421.0)                        # where the dog's nose meets it from below
L1, L2 = 5.0, 3.61                            # lengths of the two shots

# WEAVE 1 (clock u): what she does, and when
W1 = dict(step=(0.25, 0.55), plunge=(0.55, 0.64), back=(0.66, 1.10), lower=(1.95, 2.55), touch=2.6, blow=3.45,
          dog_turn=4.2)
# WEAVE 2 (clock v)
W2 = dict(arrive=1.15, lower=(1.0, 1.45), blow=2.0, lift=(2.3, 3.0), dog_turn=2.42)


def L(wx, wy):
    """World -> screen in the LINE shot."""
    return ((wx - LBX) * LZ, (wy - LBY) * LZ)


@lru_cache(maxsize=4096)
def _rel_cached(key):
    pose = dict(key)
    im = Image.new("RGB", (8, 8))
    j = dog.draw_dog(im, pose, 0, 0, scale=1.0, facing=1, shadow=False, texture=False, ss=1, anchor="body")
    return {k: (j[k][0] * DS, j[k][1] * DS) for k in ("nose", "mouth")}


def _rel(pose, what="nose"):
    """Where the nose (or mouth) is from the middle of the body for a body-anchored pose, in world px, facing right."""
    key = tuple(sorted((k, round(v, 4) if isinstance(v, float) else v) for k, v in pose.items()))
    return _rel_cached(key)[what]


def _pin(out, pose, nose, facing):
    """Put the dog where its nose is at world point `nose`."""
    rx, ry = _rel(pose)
    pose["_anchor"] = "body"
    out.update(x=nose[0] - facing * rx, y=nose[1] - ry, pose=pose, facing=facing, anchor="body")
    return out


def _float_up(t, wag=0.0, reach=1.0):
    """Hanging under the line with the nose up to her: hardly paddling."""
    p = dog.wait_float(t, pitch=0.42)
    p["neck"], p["head"] = 0.95 * reach, 0.62 * reach
    p["ear"], p["ear_f"] = 1.05, 1.1
    p["tail"], p["wag"] = 0.5, wag
    return p


def _blown(p, a):
    """Her breath comes down as bubbles: the ears go back, the eyes shut, the head ducks. a 0..1."""
    q = dict(p)
    q["ear"], q["ear_f"] = lerp(p["ear"], 0.0, a), lerp(p["ear_f"], 0.05, a)
    q["eye"] = lerp(p.get("eye", 1.0), 0.05, a)
    q["neck"] = p["neck"] - 0.32 * a
    q["head"] = p["head"] - 0.25 * a
    return q


def dog_line1(u, t):
    """WEAVE 1. Hangs where it was, looking up at her; her leg comes through the line and it ducks; it turns round
    and swims back up to her; nose to her muzzle through the line, held; she blows and its ears go back; one more
    look; it turns and dives."""
    out = dict(carry=None, bits=None)
    n0, n1 = (424.0, 486.0), NOSE1
    hang = dog.look_up(dog.swim(t, pitch=0.12, effort=0.45), 0.85)
    hang["ear"], hang["ear_f"] = 1.1, 0.9
    st = dog.startle(u - W1["plunge"][0] - 0.02, floating=True)
    k = ease(u, W1["plunge"][0], W1["plunge"][0] + 0.08) * (1 - ease(u, 1.05, 1.35))
    pose = dog.blend(hang, st, k)
    go = ease(u, 1.15, 2.5)                                           # back up to her
    climb = dog.look_up(dog.swim(t * 1.5, pitch=0.5, effort=1.0), 0.35)
    climb["ear"], climb["ear_f"], climb["tail"] = 1.0, 1.05, 0.45
    pose = dog.blend(pose, climb, ease(u, 1.1, 1.45))
    held = ease(u, 2.2, 2.6)
    wag = 0.75 * math.sin(t * 15) * ease(u, 2.5, 2.8)
    pose = dog.blend(pose, _float_up(t, wag), held)
    nose = (lerp(n0[0], n1[0], go), lerp(n0[1], n1[1], go ** 0.8) + 9 * math.sin(math.pi * go))
    nose = (nose[0] - 5 * k, nose[1] + 9 * k)
    b = u - W1["blow"]
    if b > 0:
        a = ease(b, 0.0, 0.1) * (1 - ease(b, 0.45, 0.8))
        pose = _blown(pose, a)
        nose = (nose[0] - 7 * a, nose[1] + 13 * a)
    facing = 1.0
    d = u - W1["dog_turn"]
    if d > 0:                                                         # it turns away and goes down
        g = ease(d, 0.0, 0.8)
        before = dict(pose)
        dive = dog.swim_down(t * 1.4, steep=0.95)
        pose = dog.blend(pose, dive, ease(d, 0.0, 0.34))
        facing = lerp(1.0, -1.0, ease(d, 0.03, 0.27))
        if abs(facing) < 0.12:
            facing = 0.12 if facing >= 0 else -0.12
        rx, ry = _rel(before)                                         # from here the BODY is led, not the nose:
        bx, by = nose[0] - rx, nose[1] - ry                           # the nose swings under it as it tips over
        pose["_anchor"] = "body"
        out.update(x=lerp(bx, 548.0, g ** 1.3), y=lerp(by, 600.0, g ** 1.7), pose=pose, facing=facing, anchor="body")
        return out
    return _pin(out, pose, nose, facing)


def cow_line1(u, t):
    """WEAVE 1. She looks down where it went, puts a forefoot after it, finds no bottom, snatches it back; stands;
    lowers her nose to the dog's; breathes out into the water; watches it go."""
    ld = herd.with_(herd.look_down(t, 1.0, "lead"), ear=30.0)
    step, plunge, back = ease(u, *W1["step"]), ease(u, *W1["plunge"]), ease(u, *W1["back"])
    pose = dict(ld)
    fx = lerp(60, 97, step) + 3 * plunge
    fy = 6 * step + 12 * plunge
    fx = lerp(fx, 50, back)
    fy = lerp(fy, 0, back) - 24 * bump((u - W1["back"][0]) / 0.44)
    pose["nf"] = ("ik", fx, fy)
    tilt = 4 * step + 7 * plunge - 15 * ease(u, 0.66, 0.9) + 4 * ease(u, 0.9, 1.4) + 7 * ease(u, 1.4, 2.4)
    x = COW_X + 4 * step - 15 * back + 11 * ease(u, 1.7, 2.3)
    alert = herd.with_(herd.stand(t, "lead", chew=0, alert=1), eye=1.7)
    up = ease(u, 0.64, 0.82)
    down = ease(u, *W1["lower"])
    if up > 0:
        pose = herd.tween(pose, herd.with_(alert, nf=pose["nf"]), up, "out", "lead")
    if down > 0:
        low = herd.with_(herd.drink(0.0, 1.0, "lead"), ear=32.0, eye=1.2, jaw=0.5)
        pose = herd.tween(pose, low, down, "slow", "lead")
    pose = dict(pose)
    if u > W1["touch"]:                                               # the nostrils working; then the breath out
        pose["head"] = pose.get("head", 0.0) + 1.3 * math.sin(2 * math.pi * 3.0 * u) * (1 - ease(u, W1["blow"], W1["blow"] + 0.2))
        pose["jaw"] = pose.get("jaw", 0.0) + 6.0 * bump((u - W1["blow"]) / 0.5)
        e = pose.get("ear", 0.0)
        if isinstance(e, (int, float)):
            pose["ear"] = e - 22 * bump((u - W1["blow"] - 0.05) / 0.4)
    follow = ease(u, W1["dog_turn"] + 0.1, W1["dog_turn"] + 0.7)     # her nose goes after it along the line
    nose_to = (598.0, 376.0) if u < 0.72 else (MUZZLE[0] - 26 * follow, MUZZLE[1] - 1)
    pose["_nose"] = clamp((1 - up) + down)
    leg = 18 * ease(u, 0.38, 0.55) + 38 * plunge
    leg *= 1 - ease(u, 0.68, 0.92)
    dip = down * (1 - 0.25 * follow)
    return dict(pose=pose, x=x, tilt=tilt, nose_to=nose_to, leg=leg, dip=dip)


@lru_cache(maxsize=2)
def page_shown():
    """The page turned full to us (and to her) while the dog holds it up."""
    return props.page_sprite("jaw", flat=0.0, tint=props.TEAL, tint_amount=0.10)


def dog_line2(v, t):
    """WEAVE 2. Up from the town with the page; holds it up under her nose; her breath comes down and its ears go
    back; she lifts her head, and it turns for the door."""
    out = dict(bits=None)
    n0, n1 = (470.0, 536.0), (NOSE1[0] - 6, NOSE1[1] + 3)
    go = ease(v, 0.0, W2["arrive"] + 0.1)
    climb = dog.carry_page(t * 1.4, gait="swim_up", steep=0.62)
    climb["ear"], climb["ear_f"] = 0.9, 0.95
    held = ease(v, W2["arrive"] - 0.3, W2["arrive"] + 0.15)
    wag = 0.8 * math.sin(t * 16) * ease(v, W2["arrive"], W2["arrive"] + 0.3)
    show = dog.holding(_float_up(t, wag, reach=0.92), "page")
    pose = dog.blend(climb, show, held)
    nose = (lerp(n0[0], n1[0], go), lerp(n0[1], n1[1], go ** 0.85) + 8 * math.sin(math.pi * go))
    b = v - W2["blow"]
    if b > 0:
        a = ease(b, 0.0, 0.1) * (1 - ease(b, 0.3, 0.55))
        pose = _blown(pose, a)
        nose = (nose[0] - 5 * a, nose[1] + 10 * a)
    facing = 1.0
    d = v - W2["dog_turn"]
    if d > 0:                                                         # round, down and away to the left: the door
        g = clamp(d / (L2 - W2["dog_turn"]))
        rx, ry = _rel(pose)                                           # from here the BODY is led, not the nose
        bx, by = nose[0] - rx, nose[1] - ry
        away = dog.carry_page(t * 1.3, gait="swim", pitch=lerp(-0.5, -0.05, smooth(g)), effort=1.0)
        pose = dog.blend(pose, away, ease(d, 0.0, 0.3))
        facing = lerp(1.0, -1.0, ease(d, 0.03, 0.27))
        if abs(facing) < 0.12:
            facing = 0.12 if facing >= 0 else -0.12
        e0 = dog_end(EDIT[-1][0])                                     # where the last wide picks it up
        gg = smooth(g)
        pose["hold"], pose["_anchor"] = 1.0, "body"
        out["carry"] = page_shown() if d < 0.12 else page_sprite()
        out.update(x=lerp(bx, e0["x"], gg), y=lerp(by, e0["y"], gg) + 14 * math.sin(math.pi * gg), pose=pose,
                   facing=facing, anchor="body")
        return out
    pose["hold"] = 1.0
    out["carry"] = page_shown() if v < W2["dog_turn"] + 0.12 else page_sprite()
    return _pin(out, pose, nose, facing)


END_AT = (430.0, 550.0)                          # the boundary frame: the dog's body, heading up-left


def dog_end(t):
    """The last wide (film clock): up and left with the page, toward the amber."""
    t0 = EDIT[-1][0]
    g = clamp((t - t0) / (SECONDS - t0))
    p = dog.carry_page(t, gait="swim_up", steep=lerp(0.2, 0.78, smooth(g)))
    p["hold"] = 1.0
    x = lerp(END_AT[0] + 46, END_AT[0], g)
    y = lerp(END_AT[1] + 13, END_AT[1], g ** 1.4)
    return dict(x=x, y=y, pose=p, facing=-1, carry=page_sprite(), anchor="body", bits=None)


def cow_line2(v, t):
    """WEAVE 2. She has stood here the whole time, looking down. The dog comes up under her nose with something:
    her ears come round, she lowers her muzzle to it, breathes on it; then she lifts her head, chews again (it is
    all right), her tail goes once, and her nose follows the dog along the line toward the door."""
    wait = herd.with_(herd.look_down(t, 1.0, "lead"), ear=14.0 + 16.0 * ease(v, 0.35, 0.6))
    low = herd.with_(herd.drink(0.0, 1.0, "lead"), ear=32.0, eye=1.25, jaw=0.5)
    down = ease(v, *W2["lower"])
    pose = herd.tween(wait, low, down, "slow", "lead")
    lift = ease(v, *W2["lift"])
    if lift > 0:
        easy = herd.look_down(t, 0.38, "lead")                        # head half up, and chewing again
        sw = bump((v - W2["lift"][0] - 0.1) / 0.7)
        easy = herd.with_(easy, ear=24.0, tail=(3.0 + 30 * sw * math.sin(9 * t), 6.0 + 34 * sw * math.sin(9 * t - 0.9),
                                               8.0 + 38 * sw * math.sin(9 * t - 1.8)))
        pose = herd.tween(pose, easy, lift, "inout", "lead")
    pose = dict(pose)
    if W2["lower"][1] < v:
        pose["head"] = pose.get("head", 0.0) + 1.3 * math.sin(2 * math.pi * 3.0 * v) * (1 - ease(v, W2["blow"], W2["blow"] + 0.2)) * (1 - lift)
        pose["jaw"] = pose.get("jaw", 0.0) + 6.0 * bump((v - W2["blow"]) / 0.5)
        e = pose.get("ear", 0.0)
        if isinstance(e, (int, float)):
            pose["ear"] = e - 22 * bump((v - W2["blow"] - 0.05) / 0.4)
    follow = ease(v, W2["dog_turn"] + 0.1, L2)
    nose_to = (lerp(600.0, MUZZLE[0], down) - 62 * follow, lerp(383.0, MUZZLE[1] - 1, down * (1 - lift)) - 4 * lift)
    pose["_nose"] = 1.0
    x = COW_X + 11 - 6 * lift
    return dict(pose=pose, x=x, tilt=7 * down * (1 - lift) + 3 * lift, nose_to=nose_to, leg=0.0, dip=down * (1 - lift))


def waver_line2(v, t):
    """The yellow-satchel child is already under her nose, waving at it; when the dog comes up it darts aside and
    watches; when the dog has gone it drifts back."""
    aside = ease(v, 0.55, 0.95) * (1 - 0.6 * ease(v, 2.9, L2))
    x = lerp(604.0, 668.0, aside)
    y = lerp(452.0, 476.0, aside) + 2.5 * math.sin(t * 2.4)
    wav = (1 - ease(v, 0.5, 0.7))
    arm = 126 + 34 * math.sin(t * 10) * wav - 90 * (1 - wav)
    tilt = 9 * math.sin(t * 10 + 0.6) * wav + 34 * bump((v - 0.55) / 0.5)
    return dict(x=x, y=y, tilt=tilt, arm=arm, facing=1 if v < 0.75 else -1)


def waver_end(t):
    g = clamp((t - EDIT[-1][0]) / (SECONDS - EDIT[-1][0]))
    a = waver_line2(L2, t)
    return dict(x=lerp(a["x"], 600.0, smooth(g)), y=lerp(a["y"], 474.0, smooth(g)), tilt=0.0, arm=30.0, facing=1)


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
    """The bubble trail the dog leaves coming down: at the boundary frame from the line at x = 590 (S1's last frame
    carries it); after WEAVE 1 from her muzzle, where it turned and dived."""
    if t > 3.6:
        return
    z = cam.zoom
    ys = cam.surface()
    old = t < 1.0
    for q in range(16):
        u = (q + 0.5) / 16
        ta = -2.2 * (1 - u) if old else 1.3 - 1.1 * (1 - u)        # when the dog was there
        if old:
            wx = lerp(590, 300, u ** 1.15) + 5 * math.sin(q * 2.1 + t * 3)
            wy = lerp(404, 530, u ** 1.3) - 34 * (t - ta) * 0.5
        else:
            wx = lerp(594, DIVE0[0], u) + 5 * math.sin(q * 2.1 + t * 3)
            wy = lerp(424, DIVE0[1] + 40, u) - 34 * (t - ta) * 0.5
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


def _town_frame(ink, t, shot, cam, ta=None, st=None, ws=None):
    """A frame under water. t is the STORY clock; ta the film clock (what the water, the weed and the townsfolk
    drift on, so that a cut in the story is not a jump in the water); st, ws: the dog and the waver, when the
    story clock has stopped (the last wide)."""
    name = shot[2]
    ta = t if ta is None else ta
    if st is None:
        st = dog_state(t)
        dogw = dog_head_world(t)
    else:
        dogw = (st["x"] - 40, st["y"])
    door = _key(FOCUS, t, 4)
    states = atmos(t)
    still = "suspend" in states
    # --- far glass
    bell = 0.0
    if 1.5 < t < 3.6:
        bell = 24 * math.sin(7.2 * (t - 1.5)) * math.exp(-(t - 1.5) * 1.1)
    town.back(ink, ta, cam, door=door)
    if cam.surface() > -30:
        town.touch(ink, ta, cam, 600, "muzzle", dip=muzzle_dip(t))
    _blur_rows(ink, cam.surface() + 8 * cam.zoom, H, blur_px(0.55, t))
    # --- the street glass
    pull, taken = None, ()
    if t >= 24.5:
        taken = (0,)
    elif t >= 23.0:
        pull = (0, 0.5 * ease(t, 23.0, 23.3) + 0.5 * ease(t, 23.55, 24.5))
    wide = name in ("A wide", "G up")
    town.street(ink, ta, cam, bell=bell, holes=holes_at(t), smudges=1 if (wide and t > 15) else 0, pull=pull, taken=taken)
    if 15.0 <= t < 24.5 and not wide:
        _smudge(ink, cam, 1.0)
    if t >= 8.5:
        town.thing(ink, cam, "boot", BOOT_AT[0], BOOT_AT[1], 8)
    if t >= 11.7 + 0.62:
        town.thing(ink, cam, "spool", *SPOOL_AT)
    pin = _pin_xy(t)
    if pin:
        town.thing(ink, cam, "pin", pin[0], pin[1], pin[2])
    draw_silt(ink, t, cam, front=False)
    # --- the cast
    town.townsfolk(ink, ta, cam, look=dogw)
    if t < 17.0:
        _class_walking(ink, t, cam, dogw)
    elif t < 22.5:
        _class_walking(ink, t, cam, dogw)
    elif t < 25.5:
        pass
    else:
        town.school_class(ink, ta, cam, look=dogw, tilt=-8, skip=(WAVER,), arm={0: 124 + 30 * math.sin(ta * 9)})
    if 16.9 <= t < 25.5:
        ks = kid0_state(t)
        grow, prog, rise, pop = bubble_state(t)
        r = town.child(ink, t, cam, 0, ks["x"], ks["y"], facing=-1 if t > 17.3 else -1, tilt=ks["tilt"], arm=ks["arm"],
                       look=(dogw if t < 23 else NOSE_AT), swim=0.25 if t > 17.6 else 1.0, mouth_open=1.0 if 17.6 < t < 19.0 else 0.0)
        if grow > 0 and pop < 1:
            town.bubble(ink, t, cam, r["mouth"], "jaw", grow=grow, progress=prog, r=BUBBLE_R, side=1, pop=pop, rise=rise,
                        screen=True, calm=still)
    if ws is not None:
        town.child(ink, ta, cam, WAVER, ws["x"], ws["y"], facing=ws["facing"], tilt=ws["tilt"], arm=ws["arm"], look=(604, 396), swim=0.6)
    j = draw_dog(ink, t, cam, st)
    if 22.95 <= t < 23.32:                                       # the pin in its front teeth
        px, py = j["mouth"]
        z = cam.zoom
        ink.d.line([(px, py), (px - 5 * z, py - 3 * z)], fill=(190, 196, 190, 255), width=max(1, int(1.2 * z)))
        ink.d.ellipse([px - 7.2 * z, py - 5.2 * z, px - 2.8 * z, py - 0.8 * z], fill=(206, 60, 54, 255), outline=(14, 30, 34, 255))
    _trail(ink, t, cam)
    # --- near glass
    draw_silt(ink, t, cam, front=True)
    town.front(ink, ta, cam, calm=still)
    draw_dress(ink, ta, shot, cam)
    return j


def _line_frame(ink, t, which, c):
    """One of the two WEAVES at the line. t = film clock, c = the shot's own clock (u or v)."""
    cam = LINE_CAM
    oy = 250
    first = which == "line1"
    cs = cow_line1(c, t) if first else cow_line2(c, t)
    st = dog_line1(c, t) if first else dog_line2(c, t)
    ys = cam.surface()
    hoof_x = 590.0

    # --- far glass: the porch, the hill, the cow who waits in the gate. Drawn at F-SPLIT and enlarged.
    far = kit.Ink(ink.t, ink.i, (W, H), boil=8, wobble=1.2, seed=2)

    def hill(k, t_, oy_):
        for q, who in enumerate(("second", "mother", "calf", "fourth", "fifth", "sixth")):
            pl = herd.PATH.at(herd.hill_spot(q))
            if pl["layer"] == "hill":
                herd.cow(k, who, herd.stand(t_, who), pl["x"], pl["y"], pl["s"] * herd.S if pl["s"] < 2 else pl["s"],
                         pl["facing"], oy_, far=0.15 * q)

    def strip(k, t_, oy_):
        pl = herd.PATH.at(herd.hill_spot(0))
        if pl["layer"] != "hill":
            herd.cow(k, "second", herd.stand(t_, "second"), pl["x"], pl["y"], pl["s"] * herd.S if pl["s"] < 2 else pl["s"],
                     pl["facing"], oy_)

    def front(k, t_, oy_):
        if first:
            porch.splash(k, t_, oy_, hoof_x, c - W1["plunge"][0] - 0.02, 1.25, "in")

    rings = [porch.ring(hoof_x, t - (c - W1["plunge"][0] - 0.02), 1.6)] if first else []
    porch.scene(far, t, oy, cast=dict(hill=hill, strip=strip, front=front),
                q=porch.pose("sit", p=0.5 + 0.5 * math.sin(t * 2.2)), door=0.25, radio_on=1.0, pebbles="w", rings=rings)
    box = (LBX, LBY - oy, LBX + W / LZ, LBY - oy + H / LZ)
    big = far.img.convert("RGB").resize((W, H), Image.BICUBIC, box=box).filter(ImageFilter.GaussianBlur(1.1))
    ink.img.paste(big, (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")

    # --- the water, sharp, at the shot's own scale
    town.back(ink, t, cam, sky=False, door=0.85)

    # --- her, sharp: hooves on the path strip, the muzzle down to the line; nothing of her under it but the
    #     muzzle (town.touch) and, once, a foreleg to the knee
    lay = _Shim((W, H))
    cx, cy = L(cs["x"], 388.0)
    anchors = herd.cow(lay, "lead", cs["pose"], cx, cy, s=herd.S * LZ, facing=1, oy=0, nose_to=L(*cs["nose_to"]),
                       tilt=cs["tilt"], rim=herd.rim_at(cs["x"]))
    a = np.asarray(lay.img).copy()
    cut = int(ys + 2)
    a[cut:, :, 3] = 0
    cowl = Image.fromarray(a, "RGBA")
    if cs["dip"] > 0.3:
        town.touch(ink, t, cam, MUZZLE[0] + (cs["nose_to"][0] - MUZZLE[0]), "muzzle", dip=clamp((cs["dip"] - 0.3) / 0.6))
    ink.img.paste(cowl, (0, 0), cowl)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    wx_hoof = anchors["hooves"]["nf"][0] / LZ + LBX
    if cs["leg"] > 1:
        draw_leg_below(ink, t, cam, wx_hoof, cs["leg"])

    # --- under the line
    if not first:
        ws = waver_line2(c, t)
        look = (604, 396) if c < 0.6 else (st["x"], st["y"])
        town.child(ink, t, cam, WAVER, ws["x"], ws["y"], facing=ws["facing"], tilt=ws["tilt"], arm=ws["arm"], look=look, swim=0.6)
    j = draw_dog(ink, t, cam, st)
    blow = W1["blow"] if first else W2["blow"]
    draw_blown(ink, c, cam, blow, wx=cs["nose_to"][0])
    town.front(ink, t, cam, weeds=False)
    return dict(dog=j, cow=anchors)


def draw(t, ink):
    """One full 960x540 frame of S2 at film-local time t (0..30)."""
    t = clamp(t, 0.0, SECONDS)
    e = seg_at(min(t, SECONDS - 1e-6))
    if e[2] in ("line1", "line2"):
        _line_frame(ink, t, e[2], t - e[0])
    elif e[2] == "end":
        _town_frame(ink, 26.0, SHOTS[0], Cam(360, 0, 1.0), ta=t, st=dog_end(t), ws=waver_end(t))
    else:
        tau = story(t)
        _town_frame(ink, tau, shot_at(tau), cam_at(tau), ta=t)
    v = 0.22 * ease(t, 0.0, 0.4) * (1 - ease(t, 29.3, 29.9))        # none at the two ends: the neighbours have none
    if v > 0.01:
        ink.vignette(round(v, 2))


# ====================================================================== #
#  SOUND (depth audio)                                                   #
# ====================================================================== #

def heard(t, wx, wy, z=1.0, line=False):
    """Depth audio: where a source at world (wx, wy) on plane z is for the ear, which is where the camera is.
    t is the STORY clock (line=True: one of the two shots at the line, whose camera is locked).
    Returns (gain factor, pan, under): pan from its screen x, level from the shot's scale and its distance from
    the middle of frame, `under` = how it is filtered (True: through the whole depth of water; a number: a
    cut-off in Hz for something close to the lens under water; False: in air)."""
    cam = LINE_CAM if line else cam_at(t)
    sx, sy = cam.xy(wx, wy, z)
    pan = clamp((sx - W / 2) / (W / 2), -1, 1) * 0.75
    near = clamp(cam.zoom / 2.3, 0.45, 1.5) ** 0.5
    off = math.hypot((sx - W / 2) / W, (sy - H / 2) / H)
    gain = near * clamp(1.15 - 0.6 * off, 0.4, 1.15)
    above = wy < town.SURFACE_Y
    if line:
        under = False if above else True
        gain *= 0.85
    else:
        under = True if above else (1500 if cam.zoom > 1.8 else True)
    return gain, pan, under


def sound(mix, at=0.0):
    """Lay S2's sound into `mix` with film-local 0 at `at` seconds. Events are written on the story clock and
    placed through when(); the two shots at the line are on the film clock. Nobody has heard this."""
    def A(t):                       # film-local
        return at + t

    def S_(tau):                    # story clock
        return at + when(tau)

    a1, b1 = EDIT[1][0], EDIT[1][1]
    a2, b2 = EDIT[-2][0], EDIT[-2][1]
    # the rooms: below; both at half in the two shots at the line; below again
    snd.hush(mix, A(-0.1), a1 + 0.2, 1.0, 0.2, 0.2)
    snd.hush(mix, A(a1 - 0.1), b1 - a1 + 0.2, 0.5, 0.2, 0.2)
    snd.above(mix, A(a1 - 0.1), b1 - a1 + 0.2, 0.5, 0.2, 0.2)
    snd.hush(mix, A(b1 - 0.1), a2 - b1 + 0.2, 1.0, 0.2, 0.2)
    snd.hush(mix, A(a2 - 0.1), b2 - a2 + 0.2, 0.5, 0.2, 0.2)
    snd.above(mix, A(a2 - 0.1), b2 - a2 + 0.2, 0.5, 0.2, 0.2)
    snd.hush(mix, A(b2 - 0.1), SECONDS - b2 + 0.1, 1.0, 0.2, 0.2)
    # WEAVE 1: the hoof that finds no bottom; the breath
    g, p, u = heard(0, 590, 396, line=True)
    snd.cowbell(mix, A(0.12), 1, gain=0.05, pan=p, under=True)             # what the dog hears, and looks up at
    tp = a1 + W1["plunge"][0] + 0.02
    snd.plunge(mix, A(tp), 1.6, gain=0.3, pan=p)
    snd.cowbell(mix, A(tp + 0.05), 3, 0.2, gain=0.07, pan=p, hard=True)
    snd.hooves(mix, A(tp + 0.25), 3, 0.2, "wood", gain=0.09, pan=p)
    snd.moo(mix, A(tp + 0.6), 0.7, pan=p)
    snd.sniff(mix, A(a1 + W1["touch"] + 0.1), 2, gain=0.05, pan=p)
    snd.bubbles(mix, A(a1 + W1["blow"]), 6, 0.8, low=True, gain=0.07, pan=p)
    snd.bubbles(mix, A(a1 + W1["dog_turn"] + 0.2), 4, 0.6, gain=0.03, pan=p)
    # the school bell twice, as the dog comes down to the town (sound.music_s2 has it at +0.5, which is now WEAVE 1)
    snd.school_bell(mix, S_(1.55))
    snd.school_bell(mix, S_(2.45), gain=0.07)
    # the class
    g, p, u = heard(1.6, 60, 780)
    snd.fish_murmur(mix, S_(1.6), 1.4, gain=0.03 * g, pan=p)
    g, p, u = heard(3.0, *LAND)
    snd.land(mix, S_(3.0), pan=p)
    snd.nose_bump(mix, S_(4.0), pan=heard(4.0, 60, 800)[1])    # the last child into the one in front
    snd.sniff(mix, S_(5.1), 3, gain=0.05, pan=heard(5.1, 400, 810)[1], under=1500)
    # three digs: nothing; the boot; the spool
    for k, (d0, a, b, _) in enumerate(DIG):
        g, p, u = heard(a, *HOLE[k])
        t_a = when(a)
        snd.dig(mix, A(t_a), max(0.25, when(b) - t_a), find=(None, "thud", "ring")[k], gain=0.14 * g, pan=p, under=u)
    g, p, u = heard(8.5, *BOOT_AT)
    snd.set_down(mix, S_(8.5), pan=p)
    snd.bubbles(mix, S_(9.7), 4, 0.6, gain=0.04, pan=heard(9.7, *HOLE[2])[1])
    # the board
    g, p, u = heard(12.32, *SPOOL_AT)
    snd.set_down(mix, S_(12.32), pan=p)
    snd.sniff(mix, S_(14.1), 2, gain=0.05 * heard(14.1, *NOSE_AT)[0], pan=heard(14.1, *NOSE_AT)[1], under=1500)
    snd.sniff(mix, S_(14.6), 2, gain=0.04, pan=heard(14.6, *NOSE_AT)[1], under=1500)
    snd.duck(mix, S_(15.0), S_(15.9), 0.6)                     # the hold: the room itself drops
    # the drawing
    g, p, u = heard(17.6, *KID0_AT)
    snd.bubble_picture(mix, S_(17.6), 1.5, pan=p)
    snd.fish_murmur(mix, S_(19.75), 0.8, gain=0.02, pan=p)
    # the page
    g, p, u = heard(23.0, *PIN_AT)
    snd.page_taken(mix, S_(23.0), pan=p)
    snd.bubbles(mix, S_(24.62), 3, 0.3, gain=0.05, pan=heard(24.62, KID0_AT[0], 700)[1])
    # WEAVE 2: she smells what it has brought; the breath; the bell as her head comes up
    g, p, u = heard(0, 600, 396, line=True)
    snd.sniff(mix, A(a2 + W2["lower"][1] + 0.1), 2, gain=0.05, pan=p)
    snd.bubbles(mix, A(a2 + W2["blow"]), 6, 0.8, low=True, gain=0.07, pan=p)
    snd.cowbell(mix, A(a2 + W2["lift"][0] + 0.25), 1, gain=0.05, pan=p)
    # up: one lamp answers the motif
    for j, on in enumerate(snd.MOTIF):
        snd.lamp_chime(mix, A(a2 + W2["dog_turn"] + 0.3 + on * 1.3), (0, 0, 2, 1)[j], gain=0.022, pan=-0.3 + 0.2 * j, seconds=1.1)
    snd.bubbles(mix, A(b2 + 0.05), 4, 0.6, gain=0.03, pan=heard(0, 440, 560)[1])
    return mix


# ====================================================================== #
#  CHECKS                                                                #
# ====================================================================== #

def _pose_diff(a, b):
    return max(abs(a[k] - b[k]) for k in a if isinstance(a[k], (int, float)) and k in b)


def check():
    out = []
    # 0 · the edit: the film clock is covered once, in order, and comes to exactly 30 s
    assert EDIT[0][0] == 0.0 and abs(EDIT[-1][1] - SECONDS) < 1e-9
    assert all(abs(a[1] - b[0]) < 1e-9 for a, b in zip(EDIT, EDIT[1:]))
    taus = [(e[3], e[3] + e[1] - e[0]) for e in EDIT if e[2] == "town"]
    assert all(b[0] >= a[1] - 1e-9 for a, b in zip(taus, taus[1:]))
    assert abs((EDIT[1][1] - EDIT[1][0]) - L1) < 1e-9 and abs((EDIT[-2][1] - EDIT[-2][0]) - L2) < 1e-9
    kept = sum(b - a for a, b in taus)
    out.append(f"MEASURED edit: {kept:.2f} s of the story clock kept in {len(taus)} pieces; the two shots at the line "
               f"{L1:.2f} s and {L2:.2f} s; last wide {EDIT[-1][1] - EDIT[-1][0]:.2f} s")
    # 1 · parallax respects depth: in every shot whose camera moves, a nearer plane moves at least as far on screen
    for s in SHOTS:
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
                   + " <= ".join(f"{m:.2f}" for m in mags))
    # 2 · the planes are stacked in z order and focus blur grows away from the focus plane
    zs = [z for _, z, _ in PLANES]
    assert zs == sorted(zs)
    assert blur_px(0.45, 15.5) > blur_px(0.72, 15.5) > blur_px(1.0, 15.5) == 0 < blur_px(1.8, 15.5) < blur_px(2.3, 15.5)
    out.append(f"MEASURED defocus at the hold (story 15.5): far {blur_px(0.45, 15.5):.1f} px, back row {blur_px(0.72, 15.5):.1f}, "
               f"street 0, near glass {blur_px(1.8, 15.5):.1f} and {blur_px(2.3, 15.5):.1f}")
    # 3 · the fog is a field, not an overlay: it is uneven, and the two halves differ; and it no longer buries the dog
    cam = cam_at(9.4)
    fb, ff = silt_field(9.4, cam, False), silt_field(9.4, cam, True)
    assert fb is not None and ff is not None
    for f in (fb, ff):
        on = f[f > 0.02]
        assert on.size > 200 and on.std() / on.mean() > 0.35 and (f > 0.02).mean() < 0.6
    assert np.abs(fb - ff).max() > 0.1
    assert silt_field(16.0, cam_at(16.0), True) is None or silt_field(16.0, cam_at(16.0), True).max() < 0.02
    out.append(f"MEASURED silt at story 9.4: covers {100 * (ff > 0.02).mean():.0f}% of frame (front), peak {ff.max():.2f}, "
               f"unevenness (sd/mean) {ff[ff > 0.02].std() / ff[ff > 0.02].mean():.2f}; gone by 16")
    # 4 · holes never fill in; three at the end
    hs = [holes_at(story(k / 24)) if seg_at(k / 24)[2] == "town" else None for k in range(int(SECONDS * 24))]
    hs = [h for h in hs if h is not None]
    assert all(b >= a for a, b in zip(hs, hs[1:])) and hs[-1] == 3.0 and hs[0] == 0.0
    out.append("MEASURED holes: 0 at the first frame, never fewer than before, 3 at the end")
    # 5 · the holds: nothing of the dog moves
    for a, b, what in ((15.0, 15.9, "nose on the page"), (21.0, 21.3, "on the wobble")):
        sa = dog_state(a + 0.02)
        for q in range(1, 12):
            sb = dog_state(lerp(a + 0.02, b - 0.02, q / 11))
            assert _pose_diff(sa["pose"], sb["pose"]) < 1e-9 and sa["x"] == sb["x"], what
        out.append(f"MEASURED hold {what}: dog pose identical over {b - a:.2f} s (film {when(a):.2f} to {when(b):.2f})")
    # 6 · boundary frames
    c0 = cam_at(0.0)
    s0 = dog_state(0.0)
    assert (c0.oy, c0.ox, c0.zoom) == (360, 0, 1) and c0.xy(s0["x"], s0["y"]) == (300.0, 170.0)
    assert seg_at(SECONDS)[2] == "end"
    s1 = dog_end(SECONDS)
    assert Cam(360, 0, 1.0).xy(s1["x"], s1["y"]) == (430.0, 190.0) and s1["facing"] == -1 and s1["carry"] is not None
    out.append("MEASURED boundaries: F-TOWN at both ends; dog body at screen (300, 170) at 28.0 and (430, 190) at 58.0, heading up-left with the page")
    # 7 · no cow below the line except a muzzle and, once, a foreleg to the knee
    assert max(cow_line1(k / 24, k / 24)["leg"] for k in range(int(L1 * 24))) <= 58
    assert all(cow_line2(k / 24, k / 24)["leg"] == 0 for k in range(int(L2 * 24)))
    out.append("STRUCTURAL no cow below the line: _line_frame cuts her sprite off at the line; under it only town.touch's muzzle "
               "and one foreleg (WEAVE 1), at most 56 px deep")
    # 8 · every time the dog goes into the gravel we see what it has: nothing (it looks in), a boot, a spool
    assert dog_state(8.2)["carry"] is not None and dog_state(9.9)["carry"] is not None
    assert all(dog_line2(v, 26 + v)["carry"] is not None for v in (0.0, 1.5, 3.0, L2))
    out.append("MEASURED carried: boot at story 8.2, spool at 9.9, the page from 24.5 to the last frame")
    # 9 · THE WEAVE: in both shots at the line the dog's nose is at her muzzle, and both are big
    for name, fn_d, fn_c, a, b in (("WEAVE 1", dog_line1, cow_line1, W1["touch"], W1["blow"]),
                                   ("WEAVE 2", dog_line2, cow_line2, W2["arrive"] + 0.2, W2["blow"])):
        gaps = []
        for q in range(6):
            c = lerp(a, b, q / 5)
            st = fn_d(c, 10 + c)
            rx, ry = _rel(st["pose"])
            nose = (st["x"] + st["facing"] * rx, st["y"] + ry)
            gaps.append(math.hypot(nose[0] - MUZZLE[0], nose[1] - (MUZZLE[1] + 16)))
        assert max(gaps) < 14, (name, gaps)
        out.append(f"MEASURED {name}: dog's nose within {max(gaps):.0f} world px of the underside of her muzzle for {b - a:.2f} s; "
                   f"dog drawn at {DS * LZ:.2f} px per unit, cow at {LZ:.2f} x her strip size "
                   f"(withers {104 * LZ:.0f} px above her hooves)")
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
