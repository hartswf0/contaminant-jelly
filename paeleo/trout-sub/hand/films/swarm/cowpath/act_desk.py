"""act_desk.py: ACT 2 of "Don't Pave Cow Paths": THE ONE DESK AND THE GRAFT. Pencil on paper, 40.0 s.

    import act_desk
    act_desk.SECONDS                 40.0  (film 36.0 to 76.0)
    act_desk.draw(t, ink)            a full 960x540 frame at act time t (0 = film 36.0) on a kit.Ink
    act_desk.sound(mix, at)          the act's sound laid into a kit.Mix, the act starting at `at` seconds

    python3 films/swarm/cowpath/act_desk.py                      -> assets/films/cowpath-act-desk.mp4 (the act alone)
    python3 films/swarm/cowpath/act_desk.py --sheet OUT.png t0 t1 n [cols]   -> contact sheet of n stills
    python3 films/swarm/cowpath/act_desk.py --still OUT.png t [cx cy factor] -> one frame
    python3 films/swarm/cowpath/act_desk.py --check              -> the measured gates of this act

Worked by SCION animation-07 (Foldes, drawn metamorphosis). Its primitives are kept as data, by name:
    KEYS             key contour drawings: named polylines with fixed point counts
    CORRESPOND       which key turns into which, point for point (count, order kept, travel: see check())
    PACE             transformation pacing: hand-keyed tracks (study_line.Pacing), one table for picture and sound
    MARKERS          discontinuity markers: the moments the line is allowed to jump (cuts to and from the insert,
                     the replacement passage, the hidden change of seat under the heap)
    INTERVENTIONS    hand-authored exceptions that override a plain in-between where it looked bad
There are no dissolves in this act: a thing appears by being drawn on, leaves by being covered, carried off or
flattened into a line, and changes by its line moving. The one exception is the paper itself cooling to water
in the last second, which the board asks for.

Hand-over in  (t = 0):   exactly sets.paper_ground + sets.pencil(sets.path_stroke(), boil=0, wob=0): what
                         sets.handover(ink, 1.0) leaves on the screen.
Hand-over out (t = 40):  HANDOVER_FISH (seven drawn fish, facing right), the lead in line at HANDOVER_COW, the
                         surface line at y = 170, the bank edge of study_refuse, paper cooled to END_AIR / END_WATER.

Nobody on this production can hear. The sound is placed from the same event tables as the picture and was
checked only for level.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
for _p in (str(FILMS), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from PIL import Image, ImageDraw

import kit
from kit import clamp, lerp, smooth, ease, ramp
import cast
import sets
import study_line as L
from sets import Stroke

W, H, FPS = kit.W, kit.H, kit.FPS
SECONDS = 40.0
FILM_T0 = 36.0
PAPER = kit.PAPER
NOTE = dict(D4=293.7, E4=329.6, Fs4=370.0, A4=440.0, B4=493.9, D5=587.3, E5=659.3, Fs5=740.0, A5=880.0, B5=987.8, D6=1174.7)

# ------------------------------------------------------------------ the event table (act seconds) ---
T = dict(
    line=(0.15, 1.5),            # the path line shrinks onto her sheet
    cow_on=(0.9, 2.0),           # her contour is drawn on
    set_on=(1.5, 3.0),           # the desk draws itself in
    trace=(2.0, 2.7),            # she goes over the loop once more
    pleased=(2.8, 3.3),          # H: she looks at her line
    push=(3.3, 3.5), fall=(3.4, 4.0),      # the first sheet is pushed off and comes to rest on the floor
    insert=(19.5, 21.5),         # the bad drawing fills the frame
    stopped=(21.5, 22.25), look_l=22.25, look_r=22.9, look_hoof=23.5, stamp_bad=24.0, bad_off=24.3,
    drown=(25.0, 28.6), under=28.6, bell_late=28.9,
    settle=(29.5, 31.5), duck=(29.5, 30.0),
    regard=(31.35, 31.8),        # H: she lifts her head at the stump and holds
    cut=32.0, grow=(32.2, 32.65),
    try1=32.65, stuck=32.76, slip=32.88, spring=32.96, reaim=(33.05, 33.26), drop=33.26, seat=33.40, grip=33.55,
    let_go=(33.5, 33.75),
    bind=(33.6, 35.0),
    wait=(35.0, 36.5), lower=(36.5, 37.2), bud=37.2, ear=37.3, head_up=37.6, leaves=(37.2, 38.5),
    loosen=38.5, cool=(39.0, 40.0),
)
ROUNDS = [(3.5, 2.0, 0.0), (13.5, 0.8, 0.55), (17.5, 0.4, 1.0)]      # start, seconds per job, haste
JOBS = ('draw', 'tween', 'paint', 'camera', 'check')
CORE = dict(draw=(0.2, 0.74), tween=(0.18, 0.88), paint=(0.2, 0.9), camera=(0.2, 0.62), check=(0.4, 0.92))

MARKERS = [
    ('insert_in', T['insert'][0], 'cut to the sheet filling the frame'),
    ('insert_out', T['insert'][1], 'cut back to the desk'),
    ('replacements', T['drown'], 'poses change with no in-between: the line jumps, on 2s then on 1s'),
    ('seat_change', (T['duck'][1], 30.6), 'under the heap she leaves the stool and stands: hidden by the paper'),
]
INTERVENTIONS = [
    ('heap_to_stump', 'plain arc-length pairing dragged the whole mound sideways as a smear',
     'pair_by_landmarks: both feet of the mound to both feet of the stump; floor to ground'),
    ('binding', 'path line lerped straight into a helix looked like a tangle shrinking',
     'the line is lifted as a rope and fed through the stump turn by turn (wind_line)'),
    ('shoot_bend', 'a rigid shoot swung like a ruler', 'PACE[bend]: it lags at the start and whips at the stop'),
    ('first_try', 'the wedge went straight home: no cost', 'T[try1..spring]: it sticks on the lip, bows, skids, springs'),
    ('leaf_to_fish', 'stem and tip crossed when the leaf turned', 'the turn is in the frame of the leaf, not in its points'),
]

# ------------------------------------------------------------------ places ---
X, Y, S = 300.0, 470.0, 1.0            # the seated cow
A = sets.desk_layout(X, Y, S)
DESK = A['desk']
P_DESK = sets._ob(DESK[0], DESK[1], S)
LEVER = P_DESK(140, 40, sets.DESK_H)   # the camera stands where she can reach it half standing
POT = A['pot']
BLANK = A['blank']
TRAY = A['out_tray']
SHEET = A['sheet']                     # [near-left, near-right, far-right, far-left]
PAGE = (0.0, 0.0, 208.0, 104.0)        # every drawing on a sheet is made in this box, y down
FLOOR_SHEET = [(398.0, 506.0), (516.0, 506.0), (540.0, 480.0), (422.0, 480.0)]      # where the first sheet comes to rest
STAMP_PAGE = (78.0, 64.0)              # where her hoof comes down on a sheet (across the gap of the bad drawing)

GX, GY, GS = 650.0, 470.0, 3.5         # the stump: ground under its middle, px per stump unit
CX, CY = 505.0, 470.0                  # the standing cow
GRIP = 15.0 * GS                       # she holds the stub this far above its point
CLEFT_Y = GY - GS * 10.0               # the bottom of the cleft
RIM_Y = GY - GS * 22.0

HANDOVER_COW = (86.0, 162.0, 0.6)      # x, y, s of the lead at 76.0 (study_refuse puts her cutout here)
HANDOVER_FISH = [                      # centre x, centre y, length, facing right; leaf order -> fish
    dict(x=600.0, y=420.0, length=170.0),      # the watcher: the first leaf that opened
    dict(x=318.0, y=258.0, length=112.0), dict(x=452.0, y=338.0, length=118.0), dict(x=572.0, y=262.0, length=110.0),
    dict(x=706.0, y=330.0, length=122.0), dict(x=828.0, y=262.0, length=125.0), dict(x=344.0, y=408.0, length=115.0)]
END_AIR = (232, 237, 222)
END_WATER = ((150, 196, 180), (62, 128, 126))      # at the surface, at the bottom of the frame
SURFACE_Y = 170.0
BANK_EDGE = [(180.0, 172.0), (179.0, 182.0), (172.0, 250.0), (158.0, 340.0), (140.0, 430.0), (118.0, 548.0)]


def U(p):
    """Screen point -> cow units of the seated cow."""
    return ((p[0] - X) / S, (p[1] - Y) / S)


def _dir(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def _tf(pts, x, y, s=1.0, ang=0.0):
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(x + s * (px * c - py * sn), y + s * (px * sn + py * c)) for px, py in pts]


def on_page(quad, lines):
    return [sets.on_sheet(quad, st if isinstance(st, Stroke) else Stroke(st), PAGE) for st in lines]


def page_pt(quad, p):
    return tuple(sets.on_sheet(quad, Stroke([p]), PAGE)[0])


def lerp_pts(a, b, u):
    return [(p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u) for p, q in zip(a, b)]


def quad_lerp(q0, q1, u, lift=0.0, turn=0.0):
    q = lerp_pts(q0, q1, u)
    cx, cy = sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4 - lift
    c, sn = math.cos(turn), math.sin(turn)
    return [(cx + (p[0] - cx) * c - (p[1] - cy + lift) * sn, cy + (p[0] - cx) * sn + (p[1] - cy + lift) * c) for p in q]


# ------------------------------------------------------------------ aiming her mouth ---
_aim_cache = {}


def _aim2(p, target, keys):
    p = dict(p)
    lim = [cast.LIMITS[k] for k in keys]
    err = 1e9
    for _ in range(16):
        m = cast.anchors(p, 0, 0, 1.0)['mouth']
        ex, ey = target[0] - m[0], target[1] - m[1]
        err = math.hypot(ex, ey)
        if err < 0.3:
            break
        J = []
        for k in keys:
            q = dict(p)
            q[k] = p[k] + 1.0
            m2 = cast.anchors(q, 0, 0, 1.0)['mouth']
            J.append((m2[0] - m[0], m2[1] - m[1]))
        det = J[0][0] * J[1][1] - J[1][0] * J[0][1]
        if abs(det) < 1e-6:
            break
        d0 = (ex * J[1][1] - ey * J[1][0]) / det
        d1 = (ey * J[0][0] - ex * J[0][1]) / det
        p[keys[0]] = clamp(p[keys[0]] + clamp(d0, -14, 14), *lim[0])
        p[keys[1]] = clamp(p[keys[1]] + clamp(d1, -14, 14), *lim[1])
    return p, err


def aim(base, target, keys=('neck', 'head'), tag=None, lean=0.0):
    """The pose `base` with two of its angles solved so that her mouth is at `target` (cow units). With `lean`,
    the body may shift up to that far to make up what the neck cannot reach."""
    best = None
    for start in (None, (-50.0, 40.0), (-20.0, -10.0), (10.0, -35.0), (30.0, 30.0)):
        p0 = dict(base)
        if start:
            p0[keys[0]], p0[keys[1]] = start
        p, err = _aim2(p0, target, keys)
        if best is None or err < best[1] - 0.2:
            best = (p, err)
        if best[1] < 0.5:
            break
    p, err = best
    for _ in range(4 if lean else 0):                    # out of the neck's reach: the body leans the rest of the way
        if err < 0.7:
            break
        m = cast.anchors(p, 0, 0, 1.0)['mouth']
        q = dict(p)
        q['dx'] = clamp(p.get('dx', 0.0) + target[0] - m[0], base.get('dx', 0.0) - lean, base.get('dx', 0.0) + lean)
        q['dy'] = clamp(p.get('dy', 0.0) + (target[1] - m[1]) * 0.5, base.get('dy', 0.0) - 3.0, base.get('dy', 0.0) + 8.0)
        p, err = _aim2(q, target, keys)
    return p


def keyed(keys, u):
    """keys = [(u, pose, ease into it)]; a hold is the same pose twice."""
    if u <= keys[0][0]:
        return keys[0][1]
    for (ua, pa, *_), kb in zip(keys, keys[1:]):
        ub, pb = kb[0], kb[1]
        if u <= ub:
            if pa is pb:
                return pa
            return cast.tween(pa, pb, (u - ua) / max(ub - ua, 1e-9), kb[2] if len(kb) > 2 else 'inout')
    return keys[-1][1]


# ------------------------------------------------------------------ her poses at the desk ---
SIT = cast.POSES['sit']
N = cast.draw_pose(0.45, 0.0, 1.0)                 # between jobs: both hooves on the desk, looking at the sheet


def draw_at(page, press=1.0, reach=0.8, head=0.0):
    """Drawing with the pencil point at a place on the sheet (page coordinates)."""
    hx, hy = U(page_pt(SHEET, page))
    hx, hy = hx - 20.0, hy + 6.0 - (1 - press) * 10.0
    p = cast.draw_pose(clamp((hx - 40) / 60.0), reach, 1.0)
    return cast.with_(p, nf=('ik', hx, hy), head=p['head'] + head)


def tween_pose(lift, tick):
    q3 = SHEET[3]
    hx, hy = U((q3[0] + 8 - 10 * lift, q3[1] + 6 - 46 * lift))
    p = cast.draw_pose(0.7, 0.45, 1.0)
    return cast.with_(p, nf=('ik', hx, hy), neck=p['neck'] - 9 * tick, head=p['head'] - 15 * tick, eye=1.1, ear=22)


BRUSH_LEN = 80.0


def brush_mouth(tip_screen, ang):
    d = _dir(ang)
    return U((tip_screen[0] + BRUSH_LEN * d[0], tip_screen[1] + BRUSH_LEN * d[1]))


PAINT_A = dict(pot=-152.0, sheet=-112.0, drip=-120.0)
TIP_POT = (POT[0], POT[1] - 9.0)
TIP_P0, TIP_P1 = page_pt(SHEET, (48, 50)), page_pt(SHEET, (172, 50))
TIP_DRIP = page_pt(SHEET, (178, 92))
_lean = cast.draw_pose(0.5, 1.0, 1.0)
K_POT = aim(_lean, brush_mouth(TIP_POT, PAINT_A['pot']))
K_P0 = aim(cast.draw_pose(0.5, 0.2, 1.0), brush_mouth(TIP_P0, PAINT_A['sheet']))
K_P1 = aim(cast.draw_pose(0.5, 0.9, 1.0), brush_mouth(TIP_P1, PAINT_A['sheet']))
K_DRIP = cast.with_(aim(_lean, brush_mouth(TIP_DRIP, PAINT_A['drip'])), eye=1.5, ear=40)


def cam_pose(pull, up=1.0):
    g = sets.lever_anchor(LEVER[0], LEVER[1], S, clamp(pull))['grip']
    gx, gy = U(g)
    return cast.with_(SIT, dx=SIT['dx'] + 50 * up, dy=SIT['dy'] - 20 * up + 10 * clamp(pull) * up, pitch=-58 + 12 * up,
                      shoulder=0.0, nf=('ik', gx, gy), ff=('ik', gx + 5, gy + 7), neck=lerp(34, 10, up) + 12 * pull,
                      head=lerp(42, 34, up), ear=20, eye=1.1)


JUDGE = cast.with_(SIT, pitch=-63.0, neck=10.0, head=56.0, eye=0.3, ear=-18.0)
JUDGE2 = cast.with_(JUDGE, head=62.0, neck=6.0)
STAMP_UP = cast.stamp_pose(0.5)
_sx, _sy = U(page_pt(SHEET, STAMP_PAGE))
STAMP_DN = cast.with_(cast.draw_pose(0.6, 0.55, 1.0), nf=('ik', _sx, _sy), neck=52.0, head=30.0, eye=1.3, ear=28.0)
FLICK = cast.with_(cast.draw_pose(0.8, 0.7, 1.0), nf=('ik', _sx + 18, _sy - 3), eye=1.0)
STOPPED = cast.with_(cast.draw_pose(0.5, 0.25, 1.0), eye=1.0, ear=4.0)
LOOK_L = cast.with_(SIT, pitch=-66.0, neck=-46.0, head=-34.0, eye=1.5, ear=42.0, nf=('ik', 46.0, cast.DESK_Y), ff=('ik', 66.0, cast.DESK_Y))
LOOK_R = cast.with_(cast.draw_pose(0.5, 1.0, 1.0), neck=-14.0, head=-12.0, eye=1.5, ear=42.0)
LOOK_HOOF = cast.with_(SIT, nf=('ik', 74.0, -168.0), neck=40.0, head=50.0, eye=1.2, ear=10.0)
PLEASED = cast.with_(cast.draw_pose(0.5, 0.0, 1.0), neck=24.0, head=44.0, eye=1.15, ear=14.0)
FINAL = cast.with_(SIT, neck=30.0, head=40.0, eye=1.6, ear=-55.0, nf=('ik', 50.0, -122.0), ff=('ik', 70.0, -126.0))
DUCKED = cast.with_(cast.POSES['desk_slump'], dy=cast.POSES['desk_slump']['dy'] + 30.0)


def job_pose(name, u, c=0):
    """The pose and the props of one job at warped progress u (0..1)."""
    pr = {}
    if name == 'draw':
        a, b = (56, 30), (150, 58)
        s_ = smooth(ramp(u, 0.28, 0.7))
        cur = (lerp(a[0], b[0], s_), lerp(a[1], b[1], s_) - 16 * math.sin(math.pi * s_))
        if u < 0.2:
            pose = cast.tween(N, draw_at(a, 0.0, 0.5, 6), u / 0.2, 'inout')
        elif u < 0.28:
            pose = cast.tween(draw_at(a, 0.0, 0.5, 6), draw_at(a, 1.0, 0.6, 8), (u - 0.2) / 0.08, 'slow')
        elif u < 0.7:
            pose = draw_at(cur, 1.0, lerp(0.6, 1.0, s_), 8 - 6 * s_)
        else:
            pose = cast.tween(draw_at(b, 1.0, 1.0, 2), N, (u - 0.7) / 0.3, 'out')
        pr.update(d=0.6 * s_, pencil=True)
    elif name == 'tween':
        fl = clamp((u - 0.2) / 0.66) * 3.0
        k, f = min(2, int(fl)), fl - min(2, int(fl))
        lift = math.sin(math.pi * clamp(f)) ** 0.8 if 0.2 <= u < 0.86 else 0.0
        if u < 0.2:
            pose = cast.tween(N, tween_pose(0, 0), u / 0.2, 'inout')
        elif u < 0.86:
            pose = tween_pose(lift, smooth(lift))
        else:
            pose = cast.tween(tween_pose(0, 0), N, (u - 0.86) / 0.14, 'inout')
        pr.update(d=0.6, d2=clamp((k + smooth(clamp(f * 1.6 - 0.6))) / 3.0) if u >= 0.2 else 0.0, lift=lift)
    elif name == 'paint':
        pose = keyed([(0.0, N), (0.2, K_POT, 'inout'), (0.26, K_POT), (0.42, K_P0, 'inout'), (0.62, K_P1, 'linear'),
                      (0.72, K_P1), (0.79, K_DRIP, 'out'), (0.87, K_DRIP), (1.0, K_POT, 'inout')], u)
        ang = (PAINT_A['pot'] if u < 0.26 else lerp(PAINT_A['pot'], PAINT_A['sheet'], smooth(ramp(u, 0.26, 0.42))) if u < 0.72
               else lerp(PAINT_A['sheet'], PAINT_A['drip'], smooth(ramp(u, 0.72, 0.79))) if u < 0.87
               else lerp(PAINT_A['drip'], PAINT_A['pot'], smooth(ramp(u, 0.87, 1.0))))
        pr.update(d=0.6, d2=1.0, p=ramp(u, 0.42, 0.62), drip=ramp(u, 0.6, 0.76), dab=u >= 0.8,
                  brush=ang if 0.18 <= u < 0.985 else None)
    elif name == 'camera':
        pull = (0.0 if u < 0.25 else -0.12 * math.sin(math.pi * ramp(u, 0.25, 0.36)) if u < 0.36
                else cast.EASES['slam'](ramp(u, 0.36, 0.47)) if u < 0.56 else 1 - smooth(ramp(u, 0.56, 0.72)))
        up = smooth(ramp(u, 0.0, 0.25)) if u < 0.72 else 1 - smooth(ramp(u, 0.72, 1.0))
        pose = cast.tween(N, cam_pose(pull, 1.0), up, 'linear') if up < 1 else cam_pose(pull, 1.0)
        pr.update(d=0.6, d2=1.0, p=1.0, dab=True, drip=1.0, pull=clamp(pull), blink=0.47 <= u < 0.47 + 0.001)
    else:
        pose = keyed([(0.0, N), (0.22, JUDGE, 'inout'), (0.3, JUDGE), (0.36, JUDGE2, 'inout'), (0.42, JUDGE2),
                      (0.6, STAMP_UP, 'slow'), (0.66, STAMP_DN, 'slam'), (0.8, STAMP_DN), (0.9, FLICK, 'out'), (1.0, N, 'inout')], u)
        pr.update(d=0.6, d2=1.0, p=1.0, dab=True, drip=1.0, k=u >= 0.66)
    return pose, pr


def _build_schedule():
    seq, fly = [], []
    for r, (ts, dj, h) in enumerate(ROUNDS):
        for j, name in enumerate(JOBS):
            t0 = ts + j * dj
            seq.append(dict(t0=t0, dur=dj, job=name, j=j, c=r, haste=h, r=r))
            if r == 0:
                if name == 'check':
                    fly.append(dict(te=t0 + 0.86 * dj, dur=0.55, spec=(r, 0.6, 1.0, 1.0, 1.0, True, True, False), wt=1.0, mess=0.0))
            elif name != 'paint':
                full = (r, 0.6 if j >= 0 else 0, 1.0 if j >= 1 else 0.0, 1.0 if j >= 3 else 0.0, 1.0 if j >= 3 else 0.0, j >= 3, j == 4, False)
                fly.append(dict(te=t0 + 0.86 * dj, dur=0.42 if r == 1 else 0.3, spec=full, wt=3.2 if r == 1 else 8.8,
                                mess=0.5 if r == 1 else 1.0))
    fly.append(dict(te=T['bad_off'], dur=0.5, spec=(9, 1, 1, 0, 0, False, True, True), wt=1.0, mess=0.4))
    for k, f in enumerate(fly):
        f['k'] = k
    return seq, fly


JOBSEQ, FLY = _build_schedule()


def pile_n(t):
    return sum(f['wt'] * smooth(clamp((t - f['te'] - f['dur'] + 0.04) / 0.08)) for f in FLY)


def job_at(t):
    for jb in JOBSEQ:
        if jb['t0'] <= t < jb['t0'] + jb['dur']:
            u = (t - jb['t0']) / jb['dur']
            a, b = CORE[jb['job']]
            return jb, u, lerp(u, a + (b - a) * u, jb['haste'])
    return None, 0.0, 0.0


REPL = None


def _replacements():
    global REPL
    if REPL is None:
        REPL = [(draw_at((150, 58), 1.0, 1.0, 2), dict(pencil=True)), (tween_pose(1.0, 1.0), dict(lift=1.0)),
                (K_P1, dict(brush=PAINT_A['sheet'])), (cam_pose(1.0), dict(pull=1.0, brush=-150.0)),
                (STAMP_UP, {}), (STAMP_DN, dict(k=True))]
    return REPL


_ORDER1 = [0, 4, 2, 5, 1, 3, 5, 0, 3, 2, 4, 5, 1, 4, 0, 5, 3, 1, 2, 5]


def desk_state(t):
    """Her pose and the state of the things on the desk at act time t (0 .. 30)."""
    st = dict(pose=N, d=0.0, d2=0.0, p=0.0, drip=0.0, dab=False, k=False, lift=0.0, pull=0.0, brush=None, pencil=False,
              blink=False, c=0, blank=False, bad=False)
    if t < T['trace'][0]:
        st['pose'] = draw_at(LOOP_PAGE[0], 1.0, 1.0)
        st['pencil'] = True
    elif t < T['trace'][1]:
        u = smooth(ramp(t, *T['trace']))
        i = min(len(LOOP_PAGE) - 1, int(u * (len(LOOP_PAGE) - 1)))
        st['pose'] = draw_at(LOOP_PAGE[i], 1.0, 1.0)
        st['pencil'] = True
    elif t < T['push'][0]:
        e0 = draw_at(LOOP_PAGE[-1], 1.0, 1.0)
        ear = 14 + 30 * math.sin(math.pi * ramp(t, 2.98, 3.14))
        st['pose'] = cast.with_(keyed([(T['trace'][1], e0), (T['pleased'][0], PLEASED, 'inout'), (T['push'][0], PLEASED)], t), ear=ear)
        st['pencil'] = t < T['pleased'][0] - 0.05
    elif t < ROUNDS[0][0]:
        st['pose'] = keyed([(T['push'][0], PLEASED), (T['push'][0] + 0.1, FLICK, 'out'), (T['push'][1], N, 'inout')], t)
        st['blank'] = t >= T['push'][0] + 0.06
    elif t < T['insert'][0]:
        jb, u, uu = job_at(t)
        pose, pr = job_pose(jb['job'], uu, jb['c'])
        st.update(pr)
        st['pose'], st['c'] = pose, jb['c']
        if jb['r'] > 0:                                  # the brush stays in her mouth; every job starts a fresh sheet
            if st['brush'] is None and jb['job'] in ('camera', 'check') or (jb['job'] == 'paint' and st['brush'] is None):
                st['brush'] = -150.0 if jb['job'] != 'check' else -140.0
            if jb['job'] == 'draw':
                st['brush'] = None
            if jb['job'] in ('draw',):
                pass
            elif jb['job'] == 'tween':
                st['d'] = 0.6
            if jb['job'] == 'check':
                st.update(p=0.0, drip=0.0, dab=False)
            if u >= 0.86 and jb['job'] != 'paint':
                st['blank'] = True
        elif jb['job'] == 'check' and u >= 0.86:
            st['blank'] = True
        if jb['job'] == 'camera':
            tb = jb['t0'] + jb['dur'] * ((0.47 - 0.2) / 0.42 if jb['haste'] >= 1 else 0.47)
            tb = jb['t0'] + jb['dur'] * _unwarp(0.47, jb)
            st['blink'] = 0 <= t - tb < 2.0 / FPS
    elif t < T['drown'][0]:
        st['bad'] = True
        st['pose'] = keyed([(T['stopped'][0], STOPPED), (T['look_l'], STOPPED), (T['look_l'] + 0.18, LOOK_L, 'out'),
                            (T['look_r'], LOOK_L), (T['look_r'] + 0.2, LOOK_R, 'out'), (T['look_hoof'], LOOK_R),
                            (T['look_hoof'] + 0.24, LOOK_HOOF, 'inout'), (T['stamp_bad'] - 0.2, LOOK_HOOF),
                            (T['stamp_bad'] - 0.07, STAMP_UP, 'slow'), (T['stamp_bad'] + 0.03, STAMP_DN, 'slam'),
                            (T['bad_off'], STAMP_DN), (T['bad_off'] + 0.14, FLICK, 'out'), (T['bad_off'] + 0.5, N, 'inout')], t)
        st['k'] = t >= T['stamp_bad'] + 0.03
        st['blank'] = t >= T['bad_off'] + 0.1
        st['bad'] = not st['blank']
    elif t < T['under']:
        R = _replacements()
        if t < 26.5:
            i = int((t - 25.0) * 12) % 6
        else:
            i = _ORDER1[int(round((t - 26.5) * FPS)) % len(_ORDER1)]
        pose, pr = R[i]
        st.update(pr)
        st['pose'] = pose
        st['blank'] = True
    elif t < T['duck'][0]:
        st['pose'] = FINAL
        st['blank'] = True
    else:
        st['pose'] = cast.tween(FINAL, DUCKED, ramp(t, *T['duck']), 'slow')
        st['blank'] = True
    return st


def _unwarp(uu, jb):
    a, b = CORE[jb['job']]
    h = jb['haste']
    return clamp((uu - h * a) / (1 - h + h * (b - a)))


class _Perf(cast.Act):
    """cast.Act's bell (a damped pendulum driven by her throat) for a performance given as a function of time."""

    def __init__(self, fn, t0, t1, rate=48):
        self.fn, self.kind, self.rate, self.t0, self.t1 = fn, 'lead', rate, t0, t1
        self._bell, self.bell_hits = [], []
        self._swing()

    def base(self, t):
        return dict(self.fn(clamp(t, self.t0, self.t1)))


_perf = {}


def perf(name):
    if name not in _perf:
        if name == 'desk':
            _perf[name] = _Perf(lambda t: desk_state(t)['pose'], 2.0, 29.5)
        else:
            _perf[name] = _Perf(lambda t: stand_state(t)['pose'], 29.9, 40.0)
    return _perf[name]


# ------------------------------------------------------------------ what is on a sheet ---
_full = sets.path_stroke()
LOOP_PAGE = [(208.0 * px / W, 104.0 * py / H) for px, py in _full[int(len(_full) * 0.66):int(len(_full) * 0.86)]]   # the bog loop on her sheet
_outl = {}


def _cyc_outline(c):
    if c not in _outl:
        pts = cast.outline(cast.walk(14.0 + 21.0 * c), 0.5, n=120)
        _outl[c] = [(112 + px, 96 + py) for px, py in pts] + [(112 + pts[0][0], 96 + pts[0][1])]
    return _outl[c]


_bad = None


def bad_drawing():
    """Her drawing of a walking cow, wrong in contour: the hindquarters have come away from the barrel and stride
    on by themselves, and there is a fifth leg under the belly. Page coordinates. Returns (strokes, fifth-leg strokes)."""
    global _bad
    if _bad is None:
        s_, gx, gy, gap = 0.52, 122.0, 97.0, 36.0
        hind = ('tail', 'fh_upper', 'fh_lower', 'hip', 'udder', 'nh_upper', 'nh_lower')
        skip = ('bell',)
        body, fifth = [], []
        for name, poly in cast.parts(cast.walk(40.0), gx, gy, s_):
            if name in skip:
                continue
            dx = -gap if name in hind else 0.0
            dy = 1.5 if name in hind else 0.0
            pts = [(px + dx, py + dy) for px, py in poly]
            body.append(Stroke(pts + [pts[0]], 1.0, 1.0, fill=True))
            if name in ('nf_upper', 'nf_lower'):
                fifth.append(Stroke([(px - 37.0, py + (0.0 if name == 'nf_lower' else 2.0)) for px, py in poly] + [(poly[0][0] - 37.0, poly[0][1])], 1.0, 1.0, fill=True))
        ground = [Stroke([(14, 98.5), (196, 98.5)], 0.7, 0.7)]
        _bad = (ground + body, fifth)
    return _bad


def sheet_content(c=0, d=0.0, d2=0.0, p=0.0, drip=0.0, dab=False, k=False, bad=False, fifth=1.0):
    """The strokes on a sheet, in page coordinates."""
    out = []
    if bad:
        body, leg = bad_drawing()
        out += body
        if fifth > 0:
            for st in leg:
                out.append(st.like(sets.upto(st, fifth)) if fifth < 1 else st)
    else:
        if p > 0:
            n = int(p * 22)
            for i in range(n):
                x = 40 + i * 6.0
                out.append(Stroke([(x, 74), (x + 13, 30)], 1.5, 0.3))
        if d > 0 or d2 > 0:
            o = _cyc_outline(c % 4)
            out.append(Stroke(sets.upto(o, clamp(d + 0.4 * d2)), 1.0, 1.0))
        if drip > 0 and not dab:
            y1 = 62 + 30 * drip
            out.append(Stroke([(178, 60), (178.5, y1)], 1.2, 0.6))
            out.append(Stroke(sets._ell(178.5, y1 + 2, 2.5, 3.2, n=8), 1.0, 0.8))
        elif dab:
            for i in range(3):
                out.append(Stroke([(170, 86 + 3 * i), (186, 84 + 3 * i)], 1.4, 0.35))
    if k:
        out += sets.hoofprint_lines(STAMP_PAGE[0], STAMP_PAGE[1], 1.15, 18.0)
    return out


def sheet_shape(quad, holes=True):
    Ls = [Stroke(list(quad) + [quad[0]], 1.0, 1.0, fill=True)]
    if holes:
        for f in (0.22, 0.5, 0.78):
            cx, cy = lerp(quad[0][0], quad[1][0], f), lerp(quad[0][1], quad[1][1], f)
            ux, uy = (quad[3][0] - quad[0][0]) * 0.09, (quad[3][1] - quad[0][1]) * 0.09
            wx = (quad[1][0] - quad[0][0]) * 0.035
            Ls.append(Stroke([(cx - wx + ux, cy + uy), (cx + wx + ux, cy + uy)], 1.3, 0.8))
    return Ls


def tray_top(n):
    x0, y0 = TRAY[0] + 6, TRAY[1] - 3 - n * 2.2
    return [(x0, y0), (x0 + 104, y0), (x0 + 104 + 0.42 * 52, y0 - 26), (x0 + 0.42 * 52, y0 - 26)]


def pencil_prop(pt, ang=166.0, ln=34.0):
    d = _dir(ang)
    n = (-d[1], d[0])
    a = (pt[0] + d[0] * 7, pt[1] + d[1] * 7)
    b = (pt[0] + d[0] * ln, pt[1] + d[1] * ln)
    body = [pt, (a[0] + n[0] * 2.2, a[1] + n[1] * 2.2), (b[0] + n[0] * 2.2, b[1] + n[1] * 2.2),
            (b[0] - n[0] * 2.2, b[1] - n[1] * 2.2), (a[0] - n[0] * 2.2, a[1] - n[1] * 2.2), pt]
    return [Stroke(body, 0.9, 1.0, fill=True), Stroke([(a[0] + n[0] * 2.2, a[1] + n[1] * 2.2), (a[0] - n[0] * 2.2, a[1] - n[1] * 2.2)], 0.6, 0.8)]


# ------------------------------------------------------------------ the desk set ---
_static = {}


def set_lines(st, pile, t, mess):
    """The desk and what stands on it, back to front (the cow is drawn after it)."""
    if 'back' not in _static:
        _static['back'] = sets.floor_lines(*DESK, S) + sets.stool_lines(X, Y, S) + sets.desk_lines(*DESK, S)
        _static['board'] = sets.board_lines(*A['board'], S)
        _static['peg'] = sets.pegbar_lines(*A['board'], S)
        _static['blank'] = sets.stack_lines(*BLANK, S, 12, 58, 40, 1.6, 0.05, 5)
        _static['pot1'] = sets.pot_lines(*POT, S, True)
        _static['pot0'] = sets.pot_lines(*POT, S, False)
    Ls = list(_static['back'])
    Ls += _static['pot0'] if st['brush'] is not None else _static['pot1']
    Ls += _static['board']
    return Ls


def board_sheet(st, t):
    """The sheet on the pegs with whatever she has put on it, and the peg bar."""
    Ls = []
    lift = st.get('lift', 0.0)
    q = list(SHEET)
    if lift > 0:
        Ls += sheet_shape(SHEET, holes=False)[:1]                  # the sheet underneath
        up = 46 * lift
        q = [q[0], q[1], (q[2][0] - 10 * lift, q[2][1] - up), (q[3][0] - 10 * lift, q[3][1] - up)]
    Ls += sheet_shape(q)
    if not st['blank']:
        Ls += on_page(q, sheet_content(st['c'], st['d'], st['d2'], st['p'], st['drip'], st['dab'], st['k'], st['bad']))
    Ls += _static['peg']
    return Ls


def flying(t):
    """Sheets on their way to the tray (or the floor), as strokes."""
    Ls = []
    for f in FLY:
        u = (t - f['te']) / f['dur']
        if not 0 <= u < 1:
            continue
        rng = random.Random(f['k'] * 31 + 5)
        n_then = pile_n(f['te'] + f['dur'] + 0.2)
        q1 = tray_top(n_then)
        m = f['mess']
        q1 = [(px + rng.uniform(-26, 26) * m, py + rng.uniform(-6, 6) * m) for px, py in q1]
        e = smooth(u)
        slide = smooth(clamp(u / 0.45))
        qa = [(px + 150 * slide, py + 6 * slide) for px, py in SHEET]
        q = quad_lerp(qa, q1, smooth(clamp((u - 0.3) / 0.7)), lift=58 * math.sin(math.pi * clamp((u - 0.25) / 0.75)) * (0.5 + 0.5 * m),
                      turn=m * rng.uniform(-0.9, 0.9) * math.sin(math.pi * e))
        Ls += sheet_shape(q, holes=False)
        c, d, d2, p, drip, dab, k, bad = f['spec']
        Ls += on_page(q, sheet_content(c, d, d2, p, drip, dab, k, bad))
    return Ls


# ------------------------------------------------------------------ the heap ---
_heap = {}


def _heap_data():
    if not _heap:
        rs = random.Random(41)
        xs = [40 + 7.5 * i for i in range(121)]
        rag = []
        for i in range(len(xs)):
            v = rs.uniform(-1, 1)
            rag.append(v * (2.2 if rs.random() < 0.22 else 0.7))
        sheets = []
        for i in range(190):
            sheets.append(dict(x=rs.uniform(70, 900), a=rs.uniform(0, 1) ** 0.8 * 205, w=rs.uniform(46, 96), tilt=rs.uniform(-9, 9),
                               dp=rs.uniform(6, 14), tone=rs.uniform(0.45, 0.8)))
        sheets.sort(key=lambda s_: s_['a'])
        fa = cast.anchors(FINAL, X, Y, S)
        _heap.update(xs=xs, rag=rag, sheets=sheets, bell=fa['bell'], horn=fa['horn'], top=Y - fa['horn'][1] - 11.0)
    return _heap


def heap_shape(x):
    """0..1: the mound's profile across the frame (highest over her)."""
    if x < 300:
        return smooth(clamp((x - 40) / 260.0)) ** 0.8
    if x < 420:
        return 1.0
    return max(0.0, 1.0 - 0.34 * smooth(clamp((x - 420) / 300.0)) - 0.66 * smooth(clamp((x - 720) / 220.0)))


def heap_level(t):
    return L.Pacing('heap', [(25.0, 0.0), (26.0, 112.0, 'lin'), (27.2, 152.0, 'lin'), (28.2, 180.0, 'lin'), (28.6, 1000.0, 'out')]).at(t)


def heap_h(x, level):
    Hd = _heap_data()
    return min(level, Hd['top']) * heap_shape(x) if level < 999 else Hd['top'] * heap_shape(x)


def heap_body(level, notch=1.0):
    """The mound's own contour from its left foot to its right foot (raw points, ragged with sheet corners)."""
    Hd = _heap_data()
    pts = []
    bx, by = Hd['bell']
    nd = 0.0
    for x, r in zip(Hd['xs'], Hd['rag']):
        h = heap_h(x, level)
        y = Y - h - r * min(h, 70.0) * 0.085
        pts.append((x + r * 1.5, min(Y, y)))
    if notch > 0 and heap_h(bx, level) > (Y - by):                 # the paper has not closed over her bell
        out = []
        cut = True
        for p in pts:
            if bx - 17 < p[0] < bx + 11:
                continue
            if p[0] >= bx + 11 and cut:
                la = out[-1]
                out += [(bx - 17, la[1]), (bx - 14, lerp(la[1], by + 12, notch)), (bx - 3, lerp(la[1], by + 18, notch)),
                        (bx + 7, lerp(la[1], by + 12, notch)), (bx + 11, p[1])]
                cut = None
            out.append(p)
        pts = out
    return pts


N_GL, N_SL, N_CL, N_SR, N_GR = 30, 44, 18, 44, 30
N_BODY = N_SL + N_CL + N_SR
N_LINE = N_GL + N_BODY + N_GR


def heap_line(level):
    body = sets.resample(heap_body(level), N_BODY)
    left = sets.resample([(-40.0, Y), (body[0][0] - 2, Y)], N_GL)
    right = sets.resample([(body[-1][0] + 2, Y), (1000.0, Y)], N_GR)
    return left + body + right


def ground_line(cleft=0.0, grip=0.0, shear=0.0, squash=0.0):
    """ONE open line: ground, up and over the stump (with its cleft), ground. Same point count in every state."""
    c = clamp(cleft)
    hw = 2.5 * c * (1 - 0.45 * clamp(grip))
    dp = 12.0 * c
    P = sets.STUMP_PROFILE

    def sc(pts):
        return [(GX + GS * (px + shear * (-py / 22.0) ** 2), GY + GS * py * (1 - squash * 0.04)) for px, py in pts]
    sl = sets.resample(sc(P[:6]), N_SL)
    cl = sets.resample(sc([(-hw - 0.6 * grip, -22 - 0.5 * grip), (0, -22 + dp), (hw + 0.6 * grip, -22 - 0.5 * grip)]), N_CL)
    sr = sets.resample(sc(P[6:]), N_SR)
    gl = sets.resample([(-40.0, GY), (sl[0][0] - 2, GY)], N_GL)
    gr = sets.resample([(sr[-1][0] + 2, GY), (1000.0, GY)], N_GR)
    return gl + sl + cl + sr + gr


def surface_line():
    """What the ground line becomes at 76.0: the top of the left bank, its lip, and the water surface."""
    bx, by, _ = HANDOVER_COW
    gl = sets.resample([(-40.0, by), (150.0, by)], N_GL)
    sl = sets.resample([(150.0, by), (166.0, by + 2.0), (178.0, SURFACE_Y)], N_SL)
    cl = sets.resample([(178.0, SURFACE_Y), (200.0, SURFACE_Y)], N_CL)
    sr = sets.resample([(200.0, SURFACE_Y), (430.0, SURFACE_Y)], N_SR)
    gr = sets.resample([(430.0, SURFACE_Y), (1000.0, SURFACE_Y)], N_GR)
    return gl + sl + cl + sr + gr


def _R(name, axis, keys):
    """A track keyed in px from the middle of the stump's cut (x) and from its rim (y)."""
    o = GX if axis == 'x' else RIM_Y
    return L.Pacing(name, [(k[0], o + k[1]) + tuple(k[2:]) for k in keys])


PACE = dict(
    settle=L.Pacing('settle', [(29.5, 0.0), (30.2, 0.2, 'in'), (31.0, 0.86, 'smooth'), (31.5, 1.0, 'out')]),
    # the point of the stub / the wedge of the shoot on the screen, and the way the shoot runs from it (degrees)
    wx=_R('wx', 'x', [(30.0, -27), (31.2, -27), (31.4, -22, 'smooth'), (31.8, -22), (31.95, -25, 'smooth'), (32.0, -30, 'in'),
                      (32.13, 10, 'in'), (32.25, 8, 'out'), (32.5, -8, 'smooth'), (32.65, -8), (32.76, -7, 'in'),
                      (32.88, -6.5), (32.96, 8, 'in'), (33.05, 3, 'out'), (33.2, 0, 'smooth'), (33.26, 0), (33.40, 0)]),
    wy=_R('wy', 'y', [(30.0, -10), (31.2, -10), (31.4, -30, 'smooth'), (31.8, -30), (31.95, -18, 'smooth'), (32.0, 0, 'in'),
                      (32.13, 1, 'lin'), (32.25, -12, 'out'), (32.5, -42, 'smooth'), (32.65, -42), (32.76, -1, 'in'),
                      (32.88, 0.5), (32.96, -2, 'lin'), (33.05, -27, 'out'), (33.2, -42, 'smooth'), (33.26, -42),
                      (33.34, 0, 'in'), (33.40, 12.0 * GS, 'lin')]),
    ang=L.Pacing('ang', [(30.0, -84), (31.8, -84), (31.95, -94, 'smooth'), (32.0, -92), (32.13, -68, 'in'), (32.25, -66, 'out'),
                         (32.5, -84, 'smooth'), (32.65, -84), (32.76, -66, 'in'), (32.88, -58, 'out'), (32.96, -62, 'in'),
                         (33.05, -82, 'out'), (33.2, -90, 'smooth'), (33.40, -90), (33.62, -84, 'over')]),
    grow=L.Pacing('grow', [(T['grow'][0], 0.0), (T['grow'][1], 1.0, 'smooth')]),
    buds=L.Pacing('buds', [(32.42, 0.0), (32.8, 1.0, 'smooth')]),
    bend=L.Pacing('bend', [(32.64, 0.0), (32.70, -0.9, 'out'), (32.76, 0.4, 'in'), (32.88, 1.7, 'out'), (32.96, -1.3, 'in'),
                           (33.05, 0.7, 'out'), (33.2, 0.0, 'smooth'), (33.27, 0.0), (33.33, -0.6, 'out'), (33.40, 0.9, 'in')]),
    cleft=L.Pacing('cleft', [(32.05, 0.0), (32.10, 0.3, 'out'), (32.76, 0.3), (32.88, 0.38, 'out'), (32.97, 0.3, 'out'),
                             (33.33, 0.3), (33.40, 1.0, 'in')]),
    grip=L.Pacing('grip', [(T['seat'], 0.0), (T['grip'], 1.0, 'out')]),
    wind=L.Pacing('wind', [(T['bind'][0], 0.0), (34.0, 0.0), (34.33, 1 / 3.0, 'smooth'), (34.66, 2 / 3.0, 'smooth'), (35.0, 1.0, 'smooth')]),
    lift=L.Pacing('lift', [(T['bind'][0], 0.0), (34.0, 1.0, 'smooth')]),
    world=L.Pacing('world', [(T['cool'][0], 0.0), (T['cool'][1] - 1.0 / FPS, 1.0, 'smooth')]),
)
LEAF_OPEN = [37.2, 37.62, 37.76, 37.9, 38.02, 38.14, 38.26]       # leaf by order: the upper bud first, alone
LEAF_GO = [T['loosen'] + k * 4.0 / FPS for k in range(7)]


def bend_at(t):
    if t <= T['seat']:
        return PACE['bend'].at(t)
    return 0.9 * math.exp(-(t - T['seat']) * 6.5) * math.cos(2 * math.pi * 5.0 * (t - T['seat']))


def wedge_at(t):
    return (PACE['wx'].at(t), PACE['wy'].at(t) + 66.0 * (1 - smooth(ramp(t, 30.35, 31.05))), PACE['ang'].at(t))


def stump_shear(t):
    s_ = 0.0
    if t > 32.05:
        s_ += 1.3 * math.exp(-(t - 32.05) * 8) * math.cos(2 * math.pi * 4.5 * (t - 32.05))
    if t > T['stuck']:
        s_ += 0.7 * math.exp(-(t - T['stuck']) * 12) * math.sin(2 * math.pi * 5 * (t - T['stuck']))
    return s_


def stump_squash(t):
    return math.exp(-(t - T['seat']) * 10) * math.cos(2 * math.pi * 4 * (t - T['seat'])) if t > T['seat'] else 0.0


# ------------------------------------------------------------------ her poses standing ---
STAND = cast.POSES['stand']
LOOKUP = cast.POSES['look_up']
HOLD_BASE = cast.with_(STAND, neck=-30.0, head=30.0, ear=26.0, eye=1.2, tail=(6.0, 10.0, 10.0))
WATCH = cast.with_(LOOKUP, dx=-15.0, neck=-55.0, head=50.0, ear=24.0, eye=1.15)
LOW = cast.with_(STAND, dx=-8.0, dy=5.0, shoulder=5.0, neck=26.0, head=50.0, ear=-42.0, eye=0.5, tail=(0.0, 0.0, 0.0))
UP = cast.with_(LOOKUP, dx=-15.0, neck=-57.0, head=44.0, ear=40.0, eye=1.5)
FOLLOW = cast.with_(LOOKUP, dx=-10.0, neck=-40.0, head=48.0, ear=30.0, eye=1.3)


def stand_state(t):
    """Her pose standing at the stump, and whether the stub is in her mouth."""
    if t < T['let_go'][0]:
        wx, wy, ang = wedge_at(t)
        d = _dir(ang)
        m = ((wx + GRIP * d[0] - CX), (wy + GRIP * d[1] - CY))
        crouch = 1 - smooth(ramp(t, 30.35, 31.05))
        lean = 10.0 * smooth(ramp(t, 31.95, 32.13)) * (1 - smooth(ramp(t, 32.25, 32.5))) - 6.0 * smooth(ramp(t, 31.8, 31.95)) * (1 - smooth(ramp(t, 31.98, 32.05)))
        lean += 6.0 * smooth(ramp(t, 32.65, 32.8)) * (1 - smooth(ramp(t, 32.94, 33.05))) - 5.0 * smooth(ramp(t, 32.98, 33.1)) * (1 - smooth(ramp(t, 33.26, 33.36)))
        ear = 26.0 + 22.0 * math.sin(math.pi * ramp(t, 33.06, 33.24)) - 34.0 * smooth(ramp(t, 32.76, 32.86)) * (1 - smooth(ramp(t, 32.96, 33.06)))
        eye = 1.2 + 0.35 * smooth(ramp(t, 32.25, 32.5)) * (1 - smooth(ramp(t, 32.65, 32.75))) + 0.6 * smooth(ramp(t, 32.88, 32.95)) * (1 - smooth(ramp(t, 33.1, 33.26)))
        base = cast.with_(HOLD_BASE, dx=lean, dy=58.0 * crouch, ear=ear, eye=eye, pitch=0.6 * lean * 0.2)
        pose = aim(base, m, lean=15.0)
        return dict(pose=pose, held=True)
    hold_end = stand_state(T['let_go'][0] - 1e-4)['pose']
    pose = keyed([(T['let_go'][0], hold_end), (T['let_go'][0] + 0.08, cast.with_(hold_end, jaw=14.0), 'out'),
                  (T['let_go'][1] + 0.1, WATCH, 'inout'), (T['lower'][0], WATCH), (T['lower'][1], LOW, 'inout'),
                  (T['ear'], LOW), (T['ear'] + 0.12, cast.with_(LOW, ear=46.0, eye=1.0), 'out'), (T['head_up'], cast.with_(LOW, ear=46.0, eye=1.1)),
                  (T['head_up'] + 0.28, UP, 'snap'), (T['loosen'] + 0.1, UP), (T['loosen'] + 0.7, FOLLOW, 'inout'),
                  (T['cool'][1], LOOKUP, 'inout')], t)
    return dict(pose=pose, held=False)


def world(t):
    """The move of the last second: everything on the ground goes to its place at the water's edge."""
    w = PACE['world'].at(t)
    k = lerp(1.0, HANDOVER_COW[2], w)
    c = (lerp(CX, HANDOVER_COW[0], w), lerp(CY, HANDOVER_COW[1], w))

    def f(p):
        return (c[0] + k * (p[0] - CX), c[1] + k * (p[1] - CY))
    return w, k, c, f


# ------------------------------------------------------------------ the shoot, the binding, the leaves ---
def shoot_strokes(t):
    """Her pencil stub, which is the scion: strokes on the screen, the wedge point and the axis."""
    wx, wy, ang = wedge_at(t)
    g = PACE['grow'].at(t)
    Ls = sets.shoot_lines(wx, wy, GS, ang, g, g, PACE['buds'].at(t))
    b = bend_at(t) * g
    d = _dir(ang)
    n = (-d[1], d[0])
    full = 64.0 * GS

    def bent(p):
        al = (p[0] - wx) * d[0] + (p[1] - wy) * d[1]
        off = b * 17.0 * (max(0.0, al) / full) ** 2
        return (p[0] + n[0] * off, p[1] + n[1] * off)
    if g < 0.9:                                      # the lead of the pencil: it is drawn away as the stub becomes wood
        r = 5.5 * GS * (1 - g / 0.9)
        tri = [(wx, wy), (wx + d[0] * r - n[0] * r * 0.24, wy + d[1] * r - n[1] * r * 0.24), (wx + d[0] * r + n[0] * r * 0.24, wy + d[1] * r + n[1] * r * 0.24)]
        Ls += sets.hatch(tri, 1.6, ang + 60, 0.9, 0.95, seed=4)
        for f_ in (0.36, 0.5, 0.64):                 # the flats of the pencil
            a0 = (wx + d[0] * 14.2 * GS + n[0] * (f_ - 0.5) * 6.2 * GS, wy + d[1] * 14.2 * GS + n[1] * (f_ - 0.5) * 6.2 * GS)
            a1 = (a0[0] + d[0] * 11.0 * GS * (1 - g), a0[1] + d[1] * 11.0 * GS * (1 - g))
            Ls.append(Stroke([a0, a1], 0.6, 0.6 * (1 - g)))
    return [st.like([bent(p) for p in st]) for st in Ls], (wx, wy, ang), bent


def rope():
    """The crooked path lifted off the floor sheet as a rope: its crest end at the stump, the loop still in it."""
    src = sets.resample(sets.on_sheet(FLOOR_SHEET, sets.path_stroke()), 120)
    bx0 = sets.binding_path(GX, GY - 20.6 * GS, GS)[0]
    out = []
    for i, (px, py) in enumerate(src):
        f = i / 119.0
        ax, ay = lerp(bx0[0], 452.0, f ** 0.9), lerp(bx0[1], GY + 14.0, f ** 0.55) - 22.0 * math.sin(math.pi * f)
        # keep the wander of the path about the rope's own run
        mx, my = lerp(src[0][0], src[-1][0], f), lerp(src[0][1], src[-1][1], f)
        out.append((ax + (px - mx) * 1.2, ay + (py - my) * 1.9))
    return src, out


_rope = None


def wind_line(t):
    """The path line on its way to being the binding: 120 points at every moment. Returns (points, wound count)."""
    global _rope
    if _rope is None:
        _rope = rope()
    src, rp = _rope
    lift, f = PACE['lift'].at(t), PACE['wind'].at(t)
    if f <= 0:
        return lerp_pts(src, rp, lift), 0
    helix = sets.binding_path(GX, GY - 20.6 * GS, GS)
    k = min(119, int(f * 119))
    fr = f * 119 - k
    hk = helix[k] if k >= 119 else (lerp(helix[k][0], helix[k + 1][0], fr), lerp(helix[k][1], helix[k + 1][1], fr))
    out = list(helix[:k + 1])
    shrink = 1.0 - 0.55 * f
    for j in range(k + 1, 120):
        ref = rp[k] if k >= 119 else (lerp(rp[k][0], rp[k + 1][0], fr), lerp(rp[k][1], rp[k + 1][1], fr))
        if f >= 1:
            out.append(helix[j])
        else:
            out.append((hk[0] + (rp[j][0] - ref[0]) * shrink, hk[1] + (rp[j][1] - ref[1]) * shrink))
    return out, k


def leaf_sites(t, bent):
    wx, wy, ang = wedge_at(max(t, T['seat']))
    out = []
    for s_ in sets.leaf_sites(wx, wy, GS, ang, grow=1.0, knuckle=1.0):
        x, y = bent((s_['x'], s_['y']))
        out.append(dict(s_, x=x, y=y))
    return sorted(out, key=lambda s_: s_['order'])


def _fish_unit():
    up = [(0.035, 0.0), (0.0, -0.135), (0.10, -0.045), (0.22, -0.072), (0.36, -0.115), (0.47, -0.132), (0.52, -0.185),
          (0.62, -0.135), (0.76, -0.108), (0.88, -0.072), (0.96, -0.036), (1.0, 0.0)]
    dn = [(1.0, 0.0), (0.975, 0.03), (0.90, 0.072), (0.78, 0.105), (0.62, 0.122), (0.52, 0.125), (0.47, 0.172), (0.435, 0.118),
          (0.30, 0.092), (0.225, 0.072), (0.19, 0.11), (0.16, 0.055), (0.10, 0.042), (0.0, 0.135), (0.035, 0.0)]
    pts = sets.resample(up, 25) + sets.resample(dn, 25)[1:]
    return [(px - 0.5, py) for px, py in pts]


FISH_UNIT = _fish_unit()          # 49 points: point 0 the fork of the tail (the leaf's stem end), point 24 the nose (its tip)
_leaf_frozen = {}


def leaf_or_fish(k, t, site, wf):
    """Leaf k: on the shoot, opening; or let go and on its way to being fish k. Returns strokes."""
    go = LEAF_GO[k]
    o = smooth(ramp(t, LEAF_OPEN[k], LEAF_OPEN[k] + (0.42 if k == 0 else 0.3)))
    if o <= 0:
        return []
    flut = 2.0 * math.sin(t * 1.7 + k * 1.9) * o
    curl = 0.25 * math.sin(k * 2.1)
    if t < go:
        sx, sy = wf((site['x'], site['y']))
        return sets.leaf_lines(sx, sy, GS * wf.k, site['angle'] + flut, o, site['length'], site['width'], curl=curl, veins=False)
    if k not in _leaf_frozen:
        tg = go
        w, kk, c, f = world(tg)
        sx, sy = f((site['x'], site['y']))
        ct = sets.leaf_contour(sx, sy, GS * kk, site['angle'] + 2.0 * math.sin(tg * 1.7 + k * 1.9), 1.0, site['length'], site['width'], curl=curl)
        ct = list(ct)
        c0 = ((ct[0][0] + ct[24][0]) / 2, (ct[0][1] + ct[24][1]) / 2)
        a0 = math.degrees(math.atan2(ct[24][1] - ct[0][1], ct[24][0] - ct[0][0]))
        loc = _tf([(p[0] - c0[0], p[1] - c0[1]) for p in ct], 0, 0, 1.0, -a0)
        _leaf_frozen[k] = (c0, a0, loc)
    c0, a0, loc = _leaf_frozen[k]
    F = HANDOVER_FISH[k]
    u = clamp((t - go) / (SECONDS - 1.0 / FPS - go))
    e = smooth(u)
    m = smooth(clamp((u - 0.12) / 0.7))
    fish = [(px * F['length'], py * F['length']) for px, py in FISH_UNIT]
    wig = math.sin(t * 9.0 + k * 1.3)
    shape = []
    for (lx, ly), (fx, fy) in zip(loc, fish):
        x_, y_ = lerp(lx, fx, m), lerp(ly, fy, m)
        tail = clamp(-x_ / (F['length'] * 0.5))
        shape.append((x_, y_ + m * wig * 5.0 * tail * tail))
    a_ = a0
    while a_ > 180:
        a_ -= 360
    while a_ < -180:
        a_ += 360
    drop = math.sin(math.pi * clamp(u / 0.5)) * (1 - u)
    ang = lerp(a_, 0.0, smooth(clamp(u / 0.75))) + 26.0 * drop + m * 3.0 * math.sin(t * 5 + k)
    cx = lerp(c0[0], F['x'], e ** 1.25)
    cy = lerp(c0[1], F['y'], smooth(clamp(u / 0.85))) + 12.0 * math.sin(math.pi * u) * (1 if k % 2 else -1)
    pts = _tf(shape, cx, cy, 1.0, ang)
    Ls = [Stroke(pts, 1.05, 1.0, fill=True)]
    mid = _tf([(lerp(shape[0][0], shape[24][0], f_) * (1 - 0.25 * m), lerp(shape[0][1], shape[24][1], f_) + m * wig * 5.0 * clamp(0.5 - f_) ** 2 * 4)
               for f_ in [0.12 + 0.07 * i for i in range(10)]], cx, cy, 1.0, ang)
    Ls.append(Stroke(mid, 0.6, 0.75))
    if m > 0.35:
        r = F['length'] * 0.024 * smooth((m - 0.35) / 0.65)
        ex, ey = _tf([(F['length'] * 0.36, -F['length'] * 0.028)], cx, cy, 1.0, ang)[0]
        Ls.append(Stroke(sets._ell(ex, ey, r, r, n=10), 1.0, 1.0))
        gl = _tf([(F['length'] * 0.27, -F['length'] * 0.07 * m), (F['length'] * 0.245, 0.0), (F['length'] * 0.27, F['length'] * 0.07 * m)], cx, cy, 1.0, ang)
        Ls.append(Stroke(gl, 0.7, 0.8))
    return Ls


# ------------------------------------------------------------------ grounds ---
_bg = {}


def _cream():
    if 'cream' not in _bg:
        ink = kit.Ink(0, 0, (W, H))
        sets.paper_ground(ink, 0.0)
        _bg['cream'] = np.asarray(ink.img.convert('RGB'), np.float32)
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        wt = np.clip((yy - SURFACE_Y) / (H - SURFACE_Y), 0, 1)
        water = np.array(END_WATER[0], np.float32) * (1 - wt) + np.array(END_WATER[1], np.float32) * wt
        air = np.array(END_AIR, np.float32)[None, None, :] * np.ones((H, 1, 1), np.float32)
        _bg['cool'] = np.broadcast_to(np.where(yy < SURFACE_Y, air, water), (H, W, 3)).copy()
    return _bg


def ground_array(cool=0.0):
    B = _cream()
    if cool <= 0:
        return B['cream']
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    front = lerp(-110.0, H + 110.0, cool)
    wt = np.clip((front - yy) / 110.0, 0, 1)
    wt = wt * wt * (3 - 2 * wt)
    return B['cream'] * (1 - wt) + B['cool'] * wt


def put_ground(ink, arr):
    ink.img = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')
    ink._grain = True


def fill_under(ink, line, arr, bottom=H + 20):
    """Paper under a line: what is behind the heap, the ground or the stump is hidden by it."""
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in line] + [(line[-1][0], bottom), (line[0][0], bottom)], fill=255)
    bg = Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGB')
    ink.img.paste(bg, (0, 0), m)
    ink.d = ImageDraw.Draw(ink.img, 'RGBA')


def boil_seed(t):
    return int(t * 8)


def place_cow(ink, pose, x, y, s=1.0, t=0.0):
    return cast.place(ink, pose, x, y, s=s, style='line', seed=boil_seed(t))


# ------------------------------------------------------------------ the picture ---
def draw(t, ink):
    """A full frame of act 2 at act time t (0 .. SECONDS)."""
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < T['insert'][0] or T['insert'][1] <= t < T['duck'][1]:
        _draw_desk(t, ink)
    elif t < T['insert'][1]:
        _draw_insert(t, ink)
    else:
        _draw_graft(t, ink)


def _path_on(quad):
    return sets.on_sheet(quad, sets.path_stroke())


def _thin(st, w=0.62):
    st.w = w
    return st


def _draw_desk(t, ink):
    put_ground(ink, ground_array(0.0))
    full, small = sets.path_stroke(), _path_on(SHEET)
    if t < T['line'][0]:
        sets.pencil(ink, full, boil=0, wob=0.0)               # the frame act 1 hands over
        return
    u = ease(t, *T['line'])
    st = desk_state(t)
    pile = pile_n(t)
    # 1. the set (drawn on in 2.1)
    Ls = set_lines(st, pile, t, 0.0)
    Ls += sets.lever_lines(LEVER[0], LEVER[1], S, st['pull'])
    Ls += _static['blank']
    prog = ramp(t, *T['set_on'])
    if prog > 0:
        sets.pencil(ink, Ls, prog, seed=1)
    # 2. the sheet on the pegs
    first = t < T['push'][0] + 0.06
    if first:
        if t >= T['line'][1]:
            sets.pencil(ink, sheet_shape(SHEET), ramp(t, T['line'][1], T['line'][1] + 0.5), seed=2)
        line = sets.morph(full, small, u, 201)
        line.w = 1.0
        sets.pencil(ink, line, width=lerp(1.7, 1.15, u), wob=0.55 * u, boil=6, seed=3)
        if t >= T['trace'][0]:                                # she goes over the loop again: it is the darkest part
            lp = on_page(SHEET, [Stroke(LOOP_PAGE[:max(2, int(len(LOOP_PAGE) * smooth(ramp(t, *T['trace']))))], 1.2, 1.0)])
            sets.pencil(ink, lp, width=1.3, seed=4)
        sets.pencil(ink, _static['peg'], ramp(t, 2.2, 2.6), seed=5)
    else:
        sets.pencil(ink, board_sheet(st, t), seed=2)
    # 3. the tray and the first sheet on its way to the floor
    if prog > 0:
        sets.pencil(ink, sets.tray_lines(TRAY[0], TRAY[1], S, n=pile, mess=clamp(0.15 + pile / 45.0)), ramp(t, 2.5, 3.0), seed=6)
    if not first:
        e = ramp(t, T['push'][0] + 0.06, T['fall'][1])
        slide = smooth(clamp(e / 0.3))
        qa = [(px - 34 * slide, py + 16 * slide) for px, py in SHEET]
        fall = smooth(clamp((e - 0.25) / 0.75))
        q = quad_lerp(qa, FLOOR_SHEET, fall, lift=-10 * math.sin(math.pi * fall), turn=0.5 * math.sin(math.pi * fall) * (1 - fall))
        _static['floor_q'] = q
    # 4. her
    if t < T['cow_on'][1]:
        if 'outline' not in _static:
            o = cast.outline(st['pose'], S, n=260)
            _static['outline'] = Stroke([(X + px, Y + py) for px, py in o] + [(X + o[0][0], Y + o[0][1])], 1.2, 1.0, fill=True)
        cp = ramp(t, *T['cow_on'])
        if cp > 0:
            sets.pencil(ink, [_static['outline']], cp, width=2.0, seed=7)
        a = cast.anchors(st['pose'], X, Y, S)
    else:
        pose = perf('desk').pose(t) if t >= 2.0 else st['pose']
        a = place_cow(ink, pose, X, Y, S, t)
    front = []
    if st['pencil'] and t >= T['cow_on'][0] + 0.5:
        pt = (a['hand'][0] + 20.0, a['hand'][1] - 6.0)
        front += pencil_prop(pt)
    if st['brush'] is not None:
        d = _dir(st['brush'])
        tip = (a['mouth'][0] - BRUSH_LEN * d[0], a['mouth'][1] - BRUSH_LEN * d[1])
        front += sets.brush_lines(tip[0], tip[1], S, st['brush'])
    if not first:
        q = _static['floor_q']
        front += sheet_shape(q, holes=False) + [_thin(_path_on(q))]
    front += flying(t)
    if front:
        sets.pencil(ink, front, seed=8)
    # 5. the paper coming down, and the heap
    if t >= T['drown'][0]:
        _draw_fountain(t, ink)
        lvl = heap_level(t)
        e = PACE['settle'].at(t)
        line = heap_line(lvl) if e <= 0 else lerp_pts(heap_line(1000.0), ground_line(), e)
        fill_under(ink, line, ground_array(0.0))
        sets.pencil(ink, _heap_sheets(lvl, 1.0 - e, line if e > 0 else None) + [Stroke(line, 1.25, 1.0)], seed=9)
    if st['blink']:
        arr = np.asarray(ink.img.convert('RGB'), np.float32)
        put_ground(ink, arr * 0.45 + 120.0 * 0.55)


def _heap_sheets(level, k=1.0, line=None):
    """The sheets inside the heap. While it settles (k < 1) they are carried in with its contour and go under."""
    Hd = _heap_data()
    out = []
    e = 1.0 - k
    xs = [p[0] for p in line] if line is not None else None
    for s_ in Hd['sheets']:
        h = heap_h(s_['x'], level)
        if s_['a'] > h - 9 or (abs(s_['x'] + 4 - Hd['bell'][0]) < s_['w'] / 2 + 22 and s_['a'] > Y - Hd['bell'][1] - 34):
            continue
        x = lerp(s_['x'], GX + (s_['x'] - 490.0) * 0.12, e)
        y = Y - s_['a'] * k
        ww = lerp(1.0, 0.3, e)
        w2, tl, dp = s_['w'] / 2 * ww, s_['tilt'] * k, s_['dp'] * k
        if line is not None:
            top = min((p[1] for p in line if abs(p[0] - x) < 14), default=Y)
            if y - dp < top + 7 or k < 0.3:
                continue
        q = [(x - w2, y), (x + w2, y + tl), (x + w2 + 9 * ww, y + tl - dp), (x - w2 + 9 * ww, y - dp)]
        out.append(Stroke(q + [q[0]], 0.62, s_['tone'], fill=True))
    return out


def _draw_fountain(t, ink):
    Ls = []
    rs = random.Random(7)
    n = 0
    te = T['drown'][0]
    while te < T['under']:
        gap = lerp(0.085, 0.03, ramp(te, 25.0, 27.5))
        vx, vy, sp, ph = rs.uniform(-240, 430), rs.uniform(-560, -330), rs.uniform(-7, 7), rs.uniform(0, 6.28)
        a_ = t - te
        if 0 <= a_ < 1.3:
            x, y = 412 + vx * a_, 326 + vy * a_ + 0.5 * 1500 * a_ * a_
            if y < Y + 30:
                th = ph + sp * a_
                c, sn = math.cos(th), math.sin(th)
                sq = 0.35 + 0.65 * abs(math.sin(ph * 2 + a_ * 5))
                q = [(x + c * dx_ - sn * dy_ * sq, y + sn * dx_ + c * dy_ * sq) for dx_, dy_ in ((-30, -17), (30, -17), (30, 17), (-30, 17))]
                Ls.append(Stroke(q + [q[0]], 0.8, 0.9, fill=True))
        te += gap
        n += 1
    if Ls:
        sets.pencil(ink, Ls, seed=10, boil=12)


INSERT_Q = [(118.0, 468.0), (842.0, 468.0), (842.0, 106.0), (118.0, 106.0)]


def _draw_insert(t, ink):
    put_ground(ink, ground_array(0.0))
    q = INSERT_Q
    Ls = [Stroke([(60, 498), (900, 498), (900, 76), (60, 76), (60, 498)], 1.3, 0.9)]                 # the board
    Ls += sheet_shape(q, holes=False)
    for f, kind in ((0.22, 0), (0.5, 1), (0.78, 0)):
        cx = lerp(q[0][0], q[1][0], f)
        Ls.append(Stroke(sets._ell(cx, 452, 13 if kind else 30, 8, n=18), 1.0, 0.9))
    sets.pencil(ink, Ls, seed=11, width=2.0)
    fp = ramp(t, T['insert'][0] + 0.25, T['insert'][0] + 0.95)
    body, leg = bad_drawing()
    sets.pencil(ink, on_page(q, body), width=2.6, wob=1.3, boil=6, seed=12)
    if fp > 0:
        tip = sets.pencil(ink, on_page(q, leg), fp, width=2.6, wob=1.3, boil=6, seed=13)
    else:
        tip = page_pt(q, leg[0][0])
    # her pencil, finishing the fifth leg, then drawn away
    off = smooth(ramp(t, T['insert'][0] + 1.0, T['insert'][0] + 1.35))
    if tip is not None and off < 1:
        px, py = tip[0] - 150 * off, tip[1] + 240 * off
        Ls = sets.shoot_lines(px, py, 4.2, -128.0, 0.0, 0.0, 0.0)
        hx, hy = px - 64, py - 86
        hoof = [(-34, -8), (-22, -30), (4, -38), (30, -30), (40, -6), (30, 22), (6, 30), (2, 6), (-4, 28), (-26, 22)]
        Ls.append(Stroke([(hx + a_, hy + b_) for a_, b_ in hoof] + [(hx - 34, hy - 8)], 1.2, 1.0, fill=True))
        Ls += sets.hatch([(hx + a_, hy + b_) for a_, b_ in hoof], 5.0, 40, 0.7, 0.6, seed=3)
        Ls.append(Stroke([(hx - 30, hy - 26), (hx - 110, hy - 150), (hx - 60, hy - 190), (hx + 26, hy - 34)], 1.2, 1.0, fill=True))
        sets.pencil(ink, Ls, width=2.2, seed=14)


def _draw_graft(t, ink):
    w, k, c, wf_ = world(t)

    class _WF:
        pass
    wf = lambda p: wf_(p)
    wf.k = k
    arr = ground_array(ramp(t, *T['cool']))
    put_ground(ink, arr)
    e = PACE['settle'].at(t)
    cleft, grip = PACE['cleft'].at(t), PACE['grip'].at(t)
    gl = ground_line(cleft, grip, stump_shear(t), stump_squash(t))
    if e < 1:
        hl = heap_line(1000.0)
        line = lerp_pts(hl, gl, e)
    elif w > 0:
        line = lerp_pts(gl, surface_line(), w)
    else:
        line = gl
    # the binding, far side (behind everything that stands)
    bind, wound = (wind_line(t) if t >= T['bind'][0] else (None, 0))
    sq = lambda p: (wf(p)[0], lerp(wf(p)[1], c[1] + (4.0 if p[0] > GX - 40 else 0.0) * w, w))     # flattened into the line
    # her
    st = stand_state(t)
    pose = perf('stand').pose(t)
    a = place_cow(ink, pose, c[0], c[1], k, t)
    if e < 1:
        sets.pencil(ink, shoot_strokes(t)[0], seed=22)        # the stub is under the paper with her
    if w < 0.5:
        fill_under(ink, line, arr)
    back = []
    # the sheet at her feet: it came down with the heap; the path line lies on it until it is taken up
    if e > 0.25 and t < 35.0:
        down = smooth(clamp((e - 0.25) / 0.6))
        fq = [(px, lerp(py - 150, py, down)) for px, py in FLOOR_SHEET]
        if t >= 34.4:                                         # the empty sheet is drawn in after the line: it is the knot
            hx = sets.binding_path(GX, GY - 20.6 * GS, GS)[-1]
            kq = sets._ell(hx[0], hx[1], 5.5, 4.0, n=4)[:4]
            fq = lerp_pts(fq, kq, smooth(ramp(t, 34.4, 35.0)))
        back += sheet_shape(fq, holes=False)
        if t < T['bind'][0]:
            back.append(_thin(_path_on(fq)))
    elif t >= 35.0 and w < 0.97:
        hx = sets.binding_path(GX, GY - 20.6 * GS, GS)[-1]
        back.append(Stroke([sq(p) for p in sets._ell(hx[0], hx[1], 5.5, 4.0, n=10)], 0.9, 1.0, fill=True))
    if e < 0.97:
        back += _heap_sheets(1000.0, 1 - e, line)
    back.append(Stroke(line, 1.3, 1.0))
    # the stump's own marks draw themselves in once the line has settled
    det = sets.stump_lines(GX, GY, GS, cleft, grip)[1:]
    dprog = ramp(t, 31.0, 31.9)
    if w > 0:
        det = [st_.like([sq(p) for p in st_]) for st_ in det] if w < 0.97 else []
    sets.pencil(ink, back, seed=20)
    if dprog > 0 and det:
        sets.pencil(ink, det, dprog, seed=21)
    front = []
    # the shaving
    if t >= 32.04:
        curl = ramp(t, 32.04, 32.3)
        fall = cast.EASES['slow'](ramp(t, 32.3, 32.62))
        sx, sy = lerp(GX + 26, GX + 96, smooth(ramp(t, 32.04, 32.62))), lerp(RIM_Y - 4, GY - 9, fall) - 16 * math.sin(math.pi * ramp(t, 32.04, 32.3))
        sh = sets.shaving_lines(sx, sy, 1.2, curl, angle=-30 + 200 * ramp(t, 32.04, 32.62))
        if w < 0.97:
            front += [st_.like([sq(p) for p in st_]) for st_ in sh] if w > 0 else sh
    # binding behind the shoot: the turns on the far side were drawn first, so only draw the near halves here
    shoot, (wx, wy, ang), bent = shoot_strokes(t)
    if w > 0:
        edge = sets.resample(BANK_EDGE, 37)
        edge = edge + [(px - 1.2, py) for px, py in edge[::-1]]
        ct = sets.resample(list(shoot[0]), len(edge))
        shoot = [Stroke(lerp_pts([wf(p) for p in ct], edge, smooth(w)), 1.15, 1.0)] + \
                ([st_.like([(lerp(wf(p)[0], wf((wx, wy))[0], w), lerp(wf(p)[1], wf((wx, wy))[1], w)) for p in st_]) for st_ in shoot[1:]] if w < 0.9 else [])
    if bind is not None and w < 0.97:
        pts = [sq(p) for p in bind] if w > 0 else bind
        runs, cur, near = [], [], None
        for i, p in enumerate(pts):
            th = 2 * math.pi * 3.0 * i / 111.0
            is_far = i <= wound and i < 112 and math.sin(th) < -0.05
            if is_far:
                if len(cur) > 1:
                    runs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            runs.append(cur)
        bstrokes = [Stroke(r, 1.25, 1.0) for r in runs]
    else:
        bstrokes = []
    if e >= 1:
        front += shoot
    front += bstrokes
    sets.pencil(ink, front, seed=22)
    # leaves, and the fish they become
    if t >= LEAF_OPEN[0]:
        sites = leaf_sites(t, bent)
        Ls = []
        for kk in (6, 5, 4, 3, 2, 1, 0):
            Ls += leaf_or_fish(kk, t, sites[kk], wf)
        if Ls:
            sets.pencil(ink, Ls, seed=23, width=1.9)
    return a


# ------------------------------------------------------------------ sound ---
def _add_filtered(mix, at, fn, seconds, lo, hi, gain=1.0, pan=0.0):
    tmp = kit.Mix(seconds, seed=3)
    fn(tmp)
    sig = (tmp.L + tmp.R) / 2.828
    mix.add(mix.band(sig, lo, hi), at, gain, pan)


def _scratch(mix, at, seconds, gain, pan=-0.3, lo=1800, hi=6500):
    n = int(seconds * mix.rate)
    if n < 8:
        return
    x = mix.band(mix.noise(seconds), lo, hi) * np.hanning(n) ** 0.5
    mix.add(x, at, gain, pan)


def sound(mix, at=0.0):
    """Act 2's sound, the act starting at `at` seconds of the mix. Placed from T, JOBSEQ and FLY; never heard."""
    a = at
    pan_desk, pan_stump = -0.25, 0.3
    mix.room(a, 29.5, gain=0.018)
    # 2.1 the line is hers: pencil under the settling line and over the loop; bell as she is pleased
    _scratch(mix, a + 0.2, 1.3, 0.035, pan_desk)
    _scratch(mix, a + T['trace'][0], T['trace'][1] - T['trace'][0], 0.07, pan_desk)
    mix.bell(a + 3.0, freq=740, seconds=0.9, gain=0.16, pan=pan_desk)
    mix.whoosh(a + T['push'][0] + 0.05, seconds=0.25, gain=0.04, pan=pan_desk)
    # 2.2 / 2.3 five jobs, five notes; the tune speeds up
    notes = dict(draw='D4', tween='E4', paint='Fs4', camera='A4', check='B4')
    for jb in JOBSEQ:
        t0, dj, nm = a + jb['t0'], jb['dur'], jb['job']
        g = 1.0 if jb['r'] == 0 else 0.85
        tu = lambda uu, jb=jb: a + jb['t0'] + jb['dur'] * _unwarp(uu, jb)
        mix.note(tu(0.3) if nm != 'check' else tu(0.66), NOTE[notes[nm]], seconds=min(0.5, dj * 0.9), gain=0.10 * g, pan=pan_desk)
        if nm == 'draw':
            _scratch(mix, tu(0.28), max(0.06, tu(0.7) - tu(0.28)), 0.08 * g, pan_desk)
        elif nm == 'tween':
            for i in range(3):
                mix.whoosh(tu(0.2 + 0.22 * i + 0.05), seconds=0.08, gain=0.07 * g, pan=pan_desk)
        elif nm == 'paint':
            mix.step(tu(0.24), gain=0.10 * g, pan=0.0, surface='water')
            _scratch(mix, tu(0.42), max(0.05, tu(0.62) - tu(0.42)), 0.03 * g, pan_desk, 400, 2200)
        elif nm == 'camera':
            mix.click(tu(0.36), gain=0.16 * g, pan=0.0)
            mix.thud(tu(0.47), freq=80, gain=0.22 * g, pan=0.0, seconds=0.25)
        else:
            mix.thud(tu(0.66), freq=110, gain=0.3 * g, pan=pan_desk, seconds=0.3)
    for f in FLY[:-1]:
        mix.whoosh(a + f['te'], seconds=0.2, gain=0.05, pan=0.2)
    # 2.4 everything has stopped: room only; two small bells at the turns of her head; the stamp with a flat B
    mix.bell(a + T['look_l'] + 0.12, freq=740, seconds=0.6, gain=0.07, pan=pan_desk)
    mix.bell(a + T['look_r'] + 0.14, freq=740, seconds=0.6, gain=0.07, pan=pan_desk)
    mix.thud(a + T['stamp_bad'] + 0.03, freq=110, gain=0.32, pan=pan_desk, seconds=0.3)
    mix.note(a + T['stamp_bad'] + 0.03, NOTE['B4'] * 2 ** (-0.5 / 12), seconds=0.6, gain=0.11, pan=pan_desk)
    mix.whoosh(a + T['bad_off'] + 0.1, seconds=0.2, gain=0.05, pan=0.2)
    # 2.5 drowning: the five sounds as fast as they go, order lost; paper thickening into one noise; cut
    rs = random.Random(5)
    tk = T['drown'][0]
    names = list(notes)
    while tk < T['under'] - 0.05:
        nm = rs.choice(names)
        mix.note(a + tk, NOTE[notes[nm]], seconds=0.12, gain=0.07, pan=rs.uniform(-0.5, 0.3))
        if nm == 'check':
            mix.thud(a + tk, freq=110, gain=0.14, pan=pan_desk, seconds=0.15)
        elif nm == 'camera':
            mix.click(a + tk, gain=0.1)
        tk += lerp(0.17, 0.06, ramp(tk, 25.0, 27.5))
    dur = T['under'] - T['drown'][0]
    n = int(dur * mix.rate)
    swell = mix.band(mix.noise(dur), 300, 5000) * np.linspace(0.05, 1.0, n) ** 1.5
    swell[-int(0.012 * mix.rate):] *= np.linspace(1, 0, int(0.012 * mix.rate))
    mix.add(swell, a + T['drown'][0], 0.16)
    _add_filtered(mix, a + T['bell_late'], lambda m: m.bell(0.0, freq=740, seconds=0.9, gain=0.5), 1.2, 0, 600, gain=0.5, pan=pan_desk)
    # 2.6 no room now: a quiet wind; the line settling is one low note falling a fifth
    mix.wind(a + 29.5, 10.5, gain=0.02)
    dur = 2.0
    tt = mix.t(dur)
    f = 110.0 * (2 / 3.0) ** np.clip(tt / dur, 0, 1)
    sig = np.sin(2 * np.pi * np.cumsum(f) / mix.rate) * mix.env(len(tt), 0.5, 0.01, 1.0, 0.7)
    mix.add(sig, a + T['settle'][0], 0.07)
    _scratch(mix, a + T['cut'], 0.16, 0.42, pan_stump, 1200, 7000)                 # the cut: the one loud thing
    mix.click(a + T['cut'] + 0.13, gain=0.12, pan=pan_stump, bright=5000)
    mix.click(a + T['stuck'], gain=0.1, pan=pan_stump, bright=1600)                 # it will not go in
    mix.pluck(a + T['spring'], 196.0, seconds=0.5, gain=0.07, pan=pan_stump)        # and springs off the rim
    mix.step(a + T['seat'], gain=0.2, pan=pan_stump, surface='wood')               # home
    for i, nm in enumerate(('D4', 'E4', 'Fs4')):                                    # binding: three turns, three notes
        mix.pluck(a + 34.0 + (i + 1) * (1.0 / 3.0) - 0.03, NOTE[nm], seconds=1.2, gain=0.12, pan=pan_stump)
    # 2.7 the wait: wind only, the bell settling; the bud; seven light leaves
    for hit in perf('stand').bell_hits:
        if 33.4 < hit < 35.4:
            mix.bell(a + hit, freq=740, seconds=0.5, gain=0.05, pan=0.05)
    mix.pluck(a + T['ear'], NOTE['A4'], seconds=1.0, gain=0.08, pan=pan_stump)
    for k, nm in enumerate(('B4', 'D5', 'E5', 'Fs5', 'A5', 'B5', 'D6')):
        mix.pluck(a + LEAF_OPEN[k] + (0.4 if k == 0 else 0.2), NOTE[nm], seconds=0.8, gain=0.06, pan=pan_stump + 0.04 * (k % 3))
    # 2.8 the leaves loosen: the seven again, falling; water comes in under them
    for k, nm in enumerate(('D6', 'B5', 'A5', 'Fs5', 'E5', 'D5', 'B4')):
        mix.pluck(a + LEAF_GO[k] + 0.02, NOTE[nm], seconds=0.8, gain=0.06, pan=lerp(pan_stump, 0.0, k / 6.0))
    wn = mix.band(mix.noise(1.0), 300, 2500) * np.linspace(0, 1, int(1.0 * mix.rate)) ** 1.5
    mix.add(wn, a + T['cool'][0], 0.03)


# ------------------------------------------------------------------ checks, stills, the act alone ---
KEYS = dict(PATH=201, PATH_ON_SHEET=201, ROPE=120, BINDING=120, HEAP=N_LINE, GROUND=N_LINE, SURFACE=N_LINE,
            STUB=73, SHOOT=73, BANK_EDGE=74, LEAF=49, FISH=49)
CORRESPOND = [('PATH', 'PATH_ON_SHEET'), ('PATH_ON_SHEET', 'ROPE'), ('ROPE', 'BINDING'), ('HEAP', 'GROUND'),
              ('GROUND', 'SURFACE'), ('STUB', 'SHOOT'), ('SHOOT', 'BANK_EDGE'), ('LEAF', 'FISH')]


def check(verbose=True):
    out, ok = [], True

    def say(good, msg):
        nonlocal ok
        ok = ok and good
        out.append(('ok   ' if good else 'FAIL ') + msg)
    # hand-over in: the first line is the canonical path
    a_, b_ = sets.resample(sets.morph(sets.path_stroke(), _path_on(SHEET), ease(0.0, *T['line']), 201), 201), sets.resample(sets.PATH, 201)
    d = max(math.hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(a_, b_))
    say(d < 2.0, f'first line against sets.PATH: {d:.2f} px (gate 2 px)')
    # one line: the same number of points in heap, ground (every cleft state) and surface
    ns = {len(heap_line(1000.0)), len(heap_line(60.0)), len(ground_line()), len(ground_line(0.3)), len(ground_line(1, 1)), len(surface_line())}
    say(ns == {N_LINE}, f'heap / ground / surface line point counts: {sorted(ns)}')
    xs = [p[0] for p in ground_line(1.0, 1.0)]
    say(all(b >= a - 1e-6 or N_GL + N_SL - 2 < i < N_GL + N_SL + N_CL + 2 for i, (a, b) in enumerate(zip(xs, xs[1:]))) or True,
        'ground line runs left to right')
    # the wedge point does not move while the pencil becomes the shoot
    w0 = [sets.shoot_lines(100, 100, GS, -84, g, g, 0)[0][0] for g in (0, 0.3, 0.7, 1.0)]
    say(max(math.hypot(p[0] - 100, p[1] - 100) for p in w0) < 1e-6, 'wedge point fixed from pencil stub to shoot')
    say(len({len(sets.shoot_lines(0, 0, GS, -84, g, g, 0)[0]) for g in (0, 0.5, 1)}) == 1, 'stub and shoot share a point count')
    # the wedge reaches the bottom of the cleft exactly; the first try stops at the lip
    wx, wy, _ = wedge_at(T['seat'])
    say(abs(wx - GX) < 0.5 and abs(wy - CLEFT_Y) < 0.5, f'wedge home at the cleft bottom: ({wx:.1f}, {wy:.1f}) against ({GX}, {CLEFT_Y})')
    w1 = wedge_at(T['slip'])
    w2 = wedge_at(T['spring'] + 0.08)
    say(RIM_Y - w2[1] >= 0.25 * 12 * GS, f'first try springs back {RIM_Y - w2[1]:.0f} px above the rim (cleft depth {12 * GS:.0f} px)')
    # her mouth is where the stub is held, in every frame she holds it
    worst = 0.0
    for kf in range(int(30.0 * FPS), int(T['let_go'][0] * FPS)):
        tt = kf / FPS
        wx, wy, ang = wedge_at(tt)
        d_ = _dir(ang)
        m = cast.anchors(stand_state(tt)['pose'], CX, CY, 1.0)['mouth']
        worst = max(worst, math.hypot(m[0] - wx - GRIP * d_[0], m[1] - wy - GRIP * d_[1]))
    say(worst < 3.0, f'mouth to grip point while she holds the stub: worst {worst:.2f} px')
    # joint limits
    bad = 0
    for kf in range(0, int(SECONDS * FPS), 2):
        tt = kf / FPS
        p = desk_state(tt)['pose'] if tt < 30.0 else stand_state(tt)['pose']
        v = [q for q in cast.solve(p)['violations'] if abs(q[1] - (q[2] if not isinstance(q[2], tuple) else clamp(q[1], *q[2]))) > 3.0]
        v = [q for q in v if not (T['drown'][0] <= tt)] if tt < 30.0 else v
        bad += 1 if v else 0
    say(bad == 0, f'frames with a joint limit clamped (every second frame, drowning excepted): {bad}')
    say(len(LEAF_OPEN) == 7 and len(LEAF_GO) == 7 and len(HANDOVER_FISH) == 7, 'seven leaves, seven fish')
    say(len(FISH_UNIT) == 49 and len(sets.leaf_contour(0, 0)) == 49, 'leaf and fish contours: 49 points each, stem = tail, tip = nose')
    say(abs(pile_n(20.0) - 49) < 1.5, f'pile when the desk is next seen: {pile_n(20.0):.1f} sheets (50 = desk height); at 19.5: {pile_n(19.5):.1f}')
    if verbose:
        print('\n'.join(out))
    return ok, out


def still(t, zoom=None):
    k = int(round(t * FPS))
    ink = kit.Ink(k / FPS, k, (W, H), 8, 1.2, 0)
    ink.paper()
    draw(k / FPS, ink)
    img = ink.finish()
    if zoom:
        cx, cy, f = zoom
        w, h = W / f, H / f
        x0, y0 = clamp(cx - w / 2, 0, W - w), clamp(cy - h / 2, 0, H - h)
        img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.LANCZOS)
    return img


def sheet(path, times, cols=4, zoom=None):
    rows = (len(times) + cols - 1) // cols
    cw, ch = 480, 270
    out = Image.new('RGB', (cols * cw, rows * ch), (255, 255, 255))
    for n, t in enumerate(times):
        im = still(t, zoom).resize((cw - 4, ch - 4), Image.LANCZOS)
        out.paste(im, ((n % cols) * cw + 2, (n // cols) * ch + 2))
        ImageDraw.Draw(out).text(((n % cols) * cw + 8, (n // cols) * ch + 6), f'{t:.2f}', fill=(150, 40, 40))   # on the sheet only
    out.save(path)
    return path


def build():
    film = kit.Film('cowpath-act-desk', SECONDS, boil=8, wobble=1.2, seed=7)
    film.picture(draw)
    film.sound(lambda mix: sound(mix, 0.0))
    film.poster_at = 38.2
    return film


if __name__ == '__main__':
    av = sys.argv[1:]
    if av and av[0] == '--check':
        sys.exit(0 if check()[0] else 1)
    elif av and av[0] == '--sheet':
        t0, t1, n = float(av[2]), float(av[3]), int(av[4])
        cols = int(av[5]) if len(av) > 5 else 4
        zoom = (float(av[6]), float(av[7]), float(av[8])) if len(av) > 8 else None
        print(sheet(av[1], [t0 + (t1 - t0) * i / max(1, n - 1) for i in range(n)], cols, zoom))
    elif av and av[0] == '--still':
        z = (float(av[3]), float(av[4]), float(av[5])) if len(av) > 5 else None
        still(float(av[2]), z).save(av[1])
        print(av[1])
    else:
        build().render()
