"""DON'T PAVE COW PATHS · the sound library and the music (SCION law 7).

Everything is synthesized sample by sample and laid into a kit.Mix. Nothing is foraged, nothing is a sample.

NOBODY ON THIS PRODUCTION CAN HEAR. Every sound here was designed from physical reasoning and checked only by
measurement (levels, durations, spectra, pitch) and by looking at spectrograms. How any of it SOUNDS is UNKNOWN.
See SOUND.md for what was measured and what was not.

Use, from an act or from the assembly:

    import sound as snd                       # with films/swarm/cowpath on sys.path
    snd.hoof(mix, 5.25, 'turf', weight=1.0, pan=snd.pan_x(140))
    snd.bell(mix, 4.5, pan=snd.pan_x(130))    # `at` is when her head changes direction; the strike comes late
    snd.music(mix)                            # the three movements at the board's times
    snd.music(mix, cues={'tree': 6.94})       # ... or at the picture's real times

Conventions
    at        seconds in the Mix (film time when the Mix is the film's).
    gain      roughly the peak sample value the sound reaches in each channel when pan = 0 (every source is
              normalised to peak 1 before `gain`); defaults were set by measurement, see SOUND.md.
    pan       -1 left .. +1 right; pan_x(x) turns a screen x (0..960) into a pan clamped to +-0.8.
    Every sound is deterministic: its noise is seeded from its own name and its `at`, so the order in which
    other agents' code calls the library does not change what any one call produces.

Run:  python3 films/swarm/cowpath/sound.py     renders every sound and the music to films/swarm/cowpath/sound/*.wav,
                                               measures them, prints the table and writes sound/levels.json
"""

from __future__ import annotations

import json
import math
import sys
import wave
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))

from kit import Mix, RATE, W, clamp  # noqa: E402

OUT = HERE / "sound"

# The tune's scale (board (e)): D pentatonic.
D4, E4, FS4, A4, B4, D5 = 293.7, 329.6, 370.0, 440.0, 493.9, 587.3
E5, FS5, A5, B5, D6 = 659.3, 740.0, 880.0, 987.8, 1174.7
SCALE = (D4, E4, FS4, A4, B4, D5)                      # the straight road: lane 1 .. lane 6
A_WRONG = 415.0                                        # slab 4 before the repair (board 3.4)
B_FLAT = B4 * 2 ** (-1 / 24)                           # a quarter-tone flat: the stamp on the bad drawing (2.4)
TURN = (A4, FS4, A4)                                   # the three-note turn: the bog loop
WANDER = (D4, E4, FS4,                                 # she sets off straight ...            (breaks off: the tree)
          E4, D4, E4, FS4, A4,                         # back a note, then on                 (round the tree)
          B4, A4,                                      # up and back                          (over the boulder)
          A4, FS4, A4,                                 # the turn                             (the bog loop)
          B4, D5)                                      # on to the water
BELL_HZ = 740.0


def pan_x(x):
    """Screen x (0..960) to a pan, clamped so nothing is hard left or right."""
    return clamp((x - W / 2) / (W / 2), -0.8, 0.8)


def lane_pan(lane):
    """Act 3 lane 1..6 (x = 180..780) to a pan."""
    return pan_x(130 + 100 * lane)


# ======================================================================================= plumbing ===

def _rs(tag, at):
    return np.random.RandomState(zlib.crc32(f"{tag}:{at:.4f}".encode()) & 0x7FFFFFFF)


def _n(seconds):
    return max(1, int(round(seconds * RATE)))


def _t(seconds):
    return np.arange(_n(seconds)) / RATE


def _norm(x):
    return x / (np.abs(x).max() + 1e-12)


def _band(x, lo, hi, soft=0.2):
    """FFT band-pass with raised-cosine skirts (the kit's band has brick walls, which ring on short sounds).
    Pads to a power of two so long beds stay fast."""
    n = len(x)
    m = 1 << int(math.ceil(math.log2(max(n, 2))))
    X = np.fft.rfft(x, m)
    f = np.fft.rfftfreq(m, 1 / RATE)
    g = np.ones(len(f))
    if lo > 0:
        g *= np.clip((f - lo * (1 - soft)) / (lo * soft + 1e-9), 0, 1)
    if hi < RATE / 2:
        g *= np.clip((hi * (1 + soft) - f) / (hi * soft + 1e-9), 0, 1)
    g = g * g * (3 - 2 * g)
    return np.fft.irfft(X * g, m)[:n]


def _fade(x, a=0.004, r=0.004):
    na, nr = min(len(x) // 2, _n(a)), min(len(x) // 2, _n(r))
    x = x.copy()
    x[:na] *= np.linspace(0, 1, na)
    x[len(x) - nr:] *= np.linspace(1, 0, nr)
    return x


def _noise(rs, seconds, color="white"):
    x = rs.normal(0, 1, _n(seconds))
    if color == "brown":
        x = np.cumsum(x)
        k = 2000
        c = np.cumsum(np.concatenate([[0.0], x]))
        ma = (c[k:] - c[:-k]) / k
        x = x - np.interp(np.arange(len(x)), np.arange(len(ma)) + k / 2, ma)
        x = _norm(x)
    return x


def _slow(rs, n, hz, lo=0.0, hi=1.0):
    """A slow random curve in lo..hi with about `hz` wiggles a second."""
    k = max(2, int(n / RATE * hz) + 2)
    pts = rs.uniform(lo, hi, k)
    u = np.linspace(0, k - 1, n)
    i = np.minimum(u.astype(int), k - 2)
    f = u - i
    f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f) + pts[i + 1] * f


def _string(freq, seconds, rs, damp=0.996, soft=0):
    """Karplus-Strong string, vectorised a period at a time and resampled to the exact pitch (the kit's pluck
    rounds the period to whole samples, which is up to 10 cents out; here 440 is 440)."""
    n = _n(seconds)
    p = max(2, int(round(RATE / freq + 0.5)))
    actual = RATE / (p - 0.5)                            # the two-point average LEADS by half a sample
    ratio = freq / actual
    need = int(n * ratio) + p + 2
    buf = rs.uniform(-1, 1, p)
    for _ in range(soft):                                # a softer pick: fewer highs in the burst
        buf = 0.5 * (buf + np.roll(buf, 1))
    buf -= buf.mean()
    blocks = []
    for _ in range(need // p + 1):
        blocks.append(buf)
        new = damp * 0.5 * (buf + np.roll(buf, -1))
        new[-1] = damp * 0.5 * (buf[-1] + new[0])
        buf = new
    x = np.concatenate(blocks)
    y = np.interp(np.arange(n) * ratio, np.arange(len(x)), x)
    k = min(n // 3, _n(0.08))
    y[n - k:] *= np.linspace(1, 0, k) ** 2                # a string that is cut off clicks; let it down
    return _norm(y)


def _add(mix, sig, at, gain=1.0, pan=0.0):
    if at < 0:
        sig = sig[int(-at * mix.rate):]
        at = 0.0
    mix.add(sig, at, gain, pan)


def _add_sweep(mix, sig, at, gain, pan0, pan1):
    """Like mix.add, with the pan travelling from pan0 to pan1 over the sound."""
    i = int(at * mix.rate)
    if i >= mix.n or len(sig) == 0 or i < 0:
        return
    sig = sig[: mix.n - i] * gain
    p = np.linspace(pan0, pan1, len(sig))
    mix.L[i:i + len(sig)] += sig * np.cos((p + 1) * np.pi / 4) * 1.414
    mix.R[i:i + len(sig)] += sig * np.sin((p + 1) * np.pi / 4) * 1.414


def _thump(freq, seconds, drop=1.5, rate=30.0, decay=12.0):
    t = _t(seconds)
    f = freq * (1 + drop * np.exp(-t * rate))
    return np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * decay)


def _tick(rs, seconds, lo, hi, decay=8.0):
    n = _n(seconds)
    return _fade(_band(rs.normal(0, 1, n) * np.exp(-np.linspace(0, decay, n)), lo, hi), 0.0005, 0.002)


# ========================================================================================== hooves ===

SURFACES = ("turf", "pavement", "gravel", "mud", "water", "wood", "slab")


def hoof(mix, at, surface="turf", weight=1.0, gain=None, pan=0.0):
    """One hoof coming down. `weight` 0.4 (a tentative touch) .. 1.0 (a walking plant) .. 1.6 (the whole cow).

    Weight is not only loudness: a heavier plant is lower, longer and has more thump under it, so a touch and a
    committed step differ in kind (board 3.5: 'ten frames with the weight not yet on it').
      turf      a soft low thud and crushed grass; no click at all.
      pavement  the cloven hoof: two hard ticks 14 ms apart and a short knock; a thump under it with weight.
      slab      pavement, standing in the open over water: the same ticks, a longer stony knock.
      gravel    a grind of small stones.     mud  a low suck.     water  a slap and a wash.     wood  a desk knock.
    Default gain: 0.26 x weight (turf, mud), 0.22 x weight (the rest)."""
    rs = _rs("hoof" + surface, at)
    w = clamp(weight, 0.2, 2.0)
    if surface == "turf":
        sec = 0.16 + 0.10 * w
        t = _t(sec)
        body = _thump(88 / w ** 0.5, sec, drop=0.9, rate=38, decay=20 / w ** 0.6)
        grass = _band(rs.normal(0, 1, len(t)), 140, 1100) * np.exp(-t * 34) * (0.30 + 0.10 * w)
        sig, g = body + grass, 0.26 * w
    elif surface in ("pavement", "slab"):
        sec = 0.14 + 0.05 * w + (0.08 if surface == "slab" else 0)
        t = _t(sec)
        sig = np.zeros(len(t))
        for k, dt in enumerate((0.0, 0.014)):                   # two toes
            tk = _tick(rs, 0.035, 1200, 5200 - 900 * k, decay=5) * (1.0 - 0.35 * k)
            i = _n(dt) if dt else 0
            sig[i:i + len(tk)] += tk[: len(sig) - i]
        knock_f, knock_d = (430, 48) if surface == "pavement" else (310, 22)
        sig = 1.6 * _norm(sig) + 0.5 * np.sin(2 * np.pi * knock_f * t) * np.exp(-t * knock_d)
        sig += (0.08 + 0.3 * (w - 0.4)) * _thump(92 / w ** 0.4, sec, drop=0.6, rate=40, decay=24)
        g = 0.22 * w
    elif surface == "gravel":
        sec = 0.12 + 0.04 * w
        t = _t(sec)
        grind = _band(rs.normal(0, 1, len(t)), 700, 6500) * np.exp(-t * 22) * (0.5 + 0.5 * _slow(rs, len(t), 90))
        sig, g = grind + 0.4 * _thump(110, sec, decay=30), 0.22 * w
    elif surface == "mud":
        sec = 0.34 + 0.12 * w
        t = _t(sec)
        suck = _band(rs.normal(0, 1, len(t)), 180, 900) * np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 2
        sig, g = _thump(60 / w ** 0.3, sec, drop=0.5, rate=18, decay=9) + 0.45 * suck, 0.26 * w
    elif surface == "water":
        sec = 0.34
        t = _t(sec)
        slap = _band(rs.normal(0, 1, len(t)), 300, 3200) * np.exp(-t * 16)
        sig, g = slap + 0.5 * _thump(120, sec, decay=18), 0.22 * w
    elif surface == "wood":
        sec = 0.14
        t = _t(sec)
        sig = _norm(_tick(rs, sec, 300, 2200, decay=9)) + 0.9 * np.sin(2 * np.pi * 150 * t) * np.exp(-t * 36)
        g = 0.22 * w
    else:
        raise ValueError(surface)
    _add(mix, _fade(_norm(sig), 0.0008, 0.01), at, g if gain is None else gain, pan)


def walk(mix, plants, surface="turf", weight=1.0, gain=None, pan=0.0):
    """Several hoof plants. `plants` is a list of times, or of (time, screen_x) so each step sits where the hoof is.
    Fore and hind alternate a little in weight. Take the times from the puppet's plant frames, not from a metronome."""
    for k, p in enumerate(plants):
        t, pn = (p[0], pan_x(p[1])) if isinstance(p, (tuple, list)) else (p, pan)
        hoof(mix, t, surface, weight * (1.0 if k % 2 == 0 else 0.86), gain, pn)


# ============================================================================================ bell ===

def bell(mix, at, swing=1.0, late=0.11, gain=0.2, pan=0.0, under=None, freq=BELL_HZ, rings=2, seconds=0.9):
    """Her bell. `at` is the moment her head changes direction; the clapper is a follower, so the first strike
    comes `late` seconds after (default 0.11 s, about 2.6 frames), and the clapper swings back for a second,
    softer strike on the other wall 0.27 s later (`rings=1` for a single knock, `rings=3` for a big swing).
    `swing` 0.3 (settling) .. 1.0 (a turn of the head) .. 1.5 (startled): scales level and the gap between strikes.
    `under` low-passes it (Hz): 600 = under paper (2.5), 900 = heard from below the water (3.1).
    A cow bell is folded sheet iron, not a cast bell: two strong partials a fifth apart, a rattle of high ones
    that die in 60 ms, the whole thing over in under a second.
    Returns the strike times."""
    rs = _rs("bell", at)
    t = _t(seconds)
    part = [(0.5, 0.3, 5.0), (1.0, 1.0, 5.5), (1.504, 0.85, 7.0), (2.0, 0.22, 11.0), (2.76, 0.35, 16.0), (3.93, 0.25, 28.0), (5.41, 0.2, 45.0)]
    strikes, out = [], np.zeros(_n(seconds + 0.8))
    gap = 0.27 * (0.8 + 0.2 * swing)
    for k in range(rings):
        dt = late + gap * k
        amp = (0.5 ** k) * swing
        det = 1.0 + (0.004 if k % 2 else 0.0)                 # the other wall is a hair sharp
        sig = sum(a * np.sin(2 * np.pi * freq * r * det * t + rs.uniform(0, 6.28)) * np.exp(-t * d) for r, a, d in part)
        sig += 0.5 * _band(rs.normal(0, 1, len(t)), 2500, 7000) * np.exp(-t * 140)        # the clapper's knock
        sig[: _n(0.0015)] *= np.linspace(0, 1, _n(0.0015))
        sig[-_n(0.12):] *= np.linspace(1, 0, _n(0.12)) ** 2
        i = _n(dt)
        out[i:i + len(sig)] += amp * sig[: len(out) - i]
        strikes.append(at + dt)
    peak = np.abs(out).max() / max(swing, 1e-6)
    out = out / (peak + 1e-12)                                # swing=1 peaks at `gain`
    if under:                                                 # what is left is mostly the hum, an octave under the strike note
        out = _band(out, 0, under, soft=0.1)
        out = _fade(out / (np.abs(out).max() + 1e-12) * 0.6 * swing, 0.004, 0.05)
    _add(mix, out, at, gain, pan)
    return strikes


# ============================================================================================= moo ===

MOODS = {
    # f0 contour (time fraction, Hz), mouth opening contour (fraction, 0 closed .. 1 open), seconds, attack, rough, breath, gain
    "content": dict(f0=[(0, 104), (0.25, 122), (0.7, 112), (1.0, 92)], mouth=[(0, 0.0), (0.3, 0.55), (0.75, 0.5), (1, 0.05)],
                    seconds=1.45, attack=0.28, rough=0.0, breath=0.05, gain=0.20),
    "puzzled": dict(f0=[(0, 108), (0.3, 100), (0.5, 101), (0.8, 138), (1.0, 172)], mouth=[(0, 0.0), (0.25, 0.35), (0.5, 0.15), (1, 0.8)],
                    seconds=0.95, attack=0.10, rough=0.0, breath=0.06, gain=0.20, gap=(0.44, 0.52)),
    "alarmed": dict(f0=[(0, 150), (0.12, 236), (0.6, 222), (1.0, 176)], mouth=[(0, 0.5), (0.1, 1.0), (0.8, 0.9), (1, 0.5)],
                    seconds=0.82, attack=0.025, rough=0.45, breath=0.14, gain=0.30),
}


def moo(mix, at, mood="content", gain=None, pan=0.0, pitch=1.0, seconds=None):
    """A moo: content (low, slow, rises a little and settles, mouth nearly shut again at the end), puzzled
    (short, a catch in the middle, then the pitch climbs a fifth and stays up, the question), alarmed (starts
    high and open with no run-up, rough, loud, breathy).

    Built additively: 44 harmonics of a gliding fundamental, each weighted moment by moment by a cow-sized vocal
    tract (formants that move as the mouth opens). `pitch` scales the fundamental (a calf: 1.4).
    The board uses NO moo (its sound plan is hooves, bell and the tune); this is in the library because the
    brief for it asked, and foley(moos=True) shows where three could go. It is not speech and has no words."""
    m = MOODS[mood]
    sec = seconds or m["seconds"]
    rs = _rs("moo" + mood, at)
    t = _t(sec)
    u = t / sec
    f0 = np.interp(u, *zip(*m["f0"])) * pitch
    f0 = f0 * (1 + 0.012 * np.sin(2 * np.pi * 4.6 * t) + 0.006 * (_slow(rs, len(t), 9) - 0.5))
    mouth = np.interp(u, *zip(*m["mouth"]))
    F = [(260 + 380 * mouth, 70, 1.0), (780 + 420 * mouth, 110, 0.55 + 0.3 * mouth), (2250 + 300 * mouth, 220, 0.10 + 0.22 * mouth)]
    ph = 2 * np.pi * np.cumsum(f0) / RATE
    out = np.zeros(len(t))
    for k in range(1, 45):
        fk = k * f0
        if fk.min() > 9000:
            break
        a = np.zeros(len(t))
        for fc, bw, g in F:
            a += g / np.sqrt(1 + ((fk - fc) / bw) ** 2)
        a += 0.05                                             # the nose: a little of everything while the mouth is shut
        out += a / k ** 0.9 * np.sin(k * ph + 0.3 * k) * (fk < 9000)
    if m["rough"]:
        out *= 1 - m["rough"] * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * t + 1.5 * np.sin(2 * np.pi * 7 * t))) * 0.8)
    out = _norm(out) + m["breath"] * _band(rs.normal(0, 1, len(t)), 700, 4200) * (0.3 + mouth)
    env = np.clip(t / m["attack"], 0, 1) ** 1.5 * np.clip((sec - t) / (0.22 * sec), 0, 1) ** 1.2
    if "gap" in m:                                            # the catch in the throat
        a, b = m["gap"]
        env *= 1 - 0.92 * np.exp(-((u - (a + b) / 2) / ((b - a) / 2)) ** 4)
    _add(mix, _norm(out * env), at, m["gain"] if gain is None else gain, pan)


# ================================================================================== pencil and desk ===

def pencil(mix, at, seconds, speed=1.0, pressure=1.0, gain=0.06, pan=0.0):
    """Graphite on paper for `seconds`. The loudness follows the pencil's SPEED, so give it the picture's:
    `speed` is a number, an array (any length, stretched over the stroke, in 0..1 of the fastest the pencil
    goes) or a function of u in 0..1. A stopped pencil is silent. `pressure` 0.5 (a sketch line) .. 2 (bearing down):
    more pressure is lower and grittier, not only louder.
    The grain is the paper's tooth: the noise is broken up at a rate that also rises with speed."""
    rs = _rs("pencil", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    if callable(speed):
        sp = np.array([speed(x) for x in np.linspace(0, 1, 200)], float)
        sp = np.interp(u, np.linspace(0, 1, 200), sp)
    elif np.ndim(speed) == 0:
        sp = np.full(n, float(speed))
    else:
        sp = np.interp(u, np.linspace(0, 1, len(speed)), np.asarray(speed, float))
    sp = np.clip(sp, 0, 1.5)
    k = _n(0.012)
    sp = np.convolve(sp, np.ones(k) / k, "same")
    p = clamp(pressure, 0.3, 2.5)
    x = rs.normal(0, 1, n)
    hiss = _band(x, 1900 / p ** 0.4, 6800 / p ** 0.25)
    body = _band(x, 240, 760) * (0.22 + 0.2 * (p - 1))
    tooth = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(35 + 140 * sp) / RATE + 6 * _slow(rs, n, 14))
    grit = 0.6 + 0.8 * _slow(rs, n, 55)
    sig = (hiss * tooth * grit + body) * sp ** 0.7
    _add(mix, _fade(sig / (np.abs(hiss).max() + 1e-12), 0.004, 0.006), at, gain * p ** 0.6, pan)


def pencil_stroke(mix, at, seconds=0.5, pressure=1.0, gain=0.06, pan=0.0):
    """One pulled stroke: the pencil lands, speeds up, slows into the end of the line."""
    pencil(mix, at, seconds, lambda u: math.sin(math.pi * u ** 0.8) ** 0.8, pressure, gain, pan)
    _add(mix, _tick(_rs("ptick", at), 0.012, 900, 4000), at, gain * 0.5 * pressure, pan)       # the point lands


def stamp(mix, at, weight=1.0, gain=0.34, pan=0.0):
    """Her hoof brought down on a sheet on the desk: the approval mark. A slap of paper, a short thump at 110 Hz
    falling, and the desk top answering at 180 Hz. `weight` 0.6 (careless, 2.3's last round) .. 1.3 (2.4, the bad drawing).
    It has no pitch of its own to speak of; the tune's B is laid over it by the music (cue 'stamp_bad')."""
    rs = _rs("stamp", at)
    w = clamp(weight, 0.3, 2.0)
    sec = 0.32
    t = _t(sec)
    sig = _thump(110 / w ** 0.3, sec, drop=1.2, rate=40, decay=15)
    sig += 0.45 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 26)
    sig += 0.7 * np.pad(_tick(rs, 0.03, 350, 3200, decay=7), (0, len(t) - _n(0.03)))
    _add(mix, _fade(_norm(sig), 0.0005, 0.01), at, gain * w, pan)


def lever(mix, at, gain=0.24, pan=0.0):
    """The camera lever (2.2 'camera'): a dry latch tick, then 60 ms later the weight of the pull going home."""
    rs = _rs("lever", at)
    _add(mix, _tick(rs, 0.03, 900, 5000), at, gain * 0.7, pan)
    _add(mix, _fade(_norm(_thump(74, 0.3, decay=14) + 0.3 * _tick(rs, 0.3, 200, 1200, decay=20)), 0.001, 0.01), at + 0.06, gain, pan)


def brush(mix, at, seconds=0.5, gain=0.07, pan=0.0):
    """A loaded brush drawn across paper: wet, low, no grit (2.2 'paint')."""
    rs = _rs("brush", at)
    n = _n(seconds)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.7
    sig = _band(rs.normal(0, 1, n), 300, 1900) * env * (0.7 + 0.3 * _slow(rs, n, 6))
    _add(mix, _fade(_norm(sig)), at, gain, pan)


def paper_flip(mix, at, gain=0.09, pan=0.0):
    """A sheet flipped over a peg (2.2 'in-between'): 80 ms, bright, with the snap of the corner at the end."""
    rs = _rs("flip", at)
    n = _n(0.085)
    u = np.linspace(0, 1, n)
    sig = _band(rs.normal(0, 1, n), 1500, 8000) * u ** 0.6 * (1 - u) ** 0.3 * (0.5 + 0.5 * _slow(rs, n, 120))
    sig = _norm(sig)
    tk = _tick(rs, 0.008, 2500, 9000, decay=5)
    sig[-len(tk):] += 0.8 * _norm(tk)
    _add(mix, _fade(_norm(sig), 0.002, 0.002), at, gain, pan)


def paper_land(mix, at, gain=0.07, pan=0.0, height=1.0):
    """A sheet coming to rest on the pile: a soft pat with air under it. `height` raises it as the pile grows
    (a sheet falling onto a tall loose heap is lighter and rustles: 2.3 'sheets stop landing square')."""
    rs = _rs("land", at)
    sec = 0.11
    t = _t(sec)
    h = clamp(height, 0.5, 3.0)
    pat = _band(rs.normal(0, 1, len(t)), 180, 900 * h) * np.exp(-t * 38)
    rustle = _band(rs.normal(0, 1, len(t)), 2500, 7000) * np.exp(-t * 26) * 0.25 * (h - 0.5)
    _add(mix, _fade(_norm(pat + rustle), 0.001, 0.01), at, gain, pan)


def paper_slide(mix, at, seconds=0.2, gain=0.08, pan=0.0, pan_to=None, land=True):
    """A sheet sliding off the desk (and, if `land`, patting down at the end). The slide is friction: high, with a
    flutter that slows as the sheet leaves the desk; it travels from `pan` to `pan_to`."""
    rs = _rs("slide", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    flut = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(70 - 40 * u) / RATE)
    sig = _band(rs.normal(0, 1, n), 2000, 9000) * np.sin(np.pi * u ** 0.7) ** 1.2 * flut
    sig += 0.35 * _band(rs.normal(0, 1, n), 400, 1500) * np.sin(np.pi * u) ** 2
    _add_sweep(mix, _fade(_norm(sig)), at, gain, pan, pan if pan_to is None else pan_to)
    if land:
        paper_land(mix, at + seconds, gain * 0.8, pan if pan_to is None else pan_to)


def paper_pile(mix, at, seconds, rate0=3.0, rate1=28.0, gain=0.16, pan=0.0, spread=0.5, cut=True):
    """Paper thickening into one noise (2.5): single sheets at `rate0` a second quickening to `rate1`, over a bed of
    rustle that rises with them, and (if `cut`) all of it stopped dead at the end, no tail. `gain` is the level at
    the top of the rise. The sheets scatter `spread` either side of `pan`."""
    rs = _rs("pile", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    bed = _band(rs.normal(0, 1, n), 900, 8000) * u ** 1.8 * (0.75 + 0.25 * _slow(rs, n, 18))
    bed += 0.5 * _band(rs.normal(0, 1, n), 250, 900) * u ** 2.4
    bed = bed / (np.abs(bed).max() + 1e-12)
    if cut:
        bed[-_n(0.004):] *= np.linspace(1, 0, _n(0.004))
    else:
        bed = _fade(bed, 0.01, 0.4)
    _add(mix, bed, at, gain, pan)
    t = 0.0
    while t < seconds - 0.12:
        f = t / seconds
        g = gain * (0.35 + 0.5 * f)
        p = clamp(pan + rs.uniform(-spread, spread), -0.9, 0.9)
        if rs.rand() < 0.5:
            paper_flip(mix, at + t, g * 0.8, p)
        else:
            paper_land(mix, at + t, g, p, height=1 + 1.5 * f)
        t += 1.0 / (rate0 + (rate1 - rate0) * f ** 1.5) * rs.uniform(0.7, 1.3)


# ============================================================================== the cut and the graft ===

def knife_cut(mix, at, seconds=0.42, gain=0.42, pan=0.0, curl=True):
    """The cut across the stump's rim (2.6, 68.0): the one hard sound of the act. A blade (here the pencil's
    point, drawn hard) through green wood: a rasp whose pitch climbs as the cut thins to a wedge, fibres
    parting at about 190 a second, then the snap as it comes free, and (if `curl`) the shaving curling off."""
    rs = _rs("cut", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    x = rs.normal(0, 1, n)
    lo, mid, hi = _band(x, 900, 2400), _band(x, 2400, 5200), _band(x, 5200, 10500)
    sig = lo * (1 - u) ** 1.5 + mid * np.sin(np.pi * u) ** 0.8 + hi * u ** 1.6
    fibre = 0.45 + 0.55 * (np.sin(2 * np.pi * np.cumsum(150 + 90 * u) / RATE) > 0.2)
    sig = _norm(sig * fibre * (0.35 + 0.65 * u ** 0.5) * np.clip(u / 0.03, 0, 1))
    snap = _norm(_tick(rs, 0.03, 1800, 11000, decay=9))
    sig = np.concatenate([sig, np.zeros(_n(0.03))])
    sig[n - _n(0.004): n - _n(0.004) + len(snap)] += 1.1 * snap[: len(sig) - n + _n(0.004)]
    _add(mix, _fade(_norm(sig), 0.002, 0.004), at, gain, pan)
    if curl:
        m = _n(0.22)
        v = np.linspace(0, 1, m)
        c = _band(rs.normal(0, 1, m), 3000, 9000) * (1 - v) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(60 - 35 * v) / RATE))
        _add(mix, _fade(_norm(c)), at + seconds + 0.03, gain * 0.12, pan)


def graft_seat(mix, at, gain=0.2, pan=0.0):
    """The wedge set into the cleft (69.3): green wood on old wood, small, close, and the cleft closing on it 50 ms later."""
    rs = _rs("seat", at)
    t = _t(0.16)
    sig = _norm(_tick(rs, 0.16, 400, 2600, decay=10)) + 0.9 * np.sin(2 * np.pi * 235 * t) * np.exp(-t * 34)
    _add(mix, _fade(_norm(sig), 0.0005, 0.01), at, gain, pan)
    _add(mix, _norm(_tick(rs, 0.05, 250, 1400, decay=8)), at + 0.05, gain * 0.4, pan)


def creak(mix, at, seconds=0.6, tension=1.0, gain=0.12, pan=0.0):
    """A binding drawn tight round the join: stick-slip. The fibre grips, lets go, grips: a train of tiny knocks
    whose rate climbs from about 16 to 16 + 34 x tension a second as the turn is pulled and falls away as it
    holds, each knock ringing the wood (310, 545, 880 Hz, dead in 15 ms). Not a door hinge: it is quiet, close
    and irregular. `tension` 0.5 (first turn) .. 1.5 (the last, pulled home)."""
    rs = _rs("creak", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    rate = 16 + 34 * tension * np.sin(np.pi * u ** 0.8) ** 1.5
    rate *= 1 + 0.25 * (_slow(rs, n, 12) - 0.5)
    ph = np.cumsum(rate) / RATE
    hits = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    imp = np.zeros(n + _n(0.06))
    for h in hits:
        imp[h] = rs.uniform(0.5, 1.0) * (0.4 + 0.6 * math.sin(math.pi * h / n))
    tk = _t(0.05)
    res = sum(a * np.sin(2 * np.pi * f * (1 + 0.1 * (tension - 1)) * tk) * np.exp(-tk * d)
              for f, a, d in ((310, 1.0, 70), (545, 0.7, 90), (880, 0.45, 120), (1650, 0.2, 200)))
    sig = np.convolve(imp, res)[: len(imp)]
    sig += 0.12 * np.pad(_band(rs.normal(0, 1, n), 1500, 5000) * np.sin(np.pi * u) ** 2, (0, len(imp) - n)) * np.abs(sig).max()
    _add(mix, _fade(_norm(sig), 0.002, 0.01), at, gain * (0.7 + 0.3 * tension), pan)


def binding(mix, at, turns=3, every=0.5, gain=0.12, pan=0.0):
    """The path line winding `turns` times round the join (69.5 to 71.0): a creak a turn, each pulled a little
    tighter than the last, and a small knock as the last is drawn home. The tune's D E F# over the turns is the
    music's (cue 'binding'). Returns the time each turn starts."""
    out = []
    for k in range(turns):
        tk = at + every * k
        creak(mix, tk, seconds=min(every * 0.85, 0.55), tension=0.6 + 0.45 * k, gain=gain, pan=pan)
        out.append(tk)
    _add(mix, _norm(_tick(_rs("bindend", at), 0.04, 300, 1800, decay=8)), at + every * turns - 0.05, gain * 0.6, pan)
    return out


# =========================================================================================== beds ===

def wind(mix, at, seconds, gain=0.035, out_by=None):
    """Low wind (acts 1 and 2.6 to 2.8). Like the kit's, but with a release you can place: `out_by` (seconds from
    `at`) is when it has thinned to nothing (board 1.7: 'wind thins to nothing by 35.0'), over the 3 s before."""
    rs = _rs("wind", at)
    n = _n(seconds)
    x = _noise(rs, seconds, "brown")[:n]
    lfo = 0.55 + 0.45 * _slow(rs, n, 0.3)
    t = np.arange(n) / RATE
    env = np.clip(t / 1.0, 0, 1)
    end = seconds if out_by is None else min(out_by, seconds)
    env *= np.clip((end - t) / (3.0 if out_by is not None else 1.0), 0, 1)
    _add(mix, x * lfo * env, at, gain)


def room(mix, at, seconds, gain=0.02):
    """Room tone for the desk (act 2): air, no mains hum (a cow's desk has no electricity), slightly different in each ear."""
    for k, pn in enumerate((-0.3, 0.3)):
        rs = _rs(f"room{k}", at)
        n = _n(seconds)
        x = _band(rs.normal(0, 1, n), 60, 1400, soft=0.5)
        t = np.arange(n) / RATE
        env = np.clip(t / 0.4, 0, 1) * np.clip((seconds - t) / 0.02, 0, 1)        # in gently, out at once (2.5's cut)
        _add(mix, _norm(x) * env * 0.5, at, gain, pn)


def water(mix, at, seconds, gain=0.05, under=False, ducks=(), fade_in=0.8, fade_out=0.8):
    """The river. under=False: at the bank, from the air (acts 1, 2.8): a wash with small bright droplets.
    under=True: from below the surface (act 3): everything above 900 Hz gone, a slow swell, and now and then a
    low bubble. `ducks` = [(t0, t1, level)] in the Mix's time pulls the bed down to `level` between t0 and t1
    (board 3.4: 'the quietest second in the film (water at half gain)': ducks=[(100.2, 101.2, 0.5)]).
    One bed call per stretch of film; do not stack them."""
    rs = _rs("water" + str(under), at)
    n = _n(seconds)
    t = np.arange(n) / RATE
    x = _band(rs.normal(0, 1, n), 300, 2500)
    drops = int(seconds * (3 if under else 14))
    tt = np.arange(1500) / RATE
    for _ in range(drops):
        k = rs.randint(0, max(1, n - 1600))
        if under:                                             # a bubble: the pitch rises as it shrinks toward the surface
            f = rs.uniform(260, 620)
            x[k:k + 1500] += 0.9 * np.sin(2 * np.pi * (f + 2200 * tt) * tt) * np.exp(-tt * 45)
        else:
            f = rs.uniform(600, 1800)
            x[k:k + 1500] += 1.6 * np.sin(2 * np.pi * (f + 4000 * tt) * tt) * np.exp(-tt * 60)
    if under:
        x = _band(x, 40, 900, soft=0.3) * 2.4 + 0.8 * _band(rs.normal(0, 1, n), 30, 160) * 3.0
        x *= 0.6 + 0.4 * _slow(rs, n, 0.25)
    else:
        x *= 0.55 + 0.45 * _slow(rs, n, 0.6)
    x = x / (np.sqrt((x ** 2).mean()) * 3.2 + 1e-12)          # so `gain` means the same for both: RMS = gain / 3.2
    env = np.clip(t / max(fade_in, 1e-3), 0, 1) * np.clip((seconds - t) / max(fade_out, 1e-3), 0, 1)
    ft = t + at
    for a, b, lv in ducks:
        k = np.clip((ft - (a - 0.25)) / 0.25, 0, 1) * np.clip(((b + 0.35) - ft) / 0.35, 0, 1)
        env *= 1 - (1 - lv) * k
    _add(mix, x * env, at, gain, -0.15)
    _add(mix, np.roll(x, 7919) * env, at, gain * 0.8, 0.25)


def splash(mix, at, size=1.0, gain=0.22, pan=0.0, under=True):
    """A hoof into the water (3.1, 78.0). From below (`under`): a blunt low knock of the surface breaking, then
    the air she carried down breaking up into bubbles. From above: a slap and a wash."""
    rs = _rs("splash", at)
    if not under:
        hoof(mix, at, "water", size, gain, pan)
        return
    sec = 0.5
    t = _t(sec)
    sig = _thump(95 / size ** 0.3, sec, drop=1.0, rate=22, decay=9) + 0.5 * _band(rs.normal(0, 1, len(t)), 120, 800) * np.exp(-t * 11)
    _add(mix, _fade(_norm(sig), 0.001, 0.02), at, gain * size, pan)
    bubbles(mix, at + 0.06, n=int(6 * size) + 2, seconds=0.5, gain=gain * 0.35, pan=pan)


def bubbles(mix, at, n=5, seconds=0.5, gain=0.06, pan=0.0, spread=0.1):
    """`n` bubbles let go over `seconds`: each a 30 ms sine that climbs (a bubble's pitch rises as it shrinks)."""
    rs = _rs("bub", at)
    tt = _t(0.035)
    for _ in range(n):
        f = rs.uniform(380, 900)
        s = np.sin(2 * np.pi * (f + 3000 * tt) * tt) * np.exp(-tt * 70) * np.clip(tt / 0.002, 0, 1)
        _add(mix, s, at + rs.uniform(0, seconds), gain * rs.uniform(0.5, 1.0), clamp(pan + rs.uniform(-spread, spread), -0.9, 0.9))


# =========================================================================================== fish ===

def fish_move(mix, at, seconds=0.3, speed=1.0, gain=0.07, pan=0.0, pan_to=None):
    """A fish moving through water, heard under water: displaced water, low and soft (150 to 600 Hz at speed 1),
    swelling and going, with no edge. Faster is brighter and shorter in feel: a drift (speed 0.4), a swim (1), a dart (2).
    It travels from `pan` to `pan_to`."""
    rs = _rs("fish", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    sp = clamp(speed, 0.2, 3.0)
    sig = _band(rs.normal(0, 1, n), 110 + 40 * sp, 360 + 320 * sp, soft=0.4) * np.sin(np.pi * u ** (1 / (0.6 + 0.4 * sp))) ** 1.5
    sig += 0.5 * _band(rs.normal(0, 1, n), 40, 140) * np.sin(np.pi * u) ** 2
    _add_sweep(mix, _fade(_norm(sig)), at, gain * sp ** 0.5, pan, pan if pan_to is None else pan_to)


def tail_flick(mix, at, gain=0.08, pan=0.0, beats=2):
    """A tail beat or two: a soft low pulse of pushed water for each (90 Hz, 70 ms), the second weaker. For a
    fish that starts, stops or turns on the spot. (3.4: builder 4's tail 'slows and stops' is these, thinning out.)"""
    for k in range(beats):
        t = _t(0.09)
        s = np.sin(2 * np.pi * (92 - 30 * t / 0.09) * t) * np.sin(np.pi * t / 0.09) ** 2
        _add(mix, s, at + 0.13 * k, gain * 0.65 ** k, pan)


def fish_turn(mix, at, seconds=0.45, gain=0.07, pan=0.0):
    """A fish turning about (101.2, builder 4 turning back; the board asks for NO sound there: use this only
    elsewhere, e.g. the seven fish turning to look in 3.1). A swish that falls in pitch as the body comes round."""
    rs = _rs("fturn", at)
    n = _n(seconds)
    u = np.linspace(0, 1, n)
    x = rs.normal(0, 1, n)
    sig = _band(x, 300, 800) * (1 - u) ** 1.5 + _band(x, 110, 320) * u ** 0.8
    _add(mix, _fade(_norm(sig * np.sin(np.pi * u) ** 1.2)), at, gain, pan)
    tail_flick(mix, at + seconds * 0.7, gain * 0.7, pan, beats=1)


def stone_set(mix, at, pitch=None, gain=0.2, pan=0.0, dull=False):
    """A stone set on a pier, under water: a short stony clack with the highs taken off by the water, and under
    it the weight. With `pitch` the stone also sounds its lane's note (a plucked string, the board's rule for 3.3).
    `dull=True` is a stone dropped on the river bed (builder 4, 87.0): no clack, no note, a thud in silt."""
    rs = _rs("stone", at)
    if dull:
        sec = 0.4
        t = _t(sec)
        sig = _thump(64, sec, drop=0.8, rate=20, decay=11) + 0.35 * _band(rs.normal(0, 1, len(t)), 100, 500) * np.exp(-t * 14)
        _add(mix, _fade(_norm(sig), 0.002, 0.02), at, gain, pan)
        return
    t = _t(0.2)
    sig = _norm(_tick(rs, 0.2, 500, 2600, decay=12)) + 0.7 * np.sin(2 * np.pi * 280 * t) * np.exp(-t * 45) + 0.5 * _thump(96, 0.2, decay=22)
    _add(mix, _fade(_norm(sig), 0.0005, 0.01), at, gain, pan)
    if pitch:
        _add(mix, _string(pitch, 1.1, rs, soft=1), at + 0.012, gain * 0.8, pan)


def slab_on(mix, at, pitch=None, gain=0.24, pan=0.0):
    """A slab laid across two piers at the surface: two contacts 45 ms apart (it never lands flat), heavier and
    lower than a stone, and with `pitch` the lane's note an octave down."""
    rs = _rs("slab", at)
    for k, dt in enumerate((0.0, 0.045)):
        t = _t(0.26)
        sig = _norm(_tick(rs, 0.26, 350, 2000, decay=11)) + 0.9 * np.sin(2 * np.pi * (170 - 20 * k) * t) * np.exp(-t * 26) + 0.6 * _thump(70, 0.26, decay=16)
        _add(mix, _fade(_norm(sig), 0.0005, 0.01), at + dt, gain * (1.0 - 0.35 * k), pan)
    if pitch:
        _add(mix, _string(pitch / 2, 1.5, rs, soft=2), at + 0.05, gain * 0.7, pan)


def nudge(mix, at, pitch=A4, firm=True, ring=1.0, gain=0.26, pan=0.0):
    """The watcher's nose under a slab: the slab is sounded.
    firm=True   the slab's note, true, a plucked string with a faint bell on top; `ring` scales how long it is
                left (1.0 about 1.3 s; the retest at 103.2 uses ring=2).
    firm=False  slab_rocks(): the note is flat and the slab clacks on its pier.
    Returns the pitch sounded."""
    if not firm:
        return slab_rocks(mix, at, pitch, gain, pan)
    rs = _rs("nudge", at)
    sec = 1.3 * ring
    damp = 0.996 if ring <= 1 else 0.9982
    _add(mix, _string(pitch, sec, rs, damp=damp, soft=1), at, gain, pan)
    t = _t(sec * 0.9)                                         # a little bell on top (the kit's partials, but let down at the end:
    bl = sum(a * np.sin(2 * np.pi * pitch * r * t) * np.exp(-t * d)            # the kit's own bell stops with a step)
             for r, a, d in ((1.0, 1.0, 3.0), (1.19, 0.5, 4.0), (1.56, 0.45, 5.0), (2.0, 0.35, 6.0), (2.51, 0.25, 8.0)))
    _add(mix, _fade(_norm(bl), 0.002, 0.15), at, gain * 0.15, pan)
    _add(mix, _norm(_tick(rs, 0.03, 300, 1500, decay=9)), at, gain * 0.3, pan)       # nose on stone
    return pitch


def slab_rocks(mix, at, pitch=A4, gain=0.26, pan=0.0, clacks=4, pebble=True):
    """Slab 4 at 97.5: it see-saws on its short pier. The note is WRONG (a semitone flat for A4: 415 Hz, the
    board's figure; other pitches are flattened by the same ratio) and is choked in 0.3 s, because a slab that
    is not seated cannot ring; under it the slab clacks down on one pier and then the other, twice each, dying;
    and (if `pebble`) a pebble ticks off the pier and, 0.5 s later, lands on the bed.
    Returns the wrong pitch."""
    rs = _rs("rocks", at)
    wrong = pitch * A_WRONG / A4
    sig = _string(wrong, 0.6, rs) * np.exp(-_t(0.6) * 9)
    _add(mix, sig, at, gain, pan)
    for k in range(clacks):                                   # see-saw: left pier, right pier, slower each time
        tk = at + 0.03 + 0.17 * k + 0.02 * k * k
        hoof(mix, tk, "wood", 1.0, gain * (0.9, 0.65, 0.4, 0.25, 0.15)[min(k, 4)], clamp(pan + (0.12 if k % 2 else -0.12), -0.9, 0.9))
    if pebble:
        _add(mix, _norm(_tick(rs, 0.02, 2000, 6000)), at + 0.22, gain * 0.35, pan)
        _add(mix, _norm(_tick(rs, 0.05, 300, 1500)), at + 0.74, gain * 0.25, pan)
    return wrong


def refuse(mix, at, gain=0.16, pan=0.0, seconds=0.7):
    """The watcher puts its body across the way (98.6, and again as it rises at 99.2 and sinks at 99.8).

    NOT a buzzer: no tone is held, nothing is harsh, nothing repeats, nothing is loud. The refusal is a body
    of water moved and then stillness: a low swell (60 to 300 Hz) that comes up over 0.15 s and is gone, with
    a soft pitch inside it that FALLS (150 to 85 Hz) and is absorbed, no ring, no tail. It closes.
    Everything about it is the opposite of passed(): falling against level, low against the tune's register,
    damped against ringing, unpitched against a true note. The silence after it is part of it: lay nothing
    else for a second (the board ducks the water to half)."""
    rs = _rs("refuse", at)
    n = _n(seconds)
    t = np.arange(n) / RATE
    u = t / seconds
    swell = _band(rs.normal(0, 1, n), 60, 300, soft=0.5) * np.clip(t / 0.15, 0, 1) * (1 - u) ** 2.2
    f = 150 * (85 / 150) ** np.clip(u / 0.7, 0, 1)
    body = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.clip(t / 0.08, 0, 1) * np.exp(-t * 6.5)
    sig = _norm(swell) * 0.8 + body
    _add(mix, _fade(_norm(sig), 0.01, 0.05), at, gain, pan)


def passed(mix, at, pitch=A4, gain=0.26, pan=0.0, ring=2.0):
    """The retest that holds (103.2), and the way opening.

    NOT a ding: no bright metal attack, no major chord, no upward arpeggio. It is the same slab, the same nose,
    the same string as every other nudge; what is different is that the note is TRUE and is LEFT ALONE: it rings
    `ring` times as long as an ordinary nudge, its octave comes up quietly under the tail 0.25 s in, and 0.3 s
    after the touch the water the watcher was holding lets go upward (a thin rising wash and four bubbles).
    It opens. Pair it with refuse(); between them: pitch, direction, length and register all differ."""
    rs = _rs("passed", at)
    nudge(mix, at, pitch, True, ring, gain, pan)
    sec = 1.3 * ring
    t = _t(sec)
    octave = np.sin(2 * np.pi * pitch * 2 * t) * np.clip((t - 0.1) / 0.5, 0, 1) * np.exp(-t * 1.6)
    _add(mix, _fade(octave, 0.004, 0.3), at, gain * 0.10, pan)
    n = _n(0.9)
    u = np.linspace(0, 1, n)
    x = rs.normal(0, 1, n)
    wash = _band(x, 300, 700) * (1 - u) ** 1.2 + _band(x, 700, 1600) * np.sin(np.pi * u) + _band(x, 1600, 3200) * u ** 1.5
    _add(mix, _fade(_norm(wash * np.sin(np.pi * u ** 0.6) ** 1.5)), at + 0.3, gain * 0.14, pan)
    bubbles(mix, at + 0.35, n=4, seconds=0.6, gain=gain * 0.16, pan=pan)


# ========================================================================================== music ===
# One piece in three movements. Its times are the board's; pass `cues` to move any of them to the picture's.

CUES = dict(
    # ---- movement 1 · THE COW PATH · 0.0 to 36.0 · the tune wanders (plucked string; then square, stiff)
    act1=0.0,
    set_off=5.25,                      # she sets off down STRAIGHT: D E F# ...
    tree=7.0,                          # ... broken off on F#: nose to trunk. Silent to round_tree.
    round_tree=7.6,                    # the detour: back a note, then on
    boulder=10.4,                      # up and back
    loop=(12.4, 13.6),                 # the three-note turn
    water=14.0,                        # the tune stops; drinking is water only
    herd=(14.6, 20.4),                 # the whole wandering tune, three times, louder each time
    dims=(18.0, 19.5),                 # the lamp's two dimmings: the drone swells with each
    tree_falls=23.8,                   # (no music from the herd's end until hoof_off)
    hoof_off=26.6,                     # one pluck, A4, the straight scale's next note; not followed
    paving=(27.5, 33.0),               # the same tune, square wave, strict time
    paved_loop=(31.0, 32.2),           # the turn, with full solemnity
    last_note=33.0,                    # ends unresolved on E
    act1_silence=35.0,                 # nothing from here to act2
    # ---- movement 2 · THE ONE DESK AND THE GRAFT · 36.0 to 76.0 · the tune is ground up
    act2=36.0,
    jobs=(40.1, 42.1, 44.1, 46.1, 48.4),   # round 1: draw D, in-between E, paint F#, camera A, check (the stamp) B
    round2=(49.5, 53.5),               # the wandering tune over the five jobs in 4 s
    round3=(53.5, 55.5),               # and in 2 s, notes overlapping
    bad=55.5,                          # everything cuts off
    stamp_bad=60.0,                    # B, a quarter-tone flat
    drown=(61.0, 64.6),                # the five notes as fast as they go, order lost, rising; then cut
    settle=(65.5, 67.5),               # one low note falling a fifth (A2 to D2)
    binding=(69.6, 70.1, 70.6),        # D E F#, one a turn, slow: the straight scale's first three notes
    bud=73.3,                          # A4, with her ear
    leaves=(73.6, 74.5),               # seven light plucks, B4 D5 E5 F#5 A5 B5 D6
    loosen=(74.5, 75.5),               # the same seven, falling, one a leaf
    # ---- movement 3 · THE FISH AND THE ROAD · 76.0 to 116.0 · the tune is played straight
    act3=76.0,
    look_across=79.0,                  # the drone is out by here: her look is water only
    survey=(81.0, 83.0),               # one held D4, sine, exactly as long as the watcher swims the line
    build=(84.0, 93.5),                # six lanes at once (see `sets`, `slabs`)
    sets=None,                         # {lane: [t, t, t]}; None = _default_sets(); lane 4 has two
    slabs=None,                        # {lane: t}; None = lane 4 at 90.0, the rest 91.5 to 93.4
    loop4=90.25,                       # builder 4's loop of pleasure: the turn, fast
    nudges=(94.5, 95.5, 96.5),         # slabs 1 2 3: D E F#, straight, in time
    rock=97.5,                         # slab 4: the A is wrong (415 Hz). Then nothing until retest.
    retest=103.2,                      # A4, 440, true, left to ring
    joined=103.6,                      # the school's six pitches, once, softly
    last_nudges=(104.4, 105.0),        # slabs 5 6: B D5. The scale completed.
    crossing=(105.4, 106.5, 107.35, 108.62, 109.4, 110.2),   # her weight on slabs 1..6: D E F# (rest) A B D5
    bank=111.0,
    drone_out=(112.0, 116.0),          # the drone thins over this
    credit=116.0,
    end=120.0,
)


def cues(over=None):
    c = dict(CUES)
    if over:
        unknown = set(over) - set(CUES)
        if unknown:
            raise KeyError(f"unknown cue(s) {sorted(unknown)}; see sound.CUES")
        c.update(over)
    if c["sets"] is None:
        c["sets"] = _default_sets()
    if c["slabs"] is None:
        c["slabs"] = {1: 92.4, 2: 93.0, 3: 93.4, 4: 90.0, 5: 91.5, 6: 92.0}
    return c


def _default_sets():
    """Board 3.3: six builders at the same time, staggered by a few frames and not alike. 1 taps each stone
    twice (the taps are foley, not notes); 2 is slow; 3 copies 2 a beat late; 4 is quick and sets only two;
    5 keeps looking at 4 (uneven); 6 works hardest (earliest, most regular)."""
    return {1: [85.3, 87.6, 89.9], 2: [85.9, 88.4, 90.9], 3: [86.4, 88.9, 91.4],
            4: [85.0, 88.2], 5: [85.6, 87.3, 89.6], 6: [84.9, 86.9, 88.9]}


def _pl(m, at, f, seconds=0.9, gain=0.15, pan=0.0, damp=0.996, soft=0, stop=None):
    """A plucked note into the scratch mix; `stop` chokes it that many seconds in."""
    s = _string(f, seconds, _rs("pl", at + f), damp=damp, soft=soft)
    if stop is not None:
        s = s * np.clip((stop - _t(seconds)) / 0.03 + 1, 0, 1)
    _add(m, s, at, gain, pan)


def _sq(m, at, f, seconds, gain=0.07, pan=0.0):
    """The paver's note: a square-ish wave with no vibrato, on at once, off at once."""
    n = _n(seconds)
    t = np.arange(n) / RATE
    s = np.tanh(4 * np.sin(2 * np.pi * f * t)) * 0.6
    _add(m, _fade(s, 0.004, 0.012), at, gain / 0.6, pan)


def _dr(m, at, seconds, freqs=(73.4, 110.0), gain=0.06, attack=1.5, release=1.5):
    n = _n(seconds)
    t = np.arange(n) / RATE
    s = sum(np.sin(2 * np.pi * f * t * (1 + 0.0007 * k)) / (k + 1) for k, f in enumerate(freqs))
    env = np.clip(t / attack, 0, 1) * np.clip((seconds - t) / release, 0, 1)
    _add(m, _norm(s) * env ** 1.5, at, gain)


def _gate(m, t0, spans):
    """Silence the scratch mix inside each (a, b) of film time, with 6 ms edges. This is how 'music never runs
    under a hold marked silent' is made true by construction and not by hoping the tails are short."""
    t = np.arange(m.n) / m.rate + t0
    g = np.ones(m.n)
    for a, b in spans:
        g *= 1 - np.clip((t - a) / 0.006 + 1, 0, 1) * np.clip((b - t) / 0.006 + 1, 0, 1)
    m.L *= g
    m.R *= g


def _lay(mix, m, at, gain):
    i = int(round(at * mix.rate))
    k = min(m.n, mix.n - i)
    if k > 0:
        mix.L[i:i + k] += m.L[:k] * gain
        mix.R[i:i + k] += m.R[:k] * gain


def movement_1(mix, at=0.0, cues_=None, gain=1.0):
    """I · the tune wanders. 36 s. `at` is where the act starts in `mix`. Returns the paving beat times (film
    time) so the editor can lay a sett on every beat: hoof(mix, t, 'pavement', 0.6)."""
    c = cues(cues_)
    t0, t1 = c["act1"], c["act2"]
    m = Mix(t1 - t0)
    L = lambda t: t - t0
    # 1.2 straight up the scale, broken off at the tree
    so, tr = c["set_off"], c["tree"]
    step = (tr - so) / 3.18
    for k, f in enumerate((D4, E4, FS4)):
        _pl(m, L(so + step * k), f, 1.0, 0.16, -0.5)
    _pl(m, L(tr - 0.16), FS4, 0.4, 0.16, -0.45, stop=0.12)             # the same note again, choked: nose to trunk
    # round the tree: back a note, then on
    rt, bo = c["round_tree"], c["boulder"]
    n1 = (E4, D4, E4, FS4, A4)
    for k, f in enumerate(n1):
        _pl(m, L(rt + 0.1 + (min(bo, rt + 2.2) - rt - 0.1) * k / len(n1)), f, 0.9, 0.15, -0.3)
    # over the boulder
    lp0, lp1 = c["loop"]
    for k, f in enumerate((B4, A4)):
        _pl(m, L(bo + (lp0 - bo) * 0.35 * k), f, 0.9, 0.15, 0.0)
    # the loop: the three-note turn
    for k, f in enumerate(TURN):
        _pl(m, L(lp0 + 0.1 + (lp1 - lp0 - 0.1) * k / 3), f, 0.8, 0.17, 0.35)
    wa = c["water"]
    _pl(m, L(lp1 + (wa - lp1) * 0.1), B4, 0.6, 0.14, 0.5)
    _pl(m, L(lp1 + (wa - lp1) * 0.55), D5, 0.5, 0.14, 0.55)
    # 1.4 the herd: the whole tune three times, quicker and louder as time is compressed
    h0, h1 = c["herd"]
    d1, d2 = c["dims"]
    spans = ((h0, d1 - 0.55, 0.08), (d1 + 0.45, d2 - 0.5, 0.115), (d2 + 0.4, h1, 0.15))
    for a, b, g in spans:
        for k, f in enumerate(WANDER):
            _pl(m, L(a + (b - a) * k / len(WANDER)), f, 0.55, g, -0.6 + 1.2 * k / len(WANDER))
    for d in c["dims"]:
        _dr(m, L(d - 0.8), 1.6, (73.4, 110.0), 0.12, 0.7, 0.7)
    # 1.5 one note of the straight scale, not followed
    _pl(m, L(c["hoof_off"]), A4, 1.0, 0.17, -0.4)
    # 1.6 paving: the tune stiff, in strict time
    p0, p1 = c["paving"]
    q0, q1 = c["paved_loop"]
    beats = []
    pre, post = WANDER[:10], WANDER[13:]
    beat = (q0 - p0) / len(pre)
    for k, f in enumerate(pre):
        tb = p0 + beat * k
        _sq(m, L(tb), f, beat * 0.9, 0.05, pan_x(160 + 45 * k))
        beats.append(tb)
    tb_ = (q1 - q0) / 3
    for k, f in enumerate(TURN):                                        # solemn: longer, doubled an octave down
        tb = q0 + tb_ * k
        _sq(m, L(tb), f, tb_ * 0.96, 0.055, 0.45)
        _sq(m, L(tb), f / 2, tb_ * 0.96, 0.035, 0.45)
        beats.append(tb)
    for k, f in enumerate(post):
        tb = q1 + beat * k
        if tb < p1 - 0.05:
            _sq(m, L(tb), f, beat * 0.9, 0.05, 0.6)
            beats.append(tb)
    # 1.7 unresolved on E
    _sq(m, L(c["last_note"]), E4, 1.3, 0.045, 0.6)
    _gate(m, t0, [(t0, so - 0.02), (tr, rt), (wa, h0 - 0.02), (h1 + 0.3, c["hoof_off"] - 0.02),
                  (c["hoof_off"] + 0.75, p0 - 0.02), (c["act1_silence"], t1 + 1)])
    _lay(mix, m, at, gain)
    return beats


def movement_2(mix, at=36.0, cues_=None, gain=1.0):
    """II · the tune ground up. 40 s. `at` is where the act starts in `mix`."""
    c = cues(cues_)
    t0, t1 = c["act2"], c["act3"]
    m = Mix(t1 - t0 + 1.5)
    L = lambda t: t - t0
    five = (D4, E4, FS4, A4, B4)
    # 2.2 five jobs, five notes, properly
    for k, (tj, f) in enumerate(zip(c["jobs"], five)):
        _pl(m, L(tj), f, 1.2, 0.15, -0.2 + 0.1 * k)
    # 2.3 the wandering tune over the jobs, twice as fast, then four times: notes run into each other
    for (a, b), g, ln in ((c["round2"], 0.13, 0.5), (c["round3"], 0.14, 0.45)):
        for k, f in enumerate(WANDER):
            _pl(m, L(a + (b - a) * k / len(WANDER)), f, ln, g, -0.3 + 0.6 * k / len(WANDER))
    # 2.4 the stamp on the bad drawing: B, a quarter-tone flat
    _pl(m, L(c["stamp_bad"]), B_FLAT, 0.8, 0.16, 0.0)
    # 2.5 drowning: the five, as fast as they go, order lost, in any octave, rising to the cut
    a, b = c["drown"]
    rs = _rs("drown", a)
    t = a
    while t < b - 0.03:
        u = (t - a) / (b - a)
        f = five[rs.randint(5)] * (0.5, 1, 1, 2)[rs.randint(4)]
        n = _n(0.07 + 0.1 * (1 - u))
        tt = np.arange(n) / RATE
        s = (2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * tt)) + 0.35 * u * np.tanh(4 * np.sin(2 * np.pi * f * tt))) * np.exp(-tt * 14)
        _add(m, _fade(s, 0.002, 0.004), L(t), 0.07 + 0.09 * u, rs.uniform(-0.6, 0.6))
        t += 0.17 - 0.125 * u ** 0.7
    # 2.6 the heap settles into the hill: one low note falling a fifth
    a, b = c["settle"]
    n = _n(b - a + 0.8)
    tt = np.arange(n) / RATE
    f = 110.0 * (73.4 / 110.0) ** np.clip(tt / (b - a), 0, 1) ** 1.3
    ph = 2 * np.pi * np.cumsum(f) / RATE
    s = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * np.clip(tt / 0.5, 0, 1) * np.clip((b - a + 0.8 - tt) / 0.8, 0, 1)
    _add(m, _norm(s), L(a), 0.05)
    # the binding: D E F#, one a turn, slow
    for tk, f in zip(c["binding"], (D4, E4, FS4)):
        _pl(m, L(tk), f, 1.4, 0.11, -0.35, soft=2)
    # 2.7 the bud, then seven leaves
    _pl(m, L(c["bud"]), A4, 1.1, 0.08, -0.35, soft=1)
    seven = (B4, D5, E5, FS5, A5, B5, D6)
    a, b = c["leaves"]
    for k, f in enumerate(seven):
        _pl(m, L(a + (b - a) * k / 7 + 0.03), f, 0.9, 0.07, -0.4 + 0.06 * k, damp=0.998)
    # 2.8 the leaves let go: the same seven, falling
    a, b = c["loosen"]
    for k, f in enumerate(reversed(seven)):
        _pl(m, L(a + (b - a) * k / 6), f, 1.0, 0.065, -0.3 + 0.1 * k, damp=0.998)
    _gate(m, t0, [(t0 - 1, c["jobs"][0] - 0.02), (c["bad"], c["stamp_bad"] - 0.01), (c["stamp_bad"] + 0.7, c["drown"][0] - 0.01),
                  (c["drown"][1], c["settle"][0] - 0.01), (c["binding"][-1] + 0.9, c["bud"] - 0.01)])
    _lay(mix, m, at, gain)


def movement_3(mix, at=76.0, cues_=None, gain=1.0):
    """III · the tune played straight, once, by her feet. 40 s plus the credit's silence. `at` is where the act
    starts in `mix`. The notes of 3.3, 3.4 and 3.5 are the notes of picture events (a stone set, a nudge, her
    weight on a slab): if the act's own foley already sounds them (stone_set(pitch=...), nudge(), passed()),
    call movement_3(..., events=False) and take only the drone and the survey note from here."""
    return _movement_3(mix, at, cues_, gain, True)


def _movement_3(mix, at, cues_, gain, events):
    c = cues(cues_)
    t0, t1 = c["act3"], c["end"]
    m = Mix(t1 - t0)
    L = lambda t: t - t0
    # 3.1 a low drone under the water, out before her look
    _dr(m, L(t0 + 0.3), c["look_across"] - t0 - 0.3, (73.4, 110.0), 0.05, 1.2, 1.2)
    # 3.2 the survey: one held D4, as long as the watcher swims the line. The first long straight sound in the film.
    a, b = c["survey"]
    n = _n(b - a)
    tt = np.arange(n) / RATE
    s = np.sin(2 * np.pi * D4 * tt) * np.clip(tt / 0.25, 0, 1) * np.clip((b - a - tt) / 0.12, 0, 1)
    _add_sweep(m, s, L(a), 0.045, pan_x(180), pan_x(780))
    if events:
        # 3.3 six at once: a pluck per stone at the lane's pitch, the slab an octave down
        for lane, times in c["sets"].items():
            for tk in times:
                _pl(m, L(tk), SCALE[lane - 1], 1.0, 0.13, lane_pan(lane), soft=1)
        for lane, tk in c["slabs"].items():
            _pl(m, L(tk), SCALE[lane - 1] / 2, 1.5, 0.15, lane_pan(lane), soft=2)
        for k, f in enumerate(TURN):                                    # 4's loop: the bog's turn, fast
            _pl(m, L(c["loop4"] + 0.13 * k), f, 0.5, 0.12, lane_pan(4))
        # 3.4 the test: D E F#, straight, in time; then the A is wrong
        for k, tk in enumerate(c["nudges"]):
            _pl(m, L(tk), SCALE[k], 1.3, 0.2, lane_pan(k + 1))
        s = _string(A_WRONG, 0.6, _rs("wrongA", c["rock"])) * np.exp(-_t(0.6) * 9)
        _add(m, s, L(c["rock"]), 0.2, lane_pan(4))
        # the retest: A, true, left to ring
        _pl(m, L(c["retest"]), A4, 2.6, 0.22, lane_pan(4), damp=0.9982)
        for k, f in enumerate((D4, E4, FS4, B4, D5, A4)):               # the school, once, softly; 4 last
            _pl(m, L(c["joined"] + 0.07 * k), f, 1.0, 0.06, 0.6 + 0.02 * k, soft=1)
        # 3.5 the scale completed, and then played by her feet
        for tk, f, ln in zip(c["last_nudges"], (B4, D5), (5, 6)):
            _pl(m, L(tk), f, 1.3, 0.2, lane_pan(ln))
        for k, tk in enumerate(c["crossing"]):
            _pl(m, L(tk), SCALE[k], 1.6, 0.22, lane_pan(k + 1), damp=0.9975)
            _pl(m, L(tk), SCALE[k] / 2, 1.2, 0.07, lane_pan(k + 1), soft=2)
    # the drone returns with the road and thins at the end
    d0, d1 = c["drone_out"]
    a = c["last_nudges"][0] - 0.4
    _dr(m, L(a), d1 - a, (73.4, 110.0, 146.8), 0.055, 1.5, d1 - d0)
    _gate(m, t0, [(c["look_across"], c["survey"][0] - 0.01), (c["survey"][1], c["build"][0] + 0.5),
                  (c["build"][1], c["nudges"][0] - 0.01), (c["rock"] + 0.32, c["retest"] - 0.01), (c["credit"], t1 + 1)])
    _lay(mix, m, at, gain)


def music(mix, at=0.0, cues_=None, gain=1.0, events=True):
    """The whole piece, laid so that film time 0 is at `at` in `mix`. `cues_` overrides any of sound.CUES.
    events=False leaves out the act 3 notes that belong to picture events (see movement_3)."""
    c = cues(cues_)
    beats = movement_1(mix, at + c["act1"], cues_, gain)
    movement_2(mix, at + c["act2"], cues_, gain)
    _movement_3(mix, at + c["act3"], cues_, gain, events)
    return beats


def music_silences(cues_=None):
    """The stretches of film time in which music() lays nothing at all (gated to exact zero)."""
    c = cues(cues_)
    return [(0.0, c["set_off"] - 0.02), (c["tree"] + 0.006, c["round_tree"] - 0.006), (c["water"] + 0.006, c["herd"][0] - 0.03),
            (c["herd"][1] + 0.31, c["hoof_off"] - 0.03), (c["hoof_off"] + 0.76, c["paving"][0] - 0.03),
            (c["act1_silence"] + 0.006, c["jobs"][0] - 0.03), (c["bad"] + 0.006, c["stamp_bad"] - 0.02),
            (c["stamp_bad"] + 0.71, c["drown"][0] - 0.02), (c["drown"][1] + 0.006, c["settle"][0] - 0.02),
            (c["binding"][-1] + 0.91, c["bud"] - 0.02), (c["look_across"] + 0.006, c["survey"][0] - 0.02),
            (c["survey"][1] + 0.006, c["build"][0] + 0.49), (c["build"][1] + 0.006, c["nudges"][0] - 0.02),
            (c["rock"] + 0.33, c["retest"] - 0.02), (c["credit"] + 0.006, c["end"])]


# ====================================================================== the board's foley, by time ===

def foley(mix, at=0.0, cues_=None, gain=1.0, moos=False):
    """Every effect of the board's sound plan (e), laid at the BOARD's times with this library, WITHOUT the music.
    It is a reference lay and a fallback for the assembly: where an act has its own event table (plant frames,
    contacts, the watcher's decision trace) the act should place these sounds from that table instead, and not
    call this as well. Hoof plants here are a metronome between the board's beat times because this file does
    not know the puppet's plant frames; that is a known approximation.
    moos=True adds three moos the board does not ask for (alarmed at the bog, puzzled at the fence post, content
    in the far grass)."""
    c = cues(cues_)
    g = gain
    T = lambda t: at + t
    # ---------------- act 1
    wind(mix, T(0.0), 35.2, 0.035 * g, out_by=35.0)
    for a, b, x0, x1 in ((3.2, 4.4, 120, 150), (5.3, 6.95, 150, 300), (7.7, 9.5, 300, 420), (10.5, 11.9, 440, 640), (12.5, 13.9, 650, 800)):
        walk(mix, [(T(a + 0.44 * k), x0 + (x1 - x0) * k * 0.44 / (b - a)) for k in range(int((b - a) / 0.44) + 1)], "turf", 1.0, 0.2 * g)
    bell(mix, T(4.5), 1.0, gain=0.2 * g, pan=pan_x(140))
    _add(mix, _norm(_tick(_rs("slip", 10.2), 0.03, 1500, 6000)), T(10.2), 0.25 * g, pan_x(500))         # the slip
    hoof(mix, T(12.0), "mud", 1.4, 0.36 * g, pan_x(716))
    hoof(mix, T(12.35), "water", 1.0, 0.2 * g, pan_x(716))
    water(mix, T(13.8), 1.4, 0.07 * g, fade_in=0.5, fade_out=0.5)
    for k in range(4):                                                   # the herd, nose to tail
        walk(mix, [(T(14.6 + 0.3 * k + 0.47 * j), 140 + 55 * j) for j in range(6)], "turf", 0.9, 0.11 * g)
    for d in c["dims"]:
        walk(mix, [(T(d + 0.5 + 0.2 * j), 300 + 70 * j) for j in range(5)], "turf", 0.9, 0.13 * g)
    for k in range(9):                                                   # a roof a click, rising down the row
        _add(mix, _norm(_tick(_rs("roof", k), 0.03, 300, 1800 + 320 * k)), T(20.7 + 0.25 * k), 0.14 * g, pan_x(150 + 75 * k))
    for tw in (23.03, 23.28):                                            # the saw
        fish_move(mix, T(tw), 0.22, 2.5, 0.12 * g, pan_x(331))
    mix.thud(T(c["tree_falls"]), freq=52, gain=0.45 * g, pan=pan_x(420), seconds=0.6)                    # the act's one loud event
    _add(mix, _norm(_tick(_rs("tree", 0), 0.08, 200, 2500)), T(c["tree_falls"]), 0.2 * g, pan_x(420))
    hoof(mix, T(24.5), "gravel", 1.5, 0.22 * g, pan_x(500))
    hoof(mix, T(25.0), "gravel", 1.2, 0.2 * g, pan_x(716))
    hoof(mix, T(26.6), "turf", 0.5, 0.12 * g, pan_x(340))                # one hoof off the path, no weight on it
    _add(mix, _norm(_tick(_rs("post", 0), 0.04, 300, 1500)), T(26.8), 0.3 * g, pan_x(350))               # the fence post
    beats = movement_1(Mix(1.0), 0.0, cues_, 0.0)                        # only for the beat times
    for tb in beats:
        hoof(mix, T(tb), "pavement", 0.6, 0.12 * g, pan_x(160 + 640 * (tb - 27.5) / 5.5))
    bell(mix, T(33.4), 1.0, gain=0.22 * g, pan=pan_x(800))
    # ---------------- act 2
    room(mix, T(36.0), c["drown"][1] - 36.0, 0.02 * g)                   # ends dead at the cut (64.6)
    pencil(mix, T(36.6), 2.2, lambda u: 0.35 + 0.65 * abs(math.sin(4.2 * math.pi * u)) * (u < 0.97), 1.0, 0.06 * g, -0.2)
    bell(mix, T(39.0), 0.6, gain=0.14 * g, pan=-0.2, rings=1)

    def jobs(t0, each, gg, haste):
        pencil_stroke(mix, T(t0 + 0.3 * each), 0.3 * each, 1.0 + 0.5 * haste, 0.06 * gg, -0.2)
        for k in range(3):
            paper_flip(mix, T(t0 + each * (1.25 + 0.2 * k)), 0.09 * gg, -0.1)
        brush(mix, T(t0 + each * 2.3), 0.3 * each + 0.1, 0.07 * gg, 0.0)
        lever(mix, T(t0 + each * 3.3), 0.24 * gg, 0.2)
        st = 4.45 if haste < 1 else 4.2                                  # the last round: she stamps before she has finished looking
        stamp(mix, T(t0 + each * st), 1.0 - 0.3 * haste, 0.34 * gg, -0.1)
        paper_slide(mix, T(t0 + each * (st + 0.15)), min(0.2, 0.2 * each), 0.08 * gg, 0.0, 0.5)
    jobs(39.5, 2.0, g, 0.0)
    jobs(49.5, 0.8, g, 0.5)
    jobs(53.5, 0.4, g, 1.0)
    for tb in (58.25, 58.9):
        bell(mix, T(tb), 0.45, gain=0.09 * g, pan=-0.2, rings=1)
    stamp(mix, T(60.0), 1.3, 0.36 * g, -0.1)
    paper_slide(mix, T(60.3), 0.25, 0.08 * g, 0.0, 0.5)
    d0, d1 = c["drown"]
    paper_pile(mix, T(d0), d1 - d0, 4.0, 30.0, 0.18 * g, 0.1)
    tk, k = d0, 0
    while tk < d1 - 0.15:
        u = (tk - d0) / (d1 - d0)
        (stamp if k % 3 == 0 else pencil_stroke if k % 3 == 1 else lever)(mix, T(tk), gain=(0.2, 0.05, 0.14)[k % 3] * g, pan=-0.2 + 0.2 * (k % 3))
        tk += 0.42 - 0.3 * u
        k += 1
    _hard_cut(mix, T(d1), T(64.9))                                       # 'then cut to nothing'
    bell(mix, T(64.9), 0.5, gain=0.16 * g, pan=-0.1, rings=1, under=600, seconds=0.4)   # under paper: short, the heap damps it
    wind(mix, T(65.5), 10.0, 0.022 * g, out_by=10.0)                     # to 75.5
    knife_cut(mix, T(68.0), 0.42, 0.42 * g, -0.35)
    graft_seat(mix, T(69.3), 0.2 * g, -0.35)
    binding(mix, T(69.5), 3, 0.5, 0.11 * g, -0.35)
    bell(mix, T(71.2), 0.3, gain=0.07 * g, pan=-0.25, rings=1)
    water(mix, T(75.0), 1.3, 0.05 * g, fade_in=1.0, fade_out=0.3)
    # ---------------- act 3
    water(mix, T(76.0), 43.6, 0.035 * g, under=True, ducks=[(T(100.2), T(101.2), 0.5)],
          fade_in=0.3, fade_out=1.1)                                     # fading from 118.5, silent by 119.6
    splash(mix, T(78.0), 1.0, 0.24 * g, pan_x(150))
    bubbles(mix, T(78.6), 3, 0.3, 0.05 * g, pan_x(150))
    bell(mix, T(79.0), 0.8, gain=0.2 * g, pan=pan_x(120), under=900)
    fish_move(mix, T(81.0), 2.0, 0.5, 0.04 * g, pan_x(180), pan_x(780))
    for lane, times in c["sets"].items():
        for tk in times:
            stone_set(mix, T(tk), None, 0.16 * g, lane_pan(lane))
            if lane == 1:                                                # 1 taps each stone twice
                for dt in (0.18, 0.32):
                    _add(mix, _norm(_tick(_rs("tap", tk + dt), 0.02, 500, 2400)), T(tk + dt), 0.06 * g, lane_pan(1))
    stone_set(mix, T(87.0), None, 0.22 * g, lane_pan(4), dull=True)
    for lane, tk in c["slabs"].items():
        slab_on(mix, T(tk), None, 0.2 * g, lane_pan(lane))
    for k, tk in enumerate(c["nudges"]):
        _add(mix, _norm(_tick(_rs("nose", tk), 0.03, 300, 1500)), T(tk), 0.07 * g, lane_pan(k + 1))
    slab_rocks(mix, T(c["rock"]), A4, 0.0001, lane_pan(4))               # clacks and pebble only: the wrong A is the music's
    for k in range(4):
        tk = c["rock"] + 0.03 + 0.17 * k + 0.02 * k * k
        hoof(mix, T(tk), "wood", 1.0, (0.24, 0.17, 0.1, 0.06)[k] * g, lane_pan(4) + (0.12 if k % 2 else -0.12))
    _add(mix, _norm(_tick(_rs("peb", 0), 0.02, 2000, 6000)), T(c["rock"] + 0.22), 0.09 * g, lane_pan(4))
    _add(mix, _norm(_tick(_rs("peb", 1), 0.05, 300, 1500)), T(c["rock"] + 0.74), 0.06 * g, lane_pan(4))
    refuse(mix, T(98.6), 0.14 * g, lane_pan(4) + 0.1)
    fish_move(mix, T(99.2), 0.35, 1.0, 0.06 * g, lane_pan(4) + 0.1)
    fish_move(mix, T(99.8), 0.35, 1.0, 0.06 * g, lane_pan(4) + 0.1)
    tail_flick(mix, T(100.0), 0.05 * g, lane_pan(4), beats=2)
    hoof(mix, T(102.6), "pavement", 1.2, 0.26 * g, lane_pan(4))          # the wedge: one firm step of stone
    passed(mix, T(c["retest"]), A4, 0.0001, lane_pan(4))                 # the wash and bubbles; the true A is the music's
    hoof(mix, T(105.4), "slab", 0.5, 0.14 * g, lane_pan(1))              # the weight not yet on it
    for k, tk in enumerate(c["crossing"]):
        if k:
            hoof(mix, T(tk), "slab", 1.1, 0.22 * g, lane_pan(k + 1))
    hoof(mix, T(105.82), "slab", 1.1, 0.22 * g, lane_pan(1))
    bell(mix, T(108.2), 1.0, gain=0.2 * g, pan=lane_pan(4))
    hoof(mix, T(c["bank"]), "turf", 1.0, 0.2 * g, pan_x(800))
    bell(mix, T(115.0), 0.9, gain=0.2 * g, pan=pan_x(850), seconds=1.6)
    if moos:
        moo(mix, T(12.1), "alarmed", 0.26 * g, pan_x(716))
        moo(mix, T(27.0), "puzzled", 0.16 * g, pan_x(340))
        moo(mix, T(111.5), "content", 0.16 * g, pan_x(850))


def _hard_cut(mix, t0, t1):
    """Zero everything already in the mix between t0 and t1 (3 ms edge in). For the board's 'cut to nothing'."""
    i, j = int(t0 * mix.rate), min(mix.n, int(t1 * mix.rate))
    k = int(0.003 * mix.rate)
    for ch in (mix.L, mix.R):
        ch[max(0, i - k):i] *= np.linspace(1, 0, i - max(0, i - k))
        ch[i:j] = 0.0


def film_sound(mix, at=0.0, cues_=None, moos=False, reverb=0.0):
    """The whole plan (e): foley() and music() together at the board's times. The assembly's fallback."""
    foley(mix, at, cues_, 1.0, moos)
    beats = music(mix, at, cues_)
    if reverb:
        mix.reverb(reverb)      # NB the kit's reverb smears into the silent holds; measured in SOUND.md. Default: none.
    return beats


# ==================================================================== rendering and measuring ===

def write_wav(path, mix, half_rate=False):
    """Write a Mix as it is (no normalising: the kit's master() rescales, which would hide the real levels).
    half_rate=True writes 22.05 kHz (each pair of samples averaged) to keep a two-minute file small.
    Returns the number of samples that had to be clipped."""
    st = np.stack([mix.L, mix.R], 1)
    rate = RATE
    if half_rate:
        st = 0.5 * (st[0:len(st) // 2 * 2:2] + st[1:len(st) // 2 * 2:2])
        rate = RATE // 2
    clipped = int((np.abs(st) > 1.0).sum())
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())
    return clipped


def db(x):
    return -120.0 if x <= 1e-6 else round(20 * math.log10(x), 1)


def measure(mix, t0=0.0, t1=None):
    """Numbers for a stretch of a Mix. All MEASURED from the samples; none of them says how it sounds."""
    i, j = int(t0 * mix.rate), mix.n if t1 is None else int(t1 * mix.rate)
    L, R = mix.L[i:j], mix.R[i:j]
    mono = 0.5 * (L + R)
    peak = float(max(np.abs(L).max(), np.abs(R).max())) if len(L) else 0.0
    out = dict(peak_dbfs=db(peak), peak=round(peak, 4))
    if peak <= 1e-6:
        out.update(rms_dbfs=-120.0, seconds=0.0, centroid_hz=0, dominant_hz=0, lr_db=0.0, onset_ms=0.0)
        return out
    env = np.maximum(np.abs(L), np.abs(R))
    k = max(1, int(0.005 * mix.rate))
    sm = np.convolve(env, np.ones(k) / k, "same")
    on = np.nonzero(sm > sm.max() * 10 ** (-40 / 20))[0]
    a, b = on[0], on[-1] + 1
    act = np.concatenate([L[a:b], R[a:b]])
    spec = np.abs(np.fft.rfft(mono[a:b] * np.hanning(b - a))) ** 2
    f = np.fft.rfftfreq(b - a, 1 / mix.rate)
    pk = int(np.argmax(env))
    out.update(rms_dbfs=db(float(np.sqrt((act ** 2).mean()))),
               seconds=round((b - a) / mix.rate, 3),                       # length above -40 dB of its own peak
               centroid_hz=int(round(float((spec * f).sum() / (spec.sum() + 1e-20)))),
               dominant_hz=int(round(float(f[int(np.argmax(spec))]))),
               lr_db=round(db(float(np.sqrt((L ** 2).mean()) + 1e-9)) - db(float(np.sqrt((R ** 2).mean()) + 1e-9)), 1),
               onset_ms=round((pk - a) / mix.rate * 1000, 1))               # first -40 dB crossing to the peak
    return out


def pitch_of(mix, t0, t1, lo=60, hi=1500, near=None):
    """The strongest spectral peak between lo and hi Hz (or within 8 % of `near`) in a stretch, refined by
    parabolic interpolation."""
    if near:
        lo, hi = near * 0.92, near * 1.08
    i, j = int(t0 * mix.rate), int(t1 * mix.rate)
    x = 0.5 * (mix.L[i:j] + mix.R[i:j])
    n = 1 << 17
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), n))
    f = np.fft.rfftfreq(n, 1 / mix.rate)
    m = (f >= lo) & (f <= hi)
    k = int(np.argmax(X * m))
    a, b_, c_ = np.log(X[k - 1] + 1e-12), np.log(X[k] + 1e-12), np.log(X[k + 1] + 1e-12)
    d = 0.5 * (a - c_) / (a - 2 * b_ + c_ + 1e-12)
    return round(float((k + d) * mix.rate / n), 1)


LIBRARY = [
    # name, seconds of Mix, call
    ("hoof_turf_touch", 0.8, lambda m: hoof(m, 0.1, "turf", 0.5)),
    ("hoof_turf_walk", 0.8, lambda m: hoof(m, 0.1, "turf", 1.0)),
    ("hoof_turf_heavy", 0.8, lambda m: hoof(m, 0.1, "turf", 1.6)),
    ("hoof_pavement_touch", 0.8, lambda m: hoof(m, 0.1, "pavement", 0.5)),
    ("hoof_pavement_walk", 0.8, lambda m: hoof(m, 0.1, "pavement", 1.0)),
    ("hoof_pavement_heavy", 0.8, lambda m: hoof(m, 0.1, "pavement", 1.6)),
    ("hoof_slab", 0.8, lambda m: hoof(m, 0.1, "slab", 1.1)),
    ("hoof_gravel", 0.8, lambda m: hoof(m, 0.1, "gravel", 1.0)),
    ("hoof_mud", 1.0, lambda m: hoof(m, 0.1, "mud", 1.4)),
    ("hoof_water", 0.8, lambda m: hoof(m, 0.1, "water", 1.0)),
    ("hoof_wood", 0.8, lambda m: hoof(m, 0.1, "wood", 1.0)),
    ("walk_turf_then_pavement", 5.0, lambda m: (walk(m, [0.2 + 0.5 * k for k in range(4)], "turf"),
                                                 walk(m, [2.4 + 0.5 * k for k in range(4)], "pavement"))),
    ("bell", 2.0, lambda m: bell(m, 0.1)),
    ("bell_settling", 2.0, lambda m: bell(m, 0.1, 0.3, rings=1)),
    ("bell_startled", 2.4, lambda m: bell(m, 0.1, 1.5, rings=3)),
    ("bell_under_paper", 2.0, lambda m: bell(m, 0.1, 0.5, rings=1, under=600)),
    ("bell_under_water", 2.0, lambda m: bell(m, 0.1, 0.8, under=900)),
    ("moo_content", 2.0, lambda m: moo(m, 0.1, "content")),
    ("moo_puzzled", 1.5, lambda m: moo(m, 0.1, "puzzled")),
    ("moo_alarmed", 1.5, lambda m: moo(m, 0.1, "alarmed")),
    ("pencil_line", 2.6, lambda m: pencil(m, 0.1, 2.2, lambda u: 0.35 + 0.65 * abs(math.sin(4.2 * math.pi * u)))),
    ("pencil_stroke", 1.0, lambda m: pencil_stroke(m, 0.1, 0.5)),
    ("pencil_hard", 1.0, lambda m: pencil_stroke(m, 0.1, 0.5, pressure=2.0)),
    ("stamp", 0.8, lambda m: stamp(m, 0.1)),
    ("stamp_careless", 0.8, lambda m: stamp(m, 0.1, 0.6)),
    ("lever", 0.8, lambda m: lever(m, 0.1)),
    ("brush", 1.0, lambda m: brush(m, 0.1)),
    ("paper_flip", 0.5, lambda m: paper_flip(m, 0.1)),
    ("paper_land", 0.5, lambda m: paper_land(m, 0.1)),
    ("paper_slide", 0.8, lambda m: paper_slide(m, 0.1, 0.2, pan=0.0, pan_to=0.5)),
    ("paper_pile", 4.2, lambda m: paper_pile(m, 0.1, 3.6)),
    ("knife_cut", 1.2, lambda m: knife_cut(m, 0.1)),
    ("graft_seat", 0.6, lambda m: graft_seat(m, 0.1)),
    ("creak", 1.0, lambda m: creak(m, 0.1)),
    ("binding", 2.2, lambda m: binding(m, 0.1)),
    ("wind", 8.0, lambda m: wind(m, 0.0, 8.0, out_by=8.0)),
    ("room", 6.0, lambda m: room(m, 0.0, 6.0)),
    ("water_bank", 8.0, lambda m: water(m, 0.0, 8.0)),
    ("water_under", 8.0, lambda m: water(m, 0.0, 8.0, under=True)),
    ("splash_under", 1.2, lambda m: splash(m, 0.1)),
    ("bubbles", 1.0, lambda m: bubbles(m, 0.1)),
    ("fish_drift", 1.2, lambda m: fish_move(m, 0.1, 0.8, 0.4, pan=-0.4, pan_to=0.4)),
    ("fish_swim", 0.8, lambda m: fish_move(m, 0.1, 0.3, 1.0)),
    ("fish_dart", 0.6, lambda m: fish_move(m, 0.1, 0.18, 2.0)),
    ("tail_flick", 0.6, lambda m: tail_flick(m, 0.1)),
    ("fish_turn", 1.0, lambda m: fish_turn(m, 0.1)),
    ("stone_set", 1.6, lambda m: stone_set(m, 0.1, FS4)),
    ("stone_dropped", 0.8, lambda m: stone_set(m, 0.1, dull=True)),
    ("slab_on", 2.0, lambda m: slab_on(m, 0.1, FS4)),
    ("nudge_firm", 2.0, lambda m: nudge(m, 0.1, A4)),
    ("slab_rocks", 2.0, lambda m: slab_rocks(m, 0.1, A4)),
    ("refuse", 1.2, lambda m: refuse(m, 0.1)),
    ("passed", 3.4, lambda m: passed(m, 0.1, A4)),
    ("refuse_then_passed", 6.5, lambda m: (slab_rocks(m, 0.2), refuse(m, 1.3), passed(m, 3.4))),
]


def render_all(out=OUT, verbose=True):
    out.mkdir(parents=True, exist_ok=True)
    levels = {}
    for name, sec, call in LIBRARY:
        m = Mix(sec)
        call(m)
        clipped = write_wav(out / f"{name}.wav", m)
        levels[name] = dict(measure(m), clipped=clipped)
        if verbose:
            v = levels[name]
            print(f"{name:26s} peak {v['peak_dbfs']:6.1f} dBFS  rms {v['rms_dbfs']:6.1f}  len {v['seconds']:5.2f} s  "
                  f"centroid {v['centroid_hz']:5d} Hz  dominant {v['dominant_hz']:5d} Hz  onset {v['onset_ms']:6.1f} ms  L-R {v['lr_db']:+.1f} dB")
    c = cues()
    parts = {}
    for name, fn, a, b in (("music_1_wanders", movement_1, c["act1"], c["act2"]), ("music_2_ground_up", movement_2, c["act2"], c["act3"]),
                           ("music_3_straight", movement_3, c["act3"], c["end"])):
        m = Mix(b - a)
        fn(m, 0.0)
        clipped = write_wav(out / f"{name}.wav", m)
        parts[name] = dict(measure(m), clipped=clipped, film_span=[a, b])
    mm = Mix(c["end"])
    music(mm)
    parts["music (the three together, not written: it is the three files end to end)"] = dict(measure(mm), clipped=int((np.abs(mm.L) > 1).sum() + (np.abs(mm.R) > 1).sum()))
    fo = Mix(c["end"])
    foley(fo)
    parts["foley (board times, no music; not written)"] = dict(measure(fo), clipped=int((np.abs(fo.L) > 1).sum() + (np.abs(fo.R) > 1).sum()))
    full = Mix(c["end"])
    film_sound(full)
    parts["film_reference"] = dict(measure(full), clipped=write_wav(out / "film_reference.wav", full, half_rate=True))
    if verbose:
        for k, v in parts.items():
            print(f"{k[:26]:26s} peak {v['peak_dbfs']:6.1f} dBFS  rms {v['rms_dbfs']:6.1f}  clipped {v['clipped']}")
    # the music's silences: peak inside each must be exactly zero
    sil = []
    for a, b in music_silences():
        sil.append(dict(span=[round(a, 3), round(b, 3)], music_peak=measure(mm, a, b)["peak"], film_peak_dbfs=measure(full, a, b)["peak_dbfs"],
                        film_rms_dbfs=db(float(np.sqrt((np.concatenate([full.L[int(a * RATE):int(b * RATE)], full.R[int(a * RATE):int(b * RATE)]]) ** 2).mean())))))
    # the board's holds, in the full reference mix
    holds = {}
    for name, a, b in (("1.1 title 0.8-3.0", 0.8, 3.0), ("1.2 at the tree 7.0-7.6", 7.0, 7.6), ("1.5 after the tree 23.8+0.6..24.3", 24.4, 24.5),
                       ("1.5 her look 25.5-26.5", 25.5, 26.5), ("1.7 silence 35.2-36.0", 35.2, 36.0), ("2.4 insert 55.5-57.5", 55.5, 57.5),
                       ("2.5 silence 64.6-64.9", 64.6, 64.9), ("2.5 silence 65.2-65.5", 65.3, 65.5), ("2.7 the wait 71.6-73.3", 71.6, 73.3),
                       ("3.2 bubble line 83.0-83.5", 83.0, 83.5), ("3.3 hold 93.6-94.0", 93.6, 94.0), ("3.4 97.9-98.6", 98.3, 98.6),
                       ("3.4 stillest second 100.3-101.2", 100.45, 101.2), ("3.4 before it 99.0-99.2", 98.0, 98.2),
                       ("credit 119.6-120", 119.6, 120.0)):
        i, j = int(a * RATE), int(b * RATE)
        x = np.concatenate([full.L[i:j], full.R[i:j]])
        holds[name] = dict(peak_dbfs=db(float(np.abs(x).max())), rms_dbfs=db(float(np.sqrt((x ** 2).mean()))))
    # the pitches that carry meaning
    pitches = dict(
        crossing=[pitch_of(mm, t + 0.05, t + 0.6, near=f) for t, f in zip(c["crossing"], SCALE)],
        nudges=[pitch_of(mm, t + 0.05, t + 0.6, near=f) for t, f in zip(c["nudges"], SCALE)],
        wrong_A=pitch_of(mm, c["rock"] + 0.02, c["rock"] + 0.3, 300, 700),
        true_A=pitch_of(mm, c["retest"] + 0.05, c["retest"] + 0.38, 300, 700),
        stamp_bad_B=pitch_of(mm, c["stamp_bad"] + 0.03, c["stamp_bad"] + 0.6, 300, 700),
        survey_D=pitch_of(mm, c["survey"][0] + 0.3, c["survey"][1] - 0.2, 200, 700),
        settle_start=pitch_of(mm, c["settle"][0] + 0.05, c["settle"][0] + 0.35, 50, 200),
        settle_end=pitch_of(mm, c["settle"][1] + 0.1, c["settle"][1] + 0.6, 50, 200),
    )
    for mood in MOODS:                                        # each moo's fundamental, early and late
        mo = Mix(2.0)
        moo(mo, 0.0, mood)
        sec = MOODS[mood]["seconds"]
        pitches["moo_" + mood] = dict(first_third_hz=pitch_of(mo, 0.05 * sec, 0.35 * sec, 70, 300), last_third_hz=pitch_of(mo, 0.7 * sec, 0.98 * sec, 70, 300))
    bm = Mix(2.0)
    pitches["bell_strikes_s_after_head_turn"] = [round(x, 3) for x in bell(bm, 0.0)]
    # how loud each act is, in the reference mix, second by second
    acts = {}
    for name, a, b in (("act 1", 0, 36), ("act 2", 36, 76), ("act 3", 76, 116), ("credit", 116, 120)):
        acts[name] = dict(music=measure(mm, a, b), foley=measure(fo, a, b), together=measure(full, a, b))
    data = dict(library=levels, music=parts, music_silences=sil, holds=holds, pitches=pitches, acts=acts)
    (out / "levels.json").write_text(json.dumps(data, indent=1))
    if verbose:
        print(json.dumps(dict(music_silences=sil, holds=holds, pitches=pitches, acts=acts), indent=1))
    return data


if __name__ == "__main__":
    render_all()
