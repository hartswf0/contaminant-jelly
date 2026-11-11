# CITIES: every shot in the Cineosis Lab archive gets an address. A poem is a city; a scene of the poem is a street; a source film is a tower; a shot is a floor.
import json, collections, hashlib, os, re
D = json.load(open('lab-data.json')); S = [s for s in D['shots'] if 'wargames' not in (s.get('collections') or [])]; W = D['wygwyl']; OUT = '/home/user/contaminant-jelly/bonus/jellystudio/cities/'; os.makedirs(OUT, exist_ok=True)
SIGN = {s['n']: s for s in D['signs']}; beats = W['beats']; poems = W['films']; byb = collections.defaultdict(list); [byb[b['chapter']].append(b) for b in beats]; bidx = {b['id']: b for b in beats}
SET = ['sea', 'moon', 'stacks', 'store', 'orbit']; SETNAME = {'sea': 'an underwater data center', 'moon': 'a data center on the moon', 'stacks': 'a library of stacks', 'store': 'a video store the size of a city', 'orbit': 'a data center in orbit'}
films = collections.defaultdict(list); [films[s['title']].append(s) for s in S]
def city_of(title, shots):
    c = collections.Counter()
    for s in shots:
        for b in ((s.get('wygwyl') or {}).get('beats') or []):
            bb = bidx.get(b if not isinstance(b, dict) else b.get('id'))
            if bb: c[bb['chapter']] += 1
    return c.most_common(1)[0][0] if c else None
assign = {}; free = []
for t, sh in films.items():
    c = city_of(t, sh)
    if c is None: free.append(t)
    else: assign[t] = c
load = collections.Counter(); [load.__setitem__(c, load[c] + len(films[t])) for t, c in assign.items()]
for t in sorted(free, key=lambda t: -len(films[t])): c = min(range(14), key=lambda k: load[k]); assign[t] = c; load[c] += len(films[t])     # films no poem asked for fill the emptiest city: the stacks
index = []
for ci, p in enumerate(poems):
    bl = sorted(byb[ci], key=lambda b: b['start']); bpos = {b['id']: k for k, b in enumerate(bl)}; towers = []; nshots = nthumb = 0; years = []
    for t in sorted([t for t, c in assign.items() if c == ci], key=lambda t: -len(films[t])):
        sh = sorted(films[t], key=lambda s: (s.get('start') or 0)); c = collections.Counter()
        for s in sh:
            for b in ((s.get('wygwyl') or {}).get('beats') or []):
                bid = b if not isinstance(b, dict) else b.get('id')
                if bid in bpos: c[bpos[bid]] += 1
        blk = c.most_common(1)[0][0] if c else -1; yr = next((int(s['year']) for s in sh if str(s.get('year') or '').isdigit()), 0); pg = sh[0].get('page') or ''
        for part in range(0, len(sh), 36):
            fl = [[s['id'], 1 if str(s.get('thumb', '')).startswith('thumbs/') else 0, (s.get('palette') or ['#3a2a18'])[min(2, len(s.get('palette') or [1]) - 1)], (s.get('signs') or [{}])[0].get('n', '') if s.get('signs') else ''] for s in sh[part:part + 36]]
            towers.append({'t': t, 'y': yr, 'b': blk, 'p': pg if pg.startswith('http') else '', 'part': part // 36 + 1 if len(sh) > 36 else 0, 's': fl}); nshots += len(fl); nthumb += sum(f[1] for f in fl)
        if yr: years.append(yr)
    have = {f[0] for t in towers for f in t['s']}; byid = {s['id']: s for s in S}; loans = 0
    for k, b in enumerate(bl):   # a shot the cut chose that lives in another city is here on loan, as a one-floor tower on its street
        pid = b['a']['id']
        if pid not in have and pid in byid: s_ = byid[pid]; towers.append({'t': s_['title'], 'y': int(s_['year']) if str(s_.get('year') or '').isdigit() else 0, 'b': k, 'p': '', 'part': 0, 'loan': 1, 's': [[pid, 1 if str(s_.get('thumb', '')).startswith('thumbs/') else 0, (s_.get('palette') or ['#3a2a18'])[0], '']]}); have.add(pid); loans += 1
    for t in towers:
        if t['b'] < 0: continue
    tall = max(towers, key=lambda t: len(t['s'])); setting = SET[ci % 5]; nf = len({t['t'] for t in towers}); signs = collections.Counter(f[3] for t in towers for f in t['s'] if f[3]); top = signs.most_common(1)
    lines = ['%s is %s.' % (p['title'].capitalize(), SETNAME[setting]), 'It keeps %s shots from %d films. Every film is a tower, every shot a floor, every frame a window.' % (f'{nshots:,}', nf), 'Its %d streets are the scenes of the poem, in order: the first is “%s”.' % (len(bl), bl[0]['title'].split(';')[0]),
             'The tallest tower is %s%s: %d floors.' % (tall['t'], ' (%d)' % tall['y'] if tall['y'] else '', len(tall['s'])), 'Nothing in it is older than %d or newer than %d.' % (min(years), max(years)) if years else '', ('The sign most often read here is %s.' % SIGN[top[0][0]]['name'].lower()) if top else 'No one has read a sign here yet.']
    city = {'n': p['n'], 'title': p['title'], 'setting': setting, 'lines': [l for l in lines if l], 'beats': [{'t': b['title'], 'codes': b['codes'], 'pick': b['a']['id'], 'pt': b['a']['title'], 'py': b['a'].get('year') or 0} for b in bl], 'towers': towers, 'shots': nshots, 'thumbs': nthumb, 'films': nf, 'loans': loans}
    json.dump(city, open(OUT + 'c%s.json' % p['n'], 'w'), separators=(',', ':'), ensure_ascii=False); index.append({'n': p['n'], 'title': p['title'], 'setting': setting, 'shots': nshots, 'films': nf, 'streets': len(bl), 'towers': len(towers), 'loans': loans})
json.dump({'source': 'hartswf0/cineosis-lab lab/lab-data.json', 'excluded': 'the WarGames collection (a feature film, not archive footage): 302 shots', 'cities': index, 'signs': {k: {'name': v['name'], 'col': v['col'], 'row': v['row'], 'symbol': v['symbol']} for k, v in SIGN.items()}}, open(OUT + 'index.json', 'w'), indent=1, ensure_ascii=False)
for c in index: print(c)
print('total shots', sum(c['shots'] for c in index), 'of', len(S)); print(sum(os.path.getsize(OUT + f) for f in os.listdir(OUT)) // 1024, 'KB')
