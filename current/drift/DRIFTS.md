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
