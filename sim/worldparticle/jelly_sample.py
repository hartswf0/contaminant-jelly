"""A moon jellyfish as a WorldParticle sample.

Writes ground-truth trajectories in WorldParticle's `elastic_drag` NPZ layout
(see https://github.com/WorldParticle/WorldParticle, README "NPZ Particle Data"):

  position [T, N, 3], velocity [T, N, 3], feats [N, 6], box [M, 3], box_feats [M, 3],
  neighbors_index [E], neighbors_row_splits [N + 1], force [T, N, 3]

The body is an elastic particle system:
- the bell is a two-layer shell (exumbrella and subumbrella);
- 16 marginal tentacles and 4 oral arms are particle chains;
- the neighbour graph is the topology the model's topology convolution reads.

The simulator (position-based dynamics with distance constraints, water drag, and a tank) produces the motion.

`force` is a per-particle acceleration that, in WorldParticle's physics step, replaces gravity. It carries what acts on the body from outside its own elasticity:
- buoyancy (the net sink);
- the coronal muscle's squeeze of the rim;
- the jet's reaction, from how fast the bell closes;
- in the `drag` sample, a pull on one tentacle tip.

Water drag stays inside the simulator, for the model to learn.

Usage:
  python3 jelly_sample.py --out DATA_ROOT [--web ../../bonus/wp]
"""
import argparse, json, os
import numpy as np

S = 0.009            # particle spacing (m): neighbours sit inside WorldParticle's topology radius
R, H = 0.06, 0.032   # bell radius and height (m): a 12 cm moon jelly
FPS, T = 100, 600    # 0.01 s frames (config.yaml timestep), 6 s
SUB, ITERS = 10, 4   # substeps per frame, constraint iterations per substep


def build():
    P, part, ring, phi_of = [], [], [], []
    TH = 1.25
    nth = 8
    rims = {}
    for layer, (sc, dy) in enumerate([(1.0, 0.0), (0.82, -0.006)]):
        P.append([0.0, H * sc + dy, 0.0]); part.append(0); ring.append(0); phi_of.append(0.0)
        for i in range(1, nth + 1):
            th = TH * i / nth
            r = R * sc * np.sin(th)
            y = H * sc * np.cos(th) + dy
            n = max(6, int(round(2 * np.pi * r / S)))
            for k in range(n):
                ph = 2 * np.pi * (k + 0.5 * (i % 2)) / n
                P.append([r * np.cos(ph), y, r * np.sin(ph)]); part.append(0); ring.append(i); phi_of.append(ph)
                if i == nth and layer == 0:
                    rims.setdefault('outer', []).append(len(P) - 1)
    P = np.array(P)
    nb = len(P)
    # tentacles: 16 chains hanging from the outer rim
    rim = np.array(rims['outer'])
    chains = []
    for t in range(16):
        ph = 2 * np.pi * t / 16
        a = rim[np.argmin(np.abs(np.angle(np.exp(1j * (np.array(phi_of)[rim] - ph)))))]
        base = P[a]
        ch = [a]
        for j in range(1, 29):
            q = base + np.array([np.cos(ph) * 0.002 * j, -S * j, np.sin(ph) * 0.002 * j])
            P = np.vstack([P, q]); part.append(1); ring.append(100 + j); phi_of.append(ph); ch.append(len(P) - 1)
        chains.append(ch)
    # oral arms: 4 chains from the subumbrella's centre
    sub_top = np.where((np.array(part[:nb]) == 0) & (np.arange(nb) >= nb // 2))[0]
    centre = sub_top[np.argmin(np.linalg.norm(P[sub_top][:, [0, 2]], axis=1))]
    for t in range(4):
        ph = 2 * np.pi * t / 4 + np.pi / 4
        ch = [centre]
        for j in range(1, 15):
            q = P[centre] + np.array([np.cos(ph) * 0.004 * min(j, 4), -S * j, np.sin(ph) * 0.004 * min(j, 4)])
            P = np.vstack([P, q]); part.append(2); ring.append(200 + j); phi_of.append(ph); ch.append(len(P) - 1)
        chains.append(ch)
    part = np.array(part); ring = np.array(ring); phi_of = np.array(phi_of)
    # topology: bell particles within 1.6 S of each other; chain links; each chain's first link joins the bell
    edges = set()
    bell = np.where(part == 0)[0]
    Bp = P[bell]
    d = np.linalg.norm(Bp[:, None] - Bp[None], axis=-1)
    ii, jj = np.where((d < 1.6 * S) & (d > 0))
    for a, b in zip(bell[ii], bell[jj]):
        edges.add((min(a, b), max(a, b)))
    bend = []
    for ch in chains:
        for a, b in zip(ch[:-1], ch[1:]):
            edges.add((min(a, b), max(a, b)))
        bend += [(a, c) for a, c in zip(ch[:-2], ch[2:])]
    edges = np.array(sorted(edges))
    return P, part, ring, phi_of, edges, np.array(bend), rim, chains


def csr(n, edges):
    nbrs = [[] for _ in range(n)]
    for a, b in edges:
        nbrs[a].append(b); nbrs[b].append(a)
    idx, splits = [], [0]
    for l in nbrs:
        idx += sorted(l); splits.append(len(idx))
    return np.array(idx, dtype=np.int64), np.array(splits, dtype=np.int64)


def tank(half=0.25, floor=-0.6, top=0.36, sp=0.012):   # floor, four walls and a lid, as obstacle points with inward normals
    pts, nrm = [], []
    g = np.arange(-half, half + 1e-9, sp)
    for x in g:
        for z in g:
            pts.append([x, floor, z]); nrm.append([0, 1, 0])
    hs = np.arange(floor, top + 1e-9, sp)
    for s in g:
        for y in hs:
            pts += [[-half, y, s], [half, y, s], [s, y, -half], [s, y, half]]
            nrm += [[1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1]]
    for x in g:
        for z in g:
            pts.append([x, top, z]); nrm.append([0, -1, 0])
    return np.array(pts, np.float32), np.array(nrm, np.float32), half, floor, top


def simulate(kind, seed=0):
    P0, part, ring, phi_of, edges, bend, rim, chains = build()
    n = len(P0)
    box, box_n, half, floor, top = tank()
    rest = np.linalg.norm(P0[edges[:, 0]] - P0[edges[:, 1]], axis=1)
    brest = np.linalg.norm(P0[bend[:, 0]] - P0[bend[:, 1]], axis=1)
    # stiffness per edge: the bell's mesoglea is stiff; tentacles are soft
    ek = np.where((part[edges[:, 0]] == 0) & (part[edges[:, 1]] == 0), 0.9, 0.5)
    drag = np.where(part == 0, 2.0, np.where(part == 1, 4.0, 3.0))[:, None]
    sink = np.where(part == 0, -0.01, -0.04)[:, None]   # net of gravity and buoyancy (m/s^2): a jelly is nearly neutral
    period, squeeze = (1.0, 0.3)
    bias = np.zeros(n)
    if kind == 'turn':
        bias = 0.7 * np.cos(phi_of)        # the +x side squeezes harder: it turns
    ring_w = np.where(part == 0, np.clip((ring - 4) / 4.0, 0, 1), 0)[:, None]
    tip = chains[3][-1]
    x = P0.copy() + np.array([0.0, -0.13, 0.0]); v = np.zeros_like(x)   # it starts low in the tank (its tentacles clear of the floor) and swims up
    X, Vv, Fo = np.zeros((T, n, 3), np.float32), np.zeros((T, n, 3), np.float32), np.zeros((T, n, 3), np.float32)
    rim_r_prev = None
    h = 1.0 / FPS / SUB
    for f in range(T):
        t = f / FPS
        ph = (t % period) / period
        pulse = np.sin(np.pi * ph / squeeze) ** 2 if ph < squeeze else 0.0
        # the bell's axis and the rim's radius, from the state
        apex = x[0]; rc = x[rim].mean(0); axis = apex - rc; axis /= np.linalg.norm(axis) + 1e-9
        rr = np.linalg.norm((x[rim] - rc) - np.outer((x[rim] - rc) @ axis, axis), axis=1).mean()
        rr_s = rr if rim_r_prev is None else rim_r_prev * 0.6 + rr * 0.4   # a smoothed rim radius, so jitter is not thrust
        closing = 0.0 if rim_r_prev is None or pulse <= 0 else max(0.0, (rim_r_prev - rr_s) * FPS)   # only the squeeze throws water
        rim_r_prev = rr_s
        a = np.zeros_like(x); a[:] += sink * np.array([0, 1, 0])
        # the coronal muscle: the lower bell squeezes toward the axis
        bc = x[part == 0].mean(0)
        rad = x - bc; rad -= np.outer(rad @ axis, axis); rad /= (np.linalg.norm(rad, axis=1, keepdims=True) + 1e-9)
        a += -rad * (40.0 * pulse) * ring_w * (1 + bias)[:, None]
        # the jet: water thrown out of the closing bell pushes the bell along its axis
        a[part == 0] += axis * min(1.0, 5.0 * closing)
        if kind == 'drag' and 2.0 <= t < 3.6:
            a[tip] += np.array([1.0, 0.25, 0.0]) * 14.0     # an outside pull on one tentacle tip
        Fo[f] = a
        for _ in range(SUB):
            v += h * a
            v *= np.exp(-h * drag)
            xp = x + h * v
            for _ in range(ITERS):
                for E, L0, k in ((edges, rest, ek), (bend, brest, 0.25)):
                    d = xp[E[:, 1]] - xp[E[:, 0]]; ln = np.linalg.norm(d, axis=1) + 1e-9
                    c = ((ln - L0) / ln * 0.5 * k)[:, None] * d
                    acc = np.zeros_like(xp); cnt = np.zeros(n)
                    np.add.at(acc, E[:, 0], c); np.add.at(acc, E[:, 1], -c)
                    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
                    xp += acc / np.maximum(cnt, 1)[:, None] * 1.6
                xp[:, 1] = np.clip(xp[:, 1], floor + 0.004, top - 0.004)   # the tank's floor and its lid
                xp[:, [0, 2]] = np.clip(xp[:, [0, 2]], -half + 0.004, half - 0.004)
            v = (xp - x) / h; x = xp
        X[f], Vv[f] = x, v
    feats = np.stack([np.ones(n), part, ring, np.cos(phi_of), np.sin(phi_of), np.where(part == 0, 0.9, 0.5)], 1).astype(np.float32)
    ni, ns = csr(n, edges)
    return dict(position=X, velocity=Vv, feats=feats, box=box, box_feats=box_n, neighbors_index=ni, neighbors_row_splits=ns, force=Fo), part, edges


def export_web(name, data, part, out, stride=2):
    """A compact copy for the browser viewer: int16 positions in the tank's bounds, every `stride` frames."""
    X = data['position'][::stride]
    lo, hi = X.reshape(-1, 3).min(0), X.reshape(-1, 3).max(0)
    q = np.round((X - lo) / np.maximum(hi - lo, 1e-6) * 65535 - 32768).astype(np.int16)
    os.makedirs(out, exist_ok=True)
    q.tofile(os.path.join(out, name + '.bin'))
    meta = dict(name=name, frames=int(X.shape[0]), n=int(X.shape[1]), fps=FPS // stride, lo=lo.tolist(), hi=hi.tolist(), part=part.astype(int).tolist(),
                tank=dict(half=0.25, floor=-0.6, top=0.36))
    json.dump(meta, open(os.path.join(out, name + '.json'), 'w'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='data')
    ap.add_argument('--web', default=None)
    a = ap.parse_args()
    for kind in ('straight', 'turn', 'drag'):
        name = f'jelly_{kind}'
        data, part, edges = simulate(kind)
        os.makedirs(os.path.join(a.out, name), exist_ok=True)
        np.savez_compressed(os.path.join(a.out, name, name + '.npz'), **data)
        X = data['position']; bell = part == 0
        c0, c1 = X[0][bell].mean(0), X[-1][bell].mean(0)
        print(f'{name}: N={X.shape[1]} E={len(edges)} T={X.shape[0]} bell moved {np.round((c1 - c0) * 100, 1).tolist()} cm')
        if a.web:
            export_web(name, data, part, a.web)
