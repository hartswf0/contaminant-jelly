# SCION SYSTEM INSTRUCTION: TAXA (species · verbs · the life of a jelly)

**Role.** Keep every level a different animal doing a different thing, and let the levels add up to one life and one film.

**The direction:**
- "many of the current jars lack a clear sense of what we are meant to do, or a sense to explore"
- "we keep seeing the same videos over and over; each level feels repetitive"
- "there is no bigger arc"
- "different species of level need a taxonomy: how many different types of jellyfish do we have, movement, levels"

## 0 · The audit (before)
- **86 levels and one jellyfish.** Every level used the same body, speed, reach, arms and sting.
- **70 levels played one game:**
  - the 67 cineosis levels and the 3 Crash Lab levels shared one recipe;
  - films in a line, "take frames", a school of fish and comb jellies.
- **Only 16 levels had a verb of their own:**
  - the 11 drifts;
  - Doodles, Menagerie, Bolas, Strata, Spectrum.
- **Repeats:** the 11 drifts all drew from the same 109 films at random. They opened on the same videos and repeated them inside a level.
- **No arc:** levels unlocked nothing, and nothing carried over between them.

## 1 · The taxonomy (after): 13 species in 3 phyla
Each level is **a species** (the body) playing **a mechanic** (the verb).

| ch | species | latin | phylum · class | body | verb | hero level |
|---|---|---|---|---|---|---|
| 1 | Upside-down jelly | *Cassiopea xamachana* | Cnidaria · Scyphozoa | slow (0.75×), 6 arms | **DIG** | Silt Bench |
| 2 | Moon jelly | *Aurelia aurita* | Cnidaria · Scyphozoa | drifts (0.9×), 6 arms | **WAKE** | Ascent |
| 3 | Crystal jelly | *Aequorea victoria* | Cnidaria · Hydrozoa | green glow, pulse 1.3× | **WATCH** | Toward the Surface |
| 4 | Salp chain | *Salpa maxima* | Chordata · Thaliacea (not a jelly) | no sting | **LINK** | Pairs |
| 5 | Sea nettle | *Chrysaora fuscescens* | Cnidaria · Scyphozoa | reach 1.35× | **CHOOSE** | Twin Caves |
| 6 | Lion's mane | *Cyanea capillata* | Cnidaria · Scyphozoa | slow (0.8×), reach 1.9×, large | **SWEEP** | Lure |
| 7 | Box jelly | *Chironex fleckeri* | Cnidaria · Cubozoa | fast (1.55×), 4 arms | **CHASE** | Ray Run |
| 8 | Comb jelly | *Mnemiopsis leidyi* | Ctenophora · Tentaculata (not a jelly) | **no sting**: the pulse only lights | **CIRCLE** | Halo |
| 9 | Mauve stinger | *Pelagia noctiluca* | Cnidaria · Scyphozoa | violet, pulse 1.4× | **WATCH** (bloom) | Bloom |
| 10 | Portuguese man o' war | *Physalia physalis* | Cnidaria · Hydrozoa (a colony) | reach 1.5× | **DYE** | Secondhand Doodles |
| 11 | By-the-wind sailor | *Velella velella* | Cnidaria · Hydrozoa | blue | **GATHER** | Menagerie |
| 12 | Atolla | *Atolla wyvillei* | Cnidaria · Scyphozoa | deep red, pulse 1.7× | **LIGHT** | The Long Descent |
| 13 | Immortal jelly | *Turritopsis dohrnii* | Cnidaria · Hydrozoa | small (0.7×) | **REWIND** | Slices |

**What each body changes:**
- swimming speed and reach (how close you must be to take a film);
- the arm cap (from 4 to 8);
- the pulse radius;
- whether the pulse stings (and so scares hunters);
- the bell's size and colour.

**The 14 mechanics** (`taxa.js` MECH), each with one verb, three plain steps and an idle nudge:
- WAKE, LINK, SWEEP, WATCH, CIRCLE, CHASE, CHOOSE, LIGHT, DIG, DYE, GATHER, TAKE;
- REWIND, in two forms:
  - the slices of one film, in order (Slices);
  - archive films going back in time, each older than the last, read from their year (new).

## 2 · The archive re-laid
The 70 look-alike levels each take their species' verb, laid out for the size of their film pool.

**Cineosis types and the species they become:**

| species | verb | cineosis types |
|---|---|---|
| Atolla | LIGHT | perception, noosign |
| Crystal jelly | WATCH | affection, hyalosign |
| Box jelly | CHASE | impulse |
| Lion's mane | SWEEP | action · small |
| Sea nettle | CHOOSE | action · large |
| Salp | LINK | attraction, relation |
| Upside-down jelly | DIG | inversion |
| Moon jelly | WAKE | discourse, lectosign |
| Mauve stinger | WATCH (bloom) | dream |
| Immortal jelly | REWIND | recollection, chronosign |
| Comb jelly | CIRCLE | opsign · sonsign |

**Subjects:**
- person → crystal;
- machine → box;
- landscape → lion's mane;
- animal → salp;
- screen → comb;
- crowd → moon.

**Crash Lab:**
- The Crash Lab → lion's mane (SWEEP);
- Found Odyssey → moon jelly (WAKE);
- Handmade → upside-down jelly (DIG).

**Result:**
- 14 mechanics are in play;
- no mechanic holds more than 14 of the 86 levels;
- every species has 1–10 levels.

## 3 · No repeats
- **Films are dealt from a deck:** none repeats until every film in the pool has appeared.
- **Each drift gets its own share first:** of the 109 films, a ninth are dealt to each drift first. In testing, the first 8 films of four drifts were 32 different films.
- **Years for rewind:** an archive film's year comes from its record, or from its title ("ca. 1938") when the record has none. Undated films are left out of a rewind run.

## 4 · Clear instructions
- **The briefing card:** chapter and species (with its Latin name and taxonomy), the verb in large type, three steps, the goal and its number, then one true fact about the animal that explains the rule.
- **Idle nudge:** after 16 s without progress, the verb and its nudge are said again. The amber arrows already point to the nearest film.
- **In the seas,** entering a region says its verb.

## 5 · The arc: the life of a jelly
- **13 chapters** follow one life: a polyp on the floor (dig), the first bell (wake), learning to see (watch) … the deep (light), and rewind, when it becomes a polyp again. The seas are the open water after the chapters.
- **The landing** shows the 13 chapters as the main shelf: each with its jar, its verb, its species, and the archive "waters" that share its body.
- **Moving on:** swiping ← at the end of a chapter's hero level goes to the next chapter.
- **The life reel** (`reel.html`):
  - every level you finish (not eaten) adds the clips you kept, as long as you held them;
  - the clips are ordered by chapter into one film, in the same cutting room (recut, save);
  - sealed chapters are marked with their stars.
- **Fixed:** a hunter could be `undefined` on some levels (a signed shift gave a negative index), which crashed them, e.g. type-perception.
