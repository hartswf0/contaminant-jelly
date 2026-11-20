"""c13 · scene_pilot · the pilot's page (board beats A1 to A9, 0.0 to 20.0 s).

A1-A6  0.0-9.0   the pilot's drawing made in pencil on the table, stroke by stroke, clockwise round the ring.
A7     9.0-13.0  line 1: cut pieces laid over the pencil ones; the tin's lamp touches the cord, the bell tips,
                 both trout turn clockwise, find nobody at the bell, and end nose-down staring at the tin.
A8    13.0-16.0  line 2: the tin is turned a quarter clockwise to face us; Turkey freaks out behind the glass.
A9    16.0-20.0  line 3: the brass arm sweeps to Turkey's seat; the bell comes to rest over his reflection like
                 the dome of a serving dish, the two trout settle either side of it, he gasps, the needle falls.

Exposes SECONDS, CAPTIONS, draw(t, ink). Uses only world.py and the kit. Captions are drawn by the editor.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402
from kit import Ink, W, H, FPS, clamp, ramp, ease, smooth, lerp, lerp2     # noqa: E402,F401

SECONDS = 20.0
CAPTIONS = [
    (9.0, 13.0, "The trout. The trout think the sub is a bell-ringer prank."),
    (13.0, 16.0, "Freak out."),
    (16.0, 20.0, "He is going to be turkey dinner."),
]

P = w.PILOT_PLACES
C = w.PORT_C
R = w.PORT_R

# ------------------------------------------------------------------ A1-A6 ---
T_DRAWN = w.PILOT_TIMES["weed_l"][1]          # 8.75: the drawing is whole
T_PENCIL_OUT = 9.25


def _polar(p):
    dx, dy = p[0] - C[0], p[1] - C[1]
    return math.hypot(dx, dy), math.degrees(math.atan2(dx, -dy)) % 360.0      # radius, clock angle


def _pencil_exit(ink, tip, t):
    """The pencil lifts and leaves the frame on a clockwise curl about the ring's centre."""
    f = ramp(t, T_DRAWN, T_PENCIL_OUT)
    r0, a0 = _polar(tip)
    f2 = f * f
    p = w.clock_xy(C, r0 + 560 * f2, a0 + 75 * smooth(f))
    w.pencil(ink, p, 52 - 30 * f, lift=1.0)


def _page(ink, t):
    w.table(ink)
    w.sheet_ring(ink)
    tip, down = w.pilot_page(ink, t)
    if t < T_DRAWN:
        w.pencil(ink, tip, lift=0 if down else 1)
    elif t < T_PENCIL_OUT:
        _pencil_exit(ink, tip, t)


# --------------------------------------------------------------------- A7 ---
# The pieces are laid clockwise: upper trout, bell, lower trout's turn comes after the upper (board: upper first,
# then lower), then the bell, then the tin at six o'clock.
LAY = dict(fish1=(9.0, 9.5), fish2=(9.3, 9.8), bell=(9.6, 10.05), tin=(9.9, 10.45))
T_BEAM = 10.45                   # the lamp-beam card comes on and touches the cord
T_KICK = 10.62                   # the bell tips out to the right ...
KICK_LEN = 0.6                   # ... and back
TABLE_BELL = w.ring_xy(*P["bell_top"])
TABLE_TIN = (480, 420)
F1 = w.ring_xy(*P["fish1"])
F2 = w.ring_xy(*P["fish2"])


def _bell_swing7(t):
    x = (t - T_KICK) / KICK_LEN
    if x <= 0:
        return 0.0
    if x < 1:
        return 30.0 * math.sin(math.pi * x) ** 1.2
    return -5.0 * math.exp(-(t - T_KICK - KICK_LEN) * 4.0) * math.sin((t - T_KICK - KICK_LEN) * 9.0)


_clap7 = w.Follower(_bell_swing7, 16.5, f=1.15, zeta=0.4)
_cord7 = w.Follower(_bell_swing7, 16.5, f=0.8, zeta=0.2)


def _first_strike():
    """The clapper arrives late: the strike is the frame it is furthest behind the bell."""
    best, bt = 0.0, T_KICK + 0.3
    for k in range(int(T_KICK * FPS), int((T_KICK + 1.0) * FPS)):
        tt = k / FPS
        d = abs(_clap7.at(tt) - _bell_swing7(tt))
        if d > best:
            best, bt = d, tt
    return bt


T_STRIKE = _first_strike()


def _dir_angle(src, dst):
    """Trout angle (degrees CCW, facing left) that points the nose from src at dst, in (-180, 180]."""
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    return math.degrees(math.atan2(dy, -dx))


def _cw_to(a_from, a_to):
    """The equivalent of a_to that is reached from a_from by turning CLOCKWISE only (angle only decreases)."""
    while a_to > a_from:
        a_to -= 360.0
    return a_to


_TIN_LOOK = (TABLE_TIN[0], TABLE_TIN[1] - 6)
_BELL_LOOK = (TABLE_BELL[0], TABLE_BELL[1] + 60)
# upper trout: drawing angle -> looks at the bell -> looks down at the tin; always clockwise
A1_0 = P["fish1_angle"]
A1_BELL = _cw_to(A1_0, _dir_angle(F1, _BELL_LOOK))
A1_TIN = _cw_to(A1_BELL, 78.0)
A2_0 = P["fish2_angle"]
A2_BELL = _cw_to(A2_0, _dir_angle(F2, _BELL_LOOK))
A2_TIN = _cw_to(A2_BELL, _dir_angle(F2, _TIN_LOOK))
# state machine timings: QUEUE (as drawn) -> TURN (to the bell) -> LOOK_AT_TIN. The upper trout has the turn first.
TURN1 = (T_STRIKE + 0.1, T_STRIKE + 0.5, T_STRIKE + 0.7, T_STRIKE + 1.15)
TURN2 = (T_STRIKE + 0.25, T_STRIKE + 0.65, T_STRIKE + 0.85, T_STRIKE + 1.35)


def _fish_angle(t, a0, a_bell, a_tin, tm):
    a = lerp(a0, a_bell, ease(t, tm[0], tm[1]))
    return lerp(a, a_tin, ease(t, tm[2], tm[3])) if t > tm[2] else a


def _spiral_in(place, t, t0, t1, turn=38.0, far=330.0):
    """A piece slid onto the table: it arrives on a clockwise curl about the ring's centre and settles."""
    e = ease(t, t0, t1)
    r0, a0 = _polar(place)
    return w.clock_xy(C, r0 + far * (1 - e) ** 1.5, a0 - turn * (1 - e)), e


def _table_pieces(ink, t, tin=True):
    """The table with the finished drawing and the cut pieces of line 1, as they stand at time t (>= 9)."""
    w.table(ink)
    w.sheet_ring(ink)
    tip, _ = w.pilot_drawing(ink, 1.0, alpha=lerp(1.0, 0.8, ease(t, 9.0, 10.0)))
    if t < T_PENCIL_OUT:
        _pencil_exit(ink, tip, t)

    # the tin at six o'clock, lamp up
    if tin and t >= LAY["tin"][0]:
        (tx, ty), e = _spiral_in(TABLE_TIN, t, *LAY["tin"], turn=-30.0, far=260.0)
        beam = 0.9 * ease(t, T_BEAM, T_BEAM + 0.18)
        w.tin(ink, (tx, ty), 0.42, t, mood=None, angle=-90, beam=beam, shadow=0.7 + 0.3 * (1 - e))

    # the brass bell laid over the pencil bell
    if t >= LAY["bell"][0]:
        (bx, by), e = _spiral_in(TABLE_BELL, t, *LAY["bell"], turn=30.0, far=240.0)
        fl = clamp(1 - (t - T_STRIKE) / 0.35) if t >= T_STRIKE else 0.0
        w.bell(ink, (bx, by), 0.55, swing=_bell_swing7(t), clapper=_clap7.at(t), cord=_cord7.at(t), flash=fl)
        if fl > 0:                                      # the one strike, seen: short pencil-grey ticks off the bell mouth
            m = (bx + 0.55 * 100 * math.sin(math.radians(_bell_swing7(t))), by + 0.55 * 100)
            g = 1 - fl
            for k in range(5):
                a = math.radians(20 + 35 * k)
                r0, r1 = 26 + 26 * g, 38 + 40 * g
                ink.d.line([(m[0] + math.cos(a) * r0, m[1] - 18 + math.sin(a) * r0 * 0.8),
                            (m[0] + math.cos(a) * r1, m[1] - 18 + math.sin(a) * r1 * 0.8)],
                           fill=w.PAL["brass_dk"] + (int(230 * fl),), width=3)

    # the two trout, laid exactly over the two pencil fish; later they turn, clockwise only
    for (place, ln, lay, a0, ab, at_, tm) in ((F2, P["fish2_len"], LAY["fish2"], A2_0, A2_BELL, A2_TIN, TURN2),
                                              (F1, P["fish1_len"], LAY["fish1"], A1_0, A1_BELL, A1_TIN, TURN1)):
        if t < lay[0]:
            continue
        (x, y), e = _spiral_in(place, t, *lay)
        ang = _fish_angle(t, a0, ab, at_, tm)
        lid = 0.45 * ease(t, tm[2] + 0.1, tm[3])
        w.trout(ink, x, y, length=ln * R, angle=ang, lid=lid, amp=0.0, shadow=0.8,)


# --------------------------------------------------------------------- A8 ---
PAN = 120.0                        # the camera comes down the table so the tin's face has room
PLATE_C = (480, 398)
PLATE_R = 118
T_FACE = (13.0, 13.75)             # the tin is turned a quarter clockwise and brought up to face us
T_SNAP = 14.05                     # Turkey freaks out
GAUGE_AT = w.STAGE["gauge"]


def _wattle_target(t):
    return 0.0 if t < T_SNAP else 34.0 * math.sin((t - T_SNAP) * 9.0)


_wattle8 = w.Follower(_wattle_target, 17.0, f=2.0, zeta=0.22)

_static = {}


def _table_static():
    """The table as line 1 left it (pieces at rest, trout staring at the tin), made tall so the camera can come
    down it. Nothing on it moves again: the trout do not flinch."""
    if "img" not in _static:
        o = Ink(12.99, int(12.99 * FPS))
        _table_pieces(o, 12.99, tin=False)
        top = o.img.convert("RGB")
        bare = Ink(0, 0)
        w.table(bare)
        tall = Image.new("RGB", (W, H + 140))
        tall.paste(bare.img.convert("RGB").transpose(Image.FLIP_TOP_BOTTOM), (0, H))
        tall.paste(top, (0, 0))
        _static["img"] = tall
        _static["trout"] = None
    return _static["img"]


_plate_cache = {}


def _plate(t, mood, shake_over):
    """The tin's face (riveted plate, brass ring, Turkey in the glass) as a loose cut piece."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o = Ink(t, int(t * FPS))
    o.img = lay
    o.d = ImageDraw.Draw(lay, "RGBA")
    w.tin_porthole(o, (W // 2, H // 2), PLATE_R, mood, t, shadow=0.0, **shake_over)
    half = int(PLATE_R * 1.7) + 4
    return o.img.crop((W // 2 - half, H // 2 - half, W // 2 + half, H // 2 + half))


def _smudge(ink, amount, t):
    """The pencil lines by the rattling tin smudge: soft graphite dragged out from under its edges."""
    if amount <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay, "RGBA")
    col = w.PAL["pencil"]
    cx, cy = PLATE_C
    half = PLATE_R * 1.7
    for k in range(14):
        side = -1 if k % 2 else 1
        y = cy - half * 0.75 + (k // 2) * 34 + 7 * math.sin(k * 2.3)
        x0 = cx + side * (half - 6)
        ln = (26 + 22 * abs(math.sin(k * 1.7))) * amount
        d.line([(x0, y), (x0 + side * ln, y + 5 * math.sin(k))], fill=col + (int(120 * amount),), width=7)
    ink.paste(lay.filter(ImageFilter.GaussianBlur(5)), (0, 0))


def _gauge8(t):
    """8 notches full; the freak-out costs two: 8 -> 7 -> 6."""
    return 8.0 - ease(t, T_SNAP + 0.25, T_SNAP + 0.6) - ease(t, T_SNAP + 1.0, T_SNAP + 1.35)


def _line2(ink, t):
    f = ease(t, *T_FACE)
    tall = _table_static()
    ink.img.paste(tall.crop((0, int(PAN * f), W, int(PAN * f) + H)), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    off = -PAN * f

    freak = t >= T_SNAP
    shake = 4.0 * ease(t, T_SNAP + 0.1, T_SNAP + 0.5) if freak else 0.0
    _smudge(ink, ease(t, T_SNAP + 0.3, T_SNAP + 1.6), t)

    # the small tin on the table until its face has come up
    if f < 0.35:
        w.tin(ink, (TABLE_TIN[0], TABLE_TIN[1] + off), 0.42, t, mood=None, angle=-90 - 90 * smooth(f / 0.35) * 0.4,
              beam=0.9 * (1 - ramp(f, 0.0, 0.2)))
    if f > 0.15:
        g = smooth(ramp(f, 0.15, 1.0))
        over = {}
        if freak:
            mood = "freak"
            over["wattle"] = _wattle8.at(t)
        else:
            mood = "calm"
        spr = _plate(t, mood, over)
        sc = lerp(0.2, 1.0, g)
        ang = 90.0 * (1 - g)                                   # CCW 90 -> 0: a quarter turn clockwise
        cx = lerp(TABLE_TIN[0], PLATE_C[0], g) + shake * math.sin(t * 61)
        cy = lerp(TABLE_TIN[1] + off, PLATE_C[1], g) + shake * 0.6 * math.cos(t * 67)
        if shake:
            ang += shake * 0.3 * math.sin(t * 43)
        w.put(ink, spr, cx, cy, angle=ang, scale=sc, shadow=0.85, shadow_off=(9, 13), shadow_blur=9)
        if freak and shake > 1:                                # wings drumming the inside: the tin jumps, dust leaves it
            for k in range(6):
                ph = (t * 3.1 + k * 0.37) % 1.0
                a = math.radians(200 + 28 * k + 10 * math.sin(k))
                r0 = PLATE_R * 1.72 + 34 * ph
                ink.d.ellipse([cx + math.cos(a) * r0 - 3, cy + math.sin(a) * r0 * 0.9 - 3,
                               cx + math.cos(a) * r0 + 3, cy + math.sin(a) * r0 * 0.9 + 3],
                              fill=w.PAL["pencil"] + (int(150 * (1 - ph)),))

    # the two trout have not moved: they lie in front of the tin's top edge, still staring down at it
    if f > 0.15:
        for (place, ln, ang) in ((F2, P["fish2_len"], A2_TIN), (F1, P["fish1_len"], A1_TIN)):
            w.trout(ink, place[0], place[1] + off, length=ln * R, angle=ang, lid=0.45, amp=0.0, shadow=0.8)

    # the air gauge, slid onto the table at four o'clock (it comes down, clockwise)
    ge = ease(t, 13.25, 13.8)
    if ge > 0:
        w.gauge(ink, _gauge8(t), GAUGE_AT[0] + 40 * (1 - ge), GAUGE_AT[1] - 420 * (1 - ge) ** 1.5,
                tremble=1.0 if freak and t < T_SNAP + 1.6 else 0.0, t=t)


# --------------------------------------------------------------------- A9 ---
T_SWEEP = (16.0, 16.75)
T_SEES = 18.05                     # the dome is over him and he sees it
DOME = (480, 385)                  # Turkey's reflection, brought under the bell
REFL_H = 230


def _bell_swing9(t):
    x = t - 16.2
    if x <= 0:
        return 26.0
    return 26.0 * math.exp(-x * 1.75) * math.cos(x * 5.2)


_clap9 = w.Follower(_bell_swing9, SECONDS + 0.5, f=1.9, zeta=0.5)
_cord9 = w.Follower(_bell_swing9, SECONDS + 0.5, f=1.1, zeta=0.3)

# The two trout round the dish: clockwise only, one at a time. The upper trout (it has the turn) goes first, over
# the top and down the right side; the lower one waits, then goes under and up the left side.
_C0, _C1 = (480, 290), (480, 306)
_r1a, _a1a = math.hypot(w.STAGE["fish1"][0] - _C0[0], w.STAGE["fish1"][1] - _C0[1]), None
_K1 = dict(a0=318.0, a1=450.0, r0=72.0, r1=132.0, t0=16.75, t1=18.0)
_K2 = dict(a0=108.0, a1=270.0, r0=90.0, r1=132.0, t0=17.35, t1=18.75)


def _knife_fork(t, K):
    e = ease(t, K["t0"], K["t1"])
    c = lerp2(_C0, _C1, e)
    r = lerp(K["r0"], K["r1"], e) + (26.0 * math.sin(math.pi * e) if K is _K2 else 0.0)
    return c, r, lerp(K["a0"], K["a1"], e), e


def _gauge9(t):
    return 6.0 - ease(t, T_SEES + 0.25, T_SEES + 0.75)


def _seat(ink, t):
    sw, cl, co = _bell_swing9(t), _clap9.at(t), _cord9.at(t)
    w.seat_stage(ink, t, "back")
    # the upper trout passes behind the bell and its cord
    c1, r1, a1, e1 = _knife_fork(t, _K1)
    x1, y1 = w.trout_on_circle(ink, c1, r1, a1, 150, phase=t * 6 * (1 - e1), amp=8 * (1 - e1), lid=0.45)
    w.bell(ink, swing=sw, clapper=cl, cord=co, part="cord")
    w.seat_stage(ink, t, "front")
    w.bell(ink, swing=sw, clapper=cl, cord=co, part="body")
    # the lower trout comes round in front of the left pillar
    c2, r2, a2, e2 = _knife_fork(t, _K2)
    w.trout_on_circle(ink, c2, r2, a2, 150, phase=t * 6 * (1 - e2), amp=8 * (1 - e2), lid=0.45)
    # "haha verry funny" stays pinned to the upper trout
    w.speech_bubble(ink, (x1 - 30 + 20 * e1, y1 - 34 - 58 * e1), 0.62, shadow=0.5)

    if t < T_SEES:
        mood, over = "freak", {}
    elif t < T_SEES + 1.0:
        mood, over = "gasp", {}
    else:
        mood, over = "freak", {}
    w.turkey_reflection(ink, DOME[0], DOME[1], REFL_H, mood, t, alpha=0.85, **over)
    if t >= T_SEES + 0.1:
        w.bubbles(ink, (DOME[0] + 46, DOME[1] - 62), t, T_SEES + 0.1, n=8, rise=150.0, curl=90.0, size=7.0)
    w.seat_frame(ink)
    w.gauge(ink, _gauge9(t), tremble=1.0 if T_SEES < t < T_SEES + 1.2 else 0.0, t=t)


# ------------------------------------------------------------------- draw ---
def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < 9.0:
        _page(ink, t)
    elif t < 13.0:
        _table_pieces(ink, t)
    elif t < T_SWEEP[0]:
        _line2(ink, t)
    elif t < T_SWEEP[1]:
        _line2(ink, t)
        o = w.offscreen(ink)
        _seat(o, t)
        w.sweep(ink, o.img, ramp(t, *T_SWEEP))
    else:
        _seat(ink, t)
    w.badge(ink)


def check():
    """Clockwise Etiquette, numerically: every turn is clockwise only, and one trout moves first."""
    prev = None
    for k in range(int(9 * FPS), int(13 * FPS)):
        tt = k / FPS
        cur = (_fish_angle(tt, A1_0, A1_BELL, A1_TIN, TURN1), _fish_angle(tt, A2_0, A2_BELL, A2_TIN, TURN2))
        if prev:
            assert cur[0] <= prev[0] + 1e-9 and cur[1] <= prev[1] + 1e-9, "a trout turned anticlockwise on the table"
        prev = cur
    assert TURN1[0] < TURN2[0] and TURN1[3] < TURN2[3], "the upper trout has the turn first"
    assert TURN2[3] < 12.7, "the stare must be held before the line ends"
    prev = None
    for k in range(int(16 * FPS), int(20 * FPS)):
        tt = k / FPS
        cur = (_knife_fork(tt, _K1)[2], _knife_fork(tt, _K2)[2])
        if prev:
            assert cur[0] >= prev[0] - 1e-9 and cur[1] >= prev[1] - 1e-9, "a trout went anticlockwise round the dish"
        prev = cur
    assert _K1["t0"] < _K2["t0"], "one at a time: the upper trout leaves first"
    for (a, b, s) in CAPTIONS:
        assert b - a >= 2.5 and b <= SECONDS
    assert abs(_gauge8(15.99) - 6) < 1e-6 and abs(_gauge9(19.99) - 5) < 1e-6
    return True


if __name__ == "__main__":
    from kit import Film
    check()
    film = Film("c13_scene_pilot", SECONDS)
    film.picture(draw)
    args = [float(a) for a in sys.argv[1:] if not a.startswith("-")]
    times = args or [1.2, 3.2, 4.8, 7.0, 8.9, 9.5, 10.4, 11.2, 11.9, 12.8, 13.4, 14.0, 14.6, 15.6, 16.4, 17.3, 18.3, 19.6]
    film.render(preview=times)
    sdir = Path(w.FILMS) / "stills" / "c13_scene_pilot"
    cols = 3
    tw, th = 480, 270
    sheet = Image.new("RGB", (cols * tw, ((len(times) + cols - 1) // cols) * th), (20, 20, 20))
    for i, tt in enumerate(times):
        im = Image.open(sdir / f"{tt:06.2f}.png").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(sdir / "contact.png")
    print("contact ->", sdir / "contact.png", "strike at", round(T_STRIKE, 2))
