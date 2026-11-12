# Pinned Chimera runtime

This is a fresh build of **unmodified upstream Chimera** at `e33221d006f44c78849210eb29dd1eb9755dc78e`, with a small Worker/browser/Node host adapter. It does not contain the earlier Speaking Film material or closure-guard patch.

## Files and licenses

`chimera.wasm` is the Rust engine; `chimera.mjs` is the new adapter; `wire.mjs` is the exact upstream TypeScript serializer with annotations erased; `cmudict.txt.gz` is the upstream pronunciation dictionary. Keep `CHIMERA-LICENSE.txt` (MIT) and `CMUDICT-LICENSE.txt` when redistributing. `manifest.json` records hashes and build provenance. Upstream: https://github.com/jamesondh/chimera-vocal-synth/tree/e33221d006f44c78849210eb29dd1eb9755dc78e.

## Worker API

```js
import { initChimera } from './chimera.mjs';
const engine = await initChimera();
await engine.loadDictionary();
const body = { female: 0, child: 0 };
const plan = engine.planSpeech('The jelly has a voice.', {
  body, t0: 0, f0: 120, rate: 1, accent: 0.12,
});
const take = engine.renderPlan(plan, {
  body, source: { breathiness: 0.1, roughness: 0.05, drift: 0 },
  sampleRate: 48000, telemetryHz: 30,
});
// take: {pcm: Float32Array, sampleRate, duration, offset, segments, telemetry}
```

Both initializers accept URL or byte-buffer input; the WASM initializer also accepts WebAssembly.Module. The defaults resolve assets beside this module. The dictionary must finish loading before dictionary-backed speech is claimed. Planning and rendering are synchronous once loaded; use a Worker and enforce text, duration and cancellation budgets in its host.

`engine.phrases(text)` exposes phrases with `segments,intonation,pause,words`. Change a setup phrase's `pause` in seconds, then call `engine.planPhrases(phrases,options)` for a joke delivery. `engine.syllables(lyrics)` returns onset/nucleus/coda syllables. `engine.planSong(notes,{body,bpm,t0,vibrato})` accepts `{syl,midi,beats}[]`; vibrato is **cents**. A rap prototype can use short beat lengths, zero vibrato and a narrow pitch contour. It is not a trained rap model.

Use the same body blend for planning and rendering. Set speech pitch in planning options because scheduled pitch gestures override source f0. Plans are `{gestures,segments,end}`, all times in seconds. `renderPlan` options default to `sampleRate:48000`, `body:{female:0,child:0}`, `source:{}`, `lead:0`, `tail:0.35`, `blockSize:128`, `telemetryHz:30`. It returns exact engine samples without normalization; telemetry arrays are copied and snapshots carry voice-clock timestamps. RMS describes the interval since the preceding snapshot.

For injected controls, create `voice=engine.createVoice({sampleRate,body,source})`; use `voice.schedule(plan.gestures,{lead:0,replace:true})`, `voice.render(frames,blockSize)`, `voice.state()`, `voice.setSource(values)`, `voice.setArtic(values)`, and `voice.dispose()`. Split renders at event sample positions. Host blocks are limited to 4096 samples; the adapter splits total renders. More than 4000 gestures raises an error.

## Timing and ranges

Song `t0` locates the first vowel's beat; onset consonants and preparation precede it. Inspect `min(g.t0-g.rampIn)` and add enough preroll to avoid truncation. The singer tries to preserve a 50 ms vowel while shrinking consonants no shorter than 12 ms each. If the consonants still cannot fit, a 20 ms vowel floor can push the next vowel late. Check planned vowel timestamps against the intended beat grid and warn on dense syllables; text limits alone do not prove timing fidelity.

Upstream UI ranges (`src/ui/components/VoiceControls.tsx`): pressure 2–22 cmH₂O; tension, brightness, breathiness, roughness and fry 0–1; pitch 40–1100 Hz; vibrato depth 0–120 cents. Source defaults (`crates/chimera/src/voice/human_voice.rs`): pressure 8, tension .5, brightness .25, breathiness .15, roughness .1, fry 0, f0 110 Hz. These are UI ranges, not a measured guarantee of pleasant speech throughout the range.

## Build and executed checks

Run `bash build-runtime.sh` with Git, Node 24 and rustup available. It checks out the exact pin, installs Rust 1.99.1 with wasm32-unknown-unknown, and builds using the upstream lockfile. The run compiler was `1.99.1 (58cf8f9c3 2026-10-13)`, full commit `58cf8f9c35b355199727627d07ae34a4e2846d67`, LLVM 23.1.1. The exact command was `cargo build --locked --release --target wasm32-unknown-unknown -p chimera-wasm`. Upstream source was clean after the build.

`verification-summary.json` records actual Node renders of speech, song and beat-scheduled rap, finite levels, block independence, source-control causality and 44.1 kHz behavior. Speech PCM matched byte-for-byte across 128/1024/4096-frame host blocks and with telemetry enabled/disabled. The song reaches upstream's 0.75 limiter envelope. These checks do not establish naturalness or intelligibility. This recovery pass did not audition audio, run ASR, or test browser playback; the integration must report its own checks separately.
