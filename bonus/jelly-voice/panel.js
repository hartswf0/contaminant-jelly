import {CAST} from './cast.mjs';
import {createScore} from './score.mjs';
import {VoiceRenderer} from './client.mjs';
import {TakePlayer, encodeWav, frameAt} from './performance.mjs';

const DEFAULTS = {
  speech: 'The little jelly has a voice. Can you hear the water in my words?',
  joke: 'I tried to bottle my thoughts. | They kept escaping.',
  sing: 'Let the little river carry me home.',
  rap: 'Wet bell, slow glow. Let the little river flow.',
};
const CSS = `
 :host{position:fixed;left:16px;bottom:16px;z-index:9000;font:13px/1.45 ui-sans-serif,system-ui,sans-serif;color:#ecf1ec;--accent:#c6efb0;letter-spacing:0;max-width:calc(100vw - 32px);}
 *{box-sizing:border-box} button,select,input,textarea{font:inherit} button{cursor:pointer} button:disabled{cursor:default;opacity:.4}
 .toggle{border:1px solid #bdcdbb5c;border-radius:100px;background:#16221de8;color:#ecf1ec;padding:10px 16px;box-shadow:0 4px 24px #0003;display:flex;gap:10px;align-items:center;font-size:11px;letter-spacing:.13em;text-transform:uppercase}
 .dot{height:7px;width:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px #c6efb040}
 .panel{width:360px;max-width:calc(100vw - 32px);max-height:calc(100dvh - 90px);overflow:auto;margin-bottom:10px;border:1px solid #bdcdbb4a;border-radius:16px;background:#101b16f5;box-shadow:0 12px 60px #0005;backdrop-filter:blur(18px);padding:18px;}
 [hidden]{display:none!important} h2{font-size:21px;font-weight:500;letter-spacing:-.03em;margin:0} p{margin:6px 0 14px;color:#a4b4a7;font-size:12px} header{display:flex;align-items:start;justify-content:space-between;margin-bottom:14px}
 .eyebrow{font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:#a3bc9b;margin-bottom:5px} .close{border:0;background:none;color:#afbdaf;font-size:21px;padding:0 4px}
 label{display:block;color:#b8c9bb;font-size:11px} select,input[type=number],input[type=text],textarea{display:block;width:100%;border:1px solid #a7b59f33;border-radius:7px;background:#ffffff07;color:#eef5ed;padding:8px;margin-top:5px;outline:none}
 select option{color:#17261b;background:#edf3ed} textarea{resize:vertical;min-height:78px;font-size:13px;line-height:1.5} textarea:focus,input:focus,select:focus{border-color:#b9e1a4}
 .row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px} .mode{display:flex;gap:5px;margin:12px 0} .mode button{flex:1;border:1px solid transparent;background:#ffffff09;color:#aebfb0;border-radius:6px;padding:7px 2px;font-size:11px} .mode button[aria-pressed=true]{background:#c6efb0;color:#17251a}
 .hint{font-size:10px;color:#94a996;margin:5px 0 10px}.range{display:flex;align-items:center;gap:9px;margin-top:4px}.range input{width:100%;accent-color:#c6efb0}.range output{font-variant-numeric:tabular-nums;width:30px;color:#c3d9c0}
 .actions{display:flex;gap:7px;margin-top:14px}.actions button{padding:10px;border-radius:7px;border:1px solid #8ea88c42;background:#ffffff07;color:#dbe9d9;font-size:12px}.actions .primary{flex:1;background:#c6efb0;color:#15241a;border-color:#c6efb0;font-weight:600}
 .status{min-height:36px;padding-top:10px;font-size:11px;color:#afc5af}.status.error{color:#ffb7a8}.status.busy{color:#d7ebbb}
 canvas{width:100%;height:50px;display:block;margin-top:6px;border-bottom:1px solid #a7b59f24}.clock{display:flex;justify-content:space-between;font:10px/1.5 ui-monospace,monospace;color:#9eb29d;margin-top:4px;min-height:16px}
 .downloads{display:flex;gap:7px;margin-top:10px}.downloads button{flex:1;border:1px solid #8ea88c42;border-radius:6px;background:transparent;color:#bdcfb9;padding:7px;font-size:10px}
 details{border-top:1px solid #a7b59f24;margin-top:12px;padding-top:9px;color:#9aaf9a;font-size:11px} summary{cursor:pointer} details p{font-size:11px;margin:8px 0} .warning{color:#e6d4a0;font-size:10px;margin-top:8px}
 @media(max-width:500px){:host{left:10px;bottom:10px;max-width:calc(100vw - 20px)}.panel{max-width:calc(100vw - 20px);max-height:calc(100dvh - 80px);padding:15px}}
`;

function download(bytes, type, name) {
  const url = URL.createObjectURL(new Blob([bytes], {type}));
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

export function mountVoicePanel(adapter = {}) {
  const pageId = adapter.pageId ?? 'jelly', actorIds = adapter.actors ?? Object.keys(CAST);
  const host = document.createElement('jelly-voice-panel');
  host.dataset.page = pageId;
  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `<style>${CSS}</style>
    <section class="panel" hidden aria-label="Jelly voice">
      <header><div><div class="eyebrow">Jelly Cast / physical voice</div><h2>Give the body a voice.</h2></div><button class="close" aria-label="Close voice panel">×</button></header>
      <label>Character<select id="actor"></select></label>
      <div class="mode" role="group" aria-label="Delivery">${[['speech','Speak'],['joke','Joke'],['sing','Sing'],['rap','Rap']].map(([value,label]) => `<button data-mode="${value}" aria-pressed="${value==='speech'}">${label}</button>`).join('')}</div>
      <label id="text-label">Words<textarea id="words" maxlength="240" spellcheck="true"></textarea></label>
      <div id="text-hint" class="hint">A short English phrase. Each character keeps the same voice across bodies.</div>
      <div class="row"><label id="rate-label">Pace<input id="rate" type="number" min="0.7" max="1.5" step="0.05" value="1"></label><label id="tempo-label" hidden>Tempo / BPM<input id="bpm" type="number" min="50" max="180" step="1" value="96"></label><label id="pause-label" hidden>Punchline pause / s<input id="pause" type="number" min="0.1" max="2.5" step="0.05" value="0.55"></label><label id="feel-label" hidden>Feel<select id="feel"><option value="straight">Straight eighths</option><option value="swing">Swing</option><option value="triplet">Triplets</option></select></label></div>
      <label id="melody-label" hidden>Melody / semitones : beats<input id="melody" type="text" value="0:1 2:1 4:1 7:1 4:1 2:1 0:2"><div class="hint">Relative to this voice. The pattern repeats, one note per syllable.</div></label>
      <label>Body colour<div class="range"><input id="material" type="range" min="0" max="1" step="0.05" value="0.2"><output id="material-value">20%</output></div></label>
      <div class="hint">Capture this body’s energy and pressure when preparing the take.</div>
      <div class="actions"><button class="primary" id="prepare">Prepare & play</button><button id="replay" disabled>Replay</button><button id="stop">Stop</button></div>
      <div id="status" class="status" role="status" aria-live="polite">Ready. First take loads the voice and pronunciation dictionary.</div>
      <canvas width="640" height="100" aria-label="Prepared voice waveform"></canvas><div class="clock"><span id="time">0.00 s</span><span id="phone"></span></div>
      <div class="downloads"><button id="wav" disabled>Save vocal WAV</button><button id="score" disabled>Save take record</button></div>
      <div id="warnings" class="warning"></div>
      <details><summary>About this take</summary><p>Chimera’s physical vocal tract makes the words and notes. Body colour changes a bounded source setting; the body then follows the prepared voice. These are editable physical presets, with no trained voice model.</p><p>WAV is the dry vocal from the last prepared take. Existing page music and effects are separate. Phone marks come from the engine’s plan, not measured lip sync. Listen before treating a take as finished.</p><p id="provenance"></p></details>
    </section><button class="toggle" aria-expanded="false"><span class="dot"></span>Voice</button>`;
  document.body.append(host);
  const $ = selector => root.querySelector(selector);
  for (const id of actorIds) { if (!CAST[id]) continue; const option = document.createElement('option'); option.value = id; option.textContent = `${CAST[id].name} / ${id}`; $('#actor').append(option); }
  $('#actor').value = actorIds.includes(adapter.defaultActorId) ? adapter.defaultActorId : actorIds[0];
  const renderer = new VoiceRenderer();
  let context, ownsContext = false, player, take, mode = 'speech', generation = 0, busy = false, disposed = false, playing = false, visualError = false;
  const lastText = {...DEFAULTS};
  $('#words').value = lastText.speech;
  const setStatus = (text, state = '') => { $('#status').textContent = text; $('#status').className = `status ${state}`; };
  const draw = frame => {
    const canvas = $('canvas'), pen = canvas.getContext('2d');
    pen.clearRect(0,0,canvas.width,canvas.height);
    if (take) {
      const values = take.envelope.values;
      pen.strokeStyle = '#7eae83'; pen.lineWidth = 1.5; pen.beginPath();
      for (let x = 0; x < canvas.width; x += 2) {
        const i = Math.min(values.length - 1, Math.floor(x / canvas.width * values.length));
        const h = Math.min(47, values[i] * 300); pen.moveTo(x, 50 - h); pen.lineTo(x, 50 + h);
      }
      pen.stroke();
      if (frame) { const x = Math.min(canvas.width, frame.t / take.duration * canvas.width); pen.strokeStyle='#e2f4cb';pen.beginPath();pen.moveTo(x,0);pen.lineTo(x,100);pen.stroke(); }
    }
    if (frame) { $('#time').textContent = `${frame.t.toFixed(2)} / ${frame.duration.toFixed(2)} s`; $('#phone').textContent = frame.phone ? `planned /${frame.phone}/` : ''; }
  };
  const deliverFrame = frame => {
    draw(frame);
    if (!visualError) {
      try { adapter.applyFrame?.(frame); } catch (error) { visualError = true; setStatus(`Voice plays; body response failed: ${error.message}`, 'error'); }
    }
  };
  const ensureAudio = async () => {
    if (!context) {
      if (adapter.getAudioContext) context = await adapter.getAudioContext();
      if (!context) { const Audio = window.AudioContext || window.webkitAudioContext; if (!Audio) throw new Error('This browser does not support Web Audio.'); context = new Audio(); ownsContext = true; }
      player = new TakePlayer(context, adapter.getDestination?.(context), {onFrame: deliverFrame, onEnd: () => {playing = false; adapter.onStop?.(); if (!visualError) setStatus('Take finished. Replay it or save the vocal.');}});
    }
    await context.resume();
    if (context.state !== 'running') throw new Error('Audio is suspended. Tap Prepare & play again.');
  };
  const refreshButtons = () => { $('#prepare').disabled = busy; $('#replay').disabled = busy || !take; $('#wav').disabled = !take; $('#score').disabled = !take; };
  const stop = (message = true) => {
    ++generation; renderer.cancel(); player?.stop(); busy = false; playing = false;
    try { adapter.onStop?.(); } catch {}
    refreshButtons(); if (message) setStatus(take ? 'Stopped. The last prepared take is saved for replay.' : 'Stopped.');
  };
  const prepare = async () => {
    stop(false); const token = generation; visualError = false;
    try {
      let features = {}; try { features = adapter.readFeatures?.() ?? {}; } catch { setStatus('Body snapshot unavailable; preparing with neutral body colour.'); }
      const score = createScore({actorId: $('#actor').value, text: $('#words').value, mode, bpm: $('#bpm').value, rate: $('#rate').value, pause: $('#pause').value, feel: $('#feel').value, melody: $('#melody').value, material: $('#material').value}, features);
      busy = true; refreshButtons(); setStatus('Opening audio…', 'busy');
      await ensureAudio();
      if (disposed || token !== generation) return;
      const result = await renderer.render(score, {sampleRate: context.sampleRate === 44100 ? 44100 : 48000, onStatus: status => setStatus(status === 'loading' ? 'Loading the physical voice…' : 'Preparing the whole take. Stop cancels.', 'busy')});
      if (disposed || token !== generation) return;
      take = result; busy = false; refreshButtons();
      $('#warnings').textContent = take.warnings.join(' ');
      $('#provenance').textContent = `${CAST[take.score.actorId].name} · ${take.score.mode} · ${take.sampleRate} Hz · take ${take.pcmHash.slice(0,12)}`;
      player.play(take); playing = true; setStatus(`Playing ${take.duration.toFixed(1)} s. This exact take can be replayed or saved.`);
    } catch (error) {
      if (token !== generation || error.name === 'AbortError') return;
      busy = false; refreshButtons(); setStatus(error.message || String(error), 'error');
    }
  };
  $('#prepare').onclick = prepare;
  $('#stop').onclick = () => stop();
  $('#replay').onclick = async () => { stop(false); const token = generation; try { await ensureAudio(); if (token !== generation || !take) return; visualError = false; player.play(take); playing = true; setStatus('Replaying the saved take.'); } catch (error) { setStatus(error.message, 'error'); } };
  $('#wav').onclick = () => { if (take) download(encodeWav(take), 'audio/wav', `jelly-${take.score.actorId}-${take.score.mode}-${take.pcmHash.slice(0,8)}.wav`); };
  $('#score').onclick = () => {
    if (!take) return;
    const {pcm, envelope, ...record} = take;
    download(JSON.stringify({...record, pageId, bodyPerformance: {clock: 'AudioContext', envelope: 'RMS / 10 ms', physicsReplay: 'not-captured'}, pcmEncoding: 'Float32 mono, hashed before 16-bit WAV encoding'}, null, 2), 'application/json', `jelly-take-${take.pcmHash.slice(0,8)}.json`);
  };
  $('#material').oninput = () => { $('#material-value').textContent = `${Math.round(Number($('#material').value)*100)}%`; };
  root.querySelectorAll('[data-mode]').forEach(button => { button.onclick = () => {
    lastText[mode] = $('#words').value; mode = button.dataset.mode; $('#words').value = lastText[mode];
    root.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    $('#rate-label').hidden = mode === 'sing' || mode === 'rap'; $('#tempo-label').hidden = mode !== 'sing' && mode !== 'rap';
    $('#pause-label').hidden = mode !== 'joke'; $('#feel-label').hidden = mode !== 'rap'; $('#melody-label').hidden = mode !== 'sing';
    $('#text-hint').textContent = mode === 'joke' ? 'The | marks the pause before the punchline.' : mode === 'sing' ? 'One note per syllable. Edit the melody below.' : mode === 'rap' ? 'Syllable vowels follow the beat. Punctuation does not add rests.' : 'A short English phrase. Each character keeps the same voice across bodies.';
  }; });
  const toggle = () => { const open = $('.panel').hidden; $('.panel').hidden = !open; $('.toggle').setAttribute('aria-expanded', String(open)); };
  $('.toggle').onclick = toggle; $('.close').onclick = toggle;
  for (const event of ['keydown', 'keyup', 'pointerdown', 'pointerup', 'click', 'wheel']) host.addEventListener(event, e => e.stopPropagation());
  const controller = {
    stop, prepare, host,
    getState: () => ({pageId, busy, playing, contextState: context?.state, take: take ? {score: take.score, duration: take.duration, pcmHash: take.pcmHash, signal: take.signal} : null}),
    getTake: () => take ? structuredClone(take) : null,
    frameAt: time => take ? frameAt(take, time) : null,
    dispose() { stop(false); disposed = true; if (ownsContext) context?.close(); host.remove(); delete window.JELLY_VOICES?.[pageId]; },
  };
  window.JELLY_VOICES ??= {}; window.JELLY_VOICES[pageId] = controller;
  draw(); return controller;
}
