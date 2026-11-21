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
