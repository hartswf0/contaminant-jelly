"""ACT 1 · THE COW PATH · 0.0 to 36.0 · backlit shadow theatre (scion/animation-02).

    import act_cows
    act_cows.SECONDS            # 36.0
    act_cows.draw(t, ink)       # a full 960x540 frame at act time t (0 = lamp up, 36 = the pencil line)
    act_cows.sound(mix, at)     # the act's sound, placed at `at` seconds in the film's Mix

Run alone:
    python3 films/swarm/cowpath/act_cows.py                  # assets/films/cowpath-act1.mp4
    python3 films/swarm/cowpath/act_cows.py --sheet OUT.png t0 t1 [n] [--bw]   # contact sheet
    python3 films/swarm/cowpath/act_cows.py --still OUT.png t
    python3 films/swarm/cowpath/act_cows.py --check          # measured invariants
    python3 films/swarm/cowpath/act_cows.py --xsheet         # the exposure sheet as text

The SCION's primitives as they stand in this file:
  backlit character shapes   cast.sprite(style='shadow') cards; men, roller, barrow cut with sets.Card
  pinned joints + limits     cast's rig (cast.LIMITS, enforced; --check counts clamps); the tree's pin at its cut
  fore/midground shadows     PLANES: tissue hills, 'mid' (tree, stump, fence: umber card), 'actor' (black), 'fore'
  replacement profiles       the card turned on its vertical axis (TURN) for the wheel at the bog
  contact planes             Track: every planted hoof is a fixed point of the path until it is lifted; the
                             prints are those same points, and they are what wears the tissue
  exposure sheet             XSHEET: named cells on 2s (12 drawings a second); the tree falls on 1s
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
for _p in (str(HERE), str(FILMS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from kit import Film, Ink, clamp, ramp, smooth, ease, lerp, W, H, FPS   # noqa: E402
import cast                                                            # noqa: E402
import sets                                                            # noqa: E402
import study_shadow as ss                                              # noqa: E402

SECONDS = 36.0
SLUG = 'cowpath-act1'
S_COW = 0.55                 # the board's scale for the hill: the lead is 78 px at the withers
ON = 2                       # staged on 2s
DPS = FPS // ON              # drawings a second

BLACK = sets.BLACK
MID = (66, 40, 24)           # the 'mid' plane: umber card (tree, stump, fence) so a black actor in front still reads
P_ = cast.POSES


# ================================================================ the contact plane ===

def _polyline_y(pts):
    xs = [p[0] for p in pts]

    def f(x):
        if x <= xs[0]:
            return pts[0][1]
        for a, b in zip(pts, pts[1:]):
            if a[0] <= x <= b[0] and b[0] > a[0]:
                return lerp(a[1], b[1], (x - a[0]) / (b[0] - a[0]))
        return pts[-1][1]
    return f


RIDGE_Y = _polyline_y(sets.catmull(sets.RIDGE, 8))          # the hill sheet's cut top edge, as the mask cuts it


class Track:
    """A walked line on the stage, by arc length (px). Arc 0 is the crest; negative arcs are behind the hill
    (the climb up its back, hidden by the sheet); `dip` pushes the line down the screen locally."""

    def __init__(self, pts, zero, dip=None):
        self.pts = [(float(x), float(y)) for x, y in pts]
        acc = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.acc = [v - acc[zero] for v in acc]
        self.dip = dip
        self.a0, self.a1 = self.acc[0], self.acc[-1]

    def at(self, a):
        acc, pts = self.acc, self.pts
        if a <= acc[0]:
            i = 0
        elif a >= acc[-1]:
            i = len(pts) - 2
        else:
            lo, hi = 0, len(acc) - 1
            while hi - lo > 1:
                m = (lo + hi) // 2
                if acc[m] <= a:
                    lo = m
                else:
                    hi = m
            i = lo
        d = acc[i + 1] - acc[i]
        f = (a - acc[i]) / d if d > 0 else 0.0
        x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
        y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        if self.dip:
            y += self.dip(a)
        return x, y

    def heading(self, a, h=42.0):
        p, q = self.at(a - h), self.at(a + h)
        return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


# the climb up the back of the hill to the crest: steep, wholly hidden by the sheet
_BACK = sets.catmull([(14, 372), (40, 306), (72, 236), (100, 190), (120, 170)], 8)[:-1]
_N_BACK = len(_BACK)
A_BRANCH = 868.0             # where the herd leaves the path for the bank (after the loop, short of the water)
_i_br = min(range(len(sets.PATH)), key=lambda i: abs(sets.path_u(*sets.PATH[i]) * sets.PATH_LEN - A_BRANCH))
_BANK = sets.catmull([sets.PATH[_i_br - 6], sets.PATH[_i_br], (796, 412), (846, 404), (896, 390), (950, 378), (1030, 366),
                      (1160, 352)], 8)[9:]

A_BOULDER = 352.0            # where she stands when she tries the boulder


def _dip(a):                 # her first line bends toward the boulder (she was aiming straight) by 12 px
    return 11.0 * smooth(ramp(a, 296.0, A_BOULDER)) * (1 - smooth(ramp(a, A_BOULDER + 22, A_BOULDER + 92)))


PATH_T = Track(_BACK + sets.PATH, _N_BACK)                        # the canonical path, with the hidden climb
FIRST_T = Track(_BACK + sets.PATH, _N_BACK, dip=_dip)             # the line she walks the first time
HERD_T = Track(_BACK + sets.PATH[:_i_br] + _BANK, _N_BACK)        # the herd's: off along the bank at the bottom
A_END = PATH_T.a1                                                 # 981: the water


# ================================================================ the walker ===

def _tilt(theta):
    """How far the card is leaned for a line heading `theta` degrees: part of the slope; the legs take the rest."""
    return clamp(LEAN * math.degrees(math.asin(math.sin(math.radians(theta)))), -15.0, 15.0)


def _turn(theta):
    """The card turned on its vertical axis: 1 = profile facing right, -1 facing left, between = edge-on."""
    k = clamp(math.cos(math.radians(theta)) / 0.42, -1.0, 1.0)
    if abs(k) < 0.3:
        k = 0.3 if k >= 0 else -0.3
    return k


LEAN = 0.40                  # share of the path's slope taken by leaning the whole card
PITCH = 0.50                 # share of what is left taken by pitching the body; the legs fold for the rest


class Stance:
    """Where a puppet is held: ground point, lean, which way the card faces, and how the path lies under it."""

    def __init__(self, track, a, kind='lead', s=S_COW):
        self.track, self.a, self.kind, self.s = track, a, kind, s
        self.R = cast.Rig.of(kind)
        self.sc = s * self.R.size
        self.x, self.y = track.at(a)
        th = track.heading(a)
        self.theta = th
        self.tilt = _tilt(th)
        self.turn = _turn(th)
        self.face = 1 if self.turn >= 0 else -1
        self.flat = smooth(ramp(abs(math.degrees(math.asin(math.sin(math.radians(th))))), 48.0, 62.0))   # 1 = in the wheel
        if a < 0:
            self.flat = max(self.flat, smooth(ramp(-a, 10.0, 40.0)))
        self._c, self._s = math.cos(math.radians(self.tilt)), math.sin(math.radians(self.tilt))

    def local(self, arc):
        """A point of the path, in the puppet's own units (x ahead, y down), seen from where it is held."""
        qx, qy = self.track.at(arc)
        ex, ey = (qx - self.x) * self.face, qy - self.y
        return (ex * self._c + ey * self._s) / self.sc, (-ex * self._s + ey * self._c) / self.sc

    def ground(self, xr):
        """Height of the path (units, + = lower) at xr units ahead of her."""
        if self.flat >= 1:
            return 0.0
        return self.local(self.a + xr * self.sc)[1] * (1 - self.flat)

    def world(self, lx, ly=0.0):
        ex = (lx * self._c - ly * self._s) * self.sc
        ey = (lx * self._s + ly * self._c) * self.sc
        return self.x + self.face * ex, self.y + ey


def stand_on(pose, st):
    """Set a standing pose on the path under a Stance: every hoof target follows the ground there and the
    body takes the slope the lean has not."""
    R = st.R
    q = dict(pose)
    gf, gh = st.ground(R.PIN['fore'][0]), st.ground(R.PIN['hind'][0])
    span = R.PIN['fore'][0] - R.PIN['hind'][0]
    q['pitch'] = pose.get('pitch', 0.0) + PITCH * math.degrees(math.atan2(gf - gh, span))
    q['dy'] = pose.get('dy', 0.0) + (gf * -R.PIN['hind'][0] + gh * R.PIN['fore'][0]) / span
    for leg in cast.LEGS:
        v = pose[leg]
        if v[0] == 'ik':
            q[leg] = ('ik', v[1], v[2] + st.ground(v[1] * R.kx))
    return q


def walk_pose(st, phase=0.0, stride_k=1.0, lift=1.0, carry=0.0, weight=1.0):
    """The walking pose at a Stance. Each planted hoof is a fixed point of the path (by arc), so it stays on
    the same pixel until it is lifted, whatever the slope or the bend. Returns (pose, planted) where planted is
    {leg: (x, y, heading)} for hooves on the ground."""
    R = st.R
    stride = R.stride * stride_k
    dist = st.a / st.sc + phase * stride
    pose = cast.walk(dist, lift=lift, carry=carry, stride=stride, kind=st.kind, weight=weight)
    gf, gh = st.ground(R.PIN['fore'][0]), st.ground(R.PIN['hind'][0])
    span = R.PIN['fore'][0] - R.PIN['hind'][0]
    pose['pitch'] += PITCH * math.degrees(math.atan2(gf - gh, span))
    pose['dy'] += (gf * -R.PIN['hind'][0] + gh * R.PIN['fore'][0]) / span
    planted = {}
    for leg in cast.LEGS:
        v = pose[leg]
        xr = v[1] * R.kx
        hgt = -v[2]
        arc = st.a + xr * st.sc
        if st.flat < 1:
            lx, ly = st.local(arc)
            lx = lerp(lx, xr, st.flat)
            ly = ly * (1 - st.flat)
            pose[leg] = ('ik', lx / R.kx, ly - hgt)
        if hgt < 0.01 and st.flat < 0.5:
            qx, qy = st.track.at(arc)
            planted[leg] = (qx, qy, st.track.heading(arc, 8.0), arc)
    return ss.reach_fix(pose, st.kind), planted


_sprite_cache = {}


def cut(pose, st, color=None):
    """The card for a pose at a Stance: (RGBA, (left, top))."""
    im, (ax, ay) = cast.sprite(pose, st.s, st.face, 'shadow', st.tilt, kind=st.kind, color=color)
    k = abs(st.turn)
    if k < 0.999:                                           # the card turning on its own axis (a replacement profile)
        w = max(2, int(round(im.width * k)))
        im = im.resize((w, im.height), Image.LANCZOS)
        ax = ax * k
    return im, (int(round(st.x - ax)), int(round(st.y - ay)))


def _clip_behind_hill(im, xy, a):
    """What is behind the hill sheet does not show: below the cut edge, left of the crest."""
    if a > 70:
        return im
    x_lim = 121 + 26 * clamp(-a / 60.0)
    x0, y0 = xy
    if x0 >= x_lim:
        return im
    al = np.asarray(im.getchannel('A')).copy()
    for cx in range(0, min(im.width, int(x_lim - x0) + 1)):
        ry = int(RIDGE_Y(x0 + cx) + 1.5) - y0
        if ry < im.height:
            al[max(ry, 0):, cx] = 0
    im = im.copy()
    im.putalpha(Image.fromarray(al))
    return im


def put(ink, im, xy):
    ink.img.paste(im, xy, im)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


# ================================================================ timing ===

def trap(t, t0, t1, a0, a1, r0=0.35, r1=0.35):
    """Arc at time t for a move a0 -> a1 over [t0, t1]: speeds up for r0 s, cruises, brakes for r1 s
    (r = 0 means already at speed at that end)."""
    T = t1 - t0
    v = (a1 - a0) / (T - r0 / 2 - r1 / 2)
    tau = clamp(t - t0, 0.0, T)
    if r0 > 0 and tau < r0:
        return a0 + v * tau * tau / (2 * r0)
    if tau <= T - r1 or r1 <= 0:
        return a0 + v * (tau - r0 / 2)
    q = T - tau
    return a1 - v * q * q / (2 * r1)


def q2(t):
    """Time of the drawing on screen at t (staged on 2s)."""
    return math.floor(t * DPS + 1e-6) / DPS


# the lamp dims and returns twice: each dark is a jump in time
DIM1, DIM2 = 17.85, 19.40
T_TITLE = (0.8, 3.0)
T_TOWN = 20.5
T_SAW, T_FALL, T_LAND = 23.0, 23.5, 23.8
T_BREAK, T_FILL = 24.5, 25.0
T_POST, T_RAIL = 26.8, 27.0
T_PAVE0, T_PAVE1 = 27.6, 33.0
T_SINK, T_PAPER, T_END = 34.0, 35.0, 36.0


def lamp_at(t):
    lv = smooth(ramp(t, 0.0, 1.5))
    for c in (DIM1, DIM2):
        lv *= 1 - 0.95 * smooth(clamp(1 - abs(t - c) / 0.34))
    return lv


def lamp_xy(t):
    u = smooth(ramp(t, 0.0, 1.6))
    return (sets.LAMP[0], lerp(300.0, sets.LAMP[1], u))


# ================================================================ poses ===

W_ = cast.with_
STAND = P_['stand']
A_CREST, A_TREE, A_BOG, A_WATER, A_BEND = 6.0, 108.0, 630.0, 940.0, 150.0
A_BOULDER = 360.0
A_BACKED = A_BOULDER - 10.0
BACK_U = 10.0 / S_COW                      # one pace back, in cow units

ST = {k: Stance(FIRST_T, a) for k, a in dict(crest=A_CREST, tree=A_TREE, boulder=A_BOULDER, bog=A_BOG, water=A_WATER).items()}
ST['bend'] = Stance(PATH_T, A_BEND)
ST['watch'] = Stance(PATH_T, 70.0)
ST['end'] = Stance(PATH_T, A_WATER)
ST['crest2'] = Stance(PATH_T, A_CREST)


def tgt(st, wx, wy):
    """A hoof target at a point of the stage, as a pose leg (stand_on() will add the ground back)."""
    ex, ey = (wx - st.x) * st.face, wy - st.y
    lx, ly = (ex * st._c + ey * st._s) / st.sc, (-ex * st._s + ey * st._c) / st.sc
    return ('ik', lx / st.R.kx, ly - st.ground(lx))


ROCK_TOP = (sets.BOULDER[0] - 13.0, sets.BOULDER[1] - 14.5)      # the boulder's near shoulder
ROCK_SIDE = (sets.BOULDER[0] - 23.5, sets.BOULDER[1] - 3.0)      # where the hoof skids to
BOG_IN = (sets.BOG[0] - 7.0, sets.BOG[1] - 2.0)
BOG_DEEP = (sets.BOG[0] - 5.0, sets.BOG[1] + 15.0)
OFF_PT = (ST['bend'].world(96.0, 0.0)[0] + 2.0, ST['bend'].world(96.0, 0.0)[1] - 3.0)   # the open, straight ground

GRAZE = P_['graze']
WANT = W_(P_['look_up'], dx=4.0, neck=-27.0, head=14.0, ear=34.0, eye=1.3)
NOSE_TO = W_(STAND, dx=5.0, neck=-2.0, head=13.0, ear=24.0, eye=1.15)
EAR_TURN = W_(NOSE_TO, ear=-36.0)
LOOK_LOW = W_(STAND, dx=1.0, dy=1.5, pitch=2.5, neck=33.0, head=13.0, ear=30.0, eye=1.25)
B_SEE = W_(STAND, dx=2.0, neck=24.0, head=18.0, ear=28.0, eye=1.2)
B_LIFT = W_(STAND, dx=-7.0, dy=1.0, pitch=-2.5, neck=12.0, head=20.0, ear=18.0, nf=('ik', 70.0, -24.0))
B_ON = W_(STAND, dx=13.0, dy=17.0, pitch=11.0, shoulder=6.0, neck=24.0, head=12.0, ear=30.0, eye=1.2,
          nf=tgt(ST['boulder'], *ROCK_TOP))
B_SLIP = W_(B_ON, dx=20.0, dy=25.0, pitch=17.0, neck=40.0, head=-2.0, ear=48.0, eye=1.9, jaw=7.0,
            tail=(58.0, 30.0, -20.0), nf=tgt(ST['boulder'], *ROCK_SIDE))
B_RECOIL = W_(cast.blend(STAND, P_['startle'], 0.8), eye=1.8)
B_BACKED = ss.shift_pose(W_(STAND, dy=1.0, neck=-4.0, head=16.0, ear=-14.0, eye=1.0), -BACK_U)
B_ROUND = ss.shift_pose(W_(P_['look_up'], neck=-36.0, head=4.0, ear=38.0, eye=1.3), -BACK_U)
B_DEPART = W_(P_['look_up'], neck=-36.0, head=4.0, ear=38.0, eye=1.3)       # the same picture, held from the backed point
G_SINK = W_(STAND, dx=9.0, dy=15.0, pitch=13.0, shoulder=8.0, neck=-20.0, head=-8.0, ear=46.0, eye=1.9, jaw=8.0,
            tail=(60.0, 32.0, -24.0), nf=tgt(ST['bog'], *BOG_DEEP))
G_STUCK = W_(G_SINK, dx=5.0, dy=13.0, neck=-34.0, head=-10.0, jaw=3.0)
G_HAUL = W_(P_['startle'], dx=-20.0, dy=10.0, pitch=-11.0, neck=-60.0, head=-14.0, jaw=10.0, eye=1.9,
            nf=('ik', 76.0, -30.0))
G_OUT = W_(STAND, dx=-8.0, dy=2.0, pitch=-3.0, neck=-34.0, head=2.0, ear=44.0, eye=1.6, nf=('ik', 58.0, 0.0))
DRINK = W_(GRAZE, neck=63.0, head=-20.0, jaw=8.0, ear=-12.0)
DRINK_UP = W_(GRAZE, neck=56.0, head=-14.0, jaw=2.0, ear=-4.0)
N_ALONG = W_(P_['look_up'], dx=3.0, neck=-19.0, head=19.0, ear=36.0, eye=1.3)
N_BACK = W_(N_ALONG, dx=-5.0, dy=1.0, neck=-10.0, head=22.0, nf=('ik', 64.0, -16.0))
N_OFF = W_(STAND, dx=8.0, dy=2.0, pitch=1.0, neck=2.0, head=27.0, ear=32.0, eye=1.2, nf=tgt(ST['bend'], *OFF_PT))
N_JERK = W_(STAND, dx=-7.0, dy=3.0, pitch=-4.5, neck=-44.0, head=-4.0, ear=50.0, eye=1.8, jaw=4.0,
            tail=(40.0, 22.0, -8.0), nf=('ik', 80.0, -27.0))
N_TAKEN = W_(STAND, dy=1.0, neck=-8.0, head=20.0, ear=-30.0, eye=0.85)
N_DOWN = W_(LOOK_LOW, ear=-18.0, eye=0.9)
E_ARRIVE = W_(STAND, neck=6.0, head=16.0, ear=0.0)
E_LOOK = W_(P_['look_up'], dx=3.0, neck=-24.0, head=16.0, ear=36.0, eye=1.3)
WATCH = W_(P_['look_up'], neck=-22.0, head=20.0, ear=38.0, eye=1.35)
FLINCH = W_(cast.blend(STAND, P_['startle'], 0.55), eye=1.8)
H_NOSE = W_(STAND, dx=4.0, neck=4.0, head=16.0, ear=10.0)          # a herd cow at the tree: the same stop, duller
H_EAR = W_(H_NOSE, ear=-34.0)


# ================================================================ the cast and its exposure sheet ===

class Actor:
    """One puppet's level of the sheet: cells of ('walk', t0, t1, a0, a1, r0, r1, opts) and ('act', t0, t1, stance, Act)."""

    def __init__(self, name, kind, cells, phase=0.0, k=1.3, carry=0.0, lift=1.0, weight=1.0, s=S_COW, track=None, prints=False):
        self.name, self.kind, self.cells = name, kind, cells
        self.o = dict(phase=phase, k=k, carry=carry, lift=lift, weight=weight)
        self.s, self.track, self.prints = s, track or PATH_T, prints

    def cell(self, t):
        for i, c in enumerate(self.cells):
            if c[1] <= t < c[2]:
                return i, c
        return None, None

    def _o(self, c):
        o = dict(self.o)
        if c[0] == 'walk' and len(c) > 7:
            o.update(c[7])
        return o

    def arc(self, t):
        i, c = self.cell(t)
        if c is None:
            return None
        return trap(t, c[1], c[2], c[3], c[4], c[5], c[6]) if c[0] == 'walk' else c[3].a

    def state(self, t):
        """(pose, stance, planted) at time t, or None if she is not on the stage."""
        i, c = self.cell(t)
        if c is None:
            return None
        if c[0] == 'act':
            st = c[3]
            return ss.reach_fix(stand_on(c[4].pose(t), st), self.kind), st, {}
        o = self._o(c)
        a = trap(t, c[1], c[2], c[3], c[4], c[5], c[6])
        st = Stance(o.get('track', self.track), a, self.kind, self.s)
        pose, planted = walk_pose(st, o['phase'], o['k'], o['lift'], o['carry'], o['weight'])
        nxt = self.cells[i + 1] if i + 1 < len(self.cells) else None
        prv = self.cells[i - 1] if i > 0 else None
        if nxt and nxt[0] == 'act' and abs(nxt[1] - c[2]) < 1e-6 and c[6] > 0 and t > c[2] - c[6]:
            u = (t - (c[2] - c[6])) / c[6]
            pose = ss.step_blend(pose, stand_on(nxt[4].pose(nxt[1]), st), u, kind=self.kind)
            planted = {}
        elif prv and prv[0] == 'act' and abs(prv[2] - c[1]) < 1e-6 and c[5] > 0 and t < c[1] + c[5]:
            u = (t - c[1]) / c[5]
            p0 = o.get('depart') or prv[4].pose(prv[2])
            pose = ss.step_blend(stand_on(p0, st), pose, u, kind=self.kind)
            planted = {}
        return ss.reach_fix(pose, self.kind), st, planted


def _act(keys, kind='lead'):
    return cast.Act(keys, kind=kind, bell=(kind == 'lead'))


FIRST = dict(track=FIRST_T)
LEAD_CELLS = [
    # 1.2 she aims straight
    ('walk', 3.00, 4.30, -112.0, A_CREST, 0.0, 0.45, dict(FIRST, k=1.0, carry=30.0)),
    ('act', 4.30, 5.25, ST['crest'], _act([(4.30, GRAZE), (4.45, GRAZE), (4.62, WANT, 'snap'), (5.25, WANT)])),
    ('walk', 5.25, 6.95, A_CREST, A_TREE, 0.4, 0.4, dict(FIRST, k=1.15)),
    ('act', 6.95, 7.60, ST['tree'], _act([(6.95, NOSE_TO), (7.20, NOSE_TO), (7.28, EAR_TURN, 'out'), (7.36, EAR_TURN),
                                           (7.50, LOOK_LOW, 'slow'), (7.60, LOOK_LOW)])),
    ('walk', 7.60, 9.90, A_TREE, A_BOULDER, 0.4, 0.45, FIRST),
    # 1.3 two more detours
    ('act', 9.90, 11.35, ST['boulder'], _act([(9.90, B_SEE), (9.98, B_SEE), (10.08, B_LIFT, 'slow'), (10.19, B_ON, 'inout'),
                                               (10.27, B_SLIP, 'out'), (10.33, B_SLIP), (10.50, B_RECOIL, 'out'), (10.66, B_RECOIL),
                                               (10.98, B_BACKED, 'inout'), (11.04, B_BACKED), (11.17, B_ROUND, 'snap'),
                                               (11.35, B_ROUND)])),
    ('walk', 11.35, 13.85, A_BACKED, A_BOG, 0.4, 0.25, dict(FIRST, depart=B_DEPART)),
    ('act', 13.85, 14.40, ST['bog'], _act([(13.85, G_SINK), (13.96, G_STUCK, 'out'), (14.06, G_STUCK), (14.22, G_HAUL, 'slow'),
                                            (14.30, G_HAUL), (14.40, G_OUT)])),
    ('walk', 14.40, 15.45, A_BOG, 776.0, 0.3, 0.0, FIRST),
    ('walk', 15.45, 16.95, 776.0, A_WATER, 0.0, 0.55, FIRST),
    ('act', 16.95, DIM1, ST['water'], _act([(16.95, E_ARRIVE), (17.12, DRINK, 'slow'), (17.30, DRINK), (17.45, DRINK_UP),
                                             (17.60, DRINK), (DIM1, DRINK)])),
    # 1.4 (third return of the lamp) she is at the top again
    ('walk', DIM2, 20.70, -112.0, A_CREST, 0.0, 0.45, dict(k=1.0, carry=30.0)),
    ('act', 20.70, 21.90, ST['crest2'], _act([(20.70, GRAZE), (21.60, GRAZE), (21.90, STAND)])),
    # 1.5 the town, and the tree
    ('walk', 21.90, 23.20, A_CREST, 70.0, 0.4, 0.4, dict(k=1.0, carry=8.0)),
    ('act', 23.20, 24.25, ST['watch'], _act([(23.20, WATCH), (T_LAND, WATCH), (T_LAND + 0.09, FLINCH, 'out'),
                                              (T_LAND + 0.40, FLINCH), (24.25, WATCH)])),
    ('walk', 24.25, 25.50, 70.0, A_BEND, 0.4, 0.45, dict(k=1.0)),
    ('act', 25.50, 27.50, ST['bend'], _act([(25.50, N_ALONG), (26.48, N_ALONG), (26.58, N_BACK, 'slow'), (26.70, N_OFF, 'inout'),
                                             (T_POST + 0.04, N_OFF), (T_POST + 0.16, N_JERK, 'out'), (27.06, N_JERK),
                                             (27.24, N_TAKEN, 'inout'), (27.32, N_TAKEN), (27.44, N_DOWN, 'slow'), (27.50, N_DOWN)])),
    # 1.6 she goes down ahead of the pavers
    ('walk', 27.50, 32.80, A_BEND, A_WATER, 0.45, 0.5, dict(k=1.5)),
    # 1.7 the hold
    ('act', 32.80, 99.0, ST['end'], _act([(32.80, E_ARRIVE), (33.00, E_ARRIVE), (33.25, E_LOOK, 'snap'), (99.0, E_LOOK)])),
]
LEAD = Actor('lead', 'lead', LEAD_CELLS, prints=True)


def _herd_stop(t_arr):
    """A herd cow's halt at the tree: the lead's 14 frames, the lead's ear."""
    st = Stance(PATH_T, A_TREE - 4, 'herd')
    t1 = t_arr + 14 / FPS
    return ('act', t_arr, t1, st, _act([(t_arr, H_NOSE), (t_arr + 0.25, H_NOSE), (t_arr + 0.33, H_EAR, 'out'), (t1, H_EAR)], 'herd'))


def _herd():
    H = dict(track=HERD_T)
    out = []
    v = 100.0
    # first return (14.5 to DIM1): they come over the crest in file, in real time
    out.append(Actor('h1', 'herd', [('walk', 14.50, 16.95, -112.0, A_TREE - 4, 0.0, 0.4, H), _herd_stop(16.95),
                                    ('walk', 16.95 + 14 / FPS, DIM1 + 0.1, A_TREE - 4, A_TREE + 20, 0.4, 0.0, H)],
                     phase=0.37, carry=10.0, prints=True))
    out.append(Actor('h2', 'herd', [('walk', 16.25, DIM1 + 0.1, -112.0, -112.0 + v * (DIM1 + 0.1 - 16.25), 0.0, 0.0, H)],
                     phase=0.81, carry=24.0, weight=1.15, prints=True))
    # second return (DIM1 to DIM2): later; further down; one more stops at the tree
    a, b = DIM1 - 0.1, DIM2 + 0.1
    out.append(Actor('h1', 'herd', [('walk', a, b, 760.0, 760.0 + v * (b - a), 0.0, 0.0, H)], phase=0.37, carry=10.0))
    out.append(Actor('h2', 'herd', [('walk', a, b, 400.0, 400.0 + v * (b - a), 0.0, 0.0, H)], phase=0.81, carry=24.0, weight=1.15))
    out.append(Actor('h3', 'herd', [('walk', a, 18.40, A_TREE - 4 - 42.0, A_TREE - 4, 0.0, 0.4, H), _herd_stop(18.40),
                                    ('walk', 18.40 + 14 / FPS, b, A_TREE - 4, A_TREE + 26, 0.4, 0.0, H)],
                     phase=0.12, carry=3.0, lift=1.25))
    out.append(Actor('h4', 'herd', [('walk', a, b, -150.0, -150.0 + 80.0 * (b - a), 0.0, 0.0, H)], phase=0.58, carry=34.0, s=0.5))
    # third return (DIM2 on): they are all low on the hill; the last of them turns the loop on dry ground
    a = DIM2 - 0.1
    for name, a0, ph, o in (('h1', 1010.0, 0.37, dict(carry=10.0)), ('h2', 890.0, 0.81, dict(carry=24.0, weight=1.15)),
                            ('h3', 742.0, 0.12, dict(carry=3.0, lift=1.25)), ('h4', 596.0, 0.58, dict(carry=34.0, s=0.5))):
        t1 = a + (HERD_T.a1 - a0) / v
        out.append(Actor(name, 'herd', [('walk', a, t1, a0, HERD_T.a1, 0.0, 0.0, H)], phase=ph, **o))
    return out


HERD = _herd()
ACTORS = [LEAD] + HERD


# ---- the prints: every hoof that was put down, where and when

_prints = None


def prints():
    """[(t, x, y, heading)] for every hoof set down on the hill by the lead's first walk and the first herd."""
    global _prints
    if _prints is not None:
        return _prints
    out = []
    for ac in ACTORS:
        if not ac.prints:
            continue
        last, last_syn = {}, None
        for c in ac.cells:
            if c[1] >= DIM1 or c[0] != 'walk':
                continue
            for d in range(int(math.ceil(c[1] * DPS - 1e-6)), int(c[2] * DPS + 1e-6)):
                t = d / DPS
                res = ac.state(t)
                if res is None:
                    continue
                _, st, planted = res
                for leg, (x, y, hd, arc) in planted.items():
                    if 0 <= arc <= A_END and abs(arc - last.get(leg, -1e9)) > 3.0:
                        out.append((t, x, y, hd))
                    last[leg] = arc
                if st.flat >= 0.5 and st.a > 0:                       # in the wheel her feet patter round the turn
                    n = int(st.a / 8.0)
                    if n != last_syn:
                        last_syn = n
                        for da, off in ((-4.0, -1.6), (-12.0, 1.6)):
                            x, y = st.track.at(n * 8.0 + da)
                            hd = st.track.heading(n * 8.0 + da, 6.0)
                            out.append((t, x - off * math.sin(math.radians(hd)), y + off * math.cos(math.radians(hd)), hd))
    _prints = sorted(out)
    return _prints


def wear_at(t):
    """How the tissue is worn at time t: (worn, wear, width, prints)."""
    pr = [(x, y, hd) for (tp, x, y, hd) in prints() if tp <= t + 1e-6]
    if t < 14.5:
        return 0.0, 1.0, 9.0, pr
    if t < DIM1:
        a = None
        for ac in HERD[:1]:
            a = ac.arc(t)
        w = clamp(((a or 0.0) - 30.0) / A_END)
        return w, 0.5, 5.0, pr
    lead_only = [(x, y, hd) for (tp, x, y, hd) in prints() if tp < 14.0]
    if t < DIM2:
        return 1.0, 0.78, 7.0, lead_only
    return 1.0, 1.0, 9.0, lead_only
