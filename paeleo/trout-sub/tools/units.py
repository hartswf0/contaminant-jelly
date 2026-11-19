#!/usr/bin/env python3
"""units: one standard unit per porthole, so the deck plays as one seamless chain.

    python3 tools/units.py            # build every unit
    python3 tools/units.py p07 p49    # rebuild these

A unit is exactly 8.000 s, 960x540, 24 fps, with sound, and has no camera
move. The brass porthole is tracked on every frame of the film and held at one
place and size (frame centre, outer rim radius CANON_R of frame width) from
the first frame to the last:

- Turkey's side. The room is the film's own opening framing, held still. While
  the film's camera stays there the frame is shown live (so the wing on the
  control is kept). When the film pushes in on the glass, only the porthole is
  taken from the film, resized to the lock and set into the held room. If the
  film goes right through the rim, its picture fills the glass.
- Trout's side. From the film's cut across the glass, the outside shot is held
  at one framing with the port on the lock. If that shot has no port that can
  be brought to the lock, the unit dissolves to masters/outside.jpg on the lock.
- Frame one carries the deck drawing in the glass, dissolving into the film.

So the shot that ends any unit registers rim on rim with the shot that opens
any other, and a unit loops on itself. A porthole with no generated film gets a
keyframe unit built from the two masters and its deck still. No fal call here.
"""
import json, os, subprocess, sys
import cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import porttrack as pt

LEN, FPS = 8.0, 24
OW, OH = 960, 540
CANON_R = 0.215        # outer rim radius on the lock, as a fraction of frame width
GLASS = 0.77           # glass radius / outer rim radius
STILL_RIM, STILL_GLASS = 300, 0.715   # deck stills: outer rim radius in a 640 px still; glass / rim
MASTER_IN = (670, 356, 195)     # port in masters/cockpit.jpg (1344x768): centre x, centre y, outer rim radius
MASTER_OUT = (675, 387, 268)    # port in masters/outside.jpg
KF_CUT = 5.5           # keyframe units: seconds on Turkey's side
MIN_SCORE, PUSH_SCORE = 0.33, 0.5
N = int(LEN * FPS)
C = (OW / 2.0, OH / 2.0, CANON_R * OW)     # the lock, in output pixels


def frames(src, n, w=1280, h=720):
    """n frames spread evenly over the whole film (this is the time fit to 8 s)."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                               capture_output=True, text=True, check=True).stdout)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "fps=%f,scale=%d:%d:flags=lanczos" % (n / dur, w, h),
                          "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    if len(a) < n:
        a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    return a, dur


def place(img, port, size=(OW, OH)):
    """Scale and shift a frame so the given port (cx, cy, r in img pixels) sits on the lock."""
    s = C[2] / port[2]
    M = np.float32([[s, 0, C[0] - s * port[0]], [0, s, C[1] - s * port[1]]])
    return cv2.warpAffine(img, M, size, flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def disc(radius, feather=3.0):
    yy, xx = np.mgrid[:OH, :OW]
    d = np.hypot(xx - C[0], yy - C[1])
    return np.clip((radius - d) / feather + 0.5, 0, 1)[..., None].astype(np.float32)


def covers(port, w, h):
    """Does a frame placed on the lock by this port fill the output with no edge showing?"""
    s = C[2] / port[2]
    x0, y0 = C[0] - s * port[0], C[1] - s * port[1]
    return x0 <= 0.5 and y0 <= 0.5 and x0 + s * w >= OW - 0.5 and y0 + s * h >= OH - 0.5


def still_glass(pid):
    """The deck drawing's glass, sized to the lock's glass, as a full output frame."""
    im = cv2.imread("stills/%s.jpg" % pid)
    r = STILL_RIM * STILL_GLASS
    return place(im, (320, 320, r / GLASS * 1.0), (OW, OH)) if im is not None else None


def cut_time(src, dur):
    """The film's cut across the glass: its strongest scene change in the second half, in seconds."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", "scale=320:-1,select='gte(scene,0)',metadata=print:file=-",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stdout
    best, t = (0.0, None), None
    for line in out.splitlines():
        if "pts_time:" in line:
            t = float(line.split("pts_time:")[1].split()[0])
        elif "scene_score=" in line and t is not None and 0.45 * dur < t < 0.97 * dur:
            v = float(line.split("=")[1])
            if v > best[0]:
                best = (v, t)
    return best[1] if best[0] >= 0.2 else None


def follow(F, i0, i1, first):
    """Track the rim over frames i0..i1-1. Returns per frame (cx, cy, r) in 1280-wide pixels, or
    None once the film has gone in so close that the rim leaves the picture. Inside Turkey's
    shot the port never gets smaller than it starts, so smaller or weak matches are refused,
    and once the rim is lost it stays lost (no flicker between the two treatments)."""
    k = F.shape[2] / float(pt.W)
    out, prev, gone = [], first, False
    for i in range(i0, i1):
        hit = None
        if not gone:
            small = cv2.resize(F[i], (pt.W, pt.H), interpolation=cv2.INTER_AREA)
            cx, cy, r, sc = pt.fit_near(small, prev)
            if sc >= PUSH_SCORE and r >= 0.92 * first[2]:
                hit = (cx, cy, r)
        if hit:
            prev = hit
            out.append((hit[0] * k, hit[1] * k, hit[2] * k))
        else:
            gone = True
            out.append(None)
    return out


def keyframe_film(pid):
    """Frames for a porthole with no film: the cockpit master with the deck drawing in its port
    (dim, then lit), a cut, and the outside master. Returns frames and the known ports."""
    room = cv2.resize(cv2.imread("masters/cockpit.jpg"), (1280, 731))[5:725]
    out_ = cv2.resize(cv2.imread("masters/outside.jpg"), (1280, 731))[5:725]
    k = 1280 / 1344.0
    pin = (MASTER_IN[0] * k, MASTER_IN[1] * k - 5, MASTER_IN[2] * k)
    pout = (MASTER_OUT[0] * k, MASTER_OUT[1] * k - 5, MASTER_OUT[2] * k)
    F = np.empty((N, 720, 1280, 3), np.uint8)
    nc = int(KF_CUT * FPS)
    F[:nc] = room
    F[nc:] = out_
    return F, pin, pout, nc


def unit(pid):
    src = "films/%s.mp4" % pid
    kind = "film" if os.path.exists(src) else "keyframe"
    glass_r = C[2] * GLASS
    card = still_glass(pid)
    m_glass, m_rim = disc(glass_r - 2), disc(C[2] * 1.02)
    out = np.empty((N, OH, OW, 3), np.uint8)
    info = {"kind": kind}
    if kind == "keyframe":
        F, pin, pout, nc = keyframe_film(pid)
        room, outside = place(F[0], pin), place(F[-1], pout)
        for i in range(N):
            if i < nc:
                lit = np.clip((i / FPS - 1.2) / 0.6, 0, 1)
                c = cv2.GaussianBlur(card, (0, 0), 3 * (1 - lit) + 0.01) * (0.45 + 0.55 * lit)
                out[i] = room * (1 - m_glass) + c * m_glass
            else:
                out[i] = outside
        info.update(lock_start=True, lock_end=True, cut=KF_CUT, pushed_in=0, lost=0)
        audio = None
    else:
        F, dur = frames(src, N)
        ports = json.load(open("ports.json")) if os.path.exists("ports.json") else {}
        if pid not in ports:
            ports[pid] = pt.track(pid)
            json.dump(dict(sorted(ports.items())), open("ports.json", "w"), indent=1)
        P = ports[pid]
        W = F.shape[2]
        st = (P["start"]["cx"] * W, P["start"]["cy"] * W, P["start"]["r"] * W)
        en = P.get("end")
        tc = cut_time(src, dur)
        nc = int(round(tc / dur * N)) if tc else None
        end_port = (en["cx"] * W, en["cy"] * W, en["r"] * W) if en and en["score"] >= MIN_SCORE else None
        lock_end = bool(end_port) and nc is not None and covers(end_port, W, F.shape[1])
        n_in = nc if nc is not None else N - int(0.9 * FPS)
        tr = follow(F, 0, n_in, (st[0] * pt.W / W, st[1] * pt.W / W, st[2] * pt.W / W))
        room = place(F[0], st)
        pushed = lost = 0
        for i in range(n_in):
            p = tr[i]
            if p is not None and abs(p[2] / st[2] - 1) < 0.03 and np.hypot(p[0] - st[0], p[1] - st[1]) < 0.02 * W and covers(p, W, F.shape[1]):
                frame = place(F[i], p)                    # film camera is at home: show it live, on the lock
                room = frame
            elif p is not None:
                pushed += 1                               # film pushed in: keep the room, take only the port
                live = place(F[i], p)
                frame = room * (1 - m_rim) + live * m_rim
            else:
                lost += 1                                 # film is inside the rim: its picture fills the glass
                s = glass_r / (0.5 * F.shape[1]) * 1.02    # the largest circle in the picture fills the glass
                M = np.float32([[s, 0, C[0] - s * W / 2], [0, s, C[1] - s * F.shape[1] / 2]])
                live = cv2.warpAffine(F[i], M, (OW, OH), flags=cv2.INTER_AREA)
                frame = room * (1 - m_glass) + live * m_glass
            out[i] = np.clip(frame, 0, 255)
        if lock_end:
            for i in range(n_in, N):
                out[i] = place(F[i], end_port)
        else:
            k = 1280 / 1344.0
            tail = place(cv2.resize(cv2.imread("masters/outside.jpg"), (1280, 731)), (MASTER_OUT[0] * k, MASTER_OUT[1] * k, MASTER_OUT[2] * k))
            last = out[n_in - 1].astype(np.float32)
            for i in range(n_in, N):
                a = min(1.0, (i - n_in + 1) / (0.5 * FPS))
                src_f = place(F[i], st) if nc is None else last
                out[i] = src_f * (1 - a) + tail * a
        if card is not None:                              # frame one carries the deck drawing
            for i in range(int(1.25 * FPS)):
                a = float(np.clip(1 - (i / FPS - 0.45) / 0.8, 0, 1))
                out[i] = out[i] * (1 - m_glass * a) + card * (m_glass * a)
        info.update(lock_start=True, lock_end=lock_end, cut=round(nc / FPS, 3) if nc else None, pushed_in=pushed, lost=lost)
        audio = (src, dur)
    os.makedirs("units", exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (OW, OH), "-r", str(FPS), "-i", "-"]
    if audio:
        tempo = min(max(audio[1] / LEN, 0.5), 2.0)
        cmd += ["-i", audio[0], "-filter_complex",
                "[1:a]atempo=%f,apad,atrim=0:%f,afade=t=in:d=0.15,afade=t=out:st=%f:d=0.15[a]" % (tempo, LEN, LEN - 0.15),
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-f", "lavfi", "-t", str(LEN), "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a"]
    cmd += ["-t", str(LEN), "-c:v", "libx264", "-preset", "slow", "-crf", "25", "-pix_fmt", "yuv420p", "-g", "24",
            "-c:a", "aac", "-b:a", "80k", "-movflags", "+faststart", "units/%s.mp4" % pid]
    subprocess.run(cmd, input=out.tobytes(), check=True)
    print(pid, json.dumps(info), flush=True)
    return info


if __name__ == "__main__":
    ids = sys.argv[1:] or ["p%02d" % n for n in range(1, 56)]
    state = json.load(open("units.json")) if os.path.exists("units.json") else {}
    for i in ids:
        state[i] = unit(i)
        json.dump(dict(sorted(state.items())), open("units.json", "w"), indent=1)
    print("%d units; keyframe: %s; closed on the master: %s" % (
        len(ids), [i for i in ids if state[i]["kind"] == "keyframe"], [i for i in ids if not state[i]["lock_end"]]))
