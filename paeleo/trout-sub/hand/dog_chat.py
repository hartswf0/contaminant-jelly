#!/usr/bin/env python3
"""dog_chat: this chat, told the way IT'S ALL RIGHT tells its scene. A person at a door, and dogs.

    python3 dog_chat.py     # assets/behind-the-chat-dogs.mp4

The person at the door is the one who asks (Cool Radio). Claude is a dog. Every agent Claude started is a
different dog, and each dog on screen is a real telling from IT'S ALL RIGHT (bolas/paeleo/its-all-right),
where 54 animation SCIONs each told the same porch scene. Nothing is newly drawn here: this is an edit
of that footage against the record of this chat (chat_events.json and the saved agent transcripts).
  a tool call                  a dog goes out and comes back
  a file sent to the person    a dog lies down at the sill, and what it brought back is shown
  a swarm                      the wall of dogs: as many dogs light up as there were agents
  the person saying no         the dog backs away, then comes again
The words under the picture are the person's own, as typed, cut short.
"""
import json, math, os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
import class_cut as C
from class_cut import W, H, FPS, SR, TMP, F, PAPER, INK, PENCIL, RUST, TEAL, ease, say
from scion_explainer import SERIF

IAR = "/home/user/hartswf0/bolas/paeleo/its-all-right"
HANDS = {h["id"]: h for h in json.load(open(IAR + "/media/layout.json"))["hands"]}
EV = json.load(open("chat_events.json"))
N_USER = sum(1 for e in EV if e["who"] == "user"); N_TOOL = sum(1 for e in EV if e["who"] == "tool")
cnt = lambda name: sum(1 for e in EV if e["who"] == "tool" and e["name"] == name)
N_PROGRESS = sum(1 for e in EV if e["who"] == "user" and e["text"].lower().startswith("show me progress"))


def run(cmd, **k): return subprocess.run(cmd, check=True, **k)


def tile(src, idx, t, tw, th):
    """One telling's tile from a mosaic video at score time t."""
    col, row = idx % 9, idx // 9
    raw = run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", "%s/media/%s.mp4" % (IAR, src), "-frames:v", "1", "-vf", "crop=%d:%d:%d:%d" % (tw, th, col * 213 if src == "scenes" else col * tw, row * th),
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(th, tw, 3).astype(np.float32)


_start = {}
def start_of(i):
    """Where telling i begins in the long film, found by matching its mosaic tile at score second 20."""
    if i in _start: return _start[i]
    film = "come-in-1.mp4" if i <= 27 else "come-in-2.mp4"; est = 25 + 30 * (i - 1) if i <= 27 else 29.5 * (i - 28)
    ref = tile("scenes", i - 1, 20.0, 212, 120); best = (1e18, est)
    for k in range(-24, 25):
        t = est + 20 + k * 0.5
        if t < 0: continue
        raw = run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", "%s/films/%s" % (IAR, film), "-frames:v", "1", "-vf", "scale=213:120", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) < 213 * 120 * 3: continue
        f = np.frombuffer(raw, np.uint8).reshape(120, 213, 3).astype(np.float32)[:, :212]; e = float(((f - ref) ** 2).mean())
        if e < best[0]: best = (e, t - 20)
    _start[i] = (film, best[1]); print("telling %02d starts %.1f in %s (err %.0f)" % (i, best[1], film, best[0]), flush=True); return _start[i]


def lower(d, who, text, y=H - 78):
    d.rectangle((0, y, W, H), fill=(14, 18, 20, 215)); d.text((28, y + 10), who, font=F(15), fill=PENCIL)
    f = F(25, "SemiBold")
    while d.textlength(text, font=f) > W - 56 and len(text) > 10: text = text[:-2]
    d.text((28, y + 32), text, font=f, fill=PAPER)


def chip(d, text, col=RUST):
    w = d.textlength(text, font=F(17)) + 26; d.rounded_rectangle((20, 18, 20 + w, 52), 10, fill=col + (235,)); d.text((33, 24), text, font=F(17), fill=PAPER)


def shot(name, i, a, b, line=None, tag=None, col=RUST, speak=None, thumbs=None, speed=1.0):
    """Score seconds a..b of telling i, full frame, with the person's words under it."""
    film, st = start_of(i); dur = (b - a) / speed; out = "%s/%s.mp4" % (TMP, name)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", "%.3f" % (st + a), "-t", "%.3f" % (b - a), "-i", "%s/films/%s" % (IAR, film), "-vf", "setpts=PTS/%g,fps=24,scale=960:540" % speed,
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wav = voice(name, dur, speak)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", "24", "-i", "-", "-ss", "%.3f" % (st + a), "-t", "%.3f" % (b - a), "-i", "%s/films/%s" % (IAR, film), "-i", wav,
                           "-filter_complex", "[1:a]atempo=%g,volume=0.55[c];[c][2:a]amix=inputs=2:normalize=0[a]" % speed, "-map", "0:v", "-map", "[a]", "-t", "%.3f" % dur,
                           "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    k = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        t = k / 24.0; im = Image.frombytes("RGB", (W, H), buf); d = ImageDraw.Draw(im, "RGBA")
        if tag: chip(d, tag, col)
        d.text((W - 20 - d.textlength("dog: SCION %02d, %s" % (i, HANDS[i]["name"]), font=F(13, "SemiBold")), 26), "dog: SCION %02d, %s" % (i, HANDS[i]["name"]), font=F(13, "SemiBold"), fill=(236, 226, 204, 220))
        if thumbs:                                              # what the dog brought back
            n = int(min(1, t / max(0.1, dur - 0.8)) * len(thumbs))
            for j in range(n): im.paste(thumbs[j], (20 + j * 118, H - 78 - 76)); d = ImageDraw.Draw(im, "RGBA")
        if line: lower(d, "COOL RADIO", line)
        wr.stdin.write(im.tobytes()); k += 1
    wr.stdin.close(); wr.wait(); return out


def voice(name, dur, speak):
    y = np.zeros(int((dur + 0.3) * SR), np.float32)
    if speak:
        clip = say(speak); j = int(0.25 * SR); clip = clip[:max(0, len(y) - j)]; y[j:j + len(clip)] += clip * 1.35
    wav = "%s/%s.wav" % (TMP, name); sf.write(wav, y, SR); return wav


def wall(name, a, b, lit_at, line=None, tag=None, speak=None, dark_at=None, n_dark=0, blackout=None):
    """The wall of 54 dogs over score seconds a..b. lit_at(t) says how many dogs are awake."""
    dur = b - a; out = "%s/%s.mp4" % (TMP, name)
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", "%.3f" % a, "-t", "%.3f" % dur, "-i", IAR + "/media/dogs.mp4", "-vf", "fps=24,scale=864:460", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    wav = voice(name, dur, speak)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", "24", "-i", "-", "-ss", "%.3f" % a, "-t", "%.3f" % dur, "-i", IAR + "/media/audio.mp3", "-i", wav,
                           "-filter_complex", "[1:a]volume=0.5[c];[c][2:a]amix=inputs=2:normalize=0[a]", "-map", "0:v", "-map", "[a]", "-t", "%.3f" % dur,
                           "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    order = [(k * 23) % 54 for k in range(54)]; k = 0; tw, th = 96, 460 / 6.0
    while True:
        buf = rd.stdout.read(864 * 460 * 3)
        if len(buf) < 864 * 460 * 3: break
        t = k / 24.0; m = Image.frombytes("RGB", (864, 460), buf); im = Image.new("RGB", (W, H), (10, 12, 14)); im.paste(m, (48, 6)); d = ImageDraw.Draw(im, "RGBA")
        lit = lit_at(t); awake = set(order[:lit])
        if dark_at is not None and t > dark_at: awake -= set(order[lit - n_dark:lit][:int(min(1, (t - dark_at) / 1.5) * n_dark) or 0])
        for idx in range(54):
            if idx not in awake or (blackout and blackout[0] < t < blackout[1]):
                c, r = idx % 9, idx // 9; d.rectangle((48 + c * tw, 6 + r * th, 48 + (c + 1) * tw, 6 + (r + 1) * th), fill=(10, 12, 14, 232))
        if tag: chip(d, tag(t) if callable(tag) else tag, TEAL)
        if line: lower(d, "COOL RADIO", line, y=H - 70)
        wr.stdin.write(im.tobytes()); k += 1
    wr.stdin.close(); wr.wait(); return out


def card(name, dur, lines, speak=None):
    out = "%s/%s.mp4" % (TMP, name); wav = voice(name, dur, speak)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "960x540", "-r", "24", "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-t", "%.3f" % dur,
                           "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out], stdin=subprocess.PIPE)
    for k in range(int(dur * 24)):
        t = k / 24.0; im = Image.new("RGB", (W, H), (14, 18, 20)); d = ImageDraw.Draw(im)
        for j, (at, size, col, text) in enumerate(lines):
            if t > at: d.text((70, 150 + sum(l[1] + 22 for l in lines[:j])), text, font=F(size), fill=col)
        wr.stdin.write(im.tobytes())
    wr.stdin.close(); wr.wait(); return out


def thumbs_of(names):
    out = []
    for n in names:
        p = "assets/films/%s.webp" % n
        if os.path.exists(p): out.append(Image.open(p).convert("RGB").resize((112, 63), Image.LANCZOS))
    return out


if __name__ == "__main__":
    P = []
    P.append(card("d_title", 5.0, [(0.3, 64, PAPER, "BEHIND THE CHAT"), (1.6, 30, PENCIL, "A person at a door. A dog. And then a lot of dogs.")], "This is how Claude works. Watch the dogs."))
    P.append(shot("d_ask", 2, 8.0, 14.0, "we want to make a film for Trout Sub we have 55 portals", "CLAUDE LISTENS", speak="A person asks for something. Claude is the dog. Nobody can make it come. It has to go and find out."))
    P.append(shot("d_bash", 8, 14.7, 22.5, None, "TOOL: RUN A COMMAND  ×%d" % cnt("Bash"), TEAL, speak="Every time Claude uses a tool, a dog goes out, and comes back with something."))
    P.append(shot("d_read", 5, 9.0, 14.0, None, "TOOL: LOOK AT A FILE  ×%d" % cnt("Read"), TEAL, speak="Some dogs only look."))
    P.append(shot("d_send", 11, 22.0, 29.5, None, "TOOL: BRING IT BACK  ×%d" % cnt("SendUserFile"), TEAL, speak="And some carry a film back to the door.",
                  thumbs=thumbs_of(["p01", "p03", "p14", "p35", "p44", "c10", "c13"])))
    for j, i in enumerate((12, 13, 14, 15, 16, 17)):
        P.append(shot("d_prog%d" % j, i, 16.0, 17.6, "show me progress now", "ASKED %d OF %d TIMES" % (min(N_PROGRESS, (j + 1) * N_PROGRESS // 6), N_PROGRESS), speak="The person kept asking." if j == 0 else None))
    P.append(shot("d_one", 20, 9.5, 12.5, "Shouldn't we have swarms running, not just one agent, one thread?", "ONE DOG", speak="One dog was not enough."))
    P.append(wall("d_swarm", 14.7, 25.0, lambda t: 1 + int(min(1, t / 5.0) * 50), tag=lambda t: "A SWARM: %d AGENTS, EVERY ONE A DIFFERENT DOG" % (1 + int(min(1, t / 5.0) * 50)),
                  speak="So Claude sent a pack. Fifty one dogs. Every dog is a different helper, working at the same time."))
    P.append(wall("d_restart", 23.0, 28.0, lambda t: 51, tag="THE COMPUTER RESTARTED", blackout=(1.0, 2.6), speak="Once, the computer restarted. The dogs came back."))
    P.append(wall("d_limit", 3.4, 9.5, lambda t: 37, tag="11 DOGS RAN OUT OF ALLOWANCE", dark_at=1.2, n_dark=11, speak="Once, eleven dogs had to stop. They were the ones who check the work."))
    P.append(shot("d_alone", 23, 15.0, 20.0, "Finish it", "CLAUDE FINISHES ALONE", speak="So one dog finished it alone."))
    P.append(shot("d_no", 1, 0.6, 6.4, "Why do you make yhis a PowerPoint instead of cartoon? Why so many words.", "THE PERSON SAYS NO", speak="Sometimes the person says, no. That is wrong."))
    P.append(shot("d_again", 7, 14.7, 21.5, "Its only one agent.....", "CLAUDE TRIES AGAIN", speak="Then the dog comes again, a different way."))
    P.append(wall("d_six", 14.7, 21.0, lambda t: 1 if t < 1.5 else (6 if t < 3.6 else 17), tag=lambda t: "1 DOG" if t < 1.5 else ("6 DOGS AT ONCE" if t < 3.6 else "17 DOGS IN THIS PACK"), speak="One dog became six. Then seventeen."))
    P.append(shot("d_end", 2, 23.5, 31.0, "See how abstract this is for a kid?", "STILL GOING", thumbs=thumbs_of(["c16", "c25", "c33", "m10", "m13", "m16", "m25"]),
                  speak="%d asks. %d tools. One hundred and nine dogs. And the person is still at the door." % (N_USER, N_TOOL)))
    P.append(card("d_credit", 6.0, [(0.3, 26, PAPER, "Every dog is from IT'S ALL RIGHT,"), (0.3, 26, PAPER, "one porch scene told by 54 animation SCIONs."), (2.2, 22, PENCIL, "The words under the pictures are the person's own.")]))
    lst = TMP + "/d.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in P)); out = "assets/behind-the-chat-dogs.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]); print(out)
