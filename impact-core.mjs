export const IMPACT_SCHEMA = 'citizen-impact-proof/1.0';

function norm(value) {
  return String(value || '').trim().toLowerCase();
}

function setOf(values = []) {
  return new Set(values.map(norm).filter(Boolean));
}

export function scoreChange(change, profile = {}) {
  const topics = setOf(profile.topics);
  const audiences = setOf(profile.audiences);
  const changeTopics = (change.topics || []).map(norm);
  const changeAudiences = (change.life_situations || []).map(norm);

  let score = 0;
  const reasons = [];

  const topicHits = changeTopics.filter((x) => topics.has(x));
  if (topicHits.length) {
    score += Math.min(45, 24 + topicHits.length * 9);
    reasons.push(`Themen-Match: ${topicHits.join(', ')}`);
  }

  const audienceHits = changeAudiences.filter((x) => audiences.has(x));
  if (audienceHits.length) {
    score += Math.min(35, 20 + audienceHits.length * 8);
    reasons.push(`Zielgruppen-Match: ${audienceHits.join(', ')}`);
  }

  const verification = norm(change?.evidence?.verification_status);
  if (verification === 'multi_source') {
    score += 12;
    reasons.push('Mehrquellen-Nachweis');
  } else if (change?.evidence?.source_count > 0) {
    score += 6;
    reasons.push('Quelle vorhanden');
  }

  if (change?.actionability?.action_available) {
    score += 8;
    reasons.push('Konkreter nächster Schritt verfügbar');
  }

  if (!topicHits.length && !audienceHits.length) score = Math.min(score, 18);

  return {
    score: Math.max(0, Math.min(100, score)),
    reasons,
    topicHits,
    audienceHits,
  };
}

export function rankChanges(items = [], profile = {}) {
  return items
    .map((change) => ({ change, ...scoreChange(change, profile) }))
    .sort((a, b) => b.score - a.score || String(b.change.observed_on).localeCompare(String(a.change.observed_on)));
}

export function buildUsefulnessReport({ profile = {}, judgments = {}, ranked = [], startedAt = null, finishedAt = null } = {}) {
  const entries = ranked
    .filter((row) => judgments[row.change.id])
    .map((row) => ({
      change_id: row.change.id,
      headline: row.change.change?.headline || '',
      impact_score: row.score,
      judgment: judgments[row.change.id],
      verification_status: row.change.evidence?.verification_status || 'UNKNOWN',
      source_count: Number(row.change.evidence?.source_count || 0),
    }));

  const total = entries.length;
  const count = (field) => entries.filter((e) => e.judgment?.[field] === true).length;
  const useful = count('useful');
  const wouldHaveMissed = count('would_have_missed');
  const actionTaken = count('action_taken');
  const alreadyKnew = count('already_knew');
  const falsePositive = count('not_useful');

  const minutes = startedAt && finishedAt
    ? Math.max(0, Math.round((new Date(finishedAt).getTime() - new Date(startedAt).getTime()) / 60000))
    : null;

  return {
    schema_version: IMPACT_SCHEMA,
    generated_at: new Date().toISOString(),
    profile: {
      organisation_type: profile.organisationType || '',
      topics: profile.topics || [],
      audiences: profile.audiences || [],
      workflow: profile.workflow || '',
    },
    observed: {
      reviewed_items: total,
      useful_items: useful,
      useful_rate: total ? Number((useful / total).toFixed(3)) : null,
      would_have_missed_items: wouldHaveMissed,
      action_taken_items: actionTaken,
      already_known_items: alreadyKnew,
      not_useful_items: falsePositive,
      review_minutes: minutes,
    },
    proof: {
      useful_signal_observed: useful > 0,
      miss_prevention_observed: wouldHaveMissed > 0,
      actionability_observed: actionTaken > 0,
      paid_proof_candidate: total >= 3 && useful / total >= 0.6 && falsePositive / total <= 0.4,
    },
    truth_boundary: {
      estimated_hours_saved: null,
      guaranteed_roi: false,
      note: 'This report measures observed usefulness judgments. It does not infer financial ROI or completeness of coverage.',
    },
    entries,
  };
}
