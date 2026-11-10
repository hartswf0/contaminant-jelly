// SWIM: the open water and the steer lab as one body model, shared by the Lab's OPEN WATER and STEER modes.
// The water: a dune floor, stones, kelp and beacons for the bonus pieces (after sea.html).
// The body: one bell {p, v, q, w, H} that strokes on its own beats (rhythm is propulsion, SCION_SWIM_CONTROLS §1.5).
//   OPEN WATER steers the heading H (glide stick, tap-to-go, drag-and-fling, keys, autopilot);
//   STEER hands the bell to the arms of tentacles3d.js (every finger owns one arm until it lifts, SCION_STEERLAB*).
import {makeArms3D} from './tentacles3d.js';

export const PLACES = [
  {id: 'sea', name: 'The Open Water', href: './sea.html', p: [14, 1, -10]},
  {id: 'steerlab3d', name: 'Steer Lab 3D', href: './steerlab3d.html', p: [-16, 0, -6]},
  {id: 'steerlab4d', name: 'Steer Lab 4D', href: './steerlab4d.html', p: [-12, 2, 14]},
  {id: 'orchestra', name: 'The Jelly Orchestra', href: './jellyorchestra.html', p: [10, 3, 16]},
  {id: 'realjelly', name: 'The Real Jelly', href: './realjelly.html', p: [0, -1, -22]},
  {id: 'medusae', name: 'Afterlight Medusae', href: './medusae.html', p: [24, -2, 4]},
];
export const FLOOR_Y = -7;
export const floorY = (x, z) => FLOOR_Y + Math.sin(x * .13) * .9 + Math.cos(z * .11 + x * .05) * .7 + Math.sin((x + z) * .31) * .2;

export function makeWater(THREE, scene, opt = {}) {
  const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z), root = new THREE.Group(); scene.add(root);
  // the floor: dunes of silt
  const N = opt.low ? 60 : 110, fl = new THREE.PlaneGeometry(140, 140, N, N); fl.rotateX(-Math.PI / 2); const P = fl.attributes.position;
  for (let i = 0; i < P.count; i++) P.setY(i, floorY(P.getX(i), P.getZ(i))); fl.computeVertexNormals();
  root.add(new THREE.Mesh(fl, new THREE.MeshStandardMaterial({color: 0x24302c, roughness: 1, metalness: 0})));
  // stones: anchors for the arms, solid for the bell
  const STONES = [], stoneM = new THREE.MeshStandardMaterial({color: 0x4a524c, roughness: .95});
  const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
  for (let i = 0; i < (opt.low ? 9 : 15); i++) { const a = rnd() * Math.PI * 2, r = 6 + rnd() * 26, x = Math.cos(a) * r, z = Math.sin(a) * r, rad = .7 + rnd() * 1.6, c = V3(x, floorY(x, z) + rad * .55, z);
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(rad, 1), stoneM); m.position.copy(c); m.rotation.set(rnd() * 3, rnd() * 3, 0); root.add(m); STONES.push({c, r: rad, m}); }
  // kelp: swaying stalks of nodes, light anchors the arms can hook
  const KELP = [], kelpM = new THREE.LineBasicMaterial({color: 0x6f8f4a, transparent: true, opacity: .85});
  for (let i = 0; i < (opt.low ? 10 : 18); i++) { const a = rnd() * Math.PI * 2, r = 4 + rnd() * 24, x = Math.cos(a) * r, z = Math.sin(a) * r, y0 = floorY(x, z), n = 9, h = 4 + rnd() * 5, nodes = [];
    for (let j = 0; j < n; j++) nodes.push({j, p: V3(x, y0 + j * h / (n - 1), z), base: V3(x, y0 + j * h / (n - 1), z)});
    const g = new THREE.BufferGeometry().setFromPoints(nodes.map(nd => nd.p)), line = new THREE.Line(g, kelpM); root.add(line); KELP.push({x, z, ph: rnd() * 6, nodes, line}); }
  // beacons: the other bonus pieces, as places in this water
  const BEACONS = PLACES.map(pl => { const p = V3(...pl.p), ring = new THREE.Mesh(new THREE.TorusGeometry(1.1, .06, 8, 40), new THREE.MeshBasicMaterial({color: 0xf0a35a, transparent: true, opacity: .8, toneMapped: false}));
    ring.position.copy(p); root.add(ring); const core = new THREE.PointLight(0xffc488, 2, 9, 2); core.position.copy(p); root.add(core); return {...pl, pos: p, ring}; });
  function update(T, cam) { for (const k of KELP) { for (const nd of k.nodes) { nd.p.x = nd.base.x + Math.sin(T * .7 + k.ph + nd.j * .3) * .02 * nd.j * nd.j; nd.p.z = nd.base.z + Math.cos(T * .5 + k.ph + nd.j * .2) * .015 * nd.j * nd.j; } k.line.geometry.setFromPoints(k.nodes.map(nd => nd.p)); }
    for (const b of BEACONS) { b.ring.lookAt(cam.position); b.ring.scale.setScalar(1 + Math.sin(T * 2 + b.pos.x) * .06); } }
  // an arm-host: what a finger's ray touches (tentacles3d env.pick); the nearest anchor to the ray, else the floor
  function pick(r, maxReach, bodyP) { let best = null, bs = 1e9; const _b = V3(), tol = t => .8 + t * .035;
    for (const k of KELP) for (const nd of k.nodes) { if (nd.j < 2) continue; const t = _b.copy(nd.p).sub(r.origin).dot(r.direction); if (t < 0) continue; const d = r.distanceToPoint(nd.p); if (d < tol(t)) { const sc = t + d * 4; if (sc < bs) { bs = sc; best = {type: 'kelp', p: nd.p.clone(), k: 52, heavy: false, n: nd}; } } }
    for (const s of STONES) { const t = _b.copy(s.c).sub(r.origin).dot(r.direction); if (t < 0) continue; const d = r.distanceToPoint(s.c); if (d < s.r + tol(t)) { const sc = t + d * 4; if (sc < bs) { bs = sc; const hit = r.at(Math.max(0, t - s.r * .8), V3()); best = {type: 'stone', p: hit, k: 64, heavy: true}; } } }
    if (best) return best;
    for (let t = 1; t < 70; t += .5) { const p = r.at(t, _b); if (p.y < floorY(p.x, p.z) + .3) { if (!bodyP || p.distanceTo(bodyP) < maxReach * 1.6) return {type: 'floor', p: p.clone(), k: 58, heavy: true}; break; } }
    return null; }
  return {root, STONES, KELP, BEACONS, update, pick, set visible(v) { root.visible = v; }, get visible() { return root.visible; }};
}

// ---------------------------------------------------------------- the body
export const STEER_DEFAULTS = {scheme: 'glide', thrust: 2.6, turn: 1.8, drag: .9, grav: .25, reach: 8.5, arms: 6, current: [0, 0, 0]};
export function makeBody(THREE, at) {
  const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
  const B = {p: at ? at.clone() : V3(), v: V3(), q: new THREE.Quaternion(), w: V3(), H: V3(0, 0, -1), want: V3(0, 0, -1), lastStroke: -9, strokes: 0, odo: 0, mode: 'open'};
  const UP = V3(0, 1, 0), _q = new THREE.Quaternion(), _a = V3();
  B.stroke = (T, k = 1, P) => { if (T - B.lastStroke < .3) return false; B.lastStroke = T; B.strokes++; const dir = B.mode === 'steer' ? V3(0, 1, 0).applyQuaternion(B.q) : B.H; B.v.addScaledVector(dir, P.thrust * k); return true; };
  // OPEN WATER: the heading turns toward what the hand wants (turn rate), the strokes push along it, the water drags
  B.open = (dt, T, P, water) => { const turn = 1 - Math.exp(-dt * P.turn); if (B.want.lengthSq() > 1e-6) { B.H.lerp(_a.copy(B.want).normalize(), turn).normalize(); }
    const cur = P.current || [0, 0, 0]; B.v.x += (cur[0] - B.v.x) * dt * .15; B.v.y += (cur[1] - B.v.y) * dt * .15; B.v.z += (cur[2] - B.v.z) * dt * .15;
    B.v.y -= P.grav * dt * .2; B.v.multiplyScalar(Math.exp(-dt * P.drag)); const before = B.p.clone(); B.p.addScaledVector(B.v, dt); collide(water); B.odo += before.distanceTo(B.p);
    // crown first: the bell's up axis leans into the heading, and levels out when it drifts
    const lead = _a.copy(B.H).multiplyScalar(Math.min(1, B.v.length() / 2)).add(V3(0, 1, 0).multiplyScalar(1.1)).normalize(); _q.setFromUnitVectors(UP, lead); B.q.slerp(_q, 1 - Math.exp(-dt * 2.4)); };
  // STEER: the arms pull, the bell answers with force and torque, rights itself slowly (steerlab3d.html's body)
  B.steer = (dt, T, P, o, water) => { B.v.addScaledVector(o.F, dt); if (o.snap) { B.v.addScaledVector(o.F, .14); B.w.addScaledVector(o.T, .1); }
    B.v.y -= P.grav * dt; const upv = V3(0, 1, 0).applyQuaternion(B.q); B.w.addScaledVector(o.T, dt * .9).addScaledVector(upv.clone().cross(UP), dt * 1.6); B.w.multiplyScalar(Math.exp(-dt * 1.8)); B.v.multiplyScalar(Math.exp(-dt * P.drag));
    const before = B.p.clone(); B.p.addScaledVector(B.v, dt); const wl = B.w.length(); if (wl > 1e-5) B.q.premultiply(new THREE.Quaternion().setFromAxisAngle(B.w.clone().divideScalar(wl), wl * dt)).normalize(); collide(water); B.odo += before.distanceTo(B.p); };
  function collide(water) { if (!water) return; const fy = floorY(B.p.x, B.p.z); if (B.p.y < fy + 1) { B.p.y = fy + 1; B.v.y = Math.abs(B.v.y) * .3; }
    for (const s of water.STONES) { const d = B.p.distanceTo(s.c); if (d < s.r + 1.1) { const n = B.p.clone().sub(s.c).normalize(); B.p.copy(s.c).addScaledVector(n, s.r + 1.1); B.v.addScaledVector(n, -Math.min(0, B.v.dot(n)) * 1.4); } }
    const rr = Math.hypot(B.p.x, B.p.z); if (rr > 60) { B.p.x *= 60 / rr; B.p.z *= 60 / rr; B.v.multiplyScalar(-.3); } if (B.p.y > 14) { B.p.y = 14; B.v.y = -Math.abs(B.v.y) * .3; } }
  return B;
}

// the arms, wired to this water (an env for tentacles3d)
export function makeArms(THREE, water, cam, opt = {}) {
  const AR = makeArms3D(THREE, {n: opt.arms || 6, AN: 16, reach: opt.reach || 8.5, R: 1.0});
  const screen = v => { const p = v.clone().project(cam); if (p.z > 1) return null; return [(p.x + 1) / 2 * innerWidth, (1 - p.y) / 2 * innerHeight]; };
  const env = {screen, pick: (r, arm, B) => water.pick(r, AR.REACH, B.p),
    water(r, B, depth) { const n = cam.getWorldDirection(new THREE.Vector3()), pl = new THREE.Plane().setFromNormalAndCoplanarPoint(n, B.p), hit = new THREE.Vector3(); if (!r.intersectPlane(pl, hit)) hit.copy(r.at(B.p.distanceTo(r.origin), new THREE.Vector3())); return hit.addScaledVector(r.direction, depth); },
    update(an) { if (an.type === 'kelp' && an.n) an.p.copy(an.n.p); }, react() {}, event(name) { if (opt.onEvent) opt.onEvent(name); }};
  const lines = AR.arms.map((a, i) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(AR.AN * 3), 3)); const m = new THREE.LineBasicMaterial({color: new THREE.Color(...a.col), transparent: true, opacity: .9, toneMapped: false}); const l = new THREE.Line(g, m); l.frustumCulled = false; return l; });
  const group = new THREE.Group(); lines.forEach(l => group.add(l));
  function draw() { AR.arms.forEach((a, i) => { const at = lines[i].geometry.attributes.position; at.array.set(a.X); at.needsUpdate = true; lines[i].material.color.setRGB(...a.col); lines[i].material.opacity = a.mode === 'latch' ? 1 : .45; }); }
  return {AR, env, group, draw};
}
