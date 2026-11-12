# SCION SYSTEM INSTRUCTION · STEER, TOUCH, LISTEN

Three things were called critical: there is no steering control in the worlds or the game; the jelly should be
real jelly you can touch to play; and Amharic and Chinese must be effective.

## 1. Steering
**What was wrong.** WALK was hidden in the menu, and the on-screen stick only appeared after you had found it,
and only on touch screens. On a phone the worlds and the game looked as though they could not be steered.

**Now.**
- A stick is always on screen at lower left, in every world and in the game, on phones and desktops.
- Touching it takes the camera. There is no mode to find first.
- Drag the picture to look. ▲ and ▼ rise and sink. AUTO gives the camera back to the edit.
- A line above the stick says so until you first use it. It hides during theatre and the demo, and on a phone
  while the talk bar is open (they share the same corner).

Checked on a phone-sized screen in the film depot: the stick was visible before anything was pressed; pushing it
moved the camera from (1.3, 3.1, 1.9) to (−2.7, 2.8, 0.2); dragging the picture turned the view; AUTO handed the
camera back; the stick was present in the game.
Not checked: a real finger on a real phone.

## 2. Touch the jelly
The body built from the voice (`SCION_TRACT_JELLY.md`) can now be pressed, in the voice lab and in talk.
- **It gives where you press.** The touch pushes that ring of the bell inward; the springs carry the dent along the
  body and it wobbles back.
- **It sings.** Near the rim it says "ma", then "me", "mi", "mo", and "mu" near the crown. Each press in a row steps
  up a five-note scale. In talk, each person's jelly answers at its own pitch.
- The five syllables are made once, the first time you touch (a second or two), so later touches are immediate.
- While it sings, the body takes the shape of that syllable: the rim closes on the "m" and opens on the vowel.

Checked in the lab: two touches at different heights produced "mo" then "mi"; a still shows the dent.
Not checked: touching in talk (same code, not run); the sound; whether this feels like playing an instrument.
Not built: touching the four singers or the orchestra's soloists; pressing and holding to bend a note. The engine
has a touchable membrane for exactly that, but it would have to run live with the sound, which it does not yet.

## 3. Amharic and Chinese
I cannot make these effective by reasoning, because I cannot hear them. What I can do is fix what is known to be
wrong and give a speaker a fast way to show me the rest.

**Fixed**
- **Mandarin, sung:** each note now leans the way its tone goes (rising starts low, falling starts high and drops,
  the low tone dips). Before, sung Mandarin ignored tones completely.
- **Mandarin, spoken:** full tones (previous pass).
- **Amharic:** the ejectives ቀ ጠ ጨ ጰ ጸ are now a stop followed by a catch in the throat, not a plain stop.
- All Mandarin and Amharic songs are being made again with these and with the softer voice.

**The listening test** (voice lab, section 5)
- Choose a language. The jelly says one of four words that differ by one thing: 妈 麻 马 骂 (tone), 四 十 西 七,
  八 怕 大 他 (aspiration), ጠላ ተላ ደላ ሰላ, ቀን ከን ገን ነን (ejective), and whole phrases.
- Press the one you heard. Twelve rounds. Chance is 3 of 12.
- The result is one line, `LISTEN zh 7/12 said→heard: 妈→麻, …`, which tells me exactly which sounds fail.

That is the only honest measure of "effective" available here. Until a speaker of each language has run it,
**I do not claim either language works.**

Checked: 54 test words across the four languages give the syllables they should; one song rendered in each of
Mandarin and Amharic with the new rules; the listening test ran twelve rounds and produced its result line (a
script pressed the first button every time, so its score means nothing).

## 4. If the score is low
A voice model built for English may not be able to make these languages clear whatever table it is given. If a
speaker scores near chance, the right move is a voice that was made for the language (recorded syllables, or a
different engine), with the jelly body driven by loudness. The lab's result line is the evidence for that call.
