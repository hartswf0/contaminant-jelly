#!/usr/bin/env python3
"""scion_explainer: how a language model makes a film with a SCION prompt, shown on one real film.

    python3 scion_explainer.py     # assets/how-a-language-model-makes-a-film.mp4

Everything shown is from the making of the class film for porthole 13: its page (as transcribed), the
four parts of its instructions, lines of the code the agents wrote, the pieces that code draws, the
first render beside the repaired one, and the finished film. Nothing is staged for the explainer.
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import class_cut as C
from class_cut import W, H, FPS, SR, TMP, F, PAPER, INK, MUTE, RUST, TEAL, GOLD, PENCIL, ease, back, lerp, segment, say, tone, whoosh

MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", s)
SERIF = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", s)
ST = "films/stills/c13_world/"
img = lambda p: Image.open(p).convert("RGB")


def first_render(at, name):
    """A frame of the film as first rendered, before the critic (kept in git history)."""
    mp4 = TMP + "/c13_first.mp4"
    if not os.path.exists(mp4):
        open(mp4, "wb").write(subprocess.run(["git", "show", "8b0b79a:paeleo/trout-sub/hand/assets/films/c13.mp4"], capture_output=True, check=True).stdout)
    png = "%s/%s.png" % (TMP, name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", mp4, "-frames:v", "1", png], check=True); return img(png)


def final_frame(at, name):
    png = "%s/%s.png" % (TMP, name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", "assets/films/c13.mp4", "-frames:v", "1", png], check=True); return img(png)


def table():
    return C.WOOD.copy()


def sheet(im, box, shadow=True):
    d = ImageDraw.Draw(im); x0, y0, x1, y1 = box
    if shadow: d.rectangle((x0 + 6, y0 + 8, x1 + 6, y1 + 8), fill=(40, 28, 16))
    d.rectangle(box, fill=PAPER); return ImageDraw.Draw(im)


def typed(d, xy, text, font, fill, u):
    d.text(xy, text[:int(len(text) * min(1, max(0, u)) + 0.5)], font=font, fill=fill)


def heading(d, text, sub=None):
    d.text((40, 22), text, font=F(34), fill=PAPER)
    if sub: d.text((42, 64), sub, font=F(19, "SemiBold"), fill=(226, 212, 186))


# ---------- scenes ----------
def s_title(t):
    im = table(); d = sheet(im, (150, 110, 810, 430)); u = ease(t / 0.6)
    d.text((190, 150), "HOW A LANGUAGE", font=F(52), fill=INK); d.text((190, 212), "MODEL MAKES", font=F(52), fill=INK); d.text((190, 274), "A FILM", font=F(84), fill=RUST)
    if t > 1.4: d.text((194, 376), "with a SCION prompt. One real film, start to finish.", font=F(20, "SemiBold"), fill=MUTE)
    if t > 0.8:                                                        # a stick of chalk writing with no hand on it
        x = 560 + 150 * ease((t - 0.8) / 3.0); y = 330 + 6 * math.sin(t * 9)
        d.line((560, 338, x, 338), fill=RUST, width=5); d.rounded_rectangle((x - 6, y - 46, x + 12, y + 4), 4, fill=(244, 241, 232), outline=(150, 150, 150))
    return im


def s_two(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "TWO WAYS TO MAKE A FILM")
    for k, (x, title, col) in enumerate(((40, "1  GUESS THE PIXELS", MUTE), (500, "2  WRITE THE RULES", TEAL))):
        if t < k * 6.0: continue
        q = t - k * 6.0; d = sheet(im, (x, 110, x + 420, 500)); d.text((x + 20, 124), title, font=F(24), fill=col)
        d.rounded_rectangle((x + 20, 168, x + 400, 206), 8, outline=MUTE, width=2)
        typed(d, (x + 30, 176), "a trout rings a bell" if k == 0 else "captions must match the page", MONO(16), INK, q / 1.2)
        if q > 1.6: d.text((x + 196, 212), "▼", font=F(22), fill=MUTE)
        if k == 0 and q > 2.0:                                          # the same ring, wandering from frame to frame
            for j in range(3):
                dx, dy, r = [(0, 0, 44), (9, -6, 49), (-7, 8, 40)][j]
                cx = x + 80 + j * 130 + dx * min(1, (q - 2) / 2); cy = 330 + dy * min(1, (q - 2) / 2)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(176, 132, 44), width=9); d.ellipse((cx - 14, cy - 8, cx + 16, cy + 8), fill=(120, 140, 136))
            if q > 4.0: d.text((x + 20, 430), "Nobody can say why a frame looks this way.", font=F(17, "SemiBold"), fill=RUST)
        if k == 1 and q > 2.0:
            for j, ln in enumerate(("def bell(ink, hang, swing):", "def trout_on_circle(ink, c, r):", "assert len(CAPTIONS) == 6")):
                typed(d, (x + 24, 250 + j * 26), ln, MONO(15), INK, (q - 2.0 - j * 0.7) / 0.8)
            if q > 4.4:
                for j in range(3):
                    cx = x + 80 + j * 130; d.ellipse((cx - 36, 362, cx + 36, 434), outline=(176, 132, 44), width=8); d.ellipse((cx - 14, 390, cx + 16, 406), fill=(120, 140, 136))
            if q > 5.6: d.text((x + 20, 452), "The code draws every frame. You can read why.", font=F(17, "SemiBold"), fill=TEAL)
    return im


PARTS = [(4.0, "1", "A CLAIM TO PROVE", "Every sentence on screen is the child's own.", RUST),
         (7.2, "2", "ONE HARD SCENE", "\"The dinner bell goes off and the fish go crazy.\"", GOLD),
         (12.4, "3", "A JOB FOR EACH AGENT", "story · world · three scenes · editor", TEAL),
         (17.8, "4", "A JUDGE WHO BUILT NOTHING", "critic · rights reviewer", INK)]


def s_card(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE SCION PROMPT", "four parts, here for porthole 13")
    d = sheet(im, (110, 100, 850, 510))
    for at, n, head, body, col in PARTS:
        if t < at: continue
        k = int(n) - 1; u = back((t - at) / 0.4); y = 122 + k * 96; x = int(lerp(900, 140, u))
        d.ellipse((x, y, x + 56, y + 56), fill=col); d.text((x + 28 - d.textlength(n, font=F(32)) / 2, y + 8), n, font=F(32), fill=PAPER)
        d.text((x + 76, y - 2), head, font=F(27), fill=INK); typed(d, (x + 76, y + 36), body, SERIF(24), MUTE, (t - at - 0.5) / 1.4)
    return im


PAGE = [(0.6, "Pilot S. drew:", "two fish, a bell, and a speech bubble: haha verry funny", 0),
        (4.2, "Who is outside?", "The trout. The trout think the sub is a bell-ringer prank.", 0),
        (7.6, "Friend A. wrote:", "The dinner bell to go off.", 1), (9.2, "", "The dinner bell goes off and the fish go crazy.", 1), (10.8, "", "The fish go quiet and calm.", 1),
        (12.6, "Friend M. wrote:", "", 2)]


def s_page(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE PAGE", "what three fourth graders wrote, as transcribed")
    d = sheet(im, (130, 100, 830, 516)); y = 118
    for at, label, text, who in PAGE:
        if label:
            y += 8
            if t > at: d.text((156, y), label, font=F(17, "SemiBold"), fill=(RUST, RUST, TEAL)[who])
            y += 26
        if text:
            if t > at: typed(d, (156, y), text, SERIF(23), INK, (t - at) / 1.3)
            d.line((156, y + 30, 800, y + 30), fill=(214, 206, 188), width=1); y += 38
        else:
            for j in range(3):
                d.line((156, y + 30, 800, y + 30), fill=(214, 206, 188), width=1); y += 38
            if t > at + 1.0: d.text((560, y - 100), "left blank", font=F(22), fill=MUTE)
    return im


CODE = ["# world.py, written by the world agent", "def trout_on_circle(ink, c, r, clock_deg, length=150):", "def bell(ink, hang=None, scale=1.0, swing=0.0):", "def bubble_on(ink, x, y, heading, length):", "",
        "# c13.py, written by the editor agent", "CAPTIONS = [", '  (23.3, 27.7, "The dinner bell to go off."),', '  (28.3, 33.7, "The dinner bell goes off',  '                and the fish go crazy."),',
        '  (34.4, 40.0, "The fish go quiet and calm."),', "]", "assert len(CAPTIONS) == 6"]


def s_code(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE AGENTS WRITE CODE", "they do not paint")
    d.rectangle((30, 100, 500, 516), fill=(22, 28, 30))
    for j, ln in enumerate(CODE):
        col = (130, 150, 150) if ln.startswith("#") else ((236, 178, 46) if ln.startswith("assert") else (226, 230, 224))
        typed(d, (44, 112 + j * 30), ln, MONO(13), col, (t - 0.6 - j * 1.25) / 1.0)
    shots = [(2.0, ST + "08_props.png"), (8.5, ST + "07_turkeys.png"), (13.5, ST + "12_wheel.png")]
    cur = [p for at, p in shots if t >= at]
    if cur:
        pic = img(cur[-1]).resize((420, 236), Image.LANCZOS); d.rectangle((516, 176, 944, 420), fill=PAPER); im.paste(pic, (520, 180))
        d = ImageDraw.Draw(im); d.text((520, 428), ["the pieces the code draws", "Turkey, in eight moods", "one frame, from the code"][len(cur) - 1], font=F(18, "SemiBold"), fill=PAPER)
    if t > 17.0:
        d.rounded_rectangle((30, 452, 500, 516), 0, fill=(60, 44, 12)); d.text((44, 462), "If the captions do not match", font=F(19), fill=PENCIL); d.text((44, 486), "the page, the film will not run.", font=F(19), fill=PENCIL)
    return im


def s_judge(before, after):
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "THE JUDGE BUILT NOTHING", "so the judge can say no")
        for k, (pic, x, label, at) in enumerate(((before, 30, "first render", 0.5), (after, 500, "after the repair", 13.0))):
            if t < at: continue
            im.paste(pic.resize((430, 242), Image.LANCZOS), (x, 120)); d = ImageDraw.Draw(im); d.text((x, 368), label, font=F(20), fill=PAPER)
        if t > 4.0:                                                     # where the fault is, on the first render
            d.ellipse((216, 128, 300, 196), outline=RUST, width=5)
        if t > 5.0:
            u = back((t - 5.0) / 0.35); s = int(40 * u)
            if s > 4: d.text((36, 404), "VERDICT: NEARLY", font=F(s), fill=RUST)
        if t > 7.0: typed(d, (36, 456), "\"The speech bubble floats loose.", SERIF(24), PAPER, (t - 7.0) / 1.2)
        if t > 8.6: typed(d, (36, 486), " Tie it to the trout that says it.\"", SERIF(24), PAPER, (t - 8.6) / 1.2)
        if t > 14.2:
            d.ellipse((746, 252, 830, 320), outline=TEAL, width=5); d.text((506, 404), "REPAIRED", font=F(40), fill=(120, 214, 200))
        return im
    return draw


LEDGER = [(1.0, "MEASURED", "The six captions match the page.", TEAL), (5.2, "JUDGED BY A VIEWER", "The speech bubble looked loose.", GOLD),
          (9.4, "UNKNOWN", "Nobody has listened to the sound yet.", RUST)]


def s_ledger(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "EVERY CLAIM GETS A LABEL"); d = sheet(im, (130, 110, 830, 470))
    for k, (at, lab, text, col) in enumerate(LEDGER):
        if t < at: continue
        y = 140 + k * 104; w = d.textlength(lab, font=F(22)) + 28
        d.rounded_rectangle((160, y, 160 + w, y + 40), 8, fill=col); d.text((174, y + 6), lab, font=F(22), fill=PAPER)
        typed(d, (160, y + 50), text, SERIF(26), INK, (t - at - 0.3) / 1.2)
    return im


def s_end(t):
    im = table(); d = sheet(im, (150, 120, 810, 430))
    d.text((190, 150), "WHO IS HOLDING", font=F(54), fill=INK); d.text((190, 214), "THE CHALK?", font=F(54), fill=INK)
    if t > 3.2: d.text((190, 296), "Whoever writes the rules.", font=F(38), fill=RUST)
    if t > 6.0: d.text((190, 362), "Now you write one.", font=F(30), fill=TEAL)
    return im


def clip(seconds, start):
    """Eight seconds of the finished film, with its own voices and music."""
    out = TMP + "/clip.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(seconds), "-i", "assets/voiced/c13.mp4", "-vf", "fps=24,scale=960:540,fade=t=in:d=0.3,fade=t=out:st=%.2f:d=0.4" % (seconds - 0.4),
                    "-af", "afade=t=in:d=0.3,afade=t=out:st=%.2f:d=0.5" % (seconds - 0.5), "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], check=True)
    return out


def parts():
    N = "narrator"
    return [
        segment("x_title", 7.5, s_title, [(1.2, "How does a language model make a film? Watch one get made.", N)], sfx=[(tone, (0.3, 196)), (tone, (0.8, 262))]),
        segment("x_two", 17.0, s_two, [(0.6, "There are two ways. One. Type a caption, and a video model guesses the pixels.", N),
                                       (6.4, "Two. The model writes rules and code, and the code draws every frame. This film was made the second way.", N)], sfx=[(tone, (0.2, 180)), (tone, (6.0, 240))]),
        segment("x_card", 25.0, s_card, [(0.3, "The rules come from a SCION prompt. It has four parts.", N), (4.0, "A claim to prove.", N), (7.2, "One hard scene that proves it.", N),
                                         (12.4, "A job for each agent.", N), (17.8, "And a judge who built nothing.", N), (20.6, "The judge is the part people forget.", N)],
                sfx=[(tone, (at, 196 + 40 * k)) for k, (at, *_) in enumerate(PARTS)]),
        segment("x_page", 18.0, s_page, [(0.5, "Here is the page. One fourth grader drew two fish and a bell.", N), (7.4, "A friend wrote three endings.", N), (12.6, "The next friend left the lines blank. The film has to keep them blank.", N)]),
        segment("x_code", 22.0, s_code, [(0.5, "Now the agents work. They do not paint. They write code.", N), (5.4, "One agent builds the pieces. A trout. A bell. A turkey in eight moods.", N),
                                         (12.4, "Another agent writes each scene.", N), (16.4, "One line checks the captions against the page. If they do not match, the film will not run.", N)]),
        segment("x_judge", 19.0, s_judge(first_render(30.5, "before"), final_frame(30.5, "after")),
                [(0.5, "Then the judge watches. The judge built nothing, so the judge can say no.", N), (5.2, "Here the judge said, nearly.", N), (7.4, "The speech bubble floats loose. Tie it to the trout that says it.", N),
                 (12.8, "A repair agent fixed it, and the judge looked again.", N)], sfx=[(tone, (5.0, 130, 0.4, 0.5)), (tone, (14.2, 392))]),
        clip(9.0, 28.0),
        segment("x_ledger", 14.5, s_ledger, [(0.4, "Every claim gets a label.", N), (2.0, "Measured. The captions match the page.", N), (5.4, "Judged. The speech bubble looked loose.", N),
                                             (9.4, "Unknown. Nobody has listened to the sound yet.", N)]),
        segment("x_end", 10.0, s_end, [(0.6, "So who is holding the chalk?", N), (3.2, "Whoever writes the rules.", N), (6.0, "Now you write one.", N)], sfx=[(tone, (3.1, 262)), (tone, (5.9, 330))]),
    ]


if __name__ == "__main__":
    ps = parts(); lst = TMP + "/x.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in ps))
    out = "assets/how-a-language-model-makes-a-film.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
