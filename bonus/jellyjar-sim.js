// JELLY JAR: a moon jellyfish cast in gelatin, as a tetrahedral soft body.
// XPBD (Macklin, Müller & Chentanez 2016), after Müller's Ten Minute Physics soft bodies: every tetrahedron keeps its volume (incompressible),
// every edge resists stretching with a compliance (firmness), the floor grips, the jar's wall holds it in. A visible surface (and anything set
// in the jelly: film frames, gonads, bubbles) is embedded in the tetrahedra by barycentric coordinates, so it rides the flesh.
export function makeGel(o = {}) {
  const R = o.R || 1, H = o.H || .8, S = o.s || .2, JAR = o.jar || 1.55, G = -9.8;
  // the bell, as a solid: a dome over a hollow underside (the subumbrella), with a rim around it
  const inside = (x, y, z) => { const r = Math.hypot(x, z); if (r > R) return false; const top = H * Math.sqrt(Math.max(0, 1 - (r / R) ** 2)); if (y > top || y < 0) return false; if (r < .74 * R && y < .3 * H * (1 - (r / (.74 * R)) ** 2)) return false; return true; };
  const NX = Math.ceil(2 * R / S) + 1, NY = Math.ceil(H / S) + 1, NZ = NX, id = (i, j, k) => (k * NY + j) * NX + i, node = new Map();
  const P = [], tets = [];
  const nodeAt = (i, j, k) => { const key = id(i, j, k); if (!node.has(key)) { node.set(key, P.length / 3); P.push(-R + i * S, j * S, -R + k * S); } return node.get(key); };
  for (let i = 0; i < NX - 1; i++) for (let j = 0; j < NY - 1; j++) for (let k = 0; k < NZ - 1; k++) { const cx = -R + (i + .5) * S, cy = (j + .5) * S, cz = -R + (k + .5) * S; if (!inside(cx, cy, cz)) continue;
    const c = b => nodeAt(i + (b & 1), j + ((b >> 1) & 1), k + ((b >> 2) & 1));   // the cube's corners; split into 6 tetrahedra sharing the 0-7 diagonal, so neighbours conform
    for (const [a, b, d, e] of [[0, 1, 3, 7], [0, 1, 5, 7], [0, 2, 3, 7], [0, 2, 6, 7], [0, 4, 5, 7], [0, 4, 6, 7]]) tets.push(c(a), c(b), c(d), c(e)); }
  const N = P.length / 3, NT = tets.length / 4, X = new Float32Array(P), PREV = new Float32Array(N * 3), V = new Float32Array(N * 3), W = new Float32Array(N), TI = new Int32Array(tets), RV = new Float32Array(NT);
  const vol = (t, A = X) => { const a = TI[t * 4] * 3, b = TI[t * 4 + 1] * 3, c = TI[t * 4 + 2] * 3, d = TI[t * 4 + 3] * 3, e1 = [A[b] - A[a], A[b + 1] - A[a + 1], A[b + 2] - A[a + 2]], e2 = [A[c] - A[a], A[c + 1] - A[a + 1], A[c + 2] - A[a + 2]], e3 = [A[d] - A[a], A[d + 1] - A[a + 1], A[d + 2] - A[a + 2]];
    return ((e1[1] * e2[2] - e1[2] * e2[1]) * e3[0] + (e1[2] * e2[0] - e1[0] * e2[2]) * e3[1] + (e1[0] * e2[1] - e1[1] * e2[0]) * e3[2]) / 6; };
  const mass = new Float32Array(N); let REST = 0; for (let t = 0; t < NT; t++) { RV[t] = vol(t); REST += Math.abs(RV[t]); for (let q = 0; q < 4; q++) mass[TI[t * 4 + q]] += Math.abs(RV[t]) * 1000 / 4; }   /* gelatin: about the density of water, 1000 kg per cubic metre */ for (let i = 0; i < N; i++) W[i] = mass[i] > 0 ? 1 / mass[i] : 0;
  const ed = new Set(); for (let t = 0; t < NT; t++) for (const [p, q] of [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]) { const a = TI[t * 4 + p], b = TI[t * 4 + q]; ed.add(a < b ? a * 100000 + b : b * 100000 + a); }
  const EI = new Int32Array(ed.size * 2), EL = new Float32Array(ed.size); { let e = 0; for (const k of ed) { const a = Math.floor(k / 100000), b = k % 100000; EI[e * 2] = a; EI[e * 2 + 1] = b; EL[e] = Math.hypot(X[a * 3] - X[b * 3], X[a * 3 + 1] - X[b * 3 + 1], X[a * 3 + 2] - X[b * 3 + 2]); e++; } }
  const ORDER = [[1, 3, 2], [0, 2, 3], [0, 3, 1], [0, 1, 2]], gr = new Float32Array(12);
  const M = {N, NT, X, V, W, TI, mass, REST, firm: o.firm ?? .4, damp: o.damp ?? .3, EC: o.EC ?? 4e-3, EC0: o.EC0 ?? 1e-5, VC: o.VC ?? 0, grab: null, R, H, JAR, kinetic: 0};
  M.volume = () => { let v = 0; for (let t = 0; t < NT; t++) v += Math.abs(vol(t)); return v; };
  M.step = (dt, sub = 12) => { const h = dt / sub, ec = M.EC * Math.pow(1 - M.firm, 2.2) + M.EC0, ea = ec / (h * h), va = M.VC / (h * h), damp = Math.exp(-h * (.4 + 9 * M.damp * M.damp));
    for (let s = 0; s < sub; s++) {
      for (let i = 0; i < N; i++) { if (!W[i]) continue; const o3 = i * 3; V[o3 + 1] += G * h; for (let c = 0; c < 3; c++) { V[o3 + c] *= damp; PREV[o3 + c] = X[o3 + c]; X[o3 + c] += V[o3 + c] * h; } }
      if (M.grab) { const g = M.grab, o3 = g.i * 3; X[o3] = g.x; X[o3 + 1] = g.y; X[o3 + 2] = g.z; }
      // edges: stretching costs, as firm as you set it
      for (let e = 0; e < EL.length; e++) { const a = EI[e * 2], b = EI[e * 2 + 1], wa = W[a], wb = W[b], w = wa + wb; if (!w) continue; const dx = X[a * 3] - X[b * 3], dy = X[a * 3 + 1] - X[b * 3 + 1], dz = X[a * 3 + 2] - X[b * 3 + 2], L = Math.hypot(dx, dy, dz); if (L < 1e-9) continue; const lam = -(L - EL[e]) / (w + ea) / L;
        X[a * 3] += dx * lam * wa; X[a * 3 + 1] += dy * lam * wa; X[a * 3 + 2] += dz * lam * wa; X[b * 3] -= dx * lam * wb; X[b * 3 + 1] -= dy * lam * wb; X[b * 3 + 2] -= dz * lam * wb; }
      // volumes: gelatin is nearly incompressible
      for (let t = 0; t < NT; t++) { let w = 0; for (let j = 0; j < 4; j++) { const [p, q, r] = ORDER[j], A = TI[t * 4 + p] * 3, B = TI[t * 4 + q] * 3, C = TI[t * 4 + r] * 3, e1x = X[B] - X[A], e1y = X[B + 1] - X[A + 1], e1z = X[B + 2] - X[A + 2], e2x = X[C] - X[A], e2y = X[C + 1] - X[A + 1], e2z = X[C + 2] - X[A + 2];
          gr[j * 3] = (e1y * e2z - e1z * e2y) / 6; gr[j * 3 + 1] = (e1z * e2x - e1x * e2z) / 6; gr[j * 3 + 2] = (e1x * e2y - e1y * e2x) / 6; const wi = W[TI[t * 4 + j]]; w += wi * (gr[j * 3] ** 2 + gr[j * 3 + 1] ** 2 + gr[j * 3 + 2] ** 2); }
        if (w < 1e-12) continue; const lam = -(vol(t) - RV[t]) / (w + va);   /* a little give: perfectly incompressible tetrahedra lock */ for (let j = 0; j < 4; j++) { const i = TI[t * 4 + j], wi = W[i]; X[i * 3] += lam * wi * gr[j * 3]; X[i * 3 + 1] += lam * wi * gr[j * 3 + 1]; X[i * 3 + 2] += lam * wi * gr[j * 3 + 2]; } }
      // the floor grips; the jar's glass holds it in
      for (let i = 0; i < N; i++) { const o3 = i * 3; if (X[o3 + 1] < 0) { X[o3 + 1] = 0; X[o3] = PREV[o3] + (X[o3] - PREV[o3]) * .1; X[o3 + 2] = PREV[o3 + 2] + (X[o3 + 2] - PREV[o3 + 2]) * .1; } const r = Math.hypot(X[o3], X[o3 + 2]); if (r > JAR) { X[o3] *= JAR / r; X[o3 + 2] *= JAR / r; } }
      for (let i = 0; i < N; i++) { const o3 = i * 3; for (let c = 0; c < 3; c++) V[o3 + c] = (X[o3 + c] - PREV[o3 + c]) / h; } }
    let k = 0; for (let i = 0; i < N; i++) if (W[i]) k += .5 * mass[i] * (V[i * 3] ** 2 + V[i * 3 + 1] ** 2 + V[i * 3 + 2] ** 2); M.kinetic = k; };
  // grabbing: the nearest particle follows the hand (its weight set aside); letting go flings it with the hand's last speed
  M.pick = (x, y, z) => { let bi = -1, bd = 1e9; for (let i = 0; i < N; i++) { const d = (X[i * 3] - x) ** 2 + (X[i * 3 + 1] - y) ** 2 + (X[i * 3 + 2] - z) ** 2; if (d < bd) { bd = d; bi = i; } } return bi; };
  M.hold = (i, x, y, z) => { if (!M.grab || M.grab.i !== i) { if (M.grab) M.release(); M.grab = {i, w: W[i], x, y, z, hist: []}; W[i] = 0; } const g = M.grab, t = performance.now(); g.hist.push([x, y, z, t]); if (g.hist.length > 6) g.hist.shift(); g.x = x; g.y = y; g.z = z; };
  M.release = () => { const g = M.grab; if (!g) return; W[g.i] = g.w; const a = g.hist[0], b = g.hist[g.hist.length - 1], dt = Math.max(.016, (b[3] - a[3]) / 1000); if (a && b) { V[g.i * 3] = (b[0] - a[0]) / dt; V[g.i * 3 + 1] = (b[1] - a[1]) / dt; V[g.i * 3 + 2] = (b[2] - a[2]) / dt; } M.grab = null; };
  M.nudge = (k = 2.5) => { for (let i = 0; i < N; i++) { V[i * 3 + 1] += k * (X[i * 3 + 1] / H); V[i * 3] += Math.sin(i) * k * .2; } };
  // embedding: each point of a mesh is tied to the tetrahedron that holds it (or the nearest), by barycentric coordinates
  M.embed = pts => { const n = pts.length / 3, T = new Int32Array(n), B = new Float32Array(n * 4); const ctr = new Float32Array(NT * 3); for (let t = 0; t < NT; t++) for (let q = 0; q < 4; q++) for (let c = 0; c < 3; c++) ctr[t * 3 + c] += X[TI[t * 4 + q] * 3 + c] / 4;
    for (let v = 0; v < n; v++) { const px = pts[v * 3], py = pts[v * 3 + 1], pz = pts[v * 3 + 2]; let best = -1, bm = -1e9, bb = null;
      for (let t = 0; t < NT; t++) { if ((ctr[t * 3] - px) ** 2 + (ctr[t * 3 + 1] - py) ** 2 + (ctr[t * 3 + 2] - pz) ** 2 > (S * 2.2) ** 2) continue; const bc = bary(t, px, py, pz), m = Math.min(...bc); if (m > bm) { bm = m; best = t; bb = bc; } }
      if (best < 0) { let bd = 1e9; for (let t = 0; t < NT; t++) { const d = (ctr[t * 3] - px) ** 2 + (ctr[t * 3 + 1] - py) ** 2 + (ctr[t * 3 + 2] - pz) ** 2; if (d < bd) { bd = d; best = t; } } bb = bary(best, px, py, pz); }
      T[v] = best; B.set(bb, v * 4); } return {T, B, n}; };
  function bary(t, px, py, pz) { const a = TI[t * 4] * 3, b = TI[t * 4 + 1] * 3, c = TI[t * 4 + 2] * 3, d = TI[t * 4 + 3] * 3; const m = [X[a] - X[d], X[b] - X[d], X[c] - X[d], X[a + 1] - X[d + 1], X[b + 1] - X[d + 1], X[c + 1] - X[d + 1], X[a + 2] - X[d + 2], X[b + 2] - X[d + 2], X[c + 2] - X[d + 2]];
    const det = m[0] * (m[4] * m[8] - m[5] * m[7]) - m[1] * (m[3] * m[8] - m[5] * m[6]) + m[2] * (m[3] * m[7] - m[4] * m[6]); if (Math.abs(det) < 1e-12) return [.25, .25, .25, .25]; const rx = px - X[d], ry = py - X[d + 1], rz = pz - X[d + 2];
    const l0 = (rx * (m[4] * m[8] - m[5] * m[7]) - m[1] * (ry * m[8] - m[5] * rz) + m[2] * (ry * m[7] - m[4] * rz)) / det, l1 = (m[0] * (ry * m[8] - m[5] * rz) - rx * (m[3] * m[8] - m[5] * m[6]) + m[2] * (m[3] * rz - ry * m[6])) / det, l2 = (m[0] * (m[4] * rz - ry * m[7]) - m[1] * (m[3] * rz - ry * m[6]) + rx * (m[3] * m[7] - m[4] * m[6])) / det; return [l0, l1, l2, 1 - l0 - l1 - l2]; }
  M.apply = (emb, out) => { const {T, B, n} = emb; for (let v = 0; v < n; v++) { const t = T[v]; let x = 0, y = 0, z = 0; for (let q = 0; q < 4; q++) { const i = TI[t * 4 + q] * 3, b = B[v * 4 + q]; x += X[i] * b; y += X[i + 1] * b; z += X[i + 2] * b; } out[v * 3] = x; out[v * 3 + 1] = y; out[v * 3 + 2] = z; } };
  M.inside = inside; return M;
}
