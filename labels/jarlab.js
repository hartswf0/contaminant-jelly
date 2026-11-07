// Jar lab: three ways to bottle a film, drawn to stay crisp and readable at any size.
// Every jar is unique (tint, fill line, number, bubbles from its seed); the lid is a film reel; the label says CONTAMINANT; the film fills the jar like a liquid.
// Labels sit on the jar's centre line with one hierarchy: CONTAMINANT (small caps) · the name (large, wrapped to two lines when long) · the number.
// Anything with class "fine" (notes, string, ticks, sources) hides when the jar is drawn small (see BOTTLE_CSS).
// Each returns {back, front, box, clip}: the film sits between back and front; box is its rectangle in % of the jar; clip is its liquid outline (objectBoundingBox).
const R = s => n => { const x = Math.sin((s + 1) * 91.7 + n * 17.3) * 43758.5; return x - Math.floor(x); };
const SVG = inner => `<svg viewBox="0 0 240 320" shape-rendering="geometricPrecision" text-rendering="geometricPrecision">${inner}</svg>`;
const INK = '#141b26', PAPER = '#efe4cc', KRAFT = '#d8c299', LINE = '#cfdde8';
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
// the name, fitted: one line if it fits, else two balanced lines; never smaller than min
function nameText(name, cx, cy, maxW, base, min, fill, family = 'Jost,system-ui,sans-serif', weight = 500, k = .55) {
  const w = s => s.length * k;   // width per unit of font size
  let lines = [name], size = Math.min(base, maxW / w(name));
  if (size < base * .8 && name.includes(' ')) { const words = name.split(' '); let best = null;
    for (let i = 1; i < words.length; i++) { const a = words.slice(0, i).join(' '), b = words.slice(i).join(' '), m = Math.max(w(a), w(b)); if (!best || m < best.m) best = {a, b, m}; }
    lines = [best.a, best.b]; size = Math.min(base * .86, maxW / best.m); }
  size = Math.max(min, size); const lh = size * 1.02, y0 = cy - (lines.length - 1) * lh / 2 + size * .34;
  return lines.map((l, i) => `<text x="${cx}" y="${(y0 + i * lh).toFixed(1)}" text-anchor="middle" font-family="${family}" font-weight="${weight}" font-size="${size.toFixed(1)}" fill="${fill}"${w(l) * size > maxW ? ` textLength="${maxW}" lengthAdjust="spacingAndGlyphs"` : ''}>${esc(l)}</text>`).join('');
}
const caps = (t, cx, y, size, fill, track = 1.6, cls = '') => `<text${cls ? ` class="${cls}"` : ''} x="${cx}" y="${y}" text-anchor="middle" font-family="Anton,Impact,'Arial Narrow',sans-serif" font-size="${size}" letter-spacing="${track}" fill="${fill}">${t}</text>`;
const mono = (t, x, y, size, fill, anchor = 'middle', cls = '') => `<text${cls ? ` class="${cls}"` : ''} x="${x}" y="${y}" text-anchor="${anchor}" font-family="'Courier Prime','Courier New',monospace" font-weight="700" font-size="${size}" fill="${fill}">${esc(t)}</text>`;
const reel = (cx, cy, rx, ry, D, A, side) => `<path d="M${cx - rx} ${cy}v${side}a${rx} ${ry} 0 0 0 ${2 * rx} 0v-${side}" fill="${D}"/>`
  + Array.from({length: 11}, (_, i) => { const a = Math.PI * (i + .5) / 11, x = cx - Math.cos(a) * rx * .9; return `<rect x="${(x - 2.4).toFixed(1)}" y="${(cy + side * .32 + Math.sin(a) * ry * .5).toFixed(1)}" width="4.8" height="${(side * .4).toFixed(1)}" rx="1" fill="${PAPER}" opacity=".85"/>`; }).join('')
  + `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${A}" stroke="${D}" stroke-width="3"/>`
  + Array.from({length: 5}, (_, i) => { const a = i / 5 * 6.283 + .3; return `<ellipse cx="${(cx + Math.cos(a) * rx * .56).toFixed(1)}" cy="${(cy + Math.sin(a) * ry * .56).toFixed(1)}" rx="${(rx * .17).toFixed(1)}" ry="${(ry * .27).toFixed(1)}" fill="${D}"/>`; }).join('')
  + `<ellipse cx="${cx}" cy="${cy}" rx="${(rx * .14).toFixed(1)}" ry="${(ry * .22).toFixed(1)}" fill="${D}"/><ellipse cx="${cx}" cy="${cy}" rx="${(rx * .05).toFixed(1)}" ry="${(ry * .08).toFixed(1)}" fill="${PAPER}"/>`;
const bubbles = (r, n, x0, x1, y0, y1) => `<g class="fine">${Array.from({length: n}, (_, i) => `<circle cx="${(x0 + r(i + 30) * (x1 - x0)).toFixed(1)}" cy="${(y0 + r(i + 50) * (y1 - y0)).toFixed(1)}" r="${(1.4 + r(i + 70) * 3).toFixed(1)}" fill="none" stroke="#e6f0f6" stroke-width="1" opacity="${(.3 + r(i + 90) * .4).toFixed(2)}"/>`).join('')}</g>`;
const glass = (id, tint) => `<defs><linearGradient id="${id}g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".16" stop-color="#fff" stop-opacity=".03"/><stop offset=".8" stop-color="#fff" stop-opacity="0"/><stop offset=".92" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity=".04"/></linearGradient>
  <linearGradient id="${id}t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${tint}" stop-opacity=".4"/><stop offset="1" stop-color="${tint}" stop-opacity=".75"/></linearGradient></defs>`;
const surf = (x0, x1, fy, ph) => Array.from({length: 13}, (_, i) => `${i ? 'L' : 'M'}${(x0 + (x1 - x0) * i / 12).toFixed(1)} ${(fy + Math.sin(i * 1.25 + ph) * 2.2).toFixed(1)}`).join('');
const wave = (y, ph) => Array.from({length: 13}, (_, i) => `${i ? 'L' : 'M'}${(i / 12).toFixed(3)} ${(y + Math.sin(i * 1.25 + ph) * .01).toFixed(3)}`).join('') + ' L1 1 L0 1 Z';

// A · SPECIMEN: a tall graduated lab jar; a flat paper label on its front; a red-ink note underneath
export function specimen(o) {
  const r = R(o.seed), id = 'sp' + o.seed, x0 = 54, x1 = 186, y0 = 76, y1 = 294, fill = .28 + r(1) * .2, fy = y0 + (y1 - y0) * fill, ph = r(3) * 6, no = String(o.no).padStart(2, '0'), tilt = ((r(2) - .5) * 3).toFixed(1);
  const body = `M${x0 + 16} ${y0}H${x1 - 16}Q${x1} ${y0} ${x1} ${y0 + 16}V${y1 - 14}Q${x1} ${y1} ${x1 - 14} ${y1}H${x0 + 14}Q${x0} ${y1} ${x0} ${y1 - 14}V${y0 + 16}Q${x0} ${y0} ${x0 + 16} ${y0}Z`;
  const back = SVG(`${glass(id, o.tint)}<path d="${body}" fill="#0a141f" opacity=".6"/><clipPath id="${id}c"><path d="${body}"/></clipPath><path d="${surf(x0, x1, fy, ph)}V${y1}H${x0}Z" fill="url(#${id}t)" clip-path="url(#${id}c)"/>`);
  const lx = 70, lw = 100, ly = 156, lh = 78;
  const front = SVG(`${glass(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="${LINE}" stroke-width="2.2" stroke-opacity=".75"/>
    <g class="fine" stroke="${LINE}" stroke-width="1.2" opacity=".55">${Array.from({length: 8}, (_, i) => `<path d="M${x1 - 12} ${y1 - 26 - i * 22}h${i % 2 ? 6 : 10}"/>`).join('')}</g>
    ${bubbles(r, 8, x0 + 14, x1 - 20, fy + 12, y1 - 18)}
    <rect x="${x0 - 4}" y="${y0 - 12}" width="${x1 - x0 + 8}" height="14" rx="4" fill="#26303c"/>${reel(120, 46, 74, 17, o.ink, o.lid, 18)}
    <g transform="rotate(${tilt} 120 ${ly + lh / 2})"><rect x="${lx}" y="${ly}" width="${lw}" height="${lh}" rx="3" fill="${PAPER}"/><rect x="${lx}" y="${ly}" width="${lw}" height="17" rx="3" fill="${o.ink}"/><rect x="${lx}" y="${ly + 12}" width="${lw}" height="5" fill="${o.ink}"/>
      ${caps('CONTAMINANT', 120, ly + 12.6, 10.5, PAPER, 2)}${nameText(o.name, 120, ly + 42, lw - 14, 20, 13, INK)}
      <path d="M${lx + 8} ${ly + lh - 17}H${lx + lw - 8}" stroke="${o.ink}" stroke-width="1" opacity=".5"/>${mono('No. ' + no, 120, ly + lh - 6, 10, o.ink)}</g>
    <text class="fine" x="120" y="${ly + lh + 22}" text-anchor="middle" font-family="Caveat,cursive" font-size="17" fill="#e8b88a">${esc(o.note)}</text>`);
  return {back, front, box: [x0 / 240, y0 / 320, (x1 - x0) / 240, (y1 - y0) / 320], clip: wave((fy - y0) / (y1 - y0), ph)};
}

// B · APOTHECARY: a round-bellied flask, a reel stopper, an oval enamel plaque centred on the bulb
export function apothecary(o) {
  const r = R(o.seed + 7), id = 'ap' + o.seed, cx = 120, cy = 208, rr = 84, fill = .22 + r(1) * .22, fy = cy - rr + 2 * rr * fill, ph = r(3) * 6;
  const body = `M104 82V124C62 136 36 168 36 208A84 84 0 1 0 204 208C204 168 178 136 136 124V82Z`, bx = 36, by = 82, bw = 168, bh = 210;
  const back = SVG(`${glass(id, o.tint)}<path d="${body}" fill="#0a141f" opacity=".6"/><clipPath id="${id}c"><path d="${body}"/></clipPath><path d="${surf(bx, bx + bw, fy, ph)}V320H${bx}Z" fill="url(#${id}t)" clip-path="url(#${id}c)"/>`);
  const front = SVG(`${glass(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="${LINE}" stroke-width="2.2" stroke-opacity=".75"/>
    <path class="fine" d="M62 172Q74 148 98 138" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".2"/>${bubbles(r, 7, 66, 174, fy + 10, 268)}
    <rect x="98" y="72" width="44" height="12" rx="3" fill="#26303c"/>${reel(120, 56, 44, 11, o.ink, o.lid, 14)}
    <g transform="translate(${cx} ${cy + 12})"><ellipse rx="62" ry="40" fill="${PAPER}" stroke="${o.ink}" stroke-width="3.5"/><ellipse class="fine" rx="54" ry="32" fill="none" stroke="${o.lid}" stroke-width="1.5"/>
      ${caps('CONTAMINANT', 0, -17, 10, o.ink, 1.8)}${nameText(o.name, 0, 2, 90, 17, 11.5, INK)}${mono('No. ' + String(o.no).padStart(2, '0'), 0, 27, 9.5, o.ink)}</g>`);
  return {back, front, box: [bx / 240, by / 320, bw / 240, bh / 320], clip: wave((fy - by) / bh, ph), flask: true};
}

// C · PRESERVE: a wide preserving jar with CONTAMINANT pressed into the glass, a reel lid, a round batch seal on its front
export function preserve(o) {
  const r = R(o.seed + 13), id = 'pr' + o.seed, x0 = 40, x1 = 200, y0 = 86, y1 = 296, fill = .2 + r(1) * .22, fy = y0 + (y1 - y0) * fill, ph = r(3) * 6, no = String(o.no).padStart(2, '0');
  const body = `M64 ${y0}H176Q178 ${y0 + 14} 192 ${y0 + 26}Q${x1} ${y0 + 34} ${x1} ${y0 + 52}V${y1 - 26}Q${x1} ${y1} 172 ${y1}H68Q${x0} ${y1} ${x0} ${y1 - 26}V${y0 + 52}Q${x0} ${y0 + 34} 48 ${y0 + 26}Q62 ${y0 + 14} 64 ${y0}Z`;
  const back = SVG(`${glass(id, o.tint)}<path d="${body}" fill="#0a141f" opacity=".6"/><clipPath id="${id}c"><path d="${body}"/></clipPath><path d="${surf(x0, x1, fy, ph)}V${y1}H${x0}Z" fill="url(#${id}t)" clip-path="url(#${id}c)"/>`);
  const sy = y1 - 50;
  const front = SVG(`${glass(id, o.tint)}<path d="${body}" fill="url(#${id}g)" stroke="${LINE}" stroke-width="2.2" stroke-opacity=".75"/>
    <text x="120" y="${y0 + 62}" text-anchor="middle" font-family="Anton,Impact,sans-serif" font-size="20" letter-spacing="2.2" fill="#eef4f8" opacity=".26" textLength="128" lengthAdjust="spacingAndGlyphs">CONTAMINANT</text>
    <text class="fine" x="120" y="${y0 + 78}" text-anchor="middle" font-family="Jost,system-ui,sans-serif" font-weight="400" font-size="9" letter-spacing="4" fill="#eef4f8" opacity=".5">JELLY-FILMS</text>
    <path class="fine" d="M${x0 + 8} ${(fy - 3).toFixed(1)}H${x0 + 26}" stroke="#e8b88a" stroke-width="1.8" stroke-linecap="round"/>
    ${bubbles(r, 9, x0 + 16, x1 - 16, fy + 14, sy - 30)}
    <rect x="60" y="${y0 - 12}" width="120" height="16" rx="4" fill="#26303c"/>${reel(120, 60, 68, 16, o.ink, o.lid, 16)}
    <g transform="translate(120 ${sy})"><circle r="38" fill="${KRAFT}" stroke="${o.ink}" stroke-width="3"/><circle class="fine" r="32" fill="none" stroke="${o.ink}" stroke-width="1" stroke-dasharray="2 2.4"/>
      ${caps('BATCH', 0, -18, 8.5, o.ink, 2.4)}${mono('No. ' + no, 0, -3, 13, o.ink)}${nameText(o.name, 0, 16, 56, 12, 9, INK, 'Jost,system-ui,sans-serif', 500, .55)}</g>`);
  return {back, front, box: [x0 / 240, y0 / 320, (x1 - x0) / 240, (y1 - y0) / 320], clip: wave((fy - y0) / (y1 - y0), ph)};
}

// a jar on a shelf: back, the film (clipped to its liquid), front; returns the html and the clip-path defs it needs
export function bottle(kind, o) {
  const J = {specimen, apothecary, preserve}[kind](o), [l, t, w, h] = J.box.map(v => (v * 100).toFixed(2) + '%'), cid = `${kind}-${o.seed}-liq`;
  const flask = J.flask ? 'M.405 0V.2C.155 .257 0 .41 0 .6A.5 .4 0 1 0 1 .6C1 .41 .845 .257 .595 .2V0Z' : null;
  const defs = `<clipPath id="${cid}" clipPathUnits="objectBoundingBox"><path d="${J.clip}"/></clipPath>${flask ? `<clipPath id="${cid}b" clipPathUnits="objectBoundingBox"><path d="${flask}"/></clipPath>` : ''}`;
  const film = (cls, poster) => `<div class="lq ${cls}" style="left:${l};top:${t};width:${w};height:${h};${flask ? `clip-path:url(#${cid}b)` : 'border-radius:7%'}"><video muted loop playsinline preload="none" ${poster ? `poster="${poster}"` : ''} style="clip-path:url(#${cid})"></video></div>`;
  return {html: `<div class="bt ${kind}">${J.back}${film('f', o.poster)}${film('g', '')}${J.front}</div>`, defs};
}
export const BOTTLE_CSS = `.bt{position:relative;aspect-ratio:240/320;container-type:inline-size}.bt>svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .bt .lq{position:absolute;overflow:hidden}.bt .lq video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.8) contrast(1.06);opacity:.55;transition:opacity .7s}
  .bt .lq.g video{opacity:0}.bt.live .lq.f video{opacity:.96}.bt.live.game .lq.f video{opacity:0}.bt.live.game .lq.g video{opacity:.96}
  @container (max-width: 150px){.bt .fine{display:none}}`;
