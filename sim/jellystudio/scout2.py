# SCOUT (blind listening pass, by measurement): eight kinds of moment, a random draw, and a search for the quiet and awkward. Ids only: no names.
import json, numpy as np, sys, random, hashlib; from sig import *
reg = [r for r in json.load(open('registry2.json')) if r['status'] == 'decoded']; hop = 512 / 22050; C = {k: [] for k in ('transient', 'decay', 'negative space', 'unstable pitch', 'room tone', 'breath', 'modulation', 'evolving texture', 'quiet')}; INFO = {}
dup = {b for a, b, c in json.load(open('scout.json'))['near_duplicates']}
for r in reg:
    if r['id'] in dup: continue
    x = load(r['id']); m = mono22(x); n = len(m); f, t, S = stft(m); P = S ** 2; E = P.sum(0) + 1e-12; rms = 10 * np.log10(E / 2048 + 1e-12); L = np.log1p(30 * S); env = np.concatenate([[0], np.maximum(0, np.diff(L, axis=1)).sum(0)]); flux = env / (L.sum(0) + 1e-9); cen = (f[:, None] * P).sum(0) / E; flat = np.exp(np.log(P + 1e-12).mean(0)) / (P.mean(0) + 1e-12)
    loud = float(np.percentile(rms, 90)); dur = n / 22050; F = lambda a, b: slice(max(0, int(a / hop)), max(int(a / hop) + 1, int(b / hop))); INFO[r['id']] = {'loud': loud, 'dur': dur}
    inside = lambda a, b: a > 1.5 and b < dur - 4; clip = lambda a, b: int((np.abs(x[int(a * SR):int(b * SR)]) > .985).sum())
    step = 4096; pt = []
    for s in range(0, n - 8192, step):
        seg = m[s:s + 8192]; fz, cf = f0(seg); pt.append((12 * np.log2(fz / 440) + 69, cf, 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9), fz))
    pt = np.array(pt); ps = step / 22050
    def add(kind, a, b, score, obs):
        if inside(a, b) and not clip(a, b): C[kind].append({'src': r['id'], 't0': round(float(a), 3), 't1': round(float(b), 3), 'score': round(float(score), 2), 'obs': obs})
    pk, _ = signal.find_peaks(env, height=env.mean() + 3 * env.std(), distance=int(.3 / hop))
    for p in pk:
        a = float(t[p]); 
        if a < 2 or a > dur - 5: continue
        pre = rms[F(a - .2, a - .03)].mean(); hit = rms[F(a, a + .06)].max(); aft = rms[F(a + .25, a + .45)].mean(); c0 = float(cen[F(a, a + .08)].mean())
        if hit - pre > 14 and hit - aft > 10 and 300 < c0 < 4500 and hit > loud - 8: add('transient', a - .02, a + .45, (hit - pre) + (hit - aft), 'rises %.0f dB in under 50 ms, falls %.0f dB in 0.3 s; centre %.0f Hz' % (hit - pre, hit - aft, c0))
        seg = rms[F(a + .05, a + 2.6)]
        if len(seg) > 40 and seg[:4].mean() > loud - 8:
            k0 = seg[:4].mean(); below = np.where(seg < k0 - 25)[0]
            if len(below) and .6 <= below[0] * hop <= 2.4 and np.max(-np.diff(seg[:below[0] + 1])) < 7: add('decay', a - .02, a + below[0] * hop + .3, 25 / (below[0] * hop) + 10, 'falls 25 dB in %.2f s with no step over 7 dB; centre %.0f Hz' % (below[0] * hop, c0))
    q = rms < loud - 28; i = 0
    while i < len(q):
        if q[i]:
            j = i
            while j + 1 < len(q) and q[j + 1]: j += 1
            g = (j - i + 1) * hop; a, b = i * hop, (j + 1) * hop
            if .25 <= g <= 1.5 and a > 3 and b < dur - 6:
                bef = rms[F(a - .8, a - .05)].mean(); aft = rms[F(b + .02, b + .4)].mean()
                if bef > loud - 8 and aft > loud - 8: add('negative space', a - .8, b + .5, (loud - rms[i:j + 1].mean()) / 6 + (aft - rms[i:j + 1].mean()) / 10, 'a hole of %.2f s, %.0f dB down, with sound on both sides; the re-entry rises %.0f dB' % (g, loud - rms[i:j + 1].mean(), aft - rms[i:j + 1].mean()))
            i = j
        i += 1
    W = int(1.3 / ps)
    for s in range(0, len(pt) - W, 2):
        w = pt[s:s + W]
        if w[:, 1].min() < .82 or w[:, 2].mean() < loud - 16 + 20 * 0 - 12: continue
        d = np.diff(w[:, 0]); rng_ = w[:, 0].max() - w[:, 0].min()
        if 1.5 <= rng_ <= 7 and np.abs(d).max() < 1.2 and (np.all(d > -.15) or np.all(d < .15)): add('unstable pitch', s * ps, (s + W) * ps + .15, rng_ * w[:, 1].mean(), 'a glide of %.1f semitones (%.0f to %.0f Hz) in 1.3 s, periodic throughout (%.2f)' % (rng_, w[0, 3], w[-1, 3], w[:, 1].mean()))
    W = int(1.6 / hop)
    for s in range(int(2 / hop), len(rms) - W - int(4 / hop), W // 2):
        k = slice(s, s + W); lv = rms[k]
        if loud - 46 < lv.mean() < loud - 24 and lv.std() < 1.3 and lv.min() > -75 and flat[k].mean() > .02: add('room tone', s * hop, s * hop + 1.6, 10 - 4 * lv.std() + 20 * flat[k].mean(), 'steady to %.1f dB for 1.6 s, %.0f dB under the loud passages, noise-like (flatness %.2f): what is left in the room' % (lv.std(), loud - lv.mean(), flat[k].mean()))
        if loud - 34 < lv.mean() < loud - 18 and lv.std() < 2.2:
            pp = pt[int(s * hop / ps):int((s * hop + 1.6) / ps)]
            if len(pp) and pp[:, 1].mean() > .8: add('quiet', s * hop, s * hop + 1.6, pp[:, 1].mean(), 'quiet (%.0f dB under the loud passages) but pitched (periodicity %.2f): easy to pass over' % (loud - lv.mean(), pp[:, 1].mean()))
    W = int(.5 / hop)
    for s in range(int(2 / hop), len(rms) - W - int(4 / hop), W // 3):
        k = slice(s, s + W); a = s * hop
        if not (1200 < cen[k].mean() < 6500 and flat[k].mean() > .05 and rms[k].mean() > loud - 26): continue
        pre = rms[F(a - .35, a - .05)].mean(); aft = rms[F(a + .55, a + .85)].mean(); pp = pt[int(a / ps):int((a + .5) / ps) + 1]
        if rms[k].mean() - pre > 8 and rms[k].mean() - aft > 6 and len(pp) and pp[:, 1].mean() < .55: add('breath', a - .08, a + .62, (rms[k].mean() - pre) + 20 * flat[k].mean(), 'half a second of unpitched air (periodicity %.2f, centre %.0f Hz) standing %.0f dB above what comes before' % (pp[:, 1].mean(), cen[k].mean(), rms[k].mean() - pre))
    W = int(2.0 / hop)
    for s in range(int(2 / hop), len(rms) - W - int(4 / hop), W // 2):
        k = slice(s, s + W); lv = rms[k]
        if lv.mean() < loud - 12: continue
        e = lv - lv.mean(); ac = np.correlate(e, e, 'full')[len(e) - 1:]; ac = ac / (ac[0] + 1e-9); lo, hi = int(1 / 9 / hop), int(1 / 3 / hop); j = lo + int(np.argmax(ac[lo:hi])); pp = pt[int(s * hop / ps):int((s * hop + 2) / ps)]
        if ac[j] > .55 and lv.std() > 1.2 and len(pp) and pp[:, 1].mean() > .75 and flux[k].mean() < .12: add('modulation', s * hop, s * hop + 2, ac[j] * lv.std(), 'the level trembles %.1f times a second (depth %.1f dB) under a steady pitch' % (1 / (j * hop), 2 * lv.std()))
    W = int(4.0 / hop)
    for s in range(int(2 / hop), len(rms) - W - int(4 / hop), W // 3):
        k = slice(s, s + W); lv = rms[k]
        if lv.mean() < loud - 14 or lv.std() > 2.6: continue
        c = np.log(cen[k]); cs = np.convolve(c, np.ones(20) / 20, 'valid'); r_ = np.corrcoef(cs, np.arange(len(cs)))[0, 1]; ratio = np.exp(cs[-20:].mean() - cs[:20].mean())
        if abs(r_) > .9 and (ratio > 1.8 or ratio < .55): add('evolving texture', s * hop, s * hop + 4, abs(r_) * abs(np.log(ratio)), 'four seconds at a steady level while the brightness moves from %.0f to %.0f Hz' % (np.exp(cs[:20].mean()), np.exp(cs[-20:].mean())))
    print(r['id'], file=sys.stderr)
json.dump({'candidates': C, 'info': INFO}, open('scout2.json', 'w')); print({k: len(v) for k, v in C.items()})
