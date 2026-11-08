# SCION SYSTEM INSTRUCTION: FLOW AND THE OPEN WATER

**Role.** A jelly's tentacles must flow from its motion. Choosing a jelly means playing with it. The bonus pieces sit in one open 3D sea that you swim between.

**The direction:**
- "many of the jellyfish have bad physics now that we made them interchangeable; their tentacles no longer act like before or have any flow"
- "in picking them we should be able to play with them"
- "the bonus levels: an open-world 3D game map to drive them around more"

## 1 · Flow: tentacles as verlet chains (`current/drift/rigs.js`)
**The cause.** When the jellies were made interchangeable, their tentacles became sine waves in the rig's own space. They waved, but never trailed when the bell moved.

**The fix.** Every tentacle is now a verlet chain in world space:
- its root is pinned to the bell's rim, which contracts with each stroke;
- the water drags it (it keeps 12% of its velocity per second);
- it sinks along the bell's own downward axis;
- a slow, curling current stirs its outer half;
- 8 constraint passes per frame hold each segment's length.

**Drawing.** Chains are drawn back in the rig's space. Ribbons (35 mm strips, timeworms, film strands) turn to face the camera; threads are lines.

**Jellies that came without tentacles** now carry the ones their versions swam with:
- the Film Bell: threads and two film strands;
- the Golden Splat: ten gold filaments;
- the Sewer Creature: trailing arms and two strands;
- the Celluloid: amber threads and two film strands.

**Wiring.** `update(s)` takes `dt` and `cam`. The engine, the character select and the open water all pass them.

## 2 · Play in the picker (`characters.html`)
**The jelly is yours to swim in a tank:**
- hold and drag, and it swims toward your finger, crown first;
- tap, or press space, for a single stroke;
- W A S D and Q E swim; ‹ › or [ ] change jelly.

**Its body:**
- the strokes quicken as it works;
- left alone, it drifts;
- the tank's soft walls turn it back;
- the camera keeps it beside the words.

## 3 · The Open Water (`bonus/sea.html`)
**The world:**
- an open sea about 900 m across, with a fbm seafloor of ridges;
- a deep trench under the Medusae, and the Doodle reef rising;
- 900 kelp ribbons swaying, 360 rocks;
- light shafts, and a rippling surface overhead;
- marine snow wrapping around you, bloom and fog.

**The places,** each a landmark with a glowing ring. Swim through the ring to enter:

| place | landmark | enters |
|---|---|---|
| The Reel Tower | a stack of reels inside a gold helix | Film-Reel Jelly |
| The Sewer Mouth | a drowned pipe with lit arches | Sentinel Timeworm |
| The Medusae Trench | golden medusae down the trench | Afterlight Medusae |
| The Doodle Reef | hand-drawn branching lines | Raw Doodle Worms |
| The Current | the start | the drifts |

**The films:**
- 60 archive films hang as soft screens, laid out on a golden-angle spiral;
- the nearest one plays its clip;
- swim through it to take it: the film lights your jelly's bell, and the Medusa lights a tentacle per film.

**Swimming:**
- hold to swim; the finger's offset from centre steers yaw and pitch;
- two fingers, or shift, to boost (the field of view widens);
- tap or space to stroke; W/S, A/D and R/F to steer.

**Camera:** a chase camera behind and above you, pulling further back the faster you go, and kept off the floor and under the surface.

**Guidance:**
- a minimap that follows you, and M (or tapping the map) opens the full map;
- a compass naming the nearest place and its distance;
- labels over each place;
- a HUD with films, places, depth and speed.

**Sound:** the water's own noise, opening up with your speed; a song from the bonus pieces; a tone on each stroke and each film.

**Links:**
- you swim as your chosen jelly (`cj-rig`), with a "change jelly" link on the card;
- the sea remembers where you entered a piece (`cj-sea`), so you return beside it;
- every bonus piece now has "← the open water";
- the main index lists the Open Water first on the Bonus shelf.
