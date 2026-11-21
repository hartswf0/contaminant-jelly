#!/usr/bin/env python3
"""scion_film: what a SCION is, and how it animates.

    python3 scion_film.py     # assets/what-is-a-scion.mp4

Told from three texts: MULTIPLANE ANIMATION STUDIO (one drawing agent that is the whole studio, 38 laws),
AGENT_FIRST_ARCHITECT_PROMPT (the questions that turn a one-desk workflow into an agent-first one) and
SCION: AUTONOMOUS ANIMATION STUDIO (the swarm instruction that results, 15 laws). Words on screen in
quotation marks are quoted from those texts. The animation shown (keys, breakdowns, in-betweens, planes)
is drawn live with the cut-paper world of class film c13, and the last part shows that film's own record.
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw
sys.path.insert(0, "films"); sys.path.insert(0, "films/swarm/c13")
import kit, world as Wd
import class_cut as C
from class_cut import W, H, TMP, F, PAPER, INK, MUTE, RUST, TEAL, GOLD, PENCIL, ease, back, lerp, segment, tone, whoosh
from scion_explainer import MONO, SERIF, table, sheet, typed, heading, img, first_render, final_frame, clip

ST = "films/stills/c13_world/"
N = "narrator"


def ink():
    k = kit.Ink(0, 0, boil=0, wobble=0); k._grain = False; return k


def center(d, x, y, text, font, fill):
    d.text((x - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)


# ---------- A · title ----------
def s_title(t):
    im = table(); d = sheet(im, (150, 120, 810, 420))
    d.text((190, 150), "WHAT IS", font=F(60), fill=INK); d.text((190, 218), "A SCION?", font=F(92), fill=RUST)
    if t > 2.2: d.text((194, 340), "And how does it animate?", font=F(34), fill=TEAL)
    return im


# ---------- B · one desk ----------
JOBS = ["animation director", "layout artist", "character animator", "in-betweener", "background painter", "effects animator", "camera operator", "animation checker"]
LOOP = ["DRAW", "LOOK", "COMPARE", "ADJUST", "DRAW AGAIN"]


def s_desk(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "START WITH ONE DESK", "MULTIPLANE ANIMATION STUDIO: one prompt, one model, 38 laws")
    d = sheet(im, (60, 110, 900, 330)); d.text((84, 124), "\"You are the", font=SERIF(24), fill=MUTE)
    for k, j in enumerate(JOBS):
        at = 2.0 + k * 0.9
        if t < at: continue
        x = 84 + (k % 4) * 204; y = 162 + (k // 4) * 70; d.rounded_rectangle((x, y, x + 192, y + 54), 8, outline=INK, width=2)
        center(d, x + 96, y + 15, j, F(17), INK)
    if t > 9.6: d.text((84, 296), "for a classical hand-drawn animation studio.\"", font=SERIF(22), fill=MUTE)
    if t > 12.0:
        d = ImageDraw.Draw(im); d.text((60, 356), "ITS PRIMITIVE", font=F(18), fill=(226, 212, 186)); live = int((t - 12.0) / 1.1) % 5
        x = 60
        for k, w in enumerate(LOOP):
            ww = d.textlength(w, font=F(24)) + 24; on = k == live
            d.rounded_rectangle((x, 386, x + ww, 436), 10, fill=PENCIL if on else None, outline=PENCIL, width=3); d.text((x + 12, 396), w, font=F(24), fill=INK if on else PENCIL)
            x += ww + 8
            if k < 4: d.text((x, 394), "→", font=F(24), fill=PAPER); x += 30
    if t > 19.0: d.text((60, 462), "\"Do not try to finish the shot in one drawing.\"", font=SERIF(26), fill=PAPER)
    return im


# ---------- C · keys, breakdowns, in-betweens ----------
def leap(u):
    """A trout's leap over the page, u from 0 to 1: position and heading."""
    x = lerp(810, 150, u); y = 420 - 250 * math.sin(math.pi * u); ang = lerp(-42, 42, u)
    return x, y, ang


KEYS = [0.0, 0.34, 0.66, 1.0]; BREAK = [0.17, 0.5, 0.83]
def spaced(v):                                     # slow out of the water, fast over the top, slow in
    return 0.5 - 0.5 * math.cos(math.pi * v)


def s_keys(t):
    k = ink(); k.paper(); d = k.d
    d.text((40, 22), "KEYS FIRST", font=F(34), fill=INK)
    d.line((90, 452, 870, 452), fill=(120, 150, 150), width=3)
    def fish(u, alpha):
        x, y, a = leap(u); Wd.trout(k, x, y, length=170, angle=a, alpha=alpha)
    if t < 17.0:
        for i, u in enumerate(KEYS):
            if t > 1.0 + i * 1.3:
                fish(u, 1.0); x, y, _ = leap(u); k.d.text((x - 16, min(480, y + 46)), "K0%d" % (i + 1), font=F(18), fill=RUST)
        for i, u in enumerate(BREAK):
            if t > 8.0 + i * 0.9:
                fish(u, 0.55); x, y, _ = leap(u); k.d.text((x - 12, y + 46), "B%d" % (i + 1), font=F(15), fill=TEAL)
        if t > 12.0:
            n = int(min(1, (t - 12.0) / 3.0) * 12)
            for j in range(n):
                u = spaced((j + 0.5) / 12)
                if min(abs(u - q) for q in KEYS + BREAK) > 0.035: fish(u, 0.22)
        lab = "the poses that tell the story" if t < 8.0 else ("breakdowns: how the move happens" if t < 12.0 else "in-betweens: close together where it is slow")
        k.d.text((40, 66), lab, font=F(19, "SemiBold"), fill=MUTE)
    else:
        v = ((t - 17.0) / 2.2) % 1.0; fish(spaced(v), 1.0); k.d.text((40, 66), "playback", font=F(19, "SemiBold"), fill=MUTE)
    if t > 5.6 and t < 12.0: k.d.text((40, 494), "\"If I removed every other drawing, would the audience still understand what happened?\"", font=SERIF(20), fill=INK)
    if t > 19.5: k.d.text((40, 494), "\"A drawing becomes meaningful because of the drawing before it and the drawing after it.\"", font=SERIF(20), fill=INK)
    return k.img.convert("RGB")


# ---------- D · planes ----------
PLANES = [("6  sky and atmosphere", 9.0), ("5  distant background", 6.0), ("4  midground", 3.0), ("2  character action", 1.6), ("1  foreground", 0.8)]


def s_planes(t):
    cam = 170 * math.sin((t - 2.0) * 0.55) if t > 2.0 else 0.0
    k = ink()
    Wd.river(k, t, planes=("back",), shift=cam / 9.0); Wd.river(k, t, planes=("far",), shift=cam / 6.0)
    Wd.arch(k, c=(520 - cam / 3.0, 300)); Wd.river(k, t, planes=("bed",), shift=cam / 2.2)
    Wd.trout(k, 330 - cam / 1.6, 250 + 8 * math.sin(t * 2), length=210, angle=-6, phase=t * 3)
    Wd.trout(k, 700 - cam / 0.8, 420, length=330, angle=6, phase=t * 3 + 1, alpha=0.96)
    im = k.img.convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0, 0, W, 88), fill=(14, 22, 24, 190)); d.text((40, 16), "BUILD DEPTH IN PLANES", font=F(34), fill=PAPER); d.text((42, 58), "near layers move more, far layers move less", font=F(19, "SemiBold"), fill=(226, 212, 186))
    if t > 4.0:
        d.rectangle((640, 104, 944, 300), fill=(14, 22, 24, 200))
        for j, (name, depth) in enumerate(PLANES):
            y = 116 + j * 36; d.text((652, y), name, font=F(16, "SemiBold"), fill=PAPER); w = 80 * abs(cam) / 170 / depth * 2.4
            d.rectangle((652, y + 22, 652 + w, y + 28), fill=PENCIL)
    if t > 9.0: d.rectangle((0, 478, W, H), fill=(14, 22, 24, 200)); d.text((40, 492), "screen motion  ∝  camera motion / layer depth", font=MONO(22), fill=PENCIL)
    return im


# ---------- E · why one desk does not scale ----------
def s_problem(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "ONE DESK DOES NOT SCALE")
    d = sheet(im, (60, 120, 330, 400)); center(d, 195, 140, "ONE DESK", F(26), INK)
    for k, j in enumerate(JOBS): d.text((84, 184 + k * 25), "%d  %s" % (k + 1, j), font=F(16, "SemiBold"), fill=RUST if int(t * 1.2) % 8 == k else MUTE)
    d = ImageDraw.Draw(im)
    if t > 3.0:
        n = int(min(1, (t - 3.0) / 6.0) * 60)
        for j in range(n):
            x = 400 + (j % 12) * 26; y = 330 - (j // 12) * 44; d.rectangle((x, y, x + 22, y + 34), fill=PAPER, outline=(150, 140, 120))
        d.text((400, 372), "frames made: x%d" % (1 + int(min(1, (t - 3.0) / 6.0) * 99)), font=F(24), fill=PENCIL)
    if t > 9.6:
        d.ellipse((770, 200, 890, 270), fill=PAPER, outline=INK, width=4); d.ellipse((812, 216, 848, 252), fill=INK); d.text((772, 284), "one pair of eyes", font=F(17, "SemiBold"), fill=PAPER)
    if t > 12.0: d.text((60, 426), "The bottleneck moves from making to watching.", font=F(27), fill=PAPER)
    if t > 15.5: d.text((60, 470), "And the desk checks its own work: a correlated blind spot.", font=F(24), fill=PENCIL)
    return im


# ---------- F · the architect's four questions ----------
FOUR = [(1.0, "STATE", "one document", "a project state every agent can read"),
        (5.6, "CONCURRENCY", "one job after another", "many agents at once, on separate candidates"),
        (10.4, "VERIFICATION", "the maker rereads its work", "a critic who built nothing checks it"),
        (15.0, "BATCH SIZE", "finish, then look", "a rough cut, playable from day one")]


def s_four(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE ARCHITECT PROMPT ASKS FOUR QUESTIONS", "AGENT_FIRST_ARCHITECT_PROMPT: rebuild the work for agents, keep people for intent")
    d.text((250, 104), "ONE DESK", font=F(17), fill=(226, 212, 186)); d.text((560, 104), "SCION", font=F(17), fill=PENCIL)
    for k, (at, name, old, new) in enumerate(FOUR):
        if t < at: continue
        y = 132 + k * 86; d = sheet(im, (40, y, 920, y + 74), shadow=False); d.text((56, y + 22), name, font=F(22), fill=RUST)
        d.text((250, y + 24), old, font=SERIF(21), fill=MUTE)
        if t > at + 1.4: d.text((500, y + 22), "→", font=F(22), fill=INK); typed(d, (536, y + 24), new, SERIF(21), INK, (t - at - 1.4) / 1.4)
    if t > 19.6: d = ImageDraw.Draw(im); d.text((40, 488), "\"Move verification from syntax to invariants.\"", font=SERIF(26), fill=PAPER)
    return im


# ---------- G · the SCION ----------
CHAIN = [("Owns", "COMPLETE VIEWING EXPERIENCE"), ("Coordinates", "PRODUCTION SWARM"), ("Maintains", "REPRODUCIBLE WORLD AND PROJECT STATE"), ("Tests against", "INSPECTABLE QUALITY REFERENCES"),
         ("Improves through", "INDEPENDENT CRITIQUE"), ("Reconsiders through", "TARGETED INQUIRY"), ("Delivers", "FINISHED ANIMATED WORK")]


def s_chain(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE RESULT: A SCION", "SCION: AUTONOMOUS ANIMATION STUDIO")
    d.rounded_rectangle((40, 250, 190, 320), 10, fill=RUST); center(d, 115, 266, "SCION", F(32), PAPER)
    for k, (verb, obj) in enumerate(CHAIN):
        at = 1.6 + k * 2.6
        if t < at: continue
        y = 106 + k * 58; u = ease((t - at) / 0.5)
        d.line((190, 285, 230, y + 22), fill=(226, 212, 186), width=2); d.text((240, y + 10), verb, font=SERIF(21), fill=PENCIL)
        x0 = 430; w = (d.textlength(obj, font=F(19)) + 28) * u; d.rounded_rectangle((x0, y, x0 + w, y + 44), 8, fill=PAPER)
        if u > 0.9: d.text((x0 + 14, y + 10), obj, font=F(19), fill=INK)
    return im


# ---------- H · fifteen laws ----------
LAWS = ["Define what would make this work exceptional", "Establish a bar that survives inspection", "Prove the production method early", "Make the swarm accountable to artifacts",
        "Build performances with specificity", "Make the world consequent", "Compose attention through image and sound", "Keep a shared, recoverable production state",
        "Never let the builder award the pass", "Repair the cause, then recheck the whole", "Investigate when repair stops working", "Preserve discovery and distinctiveness",
        "Keep the film under continuous review", "Verify claims and protect resources", "Make progress and stopping honest"]
KEY3 = {3: (12.0, "Build the hardest passage first. If the method fails, change it while that is cheap."),
        9: (17.5, "The critic sees the film, not the builder's reasons."), 14: (22.5, "Every finding is MEASURED, STRUCTURAL, JUDGED or UNKNOWN.")}


def s_laws(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "FIFTEEN LAWS"); d = sheet(im, (40, 84, 920, 452))
    for k, law in enumerate(LAWS):
        if t < 0.8 + k * 0.62: continue
        n = k + 1; y = 96 + k * 23.4; hot = n in KEY3 and t > KEY3[n][0]
        if hot: d.rectangle((48, y - 1, 912, y + 21), fill=(246, 226, 170))
        d.text((60, y), "%2d" % n, font=F(16), fill=RUST); d.text((96, y), law, font=F(16, "Bold" if hot else "SemiBold"), fill=INK)
    d = ImageDraw.Draw(im)
    for n, (at, line) in KEY3.items():
        if at < t < at + 5.2: d.text((40, 470), "Law %d" % n, font=F(20), fill=PENCIL); typed(d, (40, 498), line, SERIF(24), PAPER, (t - at) / 1.4)
    return im


# ---------- I · how a SCION animates ----------
def s_how(pieces, wheel, before, after):
    cols = [(1.0, "WORLD AGENT", "builds the planes and the pieces", pieces, TEAL), (7.0, "PERFORMANCE AGENTS", "build the keys and the timing", wheel, GOLD),
            (13.0, "EDITOR", "keeps a cut you can always play", after, RUST), (19.0, "CRITIC", "built nothing, watches at speed", before, INK)]
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "HOW A SCION ANIMATES", "the desk's craft, shared out")
        for k, (at, name, does, pic, col) in enumerate(cols):
            if t < at: continue
            x = 28 + k * 230; y = int(lerp(560, 108, back((t - at) / 0.4))); d = sheet(im, (x, y, x + 214, y + 262))
            d.rectangle((x, y, x + 214, y + 40), fill=col); center(d, x + 107, y + 9, name, F(17), PAPER)
            im.paste(pic.resize((198, 111), Image.LANCZOS), (x + 8, y + 50)); d = ImageDraw.Draw(im)
            words = does.split(); h = (len(words) + 1) // 2
            for j, ln in enumerate((" ".join(words[:h]), " ".join(words[h:]))): center(d, x + 107, y + 176 + j * 26, ln, SERIF(20), INK)
            if k == 3 and t > at + 2.6: center(d, x + 107, y + 232, "VERDICT: NEARLY", F(17), RUST)
        d = ImageDraw.Draw(im)
        if t > 25.0:
            beats = ["situation and intention", "perception and choice", "body and timing", "resistance and consequence"]; x = 28
            d.text((28, 392), "A PERFORMANCE, BY LAW 5", font=F(17), fill=(226, 212, 186))
            for j, b in enumerate(beats):
                if t < 25.6 + j * 1.5: break
                w = d.textlength(b, font=F(15)) + 18; d.rounded_rectangle((x, 420, x + w, 456), 8, outline=PENCIL, width=2); d.text((x + 9, 429), b, font=F(15), fill=PENCIL); x += w + 6
                if j < 3: d.text((x, 427), "→", font=F(18), fill=PAPER); x += 24
        if t > 32.5: d.text((28, 484), "\"Do not smooth away intention.\"", font=SERIF(26), fill=PAPER)
        return im
    return draw


# ---------- K · end ----------
def s_end(t):
    im = table(); d = sheet(im, (90, 130, 870, 420))
    for j, ln in enumerate(("\"Make every important claim", "about quality answerable", "by opening the work", "and watching it.\"")):
        if t > 0.6 + j * 1.3: d.text((130, 158 + j * 58), ln, font=SERIF(46), fill=INK if j < 3 else RUST)
    if t > 7.0: d.text((132, 388), "the last line of the SCION", font=F(17, "SemiBold"), fill=MUTE)
    return im


if __name__ == "__main__":
    parts = [
        segment("s_title", 6.5, s_title, [(0.8, "What is a SCION? And how does it animate?", N)], sfx=[(tone, (0.3, 196)), (tone, (2.2, 262))]),
        segment("s_desk", 23.5, s_desk, [(0.6, "Start with one desk. One prompt tells one model to be the whole studio.", N), (5.6, "Eight jobs, one model.", N),
                                        (12.0, "Its rule is simple. Draw. Look. Compare. Adjust. Draw again.", N), (19.0, "Do not try to finish the shot in one drawing.", N)]),
        segment("s_keys", 24.5, s_keys, [(0.6, "It draws the key poses first. Four drawings tell the whole leap.", N), (8.0, "Then the breakdowns. They say how the move happens.", N),
                                        (12.0, "Then the in-betweens, close together where the fish is slow.", N), (17.0, "Play them, and the fish jumps.", N),
                                        (19.6, "A drawing means something because of the drawing before it and the drawing after it.", N)]),
        segment("s_planes", 17.5, s_planes, [(0.6, "It builds depth in planes. Watch the camera move.", N), (4.4, "Near layers move more. Far layers move less.", N), (9.4, "That one rule turns flat paper into a river.", N)]),
        segment("s_problem", 20.5, s_problem, [(0.6, "But one desk does one job at a time.", N), (3.4, "Ask it for a hundred times more, and the hard part is no longer drawing.", N), (9.8, "It is watching.", N),
                                              (15.5, "And the desk checks its own work. It cannot see what it cannot see.", N)]),
        segment("s_four", 24.5, s_four, [(0.4, "So a second prompt asks four questions.", N), (2.6, "Where does the work live? In a project state every agent can read.", N),
                                        (7.2, "Who works when? Many agents at once.", N), (11.8, "Who checks? A critic who built nothing.", N), (16.4, "When do we look? From the first day, at a rough cut.", N),
                                        (20.4, "Move verification from syntax to invariants.", N)]),
        segment("s_chain", 23.0, s_chain, [(0.4, "The answer is a SCION.", N), (2.0, "It owns the whole viewing experience. It coordinates a swarm. It keeps the project state.", N),
                                          (9.6, "It tests against references you can inspect. It improves through independent critique.", N), (16.6, "And it delivers a finished film.", N)]),
        segment("s_laws", 29.0, s_laws, [(0.6, "A SCION has fifteen laws.", N), (12.0, "Law three. Prove the production method early. Build the hardest passage first.", N),
                                        (17.5, "Law nine. Never let the builder award the pass.", N), (22.5, "Law fourteen. Every finding is measured, structural, judged, or unknown.", N)],
                sfx=[(tone, (12.0, 220)), (tone, (17.5, 262)), (tone, (22.5, 330))]),
        segment("s_how", 37.0, s_how(img(ST + "08_props.png"), img(ST + "12_wheel.png"), first_render(30.5, "hb"), final_frame(30.5, "ha")),
                [(0.4, "So how does a SCION animate? The craft does not go away. It is shared out.", N), (6.6, "One agent builds the world. The planes. The pieces.", N),
                 (12.0, "Other agents build the performances, from keys and timing.", N), (17.0, "An editor keeps a cut you can always play.", N),
                 (21.4, "And a critic who built nothing watches it at normal speed.", N), (25.6, "Every performance starts with a situation and an intention, and ends with a consequence.", N), (32.5, "Do not smooth away intention.", N)]),
        clip(9.0, 28.0),
        segment("s_end", 10.5, s_end, [(0.6, "Make every important claim about quality answerable by opening the work and watching it.", N)]),
    ]
    lst = TMP + "/s.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts)); out = "assets/what-is-a-scion.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
