# SCION SYSTEM INSTRUCTION: THE REPAIR LOOP (how to fix a jelly that does not look real)

**The direction:** "Re-measure the distance per beat and fix the thrust. The legs clip the body. The pulse is not really looking good: compare with some other species we have, and think about the prompt loop to repair."

**Role.** Stop repairing by guessing. "It doesn't look real" becomes a loop with five steps, and the loop is built into the project so anyone (a person or an agent) can run it.

## 1 · The loop
1. **Name the complaint as a measure.** "It goes too far" → bell widths travelled per beat. "The legs clip" → tentacle points inside the bell. "The pulse looks wrong" → how much the bell narrows, whether it deepens, and what share of the beat the squeeze takes.
2. **Give each measure a target range, with its source.** The source may be a paper, one of our own species that already looks right, or a stated judgement. A target with no source must say so.
3. **Measure the running animal,** not the code: beat by beat, on the visible skin.
4. **Change one thing,** the one the failing measure points at.
5. **Measure again.** Stop when every measure is in range. Then look at it: the numbers are necessary, not sufficient.

## 2 · The instrument (as built)
- **In the page: CHECK.** In the Real Jelly, open LAB and press **CHECK** (or add `?check` to the address). A panel lists every measure over the last four beats, with its range: green in range, red out. You can watch a slider or a cut change the numbers.
- **From a terminal:** `node sim/jellycheck/check.js`. It runs the page headless, lets it swim with the light held straight ahead, prints the same table, and exits 0 only if everything passes.
  - `--thr 0.8` tries a thrust.
  - `--beats 5` sets how long it swims.
  - `--full` uses the desktop build (the default is the phone build).
  - It needs Playwright.

| measure | target | where the target comes from |
|---|---|---|
| beats a minute | 8–21 | a mature moon jelly pulses at 0.24 ± 0.11 Hz (a 2026 preprint, citing earlier work) |
| bell narrows, % | 10–30 | our older species narrow up to 30% at the rim; no published figure was found |
| height / width, relaxed | 0.28–0.45 | "a shallow saucer": a judgement from standard descriptions |
| deepens when squeezed | 0.005–0.2 | the bell must get taller for its width, not flatter; the upper bound is a judgement |
| bell widths per beat | 0.2–0.45 | about a third: an estimate from typical swimming speeds, not from a fetched source |
| squeeze, share of the beat | 0.1–0.4 | our older species: 0.28; real contraction is the shorter, muscle-driven phase |
| tentacle points inside the bell | 0 | none |

## 3 · What the loop found and fixed this time
| complaint | measured | cause | change | measured after |
|---|---|---|---|---|
| "re-measure the distance per beat" | **0.95** bell widths per beat (the earlier cut had been a guess) | thrust too high | thrust 2.3 → **0.8**, now a named number (`?thr=`) | **0.31** |
| "the legs clip the body" | tentacle and oral-arm points passed up through the bell | nothing stopped them | every point is kept below the bell's underside, which moves with the squeeze | **0** inside; about 14,000 corrections in 17 s of swimming |
| "the pulse is not really looking good" | the bell narrowed **6%**, all at once | the soft body's ring muscle alone is too weak and uniform | the pulse of our older species, brought to the skin (see §4) | narrows **18%**, deepens |
| (found by the loop) | height / width 0.25: too flat | the body had been made too shallow | height 0.62 → 0.7 | 0.30 |
| (found by the loop) | deepened 0.22: too much | the crown's lift and the margin's sweep were too strong | both reduced | 0.17 |

**The final run passed every measure, on the phone build.** The desktop build passed all but the over-deepening before the last trim, and was not re-run after it.

## 4 · Compared with our other species
The older species (the Glass Moon, the Film Bell and the others in `rigs.js`) look right when they pulse. Their pulse is a hand-made shape with three properties the Real Jelly lacked:
- **It travels:** the squeeze reaches the rim later than the crown (a lag of 18% of the beat).
- **It is strongest at the rim** (weight rises as the 1.4th power from crown to rim), narrowing it up to 30%.
- **The crown lifts** a little as the rim closes.

The Real Jelly's pulse came only from its soft body: honest physics, but weak and uniform. The older species' shape is now applied to its **skin** on top of the body:
- the muscle's pull at each stretch of rim, delayed by up to 0.2 s toward the rim;
- narrowing up to 13% on top of the body's own;
- the margin sweeping down and in.

Because it reads the live nerve signal, a silenced or cut ring still shows in the pulse: an uneven signal gives an uneven squeeze.

## 5 · As a prompt (for the next repair, by person or agent)
> **Complaint:** (what looks wrong, in the viewer's words).
> 1. Which measure in CHECK would this move? If none, add one: what on the animal would you put a ruler or a stopwatch against?
> 2. What range should it be in, and where does that come from (a source, one of our species that looks right, or a stated judgement)?
> 3. Run `node sim/jellycheck/check.js`. Paste the table.
> 4. Name the one cause the failing measure points to. Change only that.
> 5. Run it again. Paste the table. Repeat from 4 until it exits 0.
> 6. Then look: two stills (relaxed, squeezed) and, if you can, ten seconds of motion beside reference footage. Report what the numbers could not tell you.

## 6 · Not yet judged
- **By eye, in motion.** The stills (relaxed and squeezed) now read as a saucer that narrows and deepens with the fringe hanging clear. Nobody has watched it move beside footage.
- **Weight.** The tentacles hang and trail (they keep a fifth of their speed each step), but there is no measure yet for "weight". A candidate: how far the fringe lags the rim during a squeeze.
- **The other pages.** The loop measures only the Real Jelly.
