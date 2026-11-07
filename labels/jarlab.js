// Jar lab: three ways to bottle a film. Every jar is unique (tint, fill line, tag, number, bubbles from its seed);
// the lid is a film reel; the label says CONTAMINANT; the film fills the jar like a liquid, up to its own fill line.
// Each returns {back, front, box, clip}: back and front SVG layers (the film sits between them), the film's box in % of the jar, and its liquid outline (objectBoundingBox).
const R = s => n => { const x = Math.sin((s + 1) * 91.7 + n * 17.3) * 43758.5; return x - Math.floor(x); };
const wave = (y0, amp, ph, x0 = 0, x1 = 1, n = 10) => Array.from({length: n + 1}, (_, i) => { const x = x0 + (x1 - x0) * i / n; return `${x.toFixed(3)} ${(y0 + Math.sin(i * 1.3 + ph) * amp).toFixed(3)}`; }).join(' L');
const reel = (cx, cy, rx, ry, D, A, side = 14) => `
  <path d="M${cx - rx} ${cy}v${side}a${rx} ${ry} 0 0 0 ${2 * rx} 0v-${side}" fill="${D}"/>${Array.from({length: 13}, (_, i) => { const a = Math.PI * (i + .5) / 13, x = cx - Math.cos(a) * rx * .92; return `<rect x="${(x - 2.2).toFixed(1)}" y="${(cy + side * .3 + Math.sin(a) * ry * .55).toFixed(1)}" width="4.4" height="${(side * .42).toFixed(1)}" rx="1" fill="#e8dcc3" opacity=".8"/>`; }).join('')}
  <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${A}" stroke="${D}" stroke-width="3"/>
  ${Array.from({length: 5}, (_, i) => { const a = i / 5 * 6.283 + .3; return `<ellipse cx="${(cx + Math.cos(a) * rx * .55).toFixed(1)}" cy="${(cy + Math.sin(a) * ry * .55).toFixed(1)}" rx="${(rx * .16).toFixed(1)}" ry="${(ry * .26).toFixed(1)}" fill="${D}"/>`; }).join('')}
  <ellipse cx="${cx}" cy="${cy}" rx="${rx * .13}" ry="${ry * .2}" fill="${D}"/><ellipse cx="${cx}" cy="${cy}" rx="${rx * .05}" ry="${ry * .08}" fill="#e8dcc3"/>`;
const bubbles = (r, n, x0, x1, y0, y1) => Array.from({length: n}, (_, i) => `<circle cx="${(x0 + r(i + 30) * (x1 - x0)).toFixed(1)}" cy="${(y0 + r(i + 50) * (y1 - y0)).toFixed(1)}" r="${(1 + r(i + 70) * 3.2).toFixed(1)}" fill="none" stroke="#e6f0f6" stroke-width=".9" opacity="${(.25 + r(i + 90) * .45).toFixed(2)}"/>`).join('');
const glassDefs = (id, tint) => `<defs><linearGradient id="${id}g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/><stop offset=".18" stop-color="#fff" stop-opacity=".02"/><stop offset=".78" stop-color="#fff" stop-opacity="0"/><stop offset=".9" stop-color="#fff" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>
  <linearGradient id="${id}t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${tint}" stop-opacity=".35"/><stop offset="1" stop-color="${tint}" stop-opacity=".7"/></linearGradient></defs>`;

// A · SPECIMEN: a tall lab jar, a kraft tag typed and signed, tied at the neck with string; flecks settle at the bottom
export function specimen(o) {
  const r = R(o.seed), id = 'sp' + o.seed, fill = .3 + r(1) * .25, x0 = 52, x1 = 188, y0 = 74, y1 = 292, fy = y0 + (y1 - y0) * fill, tilt = (r(2) - .5) * 10, no = String(o.no).padStart(2, '0');
  const body = `M${x0 + 18} ${y0}H${x1 - 18}Q${x1} ${y0} ${x1} ${y0 + 18}V${y1 - 16}Q${x1} ${y1} ${x1 - 16} ${y1}H${x0 + 16}Q${x0} ${y1} ${x0} ${y1 - 16}V${y0 + 18}Q${x0} ${y0} ${x0 + 18} ${y0}Z`;
  const liquid = `M${wave((fy - y0) / (y1 - y0), .012, r(3) * 6)} L1 1 L0 1 Z`;
  const back = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="#0b1622" opacity=".55"/><path d="M${x0 + 2} ${fy}${Array.from({length: 11}, (_, i) => `L${x0 + 2 + i * 13.2} ${(fy + Math.sin(i * 1.3 + r(3) * 6) * 2.6).toFixed(1)}`).join('')}V${y1 - 3}H${x0 + 2}Z" fill="url(#${id}t)"/></svg>`;
  const front = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="#c9d8e3" stroke-width="2" stroke-opacity=".7"/>
    ${Array.from({length: 9}, (_, i) => `<path d="M${x1 - 10} ${y1 - 24 - i * 20}h${i % 2 ? 6 : 10}" stroke="#c9d8e3" stroke-width="1" opacity=".55"/>`).join('')}<text x="${x1 - 26}" y="${y1 - 186}" font-family="'JetBrains Mono',monospace" font-size="7" fill="#c9d8e3" opacity=".6">ml</text>
    ${bubbles(r, 9, x0 + 12, x1 - 18, fy + 10, y1 - 14)}${Array.from({length: 22}, (_, i) => `<rect x="${(x0 + 8 + r(i + 110) * (x1 - x0 - 16)).toFixed(1)}" y="${(y1 - 8 - r(i + 140) * 12).toFixed(1)}" width="3.4" height="2.6" rx=".6" fill="#e8dcc3" opacity=".5" transform="rotate(${(r(i + 160) * 80 - 40).toFixed(0)} ${(x0 + 8 + r(i + 110) * (x1 - x0 - 16)).toFixed(1)} ${(y1 - 8).toFixed(1)})"/>`).join('')}
    <rect x="${x0 - 4}" y="${y0 - 10}" width="${x1 - x0 + 8}" height="12" rx="4" fill="#2a3440"/>${reel(120, 46, 74, 17, o.ink, o.lid, 16)}
    <path d="M${x0 + 6} ${y0 - 2}C${x0 - 8} ${y0 + 30} ${x0 + 20} ${y0 + 70} ${x0 + 40} ${y0 + 96}" fill="none" stroke="#cdb48a" stroke-width="1.4"/>
    <g transform="translate(${x0 + 30} ${y0 + 92}) rotate(${tilt})"><path d="M0 0H118L126 8V66L118 74H0Z" fill="#d9c39a"/><circle cx="10" cy="10" r="3.4" fill="#0b1622" opacity=".8"/>
      <text x="22" y="20" font-family="Anton,Impact,sans-serif" font-size="13" letter-spacing="1.2" fill="#1d2430">CONTAMINANT</text>
      <text x="8" y="38" font-family="'Courier Prime','Courier New',monospace" font-weight="700" font-size="9.5" fill="#1d2430" textLength="${Math.min(110, 8 + (o.name.length + 9) * 5.8).toFixed(0)}" lengthAdjust="spacingAndGlyphs">No. ${no} · ${o.name.toUpperCase()}</text>
      <text x="8" y="50" font-family="'Courier Prime','Courier New',monospace" font-size="8" fill="#3a4250">from ${o.src}</text>
      <text x="8" y="66" font-family="Caveat,cursive" font-size="15" fill="#7a2f22">${o.note}</text></g></svg>`;
  return {back, front, box: [x0 / 240, y0 / 320, (x1 - x0) / 240, (y1 - y0) / 320], clip: liquid};
}

// B · APOTHECARY: a round-bellied flask, a small reel stopper, an enamel plaque; the film swirls in the bulb
export function apothecary(o) {
  const r = R(o.seed + 7), id = 'ap' + o.seed, cx = 120, cy = 206, rr = 86, fill = .28 + r(1) * .3, fy = cy - rr + 2 * rr * fill;
  const body = `M106 78V122C64 134 34 168 34 206A86 86 0 1 0 206 206C206 168 176 134 134 122V78Z`;
  const bx = 34, by = 78, bw = 172, bh = 214, ny = (fy - by) / bh;
  const liquid = `M${wave(ny, .012, r(3) * 6, 0, 1)} L1 1 L0 1 Z`;
  const back = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="#0b1622" opacity=".55"/><clipPath id="${id}c"><path d="${body}"/></clipPath><rect x="0" y="${fy}" width="240" height="320" fill="url(#${id}t)" clip-path="url(#${id}c)"/></svg>`;
  const front = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="#c9d8e3" stroke-width="2" stroke-opacity=".7"/>
    <path d="M60 170Q72 146 96 136" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".18"/>${bubbles(r, 8, 70, 170, fy + 8, 270)}
    <rect x="100" y="70" width="40" height="10" rx="3" fill="#2a3440"/>${reel(120, 56, 40, 10, o.ink, o.lid, 12)}
    <g transform="translate(120 ${cy + 18})"><ellipse cx="0" cy="0" rx="58" ry="36" fill="#f0e6d2" stroke="${o.ink}" stroke-width="3"/><ellipse cx="0" cy="0" rx="51" ry="29" fill="none" stroke="${o.lid}" stroke-width="1.4"/>
      <text x="0" y="-9" text-anchor="middle" font-family="Anton,Impact,sans-serif" font-size="11" letter-spacing="1.6" fill="${o.ink}">CONTAMINANT</text>
      <text x="0" y="9" text-anchor="middle" font-family="Jost,system-ui,sans-serif" font-weight="400" font-size="14" fill="#1d2430" ${o.name.length > 11 ? 'textLength="88" lengthAdjust="spacingAndGlyphs"' : ''}>${o.name}</text>
      <text x="0" y="22" text-anchor="middle" font-family="'Courier Prime',monospace" font-size="7.5" fill="#5a6270">No. ${String(o.no).padStart(2, '0')}</text></g>
    <text x="${cx + 54}" y="${cy + 72}" font-family="Caveat,cursive" font-size="14" fill="#e6c79a" transform="rotate(-8 ${cx + 54} ${cy + 72})">${o.note}</text></svg>`;
  return {back, front, box: [bx / 240, by / 320, bw / 240, bh / 320], clip: liquid, body: 'flask'};
}

// C · PRESERVE: a wide preserving jar with CONTAMINANT embossed in the glass, a reel for a lid, a kraft tag on twine and a hand-drawn fill line
export function preserve(o) {
  const r = R(o.seed + 13), id = 'pr' + o.seed, x0 = 40, x1 = 200, y0 = 84, y1 = 296, fill = .24 + r(1) * .3, fy = y0 + (y1 - y0) * fill, tilt = 8 + r(2) * 14;
  const body = `M64 ${y0}H176Q178 ${y0 + 14} 192 ${y0 + 26}Q${x1} ${y0 + 34} ${x1} ${y0 + 52}V${y1 - 26}Q${x1} ${y1} 172 ${y1}H68Q${x0} ${y1} ${x0} ${y1 - 26}V${y0 + 52}Q${x0} ${y0 + 34} 48 ${y0 + 26}Q62 ${y0 + 14} 64 ${y0}Z`;
  const liquid = `M${wave((fy - y0) / (y1 - y0), .01, r(3) * 6)} L1 1 L0 1 Z`;
  const back = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="#0b1622" opacity=".55"/><clipPath id="${id}c"><path d="${body}"/></clipPath><rect x="0" y="${fy}" width="240" height="320" fill="url(#${id}t)" clip-path="url(#${id}c)"/></svg>`;
  const front = `<svg viewBox="0 0 240 320">${glassDefs(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="#c9d8e3" stroke-width="2" stroke-opacity=".7"/>
    <text x="120" y="${y0 + 66}" text-anchor="middle" font-family="Anton,Impact,sans-serif" font-size="22" letter-spacing="2" fill="none" stroke="#e6f0f6" stroke-width=".9" opacity=".55" textLength="138" lengthAdjust="spacingAndGlyphs">CONTAMINANT</text>
    <text x="120" y="${y0 + 84}" text-anchor="middle" font-family="Jost,system-ui,sans-serif" font-size="10" letter-spacing="4" fill="#e6f0f6" opacity=".45">JELLY-FILMS</text>
    <path d="M${x0 + 8} ${fy - 1}q20 -4 40 0t40 0" fill="none" stroke="#e6c79a" stroke-width="1.6" stroke-dasharray="3 3" opacity=".8"/><text x="${x0 + 92}" y="${fy + 3}" font-family="Caveat,cursive" font-size="13" fill="#e6c79a">fill to here</text>
    ${bubbles(r, 10, x0 + 14, x1 - 14, fy + 12, y1 - 12)}
    <rect x="60" y="${y0 - 10}" width="120" height="14" rx="4" fill="#2a3440"/>${reel(120, 60, 66, 15, o.ink, o.lid, 14)}
    <path d="M176 ${y0 - 2}Q206 ${y0 + 6} 208 ${y0 + 30}" fill="none" stroke="#cdb48a" stroke-width="1.3"/>
    <g transform="translate(196 ${y0 + 28}) rotate(${tilt})"><path d="M0 0L10 -8H62V44H10L0 36Z" fill="#cfb488"/><circle cx="9" cy="18" r="2.8" fill="#0b1622"/>
      <text x="16" y="10" font-family="'Courier Prime',monospace" font-weight="700" font-size="7.5" fill="#1d2430">No. ${String(o.no).padStart(2, '0')}</text>
      <text x="16" y="22" font-family="Caveat,cursive" font-size="12" fill="#1d2430">${o.name.length > 10 ? o.name.split(' ').slice(-1)[0] : o.name}</text>
      <text x="16" y="34" font-family="'Courier Prime',monospace" font-size="6.2" fill="#3a4250">${o.src.slice(0, 13)}</text></g></svg>`;
  return {back, front, box: [x0 / 240, y0 / 320, (x1 - x0) / 240, (y1 - y0) / 320], clip: liquid};
}

// a jar on a shelf: back, the film (clipped to its liquid), front; returns the html and the clip-path defs it needs
export function bottle(kind, o) {
  const J = {specimen, apothecary, preserve}[kind](o), [l, t, w, h] = J.box.map(v => (v * 100).toFixed(2) + '%'), cid = `${kind}-${o.seed}-liq`;
  const bodyClip = kind === 'apothecary' ? 'M.419 0V.206C.174 .262 0 .421 0 .598A.5 .402 0 1 0 1 .598C1 .421 .826 .262 .581 .206V0Z' : null;
  const defs = `<clipPath id="${cid}" clipPathUnits="objectBoundingBox"><path d="${J.clip}"/></clipPath>${bodyClip ? `<clipPath id="${cid}b" clipPathUnits="objectBoundingBox"><path d="${bodyClip}"/></clipPath>` : ''}`;
  const film = (cls, poster) => `<div class="lq ${cls}" style="left:${l};top:${t};width:${w};height:${h};${bodyClip ? `clip-path:url(#${cid}b)` : 'border-radius:7%'}"><video muted loop playsinline preload="none" ${poster ? `poster="${poster}"` : ''} style="clip-path:url(#${cid})"></video></div>`;
  return {html: `<div class="bt ${kind}">${J.back}${film('f', o.poster)}${film('g', '')}${J.front}</div>`, defs};
}
export const BOTTLE_CSS = `.bt{position:relative;aspect-ratio:240/320}.bt>svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .bt .lq{position:absolute;overflow:hidden}.bt .lq video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.75) contrast(1.05);opacity:.5;transition:opacity .7s}
  .bt .lq.g video{opacity:0}.bt.live .lq.f video{opacity:.95}.bt.live.game .lq.f video{opacity:0}.bt.live.game .lq.g video{opacity:.95}`;
