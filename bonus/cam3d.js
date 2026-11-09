// CAM3D: one camera for the 3D and 4D worlds, built around the jelly's controls rather than beside them.
// makeCam(THREE, cam, opt) -> {C, step(dt, ctx), dialDown(id, x, y), dialMove(id, x, y), dialUp(id), draw(g), basis(), hold(on), cycle(), set(mode), recentre(), zoom(k)}
// ctx = {eyeDist (EYE: how far behind the bell), p: Vector3 (the jelly), v: Vector3, axis: Vector3, target: Vector3|null (the next goal), extra: [Vector3] (held anchors, a trail...),
//        hush: bool (a finger is steering: do not turn under it), carve: bool (a stick is steering: turning behind it IS the steering), auto: mode|null (the species asks for a mode now)}
// Optional ctx (SCION_CAMERA_DIRECTOR.md): lead (look-ahead along the glide, s), window (a dead zone the bell can move in before the view follows, m),
//   low (keep the bell low in frame, fraction of distance), occlude(look, want) -> 0..1 (pull in before a wall), fixed {pos, look} (mode 'fixed'), target (mode 'profile': what we match).
// shake(a) adds trauma that decays (shape: trauma squared); C.shakeOn turns it off. snap() makes the next step a hard cut.
// The rules (see SCION_CAMERA.md):
//  1 the view never turns under a finger that has planted something in the world (hush), but keeps the jelly framed by moving, not turning;
//  2 a stick that steers relative to the view is the one exception: there the view swings behind the motion, and that swing is the turning (carve);
//  3 the controls read the view as it was when the finger landed (the input basis is held until the last finger lifts), so a turning camera cannot bend a gesture;
//  4 a manual turn of the dial is an offset, and drifts home after 2.5 s (the recentre delay), unless the mode is ORBIT;
//  5 the camera never rolls, never turns faster than 1.8 rad/s, and stays above the floor.
export const MODES = {
  chase: {name: 'CHASE', line: 'behind the jelly, swinging behind its motion'},
  frame: {name: 'FRAME', line: 'the jelly and the next light, both in view'},
  side: {name: 'SIDE', line: 'side-on: depth reads as up and down'},
  top: {name: 'TOP', line: 'from above: a map'},
  eye: {name: 'EYE', line: 'just behind the bell, looking where it points'},
  orbit: {name: 'ORBIT', line: 'yours: only the dial turns it'},
  trail: {name: 'TRAIL', line: 'pulled back to show the whole of something'},
  profile: {name: 'PROFILE', line: 'side-on to a shared drift: the jelly and what it is matching, holding position'},
  fixed: {name: 'FIXED', line: 'a camera placed in the world; the jelly swims through its frame'}};
export function makeCam(THREE, cam, opt = {}) {
  const V = () => new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0), wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
  const C = {mode: opt.mode || 'chase', modes: opt.modes || ['chase', 'frame', 'side', 'top', 'orbit'], yaw: opt.yaw ?? 0, pitch: .25, dist: opt.dist || 15, zoomK: 1,
    man: {yaw: 0, pitch: 0, t: -9}, trauma: 0, shakeOn: opt.shake !== false, dial: null, held: null, live: {R: V(), U: V(), F: V(), Fh: V()}, look: V(), pos: V(), init: false, T: 0, sideYaw: null, auto: null, floor: opt.floor || null};
  const D = () => ({x: 70, y: innerHeight - 90, r: 46}), chip = () => ({x: 70, y: innerHeight - 160, w: 96, h: 24});
  function liveBasis() { const L = C.live; cam.getWorldDirection(L.F); L.R.crossVectors(L.F, UP).normalize(); L.U.crossVectors(L.R, L.F).normalize(); L.Fh.set(L.F.x, 0, L.F.z).normalize(); }
  const copyB = b => ({R: b.R.clone(), U: b.U.clone(), F: b.F.clone(), Fh: b.Fh.clone()});
  function step(dt, ctx) { C.T += dt; const p0 = ctx.p, mode = ctx.auto || C.mode; C.auto = ctx.auto || null;
    // the camera window: the bell may move this far before the view follows it (a pulse stays inside; a committed glide pushes the frame)
    let p = p0; if (ctx.window) { if (!C.win) C.win = p0.clone(); const d = p0.clone().sub(C.win), L = d.length(); if (L > ctx.window) C.win.addScaledVector(d, (L - ctx.window) / L); p = C.win; } else C.win = null;
    const hv = Math.hypot(ctx.v.x, ctx.v.z), heading = Math.atan2(-ctx.v.x, -ctx.v.z); let yawT = C.yaw, pitchT = .25, distT = C.dist, lookT = p.clone(), rate = 0, posAbs = null;
    if (mode === 'chase') { if (hv > 1) { yawT = heading; rate = ctx.carve ? 1.6 : ctx.hush ? 0 : .5; } lookT.addScaledVector(ctx.v, ctx.lead ?? .35); if (ctx.low) lookT.y += C.dist * ctx.low; }
    else if (mode === 'profile') { const t = ctx.target || p; let sd = (hv > 1 ? heading : C.yaw) + Math.PI / 2; if (Math.abs(wrap(sd - C.yaw)) > Math.PI / 2) sd += Math.PI; yawT = sd; rate = .9; pitchT = .12; lookT = p.clone().lerp(t, .5); distT = Math.max(C.dist * .85, p.distanceTo(t) * 1.5 + 6); }
    else if (mode === 'fixed' && ctx.fixed) { posAbs = ctx.fixed.pos.clone(); lookT = ctx.fixed.look ? ctx.fixed.look.clone() : p.clone(); }
    else if (mode === 'frame') { const t = ctx.target; if (t) { const d = t.clone().sub(p), L = Math.hypot(d.x, d.z); if (L > 1.5) { yawT = Math.atan2(-d.x, -d.z); rate = ctx.hush ? .15 : .9; } pitchT = .3 + Math.max(-.2, Math.min(.35, -d.y / Math.max(8, d.length()) * .6)); distT = Math.min(28, C.dist + Math.min(1, d.length() / 30) * 9); lookT.lerp(t, Math.min(.35, 6 / Math.max(6, d.length()) * .35 + .1)); } else if (hv > 1) { yawT = heading; rate = .4; } }
    else if (mode === 'side') { if (C.sideYaw === null) C.sideYaw = (hv > 1 ? heading : C.yaw) + Math.PI / 2; if (hv > 2 && !ctx.hush) { let s = heading + Math.PI / 2; if (Math.abs(wrap(s - C.sideYaw)) > Math.PI / 2) s += Math.PI; C.sideYaw += wrap(s - C.sideYaw) * Math.min(1, dt * .15); } yawT = C.sideYaw; rate = 1.2; pitchT = .06; distT = C.dist * 1.35; }
    else if (mode === 'top') { pitchT = 1.32; distT = C.dist * 1.7; rate = 0; }
    else if (mode === 'eye') { const ax = ctx.axis.clone().normalize(); if (Math.abs(ax.y) > .8) ax.set(-Math.sin(C.yaw), 0, -Math.cos(C.yaw)); const ed = ctx.eyeDist || 3.2; posAbs = p.clone().addScaledVector(ax, -ed).addScaledVector(UP, .6 + ed * .05); lookT = p.clone().addScaledVector(ax, 12); C.yaw = Math.atan2(-ax.x, -ax.z); }
    else if (mode === 'trail') { const pts = ctx.extra || []; if (pts.length) { const c = V(); pts.forEach(q => c.add(q)); c.divideScalar(pts.length); let r = 0; pts.forEach(q => r = Math.max(r, q.distanceTo(c))); lookT.copy(c).lerp(p, .3); distT = Math.min(60, Math.max(C.dist, r * 1.6 + 6)); pitchT = .55; } }
    if (mode !== 'side') C.sideYaw = null;
    // held anchors widen the shot and pull its centre toward them (the 3D lab's arms)
    if (ctx.extra && mode !== 'trail' && mode !== 'eye') { let sp = 0; const c = V(); ctx.extra.forEach(q => { c.add(q); sp = Math.max(sp, q.distanceTo(p)); }); if (ctx.extra.length) { lookT.lerp(c.divideScalar(ctx.extra.length), .2); distT += sp * .5; } }
    // the dial: an offset that drifts home after 2.5 s (ORBIT keeps it)
    if (mode === 'orbit') { rate = 0; } else if (!C.dial && C.T - C.man.t > 2.5) { C.man.yaw *= Math.exp(-dt * .8); C.man.pitch *= Math.exp(-dt * .8); }
    if (rate) { const d = wrap(yawT - C.yaw); C.yaw += Math.sign(d) * Math.min(Math.abs(d) * Math.min(1, dt * rate), 1.8 * dt); }
    C.pitch += (pitchT - C.pitch) * Math.min(1, dt * 1.5); const Y = C.yaw + C.man.yaw, P = Math.max(-.7, Math.min(1.45, C.pitch + C.man.pitch)), dist = distT * C.zoomK;
    const want = posAbs || lookT.clone().add(V().set(Math.sin(Y) * Math.cos(P), Math.sin(P), Math.cos(Y) * Math.cos(P)).multiplyScalar(dist));
    if (ctx.occlude && !posAbs) { const f = ctx.occlude(lookT, want); if (f < 1) want.copy(lookT).lerp(want, Math.max(.22, f * .9)); }   // pull in before a wall, ease back out after
    if (C.floor) want.y = Math.max(want.y, C.floor(want.x, want.z) + 1.5);
    if (C.trauma > 0) { if (C.shakeOn) { const k2 = C.trauma * C.trauma * .5, t = C.T * 23; want.x += Math.sin(t * 1.1) * k2; want.y += Math.sin(t * 1.7 + 2) * k2; want.z += Math.sin(t * 1.3 + 4) * k2; } C.trauma = Math.max(0, C.trauma - dt * 1.8); }
    if (!C.init) { C.init = true; C.pos.copy(want); C.look.copy(lookT); }
    const k = 1 - Math.pow(mode === 'eye' ? .002 : mode === 'fixed' ? .0001 : .03, dt); C.pos.lerp(want, k); C.look.lerp(lookT, 1 - Math.pow(.02, dt)); cam.position.copy(C.pos); cam.up.copy(UP); cam.lookAt(C.look); cam.updateMatrixWorld(); liveBasis(); }
  const inDial = (x, y) => Math.hypot(x - D().x, y - D().y) < D().r + 10, inChip = (x, y) => { if (C.modes.length < 2) return false; const c = chip(); return Math.abs(x - c.x) < c.w / 2 && Math.abs(y - c.y) < c.h / 2 + 4; };
  function cycle() { const i = C.modes.indexOf(C.mode); C.mode = C.modes[(i + 1) % C.modes.length]; C.man.yaw = C.man.pitch = 0; return C.mode; }
  return {C, shake(a) { C.trauma = Math.min(1, (C.trauma || 0) + a); }, snap() { C.init = false; },
    step, cycle, set(m) { if (C.modes.includes(m)) C.mode = m; }, recentre() { C.man.yaw = C.man.pitch = 0; C.man.t = -9; }, zoom(f) { C.zoomK = Math.max(.45, Math.min(2.6, C.zoomK * f)); },
    // the input basis: the view as it was when the first finger landed, held until the last lifts
    hold(on) { if (on && !C.held) C.held = copyB(C.live); if (!on) C.held = null; }, basis() { return C.held || C.live; },
    dialDown(id, x, y) { if (inChip(x, y)) { cycle(); return 'chip'; } if (!inDial(x, y)) return false; const now = performance.now(); if (now - (C.lastTap || 0) < 320) { this.recentre(); C.lastTap = 0; } else C.lastTap = now; C.dial = {id, x, y}; return true; },
    dialMove(id, x, y) { if (!C.dial || C.dial.id !== id) return false; const dx = x - C.dial.x, dy = y - C.dial.y; if (C.mode === 'orbit') { C.yaw -= dx * .012; C.pitch = Math.max(-.7, Math.min(1.45, C.pitch + dy * .008)); } else { C.man.yaw -= dx * .012; C.man.pitch = Math.max(-.9, Math.min(1.1, C.man.pitch + dy * .008)); } C.man.t = C.T; C.dial.x = x; C.dial.y = y; return true; },
    dialUp(id) { if (C.dial && C.dial.id === id) { C.dial = null; C.man.t = C.T; return true; } return false; },
    key(k, dt) { if (k === 'q') { C.man.yaw += dt * 1.4; C.man.t = C.T; } if (k === 'e') { C.man.yaw -= dt * 1.4; C.man.t = C.T; } },
    draw(g) { const d = D(), c = chip(), m = C.auto || C.mode, Y = C.yaw + C.man.yaw; g.strokeStyle = 'rgba(207,221,232,.35)'; g.lineWidth = 1.5; g.beginPath(); g.arc(d.x, d.y, d.r, 0, 7); g.stroke();
      g.fillStyle = 'rgba(240,163,90,.85)'; g.beginPath(); g.arc(d.x + Math.sin(Y) * d.r * .7, d.y + Math.cos(Y) * d.r * .7 * Math.cos(C.pitch + C.man.pitch), 6, 0, 7); g.fill();
      if (Math.abs(C.man.yaw) > .05 && m !== 'orbit') { const left = Math.max(0, 2.5 - (C.T - C.man.t)); g.strokeStyle = 'rgba(240,163,90,.5)'; g.beginPath(); g.arc(d.x, d.y, d.r + 5, -Math.PI / 2, -Math.PI / 2 + TAU * left / 2.5); g.stroke(); }
      if (C.modes.length < 2 && !C.auto) return;
      g.fillStyle = 'rgba(5,9,9,.6)'; g.fillRect(c.x - c.w / 2, c.y - c.h / 2, c.w, c.h); g.strokeStyle = C.auto ? 'rgba(255,214,140,.8)' : 'rgba(207,221,232,.4)'; g.strokeRect(c.x - c.w / 2, c.y - c.h / 2, c.w, c.h);
      g.fillStyle = 'rgba(240,163,90,.95)'; g.font = "400 11px Anton, Impact, sans-serif"; g.textAlign = 'center'; g.fillText(`CAM · ${MODES[m].name}`, c.x, c.y + 4); g.fillStyle = 'rgba(207,221,232,.6)'; g.font = "300 10px 'JetBrains Mono', monospace"; g.fillText(C.auto ? 'the body chose it' : 'tap to change', c.x, c.y - 18); g.fillText('view · double-tap: home', d.x + 26, d.y + d.r + 14); }};
}
const TAU = Math.PI * 2;
