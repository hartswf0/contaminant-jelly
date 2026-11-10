# SIGNAL SCOUTS: four independent passes over every decoded source. They see ids and samples only: no titles, no catalog names.
import json, numpy as np, sys; from sig import *
reg = [r for r in json.load(open('registry.json')) if r['status'] == 'decoded']; C = []; FP = {}
PC = {'D': 2, 'A': 9, 'G': 7, 'C': 0}
for r in reg:
    x = load(r['id']); m = mono22(x); n = len(m); f, t, S = stft(m); hop = 512 / 22050; P = S ** 2; E = P.sum(0) + 1e-12
    rms = 10 * np.log10(E / 2048 + 1e-12); env = onset_env(S); low = P[f < 110].sum(0) / E; mid = P[(f >= 240) & (f <= 840)].sum(0) / E; cen = (f[:, None] * P).sum(0) / E
    flat = np.exp(np.log(P + 1e-12).mean(0)) / (P.mean(0) + 1e-12); flux = env / (np.log1p(30 * S).sum(0) + 1e-9)
    peak = float(np.abs(x).max()); clip = int((np.abs(x) > .985).sum()); bpm, bconf = tempo(env)
    # fingerprint: 12-band log-energy contour over the whole file, 64 time slices (for near-duplicates)
    bands = np.array([P[(f >= a) & (f < b)].sum(0) for a, b in zip(np.geomspace(60, 6000, 13)[:-1], np.geomspace(60, 6000, 13)[1:])]); sl = np.array_split(np.arange(bands.shape[1]), 64); fp = np.log1p(np.array([bands[:, s].mean(1) for s in sl]) * 1e3).ravel(); FP[r['id']] = (fp - fp.mean()) / (fp.std() + 1e-9)
    loud = np.percentile(rms, 90); r['bpm'] = round(bpm, 1); r['beat_conf'] = round(bconf, 2); r['peak'] = round(peak, 3); r['clipped_samples'] = clip; r['loud_dB'] = round(float(loud), 1)
    T = lambda k: float(t[k]); F = lambda a, b: slice(int(a / hop), max(int(a / hop) + 1, int(b / hop)))
    ok = lambda a, b: a > 1.0 and b < n / 22050 - 3.0     # not the file's own fade-in or fade-out
    # 1 ATTACK: a strong onset out of quiet, short, not clipped
    pk, _ = signal.find_peaks(env, height=env.mean() + 3 * env.std(), distance=int(.25 / hop))
    for p in pk:
        a = T(p); 
        if not ok(a, a + .6): continue
        pre = rms[F(a - .18, a - .03)].mean(); hit = rms[F(a, a + .06)].max(); after = rms[F(a + .25, a + .45)].mean(); rise = hit - pre; dec = hit - after
        if rise > 9 and dec > 6 and hit > loud - 8: C.append({'role': 'attack', 'src': r['id'], 't0': round(a - .02, 3), 't1': round(a + .5, 3), 'score': round(float(rise + dec), 1), 'rise_dB': round(float(rise), 1), 'decay_dB': round(float(dec), 1), 'centroid': round(float(cen[F(a, a + .08)].mean())), 'low': round(float(low[F(a, a + .15)].mean()), 2), 'mid': round(float(mid[F(a, a + .3)].mean()), 2)})
    # 2 BED: 3.3 s (one bar) of steady level and low flux
    W = int(3.333 / hop)
    for s in range(int(1 / hop), len(rms) - W - int(3 / hop), W // 2):
        k = slice(s, s + W); lv = rms[k]
        if lv.mean() < loud - 14 or lv.std() > 2.2: continue
        C.append({'role': 'bed', 'src': r['id'], 't0': round(T(s), 3), 't1': round(T(s) + 3.333, 3), 'score': round(float(30 - 4 * lv.std() - 60 * flux[k].mean()), 1), 'level_sd_dB': round(float(lv.std()), 2), 'flux': round(float(flux[k].mean()), 3), 'centroid': round(float(cen[k].mean())), 'low': round(float(low[k].mean()), 2), 'mid': round(float(mid[k].mean()), 2), 'flat': round(float(flat[k].mean()), 3)})
    # 3 PITCH-STABLE PHRASE: >= 1.25 s on one pitch class (so it can answer in the sample's own key)
    step = 5512; pcs = []
    for s in range(0, n - 8192, step):
        seg = m[s:s + 8192]; fz, cf = f0(seg); lv = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9); nn = 12 * np.log2(fz / 440) + 69; pcs.append((int(round(nn)) % 12 if cf > .8 and lv > loud - 20 + 0 else -1, cf, abs(nn - round(nn)), fz))
    i = 0
    while i < len(pcs):
        j = i
        while j + 1 < len(pcs) and pcs[j + 1][0] == pcs[i][0]: j += 1
        if pcs[i][0] >= 0 and j - i >= 4:
            a, b = i * step / 22050, (j + 1) * step / 22050 + .12
            if ok(a, b):
                pcn = [k for k, v in PC.items() if v == pcs[i][0]]; cf = np.mean([q[1] for q in pcs[i:j + 1]]); k = F(a, b)
                C.append({'role': 'answer', 'src': r['id'], 't0': round(a, 3), 't1': round(min(b, a + 3.333), 3), 'score': round(float(10 * cf + min(b - a, 3.3) + (4 if pcn else 0) - 6 * mid[k].mean()), 1), 'pitch_class': ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][pcs[i][0]], 'f0': round(float(np.median([q[3] for q in pcs[i:j + 1]])), 1), 'cents_off': round(float(100 * np.mean([q[2] for q in pcs[i:j + 1]]))), 'periodicity': round(float(cf), 2), 'in_key': bool(pcn), 'centroid': round(float(cen[k].mean())), 'low': round(float(low[k].mean()), 2), 'mid': round(float(mid[k].mean()), 2)})
        i = j + 1
    # 4 TAIL: after an onset, a smooth fall of 18 dB or more inside the file (not the final fade)
    for p in pk:
        a = T(p)
        if not ok(a, a + 2.5): continue
        seg = rms[F(a + .05, a + 2.5)]; 
        if len(seg) < 20: continue
        drop = seg[:4].mean() - seg[-8:].mean(); mono = np.mean(np.diff(seg) < 1.0)
        if drop > 18 and mono > .9 and seg[:4].mean() > loud - 8: C.append({'role': 'tail', 'src': r['id'], 't0': round(a - .02, 3), 't1': round(a + 2.5, 3), 'score': round(float(drop * mono), 1), 'drop_dB': round(float(drop), 1), 'smooth': round(float(mono), 2), 'centroid': round(float(cen[F(a, a + 1)].mean())), 'low': round(float(low[F(a, a + 1)].mean()), 2), 'mid': round(float(mid[F(a, a + 1)].mean()), 2)})
    print(r['id'], r['seconds'], r['bpm'], r['beat_conf'], 'peak', r['peak'], 'clip', clip, file=sys.stderr)
ids = list(FP); near = []
for i in range(len(ids)):
    for j in range(i + 1, len(ids)):
        c = float((FP[ids[i]] * FP[ids[j]]).mean())
        if c > .9: near.append([ids[i], ids[j], round(c, 3)])
json.dump({'sources': reg, 'near_duplicates': near, 'candidates': C}, open('scout.json', 'w'))
from collections import Counter; print(Counter(c['role'] for c in C), 'near-dups', near)
