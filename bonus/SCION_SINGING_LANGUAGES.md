# SCION SYSTEM INSTRUCTION · FIVE SINGING LANGUAGES

Where: `bonus/jellyorchestra.html` (Bolas edition `/bolas/cities/`). Menu → SUNG IN, or `?voice=zh`, `am`, `es`, `pt`, `en`.

## 1. Thesis
The cast could only sing English because the voice engine's dictionary is English. But the engine does not need
a dictionary: it needs speech sounds. So each new language gets a table from its writing to sounds the engine
already has, and the same four jellyfish sing Mandarin, Amharic, Spanish and Portuguese.

## 2. What "train" means here
Nothing was trained. No model learned anything. Each language has:
- **a pronunciation table** written by hand (`bonus/jellystudio/voice/g2p.js`);
- **test words** with the syllables they must produce (`sim/jellystudio/g2p_test.js`): 52 words, all passing;
- **a probe of the engine** that showed which sounds are real and which silently fall back, so the tables only
  use real ones.
If you want real training (a voice that learns from recordings of each language), that is a different project
and needs recordings and a model that can learn.

## 3. The engine's sounds
Probed by comparing each sound's plan with a nonsense symbol's.
- **Has:** p b t d k g m n ŋ ɲ f v s z ʃ ʒ ʂ ʐ ç x ɣ h β ts dz tʃ dʒ l ʎ r ɾ j w and the vowels
  i y ɨ ɯ u e ø ɤ o ə ɛ ɔ a ɑ ɐ plus five diphthongs.
- **Lacks:** ɕ tɕ tʂ, all aspirated stops, all ejectives, the glide ɥ, nasal vowels, long vowels.

## 4. The four tables
| Language | Writing → sound | Approximations (what a native ear will notice) |
|---|---|---|
| **Mandarin** | Character → pinyin (table of 6,763 characters) → initial and final | **Tones are not sung**: the melody decides pitch. j/zh and q/ch are merged; x is sung as ç; the ü-glide is j. A character with two readings takes its commonest one when you type (the rendered songs use readings chosen in context) |
| **Amharic** | Each fidel is a consonant row and one of seven vowel orders | **Ejectives are plain stops** (ጠ as t, ቀ as k, ጸ as ts). Doubled consonants are not written, so not sung. Whether a sixth-order letter carries a vowel is a rule of thumb |
| **Spanish** | Spelling rules, Latin American (z and soft c as s, ll as y) | b/v, d, g are always hard; no linking between words |
| **Portuguese** | Spelling rules, Brazilian (final e as i, final o as u, ti as "chi") | **Nasal vowels are vowel plus n**; open and closed e/o follow the accent mark only; final r is h |

One syllable is one bell squeeze. In Mandarin one character lights per syllable; in Amharic one or two fidel.

## 5. What they sing
- The song's title, translated, on the same sixteen-bar cycle (LAVENDER, HOLLOW, TICK, all four).
- Mandarin also has the mechanisms for TICK. The other three sing the title in TICK's slot.
- **All translations are mine, made for this, and not checked by native speakers.** The Amharic is the one I
  trust least.
- An English subtitle (or Chinese, in the Chinese interface) runs under anything sung in another language.

## 6. Writing a bar
The songbook has a language choice next to the singer. Type in any of the five and the engine runs in the page.

## 7. What was checked
- Test words: Spanish 14/14, Portuguese 14/14, Amharic 12/12, Mandarin 12/12.
- All 50 songs rendered in each of the four languages. Every file was measured when made; the figures are in each language's `index.json`.
- In a browser, each language: the right words lit in the right script, with the English subtitle. No errors.
- Typed bars: 水母在唱歌 gave five syllables; "las medusas cantan en la ciudad" gave ten.

## 8. What was not checked
- **I cannot hear.** Whether any of this is intelligible to a speaker of the language is unjudged, and for a
  voice model built for English it may well not be.
- The translations. Typed bars in Amharic and Portuguese. Phones. The live site.

## 9. Next
- Sing Mandarin tones as small bends inside each note, and test whether words become clearer.
- Ask a native speaker of each language for five corrections and add them to the test words.

## 10. Jelly translation
`?voice=all`, or TRANSLATE in the songbook, or SUNG IN → TRANSLATION in the menu.

One line is handed from singer to singer, each in another language, a new one every three bars:
| Bar | Who | Language |
|---|---|---|
| 1 | LAVENDER | English |
| 4 | HOLLOW | Mandarin |
| 7 | TICK | Spanish |
| 10 | all four | Amharic |
| 13 | LAVENDER | Portuguese |

- Under the singer a card shows the line in all five languages, with the one being sung lit.
- The songbook now lists every song in all five languages: 50 songs, four translations each.
- **This is not a translator.** It cannot translate a sentence you type. Every line it knows was translated by
  hand in advance. Typing a bar still works in any one language, but it is sung as written, not translated.
  A real translator would need a translation service or model, which this page does not have.

Checked: on a phone-sized screen, all five languages took their turn in order with the right singer and script,
the card showed five lines, and the songbook showed four translations for each of 50 songs. No page errors.

**A fault I shipped and fixed:** the version pushed just before this one failed to start unless the address
contained `?voice=`. It was live on main for a short time. The plain address was re-tested and loads.
