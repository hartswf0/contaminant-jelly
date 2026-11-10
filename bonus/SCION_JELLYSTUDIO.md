# SCION SYSTEM INSTRUCTION: THE JELLY STUDIO (a jellyfish that is a sampler, and the track made on it)

**The direction:** "We want a jellyfish version, a jelly instrument for sampling", with the brief *SCION: Autonomous Music Production Studio*: an original instrumental for **ET TU, BRUTE · BOXES ON MY BACK**, built from *Hollow Square Roar-Brute*, searched by signal with the names hidden, proved in eight bars before it is extended, and delivered so it can be played and revised.

**Nothing in this document was heard.** This machine cannot listen. Every claim below is a measurement of a file. Whether it sounds good is yours to judge, and the instrument is built so you can.

## 1 · What was made
| | where |
|---|---|
| **The instrument** | `bonus/jellystudio.html` (on the index's Bonus shelf) |
| **The edit maps** (every placement, one per track) | `bonus/jellystudio/<track>/scion.json` |
| **The names behind the hidden labels** | `bonus/jellystudio/identity.json` |
| **The cut sounds** (exact, uncompressed) | `bonus/jellystudio/<track>/clips/` |
| **The renders** | `bonus/jellystudio/<track>/renders/` |
| **Five aligned stems of the main track** | `bonus/jellystudio/boxes-found/stems/` |
| **The tools that made them** | `sim/jellystudio/` (archivist, scouts, ranking, builder, checks) |

## 2 · The instrument: the brief, turned into an animal
You look at a moon jelly from below.
| the brief | on the jelly |
|---|---|
| a two-bar recurrence at 72 BPM | **the rim is two bars.** Its **eight pacemakers are the eight beats**; a signal runs round the rim and lights each as it passes |
| lanes | **five rings inside the bell:** roar, answer, drums, sub, air |
| a placement | **an arc or a dot on a ring,** starting on its beat and as long as it sounds |
| "the weight arrives" | when the sub sounds, **the animal sinks and its fringe hangs**; with the low end held back it floats. The bell squeezes on every kick |
| stems | **the four gonads** glow with the four loudest stems |
| the protected vocal window | a **dashed arc marked "kept clear for the voice"** on the bar that is left empty |
| mask the labels | the pads read MOTIF 1, ANSWER and so on. **REVEAL NAMES** shows the track and time each came from |
| matched comparisons | **A** and **B** switch while it plays, at the same place in the bar. Nothing else changes |
| test a disputed layer by muting it | the five **mute** buttons: everything else stays exactly as it was |
| the smallest committable unit | touch a pad, then touch the bell: the sound is **placed** on the nearest quarter-beat. Touch a sound, then **REMOVE**. **UNDO** steps back through every edit |
| preserve the best checkpoint | **KEEP** stores the current state in the browser; **RESTORE** returns to it (or to the delivered state) |
| deliver an edit map and stems | **EDIT MAP** downloads the placements as a file. **RENDER** makes the mix and five stems in the browser from those placements |

Keys: 1 to 0, - and = play the twelve pads; space plays and stops; z undoes.

## 3 · The primitive (as built)
Each placement carries everything needed to reproduce or remove it:
`source_hash, sample_in, sample_out, channel_mode, fades, stretch, pitch_shift, gain, pan, lane, bar, beat, timing_offset, intent, evidence, parent_revision`.
- **Source time is in samples.** Arrangement time is bar and beat. At 72 BPM and 44.1 kHz one beat is exactly **36,750 samples**, so nothing drifts.
- **Three kinds of evidence are kept apart:** the catalog's names (`identity.json`), the signal measurements (the `evidence` field), and the rendered mix (the checks in section 7).

## 4 · The sources (the archivist)
- **The four catalog pages have no audio links in them.** Their track lists are filled in by `album-page.js`. They were resolved from that script: **70 entries**.
- **69 were decoded** (183 minutes) and hashed. **1 was not found** by my resolver, an accented file name (*El Sueño De La Divina*); it was left out and the run continued.
- **No exact duplicates.** Four pairs were near-duplicates by their spectral contour; one of each pair was dropped from the search.
- **The primary** is `S29988c`, 128.8 s.
- **The reference instrumental was not used as audio.** Only what the brief stated was taken from it: 72 BPM, 4/4, a two-bar recurrence.

## 5 · What the signal said
**The primary sample**
| finding | measured |
|---|---|
| it has no low end | 90% of its energy lies between 237 and 840 Hz; almost nothing below 120 Hz. The weight has to be made new |
| it already moves at 72 | in its strongest phrase the second onset comes 0.83 s after the first: one beat at 72 BPM. No stretching was needed |
| its harmony | long, steady **D** (four places), **C**, **G**, and **A** after D. So the brief's provisional fifths hold, as **D to A** and **C to G** |
| the four cues | **0:13** and **0:49** sit inside the two D-to-A phrases; **0:42** is the C-to-G phrase. **0:03.38** showed no clear attack and was not used |
| beyond the cues | **1:47.66**: the loudest and steadiest D in the file. It is used where the weight returns |

**The catalog search** (names hidden; four independent passes)
| role | raw candidates | what the test was |
|---|---|---|
| attack | 1,940 | a rise out of quiet, a fast fall |
| bed | 683 | one bar of steady level and little change |
| answer | 384 | 1.25 s or more on one pitch |
| tail | 78 | a long fall after an onset |

The queue was collapsed to at most 14 per role (no more than two per source, none within four seconds of another) and each survivor was scored against the primary motif: how much of its energy falls where the motif's does.

**False positives caught by looking at the envelopes of the top candidates**
- **The top "tail"** was a hard cut to digital silence: 53 dB in 50 ms. Rejected; the tail test now needs a gradual fall.
- **The top "answer"** was a fade 30 to 60 dB down: a steady pitch, but almost no sound. Rejected.
- **The top "attacks"** from the catalog were kicks and clicks cut out of silence. Not used: the drums were to be new.

**The one support sound chosen:** a single struck **A** (110.8 Hz) from `Sd3ac86`, falling smoothly 39 dB in one bar. It is in the sample's key, it is both an answer and a tail, and only 11% of its energy overlaps the motif. It was 13 cents sharp against the sub's A and is lowered by 0.16 of a semitone.

**A limit of the search:** 22 sources with clipped samples anywhere in the file were excluded whole. That is stricter than the brief asks (a clean passage in a loud master could have been used).

## 6 · The arrangement
- **The motif:** two bars of the primary, uncut inside: bar one D to A (from 0:10.12), bar two C to G (from 0:41.62).
- **New drums:** a kick, a "knock" (the same kick with its weight filtered out), a snare whose band sits above the motif, a hat.
- **New sub:** sine notes tuned to the pitches measured in the sample (D 72.8 Hz, A 54.85, C 66.1, G 48.55).
- **New textures:** a bar of high air, and one riser.

| proof | what it is |
|---|---|
| **A** | eight bars: roar, drums, sub. Bars 1 to 4 use the knock and no sub. The kick and the sub arrive on bar 5 |
| **B** | A, plus the struck A on beat 4 of bars 1, 3, 5 and 7, where the choir itself moves to A |
| **The break** | bars 1 to 3 the groove, with a riser in bar 3; bar 4 the sub and kick are taken away and the struck A is left ringing; **bar 5 is empty** but for two hats and the air; bar 6 the kick, the sub and the loudest D return together |
| **The whole track** | 36 bars, two minutes: four bars without low end, an eight-bar verse, the four-bar break, an eight-bar hook on the loudest D, a second verse on the other take, and the source's own ending |

## 7 · The hard checks (all passed; `sim/jellystudio/verify.py`)
| check | measured |
|---|---|
| every placement resolves to a source and an exact edit | 929 placements, 16 spans |
| the low end is held four bars and arrives on bar 5 | below 110 Hz: about -54 dB in bars 1 to 4, -15 dB from bar 5 |
| the protected bar | 300 to 3400 Hz: -44 dB in the empty bar against -22 dB in the groove |
| the sub leaves and returns | below 110 Hz: -38 and -43 dB in the two break bars, -13 dB on the return |
| no clipping | peaks at -1.0 dBFS or lower |
| no clicks | the largest step at any edit point is 5% of full scale |
| no drift | every render is a whole number of bars to the sample |
| stems | same zero point, same length; they add up to the master to within 16-bit rounding (80 dB down) |
| **the master bus** | **one fixed gain (+1.02 dB) and nothing else.** No compressor, no limiter. That is why the stems add up exactly |
| the instrument plays what was rendered | the page's own render of each proof matches the reference to 58 dB down; its stems add up to its mix |

## 8 · A against B
**Measured, the two cannot be told apart in quality.** B is A plus one layer, and that layer does not collide with anything.
| | measured |
|---|---|
| where the layer is | beat 4 of bars 1, 3, 5 and 7, decaying into the next bar |
| against the motif (240 to 840 Hz) | 8 to 9 dB under it at the onset, 16 to 21 dB under it after |
| against the low end | 20 dB under the bass |
| pitch | an octave over the sub's A, then a sixth over its C. No clash found |

**The critic's verdict:** "keep or drop cannot be decided from signal data." So B has not lost to A, and it has not won. **The layer is kept in the whole track, provisionally, and the choice is yours:** switch A and B while it plays, or mute ANSWER.

**What the independent critic found, and what was changed** (one repair pass; each change is marked `r2` in the edit map)
| the critic's finding | the repair | measured after |
|---|---|---|
| in bars 1 and 3, with no bass under it, the answer stood 3 dB above everything | the answer is 4 dB lower in the four bars before the low end arrives | |
| the return of the weight was no heavier than the bars before the break (0.0 dB) | the bar before the break carries a lighter sub; the return carries a heavier sub and kick | the return is **5.0 dB** above the bar before the break |
| 0.77 s of digital silence in the empty bar | the high air runs through it (5 to 11 kHz, outside the vocal band) | no zero samples; the vocal band is still 22 dB clear |
| every eight-bar section was one two-bar loop four times, sample for sample | a two-snare turnaround and a dropped sub note every fourth bar; the second verse starts without hats; the answer fills the empty beat 4 of the hook | no neighbouring two-bar pairs are identical |
| the low end held about 80% of the energy, 8 dB over the mid band | the sub is 3 dB lower | bass and roar are now 2 dB apart |

**Found by the critic and left alone**
- The struck note's upper partials ring into the empty bar at -41 dB, gone by beat 3.
- The loudest D is 14 cents below the main motif's D. It is the same choir, later in the same recording.
- The ending fades over the last sixteenth from -44 dB.

**No second critic pass was run.** After the repairs the checks found no specific problem left to solve. The remaining questions are for the ear.

## 9 · The cue sheet (exact edits)
| span | source | sample in | sample out | time in source | fades in / out (samples) | uses in the whole track | lane |
|---|---|---|---|---|---|---|---|
| `roar_D` | Hollow Square Roar-Brute (`S29988c`, sha256 `29988cce89b7…`) | 446,292 | 593,292 | 0:10.120 to 0:13.453 | 661 / 2646 | 8 | primary |
| `roar_C` | Hollow Square Roar-Brute (`S29988c`, sha256 `29988cce89b7…`) | 1,835,442 | 1,982,442 | 0:41.620 to 0:44.953 | 661 / 2646 | 15 | primary |
| `roar_D2` | Hollow Square Roar-Brute (`S29988c`, sha256 `29988cce89b7…`) | 2,148,552 | 2,295,552 | 0:48.720 to 0:52.053 | 661 / 2646 | 4 | primary |
| `roar_long` | Hollow Square Roar-Brute (`S29988c`, sha256 `29988cce89b7…`) | 4,747,806 | 4,858,056 | 1:47.660 to 1:50.160 | 661 / 3528 | 5 | primary |
| `roar_out` | Hollow Square Roar-Brute (`S29988c`, sha256 `29988cce89b7…`) | 4,939,200 | 5,380,200 | 1:52.000 to 2:02.000 | 661 / 17640 | 1 | primary |
| `answer_A` | Boxes on My Back (`Sd3ac86`, sha256 `d3ac8625d68e…`) | 6,349,090 | 6,496,090 | 2:23.970 to 2:27.304 | 176 / 13230 | 12 | support |
| `kick` | made for this track | 0 | 22,050 |  | 0 / 256 | 86 | drums |
| `knock` | made for this track | 0 | 8,820 |  | 0 / 256 | 12 | drums |
| `snare` | made for this track | 0 | 13,230 |  | 0 / 256 | 75 | drums |
| `hat` | made for this track | 0 | 2,646 |  | 0 / 256 | 250 | drums |
| `sub_D` | made for this track | 0 | 110,250 |  | 64 / 256 | 16 | bass |
| `sub_A` | made for this track | 0 | 36,750 |  | 64 / 256 | 15 | bass |
| `sub_C` | made for this track | 0 | 73,500 |  | 64 / 256 | 12 | bass |
| `sub_G` | made for this track | 0 | 73,500 |  | 64 / 256 | 6 | bass |
| `riser` | made for this track | 0 | 147,000 |  | 64 / 256 | 1 | texture |
| `hiss` | made for this track | 0 | 147,000 |  | 64 / 256 | 33 | texture |

Every placement of these spans, with its bar, beat, gain and reason, is in `scion.json`; **EDIT MAP** in the instrument downloads the current state.

## 10 · The swarm, honestly
| role in the brief | who did it |
|---|---|
| archivist, signal scouts, audition producer, builders, integrator | one agent, in separate passes with separate scripts |
| independent critic | a second agent, given only four unlabelled, level-matched files and no explanation |

Neither could listen. "Audition" here means measuring a candidate against the motif. **The listening is still to be done, by you.**

## 11 · Not yet judged
- **Everything by ear:** the drum sounds, the sub's level, whether the struck A helps, whether the break works under the vocal.
- **The vocal itself.** No vocal take was in the brief; the protected bar is measured as empty, not tested against a voice.
- **The instrument on a phone,** by hand. It was run in a simulated phone browser only.
- **One catalog track** was not indexed (the accented file name).

## 12 · A third revision: better drums, a better sub, and three remixes of other sources
**The direction (after listening):** "The drums and sub don't sound good enough, make them better, and make some other good remixes of others."

Sections 6 to 9 describe the first two revisions. The tracks in the instrument are now the ones below. **Still nothing was heard here:** what follows says what was changed and what was measured. Whether it is better is for your ear.

### Why the first drums and sub were weak (measured)
| sound | what it was | measured |
|---|---|---|
| kick | one sine sweep and a tick of noise | 94% of its energy below 120 Hz; nothing above 400 Hz: no knock, no click |
| snare | filtered noise and one tone | 6% of its energy between 400 Hz and 2 kHz, where a snare's rattle is |
| hat | a 60 ms burst of noise | no pitch, no ring, every hit the same |
| sub | a flat sine | 99% between 60 and 120 Hz: a phone or laptop speaker plays none of it |
| the pattern | every hit on the grid at one of two levels | no swing, no ghost notes, no open hat |

### What was done
**Two new kits, to compare** (two tracks in the instrument: BOXES · FOUND DRUMS and BOXES · MADE DRUMS).
| | FOUND | MADE |
|---|---|---|
| kick | cut from *Subterranean Dreams* at 1:07: it stands 60 dB out of silence | a driven body that falls from 230 to 49 Hz, a louder click, a low thump; 15% of its energy now between 120 and 400 Hz |
| snare | cut from *The Cathedral of Tape Echo* at 2:00 (54 dB out of silence) | two falling tones, hiss, a separate layer of rattle (22% between 400 Hz and 2 kHz, up from 6%), and a short room, different in each ear |
| hat | cut from *Trap-Tox & Cardboard* at 0:18 (50 dB out of silence) | six square waves at clashing pitches, as the old drum machines did; a closed and an open one |

**A limit of the search:** 299 hits in the catalog rise sharply out of quiet, but nearly all have music under them within a third of a second. Only these three were clean enough to use as they are. The found hat is mostly middle (63% between 400 Hz and 2 kHz): it may read as a click, not a hat.

**The sub** is now an 808-style note:
- it starts almost an octave high and falls to its pitch in about a hundredth of a second;
- it is driven, so it has overtones: 10% of its energy is now above 120 Hz (it was 1%), which a small speaker can play;
- it decays, where the first was flat;
- under a kick it fades in over 28 ms, so the kick's click is heard first.

**The pattern:**
- sixteenth-note hats with swing and three levels of accent;
- ghost snares, and an open hat at the end of every second bar;
- small seeded differences in time and level on hats and ghosts, so no two bars are the same machine.

### Three remixes of other sources
**How the sources were chosen (names hidden):** every source was scored by how many loud, steady, pitched phrases it holds that sit together (thirds, fourths, fifths, sixths). Six qualified; the best from three different catalogs were taken.

**How they are made:** each phrase is cut at its own onset into a short chop and replayed on a new grid. The source's own tempo therefore does not matter, and nothing is stretched.

| remix | source (revealed after ranking) | tempo | the idea |
|---|---|---|---|
| **1 · BOOM-BAP** | *Blown-Out Sanctuary* | 86 | four chops (A, A, E, E) on a swung grid; a new sub at each chop's own pitch, brought down by octaves |
| **2 · DUB** | *Chiral Cargo & The Rope-Not-Stick Choir* | 63 | kick and snare together on beat three; an echo made of five single placements, each 5 dB quieter, thrown from side to side. Every repeat can be removed on the bell |
| **3 · HALF-TIME** | *Steppe Telegraph & The 6,500-Voice Lavender Shanty* | 70 | stabs, snare on three, hat rolls |

Each is 21 bars (59 to 80 seconds): four bars without drums' weight, an eight-bar drop, a two-bar break, a six-bar return, a last word.

**No new sub in remixes 2 and 3.** Their chops already hold 83 to 87% of their energy below 110 Hz. A second bass would fight them, so the sample is its own bass.

**A false positive caught:** three different sources all appeared to sing the same A sharp at 918.8 Hz. That number is the upper edge of my pitch search, not a pitch. Those phrases were thrown out and the sources chosen again.

### Checked
| check | result |
|---|---|
| both versions of the main track | low end held four bars and arriving on bar 5; the voice bar 20 dB clear or more; the sub out for two bars and back 5 dB heavier; peaks at -1.0 dBFS; stems add up to the master (79 dB down) |
| the three remixes | whole numbers of bars; peaks under -1 dBFS; no clicks at edit points |
| the instrument | all five tracks load and play with no errors; its own render of each whole track matches the reference to between 48 and 61 dB down; the short scenes match less closely (33 to 38 dB), at the cut-off of their last notes |

### Not done, not judged
- **No blind critic this time.** The complaint was about how it sounds, which a measuring critic cannot settle.
- **Switching between FOUND and MADE reloads the page.** They are two tracks, so the comparison is not instant.
- **The remixes by ear:** whether the chops make a phrase, and whether the chosen sources were the right "others". Name the tracks you want and they can be built the same way.
- **The remix chops were chosen by steadiness of pitch.** That favours held notes and drones over rhythmic or sung lines.
