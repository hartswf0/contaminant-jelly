# ENGINE for the swarm songs: every sound is a slice of a crate clip; a placement carries slice, pitch, filters, room send, gain, pan.
# One shared room; a master that is one gain into a soft limiter (tanh), which the instrument reproduces exactly.
import json, numpy as np, os, wave, hashlib; from scipy import signal
SR = 44100; CRATE = json.load(open('out3/crate/crate.json')); CL = CRATE['clips']; LANES = ['primary', 'support', 'drums', 'bass', 'texture']
LANE = {'kick': 'drums', 'snare': 'drums', 'hat': 'drums', 'tick': 'drums', 'bass': 'bass', 'phrase': 'primary', 'choir': 'primary', 'glide': 'primary', 'call': 'support', 'breath': 'support', 'hole': 'support', 'tail': 'support', 'bed': 'texture', 'texture': 'texture', 'quiet': 'texture', 'random': 'texture'}
RG = {'kick': -6, 'snare': -8, 'hat': -15, 'tick': -11, 'bass': -4, 'phrase': -2, 'choir': -2, 'glide': -3, 'call': -3, 'breath': -6, 'hole': -8, 'tail': -7, 'bed': -11, 'texture': -13, 'quiet': -7, 'random': -10}
def wav_write(path, x): x = np.clip(x, -1, 1); w = wave.open(path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).round().astype('<i2').tobytes()); w.close()
def wav_read(path): w = wave.open(path, 'rb'); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2).astype(np.float64) / 32767; w.close(); return x
_c = {}
def clip(name):
    if name not in _c: _c[name] = wav_read('out3/crate/%s.wav' % name)
    return _c[name]
IR = wav_read('out3/crate/room.wav'); pitched = lambda c: 60 < c['f0'] < 880 and c['periodicity'] >= .85; db = lambda x: 10 * np.log10((x ** 2).mean() + 1e-15)
def rhe(x): return int(np.round(x))
def snd_any(R, sc, l): return 0
class Song:
    def __init__(s, idx, slug, title, mech, bpm):
        s.idx, s.id, s.title, s.mech, s.bpm = idx, 's%02d-%s' % (idx, slug), title, mech, bpm; s.BEAT = int(round(SR * 60 / bpm)); s.BAR = 4 * s.BEAT; s.PL = []; s.scenes = {}; s.used = {}; s.rng = np.random.default_rng(idx * 101); s.root = None; s.notes = {}
    def pick(s, role, i=0): names = sorted(k for k, v in CL.items() if v['role'] == role); return names[(s.idx + i) % len(names)]
    def set_root(s, name): s.root = CL[name]['midi'] if pitched(CL[name]) else 62.0; return name
    def tune(s, name):
        c = CL[name]
        if s.root is None or not pitched(c): return 0.0
        d = c['midi'] - s.root; best = min((t for o in range(-4, 5) for t in [o * 12 + k for k in (0, 3, 4, 5, 7, 8, 9)]), key=lambda t: abs(t - d)); sh = best - d; return float(sh) if abs(sh) <= 2.5 else 0.0
    def put(s, sc, name, bar, beat, g=0, pan=0, off=0, sl=None, shift=None, hp=None, lp=None, room=0, lane=None, intent='', fin=None, fout=None):
        c = CL[name]; s.used[name] = s.used.get(name, 0) + 1; n = c['sample_out'] - c['sample_in']; a, L = (0, n) if sl is None else (int(sl[0] * SR), int(sl[1] * SR)); a = max(0, min(a, n - 64)); L = max(64, min(L, n - a)); sh = s.tune(name) if shift is None else float(shift)
        fa = dict(c['fades']); 
        if sl is not None: fa = {'in': min(fa['in'], 220) if a else fa['in'], 'out': min(max(fa['out'], 330), L // 3)}
        if fin is not None: fa['in'] = int(fin * SR)
        if fout is not None: fa['out'] = int(fout * SR)
        s.PL.append({'id': 'p%04d' % len(s.PL), 'scene': sc, 'span': name, 'source_hash': c['source_hash'], 'sample_in': c['sample_in'] + a, 'sample_out': c['sample_in'] + a + L, 'clip_offset': a, 'clip_len': L, 'channel_mode': 'stereo', 'fades': fa, 'stretch': 1, 'pitch_shift': round(sh, 3), 'gain': round(c['trim_dB'] + RG[c['role']] + g, 2), 'pan': pan, 'hp': c['hp'] if hp is None else hp, 'lp': c['lp'] if lp is None else lp, 'room': room, 'lane': lane or LANE[c['role']], 'bar': int(bar), 'beat': float(beat), 'timing_offset': int(off), 'intent': intent, 'evidence': c['why'], 'parent_revision': 'r1'})
    def at(s, sc, name, q, **kw):   # q = absolute beat from 0
        s.put(sc, name, 1 + int(q // 4), 1 + q % 4, **kw)
    def bass(s, sc, bar, beat, semis=0, beats=1.0, g=0, name=None, off=0):
        name = name or s.pick('bass'); c = CL[name]; rootpc = (s.root if s.root is not None else 62.0) % 12; tgt = min((o * 12 + rootpc + semis for o in range(1, 5)), key=lambda t: abs(t - c['midi'])); sh = tgt - c['midi']; r = 2 ** (sh / 12); s.put(sc, name, bar, beat, g=g, sl=(.0, min(beats * s.BEAT / SR * r, c['seconds'])), shift=sh, intent='bass: a catalog note tuned to the song', fin=.012, fout=.05, off=off)
    def kit(s, sc, bar, k=(1,), sn=(2, 4), hats='8', ghosts=(), swing=.12, feel=(0, 0, 0), low=True, kg=0, hatg=0, K=0):
        kk, ss, hh = s.pick('kick', K), s.pick('snare', K), s.pick('hat', K)
        for b in k: s.put(sc, kk, bar, b, g=(0 if b == 1 else -2.5) + kg, off=feel[0], hp=0 if low else 220, intent='kick' if low else 'the kick without its weight')
        for b in sn: s.put(sc, ss, bar, b, off=feel[1], intent='backbeat')
        for b in ghosts: s.put(sc, ss, bar, b, g=-10 + s.rng.uniform(-1.5, 1.5), off=feel[1] + int(s.rng.integers(-150, 250)), intent='ghost note')
        if hats:
            st = .25 if hats == '16' else .5
            for i in range(int(4 / st)): s.put(sc, hh, bar, 1 + i * st, g=(0 if i % (4 if hats == '16' else 2) == 0 else -3 if hats == '16' and i % 2 == 0 else -6) + hatg + s.rng.uniform(-1, 1), pan=.15, off=(int(swing * st * s.BEAT) if i % 2 else 0) + feel[2] + int(s.rng.integers(-80, 80)), intent='grid')
    def cells(s, name, k):   # k slices of a clip, cut at its own onsets where it has them
        y = clip(name).mean(1); n = len(y); e = np.sqrt(np.convolve(y ** 2, np.ones(441) / 441, 'same')); d = np.maximum(0, e[882:] - e[:-882]); pk, _ = signal.find_peaks(d, height=d.max() * .2, distance=int(.12 * SR)); cuts = sorted(set([0] + [int(p) + 300 for p in pk if .08 * SR < p < n - .15 * SR]))
        if len(cuts) < k: cuts = [int(i * n / k) for i in range(k)]
        cuts = cuts[:k] + [n] if len(cuts) > k else cuts + [n]; cuts = sorted(set(cuts)); return [(cuts[i] / SR, (cuts[i + 1] - cuts[i]) / SR) for i in range(len(cuts) - 1)][:k]
    def scene(s, key, bars, label, say, **kw): s.scenes[key] = {'bars': bars, 'label': label, 'say': say, **kw}
    def render(s, sc):
        n = s.scenes[sc]['bars'] * s.BAR; dry = {l: np.zeros((n, 2)) for l in LANES}; snd = {l: np.zeros((n, 2)) for l in LANES}; edges = []
        for p in s.PL:
            if p['scene'] != sc: continue
            x = clip(p['span'])[p['clip_offset']:p['clip_offset'] + p['clip_len']].copy()
            if p['pitch_shift']: r = 2 ** (p['pitch_shift'] / 12); m = max(2, int(len(x) / r)); x = np.stack([np.interp(np.arange(m) * r, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
            if p['hp']: x = signal.sosfilt(signal.butter(2, p['hp'], 'highpass', fs=SR, output='sos'), x, axis=0)
            if p['lp']: x = signal.sosfilt(signal.butter(2, p['lp'], 'lowpass', fs=SR, output='sos'), x, axis=0)
            fi, fo = min(p['fades']['in'], len(x)), min(p['fades']['out'], len(x))
            if fi: x[:fi] *= np.linspace(0, 1, fi)[:, None]
            if fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
            a = (p['pan'] + 1) * np.pi / 4; x = x * 10 ** (p['gain'] / 20) * np.array([np.cos(a), np.sin(a)]) * np.sqrt(2); st = (p['bar'] - 1) * s.BAR + rhe((p['beat'] - 1) * s.BEAT) + p['timing_offset']
            if st < 0: x = x[-st:]; st = 0
            e = min(n, st + len(x))
            if e <= st: continue
            if e < st + len(x): x = x[:e - st].copy(); k = min(256, len(x)); x[-k:] *= np.linspace(1, 0, k)[:, None]
            dry[p['lane']][st:e] += x
            if p['lane'] != 'drums' and not CL[p['span']]['perc']: edges += [(p['lane'], st), (p['lane'], e - 1)]
            if p['room']: snd[p['lane']][st:e] += x * p['room']
        for l in LANES:
            if np.abs(snd[l]).max() > 0: dry[l] += np.stack([signal.fftconvolve(snd[l][:, c], IR[:, c])[:n] for c in (0, 1)], 1)
        return dry, edges
    def finish(s, lane_names, pads):
        d = 'out3/' + s.id; os.makedirs(d + '/renders', exist_ok=True); os.makedirs(d + '/stems', exist_ok=True); R = {sc: s.render(sc) for sc in s.scenes}; mix = {sc: sum(R[sc][0].values()) for sc in s.scenes}; main = 'song' if 'song' in mix else list(mix)[-1]; x = mix[main]
        g = 1.0
        for _ in range(30):   # one gain into the limiter, set so the song's average level is -15 dB, without pushing peaks past 2.2 times the knee
            cur = db(np.tanh(g * x)); g *= 10 ** ((-15 - cur) / 20 * .7); g = min(g, 2.2 / (np.abs(x).max() + 1e-9))
        worst = 0
        for sc in s.scenes:
            wav_write('%s/renders/%s.wav' % (d, sc), .94 * np.tanh(g * mix[sc])); worst = max([worst] + [float(np.abs(R[sc][0][l][k + 1] - R[sc][0][l][k]).max()) * g for l, k in R[sc][1] if 2 < k < len(mix[sc]) - 2 and not np.abs(snd_any(R, sc, l)) ])
        for l, y in R[main][0].items(): wav_write('%s/stems/%s.wav' % (d, l), np.clip(g * y, -1, 1))
        spans = {k: {'source': CL[k]['source'], 'source_hash': CL[k]['source_hash'], 'sample_in': CL[k]['sample_in'], 'sample_out': CL[k]['sample_out'], 'source_rate': SR, 'channel_mode': 'stereo', 'fades': CL[k]['fades'], 'role': CL[k]['role'], 'file': CL[k]['file'], 'note': CL[k]['why'], 'blind': CL[k]['blind'], 'kick': CL[k]['role'] == 'kick'} for k in s.used}
        y = .94 * np.tanh(g * x); st = R[main][0]; out = {'id': s.id, 'title': s.title, 'mechanism': s.mech, 'bpm': s.bpm, 'sample_rate': SR, 'beat_samples': s.BEAT, 'bar_samples': s.BAR, 'master_gain_dB': 0, 'master': {'drive': round(float(g), 5), 'ceiling': .94, 'shape': 'tanh'}, 'room': CRATE['room'], 'lanes': LANES, 'lane_names': lane_names, 'pads': [p for p in pads if p in s.used] or sorted(s.used)[:10], 'spans': spans, 'scenes': s.scenes, 'placements': s.PL}
        json.dump(out, open(d + '/scion.json', 'w'), indent=0)
        return {'id': s.id, 'bpm': s.bpm, 'seconds': round(len(x) / SR, 1), 'level_dB': round(float(db(y)), 1), 'peak_dB': round(float(20 * np.log10(np.abs(y).max())), 2), 'crest_dB': round(float(20 * np.log10(np.abs(y).max()) - db(y)), 1), 'drive': round(float(g), 2), 'edit_step': round(worst, 3), 'clips': len(s.used), 'sources': len({CL[k]['source'] for k in s.used}), 'placements': len([p for p in s.PL if p['scene'] == main]), 'low_share': round(float(10 ** ((db(signal.sosfilt(signal.butter(4, 110, 'lowpass', fs=SR, output='sos'), y.mean(1))) - db(y.mean(1))) / 10)), 2), 'mono_loss_dB': round(float(db(y.mean(1)) - db(y)), 2), 'lanes': {l: round(float(db(v * g)), 0) for l, v in st.items()}}
