// Independent executable audit of actual Jelly Cast planner/take metadata.
// Run from any directory: node tests/jelly-voice/critic-timing.mjs
// No listening-quality claims are made. A rejected score is distinguished from
// an accepted score with false metadata or a frame that misses an active phone.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {initChimera} from '../../bonus/jelly-voice/chimera/chimera.mjs';
import {createScore, compileScore} from '../../bonus/jelly-voice/score.mjs';
import {renderTake} from '../../bonus/jelly-voice/render.mjs';
import {frameAt} from '../../bonus/jelly-voice/performance.mjs';

const base = new URL('../../bonus/jelly-voice/', import.meta.url);
const hashFile = async name => createHash('sha256').update(await fs.readFile(new URL(name, base))).digest('hex');
const inspected = Object.fromEntries(await Promise.all(['score.mjs', 'render.mjs', 'performance.mjs', 'chimera/chimera.wasm'].map(async name => [name, await hashFile(name)])));
const runtime = await initChimera(await fs.readFile(new URL('chimera/chimera.wasm', base)));
await runtime.loadDictionary(await fs.readFile(new URL('chimera/cmudict.txt.gz', base)));
const results = [];
async function check(name, fn) {
  try { const evidence = await fn(); results.push({name, status: 'PASS', evidence}); }
  catch (error) { results.push({name, status: 'FAIL', error: error.message}); }
}
const fast = text => createScore({text, mode: 'sing', bpm: 180, melody: '0:0.25'});
const approximate = (actual, expected, label) => assert.ok(Math.abs(actual - expected) < 1e-9, `${label}: actual ${actual}, expected ${expected}`);

await check('actual rendered song note metadata is tied to actual nucleus starts', async () => {
  const take = await renderTake(runtime, fast('she sings'), 44100);
  const vowels = take.segments.filter(s => s.kind === 'vowel');
  assert.equal(vowels.length, 2);
  take.notes.forEach((n, i) => approximate(n.plannedNucleusTime, vowels[i].t0, n.syllable));
  assert.ok(take.signal.rms > 0 && Number.isFinite(take.signal.rms));
  return {notes: take.notes, vowels, pcmHash: take.pcmHash, sampleRate: take.sampleRate, frames: take.pcm.length, signal: take.signal};
});

await check('fast consonant-heavy timing distinguishes target from measured plan', () => {
  const compiled = compileScore(runtime, fast('strengths strengths strengths'));
  const vowels = compiled.plan.segments.filter(s => s.kind === 'vowel');
  compiled.notes.forEach((n, i) => approximate(n.plannedNucleusTime, vowels[i].t0, n.syllable));
  const drift = Math.max(...compiled.notes.map(n => Math.abs(n.plannedNucleusTime - n.targetNucleusTime)));
  assert.ok(drift > .04, `fixture expected >40 ms drift, got ${drift}`);
  assert.ok(compiled.warnings.some(w => /off its beat/.test(w)), 'missing explicit plan drift warning');
  return {maximumDriftSeconds: drift, notes: compiled.notes, warnings: compiled.warnings};
});

await check('triplet rap remains on its planned beat for consonant fixture', () => {
  const score = createScore({text: 'strengths strengths strengths', mode: 'rap', bpm: 180, feel: 'triplet'});
  const compiled = compileScore(runtime, score);
  const vowels = compiled.plan.segments.filter(s => s.kind === 'vowel');
  compiled.notes.forEach((n, i) => {
    approximate(n.plannedNucleusTime, vowels[i].t0, `nucleus ${i}`);
    approximate(n.targetNucleusTime, vowels[i].t0, `triplet beat ${i}`);
  });
  return {notes: compiled.notes};
});

await check('dynamic preroll preserves unusually long first onset', () => {
  const compiled = compileScore(runtime, fast('ssssssssssssssssssa'));
  const minimumRampStart = Math.min(...compiled.plan.gestures.map(g => g.t0 - g.rampIn));
  assert.ok(compiled.preroll > 1, `no sufficient preroll: ${compiled.preroll}`);
  assert.ok(minimumRampStart >= 0, `negative gesture ramp start: ${minimumRampStart}`);
  const vowel = compiled.plan.segments.find(s => s.kind === 'vowel');
  approximate(compiled.notes[0].plannedNucleusTime, vowel.t0, 'shifted nucleus');
  return {preroll: compiled.preroll, minimumRampStart, note: compiled.notes[0]};
});

for (const mode of ['sing', 'rap']) await check(`${mode} rejects a pronounceable-looking lyric with no vowels`, () => {
  assert.throws(() => compileScore(runtime, createScore({text: 'psst', mode})), /no pronounceable syllables/);
  return {text: 'psst'};
});

await check('over-duration song is rejected before rendering', () => {
  assert.throws(() => compileScore(runtime, createScore({text: 'la '.repeat(32), mode: 'sing', melody: '0:4', bpm: 50})), /keep it under 40/);
  return {syllables: 32, expectedBeats: 128, bpm: 50};
});

await check('accepted melisma metadata points to its nucleus, not the final nasal', () => {
  const compiled = compileScore(runtime, fast('home ~'));
  const actualNuclei = compiled.plan.segments.filter(s => s.ipa === 'o');
  assert.equal(actualNuclei.length, 2);
  approximate(compiled.notes[1].plannedNucleusTime, actualNuclei[1].t0, 'second nucleus in home ~');
  return {notes: compiled.notes, actualNuclei};
});

await check('accepted melisma does not corrupt the next word timing', () => {
  const compiled = compileScore(runtime, fast('my ~ go'));
  const actualGo = compiled.plan.segments.find(s => s.ipa === 'o');
  approximate(compiled.notes[2].plannedNucleusTime, actualGo.t0, 'go nucleus after melisma');
  return {notes: compiled.notes, actualGo};
});

await check('overlapping phrases are rejected or expose the actual active planned phone', async () => {
  let take;
  try { take = await renderTake(runtime, fast('a. a. shrieks.'), 44100); }
  catch (error) {
    assert.match(error.message, /overlaps two phonemes/, 'only an explicit overlap rejection satisfies this fixture');
    return {rejected: true, reason: error.message};
  }
  const time = .36;
  const active = take.segments.filter(s => s.t0 <= time && time < s.t1);
  assert.equal(active.length, 1, 'fixture must have exactly one active phone');
  const frame = frameAt(take, time);
  assert.equal(frame.phone, active[0].ipa, `frameAt(${time}) returned ${JSON.stringify(frame.phone)} but active plan phone is ${active[0].ipa} at ${active[0].t0}–${active[0].t1}; actual PCM hash ${take.pcmHash}`);
  return {sampleRate: take.sampleRate, pcmHash: take.pcmHash, active, frame};
});

const hashesUnchanged = (await hashFile('score.mjs')) === inspected['score.mjs'];
const failures = results.filter(r => r.status === 'FAIL').length;
console.log(JSON.stringify({audit: 'independent timing adversary', inspected, hashesUnchanged, results, counts: {pass: results.length - failures, fail: failures}, listeningQuality: 'UNKNOWN; no listening performed'}, null, 2));
process.exitCode = failures || !hashesUnchanged ? 1 : 0;
