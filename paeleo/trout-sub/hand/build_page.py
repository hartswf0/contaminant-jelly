#!/usr/bin/env python3
"""build_page: hand/index.html, the hand films with their whole process and provenance.

For each film: the film, what the porthole asks, the direction the maker was given, what the maker reported,
what the critic changed and still lists as open, every foraged source with author and licence, and the script
that draws it. Shared: the two briefs, the kit, and the swarm script with the exact maker and critic prompts.
"""
import html, json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
seeds = json.load(open("../seeds.json")); prov = json.load(open("provenance.json")); direction = json.load(open("directions.json"))
E_ = lambda s: html.escape(str(s), quote=True)
def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
cards = []
for pid in sorted(f[:-4] for f in os.listdir("assets/films") if f.endswith(".mp4") and f.startswith("p")):
    n = int(pid[1:]); r = seeds[n - 1]; p = prov.get(pid, {}); mk, cr = p.get("maker", {}), p.get("critic", {})
    note = open("films/notes/%s.txt" % pid).read().strip() if os.path.exists("films/notes/%s.txt" % pid) else ""
    cred = json.load(open("films/credits/%s.json" % pid)) if os.path.exists("films/credits/%s.json" % pid) else []
    li = lambda xs: "".join("<li>%s</li>" % E_(x) for x in xs)
    rows = "".join('<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        E_(c.get("source_url", "")), E_(c.get("title", "")), E_(c.get("author", "")),
        ('<a href="%s">%s</a>' % (E_(c["license_url"]), E_(c.get("license", "")))) if c.get("license_url") else E_(c.get("license", "")), E_(c.get("used_as", ""))) for c in cred)
    verdict = {"pass": "Passed review", "nearly": "Nearly passed", "not yet": "Not yet passed"}.get(cr.get("verdict"), "Not reviewed")
    cards.append('''<article id="%s">
<video controls playsinline preload="metadata" poster="assets/films/%s.webp" src="assets/films/%s.mp4"></video>
<div class="body"><div class="mono">Porthole %02d · %s · %d s</div><h2>%s</h2>
<span class="tag %s">%s</span>
<p><b>Turkey looking out:</b> %s<br><b>Trout looking in:</b> %s<br><b>Rule:</b> %s<br><b>Descends from:</b> %s</p>
<p class="note">%s</p>
<details><summary>Direction given to the maker</summary><p>%s</p></details>
<details><summary>What the maker reported</summary><p><b>Method.</b> %s</p><p><b>Animation SCIONs used.</b></p><ul>%s</ul><p><b>Weakest part, in the maker's words.</b> %s</p></details>
<details><summary>What the critic repaired (%d) and still lists as open (%d)</summary><p><b>Repaired</b></p><ul>%s</ul><p><b>Open</b></p><ul>%s</ul></details>
<details><summary>Foraged sources and licences (%d)</summary>%s</details>
<p class="links"><a href="films/%s.py.txt">The script that draws it</a> · <a href="assets/films/%s.mp4" download>Download</a></p>
</div></article>''' % (pid, pid, pid, n, E_(r[0].split("·")[1].strip()), round(dur("assets/films/%s.mp4" % pid)), E_(r[1]),
                       cr.get("verdict", "none").replace(" ", "-"), verdict, E_(r[3]), E_(r[4]), E_(r[5]), E_(r[2]), E_(note),
                       E_(direction.get(pid, "")), E_(mk.get("method", "")), li(mk.get("scions", [])), E_(mk.get("weak", "")),
                       len(cr.get("repaired", [])), len(cr.get("open", [])), li(cr.get("repaired", [])), li(cr.get("open", [])),
                       len(cred), ("<table><tr><th>Item</th><th>Author</th><th>Licence</th><th>Used as</th></tr>%s</table>" % rows) if cred else "<p>Nothing foraged; everything is handmade.</p>",
                       pid, pid))
    open("films/%s.py.txt" % pid, "w").write(open("films/%s.py" % pid).read())
for f in ("films/kit.py", "films/kit_anim.py"):
    open(f + ".txt", "w").write(open(f).read())
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tourkey Hand Films</title><style>
:root{--paper:#faf7ef;--ink:#24201d;--mute:#655c52;--rule:#d2c7b8;--accent:#812c3a;--teal:#1f6f66}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.5 Georgia,"Times New Roman",serif}
main{max-width:1080px;margin:0 auto;padding:28px 16px 80px}h1{font:800 clamp(34px,6vw,58px)/1 "Arial Narrow",Arial,sans-serif;text-transform:uppercase;margin:0 0 8px}
.lede{max-width:66ch;margin:0 0 10px}.mono{font:12px/1.4 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--mute)}
article{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:22px;align-items:start;border-top:2px solid var(--ink);padding:22px 0}
video{width:100%;aspect-ratio:16/9;background:#000;display:block}h2{font:800 28px/1.1 "Arial Narrow",Arial,sans-serif;text-transform:uppercase;margin:2px 0 8px}
.tag{display:inline-block;font:12px ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;border:1px solid;padding:2px 7px;margin-bottom:8px}
.tag.pass{color:var(--teal)}.tag.nearly{color:#9a6a12}.tag.not-yet,.tag.none{color:var(--accent)}
article>*{min-width:0}body{overflow-wrap:break-word}td:nth-child(3){white-space:nowrap}td:first-child{word-break:break-all;max-width:220px}details{overflow-x:auto}p{margin:0 0 10px}.note{color:var(--mute)}details{border-top:1px solid var(--rule);padding:7px 0}summary{cursor:pointer;font:13px ui-monospace,Menlo,monospace;letter-spacing:.04em;text-transform:uppercase}
details p,details ul{font-size:15px}ul{margin:4px 0 8px;padding-left:20px}table{width:100%;border-collapse:collapse;font-size:13.5px}td,th{text-align:left;vertical-align:top;border-top:1px solid var(--rule);padding:5px 8px 5px 0}
a{color:var(--accent)}.links{font:13px ui-monospace,Menlo,monospace;margin-top:8px}.shared{border-top:2px solid var(--ink);padding-top:18px}
@media(max-width:760px){article{grid-template-columns:1fr}}
</style></head><body><main>
<div class="mono">Tourkey Trouttown · hand films · batch 1</div>
<h1>Made by hand</h1>
<p class="lede">Each porthole gets a short film in which the thing is made on a table, then seen by Turkey through the glass, then by the trout from the river. The rule for all of them: <b>handmake or forage, no style costumes</b>. Everything on screen is either real printed matter from open archives, cut and hinged, or the actual object built in code.</p>
<p class="lede">Every film was made by one agent and then repaired by a second who had not seen it made. Their reports, the sources and the scripts are all here.</p>
@@CARDS@@
<section class="shared"><h2>How the batch was run</h2>
<p>One maker and one independent critic per porthole, five portholes at a time.</p>
<p class="links"><a href="BRIEF.md.txt">The brief every maker read</a> · <a href="films/BRIEF-2-oulipo.md.txt">The Oulipo "handmake or forage" brief it rests on</a> · <a href="swarm-batch-1.js.txt">The swarm script, with the exact maker and critic prompts</a> · <a href="films/kit.py.txt">The film kit</a> · <a href="films/kit_anim.py.txt">The animation and foraging kit</a> · <a href="../drawn/scions.json">The 54 animation SCIONs the makers chose from</a></p>
<p class="note">Not checked: the critics read each licence from the film's credits file and did not query the archive again. Sound is synthesized except where a source is listed.</p></section>
</main></body></html>'''.replace("@@CARDS@@", "\n".join(cards))
open("index.html", "w").write(page)
for f in ("BRIEF.md", "films/BRIEF-2-oulipo.md", "swarm-batch-1.js"):
    open(f + ".txt", "w").write(open(f).read())
print("hand/index.html", len(cards), "films")
