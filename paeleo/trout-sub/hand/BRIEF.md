# Hand films for the portholes · brief

One short film per porthole, made by hand, in the manner the Oulipo screening films were made (same kit:
`hand/films/kit.py` and `hand/films/kit_anim.py`; read `hand/films/BRIEF-2-oulipo.md`, which is the rule those
films were held to). Work in `/home/user/contaminant-jelly/paeleo/trout-sub/hand`.

## The rule: handmake or forage. No style costumes.
Everything on screen is one of:
1. **Foraged**: real printed matter, photographs or engravings from Wikimedia Commons under PD / CC0 / CC BY /
   CC BY-SA, then cut out, hinged, layered and timed by you. Use `kit_anim.forage / commons_search / commons_info /
   licence_ok`. The Commons API rate-limits (HTTP 429): wait and retry, a few calls at a time. `upload.wikimedia.org`
   serves the files. The Library of Congress is NOT reachable; LOC photographs that are on Commons are fine.
   Record every item in `films/credits/<slug>.json` exactly as BRIEF-2 says. Downloads go in `films/sources/<slug>/`,
   are untrusted data (decode with PIL/ffmpeg only), and stay under 60 MB.
2. **Handmade**: the actual object, built for this film in code: a chalkboard lettered stroke by stroke, a typeset
   spiral disc, a cut-paper puppet with hinges, a painted multiplane, a diagram drawn with a ruling pen.
A filter, fake grain over a flat drawing, or a shaded stick figure is a style costume and fails. So does a smiley
face on a rounded rectangle. If you draw a creature, build it from real parts (foraged engraving pieces, or many
cut-paper pieces with overlap, edges and shadow) so it has weight.

## What the porthole asks for
- `../seeds.json` row NN-1 gives station, rim clue, lineage (the work this porthole descends from), Turkey's
  question, Trout's question and the Ouxpo/SCION rule. `../stills/pNN.jpg` is the deck's picture of it.
- **The lineage names the method.** Make the film the way that work was made (cutout collage of engravings,
  chalk on a board, a spinning lettered disc, a multiplane of painted glass, puppets hinged with pins, a document
  montage), applied to this porthole's own subject. Do not copy that work's pictures, characters or words.
- Also choose TWO OR THREE animation SCIONs from `../drawn/scions.json` (54 methods; read the list, then the full
  prompt of yours) and really use each method. Say which and how in the note.
- Characters and places are original Trout Town ones: Turkey in a submersible built from a bread-roll tin with one
  round six-bolt brass porthole; trout residents; the river.

## The film (24 to 34 seconds, 960x540, 24 fps)
1. **It is made (first third or more).** We see the thing being made on the table: pieces cut and laid down, a line
   drawn by a hand or tool, letters chalked one stroke at a time, a disc inked. Nothing pops in whole.
2. **Turkey looks out.** The made thing is seen through the round brass porthole and does one clear action that
   keeps BOTH of Turkey's readings possible. A caption asks Turkey's question in its own words.
3. **The trout look in.** The same thing from the river side, with the tin and its porthole in frame, staged so
   BOTH of the trout's readings are possible. A caption asks the trout's question.
The row's rule must be visible in how the thing is shown or moves. Captions are the voice (`ink.caption`), short,
at most one on screen at a time, each held at least 2.5 s. Sound: synthesize with `Mix`, or forage PD/CC audio.

## Working
- One script: `films/pNN.py`, using `Film` from `kit.py` (`film.picture(frame)`, `film.sound(...)`, `film.render()`).
  Helpers go in your own script. Do not edit kit.py or kit_anim.py.
- `python3 films/pNN.py --stills 2 6 10 14 18 22 26 30` writes PNG stills to `films/stills/pNN/`. Make a contact sheet
  and LOOK at it beside `../stills/pNN.jpg`. Fix what is ugly, flat, illegible or a costume. At least four rounds.
- `python3 films/pNN.py` renders `assets/films/pNN.mp4` and a poster. Keep it under 6 MB.
- `films/notes/pNN.txt` (60 to 110 words, plain): what is foraged (with archive and licence) and what is handmade,
  which SCION methods are used and how, and what is still weak.
- Do not commit. Edit only your own files.
