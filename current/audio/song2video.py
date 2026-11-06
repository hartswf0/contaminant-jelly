#!/usr/bin/env python3
"""song2video: one 10 s design video per song, from audio/song2game.json.

    python3 audio/song2video.py --dry-run              # print every prompt, send nothing
    python3 audio/song2video.py --dry-run --only event-03,siltwire-02
    FAL_KEY=... python3 audio/song2video.py            # submit all 26 (skips videos already on disk)
    FAL_KEY=... python3 audio/song2video.py --only twobuttons-14 --force

Each prompt goes to the fal queue endpoint minimax/h3-max/text-to-video
(POST https://queue.fal.run/minimax/h3-max/text-to-video, header
"Authorization: Key $FAL_KEY"). The script polls status_url, fetches
response_url, downloads video.url to fal/song_<id>.mp4 and appends an entry
to fal/fal_log.json in the same shape as the design_v* entries.

This is a paid API. Nothing is sent without FAL_KEY, and nothing at all with --dry-run.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = os.path.join(HERE, "song2game.json")
FAL_DIR = os.path.join(ROOT, "fal")
LOG = os.path.join(FAL_DIR, "fal_log.json")
ENDPOINT = "minimax/h3-max/text-to-video"
QUEUE = "https://queue.fal.run/" + ENDPOINT
ARGS = {"duration": 10, "resolution": "1080P", "aspect_ratio": "16:9", "prompt_expansion_mode": "disabled"}


def http(method, url, key, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Key " + key)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def download(url, path):
    tmp = path + ".part"
    with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, path)


def append_log(entry):
    log = []
    if os.path.exists(LOG):
        with open(LOG) as f:
            log = json.load(f)
    log.append(entry)
    tmp = LOG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    os.replace(tmp, LOG)


def run_one(sid, song, key, poll, max_wait):
    prompt = song["video"]["prompt"]
    t0 = time.time()
    sub = http("POST", QUEUE, key, dict(prompt=prompt, **ARGS))
    status_url = sub.get("status_url") or "%s/requests/%s/status" % (QUEUE, sub["request_id"])
    response_url = sub.get("response_url") or "%s/requests/%s" % (QUEUE, sub["request_id"])
    print("  queued", sub.get("request_id"), flush=True)
    while True:
        st = http("GET", status_url, key)
        s = st.get("status")
        if s == "COMPLETED":
            break
        if s not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError("unexpected status: %s" % json.dumps(st)[:400])
        if time.time() - t0 > max_wait:
            raise TimeoutError("gave up after %ds (request %s)" % (max_wait, sub.get("request_id")))
        time.sleep(poll)
    res = http("GET", response_url, key)
    url = (res.get("video") or {}).get("url")
    if not url:
        raise RuntimeError("no video.url in response: %s" % json.dumps(res)[:400])
    rel = "fal/song_%s.mp4" % sid
    download(url, os.path.join(ROOT, rel))
    secs = round(time.time() - t0, 1)
    append_log(dict(endpoint=ENDPOINT, name="song_" + sid, seconds=secs, arguments=dict(ARGS), prompt=prompt,
                    files=[rel], song=sid, level=song["treatment"]["level"], audio_start=song["video"]["audio_start"],
                    request_id=sub.get("request_id")))
    print("  saved", rel, "in %ss" % secs, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the prompts and exit; sends nothing")
    ap.add_argument("--only", default="", help="comma-separated song ids")
    ap.add_argument("--force", action="store_true", help="regenerate even if fal/song_<id>.mp4 exists")
    ap.add_argument("--poll", type=float, default=10.0, help="seconds between status polls")
    ap.add_argument("--max-wait", type=int, default=1800, help="seconds to wait per video")
    a = ap.parse_args()

    with open(SPEC) as f:
        spec = json.load(f)
    songs = spec["songs"]
    ids = [s for s in a.only.split(",") if s] or list(songs)
    bad = [s for s in ids if s not in songs]
    if bad:
        sys.exit("unknown song id(s): " + ", ".join(bad))

    if a.dry_run:
        for sid in ids:
            s = songs[sid]
            print("=== %s  %s  [level %s, audio from %.2fs, turn %.2fs]" % (
                sid, s["title"], s["treatment"]["level"], s["video"]["audio_start"], s["video"]["turn_at"]))
            print(json.dumps(dict(prompt=s["video"]["prompt"], **ARGS), ensure_ascii=False, indent=1))
            print("  -> fal/song_%s.mp4  (%d chars)\n" % (sid, len(s["video"]["prompt"])))
        print("dry run: %d prompts, nothing sent to %s" % (len(ids), QUEUE))
        return

    key = os.environ.get("FAL_KEY")
    if not key:
        sys.exit("FAL_KEY is not set (use --dry-run to only print the prompts)")
    os.makedirs(FAL_DIR, exist_ok=True)
    failed = []
    for n, sid in enumerate(ids, 1):
        out = os.path.join(FAL_DIR, "song_%s.mp4" % sid)
        if os.path.exists(out) and not a.force:
            print("[%d/%d] %s exists, skipping" % (n, len(ids), sid))
            continue
        print("[%d/%d] %s" % (n, len(ids), sid), flush=True)
        try:
            run_one(sid, songs[sid], key, a.poll, a.max_wait)
        except (urllib.error.HTTPError) as e:
            body = e.read().decode(errors="replace")[:400]
            print("  FAILED: HTTP %s %s" % (e.code, body), flush=True)
            failed.append(sid)
            if e.code in (401, 402, 403):
                print("  stopping: authorization or balance problem")
                break
        except Exception as e:  # keep going with the next song
            print("  FAILED:", e, flush=True)
            failed.append(sid)
    if failed:
        sys.exit("failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
