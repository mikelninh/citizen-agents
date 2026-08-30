import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreChange, rankChanges, buildUsefulnessReport } from '../impact-core.mjs';

const change = (id, topics, life, verified='MULTI_SOURCE', action=true) => ({
  id,
  observed_on: '2026-08-30',
  topics,
  life_situations: life,
  change: { headline: id },
  impact: { who_is_affected: life.join(', ') },
  actionability: { action_available: action, recommended_action: action ? 'Review now' : '' },
  evidence: { verification_status: verified, source_count: verified === 'MULTI_SOURCE' ? 2 : 1 },
});

test('matched audience/topic outranks unrelated signal', () => {
  const profile = { topics: ['wohngeld'], audiences: ['Mieter:in'] };
  const matched = scoreChange(change('matched', ['wohngeld'], ['Mieter:in']), profile);
  const unrelated = scoreChange(change('other', ['steuer'], ['Studierende']), profile);
  assert.ok(matched.score > unrelated.score);
  assert.ok(matched.score >= 60);
});

test('multi-source/actionable evidence improves score without creating relevance', () => {
  const profile = { topics: ['wohngeld'], audiences: [] };
  const strong = scoreChange(change('strong', ['wohngeld'], [], 'MULTI_SOURCE', true), profile);
  const weak = scoreChange(change('weak', ['wohngeld'], [], 'SINGLE_SOURCE', false), profile);
  assert.ok(strong.score > weak.score);
  const unrelated = scoreChange(change('unrelated', ['steuer'], [], 'MULTI_SOURCE', true), profile);
  assert.ok(unrelated.score <= 18);
});

test('ranking is deterministic and relevance-first', () => {
  const profile = { topics: ['kindergeld'], audiences: ['Eltern/Familie'] };
  const items = [
    change('noise', ['steuer'], ['Studierende']),
    change('family', ['kindergeld'], ['Eltern/Familie']),
  ];
  const ranked = rankChanges(items, profile);
  assert.equal(ranked[0].change.id, 'family');
});

test('usefulness proof never invents ROI and requires observed evidence', () => {
  const ranked = [
    { change: change('a', ['wohngeld'], ['Mieter:in']), score: 80 },
    { change: change('b', ['wohngeld'], ['Mieter:in']), score: 78 },
    { change: change('c', ['wohngeld'], ['Mieter:in']), score: 76 },
  ];
  const judgments = {
    a: { useful: true, would_have_missed: true, action_taken: true },
    b: { useful: true },
    c: { not_useful: true },
  };
  const report = buildUsefulnessReport({ profile: { topics:['wohngeld'] }, judgments, ranked });
  assert.equal(report.observed.reviewed_items, 3);
  assert.equal(report.observed.useful_items, 2);
  assert.equal(report.proof.paid_proof_candidate, true);
  assert.equal(report.truth_boundary.estimated_hours_saved, null);
  assert.equal(report.truth_boundary.guaranteed_roi, false);
});

test('single useful click is not enough to claim paid-proof usefulness', () => {
  const ranked = [{ change: change('a', ['wohngeld'], ['Mieter:in']), score: 80 }];
  const report = buildUsefulnessReport({ judgments: { a: { useful: true } }, ranked });
  assert.equal(report.proof.paid_proof_candidate, false);
});
