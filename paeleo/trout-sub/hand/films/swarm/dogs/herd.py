"""THE HERD of "The Dogs of Trouttown": the lead cow, five plain cows and the calf.

Cut-paper puppets for the porch at dusk. The skeleton is the jointed cow of the earlier film
(films/swarm/cowpath/cast.py: the rig, the joint limits, the planted-hoof walk); what is made new here is
everything you see and everything they do in this film:

  * the material: one dark plum-brown card for the whole herd, dim bone patches (a different map on every
    cow), a hard paper edge under each piece and an amber rim on the lamp side only;
  * the lead cow's left horn, recut so that it bends forward and down like a finger and reads in silhouette;
  * a real pendulum for her bell, so it swings late and rings on after she stops;
  * the route down the worn path, through the one gate, along the bank (numbers from porch.py);
  * the performances: file past, wait a turn, touch noses, drink, look down into the water, be turned aside,
    the calf following a dog and being nosed back, walk out on the ice and stamp, stand round wet dogs
    steaming, fold down, lie, sleep, get up.

Nothing here is foraged and there is no lettering. Run `python3 films/swarm/dogs/herd.py` to re-make the
sheets (herd_sheet.png, herd_strip_*.png in this folder) and run the measured checks. See HERD.md.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
for _p in (str(FILMS), str(HERE.parent / "cowpath"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kit import W, H, clamp, lerp, smooth  # noqa: E402
import cast as cc  # noqa: E402  (films/swarm/cowpath/cast.py: the jointed cow)

try:                                    # the set: only its numbers are needed here
    import porch as _porch
except Exception:                       # pragma: no cover  (the herd still works on its own)
    _porch = None

SS = 2                                  # supersampling of every cut-out
SURFACE = 400                           # the bright line
STRIP_Y = 388                           # hooves on the path strip behind the sill
GATE = (304, 346, 330)                  # the two posts and their tops
MEADOW_X = 640
LAMP = (205, 140)
SPEED = 45.0                            # px a second on the strip: the one tempo of the herd

# ------------------------------------------------------------------ the herd ---

CARD = (50, 32, 42)                     # plum-brown card: darker than the hill, darker than any dog
BONE = (158, 138, 128)                  # dim bone
AMBER = (255, 188, 98)
BRASS = (150, 116, 58)                  # a dull bell


def _tones(card, bone=BONE, warm=0.0):
    c = tuple(int(lerp(a, b, warm)) for a, b in zip(card, (96, 62, 56)))
    return dict(hide=c, far=tuple(int(v * 0.68) for v in c), edge=tuple(int(v * 0.5) for v in c),
                patch=bone, horn=(176, 160, 140), udder=(128, 88, 96), hoof=(24, 16, 22), muzzle=(132, 100, 104),
                bell=BRASS, strap=(104, 44, 40), eye=(226, 214, 196), pupil=(18, 12, 16))


# a patch: (piece, cx, cy, rx, ry, seed) in the master cow's standing units (head patches in head-local units)
WHO = dict(
    lead=dict(kind='lead', phase=0.00, k=1.0, tones=_tones((50, 32, 42)), patches=[
        ('barrel', -8, -112, 30, 24, 1), ('hip', -84, -116, 16, 22, 2), ('shoulder', 70, -100, 12, 20, 3),
        ('head', 22, -10, 16, 5, 4)]),
    second=dict(kind='herd', phase=0.37, k=1.0, tones=_tones((56, 34, 40)), patches=[
        ('barrel', 26, -104, 26, 30, 11), ('hip', -60, -84, 20, 16, 12)]),
    mother=dict(kind='herd', phase=0.71, k=0.98, tones=_tones((46, 30, 44)), patches=[
        ('shoulder', 56, -118, 22, 26, 21), ('barrel', -30, -74, 26, 14, 22), ('hip', -86, -124, 14, 12, 23),
        ('head', 30, -6, 12, 6, 24)]),
    calf=dict(kind='calf', phase=0.20, k=1.0, tones=_tones((60, 38, 44), warm=0.25), patches=[
        ('barrel', -20, -116, 24, 18, 31), ('head', 16, -10, 12, 6, 32)]),
    fourth=dict(kind='herd', phase=0.15, k=1.02, tones=_tones((52, 34, 46)), patches=[
        ('hip', -70, -112, 26, 30, 41), ('neck', 100, -128, 16, 10, 42)]),
    fifth=dict(kind='herd', phase=0.55, k=0.96, tones=_tones((58, 36, 42)), patches=[
        ('barrel', 0, -90, 44, 14, 51), ('shoulder', 62, -84, 14, 12, 52)]),
    sixth=dict(kind='herd', phase=0.88, k=1.0, tones=_tones((44, 28, 40)), patches=[
        ('barrel', 34, -124, 18, 12, 61), ('barrel', -28, -100, 14, 18, 62), ('hip', -64, -90, 12, 14, 63)]),
)
HERD = ('lead', 'second', 'mother', 'calf', 'fourth', 'fifth', 'sixth')

# the lead cow's LEFT horn: up from the poll, then bent forward and down like a finger (head-local units)
_CROOK_L = [(3, -13), (3, -23), (8, -31), (20, -35), (32, -34), (39, -28), (41, -19), (39, -12), (35, -13), (35, -21),
            (31, -27), (21, -28), (13, -26), (10, -20), (10, -13)]


def _h(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def _blob(cx, cy, rx, ry, seed, n=14):
    """A torn patch: an oval with an unsteady edge."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 0.78 + 0.44 * _h(seed * 7.3 + i * 1.9)
        out.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return cc._smooth(out, n=3)


def _kind(who):
    return WHO[who]['kind']


def _rig(who):
    return cc.Rig.of(_kind(who))


def _size(who):
    """Pixels per cow unit at s = 1 for this animal (the calf is cut so that s = S makes it dog-height)."""
    return _rig(who).size * WHO[who]['k']


# the strip scale: the lead cow stands 104 px to the withers there (board: "Sizes")
S = 104.0 / -cc.solve(cc.POSES['stand'], 'lead')['anchors']['withers'][1]
WHO['calf']['k'] = 60.0 / (S * cc.Rig.of('calf').size * -cc.solve(cc.POSES['stand'], 'calf')['anchors']['withers'][1])

# ------------------------------------------------------------------ poses ---

LEGS = cc.LEGS
with_ = cc.with_


def _P(**kw):
    return cc._pose(**kw)


def blend(p, q, x, who='lead'):
    """The pose x of the way from p to q (0..1). Planted hooves stay planted; a leg that is planted in one and
    folded in the other turns on its joints."""
    x = clamp(x, -0.3, 1.3)
    if x == 0.0:
        return dict(p)
    if x == 1.0:
        return dict(q)
    out, sp, sq = {}, None, None
    base = cc.POSES['stand']
    for k in set(p) | set(q):
        a, b = p.get(k, base.get(k, 0.0)), q.get(k, base.get(k, 0.0))
        if k in LEGS:
            if a[0] == b[0]:
                out[k] = (a[0], lerp(a[1], b[1], x), lerp(a[2], b[2], x))
            else:
                sp = sp or cc.solve(p, _kind(who))['angles']
                sq = sq or cc.solve(q, _kind(who))['angles']
                out[k] = ('fk', lerp(sp[k][0], sq[k][0], x), lerp(sp[k][1], sq[k][1], x))
        elif k == 'tail':
            out[k] = tuple(lerp(u, v, x) for u, v in zip(a, b))
        else:
            out[k] = lerp(a, b, x)
    return out


def tween(p, q, x, ease='inout', who='lead'):
    """blend() with one of cast's named eases: linear, inout, out, slow, slam, snap, anticip."""
    return blend(p, q, cc.EASES[ease](clamp(x)), who)


def _keys(keys, t, who='lead'):
    """keys [(time, pose, ease_into='inout')] -> the pose at t."""
    if t <= keys[0][0]:
        return dict(keys[0][1])
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            return tween(a[1], b[1], (t - a[0]) / max(b[0] - a[0], 1e-9), b[2] if len(b) > 2 else 'inout', who)
    return dict(keys[-1][1])


def stand(t=0.0, who='lead', chew=1.0, alert=0.0):
    """Standing and waiting her turn. She breathes; she chews (chew 0 = she has stopped chewing: she has noticed
    something); an ear flicks and the tail swishes now and then. alert 0..1 lifts the head and brings the ears
    round. Every cow has her own clock, so a queue never moves in step."""
    o = WHO[who]['phase'] * 17.0
    br = math.sin(2 * math.pi * (t + o) / 3.6)
    ch = chew * (0.5 + 0.5 * math.sin(2 * math.pi * 1.25 * (t + o)))
    fl = max(0.0, math.sin(2 * math.pi * (t + o * 1.7) / 5.3)) ** 14          # an ear flick
    sw = max(0.0, math.sin(2 * math.pi * (t + o * 2.3) / 6.7)) ** 6           # a tail swish
    calf = _kind(who) == 'calf'
    return _P(dy=0.9 + 0.8 * br, neck=(-8.0 if calf else 6.0) - 26.0 * alert + 1.2 * br, head=2.0 + 8.0 * alert + 2.0 * ch * chew,
              jaw=1.0 + 6.0 * ch, ear=(8.0 if calf else -4.0) + 34.0 * alert - 30.0 * fl, eye=1.0 + 0.3 * alert,
              tail=(3.0 + 26.0 * sw * math.sin(9 * t), 6.0 + 30.0 * sw * math.sin(9 * t - 0.9), 8.0 + 34.0 * sw * math.sin(9 * t - 1.8)),
              udder=2.0 * br)


def notice(pose, amount=1.0):
    """She has noticed something: chewing stops, both ears come round, the eye opens, the head lifts a little."""
    amount = clamp(amount)
    q = dict(pose)
    q['jaw'] = lerp(pose.get('jaw', 0.0), 0.5, amount)
    q['ear'] = lerp(pose.get('ear', 0.0), 34.0, amount)
    q['eye'] = lerp(pose.get('eye', 1.0), 1.35, amount)
    q['neck'] = pose.get('neck', 0.0) - 9.0 * amount
    return q


def look_down(t=0.0, p=1.0, who='lead'):
    """On the bank, looking down into the water where she cannot go: fore hooves set at the very edge, the head
    hung out and low, ears forward, not chewing. p 0..1 lowers the head. Pass nose_to= to cow() to hang the
    muzzle over a point."""
    a = stand(t, who, chew=1.0 - clamp(p * 2))
    b = _P(pitch=3.0, dy=1.5, shoulder=4.0, neck=44.0, head=4.0, ear=26.0, eye=1.2, jaw=0.5,
           nf=('ik', 60.0, 0.0), ff=('ik', 66.0, 0.0), tail=(2.0, 3.0, 4.0),
           _nose=1.0)
    q = blend(a, b, smooth(clamp(p)), who)
    q['neck'] += 1.5 * math.sin(2 * math.pi * t / 4.1)
    return q


def drink(t=0.0, p=1.0, who='lead'):
    """Head down to the water, drinking: p 0..1 lowers it; then the throat works (the jaw and ears tick) and the
    tail hangs. Pass nose_to=(x, 400 - oy) to cow() to put the muzzle on the line."""
    a = stand(t, who)
    sip = 0.5 + 0.5 * math.sin(2 * math.pi * 1.6 * t)
    b = _P(pitch=10.0, dy=8.0, shoulder=12.0, neck=64.0, head=-20.0, jaw=2.0 + 4.0 * sip, ear=-10.0 + 6.0 * sip, eye=0.7,
           nf=('ik', 40.0, 0.0), ff=('ik', 78.0, 0.0), tail=(1.0, 2.0, 3.0), _nose=1.0)
    return blend(a, b, smooth(clamp(p)), who)


NOSE_TOUCH = dict(contact=0.75, hold_end=1.55, breath=1.6, away=2.6)      # the same clock as dog.nose_touch(t)


def nose_touch(tau, t=None, who='lead'):
    """Touching noses with a dog. tau is seconds on the dog's clock (dog.nose_touch(tau)): she stops chewing and
    her ears come round (0..0.3), the big head comes down (contact at 0.75), both hold still, nostrils working
    (0.75..1.55), she breathes out (1.6: pose['_breath'] runs 0..1 for herd.breath), lifts her head and chews
    again (2.6). Give cow() nose_to=the dog's nose; pose['_nose'] is how far the muzzle has come to it."""
    t = tau if t is None else t
    N = NOSE_TOUCH
    down = smooth(clamp((tau - 0.15) / (N['contact'] - 0.15)))
    up = smooth(clamp((tau - N['breath'] - 0.25) / (N['away'] - N['breath'] - 0.25)))
    amt = down * (1 - up)
    a = stand(t, who, chew=1.0 - smooth(clamp(tau / 0.3)) * (1 - smooth(clamp((tau - N['away'] + 0.3) / 0.6))))
    b = _P(pitch=2.5, dy=1.0, shoulder=3.0, neck=52.0, head=-8.0, ear=30.0, eye=1.15, jaw=0.5, _nose=1.0)
    q = blend(a, b, amt, who)
    held = clamp((tau - N['contact']) / 0.2) * (1 - clamp((tau - N['hold_end']) / 0.2))
    q['head'] += 1.2 * held * math.sin(2 * math.pi * 3.0 * tau)              # the nostrils working
    q['ear'] = lerp(q['ear'], 30.0, clamp(tau / 0.3) * (1 - up))
    br = clamp((tau - N['breath']) / 0.5)
    q['_breath'] = br if tau < N['breath'] + 0.9 else 0.0
    q['_face'] = 78.0                                           # the head comes down on the dog's nose from above
    if 0 < br < 1:
        q['jaw'] = q.get('jaw', 0.0) + 5.0 * math.sin(math.pi * br)
        q['neck'] -= 2.0 * math.sin(math.pi * br)
    return q


def smell(tau, who='lead'):
    """Lowers her nose to something held up to her (a reel), breathes on it, lifts away. 0..0.6 down, holds to
    1.4, breath at 1.4, up by 2.2. Use nose_to=."""
    return nose_touch(tau * 0.75 / 0.6 if tau < 0.6 else 0.75 + (tau - 0.6), tau, who)


def yield_to(tau, who='fourth'):
    """The herding dog is in front of her, low, looking. She stops chewing (0), her ears come round and the head
    comes up (0..0.3); she holds, looking at it (0.3..0.9); then the head swings away and she takes one step back
    (0.9..1.5). After this, turn her (cow(..., turn=p)) and walk her off the path."""
    a = notice(stand(tau, who, chew=0.0, alert=0.6), smooth(clamp(tau / 0.3)))
    b = with_(a, dx=-9.0, pitch=-1.5, neck=a['neck'] - 14.0, head=a['head'] + 16.0, ear=-20.0,
              nf=('ik', cc.STANCE['nf'] - 12.0, 0.0), nh=('ik', cc.STANCE['nh'] - 12.0, 0.0),
              ff=('ik', cc.STANCE['ff'] - 3.0, 0.0), fh=('ik', cc.STANCE['fh'] - 3.0, 0.0))
    q = blend(a, b, smooth(clamp((tau - 0.9) / 0.6)), who)
    lift = math.sin(math.pi * clamp((tau - 0.9) / 0.6))
    if lift > 0:
        q['nf'] = ('ik', q['nf'][1], -10.0 * lift)
        q['nh'] = ('ik', q['nh'][1], -7.0 * max(0.0, math.sin(math.pi * clamp((tau - 1.05) / 0.45))))
    return q


def nudge(tau, who='mother'):
    """The mother noses the calf back into line. Head down and round to it (0..0.5), one slow shove with the flat
    of her muzzle (0.5..1.1: the body leans into it), holds a breath, lifts away (1.3..2.0). She stands
    behind the calf with her head past it: give nose_to=the front of the calf's chest, and move that point back
    with the calf as it gives way (calf_nosed(tau)['_push']). Pair it with calf_nosed(tau) on the calf."""
    a = stand(tau, who, chew=1.0 - smooth(clamp(tau / 0.25)))
    b = _P(pitch=3.0, dy=2.0, shoulder=4.0, neck=50.0, head=-2.0, ear=14.0, eye=0.9, jaw=0.5, _nose=1.0)
    amt = smooth(clamp(tau / 0.5)) * (1 - smooth(clamp((tau - 1.3) / 0.7)))
    q = blend(a, b, amt, who)
    shove = math.sin(math.pi * clamp((tau - 0.5) / 0.6)) ** 2
    q['dx'] = q.get('dx', 0.0) + 3.0 * shove
    q['_shove'] = shove
    return q


def calf_nosed(tau, who='calf'):
    """The calf, nosed back: it is looking after the dog (ears up, head high); at 0.5 the muzzle arrives and it is
    pushed a step, legs catching up one at a time, ears down, tail clamped (0.5..1.1); it looks round at her
    (1.1..1.6) and gives in: head level, ears out sideways (2.0). pose['_push'] 0..1 is how far it has been
    moved; shift its x by about 16 px * that, away from her."""
    a = notice(stand(tau, who, chew=0.0, alert=1.0), 1.0)
    push = smooth(clamp((tau - 0.5) / 0.6))
    wob = math.sin(math.pi * clamp((tau - 0.5) / 0.6))
    b = with_(a, pitch=-4.0 * wob, dy=4.0 * wob, neck=a['neck'] + 22.0, head=a['head'] - 6.0, ear=-34.0, eye=1.5,
              tail=(-8.0, -4.0, 0.0))
    q = blend(a, b, smooth(clamp((tau - 0.45) / 0.3)), who)
    for i, leg in enumerate(('nh', 'ff', 'fh', 'nf')):                        # the scramble: one leg at a time
        w = math.sin(math.pi * clamp((tau - 0.5 - 0.12 * i) / 0.3))
        if w > 0:
            q[leg] = ('ik', q[leg][1], -12.0 * w)
    c = with_(stand(tau, who, chew=0.0), neck=-2.0, head=10.0, ear=-18.0, eye=0.85, tail=(2.0, 3.0, 4.0))
    q = blend(q, c, smooth(clamp((tau - 1.5) / 0.5)), who)
    q['_push'] = push
    return q


def calf_skid(p, who='calf'):
    """The calf stops badly: fore legs braced out in front, rump still coming, head thrown up, tail up (p 0..0.4),
    then it sorts its legs out and stands (0.4..1)."""
    a = _P(dx=6.0, dy=6.0, pitch=7.0, neck=-44.0, head=-4.0, ear=-30.0, eye=1.7, tail=(70.0, 40.0, 10.0),
           nf=('ik', cc.STANCE['nf'] + 22.0, 0.0), ff=('ik', cc.STANCE['ff'] + 26.0, 0.0),
           nh=('ik', cc.STANCE['nh'] + 20.0, 0.0), fh=('ik', cc.STANCE['fh'] + 12.0, 0.0))
    b = stand(0.0, who, chew=0.0, alert=0.8)
    if p < 0.4:
        return a
    q = blend(a, b, smooth(clamp((p - 0.4) / 0.6)), who)
    for i, leg in enumerate(('nf', 'nh', 'ff', 'fh')):
        w = math.sin(math.pi * clamp((p - 0.4 - 0.1 * i) / 0.25))
        if w > 0:
            q[leg] = ('ik', q[leg][1], -9.0 * w)
    return q


DOG_NOSE_UP = 100.0     # dog units: give this to dog.nose_touch(t, height=) so its nose comes up to where her head can hang
STAMP_HIT = 1.38        # seconds into stamp(tau) at which the hoof lands (the crack, the bell, the sound)


def stamp(tau, who='lead'):
    """Out on the ice. She looks down at the dogs under her hooves and holds (0..0.7); the near fore leg comes up
    slowly, knee high, while she rocks back and the head lifts (0.7..1.2); it hangs (1.2..1.26); it comes down in
    three frames (STAMP_HIT = 1.38) with her whole front end behind it; the bell jumps on its strap and rings on;
    she holds, head down, watching what the ice does (to 2.4). At tau >= 2.4 the pose is the same as at 0.7, so
    stamp(tau - 1.7) stamps again."""
    look = _P(pitch=2.0, dy=1.0, shoulder=3.0, neck=46.0, head=8.0, ear=30.0, eye=1.2, jaw=0.5, tail=(2.0, 3.0, 4.0))
    up = with_(look, dx=-4.0, dy=4.0, pitch=-2.0, shoulder=-2.0, neck=20.0, head=14.0, ear=10.0, eye=1.0,
               nf=('fk', 70.0, -112.0), ff=('ik', cc.STANCE['ff'] - 4.0, 0.0), tail=(14.0, 18.0, 10.0))
    hit = with_(look, dx=3.0, dy=5.0, pitch=4.5, shoulder=7.0, neck=52.0, head=2.0, ear=-12.0, eye=1.5,
                nf=('ik', cc.STANCE['nf'] + 5.0, 0.0), tail=(30.0, 20.0, -6.0))
    q = _keys([(0.0, look), (0.7, look), (1.2, up, 'slow'), (1.26, up), (STAMP_HIT, hit, 'slam'),
               (1.56, with_(look, dy=2.5, ear=20.0, eye=1.35), 'out'), (2.4, look)], tau, who)
    e = tau - STAMP_HIT
    q['bell'] = 44.0 * math.exp(-1.9 * e) * math.sin(2 * math.pi * 2.3 * e + 0.6) if e >= 0 else \
        -10.0 * smooth(clamp((tau - 0.8) / 0.4))
    q['_hit'] = clamp(e / 0.12) if e >= 0 else 0.0
    return q


def warm(t, who='lead', p=1.0):
    """Standing round the wet dogs, steaming. Head low over them, ears out, eyes half shut, a slow deep breath
    (every 4 s the flanks fill and she breathes out: pose['_breath'] 0..1). p 0..1 brings her from standing."""
    o = WHO[who]['phase'] * 4.0
    c = ((t + o) % 4.0) / 4.0
    fill = math.sin(math.pi * clamp(c / 0.55)) ** 2
    a = stand(t, who)
    b = _P(dy=2.0 - 1.6 * fill, pitch=1.5, shoulder=3.0, neck=36.0 - 3.0 * fill, head=14.0, ear=-16.0, eye=0.45,
           jaw=1.0, tail=(1.0, 2.0, 3.0), udder=3.0 * fill, _nose=1.0)
    q = blend(a, b, smooth(clamp(p)), who)
    q['_breath'] = clamp((c - 0.55) / 0.3) if 0.55 < c < 0.9 else 0.0
    return q


def _lying(who='lead', sleep=0.0):
    R = _rig(who)
    belly = -cc.solve(cc.POSES['stand'], _kind(who))['anchors']['belly'][1]
    q = _P(dy=belly - 8.0, dx=-4.0, pitch=-1.5, shoulder=2.0, hip=-6.0, neck=-6.0, head=6.0, ear=-8.0, eye=0.8,
           jaw=0.5, udder=-20.0, tail=(-58.0, -76.0, -84.0),
           nf=('fk', 52.0, -138.0), ff=('fk', 68.0, -134.0), nh=('fk', -40.0, 136.0), fh=('fk', -26.0, 126.0))
    if sleep:
        if who not in _chin:                                   # the chin comes down on the ground in front of her
            a, _ = aim(with_(q, head=-14.0), who, (_rig(who).PIN['head'][0] + 44.0 * _rig(who).kx, -9.0))
            _chin[who] = (a['neck'], a['head'])
        q = blend(q, with_(q, neck=_chin[who][0], head=_chin[who][1], ear=-34.0, eye=0.0, pitch=0.5), sleep, who)
    return q


_chin = {}


def _kneel(who='lead'):
    lie_ = _lying(who)
    return _P(dy=lie_['dy'] * 0.56, dx=4.0, pitch=22.0, shoulder=5.0, hip=3.0, neck=-34.0, head=10.0, ear=-14.0, eye=0.9,
              tail=(18.0, 14.0, 6.0), nf=('fk', lie_['nf'][1] + 27.0, lie_['nf'][2]), ff=('fk', lie_['ff'][1] + 27.0, lie_['ff'][2]),
              nh=('ik', cc.STANCE['nh'] + 8.0, 0.0), fh=('ik', cc.STANCE['fh'] + 12.0, 0.0))


def fold_down(p, who='lead'):
    """Lying down the way a cow does. p 0..1 over about 2 s: she looks at the ground and gathers her feet
    (0..0.12), goes down on her front knees (0.12..0.45), waits there with her rump in the air (0.45..0.62), the
    hind end sinks and rolls (0.62..0.86), and she lets a long breath go (0.86..1). At p = 1 this is lie(0)."""
    st = stand(0.0, who, chew=0.0)
    gather = with_(st, neck=34.0, head=6.0, ear=-10.0, pitch=2.0, dy=1.0,
                   nf=('ik', cc.STANCE['nf'] - 10.0, 0.0), ff=('ik', cc.STANCE['ff'] - 6.0, 0.0))
    kn, ly = _kneel(who), _lying(who)
    over = with_(ly, dy=ly['dy'] + 3.0, pitch=-4.0, neck=-16.0, tail=(-30.0, -60.0, -80.0))
    return _keys([(0.0, st), (0.12, gather), (0.45, kn, 'slow'), (0.62, with_(kn, neck=-28.0, dy=kn['dy'] + 1.0)),
                  (0.86, over, 'slam'), (1.0, ly, 'out')], p, who)


def get_up(p, who='lead'):
    """Getting up, hind end first. p 0..1 over about 2 s: the head swings forward and down for the heave
    (0..0.15), the rump goes up while she is still on her knees (0.15..0.5), a wait (0.5..0.6), then one fore leg
    at a time unfolds and she stands (0.6..1)."""
    ly, kn, st = _lying(who), _kneel(who), stand(0.0, who, chew=0.0)
    heave = with_(ly, neck=38.0, head=-6.0, dx=4.0, pitch=4.0)
    half = blend(kn, st, 0.55, who)
    half['nf'] = ('ik', cc.STANCE['nf'] + 14.0, 0.0)
    return _keys([(0.0, ly), (0.15, heave), (0.5, kn, 'slow'), (0.6, kn), (0.8, half, 'slow'), (1.0, st, 'out')], p, who)


def lie(t=0.0, who='lead', chew=1.0, alert=0.0):
    """Lying folded down, awake: chewing the cud, breathing, an ear turning. alert lifts the head."""
    o = WHO[who]['phase'] * 9.0
    br = math.sin(2 * math.pi * (t + o) / 4.2)
    ch = chew * (0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * (t + o)))
    fl = max(0.0, math.sin(2 * math.pi * (t + o) / 6.1)) ** 14
    q = _lying(who)
    q.update(dy=q['dy'] - 0.9 * br, neck=q['neck'] - 16.0 * alert - 1.5 * br, head=q['head'] + 2.0 * ch,
             jaw=0.5 + 5.0 * ch, ear=q['ear'] + 30.0 * alert - 26.0 * fl)
    return q


def sleep(t=0.0, who='lead', p=1.0):
    """Asleep: p 0..1 lets the head down until the chin is on the ground (or on whatever nose_to= gives it: the
    calf's chin on the wooden retriever's back), eye shut, ears fallen, a slow breath every 5 s."""
    br = math.sin(2 * math.pi * (t + WHO[who]['phase'] * 9.0) / 5.0)
    q = _lying(who, smooth(clamp(p)))
    q.update(dy=q['dy'] - 1.1 * br, neck=q['neck'] - 1.2 * br, _nose=smooth(clamp(p)))
    return q


# ------------------------------------------------------------------ gaits ---

def _trot(dist, ground=None, kind='calf'):
    """The calf's trot: diagonal pairs, a moment in the air, head up, tail out. Hooves that are down stay down."""
    R = cc.Rig.of(kind)
    PIN = R.PIN
    stride = R.stride * 0.86
    ph = dist / stride
    gr = ground or (lambda xr: 0.0)
    duty = 0.44
    off = dict(nh=0.0, ff=0.0, nf=0.5, fh=0.5)
    p = _P()
    air = math.sin(2 * math.pi * (ph * 2 - 0.12))
    gf, gh = gr(PIN['fore'][0]), gr(PIN['hind'][0])
    span = PIN['fore'][0] - PIN['hind'][0]
    p['pitch'] = math.degrees(math.atan2(gf - gh, span)) - 2.0 + 2.2 * math.sin(2 * math.pi * ph * 2)
    p['dy'] = (gf * -PIN['hind'][0] + gh * PIN['fore'][0]) / span + 1.0 - 4.5 * air
    for name in LEGS:
        fore = name[1] == 'f'
        u = (ph - off[name]) % 1.0
        n = math.floor(ph - off[name])
        rest = (PIN['fore'][0] + (2 if name[0] == 'n' else cc.FAR_DX + 2)) if fore else (PIN['hind'][0] - (4 if name[0] == 'n' else -cc.FAR_DX + 4))
        down = (n + off[name]) * stride + rest + stride * duty / 2
        if u < duty:
            xw, hgt = down, 0.0
        else:
            w = (u - duty) / (1 - duty)
            xw = down + stride * (0.1 * w + 0.9 * w * w * (3 - 2 * w))
            hgt = (26.0 if fore else 20.0) * math.sin(math.pi * w ** 0.8) ** 1.2
        xr = xw - dist
        p[name] = ('ik', xr / R.kx, gr(xr) - hgt)
    p['neck'] = -30.0 + 5.0 * math.sin(2 * math.pi * ph * 2 - 1.0)
    p['head'] = 6.0 - 4.0 * math.sin(2 * math.pi * ph * 2 - 1.6)
    p['ear'] = 22.0 + 16.0 * math.sin(2 * math.pi * ph * 2 - 2.2)
    p['tail'] = (52.0 + 10.0 * air, 44.0 + 16.0 * math.sin(2 * math.pi * ph * 2 - 1.2), 30.0 + 24.0 * math.sin(2 * math.pi * ph * 2 - 2.2))
    return p


def _stand_on(rel, who):
    """Standing on sloping ground: rel(xr) is the ground height xr cow units ahead of her middle."""
    R = _rig(who)
    PIN = R.PIN
    gf, gh = rel(PIN['fore'][0]), rel(PIN['hind'][0])
    span = PIN['fore'][0] - PIN['hind'][0]
    p = _P(pitch=math.degrees(math.atan2(gf - gh, span)), dy=(gf * -PIN['hind'][0] + gh * PIN['fore'][0]) / span)
    for leg in LEGS:
        p[leg] = ('ik', cc.STANCE[leg], rel(cc.STANCE[leg] * R.kx))
    return p


def step_pose(who, dist, slope=0.0, rest=0.0, t=0.0, carry=0.0, lift=1.0, gait='walk', chew=1.0, weight=1.0):
    """The walking (or standing) pose after `dist` cow units of travel on ground that rises `slope` (dy per unit
    forward, + = downhill). rest 0..1 brings her to a stand (and she starts to chew). carry hangs the head."""
    kind = _kind(who)
    rel = lambda xr: slope * xr
    d = dist + WHO[who]['phase'] * cc.Rig.of(kind).stride
    if gait == 'trot':
        p = _trot(d, rel, kind)
    else:
        p = cc.walk(d, ground=rel, lift=lift, carry=carry, kind=kind, weight=weight)
    if rest > 0:
        idle = stand(t, who, chew=chew)
        st = _stand_on(rel, who)
        for k in ('neck', 'head', 'jaw', 'ear', 'eye', 'tail', 'udder'):
            st[k] = idle[k]
        st['dy'] += idle['dy']
        st['neck'] += carry
        p = blend(p, st, smooth(clamp(rest)), who)
    return p


# ------------------------------------------------------------------ aiming the muzzle ---

def _chain(pose, R):
    cx, cy = R.C
    pitch = clamp(float(pose.get('pitch', 0.0)), *cc.LIMITS['pitch'])
    r = cc._rot((cx, cy), pitch)
    F_b = cc.Fr(pitch, cx - r[0] + pose.get('dx', 0.0), cy - r[1] + pose.get('dy', 0.0) + R.drop)
    return F_b.pin(clamp(float(pose.get('shoulder', 0.0)), *cc.LIMITS['shoulder']), R.PIN['shoulder'])


def aim(pose, who, target, amount=1.0, face=None):
    """The pose with neck and head turned so the muzzle goes to `target` (cow units, relative to her ground
    point, +x ahead of her, +y down). amount 0..1 goes part of the way. face (degrees below level, e.g. 80)
    asks for the face to hang at that angle, so the head comes down on the point from above instead of
    poking at it. If the point is out of reach she stretches toward it as far as her neck allows.
    Returns (pose, miss_in_units)."""
    R = _rig(who)
    F_s = _chain(pose, R)
    h0 = pose.get('head', 0.0)

    def cost(F_n, head):
        F_h = F_n.pin(head, R.PIN['head'])
        m = F_h(R.NOSE)
        e = (m[0] - target[0]) ** 2 + (m[1] - target[1]) ** 2
        if face is None:
            return e + 0.002 * (head - h0) ** 2
        return e + 0.06 * max(0.0, abs(F_h.a + cc.HEAD_ANGLE - face) - 8.0) ** 2

    best = None
    for neck in range(-64, 83, 4):
        F_n = F_s.pin(neck, R.PIN['neck'])
        for head in range(-46, 63, 6):
            e = cost(F_n, head)
            if best is None or e < best[0]:
                best = (e, neck, head)
    _, n0, hd0 = best
    for neck in (n0 + k for k in range(-4, 5)):
        if not cc.LIMITS['neck'][0] <= neck <= cc.LIMITS['neck'][1]:
            continue
        F_n = F_s.pin(neck, R.PIN['neck'])
        for head in (hd0 + k for k in range(-6, 7, 2)):
            if not cc.LIMITS['head'][0] <= head <= cc.LIMITS['head'][1]:
                continue
            e = cost(F_n, head)
            if e < best[0]:
                best = (e, neck, head)
    _, neck, head = best
    m = F_s.pin(neck, R.PIN['neck']).pin(head, R.PIN['head'])(R.NOSE)
    q = dict(pose)
    q['neck'] = lerp(pose.get('neck', 0.0), neck, amount)
    q['head'] = lerp(pose.get('head', 0.0), head, amount)
    return q, math.hypot(m[0] - target[0], m[1] - target[1])


# ------------------------------------------------------------------ drawing ---

def _img(target):
    return target.img if hasattr(target, 'img') else target


def _refresh(target):
    if hasattr(target, 'img'):
        target.d = ImageDraw.Draw(target.img, 'RGBA')


def _paste(target, layer, x, y):
    _img(target).paste(layer, (int(round(x)), int(round(y))), layer)
    _refresh(target)


def _solved(who, pose):
    """cast.solve() plus this film's cuts: the bent horn, the calf's ears and knees, this cow's patches."""
    kind = _kind(who)
    sol = cc.solve(pose, kind)
    R = sol['rig']
    F_hd = sol['frames']['head']
    parts = []
    for n, poly, tone in sol['parts']:
        if n == 'crump' and kind == 'lead':
            poly = [F_hd(q) for q in _crook(R)]
        if n == 'ear' and kind == 'calf':
            cx, cy = (poly[0][0] + poly[-1][0]) / 2, (poly[0][1] + poly[-1][1]) / 2
            poly = [(cx + (q[0] - cx) * 1.3, cy + (q[1] - cy) * 1.3) for q in poly]
        parts.append((n, poly, tone))
    patches = {}
    for piece, cx, cy, rx, ry, seed in WHO[who]['patches']:
        if piece == 'head':
            poly = [F_hd(q) for q in R.hd(_blob(cx, cy, rx, ry, seed))]
        else:
            poly = [sol['frames'][piece](R.M(q)) for q in _blob(cx, cy, rx, ry, seed)]
        patches.setdefault(piece, []).append(poly)
    muzzle = [F_hd(q) for q in R.hd([(47, -14), (70, -12), (72, 12), (50, 12), (46, 0)])]
    return sol, parts, patches, muzzle


_crook_cache = {}


def _crook(R):
    if R.kind not in _crook_cache:
        _crook_cache[R.kind] = cc._smooth(R.hd(_CROOK_L), n=4)
    return _crook_cache[R.kind]


def sprite(who, pose, s=None, facing=1, tilt=0.0, squash=1.0, rim=0.5, far=0.0, flat=None, tones=None, only=None):
    """The animal as an RGBA cut-out. Returns (image, (ax, ay)): paste its top-left at (x - ax, y - ay).

    rim 0..1: the amber edge on the lamp side (the left of the picture, whichever way she faces).
    far 0..1: distance: the card goes toward the violet of the hill (cows high on the path).
    flat=(r, g, b): one flat colour, no rim, no eye: her silhouette.
    only='head': just her head (horns, ears, jaw), in the same place: to lay it over a dog she has put her
    nose down to."""
    s = S if s is None else s
    sol, parts, patches, muzzle = _solved(who, pose)
    Sx = s * _size(who) * SS
    sq = max(0.05, abs(squash))
    c, sn = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))

    def P(poly):
        if tilt:
            poly = [(q[0] * c - q[1] * sn, q[0] * sn + q[1] * c) for q in poly]
        return [(facing * sq * Sx * q[0], Sx * q[1]) for q in poly]

    polys = [(n, P(poly), tone) for n, poly, tone in parts]
    xs = [q[0] for _, poly, _ in polys for q in poly]
    ys = [q[1] for _, poly, _ in polys for q in poly]
    pad = 5 * SS
    x0, y0 = math.floor(min(xs)) - pad, math.floor(min(ys)) - pad
    wd, ht = int(max(xs) - x0) + pad + int(6 * Sx), int(max(ys) - y0) + pad + int(8 * Sx)
    wd, ht = wd + (-wd) % SS, ht + (-ht) % SS
    O = lambda poly: [(q[0] - x0, q[1] - y0) for q in poly]
    tn = dict(tones or WHO[who]['tones'])
    if far:
        for k in ('hide', 'far', 'edge', 'patch', 'horn', 'udder', 'hoof', 'muzzle', 'bell', 'strap'):
            tn[k] = tuple(int(lerp(v, w, far)) for v, w in zip(tn[k], (84, 60, 108)))
    if flat is not None:
        tn = {k: tuple(flat) for k in tn}
    img = Image.new('RGBA', (wd, ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    off = (0.9 * Sx, 1.5 * Sx)
    col = lambda k: tuple(tn[k]) + (255,)
    for n, poly, tone in polys:
        if only == 'head' and n not in _HEAD_PARTS:
            continue
        pp = O(poly)
        if flat is None and tone != 'far':
            d.polygon([(q[0] + off[0], q[1] + off[1]) for q in pp], fill=col('edge'))     # the paper's own shadow
        d.polygon(pp, fill=col(tone if tone in tn else 'hide'))
        if flat is not None:
            continue
        extra = list(patches.get(n, ()))
        fills = [(O(P(q)), col('patch')) for q in extra]
        if n == 'head':
            fills.append((O(P(muzzle)), col('muzzle')))
        if fills:
            bx0, by0 = int(min(q[0] for q in pp)) - 1, int(min(q[1] for q in pp)) - 1
            bw, bh = int(max(q[0] for q in pp)) - bx0 + 3, int(max(q[1] for q in pp)) - by0 + 3
            pm = Image.new('L', (bw, bh), 0)
            ImageDraw.Draw(pm).polygon([(q[0] - bx0, q[1] - by0) for q in pp], fill=255)
            for fp, fc in fills:
                qm = Image.new('L', (bw, bh), 0)
                ImageDraw.Draw(qm).polygon([(q[0] - bx0, q[1] - by0) for q in fp], fill=255)
                img.paste(fc, (bx0, by0), ImageChops.multiply(qm, pm))
            d = ImageDraw.Draw(img)
        if n.endswith('_lower'):
            d.polygon(O(P(sol['hoofs'][n[:2]])), fill=col('hoof'))
        if n == 'tail':
            j = int(len(pp) // 2 * 0.66)
            d.polygon(pp[j:len(pp) - j], fill=col('hoof'))
        if n == 'bell':
            d.line(O(P(list(sol['strap']))), fill=col('strap'), width=max(2, int(3.0 * Sx)))
            lo = [pp[k] for k in (5, 6)]
            d.line(lo, fill=tuple(int(v * 0.6) for v in tn['bell']) + (255,), width=max(1, int(1.6 * Sx)))
    if sol['clapper'] and only is None:
        (bx, by), br = O(P([sol['clapper'][0]]))[0], sol['clapper'][1] * Sx
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col('hoof'))
        if flat is not None:
            d.line(O(P(list(sol['strap']))), fill=col('strap'), width=max(2, int(3.0 * Sx)))
    if _kind(who) == 'calf' and only is None:                   # knobby knees
        for key in ('knee', 'hock'):
            kx_, ky_ = O(P([sol['anchors'][key]]))[0]
            r = 6.2 * Sx
            d.ellipse([kx_ - r * sq, ky_ - r, kx_ + r * sq, ky_ + r], fill=col('hide'))
    if flat is None:
        (ex, ey), opn, er = O(P([sol['eye'][0]]))[0], sol['eye'][1], sol['eye'][2] * Sx * 0.95
        if opn <= 0.08:
            d.arc([ex - er * 1.2, ey - er * 0.5, ex + er * 1.2, ey + er * 1.3], 15, 165, fill=col('eye'), width=max(1, int(1.2 * Sx)))
        else:
            k = opn ** 0.6 if opn > 1 else 1.0
            rx, ry = er * k * sq ** 0.5, er * k * min(opn, 1.0)
            d.ellipse([ex - rx, ey - ry, ex + rx, ey + ry], fill=col('eye'))
            pr = er * 0.74
            px = ex + facing * er * 0.14
            d.ellipse([px - pr, ey - min(pr, ry), px + pr, ey + min(pr, ry)], fill=col('pupil'))
            if opn < 0.75:
                d.line([(ex - er * 1.3, ey - ry), (ex + er * 1.3, ey - ry)], fill=col('hide'), width=max(1, int(1.6 * Sx)))
    img = img.resize((wd // SS, ht // SS), Image.LANCZOS)
    if rim > 0 and flat is None:
        a = img.getchannel('A')
        edge = ImageChops.subtract(a, ImageChops.offset(a, 2, 1))          # what has nothing to its upper left
        edge = edge.point(lambda v: int(v * 0.62 * clamp(rim)))
        glow = Image.new('RGBA', img.size, AMBER + (0,))
        glow.putalpha(edge)
        img = Image.alpha_composite(img, glow)
    return img, (-x0 / SS, -y0 / SS)


_HEAD_PARTS = ('crump', 'jaw', 'head', 'horn', 'ear')


def rim_at(x):
    """How much lamp falls on a cow at world x: strong by the gate, gone past the drinking place."""
    return clamp(1.0 - (x - 300) / 420.0) * 0.9 + 0.1


def cow(ink, who, pose, x, y, s=None, facing=1, oy=0, nose_to=None, turn=None, tilt=0.0, rim=None, far=0.0,
        flat=None, alpha=1.0, reflect=None, squash=1.0, shadow=0.45, only=None):
    """Draw one of the herd with the ground under the middle of her barrel at world (x, y); screen y = y - oy.

    who      'lead', 'second', 'mother', 'calf', 'fourth', 'fifth', 'sixth'
    pose     a pose dict: from stand(), drink(), stamp(), fold_down() ..., or step_pose()
    s        px per cow unit; herd.S (the default) is the size on the path strip (lead 104 px to the withers,
             the calf 60). On the hill multiply by porch.path_point(u)[2].
    facing   1 looks right, -1 looks left
    nose_to  a WORLD point the muzzle goes to, as far as pose['_nose'] says (1 if the pose has no '_nose'):
             the dog's nose, the water, the calf's rump, the old dog's shoulder, a reel
    turn     0..1: she turns round the way a paper puppet does, edge-on at 0.5; `facing` is the way she faced
             before the turn
    rim      0..1 amber on her lamp side (default: by x, see rim_at)
    far      0..1 distance haze for cows up the hill
    flat     (r, g, b): draw her silhouette only
    reflect  a world y: a dim reflection below that line (her on the ice)
    only     'head': draw just her head again, in the same place (call cow() a second time, after the dog, so
             that the head she has lowered over the sill lies in front of the dog she is touching)
    shadow   0..1: the soft dark she stands on (it is what puts her ON the path and the grass); 0 for none
    Returns the anchors in SCREEN pixels: muzzle, mouth, eye, horn, ear, poll, throat, bell, withers, back,
    hook, rump, seat, belly, tail_tip, tail_head, hand (near fore hoof), knee, hock, hooves{nf, ff, nh, fh},
    plus facing, s, miss (how far the muzzle fell short of nose_to, px), breath, hit."""
    s = S if s is None else s
    if turn is not None:
        f = math.cos(math.pi * clamp(turn))
        facing, squash = (facing if f >= 0 else -facing), max(0.05, abs(f))
    Sx = s * _size(who)
    miss = 0.0
    if nose_to is not None:
        amt = pose.get('_nose', 1.0)
        if amt > 0:
            pose, m = aim(pose, who, ((nose_to[0] - x) / (facing * Sx), (nose_to[1] - y) / Sx), amt, pose.get('_face'))
            miss = m * Sx
    img, (ax, ay) = sprite(who, pose, s, facing, tilt, squash, rim_at(x) if rim is None else rim, far, flat, only=only)
    if only:
        shadow, reflect = 0.0, None
    if alpha < 1:
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    px, py = int(round(x - ax)), int(round(y - oy - ay))
    if shadow > 0 and flat is None and reflect is None:
        _ground_shadow(ink, x - facing * 6 * Sx * squash, y - oy, 92 * Sx * max(0.25, squash), max(2.5, 7 * Sx), shadow * alpha)
    if reflect is not None:
        ry = int(round(reflect - oy))
        gh = int(ay + (ry - (y - oy)))                         # rows of her above the line
        if gh > 4:
            r = img.crop((0, 0, img.size[0], min(img.size[1], gh))).transpose(Image.FLIP_TOP_BOTTOM)
            r = r.resize((r.size[0], max(1, int(r.size[1] * 0.5))))
            r.putalpha(r.getchannel('A').point(lambda v: int(v * 0.2)))
            _paste(ink, r, px, ry + 1)
    _paste(ink, img, px, py)
    sol = cc.solve(pose, _kind(who))
    sq = squash
    T = lambda q: (px + ax + facing * sq * Sx * q[0], py + ay + Sx * q[1])
    a = {k: (T(v) if k != 'hooves' else {n: T(q) for n, q in v.items()}) for k, v in sol['anchors'].items()}
    a.update(facing=facing, s=s, miss=miss, breath=pose.get('_breath', 0.0), hit=pose.get('_hit', 0.0), who=who,
             violations=sol['violations'])
    return a


def _ground_shadow(ink, x, y, rx, ry, amount):
    pad = 6
    m = Image.new('L', (int(2 * rx) + 2 * pad, int(2 * ry) + 2 * pad), 0)
    ImageDraw.Draw(m).ellipse([pad, pad, pad + 2 * rx, pad + 2 * ry], fill=int(255 * clamp(amount)))
    m = m.filter(ImageFilter.GaussianBlur(max(1.2, ry * 0.45)))
    layer = Image.new('RGBA', m.size, (18, 10, 30, 0))
    layer.putalpha(m)
    _paste(ink, layer, x - rx - pad, y - ry * 0.9 - pad)


def anchors(who, pose, x, y, s=None, facing=1, oy=0):
    """Where her parts are on screen without drawing her (same keys as cow())."""
    s = S if s is None else s
    Sx = s * _size(who)
    sol = cc.solve(pose, _kind(who))
    T = lambda q: (x + facing * Sx * q[0], y - oy + Sx * q[1])
    a = {k: (T(v) if k != 'hooves' else {n: T(q) for n, q in v.items()}) for k, v in sol['anchors'].items()}
    a.update(facing=facing, s=s, who=who, violations=sol['violations'])
    return a


_reach = {}


def reach(who='lead', drop=12.0, s=None, face=None):
    """How far ahead of her middle (px) her muzzle can be put down, `drop` px below the ground she stands on
    (12 = the water line seen from the path strip; negative = above the ground: a dog's nose). face as in aim().
    To drink at water x = 600 facing right she stands at x = 600 - herd.reach('lead'). To touch a dog's nose at
    world (nx, ny) from the strip she stands at nx - herd.reach('lead', ny - 388, face=78)."""
    s = S if s is None else s
    k = s * _size(who)
    key = (who, round(drop / k, 1), face)
    if key not in _reach:
        base = drink(0.0, 1.0, who) if drop > -20 else nose_touch(0.9, None, who)
        tries = [(aim(base, who, (x, drop / k), 1.0, face)[1], -x) for x in range(190, 40, -2)]
        ok = [t for t in tries if t[0] <= 1.0]
        _reach[key] = -(ok[0][1] if ok else min(tries)[1]) - 2.0
    return _reach[key] * k


# ------------------------------------------------------------------ steam and breath ---

def _soft(ink, blobs, color=(236, 228, 240), blur=5):
    """blobs: [(x, y, r, alpha 0..255)] on screen, drawn as one soft sheet."""
    blobs = [b for b in blobs if b[3] > 1 and b[2] > 0.5]
    if not blobs:
        return
    x0 = int(min(b[0] - b[2] for b in blobs)) - 3 * blur
    y0 = int(min(b[1] - b[2] for b in blobs)) - 3 * blur
    x1 = int(max(b[0] + b[2] for b in blobs)) + 3 * blur
    y1 = int(max(b[1] + b[2] for b in blobs)) + 3 * blur
    x0, y0, x1, y1 = max(x0, -40), max(y0, -40), min(x1, W + 40), min(y1, H + 40)
    if x1 <= x0 or y1 <= y0:
        return
    m = Image.new('L', (x1 - x0, y1 - y0), 0)
    for x, y, r, al in blobs:
        dab = Image.new('L', m.size, 0)
        ImageDraw.Draw(dab).ellipse([x - x0 - r, y - y0 - r * 0.8, x - x0 + r, y - y0 + r * 0.8], fill=int(clamp(al, 0, 255)))
        m = ImageChops.lighter(m, dab)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new('RGBA', m.size, tuple(color) + (0,))
    layer.putalpha(m)
    _paste(ink, layer, x0, y0)


def steam(ink, t, x, y, amount=1.0, width=70.0, height=64.0, seed=0, drift=6.0):
    """Steam off a warm wet flank: soft pale plumes that leave the line y between x - width/2 and x + width/2,
    rise `height` px, lean with `drift`, widen and thin. (x, y) are SCREEN px (use anchors['back']).
    amount 0..1 fades the whole thing in and out."""
    if amount <= 0:
        return
    blobs = []
    n = max(3, int(width / 14))
    for k in range(n * 2):
        life = 2.4 + 1.2 * _h(seed * 3.1 + k * 1.7)
        u = ((t + life * _h(seed * 5.3 + k * 2.9)) % life) / life
        bx = x + (_h(seed + k * 4.1) - 0.5) * width + drift * u * u * 2.5 + 4 * math.sin(3 * u + k)
        by = y - height * u ** 0.9
        blobs.append((bx, by, 5 + 11 * u, 150 * amount * clamp(u / 0.12) * (1 - u) ** 1.6))
    _soft(ink, blobs, blur=5)


def breath(ink, x, y, p, facing=1, size=1.0, down=0.25):
    """One breath out of her nostrils at SCREEN (x, y): p 0..1 (use anchors['breath']). It rolls forward and a
    little down, opens and is gone. In the cold (S5) call it with size=1.6."""
    if not 0 < p < 1:
        return
    blobs = []
    for k in range(4):
        u = clamp(p * 1.15 - 0.08 * k)
        if u <= 0:
            continue
        r = (3 + 11 * u) * size
        blobs.append((x + facing * (6 + 26 * u + 5 * k) * size, y + (down * 26 * u + 2 * k) * size - 6 * u * u * size,
                      r, 135 * (1 - p) ** 0.7 * (1 - 0.15 * k)))
    _soft(ink, blobs, blur=max(2, int(3 * size)))


def steam_on(ink, t, a, amount=1.0, cold=1.0):
    """Steam and breath for one drawn cow: a is what cow() returned. Plumes off her back and rump, and her
    breath when the pose breathes out (warm(), nose_touch())."""
    wd = abs(a['withers'][0] - a['rump'][0])
    cx = (a['withers'][0] + a['rump'][0]) / 2
    steam(ink, t, cx, a['back'][1] + 4, amount, wd * 0.9, 46 + 30 * cold, seed=int(WHO[a['who']]['phase'] * 100))
    if a.get('breath', 0) > 0:
        breath(ink, a['muzzle'][0], a['muzzle'][1], a['breath'], a['facing'], 1.0 + 0.6 * cold)


# ------------------------------------------------------------------ the bell ---

class Bell:
    """The bell as a real pendulum on its strap, driven by how her throat moves: it lags every step and nod and
    rings on after she stops. throat(t) -> (x, y) in px (use Walker, which does this for you).
    .angle(t) degrees for pose['bell']; .hits = the times the clapper strikes (for the sound designer)."""

    def __init__(self, throat, t0, t1, rate=72, length=22.0, damp=1.3):
        self.t0, self.rate = t0, rate
        dt = 1.0 / rate
        n = int((t1 - t0 + 3.0) * rate) + 3
        xs = [throat(t0 + (i - 1) * dt) for i in range(n + 1)]
        th = om = prev = 0.0
        self.a, self.hits = [], []
        for i in range(1, n):
            ax = (xs[i + 1][0] - 2 * xs[i][0] + xs[i - 1][0]) / (dt * dt)
            ay = (xs[i + 1][1] - 2 * xs[i][1] + xs[i - 1][1]) / (dt * dt)
            ax, ay = clamp(ax, -5000, 5000), clamp(ay, -800, 5000)
            om += (-(981.0 / length * 0.42 + ay / length) * math.sin(th) - damp * om + (ax / length) * math.cos(th)) * dt
            th = clamp(th + om * dt, -1.1, 1.1)
            self.a.append(math.degrees(th))
            if prev * th < 0 and abs(om) > 1.4 and (not self.hits or t0 + i * dt - self.hits[-1] > 0.12):
                self.hits.append(round(t0 + (i - 1) * dt, 3))
            prev = th

    def angle(self, t):
        return self.a[int(clamp((t - self.t0) * self.rate, 0, len(self.a) - 1))]


# ------------------------------------------------------------------ the path, the gate, the bank ---

def _path_point(u):
    if _porch is not None:
        return _porch.path_point(u)
    pts = [(600, 222), (540, 246), (470, 280), (420, 306), (380, 330), (346, 356), (326, 384)]
    f = clamp(u) * (len(pts) - 1)
    k = min(int(f), len(pts) - 2)
    x, y = lerp(pts[k][0], pts[k + 1][0], f - k), lerp(pts[k][1], pts[k + 1][1], f - k)
    return x, y, lerp(0.25, 0.9, clamp((y - 222) / 162.0) ** 1.15)


def depth_scale(y):
    """The size of a cow (relative to herd.S) standing on the hill face at world y: 0.25 at the crest (222),
    0.9 in the gate (384), 1 on the strip (388)."""
    if y >= 384:
        return lerp(0.9, 1.0, clamp((y - 384) / 4.0))
    return lerp(0.25, 0.9, clamp((y - 222) / 162.0) ** 1.15)


def meadow_y(x):
    """Ground under a cow on the bank: the strip (388) and the meadow rising to the right (376 at x = 960)."""
    return lerp(388.0, 376.0, clamp((x - MEADOW_X) / 320.0))


TURN = 46.0     # px of a route a cow spends turning round


class Route:
    """A way a cow can go: nodes (x, y, size) in WORLD px, size relative to herd.S (1 = on the strip).

        r = herd.Route([(600, 222, 0.25), ..., (346, 388, 1.0), (640, 388, 1.0)], lean=0.3)
        st = r.at(d)          # d = px along it -> dict(x, y, s, facing, squash, slope, c, layer)

    Where the route doubles back (the gate) she turns round over TURN px, edge-on in the middle, like the
    paper puppet she is. `lean` is how much of the drawn slope her body takes (the hill path is mostly depth,
    so 0.3; the bank is real ground, so 1). layer(x, y) names the porch.scene cast layer she belongs to there."""

    def __init__(self, nodes, lean=1.0, layer=None, step=2.0):
        self.nodes = [(float(n[0]), float(n[1]), float(n[2]) if len(n) > 2 else 1.0, (n[3] if len(n) > 3 else lean)) for n in nodes]
        self.step = step
        xs, ys, ss, ln = [], [], [], []
        for a, b in zip(self.nodes, self.nodes[1:]):
            m = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
            for k in range(m):
                f = k / m
                xs.append(lerp(a[0], b[0], f)); ys.append(lerp(a[1], b[1], f)); ss.append(lerp(a[2], b[2], f)); ln.append(lerp(a[3], b[3], f))
        e = self.nodes[-1]
        xs.append(e[0]); ys.append(e[1]); ss.append(e[2]); ln.append(e[3])
        n = len(xs)
        for _ in range(3):                                           # round the corners a little
            ys = [ys[0]] + [(ys[i - 1] + 2 * ys[i] + ys[i + 1]) / 4 for i in range(1, n - 1)] + [ys[-1]]
        self.x, self.y, self.s, self.lean = xs, ys, ss, ln
        self.d = [0.0]
        for i in range(1, n):
            self.d.append(self.d[-1] + math.hypot(xs[i] - xs[i - 1], ys[i] - ys[i - 1]))
        self.length = self.d[-1]
        face, f = [], 1
        for i in range(n):
            j0, j1 = max(0, i - 3), min(n - 1, i + 3)
            dx = xs[j1] - xs[j0]
            if abs(dx) > 1.5:
                f = 1 if dx > 0 else -1
            face.append(f)
        f0 = next((face[i] for i in range(n) if abs(xs[min(n - 1, i + 3)] - xs[max(0, i - 3)]) > 1.5), 1)
        for i in range(n):
            if abs(xs[min(n - 1, i + 3)] - xs[max(0, i - 3)]) > 1.5:
                break
            face[i] = f0
        self.face = face
        self.turns = [self.d[i] for i in range(1, n) if face[i] != face[i - 1]]
        self._layer = layer or (lambda x, y: 'strip')

    def _i(self, d):
        d = clamp(d, 0.0, self.length)
        lo, hi = 0, len(self.d) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.d[mid] <= d:
                lo = mid
            else:
                hi = mid
        f = (d - self.d[lo]) / max(self.d[hi] - self.d[lo], 1e-9)
        return lo, hi, f

    def at(self, d):
        lo, hi, f = self._i(d)
        x, y, s = lerp(self.x[lo], self.x[hi], f), lerp(self.y[lo], self.y[hi], f), lerp(self.s[lo], self.s[hi], f)
        n = len(self.x)
        j0, j1 = max(0, lo - 8), min(n - 1, hi + 8)
        facing, squash = self.face[lo], 1.0
        for td in self.turns:
            if abs(d - td) < TURN / 2:
                before = self.face[max(0, self._i(td - TURN / 2 - 1)[0])]
                fsig = before * math.cos(math.pi * (d - td + TURN / 2) / TURN)
                facing, squash = (1 if fsig >= 0 else -1), max(0.05, abs(fsig))
        dx = self.x[j1] - self.x[j0]
        slope = 0.0
        if abs(dx) > 4:
            slope = clamp((self.y[j1] - self.y[j0]) / dx, -0.7, 0.7) * facing * lerp(self.lean[lo], self.lean[hi], f)
        return dict(x=x, y=y, s=s * S, rel=s, facing=facing, squash=squash, slope=slope * squash, layer=self._layer(x, y), d=d)

    def units(self, d, who):
        """Cow units walked from the start of the route to d (what the walk cycle runs on)."""
        key = who
        if not hasattr(self, '_c'):
            self._c = {}
        if key not in self._c:
            k = _size(who)
            c = [0.0]
            for i in range(1, len(self.d)):
                c.append(c[-1] + (self.d[i] - self.d[i - 1]) / (0.5 * (self.s[i] + self.s[i - 1]) * S * k))
            self._c[key] = c
        lo, hi, f = self._i(d)
        c = self._c[key]
        return lerp(c[lo], c[hi], f)

    def find(self, x, last=True):
        """The d at which the route passes world x (the last time it does, or the first)."""
        hit = [self.d[i] for i in range(1, len(self.x)) if (self.x[i - 1] - x) * (self.x[i] - x) <= 0]
        return (hit[-1] if last else hit[0]) if hit else (self.length if x > self.x[-1] else 0.0)


def _path_layer(x, y):
    return 'hill' if y < 368 else 'strip'


def path_nodes(u0=0.0, n=24):
    """The worn path from u0 (0 = the crest) down to the gate, as Route nodes (the hill is mostly depth: lean 0.3)."""
    return [(_path_point(lerp(u0, 1.0, k / n)) + (0.3,)) for k in range(n + 1)]


def path_route(end_x=960.0, u0=0.0):
    """THE way the herd goes: down the pale path from the crest, through the one gate (she turns there), along
    the path strip behind the sill, past the drinking place and up into the meadow as far as end_x."""
    nodes = path_nodes(u0) + [(352, STRIP_Y, 1.0, 1.0), (MEADOW_X, STRIP_Y, 1.0, 1.0)]
    x = MEADOW_X
    while x < end_x:
        x = min(end_x, x + 40)
        nodes.append((x, meadow_y(x), 1.0, 1.0))
    return Route(nodes, layer=_path_layer)


PATH = path_route()
D_GATE = PATH.turns[0] if PATH.turns else 0.0            # the d at which a cow stands in the gate, turning
D_CREST = 0.0


def d_at(x):
    """The d on herd.PATH at which a cow's middle is at world x on the strip or the meadow (x >= 352)."""
    return PATH.find(x, last=True)


def hill_spot(k, gap=None):
    """The d on herd.PATH where the k-th cow of the queue waits (k = 0 stands in the gate, 1 behind her, ...).
    The gaps close up the hill the way the path narrows, so the queue reads as one line getting smaller."""
    d = D_GATE - TURN * 0.5
    for i in range(k):
        st = PATH.at(d)
        d -= (gap or 196.0) * st['rel'] * 0.86 + 8
    return max(0.0, d)


def off_path(u, to=(760, None), mid=None):
    """Turned off the path: a Route from the path at u (0 crest .. 1 gate) across the dark grass of the hill
    face to the meadow at to=(x, y) (y None = the meadow's own ground). She turns round where she stood.
    r.find(x_start, last=False) is where she stands at the start."""
    x0, y0, s0 = _path_point(u)
    x1 = to[0]
    y1 = meadow_y(x1) if to[1] is None else to[1]
    back = _path_point(max(0.0, u - 0.07))
    mid = mid or (lerp(x0, x1, 0.5), lerp(y0, y1, 0.62))
    nodes = [back + (0.3,), (x0, y0, s0, 0.3)]
    for f in (0.25, 0.5, 0.75):
        qx = (1 - f) ** 2 * x0 + 2 * f * (1 - f) * mid[0] + f * f * x1
        qy = (1 - f) ** 2 * y0 + 2 * f * (1 - f) * mid[1] + f * f * y1
        nodes.append((qx, qy, depth_scale(qy), 0.5))
    nodes.append((x1, y1, 1.0, 1.0))
    return Route(nodes, layer=lambda x, y: 'hill' if y < 368 else 'strip')


def ice_route(x0=700.0, out=600.0, y=None):
    """Out onto the ice and back: from the meadow's edge at x0 down onto the frozen water (hooves on the line,
    y = 400) as far as x = out. Walk d forward to go out; walk d back down to come back (she backs off the ice
    without turning, which is how a cow leaves ice)."""
    y = SURFACE + 1.0 if y is None else y
    step = -1 if out < x0 else 1
    return Route([(x0, meadow_y(x0), 1.0), (x0 + step * 34, y, 1.0), (out, y, 1.0)], lean=0.6, layer=lambda x, yy: 'front')


class Plan:
    """Where along her route a cow is at each moment: keys [(t, d), ...]. Between two keys with different d she
    walks, easing off and coming to a stop over `ramp` seconds at each end that meets a wait; between two keys
    with the same d she waits. plan(t) -> (d, rest): rest 1 = standing, 0 = walking."""

    def __init__(self, keys, ramp=0.7):
        self.keys = sorted((float(a), float(b)) for a, b in keys)
        self.ramp = ramp

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1], 1.0
        if t >= ks[-1][0]:
            return ks[-1][1], 1.0
        for i in range(len(ks) - 1):
            (ta, da), (tb, db) = ks[i], ks[i + 1]
            if ta <= t <= tb:
                if da == db:
                    return da, 1.0
                T = tb - ta
                stop_a = i == 0 or ks[i - 1][1] == da
                stop_b = i == len(ks) - 2 or ks[i + 2][1] == db
                a_in = min(0.45, self.ramp / T) if stop_a else 0.0
                a_out = min(0.45, self.ramp / T) if stop_b else 0.0
                vc = 1.0 / (1.0 - a_in / 2 - a_out / 2)
                u = (t - ta) / T
                if u < a_in:
                    pos, v = vc * u * u / (2 * a_in), u / a_in
                elif u > 1 - a_out:
                    w = 1 - u
                    pos, v = 1 - vc * w * w / (2 * a_out), w / a_out
                else:
                    pos, v = vc * (u - a_in / 2), 1.0
                return lerp(da, db, pos), clamp(1.0 - v) ** 1.5
        return ks[-1][1], 1.0


class Walker:
    """One cow, her route and her evening.

        lead = herd.Walker('lead', herd.PATH, [(0.0, herd.D_GATE - 60), (3.4, herd.d_at(430)), (5.6, herd.d_at(430)),
                                               (6.5, herd.d_at(540))],
                           acts=[(3.0, 5.6, lambda tau: herd.nose_touch(tau))])
        a = lead.draw(ink, t, oy, nose_to=dog_nose_world)      # inside porch.scene's cast['strip'] callback

    keys      Plan keys [(t, d)] along the route (px). A cow never trots: keep her at or under herd.SPEED
              (45 px a second on the strip; herd.SPEED * size on the hill).
    acts      [(t0, t1, fn)]: while she stands, fn(tau) (tau = t - t0) gives the pose she plays; it is blended
              in and out over 0.3 s. Give acts only inside waits.
    gait      'walk', or 'trot' (the calf only)
    carry     degrees the head hangs as she walks (0 fresh, 20 tired or careful: on the ice)
    The lead cow's bell is a pendulum run over the whole plan: .bell_hits are the strike times (seconds)."""

    def __init__(self, who, route, keys, acts=(), gait='walk', carry=0.0, lift=1.0, ramp=0.7):
        self.who, self.route, self.plan = who, route, Plan(keys, ramp)
        self.acts, self.gait, self.carry, self.lift = list(acts), gait, carry, lift
        self._bell = None

    def state(self, t, bell=True):
        d, rest = self.plan(t)
        st = self.route.at(d)
        pose = step_pose(self.who, self.route.units(d, self.who), st['slope'], rest, t, self.carry, self.lift, self.gait)
        for t0, t1, fn in self.acts:
            if t0 - 0.001 <= t <= t1 + 0.3:
                w = smooth(clamp((t - t0) / 0.3)) * (1 - smooth(clamp((t - t1) / 0.3)))
                if w > 0:
                    pose = blend(pose, fn(t - t0), w, self.who)
        if bell and _kind(self.who) == 'lead':
            if self._bell is None:
                self._bell = False
                ks = self.plan.keys
                self._bell = Bell(lambda tt: self._throat(tt), ks[0][0], ks[-1][0])
            if self._bell:
                pose['bell'] = clamp(0.25 * pose.get('bell', 0.0) + self._bell.angle(t), -70, 70)
        st.update(pose=pose, rest=rest)
        return st

    def _throat(self, t):
        st = self.state(t, bell=False)
        a = anchors(self.who, st['pose'], st['x'], st['y'], st['s'], st['facing'])
        return a['throat']

    @property
    def bell_hits(self):
        if _kind(self.who) != 'lead':
            return []
        self.state(self.plan.keys[0][0])
        return list(self._bell.hits) if self._bell else []

    def hoof_falls(self, t0, t1, dt=1 / 48.0):
        """[(t, x_world, y_world, leg)] each time a hoof comes down between t0 and t1: for hoof sounds, rings in
        the shallows, dints in the path."""
        out, prev = [], None
        n = int((t1 - t0) / dt)
        for i in range(n + 1):
            t = t0 + i * dt
            st = self.state(t, bell=False)
            up = {leg: (st['pose'][leg][0] == 'ik' and st['pose'][leg][2] < st['slope'] * st['pose'][leg][1] * _rig(self.who).kx - 0.6)
                  for leg in LEGS}
            if prev:
                for leg in LEGS:
                    if prev[leg] and not up[leg] and st['rest'] < 0.9:
                        k = st['s'] * _size(self.who)
                        out.append((round(t, 3), st['x'] + st['facing'] * st['pose'][leg][1] * _rig(self.who).kx * k, st['y'], leg))
            prev = up
        return out

    def draw(self, ink, t, oy=0, layer=None, nose_to=None, far=None, **kw):
        """Draw her at time t. layer: only draw if she is in that porch.scene layer now ('hill' or 'strip' or
        'front'); None draws her wherever she is. Returns what cow() returns (plus x, y, d, layer, rest), or None."""
        st = self.state(t)
        if layer is not None and st['layer'] != layer:
            return None
        if far is None:
            far = clamp((0.62 - st['rel']) / 0.5) * 0.5
        a = cow(ink, self.who, st['pose'], st['x'], st['y'], st['s'], st['facing'], oy, nose_to=nose_to,
                squash=st['squash'], far=far, **kw)
        a.update(x=st['x'], y=st['y'], d=st['d'], layer=st['layer'], rest=st['rest'])
        return a


def stand_round(cx=790.0, who=HERD, y=None, spread=1.0):
    """Where the herd stands round the wet dogs lying at about world x = cx - 90 .. cx + 90: two cows behind
    them, a cow at each end, a cow further out at each end, all with their heads in toward the dogs; the calf
    at the left end, nearest the water. Returns [dict(who, x, y, s, facing, back, nose)], furthest first: draw
    them in this order, with the dogs after the back=True cows and before the others. nose is a world point to
    give cow(nose_to=) so the head hangs over the dogs."""
    cows = [w for w in who if w != 'calf']
    spots = [(-58, -12, 0.92, 1, True), (62, -13, 0.92, -1, True), (-160, -5, 0.97, 1, False), (166, -6, 0.97, -1, False),
             (-236, 3, 1.0, 1, False), (238, 2, 1.0, -1, False)]
    out = []
    for w, (dx, dy, sc, f, back) in zip(cows, spots):
        x = cx + dx * spread
        gy = (meadow_y(x) if y is None else y) + dy
        out.append(dict(who=w, x=x, y=gy, s=S * sc, facing=f, back=back, nose=(x + f * 96 * sc, gy - 30 * sc)))
    if 'calf' in who:
        x = cx - 118 * spread
        gy = (meadow_y(x) if y is None else y) + 6
        out.append(dict(who='calf', x=x, y=gy, s=S, facing=1, back=False, nose=(x + 40, gy - 14)))
    return sorted(out, key=lambda o: o['y'])


# ------------------------------------------------------------------ checks ---

def check(verbose=True):
    """MEASURED checks. Raises AssertionError on failure; returns the numbers."""
    out = {}
    # 1 joint limits and reach in every named performance
    bad = []
    perf = dict(stand=lambda u, w: stand(u * 6, w), look_down=lambda u, w: look_down(u * 4, u, w), drink=lambda u, w: drink(u * 4, u, w),
                nose_touch=lambda u, w: nose_touch(u * 2.8, None, w), yield_to=lambda u, w: yield_to(u * 1.6, w),
                nudge=lambda u, w: nudge(u * 2.0, w), stamp=lambda u, w: stamp(u * 2.4, w), warm=lambda u, w: warm(u * 8, w),
                fold_down=lambda u, w: fold_down(u, w), get_up=lambda u, w: get_up(u, w), lie=lambda u, w: lie(u * 6, w),
                sleep=lambda u, w: sleep(u * 6, w, u), calf_nosed=lambda u, w: calf_nosed(u * 2.2, w), calf_skid=lambda u, w: calf_skid(u, w))
    for name, fn in perf.items():
        for who in ('lead', 'second', 'calf'):
            if name.startswith('calf') and who != 'calf':
                continue
            for k in range(41):
                v = cc.solve(fn(k / 40.0, who), _kind(who))['violations']
                if v:
                    bad.append((name, who, k, v[:2]))
    out['violations'] = len(bad)
    assert not bad, bad[:6]
    # 2 planted hooves do not slide on the strip (constant size): worst drift of a hoof while it is down
    worst = 0.0
    for who, gait in (('lead', 'walk'), ('second', 'walk'), ('calf', 'walk'), ('calf', 'trot')):
        k = S * _size(who)
        R = _rig(who)
        down = {}
        for i in range(400):
            dist = i * 0.6
            p = step_pose(who, dist, 0.0, 0.0, gait=gait)
            for leg in LEGS:
                if p[leg][0] == 'ik' and abs(p[leg][2]) < 1e-6:
                    wx = (dist + p[leg][1] * R.kx) * k
                    if leg in down:
                        worst = max(worst, abs(wx - down[leg]))
                    else:
                        down[leg] = wx
                else:
                    down.pop(leg, None)
    out['hoof_drift_px'] = round(worst, 3)
    assert worst < 0.05, worst
    # 3 sizes on the strip
    a = anchors('lead', cc.POSES['stand'], 0, 0)
    c = anchors('calf', stand(0, 'calf'), 0, 0)
    out['lead_withers_px'] = round(-a['withers'][1], 1)
    out['calf_withers_px'] = round(-c['withers'][1], 1)
    out['lead_length_px'] = round(a['muzzle'][0] - a['rump'][0], 1)
    assert abs(out['lead_withers_px'] - 104) < 1 and abs(out['calf_withers_px'] - 60) < 3
    # 4 the muzzle reaches the water from the strip, and a dog's nose 40 px above the sill
    q, miss = aim(drink(0, 1, 'lead'), 'lead', (reach('lead') / S, (SURFACE - STRIP_Y) / S))
    out['dog_nose_miss_px'] = round(aim(nose_touch(0.9), 'lead', (reach('lead', -80, face=78.0) / S, -80 / S), 1.0, 78.0)[1] * S, 2)
    out['drink_miss_px'] = round(miss * S, 2)
    out['reach_px'] = round(reach('lead'), 1)
    assert miss * S < 1.5
    # 5 the route: single file means the same d never holds two cows; here, that the route is monotone in d
    out['path_px'] = round(PATH.length, 1)
    out['gate_d'] = round(D_GATE, 1)
    assert PATH.turns and len(PATH.turns) == 1
    # 6 the bell lags: after a stop it is still swinging
    wk = Walker('lead', PATH, [(0.0, d_at(380)), (3.0, d_at(500)), (6.0, d_at(500))])
    out['bell_after_stop_deg'] = round(max(abs(wk.state(3.0 + k / 24.0)['pose']['bell']) for k in range(1, 18)), 1)
    out['bell_hits'] = len(wk.bell_hits)
    assert out['bell_after_stop_deg'] > 3.0
    if verbose:
        for k, v in out.items():
            print(f'  {k}: {v}')
    return out


# ------------------------------------------------------------------ sheets ---

def _dusk(size, split=None):
    """A plain dusk card for the sheets: violet down to amber, and (below `split`) bone paper for silhouettes."""
    w, h = size
    im = Image.new('RGB', size, (236, 228, 214))
    top, bot = (62, 44, 104), (224, 138, 104)
    hh = split or h
    px = im.load()
    for y in range(hh):
        f = (y / hh) ** 1.6
        c = tuple(int(lerp(a, b, f)) for a, b in zip(top, bot))
        for x in range(w):
            px[x, y] = c
    return im


def _ground(im, x0, x1, y, col=(40, 28, 52)):
    ImageDraw.Draw(im).line([(x0, y), (x1, y)], fill=col, width=2)


def sheet_poses(path):
    """Every pose, in paper at dusk and again as a silhouette."""
    cells = [
        ('lead', stand(0.3, 'lead'), {}), ('second', stand(1.2, 'second'), {}), ('calf', stand(0.7, 'calf'), {}),
        ('lead', notice(stand(0.3, 'lead', chew=0, alert=0.7)), {}), ('lead', look_down(0, 1), {}), ('lead', drink(0.2, 1), {'nose': (None, 6)}),
        ('lead', nose_touch(0.9), {'nose': (None, -96)}), ('fourth', yield_to(1.4), {}), ('mother', nudge(0.75), {'nose': (None, -40)}),
        ('calf', calf_nosed(0.8), {}), ('calf', calf_skid(0.2), {}), ('calf', step_pose('calf', 60, gait='trot'), {}),
        ('lead', stamp(1.22), {}), ('lead', stamp(STAMP_HIT + 0.02), {}), ('lead', warm(2.6), {}),
        ('lead', fold_down(0.5), {}), ('lead', fold_down(0.74), {}), ('lead', lie(0.5), {}),
        ('lead', sleep(1.0), {}), ('calf', sleep(1.0, 'calf'), {}), ('lead', get_up(0.72), {}),
    ]
    cols, cw, ch = 6, 310, 190
    rows = (len(cells) + cols - 1) // cols
    im = Image.new('RGB', (cols * cw, rows * ch * 2), (236, 228, 214))
    top = _dusk((cols * cw, rows * ch))
    im.paste(top, (0, 0))
    for i, (who, pose, opt) in enumerate(cells):
        cx, cy = (i % cols) * cw + cw // 2 - 12, (i // cols) * ch + ch - 22
        for half, flat in ((0, None), (rows * ch, (22, 16, 26))):
            _ground(im, cx - cw // 2 + 26, cx + cw // 2 + 2, cy + half, (40, 28, 52) if flat is None else (120, 110, 100))
            nose = None
            if 'nose' in opt:
                nose = (cx + reach(who, opt['nose'][1] / 1.2, face=pose.get('_face')) * 1.2, cy + half + opt['nose'][1])
            a = cow(im, who, pose, cx, cy + half, 1.2 * S, 1, nose_to=nose, rim=0.8, flat=flat)
            if flat is None and a['breath'] > 0:
                breath(im, a['muzzle'][0], a['muzzle'][1], a['breath'])
    im.save(path)
    return path


def sheet_walk(path, who='lead', gait='walk', n=8, s=None):
    """One cycle of the walk in n frames, paper above and silhouette below, with the hoof line."""
    s = 1.15 * S if s is None else s
    cw, ch = 300, 190
    im = Image.new('RGB', (n * cw, ch * 2), (236, 228, 214))
    im.paste(_dusk((n * cw, ch)), (0, 0))
    stride = _rig(who).stride * (0.86 if gait == 'trot' else 1.0)
    for half, flat in ((0, None), (ch, (22, 16, 26))):
        _ground(im, 0, n * cw, ch - 20 + half, (40, 28, 52) if flat is None else (120, 110, 100))
        for i in range(n):
            pose = step_pose(who, stride * i / n - WHO[who]['phase'] * _rig(who).stride, gait=gait)
            cow(im, who, pose, i * cw + cw // 2 - 14, ch - 20 + half, s, 1, rim=0.8, flat=flat)
    im.save(path)
    return path


def _strip(frames, path, cols=2):
    """frames: [PIL RGB] film frames, laid out in a grid, in reading order."""
    w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    im = Image.new('RGB', (w * cols, h * rows), (18, 14, 24))
    for i, f in enumerate(frames):
        im.paste(f, ((i % cols) * w, (i // cols) * h))
    im.save(path)
    return path


def _scene(t, cast, oy=0, **kw):
    """One film frame of the porch with a cast, for the strips (falls back to a dusk card without porch.py)."""
    from kit import Ink
    ink = Ink(t, int(t * 24), boil=0)
    if _porch is not None:
        _porch.scene(ink, t, oy, cast=cast, **kw)
    else:
        ink.img.paste(_dusk((W, H)), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, 'RGBA')
        for k in ('hill', 'strip', 'sill', 'front'):
            if k in cast:
                cast[k](ink, t, oy)
    return ink.img.convert('RGB')


def file_plan(n=7, t0=0.0, dog_nose=(548.0, 306.0), lead_to=None):
    """The opening file (S1, t0 .. t0 + 8 s) as Walkers: the lead through the gate at about t0 + 1.6, a stop for
    the nose touch (she has stopped by t0 + 3.4 with her muzzle able to come down on dog_nose, a WORLD point;
    she plays nose_touch on the dog's clock from t0 + 3.0 and walks on at t0 + 5.6), and on to the drinking
    place; the second down to wait in the gate; the rest closing up the hill behind her. Returns {who: Walker}."""
    order = ('lead', 'second', 'mother', 'calf', 'fourth', 'fifth', 'sixth')[:n]
    stop = d_at(dog_nose[0] - reach('lead', dog_nose[1] - STRIP_Y, face=78.0))
    lead_to = (600.0 - reach('lead')) if lead_to is None else lead_to
    out = {}
    for k, who in enumerate(order):
        if who == 'lead':
            keys = [(t0, D_GATE - 40), (t0 + 3.4, stop), (t0 + 5.6, stop), (t0 + 5.6 + max(1.2, (d_at(lead_to) - stop) / SPEED), d_at(lead_to))]
            out[who] = Walker(who, PATH, keys, acts=[(t0 + 3.0, t0 + 5.6, lambda tau: nose_touch(tau)),
                                                    (keys[-1][0], keys[-1][0] + 600.0, lambda tau: drink(tau, tau / 1.2))])
        else:
            d1 = hill_spot(k - 1)
            d0 = max(0.0, d1 - (150 if k < 3 else 80) * PATH.at(d1)['rel'] ** 0.5)
            out[who] = Walker(who, PATH, [(t0, d0), (t0 + 6.0 + 0.5 * k, d1)])
    return out


def sheets(out_dir=HERE):
    out_dir = Path(out_dir)
    made = [sheet_poses(out_dir / 'herd_sheet.png'),
            sheet_walk(out_dir / 'herd_strip_walk.png', 'lead'),
            sheet_walk(out_dir / 'herd_strip_trot.png', 'calf', 'trot', s=1.9 * S)]
    try:
        import dog
    except Exception:
        dog = None

    def lead_dog(ink, pose, x=470, y=394, oy=0, scale=0.6, facing=1):
        if dog is not None:
            return dog.draw_dog(ink, pose, x, y - oy, scale=scale, facing=facing)

    def dog_nose(t):
        if dog is None:
            return (548.0, 306.0)
        return dog.draw_dog(Image.new('RGB', (W, H)), dog.nose_touch(t - 3.0, height=DOG_NOSE_UP), 470, 394, scale=0.6, facing=1)['nose']

    # S1: the file comes down the path, the lead touches noses with the dog and goes on to drink
    fp = file_plan(dog_nose=dog_nose(3.9))

    def nose(t):
        if t > 5.8:
            return (600, SURFACE)
        n = dog_nose(t)
        return (n[0] + 10, n[1] - 3)

    frames = []
    for t in (0.6, 2.2, 3.3, 3.9, 4.75, 7.9):
        def hill(ink, t, oy):
            for w in reversed(HERD):
                fp[w].draw(ink, t, oy, layer='hill')

        def strip(ink, t, oy):
            for w in reversed(HERD):
                fp[w].draw(ink, t, oy, layer='strip', nose_to=nose(t) if w == 'lead' else None)

        def sill(ink, t, oy):
            if dog is not None:
                lead_dog(ink, dog.nose_touch(t - 3.0, height=DOG_NOSE_UP) if 3.0 <= t <= 5.8 else dog.watch(t))
            if 3.0 < t < 5.8:                                   # her head again, over the dog
                a = fp['lead'].draw(ink, t, oy, nose_to=nose(t), only='head')
                breath(ink, a['muzzle'][0], a['muzzle'][1], a['breath'], a['facing'])

        frames.append(_scene(t, dict(hill=hill, strip=strip, sill=sill)))
    made.append(_strip(frames, out_dir / 'herd_strip_file.png'))

    # S3: the queue waits its turn; the calf starts after the dog and its mother noses it back into line
    frames = []
    for t in (0.0, 0.5, 0.85, 1.2, 1.9, 2.8):
        def hill(ink, t, oy):
            for k, w in enumerate(('fourth', 'fifth', 'sixth')):
                st = PATH.at(hill_spot(k + 1))
                if st['layer'] == 'hill':
                    cow(ink, w, step_pose(w, PATH.units(st['d'], w), st['slope'], 1.0, t), st['x'], st['y'], st['s'], st['facing'], oy,
                        far=clamp((0.62 - st['rel']) / 0.5) * 0.5)

        def strip(ink, t, oy):
            cn = calf_nosed(t)
            cx = 520 - 16 * cn['_push']
            cow(ink, 'mother', nudge(t), 440, STRIP_Y, S, 1, oy, nose_to=(cx + 30, 352))
            cow(ink, 'calf', cn, cx, STRIP_Y + 3, S, 1, oy)

        def sill(ink, t, oy):
            if dog is not None:
                lead_dog(ink, dog.walk(t) if hasattr(dog, 'walk') else dog.watch(t), 590 + 14 * t, 396, oy)

        frames.append(_scene(76 + t, dict(hill=lambda i, tt, oy, f=hill: f(i, tt - 76, oy), strip=lambda i, tt, oy, f=strip: f(i, tt - 76, oy),
                                          sill=lambda i, tt, oy, f=sill: f(i, tt - 76, oy))))
    made.append(_strip(frames, out_dir / 'herd_strip_nosed_back.png'))

    frames = []
    for t, p in ((0.0, 0.0), (1.0, 0.6), (2.0, 1.0), (4.0, 1.0)):
        def strip(ink, t, oy, p=p):
            x = 600 - reach('lead')
            cow(ink, 'lead', drink(t, p) if t < 3 else look_down(t, 1.0), x, STRIP_Y, S, 1, oy,
                nose_to=(600, 400) if t < 3 else (596, 372))
            st = PATH.at(hill_spot(0))
            cow(ink, 'second', step_pose('second', PATH.units(st['d'], 'second'), st['slope'], 1.0, t), st['x'], st['y'], st['s'], st['facing'], oy)
        frames.append(_scene(10 + t, dict(strip=lambda i, tt, oy, f=strip: f(i, tt - 10, oy))))
    made.append(_strip(frames, out_dir / 'herd_strip_drink.png'))

    # S4: turned aside by the herding dog
    try:
        import kennel_a as ka
    except Exception:
        ka = None
    U4 = 0.6
    r4 = off_path(U4, (770, None))
    x0, y0, s0 = _path_point(U4)
    w4 = Walker('fourth', r4, [(1.6, r4.find(x0, last=False)), (1.6 + (r4.length - r4.find(x0, last=False)) / (SPEED * 0.8), r4.length)])
    frames = []
    for t in (0.2, 1.0, 1.5, 2.3, 4.0, 7.0):
        def hill(ink, t, oy):
            for k, wh in enumerate(('sixth', 'fifth')):
                u = U4 - 0.36 + 0.2 * k
                px_, py_, ps = _path_point(u)
                cow(ink, wh, notice(stand(t, wh), clamp(t - 1)), px_, py_, ps * S, -1, oy, far=0.25)
            if t < 1.6:
                cow(ink, 'fourth', yield_to(t), x0, y0, s0 * S, -1, oy)
            else:
                w4.draw(ink, t, oy, layer='hill')
            if ka is not None:
                dx_, dy_, ds = _path_point(U4 + 0.2)
                ka.herding_dog(ink, dx_, dy_ - oy, 0.75, 1, "eye", p=clamp(t / 0.6))

        def strip(ink, t, oy):
            if t >= 1.6:
                w4.draw(ink, t, oy, layer='strip')

        frames.append(_scene(92 + t, dict(hill=lambda i, tt, oy, f=hill: f(i, tt - 92, oy), strip=lambda i, tt, oy, f=strip: f(i, tt - 92, oy))))
    made.append(_strip(frames, out_dir / 'herd_strip_turned.png'))

    # S5: out on the ice, the stamp; then standing round, steaming
    ir = ice_route(700, 606)
    wk = Walker('lead', ir, [(0.0, 0.0), (3.2, ir.length), (6.0, ir.length)], carry=16.0,
                acts=[(3.4, 6.0, lambda tau: stamp(tau))])
    frames = []
    for t in (1.6, 4.0, 4.62, 4.8, 5.4):
        def front(ink, t, oy):
            wk.draw(ink, t, oy, reflect=SURFACE + 2, rim=0.15)
        hit = t - 3.4 - STAMP_HIT
        frames.append(_scene(119 + t, dict(front=lambda i, tt, oy, f=front: f(i, tt - 119, oy)), freeze=1.0,
                             stamps=[(wk.state(t)['x'] + 40, clamp(hit / 0.3))] if hit > 0 else (), crack=clamp(hit / 1.2) if hit > 0 else 0))
    made.append(_strip(frames, out_dir / 'herd_strip_ice.png'))

    frames = []
    for t in (0.0, 2.4):
        def strip(ink, t, oy):
            for o in stand_round(760):
                a = cow(ink, o['who'], warm(t, o['who']) if o['who'] != 'calf' else stand(t, 'calf', alert=0.4), o['x'], o['y'], o['s'],
                        o['facing'], oy, nose_to=o['nose'] if o['who'] != 'calf' else None, rim=0.1)
                steam_on(ink, t, a, 1.0)
        frames.append(_scene(134 + t, dict(strip=lambda i, tt, oy, f=strip: f(i, tt - 134, oy)), dusk=0.8))
    made.append(_strip(frames, out_dir / 'herd_strip_warm.png'))

    # S6: she folds down behind the sill; the calf asleep
    frames = []
    for p in (0.0, 0.3, 0.52, 0.76, 1.0):
        def strip(ink, t, oy, p=p):
            cow(ink, 'lead', fold_down(p) if p < 1 else lie(t), 645, STRIP_Y, S, -1, oy)
            cow(ink, 'calf', sleep(t, 'calf'), 790, meadow_y(790), S, -1, oy, nose_to=(752, 362))
            for k, w in enumerate(('second', 'fifth', 'sixth')):
                cow(ink, w, sleep(t, w), 850 + 70 * k, meadow_y(900) - 6 + 4 * k, S * 0.92, -1, oy, rim=0.0)
        frames.append(_scene(173 + 2 * p, dict(strip=strip), dusk=1.0, stars=1.0))
    made.append(_strip(frames, out_dir / 'herd_strip_fold.png'))
    return made


if __name__ == '__main__':
    print('checks (MEASURED):')
    check()
    for p in sheets(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE):
        print('wrote', p)
