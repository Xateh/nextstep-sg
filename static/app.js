'use strict';

const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const isText = value => typeof value === 'string' && value.trim().length > 0;
const isTextArray = value => Array.isArray(value) && value.every(isText);
const hasKeys = (value, keys) => isObject(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const invalidResponse = () => new Error('The service returned an invalid response. Nothing new was accepted or downloaded. Check the service before trying again.');

// Shape checks protect the interface; only the server verifies signatures and ownership.
function validateEnvelope(value) {
  if (!hasKeys(value, ['plan', 'reviewed', 'expires_at', 'principal', 'signature']) ||
      typeof value.reviewed !== 'boolean' || !Number.isSafeInteger(value.expires_at) ||
      value.expires_at <= 0 || value.expires_at > 8640000000000 ||
      !isText(value.principal) || !isText(value.signature)) throw invalidResponse();
  const plan = value.plan;
  if (!isObject(plan) || !['offline', 'bedrock'].includes(plan.mode) ||
      !['draft', 'needs_clarification', 'partial'].includes(plan.status) ||
      !isObject(plan.profile) || typeof plan.profile.goal !== 'string' || plan.profile.synthetic !== true ||
      !Array.isArray(plan.actions) || plan.actions.length > 3 || !isTextArray(plan.questions) ||
      !Array.isArray(plan.trace)) throw invalidResponse();
  for (const action of plan.actions) {
    if (!isObject(action) || !['resource_id', 'title', 'next_step', 'source_url'].every(key => isText(action[key])) ||
        !isTextArray(action.checks)) throw invalidResponse();
  }
  if (new Set(plan.actions.map(action => action.resource_id)).size !== plan.actions.length ||
      (plan.status === 'draft' ? !plan.actions.length : plan.actions.length > 0 || !plan.questions.length)) throw invalidResponse();
}

function sameJson(left, right) {
  if (left === right) return true;
  if (Array.isArray(left)) return Array.isArray(right) && left.length === right.length && left.every((value, index) => sameJson(value, right[index]));
  if (!isObject(left) || !isObject(right)) return false;
  return Object.keys(left).length === Object.keys(right).length &&
    Object.keys(left).every(key => Object.hasOwn(right, key) && sameJson(left[key], right[key]));
}

function validateResponse(path, result, body) {
  if (path === '/v1/plans' || path === '/v1/plans/review') {
    validateEnvelope(result);
    if (path === '/v1/plans') {
      if (result.reviewed || result.plan.mode !== body.mode) throw invalidResponse();
    } else if (!result.reviewed || result.principal !== body.envelope.principal ||
        result.expires_at !== body.envelope.expires_at || !sameJson(result.plan, body.envelope.plan)) throw invalidResponse();
  } else if (path === '/v1/plans/export') {
    if (!hasKeys(result, ['filename', 'content']) || result.filename !== 'transition-plan.md' || !isText(result.content)) throw invalidResponse();
  } else if (path === '/health') {
    if (!isObject(result) || result.status !== 'ok' || !isText(result.version) || result.data_policy !== 'synthetic-only') throw invalidResponse();
  }
}

async function request(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 95000);
  try {
    const response = await fetch(path, {method: body ? 'POST' : 'GET',
      headers: {'Content-Type': 'application/json', 'X-SimplifyNext-Client': '1'},
      body: body ? JSON.stringify(body) : undefined, signal: controller.signal});
    if (!response.ok) {
      const messages = {
        400: 'The service could not accept this request. Check the profile and current plan.',
        403: 'Access was not accepted. Check your AWS session and local server configuration.',
        409: 'A current, actionable plan must be reviewed before downloading.',
        410: 'This plan has expired. Generate and review a fresh plan to continue.',
        429: 'The service is busy or rate-limited. Coordinate with your team before trying again.',
        503: 'The service is unavailable. Check the local server and AWS access.',
      };
      throw Object.assign(new Error(messages[response.status] || `Request failed (${response.status}). Check the service before trying again.`), {status: response.status});
    }
    let result;
    try { result = await response.json(); }
    catch (error) { if (error.name === 'AbortError' || error instanceof TypeError) throw error; throw invalidResponse(); }
    validateResponse(path, result, body);
    return result;
  } catch (error) {
    if (error.name === 'AbortError' || error instanceof TypeError) {
      const cause = error.name === 'AbortError' ? 'Request timed out.' : 'Connection interrupted.';
      const guidance = path === '/v1/plans' && body?.mode === 'bedrock' ?
        ' The server may still finish. Generating again may incur another charge; check with your team first.' :
        ' Check the local server and, if configured, your AWS session before trying again.';
      throw new Error(`${cause}${guidance} The request was not automatically retried.`);
    }
    throw error;
  } finally { clearTimeout(timer); }
}

class PlanState {
  constructor() { this.revision = 0; this.envelope = null; this.serverExpired = false; }
  edited() { this.revision += 1; this.envelope = null; this.serverExpired = false; }
  accept(envelope, revision) {
    if (revision !== this.revision) return false;
    validateEnvelope(envelope);
    this.envelope = envelope;
    this.serverExpired = false;
    return true;
  }
  expire() { this.serverExpired = true; }
  isExpired(now = Date.now()) { return Boolean(this.envelope && (this.serverExpired || this.envelope.expires_at * 1000 <= now)); }
  canReview() { return Boolean(this.envelope?.plan.actions.length) && !this.isExpired(); }
  canExport() { return this.canReview() && this.envelope.reviewed === true; }
}

if (typeof module !== 'undefined') module.exports = { PlanState, request };

if (typeof document !== 'undefined') {
  const $ = id => document.getElementById(id);
  const state = new PlanState();
  let busy = false;
  let expiryTimer;
  const expiryMessage = 'This plan has expired. You can still read it, but must generate and review a fresh plan before downloading.';
  const say = (message, error = false) => {
    $('status').textContent = message;
    $('status').className = error ? 'error' : '';
  };
  const buttons = () => {
    $('profile-fields').disabled = busy;
    $('example').disabled = busy;
    $('edit-profile').disabled = busy;
    $('reset-profile').disabled = busy;
    if (state.isExpired()) $('approval').checked = false;
    $('approval').disabled = busy || !state.canReview() || state.canExport();
    $('review').disabled = busy || !state.canReview() || !$('approval').checked || state.canExport();
    $('export').disabled = busy || !state.canExport();
    $('plan-expiry').textContent = !state.envelope ? '' : state.isExpired() ? expiryMessage :
      `This plan expires at ${new Date(state.envelope.expires_at * 1000).toLocaleTimeString()}. Expiry does not delete downloaded files.`;
  };
  const clearPlan = () => {
    clearTimeout(expiryTimer);
    state.edited();
    $('result').hidden = true;
    for (const id of ['plan-mode', 'plan-goal', 'trace']) $(id).textContent = '';
    $('questions').replaceChildren(); $('actions').replaceChildren();
    $('approval').checked = false;
    buttons();
  };
  const invalidate = () => {
    clearPlan();
    say('Profile changed. Generate and review a fresh plan.');
  };
  function scheduleExpiry() {
    clearTimeout(expiryTimer);
    if (!state.envelope || state.isExpired()) return;
    expiryTimer = setTimeout(() => {
      buttons();
      if (state.isExpired()) say(expiryMessage);
      else scheduleExpiry();
    }, Math.min(state.envelope.expires_at * 1000 - Date.now(), 2147483647));
  }
  function failed(error) {
    if (error.status === 410) state.expire();
    buttons();
    say(error.message, true);
  }
  $('profile-form').addEventListener('input', invalidate);
  $('profile-form').addEventListener('change', invalidate);
  $('approval').addEventListener('change', buttons);

  function paragraph(parent, text, tag = 'p') {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.append(element);
    return element;
  }

  function render() {
    const plan = state.envelope.plan;
    $('result').hidden = false;
    $('plan-mode').textContent = plan.mode === 'offline' ? 'OFFLINE DEMO · No AI used' : 'AWS BEDROCK · Bounded model-assisted plan';
    $('plan-goal').textContent = plan.profile.goal || 'Let’s find a goal first';
    $('questions').replaceChildren();
    $('actions').replaceChildren();
    if (plan.questions.length) {
      paragraph($('questions'), 'Questions to discuss', 'h3');
      const list = document.createElement('ul');
      plan.questions.forEach(question => paragraph(list, question, 'li'));
      $('questions').append(list);
    }
    plan.actions.forEach((action, index) => {
      const card = document.createElement('article');
      card.className = 'action';
      paragraph(card, `${index + 1}. ${action.title}`, 'h3');
      paragraph(card, action.next_step);
      try {
        const source = new URL(action.source_url);
        if (source.protocol === 'https:' && !source.hostname.endsWith('.invalid')) {
          const link = paragraph(card, 'Read source information', 'a');
          link.href = source.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
          link.setAttribute('aria-label', `Read source information for ${action.title} (opens a new tab)`);
        } else { paragraph(card, 'Fictional demo resource — no real booking or provider.'); }
      } catch { paragraph(card, 'Source unavailable; confirm with the provider.'); }
      paragraph(card, 'Check before acting:', 'strong');
      const checks = document.createElement('ul');
      action.checks.forEach(check => paragraph(checks, check, 'li'));
      card.append(checks); $('actions').append(card);
    });
    $('trace').textContent = JSON.stringify(plan.trace, null, 2);
    $('approval').checked = state.canExport();
    buttons();
    scheduleExpiry();
  }

  const numberOrNull = id => $(id).value === '' ? null : Number($(id).value);
  $('profile-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || !$('profile-form').reportValidity()) return;
    clearPlan();
    const revision = state.revision;
    $('result').hidden = true;
    busy = true; buttons(); say('Preparing a short plan to review together.');
    const profile = {goal: $('goal').value.trim(), strengths: $('strengths').value.trim(),
      interests: $('interests').value.split(',').map(value => value.trim()).filter(Boolean),
      full_time_student: $('student').value === '' ? null : $('student').value === 'true',
      weekly_hours: numberOrNull('hours'), budget_sgd: numberOrNull('budget'),
      supporter_goal: $('supporter-goal').value.trim(), synthetic: $('synthetic').checked};
    try {
      const result = await request('/v1/plans', {profile, mode: $('mode').value});
      if (state.accept(result, revision)) {
        render();
        $('plan-title').focus();
        say(state.isExpired() ? expiryMessage : result.plan.status === 'needs_clarification' ? "Update the fictional young adult's profile after discussing these questions, then generate again." :
          result.plan.status === 'partial' ? 'The planner reached its limit. Review the unresolved questions; this is not a complete live plan.' :
          'Draft ready. Review these options with the young adult; they are not confirmed eligibility or available places.');
      }
    } catch (error) { failed(error); }
    finally { busy = false; buttons(); }
  });

  $('review').addEventListener('click', async () => {
    buttons();
    if (busy || !state.canReview() || !$('approval').checked) return;
    busy = true; buttons();
    const revision = state.revision;
    let confirmed = false;
    try {
      const result = await request('/v1/plans/review', {envelope: state.envelope, approved: true});
      if (state.accept(result, revision)) {
        render(); confirmed = state.canExport();
        say(confirmed ? 'Review confirmed for this document. You can now download it.' : expiryMessage);
      }
    } catch (error) { failed(error); }
    finally { busy = false; buttons(); if (confirmed && state.canExport()) $('export').focus(); }
  });

  $('export').addEventListener('click', async () => {
    buttons();
    if (busy || !state.canExport()) return;
    busy = true; buttons();
    const revision = state.revision;
    try {
      const result = await request('/v1/plans/export', {envelope: state.envelope});
      if (revision !== state.revision) return;
      if (!state.canExport()) { say(expiryMessage); return; }
      const url = URL.createObjectURL(new Blob([result.content], {type: 'text/markdown;charset=utf-8'}));
      const link = document.createElement('a'); link.href = url; link.download = result.filename;
      document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      say('Reviewed plan downloaded. Nothing was sent, applied for or booked.');
    } catch (error) { failed(error); }
    finally { busy = false; buttons(); }
  });

  $('example').addEventListener('click', () => {
    if (busy) return;
    $('goal').value = 'Explore office skills at my own pace'; $('strengths').value = 'Organising files and following a checklist';
    $('interests').value = 'office, organising, computers'; $('student').value = 'false';
    $('hours').value = '3'; $('budget').value = '0'; $('supporter-goal').value = '';
    $('synthetic').checked = true; invalidate();
    say('Fictional young adult example loaded. Choose Explore next steps to try it.');
  });
  $('edit-profile').addEventListener('click', () => {
    if (busy) return;
    invalidate(); $('goal').focus();
  });
  $('reset-profile').addEventListener('click', () => {
    if (busy) return;
    $('profile-form').reset(); clearPlan(); $('goal').focus();
    say('Local profile and draft cleared. Offline mode restored. Downloaded files are unchanged.');
  });
  request('/health').then(result => {
    $('connection').textContent = `Service connected · v${result.version} · synthetic profiles only`;
  }).catch(() => { $('connection').textContent = 'Service unavailable. Check the local server and, if configured, your AWS session.'; });
  buttons();
}
