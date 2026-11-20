"""m33 · scene_trout · the next friend, e. (board beats W1 to W7, film seconds 57.0 to 80.0; this clock = film - 57).

W1   0.0 ..  1.4  the sheet has landed page 2 up and askew; the ochre left hand that took it by its far edge lies
                  flat on the right end of the "Draw the one you pick" row and squares it. A round slow `e` on the
                  name line, and a looped joined line running on from it that is not letters, as the eye drifts
                  down to "The trout think"                                                  (traces 31, 33)
W2   1.4 ..  4.0  the point hovers between the cross and the square; the eye goes LEFT across the gutter to E.'s
                  black button (the curls turn that way), holds, comes back; the square's button is coloured in,
                  evenly, inside its ring, lighter than the one it looked at                       (trace 32)
W3   4.0 ..  6.0  the sheet turned over to see what the pilot drew; a beat on the ring; the dive through it, landing
                  in Turkey's seat already facing the glass
W4   6.0 .. 11.2  THROUGH THE GLASS into open water; THE SWING ROUND to the left; the river looking back: the small
                  tin canted on the bed, a small black Turkey shoving in its small round window, the bars between it
                  and the wall, weed near the lens. The porthole brightens, a cone of light reaches out, on the wall
                  a pencil circle, then light, then the flickering shadow                         (traces 34, 12)
W5  11.2 .. 15.6  in through the small tin's porthole; up out of the ring to the desk; the sheet turned back. The
                  point rests under the printed "Movie"; then `a movie`, seven separate letters      (trace 34)
W6  15.6 .. 20.6  down one ending; `a`, the same letter in the same place, lighter. The point lifts to where the
                  next word would begin. From 16.6 NOTHING moves for 4.0 s but breath               (trace 35)
W7  20.6 .. 23.0  the eye and the hand go down to ending 6. The hand stays above the paper. It does not come down
                                                                                                    (trace 36)

Nobody on this sheet rubbed anything out. No thought opens at this desk after the river: the not-writing is the scene.
The dashed "Draw the one you pick" circle of this column cannot be seen in the photograph (trace 33): it is under the
ochre left hand in every frame of page 2 (covered() checks it).

Reuses the first friend's module beside this one (its sheet, desk camera and Turkey's seat) without editing it.
Exposes SECONDS, CAPTIONS (times from this module's start), draw(t, ink); also page2(t) / page2_done() (the sheet
images, 1520 x 1960), desk_frame(t), frame(t) (no badge) and view(t) for the editor.
Test:  python3 films/swarm/m33/scene_trout.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import importlib.util
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
FILMS = HERE.parents[1]
sys.path.insert(0, str(FILMS))
sys.path.insert(0, str(FILMS / "swarm" / "c33"))
import world as Wd  # noqa: E402   (the c33 world; not edited)
import cam  # noqa: E402
import people as P  # noqa: E402
from kit import Ink, clamp, ramp, ease, lerp  # noqa: E402


def _load_first_friend():
    name = "m33_scene_turkey"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "scene_turkey.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _load_first_friend()

W, H = 960, 540
key = cam.key

SECONDS = 23.0
CAPTIONS = [
    (15.6, 18.1, "A movie."),
]

OCHRE = "ochre"
HAIR = "curly"
WOOD = T.WOOD
S = T.S
SIZE = T.SIZE
SO, SC = T.SO, T.SC
B = T.B
Line = T.Line
_mid = T._mid

# ------------------------------------------------------------- the times ---
T_SQUARE = 0.5                      # the askew sheet is square
T_E = (0.55, 1.0)                   # e
T_LOOPS = (1.0, 1.4)                # the looped line that is not letters
T_BTN = (2.95, 4.0)                 # the square's button coloured in
T_FLIP1 = (4.0, 4.5)                # over, to the pilot's drawing
T_DIVE = (4.9, 6.0)
T_GLASS = (6.0, 7.2)
T_TURN = (7.2, 8.4)
T_RIVER = (8.4, 11.2)
T_IN = (11.2, 12.2)
T_UP = (12.2, 13.1)
T_FLIP2 = (13.1, 13.5)
T_MOVIE = (14.0, 15.6)              # a movie
T_A = (16.0, 16.6)                  # a
T_STILL = (16.6, 20.6)              # nothing moves
T_DOWN = (20.6, 21.2)

# ------------------------------------------------------- e.'s pencil marks ---
XH4 = 0.55 * (B(2, "bolt4.1")[3] - B(2, "bolt4.1")[1])        # big round letters
GAP = 6 * S                                                    # between letters


def _letters(box, text, seed, xh, gap=GAP, tall_last=1.0):
    """Letters made one at a time, each in its own place, wide apart (trace 34)."""
    x = box[0]
    strokes, idx = [], []
    k = 0
    for n, ch in enumerate(text):
        if ch == " ":
            x += 1.5 * xh
            continue
        ln = T._lettered((x, box[1], box[2] + 400, box[3]), ch, seed + n, xh, slant=0.0)
        sts = ln.strokes
        if n == len(text) - 1 and tall_last != 1.0:           # the last e a tall loop
            base = max(p[1] for st in sts for p in st)
            sts = [[(px, base - (base - py) * tall_last) for px, py in st] for st in sts]
        strokes += sts
        idx += [k] * len(sts)
        x = max(p[0] for st in sts for p in st) + gap
        k += 1
    return Line(strokes, xh, idx)


def _loops():
    """What runs on from the `e`: joined-up loops, large and soft, that are NOT letters, the last stroke sweeping
    away under the rule (trace 31)."""
    b = B(2, "name2.line")
    rs = random.Random(351)
    x0 = b[0] + 30 * S
    base = b[3] - 1.5 * S
    pts = []
    x = x0
    hs = [9, 15, 8, 9, 17, 8, 10]
    for n, h in enumerate(hs):
        h = h * S * rs.uniform(0.9, 1.1)
        wd = (5.2 if h < 12 * S else 3.6) * S
        for i in range(13):
            a = 2 * math.pi * i / 12
            pts.append((x + wd * (a / (2 * math.pi)) * 2.1 + wd * 0.9 * math.sin(a) * 0.5 + 0.12 * h * (1 - math.cos(a)) / 2,
                        base - h * (1 - math.cos(a)) / 2 + rs.uniform(-0.6, 0.6)))
        x += wd * 2.1
    ex, ey = pts[-1]
    pts += [(ex + 6 * S, ey + 2 * S), (ex + 2 * S, ey + 7 * S), (ex - 14 * S, ey + 8.5 * S), (ex - 34 * S, ey + 7 * S)]
    return Line([pts], 14.0)


def _hatch():
    """Even grey colouring inside the ring of the pink-square button, the printed square left clear (trace 32)."""
    b = B(2, "btn2b")
    cx, cy = _mid(b)
    rb = (b[2] - b[0]) / 2 * 0.90
    q = rb * 0.50
    rs = random.Random(352)
    ca, sa = math.cos(math.radians(-52)), math.sin(math.radians(-52))
    strokes = []
    n = 15
    for k in range(n):
        d = -rb * 0.93 + 2 * rb * 0.93 * k / (n - 1)
        half = math.sqrt(max(1.0, rb * rb - d * d))
        seg, cur = [], []
        for i in range(21):
            s = -half + 2 * half * i / 20
            x, y = cx + s * ca - d * sa, cy + s * sa + d * ca
            if abs(x - cx) < q and abs(y - cy) < q:
                if len(cur) > 1:
                    seg.append(cur)
                cur = []
            else:
                cur.append((x + rs.uniform(-0.5, 0.5), y + rs.uniform(-0.5, 0.5)))
        if len(cur) > 1:
            seg.append(cur)
        if k % 2:
            seg = [s[::-1] for s in seg[::-1]]
        strokes += seg
    return Line(strokes, 6.0)


@lru_cache(None)
def _plans():
    d = {}
    nb = B(2, "name2.line")
    d["e"] = T._lettered((nb[0] + 12 * S, nb[1], nb[2], nb[3]), "e", 350, 0.50 * (nb[3] - nb[1]), slant=0.0)
    d["loops"] = _loops()
    d["btn"] = _hatch()
    b = B(2, "bolt4.1")
    d["movie"] = _letters((b[0] + 8 * S, b[1], b[2], b[3]), "a movie", 353, XH4, tall_last=1.7)
    dy = B(2, "bolt5.1")[3] - b[3]
    a4 = d["movie"].part((0,))
    d["a"] = Line([[(x, y + dy) for x, y in st] for st in a4.strokes], XH4)      # the same letter, the same place
    return d


#          weight, width factor, graphite seed
STYLE = {"e": (0.85, 1.3, 350), "loops": (0.75, 1.15, 351), "btn": (0.7, 1.7, 352), "movie": (0.9, 1.45, 353), "a": (0.7, 1.45, 353)}
SPANS = {"e": T_E, "loops": T_LOOPS, "btn": T_BTN, "movie": T_MOVIE, "a": T_A}
ORDER = ["e", "loops", "btn", "movie", "a"]
_MARK_CIRCLE = False                # test only: paint the unseen circle so covered() can look for it


def _write(img, name, u):
    ln = _plans()[name]
    done, x, y, down = ln.upto(u)
    wt, wf, seed = STYLE[name]
    wd = max(1.5, ln.xh * 0.135) * (0.82 + 0.22 * wt) * wf            # a soft pencil: a rounder, greyer line
    P.graphite(img, done, wd, wt, seed)
    return x, y, down


@lru_cache(None)
def _base(n):
    if n == 0:
        img = T.page2(T.SECONDS + 1.0).copy()                         # E.'s whole column, as that child left it
        if _MARK_CIRCLE:
            c = B(2, "draw2.circle")
            ImageDraw.Draw(img).rectangle([c[0] - 2, c[1] - 2, c[2] + 2, c[3] + 2], fill=(255, 0, 255))
        return img
    img = _base(n - 1).copy()
    _write(img, ORDER[n - 1], 1.0)
    return img


def page2(t):
    """Page 2 as it stands at module second t (1520 x 1960)."""
    n = 0
    while n < len(ORDER) and SPANS[ORDER[n]][1] <= t:
        n += 1
    img = _base(n).copy()
    for name in ORDER[n:]:
        a, b = SPANS[name]
        if t > a:
            _write(img, name, ramp(t, a, b))
    return img


def page2_done():
    """Page 2 as the three children left it: `a movie`, `a`, and the rest clean."""
    return _base(len(ORDER)).copy()


# ------------------------------------------------------- the desk camera ---
def _ry(name, dy=0.0):
    return B(2, name)[3] + dy * S


CIRC = _mid(B(2, "draw2.circle"))                              # the circle nobody can see: under the left hand
HOLDC = (CIRC[0] + 1 * S, CIRC[1] + 9 * S)                     # the left palm's place on it
HOLD1 = (1400.0, 1750.0)                                       # ... and on the pilot's page (lower right corner)

#        tilt  log zoom        aim (sheet px)             held at (screen)
LAND = (40.0, math.log(1.0), 1000.0, 640.0, 440.0, 250.0)             # where the pass lands
NAME2 = (50.0, math.log(1.5), 940.0, 500.0, 330.0, 235.0)             # the top of the right column, from the gutter
PICKV = (50.0, math.log(1.5), 940.0, 650.0, 330.0, 250.0)             # the two trout plates and their buttons
EBTN = (52.0, math.log(1.2), 300.0, 670.0, 400.0, 240.0)              # across the gutter: E.'s black button
FRONT = T.READ1                                                       # the pilot's page from the seat
FLIPV = T.FLIPV                                                       # the eye down at the desk's edge
L4 = (46.0, math.log(1.5), 1000.0, _ry("bolt4.1", -8), 380.0, 300.0)
L5 = (46.0, math.log(1.5), 1000.0, _ry("bolt5.1", -8), 380.0, 300.0)
L6 = (46.0, math.log(1.5), 1000.0, _ry("bolt5.1", -8), 380.0, 260.0)  # the same frame, 40 px further down the page
L6UP = (44.5, math.log(1.46), 1000.0, _ry("bolt5.1", -8), 380.0, 260.0)   # the eye begins to stand up
CAM_KEYS = [(0.0, LAND), (0.55, NAME2), (0.95, NAME2), (1.4, PICKV), (1.6, PICKV), (2.1, EBTN), (2.5, EBTN), (2.9, PICKV),
            (4.0, PICKV), (4.25, FLIPV), (4.5, FRONT), (13.1, FRONT), (13.3, FLIPV), (13.5, L4), (15.6, L4), (16.0, L5),
            (20.6, L5), (21.2, L6), (22.75, L6), (23.0, L6UP)]
SHAKE_KEYS = [(0.0, 0.0), (0.6, 2.0), (3.9, 2.0), (4.0, 0.0), (4.5, 0.0), (4.7, 1.5), (4.9, 1.5), (12.2, 1.5), (13.0, 1.5),
              (13.1, 0.0), (13.5, 0.0), (13.7, 2.0), (15.9, 2.0), (16.4, 0.0), (23.0, 0.0)]


def view(t, shot=None):
    deg, lz, ax, ay, tx, ty = shot or key(t, CAM_KEYS, "smoother")
    return T.View(deg, math.exp(lz), (ax, ay), (tx, ty), 0.0 if shot else key(t, SHAKE_KEYS, "linear"), t)


def _angle(t):
    return 14.0 * (1 - cam.smooth(ramp(t, 0.05, T_SQUARE)))


def _zoom(v):
    return v.z * S


def _head(fr, t, v):
    """The back of a curly head, low in the frame when the eye is far enough back to have one."""
    z = _zoom(v)
    if z > 1.34:
        return
    look = math.sin(math.pi * cam.smooth(ramp(t, 1.6, 2.9))) if 1.6 < t < 2.9 else 0.0     # across the gutter
    y = 600 + 300 * clamp((z - 0.62) / 0.7) - 200 * look
    P.head_back(fr, 170 - 30 * look, y, OCHRE, 1.15, tilt=-10 * look, hair=HAIR, turn=-0.75 * look, t=t)


# ------------------------------------------------ where the right hand is ---
AWAY = (1380.0, 1500.0)
BETWEEN = ((_mid(B(2, "btn2a"))[0] + _mid(B(2, "btn2b"))[0]) / 2 + 8 * S, (_mid(B(2, "btn2a"))[1] + _mid(B(2, "btn2b"))[1]) / 2)
CROSS = (_mid(B(2, "btn2a"))[0] + 6 * S, _mid(B(2, "btn2a"))[1] + 3 * S)
SQUARE = (_mid(B(2, "btn2b"))[0] + 6 * S, _mid(B(2, "btn2b"))[1] + 1 * S)
MOVIE_WORD = (B(2, "plate2b")[0] + 53 * S, B(2, "plate2b")[3] - 3 * S)      # under the printed word "Movie"
RING_SIDE = (T.RING1[0] + 1.25 * T.RING_R, T.RING1[1] + 0.9 * T.RING_R)     # beside the pilot's ring
E6 = (B(2, "bolt6.1")[0] + 9 * S, B(2, "bolt6.1")[3] - 2 * S)               # where ending 6 would begin


def _next_word():
    a = _plans()["a"]
    return (a.x_end + 9 * S, a.end[1] - 1 * S)


def pen(t):
    """(sheet point, pose, lift) of e.'s right hand."""
    pl = _plans()

    def wr(name):
        x, y, down = pl[name].tip(ramp(t, *SPANS[name]))
        return (x, y), "write", 0 if down else 5

    if t < T_E[0]:
        f = cam.smooth(ramp(t, 0.1, T_E[0]))
        s = pl["e"].start
        return (lerp(AWAY[0] - 300, s[0], f), lerp(AWAY[1] - 700, s[1], f)), "hover", lerp(18, 4, f)
    if t < T_E[1]:
        return wr("e")
    if t < T_LOOPS[1]:
        return wr("loops")
    if t < T_BTN[0]:                                # between the cross and the square; it waits while she looks across
        p = key(t, [(T_LOOPS[1], pl["loops"].end), (1.5, CROSS), (1.62, CROSS), (1.78, BETWEEN), (2.72, BETWEEN), (2.86, SQUARE),
                    (T_BTN[0], pl["btn"].start)])
        return p, "hover", key(t, [(T_LOOPS[1], 4), (1.45, 14), (1.62, 12), (2.72, 14), (2.86, 9), (T_BTN[0], 2)])
    if t < T_BTN[1]:
        return wr("btn")
    if t < T_FLIP1[0] + 0.25:                       # the hand comes away for the turning over
        f = cam.smooth(ramp(t, T_BTN[1], T_FLIP1[0] + 0.25))
        e = pl["btn"].end
        return (lerp(e[0], AWAY[0], f), lerp(e[1], AWAY[1], f)), "hover", lerp(3, 18, f)
    if t < T_FLIP2[0] + 0.2:                        # page 1: the pencil waits beside the pilot's ring
        f = cam.smooth(ramp(t, 4.3, 4.75))
        g = cam.smooth(ramp(t, T_FLIP2[0], T_FLIP2[0] + 0.2))
        p = (lerp(AWAY[0], RING_SIDE[0], f), lerp(AWAY[1], RING_SIDE[1], f))
        return (lerp(p[0], AWAY[0], g), lerp(p[1], AWAY[1], g)), "hover", 16
    if t < T_MOVIE[0]:                              # the point rests under the printed word "Movie" (trace 34)
        s = pl["movie"].start
        p = key(t, [(T_FLIP2[0] + 0.2, AWAY), (13.55, MOVIE_WORD), (13.86, MOVIE_WORD), (T_MOVIE[0], s)])
        return p, "write", key(t, [(T_FLIP2[0] + 0.2, 16), (13.55, 1), (13.86, 1), (13.93, 8), (T_MOVIE[0], 2)])
    if t < T_MOVIE[1]:
        return wr("movie")
    if t < T_A[0]:
        f = cam.smooth(ramp(t, T_MOVIE[1], T_A[0]))
        e, s = pl["movie"].end, pl["a"].start
        return (lerp(e[0], s[0], f), lerp(e[1], s[1], f)), "write", 3 + 9 * math.sin(math.pi * f)
    if t < T_A[1] - 0.14:
        x, y, down = pl["a"].tip(ramp(t, T_A[0], T_A[1] - 0.14))
        return (x, y), "write", 0 if down else 5
    nw = _next_word()
    if t < T_A[1]:                                  # the point lifts to where the next word would begin
        f = cam.smooth(ramp(t, T_A[1] - 0.14, T_A[1]))
        e = pl["a"].end
        return (lerp(e[0], nw[0], f), lerp(e[1], nw[1], f)), "hover", lerp(2, 16, f)
    if t < T_DOWN[0]:                               # and does not move
        return nw, "hover", 16
    f = cam.smooth(ramp(t, *T_DOWN))                # down to ending 6; it stays above the paper
    return (lerp(nw[0], E6[0], f), lerp(nw[1], E6[1], f)), "hover", 16


def _right(fr, v, t):
    p, pose, lift = pen(t)
    arm = key(t, [(4.0, 74), (4.3, 66), (13.3, 66), (13.6, 82)])       # on her own column the hand lies under the line
    P.hand(fr, *v.pt(p), pose=pose, tone=OCHRE, scale=v.hs(p), t=t, lift=lift, arm=arm)


def _left_on_circle(fr, v, t, ang=0.0):
    """The ochre left hand, flat on the right end of the "Draw the one you pick" row: the circle is under it."""
    x, y = T._on_sheet(HOLDC, ang)
    k = 1.12
    if t >= T_A[1]:                                   # stuck: the flat hand does not stir
        t = T_A[1]
    P.hand(fr, *v.dpt(x, y), pose="hold", tone=OCHRE, scale=v.hs(HOLDC, k), flip=True, t=t, arm=84 + 0.5 * ang)


# ------------------------------------------------------------ desk frames ---
def desk_frame(t, shot=None):
    """e.'s desk at module second t: the whole over-the-shoulder picture (sheet, hands, head)."""
    v = view(t, shot)
    flip1 = T_FLIP1[0] <= t < T_FLIP1[1]
    flip2 = T_FLIP2[0] <= t < T_FLIP2[1]
    front = (T_FLIP1[0] + 0.25 <= t < T_FLIP2[0] + 0.2)
    lift = 0.0
    if flip1:
        lift = 26 * math.sin(math.pi * ramp(t, *T_FLIP1))
    if flip2:
        lift = 26 * math.sin(math.pi * ramp(t, *T_FLIP2))
    if front:                                        # the pilot's page
        fr = v.render(T._desktop(T.page1_done(), lift=lift))
        P.hand(fr, *v.pt(HOLD1), pose="hold", tone=OCHRE, scale=v.hs(HOLD1, 1.1), flip=True, t=t, arm=100,
               lift=(lift * 0.5) or None)
        _right(fr, v, t)
        _head(fr, t, v)
        return fr
    ang = _angle(t)
    fr = v.render(T._desktop(page2(t), angle=ang, lift=lift))
    _left_on_circle(fr, v, t, ang)
    _right(fr, v, t)
    _head(fr, t, v)
    return fr


def ring_xy(t):
    return view(t).pt(T.RING1)


# ------------------------------------------------------------- the river ---
T_LAMP = 9.2                        # the porthole brightens
T_PENCIL = (9.25, 9.85)             # a pencil circle on the wall
T_LIT = (9.8, 10.2)                 # light
T_SHADOW = (10.15, 10.5)            # the shadow in it
WRECK = dict(c=(196, 352), scale=0.56)        # the SMALL tin
PIC_C, PIC_R = Wd.RIVER["picture"], Wd.RIVER["picture_r"]


def seat(t):
    """Turkey's seat, already facing the glass: the pilot's pencil bars outside, the reflection shoving, the fog."""
    return T.view_out(t, fog=0.22, drift=(0, 0))


def open_water(t, shift=0.0):
    ink = Ink(t, int(t * 24))
    Wd.river_backdrop(ink, t, shift=shift, wall=False)
    return ink.img.convert("RGB")


@lru_cache(None)
def _pane_mask():
    m = Image.new("L", (W, H), 0)
    c, r = Wd.PORT_C, Wd.PORT_R - 5
    ImageDraw.Draw(m).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    return m.filter(ImageFilter.GaussianBlur(3))


FAR = 0.78


def beyond_glass(t, u):
    """What the window holds on the way out: open water, and in front of it the pane as it was from the seat (the
    pilot's pencil bars on paper-white, the reflection, the fog), which swells and goes by as the lens passes it."""
    water = open_water(t)
    if u >= 0.62:
        return water
    k = 1.0                                           # the pane sits in the window exactly as the seat showed it
    pane = seat(t).convert("RGBA")
    a = 1 - cam.smooth(clamp((u - 0.22) / 0.4))
    pane.putalpha(_pane_mask().point(lambda v: int(v * a)))
    d = 0.8 * cam.smooth(clamp(u / 0.62))
    return cam.shoot([(water, 100.0), (pane, 1.0, (0, (270 - Wd.PORT_C[1]) * k))], dolly=d, focus=100.0, aperture=0.05 * d, bg=(20, 60, 64))


def _river(t):
    """The river looking back: the small tin canted on the bed, the bars, the wall. Returns (picture, wreck points)."""
    ink = Ink(t, int(t * 24))
    lamp = ease(t, T_LAMP, T_LAMP + 0.5)
    Wd.river_backdrop(ink, t, dim=0.12 + 0.26 * lamp)
    lit = ease(t, *T_LIT)
    sh = ease(t, *T_SHADOW)
    if lit > 0:
        o = Ink(t, int(t * 24))
        o.img.paste(ink.img)
        o.d = ImageDraw.Draw(o.img, "RGBA")
        Wd.wall_picture(o, t, show=False, bar_shadows=False)
        if sh > 0:
            o2 = Ink(t, int(t * 24))
            o2.img.paste(ink.img)
            o2.d = ImageDraw.Draw(o2.img, "RGBA")
            Wd.wall_picture(o2, t, show=True, mood="shove")
            o.img = Image.blend(o.img, o2.img, sh)
        ink.img.paste(Image.blend(ink.img, o.img, lit))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    u = ramp(t, *T_PENCIL)
    if u > 0:                                        # first only a pencil circle (pale, as pencil shows on stone)
        n = max(2, int(84 * u))
        rs = random.Random(34)
        pts = [(PIC_C[0] + (PIC_R + 2 + 2.5 * math.sin(k * 0.37) + rs.uniform(-1, 1)) * math.cos(-2.2 + 6.45 * k / 80),
                PIC_C[1] + (PIC_R + 2 + 2.5 * math.cos(k * 0.29) + rs.uniform(-1, 1)) * math.sin(-2.2 + 6.45 * k / 80)) for k in range(n)]
        P.graphite(ink.img, [pts], 3.2, 1.0 - 0.55 * lit, 354, color=(226, 232, 214))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    tp = Wd.wreck(ink, t, mood="shove", dial=5.0, glow=0.55 + 0.45 * lamp, **WRECK)
    Wd.river_bars(ink)
    if lamp > 0:
        Wd.light_cone(ink, tp["port"], strength=lamp, t=t)
    return ink.img.convert("RGB"), tp


@lru_cache(None)
def _weed_layers():
    """Weed near the lens, on its own sheet (it slides and blurs in front of everything)."""
    out = []
    for k in range(3):
        lay = Ink(0.0, 0)
        lay.img = Image.new("RGBA", (W + 240, H + 60), (0, 0, 0, 0))
        lay.d = ImageDraw.Draw(lay.img, "RGBA")
        lay.w, lay.h = lay.img.size
        tt = k * 0.5
        Wd.weed(lay, 120, H + 70, height=430, lean=10, t=tt, seed=3, n=6, spread=60, dark=0.75)
        Wd.weed(lay, W + 150, H + 80, height=330, lean=-12, t=tt, seed=8, n=5, spread=50, dark=0.75)
        out.append(lay.img)
    return out


def _river_cam(t):
    f = ramp(t, T_TURN[1], T_RIVER[1] + 1.0)
    return dict(x=-8 + 16 * f, y=2 * math.sin(t * 0.9), zoom=1.04 + 0.05 * f)


def river_frame(t):
    """The held shot: a slow drift towards the tin and its picture, weed close to the lens."""
    img, tp = _river(t)
    c = _river_cam(t)
    wl = _weed_layers()
    a = (t * 0.7) % 3
    k0, k1 = int(a) % 3, (int(a) + 1) % 3
    weed = Image.blend(wl[k0], wl[k1], a - int(a))
    fr = cam.shoot([(img, 1.0), (weed, 0.5)], focus=1.0, aperture=5, shake=1.2, t=t, bg=(10, 30, 34), **c)
    return fr, tp


def _port_on_screen(t, tp):
    c = _river_cam(t)
    x, y = cam.shoot_point(tp["port"][0], tp["port"][1], (W, H), 1.0, **c)
    return x, y, tp["port_r"] * c["zoom"]


# ------------------------------------------------------------------ draw ---
def frame(t):
    """The 960 x 540 picture at module second t, without the badge."""
    t = clamp(t, 0.0, SECONDS - 1e-4)
    if t < 0.6:                                       # the eye rolls a little as the sheet is squared, and settles
        e = math.sin(math.pi * ramp(t, 0.0, 0.6))
        return cam.shoot([(desk_frame(t), 1.0)], rot=-4 * e, zoom=1.0 + 0.035 * e, bg=WOOD)
    if t < T_DIVE[0]:
        return desk_frame(t)
    if t < T_DIVE[1]:                                 # down through the pilot's drawn ring, landing facing the glass
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat(t), rx, ry, ramp(t, *T_DIVE), spin=30)
    if t < T_GLASS[1]:                                # out through the glass
        u = ramp(t, *T_GLASS)
        return cam.through_glass(seat(t), beyond_glass(t, u), Wd.PORT_C[0], Wd.PORT_C[1], Wd.PORT_R, u, far=FAR)
    if t < T_TURN[1]:                                 # the swing round, to the left
        return cam.turn(open_water(t), river_frame(t)[0], ramp(t, *T_TURN), axis="y", direction=-1, side=open_water(t, shift=-260))
    if t < T_RIVER[1]:
        return river_frame(t)[0]
    if t < T_IN[1]:                                   # in through the small tin's porthole
        fr, tp = river_frame(t)
        x, y, r = _port_on_screen(t, tp)
        return cam.through_glass(fr, seat(t), x, y, r, ramp(t, *T_IN), far=0.5)
    if t < T_UP[1]:                                   # and up out of the ring, to the desk
        rx, ry = ring_xy(t)
        return cam.dive(desk_frame(t), seat(t), rx, ry, 1 - ramp(t, *T_UP))
    return desk_frame(t)


def draw(t, ink):
    fr = frame(t)
    ink.img.paste(fr.convert("RGB"))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    Wd.badge(ink)


# ------------------------------------------------------------------ test ---
def covered(ts=None):
    """Trace 33: paint the unseen circle magenta on the sheet and count the magenta that reaches the screen."""
    global _MARK_CIRCLE
    _MARK_CIRCLE = True
    _base.cache_clear()
    bad = []
    try:
        for t in ts or [k / 8 for k in range(0, int(SECONDS * 8))]:
            if T_DIVE[0] + 0.3 < t < T_UP[1] - 0.3:
                continue
            a = np.asarray(frame(t).convert("RGB"), np.int32)
            n = int(((a[..., 0] > 180) & (a[..., 1] < 110) & (a[..., 2] > 180)).sum())
            if n:
                bad.append((t, n))
    finally:
        _MARK_CIRCLE = False
        _base.cache_clear()
    return bad


def _test(argv):
    if "--covered" in argv:
        print("circle showing at:", covered())
        return
    out = Path(argv[0]) if argv and not argv[0].replace(".", "").isdigit() and not argv[0].startswith("--") else FILMS / "stills" / "m33_scene_trout"
    ts = [float(a) for a in argv if a.replace(".", "").isdigit()]
    caps = "--captions" in argv
    if not ts:
        ts = [0.0, 0.25, 0.5, 0.8, 1.2, 1.5, 1.9, 2.3, 2.7, 3.2, 3.6, 3.95, 4.15, 4.3, 4.7, 5.1, 5.4, 5.8, 6.1, 6.5, 6.9, 7.3,
              7.6, 7.9, 8.2, 8.6, 9.3, 9.7, 10.1, 10.6, 11.1, 11.4, 11.7, 12.0, 12.4, 12.8, 13.2, 13.4, 13.7, 14.3, 14.9, 15.5,
              15.9, 16.3, 16.6, 18.0, 20.5, 20.9, 21.4, 22.9]
    out.mkdir(parents=True, exist_ok=True)
    tiles = []
    for t in ts:
        ink = Ink(t, int(t * 24))
        draw(t, ink)
        if caps:
            for a, b, s in CAPTIONS:
                if a <= t < b:
                    ink.caption(s)
        im = ink.img.convert("RGB")
        im.save(out / f"{t:06.2f}.png")
        ImageDraw.Draw(im).text((8, 6), f"{t:.2f}", fill=(255, 255, 0))
        tiles.append(im.resize((480, 270), Image.LANCZOS))
    cols = 4
    for n in range(0, len(tiles), 16):
        part = tiles[n:n + 16]
        rows = (len(part) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 24))
        for i, im in enumerate(part):
            sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
        sheet.save(out / f"sheet{n // 16}.png")
    print("stills ->", out)


if __name__ == "__main__":
    _test([a for a in sys.argv[1:]])
