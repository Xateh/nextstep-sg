'use strict';

class PlanState {
  constructor() { this.revision = 0; this.envelope = null; }
  edited() { this.revision += 1; this.envelope = null; }
  accept(envelope, revision) {
    if (revision !== this.revision) return false;
    this.envelope = envelope;
    return true;
  }
  canReview() { return Boolean(this.envelope?.plan?.actions?.length); }
  canExport() { return this.canReview() && this.envelope.reviewed === true; }
}

if (typeof module !== 'undefined') module.exports = { PlanState };

if (typeof document !== 'undefined') {
  const $ = id => document.getElementById(id);
  const state = new PlanState();
  let busy = false;
  const say = (message, error = false) => {
    $('status').textContent = message;
    $('status').className = error ? 'error' : '';
  };
  const buttons = () => {
    $('profile-fields').disabled = busy;
    $('example').disabled = busy;
    $('approval').disabled = busy || !state.canReview() || state.canExport();
    $('review').disabled = busy || !state.canReview() || !$('approval').checked || state.canExport();
    $('export').disabled = busy || !state.canExport();
  };
  const invalidate = () => {
    state.edited();
    $('result').hidden = true;
    $('approval').checked = false;
    buttons();
    say('Profile changed. Generate and review a fresh plan.');
  };
  $('profile-form').addEventListener('input', invalidate);
  $('profile-form').addEventListener('change', invalidate);
  $('approval').addEventListener('change', buttons);

  async function request(path, body) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 95000);
    try {
      const response = await fetch(path, {method: body ? 'POST' : 'GET',
        headers: {'Content-Type': 'application/json', 'X-SimplifyNext-Client': '1'},
        body: body ? JSON.stringify(body) : undefined, signal: controller.signal});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
      return result;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('Request timed out. No live result was fabricated. Try again after checking AWS access.');
      throw error;
    } finally { clearTimeout(timer); }
  }

  function paragraph(parent, text, tag = 'p') {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.append(element);
    return element;
  }

  function render() {
    const plan = state.envelope.plan;
    $('result').hidden = false;
    $('plan-mode').textContent = plan.mode === 'offline' ? 'OFFLINE DEMO · No AI used' : 'AWS BEDROCK · Bounded tool loop';
    $('plan-goal').textContent = plan.profile.goal || 'Let’s find a goal first';
    $('questions').replaceChildren();
    $('actions').replaceChildren();
    if (plan.questions.length) {
      paragraph($('questions'), 'Questions before moving forward', 'h3');
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
  }

  const numberOrNull = id => $(id).value === '' ? null : Number($(id).value);
  $('profile-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || !$('profile-form').reportValidity()) return;
    state.edited();
    const revision = state.revision;
    $('result').hidden = true;
    busy = true; buttons(); say('Preparing a short plan. You can review every next step.');
    const profile = {goal: $('goal').value.trim(), strengths: $('strengths').value.trim(),
      interests: $('interests').value.split(',').map(value => value.trim()).filter(Boolean),
      full_time_student: $('student').value === '' ? null : $('student').value === 'true',
      weekly_hours: numberOrNull('hours'), budget_sgd: numberOrNull('budget'),
      supporter_goal: $('supporter-goal').value.trim(), synthetic: $('synthetic').checked};
    try {
      const result = await request('/v1/plans', {profile, mode: $('mode').value});
      if (state.accept(result, revision)) {
        render();
        say(result.plan.status === 'needs_clarification' ? 'Answer the questions by updating your profile, then generate again.' :
          result.plan.status === 'partial' ? 'The planner reached its limit. Review the unresolved questions; this is not a complete live plan.' :
          'Draft ready. These are options to explore, not confirmed eligibility or available places.');
      }
    } catch (error) { say(error.message, true); }
    finally { busy = false; buttons(); }
  });

  $('review').addEventListener('click', async () => {
    if (busy || !state.canReview() || !$('approval').checked) return;
    busy = true; buttons();
    const revision = state.revision;
    try {
      const result = await request('/v1/plans/review', {envelope: state.envelope, approved: true});
      if (state.accept(result, revision)) { render(); say('Review confirmed for this document. You can now download it.'); }
    } catch (error) { say(error.message, true); }
    finally { busy = false; buttons(); }
  });

  $('export').addEventListener('click', async () => {
    if (busy || !state.canExport()) return;
    busy = true; buttons();
    try {
      const result = await request('/v1/plans/export', {envelope: state.envelope});
      const url = URL.createObjectURL(new Blob([result.content], {type: 'text/markdown;charset=utf-8'}));
      const link = document.createElement('a'); link.href = url; link.download = result.filename;
      document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      say('Reviewed plan downloaded. Nothing was sent, applied for or booked.');
    } catch (error) { say(error.message, true); }
    finally { busy = false; buttons(); }
  });

  $('example').addEventListener('click', () => {
    $('goal').value = 'Explore office skills at my own pace'; $('strengths').value = 'Organising files and following a checklist';
    $('interests').value = 'office, organising, computers'; $('student').value = 'false';
    $('hours').value = '3'; $('budget').value = '0'; $('supporter-goal').value = '';
    $('synthetic').checked = true; invalidate();
    say('Fictional example loaded. Choose Explore next steps to try it.');
  });
  request('/health').then(result => {
    $('connection').textContent = `Service connected · v${result.version} · synthetic profiles only`;
  }).catch(() => { $('connection').textContent = 'Service unavailable. Check the local server and, if configured, your AWS session.'; });
  buttons();
}
