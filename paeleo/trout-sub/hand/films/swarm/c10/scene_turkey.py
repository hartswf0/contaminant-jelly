"""c10 · scene_turkey · Turkey thinks (board part II, 18.0 to 31.5 s of the film).

T0  0.0 ..  2.5  the pick: the red circle button on a card that flips up on its brad; the shell talks behind it
B1  2.5 ..  6.0  bolt 1, die 1, Probable      "The trout to be outside."
B2  6.0 ..  9.5  bolt 2, die 2, Plausible     "He does not get back."
B3  9.5 .. 13.5  bolt 3, die 3, Preposterous  "The turkey gets back."

Fixed view: Turkey's seat inside the tin, the six-bolt brass porthole, the AIR dial, Turkey freaking out (the
pilot's word) in every frame, his loose feather stuck to the glass, little french fries outside in every scene.
Everything comes from world.py (handmade cut paper); the dock ladder, the surface, the kitchen wall and the water
drops are built here from the world's own cut-paper tools. Nothing is foraged.

The porthole's rule (Single Hinge): each new ending is a round card that swings in behind the glass about ONE
brad on the rim of the ring; the shell turns on its pin; each die flips down about its own bolt; each fry tips
about its middle pin; the pick card flips about its corner brad; in bolt 3 the whole river turns about the
shell's pin. Loose things lag and settle inside a second (Wd.settle).

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink).
Test:  python3 films/swarm/c10/scene_turkey.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp
Tm, Rm = Wd.Tm, Wd.Rm

SECONDS = 13.5
T_B1, T_B2, T_B3 = 2.5, 6.0, 9.5
CAPTIONS = [
    (2.5, 6.0, "The trout to be outside."),
    (6.0, 9.5, "He does not get back."),
    (9.5, 13.5, "The turkey gets back."),
]

PORT = Wd.PORT                      # (560, 246)
R = Wd.PORT_R                       # 178
PAGE_PIN = (PORT[0] - 131, PORT[1] - 131)     # the brad every new ending swings in on (rim of the ring, upper left)
GAUGE = (880, 150)
TURKEY = (150, 478, 1.62)
STUCK = (410, 196)                  # the loose feather stuck to the glass since the pilot's page
SWING = 0.45
HALF = 0.5                          # where the pilot's page left the needle


# ------------------------------------------------------------ helpers ---
def _bump(t, a, b, c):
    if t <= a or t >= c:
        return 0.0
    return ease(t, a, b) if t < b else 1 - ease(t, b, c)


def _arc_between(a, b, u, bulge=0.35):
    """A point a fraction u along a circular arc from a to b (one turn about one centre)."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    c = (mx - dy / (2 * bulge) * 0.5, my + dx / (2 * bulge) * 0.5)
    a0 = math.atan2(a[1] - c[1], a[0] - c[0])
    a1 = math.atan2(b[1] - c[1], b[0] - c[0])
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    r = math.hypot(a[0] - c[0], a[1] - c[1])
    th = a0 + d * u
    return (c[0] + r * math.cos(th), c[1] + r * math.sin(th))


def _fry_school(tgt, spots, t, kicks=(), amp=20.0, scale=0.4, seed=0):
    """Little french fries, each a rigid crinkle strip tipping about its own middle pin (the brad shows).
    After each time in `kicks` they rock and come to rest inside a second."""
    rs = random.Random(seed)
    for k, (x, y) in enumerate(spots):
        ph = rs.uniform(0, 6.28)
        base = rs.uniform(-26, 26)
        a = base + 5 * math.sin(t * rs.uniform(0.7, 1.2) + ph)
        sg = rs.uniform(0.6, 1.2) * rs.choice((-1, 1))
        for kt in kicks:
            a += amp * sg * Wd.settle(t, kt + 0.04 * k, 1.0, 2.0, 4.2)
        s = scale * rs.uniform(0.85, 1.15)
        Wd.fry(tgt, x, y, s, a, seed * 7 + k)
        Wd.brad(tgt, x, y, max(2, int(round(3.4 * s))))


def _bubble_layer(items):
    """Ring bubbles: items = [(x, y, r, alpha 0..1)]."""
    S = 2
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x, y, r, al in items:
        a = int(240 * clamp(al))
        if a < 4:
            continue
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(232, 248, 242, int(a * 0.42)),
                  outline=(240, 250, 244, a), width=max(3, int(r * 0.22 * S)))
        d.arc([(x - r * 0.6) * S, (y - r * 0.6) * S, (x + r * 0.6) * S, (y + r * 0.6) * S], 190, 265, fill=(255, 255, 255, a), width=S)
    return lay.resize((W, H), Image.LANCZOS)


@lru_cache(None)
def _disc_mask():
    S = 2
    m = Image.new("L", (W * S, H * S), 0)
    r = R + 6
    ImageDraw.Draw(m).ellipse([(PORT[0] - r) * S, (PORT[1] - r) * S, (PORT[0] + r) * S, (PORT[1] + r) * S], fill=255)
    return m.resize((W, H), Image.LANCZOS)


def _disc_card(fn, *args):
    """An outside scene as a round card (what the glass shows), ready to swing on a pin."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    fn(img, *args)
    img = img.convert("RGBA")
    img.putalpha(_disc_mask())
    return img


# ----------------------------------------------- the intercom (T0, B1) ---
CLAM = (702, 150, 0.7)               # pin on the brick wall, the shell opening to the left
FRIES_A = [(446, 96), (498, 70), (590, 262), (660, 300), (452, 398), (560, 404), (640, 372), (610, 60), (706, 250)]
T0_FLAPS = (0.95, 1.5)
B1_FLAPS = (0.5, 1.05, 2.75)


def _intercom(tgt, T, u, flaps, trout=None):
    """River, brick flat, fries, (trout), and the clam shell flapping like something talking."""
    Wd.river(tgt, T, seed=0)
    Wd.brick_wall(tgt, 598, 0, 390, 540, seed=2, flip=True)
    _fry_school(tgt, FRIES_A, T, kicks=[T - u + f + 0.1 for f in flaps], amp=14, scale=0.4, seed=21)
    if trout:
        trout(tgt)
    g = 3.0
    for f in flaps:
        g += 38 * _bump(u, f, f + 0.12, f + 0.46)
    x, y, s = CLAM
    c = Wd.clam_pa(tgt, x, y, s, g, T, flip=True)
    for f in flaps:
        if f < u < f + 0.9:
            Wd.sound_rings(tgt, c["mouth"][0] + 26, c["mouth"][1], u - f, direction=180, n=3, r0=18, r1=200, arc=76,
                           strength=clamp(1.5 - 1.7 * (u - f)), rate=1.1, width=3.5)


def _t0_out(tgt, T, u):
    _intercom(tgt, T, u, T0_FLAPS)


# B1: three brook trout hold station out in the current, then swim up to the glass and stop on the far side of it.
B1_GO, B1_STOP, B1_TAP = 1.0, 2.1, 2.55
B1_TROUT = [   # (far x, y, scale), (near x, y, scale), kind, phase
    ((628, 300, 0.30), (488, 192, 0.60), 0, 0.0),
    ((588, 346, 0.30), (506, 290, 0.66), 2, 1.3),
    ((652, 372, 0.28), (524, 378, 0.56), 1, 2.4),
]
B1_NOSE = (506 - 120 * 0.66, 290 + 4)       # where the middle trout's nose meets the glass


def _b1_trout(T, u):
    def lay(tgt):
        v = ease(u, B1_GO, B1_STOP)
        for k, (far, near, kind, ph) in enumerate(B1_TROUT):
            x, y = _arc_between(far[:2], near[:2], v, bulge=0.5 if k != 1 else -0.6)
            s = lerp(far[2], near[2], v)
            dx = 0.0
            if k == 1:                        # one nose taps the glass, and the glass holds
                dx = -9 * _bump(u, B1_TAP - 0.14, B1_TAP, B1_TAP + 0.3)
            pose = "swim" if u < B1_STOP else "look"
            Wd.trout(tgt, x + dx, y, s, T, kind=kind, pose=pose, phase=ph, pitch=6 * math.sin(math.pi * v) * (1 if k else -1),
                     gaze=(-2.0, 0.4 - 0.6 * k))
    return lay


def _b1_out(tgt, T, u):
    _intercom(tgt, T, u, B1_FLAPS, _b1_trout(T, u))


# ----------------------------------- the way back and the lid (B2, B3) ---
BIG = (715, 215, 1.25)               # the same shell, hanging between the porthole and the light
OPEN = 58.0
B2_SHUT0, B2_SHUT1 = 2.0, 2.34          # the way back is held in view for a second and a half before the lid comes down
FRIES_B = [(432, 356), (540, 372), (668, 366), (586, 404), (474, 404)]


@lru_cache(None)
def _surface():
    """The bright surface, far up and to the left: a pale cut-paper strip with a rippled lower edge."""
    top = [(0, 0), (300, 0)]
    low = [(300 - 12 * k, 86 + (6 if k % 2 else -4)) for k in range(26)]
    return Wd.cut(top + low, (246, 250, 232), curve=False, seed=611, grain=0.05)


@lru_cache(None)
def _rail(n, thick, seed):
    return Wd._plank(int(n), int(thick), int(seed))


def _way_back(tgt, T):
    """Top left through the glass: the light of the surface and the foot of a dock ladder."""
    Wd.glow(tgt, 470, 120, 230, (236, 250, 232), 1.0)
    Wd.glow(tgt, 462, 104, 150, (255, 252, 226), 1.0)
    Wd.draw_sprite(tgt, _surface(), Tm(340, 30) @ Rm(1.2 * math.sin(T * 1.1)), (2, 5, 4, 0.3))
    # ladder: two rails and four rungs of plank, leaning a little
    M = Tm(462, 62) @ Rm(5.0)
    for k, yy in enumerate((34, 76, 118, 160)):
        Wd.draw_sprite(tgt, _rail(74, 11, 40 + k), M @ Tm(-4, yy), (2, 3, 2, 0.3))
    for xx, n in ((0, 186), (62, 198)):
        Wd.draw_sprite(tgt, _rail(n, 13, 30 + xx), M @ Tm(xx + 13, 0) @ Rm(90), (3, 4, 3, 0.35))


def _b2_gape(u):
    if u < B2_SHUT0:
        return OPEN + 2.0 * math.sin(u * 2.2)
    if u < B2_SHUT1:
        return OPEN * (1 - ramp(u, B2_SHUT0, B2_SHUT1) ** 2.2)        # like a lid coming down
    return max(0.0, 5.0 * Wd.settle(u, B2_SHUT1, 1.0, 3.2, 7.0))       # one small bounce, then shut for good


def _way_scene(tgt, T, u, gape, kick=None, flinch=None):
    Wd.river(tgt, T, seed=0)
    Wd.brick_wall(tgt, 660, 0, 340, 540, seed=2, flip=True)
    _way_back(tgt, T)
    kicks = [T - u + kick] if kick is not None else ()
    _fry_school(tgt, FRIES_B, T, kicks=kicks, amp=30, scale=0.4, seed=33)
    fl = Wd.settle(u, flinch, 1.0, 2.4, 4.0) if flinch is not None else 0.0
    up = 0.0 if flinch is None else ease(u, flinch - 0.3, flinch)
    Wd.trout(tgt, 470 - 8 * fl, 376, 0.36, T, kind=0, flip=True, pose="look", phase=0.4, pitch=10 + 6 * fl, gaze=(1.5, -2.2 + 1.5 * up))
    Wd.trout(tgt, 626 + 8 * fl, 392, 0.33, T, kind=2, pose="look", phase=1.9, pitch=8 - 6 * fl, gaze=(-1.5, -2.2 + 1.5 * up))
    x, y, s = BIG
    Wd.clam_pa(tgt, x, y, s, gape, T, flip=True, split=0.0)


def _b2_out(tgt, T, u):
    _way_scene(tgt, T, u, _b2_gape(u), kick=B2_SHUT1, flinch=B2_SHUT1)


# B3: the shell goes round the wrong way, a full half turn on its pin, and the world turns about that pin.
B3_BAT0, B3_BAT1 = 0.8, 1.22          # the valve's half turn
B3_HIT = 1.0                          # it meets the tin
B3_TURN0, B3_TURN1 = 1.0, 1.8         # the river sweeps down and out about the shell's pin
B3_HOME0, B3_HOME1 = 1.6, 2.2         # home swings in on the page pin
B3_FRY = (596, 392)                   # the one little french fry that stays stuck to the glass


def _b3_gape(u):
    return OPEN - 180.0 * ease(u, B3_BAT0, B3_BAT1) + (2.0 * math.sin(u * 2.2) if u < B3_BAT0 else 0.0)


def _b3_river(tgt, T, u):
    _way_scene(tgt, T, u, _b3_gape(u), kick=B3_HIT)


def _foam(tgt, T, u):
    """The surface breaking white across the glass."""
    img = Wd._img(tgt)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, H], fill=(206, 232, 226, 255))
    Wd.glow(tgt, PORT[0], PORT[1] - 40, 260, (255, 255, 250), 1.0)
    rs = random.Random(77)
    items = []
    for _ in range(90):
        x0, y0 = rs.uniform(370, 750), rs.uniform(40, 460)
        r = rs.uniform(5, 26)
        v = rs.uniform(260, 520)
        y = (y0 + v * (u - B3_TURN0)) % 440 + 30
        items.append((x0 + 8 * math.sin(u * 9 + r), y, r, 0.95))
    Wd._comp(tgt, _bubble_layer(items), (0, 0))


@lru_cache(None)
def _kitchen_wall():
    """Home: a warm papered kitchen wall, cut-paper tiles along the bottom."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    wall = Wd.cut([(0, 0), (W, 0), (W, H), (0, H)], (238, 214, 160), curve=False, seed=701, grain=0.08)
    Wd.draw_sprite(img, wall, Tm(0, 0), None)
    rs = random.Random(5)
    for x in range(330, 800, 46):                   # wallpaper stripes, each a strip of paper
        st = Wd.cut([(0, 0), (16, 0), (16, 330), (0, 330)], Wd.lt((226, 176, 104), rs.uniform(0.95, 1.06)), curve=False, seed=710 + x, grain=0.07)
        Wd.draw_sprite(img, st, Tm(x, 20), (1, 1, 1, 0.12))
    for j in range(2):                              # tiles
        for i in range(12):
            c = (236, 240, 232) if (i + j) % 2 else (150, 190, 200)
            tl = Wd.cut(Wd.rrect(0, 0, 42, 42, 3), Wd.lt(c, rs.uniform(0.94, 1.04)), curve=False, seed=730 + i + 20 * j, grain=0.06)
            Wd.draw_sprite(img, tl, Tm(318 + 44 * i, 372 + 44 * j), (1, 2, 1.5, 0.3))
    return img


TIN_S = 0.33
SHELF_Y = (204, 340)
SHELF_TINS = [(404, 0), (560, 0), (716, 0), (404, 1), (716, 1)]        # the gap is at (560, lower shelf)


@lru_cache(None)
def _home_still():
    """The kitchen shelf: a row of bread-roll tins, and one empty gap."""
    img = _kitchen_wall().copy()
    for sy in SHELF_Y:
        Wd.plank(img, 320, sy, 800, thick=16, seed=3 + sy)
        for bx in (372, 748):                       # brackets
            br = Wd.cut([(0, 0), (8, 0), (8, 30), (0, 30)], (70, 64, 60), curve=False, seed=760 + bx, grain=0.05)
            Wd.draw_sprite(img, br, Tm(bx, sy + 14), (1, 2, 1.5, 0.3))
    for k, (x, row) in enumerate(SHELF_TINS):
        y = SHELF_Y[row] - 84 * TIN_S
        p = Wd.tin(img, x, y, TIN_S, 0.0, mood="calm", lamp=0.0, spin=40.0 * k, latch=0.0)
        px, py = p["port"]
        pr = p["port_r"] - 0.5                      # nobody is in these: dark glass
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(30, 34, 36, 255))
        d.arc([px - pr * 0.7, py - pr * 0.7, px + pr * 0.7, py + pr * 0.7], 200, 260, fill=(200, 214, 210, 200), width=2)
    # the empty place on the lower shelf: the clean patch a tin has stood on
    d = ImageDraw.Draw(img, "RGBA")
    x0, x1, sy = 560 - 200 * TIN_S, 560 + 204 * TIN_S, SHELF_Y[1]
    d.rounded_rectangle([x0, sy - 148 * TIN_S - 8, x1, sy], radius=8, fill=(255, 240, 200, 70))
    d.rectangle([x0, sy, x1, sy + 3], fill=(206, 164, 112, 150))
    return img


def _drops(tgt, u):
    """River water running down the outside of the glass."""
    S = 2
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rs = random.Random(91)
    for _ in range(13):
        x = rs.uniform(392, 728)
        y0 = rs.uniform(40, 330)
        v = rs.uniform(26, 80)
        r = rs.uniform(3.0, 6.5)
        y = y0 + v * max(0.0, u - B3_HOME0)
        ln = rs.uniform(30, 110)
        wob = 2.5 * math.sin(y * 0.05 + x)
        d.line([((x) * S, (y - ln) * S), ((x + wob) * S, y * S)], fill=(214, 240, 236, 70), width=int(r * 0.6 * S))
        d.ellipse([(x + wob - r) * S, (y - r) * S, (x + wob + r) * S, (y + r * 1.25) * S], fill=(196, 230, 228, 190), outline=(246, 255, 250, 240), width=S)
        d.ellipse([(x + wob - r * 0.5) * S, (y - r * 0.5) * S, (x + wob) * S, y * S], fill=(255, 255, 255, 230))
    Wd._comp(tgt, lay.resize((W, H), Image.LANCZOS), (0, 0))


def _b3_out(ink, T, u):
    """Everything behind the glass in bolt 3, laid straight on the frame."""
    if u < B3_TURN0:
        _b3_river(ink, T, u)
    else:
        if u < B3_HOME1:
            _foam(ink, T, u)
            if u < B3_TURN1 + 0.05:
                a = -168.0 * ease(u, B3_TURN0, B3_TURN1) ** 1.25
                Wd.swing_card(ink, _disc_card(_b3_river, T, u), BIG[:2], a, pinned=False, shadow=0.5)
                Wd.brad(ink, BIG[0], BIG[1], 8)
        if u >= B3_HOME0:
            a = -170.0 * (1 - ease(u, B3_HOME0, B3_HOME1)) + 5.0 * Wd.settle(u, B3_HOME1, 1.0, 2.6, 5.0)
            home = _home_still().convert("RGBA")
            home.putalpha(_disc_mask())
            Wd.swing_card(ink, home, PAGE_PIN, a, pinned=False, shadow=0.5)
            _drops(ink, u)
    if u >= B3_HIT:           # one little french fry, flung against the glass, stays there
        v = ease(u, B3_HIT, B3_HIT + 0.35)
        x, y = _arc_between(FRIES_B[2], B3_FRY, v, bulge=0.6)
        ang = lerp(10, 64, v) + 22 * Wd.settle(u, B3_HIT + 0.35, 1.0, 2.2, 4.0) + 10 * Wd.settle(u, B3_HOME1, 1.0, 2.2, 4.0)
        sc = lerp(0.4, 0.8, v)
        Wd.fry(ink, x, y, sc, ang, 33 * 7 + 2)
        Wd.brad(ink, x, y, max(2, int(round(3.4 * sc))))


# ------------------------------------------------------------- inside ---
DIE_OFF = {1: (52, 7), 2: (22, 50), 3: (-30, 43)}     # the die sits on the ring beside its bolt (clockwise of it)


def _die(ink, n, bolts, u):
    """The die face flips down about its own bolt and settles."""
    bx, by = bolts[n]
    ox, oy = DIE_OFF[n]
    a = -84.0 * (1 - ease(u, 0.12, 0.42)) + 9.0 * Wd.settle(u, 0.42, 1.0, 2.6, 5.5)
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    Wd.die(ink, n, bx + ox * ca - oy * sa, by + ox * sa + oy * ca, size=40, angle=a)


def _inside(ink, T, u, bolt, level, turkey_dx=0.0, look=(1.5, -0.5), pose=None, turkey_dy=0.0, tag=True):
    c = Wd.cabin(ink, T, lit=(bolt,) if bolt else ())
    Wd.brad(ink, PAGE_PIN[0], PAGE_PIN[1], 7)
    Wd.feather(ink, STUCK[0], STUCK[1], 1.35, 28)                   # still stuck to the glass
    Wd.air_gauge(ink, GAUGE[0], GAUGE[1], clamp(level), t=T)
    x, y, s = TURKEY
    Wd.turkey(ink, x + turkey_dx, y + turkey_dy, s, "freak", T * 1.35, flip=True, look=look, shade=0.2, pose=pose)
    if bolt:
        _die(ink, bolt, c["bolts"], u)
        if tag:
            Wd.bolt_tag(ink, bolt)
    return c


def _swing_in(ink, fn, T, u):
    """A new ending: a round card behind the glass, swinging in about the page pin."""
    if u < SWING + 0.5:
        a = -172.0 * (1 - ease(u, 0.0, SWING)) + 4.0 * Wd.settle(u, SWING, 1.0, 3.0, 6.5)
        if abs(a) > 0.05:
            Wd.swing_card(ink, _disc_card(fn, T, u), PAGE_PIN, a, pinned=False, shadow=0.5)
            return
    fn(ink, T, u)


# ---------------------------------------------------------------- draw ---
def draw(t, ink):
    T = max(0.0, min(float(t), SECONDS - 1e-6))
    if T < T_B1:
        u = T
        _t0_out(ink, T, u)
        _inside(ink, T, u, None, HALF, turkey_dy=96 * (1 - ease(u, 2.1, 2.5)), turkey_dx=-10 * (1 - ease(u, 2.1, 2.5)))   # ducked under the card
        a = -104.0 * (1 - ease(u, 0.12, 0.6)) + 5.0 * Wd.settle(u, 0.6, 1.0, 2.8, 6.0) - 104.0 * ease(u, 2.08, 2.5) ** 1.4
        Wd.pick_card(ink, "circle", "Turkey thinks", "Morning intercom", "M.", angle=a, pin_at=(22, 22),
                     drawn=ramp(u, 0.75, 1.45), pressed=ease(u, 0.6, 0.78), lit=ease(u, 0.6, 0.9))
    elif T < T_B2:
        u = T - T_B1
        _t0_out(ink, T, T_B1)                                        # the scene before, under the new card
        _swing_in(ink, _b1_out, T, u)
        _inside(ink, T, u, 1, HALF - 0.1 * ease(u, B1_FLAPS[0], B1_FLAPS[0] + 0.3) + 0.04 * Wd.settle(u, B1_FLAPS[0] + 0.3, 1.0, 3.0, 5.0))
        if B1_TAP - 0.02 < u < B1_TAP + 0.7:                         # the tap, and the glass holding
            Wd.sound_rings(ink, B1_NOSE[0], B1_NOSE[1], u - B1_TAP + 0.1, direction=0, n=2, r0=5, r1=36, arc=360,
                           strength=clamp(1.5 - 2.0 * (u - B1_TAP)), rate=1.3, width=3.0)
    elif T < T_B3:
        u = T - T_B2
        if u < SWING + 0.5:
            _b1_out(ink, T, T_B2 - T_B1)
        _swing_in(ink, _b2_out, T, u)
        level = HALF - 0.4 * ease(u, B2_SHUT0, B2_SHUT1 + 0.45) + 0.04 * Wd.settle(u, B2_SHUT1 + 0.45, 1.0, 3.0, 5.0)
        press = ease(u, B2_SHUT1 - 0.1, B2_SHUT1 + 0.45)
        _inside(ink, T, u, 2, level, turkey_dx=58 * press, look=(2.4, -1.2))
    else:
        u = T - T_B3
        if u < SWING + 0.5:
            _b2_out(ink, T, T_B3 - T_B2)
            _swing_in(ink, _b3_river, T, u)
        else:
            _b3_out(ink, T, u)
        level = HALF - 0.1 * ease(u, B3_HIT, B3_HIT + 0.2) + 0.6 * ease(u, B3_HOME1 - 0.1, B3_HOME1 + 0.6) + 0.07 * Wd.settle(u, B3_HOME1 + 0.6, 1.0, 2.6, 4.5)
        thrown = Wd.settle(u, B3_HIT, 1.0, 1.7, 2.6)
        _inside(ink, T, u, 3, level, turkey_dx=-26 * thrown, look=(2.0, 0.0), tag=False)
        # the whole tin is thrown: the cabin tips about the porthole and settles; beak, needle and dice keep their pins
        tip = 4.0 * thrown + 2.0 * Wd.settle(u, B3_HOME1, 1.0, 2.2, 4.0)
        if abs(tip) > 0.08:
            img = Wd._img(ink)
            rot = img.rotate(tip, resample=Image.BICUBIC, center=PORT, fillcolor=(22, 16, 12))
            img.paste(rot)
        Wd.bolt_tag(ink, 3)
    Wd.badge(ink)


# ---------------------------------------------------------------- test ---
if __name__ == "__main__":
    from kit import Film

    out = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("/tmp/c10_scene_turkey")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in sys.argv[2:] if not a.startswith("--")] or [
        0.3, 0.8, 1.1, 1.6, 2.3, 2.7, 3.1, 3.7, 4.3, 5.1, 5.8, 6.2, 6.9, 7.4, 7.6, 8.4, 9.4,
        9.7, 10.2, 10.45, 10.65, 10.9, 11.2, 11.5, 11.9, 12.6, 13.4]
    captions = "--captions" in sys.argv
    film = Film("c10_scene_turkey", SECONDS)

    def frame(t, ink):
        draw(t, ink)
        if captions:
            for a, b, text in CAPTIONS:
                if a <= t < b:
                    ink.caption(text, size=27)
    film.picture(frame)
    frames = []
    for tt in times:
        im = film.frame(int(round(tt * film.fps)))
        im.save(out / f"{tt:06.2f}.png")
        frames.append(im)
    Wd._sheet(frames, 4, out / "sheet.png", scale=0.5)
    print("wrote", out / "sheet.png")
