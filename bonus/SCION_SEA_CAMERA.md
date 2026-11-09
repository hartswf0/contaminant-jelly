# SCION SYSTEM INSTRUCTION: THE OPEN WATER'S CAMERA (variables, and ways to think with them)

**The direction:** "The camera controls, camera variables, etc. in the open ocean: more ways to think with the camera."

**Role.** Before this, the open water's camera had one behaviour and hard-coded numbers.

**Now:**
- **Variables:** every number that shapes the view is a variable you can see and move.
- **Lenses:** the variables are grouped into nine lenses. Each lens is a way of thinking with the camera: what is the camera, in relation to the jelly?

**Where:** `bonus/sea.html`. The camera now lives in the world (§5); the slider panel is a tuning tool behind `?camdev=1`.

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

## 5 · The camera in the world (no panel)
**The direction:** "The camera controls cover what they control. Keep them in the game, more diegetic, in the world: see the vision. The camera is the game; the game and the camera are all the same."

**The principle:**
- **Nothing about the camera sits over the water.** There is no panel and no button.
- **Choosing how you see is part of exploring:** you find lenses, you swim into other cameras' gaze, you ride with a creature that sees.

**Your own lenses are glass shells:**
- **Collecting:** CHASE is yours from the start. LEAD, SHOULDER, PROFILE, WIDE and BELL-EYE drift in the water near the start as glowing shells, each labelled in the water. Swim through one to keep it; it says what kind of camera it is.
- **Orbiting:** the lenses you own orbit your bell as small orbs, and the one you are using glows brighter. Your inventory is visible on your body.
- **Choosing:** hold your finger on the bell (half a second, without moving). The orbs open into a ring around it; drag toward one and let go.
- **Remembered:** your lenses are saved (`cj-sea-lenses`). C on a keyboard cycles them.

**Placed cameras stand in the sea, and show their gaze** (Stunt Island's cameras, made into places):
- **Three tripods,** on three splayed legs, each with a lens at the top. Each shows a cone of light where it is looking. Swim into a tripod's light and it takes the view: a hard cut to the post, a 46° lens, watching you. Swim out of the light and the view eases back to your own lens ("the view is yours again").
- **The spyglass,** a long tube of rings on a ridge, with a narrow cone reaching 120 m. Inside it, the view is a 13° lens from the ridge: you become a far figure in the wildlife cameraman's eye.
- **The ray,** a manta of light slowly circling high over the start. Swim up to it (within 10 m) and you see what it sees: the view rides just above it as it circles. It lets go when you are 46 m away.

**Labels are in the water:**
- "a tripod · swim into its light";
- "the tripod is filming you";
- "the ray · swim up to it to see what it sees".

**The vision is visible:** every placed camera's frame is drawn as light in the sea, so you can see where you would be filmed before you are, and swim into the frame on purpose.

**Tested (simulated input):**
| test | result |
|---|---|
| Starting | only CHASE owned; no camera button in the interface |
| Swimming through the LEAD shell | LEAD collected, and the view switched to it |
| Holding the bell 1.6 s with real mouse input | the ring opened; dragging up selected the top orb (CHASE); letting go chose it |
| Inside a tripod's cone | the view cut to the post (0.00 m from its lens), at 46° |
| Inside the spyglass's cone | the view was from the spyglass, at 13° |
| Reaching the ray | its view; swimming far away gave the view back |
| Into a second tripod's light, then out behind it | it filmed, then let go |

**Fixed along the way:**
- **The ring's hint overlapped the bottom orb's label.** The "drag to a lens" hint now sits below the ring.

## 4 · Next
- **More placed cameras by place:** tripods at the reef crossings and a spyglass near the predators. The tripods, spyglass and ray near the start are the first.
- **A lens that fits a mode:** e.g. PROFILE offered when you take up REINS.
- **Record a swim in the open water for the Director** (as in Four-Space), so any lens can film it afterward.
- **Show the variables on the glass while the panel is open:** draw the window and the look-ahead point.
