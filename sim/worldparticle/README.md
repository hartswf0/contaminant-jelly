# A moon jellyfish for WorldParticle

[WorldParticle](https://github.com/WorldParticle/WorldParticle) is a *learned* particle simulator.
- **Input:** the particles' positions and velocities, a topology graph, obstacles, and an external force.
- **Output:** the next frame, step after step.

This folder starts a jellyfish in its world:
- **`jelly_sample.py`:** simulates a 12 cm moon jelly as 879 particles and writes ground-truth samples in WorldParticle's `elastic_drag` NPZ layout.
  - **The body:** a two-layer bell, 16 marginal tentacles and 4 oral arms, joined by 2,630 neighbour links.
  - **The motion:** position-based dynamics with distance constraints, water drag, and a tank with a floor, walls and a lid.
- **`config_jelly.yaml`:** WorldParticle's config, changed for these samples: `data: elastic_drag`, `particle_radius: 0.0045`, `topology_search_radius: 0.015`, `frame_end: 600`.
- **`pred_to_web.py`:** turns a WorldParticle rollout into the browser viewer's format, so the prediction can be laid over the simulation.
- **The viewer:** [`bonus/worldparticle.html`](../../bonus/worldparticle.html).

## The samples
| sample | what happens |
|---|---|
| `jelly_straight` | Six symmetric pulses. The rim squeezes for 0.3 s each second, the bell springs back, and the body rows itself up through the tank. |
| `jelly_turn` | The +x side of the rim squeezes 70% harder, so the bell tips and the pulses carry it to one side. This is steering by an uneven squeeze. |
| `jelly_drag` | From 2 s to 3.6 s an outside pull drags one tentacle tip sideways, and the whole body answers. |

**Each NPZ holds:**
- `position` and `velocity`: [600, 879, 3] (6 s at 0.01 s, the config's `timestep`);
- `feats`: [879, 6] (mass, part, ring, cos φ, sin φ, stiffness; `elastic_drag` replaces these with ones);
- `box` and `box_feats`: [17136, 3] (the tank's points and inward normals);
- `neighbors_index` and `neighbors_row_splits`: the topology in CSR form;
- `force`: [600, 879, 3].

**`force` is a per-particle acceleration that replaces gravity** in WorldParticle's physics step. It carries what acts from outside the body's own elasticity:
- buoyancy (a slight net sink);
- the coronal muscle's squeeze of the rim;
- the jet's reaction while the bell closes;
- the pull, in `jelly_drag`.

Water drag stays inside the simulation, for the model to learn.

## Make the samples
```bash
python3 jelly_sample.py --out DATA_ROOT --web ../../bonus/wp
```
It takes about 20 s per sample on a CPU. The NPZ files are about 12 MB each, so they are not committed; the viewer's compact copies are in `bonus/wp/`.

## Run WorldParticle on them
WorldParticle needs:
- a CUDA GPU;
- PyTorch;
- FlashAttention (`ATTN_IMPL=flash_attn`);
- Open3D;
- a **trained checkpoint**.

**The repository publishes neither a checkpoint nor a training script.** To predict these samples you need a checkpoint trained on elastic bodies: train one on many jelly samples (vary the pulse, the squeeze bias and the pulls), or ask the authors for one. Then:
```bash
ATTN_IMPL=flash_attn python inference.py --data_dir DATA_ROOT --sample jelly_straight \
  --config /path/to/contaminant-jelly/sim/worldparticle/config_jelly.yaml --checkpoint CKPT \
  --num_steps 599 --dt 1 --output_dir OUT --start 0 --end 600
```
Then convert the rollout for the viewer:
```bash
python3 pred_to_web.py OUT/outcomes/npz/jelly_straight/jelly_straight_0_600.npz jelly_straight
```
The viewer then shows a **WORLDPARTICLE** button: the prediction in blue over the simulation, with the mean error per frame.

## What was checked here
- **WorldParticle's own loader** (`TrajDataset.load_npz_sample_by_data('elastic_drag', …)`, run with a numpy stand-in for torch, since this machine has none) reads all three samples. It classes them as obstacle, topology and force data, reduces `feats` to [879, 1], and gets a consistent CSR topology (N + 1 row splits, every index valid).
- **`pred_to_web.py`** round-trips a stand-in prediction into the viewer's format.
- **Nothing here has run the model itself.**
