#!/usr/bin/env python3
"""units: one standard unit per porthole, so the deck plays as one seamless chain.

    python3 tools/units.py            # build every missing unit
    python3 tools/units.py p07 p49    # rebuild these

A unit is exactly 8.000 s, 960x540, 24 fps, with sound. It opens with a
0.4 s iris out of the river colour and closes with a 0.4 s iris back into it,
so any unit loops on itself and joins any other unit in any order.

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


def unit(pid):
    src = "films/%s.mp4" % pid
    kind = "film"
    if not os.path.exists(src):
        src = os.path.join(tempfile.mkdtemp(), pid + ".mp4")
        keyframe_source(pid, src)
        kind = "keyframe"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True, check=True).stdout)
    k = LEN / dur
    tempo = min(max(1 / k, 0.5), 2.0)
    fc = (
        "[0:v]setpts=%f*PTS,fps=24,scale=960:540:flags=lanczos,setsar=1,trim=0:%f,tpad=stop_mode=clone:stop_duration=1,trim=0:%f,setpts=PTS-STARTPTS[v];"
        "color=c=%s:s=960x540:r=24:d=%f,setsar=1[c0];color=c=%s:s=960x540:r=24:d=1,setsar=1[c1];"
        "[c0][v]xfade=transition=circleopen:duration=%f:offset=0[v1];"
        "[v1][c1]xfade=transition=circleclose:duration=%f:offset=%f,trim=0:%f,format=yuv420p[vo];"
        "[0:a]atempo=%f,apad,atrim=0:%f,afade=t=in:d=0.3,afade=t=out:st=%f:d=0.4[ao]"
        % (k, LEN, LEN, RIVER, IRIS, RIVER, IRIS, IRIS, LEN - IRIS, LEN, tempo, LEN, LEN - 0.4)
    )
    os.makedirs("units", exist_ok=True)
    run("-i", src, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]", "-t", str(LEN),
        "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-g", "24", "-c:a", "aac", "-b:a", "80k",
        "-movflags", "+faststart", "units/%s.mp4" % pid)
    print(pid, kind, "%.2fs -> %.1fs" % (dur, LEN))
    return kind


if __name__ == "__main__":
    ids = sys.argv[1:] or ["p%02d" % n for n in range(1, 56) if not os.path.exists("units/p%02d.mp4" % n)]
    kinds = {i: unit(i) for i in ids}
    print("%d units; keyframe: %s" % (len(kinds), [i for i, k in kinds.items() if k == "keyframe"]))
