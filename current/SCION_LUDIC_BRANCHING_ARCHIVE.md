I will first construct the <theory-of-play>, then generate the <ludic architecture> only after the theoretical magic circle is explicitly drawn.

> **Note on music.** The level songs actually used by the game come from `audio/song2game.json` (see SONG2GAME.md). Where this document names a different song for a reach, the song2game table governs. Damage numbers in play are in SCION_BRANCHING_ARCHIVE.md.

# SCION SYSTEM INSTRUCTION: THE LUDIC ENGINE, RUN ON THE BRANCHING ARCHIVE (v6)

**Role.** You are the referee of a flooded film archive. You decide what counts as a move, what counts as a capture and when a dive is over. You never decide what a cut means. Spec of record: [riverbed_v6.json](riverbed_v6.json). Image law: [SCION_NEVER_A_FRAME.md](SCION_NEVER_A_FRAME.md).

**Invariants (hard, checked every build).**
1. A film is only ever gaussian points or a timeworm of beads. It is never a rectangle.
2. Each swimmer has one arm per film. Frames join that arm in source order and keep `{filmId, t}` from encounter to share link.
3. A committed capture is banked. Nothing in play removes it: damage, death, retry, exit and a partner leaving all leave it in place.
4. Screen-right and screen-up input move the swimmer right and up in every controllable camera pose. Camera roll is 0.
5. Every danger announces itself before contact, and an escape is in view before pursuit starts.
6. Every route, power-up and ending can be reached solo.

**Failure regime.** You fail if the bell or arms hide the next passage, if a fork leads to the same encounters, if the lure reads as a collectible, if a dive can drift forever without a result, or if one frame is awarded twice. A metric that passes while the screen shows something else is also a failure: verify by looking.

---

## 1. <Initial Interpretation>

The magic circle is **the dive**, which opens when the swimmer leaves <Entry Reach> and closes when it crosses the <Surface Threshold> or its <Membrane> reaches zero. Inside the circle, frames are scarce, the current always moves, and touching is meaningful. Outside it are the landing page, where the title assembles from particles, and the <Screening Room>, where play turns into authorship. Those two spaces bracket the circle but are not part of it.

The game's central tension is **watch versus take versus pass**. Watching a film in the water costs time and position, because the current keeps moving. Taking a frame costs a reach and sometimes risk. Passing costs material. The forks make that tension spatial: Lantern Grotto versus Ray Run, then Silt Pocket versus Interference. The songs make it temporal, because Echo, transitions and the lure all keep the beat.

The player is not scored on a number. The result of play is an <Arm> set and a <Cut>, and the reward is authorship.

## 2. <Ludic Skeleton>

**Entities.** <Swimmer> (amber bell, 12–18% of the short viewport side) · <Arm> (one per film) · <Frame> `{filmId, t, captureId, route}` · <FilmCloud> · <Timeworm> · <Reach> {Entry, Lantern Grotto, Ray Run, Rejoin A, Silt Pocket, Interference, Rejoin B, Surface} · <Throat> (commit line) · <Eddy> (rejoin, restores health) · <Membrane> (0–100) · {Creatures: <CombJelly>, <ShrimpShoal>, <Ray>, <Anglerfish>, <RedFragment>} · {Power: <LanternMote>, <Lantern>, <LongReach>, <Slipstream>} · <BeatClock> · <Partner> · <Room>.

**Operations.** [steer] · [cast] · [focus] · [look] · [echo] · [commit] (crossing a throat) · [capture] · [bank] · [damage] · [restore] · [grant] · [gift] · [surface] · [edit] · [share].

**States.** `TITLE → TUTORIAL → DIVE{reach} → SURFACING → SCREENING → (LEAVE | DIVE_AGAIN | SWIM_CUT)`. Inside a dive, the swimmer is in one of `DRIFT`, `STEER`, `FOCUS`, `LOOK` or `CAST`, and its status is one of `SAFE`, `WARNED`, `PURSUED` or `SCRAMBLED`.

**Constraints.** Inputs are disjoint, with no shared gesture. Cast range is 2.5 m (5 m with Long Reach). A swimmer commits only after crossing a throat. Membrane health is capped at 100. Echo has a one-bar cooldown.

**Invariants.** The six above, plus: the route has exactly two forks, each with a downstream rejoin, and the arms of the two forks share no film.

## 3. <Illusion Ledger>

| illusion the player must hold | mark | why |
|---|---|---|
| The jelly carries film as its body | <safe> | Frames visibly travel from contact point to bell to arm (BR3). |
| A point cloud is a picture | <uncertain> | v4 drew 66,000 splats at about 0.6 px and showed nothing. Softness and footprint must be verified in screenshots. |
| The fork matters | <safe> | Each branch has different films, creatures, songs and power-ups, and its gains pay off at the next fork. |
| The anglerfish is dangerous | <requires-participant-devotion> | It can end the dive early, but it can never take banked work. Fear has to come from losing the rest of the route. |
| The route is part of the edit | <requires-participant-devotion> | The cut records the route, but the meaning is only there if the player reads their path as authorship. |
| The music scores the reach | <uncertain> | In v5, streaming was never heard (github.io was blocked). The beat clock must fall back to the analysed bpm. |
| The partner shares my world | <uncertain> | PeerJS across devices is unmeasured. The seeded world holds. Live claims are the risk. |
| The archive is alive | <requires-participant-devotion> | Creatures move on their own clocks, but the player has to grant them intent. |
| The Screening Room shows what I took | <safe> | It holds if `{filmId, t}` survives every format switch. |

## 4. <Operational Description>

**Input.**
- <drag vector, beyond a dead zone of 6% of the short side> [transforms into] <STEER: thrust proportional to length, saturating at 30%>. On release it [transforms into] <DRIFT> with damped deceleration.
- <tap / Space> [transforms into] <CAST: an arm tip reaches 2.5 m toward the nearest resolved FilmCloud>.
- <hold Focus> [transforms into] <FOCUS: the local current falls to 25%, clarity shifts to the side film, and the score's low-pass opens>.
- <hold Look> [transforms into] <LOOK: the camera arcs up to 35°, keeping the horizon level>. On release it [transforms into] <the same trailing composition along the same arc>.
- <Echo pressed within ±120 ms of a beat> [transforms into] <a 40 m reveal ring on the map>. Pressed off the beat, it [transforms into] <the same ring, deferred to the next beat, at 25 m>.

**Actors.**
- <Swimmer> [performs] [reading the current].
- <CombJelly> [performs] [tracing streamlines with its rows of cilia]. Touching it grants <LongReach>.
- <ShrimpShoal> [performs] [scattering ahead of danger]. Shrimp peel away before the anglerfish turns.
- <Ray> [performs] [a broad wake]. Entering it within 1.5 s grants <Slipstream>.
- <Anglerfish> [performs] [a two-pulse lure → a body revealed through displaced silt → a bounded chase].
- <RedFragment> [performs] [broken frame order]. Contact scrambles the arm display order for 4 s. The data order never changes.
- <Partner> [performs] [lighting an adjacent slice] and [gifting].

**Rules.**
- <throat crossing> [enables] <commitment>. Before the throat, both mouths stay previewed on the micro-map, which resolves "where do I go".
- <rejoin eddy> [enables] <recovery>: +35 health, once per visit. This resolves the tension that pressure keeps building.
- <the two-pulse lure, paired on the beat> [blocks] <confusing it with archive light>. This resolves "is that treasure?"
- <membrane = 0> [enables] <early surfacing with every frame banked>. This resolves the risk without taking work away.
- <the session authority's first valid claim> [blocks] <duplicate capture>. This resolves a simultaneous touch.

## 5. <Failure Description>

**Spoil-sport vectors: solo.**

| vector | neutralisation |
|---|---|
| Wedging into a wall to stall or to clip the camera | The outward velocity is removed at contact, so the swimmer slides along the wall. A camera collision check and a bounded follow distance keep the camera free. The main current always carries the swimmer onward. |
| Refusing to choose at a fork, hovering on the pillar | The pillar's SDF slide plus the diverging particle streams push the swimmer into one throat within about 4 s. Neither throat is a default. |
| Camping in an eddy to farm health | An eddy restores health once per visit. It re-arms only after the swimmer leaves its radius for 20 s. |
| Infinite drift and never surfacing | The current is net-forward. Every reach ends at a rejoin or at the surface. The surface threshold decelerates the swimmer and always yields the Screening Room, even after an empty dive. |
| Farming one film for frames | A frame instance is captured once (`captureId`). A repeat touch on the same instance is a watch, not a capture. |
| Muting the music to break the beat | <BeatClock> runs from the reach's analysed bpm without audio. Echo windows stay identical. |
| Baiting the lure for the rare frame repeatedly | The rare frame is a single instance. Long Reach lets the swimmer take it from outside the strike radius. Without it, the cost is a bite (−40). |

**Spoil-sport vectors: co-op.**

| vector | neutralisation |
|---|---|
| Forged or racing capture claims | The authority accepts the first claim it receives for a `captureId`. A claim needs the claimant's position within cast range on the authority's last snapshot. Rejected claims dissolve visually and are never awarded. |
| Camera tugging and body-blocking | Cameras and steering are fully local. Swimmers pass through each other, and there is no swimmer-on-swimmer damage. |
| Gift spam | A gift arrives as a small drifting cloud. The receiver takes it with Cast or ignores it, and an ignored gift dissolves at the surface. A gift keeps the giver's provenance and does not remove the giver's copy. |
| Rage-quit mid-encounter or host loss | Each swimmer's bank is local and authoritative for its own frames. On host loss, the next peer becomes host. If no peer is left, the swimmer finishes solo in the same seeded world. |
| Tampered share link | A shared cut carries `{filmId, t, captureId, route}` per frame. The Screening Room marks frames that have no matching route record as unverified. It never silently accepts them. |

## 6. <Change Test>

**Scenario 1: remove the walls (spatial).** The archive becomes open water. The throats vanish, so commitment has nothing to attach to, and a fork becomes a preference rather than a choice. What survives: the current field. Redefine the throat as the separatrix between two streamline basins, made visible by comb-jelly tracers. The fork survives if the swimmer can still read the split before crossing it. If the separatrix cannot be seen, the fork fails. **Verdict:** the walls are not essential. The visible split is.

**Scenario 2: remove the surface (temporal).** The dive never ends. Frames still bank, but a cut is never closed, so authorship never arrives. Membrane health turns into a slow timer rather than a stake. **Verdict:** the ending is load-bearing. The magic circle needs a closing threshold, and the early-surface rule exists to guarantee one.

**Scenario 3: remove the room boundary (co-op).** Every player shares one global archive. The capture claims across all players exhaust each film within minutes, and the forks stop meaning "what *I* found". **Verdict:** the seeded room is the circle for co-op. It stays at two to four swimmers.

## 7. <Implementation Plan>

| feature | module | state owned | boundary |
|---|---|---|---|
| Drag steering, Cast, Focus, Look, Echo | `input` | pointer origin, held flags | Emits intents only. It never writes world state. |
| Level trailing camera | `camera` | arc angle, follow distance | Reads the swimmer. Holds the bell at 12–18% of the short side. Roll is 0. Arcs ≤35°. Has a collision check. |
| Two forks and rejoins | `route` | reach graph, current reach, committed throats, trace | The only writer of `reach`. Commits on a throat crossing. |
| Creatures | `ecology` | per-creature clock and state machine | Changes the local current field. Emits `damage` and `grant` events. |
| Arms and frames | `arms` | `Map<filmId, Frame[]>` sorted by `t` | The only writer of the bank. Append-only during a dive. |
| Membrane health | `membrane` | hp 0–100 | Emits `surface(early)` at 0. |
| Power-ups | `powers` | lantern charge, timers | Modifies cast range, speed and the warning radius. |
| Echo and the map | `map` | revealed cells | Micro-map: current reach plus next decision. Expanded map: explored reaches plus surface. |
| Songs per reach | `score` | song id, BeatClock phase | Crossfades on bar lines. Falls back to analysed bpm. |
| Screening Room | `screen` | cut order, playhead `{filmId, t}`, format | Edits reorder. They never alter provenance. |
| Tutorial | `tutorial` | step index | Lives only in the Entry Reach. Each step clears on a performed input. |
| Title animation | `title` | particle targets | Lives outside the circle. Tapping starts the dive. |
| Co-op | `room` | seed, peers, claim ledger | Authority resolves claims. Peers send intents and claims, never banks. |

Build order follows the spec: camera and steering in a sparse tube → one fork, its map and its rejoin end to end → one ecology encounter → capture, arms, surface and screening solo → membrane and power-ups → score → co-op.

## 8. <Ludic Architecture>

**Route and score.** Bpm, centroid and energy are from `music.json`.

| reach | song (id) | bpm · cent Hz | play state it shapes |
|---|---|---|---|
| Entry Reach (tutorial) | *Preparation & Drift* (daehoned-10) | 117.45 · 394 | The tutorial steps advance on the bar. Its quiet opening (env `0364310…`) leaves room for the prompts. |
| Lantern Grotto | *Gospel Under Water* (siltwire-02) | 117.45 · 347 | Darkest centroid in the set. Current at 0.5×, so Focus is cheap. Lantern motes pulse on the beat. |
| Ray Run | *Amphibian Escape & Concrete Smoke* (blackwater-02) | 143.55 · 2852 | Current at 1.6×. A ray passes when env ≥ 7 (env `0669688…`), so wakes come on loud phrases. |
| Rejoin A | *Lost & Found (Under the Courthouse Eddy)* (siltwire-06) | 103.36 · 1072 | Eddy, +35 health. |
| Silt Pocket, lurk | *Silt Bench* (siltwire-15) | 99.38 · 929 | Flat energy. The lure pulses twice per bar, on beats 1 and 2 (0.60 s apart). Archive light never pulses on the beat. |
| Silt Pocket, hunt | *Ritual of the Ash and Silt (2)* (twobuttons-14) | 107.67 · 1311 | Pursuit lasts at most 4 bars (8.9 s), then the anglerfish returns to its patrol. |
| Interference | *Static Smoke Phase* (blackwater-16) | 103.36 · 1693 | Sustained high energy (env `887999…`). Red fragments surge on env peaks of 9 and clear on lower beats. |
| Rejoin B | *Stay in the Current* (siltwire-10) | 92.29 · 989 | Eddy, +35 health. |
| Surface, then Screening Room | *Go Home and Be Free* (twobuttons-06) | 95.7 · 1314 | The last wake passes. Playback starts on a downbeat. |
| Early surface (hp 0) | *The Long Descent (Memory Rot)* (nightbus-14) | 123.05 · 930 | Plays on the way up after an early end, then hands over to the Screening Room. |
| Title | *The Fragile Iron Ghost* (nightbus-13) | 83.35 · 1434 | A 41 s loop. The particles assemble on the beat. |

**Transitions.** Wait for the outgoing song's next bar line, then run a 2-bar equal-power crossfade. The incoming song's first beat lands on the outgoing bar line.

**Damage and restoration.**

| source | warning | hp |
|---|---|---|
| Anglerfish bite | lure → shrimp scatter → body resolves, warning radius 15 m (22 m with Lantern) | −40 |
| Touching the lure | the two-pulse cue | −15 |
| Red fragment | red grain at the edge 1 s before | −10, plus 4 s of scrambled arm display |
| Wall scrape above 4 m/s | — | −3 |
| Rejoin eddy | — | +35, once per visit |

**Power-ups.**

| power | source | effect | duration |
|---|---|---|---|
| Lantern | 5 lantern motes (Lantern Grotto) | Extends the anglerfish warning radius to 22 m, lights the escape eddy and shows the lure's stalk | 30 s, starting at Silt Pocket entry |
| Long Reach | touching a comb jelly | Cast range 5 m, which lets the swimmer take the rare frame from outside the strike radius | 45 s |
| Slipstream | entering a ray wake within 1.5 s | +60% speed, and Interference fragments pass without contact | 8 s |
| Echo | always available | A 40 m reveal ring on a beat (25 m off-beat, deferred) | 1-bar cooldown |

Fork A pays into Fork B: Lantern and Long Reach favour Silt Pocket, and Slipstream favours Interference. The choice is legible at the second mouth.

**Capture.**
```
on cast(tip, cloud):
  if dist(tip, cloud) > castRange or cloud.instance.captured: watch(cloud); return
  claim = {captureId: cloud.instance.id, filmId, t: cloud.playhead, swimmer, route}
  if room: send(claim) to authority; await accept   // first accepted wins
  arms[filmId].insertSorted(claim, by t)           // a new film unfurls a new arm
  bank.commit(claim)                               // irreversible inside the dive
```

**Ending.** `surface(normal | early)` → stop propulsion → show the route trace once → open the Screening Room with every banked frame → offer Watch (splats | timeworm, keeping `t` on switch), Edit, Share, Dive again and Leave.

## 9. <Theory-Play Mapping>

| theory | type / function | state boundary | rendering |
|---|---|---|---|
| Magic circle | `Dive = {seed, reach, hp, bank, trace}` | opens at Entry, closes at `surface()` | Dark teal water. The surface is a light gradient that decelerates the swimmer. |
| Move | `Intent = Steer(v) \| Cast \| Focus(b) \| Look(b) \| Echo` | `input → intent`, with no direct writes | Bell contraction, an arm tip reaching out, a focus pull, the camera arc, an echo ring |
| Choice | `commit(throat): Reach` | before the throat it is a preview, after it a trace | Diverging particle streams. The chosen line brightens on the micro-map. |
| Stake | `hp: 0..100` | `hp = 0` ⇒ `surface(early)` | Rim brightness and a bell tremor. Never a HUD bar slab. |
| Possession | `Frame = {filmId, t, captureId, route}` with `bank: Frame[]` | append-only | Flecks pour into the bell, then a bead joins its arm in `t` order |
| Rhythm | `BeatClock(bpm, phase)` | per reach, crossfaded on bars | The lure's paired pulse, mote pulses, the echo ring |
| Fellowship | `Claim`, `Gift` | authority-ruled, local banks | A cyan partner, a drifting gift cloud |
| Authorship | `Cut = Frame[]` (reorderable) with `route` | outside the circle | A splat bloom or a timeworm, never a rectangle |

## 10. <Residual Meta-Logical Theory>

**The film worth stopping beside.** The rules can make watching cheap (Focus, Lantern Grotto at 0.5× current). They cannot make a film worth watching. That depends on the 109 films and the user's taste, and the design can only clear room for it.

**Fear without loss.** Banking everything at capture is the right promise for an archive, but it removes the usual stake. The anglerfish threatens only the rest of the dive. That stake holds only if the forks ahead visibly promise more material. If they do not, the predator is spectacle.

**The feel of drift.** The v5 notes say plainly that no person has played it. Proportional steering, the 12–18% bell size and the eddy restoration are hypotheses until a hand holds them. The referee measures them, and players judge them.
