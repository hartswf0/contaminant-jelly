"""m10 · the MAKING film for porthole 10 · PA · "Elementary brick: flapping Clam-Shell PA".

Not what the children wrote (that is c10) but the writing of it: one Porthole Log passing through three children
(see swarm/m10/board.md for the traces of working that are really on the sheet, and where each is shown).

   0.0 .. 32.0   the pilot (rust): page 1                         swarm/m10/scene_pilot.py
  32.0 .. 57.5   the first friend, M. (teal): Turkey's seat       swarm/m10/scene_turkey.py
  57.5 .. 81.5   the next friend, S. (plum): the trout's seat     swarm/m10/scene_trout.py
  81.5 .. 91.5   the ending (this file): the sheet goes back to the pilot; zones 7 and 8 stay blank (a hand not
                 writing, held still); three pairs of hands round one sheet; cam.rise to the whole room; the die
                 in the cup, not thrown.

The joins are the PASS of the sheet: a cam.whip from the last frame of the child who lets go to the desk of the
child who takes it, the page arriving turned (sideways for M., upside down for S.) and the eye rolled with it.
Sound is synthesized with the kit's Mix: pencil per letter, a slower harder scratch for every letter gone over,
the rubber once, paper on the passes, a chair, a room of children far off under every desk shot, water and a low
drone only inside a thought, and nothing at all while a child is stuck.

Nothing is foraged (credits/m10.json is empty): c10's cut-paper world, people.py and cam.py, all handmade in code.

  python3 films/m10.py                      -> assets/films/m10.mp4 (+ .webp poster)
  python3 films/m10.py --stills 3 7.8 ...   -> films/stills/m10/*.png and sheet.png
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
sys.path.insert(0, str(HERE / "swarm" / "c10"))

from kit import Film, Mix  # noqa: E402
import cam  # noqa: E402
import people as P  # noqa: E402
import world as Wd  # noqa: E402   (the c10 world; not edited)

M10 = HERE / "swarm" / "m10"


def _load(name, path):
    """The m10 scene modules share file names with c10's, so they are loaded by path, not by import."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SR = _load("m10_scene_trout", M10 / "scene_trout.py")
ST = SR._turkey_module()                      # the same instance the trout scene takes M.'s column and desk from
assert ST, "scene_turkey.py did not load"
SP = _load("m10_scene_pilot", M10 / "scene_pilot.py")

W, H = 960, 540
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp
key = cam.key

T_TURKEY = SP.SECONDS                         # 32.0
T_TROUT = T_TURKEY + ST.SECONDS               # 57.5
T_END = T_TROUT + SR.SECONDS                  # 81.5
END_SECONDS = 10.0
SECONDS = T_END + END_SECONDS                 # 91.5
assert abs(SECONDS - 91.5) < 1e-6

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
assert len(CAPTIONS) == 9 and CAPTIONS[-1][1] <= T_END

PASS = 0.5                                    # a whip
BG = SR.BG


# ------------------------------------------------------------ the passes ---
@lru_cache(None)
def _pilot_last():
    return cam.fit(SP.frame(SP.SECONDS - 1e-3))


def _rolled(fr, rot):
    """The eye has not righted itself yet: the new desk seen rolled, as the module's next frame will show it."""
    return cam.shoot([(fr, 1.0)], rot=rot, zoom=1.05, bg=BG)


def _pass_to_m(u):
    """Pilot -> M. The sheet slides in sideways from the right; the lens whips left, as the sheet says."""
    return cam.whip(_pilot_last(), _rolled(ST.desk_frame(u), 9), ramp(u, 0.0, PASS), direction=-1)


def _pass_to_s(u):
    """M. -> S. The sheet lands upside down."""
    return cam.whip(SR.m_desk(), _rolled(SR.desk_frame(u), -8), ramp(u, 0.0, PASS), direction=-1)


# ------------------------------------------------------------ the ending ---
E_STILL = (0.5, 4.0)                          # E2: locked, nothing breathes
E_MOVE = (2.1, 2.7)                           # the lifted point goes from "I rolled ____" to the newspaper's first rule
E_HANDS = (3.25, 3.85)                        # the other two pairs of hands come to rest
E_RISE = (4.0, 8.0)                           # E3
S2 = SR.SIZE
CUP_AT = (SR.SO[0] + S2[0] + 170, SR.SO[1] + 1330)        # desk-plane px: beside the sheet, level with "Roll"
END_VIEW = SR._shot(56.0, 1.14, 860.0, 1500.0, 470.0, 262.0)
HERO_BOX = (385, 268, 577, 376)               # where this desk belongs in the room (16:9)


def _b2(name):
    return P.where(2, name, S2)


@lru_cache(None)
def _page_done():
    return SR.page2(1e6).convert("RGB")


@lru_cache(None)
def _end_plane():
    """The pilot's desk again: page 2 up, the right way round, all six endings on it; the cup with the die in it."""
    im = SR._desk_plane().copy()
    P.lay(im, _page_done(), SR.SC[0], SR.SC[1])
    P.cup(im, CUP_AT[0], CUP_AT[1], scale=3.3, die=True)
    return im


@lru_cache(None)
def _end_view():
    return SR.View(END_VIEW[0], math.exp(END_VIEW[1]), END_VIEW[2:4], END_VIEW[4:6])


@lru_cache(None)
def _end_ground():
    return _end_view().render(_end_plane())


def _end_desk(e):
    """The rust desk at ending second e: zones 7 and 8 as printed. The pencil is up. It does not come down."""
    v = _end_view()
    fr = _end_ground().copy()
    rl, ga = _b2("rolled.line"), _b2("ga.1")
    p0 = ((rl[0] + rl[2]) / 2 - 10, rl[3] - 4)
    p1 = (ga[0] + 420, ga[3] - 4)
    # the other two children: flat hands on the desk, from the left (teal) and from across (plum)
    g = ease(e, *E_HANDS)
    if g > 0:
        k = v.hs((760, 1300), 1.0)
        off = 1 - g
        for (x, y), flip in (((100, 1215), False), ((60, 1480), True)):
            q = v.dpt(SR.SO[0] + x - 420 * off, SR.SO[1] + y)
            P.hand(fr, q[0], q[1], pose="hold", tone="teal", scale=k * 0.96, flip=flip, t=0.0, arm=180, lift=14 * off)
        for (x, y), flip in (((560, 800), True), ((1040, 780), False)):
            q = v.dpt(SR.SO[0] + x, SR.SO[1] + y - 520 * off)
            P.hand(fr, q[0], q[1], pose="hold", tone="plum", scale=k * 0.9, flip=flip, t=0.0, arm=270, lift=14 * off)
    hp = (330, 1885)
    P.hand(fr, *v.pt(hp), pose="hold", tone="rust", scale=v.hs(hp), flip=True, t=0.0, arm=140)
    f = ease(e, *E_MOVE)
    p = (lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f) - 26 * math.sin(math.pi * f))
    P.hand(fr, *v.pt(p), pose="hover", tone="rust", scale=v.hs(p), t=0.0, lift=16, arm=58)
    P.head_back(fr, 742, 632, "rust", 1.15, hair="short", t=0.0)
    return fr


@lru_cache(None)
def _small_page():
    return _page_done().resize((380, 490), Image.LANCZOS)


_room_cache = {}


def _room(t):
    k = int(t * 12)
    if k not in _room_cache:
        if len(_room_cache) > 3:
            _room_cache.clear()
        im = Image.new("RGB", (W, H), (0, 0, 0))
        P.classroom(im, k / 12.0, sheets={P.HERO: _small_page()}, cup_at="hero")
        _room_cache[k] = im
    return _room_cache[k]


def _ending(e):
    if e < PASS:                              # E1: the pass back, to the right, the way it came
        return cam.whip(cam.fit(SR.frame(SR.SECONDS - 1e-3)), _end_desk(e), ramp(e, 0.0, PASS), direction=1)
    if e < E_RISE[0]:                         # E2: the blank
        return _end_desk(e)
    u = ramp(e, *E_RISE)
    room = _room(e)
    if u >= 1:
        return room
    a = _end_desk(e)
    melt = cam.smooth((u - 0.5) / 0.42)       # the desk we sat at melts into its place among the twenty
    if melt > 0.004:
        a = Image.blend(a, room.crop(HERO_BOX).resize((W, H), Image.BICUBIC), melt)
    return cam.rise(a, room, u, box=HERO_BOX, tip=26, sway=5)


# ---------------------------------------------------------------- film ---
film = Film("m10", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + 9.6               # Turkey's seat: the pilot's pencil jaw outside the glass


def picture(t):
    if t < T_TURKEY:
        return SP.frame(t)
    if t < T_TROUT:
        u = t - T_TURKEY
        return _pass_to_m(u) if u < PASS else ST.frame(u)
    if t < T_END:
        u = t - T_TROUT
        return _pass_to_s(u) if u < PASS else SR.frame(u)
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
    """A sheet sliding over a desk top."""
    n = int(seconds * mix.rate)
    tt = np.arange(n) / mix.rate
    x = mix.band(mix.noise(seconds), 700, 5200)[:n] * np.hanning(n) ** 0.5 * (0.75 + 0.25 * np.sin(2 * np.pi * 13 * tt))
    x = x + 0.35 * mix.band(mix.noise(seconds), 120, 500)[:n] * np.hanning(n)
    if to is None:
        mix.add(x, at, gain, pan)
    else:                                      # it travels across
        half = n // 2
        mix.add(x * np.linspace(1, 0, n), at, gain, pan)
        mix.add(x * np.linspace(0, 1, n), at, gain, to)
        del half


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
    tt = np.arange(n) / rate
    return np.interp(tt, [k[0] for k in keys], [k[1] for k in keys])


# when we are at a desk (1), away in a thought (0), or the child is stuck (0: the room falls away)
A, B_, C, E = 0.0, T_TURKEY, T_TROUT, T_END
ROOM_KEYS = [
    (0.0, 1.0), (6.0, 1.0), (6.6, 0.0), (10.5, 0.0), (11.1, 1.0),
    (14.6, 1.0), (14.9, 0.55), (16.1, 0.55), (16.4, 1.0),
    (21.4, 1.0), (21.9, 0.0), (26.0, 0.0), (26.5, 1.0),                       # P9: the long still hold
    (B_ + 6.0, 1.0), (B_ + 6.6, 0.0), (B_ + 11.9, 0.0), (B_ + 12.5, 1.0),
    (B_ + 15.0, 1.0), (B_ + 15.3, 0.0), (B_ + 17.0, 0.0), (B_ + 17.3, 1.0),   # T9: stuck
    (B_ + 17.31, 0.55), (B_ + 19.0, 0.55), (B_ + 19.3, 1.0),
    (C + 6.1, 1.0), (C + 6.6, 0.0), (C + 12.3, 0.0), (C + 12.8, 1.0),
    (C + 13.95, 1.0), (C + 14.03, 0.0), (C + 14.5, 0.0), (C + 14.62, 1.0),    # she looks across: nothing moves
    (C + 16.4, 1.0), (C + 16.7, 0.55), (C + 20.8, 0.55), (C + 21.2, 1.0),
    (E + 0.35, 1.0), (E + 0.7, 0.0), (E + 4.0, 0.0), (E + 6.5, 1.5), (SECONDS, 1.5),   # E2: the blank; then the room
]
WATER_KEYS = [
    (0.0, 0.0), (6.0, 0.0), (6.7, 1.0), (10.4, 1.0), (11.1, 0.0),
    (14.6, 0.0), (15.0, 0.4), (16.05, 0.4), (16.4, 0.0),
    (B_ + 6.0, 0.0), (B_ + 6.7, 1.0), (B_ + 11.8, 1.0), (B_ + 12.5, 0.0),
    (B_ + 17.3, 0.0), (B_ + 17.75, 0.4), (B_ + 18.9, 0.4), (B_ + 19.3, 0.0),
    (C + 6.1, 0.0), (C + 6.7, 1.0), (C + 12.2, 1.0), (C + 12.8, 0.0),
    (C + 16.4, 0.0), (C + 16.85, 0.4), (C + 18.1, 0.4), (C + 18.5, 0.0),
    (C + 19.1, 0.0), (C + 19.55, 0.4), (C + 20.8, 0.4), (C + 21.2, 0.0), (SECONDS, 0.0),
]


def _beds(mix):
    # a room of children, far off: air, and voices too far away to be words
    room = Mix(SECONDS, seed=21)
    room.room(0.0, SECONDS, 0.05, hum=60)
    rs = np.random.RandomState(3)
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
    # water and a low drone: only inside the thought
    wat = Mix(SECONDS, seed=22)
    wat.water(0.0, SECONDS, 0.085)
    wat.drone(0.0, SECONDS, (55, 82.5, 110), 0.06, attack=0.1, release=0.1)
    env = _envelope(wat.n, wat.rate, WATER_KEYS)
    mix.L += wat.L * env * 0.7
    mix.R += wat.R * env * 0.7


def _act_sounds(mix, acts, off, seed, pan):
    for i, a in enumerate(acts):
        t0, t1 = off + a.t0, off + a.t1
        kind = type(a).__name__
        if kind == "Write":
            n = a.plan.letters(1.0)
            _letters(mix, t0, t1, n, 0.05 + 0.03 * getattr(a, "weight", 1.0), seed + 17 * i, pan)
        elif kind == "Lines":
            if t1 - t0 < 0.12:                 # a stab: the dot of the exclamation mark
                _scratch(mix, t0, t1, 0.16, seed + i, lo=900, hi=4200, pan=pan)
                mix.thud(t1 - 0.02, 160, 0.1, pan, 0.08)
            else:
                _go_over(mix, t0, t1, 0.075 + 0.03 * a.weight, seed + 17 * i, pan)
        elif kind == "Jaw":
            n = 13 if a.part == "jaw" else 5
            _letters(mix, t0, t1, n, 0.085 * (0.6 + 0.4 * a.alpha), seed + 17 * i, pan)
        elif kind == "Mark":
            _letters(mix, t0, t1, 4, 0.07, seed + 17 * i, pan)
        elif kind == "Rub":
            _rubber(mix, t0, t1, 0.1, pan)


@film.sound
def sound(mix):

    # --- I. the pilot
    _creak(mix, 0.7, 1.5, 150, 210, 0.05, -0.2)                 # sitting down into the seat
    for at in (1.25, 2.0):
        mix.step(at, 0.035, 0.5, "wood")                        # a finger on the slip, twice
    _tick(mix, 2.62, 0.07, 0.3)                                 # the pencil out of the groove
    _act_sounds(mix, SP.ACTS, A, 100, 0.12)
    mix.whoosh(6.0, 1.1, 0.07, 0.0)                             # down through the drawn ring
    for k in range(5):                                          # the shut box rattles on its one corner
        _tick(mix, 7.92 + 0.075 * k, 0.07, -0.1)
    for at in (9.56, 9.88):                                     # the two rows, on one pin: it opens and shuts, twice
        mix.thud(at, 96, 0.22, 0.1, 0.22)
        mix.click(at, 0.12, 0.1, 4200, 0.04)
    mix.whoosh(10.1, 1.0, 0.06, 0.0)
    _tick(mix, 30.25, 0.09, 0.0)                                # the pencil laid in the groove
    mix.thud(30.25, 210, 0.05, 0.0, 0.06)
    _paper(mix, 31.0, 0.5, 0.05, 0.0)                           # lifted

    # --- the pass, left
    _paper(mix, B_ - 0.15, 0.9, 0.16, 0.5, to=-0.4)
    mix.whoosh(B_, 0.5, 0.05, 0.0)
    _creak(mix, B_ + 0.1, B_ + 0.55, 230, 170, 0.045, -0.4)

    # --- II. M.
    _paper(mix, B_ + 0.6, 0.7, 0.07, -0.1)                      # squared up
    for at in (1.55, 1.95, 2.3):
        mix.step(B_ + at, 0.03, -0.1, "wood")                   # a finger on the firm jaw, the pale one, "freak out"
    _paper(mix, B_ + 2.4, 0.6, 0.12, 0.0)                       # turned over
    mix.thud(B_ + 3.0, 180, 0.05, 0.0, 0.08)
    b = B_
    _letters(mix, b + ST.T_M[0], b + ST.T_M[1], 2, 0.07, 201, 0.0)
    _go_over(mix, b + ST.T_OVAL[0], b + ST.T_OVAL[1], 0.07, 202, 0.0)                  # the tall oval, copied
    _letters(mix, b + ST.T_B1A[0], b + ST.T_B1A[1], 12, 0.07, 203, 0.0)
    _letters(mix, b + ST.T_B1B[0], b + ST.T_B1B[1], 6, 0.05, 204, 0.0)
    _tick(mix, b + ST.T_TICK[0] + 0.02, 0.05, -0.2)             # the point comes to rest on the printed "it"
    _letters(mix, b + ST.T_B2[0], b + ST.T_B2[1], 15, 0.075, 205, 0.0)
    _go_over(mix, b + ST.T_G1[0], b + ST.T_G1[1], 0.1, 206, 0.0)                       # the g, round twice
    _letters(mix, b + ST.T_B3A[0], b + ST.T_B3A[1], 9, 0.07, 207, 0.0)
    _scratch(mix, b + ST.T_TAIL[0], b + ST.T_TAIL[1] + 0.08, 0.1, 208, pan=0.0)        # the tail on the y
    _letters(mix, b + ST.T_B3B[0] + 0.1, b + ST.T_B3B[1], 4, 0.07, 209, 0.0)
    _go_over(mix, b + ST.T_G2[0], b + ST.T_G2[1], 0.1, 210, 0.0)
    _letters(mix, b + ST.T_BOCK[0], b + ST.T_BOCK[1], 4, 0.07, 211, 0.0)
    _go_over(mix, b + ST.T_BLOT[0], b + ST.T_BLOT[1], 0.11, 212, 0.0)                  # the vowel, blotted
    mix.whoosh(b + 6.0, 1.1, 0.07, 0.0)                         # down through her own oval
    mix.whoosh(b + 7.1, 1.2, 0.05, 0.3)                         # turning round in the tin
    for f in ST.FLAPS:                                          # the pencil jaw talks: it is an intercom
        x = mix.tone(392.0, 0.3, "square", vibrato=0.03) + 0.5 * mix.tone(588.0, 0.3, "square")
        mix.add(mix.band(x, 500, 2600) * mix.env(len(x), 0.01, 0.06, 0.7, 0.08), b + ST.T6 + f + 0.08, 0.07, 0.2)
    mix.whoosh(b + 11.5, 1.0, 0.06, 0.0)
    _tick(mix, b + 23.3, 0.08, 0.0)                             # pencil down
    _paper(mix, b + 24.3, 0.5, 0.05, 0.0)

    # --- the pass, left again
    _paper(mix, C - 0.15, 0.9, 0.16, 0.5, to=-0.4)
    mix.whoosh(C, 0.5, 0.05, 0.0)
    _creak(mix, C + 0.15, C + 0.6, 210, 160, 0.04, 0.4)

    # --- III. S.
    _paper(mix, C + 0.5, 0.5, 0.09, -0.2)                       # turned round, in two pushes
    _paper(mix, C + 1.05, 0.5, 0.09, 0.2)
    _tick(mix, C + 1.68, 0.07, 0.1)
    _act_sounds(mix, SR.ACTS, C, 300, -0.05)
    mix.whoosh(C + SR.T_IN[0], 0.9, 0.07, 0.0)
    mix.whoosh(C + SR.T_GLASS[0] + 0.3, 0.9, 0.06, 0.0)         # through the glass
    for k in range(4):
        tt = mix.t(0.16)
        fr = (380 + 60 * k) * (1 + 0.9 * (tt / 0.16) ** 1.6)
        mix.add(np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7, C + SR.T_GLASS[0] + 0.75 + 0.1 * k, 0.07, -0.3 + 0.2 * k)
    mix.whoosh(C + SR.T_SWING[0], 1.2, 0.06, -0.3)
    mix.whoosh(C + SR.T_UP[0], 0.9, 0.06, 0.0)
    _tick(mix, C + 22.1, 0.08, 0.0)                             # pencil down
    _paper(mix, C + 23.0, 0.5, 0.05, 0.0)

    # --- IV. the ending
    _paper(mix, E - 0.15, 0.9, 0.16, -0.5, to=0.4)              # back the way it came
    mix.whoosh(E, 0.5, 0.05, 0.0)
    # E2: nothing. A hand not writing.
    for k, pan in enumerate((-0.6, -0.5, 0.1, 0.3)):            # four flat hands come to rest on the desk
        mix.step(E + E_HANDS[1] - 0.12 + 0.04 * k, 0.03, pan, "wood")
    mix.whoosh(E + E_RISE[0], 3.0, 0.035, 0.0)                  # up and away
    _creak(mix, E + 8.6, E + 9.3, 170, 230, 0.05, 0.5)          # one chair
    # the die is in the cup. Nothing rolls.
    mix.L *= 2.0                               # the desk is the film: pencil and paper sit above the beds
    mix.R *= 2.0
    _beds(mix)


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "m10"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            Wd._sheet(ims, 4, d / "sheet.png", scale=0.5)
            print("sheet ->", d / "sheet.png")
