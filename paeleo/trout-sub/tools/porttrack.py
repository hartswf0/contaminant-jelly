#!/usr/bin/env python3
"""porttrack: find the brass porthole in the first and last frames of each film.

    python3 tools/porttrack.py            # every film in films/, writes ports.json
    python3 tools/porttrack.py p07 p21

For each film it samples three frames in the opening 0.5 s and three in the
closing 0.5 s, and finds the brass rim by matching the rim annulus cut from the
two masters (bolts, hinge, latch; the glass is masked out) at every size.
ports.json holds the centre and outer rim radius as fractions of frame width, plus a fit score.
tools/units.py uses it to lock the port to one place and size at both ends.
"""
import json, os, subprocess, sys
import cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
W, H = 480, 270
ANG = np.linspace(0, 2 * np.pi, 64, endpoint=False)
COS, SIN = np.cos(ANG), np.sin(ANG)


def frame(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", path, "-frames:v", "1",
                          "-vf", "scale=%d:%d" % (W, H), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3) if len(raw) == W * H * 3 else None


# The two masters carry the same port. Its rim (outer-edge circle) was measured
# by hand on each: centre x, centre y, outer radius, in 1344x768 pixels.
MASTERS = {"masters/cockpit.jpg": (670, 356, 195), "masters/outside.jpg": (675, 387, 268)}
GLASS = 0.77          # glass radius / outer rim radius
TSIZE = 128           # template is the rim annulus at outer radius 56 px in a 128 px tile
_T = []


def templates():
    """Rim annulus (bolts, hinge, latch) cut from each master; the glass is masked out."""
    if not _T:
        for path, (cx, cy, r) in MASTERS.items():
            im = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
            half = int(r * TSIZE / 112.0)
            tile = cv2.resize(im[cy - half:cy + half, cx - half:cx + half], (TSIZE, TSIZE), interpolation=cv2.INTER_AREA)
            yy, xx = np.mgrid[:TSIZE, :TSIZE] - TSIZE / 2.0
            d = np.hypot(xx, yy)
            mask = ((d > 56 * (GLASS - 0.04)) & (d < 56 * 1.12)).astype(np.uint8) * 255
            _T.append((tile, mask))
    return _T


def match(gray, r, pad, box=None):
    """Best place for the rim at outer radius r in a padded grey image: (score, cx, cy)."""
    n = max(16, int(round(TSIZE * r / 56.0)))
    best = (-1.0, 0.0, 0.0)
    if n >= min(gray.shape):
        return best
    for tile, mask in templates():
        t = cv2.resize(tile, (n, n), interpolation=cv2.INTER_AREA)
        k = cv2.resize(mask, (n, n), interpolation=cv2.INTER_NEAREST)
        res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED, mask=k)
        res[~np.isfinite(res) | (res > 1.01)] = -1
        if box is not None:          # keep only centres inside box = (x0, y0, x1, y1), unpadded pixels
            x0, y0, x1, y1 = [int(round(v + pad - n / 2.0)) for v in box]
            keep = np.zeros(res.shape, bool)
            keep[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
            res[~keep] = -1
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), loc[0] - pad + n / 2.0, loc[1] - pad + n / 2.0)
    return best


# Where the port may sit, per end of the film: outer rim radius range and centre box,
# as fractions of frame width. Every film is generated from the same two masters, so
# the port opens near (0.50, 0.26) r 0.145 and closes near (0.50, 0.285) r 0.20.
SEARCH = {"start": ((0.12, 0.20), (0.40, 0.16, 0.60, 0.36)),
          "end": ((0.15, 0.32), (0.30, 0.14, 0.70, 0.44)),
          "any": ((0.12, 0.50), (0.15, 0.05, 0.85, 0.52))}


def fit(img, key):
    (rlo, rhi), box = SEARCH[key]
    RMIN, RMAX = rlo * W, rhi * W
    box = [v * W for v in box]
    """Coarse scan of rim sizes at half resolution, then a fine scan around the hit."""
    g = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    half = cv2.resize(g, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    pad = 60
    hp = cv2.copyMakeBorder(half, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=int(g.mean()))
    radii = list(np.arange(RMIN, RMAX, 4.0))
    sc = [match(hp, r / 2.0, pad, [v / 2.0 for v in box]) for r in radii]
    i = int(np.argmax([x[0] for x in sc]))
    r0, cx0, cy0 = radii[i], sc[i][1] * 2, sc[i][2] * 2
    pad = 120
    gp = cv2.copyMakeBorder(g, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=int(g.mean()))
    m = int(r0 * 1.25 + 14)
    x0, y0 = max(0, int(cx0 + pad - m)), max(0, int(cy0 + pad - m))
    roi = gp[y0:int(cy0 + pad + m), x0:int(cx0 + pad + m)]
    best = (-1.0, cx0, cy0, r0)
    for r in np.arange(max(RMIN, r0 - 4), r0 + 4.1, 1.0):
        s_, x, y = match(roi, r, 0)
        if s_ > best[0]:
            best = (s_, x + x0 - pad, y + y0 - pad, float(r))
    return best[1], best[2], best[3], best[0]


def fit_near(img, prev):
    """Follow the rim from where it was in the previous frame: (cx, cy, r, score) in 480-wide pixels."""
    g = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    pcx, pcy, pr = prev
    pad = 160
    gp = cv2.copyMakeBorder(g, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=int(g.mean()))
    f = 1.0 if pr < 90 else 0.5                   # big rims are matched at half size for speed
    if f != 1.0:
        gp = cv2.resize(gp, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    m = pr * 1.35 + 24
    x0, y0 = max(0, int((pcx + pad - m) * f)), max(0, int((pcy + pad - m) * f))
    roi = gp[y0:int((pcy + pad + m) * f), x0:int((pcx + pad + m) * f)]
    best = (-1.0, pcx, pcy, pr)
    for q in (0.92, 0.96, 0.985, 1.0, 1.015, 1.04, 1.08):
        s_, x, y = match(roi, pr * q * f, 0)
        if s_ > best[0]:
            best = (s_, (x + x0) / f - pad, (y + y0) / f - pad, pr * q)
    return best[1], best[2], best[3], best[0]


def track(pid, src=None):
    path = src or "films/%s.mp4" % pid
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    out = {"duration": round(dur, 3)}
    for key, times in (("start", (0.05, 0.25, 0.5)), ("end", (dur - 0.55, dur - 0.3, dur - 0.1))):
        fits = []
        for t in times:
            img = frame(path, t)
            if img is not None:
                fits.append(fit(img, key))
        if not fits:
            continue
        a = np.array(fits)
        out[key] = {"cx": round(float(np.median(a[:, 0])) / W, 5), "cy": round(float(np.median(a[:, 1])) / W, 5),
                    "r": round(float(np.median(a[:, 2])) / W, 5), "score": round(float(a[:, 3].min()), 3),
                    "drift": round(float(np.ptp(a[:, :3], axis=0).max()) / W, 4)}
    return out


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(f[:-4] for f in os.listdir("films") if f.startswith("p") and f.endswith(".mp4"))
    ports = json.load(open("ports.json")) if os.path.exists("ports.json") else {}
    for i in ids:
        ports[i] = track(i)
        print(i, json.dumps(ports[i]))
    json.dump(dict(sorted(ports.items())), open("ports.json", "w"), indent=1)
