// THE WHITNEY LIGHT ORGAN: lights as programmed curves, after John Whitney Sr.'s differential motion (Digital Harmony, 1980;
// Permutations, 1968; Matrix III, 1972; Arabesque, 1975) and the incremental drift of the "Music Box" idea.
//
// Differential motion: light i turns at  ω_i = base · (i + 1) · ratio  (+ detune · i), so the fastest makes many orbits while the slowest
// makes one; when the speeds are whole-number ratios the pattern locks into symmetries (resolution) and drifts apart between them (tension).
// RDTD-style controls (after the Whitney–Reed radius-differential / theta-differential idea): each light's radius steps by dR and its phase
// by dθ. Paths: 'rose' (polar rose r·cos(kθ)), 'lissajous' (a:b), 'epicycle' (two circles), 'musicbox' (circles; a light crossing the
// line at angle 0 strikes a note). Tempo-locked: base is in turns per bar of the song's BPM.
const TAU = Math.PI * 2, PENTA = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24, 26, 28, 31, 33, 36];
export const PRESETS = {
  'Permutations': {mode: 'rose', n: 12, base: .125, ratio: 1, detune: 0, radius: 2.6, dR: .05, dTheta: 0, k: 3, height: 1.2, intensity: 1.1, notes: false},
  'Matrix': {mode: 'lissajous', n: 10, base: .125, ratio: 1.5, detune: 0, radius: 3, dR: 0, dTheta: .2, k: 2, height: 1.8, intensity: 1, notes: false},
  'Arabesque': {mode: 'epicycle', n: 14, base: .0625, ratio: 1, detune: .004, radius: 2.2, dR: .08, dTheta: .45, k: 5, height: 1, intensity: 1.2, notes: false},
  'Music Box 1:n': {mode: 'musicbox', n: 12, base: .0625, ratio: 1, detune: 0, radius: 1.4, dR: .22, dTheta: 0, k: 1, height: .4, intensity: 1, notes: true},
  'Drift (tension)': {mode: 'musicbox', n: 12, base: .0625, ratio: 1, detune: .011, radius: 1.4, dR: .22, dTheta: 0, k: 1, height: .4, intensity: 1, notes: true}};

export function makeOrgan(THREE, scene, o = {}) {
  const P = Object.assign({}, PRESETS['Permutations'], o.params || {}), MAXN = 16, REAL = o.lights ?? 4, group = new THREE.Group(); scene.add(group);
  const dotTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 30); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.3, 'rgba(255,230,190,.6)'); gr.addColorStop(1, 'rgba(255,200,140,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
  const dots = [], lights = [], TR = 48, trail = new Float32Array(MAXN * TR * 3), trailG = new THREE.BufferGeometry(); trailG.setAttribute('position', new THREE.BufferAttribute(trail, 3));
  const tl = new THREE.Points(trailG, new THREE.PointsMaterial({size: .05, color: 0xffd9a0, transparent: true, opacity: .45, depthWrite: false, blending: THREE.AdditiveBlending})); tl.frustumCulled = false; group.add(tl);
  for (let i = 0; i < MAXN; i++) { const s = new THREE.Sprite(new THREE.SpriteMaterial({map: dotTex, color: new THREE.Color().setHSL(.08 + i * .045, .8, .7), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending})); s.scale.setScalar(.35); group.add(s); dots.push(s); }
  for (let i = 0; i < REAL; i++) { const l = new THREE.PointLight(0xffe0b0, 0, 9, 1.6); group.add(l); lights.push(l); }
  const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(6, 0, 0)]), new THREE.LineBasicMaterial({color: 0xf0a35a, transparent: true, opacity: .25})); group.add(line);
  const O = {params: P, group, on: true, bpm: 120, ac: null, out: null, crossings: [], onCross: null, angles: new Float64Array(MAXN), pos: [], env: 1, mute: false, k: 0,
    set(p) { Object.assign(P, typeof p === 'string' ? PRESETS[p] : p); },
    omega(i) { return TAU * (P.base * (i + 1) * P.ratio + P.detune * i) * (O.bpm / 240); },   // rad/s: base is turns per 4-beat bar
    at(i, t) { const th = O.omega(i) * t + i * P.dTheta, r = P.radius + i * P.dR; let x, y, z;
      if (P.mode === 'rose') { const rr = r * Math.cos(P.k * th); x = rr * Math.cos(th); z = rr * Math.sin(th); y = P.height + .4 * Math.sin(th * 2); }
      else if (P.mode === 'lissajous') { x = r * Math.sin(th + i * .3); y = P.height + r * .55 * Math.sin(th * P.ratio + P.dTheta * i); z = r * .4 * Math.cos(th * .5); }
      else if (P.mode === 'epicycle') { x = r * Math.cos(th) + r * .45 * Math.cos(P.k * th); z = r * Math.sin(th) + r * .45 * Math.sin(P.k * th); y = P.height + .5 * Math.sin(th * 3); }
      else { x = r * Math.cos(th); z = r * Math.sin(th); y = P.height; }
      return {x, y, z, th}; },
    audio(ac, dest) { O.ac = ac; O.out = dest; },
    note(i, gain = .2) { if (!O.ac || O.mute) return; const t = O.ac.currentTime, f = 220 * Math.pow(2, PENTA[i % PENTA.length] / 12), os = O.ac.createOscillator(), g = O.ac.createGain(); os.type = 'triangle'; os.frequency.value = f; g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(gain, t + .005); g.gain.exponentialRampToValueAtTime(.0004, t + 1.6); os.connect(g).connect(O.out || O.ac.destination); os.start(t); os.stop(t + 1.7); },
    update(t, dt) { group.visible = O.on; const n = Math.min(MAXN, P.n); O.pos.length = 0;
      for (let i = 0; i < MAXN; i++) { const d = dots[i]; d.visible = O.on && i < n; if (i >= n) continue; const q = O.at(i, t); d.position.set(q.x, q.y, q.z); O.pos.push(d.position);
        const prev = O.angles[i], cur = q.th; if (P.mode === 'musicbox' && Math.floor(cur / TAU) !== Math.floor(prev / TAU) && prev !== 0) { O.crossings.push({t, i}); if (O.crossings.length > 400) O.crossings.shift(); if (P.notes) O.note(i); d.scale.setScalar(.8); if (O.onCross) O.onCross(i, d.position); }
        O.angles[i] = cur; d.scale.setScalar(Math.max(.35, d.scale.x * Math.exp(-dt * 4))); d.material.opacity = Math.min(1, .55 + .45 * O.env);
        const o3 = (i * TR + (O.k % TR)) * 3; trail[o3] = q.x; trail[o3 + 1] = q.y; trail[o3 + 2] = q.z; }
      for (let i = n; i < MAXN; i++) for (let j = 0; j < TR; j++) trail.fill(999, (i * TR + j) * 3, (i * TR + j) * 3 + 3);
      O.k++; trailG.attributes.position.needsUpdate = true; line.visible = O.on && P.mode === 'musicbox'; line.position.y = P.height;
      lights.forEach((l, j) => { const i = Math.floor(j * n / lights.length); l.intensity = O.on ? 6 * P.intensity * O.env : 0; if (dots[i]) l.position.copy(dots[i].position); l.color.setHSL(.08 + i * .045, .7, .7); }); },
    nearest(p) { let b = 1e9; for (const q of O.pos) b = Math.min(b, q.distanceTo(p)); return b; }};
  return O;
}
