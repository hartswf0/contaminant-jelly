# BUILDERS, second pass: two new drum kits (FOUND in the catalog, and MADE again properly), an 808-style sub, and a remix engine for other sources.
# Source time is in samples; arrangement time is bar/beat. Each track has its own tempo; a beat is always a whole number of samples.
import json, numpy as np, hashlib, os, wave, sys; from sig import *
OUT = 'out2'; reg = {r['id']: r for r in json.load(open('registry.json')) if r.get('status') == 'decoded'}; SC = json.load(open('scout.json')); SRCINFO = {s['id']: s for s in SC['sources']}
def wav_write(path, x): x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).round().astype('<i2').tobytes()); w.close()
def wav_read(path): w = wave.open(path, 'rb'); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2).astype(np.float64) / 32767; w.close(); return x
t_ = lambda n: np.arange(n) / SR
def filt(x, lo=None, hi=None, order=4): sos = signal.butter(order, [lo, hi] if lo and hi else (hi or lo), 'bandpass' if lo and hi else ('lowpass' if hi else 'highpass'), fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=0)
def norm(y, pk): return y * pk / np.abs(y).max()
def room(y, rng, ms=140, wet=.18):   # a short room, made of decaying noise, different in each ear
    n = int(ms / 1000 * SR); out = []
    for c in range(2): ir = rng.standard_normal(n) * np.exp(-t_(n) / (ms / 1000 / 5)); ir = filt(ir, 400, 7000); ir /= np.sqrt((ir ** 2).sum()); w = signal.fftconvolve(y, ir); d = np.zeros(len(w)); d[:len(y)] = y; out.append(d + wet * w)
    return np.stack(out, 1)
# ---------------- the MADE kit
def made_kit():
    rng = np.random.default_rng(808); K = {}
    n = int(.42 * SR); t = t_(n); f = 49 + 150 * np.exp(-t / .018) + 30 * np.exp(-t / .09); body = np.sin(2 * np.pi * np.cumsum(f) / SR) * (np.exp(-t / .13) * .85 + .15 * np.exp(-t / .3)); body = np.tanh(2.4 * body) / np.tanh(2.4)
    click = filt(rng.standard_normal(n), 1800, 7000) * np.exp(-t / .003) * 1.1; thump = filt(rng.standard_normal(n), 90, 240) * np.exp(-t / .012) * .5; y = body + click + thump; y[-400:] *= np.linspace(1, 0, 400); K['kick'] = np.stack([norm(y, .92)] * 2, 1)
    yk = filt(y, 200, None) * np.exp(-t / .045); K['knock'] = np.stack([norm(yk[:int(.2 * SR)], .5)] * 2, 1)
    n = int(.26 * SR); t = t_(n); tone = (np.sin(2 * np.pi * np.cumsum(182 + 60 * np.exp(-t / .012)) / SR) + .6 * np.sin(2 * np.pi * np.cumsum(331 + 80 * np.exp(-t / .01)) / SR)) * np.exp(-t / .055)
    nz = filt(rng.standard_normal(n), 2000, 9000) * (.5 * np.exp(-t / .028) + .22 * np.exp(-t / .11)) + 1.5 * filt(rng.standard_normal(n), 450, 1700) * (.8 * np.exp(-t / .035) + .2 * np.exp(-t / .09)); cl = filt(rng.standard_normal(n), 2500, None) * np.exp(-t / .0015); y = np.tanh(1.8 * (.55 * tone + nz + .6 * cl)); K['snare'] = norm(room(y, rng), .85)
    def hat(dur, dec):
        n = int(dur * SR); t = t_(n); y = sum(signal.square(2 * np.pi * f * 1.48 * t + i) for i, f in enumerate((205.3, 304.4, 369.6, 522.7, 540, 800))); y = filt(filt(y, 6500, None), None, 14000) * np.exp(-t / dec); y[-64:] *= np.linspace(1, 0, 64); return np.stack([norm(y, .5), norm(np.roll(y, 9), .5)], 1)
    K['hat'] = hat(.07, .014); K['ohat'] = hat(.34, .11)
    return K
# ---------------- the FOUND kit: three hits that stand alone in the catalog (60, 54 and 50 dB out of silence)
FOUND = {'kick': ('S484319', 67.086, .30), 'snare': ('S5bb2f2', 120.213, .30), 'hat': ('S5e8b37', 18.533, .16)}
def onset_exact(src, t, pre=.03):
    x = load(src); a = int((t - .06) * SR); seg = np.abs(x[a:a + int(.2 * SR)]).max(1); thr = seg.max() * .08; return a + int(np.argmax(seg > thr)) - 32
def sub808(f, sec, rng=None):   # a sine that starts above its note, is driven so it has overtones a small speaker can play, and decays
    n = int(sec * SR); t = t_(n); ph = 2 * np.pi * np.cumsum(f * (1 + .9 * np.exp(-t / .011))) / SR; y = np.sin(ph) + .38 * np.sin(2 * ph) + .24 * np.sin(3 * ph); y = np.tanh(3.2 * y) / np.tanh(3.2); y = filt(y, None, 900, 2)
    env = np.minimum(1, t / .004) * (.72 + .28 * np.exp(-t / .5)) * np.minimum(1, (sec - t) / .07); return np.stack([y * env * .8] * 2, 1)
def riser(n, rng): y = rng.standard_normal(n); f, tt, Z = signal.stft(y, SR, nperseg=1024); cut = 300 * (20 ** (tt / tt[-1])); Z *= (f[:, None] < cut[None, :]) * (f[:, None] > 250); _, y = signal.istft(Z, SR, nperseg=1024); y = y[:n] * (t_(n) / (n / SR)) ** 2; return np.stack([norm(y, .5)] * 2, 1)
def hiss(n, rng): y = filt(rng.standard_normal(n + 2000), 5000, 11000)[2000:]; y *= .75 + .25 * np.sin(2 * np.pi * np.arange(n) / n); return np.stack([y, np.roll(y, 331)], 1) * .25 / np.abs(y).max()
NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def fold(f, lo=41, hi=82):
    while f > hi: f /= 2
    while f < lo: f *= 2
    return f
class Track:
    def __init__(s, tid, title, bpm, kit, seed=1):
        s.id, s.title, s.bpm = tid, title, bpm; s.BEAT = int(round(SR * 60 / bpm)); s.BAR = 4 * s.BEAT; s.dir = '%s/%s' % (OUT, tid); os.makedirs(s.dir + '/clips', exist_ok=True); s.spans = {}; s.lane = {}; s.PL = []; s.scenes = {}; s.gain = {}; s.rng = np.random.default_rng(seed); s.pads = []; s.kit = kit
    def raw(s, name, y, lane, gain, blind, note='', kick=False):
        p = '%s/clips/%s.wav' % (s.dir, name); wav_write(p, y); h = hashlib.sha256(open(p, 'rb').read()).hexdigest(); s.spans[name] = {'source': 'new:' + name, 'source_hash': h, 'sample_in': 0, 'sample_out': len(y), 'channel_mode': 'stereo', 'fades': {'in': 0, 'out': 128}, 'role': 'made here', 'file': 'clips/%s.wav' % name, 'note': note, 'blind': blind, 'kick': kick}; s.lane[name] = lane; s.gain[name] = gain
    def cut(s, name, src, s_in, s_out, lane, gain, blind, fin=.004, fout=.04, note='', role='', kick=False):
        y = load(src)[s_in:s_out].astype(np.float64); wav_write('%s/clips/%s.wav' % (s.dir, name), y); s.spans[name] = {'source': src, 'source_hash': reg[src]['sha256'], 'sample_in': int(s_in), 'sample_out': int(s_out), 'channel_mode': 'stereo', 'fades': {'in': int(fin * SR), 'out': int(fout * SR)}, 'role': role, 'file': 'clips/%s.wav' % name, 'note': note, 'blind': blind, 'kick': kick}; s.lane[name] = lane; s.gain[name] = gain
    def drums(s, which):
        if which == 'made':
            K = made_kit(); s.raw('kick', K['kick'], 'drums', -4, 'KICK', 'made again: a driven body, a click and a thump', True); s.raw('snare', K['snare'], 'drums', -9, 'SNARE', 'two tones, two layers of noise, a short room'); s.raw('hat', K['hat'], 'drums', -19, 'HAT', 'six square waves, as the old drum machines did'); s.raw('ohat', K['ohat'], 'drums', -21, 'OPEN HAT'); s.raw('knock', K['knock'], 'drums', -11, 'KNOCK', 'the kick with its weight taken out')
        else:
            for k, (src, t, d) in FOUND.items(): a = onset_exact(src, t); s.cut(k, src, a, a + int(d * SR), 'drums', {'kick': -1, 'snare': -3, 'hat': -14}[k], k.upper(), fin=0, fout=.02, note='found in the catalog, alone in silence', role='drum hit', kick=k == 'kick')
            y = wav_read(s.dir + '/clips/kick.wav'); yk = filt(y, 200, None); s.raw('knock', norm(yk, .5), 'drums', -8, 'KNOCK', 'the found kick with its weight taken out'); K = made_kit(); s.raw('ohat', K['ohat'], 'drums', -21, 'OPEN HAT')
    def sub(s, name, f, beats, note=''): s.raw(name, sub808(f, beats * s.BEAT / SR), 'bass', -10, 'SUB ' + name.split('_')[1].replace('s', '#'), note or '%.1f Hz' % f)
    def put(s, scene, name, bar, beat, intent='', evidence='', gain=0, pan=0, off=0, pitch=0, rev='r3', fin=None):
        sp = s.spans[name]; fades = dict(sp['fades']); 
        if fin is not None: fades['in'] = fin
        s.PL.append({'id': 'p%04d' % len(s.PL), 'scene': scene, 'span': name, 'source_hash': sp['source_hash'], 'sample_in': sp['sample_in'], 'sample_out': sp['sample_out'], 'channel_mode': 'stereo', 'fades': fades, 'stretch': 1, 'pitch_shift': pitch, 'gain': round(s.gain[name] + gain, 2), 'pan': pan, 'lane': s.lane[name], 'bar': bar, 'beat': beat, 'timing_offset': int(off), 'intent': intent, 'evidence': evidence, 'parent_revision': rev})
    # one bar of drums. k/sn: beats; hats: '8' or '16'; swing delays the off sixteenths; small seeded differences in time and level so no two bars are the same machine
    def beatbar(s, sc, bar, k=(1,), sn=(2, 4), ghosts=(), hats='16', low=True, openhat=None, swing=.14, kg=0, hatg=0):
        for b in k: s.put(sc, 'kick' if low else 'knock', bar, b, 'the weight' if low else 'the pattern without its weight', '', (0 if b == 1 else -2.5) + kg)
        for b in sn: s.put(sc, 'snare', bar, b, 'backbeat')
        for b in ghosts: s.put(sc, 'snare', bar, b, 'ghost note', '', -11 + s.rng.uniform(-1.5, 1.5), off=s.rng.integers(-150, 250))
        if hats:
            step = .25 if hats == '16' else .5
            for i in range(int(4 / step)):
                b = 1 + i * step; 
                if openhat and abs(b - openhat) < 1e-6: s.put(sc, 'ohat', bar, b, 'lift'); continue
                acc = 0 if i % (2 if hats == '8' else 4) == 0 else (-3 if hats == '16' and i % 2 == 0 else -6.5); sw = int(swing * step * s.BEAT) if (i % 2 == 1) else 0
                s.put(sc, 'hat', bar, b, 'grid', '', acc + hatg + s.rng.uniform(-1, 1), pan=.12, off=sw + s.rng.integers(-90, 90))
    def subnote(s, sc, name, bar, beat, with_kick=True, gain=0): s.put(sc, name, bar, beat, 'the floor', s.spans[name]['note'], gain, fin=int(.028 * SR) if with_kick else 200)   # under a kick the sub fades in over 28 ms, so the kick's click is heard first
    def render(s, sc, only=None):
        n = s.scenes[sc]['bars'] * s.BAR; stems = {l: np.zeros((n, 2)) for l in LANES}; edges = []; cl = {}
        for p in s.PL:
            if p['scene'] != sc: continue
            if p['span'] not in cl: cl[p['span']] = wav_read('%s/clips/%s.wav' % (s.dir, p['span']))
            x = cl[p['span']].copy()
            if p['pitch_shift']: r = 2 ** (p['pitch_shift'] / 12); m = int(round(len(x) / r)); x = np.stack([np.interp(np.arange(m) * r, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
            fi, fo = p['fades']['in'], min(p['fades']['out'], len(x))
            if fi: fi = min(fi, len(x)); x[:fi] *= np.linspace(0, 1, fi)[:, None]
            if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
            a = (p['pan'] + 1) * np.pi / 4; x = x * 10 ** (p['gain'] / 20) * np.array([np.cos(a), np.sin(a)]) * np.sqrt(2)
            st = (p['bar'] - 1) * s.BAR + int(round((p['beat'] - 1) * s.BEAT)) + p['timing_offset']; st = max(st, 0); e = min(n, st + len(x))
            if e <= st: continue
            if e < st + len(x): x = x[:e - st].copy(); k = min(256, len(x)); x[-k:] *= np.linspace(1, 0, k)[:, None]
            stems[p['lane']][st:e] += x; edges += [e - 1] if p['lane'] == 'drums' else [st, e - 1]   # a drum's first sample is its attack, not a click
        return stems, edges
    def finish(s, labels, names):
        R = {sc: s.render(sc) for sc in s.scenes}; mix = {sc: sum(R[sc][0].values()) for sc in s.scenes}; g = 10 ** (-1 / 20) / max(np.abs(m).max() for m in mix.values()); os.makedirs(s.dir + '/renders', exist_ok=True); os.makedirs(s.dir + '/stems', exist_ok=True); worst = 0
        for sc in s.scenes:
            wav_write('%s/renders/%s.wav' % (s.dir, sc), mix[sc] * g); x = mix[sc]; e = np.array([k for k in R[sc][1] if 2 < k < len(x) - 2]); worst = max(worst, float(np.abs(x[e + 1] - x[e]).max()), float(np.abs(x[e] - x[e - 1]).max()))
        last = list(s.scenes)[-1]; [wav_write('%s/stems/%s.wav' % (s.dir, l), y * g) for l, y in R[last][0].items()]
        json.dump({'id': s.id, 'title': s.title, 'bpm': s.bpm, 'sample_rate': SR, 'beat_samples': s.BEAT, 'bar_samples': s.BAR, 'master_gain_dB': round(20 * np.log10(g), 3), 'lanes': LANES, 'lane_names': labels, 'pads': s.pads, 'spans': s.spans, 'scenes': s.scenes, 'placements': s.PL}, open(s.dir + '/scion.json', 'w'), indent=0)
        db = lambda x: 10 * np.log10((x ** 2).mean() + 1e-15); st = R[last][0]
        print('%-9s %5.1f BPM  %s  master %+.2f dB  peak-check ok  largest edit step %.3f  lanes: %s' % (s.id, s.bpm, {k: v['bars'] for k, v in s.scenes.items()}, 20 * np.log10(g), worst, ' '.join('%s %.0f' % (l[:3], db(y * g)) for l, y in st.items())))
        return {'clicks': worst, 'gain': g}
LANES = ['primary', 'support', 'drums', 'bass', 'texture']
def tc(smp): return '%d:%05.2f' % (smp / SR // 60, smp / SR % 60)
