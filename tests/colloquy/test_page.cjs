// Headless Chromium (SwiftShader) tests of bonus/colloquy.html. Usage: node tests/colloquy/test_page.cjs [baseURL] [shotDir]
// Writes tests/colloquy/report-page.json and screenshots (desktop/phone, with and without plates).
const {chromium, devices} = require('playwright'), fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8791', SHOTS = process.argv[3] || path.join(__dirname, 'shots');
const {spawnSync} = require('child_process'), os = require('os');
fs.mkdirSync(SHOTS, {recursive: true});
const results = []; let failed = 0;
async function test(name, fn) { let ok = false, detail; try { detail = await fn(); ok = true; } catch (e) { detail = String(e.message || e).slice(0, 400); } if (!ok) failed++; results.push({name, ok, detail}); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? '  ' + JSON.stringify(detail) : '')); }
const assert = (c, m) => { if (!c) throw new Error(m); };
// render n frames in small batches (SwiftShader queues work; finish() keeps the queue short)
const ticks = async (p, n) => { for (let k = 0; k < n; k += 8) await p.evaluate(m => { for (let i = 0; i < m; i++) COLLOQUY.tick(1 / 30); COLLOQUY.stage.R.getContext().finish(); }, Math.min(8, n - k)); };
async function open(b, url, ctxOpts) { const ctx = await b.newContext(ctxOpts), p = await ctx.newPage(), errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(BASE + url); await p.waitForFunction(() => window.COLLOQUY && COLLOQUY.stage, null, {timeout: 60000}); return {p, ctx, errs}; }

(async () => {
  const b = await chromium.launch();
  // ---------------------------------------------------------------- desktop
  const D = await open(b, '/bonus/colloquy.html?test&manual&ui&seed=7', {viewport: {width: 1280, height: 720}});
  await test('desktop: loads and runs with no page errors', async () => { await D.p.evaluate(() => COLLOQUY.step(4.5)); await ticks(D.p, 24); assert(!D.errs.length, D.errs.join(' | ')); return {t: await D.p.evaluate(() => COLLOQUY.state.t)}; });
  await D.p.screenshot({path: path.join(SHOTS, 'desktop-clean.png')});
  await test('desktop: plates (wall label, state, legend) open and fill', async () => {
    await D.p.evaluate(() => { COLLOQUY.plate('label', true); COLLOQUY.plate('state', true); COLLOQUY.plate('legend', true); }); await ticks(D.p, 8);
    const r = await D.p.evaluate(() => ({label: document.querySelector('#label').innerText, state: document.querySelector('#stateBody').innerText, legend: document.querySelector('#legend').innerText}));
    for (const w of ['Sonnabend', 'Dowson', 'Watts', 'Institute of Contemporary Arts', 'ZKM', 'Pangaro', 'Dreher', 'satire']) assert(r.label.includes(w), 'label lacks ' + w);
    for (const w of ['G', 'J', 'F1', 'F2', 'F3', 'regime', 'stage', 'bar Z', 'per min']) assert(r.state.includes(w), 'state lacks ' + w);
    for (const w of ['G, J', 'Z', 'F1–F3', 'u', 'B', 'C, D', 'a', 'b', 'MA', 'MB', 'τ']) assert(r.legend.replace(/\s/g, '').includes(w.replace(/\s/g, '')), 'legend lacks ' + w);
    return {labelChars: r.label.length}; });
  await D.p.screenshot({path: path.join(SHOTS, 'desktop-plates.png')});
  await test('cinema (H) hides all UI', async () => {
    await D.p.keyboard.press('h'); await D.p.waitForTimeout(600); await ticks(D.p, 3);
    const vis = await D.p.evaluate(() => [...document.querySelectorAll('.ui:not(#cap),.plate')].filter(el => { const cs = getComputedStyle(el); return cs.display !== 'none' && +cs.opacity > .01 && el.getBoundingClientRect().width > 0; }).map(el => el.id));
    assert(!vis.length, 'still visible: ' + vis); return {hidden: true}; });
  await D.p.evaluate(() => COLLOQUY.letterbox(true)); await ticks(D.p, 4); await D.p.screenshot({path: path.join(SHOTS, 'desktop-cinema-letterbox.png')});
  await D.p.evaluate(() => { COLLOQUY.letterbox(false); COLLOQUY.cinema(false); });
  await test('auto-director cuts to the active handshake', async () => {
    const d = await D.p.evaluate(() => { const st = COLLOQUY.stage, rr = st.render; st.render = () => {}; for (let i = 0; i < 40 * 24; i++) COLLOQUY.tick(1 / 24); st.render = rr; return COLLOQUY.director(); });
    assert(d.cuts >= 3 && d.log.some(l => l.shot === 'mirror') && d.log.some(l => l.shot === 'two'), JSON.stringify(d)); return {cuts: d.cuts, shots: [...new Set(d.log.map(l => l.shot))]}; });
  await test('shots: plan, side, mirror close-up, triangulation render', async () => { for (const s of ['plan', 'side', 'mirror', 'tri']) { await D.p.evaluate(s => COLLOQUY.shot(s), s); await ticks(D.p, 3); await D.p.screenshot({path: path.join(SHOTS, `shot-${s}.png`)}); } await D.p.evaluate(() => COLLOQUY.shot('auto')); assert(!D.errs.length, D.errs.join('|')); return {shots: 4}; });
  await test('visitor gestures (desktop): stand in by tapping the floor; torch by tapping a female', async () => {
    await D.p.evaluate(() => { COLLOQUY.mode('stand'); }); await ticks(D.p, 3);
    await D.p.mouse.click(640, 360); const body = await D.p.evaluate(() => COLLOQUY.sim.S.visitor.body); assert(body, 'no visitor body after tap');
    await D.p.evaluate(() => COLLOQUY.mode('torch')); await ticks(D.p, 3);
    const xy = await D.p.evaluate(() => { const f = COLLOQUY.sim.S.females.findIndex(f => f.stage === 1); return {i: f, ...COLLOQUY.stage.screenOf('female', Math.max(0, f))}; });
    await D.p.mouse.click(xy.x, xy.y); const tor = await D.p.evaluate(() => COLLOQUY.sim.S.visitor.torch); assert(tor && tor.f === xy.i, 'torch not set ' + JSON.stringify(tor));
    await D.p.evaluate(() => { COLLOQUY.visitor.leave(); COLLOQUY.mode('watch'); }); return {body: {x: +body.x.toFixed(2), z: +body.z.toFixed(2)}, torch: tor.f}; });
  await test('PEO hook: state, parameters and setters', async () => {
    const r = await D.p.evaluate(() => { COLLOQUY.set({delta: 1.3, omega: .4, Lmin: .25, Lmax: .85, tau: 5, ambient: .3}); COLLOQUY.setDelta(.03, 'G', 'O'); const p = COLLOQUY.params, s = COLLOQUY.state; COLLOQUY.set({delta: 1, omega: .55, Lmin: .3, Lmax: .8, tau: 4.2, ambient: 0}); return {p, keys: Object.keys(s), m: Object.keys(s.males[0]), f: Object.keys(s.females[0])}; });
    assert(r.p.delta === 1.3 && r.p.omega === .4 && r.p.Lmin === .25 && r.p.Lmax === .85 && r.p.tau === 5 && r.p.ambient === .3 && r.p.deltas.G.O === .03 && r.p.cast.G === 'sentinel', JSON.stringify(r.p));
    for (const k of ['O', 'P', 'regime', 'stage', 'B', 'F', 'lamp']) assert(r.m.includes(k), 'male lacks ' + k); for (const k of ['b', 'tone', 'MA', 'MB', 'timer']) assert(r.f.includes(k), 'female lacks ' + k);
    return {params: Object.keys(r.p)}; });
  await test('ambient light control has a measurable effect on the page', async () => {
    const r = await D.p.evaluate(() => { const {makeColloquy} = {makeColloquy: null}; const run = amb => { COLLOQUY.set({ambient: amb}); const h0 = COLLOQUY.sim.S.handshakes; COLLOQUY.step(600); return COLLOQUY.sim.S.handshakes - h0; }; const dark = run(0), lit = run(.9); COLLOQUY.set({ambient: 0}); return {dark, lit}; });
    assert(r.dark > r.lit, JSON.stringify(r)); return {handshakesPer10min: r}; });
  await test('exhibition: 30 sim-minutes with the ghost visitor, no stuck states, all satisfied, no errors', async () => {
    const r = await D.p.evaluate(() => { COLLOQUY.exhibit(true); const s0 = COLLOQUY.sim.S.stuck; const out = COLLOQUY.soak(1800); out.stuck -= s0; return out; }); await ticks(D.p, 4);
    assert(r.stuck === 0 && r.sat.every(x => x > 0) && r.ghosts >= 10 && !D.errs.length, JSON.stringify(r) + D.errs.join('|')); await D.p.screenshot({path: path.join(SHOTS, 'desktop-exhibition.png')}); await D.p.evaluate(() => COLLOQUY.exhibit(false)); return r; });
  await D.ctx.close();
  // ---------------------------------------------------------------- the cineulation: the live machine plays as cinema by default
  const C = await open(b, '/bonus/colloquy.html?test&manual&seed=7', {viewport: {width: 1280, height: 720}});
  // @test cinema is the default view: letterboxed, every control invisible, captions only in the bar
  await test('cineulation: cinema is the default view, controls invisible', async () => { await ticks(C.p, 4); await C.p.waitForTimeout(600);
    const r = await C.p.evaluate(() => ({cls: document.body.className, vis: [...document.querySelectorAll('.ui:not(#cap),.plate,.dock button')].filter(el => { let e = el; while (e && e !== document.body) { const cs = getComputedStyle(e); if (cs.display === 'none' || +cs.opacity <= .01 || cs.visibility === 'hidden') return false; e = e.parentElement; } return el.getBoundingClientRect().width > 0; }).map(el => el.id || el.textContent)}));
    assert(/cinema/.test(r.cls) && /letter/.test(r.cls) && !r.vis.length, JSON.stringify(r)); await C.p.screenshot({path: path.join(SHOTS, 'cine-default.png')}); return r; });
  // @test cut count per minute in range; @test every cut within 1 frame of a sim event
  await test('cineulation: cuts per minute in range, every cut on a sim event (within one frame)', async () => {
    const r = await C.p.evaluate(() => { const st = COLLOQUY.stage, rr = st.render; st.render = () => {}; const t0 = COLLOQUY.state.t, c0 = st.director.cuts; for (let i = 0; i < 180 * 24; i++) COLLOQUY.tick(1 / 24); st.render = rr;
      const D = st.director, mins = (COLLOQUY.state.t - t0) / 60, log = D.log.filter(l => l.t > t0), ev = COLLOQUY.sim.S.log;
      const bad = log.filter(l => !(Math.abs(l.t - l.ev.t) <= 1 / 24 + 1e-6) || !ev.some(e => e.kind === l.ev.kind && Math.abs(e.t - l.ev.t) < 1e-3));
      const durs = log.slice(1).map((l, i) => l.t - log[i].t); return {perMin: +((D.cuts - c0) / mins).toFixed(1), cuts: D.cuts - c0, bad: bad.slice(0, 3), minDur: +Math.min(...durs).toFixed(2), maxDur: +Math.max(...durs).toFixed(2), shots: [...new Set(log.map(l => l.shot))]}; });
    assert(r.perMin >= 6 && r.perMin <= 40, 'cuts/min ' + r.perMin); assert(!r.bad.length, 'off-event cuts ' + JSON.stringify(r.bad)); assert(r.minDur >= .79, 'thrash ' + r.minDur);
    for (const s of ['two', 'mirror', 'bar', 'vane', 'memory', 'plan']) assert(r.shots.includes(s), 'never cut to ' + s); return r; });
  // @test the visitor's torch (a press on a female) works in cinema and the director cuts to it on that frame
  await test('cineulation: a press is the torch, and the director cuts to it', async () => {
    await C.p.evaluate(() => { COLLOQUY.shot('plan'); COLLOQUY.tick(1 / 24); COLLOQUY.shot('auto'); let n = 0; while (!COLLOQUY.sim.S.females.some(f => f.stage === 1 && COLLOQUY.sim.desireOf(f)) && n++ < 2400) COLLOQUY.sim.step(1 / 60); COLLOQUY.tick(1 / 24); });   // the wide plan, so every female is on screen
    const xy = await C.p.evaluate(() => { const i = Math.max(0, COLLOQUY.sim.S.females.findIndex(f => f.stage === 1 && COLLOQUY.sim.desireOf(f))); return {i, ...COLLOQUY.stage.screenOf('female', i)}; });
    await C.p.mouse.move(xy.x, xy.y); await C.p.mouse.down(); await C.p.evaluate(() => { COLLOQUY.tick(1 / 24); COLLOQUY.tick(1 / 24); }); await C.p.mouse.up();
    const r = await C.p.evaluate(() => ({tor: COLLOQUY.sim.S.visitor.torch, last: COLLOQUY.stage.director.log.slice(-1)[0], cinema: document.body.classList.contains('cinema')}));
    assert(r.tor && r.tor.f === xy.i && r.last.ev.kind === 'visitor' && r.last.shot === 'stranger' && r.cinema, JSON.stringify(r)); await ticks(C.p, 6); await C.p.screenshot({path: path.join(SHOTS, 'cine-torch.png')}); return {f: r.tor.f, cut: r.last.why}; });
  await test('cineulation: a tap on open water or a key reveals the controls', async () => {
    await C.p.mouse.click(30, 300); const a = await C.p.evaluate(() => document.body.classList.contains('cinema')); await C.p.keyboard.press('h'); const b2 = await C.p.evaluate(() => document.body.classList.contains('cinema')); await C.p.keyboard.press('x'); const c = await C.p.evaluate(() => document.body.classList.contains('cinema'));
    assert(!a && b2 && !c, JSON.stringify({a, b2, c})); return {}; });
  // @test satisfaction is visible: the satisfied male's region, 0.5 s after F = 1, is ≥ 40% darker than at his commitment (rendered frames)
  await test('satisfaction visible: brightness 0.5 s after closure ≥ 40% below the commit value', async () => {
    const out = [];
    for (let k = 0; k < 3; k++) out.push(await C.p.evaluate(() => { const st = COLLOQUY.stage, S = COLLOQUY.sim.S, rr = st.render; st.render = () => {}; const frame = () => { st.render = rr; COLLOQUY.tick(1 / 24); st.R.getContext().finish(); st.render = () => {}; };
      let n = 0; while (!S.males.some(m => m.stage === 4) && n++ < 24 * 300) COLLOQUY.tick(1 / 24); const mi = S.males.findIndex(m => m.stage === 4), m = S.males[mi], f = S.females[m.partner];
      st.director.focus = {f, m}; st.setShot('vane'); st.director.focus = {f, m}; for (let i = 0; i < 12; i++) COLLOQUY.tick(1 / 24); frame(); let c = st.screenOf('male', mi); const A = COLLOQUY.lum(c.x, c.y, 60);
      n = 0; while (m.stage !== 6 && m.stage !== 1 && n++ < 24 * 20) COLLOQUY.tick(1 / 24); if (m.stage !== 6) { st.setShot('auto'); st.render = rr; return {skip: 'aborted'}; } const tc = S.t; while (S.t < tc + .5) COLLOQUY.tick(1 / 24); frame(); c = st.screenOf('male', mi); const B = COLLOQUY.lum(c.x, c.y, 60);
      st.setShot('auto'); while (m.stage !== 1) COLLOQUY.tick(1 / 24); st.render = rr; return {male: m.id, female: f.id, closureT: +tc.toFixed(2), commitLum: +A.toFixed(1), postLum: +B.toFixed(1), drop: +(1 - B / A).toFixed(3)}; }));
    const ok = out.filter(o => !o.skip); assert(ok.length && ok.every(o => o.drop >= .4), JSON.stringify(out)); return out; });
  // @test an EBU R128 momentary peak within 0.5 s of every F = 1, at least 6 LU above the bed
  await test('satisfaction audible: momentary loudness ≥ +6 LU above the bed within 0.5 s of each F = 1', async () => {
    const au = await C.p.evaluate(() => COLLOQUY.audioProbe(150)); const wavp = path.join(os.tmpdir(), 'colloquy-probe.wav'); fs.writeFileSync(wavp, Buffer.from(au.wav, 'base64'));
    const txt = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', wavp, '-af', 'ebur128', '-f', 'null', '-'], {encoding: 'utf8'}).stderr; fs.unlinkSync(wavp);
    const M = [...txt.matchAll(/t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)/g)].map(x => [+x[1], x[2] === '-inf' ? -120 : +x[2]]), live = M.map(x => x[1]).filter(v => v > -70).sort((a, b) => a - b), bed = live[Math.floor(live.length / 2)];
    const rise = au.reinforce.map(t => +(Math.max(...M.filter(x => x[0] >= t && x[0] <= t + .5).map(x => x[1])) - bed).toFixed(1)), lra = +((txt.match(/LRA:\s*([\d.]+) LU/g) || []).pop() || 'LRA: 0').replace(/[^\d.]/g, '');
    assert(rise.length >= 3 && rise.every(r => r >= 6), JSON.stringify({bed, rise})); return {bedLUFS: bed, risesLU: rise, closures: rise.length, LRA: lra}; });
  await C.ctx.close();
  // @test phone view uncovered: in cinema on a 390 px phone, nothing but the picture covers the picture
  const PC = await open(b, '/bonus/colloquy.html?test&manual&seed=7', {...devices['iPhone 13'], viewport: {width: 390, height: 844}});
  await test('cineulation 390 px: the phone view is uncovered', async () => { await PC.p.evaluate(() => COLLOQUY.step(4)); await ticks(PC.p, 8); await PC.p.waitForTimeout(600);
    const r = await PC.p.evaluate(() => { const bar = document.getElementById('lbT').getBoundingClientRect().height, cap = document.getElementById('cap').getBoundingClientRect(), hits = [];
      for (let y = bar + 4; y < innerHeight - bar - 4; y += 40) for (let x = 6; x < innerWidth; x += 48) { if (y > cap.top - 2 && y < cap.bottom + 2) continue; const el = document.elementFromPoint(x, y); if (el && el.id !== 'gl') hits.push([x, Math.round(y), el.id || el.tagName]); }
      return {bar: Math.round(bar), covered: hits.slice(0, 5), n: hits.length, sw: document.documentElement.scrollWidth}; });
    assert(!r.n && r.sw <= 390 && r.bar < 70, JSON.stringify(r)); await PC.p.screenshot({path: path.join(SHOTS, 'cine-phone.png')}); return r; });
  await PC.ctx.close();
  // ---------------------------------------------------------------- phone, 390 px
  const M = await open(b, '/bonus/colloquy.html?test&manual&ui&seed=7', {...devices['iPhone 13'], viewport: {width: 390, height: 844}});
  await test('390 px phone: no horizontal overflow, the dock fits, no errors', async () => { await M.p.evaluate(() => COLLOQUY.step(5)); await ticks(M.p, 16);
    const r = await M.p.evaluate(() => { const d = document.querySelector('#dock').getBoundingClientRect(); const over = [...document.querySelectorAll('.ui, .dock button')].filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.left < -1 || r.right > innerWidth + 1); }).map(e => e.id || e.textContent);
      return {sw: document.documentElement.scrollWidth, iw: innerWidth, dock: [d.left, d.right, d.top, d.bottom].map(Math.round), over, low: COLLOQUY.stage.pr}; });
    assert(r.sw <= r.iw && !r.over.length && r.dock[3] <= 844 && r.dock[0] >= 0 && r.dock[1] <= 390 && !M.errs.length, JSON.stringify(r) + M.errs.join('|')); return r; });
  await M.p.screenshot({path: path.join(SHOTS, 'phone-clean.png')});
  await test('390 px phone: plates open as a bottom sheet inside the screen', async () => {
    const r = []; for (const id of ['state', 'label', 'legend']) { await M.p.evaluate(id => COLLOQUY.plate(id, true), id); await ticks(M.p, 2); const bb = await M.p.evaluate(id => { const r = document.getElementById(id).getBoundingClientRect(); return [r.left, r.right, r.top, r.bottom].map(Math.round); }, id); r.push(bb);
      assert(bb[0] >= 0 && bb[1] <= 390 && bb[2] >= 0 && bb[3] <= 844, id + ' ' + bb); await M.p.screenshot({path: path.join(SHOTS, `phone-plate-${id}.png`)}); }
    await M.p.evaluate(() => { for (const id of ['state', 'label', 'legend']) COLLOQUY.plate(id, false); }); return r; });
  await test('390 px phone: touch gestures (tap STAND IN, tap a female with TORCH, drag CONDUCT)', async () => {
    await M.p.tap('[data-v="stand"]'); await ticks(M.p, 3); await M.p.touchscreen.tap(195, 400); const body = await M.p.evaluate(() => !!COLLOQUY.sim.S.visitor.body);
    await M.p.tap('[data-v="torch"]'); await ticks(M.p, 3); const xy = await M.p.evaluate(() => { const i = Math.max(0, COLLOQUY.sim.S.females.findIndex(f => f.stage === 1)); return {i, ...COLLOQUY.stage.screenOf('female', i)}; });
    await M.p.touchscreen.tap(xy.x, xy.y); const tor = await M.p.evaluate(() => COLLOQUY.sim.S.visitor.torch);
    await M.p.tap('[data-v="conduct"]'); const cv = await M.p.$('#gl'); await M.p.evaluate(() => { const c = document.getElementById('gl'); const ev = (t, x, y) => c.dispatchEvent(new PointerEvent(t, {pointerId: 3, clientX: x, clientY: y, bubbles: true, pointerType: 'touch'})); ev('pointerdown', 100, 400); ev('pointermove', 200, 300); ev('pointermove', 260, 260); ev('pointerup', 260, 260); });
    const P = await M.p.evaluate(() => COLLOQUY.params); assert(body && tor && P.zBias > .3 && P.delta > 1.3, JSON.stringify({body, tor, z: P.zBias, d: P.delta}));
    await M.p.evaluate(() => { COLLOQUY.visitor.conduct({zBias: 0, tempo: 1}); COLLOQUY.visitor.leave(); COLLOQUY.mode('watch'); }); return {stand: body, torchF: tor.f, zBias: P.zBias, tempo: P.delta}; });
  await test('390 px phone: cinema hides all UI', async () => { await M.p.evaluate(() => COLLOQUY.cinema(true)); await M.p.waitForTimeout(600); await ticks(M.p, 3);
    const vis = await M.p.evaluate(() => [...document.querySelectorAll('.ui:not(#cap),.plate')].filter(el => { const cs = getComputedStyle(el); return cs.display !== 'none' && +cs.opacity > .01; }).map(el => el.id)); assert(!vis.length, vis.join()); await M.p.screenshot({path: path.join(SHOTS, 'phone-cinema.png')}); return {}; });
  await M.ctx.close(); await b.close();
  fs.writeFileSync(path.join(__dirname, 'report-page.json'), JSON.stringify({suite: 'colloquy page (headless Chromium, SwiftShader)', when: new Date().toISOString(), passed: results.length - failed, failed, shots: SHOTS, results}, null, 1));
  console.log(`\n${results.length - failed}/${results.length} passed`); process.exit(failed ? 1 : 0);
})();
