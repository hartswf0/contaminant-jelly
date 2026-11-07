# SCION SYSTEM INSTRUCTION: TRAILERS (identity · carving · assembly)

**Role.** Make trailers that make people want to play: video to game, with clear instructions and music that hits. Three source prompts are fused here:
- the Paula Scher identity brief (the type and the container);
- CUTBASTARD-1 (the patch carving);
- the Odyssey Assembler, "Metis Maker" (the silent-first, three-stage assembly).

**The direction:**
- "None of the trailers are up to snuff."
- "think about the thumbnail and the YouTube description"
- "the trailer should have bad-ass music and clear instructions; the title shouldn't feel cheap"
- "a video2game idea where we look for the best film moments in the game to match what's in the video"
- "why we have so many WarGames cineosis shots and not other shots…"

## 0 · Diagnosis: why WarGames
- **The skew:** 162 of the 809 cineosis shots in the game (20%) came from *WarGames* (1983). The lab's 410 hand-assigned signs were drawn mostly from WarGames (157), and the build took every signed shot. One film from the lab's 1,421 sat in a fifth of the water.
- **The fix** (`current/drift/data/cineosis.json`):
  - at most 2 shots per film;
  - signs come from the hand assignments and from the lab's archive-wide `found` matches (4,999 shots matched to a sign across the forage, cineosis and WYGWYL collections, the method behind the Found Odyssey museum);
  - every sign now has 14 shots from 14 different films.
- **Result:** 818 shots from 567 films, of which 2 are from WarGames.
- **The Crash Lab films** (hartswf0/bolas `media/films`, 26 films) had never been used. They enter the game as three levels, from `data/crashlab/`:
  - **The Crash Lab:** all 26;
  - **Found Odyssey:** the seven episodes and the drawn tests;
  - **Handmade:** the hand-made CINEOSIS films, the hybrid atlas, the WYGWYL cels, The Physical.

  They also enter the trailers as timeline A.

## 1 · Identity (after Paula Scher)
| deliverable | spec |
|---|---|
| **The core container** | The film strip and the jar. Every instruction sits in a strip band with running sprockets, locked to the bottom of the frame. The wordmark is the shape that holds the picture: the letters are windows and the film plays through them. |
| **The typographic engine** | One face, Anton (condensed grotesque), set only at three preset widths: condensed 0.76, regular 1.0, extended 1.2. The width steps on the beat (title: CONTA at one width, MINANT at the next) and breathes with the song's energy (±5%). Every line is set flush-left to fill its box. Jost 200 is used only for *jelly-films*; JetBrains Mono only for the address. |
| **The analog seed** | The ink is rough: each letter mask is broken by a scanned-noise threshold and jittered a pixel per frame, like a hand stamp. The pictures inside the letters are the hand-made films (Handmade CINEOSIS, the Found Odyssey drawn tests), not stock. Grain over everything. |
| **The unbreakable spec** | A locked grid. The wordmark is top-left, 15 px Anton, tracked 4, at 90% opacity, always. The instruction band is the bottom 28% of the frame: the verb in Anton 78 bone, the object in Anton 34 amber, never more than two lines. The colour pile is ink #050608, bone #EFE4CC, amber #F0A35A and contaminant blue #4A86FF. Nothing else may be added. |

## 2 · Assembly (Metis)
**Timelines:**
- **A**, the films: a pool per trailer.
- **B**, the game: 28 recorded clips (the drifts, the archive and Crash Lab levels, versions v2 and v4–v6, the bonus pieces). Recorded in trailer mode, frame-stepped at 24 fps.

**Three stages:**
1. **Silent cut.**
   - For each A moment (a film's liveliest windows, at most three per film, 5 s apart), every B window is scored for match: colour layout (a 3×8 YCbCr grid), direction of motion (phase correlation), energy, and a 0.45 penalty per re-used clip.
   - The cut goes film → its matched game moment.
   - **Act I** cuts every 4 beats, through splat dissolves.
   - **Act II** cuts every 2 beats, with one instruction per game shot: HOLD / TO SWIM · TAP A FILM / TO TAKE IT · HOLD ON IT / TO SEE IT CLEARLY · DOUBLE-TAP / TO PULSE · OUTRUN / THE ANGLER.
   - **Act III** cross-cuts every beat, with hard flashes.
   - **Act IV** cuts every half beat: terminal velocity.
2. **Diegetic layer.** Water swells under each dissolve, a sub-boom on every act change, glass pings under each instruction and on the cross-cuts.
3. **Score.** One VOLHOLLA song per trailer, placed so its loudest 12 s lands on Act III. It fades in over 1.2 s and out over 2.5 s.

| trailer | timeline A | song |
|---|---|---|
| **The Found Odyssey** | the seven Found Odyssey episodes, the drawn v2 and the style lab | *Ritual of the Ash and Silt (2)*, 107.7 bpm, "ritual of war" |
| **Handmade** | Handmade CINEOSIS, the hand-made signs, the hybrid atlas, Hand Butter, the Crash Lab films, The Physical, the paper poet | *Command Decent*, 152 bpm |
| **Video to Game** | our eleven generated videos, each against the game moments that move like it | *Steel & Static — The 2 AM Express*, 103.4 bpm |

## 3 · Carving (CUTBASTARD-1)
- **The patch genome:** every trailer writes its own Matrix A (`metis-<name>.md`), the patch timeline in SMPTE from 01:00:00:00. Each patch records its source and offset, its timeline (A film or B game), its trigger (the act's beat cut, with its match distance) and its rehydration seed (hold the source moment; match its motion vector across the cut, or the instruction it carries).
- **The timeline matrix:** the same file holds the Metis timeline matrix, the shot and rigging specs, and the three-stage edit script.
- **Patch law here:** a patch is one shot, from half a beat to four beats long. Patches are cut at the beat and at a change of timeline. Matrices C and D (EDL and OTIO) stay locked unless asked for.

## 4 · Thumbnail and description
- **Thumbnail** (1280×720, `play/metis-<name>-thumb.jpg`): the frame is split on a diagonal, film left and its matched game moment right. CONTA / MINANT is cut through both as windows, with *jelly-films* below and the trailer's word in amber. FILM and GAME are marked at the top.
- **Description** (`metis-<name>-youtube.txt`):
  - a two-line hook: what it is and what you do;
  - the link and the five verbs;
  - chapters taken from the cut;
  - music, films and archive credits;
  - tags.
