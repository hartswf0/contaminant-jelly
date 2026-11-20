"""c16 · class film for porthole 16 · Aft · "Identical twin Turkey Sub waving back".

The children's own sheet, in order, nothing added (see swarm/c16/board.md):
  0.0 .. 20.0   the pilot's page                     swarm/c16/scene_pilot.py
 20.0 .. 32.0   Turkey thinks: bolts 1, 2 blank, 3   swarm/c16/scene_turkey.py
 32.0 .. 44.2   the trout think: 4 blank, 5, 6 blank swarm/c16/scene_trout.py
 44.2 .. 52.0   the die is still in the cup (this file): the six bolts are checked in turn, 3 and 5 lit, 1, 2, 4
                and 6 left as empty outlines; one die resting in its cup, not thrown

Everything on screen is handmade cut paper and pencil from swarm/c16/world.py; nothing is foraged (credits/c16.json
is an empty list). Sound is synthesized with the kit's Mix.

The porthole's rule (Temporal Double, D = 12 frames) is kept by the editor too:
  - the joins: pilot -> Turkey is one continuous shot (same camera, same wave); Turkey -> trout is a straight cut on
    the shoulder pin (a drawing substitution, never tweened); trout -> table is a dissolve exactly D frames long,
    the one place two times share the screen;
  - the ending: each bolt's die face arrives as a pencil outline, and the painted, lit double lands D frames later
    ONLY where an ending was written. An unwritten bolt keeps its outline: its double never comes;
  - the sound: every sound is heard twice, the second time D frames later and quieter. A written bolt is a bell and
    its late double; an unwritten bolt is one dead knock on wood with no double at all. The die makes no sound.

  python3 films/c16.py                      -> assets/films/c16.mp4 (+ .webp poster)
  python3 films/c16.py --stills 3 7.8 ...   -> films/stills/c16/*.png and sheet.png
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
sys.path.insert(0, str(HERE / "swarm" / "c16"))

from kit import Film  # noqa: E402
import world as Wd  # noqa: E402
import scene_pilot as SP  # noqa: E402
import scene_turkey as ST  # noqa: E402
import scene_trout as SR  # noqa: E402

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp
DT = Wd.DT                                    # the double's delay: 12 frames

T_TURKEY = SP.SECONDS                         # 20.0
T_TROUT = T_TURKEY + ST.SECONDS               # 32.0
T_END = T_TROUT + SR.SECONDS                  # 44.2
END_SECONDS = 7.8
SECONDS = T_END + END_SECONDS                 # 52.0
assert abs(T_TURKEY - ST.T0) < 1e-9 and abs(T_TROUT - SR.T0) < 1e-9 and abs(SECONDS - 52.0) < 1e-6

# The children's sentences, in the sheet's `reads` spelling, absolute times. One at a time, each 2.5 s or more.
GAP = 0.2                                     # a breath of clear picture between two captions that would touch


def _captions():
    raw = [(a, b, s) for a, b, s in SP.CAPTIONS] + \
          [(T_TURKEY + a, T_TURKEY + b, s) for a, b, s in ST.CAPTIONS] + \
          [(T_TROUT + a, T_TROUT + b, s) for a, b, s in SR.CAPTIONS]
    out = []
    for k, (a, b, s) in enumerate(raw):
        if k + 1 < len(raw) and raw[k + 1][0] < b + GAP:
            b = raw[k + 1][0] - GAP           # trim the earlier one
        out.append((round(a, 3), round(b, 3), s))
    return out


CAPTIONS = _captions()
assert [s for _, _, s in CAPTIONS] == ["A giant three-headed monster.", "Wave at his twin turkey.", "Using up his energy.",
                                       "There is another turkey here.", "Two-headed tin monster fits the submarine."]
for a, b, _ in CAPTIONS:
    assert b - a >= 2.5 - 1e-9, (a, b)
for (a, b, _), (c, d, _) in zip(CAPTIONS, CAPTIONS[1:]):
    assert c >= b + GAP - 1e-9, (b, c)
assert CAPTIONS[-1][1] <= T_END

WRITTEN = (3, 5)                              # "There is another turkey here." / "Two-headed tin monster fits the submarine."
UNWRITTEN = (1, 2, 4, 6)                      # blank on the sheet (bolt 1 rubbed out and unreadable): never invented
BOLT_AT = {1: ST.T_B1, 2: ST.T_B2, 3: ST.T_B3, 4: SR.T_C1, 5: SR.T_C2, 6: SR.T_C3}       # film seconds
BELL = {1: 523.25, 2: 587.33, 3: 659.25, 4: 698.46, 5: 783.99, 6: 880.0}

# ----------------------------------------------------------- the ending ---
E_MIX = DT                                    # the dissolve from the last blank to the table: exactly D frames
E_BOLT0, E_STEP = 0.6, DT                     # bolt n is checked at T_END + E_BOLT0 + E_STEP * (n - 1)
E_CUP = 3.8                                   # 48.0: the die has not been thrown
E_BUB = 3.6                                   # the last pair of bubbles is let go; gone by about 50.0
PORT_E = (380, 262)
R_IN, R_OUT = 150, 196
CUP = (790, 470)


def check_time(n):
    """Film time at which bolt n's outline is pencilled in the ending (its lit double, if any, lands DT later)."""
    return T_END + E_BOLT0 + E_STEP * (n - 1)


assert check_time(6) + DT <= T_END + E_CUP + 1e-9


@lru_cache(None)
def _end_plate():
    """The table, the porthole face-on, its glass dark and still, and the cup with the die in its mouth. It never moves."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    Wd.table(img)
    ring = Wd.brass_ring(R_IN, R_OUT, fittings=True)
    cx, cy = PORT_E
    Wd._comp(img, Wd.shadow_of(ring.getchannel("A"), 9, 0.6), (cx - ring.width / 2 + 7, cy - ring.height / 2 + 11))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R_IN - 2, cy - R_IN - 2, cx + R_IN + 2, cy + R_IN + 2], fill=(14, 30, 30))
    Wd._comp(img, ring, (cx - ring.width / 2, cy - ring.height / 2))
    Wd.die_cup_side(img, CUP[0], CUP[1])
    return img


def _ending(tgt, e):
    Wd._comp(tgt, _end_plate().convert("RGBA"), (0, 0))
    # the last pair of bubbles from the tin's pipe rises past behind the glass and is gone
    Wd.bubble_pair(tgt, PORT_E[0] - 18, PORT_E[1] + 124, e, E_BUB, rise=236, size=8, drift=9, life=1.7, seed=4)
    g = ease(e, E_CUP, E_CUP + 0.8)
    if g > 0:                                 # the light comes round to the cup; the cup and the die do not move
        Wd.glow(tgt, CUP[0], CUP[1] - 130, 190, (255, 232, 170), 0.8 * g)
        Wd.die_cup_side(tgt, CUP[0], CUP[1])
    for n in range(1, 7):
        s = Wd.arrive(T_END + e, check_time(n))
        if not s:
            continue
        if n in WRITTEN and s == 2:           # written: the painted, lit double lands on its outline
            bx, by = Wd.bolt_xy(n, PORT_E[0], PORT_E[1], R_IN, R_OUT)
            Wd.glow(tgt, bx, by, 84, (255, 196, 90), 0.9 * ease(e, check_time(n) - T_END + DT, check_time(n) - T_END + DT + 0.4))
            Wd.die_at_bolt(tgt, n, PORT_E, R_IN, size=40, lit=True, outline=False, t=0.0, ring_w=R_OUT - R_IN)
        else:                                 # unwritten: the outline is all there ever is
            Wd.die_at_bolt(tgt, n, PORT_E, R_IN, size=40, lit=False, outline=True, ring_w=R_OUT - R_IN)


@lru_cache(None)
def _last_trout():
    img = Image.new("RGB", (W, H), (0, 0, 0))
    SR.draw(SR.SECONDS - 1e-3, img)
    return img


# ---------------------------------------------------------------- film ---
film = Film("c16", SECONDS, boil=0, wobble=0.0)
film.poster_at = 40.0                         # bolt 5 seated: rim on rim, Turkey still waving in the porthole


@film.picture
def frame(t, ink):
    ink._grain = False            # the paper's fibre is in the cut pieces themselves; no grain laid over the frame
    if t < T_TURKEY:
        SP.draw(t, ink)
    elif t < T_TROUT:
        ST.draw(t - T_TURKEY, ink)
    elif t < T_END:
        SR.draw(t - T_TROUT, ink)
    else:
        e = t - T_END
        _ending(ink, e)
        if e < E_MIX:                         # two times on screen at once, for D frames
            a = 1 - ease(e, 0.0, E_MIX)
            now = ink.img.convert("RGB")
            ink.img.paste(Image.blend(now, _last_trout(), a).convert(ink.img.mode), (0, 0))
    Wd.badge(ink)
    for a, b, text in CAPTIONS:
        if a <= t < b:
            ink.caption(text, size=27)
            break


# --------------------------------------------------------------- sound ---
ECHO = 0.5                                    # the double is this much of the first


def twice(fn, at, *args, gain=0.1, pan=0.0, **kw):
    """The rule, for the ear: the sound now, and its double D frames later, quieter, from the other side."""
    fn(at, *args, gain=gain, pan=pan, **kw)
    fn(at + DT, *args, gain=gain * ECHO, pan=-pan, **kw)


def make_sound(mix):
    def scratch(a, b, gain=0.07, pan=-0.1, seed=0):
        """Pencil on paper: a band of noise that swells along the stroke."""
        n = max(0.06, b - a)
        x = mix.band(mix.noise(n), 1800, 7000)
        tt = mix.t(n)[: len(x)]
        x = x[: len(tt)] * (0.55 + 0.45 * np.sin(2 * np.pi * (5 + seed % 3) * tt + seed)) * np.hanning(len(tt)) ** 0.5
        mix.add(x, a, gain, pan)

    def bloop(at, f=420.0, gain=0.12, pan=0.0, seconds=0.16, up=1.9):
        """A bubble."""
        tt = mix.t(seconds)
        fr = f * (1 + (up - 1) * (tt / seconds) ** 1.6)
        mix.add(np.sin(2 * np.pi * np.cumsum(fr) / mix.rate) * np.hanning(len(tt)) ** 0.7, at, gain, pan)

    def tick(at, gain=0.12, pan=-0.6):
        """The air needle, one tick."""
        mix.click(at, gain, pan, 7000, 0.015)

    def flap(at, gain=0.1, pan=0.4, seconds=0.42):
        """One wave of a wing: soft air and feathers."""
        mix.whoosh(at - seconds * 0.6, seconds, gain, pan)

    def creak(at, gain=0.07, pan=0.0, f0=120.0, f1=84.0, seconds=0.6):
        """Something very large turning its head."""
        tt = mix.t(seconds)
        fr = lerp(f0, f1, tt / seconds) * (1 + 0.05 * np.sin(2 * np.pi * 19 * tt))
        ph = 2 * np.pi * np.cumsum(fr) / mix.rate
        x = sum(np.sin(k * ph) / k for k in range(1, 7)) * np.hanning(len(tt))
        mix.add(mix.band(x, 60, 900), at, gain, pan)

    def clink(at, gain=0.4, pan=0.0):
        """Tin on tin: rims meeting."""
        mix.thud(at, 150, gain * 0.7, pan, 0.16)
        mix.click(at, gain * 0.6, pan, 5200, 0.04)
        mix.bell(at, 1480, 0.7, gain * 0.25, pan)

    def knock(at, n, gain=0.3, pan=0.0):
        """An unwritten bolt: one dead knock on wood. No ring, no double."""
        tt = mix.t(0.08)
        mix.add(np.sin(2 * np.pi * BELL[n] * 0.25 * tt) * np.exp(-tt * 65), at, gain, pan)
        mix.click(at, gain * 0.45, pan, 1400, 0.03)

    def bell(at, n, gain=0.28, pan=0.0):
        mix.click(at, gain * 0.5, pan, 3000, 0.03)
        mix.bell(at + 0.01, BELL[n], 2.4, gain, pan)

    return scratch, bloop, tick, flap, creak, clink, knock, bell


def _energy(tt):
    return SP.energy(tt) if tt < T_TURKEY else ST.energy(tt) if tt < T_TROUT else SR.energy(tt)


def _in_view(tt):
    """Is Turkey on screen (not a blank, not the table)?"""
    return (SP.T_A3 <= tt < ST.T_B1) or (ST.T_B3 <= tt < SR.T_C1) or (SR.T_C2 <= tt < SR.T_C3)


@film.sound
def sound(mix):
    scratch, bloop, tick, flap, creak, clink, knock, bell = make_sound(mix)
    A2, B, C, E = SP.T_A2, T_TURKEY, T_TROUT, T_END
    bolt_pan = {n: 0.5 * math.sin(math.radians((n - 1) * 60)) for n in range(1, 7)}

    # beds: the room over the table; the tin's hum and the river through thick glass from the seat; the open river
    mix.room(0.0, A2 + 0.6, 0.022)
    mix.room(E - 0.2, END_SECONDS + 0.2, 0.022)
    for a, b in ((A2 + DT, ST.T_B1), (ST.T_B3, C)):                    # SEAT (the blanks are silent stages)
        mix.water(a, b - a, 0.022)
        mix.drone(a, b - a, (55, 82.5, 110), 0.045, attack=0.5, release=0.3)
    for a, b in ((C, SR.T_C1), (SR.T_C2, SR.T_C3)):                    # RIVER
        mix.water(a, b - a, 0.05)
    for a, b in ((ST.T_B1, ST.T_B3), (SR.T_C1, SR.T_C2), (SR.T_C3, E)):
        mix.room(a, b - a, 0.012)

    # --- A1: the pencil. The window's scribble is heard twice, D frames apart (it is why it is so dark).
    for k, (part, (a, b)) in enumerate(Wd.PILOT_TIMES.items()):
        faint = part in ("faint", "head")
        if part == "head":                                             # head, beak, eye, wattle, the two neck lines
            for j, (u0, u1) in enumerate(((0.0, 0.3), (0.33, 0.47), (0.5, 0.54), (0.58, 0.7), (0.74, 0.86), (0.89, 1.0))):
                scratch(lerp(a, b, u0), lerp(a, b, u1), 0.045, 0.3, seed=20 + j)
        else:
            scratch(a + 0.02, b - 0.02, 0.05 if faint else 0.09 if part.startswith("scribble") else 0.075, -0.1 + 0.05 * k, seed=k)
        mix.click(a + 0.02, 0.03, 0.0, 3000, 0.012)
    mix.whoosh(SP.T_PUSH[0], SP.T_PUSH[1] - SP.T_PUSH[0], 0.07, 0.0)   # down into the ring
    scratch(SP.T_RIM, SP.T_RIM + 0.42, 0.08, 0.0, seed=7)              # the pencil ring ...
    mix.thud(SP.T_PAINT, 90, 0.4, 0.0, 0.3)                            # ... and its brass double lands D frames later
    mix.bell(SP.T_PAINT, 392, 1.8, 0.12, 0.0)

    # --- A2: three heads rise, one after another, D apart
    for k in range(3):
        at = SP.T_HEADS + k * DT
        mix.whoosh(at, SP.RISE, 0.09 * (1 - 0.15 * k), (-0.5, 0.0, 0.5)[k])
        creak(at + SP.RISE - 0.25, 0.1 * (1 - 0.15 * k), (-0.5, 0.0, 0.5)[k], 110 - 12 * k, 78 - 8 * k, 0.7)
    twice(mix.click, SP.T_A3, bright=2500, seconds=0.03, gain=0.16, pan=0.2)          # the twin's window lights
    mix.note(SP.T_A3 + 0.05, 880, 0.3, 0.05, 0.2, "sine", decay=0.2, sustain=0.0)

    # --- the wave: every beat from 13.5, Turkey now and the twin D frames later; each one a pair of bubbles
    peaks = [13.5 + k for k in range(30)]
    for k, tp in enumerate(peaks):
        if not _in_view(tp):
            continue
        en = _energy(tp)
        river = tp >= C
        twice(flap, tp, gain=(0.05 + 0.09 * en) * (0.7 if river else 1.0), pan=0.45 if not river else -0.3,
              seconds=0.36 + 0.3 * (1 - en))                           # lower and slower as the energy goes
        twice(bloop, tp + 0.12, 380 + 30 * (k % 5), gain=0.07, pan=0.25)
    # the second turkey's own wing, inside the tin, from the left
    flap(ST.T_OTHER + 0.45, 0.16, -0.6, 0.6)
    mix.thud(ST.T_OTHER + 0.45, 180, 0.12, -0.6, 0.1)                  # it brushes the brass
    twice(mix.click, ST.T_HEAD, bright=2200, seconds=0.03, gain=0.14, pan=0.5)        # Turkey's head: one drawing for the other
    # --- the air: each drop is two ticks, D apart
    for d in SP.DROPS + ST.DROPS + SR.PEAKS:
        if _in_view(d) or _in_view(d - 0.01):
            twice(tick, d, gain=0.13, pan=-0.6)

    # --- B0: the pick
    scratch(B + 0.3, B + 0.3 + 0.4, 0.07, -0.2, seed=3)                # the card's outline ...
    mix.thud(ST.T_CARD + DT, 200, 0.14, -0.2, 0.09)                    # ... and its painted double
    for j in range(3):                                                 # B.'s triangle: left side, right side, base
        a = lerp(ST.T_MARK[0], ST.T_MARK[1], j / 3)
        scratch(a + 0.02, a + 0.29, 0.07, 0.3, seed=30 + j)
    twice(mix.note, ST.T_PRESS, freq=523.25, seconds=0.3, gain=0.13, pan=-0.3)      # the green triangle pressed
    mix.click(ST.T_PRESS, 0.2, -0.3, 2500, 0.04)
    x = mix.band(mix.noise(1.6), 200, 1400) * np.hanning(int(1.6 * mix.rate))[: int(1.6 * mix.rate)]
    mix.add(x, ST.T_RIPPLE, 0.06)                                      # the pond takes one slow ripple

    # --- the bolts as they come up: a written one is pencilled, then rings D frames later
    for n in range(1, 7):
        at = BOLT_AT[n]
        if n in WRITTEN:
            scratch(at + 0.03, at + 0.4, 0.06, bolt_pan[n], seed=40 + n)
            twice(bell, at + DT, n, gain=0.28, pan=bolt_pan[n])
        else:                                                          # a blank has no outline-then-double: the die
            knock(at + 0.04, n, 0.3, bolt_pan[n])                      # face is simply there, and one dead knock

    # --- B3: the heads tilt to look at the second one, D apart
    for k in range(3):
        creak(ST.T_TILT + k * DT, 0.08, (-0.5, 0.0, 0.5)[k], 104 - 10 * k, 80 - 8 * k, 0.6)

    # --- C0: the cut to the river; the pick
    mix.whoosh(C - 0.05, 0.3, 0.07, 0.0)
    scratch(SR.T_CARD, SR.T_CARD + 0.4, 0.07, -0.2, seed=5)
    mix.thud(SR.T_CARD + DT, 200, 0.14, -0.2, 0.09)
    scratch(SR.T_MARK[0] + 0.02, SR.T_MARK[1] - 0.02, 0.07, 0.0, seed=6)    # W.'s one wobbly loop
    twice(mix.note, SR.T_PRESS, freq=587.33, seconds=0.3, gain=0.13, pan=-0.3)      # the blue cross pressed
    mix.click(SR.T_PRESS, 0.2, -0.3, 2500, 0.04)
    twice(mix.whoosh, C + 0.2, seconds=0.9, gain=0.05, pan=0.6)                # the pair of trout come in

    # --- C2: the two-headed tin monster comes down over the submarine and seats, rim on rim
    a, b = SR.T_DROP
    tt = mix.t(b - a)
    fr = lerp(300, 140, (tt / (b - a)) ** 0.8) * (1 + 0.03 * np.sin(2 * np.pi * 17 * tt))
    ph = 2 * np.pi * np.cumsum(fr) / mix.rate
    x = sum(np.sin(k * ph) / k for k in range(1, 6)) * np.hanning(len(tt)) ** 0.6
    mix.add(mix.band(x, 150, 1800), a, 0.05, -0.3)
    mix.whoosh(a, b - a, 0.08, -0.3)
    twice(clink, SR.T_SEAT, gain=0.45, pan=-0.3)                       # the seating, and the second look at it
    mix.thud(SR.T_SEAT, 60, 0.4, -0.3, 0.4)
    for k in range(6):                                                 # the ring of bubbles where the rims meet
        twice(bloop, SR.T_SEAT + 0.06 + 0.05 * k, 320 + 60 * k, gain=0.07, pan=-0.6 + 0.2 * k)
    twice(mix.whoosh, SR.T_SEAT - 0.1, seconds=0.5, gain=0.05, pan=0.6)        # the trout dart in for a look
    for k in range(3):                                                 # the three heads look down in turn
        creak(SR.T_LOOK + k * DT, 0.08, (-0.5, 0.0, 0.5)[k], 104 - 10 * k, 76 - 8 * k, 0.6)

    # --- D: the table. The bolts checked 1 to 6: a dead knock for each blank; 3 and 5 ring, and ring again.
    for n in range(1, 7):
        at = check_time(n)
        scratch(at + 0.03, at + 0.3, 0.05, bolt_pan[n], seed=50 + n)
        if n in WRITTEN:
            twice(bell, at + DT, n, gain=0.3, pan=bolt_pan[n])
        else:
            knock(at + DT, n, 0.3, bolt_pan[n])
    twice(bloop, E + E_BUB + 0.05, 360, gain=0.08, pan=-0.2)           # the last pair of bubbles
    # 50.0 .. 52.0: the die is still in the cup. Nothing moves, nothing doubles, nothing sounds but the room.
    mix.reverb(0.1, 0.7)
    peak = max(np.abs(mix.L).max(), np.abs(mix.R).max())               # the kit only turns down: bring the mix up
    if peak > 0:
        mix.L *= 0.85 / peak
        mix.R *= 0.85 / peak


if __name__ == "__main__":
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / "c16"
        times = [float(x) for x in sys.argv[2:]]
        ims = [Image.open(d / f"{t:06.2f}.png") for t in times if (d / f"{t:06.2f}.png").exists()]
        if ims:
            Wd._sheet(ims, 4, d / "sheet.png", scale=0.5)
            print("sheet ->", d / "sheet.png")
