#!/usr/bin/env node
// JELLYCHECK: the repair loop's measuring step. Runs the Real Jelly headless, lets it swim for some beats, and prints its own CHECK
// (the same numbers the page shows with ?check) against the target ranges. Exit code 0 if every measure is in range, 1 if not.
//   node sim/jellycheck/check.js [--thr 2.3] [--beats 5] [--page bonus/realjelly.html] [--full]   (--full: the desktop build; default is the phone build)
// Needs Playwright (npm i playwright) and a Chromium it can launch. See bonus/SCION_REPAIR_LOOP.md.
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const ROOT = path.resolve(__dirname, '../..'), PAGE = arg('page', 'bonus/realjelly.html'), BEATS = +arg('beats', 5), THR = arg('thr', null);
const TY = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.glb': 'model/gltf-binary'};
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); } r.writeHead(200, {'Content-Type': TY[path.extname(f)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(r); });
(async () => { await new Promise(r => srv.listen(0, '127.0.0.1', r)); const b = await chromium.launch({args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await (await b.newContext({viewport: {width: 320, height: 320}})).newPage(), errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(`http://127.0.0.1:${srv.address().port}/${PAGE}?check${process.argv.includes('--full') ? '' : '&low'}${THR ? '&thr=' + THR : ''}`); await p.waitForTimeout(3000); await p.mouse.click(160, 160);
  const out = await p.evaluate(async beats => { const L = window.__rj; L.stopFilm(false); const w = ms => new Promise(r => setTimeout(r, ms)), t0 = performance.now(); let seen = 0, last = null;
    while (seen < beats + 1 && performance.now() - t0 < 240000) { L.LIGHT.copy(L.COM).addScaledVector(L.AX, 9); await w(50); if (L.CK.cur !== last) { last = L.CK.cur; seen++; } }   // the light is held straight ahead: a steady swim
    return {out: L.CK.out, target: L.TARGET, thrust: L.THRUST, fixed: L.CK.fixed, T: L.T}; }, BEATS);
  await b.close(); srv.close(); let bad = 0; console.log(`jellycheck · ${PAGE} · thrust ${out.thrust} · ${out.out.n || 0} beats · ${out.T.toFixed(0)} s of swimming`);
  for (const [k, name, lo, hi, why] of out.target) { const v = out.out[k], ok = v !== undefined && v >= lo && v <= hi; if (!ok) bad++; console.log(`${ok ? 'ok  ' : 'FAIL'} ${name.padEnd(32)} ${(v === undefined ? '—' : v.toFixed(2)).padStart(7)}   want ${lo}–${hi}   (${why})`); }
  console.log(`tentacle points pushed back out of the bell while swimming: ${out.fixed || 0}`); if (errs.length) { console.log('page errors:', errs.slice(0, 3)); bad++; } process.exit(bad ? 1 : 0); })();
