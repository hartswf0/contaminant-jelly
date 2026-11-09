# SCION SYSTEM INSTRUCTION: THE CAMERA AND THE DIRECTOR (filming a dive twice)

**The direction:** "Make more camera exploration." It came with a set of references:
- John Nesky's *50 Camera Mistakes* (he designed the camera for Journey);
- the swing framing of *Marvel's Spider-Man*;
- Itay Keren's *Scroll Back* (camera windows and look-ahead);
- Squirrel Eiserloh's *Juicing Your Cameras With Math* (shake as a shaped response);
- the continuous shot in *God of War*;
- Unreal Sequencer's Camera Cut Track.

It also came with a history of who controls the camera (Stunt Island, Pilotwings 64, Super Mario 64, the Quake demos, Driver, Trackmania's MediaTracker), the swimming references (ABZÛ, Superflight, Exo One, Subnautica, New Pokémon Snap), and the request: "the history of reimagining video editing as a game."

**Role.** In Jelly Film the player must see three things, sometimes in one frame:
- where they are going;
- what their body is doing;
- what they are about to catch.

So:
- **The live camera** serves the swim.
- **The swim is recorded,** so it can be filmed again afterward.
- **Three things are edited apart:** the swim, the camera, and the archive cut.

**Where it is built:** The Reef Film (`bonus/fourspace.html?g=dive`) and the shared camera (`bonus/cam3d.js`).

## 1 · The live camera (as built)
| effect | the reference | as built |
|---|---|---|
| **A camera window** | Scroll Back | The bell can move 1.4 m before the view follows. A small pulse stays inside the window; a committed glide pushes the frame. In the test, ten quick pulses moved the view only 0.35 m. |
| **Look-ahead along the glide** | Spider-Man's swing framing; ABZÛ | The view aims ahead along the glide by 1.1 s of motion. The bell sits low in the frame, giving the opening ahead more room. |
| **Side-on while matching** (the first test the brief asks for) | God of War's continuous shot; the brief | When you match a shot's drift, the camera eases, with no cut, to a profile, side-on to the shared drift, framing the bell and the shot together. You can see the two holding position, which makes matching drift visible without a meter. Peel away and it eases back to the chase. |
| **Pulling in at the reef** | the brief's "pass a wall" | If coral in your slice comes between the jelly and the camera, the camera pulls in in front of it, then eases back out. |
| **Shake as a shaped response** | Eiserloh | Only a hard reef impact (or, faintly, the start of a hold) adds *trauma*. The shake is trauma squared and fades in about half a second. An ordinary stroke does not shake. |
| **No roll, ever** | the brief, and the 4D rule | The bell may tumble; the camera's up never changes. Tilting the slice is shown on its own strip. |
| **Motion settings** | Xbox's motion accessibility guidance | "camera shake: on / off" on the Four-Space card. It starts off if the device asks for reduced motion. |

**The three-way test** is built in. A chip under the game's name cycles the live camera between:
- **STEADY**, a plain chase;
- **LEAD**, the window and look-ahead;
- **LEAD + SIDE-ON**, with the profile move added.

The test, as the brief proposes it: ask players to point out when they gained on the shot, when they matched it, and when they broke away, under each style. Whichever camera makes those moments easiest to point to is the one that teaches the move.

## 2 · The Director: the same swim, filmed again
When you surface, the dive does not become pixels. It becomes **a recording the engine plays again** (the Quake-demo distinction):
- 30 frames a second of the jelly's 4D position and velocity;
- the slice's tilt;
- every shot's position and playhead;
- the hold.

**Events** are logged with their times: each hold, each cut, the wall crossing, a hard bump, surfacing.

**Three tracks, edited apart:**
| track | what it stores | what you do with it |
|---|---|---|
| **The swim** | the recording | scrub the timeline; play, pause |
| **The camera cut track** | a list of cuts, each to FOLLOW, PROFILE or FIXED | tap a camera during playback to cut to it; PLACE FIXED HERE puts the fixed camera where the view is now; AUTO CUTS rebuilds the track |
| **The archive cut** | each held shot's source, in and out | trim in and out by half a second (6 frames); THE FILM ▸ plays the result |

**Three cameras:**
- **FOLLOW** is the live chase with look-ahead.
- **PROFILE** is side-on to the jelly and the shot it holds.
- **FIXED** is a camera placed in the world, which the jelly swims through. Like a stunt camera, it starts beyond the wall, composed on where you crossed. It is stored as a 4D point, so it means the same place in any slice.

**Cuts tied to events** (from Stunt Island's triggers and Driver's Film Director):
- **Tied to an event:** a cut made within 0.6 s of a hold, a cut or the crossing ties itself to that event, keeping its offset ("tied to the wall crossing, −0.25 s"). On a faster or slower take, the same cut still catches the move.
- **Tied to a time:** other cuts sit at their time.
- **On the timeline:** a dot above a cut marks it as tied, with a line to its event.

**The auto track:**
- FOLLOW from the start;
- PROFILE a quarter-second before each hold;
- FOLLOW on each cut;
- FIXED a quarter-second before the wall crossing, then FOLLOW 2.5 s later.

**The brief's door example,** in this build:
- **Changing how we see the swim:** cut to the fixed reef camera just before the swing, to see the whole body move.
- **Changing what the film reveals:** trim the held clip's out point by half a second.

Both edits come from the same dive, and neither re-swims it.

## 3 · A history of reimagining video editing as a game
Each tradition gives the player a different job.

| year | work | the player's job | what Jelly Film takes |
|---|---|---|---|
| 1992 | *Stunt Island* (Disney) | **place** cameras on a set, trigger their moves from events, fly the stunt, splice the film | cuts tied to events, not just times; the fixed camera as a stunt camera |
| 1996 | *Super Mario 64* | **direct** a camera operator (Lakitu, with the C-buttons) | the camera as a performer with its own job: keep the bell and the opening readable |
| 1996 | *Pilotwings 64*, Birdman | **fly** the camera into position to photograph | the approach is the shot: see it, bank toward it, settle alongside |
| 1996 | *Quake* demos; *Diary of a Camper* (the Rangers) | **perform** for a recording the engine replays | record action, not pixels |
| 1999 | *Pokémon Snap* | **catch** a moving moment from a moving vehicle | matching drift as the moment of capture |
| 1999 | *Driver*, Film Director | **perform first, direct afterward** | the Director: swim, then film the swim again |
| 2000s | *Trackmania*, MediaTracker | give the camera **its own track** over a run | the camera cut track, apart from the swim and the archive cut |
| 2005 | *The Movies* (Lionhead) | **run a studio**: shoot, then edit films | the reel as something you made |
| 2007 | *Halo 3*, Theater | **reshoot** any saved game with a free camera | a dive you can always go back into |
| 2012 | *Source Filmmaker* (Valve) | **animate and cut** in the engine itself | the timeline as the editor |
| 2014 | *Framed* | **reorder panels** to change what happens | an edit that changes the meaning |
| 2015 | *Her Story* | **search** an archive of clips to find a story | the archive as a place to look through |
| 2015 | *GTA V*, Rockstar Editor | **direct** replays: cameras, cuts, effects | the three cameras, and placing one |
| 2018 | *Fortnite*, Replay | switch between **follow and free drone** views after play | FOLLOW and FIXED |
| 2021 | *Before Your Eyes* | **blink to cut**: your body ends the scene | the body making the cut (breaking formation) |
| 2021 | *New Pokémon Snap* | keep moving while waiting for the instant | pursuit and anticipation |
| 2022 | *Immortality* | **match-cut** by choosing a thing in the frame | next: a cut that follows something the bell holds |
| — | Unreal Sequencer, Camera Cut Track | a track that **chooses the active camera** over time | the cut track itself |

**The thread through all of these:** an edit is a decision made with the body (a swing, a blink, a pursuit) and then remade with a timeline. Jelly Film puts both in one loop:
1. swim to make the archive cut;
2. direct to make the camera cut;
3. dive again to make a different film of the same reef.

## 4 · Tested in the build (simulated input, swiftshader, timed on the game clock)
| test | result |
|---|---|
| The style chip | cycles STEADY → LEAD → LEAD + SIDE-ON |
| The camera window: ten quick up-and-down pulses | the view moved 0.35 m |
| Matching a shot's drift (LEAD + SIDE-ON) | the camera went to PROFILE; breaking away returned it to the chase |
| A hard reef impact | shake 0.28, decaying; logged as a bump |
| The Director: a hold, a cut and a wall crossing, then surfacing | the swim was recorded (197 frames, 6.5 s); the auto track was FOLLOW, then PROFILE at the hold −0.25 s, FOLLOW at the cut, FIXED at the crossing −0.25 s, then FOLLOW at the crossing +2.5 s |
| Just before the crossing | the FIXED camera was live, placed beyond the wall |
| During the hold | the PROFILE camera was live |
| A FIXED cut made 0.3 s after the hold | it tied itself to the hold (+0.30 s); moving the hold 1.5 s later moved the cut 1.5 s with it |
| Trimming the archive cut's out by half a second | the out point went from frame 34 to 28 |
| Playing, then THE FILM ▸ | the playhead moved; the film screened |

**Fixed along the way:**
- **The camera label overlapped the hint.** The Director's "camera ·" label sat under the spoken hint; it now sits clear of it.

**Not yet judged on a real phone:**
- whether the side-on move teaches matching better than the plain chase (the three-way test needs players);
- shake strength.

## 5 · Next
- **An Immortality-style match-cut:** in the Director, tap something the bell held to jump to the next time it appears.
- **A Free camera** (the brief's third replay camera) that you swim yourself through the recording.
- **The three-camera test with real players,** recorded as each player's three answers per style.
