# SCION SYSTEM INSTRUCTION · ONE WORLD

Where: `bonus/jellyorchestra.html` (Bolas edition: `/bolas/cities/`). Press SETTINGS or WALK in the bar.

## 1. Thesis
The experiments were built as separate worlds and reached by separate addresses. They are one scene. So the
system is now stated as one world with four dials, and a contract every room and every paint has to meet.

## 2. The four dials (the state)
| Dial | Values | Address |
|---|---|---|
| PLACE | 12 experiments, 6 rooms (library, data center, video store, film depot, wet collection, orbit), 21 cities | `?look=` or `?city=` |
| PAINT | none, 11 experiment lenses, and 12 paints and prints | `&lens=` |
| SONG | every song in the studio | `&song=` |
| CAMERA | the edit, or you | `&walk=1` |

**Any place takes any paint.** Before this, only cities took a lens. Now a room does too: the depot in woodblock,
the orbit in cyanotype. The settings panel shows the address of the state you are in; COPY ADDRESS shares it.

## 3. The contracts
**A place** must provide:
- `id`, `name`, one line of what it is
- `build(group)`: its geometry and lights, built once, in the shared scene's units (floor at y = -6.8, aisle along z)
- a rule, a swerve, a thing to watch and a test (the experiment card)
- optionally: a performance style, a sound bed, objects that can be touched

**A paint** must provide:
- `id`, `name`, a post mode in the one shared shader, bloom and trail amounts
- a rule, swerve, watch and test of its own
- a builder: how a frame is carried and what it leaves, for cities with cut lists
- it reads only the rendered picture, the song's film and the beat; it may not assume a place

**An object** (first built in the video store) is one of three kinds:
- film: plays a real file on the room's screens
- door: sets PLACE
- power: presses a control (swerve, song, follow, video, record, pause)

**A song** provides bars, lanes, energy per bar, and two films it was cut from.

## 4. Steering
WALK takes the camera from the edit and gives it to you.
- Desktop: drag to look; W A S D or arrows to move; Q and E to sink and rise; shift to hurry.
- Touch: drag to look; a pad appears at lower left to move.
- It works in every place, because every place is the same scene. There are no walls: you can walk through a shelf.

## 5. New in this pass
**Prints (four)**
| Paint | Rule |
|---|---|
| WOODBLOCK | Four blocks: indigo, slate, bare paper, rust. Every flat carries the grain; the sky is cut in long strokes |
| CYANOTYPE | Whatever lies on the paper stays white; the coating is brushed on unevenly and stops short of the edge |
| RISOGRAPH | Three drums and black, each at its own screen angle and a little out of register |
| GLASS | Everything is glass: only edges and thickness show |

**A place in space: THE ORBIT.** An observation deck above a planet with moving cloud, about 4,200 stars, a few
unnamed constellations, and four long ribbons of film strung between masts. The orchestra drifts between them.

## 6. What was checked
- By script, in the depot: WALK on, W held for 5 s moved the camera about 8 units; a drag turned it; no errors.
- Settings: choosing WOODBLOCK repainted the depot and the address read `look=depot&lens=woodblock&song=…&walk=1`.
- Stills of the four prints, the orbit, and the depot in woodblock: no page errors.

## 7. What was not checked
- Motion and sound. The touch pad (not run on a touch screen). Phone speed. The live site.
- Paints over the experiment worlds that already have their own post effect (the paint replaces it).

## 8. Honest distance from the reference pictures
The pictures show places with their own architecture: a greenhouse of pressed-flower prints, a waterwheel of film
on a cliff, an amphitheatre under an eclipse, a cardboard town, a market, an ice canyon with film frozen in it, a
marsh with a projector, a flooded ruin of jars, a rotunda of cans. Of those, only the orbit deck is built, and
simply. The prints are filters over the same orchestra; they do not redraw the world as a woodcut would.
Not built: collisions, doors you walk through between rooms, objects in rooms other than the store, a doodle or
thread style, and saved settings.

## 9. Next, in order
1. Doors in space: walk to the end of an aisle and you are in the next place.
2. Objects in every room under the one contract (cans, jars, books, racks).
3. One new place per reference picture, starting with the ice canyon and the waterwheel.
4. Line styles as a fifth dial: outline weight and wobble (doodle, thread, brush) separate from colour.
