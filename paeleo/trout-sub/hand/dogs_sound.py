#!/usr/bin/env python3
"""dogs_sound: the real-recordings pass for The Dogs of Trouttown.

    python3 dogs_sound.py      # assets/films/dogs.mp4 -> assets/the-dogs-of-trouttown.mp4

The swarm's six sequences laid synthesized sound and almost none of the foraged recordings. This pass
keeps their mix underneath and lays real recordings over it (films/swarm/dogs/foley.py: CC0 from
Freesound, open licences from Wikimedia Commons), then brings the whole film up to web loudness.

Where each recording goes is read from the picture, not guessed: every half second the top of the frame
is measured. Dusk sky means the camera is above the water; teal means it is under. Above gets night air,
creek and frogs; under gets the underwater bed and bubbles; each crossing down gets a plunge and each
crossing up a splash and a shake. The howl, the ice and the bell are placed at the seconds the film
critics timed from stills. NOBODY HAS HEARD THIS MIX: it is placed by measurement and metered only.
"""
import subprocess, sys, os, json
import numpy as np, soundfile as sf
sys.path.insert(0, "films"); sys.path.insert(0, "films/swarm/dogs")
from kit import Mix, RATE
import foley

SRC, OUT, TMP = "assets/films/dogs.mp4", "assets/the-dogs-of-trouttown.mp4", "/tmp/dogs_sound"
os.makedirs(TMP, exist_ok=True)
SEC = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
STEP = 0.5


def above_track():
    """True where at least a third of the top band of the frame is dusk-sky purple."""
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", SRC, "-vf", "fps=2,crop=iw:ih/6:0:0,scale=32:6", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    a = np.frombuffer(raw, np.uint8).reshape(-1, 6 * 32, 3).astype(float)
    purple = (a[:, :, 2] > a[:, :, 1] * 1.15) & (a[:, :, 0] > a[:, :, 1] * 0.9)      # dusk sky: blue over green, red not far under
    return purple.mean(1) > 0.3


def runs(track):
    out = []; s = 0
    for i in range(1, len(track) + 1):
        if i == len(track) or track[i] != track[s]:
            out.append((bool(track[s]), s * STEP, i * STEP)); s = i
    # swallow flickers shorter than 1.5 s into their neighbours
    merged = []
    for r in out:
        if merged and (r[2] - r[1] < 1.5 or merged[-1][0] == r[0]): merged[-1] = (merged[-1][0], merged[-1][1], r[2])
        else: merged.append(r)
    return merged


if __name__ == "__main__":
    track = above_track(); R = runs(track); mix = Mix(SEC); k = 0
    for up, a, b in R:
        d = b - a
        if up:
            foley.play(mix, "night", a, gain=0.20, seconds=d, loop=True, take=k); foley.play(mix, "creek", a, gain=0.16, seconds=d, loop=True, take=k, pan=0.3)
            if d > 6: foley.play(mix, "frogs", a + 1.0, gain=0.10, seconds=d - 1.5, loop=True, take=k, pan=-0.4)
            if d > 5: foley.play(mix, "bell", a + 2.2, gain=0.30, pan=0.25)
            if d > 12: foley.play(mix, "moo", a + 7.0, gain=0.26, pan=0.5, take=k)
            if a > 1:                                        # came up through the surface
                foley.play(mix, "splash", a - 0.2, gain=0.50, take=k); foley.play(mix, "shake", a + 1.0, gain=0.40); foley.play(mix, "drip", a + 2.0, gain=0.22, seconds=min(3.0, d))
        else:
            foley.play(mix, "under", a, gain=0.30, seconds=d, loop=True, take=k); foley.play(mix, "bubbles", a + 0.6, gain=0.20, seconds=min(d - 0.6, 6.0))
            foley.play(mix, "plunge", a - 0.15, gain=0.55)
        k += 1
    # moments timed from stills by the film critics and the sequence contract
    for name, at, gain, kw in (("door", 6.5, 0.35, {}), ("radio", 12.5, 0.14, dict(seconds=6.0)), ("dig", 36.0, 0.40, {}), ("dig", 40.0, 0.38, dict(take=1)), ("paper", 51.5, 0.40, {}),
                               ("paper", 63.0, 0.36, dict(take=1)), ("calf", 76.0, 0.30, {}), ("pant", 80.0, 0.30, dict(seconds=3.0)), ("howl", 85.5, 0.60, {}),
                               ("bark", 90.5, 0.40, dict(pan=-0.6)), ("bark", 92.0, 0.36, dict(take=1, pan=0.6)), ("bark", 94.0, 0.34, dict(take=2)), ("dig", 104.0, 0.30, {}), ("dig", 108.0, 0.30, dict(take=1, pan=0.4)),
                               ("ice", 117.0, 0.55, {}), ("ice", 124.0, 0.60, dict(take=1)), ("pant", 131.0, 0.34, dict(seconds=5.0, take=1)), ("moo", 135.0, 0.30, dict(take=2)),
                               ("sigh", 151.0, 0.45, {}), ("whine", 152.5, 0.30, {}), ("bell", 174.0, 0.34, {})):
        if at < SEC - 1: foley.play(mix, name, at, gain=gain, **kw)
    lay = np.stack([mix.L, mix.R], 1); lay = np.tanh(lay * 1.2) / 1.2
    sf.write(TMP + "/foley.wav", lay.astype(np.float32), RATE)
    # the swarm's own mix stays underneath; then one loudness pass to -16 LUFS, true peak -1.5
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-i", TMP + "/foley.wav", "-filter_complex",
                    "[0:a]volume=1.0[a];[1:a]volume=0.9[b];[a][b]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-2.5:LRA=11[o]",
                    "-map", "0:v", "-map", "[o]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", OUT], check=True)
    json.dump([dict(above=u, start=a, end=b) for u, a, b in R], open(TMP + "/runs.json", "w"))
    print(OUT, round(SEC, 1), "s;", len(R), "stretches;", sum(1 for u, _, _ in R if u), "above water")
    for u, a, b in R: print("  %6.1f %6.1f %s" % (a, b, "above" if u else "under"))
