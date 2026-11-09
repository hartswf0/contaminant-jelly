# SCION SYSTEM INSTRUCTION: THE THINKING JELLY (a jelly to think with, and to hear)

**The direction:** "We need jelly that can help us think, and with great sound", with the six-principle interface brief (surface the invisible, overcome cognitive limits, multiple modes, direct manipulation, semantic zoom, constrained play), and: "consider modelling not just the jelly but the jellyfish muscles, etc."

## The component, and what was weak
- **Component:** Jelly Jar (`jellyjar.html`), a jellyfish cast in gelatin that you grab and wobble.
- **Its behaviour:** it answers the hand, and nothing else. It has no reason to move. Everything that makes a real jellyfish pulse was missing:
  - who decides;
  - how the decision travels;
  - what pulls;
  - what springs back.

  What it did have (the tetrahedra, the strain) was hidden.

## The redesign: model the animal, then make every part of it visible, audible and touchable
**Where:**
- the page: `bonus/thinkjelly.html`;
- the nervous system: `bonus/thinkjelly-sim.js`;
- the body: `bonus/jellyjar-sim.js` (the same soft body, now also afloat);
- on the index's Bonus shelf.

### What is modelled
| part | the model | what it does |
|---|---|---|
| **Eight pacemakers** (rhopalia) | each charges at its own rate (its own beat is between 1.62 s and 2.8 s) and fires when full | the first to fill **leads** the beat |
| **The nerve ring** | 48 stretches of ring. A firing stretch excites its neighbours 21 ms later and then cannot fire again for 0.42 s. It runs on its own 5 ms clock, so a slow frame cannot slow the signal. | the signal runs **both ways round**; the two waves meet at the far side and die; a pacemaker the signal passes is **reset** |
| **The coronal muscle** | 500 or so edges of the lower bell that run round it; each twitches when its stretch of ring fires (0.1 s up, 0.32 s down) and is then up to **30% shorter** | the rim squeezes, in the order the signal arrives |
| **The jelly** (mesoglea) | the tetrahedral soft body from Jelly Jar: 2,208 tetrahedra that each keep their volume | squeezed, it stores the spring that reopens the bell |
| **The water** | where the rim is closing, the bell there is pushed along its axis | it swims; an uneven squeeze turns it |

### The six principles, as built
1. **Surface the invisible.**
   - **Four views of the same running animal:**
     - **FLESH:** as you would see it;
     - **NERVES:** the ring, with the signal running round it as light;
     - **MUSCLE:** each fibre brightening as it twitches;
     - **STRAIN:** every edge of the jelly, warm where stretched, cold where squeezed.
   - **Each pacemaker wears a ring that fills as it charges,** so you can see who is about to fire.
2. **Overcome cognitive limits.** A beat is over in half a second, so **the score** keeps the last 14 seconds:
   - a row per pacemaker;
   - a gold tick for the one that led each beat;
   - small ticks where the signal passed the others, which fan out diagonally (that is the wave, drawn);
   - grey ticks for silenced ones;
   - the muscle's pull underneath.

   The stats line reads the beat rate, the current leader, and what you have changed.
3. **Multiple modes.**
   - **Four views:** as above.
   - **Three situations to compare:** **INTACT**, **ONE PACEMAKER**, **TRAPPED WAVE**.
   - **Two dials:** **cold–warm** (every pacemaker's rate; a warm jelly beats faster) and **soft–firm** (the jelly's stiffness).
4. **Direct manipulation.** Touch the animal itself:
   - **FIRE** a pacemaker now;
   - **SILENCE** one, or wake it;
   - **CUT THE RING** between two pacemakers, or join it.

   The beat, the score and the sound answer at once.
5. **Semantic zoom** (pinch or wheel).
   - **Far:** the path it has swum.
   - **Middle:** the organs and their charge.
   - **Near:** each pacemaker's numbers: its own beat, when it will fire, and how hard the muscle beside it is pulling.
6. **Constrained play.** Every intervention is reversible: **UNDO** steps back through them, and the three situations are one tap each. Nothing can be broken. These are the classic experiments, made safe:
   - **Romanes (1870s):** cut away pacemakers and the beat slows; one is enough.
   - **Mayer (1906):** a wave trapped in a ring circles for ever.

### The sound (it is information, not decoration)
- **Each pacemaker has a note** (D3 F3 G3 A3 C4 D4 F4 G4), a bell-like FM pluck, panned to where it is on screen.
- **The leader plays its note in full; the signal strums the others softly as it reaches them.** So every beat is an arpeggio whose order is the wave's path. A new leader changes the melody; a cut changes the order; the trapped wave is an endless round.
- **The signal itself** is a fine hiss of grains travelling round the ring, panned.
- **The muscle** is a low thump on each led beat, and a low tone that follows how much of it is pulling. The trapped wave has no thump, only a steady tone: you can hear that it is a constant squeeze, not a beat.
- **The water** is a hush that brightens with speed.
- **Space:** all of it sits in a generated three-second reverb.

## Tested
**The nervous system alone** (in Node, at 12 to 120 frames a second: the same result at each):
| experiment | result |
|---|---|
| Intact | **37.0 beats a minute**, the fastest pacemaker's own rate (its beat is 1.62 s); it led 24 of 26 beats; every stretch of ring fired exactly once per beat |
| The fastest silenced | **31.5** (the next fastest, 1.9 s, gives 31.6); the new leader took a few beats to capture the others |
| Only the slowest left | **21.4** (2.8 s) |
| One cut in the ring | still 37.0, and every stretch still fires: the signal goes the long way round |
| Two cuts | the two halves beat apart |
| Trapped wave, no pacemakers | still circling after 20 s (18 laps) |
| Warmer (×1.5) | 55.4 |

**The page** (simulated browser, real mouse clicks):
- **Intact:** 37 beats a minute, led by pacemaker 5.
- **SILENCE:** a click on the leader gave 32, led by pacemaker 2.
- **UNDO:** woke it again.
- **TRAPPED WAVE:** read "a wave circling, with no pacemaker".
- **Swimming:** the jelly swam, with its volume at 100%.
- **Errors:** none.

**Fixed along the way:**
- **Slow frames slowed the signal.** On slow frames the signal crossed only one stretch of ring per frame, so several pacemakers led at once (55 a minute). The nerve now has its own 5 ms clock.
- **Two leaders in one beat were counted as two beats.**
- **The muscle view was hairy.** The muscle included long diagonal edges.

**Not yet judged:**
- **The sound by ear.** It was built and runs without errors, but this machine cannot listen.
- **Feel on a phone.**
- **Swimming speed.** Whether it looks right; it is a simple thrust model, not fluid dynamics.

## Next
- **Radial muscles and the manubrium**, for deliberate turning; and a light or a touch that the pacemakers respond to, so it steers itself.
- **Record an experiment** as a score you can replay and compare side by side.
- **Bring this animal into the films:** its beat as the clock that cuts between shots.
