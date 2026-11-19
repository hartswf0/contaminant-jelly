/* Porthole 07 · Hatch · River Choir around sunken Birthday Piñata
 * Feedstock: submarines (rubbed sepia paper, traced pencil line, pale search cone in a grainy field).
 * Made in this order, as a hand would: paper, the rope, the star, its stripes, the choir one fish at a time,
 * the lamp's cone. Then it lives: the star swings and the choir opens its mouths in turn.
 * Rule held: Sound-Action (pitch shift) — each fish's mouth opens wider the higher it sits. */
(function () {
  var STRIPES = ["#c95c3e", "#d9a22b", "#3f8f84", "#7b5aa6", "#c95c3e"];
  function fish(K, cx, cy, s, flip) {
    var k = flip ? -1 : 1;
    return K.curve([[cx - 70 * s * k, cy], [cx - 30 * s * k, cy - 26 * s], [cx + 40 * s * k, cy - 20 * s], [cx + 78 * s * k, cy], [cx + 40 * s * k, cy + 20 * s],
                    [cx - 30 * s * k, cy + 24 * s], [cx - 70 * s * k, cy], [cx - 104 * s * k, cy - 24 * s], [cx - 96 * s * k, cy + 24 * s], [cx - 70 * s * k, cy]], 8);
  }
  var CHOIR = [[250, 330, 0.95, false], [760, 300, 1.0, true], [200, 560, 1.1, false], [800, 540, 1.05, true], [330, 760, 1.0, false], [680, 770, 0.95, true]];
  DRAWN.add({
    id: 7, title: "River Choir around sunken Birthday Piñata",
    style: "Rubbed sepia paper and a traced pencil line; the lamp is a pale cone. The choir is drawn one fish at a time.",
    scions: ["7 · Peter Foldès — Drawn Metamorphosis (a line that keeps becoming)", "2 · Lotte Reiniger — Articulated Shadow Theater (the star hangs from one hinge)", "47 · Sound-to-Action (mouths open to the pitch)"],
    draw: function (ctx, t, K) {
      var live = K.prog(t, 8, 8.6), swing = Math.sin(t * 1.7) * 0.16 * live;
      K.paper(ctx, "#d8c7a3", 0.09);
      var star = [], R = 120, r = 52;
      for (var i = 0; i < 10; i++) { var a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r : R; star.push([500 + rr * Math.cos(a), 470 + rr * Math.sin(a)]); }
      var cone = [[500, 990], [330, 560], [670, 560]];
      K.seq(t, [
        [0.9, function (u) { K.fill(ctx, [[60, 60], [940, 60], [940, 940], [60, 940]], u, "#7fa7a0", "wash", { rows: 7, alpha: 0.55 }); }],
        [0.7, function (u) { K.stroke(ctx, K.line(500, 60, 500, 350, 20), u, { color: "#3b2a1a", width: 7, seed: 3 }); }],
        [1.3, function (u) {
          ctx.save(); ctx.translate(500, 350); ctx.rotate(swing); ctx.translate(-500, -350);
          K.stroke(ctx, K.poly(star, true), u, { color: "#2a2018", width: 6, seed: 9 });
          ctx.restore();
        }],
        [1.5, function (u) {
          ctx.save(); ctx.translate(500, 350); ctx.rotate(swing); ctx.translate(-500, -350);
          for (var s = 0; s < 5; s++) {
            var band = [[380, 350 + s * 48], [620, 350 + s * 48], [620, 398 + s * 48], [380, 398 + s * 48]];
            ctx.save(); ctx.beginPath(); star.forEach(function (p, j) { j ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); }); ctx.closePath(); ctx.clip();
            K.fill(ctx, band, K.prog(u, s / 5, (s + 1) / 5), STRIPES[s], "hatch", { gap: 7, width: 4 });
            ctx.restore();
          }
          K.stroke(ctx, K.poly(star, true), 1, { color: "#2a2018", width: 6, seed: 9 });
          ctx.restore();
        }],
        [2.4, function (u) {
          CHOIR.forEach(function (f, i) {
            var uu = K.prog(u, i / 6, (i + 1) / 6), bob = Math.sin(t * 2 + i) * 6 * live;
            var body = K.move(fish(K, f[0], f[1], f[2], f[3]), 0, bob);
            K.stroke(ctx, body, uu, { color: "#2a2018", width: 5, seed: 20 + i });
            if (uu >= 1) {
              var k = f[3] ? -1 : 1, open = live * (0.5 + 0.5 * Math.sin(t * 5 - i * 0.9)) * (1.4 - f[1] / 800);
              ctx.fillStyle = "#2a2018"; ctx.beginPath(); ctx.ellipse(f[0] + 66 * f[2] * k, f[1] + bob, 7, 3 + 12 * Math.max(0, open), 0, 0, K.TAU); ctx.fill();
              ctx.beginPath(); ctx.arc(f[0] + 44 * f[2] * k, f[1] - 8 * f[2] + bob, 4, 0, K.TAU); ctx.fill();
            }
          });
        }],
        [1.2, function (u) { K.fill(ctx, cone, u, "#f4e3a6", "wash", { rows: 5, alpha: 0.38 }); }],
      ]);
      if (live > 0) {                                   // the notes the choir sends up
        for (var n = 0; n < 6; n++) {
          var f = CHOIR[n], ph = (t * 0.5 + n * 0.17) % 1, k = f[3] ? -1 : 1;
          ctx.globalAlpha = (1 - ph) * live; ctx.strokeStyle = "#2a2018"; ctx.lineWidth = 3;
          ctx.beginPath(); ctx.arc(f[0] + (80 + ph * 60) * k, f[1] - ph * 70, 6 + ph * 10, 0, K.TAU); ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
    }
  });
})();
