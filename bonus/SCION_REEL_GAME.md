# SCION RUN · BRING THE REELS HOME

Mode: RUN. Where: `bonus/jellyorchestra.html?game=1` (Bolas edition `/bolas/cities/?game=1`), or GAME in the dock.

## I. Diagnostic
- **Force in motion:** seven walkable places, twelve paints, a cast that sings, fifty songs.
- **Inherited ritual:** each was reached by a menu. Nothing you did in one place mattered in another.
- **The Lie:** a list of worlds is a world.
- **Catalyst:** WALK. Once you can move, the menu is the wrong way to travel.
- **Mirror moment:** you come home with a reel and a singer who was silent starts to sing.
- **Abandoned objective:** score. **Novelty bait:** paints were only ever chosen from a list. **Deceptive potential:**
  a paint can be a thing you earn and carry.

## II. Genome
```yaml
title: "Bring the Reels Home"
seed: "The Chorus has lost its voices. Walk through six doors, take one reel from each place, and the singers come back two reels at a time."
active_axis: CODE_MATH
ancestral_sources:
  - {id: scion-compiler-prompt, anchor: "supplied POML, worked case and section 7", role: "first success, consequence, memory in the world", evidence: "supplied note"}
  - {id: one-world, anchor: "bonus/SCION_ONE_WORLD.md", role: "shared place and paint contracts", evidence: "built"}
  - {id: speaking-cast, anchor: "bonus/SCION_SPEAKING_CAST.md", role: "four parts that can be withheld", evidence: "built"}
origin_conditions: ["Places that already share one scene", "A cast whose parts are separate"]
formation_epochs:
  - {id: menu-of-worlds, weight: 30, event: "worlds chosen from a list", reason: "still there, outside the game"}
  - {id: doors, weight: 90, event: "a door is a picture of where it leads", reason: "travel is now an action in space"}
  - {id: reels-as-voices, weight: 100, event: "reels give singers back", reason: "the only consequence that crosses places"}
  - {id: paint-as-power, weight: 75, event: "each reel unlocks a way of seeing", reason: "a reward you can use at once"}
signature_rules: ["A door shows the place it leads to.", "One reel per place, at the far end.", "Singers return at 0, 2, 4 and 6 reels.", "Progress is kept on this device."]
tagline: "Six doors out. One way home."
ttl: 2
lineage_tags: ["#doors-in-space", "#reels-as-voices", "#paint-as-power", "#hub-and-ring"]
```

## III. Theory of play and Olog
I will first construct the theory of play, then the architecture.
1. **Invitation:** press GAME. Press it again to stop; nothing is lost.
2. **Magic circle:** the Chorus and six places; no clock; the song keeps playing.
3. **Stance:** wanting to hear the whole chorus.
4. **Illusion:** that the places are next to each other. Supported by doors that show their destination.
5. **Grammar:** walk, look, go through a door, take a reel, change paint.
6. **Resistance:** distance only. There are no walls, enemies or timers.
7. **Chance:** none.
8. **Memory:** reels and paints persist on the device. A door's frame turns amber once its reel is home.
9. **Spoil-sport:** jumping by the worlds menu still works and still counts; the doors are rebuilt where you land.
10. **Change tests:** (a) remove the door pictures: can you still find the depot? (b) give all six reels at once: is the full chorus still a reward?

```
◻(DOOR) → [on contact sets] → ◻(PLACE)                      cooldown 1.2 s after arrival
◻(REEL in PLACE) → [on contact adds] → ◻(REEL_LEDGER)       a set; order does not matter
◻(REEL_LEDGER) → [unlocks] → ◻(PAINT)                        one paint per place
|REEL_LEDGER| ≥ 2k → [enables] → ◻(CAST_PART k)              k = 0..3
◻(REEL_LEDGER) → [is stored as] → ◻(DEVICE_MEMORY)
```
Reel additions commute (set union), so any route gives the same end state. STRUCTURAL.
Assumptions: safe — one player, one device; uncertain — that silence reads as "missing singers" and not as a fault.

## IV. The artifact
- **Hub:** the Chorus, with six doors in two rows of three. Each door is a picture of its place with a name tag.
- **Places and paints:** library → ink wash; data center → glass; video store → risograph; film depot → woodblock;
  wet collection → watercolour; orbit → cyanotype. Each place also has a door home and doors to its two neighbours.
- **Reel:** a turning gold reel at the far end of each place. Touch it and a card names the paint you won.
- **PAINT:** a dock button that appears with your first reel and cycles the paints you hold.
- **Voices:** LAVENDER always sings; HOLLOW from two reels; TICK from four; all four together at six.
- **Panel:** top left, reel count and what to do next. RESET THE GAME is in the menu.

**Also fixed: the Chorus camera.** It has its own two shots, four bars each: the whole stage with the wall of words, then
the row of four singers. The earlier fix was being overridden every frame by the ordinary shot list.

**Evidence (MEASURED, local copy, headless browser, keyboard only)**
- Hub built six doors. Walking into the depot door changed the place; the depot had doors to chorus, store and wet, and a reel.
- Walking down the aisle took the reel: ledger `["depot"]`, saved on the device, paint WOODBLOCK applied, PAINT button shown.
- Home with two reels the panel read "HOLLOW is back".
- Chorus camera: both shots captured; all four singers and the wall are in frame in each. No page errors.

**Verdict:** inconclusive. It works as specified; whether it is fun is unjudged.
**Not run:** touch controls, all six reels by walking, the finale, the orbit reel (it floats; you have to look up and walk at it), the live site.

## V. Next
- **Walls and floors**, so a door is the only way out.
- **Objects under one contract:** a can in the depot plays its film; a jar in the wet collection adds a species.
- **A second ring:** the seven Bolas cities, each holding a cut to rebuild.
- **Reentry:** mutation invert_goal — carry a reel out of the Chorus and a place loses its paint. ttl 1.

#doors-in-space #reels-as-voices #paint-as-power #hub-and-ring
