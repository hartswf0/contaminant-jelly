// Headless tests of the Colloquy state machine (node). Writes tests/colloquy/report-sim.json.
import {makeColloquy, regime, DEFAULTS} from '../../bonus/colloquy/sim.js';
import {writeFileSync} from 'node:fs';
const results = []; let failed = 0;
function test(name, fn) { let ok = false, detail; try { detail = fn(); ok = true; } catch (e) { detail = String(e.message || e); } if (!ok) failed++; results.push({name, ok, detail}); console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail ? '  ' + JSON.stringify(detail) : '')); }
const assert = (c, m) => { if (!c) throw new Error(m); };
const record = c => { const ev = []; c.on(e => ev.push(e)); return ev; };
const runUntil = (c, pred, max = 600) => { const dt = 1 / 60; for (let i = 0; i < max * 60; i++) { c.step(dt); if (pred()) return true; } return false; };
const {Lmin, Lmax} = DEFAULTS;

test('regime classification matches the drive table', () => {
  const cases = [[.1, .1, 'satisfied'], [.9, .95, 'dual'], [.9, .1, 'O'], [.1, .9, 'P'], [.6, .5, 'O'], [.4, .7, 'P'], [.5, .2, 'O'], [.2, .45, 'P']];
  for (const [O, P, want] of cases) assert(regime(O, P, Lmin, Lmax) === want, `${O},${P} → ${regime(O, P, Lmin, Lmax)} ≠ ${want}`);
  return {cases: cases.length};
});

test('a full 7-stage handshake completes in order; F = 1 decrements the drive by ω', () => {
  const c = makeColloquy({seed: 7}), ev = record(c);
  assert(runUntil(c, () => ev.some(e => e.kind === 'memory'), 300), 'no closure in 300 s');
  const mem = ev.find(e => e.kind === 'memory'), rf = ev.find(e => e.kind === 'reinforce' && e.f === mem.f);
  c.run(4);
  for (const who of [rf.m, mem.f]) {
    const st = [1, ...ev.filter(e => e.kind === 'stage' && e.who === who && e.t <= mem.t + 3).map(e => e.stage)];
    const last1 = st.lastIndexOf(1, st.indexOf(7)); const seq = st.slice(last1, st.indexOf(7, last1) + 2);
    assert(JSON.stringify(seq) === '[1,2,3,4,5,6,7,1]', who + ' sequence ' + JSON.stringify(seq));
  }
  assert(Math.abs((rf.before - rf.after) - DEFAULTS.omega) < 1e-3 || rf.after === 0, 'drop ' + (rf.before - rf.after));
  return {male: rf.m, female: mem.f, desire: rf.desire, vane: rf.vane, before: rf.before, after: rf.after, t: +rf.t.toFixed(2)};
});

test('an unreinforced τ aborts and scanning resumes', () => {
  const c = makeColloquy({seed: 7, close: 1e9}), ev = record(c);   // the reflection can never register
  assert(runUntil(c, () => ev.some(e => e.kind === 'abort' && /timeout τ/.test(e.why)), 300), 'no τ abort');
  const ab = ev.find(e => e.kind === 'abort' && /timeout τ/.test(e.why)), sw = ev.filter(e => e.kind === 'stage' && e.who === ab.f && e.stage === 5 && e.t <= ab.t).pop();
  assert(Math.abs((ab.t - sw.t) - DEFAULTS.tau) < .1, 'abort at ' + (ab.t - sw.t));
  assert(runUntil(c, () => ev.some(e => e.kind === 'stage' && e.stage === 2 && e.t > ab.t), 120), 'never re-contacted');
  return {f: ab.f, m: ab.m, window: +(ab.t - sw.t).toFixed(2), handshakes: c.S.handshakes};
});

test('memory: after an UP reinforcement the next encounter with that male sweeps UP first', () => {
  const c = makeColloquy({seed: 7}), ev = record(c); c.run(1800);
  let checked = 0;
  for (const m of ev.filter(e => e.kind === 'memory')) {
    const next = ev.find(e => e.kind === 'sweep' && e.t > m.t && e.f === m.f && e.m === m.m && (e.desire === 'O' ? 'MA' : 'MB') === m.reg);
    if (!next) continue; checked++;
    // the most recent write before that sweep governs it
    const lastW = ev.filter(e => e.kind === 'memory' && e.f === m.f && e.m === m.m && e.reg === m.reg && e.t < next.t).pop();
    assert(next.mode === 'memory' && next.first === lastW.val, `${m.f}/${m.m}: wrote ${lastW.val}, swept ${next.first}`);
  }
  const ups = ev.filter(e => e.kind === 'memory' && e.val === 'UP').length;
  assert(checked > 10 && ups > 3, 'too few re-encounters ' + checked);
  return {reencounters: checked, upWrites: ups};
});

test('memory adapts when a male has inverted preferences', () => {
  const c = makeColloquy({seed: 7}), ev = record(c); c.run(400); c.S.males[0].inverted = true; const t0 = c.S.t; c.run(900);
  const ad = ev.filter(e => e.kind === 'adapt' && e.t > t0).length, rf = ev.filter(e => e.kind === 'reinforce' && e.m === 'G' && e.t > t0).length;
  assert(ad > 0 && rf > 0, `adapt ${ad} reinforce ${rf}`); return {adaptations: ad, reinforcementsAfterInversion: rf};
});

test('majority arbitration resolves contention over bar Z', () => {
  const c = makeColloquy({seed: 7}), ev = record(c); let still = 0, moved = 0, last = c.S.z;
  for (let i = 0; i < 600 * 60; i++) { c.step(1 / 60); if (c.S.zHalt) { if (c.S.z !== last) moved++; else still++; } last = c.S.z; }
  const cont = ev.filter(e => e.kind === 'contention');
  assert(cont.length > 5, 'few contentions'); for (const e of cont) assert(e.halt === (e.wHalt >= e.wTurn), 'bad verdict ' + JSON.stringify(e));
  assert(moved === 0 && still > 0, 'Z moved while halted');
  return {contentions: cont.length, haltWins: cont.filter(e => e.halt).length, turnWins: cont.filter(e => !e.halt).length};
});

test('raising the ambient light gives fewer handshakes per minute', () => {
  const rate = amb => { let n = 0; for (const seed of [3, 7, 11]) { const c = makeColloquy({seed, ambient: amb}); c.run(900); n += c.S.handshakes; } return +(n / 45).toFixed(2); };
  const dark = rate(0), dim = rate(.35), lit = rate(.8);
  assert(dark > dim && dim > lit, `dark ${dark} dim ${dim} lit ${lit}`); return {perMinute: {dark, dim, lit}};
});

test('visitor · prosthetic male (torch) engages a female', () => {
  const c = makeColloquy({seed: 7}), ev = record(c); c.run(30); const f = c.S.females[1]; f.O = .7; f.P = .1;
  runUntil(c, () => f.stage === 1, 30); c.visitor.torch(1, 'O', 8); c.run(5);
  const st = ev.filter(e => e.kind === 'stage' && e.who === 'F2' && /torch/.test(e.why));
  assert(st.length >= 2 && ev.some(e => e.kind === 'sweep' && e.f === 'F2' && e.m === 'V'), 'no torch engagement');
  return {stages: st.map(e => e.stage)};
});

test('visitor · prosthetic female (hand mirror) reinforces a committed male', () => {
  const c = makeColloquy({seed: 7, mirrorSpeed: .02}), ev = record(c);   // her own servo is too slow: only the visitor can close the loop
  assert(runUntil(c, () => c.S.males.some(m => m.stage === 5), 300), 'no committed male');
  const mi = c.S.males.findIndex(m => m.stage === 5), m = c.S.males[mi], dir = (m.desire === 'O') !== m.inverted ? 'UP' : 'DOWN';
  c.visitor.mirror(mi, dir, 3); c.run(2);
  const rf = ev.find(e => e.kind === 'reinforce' && e.how === 'visitor mirror'); assert(rf, 'no visitor reinforcement');
  return {m: rf.m, vane: rf.vane, before: rf.before, after: rf.after};
});

test('visitor · occlusion breaks the beam and aborts', () => {
  const c = makeColloquy({seed: 7, mirrorSpeed: .05}), ev = record(c);
  assert(runUntil(c, () => c.S.males.some(m => m.stage === 5), 300), 'no committed male');
  const m = c.S.males.find(m => m.stage === 5), f = c.S.females[m.partner], a = c.malePos(m), b = c.femalePos(f);
  c.visitor.stand((a.x + b.x) / 2, (a.z + b.z) / 2, .3); c.run(1.5); c.visitor.leave();
  const ab = ev.find(e => e.kind === 'abort' && e.why === 'occluded by visitor'); assert(ab, 'no occlusion abort'); return {m: ab.m, f: ab.f};
});

test('visitor · higher-order composition changes bar Z and the tempo of desire', () => {
  const zRate = bias => { const c = makeColloquy({seed: 7}); c.visitor.conduct({zBias: bias}); let s = 0, n = 0, last = c.S.z; for (let i = 0; i < 60 * 60; i++) { c.step(1 / 60); if (!c.S.zHalt) { let d = c.S.z - last; if (d < -Math.PI) d += 2 * Math.PI; s += d; n++; } last = c.S.z; } return s / n * 60; };
  const slow = zRate(-.5), fast = zRate(.8);
  const hs = tempo => { const c = makeColloquy({seed: 7}); c.visitor.conduct({tempo}); c.run(900); return c.S.handshakes; };
  const calm = hs(.5), urgent = hs(2);
  assert(fast > slow * 2 && urgent > calm, `z ${slow}/${fast} hs ${calm}/${urgent}`);
  return {zRadPerS: {slow: +slow.toFixed(3), fast: +fast.toFixed(3)}, handshakes15min: {calm, urgent}};
});

test('30-minute exhibition: no stuck states, every agent satisfied', () => {
  const out = [];
  for (const seed of [7, 19, 42]) {
    const c = makeColloquy({seed}), ev = record(c); let maxHold = 0;
    for (let i = 0; i < 1800 * 60; i++) { c.step(1 / 60); if (i % 30 === 0) for (const a of [...c.S.males, ...c.S.females]) if (a.stage !== 1) maxHold = Math.max(maxHold, c.S.t - a.since); }
    const sat = [...c.S.males, ...c.S.females].map(a => a.sat);
    assert(c.S.stuck === 0, 'watchdog fired ' + c.S.stuck); assert(sat.every(s => s > 0), 'unsatisfied ' + sat);
    assert(maxHold < DEFAULTS.tau * 3, 'long hold ' + maxHold);
    for (const a of [...c.S.males, ...c.S.females]) for (const k of ['O', 'P']) assert(isFinite(a[k]) && a[k] >= 0 && a[k] <= DEFAULTS.Lcap, 'drive out of range');
    out.push({seed, handshakes: c.S.handshakes, perMin: +(c.S.handshakes / 30).toFixed(2), aborts: c.S.aborts, contentions: c.S.contentions, satisfied: sat, maxHoldS: +maxHold.toFixed(2)});
  }
  return out;
});

test('deterministic for a seed', () => {
  const a = makeColloquy({seed: 5}), b = makeColloquy({seed: 5}); a.run(300); b.run(300);
  assert(JSON.stringify(a.snapshot()) === JSON.stringify(b.snapshot()), 'diverged'); return {t: 300};
});

writeFileSync(new URL('./report-sim.json', import.meta.url), JSON.stringify({suite: 'colloquy sim', when: new Date().toISOString(), passed: results.length - failed, failed, results}, null, 1));
console.log(`\n${results.length - failed}/${results.length} passed`); process.exit(failed ? 1 : 0);
