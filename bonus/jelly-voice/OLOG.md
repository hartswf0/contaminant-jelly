# Jelly Cast — theory before implementation

Input distinction: F := ◻(operator handoff + pinned jelly source + pinned Chimera source).
Revision: jc-theory-1, created before implementation. TTL 2.

## Distinctions and morphisms

Source evidence is explicit. Confidence 1.0 below means direct presence in inspected source, not probability of audible success. Proposed behavior has no fabricated confidence value.

| Typed distinction | Provenance | Evidence / confidence |
| --- | --- | --- |
| ◻(page), ◻(body state), ◻(gesture) | Jelly repo e393e9f | source-inspected / 1.0 |
| ◻(actor G, J, F1, F2, F3) | Colloquy sim/stage | source-inspected / 1.0 |
| ◻(phoneme plan), ◻(song plan), ◻(PCM) | Chimera e33221d | source-inspected / 1.0 |
| ◻(voice profile), ◻(take), ◻(body adapter) | this design | proposed / unmeasured |
| ◻(pleasantness), ◻(intelligibility) | listeners | unknown; no listener in this run |

{◻(text), ◻(mode), ◻(notes), ◻(tempo), ◻(voice profile)}
→ [validates and freezes] → ◻(score)
→ [plans in pinned engine] → ◻(gestural plan)
→ [renders on sample clock] → ◻(immutable PCM take).

◻(actor ID) → [resolves] → ◻(voice profile revision).
◻(actor ID) → [binds independently] → ◻(body adapter).
{◻(take), ◻(AudioContext time)} → [samples] → ◻(performance frame)
→ [applies bounded visual response] → ◻(existing body).
◻(take) → [schedules once] → ◻(audible playback).
◻(take) → [encodes] → ◻(WAV).

## Composition and closure obligations

1. Score → renderer → PCM → WAV decode and Score → renderer → PCM must agree to the WAV quantization bound. Never rerender an export using changed controls.
2. Actor → profile and Actor → a different body → same profile must resolve the same profile ID and revision. Recasting must not rewrite identity.
3. Audio start + elapsed sample count → take position and AudioContext time − start → take position agree within one output sample after rounding. A display frame is a sample of this state, not an audio scheduler.
4. Stop → cancel pending playback → silence must also invalidate an asynchronous render result; a late worker reply cannot restart a stopped phrase.

These are test obligations, not completed proofs. Scope: identity, timing, PCM integrity. Body physics replay is not claimed bit-identical; independent perceptual paths need not commute.

## Assumption ledger

- <safe> Existing pages remain vanilla modules. All adapters are opt-in controls with no automatic speech on load.
- <safe> CMUdict is English; the baseline is an English physical voice.
- <uncertain> Voice quality, character distinction, singing pleasantness, and mobile render cost require measurement or listeners.
- <uncertain> The reported custom Speaking Film engine may improve this baseline; its patch is missing here.
- <requires-user-decision> A specific performer or voicebank for bespoke training, when that stage is reached.

## Operational and failure calculus

- <valid score> [transforms_into] <bounded prepared take>.
- <worker> [performs] <planning and synthesis>.
- <user gesture> [enables] <AudioContext resume and playback>.
- <missing WASM or dictionary> [blocks] <render>; report the resource error, keep existing page usable.
- <invalid note, empty lyric, oversubscribed score, excessive duration> [blocks] <render>; show the exact invalid field.
- <stop or replacement generation> [blocks] <stale result playback>; discard that result.
- <renderer failure or timeout> [blocks] <take adoption>; terminate/recreate worker, keep last valid take available.
- <body adapter failure> [blocks] <visual feedback only>; surface the error without stopping already scheduled PCM.

## Change tests specified before code

1. Stall graphics for 800 ms during a prepared phrase. Audio scheduling must remain a single buffer start, and the completed buffer remains unchanged. On return, visuals read current audio time, not a queue of missed syllables.
2. Rebind the same actor to another body. Profile identity and cached take provenance remain equal; only the adapter changes.
3. Change sample rate between 44.1 and 48 kHz. WAV header, duration, and plan time conversion use the actual renderer rate. Equality of PCM across rates is not required.
4. Stop while a worker is rendering. A late result must never auto-play.

## Theory/artifact mapping

Score validation and immutable cast registry hold identity. The worker owns synthesis time. The take owns PCM and plan metadata. Playback owns AudioContext start time. WAV encoding reads the take. Body adapters preserve page controls. Separate tests exercise invalid input, cancellation, rate changes, and replay.

## Deceptive stepping stone and protected strength

The missing live membrane patch suggests a useful separate branch: prepare a locked vocal take, then let different bodies perform it. This preserves exact dialogue and singing during expensive film rendering. It does not replace a future live articulatory instrument. Preserve both branches; do not silently call filtered playback an anatomical airway.

## Residual human theory

A maintainer holds actor continuity and the intended material mapping. A listener judges words, character, comic timing, musical phrasing, and whether the body seems to cause the sound. Neither numerical signal checks nor this diagram can certify those judgments.
