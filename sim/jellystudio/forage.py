# FORAGE (index): a seeded random draw of new sources from the rest of the catalog repository, one per album. Registered before processing.
import json, random, subprocess, hashlib, os, codecs, re
R = '/home/user/hartswf0/moto'; rev = subprocess.run(['git', '-C', R, 'rev-parse', 'origin/main'], capture_output=True, text=True).stdout.strip()
names = subprocess.run(['git', '-C', R, '-c', 'core.quotepath=off', 'ls-tree', '-r', '--name-only', 'origin/main'], capture_output=True, text=True).stdout.split('\n')
aud = [n for n in names if re.search(r'\.(ogg|mp3)$', n, re.I) and not n.startswith(('Et ', 'VOLHOLLA', 'MEDIA_DERIV')) and '/' in n]
by = {}; [by.setdefault(n.split('/')[0], []).append(n) for n in aud]; rnd = random.Random(1906); albums = sorted(by); rnd.shuffle(albums); reg = json.load(open('registry.json')); have = {r.get('sha256') for r in reg}; new = []
os.makedirs('new_src', exist_ok=True)
for al in albums[:24]:
    path = rnd.choice(sorted(by[al])); blob = subprocess.run(['git', '-C', R, 'cat-file', 'blob', 'origin/main:' + path], capture_output=True).stdout
    if len(blob) < 10000: print('unreachable', path); continue
    h = hashlib.sha256(blob).hexdigest(); 
    if h in have: continue
    i = 'S' + h[:6]; f = 'new_src/%s%s' % (i, os.path.splitext(path)[1]); open(f, 'wb').write(blob); w = 'pcm/%s.f32' % i
    c = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-ac', '2', '-ar', '44100', '-f', 'f32le', w], capture_output=True, text=True); os.remove(f)
    if c.returncode: print('decode failed', path); continue
    e = {'catalog': 'forage:' + al, 'path': path, 'sha256': h, 'bytes': len(blob), 'id': i, 'seconds': round(os.path.getsize(w) / 8 / 44100, 2), 'status': 'decoded', 'forage': {'draw': 'seeded random (1906), one per album', 'repo': 'hartswf0/moto', 'commit': rev}}; new.append(e); have.add(h)
for r in reg: r.setdefault('forage', {'draw': 'the four catalogs named in the first brief', 'repo': 'hartswf0/moto', 'commit': rev})
json.dump(reg + new, open('registry2.json', 'w'), indent=1, ensure_ascii=False); print(len(new), 'new sources,', round(sum(e['seconds'] for e in new) / 60, 1), 'min; total', len([r for r in reg + new if r['status'] == 'decoded']))
