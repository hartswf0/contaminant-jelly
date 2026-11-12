/** Small Worker/browser/Node adapter for unmodified Chimera e33221d0, MIT.
 * This adapter does not contain the unrecovered Speaking Film material patch.
 * Planning allocates; call it in a Worker or outside the real-time audio callback.
 */
import { writeGestures, fromUtf8, CONTROL_KEYS } from './wire.mjs';

export const CHIMERA_REVISION = 'e33221d006f44c78849210eb29dd1eb9755dc78e';
export const DEFAULT_BODY = Object.freeze({ female: 0, child: 0 });
const SOURCE_KEYS = ['f0', 'glide', 'pressure', 'breathiness', 'tension', 'fry', 'roughness', 'vibratoDepth', 'vibratoRate', 'drift', 'voiced', 'brightness'];
const enc = new TextEncoder();
const dec = new TextDecoder();

async function bytesOf(source) {
  if (source instanceof ArrayBuffer) return new Uint8Array(source);
  if (ArrayBuffer.isView(source)) return new Uint8Array(source.buffer, source.byteOffset, source.byteLength);
  const response = await fetch(source);
  if (!response.ok) throw new Error(`Chimera asset HTTP ${response.status}: ${source}`);
  return new Uint8Array(await response.arrayBuffer());
}

export async function initChimera(source = new URL('./chimera.wasm', import.meta.url)) {
  const module = source instanceof WebAssembly.Module ? source : await WebAssembly.compile(await bytesOf(source));
  if (WebAssembly.Module.imports(module).length) throw new Error('Chimera module unexpectedly needs imports');
  const x = new WebAssembly.Instance(module, {}).exports;
  if (x.chimera_layout_version() !== 1 || x.chimera_gesture_record_size() !== 272) throw new Error('Incompatible Chimera record layout');

  function call(fn, args = {}) {
    const bytes = enc.encode(JSON.stringify({ ...args, fn }));
    const p = x.chimera_alloc(bytes.length);
    let status;
    try {
      new Uint8Array(x.memory.buffer, p, bytes.length).set(bytes);
      status = x.chimera_call(p, bytes.length);
    } finally {
      x.chimera_free(p, bytes.length);
    }
    const result = JSON.parse(dec.decode(new Uint8Array(x.memory.buffer, x.chimera_result_ptr(), x.chimera_result_len())));
    if (status !== 0) throw new Error(`Chimera ${fn}: ${result.error}`);
    return result;
  }

  const runtime = {
    module,
    call,
    dictionaryLoaded: false,
    setDictionaryText(text) {
      call('g2pLoad', { text });
      this.dictionaryLoaded = true;
    },
    async loadDictionary(source = new URL('./cmudict.txt.gz', import.meta.url)) {
      const bytes = await bytesOf(source);
      const text = bytes[0] === 0x1f && bytes[1] === 0x8b
        ? await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text()
        : dec.decode(bytes);
      this.setDictionaryText(text);
    },
    phrases(text) { return call('g2pPhrases', { text }); },
    syllables(text) { return call('lyricsToSyllables', { text }); },
    planSpeech(text, options = {}) {
      return call('planPhrases', { phrases: this.phrases(text), options: { body: DEFAULT_BODY, t0: 0, ...options } });
    },
    planPhrases(phrases, options = {}) {
      return call('planPhrases', { phrases, options: { body: DEFAULT_BODY, t0: 0, ...options } });
    },
    planSong(notes, options = {}) {
      return call('planSong', { notes, options: { body: DEFAULT_BODY, bpm: 120, t0: 0, vibrato: 0, ...options } });
    },
    createVoice(options = {}) { return new ChimeraVoice(module, options); },
    renderPlan(plan, options = {}) {
      const { sampleRate = 48000, body = DEFAULT_BODY, source = {}, lead = 0, tail = 0.35, blockSize = 128, telemetryHz = 30 } = options;
      if (!Number.isFinite(plan.end) || plan.end < 0 || !Number.isFinite(lead) || lead < 0 || !Number.isFinite(tail) || tail < 0) throw new Error('Invalid render duration');
      const voice = new ChimeraVoice(module, { sampleRate, body, source });
      try {
        const offset = voice.schedule(plan.gestures, { lead });
        const frames = Math.ceil((offset + plan.end + tail) * sampleRate);
        const { pcm, telemetry } = voice.renderWithTelemetry(frames, { blockSize, telemetryHz });
        return { pcm, sampleRate, offset, duration: pcm.length / sampleRate, telemetry, segments: plan.segments.map(s => ({ ...s, t0: s.t0 + offset, t1: s.t1 + offset })) };
      } finally { voice.dispose(); }
    },
  };
  return runtime;
}

export class ChimeraVoice {
  constructor(module, { sampleRate = 48000, body = DEFAULT_BODY, source = {} } = {}) {
    if (!Number.isFinite(sampleRate) || sampleRate < 8000 || sampleRate > 192000) throw new Error('Unsupported sample rate');
    this.x = new WebAssembly.Instance(module, {}).exports;
    this.h = this.x.engine_new(sampleRate);
    this.sampleRate = sampleRate;
    this.setBody(body);
    this.setSource(source);
  }
  live() { if (!this.h) throw new Error('Voice is disposed'); }
  get clock() { this.live(); return this.x.engine_clock(this.h); }
  setBody({ female, child }) {
    this.live();
    if (![female, child].every(v => Number.isFinite(v) && v >= 0 && v <= 1)) throw new Error('Body blend must be within 0..1');
    this.x.engine_set_body(this.h, female, child);
  }
  setSource(values) {
    this.live();
    const v = new Float64Array(this.x.memory.buffer, this.x.engine_values(this.h), 32).fill(NaN);
    for (const [key, value] of Object.entries(values)) {
      const i = SOURCE_KEYS.indexOf(key);
      if (i < 0 || (typeof value !== 'boolean' && !Number.isFinite(value))) throw new Error(`Invalid source control: ${key}`);
      v[i] = typeof value === 'boolean' ? Number(value) : value;
    }
    this.x.engine_set_source(this.h);
  }
  setArtic(values, tipFree) {
    this.live();
    const v = new Float64Array(this.x.memory.buffer, this.x.engine_values(this.h), 32).fill(NaN);
    for (const [key, value] of Object.entries(values)) {
      const i = CONTROL_KEYS.slice(0, 17).indexOf(key);
      if (i < 0 || !Number.isFinite(value)) throw new Error(`Invalid articulation control: ${key}`);
      v[i] = value;
    }
    this.x.engine_set_artic(this.h, tipFree === undefined ? 2 : Number(Boolean(tipFree)));
  }
  schedule(gestures, { lead = 0, replace = true } = {}) {
    this.live();
    if (gestures.length > 4000) throw new Error('Plan exceeds Chimera 4000-gesture capacity');
    const n = writeGestures(this.x.memory.buffer, this.x.engine_records(this.h), gestures, 4000);
    return this.x.engine_schedule(this.h, n, lead, Number(replace));
  }
  stop() { this.live(); this.x.engine_stop_speech(this.h); }
  setGate(level) { this.live(); this.x.engine_set_gate(this.h, level); }
  release(tag) { this.live(); this.x.engine_release(this.h, tag); }
  render(frames, blockSize = 128) { return this.renderWithTelemetry(frames, { blockSize, telemetryHz: 0 }).pcm; }
  renderWithTelemetry(frames, { blockSize = 128, telemetryHz = 30 } = {}) {
    this.live();
    if (!Number.isSafeInteger(frames) || frames < 0 || frames > 2 ** 28) throw new Error('Invalid PCM frame count');
    if (!Number.isInteger(blockSize) || blockSize < 1 || blockSize > 4096) throw new Error('Render block must be 1..4096 frames');
    const pcm = new Float32Array(frames), telemetry = [];
    const spacing = telemetryHz > 0 ? this.sampleRate / telemetryHz : Infinity;
    let nextTelemetry = 0;
    for (let i = 0; i < frames; i += blockSize) {
      const n = Math.min(blockSize, frames - i);
      const p = this.x.engine_render(this.h, n);
      pcm.set(new Float32Array(this.x.memory.buffer, p, n), i);
      if (i + n >= nextTelemetry && telemetryHz > 0) {
        telemetry.push(this.state());
        nextTelemetry += spacing;
      }
    }
    return { pcm, telemetry };
  }
  state() {
    this.live();
    const p = this.x.engine_telemetry(this.h);
    const head = Array.from(new Float64Array(this.x.memory.buffer, p, 16));
    const [phLen, orLen, velumPort, f0, voicing, pLung, outRms, noiseLevel, noiseNode, gate, clock, nArtic, nPh, nOr, nScope, nActive] = head;
    const all = new Float64Array(this.x.memory.buffer, p, 16 + nArtic + 3 * (nPh + nOr) + 2 * nScope);
    let o = 16;
    const take = n => Float32Array.from(all.subarray(o, (o += n)));
    const artic = take(nArtic), phAreas = take(nPh), orAreas = take(nOr);
    const pressureRms = take(nPh + nOr), flow = take(nPh + nOr), glottalArea = take(nScope), glottalFlow = take(nScope);
    const labelBytes = new Uint8Array(this.x.memory.buffer, this.x.engine_tele_labels(this.h), 100), active = [];
    for (let i = 0; i < nActive; i++) active.push(fromUtf8(labelBytes.subarray(i * 25 + 1, i * 25 + 1 + labelBytes[i * 25])));
    return { clock, f0, voicing, outRms, gate, phLen, orLen, velumPort, pLung, noiseLevel, noiseNode, artic, phAreas, orAreas, pressureRms, flow, glottalArea, glottalFlow, active };
  }
  dispose() { if (this.h) { this.x.engine_free(this.h); this.h = 0; } }
}
