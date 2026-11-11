# Writes the worlds wall: bonus/worlds.html and the Bolas edition bolas/worlds/index.html. Every tile is a still captured from the running orchestra (bonus/worlds/<id>.jpg).
import json, os, sys, shutil, glob, html
SRC = '/home/user/contaminant-jelly/bonus/'; W = json.load(open(SRC + 'worlds/worlds.json')); L = W['looks']; E = html.escape
def page(orch, img, fonts, home, homename):
    def tile(l, k):
        q = ('?city=' + l['city']) if l['city'] else ('?look=' + l['id']); sub = l['own'] or ('after ' + l['after'].split(':')[0]); rot = [-1.2, .8, -.5, 1.4, -.9, .4][k % 6]
        return f'<a class="p t{k % 5}" style="--r:{rot}deg" href="{orch}{q}"><img src="{img}{l["id"]}.jpg" alt="" loading="lazy"><b>{E(l["name"])}</b><i>{E(sub)}</i><span>{E(l["rule"])}</span></a>'
    def sec(tag, title, say, ls): return f'<section><h2><em>{tag}</em>{title}</h2><p class="say">{say}</p><div class="wall">' + ''.join(tile(l, k) for k, l in enumerate(ls)) + '</div></section>'
    street = [l for l in L if l['street']]; rooms = [l for l in L if l['id'] in ('library', 'datacenter', 'store', 'depot', 'wet')]; cities = [l for l in L if str(l['city']).startswith('b')]; exps = [l for l in L if not l['city'] and not l['street'] and l not in rooms]
    npoem = len([l for l in L if l['city'] and not str(l['city']).startswith('b')]); lens = W['lenses']; names = {l['id']: l['name'] for l in L}
    lensrow = ''.join(f'<a href="{orch}?city=b5&lens={x}"><b>{E(names.get(x, "BY HAND"))}</b>{E(W["build"][x])}</a>' for x in lens)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Worlds · the Jelly Orchestra</title><link rel="stylesheet" href="{fonts}">
<style>
:root{{--wall:#3b3936;--ink:#ece4d2;--dim:#a89f8f;--red:#d2261a;--amber:#f0a35a;--teal:#1d5a63}}
*{{box-sizing:border-box}}html{{background:#2b2a28}}
body{{margin:0;color:var(--ink);font:300 15px/1.5 'Jost',system-ui,sans-serif;background:
 radial-gradient(1200px 500px at 20% 10%,#4a4743 0,transparent 70%),radial-gradient(900px 600px at 85% 60%,#45413c 0,transparent 70%),
 repeating-linear-gradient(0deg,rgba(0,0,0,.05) 0 1px,transparent 1px 3px),repeating-linear-gradient(90deg,rgba(255,255,255,.015) 0 2px,transparent 2px 7px),#34322f}}
a{{color:inherit;text-decoration:none}}
header{{padding:18px 16px 0;max-width:1240px;margin:auto}}
.k{{font:400 11px/1 'JetBrains Mono',monospace;letter-spacing:.22em;color:var(--amber)}}
.hero{{display:block;width:100%;margin:14px 0 0;border:0;box-shadow:0 18px 50px rgba(0,0,0,.55)}}
.cap{{font:400 11px/1.5 'JetBrains Mono',monospace;color:var(--dim);margin:8px 0 0}}
h1{{font:400 clamp(34px,7vw,76px)/.95 'Anton',sans-serif;letter-spacing:.01em;margin:26px 0 6px;text-transform:uppercase}}
h1 u{{text-decoration:none;color:var(--red)}}
.lede{{max-width:62ch;color:#d8cfbd;margin:0 0 6px}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}}
nav a{{font:400 11px/1 'JetBrains Mono',monospace;letter-spacing:.14em;padding:9px 11px;background:#161514;border:1px solid #55504a}}
nav a:hover{{background:var(--red);border-color:var(--red)}}
section{{max-width:1240px;margin:auto;padding:44px 16px 8px}}
h2{{font:400 clamp(26px,4.4vw,44px)/1 'Anton',sans-serif;text-transform:uppercase;margin:0;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
h2 em{{font:400 11px/1 'JetBrains Mono',monospace;letter-spacing:.2em;color:#161514;background:var(--amber);padding:5px 7px;font-style:normal}}
.say{{color:var(--dim);max-width:70ch;margin:8px 0 20px}}
.wall{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px 18px}}
.p{{display:block;background:#e9dfc8;color:#1a1816;padding:8px 8px 12px;transform:rotate(var(--r));box-shadow:0 10px 24px rgba(0,0,0,.5);transition:transform .18s;position:relative;
 clip-path:polygon(0 1.5%,3% 0,22% 1%,41% 0,63% 1.2%,82% 0,100% 1%,99.2% 24%,100% 52%,99% 78%,100% 99%,78% 100%,55% 99%,31% 100%,9% 99.2%,0 100%,.8% 71%,0 44%,.9% 18%)}}
.p:hover{{transform:rotate(0) scale(1.03);z-index:2}}
.p.t1{{background:#d9cdb2}}.p.t2{{background:#efe8d8}}.p.t3{{background:#e3d2ad}}.p.t4{{background:#dcd6c8}}
.p img{{display:block;width:100%;aspect-ratio:8/5;object-fit:cover;background:#111}}
.p b{{display:block;font:400 22px/1 'Anton',sans-serif;letter-spacing:.02em;margin:9px 2px 2px;text-transform:uppercase}}
.p i{{display:block;font:400 10px/1.35 'JetBrains Mono',monospace;color:#8a2219;font-style:normal;margin:0 2px 5px}}
.p span{{display:block;font-size:13px;line-height:1.35;margin:0 2px;color:#3a3530}}
.lens{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1px;background:#55504a;border:1px solid #55504a}}
.lens a{{background:#1b1a19;padding:11px 12px;font-size:13px;line-height:1.35;color:#cfc6b4}}
.lens a:hover{{background:#262422}}
.lens b{{display:block;font:400 11px/1 'JetBrains Mono',monospace;letter-spacing:.14em;color:var(--amber);margin-bottom:5px}}
.refs{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.refs img{{width:100%;display:block;box-shadow:0 10px 24px rgba(0,0,0,.5)}}
footer{{max-width:1240px;margin:auto;padding:40px 16px 60px;color:var(--dim);font-size:13px}}
@media (max-width:560px){{.wall{{grid-template-columns:1fr 1fr;gap:14px 10px}}.p b{{font-size:17px}}.p span{{display:none}}.refs{{grid-template-columns:1fr 1fr 1fr;gap:6px}}}}
</style></head><body>
<header><div class="k"><a href="{home}">{homename}</a> · WORLDS</div>
<img class="hero" src="{img}ref-wall.jpg" alt="A concrete wall of twelve painted panels of jellyfish under the word WORLDS">
<p class="cap">The wall above is the reference board. Every tile below it is a still taken from the running page; touch one to go in.</p>
<h1>{len(street) + len(exps) + len(rooms) + len(cities) + npoem} worlds.<br><u>One orchestra.</u></h1>
<p class="lede">Each world is a different answer to the same question: what does it look like when every jellyfish is one sound? Some are places, some are ways of seeing, and eight are painted.</p>
<nav><a href="#street">PAINT · {len(street)}</a><a href="#exp">EXPERIMENTS · {len(exps)}</a><a href="#rooms">ROOMS · {len(rooms)}</a><a href="#cities">CITIES · {len(cities)} + {npoem}</a><a href="#lens">BUILDERS · {len(lens)}</a><a href="#brief">THE BRIEF</a><a href="#find">WHERE THINGS ARE</a><a href="#objects">OBJECTS</a><a href="#evolve">NEXT</a></nav></header>
<span id="street"></span>{sec('PAINT', 'Street and film', 'Paint. On concrete: a stencil, a three-colour poster and a spray can. On film: running dye, and ink still wet. On paper: watercolour and black ink wash. On canvas: thick paint.', street)}
<span id="exp"></span>{sec('TWELVE', 'Experiments', 'Twelve ways of seeing, each with one rule and one animal that breaks it.', exps)}
<span id="rooms"></span>{sec('FIVE', 'Rooms', 'Built places to be inside: a reading room, a cold aisle, a flooded rental store, a depot of film cans, and a store of specimens in jars.', rooms)}
<span id="cities"></span>{sec('SEVEN', 'Celluloid cities', f'All 434 Bolas films as towers built of their own frames. In ALLWAYS · ARGON, schools of jellies rebuild the cuts shot by shot. {npoem} more cities hold the Cineosis poems; choose them from the cities menu inside.', cities)}
<section id="lens"><h2><em>{len(lens)}</em>Builders</h2><p class="say">Any city can be seen through any lens, and each lens rebuilds a cut in its own way. Each link opens ALLWAYS · ARGON through that lens.</p><div class="lens">{lensrow}</div></section>

<section id="find"><h2><em>MAP</em>Where everything is</h2><p class="say">Every world has an address. Add it to the page address, or use the two menus at the bottom of the orchestra (worlds… and cities…).</p><div class="lens">
<a href="{orch}?look=ink"><b>A WORLD</b>?look= and its name: ink, wash, watercolour, sumi, impasto, stencil, poster, spray, store, depot, wet, library, datacenter, and the twelve experiments</a>
<a href="{orch}?city=b5"><b>A CITY</b>?city=b1 to b7 for the Bolas cities; ?city=1 to 14 for the poem cities</a>
<a href="{orch}?city=b5&lens=watercolour"><b>A CITY THROUGH A LENS</b>?city=b5&amp;lens= and a paint or experiment name. Or press LENS on the card inside a city</a>
<a href="{orch}?city=b5&arch=reef"><b>A CITY IN ANOTHER SHAPE</b>&amp;arch= grid, shell, reef, amph, kelp, helix, wheel, comb, table</a>
<a href="{orch}?look=store"><b>THE ARCHIVE AS OBJECTS</b>The video store. Film tapes play; red tapes are doors to other worlds; yellow tapes are powers</a>
<a href="{orch}?look=ink&song=s27-two-rooms"><b>A SONG</b>&amp;song= and its id, or the songs menu</a></div></section>
<section id="objects"><h2><em>IDEA</em>The archive as things you use</h2><p class="say">The store is the first room where objects do something. Three kinds of tape are on its shelves now. The list after them is not built; it is where this could go.</p><div class="lens">
<a><b>BUILT · FILM TAPE</b>434 of them. Touch one and the televisions play that film; the caption opens it</a>
<a><b>BUILT · DOOR TAPE (RED)</b>31 of them. Touch one and you are in that world or city</a>
<a><b>BUILT · POWER TAPE (YELLOW)</b>7 of them: swerve, next and previous song, follow the odd one, video mode, record, pause</a>
<a><b>NOT BUILT · A CAN IN THE DEPOT</b>Take a can down and the orchestra plays over that film; put two on the bench and they are cut together</a>
<a><b>NOT BUILT · A JAR</b>Open a jar and that species joins the orchestra; close it and it leaves</a>
<a><b>NOT BUILT · A BOOK IN THE LIBRARY</b>Each book is a SCION swarm prompt; opening one changes how the room is built</a>
<a><b>NOT BUILT · A RACK IN THE DATA CENTER</b>Each rack is a setting: pull a drive to mute a lane, swap two to swap their sounds</a>
<a><b>NOT BUILT · A LATE FEE</b>Powers wear off. A lens you rented goes back on the shelf after sixteen bars</a>
<a><b>NOT BUILT · WALKING</b>You move down the aisle yourself and the orchestra follows you</a></div></section>
<section id="evolve"><h2><em>NEXT</em>How these evolve</h2><p class="say">Each world is one rule with one test. A world changes when its test fails, not when a new filter is available. What was tried and withdrawn is part of the record.</p><div class="lens">
<a><b>WITHDRAWN</b>Décollage and paste-up: five passes of cut-out collage as a filter over a moving picture. Unwatchable. Removed</a>
<a><b>WITHDRAWN</b>Ink as coloured boxes laid on top. Replaced by dye the animals leave behind, pulled along the film</a>
<a><b>WEAK NOW</b>Thick paint (pale), spray wall (pale), covers too small to read in the store</a>
<a><b>TO TRY · PAINT</b>Gouache cut shapes; oil pastel resist; monotype with ghost prints; cyanotype; marbling pulled by the bass; scratch-on-film (black leader, white line)</a>
<a><b>TO TRY · TIME</b>Paint that dries: bright when wet on the beat, dull four bars later. A page that is turned every section</a>
<a><b>TO TRY · PLACE</b>A projection booth; a record crate to flip through; a street to walk; an underwater ruin</a>
<a><b>HOW TO ASK</b>Send a picture and say which part is right: the colour, the edge, the motion or the place. One of those per world</a></div></section>
<section id="brief"><h2><em>REF</em>The brief</h2><p class="say">The first reference boards. They are pictures; the worlds above are the running thing, and they do not match these. Later references (ink on Super 8, an archive depot, specimen jars) are described in the worlds they led to.</p><div class="refs"><img src="{img}ref-city.jpg" alt="Film-strip towers with jellyfish between them, painted and torn" loading="lazy"><img src="{img}ref-cut.jpg" alt="A red, teal and cream poster of jellyfish and a film strip, the word CUT" loading="lazy"><img src="{img}ref-moon.jpg" alt="A moon jelly sprayed over a strip of film frames" loading="lazy"></div></section>
<footer>Stills were captured in a slow test renderer with the sound off. Motion and sound were not judged by the machine that made this page.</footer></body></html>'''
open(SRC + 'worlds.html', 'w').write(page('jellyorchestra.html', 'worlds/', '../fonts/fonts.css', '../', 'CONTAMINANT'))
B = (sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas') + '/worlds/'; os.makedirs(B + 'img', exist_ok=True)
open(B + 'index.html', 'w').write(page('../cities/', 'img/', '/contaminant-jelly/fonts/fonts.css', '../', 'CRASH LAB'))
for f in glob.glob(SRC + 'worlds/*.jpg'): shutil.copy(f, B + 'img/')
print('wrote worlds.html and', B + 'index.html', len(glob.glob(SRC + 'worlds/*.jpg')), 'images')
