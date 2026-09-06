const test = require('node:test');
const assert = require('node:assert/strict');
const { PlanState, request } = require('../static/app.js');

function envelope(overrides = {}) {
  return {
    plan: {
      mode: 'offline', status: 'draft',
      profile: {goal: 'Explore office skills', strengths: '', interests: ['office'],
        full_time_student: null, weekly_hours: 3, budget_sgd: 0, synthetic: true},
      actions: [{resource_id: 'fictional-office', title: 'Office taster',
        next_step: 'Discuss a fictional taster', source_url: 'https://example.invalid/office',
        checks: ['Confirm interest together']}], questions: [], trace: [],
    },
    reviewed: false, expires_at: Math.floor(Date.now() / 1000) + 1800,
    principal: 'a'.repeat(64), signature: 'b'.repeat(64), ...overrides,
  };
}

test('editing invalidates the reviewed envelope and stale responses', () => {
  const state = new PlanState();
  const revision = state.revision;
  assert.equal(state.accept(envelope({reviewed: true}), revision), true);
  assert.equal(state.canExport(), true);
  state.edited();
  assert.equal(state.canExport(), false);
  assert.equal(state.envelope, null);
  assert.equal(state.accept({reviewed: true}, revision), false);
});

test('review and export require actionable current envelopes', () => {
  const state = new PlanState();
  const partial = envelope();
  partial.plan.status = 'partial'; partial.plan.actions = []; partial.plan.questions = ['What interests you?'];
  state.accept(partial, state.revision);
  assert.equal(state.canReview(), false);
  state.accept(envelope(), state.revision);
  assert.equal(state.canReview(), true);
  assert.equal(state.canExport(), false);
});

test('expired plans remain readable but cannot be reviewed or exported', () => {
  const state = new PlanState();
  const expired = envelope({reviewed: true, expires_at: 1});
  state.accept(expired, state.revision);
  assert.equal(state.canReview(), false);
  assert.equal(state.canExport(), false);
  assert.equal(state.envelope, expired);
  assert.equal(state.isExpired(), true);
});

test('expiry includes the exact boundary and server expiry never mutates signed data', () => {
  const state = new PlanState();
  const original = envelope();
  state.accept(original, state.revision);
  assert.equal(state.isExpired(original.expires_at * 1000 - 1), false);
  assert.equal(state.isExpired(original.expires_at * 1000), true);
  const before = JSON.stringify(original);
  state.expire();
  assert.equal(state.canReview(), false);
  assert.equal(JSON.stringify(original), before);
  state.edited(); state.accept(envelope(), state.revision);
  assert.equal(state.canReview(), true);
});

test('malformed envelopes never replace a valid draft', () => {
  const mutations = [
    value => { value.plan.questions = null; },
    value => { value.plan.actions[0].checks = 'not an array'; },
    value => { value.plan.actions[0].next_step = null; },
    value => { value.plan.trace = null; },
    value => { value.expires_at = 'tomorrow'; },
    value => { value.reviewed = 'true'; },
    value => { value.plan.mode = 'unknown'; },
    value => { value.plan.profile.synthetic = false; },
    value => { value.plan.actions = []; },
    value => { value.plan.status = 'partial'; },
    value => { value.signature = ''; },
  ];
  for (const mutate of mutations) {
    const state = new PlanState(); const valid = envelope();
    state.accept(valid, state.revision);
    const bad = envelope(); mutate(bad);
    assert.throws(() => state.accept(bad, state.revision), /invalid response/i);
    assert.equal(state.envelope, valid);
  }
});

function respond(t, result) {
  return t.mock.method(globalThis, 'fetch', async () => ({ok: true, json: async () => result}));
}

test('creation accepts a valid draft but rejects malformed or silently changed mode responses', async t => {
  const valid = envelope(); const fetch = respond(t, valid);
  assert.equal(await request('/v1/plans', {mode: 'offline'}), valid);
  assert.equal(fetch.mock.calls.length, 1);
  assert.equal(fetch.mock.calls[0].arguments[1].headers['X-SimplifyNext-Client'], '1');
  await assert.rejects(request('/v1/plans', {mode: 'bedrock'}), /invalid response/i);
  valid.plan.questions = null;
  await assert.rejects(request('/v1/plans', {mode: 'offline'}), /invalid response/i);
});

test('review must preserve the plan, principal and expiry; object key order may differ', async t => {
  const draft = envelope();
  const reviewed = envelope({reviewed: true, expires_at: draft.expires_at, signature: 'c'.repeat(64)});
  reviewed.plan = Object.fromEntries(Object.entries(draft.plan).reverse());
  respond(t, reviewed);
  assert.equal(await request('/v1/plans/review', {envelope: draft, approved: true}), reviewed);
  for (const changed of [
    {...reviewed, reviewed: false}, {...reviewed, expires_at: draft.expires_at + 1},
    {...reviewed, principal: 'd'.repeat(64)},
    {...reviewed, plan: {...draft.plan, profile: {...draft.plan.profile, goal: 'Changed'}}},
  ]) {
    globalThis.fetch = async () => ({ok: true, json: async () => changed});
    await assert.rejects(request('/v1/plans/review', {envelope: draft, approved: true}), /invalid response/i);
  }
});

test('downloads require the expected filename and nonempty Markdown content', async t => {
  const valid = {filename: 'transition-plan.md', content: '# Reviewed plan'};
  respond(t, valid);
  assert.equal(await request('/v1/plans/export', {envelope: envelope({reviewed: true})}), valid);
  for (const bad of [{}, {...valid, content: null}, {...valid, content: '  '},
    {...valid, filename: '../unexpected.html'}, {...valid, extra: true}]) {
    globalThis.fetch = async () => ({ok: true, json: async () => bad});
    await assert.rejects(request('/v1/plans/export', {}), /invalid response/i);
  }
});

test('HTTP expiry survives non-JSON error bodies and untrusted server text is not displayed', async t => {
  t.mock.method(globalThis, 'fetch', async () => ({ok: false, status: 410,
    json: async () => { throw new SyntaxError('private upstream details'); }}));
  await assert.rejects(request('/v1/plans/review', {}), error => {
    assert.equal(error.status, 410); assert.match(error.message, /expired/i);
    assert.doesNotMatch(error.message, /private/); return true;
  });
});

test('invalid JSON is rejected with safe guidance', async t => {
  t.mock.method(globalThis, 'fetch', async () => ({ok: true,
    json: async () => { throw new SyntaxError('private upstream details'); }}));
  await assert.rejects(request('/v1/plans/export', {}), /invalid response/i);
});

test('interrupted Bedrock creation warns of possible completion and cost without retrying', async t => {
  for (const error of [Object.assign(new Error('aborted'), {name: 'AbortError'}), new TypeError('Failed to fetch')]) {
    const fetch = t.mock.method(globalThis, 'fetch', async () => { throw error; });
    await assert.rejects(request('/v1/plans', {mode: 'bedrock'}), failure => {
      assert.match(failure.message, /may still (finish|complete)/i);
      assert.match(failure.message, /charge/i); assert.match(failure.message, /not.*retried/i); return true;
    });
    assert.equal(fetch.mock.calls.length, 1);
    fetch.mock.restore();
  }
});

test('offline timeout never implies a paid call and health must be valid', async t => {
  t.mock.method(globalThis, 'fetch', async () => { throw Object.assign(new Error(), {name: 'AbortError'}); });
  await assert.rejects(request('/v1/plans', {mode: 'offline'}), error => {
    assert.match(error.message, /timed out/i); assert.doesNotMatch(error.message, /charge/i); return true;
  });
  globalThis.fetch = async () => ({ok: true, json: async () => ({version: undefined})});
  await assert.rejects(request('/health'), /invalid response/i);
});

test('a Bedrock connection lost after headers keeps the duplicate-charge warning', async t => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => ({ok: true,
    json: async () => { throw new TypeError('terminated'); }}));
  await assert.rejects(request('/v1/plans', {mode: 'bedrock'}), error => {
    assert.match(error.message, /may still finish/i);
    assert.match(error.message, /another charge/i);
    assert.match(error.message, /not automatically retried/i); return true;
  });
  assert.equal(fetch.mock.calls.length, 1);
});
