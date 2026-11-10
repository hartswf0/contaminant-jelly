// MEMORY: film memories as first-class score operations (PEO verbs memory · condense · bloom · keep · release/stream).
// A memory is a clip (an mp4 and a start time, or a still) held by a cast jelly. Its life is a pure function of the score clock,
// so scrubbing, playback and frame-by-frame recording all agree:
//   held      a small picture hanging under its holder's bell
//   condense  flecks of the picture travel in from elsewhere and gather under the bell (in transit only)
//   bloom     the full-resolution picture, sized as a fraction of frame height, placed above the caption band
//             arrives as one of five stagings: pull-in · catch · surface · swallow · hand-off
//   keep      a small picture beside another jelly or memory, in the water
//   release   the picture breaks into flecks that stream along an arc into a target (a jelly, a memory, or x,y,z)
// After SCION jelly cuts r4b (moto/scion/jelly-cuts/corrugated-sky/METHOD.md): flecks in transit only, the picture whole at its bloom.

const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v)), ease = u => u * u * (3 - 2 * u), easeOut = u => 1 - Math.pow(1 - u, 3);
export const STAGES = ['pull-in', 'catch', 'surface', 'swallow', 'hand-off'];
export const CAPTION_BAND = 0.2;   // the lower 20% of the frame is the caption band; blooms sit above it

export function makeMemories(THREE, o) {
  const {scene, cam, low, byName, posOf, abs} = o, V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
  const MEM = new Map(), NF = low ? 700 : 1400, D = 2.2;
  let plan = [], silver = new Map();
  function texFor(m) {
    if (m.still) { const tex = new THREE.Texture(); tex.colorSpace = THREE.SRGBColorSpace; const im = new Image(); im.crossOrigin = 'anonymous';
      m.ready = new Promise(res => { im.onload = () => { tex.image = im; tex.needsUpdate = true; m.aspect = im.width / im.height; m.img = im; res(); }; im.onerror = () => res(); }); im.src = abs(m.still); return tex; }
    const v = document.createElement('video'); v.muted = true; v.defaultMuted = true; v.playsInline = true; v.setAttribute('playsinline', ''); v.crossOrigin = 'anonymous'; v.preload = 'auto'; v.loop = false; v.src = abs(m.src);
    const tex = new THREE.Texture(v); tex.colorSpace = THREE.SRGBColorSpace; tex.minFilter = tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    m.ready = new Promise(res => { v.addEventListener('loadeddata', () => { m.aspect = v.videoWidth / v.videoHeight; v.width = v.videoWidth; v.height = v.videoHeight; res(); }, {once: true}); v.addEventListener('error', () => res(), {once: true}); });
    m.video = v; m.img = v; return tex; }
  function define(op) {
    const id = op.args[0]; if (MEM.has(id)) return MEM.get(id);
    const m = {id, holder: op.holder, src: op.src, still: op.still, from: +op.from || 0, t0: op._at, gain: +op.gain || 1, aspect: 16 / 9, source: op.source, label: op.label || ''};
    m.tex = texFor(m);
    m.mat = new THREE.MeshBasicMaterial({map: m.tex, transparent: true, opacity: 0, toneMapped: false, fog: false, depthTest: false, depthWrite: false, side: THREE.DoubleSide});
    m.mat.color.setScalar(m.gain); m.panel = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), m.mat); m.panel.renderOrder = 20; m.panel.frustumCulled = false; m.panel.visible = false; scene.add(m.panel);
    // the flecks: one per cell of a grid in the picture's shape, coloured from the picture when a transit begins
    const g = new THREE.BufferGeometry(), P = new Float32Array(NF * 3), C = new Float32Array(NF * 3); g.setAttribute('position', new THREE.BufferAttribute(P, 3)); g.setAttribute('color', new THREE.BufferAttribute(C, 3));
    m.fl = new THREE.Points(g, new THREE.PointsMaterial({size: Math.max(2, 3.4 * innerHeight / 720), vertexColors: true, transparent: true, opacity: .95, depthWrite: false, toneMapped: false, fog: false, sizeAttenuation: false}));
    m.fl.frustumCulled = false; m.fl.visible = false; m.fl.renderOrder = 21; scene.add(m.fl);
    m.rnd = Array.from({length: NF}, (_, i) => { const s = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return [s - Math.floor(s), Math.abs(Math.sin(i * 3.7)), Math.abs(Math.cos(i * 1.3))]; });
    m.sampledAt = -1; MEM.set(id, m); return m; }
  // the score's memory operations, as time windows
  function load(ops, ts) { clear(); plan = []; silver = new Map();
    for (const op of ops) { if (op.verb === 'memory') define({...op, _at: ts(op.t)}); }
    for (const op of ops) if (['condense', 'bloom', 'keep', 'release', 'stream'].includes(op.verb)) { const a = ts(op.t), b = op.until ? ts(op.until) : a + (op.verb === 'bloom' ? 4 : 2); plan.push({...op, verb: op.verb === 'stream' ? 'release' : op.verb, id: op.args[0], a, b}); }
    plan.sort((x, y) => x.a - y.a); }
  function clear() { for (const m of MEM.values()) { scene.remove(m.panel); scene.remove(m.fl); m.panel.geometry.dispose(); m.mat.dispose(); m.tex.dispose(); m.fl.geometry.dispose(); m.fl.material.dispose(); if (m.video) { m.video.pause(); m.video.removeAttribute('src'); m.video.load(); } } MEM.clear(); }
  // where things are
  const camAxes = () => { const r = V3().setFromMatrixColumn(cam.matrixWorld, 0), u = V3().setFromMatrixColumn(cam.matrixWorld, 1), f = cam.getWorldDirection(V3()); return {r, u, f}; };
  const frameH = () => 2 * D * Math.tan(cam.fov * Math.PI / 360);
  function screenPlace(cx, cy, h, aspect) { const {r, u, f} = camAxes(), H = frameH(), Wf = H * cam.aspect; let ph = h * H, pw = ph * aspect; if (pw > Wf * .94) { pw = Wf * .94; ph = pw / aspect; }
    const p = cam.position.clone().addScaledVector(f, D).addScaledVector(r, cx * Wf / 2).addScaledVector(u, cy * H / 2); return {p, w: pw, h: ph, q: cam.quaternion.clone()}; }
  const ndcOf = p => { const q = p.clone().project(cam); return [clamp(q.x, -1.3, 1.3), clamp(q.y, -1.3, 1.3)]; };
  function targetPoint(spec, rel) { if (spec == null) return null; if (Array.isArray(spec)) return V3(...spec.map(Number)); if (typeof spec === 'string' && spec.includes(',')) return V3(...spec.split(',').map(Number));
    const E = byName(spec); if (E) return posOf(E).add(V3(0, -.4, 0));
    const M2 = MEM.get(spec); if (M2 && M2.panel.visible && M2.place) { const uv = rel || [.5, .5], {r, u} = camAxes(); return M2.place.p.clone().addScaledVector(r, (uv[0] - .5) * M2.place.w).addScaledVector(u, (.5 - uv[1]) * M2.place.h); }
    return null; }
  const hangUnder = (m, size = .9) => { const E = byName(m.holderNow || m.holder); if (!E) return null; const p = posOf(E).add(V3(0, -1.25, 0)); return {p, w: size * Math.min(1.6, m.aspect), h: size * Math.min(1.6, m.aspect) / m.aspect, q: cam.quaternion.clone()}; };
  function sample(m) { const gw = Math.round(Math.sqrt(NF * m.aspect)), gh = Math.ceil(NF / gw), c = document.createElement('canvas'); c.width = gw; c.height = gh; const g = c.getContext('2d', {willReadFrequently: true});
    let px = null; try { g.drawImage(m.img, 0, 0, gw, gh); px = g.getImageData(0, 0, gw, gh).data; } catch (e) {}
    const C = m.fl.geometry.attributes.color.array; m.grid = [gw, gh];
    for (let i = 0; i < NF; i++) { const x = i % gw, y = Math.floor(i / gw), k = (Math.min(gh - 1, y) * gw + x) * 4; const v = px ? [px[k] / 255, px[k + 1] / 255, px[k + 2] / 255] : [.8, .75, .65];
      const lv = Math.round((v[0] * .3 + v[1] * .59 + v[2] * .11) * 7) / 7, s = .55; for (let c2 = 0; c2 < 3; c2++) C[i * 3 + c2] = Math.min(1, (v[c2] * s + lv * (1 - s)) * m.gain * 1.15); }   // eight ink levels, after WYGWYL's dot law
    m.fl.geometry.attributes.color.needsUpdate = true; }
  const gridPoint = (m, i, pl) => { const [gw, gh] = m.grid || [40, 20], x = (i % gw + .5) / gw - .5, y = .5 - (Math.floor(i / gw) + .5) / gh, {r, u} = camAxes(); return pl.p.clone().addScaledVector(r, x * pl.w).addScaledVector(u, y * pl.h); };
  const pulseOnce = (key, E, k = 1) => { if (!E || silver.has(key)) return; silver.set(key, 1); try { E.J.pulse(k); } catch (_) {} };
  // the frame: every memory's state at clock t
  function update(t, video) {
    for (const m of MEM.values()) { m.panel.visible = false; m.fl.visible = false; m.state = 'none'; m.holderNow = m.holder; }
    // a memory that is kept beside, or released into, another memory's picture is placed after it, this frame
    const leans = m => plan.some(p => p.id === m.id && t >= p.a && t < p.b && ((p.verb === 'release' && MEM.has(p.to)) || (p.verb === 'keep' && MEM.has(p.beside)))) ? 2 : plan.some(p => p.id === m.id && p.verb === 'release' && t >= p.a && t < p.b) ? 1 : 0;
    for (const m of [...MEM.values()].sort((a, b) => leans(a) - leans(b))) {
      if (t < m.t0) continue;
      const mine = plan.filter(p => p.id === m.id), handed = mine.find(p => p.verb === 'bloom' && p.stage === 'hand-off' && t >= p.b); if (handed && handed.to) m.holderNow = handed.to;
      const released = mine.find(p => p.verb === 'release' && t >= p.b); if (released) { m.state = 'gone'; continue; }
      const act = ['release', 'bloom', 'keep', 'condense'].map(v => mine.find(p => p.verb === v && t >= p.a && t < p.b)).find(Boolean);
      const ct = m.from + (t - m.t0); if (m.video) { m.clip = ct; video(m, ct); m.tex.needsUpdate = m.video.readyState >= 2; }
      if (!act) { const pl = hangUnder(m, .8); if (pl) show(m, pl, .85, 'held'); continue; }
      const u = clamp((t - act.a) / Math.max(.001, act.b - act.a)), dur = act.b - act.a, inU = clamp((t - act.a) / Math.min(.9, dur * .25)), outU = clamp((act.b - t) / Math.min(.45, dur * .15));
      if (act.verb === 'condense') { if (m.sampledAt !== act.a) { sample(m); m.sampledAt = act.a; }
        const end = hangUnder(m, .8), src = targetPoint(act.from) || (end ? end.p.clone().add(V3(-6, 3.5, -3)) : V3()); if (!end) continue;
        const P = m.fl.geometry.attributes.position.array; for (let i = 0; i < NF; i++) { const R = m.rnd[i], ui = ease(clamp((u - R[0] * .45) / .55)), a = src.clone().add(V3((R[1] - .5) * 4, (R[2] - .5) * 3, (R[0] - .5) * 4)), b = gridPoint(m, i, end);
          const sw = Math.sin(ui * Math.PI) * 1.2; const p = a.lerp(b, ui).add(V3(Math.sin(i + t * 2) * sw * .4, sw * .5, Math.cos(i * .7 + t * 2) * sw * .4)); P[i * 3] = p.x; P[i * 3 + 1] = p.y; P[i * 3 + 2] = p.z; }
        m.fl.geometry.attributes.position.needsUpdate = true; m.fl.visible = true; m.state = 'condense'; if (u > .7) show(m, end, (u - .7) / .3 * .85, 'condense'); continue; }
      if (act.verb === 'keep') { const E = targetPoint(act.beside) || (hangUnder(m) || {}).p; if (!E) continue; const size = +act.size || .22, H = frameH(), [nx, ny] = ndcOf(E); const dx = act.dx != null ? +act.dx : .32, dy = act.dy != null ? +act.dy : .1;
        const pl = screenPlace(clamp(nx + dx, -.85, .85), clamp(ny + dy, -.55 + size, .9 - size / 2), size, m.aspect); show(m, pl, Math.min(inU, outU < 1 && !mine.some(p => p.verb === 'release' && Math.abs(p.a - act.b) < .2) ? outU : 1), 'keep'); continue; }
      if (act.verb === 'bloom') { const h = clamp(+act.size || .5, .1, .78), at = act.at || 'center', cx = at === 'left' ? -.42 : at === 'right' ? .42 : 0, cy = (CAPTION_BAND + .015 + h / 2) * 2 - 1 + (+act.lift || 0);
        const home = screenPlace(cx, cy, h, m.aspect), hp = ndcOf((hangUnder(m) || {p: cam.position.clone().addScaledVector(cam.getWorldDirection(V3()), 5)}).p);
        let x = cx, y = cy, k = 1, op = 1; const st = act.stage || 'pull-in';
        if (st === 'pull-in') { const e = easeOut(inU); x = hp[0] + (cx - hp[0]) * e; y = hp[1] + (cy - hp[1]) * e; k = .12 + .88 * e; op = clamp(inU * 2.5); }
        else if (st === 'catch') { const e = easeOut(inU), ov = Math.sin(clamp(inU) * Math.PI) * .06; x = (act.side === 'left' ? -1.9 : 1.9) * (1 - e) + cx - ov; if (inU >= 1) pulseOnce(m.id + 'catch' + act.a, byName(m.holder), 1); }
        else if (st === 'surface') { const e = ease(inU); y = -1.9 + (cy + 1.9) * e; op = clamp(inU * 1.6); }
        else if (st === 'swallow') { const s0 = .72; op = clamp(inU * 2); if (u > s0) { const e = ease((u - s0) / (1 - s0)); x = cx + (hp[0] - cx) * e; y = cy + (hp[1] - cy) * e; k = 1 - .94 * e; } if (u > .97) pulseOnce(m.id + 'sw' + act.a, byName(m.holder), 1.2); }
        else if (st === 'hand-off') { const e = easeOut(inU); x = hp[0] + (cx - hp[0]) * e; y = hp[1] + (cy - hp[1]) * e; k = .12 + .88 * e; const T2 = byName(act.to); if (T2 && u > .7) { const tp = ndcOf(posOf(T2)), f = ease((u - .7) / .3); x = cx + (tp[0] - cx) * f; y = cy + (tp[1] - cy) * f; k = 1 - .9 * f; if (u > .97) pulseOnce(m.id + 'ho' + act.a, T2, 1.2); } }
        const keeps = mine.some(p => (p.verb === 'keep' || p.verb === 'release') && Math.abs(p.a - act.b) < .35);
        if (st !== 'swallow' && st !== 'hand-off' && !keeps) op *= outU;
        const pl = screenPlace(x, y, h * k, m.aspect); show(m, pl, op, 'bloom'); continue; }
      if (act.verb === 'release') { if (m.sampledAt !== act.a) { sample(m); m.sampledAt = act.a; m.relFrom = m.place ? {...m.place, p: m.place.p.clone(), q: m.place.q.clone()} : hangUnder(m); pulseOnce(m.id + 'rel' + act.a, byName(m.holder), 1); }
        const from = m.relFrom; if (!from) continue; const tgt = targetPoint(act.to, act.uv ? String(act.uv).split(',').map(Number) : null) || from.p.clone().add(V3(0, 4, 0)), fade = clamp(1 - u / .3);
        if (fade > 0) show(m, from, fade, 'release');
        const P = m.fl.geometry.attributes.position.array, lift = +act.arc || 1.4;
        for (let i = 0; i < NF; i++) { const R = m.rnd[i], ui = easeOut(clamp((u - R[0] * .35) / .62)), a = gridPoint(m, i, from), b = tgt.clone().add(V3((R[1] - .5) * .35, (R[2] - .5) * .35, (R[0] - .5) * .2)), p = a.lerp(b, ui); p.y += Math.sin(ui * Math.PI) * lift * (.6 + R[2] * .6);
          P[i * 3] = p.x; P[i * 3 + 1] = p.y; P[i * 3 + 2] = p.z; }
        m.fl.geometry.attributes.position.needsUpdate = true; m.fl.visible = u < .995; m.state = 'release'; if (u > .96) pulseOnce(m.id + 'arr' + act.a, byName(act.to), 1); continue; }
    } }
  function show(m, pl, op, state) { m.panel.position.copy(pl.p); m.panel.quaternion.copy(pl.q); m.panel.scale.set(pl.w, pl.h, 1); m.mat.opacity = clamp(op); m.panel.visible = op > .003; m.place = pl; m.state = state;
    m.panel.renderOrder = state === 'held' || state === 'condense' ? 5 : 20; m.mat.depthTest = state === 'held' || state === 'condense'; }
  // seek every memory video to its clip time; resolves when the frames are there (the recorder waits on it)
  function sync() { const ps = []; for (const m of MEM.values()) { const v = m.video; if (!v || m.clip == null || !m.panel.visible && !m.fl.visible) continue; const want = clamp(m.clip, 0, (v.duration || 1e9) - .04);
      if (Math.abs(v.currentTime - want) > .02 || v.readyState < 2) ps.push(new Promise(res => { const done = () => { m.tex.needsUpdate = true; res(); }; const to = setTimeout(done, 1500); v.addEventListener('seeked', () => { clearTimeout(to); done(); }, {once: true}); try { v.currentTime = want; } catch (_) { clearTimeout(to); done(); } })); }
    return Promise.all(ps); }
  return {MEM, load, update, sync, clear, plan: () => plan, STAGES};
}
