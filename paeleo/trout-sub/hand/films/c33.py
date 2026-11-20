"""c33 · class film for porthole 33 · Salon · "Velvet iris frame around culvert bar shadows".

The children's own sheet, in order, nothing added (see swarm/c33/board.md):
  0.0 .. 20.0   the pilot's page             swarm/c33/scene_pilot.py
 20.0 .. 39.0   Turkey thinks, bolts 1-3     swarm/c33/scene_turkey.py
 39.0 .. 50.9   the trout think, bolts 4-6   swarm/c33/scene_trout.py   (5 and 6 are blank on the sheet)
 50.9 .. 57.0   the die is still in the cup  (this file): bolts 1 to 4 light in turn, 5 and 6 stay dull; one die unthrown

Foraged: Turkey (Audubon) and the trout (Denton), see credits/c33.json. Everything else is handmade cut paper,
ruled card and pencil from swarm/c33/world.py. The porthole's rule (shadow theatre): every cut between scenes, the
editor's included, is the velvet iris of the clue, and the ending is first seen through that iris held half open.
Sound is synthesized with the kit's Mix: each written bolt has its own bell, heard when its ending begins and again
when the bolt lights at the end; a blank bolt gets one dead knock and no bell.

  python3 films/c33.py                      -> assets/films/c33.mp4 (+ .webp poster)
  python3 films/c33.py --stills 3 7.8 ...   -> films/stills/c33/*.png and sheet.png
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "swarm" / "c33"))

from kit import FPS, Film, clamp, ease, lerp, ramp  # noqa: E402
import world as Wd  # noqa: E402
import scene_pilot as SP  # noqa: E402
import scene_turkey as ST  # noqa: E402
import scene_trout as SR  # noqa: E402

ST.check()
SR.check()

T_TURKEY = SP.SECONDS                         # 20.0
T_TROUT = T_TURKEY + ST.SECONDS               # 39.0
T_END = T_TROUT + SR.SECONDS                  # 50.9
END_SECONDS = 6.1
SECONDS = T_END + END_SECONDS                 # 57.0
assert abs(SECONDS - 57.0) < 1e-6
T_TURKEY_IN = T_TURKEY + ST.PICK_HOLD         # 21.0: zero of the Turkey module's clock after its (held) pick
T_TROUT_IN = T_TROUT + SR.PICK_HOLD           # 40.0: the same for the trout module
IRIS = 0.2                                    # half an iris move: the modules' own measure

# The children's sentences, in the sheet's `reads` spelling, absolute times. One at a time, each 2.5 s or more.
# Each is trimmed clear of the velvet iris at both ends, so no sentence is read over a closed curtain.
CAPTIONS = [
    (8.8, 11.3, "A ship that sunk."),
    (11.75, 14.75, "Look in the window, trying to get out."),
    (15.25, 19.75, "He could be freaking out, trying to get out, losing air, breathing heavy."),
    (23.8, 27.7, "Someone trapped him."),
    (28.3, 32.7, "Trying to save a hot Cheeto."),
    (33.3, 38.6, "That's his home."),
    (42.7, 48.2, "A movie."),
]
_theirs = [s for m in (SP, ST, SR) for _, _, s in m.CAPTIONS]
assert [c[2] for c in CAPTIONS] == _theirs, "captions are the modules' sentences, in order, unchanged"
for _a, _b, _ in CAPTIONS:
    assert _b - _a >= 2.5 - 1e-9, (_a, _b)
for (_a, _b, _), (_c, _d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert _c >= _b, (_b, _c)

WRITTEN = (1, 2, 3, 4)
UNWRITTEN = (5, 6)                            # blank on the sheet: never lit, never rung, nothing invented
BOLT_AT = {1: T_TURKEY_IN + ST.S1, 2: T_TURKEY_IN + ST.S2, 3: T_TURKEY_IN + ST.S3,
           4: T_TROUT_IN + SR.S4, 5: T_TROUT_IN + SR.S5, 6: T_TROUT_IN + SR.S6}
BELL = {1: 523.25, 2: 587.33, 3: 659.25, 4: 783.99}


# ----------------------------------------------------------- the ending ---
E_C, E_R = (392, 250), 176                    # the brass porthole lying on the table
E_CUP = (800, 508)
E_LIT0, E_GAP = 0.9, 0.5                      # bolts 1 to 4 light in turn, clockwise
E_WIDE = (3.1, 3.9)                           # the iris opens the rest of the way: the table, the cup, the pencil
E_HOLD = 0.56                                # how far shut the iris is held in E1: its opening just clears the dice


def lit_time(n):
    return T_END + E_LIT0 + E_GAP * (n - 1)


def _ending(ink, e):
    Wd.table(ink, sheet=False)
    Wd.end_porthole(ink, E_C, E_R)
    for n in range(1, 7):                     # the written bolts light one after another; 5 and 6 stay dull brass
        if n in WRITTEN:
            a = lit_time(n) - T_END
            lit = ease(e, a, a + 0.3) * (0.93 + 0.07 * math.sin(e * 3.1 + n * 1.7))      # a slight glimmer, nothing more
        else:
            lit = 0.0
        Wd.bolt_mark(ink, n, lit=lit, c=E_C, r=E_R, size=34)
    Wd.pencil(ink, (548, 500), 8, lift=0.0, length=200)      # the pencil lies beside the cup
    Wd.die_cup(ink, E_CUP[0], E_CUP[1], 168)                  # the die rests in the cup. Nobody touches it.
    # the velvet iris opens on the porthole alone and is held there; then it opens on the whole table
    f = lerp(1.0, E_HOLD, ease(e, 0.0, 2 * IRIS))
    f = lerp(f, 0.0, ease(e, *E_WIDE))
    Wd.iris(ink, f, E_C, 600)


# ----------------------------------------------------------- the picture ---
def _picture(t, ink):
    if t < T_TURKEY:
        SP.draw(t, ink)
        if t > T_TURKEY - IRIS - 0.02:        # the join the pilot's module left open: the iris closes on his seat
            Wd.iris(ink, ease(t, T_TURKEY - IRIS, T_TURKEY), Wd.PORT_C, 600)
    elif t < T_TROUT:
        ST.draw(t - T_TURKEY, ink)
    elif t < T_END:
        SR.draw(t - T_TROUT, ink)
    else:
        _ending(ink, t - T_END)


film = Film("c33", SECONDS, boil=0, wobble=0.0)
film.poster_at = T_TURKEY_IN + ST.S2 + 2.4


@film.picture
def frame(t, ink):
    ink._grain = False                        # the paper's fibre is in the cut pieces; no grain laid over the frame
    _picture(t, ink)
    Wd.badge(ink)                             # on top of everything, the iris included
    for a, b, text in CAPTIONS:
        if a <= t < b:
            # bolt 4's audience sits along the bottom of the frame: its caption goes under the front row
            ink.caption(text, size=26, y=ink.h - 33 if a >= T_TROUT else None)
            break


# --------------------------------------------------------------- sound ---
def _scratch(mix, a, b, gain=0.07, seed=0, lo=1800, hi=7000, pan=None):
    """Pencil on paper: a band of noise that swells along the stroke."""
    n = max(0.06, b - a)
    x = mix.band(mix.noise(n), lo, hi)
    tt = mix.t(n)[: len(x)]
    x = x[: len(tt)] * (0.55 + 0.45 * np.sin(2 * np.pi * (5 + seed % 3) * tt + seed)) * np.hanning(len(tt)) ** 0.5
    mix.add(x, a, gain, pan=-0.2 + 0.1 * (seed % 5) if pan is None else pan)


def _velvet(mix, at, close=True, opens=True, gain=0.1, half=IRIS):
    """The velvet iris: cloth leaves drawn shut over `half` seconds up to `at`, and open again after it."""
    for on, a in ((close, at - half), (opens, at)):
        if not on:
            continue
        n = half + 0.06
        tt = mix.t(n)
        x = mix.band(mix.noise(n), 250, 2400)[: len(tt)] * np.hanning(len(tt)) ** 1.5
        mix.add(x, max(0.0, a), gain, 0.0)
    if close:
        mix.thud(at - 0.01, 95, gain * 1.1, 0.0, 0.1)          # the leaves meet


def _breath(mix, at, gain=0.05, pan=-0.35, muffled=False):
    """One heavy breath: a quick gasp in, a slower sigh out."""
    hi = 900 if muffled else 2600
    tt = mix.t(0.14)
    x = mix.band(mix.noise(0.14), 500, hi + 600)[: len(tt)] * (tt / 0.14) ** 1.5 * np.hanning(len(tt)) ** 0.3
    mix.add(x, at, gain, pan)
    tt = mix.t(0.3)
    x = mix.band(mix.noise(0.3), 250, hi)[: len(tt)] * np.exp(-tt * 9) * np.sin(np.pi * np.minimum(1, tt / 0.04) / 2)
    mix.add(x, at + 0.15, gain * 0.8, pan)


def _breaths(mix, a, b, gain=0.05, pan=-0.35, muffled=False, swell=0.0):
    k = math.ceil(a * Wd.BREATH_HZ - 1e-9)
    while k / Wd.BREATH_HZ < b - 0.3:
        tk = k / Wd.BREATH_HZ
        _breath(mix, tk, gain * (1 + swell * ramp(tk, a, b)), pan, muffled)
        k += 1


def _bloop(mix, at, f=420.0, gain=0.12, pan=0.0, seconds=0.15, up=1.9):
    """A bubble."""
    tt = mix.t(seconds)
    fr = f * (1 + (up - 1) * (tt / seconds) ** 1.6)
    x = np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7
    mix.add(x, at, gain, pan)


def _tick(mix, at, gain=0.17, pan=0.6):
    """The gauge needle dropping one notch."""
    mix.click(at, gain, pan, 7000, 0.015)
    mix.note(at, 1180, 0.09, gain * 0.35, pan, "sine", decay=0.06, sustain=0.0)
    for q in range(4):                                        # and the air that went: a bead out of the cracks
        _bloop(mix, at + 0.06 + 0.05 * q, 520 + 90 * ((q * 3) % 4), 0.05, -0.1 + 0.15 * q, 0.1)


def _knock(mix, at, gain=0.2, pan=-0.35, muffled=False):
    """Turkey shoving the glass from inside the tin: wing knuckles on brass, the tin's dull body under it."""
    mix.thud(at, 150 if muffled else 185, gain, pan, 0.14)
    if not muffled:
        mix.click(at + 0.005, gain * 0.5, pan, 2200, 0.03)
    mix.note(at, 310, 0.16, gain * 0.16, pan, "sine", decay=0.12, sustain=0.0)


def _scrape(mix, a, b, f0=240.0, f1=120.0, gain=0.07, pan=0.3, chop=23):
    """Card or iron dragged along its guide: a chopped, falling rasp."""
    n = b - a
    tt = mix.t(n)
    fr = lerp(f0, f1, tt / n) * (1 + 0.03 * np.sin(2 * np.pi * 31 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 8)) * np.hanning(len(tt)) ** 0.6
    x *= 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * chop * tt))
    mix.add(mix.band(x, 150, 2600), a, gain, pan)


def _squeak(mix, at, seconds=0.2, gain=0.05, pan=-0.2, f0=900.0, f1=1300.0):
    """A wing dragged down wet glass."""
    tt = mix.t(seconds)
    fr = lerp(f0, f1, tt / seconds) * (1 + 0.02 * np.sin(2 * np.pi * 31 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.hanning(len(tt))
    mix.add(x, at, gain, pan)


def _fizz(mix, a, b, gain=0.03, pan=0.1):
    """Something hot in cold water."""
    n = b - a
    tt = mix.t(n)
    x = mix.band(mix.noise(n), 3500, 9000)[: len(tt)]
    x *= (0.55 + 0.45 * np.sin(2 * np.pi * 7.3 * tt) * np.sin(2 * np.pi * 1.9 * tt)) * mix.env(len(tt), 0.3, 0.01, 1.0, 0.5)
    mix.add(x, a, gain, pan)


def _bolt(mix, n, at, gain=0.28):
    """A written bolt's own mark: the die clicks down, then the bolt's bell."""
    mix.click(at, 0.2, 0.0, 3000, 0.03)
    mix.bell(at + 0.02, BELL[n], 2.4, gain, pan=-0.3 + 0.2 * (n - 1))


@film.sound
def sound(mix):
    # B0 / C0: where each friend's module starts (the pick). B / C: zero of that module's clock after the held pick.
    B0, C0, E = T_TURKEY, T_TROUT, T_END
    B, C = T_TURKEY_IN, T_TROUT_IN
    b1, b2, b3, b4, b5, b6 = (BOLT_AT[n] for n in range(1, 7))
    seat1 = B + ST.T_SEAT                                     # 23.1: Turkey's seat again
    river = C + SR.T_RIVER                                    # 42.05: the river side

    # beds: the room over the table; the river from outside; dull from inside the tin; the room again
    mix.room(0.0, SP.T_SWAP + 0.1, 0.02)
    mix.water(SP.T_SWAP, SP.T_P6 - SP.T_SWAP, 0.045)
    mix.water(SP.T_P6, B0 - SP.T_P6, 0.016)
    mix.drone(SP.T_P6, B0 - SP.T_P6, (55, 82.5, 110), 0.035, attack=0.4, release=0.4)
    mix.room(B0, seat1 - B0, 0.02)
    mix.water(seat1, C0 - seat1, 0.016)
    mix.drone(seat1, C0 - seat1, (55, 82.5, 110), 0.035, attack=0.4, release=0.4)
    mix.room(C0, river - C0, 0.02)
    mix.water(river, E - river, 0.045)
    mix.room(E, END_SECONDS, 0.022)

    # every change of scene is the velvet iris
    _velvet(mix, SP.T_SWAP)
    _velvet(mix, SP.T_P5)
    _velvet(mix, SP.T_P6)
    for a in (B0, seat1, b2, b3, C0, river, b5):
        _velvet(mix, a)
    _velvet(mix, b6, gain=0.07, half=SR.IRIS_Q)
    _velvet(mix, E, opens=False)
    _velvet(mix, E + 0.2, close=False, half=0.3)              # opens on the porthole alone
    _velvet(mix, E + E_WIDE[0] + 0.25, close=False, half=0.5, gain=0.08)      # and then on the table

    # --- I. the pilot's page
    mix.click(1.12, 0.1, 0.2, 3500, 0.02)                     # the pencil touches down
    for k, (g, (a, b)) in enumerate(Wd.PILOT_TIMES.items()):
        n = 3 if g.startswith("bar") else {"fish": 3, "spots": 9, "cracks": 5}.get(g, 1)
        a, b = SP.stroke_time(a), SP.stroke_time(b)           # the pencil's own (quicker) clock
        for j in range(n):                                    # each bar: two downstrokes and the side-of-the-lead fill
            aa, bb = a + (b - a) * j / n, a + (b - a) * (j + 1) / n - 0.02
            if g == "spots":
                mix.click(aa + 0.01, 0.1, 0.1, 5000, 0.015)   # a dot is a tap
            else:
                _scratch(mix, aa, bb, 0.085 if g in ("bar4", "bar5", "bar8", "bar9") else 0.06, seed=k * 3 + j)
    mix.step(SP.T_RING[1], 0.3, 0.0, "wood")                  # the brass ring set down over the page
    mix.note(SP.T_RING[1], 880, 0.5, 0.05, 0.0, "sine", decay=0.4, sustain=0.0)
    mix.whoosh(SP.T_PUSH[0], SP.T_PUSH[1] - SP.T_PUSH[0], 0.07)       # through the glass
    mix.thud(9.97, 55, 0.4, -0.3, 0.5)                        # "A ship that sunk.": the tin settles a hand's width
    _scrape(mix, 9.95, 10.5, 150, 70, 0.06, -0.3, 13)
    for q in range(7):                                        # mud rolls off, a thread of bubbles from the seam
        _bloop(mix, 10.2 + 0.16 * q, 260 + 50 * (q % 3), 0.05, -0.3 + 0.05 * q, 0.16, 1.6)
    for k in range(3):                                        # "Look in the window, trying to get out.": three shoves
        _knock(mix, 12.55 + 0.8 * k, 0.3, 0.0)
        mix.thud(12.6 + 0.8 * k, 60, 0.16, 0.0, 0.3)          # the tin rocks a degree on the bed
    _breaths(mix, 12.4, SP.T_P6 - 0.2, 0.02, 0.0, muffled=True)
    _breaths(mix, SP.T_P6, B0 - 0.1, 0.06, -0.35, swell=0.5)   # "... losing air, breathing heavy."
    for tk in SP.TICKS:
        _tick(mix, tk + 0.1)
    for k in range(int(SP.T_P6) + 1, int(B0)):
        _knock(mix, k, 0.1)

    # --- II. Turkey thinks
    _scratch(mix, B0 + 0.3, B0 + 1.15, 0.07, seed=1, lo=1200, hi=5000)        # the red circle coloured in, round and round
    mix.click(B0 + 1.2, 0.2, -0.3, 2500, 0.04)                # the button goes down
    mix.note(B0 + 1.22, 440, 0.3, 0.12, -0.3, "tri")
    _scratch(mix, B0 + 1.42, B0 + 1.82, 0.08, seed=2)         # E.'s one small circle
    for k in range(16):                                       # the stones of the tunnel mouth, laid one by one
        mix.step(seat1 + 0.27 + k * (B + 3.3 - seat1 - 0.3) / 16, 0.09, -0.5 + k / 16, "stone")
    for n in (1, 2, 3):
        _bolt(mix, n, BOLT_AT[n] + (0.0 if n == 1 else IRIS))
    _breaths(mix, seat1 + 0.2, b2 - 0.2, 0.045)
    _breaths(mix, b2 + 0.2, b3 - 0.2, 0.06, swell=0.5)        # the hardest breathing of the film
    _breaths(mix, b3 + 0.2, C0 - 0.3, 0.05, swell=0.3)
    for k in range(int(seat1) + 1, int(C0)):                  # he shoves once a second; he never stops
        if abs(k - b2) > 0.3 and abs(k - b3) > 0.3 and not (b2 + 0.6 < k < b2 + 3.6):
            _knock(mix, k, 0.2 if B + 4.95 <= k < b2 else 0.1)
    # bolt 1 · "Someone trapped him."
    _scrape(mix, B + 3.3, B + 4.2, 260, 130, 0.08, 0.3)       # the ninth bar slid down into the gap
    mix.thud(B + 4.2, 90, 0.4, 0.3, 0.2)
    mix.click(B + 4.2, 0.22, 0.3, 1800, 0.04)
    mix.click(B + 5.08, 0.35, 0.1, 5000, 0.025)               # the padlock shuts
    mix.note(B + 5.08, 1400, 0.12, 0.07, 0.1, "sine", decay=0.08, sustain=0.0)
    for q in range(4):                                        # and swings on the crossbar
        mix.click(B + 5.3 + 0.4 * q, 0.07 * 0.7 ** q, 0.1, 3000, 0.02)
    _tick(mix, B + 5.6)
    # bolt 2 · "Trying to save a hot Cheeto."
    _fizz(mix, B + ST.SINK0, b3 - 0.1, 0.03)
    mix.whoosh(B + 7.6, 0.35, 0.1, -0.3)                      # he slams up the pane
    _knock(mix, B + 7.93, 0.3)
    for q in range(6):                                        # one wing down the glass, keeping pace with it
        _squeak(mix, B + 8.2 + 0.4 * q, 0.26, 0.04, -0.2 + 0.05 * q, 1150 - 70 * q, 820 - 50 * q)
    mix.click(B + ST.SINK1, 0.14, 0.1, 2500, 0.03)            # it lodges on the crossbar
    _tick(mix, B + 8.6)
    _tick(mix, B + 10.6)
    # bolt 3 · "That's his home."
    _scrape(mix, B + 13.1, B + 13.7, 420, 620, 0.035, 0.1, 37)        # the gate opens to its nose
    mix.click(B + 14.45, 0.2, -0.2, 4500, 0.02)               # the lamp comes on
    mix.note(B + 14.47, 660, 0.6, 0.05, -0.2, "sine", decay=0.5, sustain=0.0)
    mix.whoosh(B + 15.05, 0.9, 0.035, 0.0)                    # once round in the armchair
    for q in range(5):                                        # the curtains drawn, ring by ring
        mix.click(B + 16.2 + 0.2 * q, 0.07, -0.3 + 0.15 * q, 3500, 0.02)
    mix.whoosh(B + 16.15, 1.1, 0.06, 0.0)
    _scrape(mix, B + 16.9, B + 17.5, 600, 420, 0.03, 0.1, 37)         # the gate swings to
    for tk in (13.5, 15.0, 16.5):
        _tick(mix, B + tk + 0.1)

    # --- III. the trout think
    for k in range(7):                                        # the pink square coloured in, corner to corner
        _scratch(mix, C0 + 0.35 + 0.135 * k, C0 + 0.47 + 0.135 * k, 0.07, seed=k)
    mix.click(C0 + 1.4, 0.2, 0.3, 2500, 0.04)
    mix.note(C0 + 1.42, 554, 0.3, 0.12, 0.3, "tri")           # the button goes down
    _bolt(mix, 4, b4)
    k = 0
    while river + 0.2 + k / 12.0 < b5 - 0.25:                 # "A movie.": the hand-cranked clatter of the picture
        tk = river + 0.2 + k / 12.0
        mix.click(tk, 0.035 * (1 if k % 4 else 1.7) * ramp(tk, river + 0.2, river + 1.0), 0.5, 2400, 0.012)
        k += 1
    _breaths(mix, river + 0.2, b5 - 0.3, 0.03, -0.5, muffled=True)
    for k in range(int(river) + 1, int(b5) + 1):
        _knock(mix, k, 0.1, -0.5, muffled=True)
    for q in range(9):                                        # the rows swim in and settle: tails
        mix.whoosh(river + 0.3 + 0.33 * q, 0.3, 0.025, -0.6 + 0.15 * q)
    _tick(mix, C + SR.TICK + 0.1, 0.12, -0.5)
    for n in UNWRITTEN:                                       # blank: one dead knock as the die is set on an empty stage
        mix.thud(BOLT_AT[n] + (IRIS if n == 5 else SR.IRIS_Q), 110, 0.22, 0.0, 0.12)

    # --- IV. the die is still in the cup
    for n in WRITTEN:                                         # each written bolt lights with its own bell; 5 and 6 are silent
        mix.bell(lit_time(n), BELL[n], 3.0, 0.26, pan=-0.3 + 0.2 * (n - 1))
        mix.click(lit_time(n), 0.1, 0.0, 3000, 0.02)
    mix.reverb(0.1, 0.8)


def _sheet(times):
    d = HERE / "stills" / "c33"
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
