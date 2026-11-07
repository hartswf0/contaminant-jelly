// Screens: a jelly-film that comes clear shows its real footage, projected into the water the way the design videos show film:
// one continuous picture, an oval edge that dissolves into the haze, darks gone transparent, tinted toward the water.
// Shared by the drifts and by v4, v5 and v6. A backdrop layer plays one film full and faint in the farthest dark water.
//
//   const SCN = makeScreens(THREE, scene, camera, {n: 3});
//   each frame: SCN.update(items, real, RT, scene.fog.color, scene.fog.density);  SCN.backdrop(src, alpha, RT);
//   item: {key, pos: Vector3, size, clear 0..1, hold 0..1, src, clock}
//   src:  {frames: i => url, n, fps, from} | {strip: url} | {thumb: url} | {video: url} | {el: HTMLVideoElement}, plus bw
export function makeScreens(THREE, scene, camera, opt = {}) {
  const N = opt.n || 3, geo = new THREE.PlaneGeometry(1, 1), IMG = new Map(), WHITE = new THREE.Color(1, 1, 1), _v = new THREE.Vector3(), _w = new THREE.Vector3();
  const img = url => { let e = IMG.get(url); if (!e) { const im = new Image(); im.crossOrigin = 'anonymous'; e = {im, ok: false}; im.onload = () => { e.ok = true; }; im.onerror = () => { e.bad = true; }; im.src = url; IMG.set(url, e); } return e; };
  const FS = `uniform sampler2D map; uniform float uA, uT, uSat, uAsp, uFar; uniform vec3 uWater; varying vec2 vU;
    float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f); return mix(mix(h(i), h(i + vec2(1., 0.)), f.x), mix(h(i + vec2(0., 1.)), h(i + vec2(1., 1.)), f.x), f.y); }
    void main(){ vec2 q = (vU - .5) * 2.; float r = length(q * mix(vec2(1.), vec2(.82, 1.), uFar)); float nn = n(vU * vec2(uAsp, 1.) * 4. + uT * .12) * .6 + n(vU * 21. - uT * .25) * .4;
      float lo = mix(.2 + .58 * uA, .15, uFar);
      float edge = (1. - smoothstep(lo, .99, r + (nn - .5) * .5 * (1.2 - uA * (1. - uFar)))) * (1. - smoothstep(.8, .99, abs(q.x))) * (1. - smoothstep(.8, .99, abs(q.y)));
      vec3 c = texture2D(map, vU).rgb; float l = dot(c, vec3(.299, .587, .114));
      vec3 proj = mix(uWater * .4, mix(uWater, vec3(1.), .5 - .12 * uFar), pow(smoothstep(.03, 1., l), 1.25)); vec3 col = mix(proj, c * .8, uSat) * .86 + (h(vU * 517. + fract(uT)) - .5) * .05;
      gl_FragColor = vec4(col, edge * uA * (.5 + .5 * smoothstep(.0, .55, l)) * mix(1., .25 + .75 * smoothstep(.08, .6, l), uFar)); }`;
  const mk = (order, far) => { const cv = document.createElement('canvas'); cv.width = 384; cv.height = 288; const tex = new THREE.CanvasTexture(cv); tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    const mat = new THREE.ShaderMaterial({transparent: true, depthWrite: false, depthTest: !far, fog: false, uniforms: {map: {value: tex}, uA: {value: 0}, uT: {value: 0}, uSat: {value: .5}, uAsp: {value: 1.33}, uFar: {value: far ? 1 : 0}, uWater: {value: new THREE.Color()}},
      vertexShader: `varying vec2 vU; void main(){ vU = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`, fragmentShader: FS});
    const m = new THREE.Mesh(geo, mat); m.visible = false; m.frustumCulled = false; m.renderOrder = order; scene.add(m); return {m, mat, cv, g: cv.getContext('2d'), tex, it: null, a: 0, want: 0, vid: null, vsrc: null, lastE: null}; };
  const pool = Array.from({length: N}, () => mk(5, false)), back = [mk(-20, true), mk(-20, true)];
  const video = url => { const v = document.createElement('video'); v.crossOrigin = 'anonymous'; v.muted = true; v.loop = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.preload = 'auto'; v.src = url; v.play().catch(() => {}); return v; };
  const drop = S => { if (S.vid) { S.vid.pause(); S.vid.removeAttribute('src'); S.vid.load(); S.vid = null; S.vsrc = null; } };
  function source(S, src, clock) {   // -> [image, sx, sy, sw, sh, crossfade-to or null, mix]
    if (src.el && src.el.readyState >= 2 && src.el.videoWidth) return [src.el, 0, 0, src.el.videoWidth, src.el.videoHeight, null, 0];
    if (src.video) { if (S.vsrc !== src.video) { drop(S); S.vid = video(src.video); S.vsrc = src.video; } else if (S.vid.paused) S.vid.play().catch(() => {});
      if (S.vid.readyState >= 2 && S.vid.videoWidth) return [S.vid, 0, 0, S.vid.videoWidth, S.vid.videoHeight, null, 0]; if (!src.frames && !src.strip && !src.thumb) return null; }
    if (src.frames) { const i = (src.from || 0) + Math.floor(clock * (src.fps || 8)) % (src.loop || src.n || 8); for (let k = 0; k < 3; k++) img(src.frames(i + k)); let e = img(src.frames(i));
      if (!e.ok) e = S.lastE; if (!(e && e.ok)) return null; S.lastE = e; return [e.im, 0, 0, e.im.width, e.im.height, null, 0]; }
    const e = img(src.strip || src.thumb); if (!e.ok) return null; const im = e.im;
    if (src.strip) { const ph = clock * 1.6, k = Math.floor(ph) % 8, w = im.width / 8, x = ph % 1; return [im, k * w, 0, w, im.height, [((k + 1) % 8) * w, 0], Math.max(0, (x - .55) / .45)]; }   // eight frames crossfaded: a slow living photograph
    const z = 1 - .05 * (.5 + .5 * Math.sin(clock * .2)); return [im, im.width * (1 - z) / 2, im.height * (1 - z) / 2, im.width * z, im.height * z, null, 0]; }
  function paint(S, src, clock, maxW) { const r = source(S, src, clock); if (!r) return 0; const [im, sx, sy, sw, sh, nx, mx] = r, asp = sw / sh, cw = Math.min(maxW, Math.round(sw)), ch = Math.max(2, Math.round(cw / asp));
    if (S.cv.width !== cw || S.cv.height !== ch) { S.cv.width = cw; S.cv.height = ch; } S.g.globalAlpha = 1; S.g.drawImage(im, sx, sy, sw, sh, 0, 0, cw, ch); if (nx && mx > 0) { S.g.globalAlpha = mx; S.g.drawImage(im, nx[0], nx[1], sw, sh, 0, 0, cw, ch); } S.tex.needsUpdate = true; return asp; }
  const viewW = dist => 2 * Math.tan(camera.fov * Math.PI / 360) * Math.max(.5, dist) * camera.aspect;
  const api = {
    alpha(key) { const S = pool.find(S => S.it && S.it.key === key); return S ? S.a : 0; },
    update(items, real, t, water, fogD) {
      const top = items.filter(x => x && x.pos && (x.clear || 0) > .18).sort((a, b) => (b.hold || 0) - (a.hold || 0) || b.clear - a.clear).slice(0, N);
      for (const S of pool) { const c = S.it && top.find(x => x.key === S.it.key); if (c) S.it = c; S.want = c ? Math.min(1, Math.max(c.hold || 0, c.clear * 1.15)) : 0; }
      for (const it of top) if (!pool.some(S => S.it && S.it.key === it.key)) { const S = pool.filter(S => !S.it || S.a < .03).sort((a, b) => a.a - b.a)[0]; if (S) { drop(S); S.it = it; S.a = 0; S.lastE = null; S.want = Math.min(1, it.clear * 1.15); } }
      camera.getWorldDirection(_v);
      for (const S of pool) { S.a += (S.want - S.a) * Math.min(1, real * (S.want > S.a ? 1.8 : 2.6));
        if (!S.it || S.a < .01) { S.m.visible = false; if (S.it && S.want === 0) { S.it = null; drop(S); } continue; }
        const it = S.it, asp = paint(S, it.src, it.clock ?? t, 480); if (!asp) { S.m.visible = false; continue; }
        const hu = Math.min(1, it.hold || 0), hk = hu * hu * (3 - 2 * hu), base = it.size * (1.05 + .25 * S.a), vw = viewW(_v.dot(_w.copy(it.pos).sub(camera.position)));
        const wd = hk > 0 ? THREE.MathUtils.lerp(base, Math.max(base * 1.6, Math.min(vw * .62, vw * .62 / camera.aspect * asp * .9)), hk) : base;   // held: it opens to most of the view, where it is
        S.m.position.copy(it.pos).addScaledVector(_v, .15); S.m.quaternion.copy(camera.quaternion); S.m.scale.set(wd, wd / asp, 1);
        const d = S.m.position.distanceTo(camera.position), fogK = Math.exp(-Math.pow((fogD || 0) * d, 2)), U = S.mat.uniforms;
        U.uA.value = Math.min(1, S.a) * (.35 + .65 * fogK) * (hk > .5 ? 1 : .9); U.uT.value = t; U.uAsp.value = asp; U.uSat.value = it.src.bw ? .08 : .5; U.uWater.value.copy(water).lerp(WHITE, .12); S.m.visible = true; } },
    // the farthest layer: one film plays full and faint in the dark water behind everything; a new film crossfades in
    backdrop(src, alpha, t, water, real = .016, depth = 60) {
      const B = back, cur = B[0]; if (src && (!cur.it || cur.it.key !== (src.video || src.strip || src.thumb || src.key))) { if (cur.it) { B.reverse(); } const S = B[0]; drop(S); S.it = {key: src.video || src.strip || src.thumb || src.key, src}; S.lastE = null; S.a = 0; }
      if (!src && B[0].it) B.reverse();
      camera.getWorldDirection(_v);
      B.forEach((S, i) => { const want = i === 0 && src ? alpha : 0; S.a += (want - S.a) * Math.min(1, real * (want > S.a ? .5 : .9)); if (!S.it || S.a < .004) { S.m.visible = false; if (S.it && want === 0 && S.a < .004) { S.it = null; drop(S); } return; }
        const asp = paint(S, S.it.src, t, 320); if (!asp) { S.m.visible = false; return; } const vw = viewW(depth) * 1.25, vh = vw / camera.aspect, w = Math.max(vw, vh * asp), h = w / asp;
        S.m.position.copy(camera.position).addScaledVector(_v, depth); S.m.quaternion.copy(camera.quaternion); S.m.scale.set(w, h, 1);
        const U = S.mat.uniforms; U.uA.value = S.a; U.uT.value = t; U.uAsp.value = asp; U.uSat.value = S.it.src.bw ? 0 : .3; U.uWater.value.copy(water); S.m.visible = true; }); },
    get pool() { return pool; }, get back() { return back; } };
  return api;
}

// cinema: the mode for trailers and for watching. No words on the screen, only the water, the films and the jelly; a slight vignette and grain.
// H toggles it, or a three-finger tap; ?cinema starts in it. Pass the ids of the elements to hide.
export function cinema(ids, opt = {}) {
  const Q = new URLSearchParams(location.search); let on = Q.has('cinema') || Q.has('trailer');
  const st = document.createElement('style'); st.textContent = `body.cinema ${ids.map(i => '#' + i).join(',body.cinema ')}{opacity:0!important;visibility:hidden!important}
    .cine-v{position:fixed;inset:0;pointer-events:none;z-index:50;background:radial-gradient(ellipse 75% 70% at 50% 48%,transparent 55%,rgba(0,0,0,.55) 100%);opacity:.6;transition:opacity 1s}body.cinema .cine-v{opacity:1}
    .cine-g{position:fixed;inset:-50%;pointer-events:none;z-index:51;opacity:.05;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E");animation:cineg 1.2s steps(6) infinite}
    body.cinema .cine-g{opacity:.08}@keyframes cineg{0%{transform:translate(0,0)}20%{transform:translate(-4%,3%)}40%{transform:translate(3%,-5%)}60%{transform:translate(-6%,-2%)}80%{transform:translate(5%,4%)}100%{transform:translate(0,0)}}`;
  document.head.appendChild(st); const v = document.createElement('div'); v.className = 'cine-v'; const g = document.createElement('div'); g.className = 'cine-g'; document.body.append(v, g);
  const set = x => { on = x; document.body.classList.toggle('cinema', on); opt.onChange && opt.onChange(on); }; set(on);
  addEventListener('keydown', e => { if (e.key && e.key.toLowerCase() === (opt.key || 'h') && !e.metaKey && !e.ctrlKey && !(e.target && /input|textarea/i.test(e.target.tagName))) set(!on); });
  addEventListener('touchstart', e => { if (e.touches.length === 3) set(!on); }, {passive: true});
  return {get on() { return on; }, set};
}
