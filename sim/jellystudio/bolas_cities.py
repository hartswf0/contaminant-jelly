# THE BOLAS CITIES: every video in Bolas is a tower built of its own frames. Where a cut has an edit list that names its sources (97 do),
# its source clips stand on the same street as towers, and the cut's own tower has one floor per shot, in order: the jellies carry each shot across.
import json, os, glob, re, subprocess, hashlib, collections, numpy as np
from PIL import Image
B = '/home/user/bolas/'; OUT = '/home/user/contaminant-jelly/bonus/jellystudio/cities/'; TH = {x[:-4] for x in os.listdir('/home/user/hartswf0/cineosis-lab/lab/thumbs')}
cat = json.load(open(B + 'catalog.json')); CAT = {f['file']: f for f in cat['films']}
def dur(p):
    try: return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True, timeout=30).stdout.strip() or 0)
    except Exception: return 0
def frames(p, times):   # one small frame at each time
    out = []
    for t in times:
        r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.2f' % max(0, t), '-i', p, '-frames:v', '1', '-vf', 'scale=64:48', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, timeout=60).stdout
        out.append(np.frombuffer(r, np.uint8).reshape(48, 64, 3) if len(r) == 9216 else np.full((48, 64, 3), 24, np.uint8))
    return out
pretty = lambda p: re.sub(r'[-_]+', ' ', os.path.splitext(os.path.basename(p))[0]).strip().upper()
hcol = lambda s: '#%02x%02x%02x' % tuple(int(40 + (b % 60)) + (30, 14, 0)[i] for i, b in enumerate(hashlib.md5(s.encode()).digest()[:3]))
vids = sorted(glob.glob(B + '**/*.mp4', recursive=True) + glob.glob(B + '**/*.webm', recursive=True)); rel = lambda p: p[len(B):]
# cuts with named shots
CUTS = {}
for f in sorted(glob.glob(B + 'allways-argon/studio/manifests/*.json') + glob.glob(B + 'allways-argon/films/*/edl.json')):
    d = json.load(open(f)); e = (d.get('edl') if isinstance(d, dict) else d) or []; sh = [s for s in e if isinstance(s, dict) and s.get('clip_id')]
    if not sh: continue
    if isinstance(d, dict): v = os.path.normpath(os.path.join(os.path.dirname(f), '..', d.get('video_file') or '')); title = d.get('title') or pretty(f)
    else: slug = f.split('/')[-2]; v = B + 'allways-argon/films/%s/%s.mp4' % (slug, slug); title = pretty(slug)
    if not os.path.exists(v): v = next((p for p in vids if os.path.basename(p) == os.path.basename(v)), None)
    if v and v not in CUTS: CUTS[v] = {'title': re.split(r' — | - ', title)[0].upper(), 'shots': sh}
print(len(CUTS), 'cuts matched to a video;', sum(len(c['shots']) for c in CUTS.values()), 'shots')
CITY = [('b1', 'CRASH LAB', 'stacks', lambda p: p.startswith('media/') and not p.startswith('media/afterlight')), ('b2', 'AFTERLIGHT', 'orbit', lambda p: p.startswith('afterlight/') or p.startswith('media/afterlight')), ('b3', 'PAELEO', 'sea', lambda p: p.startswith('paeleo/')), ('b4', 'THIS SIDE UP', 'store', lambda p: p.startswith('this-side-up/')),
        ('b5', 'ALLWAYS · ARGON', 'moon', lambda p: p.startswith('allways-argon/')), ('b6', 'ALLWAYS · SOL', 'sea', lambda p: p.startswith('allways-sol/')), ('b7', 'ALLWAYS · SONNET, OPUS, TENSOR', 'stacks', lambda p: re.match(r'allways-(sonnet|opus|tensor|best)/', p))]
index = []
for n, title, setting, pred in CITY:
    vs = [p for p in vids if pred(rel(p))]; cells = []; towers = []; beats = []; nshots = 0
    def cell(fr): cells.append(fr); return len(cells) - 1
    cutv = [p for p in vs if p in CUTS]; rest = [p for p in vs if p not in CUTS]
    for b, p in enumerate(cutv):   # a street for each cut: its sources, and the film itself
        c = CUTS[p]; sh = c['shots']; fr = frames(p, [(s.get('start_sec') or 0) + (s.get('dur_s') or 2) / 2 for s in sh]); seq = []
        towers.append({'t': c['title'], 'y': 2026, 'b': b, 'p': '/bolas/' + rel(p), 'part': 0, 'film': 1, 'cut': 1, 's': [['f%d_%d' % (b, j), 2, '#3a2a18', '', cell(fr[j]), ''] for j in range(len(sh))]})
        bysrc = collections.OrderedDict()
        for j, s in enumerate(sh): bysrc.setdefault(s['source_title'], []).append((j, s))
        for st, lst in bysrc.items(): towers.append({'t': st, 'y': lst[0][1].get('source_year') or 0, 'b': b, 'p': lst[0][1].get('source_page') or '', 'part': 0, 'film': 0, 's': [['s%d_%d' % (b, j), 1 if s['clip_id'] in TH else 0, hcol(s['clip_id']), '', None, s['clip_id']] for j, s in lst]})
        beats.append({'t': c['title'], 'codes': [], 'seq': [['s%d_%d' % (b, j), 'f%d_%d' % (b, j)] for j in range(len(sh))], 'notes': [(s.get('phase') or '')[:60] for s in sh]}); nshots += len(sh)
    groups = collections.OrderedDict()
    for p in rest: groups.setdefault('/'.join(rel(p).split('/')[:3 if rel(p).count('/') > 2 else 2]), []).append(p)
    street = []; 
    for g, ps in groups.items():
        for p in ps:
            street.append((g, p))
    per = 8; nb0 = len(beats)
    for k in range(0, len(street), per):
        chunk = street[k:k + per]; b = nb0 + k // per; beats.append({'t': pretty(chunk[0][0].split('/')[-1]) if len({c[0] for c in chunk}) == 1 else '%s to %s' % (pretty(chunk[0][0].split('/')[-1]), pretty(chunk[-1][0].split('/')[-1])), 'codes': [], 'seq': []})
        for g, p in chunk:
            d = dur(p); nf = max(2, min(14, int(np.ceil(d / 8)))) if d else 2; budget = 1330 - len(cells) - 20
            if budget < nf: nf = max(0, budget)
            if nf == 0: continue
            fr = frames(p, [(i + .5) * d / nf for i in range(nf)]); ci = CAT.get(rel(p)); nm = (ci['title'] if ci else pretty(p)); towers.append({'t': nm, 'y': 2026, 'b': b, 'p': '/bolas/' + rel(p), 'part': 0, 'film': 1, 's': [['v%d_%d_%d' % (b, len(towers), i), 2, '#3a2a18', '', cell(fr[i]), ''] for i in range(nf)]})
    rows = int(np.ceil(len(cells) / 32)); A = np.zeros((rows * 48, 2048, 3), np.uint8) + 20
    for i, fr in enumerate(cells): A[(i // 32) * 48:(i // 32) * 48 + 48, (i % 32) * 64:(i % 32) * 64 + 64] = fr
    Image.fromarray(A).save(OUT + n + '.jpg', quality=82)
    nfl = sum(len(t['s']) for t in towers); nsrc = len({t['t'] for t in towers if not t.get('film')}); lines = ['%s is everything Bolas has made under that name: %d films, each a tower built of its own frames.' % (title.capitalize(), len(vs))]
    if cutv: lines += ['%d of them are cuts that kept a list of where every shot came from: %d shots from %d archive films.' % (len(cutv), nshots, nsrc), 'Each of those cuts has a street. Its sources stand along it, and its own tower is dark until the jellies have carried each shot across.']
    else: lines += ['None of them kept a list of its sources, so here the jellies can only look.']
    json.dump({'n': n, 'title': title, 'setting': setting, 'kind': 'bolas', 'atlas': n + '.jpg', 'baked': len(cells), 'lines': lines, 'beats': beats, 'towers': towers, 'shots': nfl, 'films': len(vs), 'cuts': len(cutv)}, open(OUT + 'c%s.json' % n, 'w'), separators=(',', ':'), ensure_ascii=False)
    index.append({'n': n, 'title': title, 'setting': setting, 'kind': 'bolas', 'shots': nfl, 'films': len(vs), 'streets': len(beats), 'towers': len(towers), 'cuts': len(cutv), 'cutshots': nshots, 'sources': nsrc, 'loans': 0}); print(index[-1], 'atlas cells', len(cells), flush=True)
old = json.load(open(OUT + 'index.json')); old['cities'] = index + [c for c in old['cities'] if c.get('kind') != 'bolas']; old['bolas'] = 'built from hartswf0/bolas: every mp4 and webm, and the edit lists under allways-argon'; json.dump(old, open(OUT + 'index.json', 'w'), indent=1, ensure_ascii=False)
print('videos', sum(c['films'] for c in index), 'of', len(vids))
