// FILM MATTER: one particle system in which a film's frame is a sheet, a liquid, or a sand, and a jellyfish swims through it.
// Unified position-based dynamics, after Macklin & Müller (Position Based Fluids, 2013) and Macklin et al. (Unified Particle Physics, 2014):
//   FILM  - distance constraints along the frame's grid, the top row pinned: a hanging sheet;
//   WATER - a density constraint per particle (PBF), artificial pressure, XSPH viscosity;
//   SAND  - contact constraints between touching particles, with friction;
//   HOME  - every particle is drawn back to its place in the frame, and the picture reassembles.
// Each particle keeps its place (u, v) in the frame, so the film can go on playing in whatever the particles have become.
export function makeMatter(o = {}) {
  const NX = o.nx || 64, NY = o.ny || 48, N = NX * NY, r = o.r || .05, D = 2 * r, h = 1.7 * D;
  const BW = (NX * D) / 2 + .35, TOP = NY * D + .9, BZ = o.depth || .22;   // the tank: half-width, height, half-depth (a slab, so the picture stays readable)
  const X = new Float32Array(N * 3), P = new Float32Array(N * 3), V = new Float32Array(N * 3), HOME = new Float32Array(N * 3), dP = new Float32Array(N * 3), LAM = new Float32Array(N), RHO = new Float32Array(N);
  for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) { const k = j * NX + i; HOME.set([(i - (NX - 1) / 2) * D, TOP - .45 - j * D, 0], k * 3); }
  X.set(HOME); P.set(HOME);
  // kernels
  const H2 = h * h, POLY = 315 / (64 * Math.PI * h ** 9), SPIKY = -45 / (Math.PI * h ** 6), W = q2 => q2 >= H2 ? 0 : POLY * (H2 - q2) ** 3;
  let RHO0 = 0; { const n = Math.ceil(h / D); for (let a = -n; a <= n; a++) for (let b = -n; b <= n; b++) for (let c = -n; c <= n; c++) RHO0 += W((a * a + b * b + c * c) * D * D); }   // rest density of a cubic packing at spacing D
  const WDQ = W((.2 * h) ** 2);
  // the neighbour grid
  const CS = h, GX = Math.ceil(2 * BW / CS) + 2, GY = Math.ceil(TOP / CS) + 2, GZ = Math.ceil(2 * BZ / CS) + 2, NC = GX * GY * GZ, cStart = new Int32Array(NC + 1), cIdx = new Int32Array(N), cOf = new Int32Array(N);
  const MAXN = 64, NB = new Int32Array(N * MAXN), NBc = new Int32Array(N);
  const cell = (x, y, z) => { const a = Math.min(GX - 1, Math.max(0, Math.floor((x + BW) / CS) + 1)), b = Math.min(GY - 1, Math.max(0, Math.floor(y / CS) + 1)), c = Math.min(GZ - 1, Math.max(0, Math.floor((z + BZ) / CS) + 1)); return (c * GY + b) * GX + a; };
  function neighbours() { cStart.fill(0); for (let i = 0; i < N; i++) { const c = cell(P[i * 3], P[i * 3 + 1], P[i * 3 + 2]); cOf[i] = c; cStart[c + 1]++; } for (let c = 0; c < NC; c++) cStart[c + 1] += cStart[c]; const fill = cStart.slice(0, NC); for (let i = 0; i < N; i++) cIdx[fill[cOf[i]]++] = i;
    for (let i = 0; i < N; i++) { const c = cOf[i], a = c % GX, b = ((c / GX) | 0) % GY, cz = (c / (GX * GY)) | 0, xi = P[i * 3], yi = P[i * 3 + 1], zi = P[i * 3 + 2]; let n = 0;
      for (let dz = -1; dz <= 1; dz++) for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const A = a + dx, B = b + dy, Cz = cz + dz; if (A < 0 || B < 0 || Cz < 0 || A >= GX || B >= GY || Cz >= GZ) continue; const cc = (Cz * GY + B) * GX + A;
        for (let q = cStart[cc]; q < cStart[cc + 1]; q++) { const j = cIdx[q]; if (j === i) continue; const ex = P[j * 3] - xi, ey = P[j * 3 + 1] - yi, ez = P[j * 3 + 2] - zi; if (ex * ex + ey * ey + ez * ez < H2 && n < MAXN) NB[i * MAXN + n++] = j; } }
      NBc[i] = n; } }
  // the sheet's springs: right, down and both diagonals
  const SP = []; for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) { const k = j * NX + i; if (i < NX - 1) SP.push(k, k + 1); if (j < NY - 1) SP.push(k, k + NX); if (i < NX - 1 && j < NY - 1) SP.push(k, k + NX + 1); if (i > 0 && j < NY - 1) SP.push(k, k + NX - 1); }
  const SPR = new Int32Array(SP), SPL = new Float32Array(SPR.length / 2); for (let e = 0; e < SPL.length; e++) { const a = SPR[e * 2], b = SPR[e * 2 + 1]; SPL[e] = Math.hypot(HOME[a * 3] - HOME[b * 3], HOME[a * 3 + 1] - HOME[b * 3 + 1]); }
  const M = {N, NX, NY, r, D, h, BW, TOP, BZ, X, V, HOME, RHO, state: 'film', t: 0, jelly: {x: 0, y: 1.2, z: 0, vx: 0, vy: 0, R: .42, kick: 0}, g: -9.8, mu: .55, visc: .05, eps: 600, RHO0: 0, k: 600, kn: 300, rho0: 3.2};
  function bounds(i, sand) { const o3 = i * 3; let hitF = false; if (P[o3] < -BW + r) P[o3] = -BW + r; if (P[o3] > BW - r) P[o3] = BW - r; if (P[o3 + 2] < -BZ + r) P[o3 + 2] = -BZ + r; if (P[o3 + 2] > BZ - r) P[o3 + 2] = BZ - r; if (P[o3 + 1] < r) { P[o3 + 1] = r; hitF = true; } if (P[o3 + 1] > TOP) P[o3 + 1] = TOP;
    if (hitF && sand) { P[o3] = X[o3] + (P[o3] - X[o3]) * .2; P[o3 + 2] = X[o3 + 2] + (P[o3 + 2] - X[o3 + 2]) * .2; } }   // sand grips the floor
  function jelly(i) { const J = M.jelly, o3 = i * 3, ex = P[o3] - J.x, ey = P[o3 + 1] - J.y, ez = P[o3 + 2] - J.z, d = Math.hypot(ex, ey, ez); if (d < J.R && d > 1e-6) { const s = J.R / d; P[o3] = J.x + ex * s; P[o3 + 1] = J.y + ey * s; P[o3 + 2] = J.z + ez * s; } }
  M.RHO0 = RHO0; M.set = s => { M.state = s; if (s === 'home') M.homeT = 0; };
  M.step = (dt, sub = 2, iters = 3) => { const h1 = dt / sub, J = M.jelly; M.t += dt;
    J.x = Math.max(-BW + J.R, Math.min(BW - J.R, J.x + J.vx * dt)); J.y = Math.max(J.R, Math.min(TOP - J.R, J.y + J.vy * dt));
    for (let s = 0; s < sub; s++) { const st = M.state, film = st === 'film', water = st === 'water', sand = st === 'sand', home = st === 'home';
      // forces and prediction
      for (let i = 0; i < N; i++) { const o3 = i * 3; if (home) { for (let c = 0; c < 3; c++) V[o3 + c] += ((HOME[o3 + c] - X[o3 + c]) * 9 - V[o3 + c] * 4) * h1; } else V[o3 + 1] += M.g * h1;
        if (J.kick > 0) { const ex = X[o3] - J.x, ey = X[o3 + 1] - J.y, ez = X[o3 + 2] - J.z, d = Math.hypot(ex, ey, ez); if (d < 1.4 && d > 1e-4) { const f = J.kick * (1 - d / 1.4) / d; V[o3] += ex * f; V[o3 + 1] += ey * f - J.kick * .25 * (1 - d / 1.4); V[o3 + 2] += ez * f * .3; } }
        P[o3] = X[o3] + V[o3] * h1; P[o3 + 1] = X[o3 + 1] + V[o3 + 1] * h1; P[o3 + 2] = X[o3 + 2] + V[o3 + 2] * h1; }
      J.kick = 0; if (water || sand) neighbours();
      for (let it = 0; it < iters; it++) {
        if (film) { for (let e = 0; e < SPL.length; e++) { const a = SPR[e * 2] * 3, b = SPR[e * 2 + 1] * 3, ex = P[b] - P[a], ey = P[b + 1] - P[a + 1], ez = P[b + 2] - P[a + 2], d = Math.hypot(ex, ey, ez) || 1e-6, c = (d - SPL[e]) / d * .5 * .9; P[a] += ex * c; P[a + 1] += ey * c; P[a + 2] += ez * c; P[b] -= ex * c; P[b + 1] -= ey * c; P[b + 2] -= ez * c; }
          for (let i = 0; i < NX; i++) { P[i * 3] = HOME[i * 3]; P[i * 3 + 1] = HOME[i * 3 + 1]; P[i * 3 + 2] = HOME[i * 3 + 2]; }   // the top row is pinned: the frame hangs
          for (let k = NX * 3; k < N * 3; k++) P[k] += (HOME[k] - P[k]) * .12; }   // and each particle springs back toward its place: a screen the jelly can push through
        if (water && it === 0) { // double density relaxation (Clavet, Beaudoin & Poulin 2005): pressure from crowding, a near-pressure against clumping; one sweep, applied at once
          const dt2 = h1 * h1; for (let i = 0; i < N; i++) { const o3 = i * 3; let rho = 0, rn = 0; for (let q = 0; q < NBc[i]; q++) { const j = NB[i * MAXN + q] * 3, d = Math.hypot(P[j] - P[o3], P[j + 1] - P[o3 + 1], P[j + 2] - P[o3 + 2]), u = 1 - d / h; if (u > 0) { rho += u * u; rn += u * u * u; } } RHO[i] = rho;
            const pr = M.k * Math.max(0, rho - M.rho0), pn = M.kn * rn; /* crowding pushes; a sparse liquid does not pull itself together */ for (let q = 0; q < NBc[i]; q++) { const j = NB[i * MAXN + q] * 3, ex = P[j] - P[o3], ey = P[j + 1] - P[o3 + 1], ez = P[j + 2] - P[o3 + 2], d = Math.hypot(ex, ey, ez) || 1e-6, u = 1 - d / h; if (u <= 0) continue; const m = Math.min(r, dt2 * (pr * u + pn * u * u)) * .5 / d; P[j] += ex * m; P[j + 1] += ey * m; P[j + 2] += ez * m; P[o3] -= ex * m; P[o3 + 1] -= ey * m; P[o3 + 2] -= ez * m; } } }
        if (sand) { for (let i = 0; i < N; i++) { const o3 = i * 3; for (let q = 0; q < NBc[i]; q++) { const jj = NB[i * MAXN + q]; if (jj < i) continue; const j = jj * 3, ex = P[j] - P[o3], ey = P[j + 1] - P[o3 + 1], ez = P[j + 2] - P[o3 + 2], d = Math.hypot(ex, ey, ez); if (d >= D || d < 1e-6) continue; const pen = D - d, nx = ex / d, ny = ey / d, nz = ez / d;
            let cx = -nx * pen * .5, cy = -ny * pen * .5, cz = -nz * pen * .5;   // push apart
            const rx = (P[o3] - X[o3]) - (P[j] - X[j]), ry = (P[o3 + 1] - X[o3 + 1]) - (P[j + 1] - X[j + 1]), rz = (P[o3 + 2] - X[o3 + 2]) - (P[j + 2] - X[j + 2]), rn = rx * nx + ry * ny + rz * nz, tx = rx - rn * nx, ty = ry - rn * ny, tz = rz - rn * nz, tl = Math.hypot(tx, ty, tz);
            if (tl > 1e-7) { const k = Math.min(1, M.mu * pen / tl) * .5; cx -= tx * k; cy -= ty * k; cz -= tz * k; }   // friction: the grains hold against sliding
            P[o3] += cx; P[o3 + 1] += cy; P[o3 + 2] += cz; P[j] -= cx; P[j + 1] -= cy; P[j + 2] -= cz; } } }   // applied at once (Gauss-Seidel), so a pile holds itself up
        for (let i = 0; i < N; i++) { jelly(i); bounds(i, sand); } }
      // velocities from positions; the liquid's viscosity; the sand's damping
      for (let k = 0; k < N * 3; k++) { V[k] = Math.max(-14, Math.min(14, (P[k] - X[k]) / h1)); X[k] = P[k]; }
      if (water) { dP.fill(0); for (let i = 0; i < N; i++) { const o3 = i * 3; for (let q = 0; q < NBc[i]; q++) { const j = NB[i * MAXN + q] * 3, ex = X[o3] - X[j], ey = X[o3 + 1] - X[j + 1], ez = X[o3 + 2] - X[j + 2], w = W(ex * ex + ey * ey + ez * ez) / RHO0; for (let c = 0; c < 3; c++) dP[o3 + c] += (V[j + c] - V[o3 + c]) * w; } } for (let k = 0; k < N * 3; k++) V[k] += dP[k] * M.visc; }
      if (sand) for (let k = 0; k < N * 3; k++) V[k] *= .995;
      if (film) for (let k = 0; k < N * 3; k++) V[k] *= .985; }
    if (M.state === 'home') { let e = 0; for (let k = 0; k < N * 3; k++) e += Math.abs(HOME[k] - X[k]); M.homeErr = e / N; M.homeT = (M.homeT || 0) + dt; if (M.homeErr < .02 || M.homeT > 5) { M.state = 'film'; } } };
  M.pulse = (k = 3.5) => { M.jelly.kick = k; };
  return M;
}
