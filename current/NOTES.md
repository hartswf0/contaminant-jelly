# The Current (fifth version): the dive to the Source

A golden jellyfish of light dives 605 m of drowned tunnel to the Source.
- **Films:** clouds of light. Some drift with the water, some grow on the walls as reefs, some flow inside eels, and one dangles from an anglerfish as bait.
- **Drinking:** drink a film and it blooms briefly by itself. Your tentacle becomes a time worm that carries it.
- **The end:** at the Source your worms let go, one film at a time, and the dive is told.
- **Together:** with others, everyone in a room meets the same films.

Rules:
- [SCION_NEVER_A_FRAME.md](SCION_NEVER_A_FRAME.md): video is only clouds, worms or a bloom.
- [SCION_GOLDEN_RIVERBED.md](SCION_GOLDEN_RIVERBED.md): the prompt engine, run on the game itself as [riverbed_v5.json](riverbed_v5.json).

Earlier: [v4](v4.html) ([notes](NOTES_v4.md)), [v3](v3.html), [v2](v2.html), [v1](v1.html).

## What changed from v4, and why
| ask | answer |
|---|---|
| "the videos aren't visible anywhere really" | Clouds are bigger, softer and brighter (softness 0.9). **Film reefs**, 6 large soft clouds rooted on the walls and pillars, brighten as you pass. Every drink makes a **taste bloom**: the new film blooms beside you for 2.5 s. |
| other animals and predators | **Anglerfish** (original design): a dark bulk of particles with a faint sheen, blue photophores, irregular fangs and a stalk whose lure *is a film*. It lurks, notices you within 15 m, hunts, then lunges. A bite or touching the lure costs two carried films. **Film eels** ride the currents; their bodies are one film flowing head to tail; drink from the tail and they dart away. **Fish schools** of flecks scatter from you and from the angler. |
| more paths and currents | **Three chambers** where the tunnel forks around a pillar. The right side is richer (75% pairs, 5% corrupted) and the angler waits there; the left side is poorer and 45% corrupted. **Two spiral currents**: ride one and it holds you, speeds you up (+5.5 m/s), streams your tentacles and carries the films in it. Marine snow shows them. |
| better physics | Thrust comes from the bell's contraction. Tentacles are dragged by water that flows down the tunnel, faster in currents, with eddies, and kept out of the pillars by their SDF. |
| pinch to zoom out, peek along the side | Pinch pulls back (2.8 to 24 m). Two fingers dragging swing the camera around the creature and tilt it. Desktop: scroll, right-drag or shift-drag, Z / X, − / =; double-click or R resets. The view eases back behind you after 2.5 s. The camera stays inside the tunnel and out of the pillar. |
| micro-minimap | A 26 px strip at the right edge: the next 90 m and the last 36 m of tunnel, its forks, film clouds (white), corruption (red), reefs, eels (green), anglers (amber, flashing when hunting), other divers (cyan), you (gold), the Source line, and a progress bar to the end. |
| clearer end state | The Source at 605 m. The tunnel opens into a hall, the camera orbits, and each carried film blooms in turn while *Go Home and Be Free* plays. Then the end card lists the films you carried, out of those you drank, with bites, corruption, eels, time and companions, plus Dive again, Save reel and Share the dive. |
| multiplayer | **Swim together** makes a room link. The room seeds the world, so everyone meets the same films in the same places. Others appear as cyan jellyfish. A film one diver drinks pours toward them and is gone for everyone. Transport: BroadcastChannel between tabs on one device, and PeerJS through its public broker across devices; the first diver hosts. |
| deep underwater sound and the songs | A synthesized bed: brown noise through a breathing low-pass, 38 and 55 Hz pressure tones, panned bubble chirps, distant calls through a 4.5 s reverb, a rush in currents and dashes, a stroke for every pulse, and a low drone when the angler hunts. **The 56 VOLHOLLA songs you chose** (`music.json`, with your notes) stream from the moto site through an underwater low-pass that darkens with depth and opens when you watch. They change by zone: drift, chamber, deep, hunt (*Ritual of the Ash and Silt (2)*), end (*Go Home and Be Free*). **M** switches station (the deep, the surface for the bright and lyric songs, off); tap the song line or press N to skip. |

## The video-to-game loop
1. **Source.** The GOLDEN RIVERBED prompt, transformed into SCION and run on the game: `riverbed_v5.json`.
2. **Design video.** `fal/design_v5_720.mp4` (sheet `fal/design_v5_sheet.jpg`), from the master prompt. It shows large soft film clouds (a horse, a face, a hand), the small golden jellyfish, an anglerfish silhouette with a lure, round passages, a cyan jellyfish, rows of small film clouds and red grain at the walls.
3. **Build, then fix by looking:**

| what the screenshots showed | fix |
|---|---|
| Wall plankton drew as teal squares | Round, sub-cell specks. |
| The angler's teeth lined up as a dotted rectangle | 30 uneven, curved fangs that point inward. |
| The angler was invisible on dark water | A faint sheen of larger dark-teal points, which brightens when it hunts. |
| The sheen swelled into bubbles at the lens | Size capped, and a fade from 1.5 to 5 m. |
| On a phone the films filled the screen and hid the creature | Portrait phones start 8.5 m back. |

## Measured
Headless Chromium, software GL, five films served locally. Music and PeerJS are blocked in this sandbox.

| measure | result |
|---|---|
| 60 s scripted run, 640×360 | 9 films drunk, 7 carried, no page errors |
| 60 s scripted run, 390×844 touch | 5 drunk, no page errors |
| two tabs in room `test1` (BroadcastChannel) | each sees the other as a ghost; of the 10 clouds live in both, all 10 agree in film, frame and corruption; a film drunk in one tab is gone in the other |
| real two-finger pinch (CDP touch events) | pinching in pulled the camera from 6.2 to 24 m; a two-finger drag swung it −0.73 rad |
| angler, framed run | lurk → hunt at 15 m → lunge → bite → rest → lurk |
| the Source, forced with 4 worms | hall, reel bloom of all 4, end card listing them |
| tentacle stretch | 1.4–5% in play (it spikes when a test teleports the creature) |
| frame time p95, CPU side, software GL | 7–17 ms |

**Not measured:**
- the songs actually playing: github.io is blocked here (the stream URLs, decoding and the Web Audio graph are untested);
- PeerJS across devices;
- real GPUs and phones;
- all 109 films from github.io;
- how it feels in the hand.

No person has played it yet.
