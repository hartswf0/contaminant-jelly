import {compileScore, scoreKey, sha256, RENDERER_REVISION} from './score.mjs';
import {measurePCM, envelope} from './performance.mjs';
import {CHIMERA_REVISION} from './chimera/chimera.mjs';

export async function renderTake(runtime, score, sampleRate = 48000) {
  if (![44100, 48000].includes(sampleRate)) throw new Error('Take rendering supports 44100 or 48000 Hz.');
  const compiled = compileScore(runtime, score);
  const take = runtime.renderPlan(compiled.plan, {sampleRate, body: compiled.body, source: compiled.source, tail: .6, telemetryHz: 50});
  const raw = measurePCM(take.pcm);
  if (raw.peak < 1e-7) throw new Error('The engine returned a silent take.');
  // Headroom only: preserve dynamics; never silently hard-clip a take.
  const gain = Math.min(1, .92 / raw.peak);
  if (gain < 1) for (let i = 0; i < take.pcm.length; i++) take.pcm[i] *= gain;
  const signal = measurePCM(take.pcm);
  const pcmHash = await sha256(take.pcm.buffer);
  return {...take, score, scoreHash: await scoreKey(score), pcmHash, renderer_revision: RENDERER_REVISION, engine_revision: CHIMERA_REVISION,
    notes: compiled.notes, warnings: compiled.warnings, preroll: compiled.preroll,
    telemetry: take.telemetry.map(({clock, f0, outRms, velumPort, artic}) => ({clock, f0, outRms, velumPort, jaw: artic[0], lipAp: artic[7]})),
    envelope: envelope(take.pcm, sampleRate), signal: {...signal, rawPeak: raw.peak, attenuation: gain},
    alignmentKind: 'engine-planned-phone-times-not-measured-alignment',
  };
}
