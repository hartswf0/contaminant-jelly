#!/usr/bin/env python3
"""intro: the activity in six shots, one per core SCION prompt, with captions.

Cuts films/intro-1..6.mp4 (made from prompts/intro-*.txt) into films/intro.mp4. No fal call.
"""
import os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
# (source, start, length, step, caption)
SHOTS = [
    ("films/intro-6.mp4", 2.6, 5.4, 1, "TOURKEY TROUTTOWN", "Turkey takes a tour of Trout Town. 55 portholes, one window at a time."),
    ("films/intro-1.mp4", 0.0, 5.0, 1, "1  Take Turkey's seat", "One window. Ballast slot left, chalk chart centre, lamp toggle right."),
    ("films/intro-2.mp4", 1.0, 6.0, 1, "2  Operate one part", "One slot: fit the lamp or the ballast, and watch what changes in the port."),
    ("films/intro-3.mp4", 2.0, 6.0, 1, "3  Read both sides of the glass", "Turkey looks out: odd faces 1, 3, 5. Trout look in: even faces 2, 4, 6."),
    ("films/intro-4.mp4", 2.6, 5.4, 1, "4  Roll once", "Probable, Plausible or Preposterous. One die decides, and one light comes on."),
    ("films/intro-5.mp4", 2.0, 6.0, 1, "5  Pass the record", "Mark the chart under glass and hand the postcard to the next pilot."),
]
parts, ins = [], []
for i, (src, ss, t, slow, step, cap) in enumerate(SHOTS):
    ins += ["-ss", str(ss), "-t", str(t), "-i", src]
    esc = lambda s: s.replace("'", "’").replace(":", "\\:").replace(",", "\\,")
    parts.append(
        "[%d:v]setpts=%s*PTS,fps=24,scale=1280:720,setsar=1,drawbox=y=ih-150:h=150:color=0x10201f@0.82:t=fill,"
        "drawtext=fontfile=%s:text='%s':x=48:y=h-128:fontsize=40:fontcolor=0xf0b25a,"
        "drawtext=fontfile=%s:text='%s':x=48:y=h-66:fontsize=27:fontcolor=0xe9e4d4[v%d];"
        "[%d:a]aresample=44100,volume=%s,apad,atrim=0:%s,afade=t=in:d=0.15,afade=t=out:st=%s:d=0.2[a%d]"
        % (i, slow, FONT, esc(step), FONT.replace("-Bold", ""), esc(cap), i, i, 1 if slow == 1 else 0, t * slow, t * slow - 0.2, i))
n = len(SHOTS)
fc = ";".join(parts) + ";" + "".join("[v%d][a%d]" % (i, i) for i in range(n)) + "concat=n=%d:v=1:a=1[v][a]" % n
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart", "films/intro.mp4"], check=True)
print("films/intro.mp4")
