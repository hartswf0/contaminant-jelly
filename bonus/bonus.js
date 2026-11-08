// Bonus pieces: real footage, a song and sound for the four sketches.
// Each sketch exposes window.__bonus = {scene, camera, renderer, THREE, ...}; this script then
//  - gives every film in it real footage, projected with the shared screens (../current/screens.js):
//    the 109 secondhand titles play their own frames; anything else plays a cineosis clip the drifts have not used (footage.json);
//  - plays one VOLHOLLA song (data-song), faded in on the first touch, ducked while a film is clear;
//  - adds sound: a glass ping and a bubble rush when a film comes clear, a soft reel whir while it is held clear, a low swell on the beat;
//  - H hides the sketch's own text (cinema), like every other piece.
(() => {
  const me = document.currentScript, SONG = me.dataset.song, MODE = me.dataset.mode || 'entities', Q = new URLSearchParams(location.search);
  const SM = Q.get('sm') || 'https://hartswf0.github.io/secondhand-motion/', CINEO = Q.get('cineo');
  const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const wait = (f, cb) => { const t = setInterval(() => { let v = null; try { v = f(); } catch (e) {} if (v) { clearInterval(t); cb(v); } }, 150); };
  Promise.all([fetch('../current/films109.json').then(r => r.json()), fetch('footage.json').then(r => r.json()), fetch('../current/music.json').then(r => r.json()).catch(() => null), import('../current/screens.js'), import('../current/flycam.js')])
    .then(([F, FT, MU, mod, fly]) => wait(() => window.__bonus, B => { start(B, F, FT, MU, mod); fly.attachFlycam(B.THREE, B.renderer, B.scene, B.camera, {back: +(me.dataset.back || 1.7), reach: +(me.dataset.reach || 5), max: 5, fast: 10}); })).catch(e => console.warn('[realfilm]', e));

  function start(B, F0, FT, MU, mod) { let F = F0;
    const {THREE, scene, camera, renderer} = B, SCN = mod.makeScreens(THREE, scene, camera, {n: 3}); mod.cinema(B.hide || []); SCN.pool.forEach(S => { S.mat.depthTest = false; S.m.renderOrder = 999; });   // over the sketch's own placeholders
    const NEAR = (me.dataset.near || '.07,.24').split(',').map(Number), GROW = +(me.dataset.grow || 1);
    if (Q.get('films')) { const keep = Q.get('films').split(','); F = F.filter(f => keep.includes(f.slug)); }   // testing with a few local films: every title maps onto them
    const byTitle = {}; F.forEach(f => { byTitle[norm(f.title)] = f; byTitle[norm(f.slug)] = f; byTitle[norm(f.slug.replace(/-gwp$/, ''))] = f; });
    const base = CINEO || FT.base, clips = FT.clips;
    const smSrc = f => ({frames: i => `${SM}${f.dir}/f${String(((i % f.n) + f.n) % f.n).padStart(3, '0')}.jpg`, n: f.n, fps: Math.min(10, f.fps || 8), loop: f.n});
    const clipSrc = c => ({video: base + c.clip, thumb: c.thumb ? base + c.thumb : undefined, strip: c.strip ? base + c.strip : undefined, bw: c.bw});
    const SRC = new Map();   // one source per film id, fixed for the piece
    const srcFor = (key, title, k) => { if (SRC.has(key)) return SRC.get(key); const f = byTitle[norm(title)] || (Q.get('films') && F.length ? F[k % F.length] : null); const s = f ? smSrc(f) : clipSrc(clips[k % clips.length]); SRC.set(key, s); return s; };
    // sound
    let ac = null, out, music = null, mg, duck = 1, lastClear = new Map();
    const startAudio = () => { if (ac) return; ac = new (window.AudioContext || window.webkitAudioContext)(); out = ac.createGain(); out.gain.value = .9; out.connect(ac.destination);
      const t = MU && MU.tracks.find(t => t.id === SONG); if (t) { const el = new Audio(); el.crossOrigin = 'anonymous'; el.loop = true; const ogg = el.canPlayType('audio/ogg; codecs="vorbis"');
        el.src = (Q.get('music') || MU.base) + (ogg || !t.mp3 ? t.src : t.mp3).split('/').map(encodeURIComponent).join('/'); mg = ac.createGain(); mg.gain.value = 0; mg.gain.linearRampToValueAtTime(.7, ac.currentTime + 4);
        try { ac.createMediaElementSource(el).connect(mg).connect(out); } catch (e) {} el.play().catch(() => {}); music = {el, t}; } };
    ['pointerdown', 'keydown', 'touchstart'].forEach(ev => addEventListener(ev, startAudio, {once: true, passive: true}));
    const ping = (f, g, d = 1.2) => { if (!ac) return; const o = ac.createOscillator(), v = ac.createGain(), t = ac.currentTime; o.type = 'sine'; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * .985, t + d); v.gain.setValueAtTime(0, t); v.gain.linearRampToValueAtTime(g, t + .01); v.gain.exponentialRampToValueAtTime(.0001, t + d); o.connect(v).connect(out); o.start(t); o.stop(t + d); };
    const bubbles = n => { if (!ac) return; for (let i = 0; i < n; i++) setTimeout(() => ping(500 + Math.random() * 900, .015, .12), Math.random() * 380); };
    const whir = (() => { let w = null; return on => { if (!ac) return; if (!w) { const len = ac.sampleRate, b = ac.createBuffer(1, len, ac.sampleRate), d = b.getChannelData(0); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (.5 + .5 * Math.sin(i / len * Math.PI * 48));
      const s = ac.createBufferSource(); s.buffer = b; s.loop = true; const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1900; bp.Q.value = 3; const g = ac.createGain(); g.gain.value = 0; s.connect(bp).connect(g).connect(out); s.start(); w = g; }
      w.gain.setTargetAtTime(on ? .035 : 0, ac.currentTime, .3); }; })();
    // the films in each sketch, as items for the screens
    const _p = new THREE.Vector3(), _b = new THREE.Box3(), _s = new THREE.Vector3();
    const sizeOf = o => { if (o.__sz) return o.__sz; _b.setFromObject(o); _b.getSize(_s); return (o.__sz = Math.max(.5, Math.max(_s.x, _s.y) * .9)); };
    function items() {
      const L = [], fov = camera.fov * Math.PI / 180;
      if (MODE === 'worms') (B.doodleWorms || []).forEach((w, k) => { const p = w.headPos; if (!p) return; const d = p.distanceTo(camera.position), frac = 3.2 / (d * 2 * Math.tan(fov / 2));
          L.push({key: w, pos: p.clone().add(new THREE.Vector3(0, 1.8, 0)), size: 3.2, clear: smooth(.06, .2, frac), src: srcFor('w' + k, '', k * 7 + (w.sign && w.sign.n ? +String(w.sign.n).replace(/\D/g, '') : 0)), clock: performance.now() / 1000 + k}); });
      else (B.streamEntities || []).forEach((e, k) => { if (e.kind === 'contaminant' || !e.filmDef) return; const o = e.mesh || e.plateObj || e.portalObj; if (!o || o.visible === false) return; o.getWorldPosition(_p);
          const sz = sizeOf(o), d = _p.distanceTo(camera.position), frac = sz / (d * 2 * Math.tan(fov / 2)), ahead = camera.getWorldDirection(_s).dot(_p.clone().sub(camera.position)) > 0;
          if (!ahead) return; L.push({key: e, pos: _p.clone(), size: sz * 1.1 * GROW, clear: smooth(NEAR[0], NEAR[1], frac), src: srcFor(e.filmDef.id, e.filmDef.title, e.filmDef.id), clock: performance.now() / 1000 + k * 1.7}); });
      return L; }
    const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
    // run inside the sketch's own frame: wrap its render
    let last = performance.now(); const render = renderer.render.bind(renderer);
    renderer.render = (s, c) => { if (s === scene) { const now = performance.now(), real = Math.min(.05, (now - last) / 1000); last = now; const it = items(); SCN.update(it, real, now / 1000, scene.fog ? scene.fog.color : new THREE.Color(0x061113), scene.fog && scene.fog.density ? scene.fog.density : .02);
        let held = 0; for (const S of SCN.pool) { if (!S.it) continue; const was = lastClear.get(S.it.key) || 0; if (S.a > .5 && was <= .5) { ping(1320 + Math.random() * 300, .03); bubbles(6); } lastClear.set(S.it.key, S.a); held = Math.max(held, S.a); }
        whir(held > .7); fadeStand();  if (mg && ac) { duck += ((held > .6 ? .55 : 1) - duck) * .05; mg.gain.setTargetAtTime(.7 * duck, ac.currentTime, .2); } }
      return render(s, c); };
    if (MODE === 'worms') fetch('../current/drift/data/doodles.json').then(r => r.json()).then(DD => { const DL = DD.doodles.filter(d => d.keys && d.keys.length);
      window.__realDoodle = (ctx, w, h, sign, ff, idx) => {   // the traced secondhand drawings, cycling through their keys, in the sign's colour
        const d = DL[(idx * 7) % DL.length], key = d.keys[Math.floor(ff / 6) % d.keys.length], sc = Math.min(w / (+d.w + 20), h / (+d.h + 20));
        ctx.clearRect(0, 0, w, h); ctx.save(); ctx.translate((w - +d.w * sc) / 2, (h - +d.h * sc) / 2); ctx.scale(sc, sc); ctx.strokeStyle = (sign && sign.color) || '#f6c47a'; ctx.lineWidth = 2.6 / sc; ctx.lineCap = ctx.lineJoin = 'round';
        ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 6 / sc; for (const st of key.s) { ctx.beginPath(); st.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); } ctx.restore(); }; });
    // the sketch drew stand-ins for films (pixel plates, portals); as the real footage clears, the stand-in fades
    const fadeStand = () => { for (const e of (B.streamEntities || [])) { const S = SCN.pool.find(S => S.it && S.it.key === e), a = S ? S.a : 0, o = e.mesh || e.plateObj || e.portalObj; if (!o || (!a && !o.__faded)) continue; o.__faded = a > .01;
        o.traverse(n => { const ms = n.material ? (Array.isArray(n.material) ? n.material : [n.material]) : []; for (const m of ms) { if (m.__op === undefined) { m.__op = m.opacity ?? 1; m.transparent = true; } m.opacity = m.__op * (1 - .85 * a); } }); } };
    window.__real = {SCN, items, SRC};
    console.info('[realfilm] footage for', MODE, 'song', SONG, 'films', F.length, 'clips', clips.length);
  }
})();

// every bonus piece opens back onto the open water that joins them
try { const a = document.createElement('a'); a.href = 'sea.html'; a.textContent = '← the open water'; a.style.cssText = 'position:fixed;left:14px;bottom:max(12px,env(safe-area-inset-bottom));z-index:9999;font:300 12px "JetBrains Mono",monospace;color:#f0a35a;text-decoration:none;text-shadow:0 0 6px #000;opacity:.85'; document.body.appendChild(a); } catch (e) {}
