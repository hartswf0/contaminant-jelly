# Games that make films, films that run games

Working chapter outline, with an account of how the SCION prompts worked in the Tourkey Trouttown productions.
Written from the repositories (`contaminant-jelly/paeleo/trout-sub`, `turkey-sub`, `bolas/paeleo/scion`,
`elsewhere`). The five YouTube links could not be opened from this environment, so nothing here describes them
except `ooiBjWKV8vQ`, which is an earlier cut of the Tourkey Trouttown film.

## Part 1 · The prompts we used, and what each one is

| Set | Count | Where | Addressed to | What it asks for |
|---|---|---|---|---|
| Episode SCIONs | 6 | `scions.json` | an operator and a class | one room, kit, crossing, die beat, memory, town; each with a proof a child can check |
| Animation SCIONs | 54 | `drawn/scions.json` | an autonomous animation swarm | one technique proved in one hard scene (cutout, shadow theatre, multiplane, occlusion, rigs, archives) |
| Oulipo and Ouxpo SCIONs | 42 + 1 compiler | `bolas/paeleo/scion/oulipo/prompts` | a production swarm | one constraint from literature or film turned into a testable screen rule |
| Feedstock cards and shot prompts | 18 cards, 116 shot prompts | `feedstock/`, `prompts/`, `prompts2/` | a video model | a look (the card's LAW) and two locked shots per porthole |
| Production briefs | 4 | `hand/BRIEF*.md`, `hand/films/BRIEF-2-oulipo.md` | the agents that ran | what is allowed on screen, whose words are fixed, what counts as done |
| Swarm scripts | 3 | `hand/swarm-*.js` | the orchestrator | which unit does what, in what order, with what handed on |
| Multiplane Animation Studio | 1 | `elsewhere/studio.html` | a drawing agent | draw, look, compare, adjust, draw again; a cartoon is differences between drawings |

### The shape every SCION shares
All three SCION sets use one skeleton, in eight to ten numbered sections:

1. **Assignment and inputs**: bracketed slots (`[WORK]`, `[DIRECTION_AND_REFERENCES]`, `[BUDGET]`, `[AUTHORIZATION]`).
2. **Creative thesis**: one sentence the finished thing must make true ("Draw one room that can be operated").
3. **Lineage and primitives**: where the method comes from, and the things that must stay typed and separate
   (layers, an occlusion order, a glyph path) instead of being flattened into pixels.
4. **Invariants and branches**: what may not change, and what forks.
5. **Swarm assignments**: named working roles, each owing a concrete artifact, plus one critic who did not build.
6. **Hard proof**: one short scene that would show the method failing if it fails.
7. **Fixture and independent criticism**: a check that can be run, and a viewer's verdict in three words
   (pass, reference stronger, inconclusive) with exact frames.
8. **Repair and recursive inquiry**: change one cause at a time; after two failed repairs, state two explanations.
9. **Deliverable and start**: what is handed over, and an instruction to begin.

The animation set appends a fifteen-point "inherited operating doctrine" (hard proof first, the builder cannot
approve its own work, label every claim measured, structurally verified, perceptually judged or unknown).
The Oulipo set adds a Lineage Genome, a recursion limit (TTL) and a common seed: the station, the envelope,
the key, the door that stays closed.

## Part 2 · How the SCIONs actually worked in our runs

This is the evidence the chapter can stand on, including what did not happen.

**No agent ran a SCION prompt whole.** In every production the SCION reached the agents at one of three strengths:

- **As a rule, one line long.** Each porthole in `seeds.json` carries a rule. 40 of 55 name an animation SCION
  (27 different ones: "Single Hinge (SCION 13): jaw pivot"); the other 15 name an Ouxpo constraint
  ("Lipogram (Outypopo): washed chalk"). The rule shaped how things move in that porthole's film.
- **As a method the story unit chose.** Each board picked two or three animation SCIONs and said where they
  apply. The finished films record: shadow theatre (2), metamorphosis (7), secondary motion (13), forward
  kinematics (32), drawing substitution (39), secondary dynamics (41), multiplane (44), occlusion (45),
  Whitney harmonic motion (6), the print stage (50), tabletop capture (40).
- **As doctrine folded into a brief.** The parts of the SCION skeleton that every run obeyed were carried by
  the briefs and scripts, not by the SCION text: roles became units, the hard proof became a contact sheet
  the maker had to look at, the independent critic became a critic unit that may not edit, invariants
  became assertions in code, and the evidence labels became lines such as "sound unheard" in the notes.

**What survived contact with production**
- Roles into units: story, world, three scenes, editor, critic, rights, repair.
- Invariants into assertions: the class films fail to run if the captions are not the children's 34 sentences.
- Independent criticism: the critic units found real faults (pick lines captioned as if children wrote them;
  a die that read as thrown) and the repair units fixed them.
- Honest evidence: every note says what is foraged, what is handmade and what is weak.

**What did not**
- The Lineage Genome, the Olog, TTL and the operator page were never produced.
- Numeric invariants were rare; almost all judging was by looking at stills.
- Nobody, human or agent, has judged the sound.
- One rule label drifted: a film cites "36 temporal double", but SCION 36 in the catalogue is an auto-rig method.

**How the runs failed, and what each failure taught**
- *Style costume.* Early films imitated a reference's look with filters and shaded stick figures. They were
  rejected, and the rule "handmake or forage, no style costumes" replaced them. A SCION's lineage section
  invites costume unless the brief forbids it.
- *A swarm in name only.* One maker and one critic per film was called a swarm until it was challenged. The
  nine-unit version produced visibly better films from the same sheets.
- *The critic is the first thing to go.* When usage ran out, all five making films lost their critic and
  repair passes and one lost its editor. The films exist; their truth to the sheets is unchecked.
- *The video model drifts.* 63 generations (58 cheap, 5 hero) gave footage in which the porthole wandered.
  Holding it still took a separate tracker and re-framing after the fact, and the budget ended the run.

**The contrast the chapter turns on**

| | Text to video model | Text to code to video |
|---|---|---|
| The prompt is | a description of a shot | an instruction to a maker |
| The model returns | pixels | a program that draws every frame |
| Control | reference images, then repair after the fact | rules stated before, asserted during |
| Can be inspected | only by watching | by reading, running and watching |
| A child's sentence is | a hope | an invariant |
| In this project | the 55-porthole film | the hand films, class films, making films |

## Part 3 · The philosophy, and where this stone sits

Read against `burning-house` (*The Ledger and the Curtain*, `CLAIMS.md`, the PAE ladder), Tourkey Trouttown is
not a side project for teachers. It is the next rung of the same ladder, and it is the first rung on which
somebody other than the maker wrote back.

**The ladder so far**

| Rung | Who is inside the rules | What was shown |
|---|---|---|
| The Threshold | one paper dog | a state name has to become a visible gesture (stillness as refusal) |
| The Flour Tower | one sack, six formal languages | one score, six lineages, a critic who did not build |
| VTX-0.1 | two sacks, one lamp | one changed line of intention, 46 causal paths |
| The Abominable House | four sacks, twelve deeds | four formal accounts that refuse to agree |
| **Tourkey Trouttown** | **one turkey, a river of trout, and a class of nine-year-olds** | **readers who wrote back: five pages, 34 sentences** |

The meta-essay ends by asking for a world "explicit enough to give a consequential answer" that leaves the
reader "room to pause the frame, test the rule, check the angle, and write back." In the burning house that
reader is still hypothetical: claim C13 stands open with no human ballots. In Trouttown the page says
"Pass your paper left", and three children did. That is the stepping stone: from an instrument that
invites an answer to one that received it, and then had to decide what to do with the answer.

**Six ideas from the burning house, as they land here**

1. **Against the smooth machine.** The smooth machine erases the joint where a decision happened. This
   project met it three times. The video model let the porthole drift until a tracker pinned it back. A
   chat model, shown the children's pages, filled in their blank newspaper lines and then offered "more
   kid ways" to write them: it smoothed the children. And my own tidied captions smooth their spelling,
   which is why the making films put "freek out" and "panit" back on the page in pencil.
2. **Waldemar's split mind, in a fourth grader.** Calvino's programmer is half building an algebra of
   interchangeable slots and half running "a mental film packed with fades and metamorphoses". The
   worksheet asks a child to do both at once: fill a form, and picture what a fish sees. The class films
   show the film half. The making films show both halves in one shot: the page is the ledger, the dive
   through the drawn ring is the mental film, and the return to the desk is the joint between them.
3. **The three ALAMO levels are visible in the children's handwriting.**
   Level 1, recombination: a friend picks one of two printed options and its button.
   Level 2, mold filling: sentences that carry on from the printed stem ("the trout to run") show a child
   filling a grammatical mold. Level 3, plot implication, where one scene changes what is possible in
   the next: the pages barely reach it. Nobody rolled the die, and almost no ending depends on another.
   The films reach it only because I told the story units that the pilot's first page must colour every
   later scene. That was the editor's addition, not the children's, and the chapter has to say so.
4. **Readers that do not commute.** The house sets stage, ledger, minds and insurer side by side because
   their disagreements show what each cannot see. Trouttown builds the disagreement into the fiction:
   what Turkey thinks and what the trout think are both right, and the order of the pass matters. "Check
   the angle" is literal here: the same porthole from the seat and from the river.
5. **Two kinds of absence.** A blank line is an empirical absence: a child ran out of time or did not
   know, and nobody can supply that afternoon. The unthrown die, the hands without faces, the pages never
   shown and the first initials are authored refusals, the same move as four faceless sacks and a drawn
   curtain. Filling a blank is the one thing the films are forbidden to do, and it is the first thing a
   smooth machine did.
6. **The accountable clinamen.** A swerve somebody chooses and answers for. The children's are on the
   pages: a second jaw drawn outside the ring, an option circled instead of drawn, a button coloured in,
   "Trying to save a hot Cheeto", "It is not wet". A nine-year-old cannot be asked to defend a swerve, so
   the adult's duty changes from answering for an exception to keeping it and saying whose it is. My own
   swerves need a ledger too: dropping the faint "the sub." on porthole 13, choosing tidied captions,
   making page one govern the endings.

**What this does to the claim.** The earlier version said a SCION prompt makes a film checkable. The
stronger version: a worldtext is tested when someone who did not make it acts inside it and their
action has to be carried forward without being smoothed. Games that make films are that test. The
game produces answers; the film is where the maker shows what was done with them.

**A claims ledger for this rung** (after `burning-house/CLAIMS.md`)

| | Claim | Status | What would settle it |
|---|---|---|---|
| T01 | Every caption in the class films is a child's sentence, in order, with blanks kept | measured | none: asserted in code and checked by hand against the transcripts |
| T02 | Every struggle shown in the making films is on the page | open | re-run the critic units, or check each film against its photographs |
| T03 | The voices and mix are intelligible | open | no person has listened |
| T04 | The pilot's page colours the later endings | editor's addition | mark it as such; compare with a cut that does not impose it |
| T05 | Children took another creature's point of view | open | nothing measured; needs a design and ethics approval |
| T06 | The films can teach the game to a new class | open | a second class playing from the film alone |
| T07 | The SCION text adds something the briefs do not | open | one SCION run whole on one page, compared with the brief-driven film |
| T08 | Transcription is faithful | partly | three readings are marked unsure; a second reader should check the photographs |

## Part 3b · Chapter outline

**Working title.** The House With Children In It: games that make films, films that run games.

**Claim.** A worldtext is tested when a reader who did not make it writes back and the answer has to be
carried forward unsmoothed. Tourkey Trouttown is that test at the scale of one class. It shows what a
constitution of prompts can hold fixed (words, order, blanks, sources), what it cannot (sound, kindness,
truth to a child's struggle), and what the maker added.

1. **A page is passed.** Porthole 13: a fish that says "haha verry funny"; a friend writes three endings
   for a dinner bell; the next friend writes nothing. Then a film that keeps the nothing.
2. **Against the smooth machine, again.** The three smoothings above. Friction as the place where a
   decision shows. Operative ekphrasis and thick prompting as the frame.
3. **From the burned house to the river.** The ladder; Calvino's twelve deeds become *Trouttown: Twelve
   Deeds*; what changes when the cast is children and the reader really answers.
4. **The form of a SCION.** Thesis, primitives, invariants, roles, hard proof, fixture, independent
   critic, repair. Its debts to Oulipo and to the animation studio. How it reached the agents (Part 2).
5. **Two ways a language model makes a film.** Description to pixels; instruction to a program. The
   55-porthole film against the hand films. The costume failure.
6. **Mold filling in pencil.** The three ALAMO levels read off five pages. Where the children's work
   stops and the crew's begins.
7. **The sentence as invariant.** The class films: 34 sentences, blanks kept, the die unthrown.
8. **The split mind on screen.** The making films: ledger and mental film in one shot; hands without
   faces as authored refusal; what was not verified.
9. **Two absences and a ledger.** Blank lines and refused pictures; the claims table; every swerve
   attributed to its maker.
10. **The loop.** A game that makes films and films that run the game. The second class as the next stone.
11. **Limits.** One class, five pages, no measure of learning, no human listener, no consent on record.

## Part 4 · What the chapter still needs

- **Ethics approval.** If the children's pages or films are to appear in a dissertation, check with the IRB
  and the school now. Nothing in the repositories records consent.
- **A person watching with the sound on.** Every film's audio is unjudged.
- **The missing reviews.** Re-run the critic and repair units on the five making films, and check each
  struggle shown against the page.
- **One SCION run whole.** Give one agent a complete SCION prompt for one porthole and compare the result
  with the brief-driven film of the same page. Without this the chapter cannot say what the SCION text
  itself contributes beyond the briefs.
- **A second class.** Play from the teaching film alone and collect the pages. That is the loop turning.
- **The other animation work.** The four linked videos and the wider Trout Town material need describing
  from the videos themselves: title, how each was made, which prompts.
