# SCION SYSTEM INSTRUCTION: STEERING (a catalogue of ways to move a jelly)

**Role.** Keep a living catalogue of steering schemes. Each borrows a convention people already know, says what it is good for, and is playable. Choose by the moment, not by habit.

**The direction:** "more steering experiments: a steering wheel, two thumbsticks, more convenient ones, and the bell can also be dragged."

## The open water: ten ways to swim (`bonus/sea.html`)
Pick a scheme from the chips at the foot of the screen; the choice is remembered (`cj-swim`) and can be set with `?mode=`.

| scheme | convention it borrows | the hand | the jelly | good for | costs |
|---|---|---|---|---|---|
| **GLIDE** | Sky, ABZÛ: a floating stick | a finger down anywhere is a stick; push to swoop, push to the rim to surge | carves arcs; the camera swings behind; it banks | the default: flowing turns | needs a thumb on the glass |
| **REINS** | tank and rowing: differential drive | two fingers are two fins: lift both to rise, one more than the other to carve, spread to surge | carves and climbs | expressive two-hand play | two hands |
| **TAP** | Endless Ocean, Diablo: point and go | tap a point, a film or a place; hold and drag to move the target | swims there itself, following the terrain | accessibility; long trips; the map | low agency |
| **ARMS** | the Steer Lab (Getting Over It, Gibbon) | every finger takes a tentacle and hooks kelp, rocks, films, rings, the floor or water | dragged by its arms; peel, catch, harpoon | expressive set pieces | a side view only |
| **WHEEL** | racing games | turn the wheel at the foot of the screen (or twist two fingers); it springs back; a finger elsewhere is a pitch lever | hands on the wheel swim | one-thumb steering with a visible state | the wheel covers the bottom of the view |
| **TWIN** | twin-stick (Subnautica mobile, shooters, gamepads) | left thumb moves relative to the view; right thumb looks | swims where you look, dive included | full 3D freedom; gamepad players | two thumbs; can disorient |
| **DRAG** | Angry Birds, Osmos | grab the bell and pull it on an elastic; let go and it flings; drag off the bell to turn the view | goes where it is pulled, then keeps the momentum | precision near films; slingshots | short range |
| **TILT** | Flower, Journey, tilt racers | tilt the phone from where you held it when you chose this; hold a finger to swim | turns and pitches with the phone | hands-free steering, lean-in feel | needs a phone; iOS asks permission |
| **PADDLE** | kayak and rowing | swipe up on the left to stroke and turn right, on the right to turn left; both together surge; swipe down to brake | each swipe is one bell stroke | rhythm; one swipe = one decision | slower turns |
| **DRAW** | Flight Control, Kirby: Canvas Curse | draw a path through the water | follows your line point by point | choreographed routes; film passes | indirect |

**Shared by all:**
- strokes on the beat;
- the depth bar and zoom bar;
- haptics on a phone or gamepad;
- currents to ride;
- W A S D and R F.

**Each scheme draws its own instrument:**
- the floating stick;
- the reins' fin travel;
- the wheel with its marker;
- the MOVE and LOOK sticks;
- the elastic from the bell to your finger;
- a bubble level for tilt;
- the paddled half of the screen flashing;
- the dots of a drawn path.

## The Steer Lab: six rooms (`bonus/steerlab.html`)
In every room, **a finger on the bell now holds the jelly itself**: an elastic to your finger; let go and it flings. Anywhere else, each finger owns one tentacle.

1. **The Silt Halfpipe** (PEEL)
2. **The Kelp Swing** (SWING)
3. **The Ray's Wake** (TOW)
4. **Twice the Hand** (TWICE)
5. **The Harpoon Range** (CAST)
6. **The Fling** (FLING, new): drag the bell and fling it through three rings; then the way out opens. It is the most direct steering there is, and the hardest to aim.

## How to choose
- **First play:** GLIDE (or TAP for anyone who would rather point).
- **With a gamepad:** TWIN.
- **Expressive set pieces** (kelp, wakes, films): ARMS in the open water; the lab's rooms to learn it.
- **A film to pass beside:** DRAW the pass, or DRAG the bell next to it.
- **Rhythm and calm:** PADDLE.
- **Phone in hand, standing up:** TILT.
- **One thumb, always the same place:** WHEEL.

## Tested (simulated input in the build)
| scheme | test | result |
|---|---|---|
| WHEEL | turned clockwise | turned the jelly right |
| TWIN | left stick forward, right stick right | swam forward and turned the view |
| DRAG | pulled the bell about 9 m | it followed |
| TILT | a right tilt | turned it right |
| PADDLE | a left stroke | turned it right; both sides surged straight |
| DRAW | drew a line | the jelly followed it |
| The Fling | held the bell and released it | it reached 17.5 m/s and passed ring 1 ("flung") |

**Fixed along the way:** the start card's jelly picker kept catching touches for 0.7 s after the start; it now lets go at once.

**Not yet judged on real devices:**
- feel;
- the tilt calibration;
- the wheel's size on small phones.

## Next experiments
- **A rudder and throttle pair:** the left edge sets speed, the right edge steers; as in a boat.
- **Gaze:** with a front camera, look where to go.
- **Breath:** a microphone breath as a stroke.
- **Follow a partner:** another jelly or a fish that you shadow.
- **A gyro plus a stroke button** in landscape.
- **Mixed schemes per region:** each place could pick its own default (TAP over the map, ARMS in the kelp, DRAW at the films).
