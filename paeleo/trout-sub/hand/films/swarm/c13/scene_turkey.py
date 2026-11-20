"""c13 · scene_turkey · Turkey thinks (board beats B0 to B3, film 20.0 to 40.5 s; times here from 0).

B0   0.0- 3.0  A.'s pick: the card is laid on the glass, the pencil loops clockwise in the dashed ring, the red
               circle presses in and lights, the card leaves and the red disc stays behind and settles on the bell.
B1   3.0- 8.0  bolt 1 · die 1 · "The dinner bell to go off."  The upper trout takes the knot, pulls once to the
               left, the bell kicks right, two late strikes, ripple rings, both trout turn to the tin.
B2   8.0-14.0  bolt 2 · die 2 · "The dinner bell goes off and the fish go crazy."  One pull, then a wheel of
               seven trout stampedes clockwise round the glass, single file, belly-up and rolling-eyed.
B3  14.0-20.5  bolt 3 · die 3 · "The fish go quiet and calm."  The wheel slows, each trout halts at a clock place
               clockwise from twelve, the last holds the clapper, the rings go back into the bell, nothing
               outside moves. Only Turkey still shakes.

All seen from Turkey's seat through the brass porthole, the bell's dome over his reflection, gauge low right.
Exposes SECONDS, CAPTIONS, draw(t, ink). Uses only world.py and the kit. Captions are drawn by the editor.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402
from kit import Ink, W, H, FPS, clamp, ramp, ease, smooth, lerp, lerp2     # noqa: E402,F401

SECONDS = 20.5
CAPTIONS = [
    (3.3, 7.7, "The dinner bell to go off."),
    (8.3, 13.7, "The dinner bell goes off and the fish go crazy."),
    (14.4, 20.0, "The fish go quiet and calm."),
]

C = w.PORT_C
R = w.PORT_R
DOME = (480, 400)                  # Turkey's reflection, under the bell's dome
DOME_PILOT = (480, 385)            # ... where the pilot's last shot left it (B0 eases from there behind the card)
REFL_H = 230
BEAK = (DOME[0] + 46, DOME[1] - 62)
CORD = 70                          # the cord, taken up a little so the knot hangs clear of his crest
L_LEAD = 140                       # the two trout of the drawing
L_CROWD = 116                      # the ones that pour in for bolt 2
MOUTH = 0.47                       # mouth is this far ahead of a trout's centre, in lengths
N_FISH = 7
GAP = 360.0 / N_FISH
WHEEL_R = 170.0
SLOW = 22.0                        # degrees a second: the procession the wheel calms down to

S1, S2, S3 = 3.0, 8.0, 14.0        # the three bolts begin (each behind one clockwise sweep of the brass arm)
SWEEP = 0.45

_DUMMY = Ink(0.0, 0)
KNOT0 = w.bell(_DUMMY, part="cord", cord_len=CORD)["knot"]          # the knot with the bell at rest


# ------------------------------------------------------------- small pieces ---
def _vec(h):
    a = math.radians(h)
    return math.sin(a), -math.cos(a)


def _circ(c, r, a):
    """Pose of a trout on the clockwise circuit: (x, y, compass heading)."""
    x, y = w.clock_xy(c, r, a)
    return x, y, a + 90.0


def fish(ink, x, y, h, length, roll=False, **kw):
    """A trout at (x, y) swimming on compass heading h (0 up, clockwise). It keeps its back up, so when its
    heading passes the vertical it has to roll over: with roll=True it turns edge-on through that moment."""
    dx, dy = _vec(h)
    phi = math.degrees(math.atan2(dy, dx))
    flip = dx >= 0
    ang = -phi if flip else -(phi - 180.0)
    spr = w.trout_sprite(length, kw.get("phase", 0.0), kw.get("amp", 8.0), kw.get("lid", 0.0), kw.get("eye_roll"),
                         kw.get("belly_up", False))
    if roll:
        f = clamp(abs(dx) / 0.15)
        if f < 1:
            spr = spr.resize((spr.width, max(5, int(spr.height * max(0.2, f)))), Image.BILINEAR)
    w.put(ink, spr, x, y, angle=ang, flip=flip)


def _mouth_to_centre(mouth, h, length):
    dx, dy = _vec(h)
    return mouth[0] - MOUTH * length * dx, mouth[1] - MOUTH * length * dy


def _stage_back(ink, t, lean=0.0, sway=1.0):
    w.river(ink, t)
    w.weed(ink, 250, 470, 200, lean * 0.6, t, seed=3, n=4, sway=sway, dark=0.55)
    w.weed(ink, 716, 474, 170, lean * 0.6, t, seed=4, n=4, sway=sway, dark=0.55)
    w.arch(ink, part="right")
    w.arch(ink, part="lintel")
    w.twig(ink)


def _stage_front(ink, t, lean=0.0, sway=1.0):
    w.arch(ink, part="left")
    w.weed(ink, 336, 482, 120, lean, t, seed=1, n=5, sway=sway)
    w.weed(ink, 642, 486, 150, lean, t, seed=2, n=6, sway=sway)


def _shiver(ink, t, strikes):
    """The glass shivers for a few frames after each strike."""
    amp = 0.0
    for ts in strikes:
        if 0 <= t - ts < 0.3:
            amp = max(amp, 3.5 * math.exp(-(t - ts) * 10))
    if amp > 0.6:
        k = int(round(t * FPS))
        ink.img = ImageChops.offset(ink.img, int(round(amp)) * (1 if k % 2 else -1), 0)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _grit(ink, t, strikes):
    """Grit jumps off the arch at a strike and falls."""
    for n, ts in enumerate(strikes):
        x = t - ts
        if not 0 < x < 0.9:
            continue
        for k in range(9):
            sx = 350 + 29 * k + 11 * math.sin(k * 2.3 + n)
            sy = 136 + 48 * abs(math.sin(k * 1.31 + 0.4)) + (k % 3) * 5
            px = sx + (10 + 3 * k % 7) * x
            py = sy - 46 * x + 150 * x * x
            r = 2.2 - x
            ink.d.ellipse([px - r, py - r, px + r, py + r], fill=w.PAL["stone_dk"] + (int(230 * (1 - x / 0.9)),))


def _rings(ink, mouth, t, strikes, life=2.4, back=0.0, speed=170.0):
    radii = [(16 + speed * (t - ts)) * (1 - back) for ts in strikes if 0 < t - ts < life]
    w.ripple_rings(ink, mouth, radii)


def _flash(t, strikes):
    return max([math.exp(-(t - ts) * 7) for ts in strikes if 0 <= t - ts < 0.6] or [0.0])


def _finish(ink, t, n, gauge, tremble, mood, bubble_fn=None, strikes=()):
    w.turkey_reflection(ink, DOME[0], DOME[1], REFL_H, mood, t, alpha=0.85)
    if bubble_fn:
        bubble_fn()
    _shiver(ink, t, strikes)
    w.seat_frame(ink)
    w.gauge(ink, gauge, tremble=tremble, t=t)
    w.bolt_mark(ink, n, size=38)


# ------------------------------------------------- the pull and the kick ---
def _pk_swing(t, tg, tr):
    if t < tg:
        return 0.0
    if t < tr:
        return -6.0 * ease(t, tg, tr - 0.1)
    x = t - tr
    return 30.0 * math.exp(-1.2 * x) * math.sin(7.0 * x) - 6.0 * math.exp(-10 * x)


def _pk_clap_target(t, tg, tr):
    if t < tr:
        return -16.0 * ease(t, tg, tr - 0.1)
    return _pk_swing(t, tg, tr)


def _pk_cord_target(t, tg, tr):
    if t < tr:
        return -38.0 * ease(t, tg, tr - 0.08)
    return _pk_swing(t, tg, tr)


def _peaks(rel_fn, t0, t1, floor):
    """Times of the local maxima of |rel| above floor: the frames the late clapper is hardest against the wall."""
    out, k0, k1 = [], int(t0 * FPS), int(t1 * FPS)
    for k in range(k0 + 1, k1 - 1):
        a, b, c = (abs(rel_fn(j / FPS)) for j in (k - 1, k, k + 1))
        if b > floor and b >= a and b > c:
            out.append(k / FPS)
    return out


def _lead_in(t, t0, tg):
    """The upper trout, whose turn it is, leaves its drawing place and comes round clockwise, over the top and
    down behind the bell, to the knot: heading west with its mouth on it."""
    e = ease(t, t0, tg)
    c = lerp2((480, 290), (KNOT0[0] + MOUTH * L_LEAD, KNOT0[1] - 90), e)
    return _circ(c, lerp(72, 90, e), lerp(-42, 180, e))


def _hold_heading(t, tg, tr):
    return 270.0 + 12.0 * ease(t, tg, tr)


def _knot_at(sw, cl, co, hoist=0.0):
    return w.bell(_DUMMY, swing=sw, clapper=cl, cord=co, part="cord", hoist=hoist, cord_len=CORD)["knot"]


def _low_in(t, t0, t1):
    """The lower trout goes round under the dome to the waiting place at nine o'clock and stops there."""
    e = ease(t, t0, t1)
    c = lerp2((480, 290), C, e)
    return _circ(c, lerp(90, 162, e), lerp(108, WAIT_A, e))


WAIT_A = 258.0                     # the waiting place (nine o'clock), nose up, mouth shut


# ====================================================================== B0 ===
CARD_C = (480, 208)
T_CARD_IN = (0.0, 0.55)
T_LOOP = (0.75, 1.55)
T_PRESS = (1.6, 1.9)
T_CARD_OUT = (2.15, 2.85)
T_DISC = (2.3, 2.95)               # the red disc that stayed behind drifts onto the bell
BELL_DISC = (476, 206.5)


def _b0(ink, t):
    _stage_back(ink, t)
    x1, y1 = w.trout_on_circle(ink, (480, 306), 132, 450, L_LEAD + 10, amp=0.0, lid=0.45)
    settle = ease(t, 0.7, 2.0)                         # behind the card: the cord is taken up, he sinks a little
    w.bell(ink, part="cord", cord_len=lerp(92, CORD, settle))
    _stage_front(ink, t)
    w.bell(ink, part="body", disc="circle" if t >= T_DISC[1] else None)
    w.trout_on_circle(ink, (480, 306), 132, 270, L_LEAD + 10, amp=0.0, lid=0.45)
    w.speech_bubble(ink, (x1 - 10, y1 - 92), 0.62, shadow=0.5)
    w.turkey_reflection(ink, DOME[0], lerp(DOME_PILOT[1], DOME[1], settle), REFL_H, "flap", t, alpha=0.85)
    w.seat_frame(ink)
    w.gauge(ink, 5.0, tremble=0.4, t=t)

    # the card: slid in turning clockwise, laid, and taken away still turning clockwise
    ein, eout = ease(t, *T_CARD_IN), ease(t, *T_CARD_OUT)
    press = ease(t, *T_PRESS)
    loop = ramp(t, *T_LOOP)
    red = None
    if eout < 1:
        cc = (CARD_C[0] - 520 * (1 - ein) ** 1.6 + 640 * eout ** 1.8, CARD_C[1] - 150 * (1 - ein) ** 1.6 + 250 * eout ** 1.8)
        r = w.pick_card(ink, cc, side="turkey", picked="circle", press=press, loop=loop,
                        angle=-2.0 + 24 * (1 - ein) - 26 * eout, initial="A.", lift=max(1 - ein, eout))
        red = r["buttons"]["circle"]
        if T_LOOP[0] - 0.3 < t < T_LOOP[1] + 0.35 and (r["tip"] or r["ring"]):
            tip = r["tip"] or (r["ring"][0], r["ring"][1] - 22)
            lift = max(1 - ramp(t, T_LOOP[0] - 0.3, T_LOOP[0]), ramp(t, T_LOOP[1], T_LOOP[1] + 0.35))
            a = math.radians(40 * ramp(t, T_LOOP[1], T_LOOP[1] + 0.35))
            tip = (tip[0] + 260 * lift * lift * math.cos(a), tip[1] - 120 * lift * lift + 200 * lift * lift * math.sin(a))
            w.pencil(ink, tip, 50, lift=lift)
    # the red circle stays behind on the glass as a small disc, then settles on the bell (a clockwise curl)
    if press > 0.5 and t < T_DISC[1]:
        home = _RED_HOME
        f = ease(t, *T_DISC)
        p = lerp2(home, BELL_DISC, f)
        bow = 34 * math.sin(math.pi * f)
        w.button_disc(ink, "circle", p[0] - bow * 0.5, p[1] - bow, r=lerp(15, 9, f), alpha=ease(t, T_PRESS[1], T_CARD_OUT[0] + 0.1))


def _red_home():
    r = w.pick_card(_DUMMY, CARD_C, side="turkey", picked="circle", press=1.0, loop=1.0, angle=-2.0, initial="A.")
    return r["buttons"]["circle"]


_RED_HOME = _red_home()


# ====================================================================== B1 ===
TG1, TR1 = 4.45, 5.3               # the knot is taken; the knot is let go


def _swing1(t):
    return _pk_swing(t, TG1, TR1)


_clap1 = w.Follower(lambda t: _pk_clap_target(t, TG1, TR1), SECONDS, f=1.7, zeta=0.22)
_cord1 = w.Follower(lambda t: _pk_cord_target(t, TG1, TR1), SECONDS, f=1.3, zeta=0.3)
STRIKES1 = _peaks(lambda t: _clap1.at(t) - _swing1(t), TR1, TR1 + 1.6, 12.0)[:2]
assert len(STRIKES1) == 2, STRIKES1

_HR = _hold_heading(TR1, TG1, TR1)                 # 282: heading when the knot is let go
_PR1 = _mouth_to_centre(_knot_at(_swing1(TR1), _clap1.at(TR1), _cord1.at(TR1)), _HR, L_LEAD)
_AR = _HR - 90.0
_RR1 = 104.0
_CR1 = (_PR1[0] - _RR1 * math.sin(math.radians(_AR)), _PR1[1] + _RR1 * math.cos(math.radians(_AR)))
_AEND1 = 292.0
T_AWAY1 = (TR1, TR1 + 1.35)
T_LOOK1 = (6.75, 7.45)             # the upper trout turns to the tin
T_LOOK1B = (7.0, 7.65)             # then the waiting one, without leaving nine o'clock
_PEND1 = w.clock_xy(_CR1, _RR1, _AEND1)


def _look_heading(p, h_from):
    """Compass heading from p to Turkey (the tin), reached from h_from by turning clockwise only."""
    tgt = (DOME[0] + 6, DOME[1] - 40)
    h = math.degrees(math.atan2(tgt[0] - p[0], -(tgt[1] - p[1])))
    while h < h_from:
        h += 360.0
    return h


_H_LOOK1 = _look_heading(_PEND1, _AEND1 + 90.0)
_PWAIT = w.clock_xy(C, 162, WAIT_A)
_H_LOOKB = _look_heading(_PWAIT, WAIT_A + 90.0)


def _lead1(t, knot):
    """(x, y, heading, state) of the upper trout in bolt 1."""
    if t < TG1:
        return _lead_in(t, S1 + 0.15, TG1) + ("TURN",)
    if t < TR1:
        h = _hold_heading(t, TG1, TR1)
        return _mouth_to_centre(knot, h, L_LEAD) + (h, "RING")
    x = ramp(t, *T_AWAY1)
    a = lerp(_AR, _AEND1, 1 - (1 - x) ** 2)
    px, py, h = _circ(_CR1, _RR1, a)
    if t > T_LOOK1[0]:
        h = lerp(_AEND1 + 90.0, _H_LOOK1, ease(t, *T_LOOK1))
    return px, py, h, "LOOK_AT_TIN"


def _low1(t):
    if t < S1 + 1.35:
        return _low_in(t, S1 + 0.1, S1 + 1.35) + ("QUEUE",)
    h = lerp(WAIT_A + 90.0, _H_LOOKB, ease(t, *T_LOOK1B))
    return _PWAIT[0], _PWAIT[1], h, ("QUEUE" if t < T_LOOK1B[0] else "LOOK_AT_TIN")


def _gauge1(t):
    return 5.0 - ease(t, STRIKES1[0] + 0.25, STRIKES1[0] + 0.85)


def _b1(ink, t):
    sw, cl, co = _swing1(t), _clap1.at(t), _cord1.at(t)
    _stage_back(ink, t)
    knot = _knot_at(sw, cl, co)
    x, y, h, st = _lead1(t, knot)
    moving = st == "TURN" or (st == "LOOK_AT_TIN" and t < T_AWAY1[1])
    kw = dict(phase=t * 7, amp=8.0 if moving else 0.0, lid=0.45 if t > T_LOOK1[0] else 0.12)
    if st == "TURN":                                   # it passes behind the bell and its cord
        fish(ink, x, y, h, L_LEAD, roll=True, **kw)
    b = w.bell(ink, swing=sw, clapper=cl, cord=co, part="cord", cord_len=CORD)
    _stage_front(ink, t)
    fl = _flash(t, STRIKES1)
    w.bell(ink, swing=sw, clapper=cl, cord=co, part="body", disc="circle", flash=fl)
    if st != "TURN":
        fish(ink, x, y, h, L_LEAD, roll=True, **kw)
    lx, ly, lh, lst = _low1(t)
    fish(ink, lx, ly, lh, L_LEAD, roll=t > T_LOOK1B[0], phase=t * 7, amp=8.0 if t < S1 + 1.35 else 0.0,
         lid=0.45 if t > T_LOOK1B[0] else 0.12)
    w.speech_bubble(ink, _bubble_tail(x, y, h), 0.5, shadow=0.5)
    _rings(ink, b["mouth"], t, STRIKES1)
    _grit(ink, t, STRIKES1)
    gasp = STRIKES1[0] < t < STRIKES1[0] + 1.0
    _finish(ink, t, 1, _gauge1(t), 1.0 if gasp else 0.3, "gasp" if gasp else "freak",
            lambda: w.bubbles(ink, BEAK, t, STRIKES1[0] + 0.1, n=8, rise=150.0, curl=90.0, size=7.0), STRIKES1)


def _bubble_tail(x, y, h):
    """"haha verry funny" stays pinned to the upper trout: it is towed behind it wherever it goes."""
    dx, dy = _vec(h)
    px, py = x - 0.72 * L_LEAD * dx, y - 0.72 * L_LEAD * dy - 12          # towed just behind its tail
    d = math.hypot(px - C[0], py - C[1])
    if d > 140:
        px, py = C[0] + (px - C[0]) * 140 / d, C[1] + (py - C[1]) * 140 / d
    return px, py


# ================================================================ B2 and B3 ===
TG2, TR2 = 8.9, 9.3
T0 = 15.0                          # bolt 3: the first trout halts at twelve
STEP = (60.0 - GAP) / SLOW         # ... and each next one this much later, clockwise
T_LEAVE = 15.25                    # the upper trout leaves the ring for the bell
T_HOLD = 17.75                     # it has the clapper in its mouth
T_GONE = T_HOLD + 0.7              # the rings are back in the bell
T_STILL = T_GONE + 0.05            # from here nothing outside moves at all


def _omega(t, peak):
    if t < TR2:
        return 0.0
    if t < S3:
        return 130.0 + (peak - 130.0) * ease(t, TR2 + 0.2, TR2 + 1.5)
    return peak + (SLOW - peak) * ease(t, S3, T0)


def _table(peak):
    n = int((SECONDS + 0.5 - TR2) * 96) + 2
    out, a = [], _AR
    for k in range(n):
        out.append(a)
        a += _omega(TR2 + (k + 0.5) / 96.0, peak) / 96.0
    return out


def _solve_peak():
    """Choose the wheel's top speed so that the rear trout comes to twelve o'clock exactly at T0."""
    best, bp = 1e9, 330.0
    for q in range(0, 1200):
        peak = 300.0 + q * 0.07
        a = _table(peak)[int(round((T0 - TR2) * 96))] - GAP * (N_FISH - 1)
        d = abs((a + 180.0) % 360.0 - 180.0)
        if d < best:
            best, bp = d, peak
    return bp


PEAK = _solve_peak()
_ALEAD = _table(PEAK)


def a_lead(t):
    """Clock angle (unwrapped, only ever increasing) of the wheel's front slot from the moment the knot is let go."""
    k = clamp((t - TR2) * 96.0, 0, len(_ALEAD) - 1.001)
    i = int(k)
    return _ALEAD[i] + (_ALEAD[i + 1] - _ALEAD[i]) * (k - i)


def _smin(a, g, s=2.5):
    x = (g - a) / s
    if x > 40:
        return a
    if x < -40:
        return g
    return g - s * math.log1p(math.exp(x))


def _smax(a, g, s=2.5):
    return -_smin(-a, -g, s)


_GOAL = {k: a_lead(T0) - GAP * k + (60.0 - GAP) * (N_FISH - 1 - k) for k in range(1, N_FISH)}
_TSTOP = {k: T0 + STEP * (N_FISH - 1 - k) for k in range(1, N_FISH)}
for _k in range(1, N_FISH):
    assert abs((_GOAL[_k] - 60.0 * (N_FISH - 1 - _k) + 180.0) % 360.0 - 180.0) < 1.5, (_k, _GOAL[_k])


def _wheel_fish(k, t):
    """(x, y, heading, clock angle) of trout k (1 = the lower trout of the drawing, 2..6 the crowd) from TR2 on."""
    a = _smin(a_lead(t) - GAP * k, _GOAL[k])
    if k == 1:
        a = _smax(a, WAIT_A) if a < WAIT_A + 30 else a
        r = lerp(162.0, WHEEL_R, ease(a, WAIT_A, WAIT_A + 50))
    else:
        r = WHEEL_R + 175.0 * (1 - ease(a, 188.0, 262.0))          # they pour in from behind the left pillar
    r += 13.0 * _crazy(t) * math.sin(t * 13.0 + k * 2.1)            # crazy: they buck in and out, still in file
    x, y, h = _circ(C, r, a)
    return x, y, h, a


def _thrash(t, k, q):
    """Crazy: the trout throw their heads from side to side. Their place in the file does not change."""
    return 26.0 * q * math.sin(t * 17.0 + k * 1.7)


def _froth(ink, x, y, h, t, k, q):
    """The water each crazy trout churns up behind its tail."""
    if q < 0.15:
        return
    dx, dy = _vec(h)
    for j in range(6):
        ph = (t * 2.6 + j * 0.37 + k * 0.21) % 1.0
        d = 62 + 46 * ph
        side = 12 * math.sin(j * 2.4 + k) * (0.5 + ph)
        px, py = x - dx * d - dy * side, y - dy * d + dx * side
        r = (2.2 + 2.2 * ph) * q
        ink.d.ellipse([px - r, py - r, px + r, py + r], outline=(240, 250, 244, int(220 * q * (1 - ph))), width=2)


def _swing23(t):
    amp = 17.0 * ease(t, 10.1, 10.9) * (1 - 0.5 * ease(t, 14.6, T_HOLD)) * (1 - ease(t, T_HOLD, T_HOLD + 0.3))
    return _pk_swing(t, TG2, TR2) + amp * math.sin(2 * math.pi * 2.1 * (t - 10.1))


_clap23f = w.Follower(lambda t: _pk_clap_target(t, TG2, TR2) + (_swing23(t) - _pk_swing(t, TG2, TR2)), SECONDS + 0.5, f=2.7, zeta=0.16)
_cord23f = w.Follower(lambda t: _pk_cord_target(t, TG2, TR2) + (_swing23(t) - _pk_swing(t, TG2, TR2)), SECONDS + 0.5, f=1.3, zeta=0.3)


def _clap23(t):
    return lerp(_clap23f.at(t), _swing23(t), ease(t, T_HOLD - 0.2, T_HOLD))


def _cord23(t):
    return _cord23f.at(t) * (1 - ease(t, T_HOLD, T_HOLD + 0.6))


def _hoist(t):
    return 0.75 * ease(t, 10.2, 12.2)


STRIKES23 = [s for s in _peaks(lambda t: _clap23(t) - _swing23(t), TR2 + 0.08, T_HOLD - 0.1, 11.0)]
STRIKES2 = STRIKES23[:1]

_PR2 = _mouth_to_centre(_knot_at(_swing23(TR2), _clap23(TR2), _cord23(TR2)), _HR, L_LEAD)
_CR2 = (_PR2[0] - 90.0 * math.sin(math.radians(_AR)), _PR2[1] + 90.0 * math.cos(math.radians(_AR)))

# bolt 3: the upper trout spirals in to the clapper
CLAPPER0 = (480, 257)
_HF = 285.0
_PF = _mouth_to_centre(CLAPPER0, _HF, L_LEAD)
_RF = 40.0
_AF0 = _HF - 90.0
_CF = (_PF[0] - _RF * math.sin(math.radians(_AF0)), _PF[1] + _RF * math.cos(math.radians(_AF0)))
_A_LEAVE = a_lead(T_LEAVE)
_AF = _AF0
while _AF < _A_LEAVE + 150.0:
    _AF += 360.0


def _lead23(t, knot):
    """(x, y, heading, state) of the upper trout in bolts 2 and 3."""
    if t < TG2:
        return _lead_in(t, S2 + 0.05, TG2) + ("TURN",)
    if t < TR2:
        h = _hold_heading(t, TG2, TR2)
        return _mouth_to_centre(knot, h, L_LEAD) + (h, "RING")
    if t < T_LEAVE:
        e = ease(t, TR2, TR2 + 0.9)
        return _circ(lerp2(_CR2, C, e), lerp(90.0, WHEEL_R, e), a_lead(t)) + ("CRAZY",)
    x = smooth(ramp(t, T_LEAVE, T_HOLD))
    e = ease(t, T_LEAVE, T_LEAVE + 1.0)                 # it comes off the ring at once, inside the parked ones
    return _circ(lerp2(C, _CF, e), lerp(WHEEL_R, _RF, e), lerp(_A_LEAVE, _AF, x)) + ("CALM",)


def _low_pre(t):
    return _low_in(t, S2 + 0.05, S2 + 0.85)


def _crazy(t):
    return ease(t, TR2 + 0.3, TR2 + 1.4) * (1 - ease(t, S3 + 0.1, T0 - 0.1))


def _swim_phase():
    out, p = [], 0.0
    for k in range(int(SECONDS * FPS) + 3):
        out.append(p)
        p += (6.0 + 9.0 * _crazy(k / FPS)) / FPS
    return out


_PHASE = _swim_phase()

_lean = w.Follower(lambda t: 64.0 * clamp((_omega(t, PEAK) - SLOW) / (PEAK - SLOW)) if t >= TR2 else 0.0,
                   SECONDS + 0.5, f=0.9, zeta=0.8)


def _lean_at(t):
    return _lean.at(t) * (1 - ease(t, T0, T_HOLD))


def _gauge2(t):
    return 5.0 - ease(t, TR2 + 0.3, TR2 + 1.1) - ease(t, 11.6, 12.5)


def _gauge3(t):
    return 5.0 - ease(t, 18.95, 19.55)


def _wheel_scene(ink, t, bolt):
    """Bolts 2 and 3 are one piece of water: bolt 3 opens on bolt 2's wheel still turning."""
    tw = min(t, T_STILL)                                # the river's own clock stops when everything has stopped
    sway = 1.0 - ease(t, T0, T_HOLD)
    lean = _lean_at(t)
    sw, cl, co, ho = _swing23(t), _clap23(t), _cord23(t), _hoist(t)
    q = _crazy(t)
    ph = _PHASE[min(len(_PHASE) - 1, int(round(t * FPS)))]

    _stage_back(ink, tw, lean, sway)
    knot = _knot_at(sw, cl, co, ho)
    x, y, h, st = _lead23(t, knot)
    held = t >= T_HOLD
    still0 = ease(t, T_HOLD - 0.25, T_HOLD + 0.35)
    lkw = dict(phase=ph, amp=lerp(8.0, 22.0, q) * (1 - still0) if st != "RING" else 0.0,
               lid=0.8 * still0 if st == "CALM" else 0.1,
               eye_roll=(t * 500) if q > 0.5 else None)
    if st == "TURN":
        fish(ink, x, y, h, L_LEAD, roll=True, **lkw)
    b = w.bell(ink, swing=sw, clapper=cl, cord=co, part="cord", hoist=ho, cord_len=CORD)
    _stage_front(ink, tw, lean, sway)
    strikes = STRIKES23 if (bolt == 3 or t > 10.0) else STRIKES2
    fl = _flash(t, strikes)
    w.bell(ink, swing=sw, clapper=cl, cord=co, part="body", disc="circle", flash=fl, hoist=ho)

    back = ease(t, T_HOLD + 0.05, T_GONE)
    if back < 1:
        _rings(ink, b["mouth"], t, strikes, life=1.7 if t > 10.0 else 2.4, back=back)

    # the others: single file, all clockwise, nobody overtakes
    if t < TR2:
        lx, ly, lh = _low_pre(t)
        fish(ink, lx, ly, lh, L_LEAD, phase=t * 7, amp=8.0 if t < S2 + 0.85 else 0.0, lid=0.12)
    else:
        for k in range(N_FISH - 1, 0, -1):
            fx, fy, fh, fa = _wheel_fish(k, t)
            if math.hypot(fx - C[0], fy - C[1]) > R + 80:
                continue
            still = ease(t, _TSTOP[k] - 0.15, _TSTOP[k] + 0.5)
            waiting = k == 1 and fa < WAIT_A + 2
            _froth(ink, fx, fy, fh, t, k, q)
            fish(ink, fx, fy, fh + _thrash(t, k, q), L_LEAD if k == 1 else L_CROWD, roll=not waiting,
                 phase=ph + k * 1.3, amp=0.0 if waiting else lerp(8.0, 22.0, q) * (1 - still),
                 lid=0.8 * still if t > S3 else 0.1,
                 eye_roll=(t * 500 + k * 60) if q > 0.5 else None,
                 belly_up=(q > 0.5 and k in (2, 5)))
    if st != "TURN":
        if st == "CRAZY":
            _froth(ink, x, y, h, t, 0, q)
        fish(ink, x, y, h + (_thrash(t, 0, q) if st == "CRAZY" else 0.0), L_LEAD, roll=not held, **lkw)

    # "haha verry funny": towed behind the upper trout like a kite, then it settles and lies still
    if t < TR2:
        tail = _bubble_tail(x, y, h)
        ang = 0.0
    else:
        lag = 0.16 * q
        bx, by, bh, _ = _lead23(t - lag, knot)
        dc = math.hypot(bx - C[0], by - C[1]) or 1.0
        inward = ((C[0] - bx) / dc * 52, (C[1] - by) / dc * 52)
        up = _bubble_tail(bx, by, bh)
        tail = lerp2(up, (bx + inward[0], by + inward[1]), q)
        if st == "CALM":                                # it settles clear of the bell, over the trout's back
            tail = lerp2(tail, (642, 262), smooth(ramp(t, T_LEAVE + 0.8, T_HOLD)))
        ang = 14.0 * math.sin(t * 11.0) * q
    w.speech_bubble(ink, tail, 0.5, angle=ang, shadow=0.5)

    if bolt == 2:
        mood = "freak" if t < TR2 + 0.25 else "flap"

        def bub():
            for ts in (TR2 + 0.2, 10.9, 12.3):
                w.bubbles(ink, BEAK, t, ts, n=8, rise=150.0, curl=90.0, size=7.0)
        _finish(ink, t, 2, _gauge2(t), 1.0 if t > TR2 else 0.3, mood, bub, strikes)
    else:
        mood = "flap" if t < T0 else ("freak" if t < T_HOLD else "frozen")

        def bub():
            w.bubbles(ink, BEAK, t, 14.3, n=7, rise=150.0, curl=90.0, size=7.0)
            w.bubbles(ink, BEAK, t, 17.3, n=7, rise=150.0, curl=90.0, size=7.0, frozen_at=T_STILL)   # they hang where they are
            w.bubbles(ink, (BEAK[0] + 4, BEAK[1]), t, 19.0, n=1, rise=120.0, curl=60.0, size=7.5)      # his one bubble
        _finish(ink, t, 3, _gauge3(t), 1.0 if t > T_HOLD else 0.5, mood, bub, strikes if t < T_HOLD + 0.2 else ())


# ------------------------------------------------------------------- draw ---
def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < S1:
        _b0(ink, t)
    elif t < S1 + SWEEP:
        _b0(ink, t)
        o = w.offscreen(ink)
        _b1(o, t)
        w.sweep(ink, o.img, ramp(t, S1, S1 + SWEEP))
    elif t < S2:
        _b1(ink, t)
    elif t < S2 + SWEEP:
        _b1(ink, t)
        o = w.offscreen(ink)
        _wheel_scene(o, t, 2)
        w.sweep(ink, o.img, ramp(t, S2, S2 + SWEEP))
    elif t < S3:
        _wheel_scene(ink, t, 2)
    elif t < S3 + SWEEP:
        _wheel_scene(ink, t, 2)
        o = w.offscreen(ink)
        _wheel_scene(o, t, 3)
        w.sweep(ink, o.img, ramp(t, S3, S3 + SWEEP))
    else:
        _wheel_scene(ink, t, 3)
    w.badge(ink)


def check():
    """Clockwise Etiquette, numerically (SCION 48): headings and circuit angles only ever increase clockwise,
    one trout has the turn at a time, the waiting trout keeps its place, and at the end nothing outside moves."""
    eps = 1e-6
    # bolt 1
    prev = None
    for k in range(int(S1 * FPS), int(S2 * FPS)):
        tt = k / FPS
        knot = _knot_at(_swing1(tt), _clap1.at(tt), _cord1.at(tt))
        cur = (_lead1(tt, knot)[2], _low1(tt)[2])
        if prev:
            assert cur[0] >= prev[0] - eps and cur[1] >= prev[1] - eps, ("anticlockwise in bolt 1", tt, prev, cur)
        prev = cur
        if _lead1(tt, knot)[3] in ("TURN", "RING") and tt > S1 + 1.35:
            assert _low1(tt)[3] == "QUEUE" and _low1(tt)[:2] == _PWAIT, "the waiting trout left nine o'clock"
    # bolts 2 and 3
    prev = None
    for k in range(int(TR2 * FPS) + 1, int(SECONDS * FPS)):
        tt = k / FPS
        cur = [_lead23(tt, KNOT0)[2]] + [_wheel_fish(j, tt)[3] for j in range(1, N_FISH)]
        if prev:
            for a, b in zip(prev, cur):
                assert b >= a - eps, ("anticlockwise in the wheel", tt)
        if tt < T_LEAVE:
            for j in range(1, N_FISH):                  # single file: nobody overtakes the one in front
                assert cur[j] < cur[j - 1] - 20.0, ("overtaking", tt, j)
        prev = cur
    a0 = [_wheel_fish(j, T_STILL)[3] for j in range(1, N_FISH)]
    a1 = [_wheel_fish(j, SECONDS - 0.05)[3] for j in range(1, N_FISH)]
    assert max(abs(p - q) for p, q in zip(a0, a1)) < 0.05, "a trout still moves in the stillness"
    assert abs(_swing23(T_STILL)) < 0.01 and abs(_cord23(T_STILL)) < 0.01 and _lean_at(T_STILL) == 0.0
    assert SECONDS - T_STILL >= 1.9, "hold nearly two seconds of nothing moving outside"
    assert len(STRIKES1) == 2 and len(STRIKES2) == 1
    for (a, b, s) in CAPTIONS:
        assert b - a >= 2.5 and b <= SECONDS
    assert abs(_gauge1(S2 - 0.01) - 4) < 1e-6 and abs(_gauge2(S3 - 0.01) - 3) < 1e-6 and abs(_gauge3(SECONDS - 0.01) - 4) < 1e-6
    return True


if __name__ == "__main__":
    from kit import Film
    check()
    film = Film("c13_scene_turkey", SECONDS)
    film.picture(draw)
    args = [float(a) for a in sys.argv[1:] if not a.startswith("-")]
    times = args or [0.3, 1.2, 1.8, 2.6, 3.2, 3.9, 4.5, 5.2, 5.6, 6.1, 6.8, 7.8,
                     8.2, 9.0, 9.5, 10.2, 11.0, 12.0, 13.0, 13.8,
                     14.2, 14.9, 15.4, 16.0, 16.8, 17.5, 18.0, 18.6, 19.4, 20.4]
    film.render(preview=times)
