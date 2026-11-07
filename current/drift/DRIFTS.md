# SCION SYSTEM INSTRUCTION: DRIFTS (video → game translation)

**Role.** You translate one video into one small playable drift. You do not make new videos; you read the ones we have, and you turn what each one *does* into a rule you can play.

**Origin.** The user's direction after v6:
- "No buttons on the screen."
- "Make sure we are able to more clearly see and watch films."
- "Consider making a game for each of the videos we currently have."
- "I would not make any more videos. Focus on translation and making more beta game variations."
- "All feel trapped in a tube … we want more levels, layers; see the drift idea."

Reference plates the user shared:
- side-on silhouette reefs and ruins with glowing bulbs, against a lit haze;
- a lone figure with a lamp in a cave;
- filament jellies;
- marine snow;
- silt floors, mussel beds and brine pools;
- kelp light.

## Invariants
1. **No tube.** Each drift is open water seen from the side.
   - The current carries you one way: right, up or down.
   - Silhouette layers stand in front of and behind the play plane, and fog makes far layers recede.
   - The edges of the water are reefs, ruins, kelp, pipes, caves, mussel beds or dunes, never walls you are inside.
2. **No buttons.** Every verb is a gesture on the water:

| gesture | verb |
|---|---|
| hold the water | swim toward your finger; let go and drift with the current |
| tap a film | swim to it and take the frame it is showing (with its timestamp) into that film's arm |
| hold on a film | watch: it blooms large and clear in front of you while the water nearly stops |
| double-tap | pulse: reveals films in the dark and in the silt, scatters shrimp, and reaches farther on the beat |
| pinch / scroll | pull back |
| two fingers / right-drag | look around |
| swipe in from the left edge, or Esc | back to all drifts |
| at the end: tap / swipe ← / swipe → | swim again / next drift / all drifts |

3. **Films are only clouds of flecks.** Far away they drift apart like water. Close up they condense into a picture. Held, they bloom to most of the screen. A film sits in the same plane as the camera's view, so it reads face-on.
4. **The water is lighter than its silhouettes.** Each drift has a lit haze: lighter above, darker below. Silhouettes are near-black and their bulbs glow. Light shafts fade at both ends.
5. **A clear end.** Each drift ends at a surface, a floor or the end of the current, with a card: the goal, the frames and films, the time, the cut list, and the reel playing behind it.
6. **One film, one arm; frames keep their source time.**

## The eleven translations
| drift | from | what the video does | the rule it became | song (start) |
|---|---|---|---|---|
| Ascent | design_v2 | tier after tier of small frames around a rising jelly | rise through galleries of sleeping films at three depths; brushing wakes them (goal: wake 14) | *Saltwater Static* 8.3 s |
| Pairs | design_v4 | soft ovals arriving in pairs (a face and a hand), red corruption | every pair is a cut: take a frame from both (goal: 4 pairs) | *Gospel Under Water* 130.8 s |
| Lure | design_v5 | a fork, an anglerfish with a lure, a school | the angler patrols the low water, warns with two pulses, lunges (goal: 8 frames unbitten) | *Steel & Static* 83.2 s |
| Toward the Surface | design_v6 | a huge face and hand beside a tiny jelly; water paling to a surface | the first film is enormous; the point is to stop and watch (goal: watch 2 for 4 s) | *Stay in the Current* 0.3 s |
| Halo | song neonbutterfly-02 | films orbit as a ring under the surface | the halo turns; take frames as it comes round (goal: 5) | *Catastrophic Elegance* (matched start) |
| Ray Run | song nightbus-03 | a great ray overhead; its wake pulls everything | ride under the ray for a slipstream; films stream past (goal: 10) | *Command Decent* (matched start) |
| Slices | song nightbus-06 | a diagonal chain of film slices; red squares | one film laid out in time as a chain; take its slices in order (goal: 8) | *Phosphor Waveform Log* |
| Twin Caves | song nightbus-08 | two cave mouths, sparkling dust | a rock tongue splits the water into an upper and a lower cave (goal: 6) | *Saltwater Static* |
| Bloom | song nightbus-13 | small films bloom around a rising jelly | watching is the game: hold and it blooms (goal: watch 3) | *The Fragile Iron Ghost* |
| The Long Descent | song nightbus-14 | a jelly sinks into a void, shrinking to a point | the light closes in as you sink; films show only near you or when you pulse (goal: 6) | *The Long Descent (Memory Rot)* |
| Silt Bench | song nightbus-17 | an anglerfish rising out of a silt floor | films lie buried; swim low and fast or pulse to stir them up; the angler rises from the floor (goal: unearth 5) | *The Wet Console* |

Matched starts come from `audio/song2game.json` (`songs[id].video.audio_start`, the moment the song lines up with its video).

## Measured
Headless Chromium, software GL, five films served locally; music streams are blocked in this sandbox.

| check | result |
|---|---|
| all 11 drifts, 640×360, a gesture-only bot (tap films, hold to watch, hold the water) | boot, play and reach their end card with no page errors |
| goals reached by the bot | Lure 8/8, Twin Caves 11/6, Ray Run 14/10, The Long Descent 6/6, Slices 7/8 |
| Silt Bench, swimming low and fast | 13 frames unearthed |
| Bloom, a 4.8 s hold on a film | counts as 1 watched; a repeat hold on the same film does not count twice |
| Halo, tapping the ring | frames taken from the halo |
| 390×760 touch | Ray Run 12/10, The Long Descent 9/6, no page errors |

**Not verified:**
- the songs playing (github.io is unreachable here);
- real phones and real touch;
- how each drift feels to play.

These are betas: each one tests one translated rule.

## The archive levels (real data, fluid play)
Built from the source repositories, not from screenshots:
- **`data/doodles.json`:** all 86 traced subjects of [secondhand-motion](https://hartswf0.github.io/secondhand-motion/), 1,777 drawn keys from `shots/*/drawn/k*.json`. Each key keeps its strokes (simplified), the note on why it was drawn, the source film and the year.
- **`data/cineosis.json`:** from [cineosis-lab](https://hartswf0.github.io/cineosis-lab/periodic-table.html) `lab/lab-data.json` and `cineosis-table.json`. It holds the 45 signs and 809 shots:
  - all 410 signed shots, each with an 8-frame strip;
  - up to 26 per decade from the 1900s to the 2020s;
  - an even spread across hues.

  Each shot has its title, year, palette, hue, subject and sign note.

Rules in these levels:
- **The water never stops.** Swim through a film while its reticle ring is closed to take its frame. Tapping still works for films set back in depth.
- **Light makes a film clear.** A pulse (double-tap), a speck of light, or the jelly's own light sharpens nearby clouds. The nearest lit one takes the 48,000-fleck cloud and shows its footage in place.
- **Doodles are crisp line-worms.** They are drawn from the real strokes and cycle through their keys. Catch one and its whole drawing lights up as a tentacle.
- **Tentacles dye fish.** A fish touched by a film tentacle takes that film's colour (the shot's palette, or the doodle's hue).
- **Specks of light.** Most give eight seconds of clear sight. One in four is an anglerfish's lure, and the angler comes out of the dark behind it.
- **Boost.** Two fingers steer toward their midpoint at speed (pinch still zooms). On desktop, hold Shift or the right mouse button. The camera leads with your velocity and widens when you boost.

| level | organised by |
|---|---|
| Secondhand Doodles | doodles only; goal: dye 40 fish |
| Menagerie | all 86 doodles as roaming creatures (curious or shy) |
| Strata | time: the oldest footage at the bottom, the newest at the top; the water warms from silver to colour |
| Spectrum | colour: the archive sorted by hue, and the water takes the colour of the films around it |
| People, Machines, Landscapes, Animals, Screens, Crowds | subject |
| 16 type levels | one cineosis image type each (Perception, Affection, Impulse, … Lectosign) |
| 45 sign levels | one sign each, laid out as the periodic table; the sign's question is the goal |

The main screen shows only the start, six episodes (Doodles, Menagerie, Strata, Spectrum, Ray Run, The Long Descent) and the periodic table. Everything else is under "More drifts". Every page carries the jelly favicon.

## Jelly-films (this round)
The films are now called **jelly-films**.

The user's direction:
- "the angler fish never eats us"
- "sometimes we need to see more clearly glimpses of the splats"
- "instead of having the videos zoom into the front … make them clear and transparent in the back and have some of their audio distantly play"
- "why don't the doodles animate? … eels or fish timefish or schools"
- "the bolas doodles we can populate in the ocean to try to capture"

What changed:
- **Clear in place.** Holding on a jelly-film no longer brings it to the front. It comes clear and see-through where it already is. The camera turns toward it and the water keeps moving.
- **Glimpses.** Every 7–12 s, one nearby jelly-film comes clear for a moment on its own, so you can tell what it is.
- **Distant audio.** When a cineosis shot with sound is lit or held, its clip plays through a lowpass filter. The filter opens as you get closer, the sound pans to where the film is, and the music ducks under it. 392 shots carry a clip.
- **Radar Doppler pulse** (after pretext-field/aidar). A double-tap or Space sends out a ring. Whatever it crosses flashes blue if it is coming toward you and red if it is moving away. Each one pings, pitched by its speed.
- **Doodles animate.** Each doodle cycles through its drawn keys, with a pencil scratch on each new key. It takes one of three forms:
  - an **eel**: its past keys trail behind it;
  - a **school**: four copies;
  - a single creature.
- **Bolas.** A new level with 321 drawn planes from 109 shots, taken from `bolas/allways-tensor/secondhand_worms_108.json`. Each plane replays its `strokes0` along its own track. Goal: capture 24.
- **The angler eats.** It patrols, then warns with two pulses, then lunges. A bite costs 34 membrane and a jaw closes over the screen. At 0 the dive ends with the card "SWALLOWED". One speck of light in four is a lure.

Measured (headless, software GL):

| check | result |
|---|---|
| Menagerie, pulse | 2 creatures flashed |
| Bolas | 321 planes load (the first is "grass", with 33 keys) |
| Lure, forced lunge | membrane 0, swallowed, end card |
| syntax / page errors | none |

**Not verified:**
- the distant audio and the music on a real device (github.io is blocked here);
- a bot test of holding on a sign film to watch it. It is flaky because it depends on where the camera lands.

## Seeing the films: screens
**The problem.** The user asked: "In all the videos generated see how the videos become clear? The last one we had with clear playing videos was v2 … the videos never get watched as videos in almost all of our work."

**The cause.** Since v4, every film has been drawn as flecks from a 128×96 slot, which is 8 frames in a shared atlas. The sources are much sharper:
- secondhand-motion frames are 384×288;
- cineosis strips are 8 frames of about 240×136;
- cineosis clips are 320–640 px video.

The splats threw most of that away. Pulling a film forward only made the blur bigger.

**The design videos (`fal/design_v*`) do something else.** The footage is projected into the water:
- one continuous, sharp picture;
- an oval edge that dissolves into the haze;
- darks gone transparent;
- tinted toward the water's colour;
- behind and beside the jelly, never in front of it.

v2 was legible for the same reason: real image planes.

**The rule now.** When a jelly-film comes clear, its real footage takes over as a **screen**: a soft-edged picture in the water, where the film already is.
- A film comes clear by passing near it, a glimpse, a pulse, a speck of light, or holding on it.
- Up to three screens show at once.
- **Edges:** an oval mask broken by moving noise, so the picture condenses out of the flecks. The fleck cloud fades by about 85% under it, and a few flecks still sparkle on top.
- **Tone:** brightness is mapped from the water's colour toward light, so dark areas sink into the water. Colour films keep half their colour; black-and-white films stay toned.
- **What plays:**
  - secondhand-motion films play their real frames;
  - cineosis strips crossfade slowly through their 8 frames, like a living photograph;
  - shots with a clip play the clip. It is the same video element that carries the film's distant sound, so picture and sound stay together.
- **Holding** opens the screen to about 60% of the view, in place, and the camera centres it. The film plays at its own speed even where the water slows.

**Measured (headless):**
- a 640-px clip plays in a screen (readyState 4);
- strip, frame and clip screens all render (snowy cars, a giraffe, Market Street in 1906);
- the phone HUD no longer overlaps, and film labels stay on screen.

## Clear everywhere, a back layer, and a mode for trailers
**The user's direction:**
- "bring the clear screens to v6 and the other versions too"
- "consider playing in the farthest back layer of the world in the dark water full"
- "think of each game as needing to be able to contribute to a trailer … a mode with less text and clutter"
- "clearer more visible videos in each experience where the viewer can't tell what is a generated video and what is a game"

**What changed:**
- **`current/screens.js`** is shared by the drifts, v4, v5 and v6.
  - `makeScreens()` gives each version the same projected-footage screens.
  - `backdrop()` is the farthest layer: one archive film plays full-frame in the dark water behind everything, faint, tinted to the water, with its darks transparent. In the drifts it is the film you last took or watched, otherwise the archive turning over every 24 s. In v4–v6 the archive turns over on its own.
  - The back layer sits at about 0.22 strength in the open drifts, and lower in dark levels and in the v4–v6 tunnels.
- **Cinema mode.** Press **H** or tap with three fingers; `?cinema` starts in it.
  - Every word on the screen goes: HUD, captions, hints, labels, cards and the reticle.
  - A slight vignette and moving grain are added, so the game reads like the design videos.
  - It works in the drifts, v4, v5 and v6.
- **Trailer mode** (`?trailer`, or `?auto` to keep the words). The drift swims itself:
  - it heads for the films ahead, takes them, holds on most of them to watch them open, pulses now and then and steers round interference;
  - at the end it moves on to the next drift.

  Gameplay clips for the index were recorded from it frame by frame at 24 fps: `play/<id>.mp4`, 640×360, 5 s.
- **Fix:** holding the water to swim had stopped working in the drifts. A `//` comment had swallowed that line; it is restored.

## Jars, bonus pieces, the trailer
**Jars** (`labels/`). Every piece has one SVG jar in the hand of the periodic table (`labels/cineosis/*.svg`): the same body, lid, reel, film strip and CONTAMINANT label.
- **The periodic table:** 45 sign jars and 16 type jars.
- **New jars** (`labels/jars/*.svg`, from `labels/make_jars.py`): 11 drifts, 5 archive levels, the subjects, and the 4 bonus pieces.
  - The new jars carry no periodic symbol. Their label is a window holding a cartoon of the mascot jelly, its own character for each (`labels/cartoons.py`). Lure is terrified, with a sweat drop and the lure's light close by. Pairs is two jellies holding tentacles. Ray Run surfs the wake. The Long Descent sleeps as it sinks. Bloom has heart eyes. The Medusae queen wears a crown.
  - On the index, the jar's film and then its game play inside that label window.
- **Two-tone prints** of every jar live in `black/` and `white/`: dark inks go to the ink, light inks to a mid grey, the label paper to paper.
- The game's intro card shows the level's jar.
- Your printed posters are kept in `labels/posters/`.

**Bonus pieces** (`bonus/`): the four sketches.
- `reel.html` (Film-Reel Jelly), `sewer.html` (Sentinel Timeworm), `medusae.html` (Afterlight Medusae), `worms.html` (Raw Doodle Worms).
- Each exposes `window.__bonus`. `bonus/bonus.js` then gives them real footage through the shared screens:
  - films named after the 109 secondhand titles play those films' own frames (102 match by title);
  - everything else plays one of the **145 cineosis clips the drifts have never used** (`bonus/footage.json`);
  - the worms' "raw doodles" are now the real traced secondhand drawings, cycling through their keys.
- As a film's footage clears, the sketch's stand-in (pixel plates, portals) fades out.
- **Sound:**
  - one VOLHOLLA song each: *The Fragile Iron Ghost*, *Phosphor Waveform Log*, *The Long Descent*, *The Wet Console*;
  - it fades in on the first touch and ducks while a film is held clear;
  - a glass ping and a burst of bubbles when a film clears, and a reel whir while it stays clear.
- H toggles cinema mode.
- three.js is now loaded from the repo (`bonus/vendor/three.r128.min.js`; `paeleo/.../three.module.min.js` for the worms), not from a CDN.

**The trailer** (`current/drift/play/trailer.mp4`): 73 s, 960×540, h264 yuv420p plus AAC, 5.3 MB. The last one was yuv444p, which is why it played as corrupted on phones.
- **Structure:** the printed title floods out of the jar into the water. Then each of the 11 generated films plays 4 beats and gives way to its drift's gameplay for 4 beats. The end card returns to the reel.
- **Transitions:** film→game is hidden under rising bubbles; game→next film opens through a radar ring.
- **One look:** a single grade, grain and vignette over both, so they read as one world.
- **Music:** *Saltwater Static (The Last Shanty)*, cut on its 95.7 bpm beat.

**Recordings** (`current/drift/play/*.mp4`, 960×540, 6 s): frame-stepped at 24 fps in trailer mode, with a shot list per drift (`rec3.js`: Lure's lunge, holds in Toward the Surface and Bloom, pulses in the dark levels).

**The back layer** in every game is black. It plays a film only while one is held or focused, or as an echo for about 2 s after a pulse, Echo, cast or drink.

## The water look (this round)
- **Index and jars:** the paper look is gone. Everything is dark water and thin light type (Jost).
  - The landing is a live WebGL jelly (`hero.js`) with a real film inside its bell.
  - Jars are glass drawn in light (`jar.js`), shared by the index, the drift landing's periodic table and the game's intro card.
  - The coloured cartoon jars (`labels/jars`) and the posters remain in `labels/` but are no longer shown.
- **Trailer:** gaussian-splat dissolves replace the bubbles, set to VOLHOLLA's *Stratospheric Void Crossing*. The title sequence (`title.js`) is three frames drawing in the water.
- **Trailer mode** (`?trailer`): eased, capped, drifting steering; longer holds; a looser camera; fewer scripted cues (see `SCION_VOID_INDEX.md`).

## Brand back, bigger table, the demo
- **Brand:** the CONTAMINANT wordmark (Anton) is back, small, above the light "jelly-films". Each section opens with a kicker in the same face, and a large outlined wordmark closes the page.
- **Jars:** the coloured jars return, each with its cartoon jelly or periodic symbol (`jarCard` in `jar.js`). The thin glass outlines now sit behind them as ghosts (1 → 2 → 3). The film and the game play in the label window.
- **The periodic table** is grouped under its sixteen types: each type's jar leads a row of its signs, at about 118 px each instead of a 16-column grid. The question reads in a strip pinned to the bottom of the screen. The drift landing uses the same layout.
- **The drift landing** is in the water style: thin type, the wordmark, live doodles drawn in thin light, jar shelves for the episodes and the eleven drifts, and a list for the subjects.
- **The demo:** `current/v2.html?demo` (The Rising Tube) pulls the camera back from inside the bell (5.4 behind instead of 3.4, looking up the tube), hides every word, starts itself, swims with a slow wandering hold, and pulses every 5 s. Its recording (`play/demo-v2.mp4`) opens the index right after the landing.
- **Newly linked:** VIDEOTEXT (`paeleo/scion/videotext/`); and, in the bolas repo, the Crash Lab process (18 cases, including *CINEOSIS in the crash lab*), the 108-shot cutout worms, and the SCION swarm operator.

## Three trailers, freer cameras, every version in a jar
**Titles** (`titles.html?t=jar|word|reel|outro`): drawn from a single clock, so they render frame by frame.
- **The Jar:** the landing's jelly swims into a specimen jar drawn in light. Film rises in the glass, the CONTAMINANT label settles, the wordmark glows in, and the camera pushes into the film.
- **The Wordmark:** CONTAMINANT in a 35 mm gate (sprockets, gate weave, flicker), its letters filled with moving film and edged in blue light. *jelly-films* spaces in, then the letters break into flecks.
- **The Reel:** a reel turns and a strip of live frames unspools from it, becoming the jelly's tentacle.

**Trailers** (`play/trailer-jar.mp4`, `trailer-wordmark.mp4`, `trailer-reel.mp4`):
| trailer | song | the first cut lands at | shots |
|---|---|---|---|
| The Jar | *Gospel Under Water* | the surge out of its quiet, about 52 s | the design videos and their drifts, the v2 demo, Medusae |
| The Wordmark | *Stratospheric Void Crossing* | where it comes back in, about 34 s | the song videos and their drifts, a sign level, the Sewer |
| The Reel | *The Long Descent (Memory Rot)* | its first full swell, about 31.6 s | every version, the archive levels, the Reel and Worms bonus pieces |

How the shots are chosen and cut:
- **Highlight windows:** every clip is scored frame by frame (motion, contrast, bright pictures). Each shot takes the best window, or the second-best when another trailer already used that clip, so no moment repeats across the trailers.
- **On the beat:** cuts fall every 4 beats, dissolving through gaussian splats.

**Cameras** (`current/flycam.js`): a camera layer over any piece's own camera.
- **Controls:** wheel or pinch pulls back, right-drag or two fingers orbit and tilt, Q/E · R/F · Z/X do the same from the keyboard, C recentres.
- **Speed:** moving fast, it lags, pulls back and widens.
- **Where:**
  - v2 is further back by default;
  - the four bonus sketches get the full open camera, no longer claustrophobic.
- **v2's wall** now deals films from a shuffled deck, so none repeats until all have been shown.

**Every version** has a jar on the index (v7 down to v1), filled with a frame-stepped recording of it swimming (`play/ver-v*.mp4`).

## The sea round: hunters, arms, the cutting room, the seas
See SCION_SEA.md. Hunters (sea.js) take arms, and with them clips; holding a film records a clip as long as the hold; eight arms at most, and a full jelly lets go of its weakest arm and swims heavy. The end of every level is a cutting room (editor.js): the verdict (WON / SURVIVED / LOST, three stars), the film on a monitor with a timeline you can recut and save, and the making-of recorded from the water. Three seas join each family's levels as regions: The Open Sea, The Lab Sea, The Archive Sea. A guide strip and edge arrows show films and hunters; the camera pulls back with speed and opens out when you are hunted.
