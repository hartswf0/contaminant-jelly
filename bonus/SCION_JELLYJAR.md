# SCION SYSTEM INSTRUCTION: JELLY JAR (a real jelly: a jellyfish cast in gelatin, films set inside)

**The direction:** "We want a real jelly film jellyfish jelly jar, … like this: https://jelly.henrywithu.com/". That page is Trapnest Jelly: a glossy watermelon jelly you grab, stretch and twist, built on a volume-preserving tetrahedral soft body and WebGPU.

**Role.** Make the jelly *real*, as that page does: something with mass and gloss that answers your hand. Keep the object ours: **a moon jellyfish cast in gelatin, in a CONTAMINANT specimen jar, with film frames set inside it like fruit**, still playing. The method is borrowed; the watermelon, its look and its interface are not.

**Where:**
- the page: `bonus/jellyjar.html`;
- the solver: `bonus/jellyjar-sim.js` (plain JavaScript, tested outside the browser);
- on the index's Bonus shelf.

It runs on **WebGL**, so it works on phones without WebGPU.

## 1 · As built
**The body:**
- A bell (a dome over a hollow subumbrella, with a rim) voxelised at 0.16 and split into **2,208 tetrahedra** over **632 particles**.
- Each cube is split into six tetrahedra sharing one diagonal, so neighbouring cubes fit together.
- The mass is set by gelatin's density, about that of water.

**The physics** (XPBD, after Müller's Ten Minute Physics soft bodies):
- **Edges:** they resist stretching with a compliance, the firmness slider ("trembling" to "set").
- **Volume:** every tetrahedron keeps its volume exactly. Gelatin is nearly incompressible, and loosening this lost up to three-quarters of the volume, so it stays strict.
- **Contacts and steps:** the floor grips; the jar's glass wall holds the jelly in; 12 substeps per frame.

**The skin and what's inside:**
- **The skin:** a smooth bell with eight scalloped lappets, embedded in the tetrahedra by barycentric coordinates and smoothed along its own grid, so it does not crease where the tetrahedra meet.
- **Set inside, riding the flesh:**
  - **four horseshoe gonads** (a moon jelly's mark);
  - **six film frames**, each playing a different archive clip;
  - **forty bubbles**.

**The look:**
- **Gel:** rose gelatin (physical material: transmission, absorption, clearcoat, sheen).
- **Glass:** an open jar with a rim and a CONTAMINANT label, printed mirror-wise so it reads through the glass.
- **Studio:** soft light from four studio panels, made into reflections in-page, and a contact shadow.

**The hand:**
- **Grab:** grab the jelly anywhere and pull, in the plane facing you; let go and it is flung with your hand's last speed, and wobbles.
- **Turn:** drag the empty jar to turn it; the wheel zooms.
- **Buttons:**
  - **NUDGE:** gives it a push;
  - **FILMS ▸:** changes the clips;
  - **SHOW THE MESH:** shows the tetrahedra working.
- **Readouts:** mass (about 61 g at 1 unit ≈ 3.4 cm), volume (% of rest), and a wobble meter.

## 2 · Tested
| test | result |
|---|---|
| Settling under its own weight | sags about 7%, volume **100%**, then still |
| A pull in the solver, then release | stretched to twice its height, **rocked back and forth nine times** before resting, volume 100% |
| In the page, with real mouse input: grab the bell and pull up | the top rose from **0.73 to 1.71** (more than twice its height), volume **99.9%**, then sprang back after release |
| Cost | about 7 ms per frame for the physics on this machine's CPU |

**Fixed along the way:**
- **Volume locking:** perfectly incompressible tetrahedra locked the body rigid, and softening the edges did nothing.
- **Density:** the jelly was given the density of water as 1 instead of 1000, so it could not sag; it does now.
- **Opaque:** the gel was too dark to see into.
- **The skin creased:** it followed the coarse inner mesh; it is now smoothed.
- **The label was mirrored.**
- **The energy readout was off by orders of magnitude;** it is now a wobble meter.

**Not yet judged:**
- feel and frame rate on a phone (the glass and gel transmission costs extra rendering passes);
- whether the films inside read clearly enough through the gel.

## 3 · Next
- **A jellyfish that swims out of the jelly:** at a hard enough pull the gel tears (break edges past a strain), and the jellyfish inside is free.
- **Twisting with a second finger or the scroll wheel while holding.**
- **More casts:** the other species from Ten Bodies, each set in its own gelatin and jar.
