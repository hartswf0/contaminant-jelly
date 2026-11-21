"""THE DOGS OF TROUTTOWN · the cut (editor: SCION laws 7, 8, 13).

Six sequences, each built by its own agent under its own animation SCION, played in order on one clock:

    S1 THE DOOR          0 to  28   films/swarm/dogs/s1.py   animation-48 (state machines)
    S2 TROUTTOWN        28 to  58   films/swarm/dogs/s2.py   animation-05 (atmospheric multiplane)
    S3 AGAIN, SOONER    58 to  84   films/swarm/dogs/s3.py   animation-45 (occlusion compositing)
    S4 THE PACK         84 to 116   films/swarm/dogs/s4.py   animation-41 (secondary dynamics)
    S5 ICE, AND ELEVEN 116 to 144   films/swarm/dogs/s5.py   animation-07 (drawn metamorphosis)
    S6 NO, AND AGAIN   144 to 180   films/swarm/dogs/s6.py   animation-48 (state machines)

This file draws nothing of the story. It owns four things:
  * the CLOCK: which sequence a film second belongs to (CUT), and the hand-over at each of the five joins (JOINS);
  * the WORDS: the title and the end credit, lettered by hand stroke by stroke, the only lettering in the film
    (WORDS is counted and asserted: 20 or fewer; the sequence modules are checked for lettering calls);
  * the SOUND: each sequence's own sound() laid at its film second. The music is sound.py's (the radio, the
    town's chimes, the pack's round); every sequence lays its own music_sN on its own picture's clock, so it is
    asserted here that none is laid twice. Nobody on this production has heard any of it;
  * the ENCODE: frames are drawn in parallel, kept as near-lossless pieces, and encoded once, under 12 MB.
    The sound is made 11 dB louder with a peak limiter at the encode (the cut measured -26 LUFS: far too quiet
    for a page); nothing in the mix itself is changed, and nobody has heard the result.

    python3 films/dogs.py                      -> assets/films/dogs.mp4 (+ .webp poster)
    python3 films/dogs.py --stills 3.75 28 ..  -> films/stills/dogs/*.png
    python3 films/dogs.py --sheets             -> 45 stills through the film as contact sheets, and the joins
    python3 films/dogs.py --check              -> the asserts only
"""
from __future__ import annotations

import math
import random
import re
import subprocess
import sys
import tempfile
import wave
from functools import lru_cache
from multiprocessing import get_context
from pathlib import Path

HERE = Path(__file__).resolve().parent
SWARM = HERE / "swarm" / "dogs"
for _p in (str(SWARM), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                   # noqa: E402
from PIL import Image, ImageDraw                     # noqa: E402

import kit                                           # noqa: E402
from kit import FPS, H, W, clamp, ease, lerp         # noqa: E402

import s1, s2, s3, s4, s5, s6                        # noqa: E402,E401

SLUG = "dogs"
SECONDS = 180.0
MAX_BYTES = 12_000_000       # FINAL REPAIR: the thick prompt's hard rule is under 12 MB (the cut was 15.2)

# ====================================================================== #
#  1 · THE CLOCK                                                         #
# ====================================================================== #

SEQS = (s1, s2, s3, s4, s5, s6)
CUT = []                                             # (module, film second it starts, film second it ends)
_t = 0.0
for _m in SEQS:
    CUT.append((_m, _t, _t + _m.SECONDS))
    _t += _m.SECONDS
assert [c[1] for c in CUT] == [0.0, 28.0, 58.0, 84.0, 116.0, 144.0] and _t == SECONDS, "the contract's lengths"
for _m, _a, _b in CUT[1:]:
    assert getattr(_m, "T0", _a) == _a, (_m.__name__, "believes it starts somewhere else")

# The five joins. A sequence's last frame and the next one's first frame are the same moment of the same world
# (the contract), so the default is a straight join: nothing is added and nothing is taken away. Where the two
# builders' frames do not agree, the entry says what the editor does about it and why (see --sheets: the joins
# are laid side by side). kind: "cut" (straight), or "mix" (the outgoing frame is carried across `frames` frames
# of the incoming sequence, dissolving; the incoming sequence keeps its own clock so sound stays on its frames).
JOINS = {
    28.0: ("cut", 0),
    58.0: ("mix", 3),      # same framing and place; the dog's legs and the fish are a drawing apart
    84.0: ("mix", 4),      # S3 leaves the dog a few px lower and the near cow's head down; S4 finds them up
    116.0: ("cut", 0),     # S5 draws its first seconds with S4's own functions: identical
    144.0: ("mix", 6),     # S5 and S6 agree on the framing and the count, not on the old dog's pose or the dog's feet
                           # (about 10 px): a quarter-second mix turns the jump into a settle
}


def seq_at(t):
    for m, a, b in CUT:
        if a <= t < b:
            return m, a
    m, a, b = CUT[-1]
    return m, a


def _seq_frame(m, lt, k):
    """One sequence's frame as an RGB image, before grain (the cut adds grain once, at the end)."""
    ink = kit.Ink(lt, k, (W, H), 8, 1.2, 0)
    ink.paper()
    m.draw(lt, ink)
    ink._grain = False
    return ink.finish()


# S2 lets its vignette go before it ends ("the neighbours have none") but S3 begins with its own already full:
# the corners of the picture would drop in one frame. The cut brings S3's vignette in over half a second.
VIGNETTE_IN = {58.0: 0.5}


def picture(t, ink):
    k = int(round(t * FPS))
    m, a = seq_at(t)
    lt = min(max(0.0, t - a), m.SECONDS - 1.0 / FPS)
    m.draw(lt, ink)
    if a in VIGNETTE_IN and getattr(ink, "_vignette", 0):
        ink._vignette = round(ink._vignette * ease(t, a, a + VIGNETTE_IN[a]), 2)
    kind, n = JOINS.get(a, ("cut", 0))
    if kind == "mix" and n and (t - a) * FPS < n - 0.5:
        prev = CUT[SEQS.index(m) - 1][0]
        out = _seq_frame(prev, prev.SECONDS - 1.0 / FPS, k)          # finished, without grain
        new = ink.img.convert("RGB")
        if getattr(ink, "_vignette", 0):
            new = Image.composite(new, Image.new("RGB", new.size, (0, 0, 0)), kit._vignette_mask(new.size, ink._vignette))
            ink._vignette = 0
        f = ((t - a) * FPS + 1) / (n + 1)
        ink.img = Image.blend(out, new, f * f * (3 - 2 * f))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    words(ink, t)


# ====================================================================== #
#  2 · THE WORDS: fourteen, lettered by hand                              #
# ====================================================================== #
# The board (part E) allows a title of four words and an end credit of ten, and nothing else. The glyphs are
# single strokes, each letter a little off true, written on in the order a hand would write them. Not a font.

def _arc(a0, a1, n=12, cx=0.5, cy=0.5, rx=0.5, ry=0.5):
    return [(cx + rx * math.cos(lerp(a0, a1, i / n)), cy + ry * math.sin(lerp(a0, a1, i / n))) for i in range(n + 1)]


GLYPH = {
    "T": (0.80, [[(0, 0), (1, 0)], [(0.5, 0), (0.5, 1)]]),
    "H": (0.82, [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]]),
    "E": (0.70, [[(1, 0), (0, 0), (0, 1), (1, 1)], [(0, 0.5), (0.8, 0.5)]]),
    "D": (0.82, [[(0, 0), (0, 1)], [(0, 0), (0.45, 0), (0.85, 0.2), (1, 0.5), (0.85, 0.8), (0.45, 1), (0, 1)]]),
    "O": (0.90, [_arc(-1.2, -1.2 + 2 * math.pi + 0.25, 18)]),
    "G": (0.90, [_arc(-0.75, -0.75 - 13 * math.pi / 8, 13) + [(1.0, 0.56), (0.55, 0.56)]]),
    "S": (0.74, [[(0.95, 0.14), (0.7, 0.0), (0.3, 0.0), (0.05, 0.2), (0.25, 0.45), (0.75, 0.55), (0.97, 0.8),
                  (0.7, 1.0), (0.3, 1.0), (0.02, 0.84)]]),
    "F": (0.70, [[(1, 0), (0, 0), (0, 1)], [(0, 0.5), (0.75, 0.5)]]),
    "R": (0.82, [[(0, 1), (0, 0), (0.65, 0), (0.95, 0.22), (0.65, 0.5), (0, 0.5)], [(0.45, 0.5), (1, 1)]]),
    "U": (0.84, [[(0, 0), (0, 0.68), (0.22, 0.97), (0.5, 1.0), (0.78, 0.97), (1, 0.68), (1, 0)]]),
    "W": (1.15, [[(0, 0), (0.24, 1), (0.5, 0.3), (0.76, 1), (1, 0)]]),
    "N": (0.84, [[(0, 1), (0, 0), (1, 1), (1, 0)]]),
    "I": (0.22, [[(0.5, 0), (0.5, 1)]]),
    "C": (0.84, [_arc(-0.7, -2 * math.pi + 0.7, 14)]),
    "L": (0.66, [[(0, 0), (0, 1), (1, 1)]]),
    "A": (0.90, [[(0, 1), (0.5, 0), (1, 1)], [(0.2, 0.62), (0.8, 0.62)]]),
    "V": (0.88, [[(0, 0), (0.5, 1), (1, 0)]]),
    "M": (1.10, [[(0, 1), (0.05, 0), (0.5, 0.75), (0.95, 0), (1, 1)]]),
    ".": (0.20, [[(0.4, 0.93), (0.6, 0.93), (0.6, 1.0), (0.4, 1.0), (0.4, 0.93)]]),
}

TITLE = ("THE DOGS OF", "TROUTTOWN")
CREDIT = ("THE DOG IS CLAUDE.", "IT HAS NEVER HEARD", "THIS FILM.")
WORDS = [w for line in TITLE + CREDIT for w in line.split()]
assert len(WORDS) == 14 and len(WORDS) <= 20, ("words on screen", len(WORDS))

CREAM = (244, 232, 204)
PALE_TEAL = (196, 236, 226)

# where and when (film seconds). Title: in the violet sky at upper right of the live porch shot, written on as
# the herd comes down, gone as the noses meet. Credit: in the water at lower right of the last shot, the
# picture moving under it; gone before the last half second so the film ends on the picture.
TITLE_AT = dict(t0=0.8, write=1.0, t1=3.3, out=0.6, box=(606, 62, 310), sizes=(22, 31), gaps=(6, 7), lead=36,
                color=CREAM, shade=(52, 40, 74))
CREDIT_AT = dict(t0=175.4, write=1.5, t1=179.0, out=0.5, box=(630, 404, 300), sizes=(17, 17, 17), gaps=(4.5, 4.5, 4.5),
                 lead=29, color=PALE_TEAL, shade=(10, 46, 58))


def _letter_line(text, hgt, gap, seed):
    rng = random.Random(seed)
    strokes, x = [], 0.0
    for ch in text:
        if ch == " ":
            x += hgt * 0.55
            continue
        wd, ss = GLYPH[ch]
        dy, rot, sc = rng.uniform(-0.07, 0.07) * hgt, rng.uniform(-0.06, 0.06), rng.uniform(0.94, 1.06)
        if ch == ".":
            dy, rot = 0.0, 0.0
        for s in ss:
            pts = []
            for (u, v) in s:
                px, py = (u - 0.5) * wd * hgt * sc, (v - 0.5) * hgt * sc
                pts.append((x + wd * hgt / 2 + px * math.cos(rot) - py * math.sin(rot),
                            hgt / 2 + dy + px * math.sin(rot) + py * math.cos(rot)))
            strokes.append(pts)
        x += wd * hgt + gap
    return strokes, x - gap


@lru_cache(maxsize=None)
def _strokes(which):
    lines, spec = (TITLE, TITLE_AT) if which == "title" else (CREDIT, CREDIT_AT)
    x0, y0, wd_box = spec["box"]
    out, y = [], y0
    for i, line in enumerate(lines):
        ss, wd = _letter_line(line, spec["sizes"][i], spec["gaps"][i], 4 + 5 * i + (0 if which == "title" else 20))
        assert wd <= wd_box + 1, (line, wd, "does not fit its place")
        off = x0 + ((wd_box - wd) / 2 if which == "title" else 0.0)
        out += [[(px + off, py + y) for px, py in s] for s in ss]
        y += spec["lead"]
    return out


def _partial(s, on):
    if on >= 1:
        return s
    total = sum(math.dist(p, q) for p, q in zip(s, s[1:]))
    need, run, pts = total * on, 0.0, [s[0]]
    for p, q in zip(s, s[1:]):
        d = math.dist(p, q)
        if run + d <= need:
            pts.append(q)
            run += d
        else:
            f = (need - run) / max(d, 1e-6)
            pts.append((lerp(p[0], q[0], f), lerp(p[1], q[1], f)))
            break
    return pts


def _write(ink, t, which):
    spec = TITLE_AT if which == "title" else CREDIT_AT
    t0, t1 = spec["t0"], spec["t1"]
    if t < t0 or t > t1 + spec["out"]:
        return
    strokes = _strokes(which)
    n = len(strokes)
    alpha = 1 - ease(t, t1, t1 + spec["out"])
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    wdt = 3 if max(spec["sizes"]) > 20 else 2
    for pass_, col, a, dx in (("shade", spec["shade"], 150, 1.5), ("ink", spec["color"], 255, 0.0)):
        for k, s in enumerate(strokes):
            on = clamp((t - t0 - spec["write"] * k / n) / 0.16)       # each stroke in its turn
            if on <= 0:
                continue
            pts = [(x + dx, y + dx) for x, y in _partial(s, on)]
            if len(pts) > 1:
                d.line(pts, fill=col + (a,), width=wdt + (2 if pass_ == "shade" else 0), joint="curve")
    if alpha < 1:
        sheet.putalpha(sheet.getchannel("A").point(lambda v: int(v * alpha)))
    ink.img.paste(sheet, (0, 0), sheet)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def words(ink, t):
    _write(ink, t, "title")
    _write(ink, t, "credit")


def lettered(t):
    """True while any lettering is on screen. The film's only lettering is in these two windows."""
    return any(sp["t0"] <= t <= sp["t1"] + sp["out"] for sp in (TITLE_AT, CREDIT_AT))


# ====================================================================== #
#  3 · THE SOUND                                                         #
# ====================================================================== #

def soundtrack(mix):
    """Each sequence's own sound at its film second, in order (order matters: S5 empties the mix under the ice).
    The music is sound.py's, laid by the sequences themselves; see check()."""
    for m, a, _b in CUT:
        m.sound(mix, a)


# ====================================================================== #
#  4 · WHAT IS ASSERTED                                                  #
# ====================================================================== #

_LETTERING = re.compile(r"\.(caption|card|label)\(|ink\.text\(|kit\.font\(|ImageFont")


def check():
    # the clock
    assert sum(m.SECONDS for m in SEQS) == SECONDS
    assert all(abs(m.SECONDS * FPS - round(m.SECONDS * FPS)) < 1e-9 for m in SEQS), "a sequence ends between frames"
    for a, (kind, n) in JOINS.items():
        assert a in [c[1] for c in CUT[1:]] and kind in ("cut", "mix") and 0 <= n <= 12
    # the words: 14 lettered here, none anywhere else
    assert len(WORDS) <= 20
    assert s1.TITLE_ON is False, "S1 must not letter the title as well"
    for m in SEQS:
        src = Path(m.__file__).read_text()
        body = src[src.index("\ndef draw("):]
        body = body[:body.index("\ndef ", 5)] if "\ndef " in body[5:] else body
        assert not _LETTERING.search(body), (m.__name__, "letters something in draw()")
    assert not lettered(0.5) and lettered(2.0) and not lettered(4.2) and lettered(177.0) and not lettered(179.7)
    # the music: sound.py's, once. s1, s3, s4, s6 call their music_sN; s2 and s5 lay its calls on their own clocks.
    for m, n, own in ((s1, 1, True), (s2, 2, False), (s3, 3, True), (s4, 4, True), (s5, 5, False), (s6, 6, True)):
        src = Path(m.__file__).read_text()
        calls = len(re.findall(r"^\s+\w+\.music_s%d\(" % n, src, re.M))
        assert calls == (1 if own else 0), (m.__name__, "music laid %d times" % calls)
    assert "music(" not in Path(__file__).read_text().split("def soundtrack")[1].split("def check")[0].replace(
        "music_sN", ""), "the editor must not lay the music a second time"
    return True


# ====================================================================== #
#  5 · STILLS, CONTACT SHEETS, RENDER                                    #
# ====================================================================== #

film = kit.Film(SLUG, SECONDS)
film.poster_at = 3.75
film.picture(picture)
film.sound(soundtrack)

STILLS_45 = [2.0 + 4.0 * i for i in range(45)]       # every four seconds, off the joins
SCRATCH = Path(tempfile.gettempdir()) / "dogs-cut"      # set TMPDIR to keep the pieces somewhere else


def _frame_job(k):
    return k, film.frame(k)


def _frames(ks, procs=4):
    with get_context("fork").Pool(procs) as pool:
        return dict(pool.imap_unordered(_frame_job, ks, chunksize=1))


def _sheet(imgs, cols, path, scale=0.5, labels=None):
    """A contact sheet. The time stamps are on the sheet only, never in the film."""
    cw, ch = int(W * scale), int(H * scale)
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(imgs):
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.paste(im.resize((cw, ch), Image.LANCZOS), (x, y))
        if labels:
            d.rectangle([x, y, x + 54, y + 12], fill=(0, 0, 0))
            d.text((x + 3, y + 1), labels[i], fill=(255, 255, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


def sheets(which=None):
    out = HERE / "stills" / SLUG
    f1 = 1.0 / FPS
    sets = {"a": STILLS_45[0:15], "b": STILLS_45[15:30], "c": STILLS_45[30:45]}
    for name, ts in sets.items():
        if which and name not in which:
            continue
        got = _frames([int(round(t * FPS)) for t in ts])
        imgs = [got[int(round(t * FPS))] for t in ts]
        print(_sheet(imgs, 5, out / f"sheet_{name}.png", 0.4, ["%.1f" % t for t in ts]))
    if not which or "j" in which:
        for a in [c[1] for c in CUT[1:]]:
            ts = [a - 1.0, a - 0.5, a - f1, a, a + f1, a + 2 * f1, a + 0.5, a + 1.0]
            got = _frames([int(round(t * FPS)) for t in ts])
            imgs = [got[int(round(t * FPS))] for t in ts]
            diff = np.abs(np.asarray(imgs[2], np.int16) - np.asarray(imgs[3], np.int16)).mean()
            before = np.abs(np.asarray(_one(a - 2 * f1), np.int16) - np.asarray(imgs[2], np.int16)).mean()
            print("join %5.1f  mean |last - first| = %.2f  (the frame before it: %.2f)" % (a, diff, before))
            print(_sheet(imgs, 4, out / f"join_{int(a):03d}.png", 0.5, ["%.2f" % t for t in ts]))


def _one(t):
    return film.frame(int(round(t * FPS)))


def _piece(job):
    """Draw frames a..b and keep them as a near-lossless piece (so the final encode can be tried more than once)."""
    idx, a, b = job
    path = SCRATCH / f"piece_{idx:03d}.mkv"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "6", "-pix_fmt", "yuv444p",
           str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(a, b):
        img = film.frame(k)
        if k == int(film.poster_at * FPS):
            img.save(kit.OUT / f"{SLUG}.webp", quality=82)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed on piece %d" % idx)
    return idx, a, b


def render(procs=4, piece_frames=96, reuse=False):
    check()
    kit.OUT.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    total = int(round(SECONDS * FPS))
    jobs = [(i, a, min(total, a + piece_frames)) for i, a in enumerate(range(0, total, piece_frames))]
    todo = [j for j in jobs if not (reuse and (SCRATCH / f"piece_{j[0]:03d}.mkv").exists())]
    done = 0
    with get_context("fork").Pool(procs) as pool:
        for idx, a, b in pool.imap_unordered(_piece, todo, chunksize=1):
            done += 1
            print(f"  {SLUG}: piece {idx:02d} ({a / FPS:5.1f}s to {b / FPS:5.1f}s)  {done}/{len(todo)}", flush=True)
    # sound
    wav = SCRATCH / "a.wav"
    mix = kit.Mix(SECONDS, seed=0)
    soundtrack(mix)
    pcm = mix.master()
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(kit.RATE)
        wf.writeframes(pcm.tobytes())
    encode()


LOUDER = "volume=11dB,alimiter=limit=0.7:attack=4:release=90:level=disabled"


def encode():
    """One encode of the kept pieces with the kit's settings; the quality is lowered only if the file is too big."""
    total = int(round(SECONDS * FPS))
    lst = SCRATCH / "pieces.txt"
    pieces = sorted(SCRATCH.glob("piece_*.mkv"))
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    mp4 = kit.OUT / f"{SLUG}.mp4"
    for crf in (28, 29, 30, 31, 32, 33, 34):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-r", str(FPS), "-i", str(lst),
               "-i", str(SCRATCH / "a.wav"),
               "-c:v", "libx264", "-preset", "veryslow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-tune", "animation",
               "-r", str(FPS), "-af", LOUDER, "-ar", str(kit.RATE), "-c:a", "aac", "-b:a", "96k", "-shortest",
               "-movflags", "+faststart", str(mp4)]
        if subprocess.run(cmd).returncode != 0:
            raise SystemExit("ffmpeg failed")
        size = mp4.stat().st_size
        print(f"wrote {mp4.relative_to(kit.PROJECT)} at crf {crf} ({size / 1e6:.2f} MB)")
        if size < MAX_BYTES:
            break
    else:
        raise SystemExit("could not get under %d bytes" % MAX_BYTES)
    n = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    assert int(n) == total, ("frames in the file", n, "expected", total)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        print("check:", check())
    elif args and args[0] == "--sheets":
        sheets(args[1:])
    elif args and args[0] == "--stills":
        ts = [float(x) for x in args[1:]] or STILLS_45
        out = HERE / "stills" / SLUG
        out.mkdir(parents=True, exist_ok=True)
        got = _frames([int(round(t * FPS)) for t in ts])
        for t in ts:
            got[int(round(t * FPS))].save(out / f"{t:06.2f}.png")
        print("stills ->", out)
    elif args and args[0] == "--encode":
        encode()
    else:
        render(reuse="--reuse" in args)


if __name__ == "__main__":
    main()
