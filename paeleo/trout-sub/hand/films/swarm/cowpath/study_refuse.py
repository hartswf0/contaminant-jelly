"""STUDY (SCION law 3, animation-48 hard proof): a character that can refuse.

In the river of films/swarm/c13/world.py a builder trout brings a piece of work (a slab on a pier, one span
of the road) to a watching trout that built nothing. The watcher chooses among WATCH, APPROACH, INSPECT,
REFUSE and PASS. It refuses the first piece (the slab rocks when nudged, because the pier is one stone
short) by putting its body in the way. The builder tries over, tries under, stops, turns round, fetches
the stone it left on the bed, wedges it in, and is passed.

Nothing in the picture is keyed by hand. The film is a recording of a simulation: two finite-state
machines (and three two-state onlookers) stepped 24 times a second against persistent world data. The
picture and the sound are both drawn from the recorded run.

    python3 films/swarm/cowpath/study_refuse.py              -> assets/films/cowpath-study-refuse.mp4
    python3 films/swarm/cowpath/study_refuse.py --check      -> model-based tests and measured invariants
    python3 films/swarm/cowpath/study_refuse.py --trace      -> the decision trace of every character
    python3 films/swarm/cowpath/study_refuse.py --chart      -> the state charts as text
    python3 films/swarm/cowpath/study_refuse.py --sheet OUT.png [t0 t1]   -> 16-still contact sheet

The native primitives of animation-48 are kept as data, by name:
    State, Guard, Transition (with .priority), ActionWindow, Intention, WorldData (persistent), Memory.
Importing this module renders nothing and simulates nothing until `simulate()` or `the_run()` is called.
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
FILMS = HERE.parent.parent
for _p in (str(FILMS), str(HERE), str(HERE.parent / "c13")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from PIL import Image, ImageDraw

import kit
from kit import Film, Mix, clamp, lerp, smooth, mix_color
import world as w

W, H, FPS = kit.W, kit.H, kit.FPS
SLUG = "cowpath-study-refuse"
SECONDS = 12.0
DT = 1.0 / FPS

# ----------------------------------------------------------------- the board's Act 3 layout ---

SURFACE = 170            # water surface (y)
BED = 480                # where stones stand on the gravel
LEFT, RIGHT = 180, 780   # the banks
LANE_W = 100
SLAB_T = 20              # slab thickness; slab top lies at SURFACE
SLAB_BOTTOM = SURFACE + SLAB_T
LANE = 4                 # the hasty builder's lane
SCALE = dict(D4=293.7, E4=329.6, Fs4=370.0, A4=440.0, B4=493.9, D5=587.3)
LANE_PITCH = {1: 293.7, 2: 329.6, 3: 370.0, 4: 440.0, 5: 493.9, 6: 587.3}

ROCK_LIMIT = 1.5         # degrees: a slab that tips further than this when nudged is refused


def lane_cx(i):
    return LEFT + LANE_W * (i - 0.5)


# =============================================================== native primitives (animation-48) ===

@dataclass(frozen=True)
class ActionWindow:
    """How long a state's action must run before a guarded exit may be taken (commitment), in frames."""
    min_frames: int = 0


@dataclass(frozen=True)
class Intention:
    """What the character wants while in a state. Recorded in the decision trace; it is why a part moves."""
    want: str


@dataclass(frozen=True)
class State:
    name: str
    intention: Intention
    window: ActionWindow = ActionWindow()
    terminal: bool = False          # a declared resting end; any other state without an exit is a fault


@dataclass(frozen=True)
class Guard:
    """A named condition on what the character perceives and remembers. test(see, mem) -> (bool, evidence)."""
    name: str
    test: Callable


@dataclass(frozen=True)
class Transition:
    src: str
    dst: str
    guard: Guard
    priority: int = 1               # lower fires first when two guards hold on the same frame
    interrupt: bool = False         # may cut the action window short


@dataclass
class Memory:
    """What a character keeps between states. Plain data, printed in the trace."""
    data: dict = field(default_factory=dict)

    def __getitem__(self, k):
        return self.data[k]

    def __setitem__(self, k, v):
        self.data[k] = v

    def get(self, k, d=None):
        return self.data.get(k, d)


class Machine:
    """A finite-state machine. One step = perceive (done by the caller), then take the first transition,
    in priority order, whose guard holds and whose action window allows it."""

    def __init__(self, name, states, transitions, start, memory=None):
        self.name = name
        self.states = {s.name: s for s in states}
        self.transitions = sorted(transitions, key=lambda tr: tr.priority)
        self.start = start
        self.state = start
        self.since = 0
        self.memory = memory or Memory()
        self.visited = {start}
        self.fired = set()
        self.entries = {start: 1}

    def age(self, frame):
        return frame - self.since

    def step(self, frame, see, trace):
        st = self.states[self.state]
        for tr in self.transitions:
            if tr.src != self.state:
                continue
            if not tr.interrupt and self.age(frame) < st.window.min_frames:
                continue
            ok, ev = tr.guard.test(see, self.memory)
            if ok:
                trace.append(dict(frame=frame, t=round(frame * DT, 3), who=self.name, src=tr.src, dst=tr.dst,
                                  guard=tr.guard.name, priority=tr.priority, evidence=ev,
                                  want=self.states[tr.dst].intention.want))
                self.fired.add((tr.src, tr.dst, tr.guard.name))
                self.state = tr.dst
                self.since = frame
                self.visited.add(tr.dst)
                self.entries[tr.dst] = self.entries.get(tr.dst, 0) + 1
                return tr
        return None

    # -- model-based checks on the graph itself
    def reachable(self):
        seen, todo = {self.start}, [self.start]
        while todo:
            s = todo.pop()
            for tr in self.transitions:
                if tr.src == s and tr.dst not in seen:
                    seen.add(tr.dst)
                    todo.append(tr.dst)
        return seen

    def absorbing(self):
        """States with no way out that were not declared terminal."""
        outs = {tr.src for tr in self.transitions}
        return [s for s, st in self.states.items() if s not in outs and not st.terminal]

    def chart(self):
        lines = [f"{self.name}: start {self.start}"]
        for s, st in self.states.items():
            lines.append(f"  [{s}] wants: {st.intention.want}" + (f" (window >= {st.window.min_frames} fr)" if st.window.min_frames else "")
                         + (" TERMINAL" if st.terminal else ""))
            for tr in self.transitions:
                if tr.src == s:
                    lines.append(f"      -> {tr.dst:<10} if {tr.guard.name}  (priority {tr.priority}{', interrupt' if tr.interrupt else ''})")
        return "\n".join(lines)


# ====================================================================== persistent world data ===

@dataclass
class Stone:
    id: str
    x: float
    y: float           # centre
    w: float
    h: float
    seed: int = 0
    where: str = "pier"     # 'pier' | 'bed' | 'carried'
    tilt: float = 0.0


@dataclass
class Piece:
    """A piece of work: one span of the road, a slab on a pier of stones. Persistent."""
    lane: int
    stones: list            # the pier, bottom to top
    x: float = 0.0          # slab centre
    y: float = 0.0
    set: bool = False
    rev: int = 0            # goes up every time the builder changes the piece
    theta: float = 0.0      # degrees, + = right end up (counter-clockwise on screen)
    omega: float = 0.0
    peak: float = 0.0       # largest excursion from rest since the last nudge
    nudged_at: int = -999
    nudges: int = 0
    pebble_out: bool = False

    @property
    def seat(self):
        return (lane_cx(self.lane), SURFACE + SLAB_T / 2)

    def pier_top(self):
        return BED - sum(s.h for s in self.stones)

    def gap(self):
        """Daylight between the top of the pier and the underside of the slab, px."""
        return self.pier_top() - SLAB_BOTTOM

    def supported(self):
        return self.gap() < 2.0

    def rest(self):
        return 0.0 if self.supported() else -2.2      # an unsupported slab hangs a little crooked


@dataclass
class WorldData:
    pieces: dict
    loose: list                      # stones lying on the bed or in a mouth
    pebbles: list = field(default_factory=list)
    events: list = field(default_factory=list)       # (frame, kind, dict): contacts, for sound and for tests
    frame: int = 0

    def emit(self, kind, **kw):
        self.events.append((self.frame, kind, kw))

    def nudge(self, piece, x, strength=1.0):
        """A nose pushes up on the slab at x. What the slab then does depends only on what is under it."""
        arm = (x - piece.x) / (LANE_W / 2)
        if piece.supported():
            piece.omega += 40.0 * strength * arm
        else:
            piece.omega += 165.0 * strength * arm
        piece.peak = 0.0
        piece.nudged_at = self.frame
        piece.nudges += 1
        piece.pebble_out = False
        self.emit("nudge", lane=piece.lane, x=x, supported=piece.supported(), n=piece.nudges)

    def step(self):
        for p in self.pieces.values():
            if not p.set:
                continue
            f, zeta = (10.0, 0.6) if p.supported() else (2.0, 0.14)
            om = 2 * math.pi * f
            prev = p.theta - p.rest()
            for _ in range(8):
                h = DT / 8
                p.omega += (-om * om * (p.theta - p.rest()) - 2 * zeta * om * p.omega) * h
                p.theta += p.omega * h
            dev = p.theta - p.rest()
            p.peak = max(p.peak, abs(dev))
            if not p.supported() and self.frame - p.nudged_at < 40:
                if prev * dev < 0 and abs(p.omega) > 25 and self.frame > p.nudged_at:          # passes level, going fast: it knocks
                    self.emit("clack", lane=p.lane, x=p.x, speed=abs(p.omega))
                if not p.pebble_out and abs(dev) > 4.5:
                    p.pebble_out = True
                    self.pebbles.append(dict(x=p.x + LANE_W / 2 - 3, y=SLAB_BOTTOM + 3, vx=-14.0, vy=10.0, rest=False))
                    self.emit("pebble", x=p.x + LANE_W / 2 - 3)
        for b in self.pebbles:
            if b["rest"]:
                continue
            b["vy"] = min(b["vy"] + 520 * DT, 210.0)
            b["vx"] *= 0.97
            b["x"] += b["vx"] * DT
            b["y"] += b["vy"] * DT
            if b["y"] >= BED - 6:
                b["y"] = BED - 6
                b["rest"] = True
                self.emit("pebble_land", x=b["x"])


def make_world(short=True, loose_stone=True):
    """The road with lane 4 not yet laid. short=True: pier 4 is two stones and 34 px short."""
    rs = random.Random(48)
    pieces = {}
    for lane in range(1, 7):
        cx = lane_cx(lane)
        if lane == LANE and short:
            hs = [130.0, 126.0]
            ws = [46.0, 42.0]
        else:
            a, b = rs.uniform(92, 104), rs.uniform(90, 102)
            hs = [a, b, 290.0 - a - b]
            ws = [rs.uniform(54, 62), rs.uniform(48, 58), rs.uniform(46, 54)]
        stones, y = [], BED
        for k, (hh, ww) in enumerate(zip(hs, ws)):
            stones.append(Stone(f"p{lane}s{k}", cx + rs.uniform(-3, 3), y - hh / 2, ww, hh, seed=lane * 10 + k, tilt=rs.uniform(-3, 3)))
            y -= hh
        p = Piece(lane, stones)
        p.x, p.y = p.seat
        p.set = lane != LANE
        p.rev = 1 if p.set else 0
        pieces[lane] = p
    loose = [Stone("dropped", 318.0, BED - 16.0, 56.0, 34.0, seed=77, where="bed", tilt=-4.0)] if (short and loose_stone) else []
    return WorldData(pieces, loose)


# ============================================================================ bodies (locomotion) ===

@dataclass
class Body:
    name: str
    x: float
    y: float
    length: float
    facing: int = 1            # +1 looks right
    pitch: float = 0.0         # degrees, + = nose up, measured in the fish's own facing
    vx: float = 0.0
    vy: float = 0.0
    lid: float = 0.0
    amp: float = 8.0
    phase: float = 0.0
    flip_k: int = -1           # frames into a paper flip (turning round), -1 = not flipping
    flip_n: int = 9
    flip_face0: int = 1

    @property
    def half(self):
        return self.length * 0.5

    @property
    def radius(self):
        return self.length * 0.105

    def s(self):
        """Signed width while turning: 1 = full, 0 = edge on, -1 = turned round."""
        if self.flip_k < 0:
            return 1.0
        return math.cos(math.pi * clamp(self.flip_k / self.flip_n))

    def face_drawn(self):
        if self.flip_k < 0:
            return self.facing
        return self.flip_face0 if self.s() >= 0 else -self.flip_face0

    def wide(self):
        return max(0.07, abs(self.s()))

    def axis(self):
        """Unit vector tail -> nose on screen, foreshortened while turning."""
        if self.flip_k < 0:
            f, s = self.facing, 1.0
        else:
            f, s = self.flip_face0, self.s()
        a = math.radians(self.pitch)
        return (f * s * math.cos(a), -math.sin(a))

    def nose(self, beyond=0.0):
        ax, ay = self.axis()
        return (self.x + ax * (self.half + beyond), self.y + ay * (self.half + beyond))

    def tail(self):
        ax, ay = self.axis()
        return (self.x - ax * self.half, self.y - ay * self.half)

    def start_flip(self, n=9):
        self.flip_k, self.flip_n, self.flip_face0 = 0, n, self.facing

    def speed(self):
        return math.hypot(self.vx, self.vy)


@dataclass
class Drive:
    """What a state asks of the body this frame. The body gets there under its own limits."""
    target: tuple
    speed: float = 150.0
    accel: float = 700.0
    pitch: Optional[float] = None      # None = point along the velocity
    pitch_rate: float = 260.0
    amp: float = 8.0
    lid: Optional[float] = None
    gain: float = 5.0                  # arrival: speed falls off inside speed/gain px of the target


def steer(b: Body, d: Drive):
    """Advance one frame. Speed, acceleration and turn rate are limited, so motion is continuous by construction."""
    for _ in range(2):
        h = DT / 2
        dx, dy = d.target[0] - b.x, d.target[1] - b.y
        dist = math.hypot(dx, dy)
        vdes = min(d.speed, dist * d.gain)
        ux, uy = (dx / dist, dy / dist) if dist > 1e-6 else (0.0, 0.0)
        ax, ay = ux * vdes - b.vx, uy * vdes - b.vy
        am = math.hypot(ax, ay)
        lim = d.accel * h
        if am > lim:
            ax, ay = ax / am * lim, ay / am * lim
        b.vx += ax
        b.vy += ay
        b.x += b.vx * h
        b.y += b.vy * h
    if d.pitch is not None:
        pt = d.pitch
    elif b.speed() > 24 and b.vx * b.facing > 0:
        pt = clamp(math.degrees(math.atan2(-b.vy, b.vx * b.facing)), -75, 75)
    elif b.speed() > 24:
        pt = clamp(-b.vy * 0.4, -60, 60)
    else:
        pt = b.pitch * 0.9
    step = d.pitch_rate * DT
    b.pitch += clamp(pt - b.pitch, -step, step)
    b.amp += (d.amp - b.amp) * 0.25
    if d.lid is not None:
        b.lid += clamp(d.lid - b.lid, -0.09, 0.09)
    b.phase += (3.0 + 11.0 * clamp(b.speed() / 230.0)) * DT * (1.0 if b.amp > 0.6 else 0.0)
    if b.flip_k >= 0:
        b.flip_k += 1
        if b.flip_k * 2 >= b.flip_n and b.facing == b.flip_face0:
            b.facing = -b.flip_face0
        if b.flip_k >= b.flip_n:
            b.flip_k = -1


def seg_dist(p1, p2, q1, q2):
    """Smallest distance between two segments (sampled; good to a pixel)."""
    best = 1e9
    for i in range(13):
        a = (lerp(p1[0], p2[0], i / 12), lerp(p1[1], p2[1], i / 12))
        vx, vy = q2[0] - q1[0], q2[1] - q1[1]
        L = vx * vx + vy * vy
        u = clamp(((a[0] - q1[0]) * vx + (a[1] - q1[1]) * vy) / L) if L > 0 else 0
        best = min(best, math.hypot(a[0] - q1[0] - u * vx, a[1] - q1[1] - u * vy))
    return best


def clearance(a: Body, b: Body):
    """Water between two fish (body capsules, fins not counted), px. Negative = they overlap."""
    def core(f):
        n, t = f.nose(-f.half * 0.14), f.tail()
        t = (lerp(t[0], f.x, 0.2), lerp(t[1], f.y, 0.2))
        return n, t
    return seg_dist(*core(a), *core(b)) - a.radius - b.radius


def flank_x(gate: Body, y, margin=0.0):
    """The x of a fish's left side at height y, or None where its body does not reach. What a blocked fish sees."""
    n, t = gate.nose(), gate.tail()
    lo, hi = min(n[1], t[1]) - gate.radius, max(n[1], t[1]) + gate.radius
    if y < lo - margin or y > hi + margin:
        return None
    if abs(n[1] - t[1]) < 1e-3:
        return min(n[0], t[0])
    u = clamp((y - t[1]) / (n[1] - t[1]))
    return lerp(t[0], n[0], u) - gate.radius * 1.15


# ===================================================================== the two characters ===

P_GATE = 72.0                               # the watcher's nose-up pitch when inspecting and when in the way
NUDGE_X = lane_cx(LANE) + LANE_W / 2 - 4    # it tests the end of the slab
_GA = math.radians(P_GATE)
CONTACT = (NUDGE_X - 85 * math.cos(_GA), SLAB_BOTTOM + 85 * math.sin(_GA))      # watcher centre when its nose touches
STATION = (CONTACT[0], CONTACT[1] + 26)
GATE_Y = (STATION[1] - 8, 392.0)            # how far it will rise and sink to stay in the way
LOW = (528.0, 438.0)                        # where it lies after it has passed a piece: out of the way
HOVER1 = (392.0, 364.0)                     # where the builder waits the first time (not for long)
HOVER2 = (432.0, 268.0)                     # and the second time (it has learned to wait)
SCHOOL = (706.0, 286.0)                     # the builder's place in the school
CARRY_PITCH = 64.0
SLAB_ON_NOSE = (6.0, -11.0)                 # slab centre relative to the carrying nose
STONE_AHEAD = 20.0
TRY_Y = (226.0, 392.0)                     # how high and how low it goes looking for a way round
STOP_Y = 392.0                              # where it comes to rest, nose to flank, in open water
HOLD_FRAMES = 24                            # how long the builder is stopped dead before it turns back: one second                          # a carried stone rides this far ahead of the nose


def _watcher_machine():
    S = [State("WATCH", Intention("know whether each piece will bear weight; keep still until one is offered"), ActionWindow(5)),
         State("APPROACH", Intention("get under the offered slab")),
         State("INSPECT", Intention("push the slab once from below and feel what it does"), ActionWindow(0)),
         State("REFUSE", Intention("stay between the builder and the school until the piece is changed")),
         State("PASS", Intention("say yes once, with the eye, and get out of the way"), ActionWindow(6))]
    G = dict(
        offered=Guard("a piece is set that I have not judged at this revision, and its builder has let go of it",
                      lambda see, m: (see["piece_set"] and m.get("judged_rev") != see["piece_rev"] and see["builder_off"] > 76,
                                      dict(piece_rev=see["piece_rev"], judged_rev=m.get("judged_rev"), builder_off=round(see["builder_off"])))),
        at_station=Guard("I am under the slab",
                         lambda see, m: (see["to_station"] < 5.0 and see["my_speed"] < 60, dict(dist=round(see["to_station"], 1)))),
        rocked=Guard(f"after my push the slab tipped more than {ROCK_LIMIT} deg",
                     lambda see, m: (m.get("pushed", False) and see["since_push"] >= 10 and see["peak"] > ROCK_LIMIT,
                                     dict(peak_deg=round(see["peak"], 2), limit=ROCK_LIMIT))),
        firm=Guard(f"after my push the slab stayed within {ROCK_LIMIT} deg",
                   lambda see, m: (m.get("pushed", False) and see["since_push"] >= 10 and see["peak"] <= ROCK_LIMIT,
                                   dict(peak_deg=round(see["peak"], 2), limit=ROCK_LIMIT))),
        changed=Guard("the piece is not the one I refused (its revision changed)",
                      lambda see, m: (see["piece_rev"] != m.get("judged_rev"), dict(piece_rev=see["piece_rev"], judged_rev=m.get("judged_rev")))),
        gone_by=Guard("the builder has gone by",
                      lambda see, m: (see["builder_x"] > see["my_x"] + 70, dict(builder_x=round(see["builder_x"])))),
    )
    T = [Transition("WATCH", "APPROACH", G["offered"]),
         Transition("APPROACH", "INSPECT", G["at_station"]),
         Transition("INSPECT", "REFUSE", G["rocked"], priority=0),
         Transition("INSPECT", "PASS", G["firm"], priority=1),
         Transition("REFUSE", "INSPECT", G["changed"]),
         Transition("PASS", "WATCH", G["gone_by"])]
    return Machine("watcher", S, T, "WATCH", Memory(dict(judged_rev=None, refusals=0, passes=0, pushed=False)))


def _builder_machine(will_repair=True):
    S = [State("CARRY", Intention("get my slab into the road")),
         State("PRESENT", Intention("be told it is done"), ActionWindow(16)),
         State("LEAVE", Intention("join the school at the far bank")),
         State("TRY_OVER", Intention("get past, over the top"), ActionWindow(9)),
         State("TRY_UNDER", Intention("get past, underneath"), ActionWindow(9)),
         State("STOPPED", Intention("nothing: there is no way past"), ActionWindow(8)),
         State("TURN_BACK", Intention("go back for the stone I left"), ActionWindow(8)),
         State("FETCH", Intention("get the stone off the bed")),
         State("TURN_FWD", Intention("face the pier again, stone in mouth"), ActionWindow(8)),
         State("REPAIR", Intention("wedge the stone under my slab")),
         State("JOINED", Intention("be one of the school"), terminal=True)]
    G = dict(
        seated=Guard("my slab is in its seat", lambda see, m: (see["slab_to_seat"] < 2.5, dict(dist=round(see["slab_to_seat"], 1)))),
        thinks_done=Guard("I think it is done (first time: it has been touched; after a refusal: the watcher's eye opened and the way is clear)",
                          lambda see, m: ((see["my_piece_nudges"] > m.get("nudges_at_present", 0) and see["frames_since_nudge"] >= 12)
                                          if m.get("refused", 0) == 0 else (m.get("saw_yes", False) and not see["barred"]),
                                          dict(refused=m.get("refused", 0), nudges=see["my_piece_nudges"], saw_yes=m.get("saw_yes", False),
                                               barred=see["barred"]))),
        blocked=Guard("a body is across my way", lambda see, m: (see["blocked"], dict(flank_x=see["flank"]))),
        still_blocked=Guard("I got to that height and there is still no way through", lambda see, m: (see["barred"] and see["try_done"], dict(flank_x=see["flank"], tries=list(m.get("tries", []))))),
        way_open=Guard("the way is open", lambda see, m: (not see["barred"], {})),
        in_school=Guard("I am with the others", lambda see, m: (see["to_school"] < 26, dict(dist=round(see["to_school"])))),
        knows_fault=Guard("I tried both ways, I am still stopped, and I remember the stone I dropped",
                          lambda see, m: (will_repair and see["barred"] and len(m.get("tries", [])) >= 2 and see["stone_on_bed"]
                                          and see["still_frames"] >= HOLD_FRAMES,
                                          dict(tries=list(m.get("tries", [])), stone_on_bed=see["stone_on_bed"], still_frames=see["still_frames"]))),
        turned=Guard("I have turned round", lambda see, m: (not see["flipping"], {})),
        has_stone=Guard("my nose is on the stone", lambda see, m: (see["nose_to_stone"] < 9.0, dict(dist=round(see["nose_to_stone"], 1)))),
        wedged=Guard("the stone is in the gap", lambda see, m: (see["stone_to_slot"] < 4.0, dict(dist=round(see["stone_to_slot"], 1)))),
    )
    T = [Transition("CARRY", "PRESENT", G["seated"]),
         Transition("PRESENT", "LEAVE", G["thinks_done"]),
         Transition("LEAVE", "JOINED", G["in_school"], priority=0),
         Transition("LEAVE", "TRY_OVER", G["blocked"], priority=1),
         Transition("TRY_OVER", "LEAVE", G["way_open"], priority=0, interrupt=True),
         Transition("TRY_OVER", "TRY_UNDER", G["still_blocked"], priority=1),
         Transition("TRY_UNDER", "LEAVE", G["way_open"], priority=0, interrupt=True),
         Transition("TRY_UNDER", "STOPPED", G["still_blocked"], priority=1),
         Transition("STOPPED", "LEAVE", G["way_open"], priority=0, interrupt=True),
         Transition("STOPPED", "TURN_BACK", G["knows_fault"], priority=1),
         Transition("TURN_BACK", "FETCH", G["turned"]),
         Transition("FETCH", "TURN_FWD", G["has_stone"]),
         Transition("TURN_FWD", "REPAIR", G["turned"]),
         Transition("REPAIR", "PRESENT", G["wedged"])]
    return Machine("builder", S, T, "CARRY", Memory(dict(refused=0, tries=[], saw_yes=False, nudges_at_present=0)))


def _onlooker_machine(k):
    S = [State("AHEAD", Intention("wait to go on")),
         State("LOOK_BACK", Intention("see what is holding number four up"), ActionWindow(18))]
    T = [Transition("AHEAD", "LOOK_BACK", Guard("the builder has been held up for a while",
                                                lambda see, m: (see["standoff"] > 5 + 8 * k, dict(frames=see["standoff"])))),
         Transition("LOOK_BACK", "AHEAD", Guard("the builder is through",
                                                lambda see, m: (see["through"] > 3 + 6 * (2 - k), dict(frames=see["through"]))))]
    return Machine(f"onlooker{k + 1}", S, T, "AHEAD")


# ================================================================================ simulation ===

@dataclass
class Run:
    scenario: str
    frames: list            # one snapshot dict per frame
    trace: list             # every transition taken, with the evidence its guard saw
    events: list            # contacts in the world: (frame, kind, dict)
    machines: dict
    world: WorldData

    def at(self, t):
        return self.frames[int(clamp(round(t * FPS), 0, len(self.frames) - 1))]

    def when(self, who, dst, nth=1):
        """Time of the nth entry of `who` into state `dst`, or None."""
        k = 0
        for d in self.trace:
            if d["who"] == who and d["dst"] == dst:
                k += 1
                if k == nth:
                    return d["t"]
        return None

    def event_times(self, kind):
        return [f * DT for f, k, _ in self.events if k == kind]


def _snap_body(b: Body):
    return dict(x=b.x, y=b.y, pitch=b.pitch, face=b.face_drawn(), wide=b.wide(), length=b.length, lid=b.lid, amp=b.amp,
                phase=b.phase, nose=b.nose(), tail=b.tail(), flipping=b.flip_k >= 0)


def simulate(scenario="short", seconds=SECONDS):
    """Run the scene and record it. scenario:
         'short'    the film: pier one stone short, the stone lying on the bed
         'firm'     the same builder with a whole pier (the watcher must pass it at once)
         'stubborn' the pier short and no stone to fetch (waiting must never buy the pass)
         'helped'   as 'stubborn', but at 7 s somebody else wedges the pier (the pass follows the piece)
    Returns a Run. Deterministic: same arguments, same run."""
    world = make_world(short=scenario != "firm", loose_stone=scenario == "short")
    help_at = int(7.0 * FPS) if scenario == "helped" else -1
    piece = world.pieces[LANE]
    wm, bm = _watcher_machine(), _builder_machine(will_repair=True)
    lookers = [_onlooker_machine(k) for k in range(3)]
    wb = Body("watcher", 336.0, 236.0, 170.0, lid=0.45, amp=2.0)
    bb = Body("builder", 452.0, 376.0, 118.0, lid=0.0, amp=10.0, pitch=CARRY_PITCH)
    lb = [Body(f"onlooker{k + 1}", x, y, L, amp=4.0, phase=k * 1.7) for k, (x, y, L) in
          enumerate(((716.0, 338.0, 112.0), (694.0, 384.0, 122.0), (720.0, 428.0, 116.0)))]
    stone = world.loose[0] if world.loose else None
    carried_slab, carried_stone = True, False
    stone_lerp = 0.0
    piece.x, piece.y = bb.nose()[0] + SLAB_ON_NOSE[0], bb.nose()[1] + SLAB_ON_NOSE[1]
    trace, frames = [], []
    n = int(round(seconds * FPS))
    twirl_at = None
    still = 0
    held = thru = 0
    for k in range(n):
        world.frame = k
        # ------------------------------------------------ perceive (only what each could see or feel)
        flank = None
        for yy in (bb.y - 14, bb.y, bb.y + 14, bb.nose()[1], (bb.y + bb.nose()[1]) / 2):
            fx = flank_x(wb, yy)
            if fx is not None:
                flank = fx if flank is None else min(flank, fx)
        goal_x = SCHOOL[0]
        barred = flank is not None and bb.x < wb.x and flank < goal_x                 # a body reaches across my height
        blocked = barred and bb.nose()[0] > flank - 30                                # ... and I am up against it
        slot = (lane_cx(LANE), SLAB_BOTTOM + piece.gap() / 2 + 0.0)
        see_w = dict(piece_set=piece.set, piece_rev=piece.rev, to_station=math.hypot(wb.x - STATION[0], wb.y - STATION[1]),
                     my_speed=wb.speed(), my_x=wb.x, peak=piece.peak, since_push=k - piece.nudged_at, builder_x=bb.x,
                     builder_off=math.hypot(bb.nose()[0] - piece.seat[0], bb.nose()[1] - piece.seat[1]))
        still = still + 1 if (bm.state == "STOPPED" and bb.speed() < 16.0 and abs(bb.y - STOP_Y) < 12) else 0
        if still == 5:                                   # it lets its breath go: the only thing that moves in the hold
            world.emit("sigh", x=bb.nose()[0] + 4, y=bb.nose()[1] - 4)
        if k == help_at:                                 # somebody else puts the piece right
            gap = piece.gap()
            piece.stones.append(Stone("helped", lane_cx(LANE), SLAB_BOTTOM + gap / 2, 56.0, gap, seed=78))
            piece.rev += 1
            world.emit("wedge", lane=LANE, x=piece.x, gap=round(piece.gap(), 1))
        try_y = {"TRY_OVER": TRY_Y[0], "TRY_UNDER": TRY_Y[1]}.get(bm.state)
        see_b = dict(still_frames=still, try_done=try_y is not None and abs(bb.y - try_y) < 14 and bb.speed() < 130, slab_to_seat=math.hypot(piece.x - piece.seat[0], piece.y - piece.seat[1]) if carried_slab else 0.0,
                     my_piece_nudges=piece.nudges, frames_since_nudge=k - piece.nudged_at, blocked=blocked, barred=barred,
                     flank=None if flank is None else round(flank, 1),
                     to_school=math.hypot(bb.x - SCHOOL[0], bb.y - SCHOOL[1]), flipping=bb.flip_k >= 0,
                     stone_on_bed=stone is not None and stone.where == "bed",
                     nose_to_stone=(math.hypot(bb.nose()[0] - (stone.x + stone.w * 0.3), bb.nose()[1] - (stone.y - stone.h * 0.35))
                                    if stone is not None else 1e9),
                     stone_to_slot=math.hypot(stone.x - slot[0], stone.y - slot[1]) if (stone is not None and carried_stone) else 1e9)
        if bm.memory.get("refused", 0) > 0 and bm.state == "PRESENT" and wb.lid < 0.12:
            bm.memory["saw_yes"] = True                 # the only yes there is: the lid lifting
        # ------------------------------------------------ decide
        tr = wm.step(k, see_w, trace)
        if tr:
            if tr.dst == "INSPECT":
                wm.memory["pushed"] = False
            if tr.dst == "REFUSE":
                wm.memory["judged_rev"] = piece.rev
                wm.memory["refusals"] += 1
                bm.memory["refused"] = bm.memory.get("refused", 0)        # the builder does not know yet
            if tr.dst == "PASS":
                wm.memory["judged_rev"] = piece.rev
                wm.memory["passes"] += 1
        tr = bm.step(k, see_b, trace)
        if tr:
            if tr.dst == "PRESENT" and tr.src == "CARRY":
                carried_slab = False
                piece.x, piece.y = piece.seat
                piece.set, piece.rev = True, piece.rev + 1
                piece.theta = piece.rest() + 1.5
                bm.memory["nudges_at_present"] = piece.nudges
                world.emit("set", lane=LANE, x=piece.x)
            if tr.dst == "TRY_OVER":
                bm.memory["tries"] = bm.memory["tries"] + ["over"]
                world.emit("dart", x=bb.x)
            if tr.dst == "TRY_UNDER":
                bm.memory["tries"] = bm.memory["tries"] + ["under"]
                world.emit("dart", x=bb.x)
            if tr.dst == "STOPPED":
                bm.memory["refused"] = bm.memory.get("refused", 0) + 1     # now it knows
                world.emit("stopped", x=bb.x)
            if tr.dst in ("TURN_BACK", "TURN_FWD"):
                bb.start_flip(7)
                world.emit("turn", x=bb.x)
            if tr.dst == "TURN_FWD":
                carried_stone, stone.where, stone_lerp = True, "carried", 0.0
                world.emit("pick", x=stone.x)
            if tr.dst == "PRESENT" and tr.src == "REPAIR":
                carried_stone = False
                stone.where, stone.x, stone.y, stone.tilt = "pier", slot[0], slot[1], 0.0
                world.loose.remove(stone)
                piece.stones.append(stone)
                piece.rev += 1
                piece.omega += 30.0
                bm.memory["nudges_at_present"] = piece.nudges
                bm.memory["saw_yes"] = False
                world.emit("wedge", lane=LANE, x=stone.x, gap=round(piece.gap(), 1))
            if tr.dst == "LEAVE" and tr.src == "PRESENT":
                world.emit("leave", x=bb.x, refused=bm.memory.get("refused", 0))
            if tr.dst == "JOINED":
                world.emit("joined", x=bb.x)
        held = held + 1 if bm.state in ("TRY_OVER", "TRY_UNDER", "STOPPED") else 0
        thru = thru + 1 if bb.x > wb.x + 40 else 0
        see_l = dict(standoff=held, through=thru)
        for m, body in zip(lookers, lb):
            if m.step(k, see_l, trace):
                body.start_flip(8)
        # ------------------------------------------------ act: each state drives its body
        age_w = wm.age(k)
        if wm.state == "WATCH":
            home = (wb.x, wb.y) if wm.memory["passes"] == 0 else LOW
            dw = Drive(home, 40, amp=2.0, pitch=0.0, lid=0.45)
        elif wm.state == "APPROACH":
            d = see_w["to_station"]
            dw = Drive(STATION, 212, accel=800, amp=5.0, pitch=P_GATE * smooth(1 - (d - 6) / 60.0), pitch_rate=170, lid=0.45, gain=5)
        elif wm.state == "INSPECT":
            if not wm.memory["pushed"]:
                dw = Drive((CONTACT[0], CONTACT[1] - 6), 210, accel=1100, amp=5.0, pitch=P_GATE, lid=0.45, gain=9)
                if wb.nose()[1] <= SLAB_BOTTOM + 1.0:
                    world.nudge(piece, wb.nose()[0])
                    wm.memory["pushed"] = True
            else:
                dw = Drive(STATION, 90, accel=500, amp=2.0, pitch=P_GATE, lid=0.45)
        elif wm.state == "REFUSE":
            near = bb.x < wb.x and bb.face_drawn() > 0 and bm.state in ("LEAVE", "TRY_OVER", "TRY_UNDER", "STOPPED")
            gy = clamp(bb.y - 60 + 0.2 * bb.vy, *GATE_Y) if near else STATION[1]     # high enough to shut the top, sinking to shut the bottom
            dw = Drive((STATION[0], gy), 200, accel=600, amp=2.0, pitch=P_GATE, lid=0.45, gain=6)      # same lid, same calm
        else:  # PASS
            if age_w < 5:
                dw = Drive((wb.x, wb.y), 30, amp=2.0, pitch=P_GATE, lid=0.0)
            else:
                dw = Drive(LOW, 230, accel=700, amp=4.0, pitch=0.0, pitch_rate=210, lid=0.0 if age_w < 26 else 0.45, gain=3.5)
        steer(wb, dw)

        age_b = bm.age(k)
        reach = (flank - 12 - bb.half) if flank is not None else 1e9      # as far as its nose can go
        back = min(wb.tail()[0], wb.nose()[0]) - wb.radius - 16 - bb.half   # clear of the whole of the body in the way
        if bm.state == "CARRY":
            a = math.radians(CARRY_PITCH)
            tgt = (piece.seat[0] - SLAB_ON_NOSE[0] - bb.half * math.cos(a), piece.seat[1] - SLAB_ON_NOSE[1] + bb.half * math.sin(a))
            db = Drive(tgt, 165, accel=600, amp=12.0, pitch=CARRY_PITCH, gain=7)
        elif bm.state == "PRESENT":
            if bm.memory.get("refused", 0) == 0:
                db = Drive(HOVER1, 210, accel=700, amp=7.0, pitch=16.0, pitch_rate=200, gain=5)
                if twirl_at is None and math.hypot(bb.x - HOVER1[0], bb.y - HOVER1[1]) < 14:
                    twirl_at = k                        # pleased with itself: a turn right round, on the spot
                    world.emit("twirl", x=bb.x)
                if twirl_at is not None and k in (twirl_at, twirl_at + 7):
                    bb.start_flip(7)
            else:
                db = Drive(HOVER2, 110, accel=400, amp=3.0, pitch=8.0, pitch_rate=160, gain=4)
        elif bm.state == "LEAVE":
            fast = 300 if bm.memory.get("saw_yes") else 180
            ty = SCHOOL[1] if (bm.memory.get("saw_yes") or bb.x > wb.x) else bb.y
            db = Drive((min(SCHOOL[0], reach), ty), fast, accel=700, amp=10.0, gain=5.5)
        elif bm.state == "TRY_OVER":
            db = Drive((min(SCHOOL[0], reach, back + 26), TRY_Y[0]), 300, accel=1500, amp=13.0, gain=6)
        elif bm.state == "TRY_UNDER":
            db = Drive((min(SCHOOL[0], reach, back) if bb.y < 356 else min(SCHOOL[0], reach, back + 20), TRY_Y[1]), 330, accel=1500, amp=13.0, gain=6)
        elif bm.state == "STOPPED":
            settled = math.hypot(bb.x - min(SCHOOL[0], reach), bb.y - STOP_Y) < 7 or still > 0
            db = Drive((min(SCHOOL[0], reach, back) if bb.y > STOP_Y + 40 else min(SCHOOL[0], reach), STOP_Y), 230, accel=800,
                       amp=0.0 if settled else 7.0, pitch=None if not settled else 0.0, pitch_rate=170, gain=7)
        elif bm.state in ("TURN_BACK", "TURN_FWD"):
            db = Drive((bb.x, bb.y), 30, amp=3.0, pitch=bb.pitch)
        elif bm.state == "FETCH":
            tx, ty = stone.x + stone.w * 0.3, stone.y - stone.h * 0.35
            ax, ay = bb.axis()
            db = Drive((tx - ax * bb.half, ty - ay * bb.half), 235, accel=800, amp=11.0, gain=6)
        elif bm.state == "REPAIR":
            ax, ay = bb.axis()
            ext = bb.half + STONE_AHEAD
            d = see_b["stone_to_slot"]
            db = Drive((slot[0] - ext * ax, slot[1] - ext * ay), 240, accel=700, amp=13.0,
                       pitch=lerp(14.0, 62.0, smooth((d - 20) / 90.0)), pitch_rate=170, gain=9)
        else:  # JOINED
            db = Drive(SCHOOL, 80, amp=4.0, pitch=0.0, gain=3)
        steer(bb, db)
        for m, body in zip(lookers, lb):
            steer(body, Drive((body.x, body.y), 20, amp=4.0, pitch=0.0))

        # ------------------------------------------------ attachments, then the world's own physics
        if carried_slab:
            nx, ny = bb.nose()
            piece.x, piece.y = nx + SLAB_ON_NOSE[0], ny + SLAB_ON_NOSE[1]
            piece.theta = 3.0 * math.sin(k * 0.9)
        if carried_stone:
            stone_lerp = min(1.0, stone_lerp + 0.2)
            hx, hy = bb.nose(STONE_AHEAD)
            stone.x, stone.y = lerp(stone.x, hx, stone_lerp), lerp(stone.y, hy, stone_lerp)
            stone.tilt = -bb.pitch * 0.3 * bb.facing
        world.step()
        frames.append(dict(
            k=k, t=k * DT, watcher=_snap_body(wb), builder=_snap_body(bb), lookers=[_snap_body(b) for b in lb],
            w_state=wm.state, b_state=bm.state, clear=clearance(wb, bb),
            slab=dict(x=piece.x, y=piece.y, theta=piece.theta, set=piece.set, carried=carried_slab, peak=piece.peak, gap=piece.gap()),
            stones=[(s.id, s.x, s.y, s.w, s.h, s.seed, s.tilt) for p in world.pieces.values() for s in p.stones],
            loose=[(s.id, s.x, s.y, s.w, s.h, s.seed, s.tilt, s.where) for s in world.loose],
            pebbles=[(b["x"], b["y"], b["rest"]) for b in world.pebbles]))
    return Run(scenario, frames, trace, list(world.events), dict(watcher=wm, builder=bm, **{m.name: m for m in lookers}), world)


_RUNS = {}


def the_run(scenario="short", seconds=SECONDS):
    """The recorded run, cached."""
    key = (scenario, seconds)
    if key not in _RUNS:
        _RUNS[key] = simulate(scenario, seconds)
    return _RUNS[key]


# ======================================================================================== tests ===

def check(verbose=True):
    """Model-based tests and measured invariants. Raises AssertionError on a hard failure; returns a dict."""
    out = {}
    runs = {s: simulate(s, 12.0 if s != "stubborn" else 24.0) for s in ("short", "firm", "stubborn", "helped")}
    main = runs["short"]
    # 1. the graphs: nothing unreachable, nothing absorbing that was not declared
    for name, m in main.machines.items():
        unreach = set(m.states) - m.reachable()
        assert not unreach, f"{name}: unreachable {unreach}"
        assert not m.absorbing(), f"{name}: absorbing {m.absorbing()}"
    out["graph"] = "no unreachable states; only builder.JOINED is terminal, and it is declared"
    # 2. coverage: every state is entered and every transition taken in some scenario
    for name in ("watcher", "builder"):
        m0 = main.machines[name]
        visited = set().union(*(r.machines[name].visited for r in runs.values()))
        fired = set().union(*(r.machines[name].fired for r in runs.values()))
        allt = {(tr.src, tr.dst, tr.guard.name) for tr in m0.transitions}
        assert visited == set(m0.states), f"{name}: never entered {set(m0.states) - visited}"
        out[f"{name}_untaken"] = sorted(f"{a}->{b}" for a, b, _ in allt - fired)
    assert main.machines["watcher"].visited == set(main.machines["watcher"].states)
    assert main.machines["builder"].visited == set(main.machines["builder"].states)
    out["coverage"] = "the film run enters every state of both machines"
    # 3. choices are conditioned on declared state: change the world, the verdict changes
    wm = main.machines["watcher"]
    assert wm.memory["refusals"] == 1 and wm.memory["passes"] == 1
    seq = [d["dst"] for d in main.trace if d["who"] == "watcher"]
    assert seq[:5] == ["APPROACH", "INSPECT", "REFUSE", "INSPECT", "PASS"], seq
    f = runs["firm"]
    assert f.machines["watcher"].memory["refusals"] == 0 and f.machines["watcher"].memory["passes"] == 1
    assert "TURN_BACK" not in f.machines["builder"].visited and f.machines["builder"].state == "JOINED"
    s = runs["stubborn"]
    assert s.machines["watcher"].memory["passes"] == 0 and s.machines["builder"].state != "JOINED"
    hp = runs["helped"]
    assert hp.machines["watcher"].memory["passes"] == 1 and hp.machines["builder"].state == "JOINED"
    assert "TURN_BACK" not in hp.machines["builder"].visited
    out["conditioned"] = ("short pier: refuse, then pass after the wedge; whole pier: pass at once, no refusal; "
                          "short pier and no stone: 24 s of waiting, never passed; short pier put right by somebody else at 7 s: "
                          "re-inspected and passed (the pass follows the piece, not the builder)")
    peaks = [d["evidence"]["peak_deg"] for d in main.trace if d["who"] == "watcher" and d["dst"] in ("REFUSE", "PASS")]
    out["peak_deg_refused_then_passed"] = peaks
    assert peaks[0] > ROCK_LIMIT >= peaks[1]
    # 4. obedient default: in no scenario is the builder past the watcher before a pass
    for name, r in runs.items():
        passed_at = r.when("watcher", "PASS")
        for fr in r.frames:
            if passed_at is None or fr["t"] < passed_at:
                assert fr["builder"]["nose"][0] < NUDGE_X + 10, f"{name}: builder got by at {fr['t']:.2f}"
    out["obedient_default"] = "the builder's nose never crosses the watcher's line (x = NUDGE_X + 10) before PASS, in any scenario"
    # 5. locomotion continuity (centre, outside declared paper flips the tail sweeps; the centre never jumps)
    worst = {}
    for who in ("watcher", "builder"):
        mx, mp = 0.0, 0.0
        for a, b in zip(main.frames, main.frames[1:]):
            mx = max(mx, math.hypot(b[who]["x"] - a[who]["x"], b[who]["y"] - a[who]["y"]))
            mp = max(mp, abs(b[who]["pitch"] - a[who]["pitch"]))
        worst[who] = (round(mx, 1), round(mp, 1))
        assert mx <= 15.0 and mp <= 12.0, (who, mx, mp)
    out["max_step_px_and_deg_per_frame"] = worst
    # 6. no contact between the two: the refusal is a body in the way, never a shove
    cl = min(fr["clear"] for fr in main.frames)
    out["least_water_between_them_px"] = round(cl, 1)
    assert cl > 0.0, cl
    # 7. the refusal has consequence: forward progress stops, the builder goes back, the piece is changed
    t_ref, t_pass = main.when("watcher", "REFUSE"), main.when("watcher", "PASS")
    xs = [fr["builder"]["x"] for fr in main.frames if t_ref <= fr["t"] < t_pass]
    out["builder_x_during_refusal"] = (round(min(xs)), round(max(xs)))
    gaps = (main.at(t_ref)["slab"]["gap"], main.at(t_pass)["slab"]["gap"])
    out["gap_under_slab_px_before_after"] = tuple(round(g, 1) for g in gaps)
    assert gaps[0] > 20 and gaps[1] < 2
    assert any(fr["builder"]["face"] < 0 for fr in main.frames), "the builder never turned back"
    out["times"] = {k: main.when(*v) for k, v in dict(set=("builder", "PRESENT"), approach=("watcher", "APPROACH"),
                    refuse=("watcher", "REFUSE"), stopped=("builder", "STOPPED"), turn_back=("builder", "TURN_BACK"),
                    wedge=("builder", "PRESENT", 2), passed=("watcher", "PASS"), joined=("builder", "JOINED")).items()}
    if verbose:
        for k, v in out.items():
            print(f"  {k}: {v}")
    return out


# ====================================================================================== picture ===

AIR = (232, 237, 222)
STONE_COL = mix_color(w.PAL["stone"], w.PAL["water_deep"], 0.3)
SLAB_COL = (214, 204, 168)
WEDGE_COL = (158, 156, 130)             # the stone that was left on the bed: paler, so it can be followed
_SPR = {}


def _blob(wd, ht, seed, n=22):
    rs = random.Random(seed)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        r = 1.0 + rs.uniform(-0.07, 0.07)
        pts.append((wd / 2 + 2 + (abs(c) ** 0.72) * math.copysign(1, c) * wd / 2 * r, ht / 2 + 2 + (abs(s) ** 0.72) * math.copysign(1, s) * ht / 2 * r))
    return pts


def stone_sprite(wd, ht, seed, color=None):
    """A cut-paper stone, wd x ht px (cached)."""
    key = ("stone", int(wd), int(ht), seed, color)
    if key not in _SPR:
        rs = random.Random(seed + 3)
        col = mix_color(color or STONE_COL, w.PAL["stone_lt"] if rs.random() < 0.5 else w.PAL["stone_dk"], rs.uniform(0.0, 0.22))
        _SPR[key] = w._paper_piece((int(wd) + 4, int(ht) + 4), _blob(wd, ht, seed), col, seed=seed, edge=0.16, grain=0.2, shade=(0.6, 0.8, 0.5))
    return _SPR[key]


def slab_sprite(lane):
    key = ("slab", lane)
    if key not in _SPR:
        rs = random.Random(lane * 7 + 1)
        wd, ht = LANE_W - 2, SLAB_T
        pts = [(1 + rs.uniform(0, 2), 1 + rs.uniform(0, 1.5)), (wd * 0.5, 0.5 + rs.uniform(0, 1.5)), (wd - 1 - rs.uniform(0, 2), 1 + rs.uniform(0, 1.5)),
               (wd - 0.5, ht * 0.55), (wd - 2 - rs.uniform(0, 2), ht - 1), (wd * 0.45, ht - rs.uniform(0, 1.5)), (2 + rs.uniform(0, 2), ht - 1), (0.5, ht * 0.5)]
        col = mix_color(SLAB_COL, w.PAL["stone_lt"], rs.uniform(0, 0.4))
        _SPR[key] = w._paper_piece((wd, ht), pts, col, seed=200 + lane, edge=0.2, grain=0.14, shade=(0.2, 1.0, 0.5))
    return _SPR[key]


def _bank_sprite(side):
    key = ("bank", side)
    if key not in _SPR:
        size = (210, H - SURFACE + 30)
        if side == "left":
            pts = [(0, 22), (150, 22), (178, 30), (180, 40), (172, 110), (158, 200), (140, 290), (120, 400), (0, 400)]
        else:
            pts = [(210, 22), (60, 22), (32, 30), (30, 40), (40, 120), (56, 210), (70, 300), (92, 400), (210, 400)]
        col = mix_color((122, 98, 70), w.PAL["water_mid"], 0.28)
        im = w._paper_piece(size, pts, col, seed=11 if side == "left" else 12, edge=0.12, grain=0.22, shade=(0.0, 1.0, 0.7))
        _SPR[key] = im
    return _SPR[key]


def _grass(ink, x0, x1, base, seed, tall=16, lit=0.0):
    rs = random.Random(seed)
    x = x0
    while x < x1:
        hgt = tall * rs.uniform(0.5, 1.0)
        lean = rs.uniform(-5, 5)
        col = mix_color(mix_color((92, 128, 66), (150, 176, 84), rs.random()), (226, 214, 120), lit * rs.uniform(0.4, 1.0))
        ink.d.polygon([(x - 2.5, base), (x + lean, base - hgt), (x + 2.5, base)], fill=col + (255,))
        x += rs.uniform(3, 6)


_COW = {}


def _cow_sprite():
    """The lead, in cut paper, waiting on the bank (one static cutout from cast.py). None if cast is not usable."""
    if "spr" not in _COW:
        try:
            import cast
            _COW["spr"] = cast.sprite(cast.POSES["look_up"], 0.6, 1, "paper", 0.0, kind="lead")
        except Exception as e:            # the cow is another agent's piece; the study stands without her
            _COW["spr"] = None
            _COW["err"] = repr(e)
    return _COW["spr"]


def draw_stage_back(ink, t=0.0, cow=True):
    """The Act 3 set behind the fish: c13 river, air above the surface, far weed, both banks. Fills the frame."""
    w.river(ink, t)
    wave = [(x, SURFACE + 1.6 * math.sin(x / 41.0 + t * 1.3) + 1.0 * math.sin(x / 17.0 - t * 0.9)) for x in range(0, W + 16, 16)]
    ink.d.polygon([(0, 0), (W, 0)] + wave[::-1], fill=AIR + (255,))
    ink.d.line([(x, y + 4) for x, y in wave], fill=(244, 250, 236, 110), width=5)
    ink.d.line(wave, fill=(250, 252, 244, 255), width=2)
    for x, hgt, seed in ((214, 120, 3), (662, 96, 5), (752, 150, 6), (388, 70, 8)):
        w.weed(ink, x, BED - 6, hgt, t=t, seed=seed, n=4, spread=22, dark=0.55)
    for side, x in (("left", 0), ("right", W - 210)):
        ink.paste(_bank_sprite(side), (x, SURFACE - 30))
    ink.d.rectangle([0, SURFACE - 9, LEFT - 26, SURFACE - 1], fill=(104, 132, 70, 255))
    ink.d.rectangle([RIGHT + 26, SURFACE - 9, W, SURFACE - 1], fill=(132, 156, 76, 255))
    _grass(ink, 0, LEFT - 16, SURFACE - 6, 5, tall=14)
    _grass(ink, RIGHT + 18, W, SURFACE - 6, 6, tall=34, lit=1.0)          # the far grass: what the cow wants
    if cow:
        c = _cow_sprite()
        if c is not None:
            spr, (ax, ay) = c
            ink.paste(spr, (int(86 - ax), int(SURFACE - 8 - ay)))


def draw_pier(ink, stones):
    """A pier: `stones` = [(id, x, y, w, h, seed, tilt), ...] bottom to top."""
    for _, x, y, wd, ht, seed, tilt in stones:
        w.put(ink, stone_sprite(wd, ht, seed, WEDGE_COL if _ in ("dropped", "helped") else None), x, y, angle=tilt, shadow=0.35,
              shadow_off=(3, 4), shadow_blur=3)


def draw_slab(ink, lane, x=None, y=None, theta=0.0, shadow=0.4):
    """One span of the road. Default place: seated in its lane. theta degrees, + = right end up."""
    sx, sy = (lane_cx(lane), SURFACE + SLAB_T / 2)
    w.put(ink, slab_sprite(lane), sx if x is None else x, sy if y is None else y, angle=theta, shadow=shadow, shadow_off=(2, 4), shadow_blur=3)


def draw_fish(ink, f, shadow=0.3):
    """A trout from a snapshot dict: x, y, pitch (deg, + nose up), face (+1 right), wide (1 = side on,
    toward 0 = edge on, mid paper-flip), length, lid, amp, phase."""
    spr = w.trout_sprite(f["length"], f["phase"], f["amp"], f["lid"])
    if f["face"] > 0:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    ang = f["pitch"] if f["face"] > 0 else -f["pitch"]
    if abs(ang) > 0.3:
        spr = spr.rotate(ang, expand=True, resample=Image.BICUBIC)
    if f["wide"] < 0.995:
        spr = spr.resize((max(3, int(spr.width * f["wide"])), spr.height), Image.BICUBIC)
    w.put(ink, spr, f["x"], f["y"], shadow=shadow, shadow_off=(4, 6), shadow_blur=4)


def draw_refusal(ink, run, t, cow=True):
    """The whole frame at time t of a recorded Run (see simulate / the_run)."""
    fr = run.at(t)
    draw_stage_back(ink, t, cow=cow)
    draw_pier(ink, fr["stones"])
    for sid, x, y, wd, ht, seed, tilt, where in fr["loose"]:
        if where == "bed":
            w.put(ink, stone_sprite(wd, ht, seed, WEDGE_COL), x, y, angle=tilt, shadow=0.4, shadow_off=(3, 4), shadow_blur=3)
    for x, y, rest in fr["pebbles"]:
        ink.d.ellipse([x - 4, y - 3, x + 4, y + 3], fill=(60, 68, 60, 255), outline=(20, 30, 30, 255))
    for lane in range(1, 7):
        if lane != LANE:
            draw_slab(ink, lane)
    s = fr["slab"]
    if s["set"]:
        draw_slab(ink, LANE, s["x"], s["y"], s["theta"])
    for f in fr["lookers"]:
        draw_fish(ink, f, shadow=0.2)
    draw_fish(ink, fr["watcher"])
    for sid, x, y, wd, ht, seed, tilt, where in fr["loose"]:
        if where == "carried":
            w.put(ink, stone_sprite(wd, ht, seed, WEDGE_COL), x, y, angle=tilt, shadow=0.3, shadow_off=(3, 4), shadow_blur=3)
    draw_fish(ink, fr["builder"])
    if not s["set"]:
        draw_slab(ink, LANE, s["x"], s["y"], s["theta"], shadow=0.5)
    for f, kind, d in run.events:
        if kind == "sigh" and f * DT <= t:
            w.bubbles(ink, (d["x"], d["y"]), t, f * DT, n=4, rise=64.0, curl=16.0, size=3.6)
    w.weed(ink, 60, H + 6, 120, t=t, seed=21, n=5, spread=40)
    w.weed(ink, 902, H + 10, 150, t=t, seed=22, n=5, spread=44)
    return fr


# ======================================================================================== sound ===

def _underwater(mix, at, seconds, gain, ducks=()):
    """River heard from below: the kit's water, low-passed to 900 Hz. ducks = [(t0, t1, level)] in film time."""
    m2 = Mix(seconds, seed=5)
    m2.water(0, seconds, gain=1.0)
    sig = mix.lowpass(m2.L, 900)
    env = np.ones(len(sig))
    tt = np.arange(len(sig)) / mix.rate + at
    for a, b, lv in ducks:
        k = np.clip((tt - (a - 0.25)) / 0.25, 0, 1) * np.clip(((b + 0.35) - tt) / 0.35, 0, 1)
        env *= 1 - (1 - lv) * k
    mix.add(sig * env, at, gain * 2.4)


def score_refusal(mix, run, t0=0.0, gain=1.0):
    """Sound for a recorded Run, every event taken from the run's own contacts. NOT LISTENED TO by anyone:
    timings are structural, levels are guesses from the numbers."""
    pan = lambda x: clamp((x - W / 2) / (W / 2), -0.8, 0.8)
    t_stop, t_turn = run.when("builder", "STOPPED"), run.when("builder", "TURN_BACK")
    dur = len(run.frames) * DT
    _underwater(mix, t0, dur, 0.05 * gain, ducks=[(t0 + t_stop, t0 + t_turn, 0.5)] if t_stop and t_turn else ())
    pitch = LANE_PITCH[LANE]
    clacks = 0
    for f, kind, d in run.events:
        t = t0 + f * DT
        if kind == "set":
            mix.step(t, 0.3 * gain, pan(d["x"]), "stone")
            mix.pluck(t + 0.02, pitch / 2, 0.9, 0.16 * gain, pan(d["x"]))
        elif kind == "nudge":
            if d["supported"]:
                mix.pluck(t, pitch, 2.4, 0.3 * gain, pan(d["x"]))                # true, and left to ring
                mix.bell(t, pitch, 2.2, 0.07 * gain, pan(d["x"]))
            else:
                mix.pluck(t, 415.0, 0.9, 0.26 * gain, pan(d["x"]))               # the A is wrong
            clacks = 0
        elif kind == "clack" and clacks < 4:
            mix.step(t, (0.3, 0.22, 0.12, 0.07)[clacks] * gain, pan(d["x"]), "wood")
            clacks += 1
        elif kind == "pebble":
            mix.click(t, 0.12 * gain, pan(d["x"]), bright=5000)
        elif kind == "pebble_land":
            mix.click(t, 0.08 * gain, pan(d["x"]), bright=1500, seconds=0.05)
        elif kind == "dart":
            mix.whoosh(t, 0.3, 0.07 * gain, pan(d["x"]))
        elif kind == "pick":
            mix.click(t, 0.1 * gain, pan(d["x"]), bright=1800, seconds=0.05)
        elif kind == "wedge":
            mix.step(t, 0.4 * gain, pan(d["x"]), "stone")
            mix.thud(t, 90, 0.18 * gain, pan(d["x"]), 0.25)
        elif kind == "joined":
            for k, fq in enumerate((293.7, 329.6, 370.0, 493.9, 587.3, 440.0)):
                mix.pluck(t + 0.07 * k, fq, 1.0, 0.07 * gain, pan(700))
    mix.reverb(0.12)


# ========================================================================================= film ===

def make_film():
    run = the_run("short", SECONDS)
    film = Film(SLUG, seconds=SECONDS, boil=0)
    film.poster_at = (run.when("builder", "STOPPED") or 5.0) + 0.6

    def frame(t, ink):
        draw_refusal(ink, run, t)

    film.picture(frame)
    film.sound(lambda mix: score_refusal(mix, run))
    return film, run


def sheet(path, t0=0.0, t1=SECONDS, n=16, cols=4):
    """A contact sheet of n stills between t0 and t1 (no labels drawn on the pictures: times go to stdout)."""
    film, run = make_film()
    ts = [t0 + (t1 - t0) * (k + 0.5) / n for k in range(n)]
    tw, th = W // 2, H // 2
    rows = (n + cols - 1) // cols
    im = Image.new("RGB", (cols * tw + (cols + 1) * 4, rows * th + (rows + 1) * 4), (20, 20, 20))
    for k, t in enumerate(ts):
        fr = film.frame(int(round(t * FPS))).resize((tw, th), Image.LANCZOS)
        im.paste(fr, (4 + (k % cols) * (tw + 4), 4 + (k // cols) * (th + 4)))
    im.save(path)
    print("sheet ->", path)
    print("times:", " ".join(f"{t:.2f}" for t in ts))
    print("states:", " | ".join(f"{run.at(t)['w_state']}/{run.at(t)['b_state']}" for t in ts))


def print_trace(run=None):
    run = run or the_run()
    for d in run.trace:
        print(f"{d['t']:6.2f}s  {d['who']:<10} {d['src']:>9} -> {d['dst']:<9} because {d['guard']}  {d['evidence']}")
        print(f"         now wants: {d['want']}")
    print("contacts:", ", ".join(f"{k}@{f * DT:.2f}" for f, k, _ in run.events))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check()
        print("all checks passed")
    elif args and args[0] == "--trace":
        print_trace()
    elif args and args[0] == "--chart":
        r = the_run()
        for m in r.machines.values():
            print(m.chart())
    elif args and args[0] == "--sheet":
        rest = args[2:]
        sheet(args[1], *(float(x) for x in rest[:2])) if rest else sheet(args[1])
    else:
        film, run = make_film()
        film.render()
