#!/usr/bin/env python3
"""build: gather seeds, ledgers and prompts into data.js for index.html."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
seeds = json.load(open("seeds.json"))
scions = json.load(open("scions.json"))
def entry(i):
    led = json.load(open("ledger/%s.json" % i)) if os.path.exists("ledger/%s.json" % i) else {}
    pf = "prompts/%s.txt" % i
    return {"id": i, "film": os.path.exists("films/%s.mp4" % i), "unit": os.path.exists("units/%s.mp4" % i), "verdict": led.get("verdict"),
            "takes": len(led.get("takes", [])), "open": led.get("open", []), "atlas": led.get("atlas", []),
            "control": led.get("control"), "prompt": open(pf).read().strip() if os.path.exists(pf) else ""}
ports = []
for n, r in enumerate(seeds, 1):
    e = entry("p%02d" % n)
    e.update(station=r[0], clue=r[1], lineage=r[2], turkey=r[3], trout=r[4], rule=r[5], kind=r[6])
    ports.append(e)
intro = []
for n, s in enumerate(scions, 1):
    e = entry("intro-%d" % n)
    e.update(title=s["title"], claim=s["claim"], scion=s["prompt"])
    intro.append(e)
atlas = {a["id"]: a["caption"] for a in json.load(open("atlas/atlas.json"))}
open("data.js", "w").write("window.TROUT_SUB = " + json.dumps(
    {"ports": ports, "intro": intro, "atlas": atlas, "introFilm": os.path.exists("films/intro.mp4")},
    ensure_ascii=False) + ";\n")
print("ports with film: %d/55, intro shots: %d/6" % (sum(p["film"] for p in ports), sum(p["film"] for p in intro)))
