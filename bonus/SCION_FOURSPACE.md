# SCION SYSTEM INSTRUCTION: FOUR-SPACE (five small games from the four-dimensional references)

**The direction:** "Make more of these references into experimental games", given with a theory of play for *Jelly Film in Four-Space*:
- swim a jellyfish through four spatial dimensions;
- follow archive shots through a moving three-dimensional slice;
- cut by choosing when to break formation;
- surface to watch the reel.

The references were 4D Golf, 4D Miner, 4D Toys, 4D Maze and Miegakure, with Flatland and Hollasch on slicing versus projection.

**Role.** Take one *lesson* from each reference and build a small original game around it, in this project's water, splats and films. Nothing is copied:
- no names;
- no levels;
- no look;
- no mechanics beyond the lesson.

**Where:**
- `bonus/fourspace.html` (`?g=dive|swing|turn|catch|maze`);
- the index's Bonus shelf, next to the Steer Lab 4D;
- linked from the 4D lab's card.

## 1 · The shared engine (as built)
**The world is R⁴.** You see the three-dimensional slice through the jelly.

**The slice's frame:**
- `b0 = x`;
- `b1 = y` (up never tilts, so the camera never rolls);
- `b2 = (0, 0, cos θ, −sin θ)`, the slice's depth;
- the normal `n = (0, 0, sin θ, cos θ)`.

**Positions:**
- a world point *q* appears at slice position `(b0·(q−x), q_y, b2·(q−x))`;
- its signed slice distance is `s = n·(q−x)`.

**Ana and kata** are the two senses of the extra direction (`s > 0` is ana, `s < 0` is kata). The colours are kept everywhere: **blue is ana, amber is kata.**

**Seen and reachable are kept separate** (Hollasch's slice versus projection):
- **a hypersphere** is solid where it crosses the slice, with radius `√(r² − s²)`;
- **where it does not cross,** it is a ghost ring of its full size, in its side's colour, labelled with its distance ("ana 2.3");
- **a ghost can never be caught, held or touched.** Reach is tested in four-space.

**Four verbs, never mixed** (the brief's swim, tilt, look, hold):
| verb | how | what it changes |
|---|---|---|
| **swim** | a stick where you touch (W A S D R F) | the jelly's 4D velocity, along the slice's directions |
| **tilt** | the strip on the right edge (`[` `]`) | only the slice frame: the jelly, its velocity and the world are untouched |
| **look** | the dial (Q E) | only the camera, within the slice; it never rolls |
| **hold** | no control: matching a shot's drift | capture state (in the dive) |

**After a tilt,** swimming forward moves you partly along w. That is how you travel in the extra direction.

**Shared world:**
- **collision** in four-space against solid hyperspheres;
- **motes** scattered through 4D, which show only near your slice, so swimming ana or kata makes them come and go;
- **a floor** whose dots are pinned to the slice's depth, so a tilt visibly slides it.

## 2 · The five games
| game | the lesson, and where it comes from | play |
|---|---|---|
| **1 · The Reef Film** | the photographer's dive, made into an edit (the brief's core); one memorable reef crossing opened by a change of slice (the lesson of the reveal) | See §3 for holding and cutting. **The crossing:** a wall of hyperspheres at w = 0 blocks the reef. Tilt the slice and swim through: you travel along w, past the wall's extent, and come out ana of it. |
| **2 · The Long Swing** | aiming: predict a trajectory through the extra direction before you commit (the golf lesson) | Pull back from the jelly and let go. A dotted path predicts six seconds of flight under gravity, each dot coloured by its slice distance (white in your slice, blue ana, amber kata). Tilt before you pull to aim into w. Three rings, at w 0, 4 and −5; your swings are counted. |
| **3 · Turn Into View** | orientation: predict what the next turn will reveal (the miner lesson) | Five lights hide ana and kata of you. Tilt until a ghost becomes solid, then swim to it. Every change of your mind on the strip is counted: predicting the right way is the skill. |
| **4 · Catch What Passes** | a 4D object passing through a 3D view (the toys lesson, and Flatland's sphere) | Twelve balls cross your slice from ana and kata. Each appears as a point, grows, shrinks and is gone. Tap one while it is solid. Tap a ghost and it says so ("a ghost: kata 5.5; wait for it"). |
| **5 · The Folded Maze** | navigation with another axis: remembering routes (the maze lesson) | 4 × 4 rooms in x and z, three layers in w, carved as one maze. A blue column is a door ana, an amber one a door kata; stand in it and flick the right edge. Walls of the next layer show as faint ghosts in their side's colour. The map shows only rooms you have been in. |

## 3 · The Reef Film, the brief's game
- **Shots:** four real archive clips drift on slow loops through the reef. One is off the slice at w 2.5 and one is beyond the wall at w 5.
- **Hold:** when your four-space distance stays under 3.4 m and your drift matches the shot's to within 2.4 m/s for half a second, the ring fills and you are **holding**. The source playhead runs on, and the frames you have held show beside the shot.
- **Cut (break formation):** a hold ends when you are more than 5.6 m away, or drifting more than 4 m/s differently, for 0.25 s. It also ends when the shot runs out. The hold commits a half-open source interval `[in, out)` to the reel; a hold of under three frames is not kept.
- **Surface:** swim up through the light at the top, or press SURFACE. The reel plays at 12 fps with its credits (clip, frames).
- **Dive again:** the reel is remembered. After a second dive, the two reels play side by side, so you can compare two cuts of the same material (the brief's festal variation).
- **Unavailable clips:** a clip that fails to load says "this shot is unavailable", and the dive goes on.

**The invariants, as built:**
- looking (the dial) and tilting change the view only;
- a hold is decided in four-space, so turning or tilting the view never cuts it;
- the reel stores the source and range, never pixels.

## 4 · Tested in the build (simulated input, swiftshader, timed on the game clock)
| test | result |
|---|---|
| Tilting 1 rad with the jelly still | the world moved 0.000000; the slice frame stays orthonormal (dot 0, length 1) |
| The Reef Film: drifting alongside a shot | held from frame 12; breaking away committed hand butter 12–29 |
| Surfacing | the screening played the reel (hand butter 12–34) |
| The wall, swimming straight at w 0 | stopped at z −8.7 |
| The wall, tilted 52°, swimming forward | passed through it to z −16.9, travelling ana to w 13.7 |
| The Long Swing, tilted toward ana | the swing went ana (w 9.3); the prediction drew 45 dots |
| Catch What Passes | caught a solid ball; a tapped ghost was refused with its side and distance |
| The Folded Maze | a door ana stepped the jelly from w 0 to the next layer (room 0, 3, 1) |

**Fixed along the way:**
- **Tilt marked the wrong way.** Tilting toward *ana* made swimming forward go kata. The slice's depth axis was flipped so the strip means what it shows.
- **A negative first frame.** On the first frame the browser's timestamp can be earlier than the clock, so `dt` came out negative and a shot's playhead stepped to frame −1. Fixed here and in the three other 3D pages.

**Not yet judged:**
- whether players can predict the swing's w;
- whether ana and kata colours read without the labels;
- whether two dives give two different films.

## 5 · Next
- **A second reef crossing,** where tilting reveals a gap rather than travelling past the wall.
- **Linked rings** that separate through w (the toys lesson, fully).
- **A fixed-step simulation clock and a replay log,** so the brief's "identical input, identical edit list" can be tested exactly.
- **The jelly's five tentacles as 4D tethers in the swing,** as the brief proposes; the 4D lab's w-pulling arms are the start.
