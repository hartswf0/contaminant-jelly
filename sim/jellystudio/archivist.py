# ARCHIVIST: resolve the four catalogs' track lists (they are filled in by album-page.js), decode, hash, register. Labels are masked: scoring sees only ids.
import re, os, json, hashlib, subprocess, sys
R = '/home/user/hartswf0/moto'; js = open(R + '/VOLHOLLA/album-page.js', encoding='utf8').read()
reg = []; 
for key in ['boxesback', 'etubrute', 'boxback', 'brutesenate']:
    i = js.index('\n    %s: {' % key); blk = js[i:i + 12000]; blk = blk[:blk.index('\n    },') if '\n    },' in blk else len(blk)]
    base = re.search(r'basePath:\s*"([^"]+)"', blk).group(1); slug = re.search(r'pageSlug:\s*"([^"]+)"', blk).group(1)
    for name in re.findall(r'"([^"\n]+\.(?:ogg|mp3|wav|m4a))"', blk):
        reg.append({'catalog': slug, 'path': os.path.normpath(os.path.join('VOLHOLLA', base, name)), 'name': name})
os.makedirs('pcm', exist_ok=True); out = []
for r in reg:
    p = os.path.join(R, r['path']); e = {'catalog': r['catalog'], 'path': r['path']}
    if not os.path.exists(p): e['status'] = 'unreachable: not in the repository'; out.append(e); continue
    b = open(p, 'rb').read(); e['sha256'] = hashlib.sha256(b).hexdigest(); e['bytes'] = len(b)
    dup = next((o for o in out if o.get('sha256') == e['sha256']), None)
    if dup: e['status'] = 'exact duplicate of ' + dup['id']; e['id'] = dup['id']; out.append(e); continue
    e['id'] = 'S' + e['sha256'][:6]; w = 'pcm/%s.f32' % e['id']
    if not os.path.exists(w):
        c = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', p, '-ac', '2', '-ar', '44100', '-f', 'f32le', w], capture_output=True, text=True)
        if c.returncode: e['status'] = 'decode failed: ' + c.stderr[:80]; out.append(e); continue
    e['seconds'] = round(os.path.getsize(w) / 8 / 44100, 2); e['status'] = 'decoded'; out.append(e)
json.dump(out, open('registry.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter; print(Counter((o['catalog'], o['status'].split(':')[0].split(' of ')[0]) for o in out)); print(len(out), 'entries', len({o.get('id') for o in out if o.get('id')}), 'distinct', round(sum(o.get('seconds', 0) for o in out) / 60, 1), 'min')
