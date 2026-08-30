import fs from 'node:fs';
import path from 'node:path';
import {qualifyOpportunity,actionPack,normalizePipelineRecord} from '../opportunity-core.mjs';

const root = process.cwd();
const read = file => JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const writeJson = (file,data) => {
  const out = path.join(root,file); fs.mkdirSync(path.dirname(out),{recursive:true});
  fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');
};

const profile = read('self-opportunity-profile.json');
const catalog = read('proof-catalog.json');
const opportunities = read('self-opportunities.json');
const pipeline = read('revenue-pipeline.json');
const now = new Date();
const pipelineById = new Map((pipeline.records||[]).map(x=>[x.opportunity_id,normalizePipelineRecord(x)]));

const items = (opportunities.items||[]).map(opportunity => {
  const qualification = qualifyOpportunity(profile,catalog,opportunity,now);
  const pack = actionPack(opportunity,qualification);
  const pipelineRecord = pipelineById.get(opportunity.id) || normalizePipelineRecord({opportunity_id:opportunity.id,status:'FOUND',decision:'PENDING'});
  return {...opportunity,qualification,action_pack_v1:pack,pipeline:pipelineRecord};
}).sort((a,b)=>{
  const ax=a.qualification.deadline.days, bx=b.qualification.deadline.days;
  const aExpired=ax!=null&&ax<0, bExpired=bx!=null&&bx<0;
  if(aExpired!==bExpired)return aExpired?1:-1;
  return b.qualification.qualification_score-a.qualification.qualification_score || (ax??9999)-(bx??9999);
});

const open = items.filter(x=>x.qualification.deadline.state!=='EXPIRED');
const metrics = {
  scanned:items.length,
  open:open.length,
  qualified:open.filter(x=>x.qualification.qualified).length,
  action_ready:items.filter(x=>['ACTION_READY','APPROVED','CONTACTED','REPLIED','PROPOSAL'].includes(x.pipeline.status)).length,
  won:items.filter(x=>x.pipeline.status==='WON').length,
  observed_revenue_eur:items.reduce((sum,x)=>sum+(x.pipeline.outcome_revenue_eur||0),0),
  expired_blind_spot_candidates:items.filter(x=>x.qualification.deadline.state==='EXPIRED').length
};

const api = {
  schema_version:'citizen-founder-opportunity-api/1.0',
  generated_at:now.toISOString(),
  profile:{name:profile.name,mission:profile.mission,revenue_goals:profile.revenue_goals},
  metrics,
  items,
  truth_boundary:{
    coverage_complete:false,
    qualification_is_not_formal_eligibility:true,
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
  `Open: **${metrics.open}** · Qualified: **${metrics.qualified}** · Won: **${metrics.won}** · Observed revenue: **€${metrics.observed_revenue_eur.toLocaleString('en-US')}**`,'',
  '> Revenue stays €0 until a WON record has award/contract/payment evidence.',''
];
for(const x of items.slice(0,12)){
  lines.push(`## ${x.headline}`,'',`**Score:** ${x.qualification.qualification_score}/100 · **Route:** ${x.qualification.route} · **${urgency(x)}** · **Pipeline:** ${x.pipeline.status}`,'',`**Why fit:** ${x.why_fit}`,'',`**Best proof:** ${x.qualification.proof_matches[0]?.name||'No strong proof match yet'}`,'',`**Next action:** ${x.pipeline.next_action||x.action_pack_v1.next_action}`,'',`**Approval:** required before external action`,'');
}
fs.mkdirSync(path.join(root,'agent-digests'),{recursive:true});
fs.writeFileSync(path.join(root,'agent-digests','founder-opportunity-digest.md'),lines.join('\n')+'\n');
console.log(`Founder Opportunity API built: ${metrics.open} open, ${metrics.qualified} qualified, €${metrics.observed_revenue_eur} observed revenue.`);
