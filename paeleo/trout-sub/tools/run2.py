#!/usr/bin/env python3
"""run2: render version 2 prompts (two locked-off shots, feedstock style in the glass).

    python3 tools/run2.py --dry-run            # list what would be sent, send nothing
    python3 tools/run2.py p42 p07              # render these (one paid fal take each)
    python3 tools/run2.py --all --jobs 4       # render every prompts2/pNN.txt that has no film yet

Reads prompts2/pNN.txt; the first line is "# feedstock: <slug> | control: ... | atlas: aNN[,aNN]".
Writes films/pNN-v2.mp4 through tools/portfilm.py (turbo, 480P, 8 s). Stops at the first refusal.
"""
import argparse, concurrent.futures as cf, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def one(pid, dry):
    lines = open("prompts2/%s.txt" % pid).read().strip().split("\n")
    head = lines[0] if lines[0].startswith("#") else ""
    atlas = [a for a in re.findall(r"a\d\d", head.split("atlas:")[-1]) if a != "a03" and os.path.exists("atlas/%s.jpg" % a)] if "atlas:" in head else []
    tmp = os.path.join(tempfile.mkdtemp(), pid + ".txt")
    open(tmp, "w").write("\n".join(lines[1:] if head else lines).strip() + "\n")
    cmd = ["python3", "tools/portfilm.py", "gen", pid + "-v2", "--still", pid, "--prompt-file", tmp,
           "--duration", "8", "--atlas", ",".join(atlas[:2])] + (["--dry-run"] if dry else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    text = (r.stdout + r.stderr).strip()
    return pid, ("refused" if "fal refused" in text else "ok" if r.returncode == 0 else "error"), text.split("\n")[0 if dry else -1][:220]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    ids = a.ids or sorted(f[:-4] for f in os.listdir("prompts2") if re.fullmatch(r"p\d\d\.txt", f))
    if not a.ids and not a.all and not a.dry_run:
        sys.exit("name portholes, or pass --all or --dry-run")
    ids = [i for i in ids if a.ids or a.dry_run or not os.path.exists("films/%s-v2.mp4" % i)]
    first = one(ids[0], a.dry_run)          # one probe before fanning out, so a locked account costs one call
    print(*first)
    if first[1] == "refused":
        sys.exit("fal refused the first take; nothing else was sent")
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for res in ex.map(lambda i: one(i, a.dry_run), ids[1:]):
            print(*res, flush=True)
