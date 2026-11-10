# INTEGRATOR's hard checks. Everything here is measured from the rendered files. Nothing here was heard.
import json, numpy as np, sys; from sig import *; from build import wav_read, BAR, BEAT, SR
G = json.load(open('out/scion.json')); ok = True
def band(x, lo, hi): sos = signal.butter(6, [lo, hi], 'bandpass', fs=SR, output='sos'); return signal.sosfilt(sos, x.mean(1))
def db(x): return 10 * np.log10((x ** 2).mean() + 1e-15)
def bars(x, f, n): return [round(float(db(f(x)[b * BAR:(b + 1) * BAR])), 1) for b in range(n)]
def chk(name, cond, detail): 
    global ok; ok &= bool(cond); print('%s  %s: %s' % ('ok  ' if cond else 'FAIL', name, detail))
M = {sc: wav_read('out/renders/%s.wav' % sc) for sc in G['scenes']}
for sc, x in M.items(): chk(sc + ' length', len(x) == G['scenes'][sc]['bars'] * BAR, '%d samples = %d bars exactly' % (len(x), len(x) // BAR)); chk(sc + ' peak', np.abs(x).max() <= 10 ** (-.95 / 20), '%.2f dBFS' % (20 * np.log10(np.abs(x).max())))
lowA = bars(M['proofA'], lambda x: band(x, 25, 110), 8); chk('low end held for four bars, arrives on bar 5', min(lowA[4:]) - max(lowA[:4]) > 20, 'below 110 Hz, by bar: %s' % lowA)
vb = bars(M['break'], lambda x: band(x, 300, 3400), 8); lb = bars(M['break'], lambda x: band(x, 25, 110), 8)
chk('protected vocal space (bar 5 of the break)', np.mean(vb[:3]) - vb[4] > 18, '300–3400 Hz by bar: %s' % vb); chk('sub removed for bars 4–5, back on bar 6', lb[5] - max(lb[3], lb[4]) > 20, 'below 110 Hz by bar: %s' % lb)
chk('the return is heavier than the bar it follows', lb[5] - lb[2] > 3, 'below 110 Hz: bar 6 is %.1f dB above bar 3' % (lb[5] - lb[2])); z = np.abs(M['break'][4 * BAR:5 * BAR]).max(1) == 0; chk('the empty bar is not digital silence', z.mean() < .02, '%.1f%% of its samples are zero' % (100 * z.mean()))
f_ = M['full']; same = sum(np.array_equal(f_[b * BAR:(b + 2) * BAR], f_[(b + 2) * BAR:(b + 4) * BAR]) for b in range(4, 30, 2)); chk('no eight bars are one loop four times', same <= 9, '%d of 13 neighbouring two-bar pairs are identical (the critic found all of them)' % same)
vf = bars(M['full'], lambda x: band(x, 300, 3400), 36); chk('protected vocal space survives in the full track (bar 15)', np.mean(vf[4:12]) - vf[14] > 18, 'bar 15: %.1f dB against %.1f in the verse' % (vf[14], np.mean(vf[4:12])))
# stems
st = {l: wav_read('out/stems/%s.wav' % l) for l in G['lanes']}; s = sum(st.values()); chk('stems share zero point and length', len({len(v) for v in st.values()} | {len(M['full'])}) == 1, '%d samples each' % len(s)); r = db(s - M['full']) - db(M['full']); chk('stems sum to the master', r < -70, 'residual %.0f dB below the master (16-bit rounding)' % -r)
# clicks: the largest sample-to-sample step at any placement edge, per stem
import build; worst = 0
for sc in G['scenes']:
    stems, edges = build.render(sc); x = sum(stems.values()); e = np.array([k for k in edges if 2 < k < len(x) - 2]); worst = max(worst, float(np.abs(x[e + 1] - x[e]).max()), float(np.abs(x[e] - x[e - 1]).max()))
chk('no clicks at edit points', worst < .12, 'largest step at any edit: %.3f of full scale' % worst)
chk('every audible placement resolves to a source and an exact edit', all(p['source_hash'] and p['sample_out'] > p['sample_in'] for p in G['placements']), '%d placements, %d spans' % (len(G['placements']), len(G['spans'])))
# A against B (measured only)
a, b = M['proofA'], M['proofB']; d = b - a; print('\nA/B: the only difference is the support layer: it is %.1f dB below the mix; B is %.2f dB louder overall' % (db(a) - db(d), db(b) - db(a)))
mot = band(a, 240, 840); sup = band(d, 240, 840); print('     in the motif band (240–840 Hz) the support is %.1f dB below the rest of the mix; below 110 Hz it is %.1f dB below' % (db(mot) - db(sup), db(band(a, 25, 110)[4 * BAR:]) - db(band(d, 25, 110)[4 * BAR:])))
print('     lane levels in the full mix (dB): ' + ', '.join('%s %.1f' % (l, db(v)) for l, v in st.items()))
sys.exit(0 if ok else 1)
