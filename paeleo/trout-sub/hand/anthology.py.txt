#!/usr/bin/env python3
"""anthology: the five hand films cut into one, written backwards from its ending.

    python3 anthology.py     # assets/nobody-is-holding-the-chalk.mp4

The ending was fixed first: the tools in every film move with no hand on them because the makers are the
trout. Room 4's art class has been making us a turkey. Everything before it plants that: a bold number card
before each film names the tool and says that nobody is holding it. The last film is the chalkboard, because
it ends in Room 4, where the camera then pulls back to the desk and the class around it.
"""
import math, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import voice_pass as VP
W, H, FPS, SR = 960, 540, 24, 44100
DEEP, CREAM, RUST, GOLD, TEAL = (14, 30, 40), (251, 246, 233), (201, 92, 62), (214, 158, 60), (72, 160, 150)
F = lambda size, w="Black": ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-%s.otf" % w, size)
ORDER = [("p01", "SCISSORS", "Watch the scissors. Nobody is holding them."),
         ("p14", "A SCALPEL", "A leaf gets cut. You never see who cuts it."),
         ("p35", "PINS", "Somebody pins these down. Somebody very careful."),
         ("p44", "A PEN", "Somebody inks a wheel of words."),
         ("p03", "CHALK", "And nobody is holding the chalk.")]
TMP = tempfile.mkdtemp()
ease = lambda u: (lambda v: v * v * (3 - 2 * v))(min(1.0, max(0.0, u)))
back = lambda u: (lambda v: v * v * (2.7 * v + 1.7) + 1)(min(1.0, max(0.0, u)) - 1)


def segment(name, seconds, draw, lines=(), ticks=(), bed=None):
    """Render frames from draw(t) and a soundtrack of spoken lines [(at, text, who)] into one mp4."""
    n = int(seconds * FPS); out = "%s/%s.mp4" % (TMP, name)
    y = np.zeros(int((seconds + 0.5) * SR), np.float32)
    for at, text, who in lines:
        clip = VP.speak(text, who); i = int(at * SR); clip = clip[:max(0, len(y) - i)]; y[i:i + len(clip)] += clip * 1.3
    for at, f0 in ticks:
        m = int(0.25 * SR); t = np.arange(m) / float(SR); i = int(at * SR)
        y[i:i + m] += (np.sin(2 * np.pi * f0 * t) * np.exp(-t * 22) * 0.5).astype(np.float32)[:len(y) - i]
    wav = "%s/%s.wav" % (TMP, name); sf.write(wav, np.clip(y, -1, 1), SR)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-i", wav] +
                         (["-ss", str(bed[1]), "-i", bed[0], "-filter_complex", "[2:a]volume=%.2f,afade=t=in:d=1,afade=t=out:st=%.2f:d=2[m];[1:a][m]amix=inputs=2:normalize=0[a]" % (bed[2], seconds - 2),
                           "-map", "0:v", "-map", "[a]"] if bed else ["-map", "0:v", "-map", "1:a"]) +
                         ["-t", str(seconds), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(draw(i / float(FPS)).convert("RGB").tobytes())
    p.stdin.close(); p.wait(); return out


def slab(d, x, y, word, size, fill, ink=DEEP, skew=10):
    w = d.textlength(word, font=F(size))
    d.polygon([(x - 26, y + 4), (x + w + 30, y - skew), (x + w + 20, y + size * 1.18), (x - 34, y + size * 1.1)], fill=fill)
    d.text((x, y - size * 0.02), word, font=F(size), fill=ink)


def title(t):
    im = Image.new("RGB", (W, H), DEEP); d = ImageDraw.Draw(im)
    for j in range(40):                                        # chalk dust drifting up
        a = j * 2.4; x = 480 + 420 * math.sin(a * 1.7); yy = (540 - (t * 40 + j * 37) % 600)
        d.ellipse((x - 2, yy - 2, x + 2, yy + 2), fill=(90, 110, 115))
    for k, (word, col, yy, at) in enumerate((("NOBODY IS", CREAM, 96, 0.4), ("HOLDING", GOLD, 216, 0.9), ("THE CHALK", RUST, 336, 1.4))):
        if t >= at:
            u = back((t - at) / 0.45); slab(d, int(-700 + 770 * u), yy, word, 104, col)
    if t > 2.4:
        d.text((72, 476), "Five portholes, made by hand", font=F(30, "Bold"), fill=CREAM)
    return im


def number_card(pid, tool):
    def draw(t):
        im = Image.new("RGB", (W, H), DEEP); d = ImageDraw.Draw(im)
        u = back(t / 0.4); slab(d, int(-500 + 566 * u), 120, pid[1:], 230, RUST, CREAM, 16)
        if t > 0.5:
            v = ease((t - 0.5) / 0.4); d.text((470, 170 + 20 * (1 - v)), tool, font=F(76), fill=GOLD)
            d.text((474, 262 + 20 * (1 - v)), "NO HAND.", font=F(76), fill=CREAM)
        return im
    return draw


def knock(img, tol=42):
    """Cut a figure from its paper ground: transparent wherever the colour is close to the corner colour."""
    im = img.convert("RGB"); a = np.asarray(im).astype(np.int16); bg = a[4:20, 4:20].reshape(-1, 3).mean(0)
    dist = np.abs(a - bg).sum(2); alpha = np.clip((dist - tol) * 6, 0, 255).astype(np.uint8)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.2))); return out


def ending(last_frame):
    trout = knock(Image.open("films/sources/p01/trout.jpg"))
    box = trout.getbbox(); trout = trout.crop(box)
    sc = Image.open("films/sources/p01/scissors.png").convert("L"); scis = Image.new("RGBA", sc.size, (30, 30, 34, 255)); scis.putalpha(Image.eval(sc, lambda v: 255 - v))
    def fish(scale, flip, rot):
        f = trout.resize((int(trout.size[0] * scale), int(trout.size[1] * scale)), Image.LANCZOS)
        if flip: f = f.transpose(Image.FLIP_LEFT_RIGHT)
        return f.rotate(rot, expand=True, resample=Image.BICUBIC)
    SEATS = [(60, 300, 0.36, False, 8), (650, 320, 0.36, True, -8), (120, 40, 0.30, False, -14), (620, 30, 0.30, True, 12)]
    def draw(t):
        u = ease((t - 2.2) / 2.6)                                  # the pull-back
        im = Image.new("RGB", (W, H), (20, 66, 72)); d = ImageDraw.Draw(im)
        for i in range(9):                                         # desk planks, under water
            d.rectangle((0, 150 + i * 46, W, 150 + i * 46 + 44), fill=(96 - i * 3, 70 - i * 2, 44))
        d.rectangle((0, 0, W, 150), fill=(18, 58, 64))
        s = 1 - 0.56 * u; fw, fh = int(W * s), int(H * s); fx, fy = (W - fw) // 2, int((H - fh) / 2 + 20 * u)
        if u > 0:
            d.rectangle((fx + 10, fy + 12, fx + fw + 10, fy + fh + 12), fill=(30, 22, 14))
            d.rectangle((fx - 8, fy - 8, fx + fw + 8, fy + fh + 8), fill=CREAM)
        im.paste(last_frame.resize((fw, fh), Image.LANCZOS), (fx, fy))
        if u > 0.25:
            for k, (x, y, scale, flip, rot) in enumerate(SEATS):
                v = back((u - 0.25 - k * 0.08) / 0.5)
                if v <= 0: continue
                f = fish(scale, flip, rot + 3 * math.sin(t * 2 + k)); dx = (-420 if not flip else 420) * (1 - v)
                im.paste(f, (int(x + dx), int(y + 6 * math.sin(t * 1.6 + k))), f)
            if u > 0.6:
                im.paste(scis.resize((150, 48)).rotate(24, expand=True), (300, 420), scis.resize((150, 48)).rotate(24, expand=True))
                d = ImageDraw.Draw(im); d.rounded_rectangle((590, 452, 660, 468), 4, fill=(244, 241, 232), outline=(120, 120, 120))
        d = ImageDraw.Draw(im)
        tint = Image.new("RGB", (W, H), (30, 110, 110)); im = Image.blend(im, tint, 0.16 * u); d = ImageDraw.Draw(im)
        for j in range(26):
            x = (j * 97) % W; yy = (540 - (t * 60 + j * 53) % 620); r = 2 + j % 4
            d.ellipse((x - r, yy - r, x + r, yy + r), outline=(190, 230, 225))
        if t > 5.6:
            slab(d, 60, 24, "ROOM 4", 70, GOLD); d.text((372, 40), "ART CLASS", font=F(46), fill=CREAM)
        if t > 11.2:
            a = ease((t - 11.2) / 0.6); blk = Image.new("RGB", (W, H), DEEP); im = Image.blend(im, blk, a); d = ImageDraw.Draw(im)
            if t > 12.0:
                d.text((70, 170), "WHAT WILL YOU", font=F(96), fill=CREAM); d.text((70, 280), "MAKE THEM?", font=F(96), fill=GOLD)
        return im
    return draw


if __name__ == "__main__":
    parts = [segment("title", 5.2, title, [(2.0, "Five things get made in this film. Watch who makes them.", "narrator")], ticks=[(0.4, 220), (0.9, 262), (1.4, 330)])]
    for pid, tool, line in ORDER:
        parts.append(segment("card_" + pid, 3.6, number_card(pid, tool), [(0.5, line, "narrator")], ticks=[(0.0, 180)]))
        norm = "%s/n_%s.mp4" % (TMP, pid)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "assets/voiced/%s.mp4" % pid, "-vf", "fps=24,scale=960:540,setsar=1", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", norm], check=True)
        parts.append(norm)
    lastpng = TMP + "/last.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.3", "-i", "assets/films/p03.mp4", "-frames:v", "1", lastpng], check=True)
    parts.append(segment("ending", 16.5, ending(Image.open(lastpng).convert("RGB")),
                         [(0.4, "So. Who made all this?", "narrator"), (6.0, "We did. We made you a turkey.", "trout"), (12.2, "Now. What will you make us?", "trout")],
                         ticks=[(5.6, 392), (12.0, 196)], bed=("../music/the-selkies-cradle.ogg", 40, 0.3)))
    lst = TMP + "/list.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    out = "assets/nobody-is-holding-the-chalk.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
