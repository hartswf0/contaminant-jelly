# SCION SYSTEM INSTRUCTION: RIGS (the characters)

**Role.** A species is a different animal on screen: a different rig, a different body. Show every jellyfish the project has built, and let the player choose one at the start, as in a character select.

**The direction:**
- "species means the actual jellyfish is different, like in current vs ascent: the rig and character used"
- "how many of them look different? find those and show them"
- "like choosing your character at the beginning"
- "I know in bonus each one is different"

## 0 · The audit: how many jellies look different
Every version's jelly was traced to its source. Ten are distinct; two pairs turned out to be the same body.

| # | character | source | how it is built |
|---|---|---|---|
| 1 | The Glass Moon | v1 · The Current | a lathe of the moon jelly's profile (solid glass); radial canals and four horseshoe gonads in the shader; oral arms |
| 2 | The Film Bell | v2 · The Rising Tube | 3,400 particles that *are* the film you caught last, playing, inside a fresnel lathe shell |
| 3 | The Sewer Creature | v3 · The Sewers | a prolate mantle of 5,200 golden particles; 22% form an inner nervous system that glows |
| 4 | The Golden Splat | v4 · Never a Frame · **v5** · The Dive | 4,200 gold splats. v5 is the same bell with a two-tone uniform (and blue ghosts) |
| 5 | The Celluloid | **v6** · The Branching Archive · **v7** · The Drifts | three amber celluloid sheets with sprocket holes and frame lines, contracting in turn. The drifts used this one for every level |
| 6 | The Fleck Veil | the landing (hero.js) | 24,000 blue flecks, a perforated film band at the rim, a real frame inside, one film-strip tentacle and three filaments |
| 7 | The Film-Reel Jelly | bonus · Film-Reel Jelly | an iridescent fresnel veil with 16 canals, gonads and a sprocketed margin; 35 mm film-strip tentacles with gold splices |
| 8 | The Sentinel | bonus · Sentinel Timeworm | an armoured carapace with two rings of eyes, dissolving to gold; segmented timeworm tentacles with vertebral rings |
| 9 | The Afterlight Medusa | bonus · Afterlight Medusae | a compact golden medusa with 16 ribs; 12 hanging tentacles that light silver, one per film held |
| 10 | The Doodle Jelly | bonus · Raw Doodle Worms | 18 hand-drawn rib strokes (gold and cyan) and 5 sketch rings; a drawing in the crown; 12 raw doodle tentacles |

## 1 · One module, kept as made (`rigs.js`)
**The interface:**
- `makeRig(THREE, id)` returns `{group, norm, update(s), setFilm(texture), dispose}`.
- `s` carries the pulse phase, time, glow, hurt, point scale and the number of arms held.

**Porting rules:**
- The **geometry and shaders are ported from their sources**: the lathes, the particle constructions, the GLSL, the colour presets.
- Every bell is put on the same contraction rhythm and the same scale (a crown-up bell of about 0.9 radius).
- **The bonus pieces' verlet simulations are not ported.** Their tentacles are ribbons and lines that sway, carrying the original strip and timeworm shaders.

**The rigs respond to the game:**
- The Glass Moon, the Film Bell, the Fleck Veil and the Doodle Jelly show the film you took last, inside the bell.
- The Medusa lights one tentacle per arm held. The Doodle Jelly brightens one doodle tentacle per arm held.
- Hurt tints the bell.

The game's own film arms (the clips you hold) are still drawn by the engine beneath any rig.

## 2 · Choosing (character select)
**`characters.html`:** the chosen jelly large in dark water, turning slowly with bloom.
- It shows the jelly's number, name, source, a line on how it was built, and its traits.
- Change the jelly with ‹ ›, a swipe, the arrow keys or the names.
- "Swim as this jelly" saves the choice (`cj-rig`) and returns to `?next`.

**The drift landing:**
- A new **00 · Choose your jelly** shelf shows all ten as thumbnails (`labels/rigs/`); yours is ringed in amber.
- "Start swimming" now goes through the character select first, then to chapter 1.

**Every level's card** ends with a **YOUR JELLY** row:
- tap a name and the jelly behind the card changes on the spot;
- "see them all →" opens the select and returns to the level;
- `?rig=<id>` overrides the choice for a single visit.

The species (chapter, verb, body) stays with the level. The rig is the player's: a lion's mane level can be swum as the Sentinel.
