"""Turn a WorldParticle rollout into the viewer's format, beside its ground truth.

WorldParticle's inference writes OUTPUT_DIR/outcomes/npz/<sample>/<sample>_<START>_<END>.npz with `position` [T, N, 3]
(see its README, "Inference"). This writes bonus/wp/<sample>_pred.bin in the same int16 packing and bounds as
bonus/wp/<sample>.bin, so the viewer can lay the prediction over the simulation.

Usage: python3 pred_to_web.py PRED.npz SAMPLE_NAME [--web ../../bonus/wp]
"""
import argparse, json, os
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('pred'); ap.add_argument('name'); ap.add_argument('--web', default='../../bonus/wp'); ap.add_argument('--stride', type=int, default=2)
a = ap.parse_args()
meta = json.load(open(os.path.join(a.web, a.name + '.json')))
X = np.load(a.pred)['position'][::a.stride][:meta['frames']]
lo, hi = np.array(meta['lo']), np.array(meta['hi'])
q = np.round(np.clip((X - lo) / np.maximum(hi - lo, 1e-6), 0, 1) * 65535 - 32768).astype(np.int16)
q.tofile(os.path.join(a.web, a.name + '_pred.bin'))
meta['pred_frames'] = int(X.shape[0]); json.dump(meta, open(os.path.join(a.web, a.name + '.json'), 'w'))
print('wrote', a.name + '_pred.bin', X.shape)
