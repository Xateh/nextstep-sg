const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Simulated DOM events only: not rendered-browser or accessibility verification.
const script = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const html = fs.readFileSync(path.join(__dirname, '../static/index.html'), 'utf8');
const start = 1800000000000;
const fields = ['goal', 'strengths', 'interests', 'student', 'hours', 'budget', 'supporter-goal'];
function envelope(overrides = {}) {
  return {plan: {mode: 'offline', status: 'draft',
    profile: {goal: 'Explore fictional office skills', strengths: 'Organising', interests: ['office'],
      full_time_student: false, weekly_hours: 3, budget_sgd: 0, supporter_goal: '', synthetic: true},
    actions: [{resource_id: 'fictional-office', title: 'Fictional office taster',
      next_step: 'Discuss this invented slot', source_url: 'https://example.invalid/office',
      checks: ['Fictional only; no booking']}], questions: [], trace: []},
    reviewed: false, expires_at: start / 1000 + 1800,
    principal: 'a'.repeat(64), signature: 'b'.repeat(64), ...overrides};
}
const response = (body, status = 200) => ({ok: status >= 200 && status < 300, status, json: async () => body});

function harness() {
  let now = start, timerId = 0;
  const timers = new Map(), nodes = new Map(), calls = [], replies = [], downloads = [], blobs = [], focus = [];
  const document = {activeElement: null};
  function element(id = '') {
    let text = '';
    return {id, value: '', checked: false, disabled: false, hidden: false, children: [], handlers: {}, attributes: {},
      get textContent() { return text + this.children.map(child => child.textContent).join(''); },
      set textContent(value) { text = String(value); this.children = []; },
      addEventListener(name, handler) { (this.handlers[name] ||= []).push(handler); },
      append(...children) { this.children.push(...children); },
      replaceChildren(...children) { text = ''; this.children = children; },
      setAttribute(name, value) { this.attributes[name] = String(value); },
      removeAttribute(name) { delete this.attributes[name]; },
      focus() { focus.push({id, disabled: this.disabled}); if (!this.disabled) document.activeElement = this; },
      click() { downloads.push(this); }, remove() {}, reportValidity() { return true; }};
  }
  for (const [, id] of html.matchAll(/\bid="([^"]+)"/g)) nodes.set(id, element(id));
  const el = id => { assert.ok(nodes.has(id), `HTML element ${id} exists`); return nodes.get(id); };
  document.getElementById = el; document.createElement = () => element(); document.body = element();
  el('profile-form').reset = () => {
    for (const id of fields) el(id).value = '';
    el('mode').value = 'offline'; el('synthetic').checked = false;
  };
  el('profile-form').reset(); el('result').hidden = true;
  const sandbox = {document, console, AbortController,
    Date: class extends Date { static now() { return now; } },
    Blob: class extends Blob { constructor(...args) { super(...args); blobs.push(this); } },
    URL: class extends URL { static createObjectURL() { return 'blob:simulated'; } static revokeObjectURL() {} },
    setTimeout(callback, delay) { timers.set(++timerId, {callback, due: now + delay}); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    fetch: async (url, options) => {
      if (url === '/health') return response({status: 'ok', version: '0.1.0', data_policy: 'synthetic-only', default_mode: 'offline'});
      calls.push({url, body: JSON.parse(options.body)});
      assert.ok(replies.length, `Unexpected request: ${url}`);
      return replies.shift();
    }};
  vm.runInNewContext(script, sandbox, {filename: 'static/app.js'});
  async function fire(id, event = 'click') {
    for (const handler of el(id).handlers[event] || []) await handler({preventDefault() {}, target: el(id)});
  }
  async function create(draft = envelope()) {
    await fire('example'); replies.push(response(draft)); await fire('profile-form', 'submit');
  }
  async function review(draft = envelope()) {
    el('approval').checked = true; await fire('approval', 'change');
    replies.push(response({...draft, reviewed: true, signature: 'c'.repeat(64)})); await fire('review');
  }
  async function advance(milliseconds) {
    now += milliseconds;
    for (const [id, timer] of [...timers]) {
      if (timer.due <= now) { timers.delete(id); timer.callback(); }
    }
    await Promise.resolve();
  }
  return {el, fire, create, review, advance, calls, replies, downloads, blobs, focus, document};
}

test('Edit profile invalidates the plan, retains entered fields and focuses the goal', async () => {
  const ui = harness(); await ui.create(); await ui.review();
  const before = fields.map(id => ui.el(id).value);
  await ui.fire('edit-profile');
  assert.equal(ui.el('result').hidden, true);
  assert.equal(ui.el('approval').checked, false);
  assert.equal(ui.el('review').disabled, true); assert.equal(ui.el('export').disabled, true);
  assert.deepEqual(fields.map(id => ui.el(id).value), before);
  assert.equal(ui.document.activeElement, ui.el('goal'));
});

test('Start over clears local profile and plan data and restores offline unchecked defaults', async () => {
  const ui = harness(); await ui.create(); await ui.review();
  ui.el('mode').value = 'bedrock'; ui.el('supporter-goal').value = 'Invented supporter text';
  await ui.fire('reset-profile');
  for (const id of fields) assert.equal(ui.el(id).value, '', id);
  for (const id of ['plan-goal', 'questions', 'actions', 'trace']) assert.equal(ui.el(id).textContent, '', id);
  assert.equal(ui.el('mode').value, 'offline'); assert.equal(ui.el('synthetic').checked, false);
  assert.equal(ui.el('result').hidden, true); assert.equal(ui.el('approval').checked, false);
  assert.equal(ui.el('review').disabled, true); assert.equal(ui.el('export').disabled, true);
  assert.equal(ui.document.activeElement, ui.el('goal'));
  assert.equal(ui.calls.length, 2, 'Reset makes no request');
});

test('creation moves focus to the plan heading', async () => {
  const ui = harness(); await ui.create();
  assert.equal(ui.el('result').hidden, false);
  assert.equal(ui.document.activeElement, ui.el('plan-title'));
});

test('clarification and partial plans show expiry without promising review or download', async () => {
  for (const status of ['needs_clarification', 'partial']) {
    const ui = harness(), draft = envelope();
    draft.plan.status = status; draft.plan.actions = []; draft.plan.questions = ['What matters most to you?'];
    await ui.create(draft);
    assert.equal(ui.el('review').disabled, true); assert.equal(ui.el('export').disabled, true);
    assert.match(ui.el('plan-expiry').textContent, /expires/i);
    assert.doesNotMatch(ui.el('plan-expiry').textContent, /review and download available/i);
  }
});

test('review focuses download only after that control is enabled', async () => {
  const ui = harness(); await ui.create(); await ui.review();
  assert.equal(ui.el('export').disabled, false);
  assert.equal(ui.document.activeElement, ui.el('export'));
  assert.deepEqual(ui.focus.filter(item => item.id === 'export'), [{id: 'export', disabled: false}]);
});

test('expiry timer disables review and download while keeping the draft readable', async () => {
  const ui = harness(), draft = envelope({expires_at: start / 1000 + 2});
  await ui.create(draft); await ui.review(draft);
  const text = ui.el('actions').textContent;
  await ui.advance(2001);
  assert.equal(ui.el('review').disabled, true); assert.equal(ui.el('export').disabled, true);
  assert.equal(ui.el('approval').disabled, true); assert.equal(ui.el('result').hidden, false);
  assert.equal(ui.el('actions').textContent, text); assert.match(ui.el('plan-expiry').textContent, /expired/i);
  assert.equal(ui.calls.length, 2, 'Expiry makes no request');
});

test('HTTP 410 disables stale controls without removing the readable draft', async () => {
  const ui = harness(); await ui.create(); await ui.review();
  ui.replies.push(response({error: 'This plan expired.'}, 410)); await ui.fire('export');
  assert.equal(ui.el('review').disabled, true); assert.equal(ui.el('export').disabled, true);
  assert.equal(ui.el('approval').disabled, true); assert.equal(ui.el('result').hidden, false);
  assert.match(ui.el('status').textContent, /expired/i);
  assert.equal(ui.blobs.length, 0); assert.equal(ui.downloads.length, 0);
});

test('a review that finishes after expiry cannot enable download or claim confirmation', async () => {
  const ui = harness(), draft = envelope({expires_at: start / 1000 + 2});
  await ui.create(draft); ui.el('approval').checked = true;
  let resolve; ui.replies.push(new Promise(done => { resolve = done; }));
  const pending = ui.fire('review');
  await ui.advance(2001);
  resolve(response({...draft, reviewed: true, signature: 'c'.repeat(64)})); await pending;
  assert.equal(ui.el('export').disabled, true);
  assert.equal(ui.el('approval').checked, false);
  assert.match(ui.el('status').textContent, /expired/i);
  assert.equal(ui.focus.some(item => item.id === 'export'), false);
});

test('an export that finishes after expiry never starts a download', async () => {
  const ui = harness(), draft = envelope({expires_at: start / 1000 + 2});
  await ui.create(draft); await ui.review(draft);
  let resolve; ui.replies.push(new Promise(done => { resolve = done; }));
  const pending = ui.fire('export');
  await ui.advance(2001);
  resolve(response({filename: 'transition-plan.md', content: '# Reviewed plan'})); await pending;
  assert.equal(ui.el('export').disabled, true);
  assert.equal(ui.blobs.length, 0); assert.equal(ui.downloads.length, 0);
  assert.match(ui.el('status').textContent, /expired/i);
});

test('malformed export never creates a Blob, starts a download or reports success', async () => {
  const ui = harness(); await ui.create(); await ui.review();
  ui.replies.push(response({})); await ui.fire('export');
  assert.equal(ui.blobs.length, 0); assert.equal(ui.downloads.length, 0);
  assert.match(ui.el('status').textContent, /invalid response/i);
  assert.equal(ui.el('status').className, 'error');
  assert.doesNotMatch(ui.el('status').textContent, /reviewed plan downloaded/i);
  assert.equal(ui.el('profile-fields').disabled, false);
});

for (const operation of ['create', 'review', 'export']) {
  test(`duplicate ${operation} events while pending send only one request`, async () => {
    const ui = harness(); await ui.fire('example');
    if (operation !== 'create') await ui.create();
    if (operation === 'export') await ui.review();
    ui.el('approval').checked = true;
    let resolve; ui.replies.push(new Promise(done => { resolve = done; }));
    const id = operation === 'create' ? 'profile-form' : operation;
    const event = operation === 'create' ? 'submit' : 'click';
    const url = operation === 'create' ? '/v1/plans' : `/v1/plans/${operation}`;
    const first = ui.fire(id, event); await ui.fire(id, event);
    assert.equal(ui.calls.filter(call => call.url === url).length, 1);
    assert.equal(ui.el('profile-fields').disabled, true);
    resolve(response(operation === 'export' ? {filename: 'transition-plan.md', content: '# Reviewed fictional plan'} :
      envelope({reviewed: operation === 'review', signature: 'c'.repeat(64)})));
    await first;
    assert.equal(ui.el('profile-fields').disabled, false);
    assert.equal(ui.downloads.length, operation === 'export' ? 1 : 0);
  });
}
