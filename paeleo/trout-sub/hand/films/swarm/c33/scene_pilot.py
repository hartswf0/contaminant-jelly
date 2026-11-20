"""c33 · scene_pilot · the pilot's page (board part 1, 0.0 to 20.0 s of the film).

P0-P3  0.0 ..  8.0  the child's drawing is made in pencil on the table: nine bars, the fish cut by a bar, the cracks
P4     8.0 .. 11.5  "A ship that sunk."                        the tin lies canted in the silt; the fish circles it once
P5    11.5 .. 15.0  "Look in the window, trying to get out."   Turkey's black shape in the round window shoves three times
P6    15.0 .. 20.0  "He could be freaking out, trying to get out, losing air, breathing heavy."
                                                               from his seat: fog, crack bubbles, the gauge 8 to 5

Every piece comes from world.py (nothing is foraged here). The porthole's rule (shadow theatre): outside the glass
is black card on teal light; figures move only on their pins; planes only slide; each change of scene is the
velvet iris. The three pilot lines are not endings, so they carry no die face.

Exposes SECONDS, CAPTIONS (times from this module's start) and draw(t, ink).
Test:  python3 films/swarm/c33/scene_pilot.py [out_dir] [--captions] [t ...]   writes stills and a contact sheet.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world as Wd  # noqa: E402  (puts films/ on sys.path itself)

from kit import W, H, clamp, ease, lerp, lerp2, ramp  # noqa: E402

SECONDS = 20.0
T_P4, T_P5, T_P6 = 8.0, 11.5, 15.0
CAPTIONS = [
    (8.0, 11.5, "A ship that sunk."),
    (11.5, 15.0, "Look in the window, trying to get out."),
    (15.0, 20.0, "He could be freaking out, trying to get out, losing air, breathing heavy."),
]

PC, PR = Wd.PORT_C, Wd.PORT_R


def _iris_f(t, mid, half=0.2):
    """One iris move: closes over `half` seconds up to `mid` (swap the scene there), opens over the next `half`."""
    return ease(t, mid - half, mid) if t < mid else 1 - ease(t, mid, mid + half)


# ------------------------------------------------------------ P0 to P3: table ---
PENCIL_OFF = (1016, 690)                 # where the pencil waits and goes back to: off the lower right corner
T_RING = (7.62, 8.0)                     # the brass ring is slid over the finished page
T_SWAP = 8.2                             # the iris is shut: pencil bars become card bars
T_PUSH = (8.45, 9.25)                    # the ring passes us and the planes slide: the wreck comes into view


@lru_cache(maxsize=1)
def _ring_spr():
    return Wd.brass_ring(PR, Wd.RING_OUT, 6, 10, 3)


def _page(ink, t):
    Wd.table(ink)
    Wd.sheet_ring(ink)
    tip, down = Wd.pilot_page(ink, t)
    return tip, down


def _pencil(ink, t, tip, down):
    if t < 1.2:                                              # P0: comes in from the lower right, touches down
        p = lerp2(PENCIL_OFF, tip, ease(t, 0.15, 1.05))
        Wd.pencil(ink, p, lift=1 - ease(t, 1.0, 1.2))
    elif t < 7.62:
        Wd.pencil(ink, tip, lift=0 if down else 1)
    elif t < 8.05:                                           # lifts and leaves the frame
        p = lerp2(tip, PENCIL_OFF, ease(t, 7.62, 8.0))
        Wd.pencil(ink, p, lift=1)


def _ring_on_page(ink, t):
    f = ease(t, *T_RING)
    if f <= 0:
        return
    cy = lerp(-290, PC[1], f) - 5 * math.sin(math.pi * clamp((t - T_RING[1] + 0.12) / 0.12)) * (1 if t < T_RING[1] else 0)
    Wd.put(ink, _ring_spr(), PC[0], cy, shadow=0.7 * f, shadow_off=(9, 13), shadow_blur=9)


@lru_cache(maxsize=1)
def _table_overlay():
    """The table, the sheet and the brass ring lying on it, with the glass cut out: laid over the black world."""
    o = Wd.Ink(0.0, 0, (W, H))
    Wd.table(o)
    Wd.sheet_ring(o)
    Wd.put(o, _ring_spr(), PC[0], PC[1], shadow=0.7, shadow_off=(9, 13), shadow_blur=9)
    im = o.img.convert("RGBA")
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).ellipse([PC[0] - PR + 1, PC[1] - PR + 1, PC[0] + PR - 1, PC[1] + PR - 1], fill=0)
    im.putalpha(hole)
    return im


def _overlay(ink, s):
    """Lay the table-with-a-hole, scaled by s about the middle of the glass (the ring slides past the camera)."""
    ov = _table_overlay()
    if s > 1.001:
        k = 1.0 / s
        ov = ov.transform((W, H), Image.AFFINE, (k, 0, PC[0] * (1 - k), 0, k, PC[1] * (1 - k)), Image.BILINEAR)
    ink.paste(ov, (0, 0))
    r = PR * s                                               # the glass's own edge: a shadow just inside the ring
    if r < 700:
        for q in range(5):
            ink.d.ellipse([PC[0] - r + q, PC[1] - r + q, PC[0] + r - q, PC[1] + r - q], outline=(4, 20, 24, 110 - 20 * q), width=2)


# ----------------------------------------------------- P4: "A ship that sunk." ---
PAN = 300.0                              # how far the planes slide as we go through the glass
BARS_C = (PC[0] + PAN, PC[1])            # where the grating stands in the wide shot
TIN_C, TIN_S = (322, 350), 0.86
HOME = Wd.ring_xy(*Wd.PILOT_PLACES["fish"], BARS_C, PR)      # the fish where the pilot drew it, behind bar 5
FISH_L = Wd.STAGE["fish_len"]
T_LOOP = (8.5, 11.45)

# the one unhurried loop round the wreck (wide-shot coordinates): out over the top of the hull, down behind its
# tail, along behind it (unseen), up past the nose and on behind the bars
_WAY = [HOME, (HOME[0] - 110, 248), (580, 200), (440, 168), (310, 162), (215, 190), (176, 255), (205, 330),
        (310, 372), (430, 380), (535, 350), (615, 312), (715, 292), (HOME[0] + 30, 284), (HOME[0] + 110, 280)]
_HIDE = 7                                # way point where the fish is behind the hull: it turns round there, unseen


@lru_cache(maxsize=1)
def _fish_path():
    pts = Wd.catmull(_WAY, 14)
    acc, out = 0.0, [(0.0, pts[0])]
    for a, b in zip(pts, pts[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        out.append((acc, b))
    # arc length at which it turns (nearest path point to the hidden way point)
    turn = min(out, key=lambda e: math.hypot(e[1][0] - _WAY[_HIDE][0], e[1][1] - _WAY[_HIDE][1]))[0]
    return out, acc, turn


def _on_path(s):
    out, tot, _ = _fish_path()
    s = clamp(s, 0, tot - 0.01)
    lo, hi = 0, len(out) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if out[m][0] <= s:
            lo = m
        else:
            hi = m
    (s0, p0), (s1, p1) = out[lo], out[hi]
    return lerp2(p0, p1, (s - s0) / max(1e-6, s1 - s0))


@lru_cache(maxsize=1)
def _fish_base():
    """Which way the uncanted sprite's nose points (screen vector), measured from the cut shape itself."""
    import numpy as np
    spr = Wd.shadow_fish_sprite(FISH_L, 0, 0, 0, None, True)
    a = np.asarray(spr.getchannel("A"), np.float32)
    ys, xs = np.nonzero(a > 60)
    cx, cy = xs.mean(), ys.mean()
    cov = np.cov(np.vstack([xs - cx, ys - cy]))
    w, v = np.linalg.eigh(cov)
    ax = v[:, int(np.argmax(w))]
    if ax[0] > 0:                        # the sprite faces left
        ax = -ax
    return float(ax[0]), float(ax[1])


def _fish_pose(t):
    """(x, y, angle, flip) of the fish at time t in wide-shot coordinates."""
    out, tot, turn = _fish_path()
    f = ramp(t, *T_LOOP)
    f = f * f * (3 - 2 * f) * 0.35 + f * 0.65                # a soft start and stop, steady between
    # the stretch behind the hull is not seen, so it is given less of the clock and the seen passes more
    h0, h1 = turn - 70, turn + 250
    seen = tot - (h1 - h0) * 0.5
    s = f * seen
    if s > h0:
        s = h0 + (s - h0) * 2 if s < h0 + (h1 - h0) * 0.5 else s + (h1 - h0) * 0.5
    x, y = _on_path(s)
    ax, ay = _on_path(s - 16)
    bx, by = _on_path(s + 16)
    hx, hy = bx - ax, by - ay
    if math.hypot(hx, hy) < 1e-3:
        hx, hy = -1.0, 0.0
    flip = s > turn
    b0 = _fish_base()
    base = (-b0[0], b0[1]) if flip else b0
    ang = math.degrees(math.atan2(-hy, hx) - math.atan2(-base[1], base[0]))
    ang = (ang + 180) % 360 - 180
    if s < 1.0:
        ang = Wd.STAGE["fish_angle"]
    return x, y, ang, flip, s / tot


def _black_world(ink, t, dx):
    """The far side of the glass: teal ruled light, the fish, the nine card bars, and the wreck lying before them.
    dx slides every plane together (0 = the wide shot; -PAN = the bars sit in the glass as on the page)."""
    k = ease(t, *T_PUSH)
    Wd.glow_ground(ink, (int(lerp(PC[0], 430, k)), int(lerp(PC[1], 236, k))), int(lerp(PR, 370, k)), 0)
    x, y, ang, flip, f = _fish_pose(t)
    if f <= 0:
        ang = lerp(Wd.STAGE["fish_angle"], ang, 0)
    Wd.shadow_fish(ink, x + dx, y, FISH_L, angle=ang, flip=flip,
                   tail=18 * math.sin(t * 7.0), fins=14 * math.sin(t * 7.0 - 1.0))
    Wd.bars(ink, None, (BARS_C[0] + dx, BARS_C[1]), PR, v0=-1.42, v1=1.42)
    sink = 16 * ease(t, 9.95, 10.5)
    tp = Wd.wreck(ink, t, (TIN_C[0] + dx, TIN_C[1]), TIN_S, mood=None, sink=sink, puff=ramp(t, 10.05, 11.4) if t > 10.05 else 0,
                  outline=1.0, glow=0.22)
    return tp


def _p4(ink, t):
    k = ease(t, *T_PUSH)
    dx = -PAN * (1 - k)
    tp = _black_world(ink, t, dx)
    if t < T_PUSH[1] + 0.02:
        Wd.iris(ink, _iris_f(t, T_SWAP))
        _overlay(ink, 1 + 3.2 * k * k)
    if t > T_P5 - 0.22:                                      # the iris closes on the wreck's round window
        Wd.iris(ink, ease(t, T_P5 - 0.2, T_P5), tp["port"], 600)


# -------------------------------- P5: "Look in the window, trying to get out." ---
def _shove_clock(t):
    """World time handed to the 'shove' pose so the three shoves land at 12.55, 13.35 and 14.15."""
    return (t - 12.55) / 0.8


def _p5(ink, t):
    tt = _shove_clock(t)
    p = Wd.shove(tt) if 0 <= tt < 3 else 0.0
    r = int(round(lerp(184, 208, ease(t, T_P5, 12.5)) / 2)) * 2
    Wd.river_backdrop(ink, t, shift=2.5 * p, wall=False)                 # far plane slides least
    c = (PC[0] - 9 * p, PC[1] - 3 * p)                                   # the tin rocks on the bed, nearest most
    cx, cy = Wd.tin_porthole(ink, c, r, mood=None, t=t, angle=1.4 * p)
    # Turkey's black shape comes up into the round window (slid up on his own plane, clipped by the glass)
    rise = 1.7 * r * (1 - ease(t, 11.7, 12.4))
    b = Wd.breath(t)
    lay = ink.layer()                                                    # pins only: neck, beak, wings, wattle
    Wd.turkey_shadow(lay, cx - 12 * p, cy + rise - 7 * p, height=2 * r, mood="shove", t=0.6,
                     neck=-3 - 13 * p + 2 * b, wing=70 + 24 * p - 5 * b, beak=6 + 20 * b + 8 * p, ruff=0.6 + 0.4 * max(b, p),
                     wattle=16 * math.sin(9 * t) * (0.4 + p), shake=0.6 + 2.2 * p)
    m = Image.new("L", (W, H), 0)
    rr = r - 3
    ImageDraw.Draw(m).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
    al = lay.img.getchannel("A")
    lay.img.putalpha(Image.composite(al, Image.new("L", (W, H), 0), m))
    ink.paste(lay.img, (0, 0))
    Wd.cracks(ink, (cx, cy), r, mirror=True)
    ink.d.arc([cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9], 200, 250, fill=(240, 252, 244, 110), width=max(2, int(r * 0.045)))
    if p > 0.05:                                                         # the glass does not move: only silt lifts
        Wd.bubbles(ink, (cx - r * 0.2, cy + r * 1.28), t, t0=12.55 + 0.8 * math.floor(tt), n=5, rise=70, spread=60, size=4)
    if t < T_P5 + 0.22:
        Wd.iris(ink, 1 - ease(t, T_P5, T_P5 + 0.2), PC, 600)
    if t > T_P6 - 0.22:
        Wd.iris(ink, ease(t, T_P6 - 0.2, T_P6), PC, 600)


# ------------ P6: "He could be freaking out, trying to get out, losing air, breathing heavy." ---
GAUGE = (868, 392)                       # lifted clear of the long caption's band
TICKS = (16.0, 17.0, 18.0)               # the three gasps at which the needle drops: 8 -> 5


def _p6(ink, t):
    n = 8.0 - sum(ease(t, tk + 0.05, tk + 0.3) for tk in TICKS)
    fog = 0.16 + 0.012 * ramp(t, T_P6, SECONDS) * 10 + sum(0.1 * ease(t, tk, tk + 0.2) for tk in TICKS)
    Wd.seat_scene(ink, t, ring=0.0, tunnel_on=False, cross=False,
                  turkey_kw=dict(mood="shove", t=t, ruff=1.0, height=300, cy=Wd.STAGE["reflection"][1] + 14),
                  fog_level=fog, notches=n, leak_since=T_P6, shift=(3 * Wd.shove(t), 0), frame=False)
    Wd.seat_frame(ink)
    Wd.gauge(ink, n, GAUGE[0], GAUGE[1], r=54, t=t, tremble=0.5 * Wd.breath(t))
    if t < T_P6 + 0.22:
        Wd.iris(ink, 1 - ease(t, T_P6, T_P6 + 0.2), PC, 600)


# ------------------------------------------------------------------- draw ---
def draw(t, ink):
    t = clamp(t, 0.0, SECONDS - 1e-6)
    if t < T_SWAP:
        tip, down = _page(ink, t)
        if t >= T_RING[0]:
            Wd.iris(ink, _iris_f(t, T_SWAP))
            _ring_on_page(ink, t)
        _pencil(ink, t, tip, down)
    elif t < T_P5:
        _p4(ink, t)
    elif t < T_P6:
        _p5(ink, t)
    else:
        _p6(ink, t)
    Wd.badge(ink)


# ------------------------------------------------------------------- test ---
if __name__ == "__main__":
    from kit import Film

    args = sys.argv[1:]
    captions = "--captions" in args
    args = [a for a in args if not a.startswith("--")]
    out = Path(args[0]) if args and not args[0].replace(".", "").isdigit() else Path("/tmp/c33_scene_pilot")
    times = [float(a) for a in args if a.replace(".", "").isdigit()] or [
        0.6, 1.5, 3.0, 4.5, 5.6, 6.3, 7.5, 7.85, 8.1, 8.35, 8.7, 9.0, 9.4, 9.9, 10.4, 11.0, 11.4,
        11.6, 12.0, 12.4, 12.7, 13.5, 14.3, 14.9, 15.1, 15.6, 16.2, 17.2, 18.2, 19.9]
    out.mkdir(parents=True, exist_ok=True)
    film = Film("c33_scene_pilot", SECONDS)

    def frame(t, ink):
        draw(t, ink)
        if captions:
            for a, b, s in CAPTIONS:
                if a <= t < b:
                    ink.caption(s)

    film.picture(frame)
    import time
    t0 = time.time()
    ims = []
    for t in times:
        im = film.frame(int(round(t * film.fps)))
        im.save(out / f"{t:06.2f}.png")
        ims.append((t, im.resize((480, 270), Image.LANCZOS)))
    cols = 4
    for page in range(0, len(ims), 12):
        chunk = ims[page:page + 12]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 480, rows * 270), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for k, (t, im) in enumerate(chunk):
            x, y = (k % cols) * 480, (k // cols) * 270
            sheet.paste(im, (x, y))
            d.rectangle([x, y, x + 62, y + 18], fill=(0, 0, 0))
            d.text((x + 4, y + 3), f"{t:.2f}", fill=(255, 255, 0))
        sheet.save(out / f"sheet{page // 12}.jpg", quality=86)
    print("stills ->", out, "%.1fs for %d frames" % (time.time() - t0, len(times)))
