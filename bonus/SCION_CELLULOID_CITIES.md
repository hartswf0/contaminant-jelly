# SCION SYSTEM INSTRUCTION: CELLULOID CITIES (the whole Cineosis archive, stored as cities the jellies live and perform in)

**The direction:** "Make buildings and cities and streets out of celluloid. Think of each city and poem like a city. The idea would be to store all of our Cineosis archive in these cities: underwater data centers, moon and space data centers, cities, libraries, blockbusters, with our jellies living in each city as a world. See how creatively the swarm uses the archive in the films and presents it; we need that for cities, and the jellyfish of each to perform." With links to the Cineosis Lab and to Bolas, and: "this is the one that matters".

**Nothing here was watched in motion or heard.** Stills only.

## 1 · The idea, as built
**Every shot in the archive has an address.**

| in the archive | in the city |
|---|---|
| a poem of the WYGWYL suite (14) | **a city** |
| a scene of that poem (88 in all) | **a street**, in the poem's order |
| a source film (1,423) | **a tower** |
| a shot (15,149) | **a floor** |
| a frame | **a window** |

- **The towers are made of film.** Each floor is a strip: three frames between two rows of sprocket holes, amber, lit from inside. Where the archive holds a thumbnail, the windows show that shot; where it does not, the floor takes the shot's own measured colour.
- **The avenue is a strip of film** too, running the length of the city. Cross streets mark where one scene ends and the next begins.
- **A film goes to the city of the poem that asked for it.** The archive records which scenes each shot was foraged for. Films no poem asked for fill the emptiest cities.
- **A film with more than 36 shots is several towers,** side by side.

## 2 · The fourteen cities
| | city (the poem) | where | shots | films | streets |
|---|---|---|---|---|---|
| 01 | OUT OF LIFE | an underwater data center | 1,546 | 115 | 15 |
| 02 | FLASHING LIGHTS | a data center on the moon | 1,282 | 62 | 9 |
| 03 | HOW TO BREAK OFF AN ENGAGEMENT | a library of stacks | 1,000 | 55 | 7 |
| 04 | NEVERMORE | a video store the size of a city | 1,684 | 77 | 8 |
| 05 | BLOODLINES | a data center in orbit | 950 | 91 | 4 |
| 06 | RESURRECTING ATLANTIS | an underwater data center | 950 | 112 | 3 |
| 07 | DJ TURN ME UP | a data center on the moon | 950 | 124 | 3 |
| 08 | NEWLY SINGLE | a library of stacks | 950 | 127 | 5 |
| 09 | YET, HEARD | a video store the size of a city | 950 | 102 | 8 |
| 10 | MAGIC RIDE | a data center in orbit | 950 | 142 | 6 |
| 11 | NEW DAY | an underwater data center | 949 | 121 | 5 |
| 12 | REUNION | a data center on the moon | 949 | 104 | 2 |
| 13 | HOW TO WIN MY HEART | a library of stacks | 1,090 | 46 | 7 |
| 14 | HOT MINUTE | a video store the size of a city | 949 | 127 | 6 |

**Total: 15,149 shots, every one placed.**

**The five kinds of place**
| | what is different |
|---|---|
| **under the sea** | teal water, light from above, a film of water over the ground |
| **on the moon** | black sky, stars, grey ground, the Earth hanging over the avenue; things barely sink |
| **a library of stacks** | warm dark, a lamp over every street |
| **a video store** | cold teal, standing water |
| **in orbit** | no ground: the towers float at different heights over the curve of a planet |

**Each city has a text**, in the manner of a gazetteer, made from its own contents. For example: *"Out of life is an underwater data center. It keeps 1,546 shots from 115 films. Every film is a tower, every shot a floor, every frame a window. Its 15 streets are the scenes of the poem, in order: the first is 'Dim bedroom'. The tallest tower is All My Babies (1953): 36 floors. Nothing in it is older than 1906 or newer than 2019."* It shows on the placard while the city plays.

## 3 · How the jellies use the archive
- **They live in the avenue.** The orchestra performs any song in any city, to camera or in a cypher, as before.
- **The music walks the streets.** Every two bars the city moves one street along: that street's towers light up, pulsing on the beat, and the card names the scene (WATCH: *street 3 of 15: "Ex on the fire escape"*). A song is a walk through the poem's scenes in order.
- **The experiment, in every city:**

| | |
|---|---|
| **RULE** | every film is a tower, every shot a floor; the street the music has reached is lit |
| **SWERVE** | on each street one floor is lit before its turn, edged in gold and ringed: **the shot the poem's cut actually chose**, with its film, year and floor |
| **TEST** | from the lit street, which floor would you have chosen for this scene? |

So each street shows the poem's pick against the pool it was picked from: the cut's decision, made visible as architecture.

- **Touch any floor** and it gives its address: city, street and scene, tower (film and year), floor, shot, the sign it was read as (if it was), whether the cut chose it, and links to the lab and to the film's source page.
- **Sound:** each kind of place borrows a layer already made (water, the bay's beeps on the moon, the library, the store, the data center in orbit).

**Where to find them:** the orchestra page has a new **cities…** menu beside the songs. Cities are also experiments 16 to 29, so songs reach them in turn.

## 4 · Checked
| check | result |
|---|---|
| the data | 15,149 of 15,149 shots placed; 14 city files, 1.2 MB in all |
| five cities, one of each kind | built with no errors: 950 to 1,684 floors each |
| thumbnails | loading into the windows (about 200 of each city's 672 had arrived after 13 s in the slow test renderer) |
| the walk | the city had moved on to later streets while the song played |
| the ring | named the chosen shot, for example "Hi Diddle Diddle · floor 6" |
| touching a floor | returned its address: "city · OUT OF LIFE, street 2 · Ex on the fire escape, tower · [Amateur film: Travel/Cities] (1947), floor 10 of 10" |

**Not checked:**
- **The other nine cities** (same code, different data).
- **The live site.** The windows load their pictures from the Cineosis Lab's own site, which shares this site's address. That works in my local test, where I served the lab's files myself; I could not open the live pages from here.
- **Speed,** on anything but this test machine.
- **Whether the walk reads as a walk** in motion.

## 5 · Decisions I made, and their limits
- **I built this in `contaminant-jelly`, where the orchestra lives.** I read "this is the one that matters" as: Bolas is the bar for how the archive should be used. If you meant that this should live in Bolas, say so and it can be moved; nothing here depends on its location except the path to the thumbnails.
- **The WarGames collection is left out** (302 shots). It is a feature film, not archive footage, so I did not build with its frames. It is the only part of the lab's shot list not in a city.
- **Each city can show 672 thumbnails;** the largest holds 1,684 shots. Floors nearest the avenue get pictures first; the rest are in their own colour.
- **Only 5,574 shots have a thumbnail on the lab's site at all;** the others' pictures are on a host this site cannot draw from.
- **The gazetteer texts are assembled from counts,** not written. They are accurate and plain; they are not poems.
- **The poems' own words are not shown,** only their titles and the scene descriptions already in the lab's data.

## 6 · Considered, not built
| idea | from | why not yet |
|---|---|---|
| **Districts by sign:** the 45 signs of the periodic table as neighbourhoods, so a walk can follow a sign across cities | the lab's table | 410 shots carry a read sign; it would be a sparse map until more are read |
| **Windows that play:** the 555 shots with filmstrips flipping their frames | the lab's strips | each strip is a separate picture to load |
| **A city per cut:** the same poem as four cities (Suite, Scenes, Cineosis, Drift), to walk between | the lab's four cuts | the picks for the other three cuts are in separate files I did not read |
| **Cities you can lose things in:** floors that go dark when nothing has visited them | "a data center" | needs a memory across visits |
| **The jellies as archivists:** an animal carries a shot from a tower to the street where the poem uses it | Bolas, where the cast acts inside the archive | the strongest next step; it needs the pick's path to be animated |
