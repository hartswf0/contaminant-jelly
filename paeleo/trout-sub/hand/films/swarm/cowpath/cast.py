"""cast.py: the cow of "Don't Pave the Cow Paths". One puppet, three materials.

She is a cut silhouette on pins (barrel, shoulder, hip, udder, neck, head, jaw, ear, two horns, bell, tail,
four two-part legs), posed by joint angles with limits, and walked by planting her hooves on the ground and
carrying the body over them. The same pieces draw as

    style='shadow'   black card against a backlight          (ACT 1, Reiniger)
    style='line'     ink contour on paper, hidden lines cut  (ACT 2, Foldes)
    style='paper'    cream and brown cut paper, brass brads  (ACT 3, with the c13 river)

How she is recognised in all three: ONE HORN UP, ONE HORN CRUMPLED FORWARD, and A BELL UNDER HER NECK.

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))      # films/swarm/cowpath
    import cast
    a = cast.place(ink, cast.POSES['graze'], 300, 430, s=0.8, style='shadow')
    a = cast.walk_on(ink, x, ground, s=0.8, style='shadow')        # ground: px -> px, hooves stay planted

Everything is documented in CAST.md. `python3 films/swarm/cowpath/cast.py` writes the pose sheet, the walk
strip, the material sheet and prints the measured checks (films/stills/cowpath_cast/).

Units. The puppet is built in "cow units": x forward (the way she faces), y down, origin on the ground under
the middle of her barrel. Standing she is 141 units at the withers and about 260 from nose to tail. `s` is
pixels per unit. Angles are degrees. For every joint, POSITIVE LOWERS THE NOSE END: pitch+ tips the body nose
down, neck+ lowers the head, head+ tucks the muzzle, shoulder+ / hip+ rock that piece the same way. Leg
angles are measured from "straight down from the body", POSITIVE = HOOF FORWARD.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import PAPER, INK, BRASS, W, H, clamp, lerp  # noqa: E402

BLACK = (20, 16, 14)            # the card of the shadow theatre
SS = 3                          # supersampling of every sprite

# ------------------------------------------------------------------ geometry helpers ---


def _rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _stand(pts, pin, deg):
    """Local points (pin at 0,0) laid into the standing cow at `pin`, turned `deg`."""
    return [(pin[0] + q[0], pin[1] + q[1]) for q in (_rot(p, deg) for p in pts)]


def _smooth(pts, n=5, closed=True):
    """Catmull-Rom through the points: the scissors cut a curve, not a polygon."""
    out = []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = (pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]) if closed else \
            (pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, m - 1)])
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[a]) + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2
                                    + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


class Fr:
    """A rigid frame: p -> R(a) p + t  (a degrees, clockwise on screen = nose down)."""

    def __init__(self, a=0.0, tx=0.0, ty=0.0):
        self.a, self.tx, self.ty = a, tx, ty
        self.c, self.s = math.cos(math.radians(a)), math.sin(math.radians(a))

    def __call__(self, p):
        return (p[0] * self.c - p[1] * self.s + self.tx, p[0] * self.s + p[1] * self.c + self.ty)

    def pin(self, delta, pin):
        """The frame of a piece hinged on this one at `pin`, turned `delta`."""
        r = _rot(pin, delta)
        q = (pin[0] - r[0], pin[1] - r[1])
        t = (q[0] * self.c - q[1] * self.s + self.tx, q[0] * self.s + q[1] * self.c + self.ty)
        return Fr(self.a + delta, t[0], t[1])


# ------------------------------------------------------------------ the cut pieces ---
# All in standing cow units unless a comment says "local".

C_BARREL = (0.0, -98.0)                 # the body pitches about this point
PIN = dict(
    shoulder=(40.0, -104.0),            # shoulder piece on the barrel
    hip=(-42.0, -106.0),                # hip piece on the barrel
    neck=(70.0, -114.0),                # neck on the shoulder piece
    udder=(-44.0, -66.0),               # udder on the hip piece
    tail=(-89.0, -123.0),               # tail head on the hip piece
    fore=(58.0, -95.0),                 # point of shoulder: both fore legs
    hind=(-64.0, -104.0),               # hip joint: both hind legs
)
FAR_DX = 5.0                            # the far legs' pins sit this much forward (a hint of depth)
NECK_ANGLE = -12.0                      # the neck's own axis in the standing cow
HEAD_ANGLE = 38.0                       # the face's slope in the standing cow
NECK_LEN = 50.0
PIN['head'] = (PIN['neck'][0] + NECK_LEN * math.cos(math.radians(NECK_ANGLE)),
               PIN['neck'][1] + NECK_LEN * math.sin(math.radians(NECK_ANGLE)))

L_FORE = (56.0, 40.0)                   # shoulder to knee, knee to sole
L_HIND = (60.0, 50.0)                   # hip to hock, hock to sole

BARREL = _smooth([(-54, -131), (-28, -133), (0, -131.5), (28, -133), (52, -131), (62, -112), (60, -88), (50, -70),
                  (28, -61), (2, -56), (-24, -58), (-46, -67), (-58, -86), (-62, -110)])
SHOULDER = _smooth([(26, -132), (40, -139), (52, -142), (64, -138), (76, -126), (86, -108), (88, -90), (82, -74),
                    (70, -64), (56, -62), (42, -68), (32, -82), (26, -104)])
HIP = _smooth([(-26, -132), (-40, -139.5), (-52, -137), (-70, -132), (-88, -127), (-94, -112), (-93, -94), (-85, -78),
               (-70, -66), (-54, -64), (-38, -70), (-28, -84), (-24, -108)], n=4)
UDDER = _smooth([(-27, -68), (-29, -57), (-35, -51), (-38.5, -43), (-42, -50), (-47, -49), (-50.5, -42), (-54, -50),
                 (-59, -57), (-61, -68)], n=4)

_NECK_L = [(-14, -20), (8, -22), (30, -18), (48, -15), (58, -6), (57, 10), (44, 17), (26, 23), (8, 31), (-8, 35),
           (-20, 25), (-23, 0)]
NECK = _smooth(_stand(_NECK_L, PIN['neck'], NECK_ANGLE))
BELL_AT = _stand([(39, 17)], PIN['neck'], NECK_ANGLE)[0]            # where the strap leaves the throat

# head, local: pin at the poll end of the skull, x along the face to the muzzle
_HEAD_L = [(-10, -8), (-2, -17), (12, -18), (27, -13), (42, -8), (54, -8.5), (63, -5), (66.5, 3), (62, 8.5),
           (44, 6.5), (26, 8), (13, 17), (-1, 15), (-10, 5)]
_JAW_L = [(4, 3), (22, 5), (42, 4.5), (58, 6.5), (62, 11), (57, 15.5), (40, 14), (23, 17.5), (9, 17), (1, 10)]
_HORN_L = [(-5, -13), (-9, -25), (-5, -36), (6, -43), (3, -35), (0, -27), (5, -15)]            # the good horn
_CRUMP_L = [(3, -16), (9, -25), (20, -27), (29, -20), (22, -21.5), (14, -20), (12, -15)]        # the crumpled one
_EAR_L = [(0, -4.5), (10, -9), (22, -5), (27, 0), (18, 6.5), (5, 5.5)]                          # local to its own pin
_EYE_L = (15.0, -6.0)
_NOSE_L = (63.0, 2.0)
_JAW_PIN_L = (8.0, 9.0)
_EAR_PIN_L = (-6.0, -6.0)
EAR_ANGLE = 162.0                       # the ear's direction in head-local degrees (points back, a little up)

HEAD = _smooth(_stand(_HEAD_L, PIN['head'], HEAD_ANGLE))
JAW = _smooth(_stand(_JAW_L, PIN['head'], HEAD_ANGLE), n=4)
HORN = _smooth(_stand(_HORN_L, PIN['head'], HEAD_ANGLE), n=4)
CRUMP = _smooth(_stand(_CRUMP_L, PIN['head'], HEAD_ANGLE), n=4)
PIN['jaw'] = _stand([_JAW_PIN_L], PIN['head'], HEAD_ANGLE)[0]
PIN['ear'] = _stand([_EAR_PIN_L], PIN['head'], HEAD_ANGLE)[0]
EAR = _smooth(_stand(_EAR_L, PIN['ear'], HEAD_ANGLE + EAR_ANGLE), n=4)
EYE = _stand([_EYE_L], PIN['head'], HEAD_ANGLE)[0]
NOSE = _stand([_NOSE_L], PIN['head'], HEAD_ANGLE)[0]
HORN_TIP = _stand([(6, -43)], PIN['head'], HEAD_ANGLE)[0]

# bell, local: hangs down from (0, 0)
_BELL_L = [(-2.5, -6), (2.5, -6), (3, 2), (6.5, 5), (8.5, 15), (10, 19), (-10, 19), (-8.5, 15), (-6.5, 5), (-3, 2)]
_CLAPPER_L = (0.0, 20.5, 2.8)

# legs, local: pin at (0, 0), the limb hangs down +y, +x is the front of the limb
_FORE_UP = _smooth([(-15, -8), (-6, -17), (8, -16), (17, -4), (15, 16), (10.5, 34), (8.5, 49), (9, 57), (3, 62),
                    (-6, 60), (-7, 48), (-9, 32), (-14, 14)], n=4)
_FORE_LO = _smooth([(-6.5, -5), (0, -7), (6.5, -5), (5, 8), (4.6, 20), (6, 27), (8.5, 30.5)], n=4, closed=False) + \
    [(9.5, 32), (13, 40), (-7, 40), (-7, 33.5), (-9.5, 29.5), (-6, 26)] + \
    _smooth([(-6, 26), (-4.6, 14), (-6.5, -5)], n=4, closed=False)[1:-1]
_HIND_UP = _smooth([(-14, -12), (4, -18), (20, -8), (25, 10), (21, 28), (12.5, 42), (7.5, 53), (7, 61), (1, 66),
                    (-9.5, 64), (-8, 52), (-10, 36), (-16, 14)], n=4)
_HIND_LO = _smooth([(-7, -6), (0, -8), (6, -5), (5, 10), (4.6, 28), (6, 36), (8.5, 40)], n=4, closed=False) + \
    [(9.5, 42), (13, 50), (-7, 50), (-7, 43.5), (-9.5, 39.5), (-6, 36)] + \
    _smooth([(-6, 36), (-4.6, 17), (-7, -6)], n=4, closed=False)[1:-1]
_HOOF_F = [(8.2, 30.5), (9.5, 32), (13, 40), (-7, 40), (-7, 33.5), (-5.5, 31)]
_HOOF_H = [(8.2, 40.5), (9.5, 42), (13, 50), (-7, 50), (-7, 43.5), (-5.5, 41)]

# brown patches for the paper cow, by piece (standing units; clipped to the piece when drawn)
PATCHES = dict(
    barrel=[_smooth([(-30, -140), (-4, -136), (10, -118), (4, -96), (-14, -84), (-34, -92), (-40, -116)], n=4)],
    hip=[_smooth([(-66, -140), (-100, -132), (-100, -100), (-80, -96), (-68, -110)], n=4)],
    shoulder=[_smooth([(60, -146), (92, -128), (96, -100), (78, -96), (66, -112), (52, -124)], n=4)],
    neck=[_smooth([(84, -140), (120, -146), (126, -126), (104, -116), (86, -122)], n=4)],
    head=[_smooth(_stand([(-12, -20), (16, -20), (24, -6), (14, 4), (-2, 2), (-12, -6)], PIN['head'], HEAD_ANGLE), n=4)],
)

# ------------------------------------------------------------------ joint limits ---

LIMITS = dict(
    pitch=(-80, 30), shoulder=(-12, 12), hip=(-30, 14), neck=(-65, 82), head=(-48, 62), jaw=(0, 28), ear=(-55, 60),
    udder=(-25, 25), bell=(-70, 70), eye=(0, 2.0),
    fore_upper=(-48, 105), fore_knee=(-140, 6),          # the knee folds the hoof BACK only
    hind_upper=(-55, 80), hind_hock=(4, 150),            # the hock folds the hoof FORWARD only
)
LEGS = ('nf', 'ff', 'nh', 'fh')         # near fore, far fore, near hind, far hind
STANCE = dict(nf=62.0, ff=53.0, nh=-73.0, fh=-60.0)      # where the hooves stand, x under the body

# ------------------------------------------------------------------ poses ---


def _pose(**kw):
    p = dict(dx=0.0, dy=0.0, pitch=0.0, shoulder=0.0, hip=0.0, neck=0.0, head=0.0, jaw=0.0, ear=0.0,
             tail=(4.0, 6.0, 8.0), udder=0.0, bell=0.0, eye=1.0,
             nf=('ik', STANCE['nf'], 0.0), ff=('ik', STANCE['ff'], 0.0),
             nh=('ik', STANCE['nh'], 0.0), fh=('ik', STANCE['fh'], 0.0))
    p.update(kw)
    return p


POSES = dict(
    stand=_pose(),
    # head down in the grass, one fore hoof set forward, weight on the shoulders
    graze=_pose(pitch=4.5, dy=2.0, shoulder=5.0, neck=60.0, head=-24.0, jaw=6.0, ear=-8.0, tail=(2.0, 4.0, 6.0),
                nf=('ik', 48.0, 0.0), ff=('ik', 68.0, 0.0)),
    # something caught her eye: head up and level, ears forward, stops chewing
    look_up=_pose(pitch=-1.0, dy=1.5, neck=-30.0, head=12.0, ear=30.0, eye=1.25, tail=(6.0, 10.0, 10.0)),
    # recoil: weight thrown back on the hocks, fore legs braced, head high, tail up
    startle=_pose(dx=-12.0, dy=10.0, pitch=-8.0, hip=4.0, neck=-50.0, head=-14.0, jaw=10.0, ear=48.0, eye=1.9,
                  tail=(62.0, 30.0, -30.0), udder=-10.0, bell=-35.0,
                  nf=('ik', 67.0, 0.0), ff=('ik', 61.0, 0.0), nh=('ik', -70.0, 0.0), fh=('ik', -56.0, 0.0)),
    # standing, spent: head hung below the knees of the spine, ears down, tail dead
    slump=_pose(dy=5.0, pitch=3.0, shoulder=6.0, hip=-4.0, neck=38.0, head=18.0, ear=-42.0, eye=0.3,
                tail=(0.0, 0.0, 0.0), nf=('ik', 58.0, 0.0), ff=('ik', 60.0, 0.0), nh=('ik', -68.0, 0.0), fh=('ik', -64.0, 0.0)),
)


def with_(pose, **kw):
    """A copy of a pose with some keys replaced."""
    q = dict(pose)
    q.update(kw)
    return q


# ------------------------------------------------------------------ solving a pose ---


def _ik(pivot, target, l1, l2, bend):
    """Two-bone leg. Returns absolute angles (from straight down, + forward) of upper and lower, and reached."""
    dx, dy = target[0] - pivot[0], target[1] - pivot[1]
    d0 = math.hypot(dx, dy)
    d = clamp(d0, abs(l1 - l2) + 0.5, l1 + l2 - 0.02)
    phi = math.atan2(dx, dy)
    alpha = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    a1 = phi + bend * alpha
    beta = math.acos(clamp((l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2), -1, 1))
    a2 = a1 - bend * (math.pi - beta)
    return math.degrees(a1), math.degrees(a2), abs(d0 - d) < 1e-6


def _lim(name, v, bad, where=None):
    lo, hi = LIMITS[name]
    if v < lo - 1e-6 or v > hi + 1e-6:
        bad.append((where or name, round(v, 1), (lo, hi)))
    return clamp(v, lo, hi)


def solve(pose):
    """Pose -> the puppet laid out in cow units: frames, leg angles, every piece's polygon, and the anchors.

    Joint limits are enforced here (values outside are clamped and listed in ['violations'])."""
    bad = []
    g = lambda k: _lim(k, float(pose.get(k, 0.0)), bad)
    pitch, sh, hp = g('pitch'), g('shoulder'), g('hip')
    neck, head, jaw, ear, udder = g('neck'), g('head'), g('jaw'), g('ear'), g('udder')
    cx, cy = C_BARREL
    r = _rot((cx, cy), pitch)
    F_b = Fr(pitch, cx - r[0] + pose.get('dx', 0.0), cy - r[1] + pose.get('dy', 0.0))
    F_s, F_h = F_b.pin(sh, PIN['shoulder']), F_b.pin(hp, PIN['hip'])
    F_n = F_s.pin(neck, PIN['neck'])
    F_hd = F_n.pin(head, PIN['head'])
    F_j, F_e = F_hd.pin(jaw, PIN['jaw']), F_hd.pin(ear, PIN['ear'])
    F_u = F_h.pin(udder, PIN['udder'])

    legs, ang, hoof, joint = {}, {}, {}, {}
    for name in LEGS:
        fore, near = name[1] == 'f', name[0] == 'n'
        par = F_s if fore else F_h
        pin = PIN['fore'] if fore else PIN['hind']
        piv = par((pin[0] + (0 if near else FAR_DX), pin[1]))
        l1, l2 = L_FORE if fore else L_HIND
        spec = pose[name]
        ku, kk = ('fore_upper', 'fore_knee') if fore else ('hind_upper', 'hind_hock')
        if spec[0] == 'ik':
            a1, a2, ok = _ik(piv, (spec[1], spec[2]), l1, l2, 1 if fore else -1)
            if not ok:
                bad.append((name + ' reach', round(math.hypot(spec[1] - piv[0], spec[2] - piv[1]), 1), l1 + l2))
            up, kn = a1 + par.a, a2 - a1
            if up != _lim(ku, up, bad, name + ' upper') or kn != _lim(kk, kn, bad, name + ' knee'):
                a1 = clamp(up, *LIMITS[ku]) - par.a
                a2 = a1 + clamp(kn, *LIMITS[kk])
        else:
            up, kn = _lim(ku, spec[1], bad, name + ' upper'), _lim(kk, spec[2], bad, name + ' knee')
            a1 = up - par.a
            a2 = a1 + kn
        ang[name] = (a1 + par.a, a2 - a1)                       # relative: upper to its piece, knee to upper
        kx, ky = piv[0] + l1 * math.sin(math.radians(a1)), piv[1] + l1 * math.cos(math.radians(a1))
        hx, hy = kx + l2 * math.sin(math.radians(a2)), ky + l2 * math.cos(math.radians(a2))
        hoof[name], joint[name] = (hx, hy), (piv, (kx, ky))
        up_l, lo_l, hf_l = (_FORE_UP, _FORE_LO, _HOOF_F) if fore else (_HIND_UP, _HIND_LO, _HOOF_H)
        U, L = Fr(-a1, piv[0], piv[1]), Fr(-a2, kx, ky)
        legs[name] = ([U(p) for p in up_l], [L(p) for p in lo_l], [L(p) for p in hf_l])

    # tail: three absolute angles from hanging (+ = lifted to the rear), drawn as one tapering strip and a switch
    ta = pose.get('tail', (4.0, 6.0, 8.0))
    p0 = F_h(PIN['tail'])
    pts, p, a = [p0], p0, 0.0
    for seg, da in zip((40.0, 34.0, 26.0), ta):
        a = da
        p = (p[0] - seg * math.sin(math.radians(a)), p[1] + seg * math.cos(math.radians(a)))
        pts.append(p)
    spine = _smooth([pts[0], ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2), pts[1], pts[2], pts[3]], n=5, closed=False)
    left, right = [], []
    m = len(spine)
    for i, q in enumerate(spine):
        a_, b_ = spine[max(i - 1, 0)], spine[min(i + 1, m - 1)]
        nx, ny = -(b_[1] - a_[1]), (b_[0] - a_[0])
        nl = math.hypot(nx, ny) or 1.0
        f = i / (m - 1)
        wdt = lerp(4.2, 2.2, min(1, f / 0.62)) if f < 0.62 else 2.2 + 5.2 * math.sin(math.pi * ((f - 0.62) / 0.38) ** 0.8)
        left.append((q[0] + nx / nl * wdt, q[1] + ny / nl * wdt))
        right.append((q[0] - nx / nl * wdt, q[1] - ny / nl * wdt))
    tail_poly = left + right[::-1]

    # bell: hangs plumb from the throat whatever the neck does, plus its own swing
    bp = F_n(BELL_AT)
    F_bell = Fr(_lim('bell', float(pose.get('bell', 0.0)), bad), bp[0], bp[1])
    bell_poly = [F_bell(q) for q in _BELL_L]
    clap = F_bell(_CLAPPER_L[:2])

    T = lambda F, poly: [F(q) for q in poly]
    eye = _lim('eye', float(pose.get('eye', 1.0)), bad)
    # back to front
    parts = [
        ('tail', tail_poly, 'hide'),
        ('fh_upper', legs['fh'][0], 'far'), ('fh_lower', legs['fh'][1], 'far'),
        ('ff_upper', legs['ff'][0], 'far'), ('ff_lower', legs['ff'][1], 'far'),
        ('crump', T(F_hd, CRUMP), 'horn'),
        ('barrel', T(F_b, BARREL), 'hide'),
        ('hip', T(F_h, HIP), 'hide'),
        ('udder', T(F_u, UDDER), 'udder'),
        ('nh_upper', legs['nh'][0], 'hide'), ('nh_lower', legs['nh'][1], 'hide'),
        ('shoulder', T(F_s, SHOULDER), 'hide'),
        ('nf_upper', legs['nf'][0], 'hide'), ('nf_lower', legs['nf'][1], 'hide'),
        ('neck', T(F_n, NECK), 'hide'),
        ('bell', bell_poly, 'bell'),
        ('jaw', T(F_j, JAW), 'hide'),
        ('head', T(F_hd, HEAD), 'hide'),
        ('horn', T(F_hd, HORN), 'horn'),
        ('ear', T(F_e, EAR), 'hide'),
    ]
    hoofs = {n: legs[n][2] for n in LEGS}
    patches = {k: [T({'barrel': F_b, 'hip': F_h, 'shoulder': F_s, 'neck': F_n, 'head': F_hd}[k], q) for q in v]
               for k, v in PATCHES.items()}
    pins = [F_b(PIN['shoulder']), F_b(PIN['hip']), F_s(PIN['neck']), F_n(PIN['head']), F_hd(PIN['jaw']),
            joint['nf'][0], joint['nf'][1], joint['nh'][0], joint['nh'][1], F_h(PIN['tail'])]
    anchors = dict(
        muzzle=F_hd(NOSE), eye=F_hd(EYE), horn=F_hd(HORN_TIP), ear=F_e(EAR[len(EAR) // 2]), poll=F_n(PIN['head']),
        bell=F_bell((0, 12)), withers=F_s((52, -142)), back=F_b((0, -132)), hook=F_h((-40, -139)),
        rump=F_h((-93, -100)), seat=F_h((-80, -72)), belly=F_b((2, -56)), tail_tip=pts[3], tail_head=p0,
        hooves=dict(hoof), hand=hoof['nf'], hand_far=hoof['ff'], knee=joint['nf'][1], hock=joint['nh'][1],
        mouth=F_j((PIN['jaw'][0] + 36, PIN['jaw'][1] + 22)) if False else F_hd(_stand([(58, 8)], PIN['head'], HEAD_ANGLE)[0]),
    )
    return dict(parts=parts, hoofs=hoofs, patches=patches, pins=pins, anchors=anchors, eye=(F_hd(EYE), eye),
                clapper=(clap, _CLAPPER_L[2]), angles=ang, violations=bad,
                frames=dict(barrel=F_b, shoulder=F_s, hip=F_h, neck=F_n, head=F_hd))


def blend(p, q, x):
    """Pose between two poses (x 0 = p, 1 = q). Hooves planted in both stay planted; anything else turns on its pin."""
    x = clamp(x)
    out = {}
    sp = sq = None
    for k in set(p) | set(q):
        a, b = p.get(k, POSES['stand'].get(k)), q.get(k, POSES['stand'].get(k))
        if k in LEGS:
            if a[0] == b[0]:
                out[k] = (a[0], lerp(a[1], b[1], x), lerp(a[2], b[2], x))
            else:
                sp = sp or solve(p)['angles']
                sq = sq or solve(q)['angles']
                out[k] = ('fk', lerp(sp[k][0], sq[k][0], x), lerp(sp[k][1], sq[k][1], x))
        elif k == 'tail':
            out[k] = tuple(lerp(u, v, x) for u, v in zip(a, b))
        else:
            out[k] = lerp(a, b, x)
    return out


# ------------------------------------------------------------------ at the desk ---

DESK_Y = -110.0          # the desk top, cow units above the floor she is placed on
DESK_X = (28.0, 140.0)   # its near and far edge
STOOL_Y = -47.0          # the stool seat
STOOL_X = -52.0          # where her rump comes down on it


def _seated(pose):
    """Shift a pose so the lowest point of her rump rests on the stool."""
    hip = dict((n, poly) for n, poly, _ in solve(pose)['parts'])['hip']
    low = max(hip, key=lambda q: q[1])
    return with_(pose, dx=pose['dx'] + STOOL_X - low[0], dy=pose['dy'] + STOOL_Y - low[1])


# upright on a stool at a desk: both fore hooves on the desk top, hind legs stuck out under it, heels on the floor
POSES['sit'] = _seated(_pose(pitch=-58.0, hip=-10.0, shoulder=3.0, neck=34.0, head=42.0, ear=6.0, tail=(84.0, 62.0, 30.0),
                             nf=('ik', 46.0, DESK_Y), ff=('ik', 66.0, DESK_Y), nh=('ik', 8.0, -6.0), fh=('ik', 20.0, -6.0)))
# asleep on the desk: the whole front end goes down, the fore legs slide out across the top
POSES['desk_slump'] = _seated(_pose(pitch=-40.0, hip=-26.0, shoulder=10.0, neck=44.0, head=34.0, ear=-45.0, eye=0.0, jaw=3.0,
                                    tail=(70.0, 40.0, 10.0), nf=('ik', 96.0, DESK_Y), ff=('ik', 112.0, DESK_Y),
                                    nh=('ik', 10.0, -6.0), fh=('ik', 22.0, -6.0)))


def draw_pose(u, reach=0.0, press=1.0):
    """Seated and drawing. `u` 0..1 is where the pencil hoof is across the sheet (0 near her, 1 far); `press`
    1 = hoof down on the paper, 0 = lifted clear of it; `reach` 0..1 leans her whole front end into the far
    side of the sheet. The far hoof holds the sheet down, the head follows the pencil. The body stays on the
    stool: animate u for the stroke."""
    x = lerp(40.0, 74.0, clamp(u))
    y = DESK_Y - (1 - clamp(press)) * 12.0
    return _seated(with_(POSES['sit'], dx=0.0, dy=0.0, pitch=-58.0 + 9.0 * reach, nf=('ik', x + 8.0 * reach, y), ff=('ik', 70.0, DESK_Y),
                         neck=lerp(40.0, 28.0, u) + 4 * reach, head=lerp(46.0, 38.0, u), ear=12.0, eye=0.8,
                         shoulder=lerp(1.0, 7.0, u)))


def stamp_pose(u):
    """Seated, approving her own work. u 0 = hoof on the desk, 0.5 = hoof raised high over her head, 1 = slammed
    down (it comes down three times as fast as it went up)."""
    u = clamp(u)
    k = math.sin(math.pi * u) if u < 0.5 else math.cos(math.pi * (u - 0.5)) ** 3
    return _seated(with_(POSES['sit'], dx=0.0, dy=0.0, pitch=-58.0 - 7.0 * k, nf=('ik', lerp(52.0, 40.0, k), lerp(DESK_Y, -205.0, k)),
                         neck=lerp(34.0, 10.0, k), head=lerp(42.0, 24.0, k), shoulder=lerp(3.0, -6.0, k), ear=lerp(6.0, 30.0, k),
                         eye=lerp(1.0, 1.35, k)))


# ------------------------------------------------------------------ the walk ---

STRIDE = 96.0            # cow units travelled in one full cycle of four footfalls
DUTY = 0.64              # share of the cycle each hoof is on the ground
OFFSET = dict(nh=0.0, nf=0.25, fh=0.5, ff=0.75)        # lateral sequence: hind, fore of the same side, then the other side
_STAND_H = dict(f=95.0, h=104.0)                       # height of shoulder point / hip joint standing
_LOW = dict(f=88.4, h=100.6)                            # the same while two legs of the pair share the load
_HUMP = dict(f=6.0, h=3.8)                             # how far the body is carried up over a single stiff leg


def _vault(tau):
    """0 while both legs of a pair are down, then up and over the one that carries (tau in 0..0.5 of the cycle)."""
    lo = DUTY - 0.5
    return 0.0 if tau < lo else math.sin(math.pi * (tau - lo) / (0.5 - lo)) ** 2


def walk(dist, ground=None, lift=1.0, carry=0.0, stride=STRIDE):
    """The pose of the walking cow after `dist` cow units of travel.

    Each hoof is put down ahead of her and STAYS where it was put (in the same units as dist) while the body
    travels over it; the shoulders and the hips are carried up over each single supporting leg and sag when
    two share the load; the head, bell, udder and tail arrive late. `ground(xr)` (optional) gives the ground
    height in cow units at xr units ahead of her, relative to the ground under her middle, so the hooves and
    the body follow a hill. `lift` scales how high the hooves are picked up. `carry` (degrees) lowers the head:
    a tired cow walks with carry=25. Use walk_on() to do all of this in pixels."""
    ph = dist / stride
    gr = ground or (lambda xr: 0.0)
    p = _pose()
    sd = _STAND_H['f'] - (_LOW['f'] + _HUMP['f'] * _vault((ph - OFFSET['nf']) % 0.5))
    hd = _STAND_H['h'] - (_LOW['h'] + _HUMP['h'] * _vault((ph - OFFSET['nh']) % 0.5))
    gf, gh = gr(PIN['fore'][0]), gr(PIN['hind'][0])
    span = PIN['fore'][0] - PIN['hind'][0]
    slope = math.atan2(gf - gh, span)
    th = (sd - hd) / span + slope
    p['pitch'] = math.degrees(th)
    p['dy'] = sd - PIN['fore'][0] * math.tan((sd - hd) / span) + (gf * -PIN['hind'][0] + gh * PIN['fore'][0]) / span
    for name in LEGS:
        fore = name[1] == 'f'
        u = (ph - OFFSET[name]) % 1.0
        n = math.floor(ph - OFFSET[name])
        rest = STANCE[name] if fore else STANCE[name]
        rest = (PIN['fore'][0] + (2 if name[0] == 'n' else FAR_DX + 2)) if fore else (PIN['hind'][0] - (4 if name[0] == 'n' else -FAR_DX + 4))
        down = (n + OFFSET[name]) * stride + rest + stride * DUTY / 2          # where this hoof was put down
        if u < DUTY:
            xw, hgt = down, 0.0
        else:
            w = (u - DUTY) / (1 - DUTY)
            e = w * w * (3 - 2 * w)
            xw = down + stride * (0.12 * w + 0.88 * e)                           # leaves late, reaches, is set down
            hgt = lift * (17.0 if fore else 13.0) * math.sin(math.pi * w ** 0.75) ** 1.3
        xr = xw - dist
        p[name] = ('ik', xr, gr(xr) - hgt)
    # the shoulder blade rides up over the loaded near fore leg; the hook bone over the loaded near hind leg
    load = lambda leg: math.sin(math.pi * clamp(((ph - OFFSET[leg]) % 1.0) / DUTY)) if ((ph - OFFSET[leg]) % 1.0) < DUTY else 0.0
    p['shoulder'] = -3.2 * load('nf') + 2.0 * load('ff')
    p['hip'] = 2.6 * load('nh') - 1.6 * load('fh')
    lag = 2 * math.pi * 2 * (ph - OFFSET['nf'] - 0.11)             # late: the head is heavy
    p['neck'] = 6.0 + carry - 4.2 * math.cos(lag)
    p['head'] = 2.0 + carry * 0.35 + 2.4 * math.cos(lag - 0.9)
    p['bell'] = 15.0 * math.sin(lag - 1.3)
    p['udder'] = 7.0 * math.sin(2 * math.pi * (ph - 0.1))
    p['ear'] = -4.0 + 3.0 * math.cos(lag - 1.6)
    sw = math.sin(2 * math.pi * (ph - 0.2))
    p['tail'] = (5.0 + 5.0 * sw, 8.0 + 11.0 * math.sin(2 * math.pi * (ph - 0.36)), 10.0 + 20.0 * math.sin(2 * math.pi * (ph - 0.52)))
    return p


# ------------------------------------------------------------------ drawing ---

TONES = dict(
    paper=dict(hide=(236, 226, 204), far=(203, 190, 166), patch=(74, 56, 46), horn=(214, 196, 150), udder=(226, 172, 160),
               bell=BRASS, hoof=(52, 44, 40), edge=(60, 48, 40), pin=(176, 138, 62), eye=(30, 24, 22)),
)


def _screen(pts, x, y, s, facing, tilt):
    if tilt:
        c, sn = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        pts = [(q[0] * c - q[1] * sn, q[0] * sn + q[1] * c) for q in pts]
    return [(x + facing * s * q[0], y + s * q[1]) for q in pts]


def parts(pose, x=0.0, y=0.0, s=1.0, facing=1, tilt=0.0):
    """The cut pieces in screen pixels, back to front: [(name, [(x, y), ...]), ...]. For drawing her yourself
    (a boiling pencil line, a morph): the polygons are closed and each keeps the same point count in every pose."""
    return [(n, _screen(poly, x, y, s, facing, tilt)) for n, poly, _ in solve(pose)['parts']]


def anchors(pose, x=0.0, y=0.0, s=1.0, facing=1, tilt=0.0):
    """Where things are, in screen pixels, without drawing: see place() for the keys."""
    sol = solve(pose)
    a = {k: (_screen([v], x, y, s, facing, tilt)[0] if k != 'hooves' else
             {n: _screen([q], x, y, s, facing, tilt)[0] for n, q in v.items()}) for k, v in sol['anchors'].items()}
    a['violations'] = sol['violations']
    return a


def sprite(pose, s=1.0, facing=1, style='shadow', tilt=0.0, color=None, paper=PAPER, line=INK, width=2.2,
           pins=False, far=None):
    """The cow as an RGBA cutout. Returns (image, (ax, ay)): paste it with its top-left at (x - ax, y - ay) to
    stand her ground point on (x, y)."""
    sol = solve(pose)
    S = s * SS
    P = lambda poly: _screen(poly, 0.0, 0.0, S, facing, tilt)
    polys = [(n, P(poly), tone) for n, poly, tone in sol['parts']]
    xs = [q[0] for _, poly, _ in polys for q in poly]
    ys = [q[1] for _, poly, _ in polys for q in poly]
    pad = 6 * SS
    x0, y0 = math.floor(min(xs)) - pad, math.floor(min(ys)) - pad
    wd, ht = int(max(xs) - x0) + pad, int(max(ys) - y0) + pad
    wd, ht = wd + (-wd) % SS, ht + (-ht) % SS
    O = lambda poly: [(q[0] - x0, q[1] - y0) for q in poly]
    eye_c, eye_open = sol['eye']
    ex, ey = O(P([eye_c]))[0]
    er = 3.3 * S
    clap_c, clap_r = sol['clapper']
    bx, by = O(P([clap_c]))[0]

    if style == 'shadow':
        col = tuple(color or BLACK)
        m = Image.new('L', (wd, ht), 0)
        d = ImageDraw.Draw(m)
        far_m = None
        if far is not None:                                   # far legs a breath lighter: they are off the glass
            far_m = Image.new('L', (wd, ht), 0)
            fd = ImageDraw.Draw(far_m)
        for n, poly, tone in polys:
            d.polygon(O(poly), fill=255)
            if far_m is not None and tone == 'far':
                fd.polygon(O(poly), fill=255)
            elif far_m is not None:
                fd.polygon(O(poly), fill=0)
        d.ellipse([bx - clap_r * S, by - clap_r * S, bx + clap_r * S, by + clap_r * S], fill=255)
        if eye_open > 0.05:                                   # the eye is a hole cut in the card
            ry = er * min(eye_open, 1.0) * (1.0 if eye_open <= 1 else 1.0)
            rx = er * (1.0 if eye_open <= 1 else eye_open ** 0.6)
            ry = ry if eye_open <= 1 else er * eye_open ** 0.6
            d.ellipse([ex - rx, ey - ry, ex + rx, ey + ry], fill=0)
        if pins:
            for q in O(P(sol['pins'])):
                d.ellipse([q[0] - 1.1 * S, q[1] - 1.1 * S, q[0] + 1.1 * S, q[1] + 1.1 * S], fill=0)
        img = Image.new('RGBA', (wd, ht), col + (0,))
        if far_m is not None:
            a = ImageChops.subtract(m, far_m.point(lambda v: int(v * (1 - far))))
            img.putalpha(a)
        else:
            img.putalpha(m)
    else:
        img = Image.new('RGBA', (wd, ht), (0, 0, 0, 0))
        if style == 'paper':
            tn = dict(TONES['paper'])
            if color:
                tn['hide'] = tuple(color)
            off = (1.6 * S * 0.9, 2.4 * S * 0.9)
            for n, poly, tone in polys:
                pp = O(poly)
                sh = Image.new('L', (wd, ht), 0)
                ImageDraw.Draw(sh).polygon([(q[0] + off[0], q[1] + off[1]) for q in pp], fill=70)
                img = Image.composite(Image.new('RGBA', (wd, ht), (30, 20, 12, 255)), img, ImageChops.multiply(
                    sh, ImageChops.invert(Image.new('L', (wd, ht), 0)))) if False else _under(img, sh)
                pm = Image.new('L', (wd, ht), 0)
                ImageDraw.Draw(pm).polygon(pp, fill=255)
                img.paste(tn[tone] + (255,), (0, 0), pm)
                key = n if n in sol['patches'] else None
                if key:
                    qm = Image.new('L', (wd, ht), 0)
                    qd = ImageDraw.Draw(qm)
                    for patch in sol['patches'][key]:
                        qd.polygon(O(P(patch)), fill=255)
                    img.paste(tn['patch'] + (255,), (0, 0), ImageChops.multiply(qm, pm))
                if n.endswith('_lower'):
                    hm = Image.new('L', (wd, ht), 0)
                    ImageDraw.Draw(hm).polygon(O(P(sol['hoofs'][n[:2]])), fill=255)
                    img.paste(tn['hoof'] + (255,), (0, 0), ImageChops.multiply(hm, pm))
                if n == 'tail':                                   # the switch is dark
                    k = len(pp) // 2
                    tm = Image.new('L', (wd, ht), 0)
                    j = int(k * 0.66)
                    ImageDraw.Draw(tm).polygon(pp[j:len(pp) - j], fill=255)
                    img.paste(tn['patch'] + (255,), (0, 0), tm)
                ImageDraw.Draw(img).line(pp + [pp[0]], fill=tn['edge'] + (120,), width=max(1, int(0.5 * SS)))
            d = ImageDraw.Draw(img)
            d.ellipse([bx - clap_r * S, by - clap_r * S, bx + clap_r * S, by + clap_r * S], fill=tn['edge'] + (255,))
            if pins:
                for q in O(P(sol['pins'])):
                    d.ellipse([q[0] - 1.5 * S, q[1] - 1.5 * S, q[0] + 1.5 * S, q[1] + 1.5 * S], fill=tn['pin'] + (255,),
                              outline=tn['edge'] + (255,))
            _eye(d, ex, ey, er, eye_open, tn['eye'], (250, 246, 236), S)
        elif style == 'line':
            lw = max(1, int(round(width * SS)))
            d = ImageDraw.Draw(img)
            for n, poly, tone in polys:
                pp = O(poly)
                d.polygon(pp, fill=tuple(paper) + (255,))
                d.line(pp + [pp[0]], fill=tuple(line) + (255,), width=lw, joint='curve')
                if n.endswith('_lower'):
                    d.polygon(O(P(sol['hoofs'][n[:2]])), fill=tuple(line) + (255,))
                if n == 'bell':
                    d.polygon(pp, fill=tuple(color or BRASS) + (255,))
                    d.line(pp + [pp[0]], fill=tuple(line) + (255,), width=lw, joint='curve')
            d.ellipse([bx - clap_r * S, by - clap_r * S, bx + clap_r * S, by + clap_r * S], fill=tuple(line) + (255,))
            _eye(d, ex, ey, er * 0.9, eye_open, line, paper, S)
        else:
            raise ValueError(style)
    img = img.resize((wd // SS, ht // SS), Image.LANCZOS)
    return img, (-x0 / SS, -y0 / SS)


def _under(img, shadow_mask):
    sh = Image.new('RGBA', img.size, (40, 26, 14, 0))
    sh.putalpha(shadow_mask)
    return Image.alpha_composite(img, sh)


def _eye(d, ex, ey, er, opn, dark, white, S):
    if opn <= 0.05:
        d.arc([ex - er, ey - er * 0.6, ex + er, ey + er], 10, 170, fill=tuple(dark) + (255,), width=max(1, int(0.9 * S)))
        return
    k = opn ** 0.6 if opn > 1 else 1.0
    rx, ry = er * k, er * k * min(opn, 1.0)
    if opn > 1.15:                                             # startled: the white shows all round
        d.ellipse([ex - rx * 1.25, ey - ry * 1.25, ex + rx * 1.25, ey + ry * 1.25], fill=tuple(white) + (255,),
                  outline=tuple(dark) + (255,), width=max(1, int(0.5 * S)))
        rx, ry = er * 0.6, er * 0.6
    d.ellipse([ex - rx, ey - ry, ex + rx, ey + ry], fill=tuple(dark) + (255,))


def place(ink, pose, x, y, s=1.0, facing=1, style='shadow', tilt=0.0, alpha=1.0, **opts):
    """Draw the cow with the ground under the middle of her barrel at (x, y). `ink` is the kit's Ink or a PIL image.

    facing=1 looks right, -1 left. tilt (degrees, + = nose down as drawn facing right) leans the whole puppet.
    opts go to sprite(): color=, paper=, line=, width=, pins=True, far=0.15.
    Returns the anchors in screen pixels: muzzle, mouth, eye, horn, ear, poll, bell, withers, back, hook, rump,
    seat, belly, tail_tip, tail_head, hand (near fore hoof), hand_far, knee, hock, hooves {nf, ff, nh, fh},
    violations (joint limits that had to be clamped: should be [])."""
    img, (ax, ay) = sprite(pose, s, facing, style, tilt, **opts)
    xy = (int(round(x - ax)), int(round(y - ay)))
    if alpha < 1:
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    if hasattr(ink, 'paste') and hasattr(ink, 'd'):
        ink.paste(img, xy)
    else:
        ink.paste(img, xy, img)
    fx, fy = x - ax - xy[0], y - ay - xy[1]                     # the rounding, so anchors match the pixels
    return anchors(pose, x - fx, y - fy, s, facing, tilt)


def walk_on(ink, x, ground, s=1.0, facing=1, style='shadow', lift=1.0, carry=0.0, phase=0.0, over=None, **opts):
    """Walk her along a ground line. `x` is where her middle is now (px); `ground` is a function px -> px (or a
    number for flat ground). Her phase comes from x itself, so every hoof that is down stays on the same pixel
    of ground until it is picked up: move x, and she walks. Speed is yours: one cycle is STRIDE * s pixels
    (96 px at s=1); a plodding cow takes about 1.4 s over it. `phase` (0..1) offsets her from another cow.
    `over` replaces pose keys after the walk is solved (e.g. over=dict(neck=-20, ear=30) to look up as she goes).
    Returns the anchors."""
    g = (lambda px: float(ground)) if not callable(ground) else ground
    y0 = g(x)
    rel = lambda xr: (g(x + facing * xr * s) - y0) / s
    pose = walk(facing * x / s + phase * STRIDE, ground=rel, lift=lift, carry=carry)
    if over:
        pose.update(over)
    return place(ink, pose, x, y0, s, facing, style, **opts)


def outline(pose, s=1.0, facing=1, n=240, tilt=0.0):
    """Her whole silhouette as ONE closed line: n points (px, relative to her ground point), evenly spaced along
    the contour, starting at the tip of the muzzle and running over the head and back first. For the drawn
    acts: draw it as a pencil line, or pair it point for point with another n-point contour and interpolate."""
    img, (ax, ay) = sprite(with_(pose, eye=0.0), s * 3, facing, 'shadow', tilt)
    a = img.getchannel('A').point(lambda v: 255 if v > 127 else 0)
    wd, ht = a.size
    px = a.load()
    inside = lambda x, y: 0 <= x < wd and 0 <= y < ht and px[x, y] > 0
    start = None
    for yy in range(ht):
        for xx in range(wd):
            if px[xx, yy]:
                start = (xx, yy)
                break
        if start:
            break
    # Moore neighbour tracing, clockwise
    nb = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
    pts, cur, back = [start], start, 0
    for _ in range(wd * ht):
        for k in range(8):
            j = (back + k) % 8
            q = (cur[0] + nb[j][0], cur[1] + nb[j][1])
            if inside(*q):
                back = (j + 5) % 8
                cur = q
                break
        else:
            break
        if cur == start:
            break
        pts.append(cur)
    pts = [((q[0] - ax) / 3, (q[1] - ay) / 3) for q in pts]
    mz = anchors(pose, 0, 0, s, facing, tilt)['muzzle']
    i0 = min(range(len(pts)), key=lambda i: (pts[i][0] - mz[0]) ** 2 + (pts[i][1] - mz[1]) ** 2)
    pts = pts[i0:] + pts[:i0]
    if facing * (pts[min(12, len(pts) - 1)][1] - pts[0][1]) > 0 and False:
        pts = pts[::-1]
    # make the direction the same whichever way she faces: over the forehead first
    k = min(len(pts) // 20 + 1, len(pts) - 1)
    if pts[k][1] > pts[-k][1]:
        pts = [pts[0]] + pts[:0:-1]
    # light smoothing, then even spacing
    m = len(pts)
    for _ in range(6):
        pts = [((pts[i - 1][0] + 2 * pts[i][0] + pts[(i + 1) % m][0]) / 4, (pts[i - 1][1] + 2 * pts[i][1] + pts[(i + 1) % m][1]) / 4)
               for i in range(m)]
    seg = [math.hypot(pts[(i + 1) % m][0] - pts[i][0], pts[(i + 1) % m][1] - pts[i][1]) for i in range(m)]
    total = sum(seg)
    out, i, acc = [], 0, 0.0
    for k in range(n):
        target = total * k / n
        while acc + seg[i] < target and i < m - 1:
            acc += seg[i]
            i += 1
        f = (target - acc) / (seg[i] or 1.0)
        a_, b_ = pts[i], pts[(i + 1) % m]
        out.append((a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f))
    return out


def stool_and_desk(ink, x, y, s=1.0, facing=1, style='shadow', color=None, line=INK, paper=PAPER, width=2.2):
    """The stool she sits on and the desk she draws at, for the cow placed at the same (x, y, s, facing) in a
    'sit' pose. Returns {'top': (x0, x1, y) of the desk top, 'sheet': (cx, y) where the paper lies}."""
    X = lambda u: x + facing * s * u
    Y = lambda v: y + s * v
    im = ink.img if hasattr(ink, 'img') else ink
    d = ImageDraw.Draw(im, 'RGBA')
    col = tuple(color or (BLACK if style == 'shadow' else line))
    lw = max(1, int(round(width)))

    def box(x0, y0, x1, y1):
        pts = [(X(x0), Y(y0)), (X(x1), Y(y0)), (X(x1), Y(y1)), (X(x0), Y(y1))]
        if style == 'shadow':
            d.polygon(pts, fill=col + (255,))
        else:
            d.polygon(pts, fill=tuple(paper) + (255,) if style == 'line' else (150, 110, 70, 255))
            d.line(pts + [pts[0]], fill=col + (255,), width=lw, joint='curve')
    box(STOOL_X - 24, STOOL_Y, STOOL_X + 24, STOOL_Y + 7)          # stool seat
    box(STOOL_X - 20, STOOL_Y + 7, STOOL_X - 15, 0)
    box(STOOL_X + 15, STOOL_Y + 7, STOOL_X + 20, 0)
    box(STOOL_X - 15, -20, STOOL_X + 15, -16)
    box(DESK_X[0], DESK_Y, DESK_X[1], DESK_Y + 7)                    # desk top
    box(DESK_X[1] - 14, DESK_Y + 7, DESK_X[1] - 7, 0)
    if hasattr(ink, 'd'):
        ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    return dict(top=(X(DESK_X[0]), X(DESK_X[1]), Y(DESK_Y)), sheet=(X(84), Y(DESK_Y)))


# ------------------------------------------------------------------ checks ---


def check(verbose=True, strict=True):
    """MEASURED checks, the ones the representation supports. Returns a dict; raises if a hard one fails.

    contact drift: over two walk cycles in 1/96-cycle steps, how far each planted hoof moves from where it was
      put down (px at s=1, world space). The walk plants hooves by construction; this proves the legs reach.
    joint limits: no pose in POSES, draw_pose, stamp_pose or the walk needs a clamp.
    attachment: every limb's pin is inside the piece it hangs from (no detached limbs), all poses.
    bob: the vertical travel of withers and hook bone over a cycle (the weight you should see)."""
    drift = 0.0
    viol = []
    planted = {}
    wy, hy, heads = [], [], []
    for k in range(0, 193):
        dist = STRIDE * k / 96.0
        ph = dist / STRIDE
        pose = walk(dist)
        sol = solve(pose)
        viol += [('walk %.3f' % ph,) + v for v in sol['violations']]
        for name in LEGS:
            u = (ph - OFFSET[name]) % 1.0
            hx, hy_ = sol['anchors']['hooves'][name]
            if u < DUTY - 1e-9:
                key = (name, math.floor(ph - OFFSET[name] + 1e-9))
                wx = hx + dist
                if key in planted:
                    drift = max(drift, abs(wx - planted[key][0]), abs(hy_ - planted[key][1]))
                else:
                    planted[key] = (wx, hy_)
                drift = max(drift, abs(hy_))
        wy.append(sol['anchors']['withers'][1])
        hy.append(sol['anchors']['hook'][1])
        heads.append(sol['anchors']['muzzle'][1])
    named = dict(POSES)
    named.update({'draw_%.1f' % u: draw_pose(u, r) for u in (0, 0.5, 1) for r in (0, 1)})
    named.update({'stamp_%.2f' % u: stamp_pose(u) for u in (0, 0.25, 0.5, 0.75, 1)})
    for nm, p in named.items():
        viol += [(nm,) + v for v in solve(p)['violations']]
    res = dict(contact_drift_px=round(drift, 4), limit_violations=viol,
               withers_bob=round(max(wy) - min(wy), 2), hook_bob=round(max(hy) - min(hy), 2),
               muzzle_bob=round(max(heads) - min(heads), 2), poses=len(named))
    if verbose:
        for k, v in res.items():
            print('  %-18s %s' % (k, v))
    assert drift < 0.05, 'a planted hoof slid'
    if strict:
        assert not viol, 'joint limits broken: %r' % viol[:4]
    return res


# ------------------------------------------------------------------ sheets ---


def _backlight(size=(W, H)):
    """The lit paper screen of the shadow theatre: warm, brightest behind the middle."""
    w, h = size
    im = Image.new('RGB', size)
    d = ImageDraw.Draw(im)
    for yy in range(h):
        u = yy / h
        d.line((0, yy, w, yy), fill=(int(lerp(246, 226, u)), int(lerp(222, 170, u)), int(lerp(170, 104, u))))
    g = Image.new('L', size, 0)
    ImageDraw.Draw(g).ellipse((w * 0.25, h * 0.05, w * 0.75, h * 0.85), fill=130)
    im.paste(Image.new('RGB', size, (255, 244, 212)), (0, 0), g.filter(ImageFilter.GaussianBlur(w // 9)))
    return im


def _sheets():
    out = FILMS / 'stills' / 'cowpath_cast'
    out.mkdir(parents=True, exist_ok=True)

    # 1. pose sheet, shadow
    im = _backlight((1920, 1080))
    d = ImageDraw.Draw(im)
    cells = [('stand', POSES['stand'], False), ('graze', POSES['graze'], False), ('look_up', POSES['look_up'], False),
             ('startle', POSES['startle'], False), ('slump', POSES['slump'], False), ('sit', POSES['sit'], True),
             ('draw_pose(0.1)', draw_pose(0.1), True), ('draw_pose(1, 1)', draw_pose(1.0, 1.0), True),
             ('stamp_pose(0.5)', stamp_pose(0.5), True), ('desk_slump', POSES['desk_slump'], True)]
    for i, (nm, p, desk) in enumerate(cells):
        cx, gy = 200 + (i % 5) * 380, 440 + (i // 5) * 520
        d.line((cx - 180, gy, cx + 180, gy), fill=BLACK, width=3)
        if desk:
            stool_and_desk(im, cx - 30, gy, 1.25)
            a = place(im, p, cx - 30, gy, 1.25)
        else:
            a = place(im, p, cx - 20, gy, 1.25)
        if a['violations']:
            print('  !!', nm, a['violations'])
        d = ImageDraw.Draw(im)
        d.text((cx - 170, gy + 14), nm, fill=BLACK)
    im.save(out / 'pose_sheet.png')

    # 2. walk strip: 12 frames of one cycle, the ground marked where each hoof was put down
    im = _backlight((1920, 1080))
    d = ImageDraw.Draw(im)
    s = 1.05
    for k in range(12):
        cx, gy = 170 + (k % 6) * 310, 430 + (k // 6) * 500
        d.line((cx - 150, gy, cx + 150, gy), fill=BLACK, width=3)
        pose = walk(STRIDE * k / 12.0)
        a = place(im, pose, cx - 6, gy, s)
        d = ImageDraw.Draw(im)
        for name in LEGS:
            u = (k / 12.0 - OFFSET[name]) % 1.0
            hx, hy = a['hooves'][name]
            if u < DUTY:
                d.polygon([(hx, gy + 8), (hx - 6, gy + 20), (hx + 6, gy + 20)], fill=(150, 40, 30))
        d.text((cx - 140, gy + 26), 'frame %d  phase %.3f' % (k + 1, k / 12.0), fill=BLACK)
        d.line((cx - 150, gy - 141 * s, cx + 150, gy - 141 * s), fill=(150, 40, 30), width=1)     # standing withers
    im.save(out / 'walk_strip.png')

    # 3. the walk in place: onion skin of the cycle in world space, hooves must pile on single points
    im = _backlight((1920, 540))
    g = lambda px: 430 + 26 * math.sin(px / 210.0)
    d = ImageDraw.Draw(im)
    d.line([(xx, g(xx)) for xx in range(0, 1921, 8)], fill=BLACK, width=3)
    for k in range(0, 34):
        x = 150 + k * 48
        walk_on(im, x, g, s=1.0, alpha=1.0 if k % 6 == 0 else 0.16)
    im.save(out / 'walk_world.png')

    # 4. the three materials, and a small one
    im = Image.new('RGB', (1920, 1080), PAPER)
    bl = _backlight((640, 540))
    im.paste(bl, (0, 0))
    river = Image.new('RGB', (640, 540), (86, 128, 122))
    im.paste(river, (1280, 0))
    for i, (style, opts) in enumerate((('shadow', {}), ('line', {}), ('paper', dict(pins=True)))):
        place(im, POSES['look_up'], 300 + i * 640, 420, 1.5, style=style, **opts)
        place(im, POSES['graze'], 180 + i * 640, 520, 0.5, style=style, facing=-1, **opts)
        place(im, walk(30), 480 + i * 640, 520, 0.5, style=style, **opts)
    stool_and_desk(im, 300, 1000, 1.5, style='line')
    place(im, draw_pose(0.6, 0.4), 300, 1000, 1.5, style='line')
    stool_and_desk(im, 940, 1000, 1.5, style='paper')
    place(im, POSES['desk_slump'], 940, 1000, 1.5, style='paper', pins=True)
    pts = outline(POSES['stand'], 1.5, n=240)
    d = ImageDraw.Draw(im)
    pp = [(1560 + q[0], 1000 + q[1]) for q in pts]
    d.line(pp + [pp[0]], fill=INK, width=3)
    for q in pp[::8]:
        d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=(150, 40, 30))
    d.ellipse([pp[0][0] - 8, pp[0][1] - 8, pp[0][0] + 8, pp[0][1] + 8], outline=(150, 40, 30), width=3)
    im.save(out / 'materials.png')
    print('sheets ->', out)


if __name__ == '__main__':
    print('checks (MEASURED):')
    check(strict=False)
    _sheets()
    check(verbose=False)
