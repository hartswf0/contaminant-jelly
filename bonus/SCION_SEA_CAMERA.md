# SCION SYSTEM INSTRUCTION: THE OPEN WATER'S CAMERA (variables, and ways to think with them)

**The direction:** "The camera controls, camera variables, etc. in the open ocean: more ways to think with the camera."

**Role.** Before this, the open water's camera had one behaviour and hard-coded numbers.

**Now:**
- **Variables:** every number that shapes the view is a variable you can see and move.
- **Lenses:** the variables are grouped into nine lenses. Each lens is a way of thinking with the camera: what is the camera, in relation to the jelly?

**Where:** `bonus/sea.html`. The **CAMERA ·** button sits at the top right. C on a keyboard cycles the lenses, and `?cam=<lens>` opens with one. Your settings are remembered (`cj-sea-cam`).

## 1 · The variables
| variable | what it changes | range |
|---|---|---|
| **distance** | how far the camera sits from the jelly | 1–80 m |
| **height** | the angle it looks down from | −0.3 to 1.3 rad |
| **lens** | field of view: narrow flattens the sea, wide makes it rush | 10–100° |
| **stiffness** | how hard the camera is pulled to where it wants to be: low drifts behind like a buoy, high is bolted on | 0–20 |
| **look-ahead** | how far along the glide it aims, in seconds of motion | 0–2 s |
| **window** | how far the bell may move before the view follows (Itay Keren's camera window): a pulse stays inside it, a committed glide pushes the frame | 0–5 m |
| **shoulder** | a sideways offset, so the bell never hides the way ahead | −6 to 6 m |
| **swing behind** | how quickly the camera swings round behind (or beside) you as you curve; 0 leaves the view where you put it | 0–2× |
| **roll** | how much the horizon leans into a curve; 0 keeps it level, as motion-comfort guidance recommends | 0–1.5× |
| **punch** | how much the lens widens on a stroke, a surge or a current | 0–2× |

**The semantic zoom still owns the far end.** The right-hand bar pulls out from the jelly to the whole sea. A lens shapes the near view and fades as you zoom out; past a third of the way, every lens gives way to the map.

## 2 · Nine lenses: nine ways to think with the camera
| lens | the camera is… | what it lets you think | its settings, and its own rule |
|---|---|---|---|
| **CHASE** | your shadow | where you are going | 11 m behind, swinging behind as you curve |
| **LEAD** | your intention | where you are *about* to go: it aims ahead along the glide, and lets a small pulse pass without moving | look-ahead 1.2 s, window 2 m, less roll |
| **SHOULDER** | a companion | the way ahead, never hidden behind the bell | 8 m, 3.5 m to one side, low |
| **PROFILE** | a documentary | your shape and your speed against the reef | **side-on:** swings to 90° from your heading, keeping whichever side it is already on; level, no roll |
| **LONG LENS** | a wildlife cameraman | shapes rather than speed: far away, narrow; the sea flattens | 70 m away, a 12° lens, lazy stiffness, no punch |
| **WIDE** | your body | speed: close and wide, every stroke a lunge, the reef rushing past | 4.5 m, a 92° lens, extra punch and roll |
| **DRONE** | the weather | the currents and the places, where you could go | **high (0.95 rad), and slowly circling** on its own; never swings behind |
| **TRIPOD** | a place | the composition, and where the jelly will be | **planted:** it does not move until the jelly leaves the middle 82% of its frame (or gets three distances away); then it cuts ahead along your path and off to one side, alternating sides, and waits for you to swim through. This is a stunt camera you never place yourself. |
| **BELL-EYE** | your eye | what the bell points at | just behind the bell, looking 14 m along its axis, with a 72° lens |

**How to choose:**
- **To travel:** CHASE or LEAD.
- **To thread the kelp:** SHOULDER.
- **To watch yourself swim:** PROFILE or TRIPOD.
- **To plan a route:** DRONE (or zoom out).
- **To feel speed:** WIDE.
- **To watch from afar:** LONG LENS.
- **To look into a film you are passing:** BELL-EYE.

**Motion settings:** if the device asks for reduced motion, the first lens starts with no roll and a third of the punch.

**ARMS mode keeps its side view whatever the lens:** the screen there is the plane your fingers work in.

## 3 · Tested (simulated input, swiftshader; game time runs slowly here, so the camera had little time to settle)
| test | result |
|---|---|
| Each lens, with the jelly swimming forward at 9 m/s | each set its lens (CHASE 52°, LONG LENS 13°, WIDE 92°, BELL-EYE 72°, TRIPOD 44°); BELL-EYE sat 4.6 m from the jelly, looking within 6° of where the bell points |
| TRIPOD | it cut once as the jelly swam out of its frame, then watched from ahead and to the side (140° off the jelly's heading, so it was facing the jelly coming toward it) |
| PROFILE | the camera swung steadily toward side-on: its yaw went from 0 to 1.28 of the 1.57 rad of a full profile within the 4 s run |
| The panel | opens; nine lenses; moving *distance* to 30 changed the variable and saved it |

**Distances run long in the test.** Distances sat 6–13 m longer than each lens's setting. Part of that is the zoom bar's starting point; part is the camera's spring lag behind a jelly forced to a constant 9 m/s. In play the jelly accelerates and coasts, so the gap is smaller. Feel on a real phone is not yet judged.

## 4 · Next
- **Let a lens be chosen by a place:**
  - TRIPOD at the reef crossings;
  - DRONE over the currents;
  - LONG LENS near the predators.
- **Record a swim in the open water for the Director** (as in Four-Space), so any lens can film it afterward.
- **Show the variables on the glass while the panel is open:** draw the window and the look-ahead point.
