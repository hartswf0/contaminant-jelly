# Drawn portholes · swarm brief

Each of the 55 portholes is remade by hand, in code, as a picture you watch being drawn. One scene per file:
`drawn/pNN.js`. No generated video, no loaded images: only canvas drawing through `drawn/kit.js`.

## The scene
- 1000 x 1000 space. The glass is the circle at (500,500), radius 430; the player clips to it and draws the brass rim.
- `t` runs 0 to 12 seconds and loops. **0 to 8: the picture is made in front of the viewer. 8 to 12: it comes alive.**
- Nothing may appear all at once. Every mark arrives through a tool: a pencil line that travels, a brush that washes
  in rows, chalk, hatching, a cut-paper piece that is slid in by a hand. Order it as a person would make it:
  ground first, big shapes, then detail, then the one thing that makes it this porthole.
- In the alive phase the subject does one clear thing that keeps BOTH of Turkey's readings possible (the row's fourth
  field), and the row's Ouxpo/SCION rule (sixth field) must be visible in how it moves.
- Deterministic and cheap: no Math.random (use K.hash / K.noise), no globals, well under 5 ms a frame.

## Your sources, in this order
1. `seeds.json` row NN-1: station, rim clue, lineage, Turkey's question, Trout's question, rule.
2. `stills/pNN.jpg`: what the porthole shows. Keep its subject, composition and palette.
3. Your style: the first line of `prompts2/pNN.txt` names a feedstock slug; read `feedstock/<slug>.md`. Its LAW is how
   your scene should look and move (cut paper, etched hatching, chalk, sepia tracing, stage flats, and so on).
4. `drawn/scions.json`: 54 animation SCIONs (id, title, lineage, prompt). Choose TWO OR THREE whose method suits this
   porthole, read their prompts, and actually use each method in the scene (a hinged puppet, a multiplane with
   parallax in the alive phase, a metamorphosing line, harmonic motion, secondary motion, a state change, ...).
   Name them in `scions` with what each one does here. Use the methods; do not imitate any named artist's pictures.
5. `drawn/kit.js` (read all of it) and `drawn/p07.js` (the worked example; look at `.raw/drawn_p07.jpg`).
   p07 is the floor, not the ceiling: yours should have more made in it, and its own way of being made.

## Making it
Write `drawn/pNN.js` (copy p07's shape: an IIFE that calls `DRAWN.add({id, title, style, scions, draw})`). Then:
```
node tools/drawn_shot.js NN
```
It prints the path of a sheet of eight moments (1, 2.5, 4, 5.5, 7, 8.5, 10, 11.5 s). OPEN THE SHEET AND LOOK AT IT,
beside the still. Fix what is wrong and shoot again. Do at least three rounds of look-and-fix. Stop when a stranger
could name the subject from the last frames and could see, in the first frames, that it is being drawn.
A "DRAW ERROR" or "no scene registered" line means your code threw: fix it.

## Rules
- No lettering unless the rim clue itself is lettering (a chalkboard, a sign); then only those words, drawn stroke by stroke.
- Original Trout Town things only. No characters, logos or pictures from any film, show, band or artist.
- Edit only `drawn/pNN.js` and `drawn/ledger/pNN.json`.

## Ledger
`drawn/ledger/pNN.json`: `{id, feedstock, scions:[{id, how}], made_in_order:[...], alive:"...", rounds:n,
verdict:"pass"|"reference stronger"|"inconclusive", open:[...]}`. Write only what the last sheet shows.
