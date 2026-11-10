# The capped audition: 12 blind interval cards. Frozen (hashed) before any name is revealed.
import json, random, hashlib, numpy as np; from sig import *
D = json.load(open('scout2.json')); C = D['candidates']; reg = {r['id']: r for r in json.load(open('registry2.json')) if r['status'] == 'decoded'}; new = {i for i, r in reg.items() if r['catalog'].startswith('forage:')}
USE = {'transient': 'a percussion voice: something to move across the barline', 'decay': 'a tail: something to leave ringing across a dropout', 'negative space': 'a ready-made stop: the hole can become the place for a voice', 'unstable pitch': 'a lead that will not sit still: a hook, or a transition', 'breath': 'a human-scale event to stand where a snare would', 'modulation': 'a bed that already moves, so the drums can be sparse', 'evolving texture': 'a long cycle to run shorter loops against', 'quiet': 'an event that only works if everything else gets out of the way', 'random draw': 'unknown: drawn, not chosen'}
def env(c, w=2205): y = load(c['src']).mean(1)[int((c['t0'] - .3) * SR):int((c['t1'] + .3) * SR)]; n = len(y) // w; return 20 * np.log10(np.sqrt((y[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)
pick = []; used = set()
def take(kind, n=1):
    got = 0
    for c in sorted(C[kind], key=lambda c: -c['score']):
        if c['src'] in used or c['src'] in ('S29988c', 'Sd3ac86'): continue
        e = env(c); body = e[6:-6]
        if body.max() < (-52 if kind == 'quiet' else -34) or (kind != 'negative space' and (body.max() - body.min() > 60)): continue   # reject near-silence and cuts to digital zero
        if kind == 'decay' and np.diff(body[int(np.argmax(body)):]).max() > 4: continue   # a decay must not bounce: the first pick was a kick pattern

        pick.append({**c, 'kind': kind}); used.add(c['src']); got += 1
        if got == n: return
take('unstable pitch', 2); take('negative space', 2)
for k in ('transient', 'decay', 'breath', 'modulation', 'evolving texture'): take(k)
take('quiet', 2)
rnd = random.Random(72)
while len(pick) < 12:
    s = rnd.choice(sorted(reg)); 
    if s in used: continue
    a = rnd.uniform(5, D['info'].get(s, {'dur': reg[s]['seconds']})['dur'] - 10); c = {'src': s, 't0': round(a, 3), 't1': round(a + 2, 3), 'score': 0, 'obs': 'no test applied', 'kind': 'random draw'}
    if env(c).max() > -40: pick.append(c); used.add(s)
for i, c in enumerate(pick): c['id'] = 'M%02d' % (i + 1); c['sample_in'] = int(round(c['t0'] * SR)); c['sample_out'] = int(round(c['t1'] * SR)); c['source_rate'] = SR; c['context'] = [c['sample_in'] - 2 * SR, c['sample_out'] + 2 * SR]; c['use'] = USE[c['kind']]; c['source_hash'] = reg[c['src']]['sha256']; c['status'] = 'provisional: located by measurement, not heard'
body = json.dumps(pick, indent=1); open('blind_shortlist.json', 'w').write(body); print('frozen sha256', hashlib.sha256(body.encode()).hexdigest()[:16], '| from the new draw:', sum(c['src'] in new for c in pick), 'of', len(pick))
for c in pick: e = env(c); print(c['id'], c['kind'], c['src'], '%.2f–%.2f' % (c['t0'], c['t1']), '|', c['obs'], '\n     ', ' '.join('%.0f' % v for v in e[::2]))
