# SCION SYSTEM INSTRUCTION · THE SPEAKING CAST

Where: `bonus/jellyorchestra.html` (Bolas edition: `/bolas/cities/`). SING is on by default; `&sing=0` turns it off.

## 1. Thesis
The orchestra played samples. Nobody in it had a voice. Now four jellyfish sing words, in every song and in
every world. The voice is not a recording and not a text-to-speech service: it is a physical model of a vocal
tract, and each bell squeezes on the syllables the model was told to sing.

## 2. The cast
| Name | Voice | Body | Job |
|---|---|---|---|
| BRUTE | low | the sentinel | the root, in the chorus |
| HOLLOW | tenor | the reel | answers the title |
| LAVENDER | lead | the golden jelly | sings the title first |
| TICK | small, high | the doodle jelly | sings what the song is made of |

They stand in a row in front of the orchestra. Whoever is singing rises, comes forward, leans to the lens and
wears their name. The words appear as a line, with the syllable being sung lit.

## 3. What they sing
A sixteen-bar cycle, repeated for the length of the song:
| Bars | Who | Words |
|---|---|---|
| 1 | LAVENDER | the song's title |
| 5 | HOLLOW | the title again, on a different tune |
| 9 | TICK | the song's mechanism (for the swarm songs), otherwise the title |
| 13 | all four | the title, in four registers |

- A title of one or two words is sung three times.
- Tempo is the song's own. The first syllable lands on the second beat of the bar.
- Notes are a minor pentatonic on a root estimated from each song's audio. This is an estimate from the
  average spectrum, not a transcription, so some songs may be sung in the wrong key.
- Melodies are fixed per song (made from the song's id), so a song is sung the same way every time.

## 4. How the voice is made
- Engine: CHIMERA by Jameson Hodge (MIT licence), commit e33221d, with the speaking-film branch supplied for this
  work (`voice/film.rs`, a membrane over the airway). The compiled engine and its pronunciation dictionary are in
  `bonus/jellystudio/voice/` (`chimera.wasm`, `dict.txt.gz`).
- `sim/jellystudio/sing_build.js` runs the engine offline in Node: words to syllables, syllables and notes to a plan
  of articulator gestures, plan to sound. One sound file and one timing file per song.
- `sim/jellystudio/keys.py` estimates the roots.
- The page does not run the engine. It plays the rendered parts in time with the song and reads the syllable
  times from the plan. So the bells move on what was planned, not on what is heard.
- The film membrane (the touchable part of the speaking-film branch) is not used yet: gain is zero.

## 5. Staying in the world
The buttons at the bottom used to leave the page. Now:
- WORLDS opens a picker over the scene. Choose a place and you are there, with the song still playing. Choose a
  paint with PAINT OVER THIS PLACE lit and it is laid over the place you are in.
- OPEN IN THE STUDIO, SOLO: THE REAL JELLY and OPEN IN THE LAB open in a pane beside the world. The orchestra
  pauses while the pane is open and resumes when it closes. The world behind can still be walked.

## 6. What was checked
- One song in a browser: LAVENDER's part started at 2.7 s and HOLLOW's at 14.1 s (bars 1 and 5 at 74 beats a
  minute), the lyric line showed the right singer and words, no page errors.
- The picker showed 37 tiles with all stills loaded; choosing THE ORBIT changed the place without changing the page.
- The pane opened the solo jelly, the orchestra paused, and it resumed on close.
- All 50 songs were rendered: 1,219 seconds of singing in 12 MB. Per song, peak level is between 0.70 and 0.92 and
  between 58% and 82% of samples are above the noise floor, so no part is silent or clipped.

## 7. What was not checked
- I cannot hear. Whether the words are intelligible, in tune with the song, or pleasant is unjudged.
- The mix: the voices are at one fixed level against every song.
- RECORD may not capture the voices; it was not tested with them.
- Phone speed with four more animals, and the live site.

## 8. Next
1. Run the engine live in the page so you can type a line and a jelly sings it.
2. Use the film membrane: touch a singer's bell and the vowel changes.
3. Let each world give the cast different words (the depot sings film titles, the store sings what is rented).
