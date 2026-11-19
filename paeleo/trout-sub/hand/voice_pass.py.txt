#!/usr/bin/env python3
"""voice_pass: give each hand film its voices, a piece of a song, and its number.

    python3 voice_pass.py            # every film in assets/films -> assets/voiced/pNN.mp4
    python3 voice_pass.py p03

Each caption is spoken by its speaker: a narrator for the making, one voice for Turkey and another for the
trout (three stock American Kokoro voices, slowed and pitched per character, run on this machine), saying
the caption's two readings in a river-country idiom (LINES). A passage of one song from
DEEP SEA VOYAGE runs underneath and ducks under the voices; the film's own sound is kept. The porthole number
sits in the top right corner throughout. Captions and timings are read from the film's script, not retyped.
"""
import json, os, re, runpy, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "films")); sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import kit, voice as V
# American voices, slowed to a drawl and pitched per character: voice, speed, pitch shift in semitones.
VOICES = {"narrator": ("am_michael", 0.95, -1.0), "turkey": ("am_santa", 0.84, -2.5), "trout": ("af_bella", 0.96, 2.5)}
# What each voice SAYS, written in a Tennessee-river idiom. Same two readings as the caption on screen, in the same order.
LINES = {
 "p01": ["Now, this here is a rubber boot, cut clean out of an old poster.",
         "Well, I'll be. Is that a shipwreck? A giant's foot? Or some kinda tunnel?",
         "Lord have mercy! Is that boot sole a flashlight? Or is a crab a-bitin' its toe?"],
 "p03": ["Hoo-wee. Mister Hook, the famous guest speaker? Or... the Monster. Most wanted.",
         "Okay, mister. Are you our new class pet? Or are you the Hook Monster?"],
 "p14": ["Now, is that a spark, gone under the water?", "Oh, no. Or is that the calendar, tickin' on down to Thanksgivin'?",
         "Looky there! A feather, fell clean outta the sky?", "Or a flare. Is somebody up yonder in trouble?"],
 "p35": ["Prints from the Farm Security file.", "Box forty-four. Blue paper, cut on a pencil line.",
         "The river is green gel. The mail bag goes in last.",
         "Are those my lost mission orders? Or is that just a sack of dirty laundry?",
         "Well, shoot! A porch pirate with a vacuum? Or the mailman's truck, here at long last?"],
 "p44": ["Is that a turbine, drinkin' the whole river down a whirlpool?", "Or a trap that hypnotizes. And I am a-starin' right at it?",
         "That's the pie-prize wheel from the diner! Who wins the slice?", "Or a washin' machine. And whose sock is that?"],
}
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
    import librosa
    voice, speed, semis = VOICES[who]
    audio, sr = V.engine().create(text, voice=voice, speed=speed, lang="en-us")
    if semis:
        audio = librosa.effects.pitch_shift(audio.astype(np.float32), sr=sr, n_steps=semis)
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
    spoken = LINES.get(pid)
    if spoken and len(spoken) != len(caps):
        print(pid, "spoken lines do not match the %d captions; reading the captions" % len(caps)); spoken = None
    pops = []
    for q, (a, b, text) in enumerate(caps):
        who = speaker(text, a, dur); say = spoken[q] if spoken else re.sub(r"^(turkey|trout|the trout)\s*:\s*", "", text, flags=re.I)
        pops.append((a, who))
        clip = speak(say, who)
        room = (caps[q + 1][0] if q + 1 < len(caps) else dur) - a - 0.35        # never run into the next speaker
        if len(clip) / sr > room:
            import librosa
            clip = librosa.effects.time_stretch(clip, rate=min(1.35, len(clip) / sr / max(0.5, room)))
        i = int((a + 0.15) * sr); clip = clip[:max(0, len(y) - i)]; y[i:i + len(clip)] += clip
        script.append({"at": round(a, 2), "voice": VOICES[who][0], "speaker": who, "text": say, "caption": text, "seconds": round(len(clip) / sr, 2), "caption_held": round(b - a, 2)})
    # a small cue before each line: a low gobble-knock for Turkey, a bright bubble for the trout, a paper tick for the narrator
    fx = np.zeros_like(y)
    for a, who in pops:
        n = int(0.16 * sr); t = np.arange(n) / float(sr)
        if who == "trout":
            cue = np.sin(2 * np.pi * (700 + 2600 * t / 0.16) * t) * np.exp(-t * 26) * 0.35
        elif who == "turkey":
            cue = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 34) * 0.55 + np.sin(2 * np.pi * 300 * t) * np.exp(-t * 50) * 0.2
        else:
            cue = np.random.RandomState(int(a * 100)).randn(n) * np.exp(-t * 90) * 0.25
        i = max(0, int((a + 0.02) * sr)); fx[i:i + n] += cue[:len(fx) - i].astype(np.float32)
    vw = tempfile.mktemp(suffix=".wav"); sf.write(vw, y, sr)
    fw = tempfile.mktemp(suffix=".wav"); sf.write(fw, fx, sr)
    song, ss = SONGS.get(pid, DEFAULT_SONG)
    os.makedirs("assets/voiced", exist_ok=True); out = "assets/voiced/%s.mp4" % pid
    fc = ("[0:v][3:v]overlay,format=yuv420p[v];"
          # voice: clear of rumble, a lift where consonants live, firm compression
          "[1:a]aformat=channel_layouts=stereo,highpass=f=110,equalizer=f=3200:t=q:w=1.1:g=4.5,equalizer=f=280:t=q:w=1:g=-2.5,"
          "acompressor=threshold=-24dB:ratio=4:attack=4:release=90:makeup=6,volume=1.45,asplit[nv][ns];"
          # music: thinned in the mud so it never sits on the voice, then ducked hard under speech
          "[2:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=120,equalizer=f=350:t=q:w=1:g=-4,volume=0.4,afade=t=in:d=1.2,afade=t=out:st=%.2f:d=2.5[sg];"
          "[sg][ns]sidechaincompress=threshold=0.015:ratio=12:attack=15:release=450[duck];"
          # the film's own foley: brighter and a little louder, so cuts, chalk and scissors are crisp
          "[0:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=70,equalizer=f=6500:t=q:w=1.2:g=4,volume=1.05[fa];"
          "[4:a]aformat=channel_layouts=stereo[cue];"
          "[duck][nv][fa][cue]amix=inputs=4:normalize=0,alimiter=limit=0.93[a]" % (dur - 2.5))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", vw, "-ss", str(ss), "-t", "%.2f" % dur, "-i", "../music/%s.ogg" % song, "-i", badge(int(pid[1:])), "-i", fw,
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-c:a", "aac", "-b:a", "192k",
                    "-t", "%.2f" % dur, "-movflags", "+faststart", out], check=True)
    json.dump({"song": song, "song_from_seconds": ss, "lines": script}, open("films/notes/%s.voice.json" % pid, "w"), indent=1, ensure_ascii=False)
    over = [l for l in script if l["seconds"] > l["caption_held"] + 0.6]
    print(pid, "%d lines" % len(script), {l["speaker"] for l in script}, "song", song, ("| spoken longer than caption: %d" % len(over)) if over else "")


if __name__ == "__main__":
    for pid in (sys.argv[1:] or sorted(f[:-4] for f in os.listdir("assets/films") if f.endswith(".mp4") and f.startswith("p"))):
        one(pid)
