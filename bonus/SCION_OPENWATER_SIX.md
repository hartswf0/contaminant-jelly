# SCION SYSTEM INSTRUCTION: THE OPEN WATER AS A THINKING MACHINE

**Role.** World-class interface designer. Interface as epistemic machinery. Build-oriented output only.

**Component:** The Open Water (`bonus/sea.html`).

**Behaviour as found:**
- "too hard to control";
- "the open water still sucks";
- its surface and world were not made of the splats that the rest of the project is built from.

**Task.** Apply six principles to it and give one concrete, shipped redesign.

## The six principles, and what each became

**1 · Surface the invisible.**
- *Before:* your heading, your target, your depth and where things were were all hidden; you steered blind.
- *Now:*
  - a ring of light marks the target on the floor beneath it, with a plumb line up to your depth;
  - a dotted path runs from you to it;
  - a depth bar shows the surface, the floor under you and your jelly between;
  - a zoom bar reads jelly · water · sea;
  - the HUD says where you are going ("to The Reel Tower") and your speed;
  - the film you aimed at pulses warm.

**2 · Overcome cognitive limits.**
- *Before:* yaw, pitch, speed, depth and the floor were all yours to manage at once.
- *Now:*
  - you choose only *where*; the jelly does the rest;
  - depth follows the terrain, looking ahead so ridges are climbed in time;
  - strokes keep to the beat;
  - it keeps going after you let go;
  - the goal is always on screen (places 4, films 12);
  - your trail is drawn on the overview, so you can see the way you came.

**3 · Support multiple modes.**
- *Now:* one world, three readings on one continuous axis:
  - **the jelly** (close: its bell, its tentacles, the films clearing);
  - **the water** (the reach around you, with places named and distances given);
  - **the sea** (everything from above: all the places, every film as a mark, you, your trail).
- Keys, touch and a gamepad are three modes of the same direct control.

**4 · Direct manipulation.**
- *Before:* you steered a heading by its rate.
- *Now:*
  - tap a point, a film or a place, and the jelly swims to it;
  - hold and drag, and the target follows your finger live;
  - drag the depth bar to set your depth; drag the zoom bar, or pinch or scroll, to zoom;
  - two fingers turn the view.
- Every gesture has continuous feedback: the target ring moves, the path re-draws, the bell strokes, the phone or gamepad ticks.

**5 · Semantic zoom.**
- *Now:* the camera rises smoothly from 11 m behind the jelly to 520 m above the sea.
- As it rises:
  - the haze thins (fog falls from 0.017 to 0.0016);
  - the fine floor gives way to a coarse floor of the whole sea;
  - the surface's glare falls away;
  - labels grow, films become marks, and "YOU" and your trail appear.
- Meaning is kept at every scale, and the map *is* the world: tap a place from above to travel there.

**6 · Constrained play.**
- Nothing can hurt you here; the floor and the surface are soft limits; the sea's edge turns you back.
- H takes you home to The Current; a new tap undoes any target.
- Entering a piece is the only one-way act, and it is explicit: you swim *into* a ring of light.

## The texture: one splat language for the whole world
Everything is a gaussian splat, as in the drifts, the films and the jelly bells:
- **Shape.** A splat is a disc sized in metres, its falloff e^(−11r²).
- **Colour.** Dark splats (normal blending) are the silhouettes and fade into the haze colour with exp² fog; light splats (additive) are what glows.
- **The floor:**
  - a lattice of splats that follows your view, so it never ends;
  - each splat stands on a **heightmap baked once** (320² over 900 m), which the shader and the swimmer both read, so what you see is what you touch;
  - dark in the hollows, catching light on the ridges, with jittered sizes and a scatter of glowing silt bulbs in teal and amber.
- **The whole sea** is drawn by a coarse floor of 140² splats when you zoom out.
- **The surface** is a sheet of light splats, brightest where the ripples cross.
- **Kelp** is columns of dark splats that sway, with bulbs at their tips.
- **Rocks** are dark splat clumps.
- **Landmarks** are dark splat shells sampled from their forms (stacked reels, a drowned pipe), lit by bulbs of their own colour, with a ring of points to swim into.
- **Films** are clouds of flecks that gather into a clear screen as you near.

## Kept from before
- strokes on the song's beat (143.5 bpm: every two beats cruising, every beat pushing hard, and automatically pushing when the target is far);
- the wake ring, the thump, the field-of-view kick and haptics on a phone or gamepad;
- the medusae in the trench, the school, the comb jellies, the marine snow;
- the drift briefing card and the jelly picker;
- return-beside-the-ring, the goal, and the seal.
