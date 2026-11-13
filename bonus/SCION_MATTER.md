# SCION SYSTEM INSTRUCTION · MATTER: THE JARS, APPLIED TO THE PLACES

Where: `bonus/jellyorchestra.html` (Bolas edition `/bolas/cities/`). A new place, THE RANGE; a PING button beside
SING, RISE and SINK; two new things and two switches in BUILD.

## 1. Thesis
The five jars were demonstrations. A demonstration teaches one thing and then you leave. Here each one becomes a
rule of the places you already steer through, so that touching the world has a result for a reason:
ground you cannot pass, things that are solid and have voices, a pulse the place answers, a way of drawing what
you build, and a material you can shape.

## 2. From each jar to the world
| Jar | Now, in the places | Where you meet it |
|---|---|---|
| THE MOUNTAIN | **Ground.** A place may have ground. Nothing swims through it, built things stand on it, the camera stays above it. THE RANGE is a new place made of it: a mountain range under water with a clearing to arrive in. The blank room's floor is ground too. | WORLD, the entrance, the loadout's WORLD jar |
| THE PLATE | **Bodies and voices.** Everything built is solid. Swim into it and it stops you and rings in its own way: a column low, a jar high and long, a lamp like a bell. A STEEL PANEL rings by where you land on it: the middle wakes three of its modes, a quarter point wakes all six. Landing on any floor thuds and, in the blank room, leaves a print. | BUILD; then steer into things |
| SOUND IN A ROOM | **PING.** A pulse from your jelly. Everything in the place answers with a tick, after the time sound takes to go there and back, from the side it is on: built things, clay, friends, company, the ground, the blank room's wall, the rock ahead of you in the range. A line names the three nearest with distance and time. Every material sound is also placed: quieter with distance, to the side it is on. | the PING button |
| THE CUBE | **INK.** A finish for built things: light read from a normal bent toward a ball, in three bands, with an inside-out shell for the outline. | BUILD, FINISH |
| THE CLAY | **CLAY.** Tap to set down a lump. Lumps near each other join into one form, drawn as brush marks on its surface. TIGHT or LOOSE changes the marks. The form is solid. | BUILD, CLAY |

## 3. The shared rules
1. `groundAt(x, z)` is the one question any part of the page asks about the floor: steering, the camera, building,
   ping. A new place gets ground by answering it.
2. Arriving in a place with ground, everything already built is stood on that ground.
3. One unit is one metre and sound travels 343 a second. Echo times are true. The ring drawn on the ground is
   slowed to 30 a second so it can be watched.
4. Material sounds go through the same room as the voices, and are not music: they play with music off.
5. A thing's voice is a short list of pitches and a decay, by kind. The steel panel's is computed from the contact.

## 4. Checked (headless; values read from the page, plus stills)
- **Solid:** swum at a column, the jelly stopped 2.5 from its middle and the column rang at 70, 140, 330 Hz. Swum
  at clay, it stopped 2.5 from the lump.
- **Panel:** landing in the middle gave mode weights 1, 0, 0, 0, -1, -1; at a quarter point 0.5, 0.71, 0.71, 1,
  0.5, 0.5; on the centre line off-centre 0.71, 1, 0, 0, 0.71, -0.71. Those are the plate's own shapes.
- **Floor:** a fall came to rest 1.25 above the floor with a thud at 58 and 96 Hz and a print.
- **Ping, blank room:** "THE GROUND 3 m · 15 ms, STEEL PANEL 7 m to your left · 42 ms, JAR 7 m to your right ·
  43 ms"; six things answered.
- **Range:** pushed north and downward the whole way, the jelly rode up the slope and never came closer than
  about 1.3 to the rock. A ping there reported rock ahead at 11 m and the panel left behind at 39 m. A column set
  on a slope stood at the height of the rock under it.
- **Ink** redrew four built things; **clay** from four lumps put about 4,200 marks on one joined surface.
- No page errors.

## 5. Not checked
- I cannot hear. That the voices sound like their materials, and that left and right are the right way round in
  your ears, is unverified; only the pitches, timings and pan values were read.
- Motion and feel of collisions on a phone; speed with many things built.

## 6. Limits, plainly
- Things are solid as upright cylinders. An arch is two legs; you can swim through it but not through a leg.
- The panel does not visibly bend here as it does in its jar.
- Clay is kept on the device but does not travel in a sent link, and friends in a room do not see your clay or
  hear your things ring. Built things do travel in the link.
- INK does not redraw the screen, the lamp's bulb or the jar's glass.
- The range is one fixed range, not a new one each visit. Other places have no ground yet.
- The city worlds and the song places are untouched by this.

## 7. Next
1. Ground for the places that already have floors (store, depot, library), from their own geometry.
2. Friends hear and see what you strike and shape.
3. The panel bends; the sand from its jar gathers on it.
4. Hide something in the range and make finding it by ping the game.
