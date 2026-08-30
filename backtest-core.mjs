export const BACKTEST_POLICY = Object.freeze({
  schemaVersion:'citizen-backtest/1.0',
  maxSignals:30,
  paidProofMinReviewed:5,
  paidProofMinSelfReportedMisses:2,
  noInferredMisses:true,
  noInferredRoi:true,
});

const clean=s=>String(s??'').toLowerCase().normalize('NFKD').replace(/[^a-z0-9äöüß]+/g,' ').trim();
const terms=s=>new Set(clean(s).split(/\s+/).filter(x=>x.length>2));
const intersect=(a,b)=>[...a].filter(x=>b.has(x));

export function profileTerms(profile={}){
  return terms([
    profile.name,profile.mission,
    ...(profile.topics||[]),...(profile.jurisdictions||[]),...(profile.audiences||[]),...(profile.services||[])
  ].join(' '));
}
export function recordTerms(item={}){
  return terms([
    item.headline,item.why_it_matters,item.family,
    ...(item.topics||[]),...(item.stakeholders||[])
  ].join(' '));
}
export function scoreBacktestRecord(profile,item){
  const p=profileTerms(profile),r=recordTerms(item); const hits=intersect(p,r);
  let score=hits.length*12;
  const topicHits=(item.topics||[]).filter(x=>p.has(clean(x))).length; score+=topicHits*18;
  if(item.deadline) score+=12;
  if(item.lead_days_at_detection!=null) score+=Math.min(18,Math.max(2,Math.round(item.lead_days_at_detection/5)));
  if(item.source_status==='OFFICIAL_PRIMARY') score+=8;
  else if(item.source_status==='MULTI_SOURCE') score+=6;
  if((item.sources||[]).length>=2) score+=4;
  return {score,hits:[...new Set(hits)].slice(0,8),relevant:score>=18};
}
export function runBacktest(profile,archive,{limit=BACKTEST_POLICY.maxSignals}={}){
  const ranked=(archive.items||[]).map(item=>({item,...scoreBacktestRecord(profile,item)}))
    .filter(x=>x.relevant).sort((a,b)=>b.score-a.score||a.item.first_seen.localeCompare(b.item.first_seen)).slice(0,limit);
  const lead=ranked.map(x=>x.item.lead_days_at_detection).filter(Number.isFinite).sort((a,b)=>a-b);
  const medianLead=lead.length?lead[Math.floor(lead.length/2)]:null;
  return {
    schema_version:BACKTEST_POLICY.schemaVersion,
    organisation:profile.name||'Custom organisation',
    evidence_window:archive.evidence_window,
    matched:ranked.length,
    time_sensitive:ranked.filter(x=>x.item.deadline).length,
    multi_source:ranked.filter(x=>(x.item.sources||[]).length>=2).length,
    median_lead_days:medianLead,
    inferred_misses:null,
    inferred_roi_eur:null,
    records:ranked,
    truth_boundary:{misses_require_human_judgment:true,roi_not_inferred:true,coverage_complete:false},
  };
}
export function summarizeJudgments(result,judgments={}){
  const rows=result.records.map(x=>judgments[x.item.id]).filter(Boolean);
  const count=k=>rows.filter(r=>r===k).length;
  const reviewed=rows.length, missed=count('missed'), known=count('known'), irrelevant=count('irrelevant');
  return {
    reviewed,self_reported_would_miss:missed,known_in_time:known,irrelevant,
    potential_pain:reviewed>=BACKTEST_POLICY.paidProofMinReviewed&&missed>=BACKTEST_POLICY.paidProofMinSelfReportedMisses,
    inferred_misses:null,inferred_roi_eur:null,
  };
}
