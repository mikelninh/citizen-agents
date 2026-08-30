import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const replay = JSON.parse(await readFile(new URL('../replay-signals.json', import.meta.url), 'utf8'));
const proofHtml = await readFile(new URL('../intelligence-proof.html', import.meta.url), 'utf8');
const replayHtml = await readFile(new URL('../missed-opportunities.html', import.meta.url), 'utf8');

const daysBetween = (from, to) => Math.round((new Date(`${to}T00:00:00Z`) - new Date(`${from}T00:00:00Z`)) / 86400000);

test('historical replay never infers that a stakeholder missed a signal', () => {
  assert.equal(replay.coverage_complete, false);
  assert.equal(replay.truth_boundary.no_inferred_misses, true);
  assert.equal(replay.truth_boundary.no_inferred_roi, true);
  const raw = JSON.stringify(replay).toLowerCase();
  assert.equal(raw.includes('you_missed'), false);
  assert.equal(raw.includes('guaranteed_roi'), false);
});

test('every replay item is source-backed and tied to archive evidence', () => {
  assert.ok(replay.items.length >= 6);
  for (const item of replay.items) {
    assert.ok(item.first_seen);
    assert.ok(item.headline);
    assert.ok(item.archive_evidence);
    assert.ok(Array.isArray(item.sources) && item.sources.length >= 1);
    assert.ok(item.sources.every((url) => /^https:\/\//.test(url)));
  }
});

test('lead-day claims are deterministic calendar-day differences', () => {
  for (const item of replay.items.filter((x) => x.deadline && x.lead_days_at_detection != null)) {
    assert.equal(item.lead_days_at_detection, daysBetween(item.first_seen, item.deadline));
  }
});

test('instant-value UX leads with replay and keeps proof detail secondary', () => {
  assert.match(proofHtml, /2-Minuten Replay starten/);
  assert.match(proofHtml, /Findet Citizen Agents Dinge/);
  assert.match(proofHtml, /details/);
  assert.match(replayHtml, /hätten wir wahrscheinlich verpasst/);
  assert.match(replayHtml, /Bewertungen bleiben lokal/);
  assert.match(replayHtml, /Kein behaupteter ROI/);
});
