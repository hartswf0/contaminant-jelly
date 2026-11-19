#!/usr/bin/env python3
"""voice_pass: give each hand film its voices, a piece of a song, and its number.

    python3 voice_pass.py            # every film in assets/films -> assets/voiced/pNN.mp4
    python3 voice_pass.py p03

The film's own captions are read aloud, each by its speaker: a narrator for the making, one voice for
Turkey and another for the trout (three stock Kokoro voices, run on this machine). A passage of one song from
DEEP SEA VOYAGE runs underneath and ducks under the voices; the film's own sound is kept. The porthole number
sits in the top right corner throughout. Captions and timings are read from the film's script, not retyped.
"""
import json, os, re, runpy, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "films")); sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import kit, voice as V
VOICES = {"narrator": ("bm_george", 0.92), "turkey": ("bm_fable", 0.95), "trout": ("bf_emma", 0.95)}
SONGS = {"p01": ("lake-merritt-clave", 22), "p03": ("the-prophet", 18), "p14": ("the-selkies-cradle", 30), "p35": ("gaslit-feerie", 14), "p44": ("ondes-in-the-abbey", 20)}
DEFAULT_SONG = ("descent-to-the-abyss", 20)
TIMES = {"p03": [(19.7, 24.3, "CAP2"), (28.9, 33.7, "CAP3")]}


def captions(pid):
    """Run the film's script with rendering switched off and read the captions it defines."""
    kit.Film.render = lambda self, *a, **k: None
    argv = sys.argv; sys.argv = ["x"]
    try:
        g = runpy.run_path("films/%s.py" % pid, run_name="__main__")
    finally:
        sys.argv = argv
    ok = lambda v: (isinstance(v, (list, tuple)) and v and all(isinstance(x, (list, tuple)) and len(x) >= 3 and isinstance(x[0], (int, float)) and
                                                       isinstance(x[1], (int, float)) and isinstance(x[-1], str) for x in v))
    if ok(g.get("CAPTIONS")):
        return sorted((float(x[0]), float(x[1]), x[-1]) for x in g["CAPTIONS"])
    if pid in TIMES:                                   # a film that keeps its captions as separate names: times are read off its script
        return [(a, b, g[name]) for a, b, name in TIMES[pid]]
    best = []
    for name, v in g.items():                          # otherwise the longest list of (start, end, sentence)
        if ok(v) and sum(len(x[-1]) for x in v) / len(v) > 15 and len(v) > len(best):
            best = [(float(x[0]), float(x[1]), x[-1]) for x in v]
    return sorted(best)


def speaker(text, t, dur):
    s = text.lower()
    if s.startswith("turkey"): return "turkey"
    if s.startswith("trout") or s.startswith("the trout"): return "trout"
    return "narrator" if t < dur * 0.42 else ("turkey" if t < dur * 0.72 else "trout")


def speak(text, who):
    voice, speed = VOICES[who]
    audio, sr = V.engine().create(text, voice=voice, speed=speed, lang="en-gb")
    tmp = tempfile.mktemp(suffix=".wav"); sf.write(tmp, audio, sr)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", tmp, "-af", "silenceremove=start_periods=1:start_threshold=-45dB", "-f", "f32le", "-ac", "1", "-ar", "44100", "-"], capture_output=True).stdout
    os.remove(tmp); return np.frombuffer(raw, np.float32)


def badge(n):
    im = Image.new("RGBA", (960, 540), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf", 58); s = "%02d" % n; w = d.textlength(s, font=f)
    d.rounded_rectangle((960 - w - 46, 16, 960 - 16, 92), 16, fill=(10, 16, 18, 205)); d.text((960 - w - 31, 16), s, font=f, fill=(255, 255, 255, 255))
    p = tempfile.mktemp(suffix=".png"); im.save(p); return p


def one(pid):
    src = "assets/films/%s.mp4" % pid
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
    caps = captions(pid); sr = 44100; y = np.zeros(int((dur + 1) * sr), np.float32); script = []
    for a, b, text in caps:
        who = speaker(text, a, dur); say = re.sub(r"^(turkey|trout|the trout)\s*:\s*", "", text, flags=re.I)
        clip = speak(say, who); i = int((a + 0.15) * sr); clip = clip[:max(0, len(y) - i)]; y[i:i + len(clip)] += clip
        script.append({"at": round(a, 2), "voice": VOICES[who][0], "speaker": who, "text": say, "seconds": round(len(clip) / sr, 2), "caption_held": round(b - a, 2)})
    vw = tempfile.mktemp(suffix=".wav"); sf.write(vw, y, sr)
    song, ss = SONGS.get(pid, DEFAULT_SONG)
    os.makedirs("assets/voiced", exist_ok=True); out = "assets/voiced/%s.mp4" % pid
    fc = ("[0:v][3:v]overlay,format=yuv420p[v];"
          "[1:a]aformat=channel_layouts=stereo,highpass=f=90,acompressor=threshold=-22dB:ratio=3:makeup=4,volume=1.5,asplit[nv][ns];"
          "[2:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.42,afade=t=in:d=1.5,afade=t=out:st=%.2f:d=2.5[sg];"
          "[sg][ns]sidechaincompress=threshold=0.02:ratio=9:attack=25:release=700[duck];"
          "[0:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.8[fa];"
          "[duck][nv][fa]amix=inputs=3:normalize=0,alimiter=limit=0.93[a]" % (dur - 2.5))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", vw, "-ss", str(ss), "-t", "%.2f" % dur, "-i", "../music/%s.ogg" % song, "-i", badge(int(pid[1:])),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
                    "-t", "%.2f" % dur, "-movflags", "+faststart", out], check=True)
    json.dump({"song": song, "song_from_seconds": ss, "lines": script}, open("films/notes/%s.voice.json" % pid, "w"), indent=1, ensure_ascii=False)
    over = [l for l in script if l["seconds"] > l["caption_held"] + 0.6]
    print(pid, "%d lines" % len(script), {l["speaker"] for l in script}, "song", song, ("| spoken longer than caption: %d" % len(over)) if over else "")


if __name__ == "__main__":
    for pid in (sys.argv[1:] or sorted(f[:-4] for f in os.listdir("assets/films") if f.endswith(".mp4") and f.startswith("p"))):
        one(pid)
