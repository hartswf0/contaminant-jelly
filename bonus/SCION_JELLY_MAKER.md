# SCION SYSTEM INSTRUCTION · THE JELLY MAKER, AND FINDING EACH OTHER

Where: `bonus/jellymaker.html`, `bonus/ownjelly.js`; friends changes in `bonus/jellyorchestra.html`.

## 1. Thesis
Every body here was given. Now one can be made: a bell drawn by one shader whose every number is a dial, and one
line of that shader left open for you to write. And a room with a friend in it must show you the friend.

## 2. The jelly maker
A dim room, a plinth, your jelly over it, and the dials beneath. Drag to turn it, pinch or wheel to come closer,
touch it and it strokes.

| Tab | Dials |
|---|---|
| SHAPE | width, height, roundness, rim flare, ribs, rib depth |
| SKIN | top colour, rim colour, glow, clear, edge light, shimmer |
| PATTERN | none, stripes, rings, dots, net; count; strength |
| ARMS | how many, length, curl |
| MOTION | pulse, wobble |
| EFFECT | grain, scan lines |
| RULE | one line of shader of your own |

- **RULE** is an expression that brightens or darkens the skin. It may use `u` (round the bell, 0 to 1), `h` (0 at
  the top, 1 at the rim), `t` (seconds), `n` (noise). Six are offered to start from. The tab shows where your line
  sits in the five lines that make the skin. A line that does not compile is refused, the reason is shown, and the
  jelly keeps drawing without it. Only expressions are accepted: no statements.
- Lids: CHANCE (a random jelly), RESET, KEEP (it becomes your jelly on this device), BE IT (keep it and enter the
  blank room as it), SEND (a link that carries the whole jelly).
- The address always holds the current jelly, so a copied address is the jelly.

## 3. Where a made jelly goes
- The orchestra: YOUR OWN is first in the entrance and in the JELLY lid, with MAKE ONE beside it.
- A room with friends: your numbers travel with you, so friends see the jelly you made, not a stand-in.
- The loadout lists The Jelly Maker under ONE ANIMAL. The open water, steer labs and four space cannot draw it yet.

## 4. Why you could not see your friend
1. Everyone arrives at the same point. Two people entering a room were standing inside each other.
2. A friend out of view had no mark at all.
3. Nothing on screen said whether anyone else was connected.

## 5. What changed for friends
- **Personal space:** closer than 2.6 and you drift apart. Nobody stands inside anybody.
- **A light over every friend:** a thin vertical line, visible across the room.
- **Named at the edge:** a friend out of view is named at the edge of the picture on the side they are on, with
  the distance (`‹ HART · 30`).
- **A room line** at the top left: `ROOM · 2 HERE · HART`, or ONLY YOU, or the reason it could not connect. A
  friend not heard from for 2.5 seconds is marked quiet. Tap it for FRIENDS.
- **GO TO <NAME>** in FRIENDS puts you beside them, facing them.
- Whoever holds the room tells a newcomer which place it is in.

## 6. Checked (headless, emulated touch; values read from the pages, plus stills)
- Maker: the WIDTH dial reached the shader (1.996); the address carried the jelly; a rule was accepted; a broken
  rule was refused with the compiler's reason and the jelly kept drawing; KEEP stored it and set WHO to `own`.
- BE IT opened the orchestra with Your Own selected; the room was entered as the made jelly.
- Two pages on one device: they arrived on one spot and ended 6.1 apart; the room line read `ROOM · 2 HERE · Hart`;
  the guest saw the host's made jelly; when the guest swam off, the host showed `‹ Hart · 30` at the left edge;
  GO TO put them 3.2 apart. No page or console errors.

## 7. Not checked
- Two phones over the internet. The meeting point cannot be reached from here, so if the room line says it could
  not connect, that is the fault and it is outside this page.
- I cannot watch motion or hear sound. Phone speed of the maker.
- A made jelly was large enough in the room to hide a friend behind it; it is now drawn at 0.62 of its size there.
  That number is a guess from one still.

## 8. Next
1. Draw the made jelly in the open water, steer labs and four space.
2. More than one open line: a rule for shape as well as skin.
3. Keep several made jellies, not one.

## The made jelly everywhere, and building that works

**The made jelly is now a body like the ten species.** It lives in the shared body factory (`current/drift/rigs.js`,
id `own`), so any page that takes a species takes it:
- the open water (it is first in YOUR JELLY there), the three steer labs, four space, the loadout's JELLY jar;
- the links under OTHER WATERS at the entrance carry it;
- in the labs its own arms are hidden, because there your fingers are the arms, as with every species;
- it strokes when the page says stroke, not on its own beat;
- it is drawn after the water, so murk does not bury it.

**Why building failed on a phone.** Two faults.
1. A tap was called "held" if more than 450 ms passed between finger down and finger up as the page saw them. On a
   slow frame that is an ordinary tap. A held finger that touched nothing did nothing, so most taps were lost. In
   the headless test, two of four taps placed nothing for this reason.
2. Outside the blank room, things were still set down at the old depth, far below the jelly.

**What changed.**
- A tap that is not on a thing always sets one down. Only a finger held 600 ms on a thing takes it away.
- Outside the blank room, things are set just below your jelly, where you can see them, and keep that height.
- Each placing and each removal is said in a line ("Set down: PLINTH", "Taken away.").
- Entering the blank room always puts you low, by the floor, however walking was switched on.

**Checked (headless, real touch events).**
- Open water, steer lab, steer lab 3D, steer lab 4D and four space each loaded with the made jelly and no page
  errors from it. It is visible in the stills of the open water, the 3D lab, the 4D lab and four space.
- Blank room: four taps, four things. Deep water: taps set plinths at 2.6 below the jelly; a quick tap on a thing
  added another; a held finger removed one.

**Not checked.**
- The 2D steer lab loaded and ran, but the jelly was out of frame in the still for the made jelly and for a species
  alike, so I have not seen it there.
- In the 3D lab a bright made jelly bloomed to white; its light was cut afterwards and not re-shot.
- Real fingers, motion, sound. The open water's films come from an outside host that cannot be reached from here.
