#!/usr/bin/env python3
"""explainer: a short film that shows people doing it.

    python3 tools/explainer.py     # youtube/tks-how-it-works.mp4

Three parts, all drawn here in cut paper (no fal call), narrated by the same voice:
1. The way in. Room 4 in Trout Town has the same problem you have, the other way round:
   the trout look in at a turkey in a tin; you look in at the trout. Each class writes the other.
2. One porthole, played by three people at a table: the pilot, a first friend, a next friend.
   You see the paper move, what each one is thinking, the button they pick, and what they write.
3. The roll, and the message home.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, os.path.join(ROOT, "tools"))
import youtube as Y
import cards as C
V = Y.V
W, H, FPS = 1280, 720, 24
PAPER, NAVY, DEEP, GOLD, RUST, TEAL, CREAM = C.PAPER, C.NAVY, C.DEEP, C.GOLD, C.RUST, C.TEAL, C.CREAM
font, ease, back, span = C.font, C.ease, C.back, C.span
STILL = Image.open("stills/p07.jpg").convert("RGB")
SEATS = [(250, "Pilot", GOLD), (640, "First friend", TEAL), (1030, "Next friend", RUST)]
ENDINGS = ["Turkey backs the sub away, slowly.", "The trap is a present. It has a bow.", "The trap sneezes confetti.",
           "The choir plays a welcome song.", "The kazoo plays itself at night.", "The whole river hums. The bridge dances."]


def kid(d, x, y, col, up=0.0, name=None, on=True):
    a = 255 if on else 120
    d.rounded_rectangle((x - 46, y - 20 - up, x + 46, y + 120), 30, fill=col + (a,))
    d.ellipse((x - 34, y - 96 - up, x + 34, y - 28 - up), fill=CREAM + (a,), outline=NAVY + (a,), width=3)
    d.ellipse((x - 14, y - 68 - up, x - 8, y - 62 - up), fill=NAVY + (a,)); d.ellipse((x + 8, y - 68 - up, x + 14, y - 62 - up), fill=NAVY + (a,))
    d.arc((x - 12, y - 60 - up, x + 12, y - 44 - up), 20, 160, fill=NAVY + (a,), width=3)
    if name:
        f = font(22, "Bold"); d.text((x - d.textlength(name, font=f) / 2, y + 132), name, font=f, fill=NAVY + (a,))


def trout(d, x, y, s=1.0, flip=False):
    k = -1 if flip else 1
    d.ellipse((x - 52 * s, y - 24 * s, x + 52 * s, y + 24 * s), fill=(150, 170, 110, 255), outline=NAVY + (255,), width=3)
    d.polygon([(x - 50 * s * k, y), (x - 84 * s * k, y - 22 * s), (x - 84 * s * k, y + 22 * s)], fill=(150, 170, 110, 255), outline=NAVY + (255,))
    d.ellipse((x + 26 * s * k - 5, y - 10 * s, x + 26 * s * k + 5, y - 10 * s + 10), fill=NAVY + (255,))
    for i in range(4):
        d.ellipse((x - 20 * s + i * 14 * s, y - 6 * s, x - 14 * s + i * 14 * s, y), fill=RUST + (255,))
    d.rounded_rectangle((x - 12 * s, y + 14 * s, x + 14 * s, y + 38 * s), 4, fill=RUST + (255,), outline=NAVY + (255,), width=2)   # satchel


def tin(d, x, y, s=1.0):
    d.rounded_rectangle((x - 90 * s, y - 40 * s, x + 90 * s, y + 40 * s), int(38 * s), fill=(150, 156, 160, 255), outline=NAVY + (255,), width=3)
    d.ellipse((x - 30 * s, y - 30 * s, x + 30 * s, y + 30 * s), fill=TEAL + (255,), outline=GOLD + (255,), width=int(8 * s))
    d.ellipse((x - 10 * s, y - 12 * s, x + 12 * s, y + 12 * s), fill=(70, 110, 190, 255)); d.polygon([(x + 10 * s, y), (x + 22 * s, y + 4 * s), (x + 10 * s, y + 8 * s)], fill=GOLD + (255,))
    d.ellipse((x - 4 * s, y + 6 * s, x + 4 * s, y + 20 * s), fill=RUST + (255,))


def sheet(d, x, y, s=1.0, marks=0):
    w, h = 84 * s, 108 * s
    d.rectangle((x - w / 2 + 5, y - h / 2 + 6, x + w / 2 + 5, y + h / 2 + 6), fill=(22, 43, 52, 70))
    d.rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill=(255, 255, 255, 255), outline=NAVY + (255,), width=3)
    d.ellipse((x - 16 * s, y - 40 * s, x + 16 * s, y - 8 * s), outline=NAVY + (255,), width=2)
    for i in range(6):
        yy = y + 2 * s + i * 8 * s
        d.line((x - 32 * s, yy, x + 32 * s, yy), fill=(RUST if i < marks else (180, 188, 192)) + (255,), width=3 if i < marks else 2)


def bubble(im, x, w=440, h=250, y=70):
    d = ImageDraw.Draw(im)
    x0 = min(max(20, x - w // 2), W - w - 20)
    d.rounded_rectangle((x0, y, x0 + w, y + h), 34, fill=(255, 255, 255, 255), outline=NAVY + (255,), width=4)
    for i, r in enumerate((13, 8)):
        cy = y + h + 18 + i * 22; d.ellipse((x - r, cy - r, x + r, cy + r), fill=(255, 255, 255, 255), outline=NAVY + (255,), width=3)
    return x0, y


def caption(d, text, sub=None):
    size = 58
    while d.textlength(text, font=font(size, "Black")) > W - 120 and size > 34:
        size -= 2
    d.text((60, 24), text, font=font(size, "Black"), fill=NAVY + (255,))


def table(d):
    d.rounded_rectangle((90, 590, W - 90, 640), 18, fill=(176, 141, 62, 255), outline=NAVY + (255,), width=3)


def dice_row(d, lit, rolled=None):
    for k in range(6):
        cx = 400 + k * 96; on = k < lit
        if rolled == k + 1:
            d.ellipse((cx - 40, 664 - 40, cx + 40, 664 + 40), outline=RUST + (255,), width=6)
        C.die_face(d, cx, 664, 50, k + 1, on)


def choice(d, x, y, kind, word, on):
    col = C.SHAPE_COL[kind]
    d.rounded_rectangle((x, y, x + 390, y + 66), 18, fill=(8, 10, 14, 235 if on else 120), outline=col + (255 if on else 90,), width=4 if on else 2)
    C.button(d, x + 36, y + 33, 24, kind, on=on)
    d.text((x + 74, y + 14), word, font=font(28, "Bold"), fill=(255, 255, 255, 255 if on else 140))


def wrap(d, text, f, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width or not cur: cur = t
        else: out.append(cur); cur = w
    return out + [cur]


def scene_table(u, who, sheet_at, marks, lit, cap, draw_bubble=None, rolled=None, stand=False):
    im = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(im)
    caption(d, cap)
    for i, (x, name, col) in enumerate(SEATS):
        kid(d, x, 470, col, up=(26 * ease(u * 3) if stand and i == who else 0), name=name, on=(i == who))
    table(d)
    sheet(d, sheet_at, 560, 1.0, marks)
    dice_row(d, lit, rolled)
    if draw_bubble:
        x0, y0 = bubble(im, SEATS[who][0], y=92, h=226)
        draw_bubble(im, ImageDraw.Draw(im), x0, y0, u)
    return im


def beats():
    """(narration, frames-drawer). Each beat lasts as long as its sentence plus a breath."""
    sx = [s[0] for s in SEATS]
    def typed(text, u):
        return text[:max(1, int(len(text) * min(1, u * 1.6)))]
    def b_still(im, d, x0, y0, u):
        s = STILL.resize((200, 200)); m = Image.new("L", (200, 200), 0); ImageDraw.Draw(m).ellipse((0, 0, 199, 199), fill=255)
        im.paste(s, (x0 + 14, y0 + 13), m); d = ImageDraw.Draw(im)
        d.text((x0 + 240, y0 + 40), "07", font=font(86, "Black"), fill=NAVY + (255,)); d.text((x0 + 244, y0 + 140), "Hatch", font=font(34, "Bold"), fill=NAVY + (255,))
    def b_pick(kinds, words, pick):
        def f(im, d, x0, y0, u):
            for i, (k, w) in enumerate(zip(kinds, words)):
                choice(d, x0 + 24, y0 + 12 + i * 70, k, w, on=(u < 0.45 or i == pick))
            if u > 0.45 and len(kinds) == 2:
                d.text((x0 + 26, y0 + 166), "I pick the " + kinds[pick] + ".", font=font(26, "Bold"), fill=NAVY + (255,))
        return f
    def b_write(n):
        def f(im, d, x0, y0, u):
            C.die_face(d, x0 + 52, y0 + 56, 60, n, True)
            d.text((x0 + 96, y0 + 34), ["Probable", "Plausible", "Preposterous"][(n - 1) % 3], font=font(30, "Black"), fill=RUST + (255,))
            for i, l in enumerate(wrap(d, typed(ENDINGS[n - 1], u), font(30, "Bold"), 390)):
                d.text((x0 + 26, y0 + 104 + i * 38), l, font=font(30, "Bold"), fill=NAVY + (255,))
        return f
    def b_text(text):
        def f(im, d, x0, y0, u):
            for i, l in enumerate(wrap(d, typed(text, u), font(30, "Bold"), 392)):
                d.text((x0 + 26, y0 + 26 + i * 40), l, font=font(30, "Bold"), fill=NAVY + (255,))
        return f
    mv = lambda a, b: (lambda u: sx[a] + (sx[b] - sx[a]) * ease(u * 1.8))
    T = lambda **k: (lambda u: scene_table(u, k["who"], k["at"](u) if callable(k["at"]) else k["at"], k.get("marks", 0), k.get("lit", 0), k["cap"],
                                             k.get("bub"), k.get("rolled"), k.get("stand", False)))
    out = [
        ("The pilot gets one porthole.", T(who=0, at=sx[0], cap="The pilot gets one porthole.", bub=b_still)),
        ("The pilot watches. Then draws what Turkey sees, and writes three things.", T(who=0, at=sx[0], marks=3, cap="Watch. Draw. Write 3 things.", bub=b_still)),
        ("Pass it left.", T(who=1, at=mv(0, 1), marks=3, cap="Pass it left.")),
        ("The first friend thinks like Turkey. What is that thing outside? Pick a button.", T(who=1, at=sx[1], marks=3, cap="First friend: think like Turkey.", bub=b_pick(["triangle", "circle", "hexagon"], ["Naval contact mine", "Trap", "Party"], 1))),
        ("Now write three endings. One you would expect.", T(who=1, at=sx[1], marks=4, lit=1, cap="Ending 1: what you expect.", bub=b_write(1))),
        ("One that is strange, but fits.", T(who=1, at=sx[1], marks=4, lit=2, cap="Ending 2: strange, but it fits.", bub=b_write(2))),
        ("And one wild surprise.", T(who=1, at=sx[1], marks=5, lit=3, cap="Ending 3: a wild surprise!", bub=b_write(3))),
        ("Pass it left again.", T(who=2, at=mv(1, 2), marks=5, lit=3, cap="Pass it left again.")),
        ("The next friend thinks like the trout. What is that tin thing? Pick a button.", T(who=2, at=sx[2], marks=5, lit=3, cap="Next friend: think like the trout.", bub=b_pick(["cross", "square"], ["Brass birthday kazoo", "Piñata bat"], 0))),
        ("Three more endings. Four, five and six.", T(who=2, at=sx[2], marks=6, lit=6, cap="Endings 4, 5 and 6.", bub=b_write(5))),
        ("Give it back to the pilot.", T(who=0, at=mv(2, 0), marks=6, lit=6, cap="Give it back to the pilot.")),
        ("The pilot rolls one die. Five. Ending five is what happened.", T(who=0, at=sx[0], marks=6, lit=6, rolled=5, cap="Roll once. That ending happened.", bub=b_write(5))),
        ("Now tell it. What do the trout tell the newspaper? And why did Turkey come?", T(who=0, at=sx[0], marks=6, lit=6, rolled=5, stand=True, cap="Tell what happened.", bub=b_text("Dear Home, the kazoo plays itself at night. I think Turkey came to listen."))),
    ]
    return out


def split(u, stage):
    """Two classrooms, one above the water and one below, each imagining the other."""
    im = Image.new("RGBA", (W, H), PAPER + (255,)); d = ImageDraw.Draw(im)
    d.rectangle((0, 360, W, H), fill=(34, 92, 100, 255))
    for x in range(0, W + 40, 40):
        d.arc((x - 40, 346, x, 374), 180, 360, fill=CREAM + (255,), width=4)
    for i, (x, _, col) in enumerate(SEATS):
        kid(d, 240 + i * 150, 250, col)
    sheet(d, 390, 300, 0.7, 3)
    for i in range(3):
        trout(d, 260 + i * 150, 560 + (10 * math.sin(u * 6 + i)), 1.0)
    sheet(d, 410, 640, 0.7, 3)
    if stage >= 1:
        x0, y0 = bubble(im, 700, w=420, h=210, y=40); d = ImageDraw.Draw(im)
        trout(d, x0 + 210, y0 + 96, 1.5); d.text((x0 + 24, y0 + 160), "What do the trout think?", font=font(26, "Bold"), fill=NAVY + (255,))
    if stage >= 2:
        d.rounded_rectangle((760, 400, 1180, 610), 34, fill=(255, 255, 255, 255), outline=NAVY + (255,), width=4)
        for i, r in enumerate((16, 10, 6)):
            d.ellipse((730 - i * 26 - r, 600 - r + i * 10, 730 - i * 26 + r, 600 + r + i * 10), fill=(255, 255, 255, 255), outline=NAVY + (255,), width=3)
        tin(d, 970, 480, 1.1); d.text((784, 560), "What does Turkey think?", font=font(26, "Bold"), fill=NAVY + (255,))
    return im


def main():
    lines = ["Down in Trout Town, in Room Four, the pupils have a problem. Something has come down the river.",
             "Up here, you have the same problem, the other way round.",
             "You look in at the trout. The trout look out at Turkey, in a submarine made from a bread tin.",
             "Nobody knows what the other is thinking. So both rooms write it down.",
             "Here is one porthole, played by three people.",
             "One porthole. Three writers. Six endings. One roll.", "The Tour-key Submersible. Find the number on your slip."]
    B = beats()
    V.prefetch(lines + [b[0] for b in B])
    out = Y.Out()
    def hold(text, draw, extra=0.9):
        n = int((V.seconds(text) + extra) * FPS)
        out.cue(out.t, "line"); out.say(out.t + 0.25, text)
        for i in range(n):
            out.add(C.bgr(draw(i / float(n))))
    # 1. the way in: Room 4's chalkboard, from the porthole film
    clip = Y.film_frames("films/p03.mp4", 4.6, int((V.seconds(lines[0]) + 0.9) * FPS))
    out.tune(0.2); out.cue(0, "line"); out.say(0.4, lines[0])
    for f in clip:
        out.add(f)
    hold(lines[1], lambda u: split(u, 0))
    hold(lines[2], lambda u: split(u, 1 if u < 0.5 else 2))
    hold(lines[3], lambda u: split(u, 2))
    def title(u):
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        C.harmonic(d, 960, 360, u * 3, 3.0, [(200, 6, 11, 1), (270, 24, 3, 1)], ease(span(u, 0.5, 0.9)), GOLD)
        d.text((70, 250), "One porthole.", font=font(84, "Black"), fill=CREAM + (255,)); d.text((70, 350), "Three people.", font=font(84, "Black"), fill=GOLD + (255,))
        return im
    hold(lines[4], title)
    out.tune(out.t)
    for text, draw in B:
        hold(text, draw, extra=1.6)
    def close(u):
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        for i, (t, col) in enumerate((("One porthole.", CREAM), ("Three writers.", GOLD), ("Six endings.", TEAL), ("One roll.", RUST))):
            a = ease(span(u, i * 0.2, i * 0.2 + 0.15))
            d.text((90, 110 + i * 120), t, font=font(96, "Black"), fill=col + (int(255 * a),))
        return im
    hold(lines[5], close, extra=1.4)
    def tks(u):
        im = Image.new("RGBA", (W, H), DEEP + (255,)); d = ImageDraw.Draw(im)
        C.porthole(d, 980, 360, 190, sweep=ease(u * 2), bolts=1.0)
        d.polygon([(40, 210), (700, 196), (690, 352), (30, 344)], fill=RUST + (255,)); d.text((70, 206), "TOURKEY", font=font(124, "Black"), fill=DEEP + (255,))
        d.text((74, 372), "SUBMERSIBLE · TKS", font=font(54, "Black"), fill=GOLD + (255,)); d.text((76, 452), "Find the number on your slip.", font=font(34, "Bold"), fill=CREAM + (255,))
        return im
    hold(lines[6], tks, extra=2.0)
    bt, rms, sr, dur = Y.beats(Y.HOWTO_SONG[0])
    out.song(Y.HOWTO_SONG[0], float(bt[8]), 0.0, min(out.t, dur - 6), gain=0.8, fade=2.0)
    Y.MAX_MB = 24
    out.close("youtube/tks-how-it-works.mp4")
    print("youtube/tks-how-it-works.mp4", Y.stamp(out.t))


if __name__ == "__main__":
    main()
