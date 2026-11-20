# c25 · board · porthole 25 · Lock · "Diner Trout wearing inverted fishbowl"

Story unit. Total **52.0 s** (960x540, 24 fps). Badge "25" top right, white on a dark rounded badge, every frame.
Source: the entry with `"porthole": 25` in `../class/transcripts.json`; `../seeds.json` row 24; the deck picture
`../stills/p25.jpg`; the two sheet photographs (looked at, never shown, never committed).

## What the sheet gives us

- **Four endings are written, two are blank.** Bolts 1, 2, 3 (first friend) and bolt 4 (next friend) are written.
  **Bolts 5 and 6 are blank**: one second each, empty and lit, nothing invented.
- **Bolt 4 is marked `unsure`**: the last word runs off the edge of the photograph. The caption is the `reads`
  text exactly, trailing dots included. The picture shows only the certain part (the fish swim next to the
  astronaut, and they are looking). **What they are looking at is never shown.**
- Names: pilot **M.**, first friend **K.**, next friend **N.** Initials only, small, on the pick cards; the pilot's
  initial may be left off altogether.
- Captions are the `reads` spelling, word for word. One at a time, each held 2.5 s or more.

## The frame the pilot set (carried into EVERY later beat)

| Pilot wrote (reads) | What it fixes for the whole film |
|---|---|
| "A trout, and the trout think it is a bird in a bottle." | Outside the glass is **one trout**: the trout of the pilot's drawing, a fish lying level across the top of a round bowl-shaped body with two arms and two walking legs. It is in every beat, bolts 1 to 4. From the river side the tin is **a bird in a bottle**: Turkey is always seen whole through the round glass, small, shut in, the porthole rim the bottle's mouth. No trout ever touches or opens the tin. |
| "Panic." | **Turkey is panicking in every beat**, including the calm ones: wings beating against the tin wall, neck stretched, beak open, eye wide. From his seat we see it as his reflection low in the glass (as in the deck picture, lower left); from the river we see it through the porthole. He never settles, not even in the last shot. |
| "By panicking." | **The air is used up by the panic and by nothing else.** Each wing-beat sends a puff of bubbles out of the tin's seam and the **air gauge** drops one tick (a needle dial, lower left of Turkey's seat; the same dial riveted on the tin's flank from the river). No leak, no machine, nobody outside takes the air. Every ending starts from the level the pilot's page leaves (half) and loses at least one more tick on screen, always on a wing-beat. |

## The porthole's rule: Inverted Helmet (Oubapo, visual inversion)

A helmet keeps air in and water out. This one is a fishbowl, so it keeps **water in**. The rule for the whole film:
**every picture holds one thing that is the wrong way round, and every move is a turn-over.**

1. **Cuts are flips.** No dissolve, no slide. Each new scene is the old card turned over top to bottom (a 180 degree
   flip about the horizontal middle, 8 frames); the new picture is on its back. The blank beats flip to an empty card.
2. **Seat and river are mirror images.** From Turkey's seat the trout walks right to left; from the river side the
   same walk goes left to right, and Turkey's reflection (lower left, seat) becomes Turkey himself (through the
   glass, river).
3. **The bowl is the wrong way up and the wrong way full.** It sits mouth-down on the brass collar and the water is
   inside it. Its water line stays level with the world however the trout tilts.
4. **Bubbles obey the side they are on.** Turkey's panic bubbles rise outside the tin; the bubbles inside the bowl
   sink.
5. **Bolt 3 turns the whole river inside out** (wet goes inside, dry goes outside). That is the far end of the rule
   and is used once only.
6. The die faces and controller buttons are never inverted: they are the fixed things the eye can trust.

## Lineage and method

The row's lineage is `orig fiction`: there is no earlier work to descend from, so the method comes from the rule's
own house, **Oubapo, the comics workshop**. The film is made as **a strip of hand-drawn panels on cards that can be
turned over**: pencil first (the pilot's page), then the same shapes cut from paper and laid on the card with cut
edges and drop shadows. Turkey, the riveted bread-roll tin, the six-bolt brass porthole and the brook trout stay as
the earlier films built them. Nothing is taken from any existing comic.

## Animation SCIONs used (from `../drawn/scions.json`)

- **7 · Peter Foldès, Drawn Metamorphosis.** The pencil drawing changes into the cut-paper puppet by moving its own
  lines, point for point, so the shape is still recognisable half way. Used in **P1** (the scribbled dome behind the
  fish's head tightens into the glass bowl; the bean body becomes the brass collar and tunic), in **P2** (the round
  porthole outline holds while what is inside it reads first as bottle, then as tin) and in **B3** (the river's
  wavy hatching straightens into dry ground lines). Never a cross-fade.
- **45 · Occlusion Compositing, Who Is In Front?** The whole question here is which side of a glass is wet. Fixed
  layer order from the seat, back to front: lock wall, river, trout body, **water inside bowl**, fish head, bowl
  glass with highlight, porthole glass with Turkey's reflection, brass rim, gauge. From the river: lock wall, tin
  interior, Turkey, porthole glass, brass rim, tin shell, river, fish, bowl. Used in every beat; proved in **B3**,
  where the river layer is removed and the water inside the bowl stays, and in **B4**, where fish pass in front of
  the tin but never in front of the porthole glass.
- **41 · Secondary Dynamics, Inertia and Restraint.** Primary motion is the walk, the wing-beat and the flip. Loose
  things follow on a spring and settle: the water in the bowl slops after each step and after each card flip and is
  level again inside a second; Turkey's wattle and tail fan lag each wing-beat; the gauge needle overshoots one tick
  and comes back; the trout's tail trails the walk. Used from **P2** to the end. With the driver still, everything
  is at rest within 1 s.

---

## The beats

### PILOT'S PAGE (0.0 to 20.5 s) · scene_pilot.py

**P1 · The drawing is made · 0.0 to 10.0 s · no caption**
On the table: a white card printed with two thin concentric circles (the porthole outline, six small die squares on
the ring). A pencil draws inside the inner circle, in this order, each stroke at the child's speed and wobble, the
whole figure leaning slightly and sitting a little left of centre and high:

1. 0.0 to 1.4 · the **fish body**: one long flat lens shape, level, nose to the left, about half the circle wide.
2. 1.4 to 2.2 · the **tail**: a forked flag off the right end, tipped up, the upper lobe longer.
3. 2.2 to 2.8 · a small **back fin** bump on top near the left, and a **dark mouth** at the nose, pressed harder,
   with a few tiny teeth ticks.
4. 2.8 to 4.2 · the **bowl**: three or four loose overlapping loops, lighter pressure, behind and above the fish's
   head on the left, bigger than the head (scribbled round and round, not one clean circle).
5. 4.2 to 5.6 · the **body**: a tall bean or egg hanging down from the middle of the fish, so the fish lies across
   its top like a hat brim.
6. 5.6 to 6.6 · **two arms** on the right side of the body, short, bent, stacked one above the other, each ending
   in a small squiggle hand.
7. 6.6 to 7.8 · **two legs** from the bottom, walking: the left one stepping forward to the left with a flat foot,
   the right one trailing with the foot turned out.
8. 7.8 to 8.4 · the pencil lifts; a held look at the finished drawing.
9. 8.4 to 10.0 · **Foldès change**: the pencil lines move into the cut-paper puppet (loops close into the glass
   bowl with water inside, bean becomes collar and tunic, lens becomes a spotted brook trout head and back). Then
   the card is turned over top to bottom into P2.

**P2 · 10.0 to 14.5 s · caption: "A trout, and the trout think it is a bird in a bottle."**
- Where: the river side, looking in (the only river-side shot before bolt 4; it shows what the trout think).
- In frame: the bowl-headed trout on the left, stopped mid-stride; the bread-roll tin on the right with its round
  brass porthole; Turkey inside, whole and small behind the glass.
- One action: the trout leans in and puts its bowl against the porthole glass, glass to glass.
- Payoff: for the length of the lean the tin's outline is redrawn in pencil as a bottle lying on its side, the
  porthole its mouth, Turkey the bird in it; when the trout leans back the bottle lines return to tin. Read with no
  sound: a trout is outside, and a bottled bird is what it sees.

**P3 · 14.5 to 17.5 s · caption: "Panic."**
- Where: flip to Turkey's seat, looking out. Brass porthole fills the frame; the trout is outside in mirror image
  (now walking right to left); Turkey's reflection low left in the glass; the air gauge lower left reads FULL.
- One action: Turkey's reflection throws both wings up and beats them, beak wide, neck long.
- Payoff: the trout outside does nothing at all, it only stands there; all the motion in the frame is Turkey. The
  panic has no cause but the sight.

**P4 · 17.5 to 20.5 s · caption: "By panicking."**
- Where: same seat, same frame, pushed in so the gauge and the reflection share the lower left.
- One action: three more wing-beats.
- Payoff: on each beat, and only on the beat, a puff of bubbles leaves past the rim and the needle drops one tick:
  FULL to **half** in three beats. Between beats the needle is still. The wings are what spend the air.

### TURKEY THINKS (20.5 to 36.0 s) · scene_turkey.py · Turkey's seat, looking out

**T0 · The pick · 20.5 to 23.0 s · card text: "Scuba helmet" · K.**
A pick card flips up over the porthole: the words "Scuba helmet" and the **green triangle** button, which is
pressed (it sinks and lights). Beside it, drawn in pencil as the friend drew it, a small wobbly triangle. Behind
the card, through the glass, the trout's bowl is ringed once in green: that is the helmet. Turkey's reflection is
still beating; the gauge sits at half.

**B1 · bolt 1 · die face 1 · Probable · 23.0 to 27.0 s · caption: "The air runs out."**
- Where: Turkey's seat, looking out. Bolt 1 on the rim lit, die face 1 beside it.
- In frame: the trout outside in its scuba helmet, walking slowly right to left; Turkey's reflection; the gauge.
- One action: Turkey keeps beating; the needle goes down tick by tick from half to **EMPTY** and rests on the pin.
- Payoff, played straight: the last puff of bubbles is one single bubble, then none on the next beat. The wings
  still go, nothing comes out. Outside, the helmeted trout walks on untroubled, its bowl full. The one with the
  helmet has plenty; the one in the tin has none.

**B2 · bolt 2 · die face 2 · Plausible · 27.0 to 31.0 s · caption: "A little uncomfy."**
- Where: Turkey's seat. Bolt 2 lit, die face 2. Gauge back at half (each ending starts from the pilot's level).
- In frame: the trout stopped square in the glass, closer than before; Turkey's reflection; the gauge.
- One action: the trout hooks one small hand under the brass collar and wriggles the helmet a finger's width, the
  way a child shifts an itchy collar; the water inside slops and levels.
- Payoff, a notch stranger: the helmet does not fit because it is on the wrong way up, and the fish's nose is
  squashed a little flat against the inside of the glass. Nothing breaks, nothing leaks; it is only a bit wrong.
  Turkey's reflection does the same wriggle a beat later inside the panic, neck twisting in the tin's low roof, and
  the gauge loses one tick. Both of them are a little uncomfy, one in each container.

**B3 · bolt 3 · die face 3 · Preposterous · 31.0 to 36.0 s · caption: "It is not wet."**
- Where: Turkey's seat. Bolt 3 lit, die face 3. Gauge at half.
- In frame: the trout in its helmet, the river, Turkey's reflection, the gauge.
- One action: the whole river turns inside out. The blue goes **up** off the top of the porthole like a blind being
  raised, and its wavy hatching straightens into flat dry ground lines.
- Payoff, as far as the sentence goes: outside the glass there is now plain dry daylight. The trout keeps walking
  and each foot raises a small puff of dust; a bubble that was rising stops and drops like a pebble. The only water
  left in the picture is inside the scuba helmet, still slopping level. So the helmet was the right way round all
  along. Turkey has not noticed: he is still beating, and the needle still drops a tick, in a tin standing in dry
  air.

### THE TROUT THINK (36.0 to 46.0 s) · scene_trout.py · the river side, looking in

**R0 · The pick · 36.0 to 38.5 s · card text: "Giant astronaut suit" · N.**
Flip to the river side (mirror image; the river is wet again). A pick card: "Giant astronaut suit" and the **blue
cross** button, pressed and lit, with the friend's pencil cross beside it, and the button itself scribbled over in
pencil as on the sheet. Behind the card the bread-roll tin is ringed once in blue: riveted shell, round visor. The
bird in the bottle of the pilot's page is now the face in the visor, and it is panicking.

**B4 · bolt 4 · die face 4 · Probable · 38.5 to 44.0 s · caption: "The fish swim next to the astronaut, looking..."**
- Where: the river side, looking in. Bolt 4 lit on the tin's porthole rim, die face 4.
- In frame: the tin, large, filling the right two thirds and hanging slow and weightless, tilted a few degrees, its
  porthole a visor with Turkey beating inside it and bubbles rising from the seam; the dial on its flank going down
  a tick. Small beside it: the bowl-headed trout and three plain brook trout, a quarter of the tin's height, so the
  suit is giant.
- One action: the fish swim alongside the suit, left to right, at its drifting pace, keeping station with it like
  a small escort. All of them have their eyes open.
- Payoff, played straight: fish, next to an astronaut, swimming, looking. **Where they look is withheld**: the
  card is cut off at the right edge exactly as the word is on the sheet, the lead fish's eye already past the
  frame line, and no eye in frame is aimed at anything nameable. No fish passes in front of the visor glass.
  Do not finish the sentence in the picture.

**B5 · bolt 5 · die face 5 · Plausible · 44.0 to 45.0 s · BLANK · no caption**
Flip to an empty card: lit paper, cut edge, shadow. Bolt 5 and die face 5 only. Nothing else.

**B6 · bolt 6 · die face 6 · Preposterous · 45.0 to 46.0 s · BLANK · no caption**
Flip again: the same empty lit card. Bolt 6 and die face 6 only. Nothing else.

### THE DIE IS STILL IN THE CUP (46.0 to 52.0 s) · editor

**E1 · 46.0 to 52.0 s · no caption**
Flip to the table. The brass porthole lies flat, seen square on, its six bolts round the rim with their die faces.
Bolts **1, 2, 3 and 4 light** one after another (0.4 s apart); **5 and 6 stay dark and empty**. Through the glass,
small: the trout in its bowl, standing, and low left the reflection of Turkey, still beating, the gauge at half.
Beside the porthole a dice cup stands upright with one die resting in it, a corner showing over the lip. Nobody
touches it. Hold 2.5 s on the still cup. The last thing moving is the water in the bowl coming level.

---

## Timing check

| Part | Beats | Seconds |
|---|---|---|
| Pilot's page | P1 10.0, P2 4.5, P3 3.0, P4 3.0 | 20.5 |
| Turkey thinks | T0 2.5, B1 4.0, B2 4.0, B3 5.0 | 15.5 |
| The trout think | R0 2.5, B4 5.5, B5 1.0, B6 1.0 | 10.0 |
| The die in the cup | E1 6.0 | 6.0 |
| **Total** | | **52.0** |

Captions (film time): P2 10.0 to 14.5 · P3 14.5 to 17.5 · P4 17.5 to 20.5 · B1 23.0 to 27.0 · B2 27.0 to 31.0 ·
B3 31.0 to 36.0 · B4 38.5 to 44.0. Scene units may trim each caption's start by 0.3 s for the flip.

## Notes to the other units

- World unit: the trout puppet must keep the pilot's proportions (fish level across the top, bowl bigger than the
  head and behind it, bean body, both arms on one side, walking legs), not the deck picture's upright trout. The
  deck picture gives the materials only: brass collar, glass bowl with water, Turkey's reflection low left, cave
  wall of the lock.
- The gauge resets to half at the start of B1, B2, B3 and B4: the endings are alternatives, not a sequence.
- Nothing in any beat may take air from the tin except Turkey's wing-beats.
- Blank beats get no sound event beyond the card flip.

## Table

| Bolt | Child's sentence (caption, as in `reads`) | Scene in one line |
|---|---|---|
| pilot 1 | "A trout, and the trout think it is a bird in a bottle." | River side: the bowl-headed trout leans its bowl on the porthole and the tin redraws as a bottle with Turkey the bird in it. |
| pilot 2 | "Panic." | Turkey's seat: his reflection beats both wings while the trout outside only stands there. |
| pilot 3 | "By panicking." | Turkey's seat: three wing-beats, three puffs of bubbles, the gauge falls from full to half. |
| 1 · Probable | "The air runs out." | Turkey's seat: the needle ticks down to empty on the wing-beats; the last bubble, then none; the helmeted trout walks on. |
| 2 · Plausible | "A little uncomfy." | Turkey's seat: the trout wriggles its upside-down helmet by the collar, nose squashed on the glass; Turkey twists in the tin the same way. |
| 3 · Preposterous | "It is not wet." | Turkey's seat: the river lifts away like a blind, the trout walks on dry ground raising dust, and the only water is inside the helmet. |
| 4 · Probable | "The fish swim next to the astronaut, looking..." (unsure: last word off the edge) | River side: small fish keep station beside the giant drifting tin with Turkey beating in its visor; what they look at is cut off by the frame. |
| 5 · Plausible | (blank) | Empty lit card, bolt 5 and its die face, one second. |
| 6 · Preposterous | (blank) | Empty lit card, bolt 6 and its die face, one second. |
| end | (none) | Six bolts: 1 to 4 lit, 5 and 6 empty; a die resting unthrown in its cup. |
