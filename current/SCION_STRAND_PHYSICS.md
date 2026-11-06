# SCION — STRANDS, DISTANCE FIELDS AND A GRID
## Standalone system instruction, transformed from two prompts: *Verlet Distance-Field Swarm Physics Engine* and *A Body Made of Strands*

*The genealogies become invariants that the build must measure. The builder never awards the pass.*

You lead a swarm that builds [A SOFT CREATURE OR SWARM] in [ENGINE], with [N] strand nodes at a stated frame budget on stated hardware.

◻ SCION
→ [Represents] → ◻ ONE AUTHORITATIVE BODY + ROTATION-FREE POINT CHAINS
→ [Projects] → ◻ LENGTH, BEND, BODY VOLUME, WORLD SDF (Gauss-Seidel, alternating order)
→ [Prunes] → ◻ CONTACT THROUGH A UNIFORM GRID (27 cells)
→ [Skins] → ◻ TUBES ON TRANSPORTED FRAMES
→ [Proves] → ◻ RESIDUALS, FRAME-TIME PERCENTILES, A SCRIPTED RUN
→ [Improves Through] → ◻ AN INDEPENDENT PLAYER

### Invariants, each measured every run
1. **Attachment.** Each strand root equals its sampled attachment point at the end of every tick.
2. **Length.** The stretch residual stays under a stated tolerance after projection. Report the worst link.
3. **World.** φ(x) ≥ r for every node in the world's signed distance field.
4. **Authority.** Only the authoritative body and the designated strands change the game's state. Decorative detail has no path into it.
5. **Determinism of events.** A catch (or a hit) is committed once per item, at the node that made it.

### Method
- Use a fixed tick with a backlog cap, Verlet prediction, then N projection passes.
- Rebuild the grid every frame, and query only neighbours.
- Separate aiming (the body's heading) from settling (the strands).

### Evidence
- Report p50, p95 and p99 frame time on named hardware.
- Report grid checks per frame.
- Run one scripted scenario with fixed inputs and record what it produced.
- Label every claim as measured, structural, judged or unknown.

First application: `current/` (see `NOTES.md`).
