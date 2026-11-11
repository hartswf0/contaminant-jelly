# SCION RUN · THE CHORUS, THE DOCK AND THE THEATRE

Mode: RUN (the request was to build). ttl=2. Where: `bonus/jellyorchestra.html` (Bolas edition `/bolas/cities/`).
Addresses: `?book=1` opens the chorus, `?theatre=1` starts theatre, `?clean=0` shows every control.

## I. Shattering and collector diagnostic
- **Force in motion:** fifty songs, a cast that sings, some fifty places and paints.
- **Inherited ritual:** every new thing got a button. The screen filled up, and on a phone the buttons covered the picture.
- **The Lie:** more controls on screen means more control.
- **Catalyst:** a phone screenshot in which the lyric, the song title and three rows of buttons sit on top of each other.
- **Mirror moment:** with everything hidden, one row of seven buttons still reaches every place, song and tool.
- **Abandoned objective:** show every option at once. **Novelty bait:** the cast already knows where each syllable
  falls. **Deceptive potential:** if the page knows the syllables, a person can take a turn in the same slot.
- **Deceptive step:** the first cast build sang at you. Nothing could answer. The slot at bar 13 is now openable.

## II. Genome
```yaml
title: "The Chorus"
seed: "Four jellyfish sing every song. Write them a bar, take the last line yourself, or sit back and let the theatre run."
active_axis: SONIC
ancestral_sources:
  - {id: chimera-speaking-film, anchor: "supplied wasm and patch, voice/film.rs", role: "words to a physical voice", evidence: "executed"}
  - {id: scion-compiler-prompt, anchor: "supplied POML, sections 3 and 7", role: "play theory; hardest slice first", evidence: "supplied note"}
  - {id: one-world, anchor: "bonus/SCION_ONE_WORLD.md", role: "place, paint, song, camera as four dials", evidence: "built"}
origin_conditions: ["A phone screen", "A voice that is planned before it is heard"]
formation_epochs:
  - {id: sampled-orchestra, weight: 40, event: "every jelly is one sound", reason: "still the bed under everything"}
  - {id: sung-title, weight: 70, event: "the cast sings each song's title", reason: "gives every song words"}
  - {id: open-slot, weight: 95, event: "a bar can be written, or left for you", reason: "turns watching into taking a turn"}
  - {id: theatre, weight: 80, event: "the interface leaves and a programme runs", reason: "the only way to see all of it without steering"}
migration_map:
  - {from: "karaoke", to: "jelly chorus", kept: "words lit in time", optics: "the singer rises and wears a name", formalism: "syllable times come from the plan", concept: "the machine sings first", sound: "physical voice model", loss: "your own recorded voice", test: "C1, C3"}
  - {from: "control panel", to: "dock and sheets", kept: "every action reachable", optics: "one row; sheets from the bottom on a phone", formalism: "seven buttons, three sheets", concept: "hide until asked", sound: "n/a", loss: "seeing all options at once", test: "C4"}
jukebox_timeline:
  - {at: "bar 1", source: "LAVENDER", role: "consequence", rule: "the title"}
  - {at: "bar 5", source: "HOLLOW", role: "consequence", rule: "the title, another tune"}
  - {at: "bar 9", source: "TICK, or your bar", role: "consequence", rule: "the mechanism, or what you wrote"}
  - {at: "bar 12", source: "the lyric line", role: "anticipation", rule: "4 3 2 1, only when YOUR TURN is on"}
  - {at: "bar 13", source: "all four, or silence", role: "consequence or silence", rule: "silent when the turn is yours"}
signature_rules: ["A bell squeezes only on a planned syllable.", "Your bar replaces TICK's, never the title.", "In theatre nothing is on screen but the picture, the words and a title card."]
tagline: "They sing it first. Then it is your turn."
ttl: 2
lineage_tags: ["#speaking-cast", "#open-slot", "#one-row-dock", "#theatre-programme"]
```

## III. Theory of play and Olog
I will first construct the theory of play, then the architecture.
1. **Invitation:** touch CHORUS. Stop by closing the songbook.
2. **Magic circle:** sixteen bars; the song's clock; you may leave at any bar.
3. **Stance:** wanting to hear a jellyfish say your words, or to come in on time.
4. **Illusion:** that the four are a group with parts. Supported by fixed roles and fixed slots.
5. **Grammar:** pick a song, write a bar, choose who, RAP or sung, YOUR TURN, MIC. A bar with no sayable words is refused with a reason.
6. **Resistance:** the bar comes in only on a bar line, and the tempo is the song's.
7. **Chance:** none. The same words, voice and song give the same sound.
8. **Memory:** your bar stays in TICK's slot until the song changes or you clear it.
9. **Spoil-sport:** not singing on your turn. The slot stays silent; nothing scores it.
10. **Change tests:** (a) mute the sound: can you still take your turn from the count and the lit words? (b) a 104 bpm song: does a twelve-syllable bar still fit before the next slot?

```
◻(TYPED_LINE) → [is planned as] → ◻(GESTURE_PLAN)        fails: no words in the dictionary → refusal
◻(GESTURE_PLAN) → [is rendered as] → ◻(VOICE_PART)       same plan, same sound
◻(GESTURE_PLAN) → [yields] → ◻(SYLLABLE_TIMES)
◻(SONG_CLOCK) × ◻(SLOT) → [starts] → ◻(VOICE_PART)       first syllable on beat 2
◻(SYLLABLE_TIMES) → [drives] → {◻(BELL_SQUEEZE), ◻(LIT_WORD)}
◻(YOUR_TURN) → [blocks] → ◻(VOICE_PART at bar 13)        the words and squeezes still run
◻(THEATRE) → [every 16 bars sets] → {◻(PLACE), ◻(PAINT)}
```
Commuting claim: sound and bell both derive from the plan, so they agree without listening. STRUCTURAL, not measured against the audio.
Assumptions: safe — the song clock is the audio element's; uncertain — estimated keys; requires your decision — whether the microphone should ever record.
Human residue: what the cast should say, and whether a voice model's diction is good enough to be heard as words.

## IV. The artifact
**Interface**
- One dock: menu, previous, play, next, WORLDS, CHORUS, THEATRE. A line above it names the song and place.
- Everything else is hidden by default and lives in three sheets (menu, worlds, songbook) that rise from the bottom on a phone.
- The menu holds the four dials plus SING, WALK, SWERVE, the experiment card, video, record, studio, solo and lab. ALL CONTROLS brings the old bar back.

**The Chorus** (a place: `?look=chorus`)
- A stage with risers. The cast stand at the front, larger, with their names. A wall shows the song and who sings which line.
- **Songbook:** all 50 songs with their words; touch one to hear it.
- **Write a bar:** type a line, choose a singer, RAP (half beats on one note) or sung. The voice engine runs in the page, beside it, and the singer comes in at the next bar, then in TICK's place each time round.
- **YOUR TURN:** bar 13 of each sixteen is left silent for you, with a count-in and the words lit in time.
- **MIC:** a glass jelly at the front squeezes when you make a sound. Nothing is recorded or sent.

**Theatre**
- The interface goes away. Every sixteen bars the orchestra is in another place, often under another paint, with a title card. 52 steps cover every place and every paint. Songs follow on. Touch the picture to get the dock back.

**Evidence (MEASURED, local copy, headless browser)**
- C1 phone 390 wide: old bar, card, plate hidden; the dock spans 28 to 362 px. No errors.
- C2 songbook: 50 songs listed, the current one marked, place changed to the chorus.
- C3 typed bar "boxes on my back and a city made of film": engine loaded in the page, 12 syllables, 5.9 s, peak 0.70; TICK's name and the words appeared on the lyric line at the next bar.
- C4 theatre: step 1 of 52 in DEEP WATER, then LIGHT ALONE under STENCIL; dock hidden, back on touch.

**Verdict:** bar_unmet for sound, inconclusive overall. I cannot hear: diction, tuning and the mix are unjudged. Independent acceptance is pending your ears.
**Not run:** YOUR TURN and MIC with a real voice; a touch screen; the live site; RECORD with voices.

## V. Philogyny, wedge, reentry
- **relocate_memory:** keep bars people write in the songbook so the next visitor hears them. Reopen when there is somewhere to store them.
- **invert_goal:** the cast leaves gaps and scores nothing; instead the orchestra thins when you are quiet. Test: does silence feel like your fault?
- **transmute_medium:** theatre as a rendered film, one file per programme. Strongest discarded: it needs offline frame rendering.
- **Wedge:** one timing contract (syllable times from the plan) now drives sound, bells, lyric line and the open slot. Next user of it: the lab.
- **Reentry:** parent this revision; mutation spawn_echo; changed rule "the cast answers what the microphone hears"; protected "a bell squeezes only on a planned syllable"; ttl 1.

#speaking-cast #open-slot #one-row-dock #theatre-programme #plan-drives-everything
