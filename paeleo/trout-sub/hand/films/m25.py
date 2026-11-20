"""m25 · the MAKING film for porthole 25 · Lock · "Diner Trout wearing inverted fishbowl".

Not what the children wrote (that is c25) but the writing of it: one Porthole Log passing through three children
(see swarm/m25/board.md for the traces of working that are really on the sheet, and where each is shown).

   0.0 .. 34.6   the pilot, M. (ochre): page 1                                  swarm/m25/scene_pilot.py
  34.6 .. 35.6   THE PASS, left: the sheet slides off M.'s desk; whip; it comes down in front of K. front up and
                 UPSIDE DOWN (the bowl at the bottom with its mouth up, the legs in the air)
  35.6 .. 59.6   the first friend, K. (teal): Turkey's seat                     swarm/m25/scene_turkey.py
  59.6 .. 60.6   THE PASS, left again: whip; the sheet comes down on N.'s desk back up and a QUARTER TURN round
  60.6 .. 84.1   the next friend, N. (rust): the trout's side                   swarm/m25/scene_trout.py
  84.1 .. 93.6   the ending (this file): the eye stands up out of N.'s seat, whose pencil is still up over ending 5;
                 the whole back of the sheet from above, K.'s three small lines beside N.'s two enormous ones, four
                 empty rules, "I rolled" empty; three pairs of hands at three edges; the cup with the die in it;
                 cam.rise to the whole room; nothing is thrown.

Sound is synthesized with the kit's Mix: a pencil scratch a letter (light for the bowl's loops, slow and pressed
on one spot for M.'s three b's, a broad soft scrape for N.'s blunt pencil), paper at each flip and each pass, a
chair, a room of children far off under every desk shot, water and a low drone only away from the desk (dull and
close inside the thought and the tin, open in the river), and next to nothing while a child is stuck. Nobody on this
sheet used the rubber, so no rubber is heard.

Foraged pieces come only through c25's world (Audubon's turkey, Denton's trout): credits/m25.json.

  python3 films/m25.py                      -> assets/films/m25.mp4 (+ .webp poster)
  python3 films/m25.py --stills 3 7.8 ...   -> films/stills/m25/*.png and sheet.png
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
sys.path.insert(0, str(HERE / "swarm" / "c25"))

from kit import Film, Mix, clamp, lerp, ramp  # noqa: E402
import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c25 world; not edited)

M25 = HERE / "swarm" / "m25"


def _load(name, path):
    """The m25 scene modules share file names with c25's, so they are loaded by path, not by import."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SR = _load("m25_scene_trout", M25 / "scene_trout.py")
ST = SR.KT                                    # the same instance the trout scene takes K.'s column from
SP = _load("m25_scene_pilot", M25 / "scene_pilot.py")

W, H = 960, 540
key = cam.key

PASS = 1.0
T_PASS1 = SP.SECONDS                          # 34.6
T_TURKEY = T_PASS1 + PASS                     # 35.6
T_PASS2 = T_TURKEY + ST.SECONDS               # 59.6
T_TROUT = T_PASS2 + PASS                      # 60.6
T_END = T_TROUT + SR.SECONDS                  # 84.1
END_SECONDS = 9.5
SECONDS = round(T_END + END_SECONDS, 3)       # 93.6
assert abs(SECONDS - 93.6) < 1e-6

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
assert [s for _, _, s in CAPTIONS] == [
    "A trout, and the trout think it is a bird in a bottle.", "Panic.", "By panicking.",
    "The air runs out.", "A little uncomfy.", "It is not wet.",
    "The fish swim next to the astronaut, looking..."]
assert CAPTIONS[-1][1] <= T_END + 1e-9

WOOD = ST.WOOD
SC, SO, SIZE = ST.SC, ST.SO, ST.SIZE


# ------------------------------------------------------------ the passes ---
WHIP1 = (0.14, 0.6)                           # within the pass second
WHIP2 = (0.14, 0.6)
P_LAST = SP.SECONDS - 1e-3
K_LAST = ST.SECONDS - 1e-3


@lru_cache(None)
def _pilot_page():
    return SP.page1(SP.SECONDS)


def _pilot_going(u):
    """M.'s desk as his left hand pushes the finished sheet off to the left (the module's own camera, hands and
    desk, run on past its last frame). At u = 0 it is the module's last frame."""
    g = cam.smooth(ramp(u, 0.0, 0.62))
    if g <= 0:
        return SP.frame(P_LAST)
    c = SP._cam(P_LAST)
    dx = -760.0 * g
    im = SP._desk_base(False).copy()
    P.lay(im, _pilot_page(), SP.SCX + dx, SP.SCY, -7.0 * g, 1.0, lift=12.0 * g)
    P.pencil(im, SP.GROOVE[0], SP.GROOVE[1], 0, scale=1.25)
    fr = cam.tilt(im, c["deg"], c["hor"], c["zoom"], 700, c["shift"], bg=(92, 66, 44), shadow=0)
    lx, ly = SP.D(SP.LREST[0] + 120 + dx, SP.LREST[1] - 200 * g)
    s = 0.74 * SP._hand_scale(c, lx, ly)
    P.hand(fr, *SP._tp(c, lx, ly), pose="hold", tone=SP.TONE, scale=s, flip=True, t=P_LAST, arm=142)
    SP._right_hand(fr, c, P_LAST)
    return cam.shoot([(fr, 1.0)], zoom=SP.SHOOT_ZOOM, focus=1.0, aperture=6, shake=c["shake"], t=P_LAST)


def _k_arrive(q):
    """K.'s desk as the sheet comes in from the right: q 0 (on its way, lifted, turned past upside down) to 1 (down,
    front up and upside down under two teal hands: exactly scene_turkey's first frame)."""
    if q >= 1:
        return ST.frame(0.0)
    v = ST.view(0.0)
    ang = 180.0 + 34.0 * (1 - q)
    dx = 1100.0 * (1 - q)
    desk = ST._desk_plane().copy()
    P.lay(desk, ST.page1_done(), SC[0] + dx, SC[1], ang, 1.0, lift=22.0 * (1 - q))
    fr = v.render(desk)
    for flip, a0, arm in ((False, 62.0, 62), (True, 215.0, 132)):     # the two hands that will walk it round, coming up
        x = SC[0] + 640.0 * math.cos(math.radians(a0))
        y = SC[1] + 80 + 672.0 * math.sin(math.radians(a0))
        P.hand(fr, *v.dpt(x + 0.5 * dx, y + 520.0 * (1 - q)), pose="hold", tone=ST.TEAL, scale=v.hs((760, 1300)), flip=flip,
               t=0.0, arm=arm, lift=10.0 * (1 - q) or None)
    ST._head(fr, 0.0, ST._closeness(v), dy=120 + 240.0 * (1 - q))
    return cam.shoot([(fr, 1.0)], rot=7.0 * (1 - q), zoom=1.0 + 0.06 * (1 - q), bg=WOOD)


def _pass1(u):
    """M. -> K. The whole desk swings left; the page arrives upside down."""
    if u < WHIP1[0]:
        return _pilot_going(u)
    b = _k_arrive(cam.smooth(ramp(u, 0.4, 0.98)))
    if u >= WHIP1[1]:
        return b
    return cam.whip(_pilot_going(u), b, ramp(u, *WHIP1), direction=-1)


def _k_going(u):
    """K.'s desk as she pushes the sheet off to her left (scene_turkey's last frame, the sheet and her left hand
    sliding)."""
    g = cam.smooth(ramp(u, 0.0, 0.62))
    if g <= 0:
        return ST.frame(K_LAST)
    v = ST.view(K_LAST)
    dx = -900.0 * g
    desk = ST._desk_plane().copy()
    P.lay(desk, ST.page2(K_LAST), SC[0] + dx, SC[1], -8.0 * g, 1.0, lift=12.0 * g)
    fr = v.render(desk)
    ST._left_hold(fr, v, K_LAST, (150 + 200 * g + dx, 1620 - 260 * g))
    ST._right(fr, v, K_LAST)
    ST._head(fr, K_LAST, ST._closeness(v))
    return fr


def _n_arrive(q):
    """N.'s desk as the sheet comes in from the right, back up: q 0 (on its way, lifted, more than a quarter turn
    round) to 1 (down, a quarter turn clockwise, one rust hand flat on it: exactly scene_trout's first frame)."""
    if q >= 1:
        return SR.frame(0.0)
    v = SR.view(0.0)
    ang = 90.0 + 32.0 * (1 - q)
    dx = 1100.0 * (1 - q)
    desk = ST._desk_plane().copy()
    P.lay(desk, SR.page2(0.0), SC[0] + dx, SC[1], ang, 1.0, lift=22.0 * (1 - q))
    fr = v.render(desk)
    P.hand(fr, *v.dpt(SC[0] - 600.0 + 0.5 * dx, SC[1] + 60.0 + 460.0 * (1 - q)), pose="hold", tone=SR.RUST,
           scale=v.hs((200, 1540), 1.08), flip=True, t=0.0, arm=112 + 27, lift=10.0 * (1 - q) or None)
    SR._right(fr, v, 0.0)
    SR._head(fr, 0.0)
    return cam.shoot([(fr, 1.0)], rot=-6.0 * (1 - q), zoom=1.0 + 0.06 * (1 - q), bg=WOOD)


def _pass2(u):
    """K. -> N. Left again; the sheet stays back side up and arrives a quarter turn round."""
    if u < WHIP2[0]:
        return _k_going(u)
    b = _n_arrive(cam.smooth(ramp(u, 0.4, 0.98)))
    if u >= WHIP2[1]:
        return b
    return cam.whip(_k_going(u), b, ramp(u, *WHIP2), direction=-1)


# ------------------------------------------------------------ the ending ---
E_UP = (0.0, 1.5)                             # E1: the eye stands up out of the seat
E_HANDS = (0.4, 1.4)                          # the other hands come to rest at their edges
E_RISE = (1.5, 5.5)                           # E2: the rise; E3 after it: the room, the die in the cup
TOPV = (6.0, math.log(0.5), 760.0, 985.0, 480.0, 270.0)           # straight down on the whole of page 2
HERO_BOX = (383, 266, 575, 374)               # where this desk belongs in the room (16:9, round room_layout's hero)
CUP_AT = (SO[0] + SIZE[0] + 205, SO[1] + 700)                     # desk-plane px: right of the sheet, as in the room
N_LAST = SR.SECONDS - 1e-3


@lru_cache(None)
def _page_done():
    return SR.page2(SR.SECONDS).convert("RGB")


@lru_cache(None)
def _end_plane():
    """N.'s desk as it was left: the back of the sheet with everything K. and N. wrote, the cup, the die in it."""
    im = ST._desktop(_page_done())
    P.cup(im, CUP_AT[0], CUP_AT[1], scale=3.2, die=True)
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
    desk (the hero box of the empty room, enlarged), so the rise starts from inside the room."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    P.classroom(im, 0.0, sheets={P.HERO: _small_page()}, cup_at="hero", children=False)
    return im.crop(HERO_BOX).resize((W, H), Image.BICUBIC)


def _slide(fr, v, p, tone, flip, arm, off, k, lift=0.0):
    """A flat hand whose palm comes to rest at sheet point p, sliding in along its own forearm."""
    a = math.radians(arm)
    q = (p[0] + math.cos(a) * off, p[1] + math.sin(a) * off)
    P.hand(fr, *v.pt(q), pose="hold", tone=tone, scale=v.hs(p) * k, flip=flip, t=0.0, arm=arm, lift=lift or None)


def _end_desk_at(e):
    g = key(e, [(E_UP[0], 0.0), (E_UP[1], 1.0)], "smoother")
    deg, lz, ax, ay, tx, ty = [lerp(a, b, g) for a, b in zip(SR.STILL, TOPV)]
    v = SR.View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0, 0.0)
    fr = cam.tilt(_end_plane(), v.deg, ST.HOR, v.z, ST.F, v.shift, bg=_floor(), shadow=0)
    k = lerp(1.0, 1.5, g)                     # from high up the hands are read against the whole sheet
    h = cam.smooth(ramp(e, *E_HANDS))
    off = 640.0 * (1 - h)
    lf = 12.0 * (1 - h)
    if h > 0:
        # M. (ochre), across the desk at the top edge: "Give it back to the pilot" has not happened
        _slide(fr, v, (330, -150), "ochre", False, 270, off, k * 0.95, lf)
        _slide(fr, v, (1190, -150), "ochre", True, 270, off, k * 0.95, lf)
        # K. (teal), at the right edge, below the cup
        _slide(fr, v, (1700, 1180), ST.TEAL, False, 0, off, k, lf)
        _slide(fr, v, (1700, 1700), ST.TEAL, True, 0, off, k, lf)
        # N.'s own left hand comes up onto the near corner
        _slide(fr, v, (240, 1800), SR.RUST, True, 118, off, k, lf)
    # N.'s right hand where scene_trout left it: over the start of ending 5, the point up. It has not written.
    P.hand(fr, *v.pt(SR.HOVER5), pose="hover", tone=SR.RUST, scale=v.hs(SR.HOVER5, 1.08) * k, t=SR.T_STILL, lift=16, arm=74)
    drop = 640.0 * cam.smooth(ramp(e, 0.0, 1.1))                   # standing up: his own head leaves the frame
    if drop < 620:
        P.head_back(fr, 176, 652 + drop, SR.RUST, 1.2, hair=SR.HAIR, t=SR.T_STILL)
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
    melt = cam.smooth((u - 0.36) / 0.4)       # the desk we sat at melts into its place among the twenty
    if melt > 0.004:
        a = Image.blend(a, room.crop(HERO_BOX).resize((W, H), Image.BICUBIC), melt)
    return cam.rise(a, room, u, box=HERO_BOX, tip=26, sway=5)


# ---------------------------------------------------------------- film ---
film = Film("m25", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + 6.2               # Turkey's seat: the pilot's pencil drawing outside the glass


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


def _letters(mix, a, b, n, gain=0.07, seed=0, pan=0.1, fill=(0.62, 0.86), lo=1900, hi=7200):
    """One scratch a letter, a little uneven, with the lifts between."""
    n = max(1, int(n))
    slot = (b - a) / n
    rs = np.random.RandomState(seed)
    for k in range(n):
        s = a + slot * k + rs.uniform(0, 0.12) * slot
        _scratch(mix, s, s + slot * rs.uniform(*fill), gain * rs.uniform(0.8, 1.15), seed + k, lo=lo, hi=hi, pan=pan)


def _drag(mix, a, b, gain=0.06, seed=0, pan=0.1, lo=1700, hi=6800, rate=7.0, to=None):
    """The point not leaving the paper: one long scratch that only swells and thins."""
    n = b - a
    x = mix.band(mix.noise(n), lo, hi)
    tt = mix.t(n)[: len(x)]
    env = np.minimum(1.0, np.minimum(tt / 0.04, (n - tt) / 0.06).clip(0, None))
    x = x[: len(tt)] * (0.72 + 0.28 * np.sin(2 * np.pi * rate * tt + seed)) * env
    if to is None:
        mix.add(x, a, gain, pan)
    else:                                      # it goes off to one side, thinning
        k = np.linspace(1, 0, len(x))
        mix.add(x * k, a, gain, pan)
        mix.add(x * (1 - k) * 0.5, a, gain, to)


def _go_over(mix, a, b, gain=0.1, seed=0, pan=0.1):
    """A letter gone over: slower, deeper, pressed, on one spot."""
    n = max(2, int(round((b - a) / 0.14)))
    slot = (b - a) / n
    for k in range(n):
        _scratch(mix, a + slot * k, a + slot * (k + 0.95), gain, seed + k, lo=900, hi=4200, pan=pan)


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


# where we are: at a desk (room 1), away in a thought, the tin or the river (room 0), a look into a thought ring
# (room a little down), or the child is stuck (the room falls away to almost nothing: the film's silences)
B_, C, E = T_TURKEY, T_TROUT, T_END
STUCK = 0.06
RINGED = 0.5
ROOM_KEYS = [
    (0.0, 1.0), (8.0, 1.0), (8.7, 0.0), (12.5, 0.0), (13.2, 1.0),                         # M.'s dive into the bowl
    (22.4, 1.0), (22.8, RINGED), (24.0, RINGED), (24.4, 1.0),                             # the bottle, in a ring
    (26.9, 1.0), (27.05, STUCK), (28.7, STUCK), (28.85, 1.0),                             # P13: stuck over the third rule
    (B_ + 2.8, 1.0), (B_ + 3.5, 0.0), (B_ + 8.1, 0.0), (B_ + 8.8, 1.0),                   # K. in the tin, and back
    (B_ + 12.4, 1.0), (B_ + 12.9, RINGED), (B_ + 14.3, RINGED), (B_ + 14.8, 1.0),
    (B_ + 15.35, 1.0), (B_ + 15.5, STUCK), (B_ + 16.1, STUCK), (B_ + 16.3, RINGED),       # K10: the pencil up, not moving
    (B_ + 17.9, RINGED), (B_ + 18.4, 1.0),
    (B_ + 19.8, 1.0), (B_ + 20.3, RINGED), (B_ + 21.9, RINGED), (B_ + 22.4, 1.0),
    (C + 4.0, 1.0), (C + 4.7, 0.0), (C + 11.6, 0.0), (C + 12.3, 1.0),                     # N.: the tin, the river
    (C + 17.2, 1.0), (C + 17.5, STUCK), (E - 0.2, STUCK), (E + 0.9, 1.0),                 # N11: the long still hold
    (E + 1.5, 1.0), (E + 5.5, 1.5), (SECONDS, 1.5),                                       # the room
]
DULL_KEYS = [   # water heard from inside: the thought, a thought ring, Turkey's seat
    (0.0, 0.0), (8.0, 0.0), (8.8, 1.0), (12.4, 1.0), (13.2, 0.0),
    (22.4, 0.0), (22.8, 0.4), (24.0, 0.4), (24.4, 0.0),
    (B_ + 2.8, 0.0), (B_ + 3.6, 1.0), (B_ + 8.0, 1.0), (B_ + 8.8, 0.0),
    (B_ + 12.4, 0.0), (B_ + 12.9, 0.4), (B_ + 14.3, 0.4), (B_ + 14.8, 0.0),
    (B_ + 15.6, 0.0), (B_ + 16.0, 0.3), (B_ + 16.2, 0.04), (B_ + 16.6, 0.4), (B_ + 17.9, 0.4), (B_ + 18.4, 0.0),
    (B_ + 19.8, 0.0), (B_ + 20.3, 0.4), (B_ + 21.9, 0.4), (B_ + 22.4, 0.0),
    (C + 4.0, 0.0), (C + 4.8, 1.0), (C + 5.1, 1.0), (C + 5.9, 0.0),
    (C + 10.6, 0.0), (C + 11.3, 1.0), (C + 11.6, 1.0), (C + 12.3, 0.0), (SECONDS, 0.0),
]
OPEN_KEYS = [   # the lock and the river, wet
    (0.0, 0.0), (C + 5.0, 0.0), (C + 5.9, 1.0), (C + 10.5, 1.0), (C + 11.3, 0.0), (SECONDS, 0.0),
]


def _beds(mix):
    # a room of children, far off: air, and voices too far away to be words
    room = Mix(SECONDS, seed=21)
    room.room(0.0, SECONDS, 0.05, hum=60)
    rs = np.random.RandomState(25)
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
    # --- I. the pilot, M. (ochre). He never rubs: his corrections are pressure.
    _creak(mix, 1.0, 1.9, 150, 210, 0.05, -0.2)                 # coming down into the seat
    mix.whoosh(2.64, 0.3, 0.03, -0.4)                           # eyes to the slip, and back
    mix.whoosh(3.34, 0.3, 0.03, 0.2)
    D = SP.DRAWN
    span = lambda g: (D[g][0][0], D[g][-1][0])                  # noqa: E731
    _drag(mix, *span("bowl"), 0.05, 3, 0.12, lo=2200, hi=7000, rate=2.7)       # round and round, lightly
    for i, (g, n) in enumerate((("body", 2), ("arms", 3), ("legs", 4), ("lowtail", 3))):
        _letters(mix, *span(g), n, 0.05, 100 + 7 * i, 0.12, fill=(0.7, 0.92))
    mix.whoosh(SP.DIVE_IN[0], 1.1, 0.07, 0.0)                   # down through the drawn ring
    _bubbles(mix, 9.5, 3, 0.04, -0.2)                           # a fish going round in a bowl
    mix.whoosh(SP.T_TURN[0], 0.8, 0.05, 0.0)                    # the bowl turns over
    mix.thud(SP.T_TURN[1], 110, 0.07, 0.0, 0.25)                # and comes down on the shoulders
    mix.whoosh(SP.DIVE_OUT[0], 1.0, 0.06, 0.0)
    for i, (g, n) in enumerate((("fish", 2), ("tail", 2), ("fin_mouth", 5))):  # the fish, pressed
        a, b = span(g)
        slot = (b - a) / n
        for k in range(n):
            _scratch(mix, a + slot * k, a + slot * (k + 0.92), 0.11, 140 + 5 * i + k, lo=900, hi=4600, pan=0.12)
    mix.whoosh(SP.DOWN[0], 0.42, 0.035, 0.0)                    # eyes down the page
    for at in (16.5, 18.04):                                    # the point stops under each question mark
        _tick(mix, at, 0.05, 0.1)
    for i, a in enumerate(SP.ACTS):
        if type(a).__name__ == "Write":
            n = len(a.text.replace(" ", ""))
            _letters(mix, a.t0, a.t1, n, 0.05 + 0.03 * a.weight, 120 + 17 * i, 0.12)
        else:                                                   # gone over: the B, the b, "by" twice
            _go_over(mix, a.t0, a.t1, 0.07 + 0.035 * a.weight, 120 + 17 * i, 0.12)
    _paper(mix, SP.FLIP[0], 0.5, 0.12, -0.1)                    # the sheet turned over to the trout's plates
    _tick(mix, 20.99, 0.05, 0.2)                                # the point under the plate's capital B
    _paper(mix, SP.FLIP[3] + 0.02, 0.45, 0.12, -0.1)            # and back
    _tick(mix, 25.05, 0.045, 0.0)                               # under "one thing"
    # 27.0 .. 28.76: nothing. He is stuck over the third rule.
    _tick(mix, 30.88, 0.045, 0.0)                               # the point under his own "panit"
    _tick(mix, SP.LAID, 0.08, 0.2)                              # the pencil laid in the groove
    mix.thud(SP.LAID + 0.01, 220, 0.04, 0.2, 0.06)

    # --- the pass, left
    _paper(mix, T_PASS1 - 0.05, 1.0, 0.16, 0.5, to=-0.4)
    mix.whoosh(T_PASS1 + WHIP1[0], 0.46, 0.05, 0.0)
    _creak(mix, T_PASS1 + 0.55, T_PASS1 + 1.0, 230, 170, 0.045, -0.4)

    # --- II. K. (teal): sharp, small, on the rule
    b = B_
    _paper(mix, b + 0.4, 0.55, 0.08, -0.2)                      # two hands walk the sheet round the right way up
    _paper(mix, b + 0.9, 0.55, 0.08, 0.2)
    for at in (1.86, 2.25, 2.78):                               # the finger: under panit, under by paniting, under "air"
        mix.step(b + at, 0.03, -0.1, "wood")
    mix.whoosh(b + ST.T_DIVE[0], 1.1, 0.07, 0.0)                # down through the page's porthole
    mix.whoosh(b + ST.T_TURN[0], 1.3, 0.05, 0.3)                # turning round in the tin
    mix.thud(b + ST.BEAT + 0.05, 90, 0.08, -0.4, 0.3)           # one wing-beat
    _bubbles(mix, b + ST.BEAT + 0.2, 5, 0.06, -0.4)             # a puff
    _tick(mix, b + ST.BEAT + 0.3, 0.07, 0.5)                    # the gauge drops a tick
    mix.whoosh(b + ST.T_UP[0], 1.0, 0.06, 0.0)
    _paper(mix, b + 8.8, 0.6, 0.12, 0.0)                        # turned over to her side
    _letters(mix, b + ST.T_K[0], b + ST.T_K[1], 2, 0.075, 201, 0.0, fill=(0.75, 0.92))        # a small k
    _letters(mix, b + ST.T_TRI[0], b + ST.T_TRI[1], 3, 0.08, 202, 0.0, fill=(0.78, 0.94))     # a triangle, three sides
    _letters(mix, b + ST.T_L1[0], b + ST.T_L1[1], 13, 0.075, 203, 0.0)                        # the air run out.
    _scratch(mix, b + ST.T_A[0] + 0.05, b + ST.T_A[1] - 0.05, 0.035, 204, pan=0.0)            # a faint a
    # the pencil up, not moving: nothing
    _letters(mix, b + ST.T_L2[0], b + ST.T_L2[1], 6, 0.08, 205, 0.0)                          # little
    _letters(mix, b + ST.T_L2B[0], b + ST.T_L2B[1], 7, 0.08, 206, 0.0)                        # uncomfy
    mix.whoosh(b + ST.T_WHIP[0], 0.4, 0.03, 0.0)                # eyes up to the plate she did not pick
    mix.whoosh(b + ST.T_WHIP[2], 0.4, 0.03, 0.0)                # and down
    _letters(mix, b + ST.T_L3[0], b + ST.T_L3[1], 11, 0.075, 207, 0.0)                        # it is not wet.
    _tick(mix, b + ST.T_L3[1] - 0.02, 0.05, 0.0)                # the stop, with its tail

    # --- the pass, left again
    _paper(mix, T_PASS2 - 0.05, 1.0, 0.16, 0.5, to=-0.4)
    mix.whoosh(T_PASS2 + WHIP2[0], 0.46, 0.05, 0.0)
    _creak(mix, T_PASS2 + 0.5, T_PASS2 + 0.95, 210, 160, 0.04, 0.4)

    # --- III. N. (rust): a blunt soft pencil, a broad scrape
    c = C
    soft = dict(lo=700, hi=3600)
    _paper(mix, c + SR.T_SWING[0], 0.6, 0.09, -0.2)             # one hand swings the sheet square
    _letters(mix, c + SR.T_N[0], c + SR.T_N[1], 3, 0.1, 301, -0.05, fill=(0.8, 0.95), **soft)     # a tall N, three strokes
    _drag(mix, c + SR.T_SCR[0], c + SR.T_SCR[1], 0.12, 7, -0.05, lo=600, hi=3200, rate=5.5)       # the button, round and round, pressed
    _letters(mix, c + SR.T_X[0], c + SR.T_X[1], 2, 0.06, 302, -0.05, fill=(0.8, 0.95), lo=1500, hi=6000)   # two long light strokes
    mix.whoosh(c + SR.T_DIVE[0], 1.0, 0.07, 0.0)                # into the blackened button
    mix.whoosh(c + SR.T_GLASS[0] + 0.3, 0.9, 0.06, 0.0)         # out through the glass
    _bubbles(mix, c + SR.T_GLASS[0] + 0.7)
    mix.whoosh(c + SR.T_TURN[0], 1.2, 0.06, -0.3)               # the swing round in the water
    mix.whoosh(c + SR.T_IN[0], 0.9, 0.06, 0.0)                  # back in through the small round glass
    _bubbles(mix, c + SR.T_IN[0] + 0.35, 3, 0.05, 0.1)
    mix.whoosh(c + SR.T_UP[0], 0.8, 0.06, 0.0)
    _letters(mix, c + SR.T_L4A[0], c + SR.T_L4A[1], 15, 0.1, 310, -0.05, **soft)                  # the fish swim next
    _letters(mix, c + SR.T_L4B[0], c + SR.T_L4B[1], 19, 0.1, 330, 0.0, fill=(0.7, 0.92), **soft)  # to astronat looking th
    _drag(mix, c + SR.T_OFF[0], c + SR.T_OFF[1] + 0.25, 0.08, 9, 0.2, lo=700, hi=3600, rate=11.0, to=0.95)   # on, off the paper's edge
    mix.thud(c + SR.T_STILL - 0.06, 150, 0.035, -0.1, 0.1)      # the heel of the hand comes down at ending 5
    # N11: nothing. The pencil does not come down.

    # --- IV. the ending
    _creak(mix, E + 0.2, E + 1.0, 160, 240, 0.05, 0.0)          # standing up out of the seat
    for k, pan in enumerate((0.0, 0.2, 0.6, 0.7, -0.4)):        # five flat hands come to rest round the sheet
        mix.step(E + E_HANDS[1] - 0.2 + 0.045 * k, 0.03, pan, "wood")
    mix.whoosh(E + E_RISE[0], 3.2, 0.035, 0.0)                  # up and away
    _creak(mix, E + 7.0, E + 7.7, 170, 230, 0.04, 0.5)          # one chair, somewhere
    # the die is in the cup. Nothing rolls.
    mix.L *= 2.0                               # the desk is the film: pencil and paper sit above the beds
    mix.R *= 2.0
    _beds(mix)


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "m25"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            cols = 4
            tw, th = W // 2, H // 2
            rows = (len(ims) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 22))
            for i, im in enumerate(ims):
                sheet.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
            sheet.save(d / "sheet.png")
            print("sheet ->", d / "sheet.png")
