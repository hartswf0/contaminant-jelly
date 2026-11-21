"""S3 · AGAIN, SOONER · film seconds 58.0 to 84.0 (local t = film - 58) of "The Dogs of Trouttown".

    import s3
    s3.SECONDS                 # 26.0
    s3.draw(t, ink)            # one full 960x540 frame; t = seconds since the sequence began
    s3.sound(mix, at)          # this sequence's sound, laid into a kit.Mix with local 0 at `at` seconds

Built by one agent working scion/animation-45.md (OCCLUSION COMPOSITING: who is in front?). In this
sequence two kinds of animal use the same four metres of bank at two tempos, so the picture is one long
crossing: a dog in front of a cow, a calf in front of its mother and under her head, a page in a hand, a
dog half above the water and half under it. That SCION's primitives are real data here, not a look:

    SLOTS       the depth passes of the set (porch.scene's cast hooks), back to front
    DAG         the occlusion graph: (front, back, t0, t1, why). Cels are drawn in a topological order of it
    EVENTS      the overlap events: when two named cels really cross on screen, and which is in front
    SWITCHES    the moments a cel changes pass (dog: water -> air -> board; cow: hill -> strip)
    HOLDOUTS    the mattes: the water line cuts the dog in two; the dry world holds out the town
    CONTACTS    who stands on what, and the contact shadow that says so
    Stage       the compositor: collects named cels per frame, sorts them by the DAG, draws them, and (when
                recording) keeps each cel's alpha matte so check() can measure the above on real pixels

Semantic sublayers break the two cycles in the scene (animation-45, section 6): the mother's body is
behind her calf and her head is in front of it; the lead cow's body is behind the sill and her head hangs
over it. check() (run with --check and before every full render) asserts: the DAG has no cycle at any
frame; every frame's draw order respects it; every EVENT's two mattes really intersect with the declared
one drawn later; a cel changes pass only while it overlaps nothing it jumps over (no pop); the water-line
holdout partitions the dog's alpha exactly; feet stand on what CONTACTS says; the boundary frames are
where the board puts them; nothing goes under without coming up with a thing.

Staging is the board's (films/swarm/dogs/board.md, S3). Sets and cast are imported, never edited:
porch.py (set, person), herd.py (cows), dog.py (lead dog), town.py (Trouttown), props.py (things),
sound.py (sound). What was built here because it was missing is listed at the bottom of this docstring.

Run alone:  python3 films/swarm/dogs/s3.py              -> assets/films/dogs-s3.mp4
            python3 films/swarm/dogs/s3.py --stills 1.2 4.4 ...
            python3 films/swarm/dogs/s3.py --sheets [a b ..]   -> contact sheets in films/stills/dogs-s3/
            python3 films/swarm/dogs/s3.py --check

Built here (missing elsewhere):
  * a split framing that holds the rail, the drinking cow and the digging dog at once. The board's F-SPLIT
    (offset 250) stops 10 px above the gravel, so the dig is out of frame. SPLIT here keeps offset 250 above
    the line and takes 85 px out of the first 200 px of water under it (sq_y): nothing lives in that water
    but the swimmer, and it is mapped through the same function, so crossings stay continuous.
  * holes dug out of town.py's order (it can only draw holes 0..n). The dog digs holes 5 and 4 (right under
    where it goes in) on its two shortest rounds and 6 and 3 on its long one; by the end holes 0..6 are dug,
    which is exactly town.dig_holes(7). _hole() is town's own pit, copied; check() compares the two pictures.
  * a pebble that slides along the rail from the seated hand to its place (porch puts pebbles at the far
    left of the rail, out of a seated arm's reach).
  * cow_state/_gate_layer: herd.py hands a cow from the hill pass to the strip pass at the START of her turn in
    the gate, 93 % wide, so she jumps in front of the gate posts. Here she changes pass edge-on (check() found it).

REPAIR (law 10), after an independent critic who saw only the picture. Sections 1 to 8 are the SCORE: the first
builder's continuous take, kept whole (check() still measures it). The film is now CUT from it (section 8c, EDL):
  * nothing is thrown on the door any more (the pale panel of pencil strokes read as a counter over the picture);
  * four closer cameras on the score (_close: the board's cels drawn again at the closer size, the set out of focus
    behind and in front of them): the page in the hands at the lamp, the first reel, the calf and the dog and the
    mother's tongue, the strip and the flange;
  * two new shots under water (section 8b) in place of the score's digs for rounds three and four: the reel is
    stuck, the dog's teeth slip, it thinks, it heaves and the reel comes apart (so: half a reel); then the fish
    child who watched holds up the side that stayed, and the dog needs one rake, for the torn film (so: a strip and
    a flange). The dive that goes wrong changes the next one;
  * the drinking cow jerks her head up inside three frames when the dog bursts out under her muzzle (cow_state).
check() times are score seconds; screen_of() gives where the cut shows them. The sound goes through screen_of().

Joins. Local 0 is S2's last frame (s2.py at 30.0: F-TOWN, the dog at (430, 550) with the page, her muzzle on the
line, the waver under it, three holes, boot, spool, pin). Local 26 is S4's first frame as s4.py draws it at 84.0:
door 0.62, dusk 0.4, the dog in s4.lead_porch's own sitting pose at (470, 394), porch's plain crouch, the mother
drinking at x 515, the calf at (408, 391), the lead cow turned this way at x 806 with the second beyond her at
892, the fourth above the gate, two on the path, S4's felt dog by the step (drawn with s4.felt_dog if s4 can
be imported). Both were compared as rendered frames, side by side; neither is a pixel match.
"""
from __future__ import annotations

import fnmatch
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kit                                   # noqa: E402
from kit import clamp, ramp, ease, lerp, smooth, W, H, FPS   # noqa: E402
import dog                                   # noqa: E402
import herd                                  # noqa: E402
import porch                                 # noqa: E402
import props                                 # noqa: E402
import town                                  # noqa: E402
import importlib.util as _ilu               # noqa: E402

_spec = _ilu.spec_from_file_location("dogs_sound", str(HERE / "sound.py"))   # films/ has another module called sound
if "dogs_sound" in sys.modules:
    snd = sys.modules["dogs_sound"]
else:
    snd = _ilu.module_from_spec(_spec)
    sys.modules["dogs_sound"] = snd
    _spec.loader.exec_module(snd)

SECONDS = 26.0
T0 = 58.0                                    # film second at local 0
DS = 0.6                                     # the lead dog's scale (board: 60 px to the withers)
SILL_Y = 394.0                               # where a dog's feet stand on the sill
STRIP_Y = 388.0                              # where hooves stand on the path strip
LINE = 400.0                                 # the surface, world y
TEAL = (24, 120, 128)
def dusk_at(t):
    """Dusk deepens across the film: S2 left it at 0, S4 takes it up at 0.4. porch.py keeps one plate per tenth,
    so it steps; each step is put under a camera move."""
    return 0.0 if t < 4.9 else 0.1 if t < 9.7 else 0.2 if t < 17.9 else 0.3 if t < 22.75 else 0.4


def door_at(t):
    """S2 left the door ajar (0.25: the lamp needs its planks to throw the page on); S4 takes it up at 0.62. It
    swings in a draught while the camera is at the waterline, too slowly to see."""
    return lerp(0.25, 0.62, ease(t, 9.6, 22.4))


def puddles_at(t):
    """The dry half of the sill gets wet where the dog has stood (S4 begins with these two)."""
    return [(350, 0.7 * ease(t, T_LAID1, T_LAID1 + 2.0)), (405, 0.5 * ease(t, T_L2, T_L2 + 1.5))]
WAVER = 2                                    # the fish child S2 left under the cow's nose


def bump(x):
    return math.sin(math.pi * clamp(x)) if 0 < x < 1 else 0.0


def _hermite(keys, t):
    """Catmull-Rom through [(time, x, y)] -> (x, y, vx, vy)."""
    if t <= keys[0][0]:
        a, b = keys[0], keys[1]
        return a[1], a[2], (b[1] - a[1]) / (b[0] - a[0]), (b[2] - a[2]) / (b[0] - a[0])
    if t >= keys[-1][0]:
        a, b = keys[-2], keys[-1]
        return b[1], b[2], (b[1] - a[1]) / (b[0] - a[0]), (b[2] - a[2]) / (b[0] - a[0])
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a[0] <= t <= b[0]:
            h = b[0] - a[0]
            u = (t - a[0]) / h
            pa = keys[i - 1] if i > 0 else a
            pb = keys[i + 2] if i + 2 < len(keys) else b
            out = []
            for c in (1, 2):
                ma = (b[c] - pa[c]) / max(b[0] - pa[0], 1e-6) * h
                mb = (pb[c] - a[c]) / max(pb[0] - a[0], 1e-6) * h
                u2, u3 = u * u, u * u * u
                p = (2 * u3 - 3 * u2 + 1) * a[c] + (u3 - 2 * u2 + u) * ma + (-2 * u3 + 3 * u2) * b[c] + (u3 - u2) * mb
                v = ((6 * u2 - 6 * u) * a[c] + (3 * u2 - 4 * u + 1) * ma + (-6 * u2 + 6 * u) * b[c] + (3 * u2 - 2 * u) * mb) / h
                out.append((p, v))
            return out[0][0], out[1][0], out[0][1], out[1][1]
    return keys[-1][1], keys[-1][2], 0.0, 0.0


# ====================================================================== #
#  1 · THE CAMERA                                                        #
# ====================================================================== #
# One world, a crane and a push. (oy, sq) is where the crane is: oy the board's offset above the line, sq
# the water taken out under it (0 everywhere except the split). The push is a crop of the finished frame.

SPLIT_OY, SPLIT_SQ, SQ_ZONE = 250.0, 85.0, 200.0

SHOTS = [   # t0, t1, name, how it begins, why the camera is there
    (0.00, 2.20, "A up", "continues S2", "the camera goes up because the dog goes up; the line passes with its head"),
    (2.20, 4.80, "B sill", "push", "a medium on the board: the shake, the cow's face in it, the page laid, the paw"),
    (4.80, 9.20, "C door", "move", "over to the door, because the page goes to the lamp and what it throws lands there"),
    (9.20, 17.70, "D split", "crane", "the hand on the rail, the cow drinking and the dog digging in one frame: two clocks. It leans in"
                                      " to the line each time the dog comes up, to see what it has, and back as it goes down"),
    (17.70, 21.30, "E calf", "move", "up to the waterline and in: the calf is the event and it happens on the board"),
    (21.30, 22.30, "F under", "CUT", "the one cut, on the dive: it is already down there; no time to follow it any more"),
    (22.30, 26.00, "G quiet", "crane", "up with it one last time, then back and still: the queue is still a queue"),
]

# moves: (t0, t1, from, to), eased; the value holds between moves. A zero-length move is a cut.
_OY = [(0.0, 2.0, 360.0, 0.0), (9.2, 10.3, 0.0, SPLIT_OY), (17.7, 18.25, SPLIT_OY, 0.0), (21.3, 21.3, 0.0, SPLIT_OY),
       (22.3, 23.3, SPLIT_OY, 0.0)]
_SQ = [(0.0, 0.0, 0.0, 0.0), (9.2, 10.3, 0.0, SPLIT_SQ), (17.7, 18.25, SPLIT_SQ, 0.0), (21.3, 21.3, 0.0, SPLIT_SQ),
       (22.3, 23.3, SPLIT_SQ, 0.0)]
# the push: zoom, and the centre of the view in the un-zoomed frame
_ZM = [(1.15, 2.25, 1.0, 1.4), (4.8, 5.6, 1.4, 1.2), (9.2, 10.0, 1.2, 1.0), (12.45, 13.05, 1.0, 1.5), (14.9, 15.45, 1.5, 1.0),
       (16.9, 17.4, 1.0, 1.5), (17.7, 18.25, 1.5, 1.42), (21.3, 21.3, 1.42, 1.0), (22.6, 23.3, 1.0, 1.16), (23.5, 24.8, 1.16, 1.0)]
_CX = [(1.15, 2.25, 480.0, 452.0), (4.8, 5.6, 452.0, 400.0), (9.2, 10.0, 400.0, 480.0), (12.45, 13.05, 480.0, 440.0), (14.9, 15.45, 440.0, 480.0),
       (16.9, 17.4, 480.0, 452.0), (17.7, 18.25, 452.0, 474.0), (19.0, 20.6, 474.0, 452.0), (21.3, 21.3, 452.0, 480.0), (22.6, 23.3, 480.0, 430.0),
       (23.5, 24.8, 430.0, 480.0)]
_CY = [(1.15, 2.25, 270.0, 346.0), (4.8, 5.6, 346.0, 315.0), (9.2, 10.0, 315.0, 270.0), (12.45, 13.05, 270.0, 180.0), (14.9, 15.45, 180.0, 270.0),
       (16.9, 17.4, 270.0, 180.0), (17.7, 18.25, 180.0, 338.0), (21.3, 21.3, 338.0, 270.0), (22.6, 23.3, 270.0, 330.0), (23.5, 24.8, 330.0, 270.0)]


def _track(moves, t):
    v = moves[0][2]
    for t0, t1, a, b in moves:
        if t < t0:
            break
        v = b if t1 <= t0 else lerp(a, b, ease(t, t0, t1))
    return v


def camera(t):
    """-> dict(oy, sq, zoom, cx, cy)."""
    return dict(oy=_track(_OY, t), sq=_track(_SQ, t), zoom=_track(_ZM, t), cx=_track(_CX, t), cy=_track(_CY, t))


def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]


def sq_y(wy, oy, sq):
    """World y -> screen y. Above the line it is the board's offset. Under it, `sq` px are taken out of the
    first SQ_ZONE px of water, evenly, so the gravel comes up into frame and nothing jumps at the line."""
    if wy <= LINE or sq <= 0:
        return wy - oy
    d = wy - LINE
    if d < SQ_ZONE:
        return LINE - oy + d * (SQ_ZONE - sq) / SQ_ZONE
    return wy - oy - sq


def view_rect(cam):
    z = cam["zoom"]
    w, h = W / z, H / z
    x0 = clamp(cam["cx"] - w / 2, 0, W - w)
    y0 = clamp(cam["cy"] - h / 2, 0, H - h)
    return x0, y0, x0 + w, y0 + h


def _push(ink, cam):
    if cam["zoom"] <= 1.001:
        return
    ink.img = ink.img.resize((W, H), Image.BICUBIC, box=view_rect(cam))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ====================================================================== #
#  2 · THE OCCLUSION GRAPH (animation-45's primitives, as data)           #
# ====================================================================== #

SLOTS = ("hill", "strip", "porch", "board", "sill", "under", "front")   # porch.scene's cast passes, back to front
# ("board" is not a cast pass: it is where the set itself draws the sill, between the porch pass and the sill pass.
#  It is in the list so that an overlap with the board can be declared and measured like any other.)

# (front, back, t0, t1, why): `front` is drawn after `back` whenever both are in the same pass between t0 and t1.
# Names are cel names; * matches. Between passes the set itself decides (STRUCTURAL: porch.scene's order).
DAG = [
    ("queue.near", "queue.far", 0, 26, "down the path is nearer: a cow hides the one behind her"),
    ("cow.mother.*", "cow.lead.*", 0, 26, "the meadow is further along the bank than the strip"),
    ("cow.mother.*", "cow.second.*", 14.0, 26, "the meadow is further along the bank than the strip"),
    ("cow.lead.*", "cow.second.*", 0, 26, "in the meadow the second cow passes behind the lead cow and stands beyond her"),
    ("calf", "cow.mother.body", 0, 26, "the calf walks at her NEAR flank"),
    ("cow.mother.head", "calf", 0, 26, "her head comes down over it (a sublayer: her body stays behind it)"),
    ("cow.lead.head", "shadow.*", 0, 26, "her head hangs over the board (a sublayer: her body is behind the board)"),
    ("pile.*", "shadow.*", 0, 26, "things lie on the board and on their own wet"),
    ("pile.*", "calf", 0, 26, "the calf comes onto the board behind the pile"),
    ("pile.*", "cow.lead.head", 0, 26, "nothing of a cow comes in front of the pile"),
    ("dog*", "shadow.*", 0, 26, "the dog stands on its shadow"),
    ("dog*", "pile.*", 0, 26, "the dog is on the near edge of the board; its paw goes ON the thing"),
    ("dog*", "calf", 0, 26, "the dog is nearer than the calf: it pushes from the water side"),
    ("dog*", "cow.lead.head", 0, 26, "the dog comes up out of the near water, in front of her face"),
    ("dog*", "page.hand", 0, 26, "the hand and the page are back by the step"),
    ("page.hand", "pile.*", 0, 26, "the page is lifted off the pile"),
    ("dog.above", "dog.below", 0, 26, "what is out of the water is in front of the line"),
    ("swim.*", "town", 0, 26, "the dog swims in front of the town"),
    ("bubbles", "town", 0, 26, "its air too"),
    ("weed", "swim.*", 0, 26, "near weed and motes are nearer than the dog"),
    ("weed", "bubbles", 0, 26, "and nearer than its air"),
    ("splash", "dog*", 0, 26, "thrown water is the nearest thing there is"),
]

# Overlap events: between t0 and t1 the two cels really cross on screen and `front` is the one we see.
EVENTS = [
    (0.85, 1.15, "cow.lead.head", "board", "her chin hangs over the board, to the water where the bubbles come up"),
    (1.3, 1.6, "dog*", "cow.lead.*", "the dog bursts up in front of her"),
    (2.0, 2.6, "dog*", "cow.lead.*", "the shake, right under her face"),
    (4.35, 4.9, "dog*", "pile.0", "the paw on the page"),
    (9.05, 9.3, "dog*", "cow.second.*", "in past her muzzle"),
    (13.1, 13.9, "dog*", "cow.second.*", "the reel laid in front of the drinking cow"),
    (13.75, 14.1, "dog*", "pile.1", "the paw on the reel"),
    (16.6, 17.4, "calf", "cow.mother.body", "the calf at her near flank"),
    (17.5, 17.9, "dog*", "calf", "the calf watches over the dog's back"),
    (19.6, 20.2, "dog*", "calf", "the nudge: nose under the calf's chest"),
    (20.85, 21.2, "cow.mother.head", "calf", "her tongue over its head"),
    (24.5, 26.0, "dog*", "cow.mother.*", "the spent dog sits in front of the drinking cow"),
    (24.5, 26.0, "dog*", "calf", "and in front of the calf, which is looking at it"),
]

# A cel changes pass (a discontinuity in depth). It may only do so while it overlaps nothing it jumps over.
# (cel, about when, from, to, what must be true at that frame)
SWITCHES = [
    ("cow.second", "hill", "strip", "she is edge-on in the gate (the paper turn), so she hides nothing"),
    ("cow.mother", "hill", "strip", "edge-on in the gate"),
    ("calf", "hill", "strip", "edge-on in the gate"),
    ("dog", "under", "front", "the water line cuts it: the part above is in front, the part below is under"),
    ("dog", "front", "sill", "it lands on the board: nothing else is in the front pass"),
]

HOLDOUTS = {
    "waterline": "rows below the line are taken out of the dog and given back through water (tinted, thinner)",
    "dry_world": "rows above the line are taken out of the town: the bank, the board and the cows hold it out",
    "wet_board": "porch.surface lays an inch of water over feet on the wet half (STRUCTURAL: the set's order)",
    "rail": "porch draws the rail over the person and the tapping arm over the rail (STRUCTURAL)",
}

CONTACTS = [   # cel, what it stands on, world y of that contact
    ("dog", "the sill", SILL_Y),
    ("pile.*", "the sill", 392.0),
    ("calf", "the strip, then the sill boards", None),
    ("cow.*", "the path strip", STRIP_Y),
]


FELT_PASS = "porch"        # behind the person: while they sit on the step it is hidden by them; when they slide down to
                           # crouch (23.0) it is found lying where it always was


def _match(name, pat):
    return fnmatch.fnmatchcase(name, pat)


def dag_edges(t):
    return [(f, b) for f, b, t0, t1, _ in DAG if t0 <= t <= t1]


def topo(names, t):
    """A draw order (back first) of `names` that respects the DAG at time t, keeping the given order where the
    graph says nothing. Raises on a cycle."""
    edges = dag_edges(t)
    n = len(names)
    after = {i: set() for i in range(n)}        # i must come after these
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i != j and any(_match(a, f) and _match(b, bk) for f, bk in edges):
                after[i].add(j)
    out, done = [], set()
    while len(out) < n:
        for i in range(n):
            if i not in done and after[i] <= done:
                out.append(i)
                done.add(i)
                break
        else:
            raise ValueError("occlusion cycle at t=%.2f among %s" % (t, [names[i] for i in range(n) if i not in done]))
    return out


class View:
    """How a cel gets from the world to the picture. The plain view is the board's: screen = world, shifted up by
    y0 (the crane's offset). A CLOSE view (z > 1) looks at the world rectangle that starts at (x0, y0) and is
    W/z by H/z: a cel drawn through it is drawn again at z times the size, as sharp as it is in the wide shot
    (a closer camera, not an enlargement)."""

    def __init__(self, z=1.0, x0=0.0, y0=0.0):
        self.z, self.x0, self.y0 = float(z), float(x0), float(y0)
        self.hi = abs(self.z - 1.0) > 1e-6

    def X(self, x):
        return (x - self.x0) * self.z

    def Y(self, y):
        return (y - self.y0) * self.z

    def box(self):
        return (self.x0, self.y0, self.x0 + W / self.z, self.y0 + H / self.z)


class Stage:
    """The compositor for one frame. add() a named cel to a pass; play() draws a pass in DAG order. With
    record=True each cel is drawn a second time alone on a clear sheet and its alpha kept in .mattes."""

    def __init__(self, t, record=False):
        self.t, self.record = t, record
        self.cels = []
        self.V = View()            # the view cels are drawn through when play() is given none
        self.order = []            # (slot, name) as drawn
        self.mattes = {}

    def add(self, name, slot, fn):
        self.cels.append((name, slot, fn))

    def play(self, slot, ink, clip=None, V=None, skip=()):
        V = V or self.V
        items = [c for c in self.cels if c[1] == slot and not any(_match(c[0], pat) for pat in skip)]
        for i in topo([c[0] for c in items], self.t):
            name, _, fn = items[i]
            fn(ink, V)
            ink.d = ImageDraw.Draw(ink.img, "RGBA")
            self.order.append((slot, name))
            if self.record:
                lay = kit.Ink(self.t, int(round(self.t * FPS)))
                lay.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                lay.d = ImageDraw.Draw(lay.img, "RGBA")
                fn(lay, V)
                a = lay.img.getchannel("A")
                if clip is not None:                    # the dry_world holdout on everything in the under pass
                    a.paste(0, (0, 0, W, int(clip)))
                self.mattes[name] = a


def _overlap(a, b):
    """Pixels where two mattes are both solid."""
    return int((np.minimum(np.asarray(a), np.asarray(b)) > 96).sum())


def contact_shadow(ink, x, y, rx, amount=1.0, ry=None):
    """A soft dark on the board where something stands: it is what puts a paper animal ON the wood."""
    if amount <= 0.02 or rx < 2:
        return
    ry = ry or max(2.0, rx * 0.16)
    pad = 6
    m = Image.new("L", (int(2 * rx) + 2 * pad, int(2 * ry) + 2 * pad), 0)
    ImageDraw.Draw(m).ellipse([pad, pad, pad + 2 * rx, pad + 2 * ry], fill=int(150 * clamp(amount)))
    m = m.filter(ImageFilter.GaussianBlur(max(1.0, ry * 0.5)))
    lay = Image.new("RGBA", m.size, (26, 14, 30, 0))
    lay.putalpha(m)
    ink.img.paste(lay, (int(x - rx - pad), int(y - ry - pad)), lay)


# ====================================================================== #
#  3 · THE DOG                                                            #
# ====================================================================== #
# Four rounds. The first comes up from S2 with the page. Then: down, dig, up, a reel; again, sooner; again,
# sooner still. Every time below is local seconds. Board marks in brackets where this picture moved off them.

PILE_X = 312.0                                    # the board under the pile's left end (props.pile's x)
THING_X = [PILE_X + props.PILE[k][3] * DS for k in range(5)]    # page, reel, half reel, strip, flange
MOUTH_LAY = 70.0                                  # px from the dog's ground point to its mouth as it lays a thing
PAW_AHEAD = 43.0                                  # px from its ground point to the pressing paw

# ---- round one: the page
T_B1, XB1 = 1.20, 456.0                           # its head breaks the line, under her chin [board 59.2]
T_L1, X_SHAKE = 1.75, 440.0                       # lands on the board
T_SH1, D_SH1 = 1.80, 0.95                         # THE SHAKE [60.0-61.2]; here 59.8-60.75
T_TR1 = 2.75                                      # trots the page to where the person can reach it
X_LAY1 = THING_X[0] + MOUTH_LAY                   # 382
T_LAY1, D_LAY1 = 3.22, 0.85                       # lays it [61.2-62.2]
T_LAID1 = T_LAY1 + 0.62 * D_LAY1 / 1.4            # the jaw lets go
X_PAW1 = THING_X[0] + PAW_AHEAD + 4               # 359
T_PAW1, D_PAW1 = 4.08, 0.80                       # the paw [62.2-63.0]
T_PRESS1 = T_PAW1 + 0.45 * D_PAW1 / 1.5
T_BACK1 = 4.70
BACK_RATE = 2.6                                   # brisk: three steps back, not a retreat                                    # the hand comes for the page; the dog gives it room
X_WAIT = 428.0
T_TURN1 = 7.44                                    # an ear at the first tap; then it turns to the water
T_GO1 = 8.42                                      # on the fourth tap. THE HOLD on the water: 7.85-8.38
X_END = 552.0                                     # the last footing on the board
T_D2 = 9.28                                       # under [67.0]

# ---- round two: the first reel (holes 6 and 3)
HOLE_A, HOLE_B = town.hole_xy(6), town.hole_xy(3)    # (314, 838) nothing; (313, 855) the reel
T_DIG_A, T_DIG_B = 10.42, 11.08
T_FOUND2 = 11.72                                  # it has the reel [70.0]
T_UP2 = 11.86
T_B2, XB2 = 12.62, 454.0                          # breach [71.0]
X_LAY2 = THING_X[1] + MOUTH_LAY                   # 408
T_L2 = 13.02
T_LAID2 = T_L2 + 0.24
X_PAW2 = THING_X[1] + PAW_AHEAD + 2
T_PAW2 = 13.5
T_PRESS2 = T_PAW2 + 0.2
T_SH2 = 14.02                                     # the half shake; the hand taps at 14.2 [72.2]
T_FREEZE = 14.42                                  # it looks at the hand, one ear inside out. HOLD to 14.74
T_GO2 = 14.74                                     # [72.8]
T_D3 = 15.24

# ---- round three: half a reel (hole 5)
HOLE_C = town.hole_xy(5)                          # (571, 844)
T_DIG_C = 15.86
T_FOUND3 = 16.36
T_B3, XB3 = 17.04, 480.0                          # [75.0]
X_LAY3 = THING_X[2] + MOUTH_LAY                   # 437
T_L3 = 17.38
T_LAID3 = T_L3 + 0.22                             # [75.5]; no paw: there was no time
T_TURN3 = 17.74                                   # it does not wait to be asked: it turns to the water [76.0]
T_TROT3 = 17.96
T_WADE = 18.5                                     # off the end of the board, in to its chest
T_STOP = 18.86                                    # it has heard small hooves on the boards
T_TURNBACK = 19.0
T_NUDGE = 19.05                                   # dog.nudge clock: contacts at +0.55 and +1.05 [77.55, 78.05]
T_WATCH = 20.3                                    # watches that it stays, one ear cocked. HOLD 20.45-21.05
T_TURN4 = 21.05
T_D4 = 21.3                                       # under [79.2]

# ---- round four: a strip and a loose flange (hole 4)
TUG_GONE, GIVE_T = 16.5, 21.3                     # score seconds: the reel has come apart by; the dog is back down for the rest at
HOLE_D = town.hole_xy(4)                          # (638, 853)
T_STRIP = 21.74                                   # takes up the strip on the way: its mouth is already full
T_DIG_D = 21.8
T_FOUND4 = 22.16
T_B4, XB4 = 22.80, 506.0                          # [80.6]
X_LAY4 = 470.0                                    # its own place at the waterline; the mouth is over the strip's place
T_L4 = 23.12
T_LAID4 = T_L4 + 0.2
T_SPENT = 23.56                                   # it does not shake. It stands, then it sits.
T_SIT = 23.82
HEAR = (24.15, 24.78)                             # the voice reaches it

WADE_OUT, WADE_DEEP = 48.0, 36.0                  # how far past the board's end it wades, and how deep
DIVES = [(T_D2, 584.0), (T_D3, 580.0), (T_D4, 604.0)]
BREACHES = [(T_B1, XB1), (T_B2, XB2), (T_B3, XB3), (T_B4, XB4)]
DIGS = [   # hole index, start, end, what the gravel gives
    (6, T_DIG_A, T_DIG_A + 0.5, None), (3, T_DIG_B, T_FOUND2, "reel"), (5, T_DIG_C, T_FOUND3, "half"), (4, T_DIG_D, T_FOUND4, "flange"),
]


@lru_cache(maxsize=None)
def carry_sprite(kind, under=False):
    """What is in its mouth, as an image at dog scale 1 (dog.draw_dog hangs it from the mouth)."""
    kw = dict(tint=props.TEAL, tint_amount=0.16) if under else {}
    if kind == "page":
        return props.page_sprite("jaw", flat=0.42, wet=0.0 if under else 0.5, **kw)
    if kind == "reel":
        return props.reel_sprite(props.REEL_FIRST, tilt=0.8, wet=1, **kw)
    if kind == "half":
        return props.reel_sprite(props.REEL_HALF, tilt=0.8, half=True, loop=1.0, wet=1, **kw)
    if kind == "strip":
        return props.part_sprite("strip", weed=0.6, **kw)
    if kind == "both":                               # a strip of film and one loose flange
        a = props.part_sprite("strip", weed=0.4, **kw)
        b = props.part_sprite("flange", weed=0.0, angle=24, **kw)
        im = Image.new("RGBA", (a.width, a.height + 16), (0, 0, 0, 0))
        im.alpha_composite(b, (-14, 12))
        im.alpha_composite(a, (6, 0))
        return im
    raise ValueError(kind)


def _w(p, **kw):
    q = dict(p)
    q.update(kw)
    return q


def _held(p, kind="page"):
    return dog.holding(p, "reel" if kind in ("reel", "half") else "part" if kind in ("strip", "both") else "page")


def _swim_pose(tau, vx, vy, facing, carry=None, effort=1.0):
    """The paddle that goes with a velocity: nose along the way it is going."""
    sp = math.hypot(vx, vy)
    pitch = clamp(math.atan2(-vy, max(facing * vx, 0.12 * sp + 1e-6)), -1.42, 1.42)
    if pitch < -0.35:
        p = dog.swim_down(tau, steep=-pitch)
    elif pitch > 0.35:
        p = dog.swim_up(tau, steep=pitch)
    else:
        p = dog.swim(tau, pitch=pitch, effort=effort)
    fast = clamp((sp - 250) / 400)
    if fast > 0:                                       # going hard: ears and tail stream, legs trail
        p["ear"], p["ear_f"] = lerp(p["ear"], 0.02, fast), lerp(p["ear_f"], 0.0, fast)
        p["tail"] = lerp(p["tail"], -0.1, fast)
    if carry:
        p = _held(p, carry)
    p["_anchor"] = "body"
    return p


def _as_body(pose, x, y, facing):
    """A ground pose handed over as a body-anchored one (so it can be blended with swimming)."""
    bx, by = dog.body_point(pose, x, y, DS, facing)
    q = dict(pose)
    q["_anchor"] = "body"
    return q, bx, by


@lru_cache(maxsize=None)
def _probe(name, facing):
    im = Image.new("RGB", (8, 8))
    pose = {"dig": dog.dig(0.9), "stand": dog.stand(0.0)}[name]
    j = dog.draw_dog(im, pose, 0, 0, scale=DS, facing=facing, shadow=False)
    return {k: j[k] for k in ("fn.paw", "mouth", "nose", "body")}


def _dig_anchor(hole, facing=-1):
    """Where the dog's ground point is when its raking paw is in `hole`."""
    return hole[0] - _probe("dig", facing)["fn.paw"][0] + 2 * facing, hole[1] - 5.0


XA_A, GY_A = _dig_anchor(HOLE_A)
XA_B, GY_B = _dig_anchor(HOLE_B)
XA_C, GY_C = _dig_anchor(HOLE_C)
XA_D, GY_D = _dig_anchor(HOLE_D)


def _stand_body(x, gy, facing=-1, pose=None):
    q, bx, by = _as_body(pose or dog.stand(0.0), x, gy, facing)
    return q, bx, by


def _blend_body(pa, a_xy, pb, b_xy, w):
    p = dog.blend(pa, pb, w)
    p["_anchor"] = "body"
    return p, lerp(a_xy[0], b_xy[0], w), lerp(a_xy[1], b_xy[1], w)


def _flip(t, t0, dur, a, b):
    """Facing through a paper turn: a -> b over dur seconds from t0, never quite edge-on."""
    f = lerp(a, b, ease(t, t0, t0 + dur))
    if abs(f) < 0.12:
        f = 0.12 if (t - t0) < dur / 2 else -0.12
        f *= 1 if a > 0 else -1
    return f


def _dive(t, t0, x0, facing=1):
    """The half second from the board into the water: a gathered leap, nose first. -> pose, x, y (body)."""
    tau = t - t0
    p = dog.swim_down(tau + 0.3, steep=lerp(0.5, 1.15, ease(tau, -0.3, 0.05)))
    p["_anchor"] = "body"
    return p


def _dog_under(t):
    """Under water (and through the line). All body-anchored. -> dict or None."""
    S = dict(anchor="body", where="swim", carry=None, facing=-1, bits=None, silt=None)
    # ---- round one: up from S2's last frame with the page
    if t < T_B1:
        keys = [(-0.6, 438.0, 574.0), (0.0, 430.0, 550.0), (0.45, 432.0, 512.0), (0.85, 444.0, 462.0), (T_B1, XB1, 410.0), (T_B1 + 0.2, XB1 + 2, 372.0)]
        x, y, vx, vy = _hermite(keys, t)
        p = dog.carry_page(t + 30.0, gait="swim_up", steep=lerp(0.78, 1.16, ease(t, 0.15, 0.8)))
        lk = (1 - ease(t, 0.0, 0.35))                               # it was looking up at her as S2 ended
        p["hold"] = 1.0
        p["_anchor"] = "body"
        S.update(x=x, y=y, pose=p, carry="page")
        return S
    # ---- round two: down to holes 6 and 3, far left; two digs; the first reel
    if T_D2 <= t < T_B2:
        dn = [(T_D2 - 0.12, 566.0, 372.0), (T_D2, 586.0, 402.0), (T_D2 + 0.3, 588.0, 492.0), (T_D2 + 0.62, 520.0, 628.0),
              (T_DIG_A - 0.18, XA_A + 14, GY_A - 78.0), (T_DIG_A - 0.02, XA_A, GY_A - 42.5)]
        if t < T_DIG_A - 0.02:
            x, y, vx, vy = _hermite(dn, t)
            fc = _flip(t, T_D2 + 0.16, 0.26, 1, -1)                 # it rolls over as it goes straight down
            p = _swim_pose(t - T_D2, vx, vy, 1 if fc > 0 else -1)
            land = ease(t, T_DIG_A - 0.2, T_DIG_A - 0.02)
            if land > 0:
                q, bx, by = _stand_body(XA_A, GY_A, -1, dog.dig(0.0))
                p, x, y = _blend_body(p, (x, y), q, (bx, by), land)
            S.update(x=x, y=y, pose=p, facing=fc)
            return S
        if t < T_DIG_B:                                             # dig one: nothing. It looks in.
            tau = t - T_DIG_A
            d = dog.dig(tau + 0.42)
            look = ease(tau, 0.5, 0.58)
            if look > 0:
                d = dog.blend(d, _w(dog.dig(0.2), neck=0.05, head=-0.62, ear=1.15, ear_f=0.7, tail=0.2), look)
            xg = lerp(XA_A, XA_B, ease(t, T_DIG_B - 0.12, T_DIG_B))
            gy = lerp(GY_A, GY_B, ease(t, T_DIG_B - 0.12, T_DIG_B))
            q, bx, by = _as_body(d, xg, gy, -1)
            S.update(x=bx, y=by, pose=q, where="dig", bits=(dog.dig_spray(tau + 0.42, water=True) if tau < 0.56 else None, xg, gy),
                     silt=(HOLE_A, tau))
            return S
        if t < T_UP2:                                               # dig two: the can
            tau = t - T_DIG_B
            d = dog.dig(tau + 0.42)
            got = ease(t, T_FOUND2 - 0.06, T_FOUND2 + 0.1)
            carry = None
            if got > 0:
                d = dog.blend(d, _held(_w(dog.stand(t), neck=0.5, head=0.1, ear=1.1, ear_f=1.12, tail=0.5), "reel"), got)
                carry = "reel"
            q, bx, by = _as_body(d, XA_B, GY_B, -1)
            S.update(x=bx, y=by, pose=q, where="dig", carry=carry,
                     bits=(dog.dig_spray(tau + 0.42, water=True) if t < T_FOUND2 + 0.3 else None, XA_B, GY_B), silt=(HOLE_B, tau))
            return S
        q0, bx0, by0 = _as_body(_held(_w(dog.stand(t), neck=0.5, head=0.1, ear=1.1, ear_f=1.12, tail=0.5), "reel"), XA_B, GY_B, -1)
        up = [(T_UP2 - 0.1, bx0, by0 + 6), (T_UP2, bx0, by0), (T_UP2 + 0.3, bx0 + 34, by0 - 130), (T_B2 - 0.2, XB2 + 12, 500.0),
              (T_B2, XB2, 410.0), (T_B2 + 0.15, XB2 - 6, 372.0)]
        x, y, vx, vy = _hermite(up, t)
        p = _swim_pose(t - T_UP2, vx, vy, -1, "reel")
        off = ease(t, T_UP2, T_UP2 + 0.16)
        if off < 1:
            p, x, y = _blend_body(q0, (bx0, by0), p, (x, y), off)
        S.update(x=x, y=y, pose=p, carry="reel")
        return S
    # ---- rounds three and four: straight down, one dig, straight up
    for (td, xd, hole, xa, gy, tdig, tfound, tb, xb, thing) in (
            (T_D3, 580.0, HOLE_C, XA_C, GY_C, T_DIG_C, T_FOUND3, T_B3, XB3, "half"),
            (T_D4, 604.0, HOLE_D, XA_D, GY_D, T_DIG_D, T_FOUND4, T_B4, XB4, "both")):
        if not (td <= t < tb):
            continue
        last = thing == "both"
        q_dig0, bxd, byd = _stand_body(xa, gy, -1, dog.dig(0.0))
        if t < tdig:
            dn = [(td - 0.12, xd - 18, 372.0), (td, xd + 2, 402.0), (lerp(td, tdig, 0.45), lerp(xd, xa, 0.5) + 10, 610.0),
                  (tdig - 0.1, bxd + 4, byd - 60.0), (tdig, bxd, byd)]
            x, y, vx, vy = _hermite(dn, t)
            fc = _flip(t, tdig - 0.24, 0.2, 1, -1)
            p = _swim_pose(t - td, vx, vy, 1 if fc > 0 else -1, "strip" if (last and t >= T_STRIP) else None)
            land = ease(t, tdig - 0.12, tdig)
            if land > 0:
                p, x, y = _blend_body(p, (x, y), q_dig0, (bxd, byd), land)
            S.update(x=x, y=y, pose=p, facing=fc, carry="strip" if (last and t >= T_STRIP) else None)
            return S
        t_up = tfound + 0.06
        if t < t_up:
            tau = t - tdig
            d = dog.dig(tau + 0.44, rate=3.6 if last else 3.2)
            carry = "strip" if last else None
            if last:
                d = _held(d, "strip")
            got = ease(t, tfound - 0.07, tfound + 0.05)
            if got > 0:
                d = dog.blend(d, _held(_w(dog.stand(t), neck=0.5, head=0.12, ear=1.1, ear_f=1.12, tail=0.45), thing), got)
                if got > 0.5:
                    carry = thing
            q, bx, by = _as_body(d, xa, gy, -1)
            S.update(x=bx, y=by, pose=q, where="dig", carry=carry, bits=(dog.dig_spray(tau + 0.44, water=True), xa, gy), silt=(hole, tau))
            return S
        q0, bx0, by0 = _as_body(_held(_w(dog.stand(t), neck=0.5, head=0.12, ear=1.1, ear_f=1.12, tail=0.45), thing), xa, gy, -1)
        up = [(t_up - 0.1, bx0, by0 + 6), (t_up, bx0, by0), (lerp(t_up, tb, 0.5), lerp(bx0, xb, 0.55), 610.0), (tb, xb, 410.0), (tb + 0.15, xb - 6, 372.0)]
        x, y, vx, vy = _hermite(up, t)
        p = _swim_pose(t - t_up, vx, vy, -1, thing)
        off = ease(t, t_up, t_up + 0.12)
        if off < 1:
            p, x, y = _blend_body(q0, (bx0, by0), p, (x, y), off)
        S.update(x=x, y=y, pose=p, carry=thing)
        return S
    return None


def _burst(t, tb, xb, land_x, dur, thing):
    tau = t - tb
    x, y = dog.burst_path(tau, (xb, 410.0), (land_x, SILL_Y), DS, height=30.0, dur=dur)
    p = _held(dog.burst(tau, dur=dur), thing)
    p["_anchor"] = "body"
    return dict(anchor="body", where="air", x=x, y=y, pose=p, facing=-1, carry=thing, bits=None, silt=None)


def _landed(kind=None):
    """The bottom of a landing: legs folded under the weight, head still up with the thing."""
    p = _w(dog.stand(0.0), cy=dog.stand(0.0)["cy"] - 13, pitch=-0.06, neck=0.7, head=0.05, ear=0.25, ear_f=0.22, tail=-0.2)
    return _held(p, kind) if kind else p


def _ground(x, pose, facing=-1, carry=None, **kw):
    pose = dict(pose)
    pose["_anchor"] = "ground"
    d = dict(anchor="ground", where="sill", x=x, y=SILL_Y, pose=pose, facing=facing, carry=carry, bits=None, silt=None)
    d.update(kw)
    return d


def _leap_in(t, t0, x0, x1, dur=0.5):
    """From the board into the creek: gathers, goes, nose first. Body-anchored; ends at the line at x1."""
    tau = (t - t0) / dur
    bx0, by0 = dog.body_point(dog.stand(0), x0, SILL_Y, DS, 1)
    crouch = bump(tau / 0.36)
    x = lerp(bx0, x1, ease(tau, 0.1, 1.0))
    arc = math.sin(math.pi * clamp((tau - 0.2) / 0.8))
    y = lerp(by0, LINE + 2, ease(tau, 0.3, 1.0) ** 1.5) - 26 * arc + 5 * crouch
    st = dog.trot(0.12)
    st["_anchor"] = "body"
    dv = dog.swim_down(tau * 0.4, steep=lerp(0.2, 1.1, ease(tau, 0.3, 1.0)))
    dv["_anchor"] = "body"
    p = dog.blend(st, dv, ease(tau, 0.12, 0.42))
    p["_anchor"] = "body"
    p["ear"], p["ear_f"] = lerp(1.0, 0.05, ease(tau, 0.2, 0.5)), lerp(1.0, 0.02, ease(tau, 0.2, 0.5))
    return dict(anchor="body", where="air", x=x, y=y, pose=p, facing=1, carry=None, bits=None, silt=None)


def _trot_to(t, t0, x0, x1, rate=2.4, carry=None, facing=None):
    """Trot from x0 toward x1 without sliding a foot. -> (x, pose, arrived)."""
    f = 1 if x1 > x0 else -1
    dist = DS * dog.travel("trot", t - t0, rate)
    arrived = dist >= abs(x1 - x0)
    x = x1 if arrived else x0 + f * dist
    p = dog.carry_page(t - t0, gait="trot", rate=rate) if carry == "page" else dog.trot(t - t0, rate=rate)
    if carry:
        p = _held(p, carry)
    return x, p, arrived


def _trot_time(x0, x1, rate=2.4):
    return abs(x1 - x0) / (DS * dog.STRIDE["trot"] * rate)


def _lay_clock(t, t0, dur):
    return (t - t0) * 1.4 / dur


def dog_state(t):
    """Where the lead dog is and what it is doing at local t -> dict(anchor, where, x, y, pose, facing, carry,
    bits, silt, depth). where: swim | dig | air | sill | wade."""
    t = clamp(t, 0.0, SECONDS)
    u = _dog_under(t)
    if u is not None:
        return u
    # ================= round one, on the board =================
    if t < T_L1:
        return _burst(t, T_B1, XB1, X_SHAKE, T_L1 - T_B1, "page")
    if t < T_TR1:                                                    # THE SHAKE: but the page is held out of it
        tau = t - T_SH1
        steady = _w(dog.carry_page(t, gait="stand"), neck=0.62, head=0.16)
        if tau < 0:
            p = dog.blend(_landed("page"), dog.shake(0.0, dur=D_SH1), ease(t, T_L1, T_SH1))   # the landing is still in its legs
            p = dog.blend(p, steady, {"head": 0.86})
        else:
            p = dog.shake(tau, dur=D_SH1)
            p = dog.blend(p, steady, {"head": 0.86})                # a stiff neck: the child's page is not shaken
            p["look"], p["sway"] = 0.0, 0.25 * p["sway"]
        p = _held(p, "page")
        bits = dog.shake_drops(tau, dur=D_SH1) if tau > 0 else None
        return _ground(X_SHAKE, p, carry="page", bits=(bits, X_SHAKE, SILL_Y), shake=(T_SH1, D_SH1))
    if t < T_LAY1:
        x, p, arr = _trot_to(t, T_TR1, X_SHAKE, X_LAY1, 2.1, "page")
        if arr:
            p = dog.blend(p, _held(dog.lay(0.0), "page"), ease(t, T_LAY1 - 0.1, T_LAY1))
        return _ground(x, p, carry="page")
    if t < T_PAW1:
        c = _lay_clock(t, T_LAY1, D_LAY1)
        p = dog.lay(c)
        st = ease(t, T_PAW1 - 0.24, T_PAW1)                          # one step in, to get a paw to it
        x = lerp(X_LAY1, X_PAW1, st)
        if 0 < st < 1:
            p = dog.blend(p, dog.walk(0.35 + 0.4 * st), bump(st) * 0.8)
        return _ground(x, p, carry="page" if p["hold"] >= 0.5 else None)
    if t < T_BACK1:
        c = (t - T_PAW1) * 1.5 / D_PAW1
        return _ground(X_PAW1, dog.paw_press(min(c, 1.5)), press=True)
    if t < T_TURN1:
        # the hand comes for the page: the dog gives it exactly the room it wants, and watches what the lamp does
        tb = t - T_BACK1
        dist = min(X_WAIT - X_PAW1, -DS * dog.travel("back_away", tb, BACK_RATE))
        x = X_PAW1 + dist
        if dist < X_WAIT - X_PAW1 - 0.01:
            p = dog.blend(dog.back_away(tb + 0.25, rate=BACK_RATE), dog.stand(t), 0.35)
            p["ear"], p["ear_f"], p["tail"] = max(p["ear"], 0.6), max(p["ear_f"], 0.62), max(p["tail"], 0.0)
            p = dog.blend(dog.paw_press((T_BACK1 - T_PAW1) * 1.5 / D_PAW1), p, ease(t, T_BACK1, T_BACK1 + 0.16))
        else:
            t_arr = T_BACK1 + (X_WAIT - X_PAW1) / (DS * 44.0 * BACK_RATE)
            w = dog.watch(t)
            see = ease(t, 5.82, 6.1) * (1 - ease(t, 6.74, 7.0))    # the picture on the door: head up, tail going
            w = dog.look_up(w, 0.42 * see)
            w["wag"] = 0.5 * math.sin(2 * math.pi * 2.4 * t) * see
            w["tail"] = lerp(w["tail"], 0.55, see)
            w["ear"], w["ear_f"] = lerp(w["ear"], 1.15, see), lerp(w["ear_f"], 1.15, see)
            hear = ease(t, 7.32, 7.42)                                # the first tap: one ear
            w["ear"] = lerp(w["ear"], 0.35, hear)
            p = dog.blend(dog.back_away(t_arr - T_BACK1 + 0.25, rate=BACK_RATE), w, ease(t, t_arr, t_arr + 0.3))
        return _ground(x, p)
    if t < T_GO1:
        # it turns to the water, and holds
        fc = _flip(t, T_TURN1, 0.3, -1, 1)
        w = dog.watch(7.0)
        w["ear"], w["ear_f"] = lerp(0.35, 1.18, ease(t, T_TURN1 + 0.2, T_TURN1 + 0.32)), lerp(1.0, 1.18, ease(t, T_TURN1 + 0.2, T_TURN1 + 0.32))
        w["neck"], w["head"] = w["neck"] - 0.14 * ease(t, T_TURN1 + 0.2, T_TURN1 + 0.34), w["head"] - 0.1 * ease(t, T_TURN1 + 0.2, T_TURN1 + 0.34)
        w["tail"] = lerp(0.1, 0.42, ease(t, T_GO1 - 0.14, T_GO1))    # the tail lifts: it has decided
        return _ground(X_WAIT, w, facing=fc)
    if t < T_D2:
        t_leap = T_D2 - 0.42
        if t < t_leap:
            x, p, arr = _trot_to(t, T_GO1, X_WAIT, X_END - 26, _trot_rate(X_WAIT, X_END - 26, t_leap - T_GO1))
            return _ground(x, p, facing=1)
        return _leap_in(t, t_leap, X_END - 26, 584.0, 0.42)
    # ================= round two, on the board =================
    if t < T_L2:
        return _burst(t, T_B2, XB2, X_LAY2, T_L2 - T_B2, "reel")
    if t < T_PAW2:
        c = (t - T_L2 + 0.06) * 1.4 / 0.52
        p = dog.lay(c)
        if t < T_L2 + 0.12:
            p = dog.blend(_landed("reel"), p, ease(t, T_L2, T_L2 + 0.12))
        st = ease(t, T_PAW2 - 0.16, T_PAW2)
        x = lerp(X_LAY2, X_PAW2, st)
        if 0 < st < 1:
            p = dog.blend(p, dog.walk(0.35 + 0.4 * st), bump(st) * 0.8)
        return _ground(x, p, carry="reel" if t < T_LAID2 else None)
    if t < T_SH2:
        c = (t - T_PAW2) * 1.5 / 0.62
        return _ground(X_PAW2, dog.paw_press(min(c, 1.5)), press=True)
    if t < T_GO2:
        # half a shake. The hand taps. It stops in the middle of it and looks at the hand: one ear inside out.
        tau = min(t, T_FREEZE) - T_SH2
        p = dog.shake(tau, dur=1.1)
        lookh = ease(t, T_FREEZE - 0.06, T_FREEZE + 0.06)
        if lookh > 0:
            fr = _w(dog.shake(T_FREEZE - T_SH2, dur=1.1), twist=0.0, sway=0.0, look=0.0)
            fr = _w(fr, neck=0.92, head=0.02, ear=1.16, ear_f=-0.55, eye=1.25, tail=0.05, curl=0.3, wag=0.0)
            p = dog.blend(p, fr, lookh)
        bits = dog.shake_drops(t - T_SH2, dur=1.1) if t < T_FREEZE + 0.5 else None
        return _ground(X_PAW2, p, bits=(bits, X_PAW2, SILL_Y), shake=(T_SH2, 0.5))
    if t < T_D3:
        fc = _flip(t, T_GO2, 0.12, -1, 1)
        t_leap = T_D3 - 0.34
        if t < t_leap:
            x, p, arr = _trot_to(t, T_GO2 + 0.04, X_PAW2, X_END - 60, _trot_rate(X_PAW2, X_END - 60, t_leap - T_GO2 - 0.04))
            p["ear_f"] = lerp(-0.55, p["ear_f"], ease(t, T_GO2 + 0.1, T_GO2 + 0.3))     # the ear comes right as it runs
            return _ground(x, p, facing=fc)
        return _leap_in(t, t_leap, X_END - 60, 580.0, 0.34)
    # ================= round three, on the board =================
    if t < T_L3:
        return _burst(t, T_B3, XB3, X_LAY3, T_L3 - T_B3, "half")
    if t < T_TURN3:
        c = (t - T_L3 + 0.06) * 1.4 / 0.5
        p = dog.lay(min(c, 0.95))                                   # it does not even look up
        if t < T_L3 + 0.1:
            p = dog.blend(_landed("half"), p, ease(t, T_L3, T_L3 + 0.1))
        return _ground(X_LAY3, p, carry="half" if t < T_LAID3 else None)
    if t < T_TROT3:
        fc = _flip(t, T_TURN3, 0.2, -1, 1)
        p = dog.blend(dog.lay(0.95), dog.trot(0.0), ease(t, T_TURN3, T_TROT3))
        return _ground(X_LAY3, p, facing=fc)
    if t < T_WADE:
        x, p, arr = _trot_to(t, T_TROT3, X_LAY3, X_END, _trot_rate(X_LAY3, X_END, T_WADE - T_TROT3))
        return _ground(x, p, facing=1)
    if t < T_TURNBACK:
        # off the end of the board, in to its chest. Then it stops: small hooves on the boards behind it.
        tau = t - T_WADE
        dep = WADE_DEEP * ease(tau, 0.0, 0.3)
        x = X_END + min(WADE_OUT, DS * dog.travel("wade", tau, 2.6))
        p = dog.wade(tau, depth=0.8, rate=2.6)
        stop = ease(t, T_STOP - 0.1, T_STOP)
        if stop > 0:
            p = dog.blend(p, _w(dog.watch(t), ear=0.2, ear_f=1.1), stop)
            p = dog.over_shoulder(p, 0.85 * ease(t, T_STOP + 0.0, T_STOP + 0.12))
        return _ground(x, p, facing=1, where="wade", depth=dep)
    if t < T_TURN4:
        # THE WEAVE. It turns back, puts its head down level with the calf's shoulder, and noses it up the board.
        tau = t - T_NUDGE
        fc = _flip(t, T_TURNBACK, 0.16, 1, -1)
        p = dog.nudge(max(0.0, tau))
        if tau < 0.12:
            p = dog.blend(dog.over_shoulder(_w(dog.watch(t), ear=0.2, ear_f=1.1), 0.85 * (1 if fc > 0 else 0)), p, ease(t, T_TURNBACK + 0.02, T_NUDGE + 0.12))
        push = sum(ease(tau, 0.42 + 0.5 * i, 0.74 + 0.5 * i) for i in range(2))
        back = ease(t, T_WATCH - 0.05, T_WATCH + 0.4)
        x = X_END + WADE_OUT - 15 * push + 22 * back                 # each push it gains a little of the board; then it backs off
        dep = WADE_DEEP - 11 * push + 12 * back
        if t >= T_WATCH - 0.05:                                      # watches that it stays; one ear cocked
            w = _w(dog.watch(t), ear=1.15, ear_f=0.3, tail=0.2, neck=0.62, head=0.0)
            p = dog.blend(p, w, ease(t, T_WATCH - 0.05, T_WATCH + 0.12))
            if 0 < back < 1:
                p = dog.blend(p, dog.wade(0.3 + 0.5 * back, depth=0.8), 0.6 * bump(back))
        return _ground(x, p, facing=fc, where="wade", depth=dep)
    if t < T_D4:
        fc = _flip(t, T_TURN4, 0.1, -1, 1)
        tau = (t - T_TURN4) / (T_D4 - T_TURN4)
        x0 = X_END + WADE_OUT - 30 + 22
        d0 = WADE_DEEP - 22 + 12
        w = _w(dog.watch(t), ear=0.4, ear_f=0.4, tail=0.2, neck=0.62, head=0.0)
        if tau < 0.4:
            return _ground(x0, dog.blend(w, dog.wade(0.2, depth=0.8), tau / 0.4), facing=fc, where="wade", depth=d0)
        bx0, by0 = dog.body_point(dog.wade(0.2, depth=0.8), x0, SILL_Y + d0, DS, 1)
        k = (tau - 0.4) / 0.6
        st = dict(dog.wade(0.2, depth=0.8))
        st["_anchor"] = "body"
        dv = dog.swim_down(0.2, steep=1.15)
        dv["_anchor"] = "body"
        p = dog.blend(st, dv, ease(k, 0.0, 0.6))
        p["_anchor"] = "body"
        return dict(anchor="body", where="air", x=lerp(bx0, 604.0, ease(k, 0, 1)), y=lerp(by0, LINE + 2, k * k) - 8 * bump(k), pose=p,
                    facing=1, carry=None, bits=None, silt=None)
    # ================= round four, on the board: spent =================
    if t < T_L4:
        return _burst(t, T_B4, XB4, X_LAY4, T_L4 - T_B4, "both")
    tired = dog.tired(t)
    if t < T_SPENT:
        c = (t - T_L4 + 0.05) * 1.4 / 0.6
        p = dog.lay(min(c, 0.9))                                    # the head goes down and lets go, and stays down
        if t < T_L4 + 0.1:
            p = dog.blend(_landed("both"), p, ease(t, T_L4, T_L4 + 0.1))
        p = dog.blend(p, tired, ease(t, T_LAID4 + 0.12, T_SPENT))
        return _ground(X_LAY4, p, carry="both" if t < T_LAID4 else None)
    return _ground(X_LAY4, end_pose(t))


def end_pose(t):
    """The spent dog: it stands with its legs apart, then sits, head low, flanks going. No shake. (This is the
    pose S4 begins from: at t = 26.0 it is sitting at (470, 394), facing left, head low, ears half down.)"""
    tired = dog.tired(t)
    if t < T_SIT:
        return tired
    sit = dog.sit(t - T_SIT)
    pant = math.sin(2 * math.pi * 2.6 * t) * (1 - 0.55 * ease(t, 24.6, 25.4))
    p = dog.blend(sit, tired, {"head": 0.9, "ears": 0.75, "tail": 1.0})
    p["neck"], p["head"] = -0.72, -1.04                                       # it hangs
    p["pitch"] = sit["pitch"] - 0.15                                          # slumped on its haunches
    p["cy"] = p["cy"] - 4
    p["jaw"], p["tongue"] = 0.2 + 0.05 * pant, 0.8
    p["ear"], p["ear_f"] = 0.36, 0.32
    p["tail"], p["wag"] = -0.5, 0.0
    # the quiet voice: the head comes up a little, the mouth shuts. Low, not hanging: this is the pose S4 takes up
    # (s4.lead_porch at 84.0: sitting, ears down, the head hanging a little), so the cut between us is not a jump.
    hear = ease(t, HEAR[0], HEAR[1])
    if hear > 0:
        s9 = dog.sit(9.0)
        low = dog.blend(s9, dog.ears_down(3.0), {"ears": 0.6, "head": 1.0, "tail": 0.5, "body": 0.3, "legs": 0.0})
        low["neck"], low["head"] = low["neck"] - 0.12, low["head"] - 0.1
        p = dog.blend(p, low, hear)
    breathe = 1.0 - 0.8 * ease(t, 25.2, 25.95)                                # the flanks going, and settling
    p["arch"] = p.get("arch", 0.0) + 0.02 * pant * breathe
    p["cy"] = p["cy"] + 0.5 * pant * breathe
    return dog.blend(tired, p, ease(t, T_SIT, T_SIT + 0.5))


def _trot_rate(x0, x1, dur):
    """The trot rate that covers x0..x1 in dur seconds (the dog is hurrying: it may be well over a trot)."""
    return abs(x1 - x0) / (DS * dog.STRIDE["trot"] * max(dur, 0.05))


@lru_cache(maxsize=4096)
def _dog_points(k):
    """Screen points of the dog at frame k in F-PORCH (oy 0, no squeeze): nose, mouth, paws, bbox."""
    t = k / FPS
    st = dog_state(t)
    im = Image.new("RGB", (8, 8))
    j = dog.draw_dog(im, st["pose"], st["x"], st["y"] + st.get("depth", 0.0), scale=DS, facing=st["facing"], shadow=False,
                     anchor=st["anchor"], carry=None)
    return j


def dog_nose(t):
    return _dog_points(int(round(t * FPS)))["nose"]


def dog_wet(t):
    """Seconds since it last came out of the water (for the drips)."""
    last = max([tb for tb, _ in BREACHES if tb <= t] or [-99])
    return t - last


# ====================================================================== #
#  4 · THE HERD (one at a time; their tempo never changes)                #
# ====================================================================== #

SPOT = [herd.hill_spot(k) for k in range(6)]                 # where the queue waits: 0 just above the gate
def D(x):
    """The distance along herd.PATH at which a cow stands at world x (herd.d_at is 2 px out on the strip)."""
    d = herd.d_at(x)
    for _ in range(3):
        d -= herd.PATH.at(d)["x"] - x
    return d


X_DRINK = 600.0 - herd.reach("second")                        # where a plain cow stands to drink at x = 600
X_LEAD0 = 600.0 - herd.reach("lead")                          # where S2 left the lead cow
X_LEAD_TURNED = XB1 + 12 + herd.reach("lead")                 # turned round, chin over where the dog comes up
X_LEAD_BACK = X_LEAD_TURNED + 40.0                            # she backs a step when it bursts up under her
T_LEAD_WALK = 4.3
X_LEAD_FAR = 880.0                                            # where she goes to stand when she has drunk
X_LEAD_MEADOW = 806.0                                         # and where she comes back to, to see the dog (S4 begins with her here)
T_LEAD_BACK = 21.6
X_SECOND_MEADOW = 892.0                                       # and the second beyond her
T_SEC_TURN = 22.95
X_MOTHER_DRINK = 515.0
X_CALF_END, Y_CALF_END = 408.0, 391.0                         # S4: pressed to her mother's flank, looking at the dog
T_LEAD_LOOK = 17.25                                           # in the meadow she turns to see what the splashing is
X_MOTHER_WAIT = 396.0
T_CALF_GO = 18.08                                             # the calf leaves its mother's side [76.2]
X_CALF_STOP = 376.0
X_CALF_SKID = 472.0
T_CALF_SKID = 18.84
T_LICK = 20.72                                                # her tongue goes once over its head [79.0]
T_M_ON = 21.36                                                # she walks on to the water
T_M_DRINK = 24.3


def _walkers():
    global _WK
    if _WK is None:
        P = herd.PATH
        wk = {}
        wk["lead"] = herd.Walker("lead", P, [(T_LEAD_WALK, D(X_LEAD_BACK)), (10.75, D(X_LEAD_FAR)), (40.0, D(X_LEAD_FAR))])
        rb = herd.Route([(X_LEAD_FAR, porch.meadow_y(X_LEAD_FAR), 1.0), (X_LEAD_MEADOW, porch.meadow_y(X_LEAD_MEADOW), 1.0)])
        wk["lead2"] = herd.Walker("lead", rb, [(T_LEAD_BACK, 0.0), (T_LEAD_BACK + rb.length / 44.0, rb.length), (40.0, rb.length)])
        wk["second"] = herd.Walker("second", P, [(-5.0, SPOT[0]), (4.35, SPOT[0]), (8.75, D(X_DRINK)), (14.55, D(X_DRINK)), (22.7, D(X_SECOND_MEADOW)), (40.0, D(X_SECOND_MEADOW))],
                                   acts=[(8.8, 14.0, lambda tau: herd.drink(tau + 8.8, clamp(tau / 0.9), "second"))])
        wk["mother"] = herd.Walker("mother", P, [(-5.0, SPOT[1]), (4.8, SPOT[1]), (9.8, SPOT[0]), (15.0, SPOT[0]), (18.35, D(X_MOTHER_WAIT)),
                                               (T_M_ON, D(X_MOTHER_WAIT)), (T_M_DRINK - 0.1, D(X_MOTHER_DRINK)), (40.0, D(X_MOTHER_DRINK))],
                                   acts=[(18.5, T_LICK - 0.1, lambda tau: herd.notice(herd.stand(tau + 18.5, "mother", chew=0, alert=0.35))),
                                         (T_LICK, T_LICK + 0.62, _lick_pose),
                                         (T_M_DRINK, 40.0, lambda tau: herd.drink(tau + T_M_DRINK, clamp(tau / 0.85), "mother"))])
        wk["calfA"] = herd.Walker("calf", P, [(-5.0, SPOT[2]), (5.2, SPOT[2]), (10.2, SPOT[1]), (40.0, SPOT[1])])
        wk["calfB"] = herd.Walker("calf", P, [(15.35, SPOT[1]), (17.5, D(X_CALF_STOP)), (40.0, D(X_CALF_STOP))], gait="trot")
        r = herd.Route([(X_CALF_STOP, STRIP_Y, 1.0), (412.0, SILL_Y, 1.0), (X_CALF_SKID, SILL_Y, 1.0)])
        wk["calfC"] = herd.Walker("calf", r, [(T_CALF_GO, 0.0), (T_CALF_SKID, r.length), (40.0, r.length)], gait="trot")
        wk["fourth"] = herd.Walker("fourth", P, [(-5.0, SPOT[3]), (5.6, SPOT[3]), (10.5, SPOT[2]), (15.5, SPOT[2]), (24.2, SPOT[0]), (40.0, SPOT[0])])
        wk["fifth"] = herd.Walker("fifth", P, [(-5.0, SPOT[4]), (16.0, SPOT[4]), (24.4, SPOT[1]), (40.0, SPOT[1])])
        wk["sixth"] = herd.Walker("sixth", P, [(-5.0, SPOT[5]), (16.6, SPOT[5]), (24.3, SPOT[2]), (40.0, SPOT[2])])
        _WK = wk
    return _WK


_WK = None


def _lick_pose(tau):
    a = herd.stand(tau, "mother", chew=0)
    return herd.with_(a, pitch=3.0, dy=2.0, shoulder=4.0, neck=52.0, head=-6.0 + 9.0 * math.sin(math.pi * clamp(tau / 0.6)), ear=14.0, eye=0.8,
                      jaw=5.0, _nose=1.0)


def _bell_swing(t):
    """The lead cow's bell while she is played by hand (0 .. T_LEAD_WALK): it jumps when she jerks her head up,
    rattles under the shake, swings as she turns. Degrees."""
    a = 0.0
    for t0, amp, f, damp in ((0.3, 14.0, 2.1, 2.0), (T_B1, 46.0, 2.6, 2.2), (3.4, 18.0, 2.0, 1.6)):
        if t > t0:
            a += amp * math.sin(2 * math.pi * f * (t - t0)) * math.exp(-damp * (t - t0))
    sh = ease(t, T_SH1 + 0.15, T_SH1 + 0.3) * (1 - ease(t, T_SH1 + D_SH1 - 0.2, T_SH1 + D_SH1 + 0.3))
    a += 16.0 * sh * math.sin(2 * math.pi * 5.5 * t)
    return a


LEAD_BELL_HITS = [0.42, T_B1 + 0.06, T_B1 + 0.28, T_SH1 + 0.3, T_SH1 + 0.5, T_SH1 + 0.7, 3.6]     # for the sound


def lead_state(t):
    """The lead cow -> dict(x, y, pose, facing, turn, nose_to, layer, s, squash)."""
    wk = _walkers()
    if t >= T_LEAD_WALK and t < T_LEAD_LOOK:
        st = wk["lead"].state(t)
        if t < T_LEAD_WALK + 0.3:
            st["pose"] = herd.blend(_lead_hand(T_LEAD_WALK)["pose"], st["pose"], ease(t, T_LEAD_WALK, T_LEAD_WALK + 0.3), "lead")
        st.update(turn=None, nose_to=None)
        return st
    if t >= T_LEAD_BACK:
        # she comes a few steps back along the meadow toward the sill: she wants to see the dog she touched noses with
        st = wk["lead2"].state(t)
        seen = ease(t, T_B4 + 0.1, T_B4 + 0.5) * (1 - ease(t, 24.3, 25.0))    # it comes up spent: she stops chewing; then chews again
        idle = herd.stand(t, "lead", chew=1.0 - seen, alert=0.35 + 0.3 * seen)
        if seen > 0:
            idle = herd.notice(idle, 0.6 * seen)
        w = ease(st["rest"], 0.5, 1.0)
        pose = dict(st["pose"])
        for k in ("neck", "head", "jaw", "ear", "eye"):
            if isinstance(pose.get(k), (int, float)):
                pose[k] = lerp(pose[k], idle[k], max(w, 0.6))
        st.update(pose=pose, turn=None, nose_to=None, facing=-1)
        return st
    if t >= T_LEAD_LOOK:
        st = wk["lead"].state(40.0)
        tu = ease(t, T_LEAD_LOOK + 0.2, T_LEAD_LOOK + 1.1)
        al = ease(t, T_LEAD_LOOK, T_LEAD_LOOK + 0.3)
        calf_ = ease(t, 18.9, 19.3) * (1 - ease(t, 20.6, 21.2))   # she watches the calf
        busy = max(1 - ease(t, T_LEAD_LOOK + 1.2, T_LEAD_LOOK + 1.8), calf_)
        p = herd.stand(t, "lead", chew=1.0 - al * busy, alert=al * (0.35 + 0.3 * calf_))
        if busy > 0:
            p = herd.notice(p, 0.6 * al * calf_)
        p["bell"] = 12.0 * math.sin(2 * math.pi * 2.0 * (t - T_LEAD_LOOK)) * math.exp(-1.4 * max(0.0, t - T_LEAD_LOOK - 0.3)) * al
        st.update(pose=p, turn=tu if tu < 1 else None, facing=1 if tu < 1 else -1, nose_to=None)
        return st
    return _lead_hand(t)


def _lead_hand(t):
    drink = herd.drink(t, 1.0, "lead")
    alert = herd.with_(herd.stand(t, "lead", chew=0, alert=0.8), eye=1.35)
    look = herd.with_(herd.look_down(t, 1.0, "lead"), ear=30.0)
    wide = herd.with_(herd.stand(t, "lead", chew=0, alert=1.0), eye=1.75, ear=-22.0, neck=-34.0, head=14.0)
    p = herd.tween(drink, alert, ramp(t, 0.18, 0.5), "out", "lead")
    p = herd.tween(p, look, ramp(t, 0.72, 1.12), "inout", "lead")
    tu = ease(t, 0.42, 1.02)
    x = lerp(X_LEAD0, X_LEAD_TURNED, tu)
    nose_to = (600.0, 401.0) if t < 0.6 else (XB1 + 14.0, 397.0)
    # the dog's head breaks the line under her chin: her head goes up, eyes wide, and she backs a step
    jerk = ramp(t, T_B1 - 0.02, T_B1 + 0.14)
    if jerk > 0:
        p = herd.tween(p, wide, jerk, "out", "lead")
        back = ease(t, T_B1 + 0.08, T_B1 + 0.62)
        x = lerp(X_LEAD_TURNED, X_LEAD_BACK, back)
        if 0 < back < 1:
            stp = herd.step_pose("lead", -(x - X_LEAD_TURNED) / herd.S * 1.0)
            q = dict(p)
            for leg in herd.LEGS:
                q[leg] = stp[leg]
            p = herd.blend(p, q, bump(back) ** 0.5, "lead")
        # she watches it climb out
        settle = ease(t, T_B1 + 0.5, T_L1 + 0.1)
        p = herd.tween(p, herd.with_(alert, neck=-10.0, head=10.0, ear=30.0), settle, "inout", "lead")
    # THE SHAKE reaches her: eyes shut, head pulled up and away, ears flat; she takes all of it
    sh = ease(t, T_SH1 + 0.18, T_SH1 + 0.3) * (1 - ease(t, T_SH1 + D_SH1 - 0.1, T_SH1 + D_SH1 + 0.25))
    if sh > 0:
        fl = herd.with_(herd.stand(t, "lead", chew=0, alert=0.6), eye=0.12, ear=-30.0, neck=-30.0 - 3.0 * math.sin(2 * math.pi * 6 * t),
                        head=20.0, jaw=0.0, dy=2.0)
        p = herd.tween(p, fl, sh, "out", "lead")
    # she opens her eyes, looks at the wet dog going, and chews again: it is all right
    if t > T_SH1 + D_SH1 + 0.1:
        ok = ease(t, T_SH1 + D_SH1 + 0.1, T_SH1 + D_SH1 + 0.6)
        blink = bump((t - (T_SH1 + D_SH1 + 0.42)) / 0.2)
        st = herd.stand(t, "lead", chew=ease(t, 3.25, 3.5))
        st = herd.with_(st, eye=st["eye"] * (1 - 0.9 * blink))
        p = herd.tween(p, st, ok, "inout", "lead")
    p = dict(p)
    p["bell"] = _bell_swing(t)
    # then she turns and walks off the strip to the meadow, unhurried
    tu2 = ease(t, 3.45, 4.25)
    if tu2 > 0:
        return dict(x=X_LEAD_BACK, y=STRIP_Y, pose=p, facing=-1, turn=tu2, nose_to=None, layer="strip", s=herd.S, squash=1.0)
    return dict(x=x, y=STRIP_Y, pose=p, facing=1, turn=tu if tu < 1 else None, nose_to=nose_to, layer="strip", s=herd.S, squash=1.0) if tu < 1 else \
        dict(x=x, y=STRIP_Y, pose=p, facing=-1, turn=None, nose_to=nose_to if t < T_B1 + 0.1 else None, layer="strip", s=herd.S, squash=1.0)


def _gate_layer(st):
    """Which pass a cow on herd.PATH is in. herd.py hands her to the strip pass as soon as she starts her turn in
    the gate, while she is still nearly full width, so she jumps in front of the gate posts (check() measured it:
    93 % wide at the switch). Here she stays in the hill pass, behind the posts, until she is edge-on in the
    middle of the turn (d = herd.D_GATE), and only then comes through."""
    if "d" in st and st.get("layer") in ("hill", "strip") and st["x"] < 352:
        st["layer"] = "hill" if st["d"] < herd.D_GATE else "strip"
    return st


def cow_state(who, t):
    wk = _walkers()
    if who == "lead":
        return lead_state(t)
    st = wk[who].state(t)
    st.update(turn=None, nose_to=None)
    _gate_layer(st)
    if who == "second" and 8.8 <= t <= 14.3:
        st["nose_to"] = (600.0, 401.0)
        # the dog bursts up through her drink (T_B2): inside three frames her head is up out of it, eyes wide, ears
        # back, water falling off her chin. She looks at the wet dog; then she puts her nose back down and goes on
        # drinking: her tempo is not the dog's. (The first cut had her head stay down through the splash.)
        k = ramp(t, T_B2 + 0.02, T_B2 + 0.13) * (1 - ease(t, T_B2 + 0.62, T_B2 + 1.12))
        if k > 0:
            up = herd.with_(herd.stand(t, "second", chew=0, alert=1.0), eye=1.75, ear=-24.0, neck=-26.0 - 6.0 * bump((t - T_B2) / 0.3), head=16.0,
                            jaw=3.0)
            look = herd.with_(herd.stand(t, "second", chew=0, alert=0.8), eye=1.4, ear=30.0, neck=-6.0, head=12.0)     # at the dog, on the board
            up = herd.tween(up, look, ramp(t, T_B2 + 0.3, T_B2 + 0.55), "inout", "second")
            pose = herd.tween(st["pose"], up, k, "out", "second")
            pose = dict(pose)
            pose["_nose"] = 1.0 - k
            st["pose"] = pose
    if who == "second" and t >= T_SEC_TURN:                      # in the meadow she turns round too, and chews
        tu = ease(t, T_SEC_TURN, T_SEC_TURN + 0.85)
        st = wk[who].state(40.0)
        st.update(pose=herd.stand(t, "second"), turn=tu if tu < 1 else None, facing=1 if tu < 1 else -1, nose_to=None)
    if who == "mother":
        if T_LICK - 0.05 <= t <= T_LICK + 0.95:
            c = calf_state(t)
            st["nose_to"] = (c["x"] + 26.0 + 8.0 * math.sin(math.pi * clamp((t - T_LICK) / 0.6)), c["y"] - 50.0)
        elif t >= T_M_DRINK:
            st["nose_to"] = (600.0, 401.0)
    return st


@lru_cache(maxsize=None)
def _calf_push_table():
    """The calf is moved by the dog's nose, not by a number: its chest stays ahead of the nose once touched."""
    out = {}
    x = X_CALF_SKID
    k0, k1 = int((T_NUDGE + 0.4) * FPS), int((T_WATCH - 0.1) * FPS)
    for k in range(k0, k1 + 1):
        nx = _dog_points(k)["nose"][0]
        x = min(x, nx - CALF_CHEST)
        out[k] = x
    return out


CALF_CHEST = 26.0        # px from the calf's ground point to the front of its chest
X_CALF_HOME = 440.0      # where it ends up, against its mother's forelegs
T_CALF_BACK = 20.18


def calf_state(t):
    """The calf -> dict(x, y, pose, facing, layer, s, squash, nose_to, on_sill)."""
    wk = _walkers()
    base = dict(turn=None, nose_to=None, on_sill=False)
    if t < 15.35:
        st = _gate_layer(wk["calfA"].state(t))
        st.update(base)
        return st
    if t < 17.5:
        st = _gate_layer(wk["calfB"].state(t))                       # it trots down after her: a calf can
        st.update(base)
        return st
    if t < T_CALF_GO:
        # it has stopped walking, badly, and it is watching the dog
        st = wk["calfB"].state(40.0)
        p = herd.calf_skid(clamp((t - 17.5) / 0.5))
        look = herd.notice(herd.stand(t, "calf", chew=0, alert=1.0), 1.0)
        p = herd.blend(p, look, ease(t, 17.82, 18.0), "calf")
        st.update(base)
        st.update(pose=p, nose_to=None)
        return st
    if t < T_CALF_SKID:
        st = wk["calfC"].state(t)                                    # out along the boards after the dog
        st.update(base)
        st.update(on_sill=st["y"] > STRIP_Y + 2.5, layer="strip")
        return st
    out = dict(base, facing=1, s=herd.S, squash=1.0, layer="strip", slope=0.0, rest=1.0)
    if t < T_CALF_BACK:
        k = int(round(t * FPS))
        tab = _calf_push_table()
        x = tab.get(k, X_CALF_SKID if k < min(tab) else tab[max(tab)])
        x = min(x, X_CALF_SKID)
        tau = t - (T_NUDGE + 0.05)
        sk = herd.calf_skid(clamp((t - T_CALF_SKID) / 0.5))
        sniff = herd.with_(herd.stand(t, "calf", chew=0, alert=0.2), neck=38.0, head=6.0, ear=30.0, eye=1.3,
                           nf=sk["nf"], ff=sk["ff"])                 # forefeet in the water, nose down to follow it under
        p = herd.blend(sk, sniff, ease(t, T_CALF_SKID + 0.1, T_CALF_SKID + 0.4), "calf")
        if tau > -0.08:                                              # the dog has turned on it: its head goes up
            p = herd.blend(p, herd.calf_nosed(max(tau, 0.0)), ease(tau, -0.08, 0.22), "calf")
        if tau > 1.0:                                                # the second push: the scramble again
            q = herd.calf_nosed(tau - 0.5)
            p = herd.blend(p, q, bump((tau - 0.95) / 0.5), "calf")
        out.update(x=x, y=SILL_Y, pose=p, on_sill=True)
        return out
    tab = _calf_push_table()
    x_p = tab[max(tab)]
    if t < T_M_ON:
        # it backs up the board by itself, into its mother's legs; her tongue goes once over its head
        b = ease(t, T_CALF_BACK, T_CALF_BACK + 0.6)
        x = lerp(x_p, X_CALF_HOME, b)
        y = lerp(SILL_Y, STRIP_Y, ease(t, T_CALF_BACK + 0.15, T_CALF_BACK + 0.55))
        giving = herd.with_(herd.stand(t, "calf", chew=0), neck=-2.0, head=10.0, ear=-18.0, eye=0.85, tail=(2.0, 3.0, 4.0))
        p = giving
        if b < 1:
            stp = herd.step_pose("calf", -(x - x_p) / herd.S * 1.6)
            q = dict(giving)
            for leg in herd.LEGS:
                q[leg] = stp[leg]
            p = herd.blend(giving, q, bump(b) ** 0.4, "calf")
        lick = bump((t - T_LICK) / 0.7)
        if lick > 0:
            p = herd.blend(p, herd.with_(giving, eye=0.1, ear=-34.0, neck=10.0, head=16.0, dy=3.0), lick, "calf")
        after = ease(t, T_LICK + 0.6, T_LICK + 0.9)
        if after > 0:
            p = herd.blend(p, herd.stand(t, "calf", chew=0, alert=0.5), after, "calf")
        out.update(x=x, y=y, pose=p, on_sill=y > STRIP_Y + 2.5)
        return out
    # its mother walks on to the water. It gives her room, a few steps back along the board's edge, and from there,
    # at her flank, it looks at the dog (where S4 finds it)
    go = ease(t, T_M_ON + 0.15, T_M_ON + 1.35)
    x = lerp(X_CALF_HOME, X_CALF_END, go)
    y = lerp(STRIP_Y, Y_CALF_END, go)
    p = herd.step_pose("calf", (x - X_CALF_HOME) / herd.S * 1.5, rest=1.0 - bump(go) ** 0.5, t=t)
    see = ease(t, T_B4 - 0.1, T_B4 + 0.2) * (1 - ease(t, 24.6, 25.3))       # the dog bursts up beside it: ears, eye
    look = herd.stand(t, "calf", chew=1.0 - see, alert=0.4 + 0.5 * see)
    if see > 0:
        look = herd.notice(look, see)
    p = herd.blend(p, look, ease(t, T_M_ON + 1.2, T_M_ON + 1.6), "calf")
    out.update(x=x, y=y, pose=p)
    return out


def _draw_cow(ink, who, st, oy, only=None, shadow=0.45):
    """`oy` is the crane's offset (a number), or a View: through a close view she is drawn again at its size."""
    kw = {}
    if st.get("turn") is not None:
        kw["turn"] = st["turn"]
    else:
        kw["squash"] = st.get("squash", 1.0)
    rel = st.get("rel", 1.0)
    far = clamp((0.62 - rel) / 0.5) * 0.5
    if who == "calf" and rel > 0.95:
        kw["rim"] = 1.0                                   # the lamp finds the calf: it has to read against its mother
    if isinstance(oy, View):
        V = oy
        if not V.hi:
            oy = int(V.y0)
        else:
            nt = st.get("nose_to")
            kw.setdefault("rim", herd.rim_at(st["x"]))
            return herd.cow(ink, who, st["pose"], V.X(st["x"]), V.Y(st["y"]), st["s"] * V.z, st["facing"], 0,
                            nose_to=(V.X(nt[0]), V.Y(nt[1])) if nt else None, far=far, only=only, shadow=shadow, **kw)
    return herd.cow(ink, who, st["pose"], st["x"], st["y"], st["s"], st["facing"], oy,
                    nose_to=st.get("nose_to"), far=far, only=only, shadow=shadow, **kw)


# ====================================================================== #
#  5 · THE PERSON, THE PEBBLES, THE PAGE IN THE HAND                      #
# ====================================================================== #

MOTIF = (0.0, 0.28, 0.56, 1.08)                  # short short long short: "Will you fetch it?"
TAPS_1 = tuple(7.30 + m for m in MOTIF)          # asked again [65.2-66.2]
TAP_2 = (14.20,)                                 # once, and a point at the water [72.2]
TAP_3 = (18.22,)                                 # [76.3]
TAPS_4 = tuple(19.42 + m for m in MOTIF)         # the same four words, while the dog is busy with the calf [77.4-78.3]
ALL_TAPS = TAPS_1 + TAP_2 + TAP_3 + TAPS_4
RAIL_HAND = (213.0, 296.0)                       # the end of the rail, by the seated person's shoulder
# pebbles: (k, colour, time the hand lets it go, time it stops in its place)
PEBBLES = [(1, "w", 8.62, 9.02), (2, "g", 14.36, 14.74), (3, "g", 18.36, 18.72), (4, "w", 20.66, 21.04)]
T_TAKE, T_UPAT, T_DOWNFROM, T_BACKAT = 5.45, 5.90, 6.74, 7.06       # the page: taken, at the lamp, lowered, laid back
T_CROUCH = 23.0
LINE2 = (23.2, 24.8)                             # "It's too much for one dog." [81.2-82.8]. THE HOLD: 24.8-26.0
PAGE_REACH = (306.0, 379.0)


def pebble_string(t):
    return "w" + "".join(c for k, c, t0, t1 in PEBBLES if t >= t1)


def _tap_p(t):
    """1 = the hand is down on the rail, 0 = lifted."""
    p = 0.0
    for tt in ALL_TAPS:
        long = tt in (TAPS_1[2], TAPS_4[2])
        dur = 0.34 if long else 0.2
        p = max(p, clamp(1 - abs(t - (tt + dur * 0.35)) / (dur * 0.65)))
    return smooth(p)


def _foot(t):
    """The foot taps to the radio, slowly. It stops when the dog comes up, and whenever the person is asking."""
    on = (1 - ease(t, 1.0, 1.4)) + ease(t, 9.6, 10.2) * (1 - ease(t, 13.9, 14.1)) + ease(t, 15.7, 16.2) * (1 - ease(t, 17.6, 17.9))
    return (0.5 - 0.5 * math.cos(2 * math.pi * t / 1.1)) * clamp(on)


def _hands_back(t):
    """While the dog is at the person's knees the person keeps their hands to themselves (S1 taught them that)."""
    return max(ease(t, 2.6, 3.1) * (1 - ease(t, 4.7, 5.0)), ease(t, 12.7, 13.0) * (1 - ease(t, 13.95, 14.15)),
               ease(t, 17.1, 17.35) * (1 - ease(t, 17.85, 18.05)), ease(t, 22.75, 23.0))


def _p_sit(t):
    q = porch.pose("sit", p=_foot(t), t=t)
    k = _hands_back(t)
    if k > 0:
        b = dict(q)
        b["lean"] = 6.0
        porch._arm_ik(b, (238.0, 344.0))
        q = porch.blend(q, b, k)
    return q


def _p_offer(t):
    return porch.pose("offer", p=1.0, t=t, at=PAGE_REACH)


def _p_up(t):
    return porch.pose("hold_up", p=1.0, t=t)


def _p_tap(t):
    q = porch.pose("sit", p=0.0, t=t)
    q["lean"] = 9.0
    flick = max(bump((t - t0 + 0.1) / 0.24) for _, _, t0, _ in PEBBLES)
    porch._arm_ik(q, (RAIL_HAND[0] - 9 * flick, RAIL_HAND[1] - 12 * (1 - _tap_p(t)) * (1 - flick) - 3 * flick))
    return q


def _p_point(t):
    q = porch.pose("sit", p=0.0, t=t)
    q.update(lean=24.0, head=8.0, turn=0.3)
    porch._arm_ik(q, (322.0, 322.0))
    return q


def _p_crouch(t):
    return porch.pose("crouch", t=t)


PERSON = [   # time the pose is reached, pose, seconds of eased move into it
    (0.0, _p_sit, 0.0), (4.85, _p_sit, 0.0), (T_TAKE, _p_offer, 0.6), (T_UPAT, _p_up, 0.5), (T_DOWNFROM, _p_up, 0.0),
    (T_BACKAT, _p_offer, 0.35), (7.3, _p_tap, 0.24), (8.95, _p_tap, 0.0), (9.45, _p_sit, 0.5),
    (14.05, _p_sit, 0.0), (14.2, _p_tap, 0.15), (14.42, _p_tap, 0.0), (14.72, _p_point, 0.28), (15.1, _p_point, 0.0), (15.6, _p_sit, 0.5),
    (18.06, _p_sit, 0.0), (18.22, _p_tap, 0.16), (18.5, _p_tap, 0.0), (18.9, _p_sit, 0.4),
    (19.26, _p_sit, 0.0), (19.42, _p_tap, 0.16), (20.86, _p_tap, 0.0), (21.3, _p_sit, 0.44),
    (T_CROUCH, _p_sit, 0.0), (T_CROUCH + 0.8, _p_crouch, 0.8),
]


def person_q(t):
    cur = None
    for time, fn, dur in PERSON:
        nxt = fn(t)
        cur = nxt if cur is None else porch.blend(cur, nxt, ease(t, time - dur, time) if dur > 0 else (1.0 if t >= time else 0.0))
    if LINE2[0] <= t <= LINE2[1] + 0.3:                                   # speaking, low: the head nods on the words
        cur = dict(cur)
        cur["head"] = cur["head"] + 2.5 * math.sin(2 * math.pi * 3.2 * (t - LINE2[0])) * (1 - ease(t, LINE2[1], LINE2[1] + 0.3))
    if t > T_CROUCH:                                                      # while speaking the head is up to the dog; after the
        cur = dict(cur)                                                   # last word the shoulders drop (into porch's own crouch,
        up = ease(t, T_CROUCH + 0.3, T_CROUCH + 0.8) * (1 - ease(t, LINE2[1] - 0.25, LINE2[1]))    # which is where S4 begins)
        cur["lean"] = cur["lean"] - 5.0 * up
        cur["head"] = cur["head"] - 6.0 * up
    return cur


def hand_over_rail(t):
    return (7.2 <= t < 9.2) or (14.1 <= t < 14.6) or (18.12 <= t < 18.7) or (19.32 <= t < 21.1)


@lru_cache(maxsize=4096)
def _hands(k):
    """World points of the person's hands at frame k."""
    t = k / FPS
    pts = porch.person(Image.new("RGB", (8, 8)), t, 0, person_q(t), shadow=False)
    return pts["hand_a"], pts["hand_b"]


def page_in_hand(t):
    """While the person has the page: (x, y, flat, angle) in world px; None while it lies on the sill."""
    if not (T_TAKE <= t < T_BACKAT):
        return None
    a, b = _hands(int(round(t * FPS)))
    up = ease(t, T_TAKE, T_UPAT) * (1 - ease(t, T_DOWNFROM, T_BACKAT))
    home = (THING_X[0], 392.0 - 6.0 * DS)
    x = lerp(a[0] + 6, (a[0] + b[0]) / 2 + 2, up)
    y = lerp(a[1] + 2, min(a[1], b[1]) + 9, up)
    edge = ease(t, T_TAKE, T_TAKE + 0.12) * (1 - ease(t, T_BACKAT - 0.12, T_BACKAT))
    x, y = lerp(home[0], x, edge), lerp(home[1], y, edge)
    return x, y, lerp(0.72, 0.12, up), lerp(-6.0, -14.0, up)


# ====================================================================== #
#  6 · THE THINGS ON THE SILL                                             #
# ====================================================================== #

LAID = [T_LAID1, T_LAID2, T_LAID3, T_LAID4, T_LAID4 + 0.03]       # page, reel, half reel, strip, flange
PAWED = [T_PRESS1, T_PRESS2, None, None, None]                    # when the paw print goes on (None: never)
EDGE_Y, FLOOR_Y = 404.0, 400.0


def pile_count(t):
    return sum(1 for b in LAID if t >= b)


def _pile_item(ink, t, oy, k):
    """One thing of the pile, drawn exactly as props.pile draws it (same calls, same numbers), so that the paw
    print can come when the paw does and the page can be lifted out. check() compares the two at the end.
    `oy` is the crane's offset, or a View (a close view draws the thing again, larger and as sharp)."""
    if isinstance(oy, View) and oy.hi:
        return _pile_item_hi(ink, t, oy, k)
    if isinstance(oy, View):
        oy = int(oy.y0)
    kind, arg, pw, dx, lift, ang = props.PILE[k]
    s = DS
    x, y = PILE_X, 392.0 - oy
    born = LAID[k]
    if k == 0 and t >= T_BACKAT:
        born = T_BACKAT                                              # laid back by the hand: it settles again
    age = t - born
    if age < 0:
        return
    set_ = 1 - clamp(age / 0.32)
    drop = -7 * s * set_ * set_
    wage = t - LAID[k]
    w = 1.0 if wage < 4 else max(0.45, 1 - (wage - 4) / 20)
    paw = PAWED[k] is not None and t >= PAWED[k]
    px = x + dx * s
    if kind == "page":
        py = y - 6.0 * s - lift * s + drop
        props.page(ink, px, py, s, drawing=arg, flat=0.72, angle=ang, wet=w * 0.6, paw=paw)
    elif kind in ("reel", "half"):
        py = y - 15.5 * s - lift * s + drop
        props.reel(ink, arg, px, py, s, tilt=0.62, angle=ang, wet=w, paw=paw, half=kind == "half", loop=0.8, lit=1.0)
    else:
        py = y - (5.0 if kind in ("strip", "crank") else 8.0) * s - lift * s + drop
        sh = props._part_sheet(kind, px, py, s * 0.9, ang, 0.6, w, 0.0, t)
        if kind in ("flange", "gear"):
            sh.squash(0.55)
        sh.lay(ink, 1.0)
    if wage < 4.2:
        props.drips(ink, t, px, EDGE_Y - oy, LAID[k] + 0.25, width=22 * s, floor=FLOOR_Y - oy, s=max(0.6, s), seed=k, heavy=0.8)


def _pile_item_hi(ink, t, V, k):
    """_pile_item through a close view: the same thing in the same place, drawn at the view's size."""
    kind, arg, pw, dx, lift, ang = props.PILE[k]
    s, z = DS, V.z
    born = LAID[k]
    if k == 0 and t >= T_BACKAT:
        born = T_BACKAT
    age = t - born
    if age < 0:
        return
    set_ = 1 - clamp(age / 0.32)
    drop = -7 * s * set_ * set_
    wage = t - LAID[k]
    w = 1.0 if wage < 4 else max(0.45, 1 - (wage - 4) / 20)
    paw = PAWED[k] is not None and t >= PAWED[k]
    px = V.X(PILE_X + dx * s)
    if kind == "page":
        py = V.Y(392.0 - 6.0 * s - lift * s + drop)
        props.page(ink, px, py, s * z, drawing=arg, flat=0.72, angle=ang, wet=w * 0.6, paw=paw)
    elif kind in ("reel", "half"):
        py = V.Y(392.0 - 15.5 * s - lift * s + drop)
        props.reel(ink, arg, px, py, s * z, tilt=0.62, angle=ang, wet=w, paw=paw, half=kind == "half", loop=0.8, lit=1.0)
    else:
        py = V.Y(392.0 - (5.0 if kind in ("strip", "crank") else 8.0) * s - lift * s + drop)
        sh = props._part_sheet(kind, px, py, s * 0.9 * z, ang, 0.6, w, 0.0, t)
        if kind in ("flange", "gear"):
            sh.squash(0.55)
        sh.lay(ink, 1.0)
    if wage < 4.2:
        props.drips(ink, t, px, V.Y(EDGE_Y), LAID[k] + 0.25, width=22 * s * z, floor=V.Y(FLOOR_Y), s=max(0.6, s) * z, seed=k, heavy=0.8)


def _pile_puddle(ink, t, oy):
    n = pile_count(t)
    if n <= 0:
        return
    last_x = max(props.PILE[k][3] for k in range(n)) * DS
    if isinstance(oy, View):
        V = oy
        props.puddle(ink, V.X(PILE_X + last_x / 2), V.Y(392.0 + 1.5), (last_x + 60 * DS) * V.z, level=0.45 + 0.55 * n / len(props.PILE), t=t)
        return
    props.puddle(ink, PILE_X + last_x / 2, 392.0 - oy + 1.5, last_x + 60 * DS, level=0.45 + 0.55 * n / len(props.PILE), t=t)


# ====================================================================== #
#  7 · TROUTTOWN, FROM ABOVE IT AND IN IT                                 #
# ====================================================================== #

BOOT_AT = (316.2, 842.0)                         # where S2 left the boot, the spool and the pin
SPOOL_AT = (394.0, 808.0)
PIN_AT = (389.0, 812.0, 74)
STRIP_LIES = (HOLE_D[0] - 46.0, HOLE_D[1] - 16.0)    # a strip of film lying on the gravel by hole 4, seen from round two on


def hole_levels(t):
    """{hole index: how far dug 0..1} for the holes this sequence digs (3, 4, 5, 6). They never fill in."""
    out = {}
    for k, a, b, _ in DIGS:
        f = clamp((t - a) / max(b - a, 1e-6))
        if f > 0:
            out[k] = max(out.get(k, 0.0), 0.25 + 0.75 * f)
    return out


def _hole(ink, cam, q, f):
    """One pit and its spoil heap: town.dig_holes' own drawing for hole q, dug to f (copied; see docstring)."""
    z = cam.zoom
    x, y, wd, side = town.HOLES[q]
    sx, sy = cam.xy(x, y)
    if not (-40 < sx < W + 40 and -20 < sy < H + 20):
        return
    a = wd / 2 * z * (0.45 + 0.55 * f)
    b = a * 0.40
    rs = random.Random(q * 7 + 1)
    hx = sx + side * a * 1.5
    hr, hh = a * 0.95 * f ** 0.6, b * 1.5 * f ** 0.6
    heap = [(hx - hr, sy + b * 0.5)] + [(hx + hr * math.cos(math.radians(ang)), sy + b * 0.5 - hh * math.sin(math.radians(ang)) * (0.85 + 0.3 * rs.random())) for ang in range(180, -1, -30)]
    ink.d.polygon([(px + 1.5 * z, py + 2 * z) for px, py in heap], fill=(6, 22, 24, 90))
    ink.d.polygon(heap, fill=(118, 138, 120, 255))
    ink.d.line(heap, fill=(20, 40, 40, 230), width=max(1, int(z)))
    for _ in range(4):
        px, py = hx + rs.uniform(-0.7, 0.7) * hr, sy + b * 0.4 - rs.uniform(0.1, 0.8) * hh
        r = rs.uniform(0.9, 1.9) * z
        ink.d.ellipse([px - r, py - r * 0.7, px + r, py + r * 0.7], fill=(166, 182, 160, 255), outline=(30, 50, 48, 255))
    ink.d.ellipse([sx - a * 1.2, sy - b * 1.3, sx + a * 1.2, sy + b * 1.25], fill=(132, 150, 130, 255), outline=(26, 46, 44, 255))
    ink.d.ellipse([sx - a, sy - b, sx + a, sy + b], fill=(6, 22, 26, 255))
    ink.d.chord([sx - a, sy - b, sx + a, sy + b], 10, 170, fill=(40, 70, 70, 255))
    ink.d.arc([sx - a, sy - b, sx + a, sy + b], 200, 340, fill=(2, 10, 12, 255), width=max(1, int(1.5 * z)))


def _silt(ink, x, y, age, power=1.0, seed=0):
    """A puff of silt off a dig: it rolls up, spreads, and thins."""
    if age < 0 or age > 2.2:
        return
    rs = random.Random(seed)
    lay = Image.new("RGBA", (220, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for q in range(9):
        a0 = rs.uniform(0, 0.5)
        a = age - a0
        if a < 0:
            continue
        r = (10 + 26 * (1 - math.exp(-a * 2.2))) * rs.uniform(0.6, 1.1) * power
        px = 110 + rs.uniform(-34, 34) * (0.4 + a * 0.7)
        py = 118 - (14 + 34 * rs.random()) * (1 - math.exp(-a * 1.6))
        al = int(74 * clamp(1 - a / 1.7) * clamp(a * 6))
        d.ellipse([px - r, py - r * 0.62, px + r, py + r * 0.62], fill=(150, 160, 136, al))
    lay = lay.filter(ImageFilter.GaussianBlur(5))
    ink.img.paste(lay, (int(x - 110), int(y - 118)), lay)


def _waver(t):
    """S2 left one child up under the cow's nose. Her nose has gone; it looks after it, and goes back to its desk."""
    sx, sy = town.SEATS[WAVER]
    u = ease(t, 0.5, 2.3)
    x = lerp(596.0, sx, u) + 14 * math.sin(math.pi * u)
    y = lerp(474.6, sy - 8, u) + 2.5 * math.sin((t + 30.0) * 2.4) * (1 - u)
    tilt = -34 * math.sin(math.pi * clamp(u * 1.02))
    arm = lerp(126.0, 30.0, ease(t, 0.0, 0.5))
    return x, y, tilt, arm, u >= 1.0


def _draw_town(alt, t, camB, look, stg_dog=None):
    """Everything under the line except the swimmer, onto `alt` (a full frame; the dry world holds it out later)."""
    town.back(alt, t, camB, sky=False, door=1.0)
    town.street(alt, t, camB, holes=3, smudges=1, taken=(0,))
    lv = hole_levels(t)
    for q in sorted(lv, key=lambda q: town.HOLES[q][1]):
        _hole(alt, camB, q, lv[q])
    shove = ease(t, T_DIG_A + 0.05, T_DIG_A + 0.42)                  # the first rake of round two shoves S2's old boot aside
    town.thing(alt, camB, "boot", BOOT_AT[0] - 34 * shove, BOOT_AT[1] + 3 * shove, 8 - 24 * shove)
    town.thing(alt, camB, "spool", *SPOOL_AT)
    town.thing(alt, camB, "pin", PIN_AT[0], PIN_AT[1], PIN_AT[2])
    if TUG_GONE <= t < GIVE_T:                                       # what the tug left: the torn film, and the side still in the gravel
        sx, sy = camB.xy(*STRIP_LIES)
        props.part(alt, sx, sy, DS, "strip", angle=-8, mud=0.8, wet=0, weed=0.5, t=t, **props.UNDER)
        sx, sy = camB.xy(HOLE_C[0] - 4.0, HOLE_C[1] - 7.0)
        props.part(alt, sx, sy, DS * 1.62, "flange", angle=20, mud=0.5, wet=0, weed=0.0, t=t, **props.UNDER)
    town.townsfolk(alt, t, camB, look=look)
    wx, wy, wt, wa, home = _waver(t)
    lean = 8.0 - 16.0 * (1 - ease(t, 1.8, 3.2))                      # S2 left them leaning back to look up
    for a, b in ((T_DIG_C - 0.3, T_B3 - 0.3), (T_DIG_D - 0.2, T_B4 - 0.2)):
        lean += 12.0 * ease(t, a, a + 0.25) * (1 - ease(t, b, b + 0.3))    # the front desks lean over to see the digging
    arm = {0: 124 + 30 * math.sin((t + 30.0) * 9) if t < 0.7 else lerp(124.0, 24.0, ease(t, 0.7, 1.1))}
    town.school_class(alt, t, camB, look=look, tilt=lean, skip=() if home else (WAVER,), arm=arm)
    if not home:
        town.child(alt, t, camB, WAVER, wx, wy, facing=1, tilt=wt, arm=wa, look=look, swim=0.8)
    alt.d = ImageDraw.Draw(alt.img, "RGBA")


# ====================================================================== #
#  8 · A FRAME                                                            #
# ====================================================================== #

_FELT = []


def _felt(ink, oy):
    """S4's felt dog 'was lying by the step all along' (board, 92.8), ear to the boards. It is S4's own cut-out
    (s4.felt_dog), at S4's own place, drawn dim, so that it really was there. If s4 cannot be imported it is
    left out and the cut to S4 shows it arriving."""
    if not _FELT:
        try:
            import s4 as _s4
            _FELT.append((_s4.felt_dog, _s4.SPOT["felt"]))
        except Exception:
            _FELT.append(None)
    if _FELT[0] is None:
        return
    fn, (fx, fy) = _FELT[0]
    fn(ink, fx, fy - oy, 1.0, 1, lift=0.0, ear=0.0, hop=0.0, dim=0.5)


def _rings(t):
    out = []
    for tb, xb in BREACHES:
        if t >= tb - 0.05:
            out.append(porch.ring(xb, tb, 1.2))
            out.append(porch.ring(xb - 8, tb + 0.3, 0.8))
    for td, xd in DIVES:
        if t >= td:
            out.append(porch.ring(xd + 4, td, 1.15))
            out.append(porch.ring(xd + 4, td + 0.32, 0.8))
    # drinking: slow rings from the muzzle on the line, one every 1.9 s, whoever is drinking
    for a, b in ((-3.0, 0.25), (9.3, 13.9), (T_M_DRINK + 0.8, 30.0)):
        k = 0
        while a + 1.9 * k < min(t, b):
            out.append(porch.ring(602, a + 1.9 * k, 0.45))
            k += 1
    if t >= T_WADE:
        out.append(porch.ring(X_END + 30, T_WADE + 0.1, 0.7))
    if t >= T_CALF_SKID:
        out.append(porch.ring(X_CALF_SKID + 22, T_CALF_SKID + 0.05, 0.45))
    for i in range(2):
        tc = T_NUDGE + 0.55 + 0.5 * i
        if t >= tc:
            out.append(porch.ring(572, tc, 0.5))
    return [r for r in out if r is not None]


def _split_paste(ink, layer, line_y, deep=0.0, above=True, below=True):
    """HOLDOUT waterline: a cel that stands in the line. What is above it as it is; what is below it comes back
    through water (teal, thinner). Returns (alpha above, alpha below) for check()."""
    ly = int(round(clamp(line_y, 0, H)))
    a_top = a_bot = None
    if ly > 0:
        top = layer.crop((0, 0, W, ly))
        a_top = top.getchannel("A")
        if above:
            ink.img.paste(top, (0, 0), top)
    if ly < H:
        bot = layer.crop((0, ly, W, H))
        teal = Image.new("RGBA", bot.size, TEAL + (255,))
        tinted = Image.blend(bot, teal, 0.34 + 0.16 * clamp(deep))
        a_bot = bot.getchannel("A").point(lambda v: int(v * 0.86))
        tinted.putalpha(a_bot)
        if below:
            ink.img.paste(tinted, (0, ly), tinted)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    return a_top, a_bot


def _dog_layer(st, cam, under_tint=0.0):
    """The dog alone on a clear sheet at its screen place under camera `cam`. -> (RGBA, joints)."""
    oy, sq = cam["oy"], cam["sq"]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    carry = carry_sprite(st["carry"], under_tint > 0) if st["carry"] else None
    if st["anchor"] == "body":
        sx, sy = st["x"], sq_y(st["y"], oy, sq)
    else:
        sx, sy = st["x"], st["y"] + st.get("depth", 0.0) - oy
    kw = dict(tint=TEAL, tint_amount=under_tint) if under_tint > 0 else {}
    j = dog.draw_dog(layer, st["pose"], sx, sy, scale=DS, facing=st["facing"], carry=carry, anchor=st["anchor"], shadow=False, **kw)
    return layer, j


@lru_cache(maxsize=None)
def carry_sprite_at(kind, s):
    """carry_sprite drawn at dog scale s (for a close view: drawn at that size, not enlarged)."""
    if kind == "page":
        return props.page_sprite("jaw", s=s, flat=0.42, wet=0.5)
    if kind == "reel":
        return props.reel_sprite(props.REEL_FIRST, s=s, tilt=0.8, wet=1)
    if kind == "half":
        return props.reel_sprite(props.REEL_HALF, s=s, tilt=0.8, half=True, loop=1.0, wet=1)
    if kind == "strip":
        return props.part_sprite("strip", s=s, weed=0.6)
    if kind == "both":
        a = props.part_sprite("strip", s=s, weed=0.4)
        b = props.part_sprite("flange", s=s, weed=0.0, angle=24)
        im = Image.new("RGBA", (a.width, a.height + int(16 * s)), (0, 0, 0, 0))
        im.paste(b, (int(-14 * s), int(12 * s)), b)
        im.paste(a, (int(6 * s), 0), a)
        return im
    raise ValueError(kind)


def _close(ink, t, stg, V, sharp_strip, cast, scene_kw, drip=None):
    """A CLOSER CAMERA on the board (not an enlargement of the wide frame). The set is the first builder's
    plates and cannot be drawn larger, so it is the out-of-focus part of the shot: the wide frame's set, enlarged.
    What the shot is about is in focus: every cel of the board pass (the dog, what it lays down, the calf, a cow's
    head over them) and, with sharp_strip, every cow on the strip, is drawn again through V at V.z times the
    size. The set keeps its depth order round them: the set is rendered twice, with the cast's pass filled black
    and then white, and the difference of the two is the matte of everything the set draws IN FRONT of that pass
    (the board over a cow's hooves, the rail, the lamp's light, the water over a wading dog's legs)."""
    def run(fill):
        caps = {}

        def strip_cb(ink_, t_, oy_):
            if sharp_strip:
                caps["back"] = ink_.img.copy()
                ink_.img.paste(fill, (0, 0, W, H))
                ink_.d = ImageDraw.Draw(ink_.img, "RGBA")
            else:
                stg.play("strip", ink_)

        def sill_cb(ink_, t_, oy_):
            caps["mid"] = ink_.img.copy()
            ink_.img.paste(fill, (0, 0, W, H))
            ink_.d = ImageDraw.Draw(ink_.img, "RGBA")
            if drip:                                                 # water running off it (the set's own drops, soft)
                porch.drips(ink_, t, 0, drip[0], SILL_Y - 34, drip[1], wet=1.0 if t > 22 else 0.8, width=38, floor=SILL_Y + 2, seed=3)

        c2 = dict(cast)
        c2["strip"], c2["sill"] = strip_cb, sill_cb
        k = kit.Ink(t, ink.i)
        k.paper()
        porch.scene(k, t, 0, cast=c2, **scene_kw)
        return caps, k.img

    (cb_, fb_), (cw_, fw_) = run((0, 0, 0)), run((255, 255, 255))
    box = V.box()

    def up(im):
        return np.asarray(im.convert("RGB").resize((W, H), Image.BICUBIC, box=box), np.float32)

    def matte(b, w):
        return np.clip(1.0 - (w - b).mean(axis=2, keepdims=True) / 255.0, 0.0, 1.0)

    def sharp(arr, slot):
        k = kit.Ink(t, ink.i)
        k.img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        k.d = ImageDraw.Draw(k.img, "RGBA")
        stg.play(slot, k, V=V)
        return np.asarray(k.img.convert("RGB"), np.float32)

    if sharp_strip:
        base = sharp(up(cb_["back"]), "strip")
        mb, mw = up(cb_["mid"]), up(cw_["mid"])
        base = mb + (1.0 - matte(mb, mw)) * base
    else:
        base = up(cb_["mid"])
    base = sharp(base, "sill")
    fb, fw = up(fb_), up(fw_)
    out = fb + (1.0 - matte(fb, fw)) * base
    ink.img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _score_draw(t, ink, record=False, close=None):
    """One full 960x540 frame of the SCORE (the continuous action, as the first builder staged it) at score time
    t (0..26). record=True returns the Stage with every cel's matte (for check()); the picture is the same either
    way. close=dict(z, x0, y0[, strip]) looks at the same moment through a closer camera (see _close): the
    world rectangle at (x0, y0), W/z wide; the board's cels (and the strip's, with strip=True) are drawn again at
    that size. draw() is the film: it cuts between the score, close views of it, and the two shots under water."""
    t = clamp(t, 0.0, SECONDS)
    cam = camera(t) if close is None else dict(oy=0.0, sq=0.0, zoom=1.0, cx=W / 2, cy=H / 2)
    oy, sq = cam["oy"], cam["sq"]
    oyi = int(round(oy))
    line_s = LINE - oyi                                   # the surface on screen
    stg = Stage(t, record)
    stg.V = View(1.0, 0.0, oyi)
    ds = dog_state(t)
    wk = _walkers()
    wet = dog_wet(t)
    dog_w = (ds["x"], ds["y"] - (0 if ds["anchor"] == "body" else 30))
    crossing = ds["anchor"] == "body" and (LINE - 62 < ds["y"] < LINE + 62)
    under_now = ds["anchor"] == "body" and ds["where"] in ("swim", "dig")
    cache = {}

    # ---------------------------------------------------------------- cows
    hill_cows, strip_cows = [], []
    for who in ("sixth", "fifth", "fourth", "second", "mother", "lead"):
        st = cow_state(who, t)
        (hill_cows if st["layer"] == "hill" else strip_cows).append((who, st))
    cs = calf_state(t)

    hill_all = hill_cows + ([("calf", cs)] if cs["layer"] == "hill" else [])
    hill_all.sort(key=lambda it: it[1].get("d", 0.0))                # up the path is further: drawn first
    for i, (who, st) in enumerate(hill_all):
        stg.add("queue.far" if i < len(hill_all) - 1 else "queue.near", "hill",
                lambda ink_, V, who=who, st=st: _draw_cow(ink_, who, st, oyi))

    # further along the bank first; in the meadow the second cow passes BEHIND the lead cow, and stays behind her
    strip_cows.sort(key=lambda it: (0 if (it[0] == "second" and it[1]["x"] > 640) else 1, -it[1]["x"]))
    for who, st in strip_cows:
        def body(ink_, V, who=who, st=st):
            a = _draw_cow(ink_, who, st, V)
            cache[who] = a
        stg.add("cow.%s.body" % who, "strip", body)
    lead_st = cow_state("lead", t)
    lead_head = t < T_B1 + 0.1 and lead_st.get("nose_to") is not None and t > 0.7
    if lead_head:                                                    # SUBLAYER: her head, over the board
        stg.add("cow.lead.head", "sill", lambda ink_, V: _draw_cow(ink_, "lead", lead_st, V, only="head"))
    if cs["layer"] != "hill":
        def calf_cel(ink_, V):
            cache["calf"] = _draw_cow(ink_, "calf", cs, V, shadow=0.5)
        stg.add("calf", "sill" if cs["on_sill"] else "strip", calf_cel)
    m_st = cow_state("mother", t)
    if T_LICK - 0.05 <= t <= T_LICK + 0.9 and m_st["layer"] == "strip":
        def mhead(ink_, V):                                          # SUBLAYER: her head, over her calf
            a = _draw_cow(ink_, "mother", m_st, V, only="head")
            lk = bump((t - T_LICK - 0.08) / 0.5)
            if lk > 0:                                               # the tongue, once, over the top of its head
                mx, my = a["mouth"]
                z = V.z
                tx = mx - 4 * z + 14 * z * clamp((t - T_LICK - 0.08) / 0.5)
                ink_.d.line([(mx, my), (tx, my + 6 * z), (tx + 5 * z, my + 12 * z)], fill=(226, 138, 142, 255), width=int(round(5 * z)))
                ink_.d.line([(mx, my), (tx, my + 6 * z), (tx + 5 * z, my + 12 * z)], fill=(246, 178, 176, 255), width=int(round(2 * z)))
        stg.add("cow.mother.head", "sill" if cs["on_sill"] else "strip", mhead)

    # ---------------------------------------------------------------- the board: shadows, pile, page, dog
    def shadows(ink_, V):
        _pile_puddle(ink_, t, V)
        if ds["where"] in ("sill", "wade") and ds.get("depth", 0) < 8:
            contact_shadow(ink_, V.X(ds["x"]), V.Y(SILL_Y + 1.5), 44 * V.z, 0.75)
        elif ds["where"] == "air" and ds["facing"] < 0:              # the shadow is on the board before the dog is
            tb = max(tb_ for tb_, _ in BREACHES if tb_ <= t)
            land = {T_B1: (X_SHAKE, T_L1), T_B2: (X_LAY2, T_L2), T_B3: (X_LAY3, T_L3), T_B4: (X_LAY4, T_L4)}[tb]
            k = ease(t, tb + 0.1, land[1])
            contact_shadow(ink_, V.X(land[0]), V.Y(SILL_Y + 1.5), (20 + 24 * k) * V.z, 0.75 * k)
    stg.add("shadow.sill", "sill", shadows)
    stg.add("felt", FELT_PASS, lambda ink_, V: _felt(ink_, oyi))

    ph = page_in_hand(t)
    for k in range(5):
        if t >= LAID[k] and not (k == 0 and ph is not None):
            stg.add("pile.%d" % k, "sill", lambda ink_, V, k=k: _pile_item(ink_, t, V, k))
    if ph is not None:
        stg.add("page.hand", "sill", lambda ink_, V: props.page(ink_, V.X(ph[0]), V.Y(ph[1]), DS * V.z, "jaw", flat=ph[2], angle=ph[3], wet=0.5, paw=True))

    def dog_extras(ink_, j, V=None):
        V = V or stg.V
        if ds["bits"] and ds["bits"][0]:
            dog.draw_bits(ink_, ds["bits"][0], V.X(ds["bits"][1]), V.Y(ds["bits"][2]), DS * V.z, facing=ds["facing"])
        if 0.0 < wet < 4.0 and ds["where"] in ("sill", "wade") and not V.hi:
            porch.drips(ink_, t, oyi, ds["x"], SILL_Y - 34, wet, wet=1.0 if t > 22 else 0.8, width=38, floor=SILL_Y + 2, seed=3)

    if close is not None:
        def dog_close(ink_, V):                                      # the whole dog, once, at the close view's size
            s = DS * V.z
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dy = 0.0 if ds["anchor"] == "body" else ds.get("depth", 0.0)
            j = dog.draw_dog(layer, ds["pose"], V.X(ds["x"]), V.Y(ds["y"] + dy), scale=s, facing=ds["facing"], carry=None,
                             anchor=ds["anchor"], shadow=False)
            if ds["carry"] and ds["pose"].get("hold", 1.0) >= 0.5:
                item = carry_sprite_at(ds["carry"], round(s, 3))
                mx, my = j["mouth"]
                dog._composite(layer, item, int(mx - item.width / 2), int(my - 2 * s))
            if ds["where"] in ("wade", "air"):                       # HOLDOUT waterline, as in the wide shot
                _split_paste(ink_, layer, V.Y(LINE), deep=0.3)
            else:
                ink_.img.paste(layer, (0, 0), layer)
                ink_.d = ImageDraw.Draw(ink_.img, "RGBA")
            cache["dogj"] = j
            dog_extras(ink_, j, V)
        stg.add("dog", "sill", dog_close)
    elif ds["anchor"] == "ground":
        if ds["where"] == "wade" and ds.get("depth", 0) > 0.5:
            def wade_below(ink_, V):                                 # HOLDOUT waterline, standing in the creek
                layer, j = _dog_layer(ds, cam)
                cache["split"] = _split_paste(ink_, layer, line_s, deep=0.3, above=False)
                cache["dogj"] = j

            def wade_above(ink_, V):
                layer, j = _dog_layer(ds, cam)
                _split_paste(ink_, layer, line_s, below=False)
                dog_extras(ink_, j)
            stg.add("dog.below", "under", wade_below)
            stg.add("dog.above", "front", wade_above)
        else:
            def onboard(ink_, V):
                carry = carry_sprite(ds["carry"]) if ds["carry"] else None
                j = dog.draw_dog(ink_, ds["pose"], ds["x"], ds["y"] - oyi, scale=DS, facing=ds["facing"], carry=carry, shadow=False)
                cache["dogj"] = j
                dog_extras(ink_, j)
            stg.add("dog", "sill", onboard)
    elif ds["where"] == "air" or crossing:
        if ds["y"] < LINE - 62 or (ds["where"] == "air" and ds["y"] < LINE - 34 and ds["facing"] < 0):
            def inair(ink_, V):
                layer, j = _dog_layer(ds, cam)
                ink_.img.paste(layer, (0, 0), layer)
                cache["dogj"] = j
            stg.add("dog", "front", inair)
        else:
            def below(ink_, V):
                layer, j = _dog_layer(ds, cam)
                cache["split"] = _split_paste(ink_, layer, sq_y(LINE, oy, sq), deep=clamp((ds["y"] - LINE) / 60), above=False)
                cache["dogj"] = j
            def above(ink_, V):
                layer, j = _dog_layer(ds, cam)
                _split_paste(ink_, layer, sq_y(LINE, oy, sq), below=False)
            stg.add("dog.below", "under", below)
            stg.add("dog.above", "front", above)
    else:
        def swimmer(ink_, V):
            if ds["silt"]:
                hx, hy = ds["silt"][0]
                _silt(ink_, hx, sq_y(hy, oy, sq) + 4, ds["silt"][1] - 0.2, 1.0, seed=int(hx))
            if ds["bits"] and ds["bits"][0]:
                dog.draw_bits(ink_, ds["bits"][0], ds["bits"][1], sq_y(ds["bits"][2], oy, sq), DS, facing=-1, color=(150, 160, 136))
            layer, j = _dog_layer(ds, cam, under_tint=0.17)       # it is small down there: it stays the one cream thing
            ink_.img.paste(layer, (0, 0), layer)
            cache["dogj"] = j
        stg.add("swim.dog", "under", swimmer)

    # ---------------------------------------------------------------- under the line
    oyB = oy + sq
    camB = town.Cam(oy=oyB)
    town_seen = oyB > 34
    if town_seen:
        look = dog_w if (under_now or crossing or t < 2.0) else ((600, 400) if 8.8 < t < 14 else (480, 400))
        stg.add("town", "under", lambda ink_, V: _draw_town(ink_, t, camB, look))
        stg.add("weed", "under", lambda ink_, V: town.front(ink_, t, camB))

    def bubbles(ink_, V):
        def src(te):
            s2 = dog_state(te)
            if s2["anchor"] != "body" or s2["where"] not in ("swim", "dig"):
                return (s2["x"], LINE - 5)
            f = 1 if s2["facing"] > 0 else -1
            return (s2["x"] + f * 40, sq_y(s2["y"], oy, sq) + oyi - 8)
        for a, b, rate in ((0.2, T_B1, 5.0), (T_D2, T_B2, 6.0), (T_D3, T_B3, 9.0), (T_D4, T_B4, 11.0)):
            if a - 0.1 <= t <= b + 2.2:
                porch.bubbles(ink_, t, oyi, src, a + 0.1, b - 0.05, rate=rate, seed=int(a * 10) + 3, size=0.9)
        for td, xd in DIVES:
            if td <= t <= td + 2.4:
                porch.bubbles(ink_, t, oyi, (xd + 2, 446), td + 0.03, td + 0.7, rate=18.0, seed=int(td * 7), size=1.1)
    stg.add("bubbles", "under", bubbles)

    # ---------------------------------------------------------------- thrown water
    def splash(ink_, V):
        for tb, xb in BREACHES:
            if tb - 0.02 <= t <= tb + 1.2:
                porch.splash(ink_, t, oyi, xb, t - tb, {T_B1: 1.15, T_B2: 1.0, T_B3: 0.8, T_B4: 0.65}[tb], "out", seed=int(tb * 10))
        for td, xd in DIVES:
            if td <= t <= td + 1.2:
                porch.splash(ink_, t, oyi, xd + 4, t - td, 1.1, "in", seed=int(td * 10))
        if ds.get("shake"):
            t0, dur = ds["shake"]
            if t > t0 + 0.2:
                porch.spray(ink_, t, oyi, ds["x"] + 6, SILL_Y - 40, t - t0 - 0.2, power=1.5 if dur > 0.6 else 0.9, dur=max(0.5, dur), seed=int(t0 * 10))
        if T_SH1 + D_SH1 <= t < T_SH1 + D_SH1 + 0.9:                # the last of the spray still in the air
            porch.spray(ink_, t, oyi, X_SHAKE + 6, SILL_Y - 40, t - T_SH1 - 0.2, power=1.5, dur=D_SH1, seed=int(T_SH1 * 10))
        if T_CALF_SKID <= t <= T_CALF_SKID + 0.9:
            porch.splash(ink_, t, oyi, X_CALF_SKID + 26, t - T_CALF_SKID, 0.4, "in", seed=5)
    stg.add("splash", "front", splash)

    # ---------------------------------------------------------------- the set, with the passes in between
    def cb(slot):
        def f(ink_, t_, oy_):
            if slot == "under":
                # the pebble on its way along the rail (it is above water: drawn here because the rail is drawn by now)
                for k, c, t0, t1 in PEBBLES:
                    if t0 <= t < t1:
                        u = 1 - (1 - (t - t0) / (t1 - t0)) ** 2.2
                        tx, ty = porch.pebble_spot(k)
                        x, y = lerp(RAIL_HAND[0] - 6, tx, u), ty - oyi
                        col = (236, 228, 214) if c == "w" else (128, 118, 138)
                        ink_.d.ellipse([x - 3 + 1, y - 2.2 + 1.5, x + 4.6, y + 4.0], fill=(20, 12, 34, 110))
                        ink_.d.ellipse([x - 3.6, y - 2.6, x + 3.6, y + 2.6], fill=col + (255,))
                        ink_.d.ellipse([x - 1.8, y - 2.0, x + 0.7, y - 0.3], fill=(255, 250, 240, 120))
                for tt in ALL_TAPS:                                  # the tap itself: the rail answers, three short strokes
                    a = t - tt
                    if 0.0 <= a < 0.14:
                        hx, hy = RAIL_HAND[0] - 2, RAIL_HAND[1] - oyi - 2
                        k = a / 0.14
                        for ang in (-150, -110, -70, -30):
                            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                            r0, r1 = 9 + 8 * k, 14 + 12 * k
                            ink_.d.line([(hx + ca * r0, hy + sa * r0), (hx + ca * r1, hy + sa * r1)], fill=(250, 236, 200, int(230 * (1 - k))), width=2)
                ls = int(round(sq_y(LINE, oy, sq)))
                if ls < H:
                    alt = kit.Ink(t, ink_.i)
                    alt.img = ink_.img.copy()
                    alt.d = ImageDraw.Draw(alt.img, "RGBA")
                    stg.play("under", alt, clip=ls)
                    lo = max(0, ls)
                    ink_.img.paste(alt.img.crop((0, lo, W, H)), (0, lo))        # HOLDOUT dry_world
                    ink_.d = ImageDraw.Draw(ink_.img, "RGBA")
            else:
                stg.play(slot, ink_)
        return f

    def porch_pass(ink_, t_, oy_):
        # Nothing is thrown on the door. (The first cut had the lamp throw the page's drawing there; a stranger read
        # the pale panel of pencil strokes as a counter laid over the picture. The door stays a door; the page is
        # seen large where it is laid, and lit in the hand that lifts it.)
        stg.play("porch", ink_)

    cast = {s: cb(s) for s in ("hill", "strip", "sill", "under", "front")}
    cast["porch"] = porch_pass
    scene_kw = dict(dusk=dusk_at(t), door=door_at(t), q=person_q(t), hand_over_rail=hand_over_rail(t),
                    radio_at="step", radio_on=1.0, pebbles=pebble_string(t), rings=_rings(t),
                    puddles=[pd for pd in puddles_at(t) if pd[1] > 0.02])
    if close is not None:
        _close(ink, t, stg, View(close["z"], close["x0"], close["y0"]), close.get("strip", False), cast, scene_kw,
               drip=(ds["x"], wet) if (0.0 < wet < 4.0 and ds["where"] in ("sill", "wade")) else None)
        return stg
    porch.scene(ink, t, oyi, cast=cast, **scene_kw)

    # S2 ended looking at the dry world from below (town.back's sky). For the first half second that is still
    # how the strip above the line looks; then it is the bank itself, coming down into frame.
    if t < 0.5 and line_s > 2:
        alt = kit.Ink(t, ink.i)
        alt.img = ink.img.copy()
        alt.d = ImageDraw.Draw(alt.img, "RGBA")
        town.back(alt, t, town.Cam(oy=oy), sky=True)
        dip = 1 - ease(t, 0.16, 0.36)
        if dip > 0.02:
            town.touch(alt, t, town.Cam(oy=oy), 600, "muzzle", dip=dip)
        ly = int(line_s) + 26
        a = alt.img.convert("RGB").crop((0, 0, W, ly))
        b = ink.img.convert("RGB").crop((0, 0, W, ly))
        m = Image.new("L", (W, ly), int(255 * (1 - ease(t, 0.0, 0.5))))
        md = ImageDraw.Draw(m)
        for r in range(20):                                           # no seam: it thins out over the last rows
            md.line([(0, ly - 1 - r), (W, ly - 1 - r)], fill=int(255 * (1 - ease(t, 0.0, 0.5)) * r / 20))
        ink.img.paste(Image.composite(a, b, m), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
        if dip > 0.02:                                               # her muzzle on the line, seen from below
            alt2 = kit.Ink(t, ink.i)
            alt2.img = ink.img.copy()
            alt2.d = ImageDraw.Draw(alt2.img, "RGBA")
            town.touch(alt2, t, town.Cam(oy=oy), 600, "muzzle", dip=dip)
            ink.img.paste(alt2.img.crop((540, int(line_s) - 8, 660, int(line_s) + 40)), (540, int(line_s) - 8))
            ink.d = ImageDraw.Draw(ink.img, "RGBA")
    _push(ink, cam)
    ink.vignette(round(0.22 * clamp((oy + sq) / 250.0), 3))
    if record:
        m = Image.new("L", (W, H), 0)                                # the board itself, as a matte (the set draws it)
        ImageDraw.Draw(m).rectangle([300, 386 - oyi, 560, 407 - oyi], fill=255)
        stg.mattes["board"] = m
        stg.order.append(("board", "board"))
        stg.cache = cache
        return stg


# ====================================================================== #
#  8b · UNDER, CLOSE: the two shots the score did not have                #
# ====================================================================== #
# The first cut's three dives were one beat three times: nothing was in the dog's way and what it brought up
# was a 20 px blob. Round three is now a shot of its own, down at the gravel: the reel is STUCK. The dog pulls
# and its teeth slip; it looks; it braces and heaves, and the reel comes apart in its mouth: one side stays in
# the gravel and the film tears. That is why it comes up with half a reel. Round four answers it in the same
# framing: no blind dig this time; the fish child who watched (the waver, who waved at the cow in S2) has pulled
# the stuck side out and holds it up, and the dog frees the torn film with one rake and takes the piece from the
# child's fin. That is why it comes up with a strip and a flange. Both shots are town.py's own town through a
# zoomed town.Cam (drawn at that size, not enlarged) with the dog and the things drawn at the same zoom.

U_ZOOM = 2.8
U_LOOK = (594.0, 803.0)                           # the world point both shots are centred on
TUG_LEN, GIVE_LEN = 50 / FPS, 29 / FPS
TUG_T = 15.6                                      # the score second the tug begins at (for the town's own clocks); GIVE_T is above
TUG_XA = HOLE_C[0] + 69.0                         # where the dog stands to pull (its mouth reaches the reel's rim)
REEL_R = 14.5                                     # the reel's radius in world px (a 48 px lid at dog scale)
REEL_AT = (HOLE_C[0] - 4.0, HOLE_C[1] - 7.0)      # the middle of the reel as it sits in the gravel, a third of it in
FLANGE_S = 1.62                                   # props' flange is 30 px; a side of THIS reel is as big as its lid
U_PULL, U_SLIP, U_THINK, U_GRIP2, U_SNAP, U_TEAR = 0.46, 0.94, 1.12, 1.44, 1.74, 1.92
GIVE_KID = (580.0, 849.0)                         # where the waver stands with the flange
V_LAND, V_FREE, V_TAKE, V_OFF = 0.30, 0.60, 0.88, 0.98
UT = dict(tint=TEAL, tint_amount=0.17)
UT_THING = dict(tint=TEAL, tint_amount=0.2)


def _ucam():
    return town.Cam.look(U_LOOK[0], U_LOOK[1], U_ZOOM)


@lru_cache(maxsize=None)
def _mouth_of(key):
    """Where the mouth is, in world px from the ground point, for a named ground pose (facing left)."""
    j = dog.draw_dog(Image.new("RGB", (8, 8)), _TUG_POSES[key](), 0, 0, scale=DS, facing=-1, shadow=False)
    return j["mouth"]


def _p_grip():
    return _w(dog.dig(0.2), neck=0.05, head=-0.62, jaw=0.34, ear=0.95, ear_f=1.0, tail=0.7, curl=0.5, hold=1.0)


def _p_pull(k=1.0):
    """Hauling on it: forefeet braced, the whole dog leaning back off its teeth. k 0..1 is how hard."""
    g = _p_grip()
    return _w(g, cx=g["cx"] - 20 * k, cy=g["cy"] - 5 * k, pitch=g["pitch"] + 0.2 * k, arch=0.1 * k, neck=0.05 + 0.12 * k, head=-0.62 + 0.2 * k,
              fnx=g["fnx"] + 9 * k, ffx=g["ffx"] + 12 * k, hnx=g["hnx"] - 5 * k, hfx=g["hfx"] - 3 * k,
              ear=lerp(0.95, 0.12, k), ear_f=lerp(1.0, 0.1, k), tail=lerp(0.7, -0.15, k), eye=1.0 + 0.25 * k, jaw=0.3)


def _p_slipped():
    """Its teeth have come off: it sits down hard on nothing, head thrown up, ears flying."""
    q = dog.sit(1.0)
    return _w(q, cx=q["cx"] - 16, neck=1.05, head=0.32, ear=1.25, ear_f=1.3, eye=1.4, jaw=0.25, tail=0.9, curl=0.2, pitch=q["pitch"] + 0.12)


def _p_think():
    """Sat back, looking down at the thing that would not come. One ear cocked."""
    q = dog.sit(1.4)
    return _w(q, cx=q["cx"] - 8, neck=0.34, head=-0.5, ear=1.12, ear_f=0.28, eye=1.05, jaw=0.0, tail=0.25, curl=0.5)


def _p_grip2():
    """The second way: chest right down, both forefeet planted wide against the pit's edge, a mouthful of it."""
    g = _p_grip()
    return _w(g, cy=g["cy"] - 7, pitch=g["pitch"] - 0.1, neck=-0.02, head=-0.6, jaw=0.5, fnx=g["fnx"] + 16, ffx=g["ffx"] + 4,
              ear=0.3, ear_f=0.34, tail=1.0, eye=1.15)


_TUG_POSES = {"grip": _p_grip, "pull": _p_pull, "grip2": _p_grip2}


def _tug_dog(u):
    """The dog in the tug -> dict(pose, x, y, facing, anchor, grip 0..1 (teeth on the rim), strain, has (it has the half))."""
    gy = GY_C
    out = dict(x=TUG_XA, y=gy, facing=-1, anchor="ground", grip=0.0, strain=0.0, has=False)
    if u < U_PULL:
        # it is already raking at it as we cut in; then its nose goes to the rim
        d = dog.dig(u + 0.5, rate=3.4)
        w = ease(u, U_PULL - 0.14, U_PULL)
        out.update(pose=dog.blend(d, _p_grip(), w), grip=w, bits=u < U_PULL - 0.1)
        return out
    if u < U_SLIP:
        k = ease(u, U_PULL, U_PULL + 0.2)                        # it leans back off its teeth... and it does not come
        tremble = math.sin(2 * math.pi * 11 * u) * ease(u, U_PULL + 0.15, U_PULL + 0.3)
        p = _p_pull(k * (1.0 + 0.05 * tremble))
        out.update(pose=p, grip=1.0, strain=k)
        return out
    if u < U_THINK:
        w = ease(u, U_SLIP, U_SLIP + 0.09)                       # the teeth slip: three frames
        back = dog.ease_back(clamp((u - U_SLIP) / 0.16))
        p = dog.blend(_p_pull(1.0), _p_slipped(), clamp(back))
        out.update(pose=p, grip=1.0 - w)
        return out
    if u < U_GRIP2:
        w = ease(u, U_THINK, U_THINK + 0.14)                     # it looks at the thing. THE HOLD: it is thinking
        p = dog.blend(_p_slipped(), _p_think(), w)
        p = dog._breathe(p, u) if hasattr(dog, "_breathe") else p
        out.update(pose=p)
        return out
    if u < U_SNAP - 0.14:
        w = dog.ease_back(clamp((u - U_GRIP2) / 0.14))           # down again, lower, both forefeet planted
        out.update(pose=dog.blend(_p_think(), _p_grip2(), clamp(w)), grip=ease(u, U_GRIP2 + 0.06, U_GRIP2 + 0.14))
        return out
    if u < U_SNAP:
        k = ease(u, U_SNAP - 0.14, U_SNAP)                       # the heave: the hind end comes up off the gravel
        g = _p_grip2()
        p = _w(g, cx=g["cx"] - 12 * k, cy=g["cy"] + 4 * k, pitch=g["pitch"] + 0.3 * k, hny=10 * k, hfy=14 * k, hnx=g["hnx"] + 8 * k,
               neck=g["neck"] + 0.2 * k, head=g["head"] + 0.15 * k, ear=0.1, ear_f=0.1, eye=1.3)
        out.update(pose=p, grip=1.0, strain=1.0)
        return out
    # it comes apart: the dog goes over backwards through the water with half of it
    g = _p_grip2()
    p0 = _w(g, cx=g["cx"] - 12, cy=g["cy"] + 4, pitch=g["pitch"] + 0.3, hny=10, hfy=14, hnx=g["hnx"] + 8, neck=g["neck"] + 0.2, head=g["head"] + 0.15,
            ear=0.1, ear_f=0.1, eye=1.3)
    q0, bx0, by0 = _as_body(p0, TUG_XA, gy, -1)
    a = u - U_SNAP
    fl = dog.wait_float(u, pitch=0.5)
    fl = _w(fl, jaw=0.33, hold=1.0, eye=1.35, ear=1.2, ear_f=1.25, tail=0.9)
    look = ease(u, U_TEAR - 0.02, U_TEAR + 0.12)                 # it looks down at what it left behind
    fl = _w(fl, neck=lerp(0.75, 0.2, look), head=lerp(0.55, -0.55, look), ear=lerp(1.2, 0.5, look), ear_f=lerp(1.25, 0.45, look),
            pitch=fl["pitch"] - 0.25 * look)
    fl["_anchor"] = "body"
    w = clamp(1 - math.exp(-a * 9.0))                            # thrown, then the water stops it
    p, x, y = _blend_body(q0, (bx0, by0), fl, (bx0 + 34, by0 - 30), w)
    y -= 8 * ease(u, U_TEAR, TUG_LEN + 0.2)                     # and it is already going up
    out.update(pose=p, x=x, y=y, anchor="body", has=True)
    return out


def _reel_state(u):
    """Where the stuck reel is while it is whole -> (x, y, tip degrees, buried 0..1)."""
    d = _tug_dog(u)
    lift = tip = 0.0
    if U_PULL <= u < U_SLIP:
        lift, tip = 4.5 * d["strain"], 9.0 * d["strain"]
    elif U_SLIP <= u < U_THINK + 0.2:
        a = u - U_SLIP                                             # it drops back, rocks, and is still
        lift = 4.5 * max(0.0, 1 - a / 0.07)
        tip = 9.0 * math.exp(-a * 9) * math.cos(2 * math.pi * 5 * a)
    elif u >= U_SNAP - 0.14:
        k = ease(u, U_SNAP - 0.14, U_SNAP)
        lift, tip = 6.0 * k, 12.0 * k
    dug = 0.42 + 0.2 * (1 - ease(u, 0.0, U_PULL))                # the raking has bared it
    return REEL_AT[0] + 0.5 * lift, REEL_AT[1] - lift, tip, dug


def _mound(ink, cam, x, y, w, h, seed=3):
    """Gravel banked against the near side of something that is in it (it is what makes the thing STUCK)."""
    z = cam.zoom
    sx, sy = cam.xy(x, y)
    rs = random.Random(seed)
    pts = [(sx - w * z / 2, sy + h * z * 0.5)]
    for k in range(9):
        f = k / 8
        pts.append((sx - w * z / 2 + w * z * f, sy + h * z * 0.5 - h * z * math.sin(math.pi * f) ** 0.7 * (0.8 + 0.25 * rs.random())))
    pts.append((sx + w * z / 2, sy + h * z * 0.5))
    ink.d.polygon(pts, fill=(118, 138, 120, 255))
    ink.d.line(pts[:-1] + [pts[-1]], fill=(20, 40, 40, 230), width=max(1, int(z * 0.8)), joint="curve")
    for _ in range(7):
        px = sx + rs.uniform(-0.42, 0.42) * w * z
        py = sy + h * z * 0.5 - rs.uniform(0.15, 0.7) * h * z * math.sin(math.pi * clamp((px - sx) / (w * z) + 0.5)) ** 0.7
        r = rs.uniform(1.0, 2.2) * z
        ink.d.ellipse([px - r, py - r * 0.7, px + r, py + r * 0.7], fill=(166, 182, 160, 255), outline=(30, 50, 48, 255))


def _ubub(ink, cam, x, y, r):
    sx, sy = cam.xy(x, y)
    r *= cam.zoom
    ink.d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(190, 236, 232, 46), outline=(214, 244, 238, 200), width=max(1, int(r * 0.22)))
    ink.d.ellipse([sx - r * 0.5, sy - r * 0.55, sx - r * 0.1, sy - r * 0.15], fill=(250, 255, 250, 190))


def _ububbles(ink, cam, src, t0, t1, u, rate=14.0, seed=0, size=1.0):
    """Air from a nose under water: born at src(time) between t0 and t1, wobbling up."""
    rs = random.Random(seed * 31 + 7)
    n = int((t1 - t0) * rate)
    for k in range(n):
        tb = t0 + (k + rs.random()) / rate
        wob, r, vy = rs.uniform(0, 6.28), rs.uniform(1.0, 2.6) * size, rs.uniform(46, 74)
        age = u - tb
        if age < 0 or age > 2.0:
            continue
        x, y = src(tb)
        _ubub(ink, cam, x + 5 * math.sin(wob + age * 5) + rs.uniform(-3, 3), y - vy * age - 6 * age * age, r * min(1.0, 0.4 + age * 3))


def _usilt(ink, cam, x, y, age, power=1.0, seed=0):
    """_silt at the close camera's size."""
    if age < 0 or age > 2.2:
        return
    lay = Image.new("RGBA", (220, 150), (0, 0, 0, 0))
    hold = kit.Ink(0, 0)
    hold.img = lay
    _silt(hold, 110, 118, age, power, seed)
    lay = hold.img
    z = cam.zoom
    lay = lay.resize((int(220 * z), int(150 * z)), Image.BILINEAR)
    sx, sy = cam.xy(x, y)
    ink.img.paste(lay, (int(sx - 110 * z), int(sy - 118 * z)), lay)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _uthing(ink, cam, kind, x, y, s=1.0, angle=0.0, **kw):
    sx, sy = cam.xy(x, y)
    z = DS * cam.zoom * s
    if kind == "half":
        props.reel(ink, props.REEL_HALF, sx, sy, z, tilt=kw.get("tilt", 0.9), angle=angle, half=True, loop=kw.get("loop", 0.0), wet=0, **UT_THING)
    elif kind == "flange":
        sh = props._part_sheet("flange", sx, sy, z * FLANGE_S, angle, kw.get("mud", 0.35), 0.0, 0.0, 0.0)
        if kw.get("squash"):
            sh.squash(kw["squash"])
        sh.lay(ink, 1.0, **UT_THING)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _ufilm(ink, cam, a, b, sag, alpha=1.0):
    """A length of real film between two world points."""
    pa, pb = cam.xy(*a), cam.xy(*b)
    props.film_strip(ink, props.REEL_HALF, pa, pb, sag=sag * cam.zoom, s=DS * cam.zoom * 1.25, lit=0.0, alpha=alpha)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def _udog(ink, cam, st, carry=None):
    sx, sy = cam.xy(st["x"], st["y"])
    j = dog.draw_dog(ink, st["pose"], sx, sy, scale=DS * cam.zoom, facing=st["facing"], anchor=st["anchor"], shadow=False, carry=None, **UT)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    return j


def _ubase(ink, tt, cam, look, lv, cls, skip=()):
    town.back(ink, tt, cam, sky=False, door=1.0)
    town.street(ink, tt, cam, holes=3, smudges=1, taken=(0,))
    for q in sorted(lv, key=lambda q: town.HOLES[q][1]):
        _hole(ink, cam, q, lv[q])
    town.thing(ink, cam, "boot", BOOT_AT[0] - 34, BOOT_AT[1] + 3, -16)
    town.thing(ink, cam, "spool", *SPOOL_AT)
    town.thing(ink, cam, "pin", PIN_AT[0], PIN_AT[1], PIN_AT[2])
    town.townsfolk(ink, tt, cam, look=look)
    town.school_class(ink, tt, cam, look=look, skip=skip, **cls)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def tug_draw(u, ink):
    """Round three, at the gravel (u = seconds into the shot, 0..TUG_LEN)."""
    u = clamp(u, 0.0, TUG_LEN)
    cam = _ucam()
    tt = TUG_T + u
    d = _tug_dog(u)
    rx, ry, tip, dug = _reel_state(u)
    snap = u - U_SNAP
    # the class: they lean over to see; they duck when its teeth slip and when it comes apart; then they look at what is left
    duck = bump((u - U_SLIP) / 0.3) + 1.3 * bump(snap / 0.34)
    lean = 20.0 * ease(u, 0.0, 0.3) - 34.0 * duck
    tilt = {k: 8.0 + lean * (1.0 if k in (0, 1, 4) else 0.6) for k in range(8)}
    arm = {k: 20.0 + 120.0 * clamp(duck) for k in (0, 1, 4, 5)}
    point = ease(u, U_TEAR - 0.02, U_TEAR + 0.12)
    arm[WAVER] = lerp(20.0, 96.0, point)                             # the waver points a fin at the side that stayed
    look = (rx, ry) if snap < 0.12 else ((REEL_AT[0], REEL_AT[1]) if point > 0.5 else (d["x"], d["y"] - 30))
    _ubase(ink, tt, cam, look, {3: 1.0, 6: 1.0, 5: 0.35 + 0.65 * ease(u, 0.0, U_PULL)}, dict(tilt=tilt, arm=arm))
    # the reel in the gravel: film wound between two sides, a third of it still in
    if snap < 0:
        _uthing(ink, cam, "half", rx + 1.5, ry - 0.5, angle=tip)
        _uthing(ink, cam, "flange", rx, ry, angle=tip + 20, mud=0.5)
    else:
        # the near side stays where it was, rocking; the film pays out to the dog, goes tight, and tears
        rock = 14.0 * math.exp(-snap * 6) * math.cos(2 * math.pi * 4 * snap)
        _uthing(ink, cam, "flange", REEL_AT[0], REEL_AT[1], angle=20 + rock, mud=0.5)
    _mound(ink, cam, REEL_AT[0] - 1, REEL_AT[1] + REEL_R * (1.0 - 0.9 * dug) + 2.0, 40.0, 13.0)
    if U_SLIP <= u:
        _usilt(ink, cam, REEL_AT[0], REEL_AT[1] + 6, u - U_SLIP, 0.7, seed=4)
    if snap >= 0:
        _usilt(ink, cam, REEL_AT[0] + 6, REEL_AT[1] + 4, snap, 1.25, seed=9)
    # the dog (and, once it has it, the half in its mouth, with the film between)
    j = _udog(ink, cam, d)
    mx, my = cam.world(*j["mouth"])
    if d["has"]:
        hx, hy = mx - 3.0, my + 12.0
        if u < U_TEAR:
            _ufilm(ink, cam, (REEL_AT[0] + 2, REEL_AT[1] - 3), (hx - 8, hy + 4), sag=16.0 * (1 - ease(u, U_SNAP, U_TEAR - 0.03)))
        else:
            a = u - U_TEAR                                           # torn: the end left behind sinks toward the gravel
            fx = lerp(REEL_AT[0] + 14, STRIP_LIES[0], ease(a, 0.0, 0.5))
            fy = lerp(REEL_AT[1] - 14, STRIP_LIES[1] + 2, clamp(a / 0.5) ** 1.5)
            _ufilm(ink, cam, (fx - 12, fy + 2 - 4 * a), (fx + 14, fy - 3), sag=5.0 + 4 * math.sin(a * 9))
        _uthing(ink, cam, "half", hx, hy, angle=-18 + 10 * math.sin(6 * snap), loop=1.0, tilt=0.82)
        j = _udog(ink, cam, dict(d, pose=d["pose"]))                  # its muzzle is in front of what it holds
    if d.get("bits"):
        dog.draw_bits(ink, dog.dig_spray(u + 0.5, rate=3.4, water=True), *cam.xy(d["x"], d["y"]), DS * cam.zoom, facing=-1, color=(150, 160, 136))
    # air: a string from its nose as it strains, a burst when it comes apart
    def nose(tb):
        jj = dog.draw_dog(Image.new("RGB", (8, 8)), _tug_dog(tb)["pose"], _tug_dog(tb)["x"], _tug_dog(tb)["y"], scale=DS, facing=-1,
                          anchor=_tug_dog(tb)["anchor"], shadow=False)
        return jj["nose"][0] - 2, jj["nose"][1] - 4
    _ububbles(ink, cam, nose, U_PULL + 0.12, U_SLIP, u, rate=16.0, seed=1, size=0.8)
    _ububbles(ink, cam, nose, U_SLIP, U_SLIP + 0.1, u, rate=60.0, seed=2, size=1.3)
    _ububbles(ink, cam, nose, U_SNAP, U_SNAP + 0.12, u, rate=90.0, seed=3, size=1.5)
    town.front(ink, tt, cam)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.vignette(0.22)


GIVE_XA, GIVE_GY = XA_D, GY_D                     # the dog's ground point as it rakes at hole 4
FILM_LIES = ((604.0, 846.0), (HOLE_D[0] - 2.0, HOLE_D[1] - 1.0))     # the torn film on the gravel, one end under


def _give_dog(v):
    """The dog in the handing-over -> dict(pose, x, y, facing, anchor, film (it has the film), flange 0..1 (it has that too))."""
    out = dict(x=GIVE_XA, y=GIVE_GY, facing=-1, anchor="ground", film=False, flange=0.0, bits=None)
    q_dig0, bxd, byd = _stand_body(GIVE_XA, GIVE_GY, -1, dog.dig(0.0))
    if v < V_LAND:
        keys = [(-0.2, bxd + 96, byd - 190.0), (0.0, bxd + 70, byd - 128.0), (V_LAND - 0.1, bxd + 8, byd - 34.0), (V_LAND, bxd, byd)]
        x, y, vx, vy = _hermite(keys, v)
        p = _swim_pose(v + 0.4, vx, vy, -1)
        land = ease(v, V_LAND - 0.12, V_LAND)
        if land > 0:
            p, x, y = _blend_body(p, (x, y), q_dig0, (bxd, byd), land)
        out.update(pose=p, x=x, y=y, anchor="body")
        return out
    took = _w(dog.stand(v), cx=-6.0, neck=0.42, head=-0.2, ear=1.16, ear_f=1.18, tail=0.75, curl=0.5, jaw=0.3, hold=1.0, eye=1.1,
              wag=0.5 * math.sin(2 * math.pi * 3.0 * v))
    if v < V_FREE:
        tau = v - V_LAND
        d = dog.dig(tau + 0.44, rate=3.8)                        # ONE rake: it knows what it has come for
        got = ease(v, V_FREE - 0.1, V_FREE)
        out.update(pose=dog.blend(d, _w(_p_grip(), jaw=0.3), got), bits=tau, film=got > 0.6)
        return out
    if v < V_OFF:
        w = dog.ease_back(clamp((v - V_FREE) / 0.2))             # its head comes up to the child, ears forward
        p = dog.blend(_w(_p_grip(), jaw=0.3), took, clamp(w))
        p["jaw"] = lerp(0.3, 0.42, bump((v - V_TAKE + 0.12) / 0.2))     # it opens for the piece, and shuts on it gently
        out.update(pose=p, film=True, flange=ease(v, V_TAKE - 0.08, V_TAKE))
        return out
    q0, bx0, by0 = _as_body(took, GIVE_XA, GIVE_GY, -1)
    keys = [(V_OFF - 0.1, bx0, by0 + 4), (V_OFF, bx0, by0), (V_OFF + 0.14, bx0 - 6, by0 - 26), (GIVE_LEN + 0.1, bx0 - 30, by0 - 150.0)]
    x, y, vx, vy = _hermite(keys, v)
    p = _swim_pose(v - V_OFF, vx, vy, -1)
    p["jaw"], p["hold"] = 0.3, 1.0
    off = ease(v, V_OFF, V_OFF + 0.16)
    if off < 1:
        p, x, y = _blend_body(q0, (bx0, by0), p, (x, y), off)
    out.update(pose=p, x=x, y=y, anchor="body", film=True, flange=1.0)
    return out


def give_draw(v, ink):
    """Round four, at the gravel, in the tug's own framing (v = seconds into the shot, 0..GIVE_LEN)."""
    v = clamp(v, 0.0, GIVE_LEN)
    cam = _ucam()
    tt = GIVE_T + v
    d = _give_dog(v)
    dig = clamp((v - V_LAND) / (V_FREE - V_LAND))
    lean = 16.0 * ease(v, 0.0, 0.3)
    wave = ease(v, V_TAKE + 0.02, V_TAKE + 0.12)
    cls = dict(tilt={k: 8.0 + lean for k in range(8)}, arm={k: 20.0 + 110.0 * wave * (0.5 + 0.5 * math.sin(2 * math.pi * 3 * v + k)) for k in (1, 5)})
    _ubase(ink, tt, cam, (d["x"] - 30, d["y"] - 30), {3: 1.0, 6: 1.0, 5: 1.0, 4: 0.25 + 0.75 * dig if v >= V_LAND else 0.0}, cls, skip=(WAVER,))
    if not d["film"]:
        _ufilm(ink, cam, FILM_LIES[0], FILM_LIES[1], sag=-3.0)
        if v < V_LAND + 0.1:
            _mound(ink, cam, FILM_LIES[1][0] + 2, FILM_LIES[1][1] + 2, 20.0, 7.0, seed=8)
    if v >= V_LAND:
        _usilt(ink, cam, HOLE_D[0], HOLE_D[1] + 4, v - V_LAND - 0.05, 0.8, seed=12)
    # the waver: it has pulled the stuck side out, and holds it up for the dog
    up = ease(v, V_FREE, V_TAKE)                                 # it swims up off its tail to reach the dog's mouth
    kx, ky = GIVE_KID[0] + 3 * up, GIVE_KID[1] - 9 * up
    reach = lerp(128.0, 100.0, up)
    reach = lerp(reach, 150.0 + 14 * math.sin(2 * math.pi * 3.5 * v), ease(v, V_TAKE + 0.03, V_TAKE + 0.16))     # and waves it off
    kid = town.child(ink, tt, cam, WAVER, kx, ky, facing=1, tilt=-10.0 - 8 * up, arm=reach, look=(d["x"] - 40, d["y"] - 40), swim=0.5 + 0.5 * up)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    hand = cam.world(*kid["hand"])
    j = _udog(ink, cam, d)
    mx, my = cam.world(*j["mouth"])
    fl_from = (hand[0] + 2, hand[1] - 9)
    fl_to = (mx - 6, my + 9)
    fx, fy = lerp(fl_from[0], fl_to[0], d["flange"]), lerp(fl_from[1], fl_to[1], d["flange"])
    if d["film"]:                                                # the film hangs from its mouth
        sway = 5 * math.sin(2 * math.pi * 1.8 * v)
        _ufilm(ink, cam, (mx + 2, my + 3), (mx + 10 + sway, my + 34), sag=5.0)
    _uthing(ink, cam, "flange", fx, fy, angle=20 + 30 * d["flange"], mud=0.2)
    if d["flange"] > 0.5:
        j = _udog(ink, cam, d)                                   # its muzzle in front of what it holds
        if d["film"]:
            sway = 5 * math.sin(2 * math.pi * 1.8 * v)
            _ufilm(ink, cam, (mx + 2, my + 3), (mx + 10 + sway, my + 34), sag=5.0)
    if d["bits"] is not None:
        dog.draw_bits(ink, dog.dig_spray(d["bits"] + 0.44, rate=3.8, water=True), *cam.xy(d["x"], d["y"]), DS * cam.zoom, facing=-1, color=(150, 160, 136))

    def nose(tb):
        dd = _give_dog(tb)
        jj = dog.draw_dog(Image.new("RGB", (8, 8)), dd["pose"], dd["x"], dd["y"], scale=DS, facing=-1, anchor=dd["anchor"], shadow=False)
        return jj["nose"][0] - 2, jj["nose"][1] - 4
    _ububbles(ink, cam, nose, 0.0, V_LAND, v, rate=14.0, seed=5, size=0.9)
    _ububbles(ink, cam, nose, V_OFF, GIVE_LEN, v, rate=18.0, seed=6, size=0.9)
    town.front(ink, tt, cam)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink.vignette(0.22)


# ====================================================================== #
#  8c · THE CUT (the film: the score, closer cameras on it, and the two shots under water)   #
# ====================================================================== #
# The score above is one continuous take. An independent critic who saw only the picture said what that cost:
# what the dog brings up could not be named (20 px, never a closer shot); three dives were one beat three times;
# the calf and the cow were small in a wide frame; there was no cut at all. So the film is now CUT from the score.
# Each entry: frames on screen, kind, score second it begins at, score second it ends at, close view (or None).
#   "score"  the score through its own camera            "close"  the same moment through a closer camera (_close)
#   "tug"    round three at the gravel (tug_draw)         "give"   round four at the gravel (give_draw)
# A cut may skip score time (an ellipsis); the two shots under water REPLACE the score's own digs for rounds three
# and four. Nothing above the water is slowed or stretched: one stretch under water (the long swim down of round
# two) runs 17 % fast to pay for the tug.

K_PAGE = dict(z=2.8, x0=106.0, y0=176.0)                    # the page held up to the lamp, the dog looking up at it
K_REEL = dict(z=2.6, x0=284.0, y0=226.0, strip=True)        # the first reel: in its mouth, laid, pawed; the cow it came up under
K_CALF = dict(z=2.1, x0=346.0, y0=205.0, strip=True)        # the calf and the dog, and the mother's head coming down
K_LAST = dict(z=4.2, x0=316.0, y0=292.0)                    # the strip and the flange laid; water running off its chin

EDL = [   # frames, kind, score from, score to, view, why the camera is there
    (134, "score", 0.0, 134 / FPS, None, "up with the page; the shake; the page laid; the hand comes for it"),
    (20, "close", 5.90, 5.90 + 20 / FPS, K_PAGE, "CUT IN: the page, large, in the hands at the lamp; the dog watching it"),
    (58, "score", 7.06, 7.06 + 58 / FPS, None, "CUT BACK: asked again; it looks at the water, and goes"),
    (33, "score", 7.06 + 58 / FPS, 11.08, None, "(no cut) down to the far holes, a little fast"),
    (45, "score", 11.08, 12.955, None, "(no cut) the reel found; up; it bursts out under the drinking cow's nose"),
    (36, "close", 12.955, 14.455, K_REEL, "CUT IN: the reel in its mouth, laid, the paw on it; she has jerked her head up"),
    (27, "score", 14.455, 15.58, None, "CUT BACK: the hand points; it goes"),
    (50, "tug", 0.0, 50 / FPS, None, "CUT: at the gravel. The reel is stuck; it slips; it thinks; it comes apart"),
    (51, "score", 16.78, 18.905, None, "CUT: up with half of it; laid; the calf follows it out along the boards"),
    (56, "close", 18.95, 18.95 + 56 / FPS, K_CALF, "CUT IN: the calf nosed back; its mother's tongue; the dog watches that it stays"),
    (29, "give", 0.0, 29 / FPS, None, "CUT, on the dive: the waver holds up the side that stayed; one rake for the film"),
    (18, "score", 22.39, 23.14, None, "CUT: up with both, the camera coming up with it"),
    (18, "close", 23.14, 23.89, K_LAST, "CUT IN: the strip and the flange on the wet boards; it does not shake"),
    (49, "score", 26.0 - 49 / FPS, 26.0, None, "CUT BACK: the spent dog, the person down beside it, the queue still a queue"),
]
assert sum(e[0] for e in EDL) == int(round(SECONDS * FPS))


def _edl_starts():
    out, k = [], 0
    for e in EDL:
        out.append(k)
        k += e[0]
    return out


EDL_K0 = _edl_starts()
TUG_AT = EDL_K0[[e[1] for e in EDL].index("tug")] / FPS       # screen seconds the two shots under water begin at
GIVE_AT = EDL_K0[[e[1] for e in EDL].index("give")] / FPS


def edit_at(t):
    """Screen second -> (kind, the time to draw (score seconds, or seconds into the tug / the give), view, index)."""
    k = clamp(t, 0.0, SECONDS) * FPS
    for i, (n, kind, a, b, view, _) in enumerate(EDL):
        k0 = EDL_K0[i]
        if k < k0 + n - 1e-6 or i == len(EDL) - 1:
            return kind, lerp(a, b, clamp((k - k0) / n)), view, i
    raise AssertionError


def screen_of(ts):
    """Score second -> the screen second it is seen at (or, if the cut skips it, the cut it falls behind)."""
    best = None
    for i, (n, kind, a, b, view, _) in enumerate(EDL):
        if kind in ("tug", "give"):
            continue
        k0 = EDL_K0[i]
        if a - 1e-9 <= ts <= b + 1e-9:
            return (k0 + n * (ts - a) / max(b - a, 1e-9)) / FPS
        if ts > b:
            best = (k0 + n) / FPS
    return 0.0 if best is None else best


def draw(t, ink, record=False):
    """One full 960x540 frame of S3 at screen second t (0..26): the film."""
    kind, tau, view, _ = edit_at(t)
    if kind == "tug":
        return tug_draw(tau, ink)
    if kind == "give":
        return give_draw(tau, ink)
    return _score_draw(tau, ink, record=record, close=view)


# ====================================================================== #
#  9 · THE SOUND (laid with sound.py; nobody here has heard it)           #
# ====================================================================== #

def heard(t, wx):
    """Where a source at world x is for the ear: pan from where it is in the frame under this shot's camera."""
    x0, y0, x1, y1 = view_rect(camera(t))
    return clamp(((wx - x0) / (x1 - x0) - 0.5) * 1.5, -0.9, 0.9)


def _one_tap(mix, at, gain=0.12, pan=None):
    """One tap on the rail (sound.taps is always the four-tap motif; rounds three and four ask with one)."""
    pan = snd.P_DOOR + 0.1 if pan is None else pan
    try:
        snd._put(mix, snd._knock_sig(snd._m("taps", at, 0.2), 236), at, gain, pan)
    except Exception:                                           # the library changed: the kit's own wooden step
        mix.step(at, gain=gain, pan=pan, surface="wood")


def _slide(mix, t0, t1, pan=None):
    """A pebble sent along the rail: a small dry scrape, then the click as it stops against the others."""
    pan = snd.P_DOOR + 0.1 if pan is None else pan
    snd.card_drag(mix, t0, max(0.2, t1 - t0 - 0.04), gain=0.018, pan=pan)
    snd.pebble(mix, t1, pan=snd.P_DOOR)


def sound(mix, at=0.0):
    """S3's sound into `mix`, local 0 at `at` seconds. Every contact is timed to the frame it lands on in THIS
    picture (the board's rule: the builder's frame wins, the sound moves). Two tempos that never merge: every cow
    sound walks at 0.55 s a step; the dog's rounds get shorter. The radio's phrases do not speed up."""
    S = snd

    def A(t):
        return at + screen_of(t)                                  # the picture is cut: a contact is where the cut puts it

    wk = _walkers()
    # ---- the two shots under water: the BELOW room, and what happens in them
    for a0, ln in ((TUG_AT, TUG_LEN), (GIVE_AT, GIVE_LEN)):
        S.hush(mix, at + a0, ln, 0.6, 0.04, 0.04)
    pt = S.P_WATER * 0.2
    S.dig(mix, at + TUG_AT, U_PULL - 0.1, find=None, gain=0.07, pan=pt)
    S.bubbles(mix, at + TUG_AT + U_PULL + 0.1, 5, 0.4, gain=0.03, pan=pt)
    S.nose_bump(mix, at + TUG_AT + U_SLIP, gain=0.06, pan=pt)                                  # its teeth come off the rim
    S.bubbles(mix, at + TUG_AT + U_SLIP, 3, 0.2, low=True, gain=0.04, pan=pt)
    S.dig(mix, at + TUG_AT + U_GRIP2, U_SNAP - U_GRIP2, find="ring", gain=0.08, pan=pt)         # it comes apart: a small tin ring
    S.bubbles(mix, at + TUG_AT + U_SNAP, 6, 0.3, gain=0.05, pan=pt)
    S.dig(mix, at + GIVE_AT + V_LAND, V_FREE - V_LAND, find=None, gain=0.07, pan=pt)
    S.collar(mix, at + GIVE_AT + V_TAKE, 2, gain=0.03, pan=pt, under=True)                     # the piece taken, gently
    S.bubbles(mix, at + GIVE_AT + V_OFF, 4, 0.25, gain=0.03, pan=pt)
    # ---- rooms: below until its head breaks the line; above; both at half in the split; above again
    S.hush(mix, A(-0.1), T_B1 + 0.2, 1.0, 0.2, 0.2)
    S.above(mix, A(T_B1 - 0.1), 9.3 - T_B1 + 0.3, 1.0, 0.2, 0.3)
    S.above(mix, A(9.3), 17.85 - 9.3, 0.5, 0.3, 0.1)
    S.hush(mix, A(9.3), 17.85 - 9.3, 0.5, 0.3, 0.1)
    S.above(mix, A(17.85), 21.3 - 17.85, 1.0, 0.05, 0.05)
    S.above(mix, A(21.3), 1.6, 0.5, 0.05, 0.4)
    S.hush(mix, A(21.3), 1.6, 0.5, 0.05, 0.4)
    S.above(mix, A(22.7), SECONDS - 22.7 + 0.1, 1.0, 0.3, 0.2)
    S.crickets(mix, A(T_B1 + 0.3), SECONDS - T_B1 - 0.3, 3)
    S.music_s3(mix, t0=at)                                        # the radio: a phrase every 3 s; off after +20.2
    # ---- round one: up, the shake, the page, the paw
    S.bubbles(mix, A(0.2), 4, 0.8, gain=0.03, pan=heard(0.5, 440))
    S.swap_up(mix, A(T_B1))
    for hit in LEAD_BELL_HITS:
        S.cowbell(mix, A(hit), gain=0.06 if hit < T_SH1 else 0.045, pan=heard(hit, 560), hard=abs(hit - T_B1 - 0.06) < 0.01)
    S.hooves(mix, A(T_B1 + 0.2), 2, 0.3, "earth", gain=0.08, pan=heard(1.5, 580))             # she backs a step
    S.paws(mix, A(T_L1), 2, 0.07, gain=0.12, pan=heard(T_L1, X_SHAKE), wet=True)
    S.shake(mix, A(T_SH1 + 0.2), D_SH1 - 0.2, pan=heard(2.2, X_SHAKE))
    S.paws(mix, A(T_TR1 + 0.05), 4, 0.11, gain=0.09, pan=heard(3.0, 410), wet=True)
    S.page_slap(mix, A(T_LAID1), pan=heard(T_LAID1, THING_X[0]))
    S.paw_press(mix, A(T_PRESS1), pan=heard(T_PRESS1, THING_X[0]))
    lead = wk["lead"]
    for (tt, x, y, leg) in lead.hoof_falls(T_LEAD_WALK, 10.9)[::1]:
        S.hooves(mix, A(tt), 1, 0.55, "earth", gain=lerp(0.085, 0.04, clamp((tt - T_LEAD_WALK) / 6)), pan=heard(tt, x))
    for hit in lead.bell_hits:
        if T_LEAD_WALK < hit < 11.5:
            S.cowbell(mix, A(hit), gain=lerp(0.05, 0.025, clamp((hit - T_LEAD_WALK) / 6)), pan=heard(hit, 700))
    # ---- asked again
    S.creak(mix, A(4.7), 0.4, pan=S.P_STEP)
    S.paws(mix, A(T_BACK1 + 0.1), 3, 0.22, gain=0.08, pan=heard(5.3, 400))
    S.taps(mix, A(TAPS_1[0]))
    _slide(mix, A(PEBBLES[0][2]), A(PEBBLES[0][3]))
    sec = wk["second"]
    for (tt, x, y, leg) in sec.hoof_falls(4.35, 8.9):
        S.hooves(mix, A(tt), 1, 0.55, "wood" if 330 < x < 360 else "earth", gain=0.075, pan=heard(tt, x))
    S.drinking(mix, A(9.4), 14.0 - 9.4)                                                        # one unbroken slow drinking
    S.collar(mix, A(T_TURN1 + 0.15), 2, gain=0.04, pan=heard(T_TURN1, X_WAIT))
    S.paws(mix, A(T_GO1 + 0.04), 4, 0.1, gain=0.1, pan=heard(T_GO1, X_WAIT), pan_to=heard(9.1, X_END), wet=True)
    S.swap_down(mix, A(T_D2))
    # ---- round two (in the split both rooms are at half; what is under the line is filtered)
    S.dig(mix, A(T_DIG_A), 0.5, find=None, gain=0.07, pan=heard(T_DIG_A, HOLE_A[0]), under=True)
    S.dig(mix, A(T_DIG_B), T_FOUND2 - T_DIG_B, find="ring", gain=0.08, pan=heard(T_DIG_B, HOLE_B[0]), under=True)
    S.breach(mix, A(T_B2), gain=0.28, pan=heard(T_B2, XB2))
    S.paws(mix, A(T_L2), 2, 0.06, gain=0.1, pan=heard(T_L2, X_LAY2), wet=True)
    S.reel_down(mix, A(T_LAID2), gain=0.16, pan=heard(T_LAID2, THING_X[1]))
    S.paw_press(mix, A(T_PRESS2), pan=heard(T_PRESS2, THING_X[1]))
    S.shake(mix, A(T_SH2 + 0.2), T_FREEZE - T_SH2 - 0.2, gain=0.13, pan=heard(T_SH2, X_PAW2))
    _one_tap(mix, A(TAP_2[0]))
    _slide(mix, A(PEBBLES[1][2]), A(PEBBLES[1][3]))
    for (tt, x, y, leg) in sec.hoof_falls(14.5, 22.9):
        S.hooves(mix, A(tt), 1, 0.55, "earth", gain=lerp(0.075, 0.03, clamp((tt - 14.5) / 6)), pan=heard(tt, x))    # the cow tempo does not change
    S.paws(mix, A(T_GO2 + 0.06), 3, 0.09, gain=0.11, pan=heard(T_GO2, X_PAW2), pan_to=heard(T_D3, 560), wet=True)
    S.plunge(mix, A(T_D3), gain=0.3, pan=heard(T_D3, 580))
    # ---- round three: sooner
    S.breach(mix, A(T_B3), gain=0.27, pan=heard(T_B3, XB3))
    S.paws(mix, A(T_L3), 2, 0.06, gain=0.1, pan=heard(T_L3, X_LAY3), wet=True)
    S.reel_down(mix, A(T_LAID3), gain=0.1, pan=heard(T_LAID3, THING_X[2]))                    # half made
    mo = wk["mother"]
    for (tt, x, y, leg) in mo.hoof_falls(15.0, 18.4):
        S.hooves(mix, A(tt), 1, 0.55, "wood" if 330 < x < 360 else "earth", gain=0.075, pan=heard(tt, x))
    S.calf(mix, A(15.5), 8, 0.22, gain=0.04, pan=heard(16.0, 420), pan_to=heard(17.4, X_CALF_STOP))    # it trots down after her
    # ---- round four, and the calf
    _one_tap(mix, A(TAP_3[0]))
    _slide(mix, A(PEBBLES[2][2]), A(PEBBLES[2][3]))
    S.paws(mix, A(T_TROT3 + 0.03), 5, 0.1, gain=0.1, pan=heard(18.0, X_LAY3), pan_to=heard(18.5, X_END), wet=True)
    S.wade(mix, A(T_WADE), 0.4, 2, pan=heard(T_WADE, X_END + 20))
    S.calf(mix, A(T_CALF_GO + 0.06), 6, 0.125, pan=heard(T_CALF_GO, X_CALF_STOP), pan_to=heard(T_CALF_SKID, X_CALF_SKID))
    S.splash(mix, A(T_CALF_SKID), gain=0.08, pan=heard(T_CALF_SKID, X_CALF_SKID + 20))
    S.taps(mix, A(TAPS_4[0]), gain=0.1)                                                        # asked again before it is back
    S.nose_bump(mix, A(T_NUDGE + 0.55), pan=heard(19.6, 545))
    S.nose_bump(mix, A(T_NUDGE + 1.05), pan=heard(20.1, 530))
    S.calf(mix, A(T_NUDGE + 0.6), 3, 0.14, gain=0.05, pan=heard(19.7, 520))
    S.calf(mix, A(T_CALF_BACK + 0.05), 4, 0.15, gain=0.05, pan=heard(20.3, 500), pan_to=heard(20.8, X_CALF_HOME))
    _slide(mix, A(PEBBLES[3][2]), A(PEBBLES[3][3]))
    S.plunge(mix, A(T_D4), gain=0.28, pan=heard(T_D4, 604))
    S.breach(mix, A(T_B4), gain=0.26, pan=heard(T_B4, XB4))
    S.paws(mix, A(T_L4), 2, 0.07, gain=0.1, pan=heard(T_L4, X_LAY4), wet=True)
    S.page_slap(mix, A(T_LAID4), gain=0.07, pan=heard(T_LAID4, THING_X[3]))
    S.pebble(mix, A(T_LAID4 + 0.06), gain=0.03, pan=heard(T_LAID4, THING_X[4]))               # the flange, a small tin tick
    for (tt, x, y, leg) in mo.hoof_falls(T_M_ON, T_M_DRINK):
        S.hooves(mix, A(tt), 1, 0.55, "earth", gain=0.06, pan=heard(tt, x))
    # ---- the tired dog; something quiet
    S.pant(mix, A(T_SPENT - 0.2), SECONDS - T_SPENT + 0.1, gain=0.045, pan=heard(24.0, X_LAY4))
    S.drip(mix, A(T_L4 + 0.3), 6, 0.48, pan=heard(24.0, X_LAY4))
    S.creak(mix, A(T_CROUCH + 0.25), 0.5, pan=S.P_STEP)
    S.drinking(mix, A(T_M_DRINK + 0.8), SECONDS - T_M_DRINK - 0.8, gain=0.04)
    S.voice_quiet(mix, A(LINE2[0]))
    for (tt, x, y, leg) in wk["lead2"].hoof_falls(T_LEAD_BACK, T_LEAD_BACK + 1.9):
        S.hooves(mix, A(tt), 1, 0.55, "grass", gain=0.04, pan=heard(tt, x))
    for hit in wk["lead2"].bell_hits:
        if T_LEAD_BACK < hit < T_LEAD_BACK + 2.6:
            S.cowbell(mix, A(hit), gain=0.03, pan=heard(hit, 820))             # her bell, coming back
    fo = wk["fourth"]
    for (tt, x, y, leg) in fo.hoof_falls(20.5, 24.3)[::2]:
        S.hooves(mix, A(tt), 1, 0.55, "earth", gain=0.035, pan=heard(tt, x))
    return mix


# ====================================================================== #
#  10 · CHECKS                                                            #
# ====================================================================== #

def _render(t, record=False):
    ink = kit.Ink(t, int(round(t * FPS)))
    ink.paper()
    stg = _score_draw(t, ink, record=record)
    return ink, stg


def _find(mattes, pat):
    return [n for n in mattes if _match(n, pat)]


def check(verbose=True, pixels=True):
    out = []

    def say(s):
        out.append(s)
        if verbose:
            print("  " + s, flush=True)

    frames = [k / FPS for k in range(int(SECONDS * FPS) + 1)]
    # 1 · the camera: boundary framings; continuous except at the two declared cuts
    c0, c1 = camera(0.0), camera(SECONDS)
    assert (c0["oy"], c0["sq"], c0["zoom"]) == (360.0, 0.0, 1.0) and (c1["oy"], c1["sq"], c1["zoom"]) == (0.0, 0.0, 1.0)
    cuts = [s[0] for s in SHOTS if s[3] == "CUT"]
    for a, b in zip(frames, frames[1:]):
        ca, cb = camera(a), camera(b)
        jump = abs(ca["oy"] - cb["oy"]) + abs(ca["sq"] - cb["sq"]) + 200 * abs(ca["zoom"] - cb["zoom"])
        is_cut = any(a < c <= b + 1e-9 for c in cuts)
        assert jump < 40 or is_cut, ("camera jump", a, jump)
    k0, t0_, _, _ = edit_at(0.0)
    k1, t1_, _, _ = edit_at(SECONDS)
    assert (k0, t0_, k1, t1_) == ("score", 0.0, "score", SECONDS)
    for n, kind, a, b, view, _ in EDL:
        if kind in ("score", "close"):
            assert 0.98 < (b - a) / (n / FPS) < 1.2, ("a shot runs off speed", kind, a, b)
    ncut = sum(1 for (e0, e1) in zip(EDL, EDL[1:]) if e0[1] != e1[1] or e0[4] is not e1[4] or abs(e0[3] - e1[2]) > 1e-6)
    say("MEASURED cut: %d shots, %d cuts; begins on the score's first frame and ends on its last; no shot off speed but the swim"
        " down of round two (%.0f %% fast); the tug is at %.2f-%.2f, the handing over at %.2f-%.2f" % (
            len(EDL), ncut, 100 * ((EDL[3][3] - EDL[3][2]) / (EDL[3][0] / FPS) - 1), T0 + TUG_AT, T0 + TUG_AT + TUG_LEN, T0 + GIVE_AT, T0 + GIVE_AT + GIVE_LEN))
    say("MEASURED camera: F-TOWN at 58.0, F-PORCH at 84.0 (zoom 1); continuous everywhere but at the declared cut %s" % [T0 + c for c in cuts])
    # 2 · the squeeze is continuous and monotonic, and 1:1 above the line and below the zone
    ys = [sq_y(400 + d, SPLIT_OY, SPLIT_SQ) for d in range(-50, 480)]
    assert all(b > a for a, b in zip(ys, ys[1:])) and max(b - a for a, b in zip(ys, ys[1:])) <= 1.0 + 1e-9
    assert sq_y(380, 250, 85) == 130 and sq_y(800, 250, 85) == 800 - 335
    say("MEASURED squeeze: monotonic, never steeper than 1:1; line at screen 150, gravel at 465, hole 3 at %.0f" % sq_y(HOLE_B[1], 250, 85))
    # 3 · the dog: boundary; every down has an up with a thing; it is never empty-mouthed coming up
    s0, s1 = dog_state(0.0), dog_state(SECONDS)
    assert (round(s0["x"], 3), round(s0["y"], 3), s0["facing"], s0["carry"]) == (430.0, 550.0, -1, "page"), s0
    assert (s1["x"], s1["y"], s1["facing"], s1["anchor"]) == (470.0, 394.0, -1, "ground")
    for (td, _), (tb, _), thing in zip(DIVES, BREACHES[1:], ("reel", "half", "both")):
        assert td < tb and dog_state(tb - 0.05)["carry"] == thing and dog_state(tb + 0.1)["carry"] == thing, (td, tb, thing)
    assert dog_state(T_B1 - 0.05)["carry"] == "page"
    rounds = [T_D2 - T_B1, T_D3 - T_D2, T_D4 - T_D3, T_B4 + (T_L4 - T_B4) - T_D4]
    say("MEASURED crossings: up at %s with page, reel, one-sided reel, strip and flange; down at %s; no dog comes up empty" % (
        [round(T0 + tb, 2) for tb, _ in BREACHES], [round(T0 + td, 2) for td, _ in DIVES]))
    under = [tb - td for (td, _), (tb, _) in zip(DIVES, BREACHES[1:])]
    assert under[0] > under[1] > under[2]
    say("MEASURED sooner: seconds under water each round %s; seconds from one dive to the next %s" % (
        [round(u, 2) for u in under], [round(T_D3 - T_D2, 2), round(T_D4 - T_D3, 2)]))
    # 4 · the dog never slides: on the board, between two frames of one standing action its ground point is still,
    #     and its place is continuous across every seam (no pop bigger than a stride step)
    worst = 0.0
    for a, b in zip(frames, frames[1:]):
        if any(a < c <= b + 1e-9 for c in cuts):
            continue
        da, db = dog_state(a), dog_state(b)
        ja, jb = _dog_points(int(round(a * FPS))), _dog_points(int(round(b * FPS)))
        d = math.hypot(ja["body"][0] - jb["body"][0], ja["body"][1] - jb["body"][1])
        worst = max(worst, d)
        assert d < 56, ("the dog jumps", a, b, d, da["where"], db["where"])
    say("MEASURED continuity: the dog's body never moves more than %.0f px between two frames (fastest: the dives)" % worst)
    # 5 · the holds
    for a, b, what in ((T_TURN1 + 0.36, T_GO1 - 0.15, "looks at the water (board: 0.6 s at 66.2; here %.2f-%.2f, then the tail lifts)" % (T0 + T_TURN1 + 0.36, T0 + T_GO1 - 0.15)),
                       (T_FREEZE + 0.08, T_GO2 - 0.02, "mid-shake, looking at the hand, one ear inside out"),
                       (T_WATCH + 0.45, T_TURN4 - 0.02, "watches that the calf stays, one ear cocked")):
        pa = dog_state(a)
        for q in range(1, 8):
            pb = dog_state(lerp(a, b, q / 7))
            dv = max(abs(pa["pose"][k] - pb["pose"][k]) for k in pa["pose"] if isinstance(pa["pose"][k], (int, float)) and k in pb["pose"] and k not in ("wag",))
            assert dv < 0.16 and abs(pa["x"] - pb["x"]) < 0.01, (what, dv)       # it breathes; nothing else
        say("MEASURED hold: %s, %.2f s, the dog still" % (what, b - a))
    assert LINE2[1] <= 24.8 + 1e-9 and SECONDS - LINE2[1] >= 1.2 - 1e-9
    qa = person_q(25.4)
    assert max(abs(qa[k] - person_q(25.95)[k]) for k in qa) < 0.6
    say("MEASURED hold: after the quiet line, %.1f s (82.8-84.0): the person still, the dog only breathing" % (SECONDS - LINE2[1]))
    # 6 · holes never fill in; pebbles; the pile
    last = {}
    for tt in frames:
        lv = hole_levels(tt)
        for k, v in lv.items():
            assert v >= last.get(k, 0.0) - 1e-9
        for k in last:
            assert k in lv
        last = lv
    assert sorted(last) == [3, 4, 5, 6] and all(abs(v - 1) < 1e-9 for v in last.values())
    assert pebble_string(SECONDS) == "wwggw" and pile_count(SECONDS) == 5 and pile_count(T_LAID1 - 0.05) == 0
    say("MEASURED record: holes 0..6 dug at 84.0 (three from S2 and four here: the board's beats give four digs; its table D says five);"
        " pebbles 'wwggw' (five, three white); five things on the sill, two paw prints")
    # 7 · the herd: one at a time
    for tt in frames[::6]:
        on_strip = [w for w in ("lead", "second", "mother") if cow_state(w, tt)["layer"] == "strip" and 352 <= cow_state(w, tt)["x"] < 640]
        xs = sorted(cow_state(w, tt)["x"] for w in on_strip)
        for a, b in zip(xs, xs[1:]):
            assert b - a > 150, ("two cows abreast", tt, xs)
        at_water = [w for w in ("lead", "second", "mother") if cow_state(w, tt)["layer"] == "strip" and abs(cow_state(w, tt)["x"] - X_DRINK) < 40]
        assert len(at_water) <= 1, (tt, at_water)
    ws = _walkers()
    for w in ("second", "mother", "fourth", "fifth", "sixth"):
        ks = ws[w].plan.keys
        for (ta, da), (tb, db) in zip(ks, ks[1:]):
            if db != da:
                v = abs(db - da) / (tb - ta)
                rel = 0.5 * (herd.PATH.at(da)["rel"] + herd.PATH.at(db)["rel"])
                assert v <= herd.SPEED * max(rel, 0.3) * 1.45 + 2, (w, ta, v, rel)
    e = {w: cow_state(w, SECONDS) for w in ("lead", "second", "mother", "fourth", "fifth", "sixth")}
    ce = calf_state(SECONDS)
    assert abs(e["mother"]["x"] - X_MOTHER_DRINK) < 3 and e["fourth"]["layer"] == "hill" and abs(e["fourth"]["d"] - SPOT[0]) < 1
    assert e["lead"]["facing"] == -1 and e["lead"]["x"] > 800 and e["second"]["x"] > 690 and ce["layer"] == "strip"
    say("MEASURED herd: never two cows within a cow's length on the strip; one at the water at a time; no cow faster than a walk;"
        " at 84.0 the mother drinks, the calf at her flank, the fourth above the gate, two on the path, two in the meadow")
    drinks = (14.0 - 9.3, T_D3 - T_D2)
    say("MEASURED two clocks: the second cow's one drink lasts %.1f s; inside it the dog goes down, digs twice, comes up, lays a reel and presses it" % drinks[0])
    # 8 · the occlusion graph on every frame: no cycle (topo raises), the order respects it
    names_seen = set()
    for tt in frames[::3]:
        names = ["queue.far", "queue.near", "cow.lead.body", "cow.second.body", "cow.mother.body", "cow.lead.head", "cow.mother.head", "calf",
                 "shadow.sill", "pile.0", "pile.1", "pile.2", "pile.3", "pile.4", "page.hand", "dog", "dog.below", "dog.above", "swim.dog",
                 "town", "bubbles", "weed", "splash"]
        order = topo(names, tt)
        pos = {names[i]: n for n, i in enumerate(order)}
        for f, b in dag_edges(tt):
            for a in names:
                for c in names:
                    if a != c and _match(a, f) and _match(c, b):
                        assert pos[a] > pos[c]
    say("STRUCTURAL occlusion graph: %d edges, no cycle at any sampled frame; the two would-be cycles are cut by sublayers"
        " (cow.mother.body < calf < cow.mother.head; cow.lead.body < the board < cow.lead.head)" % len(DAG))
    if not pixels:
        return out
    # 9 · on real pixels: every overlap event is real and the declared cel is the one drawn in front
    for (a, b, front, back, what) in EVENTS:
        best = (0, None)
        for q in range(5):
            tt = lerp(a, b, q / 4)
            ink, stg = _render(tt, record=True)
            fr, bk = _find(stg.mattes, front), _find(stg.mattes, back)
            order = [n for _, n in stg.order]
            for f in fr:
                for g in bk:
                    ov = _overlap(stg.mattes[f], stg.mattes[g])
                    if ov > best[0]:
                        si = {s: i for i, s in enumerate(SLOTS)}
                        slot = {n: s for s, n in stg.order}
                        infront = (si[slot[f]], order.index(f)) > (si[slot[g]], order.index(g))
                        best = (ov, infront)
        assert best[0] >= 12 and best[1], ("overlap event not found or wrong way round", front, back, a, b, best)
        say("MEASURED overlap %.2f-%.2f: %s in front of %s, %d px of both (%s)" % (T0 + a, T0 + b, front, back, best[0], what))
    # 10 · no pop: when a cel changes pass, it overlaps nothing that it jumps over
    for who in ("second", "mother"):
        prev = None
        for tt in frames:
            st = cow_state(who, tt)
            if prev and prev["layer"] != st["layer"]:
                assert min(prev["squash"], st["squash"]) < 0.3, (who, tt, prev["squash"], st["squash"])
                say("MEASURED switch: cow.%s goes from the hill pass to the strip pass at %.2f, edge-on (width %.0f%%)" % (who, T0 + tt, 100 * st["squash"]))
            prev = st
    prev = None
    for tt in frames:
        st = calf_state(tt)
        if prev and prev["layer"] != st["layer"]:
            assert min(prev.get("squash", 1), st.get("squash", 1)) < 0.3
            say("MEASURED switch: the calf goes from the hill pass to the strip pass at %.2f, edge-on" % (T0 + tt))
        prev = st
    for tb, xb in BREACHES:
        # the frame it lands (front pass -> board pass): it must not be under anything in the board pass
        tl = {T_B1: T_L1, T_B2: T_L2, T_B3: T_L3, T_B4: T_L4}[tb]
        k = int(math.ceil(tl * FPS - 1e-9))
        ink, stg = _render(k / FPS, record=True)
        assert "dog" in stg.mattes and dict((n, s) for s, n in stg.order)["dog"] == "sill"
        order = [n for s, n in stg.order if s == "sill"]
        later = order[order.index("dog") + 1:]
        hidden = sum(_overlap(stg.mattes["dog"], stg.mattes[n]) for n in later)
        assert hidden == 0, (tb, later, hidden)
        # the frame it comes through the line: the holdout cuts it exactly in two
        k2 = int(round((tb + 0.04) * FPS))
        ink, stg2 = _render(k2 / FPS, record=True)
        if "split" in stg2.cache and stg2.cache["split"][0] is not None and stg2.cache["split"][1] is not None:
            at, ab = stg2.cache["split"]
            layer, _ = _dog_layer(dog_state(k2 / FPS), camera(k2 / FPS))
            full = np.asarray(layer.getchannel("A"), np.int32)
            ls = at.size[1]
            assert np.array_equal(np.asarray(at, np.int32), full[:ls]) and np.abs(np.asarray(ab, np.int32) - (full[ls:] * 0.86).astype(np.int32)).max() <= 1
    say("MEASURED switch: at each of the four landings the dog enters the board pass as its top cel (0 px of it under anything);"
        " at each breach the water-line holdout cuts its alpha in two with no gap and no double cover")
    # 11 · contact: paws on the board, hooves on the strip
    drift = 0.0
    for tt in (2.2, 3.5, 4.6, 6.5, 8.1, 13.3, 13.8, 17.6, 24.0, 25.9):
        st = dog_state(tt)
        j = _dog_points(int(round(tt * FPS)))
        low = max(j[k][1] for k in ("fn.paw", "ff.paw", "hn.paw", "hf.paw"))
        drift = max(drift, abs(low - SILL_Y))
        assert abs(low - SILL_Y) < 2.5, (tt, low)
    for who in ("second", "mother"):
        st = cow_state(who, 12.0 if who == "second" else 25.0)
        a = herd.anchors(who, st["pose"], st["x"], st["y"], st["s"], st["facing"], 0)
        hy = max(p[1] for p in a["hooves"].values())
        assert abs(hy - STRIP_Y) < 1.5, (who, hy)
    say("MEASURED contact: the dog's lowest paw is within %.1f px of the board (y 394) in every standing sample; drinking cows' hooves on y 388" % drift)
    # 12 · the pile at the end is props.pile's pile, and my holes are town's holes
    a = kit.Ink(26.0, 624)
    a.paper()
    b = kit.Ink(26.0, 624)
    b.paper()
    props.pile(a, 26.0, PILE_X, 392.0, 5, s=DS, born=LAID, edge=EDGE_Y, floor=FLOOR_Y)
    _pile_puddle(b, 26.0, 0)
    for k in range(5):
        _pile_item(b, 26.0, 0, k)
    diff = np.abs(np.asarray(a.img.convert("RGB"), np.int32) - np.asarray(b.img.convert("RGB"), np.int32)).max()
    assert diff <= 2, ("pile differs from props.pile", diff)
    a = kit.Ink(0, 0)
    a.paper((90, 110, 100))
    b = kit.Ink(0, 0)
    b.paper((90, 110, 100))
    cam = town.Cam(oy=335)
    town.dig_holes(a, cam, 7)
    town.dig_holes(b, cam, 3)
    for q in sorted((3, 4, 5, 6), key=lambda q: town.HOLES[q][1]):
        _hole(b, cam, q, 1.0)
    diff2 = np.abs(np.asarray(a.img.convert("RGB"), np.int32) - np.asarray(b.img.convert("RGB"), np.int32))
    assert (diff2.max(axis=2) > 2).sum() < 40, ("holes differ from town.dig_holes(7)", int((diff2.max(axis=2) > 2).sum()))
    say("MEASURED handover: the pile at 84.0 is pixel for pixel props.pile(5 things); holes 0..6 are town.dig_holes(7) (%d px differ, where pits overlap)"
        % int((diff2.max(axis=2) > 2).sum()))
    return out


# ====================================================================== #
#  11 · ALONE                                                             #
# ====================================================================== #

def _sheet(times, path, cols=4, scale=0.5, crop=None):
    ims = []
    for t in times:
        ink = kit.Ink(t, int(round(t * FPS)))
        ink.paper()
        draw(t, ink)
        im = ink.finish()
        if crop:
            im = im.crop(crop)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 58, 13], fill=(0, 0, 0))
        d.text((3, 1), "%.2f" % t, fill=(255, 255, 255))            # on the contact sheet only, never in the film
        ims.append(im)
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 24))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


SHEETS = {
    "a_up": [0.0, 0.3, 0.6, 0.9, 1.1, 1.2, 1.3, 1.45, 1.6, 1.75, 1.9, 2.1, 2.3, 2.5, 2.7, 2.85],
    "b_page": [3.0, 3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.2, 5.4, 5.6, 5.8, 6.0],
    "c_ask": [6.3, 6.7, 6.9, 7.1, 7.3, 7.45, 7.6, 7.75, 7.9, 8.1, 8.3, 8.5, 8.7, 8.9, 9.05, 9.2],
    "d_round2": [9.3, 9.45, 9.7, 10.0, 10.3, 10.5, 10.8, 11.0, 11.3, 11.6, 11.8, 12.1, 12.4, 12.62, 12.75, 12.9],
    "e_reel": [13.02, 13.15, 13.3, 13.5, 13.7, 13.9, 14.05, 14.2, 14.35, 14.5, 14.65, 14.8, 14.95, 15.1, 15.24, 15.4],
    "f_round3": [15.6, 15.86, 16.1, 16.36, 16.6, 16.85, 17.04, 17.2, 17.38, 17.5, 17.62, 17.74, 17.84, 17.86, 17.96, 18.1],
    "g_calf": [18.25, 18.4, 18.55, 18.7, 18.86, 19.0, 19.15, 19.3, 19.45, 19.6, 19.75, 19.9, 20.05, 20.2, 20.35, 20.5],
    "h_lick": [20.65, 20.8, 20.95, 21.05, 21.15, 21.25, 21.3, 21.45, 21.6, 21.8, 22.0, 22.16, 22.3, 22.5, 22.72, 22.85],
    "i_quiet": [22.95, 23.06, 23.2, 23.35, 23.5, 23.7, 23.9, 24.1, 24.3, 24.6, 24.8, 25.0, 25.3, 25.6, 25.9, 26.0],
}


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check(pixels="--fast" not in args)
        print("ok")
        return
    out = HERE.parent.parent / "stills" / "dogs-s3"
    if args and args[0] == "--sheets":
        only = args[1:]
        for name, ts in SHEETS.items():
            if only and name[0] not in only:
                continue
            print(_sheet(ts, out / ("sheet_%s.png" % name)))
        return
    film = kit.Film("dogs-s3", SECONDS)
    film.poster_at = 19.7
    film.picture(lambda t, ink: draw(t, ink))
    film.sound(lambda mix: sound(mix, 0.0))
    if args and args[0] == "--stills":
        film.render(preview=[float(x) for x in args[1:]] or [0.0, 1.2, 2.2, 4.4, 6.2, 8.2, 11.4, 13.6, 17.5, 19.6, 21.0, 26.0])
        return
    check(verbose=True, pixels=False)
    film.render()


if __name__ == "__main__":
    main()
