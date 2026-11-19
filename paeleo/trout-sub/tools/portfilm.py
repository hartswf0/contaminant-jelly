#!/usr/bin/env python3
"""portfilm: one fal film per porthole (or intro shot), held to the shared masters.

    python3 tools/portfilm.py gen p07 --prompt-file prompts/p07.txt --atlas a50,a39
    python3 tools/portfilm.py gen intro-2 --prompt-file prompts/intro-2.txt --atlas a03 --still p01
    python3 tools/portfilm.py gen p07 --prompt-file prompts/p07.txt --dry-run

Sends prompt + reference images to minimax/h3-max/reference-to-video on the fal
queue (a paid API; the cloud session's proxy supplies the key). References, in
order: masters/cockpit.jpg, masters/outside.jpg, the porthole still, then any
atlas frames. Writes the raw clip and a contact sheet to .raw/, a web-sized
films/<id>.mp4, and appends to fal_log.json.
"""
import argparse, base64, fcntl, json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "minimax/h3-max/reference-to-video"
QUEUE = "https://queue.fal.run/" + ENDPOINT
RAW = os.path.join(ROOT, ".raw")
LOG = os.path.join(ROOT, "fal_log.json")


def datauri(path):
    """JPEG data URI; pads to an aspect ratio fal accepts (0.4 to 2.5)."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    w, h = [int(x) for x in probe.stdout.strip().split(",")[:2]]
    vf = "scale='min(1280,iw)':-2"
    if w / h > 2.3:
        vf = "pad=iw:ceil(iw/2.2/2)*2:0:(oh-ih)/2:color=0x16262b," + vf
    elif w / h < 0.45:
        vf = "pad=ceil(ih*0.5/2)*2:ih:(ow-iw)/2:0:color=0x16262b," + vf
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-frames:v", "1", "-q:v", "4",
                          "-f", "image2pipe", "-vcodec", "mjpeg", "-"], capture_output=True, check=True).stdout
    return "data:image/jpeg;base64," + base64.b64encode(out).decode()


def http(method, url, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    key = os.environ.get("FAL_KEY")
    if key:
        req.add_header("Authorization", "Key " + key)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def append_log(entry):
    with open(LOG + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        log = json.load(open(LOG)) if os.path.exists(LOG) else []
        log.append(entry)
        with open(LOG + ".tmp", "w") as f:
            json.dump(log, f, indent=1, ensure_ascii=False)
        os.replace(LOG + ".tmp", LOG)


def gen(a):
    prompt = open(a.prompt_file).read().strip()
    refs = []
    if not a.no_masters:
        refs += ["masters/cockpit.jpg", "masters/outside.jpg"]
    still = a.still or (a.id if a.id.startswith("p") and a.id[1:].isdigit() else None)
    if still and still != "none":
        refs.append("stills/%s.jpg" % still)
    refs += ["atlas/%s.jpg" % x for x in a.atlas.split(",") if x]
    for r in refs:
        if not os.path.exists(os.path.join(ROOT, r)):
            sys.exit("missing reference: " + r)
    args = {"duration": a.duration, "resolution": a.resolution, "aspect_ratio": "16:9",
            "prompt_expansion_mode": "disabled"}
    if a.seed is not None:
        args["seed"] = a.seed
    print("id %s | %d chars | refs %s | %s" % (a.id, len(prompt), refs, args))
    if a.dry_run:
        print(prompt)
        return
    os.makedirs(RAW, exist_ok=True)
    take = 1
    while os.path.exists(os.path.join(RAW, "%s_t%d.mp4" % (a.id, take))):
        take += 1
    raw = os.path.join(RAW, "%s_t%d.mp4" % (a.id, take))
    body = dict(prompt=prompt, reference_image_urls=[datauri(os.path.join(ROOT, r)) for r in refs], **args)
    t0 = time.time()
    res = None
    for attempt in range(3):
        try:
            sub = http("POST", QUEUE, body)
            while True:
                st = http("GET", sub["status_url"])
                if st.get("status") == "COMPLETED":
                    break
                if st.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
                    raise RuntimeError("status: " + json.dumps(st)[:300])
                if time.time() - t0 > 900:
                    raise TimeoutError("gave up on " + sub["request_id"])
                time.sleep(5)
            res = http("GET", sub["response_url"])
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:1200]
            if e.code in (401, 402, 403, 422):
                sys.exit("fal refused (%d): %s" % (e.code, msg))
            print("retry after HTTP %d: %s" % (e.code, msg[:200]))
            time.sleep(10 * (attempt + 1))
    url = ((res or {}).get("video") or {}).get("url")
    if not url:
        sys.exit("no video in result: " + json.dumps(res)[:600])
    urllib.request.urlretrieve(url, raw)
    film = os.path.join(ROOT, "films", a.id + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", film], check=True)
    sheet = os.path.join(RAW, "%s_t%d_sheet.jpg" % (a.id, take))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf",
                    "fps=%g,scale=480:-1,tile=4x3" % (12.0 / a.duration), "-frames:v", "1", "-q:v", "4", sheet], check=True)
    append_log({"endpoint": ENDPOINT, "name": a.id, "take": take, "seconds": round(time.time() - t0, 1),
                "arguments": args, "seed": res.get("seed"), "references": refs, "prompt": prompt,
                "source_url": url, "files": ["films/%s.mp4" % a.id]})
    print("take %d\nfilm  %s\nsheet %s  (12 frames in time order, left to right, top to bottom)" % (take, film, sheet))


def use(a):
    """Make an earlier take the published film again."""
    raw = os.path.join(RAW, "%s_t%d.mp4" % (a.id, a.take))
    film = os.path.join(ROOT, "films", a.id + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", film], check=True)
    print("films/%s.mp4 is now take %d" % (a.id, a.take))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("gen")
    g.add_argument("id")
    g.add_argument("--prompt-file", required=True)
    g.add_argument("--atlas", default="")
    g.add_argument("--still")
    g.add_argument("--no-masters", action="store_true")
    g.add_argument("--duration", type=int, default=10)
    g.add_argument("--resolution", default="768P")
    g.add_argument("--seed", type=int)
    g.add_argument("--dry-run", action="store_true")
    u = sp.add_parser("use")
    u.add_argument("id")
    u.add_argument("take", type=int)
    a = ap.parse_args()
    gen(a) if a.cmd == "gen" else use(a)
