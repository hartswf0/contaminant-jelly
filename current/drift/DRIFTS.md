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
