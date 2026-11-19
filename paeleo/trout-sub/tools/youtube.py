#!/usr/bin/env python3
"""youtube: the one film for the whole exercise, made to sit beside the
Porthole Log (tools/sheet.py), the worksheet redrawn in the film's own symbols.

    python3 tools/youtube.py           # youtube/tourkey-trouttown.mp4, chapters.txt, slips.html, timing.json
    python3 tools/youtube.py --slips   # reprint the slips from the last build's timings

Rules of the cut
- The picture fills the screen. On it there are only three things: the slip number, a
  minimap of the river showing where this porthole is, and the choices.
- The choices are controller buttons: green triangle and red circle for Turkey (right of
  the glass), blue cross and pink square for the trout (left of it). Students pick one
  and draw the shape. Only the side whose shot is playing is shown, and its choices are
  lit one at a time, then together, so each line is read on its own.
- Written for fourth graders who need more time: Turkey's shot holds about 7 seconds and
  the trout's about 7 seconds, words are few, large and in sentence case, nothing blinks.
- Four dives of 16, 16, 16 and 7 portholes. Each half of a dive has its own song from
  DEEP SEA VOYAGE, and portholes change on that song's tracked beats.
- A narrator reads every line aloud (tools/voice.py), through an old wireless set; the music ducks
  under him, and each choice lights as he begins to say it.
- Sound: the music leads between lines; each film's own sound sits low under it; and a soft mallet note marks
  every line as it lights, a different pitch for each button, so choices can be told by ear.
  Every light lands on a beat.
- The change between portholes goes through the porthole: the next film opens from the
  glass outward while the rim, which the units lock, holds still.
No fal call is made here.
"""
import json, math, os, re, subprocess, sys, tempfile, warnings
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import units as U
import cards as C
import voice as V

W, H, FPS = 1280, 720, 24
BX, BY, BW, BH = 0, 0, W, H                     # the film fills the frame
TRANS = 0.6                                     # seconds of the through-the-porthole change
MAX_MB = 95                                     # the finished file is held under this
font = C.font
seeds = json.load(open("seeds.json"))
units = json.load(open("units.json")) if os.path.exists("units.json") else {}
# dive: (name, first, last, [(song file, title, beats per porthole, how many portholes), ...])
DIVES = [("Dive 1", 1, 16, [("music/lake-merritt-clave.ogg", "Lake Merritt Clave", 32, 8), ("music/cyborg-gospel.ogg", "Cyborg Gospel", 28, 8)]),
         ("Dive 2", 17, 32, [("music/submersible-propulsion.ogg", "Submersible Propulsion", 32, 8), ("music/whales-belly-escape.ogg", "Whale's Belly Escape", 36, 8)]),
         ("Dive 3", 33, 48, [("music/ondes-in-the-abbey.ogg", "Ondes In The Abbey", 24, 8), ("music/the-selkies-cradle.ogg", "The Selkie's Cradle", 24, 8)]),
         ("Dive 4", 49, 55, [("music/the-verne-bench.ogg", "The Verne Bench", 36, 7)])]
HOWTO_SONG, CLOSE_SONG = ("music/descent-to-the-abyss.ogg", "Descent to the Abyss"), ("music/the-hull-breaks-surface.ogg", "The Hull Breaks Surface")


def options(question):
    """'Shipwreck, giant's foot, or tunnel?' -> ['Shipwreck', "Giant's foot", 'Tunnel']"""
    q = question.strip().rstrip("?")
    parts = [x.strip() for x in re.split(r",\s*or\s+|,\s*|\s+or\s+", q) if x.strip()]
    return [x[0].upper() + x[1:] for x in parts]


def choices(n):
    """All the choices of a porthole with their shapes: Turkey's first, then the trout's."""
    row = seeds[n - 1]; t, r = options(row[3]), options(row[4])
    shapes = ["triangle", "circle", "hexagon"][:len(t)] + ["cross", "square", "hexagon"][:len(r)]
    return [(shapes[i], w, "turkey") for i, w in enumerate(t)] + [(shapes[len(t) + i], w, "trout") for i, w in enumerate(r)]


def wrap(d, text, f, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    return out + [cur]


RIM = U.CANON_R * W                              # outer rim radius of the locked porthole, in pixels
def side_panel(items, side, lit=None):
    """One side's buttons: Turkey's sit right of the glass, the trout's left of it. Each choice is a
    plate with its controller button and an edge in the button's colour. lit = index of the one
    choice being read now (the others wait, dimmed); None = all lit."""
    pw = int(W / 2 - RIM - 20)
    im = Image.new("RGBA", (pw, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    size = 35; tx = 96
    while size > 24 and any(len(wrap(d, w, font(size, "Bold"), pw - tx - 12)) > 3 or
                            max(d.textlength(x, font=font(size, "Bold")) for x in w.split()) > pw - tx - 12 for _, w, _ in items):
        size -= 1
    blocks = [wrap(d, w, font(size, "Bold"), pw - tx - 12) for _, w, _ in items]
    heights = [max(86, len(b) * (size + 7) + 28) for b in blocks]
    total = sum(heights) + 16 * (len(items) - 1) + 50
    y = (H - total) // 2 - 30
    tag = "Turkey thinks" if side == "turkey" else "The trout think"
    d.rounded_rectangle((0, y, d.textlength(tag, font=font(25, "Bold")) + 28, y + 40), 12, fill=(8, 10, 14, 215))
    d.text((14, y + 4), tag, font=font(25, "Bold"), fill=(255, 255, 255, 255)); y += 50
    for i, ((kind, word, _), lines, hgt) in enumerate(zip(items, blocks, heights)):
        on = lit is None or lit == i
        col = C.SHAPE_COL[kind]
        d.rounded_rectangle((0, y, pw - 2, y + hgt), 20, fill=(8, 10, 14, 225 if on else 150))
        d.rounded_rectangle((0, y, pw - 2, y + hgt), 20, outline=col + (255 if on else 90,), width=4 if on else 2)
        C.button(d, 48, y + hgt / 2, 32, kind, on=on)
        ty = y + (hgt - len(lines) * (size + 7)) / 2 - 2
        for l in lines:
            d.text((tx, ty), l, font=font(size, "Bold"), fill=(255, 255, 255, 255 if on else 130)); ty += size + 7
        y += hgt + 16
    a = np.array(im).astype(np.float32)
    x = int(W / 2 + RIM + 10) if side == "turkey" else int(W / 2 - RIM - 10 - pw)
    return x, 0, a[:, :, 2::-1].copy(), a[:, :, 3:4] / 255.0


def reading(m, count, i):
    """Which choice is being read at frame i of a side's m frames: each in turn, then all together."""
    part = 0.8 / count
    k = int((i / float(m)) / part)
    return k if k < count else None


def river(n_total=55):
    """Where each porthole sits on the minimap: a river winding down a round map."""
    pts = []
    for k in range(n_total):
        u = (k + 0.5) / n_total
        y = -0.82 + 1.64 * u
        half = math.sqrt(max(0.0, 0.86 ** 2 - y * y))
        pts.append((half * 0.9 * math.sin(u * math.pi * 7.0), y))
    return pts
RIVER = river()


def hud(n):
    """The slip number, top right, and the minimap, bottom left. Nothing else."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    s = "%02d" % n; f = font(92, "Black"); tw = d.textlength(s, font=f)
    d.rounded_rectangle((W - tw - 62, 22, W - 22, 132), 22, fill=(10, 16, 18, 200))
    d.text((W - tw - 42, 20), s, font=f, fill=(255, 255, 255, 255))
    cx, cy, r = 112, H - 112, 84
    d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), fill=(10, 16, 18, 215), outline=(255, 255, 255, 190), width=3)
    path = [(cx + x * r, cy + y * r) for x, y in RIVER]
    d.line(path, fill=(72, 160, 150, 150), width=7, joint="curve")
    for k, (x, y) in enumerate(path):
        if k + 1 < n:
            d.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=(255, 255, 255, 120))
        elif k + 1 > n:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(255, 255, 255, 60))
    x, y = path[n - 1]
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(240, 178, 90, 255), outline=(10, 16, 18, 255), width=3)
    a = np.array(im).astype(np.float32)
    regs = []
    for (x0, y0, x1, y1) in ((W - 300, 0, W, 150), (0, H - 270, 330, H)):
        regs.append((x0, y0, a[y0:y1, x0:x1, 2::-1].copy(), a[y0:y1, x0:x1, 3:4] / 255.0))
    return regs


BOLT_R = 0.925        # bolt circle radius / outer rim radius, on the locked porthole
def bolt_dice(side):
    """A die face on each of the six bolts, as on the worksheet's ring. Clockwise from the top:
    1, 2, 3 down the right (the first friend's bolts, Turkey's side), 4, 5, 6 up the left (the next
    friend's, the trout's side). The three that belong to the shot on screen are lit."""
    pad = int(RIM + 40); im = Image.new("RGBA", (2 * pad, 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(6):
        ang = math.radians(-90 + 60 * k)
        on = (k < 3) == (side == "turkey")
        C.die_face(d, pad + RIM * BOLT_R * math.cos(ang), pad + RIM * BOLT_R * math.sin(ang), 46 if on else 38, k + 1, on)
    a = np.array(im).astype(np.float32)
    return int(W / 2 - pad), int(H / 2 - pad), a[:, :, 2::-1].copy(), a[:, :, 3:4] / 255.0


def stamp_on(frame, reg, fade=1.0):
    x, y, rgb, al = reg
    if y < 0:                                  # the ring of dice is taller than the frame: trim it
        rgb, al, y = rgb[-y:], al[-y:], 0
    if y + rgb.shape[0] > H:
        rgb, al = rgb[:H - y], al[:H - y]
    return _stamp(frame, (x, y, rgb, al), fade)


def _stamp(frame, reg, fade=1.0):
    x, y, rgb, al = reg
    h, w = rgb.shape[:2]
    frame[y:y + h, x:x + w] = frame[y:y + h, x:x + w] * (1 - al * fade) + rgb * (al * fade)


yy, xx = np.mgrid[:H, :W]
DIST = np.hypot(xx - W / 2.0, yy - H / 2.0)
R0, R1 = RIM * U.GLASS, np.hypot(W, H) / 2 + 8
def through(a, b, u):
    """The next film opens from the glass outward. u runs 0..1."""
    e = u * u * (3 - 2 * u)
    r = R0 * 0.2 + (R1 - R0 * 0.2) * e
    m = np.clip((r - DIST) / 10.0 + 0.5, 0, 1)[..., None]
    return a * (1 - m) + b * m


def beats(path):
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    _, b = librosa.beat.beat_track(y=y, sr=sr)
    t = librosa.frames_to_time(b, sr=sr)
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    return t, rms, sr, len(y) / sr


def pick_start(bt, rms, sr, need_beats, dur):
    """Start on the beat whose following stretch is loudest on average, leaving the song's tail alone."""
    best, bi = -1, 0
    for i in range(0, len(bt) - need_beats - 1):
        if bt[i + need_beats] > dur - 1.5:
            break
        a, b = int(bt[i] * sr / 512), int(bt[i + need_beats] * sr / 512)
        v = float(rms[a:b].mean())
        if v > best:
            best, bi = v, i
    return bi


class Out:
    """Frames in. A lightly compressed master is written first, then the finished file is
    encoded in two passes to a size that stays under MAX_MB, with the music mixed in."""
    def __init__(self):
        self.tmp = tempfile.mkdtemp(); self.path = self.tmp + "/master.mp4"; self.n = 0; self.music = []; self.cues = []; self.said = []; self.tunes = []
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", self.path], stdin=subprocess.PIPE)
    def add(self, frame):
        self.p.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes()); self.n += 1
    @property
    def t(self):
        return self.n / float(FPS)
    def song(self, path, start_in_song, at, length, gain=1.0, fade=1.2):
        self.music.append((path, start_in_song, at, length, gain, fade))
    def cue(self, at, kind):
        """A soft mallet note when a line is lit. Each button has its own pitch, so a choice can be
        told by ear as well as by shape and colour."""
        self.cues.append((at, kind))
    def say(self, at, text, tempo=1.0):
        """The narrator speaks this line at this time. Returns how long it takes."""
        self.said.append((at, text, tempo)); return V.seconds(text) / tempo
    def tune(self, at):
        """The wireless is tuned to a new station: a burst of static and a falling whistle."""
        self.tunes.append(at)
    def voice_track(self):
        import librosa, soundfile as sf
        sr = 44100; y = np.zeros(int((self.t + 2) * sr), np.float32)
        for at, text, tempo in self.said:
            a = V.load(text)
            if tempo > 1.02:
                a = librosa.effects.time_stretch(a, rate=tempo)
            i = int(at * sr); a = a[:max(0, len(y) - i)]; y[i:i + len(a)] += a
        rng = np.random.RandomState(7)                       # a little wireless hiss and the odd crackle
        hiss = rng.randn(len(y)).astype(np.float32); hiss = np.convolve(hiss, np.ones(8) / 8.0, "same") * 0.006
        clicks = np.zeros(len(y), np.float32); idx = rng.randint(0, len(y), int(self.t * 1.5)); clicks[idx] = rng.uniform(-0.05, 0.05, len(idx))
        for at in self.tunes:
            n = int(0.6 * sr); t = np.arange(n) / float(sr); env = np.sin(np.pi * t / 0.6) ** 1.5
            f = 2600 * np.exp(-t * 3.2) + 420                         # the whistle slides down as the dial turns
            whistle = np.sin(2 * np.pi * np.cumsum(f) / sr) * 0.05
            static = rng.randn(n) * 0.11 * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
            i = max(0, int((at - 0.2) * sr)); seg = ((whistle + static) * env).astype(np.float32)[:max(0, len(clicks) - i)]
            clicks[i:i + len(seg)] += seg
        path = self.tmp + "/voice.wav"; sf.write(path, y, sr)
        path2 = self.tmp + "/air.wav"; sf.write(path2, hiss + clicks, sr)
        return path, path2
    def cue_track(self):
        sr = 44100; y = np.zeros(int((self.t + 1) * sr), np.float32)
        note = {"triangle": 659.3, "circle": 784.0, "cross": 523.3, "square": 587.3, "hexagon": 880.0, "all": 1046.5, "line": 392.0}
        for at, kind in self.cues:
            n = int(0.5 * sr); t = np.arange(n) / float(sr); f = note[kind]
            tone = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 4 * f * t)) * np.exp(-t * 9.0)
            tone[:int(0.004 * sr)] *= np.linspace(0, 1, int(0.004 * sr))
            i = int(at * sr); y[i:i + n] += (0.10 if kind != "line" else 0.07) * tone[:len(y) - i].astype(np.float32)
        import soundfile as sf
        path = self.tmp + "/cues.wav"; sf.write(path, np.stack([y, y], 1), sr); return path
    def close(self, dest):
        self.p.stdin.close(); self.p.wait()
        ins, fc, mix = ["-i", self.path], [], []
        for i, (path, ss, at, length, gain, fade) in enumerate(self.music, 1):
            ins += ["-ss", "%.3f" % ss, "-t", "%.3f" % length, "-i", path]
            fc.append("[%d:a]aresample=44100,aformat=channel_layouts=stereo,volume=%.3f,afade=t=in:d=0.3,afade=t=out:st=%.3f:d=%.2f,adelay=%d:all=1[m%d]"
                      % (i, gain, max(0, length - fade), fade, int(at * 1000), i))
            mix.append("[m%d]" % i)
        fc.append("%samix=inputs=%d:normalize=0[mus]" % ("".join(mix), len(mix)))
        last = ["[mus]"]; k = len(self.music)
        if self.said:                                    # the narrator, through an old wireless set; music ducks under him
            vp, ap = self.voice_track(); ins += ["-i", vp, "-i", ap]
            fc.append("[%d:a]aformat=channel_layouts=stereo,highpass=f=170,lowpass=f=4300,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=5,"
                      "aecho=0.8:0.25:18:0.12,volume=1.7,asplit[nv][ns]" % (k + 1))
            fc.append("[%d:a]aformat=channel_layouts=stereo,highpass=f=300,lowpass=f=5000[air]" % (k + 2))
            fc.append("[mus][ns]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=600[duck]")
            last = ["[duck]", "[nv]", "[air]"]; k += 2
        if self.cues:
            ins += ["-i", self.cue_track()]; k += 1
            fc.append("[%d:a]aresample=44100,aformat=channel_layouts=stereo[cu]" % k); last.append("[cu]")
        fc.append("%samix=inputs=%d:normalize=0,alimiter=limit=0.92,apad[a]" % ("".join(last), len(last)))
        kbps = int(min(2600, MAX_MB * 8192.0 / self.t - 136))
        v = ["-c:v", "libx264", "-preset", "medium", "-b:v", "%dk" % kbps, "-pix_fmt", "yuv420p", "-g", "48"]
        log = self.tmp + "/pass"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", self.path] + v + ["-pass", "1", "-passlogfile", log, "-an", "-f", "null", "-"], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]"] + v +
                       ["-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", "128k", "-t", "%.3f" % self.t, "-movflags", "+faststart", dest], check=True)
        os.remove(self.path)
        return kbps


def film_frames(src, ss, n, w=W, h=H):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", src, "-vf", "fps=%d,scale=%d:%d:flags=lanczos" % (FPS, w, h),
                          "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)]) if len(a) < n else a


def card_say(text):
    return re.sub(r"^(\d)\. ", lambda m: ["", "One. ", "Two. ", "Three. "][int(m.group(1))], text)


def narrate_card(out, spec):
    out.say(out.t + 0.35, spec["title"] + ".")
    for q, (_, line) in enumerate(spec["lights"]):
        at = out.t + C.CARD_LEAD + C.LINE_SECONDS * q
        out.cue(at, "line"); out.say(at + 0.25, card_say(line))


def all_lines():
    """Every sentence the film speaks, so they can be made before rendering starts."""
    out = ["Tour-key Trout Town.", "Find the number on your slip. That is your porthole.", "See four choices.", "Pick one. Draw its shape.",
           "Triangle. Circle. Cross. Square.", "The trout think."]
    for spec in C.CARDS:
        out += [spec["title"] + "."] + [card_say(l) for _, l in spec["lights"]]
    for name, a, b, _ in DIVES:
        out.append("%s. Slips %s to %s." % (name.replace("1", "one").replace("2", "two").replace("3", "three").replace("4", "four"), V.number(a), V.number(b)))
    for pid in range(1, 56):
        ch = choices(pid)
        out += spoken(pid, "turkey", [c for c in ch if c[2] == "turkey"]) + spoken(pid, "trout", [c for c in ch if c[2] == "trout"])
    return out


def opening(out):
    """Title, one card per command on the worksheet, then how the buttons work."""
    t0 = out.t
    out.say(t0 + 3.2, "Tour-key Trout Town."); out.say(t0 + 7.0, "Find the number on your slip. That is your porthole.")
    for f in C.title(film_frames("films/intro-6.mp4", 2.4, int(5.6 * FPS), 1136, 639)):
        out.add(f)
    for k, spec in enumerate(C.CARDS):
        n = int(C.card_seconds(spec) * FPS)
        narrate_card(out, spec)
        for f in C.card(spec, film_frames(spec["film"][0], spec["film"][1], n, 640, 360), n, first=(k == 0)):
            out.add(f)
    out.say(out.t + 0.3, "See four choices."); out.say(out.t + 2.0, "Pick one. Draw its shape."); out.say(out.t + 5.0, "Triangle. Circle. Cross. Square.")
    for f in C.choose_card(int(9.0 * FPS)):
        out.add(f)
    bt, rms, sr, dur = beats(HOWTO_SONG[0])
    out.song(HOWTO_SONG[0], float(bt[min(8, len(bt) - 1)]), t0, min(out.t - t0 + 0.4, dur - 1))


def closing(out):
    """The last two commands again, for the moment the logs come back."""
    t0 = out.t
    for spec in C.CARDS[6:]:
        n = int(C.card_seconds(spec) * FPS)
        narrate_card(out, spec)
        for f in C.card(spec, film_frames(spec["film"][0], spec["film"][1], n, 640, 360), n, first=False):
            out.add(f)
    bt, rms, sr, dur = beats(CLOSE_SONG[0])
    out.song(CLOSE_SONG[0], float(bt[min(8, len(bt) - 1)]), t0, min(out.t - t0 + 0.4, dur - 1))


SHAPE_WORD = {"triangle": "Triangle", "circle": "Circle", "cross": "Cross", "square": "Square", "hexagon": "Hexagon"}
def spoken(pid, side, items):
    """What the narrator says for one side of a porthole: who is thinking, then each button and its choice."""
    first = ("%s. Turkey thinks." % V.number(pid).capitalize()) if side == "turkey" else "The trout think."
    return [first] + ["%s. %s." % (SHAPE_WORD[k], w) for k, w, _ in items]


def play_porthole(out, pid, frames_n, half_n, lights, prev_tail, times, first=False):
    """One porthole: Turkey's shot for half_n frames, then the trout's. lights = for each side the
    frame offsets (from that side's start) at which its choices light in turn, the last one being
    'all together'; these are beat positions, so every light lands on the music."""
    nt = int(TRANS * FPS)
    one, _ = U.frames("units/p%02d.mp4" % pid, 192, W, H)
    u_ = units.get("p%02d" % pid) or {}
    cut = u_.get("cut") if u_.get("lock_end") and u_.get("cut") else U.LEN - 0.9
    cut_f = min(180, max(24, int(cut / U.LEN * 192)))
    # Turkey's shot fills the first half. The trout's shot is short, so it plays forward, back and
    # forward again to fill the second half, ending on its locked last frame.
    seq_t = np.linspace(0, cut_f - 1, half_n).round().astype(int)
    seg = list(range(cut_f, 192)); pp = seg + seg[::-1] + seg
    seq_r = np.array(pp)[np.linspace(0, len(pp) - 1, frames_n - half_n).round().astype(int)]
    order = np.concatenate([seq_t, seq_r])
    ch = choices(pid)
    sides = {"turkey": [c for c in ch if c[2] == "turkey"], "trout": [c for c in ch if c[2] == "trout"]}
    panels = {(s_, k): side_panel(items, s_, k) for s_, items in sides.items() for k in list(range(len(items))) + [None]}
    regs = hud(pid); dice = {"turkey": bolt_dice("turkey"), "trout": bolt_dice("trout")}
    times[pid] = out.t
    out.tune(out.t)
    out.song("units/p%02d.mp4" % pid, 0.0, out.t, min(U.LEN, frames_n / float(FPS)), gain=0.2, fade=0.8)     # the film's own sound, low
    # The narrator reads every line, and each choice lights as he begins to say it.
    lights = {}
    for side, n_side, lead_in in (("turkey", half_n, TRANS + 0.1), ("trout", frames_n - half_n, 0.3)):
        lines_ = spoken(pid, side, sides[side])
        total = sum(V.seconds(x) for x in lines_) + 0.18 * (len(lines_) - 1)
        tempo = min(1.4, max(1.0, total / max(1.0, n_side / float(FPS) - lead_in - 0.25)))
        t = lead_in; base = out.t + (0 if side == "turkey" else half_n / float(FPS)); marks = []
        for q, line in enumerate(lines_):
            if q > 0:
                marks.append(int(round(t * FPS)))
            t += out.say(base + t, line, tempo) + 0.18 / tempo
        marks.append(min(n_side - 2, int(round(t * FPS))))
        lights[side] = marks
    for i in range(frames_n):
        frame = one[order[i]].astype(np.float32)
        side, local = ("turkey", i) if i < half_n else ("trout", i - half_n)
        marks = lights[side]; count = len(sides[side])
        k = sum(1 for m in marks if local >= m) - 1                 # which light is on: -1 none yet
        for q, m in enumerate(marks):
            if local == m:
                out.cue(out.t, sides[side][q][0] if q < count else "all")
        stamp_on(frame, dice[side])
        if k >= 0:
            fade = min(1.0, (local - marks[0] + 1) / 6.0)
            stamp_on(frame, panels[(side, k if k < count else None)], fade)
        for reg in regs:
            stamp_on(frame, reg)
        if i < nt and first:                          # out of a card: the bars clear to the first porthole
            u = (i + 1) / float(nt)
            frame = C.bgr(C.bars(Image.fromarray(frame.astype(np.uint8)[:, :, ::-1]), 0.5 + 0.5 * u)).astype(np.float32)
        elif i < nt and prev_tail is not None:
            frame = through(prev_tail, frame, (i + 1) / float(nt))
        out.add(frame)
    return one[-1].astype(np.float32)


def light_marks(F, b0, step, n_t, n_r):
    """Beat-timed marks for one porthole. F(b) = frame offset of beat b from the porthole's start.
    Each side has step/2 beats: the first choice lights on its 2nd beat, the rest are spread evenly
    over the first two thirds, and 'all together' follows."""
    half = step // 2
    def side(first_beat, count):
        span_b = max(count + 1, int(half * 0.7))
        return [F(first_beat + 1 + int(round(q * (span_b - 1) / float(count)))) for q in range(count + 1)]
    t = side(0, n_t); r0 = F(half)
    r = [m - r0 for m in side(half, n_r)]
    return {"turkey": t, "trout": r}, r0


def dive(out, spec, times):
    name, a, b, halves = spec
    t_dive = out.t
    pid = a; prev_tail = None
    for h, (path, title, step, count) in enumerate(halves):
        bt, rms, sr, dur = beats(path)
        lead = 8 if h == 0 else 0                           # beats under the dive card
        i0 = pick_start(bt, rms, sr, lead + step * count, dur)
        T = lambda k: float(bt[min(i0 + k, len(bt) - 1)] - bt[i0])
        t0 = out.t
        if h == 0:
            out.say(out.t + 0.3, "%s. Slips %s to %s." % (name.replace("1", "one").replace("2", "two").replace("3", "three").replace("4", "four"), V.number(a), V.number(b)))
            for card in C.dive_card(name, a, b, " and ".join(x[1] for x in halves), int(round(T(lead) * FPS))):
                out.add(card)
            prev_tail = None
        for j in range(count):
            start_n = out.n
            F = lambda bb: int(round((t0 + T(lead + step * j + bb)) * FPS)) - start_n
            frames_n = F(step)
            ch = choices(pid)
            marks, half_n = light_marks(F, 0, step, sum(1 for c in ch if c[2] == "turkey"), sum(1 for c in ch if c[2] == "trout"))
            prev_tail = play_porthole(out, pid, frames_n, half_n, marks, prev_tail, times, first=(prev_tail is None))
            pid += 1
        out.song(path, float(bt[i0]), t0, out.t - t0 + 0.7)
    return t_dive


def stamp(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def die(n):
    """A die face drawn as SVG, in the worksheet's gold-edged square."""
    pips = {1: [(12, 12)], 2: [(7, 7), (17, 17)], 3: [(7, 7), (12, 12), (17, 17)], 4: [(7, 7), (17, 7), (7, 17), (17, 17)],
            5: [(7, 7), (17, 7), (12, 12), (7, 17), (17, 17)], 6: [(7, 6), (17, 6), (7, 12), (17, 12), (7, 18), (17, 18)]}[n]
    return ('<svg class="die" viewBox="0 0 24 24"><rect x="1.5" y="1.5" width="21" height="21" rx="4" fill="#fbf6e9" stroke="#8a5a12" stroke-width="1.6"/>%s</svg>'
            % "".join('<circle cx="%d" cy="%d" r="2" fill="#16293a"/>' % p for p in pips))


SNAIL = ('<svg class="snail" viewBox="0 0 28 20"><path d="M3 16h20c2 0 3-2 3-4" fill="none" stroke="#8a5a12" stroke-width="1.6" stroke-linecap="round"/>'
         '<circle cx="12" cy="9" r="6.2" fill="#f3e3bf" stroke="#8a5a12" stroke-width="1.6"/><circle cx="12" cy="9" r="2.6" fill="none" stroke="#8a5a12" stroke-width="1.4"/></svg>')


SVG_COL = {"triangle": "#16a56f", "circle": "#e04848", "cross": "#3f7fe0", "square": "#d457a8", "hexagon": "#c98a1e"}
def svg_shape(kind):
    inner = {"circle": '<circle cx="12" cy="12" r="5.4"/>', "triangle": '<path d="M12 6 17.8 16.2H6.2Z"/>',
             "square": '<rect x="7.2" y="7.2" width="9.6" height="9.6"/>', "cross": '<path d="M7.4 7.4 16.6 16.6M16.6 7.4 7.4 16.6"/>',
             "hexagon": '<path d="M17.6 12 14.8 16.8H9.2L6.4 12 9.2 7.2h5.6Z"/>'}[kind]
    return ('<svg class="btn" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10.8" fill="#14161b"/>'
            '<g fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">%s</g></svg>' % (SVG_COL[kind], inner))


def choice_html(n, who):
    return "".join('<span class="ch">%s%s</span>' % (svg_shape(k), w) for k, w, side in choices(n) if side == who)


def slips(times, dive_of=None):
    """One strip per pilot, built like the original worksheets so it stands on its own:
    the porthole drawing, the worksheet's header already filled in, a box for each
    River Witness with their bolts and question, and where the porthole plays in the film."""
    os.makedirs("youtube/thumbs", exist_ok=True)
    for n in range(1, 56):
        t = "youtube/thumbs/p%02d.jpg" % n
        if not os.path.exists(t):
            Image.open("stills/p%02d.jpg" % n).convert("RGB").resize((380, 380), Image.LANCZOS).save(t, quality=82)
    pages, strips = [], []
    for name, a, b, _halves in DIVES:
        for n in range(a, b + 1):
            r = seeds[n - 1]; station = r[0].split("·")[1].strip()
            strips.append("""<article class="strip">
<img src="thumbs/p%02d.jpg" alt="Porthole %02d drawing">
<div class="body">
 <header><div><div class="kick">PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE</div><h2>Porthole Slip <b>%02d</b> · %s</h2></div>
  <div class="chip">%s<div><b>%s · AT %s</b><span>IN THE FILM · TOURKEY TROUTTOWN</span></div></div></header>
 <div class="fields"><span><i>Porthole #:</i> <b>%02d</b></span><span><i>Sub Station:</i> <b>%s</b></span></div>
 <div class="fields"><span><i>Rim Clue &amp; River Rule:</i> <b>%s</b> <em>· %s</em></span></div>
 <div class="two">
  <div class="box"><div class="who"><b>Crewmate B</b> “River Witness #1” <span class="dice">%s%s%s</span></div><div class="look">TURKEY THINKS · PICK ONE, DRAW ITS SHAPE</div><p>%s</p></div>
  <div class="box"><div class="who"><b>Crewmate C</b> “River Witness #2” <span class="dice">%s%s%s</span></div><div class="look">THE TROUT THINK · PICK ONE, DRAW ITS SHAPE</div><p>%s</p></div>
 </div>
 <div class="bar"><span>&rarr; COPY THE TOP TWO LINES ONTO YOUR SUBMARINE PORTHOLE LOG</span><span>○ PROBABLE &nbsp; △ PLAUSIBLE &nbsp; ✹ PREPOSTEROUS</span></div>
</div></article>""" % (n, n, n, station, SNAIL, name.upper(), stamp(times[n]), n, station, r[1], r[5],
                       die(1), die(2), die(3), choice_html(n, "turkey"), die(4), die(5), die(6), choice_html(n, "trout")))
    for i in range(0, len(strips), 4):
        pages.append("<section>%s</section>" % "".join(strips[i:i + 4]))
    open("youtube/slips.html", "w").write("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tourkey Trouttown · Porthole Slips</title><style>
@page{size:letter;margin:9mm 10mm}*{box-sizing:border-box}
body{margin:0;font:10.5px/1.3 Inter,"Helvetica Neue",Arial,sans-serif;color:#16293a;background:#fff}
section{break-after:page;display:flex;flex-direction:column;gap:0}
.strip{display:flex;gap:4.5mm;align-items:stretch;height:64.5mm;overflow:hidden;padding:3.5mm 0;border-bottom:1.2px dashed #8fa0ab;break-inside:avoid}
section .strip:last-child{border-bottom:0}
.strip img{width:51mm;height:51mm;align-self:center;border-radius:50%%;object-fit:cover}
.body{flex:1;display:flex;flex-direction:column;gap:1.6mm;min-width:0}
header{display:flex;justify-content:space-between;align-items:flex-start;gap:3mm}
.kick{font-size:7.5px;font-weight:800;letter-spacing:.08em;color:#8a5a12}
h2{margin:.3mm 0 0;font-size:17px;line-height:1.1;font-weight:800}h2 b{font-size:22px}
.chip{display:flex;gap:1.8mm;align-items:center;border:1.2px solid #c99a4a;background:#fbf3df;border-radius:2.2mm;padding:1.2mm 2.4mm;white-space:nowrap}
.chip b{display:block;font-size:9px;letter-spacing:.03em}.chip span{font-size:7px;font-weight:700;color:#8a5a12;letter-spacing:.03em}
.snail{width:7mm;height:5mm}
.fields{display:flex;gap:6mm;border-bottom:1.1px solid #16293a;padding-bottom:.7mm}
.fields i{font-style:normal;font-weight:700}.fields b{font-size:12px}.fields em{font-style:normal;font-weight:600;color:#8a5a12}
.two{display:grid;grid-template-columns:1fr 1fr;gap:3mm;flex:1}
.box{border:1.1px solid #9fb0bf;border-top:2.2px solid #16293a;background:#f1f5f8;border-radius:1.6mm;padding:1.6mm 2.2mm}
.who{display:flex;align-items:center;gap:1.2mm;font-size:9px}.who b{font-size:10.5px}.dice{margin-left:auto;display:flex;gap:.8mm}.die{width:4.6mm;height:4.6mm}
.look{font-size:7.5px;font-weight:800;letter-spacing:.07em;color:#8a5a12;margin-top:.6mm}
.box p{margin:.6mm 0 0;font-size:12px;line-height:1.15;font-weight:700;display:flex;flex-direction:column;gap:.45mm}.ch{display:flex;align-items:center;gap:1.4mm}.btn{width:5.2mm;height:5.2mm;flex:none}
.bar{display:flex;justify-content:space-between;background:#16344a;color:#fff;border-radius:1.4mm;padding:1.3mm 2.6mm;font-size:7.6px;font-weight:800;letter-spacing:.05em}
@media screen{body{max-width:216mm;margin:0 auto;padding:16px}}
@media screen and (max-width:700px){.strip{height:auto;flex-direction:column}.two{grid-template-columns:1fr}.strip img{width:40vw;height:40vw}header{flex-direction:column}}
</style></head><body>%s</body></html>""" % "".join(pages))


if __name__ == "__main__":
    os.makedirs("youtube", exist_ok=True)
    if "--slips" in sys.argv:
        tt = json.load(open("youtube/timing.json"))["portholes"]
        stamp = lambda v: v
        slips({int(k): v for k, v in tt.items()})
        sys.exit(print("youtube/slips.html"))
    print("narration: %d new lines made" % V.prefetch(all_lines()), flush=True)
    out, times, chapters = Out(), {}, [(0, "How to play")]
    opening(out)
    for spec in DIVES:
        t0 = dive(out, spec, times)
        chapters.append((t0, "%s · slips %02d to %02d" % (spec[0], spec[1], spec[2])))
        print(spec[0], stamp(t0), flush=True)
    chapters.append((out.t, "Roll once and send it up"))
    closing(out)
    kbps = out.close("youtube/tourkey-trouttown.mp4")
    songs = [HOWTO_SONG[1]] + [h[1] for d in DIVES for h in d[3]] + [CLOSE_SONG[1]]
    open("youtube/chapters.txt", "w").write("\n".join("%s %s" % (stamp(s), nme) for s, nme in chapters) + "\n\nMusic from DEEP SEA VOYAGE: " + ", ".join(songs) + ".\n")
    json.dump({"length": round(out.t, 2), "portholes": {"%02d" % n: stamp(s) for n, s in sorted(times.items())},
               "seconds": {"%02d" % n: round(s, 3) for n, s in sorted(times.items())}}, open("youtube/timing.json", "w"), indent=1)
    slips(times)
    print("youtube/tourkey-trouttown.mp4  %s  video %d kbps" % (stamp(out.t), kbps))
