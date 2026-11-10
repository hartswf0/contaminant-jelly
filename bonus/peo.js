// PEO SCORE v0: Prompt · Ekphrasis · Operation, written as text, compiled to JSON, played by the Lab.
// After PAELEO's own definition: "how descriptions become consequential actions … the consequence changes the
// situation from which the next prompt is made." Spec: bonus/SCION_PEO.md.
//
//   parse(text)      -> {score, errors}     score is the JSON form (schema SCHEMA); errors carry line numbers
//   serialize(score) -> text                 canonical text; parse(serialize(s)) means the same as s
//   toSeconds(time, bpm, offset)             'b196' | '12.5s' | '12.5' | '1:02.5'  -> seconds
//   evalTest(test, world)                    runs one @test against a world adapter (the Lab supplies it)
// No DOM, no THREE: it runs in the browser and in node.

export const VERSION = 'peo/0';
export const DIRECTIVES = ['prompt', 'world', 'cast', 'light', 'camera', 'steer', 'ekphrasis', 'op', 'test', 'source'];
export const VERBS = {
  pulse: 'pulse <name> [k=1]: fire the jelly\'s leading pacemaker (the nerve may refuse, as a real one does)',
  swim: 'swim <name> to=x,y,z | to=<name>: the jelly swims there on its own strokes',
  steer: 'steer <name> [scheme=…] [thrust=…] [turn=…] [drag=…]: hand control (or the autopilot) to that jelly',
  view: 'view <name> <flesh|nerves|muscle|strain>',
  film: 'film <name> src=<url> [from=<sec>]: play a film in that jelly\'s bell',
  clear: 'clear <name>: take the film out of its bell',
  camera: 'camera <mode> [speed=] [ease=] [dist=] [fov=] [follow=<name>]',
  light: 'light <path|preset> [n=] [ratio=] [detune=] …',
  say: 'say "<caption>": a caption in the lower third',
  mode: 'mode <inspect|open|steer|orchestra|score>',
  set: 'set <name>.<control>=<value>: any of a jelly\'s own live controls (cold·warm, still·swims …)',
  current: 'current x,y,z: the water\'s drift',
  haze: 'haze <density>',
  // film memories (bonus/memory.js): a clip held by a jelly, condensed as flecks, bloomed whole, kept, released into a target
  memory: 'memory <id> holder=<name> src=<mp4>|still=<image> [from=<clip s>] source=<@source id> [gain=] [label=]: the clip\'s time is from + (clock − this line\'s time)',
  condense: 'condense <id> [from=<name|x,y,z>]: flecks travel in and gather under the holder (a range)',
  bloom: 'bloom <id> stage=<pull-in|catch|surface|swallow|hand-off> [size=0.5 of frame height] [at=center|left|right] [to=<name> for hand-off] [side=left|right for catch]: the whole picture, above the caption band (a range)',
  keep: 'keep <id> beside=<name|memory> [size=0.22] [dx=] [dy=]: a small picture beside something (a range)',
  release: 'release <id> to=<name|memory|x,y,z> [uv=u,v inside a memory] [arc=1.4]: the picture breaks into flecks that stream into the target (a range)',
  stream: 'stream: the same as release',
};
export const TESTS = {
  moved: 'moved <name> > <metres>: distance travelled since the score began (or since from=<time>)',
  dir: 'dir <name> <+x|-x|+y|-y|+z|-z> [> <metres>]: net displacement along an axis since the last test of that jelly',
  near: 'near <name> <name|x,y,z> < <metres>',
  beats: 'beats <name> >= <n>: beats since the score began',
  rate: 'rate <name> > <beats per minute>',
  visible: 'visible <name>: on screen and not behind the camera',
  fired: 'fired <name> >= <fraction>: share of entrained onsets the nerve accepted',
  fps: 'fps > <n>',
  ui: 'ui hidden | ui shown: cinema check',
  // cold reads on the rendered frame (a clean plate is rendered without the thing, and the difference is measured)
  bloomh: 'bloomh <memory> >= <fraction>: the picture\'s height as a share of frame height',
  bloomb: 'bloomb <memory> >= <fraction>: the picture\'s bottom edge, as a share of frame height from the bottom (above the caption band: >= 0.2)',
  legible: 'legible <memory> >= <contrast>: RMS luminance contrast inside the picture as shown',
  gone: 'gone <memory>: the picture covers less than 0.5% of the frame',
  flecks: 'flecks <memory> in <name|memory> >= <share>: share of the memory\'s fleck pixels inside the target\'s box',
  inbox: 'inbox <name> x0,y0,x1,y1 >= <share>: share of the jelly\'s pixels inside a box (frame fractions, y down)',
  streamed: 'streamed <memory> >= <seconds>: over a range, the time its flecks were on screen in transit',
};
export const MEMORY_TESTS = ['bloomh', 'bloomb', 'legible', 'gone', 'flecks', 'streamed'];
const MEMORY_VERBS = ['condense', 'bloom', 'keep', 'release', 'stream'];
export const RIGHTS = /\b(CC0|public[ _-]?domain|US[ -]?gov(ernment)?|own work|producer'?s own)/i;
export const SCHEMA = {
  $id: 'peo/0', type: 'object', required: ['version'],
  properties: {
    version: {const: VERSION}, prompt: {type: 'string'},
    world: {type: 'object', description: 'key=value: mode, haze, song, bpm, offset, onsets, current, water, duration'},
    cast: {type: 'array', items: {type: 'object', required: ['name', 'jelly'], description: 'name, jelly id, role, at [x,y,z], view, and any jelly control'}},
    light: {type: 'object', description: 'path or preset, n, ratio, detune, base, radius, dR, dTheta, k, height, lock, on, notes'},
    camera: {type: 'object', description: 'mode, speed, ease, dist, fov, follow, cut, auto, hold'},
    steer: {type: 'object', description: 'who (you|auto|<name>), scheme, thrust, turn, drag, grav, reach, arms, target'},
    ekphrasis: {type: 'array', items: {type: 'object', required: ['t', 'text']}},
    ops: {type: 'array', items: {type: 'object', required: ['t', 'verb']}},
    tests: {type: 'array', items: {type: 'object', required: ['t', 'kind']}},
    sources: {type: 'array', items: {type: 'object', required: ['id']}},
  },
};

// ---------------------------------------------------------------- tokens
// a line is: @directive head… key=value key="quoted value" key=x,y,z
function tokenize(s, ln, errors) {
  const out = []; let i = 0;
  while (i < s.length) {
    if (/\s/.test(s[i])) { i++; continue; }
    if (s[i] === '#') break;
    let j = i, tok = '';
    while (j < s.length && !/\s/.test(s[j])) {
      if (s[j] === '"') { const k = s.indexOf('"', j + 1); if (k < 0) { errors.push({line: ln, msg: 'unclosed quote'}); tok += s.slice(j + 1); j = s.length; break; } tok += s.slice(j + 1, k); j = k + 1; }
      else tok += s[j++];
    }
    out.push({raw: s.slice(i, j), v: tok}); i = j;
  }
  return out;
}
const NUM = /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i;
function value(v) {
  if (NUM.test(v)) return +v;
  if (/^(on|true|yes)$/i.test(v)) return true;
  if (/^(off|false|no)$/i.test(v)) return false;
  if (/^[-+.\d]+(,[-+.\d]+){1,3}$/.test(v)) return v.split(',').map(Number);
  return v;
}
// times: b196 · b196.5 · 12.5s · 12.5 · 1:02.5 ; ranges a..b
const TIME = /^(b[-+]?\d*\.?\d+|\d+:\d+(\.\d+)?|[-+]?\d*\.?\d+s?)$/;
function time(v, ln, errors) {
  if (!TIME.test(v)) { errors.push({line: ln, msg: `"${v}" is not a time (use b196, 12.5s or 1:02.5)`}); return null; }
  return v;
}
export function toSeconds(t, bpm = 120, offset = 0) {
  if (t == null) return 0; if (typeof t === 'number') return t; t = String(t);
  if (t[0] === 'b') return offset + parseFloat(t.slice(1)) * 60 / bpm;
  if (t.includes(':')) { const [m, s] = t.split(':'); return +m * 60 + parseFloat(s); }
  return parseFloat(t);
}
function kv(tokens) { const o = {}, rest = []; for (const tk of tokens) { const m = /^([A-Za-z][\w.-]*)=(.*)$/s.exec(tk.raw); if (m) { const q = tk.raw.indexOf('"') === m[1].length + 1; o[m[1]] = q ? tk.v.slice(m[1].length + 1) : value(m[2]); } else rest.push(tk.v); } return {o, rest}; }

// ---------------------------------------------------------------- parse
export function parse(text) {
  const errors = [], score = {version: VERSION, prompt: '', world: {}, cast: [], light: {}, camera: {}, steer: {}, ekphrasis: [], ops: [], tests: [], sources: []};
  const prompts = [];
  String(text).split(/\r?\n/).forEach((line, idx) => {
    const ln = idx + 1, s = line.trim(); if (!s || s[0] === '#') return;
    const m = /^@([a-z]+)\b(.*)$/i.exec(s);
    if (!m) { errors.push({line: ln, msg: 'a line must start with @' + DIRECTIVES.join(' @')}); return; }
    const dir = m[1].toLowerCase(), body = m[2];
    if (!DIRECTIVES.includes(dir)) { errors.push({line: ln, msg: `unknown directive @${dir} (known: ${DIRECTIVES.join(', ')})`}); return; }
    const toks = tokenize(body, ln, errors), {o, rest} = kv(toks);
    if (dir === 'prompt') { prompts.push(toks.map(t => t.v).join(' ')); return; }
    if (dir === 'world') { Object.assign(score.world, o); if (rest.length) score.world.water = rest.join(' '); return; }
    if (dir === 'light') { if (rest[0]) o.path = rest[0]; Object.assign(score.light, o); return; }
    if (dir === 'camera') { if (rest[0]) o.mode = rest[0]; Object.assign(score.camera, o); return; }
    if (dir === 'steer') { if (rest[0]) o.who = rest[0]; Object.assign(score.steer, o); return; }
    if (dir === 'cast') {
      const head = rest[0]; if (!head) { errors.push({line: ln, msg: '@cast needs name:jelly (e.g. medusa:medusa)'}); return; }
      const [name, jelly] = head.includes(':') ? head.split(':') : [head, head];
      if (!/^[a-z][\w-]*$/i.test(name)) { errors.push({line: ln, msg: `"${name}" is not a usable name`}); return; }
      if (score.cast.some(c => c.name === name)) { errors.push({line: ln, msg: `"${name}" is cast twice`}); return; }
      score.cast.push({name, jelly, ...o, line: ln}); return; }
    if (dir === 'source') { const id = rest[0]; if (!id) { errors.push({line: ln, msg: '@source needs an id'}); return; } score.sources.push({id, ...o, line: ln}); return; }
    // the timed three: ekphrasis, op, test
    const t0 = rest.shift(); if (t0 == null) { errors.push({line: ln, msg: `@${dir} needs a time first (b196, 12.5s, 1:02.5 or a..b)`}); return; }
    let t = t0, until = null; if (t0.includes('..')) [t, until] = t0.split('..');
    if (time(t, ln, errors) == null || (until != null && time(until, ln, errors) == null)) return;
    if (dir === 'ekphrasis') { const after = body.trim().slice(t0.length).trim(), qm = /^"(.*)"\s*(#.*)?$/s.exec(after), text = (qm ? qm[1] : after.replace(/\s+#.*$/, '')).trim(); if (!text) { errors.push({line: ln, msg: '@ekphrasis needs what a viewer should see or hear'}); return; } score.ekphrasis.push({t, ...(until ? {until} : {}), text, line: ln}); return; }
    if (dir === 'op') { const verb = rest.shift(); if (!verb) { errors.push({line: ln, msg: '@op needs a verb'}); return; } if (!(verb in VERBS)) { errors.push({line: ln, msg: `unknown verb "${verb}" (known: ${Object.keys(VERBS).join(', ')})`}); return; }
      score.ops.push({t, ...(until ? {until} : {}), verb, args: rest, ...o, line: ln}); return; }
    if (dir === 'test') { const kind = rest.shift(); if (!kind) { errors.push({line: ln, msg: '@test needs a kind'}); return; } if (!(kind in TESTS)) { errors.push({line: ln, msg: `unknown test "${kind}" (known: ${Object.keys(TESTS).join(', ')})`}); return; }
      const cmp = rest.findIndex(x => /^(<|>|<=|>=|=|==)$/.test(x)), args = cmp < 0 ? rest : rest.slice(0, cmp), op = cmp < 0 ? null : rest[cmp], rhs = cmp < 0 ? null : value(rest[cmp + 1] ?? '');
      if (op && typeof rhs !== 'number' && !['ui'].includes(kind)) { errors.push({line: ln, msg: `@test ${kind} ${op} needs a number after it`}); return; }
      score.tests.push({t, ...(until ? {until} : {}), kind, args, ...(op ? {op, rhs} : {}), ...o, line: ln}); return; }
  });
  score.prompt = prompts.join('\n');
  // cross-checks: every name used by an op or test must be cast
  const names = new Set(score.cast.map(c => c.name)); const needs = (x, ln) => { if (x && /^[a-z][\w-]*$/i.test(x) && !names.has(x) && !/^[-+.\d,]+$/.test(x)) errors.push({line: ln, msg: `"${x}" is not cast (add @cast ${x}:<jelly>)`}); };
  for (const o of score.ops) if (['pulse', 'swim', 'steer', 'view', 'film', 'clear'].includes(o.verb)) { needs(o.args[0], o.line); if (typeof o.to === 'string') needs(o.to, o.line); }
  for (const o of score.ops) if (o.verb === 'set') { const k = Object.keys(o).find(k => k.includes('.')); if (!k) errors.push({line: o.line, msg: 'set needs <name>.<control>=<value>'}); else needs(k.split('.')[0], o.line); }
  // memories: each needs a holder that is cast and a @source with a rights basis (CC0, public domain / US-government work, or the producer's own)
  const mems = new Map(), srcs = new Map(score.sources.map(x => [x.id, x]));
  for (const o of score.ops) if (o.verb === 'memory') { const id = o.args[0]; if (!id) { errors.push({line: o.line, msg: 'memory needs an id'}); continue; } if (mems.has(id)) errors.push({line: o.line, msg: `memory "${id}" is defined twice`}); mems.set(id, o);
    if (!o.holder) errors.push({line: o.line, msg: `memory ${id} needs holder=<name>`}); else needs(o.holder, o.line);
    if (!o.src && !o.still) errors.push({line: o.line, msg: `memory ${id} needs src=<mp4> or still=<image>`});
    const S = srcs.get(o.source); if (!o.source) errors.push({line: o.line, msg: `memory ${id} needs source=<id> pointing at an @source line with its rights basis`});
    else if (!S) errors.push({line: o.line, msg: `memory ${id}: no @source ${o.source}`}); else if (!RIGHTS.test(String(S.basis || '') + ' ' + String(S.rights || ''))) errors.push({line: S.line, msg: `@source ${S.id}: basis must be CC0, public domain / US-government work, or the producer's own work (got "${S.basis || ''}")`}); }
  const isMem = x => mems.has(x), needsMem = (x, ln) => { if (!isMem(x)) errors.push({line: ln, msg: `"${x}" is not a memory (add @op <time> memory ${x} holder=… src=… source=…)`}); };
  for (const o of score.ops) if (MEMORY_VERBS.includes(o.verb)) { needsMem(o.args[0], o.line); if (!o.until) errors.push({line: o.line, msg: `${o.verb} needs a time range (a..b)`});
    if (o.verb === 'bloom' && o.stage && !['pull-in', 'catch', 'surface', 'swallow', 'hand-off'].includes(o.stage)) errors.push({line: o.line, msg: `unknown stage "${o.stage}" (pull-in, catch, surface, swallow, hand-off)`});
    for (const k of ['to', 'beside']) if (typeof o[k] === 'string' && !o[k].includes(',') && !isMem(o[k])) needs(o[k], o.line); }
  for (const t of score.tests) { if (['fps', 'ui'].includes(t.kind)) continue; if (MEMORY_TESTS.includes(t.kind)) { needsMem(t.args[0], t.line); if (t.kind === 'flecks') { if (t.args[1] !== 'in' || !t.args[2]) errors.push({line: t.line, msg: 'flecks <memory> in <target> >= <share>'}); else if (!isMem(t.args[2])) needs(t.args[2], t.line); } if (t.kind === 'streamed' && !t.until) errors.push({line: t.line, msg: 'streamed needs a time range (a..b)'}); continue; }
    needs(t.args[0], t.line); }
  if (score.steer.who && !['you', 'auto'].includes(score.steer.who)) needs(score.steer.who, 0);
  if (score.camera.follow) needs(score.camera.follow, 0);
  return {score, errors};
}

// ---------------------------------------------------------------- serialize (canonical text)
const q = v => typeof v === 'string' && (/[\s"#=]/.test(v) || v === '') ? `"${v.replace(/"/g, "'")}"` : v;
const fmt = v => Array.isArray(v) ? v.map(n => +(+n).toFixed(4)).join(',') : typeof v === 'boolean' ? (v ? 'on' : 'off') : typeof v === 'number' ? +v.toFixed(6) : q(v);
const pairs = (o, skip = []) => Object.entries(o).filter(([k, v]) => !skip.includes(k) && k !== 'line' && v != null).map(([k, v]) => `${k}=${fmt(v)}`).join(' ');
const when = x => x.t + (x.until ? '..' + x.until : '');
export function serialize(s) {
  const L = [`# PEO score · ${VERSION} · Prompt · Ekphrasis · Operation`];
  for (const p of String(s.prompt || '').split('\n').filter(Boolean)) L.push(`@prompt ${p}`);
  if (Object.keys(s.world || {}).length) { const w = {...s.world}, water = w.water; delete w.water; L.push(`@world${water ? ' ' + q(water) : ''} ${pairs(w)}`.trimEnd()); }
  for (const c of s.cast || []) L.push(`@cast ${c.name}:${c.jelly} ${pairs(c, ['name', 'jelly'])}`.trimEnd());
  if (Object.keys(s.light || {}).length) L.push(`@light ${s.light.path ? q(s.light.path) + ' ' : ''}${pairs(s.light, ['path'])}`.trimEnd());
  if (Object.keys(s.camera || {}).length) L.push(`@camera ${s.camera.mode ? s.camera.mode + ' ' : ''}${pairs(s.camera, ['mode'])}`.trimEnd());
  if (Object.keys(s.steer || {}).length) L.push(`@steer ${s.steer.who ? s.steer.who + ' ' : ''}${pairs(s.steer, ['who'])}`.trimEnd());
  for (const x of s.sources || []) L.push(`@source ${x.id} ${pairs(x, ['id'])}`.trimEnd());
  const timed = [...(s.ekphrasis || []).map(e => ['e', e]), ...(s.ops || []).map(o => ['o', o]), ...(s.tests || []).map(t => ['t', t])];
  const bpm = +(s.world?.bpm || 120), off = +(s.world?.offset || 0); timed.sort((a, b) => toSeconds(a[1].t, bpm, off) - toSeconds(b[1].t, bpm, off) || 'eot'.indexOf(a[0]) - 'eot'.indexOf(b[0]));
  for (const [k, x] of timed) {
    if (k === 'e') L.push(`@ekphrasis ${when(x)} "${String(x.text).replace(/"/g, "'")}"`);
    else if (k === 'o') L.push(`@op ${when(x)} ${x.verb} ${(x.args || []).map(q).join(' ')} ${pairs(x, ['t', 'until', 'verb', 'args'])}`.replace(/\s+$/, '').replace(/ {2,}/g, ' '));
    else L.push(`@test ${when(x)} ${x.kind} ${(x.args || []).map(q).join(' ')}${x.op ? ` ${x.op} ${fmt(x.rhs)}` : ''} ${pairs(x, ['t', 'until', 'kind', 'args', 'op', 'rhs'])}`.replace(/\s+$/, '').replace(/ {2,}/g, ' '));
  }
  return L.join('\n') + '\n';
}
// meaning-equality for the round-trip check: same score once line numbers are dropped and timed entries are ordered
export function same(a, b) { const strip = s => JSON.stringify(s, (k, v) => k === 'line' ? undefined : v); const norm = s => { const c = JSON.parse(strip(s)); for (const k of ['ekphrasis', 'ops', 'tests']) c[k] = (c[k] || []).map(x => JSON.stringify(x)).sort(); return JSON.stringify(c); }; return norm(a) === norm(b); }

// ---------------------------------------------------------------- tests, against a world adapter
// W: {pos(name)->[x,y,z]|null, start(name)->[x,y,z], mark(name,key)->[x,y,z] (get+set), beats(name), rate(name), visible(name), fired(name), fps(), ui()}
const cmpf = (op, a, b) => op === '<' ? a < b : op === '<=' ? a <= b : op === '>' ? a > b : op === '>=' ? a >= b : Math.abs(a - b) < 1e-6;
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
export function evalTest(t, W) {
  const n = t.args[0], op = t.op || '>', rhs = typeof t.rhs === 'number' ? t.rhs : 0; let got = null, pass = false, note = '';
  try {
    if (t.kind === 'moved') { const p = W.pos(n), s = t.from != null ? W.mark(n, 'from:' + t.from) : W.start(n); got = dist(p, s); pass = cmpf(op, got, rhs); }
    else if (t.kind === 'dir') { const ax = t.args[1] || '+x', i = 'xyz'.indexOf(ax[1]), sg = ax[0] === '-' ? -1 : 1, p = W.pos(n), m = W.mark(n, 'dir'); got = (p[i] - m[i]) * sg; pass = cmpf(t.op || '>', got, t.op ? rhs : 0); note = `along ${ax}`; }
    else if (t.kind === 'near') { const o = t.args[1], q2 = /[,]/.test(o) ? o.split(',').map(Number) : W.pos(o); got = dist(W.pos(n), q2); pass = cmpf(t.op || '<', got, t.op ? rhs : 2); }
    else if (t.kind === 'beats') { got = W.beats(n); pass = cmpf(t.op || '>=', got, t.op ? rhs : 1); }
    else if (t.kind === 'rate') { got = W.rate(n); pass = cmpf(op, got, rhs); }
    else if (t.kind === 'visible') { got = W.visible(n) ? 1 : 0; pass = !!got; }
    else if (t.kind === 'fired') { got = W.fired(n); pass = cmpf(t.op || '>=', got, t.op ? rhs : .5); }
    else if (t.kind === 'fps') { got = W.fps(); pass = cmpf(op, got, rhs); }
    else if (t.kind === 'ui') { got = W.ui(); pass = (t.args[0] || 'hidden') === got; }
    else if (t.kind === 'bloomh') { got = W.frame('bloomh', t.args); pass = cmpf(t.op || '>=', got, t.op ? rhs : .45); }
    else if (t.kind === 'bloomb') { got = W.frame('bloomb', t.args); pass = cmpf(t.op || '>=', got, t.op ? rhs : .2); }
    else if (t.kind === 'legible') { got = W.frame('legible', t.args); pass = cmpf(t.op || '>=', got, t.op ? rhs : .12); }
    else if (t.kind === 'gone') { got = W.frame('coverage', t.args); pass = got < (t.op ? rhs : .005); }
    else if (t.kind === 'flecks') { got = W.frame('flecks', t.args); pass = cmpf(t.op || '>=', got, t.op ? rhs : .5); }
    else if (t.kind === 'inbox') { got = W.frame('inbox', t.args); pass = cmpf(t.op || '>=', got, t.op ? rhs : .8); }
    else if (t.kind === 'streamed') { got = W.streamed(t); pass = cmpf(t.op || '>=', got, t.op ? rhs : 1.5); }
    if (got === null && !note) { pass = null; note = 'not measurable here'; }
  } catch (e) { note = String(e.message || e); }
  return {line: t.line, t: t.t, kind: t.kind, args: t.args, op: t.op, rhs: t.rhs, got: typeof got === 'number' ? +got.toFixed(3) : got, pass, note};
}
