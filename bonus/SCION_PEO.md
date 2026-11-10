# SCION PEO · a score language for The Lab (peo/0)

PAELEO defines its cycle as **Prompt · Ekphrasis · Operation**: a prompt is what is asked for, an ekphrasis is what a viewer should see or hear, an operation is what is done to the world, and the result changes the situation the next prompt comes from. Before peo/0 that cycle existed only as prose (bolas `tools/paeleo/case.json`, the PAELEO pages). It had no concrete syntax. peo/0 gives it one.

- **The text is the source of truth.** It is a plain, line-based file (`.peo`), readable and diffable, and safe to paste into a URL.
- **The JSON is its compiled form.** `bonus/peo.js` turns `parse(text)` into `{score, errors}`, and `serialize(score)` turns a score back into canonical text. Round-tripping keeps the meaning: `same(parse(serialize(s)).score, s)`.
- **The Lab plays it** (`bonus/lab.html`). The panels and the score are the same thing in two forms. Loading a score sets the panels, and **PANELS → SCORE** or **COPY SCORE** writes the panels back out as a score.

## Lines

Each line is one directive. Blank lines and lines that start with `#` are ignored. A `#` after whitespace starts a comment, except inside quotes.

| directive | form | what it sets |
|---|---|---|
| `@prompt` | `@prompt <free text>` | the ask. Several lines join together. |
| `@world` | `@world [lab\|open\|steer] key=value …` | the water and the clock: `bpm`, `offset` (s), `haze`, `current=x,y,z`, `song=<jelly-studio id>`, `audio=<url>`, `onsets=<url>` (cast.json form: `{roles:{kick:[[t,…],…]}}`), `duration`, `until` |
| `@cast` | `@cast <name>:<jelly> key=value …` | puts a jelly in the water: `at=x,y,z`, `role=<kick\|snare\|hat\|bass\|choir\|call\|bed…>`, `view=<flesh\|nerves\|muscle\|strain>` |
| `@light` | `@light <preset\|path> key=value …` | the Whitney organ. Presets: `Permutations`, `Matrix`, `Arabesque`, `"Music Box 1:n"`, `"Drift (tension)"`. Paths: `rose`, `lissajous`, `epicycle`, `musicbox`. Parameters: `n base ratio detune radius dR dTheta k height intensity on`. |
| `@camera` | `@camera <mode> key=value …` | the modes are `orbit dolly crane track beneath far free chase`; the parameters are `speed ease dist fov follow=<name> auto=on` |
| `@steer` | `@steer <name\|you> key=value …` | who is piloted, plus `scheme=glide\|tap\|drag`, `thrust turn drag grav reach arms beats` (strokes per this many beats when driven) |
| `@ekphrasis` | `@ekphrasis <time>[..<time>] "<what is seen or heard>"` | a caption in the lower third, from its time to `until` (or for 5 s) |
| `@op` | `@op <time>[..<time>] <verb> args… key=value …` | an operation, fired when the clock crosses its time. A range ends it. |
| `@test` | `@test <time>[..<time>] <kind> args… [op number]` | a check evaluated live. Over a range it measures from the first time to the second. |
| `@source` | `@source <id> key=value …` | provenance: `url`, `basis`, `title` |

**Times:** `b16` is beat 16, counted as `offset + 16·60/bpm`. `12.5s` or `12.5` is seconds, and `1:02.5` is minutes and seconds. A range is written `a..b`.

**Values:** `x,y,z` is a vector. `on` and `off` are booleans. Use `"…"` for anything with spaces.

**Verbs:**
- `pulse <name> [k=]` fires the leading pacemaker. A real nerve may refuse.
- `swim <name> to=x,y,z|to=<name>` makes the jelly swim on its own strokes. With a range it stops at the end.
- `steer <name> [scheme= thrust= …]` hands that jelly to the hand.
- `view <name> <view>`
- `film <name> src=<url> [from=s]` plays a film in a rig's bell.
- `clear <name>`
- `camera <mode> …`
- `light <preset|path> …`
- `say "<text>"`
- `mode <inspect|open|steer|orchestra|score>`
- `set <name>.<control>=<value>` sets a jelly's own range control by its label, or a steer parameter (`set glass.drag=4`).
- `current x,y,z`
- `haze <density>`

**Film memories** are first-class verbs (`bonus/memory.js`). Each one is a pure function of the score clock, so playback, scrubbing and recording agree.
- `memory <id> holder=<name> src=<mp4>|still=<image> [from=<clip s>] source=<@source id> [gain=]` declares a clip held by a jelly. The clip time is `from + (clock − the line's time)`. Its `@source` must give a rights basis: CC0, public domain / US-government work, or the producer's own work. Anything else is a parse error.
- `condense <id> a..b [from=<name|x,y,z>]`: flecks of the picture travel in and gather under the holder's bell. The picture is in flecks only while in transit.
- `bloom <id> a..b stage=<pull-in|catch|surface|swallow|hand-off> [size=0.5] [at=center|left|right] [side=] [to=<name>]`: the full-resolution picture, `size` of frame height, with its bottom edge above the caption band (the lower 20%). The stages:
  - **pull-in** grows out of the holder;
  - **catch** flies in from a side, and the holder pulses as it lands;
  - **surface** rises from below;
  - **swallow** holds, then shrinks back into the bell;
  - **hand-off** travels on to another jelly, which becomes its holder.
- `keep <id> a..b beside=<name|memory> [size=0.22] [dx=] [dy=]`: a small picture kept beside something.
- `release <id> a..b to=<name|memory|x,y,z> [uv=u,v] [arc=]` (or `stream`): the picture fades in the first 30% of the range while its flecks stream along an arc into the target. `uv` is a point inside a target memory's picture.
- **Camera beats** are `@op <t>[..<t>] camera <mode> [frame=top|center] [cut=on] [to=<dist>]`:
  - `frame=top` puts the subject in the upper third, above a bloom;
  - `cut=on` snaps instead of easing;
  - over a range, `to=` pushes in or pulls out.

**Tests:**
- `moved <name> > m`
- `dir <name> <±x|±y|±z> [> m]`
- `near <name> <name|x,y,z> < m`
- `beats <name> >= n` counts beats since the score began.
- `rate <name> > bpm`
- `visible <name>`
- `fired <name> >= fraction` is the share of entrained onsets the nerve accepted.
- `fps > n`
- `ui hidden|shown`
- **Cold reads on the rendered frame.** A clean plate is rendered without the thing and the difference is measured at 320×180, so they only see what is on screen:
  - `bloomh <memory> >= 0.45` is the picture's height as a share of the frame;
  - `bloomb <memory> >= 0.2` is its bottom edge, which must sit above the caption band;
  - `legible <memory> >= c` is the RMS luminance contrast of the picture as shown;
  - `gone <memory>` passes when the picture covers less than 0.5% of the frame;
  - `flecks <memory> in <name|memory> >= share` is the share of fleck pixels inside the target's box;
  - `inbox <name> x0,y0,x1,y1 >= share` is the share of the jelly's pixels inside a box (frame fractions, y down);
  - `streamed <memory> a..b >= seconds` is the time the flecks were on screen in transit.

**Errors** carry line numbers. The parser reports:
- unknown directives, verbs and test kinds;
- a missing time or a bad time;
- names used but never cast;
- `set` without `name.control=`;
- a comparison with no number after it.

## Example

```
@prompt a medusa swims out toward the orchestra's beacon and comes home
@world open bpm=96 haze=0.02
@cast medusa:medusa at=0,0,0
@camera chase dist=7 follow=medusa
@steer medusa scheme=glide thrust=2.6
@ekphrasis 0s..5s "the open water: a dune floor, stones, kelp, and six lit rings"
@op b2..b22 swim medusa to=8,1,10
@op b24..b48 swim medusa to=0,0,0
@test b2..b22 dir medusa +z > 1
@test b48 near medusa 0,0,0 < 6
```

## In The Lab

| piece | what it does |
|---|---|
| **INSPECT** | the Jelly Lab as it was: spawn, inspect, camera, orchestra, light |
| **OPEN WATER** | swim the selected jelly. Hold the water to swim toward your finger (glide), double-tap to pulse, use WASD with R and F, and space. The `tap` and `drag` schemes come from `@steer`. Strokes land on the jelly's own beats. |
| **STEER** | the steer-lab arms (`tentacles3d.js`) on the same body. Each finger owns one arm until it lifts, and the arms grab stones, kelp and the floor. |
| **SCORE** | the editor with live errors: PLAY/PAUSE, STOP, STEP 1 BEAT, scrub, APPLY, PANELS → SCORE, COPY SCORE, COPY SCORE LINK (`?s=`). The test strip turns green or red as tests run. |

**URLs:**
- `lab.html?score=scores/open-water.peo` loads a score from a URL. Relative URLs inside it resolve against the score.
- `?s=<base64url text>` carries the score in the link itself.
- `&play` starts it.
- `?mode=open|steer` enters a mode.
- `jellylab.html` still works and redirects with its query.

**Headless:** `node bonus/scores/run-score.mjs [files…] [--moto <dir>] [--from s] [--until s]` plays scores in headless Chromium and prints every test. It exits 1 on a failure.

**Recording:** `node bonus/scores/run-score.mjs <score> --record out.mp4 --from 64 --until 93 [--fps 24] [--size 1280x720] [--moto ../moto]`.
- The score is played frame by frame in fixed 1/fps steps, and every memory film is seeked to its clip time before each frame renders.
- Captions are drawn into the picture. The frames are piped to ffmpeg and the song is cut to the same window.
- Every @test, the cold reads included, is measured on the frames that go into the file. Tests before `--from` are reported "scrubbed past", and tests after `--until` are "not reached".

**Lab tests:** `node bonus/scores/test-lab.mjs [--shots dir]`.

## Limits (peo/0)

- **Scrubbing** replays operations instantly but does not fast-forward the physics. Tests that you scrub past are marked "scrubbed past".
- **The 4D steer lab's w-axis** is not in the shared water. `steerlab4d.html` links to the 3D steering score.
- **The Corrugated Sky jelly cut** keeps the cut's timing, onsets, memory windows and full-res crops (`scores/media/corrugated-sky/`, re-encoded from the cut's bloom frames).
  - **Kept:** the dot law in transit is approximated by fleck colours at eight ink levels.
  - **Not ported:** the cut's halftone banks, its twelve-tentacle crown, its kick halos and its title cards.
- **Fingers in the score:** the score can set the steer physics, but it cannot place arms. Arms are the hand's.
