"""S6 · NO, AND AGAIN · film seconds 144.0 to 180.0 (local t = film - 144).

Built under scion/animation-48.md (STATE MACHINES: characters that can refuse). Its primitives are real
data in this file, not a look:

    St, Tr        a state with its ACTION WINDOW (the time the action needs before anything but an
                  interrupt may end it) and its INTENTION; a transition with a GUARD and a PRIORITY
    Machine       one character: lead dog, old dog, wooden retriever, three passers, lead cow
    World         PERSISTENT WORLD DATA: facts with the time they became true, the reels and whether
                  each is ruled straight ("tidy", the wrong kind) or as the child drew it, who is
                  holding a reel out at the sill, the ledger of cans on the boards, the pebbles
    CIRCUMSTANCES the only things typed in by hand: what the person does (takes the reel, says no)
                  and when work that happens off screen is finished. Nobody is told to move.

The film's timeline is what the machines DO under those circumstances (run once, at 24 steps a second,
then only read: a still at any time matches the film). The old dog turns its back because the reel
held out to it is tidy; it lets the same builder pass because the reel has changed. check() runs the
machines again with the circumstances changed and asserts that the refusal goes away when its cause
does (a right reel is never refused; with no "no" the dog never calls the pack), that every declared
state is reached, that nobody is left stuck in a state that is not an ending, and that the board's
seconds come out of the guards and windows to within one frame. What can only be judged by looking
is in the builder's report, not here.

Staging is the board's (films/swarm/dogs/board.md, S6): F-PORCH wide for the reel held to the lamp;
a push in for the ears; six dogs under at once and a crane down to F-SPLIT; the gate frame (lower
and closer, the old dog in profile, the cow tall behind) locked for the turn; one cut to the town
for the change; back; and the slow crane down to F-LAST. Times in this file are FILM seconds.

Exposes SECONDS, draw(t, ink), sound(mix, at).
"""
from __future__ import annotations

import bisect
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

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
try:
    import foley                             # real recordings (SOUND.md: use these first)
except Exception:                            # pragma: no cover
    foley = None

SECONDS = 36.0
T0 = 144.0
T1 = T0 + SECONDS
DT = 1.0 / FPS
TEAL = (24, 120, 128)
Cam = town.Cam
SILL_Y = 394.0
DS = 0.6                                     # lead dog
RS = 0.42                                    # retrievers, sheepdog
BIG_S = 0.5                                  # the big wooden retriever in the gate frame
BIG_REEL = 0.9                               # its can: 43 px across in the wide, a fifth of the frame high in the closer setups
HS = 0.62                                    # herding dog
GS = 0.84                                    # wire digger
OLD_S = 0.78
OLD_X0, OLD_X1 = 425.0, 405.0                # the old dog's place; where it shifts to, to lie across the dry half
PRESENT_X = 541.0                            # where a dog stands on the wet half to hold its reel out
BREACH_X = 596.0                             # where a dog comes up: just past the sill's end
LAY_X = 306.0                                # where a passed reel is put on the pile
CAN_HOME = (252.0, 366.0)                    # the can the person took from the dog, beside the knee
COW_NEAR = 548.0                             # REPAIR: where the lead cow comes to, behind the dog that was told no
COW_X0, COW_X1 = 664.0, 636.0                # the lead cow: in the meadow; behind the wet end of the sill


def bump(x):
    return math.sin(math.pi * clamp(x)) if 0 < x < 1 else 0.0


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


# ====================================================================== #
#  1 · STATE MACHINES (scion/animation-48)                               #
# ====================================================================== #

class St:
    """A state: its action window (seconds the action needs), what the character wants in it, and
    whether the film may end with the character in it."""

    def __init__(self, window=0.0, intent="", end=False):
        self.window, self.intent, self.end = window, intent, end


class Tr:
    """A transition. The guard reads the world (never the clock of the film). Higher priority is
    tried first. interrupt=True may cut an action window short."""

    def __init__(self, src, dst, guard=None, prio=0, why="", interrupt=False):
        self.src, self.dst, self.guard, self.prio, self.why, self.interrupt = src, dst, guard, prio, why, interrupt


class World:
    """Persistent world data: facts (with the time each became true), reels, and every machine's state."""

    def __init__(self, reels):
        self.facts = {}
        self.reels = {k: dict(v) for k, v in reels.items()}
        self.m = {}

    def set(self, key, value, f):
        self.facts[key] = (value, f)

    def get(self, key, default=None):
        return self.facts.get(key, (default, None))[0]

    def age(self, key, f):
        v = self.facts.get(key)
        return (f - v[1]) if v and v[0] else -1.0

    def st(self, name):
        return self.m[name].state

    def since(self, name, f):
        return f - self.m[name].entered

    def offered(self):
        """Who is holding a reel out to the old dog, and is that reel the tidy (wrong) kind."""
        who = self.get("offer")
        return (who, self.reels[who]["tidy"]) if who else (None, None)


class Machine:
    def __init__(self, name, start, states, trans, enter=None):
        self.name, self.start, self.states = name, start, states
        self.trans = sorted(trans, key=lambda tr: -tr.prio)
        self.enter = enter or {}
        for tr in trans:
            assert tr.src in states and tr.dst in states, (name, tr.src, tr.dst)

    def reset(self, f):
        self.state, self.entered, self.log = self.start, f, [(f, self.start, "start")]

    def step(self, w, f):
        st = self.states[self.state]
        done = f - self.entered >= st.window - 1e-6
        for tr in self.trans:
            if tr.src != self.state or not (done or tr.interrupt):
                continue
            if tr.guard is None or tr.guard(w, f):
                self.state, self.entered = tr.dst, f
                self.log.append((f, tr.dst, tr.why))
                if tr.dst in self.enter:
                    self.enter[tr.dst](w, f)
                return


def _offer(who):
    return lambda w, f: w.set("offer", who, f)


def _clear(w, f):
    w.set("offer", None, f)


def lead_machine():
    S = dict(
        pleased=St(0, "it has brought the right thing", end=True),
        stilled=St(1.0, "something is wrong: the tail stops"),
        ears_down=St(1.0, "it was told no"),
        hold=St(1.6, "it does not argue; it looks at the picture"),
        look_bubble=St(0.37, "it sees how the child drew it"),
        turn=St(0.8, "it will go again"),
        look_pack=St(1.2, "one dog was not enough: look along the bank, go to the edge"),
        dive=St(0.6, "down"),
        under=St(0, "making it again, the child's way"),
        come_up=St(0.5, "up, with a reel"),
        in_line=St(0, "wait its turn at the old dog"),
        step_back=St(0.6, "let the proud one go first"),
        watch_line=St(0, "watch what the old dog does"),
        walk_up=St(1.25, "its turn"),
        lay=St(0.7, "set it down"),
        lie=St(0, "half in, half out", end=True),
    )
    T = [
        Tr("pleased", "stilled", lambda w, f: w.age("no", f) >= 1.0, why="the person shook their head"),
        Tr("stilled", "ears_down"), Tr("ears_down", "hold"), Tr("hold", "look_bubble"), Tr("look_bubble", "turn"),
        Tr("turn", "look_pack"), Tr("look_pack", "dive", why="the six are up; they go with it"), Tr("dive", "under"),
        Tr("under", "come_up", lambda w, f: w.get("due:lead"), why="its reel is made"),
        Tr("come_up", "in_line"),
        Tr("in_line", "step_back", lambda w, f: w.st("big") in ("breach", "roll_up"), why="the wooden one barges up"),
        Tr("step_back", "watch_line"),
        Tr("in_line", "walk_up", lambda w, f: w.st("big") in ("leave", "rest") and w.since("big", f) >= 0.4, prio=1),
        Tr("watch_line", "walk_up", lambda w, f: w.st("big") in ("leave", "rest") and (w.st("big") == "rest" or w.since("big", f) >= 0.3),
           why="the gate is open"),
        Tr("walk_up", "lay"), Tr("lay", "lie"),
    ]
    return Machine("lead", "pleased", S, T, enter=dict(dive=lambda w, f: w.set("pack_gone", True, f)))


def old_machine():
    S = dict(
        lie=St(0, "nothing: it built nothing", end=True),
        shift=St(0.8, "lie across the whole dry half: everything passes it"),
        glance=St(0.3, "look at what is held out"),
        blink=St(0.55, "it is as the child drew it"),
        chin=St(0.25, "pass"),
        raise_=St(1.15, "this one is wrong; look properly"),
        long_look=St(1.2, "look at it until it is sure"),
        turn_back=St(2.5, "refuse: get up, turn round, lie down with its back to it"),
        back=St(0, "a back"),
        look_over=St(0.5, "it has come again: look over the shoulder"),
        let_pass=St(0.58, "it has changed: make room"),
        passed=St(0, "eyes shut"),
        rise_turn=St(0.8, "the looking is done; go to the other one who waits"),
        walk=St(1.1, "to the cow"),
        lie_down=St(0.9, "down, against her chest"),
        beside=St(0, "the two who wait", end=True),
    )
    cow_down = lambda w, f: w.st("cow") in ("fold", "lie") and (w.st("cow") == "lie" or w.since("cow", f) >= 0.45)   # noqa: E731
    T = [
        Tr("lie", "shift", lambda w, f: w.st("lead") == "under" and w.since("lead", f) >= 0.5 and not w.get("shifted"), prio=3,
           why="the pack has gone under; the reels will come"),
        Tr("shift", "lie"),
        Tr("lie", "raise_", lambda w, f: w.offered()[1] is True, prio=2, why="a tidy reel is held out"),
        Tr("lie", "glance", lambda w, f: w.offered()[1] is False, prio=1, why="a reel is held out"),
        Tr("glance", "blink"), Tr("blink", "chin"), Tr("chin", "lie"),
        Tr("raise_", "long_look"), Tr("long_look", "turn_back"), Tr("turn_back", "back"),
        Tr("back", "look_over", lambda w, f: w.offered()[1] is False, why="the same builder, the reel changed"),
        Tr("look_over", "let_pass"), Tr("let_pass", "passed"),
        Tr("passed", "rise_turn", cow_down, why="she has folded down"),
        Tr("lie", "rise_turn", lambda w, f: cow_down(w, f) and w.get("offer") is None, why="she has folded down"),
        Tr("rise_turn", "walk"), Tr("walk", "lie_down"), Tr("lie_down", "beside"),
    ]

    def passed_now(w, f):
        who = w.get("offer")
        if who:
            w.set("passed:" + who, True, f)

    return Machine("old", "lie", S, T, enter=dict(shift=lambda w, f: w.set("shifted", True, f), chin=passed_now, let_pass=passed_now))


def passer_machine(name, breach=0.45, to_cow=None, walk=1.0, lay=0.35, dive=0.6):
    S = dict(
        under=St(0, "making its piece"),
        breach=St(breach, "up, with a reel"),
        offer=St(0, "hold it out to the old dog"),
        pass_=St(walk, "passed: carry it to the pile"),
        lay=St(lay, "lay it on the pile"),
        dive=St(dive, "go for another"),
        again=St(0, "under again", end=True),
    )
    T = [Tr("under", "breach", lambda w, f: w.get("pack_gone") and w.get("due:" + name), why="it went under with the pack; its reel is made"),
         Tr("offer", "pass_", lambda w, f: w.get("passed:" + name), why="the old dog put its chin down"),
         Tr("pass_", "lay"), Tr("lay", "dive"), Tr("dive", "again")]
    if to_cow:
        S["to_cow"] = St(to_cow, "the cow wants to smell it; hold it up for her")
        T += [Tr("breach", "to_cow"), Tr("to_cow", "offer")]
    else:
        T += [Tr("breach", "offer")]
    return Machine(name, "under", S, T, enter=dict(offer=_offer(name), pass_=_clear,
                                                   lay=lambda w, f: w.set("laid:" + name, True, f)))


def big_machine():
    S = dict(
        under=St(0, "making its piece"),
        breach=St(0.5, "up, with a reel"),
        roll_up=St(1.0, "onto the sill, in front of everybody"),
        proud=St(0, "hold it high: look what I made"),
        told=St(1.2, "a back. Look at it; look at the person; look at the cow. No help."),
        nudged=St(1.4, "the cow steps up and noses it back toward the water: go on, again"),
        roll_back=St(0.8, "go down again"),
        fix=St(2.6, "take out the straight piece; put the child's page in; take the can up"),
        come_up=St(0.37, "up, with it changed"),
        offer_low=St(0, "hold it out, lower this time"),
        lay=St(0.5, "lay it down"),
        leave=St(1.5, "roll off to the meadow"),
        rest=St(0, "hold still so the calf can sleep", end=True),
    )
    T = [
        Tr("under", "breach", lambda w, f: w.get("pack_gone") and w.get("due:big"), why="it went under with the pack; its reel is made"),
        Tr("breach", "roll_up"), Tr("roll_up", "proud"),
        Tr("proud", "lay", lambda w, f: w.get("passed:big"), prio=2, why="the old dog passed it"),
        Tr("proud", "told", lambda w, f: w.st("old") == "back", prio=1, why="the old dog turned its back"),
        Tr("told", "nudged", why="no help from the old dog or the person; it looks up at the cow"),
        Tr("nudged", "roll_back", why="she pushed it to the edge"), Tr("roll_back", "fix"), Tr("fix", "come_up"), Tr("come_up", "offer_low"),
        Tr("offer_low", "lay", lambda w, f: w.st("old") in ("let_pass", "passed") and w.since("old", f) >= 0.3 - 1e-6,
           why="the old dog made room"),
        Tr("lay", "leave"), Tr("leave", "rest"),
    ]

    def changed(w, f):
        w.reels["big"]["tidy"] = False
        w.reels["big"]["paw"] = True

    return Machine("big", "under", S, T, enter=dict(proud=_offer("big"), told=_clear, come_up=changed,
                                                   offer_low=_offer("big"), lay=_clear))


def cow_machine():
    S = dict(
        stand=St(0, "watch the sill from among the herd"),
        fold1=St(2.0, "the night's work is done: lie down"),
        lying=St(0, "chew", end=True),
        get_up=St(1.0, "the dogs are going again: get up, hind end first"),
        walk=St(2.0, "down her own path to the place she always drinks"),
        watch=St(0, "watch the gate; she knows gates", end=True),
        smell=St(1.2, "smell what the dog holds up"),
        still=St(0, "the old dog is looking: stop chewing"),
        nose=St(1.4, "step up to the stuck one and nose it back to the water, the way she noses the calf"),
        chew=St(0, "it is all right: chew"),
        fold=St(2.0, "it is over: fold down where she stands"),
        lie=St(0, "beside the old dog", end=True),
    )
    laid = lambda w, f: w.st("big") in ("lay", "leave", "rest") and (w.st("big") != "lay" or w.since("big", f) >= 0.3 - 1e-6)   # noqa: E731
    T = [
        Tr("stand", "fold1", lambda w, f: w.age("reel_taken", f) >= 0.6, why="the person has the reel"),
        Tr("fold1", "lying"),
        Tr("lying", "get_up", lambda w, f: w.st("lead") == "turn" and w.since("lead", f) >= 0.5 - 1e-6, why="the dog turned to the water"),
        Tr("get_up", "walk"), Tr("walk", "watch"),
        Tr("watch", "smell", lambda w, f: w.st("sheep") == "to_cow", prio=2, why="a reel under her chin"),
        Tr("smell", "watch"),
        Tr("watch", "still", lambda w, f: w.st("old") == "long_look", prio=1, why="the old dog's long look"),
        Tr("still", "nose", lambda w, f: w.st("big") == "nudged", why="the builder looks up at her"),
        Tr("nose", "chew"),
        Tr("chew", "fold", laid, why="the reel is laid"),
        Tr("watch", "fold", laid, why="the reel is laid"),
    ]
    T.append(Tr("fold", "lie"))
    return Machine("cow", "stand", S, T)


CIRCUMSTANCES = [   # film time, fact, value: what the person does, and when off-screen work is finished
    (144.0, "reel_taken", True),             # the hand takes the reel
    (148.0, "no", True),                     # the head shakes, twice
    (157.2, "due:herder", True),
    (158.4, "due:digger", True),
    (159.6, "due:sheep", True),
    (161.0, "due:lead", True),
    (161.0, "due:big", True),
]
REELS = {   # who carries it up: is it ruled straight (wrong), which real film its lid shows
    "herder": dict(tidy=False, n=13), "digger": dict(tidy=False, n=42), "sheep": dict(tidy=False, n=props.REEL_COW),
    "lead": dict(tidy=False, n=16), "big": dict(tidy=True, n=props.REEL_RETRIEVER),
}
ORDER = ("lead", "old", "herder", "digger", "sheep", "big", "cow")
SHEEP_KW = dict(breach=0.2, to_cow=1.15, walk=0.7, lay=0.3, dive=0.5)


def run(circumstances=CIRCUMSTANCES, reels=REELS, f1=T1 + 4.0):
    """Step every machine from 144.0. Returns ({name: log}, world). log = [(film time, state, why)]."""
    w = World(reels)
    ms = dict(lead=lead_machine(), old=old_machine(), herder=passer_machine("herder"), digger=passer_machine("digger"),
              sheep=passer_machine("sheep", **SHEEP_KW), big=big_machine(), cow=cow_machine())
    w.m = ms
    for m in ms.values():
        m.reset(T0)
    circ = sorted(circumstances)
    ci = 0
    n = int(round((f1 - T0) * FPS))
    for i in range(n + 1):
        f = T0 + i * DT
        while ci < len(circ) and circ[ci][0] <= f + 1e-9:
            w.set(circ[ci][1], circ[ci][2], f)
            ci += 1
        for name in ORDER:
            ms[name].step(w, f)
    return {k: m.log for k, m in ms.items()}, w


@lru_cache(maxsize=None)
def film():
    return run()[0]


def at(name, f):
    """(state, seconds in it) of a character at film time f."""
    log = film()[name]
    i = bisect.bisect_right([e[0] for e in log], f + 1e-9) - 1
    i = max(0, i)
    return log[i][1], f - log[i][0]


def when(name, state, default=None):
    for (f, s, _) in film()[name]:
        if s == state:
            return f
    return default


def after(name, state, f):
    """Seconds since the character FIRST entered `state` (negative before)."""
    tw = when(name, state)
    return -1e9 if tw is None else f - tw


# ====================================================================== #
#  2 · CAMERA                                                            #
# ====================================================================== #

WIDE = (480.0, 270.0, 1.0)                   # F-PORCH
MED = (362.0, 336.0, 1.55)                   # the dog, the picture on the door at the left edge, the child's page below
SPLIT = (480.0, 520.0, 1.0)                  # F-SPLIT
GATE = (470.0, 345.0, 1.5)                   # a little lower and closer: sill at centre, cow tall at the upper right
LAST = (480.0, 420.0, 1.0)                   # F-LAST
INSERT = Cam.look(546.0, 768.0, 2.3)         # the making place, where the reel is changed
CLOSE = {   # the closer setups (world centre x, y, zoom): the cast is drawn again at this size, see _close_frame
    "no": (318.0, 304.0, 2.25),               # REPAIR: the person (seen from behind the shoulder, never a face), the film, the dog
    "ears": (432.0, 346.0, 2.5),             # REPAIR: the pushed-back can, the dog 190 px high, the cow's head coming down to it
    "smell": (588.0, 338.0, 2.2),            # two-shot: the sheepdog and the lead cow; the can held up under her chin
    "look": (500.0, 345.0, 2.7),             # the old dog's face, the can a fifth of the frame high, the proud dog, her muzzle above
    "nudge": (572.0, 336.0, 2.3),            # two-shot: the wooden dog and the lead cow
    "pass": (486.0, 346.0, 2.4),             # the same can, changed, held lower; the old dog over its shoulder
}


@lru_cache(maxsize=None)
def shots():
    """film a, b, name, why the camera is there. The cuts fall where the machines put the events."""
    t_look = when("old", "raise_") + 0.75
    t_turn = when("old", "turn_back")
    t_told = when("big", "told") + 0.12
    t_fix, t_up = when("big", "fix"), when("big", "come_up")
    return [
        (144.0, 145.8, "porch", "wide: the reel is taken, the lamp, the door, the herd, all in one frame"),
        (145.8, 149.3, "no", "REPAIR: close on the two of them. The film goes up to the lamp; the head says no, large enough to read"),
        (149.3, 152.6, "ears", "REPAIR: the can is pushed back to the dog; its ears, a third of the frame high; the lead cow comes to it"),
        (152.6, 153.0, "medium", "the dog, and the child's page under the sill that it looks down at"),
        (153.0, 153.7, "pull", "back out: the answer is along the whole bank"),
        (153.7, 155.0, "porch", "six dogs and a cow share the waterline"),
        (155.0, 157.0, "crane", "down with the dogs: the line passes, the rest of the pack breaks it"),
        (157.0, 159.3, "gate", "this is a gate and we look along it: two reels pass, so the pattern is learned"),
        (159.3, 161.0, "smell", "the one who has stood at gates all her life wants to know what is in the dog's mouth"),
        (161.0, t_look, "gate", "the proud one barges up in front of everybody"),
        (t_look, t_turn, "look", "close enough to see what the old dog is looking at"),
        (t_turn, t_told, "gate", "wide for the whole body: it gets up, goes round, lies down with its back to the reel"),
        (t_told, t_fix, "nudge", "nobody helps; then the cow does the one thing a cow knows"),
        (t_fix, t_up, "town", "what it goes down for: the straight piece out, the child's page in, the can taken up"),
        (t_up, 175.0, "pass", "close, so the only thing that has changed is the picture on the can"),
        (175.0, 178.0, "last-crane", "down until the line is in the middle: half the frame for the ones it was for"),
        (178.0, 180.0, "last", "locked"),
    ]


def shot_at(f):
    for sh in shots():
        if sh[0] <= f < sh[1]:
            return sh
    return shots()[-1]


def camera(f):
    """(world cx, world cy, zoom) of the frame's centre, for the setups that are one drawing of the porch."""
    def mix(a, b, u):
        return tuple(lerp(p, q, u) for p, q in zip(a, b))
    if f < 152.6:
        return WIDE                                           # (145.8 to 152.6 are closer setups, drawn by _close_frame)
    if f < 153.0:
        return MED
    if f < 155.0:
        return mix(MED, WIDE, ease(f, 153.0, 153.7))
    if f < 157.0:
        return mix(WIDE, SPLIT, ease(f, 155.0, 157.0))
    if f < 175.0:
        return GATE
    return mix(GATE, LAST, ease(f, 175.0, 178.0))


def view(ink, cx, sy, zoom):
    """Re-frame the finished picture: zoom about screen point (cx, sy), which goes to the frame's centre."""
    if abs(zoom - 1) < 1e-4 and abs(cx - W / 2) < 1e-3 and abs(sy - H / 2) < 1e-3:
        return
    a = 1.0 / zoom
    ink.img = ink.img.transform((W, H), Image.AFFINE, (a, 0, cx - W / 2 * a, 0, a, sy - H / 2 * a), resample=Image.BICUBIC)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ====================================================================== #
#  3 · SMALL TOOLS                                                       #
# ====================================================================== #

def _redraw(ink):
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# A CLOSER SETUP is not a blow-up of the wide frame. The set is drawn once at its own size and pushed in
# (soft, as a background out of focus should be); the animals and what they carry are then DRAWN AGAIN at
# the closer size, so their edges are cut as cleanly as in the wide. Everything in part 5 goes on working
# in the wide frame's pixels; these few functions carry a point or a size across.

class _Zoom:
    on, cx, cy, z = False, W / 2, H / 2, 1.0


ZM = _Zoom()


def zx(x):
    return W / 2 + (x - ZM.cx) * ZM.z if ZM.on else x


def zy(y):
    return H / 2 + (y - ZM.cy) * ZM.z if ZM.on else y


def zs():
    return ZM.z if ZM.on else 1.0


def unz(pt):
    return (ZM.cx + (pt[0] - W / 2) / ZM.z, ZM.cy + (pt[1] - H / 2) / ZM.z) if ZM.on else pt


def _is_pt(v):
    return isinstance(v, tuple) and len(v) == 2 and all(isinstance(c, (int, float)) for c in v)


def unz_a(a):
    """Anchors a cast module returned in the closer frame, carried back to the wide frame's pixels."""
    if not ZM.on or not isinstance(a, dict):
        return a
    out = {}
    for k, v in a.items():
        if _is_pt(v):
            out[k] = unz(v)
        elif isinstance(v, dict):
            out[k] = {n: (unz(q) if _is_pt(q) else q) for n, q in v.items()}
        else:
            out[k] = v
    return out


FLIP_MIN = 0.62          # a card dog turning is never drawn thinner than this: no edge-on sliver


def old_P(action, t=0.0, p=0.0, look=0.0):
    """The old dog's pose for an action of kennel_a, with its turn kept off the card's edge."""
    tq = math.floor(t * 8 + 1e-6) / 8
    P = dict(ka._old_pose(action, tq, p, look))
    sx = P.get("sx", 1.0)
    if abs(sx) < FLIP_MIN:
        P["sx"] = FLIP_MIN if sx >= 0 else -FLIP_MIN
    return P


def OLD(ink, x, y, s, facing=1, action="lie", t=0.0, p=0.0, P=None, **kw):
    """kennel_a.old_dog, drawn from a pose of ours (so two of its actions can be joined without a jump and its
    turn never goes edge-on), in whichever frame is being drawn. kennel_a is not edited: its pose function is
    borrowed for the length of this one call and put back."""
    if P is None:
        P = old_P(action, t, p)
    orig = ka._old_pose
    ka._old_pose = lambda *a, **k: dict(P)
    try:
        a = ka.old_dog(ink, zx(x), zy(y), s * zs(), facing, "swim" if action == "swim" else "lie", t=t, exposure=0, **kw)
    finally:
        ka._old_pose = orig
    return unz_a(a)


def DOG(target, pose, x, y, scale=1.0, **kw):
    return unz_a(dog.draw_dog(target, pose, zx(x), zy(y), scale=scale * zs(), **kw))


def RET(target, x, y, action, tau, scale=1.0, **kw):
    return unz_a(kb.retriever(target, zx(x), zy(y), action, tau, scale=scale * zs(), **kw))


def COW(ink, who, pose, x, y, s=None, facing=1, oy=0, nose_to=None, **kw):
    if not ZM.on:
        return herd.cow(ink, who, pose, x, y, s, facing, oy, nose_to=nose_to, **kw)
    nt = (zx(nose_to[0]), zy(nose_to[1] - oy)) if nose_to is not None else None
    return unz_a(herd.cow(ink, who, pose, zx(x), zy(y - oy), (herd.S if s is None else s) * ZM.z, facing, 0, nose_to=nt, **kw))


def BREATH(ink, x, y, p, facing=1, size=1.0):
    herd.breath(ink, zx(x), zy(y), p, facing, size=size * zs())


def DRIPS(ink, f, x, y, t0, width=20.0, floor=None, s=1.0, **kw):
    props.drips(ink, f, zx(x), zy(y), t0, width=width * zs(), floor=None if floor is None else zy(floor), s=s * zs(), **kw)


def REEL(ink, n, x, y, s=1.0, **kw):
    return props.reel(ink, n, zx(x), zy(y), s * zs(), **kw)


def on_layer(ink, fn, rot=0.0, pivot=None, tint=None, amount=0.0, alpha=1.0, split=None):
    """Draw fn(layer) on a sheet of its own, then turn it, tint it, fade it, or (split = screen y of the
    water line) show what is below the line as seen through water. Returns what fn returned."""
    lay = Image.new("RGBA", ink.img.size, (0, 0, 0, 0))
    out = fn(lay)
    box = lay.getbbox()
    if box is None:
        return out
    if rot and pivot:                                         # room for the turn, about the pivot
        r = max(math.hypot(cx - pivot[0], cy - pivot[1]) for cx in (box[0], box[2]) for cy in (box[1], box[3])) + 2
        box = (int(pivot[0] - r), int(pivot[1] - r), int(pivot[0] + r) + 1, int(pivot[1] + r) + 1)
    box = (max(0, box[0]), max(0, box[1]), min(lay.size[0], box[2]), min(lay.size[1], box[3]))
    if box[2] <= box[0] or box[3] <= box[1]:
        return out
    lay = lay.crop(box)
    ox, oy_ = box[0], box[1]
    if rot and pivot:
        lay = lay.rotate(math.degrees(rot), center=(pivot[0] - ox, pivot[1] - oy_), resample=Image.BICUBIC)
    if tint and amount > 0:
        r, g, b, a = lay.split()
        lay = Image.merge("RGBA", (*Image.blend(Image.merge("RGB", (r, g, b)), Image.new("RGB", lay.size, tint), amount).split(), a))
    if split is not None:
        ly = int(round(zy(split))) - oy_
        if ly < lay.size[1]:
            ly = max(0, ly)
            bot = lay.crop((0, ly, lay.size[0], lay.size[1]))
            r, g, b, a = bot.split()
            bot = Image.merge("RGBA", (*Image.blend(Image.merge("RGB", (r, g, b)), Image.new("RGB", bot.size, (40, 132, 138)), 0.55).split(),
                                       a.point(lambda v: int(v * 0.5))))
            lay.paste(bot, (0, ly))
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    ink.img.paste(lay, (ox, oy_), lay)
    _redraw(ink)
    return out


def rot_pt(p, pivot, ang):
    """Where a point goes under on_layer's turn (PIL turns counter-clockwise on screen)."""
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    c, s = math.cos(ang), math.sin(ang)
    return (pivot[0] + dx * c + dy * s, pivot[1] - dx * s + dy * c)


@lru_cache(maxsize=None)
def teeth_image(tidy):
    """What the lamp throws on the door: the child's teeth (wobbly, the second jaw outside the ring) or the
    ruled-straight wrong version. Dark lines on light, as porch.projection wants."""
    im = Image.new("RGB", (232, 264), (250, 240, 214))
    town.picture(im, "jaw", 116, 132, 190, tidy=tidy, color=(58, 38, 22), width=5.0)
    return im


@lru_cache(maxsize=64)
def _lid(look, size, paw):
    """The label on a can's lid: the teeth, ruled (on cold white) or as the child drew them (on the child's
    cream paper, both jaws), in pencil thin enough to read as a drawing when the can is large in frame."""
    S = 4
    n = int(size * S)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tidy = look == "tidy"
    d.ellipse([1, 1, n - 2, n - 2], fill=(222, 230, 240, 255) if tidy else (248, 236, 204, 255), outline=(44, 38, 50, 255), width=max(2, S // 2))
    town.picture(im, "jaw_only" if size < 24 else "jaw", n / 2, n * (0.5 if tidy else 0.47), n * 0.7, tidy=tidy,
                 color=(36, 54, 96) if tidy else (104, 44, 26), width=max(2.0, n * (0.034 if size >= 40 else 0.05)))
    if paw:
        props.paw_print(im, n * 0.76, n * 0.8, n / 48.0 * 0.8, angle=-18, wet=0.6)
    return im.resize((int(size), int(size)), Image.LANCZOS)


def my_reel(ink, x, y, s, look, paw=False, tilt=1.0, angle=0.0, under=False, alpha=1.0, wet=0.6, lit=1.0, tail=0.0, sway=0.0):
    """A can centred at (x, y). look = a reel number (its real frame on the lid), or 'tidy' / 'wobbly':
    the two lids the defining passage turns on. tail 0..1 = a length of film hanging out of it and
    swinging (sway): with the metal rim and the wall under the lid it is what makes this a can of film
    in a mouth and not a disc in the air."""
    ret = (x, y)
    is_ink = hasattr(ink, "img")
    if is_ink:
        x, y, s = zx(x), zy(y), s * zs()
    kw = dict(tint=TEAL, tint_amount=0.3) if under else {}
    R = 24.0 * s
    if tail > 0 and is_ink and alpha >= 1:                    # the film: out of the can's lower edge, down, dripping
        a = (x + R * 0.55, y + R * 0.7 * tilt)
        b = (a[0] + R * (0.5 + 0.35 * sway) * tail, a[1] + R * 1.25 * tail)
        props.film_strip(ink, look if isinstance(look, int) else props.REEL_RETRIEVER, a, b, sag=R * 0.22 * (1 + 0.5 * sway), s=max(0.5, 0.62 * s), lit=0.25)
    if isinstance(look, int):
        props.reel(ink, look, x, y, s, tilt=tilt, angle=angle, paw=paw, wet=wet, alpha=alpha, lit=lit, **kw)
        return ret
    props.reel(ink, props.REEL_RETRIEVER, x, y, s, tilt=tilt, angle=angle, wet=wet, face=False, alpha=alpha, **kw)
    if tilt > 0.55:
        d = 2 * R * 0.7
        lid = _lid(look, round(d), bool(paw))
        if tilt < 0.99:
            lid = lid.resize((lid.size[0], max(2, int(lid.size[1] * tilt))), Image.LANCZOS)
        if angle:
            lid = lid.rotate(-angle, resample=Image.BICUBIC, expand=True)
        if under:
            r, g, b, a = lid.split()
            lid = Image.merge("RGBA", (*Image.blend(Image.merge("RGB", (r, g, b)), Image.new("RGB", lid.size, TEAL), 0.25).split(), a))
        if alpha < 1:
            lid.putalpha(lid.getchannel("A").point(lambda v: int(v * alpha)))
        img = ink.img if is_ink else ink
        img.paste(lid, (int(round(x - lid.size[0] / 2)), int(round(y - lid.size[1] / 2))), lid)
        if is_ink:
            _redraw(ink)
    return ret


def big_look(f):
    return "tidy" if (when("big", "come_up") is None or f < when("big", "fix") + 0.95) else "wobbly"


# ---------------------------------------------------------------- the makes ---

MAKES = ("herder", "digger", "big", "mid", "small", "sheep", "blood", "terrier", "looker")
MAKE_S = dict(herder=HS, digger=GS, big=RS, mid=RS, small=RS, sheep=RS, blood=RS * 0.95, terrier=0.72, looker=0.34)


def draw_make(ink, make, x, y, f, act="stand", facing=1, k=1.0, carry=None, under=False, rot=0.0, alpha=1.0, look=0.0, split=None):
    """One pack dog of a given make. act: stand | walk | swim. k scales it. rot turns the whole dog
    (radians, nose up when positive for a dog facing right). Returns its screen anchors."""
    x, y, s = zx(x), zy(y), MAKE_S[make] * k * zs()
    uw = dict(tint=kb.WATER, tint_amount=0.3, shadow=False) if under else {}
    if make in ("big", "mid", "small", "sheep", "blood", "terrier"):
        name = {"big": "retriever", "mid": "retriever", "small": "retriever", "sheep": "sheepdog", "blood": "bloodhound",
                "terrier": "terrier"}[make]
        action = {"stand": "wait", "walk": "carry" if carry else "walk", "swim": "swim"}[act]
        kw = dict(uw)
        if name == "retriever":
            kw["size"] = make
        if action == "wait":
            kw["arrive"] = 0
        if look:
            kw["look"] = look
        fn = getattr(kb, name)

        def go(im):
            return fn(im, x, y, action, f, scale=s, facing=facing, carry=carry, **kw)
        if rot or alpha < 1 or split is not None:
            a = on_layer(ink, go, rot=rot * facing, pivot=(x, y), alpha=alpha, split=split)
            if rot:
                a = dict(a)
                a["mouth"] = rot_pt(a["mouth"], (x, y), rot * facing)
            return unz_a(a)
        return unz_a(go(ink))
    action = {"stand": "wait", "walk": "walk", "swim": "swim"}[act]
    if make == "herder":
        def go(im):
            return ka.herding_dog(im, x, y, s, facing, action, t=f, look=math.degrees(look))
    elif make == "digger":
        def go(im):
            return ka.digger(im, x, y, s, facing, action, t=f, look=math.degrees(look), spray=False, post=False)
    else:
        def go(im):
            return ka.old_dog(im, x, y, s, facing, action, t=f, paper=(150, 150, 150) if not under else (128, 150, 152))
    if rot or alpha < 1 or split is not None or (under and make != "digger"):
        a = on_layer(ink, go, rot=rot * facing, pivot=(x, y), alpha=alpha, split=split,
                     tint=kb.WATER if under else None, amount=0.22 if under else 0.0)
        if rot:
            a = dict(a)
            a["mouth"] = rot_pt(a["mouth"], (x, y), rot * facing)
        return unz_a(a)
    return unz_a(go(ink))


# ====================================================================== #
#  4 · PERSISTENT WORLD DATA: the cans, the pebbles, the pack            #
# ====================================================================== #

STACK_X = (236.0, 262.0, 289.0, 318.0, 346.0, 374.0)        # six leaning piles, step's foot to the sill's first boards
STACK_H = (10, 13, 9, 7, 6, 3)                              # 48 cans in the piles
STACK_LEAN = (1.1, -0.9, 0.8, -1.2, 1.0, -0.6)
POPUPS = (158.05, 161.45, 162.15, 162.85, 167.0)           # small dogs at the porch edge, a can each, out of the action's line
N_PILED = sum(STACK_H)


@lru_cache(maxsize=None)
def ledger():
    """Every can laid in S6: [(film time, pile, reel number, paw print)], in the order they are laid.
    53 in the record = 2 in the S3 pile + the refused one on the step + 48 here + the retriever's
    changed one + the lead dog's last one."""
    used = {props.REEL_FIRST, props.REEL_HALF, props.REEL_LEAD, REELS["big"]["n"], REELS["lead"]["n"]}
    pool = [n for n in range(props.N_REELS) if n not in used]
    first = [REELS[k]["n"] for k in ("herder", "digger", "sheep")]
    rest = [n for n in pool if n not in first]
    random.Random(6).shuffle(rest)
    order = first + rest
    assert len(order) == N_PILED, len(order)
    times = [when(k, "lay") + 0.15 for k in ("herder", "digger", "sheep")] + [tp + 0.35 for tp in POPUPS]
    early_pile = [2, 1, 2, 0, 1, 0, 2, 1]
    room = list(STACK_H)
    for p in early_pile:
        room[p] -= 1
    late = [p for p in range(6) for _ in range(room[p])]
    random.Random(11).shuffle(late)
    nlate = len(late)
    times += [170.9 + 2.4 * i / (nlate - 1) for i in range(nlate)]          # the pile jumps while we are below
    piles = early_pile + late
    paw_idx = {3, 9, 14, 21, 27, 33, 40, 46}                                  # eight more things were written
    out = [(times[i], piles[i], order[i], i in paw_idx) for i in range(N_PILED)]
    return sorted(out, key=lambda e: e[0])


def cans_at(f):
    """How many cans are on the boards at f (the record's 53 at the end)."""
    n = 3 + sum(1 for e in ledger() if e[0] <= f)
    if after("big", "lay", f) >= 0.1:
        n += 1
    if after("lead", "lay", f) >= 0.45:
        n += 1
    return n


_stack_cache = {}


def draw_stacks(ink, f, oy):
    counts = tuple(sum(1 for e in ledger() if e[1] == p and e[0] <= f) for p in range(6))
    if counts not in _stack_cache:
        if len(_stack_cache) > 40:
            _stack_cache.clear()
        lay = Image.new("RGBA", (420, 200), (0, 0, 0, 0))
        for p in range(6):
            es = [e for e in ledger() if e[1] == p and e[0] <= f]
            if es:
                props.reel_stack(lay, [e[2] for e in es], STACK_X[p] - 200, 190, 0.42, lean=STACK_LEAN[p], seed=p,
                                 paws={e[2] for e in es if e[3]})
        _stack_cache[counts] = lay
    lay = _stack_cache[counts]
    ink.img.paste(lay, (200, int(round(392 - 190 - oy))), lay)
    _redraw(ink)
    # a can that has just landed sits up for a moment
    for (tl, p, n, paw) in ledger():
        if 0 <= f - tl < 0.25 and not (170.8 <= tl < 173.4):
            h = sum(1 for e in ledger() if e[1] == p and e[0] <= f)
            props.reel(ink, n, STACK_X[p], 392 - oy - 6 - 4.0 * h - 7 * bump((f - tl) / 0.25), 0.42, tilt=0.6, wet=1)


PEBBLES = "wwggwgwggwgg" + "ggwgggwggggwgggwgg" + "gggwggggwgggggwggggwggggwggggwggggwgg"      # 67 asks; 16 white, never two together
PEB_T = ([153.4, 153.9, 154.3, 154.8, 155.2, 155.6, 156.1, 156.5, 157.5, 158.1, 158.9, 159.5, 160.1, 160.7]
         + [170.9 + 2.4 * i / 22 for i in range(23)])
PEB_SEEN = (153.4, 154.3, 155.2, 156.1, 158.9, 160.1)       # the ones the hand is seen to set down


def pebbles_at(f):
    return 30 + sum(1 for tk in PEB_T if tk <= f)


def pebble_xy(k):
    """Pebbles past the thirtieth lie on top of the two rows porch.rail draws: the heap has grown."""
    if k < 30:
        return porch.pebble_spot(k)
    j = k - 30
    row = j // 14
    return (42 + (j % 14) * 12.4 + (5 if row % 2 else 0) + 2.5 * math.sin(k * 2.3), porch.RAIL_Y - 16 - 4.6 * row + 1.2 * math.sin(k * 1.7))


def draw_more_pebbles(ink, f, oy):
    n = pebbles_at(f)
    if n <= 30 or 400 - oy <= 0:
        return
    d = ink.d
    for k in range(30, n):
        x, y = pebble_xy(k)
        y -= oy
        col = (236, 228, 214) if PEBBLES[k] == "w" else (128, 118, 138)
        r = 3.3 + 0.9 * (0.5 + 0.5 * math.sin(k * 3.1))
        d.ellipse([x - r + 1, y - r * 0.7 + 1.5, x + r + 1, y + r * 0.7 + 1.5], fill=(20, 12, 34, 110))
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=col + (255,))
        d.ellipse([x - r * 0.5, y - r * 0.55, x + r * 0.2, y - r * 0.1], fill=(255, 250, 240, 120))


SIX = {   # the six who go with it: where each stands at the waterline, how it gets there, frames after the lead
    "sheep": dict(spot=(612.0, 390.0), come=(153.05, 153.9), frm=(790.0, 326.0), lag=1, entry=586.0),
    "herder": dict(spot=(578.0, 391.0), come=(153.0, 153.8), frm=(700.0, 384.0), lag=1, entry=552.0),
    "digger": dict(spot=(642.0, 389.0), come=(153.2, 154.1), frm=(668.0, 389.0), lag=2, entry=616.0),
    "big": dict(spot=(676.0, 388.0), come=(153.1, 154.2), frm=(990.0, 378.0), lag=2, entry=650.0),
    "mid": dict(spot=(708.0, 389.0), come=(153.3, 154.3), frm=(1000.0, 380.0), lag=3, entry=684.0),
    "small": dict(spot=(735.0, 390.0), come=(153.45, 154.4), frm=(1010.0, 382.0), lag=1, entry=716.0),
}
LEAP = 0.30
NIGHT = 0.9                                  # S5's night under the line (town.back and town.grade)


@lru_cache(maxsize=None)
def curtain():
    """The rest of the third pack: thirty-one more, so that thirty-seven go under in beat 6.3."""
    rs = random.Random(37)
    out = []
    xs = [318 + 622 * (i + 0.5) / 31 for i in range(31)]
    rs.shuffle(xs)
    for i in range(31):
        mk = MAKES[(i * 4 + i // 9) % len(MAKES)]
        x = xs[i] + rs.uniform(-8, 8)
        out.append(dict(make=mk, k=rs.uniform(0.62, 1.0) * (0.8 if mk in ("herder", "digger") else 1.0), x=x,
                        go=0.45 + 1.0 * i / 30 + rs.uniform(-0.05, 0.05), dx=rs.uniform(-70, 70), deep=rs.uniform(650, 800),
                        face=1 if rs.random() < 0.5 else -1, v=rs.uniform(150, 215), seed=i))
    return out


@lru_cache(maxsize=None)
def lantern_pack():
    """The last pack, seventeen, still working far below with lanterns (the last shot only)."""
    rs = random.Random(17)
    out = []
    for i in range(17):
        mk = MAKES[(i * 2 + 1) % len(MAKES)]
        out.append(dict(make=mk, x=40 + 880 * (i + 0.5) / 17 + rs.uniform(-18, 18), y=rs.uniform(646, 684), k=rs.uniform(0.36, 0.5),
                        face=1 if rs.random() < 0.5 else -1, ph=rs.uniform(0, 6.28), seed=i))
    return out


SLEEPERS = [   # the eleven who came up with nothing (seven grey-muzzled lookers, four terriers), where S5 left them asleep
    ("looker", 731, 395), ("looker", 761, 396), ("terrier", 791, 395), ("looker", 821, 396), ("looker", 851, 395),
    ("looker", 716, 401), ("terrier", 746, 402), ("looker", 776, 401), ("terrier", 806, 402), ("looker", 836, 401), ("terrier", 866, 402),
]
HERD_SPOT = {   # the rest of the herd round them, where S5 left them: world x, dy, size, facing, when she folds down
    "second": (892.0, 0.0, 1.0, -1, 144.9), "fourth": (842.0, -3.0, 0.96, -1, 145.6), "sixth": (956.0, 0.0, 1.0, 1, 147.3),
    "fifth": (926.0, 0.0, 1.0, 1, 146.9), "mother": (718.0, -4.0, 0.96, 1, 146.3),
}
CALF_AT = (706.0, 392.5)
RET_REST = (684.0, 391.0)                    # where the big retriever stops, at the meadow's edge, beside the calf


# ====================================================================== #
#  5 · THE CAST, EACH READ OFF ITS MACHINE                               #
# ====================================================================== #

def old_x(f):
    ts = when("old", "shift")
    return lerp(OLD_X0, OLD_X1, ease(f, ts, ts + 0.8)) if ts is not None else OLD_X0


def draw_old(ink, f, oy, where):
    """where: 'sill' until it leaves the board, 'strip' when it goes to the cow."""
    st, since = at("old", f)
    on_strip = st in ("walk", "lie_down", "beside")
    if (where == "strip") != on_strip:
        return None
    x, y = old_x(f), SILL_Y - oy
    kw = dict(paper=(182, 178, 170))

    def D(action="lie", p=0.0, dy=0.0, P=None):
        return OLD(ink, x, y + dy, OLD_S, 1, action, t=f, p=p, P=P, **kw)

    def other_way(P):
        P = dict(P)
        P["sx"] = -P["sx"]
        return P

    if st == "lie":
        return D("lie")
    if st == "shift":
        return D("lift_head", 0.7 * bump(since / 0.8), dy=-2 * bump(since / 0.8))
    if st == "glance":
        return D("lift_head", ease(since, 0.0, 0.3))
    if st == "blink":
        return D("look", lerp(0.3, 0.72, since / 0.55))
    if st == "chin":
        return D("lift_head", 1 - ease(since, 0.0, 0.25))
    if st == "raise_":
        return D("lift_head", ease(since, 0.1, 1.08))
    if st == "long_look":
        return D("look", 0.0)                                                         # the hold: nothing of it moves
    if st == "turn_back":
        return D("turn_back", clamp(since / 2.5))
    if st == "back":
        P = old_P("back")
        P["bdy"] = P.get("bdy", 0.0) + 0.9 * math.sin((f - when("old", "back")) * 1.5)   # a back that breathes
        return D(P=P)
    if st == "look_over":
        return D("look_over", clamp(since / 0.5))
    if st == "let_pass":
        return D("let_pass", clamp(since / 0.58))
    if st == "passed":
        return D("let_pass", 1.0)
    if st == "rise_turn":
        # it lets its tail down and gathers itself (no fade: one pose is carried into the next), gets up
        # back end first and comes round to face the cow
        u = clamp(since / 0.8)
        if u < 0.24:
            P = ka._oblend(old_P("let_pass", p=1.0), other_way(old_P("turn_back", p=0.0)), smooth(u / 0.24))
            P["sx"] = -1.0
        else:
            P = other_way(old_P("turn_back", p=0.68 * ease(u, 0.24, 1.0)))
        return D(P=P)
    tx = COW_X1 - 106.0                                                                # under her chin, against her chest
    if st == "walk":
        u = ease(since, 0.0, 1.1)
        return OLD(ink, lerp(x, tx, u), lerp(SILL_Y, 389.0, clamp(since / 0.5)) - oy, OLD_S, 1, "walk", t=f, **kw)
    if st == "lie_down":
        return OLD(ink, tx, 389.0 - oy, OLD_S, 1, "lie_down", p=ease(since, 0.0, 0.9), **kw)
    return OLD(ink, tx, 389.0 - oy, OLD_S, 1, "lie", **kw)


def old_place(f):
    """World point where a reel is laid behind the old dog once it has made room."""
    return (old_x(f) + 86.0, SILL_Y)


NOSE_STEP = 18.0                             # the one step she takes up to the stuck dog, and back as she draws it with her
NUDGE_PX = 30.0                              # how far her muzzle rolls the wooden dog back along the board
BACK_OFF = 10.0                              # how far it has already backed away from the old dog's back, looking up at her


WEAVE = ("stand", "fold1", "lying", "get_up")   # REPAIR: in these states she used to lie down in the meadow and do nothing.
# What she does now, read off the same clocks (the person's no at 148.0, the dog's ears at 150.0, its turn at 153.0):
#   to 148.0    stands where S5 left her, chewing
#   148.0       the head shakes: she stops chewing, both ears come round
#   149.0       the dog's tail has stopped: she walks down to it, 2.2 s, and stands behind it on the strip
#   151.2       her head comes down onto its back; she breathes out on it (151.2 to 152.9)
#   153.0       the dog turns round under her chin: their noses meet; it goes, and her head comes up after it
W_NOTICE, W_GO, W_THERE, W_AWAY = 148.0, 149.0, 151.2, 153.75


@lru_cache(maxsize=512)
def lead_pts(f):
    """World joints of the lead dog on the sill at f (found by drawing it on a scrap sheet)."""
    scrap = kit.Ink(0.0, 0)
    was, ZM.on = ZM.on, False
    try:
        j = draw_lead(scrap, f, 0, "sill")
    finally:
        ZM.on = was
    return j


def weave_u(f):
    return ease(f, W_GO, W_THERE - 0.15)


def cow_xy(f):
    st, since = at("cow", f)
    if st in WEAVE:
        u = weave_u(f)
        return lerp(COW_X0, COW_NEAR, u), lerp(porch.meadow_y(COW_X0), 388.0, u)
    if st == "walk":                                          # she gives way to the pack: back along the strip to her drinking place
        u = clamp(since / 2.0)
        u = u * u * (3 - 2 * u) * 0.5 + u * 0.5
        return lerp(COW_NEAR, COW_X1, u), 388.0
    if st == "nose":
        return COW_X1 - NOSE_STEP * (ease(since, 0.0, 0.5) - ease(since, 0.6, 1.15)), 388.0
    return COW_X1, 388.0


def cow_target(f, oy):
    """WORLD point her muzzle goes to: the reel the sheepdog holds up; the wooden dog's chest."""
    st, since = at("cow", f)
    if st in WEAVE and f >= W_THERE - 0.4:
        j = lead_pts(f)
        if not j:
            return None
        back = ((j["withers"][0] + j["hip"][0]) / 2 + 12.0, min(j["withers"][1], j["hip"][1]) - 1.0)
        if at("lead", f)[0] in ("turn", "look_pack"):        # it has turned round under her chin: nose to nose
            n = j["nose"]
            w = ease(f, 152.97, 153.45)
            return (lerp(back[0], n[0] + 7.0, w), lerp(back[1], n[1] - 3.0, w))
        return back
    if st == "nose":                                          # the rim of the can it is holding, on the old dog's side of it
        cx_, cy_ = big_can_world(f)
        return (cx_ - 24.0 * BIG_REEL - 3.0, cy_ + 3.0)
    if st == "smell":
        rx, ry = sheep_reel_at(f)
        return (rx - 4, ry - 16)
    return None


@lru_cache(maxsize=256)
def sheep_reel_at(f):
    """World point of the can the sheepdog holds up (found by drawing the dog on a scrap sheet)."""
    scrap = kit.Ink(0.0, 0)
    was, ZM.on = ZM.on, False
    try:
        a = {}
        draw_passer(scrap, "sheep", f, 0, "sill", a)
    finally:
        ZM.on = was
    return a.get("sheep_reel", (PRESENT_X - 30.0, 352.0))


def cow_pose(f):
    st, since = at("cow", f)
    if st in WEAVE:
        x, _ = cow_xy(f)
        if f < W_GO:                                          # watching; at the no she stops chewing and her ears come round
            q = herd.stand(f, "lead", chew=1 - ease(f, W_NOTICE + 0.15, W_NOTICE + 0.45), alert=0.6)
            return herd.notice(q, ease(f, W_NOTICE + 0.15, W_NOTICE + 0.55))
        if f < W_THERE - 0.15:                                # down to the dog
            q = herd.step_pose("lead", (COW_X0 - x) / herd.S, rest=ease(f, W_THERE - 0.6, W_THERE - 0.15), t=f, chew=0)
            return herd.notice(q, 0.7)
        # her head on its back: nose_touch's clock (contact 0.75, held, breath at 1.6), held until the dog turns
        tau = f - (W_THERE - 0.15)
        tau = tau if tau < 1.5 else (1.5 if f < W_AWAY - 0.35 else 1.5 + (f - (W_AWAY - 0.35)) * 1.6)
        q = herd.nose_touch(min(tau, 2.6), f, "lead")
        q["_face"] = 84.0
        return q
    if st == "walk":
        x, _ = cow_xy(f)
        return herd.notice(herd.step_pose("lead", (COW_X0 - x) / herd.S, rest=ease(since, 1.55, 2.0), t=f), 1 - ease(since, 1.2, 2.0))
    if st == "watch":
        return herd.stand(f, "lead", chew=1, alert=0.25)
    if st == "smell":
        return herd.smell(since * 1.75, "lead")
    if st == "still":
        q = herd.notice(herd.stand(164.0, "lead", chew=0, alert=0.35), 1.0)             # she does not chew
        ost, osince = at("old", f)
        if ost == "turn_back":                                                         # ... but she watches it get up and go round:
            u = clamp(osince / 2.5)                                                    # her head follows, one ear goes back and comes again
            q["neck"] = q["neck"] + 7.0 * math.sin(math.pi * u) + 3.0 * ease(u, 0.7, 1.0)
            q["head"] = q["head"] + 6.0 * bump((u - 0.15) / 0.7)
            q["ear"] = q["ear"] - 26.0 * bump((u - 0.3) / 0.3)
            q["tail"] = tuple(v + 10.0 * math.sin(osince * 5.0) * bump((u - 0.5) / 0.4) for v in q["tail"])
        elif ost == "back":                                                            # the dog looks up at her: her head comes down to it
            ts = after("big", "told", f)
            q["neck"] = q["neck"] + 3.0 + 10.0 * ease(ts, 0.7, 1.15)
            q["head"] = q["head"] + 5.0 * ease(ts, 0.75, 1.15)
        return q
    if st == "nose":
        # she stops being a watcher. One step up to it (0..0.5), the head down in front of its chest (contact
        # at 0.55), one slow shove as she steps back and draws it with her (0.55..1.1), the head lifts away.
        x, _ = cow_xy(f)
        tau = since * (0.5 / 0.55) if since < 0.55 else (0.5 + (since - 0.55) * (0.6 / 0.55) if since < 1.1 else 1.3 + (since - 1.1) * (0.7 / 0.3))
        q = herd.nudge(tau, "lead")
        q["_face"] = 86.0                                     # the face hangs: the head comes down in front of the dog, not over it
        moving = clamp(1.6 * (bump(since / 0.5) + bump((since - 0.6) / 0.55)))
        legs = herd.step_pose("lead", (COW_X0 - x) / herd.S, rest=1.0 - moving, t=f, chew=0)
        for k in ("nf", "ff", "nh", "fh", "hip", "shoulder"):
            q[k] = legs[k]
        q["dy"] = legs["dy"]
        q["bell"] = legs.get("bell", 0.0) + 14.0 * math.sin(since * 9.0) * math.exp(-1.2 * since)
        return q
    if st == "chew":
        return herd.stand(f, "lead", chew=1, alert=0.2)
    if st == "fold":
        return herd.fold_down(clamp(since / 2.0), "lead")
    p = herd.lie(f, "lead", chew=1, alert=0.15)
    return herd.notice(p, 0.8 * ease(f, 177.2, 177.8)) if f > 177.2 else p            # her ears go to the radio


def draw_cow(ink, f, oy, anchors, only=None):
    st, since = at("cow", f)
    x, y = cow_xy(f)
    nose = cow_target(f, oy)
    a = COW(ink, "lead", cow_pose(f), x, y, facing=-1, oy=oy, nose_to=nose, only=only, rim=0.22 if x < 700 else None)
    anchors["cow"] = a
    if only:
        return a
    if st in WEAVE and 151.95 <= f < 152.5:                   # she breathes out on it
        BREATH(ink, a["muzzle"][0], a["muzzle"][1], clamp((f - 151.95) / 0.5), a["facing"], size=1.1)
    if st == "smell" and a.get("breath"):
        BREATH(ink, a["muzzle"][0], a["muzzle"][1], a["breath"], a["facing"])
    if st == "nose" and 1.0 < since < 1.4:
        BREATH(ink, a["muzzle"][0], a["muzzle"][1], clamp((since - 1.0) / 0.4), a["facing"], size=1.1)
    if st == "fold" and since > 1.7:
        BREATH(ink, a["muzzle"][0], a["muzzle"][1], clamp((since - 1.7) / 0.6), a["facing"], size=1.3)
    return a


def draw_herd(ink, f, oy):
    """The rest of the herd, folding down one at a time, and the eleven asleep among them."""
    still = at("old", f)[0] == "long_look"                # while the old dog looks, no cow chews
    for who, (x, dy, sc, facing, t_fold) in HERD_SPOT.items():
        y = porch.meadow_y(min(x, 958)) + dy
        if f < t_fold:
            pose = herd.warm(f, who)
        elif f < t_fold + 2.0:
            pose = herd.fold_down((f - t_fold) / 2.0, who)
        elif f < 174.5:
            pose = herd.lie(164.0 if still else f, who, chew=0 if still else 1)
        else:
            pose = herd.tween(herd.lie(f, who, chew=1), herd.sleep(f, who), ease(f, 174.5, 176.5), "inout", who)
        a = herd.cow(ink, who, pose, x, y, herd.S * sc, facing, oy, rim=0.0)
        if f < 148.0:
            herd.steam_on(ink, f, a, amount=0.4 * (1 - ease(f, 144.0, 148.0)))


def draw_heap(ink, f, oy):
    for i, (mk, x, y) in enumerate(SLEEPERS):
        if mk == "looker":
            ka.old_dog(ink, x, y - oy, 0.3 + 0.03 * (i % 3), -1 if i % 2 else 1, "lie", paper=(190, 188, 182), eye=0)
        else:
            kb.terrier(ink, x, y - oy, "wait", 10.0, scale=0.62, facing=-1 if i % 2 else 1, sit=True)


def calf_state(f):
    """(pose, facing, turn, nose_to): asleep in the heap; woken by the wooden dog; down again against it."""
    tr = when("big", "rest", 175.0)
    back = (RET_REST[0] + 20, RET_REST[1] - 33)
    if f < tr - 1.5:
        return herd.sleep(f, "calf"), 1, None, None
    if f < tr - 0.9:                                     # it wakes: something on wheels is coming
        return herd.tween(herd.sleep(f, "calf"), herd.lie(f, "calf", chew=0, alert=1.0), ease(f, tr - 1.5, tr - 1.0), "inout", "calf"), 1, None, None
    if f < tr - 0.2:                                     # up, hind end first
        return herd.get_up(clamp((f - (tr - 0.9)) / 0.7), "calf"), 1, None, None
    if f < tr + 0.3:                                     # round to look at it
        return herd.stand(f, "calf", chew=0, alert=1.0), 1, ease(f, tr - 0.2, tr + 0.3), None
    if f < tr + 1.5:
        return herd.fold_down(clamp((f - (tr + 0.3)) / 1.2), "calf"), -1, None, None
    u = ease(f, tr + 1.5, tr + 2.3)                      # its chin goes down on the wooden back, and its eye shuts
    up = herd.lie(f, "calf", chew=0, alert=0.5)
    return herd.with_(up, eye=up.get("eye", 0.8) * (1 - u), _nose=u), -1, None, back


def draw_calf(ink, f, oy):
    pose, facing, turn, nose = calf_state(f)
    tr = when("big", "rest", 175.0)
    x = CALF_AT[0] + 22 * ease(f, tr - 0.2, tr + 0.35)       # one step round, to lie against it
    if turn is not None:                                      # a card calf comes round in one flip, never edge-on
        turn = min(turn, 0.35) if turn < 0.5 else max(turn, 0.65)
    herd.cow(ink, "calf", pose, x, CALF_AT[1], facing=facing, oy=oy, nose_to=nose, turn=turn, rim=0.55)


# ------------------------------------------------------------------ lead ---

LEAD_AT = (398.0, SILL_Y)                    # two steps toward the person as the reel is taken (S5 leaves it at 440)
LEAD_EDGE = (548.0, SILL_Y)
LEAD_ENTRY = 588.0
LEAD_LINE = (664.0, 425.0)
LEAD_LINE2 = (724.0, 425.0)                 # well back: the wooden one needs the water's edge twice
LEAD_LAY = (500.0, SILL_Y)
LEAD_LIE = (462.0, SILL_Y)


def lead_swim(f):
    """Where the lead dog is under water between its dive and its coming up: (x, y, pitch, going)."""
    td = when("lead", "dive")
    tu = when("lead", "come_up")
    if f < tu - 1.6:
        u = f - td - LEAP
        return (LEAD_ENTRY + 62 * (1 - math.exp(-u * 0.9)) + 26 * u, 406 + 150 * u, -0.7, "down")
    u = clamp((f - (tu - 1.6)) / 2.1)
    return (lerp(760, LEAD_LINE[0] + 6, smooth(u)), lerp(640, 418, u ** 0.8), 0.75, "up")


def draw_lead(ink, f, oy, where):
    """where: 'sill' (on the boards), 'under' (swimming), 'front' (in the air)."""
    st, since = at("lead", f)
    y0 = SILL_Y - oy
    reel = lambda: props.reel_sprite(REELS["lead"]["n"], tail=0.4, wet=1)     # noqa: E731
    if st in ("pleased", "stilled", "ears_down", "hold", "look_bubble"):
        if where != "sill":
            return None
        lx = lerp(440.0, LEAD_AT[0], ramp(f, 144.25, 145.2))
        if st == "pleased":
            pose = dog.pleased(f)
            if 144.25 < f < 145.2:                           # it follows the reel
                pose = dog.blend(dog.walk((f - 144.25) * 1.05), pose, {"ears": 1.0, "tail": 1.0, "head": 1.0})
        else:
            tq = when("lead", "stilled")
            frozen = dog.pleased(tq)
            if st == "stilled":                              # the tail stops mid-wag; the mouth shuts; the feet stop treading
                pose = dog.blend(frozen, dog.blend(dog.watch(tq), frozen, {"tail": 1.0}), ease(since, 0.0, 0.5))
            else:
                te = when("lead", "ears_down")
                still = dog.blend(frozen, dog.blend(dog.watch(tq), frozen, {"tail": 1.0}), 1.0)
                down = dog.ears_down(f - te)
                pose = dog.blend(still, down, ease(f - te, 0.0, 0.35))
                pose["ear"] = lerp(still["ear"], down["ear"], ease(f - te, 0.45, 1.0))          # the torn ear last
                pose["ear_f"] = lerp(still["ear_f"], down["ear_f"], ease(f - te, 0.05, 0.6))
                up = ease(f - te, 0.55, 1.0)                 # ... and its eyes go down to the can that has come back
                pose["head"] += -0.26 * up
                pose["neck"] += -0.16 * up
                if st == "hold":
                    pose = dog.ears_down(9.0)                # it does not argue: it looks at the can at its feet
                    pose["head"] += -0.26
                    pose["neck"] += -0.16
                    lean = bump((f - 151.75) / 0.9)          # ... and gives a little under the cow's muzzle
                    pose["head"] += -0.05 * lean
                if st == "look_bubble":                      # down through the water at the child's page
                    pose = dog.ears_down(9.0)
                    pose["head"] += lerp(-0.26, -0.42, ease(since, 0.0, 0.3))
                    pose["neck"] += lerp(-0.16, -0.3, ease(since, 0.0, 0.3))
        return DOG(ink, pose, lx, y0, scale=DS, facing=-1)
    if st == "turn":
        if where != "sill":
            return None
        face = lerp(-1.0, 1.0, ease(since, 0.1, 0.6))
        low = dog.ears_down(9.0)
        low["head"] -= 0.42
        low["neck"] -= 0.3
        pose = dog.blend(low, dog.watch(f), ease(since, 0.0, 0.7))
        if abs(face) < FLIP_MIN:                              # a paper dog comes round in one flip, never edge-on
            face = FLIP_MIN if face >= 0 else -FLIP_MIN
        return DOG(ink, pose, LEAD_AT[0], y0 - 3 * bump(since / 0.7), scale=DS, facing=face)
    if st == "look_pack":
        if where != "sill":
            return None
        if since < 0.4:                                       # one short look along the bank
            return DOG(ink, dog.watch(f), LEAD_AT[0], y0, scale=DS, facing=1)
        u = clamp((since - 0.4) / 0.62)
        x = lerp(LEAD_AT[0], LEAD_EDGE[0], u)
        if u < 1:
            return DOG(ink, dog.trot(since * 1.6), x, y0, scale=DS, facing=1)
        pose = dog.blend(dog.watch(f), dog.dig(0.05), 0.45)   # gathers itself
        return DOG(ink, pose, x, y0, scale=DS, facing=1)
    if st in ("dive", "under"):
        u = f - when("lead", "dive")
        if u < LEAP:
            if where != "front":
                return None
            v = u / LEAP
            x, y = lerp(LEAD_EDGE[0], LEAD_ENTRY, v), lerp(SILL_Y - 26, 398, v * v) - 20 * math.sin(math.pi * v)
            return DOG(ink, dog.swim_down(f * 1.2, steep=0.3 + 0.5 * v), x, y - oy, scale=DS, facing=1, shadow=False)
        if where != "under":
            return None
        x, y, pitch, going = lead_swim(f)
        if going == "down":
            return DOG(ink, dog.swim_down(f, steep=0.72), x, y - oy, scale=DS, facing=1, tint=TEAL, tint_amount=0.3, shadow=False)
        return DOG(ink, dog.holding(dog.carry_page(f, gait="swim_up"), "reel"), x, y - oy, scale=DS, facing=-1, carry=reel(),
                            tint=TEAL, tint_amount=0.3, shadow=False)
    if st in ("come_up", "in_line", "step_back", "watch_line"):
        if where != "sill":
            return None
        if st == "come_up" and since < 0.3:
            return None                                       # still under: drawn by 'under'
        x = LEAD_LINE[0]
        if st == "step_back":
            x = lerp(LEAD_LINE[0], LEAD_LINE2[0], ease(since, 0.05, 0.55))
        elif st == "watch_line":
            x = LEAD_LINE2[0]
        pose = dog.holding(dog.wade(since * 0.8 if st == "step_back" else 0.0, depth=0.8), "reel")
        base = dog.holding(dog.watch(164.0 if at("old", f)[0] == "long_look" else f), "reel")   # in the look, not an ear moves
        pose = dog.blend(pose, base, {"ears": 1.0, "tail": 0.6, "head": 0.7})
        ost = at("old", f)[0]
        if ost in ("turn_back", "back", "look_over"):         # it knows what a back means
            w = ease(after("old", "turn_back", f), 1.2, 2.2) * (1 - ease(after("old", "look_over", f), 0.2, 0.7))
            pose = dog.blend(pose, dog.holding(dog.ears_down(9.0), "reel"), {"ears": 0.75 * w, "tail": 0.5 * w})
        rise = 10 * (1 - ease(since, 0.3, 0.5)) if st == "come_up" else 0
        return on_layer(ink, lambda im: DOG(im, pose, x, LEAD_LINE[1] + rise - oy, scale=DS, facing=-1, carry=reel(), shadow=False),
                        split=400 - oy)
    if st == "walk_up":
        if where != "sill":
            return None
        u = clamp(since / 1.25)
        x = lerp(LEAD_LINE2[0], LEAD_LAY[0], u)
        y = lerp(LEAD_LINE[1], SILL_Y, clamp((LEAD_LINE2[0] - x) / 70.0))
        fn = lambda im: DOG(im, dog.carry_reel(since, gait="trot"), x, y - oy, scale=DS, facing=-1, carry=reel(), shadow=False)   # noqa: E731
        return on_layer(ink, fn, split=400 - oy) if y > SILL_Y + 1 else fn(ink)
    if st == "lay":
        if where != "sill":
            return None
        pose = dog.lay(since * 1.45)
        j = DOG(ink, pose, LEAD_LAY[0], y0, scale=DS, facing=-1, carry=reel() if pose.get("hold", 0) >= 0.5 else None)
        return j
    if where != "sill":
        return None
    x = lerp(LEAD_LAY[0], LEAD_LIE[0], ease(since, 0.0, 0.45))
    pose = dog.lie(since, rest=1.0, settle=1.0)
    wag = bump((f - 178.9) / 0.7)
    if wag:
        pose["tail"] += 0.5 * wag                             # the tail moves once in the water
        pose["wag"] = 0.6 * math.sin((f - 178.9) * 14) * wag
    return on_layer(ink, lambda im: DOG(im, pose, x, y0, scale=DS, facing=-1), split=None)


def lead_reel_down(f):
    """World point of the lead dog's own last reel once it is laid on the boards."""
    return (LEAD_LAY[0] - 52.0, SILL_Y - 2.0)


# ---------------------------------------------------------------- passers ---

def _burst(u):
    """Up out of the water onto the wet half: (x, y world) for u 0..1."""
    return (lerp(BREACH_X, PRESENT_X - 6, smooth(u)), lerp(408.0, SILL_Y, u) - 30 * math.sin(math.pi * u))


def passer_swim(name, f):
    tb = when(name, "breach")
    u = clamp((f - (tb - 1.5)) / 1.5)
    return (lerp(790, BREACH_X, smooth(u)), lerp(600, 408, u ** 0.85))


def draw_passer(ink, name, f, oy, where, anchors):
    st, since = at(name, f)
    tb = when(name, "breach")
    reel_n = REELS[name]["n"]
    yb = SILL_Y - oy

    def can(a, dx=0.0, dy=0.0, s=0.56, under=False):
        mx, my = a["mouth"]
        return my_reel(ink, mx + dx, my + dy, s, reel_n, under=under, tail=0.8, sway=0.5 * math.sin(f * 2.6 + len(name)))

    if st == "under":
        if where != "under" or f < tb - 1.5:
            return
        x, y = passer_swim(name, f)
        a = draw_make(ink, name, x, y - oy, f, "swim", facing=-1, under=True, rot=0.6)
        can(a, -6, 6, under=True)
        return
    if st == "breach":
        if where != "sill":
            return
        x, y = _burst(clamp(since / at_window(name, "breach")))
        a = draw_make(ink, name, x, y - oy, f, "stand", facing=-1)
        can(a, -6, 2)
        return
    if st in ("to_cow", "offer"):
        if where != "sill":
            return
        x = PRESENT_X - 6
        lift = 0.0
        if st == "to_cow":
            lift = ease(since, 0.0, 0.3)                      # holds it up a little higher for her
        elif name == "sheep":
            lift = 1 - ease(since, 0.0, 0.2)
        a = draw_make(ink, name, x, yb, f, "stand", facing=-1, look=0.35 + 0.35 * lift)
        c = can(a, -6, -4 - 5 * lift)
        if name == "sheep":
            anchors["sheep_reel"] = c
        return
    if st == "pass_":
        if where != "sill":
            return
        w = at_window(name, "pass_")
        x = lerp(PRESENT_X - 6, LAY_X + 26, smooth(clamp(since / w)))
        a = draw_make(ink, name, x, yb + 2, f * 1.6, "walk", facing=-1)
        can(a, -6, 0)
        return
    if st == "lay":
        if where != "sill":
            return
        w = at_window(name, "lay")
        a = draw_make(ink, name, LAY_X + 26, yb + 2, f, "stand", facing=-1, look=-0.5 * bump(since / w))
        if since < 0.15:
            can(a, -6, 4)
        return
    if st == "dive":
        w = at_window(name, "dive")
        u = clamp(since / w)
        x = LAY_X + 26 + 10 * u
        y = SILL_Y + 2 - 14 * math.sin(math.pi * min(1.0, u * 1.5)) + 46 * u * u
        if (where == "front") == (u < 0.62):
            return
        if where not in ("front", "under"):
            return
        draw_make(ink, name, x, y - oy, f, "swim", facing=1, rot=-0.9 * u, under=u >= 0.62, alpha=1.0 if u < 0.62 else 1 - 0.8 * (u - 0.62) / 0.38)
        return


@lru_cache(maxsize=None)
def _windows():
    return {"herder": passer_machine("herder").states, "digger": passer_machine("digger").states,
            "sheep": passer_machine("sheep", **SHEEP_KW).states}


def at_window(name, state):
    return _windows()[name][state].window


# ------------------------------------------------------- the big retriever ---

def big_state(f):
    """(world x, y, action, action time, look, carry?) of the big wooden retriever on the boards."""
    st, since = at("big", f)
    if st == "breach":
        return (BREACH_X, 404.0 - 3 * ease(since, 0.0, 0.5), "surface", since, 0.0, True)
    if st == "roll_up":
        u = ease(since, 0.0, 0.95)
        return (lerp(BREACH_X, PRESENT_X, u), lerp(403.0, SILL_Y, clamp(u * 1.6)), "carry", since, 0.25 * u, True)
    if st == "proud":
        return (PRESENT_X, SILL_Y, "proud", since, 0.0, True)
    if st == "told":
        # it stays exactly where it is. It looks at the old dog's back; at the person; up at the cow.
        look = 0.0
        if since > 0.34:
            look = 0.22 * ease(since, 0.34, 0.46)
        if since > 0.66:
            look = lerp(0.22, 1.0, ease(since, 0.66, 0.8))
        back = BACK_OFF * ease(since, 0.78, 1.15)             # ... and as it looks up at her it rolls back from that back, toward her
        return (PRESENT_X + back, SILL_Y, "told", max(0.0, since - 0.25) * 1.2, look, True)
    if st == "nudged":
        # her muzzle comes down in front of its chest (0.55) and it is rolled back along the board on its
        # own wheels; it ducks from the big head, rocks, and when she lifts away it looks up at her once more
        push = smooth(clamp((since - 0.55) / 0.55))
        look = lerp(1.0, 0.5, ease(since, 0.2, 0.5))
        look += 0.2 * math.sin((since - 0.55) * 16.0) * math.exp(-3.0 * max(0.0, since - 0.55)) * (since > 0.55)
        look = lerp(look, 0.95, ease(since, 1.12, 1.32))
        x = PRESENT_X + BACK_OFF + NUDGE_PX * push
        return (x, SILL_Y - 1.5 * bump((since - 0.55) / 0.3) + 5.0 * clamp((x - 560.0) / 15.0), "told", 2.0, look, True)
    if st == "roll_back":
        u = ease(since, 0.0, 0.62)
        x = lerp(PRESENT_X + BACK_OFF + NUDGE_PX, BREACH_X + 12, u)
        return (x, SILL_Y + 60 * clamp((since - 0.5) / 0.3) ** 2 + 5.0 * clamp((x - 560.0) / 15.0) + 3.0 * clamp((x - 580.0) / 20.0), "told", 2.0,
                0.95 * (1 - ease(since, 0.0, 0.3)), True)
    if st == "come_up":
        u = ease(since, 0.0, 0.37)
        return (lerp(BREACH_X, PRESENT_X + 4, u), lerp(405.0, SILL_Y, clamp(u * 1.5)), "carry", since, -0.1, True)
    if st == "offer_low":
        return (PRESENT_X + 4, SILL_Y, "wait", 5.0, -0.3 * ease(since, 0.0, 0.25), True)
    if st == "lay":
        return (PRESENT_X + 4, SILL_Y, "wait", 5.0, -0.3 - 0.45 * bump(since / 0.3), since < 0.1)
    if st == "leave":
        u = ease(since, 0.15, 1.75)
        x = lerp(PRESENT_X + 4, RET_REST[0], u)
        return (x, lerp(SILL_Y, RET_REST[1], clamp((x - 560) / 60.0)), "walk", since, 0.0, False)
    if st == "rest":
        return (RET_REST[0], RET_REST[1], "wait", 9.0, 0.0, False)
    return None


def big_can(f, mouth):
    """Centre of the can in the wooden dog's mouth (wide-frame pixels): gripped by the top of its rim, hanging."""
    return (mouth[0] - 5.0, mouth[1] + 24.0 * BIG_REEL * 0.78)


@lru_cache(maxsize=512)
def big_can_world(f):
    """WORLD centre of that can (found by drawing the dog on a scrap sheet): what the cow puts her nose to."""
    scrap = kit.Ink(0.0, 0)
    was, ZM.on = ZM.on, False
    try:
        a = {}
        draw_big(scrap, f, 0, "sill", a)
    finally:
        ZM.on = was
    return a.get("big_reel", (PRESENT_X - 30.0, 372.0))


def draw_big(ink, f, oy, where, anchors):
    st, since = at("big", f)
    if st in ("under", "fix"):
        return
    in_meadow = st == "rest" or (st == "leave" and since > 1.0)
    if (where == "meadow") != in_meadow:
        return
    if where not in ("sill", "meadow"):
        return
    x, y, action, tau, look, carrying = big_state(f)
    facing = 1 if st == "leave" and since > 0.15 else -1
    kw = dict(scale=BIG_S, facing=facing, size="big")
    if look:
        kw["look"] = look
    if action == "wait":
        kw["arrive"] = 0
    if action == "proud" or action == "walk" or action == "carry":
        tau = f
    if st == "proud":                                         # it watches the old dog get up; the peg slows and stops
        os_ = after("old", "turn_back", f)
        if os_ > 0:
            kw["look"] = 0.2 * ease(os_, 0.3, 1.0) - 0.12 * ease(os_, 1.6, 2.4)
            if os_ > 1.3:
                tau = when("old", "turn_back") + 1.3 + (1 - math.exp(-(os_ - 1.3) * 2.2)) / 2.2
    if st == "rest" and abs(f - 179.3) < 0.2:                 # its peg tail ticks once
        action, tau = "proud", 0.0 + (f - 179.1) * 4
    go = lambda im: RET(im, x, y - oy, action, tau, carry="reel" if carrying and action != "surface" else None, thing_scale=0.01, **kw)    # noqa: E731
    wet = y > SILL_Y + 2 or st == "breach"
    a = on_layer(ink, go, split=400 - oy) if wet else go(ink)
    anchors["big"] = a
    if carrying:
        mx, my = a["mouth"]
        sway = 0.5 * math.sin(f * 2.3) + (0.8 * math.sin((f - when("big", "nudged")) * 14.0) if st == "nudged" and since > 0.55 else 0.0)
        if action == "surface":
            anchors["big_reel"] = my_reel(ink, mx - 4, my - 12, BIG_REEL, big_look(f), paw=big_look(f) == "wobbly", tilt=0.9)
        else:
            cxy = big_can(f, (mx, my))
            anchors["big_reel"] = my_reel(ink, cxy[0], cxy[1], BIG_REEL, big_look(f), paw=big_look(f) == "wobbly", tilt=0.9, tail=1.0, sway=sway)
    if when("big", "proud") <= f < when("big", "roll_back"):
        DRIPS(ink, f, x + 4, y - oy - 30, when("big", "breach") + 0.4, width=46, floor=392 - oy, s=0.7, life=9.0, seed=4)
    if st in ("come_up", "offer_low", "lay"):
        DRIPS(ink, f, x + 4, y - oy - 30, when("big", "come_up"), width=46, floor=392 - oy, s=0.7, life=5.0, seed=9)
    return a


def draw_two_reels(ink, f, oy, near):
    """The retriever's changed reel and the lead dog's own, on the boards. near 0..1: nudged to our side of the dog."""
    if when("big", "lay") is not None and f >= big_reel_laid(f)[1]:
        pt, tl = big_reel_laid(f)
        my_reel(ink, pt[0] + 6 * near, pt[1] - oy - 3 * bump((f - tl) / 0.2) + 6 * near, BIG_REEL, "wobbly", paw=True, tilt=lerp(1.0, 0.8, near),
                tail=0.7)
    if after("lead", "lay", f) >= 0.45:
        lx, ly = lead_reel_down(f)
        REEL(ink, REELS["lead"]["n"], lx - 4 * near, ly - oy - 14 + 8 * near, 0.6, wet=1, tilt=lerp(1.0, 0.8, near))


def big_reel_laid(f):
    """World point and time of the changed reel on the boards."""
    tl = when("big", "lay")
    return (old_place(tl)[0], SILL_Y - 18.0), tl + 0.1


# -------------------------------------------------------------- the person ---

def person_q(f):
    keys = [(144.0, "sit"), (144.62, "offer", {"at": (366, 374), "dur": 0.6}), (145.1, "sit", {"dur": 0.4}),
            (146.0, "hold_up", {"dur": 0.85}), (149.3, "hold_up", {"dur": 0.2}),
            # REPAIR: the no is finished with the hand. The film comes down; the hand goes to the can beside the knee
            # and pushes it back along the boards to the dog.
            (149.85, "offer", {"at": (CAN_HOME[0] + 4, 370), "dur": 0.5}), (150.55, "offer", {"at": (318, 374), "dur": 0.65}),
            (151.6, "sit", {"dur": 0.8})]
    for tk in PEB_SEEN:
        keys += [(tk, "offer", {"at": (216, 292), "dur": 0.34}), (tk + 0.4, "sit", {"dur": 0.34})]
    keys += [(174.9, "sit"), (175.05, "set_radio", {"dur": 0.45}), (175.5, "sit", {"dur": 0.35}), (177.0, "hold_up", {"dur": 0.9})]
    q = porch.act(f, sorted(keys, key=lambda k: k[0]))
    if 148.0 <= f < 149.3:                                   # no: the head, the shoulders and the film in the hands, twice, slowly
        u = (f - 148.0) / 1.3                                # (REPAIR: 1.3 s and wider, so each of the four extremes is a drawing)
        env = math.sin(math.pi * u) ** 0.5
        sw = math.sin(2 * math.pi * 2 * u) * env
        q = dict(porch.pose("hold_up", p=1.0, t=f, at=(216 + 22 * sw, 238 + 5 * abs(sw)), at_b=(268 + 22 * sw, 250 + 5 * abs(sw))))
        q["lean"] = q["lean"] + 10.0 * sw
        q["turn"] = q["turn"] + 1.7 * sw
        q["head"] = q["head"] + 5 * env + 13.0 * sw
    return q


def person_hold(f):
    if 144.62 <= f < 145.1:
        return "reel"
    if 145.3 <= f < 149.42 or f >= 176.3:
        return "film"
    for tk in PEB_SEEN:
        if tk - 0.34 <= f < tk:
            return "pebble"
    return None


def thrown(f):
    """(picture, amount) of what the lamp throws on the door planks."""
    if f < 160.0:
        a = ease(f, 145.75, 146.1) * (1 - ease(f, 149.3, 149.7))     # the film comes down: the picture goes off the door
        return teeth_image(True), a
    return teeth_image(False), ease(f, 177.1, 177.7)


# ---------------------------------------------------------- the jaw child ---

KID_HOME = (428.0, 516.0)


def kid_state(f):
    """The jaw child under the sill in 6.1 and 6.2: (x, y world, bubble grow, pop)."""
    up = ease(f, 144.6, 146.0)
    x = lerp(520.0, KID_HOME[0], up)
    y = lerp(640.0, KID_HOME[1], up) + 3 * math.sin(f * 1.4)
    away = ease(f, 154.75, 155.4)                             # it darts off as seven dogs come in
    x += 150 * away
    y += 190 * away
    return x, y, ease(f, 146.0, 146.9), ease(f, 154.6, 154.9)


def draw_kid(ink, f, oy):
    """The jaw child under the sill with its own page held up in its fin: paper, in the water, in its hand.
    (No bubble here: a picture hanging in the water by itself for eight seconds read as a badge.)"""
    if f > 156.0:
        return
    x, y, grow, pop = kid_state(f)
    cam = Cam(oy=oy)
    up = ease(f, 146.0, 146.9) * (1 - ease(f, 154.6, 154.9))
    wave = 10 * math.sin(f * 2.2) * up
    r = town.child(ink, f, cam, 0, x, y, facing=-1, tilt=10 + 60 * ease(f, 154.75, 155.2), arm=lerp(30, 122, up) + wave,
                   look=(105, 300), swim=0.4)
    hx, hy = r["hand"]
    props.page(ink, hx - 10 - 6 * up, hy - 20 * up + 4, 0.5 + 0.38 * up, drawing="jaw", angle=-8 + 0.6 * wave, wet=0.4, tint=TEAL, tint_amount=0.12)


# ====================================================================== #
#  6 · THE PORCH FRAME                                                   #
# ====================================================================== #

def six_state(name, f):
    """(x, y world, phase, pitch): arriving, standing at the waterline, in the air, swimming down."""
    q = SIX[name]
    tg = when("lead", "dive") + q["lag"] * DT
    sx, sy = q["spot"]
    if f < q["come"][0]:
        return None
    if f < tg:
        u = ease(f, q["come"][0], q["come"][1])
        fx, fy = q["frm"]
        if name == "sheep":                                   # blown in on the wind
            return (lerp(fx, sx, u), lerp(fy, sy, u * u) - 24 * math.sin(math.pi * u), "come" if u < 1 else "stand", 0.0)
        return (lerp(fx, sx, u), lerp(fy, sy, u), "come" if u < 1 else "stand", 0.0)
    u = f - tg
    if u < LEAP:
        v = u / LEAP
        return (lerp(sx, q["entry"], v), lerp(sy - 14, 400, v * v) - 16 * math.sin(math.pi * v), "air", -0.3 - 0.5 * v)
    u -= LEAP
    k = list(SIX).index(name)
    return (q["entry"] + (40 + 22 * k) * (1 - math.exp(-u)) + (k - 2.5) * 16 * u, 404 + (128 + 9 * k) * u, "swim", -0.75)


def draw_six(ink, f, oy, where):
    for name in SIX:
        s6 = six_state(name, f)
        if s6 is None:
            continue
        x, y, ph, pitch = s6
        if y - oy > H + 80:
            continue
        if ph in ("come", "stand") and where == "sill":
            if name == "digger" and ph == "come":             # it unbends out of the reeds
                ka.digger(ink, x, y - oy, GS, -1, "unbend", p=ease(f, SIX[name]["come"][0], SIX[name]["come"][1]), spray=False, post=False)
            else:
                draw_make(ink, name, x, y - oy, f * (1.5 if ph == "come" else 1.0), "walk" if ph == "come" else "stand", facing=-1)
        elif ph == "air" and where == "front":
            draw_make(ink, name, x, y - oy, f, "swim", facing=-1, rot=pitch)
        elif ph == "swim" and where == "under":
            draw_make(ink, name, x, y - oy, f, "swim", facing=1, rot=pitch, under=True)


def curtain_state(c, f):
    tg = when("lead", "dive") + c["go"]
    side = 1 if c["x"] > 600 else -1                          # they run in along the bank from whichever end is nearer
    x0 = c["x"] + side * 16
    y0 = (porch.meadow_y(min(max(x0, 640), 958)) if x0 > 640 else (390.0 if x0 > 346 else 392.0))
    if f < tg - 1.1:
        return None
    if f < tg:
        u = (f - (tg - 1.1)) / 1.1
        far = 1010.0 if side > 0 else -50.0
        return (lerp(far, x0, u), y0, "run", 0.0, -side)
    u = f - tg
    if u < 0.25:
        v = u / 0.25
        return (lerp(x0, c["x"], v), lerp(y0 - 8, 400, v * v) - 12 * math.sin(math.pi * v), "air", -0.3 - 0.5 * v, -side)
    u -= 0.25
    return (c["x"] + c["dx"] * (1 - math.exp(-u * 0.8)), min(c["deep"] + 200, 403 + c["v"] * u), "swim", -0.8, 1 if c["dx"] > 0 else -1)


def draw_curtain(ink, f, oy, where):
    td = when("lead", "dive")
    if td is None or f < td - 0.6 or f > td + 4.0:
        return
    for c in curtain():
        cs = curtain_state(c, f)
        if cs is None:
            continue
        x, y, ph, pitch, face = cs
        if not (-60 < y - oy < H + 60) or not (-60 < x < W + 60):
            continue
        if ph == "run" and where == "strip":
            draw_make(ink, c["make"], x, y - oy, f * 2.0 + c["seed"], "walk", facing=face, k=c["k"])
        elif ph == "air" and where == "front":
            draw_make(ink, c["make"], x, y - oy, f, "swim", facing=face, k=c["k"], rot=pitch)
        elif ph == "swim" and where == "under":
            draw_make(ink, c["make"], x, y - oy, f + c["seed"], "swim", facing=face, k=c["k"], rot=pitch, under=True)


def splashes(f):
    """[(world x, film time, size, kind)] every crossing of the surface in S6."""
    out = []
    td = when("lead", "dive")
    out.append((LEAD_ENTRY, td + LEAP * 0.85, 1.2, "in"))
    for name, q in SIX.items():
        out.append((q["entry"], td + q["lag"] * DT + LEAP * 0.85, 1.1 if name in ("big", "sheep") else 0.9, "in"))
    for c in curtain():
        out.append((c["x"], td + c["go"] + 0.22, 0.55 + 0.3 * c["k"], "in"))
    for name in ("herder", "digger", "sheep"):
        out.append((BREACH_X, when(name, "breach") + 0.03, 1.0, "out"))
        out.append((LAY_X + 34, when(name, "dive") + 0.62 * at_window(name, "dive"), 0.8, "in"))
    out.append((LEAD_LINE[0] + 8, when("lead", "come_up") + 0.3, 1.0, "out"))
    out.append((BREACH_X, when("big", "breach") + 0.05, 1.1, "out"))
    out.append((BREACH_X + 8, when("big", "roll_back") + 0.62, 1.1, "in"))
    out.append((BREACH_X, when("big", "come_up") + 0.02, 1.1, "out"))
    for k, tp in enumerate(POPUPS):
        out.append((popup_x(k), tp + 0.05, 0.32, "out"))
    return out


def popup_x(k):
    return (250.0, 276.0, 232.0, 262.0, 244.0)[k % 5]


def draw_popups(ink, f, oy):
    """Small dogs at the porch's front edge, each with one can: up, the can onto the pile, gone."""
    for k, tp in enumerate(POPUPS):
        u = f - tp
        if not (0 <= u < 0.8):
            continue
        x = popup_x(k)
        mk = ("terrier", "small", "blood", "terrier", "mid")[k % 5]
        up = ease(u, 0.0, 0.2) * (1 - ease(u, 0.5, 0.8))
        a = draw_make(ink, mk, x, 414 - 16 * up - oy, f, "swim", facing=1 if k % 2 else -1, k=0.8, rot=0.9, split=402 - oy)
        if u < 0.35:
            n = ledger()[3 + k][2]
            my_reel(ink, a["mouth"][0], a["mouth"][1] - 4, 0.42, n)


def _rings(f):
    rings = []
    for (x, ts, size, kind) in splashes(f):
        if ts <= f < ts + 5:
            rings.append(porch.ring(x, ts, 0.5 + 0.6 * size))
    if f >= when("lead", "lie", 999):
        rings.append(porch.ring(LEAD_LIE[0] + 62, when("lead", "lie") + 0.9, 0.6))
        if f >= 179.1:
            rings.append(porch.ring(LEAD_LIE[0] + 64, 179.1, 0.6))
    if f >= 175.4:                                            # the radio's grille throws rings on the water
        k = 0
        while 175.4 + 1.5 * k <= f:
            rings.append(porch.ring(318, 175.4 + 1.5 * k, 0.55))
            k += 1
    return rings


def town_under(ink, f, cam, last=False):
    town.back(ink, f, cam, sky=False, night=NIGHT)
    town.street(ink, f, cam, holes=374, smudges=131, taken=(0,))
    town.making_place(ink, cam, 1.0)
    if not last:
        town.school_class(ink, f, cam, skip=(0,))
        town.townsfolk(ink, f, cam)


LAST_KIDS = ((232, 606), (300, 664), (356, 592), (424, 652), (486, 598), (640, 548), (548, 642), (196, 668))   # child k; 0 the jaw child in front; 5 the waver, apart


def draw_last_below(ink, f, cam):
    """Below the line in the last shot: the last pack far down with lanterns; the fish class, every face up to the lit door."""
    for d in lantern_pack():
        x = d["x"] + 10 * math.sin(f * 0.5 + d["ph"])
        y = d["y"] + 3 * math.sin(f * 0.9 + d["ph"])
        sx, sy = cam.xy(x, y)
        if sy > H + 30:
            continue
        props.glow(ink, sx + 10 * d["face"], sy + 2, 30, (255, 214, 140), 0.5)
        a = draw_make(ink, d["make"], sx, sy, f + d["ph"], "swim", facing=d["face"], k=d["k"], under=True, alpha=0.8)
        props.lantern(ink, a["mouth"][0], a["mouth"][1], 0.34, f, swing=10 * math.sin(f * 2 + d["ph"]), halo=0.5, seed=d["seed"])
    door = (105, 300)
    rise = 1 - ease(f, 173.6, 178.0)
    for k, (x, y) in enumerate(LAST_KIDS):
        yy = y + 190 * rise * (1 + 0.1 * k) + 4 * math.sin(f * 1.3 + k)
        look = (COW_X1 - 70, 350) if k == 5 else door
        r = town.child(ink, f, cam, k, x + 40 * rise, yy, facing=-1 if k != 5 else 1, tilt=38 if k != 5 else 24, look=look, swim=0.5,
                       arm=20 if k != 5 else 60 + 40 * bump((f - 178.3) / 1.2))


def _principals_strip(ink, f, oy, anchors):
    draw_cow(ink, f, oy, anchors)
    draw_old(ink, f, oy, "strip")


def can_xy(f):
    """REPAIR: the can the person took, opened, and pushes back to the dog (world). It slides a little further than the hand."""
    u = ease(f, 149.85, 150.55)
    v = ease(f, 150.5, 150.95)
    return (lerp(CAN_HOME[0], 308.0, u) + 26.0 * v, lerp(CAN_HOME[1], 381.0, u) + 2.0 * v)


def _principals_sill(ink, f, oy, anchors):
    if f >= 145.1:
        cxw, cyw = can_xy(f)
        my_reel(ink, cxw, cyw - oy, 0.6, props.REEL_LEAD, paw=True, tilt=0.45 + 0.1 * ease(f, 149.85, 150.55))
    near = after("lead", "lie", f) >= 0.0                     # once the dog lies down the reels lean against its flank, on our side
    if not near:
        draw_two_reels(ink, f, oy, 0.0)
    for name in ("herder", "digger", "sheep"):
        if at(name, f)[0] in ("breach", "to_cow"):
            draw_passer(ink, name, f, oy, "sill", anchors)
    draw_old(ink, f, oy, "sill")
    for name in ("herder", "digger", "sheep"):
        if at(name, f)[0] not in ("breach", "to_cow"):
            draw_passer(ink, name, f, oy, "sill", anchors)
    draw_big(ink, f, oy, "sill", anchors)
    draw_lead(ink, f, oy, "sill")
    if near:
        draw_two_reels(ink, f, oy, ease(after("lead", "lie", f), 0.0, 0.5))
    if at("cow", f)[0] in ("smell", "nose") or 151.0 <= f < 154.1:   # her head again, in front of the dog she is smelling or shoving
        draw_cow(ink, f, oy, anchors, only="head")
    if not ZM.on:
        for name in ("herder", "digger", "sheep"):
            tb = when(name, "breach")
            if tb + 0.3 < f < tb + 3.0 and at(name, f)[0] in ("to_cow", "offer", "pass_"):
                porch.drips(ink, f, oy, PRESENT_X - 6, 366, f - tb - 0.3, wet=0.8, width=36, floor=392)
    else:
        for k, name in enumerate(("herder", "digger", "sheep")):
            tb = when(name, "breach")
            if tb + 0.3 < f < tb + 3.0 and at(name, f)[0] in ("to_cow", "offer", "pass_"):
                DRIPS(ink, f, PRESENT_X - 6, 366 - oy, tb + 0.3, width=36, floor=392 - oy, s=0.7, life=3.0, seed=30 + k)


def _porch_frame(ink, f, oy, mode="all"):
    """mode 'all': everybody. mode 'bg': without the ones a closer setup draws again (_principals_*)."""
    cam = Cam(oy=oy)
    anchors = {}
    wtown = 1.0                                               # S5 hands over with the town's water under the porch
    last = f >= 173.4 and oy > 76

    def hill(ink, t, oy):
        pass

    def strip(ink, t, oy):
        draw_herd(ink, f, oy)
        if mode == "all":
            _principals_strip(ink, f, oy, anchors)
        draw_big(ink, f, oy, "meadow", anchors)
        draw_calf(ink, f, oy)
        draw_heap(ink, f, oy)
        draw_curtain(ink, f, oy, "strip")

    def sill(ink, t, oy):
        props.pile(ink, f, 312, 392 - oy, 5, s=0.6, edge=404 - oy, floor=400 - oy, spread=0.58)
        draw_stacks(ink, f, oy)
        if f < 144.62:                                        # the reel it was so pleased with, on the sill in front of the person
            props.reel(ink, props.REEL_LEAD, 380, 377 - oy, 0.78, tilt=0.8, paw=True, wet=1)
        draw_six(ink, f, oy, "sill")
        if mode == "all":
            _principals_sill(ink, f, oy, anchors)

    def under(ink, t, oy):
        if wtown > 0:
            before = ink.img.copy() if wtown < 1 else None
            town_under(ink, f, cam, last=last)
            if before is not None:
                ink.img = Image.blend(before, ink.img, wtown)
                _redraw(ink)
        draw_more_pebbles(ink, f, oy)
        draw_six(ink, f, oy, "under")
        draw_curtain(ink, f, oy, "under")
        draw_lead(ink, f, oy, "under")
        for name in ("herder", "digger", "sheep"):
            draw_passer(ink, name, f, oy, "under", anchors)
        td = when("lead", "dive")
        if td <= f < td + 4.5:
            porch.bubbles(ink, f, oy, lambda te: lead_swim(te)[:2], td + LEAP, td + 3.0, rate=8.0, seed=2)
            for k, (name, q) in enumerate(SIX.items()):
                porch.bubbles(ink, f, oy, (q["entry"], 440), td + q["lag"] * DT + LEAP, td + q["lag"] * DT + LEAP + 1.0, rate=14.0, seed=20 + k, size=1.0)
            for c in curtain():
                porch.bubbles(ink, f, oy, (c["x"], 430), td + c["go"] + 0.25, td + c["go"] + 0.9, rate=11.0, seed=60 + c["seed"], size=0.7)
        tf = when("big", "roll_back")
        if tf + 0.6 <= f < tf + 2.0:
            porch.bubbles(ink, f, oy, (BREACH_X + 10, 450), tf + 0.62, tf + 1.3, rate=14.0, seed=7)
        town.front(ink, f, cam)
        town.grade(ink, cam, night=NIGHT)                     # it is night down there, as S5 left it; lamp-warm things stay bright
        draw_kid(ink, f, oy)                                  # what a child says is lit from inside: after the night
        if last:
            draw_last_below(ink, f, cam)

    def front(ink, t, oy):
        draw_lead(ink, f, oy, "front")
        draw_six(ink, f, oy, "front")
        draw_curtain(ink, f, oy, "front")
        for name in ("herder", "digger", "sheep"):
            draw_passer(ink, name, f, oy, "front", anchors)
        draw_popups(ink, f, oy)
        for i, (x, ts, size, kind) in enumerate(splashes(f)):
            if ts <= f < ts + 1.2:
                porch.splash(ink, f, oy, x, f - ts, size, kind, seed=i)

    img, amount = thrown(f)
    porch.scene(ink, f, oy, cast=dict(hill=hill, strip=strip, sill=sill, under=under, front=front),
                q=person_q(f), hold_a=person_hold(f), door=lerp(0.92, 0.25, ease(f, 144.3, 145.4)), radio_on=(1 - ease(f, 149.0, 149.4)) + ease(f, 175.2, 175.5),
                pebbles=PEBBLES[:min(30, pebbles_at(f))], rings=_rings(f), puddles=[(350, 0.6), (405, 0.5), (470, 0.4)],
                dusk=lerp(0.6, 1.0, ease(f, 144.0, 173.0)), stars=lerp(0.07, 0.5, ease(f, 150.0, 177.0)),
                thrown=img, thrown_amount=amount)
    return anchors


# ====================================================================== #
#  7 · THE TOWN INSERT: the reel is changed (170.0 to 171.5)             #
# ====================================================================== #

CELL_W, CELL_H = 22.0, 17.0
CAN_AT = (474.0, 789.0)                      # on the planks of the making place
STRIP_X0 = 502.0


def _cell(ink, cam, wx, wy, kind, ang=0.0, alpha=1.0):
    """One frame of the strip, lying on the planks: 'tidy' (ruled teeth, blue-white) or 'page' (the child's)."""
    sx, sy = cam.xy(wx, wy)
    w, h = CELL_W * cam.zoom, CELL_H * cam.zoom
    lay = Image.new("RGBA", (int(w * 2.4), int(w * 2.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx = cy = lay.size[0] / 2
    tidy = kind == "tidy"
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=(34, 30, 40, 255))
    d.rectangle([cx - w / 2 + 3, cy - h / 2 + 2, cx + w / 2 - 3, cy + h / 2 - 2], fill=(226, 234, 240, 255) if tidy else (248, 232, 196, 255))
    town.picture(lay, "jaw_only", cx, cy, h * 0.86, tidy=tidy, color=(40, 60, 96) if tidy else (124, 52, 30), width=3.0)
    if ang:
        lay = lay.rotate(ang, resample=Image.BICUBIC)
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    ink.img.paste(lay, (int(sx - cx), int(sy - cy)), lay)
    _redraw(ink)


def _insert_frame(ink, f):
    t0 = when("big", "fix")
    ur = f - t0                                               # 0..2.6: the change (0..2.0), then the can taken up (2.0..2.6)
    u = min(1.5, ur * 0.75)                                   # the change, on the clock it was drawn to
    go = ease(ur, 2.12, 2.6)
    cam = Cam.look(546.0 - 10 * go, 768.0 - 26 * go, 2.3 - 0.12 * go)        # the camera starts up after it
    town.back(ink, f, cam, sky=True, night=NIGHT)
    town.street(ink, f, cam, holes=374, smudges=131, taken=(0,))
    town.making_place(ink, cam, 1.0)
    town.school_class(ink, f, cam, skip=(0,), look=(548, 770) if f - when("big", "fix") < 2.12 else (540, 640))
    # the mouthfuls going up behind: small dogs, a can each, toward the lit door
    for i in range(9):
        ph = (u * 0.55 + i * 0.37) % 1.6
        wx = 760 - 150 * ph - 34 * i + 40 * math.sin(i * 2.1)
        wy = 760 - 62 * ph - 9 * (i % 4) - 34
        sx, sy = cam.xy(wx, wy, depth=0.8)
        a = draw_make(ink, MAKES[(i * 2 + 3) % len(MAKES)], sx, sy, f + i, "swim", facing=-1, k=0.75, rot=0.5, under=True, alpha=0.75)
        my_reel(ink, a["mouth"][0] - 6, a["mouth"][1] + 4, 0.5, ledger()[10 + i][2], under=True, alpha=0.8)
    yy = CAN_AT[1]
    # the strip pulled out of the can along the planks: five frames, the middle one the straight piece
    wind = ease(u, 1.08, 1.3)
    gap = (STRIP_X0 + 2 * (CELL_W + 1.5), yy)
    # the retriever at the can
    pull = ease(u, 0.28, 0.5)
    rx, ry = cam.xy(494.0, 797.0)
    tau = 0.3 + 0.5 * bump(u / 0.56) if u < 0.56 else (0.3 + 0.55 * bump((u - 1.18) / 0.3))
    took = ur >= 2.12
    if ur >= 2.0 and not took:                                # down to the can once more: this time to take it
        tau = 0.3 + 0.52 * ease(ur, 2.0, 2.12)
    if not took:
        a = kb.retriever(ink, rx, ry, "set_down", tau, scale=RS * cam.zoom * 1.0, facing=1, size="big", tint=kb.WATER, tint_amount=0.15)
    for k in range(5):                                        # the strip lies in front of it
        wx = lerp(STRIP_X0 + k * (CELL_W + 1.5), CAN_AT[0] + 6, wind)
        if k == 2:
            if u < 0.5:
                _cell(ink, cam, wx, yy, "tidy")
            continue
        _cell(ink, cam, wx, yy, "tidy", alpha=1 - 0.9 * wind)
    # the straight piece comes out in its teeth and is thrown away
    if 0.5 <= u < 1.15:
        v = (u - 0.5) / 0.65
        mx, my = cam.world(*a["mouth"])
        px, py = lerp(mx + 8, mx - 130, v), lerp(my, my - 86 - 30 * math.sin(v * math.pi), v)
        _cell(ink, cam, px, py, "tidy", ang=520 * v, alpha=1 - v * v)
    # the jaw child swims over, blows the teeth the way it drew them, and puts its page in the gap
    arr = ease(u, 0.0, 0.42)
    kx, ky = lerp(690.0, 618.0, arr), lerp(826.0, 800.0, arr) + 2 * math.sin(f * 3)
    placed = ease(u, 0.78, 1.04)
    kid = town.child(ink, f, cam, 0, kx, ky, facing=-1, tilt=16, arm=lerp(70, 118, bump(clamp((u - 0.6) / 0.55))), look=gap, swim=0.6)
    if u >= 0.3 and wind < 1:
        hx, hy = cam.world(*kid["hand"])
        px, py = lerp2((hx - 4, hy), gap, placed)
        px = lerp(px, CAN_AT[0] + 6, wind)
        _cell(ink, cam, px, py - 6 * bump(placed), "page", ang=14 * (1 - placed), alpha=1 - 0.9 * wind)
    # the can: open (its lid beside it) until the strip is wound back, then shut, then the print
    cx, cy = cam.xy(*CAN_AT)
    shut = ease(u, 1.26, 1.4)
    if not took:
        props.reel(ink, props.REEL_RETRIEVER, cx, cy - 3, 1.1, tilt=0.4, face=False, wet=0.3, tint=TEAL, tint_amount=0.2)
        lx, ly = lerp(cx - 50, cx, shut), lerp(cy - 8, cy - 14, shut) - 30 * bump(shut)
        my_reel(ink, lx, ly, 1.1, "wobbly" if u > 1.0 else "tidy", paw=u >= 1.42, tilt=lerp(0.62, 0.9, shut), under=True)
    else:
        # the can in its mouth: it kicks off the planks and swims up toward the bright line, the children's eyes after it
        v = (ur - 2.12) / 0.48
        wx, wy = 494.0 + 6.0 * v + 30.0 * v * v, 797.0 - 26.0 - 70.0 * v * v - 16.0 * v
        sx, sy = cam.xy(wx, wy)
        a = on_layer(ink, lambda im: kb.retriever(im, sx, sy, "swim", f, scale=RS * cam.zoom, facing=1, size="big", carry="reel",
                                                  thing_scale=0.01, tint=kb.WATER, tint_amount=0.15, shadow=False),
                     rot=0.25 + 0.75 * smooth(clamp(v * 1.4)), pivot=(sx, sy))
        mx, my = rot_pt(a["mouth"], (sx, sy), 0.25 + 0.75 * smooth(clamp(v * 1.4)))
        my_reel(ink, mx + 6, my + 12, 1.25, "wobbly", paw=True, tilt=0.9, under=True, tail=0.8, sway=math.sin(f * 9))
        for k in range(5):                                    # the breath it leaves
            bx, by = cam.xy(wx - 18 + 9 * math.sin(k * 2.4 + f * 3), wy + 14 + 22 * k * v)
            r = 2.0 + 1.6 * (k % 3)
            ink.d.ellipse([bx - r, by - r, bx + r, by + r], outline=(214, 240, 240, 190), width=1)
    town.front(ink, f, cam)
    town.grade(ink, cam, night=NIGHT * 0.6)


# ====================================================================== #
#  8 · THE CLOSER SETUPS                                                 #
# ====================================================================== #

CLOSE_BLUR = {"no": 0.45, "ears": 1.0}      # REPAIR: the person is the subject of 'no', so the set is not thrown out of focus


def _close_frame(ink, f, cam, blur=1.6):
    """A closer setup: the set pushed in and left soft behind, the animals and their cans cut again at this size."""
    cx, cy, z = cam
    oy = int(round(clamp(cy - H / 2, 0.0, 400.0)))
    _porch_frame(ink, f, oy, mode="bg")
    view(ink, cx, cy - oy, z)
    ink.img = ink.img.filter(ImageFilter.GaussianBlur(blur))
    _redraw(ink)
    ZM.on, ZM.cx, ZM.cy, ZM.z = True, cx, cy - oy, z
    try:
        anchors = {}
        _principals_strip(ink, f, oy, anchors)
        _principals_sill(ink, f, oy, anchors)
    finally:
        ZM.on = False
    return anchors


# ====================================================================== #
#  9 · THE PICTURE (no lettering anywhere in it)                         #
# ====================================================================== #

def draw(t, ink):
    """One full 960x540 frame of S6 at local time t (0..36)."""
    t = clamp(t, 0.0, SECONDS)
    f = T0 + t
    if f >= T1:
        f = T1 - 1e-4
    name = shot_at(f)[2]
    if name == "town":
        _insert_frame(ink, f)
        return
    if name in CLOSE:
        _close_frame(ink, f, CLOSE[name], CLOSE_BLUR.get(name, 1.6))
        return
    cx, cy, zoom = camera(f)
    oy = int(round(cy - H / 2))
    _porch_frame(ink, f, oy)
    view(ink, cx, H / 2 + (cy - H / 2 - oy), zoom)


# ====================================================================== #
#  10 · THE SOUND (nobody here has heard it)                             #
# ====================================================================== #

def _pan(wx):
    return clamp((wx - 480.0) / 480.0, -1, 1) * 0.8


def sound(mix, at=0.0):
    """S6's sound into `mix`, the sequence starting at mix second `at`. Every contact is timed to the frame
    it lands on in THIS picture, read off the same machines that draw it."""
    S = snd

    def A(f):
        return at + (f - T0)

    def F(name, f, gain, **kw):
        if foley is not None and name in foley.NAMES:
            try:
                foley.play(mix, name, A(f), gain=gain, **kw)
                return True
            except Exception:
                return False
        return False

    t_in, t_out = when("big", "fix"), when("big", "come_up")
    # rooms. Above water all sequence long, cut hard to the under-water room for the one cut to the town,
    # and half and half as the camera lowers at the end (the board's rule for a frame with both worlds).
    if not (F("night", T0, 0.11, seconds=t_in - T0, loop=True) and F("creek", T0, 0.09, seconds=t_in - T0, loop=True, pan=0.4)):
        S.above(mix, A(T0) - 0.1, t_in - T0 + 0.1, 1.0, 0.2, 0.02)
    if not F("under", t_in, 0.22, seconds=t_out - t_in, loop=True, fade=0.02):
        S.hush(mix, A(t_in), t_out - t_in, 1.0, 0.02, 0.02)
    if not (F("night", t_out, 0.11, seconds=T1 - t_out, loop=True, start=4.0) and F("creek", t_out, 0.09, seconds=T1 - t_out, loop=True, pan=0.4, start=3.0)):
        S.above(mix, A(t_out), T1 - t_out + 0.1, 1.0, 0.02, 0.2)
    if not F("under", 176.0, 0.1, seconds=T1 - 176.0, loop=True, start=2.0):
        S.hush(mix, A(176.0), T1 - 176.0, 0.5, 2.0, 0.2)
    S.music_s6(mix, at)                                       # the radio: two phrases, off with the "no"; back at +31.2, slower
    # 6.1 to the lamp
    S.tail(mix, A(144.3), 4)
    S.tail(mix, A(145.9), 4)
    S.ratchet(mix, A(145.35), 0.6, 16, gain=0.05, pan=S.P_DOOR + 0.1)       # film pulled off the reel
    S.tail(mix, A(147.5), 4)
    S.tail(mix, A(148.4), 3)                                  # stops mid-pattern at 149.0
    S.voice_no(mix, A(148.2))
    for who, (x, dy, back, facing, tf) in HERD_SPOT.items():
        if tf:
            S.cow_down(mix, A(tf), gain=0.05, pan=_pan(x), bell=False)
    S.cow_down(mix, A(when("cow", "fold1")), gain=0.07, pan=_pan(COW_X0))
    # 6.2 ears down: crickets and the creek. One breath.
    if not F("sigh", when("lead", "hold") + 0.6, 0.12):
        S.sigh(mix, A(when("lead", "hold") + 0.6), 1.0, gain=0.05, pan=0.0)
    # 6.3 six at once
    S.cow_up(mix, A(when("cow", "get_up")), pan=_pan(COW_X0))
    S.hooves(mix, A(when("cow", "walk") + 0.2), 4, 0.5, "earth", gain=0.09, pan=_pan(COW_X0), pan_to=_pan(COW_X1))
    S.cowbell(mix, A(when("cow", "walk") + 0.3), 2, 1.0, gain=0.05, pan=0.3)
    S.wheels(mix, A(153.1), 1.1, 1.0, gain=0.05, pan=0.8, pan_to=0.4)
    S.wheels(mix, A(153.3), 1.0, 1.26, gain=0.05, pan=0.8, pan_to=0.45)
    S.wheels(mix, A(153.45), 0.95, 1.5, gain=0.05, pan=0.8, pan_to=0.5)
    S.wire_twang(mix, A(153.3), pan=0.35)
    S.flutter(mix, A(153.2), pan=0.3)
    S.paws(mix, A(when("lead", "look_pack") + 0.24), 4, 0.12, gain=0.1, pan=-0.1, pan_to=0.15)
    td = when("lead", "dive")
    for (x, ts, size, kind) in splashes(T1):
        if kind == "in" and td <= ts < td + 0.5:
            if not F("splash", ts, 0.3 * size, pan=_pan(x), take=int(x) % 3, seconds=1.2):
                S.plunge(mix, A(ts), size * 0.8, gain=0.12, pan=_pan(x))
        elif kind == "in" and ts < td + 2.5:                  # the rest of the third pack, a ragged run
            S.splash(mix, A(ts), gain=0.07, pan=_pan(x))
    S.card_drag(mix, A(when("old", "shift")), 0.8)
    for tk in PEB_T:
        if tk < 162.0:
            S.pebble(mix, A(tk), gain=0.05)
    # 6.4 the gate: three times the same small pattern
    for name in ("herder", "digger", "sheep"):
        tb = when(name, "breach")
        S.breach(mix, A(tb + 0.03), 0.8, gain=0.2)
        S.drip(mix, A(tb + 0.5), 1)
        S.sniff(mix, A(when("old", "glance") if name == "herder" else tb + 0.75), 1, gain=0.04, pan=S.P_SILL)
        S.paws(mix, A(when(name, "pass_")), 4, 0.17, gain=0.07, pan=0.05, pan_to=-0.3, wet=True)
        S.reel_down(mix, A(when(name, "lay") + 0.15), gain=0.16, pan=-0.3)
        S.splash(mix, A(when(name, "dive") + 0.62 * at_window(name, "dive")), gain=0.08, pan=-0.3)
    S.cow_breath(mix, A(when("cow", "smell") + 0.75), 1.4, pan=0.15)
    S.breach(mix, A(when("lead", "come_up") + 0.3), 0.7, gain=0.14, pan=0.25)
    for k, tp in enumerate(POPUPS):
        S.reel_down(mix, A(tp + 0.35), gain=0.07, pan=-0.45)
    # 6.5 THE DEFINING PASSAGE
    tb = when("big", "breach")
    S.breach(mix, A(tb + 0.05), 0.8, gain=0.2)
    S.wheels(mix, A(when("big", "roll_up")), 0.9, 1.0, gain=0.07, pan=0.2, pan_to=S.P_SILL + 0.1)
    tp, tt = when("big", "proud"), when("big", "told")
    n_tick = int((when("old", "turn_back") + 1.6 - tp) / 0.25)   # the peg slows and stops as the old dog comes round
    S.peg_tick(mix, A(tp - 0.5), n_tick + 2, 0.25)            # ticking with pride, on alone through the look, stops as the back settles
    S.creak(mix, A(when("old", "turn_back")), 0.5, gain=0.05, pan=S.P_SILL)
    S.old_dog_down(mix, A(when("old", "turn_back") + 0.25), 3, gain=0.1)
    S.drip(mix, A(tt + 0.2), 1)
    S.wheels(mix, A(tt + 0.78), 0.35, 1.0, gain=0.04, pan=S.P_SILL, pan_to=S.P_SILL + 0.05)   # it backs off from the back
    tn = when("cow", "nose")                                  # THE WEAVE: she steps up and noses it back to the water
    S.hooves(mix, A(tn + 0.12), 2, 0.22, "earth", gain=0.09, pan=_pan(COW_X1))
    S.cowbell(mix, A(tn + 0.2), 2, 0.45, gain=0.05, pan=0.3)
    S.wheels(mix, A(tn + 0.55), 0.55, 1.0, gain=0.07, pan=S.P_SILL + 0.05, pan_to=0.2)         # the wooden dog rolled back by her muzzle
    S.hooves(mix, A(tn + 0.7), 2, 0.22, "earth", gain=0.08, pan=_pan(COW_X1))
    S.cow_breath(mix, A(tn + 1.0), 0.8, pan=0.15)
    S.chew(mix, A(when("cow", "chew")), 2, pan=0.2)           # and she chews
    tr = when("big", "roll_back")
    S.wheels(mix, A(tr), 0.5, 1.0, gain=0.05, pan=S.P_SILL, pan_to=0.2)
    if not F("splash", tr + 0.62, 0.25, pan=0.2, seconds=0.9):
        S.splash(mix, A(tr + 0.62), gain=0.14)
    # below: the piece out, the bubble, the page in, the lid, the print
    S.set_down(mix, A(t_in + 0.67), gain=0.07)
    S.page_slap(mix, A(t_in + 1.36), gain=0.04)
    S.ratchet(mix, A(t_in + 1.44), 0.3, 22, gain=0.04, under=True)
    S.set_down(mix, A(t_in + 1.84), gain=0.07)
    S.paw_press(mix, A(t_in + 1.9), under=600)
    S.set_down(mix, A(t_in + 2.12), gain=0.05)                # the can taken up in its mouth
    S.breach(mix, A(t_out + 0.03), 0.8, gain=0.2)
    S.drip(mix, A(t_out + 0.4), 1)
    S.card_drag(mix, A(when("old", "let_pass")), 0.5)         # the tail pulled aside: room is made
    S.reel_down(mix, A(when("big", "lay") + 0.1), gain=0.17)
    if not F("sigh", when("old", "let_pass") + 0.45, 0.07, pan=S.P_SILL):
        S.sigh(mix, A(when("old", "let_pass") + 0.45), 0.8, gain=0.035, pan=S.P_SILL)
    # 6.6 the lit door
    S.cow_down(mix, A(when("cow", "fold")), pan=_pan(COW_X1))  # the bell settles two seconds on
    S.wheels(mix, A(when("big", "leave") + 0.2), 1.5, 1.0, gain=0.045, pan=0.1, pan_to=0.5)
    S.old_dog_down(mix, A(when("old", "walk")), 4, gain=0.08, pan=0.1)
    S.paws(mix, A(when("lead", "walk_up") + 0.5), 5, 0.16, gain=0.06, pan=0.2, pan_to=S.P_SILL, wet=True)
    S.reel_down(mix, A(when("lead", "lay") + 0.45), gain=0.12)
    S.paw_press(mix, A(when("lead", "lie") + 0.95), gain=0.06, pan=S.P_SILL)       # a body on boards
    S.drip(mix, A(179.1), 1, on="water", pan=0.2)             # a tail in water
    S.radio_dial(mix, A(175.25), gain=0.02) if hasattr(S, "radio_dial") else None
    S.fish_murmur(mix, A(177.0), 2.8, gain=0.018, pan=0.2)
    S.peg_tick(mix, A(179.3))
    return mix


# ====================================================================== #
#  11 · CHECKS (MEASURED when this runs)                                 #
# ====================================================================== #

BOARD = [   # who, state, the second it falls on. Up to 161.0 these are the board's seconds. After that they are the
    # repair's (law 10): the long locked gate frame is now five setups, the cow has a turn of her own (nose),
    # the town insert runs 2.6 s so the can is seen taken, and the last crane starts at 175.0.
    ("lead", "stilled", 149.0), ("lead", "ears_down", 150.0), ("lead", "hold", 151.0), ("lead", "look_bubble", 152.6),
    ("lead", "turn", 153.0), ("lead", "dive", 155.0), ("cow", "get_up", 153.5), ("cow", "walk", 154.5), ("cow", "watch", 156.5),
    ("old", "shift", 156.2), ("herder", "breach", 157.2), ("digger", "breach", 158.4), ("sheep", "breach", 159.6),
    ("cow", "smell", 159.8), ("big", "breach", 161.0), ("big", "proud", 162.5), ("old", "raise_", 162.5), ("old", "long_look", 163.7),
    ("old", "turn_back", 164.9), ("old", "back", 167.4), ("big", "told", 167.4), ("big", "nudged", 168.6), ("cow", "nose", 168.6),
    ("cow", "chew", 170.0), ("big", "roll_back", 170.0), ("big", "fix", 170.9), ("big", "come_up", 173.5), ("old", "look_over", 173.9),
    ("old", "let_pass", 174.4), ("big", "lay", 174.75), ("cow", "fold", 175.1), ("old", "rise_turn", 175.55), ("old", "lie_down", 177.5),
    ("old", "beside", 178.4), ("cow", "lie", 177.1), ("big", "rest", 176.75), ("lead", "lie", 177.55),
]
HOLDS = [(151.0, 152.6, "the lead dog, ears down"), (163.75, 164.9, "the old dog and the reel")]


def _ends(logs):
    return {k: v[-1][1] for k, v in logs.items()}


def check(verbose=True):
    out = {}
    logs = film()
    ms = dict(lead=lead_machine(), old=old_machine(), herder=passer_machine("herder"), sheep=passer_machine("sheep", **SHEEP_KW),
              big=big_machine(), cow=cow_machine())
    # 1 the board's seconds come out of the guards and windows, to within one frame (two where a guard waits on another machine)
    worst = 0.0
    for who, state, sec in BOARD:
        got = when(who, state)
        assert got is not None, (who, state, "never entered")
        tol = 2 * DT + 1e-6
        assert abs(got - sec) <= tol, (who, state, sec, round(got, 3))
        worst = max(worst, abs(got - sec))
    out["board seconds reproduced, worst miss (s)"] = round(worst, 3)
    # 2 nobody is left in a state that is not an ending
    for k, m in ms.items():
        e = _ends(logs)[k]
        assert m.states[e].end, (k, "stuck in", e)
    out["endings"] = _ends(logs)
    # 3 every declared state is reached, in the film or in a run with the circumstances changed
    reached = {k: {e[1] for e in v} for k, v in logs.items()}
    right_first = {k: dict(v) for k, v in REELS.items()}
    right_first["big"]["tidy"] = False
    logs_right, _ = run(reels=right_first)
    logs_noask, _ = run([c for c in CIRCUMSTANCES if c[1] != "no"])
    for alt in (logs_right, logs_noask):
        for k, v in alt.items():
            reached[k] |= {e[1] for e in v}
    for k, m in ms.items():
        missing = set(m.states) - reached[k]
        assert not missing, (k, "unreachable", missing)
    out["states"] = {k: len(m.states) for k, m in ms.items()}
    # 4 the choice is conditioned on declared state: the refusal goes when its cause goes
    assert "turn_back" in {e[1] for e in logs["old"]}
    assert "turn_back" not in {e[1] for e in logs_right["old"]}, "a right reel was refused"
    assert "told" not in {e[1] for e in logs_right["big"]} and "fix" not in {e[1] for e in logs_right["big"]}
    assert _ends(logs_right)["big"] == "rest" and _ends(logs_right)["old"] == "beside" and _ends(logs_right)["cow"] == "lie"
    assert {e[1] for e in logs_noask["lead"]} == {"pleased"}, "the dog went again without being told no"
    assert {e[1] for e in logs_noask["big"]} == {"under"}, "a pack worked that nobody called"
    out["counterfactuals"] = "right reel: passed at the first look; no 'no': no pack"
    # 5 the old dog never lets a tidy reel pass, in any run
    for lg, rl in ((logs, REELS), (logs_right, right_first)):
        for (fe, s, why) in lg["old"]:
            if s == "let_pass":
                assert fe >= when("big", "come_up") - 1e-6
    # 6 the refusal has a visible consequence: the reel that is laid is not the reel that was refused
    assert big_look(when("big", "proud")) == "tidy" and big_look(when("big", "offer_low")) == "wobbly"
    # 7 the holds: nothing in the machines changes inside them, and the camera is locked
    for a, b, what in HOLDS:
        for k, v in logs.items():
            for (fe, s, why) in v:
                assert not (a + 1e-6 < fe < b - 1e-6), (what, k, s, fe)
        assert shot_at(a + 0.01) == shot_at(b - 0.01), (what, "a cut inside a hold")
    # 7b the gate (157.0 to the town insert) is at least three setups, one of them a two-shot of a dog and the cow
    names = [sh[2] for sh in shots() if 157.0 <= sh[0] < when("big", "fix")]
    assert len(names) >= 5 and "smell" in names and "nudge" in names, names
    assert max(sh[1] - sh[0] for sh in shots() if sh[0] >= 157.0) <= 3.5, "a setup runs too long"
    # 7c the exchange: the cow's step and shove come before the dog goes down, and move it
    assert when("cow", "nose") == when("big", "nudged") and when("big", "roll_back") > when("cow", "nose") + 1.0
    assert big_state(when("big", "roll_back") - DT)[0] - big_state(when("big", "nudged"))[0] >= NUDGE_PX - 1.0
    assert abs(cow_xy(when("cow", "nose") + 0.55)[0] - COW_X1) >= NOSE_STEP - 1.5, "she did not step"
    # 7d no card animal is ever drawn edge-on in a turn
    for i in range(int(SECONDS * FPS)):
        fq = T0 + i * DT
        st_, sn_ = at("old", fq)
        if st_ == "turn_back":
            assert abs(old_P("turn_back", p=clamp(sn_ / 2.5))["sx"]) >= FLIP_MIN - 1e-6
    # 8 the record, counted from the ledgers
    assert len(PEBBLES) == 67 and PEBBLES.count("w") == 16 and "ww" not in PEBBLES[2:], (len(PEBBLES), PEBBLES.count("w"))
    assert pebbles_at(T0) == 30 and pebbles_at(T1) == 67
    assert cans_at(T0) == 3 and cans_at(T1) == 53, (cans_at(T0), cans_at(T1))
    assert cans_at(175.0) == 52                              # all but the lead dog's own last one (said in the report)
    assert len({e[2] for e in ledger()}) == N_PILED
    paws = 1 + 1 + 1 + 1 + sum(1 for e in ledger() if e[3])   # the page, the first reel, the refused reel, the changed reel, eight lids
    assert paws == 12, paws
    assert len(SIX) + len(curtain()) == 37 and len(lantern_pack()) == 17 and len(SLEEPERS) == 11
    out["record"] = "67 pebbles (16 white), 53 cans, 12 paw prints, 37 under in 6.3, 17 with lanterns, 11 asleep"
    # 9 crossings: every dog that goes down in sight and comes up in sight comes up with a thing
    downs = [("lead", when("lead", "dive"), when("lead", "come_up")), ("big", when("big", "roll_back") + 0.62, when("big", "come_up"))]
    for who, d, u in downs:
        assert u is not None and u > d
    out["crossings"] = "lead down 155.0 up 161.0 with a reel; retriever down 170.7 up 173.5 with it changed; three passers up with reels, down again"
    # 10 words on screen: none. This module draws no lettering at all (the end credit that was lettered here is gone).
    src = Path(__file__).read_text()
    for banned in ("ink." + "text(", "ink." + "caption(", "ink." + "label(", "ink." + "card(", "town." + "bubble("):
        assert banned not in src, banned
    out["words"] = 0
    # 11 the camera never leaves the rendered frame
    for i in range(int(SECONDS * 8)):
        f = T0 + i / 8
        cx, cy, z = camera(f)
        oy = int(round(cy - H / 2))
        assert oy >= 0 and cx - W / 2 / z >= -0.5 and cx + W / 2 / z <= W + 0.5, (f, cx, cy, z)
    if verbose:
        for k, v in out.items():
            print(f"  {k}: {v}")
        for k in ORDER:
            print(" ", k, " ".join(f"{s}@{fe:.2f}" for fe, s, _ in logs[k]))
    return out


# ====================================================================== #
#  12 · STILLS, SHEETS, RENDER                                           #
# ====================================================================== #

def still(f):
    ink = kit.Ink(f - T0, int(round((f - T0) * FPS)))
    ink.paper()
    draw(f - T0, ink)
    return ink.finish()


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
        out = _HERE.parent.parent / "stills" / "dogs-s6"
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
    film_ = kit.Film("dogs-s6", seconds=SECONDS)
    film_.picture(draw)
    film_.sound(lambda mix: sound(mix, 0.0))
    film_.poster_at = 21.0
    film_.render()


if __name__ == "__main__":
    main()
