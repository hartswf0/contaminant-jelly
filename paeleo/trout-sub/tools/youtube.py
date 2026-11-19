#!/usr/bin/env python3
"""youtube: the one film for the whole exercise, built to be used with the
Submarine Porthole Log worksheet (tour_key_porthole_worksheet.pdf).

    python3 tools/youtube.py            # youtube/tourkey-trouttown.mp4, chapters.txt, slips.html
    python3 tools/youtube.py --only 7   # just rebuild porthole 7's segment (for checking)

Shape:
  1. How to play: six shots, one per step of the worksheet, with game-style prompts.
  2. The 55 portholes, 12 s each: the locked 8 s unit with prompts, then a 4 s slip card
     holding the three things the pilot copies onto the worksheet (Porthole #, Sub Station,
     Rim Clue & River Rule) and the question for each crewmate.
  3. Close: roll once, trout gossip, black-box message.
Every porthole is its own chapter (12 s, over YouTube's 10 s minimum), so a student
holding slip 23 jumps straight to chapter 23. No fal call is made here.
"""
import concurrent.futures as cf, json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
W, H, FPS = 1280, 720, 24
UNIT, CARD = 8.0, 4.0
F = "/usr/share/fonts/opentype/inter/"
def font(size, weight="Regular"):
    return ImageFont.truetype(F + "Inter-%s.otf" % weight, size)
INK, DIM, AMBER, TEAL, RUST, PANEL = (255, 255, 255, 255), (255, 255, 255, 150), (240, 178, 90, 255), (111, 195, 184, 255), (217, 119, 90, 255), (10, 16, 18, 190)
TMP = tempfile.mkdtemp()
seeds = json.load(open("seeds.json"))
units = json.load(open("units.json")) if os.path.exists("units.json") else {}


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


def panel(d, box, r=10, fill=PANEL):
    d.rounded_rectangle(box, r, fill=fill)


def bolt(d, x, y, n, on, colour):
    """A numbered bolt, like a button glyph in a game prompt."""
    d.ellipse((x, y, x + 34, y + 34), fill=colour if on else (0, 0, 0, 0), outline=colour if on else DIM, width=2)
    f = font(19, "Bold")
    t = str(n)
    d.text((x + 17 - d.textlength(t, font=f) / 2, y + 5), t, font=f, fill=(12, 18, 20, 255) if on else DIM)


def hud(n, row, who):
    """Prompts over the playing unit. who = 'B' (Turkey looks out) or 'C' (Trout look in)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    station = row[0].split("·")[1].strip()
    # top left: the hint, as in a game
    f1, f2 = font(25, "Bold"), font(21)
    clue = wrap(d, row[1], f2, 430)
    panel(d, (28, 26, 28 + 470, 26 + 52 + 28 * len(clue)))
    d.text((46, 38), "Porthole %02d" % n, font=f1, fill=INK)
    d.text((46 + d.textlength("Porthole %02d" % n, font=f1) + 12, 41), "· " + station, font=font(22), fill=AMBER)
    for i, l in enumerate(clue):
        d.text((46, 74 + 28 * i), l, font=f2, fill=INK)
    # top right: slip counter
    t = "SLIP %02d / 55" % n; f = font(21, "SemiBold")
    panel(d, (W - 48 - d.textlength(t, font=f) - 28, 26, W - 28, 70)); d.text((W - 42 - d.textlength(t, font=f), 36), t, font=f, fill=INK)
    # bottom right: the two actions, the live one bright
    rows = [("B", "TURKEY LOOKS OUT", "CREWMATE B", (1, 2, 3), AMBER), ("C", "TROUT LOOK IN", "CREWMATE C", (4, 5, 6), TEAL)]
    y = H - 46 - 2 * 52
    for key, label, crew, nums, col in rows:
        on = key == who
        fl = font(23, "Bold" if on else "Regular")
        x = W - 34
        for b in reversed(nums):
            x -= 40; bolt(d, x, y, b, on, col)
        tw = d.textlength(label, font=fl)
        d.text((x - 22 - tw, y + 3), label, font=fl, fill=INK if on else DIM)
        d.text((x - 22 - tw - 14 - d.textlength(crew, font=font(17, "SemiBold")), y + 8), crew, font=font(17, "SemiBold"), fill=col if on else DIM)
        y += 52
    # bottom left: the question for that crewmate
    q = row[3] if who == "B" else row[4]; col = AMBER if who == "B" else TEAL
    fq = font(30, "SemiBold"); lines = wrap(d, q, fq, 560)
    hgt = 46 + 38 * len(lines)
    panel(d, (28, H - 34 - hgt, 28 + 610, H - 34))
    d.text((46, H - 34 - hgt + 12), "Turkey looking out asks" if who == "B" else "The trout looking in ask", font=font(18, "SemiBold"), fill=col)
    for i, l in enumerate(lines):
        d.text((46, H - 34 - hgt + 38 + 38 * i), l, font=fq, fill=INK)
    p = "%s/hud_%02d_%s.png" % (TMP, n, who); im.save(p); return p


def card(n, row):
    """The slip card held after the unit: what to copy onto the worksheet."""
    im = Image.new("RGBA", (W, H), (6, 12, 14, 150)); d = ImageDraw.Draw(im)
    station = row[0].split("·")[1].strip()
    x0, y0, x1, y1 = 150, 78, W - 150, H - 78
    d.rounded_rectangle((x0, y0, x1, y1), 18, fill=(246, 241, 228, 250))
    ink, soft = (22, 43, 52, 255), (95, 108, 112, 255)
    d.text((x0 + 40, y0 + 26), "SLIP", font=font(24, "Bold"), fill=(176, 122, 40, 255))
    d.text((x0 + 40, y0 + 50), "%02d" % n, font=font(104, "ExtraBold"), fill=ink)
    d.text((x0 + 210, y0 + 34), "Copy onto your Submarine Porthole Log", font=font(22, "SemiBold"), fill=soft)
    y = y0 + 72
    for label, val in (("Porthole #", "%02d" % n), ("Sub Station", station), ("Rim Clue", row[1]), ("River Rule", row[5])):
        d.text((x0 + 210, y + 4), label, font=font(19, "SemiBold"), fill=soft)
        for l in wrap(d, val, font(27, "SemiBold"), x1 - x0 - 420):
            d.text((x0 + 360, y), l, font=font(27, "SemiBold"), fill=ink); y += 34
        y += 8
    y = max(y + 6, y0 + 300)
    d.line((x0 + 40, y, x1 - 40, y), fill=(200, 190, 165, 255), width=2); y += 18
    for crew, nums, who, q, col in (("Crewmate B", "bolts 1 2 3", "Turkey looks out", row[3], (176, 122, 40, 255)), ("Crewmate C", "bolts 4 5 6", "Trout look in", row[4], (38, 120, 112, 255))):
        d.text((x0 + 40, y), crew, font=font(21, "Bold"), fill=col)
        d.text((x0 + 40, y + 26), nums + " · " + who, font=font(17), fill=soft)
        for l in wrap(d, q, font(26, "SemiBold"), x1 - x0 - 330):
            d.text((x0 + 290, y + 2), l, font=font(26, "SemiBold"), fill=ink); y += 32
        y += 30
    p = "%s/card_%02d.png" % (TMP, n); im.save(p); return p


def caption(title, body, tag=None):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fb = font(27); lines = wrap(d, body, fb, W - 150)
    hgt = 78 + 36 * len(lines)
    panel(d, (28, H - 30 - hgt, W - 28, H - 30), 12)
    d.text((52, H - 30 - hgt + 16), title, font=font(34, "Bold"), fill=AMBER)
    if tag:
        f = font(20, "SemiBold"); d.text((W - 52 - d.textlength(tag, font=f), H - 30 - hgt + 26), tag, font=f, fill=TEAL)
    for i, l in enumerate(lines):
        d.text((52, H - 30 - hgt + 62 + 36 * i), l, font=fb, fill=INK)
    p = "%s/cap_%d.png" % (TMP, abs(hash(title)) % 10**8); im.save(p); return p


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "48",
       "-c:a", "aac", "-b:a", "112k", "-ar", "44100", "-ac", "2", "-video_track_timescale", "12288"]
def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + list(a), check=True)


def porthole(n):
    row, pid = seeds[n - 1], "p%02d" % n
    cut = (units.get(pid) or {}).get("cut") or 6.0
    out = "%s/seg_%02d.mp4" % (TMP, n)
    fc = ("[0:v]fps=24,scale=%d:%d:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=%f[v0];"
          "[v0][1:v]overlay=enable='lt(t,%f)'[v1];[v1][2:v]overlay=enable='between(t,%f,%f)'[v2];"
          "[3:v]format=rgba,fade=t=in:st=%f:d=0.35:alpha=1[c];[v2][c]overlay=enable='gte(t,%f)',format=yuv420p[v];"
          "[0:a]apad,atrim=0:%f[a]" % (W, H, CARD, cut, cut, UNIT, UNIT, UNIT, UNIT + CARD))
    ff("-i", "units/%s.mp4" % pid, "-loop", "1", "-t", str(UNIT + CARD), "-i", hud(n, row, "B"),
       "-loop", "1", "-t", str(UNIT + CARD), "-i", hud(n, row, "C"), "-loop", "1", "-t", str(UNIT + CARD), "-i", card(n, row),
       "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(UNIT + CARD), *ENC, out)
    return out


HOWTO = [
    ("films/intro-6.mp4", 2.6, 5.4, "TOURKEY TROUTTOWN", "Turkey takes a tour of Trout Town. 55 portholes. Find the number on your slip.", None),
    ("films/intro-1.mp4", 0.0, 7.0, "Pilot: take Turkey's seat", "On the front of your log write your Porthole #, Sub Station, Rim Clue and River Rule. Draw what Turkey sees right now.", "FRONT · 6 MIN"),
    ("films/intro-2.mp4", 1.0, 7.0, "Pilot: three lines", "1 What we see outside the glass. 2 My sub command: lamp or ballast. 3 The risk to our 24 hours of air. Then pass your porthole left.", "FRONT · 6 MIN"),
    ("films/intro-3.mp4", 1.0, 7.0, "Crewmates B and C: six bolts", "B writes bolts 1, 2, 3 for Turkey looking out. Pass left again. C writes bolts 4, 5, 6 for the trout looking in.", "BACK · 12 MIN"),
    ("films/intro-4.mp4", 2.0, 6.0, "Pilot: roll once", "Each crewmate wrote one Probable, one Plausible and one Preposterous. Roll 1d6 and circle that bolt.", "BACK · 12 MIN"),
    ("films/intro-5.mp4", 2.0, 6.0, "Tell the river, tell the surface", "Trout gossip: what do the trout tell FANTROL 88.7? Black-box message: Dear Alien, why did the Turkey come to Trout Town?", "BACK · 12 MIN"),
]
CLOSE = [
    ("films/intro-4.mp4", 2.0, 6.0, "Pilot: roll once", "Your log is back. Roll 1d6 and circle the bolt that happened.", None),
    ("films/intro-5.mp4", 2.0, 6.0, "Send it up", "Write the trout gossip and your black-box message. Hand your clue to the next pilot.", None),
]
def shot(i, spec, tag):
    src, ss, t, title, body, label = spec
    out = "%s/%s_%d.mp4" % (TMP, tag, i)
    fc = ("[0:v]fps=24,scale=%d:%d:flags=lanczos,setsar=1[v0];[v0][1:v]overlay,format=yuv420p[v];"
          "[0:a]apad,atrim=0:%f,afade=t=in:d=0.2,afade=t=out:st=%f:d=0.25[a]" % (W, H, t, t - 0.25))
    ff("-ss", str(ss), "-t", str(t), "-i", src, "-loop", "1", "-t", str(t), "-i", caption(title, body, label),
       "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(t), *ENC, out)
    return out, t


def slips(times):
    """55 numbered slips to print and cut: one per student. The number is the chapter."""
    cells = "".join(
        '<div class="slip"><div class="n">%02d</div><div class="t"><b>%s</b><span>Chapter %02d · at %s</span>'
        '<i>Copy the Rim Clue and River Rule from the slip card.</i></div></div>'
        % (n, seeds[n - 1][0].split("·")[1].strip(), n, stamp(times[n])) for n in range(1, 56))
    open("youtube/slips.html", "w").write("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Tourkey Trouttown · Slips</title><style>
@page{size:letter;margin:10mm}*{box-sizing:border-box}body{margin:0;font:13px/1.3 Inter,Arial,sans-serif;color:#162b34;background:#fff}
h1{font-size:15px;margin:0 0 2mm}p{margin:0 0 4mm;color:#5f6c70;font-size:11px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0}
.slip{display:flex;gap:3mm;align-items:center;border:1px dashed #9aa8ad;padding:3mm 3.5mm;height:21mm;break-inside:avoid}
.n{font-size:34px;font-weight:800;min-width:17mm}.t b{display:block;font-size:14px}.t span{display:block;color:#b07a28;font-weight:600;font-size:11px}
.t i{display:block;font-style:normal;color:#5f6c70;font-size:9.5px}
@media(max-width:700px){.grid{grid-template-columns:1fr 1fr}}</style></head><body>
<h1>TOURKEY TROUTTOWN · 55 slips</h1><p>Print, cut on the dashed lines, one slip per pilot. The slip number is the Porthole # on the Submarine Porthole Log and the chapter in the film.</p>
<div class="grid">%s</div></body></html>""" % cells)


def stamp(s):
    return "%d:%02d" % (int(s) // 60, int(s) % 60)


if __name__ == "__main__":
    if "--only" in sys.argv:
        n = int(sys.argv[sys.argv.index("--only") + 1])
        os.replace(porthole(n), "youtube/sample_%02d.mp4" % n); print("youtube/sample_%02d.mp4" % n); sys.exit()
    os.makedirs("youtube", exist_ok=True)
    parts, chapters, t = [], [], 0.0
    chapters.append((0, "How to play"))
    for i, spec in enumerate(HOWTO):
        p, d = shot(i, spec, "how"); parts.append(p); t += d
    first = t
    with cf.ThreadPoolExecutor(4) as ex:
        segs = list(ex.map(porthole, range(1, 56)))
    times = {}
    for n, p in enumerate(segs, 1):
        row = seeds[n - 1]
        chapters.append((t, "%02d %s · %s" % (n, row[0].split("·")[1].strip(), row[1]))); times[n] = t
        parts.append(p); t += UNIT + CARD
    chapters.append((t, "Roll once and send it up"))
    for i, spec in enumerate(CLOSE):
        p, d = shot(i, spec, "close"); parts.append(p); t += d
    lst = TMP + "/list.txt"
    open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", "youtube/tourkey-trouttown.mp4")
    open("youtube/chapters.txt", "w").write("\n".join("%s %s" % (stamp(s), name) for s, name in chapters) + "\n")
    json.dump({"length": round(t, 2), "first_porthole": first, "seconds_per_porthole": UNIT + CARD,
               "portholes": {("%02d" % n): stamp(s) for n, s in times.items()}}, open("youtube/timing.json", "w"), indent=1)
    slips(times)
    print("youtube/tourkey-trouttown.mp4  %s  %d chapters" % (stamp(t), len(chapters)))
