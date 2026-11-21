# THE DOGS OF TROUTTOWN · SOUND

Owner: the sound designer (law 7), "a dog with its ear to the ground, who lays sounds it cannot hear".
Files: `films/swarm/dogs/sound.py` (the library, the music, the cue sheet), `films/swarm/dogs/sound/*.wav`
(87 files, 118 MB: every sound alone, the music of each sequence, the whole score and its six slices),
`films/swarm/dogs/sound/levels.json` (every number below, machine-readable).

**Nobody has heard any of this.** I cannot hear. Every statement here is one of: MEASURED (a number
taken from the samples), STRUCTURAL (true by how the code is built), or UNKNOWN. There is no JUDGED
line about sound in this file, because judging sound needs ears. What I looked at with my eyes is one
picture: the level envelope and two spectrograms of the finished 180 s score.

Everything is synthesized with `kit.Mix` and numpy. Nothing recorded, nothing foraged, no samples.

## Use it

```python
import sys; sys.path.insert(0, "films/swarm/dogs")
import sound

film.sound(sound.score)            # the whole 180 s track: rooms + music + every cue on the board

# or lay it yourself, by time (film seconds):
def my_sound(mix):
    sound.beds(mix)                # the two rooms and the swaps between them
    sound.music(mix)               # the radio, the town's chimes, the pack's round
    sound.sfx(mix, (1, 2))         # the cue sheet for sequences 1 and 2 only
    sound.paws(mix, 8.6, n=2)      # plus anything of your own
```

Re-render and re-measure everything: `python3 films/swarm/dogs/sound.py` (about 25 s).

**Re-timing.** The cue sheet uses the board's times (board part F). The board's rule stands: the
builder's frame wins and the sound moves. Each cue is one line in `sfx_s1` … `sfx_s6` with its time as
the second argument; change the number, nothing else. Room changes are the `ROOMS` list. Each call seeds
its own noise from its name and time, so moving one cue never changes how another sounds (STRUCTURAL).

## The convention

`name(mix, at, ..., gain, pan, under)` and it returns the time the sound ends.

- `at` is where the CONTACT lands. Measured onsets are in the table: every knock, step, splash and
  ring starts within 2.2 ms of `at`. The soft sounds (breaths, swishes, drags) swell in over 20 to
  100 ms by design. One sound has a lead-in: `breach` starts its rush 0.25 s BEFORE `at` and breaks
  the surface on `at`.
- `gain` is the linear peak at centre pan (signals are normalised first). Panned hard, one channel
  rises by up to 3 dB (the kit's constant-power pan).
- `pan` −1 left (door, porch) to +1 right (water). Constants: `P_DOOR −0.55`, `P_STEP −0.35`,
  `P_SILL −0.1`, `P_GATE 0.25`, `P_WATER 0.55`.
- `under=True` puts the sound under water (low-pass 700 Hz); `under=1500` uses that cut-off.

## The library, with example calls

### The dog
| Function | What it is | Example |
|---|---|---|
| `paws(mix, at, n=4, every=0.17, wet=False, pan_to=None)` | paws on the porch boards: a small wooden knock with a click of claws; `wet=True` adds a slap | `sound.paws(mix, 21.0, 3, 0.3, pan=0.1, pan_to=0.4, wet=True)` |
| `collar(mix, at, n=3)` | the red collar's tag: tiny tinks | `sound.collar(mix, 3.6, 2)` |
| `sniff(mix, at, n=2)` | nose puffs (the look at the notice board) | `sound.sniff(mix, 42.5, 2, under=1500)` |
| `pant(mix, at, seconds, rate=3.2)` | a tired dog, in and out, slowing | `sound.pant(mix, 79.5, 4.3)` |
| `sigh(mix, at, seconds=1.1)` | a dog sighing: one long breath out through the nose, falling, a trace of voice | `sound.sigh(mix, 151.6, 1.0, gain=0.05)` |
| `tail(mix, at, n=4)` | a tail on the boards, soft double thumps | `sound.tail(mix, 143.5, 4)` |
| `howl(mix, at, seconds=2.2, tail=0.7)` | ONE howl: about 300 up to 520 Hz, settling on 440, the only long room above water | `sound.howl(mix, 86.0, 2.0, tail=0.45)` |
| `bark(mix, at)` | one short bark (the stop); in the dictionary, not on the cue sheet | `sound.bark(mix, 100.0)` |

### The person, the step, the radio
| Function | What it is | Example |
|---|---|---|
| `voice_call(mix, at)` | a low human voice, NO words, calling: four syllables on the motif, the end lifting | `sound.voice_call(mix, 6.2)` |
| `voice_quiet(mix, at)` | the quiet line: six syllables, lower, slower, sinking | `sound.voice_quiet(mix, 81.2)` |
| `voice_no(mix, at)` | no: four level syllables, the last one dropping | `sound.voice_no(mix, 148.2)` |
| `voice(mix, at, kind, pitch=1.0)` | the three above (`'call'`, `'quiet'`, `'no'`), with a pitch factor | `sound.voice(mix, 65.0, "call", pitch=0.95)` |
| `taps(mix, at)` | four taps on the rail in the motif rhythm | `sound.taps(mix, 6.2)` |
| `pebble(mix, at)` | a white pebble set on the rail | `sound.pebble(mix, 7.75)` |
| `creak(mix, at, seconds=0.45)` | a board taking weight | `sound.creak(mix, 11.0)` |
| `radio_down(mix, at)` | the radio set on the step | `sound.radio_down(mix, 12.6)` |
| `radio_dial(mix, at)` | the dial: a thin whistle through static | `sound.radio_dial(mix, 13.0)` |
| `radio_hiss(mix, at, seconds)` | the radio's quiet hiss on the step | `sound.radio_hiss(mix, 12.9, 6.45)` |
| `radio_phrase(mix, at, variant=0, slow=1.0, ring=1.0)` | four plucked notes, thin, from one place | `sound.radio_phrase(mix, 13.7, 0)` |

The motif is `sound.MOTIF = (0.0, 0.28, 0.56, 1.08)` seconds: short short long short ("Will you fetch
it?"). The voice, the taps, the radio, the lamp answering in S2 and the pack's round all use it.

### The water
| Function | What it is | Example |
|---|---|---|
| `wade(mix, at, seconds=1.0, strides=3)` | wading in: water round the legs | `sound.wade(mix, 21.2, 0.8, 2)` |
| `plunge(mix, at, size=1.0)` | THE PLUNGE: thump, white water, fizz. size 0.6 small dog, 1.6 a cow's leg | `sound.plunge(mix, 22.0)` |
| `pack_plunge(mix, at, n=10, spread=0.2)` | many dogs entering the water inside `spread` seconds, fanned across the pan | `sound.pack_plunge(mix, 97.0, 10, 0.2)` |
| `splash(mix, at)` | one small splash | `sound.splash(mix, 124.3, pan=0.2)` |
| `swap_down(mix, at)` / `swap_up(mix, at)` | a whole crossing in one call (plunge + bubbles / bubbles + breach) | `sound.swap_down(mix, 22.0)`; `sound.swap_up(mix, 59.2)` |
| `hush(mix, at, seconds, gain=1.0)` | UNDER-WATER HUSH, the BELOW room: slow low pressure and a drone on 55 and 82.5 Hz | `sound.hush(mix, 22.6, 30.9)` |
| `above(mix, at, seconds, gain=1.0)` | the ABOVE room: low wind, lamp hum left, creek right | `sound.above(mix, 0.0, 22.6)` |
| `crickets(mix, at, seconds, voices=3, stop=None)` | dusk crickets; `stop` = film times at which each one stops | `sound.crickets(mix, 59.6, 26.4, 3, stop=[84.4, 85.0, 85.6])` |
| `bubbles(mix, at, n=5, seconds=1.0, low=False)` | rising blips; `low=True` fat ones | `sound.bubbles(mix, 55.0, 5, 0.8, low=True)` |
| `bubble_picture(mix, at, seconds=2.2)` | a fish child's picture rising in a bubble: one round tone climbing a fifth | `sound.bubble_picture(mix, 45.5, 2.4)` |
| `breach(mix, at, size=1.0)` | SURFACING: rush (from `at`−0.25), break on `at`, drops falling | `sound.breach(mix, 70.4)` |
| `shake(mix, at, seconds=0.9)` | THE SHAKE: wet flutter slowing, spray on boards, the tag rattling | `sound.shake(mix, 60.0)` |
| `drip(mix, at, n=1, every=0.5, on="wood")` | drips on wood or on water | `sound.drip(mix, 80.2, 7, 0.52)` |
| `breath_out(mix, at, seconds=1.2)` | BREATH RUNNING OUT under water: fat bubbles, slowly then all at once | `sound.breath_out(mix, 131.0, 0.9)` |
| `gasp(mix, at)` | breaking the surface out of breath: sharp in, short out | `sound.gasp(mix, 132.5)` |
| `shiver(mix, at, seconds=2.0)` | wet dogs shivering, dying away | `sound.shiver(mix, 133.0, 3.0)` |

### Trouttown
| Function | What it is | Example |
|---|---|---|
| `land(mix, at)` | the dog landing on the creek bed | `sound.land(mix, 31.0)` |
| `dig(mix, at, seconds=1.2, rate=8, find=None)` | DIGGING in gravel; `find` = `None`, `'thud'` (the boot), `'ring'` (a part) | `sound.dig(mix, 36.0, 1.2, find="ring")` |
| `set_down(mix, at)` | a thing set down on the bed | `sound.set_down(mix, 39.0)` |
| `paw_press(mix, at)` | a paw pressed on a thing (it is written) | `sound.paw_press(mix, 62.3, pan=sound.P_SILL)` |
| `page_taken(mix, at)` | A PAGE TAKEN: the pin's ring, the swish, the pin landing at +0.9 | `sound.page_taken(mix, 50.5)` |
| `lamp_chime(mix, at, step=0, seconds=2.5)` | a street lamp coming on; `step` 0..6 climbs | `sound.lamp_chime(mix, 24.0, 0, pan=-0.7)` |
| `school_bell(mix, at)` | the school bell through water | `sound.school_bell(mix, 28.5)` |
| `fish_murmur(mix, at, seconds=2.0)` | the fish class, a small high burble, no words | `sound.fish_murmur(mix, 29.2, 1.8)` |

### Reels, the sill, the old dog
| Function | What it is | Example |
|---|---|---|
| `reel_down(mix, at)` | A REEL SET ON WOOD: the knock, the tin's ring, a drop | `sound.reel_down(mix, 143.3)` |
| `page_slap(mix, at)` | a wet page laid across the sill | `sound.page_slap(mix, 61.6)` |
| `ratchet(mix, at, seconds=0.8, rate=14)` | film wound on or pulled off a reel | `sound.ratchet(mix, 146.6, 0.6, 16)` |
| `old_dog_down(mix, at, steps=4)` | slow heavy steps, the body down, a long breath | `sound.old_dog_down(mix, 165.7, 3)` |
| `card_drag(mix, at, seconds=0.9)` | card on wood: the old dog shifting, a tail pulled aside | `sound.card_drag(mix, 172.1, 0.5)` |
| `long_look(mix, at, seconds=1.5)` | THE OLD DOG'S LONG LOOK as a held tone: 196 Hz and its fifth, two strings 0.7 Hz apart, no tune | `sound.long_look(mix, 164.0, 1.5)` |

### The pack, each dog its own material
| Function | Dog | Example |
|---|---|---|
| `wheels(mix, at, seconds=1.0, pitch=1.0)` | wooden retrievers (pitch 1.0, 1.26, 1.5) | `sound.wheels(mix, 90.4, 0.8, 1.26)` |
| `peg_tick(mix, at, n=1, every=0.25)` | the retriever's peg tail, even ticks | `sound.peg_tick(mix, 162.0, 22, 0.25)` |
| `wire_twang(mix, at)` | the wire digger | `sound.wire_twang(mix, 91.7, pan=0.4)` |
| `paper_slide(mix, at)` | the black cut-out herding dog | `sound.paper_slide(mix, 89.2, pan=-0.8)` |
| `flutter(mix, at)` | the crepe sheepdog | `sound.flutter(mix, 89.7, pan=0.8)` |
| `page_peel(mix, at)` | the printed bloodhound | `sound.page_peel(mix, 92.1)` |
| `pop(mix, at)` | the terrier | `sound.pop(mix, 92.6)` |
| `patter(mix, at, seconds=1.5, rate=11, pan, pan_to)` | the herding dog running wide round the herd | `sound.patter(mix, 93.0, 1.4, pan=0.7, pan_to=-0.2)` |
| `work(mix, at, seconds, voices=7, top=700, level=1.0)` | the whole pack working under water; `voices` thins it, `top` lowers the low-pass | `sound.work(mix, 101.0, 15.0)` |

### The cows (always slow, always low; their tempo never changes)
| Function | What it is | Example |
|---|---|---|
| `hooves(mix, at, n=4, every=0.55, surface="earth", pan_to, gain_to)` | walking hooves; `'earth'` the worn path, `'grass'`, `'wood'` the board, `'ice'` | `sound.hooves(mix, 0.3, 6, 0.55, "earth", gain=0.05, gain_to=0.12, pan=0.7, pan_to=0.25)` |
| `calf(mix, at, n=6, every=0.14)` | the calf's small quick hooves | `sound.calf(mix, 76.2, 6, 0.13, pan=0.3, pan_to=0.45)` |
| `cowbell(mix, at, n=1, every=0.55, hard=False)` | the lead cow's bell: a dull knock near 330 Hz, never a chime; swings late | `sound.cowbell(mix, 1.6, hard=True)`; from below: `sound.cowbell(mix, 23.4, under=True)` |
| `cow_breath(mix, at, seconds=1.6)` | one long warm breath out | `sound.cow_breath(mix, 4.6, 1.5, pan=0.1)` |
| `drinking(mix, at, seconds)` | slow gulps | `sound.drinking(mix, 66.5, 5.5)` |
| `moo(mix, at, seconds=0.7)` | her one call, 150 sagging to 120 Hz, heard from under | `sound.moo(mix, 54.9)` |
| `stamp(mix, at)` | THE STAMP on the ice, with the bell jumping | `sound.stamp(mix, 122.0)` |
| `cow_down(mix, at)` | folding down: knees (0, +0.35), hind end (+1.1), long breath (+1.3), bell settles (+2.0) | `sound.cow_down(mix, 173.0)` |
| `cow_up(mix, at)` | getting up: two heaves and a breath | `sound.cow_up(mix, 153.5)` |
| `chew(mix, at, n=2)` | she only chews | `sound.chew(mix, 168.9, 2)` |
| `nose_bump(mix, at)` | a nose against the calf; a wheel against a hoof | `sound.nose_bump(mix, 77.55)` |

### Ice
| Function | What it is | Example |
|---|---|---|
| `ice_form(mix, at, seconds=1.2)` | ICE FORMING: a thin ring climbing, ticks crowding | `sound.ice_form(mix, 116.8, 1.2)` |
| `ice_crack(mix, at, seconds=1.4)` | ICE CRACKING: one crack, a tear running both ways across the pan, plates knocking | `sound.ice_crack(mix, 122.62)` |
| `skid(mix, at)` | a hoof skidding on ice | `sound.skid(mix, 120.2)` |

### Tools
| Function | What it does | Example |
|---|---|---|
| `silence(mix, a, b)` | declares silence: empties the mix between a and b. Call after what might ring into it and before what should sound inside it | `sound.silence(mix, 118.0, 122.0)` |
| `duck(mix, a, b, level=0.5)` | turns down what is already in the mix | `sound.duck(mix, 19.4, 20.6, 0.6)` |
| `beds(mix)`, `music(mix, sequences)`, `sfx(mix, sequences)`, `score(mix)` | the layers | `sound.music(mix, (4, 5))` |
| `measure(stereo)`, `a_weighted_db(stereo)`, `write_wav(path, stereo)` | what produced the numbers below | |

## The cows and the dogs in the sound (the weave)

The person asked for cows and dogs to deal with each other in every sequence. In sound that is two
tempos that never merge: every cow sound uses the same 0.55 s walking step and is low; the dog's rounds
get shorter. Where they meet, both are in the same second (all STRUCTURAL: these calls are in the cue sheet):

| Seq | The moment | Cow sound | Dog sound |
|---|---|---|---|
| S1 | noses, 3.4–5.6 | hooves stop; the bell swings twice by itself; one long breath onto the dog (4.6) | the collar tag as its head comes up (3.6) |
| S1 | the first crossing | her bell clatters (22.1), then one knock heard from under water (23.4) | the plunge (22.0) |
| S2 | she cannot follow | a foreleg in (54.2), the bell, hooves scrabbling, her one call from below (54.9), fat bubbles | the under-water room, the page already taken |
| S3 | the gate and the calf | one unbroken slow drinking and walking under three rounds | each round shorter; the calf's quick hooves after the dog (76.2), two nose bumps (77.55, 78.05) |
| S4 | the way opened | three sets of hooves turning off onto grass, duller | the herder's patter, the fastest rhythm above water; ten plunges in 0.2 s |
| S5 | the ice | four hooves on ice, a skid, THE STAMP twice, the crack | every dog sound absent for 4 s, then the work back as it was |
| S5 | kept warm | slow hooves, four long overlapping breaths | eleven breaths let go, eleven gasps, shivering that dies under the breaths |
| S6 | the last gate | she gets up, walks, chews (168.9) during the builder's look; folds down (173.0), bell settles (175.0) | the old dog's steps, body, breath; the peg tail ticking |

## The music: six sequences, and where there is none

No score is laid over the film. Three kinds of music, each from somewhere in the picture: the RADIO
on the step (one thin plucked voice), the TOWN's chimes (lamps, school bell), and the PACK'S ROUND (the
same four-note motif in five low voices at once, each at its own pitch and moment: one dog is one voice,
the pack is the tune all at once). The board said "no music" under the pack at work; the round is my
addition for this task and it is separable: `sound.score(mix, do_music=False)` or drop `music_s4`/`music_s5`.

| Seq | Length (MEASURED) | `music_sN` | What plays | Digitally silent share of the music stem |
|---|---|---|---|---|
| S1 THE DOOR | 28.00 s | `music_s1(mix)` | nothing for 12.9 s; radio on at 13.0; phrases at 13.7, 16.7; off the air 19.35–20.65 while the dog decides; one phrase at 20.7; the town's seven lamps 24.0–27.0 | 54 % |
| S2 TROUTTOWN | 30.00 s | `music_s2(mix)` | school bell at 28.5 and 29.4; then nothing until one lamp answers the motif at 56.6 | 80 % |
| S3 AGAIN, SOONER | 26.00 s | `music_s3(mix)` | the radio, a phrase every 3.0 s from 60.2 to 78.2; it does not speed up; off at 80.45 | 15 % |
| S4 THE PACK | 32.00 s | `music_s4(mix)` | nothing for 17 s (the howl stands alone); the round from 101.0, a voice entering every 2 s | 65 % |
| S5 ICE, AND ELEVEN | 28.00 s | `music_s5(mix)` | the round to 118.0; nothing 118.0–123.0; all five voices back; they leave at 127.5, 129.0, 130.5, 132.0; one voice alone to 139.9 | 59 % |
| S6 NO, AND AGAIN | 36.00 s | `music_s6(mix)` | radio phrases at 144.8 and 147.3, off at 149.0; nothing for 26 s; radio back at 175.2, slower, the last note left to ring | 73 % |

**Silence where characters think** (`sound.THINKING`; MEASURED on the music stem, and enforced by an
assert in the render: the peak in each window is digital zero):

| Film seconds | Who is thinking |
|---|---|
| 0.0–12.9 | the herd files past; noses; the asking; the dog backs off |
| 19.4–20.6 | the dog looks at the water and decides |
| 32.6–56.5 | digging, then the dog reads the page and decides |
| 80.6–101.0 | the tired dog; the quiet line; the howl and the hold after it |
| 118.0–123.0 | under the ice; she stamps |
| 139.9–144.4 | the lead dog finishes alone; pleased |
| 149.1–175.0 | no; ears down; the old dog's look, its back, the reel changed |

"No music" is not "no sound": the rooms and the contact sounds go on in those windows, except under the ice.

## What I measured

Method: each sound rendered alone at its default gain into a stereo 44.1 kHz 16-bit wav with no gain
change (`sound/<name>.wav`, the call placed at 0.25 s). Peak = largest sample. RMS = over the part
within 60 dB of the peak. dB(A) = the same RMS after the standard A curve. Onset = first sample over
10 % of the peak, minus the call time. Centroid and the two percentages are from the power spectrum.

| sound | peak dBFS | rms dBFS | rms dB(A) | sounds for s | onset ms | centroid Hz | % under 700 Hz | % over 200 Hz |
|---|---|---|---|---|---|---|---|---|
| `paws` | -15.9 | -32.9 | -40.9 | 0.61 | 0.5 | 297 | 90 | 18 |
| `collar` | -23.1 | -40.8 | -39.7 | 0.24 | 0.1 | 3454 | 0 | 100 |
| `sniff` | -24.4 | -40.2 | -39.2 | 0.25 | 20.3 | 2336 | 0 | 100 |
| `pant` | -26.0 | -42.0 | -41.7 | 1.33 | 25.4 | 1294 | 6 | 100 |
| `sigh` | -21.9 | -39.3 | -40.3 | 1.09 | 22.0 | 943 | 39 | 96 |
| `tail` | -23.1 | -38.8 | -49.0 | 0.68 | 0.4 | 183 | 99 | 34 |
| `howl` | -2.4 | -13.1 | -15.2 | 2.75 | 36.3 | 724 | 66 | 100 |
| `bark` | -6.9 | -20.8 | -22.7 | 0.16 | 1.4 | 818 | 64 | 100 |
| `voice_call` | -14.6 | -28.6 | -34.4 | 1.34 | 12.3 | 408 | 95 | 86 |
| `voice_quiet` | -17.5 | -34.1 | -39.3 | 1.68 | 16.0 | 429 | 91 | 91 |
| `voice_no` | -16.0 | -32.7 | -37.0 | 1.2 | 14.9 | 499 | 78 | 90 |
| `taps` | -15.5 | -36.1 | -44.8 | 1.17 | 0.2 | 266 | 99 | 96 |
| `pebble` | -18.9 | -40.0 | -39.3 | 0.12 | 0.0 | 3374 | 0 | 100 |
| `creak` | -22.6 | -35.7 | -45.9 | 0.43 | 48.0 | 205 | 98 | 18 |
| `radio_down` | -16.6 | -33.3 | -38.5 | 0.08 | 0.1 | 413 | 85 | 98 |
| `radio_dial` | -30.2 | -41.5 | -41.3 | 0.55 | 3.1 | 1611 | 0 | 100 |
| `radio_hiss` | -42.6 | -58.2 | -58.8 | 3.0 | 37.1 | 2672 | 26 | 74 |
| `radio_phrase` | -30.0 | -46.0 | -46.5 | 2.08 | 0.3 | 1198 | 23 | 100 |
| `wade` | -16.9 | -33.8 | -34.4 | 0.97 | 58.6 | 1066 | 30 | 100 |
| `plunge` | -5.8 | -25.6 | -34.5 | 1.14 | 1.0 | 390 | 89 | 13 |
| `pack_plunge` | -4.8 | -25.4 | -35.1 | 1.34 | 2.2 | 356 | 91 | 10 |
| `splash` | -12.5 | -30.1 | -39.3 | 0.68 | 0.6 | 384 | 92 | 10 |
| `bubbles` | -21.9 | -36.6 | -36.7 | 1.02 | 7.1 | 993 | 15 | 100 |
| `bubble_picture` | -24.4 | -29.9 | -36.7 | 2.2 | 52.4 | 308 | 100 | 100 |
| `breach` | -7.6 | -29.0 | -28.5 | 1.36 | -139.3 | 2894 | 5 | 100 |
| `shake` | -13.3 | -31.0 | -30.2 | 0.88 | 8.0 | 2786 | 3 | 100 |
| `drip` | -26.6 | -50.1 | -53.5 | 0.99 | 0.2 | 511 | 95 | 99 |
| `breath_out` | -18.4 | -34.6 | -39.4 | 1.29 | 37.1 | 399 | 100 | 99 |
| `gasp` | -19.9 | -38.0 | -37.4 | 0.62 | 43.9 | 1879 | 4 | 100 |
| `shiver` | -30.5 | -46.6 | -47.4 | 1.96 | 25.7 | 903 | 35 | 100 |
| `land` | -17.1 | -31.7 | -40.6 | 0.4 | 0.7 | 196 | 91 | 30 |
| `dig` | -17.1 | -34.5 | -38.2 | 1.7 | 0.6 | 529 | 64 | 40 |
| `set_down` | -21.9 | -34.5 | -38.7 | 0.05 | 0.2 | 438 | 96 | 99 |
| `paw_press` | -20.9 | -31.2 | -44.1 | 0.16 | 1.3 | 136 | 100 | 27 |
| `page_taken` | -21.9 | -40.0 | -40.1 | 1.01 | 0.0 | 1262 | 24 | 100 |
| `lamp_chime` | -29.1 | -44.4 | -48.7 | 2.4 | 0.6 | 437 | 90 | 100 |
| `school_bell` | -19.7 | -35.5 | -38.9 | 3.1 | 0.2 | 519 | 84 | 100 |
| `fish_murmur` | -30.5 | -43.2 | -45.6 | 2.0 | 25.2 | 593 | 63 | 100 |
| `reel_down` | -13.3 | -34.8 | -38.5 | 0.6 | 0.5 | 735 | 70 | 33 |
| `page_slap` | -19.4 | -35.3 | -35.1 | 0.12 | 0.4 | 1417 | 20 | 100 |
| `ratchet` | -24.4 | -44.1 | -44.4 | 0.73 | 0.2 | 1076 | 4 | 100 |
| `old_dog_down` | -17.8 | -39.0 | -45.6 | 3.79 | 0.4 | 327 | 84 | 27 |
| `card_drag` | -25.4 | -40.6 | -41.8 | 0.9 | 99.1 | 821 | 43 | 100 |
| `long_look` | -32.5 | -42.0 | -52.1 | 1.5 | 41.6 | 212 | 100 | 14 |
| `wheels` | -23.1 | -39.9 | -42.6 | 1.01 | 0.2 | 589 | 92 | 100 |
| `peg_tick` | -25.4 | -47.6 | -48.5 | 0.78 | 0.2 | 829 | 12 | 100 |
| `wire_twang` | -23.1 | -48.0 | -48.1 | 0.6 | 0.0 | 4218 | 1 | 99 |
| `paper_slide` | -24.4 | -40.8 | -39.8 | 0.39 | 83.6 | 3550 | 0 | 100 |
| `flutter` | -26.0 | -43.5 | -42.6 | 0.58 | 62.7 | 2043 | 2 | 100 |
| `page_peel` | -24.4 | -42.8 | -42.1 | 0.35 | 67.0 | 4191 | 0 | 100 |
| `pop` | -21.9 | -32.6 | -33.5 | 0.05 | 0.0 | 787 | 17 | 100 |
| `patter` | -19.9 | -36.3 | -47.2 | 1.56 | 0.5 | 181 | 98 | 12 |
| `work` | -25.9 | -42.0 | -45.3 | 5.76 | 234.4 | 498 | 98 | 99 |
| `hooves` | -17.2 | -36.7 | -48.1 | 1.91 | 0.5 | 153 | 98 | 22 |
| `hooves_ice` | -17.2 | -38.5 | -45.5 | 1.32 | 0.4 | 456 | 89 | 29 |
| `calf` | -21.9 | -39.8 | -44.5 | 0.78 | 0.9 | 423 | 82 | 75 |
| `cowbell` | -19.7 | -38.2 | -43.0 | 0.48 | 0.2 | 409 | 99 | 100 |
| `cowbell_under` | -19.7 | -38.1 | -43.4 | 0.5 | 0.1 | 380 | 100 | 100 |
| `cow_breath` | -21.9 | -39.0 | -43.6 | 1.59 | 46.6 | 411 | 92 | 90 |
| `drinking` | -23.2 | -40.3 | -47.4 | 1.04 | 36.5 | 302 | 89 | 33 |
| `moo` | -14.3 | -25.1 | -31.3 | 0.7 | 12.7 | 329 | 99 | 66 |
| `stamp` | -1.9 | -21.1 | -31.1 | 0.7 | 0.5 | 193 | 99 | 31 |
| `cow_down` | -15.5 | -35.0 | -46.0 | 3.67 | 0.6 | 136 | 98 | 20 |
| `cow_up` | -18.4 | -34.3 | -44.9 | 2.2 | 0.3 | 139 | 98 | 20 |
| `chew` | -29.1 | -44.6 | -49.0 | 0.97 | 32.6 | 416 | 95 | 93 |
| `nose_bump` | -26.0 | -37.0 | -48.7 | 0.12 | 1.3 | 157 | 100 | 30 |
| `ice_form` | -24.4 | -41.9 | -41.2 | 1.2 | 0.0 | 4584 | 0 | 100 |
| `ice_crack` | -5.1 | -29.2 | -35.4 | 2.13 | 0.2 | 718 | 80 | 20 |
| `skid` | -25.1 | -42.6 | -41.8 | 0.29 | 0.9 | 3977 | 0 | 100 |
| `crickets` | -30.9 | -49.0 | -48.8 | 3.56 | 199.9 | 4323 | 0 | 100 |
| `above` | -32.9 | -49.2 | -53.2 | 4.0 | 111.2 | 628 | 62 | 45 |
| `hush` | -28.5 | -39.2 | -53.9 | 4.0 | 36.1 | 94 | 100 | 9 |
| `pack_round` | -23.1 | -36.5 | -44.5 | 5.98 | 2756.2 | 267 | 100 | 75 |

(`cowbell_under` and `hooves_ice` are `cowbell(under=True)` and `hooves(surface="ice")`. `work` and
`pack_round` start late in their test file because their pattern is locked to the film clock.)

### The whole score (`sound/score.wav`, after the kit's own `master()`), MEASURED

- 7 938 000 samples per channel = 180.000 s. The six slices `score_s1..s6.wav` are 28, 30, 26, 32,
  28, 36 s, cut from the one file, so each begins on the sample the last ended on (STRUCTURAL).
- Raw peak −1.9 dBFS; the kit's master lowered everything by 1.0 dB and changed nothing else. Final
  peak −3.0 dBFS, whole-film RMS −30.3 dBFS. No clipping.
- The two loudest seconds are the stamp (122, −3.0 dBFS) and the howl (86–87, −3.5), as the board asked.
  Next: six dogs in at once (155, −5.9), the first plunge (22, −6.9), ten dogs in (97, −7.2).
- Under the ice: 118.05–119.45 and 121.05–121.95 are digital zero in both channels. Between them the
  hooves on ice peak at −24.3 dBFS.
- The second in which the dog decides (19.5–20.5): peak −36.1, RMS −51.7; the two seconds before it:
  peak −22.7, RMS −39.9. So that hold is about 12 dB quieter than what precedes it.
- Ears down (149.5–151.5): peak −31.0, RMS −48.4. The look (164.0–165.5): peak −25.3, RMS −41.3
  (the peg tail's ticks plus the held tone).
- After the howl the room is cut by 88.45; 88.47–88.88 measures peak −35.1 (beds only).
- The radio phrase peaks at −30.0 dBFS. It sits under `paws` by 14.1 dB, `taps` 14.5, `reel_down`
  16.7, `shake` 16.7, `hooves` 12.8, `breach` 22.4, `plunge` 24.2, howl 27.6, stamp 28.1. The board
  asked for 12 dB or more. It is NOT met against `cowbell` (10.3 dB) or the smallest contacts
  (`drip`, `peg_tick`, `collar`, `wheels` are within 7 dB of the radio).
- Per sequence, peak / RMS dBFS: S1 −6.9 / −35.5, S2 −9.6 / −34.4, S3 −8.6 / −33.3, S4 −3.5 / −24.7,
  S5 −3.0 / −31.6, S6 −5.9 / −35.2.
- Looked at (one picture, envelope plus spectrograms of the score): the under-water stretches show
  almost nothing above about 1.5 kHz and the above-water stretches show the crickets' three lines near
  4 kHz; the ice gap is blank; the howl is a single rising then level trace. That is all the picture shows.

## What is unknown, and the risks I can see in the numbers

- UNKNOWN: whether any of it sounds like what it is named. A waveform cannot tell me that `howl`
  reads as a dog, that `voice_no` reads as a person refusing, or that `cowbell` reads as a bell on a
  cow and not a tin can. The three voice lines are buzz through vowel formants with a pitch contour;
  whether they read as a human voice or as a kazoo is UNKNOWN and is the first thing a listener should check.
- UNKNOWN: whether the radio is audible at all. Its A-weighted level alone (−46.5) is about the same as
  the above-water room with the cow drinking (−45.5); with the radio added that window reads −43.8.
  It was set low to meet the board's 12 dB rule. If it cannot be heard, raise `radio_phrase` gain.
- RISK (MEASURED): the film is quiet between its two peaks. Most passages sit 25 to 45 dB under the
  howl. On a phone at low volume the holds may be inaudible, and the kit's master never raises level.
- RISK (MEASURED): the stamp matches the howl in peak but not in A-weighted level (−30.7 against
  −15.5 over their windows): it is a short low impact, and only 31 % of its energy is above 200 Hz.
  On small speakers it may land softer than the howl. The crack 0.6 s later is broadband.
- RISK (MEASURED): the cows are low. `hooves` has 22 % of its energy above 200 Hz, `cow_down` 20 %,
  and the under-water room 9 %. I added overtones to the lowest sounds for small speakers (before that
  hooves had 5 %), but on a laptop the herd may still be felt less than the dogs. The bell (100 %
  above 200 Hz) is the cow sound that will certainly come through.
- UNKNOWN: sync. Every time is the board's. No animation existed for me to check a contact against a
  frame. Any action that lands on another frame needs its one number changed.
- UNKNOWN: whether the pack's round helps or sentimentalises the pack sequence. No critic has reviewed it.
- Not done: no independent critic has listened; this file passes nothing (law 9). The `sound/` folder
  is 118 MB of uncompressed wav and should not be shipped with the film.
