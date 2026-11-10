# 38 SONGS, one per swarm. Each function lays out its mechanism over n bars; ctl=True builds the control branch its defining test asks for.
# The artist names in the briefs are lenses only: nothing here imitates a recording. Titles are the swarms' own experiment names.
import json, sys, numpy as np, random; from swarm_engine import *
ms = lambda v, S=None: int(v * SR / 1000)
def groove(S, sc, n, pat='boom', bass=None, intro=0, K=0, swing=.12, feel=(0, 0, 0), skip=(), hats=None, nobass=()):
    for b in range(1, n + 1):
        if b in skip: continue
        light = b <= intro; alt = b % 2 == 0; fill = (b % 4 == 0)
        P = {'boom': dict(k=(1, 2.5, 3.75) if alt else (1, 2.75, 3.25), sn=(2, 4), hats='16'), 'half': dict(k=(1, 2.5) if not alt else (1, 3.75), sn=(3,), hats='8'), 'sparse': dict(k=(1,), sn=(3,), hats=None), 'four': dict(k=(1, 2, 3, 4), sn=(2, 4), hats='8'), 'drop': dict(k=(3,), sn=(3,), hats='8'), 'none': dict(k=(), sn=(), hats=None)}[pat]
        if hats is not None: P['hats'] = hats or None
        S.kit(sc, b, ghosts=((4.5, 4.75) if fill and pat in ('boom', 'half') else ()), swing=swing, feel=feel, low=not light, K=K, **P)
        if bass and not light and b not in nobass:
            for beat, semis, beats in bass[(b - 1) % len(bass)]: S.bass(sc, b, beat, semis, beats, off=feel[0] if len(feel) < 4 else feel[3])
def shuffled(seq, seed): r = random.Random(seed); q = list(seq); r.shuffle(q); return q
B1 = [[(1, 0, 1.5), (3.25, 0, .75)], [(1, -2, 1.5), (3, 5, 1)]]; B2 = [[(1, 0, 2)], [(1, 0, 1), (2.75, 3, 1.25)]]; WALK = [[(1, 0, 1), (2, 3, 1), (3, 5, 1), (4, 7, 1)], [(1, 8, 1), (2, 7, 1), (3, 5, 1), (4, 3, 1)]]
def m01(S, sc, n, ctl):   # micro-chop syntax: question cells, an interruption, an answer that lands somewhere else
    p = S.set_root(S.pick('phrase')); c = S.cells(p, 5); tk = S.pick('tick'); order = [0, 1, 2, 3, 4]
    for b in range(1, n + 1):
        o = shuffled(order, b + 7) if ctl else order; t = [1, 1.75, 2.5, 3.25, 3.75]   # same times, same cells, same count: only the order differs in the control
        for i, q in enumerate(t): S.put(sc, p, b, q, sl=(c[o[i]][0], min(c[o[i]][1], .42)), pan=(-.3 if i < 2 else .35 if i > 2 else 0), g=(0 if i != 2 else -3), intent=('question' if i < 2 else 'interruption' if i == 2 else 'answer') if not ctl else 'shuffled cell')
        S.put(sc, tk, b, 2.5, g=-2, intent='the cut as punctuation')
    groove(S, sc, n, 'boom', B1, intro=2 if sc == 'song' else 0)
def m02(S, sc, n, ctl):   # relational pocket: three clocks, each late or early by a fixed amount
    p = S.set_root(S.pick('choir', 0)); feel = (0, 0, 0, 0) if ctl else (-ms(8), ms(26), ms(13), ms(18))
    for b in range(1, n + 1): S.put(sc, S.pick('choir', b % 2), b, 1, intent='the phrase: its timing is never moved')
    groove(S, sc, n, 'boom', B2, intro=2 if sc == 'song' else 0, feel=feel, swing=.1); S.notes['offsets_ms'] = {'kick': -8, 'snare': 26, 'hats': 13, 'bass': 18}
def m03(S, sc, n, ctl):   # collage: the splice changes the pulse; the cue returns into a different world
    a, b_, c, cue = S.pick('texture'), S.pick('bed'), S.pick('random'), S.pick('tick'); S.set_root(S.pick('phrase')); h = n // 2
    for b in range(1, n + 1):
        w1 = ctl or b <= h; w2 = ctl or b > h
        if w1 and b % 2: S.put(sc, a, b, 1, g=-2 if ctl else 0, intent='world one')
        if w2: S.put(sc, b_, b, 1, g=1, intent='world two'); S.put(sc, b_, b, 3, g=0, intent='world two')
        if (ctl and b % 2 == 0) or (not ctl and b >= h + n // 4 and b % 2 == 0): S.put(sc, c, b, 2.5, intent='world three: the late entrance', pan=.4)
        if b in (1, 2, h, n) or ctl: [S.put(sc, cue, b, q, g=2, intent='the cue that survives') for q in (1, 1.75, 2.5)]
    if ctl: groove(S, sc, n, 'boom')
    else: groove(S, sc, h, 'boom'); [S.kit(sc, b, k=(1,), sn=(3,), hats='8', swing=0) for b in range(h + 1, n + 1)]   # after the splice the pulse is half-time
def m04(S, sc, n, ctl):   # atmosphere as arrangement: front and rear planes; the room does a drum's job
    S.set_root(S.pick('bass')); t1, t2, tx = S.pick('tail'), S.pick('tail', 1), S.pick('bed')
    for b in range(1, n + 1):
        gap = (b % 4 == 0)
        if not gap: S.bass(sc, b, 1, 0, 1.5); S.bass(sc, b, 3.5, -2 if b % 2 else 3, 1)
        if ctl: S.put(sc, tx, b, 1, g=-3, intent='neutral ambience of equal energy')
        else:
            S.put(sc, t1, b, 2, room=.9, lp=2500, g=-3, pan=-.4, intent='rear plane: a tail in the room')
            if gap: S.put(sc, t2, b, 3, room=1.0, g=3, intent='the atmosphere stands where the snare would')
        S.kit(sc, b, k=(1,), sn=() if (gap and not ctl) else (3,), hats=None)
def m05(S, sc, n, ctl):   # recurrence under loss: four exposures, one dimension at a time; then an intact return
    p = S.set_root(S.pick('choir', 0)); c = S.cells(p, 4); st = [dict(), dict(lp=1100), dict(lp=600, room=.4), dict(lp=380, room=.8, g=4)]; per = max(1, n // 5)
    for b in range(1, n + 1):
        k = min(4, (b - 1) // per)
        if k == 4: S.put(sc, p, b, 1, intent='the return: intact'); continue
        if ctl: [S.put(sc, p, b, 1 + i, sl=(c[j][0], min(c[j][1], S.BEAT / SR)), intent='equally degraded, contour broken', **st[k]) for i, j in enumerate(shuffled(range(len(c)), b))]
        else: S.put(sc, p, b, 1, intent='exposure %d: contour kept' % (k + 1), **st[k])
    groove(S, sc, n, 'sparse', [[(1, 0, 3)], [(1, -2, 2)]])
def m06(S, sc, n, ctl):   # space and reframe: one exposed silence; the bass answers after a delay
    v = S.set_root(S.pick('choir', 2)); bed = S.pick('bed'); hole = S.pick('hole')
    for b in range(1, n + 1):
        ph = (b - 1) % 4
        if ph == 0: S.put(sc, v, b, 1, intent='the fragment'); S.put(sc, bed, b, 1, g=-3)
        if ph == 1: S.put(sc, hole, b, 1, room=.5, intent='a passage that stops by itself')
        if ph == 2:
            if ctl: S.put(sc, bed, b, 1, intent='control: the bed never stops'); S.put(sc, bed, b, 3)
        if ph == 3: S.bass(sc, b, 2.5, 0, 2, intent=None) if False else S.bass(sc, b, 2.5, 0, 2); S.put(sc, bed, b, 3, g=-3)
        if ph != 2: S.kit(sc, b, k=(1,), sn=(), hats=None)
def m07(S, sc, n, ctl):   # prosody as form: a statement, cut, becomes a chorus; one whole utterance survives
    v = S.set_root(S.pick('choir', 3)); c = S.cells(v, 4); br = S.pick('breath'); bed = S.pick('phrase', 1)
    for b in range(1, n + 1):
        if b <= 2 or b == n: S.put(sc, v, b, 1, intent='the whole utterance') if b != 2 else None; continue
        if not ctl: S.put(sc, br, b - 1, 4.5, g=-2, intent='the breath kept before the entry')
        S.put(sc, v, b, 1, sl=(c[0][0], .5)); S.put(sc, v, b, 2.5, sl=(c[0][0], .3)); S.put(sc, v, b, 3, sl=(c[min(2, len(c) - 1)][0], .6), pan=.2); S.put(sc, bed, b, 1, g=-5, lane='texture', intent='the harmonic entry')
    groove(S, sc, n, 'four', B2, skip=(1, 2, n))
def m08(S, sc, n, ctl, seed=1):   # generative recurrence: three unequal cycles and a collision rule
    r = random.Random(seed); snds = [S.pick('tail', seed), S.pick('quiet', seed), S.pick('glide', seed)]; S.set_root(snds[2]); per = [7, 11, 13] if not ctl else [8, 8, 8]; ph = [r.randrange(0, 4) for _ in snds] if not ctl else [0, 2, 5]; taken = {}; ev = []
    for q in range(0, n * 4):
        for i, s_ in enumerate(snds):
            if q >= ph[i] and (q - ph[i]) % per[i] == 0:
                qq, g = q, 0
                while qq in taken: qq += 1; g -= 4      # collision rule: the later sound waits a beat and is 4 dB quieter
                taken[qq] = i
                if qq < n * 4: S.at(sc, s_, qq, g=g + 3, room=.6, pan=(-.4, 0, .4)[i], intent='cycle of %d beats' % per[i]); ev.append((qq, i))
    S.notes.setdefault('events', {})['%s' % sc] = ev
def m09(S, sc, n, ctl):   # radio-play logic: the bed stays; the interruption changes who is speaking
    a, b2, bed = S.set_root(S.pick('choir', 1)), S.pick('phrase', 2), S.pick('bed', 1); h = n // 2 + 1
    for b in range(1, n + 1):
        S.put(sc, bed, b, 1, intent='the bed: unchanged across the cut'); S.put(sc, bed, b, 3)
        if b < h and b % 2: S.put(sc, a, b, 1, pan=-.35, intent='narrator one: close, left')
        if b == h: S.put(sc, a, b, 1, sl=(0, 1.0), pan=-.35, fout=.01, intent='narrator one, cut off mid-phrase'); S.put(sc, S.pick('tick'), b, 2.5, g=3, intent='the cut')
        if b >= h: S.put(sc, S.pick('texture') if ctl else b2, b, 2.75 if b == h else 1 + (b % 2), hp=500, lp=2800, pan=.4, room=.3, g=2, intent='control: a sound, not a voice' if ctl else 'narrator two: a small speaker, right')
    groove(S, sc, n, 'half', B2)
def m10(S, sc, n, ctl):   # time layers: a gesture migrates from an old world to a new one
    old, new = S.set_root(S.pick('choir', 0)), S.pick('glide'); g_ = [1, 2.5, 4]; h = n // 2
    for b in range(1, n + 1):
        fo = 0 if b <= h else -9; fn = -9 if b <= h else 0; hinge = b in (h, h + 1)
        if not ctl or b <= h: [S.put(sc, old, b, q, sl=(0, .7), lp=3000, room=.5, g=fo, pan=-.25, intent='the old trace') for q in g_ if (b <= h or not ctl)]
        if (not ctl and (hinge or b > h or b >= h - 1)) or (ctl and b > h): [S.put(sc, new, b, q, sl=(0, .5), hp=600, g=fn if not hinge else -3, pan=.25, intent='the same gesture in a new timbre') for q in g_]
    groove(S, sc, n, 'boom', B1)
def m11(S, sc, n, ctl):   # long-cycle harmony: three vowels, three lengths; the meetings are the events
    v = [S.set_root(S.pick('phrase', 3)), S.pick('phrase', 4), S.pick('choir', 2)]; per = [4, 4, 4] if ctl else [5, 7, 9]; sh = [0, None, None]; meets = []
    for q in range(n * 4):
        on = [i for i in range(3) if q % per[i] == 0]
        for i in on: S.at(sc, v[i], q, sl=(.5, 1.6), room=.5, pan=(-.4, .4, 0)[i], g=-1, fin=.08, fout=.3, intent='a cycle of %d beats' % per[i])
        if len(on) > 1: meets.append((q, on))
        if q % 8 == 6: S.at(sc, S.pick('breath'), q, g=-4, intent='breath')
    S.notes.setdefault('meetings', {})[sc] = meets
def m12(S, sc, n, ctl):   # environment as performer: the field's own events cue the band
    f = S.pick('texture', 1); S.set_root(S.pick('phrase', 5)); y = clip(f).mean(1); e = np.sqrt(np.convolve(y ** 2, np.ones(4410) / 4410, 'same')); d = np.maximum(0, e[4410:] - e[:-4410]); pk, _ = signal.find_peaks(d, distance=int(.5 * SR)); ev = sorted(pk[np.argsort(d[pk])[-3:]] / SR) if len(pk) else [.5, 1.5, 3]; L = CL[f]['seconds']; band = [S.pick('phrase', 5), S.pick('tick'), S.pick('glide')]; per = int(np.ceil(L / (S.BEAT / SR)))
    for k, q0 in enumerate(range(0, n * 4, per)):
        if ctl: [S.at(sc, f, q0 + i * per / 4, sl=(j * L / 4, L / 4), intent='the field, time-shuffled') for i, j in enumerate(shuffled(range(4), k))]
        else: S.at(sc, f, q0, intent='the field recording')
        for i, t in enumerate(ev): S.at(sc, band[i % 3], q0 + round(t / (S.BEAT / SR) * 4) / 4, sl=(0, .9), g=1, pan=(-.3, 0, .3)[i % 3], intent='enters on a field event at %.2f s' % t)
    S.notes['field_events_s'] = [round(float(t), 2) for t in ev]; groove(S, sc, n, 'sparse', [[(1, 0, 2)]], hats='')
def m13(S, sc, n, ctl):   # minimal syncopation: three voices and a protected rest
    br, dr, tone = S.pick('breath'), S.pick('tick'), S.set_root(S.pick('phrase', 6))
    for b in range(1, n + 1):
        rest = b % 2 == 0
        if not rest or ctl: S.put(sc, S.pick('kick'), b, 1, intent='control: the rest is filled' if rest else 'kick')
        [S.put(sc, dr, b, q, g=4) for q in (2, 3.5)]; S.put(sc, br, b, 2.75, g=2, pan=-.3); S.put(sc, br, b, 4.5, g=0, pan=-.3)
        S.put(sc, tone, b, 1.75, sl=(.2, .16), g=3, pan=.3, intent='the hook: it answers the missing downbeat'); S.put(sc, tone, b, 4, sl=(.2, .16), g=1, pan=.3, shift=S.tune(tone) + (5 if rest else 0))
def m14(S, sc, n, ctl):   # one figure, two palettes: an accent is handed across the seam
    warm, cold, tk = S.set_root(S.pick('choir', 0)), S.pick('glide', 1), S.pick('tick', 2); acc = [1, 1.75, 2.5, 4]; h = n // 2
    for b in range(1, n + 1):
        for q in acc:
            hand = (b == h and q == 4 and not ctl); first = b <= h and not hand
            if first: S.put(sc, warm, b, q, sl=(.1, .4), intent='the figure, warm')
            else: S.put(sc, cold, b, q, sl=(.1, .3), hp=800, g=2, intent='the figure, bright' + (': handed across the seam one accent early' if hand else '')); S.put(sc, tk, b, q, g=-2)
    groove(S, sc, h, 'boom', B1); groove(S, sc, 0, 'four'); [S.kit(sc, b, k=(1, 2, 3, 4), sn=(2, 4), hats='16', swing=0, K=1) for b in range(h + 1, n + 1)]; [S.bass(sc, b, 1, 0, 1) or S.bass(sc, b, 2.5, 0, .5) for b in range(h + 1, n + 1)]
def m15(S, sc, n, ctl):   # understatement: the line, then a dry reply in the space cleared for it
    v, obj, bed = S.set_root(S.pick('choir', 2)), S.pick('tick', 3), S.pick('bed', 2)
    for b in range(1, n + 1):
        ph = (b - 1) % 4
        if ph in (0, 3): S.put(sc, bed, b, 1, g=-2); S.put(sc, bed, b, 3, g=-2)
        if ph == 1: S.put(sc, v, b, 1, intent='the line, with nothing under it')
        if (ph == 2 and not ctl) or (ph == 0 and ctl): S.put(sc, obj, b, 2.5 if not ctl else 4.5, g=5, intent='the reply: dry, small, ' + ('after the line' if not ctl else 'control: before it'))
        if ph in (0, 3): S.kit(sc, b, k=(1,), sn=(3,), hats='8')
def m16(S, sc, n, ctl):   # montage: three scenes, a shared pickup at each seam, a reprise in a new position
    A, Bx, C = S.pick('texture', 2), S.pick('bed', 1), S.set_root(S.pick('glide')); L = max(2, n // 3); order = [1, 2, 0] if ctl else [0, 1, 2]
    for b in range(1, n + 1):
        scn = order[min(2, (b - 1) // L)]; seam = (b % L == 0) and b < n
        if scn == 0: (b - 1) % 2 == 0 and S.put(sc, A, b, 1, intent='scene one'); S.kit(sc, b, k=(1, 2.75), sn=(2, 4), hats='16')
        if scn == 1: S.put(sc, Bx, b, 1, intent='scene two'); S.put(sc, Bx, b, 3); S.kit(sc, b, k=(1,), sn=(3,), hats='8', K=1); S.bass(sc, b, 1, 0, 2)
        if scn == 2: S.put(sc, C, b, 2, room=.8, intent='scene three'); S.kit(sc, b, k=(1,), sn=(), hats=None, K=2)
        if seam: [S.put(sc, S.pick('snare'), b, q, g=-3, intent='the pickup shared by every seam') for q in (4.5, 4.75)]
    if not ctl: S.put(sc, A, n, 1, room=1.0, lp=1500, g=-4, sl=(0, 2.5), intent='reprise: the opening sound, now far away')
def m17(S, sc, n, ctl):   # low-end hierarchy: the bass is short so the kick and the voice stay readable
    v = S.set_root(S.pick('choir', 2)); ln = 2.0 if ctl else .5
    for b in range(1, n + 1):
        if b % 2: S.put(sc, v, b, 1.5, intent='the voice: its space is kept')
        S.bass(sc, b, 1, 0, ln); S.bass(sc, b, 2.75 if not ctl else 3, 0, ln, g=-1); (b % 2 == 0) and S.bass(sc, b, 4, 3, .5)
    groove(S, sc, n, 'half', None, hats='8'); S.notes['bass_note_beats'] = ln
def m18(S, sc, n, ctl):   # the answer phrase: the flourish waits for the lead
    lead, fl, bed = S.set_root(S.pick('choir', 0)), S.pick('glide'), S.pick('bed', 2); gaps = [3.5, 3.75, 3.25, 3.5]
    for b in range(1, n + 1):
        S.put(sc, lead if b % 2 else S.pick('choir', 1), b, 1, sl=(0, 2.0), intent='the lead phrase'); S.put(sc, bed, b, 1, g=-4)
        if ctl: [S.put(sc, fl, b, q, sl=(.2, .4), g=1, pan=.35, intent='control: the flourish never waits') for q in (1, 2)] if b % 2 else None
        elif b % 2 == 0 or b % 4 == 1: S.put(sc, fl, b, gaps[(b - 1) % 4], sl=(.2, .45), g=2, pan=.35, intent='the answer, after the lead')
    groove(S, sc, n, 'boom', B1, swing=.16)
def m19(S, sc, n, ctl):   # melodic micro-chopping: one cut set, two endings
    p = S.set_root(S.pick('phrase', 8)); c = S.cells(p, 4); bt = S.BEAT / SR
    for b in range(1, n + 1):
        end2 = (b % 2 == 0) and not ctl; seq = [0, 1, 2, 3] if not end2 else [0, 1, 2, 0]
        for i, j in enumerate(seq): S.put(sc, p, b, 1 + i, sl=(c[j % len(c)][0], bt * 1.02), shift=S.tune(p) + (-2 if (end2 and i == 3) else 0), fin=.03, fout=.03, intent='ending two: the first cell returns, a tone lower' if (end2 and i == 3) else 'cell %d' % (j + 1))
    groove(S, sc, n, 'boom', B2, swing=.14)
def m20(S, sc, n, ctl):   # one hit becomes a kit
    h = S.pick('tail', 2); S.set_root(S.pick('phrase', 2))
    for b in range(1, n + 1):
        if ctl: S.kit(sc, b, k=(1, 2.75), sn=(2, 4), hats='8', swing=0)
        else:
            [S.put(sc, h, b, q, sl=(0, .35), lp=160, g=8, lane='drums', intent='kick role: the hit below 160 Hz') for q in (1, 2.75)]; [S.put(sc, h, b, q, sl=(0, .22), hp=900, g=2, lane='drums', intent='snare role: the same hit above 900 Hz') for q in (2, 4)]
            [S.put(sc, h, b, 1 + i / 2, sl=(0, .05), hp=5000, g=4, pan=.15, lane='drums', intent='hat role: its first 50 ms above 5 kHz') for i in range(8)]
            if b % 4 == 0: [S.put(sc, h, b, 4 + i / 4, sl=(0, .12), hp=900, g=-2 + i, lane='drums', intent='fill') for i in range(1, 4)]
        if b % 2: S.put(sc, S.pick('phrase', 2), b, 1, g=-2)
        S.bass(sc, b, 1, 0, 1)
def m21(S, sc, n, ctl):   # dense montage: turns, and one overlap that is an event
    lead, hook, acc = S.set_root(S.pick('choir', 3)), S.pick('phrase', 6), S.pick('call'); ov = n - n // 4
    for b in range(1, n + 1):
        both = ctl or b == ov
        if b % 2 or both: S.put(sc, lead, b, 1, sl=(0, 2.4), pan=-.3, intent='the lead takes its turn')
        if b % 2 == 0 or both: S.put(sc, hook, b, 1 if not both else 1.5, sl=(0, 2.0), pan=.3, g=1, intent='the overlap: both at once, once' if (both and not ctl) else 'the hook takes its turn')
        S.put(sc, acc, b, 4.5, g=-2, intent='the third voice, reduced to one accent')
    groove(S, sc, n, 'four', B1, swing=0)
def m22(S, sc, n, ctl):   # timbre as glue: a shadow cue in a slot the drums leave open
    sh, br = S.pick('tail', 3), S.set_root(S.pick('glide', 1)); spots = [2.5, 1.5, 3, 2]
    for b in range(1, n + 1):
        S.put(sc, S.pick('tick', 1) if ctl else sh, b, 4, lp=0 if ctl else 500, g=2 if ctl else 5, room=0 if ctl else .5, intent='control: a neutral cue of the same weight' if ctl else 'the shadow: always on four')
        if b > 1: S.put(sc, br, b, spots[b % 4], sl=(0, .7), hp=1000, g=2, pan=.3 if b % 2 else -.3, intent='the bright sound moves against it')
        S.kit(sc, b, k=(1, 2.75), sn=(2,), hats='8'); S.bass(sc, b, 1, 0, 2)
def m23(S, sc, n, ctl):   # the one is an agreement: parts diverge, and land together
    parts = [(S.pick('tick'), 3, 0), (S.pick('tick', 1), 5, .3), (S.pick('call'), 7, -.3)]; st = S.set_root(S.pick('phrase', 7))
    for b in range(1, n + 1, 2):
        for i, (c_, per, pan) in enumerate(parts):
            for k in range(0, 32, per):
                q = (k + (i + 1 if ctl else 0)) / 4       # control: same hits, each part shifted so nothing lands together
                if q < 8: S.at(sc, c_, (b - 1) * 4 + q, g=1 if k == 0 else -2, pan=pan, intent='a part with its own count of %d' % per)
        S.put(sc, st, b, 1 if not ctl else 1.5, sl=(0, .5), g=2, intent='the shared landing' if not ctl else 'no shared landing')
        for bb in (b, b + 1):
            if bb > n: continue
            S.kit(sc, bb, k=(1,) if bb == b else (2.5,), sn=(), hats=None)
            if not (bb == n - 1): S.bass(sc, bb, 1 if bb == b else 2.5, 0, 1)     # the bass is taken out on one return
def m24(S, sc, n, ctl):   # a break has grammar: pickup, ghosts, reset, and a family of fills
    S.set_root(S.pick('phrase', 1)); fills = [((4, 4.5, 4.75), ()), ((3.75, 4.5), (4.25,)), ((4.25, 4.75), (3.5,)), ((3.5, 4, 4.5, 4.75), ())]
    for b in range(1, n + 1):
        f = fills[(b // 2 - 1) % 4] if b % 2 == 0 else None
        S.kit(sc, b, k=(1, 2.75) if not f else (1, 2.5), sn=(2, 4) if not f else (2,), ghosts=(1.75, 3.25), hats='8', swing=.1)
        if f: [S.put(sc, S.pick('snare'), b, q, g=-2) for q in f[0]]; [S.put(sc, S.pick('kick'), b, q, g=-3) for q in f[1]]
        if not ctl and b < n: [S.put(sc, S.pick('hat'), b, q, g=3, intent='the pickup into the next bar') for q in (4.75,)]; S.put(sc, S.pick('tick'), b, 4.5, g=0, intent='the pickup')
        if b % 4 == 1: S.put(sc, S.pick('phrase', 1), b, 1, g=-3)
        S.bass(sc, b, 1, 0, 1)
def m25(S, sc, n, ctl):   # the exclamation is a drum
    ex, resp = S.pick('call'), S.set_root(S.pick('choir', 3)); sub_ = S.pick('tick', 4)
    for b in range(1, n + 1):
        inv = b % 4 == 0
        for q in ((2.5, 4) if not inv else (2.5,)): S.put(sc, sub_ if ctl else ex, b, q, g=2, intent='control: a drum in its place' if ctl else 'the exclamation, as percussion')
        if b % 4 == 1 and b > 1: S.put(sc, sub_ if ctl else ex, b, 1, g=4, intent='after the pause: the exclamation on the one')
        if b % 4 == 2: S.put(sc, resp, b, 1, sl=(0, 2.2), g=-1, intent='the longer response')
        S.kit(sc, b, k=(1, 3.25) if not inv else (1,), sn=(2,) if not inv else (2,), hats='16' if not inv else '8'); S.bass(sc, b, 1, 0, 1.5)
def m26(S, sc, n, ctl):   # density around a statement
    st, t1, t2 = S.set_root(S.pick('choir', 2)), S.pick('texture', 2), S.pick('random'); 
    for b in range(1, n + 1):
        say = b % 2 == 1
        if say: S.put(sc, st, b, 1, g=2, intent='the statement')
        if ctl or not say: S.put(sc, t1, b, 1, sl=(0, 2.6), g=0 if not ctl else -3, pan=-.4, intent='a layer that falls silent under the statement: it agrees' if not ctl else 'control: constant')
        if ctl or not say: [S.put(sc, t2, b, q, sl=(.2, .35), g=2 if not ctl else -1, pan=.4, intent='a layer that interrupts in the gaps: it argues') for q in ((2, 2.75, 3.5, 4.25) if not ctl else (2, 3.5))]
        if ctl and say: S.put(sc, t2, b, 2.75, sl=(.2, .35), g=-1, pan=.4); S.put(sc, t2, b, 4.25, sl=(.2, .35), g=-1, pan=.4)
    groove(S, sc, n, 'boom', B1, swing=.08)
def m27(S, sc, n, ctl):   # two rooms: each holds a fragment of the other, and one local sign
    a, b2, sign = S.set_root(S.pick('phrase', 3)), S.pick('choir', 1), S.pick('call'); h = n // 2
    for b in range(1, n + 1):
        A = b <= h; cue = S.pick('tick', 2) if ctl else sign
        if A: S.put(sc, a, b, 1, pan=-.4, room=.15, intent='room one: close'); (b == h) and S.put(sc, b2, b, 3, sl=(0, .6), g=-6, room=.9, pan=.4, intent='a fragment of the other room, heard through the wall')
        else: S.put(sc, b2, b, 1, pan=.4, room=.8, g=-1, intent='room two: large'); (b == n) and S.put(sc, a, b, 3, sl=(0, .6), g=-6, pan=-.4, intent='a fragment of the first room')
        S.put(sc, cue, b, 4, g=1, room=.15 if A else .8, intent='the shared sign' if not ctl else 'control: a generic cue')
        S.kit(sc, b, k=(1, 2.75) if A else (1,), sn=(3,), hats='8' if A else None, K=0 if A else 1); S.bass(sc, b, 1, 0 if A else 5, 2)
def m28(S, sc, n, ctl):   # negative space: two parts designed around each other
    pk, hk = S.pick('tick', 1), S.set_root(S.pick('phrase', 6)); A = [1, 2.75, 4.5] if not ctl else [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]; H = [1.75, 3.5] if not ctl else [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
    for b in range(1, n + 1):
        [S.put(sc, S.pick('kick') if q == 1 else pk, b, q, g=0 if q == 1 else 3, pan=-.2, intent='the pocket') for q in A]; [S.put(sc, hk, b, q, sl=(.15, .22), g=2, pan=.25, shift=S.tune(hk) + (0 if i % 2 == 0 else 3), intent='the hook, in the gaps the pocket leaves') for i, q in enumerate(H)]
        S.put(sc, S.pick('snare'), b, 3, g=-1); S.bass(sc, b, 1, 0, .5); S.bass(sc, b, 2.75, 0, .5, g=-2)
def m29(S, sc, n, ctl):   # the counterline: a small answer moving the other way
    lead, acc = S.set_root(S.pick('choir', 0)), S.pick('phrase', 4)
    for b in range(1, n + 1):
        S.put(sc, lead, b, 1, sl=(0, 1.9), intent='the lead: a gap after its first cadence')
        if not ctl: [S.put(sc, acc, b, q, sl=(.2, .3), g=-3, pan=.35, shift=S.tune(acc) - i * (2 if i < 2 else 1.5), intent='the counterline: stepping down while the lead rises') for i, q in enumerate((3, 3.5, 4))]
    groove(S, sc, n, 'boom', B2)
def m30(S, sc, n, ctl):   # a persona between worlds: the take never changes; the room does
    v, w1, w2, cue = S.set_root(S.pick('choir', 2)), S.pick('bed'), S.pick('texture', 1), S.pick('tick', 3); h = n // 2
    for b in range(1, n + 1):
        A = b <= h
        if b % 2: S.put(sc, v, b, 1, **({} if (A or ctl) else dict(room=1.0, lp=2400, g=-5, pan=.3)), intent='the same take: close' if A else ('control: still close' if ctl else 'the same take: across a large room'))
        (S.put(sc, w1, b, 1, g=-2), S.put(sc, w1, b, 3, g=-2)) if A else (b % 2 and S.put(sc, w2, b, 1, room=.4))
        [S.put(sc, cue, b, q, g=1, intent='the cue that does not change') for q in (2.5, 4.25)]; S.kit(sc, b, k=(1,), sn=(3,) if A else (), hats=None); S.bass(sc, b, 1, 0 if A else -4, 2)
def m31(S, sc, n, ctl):   # an ensemble that makes space: the bass rests, and the second voice answers in the rest
    v1, v2, br = S.set_root(S.pick('choir', 0)), S.pick('phrase', 6), S.pick('tick', 4)
    for b in range(1, n + 1):
        ph = (b - 1) % 4; rest = ph == 1
        for beat, semis, beats in WALK[b % 2]:
            if not (rest and beat >= 3): S.bass(sc, b, beat, semis, .9)
        if ph == 0: S.put(sc, v1, b, 1, room=.3, pan=-.3, intent='first voice')
        if (ph == 1 and not ctl): S.put(sc, v2, b, 3, sl=(0, 1.6), room=.3, pan=.3, intent='second voice: enters in the gap the bass leaves')
        if (ph == 0 and ctl): S.put(sc, v2, b, 1.5, sl=(0, 1.6), room=.3, pan=.3, intent='control: second voice on top of the first')
        [S.put(sc, br, b, q, g=-1) for q in (2, 4)]; S.put(sc, S.pick('hat'), b, 2.5); S.put(sc, S.pick('hat'), b, 4.5)
def m32(S, sc, n, ctl):   # the bass line carries the conversation
    v1, v2 = S.set_root(S.pick('choir', 1)), S.pick('phrase', 3); line = [(1, 0, .75), (1.75, 3, .5), (2.5, 5, 1), (3.75, 7, .75)]
    for b in range(1, n + 1):
        [S.bass(sc, b, beat, 0 if ctl else (semis if b % 2 else (7 - semis)), beats) for beat, semis, beats in line]
        if b % 4 == 1: S.put(sc, v1, b, 1.5, pan=-.25, intent='first entry')
        if b % 4 == 3: S.put(sc, v2, b, 2, sl=(0, 2), pan=.25, intent='second entry')
    groove(S, sc, n, 'boom', None, swing=.14)
def m33(S, sc, n, ctl):   # a hook to hand to a room: a call, a cue, and a crowd made of the same call
    call, ph, br = S.pick('call'), S.set_root(S.pick('choir', 2)), S.pick('breath', 1)
    for b in range(1, n + 1):
        if b % 2: S.put(sc, call, b, 1, g=3, intent='the call'); S.put(sc, ph, b, 1.5, sl=(0, 1.2), g=-1, intent='the call')
        else:
            if not ctl: S.put(sc, br, b - 1, 4.5, g=3, intent='the cue to come in: a breath')
            for i, (pan, det, d) in enumerate(((-.6, -.2, 0), (.6, .25, ms(14)), (0, 0, ms(7)), (-.3, .12, ms(22)), (.3, -.1, ms(18)))): S.put(sc, call, b, 1, g=-2, pan=pan, shift=det, off=d, room=.3, intent='the room answers: the same call, five times, spread and slightly apart'); S.put(sc, ph, b, 1.5, sl=(0, 1.2), g=-6, pan=pan, shift=S.tune(ph) + det, off=d, room=.3)
    groove(S, sc, n, 'four', B2, swing=0)
def m34(S, sc, n, ctl):   # voicing as tension: one inner voice moves through a still chord
    v = [S.set_root(S.pick('phrase', 3)), S.pick('phrase', 4), S.pick('choir', 2)]; inner = [0, 1, 2, 0]; 
    for b in range(1, n + 1, 2):
        k = ((b - 1) // 2) % 4; mv = inner[k]
        for i, c_ in enumerate(v):
            base = S.tune(c_) + (0, 4, 7)[i] * 0
            sh = base + ((mv if i == 1 else 0) if not ctl else mv)    # control: every voice moves in parallel
            S.put(sc, c_, b, 1, sl=(.3, 2 * S.BAR / SR * .8), shift=sh, room=.5, pan=(-.4, 0, .4)[i], fin=.15, fout=.02, g=-1, intent='inner voice: moves a step' if i == 1 else 'outer voice: holds')
        S.put(sc, S.pick('breath'), b + 1, 3.75, g=-2, intent='the common breath'); S.bass(sc, b, 1, 0, 3, g=-3)
def m35(S, sc, n, ctl):   # the room makes the line uneasy: a long tail just before the line
    v, obj = S.set_root(S.pick('choir', 3)), S.pick('tail', 1)
    for b in range(1, n + 1):
        ph = (b - 1) % 4
        if ph == 1: S.put(sc, v, b, 1, intent='the line: close and dry')
        if (ph == 0 and not ctl): S.put(sc, obj, b, 3.5, room=1.2, lp=3000, g=3, pan=.4, intent='the object, in a large room, just before the line')
        if (ph == 2 and ctl): S.put(sc, obj, b, 1.5, room=1.2, lp=3000, g=3, pan=.4, intent='control: just after the line')
        if ph == 3: S.bass(sc, b, 1, 0, 3, g=-2); S.kit(sc, b, k=(1,), sn=(), hats=None)
def m36(S, sc, n, ctl):   # the slow phrase is an anchor: a faster rhythm crosses its cadence
    a, b2, tk = S.set_root(S.pick('choir', 0)), S.pick('choir', 1), S.pick('tick', 2); bt = S.BEAT / SR
    for b in range(1, n + 1):
        c_ = a if b % 2 else b2
        if ctl: S.put(sc, c_, b, 1, intent='the phrase, uncut')
        else: S.put(sc, c_, b, 1, sl=(0, 2.4 * bt * S.bpm / 72), fout=.03, intent='the stable part'); S.put(sc, c_, b, 3.5, sl=(2.5 * 60 / 72, 1.0), fin=.02, intent='the turn, entering half a beat late: the foreground crosses here')
        [S.put(sc, tk, b, 1 + i * .75, g=1 if i % 4 == 0 else -2, pan=.25, intent='the faster foreground: every three sixteenths') for i in range(6) if 1 + i * .75 < 5]
    groove(S, sc, n, 'half', [[(1, 0, 3)], [(1, -2, 2), (3, 5, 1)]], hats='')
def m37(S, sc, n, ctl):   # the meter teaches the ear: ten pulses, grouped 3+3+2+2 or 2+2+3+3
    tk, kk, p = S.pick('tick'), S.pick('kick'), S.set_root(S.pick('phrase', 7)); grp = [0, 2, 4, 7] if ctl else [0, 3, 6, 8]; cyc = n * 8 // 10
    for c_ in range(cyc):
        for i in range(10):
            q = (c_ * 10 + i) / 2
            S.at(sc, tk, q, g=3 if i in grp else -3, intent='pulse'); 
            if i in grp: S.at(sc, kk, q, g=0 if i == 0 else -4, intent='group start'); S.bass(sc, 1 + int(q // 4), 1 + q % 4, 0 if i == 0 else (7 if i == grp[2] else 3), .5) if i in (grp[0], grp[2]) else None
        if c_ >= 2: S.at(sc, p, (c_ * 10 + (grp[1] if c_ % 2 else grp[2])) / 2, sl=(0, .8), g=-1, intent='a phrase moved across the grouping boundary')
    S.notes['grouping'] = '2+2+3+3' if ctl else '3+3+2+2'
def m38(S, sc, n, ctl, seed=1):   # the spoken cut: clauses in a seeded order
    a, b2 = S.set_root(S.pick('choir', 2)), S.pick('choir', 0); cl = [(a, x) for x in S.cells(a, 3)] + [(b2, x) for x in S.cells(b2, 3)]; seq = list(range(len(cl))) if ctl else shuffled(range(len(cl)), seed * 13); q = 0; order = []
    while q < n * 4 - 3:
        for j in seq:
            c_, (st, ln) = cl[j]; ln = min(ln, 1.6)
            if q >= n * 4 - 2: break
            S.at(sc, c_, q, sl=(st, ln), room=.5 if j % 2 else .15, pan=-.3 if c_ == a else .3, fout=.04, intent='clause %d of %s' % (j % 3 + 1, 'the first utterance' if c_ == a else 'the second')); order.append(j); q += max(2, round(ln / (S.BEAT / SR) * 2) / 2 + .5)
    S.notes.setdefault('order', {})[sc] = order[:12]
    for b in range(1, n + 1): S.put(sc, S.pick('tick', 3), b, 1, g=-4)
SW = [(1, 'cut-answers', 'THE CUT ANSWERS BACK', 'micro-chop syntax', 90, m01), (2, 'three-clocks', 'THREE CLOCKS IN ONE ROOM', 'relational pocket', 86, m02), (3, 'wrong-turn', 'THE PRODUCTIVE WRONG TURN', 'collage as discovery', 80, m03), (4, 'floor-plan', 'DREAD HAS A FLOOR PLAN', 'atmosphere as arrangement', 66, m04), (5, 'threshold', 'THE RECOGNITION THRESHOLD', 'recurrence under loss', 72, m05), (6, 'room-document', 'THE ROOM AROUND THE DOCUMENT', 'space and contextual reframe', 60, m06), (7, 'sentence-chorus', 'THE HUMAN SENTENCE BECOMES A CHORUS', 'prosody as form', 104, m07), (8, 'rule', 'THE RULE MAKES THE MUSIC', 'generative recurrence', 60, m08), (9, 'narrator', 'THE INTERRUPTION CHANGES THE NARRATOR', 'radio-play logic', 84, m09), (10, 'audible-past', 'A FUTURE WITH AN AUDIBLE PAST', 'time layers in one groove', 88, m10),
      (11, 'one-breath', 'A CHOIR BUILT FROM ONE BREATH', 'long-cycle vocal harmony', 70, m11), (12, 'landscape', 'THE LANDSCAPE JOINS THE BAND', 'environment as a performer', 76, m12), (13, 'missing-downbeat', 'THE MISSING DOWNBEAT IS THE HOOK', 'minimal syncopation', 96, m13), (14, 'clothes', 'A GROOVE THAT CHANGES ITS CLOTHES', 'translation between palettes', 92, m14), (15, 'understatement', 'THE UNDERSTATEMENT LANDS', 'conversation, timing and scale', 70, m15), (16, 'scene-cut', 'THE SPLICE IS A SCENE CUT', 'instrumental montage', 84, m16), (17, 'room-for-voice', 'THE BASS LEAVES ROOM FOR THE VOICE', 'low-end and lead hierarchy', 80, m17), (18, 'horn-remembers', 'THE HORN REMEMBERS THE VERSE', 'answer phrase and warm pocket', 88, m18), (19, 'seam-sings', 'THE SEAM SINGS', 'melodic micro-chopping', 82, m19), (20, 'one-hit-kit', 'ONE HIT BECOMES A KIT', 'percussion extraction', 90, m20),
      (21, 'collision', 'THE COLLISION STILL READS', 'dense montage intelligibility', 100, m21), (22, 'one-shadow', 'ONE SHADOW HOLDS THE SCENE', 'timbre as tonal glue', 78, m22), (23, 'the-one', 'THE ONE IS A SOCIAL AGREEMENT', 'ensemble accents and collective reset', 104, m23), (24, 'break-grammar', 'A BREAK HAS GRAMMAR', 'pickup and break continuity', 92, m24), (25, 'exclamation', 'THE EXCLAMATION IS A DRUM', 'vocal interjection as percussion', 98, m25), (26, 'pressure', 'NOISE GIVES THE ARGUMENT PRESSURE', 'density around a statement', 90, m26), (27, 'two-rooms', 'TWO ROOMS, ONE CITY', 'plural viewpoints and situated place', 74, m27), (28, 'negative-space', 'THE POCKET HAS NEGATIVE SPACE', 'paired groove and hook design', 94, m28), (29, 'counterline', 'THE COUNTERLINE HIDES IN PLAIN SIGHT', 'instrumental counterline', 80, m29), (30, 'persona', 'A PERSONA MOVES BETWEEN WORLDS', 'voice and perspective', 72, m30),
      (31, 'space-to-speak', 'THE ENSEMBLE MAKES SPACE TO SPEAK', 'distributed conversational entrances', 88, m31), (32, 'bass-conversation', 'THE BASS LINE CARRIES THE CONVERSATION', 'loop stability and variable phrasing', 90, m32), (33, 'hand-to-room', 'A HOOK YOU CAN HAND TO A ROOM', 'participatory call and response', 100, m33), (34, 'harmony-arrives', 'HARMONY ARRIVES BEFORE THE WORD', 'vocal voicing as tension', 66, m34), (35, 'uneasy-room', 'THE ROOM MAKES THE LINE UNEASY', 'voice against unsettling space', 64, m35), (36, 'slow-anchor', 'THE SLOW PHRASE CAN BE AN ANCHOR', 'slow harmonic motion under cuts', 84, m36), (37, 'meter', 'THE METER TEACHES THE EAR', 'asymmetrical grouping', 100, m37), (38, 'spoken-cut', 'THE SPOKEN CUT CHANGES THE SENTENCE', 'spoken-word and chance montage', 72, m38)]
LN = {'primary': 'LEAD', 'support': 'VOICE', 'drums': 'DRUMS', 'bass': 'BASS', 'texture': 'AIR'}
def build(idx):
    i, slug, title, mech, bpm, fn = SW[idx - 1]; S = Song(i, slug, title, mech, bpm); nsong = 16
    fn(S, 'test', 8, False); S.scene('test', 8, 'THE TEST', 'The defining passage: eight bars with the mechanism in it.')
    S.rng = np.random.default_rng(i * 101); fn(S, 'control', 8, True); S.scene('control', 8, 'THE CONTROL', 'The same eight bars with the one thing taken out or scrambled. If this works as well, the idea failed.')
    if fn in (m08, m38):
        for sd in (2, 3): S.rng = np.random.default_rng(i * 101); fn(S, 'seed%d' % sd, 8, False, seed=sd); S.scene('seed%d' % sd, 8, 'SEED %d' % sd, 'The same rule with another seed.')
    S.rng = np.random.default_rng(i * 101); fn(S, 'song', nsong, False); S.scene('song', nsong + 1, 'THE SONG', '%s: %s.' % (title.capitalize(), mech))
    return S, S.finish(LN, [])
if __name__ == '__main__':
    which = [int(a) for a in sys.argv[1:]] or range(1, 39); rows = []
    for k in which:
        try: S, r = build(k); r['notes'] = S.notes; rows.append(r); print('%-22s %3d bpm %5.1fs level %5.1f crest %4.1f drive %4.2f step %.3f clips %2d src %2d pl %3d low %.2f mono %.2f %s' % (r['id'], r['bpm'], r['seconds'], r['level_dB'], r['crest_dB'], r['drive'], r['edit_step'], r['clips'], r['sources'], r['placements'], r['low_share'], r['mono_loss_dB'], r['lanes']), flush=True)
        except Exception as ex: import traceback; print('FAILED', k, repr(ex)); traceback.print_exc(limit=3)
    if len(rows) > 30: json.dump(rows, open('out3/songs.json', 'w'), indent=1, default=float)
