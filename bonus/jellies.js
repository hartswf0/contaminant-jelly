// THE JELLIES: one registry for every jelly in the water, so any page or game can hold any of them.
//
// Two kinds share one interface:
//   · the causally real animals (the Real Jelly, the Thinking Jelly, the Jelly Jar): the soft body of jellyjar-sim.js and the nerve ring of
//     thinkjelly-sim.js, wired as in realjelly.html: eight pacemakers, a nerve ring, the coronal and radial muscle, the spring of the jelly,
//     the water's push and the second push of the recoil, the balance stones, the rim's eyes, tentacles. Nothing is animated; it runs.
//   · the ten art rigs of current/drift/rigs.js, each made a thinking animal of its own fictional species (species.js); {classic: true} gives the old clock-driven rig.
//
// createJelly(THREE, id, opts) → J, and J is a drop-in for a rig (J.group, J.norm, J.update(s), J.setFilm(tex), J.dispose(), J.tentacles),
// so a game that used makeRig can use createJelly unchanged. On top of that every J has:
//   J.pulse(k)        make it beat now (a real one fires its leading pacemaker: the nerve decides whether it can, as a real one would)
//   J.setLook(o)      {view: 'flesh' | 'nerves' | 'muscle' | 'strain', glow, tint}
//   J.views           the views it has;   J.controls  its own live controls ({kind: 'button' | 'range', label, ...}) for an inspector
//   J.onBeat(fn)      called with {t, r} each time it beats (real: when a pacemaker leads; rig: when it is pulsed)
//   J.state()         {beat, rate, com, kind}
//   J.puppet          true for a game: it holds its place (the game moves J.group) and keeps beating and bending in place
// update(s) takes the rig's argument ({t, dt, ph, glow, cam, scale, ...}); a real jelly also reads s.light (world Vector3) and s.drive.
import {makeGel} from './jellyjar-sim.js';
import {makeNerve} from './thinkjelly-sim.js';
import {RIGS, makeRig} from '../current/drift/rigs.js';
import {makeThinkingRig, SPECIES, speciesCard} from './species.js';
export {SPECIES, speciesCard};

const TAU = Math.PI * 2;
export const REAL = [
  {id: 'realjelly', name: 'The Real Jelly', kind: 'real', from: 'bonus · The Real Jelly', line: 'A moon jelly whose every move comes from a running mechanism: eight pacemakers, a nerve ring, ring and radial muscle, the spring of the jelly, the water.', traits: 'causal · swims to the light · tentacles · vortex rings'},
  {id: 'thinkjelly', name: 'The Thinking Jelly', kind: 'real', from: 'bonus · The Thinking Jelly', line: 'The same animal opened up: its pacemakers, its nerve ring and its strain on show, to think with.', traits: 'causal · nerves and strain visible · cut the ring'},
  {id: 'jarjelly', name: 'The Jelly Jar', kind: 'real', from: 'bonus · Jelly Jar', line: 'A moon jelly cast in gelatin, resting in its jar: a soft body that keeps its volume and wobbles back.', traits: 'soft body · in a jar · wobbles on the beat'}];
export const JELLIES = [...REAL, ...RIGS.map(r => ({...r, kind: 'rig'}))];
export const GAME_JELLIES = REAL.filter(r => r.id !== 'jarjelly');   // the ones a game can carry (the jar sits on its floor)

const VARIANT = {
  realjelly: {periods: [5.2, 4.2, 5.7, 4.6, 3.6, 5.4, 4.4, 6.2], rise: .55, fall: .5, refr: 1.5, loop: .5, thrust: 2.8, view: 'flesh', tent: true, free: true},
  thinkjelly: {periods: [2.35, 1.9, 2.6, 2.1, 1.62, 2.45, 2.0, 2.8], rise: .1, fall: .32, refr: .42, loop: 1, thrust: 1.6, view: 'strain', tent: false, free: true},
  jarjelly: {periods: null, thrust: 0, view: 'flesh', tent: false, free: false}};
export const RCOL = [[1, .45, .4], [1, .65, .3], [.95, .85, .35], [.55, .9, .45], [.35, .9, .8], [.4, .7, 1], [.65, .55, 1], [.95, .5, .85]];

export function createJelly(THREE, id, opts = {}) {
  if (VARIANT[id]) return makeReal(THREE, id, opts);
  if (opts.classic) return wrapRig(THREE, id, opts);   // the old art rig, beating on a clock
  return makeThinkingRig(THREE, id, opts);             // the art rig as a thinking animal of its own species (species.js)
}
// for games: a drop-in for makeRig(THREE, id) that hands back the thinking version (opts.classic for the old one)
export const makeGameJelly = (THREE, id, opts = {}) => createJelly(THREE, id, {puppet: true, ...opts});

// ---------------------------------------------------------------- an art rig, answering the shared calls
function wrapRig(THREE, id, opts) {
  const rig = makeRig(THREE, RIGS.some(r => r.id === id) ? id : 'glass'), beats = [], meta = RIGS.find(r => r.id === id) || RIGS[0];
  let ph = .999, period = opts.period || 2.6, pulsed = -9, look = {view: 'flesh', glow: 0}, t = 0, flare = 0;
  const J = {id, name: meta.name, kind: 'rig', group: rig.group, norm: rig.norm, tentacles: rig.tentacles, views: ['flesh'], puppet: !!opts.puppet,
    controls: [{kind: 'button', label: 'PULSE', run: () => J.pulse(1)}, {kind: 'range', label: 'slow · quick', min: 1, max: 5, step: .1, get: () => period, set: v => { period = +v; }}],
    pulse(k = 1) { ph = 0; pulsed = t; flare = Math.min(1.5, flare + k); for (const f of beats) f({t, r: 0}); return true; },
    setLook(o) { Object.assign(look, o); },
    onBeat(f) { beats.push(f); },
    state() { return {beat: pulsed, rate: 60 / period, kind: 'rig', com: rig.group.getWorldPosition(new THREE.Vector3())}; },
    update(s) { const dt = s.dt ?? 1 / 60; t = s.t ?? t + dt; if (s.ph != null && !s.drive) ph = s.ph; else { ph = Math.min(.999, ph + dt / period); if (!s.drive && ph >= .999 && t - pulsed > period) J.pulse(.4); }
      flare *= Math.exp(-dt * 2.5); rig.update({...s, ph, dt, t, glow: (s.glow ?? .15) + (look.glow || 0) + flare * .6, hurt: s.hurt || 0, scale: s.scale ?? 7}); },
    setFilm: tex => rig.setFilm(tex), dispose: () => rig.dispose()};
  return J;
}

// ---------------------------------------------------------------- a causally real animal (after realjelly.html, one instance per call)
function makeReal(THREE, id, opts) {
  const V = VARIANT[id], meta = REAL.find(r => r.id === id), low = !!opts.low, VOX = low ? .22 : (opts.vox || .18), V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
  const G = makeGel({free: V.free, firm: .5, s: VOX, damp: .42, H: .7, jar: 1.5}), N = G.N, X0 = Float32Array.from(G.X);
  const NV = V.periods ? makeNerve({periods: V.periods, rise: V.rise, fall: V.fall, refr: V.refr, loop: V.loop}) : null, NN = NV ? NV.N : 48;
  const group = new THREE.Group(), beats = [], look = {view: opts.view || V.view, glow: 0}; group.name = meta.name;
  // the coronal muscle (edges round the lower bell) and the radial muscle (crown to rim), each tied to the stretch of nerve ring at its angle
  const sectOf = (x, z) => ((Math.round(Math.atan2(z, x) / TAU * NN) % NN) + NN) % NN, MUS = [], RADM = [];
  for (let e = 0; e < G.EL.length; e++) { const a = G.EI[e * 2] * 3, b = G.EI[e * 2 + 1] * 3, mx = (X0[a] + X0[b]) / 2, my = (X0[a + 1] + X0[b + 1]) / 2, mz = (X0[a + 2] + X0[b + 2]) / 2, r = Math.hypot(mx, mz), dx = X0[b] - X0[a], dy = X0[b + 1] - X0[a + 1], dz = X0[b + 2] - X0[a + 2], L = Math.hypot(dx, dy, dz);
    if (r >= .45 * G.R && my <= .5 * G.H && Math.abs((-mz * dx + mx * dz) / (r * L)) >= .7 && L <= VOX * 1.5) MUS.push({e, a: a / 3, b: b / 3, n: sectOf(mx, mz)});
    else if (r >= .3 * G.R && my <= .6 * G.H && Math.abs((mx * dx + mz * dz) / (r * L)) >= .8 && L <= VOX * 1.2) RADM.push({e, n: sectOf(mx, mz)}); }
  const SECT = new Int16Array(N).fill(-1); for (let i = 0; i < N; i++) { const r = Math.hypot(X0[i * 3], X0[i * 3 + 2]); if (X0[i * 3 + 1] < .45 * G.H && r > .35 * G.R) SECT[i] = sectOf(X0[i * 3], X0[i * 3 + 2]); }
  let apex = 0; for (let i = 0; i < N; i++) if (X0[i * 3 + 1] - Math.hypot(X0[i * 3], X0[i * 3 + 2]) > X0[apex * 3 + 1] - Math.hypot(X0[apex * 3], X0[apex * 3 + 2])) apex = i;
  const GAIN = new Float32Array(NN).fill(1), AX = V3(0, 1, 0), COM = V3(), RIMC = V3(), DRV = {right: 1, photo: opts.photo ?? 1, thrust: V.thrust, tank: opts.tank ?? 5};
  let T = 0, RECOIL = 0, lastBeat = -9, flareK = 0, puppetK = opts.puppet ? 1 : 0;
  // the bell's skin, embedded in the jelly so it rides the flesh
  const PROF = []; for (let i = 0; i <= 26; i++) { const th = i / 26 * Math.PI / 2; PROF.push([G.R * Math.sin(th) * .975, G.H * Math.cos(th) * .975 + .006, i / 26]); } PROF.push([.87 * G.R, .01, 1]); for (let i = 0; i <= 14; i++) { const r = .74 * G.R * (1 - i / 14) * .985; PROF.push([r, .3 * G.H * (1 - (r / (.74 * G.R)) ** 2) + .012, 1 - i / 14 * .3]); }
  const AZ = low ? 48 : 72, NPv = PROF.length, bp = new Float32Array(NPv * (AZ + 1) * 3), idx = [];
  for (let j = 0; j < NPv; j++) for (let k = 0; k <= AZ; k++) { const a = k / AZ * TAU, [r0, y, rw] = PROF[j], r = r0 * (1 + .05 * Math.cos(8 * a) * Math.pow(rw, 6)), v = j * (AZ + 1) + k; bp.set([Math.cos(a) * r, y, Math.sin(a) * r], v * 3); if (j < NPv - 1 && k < AZ) idx.push(v, v + AZ + 1, v + 1, v + 1, v + AZ + 1, v + AZ + 2); }
  const bellGeo = new THREE.BufferGeometry(); bellGeo.setAttribute('position', new THREE.BufferAttribute(bp, 3)); bellGeo.setIndex(idx); const bellEmb = G.embed(bp), SM = new Float32Array(bp.length);
  const fleshM = new THREE.MeshPhysicalMaterial({color: 0xe9f6ff, roughness: .28, transmission: low ? 0 : .85, transparent: true, opacity: low ? .62 : .95, depthWrite: false, emissive: 0x0a1c22, sheen: .8, sheenColor: new THREE.Color(0xbfe8ff), thickness: .6, ior: 1.34, attenuationColor: new THREE.Color(0x9fd0e6), attenuationDistance: 1.6, clearcoat: .25, clearcoatRoughness: .4, side: THREE.DoubleSide});
  const ghostM = new THREE.MeshBasicMaterial({color: 0x7fb6c8, transparent: true, opacity: .1, depthWrite: false, side: THREE.DoubleSide});
  const bell = new THREE.Mesh(bellGeo, fleshM); bell.frustumCulled = false; group.add(bell);
  const line = (n, op = 1) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3)); g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3), 3)); const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({vertexColors: true, transparent: true, opacity: op, depthWrite: false})); l.frustumCulled = false; group.add(l); return l; };
  const ringP = new Float32Array(NN * 3); for (let n = 0; n < NN; n++) { const a = n / NN * TAU; ringP.set([Math.cos(a) * .88 * G.R, .05, Math.sin(a) * .88 * G.R], n * 3); } const ringEmb = G.embed(ringP), ringW = new Float32Array(NN * 3);
  const ringL = line(NN * 2), musL = line(Math.max(1, MUS.length) * 2), strL = line(G.EL.length * 2, .8);
  const rhoM = (NV ? NV.rh : []).map((r, i) => { const m = new THREE.Mesh(new THREE.SphereGeometry(.055, 10, 8), new THREE.MeshBasicMaterial({color: new THREE.Color(...RCOL[i]), toneMapped: false})); group.add(m); return m; });
  // tentacles and oral arms: chains hung from the rim, dragged by the water (their bend is the bell's motion, felt along them)
  const CH = []; if (V.tent) { const NT = low ? 16 : 24; for (let q = 0; q < NT; q++) CH.push({a: q / NT * TAU, n: 9, seg: .1 + (q % 5) * .012, X: null}); for (let q = 0; q < 4; q++) CH.push({a: q / 4 * TAU + Math.PI / 4, n: 7, seg: .07, arm: true, X: null}); }
  const anchor = []; for (const c of CH) { let best = 0, bd = 1e9; const rr = c.arm ? .18 * G.R : .95 * G.R; for (let i = 0; i < N; i++) { const d = (X0[i * 3] - Math.cos(c.a) * rr) ** 2 + (X0[i * 3 + 1] - .02) ** 2 + (X0[i * 3 + 2] - Math.sin(c.a) * rr) ** 2; if (d < bd) { bd = d; best = i; } } anchor.push(best); c.X = new Float32Array(c.n * 3); c.P = new Float32Array(c.n * 3); for (let j = 0; j < c.n; j++) { c.X.set([X0[best * 3], X0[best * 3 + 1] - j * c.seg, X0[best * 3 + 2]], j * 3); } c.P.set(c.X); }
  let nSeg = 0; for (const c of CH) nSeg += c.n - 1; const tentL = nSeg ? (() => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nSeg * 6), 3)); const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({color: 0xcfe8f0, transparent: true, opacity: .55, depthWrite: false})); l.frustumCulled = false; group.add(l); return l; })() : null;
  // the water's visible answer: vortex rings thrown back from the rim
  const VR = [], VN = 48, vrL = (() => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6 * VN * 2 * 3), 3)); const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({color: 0xaee6ff, transparent: true, opacity: .35, depthWrite: false})); l.frustumCulled = false; group.add(l); return l; })();
  // the jar, if it lives in one
  if (!V.free) { const jar = new THREE.Mesh(new THREE.CylinderGeometry(1.55, 1.55, 1.9, 48, 1, true), new THREE.MeshPhysicalMaterial({color: 0xdff6ff, roughness: .05, transmission: low ? 0 : .95, transparent: true, opacity: .18, side: THREE.DoubleSide, depthWrite: false})); jar.position.y = .95; group.add(jar); const base = new THREE.Mesh(new THREE.CircleGeometry(1.55, 48), new THREE.MeshStandardMaterial({color: 0x24343a, roughness: .9})); base.rotation.x = -Math.PI / 2; base.position.y = -.005; group.add(base); }

  function senses(dt, light) { const want = V3(); if (light) { const toL = light.clone().sub(COM), dl = toL.length(); if (dl > 1e-3) want.addScaledVector(toL.normalize(), DRV.photo * Math.min(1, dl / 3)); } want.y += .35 * DRV.right;
    const r = COM.length(); if (r > DRV.tank * .6) want.addScaledVector(COM.clone().normalize(), -1.5 * Math.min(1, (r - DRV.tank * .6) / (DRV.tank * .4)));   // a soft tank: it turns back before it leaves the shot
    const perp = want.addScaledVector(AX, -want.dot(AX)); for (let n = 0; n < NN; n++) { const o = V3(ringW[n * 3] - RIMC.x, ringW[n * 3 + 1] - RIMC.y, ringW[n * 3 + 2] - RIMC.z).normalize(), tgt = Math.max(.25, Math.min(1.9, 1 - 1.1 * o.dot(perp))); GAIN[n] += (tgt - GAIN[n]) * Math.min(1, dt * 4); } }
  function body(dt, light) {
    if (NV) { NV.step(dt); for (const ev of NV.events) if (ev.kind === 'lead') { lastBeat = T; for (const f of beats) f({t: T, r: ev.r}); if (DRV.thrust) VR.push({age: 0, c: RIMC.clone(), ax: AX.clone(), R: .75}); } }
    if (V.free) senses(dt, light);
    if (NV) { for (const m of MUS) G.SC[m.e] = 1 - .46 * NV.act[m.n] * Math.min(1.2, GAIN[m.n]); for (const m of RADM) G.SC[m.e] = 1 - .04 * NV.act[m.n]; }
    let nr = 0; COM.set(0, 0, 0); RIMC.set(0, 0, 0); for (let i = 0; i < N; i++) { COM.x += G.X[i * 3]; COM.y += G.X[i * 3 + 1]; COM.z += G.X[i * 3 + 2]; if (SECT[i] >= 0) { RIMC.x += G.X[i * 3]; RIMC.y += G.X[i * 3 + 1]; RIMC.z += G.X[i * 3 + 2]; nr++; } } COM.divideScalar(N); RIMC.divideScalar(Math.max(1, nr));
    AX.set(G.X[apex * 3], G.X[apex * 3 + 1], G.X[apex * 3 + 2]).sub(RIMC).normalize();
    RECOIL = 0; if (NV) { for (let n = 0; n < NN; n++) RECOIL += Math.max(0, -NV.dact[n]); RECOIL /= NN; }
    const th = DRV.thrust * (1 - puppetK); for (let i = 0; i < N; i++) { const s = SECT[i], k = NV && s >= 0 ? GAIN[s] * th * (Math.max(0, NV.dact[s]) + .3 * Math.max(0, -NV.dact[s])) : 0; G.F[i * 3] = AX.x * k; G.F[i * 3 + 1] = AX.y * k; G.F[i * 3 + 2] = AX.z * k; }
    G.step(dt, low ? 6 : 10);
    if (puppetK) { for (let i = 0; i < N; i++) for (let c = 0; c < 3; c++) G.X[i * 3 + c] -= COM.getComponent(c) * puppetK * .2; }   // a game carries it: it beats in place
    if (!V.free) return; const r = COM.length(), lim = DRV.tank; if (r > lim) { const k = lim / r; for (let i = 0; i < N; i++) for (let c = 0; c < 3; c++) G.X[i * 3 + c] -= COM.getComponent(c) * (1 - k); } }
  function skin() { G.apply(bellEmb, bp); G.apply(ringEmb, ringW);
    if (NV) for (let j = 0; j < NPv; j++) { const w = PROF[j][2], lag = .2 * w, wr = Math.pow(w, 1.4), wm = Math.pow(w, 5); for (let k = 0; k <= AZ; k++) { const v = j * (AZ + 1) + k, n = Math.round(k / AZ * NN) % NN, a = NV.twitchAt(n, lag) * Math.min(1.2, GAIN[n]);
      const dx = bp[v * 3] - RIMC.x, dy = bp[v * 3 + 1] - RIMC.y, dz = bp[v * 3 + 2] - RIMC.z, h = dx * AX.x + dy * AX.y + dz * AX.z, rx = dx - AX.x * h, ry = dy - AX.y * h, rz = dz - AX.z * h, kr = .13 * a * wr, ka = .01 * a * (1 - w) - .1 * a * wm; bp[v * 3] += -rx * kr + AX.x * ka; bp[v * 3 + 1] += -ry * kr + AX.y * ka; bp[v * 3 + 2] += -rz * kr + AX.z * ka; } }
    for (let it = 0; it < (low ? 2 : 4); it++) { SM.set(bp); for (let j = 1; j < NPv - 1; j++) for (let k = 0; k <= AZ; k++) { const v = j * (AZ + 1) + k, l = j * (AZ + 1) + (k + AZ - 1) % AZ, rr = j * (AZ + 1) + (k + 1) % AZ, u = v - AZ - 1, d = v + AZ + 1; for (let c = 0; c < 3; c++) bp[v * 3 + c] = SM[v * 3 + c] * .5 + (SM[l * 3 + c] + SM[rr * 3 + c] + SM[u * 3 + c] + SM[d * 3 + c]) * .125; } for (let j = 0; j < NPv; j++) for (let c = 0; c < 3; c++) bp[(j * (AZ + 1) + AZ) * 3 + c] = bp[j * (AZ + 1) * 3 + c]; }
    bellGeo.attributes.position.needsUpdate = true; bellGeo.computeVertexNormals(); }
  function views() { const vw = look.view;
    bell.material = vw === 'flesh' ? fleshM : ghostM; fleshM.emissive.setRGB(.04 + .5 * (look.glow + flareK) * .3, .11 + .8 * (look.glow + flareK) * .3, .13 + (look.glow + flareK) * .3);
    ringL.visible = vw === 'nerves' || vw === 'muscle'; musL.visible = vw === 'muscle'; strL.visible = vw === 'strain'; for (const m of rhoM) m.visible = vw !== 'flesh' || id === 'thinkjelly';
    if (ringL.visible && NV) { const p = ringL.geometry.attributes.position.array, c = ringL.geometry.attributes.color.array; for (let n = 0; n < NN; n++) { const m = (n + 1) % NN, a = NV.act[n]; if (NV.cuts.has(n)) { p.fill(0, n * 6, n * 6 + 6); continue; } p.set([ringW[n * 3], ringW[n * 3 + 1], ringW[n * 3 + 2], ringW[m * 3], ringW[m * 3 + 1], ringW[m * 3 + 2]], n * 6); const col = [.25 + a * .75, .35 + a * .55, .45 - a * .2]; c.set([...col, ...col], n * 6); } ringL.geometry.attributes.position.needsUpdate = true; ringL.geometry.attributes.color.needsUpdate = true; }
    if (musL.visible && NV) { const p = musL.geometry.attributes.position.array, c = musL.geometry.attributes.color.array; MUS.forEach((m, q) => { const a = NV.act[m.n]; p.set([G.X[m.a * 3], G.X[m.a * 3 + 1], G.X[m.a * 3 + 2], G.X[m.b * 3], G.X[m.b * 3 + 1], G.X[m.b * 3 + 2]], q * 6); const col = [.9 * a + .15, .3 * a + .1, .2]; c.set([...col, ...col], q * 6); }); musL.geometry.attributes.position.needsUpdate = true; musL.geometry.attributes.color.needsUpdate = true; }
    if (strL.visible) { const p = strL.geometry.attributes.position.array, c = strL.geometry.attributes.color.array; for (let e = 0; e < G.EL.length; e++) { const a = G.EI[e * 2] * 3, b = G.EI[e * 2 + 1] * 3, L = Math.hypot(G.X[a] - G.X[b], G.X[a + 1] - G.X[b + 1], G.X[a + 2] - G.X[b + 2]), s = Math.max(-1, Math.min(1, (L / G.EL[e] - 1) * 6)); p.set([G.X[a], G.X[a + 1], G.X[a + 2], G.X[b], G.X[b + 1], G.X[b + 2]], e * 6); const col = s > 0 ? [.55 + .45 * s, .55 - .2 * s, .45 - .3 * s] : [.5 + .2 * s, .62 + .2 * -s, .65 + .35 * -s]; c.set([...col, ...col], e * 6); } strL.geometry.attributes.position.needsUpdate = true; strL.geometry.attributes.color.needsUpdate = true; }
    if (NV) NV.rh.forEach((r, i) => { const n = r.node, m = rhoM[i]; m.position.set(ringW[n * 3], ringW[n * 3 + 1], ringW[n * 3 + 2]); m.scale.setScalar(r.silent ? .5 : .8 + .9 * Math.max(0, 1 - (NV.t - r.last) * 2) + .3 * r.charge); }); }
  function tentacles(dt) { if (!tentL) return; const p = tentL.geometry.attributes.position.array; let q = 0; const g = .9, keep = Math.pow(.25, dt);
    CH.forEach((c, ci) => { const a = anchor[ci]; c.X[0] = G.X[a * 3]; c.X[1] = G.X[a * 3 + 1]; c.X[2] = G.X[a * 3 + 2];
      for (let j = 1; j < c.n; j++) { const o = j * 3; for (let k = 0; k < 3; k++) { const v = (c.X[o + k] - c.P[o + k]) * keep; c.P[o + k] = c.X[o + k]; c.X[o + k] += v - (k === 1 ? 0 : 0) - AX.getComponent(k) * g * dt * dt * 4; } }
      for (let it = 0; it < 2; it++) for (let j = 1; j < c.n; j++) { const o = j * 3, u = o - 3, dx = c.X[o] - c.X[u], dy = c.X[o + 1] - c.X[u + 1], dz = c.X[o + 2] - c.X[u + 2], L = Math.hypot(dx, dy, dz) || 1, k = c.seg / L; c.X[o] = c.X[u] + dx * k; c.X[o + 1] = c.X[u + 1] + dy * k; c.X[o + 2] = c.X[u + 2] + dz * k; }
      for (let j = 0; j < c.n - 1; j++) { p.set([c.X[j * 3], c.X[j * 3 + 1], c.X[j * 3 + 2], c.X[j * 3 + 3], c.X[j * 3 + 4], c.X[j * 3 + 5]], q * 6); q++; } });
    tentL.geometry.attributes.position.needsUpdate = true; }
  function rings(dt) { const p = vrL.geometry.attributes.position.array; p.fill(0); let q = 0; for (let i = VR.length - 1; i >= 0; i--) { const w = VR[i]; w.age += dt; if (w.age > 2.2) { VR.splice(i, 1); continue; } }
    for (const w of VR.slice(-6)) { const c = w.c.clone().addScaledVector(w.ax, -w.age * .55), R = w.R * (1 + w.age * .6), u = V3(1, 0, 0).cross(w.ax); if (u.lengthSq() < .01) u.set(0, 0, 1).cross(w.ax); u.normalize(); const v = w.ax.clone().cross(u);
      for (let k = 0; k < VN; k++) { const a = k / VN * TAU, b = (k + 1) / VN * TAU; const A = c.clone().addScaledVector(u, Math.cos(a) * R).addScaledVector(v, Math.sin(a) * R), B = c.clone().addScaledVector(u, Math.cos(b) * R).addScaledVector(v, Math.sin(b) * R); p.set([A.x, A.y, A.z, B.x, B.y, B.z], q * 6); q++; } }
    vrL.geometry.attributes.position.needsUpdate = true; vrL.material.opacity = .35; }

  const leader = () => NV ? NV.rh.filter(r => !r.silent).sort((a, b) => a.period - b.period)[0] : null;
  const J = {id, name: meta.name, kind: 'real', group, norm: .9, tentacles: [], views: NV ? ['flesh', 'nerves', 'muscle', 'strain'] : ['flesh', 'strain'], gel: G, nerve: NV, drive: DRV,
    get puppet() { return !!puppetK; }, set puppet(v) { puppetK = v ? 1 : 0; },
    // a beat: the leading pacemaker fires (the nerve ring may refuse: it is refractory for a while after each beat, as a real one is)
    pulse(k = 1) { flareK = Math.min(1.5, flareK + .4 * k); if (!NV) { G.nudge(1.6 * k); lastBeat = T; for (const f of beats) f({t: T, r: 0}); return true; } const r = leader() || NV.rh[0]; const ok = NV.stimulate(r.i); if (ok) { lastBeat = T; for (const f of beats) f({t: T, r: r.i}); if (DRV.thrust) VR.push({age: 0, c: RIMC.clone(), ax: AX.clone(), R: .75}); } return ok; },
    setLook(o) { Object.assign(look, o); },
    onBeat(f) { beats.push(f); },
    state() { return {beat: lastBeat, rate: NV ? NV.rate() : 0, kind: 'real', com: group.localToWorld(COM.clone())}; },
    controls: [
      {kind: 'button', label: 'FIRE', run: () => J.pulse(1)},
      ...(NV ? [
        {kind: 'button', label: 'SILENCE', run: () => { const r = leader(); if (r) r.silent = true; }},
        {kind: 'button', label: 'CUT THE RING', run: () => { NV.cuts.add(Math.floor(NN / 4)); NV.cuts.add(Math.floor(3 * NN / 4)); }},
        {kind: 'button', label: 'INTACT', run: () => NV.reset()},
        {kind: 'button', label: 'ONE PACEMAKER', run: () => { NV.reset(); NV.rh.forEach((r, i) => { r.silent = i !== 4; }); }},
        {kind: 'button', label: 'TRAPPED WAVE', run: () => { NV.reset(); NV.rh.forEach(r => { r.silent = true; }); NV.oneWay(0); }},
        {kind: 'range', label: 'cold · warm', min: .4, max: 1.8, step: .01, get: () => NV.warm, set: v => { NV.warm = +v; }},
        {kind: 'range', label: 'still · swims', min: 0, max: 5, step: .1, get: () => DRV.thrust, set: v => { DRV.thrust = +v; }},
        {kind: 'range', label: 'blind · to the light', min: 0, max: 2, step: .05, get: () => DRV.photo, set: v => { DRV.photo = +v; }}] : []),
      {kind: 'range', label: 'soft · firm', min: .05, max: .95, step: .01, get: () => G.firm, set: v => { G.firm = +v; }}],
    update(s = {}) { const dt = Math.min(1 / 30, Math.max(1 / 240, s.dt ?? 1 / 60)); T = s.t ?? T + dt;
      // a game that drives it by phase (ph wrapping to 0 is a beat) gets a beat when its phase comes round
      if (s.ph != null && !s.drive) { if (J._ph != null && s.ph < J._ph - .5) J.pulse(.8); J._ph = s.ph; }
      const light = s.light ? group.worldToLocal(s.light.clone()) : null;
      body(dt, light); skin(); views(); tentacles(dt); rings(dt); flareK *= Math.exp(-dt * 2); },
    setFilm() {},
    dispose() { group.traverse(o => { o.geometry?.dispose?.(); (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m?.dispose?.()); }); }};
  return J;
}
