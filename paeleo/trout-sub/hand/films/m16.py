"""m16 · the MAKING film for porthole 16 · Aft · "Identical twin Turkey Sub waving back".

Not what the children wrote (that is c16) but the writing of it: one Porthole Log passing through three children
(see swarm/m16/board.md for the 33 traces of working that are really on the sheet, and where each is shown).

   0.0 .. 29.0   the pilot (ochre): page 1                          swarm/m16/scene_pilot.py
  29.0 .. 30.0   THE PASS, left: the sheet slides off the pilot's desk; whip; it lands askew in front of B.
  30.0 .. 54.0   the first friend, B. (plum, green pencil): Turkey's seat      swarm/m16/scene_turkey.py
  54.0 .. 55.0   THE PASS, left again: whip; the sheet arrives sideways on W.'s desk and is turned upright
                 while the eye is already going in to the name line
  55.0 .. 78.0   the next friend, W. (teal): the trout's seat       swarm/m16/scene_trout.py
  78.0 .. 90.0   the ending (this file): the eye stands up out of W.'s seat; the whole of page 2, four endings'
                 worth of clean lines; three pairs of hands at three edges of the desk; the cup with the die in
                 it; cam.rise to the whole room; nothing is thrown.

Sound is synthesized with the kit's Mix: a pencil scratch per letter (one unbroken scratch for the pilot's third
line, slow single ticks for W.'s separate letters), the rubber and the brush of crumbs, paper at each flip and
each pass, a chair, a room of children far off under every desk shot, water (dull inside the tin and the thought,
open in the river) and a low drone only away from the desk, and next to nothing while a child is stuck.

Nothing is foraged (credits/m16.json is empty, as c16's is): c16's cut-paper world, people.py and cam.py.

  python3 films/m16.py                      -> assets/films/m16.mp4 (+ .webp poster)
  python3 films/m16.py --stills 3 7.8 ...   -> films/stills/m16/*.png and sheet.png
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "swarm" / "c16"))

from kit import Film, Mix  # noqa: E402
import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c16 world; not edited)

M16 = HERE / "swarm" / "m16"


def _load(name, path):
    """The m16 scene modules share file names with c16's, so they are loaded by path, not by import."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SR = _load("m16_scene_trout", M16 / "scene_trout.py")
ST = SR._turkey_unit()                        # the same instance the trout scene takes B.'s column from
assert ST, "scene_turkey.py did not load"
SP = _load("m16_scene_pilot", M16 / "scene_pilot.py")

W, H = 960, 540
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp
key = cam.key

PASS = 1.0
T_PASS1 = SP.SECONDS                          # 29.0
T_TURKEY = T_PASS1 + PASS                     # 30.0
T_PASS2 = T_TURKEY + ST.SECONDS               # 54.0
T_TROUT = T_PASS2 + PASS                      # 55.0
T_END = T_TROUT + SR.SECONDS                  # 78.0
END_SECONDS = 12.0
SECONDS = T_END + END_SECONDS                 # 90.0
assert abs(SECONDS - 90.0) < 1e-6

# The children's sentences in the sheet's `reads` spelling, said once each when the line is finished. Absolute
# times, one at a time, each 2.5 s or more. Nothing else is captioned.
CAPTIONS = [(a, b, s) for a, b, s in SP.CAPTIONS] + \
           [(T_TURKEY + a, T_TURKEY + b, s) for a, b, s in ST.CAPTIONS] + \
           [(T_TROUT + a, T_TROUT + b, s) for a, b, s in SR.CAPTIONS]
CAPTIONS = [(round(a, 3), round(b, 3), s) for a, b, s in CAPTIONS]
for a, b, _ in CAPTIONS:
    assert b - a >= 2.5 - 1e-9, (a, b)
for (a, b, _), (c, d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert c >= b - 1e-9, (b, c)
assert [s for _, _, s in CAPTIONS] == ["A giant three-headed monster.", "Wave at his twin turkey.", "Using up his energy.",
                                       "There is another turkey here.", "Two-headed tin monster fits the submarine."]
assert CAPTIONS[-1][1] <= T_END + 1e-9

WOOD = ST.WOOD


# ------------------------------------------------------------ the passes ---
WHIP1 = (0.15, 0.6)                           # within the pass second
WHIP2 = (0.12, 0.5)


def _pilot_going(u):
    """The pilot's desk as the sheet leaves it (the module's own camera and hands, run on past its last frame)."""
    return SP._desk_frame(SP.SECONDS - 1e-3 + min(u, 0.4))


def _b_arrive(q):
    """B.'s desk as the sheet comes in from the right: q 0 (still on its way, turned 52 degrees, lifted) to 1
    (down, 12 degrees askew: exactly scene_turkey's first frame, the eye rolled 5 degrees with it)."""
    ang = 12.0 + 40.0 * (1 - q)
    dx = 330.0 * (1 - q)
    lift = 20.0 * (1 - q)
    v = ST.view(0.0)
    fr = v.render(ST._desktop(ST.page1_done(), angle=ang, lift=lift, dx=dx))
    w = math.radians(ang)
    a = (ST.SC[0] - 570 + 60 * math.sin(w) + dx, ST.SC[1] + 780 - 560 * math.sin(w))
    if q >= 1:
        P.hand(fr, *v.dpt(*a), pose="hold", tone=ST.PLUM, scale=v.hs((190, 1760)), flip=True, t=0.0, arm=140)
    else:
        P.hand(fr, *v.dpt(*a), pose="hold", tone=ST.PLUM, scale=v.hs((190, 1760)), flip=True, t=0.0, arm=140, lift=lift * 0.6)
    ST._right(fr, v, 0.0)
    ST._head(fr, 0.0, ST._closeness(v), tilt=5, turn=0.15)
    return cam.shoot([(fr, 1.0)], rot=5 + 9 * (1 - q), zoom=1.07, bg=WOOD)


def _pass1(u):
    """Pilot -> B. The whole desk swings left; the page arrives turned."""
    if u < WHIP1[0]:
        return _pilot_going(u)
    b = _b_arrive(cam.smooth(ramp(u, 0.42, 1.0)))
    if u >= WHIP1[1]:
        return b
    return cam.whip(_pilot_going(u), b, ramp(u, *WHIP1), direction=-1)


def _b_going(u):
    """B.'s desk as she pushes the sheet off to her left (scene_turkey's last frame, the sheet and both hands sliding)."""
    tt = ST.SECONDS - 1e-3
    v = ST.view(tt)
    g = cam.smooth(ramp(u, 0.0, 0.6))
    dx = -260.0 * g
    if g <= 0:
        desk = ST._desktop(ST.page2(tt))
    else:
        desk = ST._desktop(ST.page2(tt), lift=10.0 * g, dx=dx)
    fr = v.render(desk)
    ST._left_hold(fr, v, tt, (150 + dx, 1620))
    p, pose, lift = ST.pen(tt)
    arm = key(tt, ST.ARM_KEYS) if pose != "point" else 60
    P.hand(fr, *v.pt((p[0] + dx, p[1])), pose=pose, tone=ST.PLUM, scale=v.hs(p), t=ST._still_t(tt), lift=lift, arm=arm)
    ST._head(fr, tt, ST._closeness(v))
    return fr


W_WIDE = (56.0, math.log(0.8), 760.0, 900.0, 480.0, 240.0)       # W.'s whole desk, before the eye goes to the name line


def _w_arrive(u):
    """W.'s desk: the sheet comes in from the right SIDEWAYS (he circled where it said draw: he took it as it came),
    is turned upright under the teal hand, and the eye is already going in to the name line. At u = 1 this is exactly
    scene_trout's first frame."""
    q = cam.smooth(ramp(u, 0.3, 0.88))
    g = key(u, [(0.5, 0.0), (1.0, 1.0)], "smoother")
    ang = 78.0 * (1 - q)
    dx = 300.0 * (1 - q)
    deg, lz, ax, ay, tx, ty = [lerp(a, b, g) for a, b in zip(W_WIDE, SR.NAME)]
    v = SR.View(deg, math.exp(lz), (ax, ay), (tx, ty), 2.2 * g, 0.0)
    if q >= 1:
        desk = SR._desktop(SR.page2(0.0))
    else:
        desk = SR._desk_plane().copy()
        P.lay(desk, SR.page2(0.0), SR.SC[0] + dx, SR.SC[1], ang, 1.0, lift=16.0 * (1 - q))
    fr = v.render(desk)
    cl = SR._closeness(v)
    if cl < 0.9:
        hp = (150 + dx * 0.6, 1620 - 300 * (1 - q))
        P.hand(fr, *v.pt(hp), pose="hold", tone=SR.TEAL, scale=v.hs(hp), flip=True, t=0.0, arm=140)
    SR._right(fr, v, 0.0)
    y0 = 590 + 330 * clamp((0.8 - 0.62) / 0.7)
    P.head_back(fr, 250, lerp(y0, 880 - 205, g), SR.TEAL, 1.15, hair=SR.HAIR, t=SR._hand_t(0.0))
    return fr


def _pass2(u):
    """B. -> W. Left again; the sheet stays back side up."""
    if u < WHIP2[0]:
        return _b_going(u)
    if u >= WHIP2[1]:
        return _w_arrive(u)
    return cam.whip(_b_going(u), _w_arrive(u), ramp(u, *WHIP2), direction=-1)


# ------------------------------------------------------------ the ending ---
E_UP = (0.0, 1.6)                             # E1: the eye stands up out of the seat
E_HANDS = (0.45, 1.5)                         # the other two pairs of hands come to rest at their edges
E_RISE = (1.6, 6.0)                           # E2
TOPV = (7.0, math.log(0.52), 760.0, 985.0, 480.0, 270.0)          # straight down on the whole of page 2
HERO_BOX = (383, 266, 575, 374)               # where this desk belongs in the room (16:9, round room_layout's hero)
CUP_AT = (SR.SO[0] + SR.SIZE[0] + 215, SR.SO[1] + 1500)          # desk-plane px: beside the sheet, level with "Roll"
T_LAST = SR.SECONDS - 1e-3


@lru_cache(None)
def _page_done():
    return SR.page2(1e6).convert("RGB")


@lru_cache(None)
def _end_plane():
    """W.'s desk as he left it: page 2 with everything the three wrote, his pencil beside it, the cup, the die in it."""
    im = SR._desktop(_page_done())
    P.pencil(im, SR.SO[0] + SR.LAID[0], SR.SO[1] + SR.LAID[1], angle=-72, scale=2.3)
    P.cup(im, CUP_AT[0], CUP_AT[1], scale=3.3, die=True)
    return im


_room_cache = {}


@lru_cache(None)
def _small_page():
    return _page_done().resize((380, 490), Image.LANCZOS)


def _room(t):
    k = int(t * 12)
    if k not in _room_cache:
        if len(_room_cache) > 3:
            _room_cache.clear()
        im = Image.new("RGB", (W, H), (0, 0, 0))
        P.classroom(im, k / 12.0, sheets={P.HERO: _small_page()}, cup_at="hero")
        _room_cache[k] = im
    return _room_cache[k]


@lru_cache(None)
def _floor():
    """What lies beyond the edge of the desk once the eye is high enough to see it: the room's own floor round this
    desk, at this height (the hero box of the room picture, enlarged), so the rise starts from inside the room."""
    return _room(E_RISE[0]).crop(HERO_BOX).resize((W, H), Image.BICUBIC)


def _slide(fr, v, p, tone, flip, arm, off, k, lift=0.0):
    """A flat hand whose palm comes to rest at sheet point p, sliding in along its own forearm."""
    a = math.radians(arm)
    q = (p[0] + math.cos(a) * off, p[1] + math.sin(a) * off)
    P.hand(fr, *v.pt(q), pose="hold", tone=tone, scale=v.hs(p) * k, flip=flip, t=0.0, arm=arm, lift=lift or None)


def _end_desk_at(e):
    g = key(e, [(E_UP[0], 0.0), (E_UP[1], 1.0)], "smoother")
    deg, lz, ax, ay, tx, ty = [lerp(a, b, g) for a, b in zip(SR.B6, TOPV)]
    v = SR.View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0, 0.0)
    fr = cam.tilt(_end_plane(), v.deg, SR.HOR, v.z, SR.F, v.shift, bg=_floor(), shadow=0)
    k = lerp(1.0, 1.45, g)                    # from high up the hands are read against the whole sheet
    h = cam.smooth(ramp(e, *E_HANDS))
    off = 620.0 * (1 - h)
    lf = 12.0 * (1 - h)
    if h > 0:
        # the pilot (ochre), across the desk at the top edge: "Give it back to the pilot" is not done yet
        _slide(fr, v, (-160, 190), "ochre", False, 270, off, k * 0.95, lf)
        _slide(fr, v, (1690, 190), "ochre", True, 270, off, k * 0.95, lf)
        # B. (plum), at the left edge
        _slide(fr, v, (-170, 620), "plum", False, 180, off, k, lf)
        _slide(fr, v, (-170, 1250), "plum", True, 180, off, k, lf)
        # W.'s own left hand comes up onto the near corner
        _slide(fr, v, (300, 1760), SR.TEAL, True, 118, off, k, lf)
    # W.'s right hand, flat on the page where scene_trout left it
    P.hand(fr, *v.pt(SR.PALM), pose="hold", tone=SR.TEAL, scale=v.hs(SR.PALM) * k, t=SR._hand_t(SR.T_LAY), lift=0, arm=62)
    drop = 620.0 * cam.smooth(ramp(e, 0.0, 1.1))                    # standing up: his own head leaves the frame
    if drop < 600:
        P.head_back(fr, 250, 880 - 205 + 2.0 * SR._breath(T_LAST + e) + drop, SR.TEAL, 1.15, hair=SR.HAIR, t=SR._hand_t(T_LAST))
    return fr


@lru_cache(None)
def _end_desk_still():
    return _end_desk_at(E_UP[1])


def _end_desk(e):
    return _end_desk_still() if e >= E_UP[1] else _end_desk_at(e)


def _ending(e):
    if e < E_RISE[0]:                         # E1: up out of the seat
        return _end_desk(e)
    u = ramp(e, *E_RISE)
    room = _room(e)
    if u >= 1:                                # E3: the room, working; the die in the cup
        return room
    a = _end_desk(e)
    melt = cam.smooth((u - 0.5) / 0.42)       # the desk we sat at melts into its place among the twenty
    if melt > 0.004:
        a = Image.blend(a, room.crop(HERO_BOX).resize((W, H), Image.BICUBIC), melt)
    return cam.rise(a, room, u, box=HERO_BOX, tip=26, sway=5)


# ---------------------------------------------------------------- film ---
film = Film("m16", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + 5.0               # Turkey's seat: the pilot's pencil sub outside the glass


def picture(t):
    if t < T_PASS1:
        return SP.frame(t)
    if t < T_TURKEY:
        return _pass1(t - T_PASS1)
    if t < T_PASS2:
        return ST.frame(t - T_TURKEY)
    if t < T_TROUT:
        return _pass2(t - T_PASS2)
    if t < T_END:
        return SR.frame(t - T_TROUT)
    return _ending(t - T_END)


@film.picture
def frame(t, ink):
    ink._grain = False            # the paper's fibre is in the cut pieces themselves
    fr = picture(t)
    ink.img.paste(fr if fr.mode == "RGB" else fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)
    for a, b, text in CAPTIONS:
        if a <= t < b:
            ink.caption(text, size=27)
            break


# --------------------------------------------------------------- sound ---
def _scratch(mix, a, b, gain=0.07, seed=0, lo=1900, hi=7200, pan=0.1):
    """Pencil on paper: a band of noise that swells along one stroke."""
    n = max(0.045, b - a)
    x = mix.band(mix.noise(n), lo, hi)
    tt = mix.t(n)[: len(x)]
    x = x[: len(tt)] * (0.6 + 0.4 * np.sin(2 * np.pi * (9 + seed % 5) * tt + seed)) * np.hanning(len(tt)) ** 0.6
    mix.add(x, a, gain, pan=pan + 0.04 * ((seed % 5) - 2))


def _letters(mix, a, b, n, gain=0.07, seed=0, pan=0.1, fill=(0.62, 0.86)):
    """One scratch a letter, a little uneven, with the lifts between."""
    n = max(1, int(n))
    slot = (b - a) / n
    rs = np.random.RandomState(seed)
    for k in range(n):
        s = a + slot * k + rs.uniform(0, 0.12) * slot
        _scratch(mix, s, s + slot * rs.uniform(*fill), gain * rs.uniform(0.8, 1.15), seed + k, pan=pan)


def _drag(mix, a, b, gain=0.06, seed=0, pan=0.1, lo=1700, hi=6800, rate=7.0):
    """The point not leaving the paper: one long scratch that only swells and thins."""
    n = b - a
    x = mix.band(mix.noise(n), lo, hi)
    tt = mix.t(n)[: len(x)]
    env = np.minimum(1.0, np.minimum(tt / 0.04, (n - tt) / 0.06).clip(0, None))
    x = x[: len(tt)] * (0.72 + 0.28 * np.sin(2 * np.pi * rate * tt + seed)) * env
    mix.add(x, a, gain, pan)


def _go_over(mix, a, b, gain=0.1, seed=0, pan=0.1):
    """A letter gone over: slower, deeper, pressed."""
    n = max(2, int(round((b - a) / 0.14)))
    slot = (b - a) / n
    for k in range(n):
        _scratch(mix, a + slot * k, a + slot * (k + 0.95), gain, seed + k, lo=900, hi=4200, pan=pan)


def _rubber(mix, a, b, gain=0.09, pan=0.1):
    """The eraser: soft, low, 5.5 strokes a second."""
    k, t = 0, a
    while t < b:
        x = mix.band(mix.noise(0.15), 250, 1700) * np.hanning(int(0.15 * mix.rate)) ** 0.8
        mix.add(x, t, gain * (1.0 if k % 2 else 0.8), pan)
        t += 1 / 5.5
        k += 1


def _paper(mix, at, seconds=0.6, gain=0.13, pan=0.0, to=None):
    """A sheet sliding over a desk top."""
    n = int(seconds * mix.rate)
    tt = np.arange(n) / mix.rate
    x = mix.band(mix.noise(seconds), 700, 5200)[:n] * np.hanning(n) ** 0.5 * (0.75 + 0.25 * np.sin(2 * np.pi * 13 * tt))
    x = x + 0.35 * mix.band(mix.noise(seconds), 120, 500)[:n] * np.hanning(n)
    if to is None:
        mix.add(x, at, gain, pan)
    else:                                      # it travels across
        mix.add(x * np.linspace(1, 0, n), at, gain, pan)
        mix.add(x * np.linspace(0, 1, n), at, gain, to)


def _creak(mix, a, b, f0=180.0, f1=260.0, gain=0.05, pan=0.0):
    """A chair."""
    n = max(0.1, b - a)
    tt = mix.t(n)
    fr = lerp(f0, f1, tt / n) * (1 + 0.05 * np.sin(2 * np.pi * 21 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 7)) * np.hanning(len(tt))
    mix.add(mix.band(x, 300, 2400), a, gain, pan)


def _tick(mix, at, gain=0.1, pan=0.2):
    mix.click(at, gain, pan, 6500, 0.015)


def _breath(mix, a, b, gain=0.02, pan=0.0):
    """A sigh: air, no voice."""
    n = b - a
    x = mix.band(mix.noise(n), 300, 1500) * np.hanning(int(n * mix.rate)) ** 1.5
    mix.add(x, a, gain, pan)


def _bubbles(mix, at, n=4, gain=0.07, pan=-0.3):
    for k in range(n):
        tt = mix.t(0.16)
        fr = (380 + 60 * k) * (1 + 0.9 * (tt / 0.16) ** 1.6)
        mix.add(np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7, at + 0.1 * k, gain, pan + 0.2 * k)


def _envelope(n, rate, keys):
    keys = sorted(keys, key=lambda k: k[0])
    for (a, _), (b, _) in zip(keys, keys[1:]):
        assert b > a, (a, b)
    tt = np.arange(n) / rate
    return np.interp(tt, [k[0] for k in keys], [k[1] for k in keys])


# where we are: at a desk (room 1), away in a thought, the tin or the river (room 0), or the child is stuck (the
# room falls away to almost nothing: the film's silences)
B_, C, E = T_TURKEY, T_TROUT, T_END
STUCK = 0.07
ROOM_KEYS = [
    (0.0, 1.0), (8.0, 1.0), (8.7, 0.0), (12.8, 0.0), (13.5, 1.0),                         # the pilot's dive
    (15.1, 1.0), (15.16, 0.3), (15.4, 0.3), (15.5, 1.0),                                  # the point stops over the empty ring
    (17.0, 1.0), (17.3, 0.55), (18.5, 0.55), (18.8, 1.0),                                 # a look into a thought
    (21.4, 1.0), (21.66, 0.55), (22.62, 0.55), (22.86, 1.0),
    (B_ + 1.8, 1.0), (B_ + 2.5, 0.0), (B_ + 6.7, 0.0), (B_ + 7.3, 1.0),                   # into the tin, and back
    (B_ + 13.7, 1.0), (B_ + 13.95, STUCK), (B_ + 17.7, STUCK), (B_ + 17.95, 1.0),         # T8: the long still hold
    (B_ + 18.0, 0.95), (B_ + 18.35, 0.55), (B_ + 18.8, 0.55), (B_ + 19.02, 1.0),
    (C + 4.6, 1.0), (C + 4.8, STUCK), (C + 6.7, STUCK), (C + 6.9, 1.0),                   # W3: the hand does not write
    (C + 7.4, 1.0), (C + 8.1, 0.0), (C + 14.9, 0.0), (C + 15.5, 1.0),                     # the tin, the river
    (C + 20.8, 1.0), (C + 21.0, STUCK), (E - 0.1, STUCK), (E + 0.5, 1.0),                 # W9
    (E + 1.6, 1.0), (E + 5.5, 1.5), (SECONDS, 1.5),                                       # the room
]
DULL_KEYS = [   # water heard from inside: the thought in the ring, Turkey's seat
    (0.0, 0.0), (8.0, 0.0), (8.8, 1.0), (12.6, 1.0), (13.4, 0.0),
    (17.0, 0.0), (17.34, 0.4), (18.52, 0.4), (18.8, 0.0),
    (21.4, 0.0), (21.66, 0.4), (22.62, 0.4), (22.86, 0.0),
    (B_ + 1.8, 0.0), (B_ + 2.6, 1.0), (B_ + 6.5, 1.0), (B_ + 7.3, 0.0),
    (B_ + 17.95, 0.0), (B_ + 18.35, 0.4), (B_ + 18.8, 0.4), (B_ + 19.02, 0.0),
    (C + 7.4, 0.0), (C + 8.2, 1.0), (C + 8.7, 1.0), (C + 9.5, 0.0),
    (C + 13.9, 0.0), (C + 14.6, 1.0), (C + 14.9, 1.0), (C + 15.5, 0.0), (SECONDS, 0.0),
]
OPEN_KEYS = [   # the river
    (0.0, 0.0), (C + 8.6, 0.0), (C + 9.5, 1.0), (C + 13.8, 1.0), (C + 14.6, 0.0), (SECONDS, 0.0),
]


def _beds(mix):
    # a room of children, far off: air, and voices too far away to be words
    room = Mix(SECONDS, seed=21)
    room.room(0.0, SECONDS, 0.05, hum=60)
    rs = np.random.RandomState(16)
    t = 0.3
    while t < SECONDS - 2.5:
        d = rs.uniform(1.0, 2.6)
        room.murmur(t, d, gain=rs.uniform(0.012, 0.03), pitch=rs.uniform(230, 340), pan=rs.uniform(-0.9, 0.9), seed=int(t * 10))
        if rs.rand() < 0.35:                  # a pencil dropped, a chair leg, somewhere
            room.step(t + rs.uniform(0.2, 1.0), rs.uniform(0.01, 0.025), rs.uniform(-0.9, 0.9), "wood")
        t += rs.uniform(0.9, 2.2)
    for ch in (room.L, room.R):               # far off: nothing bright gets here
        ch[:] = room.lowpass(ch, 1500)
    room.reverb(0.5, 1.6)
    env = _envelope(room.n, room.rate, ROOM_KEYS)
    mix.L += room.L * env * 1.8
    mix.R += room.R * env * 1.8
    # water and a low drone: only away from the desk. Dull and close inside; open and bright in the river.
    wat = Mix(SECONDS, seed=22)
    wat.water(0.0, SECONDS, 0.085)
    dull = Mix(SECONDS, seed=23)
    dull.L[:] = wat.lowpass(wat.L, 650) * 2.2
    dull.R[:] = wat.lowpass(wat.R, 650) * 2.2
    dull.drone(0.0, SECONDS, (55, 82.5, 110), 0.07, attack=0.1, release=0.1)
    wat.drone(0.0, SECONDS, (55, 82.5, 110), 0.045, attack=0.1, release=0.1)
    env = _envelope(dull.n, dull.rate, DULL_KEYS)
    mix.L += dull.L * env * 0.7
    mix.R += dull.R * env * 0.7
    env = _envelope(wat.n, wat.rate, OPEN_KEYS)
    mix.L += wat.L * env * 0.8
    mix.R += wat.R * env * 0.8


@film.sound
def sound(mix):
    # --- I. the pilot (ochre)
    _creak(mix, 1.2, 2.1, 150, 210, 0.05, -0.2)                 # coming down into the seat
    D = SP.DRAWN
    span = lambda g: (D[g][0][0], D[g][-1][0])
    for i, (g, n, gain) in enumerate((("box", 5, 0.085), ("dome", 2, 0.08), ("blocks", 6, 0.08), ("right", 5, 0.08),
                                      ("window", 1, 0.08), ("head", 6, 0.04), ("faint", 4, 0.035))):
        a, b = span(g)
        _letters(mix, a, b, n, gain, 100 + 7 * i, 0.12, fill=(0.7, 0.92))
    _drag(mix, span("scribble1")[0], span("scribble2")[1], 0.1, 3, 0.12, lo=900, hi=4600, rate=5.0)   # round and round, black
    mix.whoosh(SP.LOOK2[0], 0.24, 0.03, 0.4)                    # a quick look across at the slip, and back
    mix.whoosh(SP.LOOK2[2], 0.24, 0.03, -0.2)
    mix.whoosh(SP.DIVE_IN[0], 1.1, 0.07, 0.0)                   # down through the drawn ring
    mix.whoosh(SP.DIVE_OUT[0], 1.0, 0.06, 0.0)
    for at in (16.56, 17.08):                                   # the finger stops at each question mark
        mix.step(at, 0.035, 0.0, "wood")
    for i, a in enumerate(SP.ACTS):
        kind = type(a).__name__
        if a.t0 >= SP.NOLIFT[0] - 1e-6 and kind == "Write":
            continue                                            # line 3 is one scratch (below)
        if kind == "Write":
            _letters(mix, a.t0, a.t1, len(a.text.replace(" ", "")), 0.05 + 0.03 * a.weight, 120 + 17 * i, 0.12)
        else:
            _go_over(mix, a.t0, a.t1, 0.075 + 0.03 * a.weight, 120 + 17 * i, 0.12)
    _drag(mix, SP.NOLIFT[0], 26.03, 0.075, 5, 0.12, rate=8.2)   # useinguphisenergy: the point hardly leaves the paper
    mix.whoosh(SP.UP_CLUE[0], 0.4, 0.035, 0.0)                  # eyes up to the printed clue
    mix.whoosh(SP.DOWN_CLUE[0], 0.4, 0.035, 0.0)
    mix.step(27.84, 0.03, -0.2, "wood")                         # the finger finds "Pass your paper left"
    _paper(mix, 28.4, 0.6, 0.06, -0.1)                          # taken by its edge

    # --- the pass, left
    _paper(mix, T_PASS1 - 0.05, 1.0, 0.16, 0.5, to=-0.4)
    mix.whoosh(T_PASS1 + WHIP1[0], 0.45, 0.05, 0.0)
    _creak(mix, T_PASS1 + 0.55, T_PASS1 + 1.0, 230, 170, 0.045, -0.4)

    # --- II. B. (plum, a green pencil)
    b = B_
    _paper(mix, b + 0.1, 0.7, 0.07, -0.1)                       # squared up
    for at in (1.0, 1.3):
        mix.step(b + at, 0.03, -0.1, "wood")                    # a finger on the black window, on the faint head
    mix.whoosh(b + 1.8, 1.1, 0.07, 0.0)                         # down through the page's porthole
    mix.whoosh(b + ST.T_TURN[0], 1.2, 0.05, 0.3)                # turning round in the tin
    mix.whoosh(b + 6.3, 1.0, 0.06, 0.0)
    _paper(mix, b + 7.3, 0.7, 0.12, 0.0)                        # turned over
    mix.thud(b + 7.95, 180, 0.05, 0.0, 0.08)
    _go_over(mix, b + ST.T_B[0], b + ST.T_B[1], 0.085, 201, 0.0)                       # a large firm B
    _letters(mix, b + ST.T_TRI[0], b + ST.T_TRI[1], 3, 0.085, 202, 0.0, fill=(0.75, 0.92))   # the button's triangle
    _letters(mix, b + ST.T_G1[0], b + ST.T_G1[1], 13, 0.07, 203, 0.0)                  # two lines we do not get to read
    _letters(mix, b + ST.T_G2[0], b + ST.T_G2[1], 11, 0.07, 204, 0.0)
    _scratch(mix, b + ST.T_STRAY[0], b + ST.T_STRAY[1], 0.06, 205, pan=0.0)
    _rubber(mix, b + ST.T_R1[0], b + ST.T_R1[1], 0.1, 0.0)
    _rubber(mix, b + ST.T_R2[0], b + ST.T_R2[1], 0.1, 0.0)
    _paper(mix, b + ST.T_BRUSH[0], 0.3, 0.05, 0.3)              # the crumbs brushed off
    # T8: nothing. The pencil does not come down.
    _breath(mix, b + ST.T_SIGH[0], b + ST.T_SIGH[1], 0.022, 0.0)
    _letters(mix, b + ST.T_W1[0], b + ST.T_W1[1], 7, 0.075, 206, 0.0)                  # there is
    _scratch(mix, b + ST.T_WA[0], b + ST.T_WA[1], 0.06, 207, pan=0.0)                  # a
    _letters(mix, b + ST.T_W2[0], b + ST.T_W2[1], 7, 0.085, 208, 0.0)                  # another
    _letters(mix, b + ST.T_W3[0], b + ST.T_W3[1], 6, 0.075, 209, 0.0)                  # turkey
    _scratch(mix, b + ST.T_YT[0], b + ST.T_YT[1] + 0.03, 0.09, 210, pan=0.0)           # the y's loop
    _letters(mix, b + ST.T_W4[0], b + ST.T_W4[1], 4, 0.075, 211, 0.0)                  # here
    for at in (ST.T_DOT[0] + 0.01, ST.T_DOT[1] - 0.01):                                # the full stop, pressed and pressed again
        mix.thud(b + at, 170, 0.09, 0.0, 0.07)
        _tick(mix, b + at, 0.07, 0.0)
    mix.step(b + 23.2, 0.03, -0.2, "wood")                      # the finger finds "Pass it left again"

    # --- the pass, left again
    _paper(mix, T_PASS2 - 0.05, 1.0, 0.16, 0.5, to=-0.4)
    mix.whoosh(T_PASS2 + WHIP2[0], 0.42, 0.05, 0.0)
    _creak(mix, T_PASS2 + 0.5, T_PASS2 + 0.95, 210, 160, 0.04, 0.4)

    # --- III. W. (teal)
    c = C
    _letters(mix, c + SR.T_W[0], c + SR.T_W[1], 4, 0.065, 301, -0.05, fill=(0.7, 0.9))  # a small W, four strokes
    _drag(mix, c + SR.T_LOOP[0], c + SR.T_LOOP[1], 0.065, 7, -0.05, rate=3.1)           # round the whole plate, slowly
    # W3: nothing.
    _paper(mix, c + 6.8, 0.6, 0.11, 0.0)                        # turned to the front
    mix.whoosh(c + SR.DIVE_IN[0], 1.0, 0.07, 0.0)
    mix.whoosh(c + SR.GLASS_OUT[0] + 0.3, 0.9, 0.06, 0.0)       # out through the glass
    _bubbles(mix, c + SR.GLASS_OUT[0] + 0.75)
    mix.whoosh(c + SR.SWING[0], 1.2, 0.06, -0.3)                # the swing round
    mix.thud(c + SR.T_LOWER[1], 120, 0.06, -0.2, 0.2)           # rim on rim: it fits
    mix.whoosh(c + SR.GLASS_IN[0], 0.9, 0.06, 0.0)
    _bubbles(mix, c + SR.GLASS_IN[0] + 0.35, 3, 0.05, 0.1)
    mix.whoosh(c + SR.DIVE_OUT[0], 0.7, 0.06, 0.0)
    _paper(mix, c + 15.5, 0.5, 0.11, 0.0)                       # and over again
    mix.step(c + 16.32, 0.035, -0.4, "wood")                    # the left finger comes down on the circled plate
    _tick(mix, c + 16.3, 0.06, 0.1)                             # the point touches the printed "fits."
    for i, (word, a, b2) in enumerate(SR.WORDS):                # each letter made alone
        _letters(mix, c + a, c + b2, len(word), 0.075, 310 + 9 * i, -0.05, fill=(0.4, 0.55))
    # W9: nothing, until the pencil is laid down.
    _tick(mix, c + SR.T_LAY + 0.02, 0.07, 0.3)
    mix.thud(c + SR.T_LAY + 0.02, 210, 0.04, 0.3, 0.06)

    # --- IV. the ending
    _creak(mix, E + 0.2, E + 1.0, 160, 240, 0.05, 0.0)          # standing up out of the seat
    for k, pan in enumerate((-0.1, 0.2, -0.6, -0.5, -0.3)):     # five flat hands come to rest round the sheet
        mix.step(E + E_HANDS[1] - 0.2 + 0.045 * k, 0.03, pan, "wood")
    mix.whoosh(E + E_RISE[0], 3.2, 0.035, 0.0)                  # up and away
    _creak(mix, E + 8.8, E + 9.5, 170, 230, 0.04, 0.5)          # one chair, somewhere
    # the die is in the cup. Nothing rolls.
    mix.L *= 2.0                               # the desk is the film: pencil and paper sit above the beds
    mix.R *= 2.0
    _beds(mix)


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "m16"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            Wd._sheet(ims, 4, d / "sheet.png", scale=0.5)
            print("sheet ->", d / "sheet.png")
