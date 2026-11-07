// The title sequence: a letterpress label, printed in order: the rule, CONTAMINANT stamped letter by letter, jelly-films typed,
// the jar drawn, the red overprint with its warning, then water rising in the jar around a jelly that lights up.
// One sequence serves two places: the landing page (it stops with the jar full) and the trailer (it floods the screen into the water).
//   const T = mountTitle(el, {mode: 'intro' | 'outro', flood: false, beat: .627});  T.play();  T.seek(seconds);  T.dur
export function mountTitle(el, opt = {}) {
  const mode = opt.mode || 'intro', b = opt.beat || .627, flood = !!opt.flood, anims = [];
  const NAVY = '#1c2a6b', RED = '#cf3a2b', PAPER = '#efe1c6', WATER = '#061113';
  const word = 'CONTAMINANT', sub = 'jelly-films';
  el.classList.add('ttl'); el.innerHTML = `
  <svg class="ttl-defs" width="0" height="0" aria-hidden="true"><defs>
    <filter id="ttl-ink" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" result="d"/>
      <feTurbulence type="fractalNoise" baseFrequency="1.7" numOctaves="1" seed="9" result="s"/><feColorMatrix in="s" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3.2 2.75" result="m"/><feComposite in="d" in2="m" operator="in"/></filter>
    <clipPath id="ttl-jarclip"><path d="M124 92h152c0 24 14 38 34 52 30 22 44 52 44 92v96c0 46-28 70-74 70H120c-46 0-74-24-74-70v-96c0-40 14-70 44-92 20-14 34-28 34-52z"/></clipPath></defs></svg>
  <div class="ttl-paper"></div>
  <div class="ttl-sheet">
    ${mode === 'outro' ? `<div class="ttl-k">RETURN TO THE REEL</div>` : ''}
    <div class="ttl-word" aria-label="${word}">${[...word].map(c => `<span>${c}</span>`).join('')}</div>
    <div class="ttl-sub" aria-label="${sub}">${[...sub].map(c => `<span>${c}</span>`).join('')}</div>
    <div class="ttl-rule"></div>
    <svg class="ttl-jar" viewBox="0 0 400 480" aria-hidden="true">
      <g class="ttl-water" clip-path="url(#ttl-jarclip)"><rect class="ttl-wrect" x="0" y="0" width="400" height="480" fill="${WATER}"/></g>
      <g class="ttl-print red" transform="translate(7 5)">${jar(RED)}</g>
      <g class="ttl-print navy">${jar(NAVY)}</g>
      <g class="ttl-glow"><path d="M150 236a50 50 0 0 1 100 0z" fill="#f2a640"/><g fill="none" stroke="#f2a640" stroke-width="9" stroke-linecap="round"><path d="M172 252c-10 14 10 22 0 38s10 22 0 36"/><path d="M200 252c-10 14 10 22 0 38s10 22 0 36"/><path d="M228 252c-10 14 10 22 0 38s10 22 0 36"/></g></g>
    </svg>
    ${mode === 'outro' ? `<div class="ttl-url">hartswf0.github.io/contaminant-jelly</div>` : `<div class="ttl-warn"><span>WHEN THE JELLY TURNS RED</span><span>KEEP OUT OF THE WATER</span></div>`}
  </div>
  <div class="ttl-flood"></div>`;
  function jar(c) { return `<g fill="none" stroke="${c}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round">
      <rect class="ttl-draw" x="104" y="34" width="192" height="30" rx="12"/><path class="ttl-draw" d="M124 72v20c0 24-14 38-34 52-30 22-44 52-44 92v96c0 46 28 70 74 70h160c46 0 74-24 74-70v-96c0-40-14-70-44-92-20-14-34-28-34-52V72"/>
      <path class="ttl-draw" d="M110 368h180" stroke-width="22"/></g>
    <path class="ttl-bell" d="M150 236a50 50 0 0 1 100 0z" fill="${c}"/>
    <g class="ttl-tent" fill="none" stroke="${c}" stroke-width="9" stroke-linecap="round"><path d="M172 252c-10 14 10 22 0 38s10 22 0 36"/><path d="M200 252c-10 14 10 22 0 38s10 22 0 36"/><path d="M228 252c-10 14 10 22 0 38s10 22 0 36"/></g>`; }
  if (!document.getElementById('ttl-css')) { const st = document.createElement('style'); st.id = 'ttl-css'; st.textContent = `
    .ttl{position:relative;overflow:hidden;background:${PAPER};color:${NAVY};isolation:isolate}
    .ttl-defs{position:absolute}.ttl-paper{position:absolute;inset:0;z-index:-1;background:radial-gradient(ellipse 85% 75% at 50% 45%,transparent 55%,rgba(90,60,20,.28)),url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E%3Cfilter id='p'%3E%3CfeTurbulence baseFrequency='.75' numOctaves='3' seed='4'/%3E%3CfeColorMatrix values='0 0 0 0 .45  0 0 0 0 .33  0 0 0 0 .18  0 0 0 .22 0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23p)'/%3E%3C/svg%3E")}
    .ttl-sheet{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:0;padding:4vh 4vw;filter:url(#ttl-ink)}
    .ttl-word{font:400 clamp(52px,15.5vmin,220px)/.86 Anton,Impact,'Arial Narrow',sans-serif;letter-spacing:.01em;white-space:nowrap}.ttl-word span{display:inline-block}
    .ttl-sub{font:700 clamp(20px,5.4vmin,72px)/1 'Courier Prime','Courier New',monospace;letter-spacing:.02em;margin-top:1.2vmin}.ttl-sub span{display:inline-block}
    .ttl-k{font:400 clamp(26px,5.6vmin,74px)/1 Anton,Impact,sans-serif;letter-spacing:.04em;color:${RED};margin-bottom:2.4vmin}
    .ttl-rule{width:min(62vmin,640px);height:clamp(7px,1.3vmin,16px);background:${NAVY};margin:2.6vmin 0 1.4vmin;transform-origin:left}
    .ttl-jar{width:min(33vmin,400px);height:auto;overflow:visible}.ttl-print.red{mix-blend-mode:multiply}.ttl-bell,.ttl-tent,.ttl-glow{transform-box:fill-box;transform-origin:50% 0}
    .ttl-warn{display:grid;justify-items:center;font:400 clamp(17px,4.6vmin,56px)/1.04 Anton,Impact,sans-serif;letter-spacing:.03em;color:${NAVY};margin-top:1.6vmin}.ttl-warn span:last-child{color:${RED}}
    .ttl-url{font:700 clamp(14px,2.4vmin,26px) 'Courier Prime',monospace;margin-top:2vmin}
    .ttl-flood{position:absolute;left:50%;top:62%;width:10px;height:10px;margin:-5px;border-radius:50%;background:${WATER};transform:scale(0);pointer-events:none}
    @media (max-aspect-ratio:3/4){.ttl-word{font-size:15.5vw}.ttl-jar{width:46vw}}`; document.head.appendChild(st); }
  const q = s => [...el.querySelectorAll(s)], A = (n, k, o) => { const a = n.animate(k, {fill: 'both', easing: 'cubic-bezier(.2,.7,.2,1)', ...o}); a.pause(); anims.push(a); return a; };
  const t = x => x * 1000;
  // 0 paper from black; the rule; the word stamped; the sub typed (all on the beat)
  A(el.querySelector('.ttl-sheet'), [{opacity: 0}, {opacity: 1}], {duration: t(.35)});
  A(el.querySelector('.ttl-paper'), [{opacity: 0}, {opacity: 1}], {duration: t(.5)});
  if (mode === 'outro') A(el.querySelector('.ttl-k'), [{opacity: 0, transform: 'scale(1.5) rotate(-3deg)'}, {opacity: 1, transform: 'none'}], {delay: t(b * .5), duration: t(.24), easing: 'cubic-bezier(.3,1.6,.5,1)'});
  q('.ttl-word span').forEach((s, i) => A(s, [{opacity: 0, transform: `scale(1.7) translateY(-6%) rotate(${(i % 2 ? 1 : -1) * 4}deg)`}, {opacity: 1, transform: 'none'}], {delay: t(b + i * b * .25), duration: t(.2), easing: 'cubic-bezier(.3,1.5,.5,1)'}));
  q('.ttl-sub span').forEach((s, i) => A(s, [{opacity: 0}, {opacity: 1}], {delay: t(b * 4 + i * b * .1), duration: 40, easing: 'linear'}));
  A(el.querySelector('.ttl-rule'), [{transform: 'scaleX(0)'}, {transform: 'scaleX(1)'}], {delay: t(b * 5), duration: t(b), easing: 'cubic-bezier(.7,0,.2,1)'});
  // the jar draws itself, the jelly pops into it
  q('.ttl-print.navy .ttl-draw').forEach((p, i) => { const L = p.getTotalLength ? p.getTotalLength() : 1200; p.style.strokeDasharray = L; A(p, [{strokeDashoffset: L}, {strokeDashoffset: 0}], {delay: t(b * 5.5 + i * b * .5), duration: t(b * 1.6), easing: 'cubic-bezier(.6,0,.3,1)'}); });
  q('.ttl-print.navy .ttl-bell').forEach(p => A(p, [{transform: 'scale(0)'}, {transform: 'scale(1)'}], {delay: t(b * 7.5), duration: t(.3), easing: 'cubic-bezier(.3,1.7,.5,1)'}));
  q('.ttl-tent').forEach(p => { A(p, [{opacity: 0}, {opacity: 1}], {delay: t(b * 7.8), duration: t(.2)}); A(p, [{transform: 'skewX(-5deg) scaleY(.96)'}, {transform: 'skewX(5deg) scaleY(1.04)'}], {delay: 0, duration: t(b * 2), direction: 'alternate', iterations: Infinity, easing: 'ease-in-out', fill: 'none'}); });
  // the red overprint: a misregistered second pass, flickering on; the warning
  const red = el.querySelector('.ttl-print.red'); red.querySelectorAll('.ttl-draw').forEach(p => { p.style.strokeDasharray = 'none'; });
  A(red, [{opacity: 0}, {opacity: 0, offset: .2}, {opacity: .9, offset: .3}, {opacity: .1, offset: .45}, {opacity: .85, offset: .6}, {opacity: .35, offset: .8}, {opacity: .8}], {delay: t(b * 8.4), duration: t(b * 2)});
  if (mode !== 'outro') q('.ttl-warn span').forEach((s, i) => A(s, [{opacity: 0, transform: 'scale(1.35)'}, {opacity: 1, transform: 'none'}], {delay: t(b * (8.6 + i)), duration: t(.18), easing: 'cubic-bezier(.3,1.6,.5,1)'}));
  else A(el.querySelector('.ttl-url'), [{opacity: 0}, {opacity: 1}], {delay: t(b * 9), duration: t(.6)});
  // water rises in the jar; the jelly lights amber in it
  A(el.querySelector('.ttl-wrect'), [{transform: 'translateY(100%)'}, {transform: 'translateY(16%)'}], {delay: t(b * 9.6), duration: t(b * 2.6), easing: 'cubic-bezier(.4,0,.2,1)'});
  A(el.querySelector('.ttl-glow'), [{opacity: 0, filter: 'blur(0)'}, {opacity: 1, filter: 'blur(1px)'}], {delay: t(b * 10.6), duration: t(b * 1.4)});
  A(el.querySelector('.ttl-glow'), [{transform: 'translateY(0)'}, {transform: 'translateY(-3%)'}], {delay: 0, duration: t(b * 2), direction: 'alternate', iterations: Infinity, easing: 'ease-in-out', fill: 'none'});
  let dur = b * 12.4;
  if (flood) { const f = el.querySelector('.ttl-flood'); A(f, [{transform: 'scale(0)'}, {transform: 'scale(320)'}], {delay: t(b * 12), duration: t(b * 1.6), easing: 'cubic-bezier(.7,0,.3,1)'}); dur = b * 13.6; }
  return {dur, anims, play() { anims.forEach(a => a.play()); }, seek(s) { anims.forEach(a => { a.pause(); a.currentTime = s * 1000; }); }, finish() { anims.forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.finish(); else a.play(); }); }};
}
