# ET TU, BRUTE · BOXES ON MY BACK, third revision: same motif and form, new drums (two kits to compare) and a new sub.
from build2 import *
PRIM, SUP = 'S29988c', 'Sd3ac86'; S_ = lambda sec: int(round(sec * SR))
def boxes(tid, kit):
    T = Track(tid, 'ET TU, BRUTE · BOXES ON MY BACK', 72, kit, seed=72); B = T.BAR
    for n, a, L, bl, note in [('roar_D', 10.12, B, 'MOTIF 1', 'one bar: D held three beats, then A'), ('roar_C', 41.62, B, 'MOTIF 2', 'one bar: C, then G on beat 4'), ('roar_D2', 48.72, B, 'MOTIF 3', 'second take of the D-to-A bar'), ('roar_long', 107.66, 3 * T.BEAT, 'MOTIF 4', 'the loudest, steadiest D in the source')]: T.cut(n, PRIM, S_(a), S_(a) + L, 'primary', -5, bl, .015, .06, note, 'primary motif')
    T.cut('roar_out', PRIM, S_(112.0), S_(112.0) + 3 * B, 'primary', -5, 'ENDING', .015, .4, "the source's own ending", 'tail'); T.cut('answer_A', SUP, 6349090, 6349090 + B, 'support', -2, 'ANSWER', .004, .3, 'one struck A (110.8 Hz) falling 39 dB in a bar', 'answer / tail')
    T.drums(kit); T.sub('sub_D', 72.8, 3, '72.8 Hz, measured in the motif'); T.sub('sub_A', 54.85, 1, '54.85 Hz'); T.sub('sub_C', 66.1, 2, '66.1 Hz'); T.sub('sub_G', 48.55, 2, '48.55 Hz')
    T.raw('riser', riser(B, T.rng), 'texture', -17, 'RISER'); T.raw('hiss', hiss(B, T.rng), 'texture', -26, 'AIR')
    T.pads = ['roar_D', 'roar_C', 'roar_D2', 'roar_long', 'answer_A', 'kick', 'snare', 'hat', 'sub_D', 'sub_A', 'sub_C', 'sub_G']
    KA, KB, KH = (1, 2.75, 3.25), (1, 2.5, 3.75), (1, 1.75, 2.75, 3.25)
    def bar(sc, b, kind, low=True, prim='auto', fill=False, hats='16', kick=True, sub=True, sn=(2, 4), subg=0, kg=0, air=True):
        pk = kind if kind in 'AB' else 'A'
        if prim == 'auto': prim = 'roar_D' if pk == 'A' else 'roar_C'
        if prim: T.put(sc, prim, b, 1, 'the motif: carries the bar', 'pitch-stable phrase of the primary source')
        T.beatbar(sc, b, k={'A': KA, 'B': KB, 'H': KH}[kind] if kick else (), sn=sn, ghosts=((1.75,) if pk == 'A' else (3.25,)) + ((4.5, 4.75) if fill else ()), hats=hats, low=low, openhat=4.5 if (pk == 'B' and not fill and hats) else None, kg=kg)
        if low and sub:
            if pk == 'A': T.subnote(sc, 'sub_D', b, 1, gain=subg); T.subnote(sc, 'sub_A', b, 4, False, subg)
            else:
                T.subnote(sc, 'sub_C', b, 1, gain=subg)
                if not fill: T.subnote(sc, 'sub_G', b, 3, False, subg)
        if air: T.put(sc, 'hiss', b, 1, 'air')
    ans = lambda sc, b, g=0: T.put(sc, 'answer_A', b, 4, 'answers the choir where it moves to A', 'pitch class A, 13 cents sharp, corrected', g, pitch=-.16)
    def brk(sc, b0):
        bar(sc, b0, 'A', subg=-4); T.put(sc, 'riser', b0, 1, 'prepare')
        bar(sc, b0 + 1, 'B', kick=False, sub=False, sn=(4,), low=False, hats='8'); ans(sc, b0 + 1)
        T.put(sc, 'hat', b0 + 2, 2, 'the grid, barely', '', -4); T.put(sc, 'hat', b0 + 2, 4, 'the grid, barely', '', -4); T.put(sc, 'hiss', b0 + 2, 1, 'air, so the empty bar is not digital silence')
        bar(sc, b0 + 3, 'A', prim='roar_long', subg=2, kg=2)
    for b in range(1, 9): bar('proof', b, 'AB'[(b - 1) % 2], low=b >= 5, hats='8' if b < 5 else '16', fill=b == 8)
    [ans('proof', b, -4 if b < 5 else 0) for b in (1, 3, 5, 7)]; T.scenes['proof'] = {'bars': 8, 'label': 'EIGHT BARS', 'say': 'Eight bars. The low end is held back until bar 5.'}
    bar('break', 1, 'A'); bar('break', 2, 'B'); brk('break', 3); bar('break', 7, 'A', prim='roar_D2'); bar('break', 8, 'B', fill=True); T.scenes['break'] = {'bars': 8, 'protected': [5], 'label': 'THE BREAK', 'say': 'The break: prepare, take the sub away, leave bar 5 clear for “Et tu, Brute?”, bring the weight back on bar 6.'}
    sc = 'full'
    for b in range(1, 5): bar(sc, b, 'AB'[(b - 1) % 2], low=False, hats='8')
    for b in range(5, 13): bar(sc, b, 'AB'[(b - 1) % 2], fill=b in (8, 12))
    brk(sc, 13)
    for b in range(17, 25): bar(sc, b, 'H' if b % 2 else 'B', prim='roar_long' if b % 2 else 'roar_C', fill=b in (20, 24))
    for b in range(25, 33): bar(sc, b, 'AB'[(b - 1) % 2], prim='roar_D2' if b % 2 else 'roar_C', fill=b in (28, 32), hats='16' if b > 26 else None)
    bar(sc, 33, 'A'); T.put(sc, 'roar_out', 34, 1, "the source's own ending"); T.subnote(sc, 'sub_D', 34, 1); T.put(sc, 'kick', 34, 1, 'last weight')
    [ans(sc, b) for b in list(range(5, 13, 2)) + list(range(17, 25, 2)) + list(range(27, 33, 2))]; T.scenes[sc] = {'bars': 36, 'protected': [15], 'label': 'WHOLE TRACK', 'say': 'The whole track: 36 bars, two minutes.'}
    return T, T.finish({'primary': 'ROAR', 'support': 'ANSWER', 'drums': 'DRUMS', 'bass': 'SUB', 'texture': 'AIR'}, None)
if __name__ == '__main__':
    for tid, kit in (('boxes-found', 'found'), ('boxes-made', 'made')): boxes(tid, kit)
