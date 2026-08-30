import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const ROOT = new URL('../', import.meta.url);
const DIGEST_DIR = new URL('../agent-digests/', import.meta.url);
const DAY = 86400000;
const TARGET_DAYS = 90;

const topicRules = [
  ['funding', /förder|funding|grant|ausschreibung|call for proposal|cerv/i],
  ['health', /gesundheit|patient|krankenhaus|pflege|notfall|medical|health/i],
  ['housing', /wohnen|miete|baugb|baugesetz|wärmeplanung|housing|tenant/i],
  ['social', /sozial|wohngeld|kinderzuschlag|elterngeld|bafög|rente|arbeitslos|benefit/i],
  ['labour', /arbeit|beschäftig|mindestlohn|tarif|gewerkschaft|labour|worker/i],
  ['digital', /digital|ki\b|künstliche intelligenz|ai act|data act|cloud|cyber|quantum|halbleiter/i],
  ['human_rights', /menschenrecht|flücht|asyl|migration|menschenhandel|victim|refugee/i],
  ['consumer', /verbrauch|finanz|bank|vertrag|consumer|sparer/i],
  ['climate', /klima|energie|umwelt|natur|wärme|energy|climate/i],
  ['democracy', /wahl|petition|anhörung|konsultation|bundestag|demokr|lobby|parlament/i],
  ['research', /forschung|wissenschaft|research|horizon/i],
];

const stakeholderMap = {
  funding: ['fundraising','ngo','research','municipality'],
  health: ['health','patient','ngo','public_affairs'],
  housing: ['housing','municipality','ngo','public_affairs'],
  social: ['social_advice','family','ngo','municipality'],
  labour: ['labour','public_affairs','ngo'],
  digital: ['digital','industry','public_affairs','research'],
  human_rights: ['human_rights','ngo','public_affairs'],
  consumer: ['consumer','ngo','public_affairs'],
  climate: ['climate','housing','ngo','public_affairs'],
  democracy: ['public_affairs','ngo','journalism'],
  research: ['research','fundraising','public_affairs'],
};

function dateFromFilename(name) {
  const m = name.match(/(20\d{2}-\d{2}-\d{2})/);
  return m?.[1] || null;
}
function normTitle(s) { return s.toLowerCase().replace(/\([^)]*\)/g,' ').replace(/[^a-z0-9äöüß]+/gi,' ').replace(/^\d+\s+/,'').trim(); }
function idFor(title) { return `arc_${createHash('sha256').update(normTitle(title)).digest('hex').slice(0,16)}`; }
function cleanUrl(s) { return s.replace(/[)>.,;`]+$/,''); }
function extractSources(text) { return [...new Set((text.match(/https?:\/\/[^\s)\]>]+/g)||[]).map(cleanUrl))]; }
function classify(text) {
  const topics = topicRules.filter(([,re])=>re.test(text)).map(([t])=>t);
  const stakeholders = [...new Set(topics.flatMap(t=>stakeholderMap[t]||[]))];
  return { topics, stakeholders };
}
function familyFor(file, text) {
  if (/consultation|anhörung|konsultation|petition|wahl/i.test(`${file} ${text}`)) return 'democracy_action_window';
  if (/funding|förder|grant|cerv|ausschreibung/i.test(text)) return 'funding_radar';
  if (/gericht|urteil|court|verfassungs/i.test(text)) return 'rights_courts';
  if (/lobby|interessenvertret/i.test(text)) return 'power_influence';
  if (/benefit|wohngeld|kinderzuschlag|elterngeld|bafög|sozialleistung/i.test(`${file} ${text}`)) return 'rights_money';
  return 'civic_change';
}
function parseSections(file, firstSeen, markdown) {
  const heading = /^##\s+(?!#)(.+)$/gm;
  const matches = [...markdown.matchAll(heading)];
  const out=[];
  for(let i=0;i<matches.length;i++){
    const rawTitle=matches[i][1].trim().replace(/^\d+\.\s*/, '');
    if (/bottom line|weiter beobachtet|so funktioniert|quellen|method|fazit|status/i.test(rawTitle)) continue;
    const start=matches[i].index + matches[i][0].length;
    const end=i+1<matches.length?matches[i+1].index:markdown.length;
    const body=markdown.slice(start,end).trim();
    const sources=extractSources(body);
    if(!sources.length || rawTitle.length<8) continue;
    const {topics,stakeholders}=classify(`${rawTitle}\n${body}`);
    if(!topics.length) continue;
    out.push({
      id:idFor(rawTitle), first_seen:firstSeen, last_seen:firstSeen,
      family:familyFor(file, `${rawTitle}\n${body}`), topics, stakeholders,
      headline:rawTitle, why_it_matters:body.replace(/\n+/g,' ').replace(/\*\*/g,'').slice(0,520),
      deadline:null, event_date:null, lead_days_at_detection:null,
      source_status:sources.length>=2?'MULTI_SOURCE':'SOURCE_BACKED', sources,
      archive_evidence:`agent-digests/${file}`, extraction_mode:'ARCHIVE_SECTION',
    });
  }
  return out;
}
function mergeItem(map,item){
  const key=normTitle(item.headline);
  const prev=map.get(key);
  if(!prev){map.set(key,item);return;}
  prev.first_seen = prev.first_seen < item.first_seen ? prev.first_seen : item.first_seen;
  prev.last_seen = prev.last_seen > item.last_seen ? prev.last_seen : item.last_seen;
  prev.sources=[...new Set([...prev.sources,...item.sources])];
  prev.source_status=prev.sources.length>=2?'MULTI_SOURCE':prev.source_status;
  prev.topics=[...new Set([...prev.topics,...item.topics])];
  prev.stakeholders=[...new Set([...prev.stakeholders,...item.stakeholders])];
  const evidence=[prev.archive_evidence,item.archive_evidence].flat().filter(Boolean);
  prev.archive_evidence=[...new Set(evidence)];
}

const files=(await readdir(DIGEST_DIR)).filter(f=>/\.md$/.test(f) && dateFromFilename(f));
const dates=files.map(dateFromFilename).filter(Boolean).sort();
const newest=dates.at(-1) || new Date().toISOString().slice(0,10);
const newestMs=Date.parse(`${newest}T00:00:00Z`);
const windowStartMs=newestMs-(TARGET_DAYS-1)*DAY;
const map=new Map();

for(const file of files){
  const d=dateFromFilename(file); const ms=Date.parse(`${d}T00:00:00Z`);
  if(ms<windowStartMs || ms>newestMs) continue;
  const md=await readFile(new URL(`../agent-digests/${file}`, import.meta.url),'utf8');
  for(const item of parseSections(file,d,md)) mergeItem(map,item);
}

// Preserve the curated replay records because they carry explicit deadlines and deterministic lead-time proof.
try{
  const curated=JSON.parse(await readFile(new URL('../replay-signals.json', import.meta.url),'utf8'));
  for(const item of curated.items||[]) mergeItem(map,{...item,last_seen:item.first_seen,extraction_mode:'CURATED_REPLAY'});
}catch{}

const items=[...map.values()].sort((a,b)=>a.first_seen.localeCompare(b.first_seen)||a.headline.localeCompare(b.headline));
const availableDates=items.map(x=>x.first_seen).sort();
const evidenceStart=availableDates[0]||null;
const evidenceEnd=availableDates.at(-1)||null;
const evidenceDays=evidenceStart&&evidenceEnd?Math.round((Date.parse(`${evidenceEnd}T00:00:00Z`)-Date.parse(`${evidenceStart}T00:00:00Z`))/DAY)+1:0;
const archive={
  schema_version:'citizen-operational-awareness-archive/1.0', generated_on:newest,
  target_window_days:TARGET_DAYS, evidence_window:{start:evidenceStart,end:evidenceEnd,days:evidenceDays},
  coverage_complete:false,
  truth_boundary:{no_inferred_misses:true,no_inferred_roi:true,no_claim_of_90_day_coverage:evidenceDays<TARGET_DAYS,claim:'Archive records prove what Citizen Agents stored and when. Relevance is algorithmic; a missed signal is only counted after a human self-reports it.'},
  stats:{records:items.length,source_backed:items.filter(x=>x.sources?.length).length,multi_source:items.filter(x=>x.sources?.length>=2).length},
  items,
};
await writeFile(new URL('../backtest-archive.json', import.meta.url),JSON.stringify(archive,null,2)+'\n');
console.log(JSON.stringify(archive.stats));
