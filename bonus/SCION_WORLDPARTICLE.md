# SCION SYSTEM INSTRUCTION: THE PARTICLE JELLY (a jellyfish for a learned simulator)

**The direction:** "We want to start up a new simulation of a jellyfish with https://github.com/WorldParticle/WorldParticle."

**Role.** Start a jellyfish in a *learned* physics. Until now every jelly here moved by hand-written rules:
- verlet tentacles;
- a bell that pulses on a beat.

WorldParticle learns how particles move from examples:
- **Its input:** positions, velocities, a topology graph, obstacles, and an external force.
- **Its output:** the next frame, from local continuous convolutions, merged super-particles and attention.

To start a jelly there, it needs **examples it can learn from and be judged against.**

## 1 · What was built
| piece | where | what it is |
|---|---|---|
| **The body** | `sim/worldparticle/jelly_sample.py` | A 12 cm moon jelly as 879 particles: a two-layer bell (exumbrella and subumbrella), 16 marginal tentacles and 4 oral arms, joined by 2,630 neighbour links, in a tank with a floor, walls and a lid. |
| **The ground truth** | the same file | Position-based dynamics, with distance constraints (a stiff bell, soft tentacles, bending along the chains), water drag, and collisions with the tank. |
| **The samples** | `DATA_ROOT/jelly_*/jelly_*.npz` | Three six-second takes (STRAIGHT, TURN, DRAG) in WorldParticle's `elastic_drag` layout. |
| **The config** | `sim/worldparticle/config_jelly.yaml` | WorldParticle's config, changed for this body's scale. |
| **The viewer** | `bonus/worldparticle.html` | The samples as gaussian splats in the tank. It lays a WorldParticle prediction over the simulation once one exists (via `pred_to_web.py`). |

## 2 · The one design decision: what counts as "force"
WorldParticle's physics step replaces gravity with the sample's `force`, a per-particle acceleration. So `force` must hold what is **outside** the elastic body:
- **buoyancy:** a slight net sink, since a jelly is nearly neutral;
- **the coronal muscle:** squeezing the lower bell toward its axis for 0.3 s of every second;
- **the jet's reaction:** along the bell's axis, only while it closes;
- **the pull:** in DRAG, on one tentacle tip.

**The model must learn the rest:**
- how the mesoglea springs back;
- how the tentacles trail;
- how water drag damps it all.

This also makes the muscle a **control input**: the same squeeze, fed to the model, is how a game would steer this jelly. The TURN sample is the first steering example, an uneven squeeze.

## 3 · Tested
- **WorldParticle's own loader** (`TrajDataset.load_npz_sample_by_data` for `elastic_drag`) reads all three samples, run with a numpy stand-in for torch because PyTorch is not installable on this machine. It classes them as obstacle, topology and force data. The topology is consistent: N + 1 row splits, all indices in range.
- **The simulation:**
  - **STRAIGHT:** the bell's rim closes by about 15% on each pulse and springs back. The body rises about 45 cm in 6 s, drifting about 15 cm sideways (it is not perfectly symmetric).
  - **TURN:** the bell tips and the body is carried about 15 cm to one side.
  - **DRAG:** the pulled tentacle swings the whole body.
  - All values are finite.
- **The viewer** plays all three samples at 50 fps with no errors.

**Fixed along the way:**
- **The tentacles were too heavy:** the body sank. Their net sink is now small, since a jelly is nearly neutral.
- **The squeeze did nothing, then too much:** first the rim did not move, then the bell crumpled. Bell stiffness 0.9 with a 40 m/s² squeeze closes the rim about 15% and lets it spring back.
- **Jitter counted as thrust:** small jitter in the rim radius was being counted as thrust. The jet now pushes only during the squeeze, from a smoothed radius.
- **The tentacles started inside the floor**, which crumpled the bell. The jelly now starts higher, in a taller tank.

**Not done:** the model has not been run. It needs a CUDA GPU and a trained checkpoint, and **WorldParticle publishes neither a checkpoint nor a training script.**

## 4 · Next
- **Many more samples:** vary the pulse period, the squeeze's strength and bias, the pulls, and the bell's stiffness. That is a training set for elastic jellies.
- **Train, or obtain, a checkpoint;** roll out STRAIGHT, TURN and DRAG; lay them over the truth in the viewer.
- **Close the loop:** a game in which your finger is the muscle force, and the learned model answers.
