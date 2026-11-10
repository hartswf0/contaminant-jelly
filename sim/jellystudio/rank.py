# AUDITION QUEUE: collapse near-duplicates, then test each survivor against the primary motif (masking), still blind to labels.
import json, numpy as np; from sig import *
D = json.load(open('scout.json')); src = {s['id']: s for s in D['sources']}; PRIM = 'S29988c'
dupof = {}
for a, b, c in D['near_duplicates']: dupof.setdefault(b, a)
xp = load(PRIM); mot = mono22(xp[int(10.0 * SR):int(13.333 * SR)]); fm, tm, Sm = stft(mot); Pm = (Sm ** 2).mean(1); Pm /= Pm.sum()
def mask(c):   # share of the candidate's energy that falls where the motif's energy is (0 = clear of it, 1 = on top of it)
    x = load(c['src']); seg = mono22(x[int(c['t0'] * SR):int(c['t1'] * SR)]); f, t, S = stft(seg); P = (S ** 2).mean(1); P /= P.sum() + 1e-12; return float(np.minimum(P, Pm).sum())
out = {}
for role in ['attack', 'answer', 'bed', 'tail']:
    cs = [c for c in D['candidates'] if c['role'] == role and c['src'] != PRIM and src[c['src']]['clipped_samples'] < 20 and c['src'] not in dupof]
    if role == 'answer': cs = [c for c in cs if c['in_key'] and c['cents_off'] < 25]
    cs.sort(key=lambda c: -c['score']); keep = []; per = {}
    for c in cs:
        if per.get(c['src'], 0) >= 2: continue
        if any(k['src'] == c['src'] and abs(k['t0'] - c['t0']) < 4 for k in keep): continue
        per[c['src']] = per.get(c['src'], 0) + 1; keep.append(c)
        if len(keep) >= 14: break
    for c in keep: c['masking'] = round(mask(c), 2); c['fit'] = round(c['score'] * (1 - c['masking']), 1)
    keep.sort(key=lambda c: -c['fit']); out[role] = keep[:8]
    print('==', role, len(cs), 'after rejects →', len(keep), 'auditioned'); 
    for i, c in enumerate(keep[:8]): print(' %s%d' % (role[0].upper(), i + 1), {k: v for k, v in c.items() if k not in ('role',)})
json.dump(out, open('shortlist.json', 'w'), indent=1)
print('rejected for clipping:', [s['id'] for s in D['sources'] if s['clipped_samples'] >= 20])
