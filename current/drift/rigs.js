// RIGS: the ten jellies the project has built, each kept as it was made (its geometry and its shader), so any of them can swim the drifts.
// makeRig(THREE, id) -> {group, norm, update(s), setFilm(texture), dispose()}; s = {t, ph (pulse phase 0..1), glow, hurt, scale (point scale), lit (arms held)}.
// Bells are built crown-up (+y) with radius about 0.9; tentacles hang down (-y). The game's own film arms are drawn by the engine.

export const RIGS = [
  {id: 'glass', name: 'The Glass Moon', from: 'v1 · The Current', line: 'A lathe of the moon jelly’s profile: radial canals, four horseshoe gonads, a warm lamp inside. The first jelly.', traits: 'solid glass bell · the caught film shows through its crown'},
  {id: 'filmbell', name: 'The Film Bell', from: 'v2 · The Rising Tube', line: 'A bell of 3,400 particles that are the film you caught last, playing, inside a fresnel shell.', traits: 'particle bell · plays your latest film'},
  {id: 'mantle', name: 'The Sewer Creature', from: 'v3 · The Sewers of Internet Video', line: 'A prolate mantle of golden particles with a nervous system of light inside; the head leads.', traits: 'squid-like mantle · inner nerves glow'},
  {id: 'golden', name: 'The Golden Splat', from: 'v4 · Never a Frame · v5 · The Dive', line: 'A golden jellyfish of 4,200 splats, crown forward; in v5 its ghosts are blue.', traits: 'jelly of light · two-tone gold'},
  {id: 'celluloid', name: 'The Celluloid', from: 'v6 · The Branching Archive · v7 · The Drifts', line: 'Three sheets of amber celluloid with sprocket holes and frame lines, contracting one after another.', traits: 'three film sheets · the drifts’ own jelly'},
  {id: 'veil', name: 'The Fleck Veil', from: 'the landing', line: '24,000 blue flecks with a perforated film band at the rim, a real frame glowing inside, one film-strip tentacle and three filaments.', traits: 'cold blue veil · a frame inside · a film-strip tentacle'},
  {id: 'reel', name: 'The Film-Reel Jelly', from: 'bonus · Film-Reel Jelly', line: 'An iridescent celluloid veil with sixteen canals and a sprocketed margin, trailing 35 mm film-strip tentacles with gold splices.', traits: 'cyan and gold · 35 mm tentacles'},
  {id: 'sentinel', name: 'The Sentinel', from: 'bonus · Sentinel Timeworm', line: 'An armoured carapace with two rings of eyes, dissolving to gold, trailing segmented timeworms that each hold a saved frame.', traits: 'carapace and eyes · timeworm tentacles'},
  {id: 'medusa', name: 'The Afterlight Medusa', from: 'bonus · Afterlight Medusae', line: 'A compact golden medusa with twelve hanging tentacles; each film you hold lights one in silver.', traits: 'twelve tentacles · they light as you collect'},
  {id: 'doodle', name: 'The Doodle Jelly', from: 'bonus · Raw Doodle Worms', line: 'Eighteen hand-drawn rib strokes in gold and cyan, a drawing floating in the crown, twelve raw doodle tentacles.', traits: 'hand-drawn lines · a drawing in its crown'},
];
const PULSE = `float c(float ph){ ph = fract(ph); return ph < .28 ? sin(ph / .28 * 1.5708) : 1. - smoothstep(0., 1., (ph - .28) / .72); }`;
const pulseC = ph => { ph = ((ph % 1) + 1) % 1; return ph < .28 ? Math.sin(ph / .28 * Math.PI / 2) : 1 - (t => t * t * (3 - 2 * t))((ph - .28) / .72); };

// tentacles are verlet chains in world space: pinned to the rim (which contracts with the stroke), heavy with water drag, trailing behind when the bell moves,
// stirred by a slow current; they are drawn back in the rig's own space. A ribbon faces the camera; a line is a thread.
const _v = {};
function chainSim(THREE, n, len, x0, y0, z0, k) {
  const X = new Float32Array(n * 3), XP = new Float32Array(n * 3), root = new THREE.Vector3(x0, y0, z0), seg = len / (n - 1), w = new THREE.Vector3(), d = new THREE.Vector3(), sc = new THREE.Vector3(); let init = false;
  return {X, n, root, k, step(dt, t, pulse, M) {
    const S = sc.setFromMatrixScale(M).x, L = seg * S; w.set(root.x * (1 - .25 * pulse), root.y + .05 * pulse, root.z * (1 - .25 * pulse)).applyMatrix4(M); d.set(0, -1, 0).transformDirection(M);
    if (!init) { init = true; for (let i = 0; i < n; i++) { X[i * 3] = XP[i * 3] = w.x + d.x * L * i; X[i * 3 + 1] = XP[i * 3 + 1] = w.y + d.y * L * i; X[i * 3 + 2] = XP[i * 3 + 2] = w.z + d.z * L * i; } }
    const keep = Math.pow(.12, dt), g = 1.6 * S * dt * dt, fl = .55 * S * dt * dt;
    for (let i = 1; i < n; i++) { const j = i * 3, f = i / (n - 1);
      for (let c = 0; c < 3; c++) { const v = (X[j + c] - XP[j + c]) * keep; XP[j + c] = X[j + c]; X[j + c] += v + d.getComponent(c) * g + fl * f * Math.sin(t * (.9 + .17 * c) + i * .45 + k * 1.7 + c * 2.1); } }
    X[0] = XP[0] = w.x; X[1] = XP[1] = w.y; X[2] = XP[2] = w.z;
    for (let it = 0; it < 8; it++) for (let i = 0; i < n - 1; i++) { const a = i * 3, b = a + 3, dx = X[b] - X[a], dy = X[b + 1] - X[a + 1], dz = X[b + 2] - X[a + 2], dd = Math.hypot(dx, dy, dz) || 1e-6, e = (dd - L) / dd, wa = i ? .5 : 0, wb = i ? .5 : 1;
      X[a] += dx * e * wa; X[a + 1] += dy * e * wa; X[a + 2] += dz * e * wa; X[b] -= dx * e * wb; X[b + 1] -= dy * e * wb; X[b + 2] -= dz * e * wb; } }};
}
function ribbon(THREE, mat, seg, len, width, x0, z0, k) {
  const n = seg + 1, g = new THREE.BufferGeometry(), P = new Float32Array(n * 2 * 3), U = new Float32Array(n * 2 * 2), C = new Float32Array(n * 2 * 3).fill(1), N = new Float32Array(n * 2 * 3), I = [];
  for (let j = 0; j < n; j++) { U.set([0, j / seg, 1, j / seg], j * 4); N.set([0, 0, 1, 0, 0, 1], j * 6); if (j < seg) { const a = j * 2; I.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); } }
  g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.BufferAttribute(U, 2)); g.setAttribute('color', new THREE.BufferAttribute(C, 3)); g.setAttribute('normal', new THREE.BufferAttribute(N, 3)); g.setIndex(I);
  const m = new THREE.Mesh(g, mat); m.frustumCulled = false; const sim = chainSim(THREE, n, len, x0, .02, z0, k), T = new THREE.Vector3(), V = new THREE.Vector3(), Sd = new THREE.Vector3(), A = new THREE.Vector3(), B = new THREE.Vector3(), sc = new THREE.Vector3();
  return {m, root: sim.root, update() {}, chain(dt, t, pulse, M, inv, cam) { sim.step(dt, t, pulse, M); const X = sim.X, S = sc.setFromMatrixScale(M).x;
    for (let j = 0; j < n; j++) { const a = Math.min(j, n - 2) * 3; T.set(X[a + 3] - X[a], X[a + 4] - X[a + 1], X[a + 5] - X[a + 2]); A.set(X[j * 3], X[j * 3 + 1], X[j * 3 + 2]);
      if (cam) V.copy(cam).sub(A); else V.set(0, 0, 1).transformDirection(M); Sd.crossVectors(T, V); if (Sd.lengthSq() < 1e-10) Sd.set(1, 0, 0); Sd.setLength(width * (1 - .45 * j / seg) / 2 * S);
      B.copy(A).add(Sd).applyMatrix4(inv); A.sub(Sd).applyMatrix4(inv); P.set([A.x, A.y, A.z, B.x, B.y, B.z], j * 6); } g.attributes.position.needsUpdate = true; }};
}
function line(THREE, color, opacity, n, len, x0, z0, k) {
  const g = new THREE.BufferGeometry(), P = new Float32Array(n * 3); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); const mat = new THREE.LineBasicMaterial({color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false}), l = new THREE.Line(g, mat); l.frustumCulled = false;
  const sim = chainSim(THREE, n, len, x0, .02, z0, k), A = new THREE.Vector3();
  return {l, mat, root: sim.root, update() {}, chain(dt, t, pulse, M, inv) { sim.step(dt, t, pulse, M); for (let j = 0; j < n; j++) { A.set(sim.X[j * 3], sim.X[j * 3 + 1], sim.X[j * 3 + 2]).applyMatrix4(inv); P.set([A.x, A.y, A.z], j * 3); } g.attributes.position.needsUpdate = true; }};
}
// the jellies that came without tentacles of their own get the ones their versions swam with: threads in their own colour, a film strand or two
function threads(THREE, group, parts, n, color, opacity, len, r, y0, strands, mats) {
  for (let i = 0; i < n; i++) { const a = i / n * 6.283 + .2, L = line(THREE, color, opacity, 22, len * (.8 + .4 * ((i * 7) % 5) / 4), Math.cos(a) * r, Math.sin(a) * r, i); L.root.y = y0; group.add(L.l); parts.push(L); }
  if (strands) { const m = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: {uT: {value: 0}, uC: {value: new THREE.Color(color)}},
      vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
      fragmentShader: `uniform float uT; uniform vec3 uC; varying vec2 v; void main(){ float f = fract(v.y * 26. - uT * .4); if ((v.x < .16 || v.x > .84) && f > .5) discard; float frame = step(.08, fract(v.y * 9. - uT * .15)); vec3 c = uC * (v.x < .16 || v.x > .84 ? .5 : .28 * frame); gl_FragColor = vec4(c * (1. - v.y * .75), 1.); }`});
    mats.push(m); for (let i = 0; i < strands; i++) { const a = i / strands * 6.283 + 1, R = ribbon(THREE, m, 30, len * 1.15, .16, Math.cos(a) * r * .6, Math.sin(a) * r * .6, i + 9); R.root.y = y0; group.add(R.m); parts.push(R); } }
}
const lathe = (THREE, R, H, n = 40) => Array.from({length: n + 1}, (_, i) => { const t = i / n, a = t * Math.PI / 2 * 1.04; return new THREE.Vector2(Math.max(.001, R * Math.sin(a) * (1 + .06 * Math.sin(t * Math.PI))), H * Math.cos(a)); });

export function makeRig(THREE, id) {
  const group = new THREE.Group(), mats = [], parts = [], filmMats = [], inv = new THREE.Matrix4(); let norm = 1, k = 1, lastT = null;
  const pts = (geo, mat) => { const p = new THREE.Points(geo, mat); p.frustumCulled = false; group.add(p); mats.push(mat); return p; };
  const attrs = (n, fill) => { const g = new THREE.BufferGeometry(), P = new Float32Array(n * 3), T = new Float32Array(n), S = new Float32Array(n), L = new Float32Array(n); let m = 0; for (let i = 0; i < n * 4 && m < n; i++) if (fill(m, P, T, S, L) !== false) m++;
    g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aT', new THREE.BufferAttribute(T, 1)); g.setAttribute('aS', new THREE.BufferAttribute(S, 1)); g.setAttribute('aL', new THREE.BufferAttribute(L, 1)); g.setDrawRange(0, m); return g; };
  const blank = (() => { const c = document.createElement('canvas'); c.width = c.height = 4; const t = new THREE.CanvasTexture(c); return t; })();

  if (id === 'glass') {   // v1: the lathe moon jelly (its own shader, kept)
    const BR = 1.25, BH = .95; norm = .72;
    const prof = inner => { const pts = []; for (let i = 0; i <= 40; i++) { const t = i / 40, a = t * Math.PI / 2 * 1.04, kk = inner ? .9 : 1; pts.push(new THREE.Vector2(Math.max(.001, BR * Math.sin(a) * (1 + .06 * Math.sin(t * Math.PI))) * kk, BH * Math.cos(a) * kk - (inner ? .04 : 0))); } return pts; };
    const sh = inner => new THREE.ShaderMaterial({transparent: true, depthWrite: false, side: inner ? THREE.BackSide : THREE.FrontSide, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uTime: {value: 0}, uInk: {value: 0}, uImg: {value: blank}, uHasImg: {value: 0}, uGlow: {value: 0}},
      vertexShader: `uniform float uPulse, uTime; varying vec3 vN, vV, vP; varying float vT; ${PULSE}
        void main(){ vec3 p = position; float t = clamp(1. - p.y / ${BH.toFixed(3)}, 0., 1.); vT = t; float k = c(uPulse - t * .18) * pow(t, 1.4); p.xz *= 1. - .3 * k; p.y += .22 * k * (1. - t) + .08 * k; p.y += .02 * sin(atan(p.z, p.x) * 8. + uTime * 2.) * t;
          vec4 w = modelMatrix * vec4(p, 1.); vP = p; vN = normalize(normalMatrix * normal); vec4 mv = viewMatrix * w; vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uInk, uHasImg, uGlow, uTime; uniform sampler2D uImg; varying vec3 vN, vV, vP; varying float vT;
        void main(){ float fr = pow(1. - abs(dot(normalize(vN), vV)), 2.2); float th = atan(vP.z, vP.x); float canals = pow(abs(sin(th * 8.)), 60.) * smoothstep(.1, .9, vT) * .5; float g = 0.;
          for (int i = 0; i < 4; i++) { float a = float(i) * 1.5708 + .785; vec2 q = vec2(cos(a), sin(a)) * .42 - vP.xz / ${BR.toFixed(3)}; float d = length(q); g += smoothstep(.06, .0, abs(d - .16)) * smoothstep(-.2, .4, dot(normalize(q), vec2(cos(a), sin(a)))); }
          vec3 body = vec3(1., .76, .5), rim = vec3(1., .86, .64), gon = vec3(1., .5, .42); vec3 col = body * (.025 + .32 * fr) + rim * pow(vT, 6.) * .45 + gon * g * .38 + body * canals * .6;
          if (uHasImg > .5) { vec3 im = texture2D(uImg, vP.xz / ${(BR * 2.1).toFixed(3)} + .5).rgb; float lum = dot(im, vec3(.3, .55, .15)); col += vec3(1., .8, .55) * lum * .5 * (1. - vT); }
          col *= 1. + uGlow * 1.5; col = mix(col, vec3(.6, .07, .04) * (.2 + fr), uInk * .75); gl_FragColor = vec4(col * ${inner ? '.55' : '1.'}, .9); }`});
    for (const inner of [false, true]) { const m = sh(inner), mesh = new THREE.Mesh(new THREE.LatheGeometry(prof(inner), 96), m); group.add(mesh); mats.push(m); filmMats.push(m); }
    // four frilled oral arms, as v1's arms hung
    for (let a = 0; a < 4; a++) { const L = line(THREE, 0xffc07a, .35, 24, 1.8, Math.cos(a * 1.57 + .78) * .25, Math.sin(a * 1.57 + .78) * .25, a); group.add(L.l); parts.push(L); }
  }
  if (id === 'filmbell') {   // v2: the bell is the film you caught last
    const BR = 1.15, BH = .9; norm = .78; k = 1.25;
    const contract = `${PULSE} vec3 contract(vec3 p, float t, float pulse){ float k = c(pulse - t * .18) * pow(t, 1.4); p.xz *= 1. - .3 * k; p.y += .2 * k * (1. - t) + .07 * k; return p; }`;
    const BN = 3400, g = new THREE.BufferGeometry(), bp = new Float32Array(BN * 3), buv = new Float32Array(BN * 2), bt = new Float32Array(BN), bs = new Float32Array(BN);
    for (let i = 0; i < BN; i++) { const t = Math.sqrt(Math.random()), a = t * Math.PI / 2 * 1.04, ph = Math.random() * Math.PI * 2, rr = BR * Math.sin(a) * (1 + .06 * Math.sin(t * Math.PI)), y = BH * Math.cos(a), depth = Math.random() < .3 ? .82 + .18 * Math.random() : 1;
      bp.set([Math.cos(ph) * rr * depth, y * depth, Math.sin(ph) * rr * depth], i * 3); buv.set([.5 + Math.cos(ph) * rr / (BR * 2.1), .5 + Math.sin(ph) * rr / (BR * 2.1)], i * 2); bt[i] = t; bs[i] = Math.random(); }
    g.setAttribute('position', new THREE.BufferAttribute(bp, 3)); g.setAttribute('aUv', new THREE.BufferAttribute(buv, 2)); g.setAttribute('aT', new THREE.BufferAttribute(bt, 1)); g.setAttribute('aS', new THREE.BufferAttribute(bs, 1));
    const m = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uImg: {value: blank}, uHas: {value: 0}, uInk: {value: 0}, uGlow: {value: 0}, uScale: {value: 1}, uTime: {value: 0}},
      vertexShader: `uniform float uPulse, uScale, uTime; attribute vec2 aUv; attribute float aT, aS; varying vec2 vUv; varying float vT, vS; ${contract}
        void main(){ vec3 p = contract(position, aT, uPulse); p += .015 * vec3(sin(uTime * 2. + aS * 40.), cos(uTime * 1.7 + aS * 30.), sin(uTime * 1.3 + aS * 20.)); vUv = aUv; vT = aT; vS = aS; vec4 mv = modelViewMatrix * vec4(p, 1.); gl_PointSize = (2.2 + 3. * aS) * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform sampler2D uImg; uniform float uHas, uInk, uGlow; varying vec2 vUv; varying float vT, vS;
        void main(){ vec2 q = gl_PointCoord - .5; float g = exp(-dot(q, q) * 14.); vec3 im = texture2D(uImg, vUv).rgb; float l = dot(im, vec3(.3, .55, .15)); vec3 film = vec3(1., .82, .58) * (.15 + 1.1 * l), warm = vec3(1., .72, .45) * (.35 + .4 * vT);
          vec3 col = mix(warm, film, uHas) * (.55 + .7 * pow(vT, 4.)) * (1. + uGlow); col = mix(col, vec3(.7, .08, .04), uInk * .7); gl_FragColor = vec4(col * g * .27, 1.); }`});
    pts(g, m); filmMats.push(m);
    const shm = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: {uPulse: {value: 0}, uInk: {value: 0}},
      vertexShader: `uniform float uPulse; varying vec3 vN, vV; varying float vT; ${contract} void main(){ float t = clamp(1. - position.y / ${BH.toFixed(2)}, 0., 1.); vT = t; vec3 p = contract(position, t, uPulse); vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(p, 1.); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uInk; varying vec3 vN, vV; varying float vT; void main(){ float fr = pow(1. - abs(dot(normalize(vN), vV)), 2.6); vec3 c = vec3(1., .8, .58) * fr * (.35 + .5 * pow(vT, 5.)); c = mix(c, vec3(.6, .06, .03) * fr, uInk * .7); gl_FragColor = vec4(c, 1.); }`});
    group.add(new THREE.Mesh(new THREE.LatheGeometry(lathe(THREE, BR, BH, 32), 72), shm)); mats.push(shm);
  }
  if (id === 'mantle') {   // v3: a mantle of golden particles with a nervous system of light inside
    norm = .5; k = 1.6;
    const MN = 5200, g = attrs(MN, (i, P, T, S, L) => { const inner = i < MN * .22, y = inner ? -.5 + 2.1 * Math.pow(Math.random(), .8) : -.6 + 2.3 * Math.random(), t = (y + .6) / 2.3, rr = .95 * Math.sqrt(Math.max(0, 1 - Math.pow((y - .55) / 1.2, 2))) * (1 - .25 * t * t), a = Math.random() * 6.283;
      const rad = inner ? rr * (.15 + .35 * Math.abs(Math.sin(a * 3 + y * 4))) : rr * (.92 + .08 * Math.random()); P.set([Math.cos(a) * rad, y - .6, Math.sin(a) * rad], i * 3); T[i] = t; S[i] = Math.random(); L[i] = inner ? 1 : 0; });
    pts(g, new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uTime: {value: 0}, uScale: {value: 1}, uGlow: {value: 0}, uHurt: {value: 0}, uDash: {value: 0}},
      vertexShader: `uniform float uPulse, uTime, uScale, uDash; attribute float aT, aS, aL; varying float vT, vK, vS; float c(float ph){ ph = fract(ph); return ph < .25 ? sin(ph / .25 * 1.5708) : 1. - smoothstep(0., 1., (ph - .25) / .75); }
        void main(){ vec3 p = position; float k = c(uPulse - (1. - aT) * .35); p.xz *= 1. - .22 * k * (1. - aL * .5); p.y += .12 * k * aT; p += .025 * vec3(sin(uTime * 3. + aS * 50.), cos(uTime * 2.3 + aS * 31.), sin(uTime * 2.7 + aS * 17.)) * (1. + 2. * uDash);
          vT = aT; vK = aL; vS = aS; vec4 mv = modelViewMatrix * vec4(p, 1.); gl_PointSize = (1.6 + 2.6 * aS + aL * 1.5) * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uGlow, uHurt, uDash; varying float vT, vK, vS; void main(){ vec2 q = gl_PointCoord - .5; float g = exp(-dot(q, q) * 14.); vec3 skin = mix(vec3(1., .5, .16), vec3(1., .78, .42), vT), nerve = vec3(1., .93, .78);
        vec3 col = mix(skin * .55, nerve * 1.4, vK) * (1. + uGlow * 1.5 + uDash * .8); col = mix(col, vec3(1., .12, .05), uHurt * .6); gl_FragColor = vec4(col * g * .15, 1.); }`}));
  }
  if (id === 'golden') {   // v4 / v5: a golden jellyfish of light (bell of splats)
    norm = 1.02; k = 1.5;
    const BN = 4200, g = attrs(BN, (i, P, T, S) => { const t = Math.sqrt(Math.random()), a = t * Math.PI / 2 * 1.05, ph = Math.random() * 6.283, rr = .9 * Math.sin(a) * (1 + .06 * Math.sin(t * Math.PI)), y = .72 * Math.cos(a), inner = Math.random() < .25 ? .55 + .35 * Math.random() : 1;
      P.set([Math.cos(ph) * rr * inner, y * inner, Math.sin(ph) * rr * inner], i * 3); T[i] = t; S[i] = Math.random(); });
    pts(g, new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uTime: {value: 0}, uScale: {value: 1}, uGlow: {value: 0}, uHurt: {value: 0}, uWhite: {value: 0}, uA: {value: new THREE.Color(0xff9e38)}, uB: {value: new THREE.Color(0xffdb80)}},
      vertexShader: `uniform float uPulse, uTime, uScale; attribute float aT, aS; varying float vT, vS; ${PULSE}
        void main(){ vec3 p = position; float k = c(uPulse - aT * .18) * pow(aT, 1.4); p.xz *= 1. - .3 * k; p.y += .18 * k * (1. - aT) + .06 * k; p.y += .02 * sin(atan(p.z, p.x) * 8. + uTime * 2.) * aT; p += .012 * vec3(sin(uTime * 2. + aS * 40.), cos(uTime * 1.7 + aS * 30.), sin(uTime * 1.3 + aS * 20.)); vT = aT; vS = aS;
          vec4 mv = modelViewMatrix * vec4(p, 1.); gl_PointSize = (1.4 + 2.4 * aS) * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uGlow, uHurt, uWhite; uniform vec3 uA, uB; varying float vT, vS; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = (exp(-r2 * 14.) - .0302) / .9698;
        vec3 col = mix(uA, uB, pow(vT, 3.)) * (.55 + .8 * pow(vT, 5.)) * (1. + uGlow * 1.2); col = mix(col, vec3(1., .96, .9), uWhite * .35); col = mix(col, vec3(1., .12, .05), uHurt * .6); gl_FragColor = vec4(col * g * .2, 1.); }`}));
  }
  if (id === 'veil') {   // the landing's jelly: a veil of flecks with a perforated film band, a frame inside, a film-strip tentacle and filaments
    norm = .72; k = .5;
    const fl = (n, fill) => { const P = new Float32Array(n * 3), C = new Float32Array(n * 3), S = new Float32Array(n), A = new Float32Array(n); for (let i = 0; i < n; i++) fill(i, P, C, S, A); const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aC', new THREE.BufferAttribute(C, 3)); g.setAttribute('aS', new THREE.BufferAttribute(S, 1)); g.setAttribute('aA', new THREE.BufferAttribute(A, 1)); return g; };
    const fm = bend => new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uT: {value: 0}, uP: {value: 0}, uScale: {value: 1}, uGlow: {value: 0}},
      vertexShader: `attribute vec3 aC; attribute float aS, aA; uniform float uT, uP, uScale, uGlow; varying vec3 vC; varying float vA; void main(){ vec3 p = position; ${bend} vec4 mv = modelViewMatrix * vec4(p, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = aS * uScale / -mv.z; vC = aC; vA = min(1., aA * (1. + uGlow)); }`,
      fragmentShader: `varying vec3 vC; varying float vA; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = exp(-r2 * 14.); gl_FragColor = vec4(vC * vA * g * .45, 1.); }`});
    const blue = new THREE.Color('#86a6c6'), pale = new THREE.Color('#d7e6f3'), amber = new THREE.Color('#f2a453');
    const bm = fm(`float k = uP; p.xz *= 1. + .06 * k * (1. - p.y); p.y *= 1. - .08 * k;`);
    pts(fl(14000, (i, P, C, S, A) => { const u = Math.random(), ph = Math.random() * Math.PI * 2, th = Math.acos(1 - u * .98), rim = th / (Math.PI / 2), scal = rim > .9 ? .03 * Math.sin(ph * 22) : 0, r = (Math.sin(th) + scal) * 1.25, y = Math.cos(th) * .95 - .05, band = rim > .86 && rim < .93, hole = band && (ph * 40 / (Math.PI * 2)) % 1 < .38;
      P[i * 3] = Math.cos(ph) * r; P[i * 3 + 1] = band ? .11 - (rim - .86) * 1.6 : y; P[i * 3 + 2] = Math.sin(ph) * r; const c = blue.clone().lerp(pale, Math.pow(rim, 3) * .7), am = Math.max(0, Math.cos(ph) * .8 + .2) * Math.max(0, rim - .35); c.lerp(amber, Math.min(.85, am * 1.1));
      C.set([c.r, c.g, c.b], i * 3); S[i] = band ? 13 : 8 + Math.random() * 14; A[i] = hole ? 0 : band ? .2 : .045 + .11 * Math.pow(rim, 2.5) + .2 * am; }), bm);
    const am = fm(`p.x += sin(uT * .9 + p.y * 3.) * .08 * -p.y; p.z += cos(uT * .7 + p.y * 2.) * .06 * -p.y;`);
    pts(fl(2000, (i, P, C, S, A) => { const f = Math.random(), a = Math.random() * 6.283, r = .35 * (1 - f) * Math.random(); P.set([Math.cos(a) * r, -f * 1.4 + .05, Math.sin(a) * r], i * 3); const c = blue.clone().lerp(pale, .4); C.set([c.r, c.g, c.b], i * 3); S[i] = 10 + Math.random() * 16; A[i] = .05 * (1 - f); }), am);
    const fr = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {map: {value: blank}, uA: {value: 0}},
      vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
      fragmentShader: `uniform sampler2D map; uniform float uA; varying vec2 v; void main(){ vec3 c = texture2D(map, v).rgb; float l = dot(c, vec3(.3,.59,.11)); float e = smoothstep(.0, .18, v.x) * smoothstep(1., .82, v.x) * smoothstep(.0, .2, v.y) * smoothstep(1., .8, v.y); vec3 tone = mix(vec3(.15,.22,.3), vec3(1.,.72,.42), smoothstep(.15, .9, l)); gl_FragColor = vec4(tone * l * 1.5 * e * uA, 1.); }`});
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(1.25, .94), fr); plane.position.set(.05, .38, .1); group.add(plane); mats.push(fr); filmMats.push(fr); parts.push({update: () => {}, frame: fr});
    const strip = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, uniforms: {uT: {value: 0}},
      vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
      fragmentShader: `uniform float uT; varying vec2 v; void main(){ float hole = step(.82, v.x) * step(.5, fract(v.y * 30. - uT * .3)); if (hole > .5 || (v.x < .18 && fract(v.y * 30. - uT * .3) > .5)) discard; vec3 c = mix(vec3(.84, .9, .95), vec3(.95, .64, .33), .25 * (1. - v.y)); gl_FragColor = vec4(c * .28 * (1. - v.y * .7), 1.); }`});
    const R0 = ribbon(THREE, strip, 40, 2.9, .13, -.25, .2, 0); group.add(R0.m); parts.push(R0); mats.push(strip);
    [[-.65, -.2], [.1, .4], [.55, -.1]].forEach(([x, z], i) => { const L = line(THREE, 0x9fb9d4, .45, 30, 2.4 + i * .25, x, z, i + 1); group.add(L.l); parts.push(L); });
  }
  if (id === 'reel' || id === 'sentinel' || id === 'medusa') {   // the bonus pieces: a fresnel bell mesh (uv.x around, uv.y crown to rim) with their own shaders, and their tentacles
    norm = 1; const U = {uTime: {value: 0}, uFilmPhase: {value: 0}, uPulsePhase: {value: 0}, uPulse: {value: 0}, uEnergy: {value: 1}, uContam: {value: 0}, uSpiritDissolve: {value: .55},
      uCoreColor: {value: new THREE.Color(id === 'reel' ? 0x0ea5e9 : 0xd97706)}, uRimColor: {value: new THREE.Color(id === 'reel' ? 0xfacc15 : 0xfef08a)}, uPulseColor: {value: new THREE.Color(id === 'reel' ? 0x67e8f9 : 0xfde047)}, uGonadColor: {value: new THREE.Color(0xfde047)}, uEyeColor: {value: new THREE.Color(0xffedd5)},
      uBellColor: {value: new THREE.Color(0xf59e0b)}, uFogColor: {value: new THREE.Color(0x05080c)}, uFogDensity: {value: 0}};
    const vs = `varying vec3 vNormal; varying vec3 vViewPos; varying vec2 vUv; varying float vFogDepth; uniform float uPulse; ${PULSE} void main(){ vUv = uv; vec3 p = position; float k = c(uPulse - uv.y * .18) * pow(uv.y, 1.4); p.xz *= 1. - .28 * k; p.y += .14 * k * (1. - uv.y); vNormal = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(p, 1.); vViewPos = -mv.xyz; vFogDepth = -mv.z; gl_Position = projectionMatrix * mv; }`;
    const FS = {
      reel: `uniform float uTime, uFilmPhase, uPulsePhase, uEnergy, uContam; uniform vec3 uCoreColor, uRimColor, uPulseColor, uGonadColor; varying vec3 vNormal; varying vec3 vViewPos; varying vec2 vUv;
        void main(){ vec3 N = normalize(vNormal); vec3 V = normalize(vViewPos); float fresnel = pow(1.0 - abs(dot(N, V)), 2.2); float angle = vUv.x * 6.2831853; float radial = vUv.y;
          float canals = smoothstep(0.72, 0.98, 0.5 + 0.5 * cos(angle * 16.0)) * smoothstep(0.12, 0.92, radial); float lobeAngle = abs(sin(angle * 2.0)); float gonadMask = exp(-pow((radial - 0.30) / 0.07, 2.0)) * smoothstep(0.25, 0.85, lobeAngle);
          float sprocketHole = 0.0; if (radial > 0.88 && radial < 0.96) { float sCell = fract(vUv.x * 64.0 + uFilmPhase * 0.5); if (sCell > 0.25 && sCell < 0.75) sprocketHole = 1.0; }
          float wave = 0.5 + 0.5 * sin(radial * 10.0 - uPulsePhase * 6.2831853); vec3 col = mix(uCoreColor * 0.45, uRimColor, fresnel); col += uGonadColor * gonadMask * (0.75 + 0.35 * wave); col += uPulseColor * canals * (0.30 + 0.45 * wave * uEnergy);
          float rimBand = smoothstep(0.84, 1.0, radial) * (1.0 - sprocketHole * 0.85); col += uRimColor * rimBand * 0.65; col = mix(col, vec3(0.95, 0.15, 0.32), uContam * 0.65);
          float alpha = clamp((0.12 + fresnel * 0.46 + gonadMask * 0.32 + canals * 0.14 + rimBand * 0.22) * (1.0 - sprocketHole * 0.7), 0.06, 0.85); gl_FragColor = vec4(col * alpha, alpha); }`,
      sentinel: `uniform float uTime, uPulsePhase, uEnergy, uSpiritDissolve, uContam; uniform vec3 uCoreColor, uRimColor, uPulseColor, uEyeColor; varying vec3 vNormal; varying vec3 vViewPos; varying vec2 vUv;
        void main(){ vec3 N = normalize(vNormal); vec3 V = normalize(vViewPos); float fresnel = pow(1.0 - abs(dot(N, V)), 1.9); float angle = vUv.x * 6.2831853; float radial = vUv.y;
          float ribs = smoothstep(0.60, 0.98, 0.5 + 0.5 * cos(angle * 18.0)) * smoothstep(0.08, 0.94, radial); float microPlates = 0.5 + 0.5 * sin(radial * 42.0 + cos(angle * 9.0) * 2.0);
          float eyeRing1 = exp(-pow((radial - 0.28) / 0.042, 2.0)) * smoothstep(0.76, 0.97, cos(angle * 8.0)); float eyeRing2 = exp(-pow((radial - 0.44) / 0.038, 2.0)) * smoothstep(0.80, 0.98, cos(angle * 12.0 + 0.3)); float eyes = (eyeRing1 + eyeRing2) * 1.9;
          float wave = 0.5 + 0.5 * sin(radial * 10.0 - uPulsePhase * 6.2831853); vec3 metalHull = mix(vec3(0.06, 0.10, 0.14), uCoreColor * 0.55, microPlates * 0.6) + uRimColor * fresnel * 0.55;
          vec3 spiritGold = mix(uCoreColor, uRimColor, fresnel) + uPulseColor * ribs * (0.45 + 0.55 * wave * uEnergy); vec3 col = mix(metalHull, spiritGold, uSpiritDissolve); col += uEyeColor * eyes * (1.2 + 0.4 * sin(uTime * 6.0)); col = mix(col, vec3(0.98, 0.12, 0.28), uContam * 0.7);
          float alpha = clamp(mix(0.68, 0.26, uSpiritDissolve) + fresnel * 0.42 + eyes * 0.5 + ribs * 0.14, 0.14, 0.94); gl_FragColor = vec4(col * alpha * .8, alpha); }`,
      medusa: `uniform float uTime, uPulsePhase, uContam; uniform vec3 uBellColor, uRimColor; varying vec3 vNormal; varying vec3 vViewPos; varying vec2 vUv;
        void main(){ vec3 N = normalize(vNormal); vec3 V = normalize(vViewPos); float fresnel = pow(1.0 - abs(dot(N, V)), 1.8); float angle = vUv.x * 6.2831853; float radial = vUv.y; float ribs = smoothstep(0.55, 0.96, 0.5 + 0.5 * cos(angle * 16.0));
          float innerRing = exp(-pow((radial - 0.35) / 0.12, 2.0)); float rimGlow = smoothstep(0.80, 1.0, radial); vec3 col = mix(uBellColor * 0.75, uRimColor, fresnel * 0.7 + innerRing * 0.5); col += uRimColor * ribs * 0.38; col = mix(col, vec3(0.95, 0.18, 0.25), uContam * 0.7);
          float alpha = clamp(0.22 + fresnel * 0.38 + ribs * 0.18 + rimGlow * 0.20, 0.16, 0.78); gl_FragColor = vec4(col * alpha, alpha); }`};
    const bm = new THREE.ShaderMaterial({uniforms: U, vertexShader: vs, fragmentShader: FS[id], transparent: true, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending});
    const R = id === 'medusa' ? .82 : .92, H = id === 'sentinel' ? .95 : id === 'medusa' ? .58 : .7;
    group.add(new THREE.Mesh(new THREE.LatheGeometry(lathe(THREE, R, H, 36), 64), bm)); mats.push(bm);
    if (id === 'medusa') norm = 1.1;
    if (id === 'reel' || id === 'sentinel') {   // 35 mm film strips with gold splices / segmented timeworms with vertebral rings
      const tfs = id === 'reel' ? `uniform float uFilmPhase, uEnergy; uniform vec3 uCoreColor, uRimColor, uPulseColor; varying vec2 vUv; varying vec3 vColor;
          void main(){ float x = vUv.x; float y = vUv.y; float taper = 1.0 - pow(y, 1.65); bool inSprocketTrack = (x < 0.16 || x > 0.84); float sprocketRepeat = fract(y * 38.0 - uFilmPhase * 2.2);
            bool isSprocketHole = inSprocketTrack && (x > 0.04 && x < 0.12 || x > 0.88 && x < 0.96) && (sprocketRepeat > 0.28 && sprocketRepeat < 0.72); if (isSprocketHole) discard;
            float frameCoord = y * 11.0 - uFilmPhase * 0.55; float frameFract = fract(frameCoord); float frameIdx = floor(frameCoord); bool isFrameLine = !inSprocketTrack && (frameFract < 0.07 || frameFract > 0.93); float isGoldCut = (isFrameLine && mod(abs(frameIdx), 3.0) < 0.5) ? 1.0 : 0.0;
            vec2 cellUv = vec2((x - 0.16) / 0.68, (frameFract - 0.07) / 0.86); vec2 gridUv = floor(cellUv * vec2(10.0, 8.0)) / vec2(10.0, 8.0); vec2 subCell = fract(cellUv * vec2(10.0, 8.0)) - 0.5; float dotMask = smoothstep(0.46, 0.18, length(subCell));
            float pattern = 0.5 + 0.5 * sin(gridUv.x * 6.28 + frameIdx * 1.7 + uFilmPhase * 1.8) * cos(gridUv.y * 6.28 - uFilmPhase * 1.4); float fleckGlow = (!inSprocketTrack && !isFrameLine) ? (dotMask * pattern) : 0.0;
            vec3 col = vColor * 0.12; if (inSprocketTrack) { col = mix(uCoreColor * 0.6, uRimColor, 0.55); } else if (isFrameLine) { col = mix(uCoreColor * 0.25, vec3(1.0, 0.88, 0.32), isGoldCut * 0.95); } else { col += mix(uPulseColor, vec3(1.0, 0.92, 0.48), pattern * 0.6) * fleckGlow * (0.9 + 0.5 * uEnergy); }
            float alpha = (inSprocketTrack ? 0.58 : (isFrameLine ? (0.35 + isGoldCut * 0.55) : (0.18 + fleckGlow * 0.72))) * taper; gl_FragColor = vec4(col * clamp(alpha, 0.0, 0.92) * .8, 1.); }`
        : `uniform float uFilmPhase; uniform vec3 uRimColor, uPulseColor, uEyeColor; varying vec2 vUv;
          void main(){ float x = vUv.x; float y = vUv.y; float taper = 1.0 - pow(y, 1.75); bool inTrack = (x < 0.15 || x > 0.85); float perf = fract(y * 34.0 - uFilmPhase * 1.8); if (inTrack && (x > 0.04 && x < 0.11 || x > 0.89 && x < 0.96) && perf > 0.3 && perf < 0.7) discard;
            float segCoord = y * 18.0 - uFilmPhase * 0.65; float segFract = fract(segCoord); float segIdx = floor(segCoord); float vertebralRing = smoothstep(0.16, 0.0, abs(segFract - 0.5) - 0.34);
            vec2 cellUv = vec2((x - 0.15) / 0.70, segFract); vec2 gridUv = floor(cellUv * vec2(8.0, 6.0)) / vec2(8.0, 6.0); vec2 subCell = fract(cellUv * vec2(8.0, 6.0)) - 0.5; float dotMask = smoothstep(0.46, 0.16, length(subCell));
            float videoPixel = 0.5 + 0.5 * sin(gridUv.x * 6.28 + segIdx * 1.4 - uFilmPhase * 2.2) * cos(gridUv.y * 6.28 + uFilmPhase * 1.6); float fleckGlow = (!inTrack) ? (dotMask * videoPixel) : 0.0;
            vec3 col = inTrack ? uRimColor * .45 : uPulseColor * fleckGlow * .9; col += uEyeColor * vertebralRing * .5; gl_FragColor = vec4(col * (.2 + .3 * fleckGlow + .2 * vertebralRing) * taper, 1.); }`;
      const tm = new THREE.ShaderMaterial({uniforms: U, vertexShader: `attribute vec3 color; varying vec2 vUv; varying vec3 vColor; void main(){ vUv = uv; vColor = color; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`, fragmentShader: tfs, transparent: true, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending});
      mats.push(tm); const n = id === 'reel' ? 6 : 5; for (let i = 0; i < n; i++) { const a = i / n * 6.283 + .3, r = R * .62; const rb = ribbon(THREE, tm, 36, id === 'reel' ? 2.8 : 2.4, id === 'reel' ? .2 : .17, Math.cos(a) * r, Math.sin(a) * r, i); group.add(rb.m); parts.push(rb); }
    }
    if (id === 'medusa') { const lines = []; for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283, L = line(THREE, 0xf59e0b, .42, 14, 2.1, Math.cos(a) * .78, Math.sin(a) * .78, i); group.add(L.l); parts.push(L); lines.push(L); } parts.push({update: (t, p, s) => lines.forEach((L, i) => { const on = i < (s.lit || 0); L.mat.color.set(on ? 0xf1f5f9 : 0xf59e0b); L.mat.opacity = on ? .95 : .4; })}); }
    parts.push({update: (t, p, s) => { U.uTime.value = t; U.uFilmPhase.value = t * .8 + (s.lit || 0); U.uPulsePhase.value = s.ph; U.uPulse.value = s.ph; U.uEnergy.value = 1 + s.glow; U.uContam.value = s.hurt; }});
  }
  if (id === 'doodle') {   // bonus worms: a bell of hand-drawn rib strokes, a drawing in its crown, raw doodle tentacles
    const BELL_R = 1.05; norm = .86; const ribs = [];
    for (let r = 0; r < 18; r++) { const phi = r / 18 * Math.PI * 2, P = []; for (let s = 0; s <= 14; s++) { const th = s / 14 * Math.PI * .68, j = Math.sin(r * 7 + s * 3) * .025; P.push(new THREE.Vector3(Math.cos(phi) * Math.sin(th) * (BELL_R + j), Math.cos(th) * (BELL_R * .88 + j) - .35, Math.sin(phi) * Math.sin(th) * (BELL_R + j))); }
      const g = new THREE.BufferGeometry().setFromPoints(P), orig = g.attributes.position.array.slice(), mat = new THREE.LineBasicMaterial({color: r % 2 === 0 ? 0xfacc15 : 0x38bdf8, transparent: true, opacity: .92}), l = new THREE.Line(g, mat); group.add(l); ribs.push({g, orig}); }
    for (let q = 1; q <= 5; q++) { const th = q / 6 * Math.PI * .68, P = []; for (let s = 0; s <= 48; s++) { const phi = s / 48 * Math.PI * 2, j = Math.sin(s * 5 + q * 2) * .02; P.push(new THREE.Vector3(Math.cos(phi) * Math.sin(th) * (BELL_R + j), Math.cos(th) * BELL_R * .88 - .35, Math.sin(phi) * Math.sin(th) * (BELL_R + j))); } group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(P), new THREE.LineBasicMaterial({color: 0xe2e8f0, transparent: true, opacity: .35}))); }
    const dm = new THREE.MeshBasicMaterial({map: blank, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending}), core = new THREE.Mesh(new THREE.PlaneGeometry(1.2, .9), dm); core.position.set(0, .05, 0); group.add(core); filmMats.push(dm);
    const cols = [0xfacc15, 0x38bdf8, 0xf472b6, 0x4ade80, 0xfb923c, 0xa78bfa], tl = []; for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283, L = line(THREE, cols[i % 6], .3, 16, 2.6, Math.cos(a) * .65, Math.sin(a) * .65, i); L.root.y = -.35; group.add(L.l); parts.push(L); tl.push(L); }
    parts.push({update: (t, p, s) => { for (const R of ribs) { const a = R.g.attributes.position.array; for (let i = 0; i < a.length; i += 3) { const y = R.orig[i + 1] + .35, kk = (1 - y / BELL_R) * p * .25; a[i] = R.orig[i] * (1 - kk) + Math.sin(t * 6 + i) * .004; a[i + 2] = R.orig[i + 2] * (1 - kk); a[i + 1] = R.orig[i + 1] + kk * .2; } R.g.attributes.position.needsUpdate = true; }
      tl.forEach((L, i) => L.mat.opacity = i < (s.lit || 0) ? .95 : .3); }});
  }
  if (id === 'filmbell') threads(THREE, group, parts, 6, 0xffc58a, .3, 2.2, .85, .05, 2, mats);
  if (id === 'golden') threads(THREE, group, parts, 10, 0xffb347, .32, 2.3, .7, .02, 0, mats);
  if (id === 'mantle') threads(THREE, group, parts, 8, 0xffa850, .35, 1.8, .45, -.55, 2, mats);
  if (id === 'celluloid') {   // v6 / v7: three celluloid sheets with sprocket holes, contracting one after another (the engine draws its own; this is for the gallery)
    norm = 1; threads(THREE, group, parts, 6, 0xffb35a, .3, 2.2, .78, .02, 2, mats); const BN = 5000, g = attrs(BN, (k2, P, T, S, L) => { const ly = k2 < 1250 ? 0 : k2 < 2900 ? 1 : 2, rad = [.62, .78, .92][ly], t = Math.sqrt(Math.random()), a = t * Math.PI / 2 * 1.05, ph = Math.random() * 6.283;
      if ((t > .86 && Math.floor(ph / 6.283 * 44) % 2 === 0 && Math.random() < .85) || (Math.abs(((ph / 6.283 * 8) % 1) - .5) < .025 && Math.random() < .7)) return false;
      P.set([Math.cos(ph) * rad * Math.sin(a), rad * .8 * Math.cos(a), Math.sin(ph) * rad * Math.sin(a)], k2 * 3); T[k2] = t; S[k2] = Math.random(); L[k2] = ly; });
    pts(g, new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uTime: {value: 0}, uScale: {value: 1}, uGlow: {value: 0}, uHurt: {value: 0}},
      vertexShader: `uniform float uPulse, uTime, uScale; attribute float aT, aS, aL; varying float vT, vS, vL; ${PULSE}
        void main(){ vec3 p = position; float k = c(uPulse - aT * .18 - aL * .06) * pow(aT, 1.3); p.xz *= 1. - .3 * k; p.y += .16 * k * (1. - aT) + .05 * k; vT = aT; vS = aS; vL = aL; vec4 mv = modelViewMatrix * vec4(p, 1.); gl_PointSize = (1.6 + 2.2 * aS) * (1.15 - .15 * aL) * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform float uGlow, uHurt; varying float vT, vS, vL; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = (exp(-r2 * 14.) - .0302) / .9698;
        vec3 col = vL < .5 ? vec3(1., .5, .12) : vL < 1.5 ? vec3(1., .72, .3) : vec3(1., .9, .66); if (vL > 1.5) col += vec3(-.05, .03, .08) * sin(vS * 40.); col *= (.45 + .9 * pow(vT, 4.)) * (1. + uGlow) * (vL > 1.5 ? .7 : 1.); col = mix(col, vec3(1., .12, .05), uHurt * .6); gl_FragColor = vec4(col * g * .24, 1.); }`})); }

  return {group, norm, k, update(s) { const p = pulseC(s.ph); for (const m of mats) { const u = m.uniforms; if (!u) continue; if (u.uPulse) u.uPulse.value = s.ph; if (u.uP) u.uP.value = p; if (u.uTime) u.uTime.value = s.t; if (u.uT) u.uT.value = s.t; if (u.uGlow) u.uGlow.value = s.glow; if (u.uHurt) u.uHurt.value = s.hurt; if (u.uInk) u.uInk.value = s.hurt * .6; if (u.uScale) u.uScale.value = s.scale * k; }
      const dt = Math.min(.05, Math.max(0, s.dt ?? (s.t - (lastT ?? s.t)))); lastT = s.t; group.updateWorldMatrix(true, false); const M = group.matrixWorld; inv.copy(M).invert();
      for (const q of parts) { if (q.chain) q.chain(dt || 1 / 60, s.t, p, M, inv, s.cam); else q.update(s.t, p, s); } },
    setFilm(tex) { for (const m of filmMats) { if (m.uniforms) { if (m.uniforms.uImg) { m.uniforms.uImg.value = tex || blank; } if (m.uniforms.uHasImg) m.uniforms.uHasImg.value = tex ? 1 : 0; if (m.uniforms.uHas) m.uniforms.uHas.value = tex ? 1 : 0; if (m.uniforms.map) m.uniforms.map.value = tex || blank; if (m.uniforms.uA) m.uniforms.uA.value = tex ? .85 : 0; } else { m.map = tex || blank; m.opacity = tex ? .5 : 0; m.needsUpdate = true; } } },
    dispose() { group.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); }};
}
