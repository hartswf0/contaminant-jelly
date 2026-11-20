"""c10 · scene_pilot · the pilot's page (board part I, 0.0 to 18.0 s of the film).

P1  0.0 ..  8.0  the child's drawing is made in pencil, stroke by stroke, on the table; a brad makes it a jaw
P2  8.0 .. 11.5  "Little french fries. A new locked school."
P3 11.5 .. 14.5  "Freak out."
P4 14.5 .. 18.0  "It is a big container, so it probably takes it up."

Everything comes from world.py (handmade cut paper); nothing is foraged here. The porthole's rule (Single Hinge):
every move below is a turn about one pin: the pencil about the heel of the hand, the paper and each new scene
about a corner brad, the shell about its pin, the fry about its middle pin, the needle about its pivot.

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink).
Test:  python3 films/swarm/c10/scene_pilot.py [out_dir] [t ...]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

W, H = Wd.W, Wd.H
ease, ramp, lerp, clamp = Wd.ease, Wd.ramp, Wd.lerp, Wd.clamp

SECONDS = 18.0
T_P2, T_P3, T_P4 = 8.0, 11.5, 14.5
CAPTIONS = [
    (8.0, 11.5, "Little french fries. A new locked school."),
    (11.5, 14.5, "Freak out."),
    (14.5, 18.0, "It is a big container, so it probably takes it up."),
]

# ------------------------------------------------------------------ P1 ---
RING = (400, 262, 0.8)                       # sheet ring centre and scale (as WORLD.md's example)
HINGE = (RING[0] + (670 - 752) * RING[2], RING[1] + (650 - 772) * RING[2])   # back (left) corner of the jaw
HEEL = (760, 640)                            # heel of the drawing hand: the pencil turns about it
BRAD_REST = (78, 236)                        # the brad waits on the table, left of the paper


@lru_cache(None)
def _stroke_ends():
    """Progress value at the end of each of the 17 strokes (pen lifts), from the world's own path."""
    try:
        path = Wd._pilot(int(round(RING[2] * 100)), "all")[4]
        ends = [p for p, _, _, down in path if not down and p > 0]
        ends = sorted(set(round(e, 5) for e in ends))
        if len(ends) >= 17:
            return ends[:17]
    except Exception:
        pass
    j, o = Wd.JAW_SHARE, 1 - Wd.JAW_SHARE
    return [j * (k + 1) / 13 for k in range(13)] + [j + o * (k + 1) / 4 for k in range(4)]


def _progress(t):
    """Board timing: top 0.15..0.8, left ..1.5, bottom lines ..2.6, teeth ..5.4, hop, the outside jaw 5.8..7.4."""
    e = _stroke_ends()
    keys = [(0.15, 0.0), (0.8, e[0]), (1.5, e[1]), (2.6, e[4]), (5.4, e[12]), (5.8, e[12] + 0.004), (7.4, 1.0)]
    if t <= keys[0][0]:
        return 0.0
    for (ta, pa), (tb, pb) in zip(keys, keys[1:]):
        if t <= tb:
            return lerp(pa, pb, (t - ta) / (tb - ta))
    return 1.0


@lru_cache(None)
def _split_layers():
    """The finished drawing as two transparent layers: the jaw's top edge (stroke 1), and everything else."""
    cx, cy, sc = RING
    full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Wd.pilot_drawing(full, cx, cy, 1.0, sc)
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Wd.pilot_drawing(top, cx, cy, _stroke_ends()[0] - 0.002, sc)
    a = np.asarray(full).copy()
    b = np.asarray(top)
    a[..., 3] = np.clip(a[..., 3].astype(np.int16) - b[..., 3].astype(np.int16), 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA"), top


def _rot_about(p, c, deg):
    a = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


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


def _pencil_angle(tx, ty):
    """The pencil turns about the heel of the hand; out past the ring the hand has moved over, so it leans back."""
    return math.degrees(math.atan2(HEEL[1] - ty, HEEL[0] - tx)) * 0.55 - 78 - 62 * ease(tx, 560, 720)


def _table_scene(tgt, t):
    """P1. t = module seconds 0..8 (later = finished)."""
    cx, cy, sc = RING
    Wd.desk(tgt)
    Wd.sheet_ring(tgt, cx, cy, sc)
    P = _progress(t)
    # the brad: waits on the table, is carried over on one arc, pressed through the back corner of the jaw
    ub = ease(t, 7.38, 7.68)
    bx, by = _arc_between(BRAD_REST, HINGE, ub)
    hop = math.sin(math.pi * ub)
    if t < 7.72:
        Wd.pilot_drawing(tgt, cx, cy, P, sc)
    else:
        # the top edge lifts a few degrees on the brad and drops back: the drawing is a jaw
        lift = 14.0 * math.sin(math.pi * ramp(t, 7.72, 7.94)) ** 0.8 if t < 7.94 else 2.2 * Wd.settle(t, 7.94, 1.0, 5.0, 9.0)
        rest, top = _split_layers()
        Wd._comp(tgt, rest, (0, 0))
        if abs(lift) < 0.05:
            Wd._comp(tgt, top, (0, 0))
        else:
            Wd.swing_card(tgt, top, HINGE, -lift, pinned=False, shadow=0)
    if hop > 0.02:      # shadow slides away while the brad is in the air
        img = Wd._img(tgt)
        d = ImageDraw.Draw(img, "RGBA")
        o = 10 * hop
        d.ellipse([bx - 6 + o, by - 4 + o * 1.4, bx + 8 + o, by + 8 + o * 1.4], fill=(20, 16, 12, 60))
    Wd.brad(tgt, bx, by - 5 * hop, 7)
    # the pencil: every stroke is an arc about the heel of the hand
    if t < 7.4:
        tx, ty, down = Wd.pilot_tip(cx, cy, P, sc)
        if t < 0.15:
            down = False
        ang = _pencil_angle(tx, ty)
        lift = 0 if down else 14
        if t < 0.15:
            lift = 14 + 60 * (1 - ease(t, 0.0, 0.15))
        Wd.pencil(tgt, tx, ty, angle=ang, lift=lift)
    elif t < 7.95:
        tx, ty, _ = Wd.pilot_tip(cx, cy, 1.0, sc)
        u = ease(t, 7.4, 7.95)
        px, py = _rot_about((tx, ty), (tx - 60, ty + 420), 30 * u)       # swings off to the right about the heel
        ang = _pencil_angle(tx, ty) + 40 * u
        Wd.pencil(tgt, px, py, angle=ang, lift=14 + 30 * u)


@lru_cache(None)
def _table_done():
    img = Image.new("RGB", (W, H), Wd.PAL["table"])
    _table_scene(img, 7.999)
    return img


# ------------------------------------------------------- shared helpers ---
def _bump(t, a, b, c):
    """0 at a, 1 at b (fast), back to 0 at c."""
    if t <= a or t >= c:
        return 0.0
    return ease(t, a, b) if t < b else 1 - ease(t, b, c)


def _one_fry(tgt, x, y, scale, angle, seed):
    """A fry and the visible pin it tips about."""
    Wd.fry(tgt, x, y, scale, angle, seed)
    Wd.brad(tgt, x, y, max(2, int(round(3.2 * scale))))


def _fry_school(tgt, spots, t, kick_t=None, amp=18.0, scale=0.4, seed=0, pins=False):
    """Little french fries, each a rigid strip tipping about its own middle pin. After `kick_t` they rock and
    come to rest inside a second (secondary motion)."""
    rs = random.Random(seed)
    for k, (x, y) in enumerate(spots):
        ph = rs.uniform(0, 6.28)
        base = rs.uniform(-26, 26)
        a = base + 5 * math.sin(t * rs.uniform(0.7, 1.2) + ph)
        if kick_t is not None:
            a += amp * rs.uniform(0.6, 1.2) * rs.choice((-1, 1)) * Wd.settle(t, kick_t + 0.04 * k, 1.0, 2.0, 4.2)
        s = scale * rs.uniform(0.85, 1.15)
        Wd.fry(tgt, x, y, s, a, seed * 7 + k)
        if pins:
            Wd.brad(tgt, x, y, max(2, int(round(3.2 * s))))


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


# ------------------------------------------------------------------ P2 ---
# River side, wide: the brick flat with the clam-shell PA over the clean, locked tin; little fries outside.
P2_TIN = (420, 360, 1.1)
P2_FRIES = [(96, 368), (150, 416), (74, 440), (204, 452), (124, 300), (176, 340), (228, 262), (60, 244), (262, 440),
            (318, 262), (150, 208), (330, 470), (400, 478)]


def _p2(tgt, u):
    """u = seconds since P2 began."""
    t = T_P2 + u
    Wd.river(tgt, t, seed=1)
    Wd.brick_wall(tgt, 650, 0, 340, 540, seed=2, flip=True)
    Wd.clam_pa(tgt, 690, 122, 0.9, 4.0 + 1.2 * math.sin(t * 1.3), t, flip=True)
    x, y, s = P2_TIN
    p = Wd.tin(tgt, x, y, s, t, mood="look", latch=0.0, dial=1.0)
    hit = 1.72                                              # the fry meets the latch
    Wd.padlock(tgt, p["bow"][0] - 4, p["bow"][1] + 2, 0.72, swing=7 * Wd.settle(u, hit, 1.0, 2.4, 3.6))
    _fry_school(tgt, P2_FRIES, t, kick_t=None, scale=0.42, seed=3)
    # one fry tips forward about its middle pin, bumps the latch, and rocks back. The latch does not move.
    lx, ly = p["latch"]
    half = 19.0                                             # a little fry
    c = (lx + 13, ly + 25)                                  # the fry's pin
    reach = math.degrees(math.atan2(lx + 9 - c[0], -(ly + 6 - c[1])))      # angle at which its top touches the latch
    rest = 30.0
    if u < hit:
        a = lerp(rest, reach, ease(u, 1.25, hit) ** 1.6)
    else:
        back = ease(u, hit, hit + 0.38)
        a = lerp(reach, rest, back) + 14 * Wd.settle(u, hit + 0.38, 1.0, 2.2, 4.0)
    _one_fry(tgt, c[0], c[1], 2 * half / 74.0 * 1.0, a, 4)
    if hit <= u < hit + 0.3:                                # the knock: two short tick marks at the latch
        img = Wd._img(tgt)
        d = ImageDraw.Draw(img, "RGBA")
        k = 1 - (u - hit) / 0.3
        for dx, dy in ((-10, -16), (4, -20), (16, -12)):
            d.line([(lx + dx * 0.6, ly + dy * 0.6), (lx + dx * (1.0 + 0.5 * (1 - k)), ly + dy * (1.0 + 0.5 * (1 - k)))],
                   fill=(255, 250, 230, int(230 * k)), width=3)
    Wd.river_plane(tgt, "front", t, 0.0, seed=1)


# ------------------------------------------------------------------ P3 ---
# The same set pushed in on the porthole: Turkey fills the glass and freaks out.
P3_S = 3.3
P3_PORT = (452, 286)
P3_FLAP = 0.95            # the shell flaps once
P3_STICK = (P3_PORT[0] + 78, P3_PORT[1] - 74)     # where the loose feather sticks to the glass


def _p3(tgt, u):
    t = T_P3 + u
    Wd.river(tgt, t, seed=1)
    s = P3_S
    freak = u >= P3_FLAP + 0.08
    shake = 0.0
    if freak:                                               # the tin rattles on its skid while he goes off
        shake = 1.6 * math.sin(u * 31) * clamp(1.4 - 0.25 * (u - P3_FLAP))
    p = Wd.tin(tgt, P3_PORT[0] + 72 * s, P3_PORT[1] - 2 * s, s, t * (1.35 if freak else 1.0), mood="freak" if freak else "look",
               pitch=shake * 0.25, latch=0.0, dial=1.0)
    # the loose feather: flung off on one arc, then stuck to the inside of the glass for good
    if u >= P3_FLAP + 0.45:
        uf = ease(u, P3_FLAP + 0.45, P3_FLAP + 1.0)
        start = (P3_PORT[0] - 10, P3_PORT[1] + 40)
        fx, fy = _arc_between(start, P3_STICK, uf, bulge=0.5)
        fa = lerp(-160, 28, uf) + 26 * Wd.settle(u, P3_FLAP + 1.0, 1.0, 2.4, 4.2)
        Wd.feather(tgt, fx, fy, 2.3, fa)
    # the clam shell, just in frame above, flaps once on its pin
    g = 3.0 + 40 * _bump(u, P3_FLAP, P3_FLAP + 0.16, P3_FLAP + 0.62)
    c = Wd.clam_pa(tgt, 1004, -52, 1.75, g, t, flip=True)
    if P3_FLAP < u < P3_FLAP + 1.0:
        Wd.sound_rings(tgt, c["mouth"][0] + 20, c["mouth"][1] + 10, u - P3_FLAP, direction=150, n=3, r0=30, r1=260,
                       arc=70, strength=clamp(1.6 - 1.6 * (u - P3_FLAP)), rate=1.1, width=4.0)
    # fries at the edge of the frame, rocked by the flap
    _fry_school(tgt, [(52, 300), (96, 420), (30, 150), (120, 196), (864, 436), (930, 330)], t, kick_t=P3_FLAP + 0.15,
                amp=30, scale=0.8, seed=5, pins=True)
    Wd.river_plane(tgt, "front", t, 0.0, seed=1)


# ------------------------------------------------------------------ P4 ---
# Wide again: the shell is plainly the bigger of the two. It opens, takes the tin's air, shuts. Needle to half.
P4_TIN = (256, 368, 1.0)
P4_CLAM = (806, 142, 1.72)
P4_OPEN, P4_SHUT = 0.55, 2.72


def _quad(a, b, c, u):
    return ((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * b[0] + u * u * c[0], (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * b[1] + u * u * c[1])


def _p4(tgt, u):
    t = T_P4 + u
    Wd.river(tgt, t, seed=1)
    Wd.brick_wall(tgt, 716, 0, 320, 540, seed=2, flip=True)
    x, y, s = P4_TIN
    gape = 4.0 + 44.0 * ease(u, P4_OPEN, P4_OPEN + 0.6) * (1 - ease(u, P4_SHUT, P4_SHUT + 0.14))
    gape += 5.0 * Wd.settle(u, P4_OPEN + 0.6, 1.0, 2.2, 4.5) * (1 if u < P4_SHUT else 0)
    level = 1.0 - 0.5 * ease(u, 1.05, 2.7) + (0.05 * Wd.settle(u, P4_SHUT + 0.14, 1.0, 3.0, 4.0))
    p = Wd.tin(tgt, x, y, s, t * 1.35, mood="freak", latch=0.0, dial=clamp(level))
    if 0.9 < u:                                              # the eye goes to the needle while it falls and where it rests
        Wd.glow(tgt, p["dial"][0], p["dial"][1], r=34, strength=0.75 * ease(u, 0.9, 1.3))
    Wd.padlock(tgt, p["bow"][0] - 4, p["bow"][1] + 2, 0.72, swing=6 * Wd.settle(u, P4_SHUT + 0.14, 1.0, 2.4, 3.6))
    Wd.feather(tgt, p["port"][0] + 20 * s, p["port"][1] - 20 * s, 0.75, 28)       # still stuck to the glass
    # the string of bubbles: out of the vent on the lid, drawn across and in between the valves
    hx, hy, cs = P4_CLAM
    half_a = math.radians(44.0 / 2 + 4)
    inside = (hx - 150 * cs * math.cos(half_a), hy + 150 * cs * math.sin(half_a) + 6)
    door = (hx - 262 * cs * math.cos(half_a), hy + 262 * cs * math.sin(half_a) + 8)
    vent = (p["top"][0], p["top"][1] - 4)
    rs = random.Random(11)
    items = []
    n = 14
    for k in range(n):
        t0 = 1.0 + 1.1 * k / (n - 1)
        r = rs.uniform(9.0, 16.0)
        jx, jy = rs.uniform(-60, 60), rs.uniform(-30, 30)
        wob = rs.uniform(0, 6.28)
        if u < t0:
            continue
        v = ramp(u, t0, t0 + 0.62)
        if v < 1:
            q = _quad(vent, (vent[0] + 40, vent[1] - 150), door, v ** 0.9)
            q = (q[0] + 5 * math.sin(u * 9 + wob), q[1])
            al = min(1.0, v * 8)
        else:
            w_ = ease(u, t0 + 0.62, t0 + 0.95)
            q = (lerp(door[0], inside[0] + jx, w_), lerp(door[1], inside[1] + jy, w_) + 2 * math.sin(u * 7 + wob))
            al = 1.0
        items.append((q[0], q[1], r, al))
    if items:
        Wd._comp(tgt, _bubble_layer(items), (0, 0))        # behind the shell: the valves close over them
    Wd.clam_pa(tgt, hx, hy, cs, gape, t, flip=True)
    _fry_school(tgt, [(470, 452), (520, 430), (586, 462), (640, 440), (64, 250), (130, 222), (250, 216), (330, 236), (40, 470)], t,
                kick_t=P4_SHUT + 0.12, amp=30, scale=0.42, seed=9)
    if P4_SHUT + 0.1 < u < P4_SHUT + 0.75:                   # the clap of the shell shutting
        Wd.sound_rings(tgt, hx - 262 * cs, hy + 16, u - P4_SHUT - 0.1, direction=180, n=2, r0=30, r1=170, arc=80,
                       strength=clamp(1.5 - 2.2 * (u - P4_SHUT - 0.1)), rate=1.3, width=3.5)
    Wd.river_plane(tgt, "front", t, 0.0, seed=1)


# ---------------------------------------------------------------- draw ---
SWING = 0.5        # a new scene is a card swinging in (or the paper swinging away) about a corner brad


def _as_card(fn, u):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    fn(img, u)
    return img


def draw(t, ink):
    t = max(0.0, min(float(t), SECONDS - 1e-6))
    if t < T_P2:
        _table_scene(ink, t)
    elif t < T_P3:
        u = t - T_P2
        _p2(ink, u)
        if u < 0.75:                                        # the paper swings away on its corner brad
            Wd.swing_card(ink, _table_done(), (26, 26), angle=-104 * ease(u, 0.0, 0.75) ** 1.3)
    elif t < T_P4:
        u = t - T_P3
        if u < SWING:
            _p2(ink, T_P3 - T_P2)
            Wd.swing_card(ink, _as_card(_p3, u), (26, 26), angle=-96 * (1 - ease(u, 0.0, SWING)))
        else:
            _p3(ink, u)
    else:
        u = t - T_P4
        if u < SWING:
            _p3(ink, T_P4 - T_P3)
            Wd.swing_card(ink, _as_card(_p4, u), (26, 26), angle=-96 * (1 - ease(u, 0.0, SWING)))
        else:
            _p4(ink, u)
    Wd.badge(ink)


# ---------------------------------------------------------------- test ---
if __name__ == "__main__":
    from kit import Film

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/c10_scene_pilot")
    out.mkdir(parents=True, exist_ok=True)
    times = [float(a) for a in sys.argv[2:] if not a.startswith("--")] or [0.5, 1.4, 2.5, 4.0, 5.3, 6.6, 7.5, 7.85, 8.3, 9.4, 9.72, 10.6,
                                                 11.7, 12.3, 12.6, 13.2, 14.2, 14.75, 15.4, 16.1, 16.9, 17.2, 17.9]
    captions = "--captions" in sys.argv
    film = Film("c10_scene_pilot", SECONDS)

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
