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


# The four face buttons of a game controller: a shape and a colour each, so a choice can be
# named by either ("the green triangle"). A fifth, amber hexagon covers the rare third choice.
SHAPES = ["triangle", "circle", "cross", "square", "hexagon"]
SHAPE_COL = {"triangle": (56, 214, 150), "circle": (255, 92, 92), "cross": (96, 160, 255), "square": (255, 128, 210), "hexagon": (255, 190, 80)}
def shape_points(kind, cx, cy, r):
    if kind == "triangle":
        return [(cx, cy - r), (cx + r * 0.95, cy + r * 0.68), (cx - r * 0.95, cy + r * 0.68)]
    if kind == "square":
        q = r * 0.8; return [(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)]
    if kind == "hexagon":
        return [(cx + r * math.cos(math.pi / 3 * i), cy + r * math.sin(math.pi / 3 * i)) for i in range(6)]
    return None
def button(d, cx, cy, r, kind, on=True):
    """A controller face button: black glossy cap, the shape drawn bold in its colour."""
    col = SHAPE_COL[kind]; a = 255 if on else 110
    if on:
        d.ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), fill=col + (70,))        # glow
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(8, 10, 14, 250 if on else 190), outline=col + (a,), width=3 if on else 2)
    if on:
        d.arc((cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5), 205, 335, fill=(255, 255, 255, 70), width=3)   # gloss
    q = r * 0.5; w = max(4, int(round(r * 0.2)))
    if kind == "circle":
        d.ellipse((cx - q, cy - q, cx + q, cy + q), outline=col + (a,), width=w)
    elif kind == "cross":
        k = q * 0.85
        d.line((cx - k, cy - k, cx + k, cy + k), fill=col + (a,), width=w); d.line((cx - k, cy + k, cx + k, cy - k), fill=col + (a,), width=w)
    else:
        pts = shape_points(kind, cx, cy, q)
        d.line(pts + [pts[0], pts[1]], fill=col + (a,), width=w, joint="curve")


PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
def die_face(d, cx, cy, size, n, on=True):
    """A die face in the worksheet's style: cream square, brown edge, dark pips."""
    h = size / 2.0; a = 255 if on else 105
    d.rounded_rectangle((cx - h, cy - h, cx + h, cy + h), size * 0.2, fill=(251, 246, 233, a), outline=(110, 72, 16, a), width=max(2, int(size * 0.07)))
    q = size * 0.26; r = size * 0.085
    for px_, py_ in PIPS[n]:
        d.ellipse((cx + px_ * q - r, cy + py_ * q - r, cx + px_ * q + r, cy + py_ * q + r), fill=(22, 41, 58, a))


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
# Every entry line and every printed prompt on the worksheet gets its own step: one box on the
# page (PDF points), one short line of words. Nothing on the sheet is left for the child to find alone.
CARDS = [
    dict(num="1", page=1, crop=(28, 22, 584, 132), chip="Front · Pilot", title="Copy your slip", film=("films/intro-1.mp4", 0.0), lights=[
        ((34, 82, 262, 101), "Write your name."),
        ((262, 82, 392, 101), "Write your number."),
        ((398, 82, 580, 101), "Write your station."),
        ((34, 107, 580, 127), "Write your clue and your rule.")]),
    dict(num="2", page=1, crop=(120, 130, 492, 420), chip="Front · Pilot", title="Draw", film=("films/intro-3.mp4", 2.0), lights=[
        ((180, 134, 430, 157), "Look. What does Turkey see?"),
        ((150, 160, 462, 396), "Draw it inside the ring."),
        ((205, 397, 405, 419), "This is Trout Town.")]),
    dict(num="3", page=1, crop=(28, 424, 584, 688), chip="Front · Pilot", title="Write 3 things", film=("films/intro-2.mp4", 1.0), lights=[
        ((34, 428, 580, 452), "1. Who is outside the glass?"),
        ((34, 428, 580, 452), "What do they think our sub is?"),
        ((34, 452, 580, 497), "Write it here."),
        ((34, 503, 580, 527), "2. What one thing does Turkey do?"),
        ((34, 527, 580, 572), "Write it here."),
        ((34, 578, 580, 602), "3. How could this use up our air?"),
        ((34, 602, 580, 647), "Write it here."),
        ((34, 653, 580, 684), "Pass your paper left.")]),
    dict(num="4", page=2, crop=(28, 70, 584, 110), chip="Back · Everyone", title="Three kinds of endings", film=("units/p22.mp4", 2.0), lights=[
        ((36, 79, 226, 104), "Probable: what you expect."),
        ((212, 79, 426, 104), "Plausible: strange, but it fits."),
        ((420, 79, 580, 104), "Preposterous: a wild surprise!")]),
    dict(num="5", page=2, crop=(28, 104, 300, 462), chip="Back · First friend", title="First friend", film=("units/p07.mp4", 0.5), lights=[
        ((36, 112, 262, 180), "First friend: write your name."),
        ((36, 184, 262, 266), "Bolt 1. What would you expect?"),
        ((36, 268, 262, 349), "Bolt 2. Strange, but it fits."),
        ((36, 351, 262, 431), "Bolt 3. A wild surprise!"),
        ((34, 433, 262, 459), "Pass it left again.")]),
    dict(num="6", page=2, crop=(312, 104, 584, 462), chip="Back · Next friend", title="Next friend", film=("units/p07.mp4", 5.6), lights=[
        ((352, 112, 580, 180), "Next friend: write your name."),
        ((352, 184, 580, 266), "Bolt 4. What would you expect?"),
        ((352, 268, 580, 349), "Bolt 5. Strange, but it fits."),
        ((352, 351, 580, 431), "Bolt 6. A wild surprise!"),
        ((352, 433, 580, 459), "Give it back to the pilot.")]),
    dict(num="7", page=2, crop=(28, 262, 584, 508), chip="Back · Pilot", title="Roll", film=("films/intro-4.mp4", 2.4), lights=[
        ((258, 270, 354, 380), "Roll the die one time."),
        ((266, 477, 342, 502), "Write the number you rolled."),
        ((342, 477, 580, 502), "Or circle that die.")]),
    dict(num="8", page=2, crop=(28, 474, 584, 648), chip="Back · Pilot", title="Tell what happened", film=("films/intro-5.mp4", 2.0), lights=[
        ((34, 503, 580, 524), "What do the trout tell the newspaper?"),
        ((34, 524, 580, 562), "Write it here."),
        ((34, 566, 580, 601), "Why did Turkey come to Trout Town?"),
        ((34, 601, 580, 644), "Write your message home.")]),
]
LINE_SECONDS, CARD_LEAD = 3.6, 1.4
def card_seconds(spec):
    return CARD_LEAD + LINE_SECONDS * len(spec["lights"]) + 0.6


def card(spec, film, n, first=False):
    """One command card. One line of words at a time, and the worksheet is magnified onto the
    field that line is about, so the eye is led: read this, write here."""
    pg = sheet(spec["page"]); k = pg.size[0] / 612.0
    AW, AH = 700, 420; px, py = 60, 250
    asp = AW / float(AH)
    def view_for(box, cap=330.0):
        """The part of the page to show for a field: never wider than cap points, so the words in
        it are always large. A field wider or taller than the view is shown from its start."""
        x0, y0, x1, y1 = box
        w = min(cap, max((x1 - x0) * 1.22, (y1 - y0) * 1.5 * asp, 190.0)); h = w / asp
        cx = (x0 + x1) / 2.0 if (x1 - x0) <= w - 20 else x0 - 12 + w / 2
        cy = (y0 + y1) / 2.0 if (y1 - y0) <= h - 14 else y0 - 10 + h / 2
        return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    def grab(v):
        """Crop the page at view v (points); anything off the page is paper white."""
        box = (int(v[0] * k), int(v[1] * k), int(v[2] * k), int(v[3] * k))
        out = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (255, 255, 255))
        out.paste(pg, (-box[0], -box[1]))
        return out.resize((AW, AH), Image.LANCZOS)
    x0, y0, x1, y1 = spec["crop"]
    whole = view_for((x0, y0, x1, y1), cap=9999.0)
    views = [whole] + [view_for(b) for b, _ in spec["lights"]]
    fcx, fcy, fr_ = 1040, 452, 180
    for i in range(n):
        t = i / float(FPS)
        im = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(im)
        u = back(span(t, 0.25, 0.7))
        d.polygon([(0, 26), (150 * u + 20, 18), (138 * u + 14, 176), (0, 184)], fill=RUST + (255,))
        d.text((38 - 160 * (1 - u), 20), spec["num"], font=font(150, "Black"), fill=PAPER + (255,))
        u2 = ease(span(t, 0.4, 0.9))
        d.text((196 + 60 * (1 - u2), 30), spec["title"], font=font(40, "Black"), fill=NAVY + (int(170 * u2),))
        cw = d.textlength(spec["chip"], font=font(17, "Bold")) + 28
        tx = 196 + d.textlength(spec["title"], font=font(40, "Black")) + 22
        d.rounded_rectangle((tx, 38, tx + cw, 70), 8, fill=(251, 243, 223, int(255 * u2)), outline=GOLD + (int(255 * u2),), width=2)
        d.text((tx + 14, 44), spec["chip"], font=font(17, "Bold"), fill=NAVY + (int(255 * u2),))
        # which line is live
        j = int((t - CARD_LEAD) // LINE_SECONDS) if t >= CARD_LEAD else -1
        j = min(j, len(spec["lights"]) - 1)
        tl = t - CARD_LEAD - j * LINE_SECONDS if j >= 0 else 0
        if j >= 0:                                                    # the one line, large
            a = ease(span(tl, 0.0, 0.35))
            line = spec["lights"][j][1]; size = 66
            while d.textlength(line, font=font(size, "Black")) > W - 230 and size > 40:
                size -= 2
            d.text((196, 92 + 18 * (1 - a)), line, font=font(size, "Black"), fill=NAVY + (int(255 * a),))
        # the worksheet, magnified onto the live field
        va = views[j] if j >= 0 else whole
        vb = views[j + 1] if j >= 0 else whole
        m = ease(span(tl, 0.0, 0.7)) if j >= 0 else 0.0
        v = [va[q] + (vb[q] - va[q]) * m for q in range(4)]
        u3 = back(span(t, 0.5, 1.05), 1.0); oy = int((1 - u3) * 560)
        src = grab(v)
        d.rectangle((px + 8, py + 10 + oy, px + AW + 8, py + AH + 10 + oy), fill=(22, 43, 52, 60))
        im.paste(src, (px, py + oy))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        if j >= 0:
            a0, b0, a1, b1 = spec["lights"][j][0]
            sx = AW / float(v[2] - v[0]); sy = AH / float(v[3] - v[1])
            X0, Y0, X1, Y1 = px + (a0 - v[0]) * sx, py + (b0 - v[1]) * sy, px + (a1 - v[0]) * sx, py + (b1 - v[1]) * sy
            X0, Y0, X1, Y1 = max(px, X0), max(py, Y0), min(px + AW, X1), min(py + AH, Y1)
            wipe = ease(span(tl, 0.5, 1.0))
            if wipe > 0 and X1 > X0 and Y1 > Y0:
                od.rectangle((X0, Y0, X0 + (X1 - X0) * wipe, Y1), fill=GOLD + (70,))
                if wipe >= 1:
                    od.rectangle((X0, Y0, X1, Y1), outline=RUST + (255,), width=5)
        im.alpha_composite(ov); d = ImageDraw.Draw(im)
        d.rectangle((px, py + oy, px + AW, py + AH + oy), outline=NAVY + (255,), width=3)
        # the film in a porthole
        u4 = back(span(t, 0.6, 1.1), 1.3)
        if u4 > 0:
            r = int(fr_ * u4)
            if r > 8:
                disc = circle_film(film[min(i, len(film) - 1)], 2 * int(r * 0.8))
                im.alpha_composite(disc, (fcx - disc.size[0] // 2, fcy - disc.size[1] // 2))
                d = ImageDraw.Draw(im)
                porthole(d, fcx, fcy, r, 1.0, 1.0)
        if not first and t < 0.75:
            bars(im, 0.5 + t / 1.5, direction=1 if int(spec["num"]) % 2 else -1)
        if n - i <= int(0.75 * FPS):
            bars(im, (1 - (n - i) / (0.75 * FPS)) * 0.5, direction=-1 if int(spec["num"]) % 2 else 1)
        yield bgr(im)


def choose_card(n):
    """Four choices, four buttons. Pick one and draw its shape."""
    demo = [("triangle", "A sunken ship"), ("circle", "A giant's foot"), ("cross", "A flashlight"), ("square", "A crab")]
    for i in range(n):
        t = i / float(FPS)
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        u = ease(span(t, 0.2, 0.8))
        d.text((90, 70 + 30 * (1 - u)), "See four choices.", font=font(72, "Black"), fill=CREAM + (int(255 * u),))
        u2 = ease(span(t, 1.6, 2.2))
        d.text((90, 160 + 30 * (1 - u2)), "Pick one. Draw its shape.", font=font(72, "Black"), fill=GOLD + (int(255 * u2),))
        for k, (kind, word) in enumerate(demo):
            ts = 2.6 + 0.7 * k
            if t < ts:
                continue
            v = back(span(t, ts, ts + 0.4)); x = 120 + (k % 2) * 560; y = 360 + (k // 2) * 150
            r = int(52 * v)
            if r > 6:
                button(d, x + 52, y + 52, r, kind)
            d.text((x + 130, y + 22), word, font=font(44, "Bold"), fill=CREAM + (int(255 * min(1, v)),))
        if t < 0.75:
            bars(im, 0.5 + t / 1.5)
        if n - i <= int(0.6 * FPS):
            bars(im, (1 - (n - i) / (0.6 * FPS)) * 0.5, direction=-1)
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
        d.text((76, 512 + 24 * (1 - u2)), "Watch for your number.", font=font(26, "SemiBold"), fill=TEAL + (int(255 * u2),))
        d.text((76, 660), "MUSIC  ·  %s  ·  DEEP SEA VOYAGE" % song.upper(), font=font(16, "Bold"), fill=GOLD + (int(200 * u2),))
        if n - i <= int(0.5 * FPS):
            bars(im, (1 - (n - i) / (0.5 * FPS)) * 0.5)
        yield bgr(im)
