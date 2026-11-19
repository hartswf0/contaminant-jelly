/* drawn/kit.js — the shared drawing kit for the hand-made porthole animations.
 * Every scene draws in a 1000 x 1000 space; the glass is the circle at (500,500) radius 430 and the
 * player clips to it. A scene is DRAWN.add({id, title, style, scions:[...], draw(ctx, t, K)}).
 * t runs 0..12 s and loops: 0-8 the picture is MADE in front of you, 8-12 it comes alive.
 * Nothing may appear all at once: every mark is revealed by a tool (pencil, chalk, brush, scissors). */
(function () {
  "use strict";
  var K = {};
  K.TAU = Math.PI * 2;
  K.clamp = function (v, a, b) { return v < a ? a : v > b ? b : v; };
  K.lerp = function (a, b, u) { return a + (b - a) * u; };
  K.prog = function (t, a, b) { return K.clamp((t - a) / ((b - a) || 1e-6), 0, 1); };
  K.ease = function (u) { u = K.clamp(u, 0, 1); return u * u * (3 - 2 * u); };
  K.back = function (u) { u = K.clamp(u, 0, 1) - 1; return u * u * (2.7 * u + 1.7) + 1; };
  K.hash = function (n) { var s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  K.noise = function (x) { var i = Math.floor(x), f = x - i; return K.lerp(K.hash(i), K.hash(i + 1), f * f * (3 - 2 * f)); };

  /* ---- point builders (all return [[x,y],...]) ---- */
  K.line = function (x0, y0, x1, y1, n) { var p = []; n = n || 12; for (var i = 0; i <= n; i++) p.push([K.lerp(x0, x1, i / n), K.lerp(y0, y1, i / n)]); return p; };
  K.poly = function (pts, closed) { var out = []; var m = pts.length - (closed ? 0 : 1); for (var i = 0; i < m; i++) { var a = pts[i], b = pts[(i + 1) % pts.length]; var seg = K.line(a[0], a[1], b[0], b[1], 8); if (i) seg.shift(); out = out.concat(seg); } return out; };
  K.arc = function (cx, cy, r, a0, a1, n) { var p = []; n = n || 40; for (var i = 0; i <= n; i++) { var a = K.lerp(a0, a1, i / n); p.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } return p; };
  K.ellipse = function (cx, cy, rx, ry, n, rot) { var p = []; n = n || 48; rot = rot || 0; for (var i = 0; i <= n; i++) { var a = K.TAU * i / n, x = rx * Math.cos(a), y = ry * Math.sin(a); p.push([cx + x * Math.cos(rot) - y * Math.sin(rot), cy + x * Math.sin(rot) + y * Math.cos(rot)]); } return p; };
  K.blob = function (cx, cy, r, seed, n, rough) { var p = []; n = n || 40; rough = rough == null ? 0.18 : rough; for (var i = 0; i <= n; i++) { var a = K.TAU * (i % n) / n; var rr = r * (1 + rough * (K.noise(seed + (i % n) * 0.7) - 0.5) * 2); p.push([cx + rr * Math.cos(a), cy + rr * Math.sin(a)]); } return p; };
  K.curve = function (ctrl, n) { /* Catmull-Rom through control points */ var p = []; n = n || 10; for (var i = 0; i < ctrl.length - 1; i++) { var p0 = ctrl[Math.max(0, i - 1)], p1 = ctrl[i], p2 = ctrl[i + 1], p3 = ctrl[Math.min(ctrl.length - 1, i + 2)]; for (var j = 0; j < n; j++) { var u = j / n, u2 = u * u, u3 = u2 * u; p.push([0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3), 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]); } } p.push(ctrl[ctrl.length - 1]); return p; };
  K.move = function (pts, dx, dy, s, rot, ox, oy) { s = s == null ? 1 : s; rot = rot || 0; ox = ox || 0; oy = oy || 0; var c = Math.cos(rot), n = Math.sin(rot); return pts.map(function (p) { var x = (p[0] - ox) * s, y = (p[1] - oy) * s; return [ox + x * c - y * n + dx, oy + x * n + y * c + dy]; }); };

  /* ---- the last place a tool touched; K.tool() draws the tool there ---- */
  K.tip = null;
  function trace(ctx, pts, upto) { ctx.beginPath(); for (var i = 0; i < upto; i++) { if (i) ctx.lineTo(pts[i][0], pts[i][1]); else ctx.moveTo(pts[i][0], pts[i][1]); } }

  /* Draw a line progressively, the way a hand does. u 0..1.
   * o: {color, width, wobble (px), seed, kind:'pencil'|'ink'|'chalk'|'brush', alpha} */
  K.stroke = function (ctx, pts, u, o) {
    o = o || {}; u = K.clamp(u, 0, 1); if (u <= 0 || pts.length < 2) return;
    var n = Math.max(2, Math.ceil(pts.length * u)), w = o.width || 5, wob = o.wobble == null ? 2.2 : o.wobble, seed = o.seed || 1, kind = o.kind || "pencil";
    var q = pts.slice(0, n).map(function (p, i) { return [p[0] + (K.noise(seed + i * 0.45) - 0.5) * 2 * wob, p[1] + (K.noise(seed + 50 + i * 0.45) - 0.5) * 2 * wob]; });
    ctx.save(); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.strokeStyle = o.color || "#16293a"; ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    if (kind === "chalk") { for (var k = 0; k < 3; k++) { ctx.globalAlpha = (o.alpha == null ? 1 : o.alpha) * (0.5 - k * 0.12); ctx.lineWidth = w * (1 - k * 0.2); ctx.setLineDash([w * (2 + k), w * (0.5 + k * 0.6)]); ctx.lineDashOffset = k * 7; trace(ctx, q, n); ctx.stroke(); } }
    else if (kind === "brush") { ctx.lineWidth = w; ctx.globalAlpha *= 0.85; trace(ctx, q, n); ctx.stroke(); ctx.lineWidth = w * 0.45; ctx.globalAlpha *= 0.5; ctx.translate(w * 0.2, w * 0.25); trace(ctx, q, n); ctx.stroke(); }
    else if (kind === "pencil") { ctx.lineWidth = w; trace(ctx, q, n); ctx.stroke(); ctx.globalAlpha *= 0.35; ctx.lineWidth = w * 0.6; ctx.translate(1.5, -1.2); trace(ctx, q, n); ctx.stroke(); }
    else { ctx.lineWidth = w; trace(ctx, q, n); ctx.stroke(); }
    ctx.restore();
    if (u < 1) K.tip = { x: q[n - 1][0], y: q[n - 1][1], kind: kind === "ink" ? "pencil" : kind };
  };

  /* Fill a closed shape progressively. mode: 'hatch' (pencil shading), 'wash' (brush sweeps), 'wipe', 'stipple'. */
  K.fill = function (ctx, pts, u, color, mode, o) {
    o = o || {}; u = K.clamp(u, 0, 1); if (u <= 0) return;
    var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
    ctx.save(); trace(ctx, pts, pts.length); ctx.closePath(); ctx.clip(); ctx.fillStyle = color; ctx.strokeStyle = color; ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    mode = mode || "wash";
    if (mode === "wipe") { ctx.fillRect(x0, y0, (x1 - x0) * u, y1 - y0); }
    else if (mode === "hatch") { var gap = o.gap || 9, total = Math.ceil((x1 - x0 + y1 - y0) / gap), done = total * u; ctx.lineWidth = o.width || 3; ctx.lineCap = "round"; for (var i = 0; i < done; i++) { var f = Math.min(1, done - i), xa = x0 + i * gap, ya = y0, xb = xa - (y1 - y0), yb = y1; ctx.beginPath(); ctx.moveTo(xa, ya); ctx.lineTo(K.lerp(xa, xb, f), K.lerp(ya, yb, f)); ctx.stroke(); if (f < 1) K.tip = { x: K.lerp(xa, xb, f), y: K.lerp(ya, yb, f), kind: "pencil" }; } }
    else if (mode === "stipple") { var count = Math.floor((o.count || 400) * u); for (var j = 0; j < count; j++) { var px = x0 + K.hash(j * 3.1 + 1) * (x1 - x0), py = y0 + K.hash(j * 7.7 + 2) * (y1 - y0); ctx.beginPath(); ctx.arc(px, py, (o.dot || 3) * (0.6 + K.hash(j) * 0.8), 0, K.TAU); ctx.fill(); } }
    else { var rows = o.rows || 6, h = (y1 - y0) / rows, prog = rows * u; for (var r = 0; r < prog; r++) { var fr = Math.min(1, prog - r), dir = r % 2 === 0; var xa2 = dir ? x0 : x1 - (x1 - x0) * fr; ctx.globalAlpha = (o.alpha == null ? 1 : o.alpha) * (0.82 + 0.18 * K.hash(r)); ctx.fillRect(xa2, y0 + r * h - 2, (x1 - x0) * fr, h + 4); if (fr < 1) K.tip = { x: dir ? x0 + (x1 - x0) * fr : x1 - (x1 - x0) * fr, y: y0 + r * h + h / 2, kind: "brush" }; } }
    ctx.restore();
  };

  /* A cut-paper piece: draws piece() with a drop shadow, sliding and settling into place. u 0..1. */
  K.cut = function (ctx, piece, u, o) {
    o = o || {}; if (u <= 0) return; var e = K.back(u), fx = (o.from && o.from[0]) || 0, fy = (o.from && o.from[1]) || -700;
    ctx.save(); ctx.translate(fx * (1 - e), fy * (1 - e)); if (o.pivot) { ctx.translate(o.pivot[0], o.pivot[1]); ctx.rotate((o.rot || 0.4) * (1 - e)); ctx.translate(-o.pivot[0], -o.pivot[1]); }
    ctx.shadowColor = "rgba(0,0,0,.35)"; ctx.shadowBlur = 14 * (1.6 - e * 0.6); ctx.shadowOffsetX = 8; ctx.shadowOffsetY = 10; piece(ctx); ctx.restore();
    if (u < 1) K.tip = { x: (o.pivot ? o.pivot[0] : 500) + fx * (1 - e), y: (o.pivot ? o.pivot[1] : 500) + fy * (1 - e), kind: "hand" };
  };
  K.shape = function (ctx, pts, fill, stroke, width) { trace(ctx, pts, pts.length); ctx.closePath(); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width || 4; ctx.lineJoin = "round"; ctx.stroke(); } };

  /* Paper, grain and washes that sit under everything. */
  K.paper = function (ctx, color, grain) { ctx.fillStyle = color || "#f3ead6"; ctx.fillRect(0, 0, 1000, 1000); if (grain !== 0) { ctx.save(); ctx.globalAlpha = grain || 0.06; for (var i = 0; i < 900; i++) { ctx.fillStyle = K.hash(i) > 0.5 ? "#000" : "#fff"; ctx.fillRect(K.hash(i * 1.3) * 1000, K.hash(i * 2.7) * 1000, 2 + K.hash(i * 5) * 3, 1.5); } ctx.restore(); } };

  /* Run steps one after another. steps: [[seconds, function(u){...}], ...]. Finished steps are redrawn at u = 1,
   * so the picture accumulates. Returns the time at which everything is finished. */
  K.seq = function (t, steps) { var at = 0; for (var i = 0; i < steps.length; i++) { var d = steps[i][0], u = K.prog(t, at, at + d); if (u > 0) steps[i][1](u, t - at); at += d; } return at; };

  /* Draw the tool at the place it last touched, then forget it. Call once, last, in draw(). */
  K.tool = function (ctx) {
    var p = K.tip; K.tip = null; if (!p) return; ctx.save(); ctx.translate(p.x, p.y);
    if (p.kind === "brush") { ctx.rotate(-0.6); ctx.fillStyle = "#3b2a1a"; ctx.fillRect(-9, -150, 18, 110); ctx.fillStyle = "#b08d3e"; ctx.fillRect(-11, -46, 22, 18); ctx.fillStyle = "#222"; ctx.beginPath(); ctx.moveTo(-10, -28); ctx.lineTo(10, -28); ctx.lineTo(0, 0); ctx.fill(); }
    else if (p.kind === "chalk") { ctx.rotate(-0.5); ctx.fillStyle = "#f4f1e8"; ctx.fillRect(-10, -70, 20, 70); ctx.strokeStyle = "#999"; ctx.lineWidth = 2; ctx.strokeRect(-10, -70, 20, 70); }
    else if (p.kind === "hand") { ctx.fillStyle = "#7a5a3a"; for (var i = 0; i < 4; i++) { ctx.beginPath(); ctx.ellipse(-40 + i * 26, -30 - (i % 2) * 10, 16, 44, -0.2 + i * 0.12, 0, K.TAU); ctx.fill(); } }
    else { ctx.rotate(-0.55); ctx.fillStyle = "#d9a22b"; ctx.fillRect(-8, -140, 16, 116); ctx.fillStyle = "#e9c9a0"; ctx.beginPath(); ctx.moveTo(-8, -24); ctx.lineTo(8, -24); ctx.lineTo(0, 0); ctx.fill(); ctx.fillStyle = "#222"; ctx.beginPath(); ctx.moveTo(-3, -8); ctx.lineTo(3, -8); ctx.lineTo(0, 0); ctx.fill(); ctx.fillStyle = "#c0504a"; ctx.fillRect(-8, -156, 16, 16); }
    ctx.restore();
  };

  window.K = K;
  window.DRAWN = window.DRAWN || { scenes: {}, add: function (s) { this.scenes[s.id] = s; } };
})();
