// DRIFT ENGINE: open water in depth layers; a celluloid jelly; films only as clouds of flecks; no buttons.
// Gestures: hold the water = swim there; tap a film = take a frame; hold on a film = watch it bloom; double-tap = pulse; pinch = pull back; two fingers = look.
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

export async function play(L, ALL) {
  const Q = new URLSearchParams(location.search), DEBUG = Q.has('debug'), COARSE = matchMedia('(pointer: coarse)').matches, $ = id => document.getElementById(id);
  document.body.className = 'game';
  document.body.innerHTML = `<canvas id="gl"></canvas><div class="ui" id="dark"></div><div class="ui" id="flash"></div><div class="ui" id="tag"></div>
    <div class="ui" id="hud"><div><b>${L.title.toUpperCase()}</b> · <span id="goal"></span></div><div id="song"></div></div><div class="ui" id="say"></div><div class="ui" id="hint"></div><div class="ui" id="dbg"></div>
    <div class="ui" id="card"><div class="k">A DRIFT FROM ${L.source.replace('_', ' ').toUpperCase()}</div><h1>${L.title}</h1><p>${L.took}</p><p style="font-style:normal;font-size:14px;color:var(--dim)">Goal: ${L.goal.label}.</p><div class="go">TOUCH THE WATER TO BEGIN</div></div>`;
  const SM = Q.get('sm') || 'https://hartswf0.github.io/secondhand-motion/';
  let FILMS = await (await fetch('../films109.json')).json();
  if (Q.get('films')) { const keep = Q.get('films').split(','); FILMS = FILMS.filter(f => keep.includes(f.slug)); }
  const MUSIC = await fetch('../music.json').then(r => r.json()).catch(() => null), S2G = await fetch('../audio/song2game.json').then(r => r.ok ? r.json() : null).catch(() => null);
  const frameURL = (f, i) => `${SM}${f.dir}/f${String(((i % f.n) + f.n) % f.n).padStart(3, '0')}.jpg`, fps = f => Math.min(10, f.fps || 8);
  const stamp = (film, fi) => { const t = fi / fps(FILMS[film]); return `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`; };
  const IMG = new Map(); const withImg = (url, fn) => { let e = IMG.get(url); if (!e) { const im = new Image(); im.crossOrigin = 'anonymous'; e = {im, ok: false, cbs: []}; im.onload = () => { e.ok = true; e.cbs.forEach(f => f(im)); e.cbs = []; }; im.onerror = () => { e.bad = true; }; im.src = url; IMG.set(url, e); } if (e.ok) fn(e.im); else if (!e.bad) e.cbs.push(fn); };
  const SEED = Q.get('seed') ? +Q.get('seed') : (Math.random() * 1e9) | 0;
  const rnd = (i, k = 0) => { let t = (SEED ^ Math.imul(i + 1, 0x9E3779B1) ^ Math.imul(k + 7, 0x85EBCA77)) >>> 0; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  // ------------------------------------------------ level coordinates: u runs with the current, w across it
  const DIR = L.dir, LEN = L.len, BAND = L.band;
  const W = (u, w, z = 0, out = new THREE.Vector3()) => DIR === 'right' ? out.set(u, w, z) : DIR === 'up' ? out.set(w, u, z) : out.set(w, -u, z);
  const toUW = v => DIR === 'right' ? [v.x, v.y] : DIR === 'up' ? [v.y, v.x] : [-v.y, v.x];
  const caveTongue = u => L.films.layout === 'caves' && u > 40 && u < LEN - 40 ? 1.8 * sm(40, 55, u) * (1 - sm(LEN - 55, LEN - 40, u)) : 0;
  // ------------------------------------------------ renderer
  const renderer = new THREE.WebGLRenderer({canvas: $('gl'), antialias: false, powerPreference: 'high-performance'});
  renderer.setPixelRatio(Math.min(COARSE ? 1.25 : 1.6, devicePixelRatio || 1)); renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const FOG = new THREE.Color(L.fog), TOP = new THREE.Color(L.top || L.fog), scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(FOG.clone(), L.fogD);
  // a lit haze: lighter above, darker below, so black silhouettes stand against it as in the reference plates
  const bgC = document.createElement('canvas'); bgC.width = 4; bgC.height = 256; const bgT = new THREE.CanvasTexture(bgC); bgT.colorSpace = THREE.SRGBColorSpace; scene.background = bgT;
  const paintBG = (col) => { const g = bgC.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 256), hi = col.clone().multiplyScalar(1.7), lo = col.clone().multiplyScalar(.35); gr.addColorStop(0, '#' + hi.getHexString()); gr.addColorStop(.55, '#' + col.getHexString()); gr.addColorStop(1, '#' + lo.getHexString()); g.fillStyle = gr; g.fillRect(0, 0, 4, 256); bgT.needsUpdate = true; }; paintBG(FOG); let bgLast = '';
  const camera = new THREE.PerspectiveCamera(50, 1, .1, 300);
  const composer = new EffectComposer(renderer); composer.addPass(new RenderPass(scene, camera)); const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .8, .6, .62); composer.addPass(bloom); composer.addPass(new OutputPass());
  const resize = () => { renderer.setSize(innerWidth, innerHeight, false); composer.setSize(innerWidth, innerHeight); bloom.setSize(innerWidth / 2, innerHeight / 2); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }; addEventListener('resize', resize); resize();
  // ------------------------------------------------ silhouette layers, drawn by hand-made rules on canvas (after the reference plates: reefs with glowing bulbs, ruins, kelp, caves, mussel beds, silt)
  function strip(kind, glow, seed) {
    const c = document.createElement('canvas'); c.width = 2048; c.height = 512; const g = c.getContext('2d'), r = i => rnd(seed * 977 + i, 3), H = 512, Wd = 2048;
    g.fillStyle = '#030707'; g.strokeStyle = '#030707'; const bulbs = [];
    const mound = (base, amp, k) => { g.beginPath(); g.moveTo(0, H); for (let x = 0; x <= Wd; x += 16) { const y = H - base - amp * (.5 + .5 * Math.sin(x * k + seed) * Math.sin(x * k * .37 + seed * 2)) - 14 * r(x); g.lineTo(x, y); } g.lineTo(Wd, H); g.fill(); };
    const fan = (x, y, len, ang, d) => { if (d > 6 || len < 4) { bulbs.push([x, y]); return; } const x2 = x + Math.cos(ang) * len, y2 = y - Math.sin(ang) * len; g.lineWidth = Math.max(1, 6 - d); g.beginPath(); g.moveTo(x, y); g.lineTo(x2, y2); g.stroke(); for (let k = 0; k < 2; k++) fan(x2, y2, len * (.7 + .1 * r(x2 + k)), ang + (k ? .45 : -.45) + (r(y2 + k) - .5) * .4, d + 1); };
    const kelp = (x, h) => { g.lineWidth = 3; g.beginPath(); g.moveTo(x, H); for (let y = 0; y < h; y += 10) g.lineTo(x + Math.sin(y * .02 + x) * 14, H - y); g.stroke(); for (let y = 30; y < h; y += 26) { g.beginPath(); g.ellipse(x + Math.sin(y * .02 + x) * 14 + 10, H - y, 12, 4, -.5, 0, 7); g.fill(); } };
    if (kind === 'reef') { mound(110, 90, .006); for (let i = 0; i < 14; i++) { const x = r(i) * Wd; fan(x, H - 120 - r(i + 9) * 60, 40 + r(i + 3) * 40, Math.PI / 2 + (r(i + 5) - .5) * .8, 0); } for (let i = 0; i < 24; i++) { const x = r(i + 40) * Wd; g.beginPath(); g.ellipse(x, H - 110 - r(i) * 50, 14 + r(i + 1) * 12, 6, 0, Math.PI, 0); g.fill(); } }
    if (kind === 'kelp') { mound(40, 30, .01); for (let i = 0; i < 26; i++) kelp(r(i) * Wd, 220 + r(i + 7) * 260); }
    if (kind === 'ruin') { mound(70, 40, .005); for (let k = 0; k < 2; k++) { const x0 = 300 + k * 1000 + r(k) * 200, w = 600; g.beginPath(); g.moveTo(x0, H); g.lineTo(x0, H - 260); for (let x = x0; x < x0 + w; x += 40) { g.lineTo(x, H - 260); g.lineTo(x, H - 290); g.lineTo(x + 22, H - 290); g.lineTo(x + 22, H - 260); } g.lineTo(x0 + w, H - 260); g.lineTo(x0 + w, H); g.lineTo(x0 + w - 120, H); g.arc(x0 + w / 2, H, w / 2 - 120, 0, Math.PI, true); g.lineTo(x0, H); g.fill();
        g.lineWidth = 2; for (let i = 0; i < 8; i++) { g.beginPath(); g.moveTo(x0 + i * 70, H - 260); g.quadraticCurveTo(x0 + i * 70 + 35, H - 200, x0 + i * 70 + 70, H - 262); g.stroke(); } for (let i = 0; i < 10; i++) bulbs.push([x0 + r(i + k * 20) * w, H - 250 - r(i + 5) * 40]); } for (let i = 0; i < 8; i++) fan(r(i + 70) * Wd, H - 70, 30, Math.PI / 2, 1); }
    if (kind === 'pipes') { for (let k = 0; k < 3; k++) { const y = H - 60 - k * 90 - r(k) * 30, t = 30 + k * 8; g.fillRect(0, y - t, Wd, t * 2); for (let x = r(k + 4) * 200; x < Wd; x += 180 + r(x) * 120) { g.fillRect(x, y - t - 10, 18, t * 2 + 20); if (r(x + 1) < .4) for (let d = 0; d < 6; d++) g.fillRect(x + 6, y + t + d * 14, 4, 8); } } mound(30, 20, .02); }
    if (kind === 'cave') { mound(50, 40, .004); for (let i = 0; i < 60; i++) { const x = r(i) * Wd, h = 80 + r(i + 1) * 300, w = 16 + r(i + 2) * 40; g.beginPath(); g.moveTo(x - w, H - 40); g.lineTo(x, H - 40 - h); g.lineTo(x + w, H - 40); g.fill(); if (r(i + 3) < .3) { g.lineWidth = 1.5; g.beginPath(); g.moveTo(x, H - 40 - h); g.lineTo(x + 4, H - 40 - h - 40); g.stroke(); } } }
    if (kind === 'mussels') { mound(60, 30, .008); for (let i = 0; i < 260; i++) { const x = r(i) * Wd, y = H - 50 - r(i + 1) * 70, a = 10 + r(i + 2) * 18; g.fillStyle = '#030707'; g.beginPath(); g.ellipse(x, y, a, a * .6, (r(i + 3) - .5) * 1.4, 0, 7); g.fill(); g.strokeStyle = 'rgba(120,150,140,.55)'; g.lineWidth = 1.2; g.beginPath(); g.ellipse(x, y, a, a * .6, (r(i + 3) - .5) * 1.4, Math.PI * 1.1, Math.PI * 1.7); g.stroke(); } }
    if (kind === 'dunes') { g.fillStyle = '#0a100e'; mound(60, 70, .002); g.fillStyle = '#030707'; mound(20, 30, .006); for (let i = 0; i < 18; i++) { g.fillStyle = 'rgba(0,0,0,.6)'; g.beginPath(); g.ellipse(r(i) * Wd, H - 30 - r(i + 2) * 30, 9, 4, 0, 0, 7); g.fill(); } }
    for (const [x, y] of bulbs) if (r(x + y) < glow) { const gr = g.createRadialGradient(x, y, 0, x, y, 7); gr.addColorStop(0, 'rgba(255,255,250,1)'); gr.addColorStop(1, 'rgba(255,255,250,0)'); g.fillStyle = gr; g.fillRect(x - 7, y - 7, 14, 14); }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; return t;
  }
  const SPAN = LEN + 200, SH = 18;
  L.layers.forEach((ly, i) => { const tex = strip(ly.kind, ly.glow, i + 1); tex.repeat.set(SPAN / (SH * 4), 1); tex.offset.x = rnd(i, 9);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(SPAN, SH), new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false, fog: true, opacity: ly.z > 0 ? .95 : 1}));
    const across = ly.side * (BAND + 2.5 + (ly.z > 0 ? 1.5 : 0) + Math.max(0, -ly.z) * .12), mid = LEN / 2;   // the silhouettes rise to the edges of the open water
    W(mid, across, ly.z, m.position); m.rotation.z = DIR === 'right' ? (ly.side > 0 ? Math.PI : 0) : (ly.side > 0 ? Math.PI / 2 : -Math.PI / 2); m.renderOrder = ly.z > 0 ? 5 : -1; scene.add(m); });
  if (L.films.layout === 'caves') for (const sd of [-1, 1]) { const tex = strip('cave', .3, 40 + sd); tex.repeat.set(SPAN / (SH * 4), 1); const m = new THREE.Mesh(new THREE.PlaneGeometry(LEN - 80, SH * .7), new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false, fog: true}));
    W(LEN / 2, sd * 5.3, -.5, m.position); m.rotation.z = sd > 0 ? 0 : Math.PI; scene.add(m); }   // the rock tongue between the twin caves: its spikes face both caves
  { const c = document.createElement('canvas'); c.width = 64; c.height = 512; const g = c.getContext('2d'), gr = g.createLinearGradient(0, 0, 0, 512); gr.addColorStop(0, 'rgba(200,230,220,0)'); gr.addColorStop(.18, 'rgba(200,230,220,.5)'); gr.addColorStop(1, 'rgba(200,230,220,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 512); const gx = g.getImageData(0, 0, 64, 512); for (let y = 0; y < 512; y++) for (let x = 0; x < 64; x++) gx.data[(y * 64 + x) * 4 + 3] *= Math.sin(x / 63 * Math.PI) ** 2; g.putImageData(gx, 0, 0);
    const tex = new THREE.CanvasTexture(c); for (let i = 0; i < 9; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(6 + rnd(i, 30) * 8, 110), new THREE.MeshBasicMaterial({map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: .25 + rnd(i, 31) * .2, fog: false}));
      W(rnd(i, 32) * LEN, (rnd(i, 35) * 2 - 1) * BAND * 1.6, -40 - rnd(i, 33) * 20, m.position); if (DIR === 'right') m.position.y = BAND + 14; m.rotation.z = (rnd(i, 34) - .5) * .5; scene.add(m); } }   // light shafts always fall from above
  // the surface: an edgeless sheet of light that ripples overhead
  let surfMat = null; if (L.surface) { const n = 6000, P = new Float32Array(n * 3), A = new Float32Array(n); for (let i = 0; i < n; i++) { const a = Math.random() * 6.283, r = Math.sqrt(Math.random()); const p = W(LEN + 3, Math.cos(a) * r * 26, Math.sin(a) * r * 18 - 4); P.set([p.x, p.y, p.z], i * 3); A[i] = r; }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aR', new THREE.BufferAttribute(A, 1));
    surfMat = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uTime: {value: 0}, uScale: {value: 1}},
      vertexShader: `uniform float uTime, uScale; attribute float aR; varying float vA; void main(){ vec3 p = position; p.y += sin(p.x * .4 + uTime) * .3 + sin(p.z * .5 - uTime * .7) * .25; vec4 mv = modelViewMatrix * vec4(p, 1.); vA = (1. - aR) * (.5 + .5 * sin(p.x * 2. + p.z * 1.7 + uTime * 2.)); gl_PointSize = max(1., .16 * uScale / -mv.z); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `varying float vA; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; gl_FragColor = vec4(vec3(.8, .95, .9) * vA * (1. - 4. * r2) * .5, 1.); }`});
    const pts = new THREE.Points(g, surfMat); pts.frustumCulled = false; scene.add(pts); }
  // ------------------------------------------------ frame atlas and the splat engine (films are clouds of flecks that resolve, flow and part around the swimmer)
  const ATW = 2048, SWd = 128, SHt = 96, COLS = 16, BLOCK = 8, NBLOCK = 42;
  const atlasC = document.createElement('canvas'); atlasC.width = atlasC.height = ATW; atlasC.getContext('2d').fillRect(0, 0, ATW, ATW);
  const atlas = new THREE.CanvasTexture(atlasC); atlas.colorSpace = THREE.SRGBColorSpace; atlas.generateMipmaps = false; atlas.minFilter = THREE.LinearFilter;
  const slotC = document.createElement('canvas'); slotC.width = SWd; slotC.height = SHt; const sgx = slotC.getContext('2d'), slotTex = new THREE.CanvasTexture(slotC); slotTex.colorSpace = THREE.SRGBColorSpace; const _v2 = new THREE.Vector2();
  const putSlot = (slot, im) => { sgx.drawImage(im, 0, 0, SWd, SHt); _v2.set((slot % COLS) * SWd, ATW - (((slot / COLS) | 0) + 1) * SHt); slotTex.needsUpdate = true; renderer.copyTextureToTexture(_v2, slotTex, atlas); };
  const free = Array.from({length: NBLOCK - 2}, (_, i) => i + 2), tags = new Int32Array(NBLOCK); let tagN = 0;
  const take = () => free.length ? free.shift() : -1, give = b => { if (b > 1) { tags[b] = -1; free.push(b); } };
  const loadClip = (b, film, from) => { const t = ++tagN; tags[b] = t; for (let i = 0; i < BLOCK; i++) withImg(frameURL(FILMS[film], from + i), im => { if (tags[b] === t) putSlot(b * BLOCK + i, im); }); };
  const loadList = (b, film, list) => { const t = ++tagN; tags[b] = t; for (let i = 0; i < BLOCK; i++) withImg(frameURL(FILMS[film], list[Math.min(list.length - 1, i)]), im => { if (tags[b] === t) putSlot(b * BLOCK + i, im); }); };
  const MAXC = 220, PT = new Float32Array(MAXC * 20), params = new THREE.DataTexture(PT, 5, MAXC, THREE.RGBAFormat, THREE.FloatType); params.needsUpdate = true;
  const row = (r, k, a, b, c, d) => PT.set([a, b, c, d], (r * 5 + k) * 4), hide = r => row(r, 1, -1, 1, 0, 0);
  const uR = {value: new THREE.Vector3()}, uU = {value: new THREE.Vector3()}, uF = {value: new THREE.Vector3()};
  const splat = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uP: {value: params}, uAtlas: {value: atlas}, uTime: {value: 0}, uScale: {value: 1}, uFog: {value: L.fogD}, uJ: {value: new THREE.Vector3()}, uJv: {value: new THREE.Vector3()}, uBeat: {value: 0}, uR, uU, uF},
    vertexShader: `uniform sampler2D uP, uAtlas; uniform vec3 uR, uU, uF, uJ, uJv; uniform float uTime, uScale, uFog, uBeat; attribute float aCloud; attribute vec4 aUV; varying vec3 vC; varying float vA;
      vec4 P(int k){ return texelFetch(uP, ivec2(k, int(aCloud + .5)), 0); } float hs(float n){ return fract(sin(n) * 43758.5453); }
      void main(){ vec4 a = P(0), b = P(1), c = P(2), d = P(3), e = P(4); float sf = 1. + e.x;
        if (b.w < .003) { gl_Position = vec4(2., 2., 2., 1.); gl_PointSize = 0.; vA = 0.; return; }
        vec2 uv = aUV.xy; float seed = aUV.z, bad = c.z; bool tick = bad > .5 && seed < .16; if (tick) { float an = seed * 390. + uTime * 1.6; uv = vec2(cos(an), sin(an)) * 1.25; }
        float r2 = dot(uv, uv); vec3 im = vec3(0.); float l = 0.;
        if (b.x >= 0.) { float fr = mod(floor(b.z), ${BLOCK}.), slot = b.x * ${BLOCK}. + fr, col = mod(slot, ${COLS}.), rw = floor(slot / ${COLS}.); vec2 iu = clamp(uv * .5 + .5, .01, .99);
          im = texture2D(uAtlas, vec2((col + iu.x) * ${SWd}. / ${ATW}., 1. - (rw + 1. - iu.y) * ${SHt}. / ${ATW}.)).rgb; l = dot(im, vec3(.3, .55, .15)); }
        float dz = (l - .5) * c.y * a.w, dist = max(.5, length(a.xyz - cameraPosition));
        vec3 off = (uR * uv.x * b.y + uU * uv.y) * a.w * (dist - dz) / dist + uF * dz, fl3 = vec3(sin(uTime * 1.3 + seed * 41.), cos(uTime * 1.05 + seed * 31.), sin(uTime * .9 + seed * 17.));
        off += a.w * (.006 + .11 * r2 * r2 + e.w * (.08 + .3 * r2)) * fl3;   // fluid: far films are drifting flecks, near films a picture
        if (bad > .5 && !tick) { float t = floor(uTime * 22.); off += a.w * .1 * vec3(hs(seed + t) - .5, hs(seed * 3. + t) - .5, 0.); }
        vec3 p = a.xyz + off; vec3 dj = p - uJ; float w = exp(-dot(dj, dj) / 2.4); vec3 jv = uJv + vec3(1e-4); p += (normalize(dj + 1e-4) * .5 + cross(normalize(jv), dj) * .35 + jv * .1) * w;   // the jelly's wake
        if (c.w > 0.) { float q = clamp(c.w * 1.7 - seed * .7, 0., 1.); q = q * q * (3. - 2. * q); p = mix(p, d.xyz, q); }
        float lf = .06 + .94 * smoothstep(.06, .82, l); vec3 tc = mix(vec3(lf), im + .1, .55), g = b.x >= 0. ? mix(tc * vec3(.9, .98, 1.) * 1.5, tc * vec3(1., .86, .62) * 1.45, d.w) : vec3(1., .64, .26) * .55;
        if (bad > .5) g = tick ? vec3(1., .25, .1) * 1.4 : vec3(1., .16, .06) * (.2 + .9 * hs(seed * 9. + floor(uTime * 16.)));
        vec4 mv = viewMatrix * vec4(p, 1.); float fog = exp(-pow(uFog * .9 * -mv.z, 2.)) * smoothstep(.8, 2.2, -mv.z);
        vC = g * (1. + .1 * uBeat); vA = b.w / (sf * sf) * exp(-r2 * (e.y > 0. ? e.y : 2.4)) * fog * (c.w > 0. ? 1. - c.w : 1.) * (tick ? 2.5 : 1.);
        gl_PointSize = max(1.5, (.55 + 1.1 * fract(seed * 7.)) * sf * aUV.w * a.w * uScale / -mv.z * (tick ? .5 : 1.)); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying vec3 vC; varying float vA; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = (exp(-r2 * 12.) - .0498) / .9502; gl_FragColor = vec4(vC * g * vA * .55, 1.); }`});
  const cloud = (first, n, pts, spread = 1.12) => { const N = n * pts, aC = new Float32Array(N), aU = new Float32Array(N * 4), kw = spread * Math.sqrt(3 * Math.PI / pts);
    for (let r = 0; r < n; r++) for (let i = 0; i < pts; i++) { const k = r * pts + i, a = Math.random() * 6.283, rr = Math.sqrt(Math.random()) * spread; aC[k] = first + r; aU.set([Math.cos(a) * rr, Math.sin(a) * rr, Math.random(), kw], k * 4); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3)); g.setAttribute('aCloud', new THREE.BufferAttribute(aC, 1)); g.setAttribute('aUV', new THREE.BufferAttribute(aU, 4));
    const p = new THREE.Points(g, splat); p.frustumCulled = false; scene.add(p); };
  const NFR = 18, NCH = 40, NAR = 8, AN = 14, NCAST = 8;
  const FROW = 0, VROW = FROW + NFR, CHROW = VROW + 1, XROW = CHROW + NCH, FLROW = XROW + 1, CROW = FLROW + 2, AROW = CROW + NCAST, COREROW = AROW + NAR * AN;
  cloud(FROW, NFR, 4200); cloud(VROW, 1, 52000, 1.1); cloud(CHROW, NCH, 700); cloud(XROW, 1, 1500, 1.2); cloud(FLROW, 2, 500); cloud(CROW, NCAST, 30); cloud(AROW, NAR * AN, 90, 1); cloud(COREROW, 1, 700);
  for (let r = 0; r < MAXC; r++) hide(r);
  // ------------------------------------------------ the films of this drift, translated from its video
  const SP = []; let order = 0;
  { const lay = L.films.layout, every = L.films.every || 10, add = (o) => { const film = (rnd(SP.length, 41) * FILMS.length) | 0; SP.push({i: SP.length, film, from: (rnd(SP.length, 42) * 40) | 0, z: 0, size: 2.4, budget: 3, bad: false, slot: -1, sleep: false, buried: false, pair: -1, ring: false, ...o}); };
    const scatter = (u0, u1, step, opt = {}) => { for (let u = u0; u < u1; u += step * (.7 + .6 * rnd(u, 43))) { const k = SP.length, bad = rnd(k, 44) < L.bad, back = !bad && rnd(k, 45) < .3;
        add({u, w: (rnd(k, 46) * 2 - 1) * BAND * .8, z: back ? -7 : 0, size: back ? 3.4 + rnd(k, 47) : 1.9 + rnd(k, 48) * 1.1, bad, ...opt}); } };
    if (lay === 'scatter' || lay === 'stream') scatter(12, LEN - 8, every, lay === 'stream' ? {size: 1.8} : {});
    if (lay === 'dark') scatter(12, LEN - 8, every, {dark: true});
    if (lay === 'giant') { add({u: 16, w: BAND * .35, z: -5, size: 8.5, budget: 5, giant: true}); scatter(34, LEN - 8, every); }
    if (lay === 'tiers') for (let u = 10, t = 0; u < LEN - 8; u += every, t++) for (const sd of [-1, 1]) add({u: u + sd * 1.5, w: sd * (BAND - 1.6 - (t % 2) * 2), z: -(t % 3) * 4, size: 2 + (t % 3) * .5, sleep: true, bad: rnd(u + sd, 49) < L.bad});
    if (lay === 'pairs') { let p = 0; for (let u = 14; u < LEN - 10; u += every * (.8 + .4 * rnd(u, 50))) { const w0 = (rnd(u, 51) * 2 - 1) * BAND * .5; add({u, w: w0 - 2.4, pair: p, size: 2.6}); add({u, w: w0 + 2.4, pair: p, size: 2.6}); p++; if (rnd(u, 52) < L.bad * 2) add({u: u + 7, w: (rnd(u, 53) * 2 - 1) * BAND * .7, bad: true, size: 1.4}); } }
    if (lay === 'halo') { scatter(14, LEN - 34, every); for (let k = 0; k < 8; k++) add({u: LEN - 16, w: 0, ring: k, size: 2.3, budget: 2}); }
    if (lay === 'caves') { for (let u = 14; u < LEN - 10; u += every * (.7 + .6 * rnd(u, 54))) { const up = rnd(u, 55) < .5; add({u, w: (up ? 1 : -1) * (4.8 + rnd(u, 56) * (BAND - 6.5)), size: up ? 2.2 : 2.8, bad: rnd(u, 57) < L.bad}); } }
    if (lay === 'buried') for (let u = 12; u < LEN - 10; u += every * (.7 + .6 * rnd(u, 58))) add({u, w: -BAND + .9 + rnd(u, 59) * .8, size: 2.2, buried: true});
    if (lay === 'chain') { for (let u = 40; u < LEN - 20; u += 16) add({u, w: (rnd(u, 62) * 2 - 1) * BAND * .8, bad: true, size: 1.2 + rnd(u, 63)}); }
  }
  var CHAIN; // declared below (hoisting for the chain layout)
  // ------------------------------------------------ marine snow and silt that the animals push
  const NSN = 2600, snP = new Float32Array(NSN * 3), snA = new Float32Array(NSN), sn = Array.from({length: NSN}, () => ({x: (Math.random() - .5) * 44, y: (Math.random() - .5) * 30, z: -32 + Math.random() * 38, vx: 0, vy: 0, s: Math.random()}));
  const snG = new THREE.BufferGeometry(); snG.setAttribute('position', new THREE.BufferAttribute(snP, 3)); snG.setAttribute('aS', new THREE.BufferAttribute(snA, 1));
  const snM = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uScale: {value: 1}, uHigh: {value: 0}, uFog: {value: L.fogD}},
    vertexShader: `uniform float uScale, uHigh, uFog; attribute float aS; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); float z = -mv.z; vA = exp(-pow(uFog * .8 * z, 2.)) * smoothstep(1., 3., z) * (.2 + .35 * aS + .3 * uHigh * fract(aS * 31.)); gl_PointSize = max(1., (.03 + .03 * aS) * uScale / z); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying float vA; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; gl_FragColor = vec4(vec3(.62, .78, .78) * vA * (1. - 4. * r2), 1.); }`});
  const snPts = new THREE.Points(snG, snM); snPts.frustumCulled = false; scene.add(snPts);
  const PUSH = [];
  // ------------------------------------------------ the jelly: three celluloid sheets with sprocket holes, contracting one after another
  const CS = .8, J = {u: 6, w: L.startW ?? 0, vu: 0, vw: 0, ph: 0, p: new THREE.Vector3(), pv: new THREE.Vector3(), mem: 100, hurt: 0, glow: 0, stun: 0, slip: 0, target: null};
  const BN = 5000, bg = new THREE.BufferGeometry(), bp = new Float32Array(BN * 3), bt = new Float32Array(BN), bs = new Float32Array(BN), bl = new Float32Array(BN);
  { let k = 0; for (const [Ly, rad, per] of [[0, .62, 1250], [1, .78, 1650], [2, .92, 2100]]) for (let i = 0, tr = 0; i < per && k < BN && tr < per * 4; tr++) { const t = Math.sqrt(Math.random()), a = t * Math.PI / 2 * 1.05, ph = Math.random() * 6.283;
      if ((t > .86 && Math.floor(ph / 6.283 * 44) % 2 === 0 && Math.random() < .85) || (Math.abs(((ph / 6.283 * 8) % 1) - .5) < .025 && Math.random() < .7)) continue;
      bp.set([Math.cos(ph) * rad * Math.sin(a), rad * .8 * Math.cos(a), Math.sin(ph) * rad * Math.sin(a)], k * 3); bt[k] = t; bs[k] = Math.random(); bl[k] = Ly; k++; i++; } }
  bg.setAttribute('position', new THREE.BufferAttribute(bp, 3)); bg.setAttribute('aT', new THREE.BufferAttribute(bt, 1)); bg.setAttribute('aS', new THREE.BufferAttribute(bs, 1)); bg.setAttribute('aL', new THREE.BufferAttribute(bl, 1));
  const bellM = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uPulse: {value: 0}, uTime: {value: 0}, uScale: {value: 1}, uGlow: {value: 0}, uHurt: {value: 0}, uFray: {value: 0}},
    vertexShader: `uniform float uPulse, uTime, uScale, uFray; attribute float aT, aS, aL; varying float vT, vS, vL;
      float c(float ph){ ph = fract(ph); return ph < .28 ? sin(ph / .28 * 1.5708) : 1. - smoothstep(0., 1., (ph - .28) / .72); }
      void main(){ vec3 p = position; float k = c(uPulse - aT * .18 - aL * .06) * pow(aT, 1.3); p.xz *= 1. - .3 * k; p.y += .16 * k * (1. - aT) + .05 * k; p += uFray * aL * .12 * vec3(sin(aS * 91. + uTime * 3.), cos(aS * 77.), sin(aS * 63.));
        vT = aT; vS = aS; vL = aL; vec4 mv = modelViewMatrix * vec4(p, 1.); gl_PointSize = (1.6 + 2.2 * aS) * (1.15 - .15 * aL) * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uGlow, uHurt; varying float vT, vS, vL; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = (exp(-r2 * 14.) - .0302) / .9698;
      vec3 col = vL < .5 ? vec3(1., .5, .12) : vL < 1.5 ? vec3(1., .72, .3) : vec3(1., .9, .66); if (vL > 1.5) col += vec3(-.05, .03, .08) * sin(vS * 40.);
      col *= (.45 + .9 * pow(vT, 4.)) * (1. + uGlow) * (vL > 1.5 ? .7 : 1.); col = mix(col, vec3(1., .12, .05), uHurt * .6); gl_FragColor = vec4(col * g * .24, 1.); }`});
  const bell = new THREE.Points(bg, bellM); bell.frustumCulled = false; const jelly = new THREE.Group(); jelly.add(bell); jelly.scale.setScalar(CS); scene.add(jelly);
  // arms: one per recovered film, its frames in source order, trailing in the water
  const ARMS = [], CUT = [], AX = new Float32Array(NAR * AN * 3), AXP = new Float32Array(NAR * AN * 3);
  const armRoot = (k, out) => { const a = k / NAR * 6.283; return out.set(Math.cos(a) * .7, -.1, Math.sin(a) * .7).multiplyScalar(CS).add(J.p); };
  const _a = new THREE.Vector3(), _b = new THREE.Vector3(), _c = new THREE.Vector3();
  function stepArms(dt) { const water = W(L.current, 0, 0, _c).sub(W(0, 0, 0, _b)).multiplyScalar(.5);
    ARMS.forEach((A, k) => { const n = Math.max(2, Math.round(A.n)); armRoot(k, _a); const i0 = k * AN * 3; AX[i0] = AXP[i0] = _a.x; AX[i0 + 1] = AXP[i0 + 1] = _a.y; AX[i0 + 2] = AXP[i0 + 2] = _a.z;
      for (let j = 1; j < AN; j++) { const i = (k * AN + j) * 3; if (j >= n) { const p = (k * AN + n - 1) * 3; AX[i] = AXP[i] = AX[p]; AX[i + 1] = AXP[i + 1] = AX[p + 1]; AX[i + 2] = AXP[i + 2] = AX[p + 2]; continue; }
        for (let c = 0; c < 3; c++) { const v = (AX[i + c] - AXP[i + c]) / dt, wv = c === 0 ? water.x : c === 1 ? water.y - .4 : 0, f = -2.2 * (v - wv) + Math.sin(T * 2.2 - j * .5 + k * 1.3 + c) * .6 * (j / AN); const nx = AX[i + c] + (AX[i + c] - AXP[i + c]) * .97 + f * dt * dt; AXP[i + c] = AX[i + c]; AX[i + c] = nx; } }
      for (let it = 0; it < 8; it++) for (let j = 0; j < n - 1; j++) { const a = (k * AN + j) * 3, b = a + 3; let dx = AX[b] - AX[a], dy = AX[b + 1] - AX[a + 1], dz = AX[b + 2] - AX[a + 2]; const d = Math.hypot(dx, dy, dz) || 1e-6, e = (d - .14) / d, wa = j ? .5 : 0, wb = j ? .5 : 1;
        AX[a] += dx * e * wa; AX[a + 1] += dy * e * wa; AX[a + 2] += dz * e * wa; AX[b] -= dx * e * wb; AX[b + 1] -= dy * e * wb; AX[b + 2] -= dz * e * wb; }
      A.n += (A.target - A.n) * Math.min(1, dt * 1.5); }); }
  const armFrames = A => { const f = A.frames.map(x => x.fi).sort((a, b) => a - b); return f.length <= BLOCK ? f : Array.from({length: BLOCK}, (_, i) => f[Math.round(i * (f.length - 1) / (BLOCK - 1))]); };
  function addFrame(film, fi, tag) { let A = ARMS.find(a => a.film === film), isNew = false; if (A && A.frames.some(x => x.fi === fi)) return 'dup';
    if (!A) { if (ARMS.length >= NAR) return 'full'; const b = take(); if (b < 0) return 'full'; A = {film, frames: [], block: b, n: 2, target: 2}; ARMS.push(A); isNew = true; armRoot(ARMS.length - 1, _a); for (let j = 0; j < AN; j++) { const i = ((ARMS.length - 1) * AN + j) * 3; AX[i] = AXP[i] = _a.x; AX[i + 1] = AXP[i + 1] = _a.y - j * .14; AX[i + 2] = AXP[i + 2] = _a.z; } }
    A.frames.push({fi}); loadList(A.block, film, armFrames(A)); A.target = Math.min(AN, 4 + 2 * A.frames.length); CUT.push({film, fi, tag}); return isNew ? 'new' : 'grow'; }
  // ------------------------------------------------ creatures (each with a motion and an effect on the water)
  const CREAT = new Set(L.creatures), pointsMat = (col, size, extra = '') => new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uScale: {value: 1}, uTime: {value: 0}, uFog: {value: L.fogD}},
    vertexShader: `uniform float uScale, uTime, uFog; attribute float aK; varying float vA, vK; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); float z = -mv.z; vK = aK; vA = exp(-pow(uFog * .9 * z, 2.)) * smoothstep(1., 3., z); gl_PointSize = max(1., ${size} * uScale / z); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uTime; varying float vA, vK; vec3 hue(float h){ return clamp(abs(fract(h + vec3(0., .33, .67)) * 6. - 3.) - 1., 0., 1.); } void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; vec3 c = ${col}; ${extra} gl_FragColor = vec4(c * vA * (1. - 4. * r2), 1.); }`});
  const mkPts = (n, mat) => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3)); g.setAttribute('aK', new THREE.BufferAttribute(new Float32Array(n), 1)); const p = new THREE.Points(g, mat); p.frustumCulled = false; scene.add(p); return p; };
  // a school of flecks
  const FISH = CREAT.has('school') ? Array.from({length: 70}, (_, i) => ({p: new THREE.Vector3(), v: new THREE.Vector3(), o: [Math.random() * 6.28, Math.random() * 6.28], init: false})) : [];
  const fishPts = FISH.length ? mkPts(FISH.length * 3, pointsMat('vec3(.7,.86,.9) * .6', '(.1 - .03 * vK)')) : null; const school = {u: 30, w: 3};
  // comb jellies: rainbow combs that drift on the current and trace it
  const COMB = CREAT.has('comb') ? Array.from({length: 7}, (_, i) => ({u: 20 + i * (LEN - 40) / 6 + rnd(i, 70) * 8, w: (rnd(i, 71) * 2 - 1) * BAND * .7, z: rnd(i, 72) < .5 ? 0 : -6, t: rnd(i, 73) * 9, p: new THREE.Vector3()})) : [];
  const combLocal = Array.from({length: 200}, (_, i) => { const row8 = i % 8, isRow = i >= 120, a = isRow ? row8 / 8 * 6.283 : Math.random() * 6.283, v = isRow ? (i - 120) / 80 : Math.random(); return [Math.cos(a) * .3 * Math.sin(v * Math.PI), .45 * Math.cos(v * Math.PI), Math.sin(a) * .3 * Math.sin(v * Math.PI), isRow ? 1 + row8 / 8 + v * .5 : 0]; });
  const combPts = COMB.length ? mkPts(COMB.length * 200, pointsMat('vK > .5 ? hue(vK + uTime * .35) * (.5 + .5 * sin(uTime * 9. - vK * 30.)) * .8 : vec3(.14, .2, .24) * .35', '(vK > .5 ? .07 : .05)')) : null;
  if (combPts) { const a = combPts.geometry.attributes.aK.array; COMB.forEach((c, ci) => combLocal.forEach((l, i) => { a[ci * 200 + i] = l[3]; })); combPts.geometry.attributes.aK.needsUpdate = true; }
  // shrimp that flick away and kick up silt
  const SHR = CREAT.has('shrimp') ? Array.from({length: 60}, (_, i) => ({home: 30 + Math.floor(i / 20) * (LEN - 60) / 2, o: [Math.random() * 6.28, Math.random() * 6.28], p: new THREE.Vector3(), v: new THREE.Vector3(), init: false, scare: 0})) : [];
  const shrPts = SHR.length ? mkPts(SHR.length * 2, pointsMat('vec3(1., .55, .45) * .55', '.06')) : null;
  // the ray: a wide glider whose wake pulls the water and you
  let RAY = null; if (CREAT.has('ray')) { const pts = [], kk = []; for (let i = 0; i < 1500; i++) { const uu = Math.random() * 2 - 1, ch = 1.6 * (1 - Math.pow(Math.abs(uu), 1.4)), edge = Math.random() < .3; pts.push(uu * 3.4, 0, edge ? ch * .55 : (Math.random() * .9 - .35) * ch); kk.push(edge ? 1 : 0); } for (let i = 0; i < 120; i++) { pts.push(0, 0, -.6 - i / 30); kk.push(.5); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); g.setAttribute('aK', new THREE.Float32BufferAttribute(kk, 1));
    const m = new THREE.Points(g, new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uScale: {value: 1}, uTime: {value: 0}, uFog: {value: L.fogD}},
      vertexShader: `uniform float uScale, uTime, uFog; attribute float aK; varying float vA, vK; void main(){ vec3 p = position; p.y += sin(uTime * 1.7 - abs(p.x) * .8) * .5 * abs(p.x) / 3.4; vec4 mv = modelViewMatrix * vec4(p, 1.); float z = -mv.z; vK = aK; vA = exp(-pow(uFog * .8 * z, 2.)) * smoothstep(1.5, 5., z); gl_PointSize = max(1., (aK > .7 ? .09 : .14) * uScale / z); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `varying float vA, vK; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; gl_FragColor = vec4(mix(vec3(.14, .18, .22), vec3(.55, .66, .72), vK) * vA * (1. - 4. * r2) * .5, 1.); }`}));
    m.frustumCulled = false; scene.add(m); RAY = {m, p: new THREE.Vector3(), v: new THREE.Vector3(), u: 30, w: BAND * .5}; }
  // the anglerfish: patrol, two pulses, a turn, a short lunge; a bite tears membrane, never frames
  let ANG = null; if (CREAT.has('angler')) { const body = [], glow = [], pt = (arr, x, y, z, k) => arr.push(x, y, z, k);
    for (let i = 0; i < 2400; i++) { const uu = Math.random(), z = 1.2 - uu * 5.4, prof = uu < .32 ? Math.sqrt(Math.max(0, 1 - ((.32 - uu) / .34) ** 2)) : Math.pow(1 - (uu - .32) / .68, 1.3), r = 1.6 * prof, a = Math.random() * 6.283, x = Math.cos(a) * r, y = Math.sin(a) * r * .85;
      pt(body, x, y, z, 0); if (Math.random() < .2) pt(glow, x * 1.02, y * 1.02, z, 7); else if (Math.random() < .03) pt(glow, x, y, z, 4); }
    for (const [n, lo] of [[17, 0], [13, 1]]) for (let i = 0; i < n; i++) { const t = ((i + .5) / n - .5) * 2.2, lx = Math.sin(t) * (1.22 - lo * .1), lz = .55 + Math.cos(t) * (.78 - lo * .08), len = .18 + .4 * Math.random() * Math.cos(t * .7); for (let k = 0; k < 6; k++) pt(glow, lx * (1 - .12 * k / 5), lo ? -.55 + k / 5 * len : -.05 - k / 5 * len, lz - .02 * k, 2); }
    for (let i = 0; i <= 40; i++) { const t = i / 40; pt(glow, 0, (1 - t) ** 2 * 1.4 + 2 * (1 - t) * t * 2.8 + t * t * 1.7, (1 - t) ** 2 * .3 + 2 * (1 - t) * t * 1.7 + t * t * 3.1, 5); }
    const mk = (arr, add) => { const n = arr.length / 4, P = new Float32Array(n * 3), K = new Float32Array(n); for (let i = 0; i < n; i++) { P.set(arr.slice(i * 4, i * 4 + 3), i * 3); K[i] = arr[i * 4 + 3]; } const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('aK', new THREE.BufferAttribute(K, 1));
      const m = new THREE.Points(g, new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: add ? THREE.AdditiveBlending : THREE.NormalBlending, uniforms: {uScale: {value: 1}, uReveal: {value: 0}, uTime: {value: 0}, uFog: {value: L.fogD}},
        vertexShader: `uniform float uScale, uFog; attribute float aK; varying float vA, vK; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); float z = -mv.z; vK = aK; vA = exp(-pow(uFog * .8 * z, 2.)) * smoothstep(1.5, 5., z); gl_PointSize = clamp((aK > 6.5 ? .12 : aK > 1.5 ? .07 : .16) * uScale / z, 1., 14.); gl_Position = projectionMatrix * mv; }`,
        fragmentShader: `uniform float uReveal, uTime; varying float vA, vK; void main(){ vec2 q = gl_PointCoord - .5; float r2 = dot(q, q); if (r2 > .25) discard; float g = 1. - 4. * r2; vec3 c = vec3(.012, .016, .028); float a = .7 * g;
          if (vK > 1.5 && vK < 3.5) { c = vec3(.75, .72, .62) * .5 * (.3 + .7 * uReveal); a = g; } else if (vK > 3.5 && vK < 4.5) { c = vec3(.15, .4, 1.) * (.3 + .7 * uReveal); a = g; } else if (vK > 4.5 && vK < 5.5) { c = vec3(.5, .35, .2) * .35; a = g; } else if (vK > 6.5) { c = vec3(.05, .1, .13) * (.25 + 3. * uReveal); a = g; }
          gl_FragColor = vec4(c * vA, a * vA); }`})); m.frustumCulled = false; return m; };
    const grp = new THREE.Group(), mb = mk(body, false), mg = mk(glow, true); grp.add(mb, mg); grp.scale.setScalar(1.3); scene.add(grp);
    const lure = mkPts(1, pointsMat('vec3(.7,.95,1.) * (.2 + 1.6 * vK)', '(.25 + .9 * vK)'));
    ANG = {grp, mb, mg, lure, st: 'patrol', t: 0, u: L.floorAngler ? LEN * .45 : LEN * .55, w: -BAND * .55, pos: new THREE.Vector3(), dir: new THREE.Vector3(-1, 0, 0), cool: 0, reveal: 0, pulse: 0, init: false, rise: L.floorAngler ? 0 : 1}; }
  // ------------------------------------------------ chain layout: one film laid out in time as a timeworm of slices
  CHAIN = {film: 0, from: 0, beads: [], next: 0, blocks: []};
  if (L.films.layout === 'chain') { CHAIN.film = (rnd(7, 60) * FILMS.length) | 0; CHAIN.from = (rnd(7, 61) * 30) | 0;
    for (let b = 0; b < NCH / 8; b++) { const k = take(); CHAIN.blocks.push(k); loadClip(k, CHAIN.film, CHAIN.from + b * 8); }
    for (let j = 0; j < NCH; j++) { const u = 22 + j * (LEN - 50) / NCH; CHAIN.beads.push({j, u, w: Math.sin(u * .045) * BAND * .65, taken: false, p: new THREE.Vector3()}); } }
  // ------------------------------------------------ input: gestures only
  const G = {state: 'card', t0: 0, wake: 0, watched: new Map(), watchDone: 0, pairs: new Map(), pairsDone: 0, halo: 0, unearth: 0, orderN: 0, pulses: 0, look: [0, 0], zoom: 1, hold: null, watch: null, lastTap: 0, endT: 0};
  const touches = new Map(); let pinch = null;
  const cv = $('gl');
  const filmAt = (x, y) => { let best = null, bd = 1e9; const test = (p, size, o) => { _a.copy(p).project(camera); if (_a.z > 1) return; const sx = (_a.x * .5 + .5) * innerWidth, sy = (-_a.y * .5 + .5) * innerHeight, dist = camera.position.distanceTo(p), rpx = size * 1.15 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * dist) * innerHeight, d = Math.hypot(sx - x, sy - y); if (d < Math.max(28, rpx) && d < bd) { bd = d; best = o; } };
    for (const s of SP) if (s.slot >= 0 && !s.bad && visible(s)) test(s.pos, s.size, s); for (const b of CHAIN.beads) if (!b.taken && Math.abs(b.u - J.u) < 40) test(b.p, 1, b); return best; };
  cv.addEventListener('contextmenu', e => e.preventDefault());
  cv.addEventListener('pointerdown', e => { touches.set(e.pointerId, {x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, t0: performance.now()}); try { cv.setPointerCapture(e.pointerId); } catch (x) {}
    if (G.state === 'card') { begin(); return; }
    if (G.state === 'end') { G.swipe = {x: e.clientX, y: e.clientY, t: performance.now()}; return; }
    if (touches.size === 2) { const [a, b] = [...touches.values()]; pinch = {d: Math.hypot(a.x - b.x, a.y - b.y), mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, z: G.zoom}; G.hold = null; endWatch(); return; }
    if (e.button === 2) { pinch = {mx: e.clientX, my: e.clientY, z: G.zoom, mouse: true}; return; }
    const f = filmAt(e.clientX, e.clientY); G.hold = {id: e.pointerId, x: e.clientX, y: e.clientY, t0: performance.now(), film: f, moved: 0}; });
  cv.addEventListener('pointermove', e => { const t = touches.get(e.pointerId); if (t) { t.x = e.clientX; t.y = e.clientY; }
    if (pinch && (touches.size >= 2 || pinch.mouse)) { const pts = [...touches.values()], mx = pinch.mouse ? e.clientX : (pts[0].x + pts[1].x) / 2, my = pinch.mouse ? e.clientY : (pts[0].y + pts[1].y) / 2; if (!pinch.mouse) { const d = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y); G.zoom = THREE.MathUtils.clamp(pinch.z * d / Math.max(20, pinch.d), .75, 1.3); }
      G.look = [THREE.MathUtils.clamp(-(mx - pinch.mx) / innerWidth * 14, -6, 6), THREE.MathUtils.clamp((my - pinch.my) / innerHeight * 10, -4, 4)]; return; }
    if (G.hold && G.hold.id === e.pointerId) { G.hold.moved = Math.max(G.hold.moved, Math.hypot(e.clientX - G.hold.x, e.clientY - G.hold.y)); G.hold.cx = e.clientX; G.hold.cy = e.clientY; } });
  const up = e => { const t = touches.get(e.pointerId); touches.delete(e.pointerId);
    if (G.state === 'end' && G.swipe) { const dx = e.clientX - G.swipe.x, dy = e.clientY - G.swipe.y; G.swipe = null; if (Math.abs(dx) > 70 && Math.abs(dx) > Math.abs(dy)) { const i = ALL.indexOf(L); go(dx < 0 ? ALL[(i + 1) % ALL.length].id : null); } else if (Math.hypot(dx, dy) < 20 && performance.now() - G.endT > 1500) go(L.id); return; }
    if (pinch) { if (touches.size < 2) { pinch = null; G.look = [0, 0]; } return; }
    if (t && t.x0 < 24 && e.clientX - t.x0 > 90) { go(null); return; }   // swipe in from the left edge: back to all drifts
    const h = G.hold; if (!h || h.id !== e.pointerId) return; G.hold = null; const dt = performance.now() - h.t0;
    if (G.watch) { endWatch(); return; }
    if (dt < 260 && h.moved < 14) { if (h.film) { J.target = h.film; say(h.film.j !== undefined ? `slice ${h.film.j + 1} of ${FILMS[CHAIN.film].title}` : `${FILMS[h.film.film].title}`); }
      else { const now = performance.now(); if (now - G.lastTap < 320 && Math.hypot(e.clientX - G.lastX, e.clientY - G.lastY) < 40) { pulse(); G.lastTap = 0; } else { G.lastTap = now; G.lastX = e.clientX; G.lastY = e.clientY; } } } };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('dblclick', e => { e.preventDefault(); });
  cv.addEventListener('wheel', e => { e.preventDefault(); G.zoom = THREE.MathUtils.clamp(G.zoom * Math.exp(-e.deltaY * .001), .75, 1.3); }, {passive: false});
  const keys = new Set(); addEventListener('keydown', e => { const k = e.key.toLowerCase(); keys.add(k); if (k === 'escape') go(null); if (G.state === 'card') begin(); if (G.state === 'end') { if (k === 'enter' || k === ' ') go(L.id); if (k === 'n' || k === 'arrowright') go(ALL[(ALL.indexOf(L) + 1) % ALL.length].id); } if (k === ' ' && G.state === 'play') { e.preventDefault(); pulse(); } });
  addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
  const go = id => { const u = new URL(location.href); if (id) u.searchParams.set('v', id); else u.searchParams.delete('v'); location.href = u.toString(); };
  // ------------------------------------------------ sound: water in layers, the song of this video, beats
  const AU = { ac: null, el: null, t: null, lp: null, bed: null, an: null,
    start() { const A = window.AudioContext || window.webkitAudioContext; if (!A || this.ac) return; const ac = this.ac = new A(); const out = ac.createDynamicsCompressor(); out.connect(ac.destination);
      const ir = ac.createBuffer(2, ac.sampleRate * 4, ac.sampleRate); for (let c = 0; c < 2; c++) { const x = ir.getChannelData(c); for (let i = 0; i < x.length; i++) x[i] = (Math.random() * 2 - 1) * (1 - i / x.length) ** 3; } const wet = ac.createConvolver(); wet.buffer = ir; const wg = ac.createGain(); wg.gain.value = .4; wet.connect(wg).connect(out); this.out = out; this.wet = wet;
      const nb = ac.createBuffer(1, ac.sampleRate * 6, ac.sampleRate), x = nb.getChannelData(0); let l = 0; for (let i = 0; i < x.length; i++) { l = (l + .02 * (Math.random() * 2 - 1)) / 1.02; x[i] = l * 3.5; } const ns = ac.createBufferSource(); ns.buffer = nb; ns.loop = true; const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 300; const bg_ = ac.createGain(); bg_.gain.value = .35; ns.connect(lp).connect(bg_).connect(out); bg_.connect(wet); ns.start(); this.bedLP = lp; this.bed = bg_;
      for (const f of [36, 54.5]) { const o = ac.createOscillator(), g = ac.createGain(); o.frequency.value = f; g.gain.value = .035; o.connect(g).connect(out); o.start(); }
      const t = MUSIC && MUSIC.tracks.find(t => t.id === L.song); if (t) { this.t = t; const el = this.el = new Audio(); el.crossOrigin = 'anonymous'; el.loop = true; const a = document.createElement('audio'), p = !a.canPlayType('audio/ogg; codecs="vorbis"') && t.mp3 ? t.mp3 : t.src; el.src = (Q.get('music') || MUSIC.base) + p.split('/').map(encodeURIComponent).join('/');
        const st = L.start ?? S2G?.songs?.[L.song]?.video?.audio_start ?? 0; el.onloadedmetadata = () => { try { el.currentTime = st; } catch (e) {} }; const g = ac.createGain(); g.gain.value = 0; g.gain.linearRampToValueAtTime(.9, ac.currentTime + 4); const lp2 = ac.createBiquadFilter(); lp2.type = 'lowpass'; lp2.frequency.value = 1400; this.lp = lp2;
        try { ac.createMediaElementSource(el).connect(lp2).connect(g).connect(out); g.connect(wet); } catch (e) {} el.play().catch(() => {}); $('song').textContent = `♪ ${t.title} · ${t.album}`; }
      this.an = ac.createAnalyser(); this.an.fftSize = 512; out.connect(this.an); this.buf = new Uint8Array(this.an.frequencyBinCount); },
    phase() { const t = this.t, el = this.el; if (!t || !el || el.paused || !t.an) return (T * .8) % 1; return ((((el.currentTime - t.an.beat0) * t.an.bpm / 60) % 1) + 1) % 1; },
    bpm() { return this.t && this.t.an && this.el && !this.el.paused ? this.t.an.bpm : 0; },
    high() { if (!this.an) return 0; this.an.getByteFrequencyData(this.buf); let h = 0; for (let i = 120; i < 256; i++) h += this.buf[i]; return h / 136 / 120; },
    tone(f, d, g) { if (!this.ac) return; const ac = this.ac, t = ac.currentTime, o = ac.createOscillator(), v = ac.createGain(); o.frequency.value = f; v.gain.setValueAtTime(0, t); v.gain.linearRampToValueAtTime(g, t + .02); v.gain.exponentialRampToValueAtTime(.0001, t + d); o.connect(v).connect(this.out); v.connect(this.wet); o.start(t); o.stop(t + d + .05); },
    focus(k) { if (!this.ac) return; const t = this.ac.currentTime; this.bed.gain.setTargetAtTime(k ? .12 : .35, t, .3); if (this.lp) this.lp.frequency.setTargetAtTime(k ? 8000 : 1400 - Math.min(900, prog() * 900 * (DIR === 'down' ? 1 : 0)), t, .5); },
    speed(v) { if (this.bedLP) this.bedLP.frequency.setTargetAtTime(200 + v * 70, this.ac.currentTime, .4); } };
  const buzz = p => { try { navigator.vibrate && navigator.vibrate(p); } catch (e) {} };
  const say = (t, hold = 0) => { $('say').textContent = t; $('say').style.opacity = 1; G.sayT = RT + hold; };
  function begin() { G.state = 'play'; G.t0 = RT; AU.start(); $('card').style.opacity = 0; setTimeout(() => $('card').style.display = 'none', 700); $('hud').style.opacity = 1; buzz(10);
    $('hint').innerHTML = COARSE ? 'hold the water to swim there · tap a film to take a frame<br>hold on a film to watch it · double-tap to pulse · pinch to pull back' : 'hold the mouse in the water to swim there · click a film to take a frame<br>hold on a film to watch it · double-click or space to pulse · scroll to pull back · Esc for all drifts';
    $('hint').style.opacity = 1; setTimeout(() => $('hint').style.opacity = 0, 11000); }
  // ------------------------------------------------ pulse, watch, capture
  let PULSE = null; const pulseMat = new THREE.ShaderMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {uR: {value: 0}, uA: {value: 0}, uC: {value: new THREE.Vector3()}, uScale: {value: 1}},
    vertexShader: `uniform float uR, uScale; uniform vec3 uC; void main(){ vec4 mv = viewMatrix * vec4(uC + position * uR, 1.); gl_PointSize = max(1., .1 * uScale / -mv.z); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `uniform float uA; void main(){ vec2 q = gl_PointCoord - .5; if (dot(q, q) > .25) discard; gl_FragColor = vec4(vec3(.5, .95, 1.) * uA, 1.); }`});
  { const n = 700, P = new Float32Array(n * 3); for (let i = 0; i < n; i++) { const a = i / n * 6.283 * 3, zz = (Math.random() - .5) * .3; P.set([Math.cos(a), Math.sin(a), zz], i * 3); } const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); const p = new THREE.Points(g, pulseMat); p.frustumCulled = false; scene.add(p); }
  function pulse() { if (G.state !== 'play' || RT - (G.pulseT || -9) < 1.5) return; const ph = AU.phase(), on = ph < .14 || ph > .86; G.pulseT = RT; PULSE = {t0: RT, R: on ? 22 : 13, c: J.p.clone(), on}; G.pulses++;
    for (const s of SP) if (s.pos && s.pos.distanceTo(J.p) < PULSE.R) { s.lit = RT; if (s.buried && !s.up) unearth(s); } if (ANG) ANG.reveal = 1; scareShrimp(J.p); for (const f of FISH) f.v.add(_a.copy(f.p).sub(J.p).setLength(8));
    AU.tone(on ? 660 : 440, 2, .05); buzz(on ? [8, 30, 8] : 10); say(on ? 'on the beat: the pulse reaches far' : 'pulse'); }
  function startWatch(s) { G.watch = {s, t0: RT}; AU.focus(1); say(`${s.j !== undefined ? FILMS[CHAIN.film].title : FILMS[s.film].title} · ${stamp(s.j !== undefined ? CHAIN.film : s.film, (s.j !== undefined ? CHAIN.from + s.j : s.from + (Math.floor(T * fps(FILMS[s.film])) % BLOCK)))}`, 99); buzz(6); }
  function endWatch() { if (!G.watch) return; const s = G.watch.s, d = RT - G.watch.t0; G.watch = null; AU.focus(0); G.sayT = RT - 2; const k = s.i ?? ('c' + s.j), tot = (G.watched.get(k) || 0) + d; G.watched.set(k, tot);
    if (tot >= 4 && !s.watchedDone) { s.watchedDone = true; G.watchDone++; say(`watched · ${G.watchDone}`); AU.tone(880, 1.4, .04); buzz([8, 30, 8]); } }
  const CAST = {t: -9, to: new THREE.Vector3()}, FLK = [{t: -9, from: new THREE.Vector3()}, {t: -9, from: new THREE.Vector3()}];
  function capture(s) { let film, fi, block, slot;
    if (s.j !== undefined) { film = CHAIN.film; fi = CHAIN.from + s.j; block = CHAIN.blocks[s.j >> 3]; slot = s.j % 8; if (s.taken) return; }
    else { if (s.budget <= 0 || s.slot < 0) { say('nothing left to take here'); return; } film = s.film; slot = Math.floor(T * fps(FILMS[film])) % BLOCK; fi = s.from + slot; block = SP_BLOCK.get(s); }
    const r = addFrame(film, fi, s.j !== undefined ? 'slice' : s.pair >= 0 ? 'pair' : 'film'); if (r === 'dup') { say('already in that arm: wait for another moment'); return; } if (r === 'full') { say('your arms are full'); return; }
    CAST.t = RT; CAST.to.copy(s.p || s.pos); const fl = FLK[0].t < FLK[1].t ? FLK[0] : FLK[1]; fl.t = RT; fl.from.copy(s.p || s.pos); fl.block = block; fl.slot = slot;
    J.glow = 1; AU.tone(220 * Math.pow(2, (film % 12) / 12), 2, .05); buzz(r === 'new' ? [8, 24, 8, 24, 14] : [8, 20, 10]);
    if (s.j !== undefined) { s.taken = true; if (s.j === CHAIN.next || CHAIN.next === 0 && G.orderN === 0) { G.orderN++; CHAIN.next = s.j + 1; say(`slice ${s.j + 1} · in order (${G.orderN})`); } else { say(`slice ${s.j + 1} · out of order`); CHAIN.next = s.j + 1; } return; }
    s.budget--; if (s.pair >= 0) { const set = G.pairs.get(s.pair) || new Set(); set.add(s.i); G.pairs.set(s.pair, set); if (set.size === 2 && !set.done) { set.done = true; G.pairsDone++; say(`a pair joins: ${G.pairsDone}`); AU.tone(990, 1.6, .05); } else say(`${FILMS[film].title} · ${stamp(film, fi)} · now its pair`); }
    else if (s.ring !== false) { G.halo++; say(`from the halo · ${G.halo}`); } else if (s.buried) { G.unearth++; say(`unearthed · ${FILMS[film].title} · ${stamp(film, fi)}`); } else say(`${FILMS[film].title} · ${stamp(film, fi)} · ${r === 'new' ? 'a new arm' : 'its arm grows'}`); }
  function unearth(s) { s.up = true; s.lit = RT; AU.tone(330, 1.2, .04); buzz(8); }
  // ------------------------------------------------ the loop
  const SP_BLOCK = new Map(), ROWOF = new Map(); const rowsFree = Array.from({length: NFR}, (_, i) => i);
  const visible = s => !(s.dark && !(s.lit > RT - 6) && s.pos && s.pos.distanceTo(J.p) > lightR()) && !(s.buried && !s.up);
  const lightR = () => L.dark ? THREE.MathUtils.lerp(12, 5, prog()) : 99;
  const prog = () => THREE.MathUtils.clamp(J.u / LEN, 0, 1);
  let T = 0, RT = 0, last = performance.now();
  function frame(now) { requestAnimationFrame(frame); const real = Math.min(.05, (now - last) / 1000); last = now; RT += real; const ws = G.watch ? .12 : 1, dt = real * ws; T += dt;
    const playing = G.state === 'play';
    // swimmer: hold the water and it swims toward your finger; let go and it drifts with the current
    let tu = 0, tw = 0; const h = G.hold; if (playing && h && !h.film && !G.watch && !pinch && performance.now() - h.t0 > 120) { const p = screenToPlane(h.cx ?? h.x, h.cy ?? h.y); if (p) { const [pu, pw] = toUW(p); tu = pu - J.u; tw = pw - J.w; J.target = null; } }
    if (playing && J.target) { const s = J.target, P = s.p || s.pos; if (!P || (s.j === undefined && s.slot < 0)) J.target = null; else { const [pu, pw] = toUW(P); tu = pu - J.u; tw = pw - J.w; if (Math.hypot(tu, tw) < (s.size || 1) * .5 + 2.2) { capture(s); J.target = null; } } }
    const kx = (keys.has('arrowright') || keys.has('d')) - (keys.has('arrowleft') || keys.has('a')), ky = (keys.has('arrowup') || keys.has('w')) - (keys.has('arrowdown') || keys.has('s')); if (kx || ky) { const v = W(kx, ky, 0).sub(W(0, 0, 0)); tu = (DIR === 'right' ? kx : DIR === 'up' ? ky : -ky) * 6; tw = (DIR === 'right' ? ky : kx) * 6; }
    if (G.hold && G.hold.film && !G.watch && performance.now() - G.hold.t0 > 340 && G.hold.moved < 14) startWatch(G.hold.film);
    const m = Math.hypot(tu, tw), sp = Math.min(6, m * 1.4), du = m > .3 ? tu / m * sp : 0, dw = m > .3 ? tw / m * sp : 0, slip = J.slip > 0 ? 4 : 0;
    const ph = J.ph % 1, thrust = ph < .28 ? Math.sin(ph / .28 * Math.PI) * .8 : 0;
    const ending = playing ? 1 : G.state === 'card' ? .12 : 0;
    const wantU = ending * (L.current + slip + du + thrust * (m > .3 ? 1 : .4)), wantW = ending * dw + .2 * Math.sin(T * .5);
    J.vu += (wantU - J.vu) * Math.min(1, dt * 2.4); J.vw += (wantW - J.vw) * Math.min(1, dt * 2.4); if (J.stun > 0) { J.vu *= .9; J.vw *= .9; }
    J.u += J.vu * dt; J.w += J.vw * dt; const tongue = caveTongue(J.u);
    if (Math.abs(J.w) > BAND) { J.w = Math.sign(J.w) * BAND; J.vw = 0; } if (tongue && Math.abs(J.w) < tongue + .6) { J.w = (J.w < 0 ? -1 : 1) * (tongue + .6); J.vw *= -.2; }
    if (J.u < 2) J.u = 2;
    const bpm = AU.bpm(), rate = bpm ? bpm / 60 / (bpm > 100 ? 2 : 1) : .8; J.ph += dt * rate; if (bpm) { const want = AU.phase() / (bpm > 100 ? 2 : 1); J.ph += (((want - J.ph % 1) % 1 + 1.5) % 1 - .5) * dt * 2; }   // the bell strokes on the beat
    J.slip = Math.max(0, J.slip - dt); J.stun = Math.max(0, J.stun - dt); J.hurt = Math.max(0, J.hurt - dt); J.glow = Math.max(0, J.glow - dt * 1.4);
    const prev = J.p.clone(); W(J.u, J.w, 0, J.p); J.pv.copy(J.p).sub(prev).divideScalar(Math.max(dt, 1e-4)); jelly.position.copy(J.p);
    const head = _a.copy(J.pv).setLength(1); if (J.pv.lengthSq() > .01) { const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), head.lerp(new THREE.Vector3(0, 1, 0), .35).normalize()); jelly.quaternion.slerp(q, 1 - Math.pow(.05, dt)); }
    stepArms(Math.max(dt, 1e-4));
    // camera: trailing from the side, small jelly, look-ahead with the current; two fingers look around
    const vis = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * Math.min(1, camera.aspect), d = THREE.MathUtils.clamp(2 * .92 * CS / (.12 * G.zoom * vis), 7, 26) * (G.state === 'end' ? 1.25 : 1);
    const look = W(J.u + 3.5 + G.look[0], J.w * .75 + G.look[1], 0), camT = look.clone().add(new THREE.Vector3(0, DIR === 'right' ? 1.2 : 0, d)); camera.position.lerp(camT, 1 - Math.pow(.02, real)); camera.lookAt(look.x, look.y, 0); camera.updateMatrixWorld();
    uR.value.setFromMatrixColumn(camera.matrixWorld, 0); uU.value.setFromMatrixColumn(camera.matrixWorld, 1); uF.value.setFromMatrixColumn(camera.matrixWorld, 2);
    // water colour toward the surface or the void
    const k = L.surface ? sm(.55, 1, prog()) : 0; scene.fog.color.copy(FOG).lerp(TOP, k); { const hx = scene.fog.color.getHexString(); if (hx !== bgLast) { bgLast = hx; paintBG(scene.fog.color); } } scene.fog.density = L.fogD * (1 - .35 * k) * (L.dark ? 1 + 1.2 * prog() : 1);
    if (L.dark) { const sp2 = J.p.clone().project(camera); $('dark').style.opacity = .35 + .6 * prog(); $('dark').style.setProperty('--x', `${(sp2.x * .5 + .5) * 100}%`); $('dark').style.setProperty('--y', `${(-sp2.y * .5 + .5) * 100}%`); $('dark').style.setProperty('--r', `${Math.max(9, 34 - 24 * prog()) * (PULSE ? 1.8 : 1)}vmin`); }
    // films: activate near the swimmer, release behind it
    for (const s of SP) { const near = s.u > J.u - 22 && s.u < J.u + 70; if (near && s.slot < 0 && rowsFree.length) { const b = s.bad ? -1 : take(); if (s.bad || b >= 0) { s.slot = rowsFree.shift(); s.born = T; s.pos = s.pos || new THREE.Vector3(); if (b >= 0) { SP_BLOCK.set(s, b); loadClip(b, s.film, s.from); } } }
      else if (!near && s.slot >= 0) { hide(FROW + s.slot); rowsFree.push(s.slot); s.slot = -1; give(SP_BLOCK.get(s)); SP_BLOCK.delete(s); } }
    for (const s of SP) { if (s.slot < 0) continue; const r = FROW + s.slot; let u = s.u, w = s.w;
      if (s.ring !== false) { const a = s.ring / 8 * 6.283 + T * .35; u += Math.sin(a) * 4; w += Math.cos(a) * 6.5; }
      if (s.buried && s.up) w += Math.min(1.6, (RT - s.lit) * 1.2);
      W(u + Math.sin(T * .3 + s.i) * .2, w + Math.cos(T * .25 + s.i) * .2, s.z, s.pos);
      const dist = Math.hypot(u - J.u, w - J.w), res = THREE.MathUtils.clamp(1 - (dist - 3) / 14, 0, 1), watching = G.watch && G.watch.s === s ? 1 : 0;
      if (s.sleep && !s.awake && dist < 4.2 && Math.abs(s.z) < 9) { s.awake = true; G.wake++; AU.tone(520 + G.wake * 20, 1, .03); buzz(6); }
      const shown = visible(s) ? 1 : (s.buried ? .35 + .15 * Math.sin(T * 2 + s.i) : s.dark ? .06 : 0), sleepy = s.sleep && !s.awake ? .35 : 1, fade = Math.min(1, (T - s.born) / 1.5);
      if (s.bad && playing && dist < s.size * .6 + .6 && Math.abs(s.z) < 1) { J.mem = Math.max(0, J.mem - 10); J.hurt = 1; flash(); say('red interference: your membrane tears; nothing is lost'); buzz([20, 20, 40]); G.burst = RT; s.bad = false; s.budget = 0; s.gone = true; }
      if (s.gone) { hide(r); continue; }
      row(r, 0, s.pos.x, s.pos.y, s.pos.z, s.size * (1 + .08 * res)); row(r, 1, s.bad ? -1 : SP_BLOCK.get(s), 1.35, s.sleep && !s.awake ? 0 : T * fps(FILMS[s.film]), (s.bad ? .9 : 1.15) * shown * sleepy * fade * (s.giant ? 1.2 : 1));
      row(r, 2, 0, s.bad ? .6 : .7, s.bad ? 1 : 0, 0); row(r, 3, 0, 0, 0, s.awake ? .4 : 0); row(r, 4, s.bad ? 0 : .7 + .6 * res + (s.giant ? .5 : 0), 1.8, 0, s.bad ? 0 : (1 - res) * .9); }
    // the chain: one film laid out as slices in time
    for (const b of CHAIN.beads) { const r = CHROW + b.j; if (b.taken || Math.abs(b.u - J.u) > 45) { hide(r); continue; } W(b.u, b.w + Math.sin(T * .8 + b.j * .4) * .25, 0, b.p); const nxt = b.j === CHAIN.next;
      row(r, 0, b.p.x, b.p.y, b.p.z, .95); row(r, 1, CHAIN.blocks[b.j >> 3], 1.35, b.j % 8, nxt ? 1.5 : .9); row(r, 2, 0, .4, 0, 0); row(r, 3, 0, 0, 0, nxt ? .5 : 0); row(r, 4, .6, 1.6, 0, .1); }
    // watching: hold on a film and it blooms, large and clear, while the water nearly stops
    if (G.watch) { const s = G.watch.s, F = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 2).negate(), p = camera.position.clone().addScaledVector(F, 5), u = Math.min(1, (RT - G.watch.t0) / .5), src = s.p || s.pos, at = src.clone().lerp(p, u * u * (3 - 2 * u));
      const blk = s.j !== undefined ? CHAIN.blocks[s.j >> 3] : SP_BLOCK.get(s), fr = s.j !== undefined ? s.j % 8 : (RT - G.watch.t0) * fps(FILMS[s.film]) % BLOCK;
      row(VROW, 0, at.x, at.y, at.z, (s.size * .4) + 2.1 * u); row(VROW, 1, blk, 1.4, fr, 1.75 * u + .3); row(VROW, 2, 0, .45, 0, 0); row(VROW, 3, 0, 0, 0, .25); row(VROW, 4, 1.6, 1.1, 0, 0); }
    else if (G.state !== 'end') hide(VROW);
    // casting, flecks travelling into the bell, the interference burst
    { const ct = RT - CAST.t, kk = ct < .25 ? ct / .25 : ct < .45 ? 1 : Math.max(0, 1 - (ct - .45) / .3); for (let j = 0; j < NCAST; j++) { const r = CROW + j; if (kk <= 0) { hide(r); continue; } _a.copy(J.p).lerp(CAST.to, (j + 1) / NCAST * kk); row(r, 0, _a.x, _a.y, _a.z, .12); row(r, 1, -1, 1, 0, .9); row(r, 4, 0, 0, 0, 0); } }
    FLK.forEach((f, j) => { const r = FLROW + j, u = (RT - f.t) / .6; if (u < 0 || u > 1) { hide(r); return; } _a.copy(f.from).lerp(J.p, u * u * (3 - 2 * u)); row(r, 0, _a.x, _a.y, _a.z, .8 - .5 * u); row(r, 1, f.block, 1.3, f.slot, 1.2); row(r, 3, 0, 0, 0, .6); row(r, 4, .3, 1.5, 0, .3); });
    { const u = (RT - (G.burst ?? -9)) / 1; if (u >= 0 && u < 1) { row(XROW, 0, J.p.x, J.p.y, J.p.z, 2.2 * (.5 + u)); row(XROW, 1, -1, 1, 0, (1 - u) * 1.3); row(XROW, 2, 0, .5, 1, 0); row(XROW, 4, 0, 0, 0, 1); } else hide(XROW); }
    // arms and the film that lights the bell
    for (let kA = 0; kA < NAR; kA++) for (let j = 0; j < AN; j++) { const r = AROW + kA * AN + j, A = ARMS[kA]; if (!A || j >= Math.round(A.n)) { hide(r); continue; } const i = (kA * AN + j) * 3, f = j / Math.max(1, A.n - 1), nf = Math.min(BLOCK, A.frames.length);
      row(r, 0, AX[i], AX[i + 1], AX[i + 2], (.22 - .08 * f) * CS); row(r, 1, A.block, 1.1, Math.max(0, Math.min(nf - 1, Math.floor(f * nf))), .85); row(r, 2, 0, .3, 0, 0); row(r, 3, 0, 0, 0, .55); row(r, 4, .25, 0, 0, 0); }
    const lastA = ARMS.length ? ARMS.find(a => a.film === CUT[CUT.length - 1].film) : null; if (lastA) { row(COREROW, 0, J.p.x, J.p.y + .1, J.p.z, .3 * CS); row(COREROW, 1, lastA.block, 1.2, Math.floor(T * 3) % Math.min(BLOCK, lastA.frames.length), .8); row(COREROW, 3, 0, 0, 0, .7); row(COREROW, 4, .5, 1.4, 0, 0); } else hide(COREROW);
    // creatures
    if (fishPts) { school.u += dt * (L.current * 1.1); if (school.u < J.u - 20 || school.u > J.u + 90) { school.u = J.u + 40; FISH.forEach(f => f.init = false); } school.w = Math.sin(T * .2) * BAND * .5; const c0 = W(school.u, school.w, -2);
      const a = fishPts.geometry.attributes.position.array, kk = fishPts.geometry.attributes.aK.array; FISH.forEach((f, i) => { const tgt = c0.clone().add(new THREE.Vector3(Math.cos(f.o[0] + T * .5) * 2.5, Math.sin(f.o[1] + T * .4) * 1.6, Math.sin(f.o[0] * 2) * 2)); if (!f.init) { f.p.copy(tgt); f.init = true; }
        f.v.addScaledVector(tgt.sub(f.p), dt * 1.8); const dd = f.p.distanceTo(J.p); if (dd < 4) f.v.addScaledVector(_a.copy(f.p).sub(J.p).normalize(), dt * 30 * (1 - dd / 4)); f.v.multiplyScalar(Math.pow(.3, dt)); f.p.addScaledVector(f.v, dt); _b.copy(f.v).normalize();
        for (let q = 0; q < 3; q++) { a.set([f.p.x - _b.x * q * .16, f.p.y - _b.y * q * .16, f.p.z - _b.z * q * .16], (i * 3 + q) * 3); kk[i * 3 + q] = q; } }); fishPts.geometry.attributes.position.needsUpdate = true; fishPts.geometry.attributes.aK.needsUpdate = true; }
    if (combPts) { const a = combPts.geometry.attributes.position.array; COMB.forEach((c, ci) => { c.t += dt; c.u += dt * L.current * .85; if (c.u < J.u - 25) c.u += 110; W(c.u + Math.sin(c.t * .3) * 1.5, c.w + Math.sin(c.t * .21) * 1, c.z, c.p); combLocal.forEach((l, i) => a.set([c.p.x + l[0], c.p.y + l[1], c.p.z + l[2]], (ci * 200 + i) * 3));
        if (playing && c.p.distanceTo(J.p) < 1.6 && !c.used) { c.used = true; J.glow = 1; say('a comb jelly: your reach grows'); AU.tone(2400, 1, .03); } }); combPts.geometry.attributes.position.needsUpdate = true; }
    if (shrPts) { const a = shrPts.geometry.attributes.position.array; SHR.forEach((s, i) => { const home = W(s.home + Math.sin(s.o[0] + T * .2) * 3, -BAND + 1.2 + Math.sin(s.o[1] + T * .3) * 1, -1); if (!s.init) { s.p.copy(home); s.init = true; }
        if (s.p.distanceTo(J.p) < 4.5 && s.scare <= 0) { scareShrimp(J.p); } s.scare = Math.max(0, s.scare - dt); s.v.addScaledVector(home.sub(s.p), dt * (s.scare > 0 ? .2 : 1.4)); s.v.multiplyScalar(Math.pow(.15, dt)); s.p.addScaledVector(s.v, dt); if (s.scare > .8) PUSH.push({p: s.p.clone(), r: 2, k: 5});
        _b.copy(s.v).normalize(); for (let q = 0; q < 2; q++) a.set([s.p.x - _b.x * q * .09, s.p.y - _b.y * q * .09, s.p.z], (i * 2 + q) * 3); if (s.home < J.u - 30) s.home += LEN * .4; }); shrPts.geometry.attributes.position.needsUpdate = true; }
    if (RAY) { RAY.u += dt * (L.current * 1.25); if (RAY.u < J.u - 25 || RAY.u > J.u + 60) RAY.u = J.u + 45; RAY.w = BAND * .45 + Math.sin(T * .17) * BAND * .3; const prevR = RAY.p.clone(); W(RAY.u, RAY.w, -.5, RAY.p); RAY.v.copy(RAY.p).sub(prevR).divideScalar(Math.max(dt, 1e-4));
      RAY.m.position.copy(RAY.p); RAY.m.lookAt(_a.copy(RAY.p).add(RAY.v)); RAY.m.rotateZ(Math.PI / 2 * 0); RAY.m.material.uniforms.uTime.value = T; PUSH.push({p: RAY.p.clone(), r: 5, k: 3, vx: RAY.v.x * .5, vy: RAY.v.y * .5});
      if (playing && RAY.p.distanceTo(J.p) < 6 && J.u < RAY.u) { if (J.slip <= 0) { say('slipstream: the ray carries you'); buzz(10); } J.slip = 1.2; } }
    if (ANG) stepAngler(dt);
    // snow
    { const cx = camera.position.x, cy = camera.position.y, cur = W(L.current, 0, 0).sub(W(0, 0, 0)).multiplyScalar(.6);
      for (let i = 0; i < NSN; i++) { const p = sn[i]; for (const u of PUSH) { const dx = cx + p.x - u.p.x, dy = cy + p.y - u.p.y, dz = p.z - u.p.z, d2 = dx * dx + dy * dy + dz * dz; if (d2 < u.r * u.r) { const dd = Math.sqrt(d2) + .01, kk = (1 - dd / u.r) * u.k * dt; p.vx += (dx / dd + (u.vx || 0)) * kk; p.vy += (dy / dd + (u.vy || 0)) * kk; } }
        p.x += (cur.x + p.vx) * dt - (camera.position.x - (G.lcx ?? camera.position.x)); p.y += (cur.y + p.vy - .05) * dt - (camera.position.y - (G.lcy ?? camera.position.y)); p.vx *= Math.pow(.3, dt); p.vy *= Math.pow(.3, dt);
        if (p.x > 22) p.x -= 44; if (p.x < -22) p.x += 44; if (p.y > 15) p.y -= 30; if (p.y < -15) p.y += 30; snP[i * 3] = cx + p.x; snP[i * 3 + 1] = cy + p.y; snP[i * 3 + 2] = p.z; snA[i] = Math.min(1, p.s + Math.hypot(p.vx, p.vy) * .3); }
      G.lcx = camera.position.x; G.lcy = camera.position.y; snG.attributes.position.needsUpdate = true; snG.attributes.aS.needsUpdate = true; PUSH.length = 0; }
    // buried films come up when you swim low and fast over them
    if (L.films.layout === 'buried' && playing) { const fast = Math.hypot(J.vu, J.vw) > 2.4, low = J.w < -BAND + 3; if (low) PUSH.push({p: J.p.clone().add(new THREE.Vector3(0, -1, 0)), r: 3, k: fast ? 6 : 2});
      for (const s of SP) if (s.buried && !s.up && s.pos && s.pos.distanceTo(J.p) < 3.6 && fast && low) unearth(s); }
    // pulse ring
    if (PULSE) { const u = (RT - PULSE.t0) / 1.2; if (u > 1) { PULSE = null; pulseMat.uniforms.uA.value = 0; } else { pulseMat.uniforms.uR.value = PULSE.R * u; pulseMat.uniforms.uA.value = (1 - u) * (PULSE.on ? .9 : .5); pulseMat.uniforms.uC.value.copy(PULSE.c); } }
    // goal, end
    if (playing) { $('goal').textContent = `${L.goal.label} · ${goalN()} / ${L.goal.n}${J.mem < 100 ? ` · membrane ${Math.round(J.mem)}%` : ''}`; if (J.u >= LEN || J.mem <= 0) arrive(); }
    if (G.state === 'end') reelStep();
    // uniforms
    const ps = innerHeight * renderer.getPixelRatio(), us = ps * .5 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    splat.uniforms.uTime.value = T; splat.uniforms.uScale.value = us; splat.uniforms.uJ.value.copy(J.p); splat.uniforms.uJv.value.copy(J.pv).multiplyScalar(.15); splat.uniforms.uBeat.value = 1 - AU.phase();
    snM.uniforms.uScale.value = us; snM.uniforms.uHigh.value = AU.high(); pulseMat.uniforms.uScale.value = us; if (surfMat) { surfMat.uniforms.uScale.value = us; surfMat.uniforms.uTime.value = T; }
    for (const m of [fishPts, combPts, shrPts, RAY && RAY.m, ANG && ANG.mb, ANG && ANG.mg, ANG && ANG.lure]) if (m) { m.material.uniforms.uScale.value = us; if (m.material.uniforms.uTime) m.material.uniforms.uTime.value = T; }
    const bu = bellM.uniforms; bu.uPulse.value = J.ph; bu.uTime.value = T; bu.uGlow.value = J.glow + (1 - AU.phase()) * .15; bu.uHurt.value = J.hurt; bu.uFray.value = 1 - J.mem / 100; bu.uScale.value = ps * .0095;
    AU.speed(Math.hypot(J.vu, J.vw)); params.needsUpdate = true;
    if (RT - (G.sayT ?? -9) > 3.2) $('say').style.opacity = 0;
    composer.render();
    if (DEBUG) { $('dbg').style.display = 'block'; $('dbg').textContent = `u ${J.u.toFixed(1)} / ${LEN} w ${J.w.toFixed(1)} · goal ${goalN()}/${L.goal.n} · cut ${CUT.length} · free ${free.length}${ANG ? ' · angler ' + ANG.st : ''}`; } }
  function screenToPlane(x, y) { const nd = new THREE.Vector3((x / innerWidth) * 2 - 1, -(y / innerHeight) * 2 + 1, .5).unproject(camera).sub(camera.position).normalize(); if (Math.abs(nd.z) < 1e-4) return null; const t = -camera.position.z / nd.z; return t > 0 ? camera.position.clone().addScaledVector(nd, t) : null; }
  function scareShrimp(from) { for (const s of SHR) if (s.scare <= 0 && s.p.distanceTo(from) < 9) { s.scare = 1.2; s.v.add(_b.copy(s.p).sub(from).setLength(9 + Math.random() * 5)); } }
  function flash() { $('flash').style.opacity = 1; setTimeout(() => $('flash').style.opacity = 0, 200); }
  function stepAngler(dt) { const A = ANG; A.t += dt; A.cool = Math.max(0, A.cool - dt); const homeU = A.u + Math.sin(T * .1) * 10, home = W(homeU, A.w + Math.sin(T * .2) * 1 - (1 - A.rise) * 5, -1); if (!A.init) { A.pos.copy(home); A.init = true; }
    const toJ = _a.copy(J.p).sub(A.pos), dist = toJ.length(), k = A.t % 2.4; A.pulse = (k < .12 || (k > .3 && k < .42)) ? 1 : A.pulse * Math.pow(.001, dt);
    if (A.st === 'patrol') { A.pos.lerp(home, 1 - Math.pow(.4, dt)); A.reveal += (.05 - A.reveal) * dt; A.rise += ((L.floorAngler ? 0 : 1) - A.rise) * dt; if (G.state === 'play' && !A.cool && dist < 15) { A.st = 'warn'; A.t = 0; say('the lure pulses twice: swim away'); scareShrimp(A.pos); } }
    else if (A.st === 'warn') { A.reveal += (1 - A.reveal) * dt; A.rise += (1 - A.rise) * dt * 1.5; A.pos.lerp(home, 1 - Math.pow(.5, dt)); if (A.pulse > .99 && !A.pinged) { A.pinged = true; AU.tone(1250, .25, .07); buzz(16); } if (A.pulse < .5) A.pinged = false; if (A.t > 4.6) { A.st = dist < 13 ? 'lunge' : 'patrol'; A.t = 0; if (A.st === 'patrol') A.cool = 5; } }
    else if (A.st === 'lunge') { A.pos.addScaledVector(toJ.clone().normalize(), dt * 7.5); A.dir.lerp(toJ.clone().normalize(), dt * 6).normalize(); if (dist < 1.8) { A.st = 'patrol'; A.cool = 8; J.mem = Math.max(0, J.mem - 30); J.hurt = 1; J.stun = 1; flash(); say('the angler bit: your frames are safe, your membrane is torn'); buzz([60, 40, 120]); AU.tone(48, 1.2, .25); } else if (A.t > 2.4) { A.st = 'patrol'; A.cool = 6; } }
    if (A.st !== 'lunge') A.dir.lerp(toJ.clone().normalize(), dt * .8).normalize();
    PUSH.push({p: A.pos.clone(), r: 4.5, k: 4}); A.grp.position.copy(A.pos); A.grp.lookAt(_b.copy(A.pos).add(A.dir)); A.grp.updateMatrixWorld(); A.mb.material.uniforms.uReveal.value = A.mg.material.uniforms.uReveal.value = A.reveal;
    const lp = A.grp.localToWorld(new THREE.Vector3(0, 1.7, 3.1)); A.lure.geometry.attributes.position.array.set([lp.x, lp.y, lp.z]); A.lure.geometry.attributes.aK.array[0] = A.pulse * (A.st === 'patrol' ? .35 : 1); A.lure.geometry.attributes.position.needsUpdate = true; A.lure.geometry.attributes.aK.needsUpdate = true;
    if (A.u < J.u - 40) A.u += LEN * .35; }
  function goalN() { const g = L.goal.type; return g === 'wake' ? G.wake : g === 'pairs' ? G.pairsDone : g === 'watch' ? G.watchDone : g === 'halo' ? G.halo : g === 'order' ? G.orderN : g === 'unearth' ? G.unearth : CUT.length; }
  // ------------------------------------------------ the end: the reel plays behind the account; tap to swim again, swipe for the next drift
  const REEL = {i: 0, t0: 0, b: 0};
  function arrive() { G.state = 'end'; G.endT = performance.now(); endWatch(); AU.focus(1); buzz([30, 60, 30]); const met = goalN() >= L.goal.n, secs = Math.round(RT - G.t0);
    $('card').style.display = 'flex'; $('card').style.opacity = 1; $('hud').style.opacity = 0;
    $('card').innerHTML = `<div class="k">${J.mem <= 0 ? 'CARRIED UP' : DIR === 'up' ? 'THE SURFACE' : DIR === 'down' ? 'THE FLOOR OF THE DARK' : 'THE END OF THE DRIFT'}</div><h1>${L.title}</h1>
      <p style="font-style:normal">${met ? '★ ' : ''}${L.goal.label}: ${goalN()} / ${L.goal.n}. ${CUT.length} frame${CUT.length === 1 ? '' : 's'} from ${ARMS.length} film${ARMS.length === 1 ? '' : 's'} in ${Math.floor(secs / 60)} min ${secs % 60} s${G.pulses ? ` · ${G.pulses} pulses` : ''}.</p>
      <ol>${CUT.slice(0, 12).map(c => `<li>${FILMS[c.film].title} · ${stamp(c.film, c.fi)}</li>`).join('')}</ol>
      <div class="go">TAP TO SWIM AGAIN · SWIPE ← FOR THE NEXT DRIFT · SWIPE → FOR ALL DRIFTS</div>`;
    REEL.i = 0; REEL.t0 = RT; if (CUT.length) loadClip(VB(0), CUT[0].film, CUT[0].fi); }
  const VB = i => i % 2;   // blocks 0 and 1 are the reel's double buffer
  function reelStep() { if (!CUT.length) { hide(VROW); return; } const len = AU.bpm() ? Math.max(1.2, 2 * 60 / AU.bpm()) : 1.6, it = CUT[REEL.i % CUT.length], t = RT - REEL.t0;
    if (t > len) { REEL.i++; REEL.t0 = RT; const nx = CUT[REEL.i % CUT.length]; loadClip(VB(REEL.i), nx.film, nx.fi); }
    const F = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 2).negate(), R = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0), p = camera.position.clone().addScaledVector(F, 6).addScaledVector(R, innerWidth > innerHeight ? 2.2 : 0);
    row(VROW, 0, p.x, p.y, p.z, 2.1); row(VROW, 1, VB(REEL.i), 1.4, (RT - REEL.t0) * fps(FILMS[it.film]) % BLOCK, 1.5); row(VROW, 2, 0, .45, 0, 0); row(VROW, 3, 0, 0, 0, .25); row(VROW, 4, 1.6, 1.1, 0, 0); }
  window.__drift = () => ({state: G.state, u: J.u, w: J.w, len: LEN, goal: goalN(), n: L.goal.n, cut: CUT.length, films: ARMS.length, mem: J.mem, watch: !!G.watch, angler: ANG && ANG.st, spots: SP.length, active: SP.filter(s => s.slot >= 0).length});
  if (DEBUG) window.__dd = {J, G, SP, CHAIN, ARMS, CUT, camera, filmAt, capture, startWatch, endWatch, pulse, THREE, visible};
  requestAnimationFrame(frame);
}
