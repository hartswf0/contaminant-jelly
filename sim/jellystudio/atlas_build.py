# Writes bonus/atlas.html: every place, game, level, jar and tool on the site, on one shelf.
# The lists of the eleven games, the archive levels and the bonus pieces are taken from index.html, so the atlas cannot drift from the main page.
import re, io, os, glob, json
C = '/home/user/contaminant-jelly/'
ix = io.open(C + 'index.html', encoding='utf-8').read()
def arr(name):
    m = re.search(r'const %s = (\[\[.*?\]\]);' % name, ix, re.S); assert m, name; return m.group(1)
J, A, B = arr('J'), arr('A'), arr('B')
inB = set(re.findall(r"'bonus/([a-z0-9]+\.html)'", B)) | {'atlas.html'}
rest = []
for f in sorted(glob.glob(C + 'bonus/*.html')):
    n = os.path.basename(f)
    if n in inB: continue
    t = re.search(r'<title>([^<·]*)', io.open(f, encoding='utf-8', errors='ignore').read()); rest.append([n, (t.group(1).strip() if t else n)])
pics = [os.path.basename(p)[6:-4] for p in glob.glob(C + 'current/drift/play/bonus-*.jpg')]
html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>The Atlas · CONTAMINANT</title><link rel="stylesheet" href="../fonts/fonts.css">
<style>
:root{--ink:#e8e4da;--dim:rgba(232,228,218,.6);--line:rgba(232,228,218,.3);--bg:#07090a}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:300 14px/1.4 Jost,system-ui,sans-serif}
main{max-width:1000px;margin:0 auto;padding:max(18px,env(safe-area-inset-top)) max(16px,4vw) 80px}
.k{font:400 10px 'JetBrains Mono',monospace;letter-spacing:.32em;color:var(--dim)}h1{margin:5px 0 0;font:italic 400 clamp(28px,6vw,44px)/1 'Cormorant Garamond',Georgia,serif}main>p{margin:6px 0 14px;max-width:56ch;font:italic 16px/1.35 'Cormorant Garamond',Georgia,serif;color:var(--dim)}
#q{width:100%;max-width:520px;font:italic 20px 'Cormorant Garamond',Georgia,serif;color:#fff;background:transparent;border:0;border-bottom:1px solid var(--line);outline:0;padding:6px 2px}
#nav{display:flex;flex-wrap:wrap;gap:6px 14px;margin:14px 0 4px}#nav a{font:400 9px 'JetBrains Mono',monospace;letter-spacing:.22em;color:var(--dim);text-decoration:none;border-bottom:1px solid var(--line);padding:3px 0}
h2{margin:30px 0 2px;font:400 11px 'JetBrains Mono',monospace;letter-spacing:.3em}h2 i{font:italic 15px 'Cormorant Garamond',Georgia,serif;letter-spacing:0;color:var(--dim);margin-left:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-top:10px}
.it{display:flex;gap:10px;align-items:flex-start;padding:8px;border:1px solid rgba(232,228,218,.16);min-height:66px}.it img,.it .sym{flex:0 0 64px;width:64px;height:48px;object-fit:cover;background:#0f1214}.it .sym{display:flex;align-items:center;justify-content:center;font:400 15px 'JetBrains Mono',monospace;color:var(--dim)}
.it b{display:block;font:400 15px/1.15 'Cormorant Garamond',Georgia,serif}.it i{display:block;font:italic 13px/1.2 'Cormorant Garamond',Georgia,serif;color:var(--dim);margin:1px 0 5px}
.it a{display:inline-block;margin:0 8px 2px 0;font:400 9px 'JetBrains Mono',monospace;letter-spacing:.2em;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line);padding:2px 0}.it a.w{color:#f2e2b8}
#none{display:none;margin-top:20px;font:italic 16px 'Cormorant Garamond',Georgia,serif;color:var(--dim)}
</style></head><body><main>
<div class="k">CONTAMINANT · THE ATLAS</div><h1>Everything, on one shelf.</h1>
<p>Every place, game, level and jar that has been built here. OPEN goes in alone and quiet. WITH FRIENDS opens a room there and gives you its link.</p>
<input id="q" placeholder="find a place, a game, a film, a sign" autocomplete="off" spellcheck="false"><div id="nav"></div><div id="all"></div><div id="none">Nothing here by that name.</div>
</main>
<script type="module">
const J = __J__, A = __A__, B = __B__, REST = __REST__, PICS = __PICS__;
const $ = id => document.getElementById(id), esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])), O = 'jellyorchestra.html', cap = s => String(s).toLowerCase().replace(/(^|\s|-)([a-z])/g, (m, a, b) => a + b.toUpperCase());
const S = [];   // sections: [id, title, line, items]; an item is {n: name, l: line, img, sym, links: [[label, href, friends?]]}
S.push(['start', 'START HERE', 'the rooms you can be a jelly in', [
  {n: 'The Blank Room', l: 'an empty room and one jelly: set things down, shape clay, record it', img: 'worlds/blank.jpg', links: [['OPEN', O + '?alone=1&look=blank'], ['WITH FRIENDS', O + '?alone=1&look=blank', 1]]},
  {n: 'The Range', l: 'a mountain range under water; the rock is solid; find things by ping', img: 'worlds/range.jpg', links: [['OPEN', O + '?alone=1&look=range'], ['WITH FRIENDS', O + '?alone=1&look=range', 1]]},
  {n: 'The Orchestra', l: 'fifty jellies play the song around you', img: 'worlds/deep.jpg', links: [['OPEN', O + '?alone=0&music=1'], ['WITH FRIENDS', O + '?alone=0&music=1', 1]]},
  {n: 'Bring the Reels Home', l: 'six doors, a reel behind each; reels are shared with friends in the room', img: 'worlds/chorus.jpg', links: [['OPEN', O + '?game=1'], ['WITH FRIENDS', O + '?game=1', 1]]},
  {n: 'Talk', l: 'say a line; jellies say it in other languages; a room for up to eight', img: 'worlds/chorus.jpg', links: [['OPEN', O + '?talk=1']]},
  {n: 'Theatre', l: 'sit back: every place and every look, sixteen bars each', img: 'worlds/silhouette.jpg', links: [['OPEN', O + '?theatre=1&music=1']]},
  {n: 'The Video Store', l: 'shelves of films; choose one under PLAY, FILMS', img: 'worlds/store.jpg', links: [['OPEN', O + '?alone=1&look=store&films=1'], ['WITH FRIENDS', O + '?alone=1&look=store', 1]]}]]);
S.push(['make', 'MAKE AND CHOOSE', 'tools', [
  {n: 'The Loadout', l: 'every decision in a jar, with the real thing running above', sym: 'LO', links: [['OPEN', 'loadout.html']]},
  {n: 'The Jelly Maker', l: 'make your own jelly: a shader with dials and one line you write', sym: 'MK', links: [['OPEN', 'jellymaker.html']]},
  {n: 'The Jar Experiments', l: 'mountain, cube, plate, sound in a room, clay', sym: 'JR', links: [['OPEN', 'jars.html'], ...['mountain', 'cube', 'plate', 'room', 'clay'].map(k => [k.toUpperCase(), 'jars.html?jar=' + k])]},
  {n: 'The Voice Lab', l: 'a jelly whose bell is its throat; make its voice better by ear', sym: 'VL', links: [['OPEN', 'voicelab.html']]}]]);
S.push(['games', 'THE ELEVEN GAMES', 'each video became a game', J.map(([id, v, t, l, th]) => ({n: t, l, img: `../current/drift/thumbs/${th}.jpg`, links: [['PLAY', `../current/drift/?v=${id}`]]}))]);
S.push(['archive', 'THE ARCHIVE LEVELS', 'the same water, filled from other collections', A.map(([id, t, l]) => ({n: t, l, sym: t.replace(/^The /, '').slice(0, 2).toUpperCase(), links: [['PLAY', `../current/drift/?v=${id}`]]}))]);
S.push(['bonus', 'BONUS PIECES', 'sketches from the same water', [...B.map(([id, t, l, h]) => ({n: t, l, img: PICS.includes(id) ? `../current/drift/play/bonus-${id}.jpg` : '', sym: t.replace(/^The /, '').slice(0, 2).toUpperCase(), links: [['OPEN', '../' + h]]})), ...REST.filter(r => !['loadout.html', 'jellymaker.html', 'jars.html', 'voicelab.html'].includes(r[0])).map(([f, t]) => ({n: t, l: f, sym: t.replace(/^The /, '').slice(0, 2).toUpperCase(), links: [['OPEN', f]]}))]]);
const draw = () => { const q = $('q').value.trim().toLowerCase(); let n = 0; $('all').innerHTML = S.map(([id, t, line, items]) => { const its = items.filter(i => !q || (i.n + ' ' + i.l + ' ' + t).toLowerCase().includes(q)); n += its.length; return its.length ? `<h2 id="${id}">${t}<i>${esc(line)} · ${its.length}</i></h2><div class="grid">${its.map(i => `<div class="it">${i.img ? `<img loading="lazy" alt="" src="${esc(i.img)}">` : `<span class="sym">${esc(i.sym || '')}</span>`}<div><b>${esc(i.n)}</b><i>${esc(i.l)}</i>${i.links.map(([lab, h, fr]) => `<a class="${fr ? 'w' : ''}" href="${esc(h)}"${fr ? ' data-fr="1"' : ''}>${lab}</a>`).join('')}</div></div>`).join('')}</div>` : ''; }).join(''); $('none').style.display = n ? 'none' : 'block'; $('nav').innerHTML = q ? '' : S.map(([id, t, , items]) => `<a href="#${id}">${t} · ${items.length}</a>`).join(''); };
$('q').oninput = draw; $('all').onclick = e => { const a = e.target.closest('a[data-fr]'); if (!a) return; e.preventDefault(); location.href = a.getAttribute('href') + '&meet=' + Math.random().toString(36).slice(2, 8); };   /* WITH FRIENDS: a new room, in that place; its link is under FRIENDS once inside */
draw(); window.__atlas = {S, draw};
fetch('worlds/worlds.json').then(r => r.json()).then(W => { const P = W.looks.filter(l => !l.street && !['blank', 'range'].includes(l.id)), mk = l => { const q = l.city ? 'city=' + l.city : 'look=' + l.id; return {n: cap(l.name), l: l.own || l.rule || '', img: `worlds/${l.id}.jpg`, links: [['OPEN', O + '?alone=1&' + q], ['WITH ORCHESTRA', O + '?alone=0&music=1&' + q], ['WITH FRIENDS', O + '?alone=1&' + q, 1]]}; };
  S.splice(2, 0, ['places', 'PLACES', 'every world that has been built', P.filter(l => !l.city).map(mk)], ['cities', 'CITIES OF FILM', 'the archive as cities', P.filter(l => l.city).map(mk)], ['paints', 'PAINTS', 'the same room seen through a paint or a print', W.looks.filter(l => l.street).map(l => ({n: cap(l.name), l: l.own || '', img: `worlds/${l.id}.jpg`, links: [['OPEN', O + '?alone=1&look=deep&lens=' + l.id], ['ON THE RANGE', O + '?alone=1&look=range&lens=' + l.id]]}))]); draw(); }).catch(() => {});
fetch('../labels/cineosis/index.json').then(r => r.json()).then(IX => { S.push(['signs', 'THE PERIODIC TABLE', 'forty-five signs and sixteen types; each is a level', IX.filter(j => j.kind === 'type' || j.kind === 'sign').map(j => ({n: j.name, l: j.kind === 'type' ? 'a type: every shot of its signs' : String(j.question || '').slice(0, 110), sym: j.symbol || j.mark || 'T', links: [['PLAY', `../current/drift/?v=${j.kind === 'type' ? 'type-' + String(j.file).slice(8) : 'sign-' + j.id}`]]}))]); draw(); }).catch(() => {});
</script><script src="jellyfilm.js"></script></body></html>
'''
html = html.replace('__J__', J).replace('__A__', A).replace('__B__', B).replace('__REST__', json.dumps(rest)).replace('__PICS__', json.dumps(pics))
io.open(C + 'bonus/atlas.html', 'w', encoding='utf-8').write(html)
print('wrote bonus/atlas.html', len(html) // 1024, 'KB;', len(rest), 'other bonus pages;', len(pics), 'bonus pictures')
