// THE COLLOQUY OF MOBILES (Gordon Pask, 1968), as five asynchronous agents. Pure logic, no drawing: the page stages it with jellies.
//
// Mechanism after Pask (1971) "A Comment, a Case History and a Plan" (Figs. 34–39) and the Colloquy 2018 reconstruction (Pangaro & McLeish),
// as set out in the monograph "Gordon Pask's The Colloquy of Mobiles (1968): System Architecture and Operational Theory":
//   · topology: a truncated-triangle frame; bar Z turning 360° carries the two "male" mobiles G and J at opposite ends, each turning 180° on its
//     own axis; three "female" mobiles F1–F3 near the outer vertices, each turning across a bounded 90° arc between right/left limit switches.
//   · drives O (Orange) and P (Puce) in every agent: μ ← μ + δ over time, μ ← μ − ω on satisfaction; four regimes between L_min and L_max.
//   · the seven-stage handshake (Fig. 2): 1 scan with the flashing lamp u (frequency-coded: who, and which desire) · 2 optical contact on the
//     female's aperture a: she halts and decodes · 3 phase-locked tone + short-term registration · 4 energetic commitment: the male halts,
//     asks bar Z to halt, turns on the steady beam B, which costs him (his drive rises) · 5 the female sweeps her servo mirror b, guided by
//     memory M_A (O) / M_B (P) or stochastically, within τ · 6 the reflection lands on vane C (O) or D (P): F = 1, a satisfaction tone, his
//     drive falls · 7 she hears it while lit, her drive falls, she writes UP/DOWN into M_A / M_B, both resume. Unreinforced timeout τ, or a
//     broken beam (a visitor's shadow), aborts to scanning.
//   · bar Z: the two males contend; a majority decision device, weighted by drive intensity, decides halt or turn. The males can occlude each other.
//   · darkness matters: ambient light lowers every photocell's contrast and weakens the coupling (Pask 1971, p. 98).
// Everything is deterministic for a seed. Interpretation choices are marked INTERPRETATION.

const TAU = Math.PI * 2;
export const STAGE = ['', 'scan', 'contact', 'sync', 'commit', 'sweep', 'closure', 'consolidate'];
export const DEFAULTS = {
  Lmin: .3, Lmax: .8, Lcap: 1.25,          // drive thresholds; Lcap: the accumulators saturate (INTERPRETATION: a physical ceiling)
  omega: .55,                               // ω: the drop on satisfaction
  kappa: .06,                               // the cost of the energetic event (stage 4 raises the male's drive)
  tau: 4.2,                                 // τ: the window for the mirror search (s)
  tempo: 1,                                 // scales every δ
  ambient: 0,                               // 0 dark .. 1 lit gallery
  zSpeed: .16, zBias: 0,                    // bar Z (rad/s); zBias −1..1 from the visitor's "conducting"
  maleSpeed: .38, femaleSpeed: .22,         // horizontal motors (rad/s)
  beamHalf: .16, apertureHalf: .3,          // optical cones (rad)
  decode: .3, sync: 1.0, close: .45,      // dwell times (s) to decode u, to phase-lock, to register the reflection
  register: .9, commitHold: 1.0, closeHold: 1.0,   // INTERPRETATION: cinematic pacing of registration, the held beam before the sweep, and closure before consolidation
  mirrorSpeed: .9,                         // servo b (units/s, b ∈ [−1, 1]: +1 up, −1 down)
  grace: .45,                               // a broken line is forgiven this long before the encounter is lost
  seed: 7};
// positions (metres, plan x/z, y up), after Fig. 1 and the ZKM volume (≈ 3.0 × 3.05 × 3.66 m)
export const GEOM = {frameY: 3.45, barY: 3.0, barR: .78, maleY: 1.95, femaleY: 1.55, femaleR: 1.62, femaleAng: [Math.PI / 2, Math.PI / 2 + TAU / 3, Math.PI / 2 + 2 * TAU / 3], body: .24};

export function regime(O, P, Lmin, Lmax) {
  // the four regimes of the drive table; INTERPRETATION for the table's gaps (one drive above L_min, the other below): the higher one leads.
  if (O < Lmin && P < Lmin) return 'satisfied';
  if (O > Lmax && P > Lmax) return 'dual';
  return O >= P ? 'O' : 'P';
}

function rng(seed) { let a = seed >>> 0 || 1; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const wrap = a => { a = (a + Math.PI) % TAU; if (a < 0) a += TAU; return a - Math.PI; };
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

export function makeColloquy(opts = {}) {
  const P = {...DEFAULTS, ...opts};
  let R = rng(P.seed);
  const log = [], listeners = [];
  const emit = (kind, o = {}) => { const ev = {t: S.t, kind, ...o}; log.push(ev); if (log.length > 4000) log.splice(0, 1000); for (const f of listeners) f(ev); return ev; };
  const mkDrive = (o, p, dO, dP) => ({O: o, P: p, dO, dP});
  const males = [
    {id: 'G', side: 0, phi: 0, dir: 1, ...mkDrive(.55, .2, .021, .012), stage: 1, since: 0, lamp: 0, B: false, F: 0, partner: -1, desire: null, inverted: false, sat: 0, lostT: 0, flashHz: 3.1, refr: {}},
    {id: 'J', side: 1, phi: 0, dir: -1, ...mkDrive(.25, .5, .012, .022), stage: 1, since: 0, lamp: 0, B: false, F: 0, partner: -1, desire: null, inverted: false, sat: 0, lostT: 0, flashHz: 4.3, refr: {}}];
  const females = [0, 1, 2].map(i => ({id: 'F' + (i + 1), i, psi: 0, dir: i % 2 ? -1 : 1, ...mkDrive([.5, .35, .62][i], [.3, .55, .45][i], [.016, .013, .019][i], [.014, .018, .012][i]),
    stage: 1, since: 0, glow: 0, b: 0, bTarget: 0, partner: -1, desire: null, tone: 0, MA: {}, MB: {}, sweep: null, dwell: 0, lostT: 0, sat: 0, contactT: 0, syncT: 0, closeT: 0, refr: {}}));
  const visitor = {body: null, torch: null, mirror: null};
  const S = {t: 0, P, z: 0, zHalt: false, males, females, visitor, log, contentions: 0, stuck: 0, handshakes: 0, aborts: 0};

  // ---------------------------------------------------------------- geometry
  function malePos(m) { const a = S.z + m.side * Math.PI; return {x: Math.cos(a) * GEOM.barR, z: Math.sin(a) * GEOM.barR, out: a}; }
  function maleHeading(m) { return malePos(m).out + m.phi; }
  function femalePos(f) { const a = GEOM.femaleAng[f.i]; return {x: Math.cos(a) * GEOM.femaleR, z: Math.sin(a) * GEOM.femaleR, inward: a + Math.PI}; }
  function femaleHeading(f) { return femalePos(f).inward + f.psi; }
  // segment a→b blocked by a circle (another male's body, or the visitor)
  function blocked(a, b, skipMale) {
    const occ = [];
    for (const m of males) if (m !== skipMale) { const p = malePos(m); occ.push({x: p.x, z: p.z, r: GEOM.body}); }
    if (visitor.body) occ.push(visitor.body);
    for (const c of occ) { const dx = b.x - a.x, dz = b.z - a.z, L2 = dx * dx + dz * dz, u = clamp(((c.x - a.x) * dx + (c.z - a.z) * dz) / L2, 0, 1); const px = a.x + dx * u - c.x, pz = a.z + dz * u - c.z;
      if (u > .04 && u < .96 && px * px + pz * pz < c.r * c.r) return c === visitor.body ? 'visitor' : 'male'; }
    return null;
  }
  // a male's lamp reaching a female's aperture: both cones aligned and the line clear
  function aligned(m, f) {
    const pm = malePos(m), pf = femalePos(f), dx = pf.x - pm.x, dz = pf.z - pm.z, ang = Math.atan2(dz, dx), dist = Math.hypot(dx, dz);
    const okM = Math.abs(wrap(maleHeading(m) - ang)) < P.beamHalf, okF = Math.abs(wrap(femaleHeading(f) - (ang + Math.PI))) < P.apertureHalf;
    return {ok: okM && okF, dist, occl: okM && okF ? blocked(pm, pf, m) : null};
  }
  // a photocell's contrast against the gallery light (Pask: in moderate light the coupling weakened)
  const contrast = (I) => I / (I + P.ambient * .55 + 1e-6);
  // a photocell fires with a probability that falls as its contrast nears threshold (INTERPRETATION of the reported weakening)
  const sees = (I, need) => R() < clamp((contrast(I) - need + .25) / .5, 0, 1);

  const desireOf = a => { const r = regime(a.O, a.P, P.Lmin, P.Lmax); return r === 'satisfied' ? null : r === 'dual' ? (a.O >= a.P ? 'O' : 'P') : r; };
  const accepts = (f, d) => { const r = regime(f.O, f.P, P.Lmin, P.Lmax); return r === 'dual' || r === d; };
  function setStage(a, s, why) { a.stage = s; a.since = S.t; emit('stage', {who: a.id, stage: s, name: STAGE[s], why}); }
  function abort(m, f, why) {
    if (m) { m.B = false; m.F = 0; m.partner = -1; m.lostT = 0; m.refr[f ? f.id : 'V'] = S.t + 1.6; setStage(m, 1, why); }
    if (f) { f.partner = -1; f.tone = 0; f.sweep = null; f.lostT = 0; f.bTarget = 0; if (m) f.refr[m.id] = S.t + 1.6; setStage(f, 1, why); }
    S.aborts++; emit('abort', {m: m && m.id, f: f && f.id, why});
  }

  // ---------------------------------------------------------------- the step
  function step(dt) {
    S.t += dt;
    // drives build (accumulators), each between 0 and the ceiling
    for (const a of [...males, ...females]) { a.O = Math.min(P.Lcap, a.O + a.dO * P.tempo * dt); a.P = Math.min(P.Lcap, a.P + a.dP * P.tempo * dt); }

    // bar Z: the majority decision device, weighted by drive intensity (INTERPRETATION of "majority decision device", Pask 1971 pp. 89, 98)
    let wHalt = 0, wTurn = 0;
    for (const m of males) { const u = Math.max(m.O, m.P); if (m.stage >= 2 && m.stage <= 6) wHalt += u; else if (desireOf(m)) wTurn += u; }
    const halt = wHalt > 0 && wHalt >= wTurn;
    if (wHalt > 0 && wTurn > 0) { if (!S._cont) { S.contentions++; emit('contention', {halt, wHalt: +wHalt.toFixed(3), wTurn: +wTurn.toFixed(3)}); } S._cont = true; } else S._cont = false;
    if (halt !== S.zHalt) { S.zHalt = halt; emit('z', {halt}); }
    if (!halt) S.z = wrap(S.z + (P.zSpeed * (1 + 1.5 * P.zBias)) * dt);

    // males
    for (const m of males) {
      const d = desireOf(m);
      if (m.stage === 1) {
        m.B = false; m.F = 0;
        if (d) { m.phi += m.dir * P.maleSpeed * dt; if (Math.abs(m.phi) > Math.PI / 2) { m.phi = Math.sign(m.phi) * Math.PI / 2; m.dir *= -1; } }
        else m.phi += Math.sin(S.t * .2 + m.side) * .02 * dt;          // satisfied: quiescent drift, lamp dark
        m.desire = d; m.lamp = d ? (Math.sin(S.t * TAU * (m.flashHz * (d === 'P' ? 1.45 : 1))) > .2 ? 1 : 0) : 0;
      } else if (m.stage === 4 || m.stage === 5 || m.stage === 6) {
        m.lamp = 1; m.B = true;                                         // the steady energetic beam
        if (m.stage === 6) { if (S.t - m.since > P.closeHold) { m.B = false; setStage(m, 7, 'consolidate and resume'); } continue; }   // F = 1 held while she listens
        const f = females[m.partner];
        if (!f) { abort(m, null, 'no partner'); continue; }
        const al = aligned(m, f);
        if (!al.ok || al.occl) { m.lostT += dt; if (m.lostT > P.grace) abort(m, f, al.occl === 'visitor' ? 'occluded by visitor' : al.occl ? 'occluded by male' : 'line lost'); continue; } else m.lostT = 0;
        if (S.t - m.since > P.tau + .6 && m.stage < 6) abort(m, f, 'timeout τ');
      } else if (m.stage === 2 || m.stage === 3) {
        m.lamp = Math.sin(S.t * TAU * (m.flashHz * (m.desire === 'P' ? 1.45 : 1))) > .2 ? 1 : 0;   // still flashing u while she decodes
        const f = females[m.partner]; if (!f || f.partner !== males.indexOf(m)) { setStage(m, 1, 'partner left'); m.partner = -1; continue; }
        const al = aligned(m, f); if (!al.ok || al.occl) { m.lostT += dt; if (m.lostT > P.grace) abort(m, f, al.occl === 'visitor' ? 'occluded by visitor' : 'line lost before commitment'); continue; } else m.lostT = 0;
        // stage 3→4: his sound sensor hears her tone phase-locked to his own flashes: he commits
        if (f.stage === 3 && S.t - f.since > P.sync && sees(1.2, .5)) { m.phi = m.phi; m[m.desire] = Math.min(P.Lcap, m[m.desire] + P.kappa); setStage(m, 4, 'phase-lock heard: energetic event'); emit('energetic', {m: m.id, f: f.id, desire: m.desire}); }
      } else if (m.stage === 7) { if (S.t - m.since > 1.6) { m.partner = -1; m.F = 0; m.B = false; setStage(m, 1, 'resume'); } }
    }

    // females
    for (const f of females) {
      const r = regime(f.O, f.P, P.Lmin, P.Lmax), fi = females.indexOf(f);
      f.glow += (Math.max(f.O, f.P) / P.Lcap - f.glow) * Math.min(1, dt * 2);
      f.b += clamp(f.bTarget - f.b, -P.mirrorSpeed * dt, P.mirrorSpeed * dt);
      if (f.stage === 1) {
        f.tone = 0; f.bTarget = 0;
        if (r === 'satisfied') { /* quiescent: her horizontal motor halts until the drives rebuild */ }
        else { f.psi += f.dir * P.femaleSpeed * dt; if (Math.abs(f.psi) > Math.PI / 4) { f.psi = Math.sign(f.psi) * Math.PI / 4; f.dir *= -1; emit('limit', {f: f.id}); } }
        // stage 1→2: a flashing u lands on her aperture a
        let hit = null;
        for (const m of males) { if (m.stage !== 1 || !m.desire || (m.refr[f.id] || 0) > S.t) continue; const al = aligned(m, f); if (al.ok && !al.occl) { hit = m; f.seen = sees(1 / (1 + (al.dist / 2.2) ** 2), .55); break; } }
        if (hit) { f.contactT = Math.max(0, f.contactT + (f.seen ? dt : -.6 * dt)); if (f.contactT > P.decode) { f.contactT = 0;
            if (r !== 'satisfied' && accepts(f, hit.desire)) { const mi = males.indexOf(hit); f.partner = mi; f.desire = hit.desire; hit.partner = fi; setStage(f, 2, 'u decoded: ' + hit.id + ' seeks ' + hit.desire); setStage(hit, 2, 'seen by ' + f.id); }
            else { f.refr[hit.id] = S.t + 1.2; emit('decline', {f: f.id, m: hit.id, desire: hit.desire, regime: r}); } } }
        else f.contactT = 0;
        if (visitor.torch && visitor.torch.f === fi && (visitor.torch.until > S.t) && r !== 'satisfied' && accepts(f, visitor.torch.desire) && sees(1, .55)) { f.partner = -2; f.desire = visitor.torch.desire; setStage(f, 2, 'torch decoded: the visitor seeks ' + visitor.torch.desire); }
      } else if (f.stage === 2) {
        // stage 2→3: she registers him in short-term memory and answers with a tone phase-locked to his flashes
        f.tone = 0; if (S.t - f.since > P.register) { setStage(f, 3, 'registered; tone phase-locked'); f.tone = 1; const pm = males[f.partner]; if (pm && pm.stage === 2) setStage(pm, 3, 'hears her tone, phase-locked to his u'); }
      } else if (f.stage === 3) {
        f.tone = 1;
        const m = males[f.partner];
        if (f.partner === -2) { if (S.t - f.since > P.sync) setStage(f, 4, 'the torch is held steady on her'); continue; }
        if (!m) { setStage(f, 1, 'lost'); continue; }
        if (m.stage === 4) setStage(f, 4, 'his steady B is on her aperture');
        else if (S.t - f.since > 2.5) abort(m.stage <= 3 ? m : null, f, 'no commitment');
      } else if (f.stage === 4) {
        f.tone = .8;
        const m = males[f.partner];
        if (f.partner === -2) { if (S.t - f.since > P.commitHold) { setStage(f, 5, 'mirror sweep for the torch'); startSweep(f, 'V'); } continue; }
        if (!m || m.stage !== 4) { setStage(f, 1, 'his beam is gone'); f.partner = -1; continue; }
        if (S.t - f.since > P.commitHold) { setStage(f, 5, 'mirror sweep within τ'); setStage(m, 5, 'holds B while she sweeps b'); startSweep(f, m.id); }
      } else if (f.stage === 5) {
        f.tone = .6;
        const m = males[f.partner];
        if (S.t - f.since > P.tau) { abort(m && m.stage >= 4 ? m : null, f, f.partner === -2 ? 'torch: timeout τ (no vanes to close)' : 'timeout τ'); continue; }
        if (f.partner !== -2 && (!m || m.stage < 4)) { setStage(f, 1, 'his beam is gone'); f.partner = -1; f.sweep = null; continue; }
        sweepStep(f, dt);
        if (m && f.partner !== -2) {
          // the reflection: where mirror b sends his beam on his body: up → vane C, down → vane D (inverted males swap)
          const vane = f.b > .55 ? 'C' : f.b < -.55 ? 'D' : null, vaneFor = m.inverted ? {C: 'P', D: 'O'} : {C: 'O', D: 'P'};
          if (vane && vaneFor[vane] === m.desire) { f.closeT = Math.max(0, f.closeT + (sees(1.1, .55) ? dt : -.6 * dt)); if (f.closeT > P.close) { f.closeT = 0; closure(m, f, vane); } } else f.closeT = 0;
        }
      } else if (f.stage === 6) {
        // stage 6→7: she hears his satisfaction tone while still lit: her drive falls, and the angle that worked is written to memory
        f.tone = .6; const m = males[f.partner];
        if (S.t - f.since > P.closeHold) { if (m) { const d = f.desire; f[d] = Math.max(0, f[d] - P.omega); f.sat++; const mem = d === 'O' ? f.MA : f.MB; mem[m.id] = f.b > 0 ? 'UP' : 'DOWN';
            setStage(f, 7, 'satisfaction tone heard while lit: memory ' + (d === 'O' ? 'M_A' : 'M_B') + '[' + m.id + '] = ' + mem[m.id]); emit('memory', {f: f.id, m: m.id, reg: d === 'O' ? 'MA' : 'MB', val: mem[m.id]}); }
          else { f.partner = -1; setStage(f, 1, 'lost'); } }
      } else if (f.stage === 7) { if (S.t - f.since > 1.8) { f.partner = -1; f.tone = 0; f.bTarget = 0; setStage(f, 1, 'resume'); } }
      if (f.stage !== 1 && f.stage !== 5 && f.stage !== 7 && S.t - f.since > P.tau * 3) { S.stuck++; abort(males[f.partner] || null, f, 'watchdog'); }
    }
    for (const m of males) if (m.stage !== 1 && S.t - m.since > P.tau * 3) { S.stuck++; abort(m, females[m.partner] || null, 'watchdog'); }

    // the visitor as a prosthetic female: a hand mirror throws a committed male's own B back onto a vane
    if (visitor.mirror && visitor.mirror.until > S.t) { const m = males[visitor.mirror.m]; if (m && m.B) { const vane = visitor.mirror.dir === 'UP' ? 'C' : 'D', vaneFor = m.inverted ? {C: 'P', D: 'O'} : {C: 'O', D: 'P'};
        if (vaneFor[vane] === m.desire && sees(2.4, .45)) { visitor.mirror.t = (visitor.mirror.t || 0) + dt; if (visitor.mirror.t > P.close) { visitor.mirror = null; closure(m, females[m.partner] || null, vane, 'visitor mirror'); } } } }
  }

  function startSweep(f, who) {
    const mem = f.desire === 'O' ? f.MA : f.MB, k = who;
    if (mem[k]) { f.sweep = {mode: 'memory', target: mem[k] === 'UP' ? 1 : -1, first: mem[k], tries: 0}; emit('sweep', {f: f.id, m: who, desire: f.desire, mode: 'memory', first: mem[k]}); }
    else { const first = R() < .5 ? 'UP' : 'DOWN'; f.sweep = {mode: 'search', target: first === 'UP' ? 1 : -1, first, tries: 0}; emit('sweep', {f: f.id, m: who, desire: f.desire, mode: 'search', first}); }
    f.bTarget = f.sweep.target; f.dwell = 0;
  }
  function sweepStep(f, dt) {
    const s = f.sweep; if (!s) return;
    if (Math.abs(f.b - s.target) < .05) { f.dwell += dt;
      if (f.dwell > (s.mode === 'memory' ? .9 : .5)) { f.dwell = 0; s.tries++;
        if (s.mode === 'memory') { s.mode = 'search'; emit('adapt', {f: f.id, why: 'remembered angle unrewarded'}); }   // "can adapt if a male has inverted preferences"
        s.target = s.target > 0 ? -1 : 1; f.bTarget = s.target; } }
  }
  function closure(m, f, vane, how = 'mirror b') {
    const d = m.desire, before = m[d]; m.F = 1; m.vane = vane; m[d] = Math.max(0, m[d] - P.omega); m.sat++; setStage(m, 6, 'F = 1 on vane ' + vane + ' (' + how + ')'); emit('reinforce', {m: m.id, f: f && f.id, vane, desire: d, how, before: +before.toFixed(4), after: +m[d].toFixed(4)});
    if (f && how === 'mirror b') setStage(f, 6, 'his reinforcement lit on vane ' + vane + '; she listens for his tone');
    else if (f) { f.partner = -1; f.sweep = null; setStage(f, 1, 'a visitor closed his loop'); }
    S.handshakes++;
  }

  // ---------------------------------------------------------------- the visitor's four modes, scriptable
  const V = {
    torch(fi, desire = 'O', seconds = 4) { visitor.torch = {f: fi, desire, until: S.t + seconds}; emit('visitor', {mode: 'prosthetic male', f: females[fi].id, desire}); },
    mirror(mi, dir = 'UP', seconds = 3) { visitor.mirror = {m: mi, dir, until: S.t + seconds}; emit('visitor', {mode: 'prosthetic female', m: males[mi].id, dir}); },
    stand(x, z, r = .32) { const fresh = !visitor.body; visitor.body = {x, z, r}; if (fresh) emit('visitor', {mode: 'occlusion', x: +x.toFixed(2), z: +z.toFixed(2)}); },
    leave() { if (visitor.body) emit('visitor', {mode: 'occlusion ends'}); visitor.body = null; },
    conduct(o = {}) { if (o.zBias != null) P.zBias = clamp(o.zBias, -1, 1); if (o.tempo != null) P.tempo = clamp(o.tempo, .2, 3); if (!(S._condT > S.t - 1)) { S._condT = S.t; emit('visitor', {mode: 'composition', zBias: +P.zBias.toFixed(2), tempo: +P.tempo.toFixed(2)}); } }};

  return {S, P, step, run(seconds, dt = 1 / 60) { const n = Math.round(seconds / dt); for (let i = 0; i < n; i++) step(dt); },
    on: f => listeners.push(f), visitor: V, malePos, femalePos, maleHeading, femaleHeading, aligned, regime: (a) => regime(a.O, a.P, P.Lmin, P.Lmax), desireOf,
    set(o) { Object.assign(P, o); if (o.seed != null) R = rng(o.seed); },
    snapshot() { return {t: +S.t.toFixed(2), z: +S.z.toFixed(3), zHalt: S.zHalt, handshakes: S.handshakes, aborts: S.aborts, contentions: S.contentions,
      males: males.map(m => ({id: m.id, O: +m.O.toFixed(3), P: +m.P.toFixed(3), regime: regime(m.O, m.P, P.Lmin, P.Lmax), stage: m.stage, B: m.B, F: m.F, lamp: m.lamp, phi: +m.phi.toFixed(3), partner: m.partner >= 0 ? females[m.partner].id : null})),
      females: females.map(f => ({id: f.id, O: +f.O.toFixed(3), P: +f.P.toFixed(3), regime: regime(f.O, f.P, P.Lmin, P.Lmax), stage: f.stage, b: +f.b.toFixed(2), tone: f.tone, MA: {...f.MA}, MB: {...f.MB}, partner: f.partner >= 0 ? males[f.partner].id : f.partner === -2 ? 'visitor' : null,
        timer: f.stage === 5 ? +(P.tau - (S.t - f.since)).toFixed(2) : null}))}; }};
}
