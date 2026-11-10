// Records bonus/colloquy/colloquy-film.mp4: the page in film mode (?film), stepped deterministically frame by frame in headless Chromium,
// piped to ffmpeg; the sound is rendered offline from the same run's trace. Usage: node tests/colloquy/render_film.cjs [baseURL] [seconds]
const {chromium} = require('playwright'), {spawn} = require('child_process'), fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8791', DUR = +(process.argv[3] || 84), FPS = 24, N = Math.round(DUR * FPS);
const OUT = path.join(__dirname, '../../bonus/colloquy/colloquy-film.mp4'), TMPV = OUT + '.video.mp4', TMPA = OUT + '.wav';
(async () => {
  const b = await chromium.launch(), p = await b.newPage({viewport: {width: 1280, height: 720}}); const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(`${BASE}/bonus/colloquy.html?film&seed=9&tempo=1.8&dur=${DUR}`); await p.waitForFunction(() => window.COLLOQUY && COLLOQUY.film);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-maxrate', '1100k', '-bufsize', '2200k', '-pix_fmt', 'yuv420p', '-threads', '2', TMPV], {stdio: ['pipe', 'inherit', 'inherit']});
  const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    await p.evaluate(() => { COLLOQUY.film.frame(); COLLOQUY.stage.R.getContext().finish(); });
    const jpg = await p.screenshot({type: 'jpeg', quality: 90}); if (!ff.stdin.write(jpg)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 120 === 0) console.log(`frame ${f}/${N} · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  const b64 = await p.evaluate(d => COLLOQUY.film.audio(d), DUR); fs.writeFileSync(TMPA, Buffer.from(b64, 'base64'));
  const log = await p.evaluate(() => COLLOQUY.events(4000).filter(e => ['reinforce', 'abort', 'visitor', 'memory'].includes(e.kind)).map(e => ({t: +e.t.toFixed(2), kind: e.kind, m: e.m, f: e.f, why: e.why, mode: e.mode, vane: e.vane})));
  await b.close();
  await new Promise(r => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-i', TMPV, '-i', TMPA, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', OUT], {stdio: 'inherit'}).on('close', r));
  fs.unlinkSync(TMPV); fs.unlinkSync(TMPA);
  fs.writeFileSync(path.join(__dirname, 'report-film.json'), JSON.stringify({film: 'bonus/colloquy/colloquy-film.mp4', seconds: DUR, fps: FPS, size: [1280, 720], seed: 9, tempo: 1.8, director: 'the live event-driven director (same page, same clock)', bytes: fs.statSync(OUT).size, renderSeconds: Math.round((Date.now() - t0) / 1000), pageErrors: errs, events: log}, null, 1));
  console.log('done', OUT, fs.statSync(OUT).size, 'bytes', errs.length ? 'ERRORS ' + errs.join('|') : '');
})();
