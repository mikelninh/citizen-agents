export const PIPELINE_STATES = Object.freeze([
  'FOUND','QUALIFIED','ACTION_READY','APPROVED','CONTACTED','REPLIED','PROPOSAL','WON','LOST','MONITOR'
]);

const clean = value => String(value ?? '')
  .toLowerCase()
  .normalize('NFKD')
  .replace(/[^a-z0-9äöüß]+/g,' ')
  .trim();
const terms = value => new Set(clean(value).split(/\s+/).filter(x => x.length > 2));
const intersection = (a,b) => [...a].filter(x => b.has(x));

export function deadlineState(deadline, now = new Date()) {
  if (!deadline) return {state:'NO_DEADLINE',days:null};
  const target = new Date(deadline);
  if (Number.isNaN(target.getTime())) return {state:'INVALID_DEADLINE',days:null};
  const days = Math.ceil((target.getTime() - now.getTime()) / 86400000);
  if (days < 0) return {state:'EXPIRED',days};
  if (days <= 3) return {state:'CRITICAL',days};
  if (days <= 7) return {state:'URGENT',days};
  if (days <= 14) return {state:'SOON',days};
  return {state:'OPEN',days};
}

export function scoreProofMatch(proof, opportunity) {
  const explicit = new Set((opportunity.product_matches || []).map(clean));
  const proofName = clean(proof.name);
  const explicitHit = explicit.has(proofName) || [...explicit].some(x => x.includes(proofName) || proofName.includes(x));
  const oppText = terms([
    opportunity.headline,
    opportunity.why_fit,
    opportunity.potential,
    ...(opportunity.needs || []),
    ...(opportunity.action_pack || [])
  ].join(' '));
  const proofText = terms([
    proof.name,
    ...(proof.capabilities || []),
    ...(proof.domains || [])
  ].join(' '));
  const hits = intersection(proofText, oppText);
  let score = Math.min(60, hits.length * 8);
  if (explicitHit) score += 35;
  if (String(proof.readiness || '').startsWith('WORKING')) score += 5;
  return {proof_id:proof.id,name:proof.name,score:Math.min(100,score),hits:[...new Set(hits)].slice(0,10),readiness:proof.readiness,evidence:proof.evidence || [],limitations:proof.limitations || []};
}

export function matchProofs(catalog, opportunity, {limit=4}={}) {
  return (catalog.proofs || [])
    .map(proof => scoreProofMatch(proof, opportunity))
    .filter(x => x.score > 0)
    .sort((a,b) => b.score - a.score || a.name.localeCompare(b.name))
    .slice(0,limit);
}

export function chooseRoute(opportunity, proofMatches=[]) {
  const type = clean(opportunity.type);
  const blockers = clean((opportunity.blockers || []).join(' '));
  const bestProof = proofMatches[0]?.score || 0;
  if (type.includes('missed')) return 'MONITOR_NEXT_ROUND';
  if (type.includes('grant partnership')) return 'CONSORTIUM_PARTNER';
  if (type.includes('tender partner')) return 'SUBCONTRACT_OR_PARTNER';
  if (type === 'tender') {
    if (/reference|partner|consortium|suitability|eignung/.test(blockers) || bestProof < 75) return 'PARTNER_FIRST';
    return 'DIRECT_BID_REVIEW';
  }
  if (type.includes('accelerator') || type.includes('grant accelerator')) return 'DIRECT_APPLICATION';
  if (type.includes('partnership')) return 'PARTNER';
  if (type.includes('customer')) return 'DIRECT_SALE';
  return 'REVIEW';
}

function sourceConfidence(sourceStatus='') {
  const s = clean(sourceStatus);
  if (s.includes('official')) return 100;
  if (s.includes('public procurement')) return 90;
  return 65;
}

function urgencyScore(deadline, now) {
  const {state} = deadlineState(deadline, now);
  return ({CRITICAL:100,URGENT:90,SOON:75,OPEN:55,NO_DEADLINE:40,EXPIRED:0,INVALID_DEADLINE:0})[state] ?? 0;
}

export function qualifyOpportunity(profile, catalog, opportunity, now=new Date()) {
  const proofs = matchProofs(catalog, opportunity);
  const proofScore = proofs[0]?.score || 0;
  const fit = Math.max(0,Math.min(100,Number(opportunity.fit_score || 0)));
  const source = sourceConfidence(opportunity.source_status);
  const urgency = urgencyScore(opportunity.deadline, now);
  const score = Math.round(fit * .55 + proofScore * .25 + source * .12 + urgency * .08);
  const route = chooseRoute(opportunity, proofs);
  const deadline = deadlineState(opportunity.deadline, now);
  const qualified = deadline.state !== 'EXPIRED' && score >= 70;
  return {
    opportunity_id: opportunity.id,
    qualification_score: score,
    qualified,
    route,
    deadline,
    proof_matches: proofs,
    revenue_eur: null,
    revenue_claimed: false,
    truth_boundary: {
      fit_is_not_formal_eligibility: true,
      programme_or_tender_value_is_not_revenue: true,
      external_action_requires_human_approval: true
    }
  };
}

export function actionPack(opportunity, qualification) {
  const first = opportunity.action_pack?.[0] || 'Review the source and decide whether to pursue.';
  return {
    schema_version:'citizen-opportunity-action-pack/1.0',
    opportunity_id:opportunity.id,
    headline:opportunity.headline,
    route:qualification.route,
    qualification_score:qualification.qualification_score,
    deadline:opportunity.deadline || null,
    buyer_or_program:opportunity.buyer_or_program || null,
    why_now:qualification.deadline.state === 'CRITICAL' ? 'Deadline is within three days.' : qualification.deadline.state === 'URGENT' ? 'Deadline is within seven days.' : qualification.deadline.state === 'SOON' ? 'Deadline is within fourteen days.' : 'Opportunity is open.',
    matching_proofs:qualification.proof_matches.map(x=>({id:x.proof_id,name:x.name,score:x.score,evidence:x.evidence,limitations:x.limitations})),
    blockers:opportunity.blockers || [],
    steps:opportunity.action_pack || [],
    next_action:first,
    approval_gate:{required:true,reason:'Any external submission, outreach, bid or commitment is consequential.'},
    revenue_eur:null,
    truth_boundary:'No revenue is recorded until a contract, award or payment is evidenced.'
  };
}

export function normalizePipelineRecord(record={}) {
  const status = PIPELINE_STATES.includes(record.status) ? record.status : 'FOUND';
  const revenue = status === 'WON' && Number(record.outcome_revenue_eur) > 0 ? Number(record.outcome_revenue_eur) : null;
  return {...record,status,outcome_revenue_eur:revenue};
}
