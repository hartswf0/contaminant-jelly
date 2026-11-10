# REMIXES OF OTHER SOURCES. Sources are chosen blind, by how many loud, steady, pitched phrases they hold. Each is cut at its onsets into
# short chops and replayed on a new grid, so the source's own tempo does not matter. Three treatments: boom-bap, dub, half-time.
from build2 import *
def phrases(src):
    x = load(src); m = x.mean(1); loud = SRCINFO[src]['loud_dB']; out = []
    for c in [c for c in SC['candidates'] if c['role'] == 'answer' and c['src'] == src and c['periodicity'] >= .88 and c['f0'] < 880]:   # 918.8 Hz is the edge of the pitch search, not a pitch: a false positive, found when three different sources all 'sang' it
        a, b = int(c['t0'] * SR), int(c['t1'] * SR); seg = x[a:b]
        if (np.abs(seg) > .985).sum() or len(seg) < SR: continue
        lv = 10 * np.log10((seg ** 2).mean() + 1e-12)
        if lv < -27: continue
        w = m[a - int(.25 * SR):a + int(.15 * SR)]; e = np.sqrt(np.convolve(w ** 2, np.ones(441) / 441, 'same')); d = e[882:] - e[:-882]; k = int(np.argmax(d)); on = a - int(.25 * SR) + k + 300 if d[k] > .25 * e.max() else a
        out.append({'in': int(on), 'len': int(b - on), 'f0': c['f0'], 'pc': c['pitch_class'], 'per': c['periodicity'], 'lv': round(float(lv), 1), 'score': float(c['periodicity'] + .02 * lv), 'onset': bool(d[k] > .25 * e.max())})
    out.sort(key=lambda p: -p['score']); keep = []
    for p in out:
        if any(abs(p['in'] - q['in']) < 3 * SR for q in keep): continue
        if sum(q['pc'] == p['pc'] for q in keep) >= 2: continue
        if keep and (NOTE.index(p['pc']) - NOTE.index(keep[0]['pc'])) % 12 not in (0, 3, 4, 5, 7, 8, 9): continue   # only phrases that sit with the first: thirds, fourths, fifths, sixths
        keep.append(p)
        if len(keep) == 4: break
    if len(keep) == 3: q = dict(keep[0]); h = q['len'] // 2; q['in'] += h; q['len'] -= h; q['onset'] = False; keep.append(q)   # a fourth chop from the second half of the first
    return keep
def choose():
    used = {'S29988c', 'Sd3ac86'}; dup = {b for a, b, c in SC['near_duplicates']}; rows = []
    for sid in SRCINFO:
        if sid in used or sid in dup: continue
        ph = phrases(sid)
        if len(ph) >= 4: rows.append((sum(p['score'] for p in ph), sid, ph))
    rows.sort(key=lambda r: -r[0]); pick = []; cats = set()
    for sc, sid, ph in rows:
        cat = reg[sid]['catalog']
        if cat in cats: continue
        cats.add(cat); pick.append((sid, ph))
        if len(pick) == 3: break
    return pick, len(rows)
def remix(sid, ph, style):
    bpm = {'boom': 86, 'dub': 63, 'half': 70}[style]; T = Track('remix-' + style, {'boom': 'REMIX 1 · BOOM-BAP', 'dub': 'REMIX 2 · DUB', 'half': 'REMIX 3 · HALF-TIME'}[style], bpm, 'made', seed=len(style) * 7 + bpm); B, Q = T.BAR, T.BEAT
    L = {'boom': [2, 1, 2, 1], 'dub': [2, 2, .5, 2], 'half': [1, 1, 1.5, 1]}[style]
    for i, p in enumerate(ph): n = min(int(L[i] * Q), p['len']); T.cut('chop%d' % (i + 1), sid, p['in'], p['in'] + n, 'primary' if i < 3 else 'support', -5, 'CHOP %d · %s' % (i + 1, p['pc']), .003, .05 if style != 'dub' else .12, '%s, %.1f Hz, steadiness %.2f, cut at %s' % (p['pc'], p['f0'], p['per'], 'its onset' if p['onset'] else 'the phrase start'), 'pitched chop')
    def lowshare(p): m = load(sid)[p['in']:p['in'] + min(p['len'], SR)].mean(1); S = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR); return float(S[f < 110].sum() / S.sum())
    LS = [lowshare(p) for p in ph]; own_bass = max(LS[:2]) > .3; print('   low share of the chops:', [round(v, 2) for v in LS], '-> the sample is its own bass: no new sub' if own_bass else '-> new sub added')
    T.drums('made'); subs = {}
    for i, p in enumerate(ph):
        f = fold(p['f0']); k = 'sub_%s' % p['pc'].replace('#', 's')
        if k not in subs: T.sub(k, f, {'boom': 1.5, 'dub': 3, 'half': 2.5}[style], '%.1f Hz: the chop’s own pitch, brought down %d octaves' % (f, round(np.log2(p['f0'] / f)))); subs[k] = 1
    T.raw('hiss', hiss(B, T.rng), 'texture', -27, 'AIR'); T.raw('riser', riser(B, T.rng), 'texture', -18, 'RISER'); c = ['chop%d' % (i + 1) for i in range(4)]; sb = ['sub_%s' % p['pc'].replace('#', 's') for p in ph]
    T.pads = c + ['kick', 'snare', 'hat', 'ohat'] + ([] if own_bass else list(subs))
    def chops(sc, b, v, g=0):
        if style == 'boom':
            for name, beat in ([(0, 1), (1, 3), (0, 4)] if v == 0 else [(2, 1), (1, 3), (3, 4)]): T.put(sc, c[name], b, beat, 'the chop, replayed on the new grid', T.spans[c[name]]['note'], g, pan=(-.25 if name == 1 else .25 if name == 3 else 0))
        elif style == 'dub':
            T.put(sc, c[0 if v == 0 else 1], b, 1, 'the phrase', '', g)
            for k in range(5): T.put(sc, c[2], b, 3 + k * .75, 'echo: each repeat 5 dB quieter, thrown from side to side', 'the delay is made of placements, so each repeat can be removed', g - 3 - 5 * k, pan=(.6 if k % 2 else -.6))
            if v == 1: T.put(sc, c[3], b, 2.5, 'answer, off the beat', '', g - 3, pan=.3)
        else:
            for name, beat in ([(0, 1), (0, 1.75), (1, 2.5), (2, 3.5)] if v == 0 else [(0, 1), (3, 2), (1, 2.75), (2, 3.5)]): T.put(sc, c[name], b, beat, 'stab', T.spans[c[name]]['note'], g, pan=(.3 if name == 3 else 0))
    def low(sc, b, v, g=0):
        if own_bass: return   # the chops already hold the low end; a second bass would fight them
        if style == 'boom': T.subnote(sc, sb[0 if v == 0 else 2], b, 1, gain=g); T.subnote(sc, sb[1], b, 3, False, g)
        elif style == 'dub': T.subnote(sc, sb[0 if v == 0 else 1], b, 1, False, g)
        else: T.subnote(sc, sb[0], b, 1, gain=g); T.subnote(sc, sb[1 if v == 0 else 3], b, 2.5, False, g - 1, )
    def drum(sc, b, v, on=True, fill=False):
        if style == 'boom': T.beatbar(sc, b, k=((1, 2.5, 3.75) if v == 0 else (1, 1.75, 2.5)) if on else (), sn=(2, 4), ghosts=(3.25,) + ((4.5, 4.75) if fill else ()), hats='16' if on else '8', low=on, openhat=None if fill else (4.5 if v else None), swing=.2)
        elif style == 'dub': T.beatbar(sc, b, k=(3,) if on else (), sn=(3,), ghosts=(4.75,) if fill else (), hats='8', low=on, openhat=2.5 if v else None, swing=.0, hatg=-2)   # one drop: kick and snare together on three
        else: 
            T.beatbar(sc, b, k=((1, 2.5) if v == 0 else (1, 1.75, 4.25)) if on else (), sn=(3,), ghosts=(), hats='8', low=on, swing=0)
            if fill or v: [T.put(sc, 'hat', b, 4 + k / 8, 'roll', '', -8 + k, pan=.12) for k in range(1, 8, 2)]
    sc = 'full'
    for b in range(1, 5): chops(sc, b, (b - 1) % 2, -2); drum(sc, b, (b - 1) % 2, on=False); T.put(sc, 'hiss', b, 1, 'air')
    T.put(sc, 'riser', 4, 1, 'prepare')
    for b in range(5, 13): v = (b - 1) % 2; chops(sc, b, v); drum(sc, b, v, fill=b in (8, 12)); low(sc, b, v); T.put(sc, 'hiss', b, 1, 'air')
    for b in (13, 14): chops(sc, b, (b - 1) % 2, -1); T.put(sc, 'hiss', b, 1, 'air'); T.put(sc, 'hat', b, 2, 'the grid, barely', '', -4); T.put(sc, 'hat', b, 4, 'the grid, barely', '', -4)
    T.put(sc, 'riser', 14, 1, 'prepare')
    for b in range(15, 21): v = (b - 1) % 2; chops(sc, b, v); drum(sc, b, v, fill=b in (18, 20)); low(sc, b, v, 1.5 if b == 15 else 0); T.put(sc, 'hiss', b, 1, 'air')
    T.put(sc, c[0], 21, 1, 'last word'); low(sc, 21, 0); T.put(sc, 'kick', 21, 1, 'last weight')
    T.scenes['loop'] = {'bars': 2, 'label': 'TWO BARS', 'say': 'The two-bar idea on its own.'}
    for b in (1, 2): chops('loop', b, b - 1); drum('loop', b, b - 1); low('loop', b, b - 1); T.put('loop', 'hiss', b, 1, 'air')
    T.scenes = {'loop': T.scenes['loop'], 'full': {'bars': 21, 'label': 'WHOLE REMIX', 'say': {'boom': 'Boom-bap at 86: four chops replayed on a swung grid.', 'dub': 'Dub at 63: one drop on beat three, and an echo built from single placements.', 'half': 'Half-time at 70: stabs, a long sub, hat rolls.'}[style]}}
    return T, T.finish({'primary': 'CHOPS', 'support': 'ANSWER', 'drums': 'DRUMS', 'bass': 'SUB', 'texture': 'AIR'}, None)
if __name__ == '__main__':
    pick, n = choose(); print(n, 'sources hold four or more loud, steady phrases; chosen blind:', [p[0] for p in pick]); json.dump([{'src': s, 'phrases': ph} for s, ph in pick], open('remix_pick.json', 'w'), indent=1)
    for (sid, ph), style in zip(pick, ('boom', 'dub', 'half')):
        print(sid, [(p['pc'], p['f0'], p['per'], p['lv'], tc(p['in']), p['onset']) for p in ph]); remix(sid, ph, style)
