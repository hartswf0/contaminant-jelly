#!/usr/bin/env python3
"""final_cut: the whole thing in one film. How the game is played, then for each of five portholes: the
children working through the sheet (the making film, mNN), and then what they pictured (the class film, cNN).

    python3 final_cut.py     # assets/tourkey-trouttown-the-class-plays.mp4

Built from class_cut.py's pieces: the paper mat with its teaching strip (step and question under every
picture), the brass-porthole bridges with one thing to watch for, the opening rules and the closing "your turn".
Every sentence inside the films is a child's own; the strip and the narrator are ours.
"""
import json, os, subprocess, sys
from PIL import Image
import class_cut as C
from class_cut import segment, say, whoosh, tone, mat, SR, TMP, W, H, FPS

# Section starts in each making film: (pilot, turkey's seat, river, ending). Read off films/mNN.py.
MTIMES = {10: (0, 32.0, 57.5, 81.5), 13: (0, 32.0, 57.5, 79.0), 16: (0, 30.0, 55.0, 78.0), 25: (0, 35.6, 60.6, 84.1), 33: (0, 33.0, 57.0, 80.0)}
TRIM = 7.0                     # the class film's own pencil drawing is cut: the making film has just drawn it
MAKE_SAY = {
 10: "First, watch them work. The pilot draws a jaw, and writes about french fries and a locked school.",
 13: "Watch the pilot draw a fish that says, haha very funny. Then a friend sits in Turkey's seat.",
 16: "This pilot draws small, at the top of the ring. The friends each write only one ending. Watch them think.",
 25: "Watch the pilot write panic. Turkey panics in every ending after that. The last friend runs right off the paper.",
 33: "This pilot draws bars across the whole window. Watch the friends try to see them from Turkey's seat, and from the river.",
}
SEE = ("NOW SEE WHAT THEY PICTURED", "The same sentences, acted out.", "Now see what they pictured. The same sentences, acted out.")


def making_hints(n):
    pid = "m%d" % n; a, b, c, d = MTIMES[n]; s = C.SHEETS[n]
    lines = json.load(open("films/notes/%s.voice.json" % pid))["lines"]
    ev = [(0.0, 0, "The pilot reads the questions and pictures what is outside.")]
    for ask, l in zip(C.ASK, lines[:3]): ev.append((l["at"] - 2.0, 0, "Writing: " + ask))
    ev.append((b, 1, "Passed! Now picture sitting in Turkey's seat, looking out."))
    q = 3
    for f, st, t0 in (("first_friend", 1, b), ("next_friend", 2, c)):
        if st == 2: ev.append((c, 2, "Passed again! Now picture being a trout, looking back at the sub."))
        fr = s[f]
        if not (fr["picked"] or any(fr[k] for k in C.KIND)):
            ev.append((t0 + 6, st, "This friend did not write. Being stuck is part of it."))
        for k in C.KIND:
            if fr[k] and fr[k].get("reads"): ev.append((lines[q]["at"] - 2.0, st, "Writing " + C.KIND[k])); q += 1
    ev.append((d, 3, "Nobody has rolled the die yet."))
    return sorted(ev)


def strip(src, out, ev, idx, ss=0.0):
    """Re-frame a film onto the mat with its teaching strip; ss trims its start."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout) - ss
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(ss), "-i", src, "-vf", "fps=24,scale=960:540", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-ss", str(ss), "-i", src,
                           "-map", "0:v", "-map", "1:a", "-af", "afade=t=in:d=0.4", "-t", "%.3f" % dur, "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    i = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        t = i / float(FPS) + ss; cur = [e for e in ev if e[0] <= t] or [ev[0]]; cur = cur[-1]
        wr.stdin.write(mat(Image.frombytes("RGB", (W, H), buf), cur[1], cur[2], dots=idx).tobytes()); i += 1
    wr.stdin.close(); wr.wait(); return out


def frame_of(path, at):
    png = "%s/f_%s_%s.png" % (TMP, os.path.basename(path), at)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + (["-sseof", "-0.2"] if at == "last" else ["-ss", str(at)]) + ["-i", path, "-frames:v", "1", "-vf", "scale=960:540", png], check=True)
    return Image.open(png).convert("RGB")


def bridge(prev, nxt, n, idx, slip, line, name):
    secs = round(len(say(line)) / SR + 4.6, 1)
    C.LESSON[n] = (slip[0], slip[1], line)
    return segment(name, secs, C.bridge(prev, nxt, n, idx, secs), [(2.6, line, "narrator")],
                   sfx=[(whoosh, (0.1,)), (whoosh, (1.6, 1.4)), (tone, (2.4, 150, 0.2, 0.5)), (whoosh, (secs - 1.2,))])


if __name__ == "__main__":
    lessons = {n: C.LESSON[n] for n in C.ORDER}
    parts = [segment("title", 7.0, C.title, [(2.6, "How to play the porthole game. Five kids already played. Watch them work. Then watch what they pictured. Then it is your turn.", "narrator")],
                     sfx=[(tone, (1.2, 196)), (tone, (1.5, 220)), (tone, (1.8, 262)), (tone, (2.1, 330))]),
             segment("rules", C.RULES_SECONDS, C.rules, [(at + 0.4, l, "narrator") for at, _, _, _, l in C.RULES], sfx=[(tone, (at, 180 + 40 * k)) for k, (at, *_) in enumerate(C.RULES)])]
    prev = C.rules(C.RULES_SECONDS - 0.05).crop((C.FX, C.FY, C.FX + C.FW, C.FY + C.FH)).resize((W, H))
    for idx, n in enumerate(C.ORDER):
        msrc, csrc = "assets/voiced/m%d.mp4" % n, "assets/voiced/c%d.mp4" % n
        t, s, _ = lessons[n]
        parts.append(bridge(prev, frame_of(msrc, 0.3), n, idx, (t, s), "Porthole %d. " % n + MAKE_SAY[n], "b1_%d" % n))
        parts.append(strip(msrc, "%s/sm%d.mp4" % (TMP, n), making_hints(n), idx))
        parts.append(bridge(frame_of(msrc, "last"), frame_of(csrc, TRIM + 0.2), n, idx, SEE[:2], SEE[2] + " Watch for this: " + lessons[n][2].split(". ", 1)[1], "b2_%d" % n))
        parts.append(strip(csrc, "%s/sc%d.mp4" % (TMP, n), C.film_hints(n), idx, ss=TRIM))
        prev = frame_of(csrc, "last"); print("cut", n, flush=True)
    parts.append(segment("ending", C.END_SECONDS, C.ending(prev),
                         [(1.4, "Now it is your turn.", "narrator"), (3.6, "Draw what is outside.", "narrator"), (5.6, "Pass it. A friend picks for Turkey.", "turkey"),
                          (8.0, "Pass it again. The trout get a turn.", "trout"), (10.4, "Roll the die.", "narrator"), (12.4, "Blank is okay. Wild is good. Being stuck is okay too. What is outside your porthole?", "narrator")],
                         sfx=[(whoosh, (0.1,))] + [(tone, (at, 196 + 44 * k)) for k, at in enumerate((3.6, 5.6, 8.0, 10.4))]))
    lst = TMP + "/list.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in parts))
    out = "assets/tourkey-trouttown-the-class-plays.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    print(out)
