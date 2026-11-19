#!/usr/bin/env python3
"""youtube: the one film for the whole exercise, made to sit beside the
Submarine Porthole Log worksheet (tour_key_porthole_worksheet.pdf).

    python3 tools/youtube.py     # youtube/tourkey-trouttown.mp4, chapters.txt, slips.html, timing.json

Rules of the cut
- Nothing is ever printed over the picture. The film plays in a box on a paper page,
  like the worksheet's drawing box; one strip under it carries the worksheet's own
  header fields in the worksheet's order: Porthole #, Sub Station, Rim Clue & River Rule.
  The two crewmate questions live on the printed slip, not on screen.
- Four dives of 16, 16, 16 and 7 portholes, one class set each, each with its own song
  from the album DEEP SEA VOYAGE. Portholes change on the song's own beats (every
  BEATS beats, tracked from the audio), so every cut lands on the music.
- The change between portholes goes through the porthole: the next film opens from
  the glass outward. Units are rim-locked, so the brass ring holds still through it.
No fal call is made here.
"""
import json, os, subprocess, sys, tempfile, warnings
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import units as U

W, H, FPS = 1280, 720, 24
BX, BY, BW, BH = 72, 16, 1136, 639             # the film box
PAPER, NAVY, SOFT, GOLD = (246, 241, 228), (22, 43, 52), (95, 108, 112), (176, 122, 40)
TRANS = 0.5                                     # seconds of the through-the-porthole change
FD = "/usr/share/fonts/opentype/inter/"
font = lambda size, weight="Regular": ImageFont.truetype(FD + "Inter-%s.otf" % weight, size)
seeds = json.load(open("seeds.json"))
# dive: (name, first, last, song file, song title, beats between portholes)
DIVES = [("Dive 1", 1, 16, "music/lake-merritt-clave.ogg", "Lake Merritt Clave", 16),
         ("Dive 2", 17, 32, "music/submersible-propulsion.ogg", "Submersible Propulsion", 16),
         ("Dive 3", 33, 48, "music/ondes-in-the-abbey.ogg", "Ondes In The Abbey", 12),
         ("Dive 4", 49, 55, "music/the-verne-bench.ogg", "The Verne Bench", 20)]
HOWTO_SONG, CLOSE_SONG = ("music/descent-to-the-abyss.ogg", "Descent to the Abyss"), ("music/the-hull-breaks-surface.ogg", "The Hull Breaks Surface")
HOWTO = [
    ("films/intro-6.mp4", 2.6, 5.4, "TOURKEY TROUTTOWN", "Turkey takes a tour of Trout Town. 55 portholes. Find the number on your slip."),
    ("films/intro-1.mp4", 0.0, 7.0, "Pilot · front · 6 min", "Write your Porthole #, Sub Station, Rim Clue and River Rule. Draw what Turkey sees right now."),
    ("films/intro-2.mp4", 1.0, 7.0, "Pilot · three lines", "1 What we see outside the glass.  2 My sub command.  3 The risk to our 24 hours of air.  Pass your porthole left."),
    ("films/intro-3.mp4", 1.0, 7.0, "Crewmates B and C · back · 12 min", "B writes bolts 1, 2, 3: Turkey looks out.  Pass left again.  C writes bolts 4, 5, 6: the trout look in."),
    ("films/intro-4.mp4", 2.0, 6.0, "Pilot · roll once", "One Probable, one Plausible, one Preposterous from each crewmate. Roll 1d6 and circle that bolt."),
    ("films/intro-5.mp4", 2.0, 6.0, "Trout gossip · black-box message", "What do the trout tell FANTROL 88.7?  Dear Alien, why did the Turkey come to Trout Town?"),
]
CLOSE = [
    ("films/intro-4.mp4", 2.0, 6.0, "Your log is back", "Pilot, roll 1d6 and circle the bolt that happened."),
    ("films/intro-5.mp4", 2.0, 6.0, "Send it up", "Write the trout gossip and your black-box message. Hand your clue to the next pilot."),
]


def fit(d, text, weight, size, width):
    while d.textlength(text, font=font(size, weight)) > width and size > 13:
        size -= 1
    return font(size, weight)


def page():
    im = Image.new("RGB", (W, H), PAPER)
    ImageDraw.Draw(im).rounded_rectangle((BX - 3, BY - 3, BX + BW + 2, BY + BH + 2), 16, outline=NAVY, width=3)
    return im


def strip_porthole(n):
    """The worksheet's header, filled in for this porthole."""
    row = seeds[n - 1]; im = page(); d = ImageDraw.Draw(im)
    y = BY + BH + 12
    d.text((BX, y - 6), "%02d" % n, font=font(50, "ExtraBold"), fill=NAVY)
    x = BX + 84
    d.text((x, y), "Porthole #", font=font(15, "SemiBold"), fill=SOFT)
    d.text((x, y + 20), "Sub Station", font=font(15, "SemiBold"), fill=SOFT)
    d.text((x + 96, y - 3), "%02d" % n, font=font(20, "Bold"), fill=NAVY)
    d.text((x + 96, y + 17), row[0].split("·")[1].strip(), font=font(20, "Bold"), fill=NAVY)
    x2 = BX + 330
    d.text((x2, y), "Rim Clue", font=font(15, "SemiBold"), fill=SOFT)
    d.text((x2, y + 20), "River Rule", font=font(15, "SemiBold"), fill=SOFT)
    wmax = BX + BW - x2 - 92
    d.text((x2 + 92, y - 3), row[1], font=fit(d, row[1], "Bold", 20, wmax), fill=NAVY)
    d.text((x2 + 92, y + 17), row[5], font=fit(d, row[5], "SemiBold", 20, wmax), fill=GOLD)
    return np.array(im)[:, :, ::-1].copy()


def strip_caption(title, body):
    im = page(); d = ImageDraw.Draw(im); y = BY + BH + 9
    d.text((BX, y), title, font=font(22, "Bold"), fill=GOLD)
    tw = d.textlength(title, font=font(22, "Bold"))
    wmax = BW - tw - 26
    f = fit(d, body, "SemiBold", 21, wmax)
    if d.textlength(body, font=f) > wmax:                      # still too long: put it on its own line
        d.text((BX, y + 28), body, font=fit(d, body, "SemiBold", 19, BW), fill=NAVY)
    else:
        d.text((BX + tw + 26, y + 1), body, font=f, fill=NAVY)
    return np.array(im)[:, :, ::-1].copy()


def title_card(name, a, b, song):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.rounded_rectangle((BX - 3, BY - 3, BX + BW + 2, BY + BH + 2), 16, outline=NAVY, width=3)
    d.text((BX + 70, 150), "PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE", font=font(22, "Bold"), fill=GOLD)
    d.text((BX + 66, 190), name.upper(), font=font(150, "ExtraBold"), fill=NAVY)
    d.text((BX + 74, 372), "Slips %02d to %02d" % (a, b), font=font(54, "Bold"), fill=NAVY)
    d.text((BX + 74, 452), "Hold up your slip when your number plays.", font=font(28), fill=SOFT)
    d.text((BX, BY + BH + 20), "Music: %s, from DEEP SEA VOYAGE" % song, font=font(18, "SemiBold"), fill=SOFT)
    return np.array(im)[:, :, ::-1].copy()


yy, xx = np.mgrid[:BH, :BW]
DIST = np.hypot(xx - BW / 2.0, yy - BH / 2.0)
CORNER = np.array(Image.new("L", (BW, BH), 0)); _c = Image.new("L", (BW, BH), 0); ImageDraw.Draw(_c).rounded_rectangle((0, 0, BW - 1, BH - 1), 14, fill=255)
CORNER = (np.array(_c) / 255.0)[..., None].astype(np.float32)
R0, R1 = U.CANON_R * BW * U.GLASS, np.hypot(BW, BH) / 2 + 8


def through(a, b, u):
    """The next film opens from the glass outward. u runs 0..1."""
    e = u * u * (3 - 2 * u)
    r = R0 * 0.2 + (R1 - R0 * 0.2) * e
    m = np.clip((r - DIST) / 10.0 + 0.5, 0, 1)[..., None]
    return a * (1 - m) + b * m


def put(canvas, box):
    out = canvas.copy()
    reg = out[BY:BY + BH, BX:BX + BW].astype(np.float32)
    out[BY:BY + BH, BX:BX + BW] = (reg * (1 - CORNER) + box * CORNER).astype(np.uint8)
    return out


def clip(src, ss, t):
    n = int(round(t * FPS))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(t + 0.2), "-i", src, "-vf",
                          "fps=%d,scale=%d:%d:flags=lanczos" % (FPS, BW, BH), "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, BH, BW, 3)
    return np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)]) if len(a) < n else a


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
    """Frames in, one silent video part out; the audio plan is mixed at the end."""
    def __init__(self):
        self.tmp = tempfile.mkdtemp(); self.path = self.tmp + "/video.mp4"; self.n = 0; self.music = []
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                                   "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-g", "48", self.path], stdin=subprocess.PIPE)
    def add(self, frame):
        self.p.stdin.write(frame.tobytes()); self.n += 1
    @property
    def t(self):
        return self.n / float(FPS)
    def song(self, path, start_in_song, at, length):
        self.music.append((path, start_in_song, at, length))
    def close(self, dest):
        self.p.stdin.close(); self.p.wait()
        ins, fc, mix = ["-i", self.path], [], []
        for i, (path, ss, at, length) in enumerate(self.music, 1):
            ins += ["-ss", "%.3f" % ss, "-t", "%.3f" % length, "-i", path]
            fc.append("[%d:a]aresample=44100,aformat=channel_layouts=stereo,afade=t=in:d=0.25,afade=t=out:st=%.3f:d=1.1,adelay=%d:all=1[m%d]" % (i, length - 1.1, int(at * 1000), i))
            mix.append("[m%d]" % i)
        fc.append("%samix=inputs=%d:normalize=0,alimiter=limit=0.9,apad[a]" % ("".join(mix), len(mix)))
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-t", "%.3f" % self.t, "-movflags", "+faststart", dest], check=True)


def shots(out, specs, song):
    t0 = out.t; prev = None
    for src, ss, t, title, body in specs:
        fr = clip(src, ss, t); canvas = strip_caption(title, body)
        for i in range(len(fr)):
            box = fr[i].astype(np.float32)
            if prev is not None and i < int(TRANS * FPS):
                u = (i + 1) / (TRANS * FPS)
                box = prev * (1 - u) + box * u
            out.add(put(canvas, box))
        prev = fr[-1].astype(np.float32)
    bt, rms, sr, dur = beats(song[0])
    out.song(song[0], float(bt[min(8, len(bt) - 1)]), t0, min(out.t - t0 + 0.4, dur - 1))


def dive(out, spec, times):
    name, a, b, path, title, step = spec
    bt, rms, sr, dur = beats(path)
    n = b - a + 1
    lead = 8                                               # beats under the title card
    i0 = pick_start(bt, rms, sr, lead + step * n, dur)
    T = lambda k: float(bt[min(i0 + k, len(bt) - 1)] - bt[i0])   # seconds from the song start point to beat k
    t0 = out.t
    card = title_card(name, a, b, title)
    for _ in range(int(round(T(lead) * FPS))):
        out.add(card)
    prev_tail = card[BY:BY + BH, BX:BX + BW].astype(np.float32); prev_canvas = card
    nt = int(TRANS * FPS)
    for j in range(n):
        pid = a + j
        start, end = t0 + T(lead + step * j), t0 + T(lead + step * (j + 1))
        frames_n = int(round(end * FPS)) - out.n
        fr, _ = U.frames("units/p%02d.mp4" % pid, frames_n, BW, BH)      # the whole unit, time-fitted to its bars
        canvas = strip_porthole(pid)
        times[pid] = out.t
        for i in range(frames_n):
            box = fr[i].astype(np.float32)
            if i < nt:
                u = (i + 1) / float(nt)
                frame = put(canvas, through(prev_tail, box, u))
                frame[BY + BH + 4:] = (prev_canvas[BY + BH + 4:] * (1 - u) + canvas[BY + BH + 4:] * u).astype(np.uint8)
            else:
                frame = put(canvas, box)
            out.add(frame)
        prev_tail = fr[-1].astype(np.float32); prev_canvas = canvas
    out.song(path, float(bt[i0]), t0, out.t - t0 + 0.6)
    return t0


def stamp(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


def slips(times, dive_of):
    """One printed slip per pilot. The slip carries the words; the film carries the picture."""
    pages = []
    for name, a, b, _, _, _ in DIVES:
        cells = "".join(
            '<div class="slip"><div class="n">%02d</div><div class="t"><div class="h"><b>%s</b><span>%s · %s</span></div>'
            '<p><u>Rim Clue</u> %s</p><p><u>River Rule</u> %s</p>'
            '<p class="q"><u>Crewmate B · bolts 1 2 3 · Turkey looks out</u> %s</p>'
            '<p class="q"><u>Crewmate C · bolts 4 5 6 · Trout look in</u> %s</p></div></div>'
            % (n, seeds[n - 1][0].split("·")[1].strip(), name, stamp(times[n]), seeds[n - 1][1], seeds[n - 1][5], seeds[n - 1][3], seeds[n - 1][4])
            for n in range(a, b + 1))
        pages.append('<section><h1>TOURKEY TROUTTOWN · %s · slips %02d to %02d</h1><div class="grid">%s</div></section>' % (name, a, b, cells))
    open("youtube/slips.html", "w").write("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tourkey Trouttown · Slips</title><style>
@page{size:letter;margin:9mm}*{box-sizing:border-box}body{margin:0;font:11px/1.3 Inter,Arial,sans-serif;color:#162b34;background:#fff}
section{break-after:page}h1{font-size:13px;margin:0 0 2mm}
.grid{display:grid;grid-template-columns:1fr 1fr}
.slip{display:flex;gap:3mm;border:1px dashed #9aa8ad;padding:2.5mm 3mm;min-height:30mm;break-inside:avoid}
.n{font-size:36px;font-weight:800;line-height:1;min-width:15mm}.h{display:flex;justify-content:space-between;gap:2mm;margin-bottom:1mm}
.h b{font-size:14px}.h span{color:#b07a28;font-weight:600}p{margin:0 0 .6mm}u{text-decoration:none;color:#5f6c70;font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.03em;margin-right:1mm}
.q u{display:block}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style></head><body>%s</body></html>""" % "".join(pages))


if __name__ == "__main__":
    os.makedirs("youtube", exist_ok=True)
    out, times, chapters = Out(), {}, [(0, "How to play")]
    shots(out, HOWTO, HOWTO_SONG)
    for spec in DIVES:
        t0 = dive(out, spec, times)
        chapters.append((t0, "%s · slips %02d to %02d · %s" % (spec[0], spec[1], spec[2], spec[4])))
        print(spec[0], stamp(t0), flush=True)
    chapters.append((out.t, "Roll once and send it up"))
    shots(out, CLOSE, CLOSE_SONG)
    out.close("youtube/tourkey-trouttown.mp4")
    open("youtube/chapters.txt", "w").write("\n".join("%s %s" % (stamp(s), nme) for s, nme in chapters) + "\n\nMusic from DEEP SEA VOYAGE: "
        + ", ".join([HOWTO_SONG[1]] + [d[4] for d in DIVES] + [CLOSE_SONG[1]]) + ".\n")
    json.dump({"length": round(out.t, 2), "portholes": {"%02d" % n: stamp(s) for n, s in sorted(times.items())}}, open("youtube/timing.json", "w"), indent=1)
    slips(times, None)
    print("youtube/tourkey-trouttown.mp4  %s" % stamp(out.t))
