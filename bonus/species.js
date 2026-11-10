// THE TEN SPECIES: every art jelly of current/drift/rigs.js, made a thinking, causally real animal of its own (fictional) species.
//
// Each keeps its art body (the rig: its look, its line, its traits) and gains the Thinking Jelly's mechanism, from thinkjelly-sim.js:
// pacemakers that charge and fire, a nerve ring that carries the signal both ways and goes refractory, a muscle that twitches where the
// signal passes. The muscle's pull is what bends the bell (the rig's own pulse shape is driven by the measured contraction, not by a clock),
// and the bell's push and recoil move the animal through the water. Its senses (light, the balance stones, touch) set how hard each
// stretch of rim pulls, so it turns because one side pulls harder. Nothing here is a canned animation.
//
// HONEST NOTE: the ten art rigs do not carry the full tetrahedral soft body of the Real Jelly (2,000+ tetrahedra each would not run ten at
// once on a phone). Their body is a lighter mechanical model: the bell is a damped spring (its stiffness and damping per species) that the
// muscle squeezes; its squeeze and rebound give the thrust and the free second push. The nervous system is the real one, unabridged.
//
// The species, their binomials and their natural history are FICTIONAL: invented for these films, consistent with each body plan.
import {makeNerve} from './thinkjelly-sim.js';
import {RIGS, makeRig} from '../current/drift/rigs.js';
import {bellWindow} from './film.js';

const TAU = Math.PI * 2;
// pace: mean pacemaker period (s); spread: how unequal the pacemakers are; loop: seconds for the signal to go round the ring (conduction);
// refr: refractory time; rise/fall: muscle pull and release (s); musc: muscle fraction (how hard a full twitch squeezes);
// stiff/damp: the bell's spring (gel stiffness) and damping; thrust; photo/stato/touch: senses; tent: tentacles (count, length);
// feed: feeding style; lum: bioluminescence (colour, strength); rings: linked nerve rings (lag between them).
export const SPECIES = {
  glass: {binomial: 'Aurelia vitrea', common: 'Glass Moon', n: 8, pace: 2.3, spread: .18, loop: 1.0, refr: .42, rise: .12, fall: .34, musc: .8, stiff: 26, damp: 4, thrust: 1.1, photo: 1.2, stato: .5, touch: .6, tent: [16, .8], feed: 'filter: a slow drift of mucus traps plankton on the bell', lum: ['#ffd8a8', .5],
    plan: 'lathe moon jelly; four horseshoe gonads; radial canals', behave: 'swims steadily toward light, slows in the dark', think: 'eight pacemakers of near-equal speed: the lead passes among them, so its beat wanders a little'},
  filmbell: {binomial: 'Cinebolus mollis', common: 'Film Bell', n: 6, pace: 4.6, spread: .25, loop: 1.8, refr: 1.1, rise: .4, fall: .9, musc: .55, stiff: 9, damp: 2.2, thrust: .55, photo: .5, stato: .4, touch: 1.2, tent: [0, 0], feed: 'absorbs the film it catches: the frames dissolve into its particles', lum: ['#ffe9c4', .7],
    plan: 'a bell of particles inside a fresnel shell; no tentacles', behave: 'a slow, soft drifter; long, wallowing pulses', think: 'six slow pacemakers on a sluggish ring: the wave takes most of a second to go round, so the bell closes in a visible ripple'},
  mantle: {binomial: 'Teuthomedusa cloacae', common: 'Sewer Creature', n: 4, pace: 1.25, spread: .06, loop: .35, refr: .3, rise: .06, fall: .2, musc: 1.1, stiff: 48, damp: 6, thrust: 2.4, photo: .9, stato: .2, touch: 1.6, tent: [8, .6], feed: 'a hunter: dashes at moving things', lum: ['#ffc060', .9], head: true,
    plan: 'prolate, squid-like mantle; a nervous system of light inside', behave: 'fast and head-led: quick jets, sharp turns', think: 'four fast pacemakers clustered at the head on a quick ring: one beat leads every time, so it jets like a metronome'},
  golden: {binomial: 'Chrysosplatta aurea', common: 'Golden Splat', n: 12, pace: 2.6, spread: .45, loop: 1.2, refr: .5, rise: .14, fall: .4, musc: .75, stiff: 22, damp: 3.5, thrust: 1.0, photo: 1.0, stato: .6, touch: .8, tent: [12, .7], feed: 'grazes: sweeps the water with its crown', lum: ['#ffb84a', 1.0],
    plan: 'a jelly of 4,200 light splats, crown forward', behave: 'irregular: bursts of quick beats, then pauses', think: 'twelve very unequal pacemakers: whichever fills first leads, so its rhythm is jazz, never quite repeating'},
  celluloid: {binomial: 'Triplicata celluloidea', common: 'Celluloid', n: 8, pace: 2.4, spread: .15, loop: .9, refr: .45, rise: .1, fall: .3, musc: .85, stiff: 30, damp: 4, thrust: 1.2, photo: 1.1, stato: .6, touch: .7, tent: [6, .9], feed: 'strains the water through its sprocket holes', lum: ['#ffcf70', .6], rings: 3, lag: .18,
    plan: 'three sheets of amber celluloid with sprocket holes and frame lines', behave: 'swims by three overlapping strokes, sheet after sheet', think: 'three nerve rings, one per sheet, linked: each sheet fires when the one before it has, 0.18 s later'},
  veil: {binomial: 'Velum frigidum', common: 'Fleck Veil', n: 16, pace: 3.4, spread: .3, loop: 2.2, refr: .9, rise: .3, fall: .8, musc: .45, stiff: 12, damp: 2.6, thrust: .7, photo: .4, stato: .5, touch: 2.0, tent: [4, 1.6], feed: 'a passive veil: whatever drifts in sticks to its flecks', lum: ['#8fd0ff', .8],
    plan: '24,000 cold blue flecks; a perforated film band at the rim; one film-strip tentacle', behave: 'drifts; flinches hard when touched', think: 'sixteen weak pacemakers on a very slow ring: touch fires the nearest one, and the flinch rolls round the veil'},
  reel: {binomial: 'Bobina iridescens', common: 'Film-Reel Jelly', n: 16, pace: 2.0, spread: .03, loop: .7, refr: .4, rise: .09, fall: .3, musc: .9, stiff: 34, damp: 4.5, thrust: 1.3, photo: 1.3, stato: .7, touch: .6, tent: [8, 1.4], feed: 'reels in prey on its 35 mm tentacles', lum: ['#7ff0e6', .7],
    plan: 'iridescent celluloid veil; sixteen canals; 35 mm film-strip tentacles with gold splices', behave: 'metronomic: the most regular swimmer in the water', think: 'sixteen pacemakers tuned almost alike: the beat is a projector at 24 frames, steady as a clock'},
  sentinel: {binomial: 'Loricomedusa vigil', common: 'Sentinel', n: 8, pace: 3.8, spread: .1, loop: 1.0, refr: 1.4, rise: .2, fall: .55, musc: 1.4, stiff: 70, damp: 7, thrust: 2.0, photo: 1.6, stato: 1.4, touch: .4, tent: [6, 1.1], feed: 'ambush: holds still, eyes open, then strikes', lum: ['#ffd27a', .6],
    plan: 'armoured carapace with two rings of eyes; segmented timeworm tentacles', behave: 'stiff, slow, strong: few beats, each a shove', think: 'a long refractory time and a stiff bell: it cannot beat fast, so each beat is saved and spent whole'},
  medusa: {binomial: 'Lucifera memor', common: 'Afterlight Medusa', n: 12, pace: 2.8, spread: .2, loop: 1.1, refr: .55, rise: .13, fall: .4, musc: .8, stiff: 24, damp: 3.6, thrust: 1.0, photo: 1.2, stato: .7, touch: 1.0, tent: [12, 1.3], feed: 'collects: each film it holds lights one tentacle silver', lum: ['#dfe8ff', .9],
    plan: 'compact golden medusa; twelve hanging tentacles', behave: 'a gatherer: lingers near films and light', think: 'twelve pacemakers, one per tentacle: a touched tentacle fires its own pacemaker first'},
  doodle: {binomial: 'Graphomedusa rudis', common: 'Doodle Jelly', n: 6, pace: 2.2, spread: .35, loop: 1.3, refr: .5, rise: .1, fall: .36, musc: .9, stiff: 20, damp: 3, thrust: 1.1, photo: .9, stato: .4, touch: 1.1, tent: [12, .9], feed: 'scribbles: grabs whatever its raw tentacles cross', lum: ['#ffd070', .7], jitter: .25,
    plan: 'eighteen hand-drawn rib strokes in gold and cyan; a drawing in its crown', behave: 'wobbly, nervous: its pacemakers drift as if drawn by hand', think: 'six pacemakers whose speeds wander each beat: a hand-drawn rhythm'}};

const pulseInv = (a, rising) => { a = Math.max(0, Math.min(1, a)); if (rising) return Math.asin(a) / (Math.PI / 2) * .28; let lo = 0, hi = 1; for (let i = 0; i < 18; i++) { const m = (lo + hi) / 2, s = m * m * (3 - 2 * m); if (1 - s > a) lo = m; else hi = m; } return .28 + .72 * (lo + hi) / 2; };

// a species' nervous system: one or more real nerve rings (thinkjelly-sim's makeNerve), with its pacemakers spread round the ring
function nerveOf(sp, seed) { const per = []; for (let i = 0; i < sp.n; i++) { const u = Math.sin(seed * 9.1 + i * 2.39) * .5 + .5; per.push(sp.pace * (1 - sp.spread / 2 + sp.spread * u)); }
  const rings = []; for (let k = 0; k < (sp.rings || 1); k++) { const nv = makeNerve({periods: per.map(p => p * (1 + .02 * k)), rise: sp.rise, fall: sp.fall, refr: sp.refr, loop: sp.loop}); nv.rh.forEach((r, i) => { r.node = Math.round(i * nv.N / sp.n) % nv.N; }); if (k) nv.rh.forEach(r => { r.silent = true; }); rings.push(nv); }
  return rings; }

export function makeThinkingRig(THREE, id, opts = {}) {
  const sp = SPECIES[id] || SPECIES.glass, meta = RIGS.find(r => r.id === id) || RIGS[0], rig = makeRig(THREE, meta.id), beats = [], V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
  const rings = nerveOf(sp, opts.seed ?? id.length), NV = rings[0], NN = NV.N, GAIN = new Float32Array(NN).fill(1), sense = {photo: sp.photo, stato: sp.stato, touch: sp.touch, thrust: sp.thrust, tank: opts.tank ?? 5};
  const root = new THREE.Group(); root.add(rig.group); root.name = meta.name; const WIN = bellWindow(THREE, rig); let filmAspect = 4 / 3;
  const B = {r: 0, v: 0, pos: V3(), vel: V3(), ax: V3(0, 1, 0), spin: V3()}; let T = 0, ph = .999, rising = false, lastA = 0, lastBeat = -9, glow = 0, look = {view: 'flesh', glow: 0}, puppet = !!opts.puppet, pending = [];
  const lead = nv => nv.rh.filter(r => !r.silent).sort((a, b) => a.period - b.period)[0] || nv.rh[0];
  const act = () => { let a = 0; for (const nv of rings) { let s = 0; for (let n = 0; n < NN; n++) s += nv.act[n]; a = Math.max(a, s / NN); } return a; };
  const dact = () => { let a = 0; for (const nv of rings) { let s = 0; for (let n = 0; n < NN; n++) s += nv.dact[n]; a += s / NN; } return a / rings.length; };
  const beat = (r) => { lastBeat = T; glow = Math.min(1.6, glow + sp.lum[1]); for (const f of beats) f({t: T, r}); };
  function steer(dt, light) { if (puppet) return; const want = V3(); if (light) { const to = light.clone().sub(B.pos); const d = to.length(); if (d > 1e-3) want.addScaledVector(to.normalize(), sense.photo * Math.min(1, d / 3)); }
    want.y += .35 * sense.stato; const r = B.pos.length(); if (r > sense.tank * .6) want.addScaledVector(B.pos.clone().normalize(), -1.5 * Math.min(1, (r - sense.tank * .6) / (sense.tank * .4)));
    // the rim pulls unevenly: the side facing away from where it wants to go pulls harder, so the bell swings round
    const perp = want.clone().addScaledVector(B.ax, -want.dot(B.ax)); const u = V3(1, 0, 0).cross(B.ax); if (u.lengthSq() < .01) u.set(0, 0, 1).cross(B.ax); u.normalize(); const w = B.ax.clone().cross(u);
    for (let n = 0; n < NN; n++) { const a = n / NN * TAU, o = u.clone().multiplyScalar(Math.cos(a)).addScaledVector(w, Math.sin(a)), tgt = Math.max(.25, Math.min(1.9, 1 - 1.1 * o.dot(perp))); GAIN[n] += (tgt - GAIN[n]) * Math.min(1, dt * 4); }
    // the torque of that uneven pull, while the muscle is pulling
    const tq = V3(); for (let n = 0; n < NN; n++) { const a = n / NN * TAU, o = u.clone().multiplyScalar(Math.cos(a)).addScaledVector(w, Math.sin(a)), f = (GAIN[n] - 1) * Math.max(0, NV.dact[n]); tq.addScaledVector(B.ax.clone().cross(o), -f); }
    B.spin.addScaledVector(tq, dt * .9 * sp.thrust / NN * 8); }
  function body(dt) { // the bell: a damped spring the muscle squeezes; the squeeze and the rebound push it along its axis
    const a = act(), k = sp.stiff, c = sp.damp; B.v += (-k * B.r - c * B.v + k * a * sp.musc) * dt; B.r += B.v * dt;
    const push = sense.thrust * (Math.max(0, B.v) + .3 * Math.max(0, -B.v)) * (puppet ? 0 : 1); B.vel.addScaledVector(B.ax, push * dt * 2.2); B.vel.multiplyScalar(Math.exp(-dt * 1.4)); B.pos.addScaledVector(B.vel, dt);
    if (!puppet) { B.ax.applyAxisAngle(B.spin.lengthSq() > 1e-12 ? B.spin.clone().normalize() : V3(1, 0, 0), B.spin.length() * dt).normalize(); B.spin.multiplyScalar(Math.exp(-dt * 2.5)); const r = B.pos.length(); if (r > sense.tank) B.pos.multiplyScalar(sense.tank / r); }
    // the art body follows the measured contraction: its pulse phase is read off the muscle, rising while it pulls, falling as the jelly springs back
    const rate = a - lastA; if (rate > .002) rising = true; else if (rate < -.002) rising = false; lastA = a; ph = a < .01 && !rising ? .999 : pulseInv(Math.min(1, B.r / Math.max(.2, sp.musc) * 1.1), rising); }
  const J = {id, name: meta.name, kind: 'species', species: sp, group: root, norm: rig.norm, tentacles: rig.tentacles, rig, views: ['flesh'], rings, nerve: NV, sense, body: B,
    get puppet() { return puppet; }, set puppet(v) { puppet = !!v; },
    pulse(k = 1, at) { const r = at != null ? NV.rh[at % NV.rh.length] : lead(NV); const ok = NV.stimulate(r.i); if (ok) beat(r.i); return ok; },
    touch(i) { const r = NV.rh[(i ?? 0) % NV.rh.length]; if (Math.random() < Math.min(1, sense.touch)) return NV.stimulate(r.i); return false; },
    setLook(o) { Object.assign(look, o); }, onBeat(f) { beats.push(f); },
    state() { return {beat: lastBeat, rate: NV.rate(), kind: 'species', com: root.localToWorld(B.pos.clone()), contraction: act()}; },
    controls: [
      {kind: 'button', label: 'FIRE', run: () => J.pulse(1)},
      {kind: 'button', label: 'SILENCE', run: () => { const r = lead(NV); if (r) r.silent = true; }},
      {kind: 'button', label: 'CUT THE RING', run: () => { NV.cuts.add(Math.floor(NN / 4)); NV.cuts.add(Math.floor(3 * NN / 4)); }},
      {kind: 'button', label: 'INTACT', run: () => { for (const nv of rings) nv.reset(); rings.slice(1).forEach(nv => nv.rh.forEach(r => { r.silent = true; })); }},
      {kind: 'range', label: 'cold · warm', min: .4, max: 1.8, step: .01, get: () => NV.warm, set: v => { for (const nv of rings) nv.warm = +v; }},
      {kind: 'range', label: 'still · swims', min: 0, max: 4, step: .05, get: () => sense.thrust, set: v => { sense.thrust = +v; }},
      {kind: 'range', label: 'blind · to the light', min: 0, max: 2.5, step: .05, get: () => sense.photo, set: v => { sense.photo = +v; }}],
    update(s = {}) { const dt = Math.min(1 / 30, Math.max(1 / 240, s.dt ?? 1 / 60)); T = s.t ?? T + dt;
      if (s.ph != null && !s.drive) { if (J._ph != null && s.ph < J._ph - .5) J.pulse(.8); J._ph = s.ph; }   // a caller that drives by phase: its beat stimulates the leading pacemaker
      if (sp.jitter) for (const r of NV.rh) r.period = Math.max(.6, r.period * (1 + (Math.random() - .5) * sp.jitter * dt));
      for (let k = 0; k < rings.length; k++) { rings[k].step(dt); for (const ev of rings[k].events) if (ev.kind === 'lead' || (k && ev.kind === 'reset')) { if (k === 0) beat(ev.r); if (k + 1 < rings.length) pending.push({t: T + sp.lag, k: k + 1, i: ev.r}); } }
      for (let q = pending.length - 1; q >= 0; q--) if (T >= pending[q].t) { const p = pending[q]; pending.splice(q, 1); const nv = rings[p.k]; nv.stimulate(p.i % nv.rh.length); if (p.k + 1 < rings.length) pending.push({t: T + sp.lag, k: p.k + 1, i: p.i}); }
      steer(dt, s.light ? root.worldToLocal(s.light.clone()) : null); body(dt); glow *= Math.exp(-dt * 1.8);
      rig.group.position.copy(B.pos); rig.group.quaternion.setFromUnitVectors(V3(0, 1, 0), B.ax);
      rig.update({...s, dt, t: T, ph, glow: (s.glow ?? .15) + (look.glow || 0) + glow * .6, hurt: s.hurt || 0, scale: s.scale ?? 7}); WIN.update(s.camObj, act()); },
    setFilm(tex, aspect) { rig.setFilm(tex); if (aspect) filmAspect = aspect; else if (tex?.image?.videoWidth) filmAspect = tex.image.videoWidth / tex.image.videoHeight; else if (tex?.image?.width) filmAspect = tex.image.width / tex.image.height; WIN.set(tex, filmAspect); }, window: WIN, dispose: () => rig.dispose()};
  return J;
}

export function speciesCard(id) { const sp = SPECIES[id], m = RIGS.find(r => r.id === id); if (!sp || !m) return ''; return `${m.name} · <i>${sp.binomial}</i> (fictional)\nBody: ${sp.plan}.\nBehaviour: ${sp.behave}.\nHow it thinks: ${sp.think}.\nFeeding: ${sp.feed}.`; }
