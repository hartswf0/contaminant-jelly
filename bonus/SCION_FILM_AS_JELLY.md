# SCION SYSTEM INSTRUCTION: THE FILM IS THE JELLY (four kinds of thing, kept apart)

**The direction** came as a long note. Its main threads:
- **The closest reference is wet cloth:** a membrane that folds, exchanges material with the water, and carries the encounter into its next movement.
- **Give the bell three separate properties:** stiffness (how it moves), thickness (how it looks), saturation (what it carries).
- **The wake is a memory.** A vortex beneath a moon jelly's bell supplies extra thrust as the bell refills: pulse → curl → glide.
- **The film itself is the jelly:** a block of frames, a field over (x, y, z, t), with a viscosity per pixel. Thick regions carry a gesture intact; thin ones shear it into overlapping moments. A cut can creep around a body and leave a pocket of the old scene in a fold.
- **"These are several different types of things."**

**Role.** Keep the types of thing apart. Each one is its own material with its own fields, and each gets its own experiment. They can be combined later.

## 1 · The four kinds of thing
| kind | what is physical | its fields | built as |
|---|---|---|---|
| **A · Film as matter** | the frame's pixels are particles | phase: sheet, liquid, sand, home | **Film Matter** (`filmmatter.html`, already built) |
| **B · Film as membrane** | the bell's skin | **stiffness** (how it moves), **thickness** (how it looks), **saturation** (what it carries) | **Wet Bell** (`wetbell.html`, new) |
| **C · Water as memory** | the wake | a vortex ring per stroke: where it is, how it turns, how strong it is, what it carries | in **Wet Bell** |
| **D · Film as time-material** | the shot's space-time block | **displacement** (which moment shows here), **viscosity** (how strongly neighbouring moments hold together), **the cut** (how far the next shot has reached) | **Time Film** (`timefilm.html`, new) |

**The distinction to keep** (from the note): *viscosity* says how strongly nearby parts resist sliding past each other; *displacement* says which moment is visible there. Time Film stores them as two separate fields.

## 2 · Wet Bell (B and C, as built)
**The skin** is 6 rings × 24 nodes over the bell. Each node has:
- **stiffness:** the crown is stiff (1.0), the rim soft (0.25); soft nodes contract and wobble more;
- **thickness:** it rises where light is soaked up and drains as it spreads; it shows as thin-film interference colour;
- **saturation, and a carried colour.**

**Soak:** swim through a cloud of light (four clouds, each the colours of a frame of an archive film). A mote that touches the lower rim is taken up by the nearest node, whose saturation and colour change.

**Spread:** during the glide, what the bell carries diffuses across the skin, weighted by stiffness, and slower while the bell contracts. The total is conserved: nothing is lost by spreading.

**Shed:** a hard pulse (double-tap, or shift + space) throws 60% of what the lower bell carries into the wake.

**The wake:** every pulse leaves a vortex ring of 200 motes. It curls (each mote turns around the ring's core), travels back, widens and fades over about 4.5 s. Shed colour rides in it, so **you can read where the jelly has been from what is still moving in its wake.**

**The water's memory:** a young ring still beneath the bell (0.25–1.1 s old, within 2.4 m) pushes the bell along its axis as it refills: pulse → curl → glide, after Gemmell et al.

**Controls:**
- drag to steer (relative to the view); holding a steer pulses on its own;
- tap to pulse; double-tap for a hard pulse that sheds;
- the unrolled bell (top right) maps saturation and thickness from crown to rim.

## 3 · Time Film (D, as built)
A clip's 64 frames sit in one GPU atlas. Every pixel shows frame `playhead + D(x, y)` of clip A, or of clip B where the cut has reached. The fields live on a 64 × 48 grid, uploaded as half floats so time does not band.

| field | how it behaves | how you touch it |
|---|---|---|
| **D**, displacement (frames) | moved by a time-velocity W that spreads to neighbours in proportion to thickness, and damps | **STIR:** drag right to pull moments forward, left to pull them back |
| **ν**, thickness (viscosity) | starts from the clip itself: **where something moves the film is thick, and carries the gesture whole; where nothing moves it is thin, and shears** | **THICKEN** and **THIN** paint it |
| **C**, the cut | a front of clip B, spreading cell to cell: fast through thin film, slowly through thick, so it **creeps around a moving body and leaves a pocket of the old scene** | **CUT:** touch where the next shot begins |

**SEE THE FIELDS** shows them:
- displacement as blue (ahead in time) and amber (behind);
- thickness as brightness;
- the cut's front as a gold line.

## 4 · Tested (simulated input, swiftshader)
| test | result |
|---|---|
| **Wet Bell:** pulse → curl → glide | the same pulse carried the bell **2.45 m with its ring, 2.06 m with the ring removed**: the wake's push is about a fifth of the glide |
| **Wet Bell:** soak | swimming through a cloud, the rim took up **314 motes** |
| **Wet Bell:** spread | over a 4 s glide, the crown's share rose **tenfold (0.09 → 0.93)**; the total was unchanged (**18.84 → 18.84**) |
| **Wet Bell:** shed | a hard pulse threw **a third** of what the bell carried (**18.84 → 12.76**) into the wake as **200** coloured motes |
| **Time Film:** viscosity | the same stir in the thickest film spread **19% of its displacement 4 cells away**; in the thinnest it stayed put (**0%**): shear |
| **Time Film:** a gesture sheared | a stir across a moving figure showed it **three times at once**, in three moments |
| **Time Film:** the cut | started from a thin corner, it reached **50% of the thin film but only 3% of the thick** in 7.5 s, leaving the figures as **pockets of the old scene** |

**Fixed along the way:**
- **Thickness ran the wrong way round.** It first came out with still places thick, so the cut rushed through the bodies. It is now the right way round: gestures are thick.
- **The time offset banded.** At 8-bit precision it moved in quarter-frame steps; it is now stored as half floats.
- **Dark seams where moments diverge.** The atlas's mipmaps smeared the tile edges; they are turned off.
- **The cut's front was blocky.** Its edge is now softened.

**Not yet judged:**
- feel on a phone;
- whether 64 × 48 is fine enough for the cut's pockets;
- whether the wake's push is felt or only measured.

## 5 · The references, and what each gave
| reference | what was borrowed |
|---|---|
| Saharan's wet cloth; libWetCloth (Fei et al. 2018) | saturation that spreads within a membrane and drips back out: the bell's soak, spread and shed |
| Soap film with evolving thickness (Ishida et al. 2020) | a thickness field you can see: the skin's interference tint |
| Ten Minute Physics; Trapnest Jelly | stiffness and compliance as separate, tunable properties |
| Unified SPH fluid–shell (Lenaerts & Dutré 2008); Physics from Scratch's coupling | next: the skin's motes as particles of the same sea, pushing both ways |
| Discrete viscous sheets (Batty et al. 2012) | next: a flap that slumps rather than springs; Time Film's thick film is its cousin in time |
| Medusae; Aurelia | the pulse travelling through a particle body |
| Gemmell et al.: passive energy recapture | the ring that pushes the bell as it refills |
| Macklin et al. (unified particles) | the baseline Film Matter is built on |

## 6 · Next: combining them
- **Wet Bell × Time Film:** the bell soaks up a **fragment of duration**. The clouds are moments of a film; what the bell carries keeps playing on its skin, a little behind the present; a hard pulse sheds that moment into the wake.
- **Film Matter × Wet Bell:** swim through film-water and come out carrying it.
- **The open water:** clouds of light from the films the player passes; the wake as a visible trail of where you have been.
