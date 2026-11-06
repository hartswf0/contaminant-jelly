# The Current (third version): the sewers of internet video

A creature of light swims the fog-choked sewers where old video still plays. It saves clips from the depths and avoids corrupted ones. The clips are the second-hand archive's 109 films, loaded from `secondhand-motion`.

## What changed from v2, and why
| v2 problem | v3 answer |
|---|---|
| The camera distance was hard to judge, and the creature was hard to steer in 3D. | **On rails.** The creature always swims forward down the pipe. Your finger or mouse position on screen *is* its place in the pipe's cross-section, reached with a critically damped glide. Arrow keys / WASD nudge it. A tap, click or space is a **dash** (speed and FOV kick). |
| The vertical tube didn't read. | **A long winding pipe** with a **chase camera**: low and behind, lagging, leaning into turns, pushing in when you save a clip, pulling back on a dash. |
| The tentacles read as hair and filled the lens. | **Eight time worms**: segmented Verlet tentacles with pulses running down them, trailing behind. They fade before they reach the lens. |
| Busy, bright. | **Fog that swallows** (dense exponential fog). Screens stay dark until the creature's light reaches them, and only glows carry through the haze: the gold creature, the red corruption. |

## The loop
- **Save.** Drifting clips play their films. Touch one with the mantle or a tentacle and it is saved: a brief slow-motion beat, a chime pitched to the film, a buzz, and the film's title.
- **Time worms.** The clip threads onto the shortest tentacle as a small screen that **keeps playing its eight frames**, and that tentacle lengthens.
- **Avoid.** Red static clips are corrupted video. Touching one flashes red and eats your newest clip.
- **Walls.** The screens lining the pipe wake and play when your light comes near.
- **Your reel.** *Play your reel* plays every saved clip, in order, for its eight frames. *Save reel* downloads an EDL (`the-current-reel.json`).

## The creature (original design)
- **Mantle.** 5,200 particles in a prolate mantle that leads with its head. 22% of them form a brighter inner nervous system of light.
- **Pulse.** A contraction runs from head to tail. Dashing quickens it and agitates the particles.
- **Tentacles.** Rotation-free Verlet chains (8 × 16 nodes), 12 alternating Gauss-Seidel passes, kept inside the pipe by its signed distance field. A wave travels down each arm.
- **Inspiration.** The compositing notes the user shared: depth fog, glows bleeding through haze, marine motion with trailing limbs. The shapes are original, not a copy of any film's machines.

## Measured
Headless Chromium, software rendering, 960×540 and 844×390 touch, with five films served locally.

| measure | result |
|---|---|
| 60 s scripted run (pointing at the nearest good clip, dashing every few seconds) | 17–25 clips saved from 5 films, about 200 m swum, no page errors |
| tentacle stretch | 2–7% |
| frame time p95, CPU side | 4–5 ms |

**Not measured:** real GPUs, all 109 films from github.io, and how it feels in the hand. No person has played it yet.
