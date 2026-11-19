#!/usr/bin/env python3
"""mixes: one video for each of the first ten songs of DEEP SEA VOYAGE.

    python3 tools/mixes.py            # youtube/mixes/mix-01-....mp4 through mix-10-....mp4
    python3 tools/mixes.py 3 8        # only these tracks
    python3 tools/mixes.py 3 --test   # first three portholes only, to check quickly

Each mix runs the whole song. A title card, then portholes one after another for as long as the
song lasts, each change and each lit choice landing on the song's own tracked beats. The deck
carries on from mix to mix, so across the ten every porthole comes round more than twice.
Same porthole screen as the main film: slip number, minimap, controller buttons, dice on the bolts.
"""
import json, os, sys
import youtube as Y
import cards as C

TRACKS = [("music/yellow-submarine-brass-foley-singalong.ogg", "Yellow Submarine: Abbey Road Brass-Foley Singalong"),
          ("music/nobody-living-can-ever-stop-me.ogg", "Nobody Living Can Ever Stop Me"),
          ("music/the-prophet.ogg", "The Prophet"),
          ("music/motor-run-on-the-water.ogg", "水上のモーター走行 (Motor Run on the Water)"),
          ("music/whales-belly-escape.ogg", "Whale's Belly Escape"),
          ("music/warning-unheeded.ogg", "Warning Unheeded"),
          ("music/exodus-song.ogg", "Exodus Song: Viennese Epic to Satire"),
          ("music/the-verne-bench.ogg", "The Verne Bench"),
          ("music/gaslit-feerie.ogg", "Gaslit Feerie Pit-Piano and Star-Film Salon"),
          ("music/whale-belly-breach.ogg", "Whale Belly Breach")]
FPS = Y.FPS


def plan():
    """For every track: beats, beats per porthole (about 13.5 s, a whole number of bars), how many
    portholes fit, and which porthole it starts on."""
    out, pid = [], 1
    for path, title in TRACKS:
        bt, rms, sr, dur = Y.beats(path)
        period = float((bt[-1] - bt[0]) / (len(bt) - 1))
        step = max(8, int(round(13.5 / period / 4.0)) * 4)
        lead = 8
        count = max(1, (len(bt) - 1 - lead) // step)
        out.append(dict(path=path, title=title, bt=bt, dur=dur, step=step, lead=lead, count=count, first=pid))
        pid = (pid - 1 + count) % 55 + 1
    return out


def render(k, p, limit=None):
    slug = os.path.splitext(os.path.basename(p["path"]))[0]
    dest = "youtube/mixes/mix-%02d-%s.mp4" % (k, slug)
    out, times = Y.Out(), {}
    Y.V.prefetch(Y.all_lines())
    bt = p["bt"]; T = lambda b: float(bt[min(b, len(bt) - 1)] - bt[0])
    count = min(p["count"], limit) if limit else p["count"]
    last = (p["first"] - 1 + count - 1) % 55 + 1
    for card in C.mix_card(k, p["title"], p["first"], last, int(round(T(p["lead"]) * FPS))):
        out.add(card)
    prev, pid = None, p["first"]
    for j in range(count):
        start_n = out.n
        F = lambda bb: int(round(T(p["lead"] + p["step"] * j + bb) * FPS)) - start_n
        ch = Y.choices(pid)
        marks, half_n = Y.light_marks(F, 0, p["step"], sum(1 for c in ch if c[2] == "turkey"), sum(1 for c in ch if c[2] == "trout"))
        prev = Y.play_porthole(out, pid, F(p["step"]), half_n, marks, prev, times, first=(prev is None))
        pid = pid % 55 + 1
    tail = min(p["dur"] - float(bt[0]) - out.t, 2.5)                 # let the song ring out on the last frame
    for _ in range(max(0, int(tail * FPS))):
        out.add(prev)
    out.song(p["path"], float(bt[0]), 0.0, out.t, fade=2.0)
    Y.MAX_MB = max(8, min(60, int(out.t * 1250 / 8192) + 1))         # about 1.1 Mbit/s of picture
    kbps = out.close(dest)
    print("%s  %s  portholes %02d to %02d (%d)  %d beats each  %d kbps" % (dest, Y.stamp(out.t), p["first"], last, count, p["step"], kbps), flush=True)
    return dict(file=dest, title=p["title"], length=Y.stamp(out.t), first=p["first"], last=last, portholes=count, beats_per_porthole=p["step"])


if __name__ == "__main__":
    os.makedirs("youtube/mixes", exist_ok=True)
    test = "--test" in sys.argv
    which = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(1, 11))
    plans = plan()
    done = [render(k, plans[k - 1], 3 if test else None) for k in which]
    if not test:
        old = json.load(open("youtube/mixes.json")) if os.path.exists("youtube/mixes.json") else []
        done = sorted([d for d in old if d["file"] not in [x["file"] for x in done]] + done, key=lambda d: d["file"])
        json.dump(done, open("youtube/mixes.json", "w"), indent=1, ensure_ascii=False)
