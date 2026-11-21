# DON'T PAVE COW PATHS · the board

Director's plan (SCION laws 1, 2, 4). Every builder is held to this. 960x540, 24 fps, 120.0 s, under 12 MB.
Status of this document: a plan. Nothing in it has been rendered by the director. The only picture the
director looked at is `films/stills/cowpath_cast/pose_sheet.png` (the cow, ten poses, stills, not playback).
Nobody here can hear: the sound plan is written from the numbers, and no claim about how it sounds may be made.

    0.0 ───────── 36.0 ───────────── 76.0 ───────────── 116.0 ── 120.0
    ACT 1 shadow    ACT 2 pencil        ACT 3 cut paper      credit
    animation-02    animation-07        animation-48

Screen direction, whole film: **she travels left to right.** The thing she wants is always to the right.
The lead cow always faces right (`facing=1`). Nothing in the film ever travels right to left except a
builder fish going back to repair (3.4), which is why that turn reads.

---

## (a) Thesis

1. A cow wants to get to the water and the grass beyond it; what she gets instead, for two acts, is her own
   first hesitant wander made permanent, first by hooves, then by paving, then by herself at a desk approving
   whatever she has just done.
2. The film changes its material each time the way of working changes (black card that only repeats, a pencil
   line that can only be one hand, cut paper pieces that many can lay at once), and it changes its answer only
   when somebody who did not make the thing is allowed to say no.
3. The viewer should laugh at the paved kink round a tree that is no longer there, wince when she looks round
   for someone to check her drawing and finds only herself, and then feel a held breath let go when a fish that
   built nothing stops a builder, and the builder turns round.

**Defining passage: 3.4, the refusal, 94.0 to 104.0.** Ten seconds, almost no movement in the middle of it. A
slab rocks; the watcher blocks; the builder tries over, tries under, stops nose to flank; one second of stillness;
the builder turns back. Everything before it is built to make that turn land: Act 1 teaches that nothing here
ever turns back; Act 2 shows the same moment with no second party (she looks left, looks right, stamps);
beat 3.3 plants the dropped stone the repair will need. If only one passage in the film is good, it is this one.

**Competent but forgettable would be:** cows, a desk and fish each acting out a caption that is no longer there
(an illustrated slide deck with the slides removed); three style costumes with a cut between them; the refusal
shown by a mark (a cross, a red flash, a shake of the head) instead of by a body in the way; the fish as a tidy
synchronized ballet in which nobody is hasty and nothing is at stake; a cow who is a mascot, present in each
act but wanting nothing; even intensity from first frame to last; music running wall to wall under all of it.

Intensity is not spread evenly. Act 1 is slow and dry. Act 2 accelerates to the film's fastest passage (2.5)
and then drops to its quietest line work (2.6, 2.7). Act 3 is busy (3.3), then nearly still (3.4), then plain (3.5).

---

## (b) The bar: four tests a stranger applies with the sound off

No external reference film could be inspected here (Reiniger and Foldès are named in the method SCIONs but were
not watched by anyone on this production; say so in the validation record). The bar is therefore these four
observable tests, plus the measured gates below. Negative reference, inspectable: the rejected deck
`cowpaths.py` (a narrated slide deck). Positive material, inspectable: `films/stills/cowpath_cast/`,
`films/stills/c13_world/`.

**T1 · The same cow.** Hand a stranger three stills, one from each act (suggested: 8.0, 59.0, 108.0), with other
cows or fish in frame. Without prompting they point to the same animal in all three and say how they know:
one horn up, one crumpled forward, a bell under the neck. Fails if the horn or bell is under 10 px at
playback size in any of the three, or is hidden by staging.

**T2 · The kink.** A stranger watches 0.0 to 36.0 mute and is asked one question: "Why does the road bend
there?" pointing at the bend round the stump. Passing answer, in any words: because a tree used to be there /
because that is where the first cow went. Fails if they say "roads bend" or cannot answer.

**T3 · The refusal.** A stranger watches 84.0 to 104.0 mute, once, at normal speed, and can then say: which
fish did not build; what it found (a slab that rocked); that it said no and how (it got in the way); what the
builder did about it (went back, put a stone under); and that the answer then changed. Fails if any of the
five is missing, or if they report the refusal as a fight or as the watcher being mean.

**T4 · The difference, and the joins.** After one mute viewing of the whole film a stranger can say, unprompted
by text, what was different between how the cow's bad drawing got through (2.4) and how the fish's bad slab
did not (3.4); and when asked "where were the cuts?" does not name 36.0 or 76.0 as cuts (the path becomes the
pencil line; the leaves become the fish).

**Measured gates (structural, a builder may check these himself):** total on-screen words at most 20 and only
those in (d); no letters, numerals or signs anywhere else in any frame (see the forbidden list in (d));
duration 110 to 125 s; file under 12 MB; her hooves do not slide while planted (cast.py's own check);
the Act 1 final path and the Act 2 first line are the same polyline within 2 px; seven leaves, seven fish.

The bar does not move. If a test cannot be met, the beat is rebuilt or the failure is reported; the test is
not reworded.

---

## Shared contracts (all three acts)

**The lead.** `cast.py`, `style='shadow'` / `'line'` / `'paper'`. Facing right. Scale: Act 1 `s=0.55` on the
hill; Act 2 `s=1.0` at the desk (she is the picture); Act 3 `s=0.6` on the bank and the road. Other cows in
Act 1 have **two ordinary horns and no bell** (if the puppet cannot drop them, the herd is drawn smaller,
`s=0.45`, and the lead walks first and apart). Her habit, used in every act: before she commits to anything she
lifts her head and holds (`look_up`, 12 to 24 frames). The bell swings late (follower), and sounds only when
her head changes direction, never as wallpaper.

**The crooked path** (Act 1 set owns the smooth curve; these are the points it must pass within 12 px of;
if the set already exports a polyline with the same three features in the same order, the set's is canonical
and the Act 2 builder imports it rather than this list):

    PATH = [(120,170), (240,214), (292,246), (330,284), (374,290), (410,278),      # crest; UNDER the TREE (foot at 331,253)
            (452,290), (486,292), (520,296), (556,318), (596,352),                  # OVER the BOULDER (centre 500,329)
            (640,368), (680,384), (698,410), (678,436), (646,428), (642,400),       # the LOOP: she wheels away from the BOG
            (668,380), (716,382), (770,420), (840,455)]                             # (716,408), crosses her own track, on to the water
    STRAIGHT = [(120,170), (840,455)]                                               # where she first aimed

(Catmull-Rom through these points was plotted and looked at by the director: the sag, the bulge and a closed,
self-crossing loop all read at 960x540 with a 9 px band. Tree, boulder and bog all sit on `STRAIGHT`.)

Three features, in order, each caused by one visible event in 1.2 and 1.3: a sag **under** the tree's foot, a
bulge **over** the boulder, a small closed **loop** beside the bog. The loop is the signature: it must survive paving and be
recognisable as the last thing drawn on her sheet in 2.1.

**The stump.** The tree of Act 1 is felled in 1.5. Its stump (one flat cut, two root flares, about 46 px wide
at `s` of the set) is the "old roots" of 2.6. Act 1 set exports its profile; Act 2 draws the same profile in line.

**The approval mark** is her hoofprint (a cloven print, two half-moons). No tick, no cross, no word.

**Act 3 layout.** Water surface `y=170`. Air above it: pale, flat, cut paper. Left bank ends `x=180`, right bank
begins `x=780`, both cut paper, tops at the surface line. Bed about `y=480`. Six lanes, each 100 px wide,
`x=180..280, ... ,680..780`. Six slabs, 100 x 20, laid end to end with tops at `y=170`: together they are the
straight road. The c13 `river`, `weed`, `trout`, `bubbles`, `ripple_rings`, `put`, `Follower` are used.

**The fish.** Seven. Six builders (length 110 to 125, each a slightly different length, lid 0), numbered 1 to
6 by lane from the left. One watcher (length 170, `lid=0.45`, `amp` 2 when watching, carries nothing, ever).
Builder 4 is the hasty one.

---

## (c) The beats

Each beat: **W** who wants what · **D** what they do · **R** what resists · **C** what changes ·
**H** the hold · **L/A** the laugh or the ache. All of it is performance. No beat may be explained by a word.

### ACT 1 · THE COW PATH · 0.0 to 36.0 · backlit shadow theatre (animation-02)

Reiniger's terms: black card, pinned joints, tissue planes, contact on the ground. The hill is a sheet of amber
tissue between us and the light: mid-tone, facing us, sloping from the crest at upper left to the water at lower
right. **The worn path is the tissue worn thin: light comes through where hooves have been.** Paving is black
card laid over the light. Staged on 2s (12 drawings a second) except the fall of the tree, on 1s.

**1.1 · 0.0 to 3.0 · Light.**
Black. The lamp comes up behind the hill (0.0 to 1.5). Tree (black card, tall, a third of the way down), boulder,
a reed-fringed dip, and at lower right a bright strip of water with a tuft of far grass beyond it. Title
(see (d)) 0.8 to 3.0. No animal yet. **H** the empty unmarked hill, 2.2 to 3.0: the last time it has no line on it.

**1.2 · 3.0 to 9.5 · She aims straight.**
**W** the lead wants the water and the far grass. **D** she comes over the crest grazing (3.0 to 4.5), lifts her
head toward the water, **H** holds 18 frames (4.5 to 5.25), sets off straight down `STRAIGHT`. **R** the tree: at
7.0 she arrives nose to trunk and stops. **L** she waits 14 frames (7.0 to 7.6) for the tree to move; it does
not; one ear turns. **C** she goes round it below its foot, in front of the trunk (7.6 to 9.5). Behind each planted hoof a small
bright print stays in the tissue.

**1.3 · 9.5 to 14.5 · Two more detours.**
**R** the boulder: she tries to go over, a fore hoof slips (`startle`, small, 10.2), she backs one step and goes
round above it. **R** the bog: a fore hoof sinks to the knee (12.0), she hauls it out with her whole neck, wheels
away from it in a full small loop across her own prints (12.4 to 13.6) and passes it on the upper side. **C** she reaches the water at 14.0, lowers her head, drinks.
**H** 12 frames of drinking, 14.0 to 14.5: the only time in the act she has what she wanted. Her prints are now a
dotted wandering line from crest to water, and the straight way lies unmarked beside it.

**1.4 · 14.5 to 20.5 · The herd.**
**W** four cows want nothing but the cow in front. **D** they come nose to tail down her prints exactly.
**L** each one stops at the tree for the same 14 frames she did, though they are already going round it; the
fourth also turns the full loop at the bog on dry ground. **C** the dotted line joins up into a continuous
bright cut. Then compressed time: the lamp dims and returns twice (17.5 to 20.5), each return the herd is
further down and the cut is wider and brighter. The lead is among them now, bell swinging, walking her own loop.

**1.5 · 20.5 to 27.5 · The town, and the tree.**
**D** houses unfold along the cut (hinged roofs, 20.5 to 23.0), one after another from the crest down, each
facing the path, the row bending wherever the path bends. A spire last. At 23.0 two small human silhouettes
fell the tree: it falls on 1s, lands at 23.8 (the act's one loud event), is carted off right. The boulder is
broken and carted (24.5); the dip is filled by a tipped cart (25.0). **Nothing stands in the straight way now.**
**W** the lead, coming down with the herd, reaches the stump bend at 25.5. **H** she stops and looks along the
open straight ground, 24 frames (25.5 to 26.5): the film's first real stillness. She puts one fore hoof off the
path onto it (26.6). **R** a fence post rises under her nose, then a rail (26.8 to 27.2). **A** she takes the hoof
back and goes round the stump. The herd behind her never looked.

**1.6 · 27.5 to 33.0 · Paving.**
**W** the two pavers want the job done. **D** with a hand roller and a barrow they lay black setts over the
bright cut from the crest down, at walking pace, never once looking up from the line. **L** at the bog loop
(31.0 to 32.2) the roller goes faithfully all the way round the loop, the paver walking backwards round it,
on flat filled ground. **C** the cut of light becomes a black band with a hair of light on each kerb.

**1.7 · 33.0 to 36.0 · The hold and the hand-over.**
The lead stands at the bottom end where the paving stops at the water. She looks across at the far grass
(`look_up`, 33.0 to 34.0), bell once. Houses, hill and cow sink into black from 34.0 while the lamp whitens
toward cream; only the paved band keeps its shape. **H** 35.0 to 36.0 the crooked path alone, sag, bulge and loop,
dark on a light ground. At 36.0 it has thinned to a line 3 px wide: it is graphite.

### ACT 2 · THE ONE DESK AND THE GRAFT · 36.0 to 76.0 · pencil on paper (animation-07)

Foldès' terms: key contour drawings, point correspondence, in-betweens that keep a shape recognisable long enough
for the change to be felt. No dissolves: every change in this act is the line moving. Cream paper, graphite,
nothing else, until the last second. Contours come from `cast.outline` (n-point, evenly spaced) so they can be
paired point for point.

**2.1 · 36.0 to 39.5 · The line is hers.**
The path line shrinks and settles (36.0 to 37.5) onto a sheet of paper on a desk: it is a drawing, and a
pencil under a hoof is just finishing the bog loop. Around the sheet the rest of the frame draws itself in,
contour first: the lead, seated (`draw_pose`), bell at her neck, crumpled horn forward; desk; to her right on the
floor an empty tray; on the desk, left to right, a second sheet, a pot with a brush, a lever on a post (the
camera), nothing else. **H** 38.8 to 39.5 she looks at her line, pleased, ear flick, bell.

**2.2 · 39.5 to 49.5 · Every job, once, properly (2 s each).**
**W** she wants to make the picture, all of it. **D** five jobs, each a distinct body:
draw (39.5): head low, the hoof pulls one stroke, the head follows the pencil;
in-between (41.5): she lifts the sheet over a second, flips it three times, head ticking between the two;
paint (43.5): brush in her mouth, dip to the pot, one wide pass, a drip she chases;
camera (45.5): she half stands, both fore hooves on the lever, pulls: the whole frame blinks grey for two frames;
check (47.5): she sits back, narrows her eye (`eye=0.3`), tilts, and brings the hoof down (`stamp_pose`): a
hoofprint in the corner. The sheet slides off into the tray. **C** one sheet in the tray. She is content.

**2.3 · 49.5 to 55.5 · Twice more, faster.**
The same five, in 4 s (49.5 to 53.5), then in 2 s (53.5 to 55.5). **R** time: the anticipations go first, then
the follow-throughs; the brush stays in her mouth while she pulls the lever; sheets stop landing square.
**C** the tray overflows; the pile is at desk height by 55.5. **L** in the 2 s round she stamps before she has
finished looking.

**2.4 · 55.5 to 61.0 · The bad drawing.**
Insert, the sheet filling the frame (55.5 to 57.5): her drawing of a walking cow, in which the hindquarters
have come away from the barrel (a clear gap of paper, the hind legs striding on their own, and a fifth leg under
the belly). It must be wrong in contour, legible at a glance, and funny. Back to her (57.5). **H** she has
stopped: the first stillness since 39.5, 18 frames (57.5 to 58.25). **W** she wants someone to say.
**D** she looks left (58.25): paper. Looks right (58.9): paper. **A** nobody, 12 frames each. She looks at her
own hoof (59.5). **L** stamps it (60.0), the print landing squarely across the gap, as if that joined it.
The sheet goes on the pile. **C** from here she does not look at anything again.

**2.5 · 61.0 to 65.5 · Drowning.**
The film's fastest passage. The five poses as replacements on 2s, then on 1s, with no in-betweens at all (the
line jumps); sheets leave the desk in a fountain; the pile's contour climbs past the desk (62.0), her
shoulder (63.2), her muzzle (64.2). At 64.6 only the crumpled horn, the good horn's tip and the bell stand
above the paper. The stamping stops. **H** 64.6 to 65.5: a heap, a horn, a bell that swings once, late, and hangs.
**A** this is the lowest point of the film. Nothing moves for the last 12 frames.

**2.6 · 65.5 to 71.0 · The cut and the graft.**
The line transforms; this is the Foldès proof. The heap's contour settles, point for point, into the hill
and the stump from Act 1 (65.5 to 67.5; the stump must be recognisable by 67.0 and the heap still
recognisable at 66.2). She stands behind the ground line now, head and neck clear (`style='line'`), the worn
pencil stub in her mouth. **W** she wants one thing to be right. **D** she draws the stub once, hard, across
the stump's rim (68.0): a wedge point, one shaving curls off: that is the cut. The stub's contour lengthens
and knuckles into a shoot with two buds (68.0 to 69.0, the wedge end unchanged throughout: it is the pencil
point and it is the scion's wedge). She sets the wedge into a cleft in the stump (69.3, contact: the stump
line gives 2 px and closes on it). The path line, still lying on the last sheet at her feet, lifts and winds
three turns round the join as binding (69.5 to 71.0). **C** the crooked line is used up; it never appears
again in line.

**2.7 · 71.0 to 74.5 · Whether it takes.**
**W** she wants it to live. **D** she stands and watches it. **R** nothing happens. **H** 36 frames of a cow
and a stick, 71.0 to 72.5; the only movement is the bell settling. She lowers her head (toward `slump`, 72.5 to
73.2). **C** behind her gaze the upper bud opens. Her ear turns first (73.3), then the head comes up
(`look_up`, 73.6). Leaves unfold from both buds, each a single closed contour, **seven by 74.5**. **A** the
ache is the wait; the release is the ear.

**2.8 · 74.5 to 76.0 · Leaves loosen (hand-over).**
The seven leaves let go one at a time, stem end first (every 4 frames from 74.5), and slide down to the right
past her nose; she watches them go. Each leaf contour fattens point for point into a fish contour (stem
becomes tail, tip becomes nose), six small and one larger. From 75.0 the paper cools from the top edge down,
cream to river teal, and the ground line rises to become the water surface at `y=170`. At 76.0: seven drawn
fish in water, her legs on a bank at upper left.

### ACT 3 · THE FISH AND THE ROAD · 76.0 to 116.0 · cut paper under water (animation-48)

State-machine terms: each fish has states, guards and memory, and what it does next depends on what it sees.
Builder: `fetch → carry → set → (next stone) → done → join`. Watcher: `watch → survey → watch → test → (firm: next
slab | rocks: block) → retest → yield`. Guard on `yield`: the slab does not rock when nudged. Nothing in the
refusal is scripted as a mood; it follows from the slab. Fish are on 1s, drifting; the cow above is on 2s.

**3.1 · 76.0 to 80.5 · The water's edge.**
The drawn fish are laid over by the cut-paper trout (by 77.5); the c13 river comes up behind them. Above, on
the left bank, the lead in cut paper, at the end of the paved crooked road, which stops at the water (a few
black setts, the last kerb). **W** she wants the far grass, lit, on the right bank. **D** she puts a fore hoof
in (78.0): rings spread on the surface, seen from below. **R** deep water: no bottom under the hoof; she
draws it back (78.6). **H** she looks straight across, 24 frames (79.0 to 80.0). The seven fish look up at the
hoof, then turn, one after another, to look where she is looking. **C** for the first time somebody other
than the cow is looking at where she wants to go.

**3.2 · 80.5 to 84.0 · The line is asked for.**
The watcher (largest, half-lidded) swims once, slowly, bank to bank just under the surface, exactly level,
leaving a string of bubbles that hangs for a moment as a straight line (81.0 to 83.0). **H** the bubble line
alone, 83.0 to 83.5: straight, where Act 1's line was crooked. The six builders drop, each into its own lane
under the line. The watcher returns to the left bank, turns to face right, and stops moving.

**3.3 · 84.0 to 94.0 · Six at once.**
**W** each builder wants its own span up. **D** all six work at the same moment, each in its own lane, never
entering another's: nose a stone off the bed, carry it up, set it, three stones to a pier, then a slab on
top at the surface. They are staggered by a few frames and they are not alike:
1 sets each stone and taps it twice; 2 is slow and never drops anything; 3 copies 2, a beat late;
**4 is quick: it carries two stones at once, drops one at 87.0 (it comes to rest on the bed in lane 4 and
stays in frame until 102), does not go back for it, and builds a pier of two**; 5 keeps looking across at 4;
6 is smallest and works hardest. **R** weight: a carried stone drags each fish's nose down; setting one pushes
the pier 2 px. 4's slab is on at 90.0, the first; **L** it turns a loop of pleasure (the same shape as the
bog loop) while the others are still carrying. The rest finish between 91.5 and 93.5. The watcher has not
moved; only its eye has. **C** at 93.5 six slabs lie end to end from bank to bank. It looks finished.
**H** 93.5 to 94.0.

**3.4 · 94.0 to 104.0 · The refusal. DEFINING PASSAGE.**
**W** builder 4 wants to be done and in the school, which is gathering at the right bank. The watcher wants
to know. **D** the watcher goes along under the road from the left and nudges each slab from below with its
nose: slab 1 (94.5) firm; slab 2 (95.5) firm; slab 3 (96.5) firm: an even pulse, one a second. Slab 4 (97.5):
**it rocks**, see-saws twice on its short pier, and a pebble falls. **H** the watcher stays under it, 20 frames
(97.8 to 98.6). Builder 4 is crossing toward the school. The watcher turns broadside across its way (98.6).
**R** 4 tries over (99.2): the watcher rises. Tries under (99.8): the watcher sinks. No contact, no chase,
no anger: the watcher's lid and speed do not change. 4 stops nose to flank (100.2); its tail slows and stops.
**H** one full second, 100.2 to 101.2, the stillest in the film: two fish, the five others turned to look, the
cow's legs waiting on the bank above. **A** this is the look-left, look-right of 2.4, and this time someone
is there. **C** 4 turns round (101.2): the only right-to-left movement in the film. It dives to the stone it
dropped, noses it up, wedges it onto the short pier (102.6), shoulders the slab level. The watcher nudges
slab 4 again (103.2): firm. Its lid lifts all the way, once (103.4). It sinks out of the way. 4 passes
(103.6 to 104.0); the school opens to let it in. The watcher goes on to slab 5.

Not permitted in this passage: any mark, symbol, colour flash, head shake, bubble with anything in it, camera
move, or cut. One fixed frame for ten seconds. If it does not read, change the staging or the timing.

**3.5 · 104.0 to 112.0 · The road.**
Slabs 5 and 6 firm (104.4, 105.0), the pulse resumed. **W** the lead wants to cross. **D** she sets a fore hoof
on slab 1 (105.4). **H** 10 frames with the weight not yet on it. It holds. She walks: straight, level,
rightward, hooves planted on the slabs, seen from the side above the surface with the piers and fish beneath;
each slab dips 1 px and comes back as she loads it. **R** at slab 4 (108.2) she stops and lifts her head, as
she always does; builder 4, directly beneath, stops too. She puts her weight on. It does not rock.
4's tail starts again. **C** she steps off onto the far bank at 111.0 and puts her head down into the grass.
The crooked path took the whole of Act 1; this took six seconds.

**3.6 · 112.0 to 116.0 · What is left.**
**H** the last picture, held: far left, small, the end of the black paved road with its loop; across the middle
the straight road at the waterline; right, the cow grazing, bell still. The builders drift apart the way the
leaves fell. The watcher stays where it is, under slab 4, lid at half again, watching. No one celebrates.
Bell once at 115.0.

**Credit · 116.0 to 120.0.** The water darkens by half; the picture keeps moving faintly; the credit of (d).

---

## (d) Words on screen: 16 of the 20 allowed

| When | Where | Words | Count |
|---|---|---|---|
| 0.8 to 3.0 | lower left over the dark foot of the hill, baseline about y=470, cut as light through the black (amber letters, serif, about 44 px), one line | `Don't Pave Cow Paths` | 4 |
| 116.4 to 119.6 | centred, two lines, serif about 22 px, pale on the darkened water, baselines about y=262 and y=294 | `SCION: a name borrowed from Anthropic's source control.` / `Not an Anthropic film.` | 12 |

Four words are left unused on purpose. No spoken lines. No murmur either.

**Forbidden, because they carry letters, numerals or labels:** from c13 `badge`, `pick_card`, `speech_bubble`,
`die_face`, `bolt_mark`, `sheet_ring`, `pilot_page`, `pilot_drawing`, `tin` and `tin_porthole` (the tin has a
printed label), `gauge`. From the kit: `caption`, `label`, `card`, `clock`, `door(sign=)`. Nowhere: shop signs,
numbers on houses, arrows, ticks, crosses, question marks, exclamation marks, thought bubbles, page numbers on
her sheets, lettering on the stamp. Her sheets carry drawings and hoofprints only.

---

## (e) Sound plan

Built with the kit's `Mix` only. **Nobody on this production can hear it.** Timings below are tied to picture
events; whether it sounds right is UNKNOWN until a person listens, and must be reported as such.

One tune carries the film, in D pentatonic: `D4 293.7, E4 329.6, F#4 370.0, A4 440.0, B4 493.9, D5 587.3`.
In Act 1 it wanders; in Act 2 it is ground up; in Act 3 it is played straight for the first time.
Her bell: `mix.bell(freq=740, seconds=0.9, gain 0.2)`, panned to her x. It rings only where listed.
Music never runs under a hold marked silent.

| Time | Picture | Sound |
|---|---|---|
| 0.0 to 3.0 | 1.1 lamp up, title | `wind` very low from 0.0; nothing else. Title is silent. |
| 3.0 to 9.5 | 1.2 she aims straight | hoof steps (`step`, gravel, on her plants). Bell at 4.5 as her head comes up. At 5.25 the tune starts straight up the scale on `pluck`, D E F# ... and breaks off on F# at 7.0 when she meets the tree. Silence 7.0 to 7.6. It resumes with a detour note (E, back, then on). |
| 9.5 to 14.5 | 1.3 boulder, bog, water | slip: `click` 10.2. Bog: low `thud` 12.0, a wet `step(water)` as the hoof comes out. The tune goes round a three-note turn at the loop (A F# A). At 14.0 `water` fades in; tune stops; drinking is water only. |
| 14.5 to 20.5 | 1.4 herd | four sets of steps, the wandering tune now complete with its three detours, repeated, each repeat a little louder; a low `drone` (D2, A2) swells and falls with each dimming of the lamp. |
| 20.5 to 27.5 | 1.5 town, tree | a `click` per roof unfolding, rising in pitch down the row. Sawing: two `whoosh` strokes 23.0 to 23.5. Tree lands: `thud` 23.8, the loudest event in Act 1, then 12 frames with nothing. 25.5 to 26.5 her look along the straight: **silence** but wind. 26.6 one pluck of the straight scale's next note (A4); 26.8 fence post: dry `click`; the note is not followed. |
| 27.5 to 33.0 | 1.6 paving | the wandering tune again, now on `note(square)`, stiff, in strict time, with a `step(stone)` on every beat (setts going down); the three-note turn played with full solemnity at the loop, 31.0 to 32.2. |
| 33.0 to 36.0 | 1.7 hold | tune ends unresolved on E. Bell at 33.4. Wind thins to nothing by 35.0. 35.0 to 36.0 **silence**. |
| 36.0 to 39.5 | 2.1 the line is hers | `room` tone in at 36.0. Pencil: band-passed noise shaped to the stroke (gain follows pencil speed), ending with the loop. Bell at 39.0. |
| 39.5 to 49.5 | 2.2 five jobs | each job has one sound, and they are five notes of the tune: draw = pencil scratch + D; in-between = three paper flips (`whoosh`, 0.08 s) + E; paint = a soft wet `step(water)` + F#; camera = `click` then `thud` (lever) + A; check = stamp `thud(freq=110)` + B. Sheet into tray: `whoosh` 0.2 s. |
| 49.5 to 55.5 | 2.3 faster | the same five sounds at double, then four times the rate: the tune is now recognisably the wandering one, speeding. Notes begin to overlap. |
| 55.5 to 61.0 | 2.4 bad drawing | everything cuts off at 55.5. Insert: room tone only. 57.5 to 60.0: room tone, and her bell twice, at each turn of the head (58.25, 58.9), small. 60.0 stamp: the `thud`, with a B that is a quarter-tone flat. |
| 61.0 to 65.5 | 2.5 drowning | the five sounds as fast as they will go, pitch order lost, paper `whoosh` thickening into continuous noise that rises to 64.6, then cut to nothing. 64.9: the bell, once, low-passed to 600 Hz (under paper). **Silence** to 65.5. |
| 65.5 to 71.0 | 2.6 cut and graft | no room tone now: a quiet `wind`. The line's settling is a single low `drone` note falling a fifth. The cut at 68.0: one long hard pencil rasp, the only loud thing. The set at 69.3: a small wooden `step(wood)`. Binding: three soft `pluck`s, D E F#, one per turn: the straight scale's first three notes, slow. |
| 71.0 to 74.5 | 2.7 waiting | wind only, 71.0 to 73.3, and the bell settling at 71.2. Bud: one `pluck` A4 at 73.3 with her ear. Leaves: seven very light plucks, B D5 and up, 73.6 to 74.5. |
| 74.5 to 76.0 | 2.8 leaves loosen | the seven plucks again, falling; `water` fades in under them from 75.0; wind out. |
| 76.0 to 80.5 | 3.1 water's edge | under water: `water` low-passed to 900 Hz, plus a low `drone`. Hoof in at 78.0: `step(water)` and a `thud`. Hoof out 78.6. Bell at 79.0, heard from below (low-passed). Her look, 79.0 to 80.0: water only. |
| 80.5 to 84.0 | 3.2 survey | one held `note(sine)` D4, very quiet, for exactly as long as the watcher swims the line (81.0 to 83.0): the first long straight sound in the film. Bubble line: nothing. |
| 84.0 to 94.0 | 3.3 six at once | each builder has one pitch of the scale (lane 1 = D4 ... lane 6 = D5) and one sound: a stone set is a `pluck` at its pitch, panned to its lane. Six lanes at once make a loose, overlapping, cheerful figure that is not yet a tune. Builder 4's dropped stone, 87.0: a dull `thud` on the bed, and lane 4 has one pluck fewer than the others (two, not three). Slab on: a lower octave of the lane's pitch. 4's loop at 90.0: the three-note turn from the bog, fast. 93.5 to 94.0 quiet. |
| 94.0 to 104.0 | 3.4 refusal | the test: each nudge sounds the slab, a `bell`-like pluck at its lane pitch, D (94.5), E (95.5), F# (96.5): the scale, straight, in time. Slab 4 (97.5): **the A is wrong**: 415 Hz, with a wooden double clack as it rocks, and the pebble's `click`. Then nothing. 97.8 to 101.2: water only, no drone, no note; at 99.2 and 99.8 only the soft `whoosh` of each fish moving. 100.2 to 101.2: **the quietest second in the film** (water at half gain). 101.2 the turn: no sound for it. 102.6 the wedge: one firm `step(stone)`. 103.2 retest: A4, 440, true, ringing longer than the others. 103.4 the lid: nothing. 103.6: the school's six pitches, once, softly, as 4 joins. |
| 104.0 to 112.0 | 3.5 the road | 104.4 B, 105.0 D5: the scale completed. Drone returns. 105.4 her hoof on slab 1: `step(stone)` above water (bright, no low-pass) + D4. Her crossing: each slab sounds its note as her weight comes on it: D, E, F#, then at slab 4 (108.2) a rest of 10 frames, then A, true, then B, D5. **This is the tune played straight, once, by her feet.** Bell at 108.2 as she lifts her head. 111.0 soft `step(gravel)` onto the bank. |
| 112.0 to 116.0 | 3.6 what is left | water, the drone thinning. Her grazing: nothing. Bell at 115.0, unfiltered, left to ring out. |
| 116.0 to 120.0 | credit | water alone, fading from 118.5; silence by 119.6. |

Reverb: one light `mix.reverb(0.15)` over the whole, or none. Do not use the drone to hold up a beat whose
picture is not working.

---

## Who is accountable for what (law 4)

| Problem | Owner | Reads | May not change | Deliverable that can be opened | Accepted when |
|---|---|---|---|---|---|
| The lead cow | puppet builder (`cast.py`) | this board's "The lead" | her two marks; facing right | pose, walk and material sheets in `films/stills/cowpath_cast/` | T1 on those sheets at `s=0.55` and `s=0.6`; hooves do not slide (measured) |
| Act 1 set, path, stump | sets builder | PATH, 1.1 to 1.7 | the three features and their order; the loop | stills of the bare hill, the worn hill, the paved hill | a stranger traces the path with a finger on the paved still and finds the loop |
| Act 1 study | animation-02 builder | 1.2 and 1.5 first (tree, then the kink with no tree) | timings of holds | a playable 0.0 to 36.0 with sound | T2 by a critic who has not read this board |
| Act 2 study | animation-07 builder | 2.4 and 2.6 first | no dissolves; pencil point = wedge | a playable 36.0 to 76.0 with sound | critic names the five jobs mute; heap, stump and shoot each recognised at the stated times |
| Act 3 study | animation-48 builder | **3.4 first, before anything else in the act** | fixed frame; no marks; guard on `yield` | a playable 84.0 to 104.0 with sound, and the decision trace of the watcher | T3 by a critic who has not read this board |
| Assembly, hand-overs, mix | whoever assembles | everything | this board's times at 36.0, 76.0, 116.0 | one mp4, 120.0 s | T4; measured gates; a whole-film critic with fresh context |

The hardest passage is 3.4 and it is built first. If 3.4 cannot be made to pass T3, the film is reported as
not finished; Acts 1 and 2 do not make up for it.

No builder passes his own beat. Stills are not playback: a claim made from stills is labelled as made from stills.
