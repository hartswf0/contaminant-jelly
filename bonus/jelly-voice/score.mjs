import {resolveActor} from './cast.mjs';

export const SCORE_VERSION = 'jelly-cast-score/1';
export const RENDERER_REVISION = 'chimera-e33221d-jelly-take-1';
export const LIMITS = Object.freeze({text: 240, syllables: 32, seconds: 40});
const modes = new Set(['speech', 'joke', 'sing', 'rap']);
const feels = new Set(['straight', 'swing', 'triplet']);
function number(value, fallback, min, max, label) {
  const n = value === undefined ? fallback : Number(value);
  if (!Number.isFinite(n) || n < min || n > max) throw new Error(`${label} must be ${min}–${max}.`);
  return n;
}
export function freeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
export function createScore(input, features = {}) {
  const actor = resolveActor(input.actorId ?? 'G');
  const text = String(input.text ?? '').trim();
  if (!/[a-z]/i.test(text)) throw new Error('Enter an English phrase.');
  if (text.length > LIMITS.text) throw new Error(`Keep a take to ${LIMITS.text} characters or fewer.`);
  const mode = input.mode ?? 'speech', feel = input.feel ?? 'straight';
  if (!modes.has(mode)) throw new Error('Choose speech, joke, sing, or rap.');
  if (!feels.has(feel)) throw new Error('Choose straight, swing, or triplet feel.');
  if (mode === 'joke' && (text.split('|').length !== 2 || text.split('|').some(s => !/[a-z]/i.test(s)))) {
    throw new Error('Place one | between the joke setup and punchline.');
  }
  const melody = String(input.melody ?? '0:1 2:1 4:1 7:1 4:1 2:1 0:2').trim();
  const notes = melody.split(/\s+/).filter(Boolean).map(token => {
    const m = /^(-?\d+)(?::(\d+(?:\.\d+)?))?$/.exec(token);
    if (!m) throw new Error('Melody uses semitone:beats pairs, for example 0:1 4:1 7:2.');
    return {semitones: number(m[1], 0, -12, 19, 'Melody interval'), beats: number(m[2], 1, .25, 4, 'Note beats')};
  });
  if (!notes.length || notes.length > 32) throw new Error('Supply 1–32 melody notes.');
  const captured = {};
  for (const name of ['energy', 'pressure', 'color']) {
    const n = Number(features[name] ?? 0);
    captured[name] = Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : 0;
  }
  return freeze({
    schema: SCORE_VERSION, renderer_revision: RENDERER_REVISION,
    actorId: actor.actorId, voice_profile_id: actor.voice_profile_id,
    voice_profile_revision: actor.voice_profile_revision,
    text, mode, feel, notes,
    bpm: number(input.bpm, 96, 50, 180, 'Tempo'),
    rate: number(input.rate, 1, .7, 1.5, 'Speaking rate'),
    pause: number(input.pause, .55, .1, 2.5, 'Punchline pause'),
    vibrato: number(input.vibrato, 22, 0, 60, 'Vibrato cents'),
    material: number(input.material, .2, 0, 1, 'Material amount'),
    captured_body: captured,
  });
}

export async function sha256(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join('');
}
export function scoreKey(score) { return sha256(new TextEncoder().encode(JSON.stringify(score))); }

export function compileScore(runtime, score) {
  if (score.schema !== SCORE_VERSION) throw new Error('Unsupported score version.');
  const actor = resolveActor(score.actorId);
  if (score.voice_profile_id !== actor.voice_profile_id || score.voice_profile_revision !== actor.voice_profile_revision) throw new Error('This score needs a different voice profile revision.');
  const body = {...actor.body};
  // Explicit creative mapping: a snapshot colours the source, never replaces articulation.
  const m = score.material, f = score.captured_body;
  const f0 = actor.f0 * 2 ** (m * f.energy * 2 / 12);
  const source = {...actor.source, f0, breathiness: Math.min(.4, actor.source.breathiness + m * f.pressure * .12), brightness: Math.min(.8, actor.source.brightness + m * f.color * .15)};
  let plan, notes = [], warnings = [], preroll = 0;
  const speechOptions = {body, t0: .2, f0, rate: score.rate};
  if (score.mode === 'joke') {
    const [setup, punch] = score.text.split('|').map(s => runtime.phrases(s.trim()));
    if (!setup.length || !punch.length) throw new Error('The joke needs pronounceable words on both sides of |.');
    setup[setup.length - 1].pause = score.pause;
    plan = runtime.planPhrases([...setup, ...punch], speechOptions);
  } else if (score.mode === 'speech') {
    plan = runtime.planSpeech(score.text, speechOptions);
  } else {
    const syllables = runtime.syllables(score.text);
    // A rap bar is one continuous breath here. Prose punctuation must not
    // launch overlapping phrase preparations between adjacent beat slots.
    if (score.mode === 'rap') syllables.forEach((s, i) => {s.phraseEnd = i === syllables.length - 1;});
    if (!syllables.length) throw new Error('The lyrics contain no pronounceable syllables.');
    if (syllables.length > LIMITS.syllables) throw new Error(`This take has ${syllables.length} syllables; use ${LIMITS.syllables} or fewer.`);
    const root = Math.round(69 + 12 * Math.log2(f0 / 440));
    let beat = 0;
    notes = syllables.map((syl, i) => {
      const n = score.notes[i % score.notes.length];
      const beats = score.mode === 'sing' ? n.beats : score.feel === 'triplet' ? 1 / 3 : score.feel === 'swing' ? (i % 2 === 0 ? 2 / 3 : 1 / 3) : .5;
      const midi = root + (score.mode === 'sing' ? n.semitones : (syl.nucleus.stress ? 1 : -1));
      const item = {syl, midi, beats, beat};
      beat += beats;
      return item;
    });
    if (notes.some(n => n.beats * 60 / score.bpm < .18)) warnings.push('Short syllable slots can compress consonants. Slow the tempo if words blur.');
    plan = runtime.planSong(notes.map(({syl, midi, beats}) => ({syl, midi, beats})), {body, bpm: score.bpm, t0: .3, vibrato: score.mode === 'sing' ? score.vibrato : 0});
    const counts = ipa => runtime.call('plannedCounts', {ipa}).reduce((sum, n) => sum + n, 0);
    let segmentIndex = 0;
    for (let i = 0; i < notes.length; i++) {
      const note = notes[i];
      const nextMelisma = !note.syl.phraseEnd && i + 1 < notes.length && notes[i + 1].syl.melisma === true;
      let chainStart = i;
      while (chainStart > 0 && notes[chainStart].syl.melisma === true) chainStart--;
      segmentIndex += note.syl.melisma ? 0 : counts(note.syl.onset.map(s => s.ipa));
      note.targetNucleusTime = .3 + note.beat * 60 / score.bpm;
      note.plannedNucleusTime = plan.segments[segmentIndex]?.t0;
      if (!Number.isFinite(note.plannedNucleusTime)) throw new Error('The song plan could not be matched to its syllable score.');
      note.plannerErrorSeconds = note.plannedNucleusTime - note.targetNucleusTime;
      // Match upstream singing: a continued diphthong holds its first vowel;
      // the original word's coda waits until the final note of the chain.
      segmentIndex += (nextMelisma ? 1 : counts([note.syl.nucleus.ipa])) + (nextMelisma ? 0 : counts(notes[chainStart].syl.coda.map(s => s.ipa)));
    }
    const maxError = Math.max(...notes.map(n => Math.abs(n.plannerErrorSeconds)));
    if (maxError > .02) warnings.push(`The plan moves a vowel up to ${Math.round(maxError * 1000)} ms off its beat. Slow the tempo or simplify that syllable.`);
  }
  const earliest = Math.min(0, ...plan.gestures.map(g => g.t0 - g.rampIn), ...plan.segments.map(s => s.t0));
  if (earliest < 0) {
    preroll = -earliest + .02;
    plan.gestures.forEach(g => {g.t0 += preroll; g.t1 += preroll;});
    plan.segments.forEach(s => {s.t0 += preroll; s.t1 += preroll;});
    plan.end += preroll;
    notes.forEach(n => {n.targetNucleusTime += preroll; n.plannedNucleusTime += preroll;});
  }
  if (!plan.segments.length || !Number.isFinite(plan.end)) throw new Error('The engine could not make a pronunciation plan.');
  for (let i = 1; i < plan.segments.length; i++) {
    if (plan.segments[i].t0 < plan.segments[i - 1].t1 - 1e-6) throw new Error('This score overlaps two phonemes. Slow the tempo or give the notes more beats.');
  }
  if (plan.end > LIMITS.seconds) throw new Error(`The planned take is ${plan.end.toFixed(1)} seconds; keep it under ${LIMITS.seconds}.`);
  return {plan, body, source, preroll, notes: notes.map(({syl, ...n}) => ({syllable: syl.text, ...n})), warnings};
}
