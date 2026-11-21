"""The lead dog of THE DOGS OF TROUTTOWN: a jointed cut-paper puppet.

One torn ear, a red collar, four two-part legs with paws on pins. Everything is
computed from a POSE (a flat dict of numbers), so any two poses blend, and the
same pose draws in colour or as a pure silhouette, facing either way.

    import dog
    pose = dog.walk(t)                               # a performance -> a pose
    dog.draw_dog(ink, pose, x, y, scale=1.0, facing=1)

    score = dog.Score([(0, "watch"), (3.0, "back_away"), (6.5, "sit")])
    dog.draw_dog(ink, score.pose(t), x, y)           # ears and tail lead every change

Units: one dog unit is one pixel at scale=1.0; the standing dog is 100 units
tall at the withers and about 250 long, nose to tail tip. The puppet is drawn
facing RIGHT (toward the water) at facing=+1. Rig maths is y-up; the anchor
(0, 0) is the ground under the middle of the body for ground poses and the
middle of the body for swimming and airborne poses (pose["_anchor"]).

Ancestor: paeleo/threshold (machine.js, stage.js). Its five-state decision
machine is ported here as DogMind. Worked under scion/animation-48.md.

    python3 films/swarm/dogs/dog.py        # writes the pose sheet and the strips
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
TAU = 2 * math.pi

# ------------------------------------------------------------------ colours ---
COLORS = {
    "coat": (216, 160, 98), "coat_far": (166, 116, 70), "chest": (245, 230, 202),
    "ear": (112, 68, 38), "ear_far": (88, 54, 31), "collar": (212, 42, 30),
    "tag": (214, 176, 84), "nose": (36, 23, 15), "eye": (30, 20, 14),
    "tongue": (226, 112, 118), "brad": (206, 170, 86), "glint": (255, 250, 232),
    "page": (250, 246, 233), "pencil": (120, 104, 150), "crayon": (212, 96, 60),
    "part": (196, 150, 70), "part_dark": (120, 86, 40),
    "reel": (176, 186, 196), "reel_dark": (70, 76, 92), "film": (48, 42, 50),
    "edge": (58, 30, 12),
}
SILHOUETTE = (20, 17, 26)


# ------------------------------------------------------------------- easing ---
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, x):
    return a + (b - a) * x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease(t, a, b):
    """0 before a, 1 after b, smoothstep between."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return smooth((t - a) / (b - a))


def ease_back(x):
    """Smoothstep that first pulls a little the wrong way and settles past the
    mark: anticipation and overshoot for anything with weight."""
    x = clamp(x)
    return smooth(x) - 0.085 * math.sin(TAU * x)


def bump(x):
    """0 -> 1 -> 0 over x in 0..1."""
    return math.sin(math.pi * clamp(x)) ** 2 if 0 < x < 1 else 0.0


def _rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def _hash(n):
    n = math.sin(n * 127.1 + 311.7) * 43758.5453
    return n - math.floor(n)


def _cut(pts, amt, seed):
    """Scissor wobble: the same on every frame, so the paper never boils."""
    return [(x + (_hash(seed + i * 1.7) - 0.5) * amt, y + (_hash(seed + i * 2.3 + 9) - 0.5) * amt)
            for i, (x, y) in enumerate(pts)]


def _ellipse(cx, cy, rx, ry, n=16, seed=0, amt=0.05, a=0.0):
    pts = []
    for i in range(n):
        th = TAU * i / n
        k = 1 + (_hash(seed + i) - 0.5) * amt
        pts.append(_add((cx, cy), _rot((math.cos(th) * rx * k, math.sin(th) * ry * k), a)))
    return pts


def _capsule(a, b, wa, wb, seed=0, n=5):
    """A tapered limb from a to b, round at both ends."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    pts = []
    for i in range(n + 1):
        th = -math.pi / 2 + i / n * math.pi
        pts.append((b[0] + wb * (math.cos(th) * ux + math.sin(th) * nx), b[1] + wb * (math.cos(th) * uy + math.sin(th) * ny)))
    for i in range(n + 1):
        th = math.pi / 2 + i / n * math.pi
        pts.append((a[0] + wa * (math.cos(th) * ux + math.sin(th) * nx), a[1] + wa * (math.cos(th) * uy + math.sin(th) * ny)))
    return _cut(pts, 0.7, seed)


# ---------------------------------------------------------------- anatomy ---
# Bone lengths and joint limits. BUILD can be overridden per draw (build={...})
# to cut a different dog on the same skeleton.
BUILD = {
    "arm": 36.0, "forearm": 36.0, "thigh": 38.0, "shank": 38.0, "hock": 22.0,
    "elbow_min": 0.50, "knee_min": 0.42,      # smallest interior joint angle, radians
    "neck": 38.0, "tail": 62.0, "ear": 40.0, "head": 1.13,
}

# cut shapes, in their own frames (x forward, y up)
_RIB = [(0, 21), (22, 25), (44, 25), (58, 17), (67, 3), (63, -13), (49, -27), (30, -31), (12, -26), (-2, -17)]
_PELVIS = [(-20, 22), (-44, 24), (-62, 17), (-71, 3), (-67, -12), (-52, -19), (-34, -15), (-22, -10)]
_CHEST = [(59, 7), (67, 2), (63, -13), (50, -26), (40, -28), (46, -13), (53, -2)]
_MUZZLE = [(16, 13), (30, 11), (44, 8), (55, 6), (60, 2), (58, -4), (40, -5), (22, -6), (12, -3)]
_JAW = [(-5, 2), (10, 1), (30, 0.5), (35, -2), (31, -6), (12, -8), (-3, -7)]
_EAR_WHOLE = [(-3, 0), (0, -8), (12, -10), (27, -6), (40, 0), (26, 5), (11, 8), (0, 7)]
# the torn ear: the tip is gone and a bite is out of the trailing edge
_EAR_TORN = [(-3, 0), (0, -8), (12, -10), (25, -8), (31, -6.5), (25, -2), (30, 2.5), (19, 2.2), (15, 7.5), (0, 7)]
_FOREPAW = [(-6, 3), (4, 4), (8, -1), (17, -5), (19, -9), (9, -10.5), (-5, -10.5), (-7, -3)]
_FORE_SOLE = (2.0, -10.0)
_TOE_OFF = (4.0, -5.0)

LEGS = ("fn", "ff", "hn", "hf")          # fore near, fore far, hind near, hind far

STAND = {
    "cx": 0.0, "cy": 84.0, "pitch": 0.0, "arch": 0.0, "twist": 0.0,
    "neck": 0.78, "head": -0.06, "jaw": 0.0, "tongue": 0.0,
    "ear": 0.72, "ear_f": 0.72, "eye": 1.0, "look": 0.0,
    "tail": 0.15, "curl": 0.45, "wag": 0.0, "sway": 0.0,
    "turn": 1.0, "air": 0.0, "hold": 1.0,
    "fnx": 42.0, "fny": 0.0, "fna": 0.0, "ffx": 51.0, "ffy": 0.0, "ffa": 0.0,
    "hnx": -56.0, "hny": 0.0, "hna": 0.0, "hfx": -45.0, "hfy": 0.0, "hfa": 0.0,
    "_anchor": "ground",
}

GROUPS = {
    "ears": ("ear", "ear_f"),
    "tail": ("tail", "curl", "wag"),
    "head": ("neck", "head", "jaw", "tongue", "eye", "look", "sway", "hold"),
    "body": ("cx", "cy", "pitch", "arch", "twist", "turn", "air"),
    "legs": tuple(l + k for l in LEGS for k in "xya"),
}


def _base(**kw):
    p = dict(STAND)
    p.update(kw)
    return p


def blend(a, b, w, groups=None):
    """Blend pose a toward pose b. w is one number, or {group: weight} over
    'ears', 'tail', 'head', 'body', 'legs'."""
    out = dict(a)
    for g, keys in GROUPS.items():
        wg = w.get(g, 0.0) if isinstance(w, dict) else w
        if groups and g not in groups:
            continue
        for k in keys:
            out[k] = lerp(a.get(k, STAND[k]), b.get(k, STAND[k]), wg)
    wb = w.get("body", 0.0) if isinstance(w, dict) else w
    out["_anchor"] = b.get("_anchor", "ground") if wb >= 0.5 else a.get("_anchor", "ground")
    return out


def _ik(root, target, l1, l2, side, min_angle):
    """Two-bone IK with a joint limit. side +1 puts the middle joint to the left
    of root->target (forward for a leg that points down), -1 to the right.
    Returns (mid, end); end falls short of the target when the leg cannot reach
    or cannot fold that far."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy) or 1e-6
    lo = math.sqrt(max(0.0, l1 * l1 + l2 * l2 - 2 * l1 * l2 * math.cos(min_angle)))
    dd = clamp(d, lo, l1 + l2 - 0.4)
    ux, uy = dx / d, dy / d
    a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    mid = (root[0] + ux * a - uy * h * side, root[1] + uy * a + ux * h * side)
    return mid, (root[0] + ux * dd, root[1] + uy * dd)


def solve(pose, carry=None, build=None):
    """Pose -> rig: {'parts': [...], 'joints': {...}} in dog units, y up.
    Each part is (name, points, colour key, edged, holes)."""
    B = dict(BUILD)
    if build:
        B.update(build)
    P = dict(STAND)
    P.update(pose)
    M = (P["cx"], P["cy"])
    ar, ap = P["pitch"] - P["arch"] / 2, P["pitch"] + P["arch"] / 2
    tw = P["twist"]

    def rib(p):
        return _add(M, _rot((p[0], p[1] * (1 + 0.13 * tw) + 5.0 * tw), ar))

    def pel(p):
        return _add(M, _rot((p[0], p[1] * (1 - 0.13 * tw) - 5.0 * tw), ap))

    def mid(p):
        return _add(M, _rot(p, P["pitch"]))

    parts, J = [], {}

    def part(name, pts, col, edged=True, holes=None):
        parts.append((name, pts, col, edged, holes))

    J["body"] = M
    S, Sf = rib((50, -8)), rib((56, -7))
    H, Hf = pel((-46, -2)), pel((-40, -1))
    J["shoulder"], J["hip"] = S, H
    air = clamp(P["air"])

    def foreleg(root, tag, far):
        C = (P[tag + "x"], P[tag + "y"])
        a = P[tag + "a"] - 1.0 * max(0.75 * air, clamp(C[1] / 14.0) * (1 - air))
        wrist_t = (C[0] - _rot(_FORE_SOLE, a)[0], C[1] - _rot(_FORE_SOLE, a)[1])
        elbow, wrist = _ik(root, wrist_t, B["arm"], B["forearm"], -1, B["elbow_min"])
        col = "coat_far" if far else "coat"
        part(tag + ".arm", _capsule(root, elbow, 12.5, 8.5, 61 + far), col)
        part(tag + ".forearm", _capsule(elbow, wrist, 8.0, 5.6, 81 + far), col)
        part(tag + ".paw", _cut([_add(wrist, _rot(q, a)) for q in _FOREPAW], 0.6, 91 + far), col)
        J[tag + ".elbow"], J[tag + ".wrist"] = elbow, wrist
        J[tag + ".paw"] = _add(wrist, _rot(_FORE_SOLE, a))

    def hindleg(root, tag, far):
        C = (P[tag + "x"], P[tag + "y"])
        a = P[tag + "a"]
        meta = _rot((2.0, -B["hock"]), a)
        k = max(air, clamp(C[1] / 12.0))
        md = math.atan2(meta[1], meta[0])
        td = lerp(0.0, md + 0.7, k)                      # toes flat when planted, trailing when lifted
        toe = (math.cos(td), math.sin(td))
        hock_t = (C[0] - _TOE_OFF[0] * (1 - k) - meta[0], C[1] - _TOE_OFF[1] * (1 - k) - meta[1])
        knee, hock = _ik(root, hock_t, B["thigh"], B["shank"], +1, B["knee_min"])
        E = _add(hock, meta)
        col = "coat_far" if far else "coat"
        part(tag + ".thigh", _capsule(root, knee, 19.0, 10.0, 71 + far), col)
        part(tag + ".shank", _capsule(knee, hock, 9.0, 5.8, 75 + far), col)
        part(tag + ".hock", _capsule(hock, E, 6.2, 5.0, 77 + far, n=3), col)
        part(tag + ".toes", _capsule(_add(E, (-toe[0] * 3, -toe[1] * 3 - 0.5)), _add(E, (toe[0] * 14, toe[1] * 14 - 0.5)), 5.0, 4.2, 79 + far, n=3), col)
        J[tag + ".knee"], J[tag + ".hock"] = knee, hock
        J[tag + ".paw"] = _add(E, (toe[0] * 6, toe[1] * 6 - 5))

    # ---- far legs, tail
    hindleg(Hf, "hf", 1)
    foreleg(Sf, "ff", 1)
    T = pel((-66, 11))
    J["tail_root"] = T
    n = 9
    spine, ang, p = [], ap + math.pi - P["tail"], T
    for i in range(n + 1):
        s = i / n
        spine.append((p, lerp(7.0, 2.4, s) + 2.2 * math.sin(math.pi * s)))
        th = ang - P["curl"] * s + P["wag"] * math.sin(math.pi * (0.25 + 0.85 * s)) * (0.35 + 0.65 * s)
        p = _add(p, (math.cos(th) * B["tail"] / n, math.sin(th) * B["tail"] / n))
    left, right = [], []
    for i, (q, w) in enumerate(spine):
        a0, a1 = spine[max(0, i - 1)][0], spine[min(n, i + 1)][0]
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]
        L = math.hypot(dx, dy) or 1.0
        left.append((q[0] - dy / L * w, q[1] + dx / L * w))
        right.append((q[0] + dy / L * w, q[1] - dx / L * w))
    part("tail", _cut(left + right[::-1], 0.6, 7), "coat")
    J["tail_tip"] = spine[-1][0]

    # ---- trunk: pelvis, loin, ribcage
    part("pelvis", _cut([pel(q) for q in _PELVIS], 0.9, 11), "coat")
    part("loin", _cut([pel((-34, 21)), mid((-6, 22.5)), rib((14, 23)), rib((12, -22)), mid((-6, -14)), pel((-30, -13))], 0.8, 13), "coat", False)
    part("ribcage", _cut([rib(q) for q in _RIB], 0.9, 17), "coat")
    part("chest", _cut([rib(q) for q in _CHEST], 0.6, 23), "chest", False)

    # ---- near legs
    hindleg(H, "hn", 0)
    foreleg(S, "fn", 0)

    # ---- neck, collar
    N = rib((53, 9))
    na = ar + P["neck"]
    nd = (math.cos(na), math.sin(na))
    K = _add(N, (nd[0] * B["neck"], nd[1] * B["neck"]))
    part("neck", _capsule(_add(N, (-nd[0] * 8, -nd[1] * 8)), K, 18.0, 12.5, 101), "coat")
    cc = _add(N, (nd[0] * B["neck"] * 0.6, nd[1] * B["neck"] * 0.6))
    nn = (-nd[1], nd[0])
    hw, th = 15.6, 3.4
    part("collar", [(cc[0] + nn[0] * hw - nd[0] * th, cc[1] + nn[1] * hw - nd[1] * th), (cc[0] + nn[0] * hw + nd[0] * th, cc[1] + nn[1] * hw + nd[1] * th),
                    (cc[0] - nn[0] * hw + nd[0] * th, cc[1] - nn[1] * hw + nd[1] * th), (cc[0] - nn[0] * hw - nd[0] * th, cc[1] - nn[1] * hw - nd[1] * th)], "collar", False)
    low = (cc[0] - nn[0] * hw, cc[1] - nn[1] * hw) if nn[1] > 0 else (cc[0] + nn[0] * hw, cc[1] + nn[1] * hw)
    part("tag", _ellipse(low[0] + 1.0, low[1] - 3.5, 3.4, 3.4, 9, 5, 0.0), "tag", False)
    J["neck"], J["head"], J["collar"] = N, K, cc

    # ---- head: far ear, jaw, skull, muzzle, near (torn) ear, eye, nose
    ha = ar + P["head"]
    sx = 1 - 2 * clamp(P["look"])
    if abs(sx) < 0.08:
        sx = 0.08 if sx >= 0 else -0.08

    def hd(p):
        q = _rot((p[0] * B["head"], p[1] * B["head"]), ha)
        return (K[0] + q[0] * sx, K[1] + q[1])

    def ear_pts(shape, pivot, v, seed):
        ea = lerp(3.45, 1.5, v)
        k = B["ear"] / 40.0
        return _cut([hd(_add(pivot, _rot((q[0] * k, q[1] * k), ea))) for q in shape], 0.5, seed)

    jp = (20, -4.6)

    def jw(p):
        return hd(_add(jp, _rot(p, -P["jaw"])))

    part("ear_far", ear_pts(_EAR_WHOLE, (15, 14), P["ear_f"] + 0.13, 51), "ear_far")
    if P["jaw"] > 0.2 and P["tongue"] > 0.05:
        tl = 9 + 13 * clamp(P["tongue"])
        part("tongue", [jw((16, 1)), jw((30, 2)), jw((30 + tl * 0.6, 1 - tl * 0.5)), jw((28 + tl * 0.4, -2 - tl * 0.6)), jw((18, -2))], "tongue", False)
    part("jaw", _cut([jw(q) for q in _JAW], 0.4, 43), "coat")
    mouth = ((hd((40, -5))[0] + jw((27, 0))[0]) / 2, (hd((40, -5))[1] + jw((27, 0))[1]) / 2)
    J["mouth"] = mouth
    J["head_angle"] = ha if sx > 0 else math.pi - ha
    if carry in ("page", "part", "reel") and P["hold"] >= 0.5:
        _carried(part, carry, mouth, P, sx)
    part("skull", [hd(q) for q in _ellipse(10, 3, 18.5, 16, 16, 31, 0.04)], "coat")
    part("muzzle", _cut([hd(q) for q in _MUZZLE], 0.5, 41), "coat")
    part("nose", [hd(q) for q in _ellipse(57.5, 2.0, 4.8, 4.0, 10, 3, 0.0)], "nose", False)
    part("ear", ear_pts(_EAR_TORN, (5, 12), P["ear"], 53), "ear")
    ey = clamp(P["eye"], 0, 1.4)
    if ey > 0.25:
        part("eye", [hd(q) for q in _ellipse(26, 8, 3.1 * min(1.15, 0.7 + 0.3 * ey), 3.4 * min(1.2, ey), 10, 2, 0.0)], "eye", False)
        part("glint", [hd(q) for q in _ellipse(27.2, 9.3, 1.0, 1.0, 6, 2, 0.0)], "glint", False)
    else:
        part("eye", [hd((22.5, 8.6)), hd((29.5, 8.6)), hd((29.5, 7.2)), hd((22.5, 7.2))], "eye", False)
    J["nose"], J["eye"], J["ear_tip"] = hd((60, 2)), hd((26, 8)), ear_pts(_EAR_TORN, (5, 12), P["ear"], 53)[4]
    J["withers"] = rib((46, 25))
    J["brads"] = [S, H, J["fn.elbow"], J["hn.knee"], J["fn.wrist"], J["hn.hock"], N, hd((5, 12)), T, hd(jp)]
    return {"parts": parts, "joints": J}


def _gear(c, r, teeth=7, a=0.0):
    pts = []
    for i in range(teeth * 4):
        th = a + TAU * i / (teeth * 4)
        rr = r if i % 4 in (0, 1) else r * 0.76
        pts.append((c[0] + math.cos(th) * rr, c[1] + math.sin(th) * rr))
    return pts


def _carried(part, kind, mouth, P, sx):
    """The thing in the mouth. It hangs with gravity; pose['sway'] swings it."""
    sw = P["sway"]
    d = 1 if sx > 0 else -1
    if kind == "page":
        a = sw * 0.5 - 0.10 * d

        def pg(p):
            return _add(mouth, _rot(p, a))
        part("page", _cut([pg((-13, 3)), pg((14, 3)), pg((15, -17)), pg((13.5, -33)), pg((-12, -34)), pg((-14, -16))], 0.6, 301), "page")
        part("mark", [pg((-8, -9)), pg((8, -8)), pg((8, -9.6)), pg((-8, -10.6))], "pencil", False)
        part("mark", [pg((-8, -15)), pg((5, -14.4)), pg((5, -16)), pg((-8, -16.6))], "pencil", False)
        part("mark", _ellipse(pg((0, -25))[0], pg((0, -25))[1], 5.5, 4.2, 8, 7, 0.2), "crayon", False)
    elif kind == "part":
        c = _add(mouth, _rot((2 * d, -11), sw * 0.6))
        part("part", _gear(c, 12.5, 7, 0.3 + sw), "part", True, [_ellipse(c[0], c[1], 4.2, 4.2, 10, 1, 0.0)])
    elif kind == "reel":
        c = _add(mouth, _rot((3 * d, -17), sw * 0.6))
        holes = [_ellipse(c[0] + 10.5 * math.cos(TAU * i / 5 + 0.3 + sw), c[1] + 10.5 * math.sin(TAU * i / 5 + 0.3 + sw), 4.3, 4.3, 9, i, 0.0) for i in range(5)]
        tail = [_add(c, (-3 * d, -18)), _add(c, (3 * d, -19)), _add(c, ((4 - 10 * sw) * d, -34)), _add(c, ((-2 - 10 * sw) * d, -35))]
        part("film", tail, "film", False)
        part("reel", _ellipse(c[0], c[1], 19.5, 19.5, 22, 9, 0.02), "reel", True, holes)
        part("hub", _ellipse(c[0], c[1], 3.4, 3.4, 9, 1, 0.0), "reel_dark", False)


# ------------------------------------------------------------------ drawing ---
_tex = None


def _texture():
    global _tex
    if _tex is None:
        rs = np.random.RandomState(7)
        g = rs.normal(0, 1, (256, 256)).astype(np.float32)
        fib = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32) - 128
        xx = np.arange(256, dtype=np.float32)
        streak = np.sin(xx[None, :] * 0.9 + np.sin(xx[:, None] * 0.13) * 4.0)
        _tex = (1.0 + fib / 128 * 0.30 + streak * 0.007).clip(0.88, 1.08)
    return _tex


def _img_of(target):
    return target.img if hasattr(target, "img") else target


def _refresh(target):
    if hasattr(target, "img") and hasattr(target, "d"):
        target.d = ImageDraw.Draw(target.img, "RGBA")


def _mix(c1, c2, x):
    return tuple(int(round(lerp(a, b, clamp(x)))) for a, b in zip(c1, c2))


def _composite(img, spr, ox, oy):
    if img.mode == "RGBA":
        box = (max(0, ox), max(0, oy), min(img.width, ox + spr.width), min(img.height, oy + spr.height))
        if box[2] <= box[0] or box[3] <= box[1]:
            return
        crop = spr.crop((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy))
        region = img.crop(box)
        region.alpha_composite(crop)
        img.paste(region, box[:2])
    else:
        img.paste(spr, (ox, oy), spr)


def draw_dog(target, pose, x, y, scale=1.0, facing=1, silhouette=False, color=None, carry=None,
             anchor=None, shadow=None, tint=None, tint_amount=0.0, alpha=1.0, colors=None,
             build=None, brads=True, keep_collar=False, texture=True, ss=3):
    """Draw the dog on an Ink (kit.py) or a PIL image. Returns screen-space
    joints: nose, mouth, eye, head, neck, collar, shoulder, hip, withers, body,
    tail_root, tail_tip, ear_tip, fn.paw, ff.paw, hn.paw, hf.paw, head_angle,
    bbox."""
    img = _img_of(target)
    rig = solve(pose, carry if isinstance(carry, str) else None, build)
    P = dict(STAND)
    P.update(pose)
    f = float(facing) * P["turn"]
    if abs(f) < 0.06:
        f = 0.06 if f >= 0 else -0.06
    f = clamp(f, -1.0, 1.0)
    anchor = anchor or P.get("_anchor", "ground")
    ax, ay = (P["cx"], P["cy"]) if anchor == "body" else (0.0, 0.0)

    def T(p):
        return (x + f * scale * (p[0] - ax), y - scale * (p[1] - ay))

    pal = dict(COLORS)
    if colors:
        pal.update(colors)
    sil = color or SILHOUETTE
    if shadow is None:
        shadow = not silhouette
    polys = []
    for name, pts, col, edged, holes in rig["parts"]:
        if silhouette:
            if name in ("eye", "glint", "nose", "chest", "tag", "mark", "hub", "tongue"):
                continue
            c = pal["collar"] if (name == "collar" and keep_collar) else sil
            if name == "collar" and not keep_collar:
                continue
            polys.append(([T(p) for p in pts], c, None, [[T(p) for p in h] for h in holes] if holes else None))
        else:
            c = pal[col]
            if tint is not None and tint_amount > 0:
                c = _mix(c, tint, tint_amount)
            e = _mix(c, pal["edge"], 0.5) if edged else None
            polys.append(([T(p) for p in pts], c, e, [[T(p) for p in h] for h in holes] if holes else None))
    xs = [p[0] for pl in polys for p in pl[0]]
    ys = [p[1] for pl in polys for p in pl[0]]
    pad = int(8 + 6 * scale)
    ox, oy = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    w, h = int(math.ceil(max(xs))) - ox + pad, int(math.ceil(max(ys))) - oy + pad
    spr = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    ew = max(1, int(round(ss * 1.15 * max(0.75, scale ** 0.5))))

    def S(pl):
        return [((px - ox) * ss, (py - oy) * ss) for px, py in pl]

    for pts, c, e, holes in polys:
        if holes:
            lay = Image.new("RGBA", spr.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.polygon(S(pts), fill=c + (255,))
            if e:
                ld.line(S(pts) + [S(pts)[0]], fill=e + (255,), width=ew, joint="curve")
            for hpts in holes:
                ld.polygon(S(hpts), fill=(0, 0, 0, 0))
                if e:
                    ld.line(S(hpts) + [S(hpts)[0]], fill=e + (255,), width=max(1, ew - 1))
                    ld.polygon(S([(q[0] * 0.8 + sum(p[0] for p in hpts) / len(hpts) * 0.2, q[1] * 0.8 + sum(p[1] for p in hpts) / len(hpts) * 0.2) for q in hpts]), fill=(0, 0, 0, 0))
            spr.alpha_composite(lay)
            d = ImageDraw.Draw(spr)
            continue
        sp = S(pts)
        d.polygon(sp, fill=c + (255,))
        if e:
            d.line(sp + [sp[0]], fill=e + (255,), width=ew, joint="curve")
    if brads and not silhouette and scale >= 0.45:
        r = 2.1 * scale * ss
        for b in rig["joints"]["brads"]:
            bx, by = S([T(b)])[0]
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=pal["brad"] + (255,), outline=_mix(pal["brad"], pal["edge"], 0.6) + (255,))
            d.ellipse([bx - r * 0.55, by - r * 0.6, bx - r * 0.05, by - r * 0.1], fill=pal["glint"] + (255,))
    spr = spr.resize((w, h), Image.LANCZOS)
    if texture and not silhouette:
        a = np.asarray(spr, np.float32).copy()
        tex = _texture()
        yy = (np.arange(h) + oy - int(round(y))) % 256
        xx = (np.arange(w) + ox - int(round(x))) % 256
        a[..., :3] *= tex[np.ix_(yy, xx)][..., None]
        spr = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    if alpha < 1:
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    if shadow:
        al = spr.getchannel("A")
        off = (int(round(3 * scale)) + 1, int(round(4 * scale)) + 1)
        sh = ImageChops.offset(al, off[0], off[1]).filter(ImageFilter.GaussianBlur(1.2 + 1.6 * scale)).point(lambda v: int(v * 0.36))
        shl = Image.new("RGBA", spr.size, (10, 8, 22, 0))
        shl.putalpha(sh)
        _composite(img, shl, ox, oy)
    _composite(img, spr, ox, oy)
    J = rig["joints"]
    out = {k: T(v) for k, v in J.items() if isinstance(v, tuple)}
    out["head_angle"] = J["head_angle"] if f > 0 else math.pi - J["head_angle"]
    out["bbox"] = (ox + pad, oy + pad, ox + w - pad, oy + h - pad)
    if carry is not None and not isinstance(carry, str) and P["hold"] >= 0.5:
        item = carry.convert("RGBA")
        if scale != 1.0:
            item = item.resize((max(1, int(item.width * scale)), max(1, int(item.height * scale))), Image.LANCZOS)
        mx, my = out["mouth"]
        _composite(img, item, int(mx - item.width / 2), int(my - 2 * scale))
    _refresh(target)
    return out


def body_point(pose, x, y, scale=1.0, facing=1, anchor=None):
    """Screen position of the middle of the body for a pose drawn at (x, y)."""
    P = dict(STAND)
    P.update(pose)
    if (anchor or P.get("_anchor", "ground")) == "body":
        return (x, y)
    return (x + facing * P["turn"] * scale * P["cx"], y - scale * P["cy"])


# ------------------------------------------------------------ performances ---
# Every performance is fn(t, **options) -> pose, t in seconds since it began.
# Cycles loop for ever; one-shots hold their last drawing after DURATION[name].

STRIDE = {"walk": 64.0, "trot": 104.0, "wade": 50.0, "back_away": -44.0}   # dog units per cycle
RATE = {"walk": 1.15, "trot": 2.1, "wade": 0.85, "back_away": 1.5, "dig": 3.0, "swim": 1.3}  # cycles per second
_REST = {"fn": 42.0, "ff": 51.0, "hn": -56.0, "hf": -45.0}
_WALK = {"hn": 0.0, "fn": 0.25, "hf": 0.5, "ff": 0.75}       # four beats, lateral sequence
_TROT = {"fn": 0.0, "hf": 0.0, "ff": 0.5, "hn": 0.5}         # diagonal pairs


def _gait(p, ph, order, duty, stride, lift, rest=None, dx=0.0):
    rest = rest or _REST
    A = abs(stride) * duty
    for leg in LEGS:
        q = (ph - order[leg]) % 1.0
        if q < duty:
            s = q / duty
            off, h, a = 0.5 - s, 0.0, 0.18 - 0.62 * s
        else:
            s = (q - duty) / (1 - duty)
            off, h = -0.5 + smooth(s), math.sin(math.pi * s ** 0.85)
            a = lerp(-0.44, 0.18, smooth(s)) - 0.55 * math.sin(math.pi * s)
        p[leg + "x"] = rest[leg] + dx + A * off
        p[leg + "y"] = lift * h * (1.0 if leg[0] == "f" else 0.8)
        p[leg + "a"] = a if leg[0] == "h" else 0.0
    return p


def _breathe(p, t, amt=1.0):
    b = math.sin(TAU * 0.28 * t)
    p["arch"] -= 0.012 * b * amt
    p["cy"] += 0.5 * b * amt
    return p


def stand(t=0.0):
    """Neutral standing dog, breathing."""
    return _breathe(_base(), t)


def watch(t=0.0, alert=1.0):
    """Stands still and looks: head up, ears pricked, weight a little back. The
    torn ear flicks once in a while; nothing else moves."""
    p = _base(cx=-3.0, neck=0.80 + 0.16 * alert, head=0.02, ear=0.80 + 0.2 * alert, ear_f=0.85 + 0.2 * alert,
              tail=0.30, curl=0.35)
    fl = bump(((t % 3.9) - 2.7) / 0.28)
    p["ear"] -= 0.55 * fl
    return _breathe(p, t, 0.8)


def walk(t=0.0, rate=None, phase=None):
    """Four-beat walk. Each foot lands, takes weight (the body dips over it) and
    pushes off. Travels STRIDE['walk'] units per cycle."""
    ph = (t * (rate or RATE["walk"])) if phase is None else phase
    p = _gait(_base(), ph, _WALK, 0.64, STRIDE["walk"], 13.0)
    sh, hp = -math.cos(2 * TAU * (ph - 0.35)), -math.cos(2 * TAU * (ph - 0.10))
    p["cy"] += 1.5 * (sh + hp) / 2 - 1.5
    p["pitch"] += 0.016 * (sh - hp)
    p["neck"] = 0.66 - 0.05 * math.cos(2 * TAU * (ph - 0.47))        # the head nods late, against the shoulders
    p["head"] = -0.10 + 0.03 * math.cos(2 * TAU * (ph - 0.5))
    p["ear"] = 0.70 + 0.05 * math.cos(2 * TAU * (ph - 0.55))
    p["ear_f"] = 0.72 + 0.05 * math.cos(2 * TAU * (ph - 0.60))
    p["tail"] = 0.22 + 0.05 * math.sin(2 * TAU * (ph - 0.2))
    p["wag"] = 0.22 * math.sin(TAU * (ph - 0.15))
    p["sway"] = 0.25 * math.sin(2 * TAU * (ph - 0.5))
    return p


def trot(t=0.0, rate=None, phase=None):
    """Two-beat trot, diagonal pairs, with bounce; ears and tail arrive late."""
    ph = (t * (rate or RATE["trot"])) if phase is None else phase
    p = _gait(_base(), ph, _TROT, 0.5, STRIDE["trot"], 20.0)
    b = -math.cos(2 * TAU * (ph - 0.25))
    p["cy"] += 3.6 * b + 1.0
    p["pitch"] = 0.03 + 0.022 * math.sin(2 * TAU * (ph - 0.30))
    p["neck"] = 0.92 - 0.05 * math.cos(2 * TAU * (ph - 0.40))
    p["head"] = -0.02
    p["ear"] = 0.62 - 0.16 * math.cos(2 * TAU * (ph - 0.47))
    p["ear_f"] = 0.66 - 0.16 * math.cos(2 * TAU * (ph - 0.52))
    p["tail"] = 0.62 - 0.10 * math.cos(2 * TAU * (ph - 0.45))
    p["curl"] = 0.55
    p["wag"] = 0.15 * math.sin(2 * TAU * (ph - 0.6))
    p["sway"] = 0.4 * math.sin(2 * TAU * (ph - 0.5))
    return p


def back_away(t=0.0, rate=None):
    """Backs off, still facing what pressed it: ears flat and tail tucked first,
    then low on its haunches, stepping backward. Travels STRIDE['back_away']
    (negative) per cycle."""
    ph = -t * (rate or RATE["back_away"])
    low = ease(t, 0.12, 0.55)
    p = _gait(_base(), ph, _WALK, 0.66, STRIDE["back_away"], 9.0)
    sh, hp = -math.cos(2 * TAU * (-ph - 0.35)), -math.cos(2 * TAU * (-ph - 0.10))
    p["cy"] = 84 - 11 * low + 1.2 * (sh + hp) / 2
    p["pitch"] = 0.085 * low + 0.012 * (sh - hp)
    p["cx"] = -5 * low
    p["arch"] = 0.10 * low
    p["neck"] = lerp(0.78, 0.30, low)
    p["head"] = lerp(-0.06, 0.03, low)
    p["ear"] = lerp(0.72, 0.03, ease(t, 0.0, 0.16))
    p["ear_f"] = lerp(0.72, 0.0, ease(t, 0.04, 0.22))
    p["tail"] = lerp(0.15, -1.25, ease(t, 0.03, 0.4))
    p["curl"] = lerp(0.45, -0.5, ease(t, 0.03, 0.4))
    return p


_SIT = dict(cx=-6.0, cy=60.0, pitch=0.60, arch=0.10, neck=0.42, head=-0.62, tail=0.50, curl=0.35,
            fnx=44.0, ffx=52.0, hnx=-8.0, hna=1.45, hfx=2.0, hfa=1.45)


def sit(t=0.0, settle=1.0):
    """Stands -> sits: the rump goes down first and lands, then the chest
    settles. After DURATION it holds, breathing."""
    u = t / settle
    a = _base()
    b = _base(**_SIT)
    w = ease_back(clamp(u / 0.8))
    p = blend(a, b, {"ears": 1, "tail": smooth(u / 0.5), "head": smooth(u / 0.9), "body": w, "legs": smooth(u / 0.7)})
    p["cy"] -= 3.0 * bump((u - 0.62) / 0.5)                 # the rump lands and gives
    p["ear"], p["ear_f"] = 0.74, 0.78
    return _breathe(p, max(0.0, t - settle))


_LIE = dict(cx=0.0, cy=27.0, pitch=0.03, arch=0.04, tail=0.12, curl=0.25,
            fnx=119.0, fny=-1.0, ffx=127.0, ffy=-1.0, hnx=-12.0, hny=1.0, hna=1.45, hfx=-3.0, hfy=1.0, hfa=1.45)


def lie(t=0.0, rest=1.0, settle=1.1):
    """Lies down across a sill: elbows first, then the hips; then (rest=1) the
    chin comes down on the paws. rest=0 keeps the head up and looking. Put the
    sill under the middle of the body (the anchor) for half in, half out."""
    u = t / settle
    a = _base()
    b = _base(**_LIE)
    b["neck"], b["head"] = 0.70, -0.02
    front, back = ease_back(clamp(u / 0.62)), ease_back(clamp((u - 0.28) / 0.72))
    p = blend(a, b, {"ears": smooth(u / 0.2), "tail": smooth(u / 0.9), "head": smooth(u / 0.8), "body": (front + back) / 2, "legs": smooth(u / 0.75)})
    p["pitch"] += -0.26 * (front - back)                     # the front end is down before the back
    r = rest * ease(t, settle + 0.25, settle + 1.05)
    p["neck"] = lerp(p["neck"], -0.47, r)
    p["head"] = lerp(p["head"], -0.02, r)
    p["ear"] = lerp(0.72, 0.42, r) - 0.35 * bump((t - settle - 2.4) / 0.3)
    p["ear_f"] = lerp(0.76, 0.40, r)
    p["eye"] = lerp(1.0, 0.75, r)
    return _breathe(p, max(0.0, t - settle), 0.7)


def wade(t=0.0, depth=0.5, rate=None):
    """Walks down into water: high careful steps, head and tail held up out of
    it, nose leading downhill. depth 0..1 only changes the carriage; the scene
    draws the water over the legs."""
    ph = t * (rate or RATE["wade"])
    p = _gait(_base(), ph, _WALK, 0.6, STRIDE["wade"], 22.0)
    sh, hp = -math.cos(2 * TAU * (ph - 0.35)), -math.cos(2 * TAU * (ph - 0.10))
    p["cy"] += 2.0 * (sh + hp) / 2 - 3
    p["pitch"] = -0.10 + 0.02 * (sh - hp)
    p["neck"] = 0.86 + 0.22 * depth - 0.04 * math.cos(2 * TAU * (ph - 0.47))
    p["head"] = 0.08 + 0.10 * depth
    p["ear"] = 0.9 - 0.3 * bump(((ph * 0.8) % 1 - 0.5) / 0.2)
    p["ear_f"] = 0.95
    p["tail"] = 0.75 + 0.3 * depth
    p["curl"] = 0.5
    p["wag"] = 0.1 * math.sin(TAU * ph)
    return p


def swim(t=0.0, pitch=0.0, rate=None, effort=1.0):
    """Dog paddle. Body-anchored: (x, y) is the middle of the body and the scene
    moves it. pitch < 0 dives nose-down, > 0 climbs. The forepaws pull in
    turn, the hind legs kick, ears and tail stream behind and arrive late."""
    ph = t * (rate or RATE["swim"])
    surge = math.sin(2 * TAU * ph)
    p = _base(cx=0.0, cy=0.0, air=1.0, pitch=pitch + 0.035 * math.sin(TAU * (ph - 0.1)), arch=0.07 * math.sin(2 * TAU * (ph - 0.2)) * effort)
    p["_anchor"] = "body"

    def B(q):
        return _rot(q, pitch)
    for leg, off in (("fn", 0.0), ("ff", 0.5)):
        th = -TAU * (ph - off)
        q = B((70 + 26 * math.cos(th) * effort + (6 if leg == "ff" else 0), -34 + 15 * math.sin(th) * effort))
        p[leg + "x"], p[leg + "y"] = q
        p[leg + "a"] = pitch + 0.35 - 0.55 * math.sin(th)
    for leg, off in (("hn", 0.5), ("hf", 0.0)):
        th = -TAU * (ph - off - 0.08)
        q = B((-80 + 24 * math.cos(th) * effort + (8 if leg == "hf" else 0), -30 + 12 * math.sin(th) * effort))
        p[leg + "x"], p[leg + "y"] = q
        p[leg + "a"] = pitch - 0.85 + 0.35 * math.cos(th)
    p["neck"] = 0.30 - 0.5 * pitch * 0.4 + 0.04 * surge
    p["head"] = 0.04 - 0.25 * pitch + 0.03 * math.sin(2 * TAU * (ph - 0.15))
    p["ear"] = 0.10 + 0.07 * math.sin(2 * TAU * (ph - 0.35))
    p["ear_f"] = 0.06 + 0.07 * math.sin(2 * TAU * (ph - 0.42))
    p["tail"] = 0.05 + 0.06 * math.sin(TAU * (ph - 0.3))
    p["curl"] = 0.10 * math.sin(TAU * (ph - 0.45))
    p["wag"] = 0.30 * math.sin(2 * TAU * (ph - 0.5))
    p["sway"] = -0.5 * pitch
    return p


def swim_down(t=0.0, rate=None, steep=0.72):
    """The crossing down: nose first, to the right and below."""
    p = swim(t, pitch=-steep, rate=rate)
    p["neck"], p["head"] = 0.16, -steep + 0.12
    return p


def swim_up(t=0.0, rate=None, steep=0.85):
    """The crossing up toward the lit surface (draw with facing=-1 to come up to
    the left): neck stretched to the light, eyes wide."""
    p = swim(t, pitch=steep, rate=rate, effort=1.1)
    p["neck"], p["head"], p["eye"] = 0.10, steep * 0.2 + 0.1, 1.15
    return p


def wait_float(t=0.0, pitch=0.25):
    """Holding still under the ice: hardly paddling, looking up."""
    p = swim(t, pitch=pitch, rate=0.33, effort=0.45)
    p["neck"], p["head"] = 0.75, 0.55
    p["ear"], p["ear_f"] = 0.45, 0.5
    return p


def dig(t=0.0, rate=None):
    """Digs in the gravel: chest down, rump up, the forepaws raking in turn.
    Each rake is a fast pull and a slower lifted reach, and the shoulders
    take the jolt. The tail goes up and the ears forward before the first
    stroke. Gravel comes from dig_spray(t)."""
    ph = t * (rate or RATE["dig"])
    bow = ease_back(clamp(t / 0.34))
    go = ease(t, 0.22, 0.5)
    p = _base(cy=lerp(84, 73, bow), pitch=-0.33 * bow, arch=0.14 * bow, cx=lerp(0, -4, bow),
              hnx=-66.0, hfx=-46.0)
    jolt = 0.0
    for leg, off in (("fn", 0.0), ("ff", 0.5)):
        q = (ph - off) % 1.0
        if q < 0.42:                                   # the rake: slow start, hard finish
            s = (q / 0.42) ** 1.9
            fx, fy = lerp(64, 6, s), -1.5 * math.sin(math.pi * s)
            jolt += bump((q - 0.2) / 0.3)
        else:                                          # lift and reach forward again
            s = smooth((q - 0.42) / 0.58)
            fx, fy = lerp(6, 64, s), 21 * math.sin(math.pi * ((q - 0.42) / 0.58) ** 0.7)
        p[leg + "x"] = lerp(_REST[leg], _REST[leg] + fx * go + (1 - go) * 14, bow)
        p[leg + "y"] = fy * go
    p["cy"] -= 3.0 * jolt * go
    p["pitch"] -= 0.035 * jolt * go
    p["cx"] -= 3.0 * jolt * go
    p["neck"] = lerp(0.78, 0.02, bow) + 0.09 * math.sin(2 * TAU * (ph - 0.18)) * go
    p["head"] = lerp(-0.06, -0.62, bow) + 0.08 * math.sin(2 * TAU * (ph - 0.26)) * go
    p["ear"] = lerp(0.72, 1.05, ease(t, 0, 0.14)) - 0.16 * math.sin(2 * TAU * (ph - 0.36)) * go
    p["ear_f"] = lerp(0.72, 1.1, ease(t, 0.03, 0.18)) - 0.16 * math.sin(2 * TAU * (ph - 0.42)) * go
    p["tail"] = lerp(0.15, 1.05, ease(t, 0, 0.2))
    p["curl"] = 0.5
    p["wag"] = 0.42 * math.sin(TAU * 2.3 * t) * ease(t, 0.1, 0.4)
    return p


def nose_page(t=0.0, reach=1.0):
    """Puts its nose to a page on the board. Ears go hard forward first; it
    leans in and sniffs (0.5-1.6 s); then it holds dead still, knowing
    something (1.6-2.4 s); then the ears flick, the head draws back and nods
    and the tail starts: it has decided."""
    lean = ease_back(clamp((t - 0.1) / 0.45))
    sniff = ease(t, 0.5, 0.6) * (1 - ease(t, 1.5, 1.65))
    dec = ease(t, 2.4, 2.75)
    p = _base(cx=7 * lean - 4 * dec, pitch=-0.045 * lean + 0.03 * dec, cy=84 - 1.5 * lean)
    p["neck"] = lerp(0.78, 0.50 + 0.12 * (reach - 1), lean) + 0.10 * dec
    p["head"] = lerp(-0.06, 0.24 * reach, lean) + 0.035 * math.sin(TAU * 5.0 * t) * sniff - 0.26 * bump((t - 2.55) / 0.5)
    p["ear"] = lerp(0.72, 1.18, ease(t, 0.0, 0.14)) - 0.5 * bump((t - 2.34) / 0.22)
    p["ear_f"] = lerp(0.72, 1.22, ease(t, 0.03, 0.18)) - 0.3 * bump((t - 2.40) / 0.22)
    p["tail"] = lerp(0.15, 0.05, lean) + 0.45 * dec
    p["curl"] = 0.3 + 0.2 * dec
    p["wag"] = 0.30 * math.sin(TAU * 1.5 * t) * ease(t, 2.5, 3.0)
    return _breathe(p, t, 0.4 * (1 - sniff))


def take_page(t=0.0):
    """Takes one page gently in the mouth: the head tips, the jaw opens slowly,
    reaches, closes soft (pose['hold'] becomes 1 at 0.95 s: draw the page on
    the board before that, carry='page' after), and draws back carefully."""
    op = ease(t, 0.1, 0.5)
    reach = ease_back(clamp((t - 0.42) / 0.42))
    close = ease(t, 0.86, 1.08)
    back = ease(t, 1.15, 1.75)
    p = _base(cx=7 + 4 * reach - 9 * back, pitch=-0.045 * (1 - back), cy=84 - 1.5 * (1 - back))
    p["neck"] = lerp(0.50, 0.44, reach) + 0.40 * back
    p["head"] = 0.24 - 0.18 * op + 0.10 * back
    p["jaw"] = 0.30 * op - 0.20 * close
    p["hold"] = 1.0 if t >= 0.95 else 0.0
    p["ear"] = 1.1 - 0.3 * back
    p["ear_f"] = 1.15 - 0.3 * back
    p["eye"] = 1.0 - 0.3 * op + 0.3 * back
    p["tail"] = 0.35
    p["wag"] = 0.20 * math.sin(TAU * 1.2 * t) * back
    p["sway"] = 0.5 * bump((t - 1.15) / 0.7)
    return p


_JAW_FOR = {"page": 0.10, "part": 0.25, "reel": 0.33}


def holding(pose, kind="page"):
    """Modifier: opens the jaw just enough for the thing being carried."""
    p = dict(pose)
    p["jaw"] = max(p.get("jaw", 0.0), _JAW_FOR.get(kind, 0.2))
    p["tongue"] = 0.0
    p["hold"] = 1.0
    return p


_GAITS = {}


def carry_part(t=0.0, gait="walk", **kw):
    """Carries a dripping part: it is heavy, so the head rides low and dips with
    each step. gait: 'walk', 'trot', 'stand', 'swim_up', 'swim'. Draw with
    carry='part'."""
    p = _GAITS[gait](t, **kw)
    if p.get("_anchor") != "body":
        p["neck"] -= 0.16
        p["head"] -= 0.05
        p["tail"] += 0.15
    return holding(p, "part")


def carry_reel(t=0.0, gait="trot", **kw):
    """Carries a finished reel: head high, tail high, careful and proud. Draw
    with carry='reel'."""
    p = _GAITS[gait](t, **kw)
    if p.get("_anchor") != "body":
        p["neck"] += 0.12
        p["head"] += 0.08
        p["tail"] += 0.3
        p["ear"] = max(p["ear"], 0.85)
        p["ear_f"] = max(p["ear_f"], 0.9)
    return holding(p, "reel")


def carry_page(t=0.0, gait="walk", **kw):
    """Carries a page without bending it: the head held level and still."""
    p = _GAITS[gait](t, **kw)
    if p.get("_anchor") != "body":
        p["neck"] = lerp(p["neck"], 0.80, 0.7)
        p["head"] = 0.02
    p["sway"] *= 0.5
    return holding(p, "page")


LAND_T = 0.78          # fraction of the burst at which the forefeet touch


def _land_h(u):
    """Height of the body above the ground through the landing of a burst."""
    return lerp(80.0, 61.0, ease(u, LAND_T, LAND_T + 0.09)) + 23.0 * ease_back(clamp((u - LAND_T - 0.07) / (1 - LAND_T - 0.07)))


def burst(t=0.0, dur=1.1):
    """Bursts up through the surface and lands. Body-anchored; move it with
    burst_path(). Stretched and nose-up on the way out, ears pinned by the
    speed, legs gathering over the top, forefeet reaching for the ground, a
    deep landing that the legs absorb, then up to standing height."""
    u = clamp(t / dur)
    pitch = lerp(1.12, 0.25, ease(u, 0.12, 0.5))
    pitch = lerp(pitch, -0.30, ease(u, 0.45, 0.74))
    pitch = lerp(pitch, 0.0, ease_back(clamp((u - LAND_T) / 0.16)))
    p = _base(cx=0.0, cy=0.0, air=1.0 - ease(u, LAND_T - 0.06, LAND_T + 0.02), pitch=pitch,
              arch=lerp(-0.16, 0.20, ease(u, 0.15, 0.55)) * (1 - ease(u, 0.6, 0.85)) + 0.12 * bump((u - LAND_T) / 0.2))
    p["_anchor"] = "body"
    g = ease(u, 0.2, 0.5)
    r = ease(u, 0.5, 0.74)
    onto = ease(u, 0.66, LAND_T)
    h = _land_h(max(u, LAND_T))
    for leg, far in (("fn", 0), ("ff", 1)):
        q = lerp(96, 52, g), lerp(-12, -44, g)
        q = lerp(q[0], 78, r), lerp(q[1], -52, r)
        b = _rot((q[0] + 6 * far, q[1]), pitch)
        gx = _REST[leg] + 14 * (1 - ease(u, LAND_T, 1.0))
        p[leg + "x"], p[leg + "y"] = lerp(b[0], gx, onto), lerp(b[1], -h, onto)
        p[leg + "a"] = lerp(pitch + 0.5, 0.0, onto)
    hind_on = ease(u, LAND_T - 0.02, LAND_T + 0.1)
    for leg, far in (("hn", 0), ("hf", 1)):
        q = lerp(-118, -62, g), lerp(-34, -46, g)
        q = lerp(q[0], -96, r), lerp(q[1], -30, r)
        b = _rot((q[0] + 8 * far, q[1]), pitch)
        gx = _REST[leg] - 8 * (1 - ease(u, LAND_T + 0.05, 1.0))
        p[leg + "x"], p[leg + "y"] = lerp(b[0], gx, hind_on), lerp(b[1], -h, hind_on)
        p[leg + "a"] = lerp(pitch - 0.9, 0.0, hind_on)
    p["neck"] = lerp(0.12, 0.62, ease(u, 0.3, 0.7)) + 0.2 * ease(u, LAND_T + 0.08, 1.0) - 0.25 * bump((u - LAND_T) / 0.2)
    p["head"] = lerp(0.2, -0.05, ease(u, 0.3, 0.7))
    p["ear"] = lerp(0.02, 0.25, ease(u, 0.35, 0.6)) + 0.75 * bump((u - LAND_T + 0.02) / 0.2) + 0.5 * ease(u, 0.9, 1.0)
    p["ear_f"] = lerp(0.0, 0.25, ease(u, 0.38, 0.63)) + 0.75 * bump((u - LAND_T + 0.05) / 0.2) + 0.5 * ease(u, 0.92, 1.0)
    p["tail"] = lerp(-0.25, 0.5, ease(u, 0.3, 0.7)) - 0.6 * bump((u - LAND_T) / 0.22) + 0.0
    p["curl"] = lerp(-0.1, 0.5, ease(u, 0.3, 0.7)) + 0.9 * bump((u - LAND_T + 0.02) / 0.22)
    p["eye"] = 1.15 - 0.9 * bump((u - LAND_T - 0.02) / 0.16)
    p["sway"] = -0.6 * (1 - ease(u, 0.4, 0.9)) + 0.5 * bump((u - LAND_T) / 0.2)
    return p


def burst_path(t, start, land, scale=1.0, height=120.0, dur=1.1):
    """Where the body is during burst(t): from `start` (the point on the surface
    where it breaks through; begin a little below it) on an arc `height` units
    above the higher end, down to standing on the ground point `land`. Draw
    burst() at the returned (x, y); afterwards draw ground poses at `land`."""
    u = clamp(t / dur)
    x0, y0 = start
    x1, y1 = land
    xt = lerp(x0, x1, 0.86)
    yt = y1 - 80.0 * scale
    if u <= LAND_T:
        s = u / LAND_T
        top = min(y0, yt) - height * scale
        va = (math.sqrt(max(0.0, y0 - top)) + 0.0)
        vb = math.sqrt(max(0.0, yt - top))
        sp = va / ((va + vb) or 1.0)                     # time of the top of the arc
        if s < sp:
            k = s / (sp or 1.0)
            yy = y0 + (top - y0) * (1 - (1 - k) ** 2)
        else:
            k = (s - sp) / ((1 - sp) or 1.0)
            yy = top + (yt - top) * k * k
        return (lerp(x0, xt, s ** 0.9), yy)
    k = (u - LAND_T) / (1 - LAND_T)
    return (lerp(xt, x1, smooth(k)), y1 - _land_h(u) * scale)


def shake(t=0.0, dur=1.5):
    """Shakes off water. It braces first (ears flat, head down, feet wide); the
    shake starts at the head and runs down the body to the tail, which is
    still whipping when the head has stopped; one last ear flick. Water comes
    from shake_drops(t)."""
    brace = ease(t, 0.0, 0.22) * (1 - ease(t, dur - 0.35, dur))
    f = 6.5

    def env(delay):
        return ease(t, 0.2 + delay, 0.34 + delay) * (1 - ease(t, dur - 0.62 + delay * 1.6, dur - 0.34 + delay * 1.6))

    def osc(delay):
        return math.sin(TAU * f * (t - 0.2 - delay)) * env(delay)
    p = _base(cy=84 - 6 * brace, cx=-2 * brace, hnx=-56 - 7 * brace, hfx=-45 - 7 * brace, fnx=42 + 6 * brace, ffx=51 + 7 * brace)
    p["twist"] = 0.9 * osc(0.07)
    p["arch"] = 0.05 * brace + 0.10 * osc(0.11)
    p["pitch"] = -0.03 * brace + 0.035 * osc(0.14)
    p["cy"] += 2.2 * osc(0.09)
    p["cx"] += 2.5 * osc(0.12)
    p["neck"] = 0.78 - 0.34 * brace + 0.13 * osc(0.02)
    p["head"] = -0.06 - 0.14 * brace + 0.34 * osc(0.0)
    p["ear"] = lerp(0.72, 0.05, ease(t, 0, 0.12)) + (0.55 + 0.55 * osc(0.03)) * env(0.03) + 0.7 * ease(t, dur - 0.5, dur - 0.3) - 0.5 * bump((t - dur + 0.2) / 0.22)
    p["ear_f"] = lerp(0.72, 0.02, ease(t, 0.02, 0.14)) + (0.55 - 0.55 * osc(0.05)) * env(0.05) + 0.72 * ease(t, dur - 0.45, dur - 0.25)
    p["eye"] = 1.0 - 0.9 * max(env(0.0), 0.6 * brace)
    p["tail"] = 0.15 - 0.35 * brace + 0.45 * osc(0.2)
    p["curl"] = 0.45 + 0.6 * osc(0.24)
    p["wag"] = 0.85 * osc(0.22)
    p["look"] = 0.17 * (1 + osc(0.0)) * env(0.0)          # the head rolls: the cut-out narrows and widens
    p["sway"] = 0.8 * osc(0.03)
    return p


def howl(t=0.0, dur=3.0):
    """Howls once at the waterline. Dips first with the ears going back, then
    the whole front of the dog rises into it: chest out, weight back, muzzle
    to the sky, mouth round. It holds, shaking a little; then down, mouth
    shut, ears pricked, listening for the pack."""
    k = t / dur * 3.0
    ant = bump(k / 0.5)
    up = ease_back(clamp((k - 0.26) / 0.62))
    rel = ease(k, 2.3, 2.85)
    on = up * (1 - rel)
    vib = math.sin(TAU * 6.0 * t) * ease(k, 0.9, 1.2) * (1 - ease(k, 2.1, 2.3))
    p = _base(cx=-5 * on + 2 * ant, cy=84 - 3.5 * ant + 1.5 * on, pitch=0.11 * on - 0.03 * ant, arch=-0.07 * on + 0.05 * ant)
    p["neck"] = 0.78 - 0.26 * ant + 0.50 * on + 0.10 * rel + 0.012 * vib
    p["head"] = -0.06 - 0.16 * ant + 1.18 * on + 0.06 * rel + 0.014 * vib
    p["jaw"] = 0.46 * ease(k, 0.5, 0.95) * (1 - ease(k, 2.2, 2.6)) - 0.10 * ease(k, 1.2, 2.0) * (1 - rel)
    p["ear"] = lerp(0.72, 0.10, ease(k, 0.0, 0.2)) + 0.95 * ease(k, 2.45, 2.7)
    p["ear_f"] = lerp(0.72, 0.06, ease(k, 0.04, 0.26)) + 1.0 * ease(k, 2.5, 2.78)
    p["eye"] = 1.0 - 0.85 * ease(k, 0.5, 0.9) * (1 - ease(k, 2.2, 2.5))
    p["tail"] = lerp(0.15, 0.50, ease(k, 0.05, 0.45)) - 0.15 * rel
    p["curl"] = lerp(0.45, 0.05, ease(k, 0.05, 0.45)) + 0.3 * rel
    p["wag"] = 0.03 * vib
    return p


def ears_down(t=0.0):
    """Told no. The ears fall first, then the tail, then the head; the body
    sags a little. It does not argue: after 1.1 s nothing moves."""
    p = _base()
    e1, e2 = ease(t, 0.0, 0.18), ease(t, 0.05, 0.26)
    tl = ease(t, 0.12, 0.62)
    hd = ease_back(clamp((t - 0.28) / 0.75))
    bd = ease(t, 0.4, 1.1)
    p["ear"], p["ear_f"] = lerp(0.72, 0.03, e1), lerp(0.72, 0.0, e2)
    p["tail"], p["curl"] = lerp(0.15, -0.95, tl), lerp(0.45, -0.25, tl)
    p["neck"], p["head"] = lerp(0.78, 0.20, hd), lerp(-0.06, -0.40, hd)
    p["eye"] = lerp(1.0, 0.62, bd)
    p["cy"], p["arch"], p["cx"] = 84 - 5 * bd, 0.09 * bd, -2 * bd
    return p


def turn_back(t=0.0, down="sit"):
    """Turns its back. Ears flat, the head goes round first, then the whole
    cut-out flips (pose['turn'] 1 -> -1), then it sits (down='sit'), lies with
    its chin down (down='lie') or stays standing (down=None), back to you."""
    e = ease(t, 0.0, 0.16)
    look = ease(t, 0.14, 0.42) * (1 - ease(t, 0.5, 0.78))
    flip = ease(t, 0.45, 0.85)
    p = _base()
    if down == "sit":
        p = blend(p, _base(**_SIT), {"tail": ease(t, 0.9, 1.4), "head": 0, "body": ease_back(clamp((t - 0.9) / 0.7)), "legs": ease(t, 0.9, 1.45), "ears": 0})
        p["cy"] -= 3.0 * bump((t - 1.3) / 0.45)
    elif down == "lie":
        b = _base(**_LIE)
        fr, bk = ease_back(clamp((t - 0.9) / 0.6)), ease_back(clamp((t - 1.15) / 0.7))
        p = blend(p, b, {"tail": ease(t, 0.9, 1.6), "head": 0, "body": (fr + bk) / 2, "legs": ease(t, 0.9, 1.7), "ears": 0})
        p["pitch"] += -0.26 * (fr - bk)
    p["turn"] = 1 - 2 * flip
    p["cy"] -= 6 * bump((t - 0.42) / 0.5)
    p["look"] = look
    settle = ease(t, 1.0, 1.7)
    p["neck"] = lerp(0.78, 0.95, look) * (1 - settle) + settle * (-0.47 if down == "lie" else 0.20)
    p["head"] = lerp(-0.06, {"sit": -0.95, "lie": -0.02}.get(down, -0.30), settle)
    p["ear"], p["ear_f"] = lerp(0.72, 0.06, e), lerp(0.72, 0.02, e)
    p["tail"] = lerp(p["tail"], -0.7, ease(t, 0.05, 0.4) * (1 - settle)) if down else lerp(0.15, -0.7, ease(t, 0.05, 0.4))
    p["eye"] = lerp(1.0, 0.6, settle)
    return p


def over_shoulder(pose, amount=1.0):
    """Modifier: turns the head back over the shoulder on any pose (walking,
    sitting, standing). amount 0..1; at 1 the head is fully round."""
    p = dict(pose)
    a = clamp(amount)
    p["look"] = a
    p["neck"] = lerp(p["neck"], 1.50, smooth(a))
    p["head"] = lerp(p["head"], 0.14, smooth(a))
    return p


def look_back(t=0.0, hold=1.2):
    """Looks back over a shoulder (at the water, when it faces the door). One
    ear turns first, then the head comes round and up; it holds, ears
    pricked at what it sees; then it turns back. hold=None never turns back."""
    a = ease_back(clamp((t - 0.14) / 0.42))
    if hold is not None:
        a *= 1 - ease(t, 0.6 + hold, 1.0 + hold)
    p = over_shoulder(_base(cx=-3 * a, tail=0.15 + 0.1 * a), a)
    p["ear_f"] = lerp(0.72, 0.30, bump(t / 0.34)) + 0.38 * ease(t, 0.5, 0.7)
    p["ear"] = 0.72 + 0.38 * ease(t, 0.55, 0.78)
    return _breathe(p, t, 0.6)


def lay(t=0.0, low=1.0):
    """Lays what it carries on the sill: the head goes down, the jaw opens and
    lets go (pose['hold'] becomes 0 at 0.62 s: draw the thing on the sill
    from then on), and the head comes up to look at you."""
    dn = ease_back(clamp(t / 0.5))
    up = ease(t, 0.8, 1.35)
    p = _base(cx=5 * dn - 6 * up, pitch=-0.07 * dn * (1 - up), cy=84 - 5 * dn * (1 - up))
    p["neck"] = lerp(0.78, 0.78 - 1.2 * low, dn * (1 - up)) + 0.14 * up
    p["head"] = lerp(-0.06, -0.06 - 0.46 * low, dn * (1 - up))
    p["jaw"] = 0.25 + 0.2 * ease(t, 0.48, 0.66) - 0.45 * ease(t, 0.9, 1.2)
    p["hold"] = 1.0 if t < 0.62 else 0.0
    p["ear"], p["ear_f"] = 0.75 + 0.3 * up, 0.8 + 0.3 * up
    p["tail"] = 0.3 + 0.25 * up
    p["wag"] = 0.3 * math.sin(TAU * 2.2 * t) * up
    return p


def pleased(t=0.0):
    """Pleased with what it brought: head high, ears up, mouth open, the tail
    going hard enough to move the hips, and the forefeet treading."""
    w = math.sin(TAU * 3.0 * t)
    p = _base(cx=-2.0, cy=84 + 0.8 * math.sin(TAU * 6.0 * t), pitch=0.03, arch=-0.03)
    p["neck"], p["head"] = 0.98, 0.06
    p["jaw"], p["tongue"] = 0.24, 0.55
    p["ear"], p["ear_f"] = 1.0 + 0.04 * w, 1.04 - 0.04 * w
    p["tail"], p["curl"], p["wag"] = 0.85, 0.55, 0.62 * w
    p["twist"] = 0.22 * math.sin(TAU * 3.0 * (t - 0.06))
    for leg, off in (("fn", 0.0), ("ff", 0.5)):
        p[leg + "y"] = 7.0 * bump(((t * 1.5 - off) % 1.0) / 0.5)
    return p


def paw_press(t=0.0):
    """Sets a paw on a thing to mark it: lifts the near forepaw, presses it
    down ahead of itself with its weight behind it (0.45 s), holds, and takes
    it back."""
    lift = bump(t / 0.5)
    down = ease(t, 0.3, 0.46) * (1 - ease(t, 1.1, 1.4))
    p = _base(cx=5 * down, pitch=-0.05 * down, cy=84 - 2.5 * down)
    p["fnx"] = 42 + 30 * ease(t, 0.1, 0.42) * (1 - ease(t, 1.1, 1.5))
    p["fny"] = 26 * lift + 12 * bump((t - 1.05) / 0.5)
    p["neck"], p["head"] = 0.78 - 0.5 * down, -0.06 - 0.5 * down
    p["ear"], p["ear_f"] = 0.95, 1.0
    p["tail"] = 0.35
    return p


def tired(t=0.0):
    """Worn out at the waterline: legs apart, head hanging, panting, tongue out,
    ribs working. The tail does nothing."""
    pant = math.sin(TAU * 2.8 * t)
    p = _base(cy=79.0 + 0.6 * pant, arch=0.07 + 0.022 * pant, pitch=-0.03, fnx=46.0, ffx=57.0, hnx=-60.0, hfx=-47.0)
    p["neck"], p["head"] = 0.24 + 0.015 * pant, -0.30
    p["jaw"], p["tongue"] = 0.27 + 0.06 * pant, 0.9
    p["ear"], p["ear_f"] = 0.30, 0.26
    p["eye"] = 0.7
    p["tail"], p["curl"] = -0.65, -0.1
    return p


_GAITS.update({"walk": walk, "trot": trot, "wade": wade, "stand": stand, "swim": swim,
               "swim_up": swim_up, "swim_down": swim_down, "sit": sit, "watch": watch})

PERFORMANCES = {
    "stand": stand, "watch": watch, "back_away": back_away, "sit": sit, "lie": lie, "walk": walk,
    "trot": trot, "wade": wade, "swim": swim, "swim_down": swim_down, "swim_up": swim_up,
    "wait_float": wait_float, "dig": dig, "nose_page": nose_page, "take_page": take_page,
    "carry_page": carry_page, "carry_part": carry_part, "carry_reel": carry_reel, "burst": burst,
    "shake": shake, "howl": howl, "ears_down": ears_down, "turn_back": turn_back,
    "look_back": look_back, "lay": lay, "pleased": pleased, "paw_press": paw_press, "tired": tired,
}
# natural length in seconds of the one-shots (cycles and holds have none)
DURATION = {"sit": 1.0, "lie": 2.2, "nose_page": 3.0, "take_page": 1.8, "burst": 1.1, "shake": 1.5,
            "howl": 3.0, "ears_down": 1.1, "turn_back": 1.8, "look_back": 2.2, "lay": 1.4, "paw_press": 1.5}


def perform(name, t=0.0, **kw):
    """Pose of the named performance at t seconds."""
    return PERFORMANCES[name](t, **kw)


def travel(name, t, rate=None):
    """How far (dog units, along the way it faces; negative is backward) a gait
    has gone after t seconds, so feet do not slide: x = x0 + facing * scale *
    travel(name, t)."""
    return STRIDE[name] * (rate or RATE[name]) * t


class Score:
    """A stateless timeline of performances: Score([(time, name, {options}), ...]).
    pose(t) can be asked for any t in any order. At each cue the ears move
    first (0.22 s early), then the tail, then the head, then the body with a
    little anticipation and overshoot; the feet go last and plainly.
    options may hold 'blend' (seconds for the body to change, default 0.5)
    besides the performance's own arguments."""

    LEAD = {"ears": (-0.22, 0.16), "tail": (-0.15, 0.34), "head": (-0.07, None), "body": (0.0, None), "legs": (0.0, None)}

    def __init__(self, cues):
        self.cues = []
        for c in sorted(cues, key=lambda c: c[0]):
            kw = dict(c[2]) if len(c) > 2 else {}
            self.cues.append((float(c[0]), c[1], kw.pop("blend", 0.5), kw))

    def cue_at(self, t):
        """(name, seconds since it began) of the performance in charge at t."""
        cur = self.cues[0]
        for c in self.cues:
            if c[0] <= t:
                cur = c
        return cur[1], max(0.0, t - cur[0])

    def pose(self, t):
        T0, name, _, kw = self.cues[0]
        out = PERFORMANCES[name](max(0.0, t - T0), **kw)
        for T, name, D, kw in self.cues[1:]:
            if t < T - 0.25:
                break
            nxt = PERFORMANCES[name](max(0.0, t - T), **kw)
            w = {}
            for g, (lead, dur) in self.LEAD.items():
                d = dur if dur is not None else (D * 0.7 if g == "head" else D)
                x = (t - (T + lead)) / max(d, 1e-3)
                w[g] = smooth(x) if g in ("ears", "legs", "tail") else clamp(ease_back(x), -0.1, 1.08)
            out = blend(out, nxt, w)
        out["turn"] = clamp(out["turn"], -1.0, 1.0)
        return out

    def draw(self, target, t, x, y, **kw):
        return draw_dog(target, self.pose(t), x, y, **kw)


# ---------------------------------------------------------------- particles ---
def shake_drops(t, n=54, seed=3, dur=1.5):
    """Water flung off by shake(t): [(x, y, r, alpha)] in dog units, y up, from
    the dog's ground anchor. Draw with draw_bits()."""
    out = []
    for i in range(n):
        b = 0.24 + _hash(seed + i * 3.1) * (dur - 0.75)
        age = t - b
        if age < 0 or age > 0.75:
            continue
        ox, oy = lerp(-70, 100, _hash(seed + i * 5.3)), lerp(62, 108, _hash(seed + i * 7.7))
        ang = lerp(0.15, math.pi - 0.15, _hash(seed + i * 9.1))
        sp = lerp(120, 300, _hash(seed + i * 11.3))
        x = ox + math.cos(ang) * sp * age
        y = oy + math.sin(ang) * sp * age - 0.5 * 560 * age * age
        if y < 0:
            continue
        out.append((x, y, lerp(1.6, 3.4, _hash(seed + i * 13.7)), 1 - age / 0.75))
    return out


def dig_spray(t, rate=None, seed=5, water=False):
    """Gravel thrown back between the hind legs by dig(t): [(x, y, r, alpha)].
    water=True makes it slow and floaty, for the creek bed."""
    rate = rate or RATE["dig"]
    out = []
    g, sp, life = (150.0, 0.55, 1.1) if water else (620.0, 1.0, 0.6)
    k0 = int((t - life) * rate * 2) - 1
    for k in range(max(0, k0), int(t * rate * 2) + 1):
        tb = (k + 0.42) / (rate * 2)
        if tb < 0.45:
            continue
        for j in range(8):
            age = t - tb - 0.02 * j
            if age < 0 or age > life:
                continue
            h = seed + k * 17.3 + j * 3.9
            vx, vy = -lerp(120, 330, _hash(h)) * sp, lerp(90, 300, _hash(h + 1)) * sp
            x = 52 + vx * age * (1 - 0.3 * age / life if water else 1)
            y = 2 + vy * age - 0.5 * g * age * age
            if y < 0:
                continue
            out.append((x, y, lerp(2.2, 5.0, _hash(h + 2)), 1 - (age / life) ** 2))
    return out


def draw_bits(target, bits, x, y, scale=1.0, facing=1, color=(206, 232, 240)):
    """Draw particles from shake_drops() or dig_spray() around a dog at (x, y)."""
    img = _img_of(target)
    d = ImageDraw.Draw(img, "RGBA")
    for bx, by, r, a in bits:
        px, py, rr = x + facing * scale * bx, y - scale * by, max(0.8, r * scale)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=tuple(color[:3]) + (int(235 * clamp(a)),))
    _refresh(target)


# ------------------------------------------------------- the decision machine ---
class DogMind:
    """The dog's decision machine, ported from paeleo/threshold/machine.js.

    Nobody moves the dog. You change circumstances (the person's posture and
    place, the door, the voice, the hand) and the dog reads them through what
    it perceives, what it trusts and what it remembers. Five states: watch,
    approach, retreat, lie_down, refuse.

    The world is a side view in metres: the sill is x = 0, the porch runs to
    +x, the person is at the door. In this film the door is on the LEFT and the
    water on the right, so a dog that faces the person is drawn facing=-1.

        m = DogMind()
        m.set(voice="call", hand="reach")
        m.step(1 / 24)                 # once per frame
        m.state, m.x, m.trust, m.pressure, m.face
    """

    STATES = ("watch", "approach", "retreat", "lie_down", "refuse")
    SILL = 0.56
    PORCH_END = 4.9
    PERSON_X = {"doorway": -0.28, "beside": -1.25}
    DWELL = {"watch": 1.0, "approach": 0.7, "retreat": 1.1, "lie_down": 2.2, "refuse": 3.5}
    WORLD = {"posture": "stand", "place": "doorway", "door": "ajar", "voice": "none", "hand": "none"}
    OPTIONS = {"posture": ("stand", "sit"), "place": ("doorway", "beside"), "door": ("ajar", "open"),
               "voice": ("call", "soft", "none"), "hand": ("none", "low", "reach")}
    PERFORM = {"watch": "watch", "approach": "walk", "retreat": "back_away", "lie_down": "lie", "refuse": "turn_back"}

    def __init__(self, **over):
        self.t, self.state, self.since = 0.0, "watch", 0.0
        self.x, self.v, self.face = 3.0, 0.0, 1
        self.trust, self.pressure = 0.2, 0.0
        self.calls, self.refusals = 0, 0
        self.last_voice, self.heard = "none", -99.0
        self.threat, self.invite, self.settle = 0.0, 0.0, 0.0
        self.reason = "starts on the porch, watching"
        self.events = []
        self.world = dict(self.WORLD)
        for k, v in over.items():
            setattr(self, k, v)

    def set(self, **circumstances):
        """Change the circumstances, e.g. set(posture='sit', voice='soft')."""
        for k, v in circumstances.items():
            if k not in self.OPTIONS or v not in self.OPTIONS[k]:
                raise ValueError(f"{k}={v!r}: choose from {self.OPTIONS.get(k)}")
        self.world.update(circumstances)
        self.events.append({"t": round(self.t, 3), "e": "world", "set": dict(circumstances)})
        return self

    def perceive(self):
        """How much the scene presses on the dog, and how much it invites."""
        w = self.world
        px = self.PERSON_X[w["place"]]
        dist = max(0.0, self.x - px)
        near = 1 + 1.3 * clamp((2.6 - dist) / 2.6)
        blocking = w["place"] == "doorway" and w["posture"] == "stand"
        threat = ((0.55 if w["hand"] == "reach" else 0) + (0.42 if w["voice"] == "call" else 0) + (0.22 if blocking else 0)
                  + (0.08 if (w["place"] == "doorway" and w["posture"] == "sit") else 0))
        threat = clamp(threat * near + self.pressure * 0.35)
        invite = clamp((0.25 if w["voice"] == "soft" else 0) + (0.35 if w["hand"] == "low" else 0) + (0.3 if w["posture"] == "sit" else 0)
                       + (0.15 if w["door"] == "open" else 0) + (0.15 if w["place"] == "beside" else 0) - (0.3 if w["voice"] == "call" else 0))
        return {"px": px, "dist": dist, "threat": threat, "invite": invite, "blocking": blocking,
                "clear": w["place"] == "beside" or w["posture"] == "sit"}

    def decide(self, p):
        """Guards in priority order; the first that holds, and may be entered now, wins."""
        S = self.state
        dwelt = self.t - self.since >= self.DWELL[S]
        G = []
        end = self.PORCH_END - 0.05
        if S == "refuse":
            if dwelt and self.pressure < 0.2 and p["invite"] > 0.5 and p["threat"] < 0.25:
                G.append(("watch", "pressure gone and invited: turns back to look"))
            else:
                G.append(("refuse", "keeps its back turned"))
        elif self.pressure > 0.62:
            G.append(("refuse", f"pressure {self.pressure:.2f} after {self.calls} calls: turns its back"))
        elif p["threat"] > 0.55 and ((S != "retreat" and p["dist"] >= 3.6) or self.x >= end):
            G.append(("refuse", f"threat {p['threat']:.2f} and already {p['dist']:.1f} m away: turns its back"))
        if S != "refuse":
            if p["threat"] > 0.55 and p["dist"] < 3.6 and self.x < end:
                G.append(("retreat", f"threat {p['threat']:.2f} at {p['dist']:.1f} m: backs away"))
            if (S == "approach" or (self.trust > 0.6 and p["threat"] < 0.3)) and S != "lie_down" and abs(self.x - self.SILL) < 0.03:
                G.append(("lie_down", "reached the sill: lies down there, half in and half out"))
            if S == "lie_down" and p["threat"] > 0.45:
                G.append(("watch", f"threat {p['threat']:.2f} while lying: gets up"))
            if self.trust > 0.6 and p["threat"] < 0.3 and p["clear"] and self.x > self.SILL + 0.03:
                G.append(("approach", f"trust {self.trust:.2f}, threat {p['threat']:.2f}, the way is clear: comes closer"))
            if S == "lie_down":
                G.append(("lie_down", "stays down"))
            if S == "approach" and (p["threat"] >= 0.3 or self.trust < 0.5):
                G.append(("watch", f"threat {p['threat']:.2f} on the way: stops to look"))
            if S == "approach":
                G.append(("approach", "keeps coming"))
            if S == "retreat" and p["threat"] > 0.35 and self.x < end:
                G.append(("retreat", "keeps backing"))
            if self.settle > 6:
                G.append(("lie_down", "nothing asked of it for a while: settles where it is"))
            G.append(("watch", "watches"))
        for to, why in G:
            if to == S:
                return S, why
            if dwelt or to in ("retreat", "refuse"):       # danger interrupts; the rest wait their window
                return to, why
        return S, "holds"

    def step(self, dt=1 / 24):
        w = self.world
        if w["voice"] == "call" and self.last_voice != "call":
            self.calls += 1
            self.pressure = clamp(self.pressure + (0.5 if self.state in ("retreat", "refuse") else 0.3))
            self.events.append({"t": round(self.t, 3), "e": "call", "n": self.calls})
        if w["voice"] != "none" and self.last_voice == "none":
            self.heard = self.t
        self.last_voice = w["voice"]
        if w["hand"] == "reach" and self.state != "refuse":
            self.pressure = clamp(self.pressure + 0.12 * dt)
        self.pressure = clamp(self.pressure - (0.02 if w["voice"] == "call" else 0.09) * dt)
        p = self.perceive()
        self.threat, self.invite = p["threat"], p["invite"]
        gain, loss = 0.16 / (1 + 0.6 * self.refusals), 0.28      # a dog that has refused warms more slowly
        self.trust = clamp(self.trust + dt * (gain * p["invite"] * (1 - self.trust) * (1 if p["threat"] < 0.3 else 0.2) - loss * p["threat"] * self.trust))
        self.settle = self.settle + dt if (p["threat"] < 0.15 and w["voice"] == "none" and w["hand"] == "none") else 0.0
        nxt, why = self.decide(p)
        if nxt != self.state:
            self.events.append({"t": round(self.t, 3), "e": "transition", "from": self.state, "to": nxt, "why": why,
                                "trust": round(self.trust, 3), "threat": round(p["threat"], 3), "x": round(self.x, 3)})
            if nxt == "refuse":
                self.refusals += 1
            self.state, self.since = nxt, self.t
        self.reason = why
        target, face = 0.0, self.face
        if self.state == "approach":
            sp = 0.25 + 0.55 * clamp((self.trust - 0.6) / 0.4)
            target, face = -min(sp, max(0.06, (self.x - self.SILL) * 1.6)), 1
        if self.state == "retreat":
            target, face = min(0.75, (self.PORCH_END - self.x) * 1.6), 1    # backs away still facing the person
        if self.state == "refuse":
            face = -1                                                       # the refusal is visible: its back
        if self.state in ("watch", "lie_down"):
            face = 1
        self.v += clamp(target - self.v, -2.2 * dt, 2.2 * dt)                # no teleporting, no instant stops
        self.x += self.v * dt
        if self.x < self.SILL:
            self.x, self.v = self.SILL, max(0.0, self.v)
        if self.x > self.PORCH_END:
            self.x, self.v = self.PORCH_END, min(0.0, self.v)
        self.face = face
        self.t += dt
        return self

    def frame(self):
        """A snapshot of the dog now."""
        return {"t": round(self.t, 4), "state": self.state, "since": self.t - self.since, "x": self.x, "v": self.v,
                "face": self.face, "trust": self.trust, "threat": self.threat, "invite": self.invite,
                "pressure": self.pressure, "heard": self.t - self.heard, "world": dict(self.world)}

    @classmethod
    def run(cls, timeline, T, dt=1 / 24, **init):
        """Run a list of circumstance changes [(t, {posture: 'sit', ...}), ...]
        for T seconds. Returns (frames, events): one frame() per step."""
        m = cls(**init)
        frames, k = [], 0
        timeline = sorted(timeline, key=lambda c: c[0])
        for _ in range(int(T / dt) + 1):
            while k < len(timeline) and timeline[k][0] <= m.t + 1e-9:
                m.set(**timeline[k][1])
                k += 1
            m.step(dt)
            frames.append(m.frame())
        return frames, m.events

    @staticmethod
    def cues(frames):
        """Turn a run into Score cues: [(t, performance), ...], one per change of state."""
        out, last = [], None
        for f in frames:
            if f["state"] != last:
                out.append((f["t"], DogMind.PERFORM[f["state"]]))
                last = f["state"]
        return out

    @staticmethod
    def pose(f, anim_t=None):
        """Pose for one frame() of a run: the state's performance at the time
        since the state began; walking speed follows the distance covered."""
        s, since = f["state"], f["since"]
        if s == "approach":
            return walk(phase=-f["x"] * 100.0 / STRIDE["walk"])     # 1 m = 100 dog units; feet follow the ground
        if s == "retreat":
            return blend(watch(since), back_away(since), {g: ease(since, 0, 0.3) for g in GROUPS})
        return PERFORMANCES[DogMind.PERFORM[s]](since)


# -------------------------------------------------------------- self-test ---
def _bg(w, h, kind):
    img = Image.new("RGB", (w, h))
    px = np.zeros((h, w, 3), np.float32)
    top, bot = ((58, 48, 98), (232, 150, 108)) if kind == "dusk" else ((38, 132, 138), (14, 60, 78))
    for c in range(3):
        px[..., c] = np.linspace(top[c], bot[c], h)[:, None]
    return Image.fromarray(px.astype(np.uint8))


def _strip(name, fn, times, cell=(230, 190), kind="dusk", ground=150, carry=None, bits=None, facing=1, scale=0.8, travel_px=None, bitcol=(206, 232, 240)):
    n = len(times)
    out = Image.new("RGB", (cell[0] * n, cell[1] * 2), (0, 0, 0))
    for row, sil in enumerate((False, True)):
        for i, t in enumerate(times):
            c = _bg(cell[0], cell[1], kind) if not sil else Image.new("RGB", cell, (236, 228, 212))
            d = ImageDraw.Draw(c)
            pose = fn(t)
            body = pose.get("_anchor") == "body"
            gx, gy = cell[0] // 2 - int(10 * facing), ground if not body else cell[1] // 2
            if not body:
                d.line([(0, ground), (cell[0], ground)], fill=(60, 40, 60) if not sil else (150, 140, 130), width=2)
                if travel_px:                       # ground ticks that should stay under planted feet
                    off = (travel_px(t) * scale) % 40
                    for k in range(-1, 8):
                        xx = k * 40 - off * facing
                        d.line([(xx, ground), (xx, ground + 7)], fill=(250, 240, 200) if not sil else (120, 110, 100), width=2)
            draw_dog(c, pose, gx, gy, scale=scale, facing=facing, silhouette=sil, carry=carry)
            if bits:
                draw_bits(c, bits(t), gx, gy, scale=scale, facing=facing, color=bitcol if not sil else (20, 17, 26))
            out.paste(c, (i * cell[0], row * cell[1]))
    path = HERE / f"dog_strip_{name}.png"
    out.save(path)
    return path


def _sheet():
    shots = [
        ("watch", watch(0.5), None, "dusk"), ("back_away", back_away(0.9), None, "dusk"), ("sit", sit(2.0), None, "dusk"),
        ("lie (chin down)", lie(4.0), None, "dusk"), ("lie rest=0", lie(4.0, rest=0), None, "dusk"), ("walk", walk(0.3), None, "dusk"),
        ("trot", trot(0.12), None, "dusk"), ("wade", wade(0.45, depth=0.8), None, "dusk"), ("swim_down", swim_down(0.2), None, "water"),
        ("swim_up + page", holding(swim_up(0.3), "page"), "page", "water"), ("dig", dig(0.98), None, "water"), ("nose_page", nose_page(1.9), None, "water"),
        ("take_page", take_page(1.0), "page", "water"), ("carry_part", carry_part(0.3), "part", "dusk"), ("carry_reel", carry_reel(0.12), "reel", "dusk"),
        ("burst (out)", burst(0.25), "page", "dusk"), ("burst (land)", burst(0.93), "page", "dusk"), ("shake", shake(0.62), None, "dusk"),
        ("howl", howl(1.4), None, "dusk"), ("ears_down", ears_down(1.5), None, "dusk"), ("turn_back", turn_back(2.2), None, "dusk"),
        ("look_back", look_back(0.9), None, "dusk"), ("lay", lay(0.5), "reel", "dusk"), ("pleased", pleased(0.25), None, "dusk"),
        ("paw_press", paw_press(0.7), None, "dusk"), ("tired", tired(0.2), None, "dusk"), ("wait_float", wait_float(0.4), None, "water"),
        ("turn_back lie", turn_back(2.6, down="lie"), None, "dusk"),
    ]
    cols, cw, ch = 7, 250, 190
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch * 2), (30, 26, 34))
    for k, (name, pose, carry, kind) in enumerate(shots):
        for r, sil in enumerate((False, True)):
            c = _bg(cw, ch, kind) if not sil else Image.new("RGB", (cw, ch), (236, 228, 212))
            d = ImageDraw.Draw(c)
            body = pose.get("_anchor") == "body"
            gy = 158 if not body else 100
            if not body:
                d.line([(0, 158), (cw, 158)], fill=(60, 40, 60) if not sil else (150, 140, 130), width=2)
            draw_dog(c, pose, cw // 2 - 14, gy, scale=0.78, silhouette=sil, carry=carry)
            d = ImageDraw.Draw(c)
            d.text((6, 4), name, fill=(255, 255, 255) if not sil else (60, 50, 40))
            sheet.paste(c, ((k % cols) * cw, (k // cols) * ch * 2 + r * ch))
    path = HERE / "dog_sheet.png"
    sheet.save(path)
    return path


def _selftest():
    # the machine: the person presses, then sits and waits; the dog must retreat, then be earned
    frames, events = DogMind.run([(1.0, {"voice": "call", "hand": "reach"}), (5.0, {"voice": "none", "hand": "none", "posture": "sit"}),
                                  (8.0, {"voice": "soft", "hand": "low", "door": "open"})], 60)
    states = [e["to"] for e in events if e["e"] == "transition"]
    assert "retreat" in states and "approach" in states and states[-1] == "lie_down", states
    obedient, _ = DogMind.run([(1.0, {"voice": "call", "hand": "reach"})], 40)
    assert all(f["state"] != "approach" for f in obedient), "a dog that is called and grabbed must never approach"
    # joints: bones keep their length and no joint folds past its limit, in every performance
    worst = 0.0
    for name, fn in PERFORMANCES.items():
        for i in range(60):
            J = solve(fn(i * 0.07))["joints"]
            for a, b, c, l1, l2 in (("shoulder", "fn.elbow", "fn.wrist", "arm", "forearm"), ("hip", "hn.knee", "hn.hock", "thigh", "shank")):
                d1 = math.hypot(J[b][0] - J[a][0], J[b][1] - J[a][1])
                d2 = math.hypot(J[c][0] - J[b][0], J[c][1] - J[b][1])
                worst = max(worst, abs(d1 - BUILD[l1]), abs(d2 - BUILD[l2]))
    assert worst < 1e-6, worst
    # feet: a planted walking foot stays put on the ground while the body travels
    slip = 0.0
    for leg in LEGS:
        prev = None
        for i in range(200):
            t = i / 96
            p = walk(t)
            if p[leg + "y"] < 1e-6:
                wx = p[leg + "x"] + travel("walk", t)
                if prev is not None and abs(t - prev[0]) < 0.011:
                    slip = max(slip, abs(wx - prev[1]))
                prev = (t, wx)
    assert slip < 0.01, slip
    return {"machine": states, "bone_error": worst, "walk_foot_slip": slip}


if __name__ == "__main__":
    print("selftest:", _selftest())
    print(_sheet())
    print(_strip("walk", walk, [i / 8 / RATE["walk"] for i in range(8)], travel_px=lambda t: travel("walk", t)))
    print(_strip("trot", trot, [i / 8 / RATE["trot"] for i in range(8)], travel_px=lambda t: travel("trot", t)))
    print(_strip("dig", dig, [0.0, 0.12, 0.3, 1.0, 1.06, 1.12, 1.18, 1.24, 1.30], bits=lambda t: dig_spray(t), kind="water", bitcol=(150, 132, 110)))
    print(_strip("swim", lambda t: swim_down(t) if t < 10 else swim_up(t - 10), [0, 0.1, 0.2, 0.3, 0.4, 10.0, 10.15, 10.3, 10.45], kind="water", scale=0.7))
    print(_strip("shake", shake, [0.0, 0.14, 0.3, 0.38, 0.46, 0.54, 0.8, 1.1, 1.3, 1.5], bits=lambda t: shake_drops(t)))
    print(_strip("howl", howl, [0.0, 0.3, 0.55, 0.9, 1.6, 2.5, 3.0]))
    print(_strip("burst", burst, [0.0, 0.2, 0.4, 0.6, 0.78, 0.86, 0.95, 1.1], scale=0.6, cell=(230, 220)))
    print(_strip("no", lambda t: ears_down(t) if t < 5 else turn_back(t - 5), [0.0, 0.2, 0.5, 1.2, 5.3, 5.6, 5.75, 6.2, 7.0]))
    print(_strip("sitlie", lambda t: sit(t) if t < 5 else lie(t - 5), [0.0, 0.4, 0.7, 1.2, 5.3, 5.6, 5.9, 6.4, 8.0], scale=0.7))
