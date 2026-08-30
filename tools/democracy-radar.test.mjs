import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const signals = JSON.parse(fs.readFileSync(new URL('../democracy-signals.json', import.meta.url)));
const registry = JSON.parse(fs.readFileSync(new URL('../watchdog-registry.json', import.meta.url)));

const families = new Set(registry.families.map((f) => f.id));

test('registry contains core democracy watchdog families', () => {
  for (const id of ['rights_money','democracy_action_window','funding_radar','rights_courts','power_influence','participation_radar','promises_laws_votes']) {
    assert.ok(families.has(id), `missing ${id}`);
  }
});

test('live democracy seed is explicitly non-exhaustive', () => {
  assert.equal(signals.coverage_complete, false);
  assert.equal(signals.capture_mode, 'CURATED_OFFICIAL_SOURCE');
  assert.ok(signals.truth_boundary.includes('not a claim'));
});

test('every democracy signal has evidence and authority boundary', () => {
  assert.ok(signals.items.length >= 8);
  for (const item of signals.items) {
    assert.ok(item.id);
    assert.ok(families.has(item.family));
    assert.ok(item.change?.headline);
    assert.ok(item.impact?.who_is_affected);
    assert.ok(item.actionability?.recommended_action);
    assert.equal(item.actionability?.authority?.external_or_consequential_action, 'APPROVAL');
    assert.ok(item.evidence?.source_count >= 1);
    assert.ok(item.evidence?.sources?.[0]?.startsWith('https://'));
  }
});

test('funding value never masquerades as customer value', () => {
  const funding = signals.items.find((x) => x.family === 'funding_radar');
  assert.ok(funding);
  assert.ok(funding.opportunity.programme_budget_eur > 0);
  assert.equal(funding.opportunity.customer_value_eur, null);
});

test('action windows expose machine-readable deadlines', () => {
  const windows = signals.items.filter((x) => x.action_window?.deadline);
  assert.ok(windows.length >= 5);
  for (const item of windows) assert.match(item.action_window.deadline, /^2026-\d{2}-\d{2}$/);
});
