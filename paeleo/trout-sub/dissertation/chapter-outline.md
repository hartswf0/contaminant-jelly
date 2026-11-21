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

## Part 3 · Chapter outline

**Claim.** A SCION prompt is a production constitution: it makes a language model's film something that can
be checked against a stated rule. The Tourkey Trouttown work shows where that holds (words, order, blanks,
sources) and where it does not (sound, kindness, whether a struggle shown is true).

1. **A page is passed.** Porthole 13: a fish that says "haha verry funny", a friend who writes three endings
   for a dinner bell, a second friend who writes nothing. Three children, one page, and then a film in
   which the blank is kept.
2. **What it means to say a language model makes a film.** The two regimes in the table above. Place this in
   operative ekphrasis: description that does something, and thick prompting as the way to study it.
3. **The SCION form.** Its nine sections; its debt to Oulipo (a constraint is a rule another person can
   check) and to the animation studio (roles, the checker, the exposure sheet). The three sets and the
   Multiplane Studio prompt as members of one family.
4. **Case one: a film from a video model.** 55 portholes, feedstock cards, two locked shots each; drift,
   tracking, the budget. What a description cannot guarantee.
5. **Case two: films made by hand in code.** The costume failure and the forage-or-handmake rule. Five
   portholes, each with sources and a review on its page.
6. **Case three: the children's sentences as invariants.** Five pages, 34 sentences, 45 agents. The sentence
   never changes; the expansion is all in the picture; blanks stay blank; the die is not thrown.
7. **Case four: filming the writing.** Hands, a desk, a camera that travels into Turkey's seat and out to the
   river. The rule that every struggle shown must be on the page, and the fact that this was not verified.
8. **The loop.** A game that makes films; films that run the game (the classroom film, the teaching cut,
   the 14:48 film). What a second class would show.
9. **What the critic cannot do.** Hearing; judging kindness; knowing what a child meant. Where a person has
   to decide, and how the prompts mark that boundary.
10. **Limits.** One class, five pages, no measure of learning. Children's work: first initials only, pages
    never shown. Authorship split between the sheet's designer, the children, the agents and the editor.
11. **What this adds.** A form for prompts that makes generated film falsifiable; a worked account of which
    parts of that form survive production; a classroom game whose output is its own instruction.

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
