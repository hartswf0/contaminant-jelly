"""c13 · class film · porthole 13 · Arch · the twig-bell on Bell Boulder arch.

The story is the children's (../class/transcripts.json, the entry with "porthole": 13). The pilot's page, the
first friend's pick and three endings are written; the second friend's pick and bolts 4, 5 and 6 are blank and
stay blank. This script is the EDITOR: it joins the swarm's three scene modules (films/swarm/c13/), adds the
ending, the captions, the number badge and the sound, and renders.

    0.0-20.0   scene_pilot    the drawing made in pencil, then the pilot's three lines
   20.0-40.5   scene_turkey   A.'s pick (red circle, "Dinner bell"), bolts 1, 2, 3 from Turkey's seat
   40.5-45.0   scene_trout    the blank pick and the blank bolts 4, 5, 6 from the river side
   45.0-51.0   the ending     the six bolts counted clockwise (1, 2, 3 light; 4, 5, 6 stay empty), then a die
                              cup with one die in it that nobody throws

Rule (Clockwise Etiquette): every join is the brass arm sweeping once, clockwise; the bolts are counted clockwise
from twelve; the cup comes in on a clockwise arc. Nothing goes back the other way.

    python3 films/c13.py --stills 2 6 10 ...
    python3 films/c13.py
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import ImageDraw

HERE_ = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE_))
sys.path.insert(0, str(HERE_ / "swarm" / "c13"))

from kit import Film, Ink, Mix, FPS, RATE, W, font, clamp, ramp, ease, smooth, lerp  # noqa: E402
import world as w                 # noqa: E402
import scene_pilot as sp          # noqa: E402
import scene_turkey as st         # noqa: E402
import scene_trout as sr          # noqa: E402

SLUG = "c13"
T_PILOT = 0.0
T_TURKEY = T_PILOT + sp.SECONDS          # 20.0
T_TROUT = T_TURKEY + st.SECONDS          # 40.5
T_END = T_TROUT + sr.SECONDS             # 45.0
SECONDS = T_END + 6.0                    # 51.0

# ---------------------------------------------------------------- captions ---
# The children's sentences, in the `reads` spelling, word for word. Absolute times, one at a time.
GAP = 0.15                               # a breath between two captions that would otherwise touch


def _join_captions():
    out = []
    for off, mod in ((T_PILOT, sp), (T_TURKEY, st), (T_TROUT, sr)):
        for a, b, s in mod.CAPTIONS:
            out.append([round(off + a, 3), round(off + b, 3), s])
    out.sort()
    for k in range(len(out) - 1):        # trim so none overlap or touch
        if out[k][1] > out[k + 1][0] - GAP:
            out[k][1] = round(out[k + 1][0] - GAP, 3)
    return [tuple(c) for c in out]


CAPTIONS = [
    (9.0, 12.85, "The trout. The trout think the sub is a bell-ringer prank."),
    (13.0, 15.85, "Freak out."),
    (16.0, 20.0, "He is going to be turkey dinner."),
    (23.3, 27.7, "The dinner bell to go off."),
    (28.3, 33.7, "The dinner bell goes off and the fish go crazy."),
    (34.4, 40.0, "The fish go quiet and calm."),
]
assert CAPTIONS == _join_captions(), "the list above must be the modules' captions, joined and trimmed"
for _k, (_a, _b, _s) in enumerate(CAPTIONS):
    assert _b - _a >= 2.5, ("caption held under 2.5 s", _s)
    assert _b <= T_TROUT, "nothing is said once the sheet goes blank"
    if _k:
        assert _a >= CAPTIONS[_k - 1][1] + GAP - 1e-9, "captions overlap"
assert len(CAPTIONS) == 6

# ------------------------------------------------------------------ ending ---
E_SWEEP = (T_END, T_END + 0.5)           # the brass arm, once round, back to the table
E_COUNT = T_END + 0.6                    # bolt 1 is counted here ...
E_STEP = 0.4                             # ... and each next bolt this much later, clockwise
E_BOLT = {n: E_COUNT + E_STEP * (n - 1) for n in range(1, 7)}
WRITTEN = (1, 2, 3)                      # the endings that are on the sheet
E_CUP = (T_END + 3.1, T_END + 3.85)      # the die cup comes in and is set down; then nothing moves
CUP_AT = (850, 505)
_CUP_R = math.hypot(CUP_AT[0] - w.PORT_C[0], CUP_AT[1] - w.PORT_C[1])
_CUP_A = math.degrees(math.atan2(CUP_AT[0] - w.PORT_C[0], -(CUP_AT[1] - w.PORT_C[1])))     # its clock angle
assert E_BOLT[6] + E_STEP <= E_CUP[0] and SECONDS - E_CUP[1] >= 2.0


def _ending(ink, t):
    """The six bolts and the die that has not been thrown. On the table, the porthole front-on."""
    w.table(ink, sheet=False)
    w.porthole_on_table(ink)
    for n in range(1, 7):
        f = ease(t, E_BOLT[n], E_BOLT[n] + 0.3)
        if f <= 0:
            continue                                       # not counted yet: the bare brass bolt
        if n in WRITTEN:
            w.bolt_mark(ink, n, lit=f)                     # written: the bolt lights, its die face bright
        else:
            x, y = w.bolt_mark(ink, n, lit=0.0, die=False)             # unwritten: no light at all ...
            w.die_face(ink, n, x, y, 30, "ivory", lit=0.0, alpha=f)    # ... its die face grey and dead
    f = ramp(t, *E_CUP)
    if f > 0:                                              # the cup slides in on a clockwise arc and stops
        e = 1 - (1 - f) ** 3
        x, y = w.clock_xy(w.PORT_C, _CUP_R + 260 * (1 - e), _CUP_A - 34 * (1 - e))
        lift = 1 - ease(t, E_CUP[1] - 0.3, E_CUP[1])
        w.die_cup(ink, x, y - 10 * lift, 150, shadow=0.9)


_LAST = {}


def _river_last(ink):
    """The last frame of the trout's part, held: what the brass arm sweeps away."""
    if "img" not in _LAST:
        o = w.offscreen(ink)
        sr.draw(sr.SECONDS - 1.0 / FPS, o)
        _LAST["img"] = o.img.convert("RGB")
    return _LAST["img"]


CAP_Y, CAP_SIZE = 511, 25


def _caption(ink, t):
    """One caption, always on the same plate (paper with a dark keyline and a shadow, so it shows on the white
    page as well as on the tin). The words are the child's; a hyphen is set tight so "bell-ringer" is one word."""
    for a, b, s in CAPTIONS:
        if a <= t < b:
            al = min(ramp(t, a, a + 0.2), 1 - ramp(t, b - 0.2, b))
            if al <= 0:
                return
            f = font("serif", CAP_SIZE)
            parts = s.split("-")
            hw = 9.0                                        # a hyphen ruled by hand: the font's own floats in gaps
            tw = sum(f.getlength(q) for q in parts) + hw * (len(parts) - 1)
            x0, y = W / 2 - tw / 2, CAP_Y
            box = [x0 - 16, y - 19, x0 + tw + 16, y + 19]
            ink.d.rounded_rectangle([box[0] + 3, box[1] + 4, box[2] + 3, box[3] + 4], radius=5, fill=(0, 0, 0, int(90 * al)))
            ink.d.rounded_rectangle(box, radius=5, fill=(248, 246, 240, int(246 * al)), outline=(44, 40, 36, int(230 * al)), width=2)
            col = (26, 24, 22, int(255 * al))
            x = x0
            for k, q in enumerate(parts):
                if k:
                    ink.d.line([(x + 1.5, y + 4), (x + 7.5, y + 4)], fill=col, width=2)
                    x += hw
                ink.d.text((x, y), q, font=f, fill=col, anchor="lm")
                x += f.getlength(q)
            return


def picture(t, ink):
    if t < T_TURKEY:
        sp.draw(t - T_PILOT, ink)
    elif t < T_TROUT:
        st.draw(t - T_TURKEY, ink)
    elif t < T_END:
        sr.draw(t - T_TROUT, ink)
    elif t < E_SWEEP[1]:
        ink.img.paste(_river_last(ink), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        o = w.offscreen(ink)
        _ending(o, t)
        w.sweep(ink, o.img, ramp(t, *E_SWEEP))
    else:
        _ending(ink, t)
    _caption(ink, t)
    w.badge(ink)                                           # 13, top right, every frame


# ------------------------------------------------------------------- sound ---
# All synthesized with the kit's Mix. No words. A small brass bell, a pencil, paper, the tin, and one note per
# bolt: bolts 1, 2, 3 (written) are a struck brass note each, a step higher; bolts 4, 5, 6 (blank) are the same
# place in the scale played on dead wood, no ring.
BOLT_HZ = {1: 660.0, 2: 742.5, 3: 880.0, 4: 990.0, 5: 1113.75, 6: 1320.0}
BELL_HZ = 1180.0


def _bolt_tick(mix, at, n, written, gain=1.0):
    if written:
        t_ = mix.t(0.9)
        f = BOLT_HZ[n]
        sig = (np.sin(2 * np.pi * f * t_) * np.exp(-t_ * 5) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t_) * np.exp(-t_ * 11)
               + 0.25 * np.sin(2 * np.pi * f * 5.4 * t_) * np.exp(-t_ * 20))
        mix.add(sig, at, 0.16 * gain, pan=0.5 * math.sin(math.radians((n - 1) * 60)))
        mix.click(at, gain=0.16 * gain, bright=6000, seconds=0.02)
    else:
        t_ = mix.t(0.07)
        sig = np.sin(2 * np.pi * BOLT_HZ[n] * 0.25 * t_) * np.exp(-t_ * 70)
        mix.add(sig, at, 0.3 * gain, pan=0.5 * math.sin(math.radians((n - 1) * 60)))
        mix.click(at, gain=0.14 * gain, bright=1400, seconds=0.03)


def _scratch(mix, rs, a, b, gain=0.05, pan=0.0):
    n = int((b - a) * RATE)
    if n < 200:
        return
    tt = np.arange(n) / RATE
    x = mix.band(rs.normal(0, 1, n), 2200, 7500)
    x *= (0.6 + 0.4 * np.sin(2 * np.pi * 9.0 * tt + rs.uniform(0, 6))) * np.minimum(1, np.minimum(tt / 0.03, (tt[-1] - tt) / 0.04))
    mix.add(x, a, gain, pan)


def _pen_runs():
    """When the pencil is on the paper during the drawing (from the world unit's own stroke timing)."""
    ink = Ink(0.0, 0)
    runs, start = [], None
    k_end = int(sp.T_DRAWN * FPS) + 1
    for k in range(k_end + 1):
        tt = k / FPS
        down = bool(w.pilot_page(ink, tt)[1]) and tt < sp.T_DRAWN
        if down and start is None:
            start = tt
        if not down and start is not None:
            runs.append((start, tt))
            start = None
    return runs


def _drum(mix, rs, a, b, rate=11.0, gain=0.05, pan=-0.3):
    """Wings beating the inside of a bread tin, heard through its wall: quick muffled knocks."""
    t_ = a
    while t_ < b:
        mix.thud(t_, freq=rs.uniform(120, 150), gain=gain * rs.uniform(0.6, 1.0) * min(1.0, (b - t_) / 0.25 + 0.3),
                 pan=pan, seconds=0.07)
        t_ += 1.0 / rate * rs.uniform(0.8, 1.2)


def _blips(mix, rs, at, n=6, gain=0.035, pan=-0.2):
    """A string of bubbles leaving a beak."""
    for k in range(n):
        tt = mix.t(0.06)
        f = rs.uniform(500, 800) + 260 * k
        mix.add(np.sin(2 * np.pi * (f + 3500 * tt) * tt) * np.exp(-tt * 45), at + 0.09 * k + rs.uniform(0, 0.02), gain, pan)


def sound(mix):
    rs = np.random.RandomState(13)
    A, B, Cc, D = T_PILOT, T_TURKEY, T_TROUT, T_END
    mix.room(0, SECONDS, gain=0.012)
    # the water, from the first look out of the seat to the last look in from the river
    mix.water(A + 16.0, Cc - (A + 16.0), gain=0.028)
    mix.water(Cc - 0.6, D - Cc + 1.0, gain=0.012)

    # -- A1-A6: the pencil
    for a, b in _pen_runs():
        _scratch(mix, rs, a, b, 0.055, pan=-0.1)
        mix.click(a, gain=0.03, bright=3000, seconds=0.012)
    mix.whoosh(sp.T_DRAWN, sp.T_PENCIL_OUT - sp.T_DRAWN, gain=0.02, pan=0.5)

    bells = Mix(SECONDS, seed=3)                      # the bell on its own strip, so it can be stopped dead

    def strike(at, gain=0.2, hz=BELL_HZ, sec=1.6, pan=0.0):
        bells.bell(at, hz, sec, gain, pan)
        mix.click(at, gain=gain * 0.35, bright=5000, seconds=0.012, pan=pan)

    # -- A7: pieces laid on the page, the lamp touches the cord, one late strike
    for name, (a, b) in sp.LAY.items():
        mix.thud(A + b - 0.03, freq=210 if name != "tin" else 120, gain=0.07 if name != "tin" else 0.14, seconds=0.09)
        mix.whoosh(A + a, b - a, gain=0.012)
    mix.click(A + sp.T_BEAM, gain=0.1, bright=3000)
    strike(A + sp.T_STRIKE, 0.2)
    # -- A8: the tin turned to face us; Turkey freaks out
    _scratch(mix, rs, A + sp.T_FACE[0], A + sp.T_FACE[1], 0.02)
    mix.thud(A + sp.T_FACE[1], freq=110, gain=0.12, seconds=0.12)
    _drum(mix, rs, A + sp.T_SNAP, A + 16.0, 12.0, 0.11, pan=0.0)
    for k in range(2):                                # the needle drops two notches
        mix.click(A + sp.T_SNAP + 0.5 + 0.5 * k, gain=0.08, bright=5500, seconds=0.015, pan=0.6)
    # -- A9: round to his seat; the bell comes to rest over him; he sees it
    mix.whoosh(A + sp.T_SWEEP[0], sp.T_SWEEP[1] - sp.T_SWEEP[0], gain=0.05)
    strike(A + 16.45, 0.07)
    strike(A + 17.05, 0.035)
    _drum(mix, rs, A + 16.75, A + sp.T_SEES, 10.0, 0.035)
    _blips(mix, rs, A + sp.T_SEES + 0.1)
    mix.click(A + sp.T_SEES + 0.5, gain=0.08, bright=5500, seconds=0.015, pan=0.6)
    _drum(mix, rs, A + sp.T_SEES + 1.0, B + 0.1, 10.0, 0.035)

    # -- B0: the pick card, the pencil's loop, the red button
    mix.thud(B + st.T_CARD_IN[1], freq=200, gain=0.08, seconds=0.09)
    _scratch(mix, rs, B + st.T_LOOP[0], B + st.T_LOOP[1], 0.05)
    mix.click(B + st.T_PRESS[0] + 0.1, gain=0.2, bright=2400, seconds=0.04)
    mix.note(B + st.T_PRESS[0] + 0.12, 440.0, 0.35, gain=0.06)
    mix.whoosh(B + st.T_CARD_OUT[0], st.T_CARD_OUT[1] - st.T_CARD_OUT[0], gain=0.03, pan=0.4)
    _drum(mix, rs, B + 0.1, B + st.S1, 10.0, 0.03)

    # -- the bolts of Turkey's side: each one behind a sweep, each with its own struck note
    for n, s in ((1, st.S1), (2, st.S2), (3, st.S3)):
        mix.whoosh(B + s, st.SWEEP, gain=0.045)
        _bolt_tick(mix, B + s + st.SWEEP, n, True)
    # bolt 1: one pull, two late strikes
    for k, s in enumerate(st.STRIKES1):
        strike(B + s, 0.26 - 0.07 * k, sec=2.2)
    _drum(mix, rs, B + st.S1 + 0.5, B + st.STRIKES1[0], 10.0, 0.03)
    _blips(mix, rs, B + st.STRIKES1[0] + 0.1)
    mix.click(B + st.STRIKES1[0] + 0.55, gain=0.08, bright=5500, seconds=0.015, pan=0.6)
    _drum(mix, rs, B + st.STRIKES1[0] + 1.0, B + st.S2, 11.0, 0.035)
    # bolt 2: it goes off, and then a crowding peal while the wheel of fish turns; wings a blur
    s23 = st.STRIKES23
    for k, s in enumerate(s23):
        if s >= st.T_HOLD:
            break
        if s < st.S3:
            g = 0.24 if k == 0 else lerp(0.13, 0.22, ramp(s, s23[1], st.S3))
        else:                                         # bolt 3 opens on the peal, the wheel slowing under it
            g = lerp(0.2, 0.08, ramp(s, st.S3, st.T_HOLD))
        strike(B + s, g, hz=BELL_HZ * (1.0 if k % 2 == 0 else 1.012), sec=1.3, pan=0.15 if k % 2 else -0.15)
    n_ = int((st.S3 - st.TR2) * RATE)                 # the stampede: churned water going round
    tt = np.arange(n_) / RATE
    churn = mix.band(rs.normal(0, 1, n_), 250, 1800) * (0.55 + 0.45 * np.sin(2 * np.pi * 1.9 * tt)) * np.minimum(1, tt / 1.2)
    mix.add(churn, B + st.TR2, 0.035)
    n_ = int((st.T_STILL - st.S3) * RATE)             # ... and dying away in bolt 3 as each trout halts
    tt = np.arange(n_) / RATE
    churn = mix.band(rs.normal(0, 1, n_), 250, 1800) * (0.55 + 0.45 * np.sin(2 * np.pi * 1.9 * tt)) * (1 - tt / tt[-1]) ** 1.5
    mix.add(churn, B + st.S3, 0.035)
    _drum(mix, rs, B + st.S2 + 0.5, B + st.S3, 19.0, 0.04)
    mix.click(B + s23[0] + 0.5, gain=0.08, bright=5500, seconds=0.015, pan=0.6)
    mix.click(B + s23[0] + 1.6, gain=0.08, bright=5500, seconds=0.015, pan=0.6)
    # bolt 3: each trout halts in turn (a soft stop each), the clapper is held, the bell is cut off dead
    for k, ts in st._TSTOP.items():
        mix.click(B + ts, gain=0.05, bright=1500, seconds=0.03, pan=0.5 * math.sin(math.radians(k * 60)))
    cut = int((B + st.T_HOLD) * RATE)
    fade = int(0.035 * RATE)
    for ch in (bells.L, bells.R):                     # nothing of the bell is left after the clapper is held
        ch[cut:cut + fade] *= np.linspace(1, 0, fade)
        ch[cut + fade:] = 0.0
    bells.reverb(0.12, 0.7)
    for ch in (bells.L, bells.R):
        ch[cut + fade:] = 0.0
    mix.L += bells.L
    mix.R += bells.R
    mix.thud(B + st.T_HOLD, freq=260, gain=0.05, seconds=0.05)          # the mouth closing on the clapper
    # ... then the only sound is Turkey, rigid and trembling, drumming very small and fast inside the tin
    _drum(mix, rs, B + st.S3 + 0.5, B + st.T_HOLD, 11.0, 0.03)
    _drum(mix, rs, B + st.T_HOLD + 0.2, Cc, 22.0, 0.05, pan=-0.25)
    mix.click(B + st.T_STILL + 0.6, gain=0.07, bright=5500, seconds=0.015, pan=0.6)        # the needle, one notch
    # the water itself goes quiet for the stillness
    a_, b_ = int((B + st.T_GONE) * RATE), int(Cc * RATE)
    duck = np.ones(mix.n)
    duck[a_:b_] = 0.45
    k_ = int(0.4 * RATE)
    duck = np.convolve(duck, np.ones(k_) / k_, "same")
    # (only the beds are below this level here; the drumming is quiet enough to sit under the same duck)
    mix.L *= duck
    mix.R *= duck

    # -- C: round to the river side. The blank pick, the three blank bolts: dead wood, no ring.
    mix.whoosh(Cc + sr.T_SWEEP[0], sr.T_SWEEP[1] - sr.T_SWEEP[0] + 0.1, gain=0.045)
    mix.thud(Cc + sr.T_LAY[1], freq=200, gain=0.07, seconds=0.09)
    mix.whoosh(Cc + sr.T_TAKE[0], sr.T_TAKE[1] - sr.T_TAKE[0], gain=0.025, pan=0.4)
    for n in (4, 5, 6):
        _bolt_tick(mix, Cc + sr.T_BOLT[n] + sr.STEP / 2, n, False)

    # -- D: back to the table. The bolts counted clockwise: three ring, three do not. The cup is set down.
    mix.whoosh(E_SWEEP[0], E_SWEEP[1] - E_SWEEP[0], gain=0.045)
    for n in range(1, 7):
        _bolt_tick(mix, E_BOLT[n] + 0.05, n, n in WRITTEN, gain=1.1)
    mix.whoosh(E_CUP[0], E_CUP[1] - E_CUP[0], gain=0.015, pan=0.6)
    mix.thud(E_CUP[1] - 0.04, freq=95, gain=0.16, seconds=0.16, pan=0.6)
    mix.click(E_CUP[1] + 0.06, gain=0.05, bright=1800, seconds=0.03, pan=0.6)       # the die settles once in the cup
    peak = max(np.abs(mix.L).max(), np.abs(mix.R).max())                            # the kit only turns down: bring
    if peak > 0:                                                                    # the quiet mix up to a fair level
        mix.L *= 0.85 / peak
        mix.R *= 0.85 / peak


film = Film(SLUG, SECONDS, seed=13)
film.picture(picture)
film.sound(sound)
film.poster_at = T_TURKEY + st.STRIKES1[0] + 0.3

if __name__ == "__main__":
    sp.check()
    st.check()
    sr.check()
    film.render()
