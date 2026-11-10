# DRUM SCOUT: isolated hits in the catalog, by class. A hit must come out of quiet and die away with nothing else playing.
import json, numpy as np; from sig import *
D = json.load(open('scout.json')); src = {s['id']: s for s in D['sources']}; out = {}
def feat(c):
    x = load(c['src']); a = int(c['t0'] * SR); seg = x[a - 4410:a + int(.9 * SR)]; m = seg.mean(1); w = 441; n = len(m) // w; e = 20 * np.log10(np.sqrt((m[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)
    pk = int(np.argmax(e[8:20])) + 8; pre = e[:8].max(); peak = e[pk]; t20 = next((i for i in range(pk, n) if e[i] < peak - 20), n) - pk; t40 = next((i for i in range(pk, n) if e[i] < peak - 40), n) - pk; ef = np.maximum(e, peak - 45); bump = max(0, (ef[pk + 6:pk + 36] - np.minimum.accumulate(ef[pk:pk + 36])[6:]).max()) if n > pk + 7 else 0
    h = m[pk * w - 441:pk * w + 8820]; S = np.abs(np.fft.rfft(h * np.hanning(len(h)))) ** 2; f = np.fft.rfftfreq(len(h), 1 / SR); cen = (f * S).sum() / S.sum(); low = S[f < 120].sum() / S.sum(); hi = S[f > 5000].sum() / S.sum(); midb = S[(f > 150) & (f < 400)].sum() / S.sum()
    return dict(peak=round(float(peak), 1), iso=round(float(peak - pre), 1), t20=t20 * 10, t40=t40 * 10, bump=round(float(bump), 1), cen=round(float(cen)), low=round(float(low), 2), hi=round(float(hi), 2), body=round(float(midb), 2), clip=int((np.abs(seg) > .985).sum()), f0=round(float(f[np.argmax(S[:400])]), 1))
C = [c for c in D['candidates'] if c['role'] == 'attack' and c['rise_dB'] > 25 and c['src'] != 'S29988c']; print(len(C), 'isolated attacks')
F = []; R = {}; ERR = None
for c in C:
    try: ft = feat(c)
    except Exception as ex: R['err'] = R.get('err', 0) + 1; ERR = ex; continue
    for k, bad in (('clip', ft['clip']), ('bump', ft['bump'] > 8), ('iso', ft['iso'] < 20), ('quiet', ft['peak'] < -30)):
        if bad: R[k] = R.get(k, 0) + 1
    if ft['clip'] or ft['bump'] > 8 or ft['iso'] < 20 or ft['peak'] < -30: continue
    F.append({**{k: c[k] for k in ('src', 't0')}, **ft})
print(R, ERR, len(F))
cls = {'kick': lambda f: f['low'] > .5 and f['t40'] <= 600, 'snare': lambda f: 900 < f['cen'] < 5000 and f['low'] < .1 and 60 <= f['t20'] <= 250 and f['hi'] > .05, 'hat': lambda f: f['cen'] > 5500 and f['t20'] <= 120, 'perc': lambda f: 250 < f['cen'] <= 900 and f['low'] < .2 and f['t20'] <= 200}
for k, fn in cls.items():
    L = sorted([f for f in F if fn(f)], key=lambda f: -(f['iso'] + f['peak'])); keep = []; per = {}
    for f in L:
        if per.get(f['src'], 0) >= 2: continue
        per[f['src']] = per.get(f['src'], 0) + 1; keep.append(f)
    out[k] = keep[:8]; print('==', k, len(L)); [print('  ', f) for f in keep[:8]]
json.dump(out, open('kit.json', 'w'), indent=1)
