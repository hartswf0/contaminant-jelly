# SCION SYSTEM INSTRUCTION: THE BRANCHING ARCHIVE (v6, as built)

**Role.** You build and referee one dive through a living film archive. The swimmer carries film as anatomy, reads currents and light, takes frames by contact, and surfaces with a cut it can watch, shape and share.

**Origin.**
- `riverbed_v6.json` (the user's GOLDEN RIVERBED record) is the spec of record.
- The theory of play is in `SCION_LUDIC_BRANCHING_ARCHIVE.md`. Its song names are provisional: the level songs used in play come from `audio/song2game.json` (see `SONG2GAME.md`).
- `SCION_NEVER_A_FRAME.md` still holds.

## Invariants (checked by script, see NOTES.md)
1. **Scale.** The bell is 12–18% of the short side of the viewport in ordinary play. The camera distance is derived from it, not chosen: `d = bellWidth / (0.15 · zoom · vis)`, and pinch or scroll changes `zoom` only within 0.8–1.2.
2. **Level camera.** `camera.up` is the passage's normal every frame, so the horizon does not roll.
   - Look arcs at most 35° (0.61 rad).
   - It moves out and back at the same rate, 1.6 per second.
   - The camera is clamped inside its passage.
3. **Steering in screen terms.** Drag input is projected through the camera's right and up vectors into the cross-section, so screen-right is right in every pose. Input has an 8 px dead zone and is full at 16% of the short side. Release returns to drift.
4. **Walls.** The swimmer is projected onto the wall and loses only its outward velocity, so it slides along and can steer away. Walls are additive light: they can never hide a film.
5. **Forks.** A branch commits only when the two passages have separated (`offset ≥ 0.98 r`).
   - Before that, both mouths are visible.
   - Both mouths carry a preview film and an ecological cue: the ray in Ray Run, comb jellies in Lantern Grotto, silt in the Silt Pocket, red marks in Interference.
   - After the commit, the other passage's contents are hidden.
   - Every fork rejoins downstream at a marked ⊕ eddy.
6. **One film, one arm.**
   - A capture records `{film, frame, timestamp, cid}`.
   - A new film unfurls a new arm; a known film lengthens its arm (4 + 3 nodes per frame) and its frames are re-sorted into source order.
   - The oldest arms sink deeper into the wake.
   - A duplicate frame is refused.
7. **Provenance.**
   - The reticle label shows the title and timestamp from first approach.
   - The capture message, the arm, the cut, the Screening Room list, the saved EDL and the share link all carry `film · frame · timestamp`.
8. **Predators announce.** The angler's sequence is patrol, then warn (two cold lure pulses, shrimp scatter, the body resolves), then turn, then chase (at most 3.2 s, bounded to the pocket). The escape eddy stops the chase. A bite costs membrane, never banked frames.
9. **A clear end.** The current slows toward the surface but always reaches it.
   - At 590 m, propulsion stops and the camera settles to a side view. The Screening Room then shows the route, frames, time, membrane and echoes, with Watch / Format / Shape / Save / Share / Swim again / Leave.
   - A torn membrane or "Surface now" ends the dive early with every frame kept.
10. **Co-op is optional and refereed.**
    - A room seeds the world.
    - Each capture is claimed once, and the earliest claim wins on every client.
    - Casting at a partner gifts your latest frame.
    - A partner leaving removes nothing.

## Control surface (Operational Pragmatist): words are buttons
| you do | it happens |
|---|---|
| Drag in the water | the jelly swims that way on screen; let go and it drifts |
| Tap **Cast** when the ring closes | the frame the film is showing joins that film's arm |
| Hold **Focus** | the water slows to 30%, the nearest film sharpens, the sound clears |
| Hold **Look**, or slide two fingers sideways, or Q / E | the camera arcs up to 35° to the side and comes back on release |
| Tap **Echo** on the beat | the ping reaches 40 m instead of 22 m and marks films and motes on the map |
| Tap **Lantern** after collecting a mote | for 7 s, dark reels show themselves and the angler is lit |
| Tap **Watch film** | the nearby film opens at the moment it was showing; Back returns you to the same place |
| Tap the edge map or **Chart** | the world waits; you see explored passages, your route and the rejoins; tap a passage name to steer toward it |
| Swim into a comb jelly | Long Reach: cast range 8 → 14 m for 20 s |
| Swim behind the ray | Slipstream: +4 m/s for 3 s |
| Enter a ⊕ eddy | membrane +45, once per eddy |

The landing copy is four numbered operations and four buttons (Dive, Dive no lessons, Dive together, Sound on). The tutorial teaches one verb at a time in the entry reach. Each step advances when its action is done, or when the swimmer passes the place where it is needed.

## Title (after Paula Scher): the structural artifact
- **Container.** A strip of perforated film stock. The title letters are punched with sprocket holes: every third column of every fourth row is removed.
- **Type engine.** "THE BRANCHING ARCHIVE" is set flush left in a heavy grotesque, then rebuilt as flecks.
  - Each letter has a width axis that breathes with the music's energy (`1 + 0.04 sin + 0.22 · energy`).
  - The flecks condense over 2.6 s, like a film resolving.
  - A small jelly of flecks swims through the letters and parts them.
  - On Dive, the letters scatter into the current.
- **Analog seed.** The grain is the archive's own footage; the warm palette is the jelly's three celluloid sheets.
- **Locked zones.** A kicker line, the title block sized to fit above the copy, four operations, and one button row. Amber is for the swimmer, cyan only for co-op, red only for damage.

## Reticle (interface designer, six principles)
- **Surface the invisible.** A ring of flecks closes as the film resolves. It reads RESOLVING, then CAST READY, with the title, timestamp and the arm's current frame count.
- **Cognitive limits.** One target at a time: the nearest film ahead within reach + 6 m.
- **Multiple modes.** Swim, Focus, Watch film, Screening (splats or timeworm).
- **Direct manipulation.** The ring reacts to distance continuously.
- **Semantic zoom.** Edge map (this reach and the next decision) ↔ Chart (the whole archive).
- **Constrained play.** Casting early only reaches; nothing is lost.

## Sound in layers
- **Far.** 36 and 54.5 Hz pressure tones that deepen with depth.
- **Mid.** Brown-noise water whose cutoff and level follow your speed (louder in a slipstream). It ducks to 35% when you Focus or watch.
- **Near, placed in space with HRTF panners:**
  - comb-jelly glass chimes
  - snapping-shrimp crackle
  - the ray's slow wingbeat swell
  - the angler's 41 Hz drone and its two-pulse ping
  - a projector whisper at the nearest film
- **Music.** The user's songs, one per level from `song2game.json`. Each starts at its chosen offset, loops its chosen section, and switches about two beats after the next downbeat. It plays through an underwater low-pass that darkens with depth and opens for Focus, Watch and the surface.
- **Sync.**
  - The bell's stroke phase-locks to the playing song's offline beat grid.
  - Splats brighten slightly on each beat.
  - The Screening Room cuts land on the beat: two beats per frame.
  - Echo rewards pinging on the beat.
  - The spectrum heard along the way is written onto the walls behind you (angle = pitch, distance = time), and the Chart draws your route as thick as the sound was loud.

## Haptics (where the browser allows; iOS Safari has none)
| event | vibration pattern (ms) |
|---|---|
| wall | 5 |
| commit | 14 |
| new arm | 8-24-8-24-14 |
| frame added to an arm | 8-20-10 |
| lure pulse | 16 |
| chase | 30-30-30 |
| bite | 60-40-120 |
| interference | 20-20-40 |
| on-beat echo | 8-30-8-30-8 |
| surface | 30-60-30 |

The Pause menu turns haptics off.

## Failure regime
- **Visual noise before control.** Prove the camera and steering in a sparse tube first. This build was tested with the invariants above before ecology was tuned.
- **The tube as an occluder.** Opaque walls painted black over films. Fixed: walls are additive.
- **The end that never comes.** The surface current once slowed almost to zero before the threshold. Fixed: it floors at about 1 m/s.
- **Comments that eat code.** A trailing `//` comment on a one-line function deleted its body and stopped the page from booting. Syntax-check the module after every edit.
