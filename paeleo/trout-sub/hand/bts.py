#!/usr/bin/env python3
"""bts: who held the chalk. The making of "Nobody Is Holding the Chalk", told from its own record.

    python3 bts.py     # assets/who-held-the-chalk.mp4

Every number and quotation is read from the run: the ten agents' transcripts (bts_agents.json: commands,
archive requests, contact sheets, start and end times), the makers' and critics' reports (provenance.json),
the credits files, the brief, and frames of earlier renders kept in git history. Nothing is re-staged.
"""
import json, math, os, subprocess
from datetime import datetime
from PIL import Image, ImageDraw
import class_cut as C
from class_cut import W, H, TMP, F, PAPER, INK, MUTE, RUST, TEAL, GOLD, PENCIL, ease, back, lerp, segment, tone, whoosh
from scion_explainer import MONO, SERIF, table, sheet, typed, heading, img

AG = json.load(open("bts_agents.json")); PROV = json.load(open("provenance.json"))
ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
T0 = min(ts(a["start"]) for a in AG); T1 = max(ts(a["end"]) for a in AG)
TOTAL = {k: sum(a[k] for a in AG) for k in ("tools", "forage", "stills", "renders")}
ORDER = ["p01", "p03", "p14", "p35", "p44"]
NAME = {"p01": "01 scissors", "p03": "03 chalk", "p14": "14 scalpel", "p35": "35 pins", "p44": "44 pen"}


def grab(src, at, name, rev=None):
    png = "%s/%s.png" % (TMP, name); path = src
    if rev:
        path = "%s/%s_%s.mp4" % (TMP, name, rev)
        open(path, "wb").write(subprocess.run(["git", "show", "%s:paeleo/trout-sub/hand/%s" % (rev, src)], capture_output=True, check=True).stdout)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", path, "-frames:v", "1", "-vf", "scale=960:540", png], check=True); return img(png)


def clip(src, start, seconds, name, text=None):
    out = "%s/%s.mp4" % (TMP, name)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(seconds), "-i", src, "-vf", "fps=24,scale=960:540,fade=t=out:st=%.2f:d=0.4" % (seconds - 0.4),
                    "-af", "volume=0.6,afade=t=out:st=%.2f:d=0.6" % (seconds - 0.6), "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], check=True)
    return out


def s_question(frame):
    def draw(t):
        im = frame.copy(); d = ImageDraw.Draw(im); d.rectangle((0, 0, W, H), fill=None)
        im = Image.blend(im, Image.new("RGB", (W, H), (12, 18, 20)), 0.55 * ease(t / 0.8)); d = ImageDraw.Draw(im)
        if t > 0.6: d.text((70, 170), "NOBODY IS HOLDING", font=F(60), fill=PAPER); d.text((70, 240), "THE CHALK.", font=F(60), fill=PAPER)
        if t > 3.4: d.text((70, 330), "So who made this?", font=F(44), fill=PENCIL)
        return im
    return draw


CAST = [(0.8, "1", "PERSON", "the director", "said what to make and what to throw out", RUST),
        (5.6, "1", "CONDUCTOR", "a language model", "wrote the brief and the script for the others", INK),
        (10.6, "5", "MAKERS", "language model agents", "one film each, from an empty file", TEAL),
        (14.8, "5", "CRITICS", "language model agents", "each judged a film it did not make", GOLD)]


def s_cast(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "WHO WAS IN THE ROOM")
    for k, (at, n, role, kind, did, col) in enumerate(CAST):
        if t < at: continue
        u = back((t - at) / 0.4); x = 40 + k * 226; y = int(lerp(560, 120, u)); d = sheet(im, (x, y, x + 208, y + 330))
        d.text((x + 104 - d.textlength(n, font=F(120)) / 2, y + 8), n, font=F(120), fill=col)
        d.text((x + 104 - d.textlength(role, font=F(26)) / 2, y + 150), role, font=F(26), fill=INK)
        d.text((x + 104 - d.textlength(kind, font=F(15, "SemiBold")) / 2, y + 186), kind, font=F(15, "SemiBold"), fill=MUTE)
        words = did.split(); lines = [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])]
        for j, ln in enumerate(lines): d.text((x + 104 - d.textlength(ln, font=SERIF(19)) / 2, y + 232 + j * 26), ln, font=SERIF(19), fill=INK)
    if t > 19.0: d.text((40, 478), "Twelve in all. Eleven of them are not people.", font=F(28), fill=PAPER)
    return im


def s_reject(bad):
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "THE FIRST TRY WAS THROWN OUT")
        im.paste(bad.resize((440, 248), Image.LANCZOS), (40, 120)); d = ImageDraw.Draw(im)
        if t > 3.0:
            u = back((t - 3.0) / 0.35); s = int(46 * u)
            if s > 4: d.text((66, 216), "REJECTED", font=F(s), fill=RUST)
        if t > 4.6: d.text((40, 382), "the director:", font=F(17, "SemiBold"), fill=(226, 212, 186)); typed(d, (40, 408), "\"we need to see it being drawn\"", SERIF(26), PAPER, (t - 4.8) / 1.2)
        if t > 7.6: typed(d, (40, 446), "\"spend some time handmaking this\"", SERIF(26), PAPER, (t - 7.6) / 1.2)
        if t > 10.4:
            d = sheet(im, (510, 120, 930, 420)); d.text((530, 136), "THE BRIEF, RULE ONE", font=F(19), fill=RUST)
            for j, ln in enumerate(("Handmake", "or forage.", "No style", "costumes.")): d.text((530, 172 + j * 56), ln, font=F(50), fill=INK)
        return im
    return draw


RULES = [(0.8, "1", "A CLAIM TO PROVE", "The first third shows the thing being made.", RUST), (5.4, "2", "ONE HARD SCENE", "Chalk letters HOOK MONSTER, one stroke at a time.", GOLD),
         (10.2, "3", "A JOB FOR EACH AGENT", "one maker for each film", TEAL), (13.8, "4", "A JUDGE WHO BUILT NOTHING", "one critic for each film, with fresh eyes", INK)]


def s_rules(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "THE RULES THE CONDUCTOR WROTE", "the four parts of a SCION prompt, as used here"); d = sheet(im, (110, 100, 850, 510))
    for at, n, head, body, col in RULES:
        if t < at: continue
        k = int(n) - 1; y = 122 + k * 96; x = int(lerp(900, 140, back((t - at) / 0.4)))
        d.ellipse((x, y, x + 56, y + 56), fill=col); d.text((x + 28 - d.textlength(n, font=F(32)) / 2, y + 8), n, font=F(32), fill=PAPER)
        d.text((x + 76, y - 2), head, font=F(27), fill=INK); typed(d, (x + 76, y + 36), body, SERIF(24), MUTE, (t - at - 0.4) / 1.3)
    return im


CLOCK = 24.0                                       # seconds of screen time for the 2 h 43 min run
def s_timeline(thumbs):
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "TWO HOURS AND FORTY-THREE MINUTES", "each bar is one agent at work")
        now = T0 + (T1 - T0) * min(1, max(0, (t - 1.0) / CLOCK)); X0, X1 = 150, 760
        X = lambda s: X0 + (X1 - X0) * (s - T0) / (T1 - T0)
        for k, pid in enumerate(ORDER):
            y = 118 + k * 62; d.text((30, y + 6), NAME[pid], font=F(17), fill=PAPER)
            for a in AG:
                if not a["label"].endswith(pid): continue
                s, e = ts(a["start"]), ts(a["end"])
                if now < s: continue
                col = TEAL if a["label"].startswith("make") else GOLD; yy = y if a["label"].startswith("make") else y + 22
                d.rounded_rectangle((X(s), yy, max(X(s) + 4, X(min(now, e))), yy + 18), 4, fill=col)
                n = int(a["tools"] * min(1, (now - s) / (e - s)))
                if a["label"].startswith("make"): d.text((X(min(now, e)) + 6, yy), "%d commands" % n, font=F(13, "SemiBold"), fill=(226, 212, 186))
                if now >= e and a["label"].startswith("critic"):
                    im.paste(thumbs[pid].resize((100, 56), Image.LANCZOS), (806, y - 4)); d = ImageDraw.Draw(im)
        d.line((X(now), 108, X(now), 430), fill=PAPER, width=2)
        d.text((X(now) - 24, 432), datetime.utcfromtimestamp(now).strftime("%H:%M"), font=F(15), fill=PAPER)
        d.rectangle((150, 452, 166, 468), fill=TEAL); d.text((172, 450), "maker", font=F(15, "SemiBold"), fill=PAPER); d.rectangle((250, 452, 266, 468), fill=GOLD); d.text((272, 450), "critic", font=F(15, "SemiBold"), fill=PAPER)
        f = min(1, max(0, (t - 1.0) / CLOCK))
        for j, (k, lab) in enumerate((("tools", "commands run"), ("forage", "archive requests"), ("stills", "looks at its own frames"), ("renders", "full renders"))):
            d.text((40 + j * 228, 478), str(int(TOTAL[k] * f)), font=F(40), fill=PENCIL); d.text((40 + j * 228 + d.textlength(str(TOTAL[k]), font=F(40)) + 10, 496), lab, font=F(15, "SemiBold"), fill=PAPER)
        return im
    return draw


def s_maker(frame, credits):
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "ONE MAKER: PORTHOLE 35", "%d commands, %d archive requests" % (next(a["tools"] for a in AG if a["label"] == "make:p35"), next(a["forage"] for a in AG if a["label"] == "make:p35")))
        im.paste(frame.resize((400, 225), Image.LANCZOS), (530, 120)); d = ImageDraw.Draw(im); d.text((530, 352), "the film it rendered", font=F(17), fill=PAPER)
        for j, c in enumerate(credits):
            at = 1.6 + j * 2.2
            if t < at: continue
            u = back((t - at) / 0.35); x = int(lerp(-480, 30, u)); y = 116 + j * 62; d = sheet(im, (x, y, x + 470, y + 52), shadow=False)
            d.text((x + 10, y + 5), c["title"].split("(")[0].strip()[:48], font=SERIF(19), fill=INK); d.text((x + 10, y + 29), "Library of Congress, FSA/OWI · no known restrictions", font=F(12, "SemiBold"), fill=MUTE)
        if t > 13.5: d.text((30, 440), "It kept five photographs and wrote down", font=F(22), fill=PAPER); d.text((30, 470), "where each one came from.", font=F(22), fill=PAPER)
        return im
    return draw


def s_critics(before, after):
    quote = "Turkey was too small in the tin to carry the 'class pet' reading."
    def draw(t):
        im = table(); d = ImageDraw.Draw(im); heading(d, "THEN THE CRITICS LOOKED", "none of them had made a film")
        for k, pid in enumerate(["p03", "p14", "p01", "p44", "p35"]):
            at = 0.8 + k * 1.1
            if t < at: continue
            v = PROV[pid]["critic"]["verdict"].upper(); col = (120, 214, 200) if v == "PASS" else PENCIL
            d.text((30 + k * 184, 104), NAME[pid], font=F(16), fill=PAPER); d.text((30 + k * 184, 124), v, font=F(30), fill=col)
        if t > 7.0:
            im.paste(before.resize((400, 225), Image.LANCZOS), (30, 190)); d = ImageDraw.Draw(im); d.text((30, 420), "porthole 03, the maker's cut", font=F(16), fill=PAPER)
            d.ellipse((270, 196, 372, 268), outline=RUST, width=4)
        if t > 9.0: typed(d, (30, 452), "\"" + quote[:31], SERIF(22), PAPER, (t - 9.0) / 1.0); typed(d, (30, 480), " " + quote[32:] + "\"", SERIF(22), PAPER, (t - 10.0) / 1.2)
        if t > 14.0:
            im.paste(after.resize((400, 225), Image.LANCZOS), (500, 190)); d = ImageDraw.Draw(im); d.text((500, 420), "after the critic's repair", font=F(16), fill=PAPER)
            d.ellipse((770, 192, 890, 280), outline=TEAL, width=4)
        return im
    return draw


NOT = [(1.0, "Nobody listened to the sound.", "No agent can hear. No person has yet."), (6.4, "It was called a swarm.", "It was one maker and one critic for each film."),
       (12.0, "The trout did not make it.", "That ending was written last, by the conductor.")]


def s_not(t):
    im = table(); d = ImageDraw.Draw(im); heading(d, "WHAT NOBODY DID"); d = sheet(im, (110, 110, 850, 480))
    for k, (at, a, b) in enumerate(NOT):
        if t < at: continue
        y = 136 + k * 112; d.text((140, y), a, font=F(32), fill=RUST); typed(d, (140, y + 44), b, SERIF(25), INK, (t - at - 0.6) / 1.3)
    return im


def s_end(t):
    im = table(); d = sheet(im, (130, 130, 830, 420))
    d.text((170, 160), "SOMEBODY WROTE", font=F(54), fill=INK); d.text((170, 224), "THE RULES.", font=F(54), fill=RUST)
    if t > 3.4: d.text((170, 308), "Then nobody held the chalk.", font=F(36), fill=TEAL)
    return im


if __name__ == "__main__":
    N = "narrator"; film = "assets/nobody-is-holding-the-chalk.mp4"
    thumbs = {p: grab("assets/films/%s.mp4" % p, 20, "th_" + p) for p in ORDER}
    cred = [c for c in json.load(open("films/credits/p35.json")) if "LC-USF" in c["title"] or "Pie Town" in c["title"]][:5]
    hrs = "Five makers, two at a time. Then five critics. Together they ran %d commands, asked the archives %d times, and looked at their own frames %d times." % (TOTAL["tools"], TOTAL["forage"], TOTAL["stills"])
    parts = [
        clip(film, 162.0, 7.0, "open"),
        segment("b_q", 7.0, s_question(grab(film, 168.8, "qf")), [(0.6, "Nobody is holding the chalk.", N), (3.4, "So who made this?", N)], sfx=[(tone, (3.3, 196))]),
        segment("b_cast", 23.0, s_cast, [(0.8, "One person. The director. They said what to make, and what to throw out.", N), (5.6, "One conductor. A language model that wrote the rules for the others.", N),
                                         (10.6, "Five makers. One film each.", N), (14.8, "And five critics. Each one judged a film it did not make.", N), (19.0, "Twelve in all. Eleven of them are not people.", N)],
                sfx=[(tone, (at, 180 + 36 * k)) for k, (at, *_) in enumerate(CAST)]),
        segment("b_rej", 16.0, s_reject(grab("../youtube/tks-how-it-works.mp4", 40, "rej")),
                [(0.5, "The first try was thrown out. It only dressed up as hand made.", N), (4.8, "The director said: we need to see it being drawn.", N), (10.4, "So the brief got one hard rule. Handmake or forage. No style costumes.", N)],
                sfx=[(tone, (3.0, 120, 0.4, 0.5))]),
        segment("b_rules", 19.0, s_rules, [(0.8, "The conductor wrote the rules. A claim to prove.", N), (5.4, "One hard scene for each film.", N), (10.2, "A job for each agent.", N), (13.8, "And a judge who built nothing.", N)]),
        segment("b_time", 1.0 + CLOCK + 5.0, s_timeline(thumbs), [(0.8, "Then the conductor stepped back. This is the real clock, sped up.", N), (7.0, hrs, N)]),
        segment("b_maker", 18.0, s_maker(grab("assets/films/p35.mp4", 12, "p35f"), cred),
                [(0.6, "Look at one maker. For porthole thirty five it asked the Library of Congress for mailboxes.", N), (8.0, "It cut them out, pinned them down, and built a film from them.", N), (13.5, "It kept five photographs, and wrote down where each one came from.", N)]),
        segment("b_crit", 20.0, s_critics(grab("assets/films/p03.mp4", 31, "p03b", rev="107d776"), grab("assets/films/p03.mp4", 31, "p03a")),
                [(0.6, "Then the critics looked. One film passed. Four were nearly right.", N), (7.0, "For porthole three, the critic wrote: Turkey was too small in the tin.", N), (14.0, "So the critic made the tin bigger, and rendered the film again.", N)],
                sfx=[(tone, (14.0, 392))]),
        segment("b_not", 18.5, s_not, [(1.0, "Here is what nobody did. Nobody listened to the sound.", N), (6.4, "It was called a swarm. It was one maker and one critic for each film.", N),
                                       (12.0, "And the trout did not make it. That ending was written last, by the conductor.", N)]),
        clip(film, 196.5, 9.5, "room"),
        segment("b_end", 8.5, s_end, [(0.6, "Somebody wrote the rules.", N), (3.4, "Then nobody held the chalk.", N)], sfx=[(tone, (3.3, 262))]),
    ]
    lst = TMP + "/b.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts)); out = "assets/who-held-the-chalk.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out, TOTAL)
