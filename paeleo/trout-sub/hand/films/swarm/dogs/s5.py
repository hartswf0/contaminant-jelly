"""S5 · ICE, AND ELEVEN · film seconds 116.0 to 144.0 (local t = film - 116).

Built under scion/animation-07.md (Peter Foldes, drawn metamorphosis): a drawn form is changed into
another by in-betweens that keep its identity long enough for the change to be felt. The SCION's
primitives are real data in this file, not a look:

    Key            a key contour drawing: a named list of points, always in the same order
    Morph          keys in time + the pacing into each key + discontinuity markers + intervention frames
    field          an in-between FIELD: every point of the contour gets its own amount of in-between
    MARKERS        discontinuity markers: moments where NO in-between is drawn (the stamp; the split)
    interventions  hand-authored frames that override an in-between that would be visibly bad

Three forms are metamorphosed, each because the story needs it:

    ICE     the creek's bright line -> a skin of ice (the frost front is the field, left to right)
            -> bruised under her hoof -> cracked -> [marker: split] -> plates that tip and sink -> the line.
            "The computer restarted."
    WOUND   her breath's round fog on the ice -> [marker: cut, the stamp] -> a white star -> the star's own
            arms run out into the crack across the whole width (one closed contour all the way).
    REEL    the row of film pieces the pack stood in the gravel -> through the lead dog's mouth (the
            intervention: a via-point) -> a spiral on the spool. The work becomes the thing carried up.

check() (run under __main__ --check, and before every render) asserts what the representation
supports: equal point counts in every key (correspondence), no topological flip in any sampled
in-between (ice thickness never negative, the wound's area never changes sign, the strip's pieces
never change order), every key recognised exactly at its planned time, the board's counts (51 dogs in,
eleven up with nothing, everybody else up with a thing), and that the frames of the hold under the
ice are identical. What can only be judged by looking is in the builder's report, not here.

Staging is the board's (films/swarm/dogs/board.md, S5); times in this file are FILM seconds.
The first two seconds and the frozen tableau are drawn by s4's own functions at a clock that slows
to a stop, so local 0 is s4's last frame. Exposes SECONDS, draw(t, ink), sound(mix, at).
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kit                                   # noqa: E402
from kit import clamp, ramp, ease, lerp, smooth, W, H, FPS   # noqa: E402
import dog                                   # noqa: E402
import herd                                  # noqa: E402
import porch                                 # noqa: E402
import props                                 # noqa: E402
import town                                  # noqa: E402
import kennel_a as ka                        # noqa: E402
import kennel_b as kb                        # noqa: E402
import importlib.util as _ilu               # noqa: E402

_spec = _ilu.spec_from_file_location("dogs_sound", str(_HERE / "sound.py"))   # films/ has another module called sound
snd = sys.modules.get("dogs_sound")
if snd is None:
    snd = _ilu.module_from_spec(_spec)
    sys.modules["dogs_sound"] = snd
    _spec.loader.exec_module(snd)

try:                                         # the sequence before this one: its last frame is my first
    import s4 as S4                          # noqa: E402
except Exception as _e:                      # pragma: no cover
    raise ImportError("s5 starts on s4's last frame and draws it with s4's own functions; s4 did not import: %r" % (_e,))

SECONDS = 28.0
T0 = 116.0
T1 = T0 + SECONDS
TEAL = (24, 120, 128)
Cam = town.Cam
DS = 0.6                                     # the lead dog
RS, HS, GS, TS = S4.RS, S4.HS, S4.GS, S4.TS  # the pack's sizes, as S4 drew them
OLD = S4.OLD
UNDER = dict(tint=kb.WATER, tint_amount=0.3)
LEAD_UNDER = dict(tint=TEAL, tint_amount=0.3, shadow=False)
LINE_Y, PS, PW = S4.LINE_Y, S4.PS, S4.PW

# ---- the beats (film seconds; the board's) ----
T_COLD = 116.8          # the warmth goes out of the water from the top
T_SKIN = 117.0          # the white skin starts along the line, left to right
T_STOP = 118.0          # everything stops; boil off
T_SPLIT = 119.5         # cut to F-SPLIT; she steps down onto the ice
T_NOSE = 120.8          # the dog's nose reaches the underside of the ice
T_HOLD = 121.0          # nose to nose through the ice, to 122.0
T_STAMP = 122.0         # the first stamp; boil back on
T_STAMP2 = 122.6        # the second; the crack runs the whole width
T_BREAK = 123.0         # plates; the amber comes back
T_CLEAR = 124.5         # clear water; cut to F-TOWN; the second pack drops in
T_GOON = 124.8          # every dog goes on from the pose it stopped in
T_LATER = 127.0         # a light change: later
T_OUT = 131.0           # the first looker's breath goes
T_UP = 133.0            # eleven heads through the surface
T_ALONE = 137.0         # the lead dog alone at the making place
T_WIND = 137.8
T_LID = 139.4
T_PAW = 139.75
T_LOOK = 139.9          # it looks up at the roof for whoever should look. Nobody. Hold to 140.7
T_TAKE = 140.7
T_RISE = 141.0
T_BREACH = 141.95
T_SHAKE = 142.45
T_LAY = 143.2
T_PLEASED = 143.7

FS = 116.55             # where s4's clock stops (its works are simulated to 116.6)


def bump(x):
    return math.sin(math.pi * clamp(x)) if 0 < x < 1 else 0.0


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def s4_clock(f):
    """S4's own clock: it runs at full speed at 116.0 and the cold slows it to a stop at 118.0."""
    if f >= T_STOP:
        return FS
    u = clamp((f - T0) / (T_STOP - T0))
    return T0 + (FS - T0) * (1 - (1 - u) ** (2.0 / (FS - T0)))


def clock(f):
    """The world's ambient clock (water, weed, lamps, the line): it stops under the ice and goes on from
    exactly where it stopped."""
    if f < T_STOP:
        return f
    if f < T_STAMP:
        return T_STOP
    return T_STOP + (f - T_STAMP)


def frozen(f):
    return T_STOP <= f < T_STAMP


def cold_at(f):
    return ease(f, T_COLD, T_STOP) * (1 - ease(f, T_BREAK, T_CLEAR - 0.2))


def night_at(f):
    return 0.9 * ease(f, T_LATER, T_LATER + 0.8)


def dusk_at(f):
    return 0.4 + 0.14 * ease(f, T_LATER - 0.4, T_LATER + 0.8) + 0.06 * ramp(f, T_LATER + 0.8, T1)


# ====================================================================== #
#  1 · DRAWN METAMORPHOSIS (scion/animation-07): keys, fields, markers   #
# ====================================================================== #

EASES = {"linear": lambda u: u, "inout": smooth, "out": lambda u: 1 - (1 - u) ** 3, "in": lambda u: u ** 3,
         "slam": lambda u: 1.0 if u > 0 else 0.0}


class Key:
    """One key contour drawing: points in a fixed order (the correspondence IS the order)."""

    def __init__(self, name, pts, closed=True):
        self.name, self.pts, self.closed = name, np.asarray(pts, float), closed

    def __len__(self):
        return len(self.pts)


class Morph:
    """keys = [(time, Key, pacing into this key)]; markers = [(time, kind, note)] where kind 'cut' means no
    in-between is drawn across that time and 'split' means the form is handed to other contours there;
    interventions = [(t0, t1, fn(pts, f, w, ka, kb) -> pts, note)] hand-authored frames; field(u, ka, kb) ->
    one in-between amount per point (an in-between field) for the span that ENDS on the named key."""

    def __init__(self, name, keys, markers=(), interventions=(), fields=None):
        self.name, self.keys, self.markers, self.interventions = name, list(keys), list(markers), list(interventions)
        self.fields = fields or {}
        n = {len(k) for _, k, _ in self.keys}
        assert len(n) == 1, f"{name}: keys disagree on point count {n}: no correspondence"
        self.n = n.pop()

    def span(self, f):
        ks = self.keys
        if f <= ks[0][0]:
            return ks[0], ks[0], 0.0
        for a, b in zip(ks, ks[1:]):
            if a[0] <= f < b[0]:
                return a, b, (f - a[0]) / (b[0] - a[0])
        return ks[-1], ks[-1], 1.0

    def at(self, f, raw=False):
        (ta, ka_, _), (tb, kb_, pace), u = self.span(f)
        cut = [tm for tm, kind, _ in self.markers if kind == "cut" and ta < tm <= tb]
        if cut:
            w = np.full(self.n, 0.0 if f < cut[0] else 1.0)
        elif kb_.name in self.fields:
            w = np.asarray(self.fields[kb_.name](EASES[pace](u), ka_, kb_), float)
        else:
            w = np.full(self.n, EASES[pace](u))
        pts = ka_.pts + (kb_.pts - ka_.pts) * w[:, None]
        if not raw:
            for t0, t1, fn, _ in self.interventions:
                if t0 <= f < t1:
                    pts = fn(pts, f, w, ka_, kb_)
        return pts

    def name_at(self, f):
        (ta, ka_, _), (tb, kb_, _), u = self.span(f)
        return ka_.name if u < 0.5 else kb_.name


def signed_area(pts):
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


# ---- ICE: the line -> skin -> bruised -> cracked -> (split) plates -------------------------------

ICE_X0, ICE_X1, ICE_M = 300.0, 960.0, 67      # one column every 10 px
ICE_TH = 13.0                                 # how thick the skin is (world px, below the line)
COW_ICE_X = 700.0                             # where she stands on it
NOSE_X = 612.0                                # where the two noses meet through it


@lru_cache(maxsize=None)
def hoof_x():
    a = herd.anchors("lead", herd.stamp(herd.STAMP_HIT + 0.05), COW_ICE_X, 401.0, herd.S, -1, 0)
    return float(a["hooves"]["nf"][0])


def _plates():
    return [(max(ICE_X0, a), min(ICE_X1, b)) for a, b in porch.ice_plates() if b > ICE_X0 + 4 and a < ICE_X1 - 4]


@lru_cache(maxsize=None)
def ice_morph():
    xs = np.linspace(ICE_X0, ICE_X1, ICE_M)
    top = np.full(ICE_M, 400.0)

    def contour(tp, bt):          # top left -> right, then the underside right -> left: one closed drawing
        return np.concatenate([np.stack([xs, tp], 1), np.stack([xs[::-1], bt[::-1]], 1)])
    belly = ICE_TH + 2.0 * np.sin(xs * 0.047) + 1.2 * np.sin(xs * 0.131 + 1.0)
    hx = hoof_x()
    dent = np.exp(-((xs - hx) / 26.0) ** 2)
    edges = [a for a, b in _plates()][1:]
    notch = np.zeros(ICE_M)
    for e in edges:
        notch = np.maximum(notch, np.exp(-((xs - e) / 7.0) ** 2))
    K = dict(
        water=Key("water", contour(top, top + 0.0)),
        skin=Key("skin", contour(top, top + belly)),
        bruised=Key("bruised", contour(top + 1.6 * dent, top + belly + 6.0 * dent)),
        cracked=Key("cracked", contour(top + 1.0 * dent, top + belly * (1 - 0.72 * notch) + 3.0 * dent)),
    )

    def frost_front(u, ka_, kb_):                 # the in-between FIELD: the skin runs left to right
        front = lerp(ICE_X0 - 30, ICE_X1 + 110, u)
        return np.clip((front - kb_.pts[:, 0]) / 90.0, 0, 1)
    return Morph("ice",
                 [(T_SKIN, K["water"], "linear"), (T_STOP, K["skin"], "linear"), (T_STAMP, K["skin"], "linear"),
                  (T_STAMP + 2 / FPS, K["bruised"], "slam"), (T_STAMP2, K["bruised"], "linear"), (T_BREAK, K["cracked"], "out")],
                 markers=[(T_STAMP + 1 / FPS, "cut", "the stamp: the bruise is there in one frame, no in-between"),
                          (T_BREAK, "split", "one slab becomes plates; each plate keeps the slab's own points")],
                 fields={"skin": frost_front})


def ice_plates_at(f):
    """After the split marker: [(polygon in world coordinates, alpha)] for each plate, tipping, drifting, sinking."""
    b = ease(f, T_BREAK, T_CLEAR)
    pts = ice_morph().keys[-1][1].pts
    tp, bt = pts[:ICE_M], pts[ICE_M:][::-1]
    out = []
    for q, (a, c) in enumerate(_plates()):
        sel = (tp[:, 0] >= a - 0.01) & (tp[:, 0] <= c + 0.01)
        if sel.sum() < 2:
            continue
        poly = np.concatenate([tp[sel], bt[sel][::-1]])
        rs = random.Random(31 + q)
        cx, cy = (a + c) / 2, 406.0
        near = math.exp(-((cx - hoof_x()) / 90.0) ** 2)
        th = math.radians(rs.uniform(7, 15) * rs.choice((-1, 1)) * (1 + 0.8 * near)) * math.sin(math.pi * min(1.0, b * 1.35)) * (1 - 0.4 * b)
        th += math.radians(rs.uniform(-5, 5)) * b
        late = clamp((b - 0.12 * rs.random()) / 0.88)
        sink = 34.0 * late ** 2.2
        dx = rs.uniform(-7, 7) * b
        ca, sa = math.cos(th), math.sin(th)
        shrink = 1 - 0.35 * ease(b, 0.55, 1.0)
        rel = (poly - (cx, cy)) * shrink
        rot = np.stack([rel[:, 0] * ca - rel[:, 1] * sa, rel[:, 0] * sa + rel[:, 1] * ca], 1) + (cx + dx, cy + sink)
        out.append((rot, 1 - ease(b, 0.5, 0.97)))
    return out


def draw_ice(ink, f, cam):
    """The skin of ice under the line, in any framing: my own drawing of it, from the ICE morph."""
    if f < T_SKIN or f >= T_CLEAR:
        return
    z = cam.zoom
    fill, edge, hi = (226, 238, 246), (128, 176, 196), (252, 254, 255)
    if f < T_BREAK:
        pts = ice_morph().at(f)
        scr = [cam.xy(x, y) for x, y in pts]
        ink.d.polygon(scr, fill=fill + (212,))
        under = scr[ICE_M:]
        ink.d.line(under, fill=edge + (255,), width=max(1, int(round(1.6 * z))))
        thick = pts[ICE_M:][::-1][:, 1] - pts[:ICE_M][:, 1]
        topl = [scr[i] for i in range(ICE_M) if thick[i] > 0.6]
        if len(topl) > 1:
            ink.d.line(topl, fill=hi + (255,), width=max(1, int(round(2.0 * z))))
        if f < T_STOP:                                  # needles of frost running ahead of the front
            u = ramp(f, T_SKIN, T_STOP)
            front = lerp(ICE_X0 - 30, ICE_X1 + 110, u)
            rs = random.Random(int(f * 12))
            for q in range(9):
                nx = front + rs.uniform(-6, 46)
                if ICE_X0 < nx < ICE_X1:
                    a = cam.xy(nx, 400.5)
                    b = cam.xy(nx + rs.uniform(6, 20), 400.5 + rs.uniform(1, 7))
                    ink.d.line([a, b], fill=hi + (230,), width=1)
        if f >= T_STAMP2:                               # the crack goes down through it at every place it will part
            hx = hoof_x()
            run = ease(f, T_STAMP2, T_BREAK)
            for q, (a_, c_) in enumerate(_plates()[1:]):
                reach_ = 1 - abs(a_ - hx) / max(hx - ICE_X0, ICE_X1 - hx)
                g = clamp((run * 1.5 - (1 - reach_)) / 0.5)
                if g <= 0:
                    continue
                i = int((a_ - ICE_X0) / (ICE_X1 - ICE_X0) * (ICE_M - 1))
                rs = random.Random(70 + q)
                seg, yy = [cam.xy(a_, 400.5)], 400.5
                while yy < 400.5 + g * (thick[i] + 1):
                    yy += 3.0
                    seg.append(cam.xy(a_ + rs.uniform(-2.5, 2.5), yy))
                ink.d.line(seg, fill=(30, 70, 100, 255), width=max(1, int(round(1.6 * z))))
        # the grain of the ice: a few short scores, fixed, so it reads as a solid thing
        rs = random.Random(9)
        for q in range(40):
            gx = rs.uniform(ICE_X0 + 8, ICE_X1 - 8)
            i = int((gx - ICE_X0) / (ICE_X1 - ICE_X0) * (ICE_M - 1))
            if thick[i] > 7:
                gy = 402.0 + rs.uniform(1, max(2.0, thick[i] - 4))
                a = cam.xy(gx, gy)
                b = cam.xy(gx + rs.uniform(5, 15), gy + rs.uniform(-1.5, 1.5))
                ink.d.line([a, b], fill=(196, 220, 232, 200), width=1)
    else:
        for poly, alpha in ice_plates_at(f):
            if alpha <= 0.02:
                continue
            scr = [cam.xy(x, y) for x, y in poly]
            ink.d.polygon(scr, fill=fill + (int(212 * alpha),))
            ink.d.line(scr + scr[:1], fill=edge + (int(255 * alpha),), width=max(1, int(round(1.4 * z))))


# ---- WOUND: fog -> (cut) star -> crack --------------------------------------------------------

WN = 32


@lru_cache(maxsize=None)
def wound_morph():
    hx = hoof_x()
    ang = [2 * math.pi * k / WN for k in range(WN)]

    def ring(cx, cy, rx, ry):
        return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in ang]
    star = []
    for k, a in enumerate(ang):
        r = 34.0 if k % 16 == 0 else 23.0 if k % 8 == 0 else 15.0 if k % 4 == 0 else 19.0 if k % 2 == 0 else 4.5
        r *= 1.0 + 0.16 * math.sin(k * 2.7)
        star.append((hx + r * math.cos(a), 400.6 + 0.3 * r * math.sin(a)))
    crack = []
    for k in range(WN):
        s = 1 - k / 8.0 if k <= 16 else -1 + (k - 16) / 8.0           # 1 .. -1 .. 1 round the contour
        x = hx + s * (ICE_X1 - hx) if s > 0 else hx + s * (hx - ICE_X0)
        side = 1 if 0 < k < 16 else -1 if k > 16 else 0
        jag = (4.6 if k % 2 else 1.0) + 1.6 * math.sin(k * 1.9)
        crack.append((x, 403.0 + side * max(0.9, jag)))
    K = dict(seed=Key("seed", ring(NOSE_X - 4, 398.4, 0.8, 0.3)), fog=Key("fog", ring(NOSE_X - 4, 397.8, 15.0, 3.6)),
             star=Key("star", star), crack=Key("crack", crack))

    def impact(pts, f, w, ka_, kb_):               # the impact frames: the star is drawn a third too big, by hand
        g = 1.42 - 0.42 * ramp(f, T_STAMP, T_STAMP + 3 / FPS)
        return np.stack([hx + (pts[:, 0] - hx) * g, 400.6 + (pts[:, 1] - 400.6) * g], 1)

    def run_out(u, ka_, kb_):                      # the field: the long arms run out first, the short ones follow
        r = np.hypot(ka_.pts[:, 0] - hx, (ka_.pts[:, 1] - 400.6) / 0.3)
        lead_ = (r - r.min()) / (r.max() - r.min())
        return np.clip(u * 1.5 - 0.5 * (1 - lead_), 0, 1)
    return Morph("wound",
                 [(T_HOLD - 0.1, K["seed"], "linear"), (T_HOLD + 0.35, K["fog"], "out"), (T_STAMP, K["fog"], "linear"),
                  (T_STAMP + 1 / FPS, K["star"], "slam"), (T_STAMP2, K["star"], "linear"), (T_BREAK, K["crack"], "out")],
                 markers=[(T_STAMP + 0.5 / FPS, "cut", "her breath's fog is under her muzzle and the star is under her hoof: "
                                                    "an in-between would slide a blob along the ice"),
                          (T_BREAK, "split", "the crack is now the edges of the plates")],
                 interventions=[(T_STAMP, T_STAMP + 3 / FPS, impact, "impact frames")],
                 fields={"crack": run_out})


def draw_wound(ink, f, cam, breathe=0.0):
    if f < T_HOLD - 0.1 or f > T_BREAK + 0.45:
        return
    m = wound_morph()
    pts = m.at(f)
    if f < T_STAMP:                                 # the fog swells with each breath out
        c = pts.mean(0)
        pts = c + (pts - c) * (1.0 + 0.22 * breathe)
    a = 1 - ease(f, T_BREAK, T_BREAK + 0.45)
    scr = [cam.xy(x, y) for x, y in pts]
    if f < T_STAMP:
        lay = Image.new("RGBA", ink.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).polygon(scr, fill=(240, 246, 250, int(150 + 60 * breathe)))
        lay = lay.filter(ImageFilter.GaussianBlur(1.6 * cam.zoom))
        ink.img.paste(lay, (0, 0), lay)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    else:
        ink.d.polygon(scr, fill=(255, 255, 255, int(255 * a)))
        ink.d.line(scr + scr[:1], fill=(40, 84, 112, int(255 * a)), width=max(1, int(round(1.5 * cam.zoom))))


# ---- REEL: the row of pieces -> through the dog's mouth -> a spiral on the spool ---------------

ROW_N = 20                                        # pieces in the row when the lead dog winds it
SPOOL_C = (566.0, 800.0)                          # where the spool stands, in the making place


def row_x(i):
    return 865.0 - 26.0 * i if i >= 8 else None


@lru_cache(maxsize=None)
def row_slots():
    """World x of every piece of the row, right to left. The first eight are where S4 left them (they are
    walked shoulder to shoulder by 126.5); the twelve the second pack adds go on leftward."""
    return [865.0 - 26.0 * i for i in range(ROW_N)]


@lru_cache(maxsize=None)
def reel_morph():
    row = [(x, LINE_Y - 13.0) for x in row_slots()]
    spiral = []
    for i in range(ROW_N):
        o = ROW_N - 1 - i                         # the left end is taken first and lies innermost
        r, th = 3.5 + 0.62 * o, 0.9 * o
        spiral.append((SPOOL_C[0] + r * math.cos(th), SPOOL_C[1] - 7.0 + 0.45 * r * math.sin(th)))
    K = dict(row=Key("row", row, closed=False), wound=Key("wound", spiral, closed=False))

    def one_by_one(u, ka_, kb_):                  # the field: the pieces go in one after another
        o = np.array([ROW_N - 1 - i for i in range(ROW_N)], float)
        return np.clip((u * (ROW_N + 5.0) - o) / 5.0, 0, 1)

    def by_mouth(pts, f, w, ka_, kb_):            # the intervention: a straight in-between would drag the film
        m = np.array(lead_mouth(f))               # through the fence; it goes by way of the dog's mouth instead
        out = np.empty_like(pts)
        for i in range(len(pts)):
            wi = w[i]
            if wi < 0.5:
                out[i] = ka_.pts[i] + (m - ka_.pts[i]) * smooth(wi * 2)
            else:
                out[i] = m + (kb_.pts[i] - m) * smooth(wi * 2 - 1)
        return out
    return Morph("reel", [(T_WIND, K["row"], "linear"), (T_LID, K["wound"], "linear")],
                 interventions=[(T_WIND, T_LID, by_mouth, "via the dog's mouth")], fields={"wound": one_by_one})


def reel_weights(f):
    m = reel_morph()
    if f <= T_WIND:
        return np.zeros(ROW_N)
    if f >= T_LID:
        return np.ones(ROW_N)
    return m.fields["wound"](ramp(f, T_WIND, T_LID), None, None)


# ====================================================================== #
#  2 · WHO IS WHERE: the second pack, the eleven, the first pack         #
# ====================================================================== #

ROOF = [(594, 696), (606, 676), (660, 654), (750, 641), (840, 646), (892, 664), (904, 696)]   # the school's hull roof


def roof_y(x):
    for (xa, ya), (xb, yb) in zip(ROOF, ROOF[1:]):
        if xa <= x <= xb:
            u = (x - xa) / (xb - xa)
            return lerp(ya, yb, smooth(u) * 0.5 + u * 0.5) - 1.5
    return 696.0


ROOF_X = [622, 646, 668, 692, 716, 786, 808, 830, 852, 874, 893]          # eleven places, either side of the belfry
ROOF_WHO = ["looker", "looker", "terrier", "looker", "looker", "terrier", "looker", "terrier", "looker", "looker", "terrier"]
HEAP = [(716, 401), (746, 402), (776, 401), (806, 402), (836, 401), (866, 402), (731, 395), (761, 396), (791, 395), (821, 396), (851, 395)]
BASE_SC = dict(looker=0.28, terrier=0.68, herder=0.42, digger=0.56, retr=0.27, sheep=0.27, blood=0.28, felt=0.62)
CARRY = dict(retr="piece", sheep="part", blood="page", herder="page", digger="part", felt="fix")
RISE = 1.3                                        # seconds from the bed to the line


@lru_cache(maxsize=None)
def crowd():
    """The second pack: 51 dogs, no two alike (make, size, seed). Eleven of them only look or mend:
    seven grey-muzzled lookers and four terriers. Each is a dict of where it is all sequence long."""
    rs = random.Random(51)
    makes = ["herder"] * 9 + ["digger"] * 7 + ["retr"] * 9 + ["sheep"] * 5 + ["blood"] * 6 + ["felt"] * 4
    rs.shuffle(makes)
    eleven = list(ROOF_WHO)
    order = makes[:10] + eleven[:4] + makes[10:24] + eleven[4:8] + makes[24:34] + eleven[8:] + makes[34:]
    assert len(order) == 51
    left = {1, 9, 20, 27, 38, 47}                 # six wait on the wet end of the sill, the rest along the meadow side
    out, nl, nr, ne = [], 0, 0, 0
    drops = sorted(T_CLEAR + 0.05 + 2.05 * rs.random() ** 1.15 for _ in range(51))
    drop_of = list(range(51))
    rs.shuffle(drop_of)
    for k, mk in enumerate(order):
        d = dict(k=k, make=mk, seed=rs.randrange(1 << 20), size=rs.choice(("big", "mid", "small")),
                 sc=BASE_SC[mk] * rs.uniform(0.82, 1.16), eleven=None)
        if mk in ("looker", "terrier") and k not in left:
            d["eleven"] = ne
            ne += 1
        if k in left:
            d.update(side="L", pad=(308.0 + 17.0 * nl, 400.5), x_from=240.0 - 12.0 * nl)
            nl += 1
        else:
            row = nr % 3
            d.update(side="R", pad=(814.0 + 3.05 * nr + 2.0 * row, 400.5 - 4.5 * row), x_from=985.0 + 2.5 * nr)
            nr += 1
        d["t_pad"] = T_SPLIT + 0.75 + 0.044 * (k // 3) + 0.012 * (k % 3)
        d["t_drop"] = drops[drop_of[k]]
        d["gap"] = rs.uniform(312, 574) if d["side"] == "L" else rs.uniform(604, 948)
        if d["eleven"] is not None:
            e = d["eleven"]
            d["spot"] = (float(ROOF_X[e]), roof_y(ROOF_X[e]))
            d["t_out"] = T_OUT + (0.0 if e == 0 else 0.55 + 0.12 * e if e < 3 else 1.0 + 0.06 * e)
            d["t_surf"] = T_UP + 0.04 + 0.085 * [5, 2, 8, 0, 10, 3, 7, 1, 9, 4, 6][e]
            d["surf_x"] = 664.0 + 21.5 * e
            d["heap"] = HEAP[e]
        else:
            band = rs.random()
            if band < 0.45:
                d["spot"] = (rs.uniform(60, 500), rs.uniform(809, 822))
            elif band < 0.85:
                d["spot"] = (rs.uniform(90, 590), rs.uniform(846, 866))
            else:
                d["spot"] = (rs.uniform(884, 940), rs.uniform(814, 860))
            d["carry"] = CARRY[mk]
        d["t_land"] = d["t_drop"] + math.hypot(d["spot"][0] - d["gap"], d["spot"][1] - 406.0) / 300.0
        out.append(d)
    workers = sorted((d for d in out if d["eleven"] is None), key=lambda d: d["t_land"])
    for r, d in enumerate(workers):
        d["t_leave"] = max(T_LATER - 0.5 + 3.9 * r / (len(workers) - 1), d["t_land"] + 0.9)
        d["exit"] = (max(318.0, d["spot"][0] - 130.0), 398.0)
    return out


def crowd_state(d, f):
    """-> (where, mode, x, y, facing, tau, pitch, carry) or None. where: ice | fall | bed | roof | rise | up |
    surface | haul | heap."""
    if f < max(T_SPLIT, d["t_pad"] - 0.7):
        return None
    px, py = d["pad"]
    if f < d["t_drop"]:
        u = ease(f, d["t_pad"] - 0.7, d["t_pad"])
        fac = -1 if d["side"] == "R" else 1
        if u < 1:
            return ("ice", "walk", lerp(d["x_from"], px, u), py, fac, f - d["t_pad"], 0.0, None)
        bob = 0.0
        if f > T_BREAK:                                     # the plate under it tips
            bob = 3.0 * math.sin((f - T_BREAK) * 7 + d["k"]) * ease(f, T_BREAK, T_BREAK + 0.5)
        return ("ice", "stand", px, py + bob, fac, 0.0 if f < T_STAMP else f - T_STAMP, 0.0, None)
    sx_, sy_ = d["spot"]
    if f < d["t_land"]:
        u = ramp(f, d["t_drop"], d["t_land"])
        x = lerp(d["gap"], sx_, smooth(u)) + 5 * math.sin((f - d["t_drop"]) * 6 + d["k"])
        return ("fall", "sink", x, lerp(408.0, sy_ - 8, u ** 0.85), 1 if sx_ >= d["gap"] else -1, f - d["t_drop"], 0.0, None)
    if d["eleven"] is not None:
        if f < d["t_out"]:
            return ("roof", "sit", sx_, sy_, -1, f - d["t_land"], 0.0, None)
        if f < d["t_surf"]:
            tau = f - d["t_out"]
            u = clamp((tau - 0.45) / max(0.2, d["t_surf"] - d["t_out"] - 0.45))
            return ("up", "float", lerp(sx_, d["surf_x"], smooth(u)), lerp(sy_, 405.0, u ** 1.7), -1, tau, 0.0, None)
        tau = f - d["t_surf"]
        hx_, hy_ = d["heap"]
        t_h = 0.55 + 0.05 * d["eleven"]
        if tau < t_h:
            return ("surface", "surface", d["surf_x"], 401.0, 1 if hx_ > d["surf_x"] else -1, tau, 0.0, None)
        if tau < t_h + 0.9:
            u = ease(tau, t_h, t_h + 0.9)
            return ("haul", "walk", lerp(d["surf_x"], hx_, u), lerp(401.0, hy_, u ** 0.6), 1 if hx_ > d["surf_x"] else -1, tau, 0.0, None)
        return ("heap", "wet", hx_, hy_, 1 if d["eleven"] % 2 else -1, tau - t_h - 0.9, 0.0, None)
    if f < d["t_leave"]:
        return ("bed", "work", sx_, sy_, 1 if d["k"] % 2 else -1, f - d["t_land"], 0.0, None)
    u = (f - d["t_leave"]) / RISE
    if u >= 1:
        return None
    ex, ey = d["exit"]
    return ("rise", "swim", lerp(sx_, ex, u), lerp(sy_ - 10, ey, smooth(u) * 0.4 + u * 0.6), -1, f - d["t_leave"], 0.95, d["carry"])


# ---- drawing any make of dog in any of a few modes -------------------------------------------

def _redraw(ink):
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _layered(ink, fn, cx, cy, ang=0.0, R=90, halo=None):
    """Draw with fn(layer) on a clear sheet, turn it by `ang` about (cx, cy) and lay it down (with a pale
    edge first if halo): for the makes that cannot pitch themselves, and for black card on dark water."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out = fn(layer)
    box = (int(cx - R), int(cy - R), int(cx + R), int(cy + R))
    part = layer.crop(box)
    if abs(ang) > 0.01:
        part = part.rotate(math.degrees(ang), resample=Image.BICUBIC)
    if halo:
        m = part.getchannel("A").filter(ImageFilter.MaxFilter(3)).point(lambda v: int(v * halo[3] / 255))
        edge = Image.new("RGBA", part.size, tuple(halo[:3]) + (0,))
        edge.putalpha(m)
        ink.img.paste(edge, box[:2], edge)
    ink.img.paste(part, box[:2], part)
    _redraw(ink)
    return out


def _thing_at(ink, kind, a, sc, under, facing=1):
    if not a or "mouth" not in a:
        return
    mx, my = a["mouth"]
    if kind == "shell":
        r = 5.0 * sc
        ink.d.ellipse([mx - r, my - r * 0.7, mx + r, my + r * 0.7], fill=(236, 242, 232, 255), outline=(40, 70, 76, 255))
    else:
        kb.draw_thing(ink, kind, mx + 2 * facing, my + 10 * sc, sc, angle=0.25 * facing, stand=False, **(UNDER if under else {}))


def draw_make(ink, make, x, y, sc, facing, mode, tau, *, size="big", carry=None, under=True, pitch=0.0, seed=0, lookup=0.0):
    """One dog of any make at SCREEN (x, y). mode: stand | walk | work | sit | sink | swim | float | surface | wet."""
    U = UNDER if under else {}
    ph = (seed % 97) / 97.0
    if make == "retr":
        kw = dict(scale=sc, facing=facing, size=size, **U)
        if mode == "stand":
            return kb.retriever(ink, x, y, "wait", 3.0 + tau, arrive=0, look=lookup, **kw)
        if mode == "walk":
            return kb.retriever(ink, x, y, "walk", tau + ph, **kw)
        if mode == "work":
            return kb.retriever(ink, x, y, "set_down", (tau + ph * 2.5) % 2.5, carry="piece", **kw)
        if mode == "sink":
            return kb.retriever(ink, x, y, "swim", tau + ph, pitch=0.25, **kw)
        return kb.retriever(ink, x, y, "swim", tau + ph, pitch=pitch, carry=carry, **kw)
    if make == "sheep":
        kw = dict(scale=sc, facing=facing, **U)
        if mode == "stand":
            return kb.sheepdog(ink, x, y, "wait", 4.0 + tau, **kw)
        if mode == "walk":
            return kb.sheepdog(ink, x, y, "walk", tau + ph, **kw)
        if mode == "work":
            return kb.sheepdog(ink, x, y, "nudge", (tau + ph * 2.6) % 2.6, **kw)
        if mode == "sink":
            return kb.sheepdog(ink, x, y, "swim", tau + ph, pitch=0.2, **kw)
        return kb.sheepdog(ink, x, y, "swim", tau + ph, pitch=pitch, carry=carry, **kw)
    if make == "blood":
        kw = dict(scale=sc, facing=facing, **U)
        if mode == "stand":
            return kb.bloodhound(ink, x, y, "wait", 9.0, sit=False, look=lookup, **kw)
        if mode == "walk":
            return kb.bloodhound(ink, x, y, "walk", tau + ph, **kw)
        if mode == "work":
            return kb.bloodhound(ink, x, y, "nose_down", min(2.0, (tau + ph * 3.0) % 3.0), **kw)
        if mode == "sink":
            return kb.bloodhound(ink, x, y, "swim", tau + ph, pitch=0.2, **kw)
        return kb.bloodhound(ink, x, y, "swim", tau + ph, pitch=pitch, carry=carry, **kw)
    if make == "terrier":
        kw = dict(scale=sc, facing=facing, **U)
        if mode in ("stand", "sit"):
            return kb.terrier(ink, x, y, "wait", 0.6, sit=(mode == "sit"), **kw)
        if mode == "walk":
            return kb.terrier(ink, x, y, "walk", tau + ph, **kw)
        if mode == "float":
            return kb.terrier(ink, x, y, "breath_out", tau, **kw)
        if mode == "surface":
            return kb.terrier(ink, x, y, "surface", tau, **kw)
        if mode == "wet":
            return kb.terrier(ink, x, y, "warm", tau, cow=facing, **kw)
        return kb.terrier(ink, x, y, "swim", tau + ph, rot=-pitch * facing if mode == "swim" else 0.0, carry=carry, **kw)
    if make == "felt":
        if mode in ("stand", "walk"):
            S4.felt_dog(ink, x, y, sc, facing, lift=1.0, ear=1.0, hop=abs(math.sin((tau + ph) * 9)) if mode == "walk" else 0.0, under=under)
        elif mode == "work":
            S4.felt_dog(ink, x, y, sc, facing, lift=0.0, ear=0.0, paw=bump(((tau + ph * 2) % 2.0) / 0.8), under=under)
        else:
            S4.felt_dog(ink, x, y + 12 * sc, sc, facing, lift=1.0, ear=1.0 + 0.3 * math.sin(tau * 9), rot=-pitch * facing * 0.8, under=under)
        a = dict(mouth=(x + facing * 30 * sc * math.cos(pitch), y - 16 * sc - 30 * sc * math.sin(pitch)))
        if carry and mode == "swim":
            _thing_at(ink, "shell", a, sc * 0.5, under)
        return a
    if make == "herder":
        halo = (150, 214, 206, 125) if under else (206, 176, 226, 140)
        if mode == "stand":
            return _layered(ink, lambda L: ka.herding_dog(L, x, y, sc, facing, "wait", t=tau + ph * 5, look=math.degrees(lookup)), x, y - 14, halo=halo)
        if mode == "walk":
            return _layered(ink, lambda L: ka.herding_dog(L, x, y, sc, facing, "walk", t=tau + ph), x, y - 14, halo=halo)
        if mode == "work":
            return _layered(ink, lambda L: ka.herding_dog(L, x, y, sc, facing, "gather", p=((tau + ph * 1.8) % 1.8) / 1.8, pages=1), x, y - 14, halo=halo)
        ang = facing * pitch * 0.8 if mode == "swim" else facing * 0.1
        return _layered(ink, lambda L: ka.herding_dog(L, x, y, sc, facing, "swim", t=tau + ph, pages=1 if carry else 0), x, y, ang=ang, halo=halo)
    if make == "digger":
        if mode == "stand":
            return ka.digger(ink, x, y, sc, facing, "wait", look=math.degrees(lookup))
        if mode == "walk":
            return ka.digger(ink, x, y, sc, facing, "walk", t=tau + ph)
        if mode == "work":
            return ka.digger(ink, x, y, sc, facing, "dig", t=tau + ph)
        ang = facing * pitch * 0.8 if mode == "swim" else facing * 0.1
        a = _layered(ink, lambda L: ka.digger(L, x, y, sc, facing, "swim", t=tau + ph), x, y, ang=ang)
        if carry and mode == "swim":
            ca, sa = math.cos(-ang), math.sin(-ang)
            mx, my = a["mouth"][0] - x, a["mouth"][1] - y
            kb.draw_thing(ink, "part", x + mx * ca - my * sa, y + mx * sa + my * ca + 7 * sc, sc * 0.55, stand=False, **U)
        return a
    if make == "looker":                                     # a small cousin of the old dog: the same engraving, small
        paper = (176, 186, 184) if under else (190, 188, 182)
        kw = dict(paper=paper)
        if mode == "sit":
            p = clamp(tau / 0.6)
            if p < 1:
                return ka.old_dog(ink, x, y, sc, facing, "lie_down", p=p, **kw)
            return ka.old_dog(ink, x, y, sc, facing, "look", p=0.0, **kw)
        if mode in ("stand",):
            return ka.old_dog(ink, x, y, sc, facing, "wait", **kw)
        if mode == "walk":
            return ka.old_dog(ink, x, y, sc, facing, "walk", t=int((tau + ph) * 8) / 8.0, **kw)
        if mode == "wet":
            p = clamp(tau / 0.7)
            if p < 1:
                return ka.old_dog(ink, x, y, sc, facing, "lie_down", p=p, **kw)
            return ka.old_dog(ink, x, y, sc, facing, "lie", eye=0 if tau > 4.0 else None, **kw)
        return ka.old_dog(ink, x, y, sc, facing, "swim", t=int((tau + ph) * 8) / 8.0, look=30 if mode in ("float", "surface") else 0, **kw)
    raise ValueError(make)


def draw_crowd_dog(ink, d, f, cam, st=None):
    st = st or crowd_state(d, f)
    if not st:
        return
    where, mode, wx, wy, fac, tau, pitch, carry = st
    z = cam.zoom
    sx, sy = cam.xy(wx, wy)
    under = where in ("fall", "bed", "roof", "rise", "up")
    sc = d["sc"] * z
    if where == "heap" and d["make"] == "looker":
        sx += 1.2 * math.sin(f * 61 + d["k"]) * (1 - ease(tau, 0.6, 2.6))          # the shaking, and it stopping
    if where == "roof" and d["eleven"] == 6 and 129.8 < f < 130.7:               # one of them goes cross-eyed and wobbles
        sx += 2.2 * math.sin((f - 129.8) * 19)
    a = draw_make(ink, d["make"], sx, sy, sc, fac, mode, tau, size=d["size"], carry=carry, under=under, pitch=pitch, seed=d["seed"])
    if where == "up" and d["make"] == "looker":                                  # its breath: one big bubble, let go
        _breath_bubble(ink, a, tau, sc / BASE_SC["looker"] * 0.5)
    if where == "roof" and f > T_LATER and a and "mouth" in a:                   # cheeks full
        mx, my = a["mouth"]
        r = (1.5 + 0.5 * ease(f, T_LATER, T_OUT)) * z
        ink.d.ellipse([mx - r + 2 * fac, my - r - 1, mx + r + 2 * fac, my + r - 1], fill=(206, 212, 206, 235) if d["make"] == "looker" else (190, 160, 110, 235),
                      outline=(30, 40, 46, 255))
    return a


def _breath_bubble(ink, a, tau, s):
    if not a or "mouth" not in a:
        return
    mx, my = a["mouth"]
    if tau < 0.45:
        r = 9.0 * s * ease(tau, 0.05, 0.45)
        cx, cy = mx - 4 * s, my - r
    else:
        r = 9.0 * s
        cx, cy = mx - 4 * s + 5 * math.sin(tau * 5), my - r - 150.0 * s * (tau - 0.45) ** 1.3
    if r > 0.5 and cy > -10:
        ink.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(206, 236, 232, 60), outline=(232, 248, 244, 235), width=max(1, int(1.5 * s)))
        ink.d.arc([cx - r * 0.6, cy - r * 0.6, cx + r * 0.2, cy + r * 0.2], 190, 260, fill=(255, 255, 255, 235), width=1)


# ---- the first pack after the ice: each goes on from where it stopped, finishes, and goes up with its thing ----

LEAVE = dict(small=127.3, terrier=127.75, mid=128.15, herder=128.65, digger=129.1, blood=129.55, big=129.95, sheep=130.35, felt=130.75)
PACK9 = ("herder", "digger", "big", "mid", "small", "sheep", "blood", "terrier", "felt")


@lru_cache(maxsize=None)
def start_state():
    """Where S4 left everybody at its stopped clock (world coordinates), read from S4's own state functions."""
    w = S4.works()
    out = {}
    for nm in ("big", "mid", "small"):
        x, y, ph, tau, fac = w.retriever(nm, FS)
        out[nm] = dict(x=x, y=y, phase=ph, tau=tau, facing=fac)
    x, y, ph, tau, moving, dd = w.sheep(FS)
    out["sheep"] = dict(x=x, y=y, phase=ph, tau=tau, push=dd)
    out["blood"] = S4.blood_town(FS)
    out["herder"] = S4.herder_town(FS)
    for nm, ag in (("lead", S4.lead_agenda()), ("digger", S4.digger_agenda()), ("terrier", S4.terrier_agenda())):
        seg, tau, u, x, y = ag.at(FS)
        out[nm] = dict(x=x, y=y, kind=seg.kind, tau=tau, facing=seg.facing, a=seg.a)
    out["felt"] = dict(x=S4.FELT_AT[0], y=S4.FELT_AT[1])
    out["pieces"] = sorted(S4.piece_x(s_) for _, s_, _ in w.pieces_at(FS))[::-1]      # right to left
    return out


def _seq(tau, steps):
    """steps = [(dur, name)]; -> (index, name, time into it, 0..1)."""
    for i, (dur, name) in enumerate(steps):
        if tau < dur or i == len(steps) - 1:
            return i, name, tau, clamp(tau / dur) if dur > 0 else 1.0
        tau -= dur
    return len(steps) - 1, steps[-1][1], tau, 1.0


def pack_state(nm, f):
    """One of the first pack between T_GOON and when it has gone up. -> dict(x, y, facing, call, rise) or None.
    `call` is (function name, args) for draw_pack; world coordinates."""
    s0 = start_state()[nm]
    tl = LEAVE[nm]
    t = f - T_GOON
    if f >= tl + RISE:
        return None

    def rising(x, y, carry):
        u = (f - tl) / RISE
        return dict(x=lerp(x, max(318.0, x - 130.0), u), y=lerp(y - 12, 398.0, smooth(u) * 0.4 + u * 0.6), facing=-1, mode="swim",
                    tau=f - tl, carry=carry, pitch=0.95)
    if nm in ("big", "mid", "small"):
        side = S4.STOCK[nm][2]
        lamp = S4.LAMP_AT[nm]
        v = S4.RET_V[nm]
        if nm == "big":                                    # it was rolling back to its lamp; takes a piece; carries it slowly
            d0 = math.hypot(lamp[0] - s0["x"], lamp[1] - s0["y"]) / v
            i, name, tau, u = _seq(t, [(d0, "back"), (0.5, "pick"), (99, "carry")])
            if f >= tl:
                x = lamp[0] + v * (tl - T_GOON - d0 - 0.5)
                return rising(x, S4.LANE[nm], "piece")
            if name == "back":
                return dict(x=lerp(s0["x"], lamp[0], u), y=lerp(s0["y"], lamp[1], u), facing=-1, call=("walk", {}), roll=f)
            if name == "pick":
                return dict(x=lamp[0], y=lamp[1], facing=side, call=("wait", dict(arrive=0, carry="piece" if tau > 0.25 else None)), roll=tau)
            return dict(x=lamp[0] + v * tau, y=lerp(lamp[1], S4.LANE[nm], ease(tau, 0, 0.8)), facing=1, call=("carry", dict(carry="piece")), roll=f)
        t_set = (1.6 if nm == "small" else 1.9) - s0["tau"]  # finishes setting its piece down, head comes up
        d1 = math.hypot(lamp[0] - s0["x"], lamp[1] - s0["y"]) / v
        i, name, tau, u = _seq(t, [(t_set, "set"), (d1, "back"), (99, "pick")])
        if f >= tl:
            return rising(lamp[0], lamp[1], "piece")
        if name == "set":
            tt = s0["tau"] + tau
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("set_down", dict(carry="piece" if tt < 1.0 else None)), roll=min(tt, 0.98) if tt < 1.0 else tt)
        if name == "back":
            return dict(x=lerp(s0["x"], lamp[0], u), y=lerp(s0["y"], lamp[1], u), facing=-1 if lamp[0] < s0["x"] else 1, call=("walk", {}), roll=f)
        return dict(x=lamp[0], y=lamp[1], facing=side, call=("wait", dict(arrive=0, carry="piece" if tau > 0.25 else None)), roll=tau)
    if nm == "sheep":
        t_n = 2.6 - s0["tau"]
        x1 = row_slots()[ROW_N - 1] + 30.0
        d1 = abs(s0["x"] - x1) / (RS * 254.0 * 0.5)
        i, name, tau, u = _seq(t, [(t_n, "nudge"), (d1, "run"), (99, "nudge2")])
        if f >= tl:
            return rising(x1, s0["y"], "piece")
        if name == "nudge":
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("nudge", dict(push=s0["push"] / (RS * kb.UNIT["sheepdog"]))), roll=s0["tau"] + tau)
        if name == "run":
            return dict(x=lerp(s0["x"], x1, u), y=s0["y"], facing=-1, call=("walk", {}), roll=f * 1.6)
        return dict(x=x1, y=s0["y"], facing=1, call=("nudge", {}), roll=tau % 2.6)
    if nm == "blood":
        if f >= tl:
            return rising(s0["x"] - 18.0 * (tl - T_GOON), s0["y"], "page")
        return dict(x=s0["x"] - 18.0 * t, y=s0["y"], facing=-1, call=("follow", {}), roll=s0["t"] + t)
    if nm == "herder":
        mp = (536.0, 812.0)
        i, name, tau, u = _seq(t, [(0.25, "wait"), (0.9, "carry"), (0.7, "lay"), (0.9, "home"), (99, "wait2")])
        if f >= tl:
            return rising(s0["x"], s0["y"], "page")
        if name == "wait":
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("wait", dict(pages=3)), roll=f)
        if name == "carry":
            return dict(x=lerp(s0["x"], mp[0], u), y=lerp(s0["y"], mp[1], u), facing=-1, call=("carry", dict(pages=3)), roll=f)
        if name == "lay":
            return dict(x=mp[0], y=mp[1], facing=-1, call=("gather", dict(p=0.42 * (1 - u), pages=3 if u < 0.5 else 1)), roll=f)
        if name == "home":
            return dict(x=lerp(mp[0], s0["x"], u), y=lerp(mp[1], s0["y"], u), facing=1, call=("circle", dict(pages=1)), roll=f)
        return dict(x=s0["x"], y=s0["y"], facing=1, call=("wait", dict(pages=1)), roll=f)
    if nm == "digger":
        hp = (470.0, 813.0)
        i, name, tau, u = _seq(t, [(0.2, "wait"), (0.6, "go"), (tl - T_GOON - 1.4, "dig"), (0.6, "heave")])
        if f >= tl:
            return rising(hp[0], hp[1], "part")
        if name == "wait":
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("wait", {}), roll=f)
        if name == "go":
            return dict(x=lerp(s0["x"], hp[0], u), y=lerp(s0["y"], hp[1], u), facing=-1, call=("walk", {}), roll=f)
        if name == "dig":
            return dict(x=hp[0], y=hp[1], facing=-1, call=("dig", {}), roll=tau)
        return dict(x=hp[0], y=hp[1], facing=-1, call=("heave", dict(p=0.2 + 0.8 * u)), roll=f, thing="part")
    if nm == "terrier":
        i, name, tau, u = _seq(t, [(0.5, "tail"), (2.2, "up"), (99, "stand")])
        if f >= tl:
            return rising(s0["x"] + 14, s0["y"], "fix")
        if name == "tail":
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("dive", dict(stay=True)), roll=1.6 + s0["tau"] + tau)
        if name == "up":
            return dict(x=s0["x"], y=s0["y"], facing=1, call=("come_up", dict(carry="fix")), roll=tau)
        return dict(x=s0["x"], y=s0["y"], facing=1, call=("come_up", dict(carry="fix")), roll=2.2)
    if nm == "felt":
        if f >= tl:
            return rising(s0["x"] - 10, s0["y"], "shell")
        return dict(x=s0["x"], y=s0["y"], facing=-1, call=("felt", dict(lift=ease(f, tl - 0.6, tl - 0.15))), roll=f)
    raise ValueError(nm)


def draw_pack(ink, nm, f, cam):
    st = pack_state(nm, f)
    if not st:
        return
    z = cam.zoom
    sx, sy = cam.xy(st["x"], st["y"])
    fac = st["facing"]
    if "mode" in st:                                          # going up with its thing
        make = dict(big="retr", mid="retr", small="retr", sheep="sheep", blood="blood", herder="herder", digger="digger",
                    terrier="terrier", felt="felt")[nm]
        sc = dict(retr=RS, sheep=RS, blood=RS, herder=HS, digger=GS, terrier=TS, felt=1.0)[make] * z
        draw_make(ink, make, sx, sy, sc, fac, "swim", st["tau"], size=nm, carry=st["carry"], pitch=st["pitch"])
        return
    act, kw = st["call"]
    roll = st["roll"]
    if nm in ("big", "mid", "small"):
        if act in ("walk", "carry"):
            roll = f * S4.RET_V[nm] / (RS * 75.0 * kb.RET_SIZE[nm])
        kb.retriever(ink, sx, sy, act, roll, scale=RS * z, size=nm, facing=fac, **UNDER, **kw)
    elif nm == "sheep":
        kb.sheepdog(ink, sx, sy, act, roll, scale=RS * z, facing=fac, **UNDER, **kw)
    elif nm == "blood":
        kb.bloodhound(ink, sx, sy, act, roll, scale=RS * z, facing=fac, **UNDER, **kw)
    elif nm == "herder":
        _layered(ink, lambda L: ka.herding_dog(L, sx, sy, HS * z, fac, act, t=roll, **kw), sx, sy - 16, halo=(150, 214, 206, 130))
    elif nm == "digger":
        a = ka.digger(ink, sx, sy, GS * z, fac, act, t=roll, **kw)
        if st.get("thing") and a and a.get("out", 1):
            props.part(ink, a["mouth"][0], a["mouth"][1] + 6 * z, 0.5 * z, "crank", t=f, **props.UNDER)
    elif nm == "terrier":
        kb.terrier(ink, sx, sy, act, roll, scale=TS * z, facing=fac, **UNDER, **kw)
    elif nm == "felt":
        S4.felt_dog(ink, sx, sy, z, fac, lift=kw["lift"], ear=kw["lift"], under=True)


ROW_ADD = [125.7 + 0.37 * i for i in range(ROW_N - 8)]     # when the second pack stands each new piece in the row


def row_pieces(f):
    """[(world x, lean)] of the pieces standing in the row at f (before the lead dog winds them)."""
    old = start_state()["pieces"]
    slots = row_slots()
    u = ease(f, T_GOON + 0.2, 126.5)                        # the sheepdog walks the first eight shoulder to shoulder
    out = [(lerp(old[i], slots[i], u), 0.06 * (1 - u) * (1 if i % 2 else -1)) for i in range(8)]
    for i, ta in enumerate(ROW_ADD):
        if f >= ta:
            out.append((slots[8 + i], -0.5 * (1 - ease(f, ta, ta + 0.3))))
    return out


def holes_at(f):
    return 40.0 + 160.0 * ramp(f, T_GOON + 0.5, T_OUT)


def smudges_at(f):
    return int(30 + 60 * ramp(f, T_GOON + 0.5, T_OUT))


# ====================================================================== #
#  3 · THE LEAD DOG                                                      #
# ====================================================================== #

SPOOL_AT = (411.0, 808.0)                    # where S2 left the spool, at the foot of the notice board
MAKE_AT = (538.0, 806.0)                     # where the lead dog stands in the making place
LAND = (440.0, 394.0)                        # where it stands on the sill at the end (board)
BREACH_X = 596.0


@lru_cache(maxsize=4096)
def _probe(key, facing=1, scale=DS):
    """Offsets of nose and mouth from the anchor for a pose, by drawing it once on scratch paper."""
    name, tq, extra = key
    pose = _pose(name, tq, extra)
    j = dog.draw_dog(Image.new("RGB", (400, 400)), pose, 200, 200, scale=scale, facing=facing, shadow=False, texture=False, ss=1)
    return (j["nose"][0] - 200, j["nose"][1] - 200), (j["mouth"][0] - 200, j["mouth"][1] - 200)


def _pose(name, tq, extra=0.0):
    if name == "float":
        return dog.look_up(dog.wait_float(tq), extra)
    if name == "startle":
        return dog.startle(tq)
    if name == "stand":
        return dog.stand(tq)
    raise ValueError(name)


FLOAT_NOSE = (NOSE_X, 400.0 + ICE_TH + 2.5)


def _float_xy(f):
    """The body point that puts the floating dog's nose against the underside of the ice."""
    tq = round(f * FPS) / FPS
    (nx, ny), _ = _probe(("float", round(tq, 4), 1.0))
    return FLOAT_NOSE[0] - nx, FLOAT_NOSE[1] - ny


def _circle(f):
    """The lead dog winding: twice and a half round the spool. -> (x, y, facing, behind)."""
    u = ramp(f, T_WIND + 0.15, T_LID - 0.1)
    ph = math.pi + 2 * math.pi * 2.5 * smooth(u) * 0.3 + 2 * math.pi * 2.5 * u * 0.7
    x = SPOOL_C[0] + 46.0 * math.cos(ph)
    y = 806.0 + 9.0 * math.sin(ph)
    fac = clamp(-math.sin(ph) * 3.0, -1, 1)
    if abs(fac) < 0.3:
        fac = 0.3 if fac >= 0 else -0.3
    return x, y, fac, math.sin(ph) < 0


def lead_state(f):
    """-> dict(pose, x, y (world), facing, carry, layer in under|front|sill, bits, anchor)."""
    out = dict(carry=None, layer="under", bits=None, anchor=None, facing=1)
    s0 = start_state()["lead"]
    bx, by = s0["x"], s0["y"]
    if f < 118.9:
        return None                                           # S4 draws it (its nose at a page on the board)
    if f < 119.25:                                            # it stops; its head comes up: what is that, up there?
        u = ease(f, 118.9, 119.2)
        p = dog.blend(dog.nose_page(min(s0["tau"], 1.9)), dog.look_up(dog.stand(0.0), 1.0), {"ears": ease(f, 118.9, 119.0), "head": u, "tail": u, "body": u * 0.6, "legs": 0.0})
        return dict(out, pose=p, x=bx, y=by)
    fx, fy = _float_xy(max(f, T_NOSE))
    if f < T_NOSE:                                            # up, toward the dark shape on the ice
        u = ramp(f, 119.25, T_NOSE)
        e = 1 - (1 - u) ** 2.2
        x = lerp(bx + 14, fx, e ** 1.25)
        y = lerp(by - 34, fy, e)
        p = dog.blend(dog.swim_up(f, steep=0.7), dog.look_up(dog.wait_float(f), 1.0), ease(u, 0.72, 1.0))
        return dict(out, pose=p, x=x, y=y, anchor="body")
    if f < T_STAMP:                                           # nose to the underside of the ice, and held
        tq = round(f * FPS) / FPS
        return dict(out, pose=dog.look_up(dog.wait_float(tq), 1.0), x=fx, y=fy, anchor="body")
    if f < 123.55:                                            # the stamp: ducks, ears flat; then looks up; the tail starts
        tau = f - T_STAMP
        duck = 16.0 * (1 - math.exp(-tau * 14)) * (1 - 0.45 * ease(tau, 0.7, 1.4))
        return dict(out, pose=dog.startle(tau), x=fx - 3 * (1 - math.exp(-tau * 14)), y=fy + duck, anchor="body")
    fx2, fy2 = fx - 3, fy + 16.0 * 0.55
    if f < 125.15:                                            # the ice is gone: back down to the work
        u = ramp(f, 123.55, 125.15)
        e = smooth(u)
        x = lerp(fx2, MAKE_AT[0] + 6, e)
        y = lerp(fy2, MAKE_AT[1] - 26, e ** 0.9)
        turn = lerp(1.0, -1.0, ease(f, 123.55, 123.85))
        if abs(turn) < 0.3:
            turn = 0.3 if turn > 0 else -0.3
        p = dog.blend(dog.wait_float(f), dog.swim_down(f, steep=0.78), ease(u, 0.05, 0.25))
        p = dog.blend(p, dog.swim(f), ease(u, 0.85, 1.0))
        return dict(out, pose=p, x=x, y=y, facing=turn, anchor="body")
    mx, my = MAKE_AT
    if f < T_ALONE - 0.4:                                     # at the making place: digging, looking, setting down
        t = f - 125.15
        if t < 0.45:
            return dict(out, pose=dog.blend(dog.dig(t), dog.stand(f), ease(t, 0.25, 0.45)), x=mx, y=my, facing=-1)
        cyc = (t - 0.45) % 3.4
        if cyc < 0.9:
            return dict(out, pose=dog.look_up(dog.watch(f), 0.55 if f < T_LATER else 0.0), x=mx, y=my, facing=-1)
        if cyc < 2.1:
            return dict(out, pose=dog.dig(cyc - 0.9), x=mx, y=my, facing=-1, bits=dog.dig_spray(cyc - 0.9, water=True))
        if cyc < 2.6:
            return dict(out, pose=dog.blend(dog.dig(1.2), dog.stand(f), ease(cyc, 2.1, 2.4)), x=mx, y=my, facing=-1)
        return dict(out, pose=dog.paw_press((cyc - 2.6) * 1.8), x=mx, y=my, facing=-1)
    # ---- alone ----
    (_, _), (tmx, tmy) = _probe(("stand", 0.0, 0.0))
    xs = SPOOL_AT[0] - tmx - 4                                 # where it stands to take the spool
    if f < 137.3:                                             # takes the spool from the foot of the board
        tau = clamp((f - 136.55) * 1.45, 0, 1.8)
        return dict(out, pose=dog.take_page(tau), x=xs, y=806.0, carry=_spool_sprite(f))
    xw = SPOOL_C[0] - 46.0
    if f < T_WIND:                                            # back to the making place with it
        u = ramp(f, 137.3, T_WIND - 0.12)
        p = dog.carry_part(f, gait="trot") if u < 1 else dog.lay((f - (T_WIND - 0.12)) * 3.0)
        return dict(out, pose=p, x=lerp(xs, xw, smooth(u) * 0.3 + u * 0.7), y=806.0, carry=_spool_sprite(f))
    if f < T_LID - 0.1:                                       # winds the strip on by walking round it with the end in its mouth
        x, y, fac, behind = _circle(f)
        return dict(out, pose=dog.carry_page(f, gait="trot"), x=x, y=y, facing=fac, behind=behind)
    xl = SPOOL_C[0] - 52.0
    if f < T_LID + 0.12:                                      # noses the lid on
        u = ramp(f, T_LID - 0.1, T_LID + 0.12)
        return dict(out, pose=dog.lay(0.25 + 0.3 * u), x=lerp(_circle(T_LID - 0.1)[0], xl, u), y=806.0)
    if f < T_LOOK:                                            # and presses a paw on it
        tau = f - (T_PAW - 0.45)
        p = dog.paw_press(max(0.0, tau)) if tau < 0.62 else dog.blend(dog.paw_press(0.62), dog.stand(0.0), ease(tau, 0.62, 0.72))
        return dict(out, pose=p, x=xl, y=806.0)
    if f < T_TAKE:                                            # looks up at the roof for whoever should look at it. Nobody.
        u = ease(f, T_LOOK - 0.02, T_LOOK + 0.24)
        p = dog.blend(dog.stand(0.0), dog.look_up(dog.watch(0.0), 1.0), {"ears": ease(f, T_LOOK - 0.05, T_LOOK + 0.08), "head": u, "tail": 0.0, "body": u * 0.5, "legs": 0.0})
        return dict(out, pose=p, x=xl, y=806.0)
    if f < T_RISE:                                            # picks the reel up
        tau = (f - T_TAKE) * 4.2
        p = dog.blend(dog.look_up(dog.watch(0.0), 1.0), dog.take_page(0.35 + tau), ease(f, T_TAKE, T_TAKE + 0.1))
        return dict(out, pose=p, x=xl, y=806.0, carry=_reel_sprite(under=True))
    if f < T_BREACH:                                          # up, to the left of where it went down
        u = ramp(f, T_RISE, T_BREACH)
        x = lerp(xl + 30, BREACH_X + 44, u / 0.55) if u < 0.55 else lerp(BREACH_X + 44, BREACH_X, (u - 0.55) / 0.45)
        y = lerp(806.0 - 30, 404.0, smooth(u) * 0.35 + u * 0.65)
        p = dog.blend(dog.carry_page(f, gait="stand"), dog.carry_page(f, gait="swim_up"), ease(u, 0.0, 0.14))
        return dict(out, pose=dog.holding(p, "reel"), x=x, y=y, facing=lerp(1.0, -1.0, ease(u, 0.5, 0.58)), anchor="body",
                    carry=_reel_sprite(under=True))
    if f < T_SHAKE:                                           # the breach
        tau = f - T_BREACH
        dur = T_SHAKE - T_BREACH
        x, y = dog.burst_path(tau, (BREACH_X, 399.0), LAND, DS, height=96.0, dur=dur)
        return dict(out, pose=dog.holding(dog.burst(tau, dur=dur), "reel"), x=x, y=y, facing=-1, layer="front", anchor="body", carry=_reel_sprite())
    if f < T_LAY:                                             # the biggest shake in the film
        tau = f - T_SHAKE
        return dict(out, pose=dog.holding(dog.shake(tau, dur=T_LAY - T_SHAKE), "reel"), x=LAND[0], y=LAND[1], facing=-1, layer="sill",
                    carry=_reel_sprite(), bits=dog.shake_drops(tau, n=90, dur=T_LAY - T_SHAKE))
    if f < T_PLEASED:                                         # lays it on the sill and noses it along
        tau = (f - T_LAY) * 2.3
        p = dog.lay(min(tau, 0.9))
        if tau > 0.9:
            p = dog.blend(p, dog.pleased(f), ease(tau, 0.9, 1.15))
        return dict(out, pose=p, x=LAND[0], y=LAND[1], facing=-1, layer="sill", carry=_reel_sprite() if tau < 0.62 else None)
    return dict(out, pose=dog.pleased(f - T_PLEASED + 0.4), x=LAND[0], y=LAND[1], facing=-1, layer="sill")


@lru_cache(maxsize=8)
def _reel_sprite(under=False):
    kw = props.UNDER if under else {}
    return props.reel_sprite(props.REEL_LEAD, tilt=0.85, paw=True, wet=1, **kw)


def _spool_sprite(f):
    return props.part_sprite("spool", mud=0.3, wet=1, weed=0.4, t=f, **props.UNDER)


def draw_lead(ink, f, cam, layer):
    st = lead_state(f)
    if not st or st["layer"] != layer:
        return None
    z = cam.zoom
    sx, sy = cam.xy(st["x"], st["y"])
    under = layer == "under"
    kw = dict(LEAD_UNDER) if under else {}
    if st["anchor"]:
        kw["anchor"] = st["anchor"]
    fac = st["facing"]
    if abs(fac) < 0.25:
        fac = 0.25 if fac >= 0 else -0.25
    j = dog.draw_dog(ink, st["pose"], sx, sy, scale=DS * z, facing=fac, carry=st["carry"], **kw)
    if st["bits"]:
        dog.draw_bits(ink, st["bits"], sx, sy, DS * z, facing=1 if fac > 0 else -1)
    return j


@lru_cache(maxsize=4096)
def _mouth_cached(fq):
    st = lead_state(fq)
    j = dog.draw_dog(Image.new("RGB", (W, H)), st["pose"], st["x"], st["y"] - 500, scale=DS, facing=st["facing"] or 0.3, shadow=False,
                     texture=False, ss=1, **({"anchor": st["anchor"]} if st["anchor"] else {}))
    return (j["mouth"][0], j["mouth"][1] + 500)


def lead_mouth(f):
    """World point of the lead dog's mouth (the via-point of the REEL morph)."""
    return _mouth_cached(round(f * FPS) / FPS)


def reel_lay_x(f):
    """Where the reel lies on the sill after the dog lets go: nosed along to x = 380."""
    return lerp(LAND[0] - 46.0, 380.0, ease(f, T_LAY + 0.62 / 2.3, T_PLEASED))


# ====================================================================== #
#  4 · THE HERD                                                          #
# ====================================================================== #

def _my(x):
    return porch.meadow_y(x)


LEAD_SPOT = 806.0                            # where S4 left her
EDGE_X = 764.0                               # the meadow's edge she steps down from
LEFT_END = (664.0, 0.0)                      # where she stands across the wind side of the eleven
REST_X = 598.0


@lru_cache(maxsize=None)
def cows():
    S = herd.S
    r_pre = herd.Route([(LEAD_SPOT + 2, _my(LEAD_SPOT + 2), 1.0), (EDGE_X, _my(EDGE_X), 1.0)])
    w_pre = herd.Walker("lead", r_pre, [(T0 - 1, 2.0), (T_SKIN, 2.0), (118.0, r_pre.length)])
    ir = herd.ice_route(EDGE_X, COW_ICE_X)
    w_ice = herd.Walker("lead", ir, [(119.3, 0.0), (120.72, ir.length), (T_BREAK, ir.length), (124.2, 0.0), (125.0, 0.0)], carry=16)
    r_off = herd.Route([(EDGE_X, _my(EDGE_X), 1.0), (REST_X, 388.0, 1.0)])
    w_off = herd.Walker("lead", r_off, [(124.95, 0.0), (128.6, r_off.length)])
    r_in = herd.Route([(REST_X, 388.0, 1.0), (LEFT_END[0], _my(LEFT_END[0]) + 1.0, 1.0)])
    w_in = herd.Walker("lead", r_in, [(133.8, 0.0), (135.1, r_in.length)])
    d5a, d6a = herd.hill_spot(0), herd.hill_spot(1)
    d5b, d6b = herd.d_at(926.0), herd.d_at(956.0)
    w5 = herd.Walker("fifth", herd.PATH, [(T0 - 1, d5a), (122.3, d5a), (135.9, d5b)])
    d6s = S4._cows()["w6"].state(116.0)["d"]
    w6 = herd.Walker("sixth", herd.PATH, [(T0 - 1, d6s), (122.9, d6s), (141.2, d6b)])
    return dict(w_pre=w_pre, w_ice=w_ice, ir=ir, w_off=w_off, w_in=w_in, w5=w5, w6=w6)


def cow_stamp_tau(f):
    """Her stamp on my clock: the leg starts up at 121.5, lands at 122.0; again at 122.6."""
    hit = herd.STAMP_HIT
    if f < 121.5:
        return 0.35
    if f < T_STAMP + 0.08:
        return 0.7 + (f - 121.5) * (hit - 0.7) / 0.5
    return None


def lead_cow(ink, f, oy, layer, anchors):
    """The lead cow all sequence long. Draws her if she is in `layer` (strip | front)."""
    c = cows()
    S = herd.S
    a = None
    if f < 116.45:                                           # as S4 left her: looking down into the water
        if layer == "strip":
            a = herd.cow(ink, "lead", herd.look_down(f, 1.0, "lead"), LEAD_SPOT, _my(LEAD_SPOT), S, -1, oy, nose_to=(LEAD_SPOT - herd.reach("lead"), 399.0))
    elif f < T_SKIN:                                         # her head comes up: the water has gone strange
        if layer == "strip":
            p = herd.tween(herd.look_down(f, 1.0, "lead"), herd.stand(f, "lead", chew=0, alert=1), ease(f, 116.45, 116.95), "inout", "lead")
            a = herd.cow(ink, "lead", p, LEAD_SPOT, _my(LEAD_SPOT), S, -1, oy)
    elif f < 119.3:                                          # along the edge to where the ice begins; she looks at it
        if layer == "strip":
            if f < 118.0:
                a = c["w_pre"].draw(ink, f, oy)
            else:
                p = herd.stand(T_STOP, "lead", chew=0, alert=1)
                a = herd.cow(ink, "lead", p, EDGE_X, _my(EDGE_X), S, -1, oy)
    elif f < 124.95:                                         # on the ice
        if layer == "front":
            w = c["w_ice"]
            if f < 120.72:
                skate = bump((f - 120.12) / 0.34)
                a = w.draw(ink, f, oy, reflect=402, rim=0.15, tilt=-0.06 * skate, nose_to=(NOSE_X + 10, 392.0) if f > 120.3 else None)
            elif f < T_BREAK:
                tau = cow_stamp_tau(f)
                nose = (NOSE_X, 399.6)
                if tau is not None and f < 121.5:            # head down to the ice over the dog; held
                    p = herd.tween(herd.stand(f, "lead", chew=0, alert=0.3), herd.stamp(tau, "lead"), ease(f, 120.72, 121.0), "inout", "lead")
                elif tau is not None:
                    p = herd.stamp(tau, "lead")
                else:
                    t2 = f - T_STAMP                          # after the first: up again at once, down at 122.6, then she watches
                    if t2 < 0.6:
                        tb = 0.86 + (t2 - 0.08) * (herd.STAMP_HIT - 0.86) / 0.52
                        p = herd.tween(herd.stamp(herd.STAMP_HIT + 0.08, "lead"), herd.stamp(tb, "lead"), ease(t2, 0.08, 0.2), "inout", "lead")
                    else:
                        p = herd.stamp(herd.STAMP_HIT + (t2 - 0.6), "lead")
                    nose = None
                a = herd.cow(ink, "lead", p, COW_ICE_X, 401.0, S, -1, oy, nose_to=nose, reflect=402 if f < T_BREAK else None, rim=0.15)
            elif f < 124.2:                                  # backing off, the plates tipping under each forefoot
                dip = 3.0 * abs(math.sin((f - T_BREAK) * 8.5))
                a = w.draw(ink, f, oy + 0, rim=0.15, tilt=0.035 * math.sin((f - T_BREAK) * 8.5))
            else:                                            # the last forefoot went in to the knee: she shakes it like a cat
                sh = f - 124.2
                tau = 1.05 + 0.2 * math.sin(sh * 42) * (1 - ease(sh, 0.35, 0.7))
                p = herd.tween(herd.stamp(tau, "lead"), herd.stand(f, "lead", chew=0, alert=0.6), ease(sh, 0.5, 0.75), "inout", "lead")
                a = herd.cow(ink, "lead", p, EDGE_X, _my(EDGE_X), S, -1, oy)
    elif f < 128.6:                                          # back along the bank, toward the sill end
        if layer == "strip":
            a = c["w_off"].draw(ink, f, oy)
    elif f < 133.8:                                          # she has turned round; she looks down into the water
        if layer == "strip":
            turn = ease(f, 128.7, 129.5)
            p = herd.tween(herd.stand(f, "lead", chew=1), herd.look_down(f, 0.9, "lead"), ease(f, 129.6, 130.6), "slow", "lead")
            a = herd.cow(ink, "lead", p, REST_X, 388.0, S, -1, oy, turn=turn if turn < 1 else None) if turn < 1 else \
                herd.cow(ink, "lead", p, REST_X, 388.0, S, 1, oy)
    elif f < 135.1:                                          # she walks over
        if layer == "strip":
            a = c["w_in"].draw(ink, f, oy)
    else:                                                    # across the wind side of them, head low over them
        if layer == "strip":
            x, y = LEFT_END[0], _my(LEFT_END[0]) + 1.0
            lick = bump((f - 136.2) / 0.9)
            target = (HEAP[6][0] - 6 + 5 * math.sin((f - 136.2) * 14) * lick, HEAP[6][1] - 13 + 3 * lick)
            p = herd.tween(herd.stand(f, "lead", chew=0), herd.warm(f, "lead"), ease(f, 135.1, 135.9), "slow", "lead")
            up = ease(f, 143.25, 143.7)                      # the reel is on the sill: her head comes up
            turn = ease(f, 142.55, 143.2)                    # ... and she has turned to look that way
            if f >= 142.4:
                p = herd.tween(p, herd.stand(f, "lead", chew=0, alert=1), max(up, 0.0 if f < 143.25 else 1.0) if f >= 143.25 else 0.0, "inout", "lead")
                p = herd.tween(herd.warm(f, "lead"), herd.stand(f, "lead", chew=0, alert=1), ease(f, 142.5, 143.6), "inout", "lead")
                if turn < 1:
                    a = herd.cow(ink, "lead", p, x, y, S, 1, oy, turn=turn, rim=0.1)
                else:
                    a = herd.cow(ink, "lead", p, x, y, S, -1, oy, rim=0.1)
            else:
                a = herd.cow(ink, "lead", p, x, y, S, 1, oy, nose_to=target if f > 135.3 else None, rim=0.1)
    if a:
        anchors["lead"] = a
    return a


def calf_xy(f):
    if f < 119.4:
        return 664.0, 388.5
    if f < 133.0:                                            # its forefeet on the ice; then back up
        u = ease(f, 119.4, 120.0) * (1 - ease(f, 123.2, 123.7))
        return 664.0 - 7 * u, 388.5 + 6.0 * u
    return lerp(664.0, 706.0, ease(f, 134.6, 135.8)), lerp(388.5, 392.5, ease(f, 134.6, 135.8))


def cow_clock(f):
    """The herd's own clock: it holds for the one and a half seconds of the frozen town shot, so that
    nothing at all moves in that frame (they are only shapes above the ice there)."""
    return T_STOP if T_STOP <= f < T_SPLIT else f


def draw_cows(ink, f, oy, layer, anchors):
    """Everybody of the herd who is in `layer` at f (hill | strip | front), in drawing order; the heap of
    wet dogs is drawn by the caller between the back cows and the end cows (see strip())."""
    c = cows()
    S = herd.S
    fp = cow_clock(f)
    if layer == "hill":
        c["w6"].draw(ink, fp, oy, layer="hill")
        c["w5"].draw(ink, fp, oy, layer="hill")
        return
    if layer == "front":
        lead_cow(ink, f, oy, "front", anchors)
        return
    warm = f >= T_UP
    # the second, far right: the right end of the horseshoe
    p = herd.look_down(fp, 1.0, "second")
    if warm:
        p = herd.tween(p, herd.warm(f, "second"), ease(f, 135.0, 135.7), "slow", "second")
    anchors["second"] = herd.cow(ink, "second", p, S4.SECOND_X, _my(S4.SECOND_X), S, -1, oy,
                                 nose_to=(HEAP[5][0] + 4, HEAP[5][1] - 12) if f > 135.2 else None, rim=0.1 if warm else None)
    # the fourth: she turns round where she stands (135.7) and is the far side of it
    x4 = 842.0
    p = herd.stand(fp, "fourth", chew=1 if not frozen(f) else 0)
    turn = ease(f, 135.6, 136.25)
    if f > 136.25:
        p = herd.tween(p, herd.warm(f, "fourth"), ease(f, 136.25, 136.9), "slow", "fourth")
        anchors["fourth"] = herd.cow(ink, "fourth", p, x4, _my(x4) - 3, S * 0.96, -1, oy, nose_to=(HEAP[9][0], HEAP[9][1] - 13), rim=0.1)
    elif turn > 0:
        anchors["fourth"] = herd.cow(ink, "fourth", p, x4, _my(x4) - 3, S * 0.96, 1, oy, turn=turn)
    else:
        anchors["fourth"] = herd.cow(ink, "fourth", p, x4, _my(x4) - 3 * ease(f, 133, 135), S * lerp(1, 0.96, ease(f, 133, 135)), 1, oy)
    # the mother: the near side of it
    xm = 740.0
    p = herd.look_down(fp, 1.0, "mother") if f < T_UP + 0.3 else herd.tween(herd.look_down(f, 1.0, "mother"), herd.warm(f, "mother"), ease(f, 135.4, 136.1), "slow", "mother")
    back = ease(f, 133.0, 135.0)
    anchors["mother"] = herd.cow(ink, "mother", p, xm - 22 * back, _my(xm) - 4 * back, S * lerp(1, 0.96, back), 1, oy,
                                 nose_to=(HEAP[7][0] - 2, HEAP[7][1] - 13) if f > 135.6 else None, rim=0.1 if warm else None)
    # the fifth and the sixth, coming down the path one at a time
    c["w6"].draw(ink, fp, oy, layer="strip")
    c["w5"].draw(ink, fp, oy, layer="strip")


def draw_calf(ink, f, oy):
    S = herd.S
    x, y = calf_xy(f)
    if f < 119.3:
        p = herd.look_down(f, 1.0, "calf")
        if 117.45 < f < 118.0:                                # its muzzle jerks away from the cold
            p = herd.tween(p, herd.stand(f, "calf", chew=0, alert=1), ease(f, 117.5, 117.62), "inout", "calf")
        elif f >= 118.0:
            p = herd.stand(T_STOP, "calf", chew=0, alert=1)
        return herd.cow(ink, "calf", p, x, y, S, -1, oy, nose_to=(x - herd.reach("calf") - 2, 399.5) if f < 117.5 else None)
    if f < 133.0:
        p = herd.tween(herd.stand(f, "calf", chew=0, alert=1), herd.look_down(f, 0.8, "calf"), ease(f, 119.6, 120.3), "inout", "calf")
        return herd.cow(ink, "calf", p, x, y, S, -1, oy)
    if f < 136.0:
        turn = ease(f, 133.3, 133.9)
        p = herd.stand(f, "calf", chew=0, alert=0.8)
        if turn < 1:
            return herd.cow(ink, "calf", p, x, y, S, -1, oy, turn=turn)
        return herd.cow(ink, "calf", p, x, y, S, 1, oy)
    if f < 137.4:                                             # it lies down in the heap as if it were a dog
        return herd.cow(ink, "calf", herd.fold_down(ramp(f, 136.0, 137.4), "calf"), x, y, S, 1, oy)
    return herd.cow(ink, "calf", herd.sleep(f, "calf", ease(f, 137.4, 139.0)), x, y, S, 1, oy)


# ====================================================================== #
#  5 · THE PICTURE                                                       #
# ====================================================================== #

SHOTS = [   # t0, t1 (film), name, why the camera is there
    (116.0, 119.5, "A town, the cold", "F-TOWN: the work, and the cold coming down on it from the top of the frame"),
    (119.5, 124.5, "B the ice", "F-SPLIT, locked: she above, the dog below, the ice between; a push on the two noses, let go by the stamp"),
    (124.5, 132.2, "C the rain, and later", "F-TOWN: fifty-one come down through the same line; the light says later; they go up with things"),
    (132.2, 133.2, "D up with the eleven", "crane up with eleven who have let their breath go"),
    (133.2, 134.4, "E through the line", "F-SPLIT: heads through the surface; the roof below them empty"),
    (134.4, 137.0, "F kept warm", "crane up and in on the meadow: the ones who could not go under are the ones who can do this"),
    (137.0, 140.7, "G alone", "medium on the making place: one dog, and the empty roof in the same frame"),
    (140.7, 142.4, "H up", "pull back, then crane up with the reel through the line"),
    (142.4, 144.0, "I pleased", "F-PORCH, as wide as the first shot of the film: the reel on the sill, the herd round the eleven"),
]
ALONE_CAM = Cam.look(650.0, 762.0, 1.72)
WARM_OY = 70


def camera(f):
    """-> (oy, push (cx, cy, zoom) or None, Cam or None). A Cam means the under-water medium (no porch)."""
    if f < T_SPLIT:
        return 360, None, None
    if f < T_CLEAR:
        z = 1.0 + 0.34 * ease(f, 120.45, 121.0) * (1 - ease(f, T_STAMP, T_STAMP + 0.22))
        return 250, (NOSE_X + 20, 150.0, z), None
    if f < 132.2:
        return 360, None, None
    if f < 134.4:
        return porch.crane(f, 132.2, 133.2, 360, 250), None, None
    if f < T_ALONE:
        u = ease(f, 134.4, 135.5)
        return lerp(250, WARM_OY, u), (960.0, 354.0, 1.0 + 0.75 * u), None
    if f < T_TAKE:
        return 360, None, ALONE_CAM
    if f < T_RISE:
        return 360, None, ALONE_CAM.mix(Cam(oy=360), ease(f, T_TAKE, T_RISE))
    if f < T_PORCH:
        return porch.crane(f, T_RISE, T_PORCH, 360, 0), None, None
    return 0, None, None


T_PORCH = 142.4


def _patched(**repl):
    """Swap S4 functions for the length of one frame (S4 is not edited; it is put back at once)."""
    class _P:
        def __enter__(self_):
            self_.old = {k: getattr(S4, k) for k in repl}
            for k, v in repl.items():
                setattr(S4, k, v)

        def __exit__(self_, *a):
            for k, v in self_.old.items():
                setattr(S4, k, v)
    return _P()


_KID = S4.kid_state


def _kid_state(k, fs):
    st = dict(_KID(k, fs))
    f = _NOW["f"]
    up = ease(f, 117.15 + 0.05 * k, 117.5 + 0.05 * k)         # the fish children look up first
    if up > 0:
        st["look"] = (st["x"] - 30, 400.0)
        st["tilt"] = lerp(st["tilt"], -10.0, up)
        st["mouth_open"] = 1.0 if up > 0.5 else 0.0
    return st


_NOW = {"f": T0}


def kids(ink, f, cam, tq, calm):
    """The fish class after the ice."""
    look = None
    if f < T_LATER:
        look = (560.0, 520.0)                                 # the rain of dogs
    elif T_OUT + 0.3 < f < T_ALONE:
        look = (760.0, 470.0)                                 # the eleven going up
    lst = lead_state(f)
    if look is None and lst:
        look = (lst["x"], lst["y"] - 20)
    town.townsfolk(ink, tq, cam, look=look, calm=calm)
    town.school_class(ink, tq, cam, skip=tuple(range(8)), look={"T": look}, calm=calm)
    for k in (4, 5, 6, 7, 0, 1, 2, 3):
        x, y = town.SEATS[k]
        gape = (f < 126.2) or (T_OUT + 0.4 < f < 133.2)
        town.child(ink, tq, cam, k, x, y, tilt=-8.0 if gape else 8.0, facing=-1 if (look and look[0] < x) else 1, arm=20.0, look=look,
                   mouth_open=1.0 if gape else 0.0, swim=0.3, calm=calm)


def town_set(ink, f, cam, sky):
    tq = clock(f)
    calm = frozen(f)
    cold = cold_at(f)
    fs = s4_clock(f)
    town.back(ink, tq, cam, sky=sky, door=1.0 - cold, calm=calm, night=night_at(f))
    town.street(ink, tq, cam, bell=S4.track("bell").x(fs), holes=8, smudges=smudges_at(f), calm=calm)
    n = holes_at(f)
    for q in sorted(range(8, int(math.ceil(n))), key=lambda q: town.HOLES[q][1]):
        S4.draw_hole(ink, cam, q, clamp(n - q))
    town.making_place(ink, cam, 1.0)
    S4._posts(ink, fs, cam, front=False)
    S4._page_stack(ink, fs, cam)
    if f >= T_GOON + 1.85:                                    # the herder has laid three more pages on the stack
        for q in range(3, 5):
            sx, sy = cam.xy(520.0 + 3 * q, 796.0 - 2.2 * q)
            props.page(ink, sx, sy, 0.5 * cam.zoom, town.CHILD_DRAWS[q], flat=0.86, angle=-4 + 5 * q, **props.UNDER)
    S4._parts_laid(ink, fs, cam)
    S4._lamp_stock(ink, fs, cam)
    if f < 137.22:
        town.thing(ink, cam, "spool", *SPOOL_AT)


def draw_row(ink, f, cam):
    """The row of pieces; and, while it is wound, the REEL morph: the same pieces on their way to the spool."""
    z = cam.zoom
    if f < T_GOON:
        return
    if f <= T_WIND:
        for x, lean in row_pieces(f):
            px, py = cam.xy(x, LINE_Y)
            kb.draw_thing(ink, "piece", px, py, PS * z, angle=lean, **UNDER)
        return
    w = reel_weights(f)
    pts = reel_morph().at(f) if f < T_LID else None
    if pts is None:
        return
    trail = []
    for i in range(ROW_N):
        wi = w[i]
        x, y = pts[i]
        if wi <= 0:
            px, py = cam.xy(row_slots()[i], LINE_Y)
            kb.draw_thing(ink, "piece", px, py, PS * z, **UNDER)
            trail.append((x, y))
        elif wi < 1:
            sc = PS * lerp(1.0, 0.34, ease(wi, 0.25, 1.0))
            px, py = cam.xy(x, y)
            kb.draw_thing(ink, "piece", px, py, sc * z, angle=1.3 * math.sin(wi * math.pi) * (1 if i % 2 else -1) + 0.6 * wi, stand=False, **UNDER)
            trail.append((x, y))
    moving = [(pts[i][0], pts[i][1]) for i in range(ROW_N) if 0 < w[i] < 1]
    if len(moving) > 1:                                       # the strip is one thing: a dark line through the pieces in the air
        ink.d.line([cam.xy(*p) for p in moving], fill=(24, 44, 52, 150), width=max(1, int(round(1.4 * z))))


def draw_spool(ink, f, cam):
    """The spool in the making place, the film winding onto it, the lid, the paw print."""
    if f < T_WIND - 0.06 or f >= T_TAKE + 0.24:
        return
    z = cam.zoom
    cx, cy = cam.xy(*SPOOL_C)
    n = float(np.sum(reel_weights(f)))
    props.part(ink, cx, cy - 2 * z, 0.62 * z, "spool", mud=0.2, wet=1, weed=0, t=f, **props.UNDER)
    if n > 0.2 and f < T_LID:
        r = (4.0 + 0.6 * n) * z
        ink.d.ellipse([cx - r, cy - 7 * z - r * 0.5, cx + r, cy - 7 * z + r * 0.5], fill=(30, 52, 60, 255), outline=(12, 28, 34, 255))
        ink.d.ellipse([cx - r * 0.55, cy - 7 * z - r * 0.27, cx + r * 0.55, cy - 7 * z + r * 0.27], outline=(96, 150, 150, 255))
        k = int(n)
        ang = f * 14.0
        ink.d.line([(cx, cy - 7 * z), (cx + r * math.cos(ang), cy - 7 * z + 0.5 * r * math.sin(ang))], fill=(150, 196, 190, 255), width=1)
    if f >= T_LID - 0.02:
        drop = 1 - ease(f, T_LID - 0.02, T_LID + 0.12)
        props.reel(ink, props.REEL_LEAD, cx, cy - 11 * z - 12 * z * drop, 0.8 * z, tilt=0.7, wet=1, paw=f >= T_PAW, angle=-10 * drop, tint=props.TEAL, tint_amount=0.12)


def under(ink, f, cam, sky, porch_oy=None):
    """Everything below the line at f, in any framing."""
    tq = clock(f)
    calm = frozen(f)
    z = cam.zoom
    _NOW["f"] = f
    town_set(ink, f, cam, sky)
    todo = []
    cr = crowd()
    if f < T_GOON:                                            # S4's own cast, at S4's clock: its last frame, slowing, stopped
        fs = s4_clock(f)
        lst = lead_state(f)
        with _patched(kid_state=_kid_state, _lead_town=(lambda ink_, f_, cam_: None) if lst else S4._lead_town):
            S4.town_cast(ink, fs, cam)
        j = draw_lead(ink, f, cam, "under")
        if j and T_NOSE - 0.02 <= f < T_STAMP + 0.1:          # a bubble sits against its nose, under the ice
            nx, ny = j["nose"]
            r = 4.2 * z * ease(f, T_NOSE - 0.02, T_NOSE + 0.2)
            ink.d.ellipse([nx - r * 1.5 + 4 * z, ny - r * 0.9 - 2 * z, nx + r * 1.5 + 4 * z, ny + r * 0.5 - 2 * z], fill=(206, 236, 232, 70),
                          outline=(236, 250, 246, 240), width=max(1, int(1.3 * z)))
    else:
        kids(ink, f, cam, tq, calm)
        for nm in PACK9:
            st = pack_state(nm, f)
            if st:
                todo.append((st["y"] if "mode" not in st else 2000, lambda nm=nm: draw_pack(ink, nm, f, cam)))
        todo.append((806.5, lambda: S4._posts(ink, FS, cam, front=True)))
        todo.append((LINE_Y, lambda: draw_row(ink, f, cam)))
        todo.append((LINE_Y + 8, lambda: S4._shells(ink, FS, cam) if f < T_WIND else None))
        lst = lead_state(f)
        if lst and lst["layer"] == "under":
            behind = lst.get("behind", False)
            todo.append((lst["y"] - (8 if behind else 0) if not lst["anchor"] else 2001, lambda: draw_lead(ink, f, cam, "under")))
        todo.append((806.0 - 1.0, lambda: draw_spool(ink, f, cam)))
    for d in cr:
        st = crowd_state(d, f)
        if st and st[0] in ("fall", "bed", "roof", "rise", "up"):
            key = st[3] if st[0] in ("bed",) else (640.0 if st[0] == "roof" else 1990)
            todo.append((key, lambda d=d, st=st: draw_crowd_dog(ink, d, f, cam, st)))
    for y, fn in sorted(todo, key=lambda q: q[0]):
        fn()
    if porch_oy is not None and z == 1.0:                     # bubble trails behind everybody who comes down
        for d in cr:
            if d["t_drop"] - 0.05 < f < d["t_land"] + 1.2:
                porch.bubbles(ink, f, porch_oy, (d["gap"], 430.0), d["t_drop"], d["t_drop"] + 0.5, rate=14.0, seed=d["k"], size=0.8)
        lst = lead_state(f)
        if lst and 119.25 < f < T_STAMP:
            porch.bubbles(ink, f if f < T_NOSE else T_NOSE, porch_oy, (start_state()["lead"]["x"] + 30, 800.0), 119.25, 119.9, rate=9.0, seed=4,
                          size=0.9, hang=None)
    town.front(ink, tq, cam, calm=calm)
    cold, night = cold_at(f), night_at(f)
    if cold > 0.01 or night > 0.01:
        town.grade(ink, cam, cold=cold, night=night)


PEBBLES_0 = "wwggwgwggwgg"
PEBBLES_1 = PEBBLES_0 + "ggwgggwggggwgggwgg"     # thirty by the time we come up: they went on being set while we were below


def person_q(f):
    base = S4.person_q(116.0)
    kneel = porch.pose("kneel", at=(338, 316))
    sit = porch.pose("sit")
    if f < T_CLEAR + 0.6:
        return porch.blend(base, kneel, ease(f, 116.9, 117.95)), ease(f, 116.9, 117.95) > 0.5
    u = ease(f, T_CLEAR + 0.6, T_CLEAR + 2.2)
    q = porch.blend(kneel, sit, u)
    if f > T_LAY:                                             # leans to look at what has been laid down
        q = porch.blend(q, porch.pose("offer", p=0.35), ease(f, T_LAY + 0.2, T_PLEASED + 0.2) * 0.5)
    return q, u < 0.5


def old_dog(ink, f, oy):
    X, Y, S = OLD
    kw = {}
    c = cold_at(f)
    if c > 0.02:                                              # frost on its back
        kw["paper"] = tuple(int(lerp(a, b, c)) for a, b in zip((186, 182, 174), (226, 232, 238)))
    if 119.6 < f < 124.6:
        return ka.old_dog(ink, X, Y - oy, S, 1, "lift_head", p=ease(f, 119.6, 120.4) * (1 - ease(f, 124.0, 124.6)), **kw)
    if 133.25 <= f < 137.2:                                   # it watches them come out, then looks down at the water
        if f < 134.5:
            return ka.old_dog(ink, X, Y - oy, S, 1, "lift_head", p=ease(f, 133.25, 133.8), look=10, **kw)
        return ka.old_dog(ink, X, Y - oy, S, 1, "lift_head", p=1.0 - 0.45 * ease(f, 134.5, 135.3), look=lerp(10, -26, ease(f, 134.5, 135.3)), **kw)
    if f >= T_BREACH + 0.1:
        if f < T_LAY + 0.3:
            return ka.old_dog(ink, X, Y - oy, S, 1, "lift_head", p=ease(f, T_BREACH + 0.1, T_BREACH + 0.5), **kw)
        return ka.old_dog(ink, X, Y - oy, S, 1, "look_over", p=ease(f, T_LAY + 0.3, T_PLEASED + 0.1), **kw)
    return ka.old_dog(ink, X, Y - oy, S, 1, "lie", **kw)


def frame(ink, f, oy):
    """One frame with the porch in it: the board's world at camera offset oy."""
    cam = Cam(oy=oy)
    tq = clock(f)
    anchors = {}
    cr = crowd()
    if frozen(f):
        ink.rng = random.Random(1180)                         # the line boil is off under the ice

    def hill(ink, t, oy):
        draw_cows(ink, f, oy, "hill", anchors)

    def strip(ink, t, oy):
        draw_cows(ink, f, oy, "strip", anchors)
        heap = [(d, crowd_state(d, f)) for d in cr if d["eleven"] is not None]
        for d, st in sorted(heap, key=lambda q: q[1][3] if q[1] else 0):
            if st and st[0] == "heap":
                draw_crowd_dog(ink, d, f, cam, st)
        draw_calf(ink, f, oy)
        lead_cow(ink, f, oy, "strip", anchors)
        if f >= 133.9:                                        # steam off their backs and out of their noses, over the dogs
            amt = ease(f, 133.9, 135.4) * (1 - 0.55 * ease(f, 141.0, 143.6))
            for nm in ("mother", "fourth", "second", "lead"):
                a = anchors.get(nm)
                t_in = dict(lead=135.2, second=135.3, mother=135.7, fourth=136.4)[nm]
                if a:
                    herd.steam_on(ink, f, a, amount=2.4 * amt * ease(f, t_in - 0.6, t_in + 0.6), cold=1.0)

    def on_sill(ink, t, oy):
        props.pile(ink, tq, 312, 392 - oy, 5, s=0.6, born=[62.2, 71.5, 75.5, 80.8, 80.9], edge=404 - oy, floor=400 - oy, spread=S4.pile_spread(116.0))
        old_dog(ink, f, oy)
        if f >= T_LAY + 0.62 / 2.3:                           # the reel on the sill, its paw print up
            props.reel(ink, props.REEL_LEAD, reel_lay_x(f), 377 - oy, 0.78, tilt=0.8, paw=True, wet=1)
            props.drips(ink, f, reel_lay_x(f), 384 - oy, T_BREACH, floor=392 - oy, s=0.6)
        j = draw_lead(ink, f, cam, "sill")
        if T_SHAKE <= f < T_LAY + 0.3:
            porch.spray(ink, f, oy, LAND[0] - 6, 358, f - T_SHAKE, power=1.7, dur=1.0)
        if f >= T_SHAKE:
            porch.drips(ink, f, oy, LAND[0], 366, f - T_SHAKE, wet=1.0, width=40, floor=392)

    def under_(ink, t, oy):
        under(ink, f, cam, sky=False, porch_oy=oy)

    def front(ink, t, oy):
        draw_ice(ink, f, cam)
        draw_cows(ink, f, oy, "front", anchors)
        a = anchors.get("lead")
        if a and T_HOLD - 0.1 <= f < T_STAMP:
            draw_wound(ink, f, cam, breathe=0.5 + 0.5 * math.sin((f - T_HOLD) * 2 * math.pi / 0.9 - 1.2))
        elif f >= T_STAMP:
            draw_wound(ink, f, cam)
        for d in sorted(cr, key=lambda d: d["pad"][1]):
            st = crowd_state(d, f)
            if st and st[0] in ("ice", "surface", "haul"):
                draw_crowd_dog(ink, d, f, cam, st)
        for d in cr:                                          # where each one goes in, and where the eleven come out
            if d["t_drop"] <= f < d["t_drop"] + 1.0:
                porch.splash(ink, f, oy, d["gap"], f - d["t_drop"], 0.6, "in", seed=d["k"])
            if d["eleven"] is not None and d["t_surf"] <= f < d["t_surf"] + 1.0:
                porch.splash(ink, f, oy, d["surf_x"], f - d["t_surf"], 0.3, "out", seed=d["k"])
        if 124.0 <= f < 125.0:                                # her forefoot goes in to the knee
            porch.splash(ink, f, oy, EDGE_X - 44, f - 124.0, 0.9, "in", seed=77)
        draw_lead(ink, f, cam, "front")
        if T_BREACH <= f < T_BREACH + 1.1:
            porch.splash(ink, f, oy, BREACH_X, f - T_BREACH, 1.5, "out", seed=5)

    q, kneeling = person_q(f)
    rings = [porch.ring(d["gap"], d["t_drop"], 0.6) for d in cr if d["t_drop"] <= f < d["t_drop"] + 3]
    rings += [porch.ring(d["surf_x"], d["t_surf"], 0.8) for d in cr if d["eleven"] is not None and d["t_surf"] <= f < d["t_surf"] + 3]
    if f >= T_BREACH:
        rings.append(porch.ring(BREACH_X, T_BREACH, 1.3))
    hx = hoof_x()
    stamps = []
    if f >= T_STAMP:
        stamps = [(hx, porch.ease(f, T_STAMP, T_STAMP + 0.12))]
    lamp_at = (338, 316) if kneeling else None
    porch.scene(ink, tq, oy, cast=dict(hill=hill, strip=strip, sill=on_sill, under=under_, front=front),
                q=q, door=0.92, hold_a="lantern" if kneeling else None, hand_over_rail=f < 116.9, radio_on=1.0,
                lamp_at=lamp_at, pebbles=PEBBLES_0 if f < T_CLEAR else PEBBLES_1, rings=rings, puddles=[(350, 0.7), (405, 0.5)],
                dusk=dusk_at(f), stars=0.07 * ease(f, T_LATER, T_LATER + 1.0),
                freeze=ease(f, T_SKIN, T_STOP) if f < T_CLEAR else 0.0, stamps=stamps if f < T_CLEAR else (),
                crack=porch.ease(f, T_STAMP2, T_BREAK) if f < T_CLEAR else 0.0, breakup=porch.ease(f, T_BREAK, T_CLEAR) if f < T_CLEAR else 0.0,
                cold=cold_at(f))


def medium(ink, f, cam):
    """The under-water medium (the porch is not in it)."""
    under(ink, f, cam, sky=True)


def draw(t, ink):
    """One full 960x540 frame of S5 at local time t (0..28)."""
    t = clamp(t, 0.0, SECONDS)
    f = T0 + t
    oy, push, cam = camera(min(f, T1 - 1e-6))
    if cam is not None:
        medium(ink, f, cam)
        return
    frame(ink, f, int(round(oy)))
    if push and push[2] > 1.001:
        porch.push(ink, push[0], push[1], push[2])


# ====================================================================== #
#  6 · THE SOUND (laid with sound.py; nobody here has heard it)          #
# ====================================================================== #

def _pan(wx):
    return clamp((wx - 480.0) / 480.0, -1, 1) * 0.8


def sound(mix, at=0.0):
    """S5's sound into `mix`, the sequence starting at mix second `at`. Every contact is timed to the frame
    it lands on in THIS picture (the board's rule: the builder's frame wins and the sound moves)."""
    S = snd

    def A(f):
        return at + (f - T0)
    cr = crowd()
    c = cows()
    # rooms: below, the split is heard from above (dry, faint), below again, the bank, below, the porch
    S.hush(mix, A(T0) - 0.1, T_STOP - T0 + 0.1, 1.0, 0.2, 0.05)
    S.music_s5(mix, at)                                      # the round: stops dead with everything else; back at +7
    S.work(mix, A(116.0), 0.8, voices=7)
    S.work(mix, A(T_COLD), 1.2, voices=4, top=320, level=0.7)   # the cold: the working sound thins from the top
    S.ice_form(mix, A(T_COLD), 1.2)
    for tf, x, y, leg in c["w_pre"].hoof_falls(T_SKIN, 118.0):
        S.hooves(mix, A(tf), 1, 0.55, "grass", gain=0.035, pan=_pan(x), under=True)
    S.silence(mix, A(T_STOP), A(T_STAMP))                     # every dog waits. Nothing.
    for tf, x, y, leg in c["w_ice"].hoof_falls(119.3, 120.75):   # four careful steps, heard faint and dry
        S.hooves(mix, A(tf), 1, 0.36, "ice", gain=0.05, pan=_pan(x))
    S.skid(mix, A(120.2), gain=0.035)
    for k, d in enumerate(cr):                                # many very soft pads
        if k % 3 == 0:
            S.paws(mix, A(d["t_pad"] - 0.3), 2, 0.12, gain=0.012, pan=_pan(d["pad"][0]))
    S.silence(mix, A(T_HOLD), A(T_STAMP), fade=0.01)          # nose to nose: complete
    S.stamp(mix, A(T_STAMP))
    S.stamp(mix, A(T_STAMP2), gain=0.55, bell=False)
    S.ice_crack(mix, A(T_STAMP2 + 0.02))
    for tf, x, y, leg in c["w_ice"].hoof_falls(T_BREAK, 124.2):
        S.hooves(mix, A(tf), 1, 0.4, "ice", gain=0.07, pan=_pan(x))
    S.splash(mix, A(124.0), pan=0.3)
    S.above(mix, A(T_SPLIT), T_CLEAR - T_SPLIT, 0.5, 0.05, 0.2)
    S.silence(mix, A(T_SPLIT), A(119.52), fade=0.005)
    S.hush(mix, A(T_BREAK), T_UP + 0.2 - T_BREAK, 1.0, 0.8, 0.3)
    S.work(mix, A(T_GOON), 2.4, voices=7)                     # exactly as it was
    for d in cr:                                              # the second pack, heard from below: a rain of small splashes
        if d["k"] % 3 == 0:
            S.splash(mix, A(d["t_drop"]), gain=0.06, pan=_pan(d["gap"]), under=True)
    for d in cr:
        if d["k"] % 5 == 0:
            S.land(mix, A(d["t_land"]), gain=0.04, pan=_pan(d["spot"][0]))
    for ta in ROW_ADD:
        S.set_down(mix, A(ta + 0.25), gain=0.05, pan=_pan(700))
    S.work(mix, A(T_LATER), 4.0, voices=4, level=0.8)         # later: thinning as they leave
    for nm, tl in LEAVE.items():
        S.bubbles(mix, A(tl), 3, 0.8, gain=0.03, pan=_pan(start_state()[nm]["x"]))
    # eleven run out of breath, and are kept warm
    for d in cr:
        if d["eleven"] is None:
            continue
        S.breath_out(mix, A(d["t_out"]), 0.9, gain=0.07, pan=_pan(d["spot"][0]))
        S.breach(mix, A(d["t_surf"]), 0.7, gain=0.12, pan=_pan(d["surf_x"]))
        S.gasp(mix, A(d["t_surf"] + 0.2), gain=0.06, pan=_pan(d["surf_x"]))
    S.above(mix, A(T_UP + 0.1), T_ALONE - T_UP - 0.1, 1.0, 0.3, 0.2)
    S.crickets(mix, A(T_UP + 0.4), T_ALONE - T_UP - 0.5, 1, gain=0.014)
    S.shiver(mix, A(T_UP + 0.9), 3.0, pan=0.5)
    for tf, x, y, leg in c["w_in"].hoof_falls(133.8, 135.1):
        S.hooves(mix, A(tf), 1, 0.55, "grass", gain=0.09, pan=_pan(x))
    for hit in c["w_in"].bell_hits:
        if 133.8 < hit < 136.0:
            S.cowbell(mix, A(hit), gain=0.04, pan=0.4)
    for tf, x, y, leg in c["w5"].hoof_falls(133.2, 136.0):
        S.hooves(mix, A(tf), 1, 0.55, "earth", gain=0.06, pan=_pan(x))
    for k, tk in enumerate((135.2, 135.8, 136.3, 136.7)):     # long warm breaths, overlapping
        S.cow_breath(mix, A(tk), 1.8, gain=0.06, pan=0.3 + 0.1 * k)
    # one dog finishes alone
    S.hush(mix, A(T_ALONE), T_BREACH - T_ALONE, 1.0, 0.1, 0.1)
    S.set_down(mix, A(137.2))                                 # the spool taken up
    S.paws(mix, A(137.35), 3, 0.14, gain=0.04, pan=0.0)
    S.set_down(mix, A(T_WIND - 0.03), gain=0.06)
    S.ratchet(mix, A(T_WIND + 0.15), T_LID - T_WIND - 0.3, 9, gain=0.05, under=1500)
    S.set_down(mix, A(T_LID + 0.1), gain=0.07)                # the lid
    S.paw_press(mix, A(T_PAW), under=600)
    S.silence(mix, A(T_LOOK + 0.05), A(T_TAKE - 0.05), fade=0.04)
    S.hush(mix, A(T_LOOK), T_TAKE - T_LOOK, 0.8, 0.1, 0.1)    # the hold: the room only
    S.bubbles(mix, A(T_RISE + 0.1), 5, 0.8, gain=0.05, pan=0.1)
    S.breach(mix, A(T_BREACH), 1.0, gain=0.34, pan=0.2)
    S.above(mix, A(T_BREACH), T1 - T_BREACH, 1.0, 0.05, 0.05)
    S.crickets(mix, A(T_BREACH + 0.3), T1 - T_BREACH - 0.3, 2, gain=0.016)
    S.paws(mix, A(T_SHAKE - 0.03), 2, 0.07, gain=0.1, pan=snd.P_SILL, wet=True)
    S.shake(mix, A(T_SHAKE + 0.08), T_LAY - T_SHAKE - 0.1, gain=0.24)
    S.reel_down(mix, A(T_LAY + 0.62 / 2.3))
    S.card_drag(mix, A(T_LAY + 0.3), 0.35, pan=snd.P_SILL)    # nosed along the board
    S.tail(mix, A(T_PLEASED - 0.1), 4)
    S.cow_breath(mix, A(142.7), 1.3, gain=0.04, pan=0.5)
    return mix


# ====================================================================== #
#  7 · CHECKS (MEASURED when this runs)                                  #
# ====================================================================== #

def _raw(f):
    ink = kit.Ink(f - T0, int(round((f - T0) * FPS)))
    ink.paper()
    draw(f - T0, ink)
    return ink.img.convert("RGB")


def check(verbose=True, frames=True):
    out = {}
    # 1 correspondence: every key of a morph has the same points, and each key is met exactly at its time
    for m in (ice_morph(), wound_morph(), reel_morph()):
        for tk, k, _ in m.keys:
            raw = m.at(tk, raw=True) if m.name != "ice" or k.name != "bruised" else m.at(tk + 1e-9, raw=True)
            err = float(np.abs(m.at(tk + 1e-9, raw=True) - k.pts).max())
            assert err < 1e-5, (m.name, k.name, err)
        out[m.name + "_points"] = m.n
    # 2 no topological flip in any in-between
    ice = ice_morph()
    worst = 1e9
    for q in range(0, 145):
        f = T_SKIN + q * (T_BREAK - T_SKIN) / 144
        p = ice.at(f)
        th = p[ICE_M:][::-1][:, 1] - p[:ICE_M][:, 1]
        worst = min(worst, float(th.min()))
    assert worst >= -1e-9, f"ice thickness goes negative: {worst}"
    out["ice_min_thickness"] = round(worst, 3)
    wm = wound_morph()
    signs = set()
    for q in range(0, 97):
        f = T_HOLD + q * (T_BREAK - T_HOLD) / 96
        signs.add(signed_area(wm.at(f)) > 0)
    assert len(signs) == 1, "the wound's contour turns inside out"
    out["wound_area_sign_constant"] = True
    order_ok = True
    for q in range(0, 49):
        f = T_WIND + q * (T_LID - T_WIND) / 48
        w = reel_weights(f)
        order_ok &= bool(np.all(np.diff(w) >= -1e-9))        # pieces go in strictly left end first: never out of order
    assert order_ok
    out["reel_order_kept"] = True
    # 3 the board's counts
    cr = crowd()
    assert len(cr) == 51 and len({(d["make"], round(d["sc"], 4), d["seed"]) for d in cr}) == 51
    drops = [d["t_drop"] for d in cr]
    assert min(drops) >= T_CLEAR and max(drops) <= T_LATER, (min(drops), max(drops))
    el = [d for d in cr if d["eleven"] is not None]
    assert len(el) == 11 and sum(d["make"] == "looker" for d in el) == 7 and sum(d["make"] == "terrier" for d in el) == 4
    for d in cr:
        if d["eleven"] is None:
            assert d["carry"] and T_LATER - 0.6 <= d["t_leave"] and d["t_leave"] + RISE <= T_UP - 0.5, d
            st = crowd_state(d, d["t_leave"] + 0.5)
            assert st and st[0] == "rise" and st[7], d
        else:
            assert T_OUT <= d["t_out"] <= T_UP and T_UP <= d["t_surf"] <= T_UP + 1.0
    for nm in PACK9:
        st = pack_state(nm, LEAVE[nm] + 0.5)
        assert st and st.get("carry"), nm
        assert pack_state(nm, T_UP) is None
    out["dogs_in"] = 51
    out["up_with_nothing"] = 11
    out["up_with_a_thing"] = len(cr) - 11 + len(PACK9)
    assert len(row_pieces(T_WIND)) == ROW_N and len(row_pieces(T_GOON)) == 8
    assert len(PEBBLES_1) == 30
    assert abs(s4_clock(T0) - T0) < 1e-9 and abs(s4_clock(T_STOP) - FS) < 1e-9
    # 4 holds, from frames (before grain)
    if frames:
        a, b = np.asarray(_raw(118.2), np.int16), np.asarray(_raw(118.85), np.int16)
        out["hold_118_identical"] = bool((a == b).all())
        assert out["hold_118_identical"], "the frozen frames differ: %d px" % int((a != b).any(2).sum())
        a, b = np.asarray(_raw(T_LOOK + 0.3), np.int16), np.asarray(_raw(T_TAKE - 0.05), np.int16)
        box = (slice(250, 540), slice(180, 420))              # the dog and the reel
        out["hold_140_dog_px_changed"] = int((np.abs(a[box] - b[box]).max(2) > 24).sum())
        a, b = np.asarray(S4.still(116.0).convert("RGB"), np.int16), np.asarray(kit_frame(0.0), np.int16)
        out["first_frame_vs_s4_last_mean_abs"] = round(float(np.abs(a - b).mean()), 3)
    if verbose:
        for k, v in out.items():
            print(f"  {k}: {v}")
    return out


def kit_frame(t):
    ink = kit.Ink(t, int(round(t * FPS)))
    ink.paper()
    draw(t, ink)
    return ink.finish()


def still(f):
    return kit_frame(f - T0)


def sheet(times, path, cols=4, scale=0.5, crop=None):
    ims = []
    for f in times:
        im = still(f)
        if crop:
            im = im.crop(crop)
        ims.append(im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS))
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * w, rows * h), (20, 20, 24))
    for i, im in enumerate(ims):
        sh.paste(im, ((i % cols) * w, (i // cols) * h))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    sh.save(path)
    return path


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check()
        return
    if args and args[0] == "--stills":
        out = _HERE.parent.parent / "stills" / "dogs-s5"
        out.mkdir(parents=True, exist_ok=True)
        for a in args[1:]:
            f = float(a)
            still(f).save(out / f"{f:07.2f}.png")
        print("stills ->", out)
        return
    if args and args[0] == "--sheet":
        out = Path(args[1])
        cols = int(args[2])
        scale = float(args[3])
        print(sheet([float(a) for a in args[4:]], out, cols, scale))
        return
    check(verbose=False)
    film = kit.Film("dogs-s5", seconds=SECONDS)
    film.picture(draw)
    film.sound(lambda mix: sound(mix, 0.0))
    film.poster_at = 5.6
    film.render()


if __name__ == "__main__":
    main()
