// FILM IN THE BELL: video that reads inside a jelly.
// filmTexture(THREE, src, o) makes a texture from a video:
//   · sRGB colour space, linear filters, no mipmaps (a video frame changes every frame; mips would blur and cost)
//   · frame-accurate upload: requestVideoFrameCallback where the browser has it (the texture is marked dirty only when a new frame lands)
//   · graceful fallback: muted + playsinline for autoplay; if play() is refused or the file fails, a still (o.poster, or the first frame
//     it managed to decode) is shown instead, and f.still is true.
// fitFilm(target, f, o) aims a jelly's bell at that texture, without touching rigs.js: it patches each film-carrying material once so the
//   picture is aspect-correct in its window (contain or cover, never squashed), and gets gain and contrast that survive fresnel, bloom and
//   fog (o.gain, o.contrast). target is a rig, a species jelly or anything with .group and .setFilm.
const WINDOW = {glass: 1, filmbell: 1, veil: 4 / 3, doodle: 4 / 3, mantle: 1, golden: 1, celluloid: 4 / 3, reel: 4 / 3, sentinel: 1, medusa: 1};
const GLSL = `uniform vec4 uFit; uniform vec2 uGC;
vec4 filmTex(sampler2D s, vec2 uv){ vec2 q = (uv - .5) * uFit.xy + .5; float inside = step(0., q.x) * step(q.x, 1.) * step(0., q.y) * step(q.y, 1.); vec4 c = texture2D(s, clamp(q, 0., 1.)); c.rgb = clamp((c.rgb - .5) * uGC.y + .5, 0., 1.) * uGC.x * inside; return c; }
`;
export function filmTexture(THREE, src, o = {}) {
  const v = document.createElement('video'); v.muted = true; v.defaultMuted = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.loop = o.loop ?? true; v.crossOrigin = 'anonymous'; v.preload = 'auto'; v.src = src;
  const rvfc = 'requestVideoFrameCallback' in HTMLVideoElement.prototype, tex = rvfc ? new THREE.Texture(v) : new THREE.VideoTexture(v);
  tex.colorSpace = THREE.SRGBColorSpace; tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false; tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
  const F = {tex, video: v, aspect: o.aspect || 4 / 3, still: false, frames: 0, ready: null, dispose() { v.pause(); v.removeAttribute('src'); v.load(); tex.dispose(); }};
  const toStill = img => { if (F.still) return; F.still = true; const c = document.createElement('canvas'); c.width = 320; c.height = Math.round(320 / F.aspect); const g = c.getContext('2d'); g.fillStyle = '#111'; g.fillRect(0, 0, c.width, c.height); try { if (img) g.drawImage(img, 0, 0, c.width, c.height); } catch (e) {} F.tex.image = c; F.tex.needsUpdate = true; };
  F.ready = new Promise(res => {
    v.addEventListener('loadedmetadata', () => { if (v.videoWidth) { F.aspect = v.videoWidth / v.videoHeight; v.width = v.videoWidth; v.height = v.videoHeight; tex.needsUpdate = true; } res(F); }, {once: true});   // three sizes the GPU texture from width/height: a bare <video> reports 0 until told
    v.addEventListener('error', () => { if (o.poster) { const im = new Image(); im.onload = () => { F.aspect = im.width / im.height; toStill(im); res(F); }; im.src = o.poster; } else { toStill(null); res(F); } }, {once: true}); });
  if (rvfc) { const tick = () => { if (!v.width && v.videoWidth) { v.width = v.videoWidth; v.height = v.videoHeight; } if (!v.width) { v.requestVideoFrameCallback(tick); return; } tex.needsUpdate = true; F.frames++; v.requestVideoFrameCallback(tick); }; v.requestVideoFrameCallback(tick); }
  const go = v.play(); if (go && go.catch) go.catch(() => { v.addEventListener('loadeddata', () => toStill(v), {once: true}); if (v.readyState >= 2) toStill(v); });
  return F;
}
export function fitFilm(target, f, o = {}) {
  const rigId = target.id || o.id, winA = o.window || WINDOW[rigId] || 1, fit = o.fit || 'contain', gain = o.gain ?? 1.35, contrast = o.contrast ?? 1.25;
  const s = (va => { const r = va / winA; if (fit === 'contain') return r > 1 ? [1, r] : [1 / r, 1]; return r > 1 ? [1 / r, 1] : [1, r]; })(f ? f.aspect : 1);
  const U = {uFit: {value: {x: s[0], y: s[1], z: 0, w: 0}}, uGC: {value: {x: gain, y: contrast}}};
  target.group.traverse(obj => { const ms = obj.material ? (Array.isArray(obj.material) ? obj.material : [obj.material]) : []; for (const m of ms) {
    if (m.isShaderMaterial && /texture2D\((uImg|map),/.test(m.fragmentShader) && !m.userData.filmFit) { m.fragmentShader = GLSL + m.fragmentShader.replace(/texture2D\((uImg|map),/g, 'filmTex($1,'); m.uniforms.uFit = U.uFit; m.uniforms.uGC = U.uGC; m.userData.filmFit = U; m.needsUpdate = true; }
    else if (m.isShaderMaterial && m.userData.filmFit) { m.userData.filmFit.uFit.value = U.uFit.value; m.userData.filmFit.uGC.value = U.uGC.value; }
    else if (m.map !== undefined && !m.isShaderMaterial && !m.userData.filmFit && (m.blending === 2 || m.opacity === 0 || o.basic)) { m.userData.filmFit = U; m.onBeforeCompile = sh => { sh.uniforms.uFit = U.uFit; sh.uniforms.uGC = U.uGC; sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + GLSL).replace('#include <map_fragment>', '#ifdef USE_MAP\n vec4 sampledDiffuseColor = filmTex(map, vMapUv);\n diffuseColor *= sampledDiffuseColor;\n#endif'); }; m.needsUpdate = true; } } });
  if (f) target.setFilm(f.tex);
  return {set(o2) { if (o2.gain != null) U.uGC.value.x = o2.gain; if (o2.contrast != null) U.uGC.value.y = o2.contrast; }, scale: s};
}

// A WINDOW IN THE BELL: every bell gets a readable film window: a camera-facing panel inside the bell, aspect-correct (its height is its
// width over the film's aspect), on a dark backing so the picture keeps its contrast against the glowing bell, the bloom and the fog
// (fog off, tone mapping off, soft-edged so it sits inside the bell rather than on it). It squeezes with the bell's contraction.
export function bellWindow(THREE, rig, o = {}) {
  const box = new THREE.Box3().setFromObject(rig.group), size = box.getSize(new THREE.Vector3()), R = Math.max(.2, Math.min(size.x, size.z) * .5), w = R * (o.scale ?? 1.15);
  const u = {map: {value: null}, uAspect: {value: 4 / 3}, uGain: {value: o.gain ?? 1.15}, uCon: {value: o.contrast ?? 1.15}, uOp: {value: 0}};
  const mat = new THREE.ShaderMaterial({transparent: true, depthWrite: false, fog: false, toneMapped: false, side: THREE.DoubleSide, uniforms: u,
    vertexShader: 'varying vec2 v; void main(){ v = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: `uniform sampler2D map; uniform float uGain, uCon, uOp; varying vec2 v;
      void main(){ vec2 q = v - .5; float edge = smoothstep(.5, .42, abs(q.x)) * smoothstep(.5, .4, abs(q.y)); vec3 c = texture2D(map, v).rgb; c = clamp((c - .5) * uCon + .5, 0., 1.) * uGain;
        gl_FragColor = vec4(c, uOp * edge); }`});
  const back = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({color: 0x000000, transparent: true, opacity: 0, depthWrite: false, fog: false})), pic = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
  const win = new THREE.Group(); back.scale.setScalar(1.06); win.add(back, pic); win.position.set((box.min.x + box.max.x) / 2, box.max.y - R * .62, (box.min.z + box.max.z) / 2); win.visible = false; win.renderOrder = 10; pic.renderOrder = 11; rig.group.add(win);
  return {win, set(tex, aspect = 4 / 3) { u.map.value = tex; u.uAspect.value = aspect; win.visible = !!tex; u.uOp.value = tex ? .96 : 0; back.material.opacity = tex ? .55 : 0; win.scale.set(w, w / aspect, 1); },
    update(cam, squeeze = 0) { if (!win.visible || !cam) return; win.quaternion.copy(rig.group.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(cam.quaternion)); const k = 1 - .22 * squeeze; win.scale.x = w * k; }, gain(g, c) { u.uGain.value = g; if (c != null) u.uCon.value = c; }};
}
