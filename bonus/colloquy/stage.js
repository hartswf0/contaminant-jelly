// THE COLLOQUY OF MOBILES · the staging. The sim (sim.js) is the cause; this module only shows it.
// Five registry jellies hang on filaments in dark water from a truncated-triangle frame (Fig. 1). Males (G: the Sentinel, J: the Celluloid)
// hang from the ends of bar Z; females (F1 Glass Moon, F2 Afterlight Medusa, F3 Fleck Veil) hang near the outer vertices. Every light,
// motor and pulse on screen is read from the machine state each frame.
import {GEOM, STAGE} from './sim.js';

const TAU = Math.PI * 2;
export const ORANGE = 0xff8a2a, PUCE = 0xc8689a, TORCH = 0xd9f7ff;
// each mobile's own hue, so it can be told apart without captions (its halo and filament carry it)
export const IDENT = {G: 0xff4a2e, J: 0x37d69a, F1: 0x5aa8ff, F2: 0xb07cff, F3: 0xf2e27a};
export const CAST = {G: 'sentinel', J: 'celluloid', F1: 'glass', F2: 'medusa', F3: 'veil'};

export function makeStage(THREE, {canvas, sim, createJelly, low = false, preserve = false, EffectComposer, RenderPass, UnrealBloomPass, OutputPass, cast = CAST}) {
  const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z), S = sim.S;
  const R = new THREE.WebGLRenderer({canvas, antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: preserve});
  R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.0; R.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const DARK = new THREE.Color('#03121a'), LIT = new THREE.Color('#46585b'), fogC = DARK.clone();
  scene.fog = new THREE.FogExp2(fogC, .085); scene.background = fogC;
  const hemi = new THREE.HemisphereLight(0x7fb4c0, 0x050a0a, .35); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xcfe8f0, .5); key.position.set(-3, 9, 4); scene.add(key);
  { const env = new THREE.Scene(); env.add(new THREE.Mesh(new THREE.BoxGeometry(20, 12, 20), new THREE.MeshBasicMaterial({color: 0x0c1618, side: THREE.BackSide}))); const p = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.MeshBasicMaterial({color: new THREE.Color(2.2, 2.4, 2.5)})); p.position.y = 5.9; p.rotation.x = Math.PI / 2; env.add(p); scene.environment = new THREE.PMREMGenerator(R).fromScene(env, .03).texture; }
  const cam = new THREE.PerspectiveCamera(40, 16 / 9, .05, 80); cam.position.set(0, 2.6, 6.5);
  const comp = new EffectComposer(R); comp.addPass(new RenderPass(scene, cam));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .55, .45, .74); comp.addPass(bloom); comp.addPass(new OutputPass());
  let pr = 1, W = 1, H = 1;
  function resize(w = innerWidth, h = innerHeight, ratio) { W = w; H = h; pr = ratio ?? Math.min(low ? 1.1 : 1.75, devicePixelRatio || 1); R.setPixelRatio(pr); R.setSize(w, h, false); comp.setPixelRatio(pr); comp.setSize(w, h); bloom.resolution.set(w * pr * (low ? .5 : 1), h * pr * (low ? .5 : 1)); cam.aspect = w / h; cam.updateProjectionMatrix(); }

  // ---------------------------------------------------------------- shared materials
  const metal = new THREE.MeshStandardMaterial({color: 0x56636a, metalness: .8, roughness: .34});
  const thread = new THREE.LineBasicMaterial({color: 0x9fc4c8, transparent: true, opacity: .32});
  const glowMat = c => new THREE.MeshBasicMaterial({color: c, transparent: true, opacity: 1, toneMapped: false, fog: false});
  const tube = (a, b, r = .018, mat = metal) => { const d = b.clone().sub(a), L = d.length(), m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, 8, 1), mat); m.position.copy(a).addScaledVector(d, .5); m.quaternion.setFromUnitVectors(V3(0, 1, 0), d.normalize()); return m; };
  const line = (pts, mat = thread) => new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat);

  // volumetric beam: a soft additive cone along local +X, unit length; scale.x = length, scale.y/z = end radius
  const beamGeo = new THREE.CylinderGeometry(.03, 1, 1, 28, 1, true); beamGeo.translate(0, -.5, 0); beamGeo.rotateZ(Math.PI / 2);
  const beamMat = (c) => new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false,
    uniforms: {uC: {value: new THREE.Color(c)}, uA: {value: 0}, uT: {value: 0}, uCore: {value: .3}},
    vertexShader: `varying float vAl; varying vec3 vN; varying vec3 vV; void main(){ vAl = 1.0 - uv.y; vec4 mv = modelViewMatrix * vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uC; uniform float uA, uT, uCore; varying float vAl; varying vec3 vN; varying vec3 vV;
      void main(){ float e = abs(dot(normalize(vN), normalize(vV))); float soft = pow(e, 2.2); float fall = (1.0 - smoothstep(.55, 1.0, vAl)) * (0.35 + 0.65 * (1.0 - vAl));
        float dust = 0.82 + 0.18 * sin(vAl * 47.0 - uT * 2.3) * sin(vAl * 13.0 + uT * .7); vec3 c = mix(uC, vec3(1.0, .95, .85), uCore * pow(e, 6.0));
        gl_FragColor = vec4(c * uA * soft * fall * dust, 1.0); }`});

  // ---------------------------------------------------------------- the frame (Fig. 1): a truncated triangle, a spindle, bar Z
  const rig = new THREE.Group(); scene.add(rig);
  const corners = GEOM.femaleAng.map(a => V3(Math.cos(a) * 2.25, GEOM.frameY, Math.sin(a) * 2.25)), frame = [];
  for (let i = 0; i < 3; i++) { const a = corners[i], b = corners[(i + 1) % 3]; frame.push(a.clone().lerp(b, .2), a.clone().lerp(b, .8)); }
  for (let i = 0; i < 6; i++) rig.add(tube(frame[i], frame[(i + 1) % 6], .026));
  for (let i = 0; i < 3; i++) { rig.add(tube(V3(0, GEOM.frameY, 0), frame[i * 2 + 1].clone().lerp(frame[(i * 2 + 2) % 6], .5), .016)); rig.add(tube(frame[i * 2], frame[i * 2].clone().setY(9), .01)); }
  rig.add(tube(V3(0, GEOM.frameY, 0), V3(0, GEOM.barY, 0), .03));
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, .12, 16), metal); hub.position.set(0, GEOM.barY, 0); rig.add(hub);
  const bar = new THREE.Group(); bar.position.y = GEOM.barY; rig.add(bar);
  bar.add(tube(V3(-GEOM.barR - .06, 0, 0), V3(GEOM.barR + .06, 0, 0), .028));
  const zLampMat = glowMat(0x2a6066), zLamp = new THREE.Mesh(new THREE.BoxGeometry(2 * GEOM.barR, .012, .012), zLampMat); zLamp.position.y = .035; bar.add(zLamp);   // Z's state: amber when halted by majority, dim teal when turning
  // floor: a dark bed with the drawing of the mechanism (Z's circle, the 90° arcs) laid faintly on it
  const floor = new THREE.Mesh(new THREE.CircleGeometry(40, 64), new THREE.MeshStandardMaterial({color: 0x0a1212, roughness: .95, metalness: 0})); floor.rotation.x = -Math.PI / 2; scene.add(floor);
  const drawMat = new THREE.LineBasicMaterial({color: 0x6fa6ac, transparent: true, opacity: .0});
  const drawing = new THREE.Group(); scene.add(drawing);
  { const c = []; for (let i = 0; i <= 96; i++) { const a = i / 96 * TAU; c.push(V3(Math.cos(a) * GEOM.barR, .01, Math.sin(a) * GEOM.barR)); } drawing.add(line(c, drawMat));
    GEOM.femaleAng.forEach(a0 => { const p = V3(Math.cos(a0) * GEOM.femaleR, .01, Math.sin(a0) * GEOM.femaleR), arc = []; for (let i = 0; i <= 24; i++) { const a = a0 + Math.PI - Math.PI / 4 + i / 24 * Math.PI / 2; arc.push(p.clone().add(V3(Math.cos(a) * .55, 0, Math.sin(a) * .55))); } drawing.add(line(arc, drawMat)); drawing.add(line([p, arc[0]], drawMat)); drawing.add(line([p, arc[24]], drawMat)); });
    for (let i = 0; i < 6; i++) drawing.add(line([frame[i].clone().setY(.01), frame[(i + 1) % 6].clone().setY(.01)], drawMat)); }

  // ---------------------------------------------------------------- labels (the legend's notation, placed on the machine)
  function label(text, color = '#d8eef0', size = .16) {
    const c = document.createElement('canvas'), x = c.getContext('2d'); c.width = 256; c.height = 96; x.font = '600 56px ui-monospace, Menlo, monospace'; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.lineWidth = 8; x.strokeStyle = 'rgba(0,0,0,.75)'; x.strokeText(text, 128, 50); x.fillStyle = color; x.fillText(text, 128, 50);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; const s = new THREE.Sprite(new THREE.SpriteMaterial({map: t, transparent: true, depthWrite: false, depthTest: false, fog: false, toneMapped: false})); s.scale.set(size * 2.67, size, 1); s.renderOrder = 20; return s;
  }
  const labels = [], addLabel = (parent, text, pos, color, size) => { const s = label(text, color, size); s.position.copy(pos); parent.add(s); labels.push(s); return s; };
  addLabel(bar, 'Z', V3(0, .2, 0), '#d8eef0', .13);

  // ---------------------------------------------------------------- jelly placement
  const ps0 = () => H * pr * .0095;
  // a dimmer on every material of a jelly: its final colour is scaled by the agent's own drive (brightness IS need)
  let dimN = 0;
  function dimmer(J) { const U = {value: 1}, key = 'dim' + (dimN++);
    J.group.traverse(o => { const mats = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of mats) { if (m.userData.dim) continue; m.userData.dim = U; const prev = m.onBeforeCompile;
      m.onBeforeCompile = (sh, r) => { if (prev) prev.call(m, sh, r); sh.uniforms.uDim = U; sh.fragmentShader = 'uniform float uDim;\n' + sh.fragmentShader.replace(/}\s*$/, '  gl_FragColor.rgb *= uDim;\n}'); };
      m.customProgramCacheKey = () => key; m.needsUpdate = true; } });
    return U; }
  function makeJelly(id, seed, scale) { const J = createJelly(THREE, id, {puppet: true, low, seed}); J.group.scale.setScalar(J.norm * scale); J.dim = dimmer(J); return J; }
  const dimOf = u => .1 + 1.1 * Math.pow(u, 1.3);

  const haloTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 0, 64, 64, 64); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(.35, 'rgba(255,255,255,.35)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
  // males: hang from the bar ends; local +X is the heading of lamp u and beam B
  const males = S.males.map((m, i) => {
    const g = new THREE.Group(); scene.add(g);
    const J = makeJelly(cast[m.id], 11 + i, .24); g.add(J.group);
    const lampMat = glowMat(ORANGE), lamp = new THREE.Mesh(new THREE.SphereGeometry(.045, 14, 10), lampMat); lamp.position.set(.27, .02, 0); g.add(lamp);
    const housing = new THREE.Mesh(new THREE.CylinderGeometry(.06, .07, .1, 14, 1, true), metal); housing.rotation.z = Math.PI / 2; housing.position.set(.22, .02, 0); g.add(housing);
    const beam = new THREE.Mesh(beamGeo, beamMat(ORANGE)); beam.position.copy(lamp.position); beam.renderOrder = 5; g.add(beam);
    const vane = (y, c) => { const mat = new THREE.MeshStandardMaterial({color: c, emissive: c, emissiveIntensity: .05, metalness: .3, roughness: .5, side: THREE.DoubleSide}); const v = new THREE.Mesh(new THREE.PlaneGeometry(.16, .1), mat); v.position.set(.2, y, 0); v.rotation.y = Math.PI / 2; g.add(v); return {v, mat}; };
    const C = vane(.24, ORANGE), D = vane(-.2, PUCE);
    // display A: the male's two drives as lit columns on his crown
    const colO = new THREE.Mesh(new THREE.BoxGeometry(.018, 1, .018), glowMat(new THREE.Color(ORANGE).multiplyScalar(.7))), colP = new THREE.Mesh(new THREE.BoxGeometry(.018, 1, .018), glowMat(new THREE.Color(PUCE).multiplyScalar(.7))); colO.position.set(-.05, .36, .05); colP.position.set(-.05, .36, -.05); g.add(colO, colP);
    const plate = new THREE.Mesh(new THREE.BoxGeometry(.03, .26, .2), metal); plate.position.set(-.08, .42, 0); g.add(plate);
    const fil = line([V3(), V3(0, 1, 0)], new THREE.LineBasicMaterial({color: IDENT[m.id], transparent: true, opacity: .45})); scene.add(fil);
    const aura = new THREE.Sprite(new THREE.SpriteMaterial({map: haloTex, color: IDENT[m.id], transparent: true, opacity: .2, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, toneMapped: false})); aura.scale.setScalar(.95); aura.position.y = .05; g.add(aura);
    addLabel(g, m.id, V3(0, .68, 0), '#f4f0e6', .13); addLabel(g, 'u', V3(.36, .1, 0), '#ffcf9a', .07); addLabel(g, 'B', V3(.6, -.06, 0), '#ffcf9a', .07);
    addLabel(g, 'C', V3(.25, .34, 0), '#ffb070', .065); addLabel(g, 'D', V3(.25, -.31, 0), '#e2a0c2', .065); addLabel(g, 'A', V3(-.08, .6, 0), '#cfe0e2', .065);
    return {m, g, J, lamp, lampMat, beam, C, D, colO, colP, fil, aura, bright: .3, recoil: V3(), last: 1};
  });
  // females: hang from the frame; local +X faces inward (aperture a, servo mirror b)
  const females = S.females.map((f, i) => {
    const g = new THREE.Group(); scene.add(g);
    const J = makeJelly(cast[f.id], 21 + i, .27); g.add(J.group);
    const apMat = glowMat(0x9fe6ff), ap = new THREE.Mesh(new THREE.TorusGeometry(.065, .012, 8, 24), apMat); ap.position.set(.25, -.02, 0); ap.rotation.y = Math.PI / 2; g.add(ap);
    const mirG = new THREE.Group(); mirG.position.set(.34, -.17, 0); g.add(mirG);
    const mirMat = new THREE.MeshStandardMaterial({color: 0xeaf6ff, metalness: 1, roughness: .06, emissive: 0xffffff, emissiveIntensity: 0, side: THREE.DoubleSide});
    const mir = new THREE.Mesh(new THREE.PlaneGeometry(.17, .17), mirMat); mir.rotation.y = Math.PI / 2; mirG.add(mir);
    const mirFrame = new THREE.Mesh(new THREE.BoxGeometry(.012, .19, .19), metal); mirFrame.position.x = -.01; mirG.add(mirFrame);
    const glint = new THREE.Mesh(new THREE.SphereGeometry(.016, 10, 8), glowMat(0xffffff)); glint.position.x = .01; mirG.add(glint);
    const ripples = [0, 1, 2].map(() => { const r = new THREE.Mesh(new THREE.RingGeometry(.9, 1, 40), new THREE.MeshBasicMaterial({color: 0xbfefff, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending, fog: false})); r.rotation.y = Math.PI / 2; r.position.set(.1, .05, 0); g.add(r); return {r, age: 9}; });
    const refl = new THREE.Mesh(beamGeo, beamMat(0xffffff)); refl.renderOrder = 6; scene.add(refl);
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({map: haloTex, color: 0xffffff, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, toneMapped: false})); halo.scale.setScalar(.9); halo.position.y = .08; g.add(halo);
    const fil = line([V3(), V3(0, 1, 0)], new THREE.LineBasicMaterial({color: IDENT[f.id], transparent: true, opacity: .45})); scene.add(fil);
    const aura = new THREE.Sprite(new THREE.SpriteMaterial({map: haloTex, color: IDENT[f.id], transparent: true, opacity: .2, depthWrite: false, blending: THREE.AdditiveBlending, fog: false, toneMapped: false})); aura.scale.setScalar(1.05); aura.position.y = .05; g.add(aura);
    addLabel(g, f.id, V3(0, .62, 0), '#f4f0e6', .13); addLabel(g, 'a', V3(.27, .1, .1), '#bfefff', .065); addLabel(g, 'b', V3(.37, -.32, .1), '#eef6ff', .065);
    return {f, g, J, ap, apMat, mirG, mirMat, glint, ripples, refl, fil, halo, aura, bright: .3, recoil: V3(), lampWas: 0, last: 1};
  });
  // the visitor: a dark figure who can stand in a beam, hold a torch, or a hand mirror
  const visitor = new THREE.Group(); visitor.visible = false; scene.add(visitor);
  { const body = new THREE.Mesh(new THREE.CapsuleGeometry(.2, 1.2, 6, 14), new THREE.MeshStandardMaterial({color: 0x050707, roughness: .9})); body.position.y = .82; visitor.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(.13, 16, 12), body.material); head.position.y = 1.66; visitor.add(head);
    const rim = new THREE.Mesh(new THREE.CapsuleGeometry(.215, 1.2, 6, 14), new THREE.MeshBasicMaterial({color: 0x7fd6e0, transparent: true, opacity: .12, side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false})); rim.position.y = .82; visitor.add(rim);
    addLabel(visitor, 'visitor', V3(0, 2.05, 0), '#9fe6ef', .09); }
  const torchBeam = new THREE.Mesh(beamGeo, beamMat(TORCH)); scene.add(torchBeam);
  // the stranger holding the torch: a second figure, visible wherever the torch is shone from
  const stranger = new THREE.Group(); stranger.visible = false; scene.add(stranger);
  { const mat = new THREE.MeshStandardMaterial({color: 0x0a0d0e, roughness: .85}); const b = new THREE.Mesh(new THREE.CapsuleGeometry(.19, 1.15, 6, 14), mat); b.position.y = .8; stranger.add(b); const h = new THREE.Mesh(new THREE.SphereGeometry(.12, 16, 12), mat); h.position.y = 1.6; stranger.add(h);
    const rim = new THREE.Mesh(new THREE.CapsuleGeometry(.205, 1.15, 6, 14), new THREE.MeshBasicMaterial({color: TORCH, transparent: true, opacity: .16, side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false})); rim.position.y = .8; stranger.add(rim);
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(.04, .04, .5, 8), mat); arm.rotation.z = Math.PI / 2; arm.position.set(.25, 1.32, 0); stranger.add(arm);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(.05, 12, 8), glowMat(new THREE.Color(TORCH).multiplyScalar(2))); bulb.position.set(.5, 1.32, 0); stranger.add(bulb); }
  const handMirror = new THREE.Mesh(new THREE.PlaneGeometry(.2, .2), new THREE.MeshStandardMaterial({color: 0xffffff, metalness: 1, roughness: .05, emissive: 0xffffff, emissiveIntensity: .3, side: THREE.DoubleSide})); handMirror.visible = false; scene.add(handMirror);

  // marine snow and a few soft shafts from above
  const SNOW = (() => { const n = low ? 500 : 1400, P = new Float32Array(n * 3); let s = 9; const r = () => (s = (s * 16807) % 2147483647) / 2147483647; for (let i = 0; i < n; i++) { P[i * 3] = (r() - .5) * 14; P[i * 3 + 1] = r() * 7; P[i * 3 + 2] = (r() - .5) * 14; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); const p = new THREE.Points(g, new THREE.PointsMaterial({size: .02, color: 0xbfe6ee, transparent: true, opacity: .35, depthWrite: false})); p.frustumCulled = false; scene.add(p); return {p, P, n}; })();

  // ---------------------------------------------------------------- shots (Fig. 1A plan, Fig. 1B side, mirror close-up, triangulation)
  const mpos = m => { const p = sim.malePos(m); return V3(p.x, GEOM.maleY, p.z); }, fpos = f => { const p = sim.femalePos(f); return V3(p.x, GEOM.femaleY, p.z); };
  const SHOTS = {
    plan: (u) => ({pos: V3(Math.sin(u * .05) * .35, 8.6 - u * .05, .5), look: V3(0, 1.6, 0), fov: 44}),
    side: (u, a0) => { const a = a0 + u * .025; return {pos: V3(Math.cos(a) * 6.6, 2.35, Math.sin(a) * 6.6), look: V3(0, 2.25, 0), fov: 40}; },
    orbit: (u, a0) => { const a = a0 + u * .05; return {pos: V3(Math.cos(a) * 4.8, 3.3 + Math.sin(u * .1) * .3, Math.sin(a) * 4.8), look: V3(0, 2.1, 0), fov: 42}; },
    mirror: (u, a0, foc) => { const f = foc.f; if (!f) return SHOTS.side(u, a0); const p = fpos(f), h = sim.femaleHeading(f), fw = V3(Math.cos(h), 0, Math.sin(h)), sd = V3(-fw.z, 0, fw.x);
      return {pos: p.clone().addScaledVector(fw, .7).addScaledVector(sd, Math.max(1.05, 1.9 - u * .14)).add(V3(0, .14, 0)), look: p.clone().addScaledVector(fw, .62).add(V3(0, -.1, 0)), fov: 36}; },   // in profile: the tilt of b reads
    tri: (u, a0, foc) => { if (!foc.f) return SHOTS.orbit(u, a0); const b = fpos(foc.f), hf = sim.femaleHeading(foc.f), a = foc.m && foc.m !== 'V' ? mpos(foc.m) : b.clone().add(V3(Math.cos(hf) * 1.5, 0, Math.sin(hf) * 1.5)), mid = a.clone().lerp(b, .5), d = b.clone().sub(a); const n = V3(-d.z, 0, d.x).normalize(); if (n.dot(mid) < 0) n.negate();
      const L = Math.max(1.6, d.length()); return {pos: mid.clone().addScaledVector(n, L * 1.25 + 1 - u * .02).add(V3(0, .75, 0)), look: mid.clone().add(V3(0, -.05, 0)), fov: 38}; },
    wide: () => ({pos: V3(0, 6.2, 5.4), look: V3(0, 1.5, 0), fov: 44}),
    stranger: (u, a0, foc) => { if (!foc.f) return SHOTS.plan(u); const p = fpos(foc.f), h = sim.femaleHeading(foc.f), fw = V3(Math.cos(h), 0, Math.sin(h)), sd = V3(-fw.z, 0, fw.x), base = p.clone().addScaledVector(fw, 1.7).setY(0);   // over the stranger's shoulder, the torch to her
      return {pos: base.clone().addScaledVector(fw, 1.35 - u * .05).addScaledVector(sd, .8).add(V3(0, 1.85, 0)), look: p.clone().lerp(base.clone().setY(1.3), .4), fov: 44}; },
    two: (u, a0, foc) => { if (!foc.f || !foc.m) return SHOTS.tri(u, a0, foc); const b = fpos(foc.f), hf = sim.femaleHeading(foc.f), a = foc.m === 'V' ? b.clone().add(V3(Math.cos(hf) * 1.5, 0, Math.sin(hf) * 1.5)) : mpos(foc.m), d = b.clone().sub(a).normalize(), sd = V3(-d.z, 0, d.x);   // along beam B, over his shoulder
      return {pos: a.clone().addScaledVector(d, -1.4 + u * .04).addScaledVector(sd, .75).add(V3(0, .4, 0)), look: a.clone().lerp(b, .68), fov: 40}; },
    bar: (u, a0) => { const a = a0 + u * .05; return {pos: V3(Math.cos(a) * 1.75, 2.25, Math.sin(a) * 1.75), look: V3(0, GEOM.barY - .12, 0), fov: 52}; },   // bar Z from below, the males hanging
    vane: (u, a0, foc) => { if (!foc.m || foc.m === 'V') return SHOTS.mirror(u, a0, foc); const p = mpos(foc.m), h = sim.maleHeading(foc.m), fw = V3(Math.cos(h), 0, Math.sin(h)), sd = V3(-fw.z, 0, fw.x);
      return {pos: p.clone().addScaledVector(fw, -.25).addScaledVector(sd, 1.25 - u * .03).add(V3(0, .25, 0)), look: p.clone().addScaledVector(fw, .25), fov: 38}; },   // from the side, behind his lamp: the vanes and his dimming bell, not the beam
    memory: (u, a0, foc) => { if (!foc.f) return SHOTS.plan(u); const p = fpos(foc.f), h = sim.femaleHeading(foc.f), fw = V3(Math.cos(h), 0, Math.sin(h)), sd = V3(-fw.z, 0, fw.x);   // hold on her memory glow
      return {pos: p.clone().addScaledVector(fw, 1.2).addScaledVector(sd, -1.1 - u * .03).add(V3(0, .5, 0)), look: p.clone().add(V3(0, .02, 0)), fov: 36}; },
    visit: (u) => { const b = S.visitor.body || {x: 0, z: 0}, o = V3(b.x, 0, b.z), out = o.lengthSq() > .01 ? o.clone().normalize() : V3(0, 0, 1), sd = V3(-out.z, 0, out.x);
      return {pos: o.clone().addScaledVector(out, 4.8 - u * .05).addScaledVector(sd, 1.8).add(V3(0, 3.1, 0)), look: o.clone().add(V3(0, 1.45, 0)).multiplyScalar(.7), fov: 42}; }};
  // ---------------------------------------------------------------- the director: every cut lands on a machine event
  // Events arrive from the sim as they happen; each rendered frame the director weighs the ones from that frame and cuts (or not).
  // A cut is never made without an event in the same frame; min/max holds keep it from thrashing or going stale.
  const D = {shot: 'plan', since: 0, a0: .6, focus: {f: null, m: null}, cuts: 0, manual: null, log: [], pending: [], minHold: 1.8, stepHold: 1.4, keyHold: .9, maxHold: 6, capHold: 8, jump: true, frame: 0};
  sim.on(ev => D.pending.push(ev));
  const femaleOf = id => S.females.find(f => f.id === id) || null, maleOf = id => S.males.find(m => m.id === id) || null;
  // event → {shot, focus, pri}; pri ≥ 4 may cut after minHold, anything may refresh a shot past maxHold
  function reading(ev) {
    const focusBusy = D.focus.f && D.focus.f.stage > 1 && D.focus.f.partner !== -1, mine = f => !focusBusy || f === D.focus.f, adj = (f, p) => mine(f) ? p : p - 5;
    if (ev.kind === 'visitor') { if (ev.mode === 'prosthetic male') { const f = femaleOf(ev.f); return {shot: 'stranger', focus: {f, m: 'V'}, pri: 10, why: 'a stranger’s torch → ' + ev.f}; }
      if (ev.mode === 'occlusion') return {shot: 'visit', focus: D.focus, pri: 10, why: 'visitor steps into the room'};
      if (ev.mode === 'prosthetic female') { const m = maleOf(ev.m); return {shot: 'vane', focus: {f: S.females[m.partner] || null, m}, pri: 9, why: 'visitor mirror → ' + ev.m}; }
      return {shot: 'bar', focus: D.focus, pri: 6, why: 'visitor conducts bar Z'}; }
    if (ev.kind === 'stage' && /^F/.test(ev.who)) { const f = femaleOf(ev.who), m = f.partner >= 0 ? S.males[f.partner] : f.partner === -2 ? 'V' : null, foc = {f, m};
      if (ev.stage === 2) return {shot: 'two', focus: foc, pri: adj(f, 6), why: 'contact: ' + f.id + ' catches u'};
      if (ev.stage === 3) return {shot: 'mirror', focus: foc, pri: adj(f, 6), why: 'phase-lock: push to mirror b'};
      if (ev.stage === 5) return {shot: 'mirror', focus: foc, pri: adj(f, 4), why: 'sweep within τ'};
      if (ev.stage === 7) return {shot: 'memory', focus: foc, pri: adj(f, 8), why: 'consolidate: memory glow'}; }
    if (ev.kind === 'energetic') { const f = femaleOf(ev.f); return {shot: 'bar', focus: {f, m: maleOf(ev.m)}, pri: adj(f, 7), why: 'commit: ' + ev.m + ' asks bar Z to halt'}; }
    if (ev.kind === 'reinforce') { const f = femaleOf(ev.f); return {shot: 'vane', focus: {f, m: maleOf(ev.m)}, pri: f ? adj(f, 8) : 8, why: 'F = 1: drive falls by ω'}; }
    if (ev.kind === 'ambient') return {shot: 'plan', focus: {f: null, m: null}, pri: 10, why: ev.rising ? 'the lights come up: the society falls quiet' : 'darkness again: the conversation resumes'};
    if (ev.kind === 'contention') return {shot: 'bar', focus: D.focus, pri: focusBusy ? 2 : 5, why: 'Z arbitration'};
    if (ev.kind === 'abort') { const f = femaleOf(ev.f); return {shot: 'side', focus: D.focus, pri: f && !mine(f) ? 0 : 5, why: 'abort: ' + ev.why}; }
    return {shot: null, pri: 1, why: ev.kind};
  }
  function idleShot() { const seq = ['plan', 'side', 'orbit']; return seq[(seq.indexOf(D.shot) + 1) % 3] || 'plan'; }
  function cut(r, ev) { const same = r.shot === D.shot && r.focus === D.focus; D.shot = r.shot; if (r.focus) D.focus = r.focus; D.since = S.t; D.a0 = (D.a0 + 1.9 + (D.cuts * 2.39) % 1.3) % TAU; D.cuts++; D.jump = true;
    D.log.push({t: +S.t.toFixed(4), shot: r.shot, why: r.why, ev: {kind: ev.kind, t: +ev.t.toFixed(4), who: ev.who || ev.f || ev.m || null}, frame: D.frame}); if (D.log.length > 400) D.log.shift(); }
  function director() {
    D.frame++; const evs = D.pending; D.pending = []; if (D.manual) return; const held = S.t - D.since;
    if (!evs.length) { if (held >= D.capHold) cut({shot: idleShot(), focus: D.focus, why: 'establishing (no event for ' + D.capHold + ' s)'}, {kind: 'none', t: S.t}); return; }
    let best = null, bestEv = null;
    for (const ev of evs) { const r = reading(ev); if (!best || r.pri > best.pri) { best = r; bestEv = ev; } }
    const sameStory = best.focus && best.focus.f && best.focus.f === D.focus.f, need = best.pri >= 10 ? 0 : sameStory ? (best.pri >= 8 ? D.keyHold : D.stepHold) : D.minHold;   // the next beat of the same encounter may come sooner
    if (sim.P.ambient > .3 && best.pri < 10) { if (held >= D.capHold) cut({shot: idleShot(), focus: {f: null, m: null}, why: 'the lit room, quiet'}, bestEv); return; }   // lights up: hold the quiet room
    if (best.pri >= 4 && held >= need && (best.shot !== D.shot || !sameStory)) return cut(best, bestEv);
    if (held >= D.maxHold) {   // stale: refresh on this frame's event, to the live encounter if there is one
      let live = null; for (const f of S.females) if (f.partner !== -1 && f.stage > 1 && (!live || f.stage > live.stage)) live = f;
      const r = live ? {shot: live.stage >= 5 ? 'mirror' : 'tri', focus: {f: live, m: live.partner >= 0 ? S.males[live.partner] : 'V'}, why: 'hold refresh: ' + live.id} : {shot: idleShot(), focus: D.focus, why: 'scan: wide'};
      cut(r, bestEv);
    }
  }
  function setShot(name) { if (name === 'auto') { D.manual = null; return; } D.manual = name; if (!D.focus.f) { const f = S.females.find(f => f.stage > 1) || S.females[0]; D.focus = {f, m: f.partner >= 0 ? S.males[f.partner] : S.males[0]}; } D.shot = name; D.since = S.t; D.jump = true; }
  const orbitCtl = {on: false, az: .8, el: .42, r: 6.4};
  const camT = {pos: V3(), look: V3(), fov: 40}, camLook = V3();

  // bell glow from drive level (urgency 0..1); the rig multiplies its colour by (1 + k·glow), so the base is set dark (−.45) and need lights it
  const brightOf = u => 2.6 * Math.pow(u, 1.3);
  // F = 1: the satisfied pair swing apart on their filaments
  sim.on(ev => { if (ev.kind !== 'reinforce') return; const M = males.find(x => x.m.id === ev.m), F = females.find(x => x.f.id === ev.f); if (!M) return;
    const a = mpos(M.m), b = F ? fpos(F.f) : a.clone().add(V3(1, 0, 0)), d = b.clone().sub(a).setY(0).normalize(); M.recoil.addScaledVector(d, -.32); if (F) F.recoil.addScaledVector(d, .26); });
  // ---------------------------------------------------------------- per frame: read the machine, light the stage
  let T = 0, ambient = 0, legend = false, labelsOn = false;
  const lampColor = d => d === 'P' ? PUCE : ORANGE;
  function update(dt) {
    T += dt; const P = sim.P;
    // the gallery light: the photocells' contrast and the look of the water both follow it
    ambient += (P.ambient - ambient) * Math.min(1, dt * 3);
    fogC.copy(DARK).lerp(LIT, Math.min(1, ambient)); scene.fog.density = .085 - .035 * Math.min(1, ambient); hemi.intensity = .35 + 2.6 * ambient; key.intensity = .5 + 1.8 * ambient;
    bar.rotation.y = -S.z; zLampMat.color.setHex(S.zHalt ? 0xffa040 : 0x2a6066).multiplyScalar(S.zHalt ? 1.6 : 1);
    const ps = ps0();
    for (const M of males) {
      const m = M.m, p = mpos(m).add(M.recoil), h = sim.maleHeading(m); M.g.position.copy(p); M.g.rotation.y = -h; M.recoil.multiplyScalar(Math.exp(-dt * .9));
      M.fil.geometry.setFromPoints([p.clone().add(V3(0, .5, 0)), V3(p.x, GEOM.barY, p.z)]);
      const d = m.desire || 'O', col = lampColor(d); M.lampMat.color.setHex(m.lamp ? col : 0x1a1410);
      M.lampMat.color.multiplyScalar(m.lamp ? (m.B ? 2.2 : 1.6) : 1);
      // beam: flashing u while scanning; steady B once committed; cut short by whatever stands in the line
      let L = 2.7, rad = Math.tan(P.beamHalf) * 1.1, op = 0;
      if (m.stage <= 3 && m.desire) op = m.lamp ? .22 : 0; if (m.B) { op = .62; }
      const tgt = m.partner >= 0 ? S.females[m.partner] : null;
      if (tgt && m.stage >= 2) { const a = sim.aligned(m, tgt); if (a.ok) L = a.dist - .28; }
      const occ = cutBy(p, h, L); if (occ < L) L = occ;
      M.beam.scale.set(L, rad * L, rad * L); M.beam.material.uniforms.uA.value += (op - M.beam.material.uniforms.uA.value) * Math.min(1, dt * (m.B ? 6 : 40)); M.beam.material.uniforms.uC.value.setHex(col); M.beam.material.uniforms.uT.value = T; M.beam.material.uniforms.uCore.value = m.B ? .45 : .15;
      M.beam.visible = M.beam.material.uniforms.uA.value > .005;
      // vanes C and D light when the reflection lands on them; F = 1 flares the right one
      const fr = tgt && tgt.stage >= 5 ? tgt.b : 0;
      const flash = m.stage === 6 ? Math.max(0, 1 - (S.t - m.since) / .3) * 1.3 : 0;   // F = 1: a brief flare on the vane, then the satisfied body dims
      M.C.mat.emissiveIntensity = .05 + (fr > .4 && m.B ? .9 * fr : 0) + (m.vane === 'C' ? flash : 0);
      M.D.mat.emissiveIntensity = .05 + (fr < -.4 && m.B ? -.9 * fr : 0) + (m.vane === 'D' ? flash : 0);
      M.colO.scale.y = Math.max(.02, m.O / P.Lcap) * .42; M.colO.position.y = .2 + M.colO.scale.y / 2; M.colP.scale.y = Math.max(.02, m.P / P.Lcap) * .42; M.colP.position.y = .2 + M.colP.scale.y / 2;
      // the jelly: its pacemakers run warm with urgency, quiescent when satisfied; stage events fire its leading pacemaker
      const urg = Math.max(m.O, m.P) / P.Lcap; if (M.J.nerve) for (const nv of M.J.rings) nv.warm = .45 + urg * 1.2;
      if (m.stage !== M.last) { if (m.stage === 2 || m.stage === 4) M.J.pulse(1); M.last = m.stage; }
      // brightness IS need: the bell and its halo are lit by the drive level, so rising need brightens and F = 1 visibly dims it
      if (m.stage === 6 && M.satT !== m.since) M.satT = m.since; M.bright += (Math.min(1, (m.O + m.P) / 2 / P.Lcap * (m.B ? 1.5 : 1 - .7 * Math.exp(-(S.t - (M.satT ?? -99)) / 7))) - M.bright) * Math.min(1, dt * 7); const lumM = brightOf(M.bright);
      // committed (B on) he burns brighter; satisfied, he goes dark and need slowly relights him
      M.J.setLook({glow: lumM}); M.J.dim.value = dimOf(M.bright); M.aura.material.opacity = .03 + 1.1 * Math.pow(M.bright, 1.7); M.aura.scale.setScalar(.7 + .5 * M.bright);
      M.J.update({t: T, dt, cam: cam.position, camObj: cam, light: p.clone().add(V3(0, 2, 0)), glow: -.45 + ambient * .15, scale: ps * .3, drive: true});
    }
    for (const F of females) {
      const f = F.f, p = fpos(f).add(F.recoil), h = sim.femaleHeading(f); F.g.position.copy(p); F.g.rotation.y = -h; F.recoil.multiplyScalar(Math.exp(-dt * .9));
      F.fil.geometry.setFromPoints([p.clone().add(V3(0, .45, 0)), V3(p.x, GEOM.frameY, p.z)]);
      const m = f.partner >= 0 ? S.males[f.partner] : null, lit = f.stage >= 2 && f.stage <= 6;
      F.apMat.color.setHex(lit ? (f.desire === 'P' ? PUCE : ORANGE) : 0x3a6670); F.apMat.color.multiplyScalar(lit ? 1.8 : .8);
      // mirror b: up for O, down for P (servo, from the sim's b)
      F.mirG.rotation.z = f.b * .42; F.mirMat.emissiveIntensity = f.stage >= 5 && f.stage <= 6 ? .28 : .02; F.glint.visible = f.stage >= 4 && f.stage <= 6; F.glint.material.color.setHex(0xffffff).multiplyScalar(1.2 + Math.abs(f.b) * 1.5);
      // tone: ripples phase-locked to his flashing u (or steady once he commits)
      const lampNow = m ? m.lamp : (f.partner === -2 ? (Math.sin(S.t * TAU * 3.6) > .2 ? 1 : 0) : 0);
      if (f.tone > 0 && lampNow && !F.lampWas) { const r = F.ripples.find(r => r.age > 1.2) || F.ripples[0]; r.age = 0; }
      F.lampWas = lampNow; for (const r of F.ripples) { r.age += dt; const k = Math.min(1, r.age / 1.2); r.r.scale.setScalar(.03 + k * .26); r.r.material.opacity = f.tone > 0 ? (1 - k) * .55 * f.tone : Math.max(0, r.r.material.opacity - dt); }
      // the reflected beam: from mirror b back to his body, landing high (C) or low (D)
      let ra = 0;
      if (f.stage >= 5 && f.stage <= 6 && m && m.B) {
        const mp = F.mirG.getWorldPosition(V3()), tp = mpos(m).add(V3(0, .02 + f.b * .24, 0)), d = tp.clone().sub(mp), L = d.length();
        F.refl.position.copy(mp); F.refl.quaternion.setFromUnitVectors(V3(1, 0, 0), d.normalize()); F.refl.scale.set(L, .07 * L, .07 * L);
        const onVane = Math.abs(f.b) > .55; ra = .35 + (onVane ? .6 : 0); F.refl.material.uniforms.uC.value.setHex(f.b > 0 ? 0xffd2a0 : 0xf0b8d8);
      }
      F.refl.material.uniforms.uA.value += (ra - F.refl.material.uniforms.uA.value) * Math.min(1, dt * 8); F.refl.material.uniforms.uT.value = T; F.refl.material.uniforms.uCore.value = .8; F.refl.visible = F.refl.material.uniforms.uA.value > .005;
      const urg = Math.max(f.O, f.P) / P.Lcap; if (F.J.nerve) for (const nv of F.J.rings) nv.warm = .45 + urg * 1.1;
      if (f.stage !== F.last) { if (f.stage === 2 || f.stage === 5) F.J.pulse(1); F.last = f.stage; }
      if (f.stage === 7 && F.satT !== f.since) F.satT = f.since; F.bright += ((f.O + f.P) / 2 / P.Lcap * (1 - .7 * Math.exp(-(S.t - (F.satT ?? -99)) / 7)) - F.bright) * Math.min(1, dt * 7); F.J.setLook({glow: brightOf(F.bright)}); F.J.dim.value = dimOf(F.bright); F.aura.material.opacity = .03 + 1.1 * Math.pow(F.bright, 1.7); F.aura.scale.setScalar(.75 + .55 * F.bright);
      // her memory being written (stage 7): a slow glow in the colour of the drive she has just satisfied
      const ho = f.stage === 7 ? .22 * Math.min(1, (S.t - f.since) * 2) : 0; F.halo.material.opacity += (ho - F.halo.material.opacity) * Math.min(1, dt * 3); F.halo.material.color.setHex(f.desire === 'P' ? PUCE : ORANGE); F.halo.visible = F.halo.material.opacity > .01;
      F.J.update({t: T, dt, cam: cam.position, camObj: cam, light: p.clone().add(V3(0, 2, 0)), glow: -.45 + ambient * .15, scale: ps * .32, drive: true});
    }
    // the visitor
    const vb = S.visitor.body; visitor.visible = !!vb; if (vb) visitor.position.set(vb.x, 0, vb.z);
    const tor = S.visitor.torch && S.visitor.torch.until > S.t ? S.visitor.torch : null;
    stranger.visible = !!tor;
    if (tor) { const f = S.females[tor.f], p = fpos(f), h = sim.femaleHeading(f), fw = V3(Math.cos(h), 0, Math.sin(h)), base = p.clone().addScaledVector(fw, 1.7).setY(0), o = base.clone().add(V3(0, 1.32, 0)), d = p.clone().add(V3(0, -.02, 0)).sub(o), L = d.length();
      stranger.position.copy(base); stranger.rotation.y = -Math.atan2(d.z, d.x); o.addScaledVector(d.clone().setY(0).normalize(), .5);
      torchBeam.position.copy(o); torchBeam.quaternion.setFromUnitVectors(V3(1, 0, 0), d.normalize()); torchBeam.scale.set(L - .5, .1 * L, .1 * L); torchBeam.material.uniforms.uC.value.setHex(TORCH);
      const on = f.stage >= 4 ? 1 : Math.sin(S.t * TAU * 3.6) > .2 ? 1 : 0; torchBeam.material.uniforms.uA.value = .18 + on * .4; torchBeam.material.uniforms.uCore.value = .35; torchBeam.visible = true; }
    else torchBeam.visible = false;
    const hm = S.visitor.mirror && S.visitor.mirror.until > S.t ? S.visitor.mirror : null; handMirror.visible = !!hm;
    if (hm) { const m = S.males[hm.m], p = mpos(m), h = sim.maleHeading(m); handMirror.position.copy(p).add(V3(Math.cos(h) * .75, hm.dir === 'UP' ? .08 : -.08, Math.sin(h) * .75)); handMirror.lookAt(p); handMirror.rotateX(hm.dir === 'UP' ? .3 : -.3); }
    // snow drifts down
    const SP = SNOW.P; for (let i = 0; i < SNOW.n; i++) { SP[i * 3 + 1] -= dt * (.03 + (i % 7) * .006); if (SP[i * 3 + 1] < 0) SP[i * 3 + 1] += 7; } SNOW.p.geometry.attributes.position.needsUpdate = true;
    drawMat.opacity += ((legend ? .5 : .1) - drawMat.opacity) * Math.min(1, dt * 3); for (const l of labels) l.visible = labelsOn;
    // camera
    director();
    if (D.manual === 'free' || orbitCtl.on) { const o = orbitCtl; camT.pos.set(Math.cos(o.az) * Math.cos(o.el) * o.r, 1.9 + Math.sin(o.el) * o.r, Math.sin(o.az) * Math.cos(o.el) * o.r); camT.look.set(0, 1.9, 0); camT.fov = 42; }
    else { const s = SHOTS[D.shot](S.t - D.since, D.a0, D.focus); camT.pos.copy(s.pos); camT.look.copy(s.look); camT.fov = s.fov; }
    if (cam.aspect < 1) camT.pos.sub(camT.look).multiplyScalar(Math.pow(1 / cam.aspect, .6)).add(camT.look);   // portrait screens: stand back so the shot still holds its subject
    if (D.jump) { cam.position.copy(camT.pos); camLook.copy(camT.look); cam.fov = camT.fov; D.jump = false; }
    else { const k = orbitCtl.on ? Math.min(1, dt * 10) : 1; cam.position.lerp(camT.pos, k);   // auto shots: the camera is the shot, no easing between (a cut is a cut)
      camLook.lerp(camT.look, k); cam.fov += (camT.fov - cam.fov) * k; }
    cam.lookAt(camLook); cam.updateProjectionMatrix();
  }
  // where a beam from p along heading h is cut by the visitor's body or the other male (plan view circles)
  function cutBy(p, h, L) {
    const dx = Math.cos(h), dz = Math.sin(h); let best = L; const circ = [];
    if (S.visitor.body) circ.push(S.visitor.body); for (const m of S.males) { const q = sim.malePos(m); if (Math.hypot(q.x - p.x, q.z - p.z) > .05) circ.push({x: q.x, z: q.z, r: GEOM.body}); }
    for (const c of circ) { const ox = c.x - p.x, oz = c.z - p.z, u = ox * dx + oz * dz; if (u < .1) continue; const d2 = ox * ox + oz * oz - u * u; if (d2 < c.r * c.r) best = Math.min(best, u - Math.sqrt(c.r * c.r - d2)); }
    return Math.max(.05, best);
  }
  function render() { comp.render(); }
  // tap → the nearest agent on screen (for the visitor's gestures), or the floor point under the finger
  function pick(cx, cy) {
    let best = null; const v = V3();
    for (const M of males) { v.copy(M.g.position).project(cam); const x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * H, d = Math.hypot(x - cx, y - cy); if (v.z < 1 && (!best || d < best.d)) best = {kind: 'male', i: S.males.indexOf(M.m), d, sy: y}; }
    for (const F of females) { v.copy(F.g.position).project(cam); const x = (v.x + 1) / 2 * W, y = (1 - v.y) / 2 * H, d = Math.hypot(x - cx, y - cy); if (v.z < 1 && (!best || d < best.d)) best = {kind: 'female', i: S.females.indexOf(F.f), d, sy: y}; }
    return best;
  }
  function floorAt(cx, cy, y0 = 0) { const rc = new THREE.Raycaster(); rc.setFromCamera(new THREE.Vector2(cx / W * 2 - 1, -(cy / H) * 2 + 1), cam); const t = (y0 - rc.ray.origin.y) / rc.ray.direction.y; if (!(t > 0)) return null; const q = rc.ray.origin.clone().addScaledVector(rc.ray.direction, t); return {x: q.x, z: q.z}; }
  function screenOf(kind, i) { const v = (kind === 'male' ? males[i].g.position : females[i].g.position).clone().project(cam); return {x: (v.x + 1) / 2 * W, y: (1 - v.y) / 2 * H}; }
  return {R, scene, cam, comp, bloom, update, render, resize, pick, floorAt, screenOf, director: D, setShot, orbit: orbitCtl, SHOTS: Object.keys(SHOTS),
    setLegend(v) { legend = !!v; labelsOn = !!v; }, get legend() { return legend; }, quality(level) { if (level === 'low') { bloom.strength = .6; resize(W, H, 1); } },
    get pr() { return pr; }, setPR(v) { resize(W, H, v); }, males, females};
}
export {STAGE};
