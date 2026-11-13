# SCION SYSTEM INSTRUCTION · THE ATLAS, FILMS, AND PLAYING TOGETHER

Where: `bonus/atlas.html` (written by `sim/jellystudio/atlas_build.py`); FILMS and room changes in
`bonus/jellyorchestra.html`.

## 1. Thesis
Things were built faster than ways to reach them. The main page has the eleven games and the periodic table; the
orchestra has the places; neither knew about the other, and nothing listed all of it. The atlas is one shelf with
everything on it, and each thing says how it can be entered: alone, with the orchestra, or with friends.

## 2. The atlas
| Section | Count | Opens |
|---|---|---|
| START HERE | 7 | the blank room, the range, the orchestra, the reel game, talk, theatre, the video store |
| MAKE AND CHOOSE | 4 | the loadout, the jelly maker, the jar experiments (and each jar), the voice lab |
| PLACES | 19 | every world, as a room for one jelly; also WITH ORCHESTRA and WITH FRIENDS |
| CITIES OF FILM | 21 | the archive as cities, the same three ways |
| PAINTS | 12 | each paint over deep water, or over the range |
| THE ELEVEN GAMES | 11 | the games on the main page's shelf |
| THE ARCHIVE LEVELS | 9 | the same water filled from other collections |
| BONUS PIECES | 23 | every bonus page, including six the main page does not list |
| THE PERIODIC TABLE | 61 | 45 signs and 16 types, each a level |

- 167 entries. A search box filters all of them by name and line.
- **OPEN** goes in alone and quiet. **WITH FRIENDS** makes a new room in that place and takes you in as its holder;
  the link to send is under FRIENDS.
- The lists of games, archive levels and bonus pieces are read from the main page when the atlas is built, so the
  two cannot drift apart. Run `python3 sim/jellystudio/atlas_build.py` after changing the main page.
- Reached from: the main page (Atlas, beside Index), the entrance (first under OTHER WATERS), MORE in the
  orchestra, the loadout's heading, the Bolas index.

## 3. Films
- The SONG lid is now **PLAY**: FILMS first, then MUSIC and the song controls.
- FILMS opens every film on the video store's shelves (434) with its cover, and a box to find one by name.
- Choosing a film takes you to the video store if you are not there, and puts it on.
- `&films=1` in a link opens the picker on arrival.

## 4. Together
- A room's link now carries the game. Opened from Bring the Reels Home, it brings the friend into the same game.
- A reel one of you brings home counts for everyone in the room, and says who found it.
- Pinch to zoom and names over friends were added earlier and are unchanged: two fingers on the picture move the
  camera in and out; a name floats over each friend, and over you, only while you are in a room.

## 5. Checked (headless; values read from the pages)
- Atlas: 167 entries in nine sections; no broken pictures; 28 distinct pages linked, none dead; searching "store"
  found the video store and seven others.
- WITH FRIENDS on the video store arrived in the store with the room line reading ONLY YOU · SEND THE LINK.
- FILMS listed 434 with covers; a search by a film's first word found 6; choosing one set the shelf's selection and
  the caption to NOW PLAYING with its title.
- The reel game's room link carried the game; the friend's entrance opened on BRING THE REELS HOME; a reel found by
  the host raised the friend's count from 0 to 1.
- Audit: 42 pages opened (every bonus page, the main page, the eleven games, one archive level, one sign). None
  threw a page error. Film Matter did not finish loading in 30 seconds here; it waits on a film from an outside host.

## 6. Not checked
- That a chosen film actually plays: the films are fetched from a host that cannot be reached from here.
- Two phones over the internet. Motion, sound, real fingers.
- "Wonky" games and levels: the audit only says they open without errors. It cannot say they play well.

## 7. Limits, plainly
- Only the orchestra's places and its reel game can be played with friends. The eleven games, the periodic table
  levels, the open water and the labs are for one.
- Editing a film (cutting it) is not in the rooms. The editor pieces remain where they were: Time Film, the Editor
  and VIDEOTEXT, all listed in the atlas.
- The atlas has no pictures for archive levels or signs, only their marks.

## 8. Next
1. Say which games and levels are wonky and how; fix those by name.
2. Friends in the open water.
3. A film chosen in FILMS shown on SCREENs you build, in any place.
