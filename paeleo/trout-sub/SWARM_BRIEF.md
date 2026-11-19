# Trout Sub · swarm brief

One film per porthole of the 55 Portholes deck, plus six intro shots, one per core SCION prompt. Every film is generated on fal (16:9, with sound; `minimax/h3-max-turbo/reference-to-video` at 480P for everyday films, `minimax/h3-max/reference-to-video` at 768P for the hero films p01-p05) from a written prompt and reference images. All paths below are relative to this folder.

## What you have
- `seeds.json`: 55 rows, `[station, rim clue, lineage, Turkey's question looking out, Trout's question looking in, Ouxpo/SCION rule, kind]`. Row 0 is porthole p01.
- `stills/pNN.jpg`: the deck's drawing of each porthole. This is the look and the content to keep.
- `masters/cockpit.jpg`: Setup A, Turkey's seat. `masters/outside.jpg`: Trout's side of the glass. Both go to fal with every film so the room never changes.
- `atlas/atlas.json` and `atlas/aNN.jpg`: 52 frames from the SCION interior atlas (staging and light from the lineage films and the Trout Town episodes), with captions.
- `scions.json`: the six core SCION prompts (cockpit, Works kit, The Bend That Moved, LEGOS beat, postcard and world memory, Trout Town world).
- `prompts/p01.txt` and `ledger/p01.json`: the pilot that worked. Look at `.raw/p01_t1_sheet.jpg` to see what it produced.

## The film, three beats in 8 seconds
1. **Turkey's seat (0-2.5 s).** Setup A exactly as the cockpit master. One control is used: the lamp toggle (lower right) or a ballast weight dropped into the slot (lower left). Choose the one that fits the porthole. Only a wing tip enters frame; a whole turkey body or tail fan blocks the room.
2. **The port (2.5-5.5 s).** Push in to the glass. The silhouette of the still is revealed and does one clear thing that keeps both of Turkey's readings possible.
3. **Across the glass (5.5-8 s).** Hard cut to Trout's side as in the outside master: the tin, Turkey small behind the amber port, and the same thing seen from the river, now staged so both of Trout's readings are possible.

Apply the row's Ouxpo/SCION rule as the constraint on how the thing moves or is shown.

## Setup A invariants (never change)
Long oval dented metal bread-roll tin (riveted steel, never bread), dent on the right wall, centered round brass six-bolt porthole with hinge, offset latch and a chip in the rim at two o'clock, empty ballast slot lower left, chalk route chart under glass lower center, brass lamp toggle lower right, amber lamp inside, cool blue-green river outside.

## Writing the prompt
- Plain description of what is seen, beat by beat with times, 900-1700 characters. Start with the style line from `prompts/p01.txt`. End with "No text, no labels, no captions." unless the porthole's own object carries lettering (a chalkboard, a sign); then name the exact few words and say no other text.
- Describe every character and prop yourself as original Trout Town residents (trout, turkey, river animals, household objects). Never name a film, show, band, artist, studio or their characters in the prompt. The lineage is a lens for staging, light and material only.
- Pick one or two atlas frames whose staging or light fits, pass them with `--atlas`, and in the prompt say what to take from them ("light as in the last reference: ..."). Do not ask for anything in them to appear.
- Diagrams with labels as references leak their labels into the film. Don't use `a03`.

## Making it
```
python3 tools/portfilm.py gen pNN --prompt-file prompts/pNN.txt --duration 8 --atlas a50,a39
```
It takes about a minute, writes `films/pNN.mp4`, and prints the path of a contact sheet (12 frames in time order). Read the sheet. `python3 tools/portfilm.py use pNN 1` puts an earlier take back. Each `gen` is a paid call and the whole deck has a fixed budget: ONE take per film, no repairs. Whoever makes the take reads its sheet and writes the ledger honestly, including when the still is stronger.

## Ledger
`ledger/pNN.json`: `{id, station, clue, rule, control, atlas: [{id, why}], prompt_file, takes: [{take, by, verdict, seen, changed}], final_take, verdict, open}`. Verdict is `pass`, `reference stronger` (the still does it better than the film) or `inconclusive`. `seen` is what a viewer can point to, with the time. `open` lists what is still wrong. Write only what the sheet shows.

## The standard unit (how the 55 become one film)
`python3 tools/units.py` turns every porthole into one unit in `units/`: exactly 8.000 s, 960x540, 24 fps, opening with a 0.4 s iris out of the river colour (#10201f) and closing with a 0.4 s iris back into it. Because every unit starts and ends on the same frame, a unit loops on itself and joins any other unit in any order, so the deck can be played in sequence or shuffled. A porthole with no generated film gets a keyframe unit built in code from the cockpit master, its deck still and the outside master. `python3 tools/intro.py` cuts the four-step intro from footage already made. Neither tool calls fal.
