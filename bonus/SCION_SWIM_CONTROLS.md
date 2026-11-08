# SCION SYSTEM INSTRUCTION: SWIMMING (controls, conventions, fun)

**Role.** Design how a body moves through water in 3D so that it feels good in the hand: curving, readable and forgiving. The games that do this best are the model.

**The direction:**
- "make better gaussian videos in it"
- "two-finger controls: more curving, cooler ways for movement; explore a few options"
- "the best underwater games' movement, flight and swimming conventions for 3D movement; best games' convention principles, fun"

## 1 · What the best games do (conventions)
| game | what it teaches |
|---|---|
| **ABZÛ** (2016) | Swimming is gliding: the body auto-orients to its motion, a boost is a burst you can chain, and **currents** are fast rails that carry you through set pieces. Never punish; let the camera sweep. |
| **Journey · Flower** | Camera-relative steering; momentum and gentle arcs; wind as a ride; joy comes from *curving*, not from precise stops. |
| **Sky: Children of the Light** (touch) | A **floating thumbstick**: put a finger down anywhere and the stick appears under it. A second finger flies higher or faster. Banking is visible. |
| **Subnautica** | Full 6-degree freedom: you move where you look. Powerful, but disorienting without a horizon; depth is always shown. |
| **Endless Ocean** | Calm and accessible: point at a thing and go to it; time and wonder over skill. |
| **Ecco the Dolphin** | Charge-then-dash, leaps at the surface, sonar to reveal the world; the momentum is the fun. |
| **Flight games (Pilotwings, Star Fox)** | Yaw and pitch from one stick, auto-level when released, a roll that sells the turn, speed shown through field of view and streaks. |
| **Tank and rowing controls** | Two inputs as two sides of a body: **differential** drive steers, both together drive straight. |

**Principles drawn from them:**
1. **Steer the heading, not the position.** The body keeps moving; input bends its path. Curves come from momentum: a turn rate held at speed draws an arc.
2. **Camera follows the motion.** It swings in behind the heading with a lag, so input stays camera-relative.
3. **Auto-orient and auto-level.** The crown leads, the body banks into turns, and letting go levels you out over the floor.
4. **Shaped input.** A dead zone, a response curve (gentle near the centre, sharp at the rim) and a stick base that follows a finger running past it.
5. **Rhythm is propulsion.** A jelly moves by strokes, so strokes land on the beat; a boost is more strokes, not a different physics.
6. **Rails for joy.** Currents carry you fast along a curve; you can steer out of them.
7. **Feedback on every channel:** bank, field-of-view kick, wake, thump, haptics, streaks.
8. **Forgive.** Soft floors and surfaces, no damage, a home key, and an accessible mode for those who would rather point than steer.

## 2 · The three ways to swim (`bonus/sea.html`)
Choose with the GLIDE · REINS · TAP chips at the foot of the screen; the choice is remembered.

**GLIDE** (default; after Sky and ABZÛ):
- Put a finger down anywhere and a ring appears under it: that is your stick. Push to swoop. Yaw rate is up to 1.9 rad/s, and turns tighten less when surging, so arcs widen with speed.
- Push to the rim to surge, with strokes on every beat. A second finger surges too.
- Let go and you coast, level out and follow the terrain again.
- A tap without dragging is a single stroke.
- The stick's base follows a finger that runs past its rim.

**REINS** (two fingers as two fins; after tank and rowing controls):
- **Both fingers up:** rise. **Both down:** dive.
- **One higher than the other:** carve. The left fin driving harder turns you right, as tracks and oars do.
- **Spread them** to surge; **squeeze them** to stop stroking and glide.
- The guide draws each fin's travel and its position.

**TAP** (accessible; after Endless Ocean):
- Tap a point, a film or a place, and the jelly swims there itself, terrain-following.
- Hold and drag, and the target follows your finger.
- Two fingers zoom and turn the view.

**All modes:**
- **The camera** swings in behind your heading (GLIDE and REINS) or stays where you set it (TAP).
- **The body** banks into turns, and the camera rolls slightly with it.
- **Strokes** land on the song's beat (143.5 bpm), with the wake ring, the thump and the field-of-view kick.
- **Haptics** for phones and gamepads.
- **Keys:** W A S D and R F act as the stick; shift surges; S brakes.
- **Gamepad:** the left stick is the stick, the right stick turns the view, the right trigger surges.

## 3 · Currents (after ABZÛ's and the East Australian Current's jet streams)
- **Two looping currents:**
  - The Current → the Reel Tower → the Doodle Reef → home;
  - The Current → the Sewer Mouth → the Medusae Trench → home.
- **Their shape:** each is a centripetal Catmull-Rom spline, kept 9–16 m over the floor and never shallower than 12 m.
- **Drawn as** streams of flecks flowing along them.
- **Swim into one** (within 5.5 m): it pulls you to its heart and carries you at about 19 m/s, with a widened field of view, "IN THE CURRENT", a chord and a haptic pattern.
- **Steer out** to leave.

## 4 · Gaussian video, better
**Each film is a strip of 48 × 36 splats (36 × 27 on phones) plus two rows of sprocket holes**, and every splat reads its own pixel of the footage:
- **Relief:** bright pixels stand forward and dark ones recede (±0.7 m), so the picture has depth.
- **Size by brightness:** highlights swell and shadows thin.
- **Overlap normalisation:** additive splats would sum to white, so each splat's light is divided by how much it overlaps its neighbours. The footage keeps its own colour at any distance.
- **From cloud to picture:** far off, a film is a swirling cloud whose scatter falls with the square of its clarity. It settles into the picture from 34 m and is fully formed at 9 m.
- **Size:** films are now 9.6 × 7.2 m, so the screen reads next to the jelly.
- **Playback:** the nearest film plays its clip as a video texture through the same splats.
- **Taking a film:** swim within 6 m of it. A faint flat underlay stays behind the splats.

**The surface** is fogged and dimmed near the camera, so riding a current near it never blows out.
