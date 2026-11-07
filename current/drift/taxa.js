// TAXA: the species of jelly you swim as, and the game each one plays.
// Every level is a species (its body: speed, reach, arms, sting, colour) and a mechanic (its verb: what you do with the films).
// The species are real gelatinous animals from three phyla; the chapters follow one life, from a polyp on the floor to an animal that turns back time.

// ---------------------------------------------------------------- the mechanics: one verb each, with the steps said plainly
export const MECH = {
  tiers:   {verb: 'WAKE',   how: ['Films sleep in galleries on both sides.', 'Brush past one to wake it.', 'Wake as many as you can before the surface.'], nudge: 'swim close along the galleries: a film wakes when you brush it'},
  pairs:   {verb: 'LINK',   how: ['Films come in pairs.', 'Take a frame from one, then from its partner.', 'Each joined pair is a cut.'], nudge: 'take both films of a pair: they drift side by side'},
  scatter: {verb: 'SWEEP',  how: ['Films drift all around you.', 'Tap one to swim to it and take a frame.', 'Your reach is long: sweep through them.'], nudge: 'tap a film to take it; the amber arrows point to the nearest'},
  giant:   {verb: 'WATCH',  how: ['Hold your finger on a film.', 'It comes clear and the water stops.', 'Hold for 4 seconds to watch it: that is your clip.'], nudge: 'press and hold on a film for 4 seconds'},
  halo:    {verb: 'CIRCLE', how: ['A ring of films turns under the surface.', 'Rise to it.', 'Take frames as each film comes round.'], nudge: 'swim up: the ring is near the surface'},
  stream:  {verb: 'CHASE',  how: ['The current runs fast and the films stream past.', 'Boost (two fingers, or shift) to catch them.', 'Take them at speed.'], nudge: 'boost with two fingers or shift and take films as they pass'},
  chain:   {verb: 'REWIND', how: ['One film is laid out as a chain of slices.', 'Take the slices in order.', 'Out of order breaks the run.'], nudge: 'follow the chain and take the bright slice next'},
  caves:   {verb: 'CHOOSE', how: ['A rock tongue splits the water in two.', 'Pick the upper or the lower passage.', 'Each passage has its own films.'], nudge: 'choose a passage, up or down, and take what is in it'},
  dark:    {verb: 'LIGHT',  how: ['The water is dark.', 'Double-tap (or space) to pulse light around you.', 'Films show for a moment: take them.'], nudge: 'double-tap to pulse: films appear in the light'},
  buried:  {verb: 'DIG',    how: ['Films lie buried in the silt.', 'Swim low and fast over the floor, or pulse.', 'They rise: take them.'], nudge: 'swim low and fast along the floor to stir the silt'},
  doodles: {verb: 'DYE',    how: ['Drawings swim as line-worms.', 'Catch one and it becomes your tentacle.', 'Brush the school of fish to dye them its colour.'], nudge: 'catch a drawing, then swim through the fish'},
  menagerie: {verb: 'GATHER', how: ['The drawings are creatures.', 'Touch one and it joins you.', 'The shy ones swim away: corner them.'], nudge: 'touch a drawing-creature to gather it'},
  rewind:  {verb: 'REWIND', how: ['Every film carries its year.', 'Take them going back in time: each older than the last.', 'A later film breaks the run.'], nudge: 'read the year on each film and take an older one'},
  list:    {verb: 'TAKE',   how: ['Films drift ahead.', 'Swim through them to take frames.', 'Take every one you can.'], nudge: 'swim through a film to take it'},
};

// ---------------------------------------------------------------- the species: three phyla of gelatinous animals
// body: speed (x), reach (x capture distance), arms (max), pulse (x radius), sting (does the pulse sting), size (x), tint (bell colour)
export const TAXA = {
  cassiopea:   {name: 'Upside-down jelly', latin: 'Cassiopea xamachana', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 1, chapter: 'The polyp on the floor', mech: 'buried',
    body: {speed: .75, reach: 1.1, arms: 6, pulse: 1.2, sting: true, size: .95, tint: [.75, .95, .7]}, fact: 'It lies bell-down on the floor and lets the algae in its arms feed it. Here you start on the floor, and dig.'},
  aurelia:     {name: 'Moon jelly', latin: 'Aurelia aurita', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 2, chapter: 'The first bell', mech: 'tiers',
    body: {speed: .9, reach: 1.15, arms: 6, pulse: 1, sting: true, size: 1, tint: [.9, .9, 1.05]}, fact: 'The ephyra grows into a moon jelly that drifts more than it swims. Ride the current and wake what you pass.'},
  aequorea:    {name: 'Crystal jelly', latin: 'Aequorea victoria', phylum: 'Cnidaria', cls: 'Hydrozoa', ch: 3, chapter: 'Learning to see', mech: 'giant',
    body: {speed: 1, reach: 1, arms: 8, pulse: 1.3, sting: true, size: 1, tint: [.55, 1.15, .75]}, fact: 'Clear as glass; its green fluorescent protein made the inside of cells visible. Hold on a film and see it clearly.'},
  salpa:       {name: 'Salp chain', latin: 'Salpa maxima', phylum: 'Chordata', cls: 'Thaliacea (not a jelly)', ch: 4, chapter: 'Joining', mech: 'pairs',
    body: {speed: 1.1, reach: 1.2, arms: 8, pulse: .9, sting: false, size: .9, tint: [.85, 1, 1.1]}, fact: 'A tunicate, nearer to us than to jellies, that lives as linked clones. Join the films two by two.'},
  chrysaora:   {name: 'Sea nettle', latin: 'Chrysaora fuscescens', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 5, chapter: 'Choosing', mech: 'caves',
    body: {speed: 1, reach: 1.35, arms: 7, pulse: 1, sting: true, size: 1.05, tint: [1.2, .8, .45]}, fact: 'Long frilled oral arms and a strong sting; it eats comb jellies. Choose your passage and take what lives there.'},
  cyanea:      {name: 'Lion’s mane', latin: 'Cyanea capillata', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 6, chapter: 'Reach', mech: 'scatter',
    body: {speed: .8, reach: 1.9, arms: 8, pulse: 1.1, sting: true, size: 1.3, tint: [1.25, .6, .35]}, fact: 'The longest tentacles of any animal, tens of metres. Slow, but everything near you is in reach.'},
  chironex:    {name: 'Box jelly', latin: 'Chironex fleckeri', phylum: 'Cnidaria', cls: 'Cubozoa', ch: 7, chapter: 'Speed', mech: 'stream',
    body: {speed: 1.55, reach: .9, arms: 4, pulse: .9, sting: true, size: .85, tint: [.8, .95, 1.2]}, fact: 'Twenty-four eyes and a real swimmer: it hunts. Fast and few-armed; choose what you chase.'},
  mnemiopsis:  {name: 'Comb jelly', latin: 'Mnemiopsis leidyi', phylum: 'Ctenophora', cls: 'Tentaculata (not a jelly)', ch: 8, chapter: 'Light without a sting', mech: 'halo',
    body: {speed: 1.2, reach: 1.1, arms: 6, pulse: 1.2, sting: false, size: .9, tint: [1, 1, 1.1], rainbow: true}, fact: 'Rows of beating combs scatter rainbows; it has no stinging cells at all. Your pulse lights, but it will not scare a hunter.'},
  pelagia:     {name: 'Mauve stinger', latin: 'Pelagia noctiluca', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 9, chapter: 'Bloom', mech: 'giant',
    body: {speed: .9, reach: 1.1, arms: 8, pulse: 1.4, sting: true, size: 1, tint: [1.1, .6, 1.2]}, fact: 'It blooms in millions and glows when touched. Stop, hold, and let each film bloom.'},
  physalia:    {name: 'Portuguese man o’ war', latin: 'Physalia physalis', phylum: 'Cnidaria', cls: 'Hydrozoa (a colony)', ch: 10, chapter: 'Colony', mech: 'doodles',
    body: {speed: .85, reach: 1.5, arms: 8, pulse: 1, sting: true, size: 1.1, tint: [.7, .6, 1.3]}, fact: 'Not one animal but a colony of zooids under a gas sail. Every drawing you catch becomes one of you.'},
  velella:     {name: 'By-the-wind sailor', latin: 'Velella velella', phylum: 'Cnidaria', cls: 'Hydrozoa', ch: 11, chapter: 'Gather', mech: 'menagerie',
    body: {speed: 1, reach: 1.3, arms: 8, pulse: 1, sting: true, size: .9, tint: [.5, .75, 1.3]}, fact: 'A blue float with a sail that the wind steers; whole fleets wash up together. Gather the creatures as you go.'},
  atolla:      {name: 'Atolla', latin: 'Atolla wyvillei', phylum: 'Cnidaria', cls: 'Scyphozoa', ch: 12, chapter: 'The deep', mech: 'dark',
    body: {speed: .9, reach: 1, arms: 6, pulse: 1.7, sting: true, size: 1, tint: [1.35, .35, .3]}, fact: 'A deep-red jelly whose alarm of light calls bigger predators to eat its attacker. In the dark, your pulse is everything.'},
  turritopsis: {name: 'Immortal jelly', latin: 'Turritopsis dohrnii', phylum: 'Cnidaria', cls: 'Hydrozoa', ch: 13, chapter: 'Rewind', mech: 'chain',
    body: {speed: 1, reach: 1, arms: 8, pulse: 1, sting: true, size: .7, tint: [1.3, .75, .5]}, fact: 'When it is hurt or old it turns back into a polyp and begins again. Take time backwards.'},
};
export const ARC = Object.entries(TAXA).sort((a, b) => a[1].ch - b[1].ch).map(([id, t]) => ({id, ...t}));
// the hero level of each chapter (a drift), and the species of every other level by its mechanic or its cineosis type
export const HERO = {cassiopea: 'silt', aurelia: 'ascent', aequorea: 'surface', salpa: 'pairs', chrysaora: 'caves', cyanea: 'lure', chironex: 'rayrun', mnemiopsis: 'halo', pelagia: 'bloom', physalia: 'doodles', velella: 'menagerie', atolla: 'descent', turritopsis: 'slices'};
// the cineosis types, each read as a species and its verb
export const BY_TYPE = {perception: 'atolla', affection: 'aequorea', impulse: 'chironex', 'action-small': 'cyanea', 'action-large': 'chrysaora', attraction: 'salpa', inversion: 'cassiopea', discourse: 'aurelia', dream: 'pelagia', recollection: 'turritopsis', relation: 'salpa',
  'opsign-sonsign': 'mnemiopsis', hyalosign: 'aequorea', chronosign: 'turritopsis', noosign: 'atolla', lectosign: 'aurelia'};
export const BY_SUB = {person: 'aequorea', machine: 'chironex', landscape: 'cyanea', animal: 'salpa', screen: 'mnemiopsis', crowd: 'aurelia'};
export const speciesOf = l => TAXA[l.species] || TAXA.aurelia;
// the verb of a level: its layout, unless its goal is to watch
export const mechOf = l => l.sea ? null : l.goal && l.goal.type === 'watch' ? MECH.giant : MECH[l.films.layout] || MECH.list;
export const an = w => (/^[aeiou]/i.test(w) ? 'an ' : 'a ') + w;
