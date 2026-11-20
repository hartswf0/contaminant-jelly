"""c25 · scene_pilot · the pilot's page (board beats P1 to P4, 0.0 to 20.5 s of the film).

P1  0.0 to 10.0   the child's drawing made in pencil on the table, stroke by stroke; the lines then move into the
                  cut-paper puppet (Foldes change) and the card is turned over.
P2 10.0 to 14.5   "A trout, and the trout think it is a bird in a bottle."   river side, looking in
P3 14.5 to 17.5   "Panic."                                                   Turkey's seat, looking out
P4 17.5 to 20.5   "By panicking."                                            same seat, pushed in on the gauge

Exposes SECONDS, CAPTIONS (times from this module's own start) and draw(t, ink). Captions are not drawn here.
The badge is drawn last in every frame; an editor who draws its own can set BADGE = False.

Test:  python3 films/swarm/c25/scene_pilot.py --sheet     (contact sheet in films/stills/c25_scene_pilot/)
       python3 films/swarm/c25/scene_pilot.py --stills 1 5 9 ...
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as w                                                    # noqa: E402  (puts films/ on sys.path)
from kit import FPS, H, W, clamp, ease, lerp                         # noqa: E402
from PIL import Image, ImageDraw                                     # noqa: E402

SECONDS = 20.5
BADGE = True

T_P2, T_P3, T_P4 = 10.0, 14.5, 17.5
FLIP = 8 / FPS                                                       # a card turned over: 8 frames

CAPTIONS = [
    (T_P2, T_P3, "A trout, and the trout think it is a bird in a bottle."),
    (T_P3 + 0.3, T_P4, "Panic."),
    (T_P4, SECONDS, "By panicking."),
]

# ------------------------------------------------------------------ P1: the table ---

P = w.PILOT_PLACES
_WX, _WY = w.ring_xy(*P["walker"])
_WH = P["walker_h"] * w.PORT_R
_PARTS = ("legs", "tunic", "bowl", "fish", "arms")


def _p1(ink, t):
    w.table(ink)
    w.sheet_ring(ink)
    if t < 8.4:
        tip, down = w.pilot_page(ink, min(t, 7.95))
        if t < 7.8:
            w.pencil(ink, tip, lift=0 if down else 1)
        else:                                                        # the pencil lifts and leaves by the right edge
            a = ease(t, 7.8, 8.35)
            w.pencil(ink, (tip[0] + 560 * a * a, tip[1] - 40 * a), lift=1)
        return
    # Foldes change: each cut piece slides in under the pencil lines while the lines move onto the pieces
    for k, part in enumerate(_PARTS):
        a = ease(t, 8.45 + k * 0.17, 8.85 + k * 0.17)
        if a > 0:
            w.walker(ink, _WX, _WY, _WH, parts=(part,), shadow=0.8, lift=1 - a, alpha=min(1.0, a * 3),
                     slosh=_SLOSH1.at(t), wave=clamp(abs(_SLOSH1.at(t)) / 8))
    fade = 1 - ease(t, 9.25, 9.6)
    if fade > 0:
        w.pilot_morph(ink, ease(t, 8.4, 9.25), alpha=fade)


def _kick1(t):                                                       # the bowl is set down at about 8.95: the water slops
    return 10.0 if 8.9 <= t < 9.0 else 0.0


_SLOSH1 = w.Follower(_kick1, SECONDS, f=1.8, zeta=0.3)

# ------------------------------------------------------------------ P2: the river side ---

TIN_C, TIN_S = (625, 285), 1.5
WALK_X0, WALK_Y, WALK_H = 222, 478, 300


def _lean(u):                                                        # u = seconds into P2
    return ease(u, 0.5, 1.3) - ease(u, 3.35, 4.05)


def _kick2(t):                                                       # the lean in and the lean back slop the bowl
    u = t - T_P2
    if -FLIP <= u < 0.25:
        return 7.0                                                   # the card flip itself
    d = (_lean(u + 0.04) - _lean(u - 0.04)) / 0.08
    return -9.0 * d


_SLOSH2 = w.Follower(_kick2, SECONDS, f=1.5, zeta=0.3)


def _wing_free(t, rate=2.3):
    """Uncounted panic: both wings thrown up and beating."""
    return 52 + 44 * math.sin(2 * math.pi * rate * t)


def _p2(ink, t):
    u = t - T_P2
    ln = _lean(u)
    w.river_backdrop(ink, t)
    tp = w.tin(ink, TIN_C, TIN_S, t, mood="freak", wing=_wing_free(t), angle=-1.2 * ln)
    w.gauge(ink, 6, *w.tin_dial_xy(tp), r=30, t=t)                   # the air is still full
    # the bottle is the tin's own outline moved, in pencil, for the length of the lean
    bf = ease(u, 0.9, 1.8) - ease(u, 3.3, 4.1)
    ba = ease(u, 0.75, 1.05) - ease(u, 4.05, 4.3)
    s = _SLOSH2.at(t)
    w.walker(ink, WALK_X0 + 53 * ln, WALK_Y, WALK_H, flip=True, lean=11 * ln, step=0.0,
             phase=t * 3, amp=4, slosh=s, wave=clamp(abs(s) / 8), bowl_bubbles=t, bob=False)
    if ba > 0:                                                       # over the trout: it is what the trout thinks
        w.bottle_lines(ink, TIN_C, TIN_S, f=bf, alpha=ba, angle=-1.2 * ln, width=4)


# ------------------------------------------------------------------ P3, P4: Turkey's seat ---

BEATS = [T_P4 + 0.75, T_P4 + 1.5, T_P4 + 2.25]                       # P4: three counted wing-beats
P3_BEATS = [T_P3 + 0.55 + 0.42 * k for k in range(6)]                # P3: he throws them up and beats, uncounted
REFL = dict(cx=388, cy=338, height=236, alpha=0.8)                  # Turkey's reflection, low left in the glass
PUFF = (300, 305)                                                    # where the bubbles leave, by the left rim


def _wing_seat(t):
    if t < T_P4 + 0.3:                                               # P3: up at once, then beating without stop
        up = ease(t, T_P3 + 0.3, T_P3 + 0.6)
        v = up * (58 + 40 * math.sin(2 * math.pi * 2.4 * (t - T_P3)))
        return max(8.0, v * (1 - ease(t, T_P4, T_P4 + 0.3)))
    return max([96 * math.sin(math.pi * clamp((t - b + 0.12) / 0.5)) for b in BEATS] + [8.0])


def _needle_target(t):
    return 6.0 - sum(1.0 for b in BEATS if t >= b + 0.12)


_NEEDLE = w.Follower(_needle_target, SECONDS, f=3.0, zeta=0.35, x0=6.0)   # goes one too far and comes back


def _wattle_target(t):
    return -0.5 * _wing_seat(t)


_WATTLE = w.Follower(_wattle_target, SECONDS, f=2.2, zeta=0.25, x0=0.0)


def _kick3(t):
    return 7.0 if T_P3 <= t < T_P3 + FLIP + 0.1 else 0.0             # the flip slops the bowl; it levels in a second


_SLOSH3 = w.Follower(_kick3, SECONDS, f=1.5, zeta=0.32)


def _seat(ink, t):
    s = _SLOSH3.at(t)
    # the trout outside does nothing at all: it only stands there (pose of the drawing, mirror of P2)
    wk = dict(x=572, height=288, step=0.0, bob=False, phase=t * 1.2, amp=2.0, slosh=s, wave=clamp(abs(s) / 8), bowl_bubbles=t)
    tk = dict(REFL, mood="freak", t=t, wing=_wing_seat(t), wattle=_WATTLE.at(t))
    w.seat_scene(ink, t, wk, tk, notches=6, bolt=None, frame=False)
    for b in BEATS:                                                  # one puff per beat, and only on the beat
        if t >= b + 0.12:
            w.bubbles(ink, PUFF, t, t0=b + 0.12, n=9, rise=170, size=9, spread=22)
    w.seat_frame(ink)
    n = clamp(_NEEDLE.at(t), 0, 6)
    tick = max([1 - clamp((t - b - 0.12) / 0.3) for b in BEATS if t >= b + 0.12] + [0.0])
    w.gauge(ink, n, tremble=tick, t=t)


def _push(ink, f):
    """Push in on the lower left so the gauge and the reflection share the frame (one move, no cut)."""
    if f <= 0:
        return
    z = lerp(1.0, 1.42, f)
    cw, ch = W / z, H / z
    x0 = lerp(0, 22, f)
    y0 = H - ch - lerp(0, 4, f)
    img = ink.img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    ink.img.paste(img, (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _p34(ink, t):
    _seat(ink, t)
    _push(ink, ease(t, T_P4 - 0.05, T_P4 + 0.6))


# ------------------------------------------------------------------ the module ---

def _flip(ink, t, t0, old, new):
    """old scene on ink, turned over top to bottom into new, from t0 for 8 frames."""
    f = (t - t0) / FLIP
    old(ink, t)
    o = w.offscreen(ink)
    new(o, t)
    w.card_flip(ink, o.img, clamp(f, 0.001, 0.999))


def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < T_P2 - FLIP:
        _p1(ink, t)
    elif t < T_P2:
        _flip(ink, t, T_P2 - FLIP, _p1, _p2)
    elif t < T_P3:
        _p2(ink, t)
    elif t < T_P3 + FLIP:
        _flip(ink, t, T_P3, _p2, _p34)
    else:
        _p34(ink, t)
    if BADGE:
        w.badge(ink)


# ------------------------------------------------------------------ test harness ---

if __name__ == "__main__":
    from kit import HERE, Film

    film = Film("c25_scene_pilot", SECONDS, boil=0)
    film.picture(draw)
    if len(sys.argv) > 1 and sys.argv[1] == "--sheet":
        ts = [float(x) for x in sys.argv[2:]] or [0.8, 2.0, 3.6, 5.0, 6.2, 7.6, 8.7, 9.1, 9.5, 9.85,
                                                  10.4, 11.3, 12.5, 13.6, 14.3, 14.65,
                                                  15.1, 15.9, 16.8, 17.9, 18.4, 19.2, 19.9, 20.4]
        cols = 4
        tw, th = W // 2, H // 2
        rows = (len(ts) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
        for k, tt in enumerate(ts):
            im = film.frame(int(tt * FPS)).resize((tw, th), Image.LANCZOS)
            ImageDraw.Draw(im).text((6, 4), f"{tt:.2f}", fill=(255, 255, 0))
            sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
        out = HERE / "stills" / "c25_scene_pilot"
        out.mkdir(parents=True, exist_ok=True)
        sheet.save(out / "sheet.png")
        print("sheet ->", out / "sheet.png")
    else:
        film.render()
