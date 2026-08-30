import assert from 'node:assert/strict'
import test from 'node:test'
import { buildIntelligence, normalizeChange, stableChangeId } from './build-org-intelligence.mjs'

test('stable id is deterministic', () => {
  const item = { headline: 'Test', sources: ['https://example.org/a'] }
  assert.equal(stableChangeId(item), stableChangeId(item))
  assert.match(stableChangeId(item), /^chg_[a-f0-9]{16}$/)
})

test('source-backed change carries provenance and fail-safe action authority', () => {
  const result = normalizeChange({
    watchdog: '2026-08-30',
    headline: 'Benefit changed',
    what_changed: 'A rule changed.',
    who_affected: 'Families',
    citizen_tip: 'Review eligibility and prepare an application.',
    tags: ['benefits'],
    life: ['family'],
    sources: ['https://example.org/official', 'https://example.org/secondary'],
  }, { generated: '2026-08-30' })

  assert.equal(result.evidence.verification_status, 'MULTI_SOURCE')
  assert.equal(result.actionability.authority.information_read, 'ALLOW')
  assert.equal(result.actionability.authority.external_or_consequential_action, 'APPROVAL')
  assert.equal(result.impact.criticality, 'UNASSESSED')
  assert.ok(result.evidence.sources.length === 2)
})

test('no source is never silently called verified', () => {
  const result = normalizeChange({ headline: 'Unverified' }, {})
  assert.equal(result.evidence.verification_status, 'UNVERIFIED')
  assert.equal(result.evidence.source_count, 0)
})

test('collection health measures structure without claiming completeness', () => {
  const result = buildIntelligence({
    generated: '2026-08-30',
    items: [
      { headline: 'A', sources: ['https://example.org/a'] },
      { headline: 'B', sources: [] },
    ],
  })
  assert.equal(result.count, 2)
  assert.equal(result.health.source_coverage_pct, 50)
  assert.equal(result.health.criticality_assessed_pct, 0)
  assert.match(result.health.note, /does not claim completeness/i)
})
