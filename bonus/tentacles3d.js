// TENTACLES 3D: the jelly's body as the controller, in space and (with film-time anchors) in time.
// A finger is a ray into the scene. The host's env.pick(ray, arm, B, {cast}) finds what that ray touches (a point in space, perhaps with a time t);
// if nothing, the arm braces in open water on a plane through the bell facing the camera, and a finger held still pushes that brace deeper.
// env: pick(ray, arm, B, o) -> {type, p: Vector3, k, heavy?, light?, obj?, t?} | null; water(ray, B, depth) -> Vector3; update(an, arm, finger, dt, T, B);
//      react(an, F, dt) (a light thing pulled); screen(v3) -> [x, y]; event(name, data)
// Invariant: a finger owns its arm from touch to lift. An interrupted touch loses its grip and never launches.
export const FCOL = [[1, .64, .3], [.35, .9, .9], [.98, .45, .7], [.45, .9, .5], [.75, .6, 1], [1, .9, .45]];
export function makeArms3D(THREE, opt = {}) {
  const NA = opt.n || 6, AN = opt.AN || 16, REACH = opt.reach || 8, BR = opt.R || 1;
  const V = () => new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0);
  const arms = Array.from({length: NA}, (_, i) => ({i, a: i / NA * Math.PI * 2, owner: null, mode: 'free', anc: null, L0: 3, L00: 3, ten: 0, slipK: 0, stretch: 0, dist: 0, ripple: -9, lostT: -9, col: [.5, .6, .65], X: new Float32Array(AN * 3), XP: new Float32Array(AN * 3), init: false, cast: null}));
  const F = new Map(), releases = []; let fingerN = 0, snap = false;
  const rimOf = (a, B, out = V()) => out.set(Math.sin(a.a) * BR, -.35 * BR, Math.cos(a.a) * BR).applyQuaternion(B.q).add(B.p);
  const tipOf = (a, out = V()) => out.set(a.X[(AN - 1) * 3], a.X[(AN - 1) * 3 + 1], a.X[(AN - 1) * 3 + 2]);
  const _r = V(), _t = V(), _d = V(), now = () => performance.now() / 1000;   // a flick is the hand's speed, so it is timed by the clock, not the game
  function down(id, ray, sx, sy, B, env, T) { if (F.has(id)) return null;
    // the arm under the finger (by screen distance to its tip), else the free arm whose rim faces the touch
    let arm = null, bd = 44; for (const a of arms) { if (a.owner !== null) continue; const s = env.screen(tipOf(a, _t)); if (!s) continue; const d = Math.hypot(s[0] - sx, s[1] - sy); if (d < bd) { bd = d; arm = a; } }
    if (!arm) { const target = ray.origin.clone().addScaledVector(ray.direction, B.p.distanceTo(ray.origin)); let ba = -9; for (const a of arms) { if (a.owner !== null || a.mode === 'cast') continue; const r = rimOf(a, B, _r), dir = _d.copy(r).sub(B.p).normalize(), want = target.clone().sub(B.p).normalize(), dot = dir.dot(want); if (dot > ba) { ba = dot; arm = a; } } }
    if (!arm) { env.event('full'); return null; }
    const keep = arm.mode === 'latch' && arm.anc && arm.anc.cast;
    const f = {id, arm, ray: ray.clone(), sx, sy, sx0: sx, sy0: sy, t0: T, still: 0, depth: 0, col: FCOL[fingerN++ % FCOL.length], hist: [{x: sx, y: sy, t: now()}]}; F.set(id, f); arm.owner = id; arm.col = f.col; arm.cast = null;
    if (keep) { arm.anc.cast = false; f.slx = sx; f.sly = sy; arm.L00 = arm.L0; return f; }
    commit(arm, f, B, env, T); return f; }
  function commit(a, f, B, env, T) { const an = env.pick(f.ray, a, B, {}) || {type: 'water', p: env.water(f.ray, B, 0), k: 20}; const r = rimOf(a, B, _r), d = r.distanceTo(an.p);
    if (d > REACH) { a.mode = 'reach'; a.anc = null; a.want = an; return; }
    a.anc = an; a.mode = 'latch'; a.L0 = Math.max(1, d * .95); a.L00 = a.L0; f.slx = f.sx; f.sly = f.sy; a.ripple = T; env.event('latch', {an, arm: a, tumbling: B.w.length() > 1.8 || B.v.length() > 7}); }
  function move(id, ray, sx, sy, T) { const f = F.get(id); if (!f) return; if (Math.hypot(sx - f.sx, sy - f.sy) > 3) f.still = 0; f.ray.copy(ray); f.sx = sx; f.sy = sy; const n = now(); f.hist.push({x: sx, y: sy, t: n}); while (f.hist.length > 2 && n - f.hist[0].t > .12) f.hist.shift(); }
  function up(id, interrupted, B, env, T) { const f = F.get(id); if (!f) return; F.delete(id); const a = f.arm; a.owner = null;
    if (interrupted) { a.mode = 'losing'; a.lostT = T; env.event('lost', {arm: a}); return; }
    const h = f.hist, h0 = h[0], h1 = h[h.length - 1], dt = Math.max(.016, h1.t - h0.t), sp = Math.hypot(h1.x - h0.x, h1.y - h0.y) / dt;
    if (sp > 900 && !(a.mode === 'latch' && a.anc && a.anc.heavy && a.ten > 6)) {   // a flick throws the arm along the finger's ray
      const hit = env.pick(f.ray, a, B, {cast: true}); a.mode = 'cast'; a.anc = null; const r = rimOf(a, B, V()); a.cast = {from: r.clone(), to: hit ? hit.p.clone() : r.clone().addScaledVector(f.ray.direction, REACH * 1.3), hit, t: 0}; env.event('cast', {arm: a}); return; }
    const wasTaut = a.mode === 'latch' && a.ten > 6; a.mode = 'free'; a.anc = null; releases.push({t: T, ten: a.ten, i: a.i}); if (wasTaut) { snap = true; env.event('release', {arm: a, ten: a.ten}); } }
  function step(dt, T, B, env) { const Fsum = V(), Tq = V();
    const pull = (a, P, k, L0, cap = 70) => { const r = rimOf(a, B, V()), dv = P.clone().sub(r), d = dv.length() || 1e-6, st = d - L0; a.dist = d; if (st <= 0) { a.ten = 0; return null; } const T0 = Math.min(cap, k * st); a.ten = T0; const Fv = dv.multiplyScalar(T0 / d); Fsum.add(Fv); Tq.add(r.sub(B.p).cross(Fv)); return Fv; };
    for (const a of arms) { const f = a.owner !== null ? F.get(a.owner) : null;
      if (a.mode === 'reach' && f) { const want = env.pick(f.ray, a, B, {}); const P = want ? want.p : env.water(f.ray, B, f.depth); const d = rimOf(a, B, _r).distanceTo(P); if (d <= REACH) commit(a, f, B, env, T); else { pull(a, P, 3.2, REACH * .7, 9); a.stretch = Math.min(1, (d - REACH) / 4); a.reachP = P; } }
      else if (a.mode === 'cast' && a.cast) { const c = a.cast; c.t += dt * 5; if (c.t >= 1) { if (c.hit) { a.anc = c.hit; c.hit.cast = true; a.mode = 'latch'; a.L0 = Math.max(1, rimOf(a, B, _r).distanceTo(c.hit.p)); a.L00 = a.L0; a.castT = T; a.ripple = T; env.event('hooked', {an: c.hit, arm: a}); } else { a.mode = 'free'; env.event('miss', {arm: a}); } a.cast = c.hit ? null : null; } }
      else if (a.mode === 'latch' && a.anc && (f || a.anc.cast)) { const an = a.anc;
        if (an.type === 'water' && f) { f.still += dt; if (f.still > .4) f.depth = Math.min(8, f.depth + dt * 3.5); const P = env.water(f.ray, B, f.depth); an.p.lerp(P, Math.min(1, dt * 6)); if (a.ten > 3) an.p.lerp(rimOf(a, B, _r), dt * .35); }   // held still, a water brace pushes deeper along your line of sight
        if (env.update) env.update(an, a, f, dt, T, B);
        if (f && an.type !== 'water' && !an.scrub) { const bs = env.screen(B.p), as = env.screen(an.p); if (bs && as) { const ux = bs[0] - as[0], uy = bs[1] - as[1], ul = Math.hypot(ux, uy) || 1, s = ((f.sx - f.slx) * ux + (f.sy - f.sly) * uy) / ul; a.L0 = Math.max(.8, a.L00 - s * .03); } }   // winch: draw the finger toward the bell on screen and the arm hauls in
        if (an.cast) { a.L0 = Math.max(an.light ? .6 : 1.5, a.L0 - dt * (an.light ? 6 : 4.5)); if (a.L0 <= (an.light ? .7 : 1.6) && T - a.castT > .5) { a.mode = 'free'; a.anc = null; env.event(an.light ? 'hauled' : 'arrived', {an, arm: a}); } }
        if (a.ten > 4 && !an.cast) a.L0 += dt * .25, a.L00 += dt * .25;
        if (a.mode === 'latch') { const Fv = pull(a, an.p, an.k, a.L0); if (Fv && an.light && env.react) env.react(an, Fv, dt);
          const slipAt = an.slipAt ?? (an.type === 'water' ? 99 : 3); a.slipK = Math.max(0, Math.min(1, (a.dist - a.L0) / slipAt)); if (a.slipK >= 1 && an.type !== 'water') { a.mode = f ? 'reach' : 'free'; a.anc = null; a.ten = 0; env.event('slip', {arm: a}); } } }
      else if (a.mode === 'losing') { if (a.anc) { a.L0 += dt * 14; pull(a, a.anc.p, a.anc.k * .5, a.L0); } if (T - a.lostT > .4) { a.mode = 'free'; a.anc = null; a.ten = 0; } }
      else { a.ten = 0; a.slipK = 0; a.stretch = 0; if (a.mode === 'latch' && !f) { a.mode = 'free'; a.anc = null; } } }
    const out = {F: Fsum, T: Tq, snap}; snap = false; while (releases.length && T - releases[0].t > 1.2) releases.shift(); return out; }
  function chains(dt, T, B) { for (const a of arms) { const r = rimOf(a, B, V()), f = a.owner !== null ? F.get(a.owner) : null, X = a.X, XP = a.XP, seg = a.mode === 'latch' ? Math.max(a.L0, 1) / (AN - 1) : 3.6 / (AN - 1), down = V().set(0, -1, 0).applyQuaternion(B.q);
      if (!a.init) { a.init = true; for (let j = 0; j < AN; j++) { X[j * 3] = XP[j * 3] = r.x + down.x * j * seg; X[j * 3 + 1] = XP[j * 3 + 1] = r.y + down.y * j * seg; X[j * 3 + 2] = XP[j * 3 + 2] = r.z + down.z * j * seg; } }
      for (let j = 1; j < AN; j++) { const q = j * 3; for (let c = 0; c < 3; c++) { const v = (X[q + c] - XP[q + c]) * Math.exp(-dt * 2.2); XP[q + c] = X[q + c]; X[q + c] += v + down.getComponent(c) * .5 * dt * dt + Math.sin(T * 2 + j * .5 + a.i + c * 2) * .003 * (a.mode === 'free' ? 1 : .2); } }
      X[0] = XP[0] = r.x; X[1] = XP[1] = r.y; X[2] = XP[2] = r.z; const tip = (AN - 1) * 3; let pin = null;
      if (a.mode === 'latch' && a.anc) pin = a.anc.p; else if (a.mode === 'reach' && a.reachP) { const dv = a.reachP.clone().sub(r), d = dv.length() || 1; pin = r.clone().addScaledVector(dv, Math.min(d, REACH + 1.2 * a.stretch) / d); } else if (a.mode === 'cast' && a.cast) pin = a.cast.from.clone().lerp(a.cast.to, Math.min(1, a.cast.t));
      if (pin) { X[tip] = pin.x; X[tip + 1] = pin.y; X[tip + 2] = pin.z; }
      const segL = a.mode === 'cast' ? r.distanceTo(pin || r) / (AN - 1) + .01 : seg;
      for (let it = 0; it < 10; it++) for (let j = 0; j < AN - 1; j++) { const p0 = j * 3, p1 = p0 + 3, dx = X[p1] - X[p0], dy = X[p1 + 1] - X[p0 + 1], dz = X[p1 + 2] - X[p0 + 2], d = Math.hypot(dx, dy, dz) || 1e-6, e = (d - segL) / d, w0 = j ? .5 : 0, w1 = (j + 1 === AN - 1 && pin) ? 0 : (j ? .5 : 1), ws = (w0 + w1) || 1;
        if (d > segL || a.mode !== 'latch') { X[p0] += dx * e * w0 / ws; X[p0 + 1] += dy * e * w0 / ws; X[p0 + 2] += dz * e * w0 / ws; X[p1] -= dx * e * w1 / ws; X[p1 + 1] -= dy * e * w1 / ws; X[p1 + 2] -= dz * e * w1 / ws; } } } }
  function releaseAll(env, T) { for (const id of [...F.keys()]) up(id, true, null, env, T); }
  return {arms, F, releases, AN, NA, REACH, down, move, up, step, chains, rimOf, releaseAll};
}
