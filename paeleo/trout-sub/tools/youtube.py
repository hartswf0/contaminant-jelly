#!/usr/bin/env python3
"""youtube: the one film for the whole exercise, made to sit beside the
Submarine Porthole Log worksheet (tour_key_porthole_worksheet.pdf).

    python3 tools/youtube.py     # youtube/tourkey-trouttown.mp4, chapters.txt, slips.html, timing.json

Rules of the cut
- The film plays in a box on a paper page, like the worksheet's drawing box; one strip
  under it carries the worksheet's own header fields in the worksheet's order:
  Porthole #, Sub Station, Rim Clue & River Rule.
- The only thing on the picture is the this-or-that: the choices from the porthole's
  question, drawn small beside the glass the way a game draws a prompt, Turkey's on
  his side of the cut and the trout's on theirs. The live choice steps on the beat.
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
units = json.load(open("units.json")) if os.path.exists("units.json") else {}
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


def options(question):
    """'Shipwreck, giant's foot, or tunnel?' -> ['SHIPWRECK', "GIANT'S FOOT", 'TUNNEL']"""
    import re
    q = question.strip().rstrip("?")
    parts = [x.strip() for x in re.split(r",\s*or\s+|,\s*|\s+or\s+", q) if x.strip()]
    return [x.upper() for x in parts]


def prompt(opts, lit, colour):
    """A this-or-that prompt as a game draws one: a ring on the live choice, dots on the others,
    one thin line joining them. Sits beside the porthole, which the lock keeps in one place.
    Returns (x, y, bgr float image, alpha) for the film box."""
    pad, gap = 10, 36
    probe = ImageDraw.Draw(Image.new("L", (4, 4)))
    size = 23
    while max(probe.textlength(o, font=font(size, "Bold")) for o in opts) > 250 and size > 15:
        size -= 1
    wmax = int(max(probe.textlength(o, font=font(size, "Bold")) for o in opts)) + 44 + 2 * pad
    hgt = gap * len(opts) + 2 * pad
    im = Image.new("RGBA", (wmax, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = pad + 11
    d.line((cx, pad + gap / 2, cx, pad + gap * (len(opts) - 0.5)), fill=(255, 255, 255, 170), width=2)
    for i, o in enumerate(opts):
        cy = pad + gap * i + gap / 2
        on = i == lit
        for dx, dy in ((2, 2), (1, 1)):                                  # soft shadow so it reads on any picture
            d.text((pad + 34 + dx, cy - size * 0.62 + dy), o, font=font(size, "Bold"), fill=(0, 0, 0, 150))
        if on:
            d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=(12, 18, 20, 235), outline=colour, width=3)
            d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=colour)
        else:
            d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(255, 255, 255, 190))
        d.text((pad + 34, cy - size * 0.62), o, font=font(size, "Bold"), fill=(255, 255, 255, 255 if on else 165))
    a = np.array(im).astype(np.float32)
    x = int(BW / 2 + U.CANON_R * BW + 18); y = int(BH / 2 - hgt / 2)
    x = min(x, BW - wmax - 6)
    return x, y, a[:, :, 2::-1].copy(), a[:, :, 3:4] / 255.0


def stamp_prompt(box, pr, fade=1.0):
    x, y, rgb, al = pr
    h, w = rgb.shape[:2]
    reg = box[y:y + h, x:x + w]
    box[y:y + h, x:x + w] = reg * (1 - al * fade) + rgb * (al * fade)
    return box


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
        u_ = units.get("p%02d" % pid) or {}
        cut = u_.get("cut") if u_.get("lock_end") and u_.get("cut") else U.LEN - 0.9
        cut_f = int(cut / U.LEN * frames_n)
        row = seeds[pid - 1]
        sides = []
        for q, col in ((row[3], (240, 178, 90, 255)), (row[4], (111, 195, 184, 255))):
            o = options(q); sides.append([prompt(o, k, col) for k in range(len(o))])
        beat_f = max(8, int(round((end - start) / step * FPS)))          # the live choice steps on the beat
        for i in range(frames_n):
            box = fr[i].astype(np.float32)
            side = sides[0] if i < cut_f else sides[1]
            since = i - nt if i < cut_f else i - cut_f
            if since >= 0 and i < frames_n - 3:
                k = (since // (2 * beat_f)) % len(side)
                box = stamp_prompt(box, side[k], min(1.0, (since + 1) / 6.0))
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


def die(n):
    """A die face drawn as SVG, in the worksheet's gold-edged square."""
    pips = {1: [(12, 12)], 2: [(7, 7), (17, 17)], 3: [(7, 7), (12, 12), (17, 17)], 4: [(7, 7), (17, 7), (7, 17), (17, 17)],
            5: [(7, 7), (17, 7), (12, 12), (7, 17), (17, 17)], 6: [(7, 6), (17, 6), (7, 12), (17, 12), (7, 18), (17, 18)]}[n]
    return ('<svg class="die" viewBox="0 0 24 24"><rect x="1.5" y="1.5" width="21" height="21" rx="4" fill="#fbf6e9" stroke="#8a5a12" stroke-width="1.6"/>%s</svg>'
            % "".join('<circle cx="%d" cy="%d" r="2" fill="#16293a"/>' % p for p in pips))


SNAIL = ('<svg class="snail" viewBox="0 0 28 20"><path d="M3 16h20c2 0 3-2 3-4" fill="none" stroke="#8a5a12" stroke-width="1.6" stroke-linecap="round"/>'
         '<circle cx="12" cy="9" r="6.2" fill="#f3e3bf" stroke="#8a5a12" stroke-width="1.6"/><circle cx="12" cy="9" r="2.6" fill="none" stroke="#8a5a12" stroke-width="1.4"/></svg>')


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
    for name, a, b, _, song, _ in DIVES:
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
  <div class="box"><div class="who"><b>Crewmate B</b> “River Witness #1” <span class="dice">%s%s%s</span></div><div class="look">TURKEY LOOKS OUT</div><p>%s</p></div>
  <div class="box"><div class="who"><b>Crewmate C</b> “River Witness #2” <span class="dice">%s%s%s</span></div><div class="look">TROUT LOOK IN</div><p>%s</p></div>
 </div>
 <div class="bar"><span>&rarr; COPY THE TOP TWO LINES ONTO YOUR SUBMARINE PORTHOLE LOG</span><span>○ PROBABLE &nbsp; △ PLAUSIBLE &nbsp; ✹ PREPOSTEROUS</span></div>
</div></article>""" % (n, n, n, station, SNAIL, name.upper(), stamp(times[n]), n, station, r[1], r[5],
                       die(1), die(2), die(3), r[3], die(4), die(5), die(6), r[4]))
    for i in range(0, len(strips), 4):
        pages.append("<section>%s</section>" % "".join(strips[i:i + 4]))
    open("youtube/slips.html", "w").write("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tourkey Trouttown · Porthole Slips</title><style>
@page{size:letter;margin:9mm 10mm}*{box-sizing:border-box}
body{margin:0;font:10.5px/1.3 Inter,"Helvetica Neue",Arial,sans-serif;color:#16293a;background:#fff}
section{break-after:page;display:flex;flex-direction:column;gap:0}
.strip{display:flex;gap:4.5mm;align-items:stretch;height:64.5mm;padding:3.5mm 0;border-bottom:1.2px dashed #8fa0ab;break-inside:avoid}
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
.box p{margin:.5mm 0 0;font-size:13px;line-height:1.22;font-weight:700}
.bar{display:flex;justify-content:space-between;background:#16344a;color:#fff;border-radius:1.4mm;padding:1.3mm 2.6mm;font-size:7.6px;font-weight:800;letter-spacing:.05em}
@media screen{body{max-width:216mm;margin:0 auto;padding:16px}}
@media screen and (max-width:700px){.strip{height:auto;flex-direction:column}.two{grid-template-columns:1fr}.strip img{width:40vw;height:40vw}header{flex-direction:column}}
</style></head><body>%s</body></html>""" % "".join(pages))


if __name__ == "__main__":
    os.makedirs("youtube", exist_ok=True)
    if "--slips" in sys.argv:                                   # reprint the slips from the last build's timings
        tt = json.load(open("youtube/timing.json"))["portholes"]
        stamp = lambda v: v
        slips({int(k): v for k, v in tt.items()})
        sys.exit(print("youtube/slips.html"))
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
    json.dump({"length": round(out.t, 2), "portholes": {"%02d" % n: stamp(s) for n, s in sorted(times.items())},
               "seconds": {"%02d" % n: round(s, 3) for n, s in sorted(times.items())}}, open("youtube/timing.json", "w"), indent=1)
    slips(times, None)
    print("youtube/tourkey-trouttown.mp4  %s" % stamp(out.t))
