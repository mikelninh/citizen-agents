import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreChange, rankChanges, buildUsefulnessReport } from '../impact-core.mjs';

const change = (id, topics, life, verified='MULTI_SOURCE', action=true, extra={}) => ({
  id,
  observed_on: '2026-08-30',
  topics,
  life_situations: life,
  change: { headline: id, deadline: extra.deadline || '' },
  impact: { who_is_affected: life.join(', ') },
  actionability: { action_available: action, recommended_action: action ? 'Review now' : '' },
  evidence: { verification_status: verified, source_count: verified === 'MULTI_SOURCE' ? 2 : 1 },
  ...extra,
});

test('matched audience/topic outranks unrelated signal', () => {
  const profile = { topics: ['wohngeld'], audiences: ['Mieter:in'] };
  const matched = scoreChange(change('matched', ['wohngeld'], ['Mieter:in']), profile, {asOf:'2026-08-30'});
  const unrelated = scoreChange(change('other', ['steuer'], ['Studierende']), profile, {asOf:'2026-08-30'});
  assert.ok(matched.score > unrelated.score);
  assert.ok(matched.score >= 50);
});

test('multi-source/actionable evidence improves score without creating relevance', () => {
  const profile = { topics: ['wohngeld'], audiences: [] };
  const strong = scoreChange(change('strong', ['wohngeld'], [], 'MULTI_SOURCE', true), profile);
  const weak = scoreChange(change('weak', ['wohngeld'], [], 'SINGLE_SOURCE', false), profile);
  assert.ok(strong.score > weak.score);
  const unrelated = scoreChange(change('unrelated', ['steuer'], [], 'MULTI_SOURCE', true), profile);
  assert.ok(unrelated.score <= 18);
});

test('family, jurisdiction and mission terms create meaningful organisation relevance', () => {
  const signal = change('hearing', ['health'], [], 'OFFICIAL_PRIMARY', true, {
    family:'democracy_action_window',
    jurisdictions:['DE'],
    related_terms:['notfallversorgung','krankenhaus'],
    action_window:{deadline:'2026-09-07'},
  });
  const profile = {
    families:['democracy_action_window'], jurisdictions:['DE'], mission:'Krankenhaus Notfallversorgung', services:['Krankenhaus']
  };
  const scored = scoreChange(signal, profile, {asOf:'2026-08-30'});
  assert.ok(scored.score >= 60);
  assert.ok(scored.daysRemaining <= 8);
  assert.ok(scored.reasons.some((x) => x.includes('Zeitkritisch') || x.includes('Action Window')));
});

test('ranking is deterministic and relevance-first', () => {
  const profile = { topics: ['kindergeld'], audiences: ['Eltern/Familie'] };
  const items = [
    change('noise', ['steuer'], ['Studierende']),
    change('family', ['kindergeld'], ['Eltern/Familie']),
  ];
  const ranked = rankChanges(items, profile, {asOf:'2026-08-30'});
  assert.equal(ranked[0].change.id, 'family');
});

test('near action window outranks same-relevance later item', () => {
  const profile = { families:['democracy_action_window'] };
  const near = change('near', [], [], 'OFFICIAL_PRIMARY', true, {family:'democracy_action_window',action_window:{deadline:'2026-09-02'}});
  const later = change('later', [], [], 'OFFICIAL_PRIMARY', true, {family:'democracy_action_window',action_window:{deadline:'2026-11-15'}});
  const ranked = rankChanges([later,near], profile, {asOf:'2026-08-30'});
  assert.equal(ranked[0].change.id, 'near');
});

test('usefulness proof never invents ROI and requires observed evidence', () => {
  const ranked = [
    { change: change('a', ['wohngeld'], ['Mieter:in']), score: 80, daysRemaining: 5 },
    { change: change('b', ['wohngeld'], ['Mieter:in']), score: 78, daysRemaining: null },
    { change: change('c', ['wohngeld'], ['Mieter:in']), score: 76, daysRemaining: null },
  ];
  const judgments = {
    a: { useful: true, would_have_missed: true, action_taken: true },
    b: { useful: true },
    c: { not_useful: true },
  };
  const report = buildUsefulnessReport({ profile: { topics:['wohngeld'] }, judgments, ranked });
  assert.equal(report.observed.reviewed_items, 3);
  assert.equal(report.observed.useful_items, 2);
  assert.equal(report.observed.time_sensitive_useful_items, 1);
  assert.equal(report.proof.paid_proof_candidate, true);
  assert.equal(report.truth_boundary.estimated_hours_saved, null);
  assert.equal(report.truth_boundary.customer_value_eur, null);
  assert.equal(report.truth_boundary.guaranteed_roi, false);
  assert.equal(report.truth_boundary.coverage_complete, false);
});

test('single useful click is not enough to claim paid-proof usefulness', () => {
  const ranked = [{ change: change('a', ['wohngeld'], ['Mieter:in']), score: 80 }];
  const report = buildUsefulnessReport({ judgments: { a: { useful: true } }, ranked });
  assert.equal(report.proof.paid_proof_candidate, false);
});
