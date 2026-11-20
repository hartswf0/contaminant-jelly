#!/usr/bin/env python3
"""build_class_page: the public page for the five class films -> class.html, plus .txt copies of every script and note.

Children appear by first initial only. The photographs of the sheets are never published."""
import html, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
E_ = html.escape
T = json.load(open("../class/transcripts.json"))
def txt(path):
    open(path + ".txt", "w").write(open(path).read()); return path + ".txt"
def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
def who(n):
    return n if n and len(n) <= 2 else "pilot"
def row(label, v):
    if not v or not v.get("reads"):
        return "<tr><th>%s</th><td class=blank colspan=2>left blank</td></tr>" % label
    return "<tr><th>%s</th><td>%s</td><td class=reads>%s</td></tr>" % (label, E_(v["wrote"]), E_(v["reads"]))
UNITS = [("Story unit", "board.md"), ("World unit", "WORLD.md"), ("World unit, code", "world.py"), ("Pilot scene unit", "scene_pilot.py"),
         ("Turkey scene unit", "scene_turkey.py"), ("Trout scene unit", "scene_trout.py")]
secs = []
for s in T["sheets"]:
    n = s["porthole"]; pid = "c%d" % n; d = "films/swarm/%s/" % pid
    links = ["<a href='%s'>%s</a>" % (txt(d + f), E_(u)) for u, f in UNITS] + ["<a href='%s'>Editor</a>" % txt("films/%s.py" % pid)]
    note = open("films/notes/%s.txt" % pid).read().strip().split("\n")
    cred = json.load(open("films/credits/%s.json" % pid))
    voice = json.load(open("films/notes/%s.voice.json" % pid))
    rows = [row("Who is outside", s["pilot"]["who_outside"]), row("What Turkey does", s["pilot"]["turkey_does"]), row("How the air goes", s["pilot"]["air"])]
    for f, lab in (("first_friend", "Turkey thinks"), ("next_friend", "The trout think")):
        fr = s[f]
        rows.append("<tr class=pick><th>%s</th><td colspan=2>%s picked: <b>%s</b></td></tr>" % (lab, E_(who(fr["name"])), E_(fr["picked"] or "nothing picked")))
        for k in ("probable", "plausible", "preposterous"):
            rows.append(row(k.capitalize(), fr[k]))
    credits = "".join("<li><a href='%s'>%s</a>, %s, %s. %s</li>" % (E_(c["source_url"]), E_(c["title"]), E_(c["author"]), E_(c["license"]), E_(c["used_as"])) for c in cred) or "<li>Nothing foraged. Every piece is cut and drawn in code.</li>"
    spoken = "".join("<li>%.1fs · %s · %s</li>" % (l["at"], l["speaker"], E_(l["text"])) for l in voice["lines"])
    secs.append("""<section id="%s"><h2><span class=num>%02d</span> %s</h2><p class=clue>%s</p>
<video controls preload=none poster="assets/films/%s.webp" src="assets/voiced/%s.mp4"></video>
<p class=meta>%.0f seconds · pilot's drawing: %s</p>
<h3>What the children wrote</h3><div class=scroll><table><tr><td></td><th>as written</th><th>on screen and spoken</th></tr>%s</table></div>
<h3>The swarm: nine units</h3><p>%s. Then a critic and a rights reviewer, and a repair unit that applied both.</p>
%s
<details><summary>Sources and credits</summary><ul>%s</ul></details>
<details><summary>Voices and song</summary><p>Song: %s, from %d s.</p><ul>%s</ul></details></section>""" % (
        pid, n, E_(s["station"]), E_(s["clue"]), pid, pid, dur("assets/voiced/%s.mp4" % pid), E_(s["pilot"]["drawing"]), "".join(rows), " · ".join(links),
        "".join("<p class=note>%s</p>" % E_(x) for x in note if x.strip()), credits, E_(voice["song"]), voice["song_from_seconds"], spoken))
page = """<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>The Class Portholes</title>
<style>
:root{--bg:#f4efe4;--ink:#1c2326;--mute:#5d676b;--line:#d5ccb8;--card:#fffdf7;--acc:#a8432a}
@media(prefers-color-scheme:dark){:root{--bg:#12191b;--ink:#ece6d8;--mute:#9aa5a8;--line:#2c383b;--card:#1a2325;--acc:#e58a6c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 Georgia,serif}
main{max-width:860px;margin:0 auto;padding:28px 16px 80px}h1{font-size:clamp(34px,7vw,58px);line-height:1.02;margin:.2em 0}
h2{font-size:28px;margin:0 0 4px}h3{font:600 13px/1.2 system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:22px 0 8px}
.num{display:inline-block;background:var(--ink);color:var(--bg);font:800 22px system-ui,sans-serif;padding:2px 10px;border-radius:8px;margin-right:8px;vertical-align:3px}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin:26px 0}
video{width:100%%;border-radius:10px;background:#000;aspect-ratio:16/9}.clue,.meta{color:var(--mute);margin:.2em 0 .8em}.meta{font-size:14px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%%;font-size:15px}th,td{text-align:left;padding:6px 8px;border-top:1px solid var(--line);vertical-align:top}
th{font:600 13px system-ui,sans-serif;color:var(--mute);white-space:nowrap}.reads{font-style:italic}.blank{color:var(--mute)}.pick td{font-family:system-ui,sans-serif;font-size:14px}
a{color:var(--acc)}.note{font-size:15px;color:var(--mute)}details{margin-top:10px;font-size:15px}summary{cursor:pointer;font-family:system-ui,sans-serif}
nav a{margin-right:12px;font:700 16px system-ui,sans-serif}
</style><main>
<p><a href="./">Hand films</a> · <a href="../../">Turkey Sub</a></p>
<h1>The Class Portholes</h1>
<p>Five Porthole Logs filled in by a fourth-grade class, made into five short films. Every sentence on screen and every sentence spoken is one a child wrote. The spelling is tidied for the caption and kept as written in the tables below. Lines the children left blank stay blank, and no die is thrown.</p>
<p>Children are named by first initial only. The photographs of their sheets are not published.</p>
<section><h2>How to Play the Porthole Game</h2><p class=clue>All five films in one, 6:22. It teaches the four steps first, names the step and the question under every picture, and gives one thing to watch for before each porthole.</p>
<video controls preload=none src="assets/how-to-play-the-porthole-game.mp4"></video>
<p class=meta><a href="assets/how-to-play-the-porthole-game.mp4" download>Download the film</a> · <a href="class_cut.py.txt">how it was cut</a></p></section>
<nav>%s</nav>
%s
<section><h2>How these were made</h2>
<p>Each film was made by nine units working in five stages: a story unit and a world unit; three scene units (the pilot, Turkey's seat, the river side); an editor; a critic and a rights reviewer; a repair unit. Forty-five agents across the five films. The pictures are cut paper and pencil drawn in code, with two public-domain plates (Audubon's wild turkey, Denton's brook trout) where a film forages. The voices are three stock Kokoro voices run locally; the songs are passages from DEEP SEA VOYAGE.</p>
<p><a href="%s">Brief</a> · <a href="%s">Swarm script</a> · <a href="%s">Transcripts</a> · <a href="%s">Voice pass</a> · <a href="%s">Kit</a></p></section>
</main></html>""" % (" ".join("<a href='#c%d'>%02d</a>" % (s["porthole"], s["porthole"]) for s in T["sheets"]), "\n".join(secs),
                    txt("BRIEF-CLASS.md"), txt("swarm-class.js"), "transcripts.json", txt("voice_pass.py"), txt("films/kit.py"))
tj = json.loads(json.dumps(T))
for s in tj["sheets"]:
    for f in ("pilot", "first_friend", "next_friend"):
        if len(s[f].get("name") or "") > 2: s[f]["name"] = "(not read)"
json.dump(tj, open("transcripts.json", "w"), indent=1, ensure_ascii=False)
txt("class_cut.py"); open("class.html", "w").write(page); print("class.html", len(page))
