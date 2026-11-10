# SCION SYSTEM INSTRUCTION: THE COLLOQUY OF MOBILES (Pask, 1968, run as a machine and staged with jellies)

**The direction:** "Make this full sim here with jelly cinematic. Museum grade." The source is the monograph *Gordon Pask's The Colloquy of Mobiles (1968): System Architecture and Operational Theory*. It draws on:
- G. Pask, "A Comment, a Case History and a Plan", in J. Reichardt (ed.), *Cybernetics, Art and Ideas* (Studio Vista, 1971), pp. 76–99;
- P. Pangaro and TJ McLeish, "Colloquy of Mobiles 2018 Project" (AISB 2018);
- the ZKM Karlsruhe collection record (2021);
- T. Dreher, *History of Computer Art*, ch. II.3 (2013).

## What it is
The work hangs five mobiles from a truncated-triangle frame. Two "males", G and J, hang at the ends of bar Z. Three "females", F1–F3, hang near the outer vertices. Each mobile carries two drives, O (orange) and P (puce), and none can satisfy itself:
- A male is relieved only when a female turns his own beam back onto the right vane.
- She is relieved only by hearing that it worked.

The page runs that machine, as causally as the sources allow, and stages it in dark water. Each mobile is played by a jelly from the registry.

**Where:**
- `bonus/colloquy.html`: the page, with the UI, the director, the plates, the visitor's gestures and the PEO hook;
- `bonus/colloquy/sim.js`: the machine (pure, deterministic, no drawing);
- `bonus/colloquy/stage.js`: the staging;
- `bonus/colloquy/sound.js`: the sound, live and offline;
- `bonus/colloquy/colloquy-film.mp4`: the recorded film;
- `tests/colloquy/`: the tests and their JSON reports;
- the index's Bonus shelf.

## Mechanism → code
| Pask / monograph | in `sim.js` |
|---|---|
| Drives O, P in every agent; μ ← μ + δ while unmet | `step()`: `a.O += a.dO·tempo·dt` (capped at `Lcap`) |
| Satisfaction μ ← μ − ω | `closure()`: his wanted drive `−= omega` at F = 1; hers on consolidation |
| Four regimes (satisfied / O / P / dual) between L_min and L_max | `regime(O, P, Lmin, Lmax)` |
| Bar Z, 360°, carrying G and J | `S.z`; `malePos()` puts them at opposite ends, radius `GEOM.barR` |
| G, J turning 180° on their own axes | `m.phi` swings within ±90° |
| F1–F3 on bounded 90° arcs, with limit switches | `f.psi` within ±45°; a `limit` event reverses the motor |
| Lamp u, flashing, frequency-coded (identity, desire) | `m.lamp` at `flashHz` (×1.45 for P) |
| 1 scan → 2 optical contact on aperture a | `aligned()`, which tests both cones and a clear line; the female decodes for `decode` s, then accepts if her regime matches (`accepts`) or declines |
| 3 tone phase-locked to his flashes; short-term registration | female stage 3; the male hears it and goes to 3 |
| 4 energetic commitment: halt, Z halt, steady B, at a cost | male stage 4: `m.B`, his drive `+= kappa`, an `energetic` event |
| 5 mirror b swept within τ, from memory M_A / M_B or by search | `startSweep()` and `sweepStep()`. Memory goes first; an unrewarded memory **adapts** to search (inverted males) |
| 6 the reflection on vane C (O) or D (P): F = 1 | `b > .55` → C, `< −.55` → D, held for `close` s; `closure()` |
| 7 consolidate: she hears his tone while lit, writes UP/DOWN, both resume | female 6 → 7 after `closeHold`: her drive `−= omega`, `MA[id]` / `MB[id]` = the sign of b |
| Unreinforced τ, or a broken line, aborts to scanning | `abort()`: `timeout τ`, `line lost`, `occluded by visitor`, `occluded by male` (after `grace`) |
| Majority decision device for Z, weighted by drive | halt if Σ urgency(stages 2–6) ≥ Σ urgency(wanting); a `contention` event when both sides want something |
| Males occlude each other | `blocked()`: the other male's body is a circle in the line |
| Ambient light weakens the coupling (Pask 1971, p. 98) | `contrast(I) = I / (I + 0.55·ambient)`; the photocell fires with a probability that falls toward its threshold; detections integrate with a leak |
| Visitor as prosthetic male (torch) | `visitor.torch(fi, desire, s)`: she engages a partner `−2`, sweeps, and times out (there are no vanes to close) |
| Visitor as prosthetic female (mirror) | `visitor.mirror(mi, 'UP'/'DOWN', s)`: throws his B onto C or D → `closure(…, 'visitor mirror')` |
| Visitor occlusion | `visitor.stand(x, z, r)` / `leave()`: a body circle in every line test |
| Higher-order composition | `visitor.conduct({zBias, tempo})`: bar Z's speed and the tempo of every δ |

**INTERPRETATION (where the sources leave gaps, marked in the code):**
- For the regime table's gaps (one drive above L_min, the other below), the higher drive leads.
- The drives saturate at `Lcap`.
- "Majority" is weighted by the larger of each male's two drives.
- The contrast law and its numbers are this version's own.
- A watchdog at 3τ guards against any state the sources do not cover. In tests it has never fired.

## Cineulation: the live machine plays as cinema
The page has no separate cinematic layer. The simulation is the film:
- **The default view is cinema.** It is letterboxed and full-bleed, with darkness as the stage, as Pask required. The controls are hidden, and the captions sit in the lower bar (C turns them off).
- **Revealing the controls:** a tap on open water, the ◐ glyph, or any key brings them back. `?ui` starts with them showing. After 30 s unattended, the page falls back into cinema.
- **The visitor is always live.** In cinema, a press or drag near a female shines the torch on her: the pointer is the light. The director cuts to it on that frame.
- **The auto-director cuts only on machine events, in the frame in which the event happened.** The grammar:

| machine event | cut to |
|---|---|
| scanning, nothing engaged (refresh past max hold) | wide plan (Fig. 1A), side (Fig. 1B), orbit |
| contact (female → 2) | a two-shot along beam B, over his shoulder |
| phase-lock (→ 3) | a slow push in to mirror b, in profile |
| commitment (`energetic`) | bar Z from below, halting by majority |
| sweep (→ 5) | mirror b |
| F = 1 (`reinforce`): the satisfaction drop | his vanes C/D flaring |
| consolidate (→ 7) | a hold on her memory glow, in the colour of the drive |
| Z contention (when nothing is engaged) | bar Z |
| abort | side |
| lights up / down (`ambient`) | the wide plan, held while the room is lit |
| visitor: torch / stand in / mirror / conduct | over the stranger's shoulder / the visitor / the vanes / bar Z |

- **Holds:** a new story needs 1.8 s and the next beat of the same encounter 0.85 s. A visitor's act (a new torch, stepping in) cuts at once, because it is rare by construction. Past 9 s a shot is refreshed, again only on the next event. The director stays with the current encounter and does not jump to another pair mid-handshake.
- **Pacing:** to give the director room, registration (`register` 0.9 s), the held beam before the sweep (`commitHold` 1.0 s) and closure before consolidation (`closeHold` 1.0 s) are paced for the screen. This is marked INTERPRETATION.
- **Sound:** it starts on the first gesture, because browsers need one.
- **The film is a recording of this cineulation:** the same page, director and fixed 1/60 s machine clock, stepped at 24 fps by `COLLOQUY.film.frame()` (which calls the live `tick`). The recorded visitor comes in at 30 s with the torch and stands in a beam at 52 s for 12 s. The sound is rendered offline from the same run's trace.

## Critic round 1 → repairs (satisfaction must be visible and audible)
- **Brightness is need.**
  - Each bell is lit by its drive level: a dimmer on every rig material is scaled by (O + P)/2, and an identity-coloured halo follows the same value. Rising need brightens the bell.
  - A committed male (B on) burns brighter.
  - At F = 1, B goes out at once. The vane flares for 0.3 s, and the satisfied body falls dark, then is slowly relit by need (time constant 7 s).
  - The pair swing apart on their filaments.
  - Measured on rendered frames, 0.5 s after closure: 64–71% below the commit value.
- **The satisfaction chord.** At F = 1 a triad on his own pitch is struck over a quieter bed. Measured with EBU R128: momentary loudness +19 to +20 LU over the bed within 0.5 s of every F = 1, with a loudness range of 12.3 LU.
- **Identity colours** carried by each mobile's halo and filament: G red, J green, F1 blue, F2 violet, F3 pale gold.
- **The torch:**
  - It has its own cold white.
  - A stranger figure holds it.
  - The director cuts at once, over the stranger's shoulder (`stranger`).
  - The film's torch solicits F2.
- **Shot holds:**
  - Shots are refreshed on an event after 6 s. With no event for 8 s, the director cuts to an establishing shot; the log marks this cut "no event".
  - Beats of one encounter are at least 1.4 s apart, except the key beats (F = 1, consolidation), which need 0.9 s.
  - Cuts are hard; the camera does not ease between shots.
- **Bloom** is clamped (strength 0.55, threshold 0.74), and the beams are softer.
- **Bar Z** has a lamp strip: amber when halted by majority, teal when turning. The commit shot frames it close from below.
- **Darkness:**
  - An `ambient` event (lights up) cuts to the wide plan and holds the quiet room.
  - The film raises the gallery light from 57 to 67 s. No handshake completes while it is lit; the conversation resumes after.
  - Exhibition mode does the same every 6 minutes.
- **Pacing:** `commitHold` is 1.5 s and `closeHold` 1.6 s, so the director can show the commitment, the sweep, the satisfaction and the consolidation.

## Critic round 2 → repairs (nothing cuts away from satisfaction)
- **Protected satisfaction:**
  - Every F = 1 cuts at once to the **satisfied male** (`vane`), whichever pair it is, and that shot is protected for 1.5 s. The same pair's consolidation may take the slot (`memory`, also protected 1.5 s).
  - Every other event, the lights and the visitor included, is queued behind it. The strongest queued event is cut on the frame the protection ends; the log marks these cuts `deferred`.
  - After consolidation, a wider `tri` shot shows the pair swinging apart. The swing now decays slowly (time constant about 3 s).
  - The director does not cut away while a reflection is nearing a vane (|b| > 0.35 in the sweep).
  - A remembered sweep, which closes within about 1 s, no longer earns its own cut.
- **The end title** waits until no agent is in stages 4–7 and no shot is protected. The film is 88 s.
- **Holds:** with no live encounter, shots refresh after 4.5 s on any event (bar Z passing a 60° mark cuts to the bar). With no event at all, the director cuts to an establishing shot after 6 s. An out-and-back insert (A → B for under 2 s → A) is refused.
- **Bloom:** F3 (the cream Fleck Veil) has her halo and dimmer capped. The memory glow uses each female's own hue, so F1 stays blue. In the film, no frame has more than 1.7% of its pixels above 230.
- **Stranger shot:** the director picks the shoulder whose line of sight passes farthest from the males. On portrait screens, the stranger, mirror and two-shots look at the solicited female.
- **Darkness is audible:** the bed (tones, hum, buzz) is ducked by up to 15 dB while the room is lit. Measured dip: 14.5 LU.

## The staging
- **Cast** (`?cast=G:sentinel,J:celluloid,F1:glass,F2:medusa,F3:veil` is the default):
  - Each mobile is `createJelly(THREE, id, {puppet: true})`, hung on a filament.
  - The pacemakers run warmer with urgency and are quiescent when satisfied.
  - Stage events (contact, commitment, closure) fire the leading pacemaker, so each pulse comes from the machine.
- **Parts:**
  - lamp u flashes in orange or puce;
  - B is a soft volumetric cone, cut short by whatever stands in it;
  - mirror b is a bright facet that tilts;
  - the reflection lands high on C or low on D, and the vane flares at F = 1;
  - aperture a glows while engaged;
  - her tone ripples outward with each of his flashes;
  - display A shows his two drives as lit columns.
- **Camera:** the event grammar above. Portrait screens stand back from every shot.
- **Sound** (WebAudio, gentle, compressed, a little room):
  - each female's tone, gated by her partner's u (phase-locked);
  - a soft buzz under B;
  - his two-step satisfaction chirp at F = 1 (higher for C);
  - her two blips over a quiet satisfaction chord as she consolidates;
  - a low drive hum that brightens with the mean urgency.

## How to use
**Visitor modes (one finger):**
- **WATCH:** drag to look; the director returns after a pause.
- **TORCH:** tap a female.
- **MIRROR:** tap a male with B on. Tap above him for UP/C, below him for DOWN/D.
- **STAND IN:** tap the floor, drag to walk, tap yourself to leave.
- **CONDUCT:** drag sideways for bar Z, up and down for the tempo of desire.

**Plates:** LABEL (the wall label), STATE (the live machine-state plate), LEGEND (the notation; it also shows the labels on the machine and the drawing on the floor), LIGHT (gallery light, parameters, cast).

**Keys:**
- H cinema (hides all UI), L letterbox, E exhibition;
- S state, G legend, I label, M sound, V view;
- 1–5 visitor modes.

**URL:** `?seed= ?tempo= ?ambient= ?cast= ?ui ?noletter ?mute ?exhibit ?plates=label,state,legend ?low`.

**Exhibition** (E or `?exhibit`):
- The auto-director runs.
- The wall label and the state plate come and go.
- Every 2.5 minutes a ghost visitor uses one of the four modes in turn.
- The light is held dark.
- A lost WebGL context reloads the page.
- The logs are bounded.
- Picture quality adapts: the pixel ratio drops, then bloom goes off, and both return when the frame rate recovers.

**PEO hook** (`window.COLLOQUY`):
- `state`: the snapshot (per agent: O, P, regime, stage, B, F, lamp, b, tone, MA, MB, partner, τ timer);
- `params`: `{delta, deltas, omega, Lmin, Lmax, tau, ambient, zBias, seed, cast}`;
- `set({...})`;
- `setDelta(v[, id, 'O'|'P'])`;
- `setOmega`, `setLmin`, `setLmax`, `setTau`, `setAmbient`, `setCast`;
- `visitor.{torch, mirror, stand, leave, conduct}` and `invert(id)`;
- `shot()`, `mode()`, `cinema()`, `letterbox()`, `exhibit()`, `plate()`;
- `events(n)`, `director()`, `handshakesPerMinute()`;
- `step(s)` (the machine only), `soak(s)` (the machine plus exhibition), `tick(dt)` (one rendered frame).

## Invariants (tested)
- The regime table holds.
- A full handshake runs 1→2→3→4→5→6→7→1 for both partners, and F = 1 lowers the wanted drive by exactly ω.
- An unreinforced τ aborts at τ, and scanning resumes.
- After a write to M_A or M_B, the next sweep for that male and drive starts from that angle.
- Every Z contention is resolved by the weighted majority, and Z never moves while halted.
- More light gives fewer handshakes per minute.
- Each visitor mode produces its effect.
- Over 30 sim-minutes (three seeds, and on the page with the ghost visitor), no state is stuck and every agent is satisfied.
- A seed gives the same run every time.
- **Cineulation** (`@test` in `test_page.cjs`):
  - cinema is the default and every control is invisible;
  - the cut rate stays between 6 and 40 per minute (measured 19.7);
  - every cut is within one frame of a logged sim event, and no shot is shorter than 0.8 s;
  - every grammar shot occurs;
  - a press is the torch, and the director cuts to it;
  - a tap or a key reveals the controls;
  - the 390 px phone picture is uncovered.
  - Satisfaction is visible: the region brightness 0.5 s after F = 1 is at least 40% below the commit value.
  - Satisfaction is audible: an EBU R128 momentary peak at least 6 LU above the bed within 0.5 s of each F = 1.
  - **Every closure** in the recorded cineulation:
    - the satisfied male is framed, on screen, in a shot of at least 1.5 s;
    - his region is at least 40% darker within 0.5 s;
    - at most 5% of the frame's pixels clip.
  - No chord-level loudness peak occurs without an F = 1 near it.
  - The lit room is at least 8 LU quieter than the dark room.
  - No out-and-back inserts.
  - Deferred cuts land on the end of the protected shot.

**Run:**
- `node tests/colloquy/test_sim.mjs`
- `node tests/colloquy/test_page.cjs http://localhost:PORT <shotDir>`, with a static server at the repo root
- `node tests/colloquy/render_film.cjs http://localhost:PORT 84` (the film: the live page at seed 7, tempo 1.8)

## Not claimed
- The personas are Pask and Sonnabend's period satire, kept as historical labels.
- The mobiles' look is the jellies', not Sonnabend's fibreglass.
- The timings and the contrast law are tuned for a screen, not measured from the 1968 relays.

## Tribunal verdict (independent critics, frame- and audio-measured)

| Round | Build | Verdict | Largest gap → repair |
|---|---|---|---|
| 1 | 430f9ac | reference stronger | satisfaction invisible → brightness bound to drive, chord on F = 1 |
| 2 | 239f8a9 | reference stronger (narrow) | director cut away from satisfaction → protected 1.5 s closure shots |
| 3 | d2af83e | **hard proof PASS** | flare: 6–11% of agent pixels clip (F1 40.0 s, G 53.5 s, J/F3 75.25 s, F3 80.5 s); target < 5%. **Not repaired.** |

What round 3 measured:
- **Closures:** all five frame the satisfied male, who darkens 51–66% within 0.5 s, in a shot of at least 1.58 s.
- **Chords:** each closure has one, 7–12 LU above the bed, and no chord sounds without a closure.
- **Torch:** the director cut to the stranger live on both desktop and phone.
- **Lit room:** it measures 15–18 LU quieter, and the society resumes afterwards.

Known open issues, by critic 3:
- The flare above.
- The 40–52 s lull.
- The pair do not visibly part inside the closure shot.
- The lights rise inside the G closure shot at 57 s.
- The torch outcome is cut away from at 31.83 s.
- The torch colour is close to F3's white.
