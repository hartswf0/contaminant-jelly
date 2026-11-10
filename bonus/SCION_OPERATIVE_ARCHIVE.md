# SCION SYSTEM INSTRUCTION: THE OPERATIVE ARCHIVE (an album made by digging, with every sound traceable)

**The direction:** "Make an album [with] this, with the samples we have; forage for new", with the brief *SCION: Operative Archive* (an agent-first studio for crate-digging, sampling and composition).

**Nothing here was heard.** This machine cannot play audio. Every moment below was located by measurement and is **provisional** until someone listens. The brief's own rule applies: a plot can locate an event; hearing it requires playback.

## 1 · The intent contract (as recorded)
| | |
|---|---|
| **Listener experience** | the album's thesis, kept from the first brief: *the weight arrives before the lyric names it* |
| **Permitted sources** | recordings in the owner's repository `hartswf0/moto`: "the samples we have", and a new draw from the rest of it |
| **Permitted operations** | cutting, placing, filtering, a synthetic room, gain, and new synthesis. No time-stretching was used |
| **Output mode** | an **audition** (renders), an **editable session** (the edit maps and tools) and a **playable instrument** (the Jelly Studio). **Not an approved release**: see section 9 |
| **Review budget** | one builder. No independent listener |
| **Fixed decisions** | *Boxes on My Back* with the found drums opens the album |
| **Defaults I chose** (all reversible) | seven new pieces, one per operator of the brief; 12 blind clips; one context-led clip; the album title **THE WEIGHT ARRIVES** |

## 2 · What was delivered
| | where |
|---|---|
| **The album**, 8 pieces, 8.5 minutes | `bonus/jellystudio/album/album.mp3`; each piece in `bonus/jellystudio/<piece>/renders/full.mp3` |
| **The audition reel**, 3.4 minutes: 13 moments, each as source context, dry cut, then in the piece, at matched loudness | `bonus/jellystudio/album/audition-reel.mp3` (cue times in section 6) |
| **The session**: every placement of every piece | `bonus/jellystudio/<piece>/scion.json`, with the exact cut sounds beside it |
| **The lineage and use manifest** | `bonus/jellystudio/album/lineage.json` |
| **The frozen blind shortlist** | `bonus/jellystudio/album/blind_shortlist.json` |
| **The recipe** | `sim/jellystudio/`: `forage.py`, `scout2.py`, `shortlist2.py`, `album.py`, `deliver.py` |
| **The instrument** | `bonus/jellystudio.html`: all eight pieces, and a new way to play it by hand (section 8) |

## 3 · The album
| | piece | operator | tempo | length | the decisive moment |
|---|---|---|---|---|---|
| 1 | **BOXES ON MY BACK** | (the first brief) | 72 | 2:00 | bar 5: the low end arrives (0:13) |
| 2 | **PICKUP** | Cut | 80 | 0:48 | bar 4, beat 4.5: the first glide that starts before the barline (0:11) |
| 3 | **LATE** | Feel | 76 | 0:51 | bar 9, beat 2: the first late snare (0:26) |
| 4 | **FIELD CLOCK** | Reframe | 92 | 0:52 | bar 5, beat 2: the call lands where the snare would (0:11) |
| 5 | **WHAT REMAINS** | Haunt | 72 | 1:10 | bar 13: only 420 to 460 Hz of the choir is left (0:40) |
| 6 | **SIXTY BEATS** | Recombine | 90 | 0:43 | bar 16, beat 1: three cycles and the barline meet (0:40) |
| 7 | **ONE ROOM** | Worldbuild | 60 | 1:04 | bar 6, beat 1: the first bar with no kick, after the broadcast (0:20) |
| 8 | **THE CHOIR, REBUILT** | Resynthesize | 72 | 1:03 | bar 9: the recording is gone; only the rebuilt choir plays (0:27) |

The album closes as it opens: on the source's own ending of *Hollow Square Roar-Brute*.

### Each piece: its thesis, the test that could disprove it, and what the remix does to its source
| piece | what the listener should hear change | the test | learns from the source · changes · lets us hear |
|---|---|---|---|
| **PICKUP** | when the glide starts half a beat early, "one" moves from the sample to the kick | scenes **A** and **B** in the instrument: four bars, identical but for where the glide starts | its glide has a slow attack · the attack is moved across the barline · where a bar begins is a decision |
| **LATE** | with the sample untouched and only the drums moved a few milliseconds, the groove leans back at bar 9 | scenes **A** and **B**: straight, and snare 24 ms late, hats 12 ms late, kick 6 ms early | the note already trembles 10.8 times a second · nothing in it is changed · the pocket belongs to the drums |
| **FIELD CLOCK** | the same half-second of voice is a call for four bars and a drum from bar 5 | mute DRUMS from bar 5: if the voice still reads as a call, the reframing failed | the strongest event in the file is a voice · only its place in the bar changes · a voice can keep time |
| **WHAT REMAINS** | the motif stays recognisable as its band shrinks, because the sub keeps its roots | mute SUB: if the motif is lost a stage earlier, the weight was carrying it | the choir lives in 285 to 742 Hz · that band is cut to 13 Hz wide · how little of a choir is still a choir |
| **SIXTY BEATS** | cycles of 3, 5 and 6 beats make a kick that only marks their meetings sound composed | mute DRUMS and SUB: the meetings should still be heard as moments of density | three unrelated lengths · none is edited to fit the bar · accident can be arranged around |
| **ONE ROOM** | one room and one pulse make four unrelated sources one place; the broadcast is an event because the pulse stops after it | the dry cuts are kept: put them back and the place should fall apart | two sources stop dead · their silences are filled by the same room · a stop is also a sound |
| **THE CHOIR, REBUILT** | at bar 9 a synthetic copy stays and the chords are still heard; at bar 15 the choir returns as a different thing | mute the rebuilt layer in bars 5 to 8: if nothing is missed, the copy adds nothing | the choir's pitch and swell · its voices are replaced by sines · what in a choir is pitch, and what is people |

**Measured, for two of them:**
- **WHAT REMAINS:** how well each stage's loudness contour follows the full motif: 1.00, 0.84, 0.61, 0.35, 0.31. By measurement the motif's shape is mostly gone at stage 3 (bar 13). Whether the ear still follows it is the question the piece asks.
- **THE CHOIR, REBUILT:** the copy follows the choir's loudness contour at 0.99 and its spectrum at 0.75. It is 20 sines on harmonics of 36.4 Hz (and of 33.05 Hz for the second bar), each given the level the choir has at that pitch. It is an **original layer**, marked as synthesis in the session, not as a cut of the recording.

## 4 · Foraging
**Index.** 24 new recordings were drawn by a seeded random draw, one from each of 24 of the 88 other albums in the repository, then hashed and registered before any processing. With the 69 from the first brief: **93 sources, 262 minutes.**

**Blind pass** (ids only). Eight kinds of moment were searched for by measurement:
| kind | found | the test |
|---|---|---|
| transient | 235 | a rise of 14 dB in under 50 ms out of quiet, and a fast fall |
| decay | 322 | a fall of 25 dB over 0.6 to 2.4 s with no step |
| negative space | 52 | a hole of 0.25 to 1.5 s with sound on both sides |
| unstable pitch | 6 | a glide of 1.5 to 7 semitones, periodic throughout |
| room tone | **0** | 1.6 s that is quiet, steady and noise-like |
| breath | 45 | half a second of unpitched air standing above its surroundings |
| modulation | 111 | a level that trembles 3 to 11 times a second under a steady pitch |
| evolving texture | 35 | four seconds at a steady level while the brightness moves |

**The cap: 12 clips.** Nine by test, one quiet moment a ranking would bury, two by random draw with no test at all. The list was hashed and frozen before any name was shown (`blind_shortlist.json`).

**Unblinded** (names shown only after the freeze)
| | kind | source | at | what was measured | used in |
|---|---|---|---|---|---|
| M01 | unstable pitch | *Sunbaked Field Chant* (new draw) | 1:40.68 | a glide up 1.8 semitones in 1.3 s | PICKUP |
| M02 | unstable pitch | *Brutus Protocol* | 1:24.71 | a glide down 1.8 semitones, quiet | ONE ROOM |
| M03 | negative space | *The Ancient-Chant Singularity* | 0:04.54 | a hole of 1.18 s | ONE ROOM |
| M04 | negative space | *The Knife I Carry* | 1:23.51 | a hole of 0.53 s | ONE ROOM |
| M05 | transient | *The Cathedral of Tape Echo* | 0:54.55 | rises 49 dB, gone in 0.3 s | PICKUP |
| M06 | decay | *Echoes of the Black Chapel* | 2:30.54 | falls 25 dB in 0.63 s | PICKUP |
| M07 | breath | *Boxes* | 3:59.42 | half a second of air, 47 dB above what precedes it | FIELD CLOCK |
| M08 | modulation | *Steppe Telegraph & The 6,500-Voice Lavender Shanty* | 2:27.77 | trembles 10.8 times a second | LATE |
| M09 | evolving texture | *Choral-First Motorik* | 1:25.38 | darkens over four seconds | SIXTY BEATS |
| M10 | quiet | *Parchman Hollow Square* | 1:02.00 | 29 dB under the loud passages, perfectly steady pitch | SIXTY BEATS |
| M11 | random draw | *What It Do?* (new draw) | 2:09.78 | none | SIXTY BEATS |
| M12 | random draw | *Fa Sol La Mi* | 0:36.98 | none | LATE, ONE ROOM |
| **C1** | **context-led** | *HUNH! (92 BPM Field Clock)* | 0:47.62 | the strongest onset in the file | FIELD CLOCK |

**The context-led pick (C1)** is the one the blind method missed. The title names a work-song grunt and a 92 BPM clock, so the piece was built at 92 and the file's strongest onset was taken as that grunt. I did not hear whether it is one.

**Only 2 of the 12 came from the new draw.** The new sources were searched with the same tests as the old, and mostly lost.

## 5 · Context, read after the freeze
Three kinds of statement, kept apart.
- **Documented facts.** These files are in the owner's repository. Their names end in "Treblo" or "Sonauto", which are music generators. The four catalog pages present them as albums.
- **Not documented.** How each was generated, with what prompt, and under what terms. I did not check.
- **Interpretation, mine, and open to dispute.** Several titles point at real traditions: *Hollow Square* and *Fa Sol La Mi* at shape-note singing; *Field Chant*, *HUNH!* and *Parchman* at work songs, and Parchman is a prison farm where such songs were recorded. These are generated recordings that evoke those traditions; they are not recordings of them.
  - **Does that change a use?** For FIELD CLOCK I kept the plan. In a work song the grunt marks the stroke: it already keeps time. Placing it on the backbeat follows its job. Someone who knows the tradition may read it differently, and that reading should win.
  - **Blind reason, informed decision, side by side:** M10 was chosen blind as "quiet but perfectly pitched". Informed: it comes from the track named for Parchman. It is used only as a steady pitch, raised 14 dB, in a piece about cycles; no meaning is claimed for it.

**On the method note.** The brief frames remix as a way of investigating a source, after Joycelyn Wilson's Design Remix Logic. That is turned into the last column of the table in section 3: for each piece, what it learns from the source, what it changes, and what the new setting lets us hear. I have not verified anything about that body of work beyond what the brief states, and make no claim about it.

## 6 · The audition reel (cue times)
Each moment is heard three times: **in its source** (two seconds either side), **cut dry**, then **in the piece**. All are set to the same average level; dynamics are untouched.
| moment | source context | dry cut | in the piece |
|---|---|---|---|
| M01 glide (PICKUP) | 0:00 | 0:05 | 0:07 |
| M05 tick (PICKUP) | 0:14 | 0:19 | 0:20 |
| M06 tail (PICKUP) | 0:27 | 0:32 | 0:34 |
| M08 tremble (LATE) | 0:43 | 0:49 | 0:51 |
| M12 random draw (LATE) | 0:58 | 1:04 | 1:06 |
| C1 call (FIELD CLOCK) | 1:15 | 1:20 | 1:21 |
| M07 breath (FIELD CLOCK) | 1:27 | 1:32 | 1:33 |
| M09 long cycle (SIXTY BEATS) | 1:41 | 1:49 | 1:54 |
| M10 quiet note (SIXTY BEATS) | 2:00 | 2:06 | 2:07 |
| M11 random draw (SIXTY BEATS) | 2:14 | 2:20 | 2:22 |
| M02 falling glide (ONE ROOM) | 2:28 | 2:34 | 2:36 |
| M03 the hole (ONE ROOM) | 2:45 | 2:52 | 2:55 |
| M04 the stop (ONE ROOM) | 3:06 | 3:12 | 3:13 |

## 7 · Checked (measurement only)
| check | result, all eight pieces |
|---|---|
| every source interval is inside its source, at the source's rate | yes |
| every audible layer resolves to a source or to named synthesis | yes: 3,738 placements |
| whole numbers of bars; peaks | yes; -1.0 dBFS |
| stems add up to the master | 77 to 81 dB down |
| mono | folding to mono loses 0.02 to 0.8 dB |
| the instrument plays what was rendered | all eight load with no errors; its own render of each whole piece is 36 to 80 dB from the reference |
| play by hand | a tap made a cut and no grains; a 1.1 s hold made 18 grains; the replay of the recorded gestures made the same 18 |

**The instrument's render is not sample-identical in three pieces** (LATE, FIELD CLOCK, WHAT REMAINS: 36 to 45 dB). I did not find the cause.

## 8 · The jelly instrument: play by hand (the brief's optional mode)
Press **PLAY BY HAND**, choose a sound, and the bell becomes the instrument.
| gesture | what you hear | what you see |
|---|---|---|
| **touch** | a cut: the sound from its start. The bell squeezes | a marker where you touched |
| **hold and move** | the sound stretched into grains. **Round the bell** is where in the sound; **toward the rim** is longer grains (40 to 400 ms) | the caption reads the slice, how far in, and the grain length |
| **let go** | a voice opens from that point and decays | |

- **Every gesture is written down** with its time, its sound and its place on the bell. **REPLAY** plays the performance again exactly. **TRACE** downloads it, with the exact source cut of each sound used.
- **Not done:** the brief asks for a performance on the jelly to be compared with the same sounds on fixed pads. That needs a player. Both are there to try: the pads row is the fixed version.

## 9 · Use decisions, and what is outstanding
| | status |
|---|---|
| **Handling and audition** | permitted: the owner supplied the repository and asked for an album from these samples |
| **Release** | **the owner's to confirm.** The renders are on the project's public site because the standing instruction is to push there. I did not check Treblo's or Sonauto's terms for these generated recordings. If any source is restricted, `lineage.json` names every piece that depends on it |
| **Independent review** | **pending.** One builder made and checked everything; the builder cannot approve its own work |
| **Listening** | **pending**, for all eight pieces and all 13 moments |

## 10 · What was rejected, and why (the crate remembers)
| what | the observation that changed the decision |
|---|---|
| **The first decay pick** | its envelope bounced: a kick pattern, not one decaying sound. The test now refuses any rise after the peak |
| **Room tone, as a category** | none exists in 93 sources: these masters have no room. The room in ONE ROOM is synthetic and labelled so |
| **Every quiet candidate, at first** | my own guard against near-silence threw them all out. Lowered for that category; one kept |
| **The first staging of WHAT REMAINS** | its first stage (nothing above 1200 Hz) changed nothing: the choir has no energy there. Redrawn inside the choir's own band |
| **The first description of SIXTY BEATS** | cycles of 3, 5 and 6 meet after 30 beats, not 60. Only the meeting on a barline takes 60. The piece keeps both |

## 11 · Limits
- **Seven pieces are about a minute each.** They are the passages that could disprove each thesis, carried into a short form; none is a full-length arrangement.
- **Each piece is one branch.** The brief allows up to three per flip; only PICKUP and LATE have a second, as their A and B.
- **The moments favour what my tests can see.** A sung line, a word, a groove: none of the eight tests looks for those.
- **The repository is heavier:** the studio folder is now about 98 MB.
