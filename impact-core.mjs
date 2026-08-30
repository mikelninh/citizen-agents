export const IMPACT_SCHEMA = 'citizen-impact-proof/1.1';

function norm(value) {
  return String(value || '').trim().toLowerCase();
}

function arr(value) {
  return Array.isArray(value) ? value : value ? [value] : [];
}

function setOf(values = []) {
  return new Set(arr(values).map(norm).filter(Boolean));
}

function tokenise(values = []) {
  return arr(values)
    .flatMap((value) => norm(value).split(/[^a-z0-9äöüß]+/i))
    .filter((x) => x.length >= 3);
}

function overlaps(left = [], right = []) {
  const l = setOf(left);
  return arr(right).map(norm).filter((x) => l.has(x));
}

function keywordHits(change, profile) {
  const needles = new Set(tokenise([
    ...(profile.keywords || []),
    ...(profile.services || []),
    profile.mission || '',
  ]));
  if (!needles.size) return [];
  const haystack = new Set(tokenise([
    ...(change.related_terms || []),
    ...(change.topics || []),
    change.change?.headline || '',
    change.change?.summary || '',
    change.impact?.who_is_affected || '',
  ]));
  return [...needles].filter((token) => haystack.has(token));
}

function utcDay(value) {
  const text = String(value || '');
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (match) return Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const parsed = new Date(text);
  if (!Number.isFinite(parsed.getTime())) return NaN;
  return Date.UTC(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate());
}

function daysUntil(dateString, asOf) {
  if (!dateString) return null;
  const target = utcDay(dateString);
  const base = utcDay(asOf || new Date().toISOString());
  if (!Number.isFinite(target) || !Number.isFinite(base)) return null;
  return Math.round((target - base) / 86400000);
}

export function scoreChange(change, profile = {}, options = {}) {
  const changeTopics = arr(change.topics);
  const changeAudiences = arr(change.life_situations);
  const changeFamilies = arr(change.family);
  const changeJurisdictions = arr(change.jurisdictions);

  const topicHits = overlaps(profile.topics, changeTopics);
  const audienceHits = overlaps(profile.audiences, changeAudiences);
  const familyHits = overlaps(profile.families, changeFamilies);
  const jurisdictionHits = overlaps(profile.jurisdictions, changeJurisdictions);
  const semanticHits = keywordHits(change, profile);

  let score = 0;
  const reasons = [];

  if (topicHits.length) {
    score += Math.min(38, 22 + topicHits.length * 8);
    reasons.push(`Themen-Match: ${topicHits.join(', ')}`);
  }
  if (audienceHits.length) {
    score += Math.min(28, 16 + audienceHits.length * 7);
    reasons.push(`Zielgruppen-Match: ${audienceHits.join(', ')}`);
  }
  if (familyHits.length) {
    score += 18;
    reasons.push(`Watchdog-Match: ${familyHits.join(', ')}`);
  }
  if (jurisdictionHits.length) {
    score += 10;
    reasons.push(`Jurisdiktion: ${jurisdictionHits.join(', ')}`);
  }
  if (semanticHits.length) {
    score += Math.min(18, 6 + semanticHits.length * 3);
    reasons.push(`Mission/Service-Match: ${semanticHits.slice(0, 4).join(', ')}`);
  }

  const verification = norm(change?.evidence?.verification_status);
  if (verification === 'multi_source') {
    score += 10;
    reasons.push('Mehrquellen-Nachweis');
  } else if (verification === 'official_primary') {
    score += 9;
    reasons.push('Offizielle Primärquelle');
  } else if (change?.evidence?.source_count > 0) {
    score += 5;
    reasons.push('Quelle vorhanden');
  }

  if (change?.actionability?.action_available) {
    score += 7;
    reasons.push('Konkreter nächster Schritt verfügbar');
  }

  const remaining = daysUntil(change?.action_window?.deadline || change?.change?.deadline, options.asOf);
  if (remaining !== null && remaining >= 0) {
    if (remaining <= 7) {
      score += 15;
      reasons.push(`Zeitkritisch: ${remaining} Tage`);
    } else if (remaining <= 30) {
      score += 10;
      reasons.push(`Action Window: ${remaining} Tage`);
    } else if (remaining <= 90) {
      score += 4;
      reasons.push(`Frist in ${remaining} Tagen`);
    }
  }

  const relevanceHits = topicHits.length + audienceHits.length + familyHits.length + jurisdictionHits.length + semanticHits.length;
  if (!relevanceHits) score = Math.min(score, 18);

  return {
    score: Math.max(0, Math.min(100, score)),
    reasons,
    topicHits,
    audienceHits,
    familyHits,
    jurisdictionHits,
    semanticHits,
    daysRemaining: remaining,
  };
}

export function rankChanges(items = [], profile = {}, options = {}) {
  return items
    .map((change) => ({ change, ...scoreChange(change, profile, options) }))
    .sort((a, b) => b.score - a.score || (a.daysRemaining ?? 99999) - (b.daysRemaining ?? 99999) || String(b.change.observed_on).localeCompare(String(a.change.observed_on)));
}

export function buildUsefulnessReport({ profile = {}, judgments = {}, ranked = [], startedAt = null, finishedAt = null } = {}) {
  const entries = ranked
    .filter((row) => judgments[row.change.id])
    .map((row) => ({
      change_id: row.change.id,
      family: row.change.family || 'rights_money',
      headline: row.change.change?.headline || '',
      impact_score: row.score,
      days_remaining: row.daysRemaining ?? null,
      judgment: judgments[row.change.id],
      verification_status: row.change.evidence?.verification_status || 'UNKNOWN',
      source_count: Number(row.change.evidence?.source_count || 0),
      action_window_deadline: row.change.action_window?.deadline || row.change.change?.deadline || null,
      opportunity_type: row.change.opportunity?.type || null,
      programme_budget_eur: row.change.opportunity?.programme_budget_eur ?? null,
    }));

  const total = entries.length;
  const count = (field) => entries.filter((e) => e.judgment?.[field] === true).length;
  const useful = count('useful');
  const wouldHaveMissed = count('would_have_missed');
  const actionTaken = count('action_taken');
  const alreadyKnew = count('already_knew');
  const falsePositive = count('not_useful');
  const timeSensitiveUseful = entries.filter((e) => e.judgment?.useful === true && e.days_remaining !== null && e.days_remaining >= 0 && e.days_remaining <= 30).length;
  const fundingSignalsUseful = entries.filter((e) => e.judgment?.useful === true && e.opportunity_type === 'grant_call').length;

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
      families: profile.families || [],
      jurisdictions: profile.jurisdictions || [],
      services: profile.services || [],
      mission: profile.mission || '',
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
      time_sensitive_useful_items: timeSensitiveUseful,
      useful_funding_signals: fundingSignalsUseful,
      review_minutes: minutes,
    },
    proof: {
      useful_signal_observed: useful > 0,
      miss_prevention_observed: wouldHaveMissed > 0,
      actionability_observed: actionTaken > 0,
      time_sensitive_value_observed: timeSensitiveUseful > 0,
      paid_proof_candidate: total >= 3 && useful / total >= 0.6 && falsePositive / total <= 0.4,
    },
    truth_boundary: {
      estimated_hours_saved: null,
      guaranteed_roi: false,
      customer_value_eur: null,
      programme_budgets_are_not_customer_value: true,
      coverage_complete: false,
      note: 'This report measures observed usefulness judgments. It does not infer financial ROI, customer winnings, or completeness of coverage.',
    },
    entries,
  };
}
