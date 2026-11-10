import numpy as np, json
from scipy import signal
SR = 44100
def load(i): return np.fromfile('pcm/%s.f32' % i, dtype=np.float32).reshape(-1, 2)
def mono22(x): return signal.resample_poly(x.mean(1), 1, 2).astype(np.float32)
def stft(m, n=2048, h=512): f, t, Z = signal.stft(m, 22050, nperseg=n, noverlap=n - h, boundary=None, padded=False); return f, t, np.abs(Z)
def onset_env(S): L = np.log1p(30 * S); d = np.maximum(0, np.diff(L, axis=1)).sum(0); return np.concatenate([[0], d])
def tempo(env, hop=512 / 22050, lo=55, hi=190):
    e = env - env.mean(); ac = signal.correlate(e, e, 'full')[len(e) - 1:]; lags = np.arange(len(ac)) * hop; bpm = 60 / np.maximum(lags, 1e-6)
    ok = (bpm >= lo) & (bpm <= hi); k = np.argmax(np.where(ok, ac, -1e18)); return float(bpm[k]), float(ac[k] / ac[0])
def f0(seg, sr=22050, lo=60, hi=900):
    seg = seg * np.hanning(len(seg)); ac = signal.correlate(seg, seg, 'full')[len(seg) - 1:]; a, b = int(sr / hi), int(sr / lo); k = a + np.argmax(ac[a:b]); return sr / k, float(ac[k] / (ac[0] + 1e-12))
def note(f): n = int(round(12 * np.log2(f / 440) + 69)); return ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][n % 12] + str(n // 12 - 1), 100 * (12 * np.log2(f / 440) + 69 - n)
