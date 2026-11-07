# SCION SYSTEM INSTRUCTION: THE SEA (hunters · arms · the cutting room · the linked waters)

**Role.** You are a jellyfish building a film in an open ocean. A video made this game; the game makes a video. Video contaminates games, and games contaminate videos.

**The direction:**
- "make the drift landing use the specimen jars too"
- "for each family, a massive sea level that connects them all together"
- "better steering, camera controls with speed and proximity, and tools for guidance"
- "at the end … see how long we grabbed it for is how long the clip is"
- "if we are attacked by the fish we lose arms" · "sometimes we max out how many arms"
- "a video of the jellyfish capturing each one … the video game is a spatial editor"
- "we never lose or know when we won or what we won"
- Other predators, from the field: marine reptiles, fish, seabirds, mammals, invertebrates, other jellies.

## 0 · The loop
1. **Swim and take.** A tap takes a frame and its film becomes an arm.
2. **Hold.** Holding on a film records it. The clip lasts exactly as long as you held it, timed in real seconds; a running "● 2.4 s" counter shows the length as it grows. A tap alone gives a 0.8 s clip.
3. **Keep your arms.** Hunters take arms, and with each arm its clip leaves the film.
4. **Arrive.** The end is a cutting room. The verdict comes first: WON, SURVIVED or LOST, with up to three stars. Below it, the film plays, and you can recut it and save it.

## 1 · Arms (the jelly's body is the film's bin)
- **Eight arms at most**, shown in the HUD as `arms n/8`.
- **When full**, taking a new film lets go of the arm that holds least. That arm's clip is struck from the cut ("let go").
- **Weight.** Each arm slows the jelly by 3%. Jellies digest fast, but a full one is heavy (six arms or more brings a warning).
- **A bite takes the newest arm** and its film. The membrane tears too; at 0% the jelly is eaten and the level is LOST.

## 2 · The hunters (`sea.js`): biology kept as rules
Each hunter is a dark point-cloud silhouette with its own gait (flippers, fins, wings, legs, tentacles). Its eyes light amber while it hunts.

Every hunter moves through the same states:
- roam;
- sense, which triggers a spoken warning and a tone;
- hunt, or for a seabird mark then dive;
- bite;
- sated, then roam again.

**The sting (the pulse)** turns away most hunters. It does nothing to the immune.

| species | zone | rule |
|---|---|---|
| leatherback turtle | open | Eats jellies almost exclusively, with spined papillae in its throat. **Immune** to stings. It turns slowly, so outrun it. |
| hawksbill turtle | open | Thick skin: **immune**. Swim wide of it. |
| ocean sunfish (*Mola mola*) | open | A slow grazer. Slip past it. |
| tuna | open | Fast passes along a led line. Dodge it or sting it. |
| chum salmon | open | Its expandable stomach takes **two arms**. Sting it. |
| grey triggerfish | open | Nips arms. Sting it. |
| sea lion | open | Fast and playful. Sting its nose. |
| seabirds (fulmar, albatross, parakeet auklet) | surface | Marks a spot, then dives. Stay deep. |
| crabs (arrow, hermit) | floor | Tears only at a **weakened** jelly (membrane under 70%). Keep off the floor. |
| nudibranch | floor | **Steals the stinging cells**: no pulse for 9 s. |
| dinnerplate jelly | open | A cannibal jelly that **carries the arm it took**. Sting it to win the film back: it reappears as a film to retake. |
| humpback whale | open | Sings, then gulps a patch of water: **two arms**, immune to stings. |

**Kept for later:** whale sharks, butterfish, rockfish, herring, whiting, the lesser-spotted dogfish, the sea nettle hunting comb jellies, and the jelly's diet (copepods, larvae, eggs) as food that heals the membrane.

**Assignment:**
- The drifts name their hunters. Examples: Ascent has a seabird and a sunfish; Twin Caves has crabs, a nudibranch and a hawksbill; The Long Descent has a humpback.
- Other levels take hunters from their water: a surface brings seabirds, a silt or mussel floor brings crabs, glowing reef brings a nudibranch, and one or two open-water species are chosen by the level's id.
- `?nopred` turns the hunters off.
- In trailer mode they appear but never bite.

## 3 · Guidance and camera
**The guide** (a canvas, hidden by H in cinema mode) has three parts:
- a strip along the foot: the length of the water, its regions (★ once you have taken a film there), the films still to take, the hunters (red), and you (amber);
- amber edge arrows to the three nearest films ahead;
- red arrows and rings, with a name, for hunters close by or hunting.

**The camera** responds to the play:
- it pulls back with speed (+22%);
- it opens out and leans toward a hunter that is hunting you (+40%);
- it closes in on a film you are beside (−12%).

**Controls:**
- Q/E orbit and R/F tilt; C recentres.
- Scroll or pinch zooms from 0.55× to 1.6×.
- Fixed: the camera's `lookAt` and the fish school's motion had been commented out by trailing `//` comments; both now run.

## 4 · The cutting room (`editor.js`): the spatial editor
- **Verdict:**
  - **WON**: the goal is met and you reached the end. The film is sealed in its jar (saved on this device as `cj-sealed`), and the landing marks the jar "sealed ★★ · 12.4 s".
  - **SURVIVED**: you reached the end, but the goal was not met.
  - **LOST**: you were eaten.
- **Stars:** one each for the goal met, no arm lost to hunters, and the membrane at 70% or more.
- **The monitor** plays the film you made:
  - a title card, then each clip from the frame you took, for as long as you held it, then the wordmark;
  - every clip carries a burned-in source and timecode;
  - the first full pass is recorded, and then "save the film" appears.
- **The timeline:**
  - clips sit side by side, their widths proportional to their lengths;
  - clips taken from you are hatched and marked ×, with the taker named below;
  - drag a clip to recut (recording restarts); tap one to jump to it.
- **The making of:** the water itself, recorded from the moment you take a film or are bitten, a few seconds each, at most 12 clips. It shows the jelly capturing each one.

## 5 · The seas: one long water per family
Each sea lays its family's levels end to end as **regions**. Every region keeps its films, layout, fog colour and hunters, and each region's hunters stay in their own region.

| sea | regions | length |
|---|---|---|
| **The Open Sea** (`sea-drifts`) | 10 drifts from our videos (Slices stays a level of its own) | 1,707 m |
| **The Lab Sea** (`sea-crashlab`) | Found Odyssey, Handmade, the rest of the Crash Lab | 519 m |
| **The Archive Sea** (`sea-archive`) | the 16 cineosis types, 8 shots each | 2,400 m |

- **Goal:** take a film in most of the regions (the strip marks each with ★).
- **Linked:** every level's end card says "SWIPE ↑ SWIM ON INTO <SEA>". You enter the sea at that level's own region (`&at=<region>`).
- The landing lists every region as an entry point.

## 6 · The landing
- The drift landing now uses the specimen jars for the episodes, the drifts and the periodic table: the standard label, a bespoke icon and the film filling the jar. The game's title card uses the same specimen jar.
- A new section, **00 · The seas**, holds the three seas and the field notes on the hunters.
