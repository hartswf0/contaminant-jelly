# c16 · board · porthole 16 · Aft · "Identical twin Turkey Sub waving back"

Story unit. Total **52.0 s** (960x540, 24 fps). Badge "16" top right, white on a dark rounded badge, every frame.
Source: the entry with `"porthole": 16` in `../class/transcripts.json`; `../seeds.json` row 15; the deck picture
`../stills/p16.jpg`; the two sheet photographs (looked at, never shown, never committed).

## What the sheet gives us

- **Two endings are written, four are blank.** Written: bolt 3 (first friend, Preposterous) and bolt 5 (next
  friend, Plausible). Blank: bolts 1, 2, 4, 6. Bolt 1 was written and rubbed out and cannot be read: it is a
  blank like the others (no smudge, no guess). Nothing is marked `unsure`.
- Pilot's name is hidden by a fold: show no name. Friends are **B.** (bolts 1 to 3) and **W.** (bolts 4 to 6),
  initials only, small, on the pick cards.
- Captions are the `reads` spelling, word for word, nothing added. One at a time, each held 2.5 s or more.
  There are exactly five captions in the film (three pilot lines, bolt 3, bolt 5). The pick cards carry the
  sheet's own printed option ("Pond mirror", "Two-headed tin monster") as lettering on the card, not as captions.

## The frame the pilot set (carried into EVERY later beat)

| Pilot wrote (reads) | What it fixes for the whole film |
|---|---|
| "A giant three-headed monster." | The one outside the glass is **a giant three-headed monster**: too big for the porthole, so we only ever see parts of it at once from Turkey's seat (three long necks and three heads in the green water behind everything), and its whole bulk only from the river side. It is in frame in every written beat and in both pick beats. It never attacks and never speaks; it is simply there, looking, three heads turning one after another. |
| "Wave at his twin turkey." | **Turkey is waving in every beat he is in.** One wing, raised, hinged at the shoulder, the same wave each time. And there is always a **twin** for him to wave at: an identical tin with an identical porthole and an identical turkey in it, as the pilot drew (boxy sub, round dark window, a turkey head beside it). |
| "Using up his energy." | **Each wave costs air.** A brass air gauge (lower left of Turkey's seat; a small dial riveted to the tin from the river side) drops one notch on every full wave, and the wave itself gets lower and slower through the film: wing high at 13 s, shoulder height by bolt 3, barely off the sill by bolt 5. A bubble leaves the tin's top pipe on each wave. The level never goes back up. Gauge schedule: full at 13.0 s, 5/6 at 20 s, 3/6 after bolt 3, 1/6 after bolt 5. |

## The porthole's rule: Temporal Double (SCION 36)

**Everything that moves in this film moves twice: once now, and once again exactly 12 frames (0.5 s) later, by
its double.** The delay is a constant `D = 12` frames in `world.py`, and the scene units never tune it by eye.

1. Turkey's wave and the twin's wave: the twin's wing is Turkey's wing angle read 12 frames back, mirrored.
   The twin is never ahead and never in step. That lag is what keeps "pond mirror or yesterday's crew?" open:
   a mirror would be in step.
2. The monster's three heads: head A turns, head B does the same turn 12 frames later, head C 24 frames later.
3. The air: every notch the needle drops is two ticks, 12 frames apart. Every bubble has a second bubble behind it.
4. The trout: they swim in pairs, the second trout on the first one's path 12 frames behind.
5. The pick cards and die faces: each arrives as a pencil outline, and its painted double lands on it 12 frames
   later, registering exactly.
6. The pencil in the opening: the dark window is scribbled twice over, the second pass 12 frames after the first
   (it is why the child's window is so dark).
7. The ending breaks the rule on purpose: the die does not move, so it has no double.

Testable invariant for the critic: for any frame f in a waving beat, `twin_angle(f) == -turkey_angle(f - 12)`.

## Lineage and method

`Yellow Submarine (1968 · Sea of Time)`: flat painted cut-out and cel work in poster colour, bold contour, shot on
twos, with a vessel that meets its own double passing the other way. We work the same way on our own subject:
flat cut-paper pieces in poster colour with a dark contour and a cast shadow on the table, moved on twos (12
poses a second), and a double that arrives late. None of that film's pictures, characters, lettering or words
are used. Turkey, the bread-roll tin, the trout and the monster are Trout Town's own, built as BRIEF.md asks
(engraved or cut-paper turkey; riveted bread-roll tin with one round six-bolt brass porthole; engraved or
cut-paper brook trout). Suggested to the world unit for the monster: one large cut-paper body with three necks,
each neck five overlapping paper links, each head a foraged brook-trout engraving head enlarged, so it has weight
and belongs to the river; or wholly cut paper if no clean head can be foraged.

## Animation SCIONs used (from `../drawn/scions.json`)

- **45 · Occlusion Compositing: Who Is In Front?** This film's two written endings are both questions of what is
  in front of what. Bolt 3: the second turkey's wing crosses IN FRONT of the brass rim, on our side of the glass,
  with a contact shadow on the rim; that single overlap is what makes "here" true. Bolt 5: the two-headed tin
  monster comes down over the submarine and its rim passes in front of the tin's shoulder and behind its
  porthole flange, so we see it seat. Fixed layer order per scene, holdout mattes at the glass, contact shadows
  at every touch. Also the ring in the pilot's page: pencil lines stay inside the ring.
- **41 · Secondary Dynamics: Inertia and Restraint.** The wave. The wing is driven; the wing-tip feathers, the
  wattle and the snood hang off it on spring-dampers and lag. As energy is used up the drive gets weaker and the
  settle gets longer (lower stiffness, same damping), so tiredness is read from the follow-through, not from a
  face. Also the gauge needle (overshoots and settles on each tick), the bubbles' wobble, and the clink-settle
  when the tin monster seats in bolt 5. Nothing wiggles unless something drove it.
- **39 · Multiview Drawing Substitution: Turn Lab.** Turkey exists as three drawings, not a 3D shape: rear
  three-quarter (from his seat, bolts 1 to 3), front through the porthole (river side, bolts 4 to 6), and the
  mirrored front (the twin). The cut from seat to river at 32 s is a drawing substitution on a shared pivot
  (the shoulder pin), and in bolt 3 the turn of Turkey's head from the glass to the seat beside him is two
  discrete drawings swapped on the neck pivot, held, never tweened. The tin has two views too: inside rim and
  outside riveted wall.

## Beats

Layout words: **SEAT** = Turkey's seat looking out: dark tin interior, the round brass porthole filling most of
the frame, Turkey's back, shoulder and one wing at lower right, air gauge lower left, green river through the
glass. **RIVER** = the river side looking in: the riveted bread-roll tin at centre-left with its brass porthole
facing us, Turkey seen through it, a small air dial riveted to the tin, green water, trout.

### A · The pilot's page (0.0 to 20.0 s) · scene_pilot.py

**A1 · 0.0 to 9.5 · the drawing is made (no caption).** Top-down on the table: a sheet with the printed ring
(two concentric circles, six small die faces set in the band at 12, 2, 4, 6, 8 and 10 o'clock, as on the sheet;
ours, redrawn, not the photograph). A pencil comes in from lower right. The child drew small and high: everything
sits in the top third of the ring and the lower two thirds stay empty. Keep that. Units: ring centre (0, 0),
inner radius 1, y down. Strokes in order, each drawn at pencil speed, with wobble:

| # | s | stroke |
|---|---|---|
| 1 | 0.6 to 1.8 | the box: a leaning, not-quite-closed rectangle about 0.40 wide by 0.45 tall, centred at (-0.07, -0.64); four sides in one go, corners overshot |
| 2 | 1.8 to 2.5 | a small dome on top of the box at (-0.03, -0.86), a flattened arch with a line under it |
| 3 | 2.5 to 3.9 | the round window at (-0.08, -0.64), radius about 0.05: a circle, then scribbled dark round and round, then scribbled again 12 frames later (the rule) until it is the darkest thing on the page |
| 4 | 3.9 to 4.8 | two little blocks on the left side of the box, at (-0.24, -0.76) and (-0.25, -0.50), each a tiny square |
| 5 | 4.8 to 5.6 | a small upright rectangle on the right side at (0.10, -0.64) and a little triangular fin below it at (0.15, -0.54) |
| 6 | 5.6 to 6.4 | faint: a long loose curve dropping from the bottom of the box, from (-0.10, -0.38) round to (-0.05, -0.16), and two short upright dashes at (0.28, -0.70) |
| 7 | 6.4 to 8.6 | faint, lighter pressure: the turkey head to the right at (0.72, -0.36): a small round head, a beak pointing LEFT toward the box, a dot eye, a wattle line under the beak, then two loose lines trailing down the neck to (0.72, -0.05) |
| 8 | 8.6 to 9.5 | pencil lifts and leaves frame. Hold on the finished drawing: a boxy sub with one dark eye of a window, and a faint turkey looking at it |

Sound: pencil on paper only. Payoff: we have watched a sub and a turkey be drawn beside each other, which is
the whole film in small.

**A2 · 9.5 to 13.0 · caption: "A giant three-headed monster."**
Where: SEAT. The camera has gone down into the ring: the pencil ring becomes the brass rim (pencil outline first,
painted brass double 12 frames later). Who and what: through the glass, the pencil sub turned to cut paper: a
second bread-roll tin hanging in the green water, its round window dark. Turkey's back at lower right, still.
The ONE action: behind the twin tin, three heads on three long necks rise into the glass from below, one after
another, 12 frames apart, and all three look in at us. Payoff: the heads are each bigger than the twin tin and the
necks run out of the porthole at the bottom, so the body must be enormous: giant, three-headed, outside. A viewer
can count the heads.

**A3 · 13.0 to 16.5 · caption: "Wave at his twin turkey."**
Where: SEAT, same framing. Who and what: the twin tin's dark window lights, and in it an identical turkey, facing
us. The monster's three heads stay, watching, upper part of the glass. The ONE action: Turkey raises his wing
and waves, high and brisk, three beats. Twelve frames after each beat the twin gives the same wave back,
mirrored. Payoff: he is waving, at a turkey exactly like him, and it answers late. Gauge reads full at the start
of this beat.

**A4 · 16.5 to 20.0 · caption: "Using up his energy."**
Where: SEAT, pushed in a little toward the lower left so the air gauge is large in frame with Turkey's wing still
visible at right and the twin still visible through the glass. The ONE action: Turkey keeps waving; on each wave
the needle drops (tick, and its double tick 12 frames later) and a pair of bubbles leaves past the glass. By the
third wave his wing only reaches shoulder height and the feathers take longer to settle. The twin's wave droops
the same way, half a second behind. Payoff: the wave and the needle fall together; waving is what is spending the
air. Needle ends at 5/6. Monster's heads still in the top of the glass.

### B · Turkey thinks (20.0 to 32.0 s) · scene_turkey.py · all from SEAT

**B0 · 20.0 to 23.0 · the pick (no caption).** SEAT, held; Turkey still waving low, twin answering late, monster
behind. A card comes up over the lower third (outline, then its painted double): the **green triangle** controller
button, large, beside the lettering **Pond mirror**, and small "B." in the corner. A pencil draws B.'s own
triangle next to the button in three strokes (left side, right side, base, not quite meeting at the top, as on
the sheet). The button presses in once. Payoff: Turkey's side has decided the twin is his reflection in the pond.
At the press, the green water behind the glass takes one slow ripple, like a surface.

**B1 · 23.0 to 24.2 · bolt 1, Probable: BLANK.** Die face 1 at the bolt-1 position on the rim (12 o'clock). The
glass shows an empty, evenly lit stage: plain lit paper, no river, no twin, no monster, no Turkey. No caption.
Hold, move on.

**B2 · 24.2 to 25.4 · bolt 2, Plausible: BLANK.** Die face 2 at the bolt-2 position (2 o'clock). The same empty,
lit stage. No caption.

**B3 · 25.4 to 32.0 · bolt 3, Preposterous · caption: "There is another turkey here."** (caption 26.0 to 31.5)
Where: SEAT. Die face 3 lit at the bolt-3 position (4 o'clock). Who and what: Turkey lower right, waving at
shoulder height, tiring. Through the glass: the twin tin and its turkey, waving back 12 frames late, rippling
slightly because this is the pond mirror; the three monster heads behind, watching.
The ONE action, played as far as "here" will go: Turkey waves. We wait the half second for the reflection's
answer. The answering wing comes up **on our side of the glass**: from the lower LEFT of frame, inside the tin,
a second wing identical to Turkey's rises and crosses in front of the brass rim, casting a contact shadow on the
brass and on the gauge. Turkey's head turns from the glass to the seat beside him (two drawings swapped on the
neck pivot). The camera eases back just enough to show a second turkey's back and shoulder at lower left, the
same cut-out as Turkey, sitting in the tin with him, waving. Out in the pond the reflection now shows two turkeys
in its window, 12 frames late.
Payoff with the sound off: a wing overlaps the INSIDE of the rim, so the other turkey is not out there, it is in
here. Two backs, one porthole. Pilot's frame held: the three heads outside each tilt in turn (12 frames apart) to
look at the second one; both turkeys are waving; the needle now drops twice per wave (two turkeys' worth, each
tick with its late double) and ends the beat at 3/6, bubbles in fours.

### C · The trout think (32.0 to 44.2 s) · scene_trout.py · all from RIVER

**C0 · 32.0 to 35.0 · the pick (no caption).** Cut to RIVER by drawing substitution: Turkey's rear view becomes
his front view on the same shoulder pin, now seen small through the brass porthole of the riveted tin,
centre-left, still waving, low. The twin tin hangs to the right, facing it, its turkey answering late. Behind and
above both, for the first time whole: the giant three-headed monster, body filling the back of the frame.
Two brook trout hold in the foreground, the second 12 frames behind the first. A card comes up (outline, then
painted double): the **blue cross** controller button beside the lettering **Two-headed tin monster**, small "W."
in the corner. W. drew no picture: a pencil loops once, wobbly, all the way round the lettering and the button,
as the choice is circled on the sheet. The button presses in. Payoff: the trout's side has decided what the
two tins are: from where the trout float, the two tins face to face, each with one glowing round window, read as
one tin thing with two heads.

**C1 · 35.0 to 36.2 · bolt 4, Probable: BLANK.** Die face 4 at the bolt-4 position (6 o'clock) on the tin's
porthole rim. Empty, evenly lit stage: no tin interior, no trout, no monster. No caption.

**C2 · 36.2 to 43.0 · bolt 5, Plausible · caption: "Two-headed tin monster fits the submarine."**
(caption 36.8 to 42.5)
Where: RIVER, the tin and its porthole in frame at centre-left, Turkey seen through the porthole. Die face 5 lit
at the bolt-5 position (8 o'clock). Who and what: the two-headed tin monster as the trout chose to see it: one
tin thing made of the same pressed bread-roll tin as the sub, two round tin heads side by side on one tin skirt,
each head with one round brass-rimmed window for an eye, hanging just above the submarine. The pair of trout
watch from lower right. The giant three-headed monster fills the background, three heads looking down.
The ONE action, a notch stranger than straight: the two-headed tin monster settles down over the submarine the
way one bread-roll tin stacks into the next. Its skirt passes in front of the sub's shoulder, the rims meet, it
seats flush with one small bounce and a ring of bubbles, and the brass porthole still shows between the two
heads with Turkey in it. Twelve frames later its double (the same seating, seen in the trout's second look: the
second trout arriving on the first one's path) confirms it.
Payoff with the sound off: no gap, no overhang. Rim on rim, rivet row lining up with rivet row. It fits the
submarine. Strange, but tins do nest. Pilot's frame held: through the porthole Turkey is still waving at his
twin, wing barely off the sill now; the twin tin at right answers half a second late; each wave still drops the
riveted dial, which ends at 1/6; and with the two tin heads seated on the sub the trout are looking at a stack
with the monster's three heads above it, all turning one after another.

**C3 · 43.0 to 44.2 · bolt 6, Preposterous: BLANK.** Die face 6 at the bolt-6 position (10 o'clock). Empty,
evenly lit stage. No caption.

### D · The die is still in the cup (44.2 to 52.0 s) · editor, in c16.py

**D1 · 44.2 to 48.0 · the six bolts.** The brass porthole face-on, centred, glass dark and still. Its six bolts
are checked in order 1 to 6, one every half second, each shown with its die face: bolt 1 empty, bolt 2 empty,
**bolt 3 lit**, bolt 4 empty, **bolt 5 lit**, bolt 6 empty. Empty bolts stay as plain unlit brass with their die
face in outline only. Two lit, four empty. No caption.

**D2 · 48.0 to 52.0 · the die has not been thrown.** Beside the porthole on the table: a die cup, upright, and
one die resting inside its mouth, not rolled, no face presented to us (seen edge-on, a corner up). Nothing
moves and nothing doubles: this is the one place in the film where the rule has nothing to act on. The last
pair of bubbles from the tin's pipe rises past and is gone. Hold 2 s of stillness. No caption, no result.

## Timing summary

| Beat | Start | End | Seconds | Caption |
|---|---|---|---|---|
| A1 drawing made | 0.0 | 9.5 | 9.5 | none |
| A2 pilot line 1 | 9.5 | 13.0 | 3.5 | A giant three-headed monster. |
| A3 pilot line 2 | 13.0 | 16.5 | 3.5 | Wave at his twin turkey. |
| A4 pilot line 3 | 16.5 | 20.0 | 3.5 | Using up his energy. |
| B0 pick, green triangle | 20.0 | 23.0 | 3.0 | none (card: Pond mirror) |
| B1 bolt 1 blank | 23.0 | 24.2 | 1.2 | none |
| B2 bolt 2 blank | 24.2 | 25.4 | 1.2 | none |
| B3 bolt 3 | 25.4 | 32.0 | 6.6 | There is another turkey here. |
| C0 pick, blue cross | 32.0 | 35.0 | 3.0 | none (card: Two-headed tin monster) |
| C1 bolt 4 blank | 35.0 | 36.2 | 1.2 | none |
| C2 bolt 5 | 36.2 | 43.0 | 6.8 | Two-headed tin monster fits the submarine. |
| C3 bolt 6 blank | 43.0 | 44.2 | 1.2 | none |
| D1 six bolts | 44.2 | 48.0 | 3.8 | none |
| D2 die unthrown | 48.0 | 52.0 | 4.0 | none |

Module lengths: `scene_pilot.SECONDS = 20.0`, `scene_turkey.SECONDS = 12.0`, `scene_trout.SECONDS = 12.2`,
ending 7.8. Captions in each module are timed from that module's own start.

## Notes to the other units

- World unit: one `D = 12` frame delay and a helper that returns any driven value "as it was D frames ago";
  Turkey in three views on a shared shoulder pin (rear, front, mirrored front); wing with sprung tip feathers and
  an `energy` parameter (1.0 to 0.2) that lowers reach and stiffness; the twin tin; the monster with three
  independently posable necks; the two-headed tin monster sized from the sub's own rim so the fit is exact; the
  gauge in two forms (seat dial, riveted river dial) with six notches; the pencil drawing as the stroke list in
  A1; green triangle and blue cross buttons; die faces 1 to 6; an empty lit stage; the die cup.
- Scene units: Turkey waves in every beat he is in. The monster is in every written beat and both picks. The gauge
  only goes down. The blanks contain nothing at all.
- Do not letter anything the children did not write, apart from the sheet's own printed option names on the two
  pick cards, the initials B. and W., and the badge.

## Table: bolt, child's sentence, scene

| Bolt | Kind | Child's sentence (as in `reads`) | Scene in one line |
|---|---|---|---|
| pilot 1 | who is outside | A giant three-headed monster. | From Turkey's seat: three huge heads rise behind the twin tin, one after another, and look in. |
| pilot 2 | what Turkey does | Wave at his twin turkey. | Turkey waves; the identical turkey in the identical tin waves back half a second late. |
| pilot 3 | the air | Using up his energy. | Each wave drops the air needle a notch and the wave gets lower and slower. |
| 1 | Probable | (blank: rubbed out, not readable) | Die face 1 on an empty, lit stage, about one second. |
| 2 | Plausible | (blank) | Die face 2 on an empty, lit stage, about one second. |
| 3 | Preposterous | There is another turkey here. | From Turkey's seat: the answering wing comes up inside the tin, in front of the brass rim; a second turkey is in the seat beside him. |
| 4 | Probable | (blank) | Die face 4 on an empty, lit stage, about one second. |
| 5 | Plausible | Two-headed tin monster fits the submarine. | From the river: the two-headed tin thing settles over the sub like one bread-roll tin stacking on another, rim on rim, Turkey still waving in the porthole. |
| 6 | Preposterous | (blank) | Die face 6 on an empty, lit stage, about one second. |
| end | | | Six bolts, 3 and 5 lit, four empty; the die still in its cup, not thrown. |
