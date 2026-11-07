// The title sequence, in the water: three thin frames draw themselves one behind another (1 → 2 → 3), a translucent jelly lights inside the front one,
// and "jelly-films" writes itself in light. The outro holds the same frames with "return to the reel". No paper, no props.
//   const T = mountTitle(el, {mode: 'intro' | 'outro'});  T.play();  T.seek(seconds);  T.finish();  T.dur
export function mountTitle(el, opt = {}) {
  const mode = opt.mode || 'intro', anims = [], word = 'jelly-films';
  el.classList.add('ttl'); el.innerHTML = `
  <svg class="ttl-svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs>
    <radialGradient id="ttl-w" cx="50%" cy="0%" r="90%"><stop offset="0" stop-color="#0b1a2c"/><stop offset=".6" stop-color="#040a16"/><stop offset="1" stop-color="#01040b"/></radialGradient>
    <radialGradient id="ttl-bell" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="#cfe0ef" stop-opacity=".5"/><stop offset=".7" stop-color="#6d8fb2" stop-opacity=".16"/><stop offset="1" stop-color="#6d8fb2" stop-opacity=".04"/></radialGradient>
    <radialGradient id="ttl-amb" cx="76%" cy="42%" r="60%"><stop offset="0" stop-color="#f2a453" stop-opacity=".85"/><stop offset=".5" stop-color="#f2a453" stop-opacity=".12"/><stop offset="1" stop-color="#f2a453" stop-opacity="0"/></radialGradient></defs>
    <rect width="1600" height="900" fill="url(#ttl-w)"/>
    <g fill="none" stroke="#b7c9d8" stroke-width="1.4">
      <rect class="ttl-f f1" x="610" y="300" width="420" height="440" rx="26" opacity=".3"/><rect class="ttl-f f2" x="680" y="350" width="420" height="440" rx="26" opacity=".5"/><rect class="ttl-f f3" x="750" y="400" width="420" height="440" rx="26" opacity=".85"/>
      <g class="ttl-ticks" opacity=".6"><path d="M960 392v16M960 832v16M742 620h16M1162 620h16M820 292v14M602 520h14"/></g></g>
    <g class="ttl-num" fill="#8aa0b4" font-family="Jost,system-ui,sans-serif" font-style="italic" font-size="26" opacity=".7"><text x="604" y="790">1 →</text><text x="672" y="830">2 →</text><text x="742" y="870">3</text></g>
    <g class="ttl-j" transform="translate(965 610)">
      <g fill="none" stroke="#9fbad3" stroke-width="2.4" stroke-linecap="round" opacity=".7"><path d="M-64 22c-22 60 18 90 -6 160"/><path d="M-22 26c-18 70 26 90 6 176" stroke-dasharray="9 6" stroke-width="5"/><path d="M22 26c18 60 -22 96 0 170"/><path d="M62 22c22 56 -16 86 6 150"/></g>
      <path d="M-120 22C-120 -78 -66 -128 0 -128S120 -78 120 22Q0 44 -120 22Z" fill="url(#ttl-bell)" stroke="#cfe0ef" stroke-opacity=".6" stroke-width="1.5"/>
      <path d="M-120 22C-120 -78 -66 -128 0 -128S120 -78 120 22Q0 44 -120 22Z" fill="url(#ttl-amb)"/>
      <path d="M-118 8Q0 32 118 8V24Q0 48 -118 24Z" fill="#cfe0ef" opacity=".5"/>
      <g fill="#050c18" opacity=".85">${Array.from({length: 19}, (_, i) => `<rect x="${-106 + i * 11.6}" y="${14 + Math.sin(i / 18 * Math.PI) * 9}" width="5.2" height="5" rx="1.2"/>`).join('')}</g></g>
    <text class="ttl-word" x="140" y="${mode === 'outro' ? 210 : 240}" fill="#e6edf3" font-family="Jost,system-ui,sans-serif" font-weight="200" font-size="150" letter-spacing="2">${[...word].map(c => `<tspan>${c}</tspan>`).join('')}</text>
    ${mode === 'outro' ? `<text class="ttl-k" x="146" y="290" fill="#f0a35a" font-family="Jost,system-ui,sans-serif" font-weight="300" font-size="40" letter-spacing="6">return to the reel</text>
      <text class="ttl-url" x="146" y="820" fill="#8293a4" font-family="'JetBrains Mono',monospace" font-weight="300" font-size="24">hartswf0.github.io/contaminant-jelly</text>` : ''}
  </svg>`;
  if (!document.getElementById('ttl-css')) { const st = document.createElement('style'); st.id = 'ttl-css'; st.textContent = `.ttl{position:relative;overflow:hidden;background:#01040b}.ttl-svg{position:absolute;inset:0;width:100%;height:100%}`; document.head.appendChild(st); }
  const q = s => [...el.querySelectorAll(s)], t = x => x * 1000, A = (n, k, o) => { const a = n.animate(k, {fill: 'both', easing: 'cubic-bezier(.3,.6,.2,1)', ...o}); a.pause(); anims.push(a); return a; };
  A(el.querySelector('.ttl-svg'), [{opacity: 0}, {opacity: 1}], {duration: t(1.2)});
  q('.ttl-f').forEach((r, i) => { const L = 2 * (420 + 440); r.style.strokeDasharray = L; A(r, [{strokeDashoffset: L}, {strokeDashoffset: 0}], {delay: t(.6 + i * .7), duration: t(2.2)}); });
  A(el.querySelector('.ttl-ticks'), [{opacity: 0}, {opacity: .6}], {delay: t(2.6), duration: t(1)});
  q('.ttl-num text').forEach((n, i) => A(n, [{opacity: 0}, {opacity: 1}], {delay: t(2.2 + i * .45), duration: t(.9)}));
  const j = el.querySelector('.ttl-j'); A(j, [{opacity: 0, filter: 'blur(8px)'}, {opacity: 1, filter: 'blur(0px)'}], {delay: t(3), duration: t(2.4)});
  q('.ttl-word tspan').forEach((s, i) => A(s, [{opacity: 0}, {opacity: 1}], {delay: t((mode === 'outro' ? 1 : 4.2) + i * .12), duration: t(.8), easing: 'linear'}));
  if (mode === 'outro') { A(el.querySelector('.ttl-k'), [{opacity: 0}, {opacity: 1}], {delay: t(2.6), duration: t(1.2)}); A(el.querySelector('.ttl-url'), [{opacity: 0}, {opacity: .9}], {delay: t(3.4), duration: t(1.2)}); }
  const dur = mode === 'outro' ? 6.5 : 7.6;
  return {dur, anims, play() { anims.forEach(a => a.play()); }, seek(s) { anims.forEach(a => { a.pause(); a.currentTime = s * 1000; }); }, finish() { anims.forEach(a => a.finish()); }};
}
