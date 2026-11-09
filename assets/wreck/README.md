# Real Jelly — Wreck and Seabed

Extract `assets/wreck/` into the project root. This pack contains four 1K material sets and one self-contained GLB. All five assets are [Poly Haven CC0](https://polyhaven.com/license).

| Asset | Suggested placement | Source |
| --- | --- | --- |
| Rusty Painted Metal | Outer hull, especially where surviving paint can mark the route into the breach | [Poly Haven](https://polyhaven.com/a/rusty_painted_metal) |
| Rusty Metal Sheet | Interior hull plates, hatch edges and deck fragments | [Poly Haven](https://polyhaven.com/a/rusty_metal_sheet) |
| Sand 02 | Main seabed and sand bank at the hull breach | [Poly Haven](https://polyhaven.com/a/sand_02) |
| Gravel Floor | Small coarse patches under the wreck and near debris | [Poly Haven](https://polyhaven.com/a/gravel_floor) |
| Barrel 03 | Rusted blue barrel as a landmark outside the cargo hold | [Poly Haven](https://polyhaven.com/a/barrel_03) |

Each material folder contains base color, OpenGL (+Y) normal, standalone roughness and an optional packed ORM map. ORM channels are red for ambient occlusion, green for roughness and blue for metalness. For Three.js, load base color as sRGB and leave the data maps linear. The GLB embeds its textures and loads through GLTFLoader.

Materials go on your own floor and hull geometry. The barrel is the only prop mesh.
