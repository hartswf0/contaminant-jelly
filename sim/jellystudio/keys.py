# Estimates a root note for each song from its render (average chroma of the low-mid band). An estimate, not a transcription.
import json, subprocess, numpy as np, os
D = '/home/user/contaminant-jelly/bonus/jellystudio/'; L = json.load(open(D + 'tracks.json')); out = {}
for t in L:
    import glob; g = sorted(glob.glob(D + t['id'] + '/renders/*.mp3')); f = g[0] if g else ''
    if not os.path.exists(f): continue
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'quiet', '-i', f, '-ac', '1', '-ar', '11025', '-f', 'f32le', '-'], capture_output=True).stdout, dtype=np.float32)
    N = 8192; ch = np.zeros(12); w = np.hanning(N); fr = np.fft.rfftfreq(N, 1 / 11025); ok = (fr > 80) & (fr < 1000); pc = np.round(12 * np.log2(fr[ok] / 440) + 69).astype(int) % 12
    for i in range(0, len(x) - N, N // 2): m = np.abs(np.fft.rfft(x[i:i + N] * w))[ok] ** 2; np.add.at(ch, pc, m)
    ch /= ch.sum() + 1e-12; minor = np.array([1, 0, .3, .8, 0, .7, 0, .9, .3, 0, .6, 0]); sc = [float((np.roll(minor, k) * ch).sum()) for k in range(12)]; r = int(np.argmax(sc)); out[t['id']] = {'root': r, 'conf': round(sc[r] / (sum(sc) / 12), 2)}
json.dump(out, open(D + 'voice/keys.json', 'w')); print(len(out), list(out.items())[:4])
