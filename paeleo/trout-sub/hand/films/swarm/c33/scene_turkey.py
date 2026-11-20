"""c33 · scene_turkey · Turkey thinks (board beats T0 to T3, film 20.0 to 38.0 s; times here from 0).

T0   0.0- 2.5  E.'s pick: the card on the table, the pencil colours the red circle in round and round, the button
               presses and lights, the pencil draws one small circle in the dashed ring. Velvet iris. Then Turkey's
               seat: the pencilled circle lies on the glass and the torn-paper stones slide in over it, one by one.
T1   2.5- 7.0  bolt 1 · die 1 · "Someone trapped him."  Eight bars and one gap. A black arm from the right edge
               slides the ninth bar down into the gap, hangs a padlock on the crossbar and withdraws. The lock
               swings twice. Turkey shoves twice; nothing outside shivers. Gauge 5 to 4.
T2   7.0-12.0  bolt 2 · die 2 · "Trying to save a hot Cheeto."  One glowing, fizzing orange curl sinks past the
               glass. Turkey's whole reflection slams up the pane and follows it down, a wing wiping a clear streak
               through the fog. The curl lodges on the crossbar between bars 5 and 6. Gauge 5 to 3.
T3  12.0-18.0  bolt 3 · die 3 · "That's his home."  The camera pushes in through the bars, the planes part: the
               gate (bars 5 and 6) opens to the fish's nose, mat, lamp comes on, the fish turns once in the armchair
               and settles, and its tail draws the two curtains shut. Turkey still shoves. Gauge 5 to 2.

All from Turkey's seat through the brass porthole except the pick card. Scene changes are the velvet iris.
The module opens with the iris opening over the whole frame and ends with it closing over the whole frame.
Exposes SECONDS, CAPTIONS, draw(t, ink). Uses only world.py and the kit. Captions are drawn by the editor.
The breath clock is the film's (film time = 20.0 + t, and 20.0 is a whole number of breaths and shoves).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageDraw, ImageFilter                              # noqa: E402
import world as Wd                                                        # noqa: E402
from kit import clamp, ramp, ease, smooth, lerp, lerp2                    # noqa: E402,F401

SECONDS = 18.0
CAPTIONS = [
    (2.8, 6.7, "Someone trapped him."),
    (7.3, 11.7, "Trying to save a hot Cheeto."),
    (12.3, 17.6, "That's his home."),
]

C = Wd.PORT_C
R = Wd.PORT_R
T_SEAT = 2.1            # the iris is shut here: table -> Turkey's seat
S1, S2, S3 = 2.5, 7.0, 12.0
IRIS = 0.2              # half an iris move
CROSS_V = 0.28           # crossbar height (ring units): in the lit mouth, so the lock and the curl read as silhouettes
HOLE = 0.74              # the far mouth of the tunnel: wide enough that the gap, the arm and the lock stand against light
LOCK = 36                # padlock size
GAP = 6                  # the bar that is missing in bolt 1 (right of centre, in front of the fish) and is slid in
REFL = Wd.STAGE["reflection"]
BEAK = Wd.STAGE["beak"]
BEAK_OFF = (BEAK[0] - REFL[0], BEAK[1] - REFL[1])
FISH = Wd.STAGE["fish"]
FISH_L = Wd.STAGE["fish_len"]
FISH_A = Wd.STAGE["fish_angle"]


def _notches(t, ticks):
    """The needle: 5 at the start of every ending, one whole notch down at each chosen breath."""
    return 5.0 - sum(ease(t, tk, tk + 0.25) for tk in ticks)


def _iris_f(t):
    """Full-frame velvet iris: opens at the module's start, closes and opens at each change, closes at the end."""
    f = 1 - ease(t, 0.0, IRIS)
    for a in (T_SEAT, S2, S3):
        if a - IRIS <= t < a + IRIS:
            f = max(f, ease(t, a - IRIS, a) if t < a else 1 - ease(t, a, a + IRIS))
    return max(f, ease(t, SECONDS - IRIS, SECONDS))


def _cross_y(x, r=R):
    """Top edge of the crossbar at x (this scene hangs it at CROSS_V so lock and curl sit in the light)."""
    return C[1] + CROSS_V * r + (x - C[0]) * math.tan(math.radians(2.0)) - 0.025 * r


def _lock_xy(r=R):
    """Where the padlock hangs: on the crossbar in the slot between bars 5 and 6, against the light."""
    v = CROSS_V + 0.2
    x = (Wd.bar_line(5, v, C, r)[0] + Wd.bar_line(6, v, C, r)[0]) / 2 - 0.01 * r
    return x, _cross_y(x, r) + 7


def _outside(i, t, shift=(0.0, 0.0), fish_kw=None):
    """Far tunnel plane, the fish, the crossbar: everything behind the bars, in the world's draw order."""
    sx, sy = shift
    Wd.tunnel(i, hole=HOLE, shift=(sx * 0.3, sy * 0.3))
    kw = dict(t=t, cx=FISH[0] + sx * 0.55, cy=FISH[1] + sy * 0.55)
    kw.update(fish_kw or {})
    Wd.shadow_fish(i, **kw)
    Wd.crossbar(i, C, R, v=CROSS_V, shift=(sx * 0.8, sy * 0.8))


# ------------------------------------------------------------------ T0: the pick ---
def _pick(t, ink):
    Wd.table(ink, sheet=False)
    scrib = ramp(t, 0.3, 1.15)
    press = ease(t, 1.15, 1.35)
    mark = ramp(t, 1.42, 1.82)
    r = Wd.pick_card(ink, (480, 268), "turkey", picked="circle", press=press, mark=mark, scribble=scrib, angle=-2,
                     initial="E.", lift=1 - ease(t, 0.0, 0.3))
    if press > 0:                                                  # the pressed button lights red through the pencil
        bx, by = r["buttons"]["circle"]
        g = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([30, 30, 90, 90], fill=Wd.PAL["red"] + (int(170 * press),))
        ink.paste(g.filter(ImageFilter.GaussianBlur(10)), (int(bx - 60), int(by - 60)))
        Wd.button_disc(ink, "circle", bx, by, r=7, alpha=0.9 * press)
    tip = r["tip"]
    if tip is None:
        tip = r["buttons"]["circle"]
    if t < 0.3:                                                    # the pencil comes in to the red circle
        b = r["buttons"]["circle"]
        tip = lerp2((b[0] + 120, b[1] + 150), (b[0] + 15, b[1] - 1), ease(t, 0.0, 0.3))
        lift = 1 - ease(t, 0.15, 0.3)
    elif t < 1.15:
        lift = 0.0
    elif t < 1.42:                                                 # hop from the button to the dashed ring
        k = ramp(t, 1.15, 1.42)
        tip = lerp2(tip, (r["ring"][0], r["ring"][1] - 15), smooth(k))
        lift = math.sin(math.pi * k)
    elif t < 1.82:
        lift = 0.0
    else:
        k = ease(t, 1.82, 2.05)
        tip = (tip[0] + 30 * k, tip[1] + 24 * k)
        lift = k
    Wd.pencil(ink, tip, lift=lift)


# -------------------------------------------------------------- T1: someone trapped him ---
def _trapped(t, ink):
    bolt = 1 if t >= S1 else None
    ring = ramp(t, T_SEAT + 0.25, 3.3)
    a_in = ease(t, 3.05, 3.5)                     # the arm comes in with the bar
    slide = ease(t, 3.3, 4.2)                     # the ninth bar goes down into the gap
    b_out = ease(t, 4.2, 4.45)                    # arm back to the edge for the lock
    c_in = ease(t, 4.5, 4.95)                     # arm in again, the lock hanging from it
    snap = ease(t, 4.95, 5.1)                     # the lock shuts on the crossbar
    d_out = ease(t, 5.15, 5.7)                    # the arm withdraws the way it came
    lx, ly = _lock_xy()
    xg = Wd.bar_line(GAP, -0.1, C, R)[0]
    edge = (C[0] + R + 70, 200.0)
    push_pt = (xg + 12, lerp(176.0, 250.0, slide))
    hang_pt = (lx + 10, ly - 22)
    if t < 4.2:
        tip = lerp2(edge, push_pt, a_in)
    elif t < 4.5:
        tip = lerp2(push_pt, (edge[0] - 30, 300.0), b_out)
    elif t < 5.15:
        tip = lerp2((edge[0] - 30, 300.0), hang_pt, c_in)
    else:
        tip = lerp2(hang_pt, (edge[0] + 10, 300.0), d_out)
    arm_on = 3.05 <= t < 5.7
    swing = 0.0
    if t >= 4.5:
        swing = 9 * math.sin((t - 4.5) * 9) * (1 - snap)                              # dangling on the way in
        if t >= 5.0:
            swing += 20 * math.exp(-(t - 5.0) * 1.9) * math.sin((t - 5.0) * 2 * math.pi * 1.25)   # then swings twice

    def front(i):
        if ring < 1:                              # the friend's pencilled circle, carried up onto the glass
            Wd.crayon_ring(i, C, 0.925 * R, color=(226, 232, 226), done=1.0, seed=3, width=4, alpha=0.85)
        if t >= 4.5:
            if snap <= 0:
                Wd.padlock(i, tip[0] - 6, tip[1] + 10, LOCK, swing=swing, open_=1.0)
            else:
                p = lerp2((tip[0] - 6, tip[1] + 10), (lx, ly), snap) if t < 5.15 else (lx, ly)
                Wd.padlock(i, p[0], p[1], LOCK, swing=swing, open_=1 - snap)
        if arm_on:
            Wd.shadow_arm(i, tip, root=(edge[0], tip[1] - (46 if t < 4.35 else 22)), width=30)

    # he shoves once a second throughout; after the lock is on (shoves at 5.0 and 6.0) nothing outside shivers
    sh = Wd.shove(t)
    shift = (2.5 * sh, 0.0) if t < 4.9 else (0.0, 0.0)
    hard = 1.0 if t >= 4.95 else 0.0
    Wd.seat_scene(ink, t, behind=lambda i: _outside(i, t, shift), front=front, slide={GAP: slide}, ring=ring,
                  fish=False, tunnel_on=False, cross=False, notches=_notches(t, [5.5]),
                  fog_level=lerp(0.16, 0.32, ramp(t, T_SEAT, S2)), bolt=bolt, leak_since=T_SEAT, shift=shift,
                  turkey_kw=dict(cx=REFL[0] + 9 * sh * hard, cy=REFL[1] - 7 * sh * hard))


# ---------------------------------------------------- T2: trying to save a hot Cheeto ---
SINK0, SINK1 = 7.25, 10.5


def _slot_x(y):
    v = (y - C[1]) / R
    return (Wd.bar_line(5, v, C, R)[0] + Wd.bar_line(6, v, C, R)[0]) / 2 + 3


def _curl(t):
    """Where the curl is: sinking from the top of the glass, wandering less and less, into the slot between bars 5
    and 6, to rest on the crossbar. Returns (x, y, angle)."""
    s = ramp(t, SINK0, SINK1)
    y_rest = _cross_y(_slot_x(C[1] + CROSS_V * R)) - 15
    y = lerp(66.0, y_rest, s ** 0.9)
    sway = (1 - s) ** 1.3
    x = _slot_x(y) + 34 * sway * math.sin((t - SINK0) * 2.4 + 0.5)
    ang = 14 + 150 * sway * math.sin((t - SINK0) * 1.3)
    if s >= 1:                                        # lodged: it rocks a hair and stays
        ang = 14 + 4 * math.exp(-(t - SINK1) * 3) * math.sin((t - SINK1) * 14)
    return x, y, ang


def _refl(t):
    """Turkey's reflection in bolt 2: at the rim till he sees it, then slammed up the pane and down after the curl."""
    cx_, cy_, _ = _curl(t)
    tx = cx_ - 62 - BEAK_OFF[0]
    ty = min(cy_ + 4 - BEAK_OFF[1], 452.0)
    k = ease(t, 7.6, 7.95)
    jx = 3 * math.sin(t * 31) * k
    return lerp(REFL[0], tx, k) + jx, lerp(REFL[1], ty, k)


def _cheeto(t, ink):
    cx_, cy_, ang = _curl(t)
    rx, ry = _refl(t)
    lunge = t >= 7.6
    # the wing on the pane keeps pace with the curl and wipes a clear streak through the fog behind it
    pts = []
    tt = 7.95
    while tt < min(t, SINK1 + 0.3) + 1e-6:
        qx, qy = _refl(tt)
        pts.append((qx + BEAK_OFF[0] + 4, qy + BEAK_OFF[1] + 46))
        tt += 0.12
    wipes = [(pts, 46)] if len(pts) > 1 else None
    look = ease(t, 7.5, 8.2)                                    # the fish looks at the curl and leaves it alone
    back = ease(t, 8.2, 9.6)
    fx, fy = FISH[0] + 44 * back, FISH[1] - 16 * back
    f_ang = lerp(FISH_A, clamp(math.degrees(math.atan2(cy_ - fy, max(90.0, (fx - 60) - cx_))), -30, 16), look)
    lx, ly = _lock_xy()

    def front(i):
        Wd.padlock(i, lx, ly, LOCK, swing=1.5 * math.sin(t * 2.2))
        Wd.cheeto(i, cx_, cy_, 30, angle=ang, t=t, glow=1.0, fizz=1.0)

    Wd.seat_scene(ink, t, behind=lambda i: _outside(i, t, fish_kw=dict(cx=fx, cy=fy, angle=f_ang, jaw=6 * look)),
                  front=front, fish=False, tunnel_on=False, cross=False, notches=_notches(t, [8.5, 10.5]),
                  fog_level=lerp(0.24, 0.56, ramp(t, S2, S3)), wipes=wipes, bolt=2, leak_since=S2,
                  turkey_kw=dict(mood="lunge" if lunge else "shove", cx=rx, cy=ry))


# ------------------------------------------------------------------ T3: that's his home ---
def _home(t, ink):
    push = ease(t, 12.9, 15.4)
    gate_open = ease(t, 13.1, 13.7) - ease(t, 16.9, 17.5)
    lamp = ease(t, 14.45, 14.7)
    closed = ease(t, 16.15, 17.25)
    rb = R * (1 + 0.5 * push)
    part = 74 * push                                   # ... and the uprights slide apart as we pass between them                 # the bars' plane comes toward us and parts (nearest fastest)
    hh = Wd.home_hole(push)
    hole = max(HOLE, hh)
    rh = R * hole / hh                                 # the room fills the far mouth from the start
    st = {}

    def fish_state(h):
        """Fish: nose to the gate, in over the mat, past the lamp, once round in the armchair, settle, tail to the curtain."""
        chair = h["chair"]
        mat = (chair[0] + 78, h["floor"] - 6)              # just over the mat on the sill, still against the lit wall
        p0 = (FISH[0], FISH[1] - 44)                       # hanging behind the bars, clear of the furniture
        p1 = (FISH[0] - 30, FISH[1] - 18)                  # nose on the gate
        p2 = (mat[0], mat[1] - 34)                         # over the mat
        p3 = (chair[0] + 6, chair[1] - 26)                 # in the armchair
        if t < 13.1:
            k = ease(t, 12.5, 13.1)
            return lerp2(p0, p1, k), FISH_L, FISH_A, 10 * k, None
        if t < 14.1:
            k = ease(t, 13.3, 14.1)
            return lerp2(p1, p2, k), lerp(FISH_L, 124, k), lerp(FISH_A, -4, k), 10 * (1 - k), None
        if t < 15.0:
            k = ease(t, 14.1, 15.0)
            return lerp2(p2, p3, k), lerp(124, 98, k), lerp(-4, 0, k), 0, None
        spin = ease(t, 15.05, 15.95)
        tail = None
        if t >= 16.1:
            tail = 26 * math.sin((t - 16.1) * 9) * (1 - ease(t, 17.1, 17.4))
        return p3, 98, -360 * spin, 0, tail

    def behind(i):
        Wd.tunnel(i, hole=hole)
        h = Wd.home(i, push, lamp=lamp, r=rh, planes=("light", "far", "room", "chair"))
        (fx, fy), L, ang, jaw, tail = fish_state(h)
        inside = t >= 13.75

        def fish():
            if tail is None:
                Wd.shadow_fish(i, fx, fy, L, angle=ang, jaw=jaw, t=t)
            else:
                Wd.shadow_fish(i, fx, fy, L, angle=ang, jaw=jaw, tail=tail, fins=10 * math.sin(t * 5))
        if inside:
            fish()
        Wd.home(i, push, r=rh, planes=("sill",))
        Wd.curtains(i, closed, span=max(0.8, hole + 0.02), glow=closed * lamp)
        if not inside:
            fish()
        Wd.crossbar(i, C, rb, v=CROSS_V, shift=(0, 46 * push))
        Wd.bars(i, [1, 2, 3, 4], C, rb, shift=(-part, 0))
        Wd.bars(i, [7, 8, 9], C, rb, shift=(part, 0))
        Wd.gate(i, gate_open, C, rb)
        st.update(h)

    sh = Wd.shove(t)
    Wd.seat_scene(ink, t, behind=behind, fish=False, tunnel_on=False, cross=False, only=[],
                  notches=_notches(t, [13.5, 15.0, 16.5]),
                  fog_level=lerp(0.18, 0.36, ramp(t, S3, 16.6)) + 0.34 * ease(t, 16.8, 17.8), bolt=3, leak_since=S3,
                  turkey_kw=dict(cx=REFL[0] + 7 * sh, cy=REFL[1] - 5 * sh))


# ------------------------------------------------------------------------- draw ---
def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < T_SEAT:
        _pick(t, ink)
    elif t < S2:
        _trapped(t, ink)
    elif t < S3:
        _cheeto(t, ink)
    else:
        _home(t, ink)
    f = _iris_f(t)
    if f > 0:
        Wd.iris(ink, f, r=600)
    Wd.badge(ink)


def check():
    assert all(0 <= a < b <= SECONDS and b - a >= 2.5 for a, b, _ in CAPTIONS)
    assert all(b0 <= a1 for (_, b0, _), (a1, _, _) in zip(CAPTIONS, CAPTIONS[1:]))
    assert [c[2] for c in CAPTIONS] == ["Someone trapped him.", "Trying to save a hot Cheeto.", "That's his home."]
    for a, b, ticks, end in ((S1, S2, [5.5], 4), (S2, S3, [8.5, 10.5], 3), (S3, SECONDS, [13.5, 15.0, 16.5], 2)):
        assert abs(_notches(a, ticks) - 5) < 1e-6 and abs(_notches(b - 0.05, ticks) - end) < 1e-6


if __name__ == "__main__":
    from kit import Film
    check()
    film = Film("c33_scene_turkey", SECONDS)
    film.picture(draw)
    args = [float(a) for a in sys.argv[1:] if not a.startswith("-")]
    times = args or [0.1, 0.7, 1.3, 1.75, 2.0, 2.25, 2.6, 3.2, 3.8, 4.3, 4.8, 5.2, 5.6, 6.5,
                     7.1, 7.5, 8.0, 8.8, 9.6, 10.4, 11.0, 11.8,
                     12.2, 12.9, 13.5, 14.0, 14.6, 15.1, 15.5, 16.0, 16.6, 17.0, 17.5, 17.9]
    film.render(preview=times)
