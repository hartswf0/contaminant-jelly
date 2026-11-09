# SCION SYSTEM INSTRUCTION: THE STEER LAB 4D (your arms reach into a fourth direction)

**The direction:** "Yes, build Steer Lab 4D. This is convoluted, hard to find or use, too many things."

**Role.** One idea, one gesture, almost no interface.
- **The idea:** a stone can live in a fourth direction, w.
- **The gesture:** the lab's own. Every finger is a tentacle; touch a stone and an arm grabs it.

There is no slider, strip, twist or mode. The fourth direction is steered with the same hand that steers the other three.

**Where:**
- `bonus/steerlab4d.html`;
- first among the Steer Labs on the index's Bonus shelf;
- "the 4D lab →" on the flat lab's card and the 3D lab's card;
- a link on the Ten Bodies card.

## 1 · The one rule
**An arm holding a stone at another w pulls you along w toward it, harder the more load it takes.**

Everything else follows from this rule:
- **Stones:**
  - each stone is a hypersphere: you see it as the sphere where it crosses your w;
  - it is solid only there;
  - at another w you pass straight through the place it fills.
- **Handholds:** each stone has a shell of them at its own w, so you can reach stones that are not here yet:
  - **blue:** further along w;
  - **amber:** behind;
  - **gold:** here;
  - they fade with distance in w, and you can reach them up to 5.2 away.
- **Two arms, two slices:** hold stones at two different w and you hang between their slices, at the w where their pulls balance.
- **Your arms show it:** an arm holding a blue stone glows blue, an amber one amber.
- **The only instrument:** a thin w gauge on the right edge, showing you (gold), the lights, and every stone you hold.

## 2 · Three stages, one lesson each (they advance on their own)
| stage | the problem | the lesson |
|---|---|---|
| 1 · The Wall | A wall of stones from floor to ceiling, side to side. A few blue stones hang in front of it. | Grab a blue stone: it pulls you along w to where the wall is not, and you swim through. Amber stones beyond bring you back. |
| 2 · Three Slices | Three lights, each at its own w (−3, 0, +3), with stones of matching w around each | Steer in w by choosing what you hold. |
| 3 · Hang Between | The last light is at w 2, and nothing lives there. | Hold a stone at w 0 and a stone at w 4, and hang between them. |

## 3 · What was cut, and why
The steering in Ten Bodies (`bodies.html`) and the 3D lab became too much to find and use. So:
- **The 4D lab has no camera chip.** There is only one camera: behind the jelly, still while an arm is planted, widening to frame what you hold.
- **There is no posture glyph and no move log.** There is one hint per stage, spoken once.
- **The card is one sentence.**
- **On a phone, the Ten Bodies card shows only:**
  - one instruction (the other two are spoken during play);
  - verb-only chips;
  - a single short line of links.

## 4 · Tested (simulated input, swiftshader, timed on the game clock)
| test | result |
|---|---|
| Stage 1 at w 0, swimming at the wall | stopped by the wall |
| Stage 1: grabbed a blue stone 6.7 m away | pulled to w 3.7; passed through the wall ("passed through a stone, in w") |
| Stage 3: one stone at w 0, one at w 4 | hung at w 2.05 ("hanging between two slices"); took the light |
| A phone-sized screen (Pixel 7) | the 4D lab's card, the trimmed Ten Bodies card and the index shelf all fit, with no errors |

**Not yet judged on a real phone:**
- whether pulling along w *feels* like a direction;
- whether blue and amber read without explanation.
