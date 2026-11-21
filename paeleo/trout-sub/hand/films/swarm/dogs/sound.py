"""THE DOGS OF TROUTTOWN · sound library, music and cue sheet (law 7).

Everything is synthesized sample by sample with kit.Mix. Nothing is recorded,
nothing is foraged, and nobody on this production has heard any of it: every
claim about this file is a waveform measurement (see SOUND.md).

Convention for every sound in the library:

    name(mix, at, ..., gain=<linear peak>, pan=<-1 left .. +1 right>, under=False)

  mix    a kit.Mix (the film's, or a scratch one)
  at     seconds; the CONTACT lands on `at` (the few sounds with a lead-in say so)
  gain   the signal is normalised to peak 1 before placing, so gain IS the peak
  under  False = heard in air; True = heard through water (low-pass 700 Hz);
         a number = that cut-off in Hz
  return the time the sound ends, so calls can be chained

Each call seeds its own noise from its name and its time, so adding or moving
one call never changes how another call sounds.

Three layers, each callable by itself or together:

    beds(mix)    the two rooms (ABOVE / BELOW) and the swaps between them
    music(mix)   the radio on the step, the town's chimes, the pack's round
    sfx(mix)     every contact sound on the board's cue sheet (part F)
    score(mix)   all three, plus the declared silences

    python3 films/swarm/dogs/sound.py           renders every sound, the music of
                                                each sequence and the whole score to
                                                films/swarm/dogs/sound/*.wav and
                                                prints what it measured
"""

from __future__ import annotations

import json
import math
import sys
import wave
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from kit import Mix, RATE  # noqa: E402

OUT = HERE / "sound"
SECONDS = 180.0
SEQ = {1: (0.0, 28.0), 2: (28.0, 58.0), 3: (58.0, 84.0),
       4: (84.0, 116.0), 5: (116.0, 144.0), 6: (144.0, 180.0)}

# The film's only motif: "Will you fetch it?"  short short long short.
# The voice, the four taps on the rail and the radio all use these onsets.
MOTIF = (0.0, 0.28, 0.56, 1.08)

# Pan positions from the shared contract: porch and door left, water right.
P_DOOR, P_STEP, P_SILL, P_GATE, P_WATER = -0.55, -0.35, -0.1, 0.25, 0.55

UNDER = 700.0  # the BELOW room's low-pass, Hz


# ------------------------------------------------------------ plumbing ---

def _m(name, at, seconds):
    """A scratch Mix seeded from the sound's name and time."""
    seed = (zlib.crc32(name.encode()) + int(round(at * 1000))) % (2 ** 31 - 1)
    return Mix(seconds + 0.05, seed=seed)


def _norm(x):
    p = np.abs(x).max() if len(x) else 0.0
    return x / p if p > 0 else x


def _fade(x, a=0.003, b=0.01):
    na, nb = min(len(x), int(a * RATE)), min(len(x), int(b * RATE))
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nb:
        x[-nb:] *= np.linspace(1, 0, nb)
    return x


def _lp(x, cutoff):
    if len(x) < 8:
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    X *= 1.0 / (1.0 + (f / cutoff) ** 6)      # soft knee, no ringing brick wall
    return np.fft.irfft(X, len(x))


def _bp(x, lo, hi):
    if len(x) < 8:
        return x
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / RATE)
    g = 1.0 / (1.0 + (f / hi) ** 6)
    if lo > 0:
        g *= 1.0 - 1.0 / (1.0 + (f / lo) ** 6)
    return np.fft.irfft(X * g, len(x))


def _add(mix, sig, at, gain=1.0, pan=0.0):
    """mix.add that also accepts a start before 0 (the part before 0 is dropped)."""
    if at < 0:
        sig, at = sig[int(-at * mix.rate):], 0.0
    mix.add(sig, at, gain, max(-1.0, min(1.0, pan)))


def _grit(x, amt=0.6, lo=190, hi=1200):
    """Give a very low sound a part a small speaker can play: its own
    overtones (soft saturation), kept between lo and hi."""
    x = _norm(np.asarray(x, np.float64))
    return x + amt * _norm(_bp(np.tanh(3.0 * x), lo, hi))


def _put(mix, sig, at, gain=1.0, pan=0.0, under=False, norm=True):
    """Normalise, optionally push under water, place. Returns the end time."""
    sig = np.asarray(sig, np.float64)
    if norm:
        sig = _norm(sig)
    if under:
        cut = UNDER if under is True else float(under)
        sig = _lp(sig, cut)
        if norm:
            sig = _norm(sig)
    _add(mix, sig, at, gain, pan)
    return max(0.0, at) + len(sig) / mix.rate


def _t(seconds):
    return np.arange(int(seconds * RATE)) / RATE


def _sweep(f0, f1, seconds, curve=1.0):
    t = _t(seconds)
    f = f0 + (f1 - f0) * (t / max(seconds, 1e-9)) ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / RATE)


def _place(buf, sig, at):
    i = int(at * RATE)
    if i < 0 or i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig


def _ping(freq, seconds, decay):
    t = _t(seconds)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t / decay)


def silence(mix, a, b, fade=0.03):
    """Declare silence: empty the mix between a and b (short fades at the edges).
    Call it AFTER everything that might ring into the gap, BEFORE anything that
    is meant to be heard inside it."""
    i, j = int(a * mix.rate), min(mix.n, int(b * mix.rate))
    k = int(fade * mix.rate)
    for ch in (mix.L, mix.R):
        ch[max(0, i - k):i] *= np.linspace(1, 0, i - max(0, i - k))
        ch[i:j] = 0.0
        ch[j:j + k] *= np.linspace(0, 1, len(ch[j:j + k]))


def duck(mix, a, b, level=0.5, fade=0.2):
    """Turn what is already in the mix down to `level` between a and b."""
    n = mix.n
    env = np.ones(n)
    i, j, k = int(a * mix.rate), min(n, int(b * mix.rate)), int(fade * mix.rate)
    env[i:j] = level
    env[max(0, i - k):i] = np.linspace(1, level, i - max(0, i - k))
    env[j:j + k] = np.linspace(level, 1, len(env[j:j + k]))
    mix.L *= env
    mix.R *= env


# ====================================================================== #
#  THE DOG                                                               #
# ====================================================================== #

def _paw_sig(m, wet=False, claw=True):
    sec = 0.11
    t = _t(sec)
    x = _bp(m.noise(sec), 90, 1500 if not wet else 900) * np.exp(-t * 55)
    x = _norm(x) * 0.6 + 0.8 * np.sin(2 * np.pi * m.rs.uniform(125, 165) * t) * np.exp(-t * 48)
    if claw:
        c = _bp(m.noise(0.012), 2500, 7000) * np.exp(-_t(0.012) * 400)
        _place(x, _norm(c) * 0.35, 0.006 + m.rs.uniform(0, 0.006))
    if wet:
        s = _bp(m.noise(0.09), 500, 2600) * np.hanning(int(0.09 * RATE))
        _place(x, _norm(s) * 0.5, 0.01)
    return _fade(x, 0.001, 0.01)


def paws(mix, at, n=4, every=0.17, gain=0.16, pan=0.0, pan_to=None, wet=False, claw=True, under=False):
    """Paws on the porch boards: a small wooden knock, a click of claws.
    n paws, `every` seconds apart; pan slides to pan_to. wet=True adds a slap."""
    m = _m("paws", at, 0.2)
    end = at
    for k in range(n):
        p = pan if pan_to is None else pan + (pan_to - pan) * k / max(1, n - 1)
        j = m.rs.uniform(-0.012, 0.012) if k else 0.0
        end = _put(mix, _paw_sig(m, wet, claw), at + k * every + j, gain * (0.85 if k % 2 else 1.0), p, under)
    return end


def collar(mix, at, n=3, gain=0.07, pan=0.0, under=False):
    """The red collar's tag: n tiny dull-bright tinks. `at` is the first tink."""
    m = _m("collar", at, 0.6)
    buf = np.zeros(int((0.07 * n + 0.2) * RATE))
    for k in range(n):
        f = m.rs.uniform(2900, 3300)
        s = _ping(f, 0.12, 0.022) + 0.6 * _ping(f * 1.52, 0.12, 0.016) + 0.3 * _ping(f * 2.09, 0.12, 0.01)
        _place(buf, _fade(s, 0.0005, 0.01) * (1.0 if k == 0 else m.rs.uniform(0.4, 0.8)), k * m.rs.uniform(0.05, 0.08))
    return _put(mix, buf, at, gain, pan, under)


def sniff(mix, at, n=2, gain=0.06, pan=0.0, under=False):
    """n short nose puffs."""
    m = _m("sniff", at, 0.6)
    buf = np.zeros(int((0.16 * n + 0.1) * RATE))
    for k in range(n):
        s = _bp(m.noise(0.1), 900, 3800) * np.hanning(int(0.1 * RATE)) ** 2
        _place(buf, s, k * 0.16)
    return _put(mix, buf, at, gain, pan, under)


def pant(mix, at, seconds=1.5, rate=3.2, gain=0.05, pan=0.0):
    """A tired dog panting: in and out, `rate` breaths a second, slowing a little."""
    m = _m("pant", at, seconds)
    buf = np.zeros(int(seconds * RATE))
    t, k = 0.0, 0
    while t < seconds - 0.16:
        d = 0.14
        hi = 2600 if k % 2 == 0 else 1700      # in is brighter than out
        s = _bp(m.noise(d), 600, hi) * np.hanning(int(d * RATE))
        _place(buf, _norm(s) * (0.7 if k % 2 == 0 else 1.0), t)
        t += 0.5 / (rate * (1 - 0.25 * t / seconds))
        k += 1
    return _put(mix, buf, at, gain, pan)


def sigh(mix, at, seconds=1.1, gain=0.08, pan=0.0):
    """A dog sighing: one long breath out through the nose, falling, with a
    trace of voice under it. `at` is where the breath starts."""
    m = _m("sigh", at, seconds)
    n = int(seconds * RATE)
    t = _t(seconds)
    air = m.noise(seconds)
    a = _bp(air, 500, 2200)
    b = _bp(air, 250, 900)
    x = a * np.linspace(1, 0, n) + b * np.linspace(0.2, 1, n)
    voice = np.sin(2 * np.pi * np.cumsum(np.linspace(230, 150, n)) / RATE) * 0.18
    env = np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.15) * 2.6)
    return _put(mix, _fade((_norm(x) + voice) * env, 0.01, 0.1), at, gain, pan)


def tail(mix, at, n=4, every=0.19, gain=0.07, pan=0.0):
    """A tail on the boards: soft double thumps (thump-thump, thump-thump)."""
    m = _m("tail", at, 0.2)
    end = at
    for k in range(n):
        t = _t(0.1)
        s = np.sin(2 * np.pi * 105 * t) * np.exp(-t * 45) + 0.4 * np.sin(2 * np.pi * 315 * t) * np.exp(-t * 70) + 0.3 * _norm(_bp(m.noise(0.1), 150, 900)) * np.exp(-t * 60)
        end = _put(mix, _fade(_grit(s, 0.5), 0.002, 0.01), at + (k // 2) * every * 2.3 + (k % 2) * every * 0.75, gain * (1.0 if k % 2 == 0 else 0.7), pan)
    return end


def howl(mix, at, seconds=2.2, gain=0.62, pan=P_WATER * 0.6, room=0.35, tail=0.7):
    """ONE howl: a voice that climbs from about 300 to 520 Hz and settles on 440,
    with the only long reverberation above the water. `at` is the first breath of
    it; the voice lasts `seconds`, the room rings `tail` seconds more and is then cut. The loudest thing so far."""
    m = _m("howl", at, seconds + 1.2)
    n = int(seconds * RATE)
    t = _t(seconds)
    u = t / seconds
    f = np.where(u < 0.38, 300 + 220 * (np.sin(np.pi * (u / 0.38 - 0.5)) * 0.5 + 0.5),
                 np.where(u < 0.62, 520.0, 520 - 80 * (np.sin(np.pi * ((u - 0.62) / 0.38 - 0.5)) * 0.5 + 0.5)))
    f = f * (1 + 0.014 * np.clip(u * 2 - 0.4, 0, 1) * np.sin(2 * np.pi * 5.4 * t))
    ph = 2 * np.pi * np.cumsum(f) / RATE
    x = sum(a * np.sin(k * ph) for k, a in zip(range(1, 8), (1.0, 0.62, 0.34, 0.2, 0.1, 0.05, 0.03)))
    x += 0.05 * _bp(m.noise(seconds), 900, 2600)
    env = np.minimum(1, t / 0.28) * np.minimum(1, (seconds - t) / 0.45) ** 1.3
    x = _norm(x[:n] * env)
    full = np.concatenate([x, np.zeros(int(tail * RATE))])
    wet = np.zeros_like(full)
    for d, g in ((0.113, 0.5), (0.171, 0.42), (0.233, 0.34), (0.307, 0.27)):
        k = int(d * RATE)
        y = full.copy()
        for _ in range(4):
            y = np.concatenate([np.zeros(k), y[:-k]]) * 0.5
            wet += y * g
    out = full + _lp(wet, 2400) * room
    k = int(min(tail, 0.6) * RATE)
    out[-k:] *= np.linspace(1, 0, k) ** 2
    return _put(mix, out, at, gain, pan)


def bark(mix, at, gain=0.45, pan=0.0):
    """One short bark (the stop). Not on the cue sheet; here because the
    dictionary has it."""
    m = _m("bark", at, 0.3)
    t = _t(0.16)
    ph = 2 * np.pi * np.cumsum(430 * np.exp(-t * 4.0) + 60) / RATE
    x = sum(np.sin(k * ph) / k for k in range(1, 9)) + 0.5 * _bp(m.noise(0.16), 700, 3000)
    return _put(mix, _fade(x * np.exp(-t * 16), 0.004, 0.02), at, gain, pan)


# ====================================================================== #
#  THE PERSON, THE STEP, THE RADIO                                       #
# ====================================================================== #

_VOWELS = {"i": (300, 2100, 2800), "u": (320, 900, 2300), "e": (500, 1750, 2500),
           "a": (700, 1150, 2500), "o": (480, 850, 2400), "uh": (560, 1200, 2450)}

# (onset s, length s, pitch at start, pitch at end (x base), vowel, loudness)
_LINES = {
    # "Will you fetch it?"  four syllables on the motif; the end lifts: a question.
    "call": dict(base=150, syl=[(MOTIF[0], 0.20, 1.00, 1.03, "i", 0.8), (MOTIF[1], 0.20, 1.02, 1.00, "u", 0.75),
                                (MOTIF[2], 0.42, 1.10, 1.02, "e", 1.0), (MOTIF[3], 0.26, 1.06, 1.26, "i", 0.8)]),
    # "It's too much for one dog."  six syllables, lower, slower, sinking.
    "quiet": dict(base=112, syl=[(0.00, 0.20, 1.04, 1.02, "i", 0.6), (0.24, 0.24, 1.06, 1.02, "u", 0.8),
                                 (0.52, 0.28, 1.04, 0.98, "uh", 0.9), (0.84, 0.18, 0.96, 0.95, "o", 0.55),
                                 (1.06, 0.24, 0.97, 0.93, "uh", 0.75), (1.34, 0.34, 0.93, 0.80, "o", 0.8)]),
    # "We don't want that."  four syllables, level, not hard; the last one drops.
    "no": dict(base=124, syl=[(0.00, 0.20, 1.00, 1.00, "i", 0.7), (0.26, 0.26, 1.02, 1.00, "o", 0.95),
                              (0.58, 0.26, 1.00, 0.99, "a", 0.9), (0.90, 0.30, 0.97, 0.80, "a", 0.8)]),
}


def voice(mix, at, kind="call", gain=0.14, pan=P_DOOR, pitch=1.0):
    """A low human voice with NO words: kind = 'call' | 'quiet' | 'no'.
    A buzz shaped by three vowel formants, one syllable at a time, low-passed
    as if from a doorway. It marks that the person spoke and how (asking, low,
    refusing) by rhythm and pitch contour only. It is not speech."""
    spec = _LINES[kind]
    total = max(s[0] + s[1] for s in spec["syl"]) + 0.08
    m = _m("voice" + kind, at, total)
    out = np.zeros(int(total * RATE))
    for on, dur, p0, p1, vow, amp in spec["syl"]:
        n = int(dur * RATE)
        t = np.arange(n) / RATE
        f0 = spec["base"] * pitch * np.linspace(p0, p1, n) * (1 + 0.008 * np.sin(2 * np.pi * 5 * t))
        ph = 2 * np.pi * np.cumsum(f0) / RATE
        buzz = sum(np.sin(k * ph) / k for k in range(1, int(3400 / (spec["base"] * pitch * 1.3))))
        y = sum(_bp(buzz, F * 0.82, F * 1.2) * g for F, g in zip(_VOWELS[vow], (1.0, 0.45, 0.16)))
        y = _norm(y) + 0.22 * _norm(_lp(buzz, 380)) + 0.02 * _bp(m.noise(dur), 1500, 3500)[:n]
        _place(out, _norm(y) * amp * np.hanning(n) ** 0.55, on)
    return _put(mix, _lp(out, 2600), at, gain, pan)


def voice_call(mix, at, **kw):
    """Line 1 (board: 6.2): four syllables on the motif, the end lifting."""
    return voice(mix, at, "call", **kw)


def voice_quiet(mix, at, **kw):
    """Line 2 (board: 81.2): six syllables, lower and slower, sinking."""
    kw.setdefault("gain", 0.10)
    return voice(mix, at, "quiet", **kw)


def voice_no(mix, at, **kw):
    """Line 3 (board: 148.2): four level syllables, the last one dropping."""
    kw.setdefault("gain", 0.12)
    return voice(mix, at, "no", **kw)


def _knock_sig(m, freq=210, bright=2200, decay=38, sec=0.09):
    t = _t(sec)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * decay) + 0.5 * _norm(_bp(m.noise(sec), 300, bright)) * np.exp(-t * 90)
    return _fade(x, 0.0008, 0.008)


def taps(mix, at, gain=0.13, pan=P_DOOR + 0.1):
    """Four taps on the rail in the motif rhythm (short short long short)."""
    m = _m("taps", at, 0.2)
    end = at
    for k, on in enumerate(MOTIF):
        end = _put(mix, _knock_sig(m, 230 + 12 * k), at + on, gain * (1.0, 0.85, 1.0, 0.8)[k], pan)
    return end


def pebble(mix, at, gain=0.09, pan=P_DOOR + 0.15):
    """One white pebble set on the rail: a small bright click, a short skitter."""
    m = _m("pebble", at, 0.2)
    buf = np.zeros(int(0.16 * RATE))
    for k, (d, a) in enumerate(((0.0, 1.0), (0.055, 0.4), (0.09, 0.2))):
        s = _ping(3300 + 250 * k, 0.04, 0.006) + 0.5 * _norm(_bp(m.noise(0.04), 2000, 8000)) * np.exp(-_t(0.04) * 300)
        _place(buf, _fade(s, 0.0003, 0.004) * a, d)
    return _put(mix, buf, at, gain, pan)


def creak(mix, at, seconds=0.45, gain=0.06, pan=P_STEP):
    """A board taking weight: a short low groan (the person sitting, a body down)."""
    m = _m("creak", at, seconds)
    n = int(seconds * RATE)
    f = np.linspace(170, 120, n) * (1 + 0.04 * np.sin(2 * np.pi * 23 * _t(seconds)))
    x = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / RATE)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 31 * _t(seconds))))
    x = _bp(x + 0.2 * m.noise(seconds)[:n], 120, 1400) * np.hanning(n)
    return _put(mix, x, at, gain, pan)


def radio_down(mix, at, gain=0.12, pan=P_STEP):
    """The radio set on the step: a small hollow plastic-and-wood knock."""
    m = _m("radio_down", at, 0.2)
    x = _knock_sig(m, 330, 3200, 55, 0.08) + 0.5 * _ping(740, 0.08, 0.012)
    return _put(mix, x, at, gain, pan)


def radio_dial(mix, at, seconds=0.55, gain=0.025, pan=P_STEP):
    """The dial turned: a thin whistle sweeping up through static."""
    m = _m("radio_dial", at, seconds)
    n = int(seconds * RATE)
    x = _sweep(700, 2600, seconds, 1.6)[:n] * 0.6 + _norm(_bp(m.noise(seconds), 1500, 5000))[:n] * np.linspace(1, 0.3, n)
    return _put(mix, _fade(x, 0.02, 0.08), at, gain, pan)


def radio_hiss(mix, at, seconds, gain=0.006, pan=P_STEP, fade_in=0.2, fade_out=0.2):
    """The radio's quiet hiss on the step: thin static with a little flutter.
    It is the radio being ON; lay it under every stretch where the tune plays
    and also across the gaps between phrases."""
    m = _m("radio_hiss", at, seconds)
    n = int(seconds * RATE)
    x = _norm(_bp(m.noise(seconds), 1800, 5200))[:n]
    x = x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.7 * _t(seconds)[:n])) + 0.12 * np.sin(2 * np.pi * 100 * _t(seconds)[:n])
    a, b = min(n, int(fade_in * RATE)), min(n, int(fade_out * RATE))
    x[:a] *= np.linspace(0, 1, a)
    x[-b:] *= np.linspace(1, 0, b)
    return _put(mix, x, at, gain, pan)


@lru_cache(maxsize=None)
def _pluck(freq, seconds):
    s = Mix(seconds + 0.05, seed=int(freq * 7) % 9973)
    s.pluck(0.0, freq, seconds, 1.0, 0.0)
    return _norm(s.L[: int(seconds * RATE)].copy())


_A4 = 440.0
_SCALE = {"A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.0, "A4": 440.0,
          "C5": 523.25, "D5": 587.33, "E5": 659.26, "G5": 783.99, "A5": 880.0}
# The tune's phrases: always the motif's rhythm; only the notes change a little.
_PHRASES = [("A4", "A4", "C5", "G4"), ("A4", "A4", "D5", "C5"), ("G4", "A4", "C5", "A4"),
            ("A4", "C5", "E5", "D5"), ("E4", "G4", "A4", "E4")]


def radio_phrase(mix, at, variant=0, slow=1.0, gain=0.018, pan=P_STEP, ring=1.0, under=False):
    """Four plucked notes in the motif rhythm, thin, from one place: the radio.
    variant picks the notes (0..4); slow stretches the rhythm (1.4 for the end);
    ring is each note's length in seconds (3.5 leaves the last note ringing)."""
    notes = _PHRASES[variant % len(_PHRASES)]
    end = at
    for k, (on, name) in enumerate(zip(MOTIF, notes)):
        sec = ring if k == 3 else min(ring, 0.9)
        x = _bp(_pluck(_SCALE[name], sec), 450, 3400)
        x = np.tanh(1.6 * _norm(x))            # a small speaker
        end = max(end, _put(mix, _fade(x, 0.001, 0.05), at + on * slow, gain * (1.0, 0.85, 1.0, 0.8)[k], pan, under))
    return end


# ====================================================================== #
#  THE WATER: IN, THROUGH, UNDER, OUT                                    #
# ====================================================================== #

def _drops(m, buf, a, b, n, lo=700, hi=2200, amp=1.0):
    for _ in range(n):
        f = m.rs.uniform(lo, hi)
        tt = _t(0.035)
        s = np.sin(2 * np.pi * (f + 5000 * tt) * tt) * np.exp(-tt * 110)
        _place(buf, s * amp * m.rs.uniform(0.3, 1.0), m.rs.uniform(a, b))


def wade(mix, at, seconds=1.0, strides=3, gain=0.12, pan=P_WATER * 0.5):
    """Wading in: water pushed round the legs, one slosh a stride, with drops."""
    m = _m("wade", at, seconds)
    n = int(seconds * RATE)
    buf = np.zeros(n)
    for k in range(strides):
        d = min(0.34, seconds / strides)
        s = _bp(m.noise(d), 250, 1900) * np.hanning(int(d * RATE)) ** 1.5
        _place(buf, _norm(s), k * seconds / strides)
    _drops(m, buf, 0.05, seconds - 0.05, int(seconds * 14), amp=0.5)
    return _put(mix, buf, at, gain, pan)


def _plunge_sig(m, size=1.0, sec=1.3):
    t = _t(sec)
    body = np.sin(2 * np.pi * np.cumsum(95 / size * (0.45 + 0.55 * np.exp(-t * 9))) / RATE) * np.exp(-t * 7)
    burst = _norm(_bp(m.noise(sec), 180, 6500)) * np.exp(-t * (6.5 / size))
    x = body * 0.9 + burst
    x[: int(0.004 * RATE)] *= np.linspace(0, 1, int(0.004 * RATE))
    _drops(m, x, 0.12, sec - 0.1, int(16 * size), 500, 1500, 0.22)
    return _fade(x, 0, 0.1)


def plunge(mix, at, size=1.0, gain=0.42, pan=P_WATER * 0.6, under=False):
    """THE PLUNGE: a body through the surface. A low thump, a burst of white
    water, a fizz of bubbles after. size 1 = a dog, 0.6 = a small one, 1.6 = a cow's leg."""
    m = _m("plunge", at, 1.4)
    return _put(mix, _plunge_sig(m, size), at, gain, pan, under)


def pack_plunge(mix, at, n=10, spread=0.2, gain=0.17, pan=P_WATER * 0.5, width=0.5, under=False):
    """Many dogs entering the water: n plunges of different sizes inside
    `spread` seconds, fanned across the pan. The pack goes in the same four frames."""
    m = _m("pack_plunge", at, 0.2)
    end = at
    for k in range(n):
        d = 0.0 if k == 0 else m.rs.uniform(0, spread)
        p = pan + width * (k / max(1, n - 1) * 2 - 1)
        end = max(end, plunge(mix, at + d, m.rs.uniform(0.6, 1.15), gain * m.rs.uniform(0.6, 1.0), p, under))
    return end


def splash(mix, at, gain=0.2, pan=P_WATER * 0.5, under=False):
    """One small splash (a hoof slipping in, a retriever going back down)."""
    m = _m("splash", at, 0.8)
    return _put(mix, _plunge_sig(m, 0.55, 0.7), at, gain, pan, under)


def bubbles(mix, at, n=5, seconds=1.0, low=False, gain=0.08, pan=0.0, under=True):
    """Bubbles: n short rising blips spread over `seconds`. low=True makes them
    fat (a cow's muzzle, a dog letting its breath go)."""
    m = _m("bubbles", at, seconds + 0.3)
    buf = np.zeros(int((seconds + 0.25) * RATE))
    for k in range(n):
        f = m.rs.uniform(140, 260) if low else m.rs.uniform(380, 900)
        d = 0.14 if low else 0.06
        s = _sweep(f, f * 1.9, d) * np.hanning(int(d * RATE))
        _place(buf, s * m.rs.uniform(0.5, 1.0), 0.0 if k == 0 else m.rs.uniform(0, seconds))
    return _put(mix, buf, at, gain, pan, 1800 if under is True else under)


def bubble_picture(mix, at, seconds=2.2, gain=0.06, pan=0.0):
    """A fish child's picture rising in a bubble: one slow round tone climbing a fifth."""
    n = int(seconds * RATE)
    x = _sweep(220, 330, seconds, 0.7)[:n] + 0.3 * _sweep(440, 660, seconds, 0.7)[:n]
    env = np.minimum(1, _t(seconds)[:n] / 0.5) * np.minimum(1, (seconds - _t(seconds)[:n]) / 0.6)
    return _put(mix, x * env, at, gain, pan)


def breach(mix, at, size=1.0, gain=0.36, pan=P_WATER * 0.4):
    """SURFACING: a rising rush that starts 0.25 s BEFORE `at`, the break through
    the surface exactly on `at`, then water falling back in drops for 0.9 s."""
    m = _m("breach", at, 1.6)
    lead, sec = 0.25, 1.15
    nl = int(lead * RATE)
    up = _norm(_bp(m.noise(lead), 300, 2400))[:nl] * np.linspace(0, 1, nl) ** 2 * 0.45
    t = _t(sec)
    burst = _norm(_bp(m.noise(sec), 400, 8000)) * np.exp(-t * 6 / size)
    burst[: int(0.003 * RATE)] *= np.linspace(0, 1, int(0.003 * RATE))
    _drops(m, burst, 0.1, sec - 0.05, int(26 * size), 900, 2600, 0.3)
    return _put(mix, np.concatenate([up, _fade(burst, 0, 0.1)]), at - lead, gain, pan)


def shake(mix, at, seconds=0.9, gain=0.2, pan=P_SILL, tag=True):
    """THE SHAKE: a flutter of wet bursts, fast then slowing, spray ticking on
    the boards, the collar tag rattling in it."""
    m = _m("shake", at, seconds)
    n = int(seconds * RATE)
    buf = np.zeros(n)
    t, k = 0.0, 0
    while t < seconds - 0.07:
        d = 0.055
        s = _norm(_bp(m.noise(d), 500, 5200)) * np.hanning(int(d * RATE))
        _place(buf, s * (1 - 0.5 * t / seconds) * (1.0 if k % 2 == 0 else 0.7), t)
        t += 1 / (15 - 7 * t / seconds)
        k += 1
    for _ in range(int(seconds * 34)):          # spray on wood
        c = _norm(_bp(m.noise(0.012), 1800, 7000)) * np.exp(-_t(0.012) * 350)
        _place(buf, c * m.rs.uniform(0.15, 0.5), m.rs.uniform(0.05, seconds - 0.02))
    end = _put(mix, buf, at, gain, pan)
    if tag:
        collar(mix, at + 0.06, n=5, gain=gain * 0.3, pan=pan)
    return end


def drip(mix, at, n=1, every=0.5, gain=0.045, pan=P_SILL, on="wood"):
    """Drips: on 'wood' a dull tick, on 'water' a small plip."""
    m = _m("drip", at, 0.2)
    end = at
    for k in range(n):
        if on == "water":
            s = _sweep(700, 1500, 0.05) * np.exp(-_t(0.05) * 70)
        else:
            s = _knock_sig(m, m.rs.uniform(380, 520), 3000, 120, 0.04)
        end = _put(mix, s, at + k * every + (m.rs.uniform(-0.06, 0.06) if k else 0), gain * m.rs.uniform(0.6, 1.0), pan)
    return end


def breath_out(mix, at, seconds=1.2, gain=0.12, pan=0.0, under=True):
    """Breath running out, heard under water: fat bubbles let go, slowly at
    first and then all at once, climbing. Follow it with gasp() above."""
    m = _m("breath_out", at, seconds)
    buf = np.zeros(int((seconds + 0.2) * RATE))
    k = 0
    while True:
        u = 1 - 0.5 ** (k / 3.0)               # onsets crowd toward the end
        if u > 0.97 or k > 40:
            break
        f = 150 + 160 * u + m.rs.uniform(-15, 15)
        s = _sweep(f, f * 1.9, 0.13) * np.hanning(int(0.13 * RATE))
        _place(buf, s * (0.5 + 0.5 * u), u * seconds)
        k += 1
    return _put(mix, buf, at, gain, pan, 1500 if under is True else under)


def gasp(mix, at, gain=0.09, pan=P_WATER * 0.3):
    """A dog breaking the surface out of breath: one sharp breath IN, a shorter one out."""
    m = _m("gasp", at, 0.8)
    n1 = int(0.32 * RATE)
    a = _norm(_bp(m.noise(0.32), 900, 3600))[:n1] * np.linspace(0.1, 1, n1) ** 1.5
    a[-int(0.03 * RATE):] *= np.linspace(1, 0, int(0.03 * RATE))
    n2 = int(0.24 * RATE)
    b = _norm(_bp(m.noise(0.24), 500, 1900))[:n2] * np.hanning(n2) * 0.6
    return _put(mix, np.concatenate([a, np.zeros(int(0.07 * RATE)), b]), at, gain, pan)


def shiver(mix, at, seconds=2.0, gain=0.03, pan=0.0):
    """Wet dogs shivering: a fast faint flutter that dies away."""
    m = _m("shiver", at, seconds)
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    x = _norm(_bp(m.noise(seconds), 300, 1600))[:n] * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 13 * t)))
    return _put(mix, _lp(x, 2500) * np.minimum(1, t / 0.2) * np.linspace(1, 0, n) ** 0.7, at, gain, pan)


# ====================================================================== #
#  TROUTTOWN                                                             #
# ====================================================================== #

def land(mix, at, gain=0.14, pan=0.0):
    """The dog landing on the creek bed: a soft thud and a hiss of gravel."""
    m = _m("land", at, 0.5)
    t = _t(0.4)
    x = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 14) + 0.3 * np.sin(2 * np.pi * 210 * t) * np.exp(-t * 25) + 0.5 * _norm(_bp(m.noise(0.4), 400, 2400)) * np.exp(-t * 9)
    return _put(mix, _fade(_grit(x, 0.5), 0.004, 0.05), at, gain, pan, 1400)


def dig(mix, at, seconds=1.2, rate=8.0, find=None, gain=0.14, pan=0.0, under=1500):
    """DIGGING in gravel: `rate` scrabbles a second for `seconds`, each a crunch
    of stones over a low push. find=None ends in nothing; 'thud' ends on a dull
    knock (the boot); 'ring' ends on a small bright ring (the spool, a part)."""
    m = _m("dig", at, seconds)
    buf = np.zeros(int((seconds + 0.5) * RATE))
    k, t = 0, 0.0
    while t < seconds - 0.06:
        d = 0.075
        tt = _t(d)
        s = _norm(_bp(m.noise(d), 500, 3600)) * np.exp(-tt * 30) + 0.5 * np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 40)
        for _ in range(3):                      # single stones
            _place(s, _ping(m.rs.uniform(900, 2400), 0.02, 0.004) * 0.5, m.rs.uniform(0, d - 0.02))
        _place(buf, _fade(s, 0.002, 0.01) * (0.8 if k % 2 else 1.0), t + m.rs.uniform(-0.01, 0.01) if k else t)
        t += 1 / rate
        k += 1
    end = _put(mix, buf, at, gain, pan, under)
    if find == "thud":
        tt = _t(0.2)
        end = _put(mix, np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 22), at + seconds, gain * 0.9, pan)
    elif find == "ring":
        end = _put(mix, _ping(1250, 0.5, 0.11) + 0.5 * _ping(1870, 0.5, 0.08), at + seconds, gain * 0.55, pan)
    return end


def set_down(mix, at, gain=0.08, pan=0.0, under=1500):
    """A thing set down on the creek bed (the spool, a lid): one small click."""
    m = _m("set_down", at, 0.1)
    return _put(mix, _knock_sig(m, 420, 2600, 90, 0.05), at, gain, pan, under)


def paw_press(mix, at, gain=0.09, pan=0.0, under=False):
    """A paw pressed on a thing (it has been written): one soft low push."""
    t = _t(0.16)
    x = (np.sin(2 * np.pi * 85 * t) * np.exp(-t * 26) + 0.4 * np.sin(2 * np.pi * 255 * t) * np.exp(-t * 45)) * np.minimum(1, t / 0.008)
    return _put(mix, _fade(_grit(x, 0.5), 0.004, 0.02), at, gain, pan, under)


def page_taken(mix, at, gain=0.08, pan=0.0, under=1600):
    """A PAGE TAKEN from the notice board: the pin's tiny ring on `at`, the soft
    swish of paper through water 0.15 s later, the pin landing (tinier) at +0.9."""
    m = _m("page_taken", at, 1.2)
    _put(mix, _ping(2400, 0.25, 0.05) + 0.4 * _ping(3650, 0.25, 0.03), at, gain * 0.6, pan)
    n = int(0.45 * RATE)
    sw = _norm(_bp(m.noise(0.45), 350, 2600))[:n] * np.hanning(n) ** 1.3
    _put(mix, sw, at + 0.15, gain, pan, under)
    return _put(mix, _ping(2700, 0.12, 0.02), at + 0.9, gain * 0.25, pan)


def lamp_chime(mix, at, step=0, gain=0.035, pan=0.0, seconds=2.5):
    """A Trouttown street lamp coming on: a soft far bell, the town's own (high
    and clear, nothing like the cow's). step 0..6 climbs the scale left to right."""
    f = (523.25, 587.33, 659.26, 783.99, 880.0, 1046.5, 1174.7)[step % 7]
    s = Mix(2.6)
    s.bell(0.0, f, 2.4, 1.0, 0.0)
    x = _lp(_norm(s.L[: int(2.5 * RATE)].copy()), 2200)[: int(min(2.5, seconds) * RATE)]
    return _put(mix, _fade(x, 0.001, 0.25), at, gain, pan)


def school_bell(mix, at, gain=0.09, pan=-0.2):
    """The Trouttown school bell: one stroke at 660 Hz heard through the water."""
    s = Mix(3.2)
    s.bell(0.0, 660, 3.0, 1.0, 0.0)
    return _put(mix, s.L[: int(3.1 * RATE)], at, gain, pan, 1500)


def fish_murmur(mix, at, seconds=2.0, gain=0.03, pan=0.0, pitch=310):
    """The peoplefish class: a small high burble of voices, no words (bubbles
    with pictures are how they talk; this is only that they are there)."""
    s = Mix(seconds + 0.1, seed=(int(at * 1000) + 17) % (2 ** 31 - 1))
    s.murmur(0.0, seconds, 1.0, pitch, 0.0, seed=int(at * 10) + 3)
    s.murmur(0.07, max(0.2, seconds - 0.1), 0.7, pitch * 1.26, 0.0, seed=int(at * 10) + 4)
    return _put(mix, s.L[: int(seconds * RATE)], at, gain, pan, 1700)


# ====================================================================== #
#  REELS, THE SILL, THE OLD DOG                                          #
# ====================================================================== #

def reel_down(mix, at, gain=0.2, pan=P_SILL, wet=True):
    """A REEL SET ON WOOD: the knock of the sill, the tin's small ring, a drop."""
    m = _m("reel_down", at, 0.8)
    t = _t(0.7)
    x = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 30) + 0.45 * _norm(_bp(m.noise(0.7), 250, 1800)) * np.exp(-t * 70)
    x += 0.32 * (np.sin(2 * np.pi * 1880 * t) * np.exp(-t * 9) + 0.6 * np.sin(2 * np.pi * 2930 * t) * np.exp(-t * 13))
    x[: int(0.001 * RATE)] *= np.linspace(0, 1, int(0.001 * RATE))
    end = _put(mix, _fade(x, 0, 0.05), at, gain, pan)
    if wet:
        drip(mix, at + 0.32, 1, gain=gain * 0.2, pan=pan)
    return end


def page_slap(mix, at, gain=0.1, pan=P_SILL):
    """A wet page laid across the sill: a small flat slap."""
    m = _m("page_slap", at, 0.2)
    n = int(0.12 * RATE)
    x = _norm(_bp(m.noise(0.12), 300, 2800))[:n] * np.exp(-_t(0.12)[:n] * 38)
    return _put(mix, _fade(x, 0.001, 0.02), at, gain, pan)


def ratchet(mix, at, seconds=0.8, rate=14, gain=0.06, pan=0.0, under=False):
    """Film wound on or pulled off a reel: an even run of small clicks."""
    m = _m("ratchet", at, seconds)
    buf = np.zeros(int((seconds + 0.05) * RATE))
    for k in range(int(seconds * rate)):
        _place(buf, _knock_sig(m, 900, 5000, 220, 0.02) * (0.8 + 0.2 * (k % 2)), k / rate)
    return _put(mix, buf, at, gain, pan, under)


def old_dog_down(mix, at, steps=4, gain=0.12, pan=P_SILL):
    """The old dog walking and lying down: slow heavy steps (0.5 s apart), the
    body going down on the boards, one long breath out. Returns the end."""
    m = _m("old_dog_down", at, 0.2)
    for k in range(steps):
        _put(mix, _paw_sig(m, False, k % 2 == 0), at + k * 0.5, gain * 0.9, pan)
    td = at + steps * 0.5 + 0.15
    t = _t(0.3)
    _put(mix, np.sin(2 * np.pi * 75 * t) * np.exp(-t * 16) + 0.3 * _lp(m.noise(0.3), 600) * np.exp(-t * 20), td, gain, pan)
    return sigh(mix, td + 0.35, 1.3, gain * 0.5, pan)


def card_drag(mix, at, seconds=0.9, gain=0.05, pan=P_SILL):
    """Card dragged on wood (the old dog shifting over, a tail pulled aside)."""
    m = _m("card_drag", at, seconds)
    n = int(seconds * RATE)
    x = _norm(_bp(m.noise(seconds), 200, 1500))[:n] * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * _t(seconds)[:n])) * np.hanning(n) ** 0.6
    return _put(mix, x, at, gain, pan)


def long_look(mix, at, seconds=1.5, gain=0.022, pan=P_SILL, freq=196.0):
    """THE OLD DOG'S LONG LOOK as a held tone: one low note and its fifth, with a
    slow beat between two strings a hair apart, no vibrato, no attack, no tune.
    It comes in under 0.4 s, holds, and stops when the dog moves. It is not
    music: it is what the room sounds like while somebody who built nothing looks."""
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    x = np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * (freq + 0.7) * t) + 0.5 * np.sin(2 * np.pi * freq * 1.5 * t) + 0.12 * np.sin(2 * np.pi * freq * 3 * t)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (seconds - t) / 0.12)
    return _put(mix, x * env, at, gain, pan)


# ====================================================================== #
#  THE PACK (each dog its own material)                                  #
# ====================================================================== #

def wheels(mix, at, seconds=1.0, pitch=1.0, gain=0.07, pan=0.0, pan_to=None, under=False):
    """A wooden retriever's wheels on boards: a fast rattle of small knocks."""
    m = _m("wheels", at, seconds)
    buf = np.zeros(int((seconds + 0.06) * RATE))
    t = 0.0
    while t < seconds:
        _place(buf, _knock_sig(m, 520 * pitch, 2800, 120, 0.035) * m.rs.uniform(0.6, 1.0), t)
        t += m.rs.uniform(0.04, 0.065) / pitch ** 0.5
    return _put(mix, buf, at, gain, pan if pan_to is None else (pan + pan_to) / 2, under)


def peg_tick(mix, at, n=1, every=0.25, gain=0.05, pan=P_SILL):
    """The wooden retriever's peg tail: even ticks (it wags like a clock)."""
    m = _m("peg_tick", at, 0.1)
    end = at
    for k in range(n):
        end = _put(mix, _knock_sig(m, 760, 3200, 160, 0.03), at + k * every, gain, pan)
    return end


def wire_twang(mix, at, gain=0.07, pan=0.0, under=False):
    """The wire dog: one high springy twang."""
    x = _pluck(987.77, 0.6) * (1 + 0.3 * np.sin(2 * np.pi * 11 * _t(0.6)))
    return _put(mix, x, at, gain, pan, under)


def paper_slide(mix, at, seconds=0.45, gain=0.06, pan=0.0, under=False):
    """The black cut-out herding dog: paper sliding on boards."""
    m = _m("paper_slide", at, seconds)
    n = int(seconds * RATE)
    x = _norm(_bp(m.noise(seconds), 1200, 6000))[:n] * np.hanning(n) ** 2
    return _put(mix, x, at, gain, pan, under)


def flutter(mix, at, seconds=0.6, gain=0.05, pan=0.0, under=False):
    """The crepe-paper sheepdog: a soft fast flutter."""
    m = _m("flutter", at, seconds)
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    x = _norm(_bp(m.noise(seconds), 600, 3500))[:n] * (0.5 + 0.5 * np.sin(2 * np.pi * 19 * t)) * np.hanning(n)
    return _put(mix, x, at, gain, pan, under)


def page_peel(mix, at, gain=0.06, pan=0.0):
    """The printed bloodhound: a page peeled off a page (a soft rip)."""
    m = _m("page_peel", at, 0.4)
    n = int(0.35 * RATE)
    x = _norm(_bp(m.noise(0.35), 1500, 7000))[:n] * np.linspace(0.2, 1, n) ** 2
    x *= 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 60 * _t(0.35)[:n]))
    return _put(mix, _fade(x, 0.01, 0.01), at, gain, pan)


def pop(mix, at, gain=0.08, pan=0.0):
    """The terrier arriving: one pop."""
    x = _sweep(900, 250, 0.05) * np.exp(-_t(0.05) * 60)
    return _put(mix, x, at, gain, pan)


def patter(mix, at, seconds=1.5, rate=11, gain=0.08, pan=0.4, pan_to=-0.4):
    """The herding dog running wide: the fastest soft paws above the water,
    travelling across the pan."""
    m = _m("patter", at, seconds)
    k, t, end = 0, 0.0, at
    while t < seconds:
        p = pan + (pan_to - pan) * t / seconds
        end = _put(mix, _lp(_paw_sig(m, False, False), 900), at + t, gain * (0.8 if k % 2 else 1.0), p)
        t += 1 / rate
        k += 1
    return end


def work(mix, at, seconds, gain=0.05, level=1.0, top=UNDER, voices=7, seed=5):
    """The pack working, heard under water: every dog's material at once, none
    in front (wheels at three pitches, wire, paper, scrabble, the felt dog's even
    shell clicks, the fish class). The pattern depends only on `seed` and the
    clock since the start of the film, so two stretches of it are the same work
    going on: it comes back after the ice exactly as it was. `voices` thins it
    (7 = everyone, 1 = one dog); `top` lowers the low-pass (the cold)."""
    rs = np.random.RandomState(seed)
    n = int(seconds * RATE)
    buf = np.zeros(n + RATE)
    period = 6.0
    lib = []
    m = Mix(1.0, seed=seed)
    for v in range(7):
        ev = []
        if v < 3:                                  # three retrievers
            for _ in range(5):
                ev.append((rs.uniform(0, period), _norm(_knock_runs(m, 430 * (1, 1.26, 1.5)[v], rs.uniform(0.3, 0.7)))))
        elif v == 3:                               # digger
            for _ in range(4):
                ev.append((rs.uniform(0, period), _norm(_scrabble(m, rs.uniform(0.4, 0.8)))))
        elif v == 4:                               # herder / sheepdog: paper
            for _ in range(4):
                d = rs.uniform(0.3, 0.6)
                ev.append((rs.uniform(0, period), _norm(_bp(m.noise(d), 400, 2000)[: int(d * RATE)] * np.hanning(int(d * RATE)))))
        elif v == 5:                               # felt dog: the only even pulse
            for k in range(12):
                ev.append((k * 0.5, _knock_sig(m, 640, 2400, 150, 0.03) * 0.7))
        else:                                      # wire, and a low sniffing push
            for _ in range(3):
                ev.append((rs.uniform(0, period), _pluck(493.88, 0.5) * 0.8))
        lib.append(ev)
    t0 = at - math.floor(at / period) * period     # phase in the 6 s pattern
    for v in range(min(voices, 7)):
        for on, s in lib[v]:
            k = -1
            while True:
                tt = on - t0 + k * period
                k += 1
                if tt > seconds:
                    break
                if tt >= 0:
                    _place(buf, s, tt)
    x = _lp(buf[:n], top)
    a = min(n, int(0.25 * RATE))
    x[:a] *= np.linspace(0, 1, a)
    x[-a:] *= np.linspace(1, 0, a)
    return _put(mix, x, at, gain * level, 0.0, norm=False)


def _knock_runs(m, f, sec):
    buf = np.zeros(int((sec + 0.05) * RATE))
    t = 0.0
    while t < sec:
        _place(buf, _knock_sig(m, f, 2400, 110, 0.035), t)
        t += m.rs.uniform(0.045, 0.07)
    return buf


def _scrabble(m, sec):
    buf = np.zeros(int((sec + 0.1) * RATE))
    t = 0.0
    while t < sec:
        d = 0.075
        _place(buf, _norm(_bp(m.noise(d), 400, 2500)) * np.exp(-_t(d) * 30), t)
        t += 0.125
    return buf


# ====================================================================== #
#  THE COWS (always slow, always low; the tempo never changes)           #
# ====================================================================== #

def _hoof_sig(m, surface="earth"):
    sec = 0.2
    t = _t(sec)
    f, bright, dk = {"earth": (62, 900, 20), "grass": (55, 480, 24), "wood": (88, 1500, 26),
                     "ice": (120, 4500, 40)}[surface]
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.8 * np.exp(-t * 40))) / RATE) * np.exp(-t * dk)
    x += 0.3 * np.sin(2 * np.pi * 3.1 * f * t) * np.exp(-t * dk * 2)        # the part a small speaker keeps
    x += 0.6 * _norm(_bp(m.noise(sec), 120, bright)) * np.exp(-t * 45)
    if surface == "ice":
        x += 0.7 * _ping(2900, sec, 0.006)
    else:
        x = _grit(x, 0.7, 190, max(600, bright))
    return _fade(x, 0.002, 0.03)


def hooves(mix, at, n=4, every=0.55, surface="earth", gain=0.12, pan=0.2, pan_to=None, gain_to=None, under=False):
    """Cow hooves at walking pace: n heavy soft knocks, `every` seconds apart
    (four to a stride, lightly paired). surface: 'earth' the worn path, 'grass'
    duller, 'wood' the board at the water, 'ice' hard and short.
    pan_to / gain_to let a cow come nearer. The tempo is the cows': leave `every` alone."""
    m = _m("hooves" + surface, at, 0.3)
    end = at
    for k in range(n):
        u = k / max(1, n - 1)
        p = pan if pan_to is None else pan + (pan_to - pan) * u
        g = gain if gain_to is None else gain + (gain_to - gain) * u
        tt = at + k * every + (0.06 if k % 2 else 0.0) + (m.rs.uniform(-0.02, 0.02) if k else 0.0)
        end = _put(mix, _hoof_sig(m, surface), tt, g * (0.85 if k % 2 else 1.0), p, under)
    return end


def calf(mix, at, n=6, every=0.14, surface="wood", gain=0.07, pan=0.2, pan_to=None):
    """The calf: small quick hooves (a third of the weight, four times the pace)."""
    m = _m("calf", at, 0.2)
    end = at
    for k in range(n):
        p = pan if pan_to is None else pan + (pan_to - pan) * k / max(1, n - 1)
        s = _hoof_sig(m, surface)[: int(0.09 * RATE)]
        end = _put(mix, _fade(_bp(s, 150, 4000), 0.001, 0.02), at + k * every + (m.rs.uniform(-0.012, 0.012) if k else 0.0), gain * (0.8 if k % 2 else 1.0), p)
    return end


def cowbell(mix, at, n=1, every=0.55, gain=0.09, pan=0.2, hard=False, under=False):
    """The lead cow's bell: a KNOCK, never a chime. A dull inharmonic clank near
    330 Hz that dies in half a second. hard=True is the bell jumping (gate post,
    a stamp); under=True is how the dog hears it from below."""
    m = _m("cowbell", at, 0.6)
    end = at
    for k in range(n):
        t = _t(0.5)
        x = sum(a * np.sin(2 * np.pi * 330 * r * t + ph) * np.exp(-t / d)
                for r, a, d, ph in ((1.0, 1.0, 0.085, 0), (1.48, 0.8, 0.06, 1), (2.07, 0.55, 0.04, 2),
                                    (2.83, 0.4 if hard else 0.2, 0.028, 3), (3.9, 0.3 if hard else 0.08, 0.018, 4)))
        x += 0.3 * _norm(_bp(m.noise(0.5), 400, 2500)) * np.exp(-t * 120)
        x[: int(0.001 * RATE)] *= np.linspace(0, 1, int(0.001 * RATE))
        late = 0.09 if n > 1 else 0.0              # the bell swings late, after the foot
        end = _put(mix, _fade(x, 0, 0.03), at + k * every + late, gain * (1.0 if k % 2 == 0 else 0.7) * (1.5 if hard else 1.0), pan, under)
    return end


def cow_breath(mix, at, seconds=1.6, gain=0.07, pan=0.2):
    """One long warm breath out of a cow: a low slow puff, four times a dog's."""
    m = _m("cow_breath", at, seconds)
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    x = _norm(_bp(m.noise(seconds), 120, 750))[:n]
    env = np.minimum(1, t / 0.3) * np.exp(-np.maximum(0, t - 0.35) * 2.0)
    return _put(mix, _fade(x * env, 0.01, 0.15), at, gain, pan)


def drinking(mix, at, seconds=1.5, gain=0.06, pan=P_WATER * 0.4):
    """A cow drinking: slow soft gulps, three every 1.5 s, for `seconds`.
    The same tempo every time it is used, on purpose."""
    m = _m("drinking", at, seconds)
    buf = np.zeros(int((seconds + 0.3) * RATE))
    t = 0.0
    k = 0
    while t < seconds - 0.2:
        g = _sweep(190, 120, 0.13) * np.hanning(int(0.13 * RATE))
        lap = _norm(_bp(m.noise(0.2), 300, 1500)) * np.hanning(int(0.2 * RATE)) * 1.1
        g = g + 0.5 * _sweep(380, 240, 0.13) * np.hanning(int(0.13 * RATE))
        _place(buf, lap, t)
        _place(buf, g, t + 0.08)
        t += 0.42 if k % 3 != 2 else 0.66
        k += 1
    return _put(mix, buf, at, gain, pan)


def moo(mix, at, seconds=0.7, gain=0.16, pan=0.3, under=True):
    """The lead cow's ONE call (she cannot follow): low and short, sagging from
    about 150 to 120 Hz. By default as the dog hears it from under the water."""
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    f = np.linspace(150, 120, n) * (1 + 0.012 * np.sin(2 * np.pi * 4.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / RATE
    buzz = sum(np.sin(k * ph) / k for k in range(1, 20))
    x = _norm(_bp(buzz, 380, 620)) + 0.5 * _norm(_bp(buzz, 900, 1250)) + 0.5 * _norm(_lp(buzz, 300))
    env = np.minimum(1, t / 0.12) * np.minimum(1, (seconds - t) / 0.25)
    return _put(mix, x * env, at, gain, pan, under)


def stamp(mix, at, gain=0.72, pan=0.15, bell=True):
    """THE STAMP: the lead cow's hoof on the ice at full weight. A deep thud, a
    hard crack on top of it, her bell jumping. With the howl, the loudest sound."""
    m = _m("stamp", at, 0.8)
    t = _t(0.7)
    x = np.sin(2 * np.pi * np.cumsum(48 * (1 + 2.2 * np.exp(-t * 28))) / RATE) * np.exp(-t * 7.5)
    x += 0.55 * _norm(_bp(m.noise(0.7), 900, 7000)) * np.exp(-t * 60)
    x += 0.3 * _ping(2500, 0.7, 0.012)
    x = _grit(x, 1.4, 190, 1500)
    x[: int(0.0015 * RATE)] *= np.linspace(0, 1, int(0.0015 * RATE))
    end = _put(mix, _fade(x, 0, 0.08), at, gain, pan)
    if bell:
        cowbell(mix, at + 0.05, gain=0.11, pan=pan, hard=True)
        cowbell(mix, at + 0.27, gain=0.05, pan=pan)
    return end


def cow_down(mix, at, gain=0.14, pan=0.0, bell=True):
    """A cow folding down: front knees on earth (two thuds, 0.35 s apart), the
    wait, the hind end (at +1.1), a very long breath (from +1.3), and the bell
    settling against the ground with one last knock at +2.0."""
    m = _m("cow_down", at, 0.3)
    _put(mix, _hoof_sig(m, "earth"), at, gain, pan)
    _put(mix, _hoof_sig(m, "earth"), at + 0.35, gain * 0.85, pan)
    t = _t(0.4)
    _put(mix, np.sin(2 * np.pi * 50 * t) * np.exp(-t * 11) + 0.3 * _lp(m.noise(0.4), 400) * np.exp(-t * 14), at + 1.1, gain * 1.2, pan)
    end = cow_breath(mix, at + 1.3, 2.4, gain * 0.45, pan)
    if bell:
        cowbell(mix, at + 2.0, gain=0.05, pan=pan)
    return end


def cow_up(mix, at, gain=0.12, pan=0.0):
    """A cow getting up, hind end first: two heaves and a breath."""
    m = _m("cow_up", at, 0.3)
    t = _t(0.35)
    for k in range(2):
        _put(mix, np.sin(2 * np.pi * 55 * t) * np.exp(-t * 12) + 0.3 * _lp(m.noise(0.35), 500) * np.exp(-t * 16), at + k * 0.6, gain, pan)
    return cow_breath(mix, at + 1.0, 1.2, gain * 0.5, pan)


def chew(mix, at, n=2, every=0.7, gain=0.035, pan=0.0):
    """Slow chewing: soft low pulses (she only chews)."""
    m = _m("chew", at, 0.3)
    end = at
    for k in range(n):
        d = 0.28
        s = _norm(_bp(m.noise(d), 150, 700)) * np.hanning(int(d * RATE))
        end = _put(mix, s, at + k * every, gain, pan)
    return end


def nose_bump(mix, at, gain=0.05, pan=0.0):
    """A nose against a calf, a wheel against a hoof: one soft bump."""
    t = _t(0.12)
    x = (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 35) + 0.4 * np.sin(2 * np.pi * 285 * t) * np.exp(-t * 55)) * np.minimum(1, t / 0.006)
    return _put(mix, _fade(_grit(x, 0.5), 0.004, 0.02), at, gain, pan)


# ====================================================================== #
#  ICE                                                                   #
# ====================================================================== #

def ice_form(mix, at, seconds=1.2, gain=0.06, pan=0.0):
    """ICE FORMING: a thin high ring climbing, with fine ticks that crowd
    together as the water sets. Ends on nothing: follow it with silence()."""
    m = _m("ice_form", at, seconds)
    n = int(seconds * RATE)
    t = _t(seconds)[:n]
    x = (_sweep(2300, 4700, seconds, 1.5)[:n] + 0.5 * _sweep(3450, 7000, seconds, 1.5)[:n]) * (t / seconds) ** 1.5 * 0.5
    for k in range(40):
        u = 1 - (1 - k / 40) ** 2
        c = _ping(m.rs.uniform(3500, 7500), 0.015, 0.003)
        _place(x, c * m.rs.uniform(0.2, 0.7), min(seconds - 0.02, u * seconds))
    x[-int(0.02 * RATE):] *= np.linspace(1, 0, int(0.02 * RATE))
    return _put(mix, x, at, gain, pan)


def ice_crack(mix, at, seconds=1.4, gain=0.5, pan=0.15, width=0.8):
    """ICE CRACKING: one sharp crack on `at`, then a long tear of small cracks
    running out across the pan in both directions, then plates knocking, low."""
    m = _m("ice_crack", at, seconds)
    t = _t(0.25)
    c = _norm(_bp(m.noise(0.25), 1200, 9000)) * np.exp(-t * 55) + 0.6 * _ping(1900, 0.25, 0.02) + 0.5 * np.sin(2 * np.pi * 140 * t) * np.exp(-t * 25)
    c[: int(0.0006 * RATE)] *= np.linspace(0, 1, int(0.0006 * RATE))
    end = _put(mix, c, at, gain, pan)
    k = 0
    tt = 0.05
    while tt < seconds:
        u = tt / seconds
        s = _norm(_bp(m.noise(0.03), 1500, 8000)) * np.exp(-_t(0.03) * 160) + 0.4 * _ping(m.rs.uniform(1500, 3500), 0.03, 0.006)
        p = pan + width * u * (1 if k % 2 == 0 else -1)
        end = _put(mix, s, at + tt, gain * 0.45 * (1 - 0.7 * u) * m.rs.uniform(0.5, 1.0), p)
        tt += m.rs.uniform(0.015, 0.05) * (1 + 2 * u)
        k += 1
    for j in range(4):                          # plates
        tp = _t(0.3)
        s = np.sin(2 * np.pi * m.rs.uniform(70, 110) * tp) * np.exp(-tp * 14)
        end = _put(mix, s, at + seconds * 0.6 + j * m.rs.uniform(0.25, 0.4), gain * 0.3, pan + m.rs.uniform(-0.5, 0.5))
    return end


def skid(mix, at, seconds=0.3, gain=0.05, pan=0.15):
    """A hoof skidding on ice: a short dry scrape."""
    m = _m("skid", at, seconds)
    n = int(seconds * RATE)
    x = _norm(_bp(m.noise(seconds), 1800, 6000))[:n] * np.linspace(1, 0, n) ** 1.5
    return _put(mix, _fade(x, 0.004, 0.02), at, gain, pan)


# ====================================================================== #
#  THE TWO ROOMS                                                         #
# ====================================================================== #

def _edge(n, fin, fout):
    e = np.ones(n)
    a, b = min(n, int(fin * RATE)), min(n, int(fout * RATE))
    if a:
        e[:a] = np.linspace(0, 1, a)
    if b:
        e[-b:] *= np.linspace(1, 0, b)
    return e


def crickets(mix, at, seconds, voices=3, gain=0.022, stop=None, fade_in=0.5):
    """Dusk crickets: each voice its own pitch, place and irregular pulse.
    stop = a list of times (film seconds), one per voice, at which that cricket
    stops: they go quiet one by one."""
    m = _m("crickets", at, 1.0)
    for v in range(voices):
        f = (4250, 3900, 4600, 4050)[v % 4]
        p = (-0.7, 0.5, 0.1, -0.3)[v % 4]
        end_v = at + seconds if not stop else min(at + seconds, stop[v % len(stop)])
        t = at + m.rs.uniform(0, 0.8)
        while t < end_v - 0.12:
            buf = np.zeros(int(0.13 * RATE))
            for k in range(3):
                pulse = np.sin(2 * np.pi * f * _t(0.02)) * np.hanning(int(0.02 * RATE))
                _place(buf, pulse, k * 0.036)
            g = gain * m.rs.uniform(0.6, 1.0) * min(1.0, (t - at) / max(fade_in, 1e-6) + 0.2)
            _add(mix, buf, t, g, p)
            t += m.rs.uniform(0.45, 1.3)
    return at + seconds


def above(mix, at, seconds, gain=1.0, fade_in=0.3, fade_out=0.3, creek=True):
    """The ABOVE room: dry and close. A very low wind, the lamp's hum on the
    left, the creek running quietly on the right. (Crickets are separate.)"""
    m = _m("above", at, seconds)
    n = int(seconds * RATE)
    e = _edge(n, fade_in, fade_out)
    t = _t(seconds)[:n]
    w = _norm(_lp(m.noise(seconds, "brown"), 260))[:n] * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))
    _add(mix, w * e, at, 0.010 * gain, -0.1)
    hum = np.sin(2 * np.pi * 100 * t) + 0.3 * np.sin(2 * np.pi * 200 * t)
    _add(mix, hum * e, at, 0.0035 * gain, P_DOOR)
    if creek:
        c = _norm(_bp(m.noise(seconds), 350, 2300))[:n] * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 0.23 * t)))
        _drops(m, c, 0, seconds - 0.05, int(seconds * 5), 700, 1700, 1.2)
        _add(mix, c * e, at, 0.011 * gain, P_WATER)
    return at + seconds


def hush(mix, at, seconds, gain=1.0, fade_in=0.2, fade_out=0.2, drone=True):
    """UNDER-WATER HUSH, the BELOW room: slow low pressure, everything above
    300 Hz gone, and a water drone on 55 and 82.5 Hz that breathes."""
    m = _m("hush", at, seconds)
    n = int(seconds * RATE)
    e = _edge(n, fade_in, fade_out)
    t = _t(seconds)[:n]
    w = _norm(_lp(m.noise(seconds, "brown"), 300))[:n] * (0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * t))
    _add(mix, w * e, at, 0.014 * gain, -0.25)
    w2 = _norm(_lp(m.noise(seconds, "brown"), 300))[:n] * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t + 1))
    _add(mix, w2 * e, at, 0.014 * gain, 0.25)
    mid = _norm(_bp(m.noise(seconds), 180, 620))[:n] * (0.65 + 0.35 * np.sin(2 * np.pi * 0.05 * t + 2))
    _add(mix, mid * e, at, 0.016 * gain, 0.0)
    if drone:
        tfilm = at + t                               # phase from the film clock: it comes back as it was
        d = (np.sin(2 * np.pi * 55 * tfilm) + 0.6 * np.sin(2 * np.pi * 82.5 * tfilm) + 0.25 * np.sin(2 * np.pi * 110 * tfilm)
             + 0.22 * np.sin(2 * np.pi * 165 * tfilm) + 0.14 * np.sin(2 * np.pi * 220 * tfilm))
        d *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * tfilm)
        _add(mix, d * e, at, 0.013 * gain, 0.0)
    return at + seconds


def swap_down(mix, at, size=1.0, gain=0.42, pan=P_WATER * 0.6):
    """The crossing DOWN as one call: the plunge on `at`, the first bubbles."""
    plunge(mix, at, size, gain, pan)
    return bubbles(mix, at + 0.35, 6, 1.2, gain=0.07, pan=pan)


def swap_up(mix, at, size=1.0, gain=0.36, pan=P_WATER * 0.4):
    """The crossing UP as one call: last bubbles, then the breach on `at`."""
    bubbles(mix, at - 0.7, 4, 0.5, gain=0.05, pan=pan)
    return breach(mix, at, size, gain, pan)


# The room plan (film seconds). Each entry: (start, end, "above"|"below"|"both").
# "both" is the board's split frame: both rooms at half level.
ROOMS = [
    (0.0, 22.6, "above"), (22.6, 53.5, "below"), (53.5, 56.5, "both"), (56.5, 59.2, "below"),
    (59.2, 67.0, "above"), (67.0, 81.0, "both"), (81.0, 98.3, "above"), (98.3, 118.0, "below"),
    # 118.0-122.0: nothing at all (the ice)
    (122.0, 131.0, "below"), (131.0, 137.0, "both"), (137.0, 141.9, "below"),
    (141.9, 170.0, "above"), (170.0, 171.5, "below"), (171.5, 175.0, "above"), (175.0, 180.0, "both"),
]


def beds(mix, rooms=ROOMS):
    """Lay the two rooms across the film from the ROOMS plan. A swap takes 0.2 s."""
    for a, b, kind in rooms:
        g = 0.5 if kind == "both" else 1.0
        if kind in ("above", "both"):
            above(mix, a - 0.1, b - a + 0.2, g, 0.2, 0.2)
        if kind in ("below", "both"):
            hush(mix, a - 0.1, b - a + 0.2, g, 0.2, 0.2)
    # crickets: all of dusk above water; they stop one by one before the howl,
    # one comes back at 88.9, and they are the only thing in the ears-down hold.
    crickets(mix, 0.5, 21.9, 3)
    crickets(mix, 59.6, 26.4, 3, gain=0.018, stop=[84.4, 85.0, 85.6])
    crickets(mix, 88.9, 8.6, 1, gain=0.018)
    crickets(mix, 142.5, 11.0, 2, gain=0.018)
    crickets(mix, 153.0, 16.5, 2, gain=0.012)
    crickets(mix, 172.0, 8.0, 2, gain=0.012)


# ====================================================================== #
#  MUSIC                                                                 #
# ====================================================================== #
#
# There is no score laid over this film. There are three kinds of music and
# each one comes from somewhere in the picture:
#   the RADIO on the step (one thin plucked voice, the motif, from one place);
#   the TOWN's own chimes (lamps, the school bell), heard through water;
#   the PACK's ROUND: the same four-note motif in several low voices at once,
#     each at its own pitch and its own moment. One dog = one voice. The pack =
#     the same tune all at once. That is the film's idea, played.
# Silence is written in: every stretch where a character thinks has no music.

def pack_round(mix, at, seconds, voices=5, enter=2.0, gain=0.028, leave=None, pan_width=0.6):
    """The pack's round, under water: the motif in up to `voices` low voices.
    Voice v enters `enter`*v seconds after `at` (enter=0: all are already there).
    Every voice repeats every 3 s but offset inside the bar, so no two land
    together. leave = {voice: film time} stops single voices early (the eleven
    going up). Phase comes from the film clock, so it resumes exactly."""
    pitches = (110.0, 164.81, 220.0, 261.63, 329.63, 392.0)
    notes = ((1.0, 1.0, 1.189, 0.891), (1.0, 1.122, 1.335, 1.0), (1.0, 1.0, 1.335, 1.189),
             (0.891, 1.0, 1.189, 1.0), (1.0, 1.189, 1.498, 1.335), (1.0, 1.0, 1.122, 0.891))
    end = at + seconds
    for v in range(min(voices, 6)):
        start_v = at + enter * v
        stop_v = end if not leave or v not in leave else min(end, leave[v])
        off = (v * 0.37) % 3.0
        k = math.ceil((start_v - off) / 3.0)
        while True:
            t0 = off + 3.0 * k
            k += 1
            if t0 + MOTIF[3] + 0.6 > stop_v:
                break
            for j, on in enumerate(MOTIF):
                f = pitches[v] * notes[v][j]
                d = 0.75 if j == 2 else 0.42
                tt = _t(d)
                s = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * tt)) * np.minimum(1, tt / 0.03) * np.exp(-tt * (3.2 if j == 2 else 5.5))
                _put(mix, _lp(_fade(s, 0, 0.05), 900), t0 + on, gain * (1.0, 0.8, 1.0, 0.75)[j],
                     pan_width * (v / 5.0 * 2 - 1) * (1 if v % 2 else -1), norm=True)
    return end


def music_s1(mix, t0=0.0):
    """S1 THE DOOR (28 s). Nothing under the herd, the noses or the first
    asking. The radio is switched on at +13.0; four phrases; the tune stops for
    the second in which the dog decides (+19.5 to +20.6); one more phrase as it
    walks in; the water closes over it at +22.6. Then the town's seven lamps."""
    radio_hiss(mix, t0 + 12.9, 6.45, fade_out=0.15)      # off the air for the second it decides
    radio_hiss(mix, t0 + 20.65, 1.95, fade_in=0.1, fade_out=0.15)
    radio_dial(mix, t0 + 13.0)
    for k, t in enumerate((13.7, 16.7)):
        radio_phrase(mix, t0 + t, k)
    radio_phrase(mix, t0 + 20.7, 2, ring=0.7)
    for k in range(7):
        lamp_chime(mix, t0 + 24.0 + k * 0.5, k, pan=-0.7 + k * 0.23)


def music_s2(mix, t0=28.0):
    """S2 TROUTTOWN (30 s). The school bell twice at +0.5 and +1.4. Then no
    music at all through the digs and the six seconds in which the dog reads the
    page and decides. One lamp answers the motif as the dog rises (+28.6)."""
    school_bell(mix, t0 + 0.5)
    school_bell(mix, t0 + 1.4, gain=0.07)
    for j, on in enumerate(MOTIF):
        lamp_chime(mix, t0 + 28.6 + on * 1.3, (0, 0, 2, 1)[j], gain=0.022, pan=-0.3 + 0.2 * j, seconds=1.1)


def music_s3(mix, t0=58.0):
    """S3 AGAIN, SOONER (26 s). The radio is still playing on the step: a phrase
    every 3 s from +2.2. It does not speed up when the asking does; the asking
    outruns the tune. The hand turns it off after the phrase at +20.2; the last
    3.5 s (the tired dog, the quiet line) have no music."""
    radio_hiss(mix, t0 + 1.8, 20.65, fade_out=0.3)
    for k in range(7):
        radio_phrase(mix, t0 + 2.2 + 3.0 * k, (0, 1, 0, 2, 0, 1, 4)[k], ring=0.9 if k < 6 else 1.1)


def music_s4(mix, t0=84.0):
    """S4 THE PACK (32 s). No music above the water: the howl stands alone and
    the hold after it is empty. Below, from +17.0, the round: the motif in five
    low voices that come in one every two seconds as each dog starts its job."""
    pack_round(mix, t0 + 17.0, 15.0, voices=5, enter=2.0)


def music_s5(mix, t0=116.0):
    """S5 ICE, AND ELEVEN (28 s). The round goes on, then stops dead at +2.0 with
    everything else. Four seconds of nothing. After the crack (+7.0) it comes
    back in all five voices, where it would have been. From +11.0 the voices
    leave one by one as the eleven go up; one voice finishes alone and stops at
    +23.9 for the hold. No music on the bank: the cows' breathing is enough."""
    pack_round(mix, t0, 2.0, voices=5, enter=0.0)
    pack_round(mix, t0 + 7.0, 16.9, voices=5, enter=0.0,
               leave={4: t0 + 11.5, 3: t0 + 13.0, 1: t0 + 14.5, 0: t0 + 16.0})


def music_s6(mix, t0=144.0):
    """S6 NO, AND AGAIN (36 s). The radio comes back, quiet, for one phrase and
    half of the next, and the hand turns it off at +5.0 with the "no". Nothing
    for twenty-six seconds: the ears, the six, the old dog's look and its back,
    the reel going down and coming up changed. At +31.2 (the bell has settled)
    the radio returns, slower; three phrases; the last note is left to ring."""
    radio_hiss(mix, t0 + 0.4, 4.6, fade_out=0.1)
    radio_phrase(mix, t0 + 0.8, 1)
    radio_phrase(mix, t0 + 3.3, 0, ring=0.6)
    radio_hiss(mix, t0 + 31.0, 4.95, fade_in=0.6, fade_out=1.5)
    radio_phrase(mix, t0 + 31.2, 0, slow=1.4, gain=0.022)
    radio_phrase(mix, t0 + 33.3, 4, slow=1.4, gain=0.022, ring=2.6)


MUSIC = {1: music_s1, 2: music_s2, 3: music_s3, 4: music_s4, 5: music_s5, 6: music_s6}

# Stretches with NO music, because somebody is thinking (film seconds).
THINKING = [
    (0.0, 12.9, "the herd files past; noses; the asking; the dog backs off"),
    (19.4, 20.6, "the dog looks at the water and decides"),
    (32.6, 56.5, "digging, then the dog reads the page and decides"),
    (80.6, 101.0, "the tired dog; the quiet line; the howl and the hold after it"),
    (118.0, 123.0, "under the ice; she stamps"),
    (139.9, 144.4, "the lead dog finishes alone; pleased"),
    (149.1, 175.0, "no; ears down; the old dog's look, its back, the reel changed"),
]


def music(mix, sequences=(1, 2, 3, 4, 5, 6)):
    """All the music, or only the sequences named. Times are film seconds."""
    for s in sequences:
        MUSIC[s](mix)


# ====================================================================== #
#  THE CUE SHEET (board part F), sequence by sequence                    #
# ====================================================================== #
# Every time below is the board's. If a builder's action lands on another
# frame, the builder's frame wins: change the number here, nothing else.

def sfx_s1(mix):
    # the file comes down the path: hooves on earth, the bell on each nod
    hooves(mix, 0.3, 6, 0.55, "earth", gain=0.05, gain_to=0.12, pan=0.7, pan_to=0.25)
    cowbell(mix, 0.3, 3, 1.1, gain=0.04, pan=0.6)
    cowbell(mix, 1.6, gain=0.07, pan=P_GATE, hard=True)          # against the gate post
    cowbell(mix, 2.2, 2, 0.55, gain=0.06, pan=0.2)
    # noses: hooves stop at 3.4; the bell swings twice more by itself
    cowbell(mix, 3.45, gain=0.05, pan=0.1)
    cowbell(mix, 3.95, gain=0.03, pan=0.1)
    collar(mix, 3.6, 2, gain=0.04, pan=0.0)                      # the dog's head coming up to hers
    cow_breath(mix, 4.6, 1.5, pan=0.1)                           # one long breath out, onto the dog
    hooves(mix, 5.6, 3, 0.55, "wood", gain=0.1, pan=0.2, pan_to=0.45)
    drinking(mix, 6.5, 9.0)
    # Line 1 and the four taps
    voice_call(mix, 6.2)
    taps(mix, 6.2)
    pebble(mix, 7.75)
    # the reach; the dog backs off
    paws(mix, 8.6, 2, 0.3, gain=0.12, pan=-0.3, pan_to=-0.1)
    collar(mix, 8.65, 2, gain=0.04, pan=-0.2)
    hooves(mix, 7.0, 3, 0.55, "earth", gain=0.09, pan=0.5, pan_to=0.3)   # second cow arrives, stops at 8.0
    # the person sits; the radio goes on the step
    creak(mix, 11.0)
    radio_down(mix, 12.6)
    # it decides (19.5): drinking pauses here too (drinking above ends 15.5; a second run after)
    drinking(mix, 16.2, 3.0)
    paws(mix, 21.0, 3, 0.3, gain=0.11, pan=0.1, pan_to=0.4, wet=True)
    wade(mix, 21.2, 0.8, 2)
    swap_down(mix, 22.0)
    cowbell(mix, 22.1, gain=0.08, pan=0.3, hard=True)            # her head jerking up
    cowbell(mix, 23.4, gain=0.05, pan=0.3, under=True)           # one knock from above, through water


def sfx_s2(mix):
    fish_murmur(mix, 29.2, 1.8, pan=-0.2)
    land(mix, 31.0)
    dig(mix, 33.0, 1.0, find=None)
    dig(mix, 34.5, 1.0, find="thud")
    dig(mix, 36.0, 1.2, find="ring")
    bubbles(mix, 37.4, 3, 0.5, gain=0.04)
    set_down(mix, 39.0)
    sniff(mix, 42.5, 2, gain=0.05, under=1500)
    bubble_picture(mix, 45.5, 2.4)
    fish_murmur(mix, 47.9, 1.2, gain=0.02, pan=0.2)
    page_taken(mix, 50.5)
    bubbles(mix, 52.6, 3, 0.4, gain=0.05)                        # the bubble breaking
    # the cow who cannot follow (split frame)
    plunge(mix, 54.2, 1.6, gain=0.3, pan=0.35)                   # her foreleg in
    cowbell(mix, 54.25, 2, 0.22, gain=0.07, pan=0.35, hard=True)
    hooves(mix, 54.8, 3, 0.2, "wood", gain=0.09, pan=0.35)       # scrabbling back onto the board
    moo(mix, 54.9, 0.7)
    bubbles(mix, 55.0, 5, 0.8, low=True, gain=0.07, pan=0.3)
    swap_up(mix, 59.2)


def sfx_s3(mix):
    shake(mix, 60.0)
    cowbell(mix, 60.5, 2, 0.3, gain=0.05, pan=0.3)               # spray reaches her; the bell rattles
    hooves(mix, 61.0, 6, 0.55, "earth", gain=0.1, gain_to=0.05, pan=0.3, pan_to=0.7)   # she walks off
    page_slap(mix, 61.6)
    paw_press(mix, 62.3, pan=P_SILL)
    hooves(mix, 64.0, 3, 0.55, "wood", gain=0.09, pan=P_GATE)    # second cow through the gate
    taps(mix, 65.0)
    pebble(mix, 66.4)
    drinking(mix, 66.5, 5.5)                                     # one unbroken slow drinking
    paws(mix, 66.4, 3, 0.18, gain=0.1, pan=0.0, pan_to=0.4)
    plunge(mix, 67.0, gain=0.32)
    # round two (67-72): shorter
    dig(mix, 68.2, 0.8, find="ring", gain=0.07)
    breach(mix, 70.4, gain=0.28)
    shake(mix, 70.8, 0.6, gain=0.14)
    reel_down(mix, 71.6, gain=0.16)
    taps(mix, 72.2, gain=0.11)
    pebble(mix, 73.5)
    hooves(mix, 72.2, 5, 0.55, "earth", gain=0.09, pan=0.5, pan_to=P_GATE)    # the cow tempo does not change
    plunge(mix, 73.0, gain=0.3)
    # round three (73-76.3): sooner
    dig(mix, 73.7, 0.5, find=None, gain=0.07)
    breach(mix, 75.0, gain=0.27)
    shake(mix, 75.3, 0.4, gain=0.12)
    page_slap(mix, 75.9, gain=0.09)                              # half made
    hooves(mix, 75.0, 2, 0.55, "wood", gain=0.09, pan=P_GATE)
    taps(mix, 76.3, gain=0.11)
    calf(mix, 76.2, 6, 0.13, pan=0.3, pan_to=0.45)               # the calf starts to follow the dog
    plunge(mix, 76.9, gain=0.28)
    taps(mix, 77.4, gain=0.1)                                    # asked again before it is back
    nose_bump(mix, 77.55, pan=0.4)                               # nosed back into line
    nose_bump(mix, 78.05, pan=0.35)
    calf(mix, 78.2, 4, 0.16, gain=0.05, pan=0.4, pan_to=0.3)
    pebble(mix, 78.75)
    breach(mix, 78.5, gain=0.26)
    page_slap(mix, 79.1, gain=0.07)
    # the tired dog
    pant(mix, 79.5, 4.3, gain=0.045, pan=0.05)
    drip(mix, 80.2, 7, 0.52, pan=0.05)
    drinking(mix, 80.6, 3.0, gain=0.04)
    voice_quiet(mix, 81.2)


def sfx_s4(mix):
    paws(mix, 84.6, 2, 0.4, gain=0.09, pan=0.1, pan_to=0.3)      # turns to the water
    howl(mix, 86.0, 2.0, tail=0.45)                              # voice 86.0-88.0, room gone by 88.45
    # arrivals, each its own material, from every side
    paper_slide(mix, 89.2, pan=-0.8)                             # herding dog
    flutter(mix, 89.7, pan=0.8)                                  # sheepdog
    wheels(mix, 90.0, 0.8, 1.0, pan=-0.5)                        # three retrievers
    wheels(mix, 90.4, 0.8, 1.26, pan=0.0)
    wheels(mix, 90.8, 0.8, 1.5, pan=0.6)
    nose_bump(mix, 91.4, gain=0.07, pan=0.3)                     # wheels bump a hoof
    wire_twang(mix, 91.7, pan=0.4)                               # digger
    page_peel(mix, 92.1, pan=-0.3)                               # bloodhound
    pop(mix, 92.6, pan=0.1)                                      # terrier
    # the old dog comes out through the door and lies down on the sill
    old_dog_down(mix, 93.2, 4, gain=0.1, pan=P_DOOR + 0.2)
    # the herder opens the way
    patter(mix, 93.0, 1.4, pan=0.7, pan_to=-0.2)
    patter(mix, 95.0, 1.1, pan=-0.2, pan_to=0.6)
    hooves(mix, 95.1, 4, 0.55, "grass", gain=0.1, pan=0.3, pan_to=0.6)
    hooves(mix, 95.4, 4, 0.55, "grass", gain=0.08, pan=0.4, pan_to=0.7)
    hooves(mix, 95.8, 3, 0.55, "grass", gain=0.07, pan=0.5, pan_to=0.8)
    cowbell(mix, 95.1, 2, 1.1, gain=0.05, pan=0.4)
    pack_plunge(mix, 97.0, 10, 0.2)
    drip(mix, 97.7, 1, pan=P_DOOR + 0.2)
    drip(mix, 98.0, 1, pan=0.55)                                 # a drip on the calf
    for k in range(10):                                          # ten bubble trails fanning out
        bubbles(mix, 98.4 + 0.05 * k, 3, 1.6, gain=0.03, pan=-0.8 + 0.18 * k)
    work(mix, 101.0, 15.0, voices=7)
    fish_murmur(mix, 103.0, 2.0, gain=0.02, pan=-0.1)
    bubbles(mix, 105.0, 4, 0.6, gain=0.04, pan=0.5)              # the calf's nose in the water, at the very edge
    bubble_picture(mix, 109.5, 2.0, gain=0.045)
    fish_murmur(mix, 111.0, 1.5, gain=0.02, pan=0.1)


def sfx_s5(mix):
    work(mix, 116.0, 0.8, voices=7)
    work(mix, 116.8, 1.2, voices=4, top=320, level=0.7)          # the cold: thins from the top
    ice_form(mix, 116.8, 1.2)
    silence(mix, 118.0, 122.0)                                   # every dog waits
    # she walks out onto the ice, heard faint and dry from above
    hooves(mix, 119.5, 4, 0.36, "ice", gain=0.05, pan=0.3, pan_to=0.15)
    skid(mix, 120.2, gain=0.035)
    silence(mix, 121.0, 122.0, fade=0.01)
    stamp(mix, 122.0)
    stamp(mix, 122.6, gain=0.55, bell=False)
    ice_crack(mix, 122.62)
    hooves(mix, 123.6, 3, 0.4, "wood", gain=0.1, pan=0.15, pan_to=0.3)   # backing onto the board
    splash(mix, 124.3, pan=0.2)
    work(mix, 123.4, 3.6, voices=7)                              # exactly as it was
    for k in range(9):                                           # the second pack, heard from below
        splash(mix, 125.2 + 0.17 * k, gain=0.07, pan=-0.6 + 0.15 * k, under=True)
    work(mix, 127.0, 4.0, voices=4, level=0.8)                   # later: thinning
    # eleven run out of breath
    for k in range(11):
        tk = 131.0 + (0.42 * k if k < 6 else 2.5 + 0.12 * (k - 6))
        breath_out(mix, tk, 0.9, gain=0.07, pan=-0.6 + 0.12 * k)
        breach(mix, tk + 1.3, 0.7, gain=0.13, pan=0.1 + 0.05 * k)
        gasp(mix, tk + 1.5, gain=0.06, pan=0.1 + 0.05 * k)
    shiver(mix, 133.0, 3.0, pan=0.3)
    hooves(mix, 133.4, 4, 0.55, "grass", gain=0.09, pan=0.6, pan_to=0.35)
    hooves(mix, 134.0, 4, 0.55, "grass", gain=0.08, pan=0.7, pan_to=0.45)
    cowbell(mix, 133.4, 2, 1.1, gain=0.04, pan=0.5)
    for k, tk in enumerate((134.3, 135.0, 135.6, 136.2)):        # long warm breaths, overlapping
        cow_breath(mix, tk, 1.8, gain=0.06, pan=0.2 + 0.12 * k)
    # one dog finishes alone
    work(mix, 137.0, 2.9, voices=1, level=0.9)
    set_down(mix, 137.3)
    ratchet(mix, 137.8, 1.3, 9, gain=0.05, under=1500)
    set_down(mix, 139.3, gain=0.07)                              # the lid
    paw_press(mix, 139.6, under=600)
    swap_up(mix, 141.9, gain=0.34)
    shake(mix, 142.3, 1.0, gain=0.22)
    reel_down(mix, 143.3)
    tail(mix, 143.5, 4)


def sfx_s6(mix, look_tone=True):
    tail(mix, 144.4, 4)
    tail(mix, 146.0, 4)
    ratchet(mix, 146.6, 0.6, 16, gain=0.05, pan=P_DOOR + 0.1)    # film pulled off the reel, to the lamp
    tail(mix, 147.6, 4)
    tail(mix, 148.5, 3)                                          # stops mid-pattern at 149.0
    voice_no(mix, 148.2)
    sigh(mix, 151.6, 1.0, gain=0.05, pan=0.0)                    # it does not argue
    cow_up(mix, 153.5, pan=0.3)
    hooves(mix, 154.9, 4, 0.55, "earth", gain=0.09, pan=0.3, pan_to=0.1)
    cowbell(mix, 154.9, 2, 1.1, gain=0.05, pan=0.2)
    paws(mix, 154.3, 4, 0.14, gain=0.1, pan=-0.1, pan_to=0.3)
    pack_plunge(mix, 155.0, 6, 0.08, gain=0.2)
    for k in range(7):                                           # the third pack, a ragged run
        splash(mix, 155.6 + 0.19 * k + 0.05 * (k % 3), gain=0.1, pan=0.1 + 0.1 * k)
    card_drag(mix, 156.2, 0.8)                                   # the old dog shifting
    for k, tk in enumerate((157.2, 158.4, 159.6)):               # the gate: three reels pass
        breach(mix, tk, 0.8, gain=0.2)
        drip(mix, tk + 0.3, 1)
        sniff(mix, tk + 0.45, 1, gain=0.04, pan=P_SILL)
        reel_down(mix, tk + 0.8, gain=0.16)
    cow_breath(mix, 159.8, 1.8, pan=0.15)
    # THE DEFINING PASSAGE 161.0-173.0
    breach(mix, 161.0, 0.8, gain=0.2)
    wheels(mix, 161.5, 0.9, 1.26, gain=0.07, pan=0.1, pan_to=P_SILL)
    peg_tick(mix, 162.0, 22, 0.25)                               # ticks to 167.25; stops at 167.5
    if look_tone:
        long_look(mix, 164.0, 1.5)                               # the look
    creak(mix, 165.5, 0.5, gain=0.05, pan=P_SILL)
    t = old_dog_down(mix, 165.7, 3, gain=0.1)                    # gets up, turns, lies down, back to the reel
    drip(mix, 168.2, 1)
    chew(mix, 168.9, 2, pan=0.2)                                 # she only chews
    wheels(mix, 169.2, 0.5, 1.26, gain=0.05, pan=P_SILL, pan_to=0.2)
    splash(mix, 169.8, gain=0.14)
    set_down(mix, 170.3, gain=0.07)                              # lid off
    bubble_picture(mix, 170.4, 0.7, gain=0.04)
    set_down(mix, 170.95, gain=0.07)                             # lid on
    paw_press(mix, 171.15, under=600)
    breach(mix, 171.6, 0.8, gain=0.2)
    drip(mix, 171.9, 1)
    card_drag(mix, 172.1, 0.5)                                   # the tail pulled aside: room is made
    reel_down(mix, 172.6, gain=0.17)
    sigh(mix, 172.75, 0.8, gain=0.035, pan=P_SILL)
    # the lit door
    cow_down(mix, 173.0, pan=-0.05)                              # bell settles at 175.0
    paws(mix, 175.6, 3, 0.5, gain=0.06, pan=P_SILL, claw=False)
    paw_press(mix, 177.0, gain=0.06, pan=P_SILL)                 # a body on boards
    drip(mix, 177.4, 1, on="water", pan=0.2)                     # a tail in water
    fish_murmur(mix, 176.0, 3.0, gain=0.018, pan=0.2)
    peg_tick(mix, 178.0)
    return t


SFX = {1: sfx_s1, 2: sfx_s2, 3: sfx_s3, 4: sfx_s4, 5: sfx_s5, 6: sfx_s6}


def sfx(mix, sequences=(1, 2, 3, 4, 5, 6)):
    for s in sequences:
        SFX[s](mix)


def score(mix, do_beds=True, do_music=True, do_sfx=True):
    """The whole 180 s sound track: use as  film.sound(sound.score).
    Order matters: beds and music first, then the cue sheet, because the cue
    sheet declares the film's silences (it empties the mix under the ice)."""
    if do_beds:
        beds(mix)
        duck(mix, 19.4, 20.6, 0.6, 0.15)        # the second in which the dog decides
    if do_music:
        music(mix)
    if do_sfx:
        sfx(mix)
    else:
        silence(mix, 118.0, 122.0)
    return mix


# ====================================================================== #
#  RENDER AND MEASURE                                                    #
# ====================================================================== #

LIBRARY = [  # (name, seconds to render, call)
    ("paws", 1.2, lambda m, t: paws(m, t)),
    ("collar", 0.6, lambda m, t: collar(m, t)),
    ("sniff", 0.6, lambda m, t: sniff(m, t)),
    ("pant", 2.0, lambda m, t: pant(m, t)),
    ("sigh", 1.5, lambda m, t: sigh(m, t)),
    ("tail", 1.4, lambda m, t: tail(m, t)),
    ("howl", 3.4, lambda m, t: howl(m, t)),
    ("bark", 0.5, lambda m, t: bark(m, t)),
    ("voice_call", 1.8, lambda m, t: voice_call(m, t)),
    ("voice_quiet", 2.2, lambda m, t: voice_quiet(m, t)),
    ("voice_no", 1.7, lambda m, t: voice_no(m, t)),
    ("taps", 1.6, lambda m, t: taps(m, t)),
    ("pebble", 0.5, lambda m, t: pebble(m, t)),
    ("creak", 0.8, lambda m, t: creak(m, t)),
    ("radio_down", 0.4, lambda m, t: radio_down(m, t)),
    ("radio_dial", 0.9, lambda m, t: radio_dial(m, t)),
    ("radio_hiss", 3.4, lambda m, t: radio_hiss(m, t, 3.0)),
    ("radio_phrase", 2.6, lambda m, t: radio_phrase(m, t)),
    ("wade", 1.4, lambda m, t: wade(m, t)),
    ("plunge", 1.8, lambda m, t: plunge(m, t)),
    ("pack_plunge", 2.0, lambda m, t: pack_plunge(m, t)),
    ("splash", 1.1, lambda m, t: splash(m, t)),
    ("bubbles", 1.6, lambda m, t: bubbles(m, t)),
    ("bubble_picture", 2.6, lambda m, t: bubble_picture(m, t)),
    ("breach", 1.6, lambda m, t: breach(m, t)),
    ("shake", 1.3, lambda m, t: shake(m, t)),
    ("drip", 1.9, lambda m, t: drip(m, t, 3)),
    ("breath_out", 1.8, lambda m, t: breath_out(m, t)),
    ("gasp", 1.0, lambda m, t: gasp(m, t)),
    ("shiver", 2.4, lambda m, t: shiver(m, t)),
    ("land", 0.8, lambda m, t: land(m, t)),
    ("dig", 2.2, lambda m, t: dig(m, t, find="ring")),
    ("set_down", 0.4, lambda m, t: set_down(m, t)),
    ("paw_press", 0.5, lambda m, t: paw_press(m, t)),
    ("page_taken", 1.5, lambda m, t: page_taken(m, t)),
    ("lamp_chime", 2.9, lambda m, t: lamp_chime(m, t)),
    ("school_bell", 3.5, lambda m, t: school_bell(m, t)),
    ("fish_murmur", 2.4, lambda m, t: fish_murmur(m, t)),
    ("reel_down", 1.1, lambda m, t: reel_down(m, t)),
    ("page_slap", 0.5, lambda m, t: page_slap(m, t)),
    ("ratchet", 1.2, lambda m, t: ratchet(m, t)),
    ("old_dog_down", 4.6, lambda m, t: old_dog_down(m, t)),
    ("card_drag", 1.3, lambda m, t: card_drag(m, t)),
    ("long_look", 1.9, lambda m, t: long_look(m, t)),
    ("wheels", 1.4, lambda m, t: wheels(m, t)),
    ("peg_tick", 1.4, lambda m, t: peg_tick(m, t, 4)),
    ("wire_twang", 1.0, lambda m, t: wire_twang(m, t)),
    ("paper_slide", 0.8, lambda m, t: paper_slide(m, t)),
    ("flutter", 1.0, lambda m, t: flutter(m, t)),
    ("page_peel", 0.7, lambda m, t: page_peel(m, t)),
    ("pop", 0.4, lambda m, t: pop(m, t)),
    ("patter", 1.9, lambda m, t: patter(m, t)),
    ("work", 6.5, lambda m, t: work(m, t, 6.0)),
    ("hooves", 2.6, lambda m, t: hooves(m, t)),
    ("hooves_ice", 2.0, lambda m, t: hooves(m, t, 4, 0.36, "ice")),
    ("calf", 1.2, lambda m, t: calf(m, t)),
    ("cowbell", 0.9, lambda m, t: cowbell(m, t)),
    ("cowbell_under", 0.9, lambda m, t: cowbell(m, t, under=True)),
    ("cow_breath", 2.0, lambda m, t: cow_breath(m, t)),
    ("drinking", 2.2, lambda m, t: drinking(m, t)),
    ("moo", 1.1, lambda m, t: moo(m, t)),
    ("stamp", 1.2, lambda m, t: stamp(m, t)),
    ("cow_down", 4.2, lambda m, t: cow_down(m, t)),
    ("cow_up", 2.6, lambda m, t: cow_up(m, t)),
    ("chew", 1.4, lambda m, t: chew(m, t)),
    ("nose_bump", 0.4, lambda m, t: nose_bump(m, t)),
    ("ice_form", 1.6, lambda m, t: ice_form(m, t)),
    ("ice_crack", 3.2, lambda m, t: ice_crack(m, t)),
    ("skid", 0.6, lambda m, t: skid(m, t)),
    ("crickets", 4.4, lambda m, t: crickets(m, t, 4.0)),
    ("above", 4.4, lambda m, t: above(m, t, 4.0)),
    ("hush", 4.4, lambda m, t: hush(m, t, 4.0)),
    ("pack_round", 9.5, lambda m, t: pack_round(m, t, 9.0, enter=1.0)),
]
LEAD = 0.25   # every library wav starts with 0.25 s of nothing; the call is at 0.25


def _db(x):
    return -120.0 if x <= 1e-6 else 20 * math.log10(x)


def write_wav(path, st):
    """Write float stereo [-1, 1] as 16-bit wav with NO gain change."""
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def a_weighted_db(st):
    """RMS in dB after the standard A curve (a rough stand-in for how loud a
    level is to an ear; it is still a number, not listening)."""
    mono = np.asarray(st).mean(1) if np.asarray(st).ndim == 2 else np.asarray(st)
    if len(mono) < 16:
        return -120.0
    X = np.fft.rfft(mono)
    f = np.fft.rfftfreq(len(mono), 1 / RATE)
    f2 = f ** 2
    A = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2) + 1e-30) * 1.2589
    y = np.fft.irfft(X * A, len(mono))
    return _db(float(np.sqrt((y ** 2).mean())))


def measure(st, lead=0.0):
    """Peak, RMS of the sounding part, how long it sounds, when it starts,
    where its energy sits. All from the samples; nothing here is hearing."""
    mono = st.mean(1)
    peak = float(np.abs(st).max())
    if peak <= 0:
        return dict(peak_db=-120.0, rms_db=-120.0, a_db=-120.0, sounding_s=0.0, onset_ms=None, centroid_hz=0, below_700_pct=0, above_200_pct=0)
    env = np.abs(st).max(1)
    idx = np.nonzero(env > peak * 0.001)[0]          # within 60 dB of the peak
    act = st[idx[0]:idx[-1] + 1]
    on = np.nonzero(env > peak * 0.1)[0][0]
    X = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1 / RATE)
    tot = X.sum() + 1e-30
    return dict(peak_db=round(_db(peak), 1), rms_db=round(_db(float(np.sqrt((act ** 2).mean()))), 1),
                sounding_s=round(len(act) / RATE, 2), onset_ms=round((on / RATE - lead) * 1000, 1),
                centroid_hz=int((X * f).sum() / tot), below_700_pct=int(round(100 * X[f < 700].sum() / tot)),
                a_db=round(a_weighted_db(act), 1), above_200_pct=int(round(100 * X[f > 200].sum() / tot)))


def _stereo(mix):
    return np.stack([mix.L, mix.R], 1)


def _win_rms(st, a, b):
    seg = st[int(a * RATE):int(b * RATE)]
    return _db(float(np.sqrt((seg ** 2).mean()))) if len(seg) else -120.0


def _win_peak(st, a, b):
    seg = st[int(a * RATE):int(b * RATE)]
    return _db(float(np.abs(seg).max())) if len(seg) else -120.0


def render_all():
    OUT.mkdir(exist_ok=True)
    report = {"library": {}, "music": {}, "score": {}}
    print("LIBRARY (each rendered alone at its default gain; call at 0.25 s)")
    print(f"{'sound':16} {'peak dBFS':>9} {'rms dBFS':>9} {'rms dBA':>8} {'sounds s':>8} {'onset ms':>8} {'centroid':>8} {'<700Hz %':>8} {'>200Hz %':>8}")
    for name, sec, call in LIBRARY:
        m = Mix(sec + LEAD, seed=1)
        call(m, LEAD)
        st = _stereo(m)
        write_wav(OUT / f"{name}.wav", st)
        r = measure(st, LEAD)
        report["library"][name] = r
        print(f"{name:16} {r['peak_db']:9.1f} {r['rms_db']:9.1f} {r['a_db']:8.1f} {r['sounding_s']:8.2f} {r['onset_ms']:8.1f} {r['centroid_hz']:8d} {r['below_700_pct']:8d} {r['above_200_pct']:8d}")

    # music alone
    mm = Mix(SECONDS, seed=2)
    music(mm)
    silence(mm, 118.0, 122.0)
    mst = _stereo(mm)
    print("\nMUSIC (alone, no beds, no effects)")
    for s, (a, b) in SEQ.items():
        seg = mst[int(a * RATE):int(b * RATE)]
        write_wav(OUT / f"music_s{s}.wav", seg)
        r = measure(seg)
        env = np.abs(seg).max(1)
        k = int(0.25 * RATE)
        blocks = env[: len(env) // k * k].reshape(-1, k).max(1)
        r["silent_pct"] = int(round(100 * float((blocks < 10 ** (-70 / 20)).mean())))
        r["seconds"] = round(len(seg) / RATE, 3)
        report["music"][f"s{s}"] = r
        print(f"  S{s} {r['seconds']:6.2f} s  peak {r['peak_db']:6.1f}  rms {r['rms_db']:6.1f}  silent (under -70 dBFS) {r['silent_pct']:3d} % of the sequence")
    print("  music inside the thinking stretches (peak dBFS; -120 = digital zero):")
    report["music"]["thinking"] = []
    for a, b, why in THINKING:
        p = round(_win_peak(mst, a + 0.05, b - 0.05), 1)
        assert p <= -90.0, f"music sounds in a thinking stretch {a}-{b}: {p} dBFS"
        report["music"]["thinking"].append([a, b, p, why])
        print(f"    {a:6.1f}-{b:6.1f}  {p:7.1f}   {why}")

    # the whole score, before and after the kit's master
    full = Mix(SECONDS, seed=3)
    score(full)
    raw = _stereo(full)
    pcm = full.master().astype(np.float64) / 32767
    write_wav(OUT / "score.wav", pcm)
    for s, (a, b) in SEQ.items():
        write_wav(OUT / f"score_s{s}.wav", pcm[int(a * RATE):int(b * RATE)])
    k = np.abs(raw).max()
    sc = report["score"]
    sc["samples"] = int(len(pcm))
    sc["seconds"] = round(len(pcm) / RATE, 4)
    sc["raw_peak_db"] = round(_db(float(k)), 1)
    sc["master_peak_db"] = round(_db(float(np.abs(pcm).max())), 1)
    sc["master_rms_db"] = round(_db(float(np.sqrt((pcm ** 2).mean()))), 1)
    sc["master_gain_db"] = round(_db(float(np.abs(pcm).max())) - _db(float(k)), 1)
    print(f"\nSCORE  {sc['seconds']} s, {sc['samples']} samples. raw peak {sc['raw_peak_db']} dBFS; "
          f"after kit master: peak {sc['master_peak_db']}, rms {sc['master_rms_db']} (master changed level by {sc['master_gain_db']} dB)")
    env = np.abs(pcm).max(1)
    sec_peak = [float(env[int(i * RATE):int((i + 1) * RATE)].max()) for i in range(int(SECONDS))]
    order = np.argsort(sec_peak)[::-1][:8]
    sc["loudest_seconds"] = [[int(i), round(_db(sec_peak[i]), 1)] for i in order]
    print("  loudest seconds (start s, peak dBFS):", sc["loudest_seconds"])
    checks = {
        "ice silence 118.05-119.45": (118.05, 119.45), "ice hooves 119.5-121.0": (119.5, 121.0),
        "ice silence 121.05-121.95": (121.05, 121.95), "decides 19.5-20.5": (19.5, 20.5),
        "before the decision 17.0-19.0": (17.0, 19.0),
        "howl 86.0-88.2": (86.0, 88.2), "stamp 122.0-122.5": (122.0, 122.5),
        "the look 164.0-165.5": (164.0, 165.5), "ears down 149.5-151.5": (149.5, 151.5),
        "the dog reads 39.5-42.4": (39.5, 42.4), "above bed alone 9.2-10.9": (9.2, 10.9),
        "radio over the bed 13.7-16.0": (13.7, 16.0), "radio at the end 175.5-179.5": (175.5, 179.5),
        "hold after howl 88.47-88.88": (88.47, 88.88), "pack working 104-112": (104.0, 112.0),
        "S3 rounds 67-79": (67.0, 79.0), "last two seconds 178-180": (178.0, 180.0),
    }
    sc["windows"] = {}
    print("  windows of the mastered score (peak dBFS / rms dBFS / A-weighted rms):")
    for name, (a, b) in checks.items():
        p, r = round(_win_peak(pcm, a, b), 1), round(_win_rms(pcm, a, b), 1)
        aw = round(a_weighted_db(pcm[int(a * RATE):int(b * RATE)]), 1)
        sc["windows"][name] = [p, r, aw]
        print(f"    {name:32} {p:7.1f} {r:7.1f} {aw:7.1f}")
    print("  per sequence (mastered):")
    sc["sequences"] = {}
    for s, (a, b) in SEQ.items():
        p, r = round(_win_peak(pcm, a, b), 1), round(_win_rms(pcm, a, b), 1)
        sc["sequences"][f"s{s}"] = [p, r]
        print(f"    S{s} {a:5.0f}-{b:5.0f}  peak {p:6.1f}  rms {r:6.1f}")
    # radio against contact sounds, both measured alone at the gains the score uses
    ra = Mix(3.0, seed=1); radio_phrase(ra, 0.2)
    radio_p = _db(float(np.abs(_stereo(ra)).max()))
    sc["radio_vs_contacts_db"] = {}
    print("  radio phrase peak %.1f dBFS; how far under each contact sound it sits:" % radio_p)
    for nm in ("paws", "taps", "reel_down", "plunge", "breach", "shake", "hooves", "cowbell", "howl", "stamp"):
        d = round(report["library"][nm]["peak_db"] - radio_p, 1)
        sc["radio_vs_contacts_db"][nm] = d
        print(f"    {nm:10} {d:5.1f} dB")
    (OUT / "levels.json").write_text(json.dumps(report, indent=1))
    return report


if __name__ == "__main__":
    render_all()
