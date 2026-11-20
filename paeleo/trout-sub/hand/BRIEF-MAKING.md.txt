# The making films · what it is like to fill in the sheet

Read `BRIEF.md`, `BRIEF-CLASS.md` and `films/BRIEF-2-oulipo.md` first. The class films (`films/cNN.py`) staged what
the children wrote. These films (`films/mNN.py`, 75 to 95 seconds) show the children WRITING it: the part nobody
films. The game asks a nine-year-old to picture what somebody else sees, and that is hard. Show it being hard.

## What the film is about
One sheet passes through three children. Each one has to leave their own seat:
1. **The pilot** looks at a small picture and has to say who is outside and what Turkey does about it.
2. **The first friend** gets the pilot's page and has to think like Turkey, inside the tin, looking out.
3. **The next friend** has to think like the trout, outside in the river, looking back at the tin.

The film is the work of getting there: reading the question, not being sure what it wants, picturing something,
remembering something, starting, rubbing out, getting it a bit wrong, settling. Be kind. Nobody is made fun of.
The mistakes are the best part of the sheet and the film treats them that way.

## Only true things
Open the two photographs of the sheet (`class_photos/pNN_front.jpg`, `pNN_back.jpg`) and the transcript
(`../class/transcripts.json`: `wrote` is the child's own spelling, `reads` the tidied one). Find the TRACES of
working that are really there and build the film on them. Examples of traces: a line rubbed out; a word added
faintly afterwards; a second drawing outside the ring; a choice circled instead of drawn; the button itself
coloured in; a sentence that carries on from the printed stem instead of standing alone; spelling by ear; a
sentence that runs off the edge; a friend who repeated the option's name as the ending; a part left blank.
- Every specific struggle on screen must be one the sheet shows. List them in the board with where each is seen.
- Ordinary thinking is allowed without evidence: the pencil hovering, a look up at the picture, a look at a
  neighbour, a false start in the air, tapping, a sigh of bubbles. Do not invent dialogue or inner speech.
  Thoughts are shown as pictures, never as words.
- A blank is a real event: somebody ran out of time or did not know. Show the pencil not moving. Do not explain it.
- The children's words appear in pencil on the page in their own spelling (`wrote`), written letter by letter
  (letter them in code so they look written, not typeset; never paste the photograph). When a line is finished,
  the caption (from a top-level `CAPTIONS` list, `reads` spelling) says it once. Nothing else is captioned.
- The sheet's own printed words may be shown, because the children were reading them.
- Children are cut-paper hands, sleeves and backs of heads in poster-paper colours (teal, rust, ochre, plum:
  not skin colours), never faces. First initials only, and only on the page. No photograph on screen.

## The camera is the idea
Perspective is not explained, it is travelled. Use `films/cam.py` (read its docstring; do not edit it) and be bold:
- **The child's eye:** over the shoulder, down at the desk, the sheet in perspective, the hand in the foreground.
- **Into the page:** dive through the drawn ring into the thought, where the thing being pictured puts itself
  together out of pencil lines, wrongly at first, and falls apart again when the child changes their mind.
- **Into Turkey's seat:** for the first friend the camera goes down through the page's porthole, lands inside the
  tin and TURNS ROUND to look out through the glass from where Turkey sits. The pilot's drawing is now outside.
- **Out to the river:** for the next friend it goes out through the glass, swings round in the water and looks
  back at the small tin with a small Turkey in it.
- **Back out:** every dive comes back up to the desk, to the hand, to the next word. The return is the thinking.
- **The pass:** when the sheet goes to the next child the whole desk swings (a whip, a 180 degree turn of the
  page so the new child first sees it upside down or sideways, if that suits what they then got wrong).
- **The end:** up and away from the three pairs of hands to the whole room: many desks, many rings, a die in a
  cup that nobody has thrown.
Hold still when the child is stuck. The contrast between the stuck desk and the moving thought is the film.

## Reuse
The class film for the same porthole already built this porthole's world: `films/swarm/cNN/world.py` and its
`WORLD.md` (Turkey with moods, the tin from both sides, trout, the subject, the pilot's drawing as pencil
strokes, buttons, dice, table, page). Import it; do not edit it. `films/people.py` gives hands, sleeves, backs of
heads, the desk and the sheet in perspective (read `PEOPLE.md`). The staged endings in `films/swarm/cNN/scene_*.py`
may be imported and shown inside a thought, small and brief, as what the child is picturing.

## Units (folder `films/swarm/mNN/`)
1. **Trace unit** writes `board.md`: the list of true traces, then the film beat by beat with seconds, the camera
   move for each beat, and what is on the page at each moment.
2. **Three scene units**: `scene_pilot.py`, `scene_turkey.py`, `scene_trout.py`. Each exposes `SECONDS`,
   `CAPTIONS` (times from its own start) and `draw(t, ink)`.
3. **Editor** writes `films/mNN.py`: joins them with the passes, adds the ending, the number badge and sound
   (pencil, eraser, paper, chair, a room of children far off; water when we are in the thought), and renders
   `assets/films/mNN.mp4`.
4. **Critic** then **repair**.
