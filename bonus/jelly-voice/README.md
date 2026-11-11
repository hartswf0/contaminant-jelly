# Jelly Cast — prepared physical voices

This branch adds shared speech, joke, song and rap controls to seven existing jelly pages. The renderer is a fresh build of **unmodified Chimera at `e33221d006f44c78849210eb29dd1eb9755dc78e`**. It does not contain the custom membrane or closure-guard patch described in the earlier Speaking Film handoff; that patch was not found in this workspace or the repository.

**Current acceptance:** actual WASM rendering, score timing and control logic pass the independent checks. Browser integration and human listening remain unverified. Chromium was blocked before opening a page by this environment's local-socket restriction; the connected browser was unavailable, and the cloud browser could not reach the local preview. This branch is a reviewable checkpoint, not a certified production voice or completed film system.

## Run it

Serve the repository over HTTP; ES modules, workers and the dictionary should not be opened directly with `file://`.

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000/bonus/jellyjar.html`. Press **Voice**, choose a character and delivery, then **Prepare & play**. The first preparation loads about 1.9 MB of engine and dictionary assets. A worker synthesizes the complete phrase before playback. **Stop** also cancels preparation. **Replay**, **Save vocal WAV**, and **Save take record** always use the last successfully prepared take; changing a field does not change that saved take.

The same controls are in:

| Page | Initial actor | Body connection |
| --- | --- | --- |
| `realjelly.html` | G / Anchor | Nerve activity, firmness and fullness snapshot; bounded visible membrane breath |
| `thinkjelly.html` | G / Anchor | Nerve activity, firmness and warmth snapshot; bounded membrane breath |
| `jellyjar.html` | J / Glint | Motion/firmness snapshot; reversible squeeze of visible gel |
| `wetbell.html` | F1 / Glass | Local material snapshot; bounded scaling and glow |
| `bodies.html?sp=glass` | F1 / Glass | Charge/energy snapshot; bounded scaling and glow; other species unchanged |
| `colloquy.html` | G / Anchor | Stable G/J/F1/F2/F3 actor binding; only the selected actor responds |
| `jellystudio.html` | G / Anchor | Prepared voice through the existing master; visible bell response |

These are creative mappings, not a claim that the displayed body is the anatomical airway. Body colour is captured once at preparation. Playback drives a presentation layer; it does not fire the nervous system, inject physics forces, or record itself as a new gesture. This preserves the existing instruments while the missing live articulatory patch remains a separate branch of work.

Real/Think/Bodies voice entry starts the existing visible body. Studio voice entry reveals the sampler without starting its transport; **LOAD & PLAY** loads its existing clips when wanted. Colloquy's sound module keeps its AudioContext private, so its voice uses a separate context in this checkpoint. Ensemble synchronization with the gallery soundtrack is not established.

## Delivery controls

- **Speak:** dictionary pronunciation, engine prosody and a pace multiplier.
- **Joke:** write `setup | punchline`; the pause field sets the gap in the engine phrase plan. This does not establish whether a joke lands.
- **Sing:** one note per syllable, with intervals relative to the character's pitch. `0:1 4:1 7:2` means root for one beat, four semitones up for one beat, seven up for two beats. The pattern repeats. `~` extends the preceding vowel onto another note; the original word's coda waits until the chain ends.
- **Rap:** continuous-breath syllables on straight eighths, swung eighths, or triplets. Prose punctuation does not insert a rest. This is a physical, pitched rap prototype, not a trained rap-performance model.

The planner adds preroll for onset consonants. It records both requested and planned nucleus times, warns on drift over 20 ms and on short slots, and rejects overlapping phoneme sequences. Planned phone times are **not measured acoustic alignment**. The independent dense fixture still moves a vowel by 41.3 ms and produces the corresponding warning.

Limits: English, 240 characters, at most 32 sung/rap syllables, at most 40 seconds of planned content, 50–180 BPM. The output includes a 0.6-second release tail. Rendering supports 44.1 or 48 kHz; an AudioContext at another device rate resamples during playback. No per-syllable `setTimeout` or animation-frame audio scheduler is used.

## What is saved

The WAV is a dry mono 16-bit vocal, at the actual take sample rate. The take record contains the immutable score, actor/profile revisions, engine revision, PCM hash, signal measurements, planned phones, notes and telemetry. Its PCM hash identifies float samples **before** WAV quantization. The independent decoder check measures the expected quantization bound.

Existing page music, reverbs and mastering are separate from this dry vocal. Studio's existing mix/stem export does not include the new take. The take record does not capture complete physics, touch or camera replay. Do not describe this checkpoint as an audiovisual film exporter. Import the vocal WAV into an editor for the current film/music-video workflow.

## Listen before claiming quality

Open `http://localhost:8000/bonus/jelly-voice/listen.html` for five shuffled, unnamed clips. Enter what you hear before revealing the words, then save the listening notes. Nothing is submitted to a server. Two clips use the same sentence with different actors. This separates actual transcription evidence from the fact that their PCM hashes differ.

Recreate the fixtures:

```sh
node tests/jelly-voice/render-samples.mjs
```

No new human transcription, naturalness score, ASR improvement or trained-voice claim is made here. The previous handoff's measurements remain reported evidence about another artifact, not results of this build.

## Independent verification

```sh
node tests/jelly-voice/critic-core.mjs
node tests/jelly-voice/critic-timing.mjs
node tests/jelly-voice/critic-browser.mjs
```

Core: **20 passing checks** on actual WASM synthesis, both sample rates, identity, invalid input, WAV decoding, and explicitly labelled Worker/clock doubles. Timing: **10 passing checks**, including held-out melisma and overlapping-phrase cases. All seven HTML modules parse. See `../../tests/jelly-voice/critique.json` for exact inspected hashes and limits. The browser suite uses Playwright, owns its read-only local server, and exits 2 when browser startup is blocked; it does not award a pass.

The separate runtime recovery pass also found byte-identical PCM across 128/1024/4096-frame host blocks and with telemetry enabled/disabled. Its provenance and measured results are in `chimera/manifest.json` and `chimera/verification-summary.json`. The two test passes have different fixtures and must not be combined into one perceptual benchmark.

## Training and production speech

These five profiles select anatomy, pitch and source controls; no neural training occurred. Training a better production voice is a different renderer behind the same actor identity and take contract.

1. **Choose the voice source.** Audition a recorded performer, usable speech model, or singing voicebank on held-out material. Preserve the exact model/voice revision and permissions with each take. A visually different jelly does not require retraining its voice.
2. **Calibrate the controller separately.** Record body features and desired expression while listening to a fixed take. Fit a small bounded mapping for breath, brightness and expression. Keep consonant timing protected. Do not train text-to-speech on audio-driven body motion as though it were independent performance intent.
3. **Prepare model-specific data.** Speech needs clean takes and accurate transcripts. Singing needs lyrics/phones, note pitch, duration and timing labels expected by the selected trainer. Rap needs actual performed syllable placement, stress and breath timing. Keep recording sessions and passages separate between training and evaluation. There is no universal amount of audio or interchangeable voice embedding across these models.
4. **Render and align.** A production renderer should return immutable PCM plus measured or verified alignment. Reuse the present actor IDs, score records and page adapters. Keep renderer failure explicit; do not silently switch voices. Store model revision, sample rate, alignment provenance and PCM hash.
5. **Gate promotion on people hearing it.** Compare shuffled takes on unheard sentences, consonant clusters, punchlines, melodic intervals and dense bars. Record actual transcriptions and specific defects before choosing a model or tuning the material mapping.

The next production slice is one actor in speech, song and rap with verified alignment and a locked vocal stem, followed by a second independently identifiable character. Multivoice film clocks, a Studio vocal lane, complete motion/camera replay and custom model training remain separate unfinished work.

## Files and reproducibility

`cast.mjs` holds actor identity. `score.mjs` validates and compiles delivery. `worker.mjs` verifies pinned asset hashes and runs `render.mjs` outside the display thread. `performance.mjs` owns playback, frame sampling and WAV encoding. `panel.js` is shared UI inside a shadow root. `adapters.js` supplies bounded, origin-tagged presentation state.

`genome.yaml`, `OLOG.md` and `SCION.md` record the design, invariants and run boundaries. `chimera/build-runtime.sh` rebuilds the exact upstream engine using the recorded toolchain. Engine and dictionary redistribution notices are retained. A clean rebuild may use different compiler bytes if a different toolchain is deliberately selected; update the manifest and worker pins together and rerun the critic.

#jelly-cast #speaking-film #chimera-voice #locked-takes #scion-swarm
