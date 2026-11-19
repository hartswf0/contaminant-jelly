#!/usr/bin/env python3
"""voice: the narrator. Every line a child would otherwise have to read is spoken.

A warm British storyteller voice (Kokoro "bm_george", a stock voice, run on this machine with kokoro-onnx),
slowed a little. Each sentence is made once and kept in narration/ as a small file, so rebuilding the film
costs nothing. The old-time-radio colour is added when the film is mixed, not baked into these files.
"""
import concurrent.futures as cf, hashlib, json, os, subprocess, time, urllib.request, urllib.error
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "narration")
VOICE, SPEED = "bm_george", 0.9
_mem = {}


def path(text):
    return os.path.join(DIR, hashlib.sha1((VOICE + "|" + text).encode()).hexdigest()[:16] + ".mp3")


MODEL = os.environ.get("KOKORO_DIR", "/root/kokoro")       # kokoro-v1.0.onnx and voices-v1.0.bin (kokoro-onnx model-files-v1.0 release)
_k = []
def engine():
    if not _k:
        from kokoro_onnx import Kokoro
        _k.append(Kokoro(os.path.join(MODEL, "kokoro-v1.0.onnx"), os.path.join(MODEL, "voices-v1.0.bin")))
    return _k[0]


def make(text):
    """Speak one sentence and keep it. Runs Kokoro on this machine; nothing is sent anywhere."""
    p = path(text)
    if os.path.exists(p):
        return p
    import soundfile as sf
    os.makedirs(DIR, exist_ok=True)
    audio, sr = engine().create(text, voice=VOICE, speed=SPEED, lang="en-gb")
    wav = p + ".wav"; sf.write(wav, audio, sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                    "-ac", "1", "-ar", "24000", "-b:a", "48k", p], check=True)
    os.remove(wav)
    return p


def prefetch(texts):
    todo = sorted(set(t for t in texts if not os.path.exists(path(t))))
    for t in todo:
        make(t)
    index = {}
    for t in set(texts):
        index[os.path.basename(path(t))] = t
    old = json.load(open(os.path.join(DIR, "index.json"))) if os.path.exists(os.path.join(DIR, "index.json")) else {}
    old.update(index); json.dump(dict(sorted(old.items())), open(os.path.join(DIR, "index.json"), "w"), indent=1, ensure_ascii=False)
    return len(todo)


def load(text, sr=44100):
    if text not in _mem:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", make(text), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
        _mem[text] = np.frombuffer(raw, np.float32)
    return _mem[text]


def seconds(text):
    return len(load(text)) / 44100.0


ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty"}
def number(n):
    return ONES[n] if n < 20 else TENS[n - n % 10] + ("-" + ONES[n % 10] if n % 10 else "")
