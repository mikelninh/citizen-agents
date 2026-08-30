import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runBacktest, summarizeJudgments } from '../backtest-core.mjs';

const archive=JSON.parse(await readFile(new URL('../backtest-archive.json',import.meta.url),'utf8'));
const examples=JSON.parse(await readFile(new URL('../example-organisations.json',import.meta.url),'utf8'));
const delivery=JSON.parse(await readFile(new URL('../delivery-contract.json',import.meta.url),'utf8'));
const html=await readFile(new URL('../organisation-backtest.html',import.meta.url),'utf8');

test('rolling archive is evidence-backed without pretending 90-day completeness',()=>{
  assert.equal(archive.target_window_days,90);
  assert.equal(archive.coverage_complete,false);
  assert.equal(archive.truth_boundary.no_inferred_misses,true);
  assert.equal(archive.truth_boundary.no_inferred_roi,true);
  assert.ok(archive.items.length>=7);
  for(const item of archive.items){
    assert.ok(item.first_seen);
    assert.ok(item.headline);
    assert.ok(Array.isArray(item.sources)&&item.sources.length>=1);
    assert.ok(item.sources.every(x=>x.startsWith('http')));
  }
});

test('public example organisations never assert a miss',()=>{
  assert.ok(examples.organisations.length>=4);
  for(const org of examples.organisations){
    assert.equal(org.miss_status,'UNKNOWN_UNTIL_REVIEWED');
    assert.ok(org.public_profile_source.startsWith('https://'));
  }
});

test('backtest can rank a profile but cannot infer missed opportunity or ROI',()=>{
  const org=examples.organisations.find(x=>x.id==='bitkom');
  const result=runBacktest(org,archive,{limit:12});
  assert.ok(result.matched>=1);
  assert.equal(result.inferred_misses,null);
  assert.equal(result.inferred_roi_eur,null);
  const ids=result.records.slice(0,5).map(x=>x.item.id);
  const judgments=Object.fromEntries(ids.map((id,i)=>[id,i<2?'missed':'known']));
  const summary=summarizeJudgments(result,judgments);
  assert.equal(summary.self_reported_would_miss,2);
  assert.equal(summary.inferred_misses,null);
  assert.equal(summary.inferred_roi_eur,null);
});

test('zero setup claim is limited to channels that actually work without account connection',()=>{
  assert.deepEqual(delivery.truth_boundary.zero_setup_claim_only_for,['web','rss','api']);
  const x=delivery.channels.find(c=>c.id==='x');
  const slack=delivery.channels.find(c=>c.id==='slack');
  assert.match(x.status,/POLICY_GATED/);
  assert.match(slack.setup,/OAUTH/);
  assert.equal(delivery.truth_boundary.hosted_push_sla_claimed,false);
});

test('self-service UI makes pain self-assessed and shareable',()=>{
  assert.match(html,/Operational Awareness Backtest/);
  assert.match(html,/hätten wir wohl verpasst/);
  assert.match(html,/Kolleg:in challengen/);
  assert.match(html,/Kein erfundener ROI/);
  assert.match(html,/keine 90-Tage-Vollständigkeit/);
});
