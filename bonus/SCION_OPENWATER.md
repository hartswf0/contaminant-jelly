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

## 4 · The feel, rebuilt
**The direction:** "steering is awkward in open water, the details are bad, the level design doesn't match the others, not enough haptic or satisfying steering."

**Steering: point to swim, as in the drifts.**
- Hold the water where you want to go. Your jelly's heading swings toward that point, 24 m out along your finger's ray.
- Turning is quicker when cruising and wider when pushing hard.
- The velocity bends toward the heading, so you never skid sideways.
- W A S D and R F, or a gamepad's left stick, steer by hand.

**Strokes: the bell is the engine.**
- Swimming comes in strokes timed to the song (143.5 bpm): every two beats cruising, every beat when pushing (two fingers, shift, or the right trigger).
- Each stroke throws you forward and closes the bell. It also sheds a ring of wake flecks, kicks the field of view out, thumps (a pitched-down sine with a noise breath), and ticks the motor: phone vibration, or gamepad rumble.
- Between strokes you glide, and the bell relaxes. Left alone, it breathes.

**Camera:**
- a damped spring behind and above you, pulling back with speed;
- it rolls a little into turns and widens when you push;
- it shakes when you hit the floor.

**Feedback:**
- haptic patterns for a stroke, taking a film, finding a place, entering a ring, and bumping the floor;
- a comb jelly's rainbow runs down your bell when you brush one;
- the HUD goal (places 4, films 12) ends in a ★ moment, and the water is sealed (`open-water`).

**The look of the drifts:**
- **The water:** a lit haze, lighter above (the same background-gradient method), fog-faded black silhouettes for the floor, kelp and rocks, and reef bulbs glowing teal and amber.
- **The films:** clouds of flecks sampled from their footage, which gather into a clear oval screen as you near.
- **The places:** rings of points instead of solid torus rings, and black landmarks lit by points of their own colour.
- **The trench:** the Afterlight's own medusae, live rigs with tentacles, rising and sinking.
- **Life:** a school of flecks that runs ahead of you and parts as you pass, 26 rainbow comb jellies, and marine snow that streams past.
- **The card:** the drift briefing (the verb, three steps, the goal) and the same jelly picker.

**Guidance:**
- amber edge arrows to the nearest films;
- the nearest unfound place named at the edge, with its distance;
- a round corner map (tap it, or M, for the full map).
