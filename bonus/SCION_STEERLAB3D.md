# SCION SYSTEM INSTRUCTION: THE STEER LAB 3D (steering in space, and through time)

**The direction:** "We need a 3D steer lab for steering in up to 4D dimensions; all our Steer Lab is 2D."

**Role.** Take the flat lab's body (every finger owns one tentacle until it lifts) out of the plane. A finger now points into a volume, so the lab must answer two questions the flat lab never asked:
1. **Depth:** how deep does a finger reach?
2. **Time:** what does it mean to hold a moment, and to move it?

The play is in those two answers.

## 1 · Interpretation
- **Ordinary reality:** a touchscreen is flat; the world behind it is not.
- **Play problem:** how a flat hand plants arms at different depths, and then in different moments of a film.
- **Cognitive puzzle:** reading depth through a flat screen. You turn the view to see which stalk is near, and you learn that a held finger sinks.

## 2 · The four dimensions, and how a finger reaches each one
| dimension | how the finger sets it | what you see |
|---|---|---|
| **x, y** (across the screen) | where you touch | the finger's ring |
| **z** (into the screen) | **the ray:** a touch is a line of sight, and the arm takes the first thing along it (a stalk, a stone, a reel, a frame, the floor). In open water it braces on a plane through the bell facing the camera, and **a finger held still pushes that brace deeper** (up to 8 m, at 3.5 m/s). | a second ring around the finger that grows with depth, labelled in metres |
| **t** (a film's time) | **the Time-Worm:** a film's 64 frames are laid through the water as a coil, so its time is a place. Hook a frame and that arm holds that moment. Slide along the coil and the held moment moves through the film's time (up to 16 frames a second), dragging the anchor and you with it. | the time bar at the foot: the playing frame ("now") and a thumbnail for every held moment |

**The rule of the fourth dimension.** The film keeps playing. When the playing frame catches up with a moment you hold, that arm lets go. So time is both:
- a handhold you can steer by;
- a tide that takes your holds away.

## 3 · The body in 3D (`bonus/tentacles3d.js`)
- **The shared module.** `makeArms3D(THREE, opt)` is the flat `tentacles.js` lifted into space, with the same verbs: down, move, up, step, chains.
- **Arms on the rim.** Six arms sit around the bell's rim, a circle in 3D that tilts with the bell.
- **Force and torque.** Every arm pulls at its own rim point, so a pull has both force and torque as a vector. The bell tumbles about any axis and rights itself slowly.
- **The finger is a ray.** The host world answers `pick(ray)`, `water(ray, depth)` and `update(anchor)`; the module asks nothing else of it.
- **Kept from the flat lab:**
  - winch (drawn on screen: a finger moved toward the bell hauls in);
  - sag;
  - snap on release;
  - slip;
  - the lost grip on an interrupted touch;
  - the flick-cast;
  - catch the wreck.
- **The flick is timed by the clock.** It measures the hand's real speed, not game time (over 900 px/s), and throws the arm along the line of sight: a hitscan into depth.
- **Frames are not winched.** A frame anchor is moved by scrubbing, never by the winch, so a finger's slide means time, not rope.

## 4 · The rooms (`bonus/steerlab3d.html?room=`)
| room | verb | the experiment | what it tests |
|---|---|---|---|
| 1 · The Kelp Cathedral | SWING | Twelve stalks stand near and far around you; you are heavy (gravity 3). Swing under a stalk, let go at the top, reach the next. The exit is a ring across the room. | Swinging in three dimensions: the next stalk can be behind you as well as ahead. Turning the view is part of the move. |
| 2 · The Time-Worm | TIME | A film (`cineosis-hand-butter`) laid as a coil of its own frames, gaussian tiles of their own pictures. The playing frame glows and climbs the coil. The exit is above the last frame. | **Steering by time:** hold a moment, slide it, ride it. Two arms on two moments ("two moments at once") swing the bell between them. The playhead releases you. |
| 3 · The Gyre | SPIRAL | A vortex turns round the middle and lifts as it turns. Floating stones are the only rest. The exit is at the top. | A 3D current: an arm braced in its water is carried round and up ("borrowed the gyre"). |
| 4 · Harpoon Sky | CAST | Seven reels float near and far, high and low. A flick throws an arm along your line of sight. Haul four in, and the way out opens overhead. | Aiming into depth: you aim with the view, not just the finger. |

**Shared by every room:**
- **The bell.** A finger on the bell holds the jelly on an elastic; let go and it flings.
- **Stroke.** Double-tap or space.
- **The view dial** (bottom left): drag it to orbit. Q E R F also orbit, and the wheel zooms. The camera drifts behind your motion and widens to frame what you hold.
- **The posture glyph** (top right): a top-down drawing of the bell, with every arm's load in its finger's colour and the tilt as a dot.
- **Desktop:** hold 1 to 5 to plant fingers at the mouse.
- **Sealing.** A finished room is sealed (`steer3d-<room>`) and offers the next.

## 5 · Failures, and how each is designed out
- **The flat finger** (every touch lands on the same plane). The ray takes whatever it meets first, at any depth, and a held finger sinks its brace.
- **The lost depth** (you cannot tell near from far). Several cues carry depth:
  - the depth ring;
  - the dial;
  - the camera framing your holds;
  - fog dimming far splats.
- **The frozen moment** (holding a frame forever). The playhead catches up and frees it.
- **The unwanted launch.** As in the flat lab, an interrupted touch loses its grip and never flings.
- **The flick that never fires on a slow frame.** The flick is timed by the clock, so a stalled frame rate cannot swallow it.

## 6 · Tested in the build (simulated input, swiftshader)
| room | test | result |
|---|---|---|
| Kelp Cathedral | a finger on a stalk 6.9 m away | latched to the kelp; the bell was pulled 4 m |
| Time-Worm | hooked frame 28 and slid along the coil | the held moment moved to frame 40; the bell travelled 20 m; "steering by time" registered |
| Gyre | a finger in open water above the bell | braced in water, carried up; "borrowed the gyre" |
| Harpoon Sky | a flick toward a reel 7.6 m away | cast, hooked, hauled: "reel 1 of 4" |

**Fixed along the way:**
- **The flick and slow frames.** The flick was timed in game time, so on slow frames it never fired. It is now timed by the clock.
- **The worm's start.** The Time-Worm used to start beside frame 0, where the playhead released your first hold at once. It now starts by frame 28.

**Not yet judged on real devices:**
- feel;
- how readable depth is on a small phone;
- whether the held-still depth push is discoverable.

## 7 · Where it lives
- **The Bonus shelf** on the index: "The Steer Lab 3D".
- **The flat lab's card:** "the 3D lab →".
- **The Open Water:** a place beside the flat lab.

## 8 · Next experiments
- **Two films crossing:** two coils that intersect, so you can change films at a shared frame. An edit made with the body.
- **Reverse time:** a room where the playhead runs backward, and holds release from the other side.
- **A Time-Worm in the open water:** a film you pass becomes a coil you can climb.
- **Depth by pinch:** two fingers on one arm set its depth directly.
- **The cathedral as a race,** with the moves you found scored.
