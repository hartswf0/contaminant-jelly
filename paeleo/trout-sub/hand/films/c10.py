"""c10 · class film for porthole 10 · PA · "Elementary brick: flapping Clam-Shell PA".

The children's own sheet, in order, nothing added (see swarm/c10/board.md):
  0.0 .. 18.0   the pilot's page          swarm/c10/scene_pilot.py
 18.0 .. 31.5   Turkey thinks, bolts 1-3  swarm/c10/scene_turkey.py
 31.5 .. 46.5   the trout think, bolts 4-6 swarm/c10/scene_trout.py
 46.5 .. 52.0   the die is still in the cup (this file): the six bolts light in turn, all six written; one die unthrown

Everything on screen is handmade cut paper from swarm/c10/world.py; nothing is foraged (credits/c10.json is empty).
The porthole's rule (Single Hinge): the editor's joins are hinges too. Each part is a card that swings in on the
corner brad over the last frame of the part before; the last scene swings away on the same brad to show the table.
Sound is synthesized with the kit's Mix; each bolt has its own bell, heard again when the bolts light at the end.

  python3 films/c10.py                      -> assets/films/c10.mp4 (+ .webp poster)
  python3 films/c10.py --stills 3 7.8 ...   -> films/stills/c10/*.png and sheet.png
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "swarm" / "c10"))

from kit import Film  # noqa: E402
import world as Wd  # noqa: E402
import scene_pilot as SP  # noqa: E402
import scene_turkey as ST  # noqa: E402
import scene_trout as SR  # noqa: E402

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

T_TURKEY = SP.SECONDS                         # 18.0
T_TROUT = T_TURKEY + ST.SECONDS               # 31.5
T_END = T_TROUT + SR.SECONDS                  # 46.5
END_SECONDS = 5.5
SECONDS = T_END + END_SECONDS                 # 52.0
assert abs(SECONDS - 52.0) < 1e-6

# The children's sentences, in the sheet's `reads` spelling, absolute times. One at a time, each 2.5 s or more.
CAPTIONS = [(a, b, s) for a, b, s in SP.CAPTIONS] + \
           [(T_TURKEY + a, T_TURKEY + b, s) for a, b, s in ST.CAPTIONS] + \
           [(T_TROUT + a, T_TROUT + b, s) for a, b, s in SR.CAPTIONS]
for a, b, _ in CAPTIONS:
    assert b - a >= 2.5 - 1e-9, (a, b)
for (a, b, _), (c, d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert c >= b - 1e-9, (b, c)
assert CAPTIONS[-1][1] <= T_END + 1e-9
assert len(CAPTIONS) == 9                     # three pilot lines and six endings: only the children's own sentences

# The two picks are shown on their cards (printed sheet words, button, the friend's mark and initial) and are
# NOT captions: they are not sentences a child wrote. Kept here, with times, only so a voice can find them.
PICKS = [(T_TURKEY, T_TURKEY + ST.T_B1, "Turkey thinks", "Morning intercom", "circle", "M."),
         (T_TROUT, T_TROUT + SR.T_B4, "The trout think", "Confiscated lunchbox", "square", "S.")]

WRITTEN = (1, 2, 3, 4, 5, 6)                  # every ending on this sheet was written
UNWRITTEN = ()                                # a blank would be shown as an empty dashed box
BOLT_AT = {1: T_TURKEY + ST.T_B1, 2: T_TURKEY + ST.T_B2, 3: T_TURKEY + ST.T_B3,
           4: T_TROUT + SR.T_B4, 5: T_TROUT + SR.T_B5, 6: T_TROUT + SR.T_B6}
BELL = {1: 523.25, 2: 587.33, 3: 659.25, 4: 698.46, 5: 783.99, 6: 880.0}

JOIN = 0.5                                    # a new part swings in on the corner brad
PIN = (26, 26)


# ------------------------------------------------------------ the joins ---
@lru_cache(None)
def _last_frame(which):
    mod = {"pilot": SP, "turkey": ST, "trout": SR}[which]
    img = Image.new("RGB", (W, H), (0, 0, 0))
    mod.draw(mod.SECONDS - 1e-3, img)
    return img


def _join(ink, prev, mod, u):
    """The first JOIN seconds of a part: its frame is a card swinging in about the corner brad, over the part before."""
    a = -96.0 * (1 - ease(u, 0.0, JOIN))
    if a > -0.05:
        mod.draw(u, ink)
        return
    Wd._comp(ink, _last_frame(prev).convert("RGBA"), (0, 0))
    card = Image.new("RGB", (W, H), (0, 0, 0))
    mod.draw(u, card)
    Wd.swing_card(ink, card, PIN, angle=a)


# ----------------------------------------------------------- the ending ---
E_AWAY = 0.75                                 # the last scene swings away on its brad
E_LIT0, E_LIT_GAP = 0.95, 0.38                # the bolts light one at a time, 1 to 6
E_CUP = 3.0                                   # then: the cup. Its lid lifts on its one brad, far enough to see the die
E_LID0, E_LID1 = 3.0, 3.5                     # still lying in there, and drops back to rest ajar. Nothing is thrown.
LID_PEEK, LID_REST = 62.0, 48.0
E_JAW0, E_JAW1 = 4.1, 4.35                    # the pencil jaw's top edge lifts on its brad and settles
CUP = (76, 420, 60)


def lit_time(n):
    return T_END + E_LIT0 + E_LIT_GAP * (n - 1)


def _ending(tgt, e):
    cx, cy, sc = SP.RING
    Wd.desk(tgt)
    lit = tuple(n for n in WRITTEN if T_END + e >= lit_time(n))
    Wd.sheet_ring(tgt, cx, cy, sc, lit=lit, empty=UNWRITTEN, t=e)
    rest, top = SP._split_layers()
    Wd._comp(tgt, rest, (0, 0))
    if e < E_JAW0:
        lift = 0.0
    elif e < E_JAW1:
        lift = 9.0 * math.sin(math.pi * ramp(e, E_JAW0, E_JAW1)) ** 0.8
    else:
        lift = 1.8 * Wd.settle(e, E_JAW1, 1.0, 5.0, 9.0)
    if abs(lift) < 0.05:
        Wd._comp(tgt, top, (0, 0))
    else:
        Wd.swing_card(tgt, top, SP.HINGE, -lift, pinned=False, shadow=0)
    Wd.brad(tgt, SP.HINGE[0], SP.HINGE[1], 5)
    Wd.pencil(tgt, 548, 512, angle=-14.0, lift=0)             # put down; nobody is holding it
    # the die cup beside the paper, the die resting in it: not thrown, and it does not move
    x, y, r = CUP
    g = ease(e, E_CUP, E_CUP + 0.7)
    if g > 0:
        Wd.glow(tgt, x, y, r + 46, (255, 232, 170), 0.55 * g)
    cup = Wd._cup(int(r))
    Wd._comp(tgt, Wd.shadow_of(cup.getchannel("A"), 9, 0.5), (x - cup.size[0] / 2 + 7, y - cup.size[1] / 2 + 10))
    Wd._comp(tgt, cup, (x - cup.size[0] / 2, y - cup.size[1] / 2))
    Wd.die(tgt, 5, x - 13, y + 11, 36, 24)                    # lying against the wall of the cup, under the lid
    if e < E_LID0:
        a = 0.0
    elif e < E_LID1:
        a = LID_PEEK * ease(e, E_LID0, E_LID1)
    else:
        a = LID_REST + (LID_PEEK - LID_REST) * (1 - ease(e, E_LID1, E_LID1 + 0.3)) + 3.0 * Wd.settle(e, E_LID1 + 0.3, 1.0, 3.0, 6.0)
    Wd.draw_sprite(tgt, _lid(r), Wd.Tm(x, y - r) @ Wd.Rm(-a), (4.0, 6.0, 4.0, 0.5))
    Wd.brad(tgt, x, y - r, 6)


@lru_cache(None)
def _lid(r):
    """The cup's leather lid, a stitched disc; its one brad is at the origin (the rim), the disc hangs below it."""
    R = r + 3

    def deco(d, L, S):
        for k in range(44):
            an = 2 * math.pi * k / 44
            p0 = L(math.cos(an) * (R - 7), r + math.sin(an) * (R - 7))
            p1 = L(math.cos(an + 0.07) * (R - 7), r + math.sin(an + 0.07) * (R - 7))
            d.line([p0, p1], fill=(226, 200, 150), width=S + 1)
        d.ellipse([L(-R * 0.42, r - R * 0.42), L(R * 0.42, r + R * 0.42)], outline=(104, 62, 36), width=2 * S)
        d.ellipse([L(-5, r - 5), L(5, r + 5)], fill=(190, 150, 80), outline=(96, 66, 30), width=S)       # the knob
    return Wd.cut(Wd.circ(0, r, R, 48), (138, 86, 50), deco, curve=False, seed=853, grain=0.11)


@lru_cache(None)
def _ending_start():
    img = Image.new("RGB", (W, H), (0, 0, 0))
    _ending(img, 0.0)
    return img


# ---------------------------------------------------------------- film ---
film = Film("c10", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TROUT + SR.T_B5 + 2.0


@film.picture
def frame(t, ink):
    ink._grain = False            # the paper's fibre is in the cut pieces themselves; no grain laid over the frame
    if t < T_TURKEY:
        SP.draw(t, ink)
    elif t < T_TROUT:
        u = t - T_TURKEY
        if u < JOIN:
            _join(ink, "pilot", ST, u)
        else:
            ST.draw(u, ink)
    elif t < T_END:
        u = t - T_TROUT
        if u < JOIN:
            _join(ink, "turkey", SR, u)
        else:
            SR.draw(u, ink)
    else:
        e = t - T_END
        if e < E_AWAY:
            Wd._comp(ink, _ending_start().convert("RGBA"), (0, 0))
            Wd.swing_card(ink, _last_frame("trout"), PIN, angle=-104.0 * ease(e, 0.0, E_AWAY) ** 1.3)
        else:
            _ending(ink, e)
    Wd.badge(ink)
    for a, b, text in CAPTIONS:
        if a <= t < b:
            ink.caption(text, size=27)
            break


# --------------------------------------------------------------- sound ---
def _scratch(mix, a, b, gain=0.07, seed=0):
    """Pencil on paper: a band of noise that swells along each stroke."""
    n = max(0.05, b - a)
    x = mix.band(mix.noise(n), 1800, 7000)
    tt = mix.t(n)[: len(x)]
    x = x[: len(tt)] * (0.55 + 0.45 * np.sin(2 * np.pi * (5 + seed % 3) * tt + seed)) * np.hanning(len(tt)) ** 0.5
    mix.add(x, a, gain, pan=-0.2 + 0.1 * (seed % 5))


def _clap(mix, at, gain=0.5, pan=0.3):
    """The shell's two valves meeting."""
    mix.thud(at, 96, gain, pan, 0.28)
    mix.click(at, gain * 0.7, pan, 5200, 0.05)


def _squawk(mix, at, seconds=0.3, gain=0.1, pan=0.3, f=392.0):
    """The PA talking: a short, boxy, band-limited buzz."""
    x = mix.tone(f, seconds, "square", vibrato=0.03) + 0.5 * mix.tone(f * 1.5, seconds, "square")
    x = mix.band(x, 500, 2600) * mix.env(len(x), 0.01, 0.06, 0.7, 0.08)
    mix.add(x, at, gain, pan)


def _gobble(mix, at, seconds=0.55, gain=0.1, pan=-0.4):
    """Turkey freaking out: a falling, chopped warble."""
    tt = mix.t(seconds)
    f0 = 560 - 230 * tt / seconds
    ph = 2 * np.pi * np.cumsum(f0) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    x *= (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 15 * tt))) * mix.env(len(x), 0.01, 0.05, 0.9, 0.12)
    mix.add(mix.band(x, 350, 3200), at, gain, pan)


def _bloop(mix, at, f=420.0, gain=0.16, pan=0.0, seconds=0.16, up=1.9):
    """A bubble."""
    tt = mix.t(seconds)
    fr = f * (1 + (up - 1) * (tt / seconds) ** 1.6)
    x = np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7
    mix.add(x, at, gain, pan)


def _tick(mix, at, gain=0.12, pan=0.5):
    mix.click(at, gain, pan, 7000, 0.015)


def _creak(mix, a, b, f0=180.0, f1=260.0, gain=0.07, pan=0.0):
    n = max(0.1, b - a)
    tt = mix.t(n)
    fr = lerp(f0, f1, tt / n) * (1 + 0.04 * np.sin(2 * np.pi * 23 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 7)) * np.hanning(len(tt))
    mix.add(mix.band(x, 300, 2400), a, gain, pan)


def _bolt(mix, n, at, gain=0.3):
    """Each bolt's own mark: the die clicks down, then the bolt's bell."""
    mix.click(at, 0.22, 0.0, 3000, 0.03)
    mix.bell(at + 0.02, BELL[n], 2.4, gain, pan=-0.3 + 0.12 * (n - 1))


@film.sound
def sound(mix):
    A, B, C, E = 0.0, T_TURKEY, T_TROUT, T_END
    # beds: the room over the table, the river outside, the tin's own hum from Turkey's seat
    mix.room(0.0, 8.6, 0.022)
    mix.room(E - 0.2, END_SECONDS + 0.2, 0.022)
    mix.water(SP.T_P2 - 0.1, B - SP.T_P2 + 0.4, 0.05)
    mix.water(B, C - B + 0.3, 0.022)
    mix.drone(B, C - B, (55, 82.5, 110), 0.05, attack=0.6, release=0.6)
    mix.water(C, E - C + 0.5, 0.05)

    # --- I. the pilot's page
    e = SP._stroke_ends()
    keys = [(0.15, 0.0), (0.8, e[0]), (1.5, e[1]), (2.6, e[4]), (5.4, e[12]), (5.8, e[12] + 0.004), (7.4, 1.0)]

    def when(p):                              # the time at which drawing progress p is reached
        for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
            if p <= pb:
                return ta + (tb - ta) * (p - pa) / max(1e-9, pb - pa)
        return keys[-1][0]
    prev = 0.0
    for k, pe in enumerate(e):
        a, b = when(prev), when(pe)
        if k == 13:
            a = 5.8
        _scratch(mix, a + 0.02, b - 0.03, 0.06 + 0.03 * Wd.PILOT_STROKES[k]["weight"], seed=k)
        prev = pe
    mix.click(7.68, 0.3, -0.3, 2500, 0.04)            # the brad pressed through the paper
    mix.thud(7.68, 150, 0.18, -0.3, 0.12)
    _tick(mix, 7.94, 0.14, -0.2)                      # the pencil jaw drops back on its brad
    mix.whoosh(SP.T_P2, 0.7, 0.12, -0.3)              # the paper swings away
    _tick(mix, SP.T_P2 + 1.72, 0.3, -0.1)             # a fry bumps the latch; the latch holds
    mix.note(SP.T_P2 + 1.72, 1568, 0.18, 0.08, -0.1, "sine", decay=0.12, sustain=0.0)
    mix.whoosh(SP.T_P3, 0.5, 0.1, -0.3)
    _clap(mix, SP.T_P3 + SP.P3_FLAP + 0.16, 0.45, 0.5)
    for k, dt in enumerate((0.3, 0.75, 1.25)):        # "Freak out."
        _gobble(mix, SP.T_P3 + SP.P3_FLAP + dt, 0.42, 0.12, -0.1)
    mix.whoosh(SP.T_P4, 0.5, 0.1, -0.3)
    _creak(mix, SP.T_P4 + SP.P4_OPEN, SP.T_P4 + SP.P4_OPEN + 0.6, 150, 250, 0.08, 0.4)
    for k in range(14):                               # the string of bubbles going into the big container
        _bloop(mix, SP.T_P4 + 1.0 + 1.1 * k / 13, 380 + 35 * (k % 5), 0.1, -0.3 + 0.05 * k)
    for k in range(5):                                # the needle falling from full to half
        _tick(mix, SP.T_P4 + 1.15 + 0.33 * k, 0.1, -0.4)
    _clap(mix, SP.T_P4 + SP.P4_SHUT + 0.14, 0.55, 0.4)
    _gobble(mix, SP.T_P4 + 3.0, 0.4, 0.08, -0.4)

    # --- II. Turkey thinks
    mix.whoosh(B, 0.6, 0.12, -0.3)
    mix.click(B + 0.6, 0.25, -0.5, 2500, 0.04)        # the pick card flips up
    mix.note(B + 0.7, 392, 0.3, 0.14, -0.3, "tri")    # the red circle pressed
    for f in ST.T0_FLAPS:
        _squawk(mix, B + f + 0.1, 0.3, 0.1, 0.4)
    mix.whoosh(B + 2.08, 0.4, 0.08, -0.4)
    b1, b2, b3 = BOLT_AT[1], BOLT_AT[2], BOLT_AT[3]
    for n in (1, 2, 3):
        mix.whoosh(BOLT_AT[n], 0.45, 0.06, 0.0)       # the ending swings in behind the glass
        _bolt(mix, n, BOLT_AT[n] + 0.42)
    for k, f in enumerate(ST.B1_FLAPS):
        _squawk(mix, b1 + f + 0.1, 0.3, 0.1, 0.4, 392 if k != 1 else 440)
    _tick(mix, b1 + ST.B1_FLAPS[0] + 0.3, 0.12, 0.7)  # the gauge loses a notch
    mix.note(b1 + ST.B1_TAP, 1760, 0.2, 0.12, -0.1, "sine", decay=0.1, sustain=0.0)   # a nose taps the glass; it holds
    mix.click(b1 + ST.B1_TAP, 0.2, -0.1, 6000, 0.02)
    _gobble(mix, b1 + 3.0, 0.35, 0.07, -0.6)
    _creak(mix, b2 + ST.B2_SHUT0, b2 + ST.B2_SHUT1, 240, 130, 0.09, 0.2)
    _clap(mix, b2 + ST.B2_SHUT1, 0.8, 0.1)            # the lid comes down over the way back
    mix.thud(b2 + ST.B2_SHUT1 + 0.02, 55, 0.5, 0.0, 0.6)
    for k in range(4):                                # the needle falls to the last mark
        _tick(mix, b2 + ST.B2_SHUT0 + 0.2 + 0.2 * k, 0.1, 0.7)
    _gobble(mix, b2 + 2.3, 0.5, 0.09, -0.6)
    _creak(mix, b3 + ST.B3_BAT0, b3 + ST.B3_HIT, 150, 420, 0.09, 0.3)
    mix.thud(b3 + ST.B3_HIT, 62, 0.9, 0.0, 0.5)       # the shell bats the tin
    mix.click(b3 + ST.B3_HIT, 0.4, 0.0, 3000, 0.06)
    mix.whoosh(b3 + ST.B3_TURN0, 0.9, 0.2, 0.0)       # the world turns about the one pin
    foam = mix.band(mix.noise(1.1), 900, 6500) * np.hanning(int(1.1 * mix.rate)) ** 0.6
    mix.add(foam, b3 + ST.B3_TURN0 + 0.15, 0.12)      # the surface breaks white
    mix.step(b3 + ST.B3_HOME1, 0.5, 0.0, "wood")      # home: the shelf
    for k, f in enumerate((392, 494, 587, 784)):      # air again: the needle swings up to full
        mix.pluck(b3 + ST.B3_HOME1 + 0.12 + 0.13 * k, f, 1.1, 0.14, -0.2 + 0.15 * k)
    _gobble(mix, b3 + 3.0, 0.45, 0.09, -0.6)          # back, and still freaking out

    # --- III. the trout think
    mix.whoosh(C, 0.6, 0.12, -0.3)
    mix.click(C + 0.6, 0.25, 0.1, 2500, 0.04)
    mix.note(C + 0.7, 494, 0.3, 0.14, 0.1, "tri")     # the pink square pressed
    mix.click(C + 1.3, 0.25, -0.3, 6500, 0.03)        # the wire handle swings up
    mix.note(C + 1.3, 1245, 0.25, 0.06, -0.3, "sine", decay=0.15, sustain=0.0)
    mix.step(C + 1.8, 0.12, -0.2, "gravel")           # the paper tag drops on its string
    mix.whoosh(C + 2.08, 0.4, 0.08, 0.2)
    b4, b5, b6 = BOLT_AT[4], BOLT_AT[5], BOLT_AT[6]
    for n in (4, 5, 6):
        mix.whoosh(BOLT_AT[n], 0.45, 0.08, -0.3)
        _bolt(mix, n, BOLT_AT[n] + 0.42)
    _creak(mix, b4 + SR.B4_OPEN0, b4 + SR.B4_SNAP0, 150, 240, 0.06, 0.5)
    mix.click(b4 + SR.B4_SNAP - 0.04, 0.35, -0.3, 5000, 0.03)      # the beak claps the glass
    _clap(mix, b4 + SR.B4_SNAP, 0.7, 0.5)
    for k in range(5):                                # five trout run
        t0 = b4 + SR.b4_start(k) + SR.B4_TURN * 0.6
        mix.whoosh(t0, 0.8, 0.11, -0.2 + 0.25 * k)
        _bloop(mix, t0 + 0.45, 520 + 40 * k, 0.07, 0.2 + 0.15 * k)
    _tick(mix, b4 + SR.B4_SNAP + 0.25, 0.12, -0.4)
    _gobble(mix, b4 + 2.4, 0.45, 0.08, -0.3)
    tune = (392, 494, 587, 494, 440, 587, 659, 784)   # the shell flaps a beat; the party is made of swimming
    for k in range(SR.B5_FLAPS):
        f = b5 + SR.B5_BEAT0 + SR.B5_PER * k
        _clap(mix, f + 0.1, 0.4, 0.5)
        mix.pluck(f + 0.1, tune[k], 0.9, 0.2, -0.3 + 0.08 * k)
        mix.pluck(f + 0.1 + SR.B5_PER / 2, tune[k] * 1.5, 0.5, 0.1, 0.3)
        mix.pluck(f + 0.1, tune[k] / 2 if k % 2 == 0 else 196, 0.8, 0.14, 0.0)
        _bloop(mix, f + 0.2, 700 + 60 * (k % 4), 0.05, -0.4 + 0.1 * k)
        if k in (3, 7):
            _tick(mix, f + 0.25, 0.12, -0.4)
    for dt in (1.33, 2.6):                            # Turkey is off the beat: he is not dancing
        _gobble(mix, b5 + dt, 0.32, 0.07, -0.3)
    mix.click(b6 + SR.B6_LATCH1, 0.4, 0.0, 6500, 0.03)             # the latch that held all film flips up
    mix.note(b6 + SR.B6_LATCH1, 1319, 0.3, 0.09, 0.0, "sine", decay=0.2, sustain=0.0)
    _creak(mix, b6 + SR.B6_DOOR0, b6 + SR.B6_DOOR1, 210, 330, 0.09, -0.2)
    for k in range(5):                                # all five swim in
        _bloop(mix, b6 + SR.B6_IN0 + SR.B6_GAP * k + SR.B6_DUR - 0.12, 300 + 55 * k, 0.2, -0.2, 0.2, 2.1)
        _tick(mix, b6 + SR.B6_IN0 + SR.B6_GAP * k + SR.B6_DUR - 0.1, 0.08, 0.2)
    _creak(mix, b6 + SR.B6_SHUT0, b6 + SR.B6_SHUT1, 330, 200, 0.08, -0.2)
    mix.thud(b6 + SR.B6_SHUT1, 110, 0.6, -0.1, 0.3)   # the door shuts behind the last tail
    mix.click(b6 + SR.B6_SHUT1, 0.3, -0.1, 4000, 0.04)
    mix.whoosh(b6 + SR.B6_PULL0, 0.3, 0.07, -0.1)
    _bloop(mix, b6 + SR.B6_BURP, 130, 0.45, 0.2, 0.34, 2.6)        # one big bubble out of the vent
    _gobble(mix, b6 + 4.55, 0.35, 0.06, -0.1)

    # --- IV. the die is still in the cup
    mix.whoosh(E, 0.7, 0.12, -0.3)                    # the last scene swings away
    for n in WRITTEN:                                 # each written bolt lights with its own bell
        mix.bell(lit_time(n), BELL[n], 2.6, 0.26, pan=-0.3 + 0.12 * (n - 1))
        mix.click(lit_time(n), 0.1, 0.0, 3000, 0.02)
    _creak(mix, E + E_LID0, E + E_LID1, 300, 380, 0.04, -0.6)     # the cup's lid lifts on its brad
    mix.thud(E + E_LID1 + 0.3, 140, 0.16, -0.6, 0.12)             # and drops back. The die has not moved.
    _tick(mix, E + E_JAW1, 0.12, -0.2)                # the pencil jaw settles. Nothing rolls.
    mix.reverb(0.12, 0.8)


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "c10"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            Wd._sheet(ims, 4, d / "sheet.png", scale=0.5)
            print("sheet ->", d / "sheet.png")
