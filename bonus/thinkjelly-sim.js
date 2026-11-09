// THE THINKING JELLY's nervous system: how a moon jelly decides to pulse.
// Eight rhopalia (pacemakers) sit on the rim. Each charges at its own rate; the first to fill fires. Its signal runs both ways round the
// nerve ring; every stretch of ring it passes makes the coronal muscle there twitch, and goes refractory, so the two waves meet at the far
// side and die. A pacemaker the wave passes is reset: the fastest one leads, the rest follow (Romanes, 1870s). Silence pacemakers and the
// beat slows to the next fastest. Cut the ring and the wave must go the long way round. Start a wave one way round a ring with no pacemakers
// and it circles for ever (Mayer's trapped wave, 1906).
export function makeNerve(o = {}) {
  const N = o.n || 48, NR = 8, LOOP = o.loop || 1.0, DELAY = LOOP / N, REFR = o.refr || .42;
  const PER = o.periods || [2.35, 1.9, 2.6, 2.1, 1.62, 2.45, 2.0, 2.8];   // seconds; pacemaker 5 (index 4) is the fastest
  const M = {N, NR, LOOP, t: 0, warm: 1, act: new Float32Array(N), dact: new Float32Array(N), tw: new Float32Array(N).fill(-9), ref: new Float32Array(N), at: new Float32Array(N).fill(Infinity),
    cuts: new Set(), rh: PER.map((p, i) => ({i, node: Math.round(i * N / NR) % N, period: p, charge: (i * .37) % 1 * .6, silent: false, last: -9, led: 0})), events: [], pulses: []};
  const RISE = o.rise || .1, FALL = o.fall || .32, twitch = a => a < 0 ? 0 : a < RISE ? .5 - .5 * Math.cos(Math.PI * a / RISE) : Math.exp(-(a - RISE) / FALL);   // how long the muscle takes to pull, and to let go
  const cutBetween = (a, b) => M.cuts.has(Math.min(a, b) === 0 && Math.max(a, b) === N - 1 ? N - 1 : Math.min(a, b));   // gap g lies between node g and g + 1
  function fire(n, kind, block) { const t = M.t; if (t < M.ref[n]) return false; M.ref[n] = t + REFR; M.tw[n] = t; M.at[n] = Infinity;
    for (const d of [1, -1]) { if (block === d) continue; const m = (n + d + N) % N; if (cutBetween(n, m) || t + DELAY < M.ref[m]) continue; M.at[m] = Math.min(M.at[m], t + DELAY); }
    const r = M.rh.find(q => q.node === n); if (r) { const lead = kind === 'lead'; r.charge = 0; r.last = t; if (lead) { r.led++; M.pulses.push({t, r: r.i}); if (M.pulses.length > 60) M.pulses.shift(); } M.events.push({t, kind: lead ? 'lead' : 'reset', r: r.i, n, silent: r.silent && !lead}); }
    M.events.push({t, kind: 'node', n}); return true; }
  // the nerve runs on its own fine clock (5 ms), whatever the frame rate: a slow frame must not slow the signal
  M.step = dt => { M.events.length = 0; const n = Math.max(1, Math.ceil(dt / .005)); for (let k = 0; k < n; k++) tick(dt / n); };
  const tick = dt => { M.t += dt; const t = M.t;
    for (const r of M.rh) { if (r.silent) continue; r.charge += dt * M.warm / r.period; if (r.charge >= 1) { if (!fire(r.node, 'lead')) r.charge = .97; } }
    for (let pass = 0; pass < 3; pass++) for (let n = 0; n < N; n++) if (M.at[n] <= t) { M.at[n] = Infinity; fire(n, 'wave'); }
    for (let n = 0; n < N; n++) { const a = twitch(t - M.tw[n]); M.dact[n] = (a - M.act[n]) / Math.max(dt, 1e-4); M.act[n] = a; } };
  M.twitchAt = (n, lag) => twitch(M.t - M.tw[n] - lag);   // the muscle's pull at a stretch of ring, as it was `lag` seconds ago
  M.stimulate = i => fire(M.rh[i].node, 'lead');                       // a touch makes a pacemaker fire now
  M.oneWay = n => { fire(n, 'wave', -1); M.ref[(n - 1 + N) % N] = M.t + REFR; };   // start a wave that can only go one way round
  // beats a minute over the last 12 s; two pacemakers firing within 0.6 s of each other are one beat (a new leader takes a few beats to capture the rest)
  M.rate = () => { const p = []; for (const q of M.pulses) if (M.t - q.t < 12 && (!p.length || q.t - p[p.length - 1].t > .6)) p.push(q); return p.length > 1 ? (p.length - 1) / (p[p.length - 1].t - p[0].t) * 60 : 0; };
  M.reset = () => { M.cuts.clear(); M.rh.forEach((r, i) => { r.silent = false; r.charge = (i * .37) % 1 * .6; r.led = 0; }); M.at.fill(Infinity); M.pulses.length = 0; };
  return M;
}
