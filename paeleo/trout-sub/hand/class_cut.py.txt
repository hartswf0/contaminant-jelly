#!/usr/bin/env python3
"""class_cut: the five class films cut into one film that teaches the game.

    python3 class_cut.py     # assets/how-to-play-the-porthole-game.mp4

The picture always sits on a paper mat with a teaching strip under it. The strip says which step of the
game is on screen (1 Draw, 2 Turkey thinks, 3 The trout think, Roll) and, line by line, which question or
which kind of ending the child is answering. Between films a brass porthole carries the last picture
across the table to the next one while a paper slip gives one thing to watch for. The opening teaches the
four steps; the ending hands the game over. Every sentence inside the films is still the children's own.
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import voice_pass as VP
W, H, FPS, SR = 960, 540, 24, 44100
FW, FH, FX, FY = 832, 468, 64, 6                     # the picture's place on the mat
PAPER, INK, MUTE = (247, 242, 230), (28, 35, 38), (112, 120, 122)
PENCIL, RUST, TEAL, GOLD = (236, 178, 46), (196, 78, 52), (38, 132, 128), (203, 150, 52)
SHAPE = {"triangle": (46, 160, 96), "circle": (214, 62, 58), "cross": (62, 108, 214), "square": (222, 110, 170)}
F = lambda size, w="Black": ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-%s.otf" % w, size)
TMP = tempfile.mkdtemp()
ease = lambda u: (lambda v: v * v * (3 - 2 * v))(min(1.0, max(0.0, u)))
back = lambda u: (lambda v: v * v * (2.7 * v + 1.7) + 1)(min(1.0, max(0.0, u)) - 1)
lerp = lambda a, b, u: a + (b - a) * u
SHEETS = {s["porthole"]: s for s in json.load(open("../class/transcripts.json"))["sheets"]}
ORDER = [10, 13, 16, 25, 33]
STEPS = [("1", "DRAW", PENCIL), ("2", "TURKEY THINKS", RUST), ("3", "THE TROUT THINK", TEAL), ("4", "ROLL", GOLD)]
KIND = {"probable": "PROBABLE: it will likely happen.", "plausible": "PLAUSIBLE: it could happen.", "preposterous": "PREPOSTEROUS: no way! Or... maybe?"}
ASK = ["Who is outside?", "What does Turkey do?", "How does the air get used up?"]
# One thing to watch for in each film: (slip title, slip second line, what the narrator says)
LESSON = {
 10: ("WATCH THE WHOLE GAME", "Draw. Pass. Pass.", "Porthole ten. Watch the whole game. One kid draws. Then two friends each write three endings."),
 13: ("EACH ENDING GETS WILDER", "Probable. Plausible. Preposterous.", "Porthole thirteen. Listen to the three endings. Each one gets wilder. The last friend left theirs blank, and that is okay."),
 16: ("ONE SENTENCE IS ENOUGH", "You do not have to fill every line.", "Porthole sixteen. These friends wrote just one ending each. One good sentence is enough."),
 25: ("PAGE ONE SETS UP THE STORY", "The pilot wrote: panic.", "Porthole twenty five. The pilot wrote, panic. So watch Turkey panic the whole way through. The first page sets up the story."),
 33: ("THE BUTTON CHANGES THE STORY", "Stone tunnel, or movie projector?", "Porthole thirty three. Watch the buttons. One friend picked a stone tunnel. The next picked a movie projector. Same porthole, two stories."),
}


# ---------- drawing ----------
def wood():
    rs = np.random.RandomState(7); im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for i in range(7):
        c = 92 + rs.randint(-8, 8); d.rectangle((0, i * 80, W, i * 80 + 78), fill=(c, int(c * 0.68), int(c * 0.42))); d.rectangle((0, i * 80 + 78, W, i * 80 + 80), fill=(52, 36, 22))
    a = np.asarray(im).astype(np.int16); grain = (rs.randn(H, 1, 1) * 5 + rs.randn(H, W, 1) * 2.5).astype(np.int16)
    return Image.fromarray(np.clip(a + grain, 0, 255).astype(np.uint8))
WOOD = wood()


def ring(im, cx, cy, r, bolts=True, lit=None):
    """A brass porthole rim of inner radius r, with six bolts."""
    d = ImageDraw.Draw(im); t = max(12, int(r * 0.13))
    for k, col in enumerate(((92, 66, 20), (176, 132, 44), (226, 186, 84), (196, 150, 56), (120, 88, 28))):
        w = [t + 4, t, int(t * 0.7), int(t * 0.42), 3][k]; o = [0, 0, int(t * 0.12), int(t * 0.3), t - 2][k]
        d.ellipse((cx - r - t + o, cy - r - t + o, cx + r + t - o, cy + r + t - o), outline=col, width=max(2, w - o))
    if bolts:
        for k in range(6):
            a = math.radians(-90 + k * 60); x, y = cx + (r + t * 0.5) * math.cos(a), cy + (r + t * 0.5) * math.sin(a); b = max(4, t * 0.3)
            d.ellipse((x - b, y - b, x + b, y + b), fill=(255, 226, 120) if lit == k else (104, 76, 24), outline=(60, 42, 12))


def through(base, frame, cx, cy, r):
    """Show `frame` through a porthole of radius r at (cx, cy) on `base`."""
    s = min(1.0, max(2 * r * 1.2 / H, 0.2)); fw, fh = int(W * s), int(H * s)
    f = frame.resize((fw, fh), Image.BILINEAR) if s < 1 else frame
    layer = Image.new("RGB", (W, H)); layer.paste(f, (int(cx - fw / 2), int(cy - fh / 2)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    base.paste(layer, (0, 0), m)


def shape(d, kind, cx, cy, r, on=True):
    col = SHAPE[kind] if on else (150, 150, 150)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(34, 38, 44), outline=col, width=max(3, r // 7)); q = r * 0.5; w = max(4, r // 5)
    if kind == "triangle": d.polygon([(cx, cy - q * 1.1), (cx + q, cy + q * 0.75), (cx - q, cy + q * 0.75)], outline=col, width=w)
    elif kind == "circle": d.ellipse((cx - q, cy - q, cx + q, cy + q), outline=col, width=w)
    elif kind == "cross": d.line((cx - q, cy - q, cx + q, cy + q), fill=col, width=w); d.line((cx - q, cy + q, cx + q, cy - q), fill=col, width=w)
    else: d.rectangle((cx - q, cy - q, cx + q, cy + q), outline=col, width=w)


def die(d, cx, cy, s, n, fill=(250, 246, 236)):
    d.rounded_rectangle((cx - s, cy - s, cx + s, cy + s), s * 0.24, fill=fill, outline=INK, width=max(2, int(s * 0.08))); p = s * 0.5; r = s * 0.15
    spots = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
             5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[n]
    for x, y in spots: d.ellipse((cx + x * p - r, cy + y * p - r, cx + x * p + r, cy + y * p + r), fill=INK)


def pencil(d, x, y, ang=-55, L=120):
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux; w = 7
    tip = (x, y); b0 = (x + ux * 22, y + uy * 22); b1 = (x + ux * L, y + uy * L); e = (x + ux * (L + 16), y + uy * (L + 16))
    d.polygon([tip, (b0[0] + px * w, b0[1] + py * w), (b0[0] - px * w, b0[1] - py * w)], fill=(226, 196, 150)); d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=INK)
    d.polygon([(b0[0] + px * w, b0[1] + py * w), (b1[0] + px * w, b1[1] + py * w), (b1[0] - px * w, b1[1] - py * w), (b0[0] - px * w, b0[1] - py * w)], fill=PENCIL, outline=(150, 108, 20))
    d.polygon([(b1[0] + px * w, b1[1] + py * w), (e[0] + px * w, e[1] + py * w), (e[0] - px * w, e[1] - py * w), (b1[0] - px * w, b1[1] - py * w)], fill=(226, 120, 130))


def fit(d, text, size, maxw, w="Black"):
    while d.textlength(text, font=F(size, w)) > maxw and size > 14: size -= 1
    return F(size, w)


def mat(inner, step, hint, progress=None, dots=None):
    """The whole frame: the picture on its paper mat and the teaching strip under it."""
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.rectangle((FX - 3, FY - 3, FX + FW + 2, FY + FH + 2), fill=(206, 198, 180))
    im.paste(inner.resize((FW, FH), Image.LANCZOS), (FX, FY))
    y0 = FY + FH + 8; x = FX
    for k, (num, name, col) in enumerate(STEPS):                        # the four steps; the live one is filled and named
        live = step == k; label = "%s %s" % (num, name) if live else num; f = F(24)
        w = d.textlength(label, font=f) + 26
        d.rounded_rectangle((x, y0, x + w, y0 + 46), 10, fill=col if live else PAPER, outline=col, width=3)
        d.text((x + 13, y0 + 8), label, font=f, fill=(255, 255, 255) if live and k != 0 else (INK if live else col)); x += w + 8
    if hint:
        f = fit(d, hint, 27, FX + FW - x - 10, "Bold"); d.text((x + 8, y0 + 23 - f.size * 0.62), hint, font=f, fill=INK)
    if dots is not None:                                                # where we are among the five portholes
        for k, n in enumerate(ORDER):
            cx = 22; cy = 150 + k * 58; on = k == dots
            d.ellipse((cx - 17, cy - 17, cx + 17, cy + 17), fill=INK if on else PAPER, outline=INK if on else MUTE, width=2)
            d.text((cx - d.textlength(str(n), font=F(15)) / 2, cy - 10), str(n), font=F(15), fill=PAPER if on else MUTE)
            if k < 4: d.line((cx, cy + 19, cx, cy + 39), fill=MUTE, width=2)
    return im


# ---------- sound and segments ----------
def tone(y, at, f0, dur=0.25, amp=0.4, sweep=0.0):
    m = int(dur * SR); t = np.arange(m) / float(SR); i = int(at * SR)
    y[i:i + m] += (np.sin(2 * np.pi * (f0 + sweep * t) * t) * np.exp(-t * (5.5 / dur)) * amp).astype(np.float32)[:max(0, len(y) - i)]


def whoosh(y, at, dur=0.9, amp=0.22):
    m = int(dur * SR); t = np.arange(m) / float(SR); i = int(at * SR)
    n = np.random.RandomState(int(at * 10)).randn(m); n = np.convolve(n, np.ones(60) / 60, "same") * 6
    y[i:i + m] += (n * np.sin(np.pi * t / dur) ** 2 * amp).astype(np.float32)[:max(0, len(y) - i)]


_said = {}
def say(text, who="narrator"):
    if (text, who) not in _said: _said[(text, who)] = VP.speak(text, who)
    return _said[(text, who)]


def segment(name, seconds, draw, lines=(), sfx=(), bed=("../music/the-verne-bench.ogg", 60, 0.16)):
    n = int(round(seconds * FPS)); out = "%s/%s.mp4" % (TMP, name); y = np.zeros(int((seconds + 0.5) * SR), np.float32)
    for at, text, who in lines:
        clip = say(text, who); i = int(at * SR); clip = clip[:max(0, len(y) - i)]; y[i:i + len(clip)] += clip * 1.35
    for fn, args in sfx: fn(y, *args)
    wav = "%s/%s.wav" % (TMP, name); sf.write(wav, np.clip(y, -1, 1), SR)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav,
                          "-ss", str(bed[1]), "-i", bed[0], "-filter_complex",
                          "[1:a]asplit[v][s];[2:a]volume=%.2f,afade=t=in:d=0.8,afade=t=out:st=%.2f:d=1.2[m];[m][s]sidechaincompress=threshold=0.02:ratio=8:release=400[dk];[v][dk]amix=inputs=2:normalize=0[a]" % (bed[2], seconds - 1.2),
                          "-map", "0:v", "-map", "[a]", "-t", "%.3f" % seconds, "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(draw(i / float(FPS)).convert("RGB").tobytes())
    p.stdin.close(); p.wait(); return out


def frame_at(pid, where):
    png = "%s/%s_%s.png" % (TMP, pid, where)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + (["-sseof", "-0.2"] if where == "last" else ["-ss", "0.3"]) + ["-i", "assets/voiced/%s.mp4" % pid, "-frames:v", "1", "-vf", "scale=960:540", png], check=True)
    return Image.open(png).convert("RGB")


# ---------- the parts ----------
def title(t):
    im = WOOD.copy(); d = ImageDraw.Draw(im)
    page = Image.new("RGB", (700, 400), PAPER); u = back(t / 0.6)
    im.paste(page, (130, int(lerp(560, 70, u)))); d = ImageDraw.Draw(im); y = int(lerp(560, 70, u))
    if t > 0.7:
        r = int(86 * ease((t - 0.7) / 0.7)); ring(im, 250, y + 200, max(8, r)); d = ImageDraw.Draw(im)
        if t > 1.3: pencil(d, 250 + 60 * math.cos(t * 3), y + 200 + 40 * math.sin(t * 3))
    for k, (word, col, yy, at) in enumerate((("HOW TO", INK, 96, 1.2), ("PLAY THE", INK, 160, 1.5), ("PORTHOLE", RUST, 224, 1.8), ("GAME", TEAL, 304, 2.1))):
        if t >= at: v = ease((t - at) / 0.3); d.text((400 + 40 * (1 - v), y + yy - 40), word, font=F(70 if k > 1 else 54), fill=col)
    return mat(im, None, "Five kids played. Watch them, then it is your turn." if t > 3.0 else "")


RULES = [(0.3, 0, "DRAW", "what is outside your porthole", "Step one. You are the pilot. Draw what is outside your porthole, and write three short lines."),
         (8.2, 1, "PASS IT", "a friend picks a button for Turkey", "Step two. Pass it to a friend. They pick one button for what Turkey thinks, and write three endings."),
         (16.6, 2, "PASS IT AGAIN", "the next friend picks for the trout", "Step three. Pass it again. The next friend picks a button for what the trout think, and writes three more."),
         (25.4, 3, "ROLL", "the die picks the ending", "Then roll the die. The bolt it lands on is the ending that happens.")]
RULES_SECONDS = 32.0


def rules(t):
    im = WOOD.copy(); page = Image.new("RGB", (880, 470), PAPER); im.paste(page, (40, 35)); d = ImageDraw.Draw(im)
    live = max(k for k, r in enumerate(RULES) if t >= r[0]) if t >= RULES[0][0] else -1
    for k, (at, st, head, sub, _) in enumerate(RULES):
        if t < at: continue
        u = back((t - at) / 0.45); x = 70 + k * 212; y = int(lerp(560, 70, u)); col = STEPS[st][2]; on = k == live
        d.rounded_rectangle((x, y, x + 196, y + 400), 14, fill=(255, 253, 246), outline=col, width=6 if on else 2)
        d.ellipse((x + 14, y + 14, x + 62, y + 62), fill=col); d.text((x + 38 - d.textlength(str(k + 1), font=F(30)) / 2, y + 20), str(k + 1), font=F(30), fill=(255, 255, 255) if k else INK)
        cx, cy = x + 98, y + 160; q = t - at
        if k == 0:
            ring(im, cx, cy, 52); d = ImageDraw.Draw(im); n = int(min(1, q / 2.2) * 40)
            pts = [(cx - 34 + j * 1.7, cy + 16 * math.sin(j * 0.5) - 4) for j in range(n)]
            if len(pts) > 1: d.line(pts, fill=(70, 70, 70), width=3)
            px, py = pts[-1] if pts else (cx - 34, cy); pencil(d, px, py, L=70)
        elif k == 1 or k == 2:
            kinds = ["triangle", "circle"] if k == 1 else ["cross", "square"]; pick = 1 if q > 2.4 else None
            for j, kd in enumerate(kinds):
                b = 1 + 0.18 * math.sin(min(1, max(0, (q - 2.4) / 0.3)) * math.pi) if pick == j else 1
                shape(d, kd, cx - 42 + j * 84, cy - 26, int(30 * b), on=(pick is None or pick == j))
            for j in range(3):
                if q > 3.4 + j * 0.7:
                    die(d, cx - 70, cy + 44 + j * 34, 12, j + 1 + (3 if k == 2 else 0)); w = int(min(1, (q - 3.4 - j * 0.7) / 0.5) * 110)
                    d.line((cx - 50, cy + 44 + j * 34, cx - 50 + w, cy + 44 + j * 34), fill=(70, 70, 70), width=3)
        else:
            n = 1 + int(q * 7) % 6 if q < 3.0 else 4; wob = 10 * math.sin(q * 16) * max(0, 1 - q / 3.0)
            die(d, cx + wob, cy - 10 - abs(wob), 44, n)
        f = fit(d, head, 30, 176); d.text((x + 98 - d.textlength(head, font=f) / 2, y + 286), head, font=f, fill=INK)
        words = sub.split(); l1 = " ".join(words[:len(words) // 2 + 1]); l2 = " ".join(words[len(words) // 2 + 1:])
        for j, ln in enumerate((l1, l2)):
            f2 = fit(d, ln, 20, 180, "SemiBold"); d.text((x + 98 - d.textlength(ln, font=f2) / 2, y + 332 + j * 26), ln, font=f2, fill=MUTE)
    return mat(im, RULES[live][1] if live >= 0 else None, ["Draw first.", "A friend picks for Turkey.", "The next friend picks for the trout.", "Roll to see which ending happens."][live] if live >= 0 else "")


def bridge(prev, nxt, n, idx, seconds):
    title_, sub, _ = LESSON[n]
    def draw(t):
        u = ease(t / 1.0); v = ease((t - (seconds - 1.1)) / 1.0)                 # shrink into the porthole, travel, open again
        if v > 0: r = lerp(150, 580, v); cx = lerp(690, 480, v); cy = lerp(290, 270, v)
        else: r = lerp(580, 150, u); cx = lerp(480, 250, u) + (690 - 250) * ease((t - 1.6) / 1.6); cy = lerp(270, 290, u) - 26 * math.sin(math.pi * ease((t - 1.6) / 1.6))
        mix = ease((t - 1.8) / 1.2); src = prev if mix <= 0 else (nxt if mix >= 1 else Image.blend(prev, nxt, mix))
        im = WOOD.copy(); d = ImageDraw.Draw(im)
        if 0 < t < seconds - 0.6:                                                   # the trail the porthole leaves, and the lesson slip
            a = ease((t - 1.6) / 1.6)
            for j in range(int(a * 22)): d.ellipse((250 + j * 20 - 3, 290 - 26 * math.sin(math.pi * j / 22) - 3 + 190, 250 + j * 20 + 3, 290 - 26 * math.sin(math.pi * j / 22) + 3 + 190), fill=(226, 196, 150))
            s = back((t - 2.6) / 0.5)
            if s > 0 and v <= 0:
                sx = int(lerp(-560, 44, s)); slip = Image.new("RGB", (470, 230), PAPER); sd = ImageDraw.Draw(slip)
                sd.rectangle((0, 0, 469, 229), outline=(206, 198, 180), width=3); sd.text((24, 18), "WATCH FOR", font=F(22), fill=RUST)
                words = title_.split(); l1 = " ".join(words[:len(words) // 2 + (len(words) % 2)]); l2 = " ".join(words[len(words) // 2 + (len(words) % 2):])
                for j, ln in enumerate((l1, l2)): sd.text((24, 54 + j * 54), ln, font=fit(sd, ln, 46, 425), fill=INK)
                sd.text((24, 174), sub, font=fit(sd, sub, 26, 425, "SemiBold"), fill=MUTE)
                im.paste(slip.rotate(-3, expand=True, fillcolor=None, resample=Image.BICUBIC), (sx, 150)) if False else im.paste(slip, (sx, 150))
        through(im, src, cx, cy, r)
        if r < 520: ring(im, int(cx), int(cy), int(r))
        if 2.4 < t and v <= 0:                                                      # the number stamps onto the rim
            b = back((t - 2.4) / 0.35); d = ImageDraw.Draw(im); s = str(n); f = F(int(54 * b)); w = d.textlength(s, font=f)
            d.rounded_rectangle((cx - w / 2 - 16, cy + 118, cx + w / 2 + 16, cy + 118 + f.size + 12), 12, fill=INK); d.text((cx - w / 2, cy + 120), s, font=f, fill=PAPER)
        return mat(im, None, "Next: porthole %d" % n if t > 1.0 else "", dots=idx if t > 1.9 else max(0, idx - 1))
    return draw


def film_hints(n):
    """(time, step, hint) through one film, read from its voice script and its sheet."""
    pid = "c%d" % n; g = {}
    for ln in open("films/%s.py" % pid):
        for k in ("T_TURKEY", "T_TROUT", "T_END"):
            if ln.startswith(k + " ") and "#" in ln: g[k] = float(ln.split("#")[1].split()[0].rstrip(":"))
    s = SHEETS[n]; lines = json.load(open("films/notes/%s.voice.json" % pid))["lines"]
    ev = [(0.0, 0, "The pilot draws what is outside.")]
    for ask, l in zip(ASK, lines[:3]): ev.append((l["at"], 0, ask))
    q = 3
    for f, st, key, who in (("first_friend", 1, "T_TURKEY", "Turkey"), ("next_friend", 2, "T_TROUT", "the trout")):
        fr = s[f]; any_ = fr["picked"] or any(fr[k] for k in KIND)
        ev.append((g[key], st, ("A friend picks a button for %s." % who) if fr["picked"] else ("This friend left it blank. That is okay." if not any_ else "A friend writes for %s." % who)))
        for k in KIND:
            if fr[k] and fr[k].get("reads"): ev.append((lines[q]["at"], st, KIND[k])); q += 1
    ev.append((g["T_END"], 3, "Now roll the die to pick the ending."))
    return sorted(ev)


def film(n, idx):
    pid = "c%d" % n; src = "assets/voiced/%s.mp4" % pid; out = "%s/f_%s.mp4" % (TMP, pid); ev = film_hints(n)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", "fps=24,scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a",
                           "-t", "%.3f" % dur, "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        t = i / float(FPS); cur = [e for e in ev if e[0] <= t][-1]
        wr.stdin.write(mat(Image.frombytes("RGB", (W, H), buf), cur[1], cur[2], dots=idx).tobytes()); i += 1
    wr.stdin.close(); wr.wait(); return out


END_SECONDS = 17.0
def ending(last):
    def draw(t):
        im = WOOD.copy(); u = ease(t / 1.0); r = lerp(580, 120, u); through(im, last, lerp(480, 190, u), lerp(270, 250, u), r)
        if r < 520: ring(im, int(lerp(480, 190, u)), int(lerp(270, 250, u)), int(r))
        d = ImageDraw.Draw(im)
        if t > 1.2:
            v = back((t - 1.2) / 0.5); x = int(lerp(980, 370, v)); page = Image.new("RGB", (540, 420), PAPER); im.paste(page, (x, 60)); d = ImageDraw.Draw(im)
            d.text((x + 30, 78), "YOUR TURN", font=F(72), fill=RUST)
            for k, (at, line) in enumerate(((3.6, "Draw what is outside."), (5.6, "Pass it. A friend picks for Turkey."), (8.0, "Pass it again. The trout get a turn."), (10.4, "Roll the die."))):
                if t > at:
                    col = STEPS[k][2]; y = 180 + k * 58; d.ellipse((x + 30, y, x + 74, y + 44), fill=col)
                    d.text((x + 52 - d.textlength(str(k + 1), font=F(26)) / 2, y + 6), str(k + 1), font=F(26), fill=(255, 255, 255) if k else INK)
                    d.text((x + 90, y + 6), line, font=fit(d, line, 27, 420, "Bold"), fill=INK)
            if t > 12.4: d.text((x + 30, 424), "Blank is okay. Wild is good.", font=F(30), fill=TEAL)
        live = max([k for k, at in enumerate((3.6, 5.6, 8.0, 10.4)) if t > at], default=None)
        return mat(im, live, "What is outside YOUR porthole?" if t > 13.6 else "", dots=4)
    return draw


if __name__ == "__main__":
    parts = [segment("title", 7.0, title, [(2.6, "How to play the porthole game. Five kids already played. Watch them. Then it is your turn.", "narrator")],
                     sfx=[(tone, (1.2, 196)), (tone, (1.5, 220)), (tone, (1.8, 262)), (tone, (2.1, 330))]),
             segment("rules", RULES_SECONDS, rules, [(at + 0.4, line, "narrator") for at, _, _, _, line in RULES], sfx=[(tone, (at, 180 + 40 * k)) for k, (at, *_) in enumerate(RULES)])]
    prev = Image.open("%s/rules_last.png" % TMP) if False else rules(RULES_SECONDS - 0.05).crop((FX, FY, FX + FW, FY + FH)).resize((W, H))
    for idx, n in enumerate(ORDER):
        pid = "c%d" % n; nxt = frame_at(pid, "first"); line = LESSON[n][2]; secs = round(len(say(line)) / SR + 4.6, 1)
        parts.append(segment("bridge_%s" % pid, secs, bridge(prev, nxt, n, idx, secs), [(2.6, line, "narrator")],
                             sfx=[(whoosh, (0.1,)), (whoosh, (1.6, 1.4)), (tone, (2.4, 150, 0.2, 0.5)), (whoosh, (secs - 1.2,))]))
        parts.append(film(n, idx)); prev = frame_at(pid, "last"); print("cut", pid, flush=True)
    parts.append(segment("ending", END_SECONDS, ending(prev),
                         [(1.4, "Now it is your turn.", "narrator"), (3.6, "Draw what is outside.", "narrator"), (5.6, "Pass it. A friend picks for Turkey.", "turkey"),
                          (8.0, "Pass it again. The trout get a turn.", "trout"), (10.4, "Roll the die.", "narrator"), (12.4, "Blank is okay. Wild is good. What is outside your porthole?", "narrator")],
                         sfx=[(whoosh, (0.1,))] + [(tone, (at, 196 + 44 * k)) for k, at in enumerate((3.6, 5.6, 8.0, 10.4))]))
    lst = TMP + "/list.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    out = "assets/how-to-play-the-porthole-game.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
