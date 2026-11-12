// Identity belongs to an actor, independently of the page or visible rig.
const definitions = [
  ['G', 'Anchor', 'anchor-1', 128, 0.05, 0, 0.08, 0.58, 0.25],
  ['J', 'Glint', 'glint-1', 190, 0.72, 0, 0.12, 0.52, 0.44],
  ['F1', 'Glass', 'glass-1', 218, 0.9, 0.05, 0.06, 0.66, 0.62],
  ['F2', 'Ember', 'ember-1', 148, 0.23, 0, 0.18, 0.46, 0.22],
  ['F3', 'Veil', 'veil-1', 174, 0.6, 0, 0.25, 0.4, 0.31],
];
export const CAST = Object.freeze(Object.fromEntries(definitions.map(([actorId, name, id, f0, female, child, breathiness, tension, brightness]) => [actorId, Object.freeze({
  actorId, name, voice_profile_id: id, voice_profile_revision: 1, f0,
  body: Object.freeze({female, child}),
  source: Object.freeze({breathiness, tension, brightness, roughness: 0, drift: 0}),
})])));
export function resolveActor(actorId) {
  const actor = Object.hasOwn(CAST, actorId) ? CAST[actorId] : null;
  if (!actor) throw new Error(`Unknown actor: ${actorId}`);
  return actor;
}
