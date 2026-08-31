import fs from 'node:fs';
import path from 'node:path';
import {qualifyOpportunity,actionPack,normalizePipelineRecord} from '../opportunity-core.mjs';

const root = process.cwd();
const read = file => JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const writeJson = (file,data) => {
  const out = path.join(root,file); fs.mkdirSync(path.dirname(out),{recursive:true});
  fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');
};
const norm=s=>String(s??'').toLowerCase().normalize('NFKD').replace(/[^a-z0-9äöüß]+/g,' ').trim();
const tokens=s=>new Set(norm(s).split(/\s+/).filter(x=>x.length>3));
const overlap=(a,b)=>{const A=tokens(a),B=tokens(b);if(!A.size||!B.size)return 0;return [...A].filter(x=>B.has(x)).length/Math.min(A.size,B.size)};

const profile = read('self-opportunity-profile.json');
const catalog = read('proof-catalog.json');
const opportunities = read('self-opportunities.json');
const tedDiscovery = read('discovered-ted-opportunities.json');
const pipeline = read('revenue-pipeline.json');
const partnerMap = read('partner-map.json');
const now = new Date();
const pipelineById = new Map((pipeline.records||[]).map(x=>[x.opportunity_id,normalizePipelineRecord(x)]));
const partnersFor = id => (partnerMap.candidates||[])
  .filter(x=>(x.fit_for||[]).includes(id))
  .map(x=>({id:x.id,name:x.name,why_candidate:x.why_candidate,our_wedge:x.our_wedge,qualification_questions:x.qualification_questions,sources:x.sources}));

const curated=[...(opportunities.items||[])];
const discovered=(tedDiscovery.items||[]).filter(candidate=>!curated.some(existing=>norm(existing.buyer_or_program)===norm(candidate.buyer_or_program)&&overlap(existing.headline,candidate.headline)>=.55));
const sourceItems=[...curated,...discovered];
const items = sourceItems.map(opportunity => {
  const qualification = qualifyOpportunity(profile,catalog,opportunity,now);
  const pack = actionPack(opportunity,qualification);
  const pipelineRecord = pipelineById.get(opportunity.id) || normalizePipelineRecord({opportunity_id:opportunity.id,status:'FOUND',decision:'PENDING',next_action:pack.next_action,outcome_revenue_eur:null,outcome_evidence:null});
  return {...opportunity,discovery_origin:curated.some(x=>x.id===opportunity.id)?'CURATED':'TED_AUTOMATED',qualification,action_pack_v1:pack,candidate_partners:partnersFor(opportunity.id),pipeline:pipelineRecord};
}).sort((a,b)=>{
  const ax=a.qualification.deadline.days, bx=b.qualification.deadline.days;
  const aExpired=ax!=null&&ax<0, bExpired=bx!=null&&bx<0;
  if(aExpired!==bExpired)return aExpired?1:-1;
  return b.qualification.qualification_score-a.qualification.qualification_score || (ax??9999)-(bx??9999);
});

const open = items.filter(x=>x.qualification.deadline.state!=='EXPIRED');
const metrics = {
  scanned:items.length,
  curated:curated.length,
  automated_new_candidates:discovered.length,
  open:open.length,
  qualified:open.filter(x=>x.qualification.qualified).length,
  partner_route:open.filter(x=>['PARTNER_FIRST','SUBCONTRACT_OR_PARTNER','CONSORTIUM_PARTNER','PARTNER'].includes(x.qualification.route)).length,
  action_ready:items.filter(x=>['ACTION_READY','APPROVED','CONTACTED','REPLIED','PROPOSAL'].includes(x.pipeline.status)).length,
  won:items.filter(x=>x.pipeline.status==='WON').length,
  observed_revenue_eur:items.reduce((sum,x)=>sum+(x.pipeline.outcome_revenue_eur||0),0),
  expired_blind_spot_candidates:items.filter(x=>x.qualification.deadline.state==='EXPIRED').length
};

const api = {
  schema_version:'citizen-founder-opportunity-api/1.0',
  generated_at:now.toISOString(),
  discovery:{ted_generated_at:tedDiscovery.generated_at,ted_query:tedDiscovery.query},
  profile:{name:profile.name,mission:profile.mission,revenue_goals:profile.revenue_goals},
  metrics,
  items,
  truth_boundary:{
    coverage_complete:false,
    automated_discovery_is_candidate_generation_not_eligibility:true,
    qualification_is_not_formal_eligibility:true,
    candidate_partner_is_not_bidder_claim:true,
    pipeline_value_is_not_revenue:true,
    revenue_requires_won_status_and_evidence:true,
    external_actions_require_human_approval:true
  }
};
writeJson('api/v1/founder-opportunities.json',api);

const urgency = x => x.qualification.deadline.days==null?'no deadline':x.qualification.deadline.days<0?`expired ${Math.abs(x.qualification.deadline.days)}d ago`:`${x.qualification.deadline.days}d left`;
const lines = [
  '# Founder Opportunity Digest','',
  `Generated: ${now.toISOString()}`,'',
  `Open: **${metrics.open}** · Qualified: **${metrics.qualified}** · Automated new: **${metrics.automated_new_candidates}** · Partner-route: **${metrics.partner_route}** · Won: **${metrics.won}** · Observed revenue: **€${metrics.observed_revenue_eur.toLocaleString('en-US')}**`,'',
  '> Revenue stays €0 until a WON record has award/contract/payment evidence. Automated TED hits are candidates until requirements are reviewed. Candidate partners are leads to qualify, not claims that they will bid.',''
];
for(const x of items.slice(0,15)){
  const partner = x.candidate_partners[0]?.name;
  lines.push(`## ${x.headline}`,'',`**Origin:** ${x.discovery_origin} · **Score:** ${x.qualification.qualification_score}/100 · **Route:** ${x.qualification.route} · **${urgency(x)}** · **Pipeline:** ${x.pipeline.status}`,'',`**Why fit:** ${x.why_fit}`,'',`**Best proof:** ${x.qualification.proof_matches[0]?.name||'No strong proof match yet'}`,partner?`**First candidate partner to qualify:** ${partner}`:'','',`**Next action:** ${x.pipeline.next_action||x.action_pack_v1.next_action}`,'',`**Approval:** required before external action`,'');
}
fs.mkdirSync(path.join(root,'agent-digests'),{recursive:true});
fs.writeFileSync(path.join(root,'agent-digests','founder-opportunity-digest.md'),lines.filter(Boolean).join('\n')+'\n');
console.log(`Founder Opportunity API built: ${metrics.open} open, ${metrics.qualified} qualified, ${metrics.automated_new_candidates} automated candidates, €${metrics.observed_revenue_eur} observed revenue.`);
