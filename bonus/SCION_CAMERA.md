# SCION SYSTEM INSTRUCTION: THE CAMERA AND THE BODY (one problem, in 3D and 4D)

**The direction:** "For the 3D and 4D we have to think about camera controls and jellyfish control. Both of them."

**Role.** Treat the camera and the jelly's controls as one system. On a touchscreen there is no second stick for the camera. Every gesture is read *through* the view, so a camera that moves on its own silently changes what your fingers mean. In 4D there is a further question: which slice of the world, or which moment, is the camera looking at?

**The module:** `bonus/cam3d.js` (`makeCam`). Ten Bodies (`bodies.html`) and the Steer Lab 3D (`steerlab3d.html`) now share it.

## 1 · The problem, stated plainly
1. **The camera bends gestures.** A finger held still on a turning view points at a moving place. In the lab an arm aimed through the camera would wander. In Ten Bodies a held squeeze would change direction under the thumb.
2. **The camera fights the hand for the hand.** Two-finger orbiting or pinching collides with bodies that already use two fingers (REINS, the lab's arms, the Reel's lean, the Golden Splat's twist).
3. **Different bodies need different eyes.** A drifter needs to see depth. A herder needs a map. A slicer needs to look straight at its slice. A stick swimmer needs to be behind itself.
4. **The 3D lab's camera faced the wrong way.** Its auto-follow aimed `atan2(-v) + π`, which puts the camera in *front* of the motion. Fixed by the shared module.
5. **4D has hidden axes.** The view has to show one step along w, or along time, before the body takes it.

## 2 · The rules (what `cam3d.js` enforces)
| # | rule | why | convention it borrows |
|---|---|---|---|
| 1 | **Hush.** While a finger has planted something in the world (an arm, a threat, a pour, a stroke, a squeeze), the view does not turn. It still moves, to keep the jelly framed. | A planted finger means a place. Turning the view would move that place. | Mouse-look stops while dragging in editors; aim-down-sights slows the camera |
| 2 | **Carve.** The one exception: a stick that steers relative to the view (the three 4D bodies). There the view swings behind the motion, and that swing *is* the turn. | Holding the stick sideways keeps you turning, as in flying games. | Chase cameras in flight and swim games |
| 3 | **The input basis is held.** Controls read the view as it was when the first finger landed, until the last finger lifts. | A gesture keeps its meaning however the camera moves meanwhile. | Third-person games holding the "forward" of the moment a move began |
| 4 | **The dial is an offset that goes home.** Turning the view dial (bottom left) shifts the view. After 2.5 s it drifts back; a ring round the dial shows the time left. Double-tap the dial to go home now. In ORBIT nothing drifts back. | You can glance without losing your heading. | The recentre delay of most third-person games |
| 5 | **Comfort.** No roll. The view turns at no more than 1.8 rad/s. It stays 1.5 m above the floor. | Steady horizons; no nausea. | VR comfort rules |
| 6 | **The camera is one tap away and never under a gesture.** The camera chip sits above the dial; tap it to change camera (C on a keyboard, V for home, Q E to look, the wheel to zoom). | It never collides with a body's own one- or two-finger gestures. | A camera button, not a gesture |
| 7 | **The body may choose.** A body can ask for a camera at a moment its control needs one. The chip then glows and reads "the body chose it". | The view serves the control. | Context cameras (lock-on, cutscene framing) |

## 3 · Seven cameras
| mode | what it does | what it is for |
|---|---|---|
| **CHASE** | behind the jelly, swinging behind its motion (hushed under a planted finger), looking a little ahead | steering relative to the view |
| **FRAME** | behind the jelly, facing the next light, both in view, pulled back by the distance between them | indirect bodies, which need to see where they are going and what moves them |
| **SIDE** | side-on, almost level; picks a side and slowly keeps to it | depth: up and down read as up and down |
| **TOP** | from above, as a map | bodies that live in a layer (herding, pouring); drawing horizontal currents |
| **EYE** | behind the bell along its axis, looking where it points | a body whose view *is* its control (the slice) |
| **ORBIT** | only the dial turns it | yours; nothing automatic |
| **TRAIL** | pulled back to frame a set of things (a trail, nearby stones) | showing a hidden axis while you scrub it |

## 4 · Each body's camera, and why
| body | default | choices | asks for | the control frame |
|---|---|---|---|---|
| PULSE · Glass Moon | FRAME | frame, chase, side, orbit | — | the screen around the bell, with the basis held while you squeeze |
| FLEE · Sewer Creature | **TOP** | top, frame, chase, orbit | — | the jelly's level: on a map, a finger behind it chases it forward, as with a sheepdog |
| SEQUENCE · Celluloid | CHASE | chase, frame, side, orbit | — | the view at the tap: left, centre and right are the view's |
| ROLL · Film-Reel Jelly | CHASE | chase, side, top, orbit | — | the reel's own body: it leans, then turns |
| LAYERS · Afterlight Medusa | **SIDE** | side, top, frame, orbit | — | the world: depth is the control, so the camera shows depth |
| DRAW · Doodle Jelly | FRAME | frame, top, side, orbit | — | **the camera is the drawing plane.** TOP draws level currents; SIDE draws climbing ones; FRAME draws toward the light. |
| POUR · Fleck Veil | **TOP** | top, frame, chase, orbit | — | the jelly's level, as a map, with the grilles as lines |
| REWIND · Sentinel (4D) | CHASE (carve) | chase, frame, top, orbit | **TRAIL** while you rewind: the camera pulls back to show your whole past, so you can choose where to return to | the view (stick); your history (the trail) |
| FOLD · Golden Splat (4D) | CHASE (carve) | chase, frame, top, orbit | **TRAIL** while you look along w, framing the nearby stones as they change | the view, and w |
| SLICE · Film Bell (4D) | CHASE (carve) | chase, side, orbit | **EYE** inside the film: the camera looks straight at the slice the bell cuts, so the screen *is* the cut | the view, which inside the film is the slice |
| The Steer Lab 3D (all rooms) | Cathedral CHASE; Time-Worm FRAME on the playing frame; Gyre SIDE (to see the climb); Harpoon Sky FRAME on the nearest reel | chase, frame, side, top, orbit | held anchors widen and re-centre the shot | the arms are aimed through the view, so it is hushed whenever an arm is planted or the bell is held |

## 5 · The camera in four dimensions
A 3D camera chooses *where to look from*. A 4D camera also chooses **which slice, or which moment, it shows**, and that can differ from where the body is. This is the new idea, and it is built for w.

- **Fold: the view leads the body in w.** Dragging the w strip moves the *view's* w, not the body's.
  - You see the slice you would fold into: the stones grow and shrink and the lights appear.
  - Your body stays where it was: the jelly shrinks to a ghost, and the strip shows both markers, a gold *you* and a blue *view*.
  - Let go, and the body **folds into the slice you looked at**.

  Look before you fold, as you would look before you jump.
- **Rewind: the view frames time.** While you scrub your past, the camera pulls back to frame the whole trail, so time is laid out in front of you as a place.
- **Slice: the view is the cut.** Inside the film the camera sits behind the bell along its axis, so the slice the bell cuts faces you. The heading you steer is the angle of the image you see.
- **Next:**
  - a time-view for the Sentinel that leads the body as the w-view does (look at a past moment before going back to it);
  - a split view showing w and w + 1 side by side;
  - for the Time-Worm, a camera that rides the playing frame.

## 6 · Tested in the build (simulated input, swiftshader; game time runs slowly, so waits are measured on the game clock)
| test | result |
|---|---|
| Lab, Kelp Cathedral: an arm planted while the bell moves | the view did not turn (0.000 rad) |
| Lab: the arm lifted, the jelly swimming | the view swung 1.9 rad, to behind the motion (0.91 of the way directly behind; before, the old camera aimed in front) |
| Ten Bodies: tap the chip | CHASE → FRAME |
| The dial turned, then left alone for 6 s | the offset went from −0.96 to −0.06 rad |
| A finger down while the view turned 0.86 | the controls' basis did not change; released, it is live again |
| Film Bell inside the film | the camera switched to EYE and looks face-on at the slice |
| Sentinel rewinding | the camera switched to TRAIL |
| Golden Splat looking along w | the view went to w 3.6 while the body stayed at 0; let go, it folded; the camera framed the stones (TRAIL) |
| Every body's control and all four lab rooms, re-run with the new camera | all registered as before |

**Fixed along the way:**
- **The Film Bell's EYE camera stared upward.** A still bell righted itself to point upward, so EYE looked at the ceiling. The bell now keeps its heading along the film, and EYE stands 12 m back, beyond the near-fade.

**Not yet judged on real devices:**
- whether the hush feels like steadiness or like stiffness;
- whether 2.5 s is the right recentre delay;
- whether TOP is too far for the Sewer Creature on a small phone.
