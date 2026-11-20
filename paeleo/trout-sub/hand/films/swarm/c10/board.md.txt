# c10 · board · porthole 10 · PA · "Elementary brick: flapping Clam-Shell PA"

Story unit. Total **52.0 s** (960x540, 24 fps). Badge "10" top right, white on a dark rounded badge, every frame.
Source: the entry with `"porthole": 10` in `../class/transcripts.json`; `../seeds.json` row 9; the deck picture
`../stills/p10.jpg`; the two sheet photographs (looked at, never shown).

## What the sheet gives us

- **All six endings are written. There are no blank beats in this film** and nothing is marked `unsure`.
  All six bolts are lit at the end.
- Pilot's name is hidden by a fold: show no name. Friends are **M.** (bolts 1 to 3) and **S.** (bolts 4 to 6),
  initials only, small, on the pick cards.
- Captions are the `reads` spelling, word for word, nothing added. One caption at a time, each held 2.5 s or more.

## The frame the pilot set (carried into EVERY later beat)

| Pilot wrote (reads) | What it fixes for the whole film |
|---|---|
| "Little french fries. A new locked school." | The ones outside the glass are **little french fries**: small crinkle-cut fries, their edges the same zigzag as the pilot's drawing. They are in every scene, bolts 1 to 6, drifting outside the glass. To them the tin is a **new, locked school**: unscuffed tin, latch shut, standing against the elementary brick wall under the clam-shell PA. The porthole latch stays shut in every beat until bolt 6. |
| "Freak out." | **Turkey is freaking out in every beat**, never calm, not even when things go well: beak flapping open on its one hinge, neck feathers thrown, eye wide. Seen as a reflection in the glass from his seat (bolts 1 to 3) and through the porthole from the river (bolts 4 to 6). |
| "It is a big container, so it probably takes it up." | The **big container** is the thing in the drawing: the hinged jaw / clam shell. Every time it swings open, a string of bubbles leaves the tin and goes into it, and the **air gauge** (one needle on one pin, lower left in Turkey's seat; a small dial riveted on the tin's side from the river) drops a notch. Every ending starts from the level the pilot's page left (about half) and loses at least one more notch on screen. |

## The porthole's rule: Single Hinge (SCION 13): jaw pivot

**Everything that moves in this film turns about exactly one pin, and the pin is visible** (a brass paper fastener).
No slides, no fades, no scaling pop-ins. The list of hinges, so the world unit builds them once:

1. the jaw / clam-shell PA: two halves, one pin at the back (the big container)
2. the brass porthole door: one hinge at the left, latch at the right (as in the deck picture)
3. Turkey's beak: lower mandible on one pin (the freak-out)
4. the air-gauge needle: one pivot
5. each trout: tail on one pin; each french fry: a rigid crinkle strip that only tips about its own middle pin
6. scene changes: the new scene is a card that swings in on a corner pin like a page on a brad; the pick card and
   its controller button flip up the same way; the die-cup lid at the end is hinged and stays down
7. the pencil in the opening pivots about the heel of the hand: every stroke is an arc, which is why the child's
   lines lean

Anything that hangs off a hinged part lags behind it and settles (see methods).

## Lineage and method

`tUnE-yArDs: Water Fountain (2014)`: made as a bright, hand-built children's-show set of painted card props and
puppets. We work the same way on our own subject: flat cut-card pieces in a few loud colours, visible cut edges and
drop shadows, props joined with brads, the whole thing a tabletop set with a brick flat at the back. None of that
work's pictures, characters or words are used. Turkey, the tin and the trout stay as the earlier films built them
(cut-paper / engraved wild turkey, riveted bread-roll tin, one round six-bolt brass porthole, brook trout).

## Animation SCIONs used (from `../drawn/scions.json`)

- **13 · Nora Willett, Secondary Motion Swarm** (the SCION the porthole's rule names). Primary motion is only ever a
  hinge angle. Loose things follow it with a spring and damper and then come to rest: Turkey's wattle and neck
  feathers after each beak snap; the fries rocking in the wash each time the jaw shuts; the bubble string trailing
  into the container; the trout tails after a dart. Used in every beat from P2 on. Test: with the hinge still, all
  secondary motion decays to rest inside 1 s (no endless wiggle).
- **32 · Forward Kinematics, Hierarchical Body Logic.** Every puppet is a parent with one child on one pin:
  shell-back > shell-lid, door-frame > door, head > mandible, body > tail, dial > needle. The child's pivot stays
  fixed in the parent's coordinates when the parent moves (bolt 3, when the whole tin is thrown, proves it: beak and
  needle keep their pins). Used for the jaw in P2 to P4, B2, B3, B5 and the porthole door in B6.
- **45 · Occlusion Compositing, Who Is In Front?** The film's whole question is inside versus outside the glass.
  Layer order, back to front, from Turkey's seat: river > brick flat > fries and trout > jaw > glass with Turkey's
  reflection > brass ring > gauge. From the river: tin interior with Turkey > glass > brass ring and door > fries and
  trout > jaw. The order is fixed for five endings and broken exactly once: bolt 6, where trout pass the ring and are
  drawn BEHIND the glass, in front of Turkey. Contact shadows on the tin wherever a piece touches it.

---

## I. The pilot's page (0.0 to 18.0 s) · `scene_pilot.py`

Top-down table: cream paper, a printed ring with six small die faces round it (1 at top, then 2, 3, 4, 5, 6
clockwise, as on the sheet), a pencil. The drawing is redrawn by hand in code from the photograph; wobble and
proportions kept; the photograph is never pasted.

### P1 · the drawing is made · 0.0 to 8.0 s · no caption

Strokes in the order the child's pressure suggests. Each stroke is a short arc with the pencil turning about the
heel of the hand; graphite is darker where a stroke is gone over twice.

| s | Stroke |
|---|---|
| 0.0 to 0.8 | Top edge of the slanted box: one long line rising left to right, overshooting the right end. |
| 0.8 to 1.5 | Left side: a single bowed curve dropping from the top-left corner down and slightly left. |
| 1.5 to 2.6 | Bottom edge, drawn twice: a first line rising to the right, then a second just under it that starts further left than the box (a tail sticking out past the corner) and runs out past the right side. |
| 2.6 to 3.1 | Right side: a short slanted line closing the box, parallel to the lean of the teeth. |
| 3.1 to 5.4 | The teeth: four tall zigzag peaks filling the box from bottom line to top line, left to right, each up-stroke leaning right, each down-stroke crossing the one before so the peaks overlap and make X's; the third peak pressed hardest. |
| 5.4 to 5.8 | The pencil lifts and travels outside the ring to the right. |
| 5.8 to 7.4 | The second, looser jaw: a faint top line, then an upper row of five shallow zigzags, then a lower row of zigzags meeting them point to point, lighter and wider than the first jaw, with a flat line underneath that trails off down and right. |
| 7.4 to 8.0 | Pencil lifts off. A brass brad is pressed through the paper at the back (left) corner of the first jaw: the hinge. The top edge lifts a few degrees on it and drops back. The drawing is a jaw. |

### P2 · line 1 · 8.0 to 11.5 s

- **Caption:** "Little french fries. A new locked school."
- **Where:** the paper swings away on its corner brad; under it, the tabletop set from the river side, wide.
- **In frame:** the brick flat with the clam-shell PA mounted on it (the jaw from the drawing, now cut card, its
  teeth the shell's ribbed edge); below it the bread-roll tin, clean and unscuffed, porthole latch shut; a loose
  bunch of little crinkle-cut french fries, each no longer than the porthole bolt is wide, outside the glass.
- **One action:** one fry tips forward and bumps the latch. The latch does not move. The fry rocks back.
- **Payoff:** little french fries are who is outside; the thing they are looking at is new (no dents, bright rivets),
  locked (the latch held) and standing where a school stands (elementary brick, PA over the door).

### P3 · line 2 · 11.5 to 14.5 s

- **Caption:** "Freak out."
- **Where:** same set, pushed in on the porthole from the river side so Turkey fills the glass.
- **In frame:** Turkey behind the glass; the fries at the edge of frame; the clam shell just visible above.
- **One action:** the clam shell flaps once, and Turkey freaks out: beak flies open on its hinge and claps three
  times, neck feathers and wattle whip after it, a feather comes loose and stays stuck to the inside of the glass.
- **Payoff:** this is the only thing Turkey does, and from here on he never stops doing it. The stuck feather stays
  on the glass for the rest of the film.

### P4 · line 3 · 14.5 to 18.0 s

- **Caption:** "It is a big container, so it probably takes it up."
- **Where:** river side, wide again, so the shell and the tin are both whole in frame and the shell is plainly the
  bigger of the two.
- **In frame:** the clam shell, the tin with its small air dial riveted beside the porthole (needle at full), the
  fries, Turkey still flapping.
- **One action:** the shell swings wide open on its one pin; a string of bubbles leaves the tin's vent and is drawn
  into the shell; the shell closes on them. The dial needle falls from full to half.
- **Payoff:** the big container took the air up. The needle stays at half: every ending starts from here.

---

## II. Turkey thinks (18.0 to 31.5 s) · `scene_turkey.py` · from Turkey's seat, looking out

Fixed view for all three bolts: inside the tin, dark riveted wall, the round six-bolt brass porthole filling most
of the frame, hinge at the left, latch at the right. Turkey's reflection low in the glass (as in the deck picture),
beak going, the loose feather stuck to the glass. Air gauge lower left, needle at half at the start of each bolt.
Outside: river, the brick flat, the fries drifting. Each bolt begins with its die face stamped beside the bolt it
belongs to on the ring, and that bolt lighting.

### T0 · the pick · 18.0 to 20.5 s

- **Caption:** "Turkey thinks: Morning intercom"
- A card flips up on its brad over the dark wall: the **red circle** controller button, pressed in, and beside it
  the friend's own drawn circle redrawn in pencil (a tall, slightly open oval), small "M." under it. Behind the
  card, through the porthole, the clam shell on the brick wall opens and shuts twice like something talking, with
  ripple rings going out from it. It is an intercom now, not a jaw. The card flips down.

### B1 · bolt 1 · die 1 · Probable · 20.5 to 24.0 s

- **Caption:** "The trout to be outside."
- **In frame:** through the glass: the intercom shell on the brick wall, the fries, and three brook trout holding
  station in the current just beyond the glass. Inside: Turkey's flapping reflection, the gauge.
- **One action:** the intercom flaps (morning announcement, ripple rings) and the trout swim up to the glass and
  stop there, noses a finger's width from it, tails ticking on their pins.
- **Payoff:** played straight: the brass ring and the glass are between us and them. They are outside and stay
  outside; one trout's nose taps the glass and the glass holds. Gauge drops one notch as the shell opens.

### B2 · bolt 2 · die 2 · Plausible · 24.0 to 27.5 s

- **Caption:** "He does not get back."
- "He" is taken as Turkey, since the same friend's next line names the turkey as the one who does get back. No
  other figure is shown leaving or returning.
- **In frame:** through the glass, top left, the way back: the bright surface and the foot of a dock ladder. The
  intercom shell hangs between the porthole and that light. Trout and fries to the side, watching.
- **One action:** the shell swings shut on its hinge across the view like a lid coming down, and covers the ladder
  and the light. It does not open again.
- **Payoff:** a notch stranger: the thing that was only talking has closed the way home. Inside, the gauge needle
  falls from half to the last mark before empty and rests there; Turkey's reflection is pressed to the glass, beak
  still going, with nothing to look at but ribbed shell. Hold the shut shell for a full second so "does not" lands.

### B3 · bolt 3 · die 3 · Preposterous · 27.5 to 31.5 s

- **Caption:** "The turkey gets back."
- **In frame:** starts as B2 began: shell, ladder light far off top left, trout, fries.
- **One action:** the shell opens the wrong way, right round on its single pin, a full half turn, and bats the
  whole tin. Through the porthole the world turns about that one pin: brick, trout and fries sweep down and out of
  the glass in an arc, the surface breaks white across it, and the view settles on home: a kitchen shelf with a row
  of bread-roll tins and one empty gap, which the porthole comes to rest in front of.
- **Payoff:** as far as the sentence goes: he is all the way back, on the shelf he came from, river water running
  down the outside of the glass and one little french fry stuck to it. The gauge needle swings up to full (air
  again). Turkey is back and still freaking out: beak flapping, feathers settling late.

---

## III. The trout think (31.5 to 46.5 s) · `scene_trout.py` · from the river side, looking in

Fixed view for all three bolts: in the river, the bread-roll tin in the middle of frame against the brick flat, its
porthole facing us, hinge left, latch right and shut; Turkey inside behind the glass, freaking out, feather stuck
to the glass; the small air dial on the tin at half at the start of each bolt; the clam shell above; fries loose in
the foreground; trout. Die face and lit bolt as before.

### R0 · the pick · 31.5 to 34.0 s

- **Caption:** "The trout think: Confiscated lunchbox"
- A card flips up on its brad: the **pink square** controller button, coloured in solid (the friend coloured the
  printed button too), and the friend's own small pencil square, a little lopsided, small "S." under it. Behind
  the card the tin is re-read: a wire carrying handle is swung up over its top on two rivets and a paper tag on a
  string is tied to the latch. It is a lunchbox that has been taken away and shut. The card flips down. Handle and
  tag stay for bolts 4 to 6.

### B4 · bolt 4 · die 4 · Probable · 34.0 to 37.5 s

- **Caption:** "The trout to run."
- **In frame:** five trout nosing round the tagged tin; fries; Turkey inside; shell above.
- **One action:** Turkey's beak claps against the inside of the glass (the freak-out, seen from outside) as the
  shell snaps shut overhead, and every trout turns about its own middle and is gone off the right edge, tails
  trailing a beat behind, each leaving a short line of bubbles.
- **Payoff:** played straight: one second the frame has five trout, the next it has none, only their bubble trails,
  the fries left rocking in the wash, the tag swinging on its string, and Turkey still at it behind the glass.
  The dial drops a notch on the snap.

### B5 · bolt 5 · die 5 · Plausible · 37.5 to 41.5 s

- **Caption:** "The trout to throw a dance party."
- **In frame:** the same five trout, the tin, the shell above, fries, Turkey.
- **One action:** the shell starts flapping on its pin in a steady beat and the trout dance to it: they pair off
  and go round the tin in a ring, every tail swinging to the same side on each flap, then the other.
- **Payoff:** a notch stranger: it is plainly a party and plainly theirs. The lunchbox is the middle of the floor;
  the fries bob up and down in the wash on the beat; each flap of the shell puffs a ring of bubbles that catches
  the light over the dancers. Inside, Turkey's flapping beak is off the beat: he is not dancing, he is freaking
  out. The dial drops one notch per four flaps, two notches in the scene.

### B6 · bolt 6 · die 6 · Preposterous · 41.5 to 46.5 s

- **Caption:** "The trout to come inside the sub!"
- **In frame:** the tin, close enough that the porthole is a third of the frame height; five trout in a line at
  the glass; fries; Turkey inside.
- **One action:** the latch that held all film flips up, the brass porthole door swings wide on its one hinge, and
  the trout swim in, one after another, all five.
- **Payoff:** as far as the sentence goes: the door swings shut behind the last tail and the glass is now full of
  trout from edge to edge, drawn behind the glass and in front of Turkey (the one time the layer order breaks).
  Turkey's eye and flapping beak show in the gap between two trout; a tail sticks out past the door seal and is
  pulled in; the tin sits visibly lower on the riverbed; one big bubble burps out of the vent and the dial needle
  drops to empty. Outside there is nobody left but the little french fries, looking at the tag.

---

## IV. The die is still in the cup (46.5 to 52.0 s) · editor

- **46.5 to 49.5** The last scene swings away on its brad and we are back on the table with the pilot's paper: the
  pencil jaw inside the ring (its brad still in the corner), the looser jaw outside to the right. The six bolts
  round the ring light one at a time in order, 1, 2, 3, 4, 5, 6, each with its die face. **All six are lit**:
  every ending on this sheet was written.
- **49.5 to 52.0** Beside the paper, a die cup with its hinged lid down and a die resting inside, seen through the
  open side, not thrown. The pencil jaw's top edge lifts a few degrees on its brad and settles. Nothing rolls.
  Hold. No caption (or, if the editor needs one for the voice track, only the sheet's own printed words:
  "Roll the die one time.").

## Blank beats

None. Pilot: three lines written. First friend: Probable, Plausible, Preposterous written. Next friend: Probable,
Plausible, Preposterous written. If a later transcript revision nulls a line, that bolt becomes a 1.0 s beat: its
die face over the empty, lit set, no figures moving, no caption.

## Timing and captions (for `CAPTIONS`)

| Start | End | Caption |
|---|---|---|
| 0.0 | 8.0 | (none: the drawing is made) |
| 8.0 | 11.5 | Little french fries. A new locked school. |
| 11.5 | 14.5 | Freak out. |
| 14.5 | 18.0 | It is a big container, so it probably takes it up. |
| 18.0 | 20.5 | Turkey thinks: Morning intercom |
| 20.5 | 24.0 | The trout to be outside. |
| 24.0 | 27.5 | He does not get back. |
| 27.5 | 31.5 | The turkey gets back. |
| 31.5 | 34.0 | The trout think: Confiscated lunchbox |
| 34.0 | 37.5 | The trout to run. |
| 37.5 | 41.5 | The trout to throw a dance party. |
| 41.5 | 46.5 | The trout to come inside the sub! |
| 46.5 | 52.0 | (none: six bolts lit, die unthrown) |

Module lengths: `scene_pilot.SECONDS = 18.0`, `scene_turkey.SECONDS = 13.5`, `scene_trout.SECONDS = 15.0`,
ending 5.5.

## Notes for the units downstream

- The two pick captions use only words printed on the sheet ("Turkey thinks", "The trout think") plus the picked
  option. If the editor prefers, drop the prefix and show the option alone; do not add anything else.
- Things that must persist: the feather stuck to the glass (from P3); the latch shut until B6; handle and tag on
  the tin for B4 to B6; the fries in every scene; Turkey's beak never still.
- Each ending is its own "what if": reset trout, shell, latch and needle (to half) at the start of each bolt.
- The trout do not get legs, hats or instruments. "Run" is a fish running; the party is made of swimming.
- Nothing from the photographs goes on screen: no handwriting, no names beyond "M." and "S.".

## Table: bolt, child's sentence, scene in one line

| Bolt | Kind | Child's sentence (reads) | Scene in one line |
|---|---|---|---|
| pilot 1 | who is outside | Little french fries. A new locked school. | River side, wide: little crinkle fries outside the clean tin under the brick-wall PA; one bumps the latch and it holds. |
| pilot 2 | what Turkey does | Freak out. | Pushed in on the porthole: the shell flaps once and Turkey's beak claps on its hinge, feathers whipping, one stuck to the glass. |
| pilot 3 | the air | It is a big container, so it probably takes it up. | The big shell swings open on its pin, swallows a string of the tin's bubbles, shuts; the needle falls to half. |
| pick 1 to 3 | M., red circle | Morning intercom | Card with the red circle flips up; behind it the shell opens and shuts like something talking. |
| 1 | Probable | The trout to be outside. | Turkey's seat: the intercom flaps, three trout come to the glass and stay on the far side of it. |
| 2 | Plausible | He does not get back. | Turkey's seat: the shell swings shut across the dock ladder and the light, and does not open; needle near empty. |
| 3 | Preposterous | The turkey gets back. | Turkey's seat: the shell turns clean round on its pin and bats the tin home; the porthole settles on the shelf of bread-roll tins, needle full, beak still flapping. |
| pick 4 to 6 | S., pink square | Confiscated lunchbox | Card with the coloured-in pink square flips up; the tin gets a carrying handle and a tag tied to its shut latch. |
| 4 | Probable | The trout to run. | River side: beak claps the glass, shell snaps, five trout turn and are gone, leaving bubble trails and rocking fries. |
| 5 | Plausible | The trout to throw a dance party. | River side: the shell flaps a beat and the trout go round the lunchbox in pairs, tails in time, bubbles for lights. |
| 6 | Preposterous | The trout to come inside the sub! | River side: the latch flips, the door swings on its hinge, all five trout swim in; the glass is full of trout with Turkey's eye between them, needle at empty. |
| end | | (none) | The pilot's paper: six bolts lit in turn, a die resting in a cup with its lid down, not thrown. |
