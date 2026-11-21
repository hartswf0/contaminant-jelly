"""cast.py: the cow of "Don't Pave the Cow Paths". One puppet, three materials, three animals.

She is a cut figure on pins (barrel, shoulder, hip, udder, neck, head, jaw, ear, two horns, bell, tail,
four two-part legs), posed by joint angles with limits, and walked by planting her hooves on the ground and
carrying the body over them. The same pieces draw as

    style='shadow'   black card against a backlight                    (ACT 1)
    style='line'     graphite contour on paper, hidden lines removed   (ACT 2)
    style='paper'    cream and brown cut paper with brass brads        (ACT 3)

and are cut in three kinds:

    kind='lead'      THE cow: her LEFT HORN IS CROOKED (crumpled forward over the brow, the other stands up)
                     and A BELL hangs under her neck
    kind='herd'      a plain herd cow: two matching horns, no bell
    kind='calf'      a calf: short body, long legs, no horns, no bell, no udder (drawn at 0.56 of a cow)

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))      # films/swarm/cowpath
    import cast
    a = cast.place(ink, cast.POSES['graze'], 300, 430, s=0.8, style='shadow')
    a = cast.walk_on(ink, x, ground, s=0.8, style='shadow')        # ground: px -> px, hooves stay planted

Everything is documented in CAST.md. `python3 films/swarm/cowpath/cast.py` writes the pose sheet, the walk
strip, the material sheet and prints the measured checks (films/stills/cowpath_cast/).

Units. The puppet is built in "cow units": x forward (the way she faces), y down, origin on the ground under
the middle of her barrel. Standing she is 141 units at the withers and about 250 from nose to tail. `s` is
pixels per unit. Angles are degrees. For every joint, POSITIVE LOWERS THE NOSE END: pitch+ tips the body nose
down, neck+ lowers the head, head+ tucks the muzzle, shoulder+ / hip+ rock that piece the same way. Leg
angles are measured from "straight down from the body", POSITIVE = HOOF FORWARD.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
if str(FILMS) not in sys.path:
    sys.path.insert(0, str(FILMS))
from kit import PAPER, INK, BRASS, W, H, clamp, lerp  # noqa: E402

BLACK = (20, 16, 14)            # the card of the shadow theatre
GRAPHITE = (58, 56, 60)         # the pencil of act 2
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
# The master pattern, in standing cow units unless a comment says "local". A kind is this pattern re-cut.

_CY = -98.0                             # the body pitches about (0, _CY); kinds are scaled about it too
_PIN = dict(
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
L_FORE = (56.0, 40.0)                   # shoulder to knee, knee to sole
L_HIND = (60.0, 50.0)                   # hip to hock, hock to sole

_BARREL = [(-54, -131), (-28, -133), (0, -131.5), (28, -133), (52, -131), (62, -112), (60, -88), (50, -70),
           (28, -61), (2, -56), (-24, -58), (-46, -67), (-58, -86), (-62, -110)]
_SHOULDER = [(26, -132), (40, -139), (52, -142), (64, -138), (76, -126), (86, -108), (88, -90), (82, -74),
             (70, -64), (56, -62), (42, -68), (32, -82), (26, -104)]
_HIP = [(-26, -132), (-40, -139.5), (-52, -137), (-70, -132), (-88, -127), (-94, -112), (-93, -94), (-85, -78),
        (-70, -66), (-54, -64), (-38, -70), (-28, -84), (-24, -108)]
_UDDER = [(-27, -68), (-29, -57), (-35, -51), (-38.5, -43), (-42, -50), (-47, -49), (-50.5, -42), (-54, -50),
          (-59, -57), (-61, -68)]
_NECK_L = [(-14, -20), (8, -22), (30, -18), (48, -15), (58, -6), (57, 10), (44, 17), (26, 23), (8, 31), (-8, 35),
           (-20, 25), (-23, 0)]
_BELL_ON_NECK = (40.0, 17.0)            # neck-local: where the strap leaves the throat

# head, local: pin at the poll end of the skull, x along the face to the muzzle
_HEAD_L = [(-10, -8), (-2, -17), (12, -18), (27, -13.5), (42, -9.5), (54, -10), (63, -6.5), (66.5, 2), (62, 8.5),
           (44, 6.5), (26, 8), (13, 17), (-1, 15), (-10, 5)]
_JAW_L = [(4, 3), (22, 5), (42, 4.5), (58, 6.5), (62, 12), (57, 17.5), (40, 16.5), (23, 19), (9, 17.5), (1, 10)]
_HORN_L = [(-5, -13), (-9, -25), (-5, -36), (6, -43), (3, -35), (0, -27), (5, -15)]            # the good horn
_CRUMP_L = [(2, -15), (7, -27), (19, -31), (32, -25), (36, -14), (31, -19), (22, -23), (14, -21), (12, -14)]  # crooked
_EAR_L = [(0, -4.5), (10, -9), (22, -5), (27, 0), (18, 6.5), (5, 5.5)]                          # local to its own pin
_EYE_L = (15.0, -6.0)
_NOSE_L = (63.0, 2.0)
_JAW_PIN_L = (8.0, 9.0)
_EAR_PIN_L = (-6.0, -6.0)
EAR_ANGLE = 162.0                       # the ear's direction in head-local degrees (points back, a little up)

# bell, local: hangs down from (0, 0)
_BELL_L = [(-3.4, -8), (3.4, -8), (4, 3), (9, 7), (11.5, 20), (13.5, 26), (-13.5, 26), (-11.5, 20), (-9, 7), (-4, 3)]
_CLAPPER_L = (0.0, 28.0, 3.6)

# legs, local: pin at (0, 0), the limb hangs down +y, +x is the front of the limb
_FORE_UP = [(-15, -8), (-6, -17), (8, -16), (17, -4), (15, 16), (10.5, 34), (8.5, 49), (9, 57), (3, 62),
            (-6, 60), (-7, 48), (-9, 32), (-14, 14)]
_HIND_UP = [(-14, -12), (4, -18), (20, -8), (25, 10), (21, 28), (12.5, 42), (7.5, 53), (7, 61), (1, 66),
            (-9.5, 64), (-8, 52), (-10, 36), (-16, 14)]


def _lower(length):
    k = length - 40.0
    return _smooth([(-6.5, -5), (0, -7), (6.5, -5), (5, 8 + k / 5), (4.6, 20 + k * 0.8), (6, 27 + k), (8.5, 30.5 + k)],
                   n=4, closed=False) + \
        [(9.5, 32 + k), (13, 40 + k), (-7, 40 + k), (-7, 33.5 + k), (-9.5, 29.5 + k), (-6, 26 + k)] + \
        _smooth([(-6, 26 + k), (-4.6, 14 + k / 2), (-6.5, -5)], n=4, closed=False)[1:-1]


def _hoof(length):
    k = length - 40.0
    return [(8.2, 30.5 + k), (9.5, 32 + k), (13, 40 + k), (-7, 40 + k), (-7, 33.5 + k), (-5.5, 31 + k)]


# brown patches for the paper animals, by piece (master units; clipped to the piece when drawn)
_PATCH = dict(
    lead=dict(
        barrel=[[(-30, -140), (-4, -136), (10, -118), (4, -96), (-14, -84), (-34, -92), (-40, -116)]],
        hip=[[(-66, -140), (-100, -132), (-100, -100), (-80, -96), (-68, -110)]],
        shoulder=[[(60, -146), (92, -128), (96, -100), (78, -96), (66, -112), (52, -124)]],
        neck=[[(84, -140), (120, -146), (126, -126), (104, -116), (86, -122)]]),
    herd=dict(
        barrel=[[(10, -140), (48, -138), (66, -112), (50, -84), (24, -78), (6, -96), (0, -120)]],
        hip=[[(-50, -100), (-30, -90), (-34, -62), (-60, -60), (-74, -76)]],
        shoulder=[[(26, -140), (60, -146), (74, -116), (56, -90), (30, -96)]],
        neck=[]),
    calf=dict(
        barrel=[[(-40, -140), (-8, -138), (0, -112), (-16, -92), (-44, -98)]],
        hip=[[(-66, -140), (-100, -132), (-100, -112), (-78, -110)]],
        shoulder=[], neck=[[(84, -140), (120, -146), (126, -126), (104, -116), (86, -122)]]),
)
_HEAD_PATCH_L = dict(lead=[(-12, -20), (16, -20), (24, -6), (14, 4), (-2, 2), (-12, -6)],
                     herd=[(30, -16), (70, -12), (70, 12), (36, 10)],
                     calf=[(-12, -20), (10, -20), (14, -8), (4, 0), (-12, -4)])

KINDS = dict(
    lead=dict(kx=1.0, ky=1.0, neck=1.0, head=1.0, limb=1.0, horns='crooked', bell=True, udder=True, tail=1.0, size=1.0),
    herd=dict(kx=1.03, ky=1.04, neck=0.96, head=0.97, limb=1.0, horns='pair', bell=False, udder=True, tail=1.0, size=0.97),
    calf=dict(kx=0.66, ky=0.62, neck=0.78, head=0.84, limb=0.74, horns='none', bell=False, udder=False, tail=0.62, size=0.56),
)


class Rig:
    """One kind's cut pieces. Rig.of('lead') is cached."""
    _cache = {}

    @classmethod
    def of(cls, kind):
        if isinstance(kind, Rig):
            return kind
        if kind not in cls._cache:
            cls._cache[kind] = cls(kind)
        return cls._cache[kind]

    def __init__(self, kind):
        K = KINDS[kind]
        self.kind, self.K = kind, K
        kx, ky, hs, ns, lw = K['kx'], K['ky'], K['head'], K['neck'], K['limb']
        self.kx, self.size = kx, K['size']
        M = self.M = lambda p: (kx * p[0], _CY + ky * (p[1] - _CY))
        Ms = lambda pts: [M(p) for p in pts]
        self.C = (0.0, _CY)
        P = self.PIN = {k: M(v) for k, v in _PIN.items()}
        P['head'] = (P['neck'][0] + NECK_LEN * ns * math.cos(math.radians(NECK_ANGLE)),
                     P['neck'][1] + NECK_LEN * ns * math.sin(math.radians(NECK_ANGLE)))
        self.BARREL = _smooth(Ms(_BARREL))
        self.SHOULDER = _smooth(Ms(_SHOULDER))
        self.HIP = _smooth(Ms(_HIP), n=4)
        self.UDDER = _smooth(Ms(_UDDER), n=4)
        nl = [(q[0] * ns, q[1] * (ns if ky == 1.0 else 0.5 * (ns + ky))) for q in _NECK_L]
        self.NECK = _smooth(_stand(nl, P['neck'], NECK_ANGLE))
        self.BELL_AT = _stand([(_BELL_ON_NECK[0] * ns, _BELL_ON_NECK[1] * ns)], P['neck'], NECK_ANGLE)[0]
        mz = (lambda q: q) if kind != 'calf' else (lambda q: (q[0] if q[0] < 20 else 20 + (q[0] - 20) * 0.8, q[1]))
        hd = lambda pts: _stand([(mz(q)[0] * hs, q[1] * hs) for q in pts], P['head'], HEAD_ANGLE)
        self.hd = hd
        self.HEAD = _smooth(hd(_HEAD_L))
        self.JAW = _smooth(hd(_JAW_L), n=4)
        self.HORN = _smooth(hd(_HORN_L), n=4) if K['horns'] != 'none' else None
        if K['horns'] == 'crooked':
            self.CRUMP = _smooth(hd(_CRUMP_L), n=4)
        elif K['horns'] == 'pair':                           # the far horn: the same cut, set a little forward
            self.CRUMP = _smooth(hd([(q[0] * 0.9 + 8, q[1] * 0.92) for q in _HORN_L]), n=4)
        else:
            self.CRUMP = None
        P['jaw'] = hd([_JAW_PIN_L])[0]
        P['ear'] = hd([_EAR_PIN_L])[0]
        es = hs * (1.12 if kind == 'calf' else 1.0)
        self.EAR = _smooth(_stand([(q[0] * es, q[1] * es) for q in _EAR_L], P['ear'], HEAD_ANGLE + EAR_ANGLE), n=4)
        self.EYE, self.NOSE = hd([_EYE_L])[0], hd([_NOSE_L])[0]
        self.MOUTH = hd([(40, 7.5), (50, 7.2), (59, 9.5)])
        self.HORN_TIP = hd([(6, -43)])[0] if self.HORN else hd([(0, -17)])[0]
        self.eye_r = 3.3 * (1.0 if kind != 'calf' else 1.15)
        thin = lambda pts: [(q[0] * lw, q[1]) for q in pts]
        self.FORE_UP, self.HIND_UP = _smooth(thin(_FORE_UP), n=4), _smooth(thin(_HIND_UP), n=4)
        self.FORE_LO, self.HIND_LO = thin(_lower(L_FORE[1])), thin(_lower(L_HIND[1]))
        self.HOOF_F, self.HOOF_H = thin(_hoof(L_FORE[1])), thin(_hoof(L_HIND[1]))
        self.tail = K['tail']
        self.PATCHES = {k: [_smooth(Ms(q), n=4) for q in v] for k, v in _PATCH[kind].items()}
        self.PATCHES['head'] = [_smooth(hd(_HEAD_PATCH_L[kind]), n=4)]
        self.STANCE = dict(nf=62.0 * kx, ff=53.0 * kx, nh=-73.0 * kx, fh=-60.0 * kx)
        self.stride = STRIDE * (kx ** 0.5)
        self.drop = max(0.0, -P['fore'][1] - 92.0) if kind == 'calf' else 0.0      # a calf stands a little in its knees


# ------------------------------------------------------------------ joint limits ---

LIMITS = dict(
    pitch=(-80, 30), shoulder=(-12, 12), hip=(-30, 14), neck=(-65, 82), head=(-48, 62), jaw=(0, 28), ear=(-55, 60),
    udder=(-25, 25), bell=(-70, 70), eye=(0, 2.0),
    fore_upper=(-48, 110), fore_knee=(-140, 6),          # the knee folds the hoof BACK only
    hind_upper=(-70, 80), hind_hock=(4, 150),            # the hock folds the hoof FORWARD only
)
LEGS = ('nf', 'ff', 'nh', 'fh')         # near fore, far fore, near hind, far hind
STANCE = dict(nf=62.0, ff=53.0, nh=-73.0, fh=-60.0)      # where the lead's hooves stand, x under the body
STRIDE = 96.0            # cow units travelled in one full cycle of four footfalls (the lead and the herd cow)
DUTY = 0.64              # share of the cycle each hoof is on the ground
OFFSET = dict(nh=0.0, nf=0.25, fh=0.5, ff=0.75)        # lateral sequence: hind, fore of the same side, then the other side

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
    # recoil: weight thrown back on the hocks, fore legs braced out in front, head high, tail up
    startle=_pose(dx=-16.0, dy=13.0, pitch=-10.0, hip=4.0, neck=-52.0, head=-6.0, jaw=7.0, ear=48.0, eye=1.9,
                  tail=(66.0, 34.0, -30.0), udder=-10.0,
                  nf=('ik', 63.0, 0.0), ff=('ik', 57.0, 0.0), nh=('ik', -70.0, 0.0), fh=('ik', -54.0, 0.0)),
    # standing, spent: back sagged, head hung level with her knees, ears down, tail dead
    slump=_pose(dy=7.0, pitch=2.0, shoulder=7.0, hip=-5.0, neck=30.0, head=30.0, ear=-46.0, eye=0.3,
                tail=(0.0, 0.0, 0.0), nf=('ik', 60.0, 0.0), ff=('ik', 58.0, 0.0), nh=('ik', -66.0, 0.0), fh=('ik', -64.0, 0.0)),
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


def solve(pose, kind='lead'):
    """Pose -> the puppet laid out in cow units: frames, leg angles, every piece's polygon, and the anchors.

    Joint limits are enforced here (values outside are clamped and listed in ['violations'])."""
    R = Rig.of(kind)
    PIN = R.PIN
    bad = []
    g = lambda k: _lim(k, float(pose.get(k, 0.0)), bad)
    pitch, sh, hp = g('pitch'), g('shoulder'), g('hip')
    neck, head, jaw, ear, udder = g('neck'), g('head'), g('jaw'), g('ear'), g('udder')
    cx, cy = R.C
    r = _rot((cx, cy), pitch)
    F_b = Fr(pitch, cx - r[0] + pose.get('dx', 0.0), cy - r[1] + pose.get('dy', 0.0) + R.drop)
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
            a1, a2, ok = _ik(piv, (spec[1] * R.kx, spec[2]), l1, l2, 1 if fore else -1)
            if not ok:
                bad.append((name + ' reach', round(math.hypot(spec[1] * R.kx - piv[0], spec[2] - piv[1]), 1), l1 + l2))
            up, kn = a1 + par.a, a2 - a1
            if up != _lim(ku, up, bad, name + ' upper') or kn != _lim(kk, kn, bad, name + ' knee'):
                a1 = clamp(up, *LIMITS[ku]) - par.a
                a2 = a1 + clamp(kn, *LIMITS[kk])
        else:
            up, kn = _lim(ku, spec[1], bad, name + ' upper'), _lim(kk, spec[2], bad, name + ' knee')
            a1 = up - par.a
            a2 = a1 + kn
        ang[name] = (a1 + par.a, a2 - a1)                       # relative: upper to its piece, knee to upper
        kx_, ky_ = piv[0] + l1 * math.sin(math.radians(a1)), piv[1] + l1 * math.cos(math.radians(a1))
        hx, hy = kx_ + l2 * math.sin(math.radians(a2)), ky_ + l2 * math.cos(math.radians(a2))
        hoof[name], joint[name] = (hx, hy), (piv, (kx_, ky_))
        up_l, lo_l, hf_l = (R.FORE_UP, R.FORE_LO, R.HOOF_F) if fore else (R.HIND_UP, R.HIND_LO, R.HOOF_H)
        U, L = Fr(-a1, piv[0], piv[1]), Fr(-a2, kx_, ky_)
        legs[name] = ([U(p) for p in up_l], [L(p) for p in lo_l], [L(p) for p in hf_l])

    # tail: three absolute angles from hanging (+ = lifted to the rear), drawn as one tapering strip and a switch
    ta = pose.get('tail', (4.0, 6.0, 8.0))
    p0 = F_h(PIN['tail'])
    pts, p = [p0], p0
    for seg, a in zip((40.0 * R.tail, 34.0 * R.tail, 26.0 * R.tail), ta):
        p = (p[0] - seg * math.sin(math.radians(a)), p[1] + seg * math.cos(math.radians(a)))
        pts.append(p)
    spine = _smooth([pts[0], ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2), pts[1], pts[2], pts[3]], n=5, closed=False)
    left, right = [], []
    m = len(spine)
    tw = 0.8 if R.kind == 'calf' else 1.0
    for i, q in enumerate(spine):
        a_, b_ = spine[max(i - 1, 0)], spine[min(i + 1, m - 1)]
        nx, ny = -(b_[1] - a_[1]), (b_[0] - a_[0])
        nl = math.hypot(nx, ny) or 1.0
        f = i / (m - 1)
        wdt = tw * (lerp(4.2, 2.2, min(1, f / 0.62)) if f < 0.62 else 2.2 + 5.2 * math.sin(math.pi * ((f - 0.62) / 0.38) ** 0.8))
        left.append((q[0] + nx / nl * wdt, q[1] + ny / nl * wdt))
        right.append((q[0] - nx / nl * wdt, q[1] - ny / nl * wdt))
    tail_poly = left + right[::-1]

    # bell: hangs plumb from the throat whatever the neck does, plus its own swing
    bp = F_n(R.BELL_AT)
    F_bell = Fr(_lim('bell', float(pose.get('bell', 0.0)), bad), bp[0], bp[1])

    T = lambda F, poly: [F(q) for q in poly]
    eye = _lim('eye', float(pose.get('eye', 1.0)), bad)
    # back to front
    parts = [('tail', tail_poly, 'hide'),
             ('fh_upper', legs['fh'][0], 'far'), ('fh_lower', legs['fh'][1], 'far'),
             ('ff_upper', legs['ff'][0], 'far'), ('ff_lower', legs['ff'][1], 'far')]
    if R.CRUMP:
        parts.append(('crump', T(F_hd, R.CRUMP), 'horn'))
    parts += [('barrel', T(F_b, R.BARREL), 'hide'), ('hip', T(F_h, R.HIP), 'hide')]
    if R.K['udder']:
        parts.append(('udder', T(F_u, R.UDDER), 'udder'))
    parts += [('nh_upper', legs['nh'][0], 'hide'), ('nh_lower', legs['nh'][1], 'hide'),
              ('shoulder', T(F_s, R.SHOULDER), 'hide'), ('neck', T(F_n, R.NECK), 'hide')]
    if R.K['bell']:
        parts.append(('bell', [F_bell(q) for q in _BELL_L], 'bell'))
    parts += [('jaw', T(F_j, R.JAW), 'hide'), ('head', T(F_hd, R.HEAD), 'hide')]
    if R.HORN:
        parts.append(('horn', T(F_hd, R.HORN), 'horn'))
    parts.append(('ear', T(F_e, R.EAR), 'hide'))
    parts += [('nf_upper', legs['nf'][0], 'hide'), ('nf_lower', legs['nf'][1], 'hide')]      # the near fore leg is nearest
    hoofs = {n: legs[n][2] for n in LEGS}
    fr = {'barrel': F_b, 'hip': F_h, 'shoulder': F_s, 'neck': F_n, 'head': F_hd}
    patches = {k: [T(fr[k], q) for q in v] for k, v in R.PATCHES.items()}
    pins = [F_b(PIN['shoulder']), F_b(PIN['hip']), F_s(PIN['neck']), F_n(PIN['head']), F_hd(PIN['jaw']),
            joint['nf'][0], joint['nf'][1], joint['nh'][0], joint['nh'][1], F_h(PIN['tail'])]
    M = R.M
    anchors = dict(
        muzzle=F_hd(R.NOSE), eye=F_hd(R.EYE), horn=F_hd(R.HORN_TIP), ear=F_e(R.EAR[len(R.EAR) // 2]), poll=F_n(PIN['head']),
        throat=bp, bell=F_bell((0, 16)), withers=F_s(M((52, -142))), back=F_b(M((0, -132))), hook=F_h(M((-40, -139))),
        rump=F_h(M((-93, -100))), seat=F_h(M((-80, -72))), belly=F_b(M((2, -56))), tail_tip=pts[3], tail_head=p0,
        hooves=dict(hoof), hand=hoof['nf'], hand_far=hoof['ff'], knee=joint['nf'][1], hock=joint['nh'][1],
        mouth=F_hd(R.MOUTH[1]),
    )
    attach = dict(nf=(joint['nf'][0], 'shoulder'), ff=(joint['ff'][0], 'shoulder'), nh=(joint['nh'][0], 'hip'),
                  fh=(joint['fh'][0], 'hip'), neck=(F_s(PIN['neck']), 'shoulder'), head=(F_n(PIN['head']), 'neck'),
                  tail=(F_h(M((-86, -121))), 'hip'))
    return dict(parts=parts, hoofs=hoofs, patches=patches, pins=pins, anchors=anchors, eye=(F_hd(R.EYE), eye, R.eye_r),
                clapper=(F_bell(_CLAPPER_L[:2]), _CLAPPER_L[2]) if R.K['bell'] else None,
                strap=(F_n((R.BELL_AT[0] - 4, R.BELL_AT[1] - 30)), bp) if R.K['bell'] else None,
                mouth=T(F_hd, R.MOUTH), nostril=F_hd(R.hd([(60, -2)])[0]),
                angles=ang, violations=bad, attach=attach, frames=fr, rig=R)


def blend(p, q, x):
    """Pose between two poses (x 0 = p, 1 = q; x may run a little past either end for an overshoot).
    Hooves planted in both stay planted; anything else turns on its pin."""
    x = clamp(x, -0.4, 1.4)
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


# ------------------------------------------------------------------ easing and performances ---

_BACK = 1.70158
EASES = dict(
    linear=lambda x: x,
    inout=lambda x: x * x * (3 - 2 * x),                         # leaves gently, arrives gently
    out=lambda x: 1 - (1 - x) ** 3,                              # jumps off, settles (a reaction)
    slow=lambda x: x * x,                                        # heavy start (lifting weight)
    slam=lambda x: x ** 4,                                       # hangs, then falls (the stamp, a collapse)
    snap=lambda x: 1 + (_BACK + 1) * (x - 1) ** 3 + _BACK * (x - 1) ** 2,     # shoots past by a tenth and comes back
    anticip=lambda x: (_BACK + 1) * x ** 3 - _BACK * x * x,      # draws back first, then goes
)


def tween(p, q, x, ease='inout'):
    """The pose x (0..1) of the way from p to q with a named ease: linear, inout, out, slow, slam, snap, anticip."""
    return blend(p, q, EASES[ease](clamp(x)))


class Act:
    """A performance: poses on a timeline, eased, with the bell swinging late on its strap.

        act = cast.Act([(0.0, 'graze'), (1.2, 'graze'), (1.5, 'look_up', 'snap'), (3.0, 'look_up'),
                        (3.25, 'startle', 'out')])
        pose = act.pose(t)                         # then cast.place(ink, pose, x, y, ...)

    keys: (time in seconds, pose or a name in POSES, ease into this key from the one before = 'inout').
    A hold is the same pose twice. The bell is a damped pendulum driven by how the throat moves, so it lags
    every move and rings on after a stop; act.bell_hits is the list of times it swings hardest (for sound)."""

    def __init__(self, keys, kind='lead', bell=True, rate=96):
        self.keys = [(float(k[0]), POSES[k[1]] if isinstance(k[1], str) else k[1], k[2] if len(k) > 2 else 'inout') for k in keys]
        self.keys.sort(key=lambda k: k[0])
        self.kind, self.rate = kind, rate
        self.t0, self.t1 = self.keys[0][0], self.keys[-1][0]
        self._bell, self.bell_hits = [], []
        if bell and KINDS[kind]['bell']:
            self._swing()

    def base(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return dict(ks[0][1])
        for (ta, pa, _), (tb, pb, eb) in zip(ks, ks[1:]):
            if t <= tb:
                return dict(pa) if pa is pb else tween(pa, pb, (t - ta) / max(tb - ta, 1e-9), eb)
        return dict(ks[-1][1])

    def _swing(self):
        g_over_l, damp, dt = 981.0 / 30.0, 1.5, 1.0 / self.rate
        n = int((self.t1 - self.t0 + 4.0) * self.rate) + 3
        xs = [solve(self.base(self.t0 + (i - 1) * dt), self.kind)['anchors']['throat'] for i in range(n + 1)]
        th, om, prev = 0.0, 0.0, 0.0
        for i in range(1, n):
            ax = (xs[i + 1][0] - 2 * xs[i][0] + xs[i - 1][0]) / (dt * dt)
            ay = (xs[i + 1][1] - 2 * xs[i][1] + xs[i - 1][1]) / (dt * dt)
            ax, ay = clamp(ax, -6000, 6000), clamp(ay, -900, 6000)
            om += (-(g_over_l + ay / 30.0) * math.sin(th) - damp * om + (ax / 30.0) * math.cos(th)) * dt
            th = clamp(th + om * dt, -1.15, 1.15)
            self._bell.append(math.degrees(th))
            if abs(th) > 0.12 and (th - prev) * om < 0 and len(self._bell) > 2:
                pass
            if prev * th < 0 and abs(om) > 1.2:                # through the bottom, moving: the clapper strikes
                self.bell_hits.append(round(self.t0 + (i - 1) * dt, 3))
            prev = th

    def pose(self, t):
        p = self.base(t)
        if self._bell:
            i = int(clamp((t - self.t0) * self.rate, 0, len(self._bell) - 1))
            p['bell'] = clamp(p.get('bell', 0.0) + self._bell[i], -70, 70)
        return p


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


_HEELS = dict(nh=('ik', 8.0, -6.0), fh=('ik', 20.0, -6.0))
_SIT = _pose(pitch=-58.0, hip=-10.0, shoulder=3.0, neck=34.0, head=42.0, ear=6.0, tail=(84.0, 62.0, 30.0),
             nf=('ik', 46.0, DESK_Y), ff=('ik', 66.0, DESK_Y), **_HEELS)
# upright on a stool at a desk: both fore hooves on the desk top, hind legs stuck out under it, heels on the floor
POSES['sit'] = _seated(_SIT)
_SIT_A = solve(POSES['sit'])['angles']
# asleep on the desk: the whole front end goes down, the fore legs slide out across the top
POSES['desk_slump'] = _seated(_pose(pitch=-40.0, hip=-26.0, shoulder=10.0, neck=44.0, head=34.0, ear=-45.0, eye=0.0, jaw=3.0,
                                    tail=(70.0, 40.0, 10.0), nf=('ik', 96.0, DESK_Y), ff=('ik', 112.0, DESK_Y), **_HEELS))


def draw_pose(u, reach=0.0, press=1.0):
    """Seated and drawing. `u` 0..1 is where the pencil hoof is across the sheet (0 near her, 1 far); `press`
    1 = hoof down on the paper, 0 = lifted clear of it; `reach` 0..1 leans her whole front end into the far
    side of the sheet. The far hoof holds the sheet down, the head follows the pencil. The body stays on the
    stool: animate u for the stroke. The pencil point is anchors['hand']."""
    x = lerp(40.0, 74.0, clamp(u))
    y = DESK_Y - (1 - clamp(press)) * 12.0
    return _seated(with_(_SIT, pitch=-58.0 + 9.0 * reach, nf=('ik', x + 8.0 * reach, y), ff=('ik', 70.0, DESK_Y),
                         neck=lerp(40.0, 28.0, u) + 4 * reach, head=lerp(46.0, 38.0, u), ear=12.0, eye=0.8,
                         shoulder=lerp(1.0, 7.0, u)))


def stamp_pose(u):
    """Seated, approving her own work. u 0 = hoof on the desk, 0.5 = hoof raised as high as it goes while her
    head goes DOWN to aim at the sheet, 1 = slammed down. Take about 0.5 s over 0..0.5 and 3 frames over
    0.5..1. The stamp is in anchors['hand']."""
    u = clamp(u)
    k = math.sin(math.pi * u) if u < 0.5 else math.cos(math.pi * (u - 0.5)) ** 3
    return _seated(with_(_SIT, pitch=-58.0 - 3.0 * k,
                         nf=('fk', lerp(_SIT_A['nf'][0], 104.0, k), lerp(_SIT_A['nf'][1], -4.0, k)),
                         ff=('ik', lerp(66.0, 48.0, k), DESK_Y), nh=('ik', 8.0 + 8.0 * k, -6.0),
                         neck=lerp(34.0, 66.0, k), head=lerp(42.0, 22.0, k), shoulder=lerp(3.0, -6.0, k),
                         ear=lerp(6.0, 30.0, k), eye=lerp(1.0, 1.35, k)))


def hold_pose(u=1.0, judge=0.0):
    """Seated, holding a drawing up in both fore hooves to look at it. u 0 = sheet flat on the desk, 1 = held up
    at arm's length in front of her face. `judge` -1..1 is her verdict: -1 pulls the head back and down the nose,
    one ear dropped, eye narrowed (she doubts it); +1 pushes the face in close, ears forward, eye wide (she
    loves it). The sheet goes between anchors['hand'] and anchors['hand_far']: see sheet_quad()."""
    u, j = clamp(u), clamp(judge, -1, 1)
    e = u * u * (3 - 2 * u)
    return _seated(with_(_SIT, pitch=-58.0 - 5.0 * e + 3.0 * j * e,
                         nf=('ik', lerp(54.0, 80.0 + 4.0 * min(j, 0), e), lerp(DESK_Y, -196.0, e)),
                         ff=('ik', lerp(72.0, 96.0 + 4.0 * min(j, 0), e), lerp(DESK_Y, -203.0, e)),
                         neck=lerp(34.0, 12.0 - 13.0 * j, e) + (9.0 * j if j > 0 else 0.0) * e,
                         head=lerp(42.0, 30.0 + (16.0 * j if j < 0 else 6.0 * j), e), shoulder=lerp(3.0, -2.0 + 5.0 * max(j, 0), e),
                         ear=lerp(6.0, 14.0 + (34.0 * j if j < 0 else 22.0 * j), e),
                         eye=lerp(1.0, 1.0 + (0.5 * j if j < 0 else 0.45 * j), e)))


def sheet_quad(a, s=1.0, facing=1, w=46.0, h=58.0, lean=0.12):
    """The drawing she holds, as four screen points [bottom-near, bottom-far, top-far, top-near], from the
    anchors `a` returned by place() for a hold_pose. The sheet is cheated a quarter turn toward the camera so
    the drawing on it can be read: map your drawing's unit square onto the quad. Its bottom edge runs from her
    near hoof out past her far hoof; `w` and `h` are its size in cow units, `lean` tips its top away from her.
    Draw it AFTER the cow (it is in front of her far hoof) and then her near hoof is behind it: that is fine,
    or redraw the hoof by pasting a dot at a['hand']."""
    (x0, y0), (x1, y1) = a['hand'], a['hand_far']
    d = math.hypot(x1 - x0, y1 - y0) or 1.0
    x1, y1 = x0 + (x1 - x0) * w * s / d, y0 + (y1 - y0) * w * s / d
    ux, uy = facing * lean * h * s, -h * s
    return [(x0, y0), (x1, y1), (x1 + ux, y1 + uy), (x0 + ux, y0 + uy)]


def drown_pose(u):
    """Seated, going under the paper. u 0 = sitting; 0.5 = chin lifted clear, hooves coming up off the desk;
    1 = head thrown back, muzzle to the sky, one fore leg stretched up and out, the other flailing.
    The paper is yours: at u=1 cover her to about 150 cow units above the floor (PAPER_LINE) and only the
    muzzle, the horns, the bell and the reaching hoof stay out."""
    u = clamp(u)
    e = u * u * (3 - 2 * u)
    k = clamp((u - 0.35) / 0.65)
    k = k * k * (3 - 2 * k)
    return _seated(with_(_SIT, pitch=lerp(-58.0, -72.0, e), hip=lerp(-10.0, -4.0, e), shoulder=lerp(3.0, -8.0, e),
                         neck=lerp(34.0, -26.0, e), head=lerp(42.0, -8.0, e), jaw=lerp(0.0, 9.0, k), ear=lerp(6.0, -40.0, e),
                         eye=lerp(1.0, 1.9, e), tail=(lerp(84.0, 70.0, e), lerp(62.0, 30.0, e), lerp(30.0, 0.0, e)),
                         nf=('fk', lerp(_SIT_A['nf'][0], 84.0, k), lerp(_SIT_A['nf'][1], -4.0, k)),
                         ff=('fk', lerp(_SIT_A['ff'][0], 34.0, k), lerp(_SIT_A['ff'][1], -58.0, k)),
                         nh=('ik', lerp(8.0, 13.0, e), -6.0), fh=('ik', lerp(20.0, 16.0, e), -6.0)))


PAPER_LINE = -150.0      # how high the paper stands at drown_pose(1), cow units above the floor

# ------------------------------------------------------------------ the walk ---

_SAG = dict(f=8.2, h=4.6)                              # how far shoulder / hip sink while two legs share the load
_HUMP = dict(f=8.0, h=4.4)                             # how far the body is carried back up over one stiff leg


def _vault(tau):
    """0 while both legs of a pair are down, then up and over the one that carries (tau in 0..0.5 of the cycle)."""
    lo = DUTY - 0.5
    return 0.0 if tau < lo else math.sin(math.pi * (tau - lo) / (0.5 - lo)) ** 2


def walk(dist, ground=None, lift=1.0, carry=0.0, stride=None, kind='lead', weight=1.0):
    """The pose of the walking cow after `dist` cow units of travel.

    Each hoof is put down ahead of her and STAYS where it was put (in the same units as dist) while the body
    travels over it. CONTACT: a hoof lands with the leg straight out ahead. DOWN: with two legs of a pair
    sharing the load the shoulders (then the hips) sink. PASS and UP: she is carried up and over the single
    stiff leg while the other swings through. The head nods AGAINST the stride (it drops as the shoulders
    rise, a beat late), and the bell, the udder and the tail arrive later still. `ground(xr)` (optional) gives
    the ground height in cow units at xr units ahead of her, relative to the ground under her middle, so the
    hooves and the body follow a hill. `lift` scales how high the hooves are picked up. `carry` (degrees)
    lowers the head: a tired cow walks with carry=25. `weight` scales the sink and the nod (1 = a heavy cow).
    Use walk_on() to do all of this in pixels."""
    R = Rig.of(kind)
    PIN = R.PIN
    stride = stride or R.stride
    ph = dist / stride
    gr = ground or (lambda xr: 0.0)
    p = _pose()
    wt = weight * (0.6 if R.kind == 'calf' else 1.0)
    sd = wt * (_SAG['f'] - _HUMP['f'] * _vault((ph - OFFSET['nf']) % 0.5))
    hd = wt * (_SAG['h'] - _HUMP['h'] * _vault((ph - OFFSET['nh']) % 0.5))
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
        rest = (PIN['fore'][0] + (2 if name[0] == 'n' else FAR_DX + 2)) if fore else (PIN['hind'][0] - (4 if name[0] == 'n' else -FAR_DX + 4))
        down = (n + OFFSET[name]) * stride + rest + stride * DUTY / 2          # where this hoof was put down
        if u < DUTY:
            xw, hgt = down, 0.0
        else:
            w = (u - DUTY) / (1 - DUTY)
            e = w * w * (3 - 2 * w)
            xw = down + stride * (0.12 * w + 0.88 * e)                           # leaves late, reaches, is set down
            hgt = lift * (19.0 if fore else 14.0) * math.sin(math.pi * w ** 0.75) ** 1.3
        xr = xw - dist
        p[name] = ('ik', xr / R.kx, gr(xr) - hgt)
    # the shoulder blade rides up over the loaded near fore leg; the hook bone over the loaded near hind leg
    load = lambda leg: math.sin(math.pi * clamp(((ph - OFFSET[leg]) % 1.0) / DUTY)) if ((ph - OFFSET[leg]) % 1.0) < DUTY else 0.0
    p['shoulder'] = -3.6 * load('nf') + 2.2 * load('ff')
    p['hip'] = 3.0 * load('nh') - 1.8 * load('fh')
    lag = 2 * math.pi * 2 * (ph - OFFSET['nf'] - 0.11)             # late: the head is heavy
    p['neck'] = 6.0 + carry - 5.6 * wt * math.cos(lag)
    p['head'] = 2.0 + carry * 0.35 + 3.0 * wt * math.cos(lag - 0.9)
    p['bell'] = 21.0 * math.sin(lag - 2.7)                        # the bell swings late: a quarter beat after the head
    p['udder'] = 7.0 * math.sin(2 * math.pi * (ph - 0.1))
    p['ear'] = -4.0 + 4.0 * math.cos(lag - 1.6)
    sw = math.sin(2 * math.pi * (ph - 0.2))
    p['tail'] = (5.0 + 5.0 * sw, 8.0 + 11.0 * math.sin(2 * math.pi * (ph - 0.36)), 10.0 + 20.0 * math.sin(2 * math.pi * (ph - 0.52)))
    if R.kind == 'calf':                                         # a calf carries its head up and its tail out
        p['neck'] -= 14.0
        p['ear'] += 14.0
        p['tail'] = tuple(a + 16.0 for a in p['tail'])
    return p


# ------------------------------------------------------------------ drawing ---

TONES = dict(
    lead=dict(hide=(236, 226, 204), far=(203, 190, 166), patch=(74, 56, 46), horn=(214, 196, 150), udder=(226, 172, 160),
              bell=BRASS, hoof=(52, 44, 40), edge=(60, 48, 40), pin=(176, 138, 62), eye=(30, 24, 22)),
    herd=dict(hide=(214, 190, 160), far=(180, 158, 132), patch=(128, 84, 58), horn=(214, 196, 150), udder=(222, 170, 158),
              bell=BRASS, hoof=(52, 44, 40), edge=(60, 48, 40), pin=(176, 138, 62), eye=(30, 24, 22)),
    calf=dict(hide=(240, 232, 214), far=(208, 196, 174), patch=(110, 78, 58), horn=(214, 196, 150), udder=(226, 172, 160),
              bell=BRASS, hoof=(70, 58, 50), edge=(60, 48, 40), pin=(176, 138, 62), eye=(30, 24, 22)),
)

# the line drawing is made of these outlines (each a union of pieces), back to front
_LINE_GROUPS = (('tail', ('tail',)), ('fh', ('fh_upper', 'fh_lower')), ('ff', ('ff_upper', 'ff_lower')), ('crump', ('crump',)),
                ('body', ('barrel', 'hip', 'udder', 'shoulder', 'neck')), ('nh', ('nh_upper', 'nh_lower')),
                ('bell', ('bell',)), ('head', ('jaw', 'head')), ('horn', ('horn',)), ('ear', ('ear',)),
                ('nf', ('nf_upper', 'nf_lower')))


def _screen(pts, x, y, s, facing, tilt):
    if tilt:
        c, sn = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        pts = [(q[0] * c - q[1] * sn, q[0] * sn + q[1] * c) for q in pts]
    return [(x + facing * s * q[0], y + s * q[1]) for q in pts]


def _S(s, kind):
    return s * Rig.of(kind).size


def parts(pose, x=0.0, y=0.0, s=1.0, facing=1, tilt=0.0, kind='lead'):
    """The cut pieces in screen pixels, back to front: [(name, [(x, y), ...]), ...]. For drawing her yourself
    (a morph, a piece flying off): the polygons are closed and each keeps the same point count in every pose."""
    return [(n, _screen(poly, x, y, _S(s, kind), facing, tilt)) for n, poly, _ in solve(pose, kind)['parts']]


def anchors(pose, x=0.0, y=0.0, s=1.0, facing=1, tilt=0.0, kind='lead'):
    """Where things are, in screen pixels, without drawing: see place() for the keys."""
    sol = solve(pose, kind)
    S = _S(s, kind)
    a = {k: (_screen([v], x, y, S, facing, tilt)[0] if k != 'hooves' else
             {n: _screen([q], x, y, S, facing, tilt)[0] for n, q in v.items()}) for k, v in sol['anchors'].items()}
    a['violations'] = sol['violations']
    return a


def _wob(pts, seed, amp):
    """The hand's tremor: a slow displacement field, so a line bends rather than fuzzes. New seed, new drawing."""
    if not amp:
        return pts
    a, b = seed * 2.39996, seed * 1.1347
    f = 2 * math.pi / (46.0 * SS)
    return [(x + amp * (math.sin(f * y * 1.3 + a) + 0.6 * math.sin(f * 2.3 * (x + y) + b)),
             y + amp * (math.sin(f * x * 1.1 + b + 1.7) + 0.6 * math.sin(f * 2.1 * (x - y) + a))) for x, y in pts]


_grain = {}
_BAND = [255 if 10 < v < 245 else 0 for v in range(256)]
_CORE = [255 if v >= 250 else 0 for v in range(256)]


def _pencil_grain(size, seed):
    key = (size, seed % 5)
    if key not in _grain:
        rs = np.random.RandomState(100 + seed % 5)
        w, h = size
        fine = rs.uniform(0.66, 1.0, (h, w))
        lowres = rs.uniform(0.8, 1.0, (h // 14 + 2, w // 14 + 2)).astype(np.float32)
        press = np.asarray(Image.fromarray((lowres * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        _grain[key] = fine * press
    return _grain[key]


def sprite(pose, s=1.0, facing=1, style='shadow', tilt=0.0, color=None, paper=PAPER, line=None, width=2.3,
           pins=False, far=None, kind='lead', seed=0, wobble=0.9, grain=True):
    """The animal as an RGBA cutout. Returns (image, (ax, ay)): paste it with its top-left at (x - ax, y - ay) to
    stand its ground point on (x, y)."""
    sol = solve(pose, kind)
    R = sol['rig']
    S = s * R.size * SS
    P = lambda poly: _screen(poly, 0.0, 0.0, S, facing, tilt)
    if style == 'line' and wobble:
        P = lambda poly: _wob(_screen(poly, 0.0, 0.0, S, facing, tilt), seed, wobble * SS * min(1.0, 0.45 + 0.55 * s * R.size))
    polys = [(n, P(poly), tone) for n, poly, tone in sol['parts']]
    xs = [q[0] for _, poly, _ in polys for q in poly]
    ys = [q[1] for _, poly, _ in polys for q in poly]
    pad = 7 * SS
    x0, y0 = math.floor(min(xs)) - pad, math.floor(min(ys)) - pad - (int(8 * S) if sol['clapper'] else 0) * 0
    wd, ht = int(max(xs) - x0) + pad, int(max(ys) - y0) + pad + (int(5 * S) if sol['clapper'] else 0)
    wd, ht = wd + (-wd) % SS, ht + (-ht) % SS
    O = lambda poly: [(q[0] - x0, q[1] - y0) for q in poly]
    eye_c, eye_open, eye_r = sol['eye']
    ex, ey = O(P([eye_c]))[0]
    er = eye_r * S
    if sol['clapper']:
        clap_c, clap_r = sol['clapper']
        bx, by = O(P([clap_c]))[0]
        strap = O(P(list(sol['strap'])))
    dot = lambda d, cx, cy, r, fill: d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)

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
            if far_m is not None:
                fd.polygon(O(poly), fill=255 if tone == 'far' else 0)
        if sol['clapper']:
            dot(d, bx, by, clap_r * S, 255)
            d.line(strap, fill=255, width=max(2, int(2.6 * S)))
        if eye_open > 0.05:                                   # the eye is a hole cut in the card
            k = 1.0 if eye_open <= 1 else eye_open ** 0.6
            d.ellipse([ex - er * k, ey - er * k * min(eye_open, 1.0), ex + er * k, ey + er * k * min(eye_open, 1.0)], fill=0)
        if pins:
            for q in O(P(sol['pins'])):
                dot(d, q[0], q[1], 1.1 * S, 0)
        img = Image.new('RGBA', (wd, ht), col + (0,))
        img.putalpha(ImageChops.subtract(m, far_m.point(lambda v: int(v * far))) if far_m is not None else m)
    elif style == 'paper':
        img = Image.new('RGBA', (wd, ht), (0, 0, 0, 0))
        tn = dict(TONES[R.kind])
        if color:
            tn['hide'] = tuple(color)
        off = (1.5 * S, 2.2 * S)
        for n, poly, tone in polys:
            pp = O(poly)
            sh = Image.new('L', (wd, ht), 0)
            ImageDraw.Draw(sh).polygon([(q[0] + off[0], q[1] + off[1]) for q in pp], fill=70)
            img = _under(img, sh)
            pm = Image.new('L', (wd, ht), 0)
            ImageDraw.Draw(pm).polygon(pp, fill=255)
            img.paste(tn[tone] + (255,), (0, 0), pm)
            if n in sol['patches'] and sol['patches'][n]:
                qm = Image.new('L', (wd, ht), 0)
                qd = ImageDraw.Draw(qm)
                for patch in sol['patches'][n]:
                    qd.polygon(O(P(patch)), fill=255)
                img.paste(tn['patch'] + (255,), (0, 0), ImageChops.multiply(qm, pm))
            if n.endswith('_lower'):
                hm = Image.new('L', (wd, ht), 0)
                ImageDraw.Draw(hm).polygon(O(P(sol['hoofs'][n[:2]])), fill=255)
                img.paste(tn['hoof'] + (255,), (0, 0), ImageChops.multiply(hm, pm))
            if n == 'tail':                                   # the switch is dark
                j = int(len(pp) // 2 * 0.66)
                tm = Image.new('L', (wd, ht), 0)
                ImageDraw.Draw(tm).polygon(pp[j:len(pp) - j], fill=255)
                img.paste(tn['patch'] + (255,), (0, 0), tm)
            if n == 'bell':
                ImageDraw.Draw(img).line(strap, fill=(120, 60, 50, 255), width=max(2, int(2.4 * S)))
            ImageDraw.Draw(img).line(pp + [pp[0]], fill=tn['edge'] + (120,), width=max(1, int(0.5 * SS)))
        d = ImageDraw.Draw(img)
        if sol['clapper']:
            dot(d, bx, by, clap_r * S, tn['edge'] + (255,))
        if pins:
            for q in O(P(sol['pins'])):
                d.ellipse([q[0] - 1.5 * S, q[1] - 1.5 * S, q[0] + 1.5 * S, q[1] + 1.5 * S], fill=tn['pin'] + (255,),
                          outline=tn['edge'] + (255,))
        _eye(d, ex, ey, er, eye_open, tn['eye'], (250, 246, 236), S)
    elif style == 'line':
        lcol = tuple(line or GRAPHITE)
        lw = max(1.0, width * SS)
        byname = {n: O(poly) for n, poly, _ in polys}
        fill = Image.new('L', (wd, ht), 0)                      # where the paper of her body covers what is behind
        lm = Image.new('L', (wd, ht), 0)                        # the graphite
        body = None
        for gname, names in _LINE_GROUPS:
            gm = Image.new('L', (wd, ht), 0)
            gd = ImageDraw.Draw(gm)
            got = False
            for n in names:
                if n in byname:
                    gd.polygon(byname[n], fill=255)
                    got = True
            if not got:
                continue
            if gname == 'bell':
                gd.line(strap, fill=255, width=max(2, int(2.2 * S)))
            edge = gm.filter(ImageFilter.BoxBlur(lw / 2.0)).point(_BAND)      # a band astride the outline
            if gname == 'body':
                body = gm.filter(ImageFilter.BoxBlur(1.6 * SS)).point(_CORE)   # the body, shrunk a little
            elif gname in ('nh', 'nf') and body is not None:   # where a leg runs up into the body the line lifts off
                edge = ImageChops.subtract(edge, body.point(lambda v: int(v * 0.62)))
            fill = ImageChops.lighter(fill, gm)
            lm = ImageChops.lighter(ImageChops.multiply(lm, ImageChops.invert(gm)), edge)
            ld = ImageDraw.Draw(lm)
            if gname in ('fh', 'ff', 'nh', 'nf'):
                ld.polygon(O(P(sol['hoofs'][gname])), fill=215)
            if gname == 'bell':
                ld.polygon(byname['bell'], fill=120)
                dot(ld, bx, by, clap_r * S, 255)
            if gname == 'head':
                ld.line(O(P(sol['mouth'])), fill=255, width=max(1, int(lw * 0.8)), joint='curve')
                nx_, ny_ = O(P([sol['nostril']]))[0]
                dot(ld, nx_, ny_, 1.2 * S, 255)
                _eye_mask(ld, ex, ey, er * 0.95, eye_open, lw)
            if gname == 'tail':
                pp = byname['tail']
                j = int(len(pp) // 2 * 0.7)
                ld.polygon(pp[j:len(pp) - j], fill=150)
        fill = fill.resize((wd // SS, ht // SS), Image.LANCZOS)
        lm = lm.resize((wd // SS, ht // SS), Image.LANCZOS)
        if grain:
            g = _pencil_grain(lm.size, seed)
            lm = Image.fromarray((np.asarray(lm, np.float32) * g).clip(0, 255).astype(np.uint8))
        img = Image.new('RGBA', lm.size, tuple(paper or PAPER) + (0,))
        if paper is not None:
            img.putalpha(fill)
        ink_l = Image.new('RGBA', lm.size, lcol + (0,))
        ink_l.putalpha(lm)
        img = Image.alpha_composite(img, ink_l)
        return img, (-x0 / SS, -y0 / SS)
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


def _eye_mask(d, ex, ey, er, opn, lw):
    if opn <= 0.05:
        d.arc([ex - er, ey - er * 0.6, ex + er, ey + er], 10, 170, fill=255, width=max(1, int(lw * 0.8)))
        return
    k = opn ** 0.6 if opn > 1 else 1.0
    rx, ry = er * k, er * k * min(opn, 1.0)
    if opn > 1.15:
        d.ellipse([ex - rx * 1.3, ey - ry * 1.3, ex + rx * 1.3, ey + ry * 1.3], outline=255, width=max(1, int(lw * 0.7)))
        rx, ry = er * 0.6, er * 0.6
    d.ellipse([ex - rx, ey - ry, ex + rx, ey + ry], fill=255)
    if opn < 0.75:                                             # a lid line over a narrowed eye
        d.line([(ex - er * 1.4, ey - ry - lw * 0.3), (ex + er * 1.4, ey - ry + lw * 0.2)], fill=255, width=max(1, int(lw * 0.8)))


def place(ink, pose, x, y, s=1.0, facing=1, style='shadow', tilt=0.0, alpha=1.0, kind='lead', **opts):
    """Draw the animal with the ground under the middle of its barrel at (x, y). `ink` is the kit's Ink or a PIL image.

    facing=1 looks right, -1 left. tilt (degrees, + = nose down as drawn facing right) leans the whole puppet.
    opts go to sprite(): color=, paper=, line=, width=, pins=True, far=0.15, seed=, wobble=, grain=.
    Returns the anchors in screen pixels: muzzle, mouth, eye, horn, ear, poll, throat, bell, withers, back, hook,
    rump, seat, belly, tail_tip, tail_head, hand (near fore hoof), hand_far, knee, hock, hooves {nf, ff, nh, fh},
    violations (joint limits that had to be clamped: should be [])."""
    img, (ax, ay) = sprite(pose, s, facing, style, tilt, kind=kind, **opts)
    xy = (int(round(x - ax)), int(round(y - ay)))
    if alpha < 1:
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    if hasattr(ink, 'paste') and hasattr(ink, 'd'):
        ink.paste(img, xy)
    else:
        ink.paste(img, xy, img)
    fx, fy = x - ax - xy[0], y - ay - xy[1]                     # the rounding, so anchors match the pixels
    return anchors(pose, x - fx, y - fy, s, facing, tilt, kind)


def walk_on(ink, x, ground, s=1.0, facing=1, style='shadow', lift=1.0, carry=0.0, phase=0.0, over=None, kind='lead',
            weight=1.0, **opts):
    """Walk the animal along a ground line. `x` is where its middle is now (px); `ground` is a function px -> px
    (or a number for flat ground). The phase comes from x itself, so every hoof that is down stays on the same
    pixel of ground until it is picked up: move x, and she walks. Speed is yours: one cycle is
    cycle_px(s, kind) pixels (96 px for the lead at s=1); a plodding cow takes about 1.4 s over it, so move her
    about 68 * s px a second. `phase` (0..1) offsets one animal from another. `over` replaces pose keys after
    the walk is solved (e.g. over=dict(neck=-20, ear=30) to look up as she goes). ink=None only returns the
    anchors."""
    g = (lambda px: float(ground)) if not callable(ground) else ground
    S = _S(s, kind)
    y0 = g(x)
    rel = lambda xr: (g(x + facing * xr * S) - y0) / S
    pose = walk(facing * x / S + phase * Rig.of(kind).stride, ground=rel, lift=lift, carry=carry, kind=kind, weight=weight)
    if over:
        pose.update(over)
    if ink is None:
        return anchors(pose, x, y0, s, facing, 0.0, kind)
    return place(ink, pose, x, y0, s, facing, style, kind=kind, **opts)


def cycle_px(s=1.0, kind='lead'):
    """Pixels travelled in one full walk cycle (four footfalls) at scale s."""
    return Rig.of(kind).stride * _S(s, kind)


def footfalls(x0, x1, s=1.0, facing=1, phase=0.0, kind='lead'):
    """Where and when (as x of her middle) each hoof comes down while she walks from x0 to x1 on walk_on():
    [(x_of_her_middle_px, leg, hoof_x_px), ...] in order. For hoof sounds, dust, and wearing the path."""
    R = Rig.of(kind)
    S = _S(s, kind)
    d0, d1 = sorted((facing * x0 / S + phase * R.stride, facing * x1 / S + phase * R.stride))
    out = []
    for name in LEGS:
        fore = name[1] == 'f'
        rest = (R.PIN['fore'][0] + (2 if name[0] == 'n' else FAR_DX + 2)) if fore else (R.PIN['hind'][0] - (4 if name[0] == 'n' else -FAR_DX + 4))
        n = math.floor(d0 / R.stride - OFFSET[name]) - 1
        while True:
            d = (n + OFFSET[name]) * R.stride                    # the travel at which this hoof lands
            if d > d1:
                break
            if d >= d0:
                down = d + rest + R.stride * DUTY / 2
                out.append((facing * (d - phase * R.stride) * S, name, facing * (down - phase * R.stride) * S))
            n += 1
    return sorted(out, key=lambda r: r[0] * facing)


def outline(pose, s=1.0, facing=1, n=240, tilt=0.0, kind='lead'):
    """The whole silhouette as ONE closed line: n points (px, relative to the ground point), evenly spaced along
    the contour, starting at the tip of the muzzle and running over the head and back first. For the drawn
    acts: draw it as a pencil line, or pair it point for point with another n-point contour and interpolate."""
    img, (ax, ay) = sprite(with_(pose, eye=0.0), s * 3, facing, 'shadow', tilt, kind=kind)
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
    mz = anchors(pose, 0, 0, s, facing, tilt, kind)['muzzle']
    i0 = min(range(len(pts)), key=lambda i: (pts[i][0] - mz[0]) ** 2 + (pts[i][1] - mz[1]) ** 2)
    pts = pts[i0:] + pts[:i0]
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


def stool_and_desk(ink, x, y, s=1.0, facing=1, style='shadow', color=None, line=None, paper=PAPER, width=2.0):
    """The stool she sits on and the desk she draws at, for the cow placed at the same (x, y, s, facing) in a
    seated pose. Draw it BEFORE the cow. Returns {'top': (x0, x1, y) of the desk top, 'sheet': (cx, y) where the
    paper lies, 'stool': (x, y) of the middle of the seat}."""
    X = lambda u: x + facing * s * u
    Y = lambda v: y + s * v
    im = ink.img if hasattr(ink, 'img') else ink
    d = ImageDraw.Draw(im, 'RGBA')
    col = tuple(color or (BLACK if style == 'shadow' else (line or GRAPHITE)))
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
    return dict(top=(X(DESK_X[0]), X(DESK_X[1]), Y(DESK_Y)), sheet=(X(84), Y(DESK_Y)), stool=(X(STOOL_X), Y(STOOL_Y)))


# ------------------------------------------------------------------ checks ---


def _inside(p, poly):
    x, y = p
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def named_poses():
    """Every pose the cast offers, by name, for sheets and checks."""
    named = dict(POSES)
    named.update({'draw_%.1f_%d' % (u, r): draw_pose(u, r) for u in (0, 0.5, 1) for r in (0, 1)})
    named.update({'stamp_%.2f' % u: stamp_pose(u) for u in (0, 0.25, 0.5, 0.75, 1)})
    named.update({'hold_%.1f_%+d' % (u, j): hold_pose(u, j) for u in (0, 0.5, 1) for j in (-1, 0, 1)})
    named.update({'drown_%.2f' % u: drown_pose(u) for u in (0, 0.25, 0.5, 0.75, 1)})
    return named


def check(verbose=True, strict=True):
    """MEASURED checks, the ones the representation supports. Returns a dict; raises if a hard one fails.

    contact drift: over two walk cycles in 1/96-cycle steps, for each kind, how far each planted hoof moves from
      where it was put down (cow units, world space), on the flat and on a hill.
    joint limits: no named pose, no blend between the standing poses, and no walk frame needs a clamp.
    attachment: every limb's pin lies inside the piece it hangs from (no detached limbs), all poses, all kinds.
    bob: the vertical travel of withers, hook bone and muzzle over a walk cycle (the weight you should see)."""
    drift, viol, loose = 0.0, [], []
    res = {}
    hill = lambda xr: 9.0 * math.sin(xr / 70.0)

    def att(sol, nm):
        pp = {n: poly for n, poly, _ in sol['parts']}
        for limb, (pt, piece) in sol['attach'].items():
            if not _inside(pt, pp[piece]):
                loose.append((nm, limb))

    for kind in KINDS:
        R = Rig.of(kind)
        for gname, gr in (('flat', None), ('hill', hill)):
            planted, wy, hy, heads = {}, [], [], []
            for k in range(0, 193):
                dist = R.stride * k / 96.0
                ph = dist / R.stride
                g = (lambda xr, d=dist: hill(xr + d) - hill(d)) if gr else None
                sol = solve(walk(dist, ground=g, kind=kind), kind)
                viol += [('%s walk %s %.3f' % (kind, gname, ph),) + v for v in sol['violations']]
                att(sol, '%s walk %.3f' % (kind, ph))
                base = hill(dist) if gr else 0.0
                for name in LEGS:
                    u = (ph - OFFSET[name]) % 1.0
                    hx, hy_ = sol['anchors']['hooves'][name]
                    if u < DUTY - 1e-9:
                        key = (name, math.floor(ph - OFFSET[name] + 1e-9))
                        wpt = (hx + dist, hy_ + base)
                        if key in planted:
                            drift = max(drift, abs(wpt[0] - planted[key][0]), abs(wpt[1] - planted[key][1]))
                        else:
                            planted[key] = wpt
                wy.append(sol['anchors']['withers'][1])
                hy.append(sol['anchors']['hook'][1])
                heads.append(sol['anchors']['muzzle'][1])
            if gname == 'flat':
                res[kind + '_bob'] = dict(withers=round(max(wy) - min(wy), 2), hook=round(max(hy) - min(hy), 2),
                                          muzzle=round(max(heads) - min(heads), 2))
    named = named_poses()
    for nm, p in named.items():
        sol = solve(p)
        viol += [(nm,) + v for v in sol['violations']]
        att(sol, nm)
    stand = ('stand', 'graze', 'look_up', 'startle', 'slump')
    for a in stand:
        for b in stand:
            for x in (0.25, 0.5, 0.75):
                viol += [('%s>%s %.2f' % (a, b, x),) + v for v in solve(blend(POSES[a], POSES[b], x))['violations']]
        for kind in ('herd', 'calf'):
            sol = solve(POSES[a], kind)
            viol += [(kind + ' ' + a,) + v for v in sol['violations']]
            att(sol, kind + ' ' + a)
    res.update(contact_drift=round(drift, 4), limit_violations=viol, detached=loose, poses=len(named))
    if verbose:
        for k, v in res.items():
            print('  %-18s %s' % (k, v))
    assert drift < 0.05, 'a planted hoof slid'
    if strict:
        assert not viol, 'joint limits broken: %r' % viol[:4]
        assert not loose, 'detached: %r' % loose[:4]
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


def _demo_sheet(im, a, s, facing=1, col=BLACK, fill=(250, 246, 236)):
    q = sheet_quad(a, s, facing)
    d = ImageDraw.Draw(im)
    d.polygon(q, fill=fill, outline=col)
    d.line(q + [q[0]], fill=col, width=2)


def _demo_paper(im, x, y, s, level, col=BLACK, fill=(250, 246, 236), seed=3):
    """A heap of loose sheets up to `level` cow units above the floor (only for the sheet: scenes make their own)."""
    import random
    rng = random.Random(seed)
    d = ImageDraw.Draw(im)
    for k in range(150):
        cx = x + s * rng.uniform(-150, 170)
        top = y + s * level * (1 - ((cx - x) / (s * 200)) ** 2) * rng.uniform(0.25, 1.0) ** 0.5
        cy = rng.uniform(top, y) if k < 110 else top
        a = rng.uniform(-0.5, 0.5)
        w, h = 30 * s, 5 * s
        pts = [(cx + (ux * math.cos(a) - uy * math.sin(a)), cy + (ux * math.sin(a) + uy * math.cos(a)))
               for ux, uy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        d.polygon(pts, fill=fill, outline=col)


def _sheets():
    out = FILMS / 'stills' / 'cowpath_cast'
    out.mkdir(parents=True, exist_ok=True)

    cells = [('stand', POSES['stand'], 0), ('graze', POSES['graze'], 0), ('look_up', POSES['look_up'], 0),
             ('startle', POSES['startle'], 0), ('slump', POSES['slump'], 0),
             ('sit', POSES['sit'], 1), ('draw_pose(0.1)', draw_pose(0.1), 1), ('draw_pose(1, 1)', draw_pose(1.0, 1.0), 1),
             ('hold_pose(1, -1)  doubts it', hold_pose(1, -1), 2), ('hold_pose(1, +1)  loves it', hold_pose(1, 1), 2),
             ('stamp_pose(0.5)', stamp_pose(0.5), 1), ('stamp_pose(1)', stamp_pose(1.0), 1),
             ('desk_slump', POSES['desk_slump'], 1), ('drown_pose(0.6)', drown_pose(0.6), 3), ('drown_pose(1)', drown_pose(1.0), 4)]

    def pose_sheet(style, name):
        im = _backlight((1920, 1620)) if style == 'shadow' else Image.new('RGB', (1920, 1620), PAPER)
        col = BLACK if style == 'shadow' else GRAPHITE
        for i, (nm, p, prop) in enumerate(cells):
            cx, gy = 200 + (i % 5) * 380, 440 + (i // 5) * 520
            d = ImageDraw.Draw(im)
            d.line((cx - 180, gy, cx + 180, gy), fill=col, width=3)
            x = cx - (30 if prop else 20)
            if prop:
                stool_and_desk(im, x, gy, 1.25, style=style)
            a = place(im, p, x, gy, 1.25, style=style, seed=i)
            if prop == 2:
                _demo_sheet(im, a, 1.25, col=col)
            if prop >= 3:
                _demo_paper(im, x, gy, 1.25, PAPER_LINE * (0.6 if prop == 3 else 1.0), col=col,
                            fill=(250, 246, 236) if style != 'shadow' else (60, 44, 30))
            if a['violations']:
                print('  !!', nm, a['violations'])
            ImageDraw.Draw(im).text((cx - 170, gy + 14), nm, fill=col)
        im.save(out / name)

    pose_sheet('shadow', 'pose_sheet.png')
    pose_sheet('line', 'pose_sheet_line.png')

    # 2. walk strip: 12 frames of one cycle, the ground marked where each hoof is down
    im = _backlight((1920, 1080))
    d = ImageDraw.Draw(im)
    s = 1.05
    for k in range(12):
        cx, gy = 170 + (k % 6) * 310, 430 + (k // 6) * 500
        d.line((cx - 150, gy, cx + 150, gy), fill=BLACK, width=3)
        a = place(im, walk(STRIDE * k / 12.0), cx - 6, gy, s)
        d = ImageDraw.Draw(im)
        for name in LEGS:
            u = (k / 12.0 - OFFSET[name]) % 1.0
            hx, hy = a['hooves'][name]
            if u < DUTY:
                d.polygon([(hx, gy + 8), (hx - 6, gy + 20), (hx + 6, gy + 20)], fill=(150, 40, 30))
        d.text((cx - 140, gy + 26), 'frame %d  phase %.3f' % (k + 1, k / 12.0), fill=BLACK)
        d.line((cx - 150, gy - 141 * s, cx + 150, gy - 141 * s), fill=(150, 40, 30), width=1)     # standing withers
        d.line((cx - 150, a['muzzle'][1], cx + 150, a['muzzle'][1]), fill=(40, 70, 150), width=1)  # the nose now
    im.save(out / 'walk_strip.png')

    # 3. the walk in the world: onion skin over a hill, hooves pile on single points; herd cow and calf follow
    im = _backlight((1920, 540))
    g = lambda px: 430 + 26 * math.sin(px / 210.0)
    d = ImageDraw.Draw(im)
    d.line([(xx, g(xx)) for xx in range(0, 1921, 8)], fill=BLACK, width=3)
    for k in range(0, 13):
        walk_on(im, 760 + k * 16, g, s=1.0, alpha=1.0 if k == 12 else 0.14)
    walk_on(im, 480, g, s=1.0, kind='herd', phase=0.4)
    walk_on(im, 250, g, s=1.0, kind='calf')
    walk_on(im, 1300, g, s=1.0, carry=25)
    walk_on(im, 1640, g, s=1.0, facing=-1, kind='herd', phase=0.2)
    im.save(out / 'walk_world.png')

    # 4. the three materials and the three kinds
    im = Image.new('RGB', (1920, 1080), PAPER)
    im.paste(_backlight((640, 1080)), (0, 0))
    im.paste(Image.new('RGB', (640, 1080), (86, 128, 122)), (1280, 0))
    for i, (style, opts) in enumerate((('shadow', {}), ('line', {}), ('paper', dict(pins=True)))):
        ox = i * 640
        place(im, POSES['look_up'], ox + 300, 400, 1.5, style=style, **opts)
        place(im, POSES['graze'], ox + 150, 640, 0.9, style=style, kind='herd', **opts)
        place(im, POSES['look_up'], ox + 470, 640, 0.9, style=style, kind='calf', facing=-1, **opts)
        place(im, walk(30), ox + 110, 800, 0.5, style=style, **opts)
        place(im, walk(60, kind='herd'), ox + 290, 800, 0.5, style=style, kind='herd', **opts)
        place(im, walk(20, kind='calf'), ox + 430, 800, 0.5, style=style, kind='calf', **opts)
        place(im, POSES['startle'], ox + 560, 800, 0.5, style=style, facing=-1, **opts)
        for j, sc in enumerate((0.36, 0.26, 0.18)):                       # how small she can go
            place(im, walk(40 + 30 * j), ox + 120 + j * 170, 960, sc, style=style, **opts)
            place(im, POSES['graze'], ox + 200 + j * 170, 960, sc, style=style, kind='herd', **opts)
    pts = outline(POSES['stand'], 0.8, n=240)
    d = ImageDraw.Draw(im)
    pp = [(960 + q[0], 1060 + q[1]) for q in pts]
    d.line(pp + [pp[0]], fill=INK, width=2)
    for q in pp[::8]:
        d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(150, 40, 30))
    im.save(out / 'materials.png')

    # 5. a performance, key by key, with the bell on its pendulum: graze, hear, look, startle, settle
    act = Act([(0.0, 'graze'), (0.8, 'graze'), (1.1, 'look_up', 'snap'), (2.2, 'look_up'), (2.45, 'startle', 'out'),
               (3.2, 'startle'), (4.4, 'stand', 'inout')])
    im = _backlight((1920, 540))
    d = ImageDraw.Draw(im)
    d.line((0, 440, 1920, 440), fill=BLACK, width=3)
    for i, t in enumerate((0.5, 0.95, 1.1, 1.3, 2.3, 2.45, 2.7, 4.4)):
        place(im, act.pose(t), 130 + i * 236, 440, 0.82)
        ImageDraw.Draw(im).text((60 + i * 236, 460), 't = %.2f' % t, fill=BLACK)
    im.save(out / 'act_strip.png')
    print('sheets ->', out)


if __name__ == '__main__':
    print('checks (MEASURED):')
    check(strict=False)
    _sheets()
    check(verbose=False)
