// THE COLLOQUY OF MOBILES · sound. Electronic chirps, as in 1968, but gentle: every voice is read from the machine.
//   female tone   each female's tone emitter, gated by her partner's flashing lamp u (phase-locked, stage 3), steady under B (4–5)
//   male reply    the satisfaction tone at F = 1 (stage 6): a short two-step chirp, pitched by which vane (C high, D low)
//   reinforcement the female hears it while lit and consolidates (stage 7): two soft blips over a quiet major chord
//   drive hum     a low hum whose level and brightness follow the mean urgency of all five drives
// The same voice graph runs live (AudioContext) and offline (OfflineAudioContext) from a recorded trace, so the film has the page's sound.
const FEM = [523.25, 659.25, 783.99], MAL = [196, 246.94];

export function makeVoices(ctx, dest) {
  const master = ctx.createGain(); master.gain.value = .9;
  const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -20; comp.ratio.value = 3; comp.attack.value = .01; comp.release.value = .25;
  master.connect(comp); comp.connect(dest);
  // a small room: a generated decaying-noise impulse (deterministic)
  const rev = ctx.createConvolver(), len = Math.floor(ctx.sampleRate * 2.2), ir = ctx.createBuffer(2, len, ctx.sampleRate); let s = 12345;
  for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < len; i++) { s = (s * 16807) % 2147483647; d[i] = (s / 2147483647 * 2 - 1) * Math.pow(1 - i / len, 3.2); } }
  rev.buffer = ir; const wet = ctx.createGain(); wet.gain.value = .28; rev.connect(wet); wet.connect(master);
  const bed = ctx.createGain(); bed.connect(master); bed.connect(rev); const bus = ctx.createGain(); bus.connect(bed);
  const fem = FEM.map((f0, i) => { const o = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain(), pan = ctx.createStereoPanner(); o.type = 'triangle'; o.frequency.value = f0; o2.type = 'sine'; o2.frequency.value = f0 * 2.003;
    const g2 = ctx.createGain(); g2.gain.value = .25; o2.connect(g2); g2.connect(g); o.connect(g); g.gain.value = 0; pan.pan.value = [-.6, .6, 0][i]; g.connect(pan); pan.connect(bus); o.start(); o2.start(); return {o, g}; });
  const buzz = MAL.map((f0, i) => { const o = ctx.createOscillator(), lp = ctx.createBiquadFilter(), g = ctx.createGain(), pan = ctx.createStereoPanner(); o.type = 'sawtooth'; o.frequency.value = f0; lp.type = 'lowpass'; lp.frequency.value = 700; lp.Q.value = 2; g.gain.value = 0; pan.pan.value = i ? .35 : -.35;
    o.connect(lp); lp.connect(g); g.connect(pan); pan.connect(bus); o.start(); return {o, g, lp}; });
  const hum = (() => { const a = ctx.createOscillator(), b = ctx.createOscillator(), lp = ctx.createBiquadFilter(), g = ctx.createGain(); a.type = b.type = 'sawtooth'; a.frequency.value = 55; b.frequency.value = 55.37; lp.type = 'lowpass'; lp.frequency.value = 160; g.gain.value = 0;
    a.connect(lp); b.connect(lp); lp.connect(g); g.connect(bed); a.start(); b.start(); return {g, lp}; })();
  const set = (p, v, t, tc = .012) => p.setTargetAtTime(v, t, tc);
  function chirp(t, f0, f1, dur, vol, type = 'sine', pan = 0) { const o = ctx.createOscillator(), g = ctx.createGain(), p = ctx.createStereoPanner(); o.type = type; p.pan.value = pan;
    o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + .006); g.gain.exponentialRampToValueAtTime(.0001, t + dur + .05);
    o.connect(g); g.connect(p); p.connect(bus); o.start(t); o.stop(t + dur + .08); }
  function chord(t, f, vol, dur, pan) { const o = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain(), p = ctx.createStereoPanner(); o.type = 'triangle'; o2.type = 'sine'; o.frequency.value = f; o2.frequency.value = f * 1.003; p.pan.value = pan;
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + .015); g.gain.exponentialRampToValueAtTime(vol * .35, t + .35); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
    o.connect(g); o2.connect(g); g.connect(p); p.connect(bus); o.start(t); o2.start(t); o.stop(t + dur + .05); o2.stop(t + dur + .05); }
  return {
    // st: {fem: [{tone, gate, stage}], mal: [{B, F}], urgency}
    frame(t, st) {
      st.fem.forEach((f, i) => set(fem[i].g.gain, f.tone > 0 ? (f.gate ? .026 * f.tone + .006 : .002) : 0, t, f.stage === 3 ? .006 : .03));
      st.mal.forEach((m, i) => { set(buzz[i].g.gain, m.B ? .009 : 0, t, .08); set(buzz[i].lp.frequency, m.B ? 900 : 400, t, .2); });
      set(hum.g.gain, .004 + st.urgency * .02, t, .6);
      set(bed.gain, 1 - .82 * Math.min(1, (st.ambient || 0) / .8), t, .5); set(hum.lp.frequency, 120 + st.urgency * 260, t, .6);   // the lit room is quiet: the photocells lose contrast and the whole society hushes
    },
    event(t, ev) {
      const fi = ev.f ? +String(ev.f).slice(1) - 1 : 0, mi = ev.m === 'J' ? 1 : 0;
      if (ev.kind === 'reinforce') { const hi = ev.vane === 'C';
        // F = 1: the satisfaction chord, well above the bed (a major triad on his own pitch, struck and left to ring)
        for (const [k, r] of [[0, 2], [1, 2.52], [2, 3], [3, 4]]) chord(t + k * .012, MAL[mi] * r, .2 - k * .025, 1.5, mi ? .3 : -.3); chirp(t, MAL[mi] * (hi ? 4 : 3), MAL[mi] * (hi ? 8 : 6), .09, .09, 'square', mi ? .3 : -.3); chirp(t + .13, MAL[mi] * (hi ? 6 : 4.5), MAL[mi] * (hi ? 12 : 9), .11, .07, 'square', mi ? .3 : -.3); }
      else if (ev.kind === 'memory') { for (const [k, r] of [[0, 1], [1, 1.25], [2, 1.5]]) chirp(t + .3 + k * .03, FEM[fi] * r / 2, FEM[fi] * r / 2 * 1.002, .9, .022, 'sine', [-.6, .6, 0][fi]);   // the satisfaction chord
       chirp(t + .32, FEM[fi] * 2, FEM[fi] * 2.02, .05, .05, 'sine', [-.6, .6, 0][fi]); chirp(t + .44, FEM[fi] * 2.5, FEM[fi] * 2.52, .07, .045, 'sine', [-.6, .6, 0][fi]); }
      else if (ev.kind === 'energetic') { chirp(t, 140, 70, .18, .12, 'sine'); chirp(t, 2400, 1800, .02, .03, 'square'); }
      else if (ev.kind === 'abort') chirp(t, 520, 260, .32, .025, 'triangle');
      else if (ev.kind === 'stage' && ev.stage === 2 && /^F/.test(ev.who)) chirp(t, 1500, 1500, .015, .025, 'sine', [-.6, .6, 0][+ev.who.slice(1) - 1]);
      else if (ev.kind === 'visitor') chirp(t, 330, 495, .2, .03, 'triangle');
    }};
}
// the per-frame sound state from the machine
export function soundState(S) {
  const males = S.males, P = S.P;
  return {fem: S.females.map(f => { const m = f.partner >= 0 ? males[f.partner] : null; return {tone: f.tone, stage: f.stage, gate: f.stage >= 4 ? 1 : m ? m.lamp : f.partner === -2 ? (Math.sin(S.t * Math.PI * 2 * 3.6) > .2 ? 1 : 0) : 0}; }),
    mal: males.map(m => ({B: m.B, F: m.F})), ambient: P.ambient, urgency: [...males, ...S.females].reduce((a, x) => a + Math.max(x.O, x.P), 0) / 5 / P.Lcap};
}
export function makeLiveSound() {
  let ctx = null, V = null, on = false, vol = null;
  return {
    get on() { return on; },
    start() { if (!ctx) { ctx = new (window.AudioContext || window.webkitAudioContext)(); vol = ctx.createGain(); vol.gain.value = .8; vol.connect(ctx.destination); V = makeVoices(ctx, vol); } ctx.resume(); on = true; },
    stop() { if (ctx) ctx.suspend(); on = false; },
    frame(S) { if (on && V) V.frame(ctx.currentTime, soundState(S)); },
    event(ev) { if (on && V) V.event(ctx.currentTime + .01, ev); },
    volume(v) { if (vol) vol.gain.value = v; }};
}
// offline: trace = [{t, st}] at a steady rate, events = [{t, ...ev}] (sim time, offset by t0)
export async function renderOffline(trace, events, dur, t0 = 0, sr = 44100) {
  const ctx = new OfflineAudioContext(2, Math.ceil(dur * sr), sr), V = makeVoices(ctx, ctx.destination);
  for (const f of trace) if (f.t - t0 >= 0 && f.t - t0 < dur) V.frame(f.t - t0, f.st);
  for (const e of events) if (e.t - t0 >= 0 && e.t - t0 < dur - .5) V.event(e.t - t0, e);
  return ctx.startRendering();
}
export function wav(buf) {
  const n = buf.length, ch = buf.numberOfChannels, out = new DataView(new ArrayBuffer(44 + n * ch * 2)), w = (o, s) => { for (let i = 0; i < s.length; i++) out.setUint8(o + i, s.charCodeAt(i)); };
  w(0, 'RIFF'); out.setUint32(4, 36 + n * ch * 2, true); w(8, 'WAVEfmt '); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, ch, true); out.setUint32(24, buf.sampleRate, true); out.setUint32(28, buf.sampleRate * ch * 2, true); out.setUint16(32, ch * 2, true); out.setUint16(34, 16, true); w(36, 'data'); out.setUint32(40, n * ch * 2, true);
  const d = [...Array(ch)].map((_, c) => buf.getChannelData(c)); let o = 44; for (let i = 0; i < n; i++) for (let c = 0; c < ch; c++) { out.setInt16(o, Math.max(-1, Math.min(1, d[c][i])) * 32767, true); o += 2; }
  return new Uint8Array(out.buffer);
}
