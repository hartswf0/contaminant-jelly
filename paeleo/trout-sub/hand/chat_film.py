#!/usr/bin/env python3
"""chat_film: this chat, as it appears, played fast. For teaching fourth graders how Claude works.

    python3 chat_film.py     # assets/behind-the-chat.mp4

Every bubble is a real message from this conversation, in order, in the words as typed (typos kept).
Every chip is a real tool call with the description it carried. Nothing is reworded or reordered.
Three things are left out or cut: Claude's private reasoning is not shown at all; a long message is cut
short after its first lines; e-mail addresses are covered. Source: chat_events.json, read from the session
transcript (visible messages and tool calls only).
"""
import json, math, re, subprocess
from datetime import datetime
from PIL import Image, ImageDraw
import class_cut as C
from class_cut import W, H, F, PAPER, INK, MUTE, RUST, TEAL, GOLD, PENCIL, ease, segment, tone
from scion_explainer import SERIF

EV = json.load(open("chat_events.json"))
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
CHAT_W = 610; X0 = 24
TOOL_NAME = {"Bash": "run a command", "Read": "look at a file", "SendUserFile": "send a file", "Write": "write a file", "Workflow": "start a swarm of agents", "TaskStop": "stop a task",
             "WebSearch": "search the web", "WebFetch": "open a web page", "ToolSearch": "find a tool", "Skill": "use a skill"}
TOOL_COL = {"Bash": (60, 110, 150), "Read": (110, 120, 60), "SendUserFile": (150, 80, 140), "Write": (190, 120, 30), "Workflow": (196, 78, 52)}
AGENTS = 109                                             # agent transcripts saved under subagents/workflows when this was made


def wrap(d, text, font, width, max_lines):
    words = text.replace("\n", " ").split(); lines = []; cur = ""
    for w in words:
        if d.textlength((cur + " " + w).strip(), font=font) <= width: cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
            if len(lines) == max_lines: break
    if len(lines) < max_lines and cur: lines.append(cur)
    cut = len(" ".join(lines)) < len(" ".join(words)) - 1
    if cut and lines: lines[-1] = lines[-1][:max(0, len(lines[-1]) - 2)] + " …"
    return lines


_d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
ITEMS = []; y = 0.0; clock = 0.0
for e in EV:
    text = EMAIL.sub("[e-mail]", e["text"])
    if e["who"] == "user":
        lines = wrap(_d, text, F(17, "SemiBold"), CHAT_W - 150, 4); h = 30 + 24 * len(lines) + 16; dur = 1.5
    elif e["who"] == "claude":
        lines = wrap(_d, re.sub(r"[*#`|]", "", text), SERIF(17), CHAT_W - 150, 3); h = 30 + 22 * len(lines) + 14; dur = 0.55
    else:
        name = e["name"].split("__")[-1]
        if "/" in text and " " not in text: text = text.rstrip("/").split("/")[-1]
        lines = wrap(_d, text or TOOL_NAME.get(name, name), F(12, "SemiBold"), CHAT_W - 250, 1); h = 28; dur = 0.055
        e = dict(e, name=name)
    ITEMS.append(dict(e, lines=lines, y=y, h=h, at=clock, dur=dur)); y += h + 6; clock += dur
TOTAL = clock; T_START = datetime.fromisoformat(EV[0]["t"].replace("Z", "+00:00"))
INTRO, OUTRO = 9.0, 12.0


def draw_item(d, it, top):
    if it["who"] == "user":
        x1 = X0 + CHAT_W; x0 = x1 - (CHAT_W - 110)
        d.rounded_rectangle((x0, top, x1, top + it["h"]), 14, fill=(214, 232, 240)); d.text((x0 + 14, top + 8), "COOL RADIO", font=F(12), fill=(40, 90, 120))
        for j, ln in enumerate(it["lines"]): d.text((x0 + 14, top + 28 + j * 24), ln, font=F(17, "SemiBold"), fill=INK)
    elif it["who"] == "claude":
        x0 = X0; x1 = X0 + CHAT_W - 110
        d.rounded_rectangle((x0, top, x1, top + it["h"]), 14, fill=(255, 253, 246), outline=(214, 206, 188)); d.text((x0 + 14, top + 8), "CLAUDE", font=F(12), fill=RUST)
        for j, ln in enumerate(it["lines"]): d.text((x0 + 14, top + 28 + j * 22), ln, font=SERIF(17), fill=INK)
    else:
        col = TOOL_COL.get(it["name"], (110, 110, 110)); x0 = X0 + 26
        d.rounded_rectangle((x0, top, x0 + CHAT_W - 150, top + 26), 13, outline=col, width=2)
        d.rounded_rectangle((x0, top, x0 + 150, top + 26), 13, fill=col); d.text((x0 + 10, top + 6), TOOL_NAME.get(it["name"], it["name"])[:22], font=F(12), fill=PAPER)
        if it["lines"]: d.text((x0 + 160, top + 6), it["lines"][0], font=F(12, "SemiBold"), fill=MUTE)


def frame(t):
    im = Image.new("RGB", (W, H), (244, 240, 230)); d = ImageDraw.Draw(im)
    c = min(TOTAL - 1e-3, max(0.0, t)); i = 0
    while i < len(ITEMS) - 1 and ITEMS[i + 1]["at"] <= c: i += 1
    it = ITEMS[i]; u = min(1.0, (c - it["at"]) / it["dur"]); bottom = it["y"] + it["h"] * (0.35 + 0.65 * u)
    scroll = bottom - (H - 30)
    for k in range(max(0, i - 40), i + 1):
        top = ITEMS[k]["y"] - scroll
        if top + ITEMS[k]["h"] < 0: continue
        draw_item(d, ITEMS[k], top)
    # the side panel: where we are, and what has happened so far
    d.rectangle((660, 0, W, H), fill=(28, 35, 38)); now = datetime.fromisoformat(it["t"].replace("Z", "+00:00")); hrs = (now - T_START).total_seconds() / 3600
    d.text((680, 18), "A REAL CHAT, PLAYED FAST", font=F(15), fill=PENCIL); d.text((680, 44), "hour %d" % int(hrs), font=F(44), fill=PAPER); d.text((680, 96), "of %d" % int((datetime.fromisoformat(EV[-1]["t"].replace("Z", "+00:00")) - T_START).total_seconds() / 3600 + 1), font=F(17, "SemiBold"), fill=(170, 180, 180))
    seen = ITEMS[:i + 1]; n_user = sum(1 for s in seen if s["who"] == "user"); n_cl = sum(1 for s in seen if s["who"] == "claude")
    rows = [("questions from Cool Radio", n_user, (120, 180, 210)), ("answers from Claude", n_cl, (236, 196, 150))]
    for name in ("Bash", "Read", "SendUserFile", "Write", "Workflow"):
        rows.append((TOOL_NAME[name], sum(1 for s in seen if s["who"] == "tool" and s["name"] == name), TOOL_COL[name]))
    rows.append(("other tools", sum(1 for s in seen if s["who"] == "tool" and s["name"] not in TOOL_COL), (130, 130, 130)))
    for j, (label, n, col) in enumerate(rows):
        yy = 140 + j * 46; d.text((680, yy), label, font=F(13, "SemiBold"), fill=(200, 206, 204)); d.text((W - 20 - d.textlength(str(n), font=F(22)), yy - 6), str(n), font=F(22), fill=PAPER)
        full = {0: 67, 1: 156, 2: 374, 3: 131, 4: 53, 5: 12, 6: 11, 7: 24}[j]; d.rectangle((680, yy + 20, 680 + 260 * min(1, n / full), yy + 28), fill=col)
    return im


def s_intro(t):
    im = Image.new("RGB", (W, H), (28, 35, 38)); d = ImageDraw.Draw(im)
    d.text((60, 70), "BEHIND THE CHAT", font=F(72), fill=PAPER)
    if t > 1.6: d.text((64, 170), "A real conversation between a person and Claude.", font=F(28), fill=PENCIL)
    for j, (at, ln) in enumerate(((3.4, "Blue bubbles: the person, who calls himself Cool Radio."), (5.0, "Cream bubbles: Claude, an AI."), (6.4, "Little chips: the tools Claude used to do the work."))):
        if t > at: d.text((64, 250 + j * 46), ln, font=SERIF(28), fill=PAPER)
    d.text((64, 470), "Nothing is reworded. Long messages are cut short. Claude's private thinking is not shown.", font=F(15, "SemiBold"), fill=(170, 180, 180))
    return im


def s_outro(t):
    im = Image.new("RGB", (W, H), (28, 35, 38)); d = ImageDraw.Draw(im)
    d.text((60, 40), "WHAT JUST HAPPENED", font=F(48), fill=PAPER)
    rows = [(0.8, "67", "times the person asked for something"), (2.6, "156", "times Claude answered in words"), (4.4, "605", "times Claude used a tool instead of only talking"),
            (6.4, str(AGENTS), "helper agents Claude started, to work at the same time"), (8.6, "0", "times Claude could hear the films it made")]
    for j, (at, n, ln) in enumerate(rows):
        if t > at: d.text((64, 124 + j * 70), n, font=F(52), fill=PENCIL); d.text((230, 142 + j * 70), ln, font=SERIF(27), fill=PAPER)
    if t > 10.2: d.text((64, 488), "An AI does not just know things. It asks, looks, tries, checks, and gets corrected.", font=F(19), fill=PAPER)
    return im


if __name__ == "__main__":
    N = "narrator"
    a = segment("ch_intro", INTRO, s_intro, [(0.6, "This is a real chat between a person and Claude, an A I. Watch what Claude does when it is asked for something.", N)], sfx=[(tone, (0.2, 196))])
    b = segment("ch_body", TOTAL, frame, [(1.0, "The person asks.", N), (4.0, "Claude does not only answer. It uses tools.", N), (TOTAL * 0.5, "When it gets something wrong, the person says so, and Claude tries again.", N)],
                bed=("../music/the-verne-bench.ogg", 20, 0.22))
    c = segment("ch_outro", OUTRO, s_outro, [(0.8, "In two days, the person asked sixty seven times.", N), (4.4, "Claude used a tool six hundred and five times.", N), (8.6, "And it never once heard a film it made.", N)])
    lst = C.TMP + "/ch.txt"; open(lst, "w").write("".join("file '%s'\n" % p for p in (a, b, c))); out = "assets/behind-the-chat.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    print(out, round(TOTAL, 1))
