#!/usr/bin/env python3
"""worksheets: one Submarine Porthole Log per slip, ready to print double-sided.

    python3 tools/worksheets.py     # youtube/porthole-logs.pdf (55 logs, front and back, 110 pages)

Takes the original two-page worksheet (sheets/tour_key_porthole_worksheet.pdf) untouched and
prints onto it, per porthole: the header already filled in (Porthole #, Sub Station, Rim Clue &
River Rule), and in the empty foot of each page the matching slip: the porthole drawing and
where it plays in the film on the front; each River Witness's question on the back.
"""
import io, json, os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
pdfmetrics.registerFont(TTFont("B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("R", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
NAVY, GOLD, SOFT, PALE, LINE = (0.086, 0.161, 0.227), (0.54, 0.35, 0.07), (0.37, 0.42, 0.44), (0.945, 0.961, 0.973), (0.62, 0.69, 0.75)
SRC = "sheets/tour_key_porthole_worksheet.pdf"
seeds = json.load(open("seeds.json"))
timing = json.load(open("youtube/timing.json"))["portholes"] if os.path.exists("youtube/timing.json") else {}
DIVES = [("Dive 1", 1, 16), ("Dive 2", 17, 32), ("Dive 3", 33, 48), ("Dive 4", 49, 55)]
PH = 792.0


def fit(c, text, font, size, width):
    while c.stringWidth(text, font, size) > width and size > 5.5:
        size -= 0.25
    return size


def wrap(c, text, font, size, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if c.stringWidth(t, font, size) <= width or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    return out + [cur]


import re, math
def options(question):
    q = question.strip().rstrip("?")
    parts = [x.strip() for x in re.split(r",\s*or\s+|,\s*|\s+or\s+", q) if x.strip()]
    return [x[0].upper() + x[1:] for x in parts]


SHAPE_RGB = {"triangle": (0.09, 0.65, 0.44), "circle": (0.88, 0.28, 0.28), "cross": (0.25, 0.5, 0.88), "square": (0.83, 0.34, 0.66), "hexagon": (0.79, 0.54, 0.12)}
def shape(c, kind, cx, cy, r):
    """The same controller button the film shows, for the student to copy."""
    col = SHAPE_RGB[kind]
    c.setFillColorRGB(0.08, 0.09, 0.11); c.circle(cx, cy, r, fill=1, stroke=0)
    c.setStrokeColorRGB(*col); c.setLineWidth(1.9); c.setLineCap(1); c.setLineJoin(1)
    q = r * 0.5
    if kind == "circle":
        c.circle(cx, cy, q, fill=0, stroke=1); return
    if kind == "cross":
        k = q * 0.85; c.line(cx - k, cy - k, cx + k, cy + k); c.line(cx - k, cy + k, cx + k, cy - k); return
    pts = {"triangle": [(cx, cy + q), (cx + q * 0.95, cy - q * 0.68), (cx - q * 0.95, cy - q * 0.68)],
           "square": [(cx - q * .8, cy - q * .8), (cx + q * .8, cy - q * .8), (cx + q * .8, cy + q * .8), (cx - q * .8, cy + q * .8)],
           "hexagon": [(cx + q * math.cos(math.pi / 3 * i), cy + q * math.sin(math.pi / 3 * i)) for i in range(6)]}[kind]
    path = c.beginPath(); path.moveTo(*pts[0])
    for pnt in pts[1:]:
        path.lineTo(*pnt)
    path.close(); c.drawPath(path, fill=0, stroke=1)


def front(n):
    r = seeds[n - 1]; station = r[0].split("·")[1].strip()
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(612, PH))
    c.setFillColorRGB(*NAVY)
    c.setFont("B", 11); c.drawString(327, PH - 93.5, "%02d" % n)                  # Porthole #
    c.setFont("B", fit(c, station, "B", 11, 118)); c.drawString(456, PH - 93.5, station)   # Sub Station
    text = "%s  ·  %s" % (r[1], r[5]); s = fit(c, text, "B", 9.5, 420)             # Rim Clue & River Rule
    c.setFont("B", s); c.drawString(153, PH - 119, text)
    # the slip, in the empty foot of the page
    y0 = 24; h = 78
    c.setStrokeColorRGB(*LINE); c.setDash(3, 3); c.line(36, y0 + h + 9, 576, y0 + h + 9); c.setDash()
    c.drawImage(ImageReader("youtube/thumbs/p%02d.jpg" % n), 40, y0, h, h, mask=None)
    c.setFillColorRGB(*GOLD); c.setFont("B", 6.5); c.drawString(132, y0 + h - 9, "PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE · YOUR SLIP")
    c.setFillColorRGB(*NAVY); c.setFont("B", 30); c.drawString(131, y0 + h - 41, "%02d" % n)
    c.setFont("B", 15); c.drawString(182, y0 + h - 33, station)
    c.setFont("R", 8.5); c.setFillColorRGB(*SOFT)
    c.drawString(182, y0 + h - 46, r[1])
    dive = next(d[0] for d in DIVES if d[1] <= n <= d[2])
    c.setFillColorRGB(*NAVY); c.setFont("B", 8)
    c.drawString(132, y0 + 14, "In the film TOURKEY TROUTTOWN: %s%s" % (dive, (", at " + timing["%02d" % n]) if timing else ""))
    c.setFont("R", 7.5); c.setFillColorRGB(*SOFT)
    c.drawString(132, y0 + 3, "Watch your porthole, then draw what the Turkey sees right now in the ring above.")
    c.save(); buf.seek(0); return PdfReader(buf).pages[0]


def back(n):
    r = seeds[n - 1]; station = r[0].split("·")[1].strip()
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(612, PH))
    y0, h = 30, 92
    c.setFillColorRGB(*GOLD); c.setFont("B", 6.5)
    c.drawString(37, y0 + h + 8, "SLIP %02d · %s · A QUESTION TO START EACH RIVER WITNESS" % (n, station.upper()))
    to, tr = options(r[3]), options(r[4])
    kinds_t = ["triangle", "circle", "hexagon"][:len(to)]
    kinds_r = ["cross", "square", "hexagon"][:len(tr)]
    for x, crew, who, opts, kinds in ((37, "Crewmate B · River Witness #1", "TURKEY THINKS · PICK ONE, DRAW ITS SHAPE", to, kinds_t),
                                      (312, "Crewmate C · River Witness #2", "THE TROUT THINK · PICK ONE, DRAW ITS SHAPE", tr, kinds_r)):
        w = 263
        c.setFillColorRGB(*PALE); c.setStrokeColorRGB(*LINE); c.setLineWidth(0.8); c.roundRect(x, y0, w, h, 4, fill=1, stroke=1)
        c.setFillColorRGB(*NAVY); c.rect(x, y0 + h - 2.2, w, 2.2, fill=1, stroke=0)
        c.setFont("B", 9); c.drawString(x + 9, y0 + h - 16, crew)
        c.setFillColorRGB(*GOLD); c.setFont("B", 6.5); c.drawString(x + 9, y0 + h - 27, who)
        gap = 20 if len(opts) > 2 else 26
        yy = y0 + h - 44
        for kind, o in zip(kinds, opts):
            shape(c, kind, x + 18, yy + 4, 9)
            c.setFillColorRGB(*NAVY); c.setFont("B", fit(c, o, "B", 12.5, w - 44)); c.drawString(x + 34, yy, o)
            yy -= gap
    c.save(); buf.seek(0); return PdfReader(buf).pages[0]


if __name__ == "__main__":
    os.makedirs("youtube", exist_ok=True)
    w = PdfWriter()
    base = PdfReader(SRC)                    # read once, so all 110 pages share the worksheet's fonts and art
    for n in range(1, 56):
        for i, over in ((0, front(n)), (1, back(n))):
            page = w.add_page(over)          # each page starts as its own overlay ...
            page.merge_page(base.pages[i], over=False)   # ... and the untouched worksheet is laid underneath it
    w.compress_identical_objects()
    w.write("youtube/porthole-logs.pdf")
    print("youtube/porthole-logs.pdf", len(w.pages), "pages")
