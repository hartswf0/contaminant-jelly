# BUILDERS + INTEGRATOR: spans -> placements -> renders. Source time is in samples; arrangement time is bar/beat at 72 BPM (one beat = 36,750 samples exactly).
import json, numpy as np, hashlib, os, wave, subprocess, sys; from sig import *
BEAT = 36750; BAR = 4 * BEAT; OUT = 'out'; [os.makedirs(OUT + '/' + d, exist_ok=True) for d in ('clips', 'renders', 'stems')]
reg = {r['id']: r for r in json.load(open('registry.json')) if r.get('status') == 'decoded'}; PRIM, SUP = 'S29988c', 'Sd3ac86'
def wav_write(path, x): x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).round().astype('<i2').tobytes()); w.close()
def wav_read(path): w = wave.open(path, 'rb'); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, w.getnchannels()).astype(np.float64) / 32767; w.close(); return x
rng = np.random.default_rng(72); t_ = lambda n: np.arange(n) / SR
def bp(x, lo, hi): sos = signal.butter(4, [lo, hi] if lo and hi else (hi or lo), 'bandpass' if lo and hi else ('lowpass' if hi else 'highpass'), fs=SR, output='sos'); return signal.sosfilt(sos, x)
def st(x): return np.stack([x, x], 1)
# ---- new sounds (made here, seeded: the same every run)
def kick(): n = int(.5 * SR); t = t_(n); f = 46 + 90 * np.exp(-t / .035); ph = 2 * np.pi * np.cumsum(f) / SR; y = np.sin(ph) * np.exp(-t / .16) + .25 * bp(rng.standard_normal(n), 1500, 5000) * np.exp(-t / .004); return st(.9 * y / np.abs(y).max())
def knock(): y = bp(kick()[:, 0], 190, None); n = int(.2 * SR); y = y[:n] * np.exp(-t_(n) / .05); return st(.5 * y / np.abs(y).max())      # the kick with its weight taken out
def snare(): n = int(.3 * SR); t = t_(n); y = .8 * bp(rng.standard_normal(n), 1400, 6500) * np.exp(-t / .07) + .5 * np.sin(2 * np.pi * 186 * t) * np.exp(-t / .05); return st(.8 * y / np.abs(y).max())
def hat(): n = int(.06 * SR); y = bp(rng.standard_normal(n), 7000, None) * np.exp(-t_(n) / .012); return st(.5 * y / np.abs(y).max())
def sub(f, beats): n = int(beats * BEAT); t = t_(n); y = np.sin(2 * np.pi * f * t) + .1 * np.sin(4 * np.pi * f * t); a = np.minimum(1, t / .012) * np.minimum(1, (n / SR - t) / .05); return st(.8 * y * a)
def riser(): n = BAR; t = t_(n); y = rng.standard_normal(n); f, tt, Z = signal.stft(y, SR, nperseg=1024); cut = 300 * (20 ** (tt / tt[-1])); Z *= (f[:, None] < cut[None, :]) * (f[:, None] > 250); _, y = signal.istft(Z, SR, nperseg=1024); y = y[:n] * (t / t[-1]) ** 2; return st(.5 * y / np.abs(y).max())
def hiss(): n = BAR; y = bp(rng.standard_normal(n + 2000), 5000, 11000)[2000:]; y *= .75 + .25 * np.sin(2 * np.pi * t_(n) / (BAR / SR)); return np.stack([y, np.roll(y, 331)], 1) * .25 / np.abs(y).max()
SYN = {'kick': kick(), 'knock': knock(), 'snare': snare(), 'hat': hat(), 'sub_D': sub(72.8, 3), 'sub_A': sub(54.85, 1), 'sub_C': sub(66.1, 2), 'sub_G': sub(48.55, 2), 'riser': riser(), 'hiss': hiss()}
# ---- spans: exact edits of catalog sources
def onset_near(src, a, b): x = load(src).mean(1)[int(a * SR):int(b * SR)]; e = np.sqrt(np.convolve(x ** 2, np.ones(441) / 441, 'same')); d = e[441:] - e[:-441]; return int(a * SR) + int(np.argmax(d))
s_on = onset_near(SUP, 143.85, 144.45) - 441
SPANS = {}
def span(name, src, s_in, s_out, role, fin=.015, fout=.06, note=''):
    x = load(src)[s_in:s_out].astype(np.float64); p = '%s/clips/%s.wav' % (OUT, name); wav_write(p, x); SPANS[name] = {'source': src, 'source_hash': reg[src]['sha256'], 'sample_in': s_in, 'sample_out': s_out, 'channel_mode': 'stereo', 'fades': {'in': int(fin * SR), 'out': int(fout * SR)}, 'role': role, 'file': 'clips/%s.wav' % name, 'note': note}
S = lambda sec: int(round(sec * SR))
span('roar_D', PRIM, S(10.12), S(10.12) + BAR, 'primary motif', note='one bar: D held three beats, then A. The source moves at 72 BPM here (an onset 0.83 s in).')
span('roar_C', PRIM, S(41.62), S(41.62) + BAR, 'primary motif', note='one bar: C, then G on beat 4')
span('roar_D2', PRIM, S(48.72), S(48.72) + BAR, 'primary motif', note='second take of the D-to-A bar')
span('roar_long', PRIM, S(107.66), S(107.66) + 3 * BEAT, 'primary motif', fout=.08, note='the loudest, steadiest D in the source (periodicity 0.98); found beyond the four cues')
span('roar_out', PRIM, S(112.0), S(112.0) + 3 * BAR, 'tail', fout=.4, note="the source's own ending")
span('answer_A', SUP, s_on, s_on + BAR, 'answer / tail', fin=.004, fout=.3, note='one struck A (110.8 Hz) falling 39 dB in 3.3 s')
for k, y in SYN.items():
    p = '%s/clips/%s.wav' % (OUT, k); wav_write(p, y); h = hashlib.sha256(open(p, 'rb').read()).hexdigest(); SPANS[k] = {'source': 'new:' + k, 'source_hash': h, 'sample_in': 0, 'sample_out': len(y), 'channel_mode': 'stereo', 'fades': {'in': 0 if k in ('kick', 'knock', 'snare', 'hat') else 64, 'out': 256}, 'role': 'made here', 'file': 'clips/%s.wav' % k, 'note': ''}
LANE = {'roar_D': 'primary', 'roar_C': 'primary', 'roar_D2': 'primary', 'roar_long': 'primary', 'roar_out': 'primary', 'answer_A': 'support', 'kick': 'drums', 'knock': 'drums', 'snare': 'drums', 'hat': 'drums', 'sub_D': 'bass', 'sub_A': 'bass', 'sub_C': 'bass', 'sub_G': 'bass', 'riser': 'texture', 'hiss': 'texture'}
GAIN = {'primary': -5, 'kick': -5, 'knock': -12, 'snare': -13, 'hat': -22, 'bass': -12, 'answer_A': -2, 'riser': -17, 'hiss': -26}
# ---- placements
PL = []; SCENES = {}
def put(scene, name, bar, beat, intent, evidence='', gain=0, pan=0, off=0, pitch=0, rev='r1'):
    sp = SPANS[name]; g = GAIN.get(name, GAIN.get(LANE[name], 0)) + gain
    PL.append({'id': 'p%04d' % len(PL), 'scene': scene, 'span': name, 'source_hash': sp['source_hash'], 'sample_in': sp['sample_in'], 'sample_out': sp['sample_out'], 'channel_mode': sp['channel_mode'], 'fades': sp['fades'], 'stretch': 1, 'pitch_shift': pitch, 'gain': g, 'pan': pan, 'lane': LANE[name], 'bar': bar, 'beat': beat, 'timing_offset': off, 'intent': intent, 'evidence': evidence, 'parent_revision': rev})
KICKS = {'A': [1, 2.75, 3.25], 'B': [1, 2.75, 3.5], 'H': [1, 1.75, 2.75, 3.25]}
def groove(sc, bar, kind, low=True, prim='auto', snare=(2, 4), hats=True, kick=True, sub=True, hiss=True, subg=0, kickg=0, fill=False, r='r1'):
    pk = kind if kind in 'AB' else 'A'
    if prim == 'auto': prim = 'roar_D' if pk == 'A' else 'roar_C'
    if prim: put(sc, prim, bar, 1, 'the motif: carries the bar', 'pitch-stable phrase of the primary source')
    if kick:
        for b in KICKS[kind]: put(sc, 'kick' if low else 'knock', bar, b, 'the weight' if low else 'the pattern without its weight', '', (0 if b == 1 else -3) + kickg)
    for b in snare: put(sc, 'snare', bar, b, 'backbeat', 'its band (1.4–6.5 kHz) is above the motif (240–840 Hz)')
    if hats:
        for k in range(8): put(sc, 'hat', bar, 1 + k / 2, 'grid', '', 0 if k % 2 == 0 else -4, off=0 if k % 2 == 0 else 880)
    if low and sub:
        if pk == 'A': put(sc, 'sub_D', bar, 1, 'the floor under D', 'tuned to the motif: 72.8 Hz measured', subg); put(sc, 'sub_A', bar, 4, 'follows the choir to A', '54.85 Hz: half of the measured 109.7', subg)
        else:
            put(sc, 'sub_C', bar, 1, 'the floor under C', '66.1 Hz measured', subg)
            if not fill: put(sc, 'sub_G', bar, 3, 'G', '48.55 Hz: half of the measured 97.1', subg)
    if fill: put(sc, 'snare', bar, 4.5, 'turnaround: the eighth bar must not be the second', 'critic: bars repeated sample for sample', -7, rev='r2'); put(sc, 'snare', bar, 4.75, 'turnaround', 'critic: bars repeated sample for sample', -4, rev='r2')
    if hiss: put(sc, 'hiss', bar, 1, 'air', '5–11 kHz only', pan=0)
def answer(sc, bar, why='answers the choir where it moves to A, and decays under the next bar', g=0): put(sc, 'answer_A', bar, 4, why, 'pitch class A, 13 cents sharp, corrected; 11% of its energy overlaps the motif', g, pitch=-.16)
def proof(sc, support):
    for b in range(1, 9): groove(sc, b, 'AB'[(b - 1) % 2], low=b >= 5); 
    if support: [answer(sc, b, g=-4 if b < 5 else 0) for b in (1, 3, 5, 7)]   # r2, critic: with no bass under it the answer stood 3 dB above everything
    SCENES[sc] = {'bars': 8}
proof('proofA', False); proof('proofB', True)
def brk(sc, b0):     # prepare -> remove the sub -> leave space -> return the weight
    groove(sc, b0, 'A', subg=-4); put(sc, 'riser', b0, 1, 'prepare: something is coming', '')   # r2, critic: the return was no heavier than the bars before it, so the bar before is lightened
    groove(sc, b0 + 1, 'B', kick=False, sub=False, snare=(4,), low=False); put(sc, 'answer_A', b0 + 1, 4, 'the tail left ringing across the dropout', 'falls 39 dB in a bar; its energy is below the vocal band', pitch=-.16)
    put(sc, 'hat', b0 + 2, 2, 'the grid, barely', '', -4); put(sc, 'hat', b0 + 2, 4, 'the grid, barely', '', -4); put(sc, 'hiss', b0 + 2, 1, 'air, so the empty bar is not digital silence', 'critic: 0.77 s of digital zero; 5–11 kHz is outside the vocal band', rev='r2')                    # the space for "Et tu, Brute?"
    groove(sc, b0 + 3, 'A', prim='roar_long', subg=2, kickg=2)
groove('break', 1, 'A'); groove('break', 2, 'B'); brk('break', 3); groove('break', 7, 'A', prim='roar_D2'); groove('break', 8, 'B'); SCENES['break'] = {'bars': 8, 'protected': [5]}
def full(sc, support):
    for b in range(1, 5): groove(sc, b, 'AB'[(b - 1) % 2], low=False)
    for b in range(5, 13): groove(sc, b, 'AB'[(b - 1) % 2], fill=b in (8, 12))
    brk(sc, 13)
    for b in range(17, 25): groove(sc, b, 'H' if b % 2 else 'B', prim='roar_long' if b % 2 else 'roar_C', fill=b in (20, 24))
    for b in range(25, 33): groove(sc, b, 'AB'[(b - 1) % 2], prim='roar_D2' if b % 2 else 'roar_C', fill=b in (28, 32), hats=b > 26)
    groove(sc, 33, 'A'); put(sc, 'roar_out', 34, 1, "the source's own ending", ''); put(sc, 'sub_D', 34, 1, 'last weight', ''); put(sc, 'kick', 34, 1, 'last weight', '')
    for k in range(8): put(sc, 'hat', 34, 1 + k / 2, 'grid', '', -4 - k)
    if support: [answer(sc, b) for b in list(range(5, 13, 2)) + list(range(17, 25, 2)) + list(range(27, 33, 2))]   # r2: in the hook the long D leaves beat 4 empty, and the answer goes there
    SCENES[sc] = {'bars': 36, 'protected': [15]}
full('full', '--nosupport' not in sys.argv)
# ---- render
CL = {}
def clip(name): 
    if name not in CL: CL[name] = wav_read('%s/clips/%s.wav' % (OUT, name))
    return CL[name]
def render(sc, mute=()):
    n = SCENES[sc]['bars'] * BAR; stems = {l: np.zeros((n, 2)) for l in ('primary', 'support', 'drums', 'bass', 'texture')}; edges = []
    for p in PL:
        if p['scene'] != sc or p['lane'] in mute: continue
        x = clip(p['span']).copy()
        if p['pitch_shift']: r = 2 ** (p['pitch_shift'] / 12); m = int(round(len(x) / r)); x = np.stack([np.interp(np.arange(m) * r, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
        fi, fo = p['fades']['in'], p['fades']['out']
        if fi: x[:fi] *= np.linspace(0, 1, fi)[:, None]
        if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
        g = 10 ** (p['gain'] / 20); a = (p['pan'] + 1) * np.pi / 4; x = x * g * np.array([np.cos(a), np.sin(a)]) * np.sqrt(2)
        s = (p['bar'] - 1) * BAR + int(round((p['beat'] - 1) * BEAT)) + p['timing_offset']; e = min(n, s + len(x)); 
        if e < s + len(x): x = x[:e - s].copy(); x[-256:] *= np.linspace(1, 0, 256)[:, None]
        stems[p['lane']][s:e] += x; edges += [s, e - 1]
    return stems, edges
if __name__ == '__main__':
    R = {sc: render(sc) for sc in SCENES}; mix = {sc: sum(R[sc][0].values()) for sc in SCENES}
    MASTER = 10 ** (-1 / 20) / max(np.abs(m).max() for m in mix.values()); print('master: one fixed gain %.2f dB, no dynamics' % (20 * np.log10(MASTER)))
    for sc in SCENES:
        wav_write('%s/renders/%s.wav' % (OUT, sc), mix[sc] * MASTER)
        if sc == 'full': [wav_write('%s/stems/%s.wav' % (OUT, l), y * MASTER) for l, y in R[sc][0].items()]
    json.dump({'title': 'ET TU, BRUTE · BOXES ON MY BACK (instrumental)', 'bpm': 72, 'sample_rate': SR, 'beat_samples': BEAT, 'bar_samples': BAR, 'master_gain_dB': round(20 * np.log10(MASTER), 3), 'lanes': ['primary', 'support', 'drums', 'bass', 'texture'], 'spans': SPANS, 'scenes': SCENES, 'placements': PL}, open(OUT + '/scion.json', 'w'), indent=0)
    print({sc: (SCENES[sc]['bars'], sum(p['scene'] == sc for p in PL)) for sc in SCENES}, 'support onset sample', s_on)
