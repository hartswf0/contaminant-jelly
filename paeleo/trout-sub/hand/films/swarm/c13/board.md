# c13 · board · porthole 13 · Arch · "Bell Boulder arch with brass twig-bell"

Story unit. Total **51.0 s** (960x540, 24 fps). Badge "13" top right, white on a dark rounded badge, every frame.
Source: the entry with `"porthole": 13` in `../class/transcripts.json`; `../seeds.json` row 12; the deck picture
`../stills/p13.jpg`; the two sheet photographs (looked at, never shown, never committed).

## What the sheet gives us

- **Three endings are written (bolts 1, 2, 3). Bolts 4, 5 and 6 are blank, and so is the second friend's pick.**
  Four blank beats in all. Nothing is invented for them.
- One `unsure`: the pilot's second line. "The sub." is faint after it. **Caption only the certain part: "Freak out."**
  Nothing in the picture may lean on "The sub." either (Turkey freaks out; the tin is not made to do anything by
  that line).
- Names: pilot **S.**, first friend **A.**, next friend **M.**: first initials only, small, on the page corner and
  the pick cards. The world unit may leave them off entirely.
- Captions are the `reads` spelling, word for word, nothing added. One at a time, each held 2.5 s or more.
- The words inside the pilot's speech bubble are part of the drawing, not a caption: they are pencilled as she
  wrote them, **"haha verry funny"**, on three short lines.

## The frame the pilot set (carried into EVERY later beat)

| Pilot wrote (reads) | What it fixes for the whole film |
|---|---|
| "The trout. The trout think the sub is a bell-ringer prank." | The ones outside are **the trout**, and only trout: two leads (the upper one and the lower one of the drawing, same placing: one high and left of centre, one low and right) plus a few more behind them when a scene needs a crowd. They believe the tin rang the twig-bell for a joke. So in every beat **the trout look at the tin with flat, unamused mouths**, and the upper trout keeps its pencilled bubble "haha verry funny" pinned above it whenever it is in frame. Nobody outside is ever frightened of the sub or curious about it. They are fed up with it. |
| "Freak out." | **Turkey is freaking out in every beat**, bolts 1 to 3 included, even the calm one: eye ringed white, beak open, wattle thrown, neck feathers up, wings beating the inside of the tin. From his seat he is the reflection low and left in the glass (as in the deck picture). In the ending shot he is not seen. |
| "He is going to be turkey dinner." | This is how the air goes: Turkey has decided the bell is about HIM. Every time the bell moves he gasps, a string of bubbles leaves his beak, and the **air gauge** (brass dial, one needle, lower right inside his seat) drops a notch. And the picture keeps saying dinner: seen from his seat, the **brass bell hangs exactly over his reflection like the dome of a serving dish**, the tin's rim is a roasting tin's rim. That alignment is held in every Turkey-side beat. Gauge: 8 notches full; the pilot's page leaves it at 5. Every ending is its own ending, so each of bolts 1, 2, 3 **starts again from 5** and loses at least one more on screen. |

## The porthole's rule: Clockwise Etiquette (SCION 48)

Seen on screen as two laws, tested by the critic frame by frame:

1. **Everything that travels, travels clockwise** as the viewer sees it. Trout circle the bell clockwise. The
   pencil works its way round the page clockwise. The bell's rope is pulled from the left and the bell swings out
   to the right first. Bubbles leave on a clockwise curl. Bolts light clockwise from the top. Scene changes are a
   brass arm pinned at the porthole's centre that sweeps the glass once, clockwise, like a clock hand, with the next
   scene behind it. Nothing ever goes back the other way, not even to reset. From the river side (bolts 4 to 6)
   the same law holds as the viewer sees it.
2. **One at a time, in turn.** Whoever is at twelve o'clock (under the bell) has the turn. The next one waits at
   nine o'clock, mouth shut, until twelve is clear. Nobody overtakes. The die faces printed round the child's ring
   already sit this way (1 at twelve, 2 at two, 3 at four, 4 at six, 5 at eight, 6 at ten o'clock): the six bolts
   keep those places all film long.

The trout are therefore little state machines, and so is Turkey (see methods). The etiquette is what bends in
each ending: kept in Probable, kept but far too fast in Plausible, kept to an absurd perfection in Preposterous.

## Lineage and method

`TROUTOWN Ep. 3 (Trading on the Current)`, marked "orig film": the town's own film, so there is no outside work to
descend from and none to copy. We make it the way the finished porthole films in this folder are made: cut-paper
and engraved pieces on a table, laid by hand, with edges and shadow. The made thing here is the **arch and its
bell**: a boulder arch of torn green-grey paper with moss, a forked twig across the top, a brass bell cut from
foil-coloured card with a separate clapper, and a knotted cord (the deck picture gives all four). The trout are
engraved or cut-paper brook trout; the weed is torn paper ribbon.

## Methods (animation SCIONs from `../drawn/scions.json`)

- **48 · State Machines: Characters That Can Refuse** (also the porthole's own rule). Each trout has states
  `QUEUE -> TURN -> RING -> LOOK_AT_TIN`, plus `CRAZY` (bolt 2) and `CALM` (bolt 3), with guards: only one trout in
  `TURN`; angle round the bell may only increase clockwise; no transition out of `QUEUE` while twelve o'clock is
  taken. Turkey has one top state, `FREAK`, with sub-states `GASP`, `FLAP`, `FROZEN` (rigid, shaking, still
  freaking). He has **no calm state at all**, so in bolt 3 the trout can go calm and he cannot: that refusal is the
  joke the picture is allowed, because the pilot wrote it. Used in: pilot lines 1 to 3, bolts 1, 2, 3. A numeric
  check the scene units should assert: every trout's angle is monotonic clockwise; never two trout in `TURN`.
- **41 · Secondary Dynamics: Inertia and Restraint.** The bell on its twig, the clapper inside the bell, the
  knotted cord under it, Turkey's wattle, and the weed are spring-damper followers of whatever drives them: the
  clapper arrives late and strikes, the cord whips after the bell, the weed leans with the current the trout make.
  It must also **stop**: in bolt 3 everything settles to dead rest and stays there, no idle wiggle. Used in: line 1
  (the bell nudged), bolt 1 (the ring), bolt 2 (bell wound round its twig, weed dragged), bolt 3 (the settle), and
  the unthrown die resting in its cup.
- **45 · Occlusion Compositing: Who Is In Front?** The clockwise circuit only reads as a circle round the bell if
  the layers are right: a trout passes **behind** the right arch pillar and the bell's cord, then **in front of**
  the left pillar; Turkey's reflection lies on the glass in front of the water but behind the brass rim; the bell
  dome sits over his reflection without hiding his eye. Contact shadows where paper lies on paper. Used in: every
  beat through the brass porthole (line 3, bolts 1 to 3) and the river-side stage of bolts 4 to 6 (tin in front of
  the arch foot, weed in front of the tin).

## The beats

### A. The pilot's page (0.0 to 20.0 s) · on the table

The printed sheet's ring is already there: a thin double circle with six small die faces at the six bolt places.
Everything inside is pencil, soft grey, a little shaky, pressed harder on outlines and lighter on shading. A real
pencil (cut card, with shadow) makes each stroke; nothing pops in. The pencil goes round the ring clockwise after
the first fish.

| # | Time | Beat | What is drawn or done |
|---|---|---|---|
| A1 | 0.0–2.2 | The upper fish | Centre, a little left and above the middle, facing left. One long pointed-oval body in two strokes (top edge, then belly), meeting in a point at the tail end. A round eye with a ring round it and a dot, a short curved smile under it. Then the tail on the right: a triangle, open end out, filled with four or five quick hatch lines. |
| A2 | 2.2–4.0 | The bubble, at ten to eleven o'clock | A lumpy cloud outline above and left of the fish, with a wobbly neck coming down to the fish's head. Inside, lettered stroke by stroke on three lines: "haha" / "verry" / "funny". Small, crowded, leaning. |
| A3 | 4.0–5.4 | The bell, at twelve to one o'clock | A small bell hanging near the top: a short upright, a little cap, a flared skirt, a dot of a clapper. From it a wavy line wanders right to the rim: the twig. It is tiny beside the fish, as she drew it. |
| A4 | 5.4–6.2 | The weed at three to four o'clock | A tight vertical squiggle hugging the right rim, like a spring. |
| A5 | 6.2–8.0 | The lower fish, at four o'clock | Lower right, facing left, slimmer and tilted nose-down. Body in two strokes, a fan tail kicked up to the right with hatching, ringed eye, small smile. Then light slanted shading strokes along its back. |
| A6 | 8.0–9.0 | The weed at seven o'clock | A scalloped scribble like a row of loops, with one thin stem running down from it to the rim. The pencil lifts and leaves frame clockwise. Hold the whole drawing for the last third of a second. |
| A7 | 9.0–13.0 | **Line 1** · caption: "The trout. The trout think the sub is a bell-ringer prank." | **Where:** still on the table, inside the pencil ring. **In frame:** two cut-paper trout laid by hand exactly over the two pencil fish (upper first, then lower, clockwise); the pencilled bubble stays above the upper one; the brass bell piece laid over the pencil bell; the bread-roll tin slid in at the bottom of the ring, six o'clock, lamp up. **The one action:** the tin's lamp-beam card touches the cord and the bell tips out to the right and back (clapper late, one strike). **Payoff:** both trout swing round clockwise to see who rang, find nobody at the bell, and both end up nose-down staring at the tin with flat mouths, under "haha verry funny". They have blamed the tin. |
| A8 | 13.0–16.0 | **Line 2** · caption: "Freak out." | **Where:** the hand turns the tin a quarter clockwise so we see in through its porthole. **In frame:** Turkey, cut-paper and engraving, filling the round glass; the two trout still staring from above. **The one action:** Turkey freaks out: eye ring snaps white, beak drops open on its hinge, wattle flies (and lags), wings drum the tin so the rivets jump. **Payoff:** the tin itself rattles on the table and the pencil lines near it smudge. Air gauge 8 down to 6. Nothing else moves: the trout do not flinch. |
| A9 | 16.0–20.0 | **Line 3** · caption: "He is going to be turkey dinner." | **Where:** the brass arm sweeps clockwise and we are in **Turkey's seat looking out**, for the first time: brass rim, six bolts, arch and bell beyond, his reflection low left. **In frame:** the bell, the two trout, Turkey's reflection, the gauge. **The one action:** the bell swings back to rest and, from where he sits, comes down **exactly over his own reflection like the dome of a serving dish**. **Payoff:** he sees it. The two trout drift to either side of the dome, where a knife and fork would lie. He gasps, a curl of bubbles goes up clockwise, and the needle falls 6 to 5. This picture (dome over the bird) is kept for all of part B. |

### B. Turkey thinks (20.0 to 40.5 s) · Turkey's seat, looking out through the brass porthole

Same framing for all three bolts: brass rim with six bolts, arch and twig-bell outside, cord hanging with its knot,
Turkey's reflection low left under the bell dome, gauge low right. Each bolt starts fresh from gauge 5, the trout
in their drawing places, after one clockwise sweep of the brass arm. The bolt's die face sits on its own bolt and
that bolt lights.

| # | Time | Beat | Scene |
|---|---|---|---|
| B0 | 20.0–23.0 | **A.'s pick: "Dinner bell"**, red circle | The pick card is laid on the glass by hand: the two choices as on the sheet, "Tripwire alarm" with a green triangle and "Dinner bell" with a red circle. A pencil draws A.'s own circle, one wobbly loop, **clockwise**, in the little dashed ring; the red circle button presses in and lights; the triangle stays dull. The card label is the only text; no caption. As the card is lifted away the red circle stays behind as a small red disc on the bell itself, and it stays there for bolts 1 to 3. Behind the card Turkey is already flapping. |
| B1 | 23.0–28.0 | **Bolt 1 · die 1 · Probable** · caption: "The dinner bell to go off." (23.3–27.7) | **Played straight. In frame:** bell, cord, upper trout at twelve o'clock, lower trout waiting at nine, Turkey's reflection, gauge. **The one action:** the upper trout, whose turn it is, takes the knot in its mouth and pulls once, to the left; the bell kicks out right, the clapper arrives late and strikes, twice. **Payoff, sound off:** at each strike a ring of ripples leaves the bell mouth and widens across the whole glass, the glass shivers, grit jumps off the arch; the red disc on the bell flashes; and both trout turn their heads to the tin as if to say "served". The dome rocks over Turkey's reflection. Turkey: `GASP`, bubbles, needle 5 to 4. The waiting trout never leaves nine o'clock: etiquette kept. |
| B2 | 28.0–34.0 | **Bolt 2 · die 2 · Plausible** · caption: "The dinner bell goes off and the fish go crazy." (28.3–33.7) | **A notch stranger: they go crazy, but all the same way round.** **In frame:** bell, both leads plus four or five more trout that pour in from the left pillar, Turkey's reflection, gauge. **The one action:** the bell goes off (one pull, ripple ring, as in bolt 1) and the trout stampede **clockwise round the inside of the porthole rim**, a wheel of fish. **Payoff:** by the second lap they are nose to tail, some belly-up, one upside down, eyes rolling, all still in single file and all clockwise; the weed is dragged over flat in their wake; the cord winds round the twig and the bell is hoisted, clanging, so ripple rings come thick and overlap; the bubble "haha verry funny" is towed round behind the upper trout like a kite. Each lap they flash across Turkey's reflection. Turkey: `FLAP`, wings a blur, needle 5 to 3. Hold the wheel at full speed to the cut. |
| B3 | 34.0–40.5 | **Bolt 3 · die 3 · Preposterous** · caption: "The fish go quiet and calm." (34.4–40.0) | **As far as the sentence goes: perfectly quiet, perfectly calm.** **In frame:** the same six or seven trout, bell, weed, Turkey's reflection, gauge. Opens on the wheel of bolt 2 still turning, bell clanging. **The one action:** the trout stop. One at a time, clockwise from twelve, each one halts at its own bolt place round the glass like the numbers on a clock, folds its fins and half-closes its eye; the stillness goes round the ring like a second hand. **Payoff:** the last trout, at twelve, takes the **clapper** gently in its mouth and holds it, so the bell cannot sound: the ripple rings shrink back into the bell mouth and are gone. Weed stands straight. The cord hangs plumb. Bubbles in the water stop where they are. The bubble "haha verry funny" settles and lies still. Hold nearly two full seconds of **nothing moving outside at all**. The only moving thing in the frame is Turkey, in the reflection under the motionless dome, `FROZEN`: rigid, trembling, eye white, one bubble, needle 5 to 4. The fish are calm. He is not. |

### C. The trout think (40.5 to 45.0 s) · the river side, looking in · ALL BLANK

M. picked nothing, drew nothing, wrote nothing. The stage is built and lit and left empty. One clockwise sweep of
the brass arm takes us round to the river side: the riveted bread-roll tin low in frame with its brass porthole
facing us, glass glowing amber from inside, the arch foot and the still bell above, weed. **No trout, no Turkey
visible, no caption, no action.** Only the light.

| # | Time | Beat | Scene |
|---|---|---|---|
| C0 | 40.5–42.0 | **Blank pick** | The pick card is laid down by hand: "Polite ferry customer" with a blue cross, "Bell-ringer prank" with a pink square, as printed. **Neither button lights.** The dashed "draw the one you pick" ring is empty. The card is lifted away. |
| C4 | 42.0–43.0 | **Bolt 4 · die 4 · Probable · BLANK** | Die face 4 on bolt 4 (six o'clock). The empty lit stage. The bolt does not light. |
| C5 | 43.0–44.0 | **Bolt 5 · die 5 · Plausible · BLANK** | Die face 5 on bolt 5 (eight o'clock). The same empty lit stage. The bolt does not light. |
| C6 | 44.0–45.0 | **Bolt 6 · die 6 · Preposterous · BLANK** | Die face 6 on bolt 6 (ten o'clock). The same empty lit stage. The bolt does not light. |

Between the three blanks nothing changes but which die face shows, stepping clockwise. Do not fill the second of
silence with a gag, a ripple or a passing fish.

### D. The die is still in the cup (45.0 to 51.0 s) · on the table

| # | Time | Beat | Scene |
|---|---|---|---|
| D1 | 45.0–48.0 | The six bolts | Back on the table, the brass porthole front-on and centred, the pilot's pencil drawing faint inside it. The bolts are counted clockwise from the top, about 0.4 s each: **1, 2, 3 light** (warm, each with its small die face), **4, 5, 6 stay dark and empty**, their die faces grey. |
| D2 | 48.0–51.0 | The die not thrown | Beside the porthole, lower right: a leather die cup standing upright, one die resting inside, seen over the lip, not moving. The hand does not come. No caption (the sheet's "I rolled ___" is empty). Hold the three lit and three dark bolts and the still die to the last frame. |

## Captions the editor should end up with (times from film start)

```
( 9.0, 13.0, "The trout. The trout think the sub is a bell-ringer prank.")
(13.0, 16.0, "Freak out.")
(16.0, 20.0, "He is going to be turkey dinner.")
(23.3, 27.7, "The dinner bell to go off.")
(28.3, 33.7, "The dinner bell goes off and the fish go crazy.")
(34.4, 40.0, "The fish go quiet and calm.")
```

Six captions. Nothing from 40.0 s on.

## Module split for the scene units

- `scene_pilot.py`: A1 to A9, `SECONDS = 20.0`
- `scene_turkey.py`: B0 to B3, `SECONDS = 20.5`
- `scene_trout.py`: C0, C4, C5, C6, `SECONDS = 4.5` (no captions)
- editor: D1, D2 (6.0 s), badge, sound, joins. Total 51.0 s.

## Sound notes for the editor (nothing here adds words)

Pencil scratch through A1 to A6. One real or synthesized small brass bell: one late double strike in A7 and B1,
a crowding peal in B2, and in B3 the peal cut off dead when the clapper is held, then near silence with only a
muffled drumming from inside the tin. C is room tone only. D: three soft ticks as bolts 1, 2, 3 light, then none.

## Table: bolt, the child's sentence, the scene in one line

| Bolt | Die | Kind | Child's sentence (caption, as in `reads`) | Scene in one line |
|---|---|---|---|---|
| 1 | 1 | Probable | "The dinner bell to go off." | From Turkey's seat: the trout whose turn it is pulls the knot once, the bell kicks right and strikes, ripple rings cross the glass, both trout look at the tin; the dome rocks over Turkey's flapping reflection. |
| 2 | 2 | Plausible | "The dinner bell goes off and the fish go crazy." | From Turkey's seat: the bell goes off and a crowd of trout stampedes round the porthole rim nose to tail, belly-up and rolling-eyed but all clockwise, winding the bell up its twig; Turkey's wings a blur. |
| 3 | 3 | Preposterous | "The fish go quiet and calm." | From Turkey's seat: the wheel of trout stops one by one at the clock places, the last holds the clapper in its mouth, the ripples go back into the bell and nothing outside moves; only Turkey still shakes. |
| 4 | 4 | Probable | (blank) | River side: the tin, the arch and the still bell, lit and empty, about one second. Bolt unlit. |
| 5 | 5 | Plausible | (blank) | River side: the same empty lit stage, about one second. Bolt unlit. |
| 6 | 6 | Preposterous | (blank) | River side: the same empty lit stage, about one second. Bolt unlit. |
