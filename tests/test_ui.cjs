const test = require('node:test');
const assert = require('node:assert/strict');
const { PlanState } = require('../static/app.js');

test('editing invalidates the reviewed envelope and stale responses', () => {
  const state = new PlanState();
  const revision = state.revision;
  assert.equal(state.accept({reviewed: true, plan: {actions: [1]}}, revision), true);
  assert.equal(state.canExport(), true);
  state.edited();
  assert.equal(state.canExport(), false);
  assert.equal(state.envelope, null);
  assert.equal(state.accept({reviewed: true}, revision), false);
});

test('review and export require actionable current envelopes', () => {
  const state = new PlanState();
  state.accept({reviewed: false, plan: {actions: []}}, state.revision);
  assert.equal(state.canReview(), false);
  state.accept({reviewed: false, plan: {actions: [1]}}, state.revision);
  assert.equal(state.canReview(), true);
  assert.equal(state.canExport(), false);
});
