# SCION SYSTEM INSTRUCTION: THE FILM IN THE GAME (the open water, shot like a film)

**The direction:** "Add placed cameras at the reef crossings and predators. Think about this as a film inside a video game."

**Role.** Treat the open water as a film set that is always rolling:
- **Scenes:** each set piece is a scene.
- **Coverage:** each scene has several cameras, each a kind of shot, placed where a crew would put them.
- **An editor:** while you swim through a scene, a live editor cuts between the cameras that can see you, as an editor cuts coverage.
- **Takes:** every shot is logged as a take, with its scene, its camera, its kind and its length.

You play the swim, and the game makes the film of it.

## 1 · The scenes (as built in `bonus/sea.html`)
| scene | the set | its coverage |
|---|---|---|
| **1 · THE CURRENT** | the start | three tripods, and the spyglass (moved clear of the new ridge) |
| **2 · THE REEL CROSSING** | a ridge of rock across the way to the Reel Tower, three rocks high, with one gap under an arch; the ridge is solid, so the gap is the way through | **the establishing shot:** a tripod high on the ridge, 26 m along it, looking at the approach (wide, 56°). **Through the gap:** a tripod 19 m beyond the gap, low, looking back through it (medium, 42°). **The long lens:** a spyglass 60 m down the approach (16°) |
| **3 · THE SEWER CROSSING** | the same kind of ridge on the way to the Sewer Mouth | the same three shots |
| **4 · THE HUNTING GROUND** | two **hunters** (long dark bodies with a light for an eye) patrol a figure-eight on the way to the Medusae Trench. Come within 24 m and one hunts you, faster than its patrol, for up to 7.5 s. If it reaches you it strikes and lets you go, knocked aside. | **the hide:** a spyglass in the reef watching the patrol (20°). **The low angle:** a tripod on the floor looking up (64°). **The hunter's eye:** a camera riding each hunter, looking at you, live only while it hunts you (72°) |

## 2 · The editor's rules
- **Who can be cut to:** a camera can be cut to only if you are in its frame (its cone), so you can always see where you will be filmed. The hunter's eye can be cut to only while it is hunting you.
- **Hold a shot:** at least 2.6 s, so the film doesn't flicker.
- **A new angle:** after 4.5 s, if another camera has you.
- **Cut on action:** the moment a hunter starts hunting you, the editor cuts to its eye, after holding the current shot at least 1.2 s.
- **Leaving:** if no camera of the scene has you, the view is yours again.
- **The ray** (Scene 1's creature camera) still lends its view to anyone who swims up to it.

**Entering a scene gives its title** ("SCENE 2 · THE REEL CROSSING").

**Each cut opens a take:**
- a line names it ("SC 2 · TK 3 · wide: the establishing shot");
- a slate hangs in the water above the camera;
- the take is logged (`cj-sea-takes`: scene, take, camera, shot, start, length);
- the stats line counts the takes, and shows the scene you are in.

## 3 · Tested (simulated input, swiftshader)
| test | result |
|---|---|
| Swimming through the Reel Crossing's gap | Scene 2; the editor cut from **the establishing shot**, to **through the gap** as the jelly entered it, to **the long lens** beyond |
| Swimming at the ridge away from the gap | stopped 7.5 m before the ridge: the rock is solid, and the gap is the way |
| Swimming toward a hunter | at 14 m it began hunting, closing from 13.3 m to 9.7 m; the editor cut to **the hunter's eye** |
| Takes | two takes logged from the crossing (wide 1.8 s, long 1.1 s) |
| The three crossing shots | establishing, through the gap and the long lens each frame the jelly |

**Fixed along the way:**
- **The long lens burned white,** because glow near the lens swelled into the frame. A narrow lens now cannot see what is within 8 m of it, as a real long lens cannot focus that close.
- **The long lens was too far away:** the jelly was a dot. It is now 60 m away, at 16°.
- **The start-area spyglass sat on the new ridge.** It has been moved clear of it.

**Not yet judged:**
- the editor's timing on a real phone;
- whether the hunters' speed (8.5 m/s while hunting) is fair.

## 4 · Next
- **Screen the rushes:** at a projector at The Current, play the takes back in order, as a film of your swim. The Director from Four-Space (a recorded swim, a camera track) is the model for this.
- **The 180° rule:** inside a scene, don't cut to a camera on the other side of the jelly's line of travel, unless the jelly crosses it.
- **More set pieces:** the kelp at the Doodle Reef, the medusae in the trench.
