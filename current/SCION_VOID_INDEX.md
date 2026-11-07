# SCION SYSTEM INSTRUCTION: VOID INDEX (the landing, the shelf, the back layer, the trailer)

**Role.** Build the least obstructive complete surface for Contaminant. Every visible element is a claim about what matters now. Cut every claim that is false, premature, duplicated or without consequence. Never cut state, warning, recovery, exit or accessibility.

**Source.** The user's VOIDBASTARD-TAO prompt, together with this direction:
- "the video in the background … takes away the effect; it should fade quickly and be there only when a piece is selected, or play as an echo on a scan"
- "we don't want that repetitive background video; it should fade into black"
- "cleaner, easier to find the whole thing … scrollytelling with parallax"
- "for each film or video2game … hover to see the video in it and click to play the game"
- "the main index needs less is more, better animation and landing experience"
- "the game should make great videos … splice the clips with the generated footage via bubbles to hide cuts and seem continuous in-world"

Reference plates: the user's letterpress jar labels (Ascent, Pairs, Lure, Toward the Surface, Halo, Ray Run, Slices, Twin Caves), the wordmarks, and the "WHEN THE JELLY TURNS RED / KEEP OUT OF THE WATER" sheet.

## 1. Way
- **Actor:** a visitor, or a player.
- **Objects:** eleven video→game pairs, six archive levels, seven versions.
- **The operation:** see a film, and see what game it became. Play that game. Or watch the trailer.
- **Completion:** the visitor is swimming, or has seen the reel.

## 2. Obstruction (what the last index did wrong)
- **The hero video:** a full-bleed loop that competed with the title.
- **The crosshair labels:** five floating claims that said nothing about state.
- **The depth gauge:** it decorated the scroll and changed nothing.
- **A WATCH | PLAY table:** 22 videos on one page, and the eye had nowhere to rest.
- **Cards for every version and tool:** they duplicated what a list does.
- **In the games:** a film always playing in the far water. It was wallpaper: it repeated, and it flattened the reveal it was meant to echo.
- **The trailer:** encoded as yuv444p, which phones cannot play; plain dissolves; no music.

## 3. Keep / cut ledger
| element | claim | verdict |
|---|---|---|
| printed title (rule, word, jar, red overprint, warning) | this is Contaminant; red means contaminated film | **keep**: it plays once, can be skipped, and finishes on scroll or a key |
| "PLAY THE DRIFTS" | the one valid action | **keep**: it appears only after the title has printed |
| "watch the trailer" | the alternative | **keep**, smaller |
| skip › | stop the running intro | **keep** while the title runs; hide it after |
| the jar shelf (11 + 6) | each jar holds a film and its game | **keep**: hover or focus plays the film printed into the jar, then the game; click plays it |
| "the film / the game" stamp on a live jar | what is playing now | **keep**, and only while a jar is live |
| one video→game walk-through (Lure) | how the workflow works | **keep**: a sticky frame, five steps, a label drifting in parallax |
| versions and lab | where everything else is | **keep**, as one plain two-column list |
| hero video, crosshair labels, depth gauge, WATCH/PLAY grid, version cards | — | **cut** |
| the far film in the games | — | **cut** as wallpaper. It returns only while a film is held (that film) or for 2.2 s after a pulse (the nearest film the ring lit) |

## 4. State map
| state | what shows |
|---|---|
| REST | The label prints itself, about 7.8 s. Paper, ink, the jar filling with water and the jelly lighting amber. Only *skip ›* is live. |
| READY | The title stays; **PLAY THE DRIFTS** and *watch the trailer* fade in. Scrolling down leads to the shelf. |
| WORKING (a jar is live) | The film, printed in ink, plays inside the label. After 3 s it dissolves into the game, then back. Leaving stops it. On touch, the jar nearest the centre plays. |
| CHANGED (walk-through) | The sticky frame changes with the step in view: the video, what it does, the rule, the drift, back to the reel. |
| COMPLETE | The page ends in dark water with the trailer and the one action again. It makes no new demand. |
| FAULT | A video that fails to load leaves the printed label in place. Reduced motion skips the title animation and the parallax. |

## 5. Wireframes
```
REST / READY                       SHELF                              WAY (sticky)
┌───────────────────────────┐     ┌────┬────┬────┬────┐             ┌────────────────────────┐
│        CONTAMINANT        │     │jar │jar │jar │jar │  hover →     │ ┌────────────────────┐ │
│        jelly-films        │     │film│    │    │    │  film, then  │ │ video / the drift  │ │ label ▫ (parallax)
│        ━━━━━━━━━━         │     ├────┼────┼────┼────┤  game        │ └────────────────────┘ │
│          [ jar ]          │     │    │    │    │    │  click →     │  ┌─────────────┐       │
│  WHEN THE JELLY TURNS RED │     └────┴────┴────┴────┘  play        │  │ 3 · THE RULE│       │
│   KEEP OUT OF THE WATER   │      FROM THE ARCHIVE (6 jars)         │  └─────────────┘       │
│ [PLAY THE DRIFTS] trailer │      EVERY VERSION · THE LAB (list)    └────────────────────────┘
└───────────────────────────┘      RETURN TO THE REEL (dark water, trailer, PLAY)
```

## 6. Void contract
- One dominant action per state.
- Motion reports real change: the printing of the label, a jar becoming live, the step of the walk-through.
- Nothing loops behind the content.
- No video loads until it is asked for: hover, focus or the step in view.
- In the games, the back layer is black.

## 7. Failure
- **Fonts fail:** Anton, Courier Prime and Cormorant are self-hosted under `fonts/`, and system fallbacks keep the layout.
- **The title cannot animate:** it shows finished.
- **Touch devices** have no hover, so the jar in the centre of the screen plays.
- **Phones:** two jars per row; the parallax label is hidden.

## 8. Implementation
- `title.js` is the printed title sequence, using Web Animations.
  - `mountTitle(el, {mode: 'intro' | 'outro', flood})` returns `play()`, `seek(t)`, `finish()` and `dur`.
  - The landing and the trailer both use it, so the title on the page and in the film are one thing.
  - `title.html?flood`, `?mode=outro` and `?seek=s` render single frames.
- `index.html` contains the landing, the shelf (one SVG jar per piece in the periodic-table hand; the label window holds a cartoon of the mascot jelly, and the film and then the game play in it), the bonus shelf, the periodic table of 45 sign and 16 type jars, the walk-through, the list, and the water.
- `current/screens.js`: in v4, v5, v6 and the drifts, the back layer fades in quickly and out quickly, and appears only for a held or focused film or as an echo after a pulse or cast.
- **The trailer** (`current/drift/play/trailer.mp4`, 960×540, h264 yuv420p with AAC audio) runs in this order:
  1. the printed title floods into the water;
  2. for each of the 11 drifts, 4 beats of the generated film, then 4 beats of the game;
  3. the end card returns to the reel.

  Its craft:
  - film→game cuts are hidden under a burst of rising bubbles; game→film cuts open through a radar ring;
  - one grade, one grain and one vignette cover both, so film and game read as one world;
  - the music is VOLHOLLA's *Saltwater Static (The Last Shanty)*, cut on its 95.7 bpm beat.
- **The recordings** are frame-stepped at 24 fps in trailer mode, with a shot list per drift:
  - Lure: the angler lunges;
  - Toward the Surface and Bloom: a film is held to watch;
  - The Long Descent, Twin Caves and Ray Run: the radar pulse;
  - Silt Bench: swimming low, then a pulse;
  - the doodle levels: the pulse, so they flash.

## Revision: the water (supersedes the paper label)
**The user's direction:** "I hate the paper look and the bubbles … keep the jelly jars but make them with this … the transition is cheap and seems scripted, as does the gameplay footage. I like the idea of the gaussian splats as the bubbles transition. Less hokey, everything integrated."

The reference plates:
- "jelly-films" in thin light type over dark water;
- one translucent jelly with a film inside its bell;
- three thin rounded frames stacked one behind another (1 → 2 → 3);
- "Play The Drifts →" over a single thin rule.

**Keep / cut:**
| element | verdict |
|---|---|
| paper, letterpress, red overprint, warning text | **cut** |
| bubbles in the trailer | **cut**, replaced by gaussian-splat dissolves |
| the jars | **kept**, redrawn as glass in light (`jar.js`): three thin outlines offset like frames, crosshair ticks, a translucent jelly inside; the film plays clipped to the glass |
| REST | the jelly itself (`hero.js`, WebGL): a bell of 24,000 gaussian flecks with a perforated film band and an amber glow; a real secondhand film (hand, face, eye or fish) lives inside the bell; film-strip and filament tentacles; light from above; marine snow. Only three words: *jelly-films*, *Index*, *Play The Drifts →* |
| the periodic table | the same glass jars, with only the sign's symbol |

**How it feels in motion:**
- **The trailer.** The title is three frames drawing in the water. Each cut breaks the picture into about 22,000 soft flecks, which drift in a slow swirl and settle bright-to-bright into the next picture. The song is *Stratospheric Void Crossing*: the title sits in its quiet passage, and the first film lands on the beat where the song comes back in.
- **The recordings.** Trailer mode now steers like a camera operator. Speed is capped and the steering is eased, with a constant gentle drift. Holds last 5.5–7.5 s, the camera turns toward a held film slowly, and it follows the jelly more loosely. Most drifts have no scripted cues; only Lure's lunge, holds in Toward the Surface and Bloom, one pulse in The Long Descent, and swimming low in Silt Bench remain.
