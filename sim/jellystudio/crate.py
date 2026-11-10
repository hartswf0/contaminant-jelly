# THE CRATE: one shared pool of exact cuts, chosen blind by measurement, used by every swarm song. More songs from fewer sounds; no synthesis.
import json, numpy as np, os, hashlib, random, wave; from sig import *
OUT = 'out3/crate'; os.makedirs(OUT, exist_ok=True); reg = {r['id']: r for r in json.load(open('registry2.json')) if r['status'] == 'decoded'}
A = json.load(open('scout.json'))['candidates']; B = json.load(open('scout2.json'))['candidates']; K = json.load(open('kit.json')); SL = {m['id']: m for m in json.load(open('blind_shortlist.json'))}; NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def wav_write(path, x): x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).round().astype('<i2').tobytes()); w.close()
def onset(src, a, b): x = load(src).mean(1)[int(a * SR):int(b * SR)]; e = np.sqrt(np.convolve(x ** 2, np.ones(441) / 441, 'same')); d = e[441:] - e[:-441]; return int(a * SR) + int(np.argmax(d)) + 60
def hard(src, t): x = np.abs(load(src)[int((t - .06) * SR):int((t + .2) * SR)]).max(1); return int((t - .06) * SR) + int(np.argmax(x > x.max() * .08)) - 32
CR = {}; usedsrc = {}
def add(role, src, s_in, s_out, why, perc=False, hp=0, lp=0, fin=.004, fout=.04):
    x = load(src); s_in = max(0, int(s_in)); s_out = min(len(x), int(s_out)); y = x[s_in:s_out].astype(np.float64)
    if (np.abs(y) > .985).sum() or len(y) < 1000: return None
    rms = 10 * np.log10((y ** 2).mean() + 1e-12); pk = 20 * np.log10(np.abs(y).max() + 1e-9)
    if rms < -52: return None
    m = signal.resample_poly(y.mean(1), 1, 2); fz, cf = (f0(m[len(m) // 4:len(m) // 4 + 8192]) if len(m) > 12000 else (0, 0)); nn = 12 * np.log2(fz / 440) + 69 if fz else 0
    trim = (-3 - pk) if perc else min(-20 - rms, -1.5 - pk); i = len([k for k in CR if k.startswith(role)]) + 1; name = '%s%d' % (role, i); wav_write('%s/%s.wav' % (OUT, name), y)
    CR[name] = {'role': role, 'source': src, 'source_hash': reg[src]['sha256'], 'sample_in': s_in, 'sample_out': s_out, 'source_rate': SR, 'seconds': round(len(y) / SR, 3), 'file': '../crate/%s.wav' % name, 'trim_dB': round(float(trim), 2), 'rms_dB': round(float(rms), 1), 'peak_dB': round(float(pk), 1), 'f0': round(float(fz), 1), 'midi': round(float(nn), 2), 'pitch_class': NOTE[int(round(nn)) % 12] if cf > .8 else '', 'periodicity': round(float(cf), 2), 'perc': perc, 'hp': hp, 'lp': lp, 'fades': {'in': int(fin * SR), 'out': int(fout * SR)}, 'why': why, 'blind': '%s %d' % (role.upper(), i), 'clip_sha256': hashlib.sha256(open('%s/%s.wav' % (OUT, name), 'rb').read()).hexdigest()}; usedsrc[src] = usedsrc.get(src, 0) + 1; return name
def top(cands, n, fn, per_src=1, key='score'):
    got = 0; seen = {}
    for c in sorted(cands, key=lambda c: -c[key]):
        if seen.get(c['src'], 0) >= per_src: continue
        if fn(c): seen[c['src']] = seen.get(c['src'], 0) + 1; got += 1
        if got >= n: break
# drums: hits that stand alone in the catalog
top(K['kick'], 4, lambda c: add('kick', c['src'], hard(c['src'], c['t0'] + .02), hard(c['src'], c['t0'] + .02) + int(.34 * SR), 'stands %.0f dB out of silence; %.0f Hz' % (c['iso'], c['f0']), True, fin=0, fout=.03), key='iso')
top(K['snare'], 3, lambda c: add('snare', c['src'], hard(c['src'], c['t0'] + .02), hard(c['src'], c['t0'] + .02) + int(.3 * SR), 'stands %.0f dB out of silence; centre %.0f Hz' % (c['iso'], c['cen']), True, hp=180, fin=0, fout=.03), key='iso')
top(K['hat'], 3, lambda c: add('hat', c['src'], hard(c['src'], c['t0'] + .02), hard(c['src'], c['t0'] + .02) + int(.12 * SR), 'stands %.0f dB out of silence; high-passed at 3 kHz so only its top is used' % c['iso'], True, hp=3000, fin=0, fout=.02), per_src=2, key='iso')
top(B['transient'], 5, lambda c: add('tick', c['src'], hard(c['src'], c['t0'] + .02), hard(c['src'], c['t0'] + .02) + int(.3 * SR), c['obs'], True, hp=250, fin=0, fout=.03))
# bass: low, steady, pitched notes
top([c for c in A if c['role'] == 'answer' and c['f0'] < 125 and c['low'] > .4 and c['periodicity'] >= .9], 4, lambda c: add('bass', c['src'], onset(c['src'], c['t0'] - .2, c['t0'] + .15), onset(c['src'], c['t0'] - .2, c['t0'] + .15) + int(1.4 * SR), 'a low note, %.0f Hz, periodicity %.2f' % (c['f0'], c['periodicity']), lp=500, fin=.006, fout=.08))
# phrases: loud, steady, pitched
top([c for c in A if c['role'] == 'answer' and 125 <= c['f0'] < 700 and c['periodicity'] >= .92 and c['low'] < .3 and c['src'] != 'S29988c'], 9, lambda c: add('phrase', c['src'], onset(c['src'], c['t0'] - .2, c['t0'] + .15), onset(c['src'], c['t0'] - .2, c['t0'] + .15) + int(min(c['t1'] - c['t0'] + .1, 2.6) * SR), 'a held pitch (%s, %.0f Hz), periodicity %.2f' % (c['pitch_class'], c['f0'], c['periodicity']), hp=120, fin=.008, fout=.08))
P = 'S29988c'; BARS = 147000
for a, L, why in ((10.12, BARS, 'the choir: D held three beats, then A'), (41.62, BARS, 'the choir: C, then G'), (107.66, 110250, 'the choir’s loudest, steadiest D'), (48.72, BARS, 'the choir: second take of D to A')): add('choir', P, int(a * SR), int(a * SR) + L, why, hp=120, fin=.015, fout=.08)
# voices and gestures
hs = next(i for i, r in reg.items() if 'HUNH' in r['path']); a = 2099831; add('call', hs, a, a + int(.42 * SR), 'context-led: taken as the grunt its title names', True, hp=120, fin=0, fout=.05)
top(B['breath'], 3, lambda c: add('breath', c['src'], onset(c['src'], c['t0'], c['t0'] + .2) - 100, onset(c['src'], c['t0'], c['t0'] + .2) - 100 + int(.55 * SR), c['obs'], True, hp=300, fin=.004, fout=.08))
for k in ('M01', 'M02'): m = SL[k]; add('glide', m['src'], m['sample_in'], m['sample_out'], m['obs'], hp=150, fin=.008, fout=.08)
for k in ('M03', 'M04'): m = SL[k]; add('hole', m['src'], m['sample_in'], m['sample_out'], m['obs'], hp=100, fin=.01, fout=.1)
def nobounce(c): y = load(c['src']).mean(1)[int(c['t0'] * SR):int(c['t1'] * SR)]; n = len(y) // 2205; e = 20 * np.log10(np.sqrt((y[:n * 2205].reshape(n, 2205) ** 2).mean(1)) + 1e-9); k = int(np.argmax(e)); return np.diff(e[k:]).max() < 4 if len(e) - k > 2 else False
top([c for c in B['decay'] if nobounce(c)], 4, lambda c: add('tail', c['src'], onset(c['src'], c['t0'] - .05, c['t0'] + .15), int(c['t1'] * SR) + int(.4 * SR), c['obs'], hp=100, fin=.003, fout=.3))
top(B['modulation'], 3, lambda c: add('bed', c['src'], int(c['t0'] * SR), int(c['t1'] * SR), c['obs'], hp=150, lp=7000, fin=.02, fout=.15))
top(B['evolving texture'], 3, lambda c: add('texture', c['src'], int(c['t0'] * SR), int(c['t1'] * SR), c['obs'], hp=200, fin=.05, fout=.4))
top(B['quiet'], 2, lambda c: add('quiet', c['src'], int(c['t0'] * SR), int(c['t1'] * SR), c['obs'], hp=150, fin=.02, fout=.15))
rnd = random.Random(38); ids = sorted(reg)
while len([k for k in CR if k.startswith('random')]) < 3:
    s = rnd.choice(ids); a = rnd.uniform(5, reg[s]['seconds'] - 10); add('random', s, int(a * SR), int((a + 2) * SR), 'a random draw: no test applied', hp=150, fin=.02, fout=.15)
# one room for everything: decaying noise, different in each ear, fixed seed
rng = np.random.default_rng(1400); n = int(1.4 * SR); t = np.arange(n) / SR; ir = np.stack([rng.standard_normal(n) * np.exp(-t / .28) for _ in (0, 1)], 1); ir = signal.sosfilt(signal.butter(2, [250, 6000], 'bandpass', fs=SR, output='sos'), ir, axis=0); ir /= np.sqrt((ir ** 2).sum(0)).max() * 1.0; wav_write(OUT + '/room.wav', ir * .5)
json.dump({'clips': CR, 'room': {'file': '../crate/room.wav', 'scale': .5, 'seed': 1400, 'seconds': 1.4}}, open(OUT + '/crate.json', 'w'), indent=1)
from collections import Counter; print(Counter(v['role'] for v in CR.values())); print(len(CR), 'clips from', len(usedsrc), 'sources;', round(sum(os.path.getsize(OUT + '/' + f) for f in os.listdir(OUT)) / 1e6, 1), 'MB')
for k, v in CR.items(): print(' %-9s %s %5.2fs rms %5.1f pk %5.1f trim %+5.1f %s %5.1fHz per %.2f' % (k, v['source'], v['seconds'], v['rms_dB'], v['peak_dB'], v['trim_dB'], v['pitch_class'] or '-', v['f0'], v['periodicity']))
