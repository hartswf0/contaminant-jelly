// TENTACLES: the jelly's body as the controller, shared by the Steer Lab and the open water.
// Works in a plane (x across, y up). The host gives it the world (anchors, what they do) through env; it gives back forces and a torque on the bell.
// Invariant: a finger owns its arm from touch to lift. An interrupted touch loses its grip; it never launches.
// env: anchorAt(p, arm, B, {cast}) -> anchor | null (null = open water); update(an, arm, finger, dt, T, B) (moving anchors, digging, currents);
//      react(an, Fx, Fy, dt) (a light thing pulled by the arm); event(name, data) (sound, haptics, moves).
export const FCOL = [[1, .64, .3], [.35, .9, .9], [.98, .45, .7], [.45, .9, .5], [.75, .6, 1], [1, .9, .45]];
export function makeArms(opt = {}) {
  const NA = opt.n || 6, AN = opt.AN || 16, REACH = opt.reach || 7.2, BR = opt.R || .95;
  const arms = Array.from({length: NA}, (_, i) => ({i, phi: (i / (NA - 1) - .5) * 2.5, owner: null, mode: 'free', anc: null, L0: 3, L00: 3, ten: 0, slipK: 0, stretch: 0, dist: 0, ripple: -9, lostT: -9, col: [.5, .6, .65], X: new Float32Array(AN * 2), XP: new Float32Array(AN * 2), init: false, cast: null}));
  const F = new Map(), releases = []; let fingerN = 0, snap = false;
  const rimOf = (a, B, out = {x: 0, y: 0}) => { const lx = Math.sin(a.phi) * BR, ly = -Math.cos(a.phi) * BR * .5 - .1, c = Math.cos(B.th), s = Math.sin(B.th); out.x = B.x + lx * c - ly * s; out.y = B.y + lx * s + ly * c; return out; };
  const tipOf = a => ({x: a.X[(AN - 1) * 2], y: a.X[(AN - 1) * 2 + 1]});
  function water(p) { return {type: 'water', x: p.x, y: p.y, k: 20}; }
  function down(id, p, B, env, T) { if (F.has(id)) return null;
    let arm = null, bd = 1.3; for (const a of arms) { if (a.owner !== null) continue; const t = tipOf(a), d = Math.hypot(t.x - p.x, t.y - p.y); if (d < bd) { bd = d; arm = a; } }   // the arm under the finger (a cast arm too)
    if (!arm) { let ba = 1e9; const ang = Math.atan2(p.x - B.x, -(p.y - B.y)) - B.th; for (const a of arms) { if (a.owner !== null || a.mode === 'cast') continue; const d = Math.abs(Math.atan2(Math.sin(ang - a.phi), Math.cos(ang - a.phi))); if (d < ba) { ba = d; arm = a; } } }
    if (!arm) { env.event('full'); return null; }
    const keep = arm.mode === 'latch' && arm.anc && arm.anc.cast;   // taking hold of an arm you threw: it is yours now, still hooked
    const f = {id, arm, p0: {...p}, p: {...p}, t0: T, col: FCOL[fingerN++ % FCOL.length], hist: [{x: p.x, y: p.y, t: T}]}; F.set(id, f); arm.owner = id; arm.col = f.col; arm.cast = null;
    if (keep) { arm.anc.cast = false; const r = rimOf(arm, B), d = Math.hypot(r.x - arm.anc.x, r.y - arm.anc.y) || 1; f.u = {x: (r.x - arm.anc.x) / d, y: (r.y - arm.anc.y) / d}; f.pl = {...p}; arm.L00 = arm.L0; return f; }
    commit(arm, f, B, env, T); return f; }
  function commit(a, f, B, env, T) { const r = rimOf(a, B), d = Math.hypot(f.p.x - r.x, f.p.y - r.y); if (d > REACH) { a.mode = 'reach'; a.anc = null; return; }
    const an = env.anchorAt(f.p, a, B, {}) || water(f.p); a.anc = an; a.mode = 'latch'; a.L0 = Math.max(1, Math.hypot(an.x - r.x, an.y - r.y) * .95); a.L00 = a.L0; const dd = Math.hypot(r.x - an.x, r.y - an.y) || 1; f.u = {x: (r.x - an.x) / dd, y: (r.y - an.y) / dd}; f.pl = {...f.p}; a.ripple = T;
    env.event('latch', {an, arm: a, tumbling: Math.abs(B.w) > 1.6 || Math.hypot(B.vx, B.vy) > 6.5}); }
  function move(id, p, T) { const f = F.get(id); if (!f) return; f.p = {...p}; f.hist.push({x: p.x, y: p.y, t: T}); while (f.hist.length > 2 && T - f.hist[0].t > .12) f.hist.shift(); }
  function up(id, interrupted, B, env, T) { const f = F.get(id); if (!f) return; F.delete(id); const a = f.arm; a.owner = null;
    if (interrupted) { a.mode = 'losing'; a.lostT = T; env.event('lost', {arm: a}); return; }
    // a flick: the finger was moving fast when it lifted, so the arm is thrown along it
    const h = f.hist, h0 = h[0], h1 = h[h.length - 1], dtH = Math.max(.016, h1.t - h0.t), vx = (h1.x - h0.x) / dtH, vy = (h1.y - h0.y) / dtH, sp = Math.hypot(vx, vy);
    if (sp > 11 && !(a.mode === 'latch' && a.anc && a.anc.heavy && a.ten > 6)) { const r = rimOf(a, B); a.mode = 'cast'; a.anc = null; a.cast = {x: r.x, y: r.y, vx: vx / sp * 24, vy: vy / sp * 24, t: 0}; env.event('cast', {arm: a}); return; }
    const wasTaut = a.mode === 'latch' && a.ten > 6; a.mode = 'free'; a.anc = null; releases.push({t: T, ten: a.ten, i: a.i}); if (wasTaut) { snap = true; env.event('release', {arm: a, ten: a.ten}); } }
  function step(dt, T, B, env) { let fx = 0, fy = 0, tq = 0;
    const pull = (a, ax, ay, k, L0, cap = 70) => { const r = rimOf(a, B), dx = ax - r.x, dy = ay - r.y, d = Math.hypot(dx, dy) || 1e-6, st = d - L0; a.dist = d; if (st <= 0) { a.ten = 0; return null; } const T0 = Math.min(cap, k * st); a.ten = T0; const Fx = dx / d * T0, Fy = dy / d * T0; fx += Fx; fy += Fy; tq += (r.x - B.x) * Fy - (r.y - B.y) * Fx; return [Fx, Fy]; };
    for (const a of arms) { const f = a.owner !== null ? F.get(a.owner) : null;
      if (a.mode === 'reach' && f) { const r = rimOf(a, B), d = Math.hypot(f.p.x - r.x, f.p.y - r.y); if (d <= REACH) commit(a, f, B, env, T); else { pull(a, f.p.x, f.p.y, 3.2, REACH * .7, 9); a.stretch = Math.min(1, (d - REACH) / 4); } }
      else if (a.mode === 'cast' && a.cast) { const c = a.cast, r = rimOf(a, B); c.t += dt; c.x += c.vx * dt; c.y += c.vy * dt; const hit = env.anchorAt({x: c.x, y: c.y}, a, B, {cast: true});
        if (hit) { a.anc = hit; hit.cast = true; a.mode = 'latch'; a.L0 = Math.max(1, Math.hypot(hit.x - r.x, hit.y - r.y)); a.L00 = a.L0; a.ripple = T; a.castT = T; env.event('hooked', {an: hit, arm: a}); }
        else if (Math.hypot(c.x - r.x, c.y - r.y) > REACH * 1.2 || c.t > .6) { a.mode = 'free'; a.cast = null; env.event('miss', {arm: a}); } }
      else if (a.mode === 'latch' && a.anc && (f || a.anc.cast)) { const an = a.anc;
        if (an.type === 'water' && f) { an.x += (f.p.x - an.x) * Math.min(1, dt * 6); an.y += (f.p.y - an.y) * Math.min(1, dt * 6); const r = rimOf(a, B); if (a.ten > 3) { an.x += (r.x - an.x) * dt * .35; an.y += (r.y - an.y) * dt * .35; } }
        if (env.update) env.update(an, a, f, dt, T, B);
        if (f && an.type !== 'water' && !an.skid) { const s = (f.p.x - f.pl.x) * f.u.x + (f.p.y - f.pl.y) * f.u.y; a.L0 = Math.max(.8, a.L00 - 1.5 * s); }   // winch: draw the finger toward the jelly and the arm hauls in
        if (an.cast) { a.L0 = Math.max(an.light ? .6 : 1.4, a.L0 - dt * (an.light ? 6 : 4.5)); if (a.L0 <= (an.light ? .7 : 1.5) && T - a.castT > .5) { a.mode = 'free'; a.anc = null; env.event(an.light ? 'hauled' : 'arrived', {an, arm: a}); } }   // a thrown arm reels itself in
        if (a.ten > 4 && !an.cast) a.L0 += dt * .25, a.L00 += dt * .25;   // a loaded arm creeps: the pose sags
        if (a.mode === 'latch') { const F2 = pull(a, an.x, an.y, an.k, a.L0); if (F2 && an.light && env.react) env.react(an, F2[0], F2[1], dt);
          const slipAt = an.slipAt ?? (an.type === 'water' ? 99 : an.skid ? 2 : 3); a.slipK = Math.max(0, Math.min(1, (a.dist - a.L0) / slipAt));
          if (a.slipK >= 1 && an.type !== 'water') { a.mode = f ? 'reach' : 'free'; a.anc = null; a.ten = 0; env.event('slip', {arm: a}); } } }
      else if (a.mode === 'losing') { if (a.anc) { a.L0 += dt * 14; pull(a, a.anc.x, a.anc.y, a.anc.k * .5, a.L0); } if (T - a.lostT > .4) { a.mode = 'free'; a.anc = null; a.ten = 0; } }
      else { a.ten = 0; a.slipK = 0; a.stretch = 0; if (a.mode === 'latch' && !f) { a.mode = 'free'; a.anc = null; } } }
    const out = {fx, fy, tq, snap: snap}; snap = false; while (releases.length && T - releases[0].t > 1.2) releases.shift(); return out; }
  // the arms' bodies: verlet chains from the rim; latched tips pinned, reaching or thrown tips leading, free arms trailing
  function chains(dt, T, B) { for (const a of arms) { const r = rimOf(a, B), f = a.owner !== null ? F.get(a.owner) : null, X = a.X, XP = a.XP, seg = a.mode === 'latch' ? Math.max(a.L0, 1) / (AN - 1) : a.mode === 'cast' ? REACH * 1.25 / (AN - 1) : 3.4 / (AN - 1);
      if (!a.init) { a.init = true; for (let j = 0; j < AN; j++) { X[j * 2] = XP[j * 2] = r.x; X[j * 2 + 1] = XP[j * 2 + 1] = r.y - j * seg; } }
      for (let j = 1; j < AN; j++) { const q = j * 2; for (let c = 0; c < 2; c++) { const v = (X[q + c] - XP[q + c]) * Math.exp(-dt * 2.2); XP[q + c] = X[q + c]; X[q + c] += v + (c === 1 ? -.4 : 0) * dt * dt + Math.sin(T * 2 + j * .5 + a.i) * .004 * (a.mode === 'free' ? 1 : .2); } }
      X[0] = XP[0] = r.x; X[1] = XP[1] = r.y; const tip = (AN - 1) * 2, pinned = a.mode === 'latch' || a.mode === 'reach' || a.mode === 'cast';
      if (a.mode === 'latch' && a.anc) { X[tip] = a.anc.x; X[tip + 1] = a.anc.y; }
      else if (a.mode === 'reach' && f) { const dx = f.p.x - r.x, dy = f.p.y - r.y, d = Math.hypot(dx, dy) || 1, L = Math.min(d, REACH + 1.2 * a.stretch); X[tip] += (r.x + dx / d * L - X[tip]) * .3; X[tip + 1] += (r.y + dy / d * L - X[tip + 1]) * .3; }
      else if (a.mode === 'cast' && a.cast) { X[tip] = a.cast.x; X[tip + 1] = a.cast.y; }
      for (let it = 0; it < 10; it++) for (let j = 0; j < AN - 1; j++) { const p0 = j * 2, p1 = p0 + 2, dx = X[p1] - X[p0], dy = X[p1 + 1] - X[p0 + 1], d = Math.hypot(dx, dy) || 1e-6, e = (d - seg) / d, w0 = j ? .5 : 0, w1 = (j + 1 === AN - 1 && pinned) ? 0 : (j ? .5 : 1), ws = (w0 + w1) || 1;
        if (d > seg || a.mode !== 'latch') { X[p0] += dx * e * w0 / ws; X[p0 + 1] += dy * e * w0 / ws; X[p1] -= dx * e * w1 / ws; X[p1 + 1] -= dy * e * w1 / ws; } } } }
  function shift(dx, dy) { for (const a of arms) { for (let j = 0; j < AN; j++) { a.X[j * 2] -= dx; a.XP[j * 2] -= dx; a.X[j * 2 + 1] -= dy; a.XP[j * 2 + 1] -= dy; } if (a.anc) { a.anc.x -= dx; a.anc.y -= dy; } if (a.cast) { a.cast.x -= dx; a.cast.y -= dy; } } for (const f of F.values()) { for (const k of ['p', 'p0', 'pl']) if (f[k]) { f[k].x -= dx; f[k].y -= dy; } f.hist.forEach(h => { h.x -= dx; h.y -= dy; }); } }   // rebase the plane
  function releaseAll(env, T) { for (const id of [...F.keys()]) up(id, true, null, env, T); }
  return {arms, F, releases, AN, NA, REACH, down, move, up, step, chains, rimOf, tipOf, shift, releaseAll};
}
// draw a body's posture: the bell tilted as it is, every arm's load in its finger's colour, a red bead for an arm about to slip
export function drawPosture(g, arms, th, cx, cy) { const R0 = 30; g.save(); g.translate(cx, cy); g.fillStyle = 'rgba(5,9,9,.55)'; g.beginPath(); g.arc(0, 0, 66, 0, 7); g.fill(); g.rotate(-th);
  g.strokeStyle = 'rgba(240,163,90,.8)'; g.lineWidth = 2; g.beginPath(); g.ellipse(0, 0, R0, R0 * .62, 0, Math.PI, 0); g.stroke();
  for (const a of arms) { const ang = a.phi, lx = Math.sin(ang) * R0, ly = Math.cos(ang) * R0 * .45, len = 8 + Math.min(34, a.ten * 1.1), owned = a.owner !== null || a.mode === 'cast' || (a.anc && a.anc.cast); g.strokeStyle = owned ? `rgba(${a.col.map(v => v * 255 | 0)},${.5 + Math.min(.5, a.ten / 30)})` : 'rgba(130,147,164,.4)'; g.lineWidth = owned ? 2 + Math.min(3, a.ten / 12) : 1.2;
    g.beginPath(); g.moveTo(lx, ly); g.lineTo(lx + Math.sin(ang) * len, ly + Math.cos(ang) * len); g.stroke(); if (a.slipK > .7) { g.fillStyle = 'rgba(255,90,70,.9)'; g.beginPath(); g.arc(lx + Math.sin(ang) * len, ly + Math.cos(ang) * len, 4, 0, 7); g.fill(); } }
  g.restore(); g.fillStyle = 'rgba(207,221,232,.6)'; g.font = "300 10px 'JetBrains Mono', monospace"; g.textAlign = 'center'; g.fillText('posture', cx, cy + 58); }
