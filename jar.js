// The jelly jar, as glass drawn in light: three outlines of the same jar, offset like frames of film (1 → 2 → 3),
// crosshair ticks, and inside the front jar a translucent jelly, or a film playing in the glass.
//   import {jarSVG, jarDefs, JAR_CSS} from './jar.js';
//   document.body.insertAdjacentHTML('beforeend', jarDefs());     // once per page: the clip the films are cut to
//   el.innerHTML = jarSVG({seed: 3, sym: 'Wd'});                  // sym only for the periodic table
//   <video style="clip-path:url(#jar-glass)" class="jar-film">      // a film inside the glass: place it with .jar-film
const BODY = 'M70 46C70 60 40 62 40 92V196Q40 222 66 222H134Q160 222 160 196V92C160 62 130 60 130 46';   // viewBox 0 0 200 240
const LID = 'M62 22Q62 18 66 18H134Q138 18 138 22V30Q138 34 134 34H66Q62 34 62 30Z', NECK = 'M70 34V46M130 34V46';
const jarPath = (dx, dy) => `<g transform="translate(${dx} ${dy})"><path d="${LID}"/><path d="${NECK}"/><path d="${BODY}"/></g>`;

export function jarSVG({seed = 0, sym = '', glow = '#f0a35a', ink = '#b7c9d8', jelly = true} = {}) {
  const r = n => { const x = Math.sin((seed + 1) * 99.7 + n * 12.9) * 43758.5; return x - Math.floor(x); };
  const tilt = (r(1) - .5) * 16, sway = 6 + r(2) * 6, tx = 100 + (r(3) - .5) * 10, id = 'j' + seed + Math.floor(r(9) * 1e6);
  const tent = [-18, -6, 6, 18].map((x, i) => `<path d="M${x} 10c${i % 2 ? sway : -sway} 18 ${i % 2 ? -sway : sway} 30 0 ${46 + r(i + 4) * 18}" ${i === 1 ? 'stroke-dasharray="3 2.2" stroke-width="2.2"' : ''}/>`).join('');
  const holes = Array.from({length: 11}, (_, i) => `<rect x="${-30 + i * 5.6}" y="3.4" width="2.6" height="2.2" rx=".6"/>`).join('');
  return `<svg class="jar-svg" viewBox="0 0 200 240" aria-hidden="true"><defs>
      <radialGradient id="${id}g" cx="72%" cy="40%" r="70%"><stop offset="0" stop-color="${glow}" stop-opacity=".9"/><stop offset=".45" stop-color="${glow}" stop-opacity=".15"/><stop offset="1" stop-color="#7fa3c7" stop-opacity="0"/></radialGradient>
      <radialGradient id="${id}b" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="#c9dcec" stop-opacity=".55"/><stop offset=".7" stop-color="#6d8fb2" stop-opacity=".18"/><stop offset="1" stop-color="#6d8fb2" stop-opacity=".05"/></radialGradient></defs>
    <g fill="none" stroke="${ink}" stroke-width=".9" stroke-linejoin="round">
      <g opacity=".18">${jarPath(-14, -12)}</g><g opacity=".32">${jarPath(-7, -6)}</g><g opacity=".7">${jarPath(0, 0)}</g>
      <g opacity=".55" stroke-width=".8"><path d="M100 38v6M100 216v8M34 140h8M158 140h8"/><path d="M86 31v5M27 128h6"/></g></g>
    ${jelly ? `<g class="jar-jelly" transform="translate(${tx} 120) rotate(${tilt})"><g fill="none" stroke="#9fbad3" stroke-width="1.3" stroke-linecap="round" opacity=".75">${tent}</g>
      <path d="M-34 6C-34 -22 -18 -36 0 -36S34 -22 34 6Q0 12 -34 6Z" fill="url(#${id}b)" stroke="#c9dcec" stroke-width="1" stroke-opacity=".7"/>
      <path d="M-34 6C-34 -22 -18 -36 0 -36S34 -22 34 6Q0 12 -34 6Z" fill="url(#${id}g)"/>
      <path d="M-33 2Q0 9 33 2V8Q0 14 -33 8Z" fill="#c9dcec" opacity=".55"/><g fill="#081221" opacity=".8">${holes}</g></g>` : ''}
    ${sym ? `<text x="100" y="${jelly ? 200 : 150}" text-anchor="middle" font-family="Jost,system-ui,sans-serif" font-weight="300" font-size="${jelly ? 22 : 46}" fill="#dfe9f2" letter-spacing="1">${sym}</text>` : ''}
    <g fill="#8aa0b4" font-family="Jost,system-ui,sans-serif" font-size="7.5" font-style="italic" opacity=".7"><text x="18" y="236">1 →</text><text x="40" y="236">2 →</text><text x="62" y="236">3</text></g></svg>`;
}
// the glass as a clip for a film: objectBoundingBox units, fitted to the body's box (x 40..160, y 46..222)
export const jarDefs = () => `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><clipPath id="jar-glass" clipPathUnits="objectBoundingBox">
  <path d="M.25 0C.25 .08 0 .09 0 .26V.85Q0 1 .217 1H.783Q1 1 1 .85V.26C1 .09 .75 .08 .75 0Z"/></clipPath></svg>`;
export const JAR_CSS = `.jar-box{position:relative;aspect-ratio:200/240}.jar-box .jar-svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .jar-film{position:absolute;left:20%;top:19.2%;width:60%;height:73.3%;object-fit:cover;clip-path:url(#jar-glass);opacity:0;transition:opacity .6s;mix-blend-mode:screen;filter:saturate(.7) contrast(1.05) brightness(1.05)}
  .jar-film.on{opacity:.92}.jar-box .jar-jelly{transition:opacity .6s}.jar-box.live .jar-jelly{opacity:.12}`;

// The coloured jar (labels/jars, labels/cineosis), with the glass outlines behind it as ghosts (1 → 2 → 3): the brand and the water together.
// The film plays in the label window. art: path to the jar svg.
const CJ = 'M64 78Q66 93 52 102Q38 113 38 141L40 290Q41 315 53 321Q160 336 267 321Q279 315 280 290L282 141Q282 113 268 102Q254 93 256 78Z';
export const jarCard = ({art, alt = ''}) => `<div class="jc"><svg class="jc-ghost" viewBox="0 0 320 350" aria-hidden="true"><g fill="none" stroke="#b7c9d8" stroke-width="1.3">
    <g opacity=".22" transform="translate(-22 -18)"><ellipse cx="160" cy="60" rx="90" ry="27"/><path d="${CJ}"/></g><g opacity=".38" transform="translate(-11 -9)"><ellipse cx="160" cy="60" rx="90" ry="27"/><path d="${CJ}"/></g></g>
    <g fill="#8aa0b4" font-family="Jost,system-ui,sans-serif" font-size="12" font-style="italic" opacity=".6"><text x="4" y="344">1 →</text><text x="34" y="344">2 →</text><text x="64" y="344">3</text></g></svg>
  <img class="jc-art" src="${art}" alt="${alt}" loading="lazy"><video class="jc-film f" muted loop playsinline preload="none"></video><video class="jc-film g" muted loop playsinline preload="none"></video><span class="now"></span></div>`;
export const JC_CSS = `.jc{position:relative;aspect-ratio:320/350}.jc-ghost{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
  .jc-art{position:absolute;inset:0;width:100%;height:100%;transition:transform .6s cubic-bezier(.2,.7,.2,1),filter .6s;filter:drop-shadow(0 18px 28px rgba(0,0,0,.55))}
  .jc-film{position:absolute;left:16.25%;top:34%;width:67.5%;height:48%;object-fit:cover;opacity:0;transition:opacity .6s;clip-path:polygon(10.2% 0,89.8% 0,100% 13.7%,100% 86.3%,89.8% 100%,10.2% 100%,0 86.3%,0 13.7%)}
  .jc-film.on{opacity:1}.live .jc-art{filter:brightness(1.1) drop-shadow(0 18px 34px rgba(240,163,90,.18))}`;
