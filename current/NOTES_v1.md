# The Current: how it works

A jellyfish drifts down a tube of currents. Its arms catch frames of public-domain archive film and draw them up into its bell. The censor's red ink clings to the arms and clouds the bell; two fast pulses shake it off, and too much ends the run.

## Controls
- **Steer.** Hold (touch or mouse) where you want the crown to point, or use the arrow keys / WASD.
- **Pulse.** Tap, click or press space to swim the way the crown points. Pulses 0.5–1.1 s apart build rhythm, and rhythm swims further.
- **Shake off ink.** Two pulses less than 0.45 s apart throw off any ink the arms are holding.
- **Debug.** `?debug` shows nodes, grid checks, stretch residual and frame-time percentiles.

## The body (after *A Body Made of Strands*)
- **Bell.** A lathe of the moon jelly's profile, in two shells. Its contraction travels from the crown to the margin as a vertex wave, and the margin ripples. The fragment shader draws a fresnel rim, radial canals and Aurelia's four horseshoe gonads. The last frame caught glows faintly inside it.
- **Authority.** The bell is the one authoritative body: a position, a velocity and a heading in the tube's cross-section. The current carries it along the tube; pulses push it the way the crown points.
- **Strands.** 36 fringe tentacles (12 nodes each) hang from the contracting margin, and 4 oral arms (18 nodes each) hang from the centre of the subumbrella: 504 nodes in total. Every strand root is pinned to its sampled attachment point each tick, which is the attachment invariant.
- **Skin.** Strands are drawn as tubes swept along parallel-transported frames: 5 sides for the fringe, 10 for the arms, with a ruffled radius. They are shaded surfaces, not hairlines.

## The physics (after *Verlet Distance-Field Swarm Physics*)
- **Integration.** Rotation-free Verlet point masses in flat Float32Arrays (structure of arrays, current and previous positions), on a fixed 1/120 s tick. Up to 12 ticks run per frame, and the backlog is dropped after a long frame.
- **Forces.** Each node gets drag toward the water's own velocity (flow down the tube, fastest at the centre, plus a swirl and eddies) and a sink away from the crown. A node holding something sinks more.
- **Projection.** 10 Gauss-Seidel passes per tick over distance constraints. Traversal direction alternates each pass against order bias, and the root carries no weight.
  - A soft minimum span over two links keeps the arms from folding.
  - The bell's own volume pushes nodes out.
  - The tube's signed distance field, φ = R − |p − C(s)|, with s found by Newton steps along the centreline, keeps every node inside the tube. The same field keeps the bell and the camera inside it.
- **Catching.** A uniform spatial grid (cell 1.2 m, hashed) buckets the drifting items each frame. Each strand node checks only its 27 neighbouring cells. A frame a node touches attaches to that node, weighs the arm down, and after 0.9 s is reeled up the arm into the bell. Ink stays attached and clouds the bell until shaken off.

## Measured
Headless Chromium with software rendering, so these say nothing about frame rate on a real GPU.

| measure | result |
|---|---|
| chain stretch residual after projection | 0.4–3.5% |
| game CPU time per frame, p95 (plus draw submission) | 9–11 ms |
| 80 s scripted run at 640×360 (steering toward the nearest frame, shaking off ink) | 12 frames caught, 272 m drifted, no page errors |

At 1280×720 the software renderer reached only 5–14 fps, so the world ran slowly: rendering, not the physics, was the bottleneck there.

**Not measured:** GPU frame time on real hardware, and how it feels in the hand. No person has played it yet.

## Sources
- Jakobsen, *Advanced Character Physics* (2001)
- Müller et al., *Position Based Dynamics* (2007)
- Teschner et al., *Optimized Spatial Hashing for Collision Detection of Deformable Objects* (2003)
- Wang et al., *Computation of Rotation Minimizing Frames* (2008)
- The moon jellyfish (Aurelia) as anatomy

Visual references named in the brief: holtsetio's Aurelia, milcktoast's Medusae, fwdapps' Jellyfish Wrap. They were not viewed from this session (no network access to them); the bell, gonads and strand skin were built from the anatomy and the papers.
