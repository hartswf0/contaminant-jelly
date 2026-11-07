// The landing: one translucent jelly in dark water. Its bell is a cloud of gaussian flecks with a film's perforated band at the rim;
// a real film frame glows inside the bell; it trails film-strip and filament tentacles; light falls from above; marine snow drifts.
// It breathes, drifts, and leans toward the pointer. Nothing else moves.
//   import {mountHero} from './hero.js';  mountHero(canvas, {frames: i => url, n, fps})
import * as THREE from './paeleo/scion/videotext/vendor/three.module.min.js';

export function mountHero(cv, opt = {}) {
  const R = new THREE.WebGLRenderer({canvas: cv, antialias: true, alpha: false}); R.setPixelRatio(Math.min(2, devicePixelRatio));
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(38, 1, .1, 100); cam.position.set(0, 0, 9);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  // water: a gradient, lighter where the light comes in
  const bg = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.ShaderMaterial({depthWrite: false, uniforms: {uT: {value: 0}},
    vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = vec4(position.xy, .999, 1.); }',
    fragmentShader: `varying vec2 v; uniform float uT; void main(){ vec3 deep = vec3(.008,.016,.032), top = vec3(.03,.07,.12); float g = smoothstep(.0, 1., v.y);
      float shaft = 0.; for (int i = 0; i < 4; i++) { float fi = float(i); float x = .18 + fi * .21 + .03 * sin(uT * .07 + fi * 2.); shaft += exp(-pow((v.x - x - (1. - v.y) * .12) / (.025 + .02 * fi), 2.)) * (.35 - fi * .06); }
      vec3 c = mix(deep, top, g * g) + vec3(.09,.16,.24) * shaft * pow(v.y, 2.2); gl_FragColor = vec4(c, 1.); }`}));
  bg.frustumCulled = false; scene.add(bg);
  // gaussian flecks
  const flecks = (n, fill) => { const P = new Float32Array(n * 3), C = new Float32Array(n * 3), S = new Float32Array(n), A = new Float32Array(n); for (let i = 0; i < n; i++) fill(i, P, C, S, A);
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aC', new THREE.BufferAttribute(C, 3)); g.setAttribute('aS', new THREE.BufferAttribute(S, 1)); g.setAttribute('aA', new THREE.BufferAttribute(A, 1)); return g; };
  const fleckMat = (bend) => new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uT: {value: 0}, uP: {value: 0}, uScale: {value: 1}, uLean: {value: new THREE.Vector2()}},
    vertexShader: `attribute vec3 aC; attribute float aS, aA; uniform float uT, uP, uScale; uniform vec2 uLean; varying vec3 vC; varying float vA;
      void main(){ vec3 p = position; ${bend}
        vec4 mv = modelViewMatrix * vec4(p, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = aS * uScale / -mv.z; vC = aC; vA = aA; }`,
    fragmentShader: `varying vec3 vC; varying float vA; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = exp(-r2 * 14.); gl_FragColor = vec4(vC * vA * g, 1.); }`});
  const jelly = new THREE.Group(); scene.add(jelly);
  // the bell: a half-ellipsoid of flecks; brighter at the rim, an amber glow on the right where light passes through
  const NB = 24000, blue = new THREE.Color('#86a6c6'), pale = new THREE.Color('#d7e6f3'), amber = new THREE.Color('#f2a453');
  const bellG = flecks(NB, (i, P, C, S, A) => { const u = Math.random(), ph = Math.random() * Math.PI * 2, th = Math.acos(1 - u * .98), rim = th / (Math.PI / 2);
    const scal = rim > .9 ? .03 * Math.sin(ph * 22) : 0, r = (Math.sin(th) + scal) * 1.25, y = Math.cos(th) * .95 - .05;
    const band = rim > .86 && rim < .93, hole = band && (ph * 40 / (Math.PI * 2)) % 1 < .38;
    P[i * 3] = Math.cos(ph) * r; P[i * 3 + 1] = band ? .11 - (rim - .86) * 1.6 : y; P[i * 3 + 2] = Math.sin(ph) * r;
    const c = blue.clone().lerp(pale, Math.pow(rim, 3) * .7); const am = Math.max(0, Math.cos(ph) * .8 + .2) * Math.max(0, rim - .35); c.lerp(amber, Math.min(.85, am * 1.1));
    C.set([c.r, c.g, c.b], i * 3); S[i] = band ? 13 : 8 + Math.random() * 14; A[i] = hole ? 0 : band ? .2 : .045 + .11 * Math.pow(rim, 2.5) + .2 * am; });
  const bellM = fleckMat(`float k = uP; p.xz *= 1. + .06 * k * (1. - p.y); p.y *= 1. - .08 * k;`);
  jelly.add(new THREE.Points(bellG, bellM));
  // a film frame glowing inside the bell
  const fc = document.createElement('canvas'); fc.width = 256; fc.height = 192; const fx = fc.getContext('2d'), ftex = new THREE.CanvasTexture(fc);
  const frame = new THREE.Mesh(new THREE.PlaneGeometry(1.25, .94), new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {map: {value: ftex}, uA: {value: 0}},
    vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: `uniform sampler2D map; uniform float uA; varying vec2 v; void main(){ vec3 c = texture2D(map, v).rgb; float l = dot(c, vec3(.3,.59,.11)); float e = smoothstep(.0, .18, v.x) * smoothstep(1., .82, v.x) * smoothstep(.0, .2, v.y) * smoothstep(1., .8, v.y);
      vec3 tone = mix(vec3(.15,.22,.3), vec3(1.,.72,.42), smoothstep(.15, .9, l)); gl_FragColor = vec4(tone * l * 1.5 * e * uA, 1.); }`}));
  frame.position.set(.18, .38, .15); frame.rotation.y = -.25; jelly.add(frame);
  const imgs = new Map(); const img = u => { let e = imgs.get(u); if (!e) { const im = new Image(); im.crossOrigin = 'anonymous'; e = {im, ok: false}; im.onload = () => e.ok = true; im.src = u; imgs.set(u, e); } return e; };
  // tentacles: one film strip, three filaments with bright tips, and soft oral arms
  const NT = 4, TL = 90, tent = []; const tentG = flecks(NT * TL * 2, (i, P, C, S, A) => { const t = Math.floor(i / (TL * 2)), j = Math.floor(i / 2) % TL, side = i % 2, f = j / TL, strip = t === 0;
    P.set([0, 0, 0], i * 3); const hole = strip && j % 4 === 0 && side; const c = strip ? pale.clone().lerp(amber, .25 * (1 - f)) : blue.clone().lerp(pale, .3); C.set([c.r, c.g, c.b], i * 3);
    S[i] = strip ? 20 : (j === TL - 1 && !side ? 40 : 9); A[i] = hole ? 0 : strip ? .22 * (1 - f * .7) : (j === TL - 1 && !side ? .9 : side ? 0 : .16 * (1 - f * .5)); });
  const tentM = fleckMat(''); const tentP = new THREE.Points(tentG, tentM); jelly.add(tentP);
  const arms = flecks(2600, (i, P, C, S, A) => { const f = Math.random(), a = Math.random() * 6.283, r = .35 * (1 - f) * Math.random(); P.set([Math.cos(a) * r, -f * 1.4 + .05, Math.sin(a) * r], i * 3); const c = blue.clone().lerp(pale, .4); C.set([c.r, c.g, c.b], i * 3); S[i] = 10 + Math.random() * 16; A[i] = .05 * (1 - f); });
  const armM = fleckMat(`p.x += sin(uT * .9 + p.y * 3.) * .08 * -p.y; p.z += cos(uT * .7 + p.y * 2.) * .06 * -p.y;`); jelly.add(new THREE.Points(arms, armM));
  // marine snow
  const snow = flecks(900, (i, P, C, S, A) => { P.set([(Math.random() - .5) * 16, (Math.random() - .5) * 10, (Math.random() - .5) * 8 - 2], i * 3); C.set([.7, .8, .9], i * 3); S[i] = 6 + Math.random() * 10; A[i] = .06 + Math.random() * .18; });
  const snowM = fleckMat(`p.y = mod(p.y - uT * .05 + 5., 10.) - 5.; p.x += sin(uT * .2 + position.z) * .1;`); scene.add(new THREE.Points(snow, snowM));
  // life
  const ptr = new THREE.Vector2(), at = new THREE.Vector3(.4, .3, 0), _v = new THREE.Vector3(); let t = 0, last = performance.now(), fi = 0, ft = 0;
  addEventListener('pointermove', e => { ptr.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight * 2 - 1)); }, {passive: true});
  const size = () => { const w = cv.clientWidth, h = cv.clientHeight; R.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); const us = h * R.getPixelRatio() * .5 / Math.tan(cam.fov * Math.PI / 360) / 330;
    [bellM, tentM, armM, snowM].forEach(m => m.uniforms.uScale.value = us); jelly.scale.setScalar(w < h ? .8 : 1); };
  addEventListener('resize', size); size();
  const api = {scroll: 0, stop: false, jelly}; jelly.position.set(cam.aspect < 1 ? .3 : .7, .25, 0);
  (function frameLoop(now) { if (api.stop) return; requestAnimationFrame(frameLoop); const dt = Math.min(.05, (now - last) / 1000); last = now; if (!reduce) t += dt; else t = 2;
    const ph = (t / 3.2) % 1, pulse = ph < .3 ? Math.sin(ph / .3 * Math.PI) : 0; bellM.uniforms.uP.value = pulse;
    // drift: a slow figure, leaning toward the pointer; rising a little on each pulse
    at.set((cam.aspect < 1 ? .3 : .7) + Math.sin(t * .13) * (cam.aspect < 1 ? .25 : .5) + ptr.x * .6, .25 + Math.sin(t * .17) * .25 + ptr.y * .35 - api.scroll * 2.2, 0);
    jelly.position.lerp(at, dt * .5); jelly.rotation.z = THREE.MathUtils.lerp(jelly.rotation.z, -(at.x - jelly.position.x) * .5 - .18, dt); jelly.rotation.y = Math.sin(t * .1) * .4;
    // tentacles follow the bell with a lag, waving
    const pa = tentG.attributes.position.array; for (let k = 0; k < NT; k++) { const x0 = [-.25, -.65, .1, .55][k], z0 = [.2, -.2, .4, -.1][k];
      for (let j = 0; j < TL; j++) { const f = j / TL, len = k === 0 ? 2.9 : 2.3 + k * .25, y = -.02 - f * len, w = Math.sin(t * (1.1 + k * .13) - f * 4.2 + k) * .28 * f + Math.sin(t * .5 - f * 2 + k) * .18 * f * f;
        for (let s = 0; s < 2; s++) { const i = ((k * TL + j) * 2 + s) * 3, off = k === 0 ? (s ? .055 : -.055) : 0; pa[i] = x0 * (1 - f * .3) + w + off; pa[i + 1] = y - pulse * .05 * f; pa[i + 2] = z0 + Math.cos(t * .8 - f * 3 + k) * .12 * f; } } }
    tentG.attributes.position.needsUpdate = true;
    // the film inside: real frames when given, at their own pace
    if (opt.frames) { ft += dt; if (ft > 1 / (opt.fps || 8)) { ft = 0; fi = (fi + 1) % (opt.n || 30); for (let k = 1; k < 3; k++) img(opt.frames(fi + k)); }
      const e = img(opt.frames(fi)); if (e.ok) { fx.drawImage(e.im, 0, 0, fc.width, fc.height); ftex.needsUpdate = true; frame.material.uniforms.uA.value = Math.min(.85, frame.material.uniforms.uA.value + dt * .4); } }
    [bellM, tentM, armM, snowM].forEach(m => m.uniforms.uT.value = t); bg.material.uniforms.uT.value = t;
    R.render(scene, cam); })(performance.now());
  return api;
}
