# The Current (fourth version): never a frame

A golden jellyfish of light swims a drowned tunnel. Films drift toward it as **clouds of gaussian light**. Drink one and it pours into the bell, and a tentacle becomes a **time worm** that carries the film down its length. Press **Watch** and what you carry **blooms** in the dark in front of you, legible, still with no edge.

Rule for this version: [SCION_NEVER_A_FRAME.md](SCION_NEVER_A_FRAME.md). Page: [v4.html](v4.html). Earlier versions: [v3](v3.html) ([notes](NOTES_v3.md)), [v2](v2.html), [v1](v1.html).

## The video-to-game loop, restarted
1. **Design video.** A new fal design video, `fal/design_v4_720.mp4`, with its sheet `fal/design_v4_sheet.jpg`. It shows a golden particle jellyfish in a foggy sewer; films as soft oval clouds, often in pairs; tentacles turning white once they carry; red corrupted smudges; a dark teal palette.
2. **Study.** Read off the sheet:
   - clouds are soft-edged, oval and glowing, never rectangles;
   - the creature is small against them;
   - worms whiten when full;
   - corruption is red grain.
3. **Spec.** The SCION instruction above.
4. **Build.** One shared splat material reads a float parameter texture (`texelFetch`). Every point samples its frame from the atlas in the vertex shader.
5. **Playtest by script, then fix by looking:**

| what the screenshots showed | fix |
|---|---|
| No clouds visible at all | Splats were about 0.6 px. Each point is now sized by its cloud's density, `spread·√(3π/N)`, with a true projection scale. |
| A bright square inside the bell | A pouring cloud converged on one point. The falloff now reaches zero at the sprite edge, and the pour target is scattered through the bell. |
| The watched film was snow | The luminance depth lift changed perspective scale. The lateral spread is now counter-scaled by depth. |
| Pale, flat field; images burned white | The walls were lit at linear 0.035, which shows as #364845. Walls are now darker than the fog, and the bloom threshold is 0.72. |
| Picture still noisy | Softness parameter: larger, fainter splats in the bloom, with partial true colour and a contrast curve. |
| The bloom took 8 s to open | It ran on slowed game time. It now runs on a real-time clock. |
| A red cloud filled the phone screen | Near-lens fade from 0.9 to 2.6 m. |

## Controls
- **Point to steer** (on rails). Tap, click or space to dash. Arrow keys or WASD also work.
- **Watch:** Enter, E or the button. Tap to go to the next clip; Escape to leave.
- **Save reel:** EDL download.

## Measured
Headless Chromium, software GL, five films served locally.

| measure | result |
|---|---|
| 30 s scripted run, 640×360 | 10–16 films drunk, 8 worms carrying, no page errors |
| 30 s scripted run, 390×844 touch | 8 drunk, bloom opens, no page errors |
| splats | 66k in clouds and worms, plus 48k in the bloom, plus a 4.2k bell |
| tentacle stretch | about 2% |
| frame time p95, CPU side | 2–4 ms |

Still images from the bloom were compared with their source frames:
- the giraffe shot reads as sky, treeline and grass;
- the bicycle wheel and the butterfly's wings read.

**Not measured:** real GPUs, all 109 films from github.io, and how it feels in the hand. No person has played it yet.
