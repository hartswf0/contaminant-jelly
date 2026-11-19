#!/usr/bin/env python3
"""cards: the drawn parts of the film. Title sequence, instruction cards and dive cards.

Two borrowed disciplines, both used on our own shapes:
- cut-paper blocks and bars that slide and slam, heavy type on offset slabs;
- harmonic motion: points on rings whose speeds are whole-number multiples of one
  another, so they scatter into patterns and all come home at the same instant.
Here the points that come home are the six bolts of the porthole.

Every instruction card shows the real worksheet (sheets/tour_key_porthole_worksheet.pdf)
with the command being explained lit up, in the worksheet's own words, beside the film.
"""
import math, os
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1280, 720, 24
PAPER, NAVY, DEEP, GOLD, RUST, TEAL, CREAM = (246, 241, 228), (22, 43, 52), (14, 30, 40), (214, 158, 60), (201, 92, 62), (72, 160, 150), (251, 246, 233)
FD = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(size, weight="Regular"):
    k = (int(size), weight)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + "Inter-%s.otf" % weight, int(size))
    return _fc[k]
def bgr(im):
    return np.array(im.convert("RGB"))[:, :, ::-1].copy()
def ease(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
def back(u, s=1.7):
    """Ease out with a small overshoot, for things that slam into place."""
    u = min(1.0, max(0.0, u)) - 1; return u * u * ((s + 1) * u + s) + 1
def span(t, a, b):
    return (t - a) / float(b - a)


_ws = {}
def sheet(page):
    if page not in _ws:
        _ws[page] = Image.open(os.path.join(ROOT, "sheets/ws-%d.png" % page)).convert("RGB")
    return _ws[page]


def harmonic(d, cx, cy, t, period, rings, home=1.0, colour=GOLD, alpha=255):
    """Whitney motion. rings = [(radius, count, dot radius, multiplier)]. Point j on a ring turns
    at (j+1) x multiplier turns per period, so every point is back at its start when t = period.
    home eases the angles toward that start so the pattern can be made to land."""
    for radius, count, dot, mult in rings:
        for j in range(count):
            base = 2 * math.pi * j / count - math.pi / 2
            ang = base + 2 * math.pi * (j + 1) * mult * (t / period) * (1 - home)
            x, y = cx + radius * math.cos(ang), cy + radius * math.sin(ang)
            d.ellipse((x - dot, y - dot, x + dot, y + dot), fill=colour + (alpha,))


def porthole(d, cx, cy, r, sweep=1.0, bolts=1.0):
    """The six-bolt brass ring, drawn flat."""
    if sweep > 0:
        box = (cx - r, cy - r, cx + r, cy + r)
        d.arc(box, -90, -90 + 360 * sweep, fill=GOLD + (255,), width=max(3, int(r * 0.2)))
        ri = r * 0.78
        d.arc((cx - ri, cy - ri, cx + ri, cy + ri), -90, -90 + 360 * sweep, fill=NAVY + (255,), width=3)
    for j in range(6):
        if bolts * 6 > j:
            a = 2 * math.pi * j / 6 - math.pi / 2
            x, y = cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)
            q = r * 0.055
            d.regular_polygon((x, y, q * 1.7), 6, rotation=0, fill=CREAM + (255,), outline=NAVY + (255,))


def bars(im, u, colours=(RUST, GOLD, TEAL, NAVY, RUST), direction=1):
    """Cut-paper bars sweep across and off. u 0..1: 0-0.5 cover, 0.5-1 uncover."""
    d = ImageDraw.Draw(im); n = len(colours); h = H / float(n)
    for i, c in enumerate(colours):
        lag = 0.06 * i
        cover = ease(span(u, lag, 0.45 + lag)); clear = ease(span(u, 0.5 + lag, 0.95 + lag))
        if direction > 0:
            x0, x1 = W * clear, W * cover
        else:
            x0, x1 = W * (1 - cover), W * (1 - clear)
        if x1 - x0 > 1:
            d.rectangle((x0, i * h, x1, (i + 1) * h + 1), fill=c)
    return im


def circle_film(frame, size):
    """A square crop of a film frame as an RGBA disc."""
    h, w = frame.shape[:2]; s = min(h, w)
    crop = frame[(h - s) // 2:(h + s) // 2, (w - s) // 2:(w + s) // 2]
    im = Image.fromarray(cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)[:, :, ::-1])
    m = Image.new("L", (size * 2, size * 2), 0); ImageDraw.Draw(m).ellipse((4, 4, size * 2 - 4, size * 2 - 4), fill=255)
    im.putalpha(m.resize((size, size), Image.LANCZOS)); return im


def title(film, n1=int(5.6 * FPS)):
    """Frames for the opening title. film: frames (1136x639 BGR) of the Trout Town shot that the
    porthole opens onto. Yields 1280x720 BGR frames."""
    cx, cy, R = 930, 330, 190
    period = 3.0
    for i in range(n1):
        t = i / float(FPS)
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        # 0-3 s: the harmonic field scatters and comes home as the six bolts
        home = ease(span(t, 2.2, 3.0))
        a = int(255 * ease(span(t, 0.0, 0.5)))
        harmonic(d, cx, cy, min(t, period), period, [(R * 1.55, 36, 3, 1), (R * 1.25, 24, 4, 1), (R * 0.55, 12, 4, 2)], home, TEAL, int(a * (1 - ease(span(t, 2.6, 3.4)))))
        harmonic(d, cx, cy, min(t, period), period, [(R * 0.9, 6, 10, 1)], home, GOLD, a)
        porthole(d, cx, cy, R, sweep=ease(span(t, 2.7, 3.5)), bolts=1.0 if t > 3.0 else 0)
        if t > 3.3:                                               # the glass fills with river
            g = R * 0.76 * back(span(t, 3.3, 3.9), 1.2)
            d.ellipse((cx - g, cy - g, cx + g, cy + g), fill=TEAL + (255,))
        # 3.1 s on: slabs slam in from the left with the title
        for k, (word, col, y, delay, sz) in enumerate((("TOURKEY", RUST, 190, 3.1, 132), ("TROUTTOWN", GOLD, 340, 3.35, 104))):
            u = back(span(t, delay, delay + 0.45))
            if t >= delay:
                wd = d.textlength(word, font=font(sz, "Black"))
                x = -wd - 120 + (wd + 190) * u
                d.polygon([(x - 40, y - 8), (x + wd + 46, y - 20 + 10 * k), (x + wd + 30, y + sz + 22), (x - 52, y + sz + 12)], fill=col + (255,))
                d.text((x, y - sz * 0.04), word, font=font(sz, "Black"), fill=DEEP + (255,))
        if t > 3.9:
            u = ease(span(t, 3.9, 4.5)); s = "Turkey takes a tour of Trout Town"
            d.text((74, 500 + 30 * (1 - u)), s, font=font(40, "SemiBold"), fill=CREAM + (int(255 * u),))
            d.text((76, 556 + 30 * (1 - u)), "55 PORTHOLES  ·  ONE SLIP EACH  ·  ONE WORKSHEET", font=font(21, "Bold"), fill=TEAL + (int(255 * u),))
        yield bgr(im)
    # the porthole opens onto the town: the glass grows until the picture fills its box
    BX, BY, BW, BH = 72, 16, 1136, 639
    last = im
    n2 = len(film)
    yy, xx = np.mgrid[:H, :W]
    for i in range(n2):
        u = ease(span(i, 0, 1.3 * FPS))
        base = bgr(last).astype(np.float32)
        page = np.full((H, W, 3), PAPER[::-1], np.float32)
        page[BY:BY + BH, BX:BX + BW] = film[i]
        ccx, ccy = cx + (BX + BW / 2 - cx) * u, cy + (BY + BH / 2 - cy) * u
        rad = R * 0.76 + (900 - R * 0.76) * u * u
        m = np.clip((rad - np.hypot(xx - ccx, yy - ccy)) / 6.0 + 0.5, 0, 1)[..., None]
        fr = base * (1 - m) + page * m
        im2 = Image.fromarray(fr.astype(np.uint8)[:, :, ::-1]); d = ImageDraw.Draw(im2)
        if u > 0.98:
            d.rounded_rectangle((BX - 3, BY - 3, BX + BW + 2, BY + BH + 2), 16, outline=NAVY, width=3)
            a = ease(span(i, 1.3 * FPS, 1.9 * FPS))
            col = tuple(int(PAPER[k] + (NAVY[k] - PAPER[k]) * a) for k in range(3))
            d.text((BX, BY + BH + 14), "Find the number on your slip. That is your porthole.", font=font(26, "Bold"), fill=col)
        yield bgr(im2)


# One card per command on the worksheet. crop and lights are in PDF points (612 x 792 page).
CARDS = [
    dict(num="1", page=1, crop=(28, 22, 584, 132), chip="FRONT · PILOT A · 6 MIN", title="COPY YOUR SLIP",
         say="Porthole #, Sub Station, Rim Clue & River Rule.",
         lights=[(262, 82, 392, 101), (398, 82, 580, 101), (34, 107, 580, 127)], film=("films/intro-1.mp4", 0.0)),
    dict(num="2", page=1, crop=(120, 130, 492, 420), chip="FRONT · PILOT A · 6 MIN", title="DRAW WHAT THE TURKEY SEES RIGHT NOW",
         say="Trout Town outside the glass, inside your six bolts.",
         lights=[(180, 134, 430, 157), (205, 397, 405, 419)], film=("films/intro-3.mp4", 2.0)),
    dict(num="3", page=1, crop=(28, 424, 584, 688), chip="FRONT · PILOT A · 6 MIN", title="E · P · O?  THEN PASS YOUR PORTHOLE LEFT",
         say="What we see. My sub command. The risk to our 24 hours of air.",
         lights=[(34, 428, 580, 497), (34, 503, 580, 572), (34, 578, 580, 647), (34, 653, 580, 684)], film=("films/intro-2.mp4", 1.0)),
    dict(num="4", page=2, crop=(28, 100, 584, 462), chip="BACK · B & C + ROLL · 12 MIN", title="SIX BOLTS AROUND THE PORTHOLE",
         say="B: River Witness #1, bolts 1 2 3. Pass left again. C: River Witness #2, bolts 4 5 6.",
         lights=[(34, 110, 260, 430), (34, 433, 260, 459), (352, 110, 580, 430), (352, 433, 580, 459)], film=("units/p07.mp4", 5.6)),
    dict(num="5", page=2, crop=(28, 262, 584, 508), chip="BACK · B & C + ROLL · 12 MIN", title="PILOT A ROLLS ONCE",
         say="Return to the original pilot. Roll 1d6. Write I ROLLED, or circle the bolt.",
         lights=[(352, 433, 580, 459), (258, 270, 354, 380), (34, 478, 580, 502)], film=("films/intro-4.mp4", 2.4)),
    dict(num="6", page=2, crop=(28, 474, 584, 648), chip="BACK · B & C + ROLL · 12 MIN", title="TROUT GOSSIP · BLACK-BOX MESSAGE",
         say="What do the trout tell FANTROL 88.7?  Dear Alien, why did the Turkey come to Trout Town?",
         lights=[(34, 503, 580, 562), (34, 566, 580, 644)], film=("films/intro-5.mp4", 2.0)),
]


def card(spec, film, n, first=False):
    """Frames for one instruction card. film: at least n square-croppable BGR frames."""
    pg = sheet(spec["page"]); k = pg.size[0] / 612.0
    x0, y0, x1, y1 = spec["crop"]
    crop = pg.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k)))
    AW, AH = 730, 456
    s = min(AW / float(crop.size[0]), AH / float(crop.size[1]))
    pw, ph = int(crop.size[0] * s), int(crop.size[1] * s)
    crop = crop.resize((pw, ph), Image.LANCZOS)
    px, py = 60 + (AW - pw) // 2, 204 + (AH - ph) // 2
    fcx, fcy, fr_ = 1040, 432, 190
    per = max(1.0, (n / float(FPS) - 1.6) / len(spec["lights"]))
    for i in range(n):
        t = i / float(FPS)
        im = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(im)
        # slab and numeral
        u = back(span(t, 0.25, 0.7))
        d.polygon([(0, 26), (150 * u + 20, 18), (138 * u + 14, 176), (0, 184)], fill=RUST + (255,))
        d.text((38 - 160 * (1 - u), 20), spec["num"], font=font(150, "Black"), fill=PAPER + (255,))
        # the worksheet's own words
        u2 = ease(span(t, 0.4, 0.9))
        tf = font(46, "Black"); size = 46
        while d.textlength(spec["title"], font=tf) > W - 250 and size > 26:
            size -= 2; tf = font(size, "Black")
        d.text((196 + 60 * (1 - u2), 44), spec["title"], font=tf, fill=NAVY + (int(255 * u2),))
        d.text((198 + 60 * (1 - u2), 44 + size + 14), spec["say"], font=font(24, "SemiBold"), fill=NAVY + (int(215 * u2),))
        cw = d.textlength(spec["chip"], font=font(17, "Bold")) + 28
        d.rounded_rectangle((198, 150, 198 + cw, 182), 8, fill=(251, 243, 223, int(255 * u2)), outline=GOLD + (int(255 * u2),), width=2)
        d.text((212, 156), spec["chip"], font=font(17, "Bold"), fill=NAVY + (int(255 * u2),))
        # the worksheet itself rises into place
        u3 = back(span(t, 0.5, 1.05), 1.0); oy = int((1 - u3) * 560)
        d.rectangle((px + 8, py + 10 + oy, px + pw + 8, py + ph + 10 + oy), fill=(22, 43, 52, 60))
        im.paste(crop, (px, py + oy))
        d.rectangle((px, py + oy, px + pw, py + ph + oy), outline=NAVY + (255,), width=2)
        # each command lights in turn, and stays faintly lit
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for j, (a0, b0, a1, b1) in enumerate(spec["lights"]):
            ts = 1.2 + j * per
            if t < ts:
                continue
            wipe = ease(span(t, ts, ts + 0.35)); live = t < ts + per
            X0, Y0 = px + (a0 - x0) * k * s, py + (b0 - y0) * k * s
            X1, Y1 = px + (a1 - x0) * k * s, py + (b1 - y0) * k * s
            od.rectangle((X0, Y0, X0 + (X1 - X0) * wipe, Y1), fill=GOLD + (95 if live else 40,))
            if live and wipe >= 1:
                od.rectangle((X0 - 3, Y0 - 3, X1 + 3, Y1 + 3), outline=RUST + (255,), width=4)
        im.alpha_composite(ov)
        # the film in a porthole, bolts turning in harmonic steps
        u4 = back(span(t, 0.6, 1.1), 1.3)
        if u4 > 0:
            r = int(fr_ * u4)
            if r > 8:
                disc = circle_film(film[min(i, len(film) - 1)], 2 * int(r * 0.8))
                im.alpha_composite(disc, (fcx - disc.size[0] // 2, fcy - disc.size[1] // 2))
                d = ImageDraw.Draw(im)
                porthole(d, fcx, fcy, r, 1.0, 0)
                harmonic(d, fcx, fcy, t, 6.0, [(r * 0.9, 6, 7, 1)], home=0.0, colour=CREAM)
                harmonic(d, fcx, fcy, t, 6.0, [(r * 1.18, 12, 3, 1)], home=0.0, colour=TEAL)
        if not first and t < 0.75:
            bars(im, 0.5 + t / 1.5, direction=1 if int(spec["num"]) % 2 else -1)       # bars leaving
        if n - i <= int(0.75 * FPS):
            bars(im, (1 - (n - i) / (0.75 * FPS)) * 0.5, direction=-1 if int(spec["num"]) % 2 else 1)   # bars arriving
        yield bgr(im)


def dive_card(name, a, b, song, n):
    """Frames for a dive title: the numeral slams in, the slips of this dive orbit and line up."""
    count = b - a + 1
    for i in range(n):
        t = i / float(FPS); T = n / float(FPS)
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        home = ease(span(t, T * 0.45, T * 0.8))
        harmonic(d, 960, 350, t, T * 0.8, [(250, count, 9, 1)], home, GOLD)
        harmonic(d, 960, 350, t, T * 0.8, [(190, 12, 4, 2), (300, 24, 3, 1)], home, TEAL, 200)
        porthole(d, 960, 350, 150, sweep=ease(span(t, T * 0.5, T * 0.85)), bolts=0)
        if t > T * 0.6:
            f = font(74, "Black"); s = "%02d–%02d" % (a, b)
            d.text((960 - d.textlength(s, font=f) / 2, 306), s, font=f, fill=CREAM + (int(255 * ease(span(t, T * 0.6, T * 0.8))),))
        u = back(span(t, 0.1, 0.5)); word = name.upper()
        wd = d.textlength(word, font=font(170, "Black"))
        x = -wd - 100 + (wd + 170) * u
        d.polygon([(x - 44, 196), (x + wd + 50, 180), (x + wd + 34, 408), (x - 56, 396)], fill=RUST + (255,))
        d.text((x, 196), word, font=font(170, "Black"), fill=DEEP + (255,))
        u2 = ease(span(t, 0.5, 1.0))
        d.text((74, 446 + 24 * (1 - u2)), "Slips %02d to %02d" % (a, b), font=font(50, "Bold"), fill=CREAM + (int(255 * u2),))
        d.text((76, 512 + 24 * (1 - u2)), "Watch for your number. Then write.", font=font(26, "SemiBold"), fill=TEAL + (int(255 * u2),))
        d.text((76, 660), "MUSIC  ·  %s  ·  DEEP SEA VOYAGE" % song.upper(), font=font(16, "Bold"), fill=GOLD + (int(200 * u2),))
        if n - i <= int(0.5 * FPS):
            bars(im, (1 - (n - i) / (0.5 * FPS)) * 0.5)
        yield bgr(im)
