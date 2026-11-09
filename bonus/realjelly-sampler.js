const LABELS = ['Roar', 'Answer', 'Breath', 'Dub', 'Kick', 'Snare', 'Sub', 'Water'];
const SLOT_SECONDS = 0.9;

export function makeJellySampler(panel, context, destination, fire, isAudible) {
  const pads = panel.querySelector('[data-pads]');
  const status = panel.querySelector('output');
  const file = panel.querySelector('input[type=file]');
  const drift = panel.querySelector('[data-drift]');
  const buttons = [];
  const voices = new Set();
  let enabled = false, bank, builtIn, loading, revision = 0;
  const show = message => { status.textContent = message; };

  function useBank(next) {
    bank = next;
    buttons.forEach((button, i) => {
      button.textContent = `${i + 1} ${next.names[i]}`;
    });
  }

  async function loadBuiltIn() {
    if (builtIn) return builtIn;
    if (!loading) loading = (async () => {
      const response = await fetch(new URL('./realjelly-bank.mp3', import.meta.url));
      if (!response.ok) throw new Error('Sample bank unavailable');
      const buffer = await context().decodeAudioData(await response.arrayBuffer());
      builtIn = {buffer, names: LABELS, span: SLOT_SECONDS};
      return builtIn;
    })().finally(() => { loading = null; });
    return loading;
  }

  async function reset() {
    const token = ++revision;
    show('Loading Treblo bank…');
    try {
      const next = await loadBuiltIn();
      if (token === revision) {
        useBank(next);
        show('Treblo bank · tap a rim node or play 1–8');
      }
    } catch {
      if (token === revision) show('Bank unavailable · try loading a local audio file');
    }
  }

  function stop() {
    for (const voice of voices) {
      if (!voice.stopping) {
        voice.stopping = true;
        const now = context().currentTime;
        voice.gain.gain.cancelScheduledValues(now);
        voice.gain.gain.setTargetAtTime(0, now, .004);
        voice.source.stop(now + .025);
      }
    }
  }

  function play(index, pan, strength = 1, rate = 1) {
    if (!enabled || !bank || !isAudible() || index < 0 || index >= LABELS.length) return;
    const ac = context();
    const source = ac.createBufferSource(), gain = ac.createGain(), stereo = ac.createStereoPanner();
    const now = ac.currentTime, start = index * bank.span;
    const duration = Math.min(bank.span, 2.5, bank.buffer.duration - start);
    if (duration <= 0) return;
    const speed = Math.max(.75, Math.min(1.25, rate));
    const end = now + duration / speed, fade = Math.min(.065, duration / speed / 3);
    source.buffer = bank.buffer;
    source.playbackRate.value = speed;
    stereo.pan.value = Math.max(-1, Math.min(1, pan));
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(.48 * strength, now + fade / 3);
    gain.gain.setValueAtTime(.48 * strength, end - fade);
    gain.gain.linearRampToValueAtTime(0, end);
    source.connect(gain).connect(stereo).connect(destination());
    const voice = {source, gain};
    if (voices.size >= 12) {
      const oldest = voices.values().next().value;
      oldest.source.stop();
      voices.delete(oldest);
    }
    voices.add(voice);
    source.onended = () => { voices.delete(voice); source.disconnect(); gain.disconnect(); stereo.disconnect(); };
    source.start(now, start, duration);
    const button = buttons[index];
    button.classList.add('on');
    clearTimeout(button.flash);
    button.flash = setTimeout(() => button.classList.remove('on'), 180);
    show(`${index + 1} · ${bank.names[index]}`);
  }

  LABELS.forEach((label, i) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${i + 1} ${label}`;
    button.addEventListener('click', () => fire(i));
    pads.append(button);
    buttons.push(button);
  });
  drift.addEventListener('click', () => {
    const on = drift.getAttribute('aria-pressed') !== 'true';
    drift.setAttribute('aria-pressed', on);
    drift.classList.toggle('on', on);
  });
  panel.querySelector('[data-reset]').addEventListener('click', reset);
  file.addEventListener('change', async () => {
    const selected = file.files[0];
    file.value = '';
    if (!selected) return;
    if (selected.size > 25 * 1024 * 1024) { show('Choose an audio file under 25 MB'); return; }
    const token = ++revision;
    show('Slicing audio locally…');
    try {
      const buffer = await context().decodeAudioData(await selected.arrayBuffer());
      if (buffer.duration < .12) throw new Error('Audio too short');
      if (token === revision) {
        useBank({buffer, span: buffer.duration / LABELS.length, names: LABELS.map((_, i) => `Slice ${i + 1}`)});
        show(`${selected.name} · eight slices · stored in this tab`);
      }
    } catch {
      if (token === revision) show('Could not decode that file · the current bank is available');
    }
  });

  return {
    get active() { return enabled; },
    get drifting() { return drift.getAttribute('aria-pressed') === 'true'; },
    setEnabled(on) {
      enabled = on;
      panel.hidden = !on;
      if (!on) stop();
      else if (!bank) reset();
    },
    play, stop,
  };
}
