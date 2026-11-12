export class VoiceRenderer {
  constructor() { this.worker = null; this.pending = null; this.serial = 0; }
  cancel() {
    if (this.pending) { clearTimeout(this.pending.timer); this.pending.reject(new DOMException('Render cancelled.', 'AbortError')); this.pending = null; }
    this.worker?.terminate(); this.worker = null;
  }
  render(score, {sampleRate = 48000, onStatus = () => {}} = {}) {
    this.cancel();
    const id = ++this.serial, worker = new Worker(new URL('./worker.mjs', import.meta.url), {type: 'module'});
    this.worker = worker;
    return new Promise((resolve, reject) => {
      const finish = (error, take) => {
        if (!this.pending || this.pending.id !== id) return;
        clearTimeout(this.pending.timer); this.pending = null; worker.terminate(); if (this.worker === worker) this.worker = null;
        error ? reject(error) : resolve(take);
      };
      this.pending = {id, reject, timer: setTimeout(() => finish(new Error('Voice preparation exceeded 90 seconds. Try a shorter phrase.')), 90000)};
      worker.onmessage = ({data}) => { if (data.id !== id) return; if (data.error) finish(new Error(data.error)); else if (data.take) finish(null, data.take); else onStatus(data.status); };
      worker.onerror = event => finish(new Error(event.message || 'The voice worker could not start.'));
      worker.postMessage({id, score, sampleRate});
    });
  }
}
