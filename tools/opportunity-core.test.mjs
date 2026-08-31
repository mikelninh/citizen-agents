import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {deadlineState,matchProofs,chooseRoute,qualifyOpportunity,normalizePipelineRecord} from '../opportunity-core.mjs';

const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const profile=read('self-opportunity-profile.json');
const catalog=read('proof-catalog.json');
const opportunities=read('self-opportunities.json');
const byId=id=>opportunities.items.find(x=>x.id===id);
const fixedNow=new Date('2026-08-30T18:00:00+02:00');

test('deadline state is deterministic at the dogfood snapshot',()=>{
  assert.equal(deadlineState(byId('opp_dataport_social_benefits_2026').deadline,fixedNow).state,'SOON');
  assert.equal(deadlineState(byId('missed_agentic_ai_hub_round2').deadline,fixedNow).state,'EXPIRED');
});

test('CARE is a leading proof for Dataport social-benefits opportunity',()=>{
  const matches=matchProofs(catalog,byId('opp_dataport_social_benefits_2026'));
  assert.ok(matches.slice(0,3).some(x=>x.proof_id==='care-public-service'));
});

test('partner-first route is selected for enterprise tender with reference blockers',()=>{
  const opp=byId('opp_dataport_social_benefits_2026');
  const matches=matchProofs(catalog,opp);
  assert.equal(chooseRoute(opp,matches),'SUBCONTRACT_OR_PARTNER');
});

test('CERV is routed to consortium partner, never solo application',()=>{
  const opp=byId('opp_cerv_charter_2026');
  assert.equal(chooseRoute(opp,matchProofs(catalog,opp)),'CONSORTIUM_PARTNER');
});

test('qualification never fabricates revenue',()=>{
  const q=qualifyOpportunity(profile,catalog,byId('opp_bsi_praki_2026'),fixedNow);
  assert.equal(q.revenue_eur,null);
  assert.equal(q.revenue_claimed,false);
  assert.equal(q.truth_boundary.programme_or_tender_value_is_not_revenue,true);
});

test('pipeline strips revenue unless status is WON',()=>{
  assert.equal(normalizePipelineRecord({status:'PROPOSAL',outcome_revenue_eur:50000}).outcome_revenue_eur,null);
  assert.equal(normalizePipelineRecord({status:'WON',outcome_revenue_eur:50000}).outcome_revenue_eur,50000);
});

test('expired opportunities cannot be qualified live opportunities',()=>{
  const q=qualifyOpportunity(profile,catalog,byId('missed_agentic_ai_hub_round2'),fixedNow);
  assert.equal(q.qualified,false);
  assert.equal(q.route,'MONITOR_NEXT_ROUND');
});

test('founder control center keeps decision, revenue, proof and health layers in one surface',()=>{
  const html=fs.readFileSync('control-center.html','utf8');
  for(const marker of ['Founder Control Center','Today · decision first','Revenue pulse','Opportunity radar','Decision queue','Revenue pipeline','Proof inventory','Partner leverage','Coverage & system health']){
    assert.ok(html.includes(marker),`missing control-center marker: ${marker}`);
  }
  assert.ok(html.includes("citizen-revenue-os/v1"),'control center must share Revenue OS local CRM state');
  assert.ok(html.includes('Observed revenue'),'control center must preserve revenue truth boundary');
  assert.ok(html.includes('External action requires approval'),'control center must preserve approval boundary');
});
