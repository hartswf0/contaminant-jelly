"""c25 · class film for porthole 25 · Lock · "Diner Trout wearing inverted fishbowl".

The children's own sheet, in order, nothing added (see swarm/c25/board.md):
  0.0 .. 20.5   the pilot's page             swarm/c25/scene_pilot.py
 20.5 .. 36.0   Turkey thinks, bolts 1-3     swarm/c25/scene_turkey.py
 36.0 .. 46.0   the trout think, bolts 4-6   swarm/c25/scene_trout.py   (5 and 6 are blank on the sheet)
 46.0 .. 52.0   the die is still in the cup  (this file): bolts 1 to 4 light in turn, 5 and 6 stay dead; one die unthrown

Foraged: Turkey (Audubon) and the trout (Denton), see credits/c25.json. Everything else is handmade cut paper and
pencil from swarm/c25/world.py. The porthole's rule (Inverted Helmet): every cut is the card turned over top to
bottom, and the editor's three joins are the same turn-over. Sound is synthesized with the kit's Mix: each written
bolt has its own bell, heard again when it lights at the end; a blank bolt gets only the slap of its card.

  python3 films/c25.py                      -> assets/films/c25.mp4 (+ .webp poster)
  python3 films/c25.py --stills 3 7.8 ...   -> films/stills/c25/*.png and sheet.png
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "swarm" / "c25"))

from kit import FPS, H, W, Film, Ink, clamp, ease, lerp, ramp  # noqa: E402
import world as w  # noqa: E402
import scene_pilot as SP  # noqa: E402
import scene_turkey as ST  # noqa: E402
import scene_trout as SR  # noqa: E402

# The modules each draw the badge last; here it must stay put while cards turn over under it, so the editor
# draws it once, on top of everything, and the modules' own call does nothing.
_badge = w.badge
w.badge = lambda *a, **k: None
SP.BADGE = False

T_TURKEY = SP.SECONDS                         # 20.5
T_TROUT = T_TURKEY + ST.SECONDS               # 36.0
T_END = T_TROUT + SR.SECONDS                  # 46.0
END_SECONDS = 6.0
SECONDS = T_END + END_SECONDS                 # 52.0
assert abs(SECONDS - 52.0) < 1e-6
FLIP = 8 / FPS                                # a card turned over: 8 frames


# The children's sentences, in the sheet's `reads` spelling, absolute times. One at a time, each 2.5 s or more.
def _captions():
    out = []
    for off, mod in ((0.0, SP), (T_TURKEY, ST), (T_TROUT, SR)):
        for a, b, s in mod.CAPTIONS:
            b = min(b, mod.SECONDS - FLIP) if mod is not SR else b      # off before the card turns over to the next part
            out.append((round(off + a, 3), round(off + b, 3), s))
    return out


CAPTIONS = _captions()
for _a, _b, _ in CAPTIONS:
    assert _b - _a >= 2.5 - 1e-9, (_a, _b)
for (_a, _b, _), (_c, _d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert _c >= _b - 1e-9, (_b, _c)

WRITTEN = (1, 2, 3, 4)
UNWRITTEN = (5, 6)                            # blank on the sheet: never lit, never rung, nothing invented
BOLT_AT = {1: T_TURKEY + ST.T_B1, 2: T_TURKEY + ST.T_B2, 3: T_TURKEY + ST.T_B3,
           4: T_TROUT + SR.T_B4, 5: T_TROUT + SR.T_B5, 6: T_TROUT + SR.T_B6}
BELL = {1: 523.25, 2: 587.33, 3: 659.25, 4: 783.99}


# ----------------------------------------------------------- the ending ---
E_C, E_R = (440, 270), 172                    # the porthole lying on the table, small enough that all six dice are in frame
E_LIT0, E_GAP = 0.7, 0.4
E_SLOSH = w.Follower(lambda e: 13.0 if e < 0.42 else 0.0, END_SECONDS + 1, f=1.1, zeta=0.16)


def lit_time(n):
    return T_END + E_LIT0 + E_GAP * (n - 1)


@lru_cache(None)
def _disc_mask(d):
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse([2, 2, d * 4 - 3, d * 4 - 3], fill=255)
    return m.resize((d, d), Image.LANCZOS)


def _ending(ink, e):
    cx, cy = E_C
    w.table(ink, sheet=False)
    ro = int(E_R * w.RING_OUT / w.PORT_R)
    ring = w.brass_ring(E_R, ro, 6, 10, 3)
    ink.paste(w._shadow_of(ring, 9, 0.7, (20, 12, 6)), (int(cx - ring.width / 2 + 9), int(cy - ring.height / 2 + 13)))
    # through the glass, small: the trout standing in its bowl, and low left Turkey's reflection, still panicking
    o = w.offscreen(ink)
    s = E_SLOSH.at(e)
    w.seat_scene(o, e, dict(x=540, step=0.0, bob=False, phase=e * 1.2, amp=2.0, slosh=s, wave=clamp(abs(s) / 8),
                            bowl_bubbles=e),
                 dict(cx=352, cy=372, height=212, alpha=0.68, wing_scale=0.66, mood="panic", t=e), frame=False)
    R = w.PORT_R
    px, py = w.PORT_C
    d = 2 * E_R
    disc = o.img.crop((px - R, py - R, px + R, py + R)).resize((d, d), Image.LANCZOS).convert("RGBA")
    disc.putalpha(_disc_mask(d))
    ink.paste(disc, (cx - E_R, cy - E_R))
    ink.d.ellipse([cx - E_R, cy - E_R, cx + E_R, cy + E_R], outline=(30, 24, 18, 150), width=6)
    ink.paste(ring, (int(cx - ring.width / 2), int(cy - ring.height / 2)))
    for n in range(1, 7):                     # the written bolts light one after another; 5 and 6 are empty from the first frame
        if n in WRITTEN:
            w.bolt_mark(ink, n, lit=ease(T_END + e, lit_time(n), lit_time(n) + 0.3), c=E_C, r=E_R, size=36)
        else:                                 # nothing was written: no die at all, only the dark seat where one would sit
            x, y = w.bolt_mark(ink, n, lit=0.0, die=False, c=E_C, r=E_R)
            ink.d.rounded_rectangle([x - 18, y - 18, x + 18, y + 18], radius=6, fill=(24, 18, 12, 190),
                                    outline=(92, 70, 34, 255), width=2)
            ink.d.line([x - 16, y + 17, x + 16, y + 17], fill=(206, 170, 96, 120), width=1)
    w.gauge(ink, 3.0, 108, 446, r=54, t=e)    # as the pilot's page left it: half
    w.die_cup(ink, 824, 500, 158)             # the die rests in the cup. Nobody touches it.


# ----------------------------------------------------------- the joins ---
def _still(fn, t):
    k = Ink(t, int(t * FPS), boil=0, wobble=0.0)
    fn(t, k)
    return k.img.copy()


@lru_cache(None)
def _first(which):
    return _still({"turkey": ST.draw, "trout": SR.draw}[which], 0.0)


@lru_cache(None)
def _last(which):
    return _still({"trout": SR.draw}[which], SR.SECONDS - 1.0 / FPS)


def _picture(t, ink):
    if t < T_TURKEY:
        SP.draw(t, ink)
        f = (t - (T_TURKEY - FLIP)) / FLIP
        if f > 0:                             # the pilot's page is turned over; Turkey's part is on its back
            w.card_flip(ink, _first("turkey"), clamp(f, 0.001, 0.999))
    elif t < T_TROUT:
        ST.draw(t - T_TURKEY, ink)
        f = (t - (T_TROUT - FLIP)) / FLIP
        if f > 0:
            w.card_flip(ink, _first("trout"), clamp(f, 0.001, 0.999))
    elif t < T_END:
        SR.draw(t - T_TROUT, ink)
    else:
        e = t - T_END
        if e < FLIP:                          # the last blank card is turned over on to the table
            ink.img.paste(_last("trout"), (0, 0))
            ink.d = ImageDraw.Draw(ink.img, "RGBA")
            o = w.offscreen(ink)
            _ending(o, e)
            w.card_flip(ink, o.img, clamp(e / FLIP, 0.001, 0.999))
        else:
            _ending(ink, e)


# ---------------------------------------------------------------- film ---
film = Film("c25", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY + ST.T_B3 + 3.0


@film.picture
def frame(t, ink):
    ink._grain = False                        # the paper's fibre is in the cut pieces; no grain laid over the frame
    _picture(t, ink)
    _badge(ink)
    for a, b, text in CAPTIONS:
        if a <= t < b:
            # bolt 4's escort swims along the bottom of the frame: its caption sits at the top, clear of every fish
            ink.caption(text, size=27, y=38 if a >= T_TROUT else None)
            break


# --------------------------------------------------------------- sound ---
def _scratch(mix, a, b, gain=0.07, seed=0, lo=1800, hi=7000):
    """Pencil on paper: a band of noise that swells along the stroke."""
    n = max(0.06, b - a)
    x = mix.band(mix.noise(n), lo, hi)
    tt = mix.t(n)[: len(x)]
    x = x[: len(tt)] * (0.55 + 0.45 * np.sin(2 * np.pi * (5 + seed % 3) * tt + seed)) * np.hanning(len(tt)) ** 0.5
    mix.add(x, a, gain, pan=-0.2 + 0.1 * (seed % 5))


def _flutter(mix, at, seconds=0.5, gain=0.12, pan=-0.4, muffled=False):
    """One wing-beat against the tin wall: a chopped gust and a dull knock on the metal."""
    tt = mix.t(seconds)
    x = mix.band(mix.noise(seconds), 150, 900 if muffled else 2600)[: len(tt)]
    x *= (0.5 + 0.5 * np.sin(2 * np.pi * 17 * tt)) ** 2 * np.sin(np.pi * tt / seconds) ** 0.8
    mix.add(x, at, gain * (2.2 if muffled else 1.0), pan)
    mix.thud(at + seconds * 0.45, 150 if muffled else 190, gain * 1.4, pan, 0.12)


def _bloop(mix, at, f=420.0, gain=0.12, pan=0.0, seconds=0.15, up=1.9):
    """A bubble."""
    tt = mix.t(seconds)
    fr = f * (1 + (up - 1) * (tt / seconds) ** 1.6)
    x = np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7
    mix.add(x, at, gain, pan)


def _puff(mix, at, n, pan=-0.4, gain=0.11):
    for k in range(n):
        _bloop(mix, at + 0.05 * k + 0.02 * (k % 3), 430 + 70 * ((k * 5) % 7), gain, pan + 0.04 * k)


def _tick(mix, at, gain=0.16, pan=-0.6):
    """The gauge needle dropping one tick."""
    mix.click(at, gain, pan, 7000, 0.015)
    mix.note(at, 1180, 0.09, gain * 0.35, pan, "sine", decay=0.06, sustain=0.0)


def _gobble(mix, at, seconds=0.5, gain=0.09, pan=-0.4):
    """Turkey panicking: a falling, chopped warble."""
    tt = mix.t(seconds)
    f0 = 600 - 240 * tt / seconds
    ph = 2 * np.pi * np.cumsum(f0) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 9))
    x *= (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 15 * tt))) * mix.env(len(x), 0.01, 0.05, 0.9, 0.12)
    mix.add(mix.band(x, 350, 3200), at, gain, pan)


def _turn(mix, at, gain=0.13, pan=0.0):
    """The card turned over: air under it, then its edge slapping the table."""
    mix.whoosh(at, FLIP + 0.05, gain, pan)
    mix.click(at + FLIP, gain * 2.0, pan, 2600, 0.04)
    mix.thud(at + FLIP, 120, gain * 1.3, pan, 0.1)


def _bolt(mix, n, at, gain=0.3):
    """A written bolt's own mark: the die clicks down, then the bolt's bell."""
    mix.click(at, 0.22, 0.0, 3000, 0.03)
    mix.bell(at + 0.02, BELL[n], 2.4, gain, pan=-0.3 + 0.2 * (n - 1))


def _squeak(mix, at, seconds=0.2, gain=0.07, pan=0.2, f0=900.0, f1=1300.0):
    """Wet glass shifted on a brass collar."""
    tt = mix.t(seconds)
    fr = lerp(f0, f1, tt / seconds) * (1 + 0.02 * np.sin(2 * np.pi * 31 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.hanning(len(tt))
    mix.add(x, at, gain, pan)


@film.sound
def sound(mix):
    B, C, E = T_TURKEY, T_TROUT, T_END
    P2, P3, P4 = SP.T_P2, SP.T_P3, SP.T_P4
    b1, b2, b3, b4, b5, b6 = (BOLT_AT[n] for n in range(1, 7))
    dry = b3 + ST.B3_LIFT[1]                  # from here the river is gone

    # beds: the room over the table; the river (louder from outside, dull from Turkey's seat); dry air; the room again
    mix.room(0.0, P2, 0.02)
    mix.water(P2 - 0.1, P3 - P2 + 0.2, 0.05)
    mix.water(P3, b3 + ST.B3_LIFT[0] + 0.9 - P3, 0.024)
    mix.drone(P3, dry - P3, (55, 82.5, 110), 0.04, attack=0.5, release=1.2)
    mix.wind(b3 + ST.B3_LIFT[0], C - FLIP - b3 - ST.B3_LIFT[0], 0.035)
    mix.water(C - 0.1, E - C - 1.9, 0.05)
    mix.room(b5, SECONDS - b5, 0.02)

    # --- I. the pilot's page
    for k, (g, (a, b)) in enumerate(w.PILOT_TIMES.items()):
        n = {"bowl": 4, "arms": 4, "legs": 3, "fin_mouth": 3}.get(g, 1)      # loops and short strokes are several scratches
        for j in range(n):
            _scratch(mix, a + (b - a) * j / n, a + (b - a) * (j + 1) / n - 0.03,
                     0.05 if g == "bowl" else 0.085, seed=k * 3 + j)
    mix.click(7.9, 0.12, 0.3, 3000, 0.02)                 # the pencil lifts
    _scratch(mix, SP.T_MORPH[0], SP.T_MORPH[1], 0.05, seed=9, lo=900, hi=4000)      # the lines move out to the cut edges
    mix.whoosh(SP.T_LAY[0], SP.T_LAY[1] - SP.T_LAY[0], 0.05, 0.3)                 # the cut puppet slid in under them, in one piece
    mix.step(SP.T_LAY[1] + 0.1, 0.2, 0.0, "wood")         # and set down
    _bloop(mix, SP.T_LAY[1] + 0.16, 300, 0.08, -0.2, 0.2)  # the water in the bowl slops
    _turn(mix, P2 - FLIP, 0.14, 0.0)
    mix.note(P2 + 1.3, 1760, 0.25, 0.1, 0.1, "sine", decay=0.15, sustain=0.0)    # glass to glass
    mix.click(P2 + 1.3, 0.18, 0.1, 6000, 0.02)
    _scratch(mix, P2 + 0.9, P2 + 1.8, 0.05, seed=4)       # the tin's outline redrawn as a bottle
    _scratch(mix, P2 + 3.3, P2 + 4.1, 0.04, seed=6)       # and back
    k = 0
    while P2 + 0.2 + k / 2.3 < P3 - 0.3:                  # he is beating in there already: heard through the tin
        _flutter(mix, P2 + 0.2 + k / 2.3, 0.36, 0.035, 0.4, muffled=True)
        k += 1
    _turn(mix, P3, 0.12, 0.0)
    _gobble(mix, P3 + 0.45, 0.55, 0.11, -0.4)             # "Panic."
    for b in SP.P3_BEATS:
        _flutter(mix, b - 0.1, 0.4, 0.1, -0.4)
    _gobble(mix, P3 + 2.1, 0.4, 0.08, -0.4)
    for b in SP.BEATS:                                    # "By panicking.": a beat, a puff, a tick. Nothing between.
        _flutter(mix, b - 0.12, 0.5, 0.14, -0.4)
        _puff(mix, b + 0.12, 6)
        _tick(mix, b + 0.14)

    # --- II. Turkey thinks
    _turn(mix, B - FLIP, 0.14, 0.0)
    mix.click(B + 0.55, 0.22, 0.5, 2500, 0.04)            # the pick card comes up flat
    mix.note(B + 0.8, 392, 0.3, 0.13, 0.5, "tri")         # the green triangle pressed
    _scratch(mix, B + 1.05, B + 1.4, 0.07, seed=1)        # K.'s triangle
    _scratch(mix, B + 1.42, B + 1.75, 0.07, seed=2)
    _scratch(mix, B + 1.15, B + 2.0, 0.045, seed=5, lo=700, hi=3000)     # the helmet ringed in green crayon
    for n in (1, 2, 3):
        _turn(mix, BOLT_AT[n], 0.12, 0.0)
        _bolt(mix, n, BOLT_AT[n] + FLIP + 0.04)
    # bolt 1 · "The air runs out."
    for k, (b, n) in enumerate(zip(ST.B1_BEATS, ST.B1_PUFFS)):
        _flutter(mix, b1 + b, 0.5, 0.13, -0.4)
        if n == 1:
            _bloop(mix, b1 + b + 0.22, 330, 0.2, -0.4, 0.24)      # the last one: a single bubble
        else:
            _puff(mix, b1 + b + 0.2, n)
        if k < 3:
            _tick(mix, b1 + b + 0.25)
    mix.click(b1 + ST.B1_BEATS[2] + 0.42, 0.22, -0.6, 2200, 0.03)    # the needle rests on the pin
    for k in range(7):                                    # the helmeted trout walks on, untroubled
        mix.step(b1 + 0.35 + 0.55 * k, 0.045, 0.3 - 0.06 * k, "water")
    # bolt 2 · "A little uncomfy."
    for k in range(3):                                    # the helmet shifted on its collar, three short tugs
        _squeak(mix, b2 + 1.08 + 0.625 * k, 0.2, 0.07, 0.15, 880 + 60 * k, 1250 - 90 * k)
        _bloop(mix, b2 + 1.3 + 0.625 * k, 260, 0.06, 0.15, 0.2, 1.5)
    for k in range(2):                                    # Turkey twists the same way, a beat later, under the low roof
        _squeak(mix, b2 + 2.08 + 0.625 * k, 0.16, 0.035, -0.5, 520, 700)
    for b in ST.B2_BEATS:
        _flutter(mix, b2 + b, 0.5, 0.13, -0.4)
        _puff(mix, b2 + b + 0.2, 5)
        _tick(mix, b2 + b + 0.25)
    # bolt 3 · "It is not wet."
    _flutter(mix, b3 + ST.B3_BEATS[0], 0.5, 0.13, -0.4)
    _puff(mix, b3 + ST.B3_BEATS[0] + 0.2, 6)
    _tick(mix, b3 + ST.B3_BEATS[0] + 0.25)
    a, bb = ST.B3_LIFT                                    # the river goes up like a blind: the cord runs, the batten knocks
    n = bb - a
    tt = mix.t(n)
    fr = lerp(170.0, 520.0, (tt / n) ** 1.4) * (1 + 0.03 * np.sin(2 * np.pi * 27 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 7)) * np.hanning(len(tt)) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 21 * tt)))
    mix.add(mix.band(x, 250, 2600), b3 + a, 0.06, 0.0)
    mix.step(b3 + bb, 0.4, 0.0, "wood")
    drop = ST._hem_passes(215) + 0.02                     # the bubbles that were rising stop and drop like pebbles
    for k in range(5):
        mix.step(b3 + drop + 0.42 + 0.07 * k, 0.16, -0.5 + 0.05 * k, "gravel")
    k = 0
    while True:                                           # each foot that lands on ground the river has left
        u = (0.25 + 0.5 * k) / ST.B3_PACE
        if u > ST.B3_LEN - 0.1:
            break
        if ST._hem(u) < w.GROUND - 30:
            mix.step(b3 + u, 0.24, 0.3 - 0.15 * k, "gravel")
        else:
            mix.step(b3 + u, 0.05, 0.3, "water")
        k += 1
    b = ST.B3_BEATS[1]                                    # he has not noticed: still beating, in a tin standing in dry air
    _flutter(mix, b3 + b, 0.5, 0.13, -0.4)
    _tick(mix, b3 + b + 0.25)

    # --- III. the trout think
    _turn(mix, C - FLIP, 0.14, 0.0)
    mix.click(C + 0.5, 0.22, -0.5, 2500, 0.04)            # the pick card
    mix.note(C + 0.7, 494, 0.3, 0.13, -0.5, "tri")        # the blue cross pressed
    _flutter(mix, C + SR.R0_BEATS[0], 0.45, 0.04, 0.4, muffled=True)
    _scratch(mix, C + 0.95, C + 1.2, 0.07, seed=1)        # N.'s cross: two strokes
    _scratch(mix, C + 1.24, C + 1.5, 0.07, seed=2)
    _scratch(mix, C + 1.0, C + 1.9, 0.045, seed=5, lo=700, hi=3000)      # the tin ringed in blue crayon
    for k in range(6):                                    # the button coloured in, zigzag
        _scratch(mix, C + 1.6 + 0.1 * k, C + 1.69 + 0.1 * k, 0.06, seed=k)
    _turn(mix, b4, 0.12, 0.0)
    _bolt(mix, 4, b4 + FLIP + 0.04)
    mix.drone(b4 + 0.3, SR.B4_LEN - 0.4, (49, 73.5, 98), 0.06, attack=0.8, release=0.8)     # the giant suit, hanging
    for b in SR.B4_BEATS:
        _flutter(mix, b4 + b, 0.5, 0.05, 0.3, muffled=True)
        _puff(mix, b4 + b + 0.2, 9, 0.2, 0.1)
        _tick(mix, b4 + b + 0.25, 0.12, 0.4)
    for k in range(9):                                    # the escort keeping station: tails
        mix.whoosh(b4 + 0.6 + 0.55 * k, 0.3, 0.022, -0.6 + 0.15 * (k % 5))
    _turn(mix, b5, 0.12, 0.0)                             # blank: the card and nothing else
    _turn(mix, b6, 0.12, 0.0)                             # blank: the card and nothing else

    # --- IV. the die is still in the cup
    _turn(mix, E, 0.14, 0.0)
    for n in WRITTEN:                                     # each written bolt lights with its own bell; 5 and 6 are silent
        mix.bell(lit_time(n), BELL[n], 2.8, 0.26, pan=-0.3 + 0.2 * (n - 1))
        mix.click(lit_time(n), 0.1, 0.0, 3000, 0.02)
    _bloop(mix, E + 0.7, 280, 0.05, -0.1, 0.22, 1.5)      # the water in the bowl, coming level
    _bloop(mix, E + 1.6, 250, 0.03, -0.1, 0.22, 1.4)
    for k in range(4):                                    # Turkey, small, behind the glass, has not stopped
        _flutter(mix, E + 2.9 + 0.7 * k, 0.3, 0.018 - 0.003 * k, -0.3, muffled=True)
    mix.reverb(0.1, 0.8)


def _sheet(times):
    d = HERE / "stills" / "c25"
    ims = [(t, Image.open(d / f"{t:06.2f}.png")) for t in times if (d / f"{t:06.2f}.png").exists()]
    if not ims:
        return
    cols = 4 if len(ims) > 9 else 3
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 20))
    for i, (t, im) in enumerate(ims):
        sheet.paste(im.resize((480, 270), Image.LANCZOS), ((i % cols) * 480, (i // cols) * 270))
        ImageDraw.Draw(sheet).text(((i % cols) * 480 + 6, (i // cols) * 270 + 4), f"{t:.2f}", fill=(255, 255, 0))
    sheet.save(d / "sheet.png")
    print("sheet ->", d / "sheet.png")


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        _sheet([float(x) for x in sys.argv[2:]])
