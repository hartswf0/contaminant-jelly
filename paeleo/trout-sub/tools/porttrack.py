#!/usr/bin/env python3
"""porttrack: find the brass porthole in the first and last frames of each film.

    python3 tools/porttrack.py            # every film in films/, writes ports.json
    python3 tools/porttrack.py p07 p21

For each film it samples three frames in the opening 0.5 s and three in the
closing 0.5 s, and fits the outer edge of the brass rim: brass just inside the circle, wall just
outside it. ports.json holds centre and rim radius as fractions of frame width, plus a fit score.
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


def brass(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    m = ((h >= 10) & (h <= 30) & (s >= 80) & (v >= 60) & (v <= 235)).astype(np.float32)
    return cv2.GaussianBlur(m, (5, 5), 0)


def ring(m, cx, cy, r, fracs):
    """Mean of mask m sampled on circles of radius r*f around (cx, cy)."""
    tot = 0.0
    for f in fracs:
        x = cx + r * f * COS
        y = cy + r * f * SIN
        ok = (x >= 0) & (x < W) & (y >= 0) & (y < H)
        tot += float((m[np.clip(y, 0, H - 1).astype(int), np.clip(x, 0, W - 1).astype(int)] * ok).mean())
    return tot / len(fracs)


def score(m, cx, cy, r):
    """r is the OUTER edge of the brass rim: brass just inside it, wall just outside."""
    return ring(m, cx, cy, r, (0.82, 0.88, 0.94)) - ring(m, cx, cy, r, (1.07, 1.15, 1.25))


def fit(img):
    """Circle candidates come from edges (Hough); the brass test picks the rim among them."""
    m = brass(img)
    gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
    best = (W / 2, H / 2, 70.0, -1.0)
    for p2 in (40, 28):
        c = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=6, param1=110, param2=p2, minRadius=40, maxRadius=230)
        if c is None:
            continue
        for cx, cy, r in c[0][:60]:
            for dr in (-2, -1, 0, 1, 2):
                sc = score(m, cx, cy, r + dr)
                if sc > best[3]:
                    best = (float(cx), float(cy), float(r + dr), sc)
        if best[3] > 0.5:
            break
    return best


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
                fits.append(fit(img))
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
