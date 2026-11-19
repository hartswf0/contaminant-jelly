#!/usr/bin/env python3
"""youtube: the one film for the whole exercise, made to sit beside the
Submarine Porthole Log worksheet (sheets/tour_key_porthole_worksheet.pdf).

    python3 tools/youtube.py           # youtube/tourkey-trouttown.mp4, chapters.txt, slips.html, timing.json
    python3 tools/youtube.py --slips   # reprint the slips from the last build's timings

Rules of the cut
- The picture fills the screen. On it there are only three things: the slip number, a
  minimap of the river showing where this porthole is, and the choices.
- The choices are buttons. Each porthole gives Turkey's choices (right of the glass) and
  the trout's (left of it), each with its own shape. Students pick one and draw the
  shape. The side whose shot is playing is lit.
- Written for fourth graders who need more time: every porthole plays twice through
  (about 14 seconds), words are few, large and in sentence case, and nothing blinks.
- Four dives of 16, 16, 16 and 7 portholes. Each half of a dive has its own song from
  DEEP SEA VOYAGE, and portholes change on that song's tracked beats.
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

W, H, FPS = 1280, 720, 24
BX, BY, BW, BH = 0, 0, W, H                     # the film fills the frame
TRANS = 0.6                                     # seconds of the through-the-porthole change
MAX_MB = 92                                     # the finished file is held under this
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
def side_panel(items, side, live):
    """One side's buttons. side 'turkey' sits right of the glass, 'trout' left of it. Each choice is
    a plate with its controller button on it and an edge in the button's colour."""
    pw = int(W / 2 - RIM - 26)
    im = Image.new("RGBA", (pw, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    size = 29; tx = 92
    while size > 21 and any(len(wrap(d, w, font(size, "Bold"), pw - tx - 14)) > 2 for _, w, _ in items):
        size -= 1
    blocks = [wrap(d, w, font(size, "Bold"), pw - tx - 14) for _, w, _ in items]
    heights = [max(78, len(b) * (size + 6) + 26) for b in blocks]
    total = sum(heights) + 14 * (len(items) - 1) + 44
    y = (H - total) // 2 - 34
    tag = "Turkey thinks" if side == "turkey" else "The trout think"
    d.text((8, y), tag, font=font(22, "Bold"), fill=(255, 255, 255, 240 if live else 120)); y += 44
    for (kind, word, _), lines, hgt in zip(items, blocks, heights):
        col = C.SHAPE_COL[kind]
        d.rounded_rectangle((0, y, pw - 2, y + hgt), 18, fill=(8, 10, 14, 215 if live else 120))
        d.rounded_rectangle((0, y, pw - 2, y + hgt), 18, outline=col + (255 if live else 90,), width=3 if live else 2)
        C.button(d, 44, y + hgt / 2, 30, kind, on=live)
        ty = y + (hgt - len(lines) * (size + 6)) / 2 - 2
        for l in lines:
            d.text((tx, ty), l, font=font(size, "Bold"), fill=(255, 255, 255, 255 if live else 150)); ty += size + 6
        y += hgt + 14
    a = np.array(im).astype(np.float32)
    x = int(W / 2 + RIM + 12) if side == "turkey" else int(W / 2 - RIM - 12 - pw)
    return x, 0, a[:, :, 2::-1].copy(), a[:, :, 3:4] / 255.0


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
    """The slip number, top right, and the minimap with the station's name, bottom left."""
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
    station = seeds[n - 1][0].split("·")[1].strip(); f = font(24, "Bold")
    tw = d.textlength(station, font=f)
    d.rounded_rectangle((cx - r, cy - r - 52, cx - r + tw + 30, cy - r - 12), 10, fill=(10, 16, 18, 215))
    d.text((cx - r + 15, cy - r - 49), station, font=f, fill=(255, 255, 255, 255))
    a = np.array(im).astype(np.float32)
    regs = []
    for (x0, y0, x1, y1) in ((W - 300, 0, W, 150), (0, H - 270, 330, H)):
        regs.append((x0, y0, a[y0:y1, x0:x1, 2::-1].copy(), a[y0:y1, x0:x1, 3:4] / 255.0))
    return regs


def stamp_on(frame, reg, fade=1.0):
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
        self.tmp = tempfile.mkdtemp(); self.path = self.tmp + "/master.mp4"; self.n = 0; self.music = []
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", self.path], stdin=subprocess.PIPE)
    def add(self, frame):
        self.p.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes()); self.n += 1
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
            fc.append("[%d:a]aresample=44100,aformat=channel_layouts=stereo,afade=t=in:d=0.3,afade=t=out:st=%.3f:d=1.2,adelay=%d:all=1[m%d]" % (i, max(0, length - 1.2), int(at * 1000), i))
            mix.append("[m%d]" % i)
        fc.append("%samix=inputs=%d:normalize=0,alimiter=limit=0.9,apad[a]" % ("".join(mix), len(mix)))
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


CARD_SECONDS = [9.0, 8.0, 11.0, 12.0, 9.0, 9.0]
def opening(out):
    """Title, one card per command on the worksheet, then how the buttons work."""
    t0 = out.t
    for f in C.title(film_frames("films/intro-6.mp4", 2.4, int(5.6 * FPS), 1136, 639)):
        out.add(f)
    for k, (spec, secs) in enumerate(zip(C.CARDS, CARD_SECONDS)):
        n = int(secs * FPS)
        for f in C.card(spec, film_frames(spec["film"][0], spec["film"][1], n, 640, 360), n, first=(k == 0)):
            out.add(f)
    for f in C.choose_card(int(9.0 * FPS)):
        out.add(f)
    bt, rms, sr, dur = beats(HOWTO_SONG[0])
    out.song(HOWTO_SONG[0], float(bt[min(8, len(bt) - 1)]), t0, min(out.t - t0 + 0.4, dur - 1))


def closing(out):
    """The last two commands again, for the moment the logs come back."""
    t0 = out.t
    for spec in C.CARDS[4:]:
        n = int(9.0 * FPS)
        for f in C.card(spec, film_frames(spec["film"][0], spec["film"][1], n, 640, 360), n, first=False):
            out.add(f)
    bt, rms, sr, dur = beats(CLOSE_SONG[0])
    out.song(CLOSE_SONG[0], float(bt[min(8, len(bt) - 1)]), t0, min(out.t - t0 + 0.4, dur - 1))


def dive(out, spec, times):
    name, a, b, halves = spec
    t_dive = out.t
    pid = a; prev_tail = None
    nt = int(TRANS * FPS)
    for h, (path, title, step, count) in enumerate(halves):
        bt, rms, sr, dur = beats(path)
        lead = 8 if h == 0 else 0                           # beats under the dive card
        i0 = pick_start(bt, rms, sr, lead + step * count, dur)
        T = lambda k: float(bt[min(i0 + k, len(bt) - 1)] - bt[i0])
        t0 = out.t
        if h == 0:
            card = None
            for card in C.dive_card(name, a, b, " and ".join(x[1] for x in halves), int(round(T(lead) * FPS))):
                out.add(card)
            prev_tail = None
        for j in range(count):
            end = t0 + T(lead + step * (j + 1))
            frames_n = int(round(end * FPS)) - out.n
            half_n = frames_n // 2
            one, _ = U.frames("units/p%02d.mp4" % pid, half_n, W, H)            # the whole unit, played twice through
            u_ = units.get("p%02d" % pid) or {}
            cut = u_.get("cut") if u_.get("lock_end") and u_.get("cut") else U.LEN - 0.9
            cut_f = int(cut / U.LEN * half_n)
            ch = choices(pid)
            tk, tr = [c for c in ch if c[2] == "turkey"], [c for c in ch if c[2] == "trout"]
            panels = {(s_, live): side_panel(items, s_, live) for s_, items in (("turkey", tk), ("trout", tr)) for live in (True, False)}
            regs = hud(pid)
            times[pid] = out.t
            for i in range(frames_n):
                k = min(i, 2 * half_n - 1) % half_n
                frame = one[k].astype(np.float32)
                turkey_live = k < cut_f
                fade = min(1.0, max(0.0, (i - nt + 4) / 8.0))
                if fade > 0:
                    stamp_on(frame, panels[("turkey", turkey_live)], fade)
                    stamp_on(frame, panels[("trout", not turkey_live)], fade)
                for reg in regs:
                    stamp_on(frame, reg)
                if i < nt and prev_tail is None:              # out of the dive card: the bars clear to the first porthole
                    u = (i + 1) / float(nt)
                    frame = C.bgr(C.bars(Image.fromarray(frame.astype(np.uint8)[:, :, ::-1]), 0.5 + 0.5 * u)).astype(np.float32)
                elif i < nt:
                    frame = through(prev_tail, frame, (i + 1) / float(nt))
                out.add(frame)
            prev_tail = one[-1].astype(np.float32)
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
.box p{margin:.8mm 0 0;font-size:12.5px;line-height:1.2;font-weight:700;display:flex;flex-direction:column;gap:.9mm}.ch{display:flex;align-items:center;gap:1.4mm}.btn{width:6.2mm;height:6.2mm;flex:none}
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
