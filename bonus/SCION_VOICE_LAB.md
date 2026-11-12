# SCION SYSTEM INSTRUCTION · THE VOICE LAB

Where: `bonus/voicelab.html` (live: `/contaminant-jelly/bonus/voicelab.html`; also VOICE LAB in the orchestra's menu).

## 1. The problem, stated plainly
The verdict on the singing and rapping voices: unlistenable to a wide audience, a good first start. I built
them without being able to hear them. Every earlier claim about them was about level and timing, never about
whether they are pleasant. So the next step cannot be me guessing harder. It has to be a way for a listener to
tell the system what is wrong, in terms the system can act on.

## 2. The model: Pask's conversation, applied
Taken from the notes supplied (Pask, Pangaro, Dubberly; Benjamin, Whorf and Sapir as the reason two people can
mean different things by "harsh").

| Pask | In the lab |
|---|---|
| **How:** show the rule and what it does | B is described as dial moves: "Tension 0.36 → 0.26 · Warmth 5600 → 4700" |
| **Why:** the rationale the rule serves | You give the reason first ("A is too harsh"). The lab says which dials that reason moves |
| **Shared modelling facility:** somewhere both can build and test | A and B, playable, on a line you can change |
| **Teach-back:** apply it to a fresh case and be corrected | TRY A ON A NEW LINE, then YES or NO. A recipe that only works on one sentence is thrown back |
| **Agreement over an understanding** | The recipe: every dial, copied as one line of text I can read and remake the songs from |
| Pangaro: the goal can change | "No difference" is recorded too: it says that reason was not the cause, which changes what to try |

Thirteen reasons are offered (too harsh, too robotic, too thin, too fast, too slow, hard to understand, too
wobbly, too dry, too echoey, too breathy, too dull, too high, too low) plus "surprise me". Each moves named dials.
"Harsh" for you may not be what I mapped it to; the verdict buttons are where that shows.

## 3. What the dials are
**The throat** (the voice has to be made again): breath, tension, brightness, vibrato, drift, speed, pitch.
**The mix** (works on sound that already exists): warmth (a treble cut), room, doubling (two more copies of the
voice a few milliseconds apart and drifting, so one synthetic voice becomes a small group).

I had never set the throat at all: every voice so far used the engine's defaults. A probe confirmed breath,
tension, brightness, roughness and drift each change the output.

## 4. What changed for listeners today, without the lab
- A **soft default recipe**: less tension and edge, more air and drift, no roughness or fry, 8 % slower.
- A **mix chain** on every voice in the orchestra: low cut, treble cut at 5.6 kHz, doubling, a little room, gentle
  levelling.
- Talk mode speaks at 108 beats a minute instead of 132.
- The English songs are being made again with the soft throat.

Measured on one song (first five seconds): energy above 2 kHz went from 6.5 % (old) to 5.6 % (soft throat) to
4.7 % (soft throat plus mix). **That is a small change, and a number is not a judgement.** I do not know that it
sounds better.

## 5. Simpler test interfaces
The lab is one plain page: no 3D, no orchestra, one line, two buttons to listen, reasons to press. It is the
pattern for testing other things the same way (a translation, a paint, a dance): one case, A and B, a reason,
a fresh case.

## 6. What was checked
On a phone-sized screen: A played; "too harsh" produced B with its dial moves named; B kept; "too fast" tried and
rejected; a fresh line played and was confirmed; the recipe saved; the log listed each decision. The orchestra,
opened afterwards, had the saved recipe and spoke through the mix chain. No page errors.

## 7. What was not checked
All of it by ear. Also: the other four languages have not been made again with the soft throat (only the mix
applies to them), and the engine may have a ceiling no recipe gets past. If the lab cannot find a voice people
like, the answer is a different voice engine or recorded singers, and the lab log will be the evidence for that.

## 8. How to send me a result
Press USE A IN THE ORCHESTRA, copy the line that starts `RECIPE`, and paste it to me. I will make all the songs
again with it.
