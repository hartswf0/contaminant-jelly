# SCION SYSTEM INSTRUCTION · THE JAR EXPERIMENTS

Where: `bonus/jars.html` (one file). A shelf of five jars; each opens one experiment full-screen with a line of what
to try, a live reading, and two to four dials. `?jar=mountain|cube|plate|room|clay` opens one directly.

## 1. Thesis
A room you can play by touching its materials has to be learned one material at a time. Each idea in the brief
gets one jar: one thing to touch, one reason it changes, and a reading that says the reason in numbers.

## 2. The jars
| Jar | What you touch | What it shows | Dials |
|---|---|---|---|
| THE MOUNTAIN | drag to turn, rise, sink; tap to ping | a range under water; the jelly cannot pass through rock; a ping ring crosses the ground | height, roughness, light bands, murk |
| THE CUBE | drag to move the light | flat faces lit from a normal bent toward a ball, so the highlight rolls over an edge while the outline stays a cube; the outline is a second shell seen from inside | round, inflate, light bands, outline |
| THE PLATE | tap or drag across the panel; drag the brass weight | eight resonances; where you strike decides which wake; sand gathers on the still lines; a weight slows a mode by how much that mode moves under it; each strike leaves a print | weight, damping, SOUND |
| SOUND IN A ROOM | drag the listener and either speaker | a 6 by 4 m office from above; two speakers on one tone make bright and dark bands; CANCEL HERE and REINFORCE HERE set speaker B for the listener's spot; PING shows the direct sound and four first echoes | tone, speaker B lag, SOUND |
| THE CLAY | drag to turn | one field of density seen four ways: BANDS, MATCAP, VOLUME, STROKES; raise the surface value and the thin bridge breaks; LOOSENESS turns tight marks into large ones | surface at, looseness |

## 3. How each is made
- **Mountain.** A height picture made once from ridged noise (ranges) and soft noise (silt). The shader lifts the
  ground from it and takes the slope from it; the page reads the same picture to keep the jelly above the rock. The
  ground follows you, so the range does not end. Your jelly is whichever the sentence says, a made one included.
- **Cube.** `normal = mix(face normal, direction from the centre, ROUND)`. INFLATE moves the points themselves
  toward a ball. The outline is the same mesh pushed outward and drawn back faces only, in ink.
- **Plate.** Modes of a simply supported square plate, `sin(m·pi·x)·sin(n·pi·y)`. A strike adds to each mode by the
  mode's height at the contact. A weight changes a mode's pitch by `1/sqrt(1 + 3·mass·height²)`. The sand walks
  down the slope of the shaking. The bend is slowed so it can be seen; the pitches are not.
- **Room.** Direct paths only for the bands: level falls with distance, and the two arrivals add by their phase
  difference. Echo times use mirror images of speaker A in the four walls at 343 m/s. The ping is slowed about 150
  times.
- **Clay.** Five soft lumps add up to a field. BANDS, MATCAP and VOLUME march a ray through it for every pixel.
  STROKES walks 5,200 seeds along the slope of the field until it equals the surface value and draws a brush mark
  at each.

## 4. Checked (headless, real touch events; values read from the page, plus stills)
- **Mountain:** held down for six seconds, the jelly stopped 1.8 above the rock. A tap sent a ping; the reading
  followed it outward.
- **Cube:** ROUND at 1 and OUTLINE at 0.10 show the round highlight on the lower cube and a flat one on the upper.
- **Plate:** a strike in the exact middle woke modes 1·1, 1·3 and 3·1 equally and left 1·2, 2·1, 2·2, 2·3 and 3·2 at
  zero, as it should. Moving a heavier weight to the middle took 1·1 from 42 Hz to 26 Hz and left 2·2 at 248 Hz.
- **Room:** CANCEL HERE took the listener from 0.6 dB below in-step to 74 dB below; 0.6 m away it was 26 dB below.
  The direct sound arrived at 11.4 ms and the four echoes between 13.9 and 20.3 ms.
- **Clay:** the field between the two lumps was 1.72. Drawn at 1.00 the bridge was whole; at 2.20 it was broken.
  STROKES put about 4,600 marks on the surface.
- No page or console errors in any jar.

## 5. Not checked
- I cannot hear. The plate's tones and the room's tone were not listened to; only the dials and envelopes were run.
- Motion, real fingers, and speed on a phone. The clay marches 70 steps a pixel and may be slow on a small phone.

## 6. What is not here, plainly
- **Marching cubes.** The clay's surface is found by marching rays, not by building a mesh from cubes. The
  isovalue behaves the same; there is no mesh to export.
- **The room** has no reflections in its bands, no room tail, no head model. The echoes are first-order only.
- **The plate** is an idealised plate, not a measured panel. The weight is one point.
- **The reference repository** (colinfizgig/webgl-mountains) was not read; this session's access is to two
  repositories only. The mountain is written from the idea.
- **Not built:** the fan (motor hum, blade pass, housing), sonar mapping with the walls hidden, particles moved by
  sound, a footstep with heel, body and scuff, and wiring mass into the Particle Jelly solver.

## 7. Next
1. Put the plate on the floor of the blank room: a foot lands, the panel bends, the room answers.
2. Sonar: hide the walls and find the door by ping.
3. The fan as a sixth jar: five blades at 1,200 turns a minute is a 100 Hz tone.
4. A cube-marched mesh for the clay, so a form can be kept and brought into a room.
