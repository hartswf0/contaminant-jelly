# Class films · the children's own stories

Read `BRIEF.md` first: the same rule holds (handmake or forage, no style costumes; the thing is made on the table).
This batch differs in one way: **the story belongs to the children.** `../class/transcripts.json` has what a
fourth-grade class wrote on five Porthole Logs. Your film renders that sheet, in order, and adds nothing to it.

## The film (40 to 60 seconds, 960x540)
1. **The pilot's page.** The pilot's drawing is made on the table, in pencil, stroke by stroke, the way the child drew
   it (look at the photograph in `class_photos/pNN_front.jpg`; redraw it by hand in code, keeping its wobble and
   proportions; do not paste the photograph). Then the pilot's three lines appear in turn, each one acted out:
   who is outside, what Turkey does, how the air gets used up.
2. **Turkey thinks.** The first friend's pick, shown with its controller button (green triangle, red circle, or amber
   hexagon). Then that friend's endings, one bolt at a time, each with its die face (1 Probable, 2 Plausible,
   3 Preposterous) and each ACTED OUT as its own short scene, through the brass porthole from Turkey's seat.
3. **The trout think.** The next friend's pick with its button (blue cross or pink square), then bolts 4, 5, 6 the same
   way, seen from the river side with the bread-roll tin and its porthole in frame.
4. **The die is still in the cup.** Nobody had rolled yet. End on the six bolts, the written ones lit and the
   unwritten ones empty, and a die that has not been thrown.

## Rules for the children's words
- Use each sentence as written, in the `reads` spelling, as the caption for its scene. Do not improve, extend or
  joke on top of it. "Trying to save a hot Cheeto" is the scene; stage exactly that.
- **A blank stays blank.** Where a line is null, show that bolt's die on an empty, lit stage for about a second and
  move on. Never invent an ending. Where `unsure` is set, show only the part that is certain.
- Children are named by first initial only, and only if you show a name at all. No photographs of the sheets on screen.
- The porthole number sits in the top right corner throughout, white on a dark rounded badge.
- Keep the world the earlier films set: Turkey is an engraved or cut-paper wild turkey inside a riveted bread-roll tin
  with one round six-bolt brass porthole; trout are engraved or cut-paper brook trout. `films/p03.py`, `p14.py`,
  `p35.py`, `p44.py` and `p01.py` are finished examples: read at least one in full and reuse its approach.
  You may forage from Wikimedia Commons as before (credits file required).
- Put the captions in a top-level list `CAPTIONS = [(start, end, text), ...]` so the voices can be added later.

## How each film is made: a swarm of units, as the Oulipo films were
Each film has its own folder `films/swarm/cNN/` and is made by units that hand work to each other:

1. **Story unit** writes `board.md`: the film beat by beat. For the pilot's page and for every WRITTEN ending it
   expands the child's sentence into a staged scene: where we are, who is in frame, the one action, and the payoff
   that makes the sentence true. The sentence itself is never changed; the expansion is all in the picture.
   The pilot's first page is the frame for everything: who the pilot says is outside, what Turkey does, and how the
   air gets used up must colour every later scene (if the pilot wrote that Turkey freaks out, he is freaking out in
   every ending). The porthole's own Ouxpo/SCION rule shapes how things move. Probable is played straight, Plausible
   a notch stranger, Preposterous as far as the sentence will go. Blanks are listed as blanks.
2. **World unit** builds `world.py`: the shared pieces every scene uses, foraged or handmade (Turkey, the bread-roll
   tin and its brass porthole, the trout, this porthole's own subject, the pilot's drawing as pencil strokes, the
   controller buttons and die faces, the palette), and writes `WORLD.md` listing each function and how to call it.
3. **Three scene units** each write one module from the board, using only `world.py` and the kit:
   `scene_pilot.py` (the drawing made, then the three lines), `scene_turkey.py` (the pick and bolts 1 to 3),
   `scene_trout.py` (the pick and bolts 4 to 6). Each module exposes `SECONDS`, `CAPTIONS` (times from its own
   start) and `draw(t, ink)`.
4. **Editor** writes `films/cNN.py`: joins the three modules, adds the ending (the die unthrown, bolts lit or
   empty), the number badge and the sound, a top-level `CAPTIONS`, and renders. The editor fixes what does not join.
5. **Critic** and **rights reviewer** look independently; a **repair unit** then applies what they found and re-renders.
