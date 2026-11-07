// THE EDITOR: the end of a level is a cutting room. What you took is on a timeline; each clip lasts as long as you held it;
// the monitor plays the film you made; drag a clip to move it, tap it to see it; the first full pass is recorded so you can keep the film.
// Under it, the making of: the moments the jelly took each one, recorded from the water as they happened.
// A video made the game; the game makes a video.
export const ED_CSS = `.ed{pointer-events:auto;width:min(980px,100%);margin-top:14px}.ed .vd{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}.ed .vd b{font:400 clamp(30px,5vw,54px)/1 Anton,Impact,sans-serif;letter-spacing:.06em}
.ed .vd.won b{color:#f0a35a}.ed .vd.lost b{color:#ff6a55}.ed .vd.survived b{color:#cfdde8}.ed .vd i{font:400 22px/1 Anton,Impact,sans-serif;color:#f0a35a;letter-spacing:.15em;font-style:normal}.ed .vd span{font:300 15px/1.5 Jost,system-ui,sans-serif;color:#dfe6e0;flex:1 1 320px}
.ed .row{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:18px;margin-top:14px;align-items:start}@media (max-width:760px){.ed .row{grid-template-columns:1fr}}
.ed .mon{position:relative;background:#000;border-radius:6px;overflow:hidden;aspect-ratio:16/9}.ed .mon canvas{width:100%;height:100%;display:block}
.ed .tc{margin-top:6px;font:300 11.5px 'JetBrains Mono',monospace;color:#8293a4;display:flex;justify-content:space-between;gap:10px}.ed .tc a{color:#f0a35a;text-decoration:none}
.ed .tl{display:flex;gap:3px;margin-top:12px;min-height:58px;touch-action:none;user-select:none}.ed .cl{position:relative;flex:1 1 0;min-width:30px;height:58px;border-radius:3px;overflow:hidden;background:#111a22;cursor:grab;outline:1px solid rgba(207,221,232,.18)}
.ed .cl canvas{position:absolute;inset:0;width:100%;height:100%;opacity:.8}.ed .cl b{position:absolute;left:4px;bottom:3px;font:300 10px 'JetBrains Mono',monospace;color:#fff;text-shadow:0 0 4px #000}.ed .cl.on{outline:2px solid #f0a35a}.ed .cl.drag{opacity:.5}
.ed .cl.lost{flex:0 0 30px;cursor:default;background:repeating-linear-gradient(135deg,#2a1210 0 5px,#140808 5px 10px)}.ed .cl.lost canvas{opacity:.25}.ed .cl .ph{position:absolute;top:0;bottom:0;width:2px;background:#f0a35a;display:none}.ed .cl.on .ph{display:block}
.ed .note{margin-top:6px;font:300 12.5px/1.5 Jost,system-ui,sans-serif;color:#8293a4}.ed .note em{color:#ff8a75;font-style:normal}
.ed h3{margin:0 0 6px;font:400 12px Anton,Impact,sans-serif;letter-spacing:.3em;color:#8293a4}.ed .mk{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:6px;max-height:34vh;overflow:auto}
.ed .mk figure{margin:0}.ed .mk video{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:3px;background:#000;display:block}.ed .mk figcaption{font:300 10px/1.3 'JetBrains Mono',monospace;color:#8293a4;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ed .go2{margin-top:14px;font:400 13px Anton,Impact,sans-serif;letter-spacing:.2em;color:#f0a35a}`;

const mmss = t => `${String(Math.floor(t / 60)).padStart(2, '0')}:${(t % 60).toFixed(1).padStart(4, '0')}`;
export function mountEditor(root, o) {
  const {cut, FILMS, drawFrame, fps, stamp, verdict, making, title, slug} = o;
  let order = cut.map((c, i) => i), lostIx = cut.map((c, i) => i).filter(i => cut[i].lost), playIx = () => order.filter(i => !cut[i].lost);
  root.innerHTML = `<div class="ed"><div class="vd ${verdict.cls}"><b>${verdict.k}</b>${verdict.stars ? `<i>${'★'.repeat(verdict.stars)}${'☆'.repeat(3 - verdict.stars)}</i>` : ''}<span>${verdict.line}</span></div>
    <div class="row"><div><div class="mon"><canvas width="640" height="360"></canvas></div><div class="tc"><span class="t">00:00.0</span><span class="nm"></span><a class="sv" style="display:none" download="${slug}-film.webm">save the film</a></div>
      <div class="tl"></div><div class="note">Each clip lasts as long as you held it. Drag a clip to recut; tap one to see it.${lostIx.length ? ` <em>${lostIx.length} taken from you</em>: ${lostIx.map(i => `${FILMS[cut[i].film].title} (${cut[i].lost})`).join(', ')}.` : ''}</div></div>
      <div><h3>THE MAKING OF</h3><div class="mk">${making.filter(m => m.url).length ? making.filter(m => m.url).map(m => `<figure><video src="${m.url}" muted loop playsinline autoplay></video><figcaption>${m.labels.join(' · ')}</figcaption></figure>`).join('') : '<p class="note">The water was not recorded on this device.</p>'}</div></div></div>
    <div class="go2">${o.go}</div></div>`;
  const cv = root.querySelector('.mon canvas'), g = cv.getContext('2d'), tl = root.querySelector('.tl'), tcT = root.querySelector('.t'), tcN = root.querySelector('.nm'), sv = root.querySelector('.sv');
  const dur = i => Math.max(.4, cut[i].dur || .8), total = () => playIx().reduce((a, i) => a + dur(i), 0);
  // the timeline: clips side by side, widths in proportion to their length
  const thumb = (c, i) => { const k = document.createElement('canvas'); k.width = 96; k.height = 54; const kg = k.getContext('2d'), tryDraw = n => { if (!drawFrame(kg, c.film, c.fi, 96, 54) && n < 30) setTimeout(() => tryDraw(n + 1), 300); }; tryDraw(0); return k; };
  function render() { tl.innerHTML = ''; for (const i of order) { const c = cut[i], d = document.createElement('div'); d.className = 'cl' + (c.lost ? ' lost' : ''); d.dataset.i = i; if (!c.lost) d.style.flexGrow = dur(i).toFixed(2);
      d.appendChild(thumb(c, i)); d.insertAdjacentHTML('beforeend', `<b>${c.lost ? '×' : dur(i).toFixed(1) + 's'}</b><span class="ph"></span>`); d.title = `${FILMS[c.film].title} · ${stamp(c.film, c.fi)}${c.lost ? ' · ' + c.lost : ''}`; tl.appendChild(d); } }
  render();
  // play: the film in its order, each clip from the frame you took for as long as you held it; a title card first and the wordmark last
  let t = 0, last = performance.now(), rec = null, recDone = false, dirty = false, alive = true;
  const HEAD = 1.4, TAIL = 1.4;
  const card = (txt, sub, k) => { g.fillStyle = '#050608'; g.fillRect(0, 0, 640, 360); g.globalAlpha = Math.min(1, k * 3, (1 - k) * 3); g.fillStyle = '#efe4cc'; g.font = '400 13px Anton, Impact, sans-serif'; g.textAlign = 'left'; g.fillText('CONTAMINANT', 28, 36);
    g.font = '400 54px Anton, Impact, sans-serif'; g.fillStyle = '#f0a35a'; g.fillText(txt.toUpperCase(), 28, 210); g.font = '200 20px Jost, system-ui, sans-serif'; g.fillStyle = '#efe4cc'; g.fillText(sub, 30, 244); g.globalAlpha = 1; };
  function at(tt) { const ix = playIx(); let a = HEAD; for (let k = 0; k < ix.length; k++) { const d = dur(ix[k]); if (tt < a + d) return {k, i: ix[k], lt: tt - a}; a += d; } return null; }
  function tick(now) { if (!alive) return; requestAnimationFrame(tick); const dt = Math.min(.1, (now - last) / 1000); last = now; t += dt; const ix = playIx(), T = HEAD + total() + TAIL;
    if (t >= T) { t = 0; if (rec) { rec.stop(); rec = null; } else if (!recDone || dirty) startRec(); dirty = false; }
    let cur = null;
    if (!ix.length) card(title, 'nothing was held', (t % 2) / 2);
    else if (t < HEAD) card(title, 'a film made by a jellyfish', t / HEAD);
    else if (t >= HEAD + total()) card('jelly-films', `${ix.length} clips · ${total().toFixed(1)} s`, (t - HEAD - total()) / TAIL);
    else { cur = at(t); const c = cut[cur.i], f = FILMS[c.film], fi = c.fi + Math.floor(cur.lt * fps(f)); drawFrame(g, c.film, fi, 640, 360);
      g.fillStyle = 'rgba(5,6,8,.55)'; g.fillRect(0, 330, 640, 30); g.fillStyle = '#efe4cc'; g.font = "300 12px 'JetBrains Mono', monospace"; g.textAlign = 'left'; g.fillText(`${f.title}`.slice(0, 60), 14, 349); g.textAlign = 'right'; g.fillStyle = '#f0a35a'; g.fillText(stamp(c.film, fi), 626, 349); }
    tcT.textContent = `${mmss(Math.max(0, t - HEAD))} / ${mmss(total())}`; tcN.textContent = cur ? `clip ${cur.k + 1} of ${ix.length}` : '';
    tl.querySelectorAll('.cl').forEach(d => { const on = cur && +d.dataset.i === cur.i; d.classList.toggle('on', !!on); if (on) d.querySelector('.ph').style.left = `${(cur.lt / dur(cur.i)) * 100}%`; }); }
  requestAnimationFrame(tick);
  // keep the film: record the monitor through one full pass
  function startRec() { if (!window.MediaRecorder || !cv.captureStream) return; const mt = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm', 'video/mp4'].find(m => MediaRecorder.isTypeSupported(m)); if (!mt) return;
    try { const ch = []; rec = new MediaRecorder(cv.captureStream(24), {mimeType: mt, videoBitsPerSecond: 2.5e6}); rec.ondataavailable = e => e.data.size && ch.push(e.data);
      rec.onstop = () => { if (dirty) return; const b = new Blob(ch, {type: mt}); if (sv.href) URL.revokeObjectURL(sv.href); sv.href = URL.createObjectURL(b); sv.download = `${slug}-film.${mt.includes('mp4') ? 'mp4' : 'webm'}`; sv.textContent = `save the film · ${total().toFixed(1)} s`; sv.style.display = ''; recDone = true; }; rec.start(); } catch (e) { rec = null; } }
  // recut: drag a clip along the timeline; tap to jump to it
  let drag = null;
  tl.addEventListener('pointerdown', e => { const d = e.target.closest('.cl'); if (!d || d.classList.contains('lost')) return; drag = {i: +d.dataset.i, x: e.clientX, moved: false}; d.classList.add('drag'); try { tl.setPointerCapture(e.pointerId); } catch (x) {} e.stopPropagation(); });
  tl.addEventListener('pointermove', e => { if (!drag) return; if (Math.abs(e.clientX - drag.x) > 8) drag.moved = true; if (!drag.moved) return;
    const els = [...tl.querySelectorAll('.cl')], to = els.findIndex(el => { const r = el.getBoundingClientRect(); return e.clientX < r.left + r.width / 2; }), from = order.indexOf(drag.i), dest = to < 0 ? order.length - 1 : to > from ? to - 1 : to;
    if (dest !== from) { order.splice(from, 1); order.splice(dest, 0, drag.i); render(); tl.querySelector(`[data-i="${drag.i}"]`).classList.add('drag'); dirty = true; if (rec) { rec.stop(); rec = null; } } });
  const end = e => { if (!drag) return; const d = drag; drag = null; tl.querySelectorAll('.cl').forEach(el => el.classList.remove('drag')); if (!d.moved) { let a = HEAD; for (const i of playIx()) { if (i === d.i) { t = a + .01; break; } a += dur(i); } if (rec) { rec.stop(); rec = null; dirty = true; } } };
  tl.addEventListener('pointerup', end); tl.addEventListener('pointercancel', end);
  root.querySelector('.ed').addEventListener('pointerdown', e => e.stopPropagation());
  const mk = root.querySelector('.mk');
  return {addMaking(m) { if (!m.url) return; if (mk.querySelector('p')) mk.innerHTML = ''; mk.insertAdjacentHTML('beforeend', `<figure><video src="${m.url}" muted loop playsinline autoplay></video><figcaption>${m.labels.join(' · ')}</figcaption></figure>`); }, stop() { alive = false; if (rec) try { rec.stop(); } catch (e) {} }, order: () => order.slice()};
}
