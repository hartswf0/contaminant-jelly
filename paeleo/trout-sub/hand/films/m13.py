"""m13 · the MAKING film for porthole 13 · Arch · "Bell Boulder arch with brass twig-bell".

Not what the children wrote (that is c13) but the writing of it: one Porthole Log passing through three children
(see swarm/m13/board.md for the traces of working that are really on the sheet, and where each is shown).

   0.0 .. 31.0   the pilot, S. (rust): page 1                      swarm/m13/scene_pilot.py
  31.0 .. 32.0   THE PASS, left: the page lands upside down        (this file)
  32.0 .. 56.5   the first friend, A. (teal): Turkey's seat        swarm/m13/scene_turkey.py
  56.5 .. 57.5   THE PASS, left again: the page lands a quarter turn round
  57.5 .. 79.0   the next friend, M. (plum): the river, and six empty lines     swarm/m13/scene_trout.py
  79.0 .. 90.0   the ending (this file): the eye comes up off M.'s shoulder to straight above the desk; three pairs
                 of hands round one sheet; the cup with the die in it; cam.rise to the whole room; nobody throws.

The joins are the PASS of the sheet: a cam.whip to the left (the sheet says "Pass your paper left") from the last
frame of the child who lets go to the desk of the child who takes it, the page arriving turned, the giver's hand
still on its edge, and the eye rolling level clockwise (the porthole's rule, Clockwise Etiquette: no roll in this
film ever goes the other way).

Sound is synthesized with the kit's Mix: one scratch a letter, a slower harder scratch for a letter gone over, the
rubber, paper on the flips and the passes, a chair, a room of children far off under every desk shot, water and a
low drone only inside a thought (dull and close inside the tin; water alone in the river), and nothing at all
while a child is stuck.

Foraged: only what c13's world carries (the Audubon turkey, the Denton trout: credits/m13.json). Everything else
is handmade in code: people.py, cam.py, the pencil lettering.

  python3 films/m13.py                      -> assets/films/m13.mp4 (+ .webp poster)
  python3 films/m13.py --stills 3 7.8 ...   -> films/stills/m13/*.png and sheet.png
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
sys.path.insert(0, str(HERE / "swarm" / "c13"))

from kit import Film, Mix  # noqa: E402
import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c13 world; not edited)

M13 = HERE / "swarm" / "m13"


def _load(name, path):
    """The m13 scene modules share file names with c13's, so they are loaded by path, not by import."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SR = _load("m13_scene_trout", M13 / "scene_trout.py")
ST = SR.T                                     # the same instance the trout scene takes A.'s column and desk from
SP = _load("m13_scene_pilot", M13 / "scene_pilot.py")

W, H = 960, 540
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp
key = cam.key

PASS = 1.0
T_PASS1 = SP.SECONDS                          # 31.0
T_TURKEY = T_PASS1 + PASS                     # 32.0
T_PASS2 = T_TURKEY + ST.SECONDS               # 56.5
T_TROUT = T_PASS2 + PASS                      # 57.5
T_END = T_TROUT + SR.SECONDS                  # 79.0
END_SECONDS = 11.0
SECONDS = T_END + END_SECONDS                 # 90.0
assert abs(SECONDS - 90.0) < 1e-6

# The children's sentences in the sheet's `reads` spelling, said once each when the line is finished. Absolute
# times, one at a time, each 2.5 s or more. Nothing else is captioned: M. wrote nothing, and nothing is said.
CAPTIONS = [(a, b, s) for a, b, s in SP.CAPTIONS] + \
           [(T_TURKEY + a, T_TURKEY + b, s) for a, b, s in ST.CAPTIONS] + \
           [(T_TROUT + a, T_TROUT + b, s) for a, b, s in SR.CAPTIONS]
CAPTIONS = [(round(a, 3), round(b, 3), s) for a, b, s in CAPTIONS]
for a, b, _ in CAPTIONS:
    assert b - a >= 2.5 - 1e-9, (a, b)
for (a, b, _), (c, d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert c >= b - 1e-9, (b, c)
assert len(CAPTIONS) == 6 and CAPTIONS[-1][1] <= T_PASS2

WOOD = ST.WOOD
S2 = ST.SIZE                                  # the sheet on A.'s and M.'s desk plane (1520 x 1960)


# ------------------------------------------------------------ the passes ---
WHIP = (0.10, 0.56)                           # of the pass second: the lens tears left after the sheet
LET_GO = 0.60                                 # the giver's thumb comes off the edge
ROLL = (0.30, 1.0)                            # the eye rolls level, clockwise, into the next child's first frame


@lru_cache(None)
def _pilot_last():
    return cam.fit(SP.frame(SP.SECONDS - 1e-3))


@lru_cache(None)
def _turkey_last():
    return cam.fit(ST.frame(ST.SECONDS - 1e-3))


def _giver(fr, v, at, tone, e):
    """The hand that gave: on the sheet's near edge while it lands, then off it, lifted, and away to the right."""
    x, y = v.dpt(*at)
    k = v.hs((760, 980), 1.0)
    if e < LET_GO:
        P.hand(fr, x, y, pose="pass", tone=tone, scale=k, t=0.0, arm=8, edge=96)
    else:
        g = cam.smooth(ramp(e, LET_GO, 0.97))
        P.hand(fr, x + 70 + 560 * g * g, y + 10 - 30 * g, pose="hold", tone=tone, scale=k, t=0.0, arm=8, lift=6 + 14 * g)


def _landing(desk, rot1, zoom1, e):
    """The new desk, not level yet. At e = 1 this is exactly the next module's frame(0.0)."""
    s = 1 - ease(e, *ROLL)
    return cam.shoot([(desk, 1.0)], rot=rot1 - 9 * s, zoom=zoom1 + 0.10 * s, bg=WOOD)


def _pass_to_a(e):
    """S. -> A. The sheet lands upside down: the pilot's three lines cannot be read, the two fish can."""
    fr = ST.desk_frame(0.0)
    if e < 0.985:
        _giver(fr, ST.view(0.0), (ST.SC[0] + S2[0] / 2 - 4, ST.SC[1] + 250), "rust", e)
    b = _landing(fr, -7.0, 1.06, e)
    return cam.whip(_pilot_last(), b, ramp(e, *WHIP), direction=-1)


def _pass_to_m(e):
    """A. -> M. The sheet lands a quarter turn round, A.'s full column nearest the new child."""
    fr = SR.desk_frame(0.0)
    if e < 0.985:
        _giver(fr, SR.view(0.0), (ST.SC[0] + S2[1] / 2 - 4, ST.SC[1] + 200), "teal", e)
    b = _landing(fr, -6.0, 1.05, e)
    return cam.whip(_turkey_last(), b, ramp(e, *WHIP), direction=-1)


# ------------------------------------------------------------ the ending ---
E_TILT = (0.0, 1.5)                           # E1: up off the shoulder to straight above the desk
E_HANDS = (0.55, 1.45)                        # the other two pairs of hands come to the sheet
E_RISE = (1.9, 5.6)                           # E2: the crane; the room is exactly the frame from 5.6 on
EXT = 2000                                    # the desk plane is widened by this much on each side (the room's desks
EDESK = (ST.DESK_SIZE[0] + 2 * EXT, ST.DESK_SIZE[1])     # are wider than they are deep), symmetrically, so the join holds
ESO = (ST.SO[0] + EXT, ST.SO[1])
ESC = (ST.SC[0] + EXT, ST.SC[1])
TOP_Z = 0.22                                  # screen px per desk px, straight above
TOP_AT = (270.0, 300.0)                       # where the sheet's centre sits then
END_KEYS = [(0.0, SR.STILL), (E_TILT[1], (0.0, math.log(TOP_Z * ST.S), S2[0] / 2, S2[1] / 2, TOP_AT[0], TOP_AT[1]))]

_LAY = P.room_layout((W, H))
_M = S2[0] * TOP_Z / 36.0                     # frame px per room px: the sheet is 36 wide on the room's desks
HERO_BOX = (_LAY["sheet"][0] - TOP_AT[0] / _M, _LAY["sheet"][1] - TOP_AT[1] / _M,
            _LAY["sheet"][0] + (W - TOP_AT[0]) / _M, _LAY["sheet"][1] + (H - TOP_AT[1]) / _M)
_CUP_D = ((_LAY["cup"][0] - _LAY["sheet"][0]) * _M / TOP_Z, (_LAY["cup"][1] - _LAY["sheet"][1]) * _M / TOP_Z)
CUP_AT = (ESC[0] + _CUP_D[0], ESC[1] + _CUP_D[1])        # desk-plane px: where the room has it, beside the sheet
CUP_SCALE = 0.30 * _M / TOP_Z


class EView:
    """scene_turkey's View on the widened plane (same hinge line, same lens: the first frame is M.'s last)."""

    def __init__(self, deg, zoom, at, to):
        self.deg, self.z = deg, zoom / ST.S
        p0 = cam.tilt_point(ESO[0] + at[0], ESO[1] + at[1], deg, ST.HOR, self.z, ST.F, (0, 0), EDESK)
        self.shift = (to[0] - p0[0], to[1] - p0[1])

    def dpt(self, x, y):
        return cam.tilt_point(x, y, self.deg, ST.HOR, self.z, ST.F, self.shift, EDESK)

    def pt(self, p):
        return self.dpt(ESO[0] + p[0], ESO[1] + p[1])

    def ls(self, p):
        a, b = self.pt(p), self.pt((p[0] + 20, p[1]))
        return math.hypot(b[0] - a[0], b[1] - a[1]) / 20 * ST.S

    def hs(self, p, k=1.0):
        ls = self.ls(p)
        return ls / 1.26 * 1.02 * k * lerp(1.0, 0.74, clamp((ls - 0.7) / 0.9))

    def render(self, desktop):
        return cam.tilt(desktop, self.deg, ST.HOR, self.z, ST.F, self.shift, bg=WOOD, shadow=0)


def _eview(e):
    deg, lz, ax, ay, tx, ty = key(e, END_KEYS, "smoother")
    return EView(deg, math.exp(lz), (ax, ay), (tx, ty))


@lru_cache(None)
def _page_done():
    return SR.page2(SR.SECONDS).convert("RGB")


@lru_cache(None)
def _end_plane():
    """M.'s desk, wider: page 2 as the film leaves it (A.'s column full, M.'s white), and the cup with the die in it."""
    d = ST._desk_plane()
    flip = d.transpose(Image.FLIP_LEFT_RIGHT)
    im = Image.new("RGB", EDESK, WOOD)
    im.paste(flip.crop((d.size[0] - EXT, 0, d.size[0], d.size[1])), (0, 0))
    im.paste(d, (EXT, 0))
    im.paste(flip.crop((0, 0, EXT, d.size[1])), (EXT + d.size[0], 0))
    P.lay(im, Image.new("RGB", S2, P.PAPER), ESC[0], ESC[1])
    im.paste(_page_done(), ESO)
    P.cup(im, CUP_AT[0], CUP_AT[1], scale=CUP_SCALE, die=True)
    return im


def _end_desk(e):
    """E1: the plum desk from M.'s last frame, the eye coming up; the other two children's hands come to the sheet."""
    e = min(e, E_RISE[0])
    v = _eview(e)
    fr = v.render(_end_plane())
    up = cam.smooth(ramp(e, 0.0, E_TILT[1]))
    big = lerp(1.0, 1.75, up)                 # from straight above the hands are cut a little larger, to be read
    ht = SR.T_STILL
    # M.: as she was left. The pencil lies where she put it; both hands flat.
    P.pencil(fr, *v.pt((1395, 1240)), angle=-64, scale=v.hs((1395, 1240), 1.0))
    go = cam.smooth(ramp(e, 0.35, E_TILT[1]))     # letting go: her hands slide down off the two columns
    lh = (lerp(150, 90, go), lerp(1330, 1730, go))
    rh = (lerp(SR.FLAT[0], 1260, go), lerp(SR.FLAT[1], 1690, go))
    P.hand(fr, *v.pt(lh), pose="hold", tone="plum", scale=v.hs(lh, big), flip=True, t=ht, arm=140)
    P.hand(fr, *v.pt(rh), pose="hold", tone="plum", scale=v.hs(rh, big), t=ht, arm=56)
    g = cam.smooth(ramp(e, *E_HANDS))
    if g > 0:
        off = 1 - g
        # A., from the left: two hands resting at the sheet's left edge
        for (x, y), flip, arm in (((-70, 640), False, 196), ((-90, 1080), True, 168)):
            q = v.pt((x - 900 * off, y))
            P.hand(fr, q[0], q[1], pose="hold", tone="teal", scale=v.hs((x, y), big), flip=flip, t=0.0, arm=arm, lift=12 * off)
        # S., from across the desk: one hand flat, one taking the sheet's corner ("Give it back to the pilot")
        q = v.pt((420, 200 - 800 * off))
        P.hand(fr, q[0], q[1], pose="hold", tone="rust", scale=v.hs((420, 200), big), flip=True, t=0.0, arm=262, lift=12 * off)
        q = v.pt((1180, 2 - 800 * off))
        if off < 0.03:
            P.hand(fr, q[0], q[1], pose="pass", tone="rust", scale=v.hs((1180, 2), big), t=0.0, arm=282, edge=0)
        else:
            P.hand(fr, q[0], q[1], pose="hold", tone="rust", scale=v.hs((1180, 2), big), t=0.0, arm=282, lift=12 * off)
    hy = key(e, [(0.0, 712.0), (0.8, 1010.0)], "in")
    if hy < 900:
        P.head_back(fr, 232.0, hy, "plum", 1.15, hair=SR.HAIR, t=SR.SECONDS)
    return fr


@lru_cache(None)
def _end_top():
    return _end_desk(E_RISE[0])


@lru_cache(None)
def _small_page():
    return _page_done().resize((380, 490), Image.LANCZOS)


_room_cache = {}


def _room(e):
    k = int(e * 12)
    if k not in _room_cache:
        if len(_room_cache) > 3:
            _room_cache.clear()
        im = Image.new("RGB", (W, H), (0, 0, 0))
        P.classroom(im, k / 12.0, sheets={P.HERO: _small_page()}, cup_at="hero")
        _room_cache[k] = im
    return _room_cache[k]


_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_FEATHER = 1 - np.clip(np.minimum(np.minimum(_xx, W - 1 - _xx), np.minimum(_yy, H - 1 - _yy)) / 110.0, 0, 1) ** 1.5


def _ending(e):
    if e < E_TILT[1]:
        return _end_desk(e)
    if e < E_RISE[0]:                         # straight above: three pairs of hands, one sheet, the cup. A breath.
        return _end_top()
    u = ramp(e, *E_RISE)
    room = _room(e)
    if u >= 1:
        return room
    a = _end_top()
    # the desk we sat at settles into its place among the twenty: its edges first (so no rectangle hangs in the
    # air), the sheet, the hands and the cup last
    edge, mid = cam.smooth((u - 0.04) / 0.26), cam.smooth((u - 0.42) / 0.36)
    if edge > 0.004:
        box = tuple(int(round(c)) for c in HERO_BOX)
        m = (mid + (edge - mid) * _FEATHER) * 255.0
        a = Image.composite(room.crop(box).resize((W, H), Image.BICUBIC), a, Image.fromarray(m.astype(np.uint8), "L"))
    return cam.rise(a, room, u, box=HERO_BOX, tip=26, sway=5)


# ---------------------------------------------------------------- film ---
film = Film("m13", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + 6.6               # Turkey's seat: the pilot's two fish outside the glass


def picture(t):
    if t < T_PASS1:
        return SP.frame(t)
    if t < T_TURKEY:
        return _pass_to_a(t - T_PASS1)
    if t < T_PASS2:
        return ST.frame(t - T_TURKEY)
    if t < T_TROUT:
        return _pass_to_m(t - T_PASS2)
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


def _letters(mix, a, b, n, gain=0.07, seed=0, pan=0.1):
    """One scratch a letter, a little uneven, with the lifts between."""
    n = max(1, int(n))
    slot = (b - a) / n
    rs = np.random.RandomState(seed)
    for k in range(n):
        s = a + slot * k + rs.uniform(0, 0.12) * slot
        _scratch(mix, s, s + slot * rs.uniform(0.62, 0.86), gain * rs.uniform(0.8, 1.15), seed + k, pan=pan)


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
    """A sheet sliding over a desk top, or turned over."""
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


def _envelope(n, rate, keys):
    keys = sorted(keys, key=lambda k: k[0])
    tt = np.arange(n) / rate
    return np.interp(tt, [k[0] for k in keys], [k[1] for k in keys])


def _gate(spans, on=1.0, off=0.0, fade=0.12, lead=0.0):
    """Envelope keys: `off` inside each (a, b) span, `on` outside."""
    keys = [(0.0, on)]
    for a, b in spans:
        keys += [(a - lead - fade, on), (a - lead, off), (b, off), (b + fade, on)]
    return keys + [(SECONDS, on)]


B_, C, E = T_TURKEY, T_TROUT, T_END
# away from the desk, inside the thought: the room is gone
AWAY = [(SP.DIVE_IN[0] + 0.5, SP.DIVE_OUT[1] - 0.4),                    # the pilot's river
        (B_ + 2.5, B_ + 7.8),                                            # the tin, and the look out
        (C + SR.T_DIVE[0] + 0.5, C + SR.T_UP[1] - 0.4)]                  # the tin, the river, and back
# stuck: the desk is there and nothing moves. Nothing sounds either.
STUCK = [(22.0, 22.8), (25.4, 25.88), (28.22, 29.0),                     # S. under each question; and before "the"
         (B_ + ST.T_STUCK[0], B_ + ST.T_STUCK[1]), (B_ + ST.T_WAIT[0], B_ + ST.T_WAIT[1]),     # no room; the wait before the dot
         (C + SR.T_HANG[0], C + SR.T_HANG[1]),                           # between the two plates
         (C + SR.T_SINK[0] - 0.25, C + SR.T_SINK[3] + 0.15)]             # the point sinks, nearly touches, comes up
# a small look into a thought, over the desk: the room dips, a little water
LOOKS = [(SP.TH2[0][0], SP.TH2[-1][0]), (SP.TH3[0][0], SP.TH3[-1][0]),
         (B_ + ST.TH1[0], B_ + ST.TH1[-1]), (B_ + ST.TH2[0], B_ + ST.TH2[-1]), (B_ + ST.TH3[0], B_ + ST.TH3[-1])]
TIN = [(B_ + 2.7, B_ + 7.6), (C + SR.T_DIVE[0] + 0.6, C + SR.T_GLASS[0] + 0.5), (C + SR.T_IN[1] - 0.3, C + SR.T_UP[1] - 0.5)]
RIVER = [(SP.DIVE_IN[0] + 0.6, SP.DIVE_OUT[1] - 0.5), (C + SR.T_GLASS[0] + 0.5, C + SR.T_IN[1] - 0.3)]
NO_DRONE = [(C + SR.T_TURN[1] - 0.3, C + SR.T_RIVER[1] + 0.2)]          # M7: water and nothing else


def _mul(n, rate, *key_sets):
    env = np.ones(n)
    for ks in key_sets:
        env = env * _envelope(n, rate, ks)
    return env


def _beds(mix):
    n, rate = mix.n, mix.rate
    # a room of children, far off: air, voices too far away to be words, other people's pencils, a chair leg
    room = Mix(SECONDS, seed=31)
    room.room(0.0, SECONDS, 0.05, hum=60)
    rs = np.random.RandomState(13)
    t = 0.3
    while t < SECONDS - 2.5:
        d = rs.uniform(1.0, 2.6)
        room.murmur(t, d, gain=rs.uniform(0.012, 0.03), pitch=rs.uniform(230, 340), pan=rs.uniform(-0.9, 0.9), seed=int(t * 10))
        if rs.rand() < 0.35:
            room.step(t + rs.uniform(0.2, 1.0), rs.uniform(0.01, 0.025), rs.uniform(-0.9, 0.9), "wood")
        if rs.rand() < 0.5:                   # somebody else is writing
            a = t + rs.uniform(0.0, 1.0)
            _letters(room, a, a + rs.uniform(0.6, 1.4), rs.randint(4, 9), 0.03, int(t * 7), rs.uniform(-0.9, 0.9))
        t += rs.uniform(0.9, 2.2)
    for ch in (room.L, room.R):               # far off: nothing bright gets here
        ch[:] = room.lowpass(ch, 1500)
    room.reverb(0.5, 1.6)
    level = [(0.0, 1.0), (C + SR.T_STILL - 0.3, 1.0), (C + SR.T_STILL + 0.4, 1.3), (E + 0.2, 1.3), (E + 1.2, 1.0),
             (E + E_RISE[0], 1.0), (E + E_RISE[1], 1.6), (SECONDS - 0.6, 1.6), (SECONDS, 0.0)]
    env = _mul(n, rate, level, _gate(AWAY, fade=0.5), _gate(STUCK, fade=0.14), _gate(LOOKS, off=0.5, fade=0.3))
    mix.L += room.L * env
    mix.R += room.R * env
    # open water and a low drone: the thought, and the river
    wat = Mix(SECONDS, seed=32)
    wat.water(0.0, SECONDS, 0.085)
    env = np.maximum(_envelope(n, rate, _gate(RIVER, on=0.0, off=1.0, fade=0.5)),
                     _envelope(n, rate, _gate(LOOKS, on=0.0, off=0.4, fade=0.3)))
    mix.L += wat.L * env
    mix.R += wat.R * env
    # inside the tin the water is dull and close
    tin = Mix(SECONDS, seed=33)
    tin.water(0.0, SECONDS, 0.12)
    for ch in (tin.L, tin.R):
        ch[:] = tin.lowpass(ch, 520)
    env = _envelope(n, rate, _gate(TIN, on=0.0, off=1.0, fade=0.45))
    mix.L += tin.L * env
    mix.R += tin.R * env
    dr = Mix(SECONDS, seed=34)
    dr.drone(0.0, SECONDS, (55, 82.5, 110), 0.04, attack=0.1, release=0.1)
    env = np.maximum(_envelope(n, rate, _gate(RIVER + TIN, on=0.0, off=1.0, fade=0.5)),
                     _envelope(n, rate, _gate(LOOKS, on=0.0, off=0.4, fade=0.3)))
    env = env * _envelope(n, rate, _gate(NO_DRONE, fade=0.6))
    mix.L += dr.L * env
    mix.R += dr.R * env


def _desk_sounds(desk):
    """Everything a hand does at a desk. Laid on its own track so that it stops when the eye leaves the desk."""
    # --- I. the pilot, S.
    pan = 0.12
    for i, a in enumerate(SP.ACTS):
        t0, t1 = max(a.t0, 0.0), a.t1
        if t1 <= 0.05:
            continue
        kind = type(a).__name__
        if kind == "Write":
            _letters(desk, t0, t1, a.plan.letters(1.0), 0.05 + 0.03 * a.weight, 100 + 17 * i, pan)
        elif kind == "Lines":
            if a.weight >= 1.2:
                _go_over(desk, t0, t1, 0.11, 100 + 17 * i, pan)               # the f, gone over twice
            else:
                _letters(desk, t0, t1, max(1, round((t1 - t0) / 0.13)), 0.04 + 0.035 * a.weight, 100 + 17 * i, pan)
        elif kind == "Rub":
            _rubber(desk, t0, t1, 0.06 + 0.04 * a.strength, pan)
    for g, t0, t1 in SP.DRAW_WIN:                                             # the drawing in the ring
        _letters(desk, t0, t1, max(2, round((t1 - t0) / 0.17)), 0.07, 400 + int(t0 * 10), pan)
    _creak(desk, 0.9, 1.8, 150, 210, 0.05, -0.2)                              # settling back into the seat
    _paper(desk, 1.55, 0.3, 0.035, 0.1)                                       # crumbs brushed
    _tick(desk, 1.85, 0.06, 0.2)                                              # the pencil turned round
    _tick(desk, 4.58, 0.05, 0.2)
    _paper(desk, 12.5, 0.4, 0.05, 0.1)                                        # the side of the hand brushes the crumbs off
    desk.whoosh(SP.WHIP_OUT[0], 0.35, 0.04, 0.4)                              # eyes to the slip, and back
    desk.whoosh(SP.WHIP_BACK[0], 0.35, 0.04, -0.2)
    _paper(desk, SP.FLIP[0], 0.45, 0.11, -0.1)                                # the sheet turned over to find "Bell-ringer"
    _paper(desk, SP.FLIP[2] - 0.15, 0.45, 0.11, -0.1)                         # and back
    _tick(desk, 30.84, 0.09, 0.3)                                             # the pencil laid down
    desk.thud(30.84, 210, 0.05, 0.3, 0.06)

    # --- II. the first friend, A.
    b = B_
    _paper(desk, b + 0.15, 1.0, 0.09, -0.1)                                   # turned to face her
    _tick(desk, b + 1.3, 0.06, 0.1)                                           # the pencil taken up
    _paper(desk, b + 8.25, 0.6, 0.12, 0.0)                                    # turned over
    desk.thud(b + 8.85, 180, 0.05, 0.0, 0.08)
    _go_over(desk, b + ST.T_A[0], b + ST.T_A[1], 0.1, 201, 0.0)               # one firm capital
    _letters(desk, b + ST.T_OVAL[0], b + ST.T_OVAL[1], 2, 0.08, 202, 0.0)     # the small leaning oval
    _letters(desk, b + ST.T_THE[0], b + ST.T_THE[1], 3, 0.075, 203, 0.0)
    _scratch(desk, b + ST.T_D[0], b + ST.T_D[1], 0.08, 204, pan=0.0)
    _go_over(desk, b + ST.T_DOVER[0], b + ST.T_DOVER[1], 0.11, 205, 0.0)      # the capital D, gone over
    _letters(desk, b + ST.T_INNER[0], b + ST.T_INNER[1], 9, 0.075, 206, 0.0)
    _letters(desk, b + ST.T_B1B[0], b + ST.T_B1B[1], 7, 0.075, 207, 0.0)
    _letters(desk, b + ST.T_B2A[0], b + ST.T_B2A[1], 17, 0.075, 208, 0.0)
    _letters(desk, b + ST.T_OF[0], b + ST.T_OF[1], 2, 0.075, 209, -0.2)       # "of", out in the margin
    _letters(desk, b + ST.T_B2B[0], b + ST.T_B2B[1], 18, 0.075, 210, 0.0)
    _scratch(desk, b + ST.T_YTAIL[0], b + ST.T_YTAIL[1] + 0.08, 0.1, 211, pan=0.2)   # the tail of the y, down the gutter
    _tick(desk, b + ST.T_TOUCH[0] + 0.25, 0.05, 0.2)                          # the point touches "crazy"
    _letters(desk, b + ST.T_B3A[0], b + ST.T_B3A[1], 14, 0.075, 212, 0.0)
    _letters(desk, b + ST.T_B3B[0], b + ST.T_B3B[1], 7, 0.075, 213, 0.0)
    _scratch(desk, b + ST.T_DOT[0], b + ST.T_DOT[1], 0.16, 214, lo=900, hi=4200, pan=0.2)   # the one full stop
    desk.thud(b + ST.T_DOT[1] - 0.02, 160, 0.1, 0.2, 0.08)
    _tick(desk, b + 22.0, 0.08, -0.1)                                         # the pencil in the groove
    _paper(desk, b + 23.3, 1.1, 0.07, 0.0)                                    # the sheet starts left

    # --- III. the next friend, M.
    c = C
    _paper(desk, c + 0.1, 0.9, 0.09, 0.0)                                     # squared up
    _tick(desk, c + 1.05, 0.06, 0.1)
    _letters(desk, c + SR.T_M[0], c + SR.T_M[1], 3, 0.07, 301, 0.1)           # one loopy lower-case letter
    _letters(desk, c + SR.T_ON[0], c + SR.T_ON[1], 5, 0.06, 302, 0.2)
    _scratch(desk, c + SR.T_SAG[0], c + SR.T_SAG[1] + 0.1, 0.035, 303, pan=0.1)      # lightly, under "but it fits"
    _scratch(desk, c + SR.T_DASH[0], c + SR.T_DASH[1] + 0.05, 0.03, 304, pan=0.2)
    _paper(desk, c + SR.T_FLIP1[0] + 0.05, 0.6, 0.12, 0.0)                    # over, to find the pilot's picture
    _paper(desk, c + SR.T_FLIP2[0], 0.55, 0.12, 0.0)                          # and back
    _creak(desk, c + SR.T_STILL + 1.0, c + SR.T_STILL + 1.6, 210, 170, 0.035, -0.6)   # somebody else's chair
    _tick(desk, c + SR.T_FLAT + 0.12, 0.06, 0.3)                              # the pencil put down. Not a word.
    desk.thud(c + SR.T_FLAT + 0.2, 170, 0.04, 0.1, 0.07)                      # the flat of the hand


@film.sound
def sound(mix):
    _beds(mix)
    desk = Mix(SECONDS, seed=41)
    _desk_sounds(desk)
    env = _mul(desk.n, desk.rate, _gate(AWAY, fade=0.25), _gate(STUCK, fade=0.05))
    mix.L += desk.L * env
    mix.R += desk.R * env

    # --- the moves of the eye
    mix.whoosh(SP.DIVE_IN[0], 1.1, 0.07, 0.0)                                 # down through the drawn ring
    mix.whoosh(SP.DIVE_OUT[0], 1.0, 0.06, 0.0)
    b = B_
    mix.whoosh(b + 2.0, 1.1, 0.07, 0.0)                                       # through the page's porthole, into the tin
    mix.thud(b + 3.05, 70, 0.16, 0.0, 0.3)                                    # landed
    mix.whoosh(b + 3.1, 1.3, 0.05, 0.3)                                       # round to the right
    at = b + ST.T4 + ST.BELL_TIP[0] + 0.3                                     # the bell tips once: one small note, through tin
    bell = Mix(3.0, seed=42)
    bell.bell(0.0, 784, 2.4, 0.3)
    mix.add(mix.lowpass(bell.L, 1800), at, 0.22, 0.25)
    mix.click(b + ST.T4 + ST.DISC[1], 0.05, 0.2, 2400, 0.03)                  # the red disc settles on its dome
    mix.whoosh(b + 7.2, 1.0, 0.06, 0.0)
    c = C
    mix.whoosh(c + SR.T_DIVE[0], 1.1, 0.07, 0.0)
    mix.whoosh(c + SR.T_GLASS[0] + 0.3, 0.9, 0.06, 0.0)                       # out through the glass
    for k in range(4):                                                        # a few bubbles off the rim
        tt = mix.t(0.16)
        fr = (380 + 60 * k) * (1 + 0.9 * (tt / 0.16) ** 1.6)
        mix.add(np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7, c + SR.T_GLASS[0] + 0.75 + 0.1 * k,
                0.07, -0.3 + 0.2 * k)
    mix.whoosh(c + SR.T_TURN[0], 1.3, 0.06, 0.3)                              # round, in the water
    # M7: water. Nothing comes.
    mix.whoosh(c + SR.T_IN[0], 1.0, 0.06, 0.0)
    mix.whoosh(c + SR.T_UP[0], 0.9, 0.06, 0.0)

    # --- the passes, left
    for at, pan_c in ((T_PASS1, -0.4), (T_PASS2, 0.4)):
        _paper(mix, at - 0.25, 1.0, 0.16, 0.5, to=-0.4)
        mix.whoosh(at + WHIP[0], 0.5, 0.06, 0.0)
        mix.thud(at + LET_GO, 190, 0.05, 0.4, 0.07)                           # it lands
        _creak(mix, at + 0.62, at + 1.05, 230, 170, 0.045, pan_c)             # the next child leans in

    # --- the ending
    _creak(mix, E + 0.15, E + 0.9, 160, 240, 0.05, 0.0)                       # up off the shoulder
    for k, pan in enumerate((-0.6, -0.5, 0.1, 0.3)):                          # four more hands come to the sheet
        mix.step(E + E_HANDS[1] - 0.2 + 0.05 * k, 0.03, pan, "wood")
    _paper(mix, E + E_HANDS[1] - 0.05, 0.35, 0.05, 0.3)                       # a thumb on its corner
    mix.whoosh(E + E_RISE[0] + 0.2, 3.0, 0.035, 0.0)                          # up and away
    _creak(mix, E + 8.4, E + 9.1, 170, 230, 0.05, 0.5)                        # one chair
    # the die is in the cup. Nothing rolls.


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "m13"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            cols = 4
            sheet = Image.new("RGB", (cols * 480, ((len(ims) + cols - 1) // cols) * 270), (20, 20, 24))
            for i, (t, im) in enumerate(zip(times, ims)):
                im = im.convert("RGB").resize((480, 270), Image.LANCZOS)
                ImageDraw.Draw(im).text((8, 6), f"{t:.2f}", fill=(255, 255, 0))
                sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
            sheet.save(d / "sheet.png")
            print("sheet ->", d / "sheet.png")
