# THE ALBUM: seven new pieces, one per operator of the brief, built on the frozen blind shortlist (M01–M12), one context-led pick (C1) and the roar.
from build2 import *
M = {c['id']: c for c in json.load(open('blind_shortlist.json'))}; S_ = lambda sec: int(round(sec * SR)); NOTES = {}
LN = {'primary': 'LEAD', 'support': 'ANSWER', 'drums': 'DRUMS', 'bass': 'SUB', 'texture': 'AIR'}
def onset(src, a, b):  # the steepest rise between a and b seconds
    x = load(src).mean(1)[S_(a):S_(b)]; e = np.sqrt(np.convolve(x ** 2, np.ones(441) / 441, 'same')); d = e[441:] - e[:-441]; return S_(a) + int(np.argmax(d)) + 100
def f0of(src, s_in, n=16384): seg = signal.resample_poly(load(src)[s_in:s_in + 2 * n].mean(1), 1, 2); return f0(seg[:n // 1])
def base(T, air=-27): T.raw('hiss', hiss(T.BAR, T.rng), 'texture', air, 'AIR'); T.raw('riser', riser(T.BAR, T.rng), 'texture', -18, 'RISER')
def qb(q): return 1 + int(q // 4), 1 + q % 4     # absolute beat -> bar, beat
def scene(T, key, bars, label, say, **kw): T.scenes[key] = {'bars': bars, 'label': label, 'say': say, **kw}
# ------------------------------------------------------------------ 2 · PICKUP (Cut)
def pickup():
    T = Track('a2-pickup', 'PICKUP', 80, 'found', seed=2); Q = T.BEAT; m1, m5, m6 = M['M01'], M['M05'], M['M06']
    a = m1['sample_in']; T.flip('glide', m1['src'], a, a + int(1.5 * Q), 'primary', 2, 'GLIDE', [], 'a rising glide: where its attack falls decides where the bar starts', 'M01', .006, .06)
    a = onset(m5['src'], m5['t0'] - .02, m5['t0'] + .1) - 60; T.flip('tick', m5['src'], a, a + S_(.3), 'support', -8, 'TICK', [], 'a dry tick to mark the off-beats', 'M05', 0, .02)
    a = onset(m6['src'], m6['t0'] + .25, m6['t1'] - .2) - 80; T.flip('tail', m6['src'], a, a + S_(1.1), 'support', -6, 'TAIL', [('room', 500, .25)], 'the last hit of the passage, left to ring in a room', 'M06', 0, .2, seed=6)
    T.drums('found'); fz = fold(551.0); T.sub('sub_Cs', fz, 2, '%.1f Hz: the glide’s starting pitch, four octaves down' % fz); base(T); T.pads = ['glide', 'tick', 'tail', 'kick', 'snare', 'hat', 'sub_Cs']
    def bar(sc, b, across, low=True, last=False):
        if across: 
            if b > 1: T.put(sc, 'glide', b - 1, 4.5, 'Cut: the attack is moved half a beat before the barline, so the body crosses it', 'branch B')
        else: T.put(sc, 'glide', b, 1, 'Cut: the attack is on the barline', 'branch A')
        T.beatbar(sc, b, k=(1, 2.75) if b % 2 else (1, 3.5), sn=(2, 4), ghosts=(3.25,) if b % 2 else (), hats='16', low=low, swing=.16, openhat=None)
        [T.put(sc, 'tick', b, q, 'off-beat marker', '', pan=-.3) for q in (2.5, 4.25)]
        if low: T.subnote(sc, 'sub_Cs', b, 1)
        if b % 4 == 0: T.put(sc, 'tail', b, 4, 'the phrase ends here', '', pan=.25)
        T.put(sc, 'hiss', b, 1, 'air')
    for sc, ac in (('a', False), ('b', True)):
        for b in range(1, 5): bar(sc, b, ac)
    scene(T, 'a', 4, 'A · ON THE BAR', 'A: the glide starts on beat one.'); scene(T, 'b', 4, 'B · ACROSS IT', 'B: the same glide starts half a beat early and crosses the barline. Nothing else differs.')
    for b in range(1, 17): bar('full', b, across=4 < b <= 12 or b == 16, low=b > 2)
    scene(T, 'full', 16, 'WHOLE PIECE', 'Four bars on the bar, eight across it, then back: listen for where “one” seems to be.', decisive='bar 5, beat 4.5 of bar 4: the first glide that starts before the barline')
    NOTES[T.id] = {'operator': 'Cut', 'thesis': 'When the glide’s attack moves half a beat before the barline, the listener should feel the downbeat shift from the sample to the kick.', 'falsifier': 'scenes A and B: four bars, identical but for where the glide starts', 'rejected': None}
    return T
# ------------------------------------------------------------------ 3 · LATE (Feel)
def late():
    T = Track('a3-late', 'LATE', 76, 'made', seed=3); Q = T.BEAT; m8, m12 = M['M08'], M['M12']
    a = m8['sample_in']; T.flip('tremble', m8['src'], a, a + int(2 * Q), 'primary', -5, 'TREMBLE', [], 'a note whose level already trembles 10.8 times a second: it carries its own pulse', 'M08', .01, .08)
    a = m12['sample_in']; T.flip('drawn', m12['src'], a, a + int(1.5 * Q), 'support', -9, 'DRAWN', [('hp', 300)], 'a random draw, thinned so it sits above the bed', 'M12', .01, .1)
    T.drums('made'); base(T); T.pads = ['tremble', 'drawn', 'kick', 'snare', 'hat', 'ohat']
    LATE = (-int(.006 * SR), int(.024 * SR), int(.012 * SR))
    def bar(sc, b, feel, low=True):
        T.put(sc, 'tremble', b, 1, 'the bed', ''); T.put(sc, 'tremble', b, 3, 'the bed', '', -1.5)
        if b % 2 == 0: T.put(sc, 'drawn', b, 2.5, 'the random draw, answering', '', pan=.3)
        T.beatbar(sc, b, k=(1, 2.5) if b % 2 else (1, 2.75, 3.5), sn=(2, 4), ghosts=(4.75,) if b % 4 == 0 else (), hats='16', low=low, swing=.1, feel=feel, openhat=4.5 if b % 4 == 2 else None); T.put(sc, 'hiss', b, 1, 'air')
    for sc, fl in (('a', (0, 0, 0)), ('b', LATE)):
        for b in range(1, 5): bar(sc, b, fl)
    scene(T, 'a', 4, 'A · STRAIGHT', 'A: every drum on the grid.'); scene(T, 'b', 4, 'B · LATE', 'B: the snare 24 ms late, the hats 12 ms late, the kick 6 ms early. The sample has not moved.')
    for b in range(1, 17): bar('full', b, LATE if b > 8 else (0, 0, 0), low=b > 2)
    scene(T, 'full', 16, 'WHOLE PIECE', 'Eight bars straight, eight bars late: the pocket should open at bar 9.', decisive='bar 9, beat 2: the first late snare')
    NOTES[T.id] = {'operator': 'Feel', 'thesis': 'With the sample’s timing kept and only the drums moved by a few milliseconds, the groove should lean back at bar 9.', 'falsifier': 'scenes A and B', 'rejected': None}
    return T
# ------------------------------------------------------------------ 4 · FIELD CLOCK (Reframe): the context-led pick
def clock():
    T = Track('a4-clock', 'FIELD CLOCK', 92, 'found', seed=4); Q = T.BEAT; R2 = json.load(open('registry2.json')); src = next(r['id'] for r in R2 if 'HUNH' in r['path'] and r['status'] == 'decoded')
    x = mono22(load(src)); f, t, Sx = stft(x, 1024, 128); env = onset_env(Sx); ok = (t > 8) & (t < len(x) / 22050 - 10); k = int(np.argmax(np.where(ok, env, 0))); a = onset(src, t[k] - .08, t[k] + .08) - 150
    T.flip('hunh', src, a, a + S_(.42), 'primary', 1, 'CALL', [], 'context-led: the title names a work-song grunt and a 92 BPM clock. The strongest onset in the file is taken as that grunt', 'C1', 0, .05); NOTES['C1'] = {'id': 'C1', 'kind': 'context-led', 'src': src, 'sample_in': a, 'sample_out': a + S_(.42), 't0': a / SR, 't1': a / SR + .42, 'obs': 'the strongest onset in the file (chosen after the names were revealed, from the title)', 'use': 'a voice that becomes the snare'}
    m7 = M['M07']; a7 = onset(m7['src'], m7['t0'], m7['t0'] + .2) - 100; T.flip('breath', m7['src'], a7, a7 + S_(.55), 'support', -7, 'BREATH', [], 'half a second of air, as the answer to the call', 'M07', 0, .08)
    T.drums('found'); fz, cf = f0of(src, a); fz = fold(fz) if cf > .6 else 46.25; T.sub('sub_X', fz, 1.5, '%.1f Hz%s' % (fz, ': the call’s own pitch, brought down' if cf > .6 else ': the call has no steady pitch, so F sharp was chosen')); base(T); T.pads = ['hunh', 'breath', 'kick', 'snare', 'hat', 'sub_X']
    for b in range(1, 21):
        T.put('full', 'hiss', b, 1, 'air')
        if b <= 4: T.put('full', 'hunh', b, 1, 'Reframe 1: a call, alone on the one', ''); T.beatbar('full', b, k=(), sn=(), hats='8', swing=0)
        elif b <= 12:
            [T.put('full', 'hunh', b, q, 'Reframe 2: the same call is now the backbeat. No snare plays', '') for q in (2, 4)]; T.beatbar('full', b, k=(1, 2.5, 3.25) if b % 2 else (1, 3.25), sn=(), hats='16', swing=.12); T.subnote('full', 'sub_X', b, 1); T.subnote('full', 'sub_X', b, 3.25, True, -1)
            if b % 2 == 0: T.put('full', 'breath', b, 4.5, 'the answer', '', pan=.3)
        elif b <= 16:
            T.put('full', 'hunh', b, 1, 'Reframe 3: call and answer; the drums step back', ''); T.put('full', 'breath', b, 3, 'the answer', '', pan=.3); T.beatbar('full', b, k=(), sn=(4,) if b == 16 else (), hats='8', swing=0)
        else:
            [T.put('full', 'hunh', b, q, 'the backbeat again, now with the snare under it', '') for q in (2, 4)]; T.beatbar('full', b, k=(1, 2.5, 3.25), sn=(2, 4), hats='16', swing=.12, ghosts=(4.75,) if b == 20 else ()); T.subnote('full', 'sub_X', b, 1)
    T.put('full', 'riser', 16, 1, 'prepare')
    scene(T, 'full', 20, 'WHOLE PIECE', 'One grunt, three jobs: a call on the one, then the backbeat, then half of a conversation.', decisive='bar 5, beat 2: the call first lands where the snare would')
    NOTES[T.id] = {'operator': 'Reframe', 'thesis': 'The same half-second of voice should be heard as a call for four bars and as a drum from bar 5, with nothing changed but where it falls.', 'falsifier': 'mute DRUMS from bar 5: if the voice still reads as a call, the reframing failed', 'rejected': None}
    return T
# ------------------------------------------------------------------ 5 · WHAT REMAINS (Haunt)
def remains():
    T = Track('a5-remains', 'WHAT REMAINS', 72, 'made', seed=5); B = T.BAR; P = 'S29988c'; STG = [('full', []), ('dim', [('lp', 560), ('gain', 2)]), ('band', [('bp', 380, 520), ('gain', 6)]), ('thread', [('bp', 420, 460), ('gain', 10), ('room', 700, .5)]), ('ghost', [('bp', 420, 460), ('gain', 12), ('room', 1100, .9)])]
    for i, (nm, ops) in enumerate(STG):
        for k, a in (('D', 10.12), ('C', 41.62)): T.flip('%s_%s' % (nm, k), P, S_(a), S_(a) + B, 'primary', -5, 'MOTIF %s · %d' % (k, i), ops, 'Haunt, stage %d: %s' % (i, {'full': 'the whole motif', 'dim': 'nothing above 560 Hz', 'band': 'only 380 to 520 Hz', 'thread': 'only 420 to 460 Hz, in a room', 'ghost': 'only 420 to 460 Hz, mostly room, every other bar'}[nm]), 'roar', .015, .06, seed=5)
    T.drums('made'); T.sub('sub_D', 72.8, 3); T.sub('sub_A', 54.85, 1); T.sub('sub_C', 66.1, 2); T.sub('sub_G', 48.55, 2); [T.gain.__setitem__(k, -13) for k in ('sub_D', 'sub_A', 'sub_C', 'sub_G')]; base(T); T.pads = ['full_D', 'dim_D', 'band_D', 'thread_D', 'ghost_D', 'kick', 'snare', 'hat', 'sub_D', 'sub_C']
    ref = {k: wav_read('%s/clips/full_%s.wav' % (T.dir, k)).mean(1) for k in 'DC'}; envf = lambda y: np.sqrt(np.convolve(y ** 2, np.ones(2205) / 2205, 'same'))[::2205]; leg = []
    for nm, ops in STG: y = wav_read('%s/clips/%s_D.wav' % (T.dir, nm)).mean(1)[:B]; S1 = np.abs(np.fft.rfft(y)) ** 2; fr = np.fft.rfftfreq(len(y), 1 / SR); c = np.cumsum(S1) / S1.sum(); leg.append({'stage': nm, 'bandwidth_Hz': [round(float(fr[np.searchsorted(c, .05)])), round(float(fr[np.searchsorted(c, .95)]))], 'envelope_match': round(float(np.corrcoef(envf(y), envf(ref['D']))[0, 1]), 2)})
    for b in range(1, 22):
        st = min(4, (b - 1) // 4); nm = STG[st][0] if b < 21 else 'full'; k = 'D' if b % 2 else 'C'
        if st < 4 or b % 2 or b == 21: T.put('full', '%s_%s' % (nm, k), b, 1, 'Haunt: stage %d of 4' % st if b < 21 else 'the whole motif, once more', '')
        if b < 21:
            T.beatbar('full', b, k=(1, 2.75) if b % 2 else (1, 3.5), sn=(2, 4) if st < 3 else (4,), ghosts=(), hats='16' if st < 2 else '8' if st < 4 else None, low=True, swing=.14)
            if k == 'D': T.subnote('full', 'sub_D', b, 1); T.subnote('full', 'sub_A', b, 4, False)
            else: T.subnote('full', 'sub_C', b, 1); T.subnote('full', 'sub_G', b, 3, False)
        T.put('full', 'hiss', b, 1, 'air')
    scene(T, 'full', 21, 'WHOLE PIECE', 'The choir is thinned every four bars while the weight stays. At what bar do you lose it?', decisive='bar 13: only 420 to 460 Hz of the choir is left')
    NOTES[T.id] = {'operator': 'Haunt', 'thesis': 'The motif should stay recognisable while its bandwidth shrinks from 600 Hz to 40 Hz, because the sub keeps playing its roots.', 'falsifier': 'mute SUB: if the motif is lost a stage earlier, the weight was carrying it', 'measured': leg, 'rejected': None}
    return T
# ------------------------------------------------------------------ 6 · SIXTY BEATS (Recombine)
def sixty():
    T = Track('a6-sixty', 'SIXTY BEATS', 90, 'found', seed=6); Q = T.BEAT; m9, m10, m11 = M['M09'], M['M10'], M['M11']
    a = m9['sample_in']; T.flip('long', m9['src'], a, a + 6 * Q, 'texture', -9, 'LONG · 6', [], 'a texture that darkens over four seconds: the long cycle, six beats', 'M09', .05, .3)
    a = m10['sample_in']; T.flip('quiet', m10['src'], a, a + int(1.5 * Q), 'primary', 3, 'QUIET · 3', [('gain', 14)], 'a quiet, perfectly steady pitch, raised 14 dB: the three-beat cycle', 'M10', .01, .1)
    a = m11['sample_in']; T.flip('drawn', m11['src'], a, a + 2 * Q, 'support', -8, 'DRAWN · 5', [], 'a random draw: the five-beat cycle', 'M11', .01, .1)
    T.drums('found'); fz, cf = f0of(m10['src'], m10['sample_in']); fz = fold(fz); T.sub('sub_Q', fz, 2, '%.1f Hz: the quiet note’s pitch, brought down' % fz); T.pads = ['quiet', 'drawn', 'long', 'kick', 'snare', 'hat', 'sub_Q']
    meet = []
    for q in range(0, 61):
        on = [n for n, per in (('quiet', 3), ('drawn', 5), ('long', 6)) if q % per == 0]; b, bt = qb(q)
        for n in on:
            if q < 60 or n == 'quiet': T.put('full', n, b, bt, 'Recombine: a cycle of %d beats' % {'quiet': 3, 'drawn': 5, 'long': 6}[n], 'beat %d of 60' % q, pan={'quiet': 0, 'drawn': .35, 'long': -.2}[n])
        if len(on) >= 2 and q < 61: meet.append({'beat': q, 'bar': b, 'beat_in_bar': bt, 'cycles': on}); T.put('full', 'kick', b, bt, 'two or more cycles meet here: the meeting is marked', '+'.join(on)); T.subnote('full', 'sub_Q', b, bt)
    for b in range(1, 16): T.beatbar('full', b, k=(), sn=(3,), hats='8', swing=0, hatg=-3)
    scene(T, 'full', 16, 'WHOLE PIECE', 'Three loops of three, five and six beats start together. They meet in mid-bar at beat 30, and meet on a barline only after sixty beats, on bar 16.', decisive='bar 16, beat 1: all three cycles and the barline meet for the first time since the start')
    NOTES[T.id] = {'operator': 'Recombine', 'thesis': 'Cycles of 3, 5 and 6 beats against a 4-beat bar should make the kick, which only marks their meetings, sound composed.', 'falsifier': 'mute DRUMS and SUB: the meetings should still be audible as moments of density', 'measured': meet, 'rejected': None}
    return T
# ------------------------------------------------------------------ 7 · ONE ROOM (Worldbuild)
def room1():
    T = Track('a7-room', 'ONE ROOM', 60, 'made', seed=7); Q = T.BEAT; RM = ('room', 1400, .55); m2, m3, m4, m12 = M['M02'], M['M03'], M['M04'], M['M12']
    a = m2['sample_in']; T.flip('glide2', m2['src'], a, a + S_(1.27), 'primary', -3, 'FALLING', [('gain', 12), RM], 'a quiet falling glide, raised and put in the room', 'M02', .01, .3, seed=60)
    a = m3['sample_in']; T.flip('hole', m3['src'], a, a + S_(2.45), 'support', -7, 'THE HOLE', [RM], 'a passage with 1.18 s of silence inside it: the room fills the hole', 'M03', .01, .3, seed=60)
    a = m4['sample_in']; T.flip('stop', m4['src'], a, a + S_(1.2), 'support', -10, 'THE STOP', [RM], 'a second source that stops dead; in the same room its stop rings like the first', 'M04', .01, .3, seed=60)
    a = m12['sample_in'] + Q; T.flip('radio', m12['src'], a, a + S_(1.5), 'texture', -8, 'BROADCAST', [('bp', 500, 2800), RM], 'a random draw, narrowed to a small speaker: the broadcast that interrupts', 'M12', .02, .3, seed=60)
    T.drums('made'); K = made_kit()
    for n in ('kick', 'snare'): y = fx(wav_read('%s/clips/%s.wav' % (T.dir, n)), [RM], 60); T.raw(n, y * .9 / np.abs(y).max(), 'drums', T.gain[n] - 2, n.upper(), 'in the same room as everything else', n == 'kick')
    fz = fold(596.0); T.sub('sub_R', fz, 3, '%.1f Hz: the glide’s starting pitch, brought down' % fz); base(T, -30); T.pads = ['glide2', 'hole', 'stop', 'radio', 'kick', 'snare', 'sub_R']
    for b in range(1, 17):
        halted = 6 <= b <= 8
        if not halted: T.put('full', 'kick', b, 1, 'the shared pulse', ''); T.subnote('full', 'sub_R', b, 1)
        if not halted and b > 2: T.put('full', 'snare', b, 3, 'the shared pulse', '', -4)
        if b % 2 == 1: T.put('full', 'glide2', b, 2, 'one voice in the room', '', pan=-.3)
        if b in (2, 4, 10, 12, 14): T.put('full', 'hole', b, 1.5, 'its silence is now the room’s', '', pan=.3)
        if b in (4, 12, 16): T.put('full', 'stop', b, 4, 'a second world, same walls', '', pan=-.15)
        T.put('full', 'hiss', b, 1, 'air')
    T.put('full', 'radio', 5, 2, 'Worldbuild: the broadcast arrives', ''); T.put('full', 'radio', 15, 2.5, 'the broadcast, remembered: quieter', '', -7, pan=.4)
    scene(T, 'full', 16, 'WHOLE PIECE', 'Four sources that never met, in one room. A broadcast arrives in bar 5, and the pulse stops for three bars because of it.', decisive='bar 6, beat 1: the first bar with no kick, after the broadcast')
    NOTES[T.id] = {'operator': 'Worldbuild', 'thesis': 'One shared room and one shared pulse should make four unrelated sources sound like one place, and the broadcast should feel like an event because the pulse stops after it.', 'falsifier': 'the flips are stored dry as well: replace them and the place should fall apart', 'rejected': None}
    return T
# ------------------------------------------------------------------ 8 · THE CHOIR, REBUILT (Resynthesize)
def rebuilt():
    T = Track('a8-rebuilt', 'THE CHOIR, REBUILT', 72, 'made', seed=8); B = T.BAR; P = 'S29988c'
    for k, a in (('D', 10.12), ('C', 41.62)): T.flip('roar_' + k, P, S_(a), S_(a) + B, 'primary', -5, 'CHOIR ' + k, [], 'the source', 'roar', .015, .06)
    T.cut('roar_out', P, S_(112.0), S_(112.0) + 3 * B, 'primary', -5, 'ENDING', .015, .4, "the source's own ending, as in the first piece", 'tail')
    def resynth(k, f1):   # a bank of sines on the harmonics of f1, each given the level the choir has at that frequency, frame by frame
        y = wav_read('%s/clips/roar_%s.wav' % (T.dir, k)).mean(1); f, tt, Z = signal.stft(y, SR, nperseg=4096, noverlap=4096 - 512); A = np.abs(Z); n = len(y); t = np.arange(n) / SR; out = np.zeros(n); rng = np.random.default_rng(8); hs = [h for h in range(4, 40) if 140 < h * f1 < 1300]
        for h in hs:
            b = int(round(h * f1 / (SR / 4096))); env = A[b - 1:b + 2].max(0); e = np.interp(t, tt, env); out += e * np.sin(2 * np.pi * h * f1 * t + rng.uniform(0, 6.28))
        out = out / np.abs(out).max() * np.abs(y).max(); return np.stack([out, out], 1), len(hs)
    for k, f1 in (('D', 36.4), ('C', 33.05)): y, nh = resynth(k, f1); T.raw('built_' + k, y, 'support', -5, 'REBUILT ' + k, 'synthesis, not the recording: %d sines on the harmonics of %.1f Hz, each following the level the choir has at that pitch. Target: the choir’s pitch and its swell' % (nh, f1))
    T.drums('made'); T.sub('sub_D', 72.8, 3); T.sub('sub_A', 54.85, 1); T.sub('sub_C', 66.1, 2); T.sub('sub_G', 48.55, 2); [T.gain.__setitem__(k, -13) for k in ('sub_D', 'sub_A', 'sub_C', 'sub_G')]; base(T); T.pads = ['roar_D', 'roar_C', 'built_D', 'built_C', 'kick', 'snare', 'hat', 'sub_D', 'sub_C']
    for b in range(1, 17):
        k = 'D' if b % 2 else 'C'; src_on = b <= 8 or b >= 15; syn_on = 5 <= b
        if src_on: T.put('full', 'roar_' + k, b, 1, 'the recording', '', 0 if b <= 4 or b >= 15 else -3)
        if syn_on: T.put('full', 'built_' + k, b, 1, 'Resynthesize: the rebuilt choir', '', -6 if b <= 8 else 0)
        T.beatbar('full', b, k=(1, 2.75, 3.25) if b % 2 else (1, 2.5, 3.75), sn=(2, 4), ghosts=(1.75,) if b % 2 else (3.25,), hats='16', low=b > 2, swing=.14, openhat=4.5 if b % 4 == 0 else None)
        if b > 2:
            if k == 'D': T.subnote('full', 'sub_D', b, 1); T.subnote('full', 'sub_A', b, 4, False)
            else: T.subnote('full', 'sub_C', b, 1); T.subnote('full', 'sub_G', b, 3, False)
        T.put('full', 'hiss', b, 1, 'air')
    T.put('full', 'roar_out', 17, 1, "the album ends as its first piece does: on the source's own ending", ''); T.subnote('full', 'sub_D', 17, 1); T.put('full', 'kick', 17, 1, 'last weight')
    scene(T, 'full', 19, 'WHOLE PIECE', 'The choir, then the choir with a copy built from sine waves, then the copy alone, then the choir again.', decisive='bar 9: the recording is gone and only the rebuilt choir plays')
    y = wav_read(T.dir + '/clips/roar_D.wav').mean(1); z = wav_read(T.dir + '/clips/built_D.wav').mean(1); envf = lambda v: np.sqrt(np.convolve(v ** 2, np.ones(2205) / 2205, 'same'))[::2205]; sp = lambda v: np.log1p(1e3 * np.abs(np.fft.rfft(v))[:4000]); 
    NOTES[T.id] = {'operator': 'Resynthesize', 'thesis': 'At bar 9 the recording leaves and a synthetic copy stays: the listener should still hear the same two chords, and should hear the choir return at bar 15 as a different thing.', 'falsifier': 'mute ANSWER (the rebuilt layer) in bars 5 to 8: if nothing is missed, the copy adds nothing', 'measured': {'envelope_match': round(float(np.corrcoef(envf(y), envf(z))[0, 1]), 2), 'spectrum_match': round(float(np.corrcoef(sp(y), sp(z))[0, 1]), 2)}, 'rejected': None}
    return T
if __name__ == '__main__':
    OUTS = {}
    for fn, labels in ((pickup, {**LN, 'primary': 'GLIDE', 'support': 'TICK+TAIL'}), (late, {**LN, 'primary': 'TREMBLE', 'support': 'DRAWN'}), (clock, {**LN, 'primary': 'CALL', 'support': 'BREATH'}), (remains, {**LN, 'primary': 'CHOIR'}), (sixty, {**LN, 'primary': 'THREE', 'support': 'FIVE', 'texture': 'SIX'}), (room1, {**LN, 'primary': 'GLIDE', 'support': 'STOPS', 'texture': 'RADIO'}), (rebuilt, {**LN, 'primary': 'CHOIR', 'support': 'REBUILT'})):
        T = fn(); OUTS[T.id] = T.finish(labels, None)
    json.dump(NOTES, open('album_notes.json', 'w'), indent=1, default=float)
