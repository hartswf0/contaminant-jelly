# The Branching Archive (The Current, sixth version)

Memory Maker · Timeworm. A small amber jellyfish of layered celluloid swims a branching film archive. It takes frames by casting at films as they resolve, grows one timeline arm per film, and chooses a current at each fork. It outruns an anglerfish that announces itself, and it surfaces at 590 m with a cut it can watch (as splats or a timeworm), shape and share.

**Documents for this version:**
- **Spec of record:** [riverbed_v6.json](riverbed_v6.json), the user's GOLDEN RIVERBED record.
- **As built:** [SCION_BRANCHING_ARCHIVE.md](SCION_BRANCHING_ARCHIVE.md): the invariants, the control surface, the title, the reticle, sound layers, haptics.
- **Theory of play:** [SCION_LUDIC_BRANCHING_ARCHIVE.md](SCION_LUDIC_BRANCHING_ARCHIVE.md).
- **Songs:** [SONG2GAME.md](SONG2GAME.md), with `audio/song2game.json` and `audio/song2video.py`.

Earlier: [v5](v5.html) ([notes](NOTES_v5.md)), [v4](v4.html), [v3](v3.html).

## The loop this time: video2game + song2game
1. **Source.** The user's riverbed JSON. It is stored as-is and governs the build.
2. **Listening.** All 56 VOLHOLLA songs were fetched from the moto repository and analysed offline (`music.json` → `an`):
   - tempo and beat phase from spectral flux;
   - a 4 Hz energy envelope;
   - spectral centroid;
   - a 48-band spectrogram strip per song (`audio/spec/`, sheet: `audio/spectrograms_picks.jpg`).
3. **Song2game.** An agent read the spectrograms and assigned one song per level, each with a start and end on a beat:

| level | song | start |
|---|---|---|
| landing | *Preparation & Drift* | 0.3 s |
| entry | *Stay in the Current* | 0.3 s |
| Lantern Grotto | *Tizita* | 0.4 s |
| Ray Run | *Command Decent* | 58.4 s |
| rejoin | *Silt Bench* | 75.9 s |
| Silt Pocket | *Ritual of the Ash and Silt (1)* | 3.0 s |
| the strike | *Ritual (2)* | 78.1 s |
| Interference | *Heart Is Stone* | 156.2 s |
| the deep | *Gospel Under Water* | 0.0 s |
| the surface | *Go Home and Be Free* | 10.9 s |

   It also matched the earlier design videos to songs (design_v5 ↔ *Steel & Static* at 83 s), wrote a Directorial Gardener treatment and a video prompt for each of the 26 songs, and wrote `song2video.py` to render them.
4. **Design videos.**
   - `fal/design_v6_720.mp4`, from the riverbed's laws. It shows a small low jelly, a huge face and hand beside it, twin mouths, an angler in a round passage, and water brightening toward a surface.
   - **Seven song videos** (`fal/song_*.mp4`, sheet `fal/songs_sheet.jpg`) before the fal balance ran out again. Three of them drew framed photo cards or red rectangles despite the prompt's law. Treat them as mood references, not as targets.
5. **What the design video changed:** a larger first screening (a face beside a small jelly), and water that pales toward the surface.

## What changed from v5, and why
| riverbed rule / ask | built |
|---|---|
| Jelly small; bell 12–18% of the short side | Camera distance is derived from the bell's width and the viewport. Measured 14–15% in ordinary play on desktop and phone, about 10% during the ray crossing (the spec allows wider framing there) |
| Level trailing camera; Look returns along the same arc | `camera.up` is the passage normal. Look arcs ≤ 35° at a fixed rate, by hold, Q / E, V or a two-finger side slide |
| Proportional drag steering; screen-right is right | The drag vector is projected through the camera axes. Measured: with Look held, screen-right input moved the jelly along camera-right (+0.11 m in the test window) |
| Wall slide | Outward velocity is removed at the wall. Measured: the jelly holds at the boundary, and the outward velocity drops to 0 |
| "The tube gets in the way" | Walls are additive outlines (rings, plankton, the spectrogram trace) and can no longer black out a film |
| Real forks | Two passages per fork with different currents, films, animals and music. The commit happens only after the throat; the far passage is hidden after the commit; each fork rejoins at a ⊕ eddy. The Chart offers "Return to the last fork" |
| One film, one arm, source order | Verified: `giraffe: [14,15,17,20,27,29,30,34]`, `cat: [15,16,18,22,23,25,26]` (frames sorted regardless of capture order) |
| Films resolve before they can be gathered; better reticles | Far clouds drift as flecks and close in as a picture; the reticle ring closes; the label goes from RESOLVING to CAST READY, with title, timestamp and arm count |
| Videos behave like fluid | Flecks are advected by flow noise, more so when far, and the swimmer's wake pushes and swirls nearby flecks |
| A clearer jellyfish of celluloid | Three nested sheets (amber, honey, pale celluloid) with sprocket perforations and frame lines, contracting one after another. The film you last took lights the bell. The silt is cold, fine and dim, so the jelly cannot be mistaken for it |
| Creatures change the water | Comb jellies (rainbow combs; touch for Long Reach). Shrimp (scatter and kick silt; the early cue of the angler). The ray (its wake pulls you and the silt: Slipstream). The anglerfish (bulk revealed by the silt it shoves). Interference fragments (orbiting red warning ticks, broken frame order) |
| Predators announce; banked work is safe | patrol → warn (two cold pulses) → turn → chase ≤ 3.2 s → patrol. The escape eddy stops it. A bite costs membrane (35), never frames |
| How long, how many | A dive is 3–5 minutes. The surface reports frames, films, time, membrane and echoes on the beat. Membrane damage and eddy repair are a stake; a torn membrane surfaces early with every frame kept |
| Powerups | Lantern motes (16 on the route) charge the Lantern, which reveals dark reels and the angler. Long Reach (8 → 14 m). Slipstream (+4 m/s). Echo (22 m, or 40 m on the beat) |
| Onboarding, tutorial, title | The landing is four operations and four buttons. The particle title condenses, is punched with sprocket holes, breathes with the music and parts around a swimming jelly. The tutorial teaches steer, Look, Focus, Cast and fork, each advancing when done |
| Audio through the experience | Layers far, mid and near. Creatures sit in HRTF space. Focus quiets the water. Each level has its own song, switched on a downbeat. The bell strokes on the beat. Splats brighten on beats. Screening cuts land on beats. The walls carry the spectrogram of what you heard. The Chart draws the route as thick as the sound was loud. The Pause menu has *Gospel Under Water*, *Stay in the Current*, *Preparation & Drift* or water only |
| Haptics on mobile | Patterns for wall, commit, capture, lure pulse, chase, bite, interference, on-beat echo and surface (Android Chrome; iOS Safari has no vibration API) |
| Multiplayer (optional) | Room link, seeded world, ghost jellies; each capture is claimed once (the earliest claim wins); Cast at a partner to share a frame; departure removes nothing |
| Screening | Splats or timeworm (the format switch keeps the playhead). Optical match: the first frame flies from its arm into the screening. Shape the cut with ↑ ↓ ✕. Save as an EDL. A share link opens the cut directly in the Screening Room |

## Measured
Headless Chromium, software GL, five films served locally, seed 7. The music and PeerJS hosts are blocked in this sandbox, so the beat sync ran on live-onset fallback with no songs.

| check | result |
|---|---|
| route left (Grotto), 640×360 | commits after the throat; 15 frames, 2 arms in source order; no page errors |
| route right (Ray Run), 640×360 | commits; 5 frames, 2 arms; bell 14–15%; no page errors |
| Silt Pocket, desktop and 390×760 touch | patrol → warn → turn; in the eddy the chase ends; no page errors |
| surface | Screening Room opens; splats → timeworm keeps playing; the cut link reopens the same 3 frames |
| arm tips leaving the frame | 0 in every sample |

**Not verified:**
- the songs actually playing, decoding and syncing in a browser (github.io was unreachable here);
- PeerJS across devices;
- real GPUs and phones;
- physical pinch;
- haptics on hardware;
- how it feels in the hand.

No person has played it yet. The remaining 19 song videos need fal credit: `FAL_KEY=… python3 audio/song2video.py` resumes and skips videos already on disk.
