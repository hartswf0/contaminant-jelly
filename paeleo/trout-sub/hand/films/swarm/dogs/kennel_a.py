"""KENNEL A: three pack dogs for THE DOGS OF TROUTTOWN, each made a different way.

    import kennel_a as ka
    ka.herding_dog(ink, x, y, s=1.0, facing=1, action="circle", t=t)
    ka.digger(ink, x, y, s=1.0, facing=-1, action="dig", t=t)
    ka.old_dog(ink, x, y, s=1.0, facing=1, action="turn_back", p=0.4)

1. herding_dog  a black articulated SHADOW PUPPET (scion/animation-02.md): flat cut
                pieces pinned at joints, joint-angle limits, a cut-out eye you can see
                through, exposed on twos (12 poses a second). No inner drawing at all.
2. digger       a CONSTRAINT-DRAWN WIRE DOG (scion/animation-08.md): points and lines.
                Each action only states relationships (these paws are planted here, the
                nose is dragged there, the rump is wanted about here) and a relaxation
                solver finds the body. Bone lengths are checked every frame.
3. old_dog      an ENGRAVED PRINT, CUT OUT AND HINGED (scion/animation-50.md and -01.md):
                Thomas Bewick's Newfoundland dog (wood engraving, public domain, foraged
                from Wikimedia Commons; credit in films/credits/dogs.json), cut with
                scissors into head, body, tail and four legs and pinned back together.
                At rest the pieces reassemble the print exactly.

Shared calling convention
    ink     a kit.Ink (or a PIL image). Drawing lands on ink.img.
    x, y    SCREEN position of the ground point under the middle of the dog (between the
            fore and hind feet). For action="swim" it is the middle of the belly instead.
    s       size. s=1: herder about 95 px long, digger about 95 px, old dog about 185 px
            long standing and 210 px lying with its tail laid out (the largest dog).
    facing  +1 nose to the right, -1 nose to the left.
    action  a name from HERDER_ACTIONS / DIGGER_ACTIONS / OLD_DOG_ACTIONS.
    t       seconds, drives cycles (walk, swim, dig, circle).
    p       0..1, drives one-shot actions (gather, heave, build, turn_back, ...).
    look    degrees the head is raised above its normal carriage (ice beat: look=45).
Every function returns a dict of SCREEN anchors: "mouth", "nose", "head", "eye", "tail",
"back", "bbox" and action-specific ones, so a prop can be put in the mouth by its owner.

Nothing here is red or cream (those belong to the lead dog) and nothing is lettered.

Run:  python3 films/swarm/dogs/kennel_a.py            sheets of every dog in every action
      python3 films/swarm/dogs/kennel_a.py --check    numeric invariants
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
_FILMS = _HERE.parent.parent
if str(_FILMS) not in sys.path:
    sys.path.insert(0, str(_FILMS))

from kit import clamp, lerp, smooth, ramp   # noqa: E402

SS = 3   # supersampling for the cut edge and the wire


# ------------------------------------------------------------------ shared ---

def _img(target):
    return target.img if hasattr(target, "img") else target


def _stamp(target, layer, ox, oy):
    """Composite an RGBA layer onto an Ink (RGB or RGBA) or a PIL image."""
    img = _img(target)
    ox, oy = int(round(ox)), int(round(oy))
    if img.mode == "RGBA":
        box = (max(0, ox), max(0, oy), min(img.width, ox + layer.width), min(img.height, oy + layer.height))
        if box[2] <= box[0] or box[3] <= box[1]:
            return
        part = layer.crop((box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy))
        img.paste(Image.alpha_composite(img.crop(box), part), box[:2])
    else:
        img.paste(layer, (ox, oy), layer)
    if hasattr(target, "d"):
        target.d = ImageDraw.Draw(img, "RGBA")


def _rot(p, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _dirv(deg):
    a = math.radians(deg)
    return (math.cos(a), math.sin(a))


def _hash(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def _gait_foot(phase, offset, duty, stride, lift, x0):
    """Foot target on the ground: planted and sliding back for `duty` of the cycle,
    then lifted and carried forward."""
    u = (phase + offset) % 1.0
    if u < duty:
        return (x0 + stride * (0.5 - u / duty), 0.0)
    v = (u - duty) / (1 - duty)
    return (x0 + stride * (-0.5 + smooth(v)), -lift * math.sin(math.pi * v))


def _ik2(root, target, l1, l2, bend):
    """Two pinned pieces from root to target. Returns (angle1, angle2, joint, end) in
    degrees (0 = forward, 90 = down). bend=+1 puts the joint to the rear."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    d = clamp(d, abs(l1 - l2) + 0.5, l1 + l2 - 0.02)
    a = math.atan2(dy, dx)
    ca = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    a1 = a + bend * math.acos(ca)
    joint = (root[0] + l1 * math.cos(a1), root[1] + l1 * math.sin(a1))
    end = (root[0] + d * math.cos(a), root[1] + d * math.sin(a))
    a2 = math.atan2(end[1] - joint[1], end[0] - joint[0])
    return math.degrees(a1), math.degrees(a2), joint, end


def _fringe(a, b, n, depth):
    """Scissor-cut fur between a and b: n teeth pointing to the right of a->b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = dy / L, -dx / L
    out = []
    for k in range(n):
        f0, f1 = (k + 0.25) / n, (k + 0.8) / n
        out.append((a[0] + dx * f0, a[1] + dy * f0))
        out.append((a[0] + dx * f1 - nx * depth, a[1] + dy * f1 - ny * depth))
    return out


# =============================================================================
# 1 · THE HERDING DOG · black articulated shadow puppet
# =============================================================================

HERDER_ACTIONS = ("wait", "walk", "circle", "gather", "carry", "swim", "turn", "slide",
                  "flank", "creep", "eye", "down")      # the last four are for the cows

# Joint-angle limits in degrees (a pinned card joint cannot go further than its
# neighbours allow). Relative to the parent piece.
HERDER_LIMITS = {
    "neck": (-95, 30),     # neck relative to torso
    "head": (-40, 125),    # head relative to neck
    "jaw": (0, 30),
    "ear": (-80, 35),
    "tail1": (95, 260),    # relative to torso
    "tail2": (-45, 60),    # relative to tail1
}
HERDER_FPS = 12            # exposed on twos, as on the glass table

# Cut pieces. Each is drawn in its own frame: origin at its pin, +x along the piece.
def _round(poly, n=2):
    """Scissors do not cut corners: Chaikin's corner cutting on a closed outline."""
    for _ in range(n):
        out = []
        for k in range(len(poly)):
            a, b = poly[k], poly[(k + 1) % len(poly)]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        poly = out
    return poly


_H_TORSO = _round([(-12, -2), (-9, -11), (0, -15), (14, -15.5), (30, -14), (44, -16), (56, -15), (62, -9)]
                  + _fringe((62, -9), (57, 13), 3, -3.6)
                  + [(57, 13), (47, 17)]
                  + _fringe((47, 17), (14, 10), 4, -2.8)
                  + [(14, 10), (4, 11)]
                  + _fringe((4, 11), (-11, 4), 2, -2.6)
                  + [(-11, 4)], 1)
_H_PINS = {"hip": (0, 3), "hip_far": (4, 3), "sh": (50, 6), "sh_far": (54, 6), "neck": (55, -9), "tail": (-9, -7)}
_H_NECK = _round([(-6, -7), (13, -5.5), (17, 0), (13, 5.5)] + _fringe((13, 5.5), (-7, 10), 3, -3.0) + [(-7, 10)], 1)
_H_HEAD = _round([(-6, 3), (-7.5, -4), (-4, -9.5), (3, -11.5), (9, -10.5), (13, -7.6), (17, -5.6), (23.5, -4.2),
                  (26.6, -2.4), (27.6, 0.6), (25.5, 2.8), (15, 3.8), (6, 6.2), (0, 6.8)])
_H_JAW = _round([(-2, -1), (16, -0.4), (17.4, 1.1), (15, 2.7), (5, 4.4), (-3, 3.4)])
_H_EAR = _round([(-3.6, 1.5), (3.6, 1.5), (3.0, -5.5), (5.2, -10.2), (1.2, -9.6), (-1.6, -6)], 1)
_H_FU = _round([(-3, -4.5), (6, -4.5), (17, -2.6), (19, 0), (17, 2.8), (4, 4.5), (-3, 3.5)])                     # fore upper
_H_FL = _round([(-2.2, -2.6), (15.5, -2), (16.6, -5.6), (19.4, -6.4), (20.7, -2.5), (20.2, 2.2), (-2.2, 2.6)], 1)  # fore lower + paw
_H_HU = _round([(-6, -8), (6, -8.5), (17, -3.8), (20, 0), (17, 4), (3, 8.5), (-6, 6)])                           # thigh
_H_HL = _round([(-2.4, -3.2), (8, -2.6), (16.5, -2), (17.2, -5.6), (20, -6.4), (21.5, -2.4), (21, 2.3),
                (11, 2.6), (8, 5), (4, 4), (-2.4, 3.2)], 1)                                                        # hock + paw
_H_T1 = _round([(-3, -3.6), (19, -3), (21, 0.5)] + _fringe((21, 0.5), (-3, 6), 3, -4.0) + [(-3, 6)], 1)
_H_T2 = _round([(-1, -3), (13, -2.8), (22, 0.5)] + _fringe((22, 0.5), (-1, 5.5), 4, -5.0) + [(-1, 5.5)], 1)
_HL1F, _HL2F, _HL1H, _HL2H = 17.0, 20.0, 17.0, 21.0


def _herder_pose(action, t, p, look=0.0, pages=0):
    """All the state of the puppet for one exposure, in dog units (x forward, y down,
    ground at 0). Angles are absolute, degrees: 0 forward, -90 up, 90 down, 180 back."""
    P = dict(hip=(-26.0, -38.5), torso=-4.0, neck=-52.0, head=6.0, jaw=0.0, ear=8.0,
             tail1=118.0, tail2=146.0, sx=1.0,
             paws=[(25, 0), (30, 0), (-29, 0), (-23, 0)],   # fore near, fore far, hind near, hind far
             held=pages, reach=None)
    if action in ("wait", "turn", "slide"):
        # a held pose; one ear turns now and then, because it is listening
        if (t % 3.1) > 2.85:
            P["ear"] = -14
        if action == "turn":
            P["sx"] = math.cos(math.pi * clamp(p))
            lift = math.sin(math.pi * clamp(p))
            P["paws"][0] = (25, -5 * lift)
            P["paws"][3] = (-23, -4 * lift)
        if action == "slide":
            # leaving a wall like a shadow: flat on the ground, then up on its pins
            u = smooth(clamp(p))
            P["hip"] = (-26, lerp(-14, -38.5, u))
            P["torso"] = lerp(3, -4, u)
            P["neck"] = lerp(-4, -52, u)
            P["head"] = lerp(2, 6, u)
            P["tail1"] = lerp(176, 118, u)
            P["tail2"] = lerp(180, 146, u)
            P["ear"] = lerp(-60, 8, u)
            P["paws"] = [(lerp(46, 25, u), 0), (lerp(51, 30, u), 0), (lerp(-50, -29, u), 0), (lerp(-44, -23, u), 0)]
    elif action == "walk":
        ph = t * 1.5
        P["hip"] = (-26, -37 + 1.0 * math.sin(4 * math.pi * ph))
        P["paws"] = [_gait_foot(ph, 0.25, 0.62, 18, 6, 25), _gait_foot(ph, 0.75, 0.62, 18, 6, 30),
                     _gait_foot(ph, 0.0, 0.62, 18, 6, -29), _gait_foot(ph, 0.5, 0.62, 18, 6, -23)]
        P["neck"] = -46 + 3 * math.sin(4 * math.pi * ph)
        P["tail1"] = 130
        P["tail2"] = 152 + 6 * math.sin(2 * math.pi * ph)
    elif action == "circle":
        # the collie crouch: low, flat, eyes on the flock, a fast trot
        ph = t * 2.3
        P["hip"] = (-25, -30 + 0.8 * math.sin(4 * math.pi * ph))
        P["torso"] = 4
        P["neck"] = -10
        P["head"] = 5
        P["ear"] = 20
        P["tail1"] = 166
        P["tail2"] = 174 + 3 * math.sin(2 * math.pi * ph)
        P["paws"] = [_gait_foot(ph, 0.5, 0.5, 24, 5, 29), _gait_foot(ph, 0.0, 0.5, 24, 5, 34),
                     _gait_foot(ph, 0.0, 0.5, 24, 5, -29), _gait_foot(ph, 0.5, 0.5, 24, 5, -23)]
    elif action == "gather":
        # reach, take, tuck. The page stays flat the whole way.
        p = clamp(p)
        a = smooth(ramp(p, 0.0, 0.34))          # the reach
        b = smooth(ramp(p, 0.52, 1.0))          # the tuck
        P["hip"] = (-26 + 4 * a - 4 * b, -37)
        P["torso"] = lerp(-4, 1, a) - 5 * b
        P["neck"] = lerp(lerp(-52, -8, a), -62, b)
        P["head"] = lerp(lerp(6, 8, a), 38, b)
        jaw_open = smooth(ramp(p, 0.08, 0.3)) * (1 - smooth(ramp(p, 0.36, 0.46)))
        P["jaw"] = 5 + 21 * jaw_open if p > 0.08 else 0
        P["ear"] = 22 - 10 * b
        P["tail1"] = 135
        P["tail2"] = 150 + 10 * math.sin(2 * math.pi * 3 * t) * a * (1 - b)
        P["held"] = pages + (1 if p >= 0.42 else 0)
        P["taking"] = 0.36 <= p
    elif action == "carry":
        ph = t * 1.3
        P["hip"] = (-26, -36.5 + 0.8 * math.sin(4 * math.pi * ph))
        P["torso"] = -5
        P["neck"] = -62
        P["head"] = 38
        P["jaw"] = 6
        P["ear"] = 4
        P["paws"] = [_gait_foot(ph, 0.25, 0.66, 15, 4, 25), _gait_foot(ph, 0.75, 0.66, 15, 4, 30),
                     _gait_foot(ph, 0.0, 0.66, 15, 4, -29), _gait_foot(ph, 0.5, 0.66, 15, 4, -23)]
        P["tail1"] = 128
        P["tail2"] = 146 + 5 * math.sin(2 * math.pi * ph)
        P["held"] = max(1, pages)
    elif action == "swim":
        ph = t * 1.4
        P["hip"] = (-26, -6 + 1.2 * math.sin(2 * math.pi * ph))
        P["torso"] = -9
        P["neck"] = -38
        P["head"] = -2
        P["ear"] = -52
        P["tail1"] = 176
        P["tail2"] = 184 + 5 * math.sin(2 * math.pi * ph)
        P["paddle"] = ph
        P["jaw"] = 6 if pages else 0
    elif action == "flank":
        # swinging wide round the herd: flat out, a gallop, everything streaming behind
        ph = t * 2.6
        g = math.sin(2 * math.pi * ph)
        P["hip"] = (-26, -31 - 2.2 * g)
        P["torso"] = 2.5 * math.cos(2 * math.pi * ph)
        P["neck"] = -20 + 4 * g
        P["head"] = 3
        P["ear"] = -46
        P["tail1"] = 172
        P["tail2"] = 181 + 5 * g
        P["paws"] = [_gait_foot(ph, 0.00, 0.34, 28, 11, 29), _gait_foot(ph, 0.10, 0.34, 28, 11, 35),
                     _gait_foot(ph, 0.52, 0.34, 28, 11, -31), _gait_foot(ph, 0.62, 0.34, 28, 11, -24)]
    elif action == "creep":
        # the stalk toward a cow: belly low, head dead level, one slow paw at a time
        ph = t * 0.7
        P["hip"] = (-25, -26)
        P["torso"] = 5
        P["neck"] = -7
        P["head"] = 3
        P["ear"] = 24
        P["tail1"] = 170
        P["tail2"] = 178
        P["paws"] = [_gait_foot(ph, 0.25, 0.8, 13, 4, 31), _gait_foot(ph, 0.75, 0.8, 13, 4, 36),
                     _gait_foot(ph, 0.0, 0.8, 13, 4, -30), _gait_foot(ph, 0.5, 0.8, 13, 4, -23)]
    elif action == "eye":
        # "the eye": the collie drops, freezes with one fore paw off the ground and
        # stares the cow down. Nothing moves once it is down; that is the point.
        u = smooth(ramp(clamp(p), 0.0, 0.5))
        P["hip"] = (-25, lerp(-38.5, -24.5, u))
        P["torso"] = lerp(-4, 6, u)
        P["neck"] = lerp(-52, -5, u)
        P["head"] = lerp(6, 2, u)
        P["ear"] = lerp(8, 26, u)
        P["tail1"] = lerp(118, 171, u)
        P["tail2"] = lerp(146, 179, u)
        pl = smooth(ramp(clamp(p), 0.35, 0.75))
        P["paws"] = [(lerp(25, 31, u) + 15 * pl, -12.0 * pl), (lerp(30, 33, u), 0),
                     (lerp(-29, -34, u), 0), (lerp(-23, -20, u), 0)]
    elif action == "down":
        # lies flat to let the herd go by, head up, watching every one of them
        u = smooth(clamp(p))
        P["hip"] = (-26, lerp(-38.5, -17.5, u))
        P["torso"] = lerp(-4, 1.5, u)
        P["neck"] = lerp(-52, -44, u)
        P["head"] = lerp(6, 4, u)
        P["ear"] = lerp(8, 14, u)
        P["tail1"] = lerp(118, 174, u)
        P["tail2"] = lerp(146, 184, u)
        P["paws"] = [(lerp(25, 57, u), -1.5 * u), (lerp(30, 60, u), -1.5 * u), (lerp(-29, -12, u), 0), (lerp(-23, -5, u), 0)]
    else:
        raise ValueError("herding_dog: unknown action %r (use one of %s)" % (action, ", ".join(HERDER_ACTIONS)))
    if look:
        P["neck"] -= look * 0.55
        P["head"] -= look * 0.6
    return P


def _herder_solve(P):
    """Pin the pieces. Returns list of (piece, origin, angle, group) and anchors, in dog units."""
    hip = P["hip"]
    ta = P["torso"]
    lim = HERDER_LIMITS

    def pin(name):
        q = _rot(_H_PINS[name], ta)
        return (hip[0] + q[0], hip[1] + q[1])

    clamped = []

    def rel(name, absolute, parent):
        r = (absolute - parent + 180) % 360 - 180
        if name == "tail1":
            r = r % 360
        lo, hi = lim[name]
        c = clamp(r, lo, hi)
        if abs(c - r) > 1e-6:
            clamped.append(name)
        return parent + c

    parts = []
    # legs
    paws_out = []
    spec = [("sh", _HL1F, _HL2F, +1, _H_FU, _H_FL, 0), ("sh_far", _HL1F, _HL2F, +1, _H_FU, _H_FL, 1),
            ("hip", _HL1H, _HL2H, -1, _H_HU, _H_HL, 2), ("hip_far", _HL1H, _HL2H, -1, _H_HU, _H_HL, 3)]
    for name, l1, l2, bend, up, lo, k in spec:
        root = pin(name)
        if "paddle" in P:
            ph = P["paddle"] + (0.0, 0.5, 0.25, 0.75)[k]
            cx = 9 if k < 2 else -7
            tgt = (root[0] + cx + 9 * math.cos(2 * math.pi * ph), root[1] + 24 + 6 * math.sin(2 * math.pi * ph))
        else:
            tgt = P["paws"][k]
        a1, a2, joint, end = _ik2(root, tgt, l1, l2, bend)
        parts.append((up, root, a1, "body"))
        parts.append((lo, joint, a2, "body"))
        paws_out.append(end)
    parts.append((_H_TORSO, hip, ta, "body"))
    # tail
    t1 = rel("tail1", P["tail1"], ta)
    tp = pin("tail")
    t2 = rel("tail2", P["tail2"], t1)
    t2o = (tp[0] + 19 * _dirv(t1)[0], tp[1] + 19 * _dirv(t1)[1])
    parts.append((_H_T1, tp, t1, "body"))
    parts.append((_H_T2, t2o, t2, "body"))
    tail_tip = (t2o[0] + 20 * _dirv(t2)[0], t2o[1] + 20 * _dirv(t2)[1])
    # neck, head, jaw, ears
    na = rel("neck", P["neck"], ta)
    npin = pin("neck")
    ha = rel("head", P["head"], na)
    hp = (npin[0] + 14 * _dirv(na)[0], npin[1] + 14 * _dirv(na)[1])
    parts.append((_H_NECK, npin, na, "head"))
    parts.append((_H_HEAD, hp, ha, "head"))
    jq = _rot((7, 4), ha)
    ja = ha + clamp(P["jaw"], *lim["jaw"])
    parts.append((_H_JAW, (hp[0] + jq[0], hp[1] + jq[1]), ja, "head"))
    ea = clamp(P["ear"], *lim["ear"])
    for off, da, sc in (((0.5, -9.2), -20, 0.9), ((4, -9.6), 0, 1.0)):
        q = _rot(off, ha)
        ear = [(x * sc, y * sc) for x, y in _H_EAR]
        parts.append((ear, (hp[0] + q[0], hp[1] + q[1]), ha + ea + da, "head"))

    def onhead(pt):
        q = _rot(pt, ha)
        return (hp[0] + q[0], hp[1] + q[1])

    mid = _rot((14, 1.6), ja)
    jo = (hp[0] + jq[0], hp[1] + jq[1])
    anchors = {"mouth": ((onhead((21, 3.4))[0] + jo[0] + mid[0]) / 2, (onhead((21, 3.4))[1] + jo[1] + mid[1]) / 2),
               "nose": onhead((28, -0.5)), "head": onhead((8, -3)), "eye": onhead((11.5, -5.0)),
               "tail": tail_tip, "back": (hip[0] + 26, hip[1] - 14), "chest": pin("sh"), "paws": paws_out,
               "head_angle": ha}
    return parts, anchors, clamped


@lru_cache(maxsize=1)
def _herder_reach():
    return _herder_solve(_herder_pose("gather", 0.0, 0.34))[1]["mouth"]


def _pages(target, T, mouth, n, s, f, sway, color, line):
    """A fan of flat pages hanging from the mouth. Rigid rectangles: never bent."""
    if n <= 0:
        return
    img = _img(target)
    w, h = 21.0, 27.0
    pad = int(40 * s + 8)
    mx, my = T(mouth)
    lay = Image.new("RGBA", (int(2 * pad * SS), int(2 * pad * SS)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in reversed(range(min(n, 9))):
        ang = sway + (_hash(k * 3.1) - 0.5) * 9 + k * 1.2
        ox, oy = -1.9 * k, 1.1 * k
        quad = []
        for q in ((-w * 0.15, -1.5), (w * 0.85, -1.5), (w * 0.85, h), (-w * 0.15, h)):
            r = _rot(q, ang)
            quad.append(((pad + f * s * (ox - r[0])) * SS, (pad + s * (oy + r[1])) * SS))
        d.polygon(quad, fill=tuple(color) + (255,))
        d.line(quad + [quad[0]], fill=tuple(line) + (255,), width=max(1, int(0.9 * s * SS)))
        if k < 2:
            # the child's wavy lines, never letters
            for row in range(3):
                pts = []
                for i in range(9):
                    u = i / 8
                    q = _rot((-w * 0.15 + 3 + u * (w - 6), 6 + row * 6.5 + 1.4 * math.sin(u * 9 + row * 2 + k)), ang)
                    pts.append(((pad + f * s * (ox - q[0])) * SS, (pad + s * (oy + q[1])) * SS))
                d.line(pts, fill=tuple(line) + (170,), width=max(1, int(0.8 * s * SS)))
    lay = lay.resize((2 * pad, 2 * pad), Image.LANCZOS)
    _stamp(target, lay, mx - pad, my - pad)


def herding_dog(ink, x, y, s=1.0, facing=1, action="wait", t=0.0, p=0.0, look=0.0, pages=0,
                color=(14, 13, 20), page_color=(226, 233, 226), page_line=(70, 84, 96), exposure=HERDER_FPS):
    """The black shadow-puppet herding dog. See module docstring for the convention.

    actions: wait, walk, circle (the low collie crouch at a trot), gather (p: reach,
    take a page, tuck it under the chin), carry (walk with `pages` flat pages), swim,
    turn (p: the flat card turns over, edge-on halfway), slide (p: comes off the ground
    like a shadow leaving a wall).
    With the cows: flank (t: the wide flat-out swing round the herd), creep (t: the low
    stalk toward a cow), eye (p: drops and freezes, one fore paw lifted, staring the cow
    down), down (p: lies flat, head up, to let the herd go by).
    pages   how many pages it already holds (gather adds one at p >= 0.42).
    Returns anchors; "reach" is where the next page must be offered during gather.
    """
    tq = math.floor(t * exposure + 1e-6) / exposure if exposure else t
    P = _herder_pose(action, tq, p, look, pages)
    parts, A, _ = _herder_solve(P)
    f = (1 if facing >= 0 else -1) * P["sx"]
    if abs(f) < 0.05:
        f = 0.05 if f >= 0 else -0.05

    def T(q):
        return (x + f * s * q[0], y + s * q[1])

    pad = int(12 + 8 * s)
    xs, ys = [], []
    polys = []
    for poly, origin, ang, grp in parts:
        pts = []
        for q in poly:
            r = _rot(q, ang)
            pts.append(T((origin[0] + r[0], origin[1] + r[1])))
        xs += [u[0] for u in pts]
        ys += [u[1] for u in pts]
        polys.append((pts, grp))
    x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
    x1, y1 = int(max(xs)) + pad, int(max(ys)) + pad
    size = ((x1 - x0) * SS, (y1 - y0) * SS)
    col = tuple(color[:3]) + (255,)
    for grp in ("body", "head"):
        lay = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for pts, g in polys:
            if g == grp:
                d.polygon([((u - x0) * SS, (v - y0) * SS) for u, v in pts], fill=col)
        if grp == "head":
            ex, ey = T(A["eye"])
            ha = math.radians(A["head_angle"])
            eye = []
            for k in range(14):
                a = 2 * math.pi * k / 14
                q = (2.5 * math.cos(a), 1.35 * math.sin(a) - 0.5 * abs(math.cos(a)))
                eye.append(((ex + f * s * (q[0] * math.cos(ha) - q[1] * math.sin(ha)) - x0) * SS,
                            (ey + s * (q[0] * math.sin(ha) + q[1] * math.cos(ha)) - y0) * SS))
            d.polygon(eye, fill=(0, 0, 0, 0))
        lay = lay.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        if grp == "head" and P["held"]:
            sway = 5 * math.sin(2 * math.pi * tq * 1.3) if action in ("carry", "walk") else (6 if action == "swim" else 0)
            _pages(ink, T, A["mouth"], P["held"], s, 1 if f >= 0 else -1, sway, page_color, page_line)
        _stamp(ink, lay, x0, y0)
    out = {k: T(v) for k, v in A.items() if k not in ("paws", "head_angle")}
    out["paws"] = [T(q) for q in A["paws"]]
    out["reach"] = T(_herder_reach())
    out["bbox"] = (x0 + pad, y0 + pad, x1 - pad, y1 - pad)
    out["pages"] = P["held"]
    return out


def herd_circle(cx, cy, rx, ry, t, period=6.0, start=0.0):
    """Where the herding dog is on its low circle round the fish class.
    Returns (x, y, facing, behind, size): draw the dog BEFORE the class when behind is
    True (the far side of the ring), after it otherwise; size is a small depth scale."""
    a = 2 * math.pi * (t / period + start)
    x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
    behind = math.sin(a) < 0
    facing = 1 if -math.sin(a) > 0 else -1          # travelling direction along the ring
    size = 1.0 + 0.12 * math.sin(a)
    return x, y, facing, behind, size


def herd_swing(x0, y0, x1, y1, p, wide=90.0, creep_from=0.82):
    """The herding dog's wide swing from (x0, y0) round the herd to (x1, y1), p 0..1.
    It never runs AT the cows: it bulges `wide` px toward the viewer (negative: behind
    them), fast in the middle, and comes in on the last stretch at a creep.
    Returns (x, y, facing, size, action) for herding_dog; finish with action "eye"."""
    p = clamp(p)
    u = smooth(p) if p < creep_from else lerp(smooth(creep_from), 1.0, (p - creep_from) / (1 - creep_from))
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 2 * wide

    def at(v):
        return ((1 - v) ** 2 * x0 + 2 * v * (1 - v) * cx + v * v * x1,
                (1 - v) ** 2 * y0 + 2 * v * (1 - v) * cy + v * v * y1)

    x, y = at(u)
    xa, _ = at(min(1.0, u + 0.02))
    xb, _ = at(max(0.0, u - 0.02))
    facing = 1 if (xa - xb if abs(xa - xb) > 1e-6 else dx) >= 0 else -1
    size = 1.0 + 0.0012 * (y - (y0 + y1) / 2)
    action = "walk" if p < 0.06 else ("flank" if p < creep_from else "creep")
    return x, y, facing, size, action


# =============================================================================
# 2 · THE DIGGER · a wire dog drawn by constraints
# =============================================================================

DIGGER_ACTIONS = ("wait", "walk", "swim", "dig", "heave", "build", "unbend",
                  "nose_up", "flinch")                 # the last two are for the cows
DIGGER_TOLERANCE = 0.01      # declared: no wire may be more than 1 % off its length

_W_NAMES = ("S", "M", "R", "C", "B", "H", "Z", "J", "E1", "P1", "E2", "P2", "K1", "Q1", "K2", "Q2")
_WI = {n: i for i, n in enumerate(_W_NAMES)}
# Rest drawing (x forward, y down, ground 0). S shoulder, M mid-back, R rump, C chest,
# B belly, H skull, Z nose, J jaw, E/P elbow and fore paw, K/Q knee and hind paw.
_W_REST = {"S": (24, -38), "M": (0, -41), "R": (-25, -38), "C": (23, -21), "B": (-9, -25),
           "H": (36, -55), "Z": (56, -50), "J": (44, -45),
           "E1": (20, -19), "P1": (25, 0), "E2": (25, -19), "P2": (30.5, 0),
           "K1": (-19, -20), "Q1": (-28, 0), "K2": (-15, -20), "Q2": (-22, 0)}
_W_TRUSS = [("S", "M"), ("M", "R"), ("S", "R"), ("S", "C"), ("M", "C"), ("C", "B"), ("M", "B"), ("B", "R"),
            ("H", "Z"), ("Z", "J"), ("J", "H"), ("S", "H")]
_W_BONES = [("S", "E1"), ("E1", "P1"), ("S", "E2"), ("E2", "P2"), ("R", "K1"), ("K1", "Q1"), ("R", "K2"), ("K2", "Q2")]


def _w_len(a, b):
    pa, pb = _W_REST[a], _W_REST[b]
    return math.hypot(pa[0] - pb[0], pa[1] - pb[1])


_W_CONS = [(_WI[a], _WI[b], _w_len(a, b)) for a, b in _W_TRUSS + _W_BONES]


def _digger_handles(action, t, p, look=0.0):
    """What the animator states for this moment: where the paws are planted (pins) and
    roughly where rump, shoulder and nose are wanted (soft). Nothing else."""
    Hd = dict(R=(-25, -38), S=(24, -38), Z=(56, -50),
              paws=[(25, 0), (30.5, 0), (-28, 0), (-22, 0)], tail=(-128, 0.0), ear=0.0, extra={})
    if action == "wait":
        pass
    elif action == "walk":
        ph = t * 1.45
        bob = 1.2 * math.sin(4 * math.pi * ph)
        Hd["R"] = (-25, -37.5 + bob)
        Hd["S"] = (24, -37.5 - bob * 0.6)
        Hd["Z"] = (56, -49 + 1.5 * math.sin(4 * math.pi * ph + 1))
        Hd["paws"] = [_gait_foot(ph, 0.25, 0.62, 17, 6, 25), _gait_foot(ph, 0.75, 0.62, 17, 6, 30.5),
                      _gait_foot(ph, 0.0, 0.62, 17, 6, -28), _gait_foot(ph, 0.5, 0.62, 17, 6, -22)]
        Hd["tail"] = (-140, 10 * math.sin(2 * math.pi * ph))
    elif action == "swim":
        ph = t * 1.5
        Hd["R"] = (-25, -9 + 1.3 * math.sin(2 * math.pi * ph))
        Hd["S"] = (24, -13)
        Hd["Z"] = (55, -31)
        pw = []
        for k in range(4):
            a = 2 * math.pi * (ph + (0, 0.5, 0.25, 0.75)[k])
            root = Hd["S"] if k < 2 else Hd["R"]
            cx = (6, 10, -8, -4)[k]
            pw.append((root[0] + cx + 9 * math.cos(a), root[1] + 27 + 6 * math.sin(a)))
        Hd["paws"] = pw
        Hd["tail"] = (-176, 8 * math.sin(2 * math.pi * ph))
        Hd["ear"] = -40
    elif action == "dig":
        # the play-bow: rump up, chest down, nose in the hole, fore paws scooping in turn
        ph = t * 3.0
        Hd["R"] = (-22, -41)
        Hd["S"] = (19, -25 + 1.2 * math.sin(4 * math.pi * ph))
        Hd["Z"] = (43, -7 + 2.0 * math.sin(4 * math.pi * ph + 0.6))
        pw = []
        for off in (0.0, 0.5):
            u = (ph + off) % 1.0
            if u < 0.55:
                v = u / 0.55
                pw.append((lerp(41, 23, smooth(v)), 2.5))
            else:
                v = (u - 0.55) / 0.45
                pw.append((lerp(23, 41, smooth(v)), 2.5 - 11 * math.sin(math.pi * v)))
        Hd["paws"] = pw + [(-31, 0), (-21, 0)]
        Hd["tail"] = (-112, 16 * math.sin(2 * math.pi * t * 5))
        Hd["ear"] = 18
        Hd["extra"]["dig"] = (32, 3)
    elif action == "heave":
        # jaws on something in the ground; the body leans back until it gives
        p = clamp(p)
        a = smooth(ramp(p, 0.0, 0.2))
        b = ramp(p, 0.2, 0.75)
        c = smooth(ramp(p, 0.75, 0.9))
        shake = (1.1 * math.sin(2 * math.pi * 11 * t) * b * (1 - c))
        Hd["R"] = (lerp(lerp(-25, -24, a), -34, b) + 7 * c + shake, lerp(lerp(-38, -39, a), -29, b) - 8 * c)
        Hd["S"] = (lerp(lerp(24, 21, a), 13, b) + 9 * c + shake, lerp(lerp(-38, -30, a), -33, b) - 5 * c)
        grip = (lerp(43, 39, b), lerp(-5, -15, b * b))
        Hd["Z"] = (lerp(lerp(56, grip[0], a), 44, c), lerp(lerp(-50, grip[1], a), -55, c))
        Hd["paws"] = [(lerp(25, 35, a), 0), (lerp(30.5, 40, a), 0), (-27, 0), (-19, 0)]
        if c > 0:
            Hd["paws"][0] = (lerp(35, 27, c), -5 * math.sin(math.pi * c))
        Hd["tail"] = (lerp(-128, -165, b) + 30 * c, 14 * math.sin(2 * math.pi * 6 * t) * c)
        Hd["ear"] = lerp(0, -35, b) + 45 * c
        Hd["extra"]["grip"] = (41, 0)
        Hd["extra"]["out"] = c
    elif action == "build":
        # stamping a post into the bed: three blows with both fore paws, then one paw holds it
        p = clamp(p)
        blows = (0.22, 0.47, 0.72)
        h = 30.0
        lift = 0.0
        for b in blows:
            h -= 6.0 * smooth(ramp(p, b, b + 0.035))
            u = ramp(p, b - 0.17, b)
            lift = max(lift, math.sin(math.pi * min(1.0, u * 1.0)) ** 0.8 * (1 if p < b else 0))
        rest = smooth(ramp(p, 0.8, 1.0))
        Hd["extra"]["post"] = (42.0, h)
        Hd["R"] = (-24, -33)
        Hd["S"] = (17, lerp(-45 - 8 * lift, -39, rest) - (h - 12) * 0.2)
        Hd["Z"] = (lerp(47, 53, rest), lerp(-h - 17 - 9 * lift, -44, rest))
        Hd["paws"] = [(41, -h - 1 - 10 * lift), (lerp(44, 30.5, rest), lerp(-h - 1 - 10 * lift, 0, rest)), (-28, 0), (-21, 0)]
        Hd["tail"] = (-120, 12 * math.sin(2 * math.pi * t * 3))
        Hd["ear"] = 10
    elif action == "nose_up":
        # a cow lowers her muzzle to this dog she can see through: it stretches its
        # nose up to hers, one fore paw off the ground, and holds there
        u = smooth(ramp(clamp(p), 0.0, 0.6))
        Hd["R"] = (-25 - 2 * u, -38 + 3 * u)
        Hd["S"] = (24 - 3 * u, -38 - 5 * u)
        Hd["Z"] = (lerp(56, 52, u), lerp(-50, -71, u))
        Hd["paws"] = [(25 + 4 * u, -9 * smooth(ramp(clamp(p), 0.3, 0.7))), (30.5, 0), (-28, 0), (-22, 0)]
        Hd["tail"] = (lerp(-128, -112, u), 13 * math.sin(2 * math.pi * 2.2 * t) * u)
        Hd["ear"] = 16 * u
    elif action == "flinch":
        # a hoof comes down on the ice overhead: the whole drawing ducks, then looks up
        p = clamp(p)
        e = ramp(p, 0.0, 0.12) * (1 - smooth(ramp(p, 0.45, 1.0)))
        up = smooth(ramp(p, 0.5, 1.0))
        Hd["R"] = (-25 - 2 * e, -38 + 10 * e)
        Hd["S"] = (24 - 4 * e, -38 + 12 * e)
        q = _rot((32, -12), -55 * up)
        Hd["Z"] = (lerp(56, 46, e) * (1 - up) + (24 + q[0]) * up, lerp(-50, -27, e) * (1 - up) + (-38 + q[1]) * up)
        Hd["tail"] = (lerp(-128, -196, e), 0.0)
        Hd["ear"] = -55 * e + 10 * up
    elif action == "unbend":
        pass
    else:
        raise ValueError("digger: unknown action %r (use one of %s)" % (action, ", ".join(DIGGER_ACTIONS)))
    if look:
        dx, dy = Hd["Z"][0] - Hd["S"][0], Hd["Z"][1] - Hd["S"][1]
        q = _rot((dx, dy), -look)
        Hd["Z"] = (Hd["S"][0] + q[0], Hd["S"][1] + q[1])
    return Hd


def _digger_solve(Hd, iters=70):
    """Relaxation solver (projected constraints, Gauss-Seidel).
    Unknowns: 16 points. Hard: the four paw pins. Exact after convergence: every wire
    length. Soft: rump, shoulder and nose targets, which steer the first passes and are
    then let go, so the answer is a drawing in which every wire has its true length."""
    P = np.array([_W_REST[n] for n in _W_NAMES], float)
    # start from the rest drawing moved rigidly to the wanted rump and shoulder
    r0, s0 = np.array(_W_REST["R"], float), np.array(_W_REST["S"], float)
    r1, s1 = np.array(Hd["R"], float), np.array(Hd["S"], float)
    a = math.atan2(*(s1 - r1)[::-1]) - math.atan2(*(s0 - r0)[::-1])
    Rm = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    P = (P - r0) @ Rm.T + r1
    pins = {_WI["P1"]: Hd["paws"][0], _WI["P2"]: Hd["paws"][1], _WI["Q1"]: Hd["paws"][2], _WI["Q2"]: Hd["paws"][3]}
    for i, q in pins.items():
        P[i] = q
    # knees start on the believable side
    for hipn, kn, pn, side in (("S", "E1", "P1", -1), ("S", "E2", "P2", -1), ("R", "K1", "Q1", 1), ("R", "K2", "Q2", 1)):
        hq, pq = P[_WI[hipn]], P[_WI[pn]]
        P[_WI[kn]] = (hq + pq) / 2 + np.array([side * 6.0, 0.0])
    soft = [(_WI["R"], np.array(Hd["R"], float), 0.35), (_WI["S"], np.array(Hd["S"], float), 0.35),
            (_WI["Z"], np.array(Hd["Z"], float), 0.6)]
    free = np.ones(len(P), bool)
    for i in pins:
        free[i] = False
    for it in range(iters):
        if it < iters * 0.6:
            w = 1.0 - it / (iters * 0.6)
            for i, tgt, k in soft:
                P[i] += (tgt - P[i]) * k * w
        for i, j, L in _W_CONS:
            d = P[j] - P[i]
            n = math.hypot(d[0], d[1]) or 1e-9
            corr = d * ((n - L) / n)
            wi, wj = (1.0 if free[i] else 0.0), (1.0 if free[j] else 0.0)
            tot = wi + wj
            if tot:
                P[i] += corr * (wi / tot)
                P[j] -= corr * (wj / tot)
    # the elbow chooses a believable configuration: mirror a knee that fell on the wrong side
    for hipn, kn, pn, side in (("S", "E1", "P1", -1), ("S", "E2", "P2", -1), ("R", "K1", "Q1", 1), ("R", "K2", "Q2", 1)):
        hq, kq, pq = P[_WI[hipn]], P[_WI[kn]], P[_WI[pn]]
        ax = pq - hq
        cr = ax[0] * (kq - hq)[1] - ax[1] * (kq - hq)[0]
        # with y down and the leg pointing down, cross > 0 means the knee is to the rear (-x)
        if (cr > 0) != (side < 0):
            u = ax / (np.hypot(*ax) or 1e-9)
            v = kq - hq
            P[_WI[kn]] = hq + 2 * u * (v @ u) - v
    # the jaw stays under the skull
    hq, zq, jq = P[_WI["H"]], P[_WI["Z"]], P[_WI["J"]]
    ax = zq - hq
    if ax[0] * (jq - hq)[1] - ax[1] * (jq - hq)[0] < 0:
        u = ax / (np.hypot(*ax) or 1e-9)
        v = jq - hq
        P[_WI["J"]] = hq + 2 * u * (v @ u) - v
    res = 0.0
    for i, j, L in _W_CONS:
        res = max(res, abs(math.hypot(*(P[j] - P[i])) - L) / L)
    return P, res


@lru_cache(maxsize=4096)
def _digger_points(action, tq, pq, look):
    Hd = _digger_handles(action, tq, pq, look)
    if action == "unbend":
        Hs = _digger_handles("wait", tq, 0.0, look)
        P, res = _digger_solve(Hs)
        u = smooth(clamp(pq))
        # p=0: every point strung along one reed leaning over the water
        Q = P.copy()
        order = ("Z", "J", "H", "S", "E1", "P1", "E2", "P2", "C", "M", "B", "R", "K1", "Q1", "K2", "Q2")
        for k, n in enumerate(order):
            f = k / (len(order) - 1)
            Q[_WI[n]] = (6 + 10 * math.sin(f * 3.0), -78 + 78 * f)
        P = Q + (P - Q) * u
        Hd = Hs
        Hd["tail"] = (lerp(-95, -128, u), 20 * (1 - u) * math.sin(tq * 9))
        Hd["extra"] = {"unbend": u}
        return P, res, Hd
    P, res = _digger_solve(Hd)
    return P, res, Hd


def _gravel(d, T, x0, y0, t, s, color):
    """Gravel thrown back between the hind legs: one small handful per scoop."""
    ph = t * 3.0
    for off in (0.0, 0.5):
        n0 = math.floor(ph + off - 0.55)
        for n in (n0, n0 - 1):
            age = (ph + off - 0.55 - n) / 3.0
            if age < 0 or age > 0.62:
                continue
            for i in range(6):
                h1, h2, h3 = _hash(n * 7.3 + i + off * 5), _hash(n * 3.7 + i * 2.1 + off), _hash(n + i * 9.4)
                vx, vy = -(70 + 60 * h1), -(52 + 46 * h2)
                px = 24 + vx * age
                py = -1 + vy * age + 150 * age * age
                if py > 2:
                    continue
                r = (1.7 + 1.9 * h3) * s
                qx, qy = T((px, py))
                al = int(255 * min(1.0, 1.6 * (1 - age / 0.62)))
                d.ellipse([(qx - x0 - r) * SS, (qy - y0 - r) * SS, (qx - x0 + r) * SS, (qy - y0 + r) * SS],
                          fill=tuple(color) + (al,), outline=(40, 44, 50, al // 2), width=max(1, SS // 2))


def digger(ink, x, y, s=1.0, facing=1, action="wait", t=0.0, p=0.0, look=0.0,
           wire=(224, 232, 238), shade=(22, 26, 40), point=(255, 255, 255), gravel=(168, 160, 138),
           post=True, post_color=(126, 104, 78), spray=True):
    """The wire digger, solved from constraints every frame.

    actions: wait, walk, swim, dig (t: play-bow, fore paws scooping in turn, gravel
    thrown back), heave (p: grips something in the bed, leans back, strains, it comes
    out), build (p: three blows drive a post in, then one paw holds it down), unbend
    (p: a single reed of wire unbends into the dog).
    With the cows: nose_up (p: stretches its nose up to a cow's lowered muzzle and
    holds), flinch (p: ducks when a hoof comes down on the ice overhead, then looks up).
    post    in build, draw the post (False: draw your own at anchors["post"]).
    spray   in dig, draw the thrown gravel.
    Returns anchors plus "residual" (worst wire-length error, as a fraction) and
    "solved" (residual <= DIGGER_TOLERANCE); in dig, "hole" is where the hole belongs.
    """
    f = 1 if facing >= 0 else -1
    P, res, Hd = _digger_points(action, round(float(t), 4), round(float(p), 4), round(float(look), 2))

    def T(q):
        return (x + f * s * q[0], y + s * q[1])

    G = {n: (float(P[i][0]), float(P[i][1])) for n, i in _WI.items()}
    # things attached-to the solved drawing: tail, ear, eye
    back = math.degrees(math.atan2(G["S"][1] - G["R"][1], G["S"][0] - G["R"][0]))
    ta = back + Hd["tail"][0] + Hd["tail"][1]
    t1 = (G["R"][0] + 11 * _dirv(ta)[0], G["R"][1] + 11 * _dirv(ta)[1])
    t2 = (t1[0] + 11 * _dirv(ta - 22 + Hd["tail"][1] * 0.8)[0], t1[1] + 11 * _dirv(ta - 22 + Hd["tail"][1] * 0.8)[1])
    hd = math.degrees(math.atan2(G["Z"][1] - G["H"][1], G["Z"][0] - G["H"][0]))
    ea = hd - 112 + Hd["ear"]
    e1 = (G["H"][0] + 13 * _dirv(ea)[0], G["H"][1] + 13 * _dirv(ea)[1])
    e2 = (G["H"][0] + 6 * _dirv(hd)[0], G["H"][1] + 6 * _dirv(hd)[1])
    eye = (G["H"][0] + 7 * _dirv(hd + 28)[0], G["H"][1] + 7 * _dirv(hd + 28)[1])
    mouth = ((G["Z"][0] * 0.62 + G["J"][0] * 0.38), (G["Z"][1] * 0.62 + G["J"][1] * 0.38) + 1.5)

    allp = list(G.values()) + [t1, t2, e1, e2, (G["Z"][0] + 4, G["Z"][1]), (G["H"][0], G["H"][1] - 14), (G["H"][0] - 14, G["H"][1])]
    post_xy = Hd["extra"].get("post")
    if post_xy:
        allp += [(post_xy[0] - 5, -post_xy[1] - 2), (post_xy[0] + 5, 6)]
    if "dig" in Hd["extra"]:
        allp += [(-70, -60), (40, 6)]
    sp = [T(q) for q in allp]
    pad = int(8 + 5 * s)
    x0, y0 = int(min(q[0] for q in sp)) - pad, int(min(q[1] for q in sp)) - pad
    x1, y1 = int(max(q[0] for q in sp)) + pad, int(max(q[1] for q in sp)) + pad
    lay = Image.new("RGBA", ((x1 - x0) * SS, (y1 - y0) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    def L(q):
        u, v = T(q)
        return ((u - x0) * SS, (v - y0) * SS)

    if post_xy and post:
        px, ph_ = post_xy
        quad = [L((px - 3.4, -ph_)), L((px + 3.4, -ph_)), L((px + 3.0, 5)), L((px - 3.0, 5))]
        d.polygon(quad, fill=tuple(post_color) + (255,))
        d.line(quad + [quad[0]], fill=tuple(shade) + (255,), width=max(1, int(1.0 * s * SS)))

    def curve(a, b, c, n=10):
        return [((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * b[0] + u * u * c[0],
                 (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * b[1] + u * u * c[1]) for u in (k / n for k in range(n + 1))]

    # control point so the back passes through M
    mc = (2 * G["M"][0] - (G["S"][0] + G["R"][0]) / 2, 2 * G["M"][1] - (G["S"][1] + G["R"][1]) / 2)
    backline = curve(G["S"], mc, G["R"])
    bc = (2 * G["B"][0] - (G["C"][0] + G["R"][0]) / 2, 2 * G["B"][1] - (G["C"][1] + G["R"][1]) / 2)
    belly = curve(G["C"], bc, G["R"])
    ribs = []
    for k in range(1, 9):
        a = backline[k] if k % 2 else belly[k]
        b = belly[k + 1] if k % 2 else backline[k + 1]
        ribs.append([a, b])
    e3 = (G["H"][0] + 11 * _dirv(ea - 24)[0], G["H"][1] + 11 * _dirv(ea - 24)[1])
    far = [[G["S"], G["E2"], G["P2"]], [G["R"], G["K2"], G["Q2"]], [G["H"], e3, (G["H"][0] + 2 * _dirv(hd)[0], G["H"][1] + 2 * _dirv(hd)[1])]]
    near = [[G["S"], G["E1"], G["P1"]], [G["R"], G["K1"], G["Q1"]]]
    wires = ([backline, belly, [G["S"], G["C"]], [G["S"], G["H"]], [G["H"], G["Z"], G["J"], G["H"]],
              [G["J"], G["C"]], [G["R"], t1, t2], [G["H"], e1, e2]] + near)
    ww = max(1.0, 1.55 * s) * SS
    for group, alpha, k in ((far, 150, 0.8), (ribs, 190, 0.7), (wires, 255, 1.0)):
        for pass_, col, wk in ((0, tuple(shade) + (int(alpha * 0.7),), 2.3), (1, tuple(wire) + (alpha,), 1.0)):
            for w in group:
                pts = [L(q) for q in w]
                wd = max(1, int(round(ww * k * wk)))
                d.line(pts, fill=col, width=wd, joint="curve")
                if pass_ == 0:
                    for q in (pts[0], pts[-1]):
                        d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=col)
    # paws: the wire is curled into a small loop
    for n, al in (("P2", 150), ("Q2", 150), ("P1", 255), ("Q1", 255)):
        q = L((G[n][0] + 2.2, G[n][1] - 1.6))
        r = 2.6 * s * SS
        for col, wd in ((tuple(shade) + (int(al * 0.7),), ww * 2.0), (tuple(wire) + (al,), ww * 0.9)):
            d.ellipse([q[0] - r, q[1] - r * 0.75, q[0] + r, q[1] + r * 0.75], outline=col, width=max(1, int(wd)))
    # the points
    for n in ("S", "M", "R", "C", "B", "H", "J", "E1", "K1"):
        q = L(G[n])
        r = 1.5 * s * SS
        d.ellipse([q[0] - r - SS, q[1] - r - SS, q[0] + r + SS, q[1] + r + SS], fill=tuple(shade) + (200,))
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=tuple(point) + (255,))
    q = L(G["Z"])
    r = 2.7 * s * SS
    d.ellipse([q[0] - r - SS, q[1] - r - SS, q[0] + r + SS, q[1] + r + SS], fill=tuple(shade) + (230,))
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], outline=tuple(wire) + (255,), width=max(1, int(ww * 0.9)))
    q = L(eye)
    r = 1.4 * s * SS
    d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=tuple(point) + (255,))
    if "dig" in Hd["extra"] and spray:
        _gravel(d, T, x0, y0, t, s, gravel)
    lay = lay.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    _stamp(ink, lay, x0, y0)
    out = {"mouth": T(mouth), "nose": T(G["Z"]), "head": T(G["H"]), "eye": T(eye), "tail": T(t2),
           "back": T(G["M"]), "paws": [T(G[n]) for n in ("P1", "P2", "Q1", "Q2")],
           "bbox": (x0 + pad, y0 + pad, x1 - pad, y1 - pad), "residual": res, "solved": res <= DIGGER_TOLERANCE}
    if "dig" in Hd["extra"]:
        out["hole"] = T(Hd["extra"]["dig"])
    if "grip" in Hd["extra"]:
        out["grip"] = T(Hd["extra"]["grip"])
        out["out"] = Hd["extra"]["out"]
    if post_xy:
        out["post"] = T((post_xy[0], -post_xy[1]))
        out["post_foot"] = T((post_xy[0], 0))
    return out


# =============================================================================
# 3 · THE OLD DOG · an engraved print, cut out and hinged
# =============================================================================

OLD_DOG_ACTIONS = ("lie", "lift_head", "look", "turn_back", "back", "look_over", "let_pass", "turn_round",
                   "rise", "lie_down", "wait", "walk", "swim",
                   "greet", "make_room", "beside")           # the last three are for the lead cow
OLD_DOG_STATES = ("lie", "back", "passed")

SOURCE = {
    "title": "File:Bewicks-newfoundland.jpg",
    "what": "The Newfoundland Dog, wood engraving by Thomas Bewick (1753-1828) for A General History of "
            "Quadrupeds (first published 1790); the dog drawn at Eslington, Northumberland",
    "author": "Thomas Bewick",
    "license": "Public domain",
    "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
    "source_url": "https://commons.wikimedia.org/wiki/File:Bewicks-newfoundland.jpg",
    "file_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Bewicks-newfoundland.jpg",
    "local": "films/sources/dogs/kennel_a/bewick-newfoundland.jpg",
}
_SRC_PATH = _FILMS / "sources" / "dogs" / "kennel_a" / "bewick-newfoundland.jpg"
_SRC_SIZE = (531, 378)

# The scissor lines, in pixels of the scan (531 x 378). Dog faces left in the print.
_CUT = {
    "head": [(52, 109), (59, 99), (73, 95), (85, 85), (103, 75), (128, 70), (150, 72), (169, 76), (176, 84), (180, 100),
             (179, 121), (171, 137), (158, 148), (151, 158), (129, 154), (112, 144), (98, 139), (80, 138), (65, 132),
             (55, 123)],
    "body": [(172, 79), (190, 79), (215, 85), (238, 94), (270, 97), (300, 98), (350, 96), (400, 94), (432, 100),
             (452, 107), (463, 121), (469, 145), (471, 170), (468, 200), (455, 222), (430, 230), (400, 228), (378, 201),
             (352, 208), (320, 220), (280, 228), (240, 228), (215, 224), (190, 224), (165, 220), (158, 203), (153, 180),
             (149, 158), (158, 150), (171, 138), (180, 122), (180, 100)],
    "tail": [(440, 104), (447, 112), (468, 123), (489, 119), (501, 96), (508, 70), (507, 42), (497, 19), (477, 7),
             (446, 5), (419, 12), (404, 27), (404, 50), (410, 66), (425, 78), (438, 69), (434, 47), (446, 34), (464, 34),
             (474, 50), (476, 74), (466, 93), (452, 102), (444, 100), (436, 122), (462, 132), (474, 120)],
    "fn": [(197, 184), (233, 184), (235, 250), (228, 287), (228, 315), (239, 330), (239, 348), (215, 353), (191, 349),
           (187, 334), (193, 315), (198, 287), (199, 250)],
    "ff": [(159, 193), (193, 193), (193, 250), (191, 290), (189, 315), (181, 327), (160, 331), (137, 329), (132, 318),
           (139, 309), (162, 299), (167, 275), (167, 225)],
    "hn": [(371, 190), (421, 184), (425, 225), (419, 250), (424, 275), (421, 300), (414, 322), (413, 337), (390, 341),
           (365, 337), (365, 325), (384, 319), (396, 300), (391, 275), (384, 250), (375, 215)],
    "hf": [(424, 180), (469, 169), (471, 205), (464, 225), (466, 250), (474, 275), (482, 312), (498, 340), (498, 351),
           (470, 353), (431, 349), (427, 334), (439, 329), (451, 318), (451, 287), (442, 250), (429, 215)],
}
_CUT["tail"] = _CUT["tail"][:23]      # the plume, as a C-shaped strip
_UNDER = [(148, 82), (182, 80), (184, 124), (176, 142), (161, 156), (146, 158), (140, 120)]   # neck under the head
_PIVOT = {"head": (170, 118), "tail": (456, 114), "fn": (215, 198), "ff": (177, 202), "hn": (398, 200), "hf": (448, 192)}
_BODY_PIVOT = (428, 226)
_GROUND = (262, 345)      # the ground point under the middle of the standing dog
_BELLY = (262, 170)       # the middle of the belly, the anchor for swimming
_EYE = (104, 106)
_CV = (860, 500)          # assembly table, in scan pixels
_CVO = (150, 70)          # where scan (0, 0) sits on the table
OLD_K = 0.43              # scan pixels to screen pixels at s = 1


def _hand_engraving():
    """Fallback only (the scan is missing): hatch the same cut pieces by hand in code,
    so the old dog is still a cut print and never a blank. Not Bewick; says so."""
    im = Image.new("L", _SRC_SIZE, 255)
    d = ImageDraw.Draw(im)
    for k, name in enumerate(("hf", "ff", "tail", "body", "hn", "fn", "head")):
        poly = _CUT[name]
        m = Image.new("L", _SRC_SIZE, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        h = Image.new("L", _SRC_SIZE, 244)
        hd = ImageDraw.Draw(h)
        ang = (25, 70, 120, 15, 80, 100, 40)[k]
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for j in range(-90, 90):
            o = j * 5
            cx, cy = 265 - dy * o, 190 + dx * o
            for seg in range(-30, 30):
                if _hash(j * 13.7 + seg * 1.9 + k) < 0.55:
                    a = (cx + dx * seg * 14, cy + dy * seg * 14)
                    hd.line([a, (a[0] + dx * 9, a[1] + dy * 9)], fill=70, width=1)
        im.paste(h, (0, 0), m)
        d.line(poly + [poly[0]], fill=30, width=2)
    d.ellipse([84, 88, 132, 124], fill=60)
    d.ellipse([52, 106, 62, 116], fill=20)
    d.ellipse([101, 103, 108, 109], fill=235)
    return im


@lru_cache(maxsize=1)
def _pieces():
    """Cut the print. Each piece: (gray L image with the print, alpha mask L, crop origin)."""
    foraged = _SRC_PATH.exists()
    gray = Image.open(_SRC_PATH).convert("L") if foraged else _hand_engraving()
    if gray.size != _SRC_SIZE:
        gray = gray.resize(_SRC_SIZE, Image.LANCZOS)
    out = {}
    for name, poly in _CUT.items():
        big = Image.new("L", (_SRC_SIZE[0] * 4, _SRC_SIZE[1] * 4), 0)
        dd = ImageDraw.Draw(big)
        dd.polygon([(px * 4, py * 4) for px, py in poly], fill=255)
        src = gray
        if name == "body":
            # the neck that the head used to cover: borrowed from the mane beside it
            under = Image.new("L", gray.size, 0)
            ImageDraw.Draw(under).polygon(_UNDER, fill=255)
            src = gray.copy()
            src.paste(ImageChops.offset(gray, -34, 4), (0, 0), under)
            dd.polygon([(px * 4, py * 4) for px, py in _UNDER], fill=255)
        if name in _PIVOT and name != "head":
            # a round tab of card round each pin, so a turned leg never opens a gap
            px, py = _PIVOT[name]
            r = 15 if name != "tail" else 11
            dd.ellipse([(px - r) * 4, (py - r) * 4, (px + r) * 4, (py + r) * 4], fill=255)
        mask = big.resize(_SRC_SIZE, Image.LANCZOS)
        # the cut edge of the card catches a little shadow
        inner = mask.filter(ImageFilter.MinFilter(5))
        rim = ImageChops.subtract(mask, inner)
        g = ImageChops.subtract(src, rim.point(lambda v: int(v * 0.22)))
        box = mask.getbbox()
        out[name] = (g.crop(box), mask.crop(box), (box[0], box[1]))
    # the closed eye: a second head, the eye inked over and one lid line scratched in
    g, m, o = out["head"]
    g2 = g.copy()
    d2 = ImageDraw.Draw(g2)
    ex, ey = _EYE[0] - o[0], _EYE[1] - o[1]
    d2.ellipse([ex - 6, ey - 5, ex + 6, ey + 4], fill=58)
    d2.arc([ex - 6, ey - 5, ex + 6, ey + 5], 20, 160, fill=190, width=1)
    out["head_shut"] = (g2, m, o)
    out["_foraged"] = foraged
    return out


_OLD_CACHE = {}


def _old_base():
    return dict(bdx=0.0, bdy=0.0, brot=0.0, head=0.0, hflip=1.0, tail=0.0, tdy=0.0, tdx=0.0,
                fn=0.0, ff=0.0, hn=0.0, hf=0.0, drop=0.0, eye=1.0, sx=1.0)


_OLD_STAND = _old_base()
_OLD_LIE = dict(_old_base(), bdy=115.0, head=-30.0, tail=104.0, tdy=84.0, tdx=4.0,
                fn=88.0, ff=82.0, hn=90.0, hf=89.0, drop=10.0)
_OLD_SIT = dict(_old_base(), bdy=106.0, brot=21.0, head=-8.0, tail=96.0, tdy=80.0, tdx=4.0,
                fn=8.0, ff=-2.0, hn=68.0, hf=64.0, drop=6.0)


def _oblend(a, b, u):
    return {k: lerp(a[k], b[k], u) for k in a}


def _old_rise(u):
    """0 lying (head up) .. 1 standing: the front end first, then the back end."""
    lie = dict(_OLD_LIE, head=12.0)
    if u < 0.55:
        return _oblend(lie, _OLD_SIT, smooth(u / 0.55))
    return _oblend(_OLD_SIT, dict(_OLD_STAND, head=-4.0), smooth((u - 0.55) / 0.45))


def _old_state(state):
    """The three ways it can be lying when the cow comes: as it began ("lie"), with its
    back turned ("back"), or after it has let a reel pass ("passed")."""
    if state == "lie":
        return dict(_OLD_LIE)
    if state == "back":
        return dict(_OLD_LIE, sx=-1.0)
    if state == "passed":
        return _old_pose("let_pass", 0.0, 1.0)
    raise ValueError("old_dog: unknown state %r (use one of %s)" % (state, ", ".join(OLD_DOG_STATES)))


_ROOM = 44.0     # scan pixels the old dog shuffles along the sill to make room


def _old_pose(action, t, p, look=0.0, state="lie", cow=1):
    p = clamp(p)
    if action in ("greet", "make_room", "beside"):
        P = _old_state(state)
        tail0, tdy0 = P["tail"], P["tdy"]
        # scan +x runs from the nose to the tail: make room AWAY from the cow
        away = _ROOM * (1.0 if cow >= 0 else -1.0)
        if action == "greet":
            # one eye opens, the head comes up and goes round to her, the tail thumps
            # the boards twice, and the head goes down again. That is a welcome.
            P["eye"] = 1.0 if 0.06 <= p < 0.97 else 0.0
            up = smooth(ramp(p, 0.08, 0.3)) * (1 - smooth(ramp(p, 0.8, 0.97)))
            P["head"] = lerp(-30.0, 9.0, up)
            if cow < 0:      # she is at its tail end: it looks over its shoulder
                P["hflip"] = math.cos(math.pi * smooth(ramp(p, 0.26, 0.4)) * (1 - smooth(ramp(p, 0.72, 0.84))))
            v = ramp(p, 0.42, 0.72)
            thump = abs(math.sin(2 * math.pi * v)) if 0 < v < 1 else 0.0
            P["tail"] = tail0 - 24 * thump
            P["tdy"] = tdy0 - 10 * thump
        elif action == "make_room":
            # head up, then two shuffles along the boards, one end at a time
            up = smooth(ramp(p, 0.0, 0.18)) * (1 - smooth(ramp(p, 0.84, 1.0)))
            P["head"] = lerp(-30.0, 6.0, up)
            P["eye"] = 1.0 if p < 0.95 else 0.0
            a, b = ramp(p, 0.2, 0.46), ramp(p, 0.52, 0.78)
            P["bdx"] += away * 0.5 * (smooth(a) + smooth(b))
            hop = math.sin(math.pi * a) * (a < 1) + math.sin(math.pi * b) * (b < 1)
            P["bdy"] -= 5.0 * hop
            P["brot"] = 2.5 * (math.sin(math.pi * a) - math.sin(math.pi * b)) * (1 if cow >= 0 else -1)
        else:
            # "beside": moved over and settled against her. A slow breath; when she
            # shifts (p, a one-shot) its eye opens, finds her, and closes again.
            P["bdx"] += away
            P["bdy"] += 1.6 * math.sin(2 * math.pi * t / 4.2)
            P["head"] = -30.0 + 2.0 * math.sin(2 * math.pi * t / 4.2 - 0.7)
            P["eye"] = 1.0 if 0.2 < p < 0.8 else 0.0
            P["head"] += 7.0 * smooth(ramp(p, 0.2, 0.4)) * (1 - smooth(ramp(p, 0.6, 0.8)))
    elif action == "lie":
        P = dict(_OLD_LIE)
    elif action == "lift_head":
        P = dict(_OLD_LIE, head=lerp(-30, 12, smooth(p)))
    elif action == "look":
        # the long look: head up and still; one slow blink in the middle
        P = dict(_OLD_LIE, head=12.0, eye=0.0 if 0.42 <= p <= 0.6 else 1.0)
    elif action in ("rise", "lie_down"):
        P = _old_rise(p if action == "rise" else 1 - p)
    elif action in ("turn_back", "turn_round"):
        u = p if action == "turn_back" else 1 - p
        if u < 0.30:
            P = _old_rise(u / 0.30)
        elif u < 0.68:
            v = (u - 0.30) / 0.38                      # three slow steps round
            k = min(2, int(v * 3))
            w = smooth(clamp((v * 3 - k) / 0.7))
            ang = (k + w) * 60.0
            P = dict(_OLD_STAND, head=-4.0)
            P["sx"] = math.cos(math.radians(ang))
            step = math.sin(math.pi * w)
            sw = 13 * step * (1 if k % 2 == 0 else -1)
            P.update(fn=sw, hf=sw, ff=-sw, hn=-sw, bdy=-2.0 * step)
        else:
            P = _old_rise(1 - (u - 0.68) / 0.32)
            P["sx"] = -1.0
            down = smooth(ramp(u, 0.86, 1.0))
            P["head"] = lerp(P["head"], -30.0, down)
        if action == "turn_round":
            P["sx"] = -P["sx"]
    elif action == "back":
        P = dict(_OLD_LIE, sx=-1.0)
    elif action == "look_over":
        # with its back turned: the head comes up and turns to look over the shoulder
        P = dict(_OLD_LIE, sx=-1.0)
        P["head"] = lerp(-30, 12, smooth(ramp(p, 0.0, 0.4)))
        P["hflip"] = math.cos(math.pi * smooth(ramp(p, 0.4, 0.62)))
        P["head"] = lerp(P["head"], 2.0, smooth(ramp(p, 0.62, 0.8)))
    elif action == "let_pass":
        # the tail comes off the place, the hindquarters are tucked aside, the eyes close
        P = dict(_OLD_LIE, sx=-1.0, hflip=-1.0, head=2.0)
        a = smooth(ramp(p, 0.0, 0.45))
        P["tail"] = lerp(104, 18, a)
        P["tdy"] = lerp(84, 6, a)
        P["tdx"] = lerp(4, 0, a)
        b = smooth(ramp(p, 0.3, 0.75))
        P["bdx"] = -26 * b
        P["hn"] = lerp(89, 96, b)
        P["hf"] = lerp(85, 93, b)
        c = smooth(ramp(p, 0.7, 0.9))
        P["hflip"] = -math.cos(math.pi * c)
        P["head"] = lerp(2, -30, smooth(ramp(p, 0.8, 1.0)))
        P["eye"] = 0.0 if p > 0.92 else 1.0
    elif action == "wait":
        P = dict(_OLD_STAND, head=-3.0)
    elif action == "walk":
        ph = t * 0.8
        a = 16 * math.sin(2 * math.pi * ph)
        P = dict(_OLD_STAND, fn=a, hf=a * 0.9, ff=-a, hn=-a * 0.9, bdy=2.5 * abs(math.sin(2 * math.pi * ph)),
                 head=-8 + 3 * math.sin(4 * math.pi * ph), tail=14 + 6 * math.sin(2 * math.pi * ph))
    elif action == "swim":
        ph = t * 1.0
        a = 26 * math.sin(2 * math.pi * ph)
        b = 26 * math.cos(2 * math.pi * ph)
        P = dict(_OLD_STAND, fn=20 + a, ff=20 - a, hn=-18 + b, hf=-18 - b, head=14.0, brot=5.0,
                 tail=62 + 8 * math.sin(2 * math.pi * ph), tdy=14.0, bdy=3 * math.sin(2 * math.pi * ph))
    else:
        raise ValueError("old_dog: unknown action %r (use one of %s)" % (action, ", ".join(OLD_DOG_ACTIONS)))
    if look:
        P["head"] += look
    P["head"] = clamp(P["head"], -40, 42)
    return P


def _aff(*steps):
    M = np.eye(3)
    for kind, *v in steps:
        if kind == "t":
            A = np.array([[1, 0, v[0]], [0, 1, v[1]], [0, 0, 1.0]])
        elif kind == "r":
            a = math.radians(v[0])
            A = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
        else:
            A = np.array([[v[0], 0, 0], [0, v[1], 0], [0, 0, 1.0]])
        M = A @ M
    return M


def _old_mats(P):
    """Scan pixel -> assembly table, for every piece. Rotations are about the pins."""
    bp = _BODY_PIVOT
    body = _aff(("t", -bp[0], -bp[1]), ("r", P["brot"]), ("t", bp[0] + P["bdx"] + _CVO[0], bp[1] + P["bdy"] + _CVO[1]))
    mats = {"body": body}
    for name in ("head", "tail", "fn", "ff", "hn", "hf"):
        pv = _PIVOT[name]
        rot = P[name]
        steps = [("t", -pv[0], -pv[1])]
        if name == "head":
            steps.append(("s", P["hflip"] if abs(P["hflip"]) > 0.08 else 0.08, 1.0))
        steps.append(("r", rot))
        off = (0.0, 0.0)
        if name == "tail":
            off = (P["tdx"], P["tdy"])
        elif name != "head":
            off = (0.0, P["drop"])
        steps.append(("t", pv[0] + off[0], pv[1] + off[1]))
        mats[name] = body @ _aff(*steps)
    return mats


def old_dog(ink, x, y, s=1.0, facing=1, action="lie", t=0.0, p=0.0, look=0.0,
            paper=(186, 182, 174), ink_color=(34, 32, 38), verso=False, eye=None, exposure=8,
            state="lie", cow=1):
    """The old dog: Bewick's engraved Newfoundland, cut out and hinged.

    actions: lie (chin on its paws, across a sill), lift_head (p), look (p: the long
    look, one slow blink at 0.42..0.6), turn_back (p: gets up one end at a time, turns
    round in three slow steps, lies down facing the other way with its tail laid out
    behind it), back (lying with its back turned), look_over (p: head up and turned to
    look over its shoulder), let_pass (p: tail lifted off the place, hindquarters
    tucked aside, head down, eyes closed), turn_round (p: turn_back undone), rise (p),
    lie_down (p), wait (standing), walk (t), swim (t).
    With the lead cow, who folds down beside it: greet (p: one eye opens, head up and
    round to her, two tail thumps, head down), make_room (p: shuffles along the sill
    away from her in two goes), beside (t breathing; p: its eye opens on her and
    closes), all three from `state` ("lie", "back", or "passed" = after let_pass) with
    `cow` = +1 when she is at its nose end, -1 at its tail end.
    `facing` is the way it faces BEFORE it turns: turn_back, back, look_over and
    let_pass draw it the other way round by themselves.
    paper / ink_color   the card and the printing ink. Dim them for dusk.
    verso   True: when its back is turned the card shows its unprinted side.
    eye     None follows the action; 0 forces the eye shut, 1 open.
    Returns anchors; "place" is the spot behind it where a reel would be laid.
    """
    tq = math.floor(t * exposure + 1e-6) / exposure if exposure else t
    P = _old_pose(action, tq, p, look, state, cow)
    if eye is not None:
        P["eye"] = eye
    pcs = _pieces()
    mats = _old_mats(P)
    f = 1 if facing >= 0 else -1
    sx = P["sx"]
    turned = sx < 0
    k = OLD_K * s
    wpx = max(2, int(round(_CV[0] * k * max(abs(sx), 0.03))))
    hpx = max(2, int(round(_CV[1] * k)))
    mirror = (f * (1 if sx >= 0 else -1)) > 0      # the print faces left; mirror it to face right
    ckey = (tuple(round(v, 2) for v in P.values()), round(s, 4), mirror, tuple(paper), tuple(ink_color), bool(verso))
    lay = _OLD_CACHE.get(ckey)
    if lay is None:
        table = Image.new("L", _CV, 255)
        alpha = Image.new("L", _CV, 0)
        for name in ("hf", "ff", "tail", "body", "hn", "fn", "head"):
            key = "head_shut" if (name == "head" and P["eye"] < 0.5) else name
            g, m, o = pcs[key]
            M = mats[name] @ _aff(("t", o[0], o[1]))
            inv = np.linalg.inv(M)
            co = (inv[0, 0], inv[0, 1], inv[0, 2], inv[1, 0], inv[1, 1], inv[1, 2])
            gg = g.transform(_CV, Image.AFFINE, co, resample=Image.BICUBIC, fillcolor=255)
            mm = m.transform(_CV, Image.AFFINE, co, resample=Image.BICUBIC, fillcolor=0)
            table.paste(gg, (0, 0), mm)
            alpha = ImageChops.lighter(alpha, mm)
        # the pins that hold it together
        td = ImageDraw.Draw(table)
        for name in ("head", "fn", "hn", "tail"):
            if name == "tail" and P["tdy"] > 30:
                continue
            pv = mats[name] @ np.array([_PIVOT[name][0], _PIVOT[name][1], 1.0])
            td.ellipse([pv[0] - 4, pv[1] - 4, pv[0] + 4, pv[1] + 4], fill=40)
            td.ellipse([pv[0] - 1.6, pv[1] - 1.6, pv[0] + 1.6, pv[1] + 1.6], fill=215)
        if verso and turned:
            table = table.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(214 + v * 0.16))
        g = table.resize((wpx, hpx), Image.LANCZOS)
        a = alpha.resize((wpx, hpx), Image.LANCZOS)
        if mirror:
            g, a = g.transpose(Image.FLIP_LEFT_RIGHT), a.transpose(Image.FLIP_LEFT_RIGHT)
        # contrast of a worn print, then card and ink
        gn = np.asarray(g, np.float32) / 255.0
        gn = np.clip((gn - 0.12) / 0.78, 0, 1)[..., None]
        rgb = np.array(ink_color, np.float32) + (np.array(paper, np.float32) - np.array(ink_color, np.float32)) * gn
        lay = Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB").convert("RGBA")
        lay.putalpha(a)
        if len(_OLD_CACHE) > 48:
            _OLD_CACHE.clear()
        _OLD_CACHE[ckey] = lay
    a = lay.getchannel("A")
    anchor = _BELLY if action == "swim" else _GROUND
    ax = (anchor[0] + _CVO[0]) / _CV[0] * wpx
    if mirror:
        ax = wpx - ax
    ay = (anchor[1] + _CVO[1]) * k
    ox, oy = x - ax, y - ay
    _stamp(ink, lay, ox, oy)

    def S(name, pt):
        q = mats[name] @ np.array([pt[0], pt[1], 1.0])
        u = q[0] / _CV[0] * wpx
        if mirror:
            u = wpx - u
        return (ox + u, oy + q[1] * k)

    bb = a.getbbox() or (0, 0, 1, 1)
    out = {"nose": S("head", (54, 113)), "mouth": S("head", (74, 128)), "eye": S("head", _EYE),
           "head": S("head", (120, 105)), "tail": S("tail", (430, 55)), "back": S("body", (330, 100)),
           "rump": S("body", (466, 150)), "chin": S("head", (100, 140)),
           "bbox": (ox + bb[0], oy + bb[1], ox + bb[2], oy + bb[3]),
           "turned": turned, "foraged": pcs["_foraged"]}
    tl = S("tail", (455, 40))
    out["place"] = (tl[0], y)
    # where the lead cow's near side should come to when she folds down next to it
    nose_side = bool(mirror)          # the print faces left; mirrored, its nose end is on the right
    right = (cow >= 0) == nose_side
    out["beside"] = (out["bbox"][2] if right else out["bbox"][0], y)
    return out


# =============================================================================
# checks (MEASURED) and the sheets
# =============================================================================

def selfcheck(verbose=True):
    """Numeric invariants. Returns a dict; raises AssertionError when one fails."""
    rep = {}
    # 1 · shadow puppet: no joint leaves its limits, no leg leaves its pin
    worst_clamp, worst_reach = [], 0.0
    for act in HERDER_ACTIONS:
        for k in range(48):
            P = _herder_pose(act, k / 12.0, k / 47.0, 0.0, 3)
            parts, A, clamped = _herder_solve(P)
            if clamped:
                worst_clamp.append((act, k, tuple(clamped)))
            if "paddle" not in P:
                for tgt, got in zip(P["paws"], A["paws"]):
                    worst_reach = max(worst_reach, math.hypot(tgt[0] - got[0], tgt[1] - got[1]))
    rep["herder_joint_limit_hits"] = worst_clamp
    rep["herder_worst_paw_miss_units"] = round(worst_reach, 4)
    assert not worst_clamp, "herder joint limit exceeded: %r" % worst_clamp[:3]
    assert worst_reach < 0.5, "herder paw did not reach its contact: %.3f" % worst_reach
    # 2 · wire dog: every wire keeps its length, every pinned paw is exactly on its pin
    worst, worst_at, pin = 0.0, None, 0.0
    for act in DIGGER_ACTIONS:
        if act == "unbend":
            continue
        for k in range(72):
            t, p = k / 24.0, k / 71.0
            Hd = _digger_handles(act, t, p)
            Pp, res = _digger_solve(Hd)
            if res > worst:
                worst, worst_at = res, (act, k)
            for n, q in zip(("P1", "P2", "Q1", "Q2"), Hd["paws"]):
                pin = max(pin, math.hypot(Pp[_WI[n]][0] - q[0], Pp[_WI[n]][1] - q[1]))
    rep["digger_worst_wire_residual"] = round(worst, 5)
    rep["digger_worst_at"] = worst_at
    rep["digger_worst_pin_drift_units"] = round(pin, 6)
    assert worst <= DIGGER_TOLERANCE, "digger wire off its length by %.2f%% at %r" % (worst * 100, worst_at)
    assert pin < 1e-6
    # 3 · print: at rest the cut pieces reassemble the scan (inside the dog)
    pcs = _pieces()
    mats = _old_mats(_OLD_STAND)
    table = Image.new("L", _CV, 255)
    alpha = Image.new("L", _CV, 0)
    for name in ("hf", "ff", "tail", "body", "hn", "fn", "head"):
        g, m, o = pcs[name]
        table.paste(g, (int(o[0] + _CVO[0]), int(o[1] + _CVO[1])), m)
        alpha.paste(255, (int(o[0] + _CVO[0]), int(o[1] + _CVO[1])), m.point(lambda v: 255 if v > 250 else 0))
    for name in mats:
        want = _aff(("t", _CVO[0], _CVO[1]))
        assert np.allclose(mats[name], want, atol=1e-9), name
    if pcs["_foraged"]:
        scan = Image.open(_SRC_PATH).convert("L")
        ref = Image.new("L", _CV, 255)
        ref.paste(scan, _CVO)
        inner = alpha.filter(ImageFilter.MinFilter(9))
        under = Image.new("L", _CV, 0)
        ImageDraw.Draw(under).polygon([(px + _CVO[0], py + _CVO[1]) for px, py in _UNDER], fill=255)
        inner = ImageChops.subtract(inner, under.filter(ImageFilter.MaxFilter(5)))
        diff = np.asarray(ImageChops.difference(table, ref), np.float32)
        msk = np.asarray(inner) > 0
        rep["print_rest_mean_abs_diff"] = round(float(diff[msk].mean()), 3)
        rep["print_pixels_compared"] = int(msk.sum())
        assert diff[msk].mean() < 6.0, "the cut print no longer reassembles the scan"
    rep["print_foraged"] = pcs["_foraged"]
    if verbose:
        for k_, v in rep.items():
            print("  %-34s %s" % (k_, v))
    return rep


def _sheet_ground(w, h, split=True):
    """Dusk above, creek below, so every dog is judged on both grounds."""
    a = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    if split:
        top = np.array([70, 58, 104], np.float32) + (np.array([214, 150, 92], np.float32) - np.array([70, 58, 104], np.float32)) * (yy ** 2.2)
        bot = np.array([78, 150, 150], np.float32) + (np.array([24, 78, 92], np.float32) - np.array([78, 150, 150], np.float32)) * yy
        a[:] = top[:, None, :]
        a[:, w // 2:] = bot[:, None, :]
    else:
        a[:] = (60, 124, 130)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")


def _sheet(name, rows, out_dir, cell=(232, 150), cols=8, scale=1.0):
    """rows: list of (label, fn(target, cx, gy, k, n)) drawing one cell for frame k of n."""
    from kit import Ink, font
    w, h = cell[0] * cols + 120, cell[1] * len(rows) + 10
    ink = Ink(0.0, 0, (w, h), boil=0)
    ink.img = _sheet_ground(w, h)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    for r, (label, fn) in enumerate(rows):
        gy = 10 + cell[1] * r + cell[1] - 26
        ink.d.line([(118, gy), (w, gy)], fill=(255, 255, 255, 60), width=1)
        ink.d.text((6, gy - 40), label, font=font("mono", 13), fill=(255, 255, 255, 235))
        for k in range(cols):
            cx = 120 + cell[0] * k + cell[0] // 2
            fn(ink, cx, gy, k, cols)
    path = Path(out_dir) / ("kennel_a_sheet_%s.png" % name)
    ink.img.save(path)
    return path


def sheets(out_dir=None):
    out_dir = Path(out_dir) if out_dir else _HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []

    def H(action, tspan=1.0, **kw):
        def fn(ink, cx, gy, k, n):
            u = k / (n - 1)
            herding_dog(ink, cx, gy - (40 if action == "swim" else 0), 1.25, 1 if k < n // 2 or action in ("gather", "turn", "slide", "eye", "down") else -1,
                        action, t=u * tspan, p=u, **kw)
        return fn

    made.append(_sheet("herder", [
        ("wait", H("wait", 3.2)), ("wait look=45", H("wait", 1, look=45)), ("walk", H("walk", 0.62)),
        ("circle", H("circle", 0.42)), ("gather p", H("gather", 1, pages=2)), ("carry 5", H("carry", 0.7, pages=5)),
        ("swim", H("swim", 0.7)), ("swim+page", H("swim", 0.7, pages=1)), ("turn p", H("turn")), ("slide p", H("slide")),
        ("flank", H("flank", 0.34)), ("creep", H("creep", 1.25)), ("eye p", H("eye")), ("down p", H("down")),
    ], out_dir))

    def D(action, tspan=1.0, **kw):
        def fn(ink, cx, gy, k, n):
            u = k / (n - 1)
            digger(ink, cx - 8, gy - (40 if action == "swim" else 0), 1.25, 1 if k < n // 2 or action in ("heave", "build", "unbend", "dig", "nose_up", "flinch") else -1,
                   action, t=u * tspan, p=u, **kw)
        return fn

    made.append(_sheet("digger", [
        ("wait", D("wait")), ("wait look=45", D("wait", look=45)), ("walk", D("walk", 0.65)), ("swim", D("swim", 0.62)),
        ("dig", D("dig", 0.33)), ("dig (later)", D("dig", 2.0)), ("heave p", D("heave", 0.4)), ("build p", D("build", 1.0)),
        ("unbend p", D("unbend")), ("nose_up p", D("nose_up", 0.5)), ("flinch p", D("flinch")),
    ], out_dir))

    def O(action, tspan=1.0, sc=0.62, **kw):
        def fn(ink, cx, gy, k, n):
            u = k / (n - 1)
            old_dog(ink, cx, gy - (26 if action == "swim" else 0), sc, kw.pop("facing", 1) if "facing" in kw else 1,
                    action, t=u * tspan, p=u, **kw)
        return fn

    made.append(_sheet("old_dog", [
        ("lie", O("lie")), ("lift_head p", O("lift_head")), ("look p", O("look")), ("turn_back p", O("turn_back")),
        ("back", O("back")), ("look_over p", O("look_over")), ("let_pass p", O("let_pass")),
        ("turn_round p", O("turn_round")), ("rise p", O("rise")), ("wait", O("wait")), ("walk", O("walk", 1.25)),
        ("swim", O("swim", 1.0)), ("turn_back verso", O("turn_back", verso=True)),
        ("greet cow=+1", O("greet")), ("greet cow=-1", O("greet", cow=-1)),
        ("greet passed -1", O("greet", state="passed", cow=-1)),
        ("make_room", O("make_room")), ("make_room passed", O("make_room", state="passed", cow=-1)),
        ("beside p", O("beside", 4.2)),
    ], out_dir, cell=(232, 124)))
    made.append(cow_strip(out_dir))
    return made


def _standin_cow(d, x, y, s=1.0, facing=1, fold=0.0, head=0.0, color=(120, 96, 86), calf=False):
    """A flat stand-in cow for judging the dogs against (NOT the film's cow: the cow
    builder owns her). Crooked left horn and a bell so the lead cow is not mistaken."""
    f = 1 if facing >= 0 else -1
    k = s * (0.55 if calf else 1.0)
    leg = 46 * (1 - fold)
    by = y - leg * k

    def P(px, py):
        return (x + f * k * px, by + k * py)

    col = tuple(color) + (255,)
    d.polygon([P(-70, -52), P(58, -56), P(72, -40), P(66, -4), P(-66, 0), P(-78, -30)], fill=col)
    for lx in (-58, -44, 44, 58):
        d.polygon([P(lx - 6, -6), P(lx + 6, -6), P(lx + 5, leg), P(lx - 5, leg)], fill=col)
    hx, hy = 78, -52 + head
    d.polygon([P(60, -54), P(hx + 4, hy - 12), P(hx + 34, hy + 6), P(hx + 30, hy + 20), P(hx + 6, hy + 14), P(62, -28)], fill=col)
    if not calf:
        d.line([P(hx + 2, hy - 10), P(hx - 2, hy - 26), P(hx + 8, hy - 34)], fill=(226, 214, 190, 255), width=max(2, int(4 * k)))
        d.line([P(hx + 8, hy - 10), P(hx + 16, hy - 24), P(hx + 10, hy - 30), P(hx + 20, hy - 34)], fill=(226, 214, 190, 255), width=max(2, int(4 * k)))
        bx, byy = P(68, -22)
        d.ellipse([bx - 5 * k, byy, bx + 5 * k, byy + 11 * k], fill=(214, 168, 70, 255))
    d.line([P(-76, -40), P(-86, -8)], fill=col, width=max(2, int(4 * k)))
    return P(hx + 32, hy + 14)      # her muzzle


def cow_strip(out_dir=None):
    """Five moments where one of these dogs deals with a cow, at film size (960x540
    each, two rows), with a stand-in cow. For judging scale and read only."""
    from kit import Ink
    out_dir = Path(out_dir) if out_dir else _HERE
    W, Hh = 960, 540
    sheet = Image.new("RGB", (W * 3, Hh * 2))
    shots = []

    def porch(ink):
        ink.img = _sheet_ground(W, Hh, split=False)
        a = np.asarray(_sheet_ground(W, Hh, split=True))[:, :W // 2][:, :1]
        ink.img = Image.fromarray(np.repeat(a, W, axis=1))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        ink.d.rectangle([0, 394, W, Hh], fill=(52, 44, 60, 255))
        ink.d.rectangle([560, 400, W, Hh], fill=(40, 104, 112, 255))
        ink.d.line([(560, 400), (W, 400)], fill=(210, 240, 236, 255), width=2)

    def water(ink, ice=False):
        a = np.asarray(_sheet_ground(W, Hh, split=True))[:, W // 2:][:, :1]
        ink.img = Image.fromarray(np.repeat(a, W, axis=1))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        ink.d.rectangle([0, 0, W, 120], fill=(70, 58, 104, 255))
        ink.d.rectangle([0, 116, W, 124], fill=(226, 240, 244, 255) if ice else (210, 240, 236, 255))
        ink.d.rectangle([0, 470, W, Hh], fill=(34, 62, 66, 255))

    # 1 · S4: the swing, three exposures of one run, and the herd on its path
    ink = Ink(0, 0, (W, Hh), boil=0); porch(ink)
    for i in range(3):
        _standin_cow(ink.d, 330 + 150 * i, 394, 0.9, 1, head=10 if i == 2 else 0)
    for p in (0.2, 0.5, 0.74):
        x, y, fc, size, act = herd_swing(140, 400, 800, 396, p, wide=58)
        herding_dog(ink, x, y, 0.9 * size, fc, act, t=p * 2.0)
    shots.append(ink.img)
    # 2 · S4: the eye. The lead cow has stopped and is turning her head away
    ink = Ink(0, 0, (W, Hh), boil=0); porch(ink)
    _standin_cow(ink.d, 420, 394, 0.9, 1, head=16)
    _standin_cow(ink.d, 250, 394, 0.9, 1)
    _standin_cow(ink.d, 110, 394, 0.9, 1, calf=True)
    herding_dog(ink, 610, 394, 0.9, -1, "eye", p=1.0)
    shots.append(ink.img)
    # 3 · S3/S4: down, while they file past
    ink = Ink(0, 0, (W, Hh), boil=0); porch(ink)
    _standin_cow(ink.d, 300, 386, 0.9, 1)
    _standin_cow(ink.d, 520, 386, 0.9, 1)
    herding_dog(ink, 420, 430, 0.9, -1, "down", p=1.0)
    digger(ink, 700, 394, 0.9, -1, "wait")
    shots.append(ink.img)
    # 4 · the wire dog and a lowered muzzle
    ink = Ink(0, 0, (W, Hh), boil=0); porch(ink)
    mz = _standin_cow(ink.d, 360, 394, 0.9, 1, head=34)
    digger(ink, mz[0] + 0.9 * 43 - 2, 394, 0.9, -1, "nose_up", p=1.0, t=0.3)
    shots.append(ink.img)
    # 5 · S5: under the ice, the stamp overhead
    ink = Ink(0, 0, (W, Hh), boil=0); water(ink, ice=True)
    _standin_cow(ink.d, 470, 116, 0.9, 1, head=30)
    digger(ink, 330, 470, 0.9, 1, "flinch", p=0.14)
    digger(ink, 520, 470, 0.9, -1, "flinch", p=1.0)
    herding_dog(ink, 690, 300, 0.9, -1, "swim", t=0.2, look=40)
    old_dog(ink, 170, 300, 0.7, 1, "swim", t=0.2, look=20)
    shots.append(ink.img)
    # 6 · S6: she folds down beside the old dog on the sill
    ink = Ink(0, 0, (W, Hh), boil=0); porch(ink)
    a = old_dog(ink, 425, 394, 0.78, 1, "greet", p=0.5, state="passed", cow=-1)
    _standin_cow(ink.d, a["beside"][0] + 0.9 * 112, 394, 0.9, -1, fold=0.9, head=22)
    shots.append(ink.img)
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % 3) * W, (i // 3) * Hh))
    path = out_dir / "kennel_a_strip_cows.png"
    sheet.save(path)
    return path


if __name__ == "__main__":
    if "--check" in sys.argv:
        selfcheck()
    else:
        selfcheck()
        for path in sheets(sys.argv[1] if len(sys.argv) > 1 else None):
            print("wrote", path)
