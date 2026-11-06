# The Current (second version): how it works

You rise through a vertical tube made of the second-hand archive's **109 films** (the same shots as the abc-flix Icaro Pro tunnel). Frames load from `secondhand-motion` on GitHub Pages.

## The tube is time
- Ring *k* sits at height *k* × 2.3 m and holds 16 frames, each from a different film.
- A panel in ring *k* shows frame (2*k* + *j*) of its film, so **rising runs the archive forward and sinking runs it back**, like scrubbing through a tomography of films.
- The rings turn a little each level, so the tube is a helix of moments: the time worm.
- Only the visible rings exist. 17 rings × 16 panels share one 2048² atlas, and each frame is uploaded into its own slot as a small sub-image, never as a whole-atlas upload.

## Brushing and catching
- When a strand comes within 0.7 m of the wall, the panel it touches **lights up and plays** its film at the film's own frame rate for about 2 seconds.
- An arm that lingers on a playing frame (0.6 s) **catches it**. The frame joins that film's strip.
- **Each new film grows a new strip**, up to ten. You start with two lengths of clear leader, which take the first two films.
- **Each strip is a timeline**: its frames run from root to tip in the order caught, and the strip lengthens as it fills.
- A panel gives a frame once every 9 s, and catches are at least 1.1 s apart, so an edit is chosen, not vacuumed.

## The body
- **The bell is particles** (3,400 splats on the moon-jelly dome) coloured by the film you caught last, **playing** on the bell at its frame rate, inside a faint fresnel shell. Its contraction wave travels from crown to margin.
- **The arms are film strips**: ribbons on parallel-transported frames, with a slow curl, textured with the caught frames and open sprocket holes.
- **A sparse fringe** of 10 short threads is kept faint so it doesn't read as hair.

## Physics
- Rotation-free Verlet chains (250 nodes), on a fixed 1/120 s tick with a backlog cap.
- 14 alternating Gauss-Seidel passes of length constraints, plus a soft bend span on the arms.
- The tube's signed distance field (φ = R − r) and the bell's own volume keep everything in place.
- Drag pulls strands toward the water. The water wells up in the middle, slackens at the wall and turns slowly.
- The bell is slightly heavier than water: **stop pulsing and you sink back through time**.

## Controls
- **Steer.** Hold where you want to go. A ray from the camera to the tube wall gives the target, so you swim toward the frame you touch. Arrow keys / WASD also steer.
- **Pulse.** Tap, click or press space. Pulses 0.5–1.1 s apart build rhythm.
- **Ink.** The red ink falls through the current, clings, and burns the newest frame on a strip. Two fast pulses shake it off. If too much clings, you sink eight metres.
- **Your edit.** After four frames, *Play your edit* replays every caught frame in order with its film title. *Save edit* downloads the edit as an EDL (`the-current-edit.json`: film, frame, source URL, height).

## The surface (VOIDBASTARD-TAO)
- On screen are only the world, one line of what just changed (it fades after about 2 s), a faint state line (height, frames, films; ink only while there is ink), and the two edit buttons once there is an edit to play.
- There are no meters over the films.

## Design loop (video-to-game, restarted)
- A new design video: `fal/design_v2_720.mp4` (MiniMax H3 Max, one call, logged in `fal/fal_log.json`).
- Its study sheet, `fal/design_v2_sheet.jpg`, set the spec: camera level with a large bell high in frame, long hanging strands, the wall as stacked curved bands of small frames with dark gaps, and wisps of red ink.

## Measured
Headless Chromium, software rendering, 960×540 and 844×390 touch. Five films were served locally, because this session cannot reach github.io.

| measure | result |
|---|---|
| strand stretch residual | 2–6% |
| frame time p95, CPU side | 4–6 ms |
| 70 s scripted run (holding toward the wall, pulsing) | 28–35 frames from 5 films, 5 strips grown, no page errors |

**Not measured:** GPU frame time on real devices, loading the full 109 films from github.io (it should work, since it's the same site as abc-flix), and how it feels in the hand.
