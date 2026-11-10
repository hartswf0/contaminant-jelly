// The Lab's own checks (headless Chromium, SwiftShader): modes without errors, steering that goes where it is told,
// a score parameter that changes measured motion, panels ⇄ score, cinema hides the UI, phone layout, the old pages.
//   node bonus/scores/test-lab.mjs [--shots <dir>]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '../..');
const argv = process.argv.slice(2), SHOTS = argv.includes('--shots') ? argv[argv.indexOf('--shots') + 1] : null; if (SHOTS) fs.mkdirSync(SHOTS, {recursive: true});
const TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.peo': 'text/plain', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg'};
const server = http.createServer((req, res) => { const u = decodeURIComponent(new URL(req.url, 'http://x').pathname), f = path.join(ROOT, u.endsWith('/') ? u + 'index.html' : u);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; } res.writeHead(200, {'content-type': TYPES[path.extname(f)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res); });
await new Promise(r => server.listen(0, '127.0.0.1', r)); const BASE = `http://127.0.0.1:${server.address().port}`;
let chromium; try { ({chromium} = await import('playwright')); } catch (e) { ({chromium} = createRequire(import.meta.url)('playwright')); }
const browser = await chromium.launch({args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio']});
const results = []; const ok = (name, pass, got) => { results.push({name, pass: !!pass, got}); console.log(`${pass ? 'PASS' : 'FAIL'} ${name}${got !== undefined ? '  ' + JSON.stringify(got) : ''}`); };
const b64 = t => Buffer.from(t, 'utf8').toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
async function open(q, vp = {width: 960, height: 600}, extra = {}) { const ctx = await browser.newContext({viewport: vp, ...extra}), page = await ctx.newPage(), errs = [];
  page.on('pageerror', e => errs.push(e.message)); await page.goto(`${BASE}/bonus/lab.html?test&low&${q}`); await page.waitForFunction(() => window.__lab && window.__lab.ready, null, {timeout: 60000}); await page.waitForTimeout(600); return {page, errs, ctx}; }
const shot = async (page, name) => { if (SHOTS) await page.screenshot({path: path.join(SHOTS, name + '.png')}); };
const simT = (page, s) => page.evaluate(s => new Promise(r => { const L = window.__lab, t0 = L.T(); const w = () => L.T() - t0 >= s ? r() : requestAnimationFrame(w); w(); }), s);

// 1 · every mode and panel, desktop, no page errors
{ const {page, errs, ctx} = await open('');
  await shot(page, 'desktop-inspect');
  await page.click('[data-p="pL"]'); await simT(page, .5); await shot(page, 'desktop-inspect-specimens'); await page.click('[data-p="pL"]');
  await page.click('[data-p="pR"]'); await simT(page, .5); await shot(page, 'desktop-camera-music-light'); await page.click('[data-p="pR"]');
  for (const m of ['open', 'steer', 'inspect']) { await page.click(`[data-mode="${m}"]`); await simT(page, 1.5); if (m !== 'inspect') await shot(page, `desktop-${m}`); }
  await page.click('[data-p="pS"]'); await simT(page, .3); await shot(page, 'desktop-score');
  ok('desktop: inspect, open water, steer, panels, score: no page errors', !errs.length, errs); await ctx.close(); }

// 2 · open water: the jelly goes where it is told (keys, then a held finger), measured along the camera's right
{ const {page, errs, ctx} = await open('mode=open');
  await simT(page, 2);
  const right = () => page.evaluate(() => { const L = window.__lab, r = new L.THREE.Vector3().setFromMatrixColumn(L.cam.matrixWorld, 0); return [r.x, r.y, r.z]; });
  const pos = () => page.evaluate(() => { const p = window.__lab.PILOT().B.p; return [p.x, p.y, p.z]; });
  const along = (a, b, r) => (b[0] - a[0]) * r[0] + (b[1] - a[1]) * r[1] + (b[2] - a[2]) * r[2];
  let r = await right(), a = await pos(); await page.keyboard.down('d'); await simT(page, 4); await page.keyboard.up('d'); let b = await pos();
  const keyR = along(a, b, r); ok('open water: holding D moves the jelly to the camera\'s right', keyR > 1, +keyR.toFixed(2));
  await simT(page, 2); r = await right(); a = await pos(); await page.keyboard.down('a'); await simT(page, 4); await page.keyboard.up('a'); b = await pos();
  const keyL = along(a, b, r); ok('open water: holding A moves it to the left', keyL < -1, +keyL.toFixed(2));
  await simT(page, 2); r = await right(); a = await pos(); await page.mouse.move(880, 300); await page.mouse.down(); await simT(page, 4); await shot(page, 'desktop-open-glide-held'); await page.mouse.up(); b = await pos();
  const fing = along(a, b, r); ok('open water: holding the water right of the bell swims it right (glide)', fing > .5, +fing.toFixed(2));
  const st = await page.evaluate(() => window.__lab.PILOT().B.strokes); ok('open water: the motion is strokes (beats), not sliding', st >= 3, st);
  ok('open water: no page errors', !errs.length, errs); await ctx.close(); }

// 3 · a steer parameter written in the score changes the measured motion
{ const run = async thrust => { const s = `@world open bpm=120\n@cast m:medusa at=0,0,0\n@steer m thrust=${thrust}\n@op 0s..8s swim m to=0,0,-40\n@test 8s moved m > 0\n`;
    const {page, errs, ctx} = await open(`s=${b64(s)}&play`); await page.waitForFunction(() => window.__lab.SC.done, null, {timeout: 120000, polling: 300}); const r = await page.evaluate(() => window.__lab.SC.results[0].got); await ctx.close(); return {r, errs}; };
  const lo = await run(1), hi = await run(4);
  ok('score: @steer thrust=4 swims farther than thrust=1 in the same 8 s', hi.r > lo.r * 1.5, {thrust1: lo.r, thrust4: hi.r}); ok('score runs: no page errors', !lo.errs.length && !hi.errs.length, [...lo.errs, ...hi.errs]); }

// 4 · steer mode: a finger on the floor below the bell plants an arm; pulling it moves the bell
{ const {page, errs, ctx} = await open('mode=steer'); await simT(page, 1.5);
  const before = await page.evaluate(() => { const p = window.__lab.PILOT().B.p; return [p.x, p.y, p.z]; });
  await page.mouse.move(480, 470); await page.mouse.down(); await simT(page, 1.2);
  const latched = await page.evaluate(() => window.__lab.ARMS_STATE ? window.__lab.ARMS_STATE() : null);
  await page.mouse.move(480, 520, {steps: 6}); await simT(page, 2.5); await shot(page, 'desktop-steer-arm'); await page.mouse.up(); await simT(page, .5);
  const after = await page.evaluate(() => { const p = window.__lab.PILOT().B.p; return [p.x, p.y, p.z]; });
  const moved = Math.hypot(after[0] - before[0], after[1] - before[1], after[2] - before[2]);
  ok('steer: a finger on the floor gives the bell an arm', latched && latched.some(m => m !== 'free'), latched); ok('steer: the arm moves the bell', moved > .3, +moved.toFixed(2));
  ok('steer: no page errors', !errs.length, errs); await ctx.close(); }

// 5 · panels ⇄ score: a score sets the panels; panels changed by hand come back out as a score that rebuilds them
{ const {page, errs, ctx} = await open('score=scores/whitney.peo');
  const a = await page.evaluate(() => { const L = window.__lab; return {cam: L.CAM.mode, dist: L.CAM.dist, light: L.ORG.params.mode, n: L.ORG.params.n, cast: L.LIVE.map(E => E.name)}; });
  ok('score → panels: camera, light and cast come from whitney.peo', a.cam === 'orbit' && a.dist === 10 && a.light === 'rose' && a.n === 12 && a.cast.join() === 'glass,veil,golden', a);
  await page.click('[data-p="pR"]'); await page.click('[data-cam="crane"]'); await page.click('[data-pre="Arabesque"]'); await page.click('[data-p="pL"]'); await page.click('[data-add="reel"]');
  const text = await page.evaluate(() => window.__lab.PEO.serialize(window.__lab.currentScore()));
  const rt = await page.evaluate(t => { const P = window.__lab.PEO, r = P.parse(t); return {errors: r.errors.length, same: P.same(r.score, P.parse(P.serialize(r.score)).score)}; }, text);
  await ctx.close();
  const two = await open(`s=${b64(text)}`); const b = await two.page.evaluate(() => { const L = window.__lab; return {cam: L.CAM.mode, light: L.ORG.params.mode, n: L.ORG.params.n, cast: L.LIVE.map(E => E.id)}; });
  ok('panels → score → panels: crane, Arabesque and the added reel survive the trip', b.cam === 'crane' && b.light === 'epicycle' && b.n === 14 && b.cast.includes('reel') && !rt.errors && rt.same, {b, rt});
  ok('panels ⇄ score: no page errors', !errs.length && !two.errs.length, [...errs, ...two.errs]); await two.ctx.close(); }

// 6 · cinema hides every piece of UI (and the glyph fades); letterbox and clean too
{ const {page, errs, ctx} = await open('mode=open'); await page.click('[data-p="pS"]'); await page.click('#cine'); await simT(page, 3.2);
  const vis = await page.evaluate(() => [...document.querySelectorAll('.ui,.panel,.tag,#stick')].filter(e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > .01 && r.width > 0 && e.textContent.trim(); }).map(e => e.id || e.className));
  await shot(page, 'desktop-cinema'); ok('cinema: no UI left on screen', !vis.length, vis);
  await page.keyboard.press('h'); await page.click('#lb'); await page.click('#clean'); await simT(page, .5); await shot(page, 'desktop-letterbox-clean');
  const tags = await page.evaluate(() => [...document.querySelectorAll('.tag')].filter(e => getComputedStyle(e).display !== 'none').length); ok('clean: the name tags go', tags === 0, tags);
  ok('cinema/letterbox/clean: no page errors', !errs.length, errs); await ctx.close(); }

// 7 · phone: no sideways scroll at 390 px, the sheet leaves the water visible, the score editor fits
{ const phone = {viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true};
  const {page, errs, ctx} = await open('', phone.viewport, {deviceScaleFactor: 2, isMobile: true, hasTouch: true});
  const sw = async () => page.evaluate(() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth));
  await shot(page, 'phone-inspect');
  const res = {};
  for (const [m, p] of [['inspect', 'pL'], ['inspect', 'pR'], ['open', null], ['steer', null], ['inspect', 'pS']]) { await page.click(`[data-mode="${m}"]`); if (p) await page.click(`[data-p="${p}"]`); await simT(page, 1);
    const r = await page.evaluate(() => { const o = document.querySelector('.panel.open'); if (!o) return null; const b = o.getBoundingClientRect(); return {top: Math.round(b.top), h: Math.round(b.height), vh: innerHeight}; });
    res[m + (p || '')] = {sw: await sw(), sheet: r}; await shot(page, `phone-${m}${p ? '-' + p : ''}`); if (p) await page.click(`[data-p="${p}"]`); }
  const wide = Object.values(res).every(x => x.sw <= 390), sheets = Object.values(res).every(x => !x.sheet || x.sheet.top > x.sheet.vh * .4);
  ok('phone 390: no horizontal scroll in any mode or panel', wide, Object.fromEntries(Object.entries(res).map(([k, v]) => [k, v.sw])));
  ok('phone 390: every sheet leaves the top 40% of the water clear', sheets, Object.fromEntries(Object.entries(res).map(([k, v]) => [k, v.sheet])));
  await page.click('[data-p="pS"]'); const ta = await page.evaluate(() => { const b = document.getElementById('peo').getBoundingClientRect(); return {w: Math.round(b.width), h: Math.round(b.height), right: Math.round(b.right)}; });
  ok('phone 390: the score editor fits and is usable', ta.w > 300 && ta.h >= 90 && ta.right <= 390, ta);
  await page.click('#cine'); await simT(page, .5); await shot(page, 'phone-cinema');
  ok('phone: no page errors', !errs.length, errs); await ctx.close(); }

// 8 · the old pages still load with no errors (jellylab.html now forwards to lab.html with its query)
for (const f of ['sea.html', 'steerlab.html', 'steerlab3d.html', 'steerlab4d.html', 'jellyorchestra.html', 'jellylab.html?cam=crane', 'scores/index.html', '../index.html']) {
  const ctx = await browser.newContext({viewport: {width: 1000, height: 650}}), page = await ctx.newPage(), errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(`${BASE}/bonus/${f}`); await page.waitForTimeout(3500);
  const extra = f.startsWith('jellylab') ? await page.evaluate(() => location.pathname.endsWith('lab.html') && !location.pathname.endsWith('jellylab.html') && window.__lab && window.__lab.CAM.mode) : null;
  ok(`old page ${f}: loads, no page errors${extra !== null ? ' (forwards to the Lab, keeps ?cam=crane)' : ''}`, !errs.length && (extra === null || extra === 'crane'), errs.length ? errs : extra ?? undefined); await ctx.close(); }

const fails = results.filter(r => !r.pass).length; console.log(`\n${results.length - fails}/${results.length} passed`);
await browser.close(); server.close(); process.exit(fails ? 1 : 0);
