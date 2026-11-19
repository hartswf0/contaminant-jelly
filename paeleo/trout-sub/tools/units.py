#!/usr/bin/env python3
"""units: one standard unit per porthole, so the deck plays as one seamless chain.

    python3 tools/units.py            # build every missing unit
    python3 tools/units.py p07 p49    # rebuild these

A unit is exactly 8.000 s, 960x540, 24 fps, with sound. Its first and last
frames show the brass porthole at the same centre and size (found per film by
tools/porttrack.py), so the outside shot that ends any unit registers rim on
rim with the inside shot that opens any other: a unit loops on itself and joins
any unit in any order. The first frame carries the deck drawing in the glass.

Source is films/<id>.mp4 (time-fitted to 8 s). Where no film exists, a
keyframe unit is built in code from masters/cockpit.jpg, the deck still and
masters/outside.jpg: lamp on, push in to the port, cut across the glass.
No fal call is made here.
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
RIVER = "0x10201f"
PORT = (672, 335, 166)      # centre x, centre y, outer rim radius in masters/cockpit.jpg (1344x768)
STILL_RIM = 300             # outer rim radius in a 640x640 deck still
LEN, IRIS = 8.0, 0.4


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + list(a), check=True)


def keyframe_source(pid, out):
    """8 s film from stills only."""
    cx, cy, r = PORT
    room = Image.open("masters/cockpit.jpg").convert("RGB")
    d = int(640 * r / STILL_RIM)
    still = Image.open("stills/%s.jpg" % pid).convert("RGB").resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse((d // 2 - r + 5, d // 2 - r + 5, d // 2 + r - 5, d // 2 + r - 5), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    tmp = tempfile.mkdtemp()
    for name, bright in (("dim", 0.45), ("lit", 1.0)):
        im = room.copy()
        s = ImageEnhance.Brightness(still).enhance(bright)
        if name == "dim":
            s = s.filter(ImageFilter.GaussianBlur(3))
        im.paste(s, (cx - d // 2, cy - d // 2), mask)
        im.resize((2688, 1536), Image.LANCZOS).save("%s/%s.png" % (tmp, name))
    zx, zy = cx / 1344.0, cy / 768.0
    fc = (
        "[0]scale=1344:768,setsar=1[a0];[1]scale=1344:768,setsar=1[a1];"
        "[a0][a1]xfade=transition=fade:duration=0.6:offset=1.2,trim=0:2.5,setpts=PTS-STARTPTS[s1];"
        "[2]zoompan=z='1+2.3*pow(on/72,1.6)':x='iw*%f-iw/zoom*%f':y='ih*%f-ih/zoom*%f':d=72:s=1344x768:fps=24,setsar=1[s2];"
        "[3]scale=2688:-2,zoompan=z='1+0.08*on/60':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=60:s=1344x768:fps=24,setsar=1[s3];"
        "[s1][s2][s3]concat=n=3:v=1:a=0,format=yuv420p[v]" % (zx, zx, zy, zy)
    )
    run("-loop", "1", "-framerate", "24", "-t", "2.5", "-i", tmp + "/dim.png",
        "-loop", "1", "-framerate", "24", "-t", "2.5", "-i", tmp + "/lit.png",
        "-i", tmp + "/lit.png", "-i", "masters/outside.jpg",
        "-f", "lavfi", "-t", "8", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", fc, "-map", "[v]", "-map", "4:a", "-t", "8",
        "-c:v", "libx264", "-crf", "18", "-c:a", "aac", out)


CANON_R = 0.215        # outer rim radius every unit opens and closes on, as a fraction of frame width
GLASS = 0.77           # glass radius / outer rim radius
STILL_GLASS = 0.715    # glass radius / outer rim radius in the deck stills
OPEN, CLOSE, HOLD = 1.3, 0.9, 0.25   # seconds: pull-back from the lock, push into the lock, held lock at the tail
MIN_SCORE, MAX_DRIFT = 0.33, 0.05


def good(p):
    return bool(p) and p["score"] >= MIN_SCORE and p["drift"] <= MAX_DRIFT


def reachable(p):
    """Can a zoom of at least 1 put this port at frame centre at CANON_R without showing an edge?"""
    if not good(p) or p["r"] > CANON_R:
        return False
    slack = 0.5 * (1 - p["r"] / CANON_R)
    return abs(p["cx"] - 0.5) <= slack and abs(p["cy"] * 16 / 9 - 0.5) <= slack


MASTER_IN = (670, 356, 195)     # port in masters/cockpit.jpg: centre x, centre y, outer rim radius (1344x768)
MASTER_OUT = (675, 387, 268)    # port in masters/outside.jpg


def still_disc(pid, diameter, out):
    """The deck drawing's glass, cut to a soft-edged disc of the given pixel diameter."""
    im = Image.open("stills/%s.jpg" % pid).convert("RGB")
    r = int(STILL_RIM * STILL_GLASS)
    im = im.crop((320 - r, 320 - r, 320 + r, 320 + r)).resize((diameter, diameter), Image.LANCZOS)
    mask = Image.new("L", (diameter * 2, diameter * 2), 0)
    ImageDraw.Draw(mask).ellipse((6, 6, diameter * 2 - 6, diameter * 2 - 6), fill=255)
    im.putalpha(mask.resize((diameter, diameter), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2)))
    im.save(out)


def unit(pid):
    """Time-fit to 8 s, then lock the porthole: the first and last frames show the brass
    rim at the same centre and size (frame centre, CANON_R), so the outside shot that
    ends one unit and the inside shot that opens the next register rim on rim. The
    opening frame also carries the deck drawing in the glass, dissolving into the film."""
    import json
    src = "films/%s.mp4" % pid
    kind = "film"
    if not os.path.exists(src):
        os.makedirs(".raw", exist_ok=True)
        src = ".raw/kf_%s.mp4" % pid
        keyframe_source(pid, src)
        kind = "keyframe"
    ports = json.load(open("ports.json")) if os.path.exists("ports.json") else {}
    if kind == "keyframe":      # built from the masters, so the port is where the masters have it
        ports[pid] = {"duration": LEN, "start": dict(zip(("cx", "cy", "r"), [v / 1344.0 for v in MASTER_IN]), score=1, drift=0),
                      "end": dict(zip(("cx", "cy", "r"), [v / 1344.0 for v in MASTER_OUT]), score=1, drift=0)}
    elif pid not in ports:
        import porttrack
        ports[pid] = porttrack.track(pid, src)
    json.dump(dict(sorted(ports.items())), open("ports.json", "w"), indent=1)
    P = ports[pid]
    dur = P["duration"]
    k = LEN / dur
    tempo = min(max(1 / k, 0.5), 2.0)
    WW, HH = 1920, 1080                       # work size; zoompan is steadier on a large frame
    st, en = P.get("start"), P.get("end")
    lock_s, lock_e = good(st), reachable(en)
    s0 = max(1.0, CANON_R / st["r"]) if lock_s else 1.0
    s1 = max(1.0, CANON_R / en["r"]) if lock_e else 1.0
    sx, sy = (st["cx"], st["cy"] * 16 / 9) if lock_s else (0.5, 0.5)     # as fractions of width, height
    ex, ey = (en["cx"], en["cy"] * 16 / 9) if lock_e else (0.5, 0.5)
    te = LEN - HOLD - CLOSE
    n = "(in/24)"
    ease = lambda u: "(0.5-0.5*cos(PI*clip(%s,0,1)))" % u
    z = "(1+%f*(1-%s)+%f*%s)" % (s0 - 1, ease("%s/%f" % (n, OPEN)), s1 - 1, ease("(%s-%f)/%f" % (n, te, CLOSE)))
    fx = "if(lt(%s,%f),%f,%f)" % (n, LEN / 2, sx, ex)
    fy = "if(lt(%s,%f),%f,%f)" % (n, LEN / 2, sy, ey)
    zp = "zoompan=z='%s':x='clip(iw*%s-iw/zoom/2,0,iw-iw/zoom)':y='clip(ih*%s-ih/zoom/2,0,ih-ih/zoom)':d=1:s=960x540:fps=24" % (z, fx, fy)
    inputs = ["-i", src]
    pre = "[0:v]setpts=%f*PTS,fps=24,scale=%d:%d:flags=lanczos,setsar=1,trim=0:%f,tpad=stop_mode=clone:stop_duration=1,trim=0:%f,setpts=PTS-STARTPTS[b];" % (k, WW, HH, LEN, LEN)
    if lock_s and kind == "film":
        d = int(round(2 * st["r"] * GLASS * WW)) // 2 * 2
        disc = os.path.join(tempfile.mkdtemp(), "disc.png")
        still_disc(pid, d, disc)
        inputs += ["-loop", "1", "-framerate", "24", "-t", "1.4", "-i", disc]
        pre += ("[1:v]format=rgba,fade=t=out:st=0.45:d=0.8:alpha=1[d];"
                "[b][d]overlay=x=%d:y=%d:eof_action=pass[b2];" % (round(st["cx"] * WW - d / 2), round(st["cy"] * WW - d / 2)))
    else:
        pre += "[b]null[b2];"
    if lock_e:
        tail = "[b2]%s,setsar=1,format=yuv420p[vo];" % zp
    else:
        # The film's last shot has no port that can be brought to the lock (hidden, off centre
        # or too large), so the unit returns to the outside master, already at the lock.
        cx, cy, r = MASTER_OUT
        cw = 1344 * (r / 1344.0) / CANON_R
        inputs += ["-loop", "1", "-framerate", "24", "-t", "0.9", "-i", "masters/outside.jpg"]
        tail = ("[b2]%s,setsar=1[zv];[%d:v]crop=%d:%d:%d:%d,scale=960:540:flags=lanczos,setsar=1,fps=24[m];"
                "[zv][m]xfade=transition=fade:duration=0.6:offset=%f,format=yuv420p[vo];"
                % (zp, len(inputs) // 2 - (2 if "-loop" in inputs[:4] else 0) if False else (2 if lock_s and kind == "film" else 1),
                   int(cw), int(cw * 9 / 16), int(cx - cw / 2), int(cy - cw * 9 / 32), LEN - 0.9))
    fc = (pre + tail +
          "[0:a]atempo=%f,apad,atrim=0:%f,afade=t=in:d=0.15,afade=t=out:st=%f:d=0.15[ao]" % (tempo, LEN, LEN - 0.15))
    os.makedirs("units", exist_ok=True)
    run(*inputs, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", "-t", str(LEN),
        "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-g", "24", "-c:a", "aac", "-b:a", "80k",
        "-movflags", "+faststart", "units/%s.mp4" % pid)
    print(pid, kind, "lock start %s x%.2f, end %s x%.2f" % (lock_s, s0, lock_e, s1))
    return {"kind": kind, "lock_start": lock_s, "lock_end": lock_e}


if __name__ == "__main__":
    import json
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    ids = sys.argv[1:] or ["p%02d" % n for n in range(1, 56)]
    state = json.load(open("units.json")) if os.path.exists("units.json") else {}
    for i in ids:
        state[i] = unit(i)
    json.dump(dict(sorted(state.items())), open("units.json", "w"), indent=1)
    print("%d units; keyframe: %s; end not locked: %s" % (len(ids), [i for i in ids if state[i]["kind"] == "keyframe"],
                                                           [i for i in ids if not state[i]["lock_end"]]))
