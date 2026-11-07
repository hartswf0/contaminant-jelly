// DRIFTS: one playable translation per video we have. Each entry says what the game took from its video.
// Shared engine: drift/index.html. Open water with depth layers, never a tube; no buttons; films only as clouds of flecks.
// dir: the way the current carries you (right, up, down). band: half-height of the open water you can swim in.
// layers: silhouette strips {kind, side (-1 below/left, 1 above/right), z (depth; negative is behind the play plane), glow (0..1 bulbs)}.
// every drift and archive level has its jar (labels/jars/*.svg): the mascot jelly on the label; on the index the level's video plays in it
const JARS = ['ascent', 'pairs', 'lure', 'surface', 'halo', 'rayrun', 'slices', 'caves', 'bloom', 'descent', 'silt', 'doodles', 'menagerie', 'bolas', 'strata', 'spectrum'];
export const LEVELS = [
  {id: 'ascent', title: 'Ascent', source: 'design_v2', video: '../fal/design_v2_720.mp4', song: 'nightbus-08', start: 8.27,
    dir: 'up', len: 230, current: 1.6, band: 9, fog: '#2a241c', top: '#5a4c38', fogD: .03, films: {layout: 'tiers', every: 7}, bad: .04,
    layers: [{kind: 'kelp', side: -1, z: -26, glow: .2}, {kind: 'kelp', side: 1, z: -26, glow: .2}, {kind: 'ruin', side: -1, z: -9, glow: .5}, {kind: 'ruin', side: 1, z: -9, glow: .5}, {kind: 'reef', side: -1, z: 5, glow: .1}],
    creatures: ['comb'], surface: true, goal: {type: 'wake', n: 14, label: 'wake films as you rise'},
    took: 'A vertical tomography of film: tier after tier of small playing frames around a rising jelly. Here the tiers become galleries of sleeping films in three depths; brushing one wakes it, tapping it takes a frame.'},
  {id: 'pairs', title: 'Pairs', source: 'design_v4', video: '../fal/design_v4_720.mp4', song: 'siltwire-02', start: 130.8,
    dir: 'right', len: 260, current: 2, band: 8, fog: '#1b2827', fogD: .032, films: {layout: 'pairs', every: 16}, bad: .2,
    layers: [{kind: 'pipes', side: 1, z: -14, glow: 0}, {kind: 'pipes', side: -1, z: -14, glow: 0}, {kind: 'reef', side: -1, z: -5, glow: .3}, {kind: 'cave', side: 1, z: 4, glow: 0}],
    creatures: ['school'], goal: {type: 'pairs', n: 4, label: 'take a frame from both films of a pair'},
    took: 'Soft oval films that arrive in pairs (a face and a hand), drifting through a drowned sewer, with red corruption spreading. Here every pair is a possible cut: take a frame from both and they join.'},
  {id: 'lure', title: 'Lure', source: 'design_v5', video: '../fal/design_v5_720.mp4', song: 'event-03', start: 83.17,
    dir: 'right', len: 280, current: 2.2, band: 10, fog: '#16201f', fogD: .034, films: {layout: 'scatter', every: 10}, bad: .1,
    layers: [{kind: 'ruin', side: -1, z: -30, glow: .4}, {kind: 'cave', side: 1, z: -12, glow: .2}, {kind: 'reef', side: -1, z: -6, glow: .7}, {kind: 'reef', side: -1, z: 5, glow: .2}],
    creatures: ['school', 'angler', 'comb'], goal: {type: 'frames', n: 8, label: 'bank frames without being bitten'},
    took: 'A fork around a pillar, an anglerfish in the right passage with a lure, a school of flecks, a cyan jelly in the distance. Here the angler patrols the lower water and warns with two pulses before it lunges.'},
  {id: 'surface', title: 'Toward the Surface', source: 'design_v6', video: '../fal/design_v6_720.mp4', song: 'siltwire-10', start: .28,
    dir: 'up', len: 200, current: 1.4, band: 10, fog: '#1d2c2c', top: '#4f8580', fogD: .026, films: {layout: 'giant', every: 14}, bad: 0,
    layers: [{kind: 'kelp', side: -1, z: -20, glow: .3}, {kind: 'reef', side: 1, z: -8, glow: .6}, {kind: 'kelp', side: 1, z: 5, glow: 0}],
    creatures: ['comb', 'school'], surface: true, goal: {type: 'watch', n: 2, label: 'hold on a film to watch it (4 s each)'},
    took: 'A huge face and a raised hand gathering beside a tiny jelly, comb jellies, water paling to a rippling surface. Here the first film is enormous and the point is to stop and watch.'},
  {id: 'halo', title: 'Halo', source: 'song_neonbutterfly-02', video: '../fal/song_neonbutterfly-02.mp4', song: 'neonbutterfly-02', start: null,
    dir: 'up', len: 170, current: 1.6, band: 9, fog: '#16252a', top: '#4b8590', fogD: .028, films: {layout: 'halo', every: 18}, bad: 0,
    layers: [{kind: 'kelp', side: -1, z: -16, glow: .2}, {kind: 'kelp', side: 1, z: -16, glow: .2}],
    creatures: ['school'], surface: true, goal: {type: 'halo', n: 5, label: 'take frames from the halo under the surface'},
    took: 'A jelly rises toward a bright surface where films orbit as a ring. Here the halo turns under the surface and you take frames from it as it comes round.'},
  {id: 'rayrun', title: 'Ray Run', source: 'song_nightbus-03', video: '../fal/song_nightbus-03.mp4', song: 'nightbus-03', start: null,
    dir: 'right', len: 340, current: 4.5, band: 9, fog: '#1a2421', fogD: .03, films: {layout: 'stream', every: 7}, bad: .06,
    layers: [{kind: 'dunes', side: -1, z: -20, glow: 0}, {kind: 'reef', side: -1, z: -6, glow: .4}, {kind: 'dunes', side: -1, z: 4, glow: 0}],
    creatures: ['ray', 'school', 'shrimp'], goal: {type: 'frames', n: 10, label: 'ride the ray’s wake and take frames at speed'},
    took: 'A great ray sweeps overhead and its wake pulls everything forward. Here you ride under it for a slipstream while films stream past.'},
  {id: 'slices', title: 'Slices', source: 'song_nightbus-06', video: '../fal/song_nightbus-06.mp4', song: 'nightbus-06', start: null,
    dir: 'right', len: 260, current: 2, band: 9, fog: '#141b1d', fogD: .03, films: {layout: 'chain', every: 0}, bad: .25,
    layers: [{kind: 'cave', side: 1, z: -10, glow: .2}, {kind: 'dunes', side: -1, z: -10, glow: 0}],
    creatures: [], goal: {type: 'order', n: 8, label: 'take the slices of one film in order'},
    took: 'A diagonal chain of film slices hangs in the dark beside a field of red fragments. Here the chain is one film laid out in time; follow it and take its slices in order.'},
  {id: 'caves', title: 'Twin Caves', source: 'song_nightbus-08', video: '../fal/song_nightbus-08.mp4', song: 'nightbus-08', start: null,
    dir: 'right', len: 260, current: 2, band: 10, fog: '#162424', fogD: .03, films: {layout: 'caves', every: 11}, bad: .05,
    layers: [{kind: 'cave', side: 1, z: -3, glow: .3}, {kind: 'mussels', side: -1, z: -3, glow: .1}, {kind: 'cave', side: 1, z: -18, glow: .1}, {kind: 'mussels', side: -1, z: -18, glow: 0}],
    creatures: ['shrimp', 'comb'], goal: {type: 'frames', n: 6, label: 'choose the upper or lower cave; take frames'},
    took: 'Twin cave mouths, a jelly trailing sparkling dust between them. Here a rock tongue splits the water into an upper and a lower cave with different films.'},
  {id: 'bloom', title: 'Bloom', source: 'song_nightbus-13', video: '../fal/song_nightbus-13.mp4', song: 'nightbus-13', start: null,
    dir: 'up', len: 150, current: 1.2, band: 10, fog: '#1c2a2a', top: '#548a86', fogD: .024, films: {layout: 'scatter', every: 12}, bad: 0,
    layers: [{kind: 'reef', side: -1, z: -12, glow: .8}, {kind: 'reef', side: 1, z: -12, glow: .8}],
    creatures: ['comb'], surface: true, goal: {type: 'watch', n: 3, label: 'hold on films to watch them bloom (4 s each)'},
    took: 'A jelly rises with small films blooming around it under the surface. Here watching is the whole game: hold on a film and it blooms full size while the water stops.'},
  {id: 'descent', title: 'The Long Descent', source: 'song_nightbus-14', video: '../fal/song_nightbus-14.mp4', song: 'nightbus-14', start: null,
    dir: 'down', len: 240, current: 1.8, band: 9, fog: '#18201f', fogD: .045, films: {layout: 'dark', every: 11}, bad: .08,
    layers: [{kind: 'ruin', side: -1, z: -14, glow: .5}, {kind: 'kelp', side: 1, z: -14, glow: .2}, {kind: 'reef', side: 1, z: 4, glow: .1}],
    creatures: ['angler'], dark: true, goal: {type: 'frames', n: 6, label: 'find films in the dark: double-tap to pulse'},
    took: 'A jelly sinks from lit water into a void and shrinks to a point of light. Here the light closes in as you descend; films show only near you or when you pulse.'},
  {id: 'silt', title: 'Silt Bench', source: 'song_nightbus-17', video: '../fal/song_nightbus-17.mp4', song: 'nightbus-17', start: null,
    dir: 'right', len: 240, current: 1.4, band: 7, fog: '#1d2420', fogD: .034, films: {layout: 'buried', every: 10}, bad: 0,
    layers: [{kind: 'dunes', side: -1, z: -2, glow: 0}, {kind: 'mussels', side: -1, z: -14, glow: .1}, {kind: 'dunes', side: -1, z: -30, glow: 0}],
    creatures: ['angler', 'shrimp'], floorAngler: true, startW: -4.5, goal: {type: 'unearth', n: 5, label: 'stir the silt to uncover buried films'},
    took: 'A seabed of silt where an anglerfish rises out of the floor. Here films lie buried; swim low and fast (or pulse) to stir them up, and watch the floor for the angler.'},
];

// ---------------------------------------------------------------- the archive levels: doodles, and the moving-image archive organised by cineosis sign, by decade, by colour, by subject
// These are fluid: no stopping; you take a frame by swimming through a film while its ring is closed; your film tentacles colour the fish they touch.
const SONGS = ['siltwire-02', 'siltwire-06', 'siltwire-10', 'siltwire-15', 'daehoned-05', 'daehoned-10', 'nightbus-17', 'nightbus-06', 'event-04', 'firstwintera-13', 'firstwintera-18', 'twobuttons-13', 'nightbus-14', 'daehoned-19'];
const TYPEHUE = {perception: 190, affection: 330, impulse: 20, action: 45, reflection: 270, mental: 150, time: 210, sound: 100, read: 60};
const hsl = (h, s, l) => { const k = n => (n + h / 30) % 12, a = s * Math.min(l, 1 - l), f = n => l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1)); return '#' + [f(0), f(8), f(4)].map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join(''); };
const LAYS = [[{kind: 'reef', side: -1, z: -8, glow: .6}, {kind: 'kelp', side: 1, z: -18, glow: .2}], [{kind: 'ruin', side: -1, z: -10, glow: .5}, {kind: 'cave', side: 1, z: -6, glow: .2}], [{kind: 'mussels', side: -1, z: -6, glow: .1}, {kind: 'cave', side: 1, z: -14, glow: .1}], [{kind: 'kelp', side: -1, z: -12, glow: .3}, {kind: 'kelp', side: 1, z: -12, glow: .3}], [{kind: 'dunes', side: -1, z: -4, glow: 0}, {kind: 'reef', side: -1, z: -18, glow: .5}]];
LEVELS.forEach(l => { if (JARS.includes(l.id)) l.jar = 'jars/' + l.id; });

export function archiveLevels(C) {
  const out = [], fluid = true, specks = true;
  out.push({id: 'doodles', kind: 'doodle', title: 'Secondhand Doodles', source: 'secondhand-motion', song: 'daehoned-05', start: null, dir: 'right', len: 300, current: 2.2, band: 9, fog: '#1b2524', fogD: .028, films: {layout: 'doodles', every: 8}, bad: 0,
    layers: LAYS[0].concat([{kind: 'reef', side: -1, z: 5, glow: .1}]), creatures: ['school', 'comb'], fluid, specks, goal: {type: 'color', n: 40, label: 'catch doodles; their tentacles colour the fish they touch'},
    took: 'The crisp traced drawings of the second-hand archive (86 subjects, 1,777 keys, each with the reason it was drawn) swim as line-worms. Catch one and it lights up as a tentacle of its own drawings; brush the school with it and the fish take its colour.'});
  out.push({id: 'menagerie', kind: 'doodle', title: 'Menagerie', source: 'secondhand-motion', song: 'daehoned-18', start: null, dir: 'right', len: 420, current: 1.6, band: 10, fog: '#1d2a28', fogD: .026, films: {layout: 'menagerie'}, bad: 0,
    layers: LAYS[1].concat([{kind: 'kelp', side: -1, z: 5, glow: 0}]), creatures: ['school'], fluid, specks, goal: {type: 'doodles', n: 20, label: 'meet the creatures: touch a drawing and it joins you as a tentacle'},
    took: 'All 86 traced drawings of the second-hand archive at once, as creatures: each swims with its own gait, cycling through its keys; the curious ones come to look at you, the shy ones slip away.'});
  out.push({id: 'bolas', kind: 'doodle', data: 'bolas', title: 'Bolas Planes', source: 'bolas', song: 'daehoned-19', start: null, dir: 'right', len: 520, current: 1.6, band: 10, fog: '#1f2624', fogD: .026, films: {layout: 'menagerie'}, bad: 0,
    layers: LAYS[4].concat([{kind: 'reef', side: 1, z: -16, glow: .4}]), creatures: ['school'], fluid, specks, goal: {type: 'doodles', n: 24, label: 'catch the drawn planes as they replay their motion'},
    took: 'The bolas depth-worm drawings: 321 drawn planes from 109 second-hand shots (a walking giraffe, its young, the grass in front), each in its tracked colour, replaying the motion it had in its shot as it swims.'});
  out.forEach(l => { if (JARS.includes(l.id)) l.jar = 'jars/' + l.id; }); if (!C) return out;
  const decs = [...new Set(C.shots.filter(s => s.dec).map(s => s.dec))].sort();
  out.push({id: 'strata', kind: 'cineosis', title: 'Strata', source: 'cineosis-lab', pick: {by: 'decade'}, song: 'nightbus-14', start: null, dir: 'up', len: decs.length * 26, current: 1.8, band: 10, fog: '#2a2620', top: '#294f52', fogD: .026, films: {layout: 'list'}, bad: 0,
    layers: LAYS[3], creatures: ['school', 'comb'], fluid, specks, goal: {type: 'decades', n: 8, label: 'take a frame from as many decades as you can'},
    took: `Rise through the moving-image archive by date: ${decs[0]}s footage at the bottom, ${decs[decs.length - 1]}s at the top. Black and white thins out as you climb; the water warms from silver to colour.`});
  out.push({id: 'spectrum', kind: 'cineosis', title: 'Spectrum', source: 'cineosis-lab', pick: {by: 'hue'}, song: 'daehoned-15', start: null, dir: 'right', len: 300, current: 2.4, band: 9, fog: '#202024', fogD: .028, films: {layout: 'list'}, bad: 0,
    layers: LAYS[0], creatures: ['school'], fluid, specks, hueWater: true, goal: {type: 'hues', n: 8, label: 'take a frame from every colour'},
    took: 'The archive sorted by its own colour: red footage gives way to amber, green, blue and violet as you drift, and the water takes the colour of the films around it.'});
  for (const [sub, title, song] of [['person', 'People', 'siltwire-06'], ['machine', 'Machines', 'nightbus-06'], ['landscape', 'Landscapes', 'siltwire-15'], ['animal', 'Animals', 'daehoned-18'], ['screen', 'Screens', 'event-03'], ['crowd', 'Crowds', 'twobuttons-14']])
    out.push({id: 'sub-' + sub, kind: 'cineosis', title, source: 'cineosis-lab', pick: {by: 'sub', v: sub}, song, start: null, dir: 'right', len: 240, current: 2.2, band: 9, fog: '#1c2423', fogD: .03, films: {layout: 'list'}, bad: 0,
      layers: LAYS[out.length % 5], creatures: ['school', 'shrimp'], fluid, specks, goal: {type: 'frames', n: 8, label: `take ${title.toLowerCase()} from the archive`}, took: `Every shot whose main subject is ${sub === 'person' ? 'a person' : sub === 'screen' ? 'a screen' : sub}, across the decades.`});
  const types = [...new Set(C.signs.map(g => g.image))];
  types.forEach((ty, i) => { const gs = C.signs.filter(g => g.image === ty), n = C.shots.filter(s => gs.some(g => g.n === s.sign)).length, hue = (i * 360 / types.length + 200) % 360;
    out.push({id: 'type-' + ty.toLowerCase().replace(/[^a-z]+/g, '-'), kind: 'cineosis', title: ty, source: 'cineosis-lab', pick: {by: 'image', v: ty}, song: SONGS[(i + 3) % SONGS.length], start: null, dir: ['right', 'up', 'down'][i % 3], len: 60 + n * 12, current: 2, band: 9,
      fog: hsl(hue, .2, .13), top: hsl(hue, .28, .3), fogD: .028, films: {layout: 'list'}, bad: 0, layers: LAYS[(i + 2) % 5], creatures: ['school', 'comb'], surface: i % 3 === 1, fluid, specks, goal: {type: 'frames', n: Math.min(10, n), label: `take ${ty.toLowerCase()}-images: ${gs.map(g => g.sym).join(' ')}`},
      took: `One level for the ${ty} type: every shot the lab read as ${gs.map(g => g.name).join(', ')}.`, type: true}); });
  // the printed jars of the periodic table (labels/cineosis/*.svg): one per sign, one per type
  const TJ = ['01-perception', '02-affection', '03-impulse', '04-action-small', '05-action-large', '06-attraction', '07-inversion', '08-discourse', '09-dream', '10-recollection', '11-relation', '12-opsign-sonsign', '13-hyalosign', '14-chronosign', '15-noosign', '16-lectosign'];
  out.forEach(l => { if (l.type) { const f = TJ.find(t => t.slice(3) === l.id.slice(5)); if (f) l.jar = 'cineosis/type-' + f; } });
  C.signs.forEach((g, i) => { const dom = (g.dom || '').toLowerCase(), hue = Object.entries(TYPEHUE).find(([k]) => dom.includes(k) || (g.image || '').toLowerCase().includes(k))?.[1] ?? (i * 37) % 360, n = C.shots.filter(s => s.sign === g.n).length;
    out.push({id: 'sign-' + g.n, kind: 'cineosis', sign: g, title: `${g.sym} · ${g.name}`, source: 'cineosis-lab', pick: {by: 'sign', v: g.n}, song: SONGS[i % SONGS.length], start: null, dir: ['right', 'up', 'down'][i % 3], len: 60 + n * 16, current: 1.8, band: 9,
      fog: hsl(hue, .22, .13), top: hsl(hue, .3, .3), fogD: .028, films: {layout: 'list'}, bad: 0, layers: LAYS[i % 5], creatures: ['school', i % 2 ? 'comb' : 'shrimp'], surface: i % 3 === 1, fluid, specks, goal: {type: 'frames', n: Math.min(6, n), label: g.q || g.gloss || g.name},
      jar: `cineosis/sign-${String(g.n).padStart(2, '0')}-${g.sym.toLowerCase()}`, took: `${g.type || g.image}. ${g.gloss ? g.gloss[0].toUpperCase() + g.gloss.slice(1) + '.' : ''} ${n} shots in the archive carry this sign.`}); });
  out.forEach(l => { if (!l.jar && JARS.includes(l.id)) l.jar = 'jars/' + l.id; if (!l.jar && l.id.startsWith('sub-')) l.jar = 'jars/subjects'; });
  return out;
}
