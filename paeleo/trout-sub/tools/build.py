#!/usr/bin/env python3
"""build: gather seeds, ledgers and prompts into data.js for index.html."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
seeds = json.load(open("seeds.json"))
scions = json.load(open("scions.json"))
def entry(i):
    led = json.load(open("ledger/%s.json" % i)) if os.path.exists("ledger/%s.json" % i) else {}
    pf = "prompts/%s.txt" % i
    clip = next((c for c in ("films/%s.mp4" % i, "films/%s-v2.mp4" % i) if os.path.exists(c)), None)
    p2 = "prompts2/%s.txt" % i
    head = open(p2).readline() if os.path.exists(p2) else ""
    m = re.search(r"feedstock:\s*([a-z0-9-]+)", head)
    return {"id": i, "film": bool(clip), "clip": clip, "feedstock": m.group(1) if m else None,
            "v2": os.path.exists("films/%s-v2.mp4" % i), "unit": os.path.exists("units/%s.mp4" % i), "verdict": led.get("verdict"),
            "takes": len(led.get("takes", [])), "open": led.get("open", []), "atlas": led.get("atlas", []),
            "control": led.get("control"), "prompt": open(pf).read().strip() if os.path.exists(pf) else "",
            "prompt2": open(p2).read().strip() if os.path.exists(p2) else ""}
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
