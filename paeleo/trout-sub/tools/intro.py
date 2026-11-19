#!/usr/bin/env python3
"""intro: the four steps of the activity, cut from footage already made, with captions.

Uses the raw films in films/ (no fal call). The six SCION intro shots in
prompts/intro-*.txt are written but unrun; when they exist they replace this.
"""
import os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
# (source, start, length, step, caption)
SHOTS = [
    ("films/p03.mp4", 0.0, 3.2, 1, "1  Take Turkey's seat", "One window. Ballast slot left, chalk chart centre, lamp toggle right."),
    ("films/p14.mp4", 0.0, 5.0, 1, "2  Operate one part", "Flip the lamp or fit the ballast, and watch what changes in the port."),
    ("films/p08.mp4", 4.0, 2.6, 1.5, "3  Turkey looks out", "Odd faces 1, 3, 5. What does Turkey suspect?"),
    ("films/p08.mp4", 6.75, 1.25, 3, "3  Trout looks in", "Even faces 2, 4, 6. What do the trout suspect?"),
    ("films/p22.mp4", 6.75, 1.25, 3.5, "4  Roll once, pass it on", "Circle the roll, mark the chart under glass, hand the clue to the next pilot."),
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
