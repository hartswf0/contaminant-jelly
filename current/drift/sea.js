// SEA: the animals that eat jellies, and the seas that join the levels of one family.
// Each predator is a cloud of points with its own gait (flippers, fins, wings, legs), a zone of the water
// (open, floor, surface), and a way of taking from the jelly: an arm (and the film it holds), the stings, the membrane.
// Biology, kept as rules: leatherbacks eat jellies almost only and their throats are lined with spines, so the stings
// do nothing to them (outrun them; they turn slowly); hawksbills have thick skin (also immune); the ocean sunfish grazes
// slowly; tuna, chum salmon and triggerfish dart in and can be stung away; seabirds take from the surface; crabs tear
// at a weakened jelly on the floor; nudibranchs steal stinging cells; the dinnerplate jelly eats other jellies and carries
// what it took until you sting it; humpbacks gulp a whole patch of water.

const R = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(91);
// ---------------------------------------------------------------- the bodies: parts encoded in aK (0 body, 1/2 left/right limb, 3 tail, 4 eye, 5/6 vertical fins), fract = how far out
function body(P, K, n, rx, ry, rz, cz = 0, k = 0, top = 1) { for (let i = 0; i < n; i++) { const u = R() * 6.283, v = Math.acos(2 * R() - 1), y = Math.cos(v) * ry; if (y < 0 && top < 1) continue; P.push(Math.sin(v) * Math.cos(u) * rx, y * (y < 0 ? top : 1), cz + Math.sin(v) * Math.sin(u) * rz); K.push(k); } }
function limb(P, K, n, side, x0, z0, span, chord, sweep, part) { for (let i = 0; i < n; i++) { const t = R(), c = (R() - .5) * chord * (1 - t * .7); P.push(side * (x0 + t * span), (R() - .5) * .05, z0 - t * sweep + c); K.push(part + Math.min(.99, t)); } }
function line(P, K, n, a, b, part, jit = .03) { for (let i = 0; i < n; i++) { const t = R(); P.push(a[0] + (b[0] - a[0]) * t + (R() - .5) * jit, a[1] + (b[1] - a[1]) * t + (R() - .5) * jit, a[2] + (b[2] - a[2]) * t + (R() - .5) * jit); K.push(part + Math.min(.99, t)); } }
const SHAPES = {
  turtle(ridge, sc) { const P = [], K = []; body(P, K, 900, 1.05, .42, 1.55, 0, 0); if (ridge) for (let r = -3; r <= 3; r++) line(P, K, 70, [r * .3, .4 - Math.abs(r) * .05, 1.4], [r * .22, .38 - Math.abs(r) * .05, -1.5], 0, .02);
    else for (let i = 0; i < 160; i++) { const a = R() * 6.283, rr = .3 + (i % 3) * .3; P.push(Math.cos(a) * rr, .43, Math.sin(a) * rr * 1.4); K.push(0); }
    body(P, K, 160, .36, .3, .42, 1.95, 0); for (const sd of [-1, 1]) { limb(P, K, 260, sd, .8, .9, 1.7 * sc, .5, .8, sd < 0 ? 1 : 2); limb(P, K, 90, sd, .7, -1.2, .6, .35, .4, sd < 0 ? 1 : 2); P.push(sd * .2, .2, 2.3); K.push(4); }
    line(P, K, 40, [0, 0, -1.5], [0, 0, -2], 3); return {P, K}; },
  mola() { const P = [], K = []; body(P, K, 1300, .28, 1.9, 1.6, 0, 0); line(P, K, 220, [0, 1.6, -.6], [0, 3.6, -1.3], 5, .3); line(P, K, 220, [0, -1.6, -.6], [0, -3.6, -1.3], 6, .3); for (let i = 0; i < 160; i++) { const a = (R() - .5) * 2.6; P.push((R() - .5) * .1, Math.sin(a) * 1.8, -1.6 - R() * .25); K.push(3.5); } P.push(.25, .5, 1.3, -.25, .5, 1.3); K.push(4, 4); return {P, K}; },
  fish(len, deep) { const P = [], K = []; body(P, K, 520, .3 * len, deep * len, 1 * len, 0, 0); for (const sd of [-1, 1]) line(P, K, 110, [0, sd * .1 * len, -.9 * len], [0, sd * .75 * len, -1.4 * len], 3, .05); line(P, K, 70, [0, deep * len, .1], [0, (deep + .5) * len, -.5 * len], 0, .08); for (const sd of [-1, 1]) { limb(P, K, 60, sd, .28 * len, .2 * len, .5 * len, .15 * len, .3 * len, sd < 0 ? 1 : 2); P.push(sd * .2 * len, .12 * len, .75 * len); K.push(4); } return {P, K}; },
  sealion() { const P = [], K = []; body(P, K, 900, .5, .55, 1.6, 0, 0); body(P, K, 220, .32, .32, .45, 1.8, 0); for (const sd of [-1, 1]) { limb(P, K, 160, sd, .45, .5, 1, .5, .5, sd < 0 ? 1 : 2); line(P, K, 60, [sd * .2, -.2, -1.5], [sd * .55, -.1, -2.2], 3); P.push(sd * .15, .15, 2.2); K.push(4); } return {P, K}; },
  bird() { const P = [], K = []; body(P, K, 260, .25, .22, .7, 0, 0); body(P, K, 70, .13, .13, .2, .8, 0); for (const sd of [-1, 1]) { limb(P, K, 380, sd, .2, .2, 2.4, .5, .6, sd < 0 ? 1 : 2); P.push(sd * .07, .05, .95); K.push(4); } line(P, K, 60, [0, 0, -.7], [0, 0, -1.1], 3, .2); return {P, K}; },
  crab() { const P = [], K = []; body(P, K, 650, 1.1, .32, .75, 0, 0, .3); for (const sd of [-1, 1]) for (let l = 0; l < 4; l++) { const z = .4 - l * .3; line(P, K, 50, [sd * .9, 0, z], [sd * 1.7, .35, z - .1], sd < 0 ? 1 : 2); line(P, K, 50, [sd * 1.7, .35, z - .1], [sd * 2.2, -.4, z - .2], sd < 0 ? 1.5 : 2.5); }
    for (const sd of [-1, 1]) { line(P, K, 70, [sd * .6, 0, .7], [sd * .9, .2, 1.4], 4.2); body(P, K, 90, .25, .14, .3, 1.55, 0); P.push(sd * .25, .45, .7); K.push(4); } return {P, K}; },
  nudi() { const P = [], K = []; body(P, K, 380, .3, .22, 1.2, 0, 0, .3); for (let i = 0; i < 46; i++) { const z = -1 + i / 46 * 1.9, sd = i % 2 ? 1 : -1; line(P, K, 14, [sd * .12, .15, z], [sd * (.4 + R() * .2), .55 + R() * .3, z - .1], 3); } for (const sd of [-1, 1]) { line(P, K, 22, [sd * .1, .1, 1.1], [sd * .25, .5, 1.4], 4.5); } return {P, K}; },
  plate() { const P = [], K = []; for (let i = 0; i < 900; i++) { const a = R() * 6.283, r = Math.sqrt(R()) * 2.1; P.push(Math.cos(a) * r, .5 * (1 - (r / 2.1) ** 2) + (R() - .5) * .05, Math.sin(a) * r); K.push(0); }
    for (let t = 0; t < 24; t++) { const a = t / 24 * 6.283; line(P, K, 40, [Math.cos(a) * 2, 0, Math.sin(a) * 2], [Math.cos(a) * 2.3, -5.5, Math.sin(a) * 2.3], 3, .05); } for (let t = 0; t < 4; t++) { const a = t / 4 * 6.283 + .4; line(P, K, 60, [Math.cos(a) * .4, 0, Math.sin(a) * .4], [Math.cos(a) * .8, -3, Math.sin(a) * .8], 3.3, .25); } return {P, K}; },
  whale() { const P = [], K = []; body(P, K, 2600, 1.6, 1.4, 6, 0, 0); for (let i = 0; i < 300; i++) { const x = (R() - .5) * 2.4; P.push(x, -1.2 + Math.abs(x) * .2, 1 + R() * 4.5); K.push(0); } for (const sd of [-1, 1]) { limb(P, K, 500, sd, 1.3, 2.5, 4.6, .8, 2.2, sd < 0 ? 1 : 2); limb(P, K, 260, sd, .2, -6, 2, .7, .9, 3); P.push(sd * 1.1, .2, 4.6); K.push(4); } return {P, K}; },
};
// ---------------------------------------------------------------- the species: zone, speed, senses, what it takes
export const SPECIES = {
  leatherback: {note: 'eats jellies almost only; spines line its throat, so stings do nothing. It turns slowly: outrun it.', name: 'a leatherback turtle', shape: () => SHAPES.turtle(true, 1.25), scale: 1.25, zone: 'open', speed: 5.4, turn: .55, sense: 18, bite: 2.6, arms: 1, dmg: 14, immune: true, flap: 1.1, rate: 1.6, col: [.42, .5, .55],
    warn: 'a leatherback turtle: it eats jellies, and stings mean nothing to its spined throat. Outrun it: it turns slowly', bit: 'the leatherback tore away'},
  hawksbill: {note: "a reef turtle with thick skin: stings don't stop it. Swim wide of it.", name: 'a hawksbill turtle', shape: () => SHAPES.turtle(false, .9), scale: .85, zone: 'open', speed: 4.6, turn: 1.2, sense: 13, bite: 2.1, arms: 1, dmg: 10, immune: true, flap: 1, rate: 2.2, col: [.55, .46, .34],
    warn: 'a hawksbill: thick skin, your stings won’t stop it. Swim wide', bit: 'the hawksbill bit off'},
  mola: {note: 'the ocean sunfish grazes slowly on jellies. Slip past; it barely turns.', name: 'an ocean sunfish', shape: SHAPES.mola, scale: 1.1, zone: 'open', speed: 2.2, turn: .4, sense: 12, bite: 3.2, arms: 1, dmg: 8, flap: .9, rate: .9, col: [.5, .55, .6], slow: true,
    warn: 'an ocean sunfish drifts in to graze: slip past it', bit: 'the sunfish grazed off'},
  tuna: {note: 'a fast pass along a straight line. Dodge sideways, or sting it as it comes.', name: 'a tuna', shape: () => SHAPES.fish(1.2, .42), scale: 1, zone: 'open', speed: 12, turn: 2.6, sense: 22, bite: 1.8, arms: 1, dmg: 8, flap: .5, rate: 6, col: [.38, .46, .58], passer: true,
    warn: 'tuna: a fast pass is coming. Pulse to sting it off, or dodge', bit: 'a tuna snatched'},
  salmon: {note: "the chum salmon's stomach swells to hold jellies; it takes two arms. Sting it.", name: 'a chum salmon', shape: () => SHAPES.fish(.8, .3), scale: .9, zone: 'open', speed: 8, turn: 2.2, sense: 15, bite: 1.6, arms: 2, dmg: 6, flap: .5, rate: 5, col: [.55, .45, .48],
    warn: 'a chum salmon, its stomach made to swell with jellies: pulse it away', bit: 'the salmon gulped'},
  trigger: {note: 'the grey triggerfish picks at arms. A sting sends it off.', name: 'a grey triggerfish', shape: () => SHAPES.fish(.6, .55), scale: .8, zone: 'open', speed: 7, turn: 3, sense: 11, bite: 1.4, arms: 1, dmg: 5, flap: .6, rate: 7, col: [.5, .52, .5],
    warn: 'a triggerfish picks at jellies: pulse', bit: 'the triggerfish nipped off'},
  sealion: {note: 'fast and playful. A sting on the nose turns it away.', name: 'a sea lion', shape: SHAPES.sealion, scale: 1, zone: 'open', speed: 9.5, turn: 3.2, sense: 16, bite: 2.2, arms: 1, dmg: 10, flap: 1, rate: 3, col: [.45, .4, .36],
    warn: 'a sea lion, playful and fast: pulse to sting its nose', bit: 'the sea lion tore off'},
  seabird: {note: 'fulmars, albatrosses and auklets take jellies at the surface. Stay deep when one circles.', name: 'a seabird', names: ['a northern fulmar', 'an albatross', 'a parakeet auklet'], shape: SHAPES.bird, scale: 1, zone: 'surface', speed: 14, turn: 4, sense: 6, bite: 2.6, arms: 1, dmg: 6, flap: 1.2, rate: 3.2, col: [.75, .78, .8], diver: true,
    warn: 'circles at the surface: dive, stay deep', bit: 'took from the surface'},
  crab: {note: 'arrow and hermit crabs tear at weakened jellies on the floor: keep off it when your membrane is low.', name: 'a crab', shape: SHAPES.crab, scale: .8, zone: 'floor', speed: 3.2, turn: 2, sense: 7, bite: 2, arms: 1, dmg: 8, flap: .35, rate: 6, col: [.6, .38, .3], weak: 70,
    warn: 'crabs tear at a weakened jelly: keep off the floor', bit: 'a crab tore away'},
  nudibranch: {note: "eats jellies and keeps their stinging cells. Touch one and you can't sting for a while.", name: 'a nudibranch', shape: SHAPES.nudi, scale: .7, zone: 'floor', speed: 1.2, turn: 1, sense: 5, bite: 1.8, arms: 0, dmg: 0, steal: 'sting', flap: .3, rate: 2, col: [.95, .5, .75],
    warn: 'a nudibranch: it steals stinging cells. Don’t touch it', bit: 'the nudibranch stole your stings'},
  dinnerplate: {note: 'a jelly that eats jellies, and carries what it takes. Sting it and it lets your film go.', name: 'a dinnerplate jelly', shape: SHAPES.plate, scale: 1, zone: 'open', speed: 2.6, turn: .8, sense: 14, bite: 3, arms: 1, dmg: 6, steal: 'arm', flap: .25, rate: 1, col: [.95, .72, .45],
    warn: 'a dinnerplate jelly: it eats other jellies. Sting it and it lets go of what it took', bit: 'the dinnerplate jelly wrapped up'},
  humpback: {note: 'a baleen whale that gulps whole patches of water and two arms with them. Get out of its line when it sings.', name: 'a humpback whale', shape: SHAPES.whale, scale: 1.3, zone: 'open', speed: 6.5, turn: .3, sense: 30, bite: 5, arms: 2, dmg: 18, immune: true, flap: .5, rate: .6, col: [.34, .4, .48], gulp: true,
    warn: 'a humpback sings below you: it gulps whole patches of water. Get out of its line', bit: 'the humpback gulped'},
};
// ---------------------------------------------------------------- one material for all: soft points, limbs that beat, eyes that light when it hunts
function mat(THREE, sp, fogD) { return new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.NormalBlending,
  uniforms: {uScale: {value: 1}, uTime: {value: 0}, uFog: {value: fogD}, uA: {value: .4}, uHunt: {value: 0}, uFlap: {value: sp.flap}, uRate: {value: sp.rate}, uCol: {value: new THREE.Vector3(...sp.col)}},
  vertexShader: `uniform float uScale, uTime, uFog, uFlap, uRate; attribute float aK; varying float vA, vP; void main(){ vec3 p = position; float part = floor(aK), t = fract(aK) + .01, w = sin(uTime * uRate) * uFlap;
    if (part == 1. || part == 2.) p.y += w * abs(p.x) * .55; if (part == 3.) p.x += sin(uTime * uRate * 1.3 + p.z * 1.7 + p.y) * .18 * t * 3.; if (part == 5. || part == 6.) p.x += w * abs(p.y) * .2;
    vec4 mv = modelViewMatrix * vec4(p, 1.); float z = -mv.z; vP = part; vA = exp(-pow(uFog * .8 * z, 2.)) * smoothstep(1.2, 4., z); gl_PointSize = max(1., (part == 4. ? .34 : .13) * uScale / z); gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `uniform float uA, uHunt; uniform vec3 uCol; varying float vA, vP; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; vec3 c = uCol * (vP == 3. ? .8 : 1.);
    float a = vA * (1. - 4. * r2) * uA; if (vP == 4.) { gl_FragColor = vec4(mix(vec3(.25), vec3(1., .5, .18), uHunt) * (1. + 2. * uHunt), a * (.4 + .6 * uHunt)); return; }
    gl_FragColor = vec4(c * (.16 + .12 * (1. - r2 * 4.)), a * .55); }`}); }   // a dark silhouette against the haze; only the eyes light, when it hunts

// ---------------------------------------------------------------- the hunters, in level coordinates (u along the current, w across it)
export function makePredators(C) {
  const {THREE, scene, L, W, J, BAND} = C, list = [], meshes = [];
  const want = (L.predators || []).map(x => typeof x === 'string' ? {sp: x, n: 1} : x);
  want.forEach((wnt, wi) => { const sp = SPECIES[wnt.sp]; if (!sp) return; for (let n = 0; n < (wnt.n || 1); n++) {
    const {P, K} = sp.shape(), g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('aK', new THREE.Float32BufferAttribute(K, 1));
    const m = new THREE.Points(g, mat(THREE, sp, L.fogD)); m.frustumCulled = false; m.scale.setScalar(sp.scale); scene.add(m); meshes.push(m);
    const nm = sp.names ? sp.names[(wi + n) % sp.names.length] : sp.name;
    list.push({sp, key: wnt.sp, name: nm, m, u: 40 + wi * 37 + n * 61, w: 0, vu: 0, vw: 0, z: -3, hd: [1, 0], st: 'roam', t: 0, cool: 6 + n * 4, pos: new THREE.Vector3(), held: [], reg: wnt.reg, seen: false}); } });
  const zoneW = p => p.sp.zone === 'floor' ? -BAND + .8 : p.sp.zone === 'surface' ? BAND + 3.5 : null;
  const place = (p, ahead) => { p.u = J.u + (ahead ? 45 + Math.random() * 40 : -30); p.w = zoneW(p) ?? (Math.random() * 2 - 1) * BAND * .8; p.z = p.sp.zone === 'open' ? -4 - Math.random() * 6 : 0; p.st = 'roam'; p.t = 0; };
  list.forEach(p => place(p, true));
  // u, w of the jelly relative to it; turn toward a heading with the species' turn rate
  const steer = (p, tu, tw, sp, dt) => { const m = Math.hypot(tu, tw) || 1, hu = tu / m, hw = tw / m, k = Math.min(1, dt * p.sp.turn); p.hd[0] += (hu - p.hd[0]) * k; p.hd[1] += (hw - p.hd[1]) * k; const n = Math.hypot(p.hd[0], p.hd[1]) || 1; p.hd[0] /= n; p.hd[1] /= n; p.vu += (p.hd[0] * sp - p.vu) * Math.min(1, dt * 2); p.vw += (p.hd[1] * sp - p.vw) * Math.min(1, dt * 2); };
  const _a = new THREE.Vector3(), _b = new THREE.Vector3();
  function step(dt, RT, T, playing) {
    const out = [];
    for (const p of list) { const sp = p.sp, du = J.u - p.u, dw = J.w - p.w, dist = Math.hypot(du, dw, p.z * .6); p.t += dt; p.cool = Math.max(0, p.cool - dt);
      if (p.reg && C.regionAt && C.regionAt(J.u).id !== p.reg && p.st === 'roam') { p.m.visible = false; continue; } p.m.visible = true;   // in the seas each animal keeps to its own region
      const zw = zoneW(p), inZone = sp.zone === 'floor' ? J.w < -BAND + 3.6 : sp.zone === 'surface' ? J.w > BAND - 4 : true, weakOK = !sp.weak || J.mem < sp.weak;
      if (p.st === 'roam') { const tu = (C.current + 1) * 1.4 + Math.sin(T * .2 + p.u) * 2, tw = (zw ?? Math.sin(T * .13 + p.u * .1) * BAND * .6) - p.w; steer(p, tu, tw * .3, sp.slow ? sp.speed * .6 : Math.max(2, sp.speed * .35), dt); p.z += ((sp.zone === 'open' ? -5 : 0) - p.z) * dt * .3;
        if (playing && !p.cool && dist < sp.sense && inZone && weakOK) { p.st = sp.diver ? 'mark' : 'hunt'; p.t = 0; out.push({type: 'warn', p}); } }
      else if (p.st === 'hunt') { const lead = sp.passer ? 1.2 : .4; steer(p, du + J.vu * lead, dw + J.vw * lead, sp.speed, dt); p.z += (0 - p.z) * dt * 1.6;
        if (dist < sp.bite * (sp.gulp ? 1.4 : 1) && Math.abs(p.z) < 1.5) { p.st = 'sated'; p.t = 0; p.cool = sp.gulp ? 30 : 9; out.push({type: 'bite', p}); }
        else if (p.t > (sp.passer ? 3.2 : 9) || !inZone || dist > sp.sense * 2.2) { p.st = 'roam'; p.cool = 5; } }
      else if (p.st === 'mark') { steer(p, du, 0, 3, dt); if (p.t > 1.8) { p.st = 'dive'; p.t = 0; p.dv = [J.u, J.w]; } }   // a seabird marks the spot, then drops on it
      else if (p.st === 'dive') { steer(p, p.dv[0] - p.u, p.dv[1] - p.w, sp.speed, dt); if (Math.hypot(J.u - p.u, J.w - p.w) < sp.bite) { p.st = 'sated'; p.cool = 10; out.push({type: 'bite', p}); } else if (p.w < BAND - 5 || p.t > 1.6) { p.st = 'sated'; p.cool = 6; } }
      else if (p.st === 'flee') { steer(p, -du, -dw, sp.speed * 1.1, dt); p.z += (-7 - p.z) * dt; if (p.t > 4) { p.st = 'roam'; p.cool = 6; } }
      else if (p.st === 'sated') { steer(p, C.current * 2 - du * .3, (zw ?? -dw) - p.w * .1, sp.speed * .5, dt); p.z += ((sp.zone === 'open' ? -6 : 0) - p.z) * dt * .5; if (p.t > 5) p.st = 'roam'; }
      p.u += p.vu * dt; p.w += p.vw * dt; if (zw !== null && p.st !== 'dive' && p.st !== 'hunt') p.w += (zw - p.w) * Math.min(1, dt * 2); if (sp.zone === 'floor') p.w = Math.max(p.w, -BAND + .4);
      if (p.u < J.u - 45 || p.u > J.u + 120) place(p, p.u < J.u);
      W(p.u, p.w, p.z, p.pos); p.m.position.copy(p.pos); const hd = W(p.u + p.hd[0], p.w + p.hd[1], p.z, _a); p.m.lookAt(hd);
      const hunting = p.st === 'hunt' || p.st === 'mark' || p.st === 'dive', near = Math.max(0, 1 - dist / 30), u = p.m.material.uniforms; u.uTime.value = T; u.uHunt.value += ((hunting ? 1 : 0) - u.uHunt.value) * Math.min(1, dt * 3); u.uA.value = .35 + .5 * near + .15 * u.uHunt.value;
      if (p.held.length && p.st !== 'flee') for (const h of p.held) h.t = RT; }
    return out; }
  // a pulse: stings everything near enough; the immune keep coming; the dinnerplate lets go
  function stung(c, R) { const out = []; for (const p of list) { if (p.pos.distanceTo(c) > R) continue; if (p.sp.immune) { out.push({type: 'immune', p}); continue; } if (p.st === 'hunt' || p.st === 'mark' || p.st === 'roam' || p.st === 'sated') { p.st = 'flee'; p.t = 0; out.push({type: 'flee', p}); } if (p.held.length) out.push({type: 'release', p, films: p.held.splice(0)}); } return out; }
  return {list, meshes, step, stung};
}

// ---------------------------------------------------------------- default predators for a level that names none: from its water
export function predatorsFor(L) {
  if (L.predators) return L.predators; const out = [];
  if (L.surface) out.push('seabird'); if ((L.layers || []).some(l => l.kind === 'mussels' || l.kind === 'dunes')) out.push('crab'); if ((L.layers || []).some(l => l.kind === 'reef' && l.glow > .4)) out.push('nudibranch');
  const open = ['leatherback', 'mola', 'tuna', 'hawksbill', 'dinnerplate', 'salmon', 'sealion', 'trigger'], h = [...L.id].reduce((a, c) => a * 31 + c.charCodeAt(0) >>> 0, 7);
  out.push(open[h % open.length]); if (L.len > 300) out.push(open[(h >> 3) % open.length]); return out;
}

// ---------------------------------------------------------------- the seas: one long water per family, its levels laid end to end as regions
export function seaLevels(LEVELS, ARCH, C) {
  const seas = [], scale = .72;
  const chain = (members, extra) => { let u = 0; const regions = members.map(l => { const len = Math.round(l.len * scale), r = {id: l.id, title: l.title, u0: u, u1: u + len, films: l.films, bad: l.bad, fog: l.fog, top: l.top, goal: l.goal, creatures: l.creatures, preds: predatorsFor(l), match: l.match}; u += len; return r; }); return {regions, len: u, ...extra}; };
  const pred = regions => regions.flatMap(r => r.preds.map(sp => ({sp, n: 1, reg: r.id})));
  { const mem = LEVELS.filter(l => !['slices'].includes(l.id)).map(l => ({...l, films: l.films.layout === 'caves' ? {layout: 'scatter', every: l.films.every} : l.films})), S = chain(mem);
    seas.push({id: 'sea-drifts', sea: true, title: 'The Open Sea', source: 'our videos', song: 'nightbus-08', start: null, dir: 'right', len: S.len, current: 2.2, band: 13, fog: mem[0].fog, fogD: .028, films: {layout: 'regions'}, regions: S.regions, bad: 0,
      layers: [{kind: 'kelp', side: -1, z: -26, glow: .2}, {kind: 'ruin', side: 1, z: -14, glow: .4}, {kind: 'reef', side: -1, z: -6, glow: .5}, {kind: 'dunes', side: -1, z: 4, glow: 0}],
      creatures: ['school', 'comb', 'shrimp', 'ray', 'angler'], predators: pred(S.regions), goal: {type: 'regions', n: Math.ceil(S.regions.length * .6), label: 'take a film in each water of the open sea'},
      took: `All the drifts from our videos laid end to end as one water: ${S.regions.map(r => r.title).join(', ')}. Each water keeps its films, its colour and its hunters.`}); }
  { const mem = ARCH.filter(l => l.kind === 'crashlab' && l.id !== 'crashlab'), rest = {...ARCH.find(l => l.id === 'crashlab'), title: 'The Crash Lab', match: '^(?!ep|found-odyssey).*$'}, S = chain(mem.concat(rest).map(l => ({...l, len: 240})));
    seas.push({id: 'sea-crashlab', sea: true, kind: 'crashlab', match: '', title: 'The Lab Sea', source: 'bolas crash lab', song: 'event-04', start: null, dir: 'right', len: S.len, current: 2, band: 12, fog: '#1a1f26', fogD: .028, films: {layout: 'regions'}, regions: S.regions, bad: 0,
      layers: [{kind: 'reef', side: -1, z: -8, glow: .6}, {kind: 'cave', side: 1, z: -10, glow: .2}, {kind: 'mussels', side: -1, z: -18, glow: .1}], creatures: ['school', 'shrimp', 'comb'], fluid: true, specks: true,
      predators: pred(S.regions), goal: {type: 'regions', n: S.regions.length, label: 'take a film in every water of the lab'}, took: 'The Crash Lab films as one water: the Found Odyssey, the hand-made films, then the rest of the lab.'}); }
  if (C) { const types = [...new Set(C.signs.map(g => g.image))], regs = types.map((ty, i) => ({id: 'type-' + ty.toLowerCase().replace(/[^a-z]+/g, '-'), title: ty, len: 150, films: {layout: 'list'}, image: ty, fog: ARCH.find(l => l.title === ty)?.fog || '#1c2423', top: ARCH.find(l => l.title === ty)?.top, preds: [['leatherback', 'mola', 'dinnerplate', 'hawksbill', 'tuna', 'salmon'][i % 6]]}));
    let u = 0; regs.forEach(r => { r.u0 = u; r.u1 = u += r.len; });
    seas.push({id: 'sea-archive', sea: true, kind: 'cineosis', pick: {by: 'regions'}, title: 'The Archive Sea', source: 'cineosis-lab', song: 'daehoned-15', start: null, dir: 'right', len: u, current: 2.2, band: 12, fog: regs[0].fog, fogD: .028, films: {layout: 'regions'}, regions: regs, bad: 0,
      layers: [{kind: 'reef', side: -1, z: -8, glow: .6}, {kind: 'kelp', side: 1, z: -18, glow: .2}, {kind: 'ruin', side: -1, z: -24, glow: .4}], creatures: ['school', 'comb', 'shrimp'], fluid: true, specks: true,
      predators: pred(regs), goal: {type: 'regions', n: Math.ceil(regs.length * .6), label: 'take a film in each type of the archive'}, took: `The periodic table as one sea: the ${regs.length} cineosis types, each a water of its own signs.`}); }
  return seas;
}
// which sea a level opens into, and where
export const seaOf = l => l.sea ? null : l.kind === 'crashlab' ? 'sea-crashlab' : l.kind === 'cineosis' && (l.type || l.sign) ? 'sea-archive' : !l.kind && l.id !== 'slices' ? 'sea-drifts' : null;
export const regionOf = l => l.sign ? 'type-' + (l.sign.image || '').toLowerCase().replace(/[^a-z]+/g, '-') : l.id === 'crashlab' ? 'crashlab' : l.id;
