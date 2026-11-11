// Presentation-only response to a prepared take. These values never enter a
// pacemaker, force accumulator, user-gesture recorder, or sound-event stream.
export const unit = value => Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
export const meanUnit = values => {
  if (!values.length) return 0;
  let sum = 0;
  for (const value of values) sum += unit(value);
  return sum / values.length;
};

export function createVoiceMotion() {
  const state = {active: false, actorId: null, level: 0};
  const onStop = () => {
    state.active = false;
    state.actorId = null;
    state.level = 0;
  };
  const applyFrame = frame => {
    if (!frame?.active || frame.origin !== 'voice-playback') return onStop();
    state.active = true;
    state.actorId = frame.actorId;
    state.level = unit(frame.level);
  };
  return {
    get active() { return state.active; },
    get actorId() { return state.actorId; },
    get level() { return state.level; },
    applyFrame,
    onStop,
  };
}
