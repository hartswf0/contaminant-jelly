"""foley: real recordings for The Dogs of Trouttown, in place of synthesized dogs, cows and water.

Every file is a field recording or foley take foraged under an open licence: CC0 from Freesound, and
public-domain or CC BY / BY-SA from Wikimedia Commons. Credits: films/credits/dogs_freesound.json and
films/credits/dogs_foley.json. Each was trimmed of leading silence and normalised to about -20 LUFS.
NOBODY HAS HEARD THESE. They were chosen by their titles and measured, not listened to.

    import foley
    foley.play(mix, "bark", at=12.4, gain=0.6, pan=-0.2)        # one bark
    foley.play(mix, "creek", at=0, seconds=28, gain=0.25, loop=True)   # a bed under a whole sequence
    foley.NAMES                                                  # what there is

play() returns the time the sound ends. `take` picks between alternates (0, 1); `start` skips into a file.
"""
import os
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(HERE, "foley")
# name -> the takes to use, chosen by title (mismatched downloads are left out)
TAKES = {
    "bark": ["fs_bark_0.wav", "bark_0.wav", "bark_1.wav"], "howl": ["fs_howl_0.wav", "fs_howl_1.wav", "howl_0.wav"], "whine": ["fs_whine_0.wav"],
    "pant": ["fs_pant_0.wav", "fs_pant_1.wav"], "shake": ["fs_shake_0.wav"], "sigh": ["fs_sigh_0.wav"],
    "moo": ["fs_moo_0.wav", "fs_moo_1.wav", "moo_0.wav"], "calf": ["fs_calf_1.wav"], "bell": ["fs_bell_0.wav"],
    "splash": ["fs_splash_0.wav", "fs_splash_1.wav", "splash_0.wav"], "plunge": ["fs_plunge_1.wav"], "under": ["fs_plunge_0.wav", "fs_under_1.wav"],
    "bubbles": ["fs_bubbles_1.wav"], "creek": ["fs_creek_0.wav", "fs_creek_1.wav", "creek_0.wav"], "night": ["fs_night_1.wav", "fs_night_0.wav"], "frogs": ["fs_frogs_0.wav", "fs_frogs_1.wav"],
    "ice": ["fs_ice_1.wav", "fs_ice_0.wav"], "door": ["fs_door_0.wav", "fs_door_1.wav", "door_0.wav"], "radio": ["fs_radio_1.wav", "fs_radio_0.wav"],
    "paper": ["fs_paper_0.wav", "fs_paper_1.wav"], "dig": ["fs_dig_0.wav", "fs_dig_1.wav"], "drip": ["fs_drip_1.wav", "fs_drip_0.wav"],
}
TAKES = {k: [f for f in v if os.path.exists(os.path.join(F, f))] for k, v in TAKES.items()}
NAMES = sorted(k for k, v in TAKES.items() if v)
_cache = {}


def clip(name, take=0):
    files = TAKES[name]; f = files[take % len(files)]
    if f not in _cache:
        y, sr = sf.read(os.path.join(F, f), dtype="float32")
        if y.ndim > 1: y = y.mean(1)
        _cache[f] = y
    return _cache[f]


def play(mix, name, at, gain=0.5, pan=0.0, seconds=None, take=0, start=0.0, loop=False, fade=0.03, rate=44100):
    y = clip(name, take)[int(start * rate):]
    if seconds is not None:
        n = int(seconds * rate)
        if loop and len(y) < n: y = np.tile(y, n // max(1, len(y)) + 1)
        y = y[:n]
    y = y.copy(); k = min(len(y) // 2, max(1, int(fade * rate) if seconds is None else int(min(0.6, (seconds or 1) * 0.15) * rate)))
    y[:k] *= np.linspace(0, 1, k); y[-k:] *= np.linspace(1, 0, k)
    mix.add(y, at, gain, pan); return at + len(y) / rate
