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

A_BOULDER = 362.0            # where she stands when she tries the boulder


def _dip(a):                 # her first line bends toward the boulder (she was aiming straight) by 12 px
    return 20.0 * smooth(ramp(a, 268.0, A_BOULDER)) * (1 - smooth(ramp(a, A_BOULDER + 16, A_BOULDER + 96)))


PATH_T = Track(_BACK + sets.PATH, _N_BACK)                        # the canonical path, with the hidden climb
FIRST_T = Track(_BACK + sets.PATH, _N_BACK, dip=_dip)             # the line she walks the first time
HERD_T = Track(_BACK + sets.PATH[:_i_br] + _BANK, _N_BACK)        # the herd's: off along the bank at the bottom
A_END = PATH_T.a1                                                 # 981: the water


# ================================================================ the walker ===

def _tilt(theta):
    """How far the card is leaned for a line heading `theta` degrees: part of the slope; the legs take the rest."""
    return clamp(LEAN * math.degrees(math.asin(math.sin(math.radians(theta)))), -12.0, 12.0)


def _turn(theta):
    """The card turned on its vertical axis: 1 = profile facing right, -1 facing left, between = edge-on."""
    k = clamp(math.cos(math.radians(theta)) / 0.42, -1.0, 1.0)
    if abs(k) < 0.3:
        k = 0.3 if k >= 0 else -0.3
    return k


LEAN = 0.40                  # share of the path's slope taken by leaning the whole card
PITCH = 0.40                 # share of what is left taken by pitching the body; the legs fold for the rest


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
    q['pitch'] = pose.get('pitch', 0.0) + clamp(PITCH * math.degrees(math.atan2(gf - gh, span)), -11.0, 11.0)
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
    pose['pitch'] += clamp(PITCH * math.degrees(math.atan2(gf - gh, span)), -11.0, 11.0)
    if st.a < 30:                                           # coming up the back of the hill the head is carried high
        up = smooth(ramp(-st.a, -30.0, 30.0))
        pose['neck'] = lerp(pose['neck'], -26.0, up)
        pose['head'] = lerp(pose['head'], 8.0, up)
        pose['ear'] = lerp(pose['ear'], 26.0, up)
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
T_PAVE0, T_PAVE1 = 28.4, 33.2
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
A_CREST, A_TREE, A_BOG, A_WATER, A_BEND = 6.0, 114.0, 630.0, 930.0, 108.0
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
ROCK_SIDE = (sets.BOULDER[0] - 24.5, sets.BOULDER[1] - 1.0)      # where the hoof skids to
BOG_IN = (sets.BOG[0] - 7.0, sets.BOG[1] - 2.0)
BOG_DEEP = (sets.BOG[0] - 5.0, sets.BOG[1] + 15.0)
OFF_PT = (ST['bend'].world(96.0, 0.0)[0] + 2.0, ST['bend'].world(96.0, 0.0)[1] - 3.0)   # the open, straight ground

GRAZE = P_['graze']
WANT = W_(P_['look_up'], dx=4.0, neck=-27.0, head=14.0, ear=34.0, eye=1.3)
NOSE_TO = W_(STAND, dx=5.0, neck=30.0, head=-6.0, ear=8.0, eye=1.15)
EAR_TURN = W_(NOSE_TO, ear=-36.0)
LOOK_LOW = W_(STAND, dx=-3.0, dy=1.5, pitch=2.5, neck=46.0, head=20.0, ear=30.0, eye=1.25)
B_SEE = W_(STAND, dx=2.0, neck=24.0, head=18.0, ear=28.0, eye=1.2)
B_LIFT = W_(STAND, dx=-7.0, dy=1.0, pitch=-2.5, neck=12.0, head=20.0, ear=18.0, nf=('ik', 70.0, -24.0))
B_ON = W_(STAND, dx=10.0, dy=9.0, pitch=6.0, shoulder=6.0, neck=14.0, head=22.0, ear=30.0, eye=1.2,
          nf=tgt(ST['boulder'], *ROCK_TOP))
B_SLIP = W_(B_ON, dx=15.0, dy=19.0, pitch=10.0, neck=-12.0, head=2.0, ear=50.0, eye=1.9, jaw=8.0,
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
DRINK = W_(STAND, dx=2.0, dy=3.0, pitch=1.0, shoulder=4.0, neck=62.0, head=-16.0, jaw=8.0, ear=-12.0, tail=(2.0, 4.0, 6.0))
DRINK_UP = W_(DRINK, neck=54.0, head=-10.0, jaw=2.0, ear=-2.0)
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
    ('walk', 3.00, 4.20, -112.0, A_CREST, 0.0, 0.45, dict(FIRST, k=1.0)),
    ('act', 4.20, 5.25, ST['crest'], _act([(4.20, GRAZE), (4.45, GRAZE), (4.62, WANT, 'snap'), (5.25, WANT)])),
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
    ('walk', DIM2, 20.70, -112.0, A_CREST, 0.0, 0.45, dict(k=1.0)),
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
    ('walk', 27.50, 32.60, A_BEND, A_WATER, 0.45, 0.5, dict(k=1.5)),
    # 1.7 the hold
    ('act', 32.60, 99.0, ST['end'], _act([(32.60, E_ARRIVE), (33.00, E_ARRIVE), (33.25, E_LOOK, 'snap'), (99.0, E_LOOK)])),
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
    out.append(Actor('h2', 'herd', [('walk', 16.75, DIM1 + 0.1, -112.0, -112.0 + v * (DIM1 + 0.1 - 16.75), 0.0, 0.0, H)],
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
    for name, a0, ph, o in (('h2', 1075.0, 0.81, dict(carry=24.0, weight=1.15)),
                            ('h3', 905.0, 0.12, dict(carry=3.0, lift=1.25)), ('h4', 612.0, 0.58, dict(carry=34.0, s=0.5))):
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


# ================================================================ the mid plane, and small cut figures ===

def _sheet():
    """A transparent sheet the size of the stage that sets' Card can paste onto."""
    sh = Ink(0.0, 0, (W, H), boil=0)
    sh.img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh.d = ImageDraw.Draw(sh.img, 'RGBA')
    return sh


def _toned(sheet, tone, lamp=1.0):
    """Whatever was cut on the sheet, as card of one tone (a shadow plane)."""
    col = tuple(int(v * (0.3 + 0.7 * lamp)) for v in tone)
    out = Image.new('RGBA', (W, H), col + (0,))
    out.putalpha(sheet.img.getchannel('A'))
    return out


_mid_cache = {}


def mid(key, fn, lamp=1.0):
    k = (key, round(lamp, 2))
    if k not in _mid_cache:
        if len(_mid_cache) > 40:
            _mid_cache.clear()
        sh = _sheet()
        fn(sh)
        _mid_cache[k] = _toned(sh, MID, lamp)
    return _mid_cache[k]


def _clip_over_brow(im, x_from=0):
    """Hide what has gone over the brow of the hill: everything below the sheet's top edge."""
    al = np.asarray(im.getchannel('A')).copy()
    for x in range(max(0, int(x_from)), W):
        al[int(RIDGE_Y(x) + 1):, x] = 0
    im = im.copy()
    im.putalpha(Image.fromarray(al))
    return im


def man(c, x, y, h=30.0, lean=0.0, facing=1, step=None, hands=None, crouch=0.0):
    """A small man of black card, feet at (x, y). lean in degrees (+ = forward), step = walk phase or None,
    hands = two stage points his hands go to. Returns his two shoulders."""
    hipy = y - h * (0.47 - 0.10 * crouch)
    hip = (x, hipy)
    la = math.radians(lean) * facing
    tor = h * (0.36 - 0.04 * crouch)
    neck = (hip[0] + math.sin(la) * tor, hip[1] - math.cos(la) * tor)
    head = (neck[0] + math.sin(la) * h * 0.13 + facing * h * 0.02, neck[1] - math.cos(la) * h * 0.13)
    wd = h * 0.095
    if step is None:
        feet = [(x - h * 0.09, y), (x + h * 0.09, y)]
        lifts = (0.0, 0.0)
    else:
        sw = math.sin(2 * math.pi * step)
        feet = [(x + facing * sw * h * 0.2, y), (x - facing * sw * h * 0.2, y)]
        lifts = (max(0.0, math.cos(2 * math.pi * step)) * h * 0.09, max(0.0, -math.cos(2 * math.pi * step)) * h * 0.09)
    for (fx, fy), lf in zip(feet, lifts):
        knee = ((hip[0] + fx) / 2 + facing * h * (0.05 + 0.08 * crouch), (hip[1] + fy - lf) / 2)
        c.line([hip, knee, (fx, fy - lf)], wd)
        c.line([(fx, fy - lf), (fx + facing * h * 0.07, fy - lf)], wd * 0.8)
    c.line([hip, neck], h * 0.17)
    c.disc(head, h * 0.088)
    c.poly([(head[0] - h * 0.11, head[1] - h * 0.045), (head[0] + h * 0.13 * facing + h * 0.02, head[1] - h * 0.05),
            (head[0] + h * 0.06 * facing, head[1] - h * 0.115), (head[0] - h * 0.08 * facing, head[1] - h * 0.11)])      # a cap
    sh = (neck[0], neck[1] + h * 0.05)
    hands = hands or [(sh[0] + facing * h * 0.05, sh[1] + h * 0.3), (sh[0] - facing * h * 0.04, sh[1] + h * 0.3)]
    for hx, hy in hands:
        mx, my = (sh[0] + hx) / 2, (sh[1] + hy) / 2 + h * 0.05
        c.line([sh, (mx, my), (hx, hy)], h * 0.075)
    return sh


def drum(c, x, y, r, roll, theta):
    """The hand roller: a drum standing on (x, y), its handle trailing back up the path; returns the grip."""
    cx, cy = x, y - r
    c.disc((cx, cy), r)
    a0 = roll / r
    for k in range(3):
        a = a0 + 2 * math.pi * k / 3
        c.hole_disc((cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a)), r * 0.17)
    th = math.radians(theta)
    grip = (cx - 27.0 * math.cos(th), cy - 27.0 * math.sin(th) * 0.55 - 15.0)
    c.line([(cx, cy), grip], 2.0)
    c.line([(grip[0] - 1.0, grip[1] - 5.0), (grip[0] + 1.0, grip[1] + 5.0)], 2.4)
    return grip


# ================================================================ what the town does to the hill (1.5) ===

TREE_PIVOT = (sets.TREE[0] + 11.0, sets.TREE[1] - 22.0)
FENCE_KW = dict(u0=(A_BEND + 62.0) / sets.PATH_LEN, u1=296.0 / sets.PATH_LEN, side=-1, offset=13.0, posts=6)


def tree_state(t):
    """(fall, carry, gone, over) at time t: standing, sawn, falling on 1s, landed, carted over the brow."""
    if t < T_SAW:
        return 0.0, (0.0, 0.0), False, False
    if t < T_FALL:                                         # it shivers with each stroke of the saw
        k = (t - T_SAW) / (T_FALL - T_SAW)
        return 0.004 + 0.006 * abs(math.sin(math.pi * 2 * k)) + 0.012 * k * k, (0.0, 0.0), False, False
    if t < T_LAND:
        u = (t - T_FALL) / (T_LAND - T_FALL)
        return 0.022 + 0.978 * u ** 2.4, (0.0, 0.0), False, False
    if t < T_LAND + 0.25:                                  # it lands, lifts once, lies
        u = (t - T_LAND) / 0.25
        return 1.0 - 0.035 * math.sin(math.pi * u) * (1 - u), (0.0, 0.0), False, False
    if t < 24.10:
        return 1.0, (0.0, 0.0), False, False
    if t < 24.70:                                          # hauled up to the brow, away from the path
        u = smooth((t - 24.10) / 0.60)
        return 1.0, (34.0 * u, -88.0 * u), False, False
    if t < 25.30:                                          # and down the far side
        u = smooth((t - 24.70) / 0.60)
        return 1.0, (34.0 + 22.0 * u, -88.0 + 124.0 * u), False, True
    return 1.0, (0.0, 0.0), True, True


def boulder_state(t):
    if t < T_BREAK:
        return 0.0
    if t < 24.95:
        return clamp((t - T_BREAK) / 0.14) * (1.0 if t < 24.75 else 1.0)
    return None


def bog_fill(t):
    return smooth(ramp(t, T_FILL, T_FILL + 0.4))


def fence_state(t):
    return clamp((t - T_POST) / 0.34), clamp((t - T_RAIL) / 0.3)


def town_grow(t):
    if t < T_TOWN or t < DIM2:
        return None
    g = [clamp((t - (T_TOWN + 0.15 * k)) / 0.62) for k in range(len(sets.TOWN))]
    g.append(clamp((t - 22.25) / 0.75))
    return g


def clearing(ink, t, td):
    """The men of the town: two fell the tree and cart it over the brow, one breaks the boulder and barrows it
    off, one tips a cart into the bog. Drawn in front of the set, behind the cows."""
    if td < 22.2 or td > 25.75:
        return
    c = sets.Card()
    behind = sets.Card()                                    # what is going down the far side of the brow
    tx, ty = sets.TREE
    fall, carry, gone, over = tree_state(t)
    # --- the two sawyers
    if td < T_SAW:                                          # they walk up from the long house below
        u = smooth(ramp(td, 22.2, 22.9))
        for k, (x0, x1) in enumerate(((270.0, tx - 27.0), (300.0, tx + 27.0))):
            x = lerp(x0, x1, clamp(u * 1.15 - 0.15 * k))
            y = lerp(296.0, ty + 3.0, clamp(u * 1.15 - 0.15 * k))
            man(c, x, y, 30, lean=8, facing=1, step=td * 3.2 + 0.5 * k if u < 1 else None)
        if u > 0.5:
            c.line([(tx - 20, ty - 14), (tx + 18, ty - 15)], 1.6)
    elif td < T_FALL:
        s = math.sin(2 * math.pi * (td - T_SAW) / 0.25) * 9.0
        y = ty - 15.0
        man(c, tx - 27, ty + 3, 30, lean=14 + s, facing=1, hands=[(tx - 17 + s, y), (tx - 14 + s, y + 1)], crouch=0.3)
        man(c, tx + 29, ty + 3, 30, lean=14 - s, facing=-1, hands=[(tx + 19 + s, y), (tx + 16 + s, y + 1)], crouch=0.3)
        c.line([(tx - 19 + s, y), (tx + 21 + s, y - 0.5)], 1.6)
    elif td < 24.10:
        u = smooth(ramp(td, T_FALL, T_FALL + 0.2))
        # the one on the fall side gets out from under it; the other shoves, then both stand and look
        man(c, tx - 27 + 4 * u, ty + 3, 30, lean=24 * (1 - smooth(ramp(td, T_LAND, T_LAND + 0.2))), facing=1,
            hands=[(tx - 12, ty - 30), (tx - 12, ty - 22)] if td < T_LAND else None)
        man(c, tx + 29 - 46 * u, ty + 3 + 22 * u, 30, lean=-6, facing=1, step=td * 4 if u < 1 else None)
    elif not gone:
        dx, dy = carry
        tgt_c = behind if over else c
        st_ = td * 3.4
        man(tgt_c, tx + 2 + dx, ty + 4 + dy, 30, lean=26, facing=-1, step=st_, hands=[(tx + 16 + dx, ty - 14 + dy)] * 2)
        man(tgt_c, tx + 150 + dx, ty + 62 + dy, 30, lean=24, facing=-1, step=st_ + 0.5, hands=[(tx + 136 + dx, ty + 40 + dy)] * 2)
    # --- the one at the boulder, with a sledge and a barrow
    bx, by = sets.BOULDER
    if 23.3 <= td < 25.5:
        u_in = smooth(ramp(td, 23.3, 23.9))
        if td < 24.62:
            x, y = lerp(566.0, bx + 36.0, u_in), lerp(250.0, by + 12.0, u_in)
            swing = 0.0
            if td >= 23.9:
                ph = ((td - 23.9) % 0.3) / 0.3                  # blows land at 24.2 and 24.5
                swing = -1.0 + 2.0 * ph ** 3 if td < T_BREAK else 1.0
            ang = math.radians(-105 + 75 * swing) if td >= 23.9 else math.radians(-60)
            hx, hy = x - 9, y - 22
            tipx, tipy = hx - 17 * math.cos(ang) * -1 * -1, hy + 17 * math.sin(ang)
            tipx = hx - 17 * math.cos(ang)
            man(c, x, y, 30, lean=10 + 16 * max(0.0, swing), facing=-1, step=td * 3.4 if u_in < 1 else None,
                hands=[(hx, hy), (hx - 2, hy + 2)])
            c.line([(hx, hy), (tipx, tipy)], 1.6)
            c.poly([(tipx - 3.5, tipy - 2.5), (tipx + 3.5, tipy - 2.5), (tipx + 3.5, tipy + 2.5), (tipx - 3.5, tipy + 2.5)])
            if u_in >= 1 or td > 23.6:
                cart_x, cart_y = lerp(590.0, bx + 62.0, u_in), lerp(256.0, by + 14.0, u_in)
                sets.cart(ink, cart_x, cart_y, 0.5, roll=cart_x, facing=-1)
        else:                                               # the pieces go in the barrow and over the brow
            u = smooth(ramp(td, 24.72, 25.42))
            load = clamp((td - 24.62) / 0.3)
            cx, cy = lerp(bx + 62.0, 566.0, u), lerp(by + 14.0, 262.0, u)
            if RIDGE_Y(cx) < cy - 4:
                sets.cart(ink, cx, cy, 0.5, roll=cx, facing=1, load=load, tilt=-20 * math.sin(math.pi * u))
                man(c, cx - 22, cy + 1, 30, lean=22, facing=1, step=td * 3.4 if u > 0 else None, hands=[(cx - 10, cy - 12)] * 2)
    # --- the cart at the bog
    gx, gy = sets.BOG
    if 24.2 <= td < 25.75:
        u_in = smooth(ramp(td, 24.2, 24.9))
        u_out = smooth(ramp(td, 25.3, 25.72))
        cx = lerp(lerp(704.0, gx - 30.0, u_in), 706.0, u_out)
        cy = lerp(lerp(322.0, gy - 4.0, u_in), 326.0, u_out)
        if RIDGE_Y(cx) < cy - 6 or u_in < 1:
            tip = smooth(ramp(td, T_FILL - 0.1, T_FILL + 0.08)) * (1 - smooth(ramp(td, 25.2, 25.32)))
            sets.cart(ink, cx, cy, 0.62, roll=cy * 2, facing=-1, tip=tip, load=1.0 if td < T_FILL + 0.2 else 0.0)
            man(c, cx - 44, cy + 2, 30, lean=18 if tip < 0.5 else -4, facing=1, step=td * 3.4 if (u_in < 1 or u_out > 0) else None,
                hands=[(cx - 31, cy - 9 - 10 * tip)] * 2)
    c.paste(ink)
    if behind.ops:
        sh = _sheet()
        behind.paste(sh)
        im = _clip_over_brow(sh.img)
        ink.img.paste(im, (0, 0), im)
        ink.d = ImageDraw.Draw(ink.img, 'RGBA')


# ================================================================ the pavers (1.6) ===

GAP_BARROW = 46.0            # the barrow goes this far ahead of the roller, tipping setts onto the cut
A_PAVE_END = 832.0           # where the roller stops: at her heels


def roller_arc(t):
    return trap(t, T_PAVE0 - 0.5, T_PAVE1, -70.0, A_PAVE_END, 0.0, 0.5)


def paved_at(t):
    if t < T_PAVE0 - 0.5:
        return 0.0
    # the roller stops at her heels; the last setts are laid by hand under her
    return clamp(roller_arc(t) / A_END + (1 - A_PAVE_END / A_END) * smooth(ramp(t, T_PAVE1 - 0.1, T_PAVE1 + 0.5)))


def pavers(ink, td):
    if td < T_PAVE0 - 0.5:
        return
    a = roller_arc(td)
    moving = td < T_PAVE1
    c = sets.Card()
    # the roller and the man on its handle: he never turns, so round the loop he goes backwards
    x, y = PATH_T.at(a)
    th = PATH_T.heading(a, 10.0)
    grip = drum(c, x, y, 7.5, a, th)
    mx, my = grip[0] - 7.0, grip[1] + 23.0
    man(c, mx, my, 30, lean=20 if moving else 6, facing=1, step=a / 26.0 if moving else None, hands=[grip, (grip[0] - 1, grip[1] + 2)])
    # the barrow and its man, ahead
    ab = a + GAP_BARROW - 18.0 * smooth(ramp(a, A_PAVE_END - 120.0, A_PAVE_END))
    bx, by = PATH_T.at(ab)
    bth = PATH_T.heading(ab, 14.0)
    bob = abs(math.sin(math.pi * td * 4.0)) if moving else 0.0             # a sett goes down on every beat
    man(c, bx + 4, by + 1, 30, lean=34 + 22 * bob, facing=1 if math.cos(math.radians(bth)) > -0.2 else -1,
        step=ab / 26.0 if moving else None, hands=[(bx + 15, by - 9 + 5 * bob), (bx + 13, by - 8 + 5 * bob)], crouch=0.5)
    sh = _sheet()
    f = 1 if math.cos(math.radians(bth)) > -0.2 else -1
    sets.cart(sh, bx + f * 26, by + 1, 0.5, roll=ab, facing=f, load=clamp(1.2 - a / A_PAVE_END),
              tilt=clamp(math.degrees(math.asin(math.sin(math.radians(bth)))), -24, 24))
    c.paste(sh)
    im = sh.img
    if a < 60:
        im = _clip_behind_hill(im, (0, 0), a - 20)
    ink.img.paste(im, (0, 0), im)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


# ================================================================ the frame ===

_title = None


def title(ink, t, lamp):
    """The four words, cut through the black foot of the hill so the lamp shows through them."""
    global _title
    a = smooth(ramp(t, T_TITLE[0], T_TITLE[0] + 0.5)) * (1 - smooth(ramp(t, T_TITLE[1] - 0.45, T_TITLE[1])))
    if a <= 0:
        return
    if _title is None:
        from kit import font
        f = font('serif', 36)
        im = Image.new('L', (280, 56), 0)
        ImageDraw.Draw(im).text((4, 44), "Don't Pave Cow Paths", font=f, fill=255, anchor='ls')
        _title = im.rotate(-15.5, resample=Image.BICUBIC, expand=True)
    col = tuple(int(v * (0.1 + 0.9 * lamp)) for v in (255, 214, 140))
    m = _title.point(lambda v: int(v * a))
    ink.img.paste(Image.new('RGB', m.size, col), (22, 428), m)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


def _bog_mask(im, xy):
    """What has gone into the bog does not show."""
    x0, y0 = xy
    al = np.asarray(im.getchannel('A')).copy()
    gx, gy = sets.BOG
    for x in range(int(gx - 24), int(gx + 22)):
        cx = x - x0
        if 0 <= cx < im.width:
            ys = int(gy - 3.5 + 0.17 * (x - gx)) - y0
            al[max(ys, 0):, cx] = 0
    im = im.copy()
    im.putalpha(Image.fromarray(al))
    return im


def stage(ink, t):
    """The whole picture at act time t (before the hand-over)."""
    td = q2(t)
    lamp = lamp_at(t)
    worn, wear, width, pr = wear_at(td)
    fall, carry, gone, over = tree_state(t if T_FALL <= t < T_LAND + 0.25 else td)
    bstate = boulder_state(td)
    fill = bog_fill(td)
    paved = paved_at(td)
    sets.hills(ink, td, lamp, lamp_xy(t), worn=worn, wear=wear, worn_width=width, prints=pr, bog=1 - fill)
    sets.water(ink, td, lamp)
    if paved > 0:
        sets.paved_path(ink, paved, 9.0, lamp)
    sets.bog(ink, td, fill=fill)
    g = town_grow(td)
    if g:
        sets.town(ink, td, g, lit=0.75, lamp=lamp)
    # the mid plane: the tree (or what is left of it) and the fence
    if not gone and fall == 0.0:
        im = mid('tree', lambda sh: sets.tree(sh, 0.0, 0.0), lamp)
    elif gone:
        im = mid('stump', lambda sh: sets.stump(sh), lamp)
    else:
        sh = _sheet()
        sets.tree(sh, 0.0, fall, carry=carry)
        im = _toned(sh, MID, lamp)
        if over:
            st_im = mid('stump', lambda s2: sets.stump(s2), lamp)
            sh2 = _sheet()
            sets.tree(sh2, 0.0, fall, carry=carry)
            up = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            up.paste(_toned(sh2, MID, lamp), (0, 0))
            # only the felled part goes over the brow: cut the stump out of it, hide the rest below the edge
            al = np.asarray(up.getchannel('A')).copy()
            al2 = np.asarray(st_im.getchannel('A'))
            if carry == (0.0, 0.0):
                pass
            up = _clip_over_brow(up)
            im = Image.alpha_composite(st_im, up)
    ink.img.paste(im, (0, 0), im)
    post, rail = fence_state(td)
    if post > 0:
        kq = (round(post, 2), round(rail, 2))
        im = mid(('fence',) + kq, lambda sh: sets.fence(sh, post=post, rail=rail, **FENCE_KW), lamp)
        ink.img.paste(im, (0, 0), im)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    if bstate is not None:
        sets.boulder(ink, broken=bstate)
    clearing(ink, t, td)
    # the animals, the far ones first
    cards = []
    for ac in ACTORS:
        res = ac.state(td)
        if res is None:
            continue
        pose, st, _ = res
        im, xy = cut(pose, st)
        im = _clip_behind_hill(im, xy, st.a)
        if ac is LEAD and 13.85 <= td < 14.3:
            im = _bog_mask(im, xy)
        if xy[0] < W and xy[0] + im.width > 0:
            cards.append((st.y, im, xy))
    for _, im, xy in sorted(cards, key=lambda r: r[0]):
        put(ink, im, xy)
    pavers(ink, td)
    sets.stage_front(ink, td)
    title(ink, t, lamp)


def handover_u(t):
    """sets.handover's u: black by 34.5, the path alone on cream by 35.0, a 3 px graphite line at 36.0."""
    if t <= T_SINK:
        return 0.0
    if t <= T_PAPER:
        return 0.86 * (t - T_SINK) / (T_PAPER - T_SINK)
    return min(1.0, 0.86 + 0.14 * (t - T_PAPER) / (T_END - T_PAPER - 1.0 / FPS))


_frame_cache = {}


def draw(t, ink):
    """Draw the full 960x540 frame for act time t onto the kit's Ink."""
    t = clamp(t, 0.0, SECONDS)
    k = int(t * FPS + 1e-6)
    per_frame = t < 1.7 or (T_TITLE[0] <= t <= T_TITLE[1]) or abs(t - DIM1) < 0.4 or abs(t - DIM2) < 0.4 \
        or (T_FALL <= t < T_LAND + 0.3) or t >= T_SINK
    key = ('f', k) if per_frame else ('d', k // ON)
    if _frame_cache.get('key') != key:
        sc = Ink(t, k, (W, H), boil=0)
        stage(sc, t if per_frame else q2(t))
        u = handover_u(t)
        if u > 0:
            sets.handover(sc, u)
        _frame_cache['key'], _frame_cache['img'] = key, sc.img.convert('RGB')
    ink.img.paste(_frame_cache['img'], (0, 0))
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    ink._grain = True
    return ink


# ================================================================ sound ===

D4, E4, FS4, A4, B4, D5 = 293.7, 329.6, 370.0, 440.0, 493.9, 587.3
WANDER = [D4, E4, FS4, E4, D4, E4, FS4, A4, B4, A4, FS4, A4, B4, D5, E4]      # the tune with its three detours


def _pan(x):
    return clamp((x - W / 2) / (W / 2), -0.8, 0.8)


def sound(mix, at=0.0):
    """The act's sound, from the same numbers as the picture. NOBODY HAS HEARD IT: only its levels were measured."""
    mix.wind(at, 35.2, gain=0.035)
    # hooves: every print is a hoof coming down
    for tp, x, y, hd in prints():
        ss.hoof(mix, at + tp, x, 'lead', gain=0.8 if tp < 14.5 else 0.55)
    # her bell: only when her head changes direction
    for tb, x in ((4.60, 130), (7.48, 200), (10.42, 440), (14.24, 690), (17.14, 800), (23.88, 190), (26.94, 220), (33.40, 800)):
        mix.bell(at + tb, freq=740, seconds=0.9, gain=0.2 if tb != 33.40 else 0.24, pan=_pan(x))
    # 1.2: the tune sets off straight up the scale and breaks off at the tree
    for tn, f in ((5.30, D4), (5.72, E4), (6.14, FS4), (6.56, A4)):
        mix.pluck(at + tn, f, seconds=0.9, gain=0.16, pan=-0.5)
    mix.pluck(at + 6.94, FS4, seconds=0.12, gain=0.16, pan=-0.4)                 # cut short: nose to trunk
    for tn, f in ((7.72, E4), (8.14, D4), (8.56, E4), (8.98, FS4), (9.40, A4)):  # the detour: back a note, then on
        mix.pluck(at + tn, f, seconds=0.8, gain=0.15, pan=-0.3)
    # 1.3: slip, bog, the turn at the loop, water
    mix.click(at + 10.21, gain=0.3, pan=_pan(sets.BOULDER[0]), bright=5000)
    for k in range(3):
        ss.hoof(mix, at + 10.72 + 0.09 * k, 440, 'lead', gain=1.0)
    for tn, f in ((11.50, B4), (11.92, A4), (12.34, FS4), (12.76, A4), (13.18, B4)):
        mix.pluck(at + tn, f, seconds=0.8, gain=0.15, pan=0.1)
    mix.thud(at + 13.86, freq=58, gain=0.45, pan=_pan(sets.BOG[0]), seconds=0.4)
    mix.step(at + 14.24, gain=0.3, pan=_pan(sets.BOG[0]), surface='water')
    for tn, f in ((14.62, A4), (14.90, FS4), (15.18, A4)):
        mix.pluck(at + tn, f, seconds=0.7, gain=0.17, pan=0.4)
    for tn, f in ((15.60, B4), (16.02, D5)):
        mix.pluck(at + tn, f, seconds=0.9, gain=0.14, pan=0.5)
    mix.water(at + 16.7, DIM1 - 16.7 + 0.2, gain=0.07)                          # drinking is water only
    # 1.4: the herd; the whole wandering tune, louder each time the lamp returns; a drone under each dark
    for t0, t1, g in ((14.6, 16.6, 0.07), (DIM1 + 0.25, DIM2 - 0.3, 0.11), (DIM2 + 0.25, 20.45, 0.14)):
        n = len(WANDER)
        for k, f in enumerate(WANDER):
            tn = t0 + (t1 - t0) * k / n
            mix.pluck(at + tn, f, seconds=0.6, gain=g, pan=-0.6 + 1.2 * k / n)
    for c in (DIM1, DIM2):
        mix.drone(at + c - 0.5, 1.0, freqs=(73.4, 110.0), gain=0.12, attack=0.4, release=0.4)
    # 1.5: a click for every roof, rising down the row; the saw; the tree; the sledge; the cart
    for k in range(len(sets.TOWN) + 1):
        mix.click(at + T_TOWN + 0.15 * k + 0.5, gain=0.14, pan=_pan(sets.TOWN[min(k, len(sets.TOWN) - 1)]['x']), bright=1800 + 320 * k)
    for tw in (T_SAW + 0.03, T_SAW + 0.28):
        mix.whoosh(at + tw, seconds=0.22, gain=0.16, pan=_pan(sets.TREE[0]))
    mix.thud(at + T_LAND, freq=52, gain=0.95, pan=_pan(420), seconds=0.6)        # the one loud event of the act
    mix.click(at + T_LAND, gain=0.4, pan=_pan(420), bright=2500, seconds=0.08)
    for tb in (24.2, T_BREAK):
        mix.thud(at + tb, freq=150, gain=0.22, pan=_pan(sets.BOULDER[0]), seconds=0.12)
        mix.click(at + tb, gain=0.18, pan=_pan(sets.BOULDER[0]), bright=6000)
    mix.step(at + T_FILL, gain=0.2, pan=_pan(sets.BOG[0]), surface='gravel')
    mix.pluck(at + 26.62, A4, seconds=1.0, gain=0.17, pan=-0.4)                  # the straight scale's next note, once
    mix.click(at + T_POST, gain=0.3, pan=-0.4, bright=1500, seconds=0.04)        # the post; the note is not followed
    mix.click(at + T_RAIL + 0.1, gain=0.18, pan=-0.35, bright=1500, seconds=0.04)
    # 1.6: the same tune, stiff, in strict time, a sett on every beat
    beat = 0.25
    k = 0
    tn = T_PAVE0
    while tn < T_PAVE1 - 0.05:
        a = roller_arc(tn)
        x = PATH_T.at(a)[0]
        f = WANDER[k % len(WANDER)]
        if 640 < a < 776:                                                        # the turn, with full solemnity
            f = (A4, FS4, A4)[k % 3]
        mix.note(at + tn, f, seconds=beat * 0.9, gain=0.07, pan=_pan(x), wave='square', decay=0.1, sustain=0.5)
        mix.step(at + tn, gain=0.12, pan=_pan(x), surface='stone')
        tn += beat
        k += 1
    mix.note(at + T_PAVE1 + 0.1, E4, seconds=0.7, gain=0.07, wave='square', decay=0.2, sustain=0.4)   # ends unresolved on E
    # 35.0 to 36.0 is silent: the wind's own release ends at 35.2


# ================================================================ looking, measuring, rendering ===

def frame(t):
    ink = Ink(t, int(t * FPS + 1e-6), (W, H), boil=0)
    draw(t, ink)
    return ink.finish()


def contact_sheet(path, times, cols=4, scale=0.5, bw=False, crop=None):
    ims = []
    for t in times:
        im = frame(t)
        if bw:
            im = ss.two_tone(im)
        if crop:
            im = im.crop(crop)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 44, 12], fill=(255, 255, 255))
        d.text((2, 0), f'{t:5.2f}', fill=(0, 0, 0))
        ims.append(im)
    w, h = ims[0].size
    sheet = Image.new('RGB', (cols * w, ((len(ims) + cols - 1) // cols) * h), BLACK)
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(path)
    return path


def xsheet():
    out = [f'ACT 1 exposure sheet: {FPS} fps on {ON}s ({DPS} drawings a second), {int(SECONDS * DPS)} drawings; tree fall on 1s']
    for ac in ACTORS:
        for c in ac.cells:
            if c[0] == 'walk':
                out.append(f'{ac.name:5s} d{int(c[1] * DPS):3d}-d{int(min(c[2], SECONDS) * DPS):3d}  walk  arc {c[3]:7.1f} -> {c[4]:7.1f}')
            else:
                out.append(f'{ac.name:5s} d{int(c[1] * DPS):3d}-d{int(min(c[2], SECONDS) * DPS):3d}  act   at arc {c[3].a:6.1f}  keys ' +
                           ' '.join(f'{k[0]:.2f}' for k in c[4].keys))
    return '\n'.join(out)


def check(verbose=True):
    """MEASURED invariants. Returns the numbers; raises if a hard one fails."""
    out = {}
    clamps, drift, n_drift = 0, 0.0, 0
    prev = {}
    for d in range(int(SECONDS * DPS)):
        t = d / DPS
        for ac in ACTORS:
            res = ac.state(t)
            key = (ac.name, id(ac))
            if res is None:
                prev.pop(key, None)
                continue
            pose, st, planted = res
            clamps += 1 if cast.solve(pose, ac.kind)['violations'] else 0
            an = cast.anchors(pose, st.x, st.y, st.s, st.face, st.tilt, ac.kind)['hooves']
            now = {leg: (arc, an[leg]) for leg, (x, y, hd, arc) in planted.items()}
            for leg, (arc, xy) in now.items():
                if key in prev and leg in prev[key] and abs(prev[key][leg][0] - arc) < 0.5:
                    q = prev[key][leg][1]
                    drift = max(drift, math.hypot(xy[0] - q[0], xy[1] - q[1]))
                    n_drift += 1
            prev[key] = now
    out['puppet_drawings_with_a_clamped_joint'] = clamps
    out['planted_hoof_drift_px_max'] = round(drift, 2)
    out['planted_hoof_samples'] = n_drift

    def overlap(t, layer):
        pose, st, _ = LEAD.state(t)
        im, xy = cut(pose, st)
        full = Image.new('L', (W, H), 0)
        full.paste(im.getchannel('A'), xy)
        a = np.asarray(full, np.float32) / 255 * (np.asarray(layer.getchannel('A'), np.float32) / 255)
        return float(a.sum())
    tree = mid('tree', lambda sh: sets.tree(sh, 0.0, 0.0))
    out['lead_over_tree_px_during_wait'] = round(max(overlap(d / DPS, tree) for d in range(int(6.95 * DPS) + 1, int(7.36 * DPS) + 1)), 1)
    fence = mid('fence_full', lambda sh: sets.fence(sh, post=1.0, rail=1.0, **FENCE_KW))
    out['lead_over_fence_px_at_the_bend'] = round(max(overlap(d / DPS, fence) for d in range(int(25.5 * DPS), int(27.5 * DPS))), 1)
    a = [mid('tree', lambda sh: sets.tree(sh, 0.0, 0.0)).tobytes() == tree.tobytes()]
    out['tree_drawing_identical_while_standing'] = all(a)
    ph = sorted(set(round(ac.o['phase'], 2) for ac in HERD))
    out['herd_stride_phases'] = ph
    out['prints'] = len(prints())
    last = None
    mono = True
    for d in range(int(3.0 * DPS), int(DIM1 * DPS)):
        a_ = LEAD.arc(d / DPS)
        if a_ is not None:
            if last is not None and a_ < last - 12.0:
                mono = False
            last = a_
    out['lead_never_goes_back_more_than_one_pace'] = mono
    ink = Ink(SECONDS, int(SECONDS * FPS), (W, H), boil=0)
    draw(SECONDS, ink)
    ref = Ink(0, 0, (W, H), boil=0)
    sets.paper_ground(ref, 0.0)
    sets.pencil(ref, sets.path_stroke(), boil=0, wob=0.0)
    df = np.abs(np.asarray(ink.img.convert('RGB'), np.int16) - np.asarray(ref.img.convert('RGB'), np.int16))
    out['last_frame_vs_paper_plus_path_stroke_max_diff'] = int(df.max())
    assert out['lead_over_tree_px_during_wait'] < 2.0, out
    assert out['tree_drawing_identical_while_standing']
    if verbose:
        for k, v in out.items():
            print(f'  {k}: {v}')
    return out


def build():
    film = Film(SLUG, seconds=SECONDS, boil=0)
    film.poster_at = 26.0
    film.picture(lambda t, ink: draw(t, ink))
    film.sound(lambda mix: sound(mix, 0.0))
    return film


if __name__ == '__main__':
    argv = sys.argv[1:]
    if argv and argv[0] == '--check':
        check()
    elif argv and argv[0] == '--xsheet':
        print(xsheet())
    elif argv and argv[0] == '--still':
        frame(float(argv[2])).save(argv[1])
    elif argv and argv[0] == '--sheet':
        bw = '--bw' in argv
        a = [v for v in argv[1:] if v != '--bw']
        t0, t1 = (float(a[1]), float(a[2])) if len(a) > 2 else (0.0, SECONDS - 0.05)
        n = int(a[3]) if len(a) > 3 else 24
        contact_sheet(a[0], [t0 + (t1 - t0) * i / max(1, n - 1) for i in range(n)], cols=6 if n > 16 else 4, bw=bw)
    else:
        build().render()
