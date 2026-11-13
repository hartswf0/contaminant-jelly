# SCION SYSTEM INSTRUCTION · THE LOADOUT

Where: `bonus/loadout.html` (live: `/contaminant-jelly/bonus/loadout.html`). Also MORE → THE LOADOUT in the orchestra.

## 1. The challenge, as you put it
Each experience grew its own menu: the orchestra's column, the open water's row of ten steers, the Steer Lab's six
rooms, Four-Space's five games, the rig picker on the front page, the Real Jelly's own controls. The same
decisions (which jelly, how to steer, where, what game) were asked in six places in six ways.
What was wanted: one universal menu, where decisions live in jars with lids, in an empty base you can bring
anything into.

## 2. The base
An empty round room, one light, a plinth. The jelly you chose floats over the plinth. In front of it is a shelf
of seven jars. Each jar is glass with a film reel for a lid, which is how every jar on this site is stopped.
Touch a jar: the lid lifts and turns, and what is in it opens below.

## 3. The seven jars
| Jar | What is in it | Shown as |
|---|---|---|
| **JELLY** | the ten bodies and the voice body | a picture of each, in a round frame |
| **STEER** | eleven ways: stick, glide, reins, tap, arms, wheel, twin, drag, tilt, paddle, draw | lids; the ones the chosen game cannot use are dimmed |
| **GAME** | 21 places to go, in groups (below) | lids |
| **WORLD** | the rooms, experiment worlds and film cities | pictures |
| **LOOK** | the twelve paints and prints, or as built | pictures |
| **WORDS** | what the jelly says when you arrive, and in which language | a line to type |
| **BRING** | anything else: give it a name and an address and it becomes a choice under GAME | lids |

**GAME holds:** The Room (one jelly, alone) · The Orchestra · Bring the Reels Home · Talk · Theatre · The Open
Water · the six Steer Lab rooms and its 3D and 4D versions · the five Four-Space games · The Real Jelly · The
Voice Lab.

ENTER is the largest lid. The address it will go to is written beside it, so nothing is hidden.

## 4. The contract
Every experience declares which jars it reads. That is the whole of the universal menu.

| Experience | Reads |
|---|---|
| The Room, The Orchestra | jelly, steer (9 ways), world, look, words |
| Bring the Reels Home | jelly, steer |
| Talk | words |
| The Open Water | jelly, steer (10 ways) |
| Steer Lab rooms, Four-Space games | jelly |
| Theatre, The Real Jelly, The Voice Lab | none |

- A jar the chosen game does not read has its label struck through, and inside the STEER jar the ways that game
  cannot use are dimmed. Nothing is promised that will not happen.
- To make a new experience part of the menu, it only has to read these names from its address:
  `rig` or `pup`, `mode` or `steer`, `look`, `lens`, `say`, `vl`. The existing pages already did for `rig`, `mode`,
  `room` and `g`; that is why this could be built without changing them.
- Your loadout is remembered on the device, and the chosen jelly is written where the older pages look for it.

## 5. The lid in the orchestra
The orchestra's right-hand column (JELLY, STEER, WORLD, LOOK, BUILD, ALONE, SONG, MORE) is now a column of the
same reel lids.

## 6. What was checked (phone-sized and desktop screens)
- Touching the JELLY jar opened it: 11 bodies, all 11 pictures loaded. Choosing one changed the jelly on the plinth.
- GAME offered 21 lids. With The Open Water chosen, STEER lit 10 of 11 ways.
- Addresses compiled: `sea.html?rig=medusa&mode=paddle`; `fourspace.html?g=maze&rig=medusa`;
  `steerlab.html?room=kelp&rig=medusa`; `jellyorchestra.html?game=1&pup=medusa&steer=glide`; and The Room with a
  world, a look and a line.
- BRING: an outside address became a jar and ENTER pointed at it.
- No missing files, no page errors.

## 7. What was not checked
- I compiled the addresses but did not follow each one into its page to confirm the page honours it. The Room and
  the reel game were tested in earlier passes; the Open Water, Steer Lab and Four-Space parameters come from
  reading their code.
- After the last stills I darkened the jar bases (they were blown out white) and moved the second row on phones;
  the orchestra's lid column was not shot at all.
- Sound. Real fingers.
- The picture for The Voice Body is a stand-in.

## 8. What it is not yet
- The jars only choose and launch. You cannot yet bring an object, a film or a room you built into the base and
  see it there.
- The other pages keep their own menus. The next step is for each to show this same shelf in place of its own.

## The door, the round trip, the preview

**Why.** The loadout chose things but did not hand them over, could only be reached from the orchestra, and
could not be tried before leaving. Changing jelly or look on any other page meant editing the address by hand.

**What changed.**
- `bonus/loadout-button.js` is one shared script. Every page that carries it shows a reel-lid door on its left
  edge. Pages: the open water, the three steer labs, four space, real jelly, the voice lab. The orchestra opens
  the same thing from MORE.
- The door opens the loadout over the page you are on. The jars start on what that page is already using
  (its game, jelly, steer, world, look), read from its address.
- ENTER goes back to the same page with only the changed choices replaced; everything else in the address is kept.
  Choosing a different game goes to that game instead.
- LOOK now applies everywhere. A page with `lens=` in its address has that look laid over its canvases.
- PREVIEW: on a screen 900 wide or more, a panel in the loadout runs the real page with the current choices and
  reloads when a jar changes. TEST (the small lid beside ENTER, and the button on the panel) fills the screen with
  it; BACK TO THE JARS returns with nothing lost.

**Limits, stated plainly.**
- Outside the orchestra the looks are colour filters over the finished picture (seven as SVG filters, five as CSS
  filters). They approximate the orchestra's paints; they do not redraw edges or grain the way its shader does.
- A phone has no live panel beside the jars; it has TEST only.
- Real Jelly has one body, so JELLY is ignored there. The voice lab ignores STEER and WORLD.
- Long names can touch each other under the jars on a narrow phone.

**Checked (headless, stills and addresses only).**
- The door is present on all seven pages; `?lens=cyanotype` put a filter on every canvas; no page errors.
- Opened over `sea.html?rig=glass&mode=glide`: jars showed open water / glass moon / glide. Chose medusa and ink
  wash, ENTER returned `sea.html?rig=medusa&mode=glide&lens=sumi` with the jelly and the look changed.
- Desktop preview ran `fourspace.html?g=swing&rig=golden&lens=woodblock`; TEST filled the screen with
  `steerlab.html?room=kelp&rig=golden&lens=woodblock`; BACK TO THE JARS worked.

**Not checked.** I cannot watch motion or hear sound. Real phones, the live site, and whether a filtered page stays
fast on a phone are untested.

## Consequence and memory

**Why.** Choosing something in a jar changed a word under the jar and nothing else. With Theatre chosen, every
other jar was struck through, so no choice did anything and the page did not say why.

**What a choice does now, in the loadout itself.**
| Jar | What you see change |
|---|---|
| JELLY | the body over the plinth, and its picture inside the jar |
| WORLD | the place is thrown on the far wall |
| LOOK | the whole room is seen through that look |
| STEER | the jelly moves the way that steering moves it; the jar holds its sign |
| GAME | its name and one line are on the plinth; jars it sets aside go dark |
| WORDS | the line is on the plinth and in the jar |
| KEPT | new jar: KEEP THIS ONE stores the whole loadout; touch one to bring it back; FORGET ONE removes it |

- Every choice is said in a sentence under the title, and the jar's lid lifts and its lamp flares.
- A choice is never ignored. If the current game cannot use it, the game changes to one that can, and the
  sentence says so: "Theatre does not use JELLY, so GAME is now The Room." A way of steering the room does not
  have (reins, arms) moves you to the open water.
- Choosing a game says what it sets aside.
- Coming back, the page says "As you left it" and the jars hold what they held. Stored on the device only.

**Checked (headless stills and text, phone size).** Starting from Theatre: choosing the medusa changed the body and
moved GAME to The Room; the video store appeared on the wall; woodblock repainted the room; reins moved GAME to the
open water; keeping, leaving, returning and bringing back restored jelly, game, steer and look. No page errors.

**Not checked.** I cannot watch motion, so the steering movements and the lid lift are unseen. Under a strong
look (woodblock) the plinth text is lost. Two long names can still touch in the back row on a narrow phone.
