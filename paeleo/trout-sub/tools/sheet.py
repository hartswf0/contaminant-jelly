#!/usr/bin/env python3
"""sheet: the Porthole Log, redrawn in the film's world, one per slip.

    python3 tools/sheet.py     # youtube/porthole-logs.pdf (55 logs, front and back), sheets/master-1.png,
                               # sheets/master-2.png and sheets/steps.json for the film's cards

One symbol, one meaning, the same on paper and on screen:
- controller buttons (green triangle, red circle, blue cross, pink square) are the four choices;
- die faces 1 to 6 are the six bolts, the six endings;
- the big numbered slabs 1 to 8 are the film's eight cards, so "card 5" on screen is "zone 5" on paper.
Probable, Plausible and Preposterous are named in words beside their dice, with no symbol of their own.
Every prompt printed on the sheet is the same sentence the film says for that line.
The page is HTML printed by Chromium; each entry line carries data-step, and its measured place on the
page is written to sheets/steps.json so the film can magnify exactly that line.
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
seeds = json.load(open("seeds.json"))
timing = json.load(open("youtube/timing.json"))["portholes"] if os.path.exists("youtube/timing.json") else {}
COL = {"triangle": "#38d696", "circle": "#ff5c5c", "cross": "#60a0ff", "square": "#ff80d2", "hexagon": "#ffbe50"}
DIVES = [("Dive 1", 1, 16), ("Dive 2", 17, 32), ("Dive 3", 33, 48), ("Dive 4", 49, 55)]


def options(q):
    parts = [x.strip() for x in re.split(r",\s*or\s+|,\s*|\s+or\s+", q.strip().rstrip("?")) if x.strip()]
    return [x[0].upper() + x[1:] for x in parts]


def button(kind, cls="btn"):
    inner = {"circle": '<circle cx="12" cy="12" r="5.4"/>', "triangle": '<path d="M12 6 17.8 16.2H6.2Z"/>',
             "square": '<rect x="7.2" y="7.2" width="9.6" height="9.6"/>', "cross": '<path d="M7.4 7.4 16.6 16.6M16.6 7.4 7.4 16.6"/>',
             "hexagon": '<path d="M17.6 12 14.8 16.8H9.2L6.4 12 9.2 7.2h5.6Z"/>'}[kind]
    return ('<svg class="%s" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#0a0c10"/><circle cx="12" cy="12" r="10.2" fill="none" stroke="%s" stroke-width="1.1"/>'
            '<g fill="none" stroke="%s" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">%s</g></svg>' % (cls, COL[kind], COL[kind], inner))


PIPS = {1: [(12, 12)], 2: [(7, 7), (17, 17)], 3: [(7, 7), (12, 12), (17, 17)], 4: [(7, 7), (17, 7), (7, 17), (17, 17)],
        5: [(7, 7), (17, 7), (12, 12), (7, 17), (17, 17)], 6: [(7, 6), (17, 6), (7, 12), (17, 12), (7, 18), (17, 18)]}
def die(n, cls="die", at=None):
    pos = ' x="%.1f" y="%.1f" width="26" height="26"' % at if at else ""
    return ('<svg class="%s"%s viewBox="0 0 24 24"><rect x="1.5" y="1.5" width="21" height="21" rx="4.4" fill="#fbf6e9" stroke="#6e4810" stroke-width="1.6"/>%s</svg>'
            % (cls, pos, "".join('<circle cx="%d" cy="%d" r="2.05" fill="#16293a"/>' % p for p in PIPS[n])))


def ring():
    """The porthole to draw in: brass rim, a die face on each bolt, in the film's order (clockwise from the top)."""
    import math
    dice = ""
    for k in range(6):
        a = math.radians(-90 + 60 * k)
        dice += die(k + 1, "rd", (150 + 128 * math.cos(a) - 13, 150 + 128 * math.sin(a) - 13))
    return ('<svg class="ring" viewBox="0 0 300 300"><circle cx="150" cy="150" r="128" fill="#fff" stroke="#d69e3c" stroke-width="26"/>'
            '<circle cx="150" cy="150" r="141.5" fill="none" stroke="#16293a" stroke-width="1.6"/><circle cx="150" cy="150" r="114.5" fill="none" stroke="#16293a" stroke-width="1.6"/>%s</svg>' % dice)


def lines(n):
    return '<div class="lines">%s</div>' % ("<i></i>" * n)


def slab(n, title, who):
    return '<div class="zone-h"><span class="slab">%d</span><b>%s</b><em>%s</em></div>' % (n, title, who)


def pick(kinds, words, tag, step_a, step_b, card):
    plates = "".join('<span class="plate" style="border-color:%s">%s<span>%s</span></span>' % (COL[k], button(k), html.escape(w) if w else "&nbsp;") for k, w in zip(kinds, words))
    return ('<div class="pick"><div class="tag" data-step="%s" data-card="%d" data-say="%s">%s</div><div class="plates%s" data-step="%s-plates" data-card="%d" data-say="Pick one.">%s</div>'
            '<div class="draw" data-step="%s" data-card="%d" data-say="Draw its shape."><span>Draw the one you pick</span><b></b></div></div>'
            % (step_a, card, tag + ".", tag, " three" if len(kinds) > 2 else "", step_a, card, plates, step_b, card))


def bolt(n, word, say, card):
    return ('<div class="bolt" data-step="bolt%d" data-card="%d" data-say="Bolt %d. %s">%s<b>%s</b><span>%s</span>%s</div>'
            % (n, card, n, say, die(n), word, say, lines(2)))


def log(n=None):
    """Front and back for porthole n; n=None gives the blank master the film shows."""
    if n:
        r = seeds[n - 1]; station = r[0].split("·")[1].strip(); num = "%02d" % n; clue, rule = html.escape(r[1]), html.escape(r[5])
        to, tr = options(r[3]), options(r[4])
        dive = next(d[0] for d in DIVES if d[1] <= n <= d[2]); when = "%s, at %s" % (dive, timing.get(num, "")) if timing else dive
    else:
        station = num = clue = rule = ""; to, tr = ["", ""], ["", ""]; when = ""
    kt, kr = ["triangle", "circle", "hexagon"][:len(to)], ["cross", "square", "hexagon"][:len(tr)]
    fill = lambda v: '<b class="fill">%s</b>' % v if v else '<b class="fill blank"></b>'
    front = '''<section class="page">
<header><div class="kick">PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE<h1>Porthole Log</h1></div><div class="badge">%s</div></header>
<div class="zone">%s
 <div class="row"><label data-step="name" data-card="1" data-say="Write your name.">Pilot <b class="fill blank wide"></b></label>
  <label data-step="number" data-card="1" data-say="This is your number.">Porthole # %s</label>
  <label data-step="station" data-card="1" data-say="This is your station.">Station %s</label></div>
 <div class="row"><label class="grow" data-step="clue" data-card="1" data-say="Read your clue and your rule.">Clue %s <span class="rule">Rule %s</span></label></div>
</div>
<div class="zone">%s
 <div class="ringwrap" data-step="ring" data-card="2" data-say="Draw it inside the ring.">%s</div>
</div>
<div class="zone">%s
 <div class="q" data-step="q1" data-card="3" data-say="1. Who is outside the glass?"><b>1.</b> Who is outside the glass? What do they think our sub is?</div>
 <div data-step="a1" data-card="3" data-say="Write it here.">%s</div>
 <div class="q" data-step="q2" data-card="3" data-say="2. What one thing does Turkey do?"><b>2.</b> What one thing does Turkey do?</div>
 <div data-step="a2" data-card="3" data-say="Write it here.">%s</div>
 <div class="q" data-step="q3" data-card="3" data-say="3. How could this use up our air?"><b>3.</b> How could this use up our air?</div>
 <div data-step="a3" data-card="3" data-say="Write it here.">%s</div>
</div>
<div class="bar" data-step="pass1" data-card="3" data-say="Pass your paper left.">&larr; Pass your paper left</div>
<footer>%s</footer></section>''' % (num or "&nbsp;", slab(1, "Your slip", "Pilot"), fill(num), fill(html.escape(station)), fill(clue), fill(rule),
                                       slab(2, "Draw what Turkey sees", "Pilot"), ring(), slab(3, "Write 3 things", "Pilot"), lines(2), lines(2), lines(2),
                                       ("In the film TOURKEY TROUTTOWN: " + when) if when else "TOURKEY TROUTTOWN")
    back = '''<section class="page back">
<header><div class="kick">PAE-09 · TROUT TOWN · TOUR-KEY SUBMARINE<h1>Six bolts, six endings</h1></div><div class="badge">%s</div></header>
<div class="zone">%s
 <div class="kinds"><span data-step="k1" data-card="4" data-say="Probable: what you expect.">%s%s<b>Probable</b> what you expect</span>
  <span data-step="k2" data-card="4" data-say="Plausible: strange, but it fits.">%s%s<b>Plausible</b> strange, but it fits</span>
  <span data-step="k3" data-card="4" data-say="Preposterous: a wild surprise!">%s%s<b>Preposterous</b> a wild surprise!</span></div>
</div>
<div class="cols">
 <div class="zone">%s
  <label class="nm" data-step="name1" data-card="5" data-say="First friend: write your name.">Name <b class="fill blank wide"></b></label>
  %s%s%s%s
  <div class="bar" data-step="pass2" data-card="5" data-say="Pass it left again.">&larr; Pass it left again</div></div>
 <div class="zone">%s
  <label class="nm" data-step="name2" data-card="6" data-say="Next friend: write your name.">Name <b class="fill blank wide"></b></label>
  %s%s%s%s
  <div class="bar gold" data-step="pass3" data-card="6" data-say="Give it back to the pilot.">&rarr; Give it back to the pilot</div></div>
</div>
<div class="zone">%s
 <div class="roll"><span data-step="roll" data-card="7" data-say="Roll the die one time.">Roll the die one time.</span>
  <label data-step="rolled" data-card="7" data-say="Write the number you rolled.">I rolled <b class="fill blank"></b></label>
  <span class="six" data-step="circle" data-card="7" data-say="Or circle that die.">or circle it %s</span></div>
</div>
<div class="zone">%s
 <div class="q" data-step="gq" data-card="8" data-say="What do the trout tell the newspaper?">What do the trout tell the newspaper?</div>
 <div data-step="ga" data-card="8" data-say="Write it here.">%s</div>
 <div class="q" data-step="mq" data-card="8" data-say="Why did Turkey come to Trout Town?">Why did Turkey come to Trout Town?</div>
 <div data-step="ma" data-card="8" data-say="Write your message home.">%s</div>
</div>
<footer>%s</footer></section>''' % (num or "&nbsp;", slab(4, "Three kinds of endings", "Everyone"), die(1), die(4), die(2), die(5), die(3), die(6),
                                       slab(5, "First friend", "Bolts 1, 2, 3"), pick(kt, to, "Turkey thinks", "pick1", "draw1", 5),
                                       bolt(1, "Probable", "What would you expect?", 5), bolt(2, "Plausible", "Strange, but it fits.", 5), bolt(3, "Preposterous", "A wild surprise!", 5),
                                       slab(6, "Next friend", "Bolts 4, 5, 6"), pick(kr, tr, "The trout think", "pick2", "draw2", 6),
                                       bolt(4, "Probable", "What would you expect?", 6), bolt(5, "Plausible", "Strange, but it fits.", 6), bolt(6, "Preposterous", "A wild surprise!", 6),
                                       slab(7, "Roll", "Pilot"), "".join(die(k) for k in range(1, 7)), slab(8, "Tell what happened", "Pilot"), lines(2), lines(2),
                                       ("Porthole %s · %s" % (num, html.escape(station))) if num else "TOURKEY TROUTTOWN")
    return front + back


CSS = '''
@font-face{font-family:Inter;font-weight:400;src:url(file:///usr/share/fonts/opentype/inter/Inter-Regular.otf)}
@font-face{font-family:Inter;font-weight:600;src:url(file:///usr/share/fonts/opentype/inter/Inter-SemiBold.otf)}
@font-face{font-family:Inter;font-weight:700;src:url(file:///usr/share/fonts/opentype/inter/Inter-Bold.otf)}
@font-face{font-family:Inter;font-weight:900;src:url(file:///usr/share/fonts/opentype/inter/Inter-Black.otf)}
@page{size:8.5in 11in;margin:0}*{box-sizing:border-box}
body{margin:0;font:600 12.5px/1.3 Inter,Arial,sans-serif;color:#16293a;background:#fff}
.page{width:8.5in;height:11in;padding:9mm 13mm 7mm;display:flex;flex-direction:column;gap:2.6mm;break-after:page;position:relative;overflow:hidden}
header{display:flex;justify-content:space-between;align-items:flex-start}
.kick{font-size:8.5px;font-weight:900;letter-spacing:.08em;color:#8a5a12}h1{margin:.5mm 0 0;font-size:25px;font-weight:900;letter-spacing:0;color:#16293a}
.badge{background:#0a1012;color:#fff;font-weight:900;font-size:40px;line-height:1;padding:2.2mm 4mm;border-radius:4mm;min-width:22mm;text-align:center}
.zone{border:1.4px solid #16293a;border-radius:3mm;padding:2.2mm 3.2mm 2.6mm;display:flex;flex-direction:column;gap:1.5mm}
.zone-h{display:flex;align-items:center;gap:2.6mm}.zone-h b{font-size:17px;font-weight:900}.zone-h em{font-style:normal;font-size:10.5px;font-weight:700;color:#8a5a12;border:1.2px solid #d69e3c;background:#fbf3df;border-radius:1.6mm;padding:.4mm 1.8mm}
.slab{display:inline-block;background:#c95c3e;color:#fff;font-weight:900;font-size:22px;line-height:1;padding:1.3mm 2.6mm 1.5mm;transform:skew(-4deg) rotate(-2deg);border-radius:.6mm}
.row{display:flex;gap:6mm;align-items:flex-end}label{display:flex;align-items:flex-end;gap:2mm;font-weight:700;white-space:nowrap}.grow{flex:1;white-space:normal;flex-wrap:wrap}
.fill{display:inline-block;font-weight:900;font-size:15px;border-bottom:1.3px solid #16293a;padding:0 2mm .3mm;min-width:16mm}.fill.blank{height:6.2mm}.fill.wide{min-width:58mm}
.rule{display:inline-flex;gap:2mm;align-items:flex-end;margin-left:5mm}.rule .fill{font-size:13px;color:#8a5a12}
.ringwrap{display:flex;justify-content:center}.ring{width:87mm;height:87mm}
.q{font-size:14.5px;font-weight:700;margin-top:.6mm}.q b{font-weight:900}
.lines{display:flex;flex-direction:column}.lines i{display:block;height:7mm;border-bottom:1.2px solid #16293a}
.bar{background:#16344a;color:#fff;font-weight:900;font-size:13px;border-radius:1.8mm;padding:1.8mm 3.4mm}.bar.gold{background:#6e4810}
footer{margin-top:auto;font-size:9px;font-weight:700;color:#5f6c70;text-align:right}
.kinds{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3mm}.kinds span{display:flex;align-items:center;gap:1.2mm;font-size:11.5px;font-weight:600;border:1.2px solid #9fb0bf;background:#f1f5f8;border-radius:2mm;padding:1.4mm 2mm}.kinds b{font-weight:900;font-size:13px;margin:0 .6mm 0 .8mm}
.die{width:6mm;height:6mm;flex:none}.cols{display:grid;grid-template-columns:1fr 1fr;gap:4mm}
.nm{width:100%}.nm .fill{flex:1;min-width:0}
.pick{display:flex;flex-direction:column;gap:1.3mm;border:1.2px solid #9fb0bf;background:#f1f5f8;border-radius:2mm;padding:1.6mm 2mm 2mm}
.tag{font-weight:900;font-size:12.5px}.plates{display:flex;flex-direction:column;gap:1.2mm}
.plate{display:flex;align-items:center;gap:2mm;background:#0a1012;color:#fff;border:1.6px solid;border-radius:2.6mm;padding:.7mm 2.4mm .7mm 1.2mm;font-weight:700;font-size:13px;min-height:7.6mm}.btn{width:6mm;height:6mm;flex:none}
.plates.three{gap:.7mm}.plates.three .plate{min-height:6.3mm;padding-top:.3mm;padding-bottom:.3mm;font-size:12px}.plates.three .btn{width:5.2mm;height:5.2mm}.draw{display:flex;align-items:center;justify-content:space-between;font-weight:700;font-size:12px}.draw b{display:block;width:11mm;height:11mm;border:1.6px dashed #16293a;border-radius:50%;background:#fff}
.bolt{display:grid;grid-template-columns:auto auto 1fr;column-gap:1.6mm;align-items:center}.bolt b{font-weight:900;font-size:13px}.bolt span{font-size:11.5px;font-weight:600;color:#44525a}.bolt .lines{grid-column:1/-1}.bolt .lines i{height:5.5mm}.back .lines i{height:6.2mm}.back .bolt .lines i{height:5.5mm}.back{gap:2.1mm}
.roll{display:flex;align-items:center;gap:7mm;font-weight:700;font-size:14px}.six{display:flex;align-items:center;gap:1.3mm}.six .die{width:7.4mm;height:7.4mm}
'''
def page(body):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Porthole Log</title><style>%s</style></head><body>%s</body></html>' % (CSS, body)


if __name__ == "__main__":
    os.makedirs("youtube", exist_ok=True); os.makedirs("sheets", exist_ok=True)
    open("youtube/porthole-logs.html", "w").write(page("".join(log(n) for n in range(1, 56))))
    open("sheets/master.html", "w").write(page(log(31)))     # the film shows a filled example, porthole 31
    js = r'''
const {chromium}=require('playwright');(async()=>{
 const b=await chromium.launch();
 let p=await b.newPage();await p.goto('file://'+process.cwd()+'/youtube/porthole-logs.html');await p.evaluate(()=>document.fonts.ready);
 await p.pdf({path:'youtube/porthole-logs.pdf',width:'8.5in',height:'11in',printBackground:true});
 const over=await p.evaluate(()=>[...document.querySelectorAll('.page')].filter(e=>e.scrollHeight>e.clientHeight+1).length);
 p=await b.newPage({viewport:{width:816,height:1056},deviceScaleFactor:2.3});await p.goto('file://'+process.cwd()+'/sheets/master.html');await p.evaluate(()=>document.fonts.ready);
 const pages=await p.$$('.page');for(let i=0;i<pages.length;i++)await pages[i].screenshot({path:'sheets/master-'+(i+1)+'.png'});
 const steps=await p.evaluate(()=>[...document.querySelectorAll('.page')].flatMap((pg,pi)=>{const o=pg.getBoundingClientRect();
   return [...pg.querySelectorAll('[data-step]')].map(e=>{const r=e.getBoundingClientRect();return {step:e.dataset.step,card:+e.dataset.card,say:e.dataset.say,page:pi+1,
     box:[(r.left-o.left)*.75,(r.top-o.top)*.75,(r.right-o.left)*.75,(r.bottom-o.top)*.75].map(v=>Math.round(v*10)/10)}})}));
 require('fs').writeFileSync('sheets/steps.json',JSON.stringify(steps,null,1));
 console.log(JSON.stringify({overflowing_pages:over,steps:steps.length}));await b.close()})()'''
    import subprocess
    print(subprocess.run(["node", "-e", js], capture_output=True, text=True, env=dict(os.environ, NODE_PATH=os.environ.get("NODE_PATH", ""))).stdout.strip() or "node failed")
