// Playback, export and body response read the same prepared take.
export function measurePCM(pcm) {
  let peak = 0, sum = 0;
  for (const x of pcm) {
    if (!Number.isFinite(x)) throw new Error('The renderer returned non-finite audio.');
    peak = Math.max(peak, Math.abs(x)); sum += x * x;
  }
  return {peak, rms: Math.sqrt(sum / Math.max(1, pcm.length)), frames: pcm.length};
}
export function envelope(pcm, sampleRate, hz = 100) {
  const step = Math.max(1, Math.round(sampleRate / hz)), frames = [];
  for (let i = 0; i < pcm.length; i += step) {
    let sum = 0, end = Math.min(pcm.length, i + step);
    for (let j = i; j < end; j++) sum += pcm[j] * pcm[j];
    frames.push(Math.sqrt(sum / (end - i)));
  }
  return {step, values: Float32Array.from(frames)};
}
function previous(items, time, key) {
  let low = 0, high = items.length - 1, found = -1;
  while (low <= high) { const mid = (low + high) >>> 1; if (items[mid][key] <= time) { found = mid; low = mid + 1; } else high = mid - 1; }
  return found < 0 ? null : items[found];
}
export function frameAt(take, time) {
  const active = time >= 0 && time < take.duration;
  const t = Math.max(0, Math.min(take.duration, time));
  const rms = active ? (take.envelope.values[Math.floor(t * take.sampleRate / take.envelope.step)] ?? 0) : 0;
  const tele = previous(take.telemetry, t, 'clock');
  const segment = previous(take.segments, t, 't0');
  return {active, actorId: take.score.actorId, t, duration: take.duration, rms, level: Math.min(1, rms * 8), f0: tele?.f0 ?? 0, phone: segment && t < segment.t1 ? segment.ipa : '', mode: take.score.mode, origin: 'voice-playback'};
}
export function encodeWav(take) {
  const {pcm, sampleRate} = take;
  const buffer = new ArrayBuffer(44 + pcm.length * 2), view = new DataView(buffer);
  const str = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  str(0, 'RIFF'); view.setUint32(4, 36 + pcm.length * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  str(36, 'data'); view.setUint32(40, pcm.length * 2, true);
  for (let i = 0; i < pcm.length; i++) { const v = Math.max(-1, Math.min(1, pcm[i])); view.setInt16(44 + i * 2, Math.round(v * (v < 0 ? 32768 : 32767)), true); }
  return buffer;
}
export class TakePlayer {
  constructor(context, destination, {onFrame = () => {}, onEnd = () => {}} = {}) {
    this.context = context; this.destination = destination ?? context.destination;
    this.onFrame = onFrame; this.onEnd = onEnd; this.source = null; this.raf = 0; this.token = 0;
  }
  play(take) {
    this.stop();
    const token = ++this.token, buffer = this.context.createBuffer(1, take.pcm.length, take.sampleRate);
    buffer.copyToChannel(take.pcm, 0);
    const source = this.context.createBufferSource(); source.buffer = buffer; source.connect(this.destination);
    this.source = source; this.take = take; this.start = this.context.currentTime + .06;
    source.onended = () => { if (token !== this.token) return; this.source = null; source.disconnect(); cancelAnimationFrame(this.raf); this.onFrame(frameAt(take, take.duration)); this.onEnd(); };
    const update = () => { if (token !== this.token || !this.source) return; this.onFrame(frameAt(take, this.context.currentTime - this.start)); this.raf = requestAnimationFrame(update); };
    source.start(this.start); update();
    return this.start;
  }
  stop() {
    ++this.token; cancelAnimationFrame(this.raf);
    if (this.source) { this.source.onended = null; try { this.source.stop(); } catch {} this.source.disconnect(); this.source = null; }
    if (this.take) this.onFrame(frameAt(this.take, this.take.duration));
  }
}
