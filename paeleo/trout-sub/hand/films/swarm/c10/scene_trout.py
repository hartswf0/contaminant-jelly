"""c10 · scene_trout · The trout think (board part III, 31.5 to 46.5 s of the film).

R0   0.0 ..  2.5  the pick: the pink square button (coloured in) on a card that flips up on its brad; behind it
                  the tin is re-read as a lunchbox: a wire handle swings up, a paper tag swings down off the latch
B4   2.5 ..  6.0  bolt 4, die 4, Probable      "The trout to run."
B5   6.0 .. 10.0  bolt 5, die 5, Plausible     "The trout to throw a dance party."
B6  10.0 .. 15.0  bolt 6, die 6, Preposterous  "The trout to come inside the sub!"

Fixed view: the river side. The bread-roll tin against the elementary brick flat, its six-bolt porthole facing us
(hinge left, latch right and shut until bolt 6), Turkey behind the glass freaking out (the pilot's word) in every
frame, his loose feather stuck to the glass, the small air dial on the tin (half at the start of each bolt), the
clam-shell PA above, little french fries outside in every scene. Everything comes from world.py (handmade cut
paper); nothing is foraged.

The porthole's rule (Single Hinge): each new ending is a card that swings in about ONE corner brad; the shell
turns on its pin; the die flips down about its own bolt; each fry tips about its middle pin; each trout turns
about its own middle pin (a paper fish turning over); latch, door, handle, tag, lid and needle each turn on
theirs. Loose things lag and settle inside a second (Wd.settle).

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink).
Test:  python3 films/swarm/c10/scene_trout.py [out_dir] [t ...] [--captions]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

SECONDS = 15.0
T_B4, T_B5, T_B6 = 2.5, 6.0, 10.0
CAPTIONS = [
    (0.0, 2.5, "The trout think: Confiscated lunchbox"),
    (2.5, 6.0, "The trout to run."),
    (6.0, 10.0, "The trout to throw a dance party."),
    (10.0, 15.0, "The trout to come inside the sub!"),
]

SWING = 0.45                 # a new ending is a card swinging in on a corner brad
PAGE_PIN = (26, 26)
HALF = 0.5                   # where the pilot's page left the needle
NOTCH = 0.1
TIN = (330, 352, 1.0)        # the wide view (R0, B4, B5)
CLAM = (856, 118, 1.15)       # the shell's pin on the brick flat, opening to the left over the tin
WALL_X = 690
SEED = 1                     # the trout's side of the river


# ------------------------------------------------------------ helpers ---
def _bump(t, a, b, c):
    if t <= a or t >= c:
        return 0.0
    return ease(t, a, b) if t < b else 1 - ease(t, b, c)


def _fry_school(tgt, spots, t, kicks=(), amp=20.0, scale=0.62, seed=0, aim=None, aim_k=0.0):
    """Little french fries, each a rigid crinkle strip tipping about its own middle pin (the brad shows).
    After each time in `kicks` they rock and come to rest inside a second. aim = a point they tip toward."""
    rs = random.Random(seed)
    for k, (x, y) in enumerate(spots):
        ph = rs.uniform(0, 6.28)
        base = rs.uniform(-26, 26)
        a = base + 5 * math.sin(t * rs.uniform(0.7, 1.2) + ph)
        sg = rs.uniform(0.6, 1.2) * rs.choice((-1, 1))
        for kt in kicks:
            a += amp * sg * Wd.settle(t, kt + 0.04 * k, 1.0, 2.0, 4.2)
        s = scale * rs.uniform(0.85, 1.15)
        if aim is not None and aim_k > 0:
            want = math.degrees(math.atan2(aim[0] - x, -(aim[1] - y)))
            a = lerp(a, clamp(want, -52, 52), aim_k)
        Wd.fry(tgt, x, y, s, a, seed * 7 + k)
        Wd.brad(tgt, x, y, max(2, int(round(3.4 * s))))


def _bubble_layer(items):
    """Ring bubbles: items = [(x, y, r, alpha 0..1)]."""
    S = 2
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x, y, r, al in items:
        a = int(240 * clamp(al))
        if a < 4 or r < 0.6:
            continue
        d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(232, 248, 242, int(a * 0.36)),
                  outline=(240, 250, 244, a), width=max(2, int(r * 0.22 * S)))
        d.arc([(x - r * 0.6) * S, (y - r * 0.6) * S, (x + r * 0.6) * S, (y + r * 0.6) * S], 190, 265, fill=(255, 255, 255, a), width=S)
    return lay.resize((W, H), Image.LANCZOS)


def _trout_turn(tgt, x, y, s, T, c, pin=True, **kw):
    """A paper trout on its own middle pin. c = +1 faces left, -1 faces right; in between the fish is seen
    turning over about the pin (its width closes to an edge and opens again)."""
    flip = c < 0
    if abs(c) > 0.985:
        Wd.trout(tgt, x, y, s, T, flip=flip, **kw)
    else:
        half = int(190 * s + 30)
        lay = Image.new("RGBA", (half * 2, half * 2), (0, 0, 0, 0))
        Wd.trout(lay, half, half, s, T, flip=flip, **kw)
        w = max(3, int(round(half * 2 * abs(c))))
        lay = lay.resize((w, half * 2), Image.LANCZOS)
        Wd._comp(tgt, lay, (x - w / 2, y - half))
    if pin:
        Wd.brad(tgt, x, y, max(2, int(round(7 * s))))


def _die(tgt, n, port, s, u):
    """The die face flips down about its own bolt on the tin's porthole ring and settles; the bolt lights."""
    bx, by = Wd.bolt_xy(n, port[0], port[1], 47 * s, 64 * s)
    Wd.glow(tgt, bx, by, 30 * s, (255, 206, 110), ease(u, 0.1, 0.4))
    Wd.glow(tgt, bx, by, 12 * s, (255, 240, 190), ease(u, 0.1, 0.4))
    ox, oy = {4: (38, 30), 5: (-34, 30), 6: (-36, -26)}[n]
    a = -84.0 * (1 - ease(u, 0.12, 0.42)) + 9.0 * Wd.settle(u, 0.42, 1.0, 2.6, 5.5)
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    Wd.die(tgt, n, bx + ox * ca - oy * sa, by + ox * sa + oy * ca, size=40, angle=a)


def _clam(tgt, T, gape, pos=CLAM):
    x, y, s = pos
    return Wd.clam_pa(tgt, x, y, s, gape, T, flip=True, split=0.3)


def _back(tgt, T, wall_x=WALL_X):
    Wd.river(tgt, T, seed=SEED)
    Wd.brick_wall(tgt, wall_x, 0, W - wall_x + 40, 540, seed=2, flip=True)


def _tin(tgt, T, pos=TIN, **kw):
    """The tin with Turkey freaking out behind the glass and his loose feather stuck to it."""
    x, y, s = pos
    p = Wd.tin(tgt, x, y, s, T * 1.35, mood="freak", handle=kw.pop("handle", 1.0), **kw)
    return p


def _feather(tgt, p, s):
    Wd.feather(tgt, p["port"][0] + 20 * s, p["port"][1] - 20 * s, 0.75 * s, 28)


def _clap(tgt, p, s, u, at):
    """Turkey's beak claps the inside of the glass: the knock seen from outside."""
    if at - 0.02 < u < at + 0.6:
        Wd.sound_rings(tgt, p["port"][0], p["port"][1], u - at + 0.1, direction=0, n=2, r0=30 * s, r1=86 * s, arc=360,
                       strength=clamp(1.5 - 2.4 * (u - at)), rate=1.4, width=3.0)


# ------------------------------------------- the five trout (R0, B4) ---
# (x, y, scale, kind, phase, pitch): all nosing round the tin, noses toward it (facing left)
FIVE = [
    (474, 196, 0.45, 3, 0.7, -16),     # at the handle
    (692, 252, 0.50, 1, 1.9, -8),      # at the lid
    (706, 350, 0.55, 2, 3.1, 0),       # at the rudder
    (646, 430, 0.48, 0, 4.0, 5),       # at the skid
    (424, 410, 0.45, 1, 5.2, 4),       # at the tag
]
FRIES_W = [(52, 236), (112, 300), (60, 400), (150, 446), (250, 452), (380, 458), (520, 452), (560, 300), (208, 214), (806, 452), (900, 400)]


# ------------------------------------------------------------- R0 ---
def _r0(tgt, T, u):
    _back(tgt, T)
    for k, (x, y, s, kind, ph, pitch) in enumerate(FIVE[:3]):
        Wd.trout(tgt, x, y, s, T, kind=kind, pose="swim", phase=ph, pitch=pitch, gaze=(-1.5, 0.5))
    handle = clamp(ease(u, 0.95, 1.3) - 0.10 * abs(Wd.settle(u, 1.3, 1.0, 2.6, 5.0)))
    tag = -160.0 * (1 - ease(u, 1.45, 1.8) ** 1.5) + 16.0 * Wd.settle(u, 1.8, 1.0, 2.2, 4.0)
    p = _tin(tgt, T, handle=handle, tag=tag, latch=0.0, dial=HALF)
    _feather(tgt, p, TIN[2])
    for k, (x, y, s, kind, ph, pitch) in enumerate(FIVE[3:]):
        Wd.trout(tgt, x, y, s, T, kind=kind, pose="look", phase=ph, pitch=pitch, gaze=(-1.8, -0.8))
    _fry_school(tgt, FRIES_W, T, kicks=[T - u + 1.3, T - u + 1.8], amp=10, seed=41)
    _clam(tgt, T, 4.0 + 1.2 * math.sin(T * 1.3))
    Wd.river_plane(tgt, "front", T, 0.0, seed=SEED)
    a = -104.0 * (1 - ease(u, 0.12, 0.6)) + 5.0 * Wd.settle(u, 0.6, 1.0, 2.8, 6.0) - 104.0 * ease(u, 2.08, 2.5) ** 1.4
    Wd.pick_card(tgt, "square", "The trout think", "Confiscated lunchbox", "S.", angle=a, pin_at=(500, 22), size=(440, 240),
                 drawn=ramp(u, 0.75, 1.45), pressed=ease(u, 0.6, 0.78), lit=ease(u, 0.6, 0.9))


# ------------------------------------------------------------- B4 ---
B4_OPEN0, B4_SNAP0, B4_SNAP = 0.55, 1.08, 1.18
B4_TURN = 0.26


def _b4_gape(u):
    if u < B4_SNAP0:
        return 4.0 + 34.0 * ease(u, B4_OPEN0, B4_SNAP0 - 0.1)
    if u < B4_SNAP:
        return 38.0 * (1 - ramp(u, B4_SNAP0, B4_SNAP) ** 2)
    return max(0.0, 5.0 * Wd.settle(u, B4_SNAP, 1.0, 3.2, 7.0))


def _b4_fish(k, u):
    """Where trout k is: (x, y, c, running). It turns about its own middle, then is gone to the right."""
    x, y, s, kind, ph, pitch = FIVE[k]
    t0 = B4_SNAP + 0.03 + 0.05 * ((k * 2) % 5)
    c = 1 - 2 * ease(u, t0, t0 + B4_TURN)
    dt = max(0.0, u - (t0 + B4_TURN * 0.6))
    return x + 1000 * dt * dt + 200 * dt, y - 30 * dt * (1 if k < 2 else -0.3), c, dt > 0


def _b4_trail(u):
    items = []
    rs = random.Random(404)
    for k in range(5):
        x0, y0, s = FIVE[k][0], FIVE[k][1], FIVE[k][2]
        t0 = B4_SNAP + 0.03 + 0.05 * ((k * 2) % 5) + B4_TURN * 0.6
        for j in range(9):
            dt = 0.03 + 0.055 * j
            te = t0 + dt
            bx = x0 + 1000 * dt * dt + 200 * dt - 90 * s + rs.uniform(-6, 6)
            by = y0 + rs.uniform(-10, 10)
            r = rs.uniform(5.0, 10.0)
            if u > te and bx < W + 20:
                age = u - te
                items.append((bx + 5 * math.sin(age * 5 + j), by - 26 * age - 30 * (1 - math.exp(-age * 3)), r * min(1.0, 0.4 + age * 4), 1.0))
    return items


def _b4(tgt, T, u):
    _back(tgt, T)
    snap = T - u + B4_SNAP
    fish = [_b4_fish(k, u) for k in range(5)]

    def lay(k):
        x, y, c, run = fish[k]
        if x > W + 120:
            return
        _, _, s, kind, ph, pitch = FIVE[k]
        scared = u > B4_SNAP
        _trout_turn(tgt, x, y, s, T, c, kind=kind, pose="run" if run else "look", phase=ph,
                    pitch=pitch * (0 if scared else 1), gaze=(-1.8, -0.6) if not scared else (2.0, 0.0), jaw=14 if scared else None)
    for k in range(3):
        lay(k)
    level = HALF - NOTCH * ease(u, B4_SNAP, B4_SNAP + 0.25) + 0.04 * Wd.settle(u, B4_SNAP + 0.25, 1.0, 3.0, 5.0)
    p = _tin(tgt, T, tag=16.0 * Wd.settle(u, B4_SNAP + 0.05, 1.0, 1.8, 2.8), latch=0.0, dial=level)
    _feather(tgt, p, TIN[2])
    _clap(tgt, p, TIN[2], u, B4_SNAP - 0.04)
    for k in range(3, 5):
        lay(k)
    Wd._comp(tgt, _bubble_layer(_b4_trail(u)), (0, 0))
    _fry_school(tgt, FRIES_W, T, kicks=[snap + 0.12], amp=34, seed=41)
    _clam(tgt, T, _b4_gape(u))
    Wd.river_plane(tgt, "front", T, 0.0, seed=SEED)
    _die(tgt, 4, p["port"], TIN[2], u)
    Wd.bolt_tag(tgt, 4)


# ------------------------------------------------------------- B5 ---
B5_BEAT0, B5_PER, B5_FLAPS = 0.55, 0.42, 8
RING = (352, 308, 285, 138)                    # the dance floor: a ring round the lunchbox
B5_SPOTS = [0.25, 0.70, 2.35, 2.80, 4.50]      # two pairs and one, round the ring (radians)
LIGHTS = [(255, 120, 170), (255, 206, 110), (120, 220, 150), (130, 190, 255)]


def _b5_gape(u):
    g = 4.0
    for k in range(B5_FLAPS):
        f = B5_BEAT0 + B5_PER * k
        g += 34 * _bump(u, f, f + 0.1, f + 0.34)
    return g


def _b5_fish(k, T, u):
    go = ease(u, 0.2, 0.9)
    th = B5_SPOTS[k] + 0.95 * (u - 0.2) * go + 0.5
    cx, cy, rx, ry = RING
    sn = math.sin(th)
    return cx + rx * math.cos(th), cy + ry * sn, sn, clamp(sn * 5, -1, 1)


def _b5_puffs(tgt, mouth, u):
    """Each flap puffs a ring of bubbles that catches the light over the dancers."""
    items = []
    for k in range(B5_FLAPS):
        f = B5_BEAT0 + B5_PER * k + 0.08
        age = u - f
        if age <= 0 or age > 1.5:
            continue
        rs = random.Random(500 + k)
        grow = 1 - math.exp(-age * 2.2)
        cx = mouth[0] - 330 * grow
        cy = mouth[1] + 60 * grow - 18 * age
        R = 16 + 120 * grow
        col = LIGHTS[k % len(LIGHTS)]
        for j in range(11):
            a = 2 * math.pi * j / 11 + rs.uniform(-0.2, 0.2)
            bx, by = cx + R * math.cos(a) * 1.25, cy + R * math.sin(a) * 0.62
            r = rs.uniform(5, 10) * (1.0 if age < 1.1 else max(0.0, 1 - (age - 1.1) / 0.4))
            if r > 1:
                Wd.glow(tgt, bx, by, r * 3.4, col, 0.75)
                items.append((bx, by, r, 1.0))
    Wd._comp(tgt, _bubble_layer(items), (0, 0))


def _b5_notes(tgt, mouth, u):
    """The PA plays: a paper note leaves the shell on each second flap, swinging about the shell's own pin."""
    for k in range(0, B5_FLAPS, 2):
        f = B5_BEAT0 + B5_PER * k + 0.06
        age = u - f
        if age <= 0 or age > 1.7:
            continue
        r = math.hypot(mouth[0] - CLAM[0], mouth[1] - CLAM[1]) + 30 + 95 * age
        a = math.radians(178 - 20 * age * (1 if k % 4 else -0.6))
        Wd.music_note(tgt, CLAM[0] + r * math.cos(a), CLAM[1] - r * math.sin(a) * 0.9 - 10, 0.95, 14 * math.sin(age * 7 + k), kind=k // 2)


def _b5(tgt, T, u):
    _back(tgt, T)
    beat = max(0.0, u - B5_BEAT0)
    tb = beat / (B5_PER * 4)                     # the dance pose swings its tail at 2 per unit: one side per flap
    dancing = u >= B5_BEAT0
    fish = [_b5_fish(k, T, u) for k in range(5)]
    kinds = [3, 1, 2, 0, 1]

    def lay(k):
        x, y, sn, c = fish[k]
        s = 0.46 + 0.06 * sn
        _trout_turn(tgt, x, y, s, tb if dancing else T, c, kind=kinds[k], pose="dance" if dancing else "look", phase=0.0,
                    shade=0.12 if sn < 0 else 0.0, gaze=(-1.0, -0.5))
    for k in sorted(range(5), key=lambda k: fish[k][2]):
        if fish[k][2] < 0:
            lay(k)
    flaps = [B5_BEAT0 + B5_PER * k for k in range(B5_FLAPS)]
    level = HALF
    for n in (3, 7):
        level -= NOTCH * ease(u, flaps[n], flaps[n] + 0.25)
    p = _tin(tgt, T, tag=6.0 * math.sin(math.pi * beat / B5_PER) * (1 if dancing else 0), latch=0.0, dial=level)
    _feather(tgt, p, TIN[2])
    c = _clam(tgt, T, _b5_gape(u))
    _b5_puffs(tgt, c["mouth"], u)
    for k in sorted(range(5), key=lambda k: fish[k][2]):
        if fish[k][2] >= 0:
            lay(k)
    _b5_notes(tgt, c["mouth"], u)
    _fry_school(tgt, FRIES_W, T, kicks=[T - u + f + 0.08 for f in flaps], amp=13, seed=41)
    Wd.river_plane(tgt, "front", T, 0.0, seed=SEED)
    _die(tgt, 5, p["port"], TIN[2], u)
    Wd.bolt_tag(tgt, 5)


# ------------------------------------------------------------- B6 ---
S6 = 1.45
TIN6 = (540, 318)
CLAM6 = (880, 78, 0.72)
PORT6 = (TIN6[0] - 72 * S6, TIN6[1] + 2 * S6)
R6 = 47 * S6
B6_LATCH0, B6_LATCH1 = 0.7, 0.92
B6_DOOR0, B6_DOOR1 = 0.95, 1.4
DOOR_WIDE = 104.0
B6_IN0, B6_GAP, B6_DUR = 1.45, 0.36, 0.6
B6_SHUT0, B6_SHUT1 = 3.5, 3.85
B6_PULL0, B6_PULL1 = 4.0, 4.3
B6_BURP = 4.3
QUEUE = [(PORT6[0] - 64 * S6 - 44, PORT6[1] + 2), (PORT6[0] - 204, PORT6[1] + 22), (PORT6[0] - 270, PORT6[1] - 8),
         (PORT6[0] - 336, PORT6[1] + 26), (PORT6[0] - 402, PORT6[1] - 2), (PORT6[0] - 470, PORT6[1] + 20)]
QS = 0.36
# where each trout ends up behind the glass: (dx, dy, scale, pitch) from the porthole centre
INSIDE = [(4, 48, 0.31, -4), (40, -50, 0.29, 10), (16, 25, 0.29, 5), (58, -22, 0.29, -12), (22, 2, 0.28, 0)]
KIND6 = [0, 2, 1, 3, 1]
FRIES6 = [(486, 452), (548, 440), (604, 456), (660, 438), (712, 452), (196, 444), (120, 420), (286, 452), (770, 440)]


@lru_cache(None)
def _disc6(dy_q):
    S = 2
    m = Image.new("L", (W * S, H * S), 0)
    cy = PORT6[1] + dy_q
    ImageDraw.Draw(m).ellipse([(PORT6[0] - R6) * S, (cy - R6) * S, (PORT6[0] + R6) * S, (cy + R6) * S], fill=255)
    return m.resize((W, H), Image.LANCZOS)


def _mask6(dy, entering, door):
    """What of a trout shows: the hole, plus (for one coming in, or a tail left outside) everything left of the rim.
    Under the brass of a door that is part way shut, nothing shows."""
    m = _disc6(int(round(dy))).copy()
    d = ImageDraw.Draw(m)
    cy = PORT6[1] + dy
    if entering:
        d.rectangle([0, 0, PORT6[0] - R6 * 0.55, H], fill=255)
    if 0.5 < door < 90:
        c = math.cos(math.radians(door))
        hx = PORT6[0] - 64 * S6
        ex = hx + 64 * S6 * c
        ring = Image.new("L", (W, H), 0)
        dr = ImageDraw.Draw(ring)
        dr.ellipse([ex - 64 * S6 * c, cy - 64 * S6, ex + 64 * S6 * c, cy + 64 * S6], fill=255)
        dr.ellipse([ex - 47 * S6 * c, cy - 47 * S6, ex + 47 * S6 * c, cy + 47 * S6], fill=0)
        m = ImageChops.subtract(m, ring)
    return m


def _sheen6(tgt, dy):
    """The glass back over the trout: they are behind it now."""
    S = 2
    n = int(R6 * 2 + 8)
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n * S / 2
    r = R6 * S
    d.ellipse([c - r, c - r, c + r, c + r], fill=(200, 236, 226, 34))
    d.arc([c - r * 0.83, c - r * 0.87, c + r * 0.83, c + r * 0.87], 196, 262, fill=(255, 255, 250, 120), width=int(4 * S))
    d.arc([c - r * 0.66, c - r * 0.70, c + r * 0.66, c + r * 0.70], 20, 50, fill=(255, 255, 250, 90), width=int(3 * S))
    Wd._comp(tgt, im.resize((n, n), Image.LANCZOS), (PORT6[0] - n / 2, PORT6[1] + dy - n / 2))


def _queue_xy(q):
    q = clamp(q, 0, len(QUEUE) - 1)
    i = min(int(q), len(QUEUE) - 2)
    f = q - i
    return lerp(QUEUE[i][0], QUEUE[i + 1][0], f), lerp(QUEUE[i][1], QUEUE[i + 1][1], f)


def _b6(tgt, T, u):
    _back(tgt, T, 720)
    starts = [B6_IN0 + B6_GAP * k for k in range(5)]
    inn = [ease(u, s, s + B6_DUR) for s in starts]
    entered = sum(1 for v in inn if v >= 1.0)
    adv = sum(ease(u, s, s + B6_GAP) for s in starts)
    # the tin sits lower with every trout aboard
    sink = sum(3.4 * ease(u, s + B6_DUR - 0.15, s + B6_DUR + 0.1) for s in starts)
    sink += 3.0 * Wd.settle(u, starts[-1] + B6_DUR + 0.1, 1.0, 1.6, 3.5)
    pitch = -1.6 * ease(u, starts[2], starts[4] + B6_DUR) + 1.0 * Wd.settle(u, starts[-1] + B6_DUR + 0.1, 1.0, 1.6, 3.5)
    latch = clamp(ease(u, B6_LATCH0, B6_LATCH1) + 0.12 * Wd.settle(u, B6_LATCH1, 1.0, 3.0, 6.0))
    door = DOOR_WIDE * ease(u, B6_DOOR0, B6_DOOR1) * (1 - ease(u, B6_SHUT0, B6_SHUT1)) + 7.0 * Wd.settle(u, B6_DOOR1, 1.0, 2.4, 4.5) * (1 if u < B6_SHUT0 else 0)
    door = clamp(door + 5.0 * abs(Wd.settle(u, B6_SHUT1, 1.0, 3.0, 7.0)), 0, 180)
    level = HALF - 0.08 * sum(ease(u, s + B6_DUR - 0.2, s + B6_DUR) for s in starts) - 0.1 * ease(u, B6_BURP, B6_BURP + 0.3)
    level += 0.03 * Wd.settle(u, B6_BURP + 0.3, 1.0, 3.0, 5.0)
    lid = 1.6 * _bump(u, B6_BURP - 0.12, B6_BURP, B6_BURP + 0.4)
    tag = 14.0 * Wd.settle(u, B6_LATCH1, 1.0, 2.0, 3.2) + 10.0 * Wd.settle(u, B6_SHUT1, 1.0, 2.0, 3.5)
    p = Wd.tin(tgt, TIN6[0], TIN6[1] + sink, S6, T * 1.35, mood="freak", pitch=pitch, lid_open=lid, door_open=door, latch=latch,
               tag=tag, handle=1.0, dial=clamp(level), look=(-1.5, 0.0))
    dy = sink
    # trout behind the glass (the one time the layer order breaks) and trout on their way in
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pull = ease(u, B6_PULL0, B6_PULL1)
    any_in = False
    for k in range(5):
        if u < starts[k]:
            continue
        any_in = True
        v = inn[k]
        ix, iy, isc, ipitch = INSIDE[k]
        tx, ty = PORT6[0] + ix, PORT6[1] + iy + dy
        if k == 4:                                  # the last tail is left outside the seal, then pulled in
            tx -= 46 * (1 - pull)
        x = lerp(QUEUE[0][0], tx, v)
        y = lerp(QUEUE[0][1] + dy * 0, ty, v) - 14 * math.sin(math.pi * v) * (1 if k % 2 else -1)
        s = lerp(QS, isc, v)
        tail_out = k == 4 and pull < 1.0
        one = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        Wd.trout(one, x, y, s, T, kind=KIND6[k], flip=True, pose="swim" if v < 1 else "look", phase=1.3 * k,
                 pitch=ipitch * v, gaze=(1.6, -0.4), drop=v < 1 or tail_out)
        if v < 1.0 or tail_out:
            one.putalpha(ImageChops.multiply(one.getchannel("A"), _mask6(dy, True, 0.0)))
            out.alpha_composite(one)
        else:
            lay.alpha_composite(one)
    if any_in:
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), _mask6(dy, False, door)))
        Wd._comp(tgt, lay, (0, 0))
        if door < 1.0:
            _sheen6(tgt, dy)
    if door < 1.0:                                  # the loose feather is on the door's glass
        Wd.feather(tgt, p["port"][0] + 20 * S6, p["port"][1] - 20 * S6, 0.75 * S6, 28)
    Wd._comp(tgt, out, (0, 0))
    # the line at the glass, moving up as each goes in
    for k in range(4, -1, -1):
        if u >= starts[k]:
            continue
        x, y = _queue_xy(k - adv)
        Wd.trout(tgt, x, y, QS, T, kind=KIND6[k], flip=True, pose="look" if u < B6_DOOR0 else "swim", phase=1.3 * k,
                 gaze=(1.8, -0.3), pitch=3 * math.sin(T * 1.3 + k))
    # the burp: one big bubble out of the vent under the lid
    if u > B6_BURP - 0.05:
        age = u - B6_BURP + 0.05
        hx, hy = p["hatch"]
        r = 10 + 22 * (1 - math.exp(-age * 5))
        items = [(hx + 30 + 8 * math.sin(age * 6), hy - 12 - 250 * age * age - 60 * age, r, 1.0)]
        for j in range(4):
            a2 = age - 0.1 - 0.07 * j
            if a2 > 0:
                items.append((hx + 14 + 22 * j + 5 * math.sin(a2 * 8 + j), hy - 8 - 200 * a2 * a2 - 50 * a2, 5 + 2 * (j % 2), 1.0))
        Wd._comp(tgt, _bubble_layer(items), (0, 0))
    # nobody left outside but the little french fries, looking at the tag
    kicks = [T - u + B6_DOOR1, T - u + B6_SHUT1]
    tag_at = (p["latch"][0] + 2, p["latch"][1] + 62 * S6 * 0.75)
    _fry_school(tgt, FRIES6, T, kicks=kicks, amp=20, seed=63, aim=tag_at,
                aim_k=clamp(ease(u, B6_SHUT1 + 0.15, B6_SHUT1 + 0.6) - 0.15 * Wd.settle(u, B6_SHUT1 + 0.6, 1.0, 2.2, 4.0)))
    _clam(tgt, T, 4.0 + 1.2 * math.sin(T * 1.3) + 14 * _bump(u, B6_SHUT1 - 0.1, B6_SHUT1, B6_SHUT1 + 0.4), CLAM6)
    Wd.river_plane(tgt, "front", T, 0.0, seed=SEED)
    _die(tgt, 6, (PORT6[0], PORT6[1] + dy), S6, u)
    Wd.bolt_tag(tgt, 6)


# ---------------------------------------------------------------- draw ---
SCENES = [(0.0, _r0), (T_B4, _b4), (T_B5, _b5), (T_B6, _b6)]


def draw(t, ink):
    T = max(0.0, min(float(t), SECONDS - 1e-6))
    k = max(i for i, (s, _) in enumerate(SCENES) if T >= s)
    start, fn = SCENES[k]
    u = T - start
    if k > 0 and u < SWING + 0.45:
        a = -96.0 * (1 - ease(u, 0.0, SWING)) + 3.0 * Wd.settle(u, SWING, 1.0, 3.0, 6.5)
        if abs(a) > 0.05:
            pstart, pfn = SCENES[k - 1]
            pfn(ink, T, start - pstart - 1e-3)          # the ending before, under the new card
            card = Image.new("RGB", (W, H), (0, 0, 0))
            fn(card, T, u)
            Wd.swing_card(ink, card, PAGE_PIN, angle=a)
            Wd.badge(ink)
            return
    fn(ink, T, u)
    if k > 0:
        Wd.brad(ink, PAGE_PIN[0], PAGE_PIN[1], 7)
    Wd.badge(ink)


# ---------------------------------------------------------------- test ---
if __name__ == "__main__":
    from kit import Film

    out = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("/tmp/c10_scene_trout")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in sys.argv[2:] if not a.startswith("--")] or [
        0.1, 0.5, 1.0, 1.5, 1.9, 2.3, 2.7, 3.2, 3.6, 3.75, 3.9, 4.1, 4.6, 5.8,
        6.2, 6.8, 7.3, 7.9, 8.5, 9.1, 9.9, 10.2, 10.6, 10.9, 11.3, 11.6, 12.0, 12.4, 12.9, 13.3, 13.7, 14.1, 14.4, 14.9]
    captions = "--captions" in sys.argv
    film = Film("c10_scene_trout", SECONDS)

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
