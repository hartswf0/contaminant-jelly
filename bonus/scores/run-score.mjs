// Headless PEO runner: plays scores in The Lab (headless Chromium) and prints each @test's result.
//   node bonus/scores/run-score.mjs [score.peo ...] [--moto <dir>] [--from <sec>] [--until <sec>] [--skip <n>] [--json]
//   node bonus/scores/run-score.mjs <score.peo> --record out.mp4 --from 64 --until 93 [--fps 24] [--size 1280x720] [--moto <dir>]
// --record plays the score frame by frame (fixed 1/fps steps, every memory film seeked to its clip time) and writes an mp4 with the
//   song cut to the same window; every @test, the frame cold reads included, is measured on the frames that go into the file.
// With no score named it plays every .peo in bonus/scores/. The repo is served from a throwaway local server.
// --moto <dir> answers requests for https://hartswf0.github.io/moto/ from a local checkout (no network needed).
// --until stops each score early (later tests report "not reached"); --skip renders one frame in n (physics still runs every frame).
// Exit code 1 if any test fails, any score has parse errors, or the page throws.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '../..');
const argv = process.argv.slice(2), opt = {moto: null, until: null, from: 0, skip: 3, json: false, record: null, fps: 24, size: '1280x720'}, files = [];
for (let i = 0; i < argv.length; i++) { const a = argv[i]; if (a === '--moto') opt.moto = argv[++i]; else if (a === '--until') opt.until = +argv[++i]; else if (a === '--skip') opt.skip = +argv[++i]; else if (a === '--json') opt.json = true; else if (a === '--from') opt.from = +argv[++i]; else if (a === '--record') opt.record = argv[++i]; else if (a === '--fps') opt.fps = +argv[++i]; else if (a === '--size') opt.size = argv[++i]; else files.push(a); }
if (!files.length) for (const f of fs.readdirSync(HERE).filter(f => f.endsWith('.peo')).sort()) files.push(path.join(HERE, f));

const TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.peo': 'text/plain; charset=utf-8', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.mp4': 'video/mp4', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.css': 'text/css', '.woff2': 'font/woff2'};
const serve = (root, req, res) => { const u = decodeURIComponent(new URL(req.url, 'http://x').pathname), f = path.join(root, u.endsWith('/') ? u + 'index.html' : u);
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, {'content-type': TYPES[path.extname(f)] || 'application/octet-stream', 'access-control-allow-origin': '*'}); fs.createReadStream(f).pipe(res); };
const server = http.createServer((q, r) => serve(ROOT, q, r)); await new Promise(r => server.listen(0, '127.0.0.1', r)); const BASE = `http://127.0.0.1:${server.address().port}`;

let chromium; try { ({chromium} = await import('playwright')); } catch (e) { ({chromium} = createRequire(import.meta.url)('playwright')); }
const browser = await chromium.launch({args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--mute-audio']});
let bad = 0; const report = [];
for (const file of files) {
  const rel = path.relative(path.join(ROOT, 'bonus'), path.resolve(file)).split(path.sep).join('/');
  const [VW, VH] = opt.record ? opt.size.split('x').map(Number) : [960, 600], page = await browser.newPage({viewport: {width: VW, height: VH}}), errs = [];
  page.on('pageerror', e => errs.push(e.message));
  if (opt.moto) await page.route('https://hartswf0.github.io/moto/**', route => { const u = decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/moto/, '')), f = path.join(path.resolve(opt.moto), u);
    if (fs.existsSync(f)) route.fulfill({status: 200, path: f, headers: {'access-control-allow-origin': '*', 'content-type': TYPES[path.extname(f)] || 'application/octet-stream'}}); else route.fulfill({status: 404, body: ''}); });
  const t0 = Date.now();
  await page.goto(`${BASE}/bonus/lab.html?test&low&cinema${opt.record ? '&rec' : `&skip=${opt.skip}`}&score=${encodeURIComponent('./' + rel)}`);
  await page.waitForFunction(() => window.__lab && window.__lab.ready, null, {timeout: 60000});
  const errors = await page.evaluate(() => window.__lab.SC.errors);
  if (opt.from) await page.evaluate(f => window.__lab.seek(f), opt.from);
  await page.evaluate(() => window.__lab.MEMS && Promise.all([...window.__lab.MEMS.MEM.values()].map(m => m.ready)));
  const dur = await page.evaluate(() => window.__lab.SC.dur);
  if (opt.record) {
    const {spawn} = await import('node:child_process'), info = await page.evaluate(() => ({audio: window.__lab.SC.aud ? window.__lab.SC.aud.src : window.__lab.SONG.aud ? window.__lab.SONG.aud.src : null}));
    let audio = null; if (info.audio) { const u = new URL(info.audio); if (opt.moto && u.hostname === 'hartswf0.github.io' && u.pathname.startsWith('/moto/')) audio = path.join(path.resolve(opt.moto), decodeURIComponent(u.pathname.slice(5))); else if (u.origin === BASE) audio = path.join(ROOT, decodeURIComponent(u.pathname)); }
    const span = (opt.until || dur) - opt.from, n = Math.round(span * opt.fps);
    const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(opt.fps), '-c:v', 'mjpeg', '-i', '-'];
    if (audio && fs.existsSync(audio)) args.push('-ss', String(opt.from), '-t', String(span), '-i', audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k', '-shortest');
    args.push('-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p', '-r', String(opt.fps), '-movflags', '+faststart', path.resolve(opt.record));
    const ff = spawn('ffmpeg', args, {stdio: ['pipe', 'inherit', 'inherit']}), done = new Promise(r => ff.on('close', r));
    await page.evaluate(() => { window.__lab.SC.playing = true; });
    for (let i = 0; i < n; i++) { await page.evaluate(dt => window.__lab.recStep(dt), 1 / opt.fps);
      const jpg = await page.evaluate(() => window.__lab.R.domElement.toDataURL('image/jpeg', .9)); if (!ff.stdin.write(Buffer.from(jpg.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
      if (!opt.json && i % (opt.fps * 5) === 0) process.stderr.write(`  frame ${i}/${n} · score ${(opt.from + i / opt.fps).toFixed(1)} s\n`); }
    ff.stdin.end(); await done; await page.evaluate(() => { const S = window.__lab.SC; S.playing = false; });
    if (!opt.json) console.log(`recorded ${n} frames (${span.toFixed(1)} s at ${opt.fps} fps, ${VW}×${VH})${audio ? ' with the song' : ' (no audio file found)'} → ${opt.record}`);
  } else {
    if (opt.until) await page.evaluate(u => { const S = window.__lab.SC; S.dur = Math.min(S.dur, u); }, opt.until);
    await page.evaluate(() => window.__lab.play());
    await page.waitForFunction(() => window.__lab.SC.done, null, {timeout: Math.max(120000, dur * 4000), polling: 500}); }
  const res = await page.evaluate(() => window.__lab.SC.results);
  await page.close();
  const fails = res.filter(r => r.pass === false).length, unreached = res.filter(r => r.pass == null).length;
  if (fails || errors.length || errs.length) bad++;
  report.push({score: rel, seconds: dur, wall: (Date.now() - t0) / 1000, errors, pageErrors: errs, results: res});
  if (!opt.json) {
    console.log(`\n${rel} · ${dur.toFixed(1)} s of score in ${((Date.now() - t0) / 1000).toFixed(1)} s · ${res.length - fails - unreached} pass, ${fails} fail${unreached ? `, ${unreached} not reached` : ''}`);
    for (const e of errors) console.log(`  parse  line ${e.line}: ${e.msg}`);
    for (const e of errs) console.log(`  PAGE ERROR ${e}`);
    for (const r of res) console.log(`  ${r.pass === true ? 'PASS' : r.pass === false ? 'FAIL' : ' -- '} line ${r.line} ${r.kind} ${(r.args || []).join(' ')}${r.op ? ` ${r.op} ${r.rhs}` : ''}  got ${r.got ?? '—'}${r.note ? ` (${r.note})` : ''}`);
  }
}
if (opt.json) console.log(JSON.stringify(report, null, 1));
await browser.close(); server.close(); process.exit(bad ? 1 : 0);
