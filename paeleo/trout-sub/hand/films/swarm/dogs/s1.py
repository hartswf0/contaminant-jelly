"""S1 · THE DOOR · 0.0 to 28.0 of "The Dogs of Trouttown".

    import s1
    s1.SECONDS                 # 28.0
    s1.draw(t, ink)            # a full 960x540 frame; t in seconds since the sequence began
    s1.sound(mix, at)          # this sequence's sound, laid into a kit.Mix starting at film second `at`

Built by one agent working `scion/animation-48.md` (STATE MACHINES: characters that can refuse).
The lead dog in this sequence is not put through a list of timed poses. It is a small machine: STATES,
guarded TRANSITIONS with priorities, action windows (minimum dwells), a memory (pressure, quiet) and a
persistent place on the sill. What the authors control is the WORLD (the cow comes level; the person
calls, reaches, sits, turns the radio on). The dog's evening comes out of running the machine over that
world, and `check()` runs it again over three other evenings in which it must NOT go into the water.

Staging is the board's (`board.md`, S1). Sets and cast are imported, never edited:
porch.py (set, person), herd.py (cows), dog.py (lead dog), town.py (Trouttown), sound.py (sound library).

Run alone:  python3 films/swarm/dogs/s1.py            -> assets/films/dogs-s1.mp4
            python3 films/swarm/dogs/s1.py --stills 3.75 19.5 ...
            python3 films/swarm/dogs/s1.py --sheets   -> contact sheets in films/stills/dogs-s1/
            python3 films/swarm/dogs/s1.py --check    -> the machine's tests only
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import kit  # noqa: E402
from kit import clamp, ease, lerp, ramp, smooth  # noqa: E402

import dog  # noqa: E402
import herd  # noqa: E402
import porch  # noqa: E402
import town  # noqa: E402
import importlib.util as _ilu  # noqa: E402

# herd.py puts films/swarm/cowpath on the path, and that folder has its own sound.py: load ours by file
_spec = _ilu.spec_from_file_location("dogs_sound", str(HERE / "sound.py"))
snd = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(snd)

SECONDS = 28.0
W, H, FPS = 960, 540, 24
DT = 1.0 / FPS

DOG_S = 0.6                       # the board's size for the lead dog in F-PORCH
SILL_Y = 394.0                    # where a dog's feet stand on the sill
SPOT_X = 470.0                    # the lead dog's waiting spot
SILL_END = 547.5                  # the last dry-ish footing: past this the board ends and the creek is deep
ENTRY_X = 592.0                   # where the dog goes through the line (beside the cow's muzzle at 600)
TEAL = (24, 120, 128)


# ====================================================================== #
#  1 · THE WORLD: what the authors may change. Nothing here moves the dog #
# ====================================================================== #
# A list of (time, {circumstance: value}). The person and the cow are performed from the same table
# (see `person_q` and `_walkers`), so the dog's machine and the picture read one evening.

WORLD = [
    (0.0, dict(cow="coming", voice="none", hand="none", posture="stand", radio=0)),
    (3.0, dict(cow="level")),              # the lead cow has come level with the dog and lowered her head
    (5.2, dict(cow="passing")),            # she chews again and walks on
    (6.2, dict(voice="call")),             # Line 1, with four taps on the rail
    (8.6, dict(cow="drinking")),
    (7.6, dict(voice="none")),
    (8.0, dict(hand="reach")),             # the hand comes
    (10.5, dict(hand="none")),             # the hand drops
    (11.0, dict(posture="sitting")),
    (12.5, dict(posture="sit")),           # seated on the step
    (14.0, dict(radio=1)),                 # the radio is on; now the person only waits
]

REACH_T0, REACH_T1 = 8.0, 9.2              # the hand travels over these seconds (the person's `reach` key)


def circumstances(t, world=WORLD):
    """The world at time t: every circumstance's latest value."""
    w = {}
    for tt, d in sorted(world, key=lambda e: e[0]):
        if tt <= t + 1e-9:
            w.update(d)
    return w


def _since(t, world, key, value):
    """Seconds for which `key` has had `value` at time t (0 if it has not)."""
    start, cur = None, None
    for tt, d in sorted(world, key=lambda e: e[0]):
        if tt > t + 1e-9:
            break
        if key in d:
            if d[key] == value and cur != value:
                start = tt
            cur = d[key]
    return (t - start) if cur == value and start is not None else 0.0


# ---- the person, performed from the same table -------------------------------------------------------

TAPS = (6.3, 6.6, 6.9, 7.4)                # short short long short: "Will you fetch it?"
PEBBLE_T = 7.8


def _tap_p(t):
    """1 = the hand is down on the rail, 0 = lifted."""
    p = 0.0
    for k, tt in enumerate(TAPS):
        dur = 0.34 if k == 2 else 0.2       # the third is the long one
        p = max(p, kit.clamp(1 - abs(t - (tt + dur * 0.35)) / (dur * 0.65)))
    return smooth(p)


def person_keys(world=WORLD):
    """porch.act keys for the person. The hand's reach is the WORLD's `hand` circumstance."""
    px, py = porch.pebble_spot(0)
    return [
        (0.0, "stand"),
        (5.9, "stand"),
        (6.3, "call", {"dur": 0.4, "p": 0.8}),
        (PEBBLE_T - 0.38, "call", {"dur": 0.3, "p": 0.55}),
        (PEBBLE_T, "tap", {"dur": 0.38, "at": (px, py - 2)}),
        (8.0, "tap", {"dur": 0.1, "at": (px, py - 2)}),
        (REACH_T1, "reach", {"dur": REACH_T1 - REACH_T0}),
        (10.5, "reach"),
        (11.0, "stand", {"x": 205, "dur": 0.5}),
        (12.5, "sit", {"dur": 1.5}),
        (13.0, "sit"),
        (14.0, "set_radio", {"dur": 1.0}),
        (14.45, "set_radio"),
        (15.2, "sit", {"dur": 0.7}),
    ]


def person_q(t):
    """The person's pose at t. The taps ride on top of the call; the foot taps while the radio plays and
    stops when the dog looks round (the person holds still: that is all they do to earn it)."""
    q = porch.act(t, person_keys())
    if 6.2 <= t < PEBBLE_T - 0.38:
        tap = porch.pose("tap", p=_tap_p(t), t=t)
        q = porch.blend(q, tap, 0.85 * ease(t, 6.2, 6.3))
    if t > 15.2:
        back = TR.t("WEIGH_PERSON") if TR else 17.0
        foot = (0.5 - 0.5 * math.cos(2 * math.pi * (t - 15.2) / 1.1)) * (1 - ease(t, back + 0.15, back + 0.5))
        q = porch.blend(q, porch.pose("sit", p=foot, t=t), 1.0) if foot > 0.01 else q
    return q


@lru_cache(maxsize=None)
def _hand_track():
    """World x of the person's reaching hand for every frame of the reach: the dog answers THIS, a thing
    in the picture, so the retreat is as far as the hand really came."""
    out = {}
    for k in range(int(REACH_T0 * FPS), int(10.6 * FPS) + 1):
        t = k / FPS
        im = Image.new("RGB", (W, H))
        out[k] = porch.person(im, t, 0, porch.act(t, person_keys()), shadow=False)["hand_a"][0]
    return out


def hand_x(t, world=WORLD):
    """Where the reaching hand is (world x); None when no hand is out."""
    if circumstances(t, world).get("hand") != "reach":
        return None
    tr = _hand_track()
    # other evenings (the tests) reach at other times: the same reach, started when theirs starts
    tau = _since(t, world, "hand", "reach")
    k = int(round((REACH_T0 + min(tau, 2.5)) * FPS))
    return tr[max(min(k, max(tr)), min(tr))]


# ====================================================================== #
#  2 · THE DOG'S MACHINE (animation-48's primitives, as data)             #
# ====================================================================== #

STATES = {
    # name            intention (what the dog wants in it)                          action window (min dwell, s)
    "WATCH":        ("to look at the water",                                         0.0),
    "GREET":        ("to find out who the big animal is",                            2.2),
    "LISTEN":       ("to hear the voice without giving it the body",                 0.0),
    "GLANCE":       ("to see what is coming up behind",                              0.25),
    "YIELD":        ("to keep exactly the distance it had",                          0.0),
    "AWAY":         ("to show it was not fetched",                                   1.0),
    "WEIGH_WATER":  ("to look at where it could go",                                 1.5),
    "WEIGH_PERSON": ("to see whether it is being made to",                           1.3),
    "WEIGH_AGAIN":  ("to look once more, now that nobody is making it",              1.2),
    "RESOLVE":      ("nothing: it is deciding",                                      1.0),
    "LIFT":         ("to go",                                                        0.5),
    "GO":           ("to reach the wet end of the board",                            0.0),
    "WADE":         ("to get in up to the chest",                                    0.37),
    "UNDER":        ("to go down",                                                   1e9),
}

COMFORT = 212.0        # px from the hand to the middle of the dog that the dog keeps
WALK_PX = 63.0         # px a second, walking along the sill to the wet end
WADE_PX = 95.0
PRESSURE_UP = dict(call=0.35, reach=0.9)
PRESSURE_DOWN = 0.22
QUIET_NEEDED = 1.5     # seconds of sitting, radio on, hands still, before the dog will even consider it


def _too_close(m, w):
    return w.get("hand_x") is not None and (m["x"] - w["hand_x"]) < COMFORT - 0.5


def _quiet(w):
    return w["posture"] == "sit" and w["radio"] == 1 and w["hand"] == "none" and w["voice"] == "none"


# Guards, highest priority first. A transition marked interrupt=True may break an action window.
# (from states, to, guard(m, w), priority, interrupt, why)
DRY = ("WATCH", "GREET", "LISTEN", "GLANCE", "AWAY", "WEIGH_WATER", "WEIGH_PERSON", "WEIGH_AGAIN", "RESOLVE", "LIFT", "GO")
TRANSITIONS = [
    (DRY, "YIELD", lambda m, w: _too_close(m, w), 9, True,
     "a hand is nearer than it allows: it moves off, and no further than the hand came"),
    (("WATCH", "LISTEN", "AWAY", "WEIGH_WATER", "WEIGH_PERSON", "WEIGH_AGAIN", "RESOLVE", "LIFT"), "GLANCE",
     lambda m, w: w["hand"] == "reach" and w["hand_since"] >= 0.3 and m["state"] != "GLANCE" and not m["glanced"], 8, True,
     "something is coming from behind: one look"),
    (("YIELD",), "AWAY", lambda m, w: not _too_close(m, w) and m["still"] >= 0.2, 7, False,
     "the hand has stopped; so has the dog; it looks elsewhere"),
    (("GLANCE",), "AWAY", lambda m, w: w["hand"] == "none", 6, False, "the hand went away by itself"),
    (("WATCH",), "GREET", lambda m, w: w["cow"] == "level" and m["pressure"] < 0.3, 6, False,
     "the lead cow has stopped beside it and put her head down"),
    (("GREET",), "WATCH", lambda m, w: w["cow"] != "level", 5, False, "it knows her now; she goes on"),
    (("WATCH",), "LISTEN", lambda m, w: w["voice"] == "call" and w["voice_since"] >= 0.2, 5, False,
     "a voice: one ear goes to it, the body does not"),
    (("LISTEN",), "WATCH", lambda m, w: w["voice"] != "call" and w["voice_off"] >= 0.2, 5, False, "the voice stopped"),
    (("AWAY",), "WATCH", lambda m, w: w["hand"] == "none" and m["pressure"] < 0.8, 4, False, "nobody is reaching"),
    (("WATCH",), "WEIGH_WATER", lambda m, w: m["quiet"] >= QUIET_NEEDED and m["pressure"] < 0.15, 3, False,
     "nobody has asked anything of it for a while"),
    (("WEIGH_WATER",), "WEIGH_PERSON", lambda m, w: True, 2, False, "is it being made to?"),
    (("WEIGH_PERSON",), "WEIGH_AGAIN", lambda m, w: _quiet(w), 2, False, "the person did not reach"),
    (("WEIGH_PERSON",), "WATCH", lambda m, w: not _quiet(w), 1, False, "the person moved: not now"),
    (("WEIGH_AGAIN",), "RESOLVE", lambda m, w: _quiet(w), 2, False, "still nobody is making it"),
    (("WEIGH_AGAIN",), "WATCH", lambda m, w: not _quiet(w), 1, False, "not now"),
    (("RESOLVE",), "LIFT", lambda m, w: _quiet(w), 2, False, "it has decided"),
    (("RESOLVE",), "WATCH", lambda m, w: not _quiet(w), 1, False, "not now"),
    (("LIFT",), "GO", lambda m, w: True, 2, False, "it goes"),
    (("GO",), "WADE", lambda m, w: m["x"] >= SILL_END - 0.01, 2, False, "the board ends"),
    (("WADE",), "UNDER", lambda m, w: True, 2, False, "head first"),
]


def run_mind(world=WORLD, T=SECONDS, x0=SPOT_X):
    """Run the dog's machine over an evening. Returns one frame dict per 1/24 s:
    {t, state, since, x, pressure, quiet, why}. Nothing in here knows a beat's time."""
    m = dict(state="WATCH", since=0.0, x=x0, pressure=0.0, quiet=0.0, still=0.0, glanced=False, why="")
    frames = []
    n = int(round(T * FPS)) + 1
    for k in range(n):
        t = k / FPS
        w = circumstances(t, world)
        w["hand_x"] = hand_x(t, world)
        w["hand_since"] = _since(t, world, "hand", "reach")
        w["voice_since"] = _since(t, world, "voice", "call")
        w["voice_off"] = _since(t, world, "voice", "none")
        # memory
        up = (PRESSURE_UP["reach"] if w["hand"] == "reach" else 0.0) + (PRESSURE_UP["call"] if w["voice"] == "call" else 0.0)
        m["pressure"] = clamp(m["pressure"] + (up if up else -PRESSURE_DOWN) * DT)
        m["quiet"] = m["quiet"] + DT if _quiet(w) else 0.0
        if w["hand"] == "none":
            m["glanced"] = False
        # decide
        window = STATES[m["state"]][1]
        for src, to, guard, prio, interrupt, why in sorted(TRANSITIONS, key=lambda r: -r[3]):
            if m["state"] not in src or to == m["state"]:
                continue
            if m["since"] < window - 1e-6 and not interrupt:
                continue
            if guard(m, w):
                if to == "GLANCE":
                    m["glanced"] = True
                m.update(state=to, since=0.0, why=why, still=0.0)
                break
        # act: only three states move the dog along the board, and each by a rule
        x_before = m["x"]
        if m["state"] == "YIELD" and w["hand_x"] is not None:
            want = w["hand_x"] + COMFORT
            m["x"] = min(max(m["x"], min(want, m["x"] + 85.0 * DT)), SILL_END - 8)     # a walk, never a jump
        elif m["state"] == "GO":
            m["x"] = min(SILL_END, m["x"] + WALK_PX * DT)
        elif m["state"] == "WADE":
            m["x"] = m["x"] + WADE_PX * DT
        m["still"] = m["still"] + DT if abs(m["x"] - x_before) < 1e-6 else 0.0
        frames.append(dict(t=t, state=m["state"], since=m["since"], x=m["x"], pressure=m["pressure"],
                           quiet=m["quiet"], why=m["why"]))
        m["since"] += DT
    return frames


class Trace:
    """The machine's run, with look-ups for the picture."""

    def __init__(self, frames):
        self.frames = frames
        self.enters = []                    # [(t, state)] each time a state is entered
        prev = None
        for f in frames:
            if f["state"] != prev:
                self.enters.append((f["t"], f["state"]))
                prev = f["state"]

    def at(self, t):
        return self.frames[max(0, min(len(self.frames) - 1, int(math.floor(t * FPS + 1e-6))))]

    def x(self, t):
        k = t * FPS
        i = max(0, min(len(self.frames) - 2, int(math.floor(k))))
        return lerp(self.frames[i]["x"], self.frames[i + 1]["x"], clamp(k - i))

    def t(self, state, nth=0):
        """When `state` was entered (the nth time); None if never."""
        hits = [tt for tt, s in self.enters if s == state]
        return hits[nth] if len(hits) > nth else None

    def left(self, state, nth=0):
        """When `state` was left."""
        seen = 0
        for (tt, s), nxt in zip(self.enters, self.enters[1:] + [(SECONDS + 1, None)]):
            if s == state:
                if seen == nth:
                    return nxt[0]
                seen += 1
        return None

    def prev_state(self, t):
        cur = None
        last = None
        for tt, s in self.enters:
            if tt <= t + 1e-9:
                last, cur = cur, s
        return last


TR = None


def _trace():
    global TR
    if TR is None:
        TR = Trace(run_mind())
    return TR


def check(verbose=True):
    """MEASURED. The machine against the board, and against three evenings in which it must refuse."""
    tr = Trace(run_mind())
    board = dict(GREET=3.0, WEIGH_WATER=15.5, WEIGH_PERSON=17.0, WEIGH_AGAIN=18.3, RESOLVE=19.5, LIFT=20.5,
                 GO=21.0, WADE=21.6, UNDER=22.0)
    out = []
    for s, want in board.items():
        got = tr.t(s)
        assert got is not None and abs(got - want) <= 1.5 * DT, (s, got, want)
        out.append(f"{s} entered at {got:.3f} (board {want})")
    ty = tr.t("YIELD")
    assert ty is not None and REACH_T0 < ty < REACH_T1 + 0.2, ty
    # the retreat is as far as the hand intruded, and the distance is kept
    hx_end = hand_x(REACH_T1 + 0.5)
    moved = tr.x(10.4) - SPOT_X
    intruded = hx_end + COMFORT - SPOT_X
    assert abs(moved - intruded) < 1.0, (moved, intruded)
    worst = min(f["x"] - hand_x(f["t"]) for f in tr.frames if hand_x(f["t"]) is not None)
    assert worst > COMFORT - 20.0, worst                     # the hand is quicker than a walk: it gets this near, no nearer
    out.append(f"hand intruded {intruded:.1f} px, dog moved {moved:.1f} px; closest {worst:.1f} px (keeps {COMFORT})")
    # no state is absorbing by accident, and all are reachable in some evening below
    seen = {s for _, s in tr.enters}
    # it never goes toward the hand
    xs = [f["x"] for f in tr.frames]
    assert all(b >= a - 1e-9 for a, b in zip(xs, xs[1:])), "the dog moved toward the door"
    # evening 2: the person never sits down. The dog must not go.
    w2 = [e for e in WORLD if e[0] < 10.9]
    t2 = Trace(run_mind(w2))
    assert t2.t("UNDER") is None and t2.t("WEIGH_WATER") is None
    out.append("never sits: the dog never considers the water")
    # evening 3: the person reaches again while the dog is looking back at them. The dog must refuse.
    w3 = WORLD + [(17.4, dict(hand="reach")), (19.0, dict(hand="none"))]
    t3 = Trace(run_mind(w3))
    assert t3.t("UNDER") is None or t3.t("UNDER") > 22.0 + 2.0, t3.t("UNDER")
    assert t3.t("GLANCE", 1) is not None or t3.t("YIELD", 1) is not None
    seen |= {s for _, s in t3.enters}
    out.append(f"reaches again at 17.4: goes under at {t3.t('UNDER')} (not at 22.0); states {[s for _, s in t3.enters if _ > 17]}")
    # evening 4: the person keeps calling from the step. The dog listens and never goes.
    w4 = WORLD + [(15.0, dict(voice="call")), (27.0, dict(voice="none"))]
    t4 = Trace(run_mind(w4))
    assert t4.t("UNDER") is None
    seen |= {s for _, s in t4.enters}
    out.append("keeps calling: the dog listens and stays")
    assert seen == set(STATES), set(STATES) - seen
    out.append(f"all {len(STATES)} states reached; x never decreases")
    if verbose:
        for line in out:
            print("  check:", line)
    return out


# ====================================================================== #
#  3 · THE DOG'S BODY: what each state looks like                         #
# ====================================================================== #

def _water_look(p, amount=1.0):
    """Head carried a little lower and forward: looking down at the water, not at the far bank."""
    q = dict(p)
    q["neck"] = lerp(p["neck"], 0.62, amount)
    q["head"] = lerp(p["head"], -0.22, amount)
    return q


GREET = dict(ear=0.0, round=0.3, contact=0.75, hold_end=1.55, breath=1.6, breath_end=2.05)   # herd.NOSE_TOUCH's clock


def _greet_pose(tau, t, follow=1.0):
    """The nose touch. She has stopped BEHIND the dog (both face the water), so the dog looks back over
    its shoulder and up, and the two muzzles meet tip to tip in profile, above the dog's back.
    The near ear goes to her first and the tail starts, low and slow; then the head comes round; they
    hold; she breathes out and the dog's ears blow flat; they spring up again. `follow` 1..0 lets the
    head come back round to the front as she walks on past."""
    a = dog.ease_back(clamp((tau - GREET["round"]) / (GREET["contact"] - GREET["round"]))) * follow
    p = dog.watch(t)
    p["ear"] = lerp(p["ear"], 0.12, ease(tau, 0.0, 0.14))               # hears her stop: the torn ear goes back
    p = dog.over_shoulder(p, a)
    p = dog.look_up(p, 0.62 * a)
    if tau > GREET["round"]:
        e = ease(tau, GREET["round"], GREET["round"] + 0.2)
        p["ear"], p["ear_f"] = lerp(p["ear"], 1.05, e), lerp(p["ear_f"], 1.05, e)
    # held: nostrils working is all (a breath of a nod)
    if GREET["contact"] <= tau < GREET["hold_end"]:
        p["head"] += 0.012 * math.sin(2 * math.pi * 3.2 * tau)
    # her breath: ears blown back in three frames, eye shut, the head gives; then they spring up
    b = ease(tau, GREET["breath"], GREET["breath"] + 0.12) * (1 - dog.ease_back(clamp((tau - GREET["breath_end"]) / 0.3)))
    if b > 0 or tau > GREET["breath"]:
        p["ear"], p["ear_f"] = lerp(p["ear"], -0.05, b), lerp(p["ear_f"], 0.0, b)
        p["eye"] = lerp(p.get("eye", 1.0), 0.25, clamp(b))
        p["neck"] -= 0.07 * b
    wag = ease(tau, 0.1, 0.5)
    p["tail"], p["curl"] = lerp(p["tail"], 0.05, wag), lerp(p["curl"], 0.25, wag)
    p["wag"] = 0.34 * wag * math.sin(2 * math.pi * 1.15 * tau) * (1.6 if tau > GREET["breath_end"] else 1.0)
    return p


def _follow_amount(t):
    """After the touch the dog's head follows the cow as she walks past behind it: 1 while her muzzle is
    behind its shoulder, 0 once she has gone by. Driven by where she IS, not by a time."""
    cx = _walkers()["lead"].state(t, bell=False)["x"]          # her middle; her head is a cow's neck ahead of it
    f = clamp((SPOT_X - 52.0 - cx) / 30.0)
    # the paper head does not hang edge-on: when she passes its shoulder it loses her and whips round to the front
    return 1.0 if f >= 0.999 else smooth(clamp((f - 0.42) / 0.26))


def _state_pose(state, t, tr, t_in):
    """The pose a state holds at time t (t_in = when the state was entered)."""
    tau = t - t_in
    if state == "GREET":
        return _greet_pose(tau, t)
    if state == "LISTEN":
        p = _watch_pose(t, tr)               # still watching her go, or the water
        p["ear"] = 0.12                      # the torn ear goes back to the voice; the far ear and the body do not
        return p
    if state == "GLANCE":
        p = dog.over_shoulder(dog.watch(t), dog.ease_back(clamp(tau / 0.24)))     # right round: it looks at the hand
        p["ear"], p["ear_f"] = 0.75, 0.8
        return p
    if state == "YIELD":
        ph = (tr.x(t) - tr.x(t_in)) / (dog.STRIDE["walk"] * DOG_S)
        p = dog.walk(phase=ph)
        p["tail"], p["curl"] = 0.18, 0.2     # level: it is not afraid
        p["ear"], p["ear_f"] = 0.35, 0.6
        return dog.over_shoulder(p, 1 - ease(tau, 0.02, 0.26))                    # and away again: it does not watch it come
    if state == "AWAY":
        ph = (tr.x(t) - tr.x(tr.t("YIELD") or t_in)) / (dog.STRIDE["walk"] * DOG_S)
        p = dog.blend(dog.walk(phase=ph), dog.stand(t), ease(tau, 0.0, 0.4))
        p = _water_look(p, 0.8 * ease(tau, 0.05, 0.5))
        p["ear"], p["ear_f"] = 0.62, 0.7
        p["tail"], p["curl"] = 0.16, 0.2
        return p
    if state == "WEIGH_WATER" or state == "WEIGH_AGAIN":
        p = _water_look(dog.watch(t, alert=1.0), ease(tau, 0.0, 0.55))
        p["ear"], p["ear_f"] = 1.0, 1.05
        return p
    if state == "WEIGH_PERSON":
        a = ease(tau, 0.12, 0.6)
        p = dog.over_shoulder(dog.watch(t), a)
        p["ear"], p["ear_f"] = 0.9, 0.95
        return p
    if state == "RESOLVE":
        p = _water_look(dog.watch(0.0, alert=1.0), 1.0)          # t frozen: nothing breathes, nothing flicks
        p["ear"], p["ear_f"] = 1.2, 1.2                          # both hard forward, the torn one too
        p["cx"] += 5.0                                           # its weight has gone forward, toward the water
        p["neck"] -= 0.06
        return p
    if state == "LIFT":
        p = _water_look(dog.watch(0.0, alert=1.0), 1.0)
        p["ear"], p["ear_f"] = 1.2, 1.2
        p["cx"] += 5.0
        p["neck"] -= 0.06
        up = dog.ease_back(clamp(tau / 0.42)) if hasattr(dog, "ease_back") else ease(tau, 0, 0.42)
        p["tail"] = lerp(p["tail"], 0.92, up)
        p["curl"] = lerp(p["curl"], 0.5, up)
        return p
    if state == "GO":
        ph = (tr.x(t) - tr.x(t_in)) / (dog.STRIDE["walk"] * DOG_S)
        p = dog.walk(phase=ph)
        p["tail"], p["curl"] = 0.9, 0.5
        p["ear"], p["ear_f"] = 1.1, 1.1
        return _water_look(p, 0.5)
    if state == "WADE":
        ph = (tr.x(t) - tr.x(t_in)) / (dog.STRIDE["wade"] * DOG_S)
        p = dog.wade(ph / dog.RATE["wade"], depth=0.9)
        up = ease(tau, 0.0, 0.14) * (1 - ease(tau, 0.14, 0.24))  # the anticipation: the head comes up a breath
        dip = ease(tau, 0.16, 0.37)                              # ... and goes first
        p["neck"] = lerp(p["neck"] + 0.14 * up, -0.05, dip)
        p["head"] = lerp(p["head"] + 0.1 * up, -0.85, dip)
        p["pitch"] = p.get("pitch", 0.0) - 0.42 * dip
        p["tail"] = lerp(p["tail"], 0.95, dip)
        p["ear"], p["ear_f"] = 1.1, 1.1
        return p
    return _watch_pose(t, tr)


def _watch_pose(t, tr):
    """WATCH: the water; or, just after the touch, the cow as she walks on past."""
    if circumstances(t).get("cow") == "passing" and tr.t("GREET") is not None and t < tr.t("GREET") + 6.0:
        f = _follow_amount(t)                       # watches her go, then looks at the water again
        if f > 0.002:
            return _greet_pose(t - tr.t("GREET"), t, follow=f)
        p = dog.watch(t)
        p["wag"] = 0.2 * math.sin(2 * math.pi * 1.15 * t) * (1 - ease(t, 6.4, 7.2))
        return p
    return dog.watch(t)


def dog_pose(t):
    """The dry-land dog at time t: the state's pose, entered ears first, then tail, head, body, feet."""
    tr = _trace()
    f = tr.at(t)
    state = f["state"]
    # entry time of the current state
    t_in = max(tt for tt, s in tr.enters if tt <= t + 1e-9)
    cur = _state_pose(state, t, tr, t_in)
    prev = tr.prev_state(t)
    tau = t - t_in
    if prev is None or tau > 0.6 or state == "GREET" or (prev == "GREET" and state == "WATCH"):
        return cur
    # the state before, carried on for a moment, so the change runs through the body in order
    t_prev_in = max(tt for tt, s in tr.enters if tt < t_in - 1e-9)
    old = _state_pose(prev, t, tr, t_prev_in)
    quick = state in ("YIELD", "GLANCE")
    k = 0.55 if quick else 1.0
    w = dict(ears=ease(tau, 0.0, 0.12 * k), tail=ease(tau, 0.02, 0.22 * k), head=ease(tau, 0.04, 0.34 * k),
             body=ease(tau, 0.08, 0.42 * k), legs=ease(tau, 0.08, 0.42 * k))
    return dog.blend(old, cur, w)


# ---- under water: the first crossing and the look at the town ------------------------------------------

T_UNDER = 22.0
# (time, world x, world y, facing, pitch): the middle of the dog's body
SWIM_KEYS = [
    (22.00, 590.0, 398.0, 1.0, -0.95),
    (22.35, 600.0, 428.0, 1.0, -1.05),
    (22.80, 609.0, 462.0, 1.0, -0.95),
    (23.50, 614.0, 496.0, 1.0, -0.50),
    (24.10, 606.0, 510.0, 1.0, -0.20),
    (24.60, 582.0, 514.0, -1.0, -0.05),     # it turns to the first lamp coming on, at the left
    (25.60, 470.0, 510.0, -1.0, -0.05),
    (26.40, 350.0, 498.0, -1.0, 0.0),
    (26.90, 282.0, 490.0, -1.0, 0.05),
    (27.35, 266.0, 494.0, 1.0, -0.35),      # the lights have run past it to the right: it turns after them
    (28.00, 300.0, 530.0, 1.0, -0.72),      # the boundary frame: screen (300, 170), nose down and right, as S2 begins
    (28.60, 372.0, 612.0, 1.0, -0.72),
]


def _hermite(keys, t, col):
    if t <= keys[0][0]:
        return keys[0][col]
    if t >= keys[-1][0]:
        return keys[-1][col]
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a[0] <= t <= b[0]:
            h = b[0] - a[0]
            u = (t - a[0]) / h
            pa = keys[i - 1] if i > 0 else a
            pb = keys[i + 2] if i + 2 < len(keys) else b
            ma = (b[col] - pa[col]) / max(b[0] - pa[0], 1e-6) * h
            mb = (pb[col] - a[col]) / max(pb[0] - a[0], 1e-6) * h
            u2, u3 = u * u, u * u * u
            return ((2 * u3 - 3 * u2 + 1) * a[col] + (u3 - 2 * u2 + u) * ma
                    + (-2 * u3 + 3 * u2) * b[col] + (u3 - u2) * mb)
    return keys[-1][col]


def swim_state(t):
    """(x, y, facing, pitch) of the swimming dog at t (world)."""
    x = _hermite(SWIM_KEYS, t, 1)
    y = _hermite(SWIM_KEYS, t, 2)
    # facing flips like the paper cut-out it is, over 0.5 s centred on the key where the sign changes
    fac, pitch = SWIM_KEYS[0][3], SWIM_KEYS[0][4]
    for a, b in zip(SWIM_KEYS, SWIM_KEYS[1:]):
        if a[0] <= t:
            u = clamp((t - a[0]) / (b[0] - a[0]))
            pitch = lerp(a[4], b[4], smooth(u))
            if a[3] == b[3]:
                fac = a[3]
            else:
                fac = lerp(a[3], b[3], smooth(u))
    if abs(fac) < 0.12:
        fac = 0.12 if fac >= 0 else -0.12
    return x, y, fac, pitch


def swim_pose(t):
    x, y, fac, pitch = swim_state(t)
    tau = t - T_UNDER
    if tau < 1.6:
        p = dog.swim_down(tau, steep=-pitch)
        q = dog.swim(tau, pitch=pitch)
        p = dog.blend(p, q, ease(tau, 1.0, 1.6))
    else:
        p = dog.swim(tau, pitch=pitch, effort=0.8)
    # wonder: under the lamps it looks down at them; the head hangs to see
    look = ease(t, 24.3, 25.0) * (1 - ease(t, 26.9, 27.3))
    p["head"] = p["head"] - 0.32 * look
    p["neck"] = p["neck"] - 0.12 * look
    # ... and then it goes down to them: S2's first drawing is dog.swim_down(0.4, steep=0.72)
    go = ease(t, 27.4, 27.9)
    if go > 0:
        p = dog.blend(p, dog.swim_down(t - 27.6, steep=0.72), go)
    return p


def dog_mouth_world(t):
    x, y, fac, pitch = swim_state(t)
    return (x + fac * 44 * math.cos(pitch), y - 44 * math.sin(pitch) - 6)


# ====================================================================== #
#  4 · THE HERD                                                           #
# ====================================================================== #

@lru_cache(maxsize=None)
def _dog_nose_at(k):
    """Where the dog's nose is at frame k of the greeting (world), from the dog as it is really drawn."""
    t = k / FPS
    return dog.draw_dog(Image.new("RGB", (W, H)), _greet_pose(t - 3.0, t), SPOT_X, SILL_Y, scale=DOG_S, facing=1,
                        shadow=False)["nose"]


def dog_nose(t):
    return _dog_nose_at(int(round(t * FPS)))


LEAD_DRINK_X = 600.0 - herd.reach("lead")       # where she stands to drink at x = 600
T_WALK_ON = 5.2                                  # she chews again and walks on (WORLD: cow = passing)
RIPPLE_T0 = 14.6                                 # the radio is on: the second cow's ears, then up the line
RIPPLE_STEP = 0.14
# where each waits on the path once the line has closed up (d along herd.PATH; 299 is the gate)
QUEUE = ("second", "mother", "calf", "fourth", "fifth", "sixth")
# d along herd.PATH (0 the crest, 322 the gate) where each cow stands:
#   HOLD1 while the lead cow has stopped for the dog (nothing on the lower path, behind the two heads);
#   HOLD2 while the person is out on the boards reaching (nothing near the gate, between hand and dog);
#   SPOTS once the line has closed up: the second with her head in the gate, over the step and the radio.
HOLD1 = dict(second=104.0, mother=66.0, calf=38.0, fourth=14.0, fifth=0.0, sixth=0.0)
HOLD2 = dict(second=175.0, mother=112.0, calf=72.0, fourth=40.0, fifth=12.0, sixth=0.0)
SPOTS = dict(second=264.0, mother=160.0, calf=100.0, fourth=58.0, fifth=22.0, sixth=0.0)


def _lead_at_water(tau, t0):
    """The lead cow once she is at the drinking place: drinks; when the dog goes under beside her muzzle
    she throws her head up, stares at the rings, and brings her nose down to the line where it went."""
    t = t0 + tau
    d = herd.drink(t, clamp(tau / 1.2))
    if t < T_UNDER:
        if 19.4 < t < 20.6:                      # the second in which the dog decides, she is still too
            d = herd.drink(19.4, 1.0)
        return d
    up = herd.notice(herd.stand(t, "lead", chew=0.0, alert=1.0), 1.0)
    up["_nose"] = 0.0
    if t < T_UNDER + 0.6:
        return herd.tween(d, up, (t - T_UNDER) / 0.22, "snap")
    down = herd.look_down(t, 1.0)
    return herd.tween(up, down, (t - (T_UNDER + 0.6)) / 0.8, "slow")


@lru_cache(maxsize=None)
def _walkers():
    n = dog_nose(3.0 + GREET["contact"] + 0.2)
    stop = herd.d_at(n[0] - 8 - herd.reach("lead", n[1] - herd.STRIP_Y, face=78.0))
    d_drink = herd.d_at(LEAD_DRINK_X)
    t_arr = T_WALK_ON + (d_drink - stop) / 49.0 + 0.5
    out = {}
    out["lead"] = herd.Walker("lead", herd.PATH,
                              [(0.0, herd.D_GATE - 74), (3.4, stop), (T_WALK_ON, stop), (t_arr, d_drink), (SECONDS + 2, d_drink)],
                              acts=[(3.0, T_WALK_ON, lambda tau: herd.nose_touch(tau)),
                                    (t_arr, SECONDS + 2, lambda tau, t0=t_arr: _lead_at_water(tau, t0))])
    for k, who in enumerate(QUEUE, start=1):
        h1, h2, d1 = HOLD1[who], HOLD2[who], SPOTS[who]
        rel = herd.PATH.at(h1)["rel"]
        d0 = max(0.0, h1 - 3.3 * herd.SPEED * rel * 0.85)
        lag = 0.28 * (k - 1)
        # the whole line stops when the lead stops for the dog (3.4); closes up when she goes on (5.2);
        # stops again and stares when the person steps out and reaches (8.0); comes on when they sit down.
        keys = [(0.0, d0), (3.5 + 0.12 * k, h1), (5.6 + lag, h1), (8.1 + 0.2 * (k - 1), h2), (10.6 + lag, h2),
                (13.5 + 0.05 * k, d1), (SECONDS + 2, d1)]
        tk = RIPPLE_T0 + RIPPLE_STEP * (k - 1)

        def stare(tau, who=who):                                  # a person is coming toward the gate
            return herd.notice(herd.stand(8.3 + tau, who, chew=0.0, alert=0.6), 1.0)

        def ears(tau, who=who, tk=tk):                            # the radio
            return herd.notice(herd.stand(tk + tau, who, chew=0.0, alert=0.35), 1.0)

        acts = [(tk, tk + 3.2 + 0.3 * k, ears)]
        if k <= 2:
            acts.insert(0, (keys[3][0] + 0.15, keys[4][0] - 0.2, stare))
        out[who] = herd.Walker(who, herd.PATH, keys, acts=acts)
    return out


def _on_hill(t):
    """Who is drawn on the path at t, far to near. A cow still behind the crest (d = 0 with another
    close in front of her) is not in sight yet: the line keeps coming over the hill."""
    wk = _walkers()
    ds = {who: wk[who].plan(t)[0] for who in herd.HERD}
    out = []
    order = ("lead", "second", "mother", "calf", "fourth", "fifth", "sixth")
    for i, who in enumerate(order):
        if i > 0 and ds[who] < 2.0 and ds[order[i - 1]] < 20.0:
            continue
        out.append(who)
    return list(reversed(out))


@lru_cache(maxsize=None)
def _lead_muzzle_at(k):
    t = k / FPS
    lead = _walkers()["lead"]
    st = lead.state(t)
    return herd.anchors("lead", st["pose"], st["x"], st["y"], st["s"], st["facing"])["muzzle"][0]


def lead_muzzle_x(t):
    return _lead_muzzle_at(int(round(t * FPS)))


def _lead_pose_xy(t):
    st = _walkers()["lead"].state(t)
    return st["pose"], st["x"], st["y"], st["s"], st["facing"]


def lead_nose_to(t):
    """The world point the lead cow's muzzle goes to."""
    if t < T_WALK_ON + 0.3:
        n = dog_nose(min(max(t, 3.0), T_WALK_ON + 0.3))
        return (n[0] - 9, n[1] - 1)                # her muzzle to the tip of its nose, from behind and above
    if t >= T_UNDER + 0.6:
        return (600.0, 401.0)                    # the line, exactly where the dog went through
    return (600.0, 400.0)


# ====================================================================== #
#  5 · THE CAMERA                                                         #
# ====================================================================== #
# One world, a crane and pushes (porch.push). Each move has a reason:
#   0.0-7.9   F-PORCH, locked: the geography is learned once and the file is seen as a file.
#   3.0-5.4   a small push on the two noses (the WEAVE beat is a foot high in the wide).
#   7.9-10.9  a medium on the hand and the dog: the hand comes, the dog goes exactly as far.
#   10.9-15.5 the wide again: the sitting, the radio, and the ears going up the hill need the hill.
#   15.5-21.0 the medium on the dog: the one decision we watch at length; we need the ears.
#   21.0-21.6 back to the wide for the walk to the water; 22.0-24.0 the crane down, because the dog goes.

def camera(t):
    """(oy, zoom, cx, cy): crane offset, and a push about a screen point."""
    oy = porch.crane(t, 22.0, 24.0, porch.F_PORCH, porch.F_TOWN)
    z, cx, cy = 1.0, 480.0, 300.0
    a = ease(t, 2.9, 3.7) * (1 - ease(t, 5.3, 6.1))
    if a > 0:
        z, cx, cy = 1 + 0.42 * a, 430.0, 372.0
    b = ease(t, 7.9, 8.7) * (1 - ease(t, 10.5, 11.2))
    if b > 0:
        z, cx, cy = 1 + 0.5 * b, 400.0, 372.0
    c = ease(t, 15.5, 16.8) * (1 - ease(t, 21.0, 21.6))
    if c > 0:
        z, cx, cy = 1 + 0.72 * c, 470.0, 395.0
    return oy, z, cx, cy


# ====================================================================== #
#  6 · THE TITLE: four words, lettered by hand in the sky                 #
# ====================================================================== #

_GLYPH = {
    "T": (0.80, [[(0, 0), (1, 0)], [(0.5, 0), (0.5, 1)]]),
    "H": (0.82, [[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, 0.5), (1, 0.5)]]),
    "E": (0.70, [[(1, 0), (0, 0), (0, 1), (1, 1)], [(0, 0.5), (0.8, 0.5)]]),
    "D": (0.82, [[(0, 0), (0, 1)], [(0, 0), (0.45, 0), (0.85, 0.2), (1, 0.5), (0.85, 0.8), (0.45, 1), (0, 1)]]),
    "O": (0.90, [[(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)) for a in [i * math.pi / 8 - 1.2 for i in range(18)]]]),
    "G": (0.90, [[(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)) for a in [-0.75 - i * math.pi / 8 for i in range(14)]]
                 + [(1.0, 0.56), (0.55, 0.56)]]),
    "S": (0.74, [[(0.95, 0.14), (0.7, 0.0), (0.3, 0.0), (0.05, 0.2), (0.25, 0.45), (0.75, 0.55), (0.97, 0.8), (0.7, 1.0),
                  (0.3, 1.0), (0.02, 0.84)]]),
    "F": (0.70, [[(1, 0), (0, 0), (0, 1)], [(0, 0.5), (0.75, 0.5)]]),
    "R": (0.82, [[(0, 1), (0, 0), (0.65, 0), (0.95, 0.22), (0.65, 0.5), (0, 0.5)], [(0.45, 0.5), (1, 1)]]),
    "U": (0.84, [[(0, 0), (0, 0.68), (0.22, 0.97), (0.5, 1.0), (0.78, 0.97), (1, 0.68), (1, 0)]]),
    "W": (1.15, [[(0, 0), (0.24, 1), (0.5, 0.3), (0.76, 1), (1, 0)]]),
    "N": (0.84, [[(0, 1), (0, 0), (1, 1), (1, 0)]]),
}
TITLE = ("THE DOGS OF", "TROUTTOWN")              # 4 words; the film's limit is 20, the board gives S1 these
CREAM = (244, 232, 204)


def _letter_line(text, x0, y0, hgt, gap, seed):
    """Stroke lists [(pts)] for one line, each letter a little off true (a hand, not a face of type)."""
    import random
    rng = random.Random(seed)
    strokes, x = [], x0
    for ch in text:
        if ch == " ":
            x += hgt * 0.55
            continue
        wd, ss = _GLYPH[ch]
        dy, rot, sc = rng.uniform(-2.2, 2.2), rng.uniform(-0.06, 0.06), rng.uniform(0.94, 1.06)
        for s in ss:
            pts = []
            for (u, v) in s:
                px, py = (u - 0.5) * wd * hgt * sc, (v - 0.5) * hgt * sc
                pts.append((x + wd * hgt / 2 + px * math.cos(rot) - py * math.sin(rot),
                            y0 + hgt / 2 + dy + px * math.sin(rot) + py * math.cos(rot)))
            strokes.append(pts)
        x += wd * hgt + gap
    return strokes, x


@lru_cache(maxsize=None)
def _title_strokes():
    a, xa = _letter_line(TITLE[0], 0, 64, 25, 7, 4)
    b, xb = _letter_line(TITLE[1], 0, 100, 37, 8, 9)
    # set both lines between x 600 and 920, the long one filling it
    out = []
    for strokes, wd in ((a, xa), (b, xb)):
        off = 606 + (310 - wd) / 2
        out += [[(x + off, y) for x, y in s] for s in strokes]
    return out


def title(ink, t):
    """THE DOGS OF TROUTTOWN, written on in the violet sky 0.8-1.4, there to 3.2, gone by 3.8."""
    if t < 0.8 or t > 3.8:
        return
    strokes = _title_strokes()
    n = len(strokes)
    out = 1 - ease(t, 3.2, 3.8)
    sheet = ink.layer()
    for k, s in enumerate(strokes):
        on = clamp((t - 0.8 - 0.6 * k / n) / 0.16)          # each stroke is drawn in its turn
        if on <= 0:
            continue
        # a partial stroke: as much of its length as has been drawn
        pts = [s[0]]
        total = sum(math.dist(p, q) for p, q in zip(s, s[1:]))
        need, run = total * on, 0.0
        for p, q in zip(s, s[1:]):
            d = math.dist(p, q)
            if run + d <= need:
                pts.append(q)
                run += d
            else:
                f = (need - run) / max(d, 1e-6)
                pts.append((lerp(p[0], q[0], f), lerp(p[1], q[1], f)))
                break
        if len(pts) > 1:
            sheet.line([(x + 1.5, y + 2) for x, y in pts], (40, 22, 60), 4.2, amount=0.5, alpha=110)
            sheet.line(pts, CREAM, 3.6, amount=0.5)
    ink.paste(sheet.img, alpha=out)


# ====================================================================== #
#  7 · THE PICTURE                                                        #
# ====================================================================== #

def _split_dog(ink, pose, x, y, line_y, facing=1, deep=0.0):
    """A dog standing in the creek: what is above the line as it is, what is below it seen through water."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    j = dog.draw_dog(layer, pose, x, y, scale=DOG_S, facing=facing, shadow=False)
    ly = int(round(line_y))
    top = layer.crop((0, 0, W, max(0, ly)))
    ink.img.paste(top, (0, 0), top)
    if ly < H:
        bot = layer.crop((0, max(0, ly), W, H))
        teal = Image.new("RGBA", bot.size, TEAL + (255,))
        tinted = Image.blend(bot.convert("RGBA"), teal, 0.5 + 0.2 * deep)
        tinted.putalpha(bot.getchannel("A").point(lambda v: int(v * 0.82)))
        ink.img.paste(tinted, (0, max(0, ly)), tinted)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    return j


T_TOWN = 24.0                                    # the crane has arrived at F-TOWN


def _trail(ink, t, oy):
    """The bubble trail down from the line at x = 590 to the dog, as the boundary frame has it (and as S2
    goes on drawing it): the same sixteen bubbles S2 draws, arriving over the last second and a half."""
    tl = t - SECONDS
    if tl < -1.6:
        return
    for q in range(16):
        u = (q + 0.5) / 16
        ta = -2.2 * (1 - u)
        if tl < ta + 0.25 * u - 0.2:                 # not let go yet
            continue
        wx = lerp(590, 300, u ** 1.15) + 5 * math.sin(q * 2.1 + tl * 3)
        wy = lerp(404, 530, u ** 1.3) - 34 * (tl - ta) * 0.5
        sx, sy = wx, wy - oy
        if sy < 400 - oy + 3:
            continue
        r = 1.5 + (q * 7 % 4) * 0.7
        a = int(230 * clamp(1 - (tl - ta) / 4.6) * ease(t, SECONDS - 1.6, SECONDS - 0.5))
        if a > 8:
            ink.d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=(226, 246, 238, a), width=1)


def _lamps(t):
    """Trouttown's lights, left to right, 24.5 to 27.0; the school windows last."""
    return ramp(t, 24.5, 27.2)


def draw(t, ink):
    """One full frame of S1 at sequence time t (0..28)."""
    t = clamp(t, 0.0, SECONDS)
    tr = _trace()
    wk = _walkers()
    oy, zoom, cx, cy = camera(t)
    w = circumstances(t)
    under = t >= T_UNDER
    st = tr.at(t)["state"]

    # rings on the water: her drinking, the dog going in, her muzzle coming back down to the line
    rings = []
    t_arr = wk["lead"].plan.keys[3][0]
    k = 0
    while t_arr + 1.0 + 1.9 * k < min(t, T_UNDER):
        rings.append(porch.ring(602, t_arr + 1.0 + 1.9 * k, 0.45))
        k += 1
    if t >= tr.t("WADE"):
        rings.append(porch.ring(tr.x(tr.t("WADE")) + 30, tr.t("WADE") + 0.1, 0.6))
    if under:
        rings.append(porch.ring(ENTRY_X + 4, T_UNDER, 1.25))
        rings.append(porch.ring(ENTRY_X + 4, T_UNDER + 0.35, 0.9))
        k = 0
        while T_UNDER + 1.4 + 2.2 * k < t:
            rings.append(porch.ring(600, T_UNDER + 1.4 + 2.2 * k, 0.5))
            k += 1

    def hill(ink, t, oy):
        for who in _on_hill(t):
            wk[who].draw(ink, t, oy, layer="hill")

    def strip(ink, t, oy):
        for who in reversed(herd.HERD):
            a = wk[who].draw(ink, t, oy, layer="strip", nose_to=lead_nose_to(t) if who == "lead" else None)
            if a and who == "lead" and T_UNDER <= t < T_UNDER + 2.5:
                porch.drips(ink, t, oy, a["muzzle"][0], a["muzzle"][1] + oy, t - T_UNDER - 0.1, wet=0.8, width=16, floor=400)

    def sill(ink, t, oy):
        if st in ("WADE", "UNDER"):
            return
        x = tr.x(t)
        dog.draw_dog(ink, dog_pose(t), x, SILL_Y - oy, scale=DOG_S, facing=1)
        if 3.0 < t < T_WALK_ON + 0.3:              # her breath out, onto the dog
            br = _lead_pose_xy(t)[0].get("_breath", 0.0)
            if br > 0:
                mz = lead_nose_to(t)
                herd.breath(ink, mz[0] + 4, mz[1] - oy + 2, br, 1)

    def swimmer(ink, t, oy):
        x, y, fac, pitch = swim_state(t)
        if t < 26.6:
            porch.bubbles(ink, t, oy, dog_mouth_world, T_UNDER + 0.15, 26.2, rate=6.0, seed=3, size=0.9)
        porch.bubbles(ink, t, oy, (ENTRY_X + 2, 452), T_UNDER + 0.05, T_UNDER + 1.2, rate=16.0, seed=11, size=1.1)
        _trail(ink, t, oy)
        deep = clamp((y - 400) / 60.0)
        pose = swim_pose(t)
        if y < 430 and abs(fac) > 0.99:
            # the moment of going through: head and shoulders already under, the rump and tail still in the air
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dog.draw_dog(layer, pose, x, y - oy, scale=DOG_S, facing=1, shadow=False)
            ly = int(400 - oy)
            top = layer.crop((0, 0, W, ly))
            ink.img.paste(top, (0, 0), top)
            bot = layer.crop((0, ly, W, H))
            teal = Image.new("RGBA", bot.size, TEAL + (255,))
            tinted = Image.blend(bot, teal, 0.3)
            tinted.putalpha(bot.getchannel("A"))
            ink.img.paste(tinted, (0, ly), tinted)
            ink.d = ImageDraw.Draw(ink.img, "RGBA")
        else:
            dog.draw_dog(ink, pose, x, y - oy, scale=DOG_S, facing=fac, tint=TEAL, tint_amount=0.2 + 0.15 * deep,
                         shadow=False)

    def under_water(ink, t, oy):
        if oy > 20:
            cam = town.Cam(oy=oy)
            lv = _lamps(t)
            town.back(ink, t, cam, lamps=lv, sky=False)
            town.street(ink, t, cam, lamps=lv, holes=0)
            town.townsfolk(ink, t, cam, look=swim_state(t)[:2] if t > 25.2 else None)
        if st == "WADE":
            tau = t - tr.t("WADE")
            y = SILL_Y + 36 * ease(tau, 0.0, 0.36)          # off the end of the board: in to the chest
            _split_dog(ink, dog_pose(t), tr.x(t), y - oy, 400 - oy, deep=tau / 0.4)
        elif under:
            swimmer(ink, t, oy)
        if oy > 20:
            town.front(ink, t, town.Cam(oy=oy))

    def front(ink, t, oy):
        if under:
            porch.splash(ink, t, oy, ENTRY_X + 4, t - T_UNDER, 1.15, "in")

    if t >= T_TOWN:
        # F-TOWN, the crane over: the dry world is only what shows through the line from below (as S2 has it)
        cam = town.F_TOWN
        lv = _lamps(t)
        town.back(ink, t, cam, lamps=lv, sky=True)
        town.touch(ink, t, cam, 600, "muzzle", dip=0.9 + 0.1 * math.sin((t - 28.0) * 1.3))
        town.street(ink, t, cam, lamps=lv, holes=0)
        town.townsfolk(ink, t, cam, look=swim_state(t)[:2] if t > 25.2 else None)
        swimmer(ink, t, porch.F_TOWN)
        town.front(ink, t, cam)
        return

    q = person_q(t)
    carrying = t < 14.0
    hold_a = "pebble" if PEBBLE_T - 0.42 <= t < PEBBLE_T else None
    porch.scene(ink, t, oy,
                cast=dict(hill=hill, strip=strip, sill=sill, under=under_water, front=front),
                q=q, door=0.62, hold_a=hold_a, hold_b="radio" if carrying else None,
                hand_over_rail=6.2 <= t < 8.05,
                radio_at=None if carrying else "step",
                radio_on=ease(t, 14.0, 14.4),
                pebbles="w" if t >= PEBBLE_T else "",
                rings=rings)
    if t > T_TOWN - 0.5:
        # the last half second of the crane: what is above the line gives way to how it looks from below
        ly = int(400 - round(oy)) + 2
        alt = kit.Ink(t, ink.i)
        town.back(alt, t, town.Cam(oy=oy), lamps=_lamps(t), sky=True)
        town.touch(alt, t, town.Cam(oy=oy), 600, "muzzle", dip=0.9)
        strip = alt.img.convert("RGB").crop((0, 0, W, ly))
        base = ink.img.convert("RGB").crop((0, 0, W, ly))
        ink.img.paste(Image.blend(base, strip, ease(t, T_TOWN - 0.5, T_TOWN)), (0, 0))
        ink.d = ImageDraw.Draw(ink.img, "RGBA")
    if zoom > 1.001:
        porch.push(ink, cx, cy, zoom)
    title(ink, t)


# ====================================================================== #
#  8 · THE SOUND (laid with sound.py; nobody here has heard it)           #
# ====================================================================== #

def sound(mix, at=0.0):
    """S1's sound into `mix`, the sequence starting at film second `at`. Rooms, the radio, and every
    contact timed to the frame it lands on in THIS picture (the board's rule: the builder's frame wins)."""
    tr = _trace()
    wk = _walkers()
    A = at
    S = snd
    # rooms: above until the line passes the camera, then below
    S.above(mix, A + 0.0 - 0.1, 22.6 + 0.2, 1.0, 0.2, 0.2)
    S.hush(mix, A + 22.6 - 0.1, SECONDS - 22.6 + 0.2, 1.0, 0.2, 0.2)
    S.crickets(mix, A + 0.5, 21.9, 3)
    S.duck(mix, A + 19.4, A + 20.6, 0.6, 0.15)
    # the radio and the town's lamps (music_s1 takes its own start time)
    S.music_s1(mix, A)
    # the file: hooves from the lead cow's own footfalls, the bell from her own pendulum
    lead = wk["lead"]
    t_arr = lead.plan.keys[3][0]
    for (tt, x, y, leg) in lead.hoof_falls(0.0, t_arr + 0.3):
        if tt < 0.05:
            continue
        S.hooves(mix, A + tt, 1, 0.55, "wood" if x > 400 else "earth", gain=0.085, pan=clamp((x - 480) / 480, -1, 1) * 0.6 + 0.15)
    for hit in lead.bell_hits:
        if hit < t_arr + 1.0:
            S.cowbell(mix, A + hit, gain=0.05, pan=0.2)
    S.cowbell(mix, A + 1.6, gain=0.07, pan=S.P_GATE, hard=True)           # against the gate post
    S.collar(mix, A + 3.6, 2, gain=0.04, pan=0.0)                         # the dog's head coming up to hers
    S.cow_breath(mix, A + 3.0 + herd.NOSE_TOUCH["breath"], 1.5, pan=0.1)  # one long breath out, onto the dog
    S.drinking(mix, A + t_arr + 1.0, 19.3 - (t_arr + 1.0))
    S.drinking(mix, A + 20.7, 1.2)
    # second cow comes down to the gate and stops
    sec = wk["second"]
    for (tt, x, y, leg) in sec.hoof_falls(5.0, 8.2)[::2]:
        S.hooves(mix, A + tt, 1, 0.55, "earth", gain=0.06, pan=0.3)
    # Line 1, four taps, the white pebble
    S.voice_call(mix, A + 6.2)
    S.taps(mix, A + TAPS[0])
    S.pebble(mix, A + PEBBLE_T)
    # the reach; the dog goes exactly as far
    ty = tr.t("YIELD")
    S.creak(mix, A + 8.1, 0.4)
    S.paws(mix, A + ty + 0.1, 3, 0.26, gain=0.12, pan=-0.1, pan_to=0.05)
    S.collar(mix, A + ty + 0.15, 2, gain=0.04, pan=-0.05)
    # sits; the radio on the step
    S.creak(mix, A + 11.6)
    S.radio_down(mix, A + 14.0)
    # it goes
    S.paws(mix, A + tr.t("GO") + 0.05, 3, 0.2, gain=0.11, pan=0.1, pan_to=0.3, wet=True)
    S.wade(mix, A + tr.t("WADE"), 0.5, 2)
    S.swap_down(mix, A + T_UNDER)
    S.cowbell(mix, A + T_UNDER + 0.12, 2, 0.2, gain=0.08, pan=0.3, hard=True)     # her head jerking up
    S.drip(mix, A + T_UNDER + 0.5, 3, 0.3, on="water")
    S.cowbell(mix, A + T_UNDER + 1.4, gain=0.05, pan=0.3, under=True)             # one knock from above, through water
    S.bubbles(mix, A + 24.6, 4, 1.2, gain=0.03)
    S.bubbles(mix, A + 27.2, 3, 0.6, gain=0.03)
    return mix


# ====================================================================== #
#  9 · ALONE                                                              #
# ====================================================================== #

def _sheet(times, path, cols=4, scale=0.5, crop=None):
    """A contact sheet of stills."""
    ims = []
    for t in times:
        ink = kit.Ink(t, int(round(t * FPS)))
        ink.paper()
        draw(t, ink)
        im = ink.finish()
        if crop:
            im = im.crop(crop)
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        ims.append(im)
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (20, 20, 24))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        check()
        return
    if args and args[0] == "--sheets":
        out = HERE.parent.parent / "stills" / "dogs-s1"
        sets = {
            "a_file": [0.0, 0.9, 1.6, 2.4, 3.0, 3.4, 3.75, 4.2, 4.6, 5.0, 5.6, 6.2],
            "b_reach": [6.4, 6.9, 7.4, 7.8, 8.2, 8.6, 9.0, 9.4, 10.0, 10.5, 11.0, 11.8],
            "c_radio": [12.5, 13.2, 14.0, 14.4, 14.7, 15.0, 15.4, 15.8, 16.4, 17.0, 17.6, 18.2],
            "d_decide": [18.6, 19.2, 19.5, 20.0, 20.5, 20.8, 21.0, 21.3, 21.6, 21.8, 21.95, 22.0],
            "e_cross": [22.1, 22.25, 22.4, 22.6, 22.9, 23.2, 23.4, 23.7, 24.0, 24.5, 25.0, 25.5],
            "f_town": [26.0, 26.5, 27.0, 27.3, 27.6, 28.0],
        }
        only = args[1:]
        for name, ts in sets.items():
            if only and name[0] not in only:
                continue
            print(_sheet(ts, out / f"sheet_{name}.png"))
        return
    check()
    film = kit.Film("dogs-s1", SECONDS)
    film.poster_at = 3.75
    film.picture(draw)
    film.sound(lambda mix: sound(mix, 0.0))
    film.render()


if __name__ == "__main__":
    main()
