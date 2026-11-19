// node tools/drawn_shot.js 7 [more ids]   -> .raw/drawn_p07.jpg : eight moments (1, 2.5, 4, 5.5, 7, 8.5, 10, 11.5 s) left to right, top to bottom
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const { execFileSync } = require('child_process');
(async () => {
  const root = path.join(__dirname, '..'); fs.mkdirSync(path.join(root, '.raw'), { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1100, height: 1100 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.join(root, 'drawn/index.html')); await p.waitForTimeout(300);
  for (const a of process.argv.slice(2)) {
    const id = parseInt(a.replace(/\D/g, ''), 10), pad = String(id).padStart(2, '0'); const files = [];
    if (!(await p.evaluate(i => !!DRAWN.scenes[i], id))) { console.log('p' + pad + ': no scene registered (syntax error or wrong id?) ' + errs.join(' | ')); continue; }
    let bad = null;
    for (const [k, t] of [1, 2.5, 4, 5.5, 7, 8.5, 10, 11.5].entries()) {
      const e = await p.evaluate(([i, tt]) => window.__shot(i, tt), [id, t]); if (e) bad = e;
      const f = path.join(root, '.raw', `d_${pad}_${k}.png`); const data = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
      fs.writeFileSync(f, Buffer.from(data.split(',')[1], 'base64')); files.push(f);
    }
    const out = path.join(root, '.raw', `drawn_p${pad}.jpg`);
    execFileSync('ffmpeg', ['-v', 'error', '-y', ...files.flatMap(f => ['-i', f]), '-filter_complex', files.map((_, i) => `[${i}]scale=420:420[v${i}]`).join(';') + ';' + files.map((_, i) => `[v${i}]`).join('') + 'xstack=inputs=8:layout=0_0|420_0|840_0|1260_0|0_420|420_420|840_420|1260_420', '-q:v', '4', out]);
    files.forEach(f => fs.unlinkSync(f));
    console.log('p' + pad + ': ' + out + (bad ? '  DRAW ERROR: ' + bad.split('\n')[0] : ''));
  }
  await b.close();
})();
