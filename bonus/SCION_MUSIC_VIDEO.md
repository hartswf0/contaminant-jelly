# SCION SYSTEM INSTRUCTION: THE MUSIC VIDEO (cut from the song, with a title, an ending, and a file you can keep)

**The direction:** "Where are all of these on main? Why not better music video."

## 1 · Where everything is
| what | on a main branch? | where |
|---|---|---|
| The orchestra: 29 experiments, the 14 cities, the archivists, the 8 architectures, the video mode below | yes: `contaminant-jelly` main | `bonus/jellyorchestra.html` (cities in the "cities…" menu; architecture and performance on the card) |
| The Jelly Studio and the 38 songs | yes: `contaminant-jelly` main | `bonus/jellystudio.html` |
| The Real Jelly solo | yes: `contaminant-jelly` main | `bonus/realjelly.html?song=<id>` |
| **Celluloid Cities in Bolas** | **no** | the branch `claude/nifty-einstein-japglf` of `hartswf0/bolas`. It reaches Bolas's live site only when that branch is merged, which needs your word |

## 2 · Why it was not a good music video
Stated plainly, from the code:
| fault | what it was |
|---|---|
| **It was not edited.** | the camera changed every four bars whatever the song did |
| **Shots did not move.** | each shot was a fixed place to stand |
| **No beginning or end.** | it started mid-scene and stopped |
| **The interface sat on the picture.** | a card, a bar, a placard and a list, over every frame |
| **There was no video.** | nothing could be taken away from the page |
| **Nobody has watched it.** | this is still true. I can only look at single frames |

## 3 · What changed
| | |
|---|---|
| **The edit comes from the song.** | each bar is weighed by how much is playing in it. Full bars: a cut every two bars, and the camera goes close or to the side. Middling bars: every three. Thin bars: the shot holds for four and stands back. A change in fullness is always a cut. The last two bars are wide |
| **Shots move.** | every shot pushes slowly in for as long as it is held |
| **The picture answers the kick.** | a small jolt, and the glow swells |
| **VIDEO** (in the bar) | hides every control, letterboxes the picture to 2.39:1, restarts the song, opens on a title card over black that clears into the scene, and closes on an end card. Escape or a double tap leaves it |
| **RECORD** (in the bar) | does the same and writes it to a file: the picture with its title and ending, the song and the sound layer. When the song ends, or you press RECORD again, the browser downloads the video |

**For one song, the edit it made** (17 bars; 2 = full, 1 = middling, 0 = thin): `22222222111111110`. Cuts at bars 1, 3, 5, 7, 9, 12, 15 and 17: close, side, close, wide, side, wide, wide, wide.

## 4 · Checked
| check | result |
|---|---|
| the edit list | built for the test song, as above |
| VIDEO | controls hidden, letterbox on, title card showing the city and the song |
| RECORD | a file was downloaded: 1280 × 536, VP9 picture, Opus sound |
| the file's sound | the song is in it at full level (mean -16.7 dB) |
| a frame from the file | the title "OUT OF LIFE" over the scene fading up |

**Not checked:**
- **How it plays.** The test renderer manages about three frames a second, so the test file is a slideshow. On a real graphics card it should record at the frame rate you see.
- **Safari and phones.** Recording needs a browser that can capture a canvas and an audio element; Chrome and Firefox can. Where it cannot, the button says so.
- **Whether the cuts land well.** They are placed by a rule about fullness, not by ear.

## 5 · What would make it better still, not built
| idea | why not yet |
|---|---|
| **Cut on the hit, not the bar:** jump on a snare or the first kick after a silence | needs watching to tune |
| **A shot list per world:** the library wants slow tracking shots; the cypher wants a circling handheld | each world has two or three shots now |
| **Focus:** a shallow depth of field that racks to whoever comes in | a second pass over the picture |
| **Words on screen:** the scene's line from the poem as a caption in a city | I have kept the poems' words out so far; your call |
| **Render offline at full quality:** step the scene frame by frame and encode, so the file is perfect at any speed | the right way to make a file; a bigger job than the live recorder |
