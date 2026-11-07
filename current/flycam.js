// Flycam: more camera for any three.js piece, without touching its own camera logic.
// Each frame the piece places its camera as it likes; just before rendering, the flycam moves it: further back, orbited round what it looks at,
// tilted, widened with speed. After the render the piece's camera is put back, so its own logic never feels the change.
//   attachFlycam(THREE, renderer, scene, camera, {back: 1.6, keys: true})
// Controls: wheel or pinch to pull back / come close; right-drag, two-finger drag or Q/E · R/F to orbit and tilt; Z/X zoom; C to recentre.
// The camera also breathes with speed: moving fast it lags, pulls back and widens, like a chase camera.
export function attachFlycam(THREE, renderer, scene, camera, opt = {}) {
  const S = {dist: opt.back ?? 1.6, yaw: 0, pitch: 0, tDist: opt.back ?? 1.6, tYaw: 0, tPitch: opt.pitch ?? .08, speed: 0, lastP: null, lastT: performance.now(), keys: new Set()};
  const save = {p: new THREE.Vector3(), q: new THREE.Quaternion(), fov: camera.fov}, fwd = new THREE.Vector3(), tgt = new THREE.Vector3(), off = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0), sm = new THREE.Vector3();
  const el = renderer.domElement, clampD = d => Math.min(opt.max ?? 4.5, Math.max(opt.min ?? .7, d));
  addEventListener('wheel', e => { S.tDist = clampD(S.tDist * (e.deltaY > 0 ? 1.08 : .93)); }, {passive: true});
  let drag = null, pinch = null;
  el.addEventListener('contextmenu', e => e.preventDefault());
  addEventListener('pointerdown', e => { if (e.button === 2 || e.altKey) drag = {x: e.clientX, y: e.clientY}; });
  addEventListener('pointermove', e => { if (!drag) return; S.tYaw -= (e.clientX - drag.x) * .006; S.tPitch = Math.max(-.6, Math.min(.9, S.tPitch + (e.clientY - drag.y) * .004)); drag = {x: e.clientX, y: e.clientY}; });
  addEventListener('pointerup', () => { drag = null; });
  addEventListener('touchstart', e => { if (e.touches.length === 2) { const [a, b] = e.touches; pinch = {d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2, dist: S.tDist}; } }, {passive: true});
  addEventListener('touchmove', e => { if (!pinch || e.touches.length !== 2) return; const [a, b] = e.touches, d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), x = (a.clientX + b.clientX) / 2, y = (a.clientY + b.clientY) / 2;
    S.tDist = clampD(pinch.dist * pinch.d / d); S.tYaw -= (x - pinch.x) * .006; S.tPitch = Math.max(-.6, Math.min(.9, S.tPitch + (y - pinch.y) * .004)); pinch.x = x; pinch.y = y; }, {passive: true});
  addEventListener('touchend', e => { if (e.touches.length < 2) pinch = null; }, {passive: true});
  if (opt.keys !== false) { addEventListener('keydown', e => { const k = e.key.toLowerCase(); if ('qerfzxc'.includes(k) && k.length === 1) { S.keys.add(k); if (k === 'c') { S.tYaw = 0; S.tPitch = opt.pitch ?? .08; S.tDist = opt.back ?? 1.6; } } });
    addEventListener('keyup', e => S.keys.delete(e.key.toLowerCase())); }
  const render = renderer.render.bind(renderer);
  renderer.render = (sc, cam) => {
    if (cam !== camera || S.off) return render(sc, cam);
    const now = performance.now(), dt = Math.min(.05, Math.max(0, (now - S.lastT) / 1000)); S.lastT = now;
    const K = S.keys; if (K.has('q')) S.tYaw += dt * 1.4; if (K.has('e')) S.tYaw -= dt * 1.4; if (K.has('r')) S.tPitch = Math.min(.9, S.tPitch + dt); if (K.has('f')) S.tPitch = Math.max(-.6, S.tPitch - dt); if (K.has('z')) S.tDist = clampD(S.tDist * (1 - dt)); if (K.has('x')) S.tDist = clampD(S.tDist * (1 + dt));
    const k = 1 - Math.pow(.02, dt); S.dist += (S.tDist - S.dist) * k; S.yaw += (S.tYaw - S.yaw) * k; S.pitch += (S.tPitch - S.pitch) * k;
    // what the piece's camera looks at: a point ahead of it, as far as it stands from the scene's subject (or a fixed reach)
    camera.updateMatrixWorld(); save.p.copy(camera.position); save.q.copy(camera.quaternion); save.fov = camera.fov;
    camera.getWorldDirection(fwd); const reach = opt.reach ?? 3.4; tgt.copy(camera.position).addScaledVector(fwd, reach);
    if (S.lastP && dt > 0) { const v = camera.position.distanceTo(S.lastP) / dt; S.speed += (v - S.speed) * Math.min(1, dt * 3); } S.lastP = (S.lastP || new THREE.Vector3()).copy(camera.position);
    const sp = Math.min(1, S.speed / (opt.fast ?? 8)), d = reach * (S.dist + .35 * sp);
    off.copy(camera.position).sub(tgt).normalize(); off.applyAxisAngle(up, S.yaw); const side = new THREE.Vector3().crossVectors(off, up).normalize(); off.applyAxisAngle(side, S.pitch);
    sm.copy(tgt).addScaledVector(off, d); camera.position.copy(sm); camera.lookAt(tgt); camera.fov = save.fov + 9 * sp + (S.dist - 1) * 2; camera.updateProjectionMatrix();
    const out = render(sc, cam);
    camera.position.copy(save.p); camera.quaternion.copy(save.q); camera.fov = save.fov; camera.updateProjectionMatrix();
    return out; };
  return S;
}
