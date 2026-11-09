# SCION SYSTEM INSTRUCTION: THE REAL JELLY, AND THE JELLY REEL (a jelly that feels real; the film it makes of itself)

**The direction:** "How to make it feel real, fully a real-jelly or jelly-reel … make the best jelly-sim jelly film you can." It came with research notes:
- how jellyfish move, hunt, sense and learn (after Ze Frank's *True Facts: How Jellyfish Hunt* and the box-jelly learning studies);
- the robot jellyfish (Max Planck, Caltech, FAU, Festo, Virginia Tech);
- what would make an autonomous jelly feel real;
- the Quixel Megascans on Fab, and how they load in Three.js.

**Role.** "Real" here means **causally real**: every behaviour comes from a mechanism that is running, not from an animation. The film is made by pointing cameras at that running animal.

**Where:**
- the page: `bonus/realjelly.html`;
- built on the Thinking Jelly's nerve model (`thinkjelly-sim.js`) and the soft body (`jellyjar-sim.js`);
- on the index's Bonus shelf.

## 1 · What makes it feel real, and what is built
| what the notes say makes a jelly real | built as |
|---|---|
| **Less than 1% muscle; two sets** (circular and radial) | The ring muscle (522 edges round the lower bell, up to 30% shorter) and the radial muscle (edges from crown to rim, 10% shorter) twitch together where the nerve signal passes. |
| **Spring-loaded recoil** | The body is a volume-keeping soft solid: squeezed, it stores the spring that reopens the bell. No force opens it. |
| **Vortex rings, and the second push for free** | The squeeze pushes the bell and throws a visible ring of water back. As the bell reopens, a second, smaller ring forms inside it and pushes again: about 30% of the squeeze's push, at no cost. |
| **Rim-based steering** | Each stretch of rim pulls harder or softer (0.25× to 1.9×). A stronger pull on one side swings the bell away from that side. |
| **Balance stones (statocysts)** | An innate pull toward upright. It also feels the surface and the floor coming, and levels off about 2 m short of them instead of hitting them. |
| **Eyes on the rim** | It turns toward **the light, which you place**: tap the water. You never steer it; you move its world and it answers. |
| **Stinging tentacles, oral arms, the mouth** | 24 tentacles and 4 frilled oral arms trail as chains. Plankton that touches one is stung (a spark, a tick) and carried to the mouth. A fired harpoon cell is spent: the tentacles need 0.45 s between stings. The reopening bell draws nearby plankton in. |
| **Learning without a brain** (the box jelly and the wall) | The tank's wall is grey bars. Every bump raises what the pacemakers have learned (by 22%) about turning away from a near wall. After a few bumps it keeps off the wall, even with the light beyond it. |
| **Reactive bioluminescence** | Touch the jelly (or let it bump): light runs down its eight canals and fades, and a pacemaker fires so it pulses away. |
| **Jelly-reel** | The plankton is film: specks the colours of an archive clip's frame. What it eats plays in its **four stomachs**, which fade as it digests. |

## 2 · The Jelly Reel (FILM ▶)
A ten-shot film, about 90 seconds, shot live on the running animal: nothing is pre-rendered, so it is different each time.
- **Its own beat cuts it:** each shot holds for its minimum time, then cuts on the jelly's **next beat**.
- **Each shot picks its view and camera:** flesh, nerves, muscle or strain; wide, close, from beneath, from far.
- **Some shots set a stage:** one moves the light to the side for the steering shot; one puts it beyond the wall for the learning shot.
- **Captions** in the lower third state what is happening, in plain words.
- **Film look:** letterbox bars and a small "● JELLY REEL · shot n of 10" slate.
- **Stopping it:** tap anywhere to stop the film and play.

## 3 · Playing with it
- **Tap the water:** the light moves there.
- **Tap the jelly:** it flares and pulses away.
- **Drag** to look round it; pinch or wheel to zoom.
- **The four views** are always available.
- **LAB** opens the Thinking Jelly's experiments: fire or silence a pacemaker, cut the ring, the trapped wave, undo, warm or cold, soft or firm.

## 4 · Tested (simulated browser; times on the game clock)
| test | result |
|---|---|
| The Jelly Reel | all its shots played in order in about 85 s, each with its view and caption, cutting on beats, with no errors (run before the wreck shot was added) |
| The light, placed 7 m to one side and behind its heading | the bell's axis swung from pointing away (−0.70) to pointing straight at it (0.99); the rim's pull ranged from 0.52× to 1.51× |
| The surface | with the light far overhead it climbed, then levelled off about 2.5 m below the surface and cruised, instead of ramming it |
| Feeding | 51 stings and 51 swallowed in 12 s; the stomachs filled; volume 100% |
| The wall, with the light held beyond it | it bumped, learned to 100% within about four bumps, and afterwards sat 4.5–8 m from the centre of a 10 m tank; a few later bumps still happened |
| The wreck | no particle of the jelly was ever inside the steel (0 over 20 s beside the hull); volume 95–100% |
| The scene without the Fab files (as on the public site) | loads with no errors: the wreck, barrels, gravel, the CC0 rocks and seabed |

**Fixed along the way:**
- **Stings were unlimited.** The jelly ate 644 plankton in 12 s. Tentacles now need 0.45 s between stings, and the inflow is weaker.
- **It rammed the surface and flipped over.** It now feels the surface and floor coming, and levels off.
- **The scanned rock and coral were in centimetres,** so they were 100 times too small.
- **The bell vanished against pale sand.** It is now milkier.

**Not yet judged:**
- the sound by ear, and feel on a phone;
- frame rate on a phone with the scene's textures (about 12 MB of CC0 assets);
- whether the jelly finds the breach on its own. It is drawn to the light inside and cannot pass through steel, but no test saw it swim in.

## 5 · The scene: a wreck on the seabed
**The direction:** two asset packs "to build the scene with".

| pack | what | licence | published? |
|---|---|---|---|
| Wreck and Seabed | four 1K material sets (rusty painted metal, rusty metal sheet, sand, gravel) and a barrel | Poly Haven, **CC0** | **yes**, in `assets/wreck/` |
| CC0 substitutes (added by the owner) | two coast-rock scans and a seabed sand | Poly Haven, **CC0** | **yes**, in `assets/fab/` |
| Jelly Fab Assets | Thai Beach rock, coral, and beach sand (Fab's low-quality GLBs, 1K) | Fab licence; the pack's own note says to keep the source files out of the public repository | **no**: those three are in `.gitignore`. The page adds them if they are there, and runs without them. |

**As built:**
- **The seabed:** a duned floor in the sand material, with a gravel patch under the wreck.
- **The hull:** a 10 m section of a ship's side, lying half sunk and tilted. It is open along the top and **breached on one flank**, with painted rust outside, sheet rust inside, eight ribs, and a fallen deck plate.
- **Steel is solid:** jelly particles that meet the shell are put back on their side of it. The breach and the open top let the jelly through.
- **Barrels:** two (the CC0 prop), one on its side by the breach, one half buried.
- **The reef (published):** six outcrops of the CC0 coast rocks, and the CC0 seabed sand on the floor.
- **With the Fab files present locally:** three more scanned rocks, six corals, and the beach sand instead.
- **A new shot in the Jelly Reel:** the light is put inside the wreck, and the jelly goes down to it.
- **Model loading:** three.js's own GLTFLoader (r160, MIT) is now in the project's vendor folder.

## 5b · The water, the light and the tentacles
**The direction:** "Why are the tentacles of the jellyfish not good? Why no caustics, or particles, sedimentation in the water? No light, no surface scattering, etc."

Each was missing; each is now built.

| what was missing | built as |
|---|---|
| **Caustics** | Every lit surface (seabed, gravel, hull, barrels, every scanned rock) catches a moving net of light from the surface: two layers of a tiling caustic pattern, strongest on upward faces, fading with depth. It is added in each material's own shader, so it needs no shadow maps. |
| **Light** | A lighter water column above and darker below; 52 soft shafts of light leaning with the sun, flickering; the light you place is now a real lamp that lights the wreck, the sand and the jelly around it. |
| **The surface** | Seen from below: a bright, rippling skin, brightest overhead (Snell's window), fading with distance. |
| **Particles** | Marine snow: 2,600 flecks sinking and swaying everywhere, near ones large and soft; it wraps round the camera, so it never runs out. |
| **Sedimentation** | Silt lifts off the seabed where a vortex ring reaches the bottom or the bell passes within 2.4 m of it; it billows, drifts and settles again over 7 s. |
| **Scattering in the flesh** | The bell has a bright rim where you see it edge-on, and glows through when the sun or the lamp is behind it. |
| **The tentacles** | They were 24 thin lines of 10 points. They are now 32 ribbons of 18 points that always face you: fine, tapering, faintly beaded with stinging cells, swaying and trailing with more drag. The four oral arms are broad frilled ribbons. They glow with the canals when the jelly is touched. |

**Fixed along the way:**
- **The bell vanished when the jelly swam far from where it started.** Its bounds were measured once at the start, so the renderer culled it. This was a real bug in play, also fixed in the Thinking Jelly.

**Tested:** the page loads and runs with no shader or script errors, with and without the Quixel files. The screenshots show the caustics on the seabed, the shafts, the surface, the snow, and the ribbon tentacles; a silt puff was triggered near the floor.

**Not yet judged:**
- **Frame rate on a phone.** This adds shader work to every surface, and the shafts and snow overdraw.
- **Whether the tentacles now read as good in motion.** I have only stills.

## 5c · One scale, and the Quixel scans published
**The direction:** "Un-ignore the Quixel scans and include them on the public site. The barrels are scaled wrong and the other stuff looks wrong too. Further: 404."

**The scale was wrong because the scene had none.** The jelly's bell is 2 units wide and the barrel was 1.6 units tall, so the jelly read as over a metre across beside a 93 cm drum. The scene now has one scale: **1 unit = 25 cm.**

| thing | real size | in the scene |
|---|---|---|
| the jelly | a 50 cm moon jelly | 2 units wide (unchanged) |
| a barrel | 93 cm tall | 3.7 units (was 1.6); three of them: on its side, upright and half sunk, rolled away |
| the hull | a section of a small ship, 3.2 m across and 6 m long | radius 6.5, length 24 (was 2.7 and 10); the ribs, the breach and the fallen deck plate scaled with it |
| the tank | 11 m across, 4.5 m deep | radius 22 (was 10) |
| the Quixel beach rock | 1.5 m | five, at 0.65 to 1.25 times true size |
| the Quixel coral | 30 cm | nine, around the rocks, at about true size |
| the CC0 coast rocks | pieces of a 20 to 60 m scan | used as low outcrops of a shelf, scaled down |

**The Quixel scans are published,** by the owner's instruction: `assets/fab/thai-beach-rock.glb`, `thai-beach-coral.glb` and `thai-beach-sand/` are no longer ignored. The public scene now has both sets of rocks, the corals, and the beach sand on the floor.

**Also fixed:**
- **Plankton drew as hard squares** close to the camera; they are soft round specks now.

**The 404:** every Pages deployment that completed succeeded, and all the files the page needs are in the repository. The deployment that first carried `realjelly.html` was cancelled when the next push arrived, so the page did not exist on the site for about nine minutes (21:24 to 21:33 UTC). The live site cannot be reached from the build session to confirm it now loads.

**Tested:** the rescaled scene loads with every asset and no errors. Screenshots show the barrel larger than the jelly, the hull's ribs arching over it, and the rocks and coral on the bed.

**Not yet judged:**
- whether the jelly's behaviours (the wall, the wreck shot) still read well in the larger tank;
- frame rate on a phone.

## 5a · What is not built
- **Real fluid:** the water is a thrust model with drawn vortex rings, not a fluid simulation.
- **Seeing:** the eyes sense the light's direction and the wall's nearness; they do not form images.
- **The life cycle** (polyp, the stack of clones) is not modelled.

## 6 · Next
- **Scanned reef and roots** in the tank, once the assets are in.
- **A second jelly:** two animals whose rings can be compared, or which avoid each other.
- **The life cycle as a level:** a polyp that buds the jellies you then play.
- **Record a take of the Jelly Reel** to a video file, so each run's film can be kept.
