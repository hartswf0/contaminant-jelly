# SCION SYSTEM INSTRUCTION: THE JELLY LAB (every jelly in one water, real, filmable, playable)

**The direction:**

> "Make all real jellies in the lab and we can inspect or hide all controls for cinema, more camera speed controls, orchestration, and totally hideable and tuneable. And lights can be programmed in John Whitney style curves to music … with the jellyfish beautiful simulations, think feeling real jelly, and with better ability to play in all other games."

It was followed by:

> "Make the art jellies each a thinking real jelly of its own unique species and improve all bells for better video playback."

**Where:**

| file | what it is |
|---|---|
| `bonus/jellylab.html` | the lab |
| `bonus/jellies.js` | the registry: every jelly, one interface |
| `bonus/species.js` | the ten species |
| `bonus/whitney.js` | the light organ |
| `bonus/film.js` | film in the bell |
| `bonus/lab-testcard.mp4` | a test film and fallback |

The lab is on the index's Bonus shelf. The Real Jelly page links to it ("JELLY LAB →"), and the drift games can carry any of these jellies.

## 1 · Every jelly, one interface (`jellies.js`)

`createJelly(THREE, id, opts)` returns a jelly that is a drop-in for a rig: `group`, `norm`, `update(s)`, `setFilm(tex)`, `dispose()` and `tentacles`. Every game that called `makeRig` can take it unchanged. On top of that it has:

| call | what it does |
|---|---|
| `pulse(k)` | Beat now. A real or species jelly fires its leading pacemaker. The nerve ring may refuse while it is refractory, as a real one would. |
| `setLook({view, glow})` | Change the view or the glow. |
| `views` | `flesh`, `nerves`, `muscle`, `strain`, where the animal has them. |
| `controls` | Its own live controls, which the lab's inspector renders. |
| `onBeat(fn)` | Called on each beat. |
| `state()` | Beat time, rate, centre of mass, kind. |
| `puppet` | When true, a game carries it: it beats and bends in place. |

`update(s)` takes the rig's argument (`{t, dt, ph, glow, cam, scale}`). It also reads `s.light`, which the jelly swims to, and `s.drive`. With `drive` true the jelly beats on its own nerve. Without it, a caller's phase wrapping to 0 stimulates the leading pacemaker, so a game's beat becomes a nerve impulse.

**The causally real animals** are ported from `realjelly.html`, one instance per call. They are built from the soft body in `jellyjar-sim.js` and the nerve ring in `thinkjelly-sim.js`:

- **The Real Jelly**: eight pacemakers, the coronal muscle (up to 46% shorter) and the radial muscle (4%), the spring of the gel, the water's push and the free second push of the recoil, the balance stones, rim eyes that turn it toward the lamp, 24 tentacles, 4 oral arms, and visible vortex rings.
- **The Thinking Jelly**: the same animal opened up, with strain and nerves on view.
- **The Jelly Jar**: the gel resting in its jar, wobbling when it is beaten.

Their controls are the source pages' own: FIRE, SILENCE, CUT THE RING, INTACT, ONE PACEMAKER, TRAPPED WAVE, cold–warm and soft–firm.

## 2 · Ten species, each a thinking jelly (`species.js`)

Each art rig keeps its look, its line and its traits. Each also runs the Thinking Jelly's real nervous system, `makeNerve` unabridged: pacemakers that charge and fire, a ring that conducts both ways and goes refractory, and a muscle that twitches where the signal passes.

The species parameters come from each body plan. The muscle's measured pull drives the rig's own pulse shape: the phase is read off the contraction, not off a clock. The bell's squeeze and rebound push it through the water. The rim's uneven pull turns it toward the light and upright.

**Honest note:** the ten rigs do not carry the full 2,000-tetrahedron soft body. Ten of those would not run at once on a phone. Their body is a lighter mechanical model: a damped spring per species that the muscle squeezes. The nervous system is the real one.

**The binomials and natural history are fictional.** They were made up for these films, to be consistent with each body plan.

| species (fictional binomial) | pacemakers | period s (spread) | ring round-trip s | refractory s | muscle | bell stiffness / damping | thrust | light · balance · touch | tentacles n×len | glow | how it thinks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Glass Moon (*Aurelia vitrea*) | 8 | 2.3 (±9%) | 1.0 | .42 | .8 | 26 / 4 | 1.1 | 1.2 · .5 · .6 | 16×.8 | #ffd8a8 | near-equal pacemakers; the lead wanders |
| Film Bell (*Cinebolus mollis*) | 6 | 4.6 (±13%) | 1.8 | 1.1 | .55 | 9 / 2.2 | .55 | .5 · .4 · 1.2 | 0 | #ffe9c4 | a sluggish ring: the bell closes in a ripple |
| Sewer Creature (*Teuthomedusa cloacae*) | 4 | 1.25 (±3%) | .35 | .3 | 1.1 | 48 / 6 | 2.4 | .9 · .2 · 1.6 | 8×.6 | #ffc060 | fast, head-led, metronomic jets |
| Golden Splat (*Chrysosplatta aurea*) | 12 | 2.6 (±23%) | 1.2 | .5 | .75 | 22 / 3.5 | 1.0 | 1.0 · .6 · .8 | 12×.7 | #ffb84a | very unequal pacemakers: jazz rhythm |
| Celluloid (*Triplicata celluloidea*) | 8 × 3 rings | 2.4 (±8%) | .9 | .45 | .85 | 30 / 4 | 1.2 | 1.1 · .6 · .7 | 6×.9 | #ffcf70 | three linked rings, 0.18 s apart, one per sheet |
| Fleck Veil (*Velum frigidum*) | 16 | 3.4 (±15%) | 2.2 | .9 | .45 | 12 / 2.6 | .7 | .4 · .5 · 2.0 | 4×1.6 | #8fd0ff | weak pacemakers on a slow ring; a touch flinch rolls round |
| Film-Reel Jelly (*Bobina iridescens*) | 16 | 2.0 (±2%) | .7 | .4 | .9 | 34 / 4.5 | 1.3 | 1.3 · .7 · .6 | 8×1.4 | #7ff0e6 | tuned alike: steady as a projector |
| Sentinel (*Loricomedusa vigil*) | 8 | 3.8 (±5%) | 1.0 | 1.4 | 1.4 | 70 / 7 | 2.0 | 1.6 · 1.4 · .4 | 6×1.1 | #ffd27a | long refractory, stiff bell: few strong beats |
| Afterlight Medusa (*Lucifera memor*) | 12 | 2.8 (±10%) | 1.1 | .55 | .8 | 24 / 3.6 | 1.0 | 1.2 · .7 · 1.0 | 12×1.3 | #dfe8ff | one pacemaker per tentacle |
| Doodle Jelly (*Graphomedusa rudis*) | 6 | 2.2 (±18%), jittering | 1.3 | .5 | .9 | 20 / 3 | 1.1 | .9 · .4 · 1.1 | 12×.9 | #ffd070 | periods wander each beat: a hand-drawn rhythm |

The tentacle counts in the table are body-plan data shown on each species card. The rendered tentacles are the rigs' own.

## 3 · Film in the bell (`film.js`)

`filmTexture(THREE, src, {poster})` handles the video itself:

- **Colour and filtering:** sRGB colour space, linear filters, and no mipmaps.
- **Frame-accurate upload:** frames are uploaded with `requestVideoFrameCallback` where the browser has it.
- **Autoplay:** `muted` and `playsinline` are set so it can autoplay.
- **Fallback:** if play is refused or the file fails, it shows a still: the poster, or the first frame it decoded.
- **Video size:** it sets the video element's `width` and `height` from the decoded size before the first upload. three.js sizes the GPU texture from those attributes, and a bare `<video>` reports 0, which left the texture empty.

`bellWindow(THREE, rig)` gives every bell a readable window:

- a camera-facing panel inside the bell, with its height set to its width over the film's aspect, so the picture is never squashed;
- a dark backing, so the picture keeps its contrast against the glow, the bloom and the fog;
- fog and tone mapping turned off on the panel, and soft edges;
- it squeezes with the contraction.

`fitFilm` also patches the rigs' own film shaders, which only the Glass Moon, Film Bell, Fleck Veil and Doodle Jelly have, with aspect fit, gain and contrast. It does this at load, so `rigs.js` is not edited.

**Measured legibility.** The method:

1. Render each bell at 320×240 behind the bloom pass, with a black/white checker film and then its inverse.
2. Count the pixels that change by more than 24 levels. That is the area where the film can be read.
3. Compare the old `setFilm` with the new window.

| bell | old: mean diff / readable px | new: mean diff / readable px |
|---|---|---|
| Glass Moon | 2.14 / 2,078 | 2.97 / 3,551 |
| Film Bell | 1.75 / 1,392 | 2.93 / 1,630 |
| Sewer Creature | 0 / 0 | 0.22 / 385 |
| Golden Splat | 0 / 0 | 1.32 / 1,607 |
| Celluloid | 0 / 0 | 2.56 / 3,031 |
| Fleck Veil | 0.26 / 0 | 1.71 / 2,643 |
| Film-Reel Jelly | 0 / 0 | 2.59 / 3,213 |
| Sentinel | 0 / 0 | 2.11 / 2,518 |
| Afterlight Medusa | 0 / 0 | 2.08 / 2,444 |
| Doodle Jelly | 5.61 / 3,220 | 2.94 / 3,326 |

Six bells showed no film before; all ten show it now. The Sewer Creature's window stays small (385 px) because its body is a narrow prolate mantle.

The test film, `lab-testcard.mp4` at 320×240 and 24 fps, uploaded 32 frames in 2.5 s through `requestVideoFrameCallback` in headless Chromium, with `colorSpace` sRGB and mipmaps off.

## 4 · The lab (`jellylab.html`)

- **Specimens:** add any of the 13 jellies, several at once; remove any; each has a name tag. Tap a jelly or its tag to inspect it. The inspector shows the species card, its views, its own controls and its parameters.
- **Cinema:** H (or CINEMA) hides every control, label and chart. A small corner glyph fades out after 2.5 s, and tapping it brings the controls back. There are also LETTERBOX and CLEAN (no tags or music-box line). Every panel collapses on its own.
- **Camera:**
  - Modes: orbit, dolly, crane, track (follow a jelly), beneath, far and free. Free is drag-to-look.
  - Sliders: speed, easing, distance and lens.
  - An auto-cinematographer cuts on the followed jelly's own beat, or on any beat. It has a minimum hold and gives up waiting at 2.5× the hold.
  - The whole shot is in the URL: jellies, selection, camera, organ settings, song, cinema and letterbox. **COPY SHOT LINK** copies it.
- **Orchestra:**
  - Choose a song from `jellystudio/tracks.json`.
  - Its sounds are cast to jellies with the Jelly Orchestra's own CASTING (kick → Sentinel, snare → Celluloid, bass → Sewer Creature, and so on), and the cast can be edited.
  - Each onset stimulates that jelly's leading pacemaker, so the real nerve model fires on the music.
  - Every jelly shows its fired and refused counts; refusals are the refractory period at work.
  - Mute and solo work per jelly.
- **Whitney light organ:**
  - N lights, each a dot with a trail. Up to 4 of them are real point lights.
  - Paths: rose, Lissajous, epicycle or music box.
  - Speed: differential, ω_i = base·(i+1)·ratio + detune·i turns per bar, locked to the song's BPM.
  - RDTD-style radius and theta differentials.
  - Envelopes follow the bar.
  - In music-box mode, a light crossing the line strikes a note and pulses the nearest jelly.
  - Lights make nearby jellies glow.
  - Presets are named after the techniques: Permutations, Matrix, Arabesque, Music Box 1:n, and Drift (tension).
  - The organ cites John Whitney Sr.'s *Digital Harmony: On the Complementarity of Music and Visual Art* (1980) and the films *Permutations* (1968), *Matrix III* (1972) and *Arabesque* (1975). No quotations are used.
- **Picture:**
  - water haze, marine snow and light shafts, each switchable;
  - a phone-quality mode, set automatically on narrow screens, with a coarser gel, fewer lights and a lower pixel ratio;
  - a 30 fps cap;
  - adaptive pixel ratio when the frame rate falls below 28.

## 5 · In other games

`current/drift/engine.js` now offers the Real Jelly and the Thinking Jelly in its YOUR JELLY row, through `GAME_JELLIES` and `makeGameJelly`. Its art rigs are now the thinking species by default; `?classic=1` brings back the old clock-driven rigs.

Other pages adopt the same jellies by swapping one call:

```js
import {makeGameJelly} from '../../bonus/jellies.js';
const RIG = makeGameJelly(THREE, id);   // was: makeRig(THREE, id)
```

Nothing else needs to change, because the game's `RIG.update({t, dt, ph, …})` beat becomes a nerve impulse.

`rigs.js` itself is unchanged. The Jelly Orchestra, the jelly-cut renderer and the other pages that call `makeRig` keep the classic rigs until they opt in.

## Invariants (tested, headless Chromium with SwiftShader)

- **No page errors** in the lab with all 13 jellies, nor in the drift game with `rig=realjelly`, `rig=medusa`, `rig=celluloid` and `rig=sentinel&classic=1`. The game's only console errors are external fonts and media this sandbox cannot reach.
- **Cinema** leaves no visible control, tag or panel: 0 visible elements at 1280×720 and at 390×844.
- **Scroll:** 390 px wide gives no horizontal scroll (scrollWidth 390).
- **Whitney:** the measured angular speeds, from the dots' positions, are exactly 1, 2, 3 … 8 × the slowest in Music Box 1:n (0.1963 rad/s × n at 120 BPM). With detune they are the predicted 1, 2.176, 3.352, 4.528 (error < 1e-14).
- **Entrainment, deterministic:** 14 onsets per jelly at 60 fps. Every onset the nerve accepts fires its pacemaker on the same frame (lag 0 frames). Refusals come only from the refractory period:

  | jelly | accepted | refused |
  |---|---|---|
  | Real Jelly | 8 | 6 |
  | Thinking Jelly | 9 | 5 |
  | Sentinel | 9 | 5 |
  | Sewer Creature | 10 | 4 |
  | Celluloid | 12 | 2 |
  | Doodle Jelly | 10 | 4 |
  | Afterlight Medusa | 7 | 7 |

- **Entrainment, live song** ("Boxes On My Back", 20 s): each onset reached its jelly within one rendered frame (63–177 ms at SwiftShader's 6–16 fps).

## Limits

- The ten species use the lighter spring body, not the tetrahedral gel (see the honest note in §2).
- The Wet Bell page is an art piece built on the rigs, not a simulation, so it is not a separate specimen.
- On a phone, more than about 6 jellies plus the Real Jelly's gel will drop frames. Phone mode starts with 3.
- No one has listened to the lab's sound or the music-box notes; they are untested by ear.
