"""cam.py: the camera rig for the making films.

The making films are about leaving your own seat, so the camera has to travel:
over a shoulder, down into the page, round inside the tin, out through the
glass, back up to the desk. Every function here takes finished pictures (PIL
RGB or RGBA, normally 960x540) and returns ONE 960x540 RGB frame. Nothing is
random and nothing is cached between calls: the same inputs give the same
frame, so a film can be rendered in any order.

    import cam
    frame = cam.dive(desk, thought, 300, 260, u)      # into the drawn ring
    ink.img.paste(frame); ink.d = ImageDraw.Draw(ink.img, "RGBA")

The moves (u always runs 0 -> 1 and should be fed LINEAR time; each move does
its own easing, and returns exactly `a` at u<=0 and exactly `b` at u>=1):

    shoot(layers, x, y, zoom, rot, focus, shake, t)   multiplane: pan, zoom, roll, parallax, rack focus, handheld
    tilt(img, deg, horizon)                           lay a sheet back on the desk in true perspective
    tilt_point(px, py, deg, horizon)                  where a point of that sheet lands on screen (for the pencil tip)
    dive(a, b, cx, cy, u, spin)                       fly into a point of a, arrive in b
    turn(a, b, u, axis)                               the camera turns round 180 degrees inside a room
    whip(a, b, u, direction)                          whip pan
    rise(a, b, u, box)                                crane up and away until a is a small sheet inside b
    through_glass(inside, outside, cx, cy, r, u)      push through a round window
    blink(img, u)                                     an eyelid shuts and opens
    thought(desk, inner, cx, cy, r, u, wobble)        a pencil-ringed opening over the desk
    key(t, [(time, value), ...], ease)                keyframes for any number or tuple

Small helpers: fit(img), smooth(x), shoot_point(...).  See CAM.md for an
example of each. Needs numpy, PIL and cv2 (all present here).
"""

from __future__ import annotations

import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

W, H = 960, 540
CX, CY = W / 2.0, H / 2.0
PAPER = (243, 239, 228)
DESK = (181, 150, 112)
GRAPHITE = (72, 68, 66)
LID = (22, 15, 14)

# constant pixel grids (never change, so the functions stay pure)
_XS = np.arange(W, dtype=np.float32)[None, :]
_YS = np.arange(H, dtype=np.float32)[:, None]

__all__ = ["shoot", "shoot_point", "tilt", "tilt_point", "dive", "turn", "whip", "rise",
           "through_glass", "blink", "thought", "key", "fit", "smooth", "W", "H"]


# ------------------------------------------------------------- small things ---

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def smooth(x):
    """Smoothstep on 0..1 (clamped)."""
    x = clamp(x)
    return x * x * (3 - 2 * x)


def _smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def fit(img, bg=PAPER):
    """Any PIL image -> a 960x540 RGB PIL image (RGBA is laid on `bg`, other sizes are scaled to cover)."""
    return Image.fromarray(_rgb(img, bg))


def _rgb(img, bg=PAPER):
    """PIL (or array) -> uint8 HxWx3 at 960x540."""
    if isinstance(img, np.ndarray):
        a = img
    else:
        if img.mode == "RGBA":
            base = Image.new("RGB", img.size, tuple(bg[:3]))
            base.paste(img, (0, 0), img)
            img = base
        elif img.mode != "RGB":
            img = img.convert("RGB")
        a = np.asarray(img)
    if a.shape[1] != W or a.shape[0] != H:
        s = max(W / a.shape[1], H / a.shape[0])
        nw, nh = max(W, int(round(a.shape[1] * s))), max(H, int(round(a.shape[0] * s)))
        a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        x0, y0 = (nw - W) // 2, (nh - H) // 2
        a = a[y0:y0 + H, x0:x0 + W]
    return np.ascontiguousarray(a[:, :, :3])


def _out(a):
    if a.dtype != np.uint8:
        a = np.clip(a + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.ascontiguousarray(a))


def _sim(scale, rot, src, dst):
    """2x3 matrix: scale and rotate (degrees, clockwise on screen) so that point src lands on dst."""
    r = math.radians(rot)
    c, s = math.cos(r) * scale, math.sin(r) * scale
    return np.array([[c, -s, dst[0] - (c * src[0] - s * src[1])],
                     [s, c, dst[1] - (s * src[0] + c * src[1])]], np.float64)


def _cover(px, py, r):
    """Smallest scale at which a frame-sized picture centred on (px, py) still covers every part of
    the disc of radius r round (px, py) that is inside the frame (so no edge of it ever shows)."""
    return max(min(r, max(py, H - py)) / CY, min(r, max(px, W - px)) / CX)


def _streak(arr, scale, rot, src, dst, amount=0.0, twist=0.0, border=cv2.BORDER_REFLECT):
    """Warp arr by a similarity (src lands on dst). With `amount` (relative scale) or `twist` (degrees)
    the shutter is open while the lens moves: many copies spread over that range are averaged, as many
    as it takes for the streaks to run together, at half size when the smear is long."""
    far = max(math.hypot(dst[0] - x, dst[1] - y) for x in (0, W) for y in (0, H))
    disp = far * (abs(amount) + abs(math.radians(twist)))
    if disp < 1.5:
        return cv2.warpAffine(arr, _sim(scale, rot, src, dst), (W, H), flags=cv2.INTER_LINEAR,
                              borderMode=border).astype(np.float32)
    n = int(math.ceil(disp / 1.7)) + 1
    half = n > 10
    if half:
        n = int(min(56, math.ceil(disp / 4.5) + 1))
        size = (W // 2, H // 2)
        if scale < 1.2:
            arr = cv2.resize(arr, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            pre = 1.0
        else:
            pre = 0.5
    else:
        size = (W, H)
    acc = np.zeros((size[1], size[0], arr.shape[2]), np.float32)
    for i in range(n):
        f = i / (n - 1) - 0.5
        m = _sim(scale * (1 + amount * f), rot + twist * f, src, dst)
        if half:
            m = m * 0.5 if pre == 0.5 else np.hstack([m[:, :2], m[:, 2:] * 0.5])
        cv2.accumulate(cv2.warpAffine(arr, m, size, flags=cv2.INTER_LINEAR, borderMode=border), acc)
    acc /= n
    if half:
        acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    return acc


def _soften(arr, sigma):
    """Gaussian blur; big blurs are done small and scaled back up, which looks the same and is quick."""
    if sigma <= 3:
        return cv2.GaussianBlur(arr, (0, 0), sigma)
    f = int(min(8, max(2, sigma // 1.5)))
    h, w = arr.shape[:2]
    small = cv2.resize(arr, ((w + f - 1) // f, (h + f - 1) // f), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / f)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def _disc(px, py, r, soft):
    """Float mask HxW: 1 inside radius r of (px, py), falling to 0 over `soft` pixels outside it."""
    d = np.sqrt((_XS - px) ** 2 + (_YS - py) ** 2)
    m = np.clip((r + soft - d) / max(soft, 1e-3), 0, 1)
    return m * m * (3 - 2 * m)


def _edge_smear(a, b, dim=0.82):
    """A picture the size of the frame that runs from a's right edge to b's left edge: what a lens
    sees between two pictures when it is moving too fast to see anything."""
    ea = cv2.blur(a[:, -40:].mean(axis=1, keepdims=True).astype(np.float32), (1, 61))
    eb = cv2.blur(b[:, :40].mean(axis=1, keepdims=True).astype(np.float32), (1, 61))
    g = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    shade = 1 - (1 - dim) * np.sin(np.pi * g)
    return np.clip((ea * (1 - g) + eb * g) * shade, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------- key ---

_EASES = {
    "linear": lambda x: x,
    "smooth": smooth,
    "smoother": _smoother,
    "in": lambda x: x * x,
    "out": lambda x: 1 - (1 - x) * (1 - x),
    "hold": lambda x: 0.0,
    "back": lambda x: 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2,   # overshoots, then settles
}


def _mix(a, b, x):
    if isinstance(a, (tuple, list)):
        return tuple(_mix(p, q, x) for p, q in zip(a, b))
    return a + (b - a) * x


def key(t, keys, ease="smooth"):
    """Keyframes. keys = [(time, value), ...] in time order; value is a number or a (nested) tuple.

    Before the first key the first value is held, after the last the last. Between two keys the value
    is eased with `ease`: 'linear', 'smooth', 'smoother', 'in', 'out', 'hold' (stay on the earlier
    value until the next key: a stuck pencil), 'back' (overshoot and settle), or any function 0..1 ->
    0..1. A key may carry its own ease as a third item, used for the segment that ARRIVES at it:
    key(t, [(0, 0), (2, 1, 'out'), (5, 1), (5.4, 0, 'in')])."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for k0, k1 in zip(keys, keys[1:]):
        if k0[0] <= t < k1[0]:
            e = k1[2] if len(k1) > 2 else ease
            fn = e if callable(e) else _EASES[e]
            return _mix(k0[1], k1[1], fn((t - k0[0]) / (k1[0] - k0[0])))
    return keys[-1][1]


# --------------------------------------------------------------- shoot ---

def _shake(t, amount):
    """Handheld drift: a few slow sines, never a jitter. Returns (dx, dy, roll degrees)."""
    if not amount:
        return 0.0, 0.0, 0.0
    dx = math.sin(t * 2.3 + 1.1) * 0.55 + math.sin(t * 5.9 + 4.2) * 0.3 + math.sin(t * 11.3 + 0.7) * 0.15
    dy = math.sin(t * 1.9 + 2.6) * 0.55 + math.sin(t * 6.7 + 0.3) * 0.3 + math.sin(t * 12.1 + 5.1) * 0.15
    ro = math.sin(t * 1.3 + 0.4) * 0.6 + math.sin(t * 4.1 + 3.3) * 0.4
    return dx * amount, dy * amount, ro * amount * 0.06


def _layer_matrix(size, depth, off, x, y, zoom, rot, dolly):
    near = depth - dolly
    scale = zoom * depth / near
    src = (size[0] / 2.0 - off[0] + x / depth, size[1] / 2.0 - off[1] + y / depth)
    return _sim(scale, rot, src, (CX, CY)), scale


def shoot(layers, x=0, y=0, zoom=1, rot=0, focus=None, shake=0, t=0, dolly=0, aperture=7, bg=PAPER):
    """A multiplane camera. Returns one 960x540 RGB frame.

    layers: [(image, depth), ...] from the back to the front. An optional third item (ox, oy) shifts
            that layer's centre. Images may be RGB or RGBA and any size (bigger than the frame is the
            point: there is then somewhere to pan to). Each layer is drawn 1:1 with its centre on the
            frame centre when x = y = 0, zoom = 1, dolly = 0.
    depth:  1 is the plane the camera is 'on' (it moves pixel for pixel with x, y). 3 is far and moves
            a third as much; 0.5 is foreground and moves twice as much.
    x, y:   where the camera looks, in depth-1 pixels from the centre (x right, y down).
    zoom:   the lens: every layer grows alike, about the frame centre.
    rot:    roll, in degrees; the picture turns clockwise.
    dolly:  the camera body moves INTO the scene by this much depth. Near layers swell faster than far
            ones and a layer the camera has passed (depth <= dolly) is gone. dolly=0.9 with a sheet at
            depth 1 puts the lens a nose away from the paper.
    focus:  a depth to hold sharp; other layers blur by aperture * |depth - focus| pixels. None: all sharp.
    shake:  handheld, in pixels of drift at depth 1; t is the time in seconds that drives it.
    bg:     colour behind the last layer."""
    sx, sy, sr = _shake(t, shake)
    x, y, rot = x + sx, y + sy, rot + sr
    out = np.empty((H, W, 3), np.float32)
    out[:] = np.array(bg[:3], np.float32)
    for layer in layers:
        img, depth = layer[0], max(float(layer[1]), 1e-3)
        off = layer[2] if len(layer) > 2 else (0, 0)
        if depth - dolly < 0.03:
            continue
        m, scale = _layer_matrix(img.size, depth, off, x, y, zoom, rot, dolly)
        src = np.asarray(img if img.mode in ("RGB", "RGBA") else img.convert("RGBA"))
        sigma = 0.0 if focus is None else min(32.0, aperture * abs(depth - focus))
        # only the part of the layer the lens can see is worth touching
        inv = cv2.invertAffineTransform(m)
        pad = 3 * sigma + 4
        cs = np.array([[-pad, -pad, 1], [W + pad, -pad, 1], [W + pad, H + pad, 1], [-pad, H + pad, 1]]) @ inv.T
        bx0, by0 = int(max(0, math.floor(cs[:, 0].min()) - 2)), int(max(0, math.floor(cs[:, 1].min()) - 2))
        bx1, by1 = int(min(src.shape[1], math.ceil(cs[:, 0].max()) + 3)), int(min(src.shape[0], math.ceil(cs[:, 1].max()) + 3))
        if bx1 <= bx0 or by1 <= by0:
            continue
        src = src[by0:by1, bx0:bx1]
        m = m.copy()
        m[:, 2] += m[:, 0] * bx0 + m[:, 1] * by0
        if src.shape[2] == 4:
            a3 = cv2.merge([src[:, :, 3]] * 3)
            src = np.dstack([cv2.multiply(src[:, :, :3], a3, scale=1 / 255.0), src[:, :, 3]])
        else:
            src = np.dstack([src, np.full(src.shape[:2], 255, np.uint8)])
        if scale < 0.6:      # shrink first so thin pencil lines do not shimmer
            src = cv2.resize(src, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            m = np.hstack([m[:, :2] / scale, m[:, 2:]])
        wp = cv2.warpAffine(src, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if sigma > 0.4:
            wp = _soften(wp, sigma)
        al = wp[:, :, 3]
        if al.min() == 255:
            out = wp[:, :, :3].astype(np.float32)
        elif al.max() > 0:
            ys, xs = np.nonzero(al.max(axis=1))[0], np.nonzero(al.max(axis=0))[0]
            sl = (slice(ys[0], ys[-1] + 1), slice(xs[0], xs[-1] + 1))
            reg = out[sl]
            w4 = wp[sl].astype(np.float32)
            reg *= 1 - w4[:, :, 3:4] / 255.0
            reg += w4[:, :, :3]
    return _out(out)


def shoot_point(px, py, size, depth, x=0, y=0, zoom=1, rot=0, dolly=0, off=(0, 0)):
    """Where pixel (px, py) of a layer image of `size` at `depth` lands on screen for the same camera
    numbers given to shoot() (shake not included). Use it to put a pencil tip on a line."""
    m, _ = _layer_matrix(size, max(float(depth), 1e-3), off, x, y, zoom, rot, dolly)
    return (float(m[0, 0] * px + m[0, 1] * py + m[0, 2]), float(m[1, 0] * px + m[1, 1] * py + m[1, 2]))


# ---------------------------------------------------------------- tilt ---

def _tilt_matrix(size, deg, horizon=0.5, zoom=1.0, f=900.0, shift=(0, 0)):
    """3x3 homography: picture pixels -> screen, for a picture hinged about its own centre line and
    laid back by `deg`, seen by a lens of focal length f whose eye line is at horizon * H."""
    th = math.radians(clamp(deg, 0, 89))
    s, c = math.sin(th), math.cos(th)
    cx, cy = size[0] / 2.0, size[1] / 2.0
    hx, hy = CX + shift[0], H * horizon + shift[1]
    r3 = np.array([0.0, -s * zoom, f + s * zoom * cy])
    r1 = f * zoom * np.array([1.0, 0.0, -cx]) + hx * r3
    r2 = f * c * zoom * np.array([0.0, 1.0, -cy]) + hy * r3
    return np.array([r1, r2, r3]) / f


def tilt(img, deg, horizon=0.5, zoom=1.0, f=900.0, shift=(0, 0), bg=DESK, shadow=0.35):
    """Lay a flat picture back in perspective: a sheet on a desk seen from a seat.

    This is a real perspective projection (a plane turned about a horizontal hinge through the
    picture's centre, seen by a lens of focal length f pixels), not a squash.
    deg:     0 is flat-on (a 960x540 picture comes back unchanged), 45 is a child leaning over the
             desk, 60 to 65 is sitting back, 70 is nearly edge-on. The far edge shrinks and climbs
             towards the vanishing line; the near edge swells towards the lens.
    horizon: the eye line, as a fraction of the frame height. The picture's centre sits on it and the
             sheet flattens towards it as deg goes to 90. 0.5 keeps the sheet centred; 0.35 puts it up
             the frame with room for a hand and sleeve below.
    zoom:    size of the sheet (1 = one picture pixel is one screen pixel at deg 0).
    f:       focal length in pixels. Shorter (500) is a wide lens right over the page, with steep
             convergence; longer (1600) is flatter.
    shift:   (dx, dy) screen offset.
    bg:      what the sheet lies on: a colour, a 960x540 picture, or None to get the sheet alone as
             a 960x540 RGBA image.
    shadow:  strength of the soft contact shadow the sheet casts on bg (0 for none).
    The picture may be RGBA and any size; a big one is not scaled down, it just covers more desk."""
    src = np.asarray(img if img.mode == "RGBA" else img.convert("RGBA"))
    m = _tilt_matrix(img.size, deg, horizon, zoom, f, shift)
    a3 = cv2.merge([src[:, :, 3]] * 3)
    pm = np.dstack([cv2.multiply(src[:, :, :3], a3, scale=1 / 255.0), src[:, :, 3]])
    if deg > 20 or zoom < 0.8:      # supersample: the far edge is strongly minified
        m2 = np.diag([2.0, 2.0, 1.0]) @ m
        wp = cv2.warpPerspective(pm, m2, (W * 2, H * 2), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        wp = cv2.resize(wp, (W, H), interpolation=cv2.INTER_AREA)
    else:
        wp = cv2.warpPerspective(pm, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    th = math.radians(clamp(deg, 0, 89))
    if th > 1e-3:       # nothing of the plane can be seen above its vanishing line
        vline = int(math.ceil(H * horizon + shift[1] - f / math.tan(th)))
        if vline > 0:
            wp[:min(vline, H)] = 0
    if bg is None:
        al = wp[:, :, 3:4].astype(np.float32)
        rgb = np.where(al > 0, wp[:, :, :3].astype(np.float32) * 255.0 / np.maximum(al, 1), 0)
        return Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), wp[:, :, 3]]), "RGBA")
    if isinstance(bg, Image.Image):
        out = _rgb(bg).astype(np.float32)
    else:
        out = np.empty((H, W, 3), np.float32)
        out[:] = np.array(bg[:3], np.float32)
    al = wp[:, :, 3]
    if shadow:
        sh = cv2.warpAffine(al, np.array([[1, 0, 5.0], [0, 1, 9.0]]), (W, H))
        sh = cv2.GaussianBlur(sh, (0, 0), 9).astype(np.float32) / 255.0
        out *= 1 - shadow * sh[:, :, None]
    out *= 1 - al.astype(np.float32)[:, :, None] / 255.0
    out += wp[:, :, :3]
    return _out(out)


def tilt_point(px, py, deg, horizon=0.5, zoom=1.0, f=900.0, shift=(0, 0), size=(W, H)):
    """Where pixel (px, py) of a picture of `size` lands on screen after tilt() with the same numbers.
    This is how a hand finds the word it is writing on the laid-back sheet."""
    m = _tilt_matrix(size, deg, horizon, zoom, f, shift)
    w = m[2, 0] * px + m[2, 1] * py + m[2, 2]
    return (float((m[0, 0] * px + m[0, 1] * py + m[0, 2]) / w), float((m[1, 0] * px + m[1, 1] * py + m[1, 2]) / w))


# ---------------------------------------------------------------- dive ---

def dive(a, b, cx, cy, u, spin=0, power=16.0):
    """Fly from picture a into the point (cx, cy) and arrive in picture b.

    The lens accelerates towards the point (a grows by `power` times, streaking outwards from it) and
    the point itself drifts to the middle of the frame, as it does when you lean in. b is already
    there, tiny, inside the point: it opens out of it and is the whole frame at u = 1.
    spin: degrees the camera rolls on the way in (b arrives upright). 0 is a straight push; 90 to 180
          is falling into the page.
    To come BACK UP to the desk, run the same call with 1 - u: dive(desk, thought, cx, cy, 1 - u)."""
    if u <= 0:
        return fit(a)
    if u >= 1:
        return fit(b)
    A, B = _rgb(a), _rgb(b)
    e = smooth(u)
    px, py = cx + (CX - cx) * e, cy + (CY - cy) * e
    sa = power ** u
    # the opening: a soft disc that is wider than the frame by the end
    rr = 700.0 * u ** 2.4
    sb = max(power ** (u - 1), _cover(px, py, rr * 1.02))
    fa = _streak(A, sa, spin * u, (cx, cy), (px, py), amount=0.02 + 0.5 * u ** 1.4, twist=spin * 0.08)
    fb = _streak(B, sb, spin * (u - 1), (CX, CY), (px, py), amount=0.30 * (1 - u) ** 1.5,
                 twist=spin * 0.08 * (1 - u))
    m = _disc(px, py, rr * 0.55, rr * 0.45 + 2)
    # the far end of the tunnel is dimmer than where we are
    fa *= 1 - 0.30 * math.sin(math.pi * u)
    out = fa + (fb - fa) * m[:, :, None]
    return _out(out)


# ---------------------------------------------------------------- turn ---

def turn(a, b, u, axis="y", direction=1, side=None, blur=1.0):
    """The camera turns round 180 degrees: a swings away, b swings in from behind us.

    The camera stands in the middle of a square room. a is the wall in front, b the wall behind, and
    the lens (90 degrees wide) pans across the wall between them, so a is foreshortened as it leaves
    (its far edge shrinks, the room's corner crosses the frame) and b is foreshortened as it arrives.
    The pan eases in and out and smears along its own direction at the middle, where it is fastest.
    axis:      'y' turns about the vertical (look round to the right); 'x' about the horizontal
               (tip forward and over: looking down at the page, then up and out).
    direction: 1 turns right (or down for axis 'x'); -1 turns the other way.
    side:      a 960x540 picture for the wall passed on the way (the inside of the tin, a row of
               desks). By default it is a dim smear from a's edge colours to b's.
    blur:      strength of the motion smear (0 for none).
    This is the move into another seat: turn(page_from_above, view_out_of_the_porthole, u)."""
    if u <= 0:
        return fit(a)
    if u >= 1:
        return fit(b)
    A, B = _rgb(a), _rgb(b)
    S = None if side is None else _rgb(side)
    if axis == "x":      # work on the transposed pictures, turn back at the end
        A, B = _to_x(A), _to_x(B)
        S = None if S is None else _to_x(S)
    if direction < 0:
        A, B = A[:, ::-1], B[:, ::-1]
        S = None if S is None else S[:, ::-1]
    A, B = np.ascontiguousarray(A), np.ascontiguousarray(B)
    if S is None:
        S = _edge_smear(A, B)
        S2 = S[:, ::-1]
    else:
        S2 = S
    pad = 124
    atlas = np.concatenate([A, S, B, S2], axis=1)
    atlas = cv2.copyMakeBorder(atlas, pad, pad, 0, 0, cv2.BORDER_REFLECT)
    f = W / 2.0
    theta = math.pi * smooth(u)
    spread = blur * 0.20 * math.sin(math.pi * u) ** 1.2
    px_smear = spread * f * 1.6           # the smear is longest at the frame edges
    n = int(math.ceil(px_smear / 1.7)) + 1 if px_smear > 1.5 else 1
    q = 1
    if n > 10:                             # long smear: sample at half size, more often
        q = 2
        n = int(min(48, math.ceil(px_smear / 4.5) + 1))
    w, h = W // q, H // q
    xs = (np.arange(w, dtype=np.float64) + 0.5) * q - CX
    ys = (np.arange(h, dtype=np.float64) + 0.5) * q - CY
    phi0 = np.arctan(xs / f)
    rho = np.hypot(xs, f)
    acc = np.zeros((h, w, 3), np.float32)
    for i in range(n):
        th = theta + (spread * (i / (n - 1) - 0.5) if n > 1 else 0.0)
        phi = phi0 + th
        k = np.floor((phi + math.pi / 4) / (math.pi / 2))
        psi = phi - k * (math.pi / 2)
        ax = (np.mod(k, 4) * W + CX + f * np.tan(psi) - 0.5).astype(np.float32)
        g = f / (rho * np.cos(psi))
        mx = np.repeat(ax[None, :], h, axis=0)
        my = (np.outer(ys, g) + (H + 2 * pad) / 2.0 - 0.5).astype(np.float32)
        cv2.accumulate(cv2.remap(atlas, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT), acc)
    acc /= n
    if q > 1:
        acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    out = np.clip(acc + 0.5, 0, 255).astype(np.uint8)
    if direction < 0:
        out = out[:, ::-1]
    if axis == "x":
        out = _from_x(out)
    return _out(out)


def _to_x(a):
    """Turn a 960x540 picture on its side and stretch it to 960x540 so the y-axis rig can pan it."""
    return cv2.resize(np.ascontiguousarray(a.transpose(1, 0, 2)), (W, H), interpolation=cv2.INTER_LINEAR)


def _from_x(a):
    return np.ascontiguousarray(cv2.resize(a, (H, W), interpolation=cv2.INTER_LINEAR).transpose(1, 0, 2))


# ---------------------------------------------------------------- whip ---

def whip(a, b, u, direction=1, axis="x", blur=1.0, gap=0.6):
    """Whip pan from a to b. The lens leaves a slowly, tears across, and settles on b.

    a and b stand side by side with a stretch of nothing between them (gap, in frame widths: the
    smeared colours of their facing edges). The frame travels across that strip; every frame is
    smeared along the travel by as much as the lens moved, so the middle of the move is pure streak.
    direction: 1 pans right (or down), so the pictures fly left (or up); -1 the other way.
    axis:      'x' sideways (the sheet handed along the row), 'y' vertical (eyes up from the desk to
               the board, or down again).
    blur:      smear strength (1 is a real whip; 0.4 is only a quick pan)."""
    if u <= 0:
        return fit(a)
    if u >= 1:
        return fit(b)
    A, B = _rgb(a), _rgb(b)
    if axis == "y":
        A, B = A.transpose(1, 0, 2), B.transpose(1, 0, 2)
    if direction < 0:
        A, B = A[:, ::-1], B[:, ::-1]
    A, B = np.ascontiguousarray(A), np.ascontiguousarray(B)
    fw, fh = A.shape[1], A.shape[0]
    gw = max(8, int(fw * gap))
    ea = cv2.blur(A[:, -40:].mean(axis=1, keepdims=True).astype(np.float32), (1, 41))
    eb = cv2.blur(B[:, :40].mean(axis=1, keepdims=True).astype(np.float32), (1, 41))
    g = np.linspace(0, 1, gw, dtype=np.float32)[None, :, None]
    mid = np.clip(ea * (1 - g) + eb * g, 0, 255).astype(np.uint8)
    strip = np.concatenate([A, mid, B], axis=1)
    travel = fw + gw
    e = _smoother(u)
    speed = 30 * u * u * (1 - u) * (1 - u)          # d(smoother)/du, peaks at 1.875
    k = int(blur * travel * speed * 0.16)
    x0 = int(round(e * travel))
    lo, hi = max(0, x0 - k), min(strip.shape[1], x0 + fw + k)
    seg = strip[:, lo:hi]
    if k >= 2:
        seg = cv2.blur(seg, (k | 1, 1), borderType=cv2.BORDER_REPLICATE)
        seg = cv2.blur(seg, (max(1, k // 3) | 1, 1), borderType=cv2.BORDER_REPLICATE)
    out = seg[:, x0 - lo:x0 - lo + fw]
    if direction < 0:
        out = out[:, ::-1]
    if axis == "y":
        out = out.transpose(1, 0, 2)
    return _out(np.ascontiguousarray(out))


# ---------------------------------------------------------------- rise ---

def rise(a, b, u, box=(400, 230, 560, 320), tip=26.0, sway=5.0):
    """Crane up and away from a until it is a small rectangle inside b.

    b is the wide picture (the whole room) and box = (x0, y0, x1, y1) is where a (one desk) belongs
    in it. At u = 0 the frame is exactly a. As the camera lifts, a shrinks towards its place and b
    spreads out round it, rigidly: a and b are one picture being left behind. On the way the camera
    tips back (`tip` degrees at the middle, so the far side of the room narrows) and rolls a little
    (`sway` degrees), and levels out as it stops. At u = 1 the frame is exactly b, so paint a (small)
    into b at box yourself or the desk will blink out on the last frame.
    box should be about 16:9; if it is not, a is squeezed to fit as it lands."""
    if u <= 0:
        return fit(a)
    if u >= 1:
        return fit(b)
    A, B = _rgb(a), _rgb(b)
    x0, y0, x1, y1 = [float(v) for v in box]
    bw, bh = max(2.0, x1 - x0), max(2.0, y1 - y0)
    bcx, bcy = (x0 + x1) / 2, (y0 + y1) / 2
    e = smooth(u)
    rx, ry = bw / W, bh / H
    sx, sy = rx ** e, ry ** e
    frac = (1 - sx) / (1 - rx) if abs(1 - rx) > 1e-6 else e
    cx, cy = CX + (bcx - CX) * frac, CY + (bcy - CY) * frac
    ma = np.array([[sx, 0, cx - sx * CX], [0, sy, cy - sy * CY], [0, 0, 1.0]])
    kx, ky = sx / rx, sy / ry
    mb = np.array([[kx, 0, cx - kx * bcx], [0, ky, cy - ky * bcy], [0, 0, 1.0]])
    bell = math.sin(math.pi * u) ** 1.3
    roll = np.vstack([_sim(1.0, sway * bell * (1 - 0.3 * u), (CX, CY), (CX, CY)), [0, 0, 1.0]])
    cam = _tilt_matrix((W, H), tip * bell, 0.5, 1.0 + 0.10 * bell, 900.0) @ roll
    out = cv2.warpPerspective(B, cam @ mb, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out = out.astype(np.float32)
    # a, pre-shrunk so its pencil lines stay clean, then set into the room
    src = A
    pre = np.eye(3)
    if min(sx, sy) < 0.7:
        src = cv2.resize(A, None, fx=sx, fy=sy, interpolation=cv2.INTER_AREA)
        pre = np.diag([1 / sx, 1 / sy, 1.0])
    full = cam @ ma
    wa = cv2.warpPerspective(src, full @ pre, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    q = cv2.perspectiveTransform(np.array([[[0, 0], [W, 0], [W, H], [0, H]]], np.float64), full)[0]
    mask = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(mask, np.round(q * 16).astype(np.int32), 255, lineType=cv2.LINE_AA, shift=4)
    lift = 16 * bell + 3
    sh = cv2.warpAffine(mask, np.array([[1, 0, lift * 0.5], [0, 1, lift]]), (W, H))
    sh = cv2.GaussianBlur(sh, (0, 0), 3 + lift * 0.6).astype(np.float32) / 255.0
    out *= 1 - 0.32 * sh[:, :, None]
    k = mask.astype(np.float32)[:, :, None] / 255.0
    out = out * (1 - k) + wa.astype(np.float32) * k
    return _out(out)


# ------------------------------------------------------- through_glass ---

def through_glass(inside, outside, cx, cy, r, u, far=0.45, tint=(196, 226, 226)):
    """Pass through a round window. `inside` is a picture with a round window at (cx, cy), radius r;
    `outside` is what is on the other side.

    The camera pushes at the window: the inside picture swells about the window (its rim grows until
    it passes the frame edges and is gone) while the outside, being far away, hardly grows at all
    until the last moment. A pane of glass sits in the hole: a faint tint, a moving shine, and the
    rim's own shadow on it, all of which thin out as the lens meets the glass and goes through. At
    u = 1 the frame is exactly `outside`.
    far:  how distant the outside is. Smaller is farther: at the start we see only the middle `far`
          of the outside picture's height through the window.
    tint: colour of the glass, or None for an open hole.
    Use it both ways: through_glass(tin_inside, river, ...) for the first friend looking out, and
    through_glass(river_with_tin, tin_inside, ...) for going back in. Nothing is drawn for the rim:
    paint the brass ring in `inside`, round the same (cx, cy, r)."""
    if u >= 1:
        return fit(outside)
    I, O = _rgb(inside), _rgb(outside)
    u = max(0.0, u)
    reach = max(math.hypot(CX, CY) * 1.12 / r, 1.5)
    s = reach ** (u ** 1.15)
    frac = (s - 1) / (reach - 1)
    px, py = cx + (CX - cx) * frac, cy + (CY - cy) * frac
    R = r * s
    fi = _streak(I, s, 0, (cx, cy), (px, py), amount=0.25 * u)
    o0 = min(1.0, (2.0 * r / H) / far)
    so = max(o0 ** (1 - smooth(u)), _cover(px, py, R + 2))
    fo = _streak(O, so, 0, (CX, CY), (px, py), amount=0.015 * math.sin(math.pi * u))
    d = np.sqrt((_XS - px) ** 2 + (_YS - py) ** 2)
    hole = np.clip((R - d) / 1.5 + 0.5, 0, 1)
    thin = (1 - u) ** 1.4
    if tint is not None:
        fo += (np.array(tint, np.float32) - fo) * (0.20 * thin)
        # shine: two soft bars across the upper left of the pane, sliding as we close in
        qa = ((_XS - px) + (_YS - py)) / (R * 1.414)
        qb = ((_XS - px) - (_YS - py)) / (R * 1.414)
        sl = 0.25 * u
        shine = (0.55 * np.exp(-((qa + 0.50 - sl) / 0.07) ** 2) + 0.35 * np.exp(-((qa + 0.30 - sl) / 0.025) ** 2))
        shine *= np.exp(-(qb / 0.55) ** 2) * thin
        fo += (255.0 - fo) * shine[:, :, None]
    # the rim throws a shadow on the pane's edge
    rim = np.clip((d - R * 0.80) / (R * 0.20), 0, 1) ** 2 * 0.55 * (0.35 + 0.65 * thin)
    fo *= (1 - rim)[:, :, None]
    out = fi + (fo - fi) * hole[:, :, None]
    return _out(out)


# --------------------------------------------------------------- blink ---

def blink(img, u, to=None, lid=LID, shut=0.12):
    """An eyelid closing and opening: a child shuts their eyes to picture something.

    u 0 -> 0.5 the lids come together (the upper one travels further, both are curved and out of
    focus, and the picture dims and softens as the light goes); around 0.5 it is dark for `shut` of
    the whole blink; 0.5 -> 1 they open again.
    to:  a second picture to open the eyes ON (the thing pictured, or the desk again after it).
         Without it the eyes open on the same picture.
    lid: colour of the inside of the eyelid.
    Hold u at 0.5 for as long as the eyes stay shut."""
    if u <= 0:
        return fit(img)
    if u >= 1:
        return fit(to if to is not None else img)
    src = _rgb(to if (to is not None and u > 0.5) else img)
    o = abs(2 * u - 1)
    o = smooth((o - shut) / (1 - shut))
    lidc = np.array(lid[:3], np.float32)
    if o <= 0:
        out = np.empty((H, W, 3), np.float32)
        out[:] = lidc
        return _out(out)
    sigma = 9.0 * (1 - o) ** 1.5
    pic = _soften(src, sigma) if sigma > 0.5 else src
    pic = pic.astype(np.float32) * (0.45 + 0.55 * o)
    xn = (_XS - CX) / (0.8 * W)
    arch = np.sqrt(1 - xn * xn)
    line = 0.60 * H
    top = line - 480.0 * o * arch
    bot = line + 345.0 * o * arch
    soft = 46.0
    m = np.clip(np.minimum(_YS - top, bot - _YS) / soft, 0, 1)
    m = m * m * (3 - 2 * m)
    # a warm bleed of light through the skin just inside the lid edge
    glow = (m * (1 - m) * 4)[:, :, None] * np.array([70, 26, 18], np.float32) * (0.4 + 0.6 * o)
    out = lidc + glow + (pic - lidc - glow) * m[:, :, None]
    return _out(out)


# -------------------------------------------------------------- thought ---

def _ring_radius(ang, rr, wobble, phase):
    """A hand-drawn circle: never quite round, and it breathes with `phase`."""
    k = 1 + 0.018 * np.sin(2 * ang + 0.6 + phase) + 0.011 * np.sin(3 * ang + 2.1 - 1.7 * phase)
    return rr * k + wobble * (0.6 * np.sin(5 * ang + 1.3 + 2.3 * phase) + 0.4 * np.sin(9 * ang + 4.0 - 3.1 * phase))


def thought(desk, inner, cx, cy, r, u, wobble=0, t=0, dim=0.16, ring=GRAPHITE):
    """The inner picture seen in a soft-edged, pencil-ringed opening over the desk picture.

    The opening grows from a point at (cx, cy) to radius r (it slightly overshoots and settles, like
    a breath), and the inner picture grows with it: at full size the middle of `inner` is shown at a
    scale that fits its height to the ring. The edge is feathered, so the thought has no hard rim,
    and a graphite ring (two passes of a not-quite-round pencil line with skips in it) is drawn round
    it as it opens. The desk outside dims and softens a little as the thought takes over.
    u:      0 nothing, 1 fully open. Run u back down to let the thought fall shut.
    wobble: unsteadiness of the ring in pixels (0 is a calm ring; 4 to 8 is a thought that will not
            hold still: use it when the child is unsure).
    t:      time in seconds; the ring is redrawn 8 times a second, like a boiling line. Leave 0 for a
            still ring.
    dim:    how much the desk darkens under a full thought.
    For a thought that fills the frame, go on from here with dive(desk_with_thought, inner, cx, cy, u)."""
    D = _rgb(desk)
    if u <= 0:
        return _out(D)
    I = _rgb(inner)
    e = clamp(u)
    grow = _EASES["back"](e) if e < 1 else 1.0
    rr = max(1.0, r * grow)
    phase = 1.7 * math.floor(t * 8)
    out = D.astype(np.float32)
    if dim:
        soft = cv2.GaussianBlur(D, (0, 0), 0.6 + 1.2 * e).astype(np.float32)
        out += (soft * (1 - dim) - out) * e
    # the inner picture, scaled with the opening
    sc = (2.0 * rr * 1.08) / H * (0.8 + 0.2 * e)
    src = I
    m = _sim(sc, 0, (CX, CY), (cx, cy))
    if sc < 0.6:
        src = cv2.resize(I, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        m = np.hstack([m[:, :2] / sc, m[:, 2:]])
    x0, y0 = int(max(0, cx - rr * 1.15 - 12)), int(max(0, cy - rr * 1.15 - 12))
    x1, y1 = int(min(W, cx + rr * 1.15 + 12)), int(min(H, cy + rr * 1.15 + 12))
    if x1 > x0 and y1 > y0:
        m_box = m.copy()
        m_box[0, 2] -= x0
        m_box[1, 2] -= y0
        wi = cv2.warpAffine(src, m_box, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        dx = _XS[:, x0:x1] - cx
        dy = _YS[y0:y1] - cy
        dist = np.sqrt(dx * dx + dy * dy)
        ang = np.arctan2(dy, dx)
        edge = _ring_radius(ang, rr, wobble, phase)
        feather = max(5.0, 0.16 * rr)
        k = np.clip((edge - dist) / feather, 0, 1)
        k = (k * k * (3 - 2 * k))[:, :, None]
        reg = out[y0:y1, x0:x1]
        reg += (wi.astype(np.float32) - reg) * k
    frame = _out(out)
    # the pencil ring, drawn round as the thought opens
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(over)
    steps = int(clamp(rr * 0.9, 40, 220))
    drawn = clamp(u * 1.6)
    for p, (dph, dr_off, wd, al) in enumerate(((0.0, 3.0, 3, 225), (0.9, 6.0, 2, 165))):
        a0 = -2.2 + 0.5 * p
        last = None
        for i in range(int(steps * drawn * (1.04 if p == 0 else 0.93)) + 1):
            an = a0 + 2 * math.pi * i / steps
            rad = float(_ring_radius(np.float64(an), rr, wobble, phase + dph)) + dr_off * (0.6 + 0.4 * math.sin(an * 1.5 + p))
            pt = (cx + rad * math.cos(an), cy + rad * math.sin(an))
            if last is not None:
                press = 0.55 + 0.45 * math.sin(an * 2.7 + 1.9 * p + phase)      # pencil pressure
                if press > 0.12:
                    dr.line([last, pt], fill=tuple(ring[:3]) + (int(al * clamp(press + 0.25)),), width=wd)
            last = pt
    frame.paste(over, (0, 0), over)
    return frame


# ----------------------------------------------------------------- test ---

def _test_pictures():
    """Two unlike pictures (a desk and a tin wall with a window) and a third for the far side."""
    from pathlib import Path
    here = Path(__file__).resolve().parent
    picks = [here / "stills/c13/005.00.png", here / "stills/c13/022.30.png", here / "stills/c13/029.30.png"]
    if all(p.exists() for p in picks):
        return [Image.open(p).convert("RGB") for p in picks]
    out = []
    for ground, ink, shape in (((236, 232, 220), (60, 56, 52), "ring"), ((48, 52, 50), (190, 150, 70), "ring"),
                               ((70, 130, 130), (230, 240, 236), "bars")):
        im = Image.new("RGB", (W, H), ground)
        d = ImageDraw.Draw(im)
        for k in range(0, W, 60):
            d.line([(k, 0), (k, H)], fill=tuple(int(c * 0.9) for c in ground), width=2)
        if shape == "ring":
            d.ellipse([260, 50, 700, 490], outline=ink, width=14)
            d.rectangle([120, 400, 260, 470], outline=ink, width=5)
        else:
            for k in range(6):
                d.ellipse([80 + k * 150, 150 + (k % 2) * 120, 180 + k * 150, 200 + (k % 2) * 120], fill=ink)
        out.append(im)
    return out


def _strip(frames, label):
    """Eight frames in a 4 x 2 sheet, each at half size, with u printed on it."""
    sheet = Image.new("RGB", (4 * 484 + 4, 2 * 276 + 4 + 22), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    d.text((6, 4), label, fill=(240, 240, 240))
    for i, (tag, fr) in enumerate(frames):
        assert fr.size == (W, H) and fr.mode == "RGB", (label, fr.size, fr.mode)
        th = fr.resize((480, 270), Image.LANCZOS)
        x, y = 4 + (i % 4) * 484, 26 + (i // 4) * 276
        sheet.paste(th, (x, y))
        d.rectangle([x, y, x + 62, y + 14], fill=(0, 0, 0))
        d.text((x + 3, y + 1), tag, fill=(255, 255, 255))
    return sheet


def _test():
    import time
    from pathlib import Path
    out = Path(__file__).resolve().parent / "stills" / "cam"
    out.mkdir(parents=True, exist_ok=True)
    a, b, c = _test_pictures()
    us = [0.0, 0.14, 0.28, 0.42, 0.56, 0.70, 0.86, 1.0]

    # layers for shoot: far wall, a big desk, a sheet, a foreground sleeve
    desk = a.resize((1920, 1080), Image.LANCZOS)
    sheet = Image.new("RGBA", (700, 500), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sheet)
    ds.rounded_rectangle([10, 10, 690, 490], 6, fill=(250, 247, 239, 255), outline=(120, 110, 100, 255), width=2)
    ds.ellipse([220, 90, 480, 350], outline=(60, 56, 52, 255), width=5)
    for k in range(5):
        ds.line([(60, 380 + k * 20), (640 - 70 * (k % 3), 380 + k * 20)], fill=(90, 86, 82, 255), width=3)
    sleeve = Image.new("RGBA", (1400, 900), (0, 0, 0, 0))
    ImageDraw.Draw(sleeve).polygon([(1400, 520), (820, 600), (760, 700), (860, 760), (1400, 900)], fill=(38, 110, 112, 255))
    ImageDraw.Draw(sleeve).ellipse([690, 600, 860, 760], fill=(196, 96, 60, 255))
    layers = [(b, 4.0), (desk, 1.6), (sheet, 1.0), (sleeve, 0.5)]

    jobs = {
        "shoot_pan_rack": lambda u: shoot(layers, x=key(u, [(0, -260), (1, 240)]), y=key(u, [(0, 60), (1, -40)]),
                                          zoom=key(u, [(0, 0.8), (1, 1.25)]), rot=key(u, [(0, -5), (1, 7)]),
                                          focus=key(u, [(0, 0.5), (0.5, 1.0), (1, 4.0)]), shake=4, t=u * 3),
        "shoot_dolly": lambda u: shoot(layers[:3], dolly=key(u, [(0, -0.6), (1, 0.93)], "in"), rot=u * 20, focus=1.0),
        "tilt": lambda u: tilt(a, u * 70, horizon=0.5),
        "tilt_seat": lambda u: tilt(desk, key(u, [(0, 0), (1, 66)]), horizon=key(u, [(0, 0.5), (1, 0.34)]),
                                    zoom=key(u, [(0, 0.5), (1, 0.85)]), f=700, bg=(60, 50, 44)),
        "dive": lambda u: dive(a, c, 520, 130, u),
        "dive_spin": lambda u: dive(a, b, 300, 300, u, spin=120),
        "turn_y": lambda u: turn(a, b, u),
        "turn_x_side": lambda u: turn(a, c, u, axis="x", side=b),
        "whip": lambda u: whip(a, b, u),
        "whip_up": lambda u: whip(a, c, u, direction=-1, axis="y"),
        "rise": lambda u: rise(a, _room(b, a, (380, 300, 540, 390)), u, box=(380, 300, 540, 390)),
        "through_glass": lambda u: through_glass(b, c, 480, 265, 212, u),
        "through_glass_small": lambda u: through_glass(_small_window(a, c), c, 700, 180, 60, u),
        "blink": lambda u: blink(a, u),
        "blink_to": lambda u: blink(a, u, to=c),
        "thought": lambda u: thought(a, c, 480, 300, 190, u),
        "thought_wobble": lambda u: thought(a, b, 300, 250, 150, key(u, [(0, 0), (0.5, 1), (1, 0.15)]), wobble=7, t=u * 2),
    }
    for name, fn in jobs.items():
        t0 = time.time()
        frames = [("u=%.2f" % u, fn(u)) for u in us]
        dt = (time.time() - t0) / len(us)
        again = fn(us[3])
        pure = np.array_equal(np.asarray(again), np.asarray(frames[3][1]))
        _strip(frames, "%s   %.0f ms per frame%s" % (name, dt * 1000, "" if pure else "   NOT PURE")).save(out / (name + ".png"))
        print("%-22s %5.0f ms/frame  pure=%s" % (name, dt * 1000, pure))
    # endpoints must be the pictures themselves
    for name, f0, f1, e0, e1 in (("dive", dive(a, c, 5, 5, 0), dive(a, c, 5, 5, 1), a, c), ("turn", turn(a, b, 0), turn(a, b, 1), a, b),
                                 ("whip", whip(a, b, 0), whip(a, b, 1), a, b), ("rise", rise(a, b, 0), rise(a, b, 1), a, b),
                                 ("blink", blink(a, 0), blink(a, 1, to=c), a, c), ("tilt", tilt(a, 0, shadow=0), a, a, a),
                                 ("glass", a, through_glass(a, c, 5, 5, 50, 1), a, c)):
        ok = np.array_equal(np.asarray(f0), np.asarray(e0)) and np.array_equal(np.asarray(f1), np.asarray(e1))
        print("endpoints %-6s %s" % (name, "exact" if ok else "DIFFER"))
    print("key:", key(1.0, [(0, 0), (2, 10)], "linear"), key(0.5, [(0, (0, 0)), (1, (10, 20))]), key(1.5, [(0, 1), (1, 2, "hold"), (2, 5)]))
    print("strips ->", out)


def _room(wall, small, box):
    im = wall.copy()
    x0, y0, x1, y1 = box
    im.paste(small.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
    return im


def _small_window(base, beyond):
    im = base.copy()
    d = ImageDraw.Draw(im)
    hole = beyond.resize((int(W * 0.5), int(H * 0.5)), Image.LANCZOS).crop((240 - 60, 135 - 60, 240 + 60, 135 + 60))
    mask = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 119, 119], fill=255)
    im.paste(hole, (640, 120), mask)
    d.ellipse([632, 112, 768, 248], outline=(176, 138, 62), width=10)
    return im


if __name__ == "__main__":
    _test()
