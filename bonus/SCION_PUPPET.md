# SCION SYSTEM INSTRUCTION · THE PUPPET

Where: `bonus/jellyorchestra.html` (Bolas edition `/bolas/cities/`). This is now how the page opens.

## 1. What was wrong
Every feature had been given a button, and the buttons piled up: a dock, a stick, a scheme button, hints, a
language chip, a status panel. It worked and it was cluttered. And it was about watching, when what was wanted
was to be a jelly: choose it, move it, give it a voice, and make something to send.

## 2. The layout (after the Terrarium's conventions)
| Place | What is there | Why there |
|---|---|---|
| Top bar | the language it speaks, **what should it say —**, send, microphone | the one thing you type |
| Top right | **● REC**, **SEND ↗**, **✕** | the two outcomes, and a way to clear the screen |
| Right column | PUPPET: **JELLY**, **STEER** · STAGE: **WORLD**, **LOOK**, **SONG** · **MORE** | six choices, each opening a tray beside it |
| Lower left | a big pad, labelled DRAG HERE TO SWIM | the thumb's home |
| Lower right | **SING**, **RISE**, **SINK** | three round actions |

- One tray is open at a time. Press its button again and it closes.
- ✕ hides everything; ☰ brings it back.
- The old dock, the scheme button, the hints and the language chip are gone from the screen. THEATRE, GAME, TALK,
  DEMO, the voice lab, the full settings and 中文 are under MORE.

## 3. What you choose
- **JELLY:** all eleven bodies. The ten species from the orchestra, and the one built from the voice's own throat
  and mouth. The species squeeze on every syllable and every stroke; the voice body's rim opens and closes with
  the words.
- **STEER:** the nine ways to swim, each with a line saying what the hand does, plus AUTO CAMERA.
- **WORLD:** the picture grid of places.
- **LOOK:** every paint and print, or AS BUILT.
- **SONG:** previous, pause, next, the songbook, and whether the cast sings.
- **What it says:** type a line (or speak it) in any of the five languages. Your jelly says it and the words light.

## 4. What you make
- **● REC** records the picture with the words on it, the song and the voice, as one file in the shape of your
  screen (portrait on a phone). Press again to stop; it stops itself at 30 seconds. Where the phone allows, the
  file goes straight to the share sheet; otherwise it is saved.
- **SEND ↗** shares a link. Whoever opens it is in your world, with your jelly, your look and your way of
  steering, and the jelly says your last line to them.

## 5. What was checked (phone-sized screen)
- It opens as a puppet: steering on, five control groups on screen, the old dock's buttons hidden.
- JELLY showed 11 bodies; choosing the Afterlight Medusa changed the avatar.
- LOOK → watercolour repainted the world. STEER → GLIDE changed the scheme.
- "hello, I live in a jar" was spoken and lit on the lyric line.
- REC produced a file: 720 × 1280, 12.7 s, picture and sound. Frames extracted from it show the jelly in its
  world (not black).
- SEND's link, opened in a fresh page, gave the same jelly, place and look, and the jelly said the line.
- ✕ hid the controls and ☰ appeared. No page errors.

**Faults found and fixed while testing:** the first recording had sound and a black picture, then a second
attempt had no picture at all. Both were my capture running at the wrong moment. The third recording is the one
measured above.

## 6. What was not checked
- A real phone: the share sheet, real fingers, and whether the file type it records can be sent in your apps.
  (This test browser recorded VP9 video with Opus sound; iPhones record a different type.)
- Sound, and whether the voices are good enough to send to anyone. See the voice lab.
- The microphone button.
- Your own voice is not in the recording, only the jelly's.

## 7. Distance from the Real Jelly
The Real Jelly is one animal with a nervous system, muscle and water. These eleven are bodies that are moved.
The voice body is the closest: its shape comes from a physical model and it has springs. Giving the puppet the
Real Jelly's nerves (so steering is a stimulus and the stroke is its own) is the step that would make it
believable, and it is not done.

## Controls that stopped controlling

**What was measured first.** With a mouse, in a headless browser: the stick, RISE and SINK in all 40 places, with
the orchestra on and alone; and seven steering schemes (glide, tap, drag, twin, paddle, draw, wheel) in four places.
All of them moved the jelly. So the code that steers was not the fault.

**What was actually wrong.**
1. The orchestra's picture did not claim finger gestures (`touch-action` was missing; every other page had it).
   On a phone the browser takes a drag back after a few pixels for its own scrolling. The stick and the wheel had
   their own claim, so they worked; glide, drag, twin, paddle, draw and drag-to-look could die mid-gesture. A mouse
   never shows this, which is why earlier tests passed.
2. In every scheme but the stick, the stick circle stayed on screen, dimmed, and swallowed any touch that began on
   it while doing nothing.
3. The camera sat so close that the jelly filled the screen and hid the place being steered through.
4. Lids that did nothing in some states: LOOK on a painted place; SONG while ALONE (the music is muted); the ALONE
   lid lost its light whenever another lid was opened.
5. The water had limits (a ceiling, a floor) that stopped you silently, and no sideways limit at all.

**What changed.**
- The picture claims its gestures. The stick circle is on screen only when the stick steers.
- The camera stands back (9.5 instead of 6.5).
- LOOK always changes what is seen: on a painted place the new paint becomes the place.
- SONG while ALONE offers MUSIC, which lets the music back in.
- ALONE stays lit while it is on.
- The ceiling and floor say so in a line and the bell flinches. Past 46 from the centre a current carries you back.

**Checked (emulated touch, headless).** A touch glide begun where the stick circle used to sit moved the jelly 5.0
with no gesture taken back; two thumbs in TWIN moved it 6.4 and raised it 5.2. The ceiling line appeared. Placed
at 52 from the centre, the jelly was back at 46 after three seconds. ALONE stayed lit with LOOK open. MUSIC
unmuted the song. No page errors.

**Not checked.** Emulated touch is not a phone: whether the browser really stops taking gestures back has to be
confirmed on yours. I cannot watch motion or hear sound. TILT cannot be tested here. Five cities (b3, b6, 03, 06,
13) open as the city after them when asked for by name.
