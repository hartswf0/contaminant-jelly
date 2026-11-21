# STUDY · the refusal (animation-48, state machines: characters that can refuse)

`films/swarm/cowpath/study_refuse.py` → `assets/films/cowpath-study-refuse.mp4`
12.0 s, 960x540, 24 fps, picture and sound, 0.6 MB, no text on screen. Poster `cowpath-study-refuse.webp`.

    python3 films/swarm/cowpath/study_refuse.py              # render (about 16 s)
    python3 films/swarm/cowpath/study_refuse.py --check      # model-based tests and measured invariants
    python3 films/swarm/cowpath/study_refuse.py --trace      # the decision trace of every character
    python3 films/swarm/cowpath/study_refuse.py --chart      # the state charts as text
    python3 films/swarm/cowpath/study_refuse.py --sheet OUT.png [t0 t1]    # 16-still contact sheet

This is the study for the board's defining passage (3.4). It is a builder's study, not an accepted beat:
**no independent critic has looked at it and nobody has heard it.** What was and was not checked is
listed under "Evidence".

## What the SCION asked for

animation-48's theorem: a cast that perceives, chooses, resists and remembers, instead of puppets that obey.
Its hard proof is a dog that chooses among watch, approach, retreat, lie down and refuse, where the player must
change circumstances to earn the approach. Its native primitives, to be kept as real things in the project:
**states, guards, transitions, priorities, action windows, character intentions, persistent world data.**
Its bar: no unreachable or unintended absorbing states; choices conditioned on declared state; locomotion
continuity; the refusal has visual consequence; the viewer can understand but not control. One invariant
tested numerically, one achievement judged only by viewing.

Turned to this film: the dog is the watching trout (it built nothing), the player is the builder trout, the
invitation is a slab laid in the road, and the circumstance that has to change is the pier under the slab.

## What was built

A simulation, recorded, then drawn. Nothing on screen is keyed by hand: two finite-state machines (plus three
two-state onlookers) are stepped 24 times a second against persistent world data, and the picture and the
sound are both made from the recorded run. Change the world and the film changes (see the four scenarios).

What happens in the 12 seconds (times from the run's own trace):

| t | who | what |
|---|---|---|
| 0.0 | builder | carries its slab up on its nose into the one gap in the road; the watcher lies under the road and watches |
| 1.04 | builder | slab seated; backs off, turns right round on the spot (pleased) |
| 1.46 | watcher | WATCH → APPROACH: a piece is set and its builder has let go |
| 3.08 | watcher | INSPECT: pushes the end of the slab once from below. The slab see-saws (9.6°), knocks three times, a pebble falls |
| 3.50 | watcher | INSPECT → REFUSE (peak 9.56° > 1.5°). It does nothing new: it stays where it is, which is in the way |
| 3.58 | builder | leaves for the school without waiting for an answer (it is the hasty one) |
| 3.88, 4.50 | builder | TRY_OVER (the watcher's nose shuts the top), TRY_UNDER (the watcher sinks) |
| 5.21 | builder | STOPPED nose to flank; tail stops; one string of bubbles; the three onlookers have turned to look |
| 6.50 | builder | after one second dead still: turns round (the only right-to-left travel), dives to the stone it left |
| 7.29 to 8.71 | builder | takes the stone, turns, pushes it up, wedges it under its slab (gap 34 px → 0) |
| 9.00 | watcher | the piece's revision changed: INSPECT again. The slab does not move (0.06°) |
| 9.42 | watcher | PASS: sinks and levels out of the way. The builder, who this time waited, goes by |
| 11.0 | builder | JOINED; the onlookers face front again; the watcher lies low, half-lidded |

### The native primitives, as data (all in `study_refuse.py`)

| primitive | class | notes |
|---|---|---|
| State | `State(name, intention, window, terminal)` | watcher: WATCH, APPROACH, INSPECT, REFUSE, PASS. builder: CARRY, PRESENT, LEAVE, TRY_OVER, TRY_UNDER, STOPPED, TURN_BACK, FETCH, TURN_FWD, REPAIR, JOINED (terminal) |
| Guard | `Guard(name, test(see, mem) -> (bool, evidence))` | reads only the percept dict built for that character and its own memory; returns the evidence that goes in the trace |
| Transition | `Transition(src, dst, guard, priority, interrupt)` | lower `priority` fires first; `interrupt` may cut an action window short |
| Priority | `Transition.priority` | e.g. INSPECT → REFUSE (0) is tested before INSPECT → PASS (1); "the way is open" (0) before "still no way" (1) |
| Action window | `ActionWindow(min_frames)` | commitment: a state's action runs at least this long before a guarded exit |
| Intention | `Intention(want)` | what the character wants in that state; printed with every decision |
| Persistent world data | `WorldData(pieces, loose, pebbles, events)`, `Piece`, `Stone` | the slab's tilt and angular velocity, the pier's stones, the piece's revision number, the fallen pebble, every contact |
| Memory | `Memory` | watcher: which revision it judged, refusals, passes. builder: tries made, refused count, whether it saw the yes |
| the machine | `Machine` | `.step(frame, see, trace)`, `.reachable()`, `.absorbing()`, `.chart()`, `.visited`, `.fired` |

The verdict is not a flag. `WorldData.nudge()` gives the slab an angular push; `WorldData.step()` integrates a
damped rocker whose stiffness depends on `Piece.gap()` (daylight between pier top and slab, computed from the
stones actually in the pier). The watcher's guard reads the peak tilt it felt in the 10 frames after its own
push. The builder cannot buy a pass except by putting a stone in the pier.

The characters are coupled only through what can be seen or felt: the builder's "yes" is the watcher's lid
lifting and its body leaving the way (`flank_x`), not a read of the watcher's state.

### State charts

    watcher  WATCH ──a piece is set, unjudged, and let go──▶ APPROACH ──under the slab──▶ INSPECT
             INSPECT ──tipped > 1.5°──▶ REFUSE ──piece revision changed──▶ INSPECT
             INSPECT ──stayed ≤ 1.5°──▶ PASS ──builder has gone by──▶ WATCH

    builder  CARRY ──seated──▶ PRESENT ──thinks it is done──▶ LEAVE ──with the others──▶ JOINED
             LEAVE ──a body across my way──▶ TRY_OVER ──still no way──▶ TRY_UNDER ──still no way──▶ STOPPED
             TRY_OVER / TRY_UNDER / STOPPED ──the way is open──▶ LEAVE            (priority 0, interrupt)
             STOPPED ──tried both, dead still 24 frames, remembers the stone──▶ TURN_BACK ──▶ FETCH
             FETCH ──nose on the stone──▶ TURN_FWD ──▶ REPAIR ──stone in the gap──▶ PRESENT

"Thinks it is done" is where the builder remembers: the first time it leaves 12 frames after the slab has
merely been touched; after one refusal it waits until it has seen the lid lift and the way clear.

## Functions other agents can import

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))        # films/swarm/cowpath
    import study_refuse as sr                                        # renders nothing on import

| function | what it does | example |
|---|---|---|
| `simulate(scenario='short', seconds=12.0) -> Run` | runs the scene and records it. Scenarios: `'short'` (the film), `'firm'` (whole pier: passed at once), `'stubborn'` (short pier, no stone: never passed), `'helped'` (somebody else wedges it at 7 s: re-inspected and passed) | `run = sr.simulate('short', 12.0)` |
| `the_run(scenario='short', seconds=12.0) -> Run` | the same, cached | `run = sr.the_run()` |
| `Run.at(t)` | the snapshot dict at time t: `watcher`, `builder`, `lookers` (fish dicts), `w_state`, `b_state`, `slab`, `stones`, `loose`, `pebbles`, `clear` | `fr = run.at(5.6); fr['b_state']  # 'STOPPED'` |
| `Run.when(who, dst, nth=1)` | time a character entered a state | `t_stop = run.when('builder', 'STOPPED')  # 5.208` |
| `Run.event_times(kind)` | times of contacts: `set, nudge, clack, pebble, pebble_land, dart, stopped, sigh, turn, pick, wedge, leave, joined, twirl` | `run.event_times('clack')` |
| `draw_refusal(ink, run, t, cow=True)` | the whole frame at time t of a run | `sr.draw_refusal(ink, run, t - 94.0)` |
| `draw_stage_back(ink, t=0.0, cow=True)` | the Act 3 set: c13 river, air above the surface at y=170, far weed, both banks, the far grass, the lead waiting on the left bank | `sr.draw_stage_back(ink, t)` |
| `draw_pier(ink, stones)` | a pier from `[(id, x, y, w, h, seed, tilt), ...]` | `sr.draw_pier(ink, run.at(t)['stones'])` |
| `draw_slab(ink, lane, x=None, y=None, theta=0.0, shadow=0.4)` | one 100x20 span; default seated in its lane; `theta` degrees, + = right end up | `sr.draw_slab(ink, 2)` · `sr.draw_slab(ink, 4, theta=-6)` |
| `draw_fish(ink, f, shadow=0.3)` | a c13 trout from a dict `x, y, pitch (+ nose up), face (+1 right), wide (1 side on .. 0 edge on), length, lid, amp, phase`. `wide` is the paper flip | `sr.draw_fish(ink, dict(x=400, y=300, pitch=20, face=1, wide=1, length=118, lid=0, amp=8, phase=t*6))` |
| `stone_sprite(w, h, seed, color=None)`, `slab_sprite(lane)` | the cut-paper pieces (cached RGBA) | `w.put(ink, sr.stone_sprite(56, 34, 77, sr.WEDGE_COL), x, y)` |
| `score_refusal(mix, run, t0=0.0, gain=1.0)` | the sound, every event taken from the run's contacts | `film.sound(lambda mix: sr.score_refusal(mix, run, t0=94.0))` |
| `Body`, `Drive`, `steer(body, drive)` | accel-, speed- and turn-limited locomotion; `Body.start_flip(n)` is the paper turn | `b = sr.Body('x', 300, 300, 118); sr.steer(b, sr.Drive((500, 260), 180))` |
| `flank_x(gate, y)`, `clearance(a, b)` | where a fish's body bars the way at height y; water between two fish | `sr.flank_x(watcher_body, 330)` |
| `make_world(short=True, loose_stone=True)`, `WorldData.nudge(piece, x)`, `WorldData.step()` | the road as data, and the slab's physics | `wd = sr.make_world(); wd.pieces[4].set = True; wd.nudge(wd.pieces[4], 576); wd.step()` |
| `Machine`, `State`, `Guard`, `Transition`, `ActionWindow`, `Intention`, `Memory` | the primitives, for further characters (the other five builders) | `m = sr.Machine('b2', states, transitions, 'CARRY')` |
| `check(verbose=True) -> dict` | the tests below; raises on a hard failure | `sr.check()` |
| `sheet(path, t0, t1)`, `print_trace(run)` | contact sheet; trace | `sr.sheet('/tmp/s.png', 3.0, 7.0)` |

Layout constants follow the board: `SURFACE=170, BED=480, LEFT=180, RIGHT=780, LANE_W=100, SLAB_T=20, LANE=4`,
`lane_cx(i)`, `LANE_PITCH` (D4 .. D5), `ROCK_LIMIT=1.5`. Cost: simulation 0.04 s; about 55 ms a frame once
the sprites are cached.

## Evidence (law 14)

**MEASURED / STRUCTURAL** (`--check`, all pass, revision as delivered):
- Graph: no unreachable state in any machine; the only state without an exit is `builder.JOINED`, declared terminal.
- Coverage: the film run enters every state of both machines. Across the four scenarios every transition
  fires except one: `TRY_UNDER → LEAVE` (the way opening during the under-try) is never taken. It is a safety
  exit; it is untested.
- Conditioned on declared state: short pier → refuse, then pass after the wedge (peaks 9.56° then 0.06°,
  limit 1.5°). Whole pier → pass at once, no refusal, no turning back. Short pier and no stone → 24 s of
  waiting and no pass. Short pier wedged by somebody else → re-inspected and passed: the pass follows the piece.
- Obedient default: in no scenario does the builder's nose cross the watcher's line before PASS.
- Locomotion continuity: largest step of a fish's centre 13.8 px a frame (builder), 9.6 (watcher); largest
  pitch change 10.8° a frame. The paper flips are declared exceptions: the centre does not move, the
  silhouette foreshortens through edge-on in 7 frames.
- No contact: least water between the two bodies 9.9 px (fins not counted). The refusal is never a shove.
- Consequence: during the refusal the builder's x stays within 390..459; it faces left at least once; the
  gap under the slab goes 34.0 → 0.0 px.
- Sound against picture (decoded from the mp4, peak per quarter second): events land on their frames
  (set 1.0, nudge and clacks 3.0 to 3.75, wedge 8.5, retest 9.0, join 11.0); the quietest stretch of the
  whole track is 6.25 to 7.0, peak 0.01 to 0.02, inside and just after the hold.

**JUDGED, from stills only, by the builder** (16-still contact sheets of the script and of the encoded mp4,
plus frame strips at 2 to 4 frame spacing over 0 to 3.3, 3.4 to 5.4, 5.4 to 8.2, 8.0 to 11.7 and frame-by-frame
over both turns). No playback was watched: nothing here is a claim about how the motion feels at speed.
- Round 1: the stop happened lying on the gravel and the "dive" was a 60 px shuffle; the slab was still
  rocking through the hold; the watcher had not decided before the builder left; fish overlapped at three
  moments. Fixed: decision before leaving (push window 10 frames, builder leaves at 12), rocker damping up,
  flank computed over the builder's whole height, watcher's tail swing kept clear of the hover place.
- Round 2: in the over-try the builder backed away instead of going for the gap, and for 8 frames the top
  was actually open (the watcher lagged). Cause: the gate tracked the builder's height. Fixed: the gate sits
  60 px above the builder, so it already shuts the top and only has to sink for the bottom; the under-try
  ends when the builder sees it shut, in open water (y 392), not on the bed. Stillness is now counted
  (24 frames at under 16 px/s) instead of timed, so the hold is one second of actual stillness.
- Round 3: sound. The river bed was as loud as the events (droplet chirps peaking at 0.4 against a nudge at
  0.26); cut to 0.4 of that. The wedged stone changed colour when it joined the pier; it now stays pale so
  the repair can still be seen at the end.

**UNKNOWN:**
- How it sounds. Nobody on this production can hear. Levels are guesses from the numbers.
- Whether T3 passes. That needs a stranger and playback. The builder cannot pass its own beat (law 9).
- How the 7-frame paper flips and the 2 Hz see-saw read at speed.

## What is weak

1. **The lid is too small to act with.** At length 170 the watcher's eye is about 5 px. Half-lidded against
   fully open cannot be seen at playback size, so "its lid lifts all the way, once" is not carried by the lid.
   The yes is carried by the body leaving the way. If the director needs the eye, the watcher has to be
   bigger or the shot closer, and the board forbids a camera move in 3.4.
2. **The refusal is not a turn "broadside".** In a side view a body across the way is a fish standing on its
   tail (72° nose up). It reads as a bar, and the same posture is its inspecting posture, so the refusal has
   no gesture of its own: it is the watcher not moving. That is true to the board ("no anger, lid and speed
   do not change") but a viewer may not separate "testing" from "refusing" until the builder bounces off.
3. **The builder leaves only 2 frames after the watcher has decided**, and it does not react to its own slab
   rocking. A flinch was not built. The comedy of "hasty" rests on the pleased turn and the early exit.
4. **Compression.** The board gives this passage 10 s after 10 s of building; the study does bring, test,
   refuse, repair and pass in 12 s. The carry is 1 s, the repair climb is fast for a fish pushing a stone
   (240 px/s; the board wants weight), and there is no even pulse of earlier slabs tested firm, so the
   first nudge has nothing to be compared with until the retest. The Act 3 builder has the time to restore these.
5. **The under-try stops short.** The builder gives up at y 392 when it sees the watcher sink; a critic
   may ask why it did not go lower. By the gate rule the watcher would have shut it (its range reaches the bed; this was
   reasoned from the numbers, not run), and the picture does not show it.
6. **Differences from the board, to be reconciled by the Act 3 builder:** the dropped stone lies in
   lane 2 (x 318), not in lane 4, because the builder is longer than a lane and has to have somewhere to
   turn back to; pier 4 is two tall stones with a 34 px gap and the slab hangs between its neighbours (the
   board says "a pier of two"; with equal stones the gap would be 97 px and nobody would need a test);
   the builder makes one extra right-to-left facing before the refusal (the pleased turn on the spot) and
   the onlookers flip to look, both of which spend a little of the "only thing that ever turns back";
   the school is three fish, not five.
7. **The piers are heavy.** Eighteen tall stones stand behind the action; the watcher's head covers part of
   the gap while it inspects. The gap is clear in the hold and in the wide stills, less so at the nudge.
8. **One fish, one lane.** The other five builders are not machines here. `Machine` and the builder's
   chart are written to be instanced per lane, but that has not been run.
9. The cow is a single static cutout from `cast.sprite` (look_up); if `cast` fails to import she is left
   out silently (`sr._COW['err']` holds the reason).

## Sources and rights

Trout: Denton's 1896 brook trout plate, public domain, already credited in `films/credits/c13.json`
(used through `world.trout_sprite`). River, weed, bubbles: `world.py`, handmade. Cow: `cast.py`, handmade.
Stones, slabs, banks, grass, air: handmade here with `world._paper_piece` (a private helper of world.py:
if it is renamed, `stone_sprite`, `slab_sprite` and the banks break). Nothing new was foraged.
