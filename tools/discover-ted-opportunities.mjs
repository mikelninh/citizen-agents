import fs from 'node:fs';

const ENDPOINT='https://api.ted.europa.eu/v3/notices/search';
const yyyyMMdd=d=>d.toISOString().slice(0,10).replaceAll('-','');
const now=new Date();const since=new Date(now.getTime()-30*86400000);
const query=process.env.TED_QUERY || `((FT~"artificial intelligence") OR (FT~"künstliche Intelligenz") OR (FT~"agentic AI") OR (FT~LLM) OR (FT~"machine learning")) AND buyer-country=DEU AND PD>=${yyyyMMdd(since)} SORT BY publication-date DESC`;
const fields=['publication-number','notice-title','buyer-name','buyer-country','publication-date','deadline','classification-cpv'];

const scalar=v=>Array.isArray(v)?v[0]:v;
const multilingual=v=>{
  if(v==null)return '';
  if(typeof v==='string')return v;
  if(Array.isArray(v))return String(v[0]||'');
  if(typeof v==='object'){
    const preferred=['deu','ger','eng','en'];
    for(const k of preferred){if(v[k])return scalar(v[k]);}
    const first=Object.values(v).find(Boolean);return scalar(first)||'';
  }
  return String(v);
};
const text=o=>`${multilingual(o['notice-title'])} ${multilingual(o['buyer-name'])}`.toLowerCase();
const productMatches=o=>{
  const s=text(o);const out=[];
  if(/agent|llm|künstliche intelligenz|artificial intelligence/.test(s))out.push('Digital Worker Factory / OpsPilot','SafeTrace / Master Proof');
  if(/sozial|wohngeld|grundsicherung|leistung/.test(s))out.push('CARE / Public Service systems');
  if(/dokument|document|prüfung|antrag/.test(s))out.push('PrüfPilot');
  if(/recht|legal|gesetz|compliance/.test(s))out.push('GitLaw');
  if(/gesund|health|klin|kranken/.test(s))out.push('CareOS');
  return [...new Set(out)];
};
const fitScore=o=>{
  const s=text(o);let score=50;
  if(/agentic|agenten|agent/.test(s))score+=20;
  if(/llm|künstliche intelligenz|artificial intelligence/.test(s))score+=12;
  if(/sozial|wohngeld|grundsicherung/.test(s))score+=15;
  if(/dokument|document|prüfung|antrag/.test(s))score+=8;
  if(/recht|compliance|sicherheit|security/.test(s))score+=8;
  return Math.min(95,score);
};
const noticeUrl=n=>`https://ted.europa.eu/de/notice/-/detail/${encodeURIComponent(n)}`;

async function main(){
  const body={query,fields,page:1,limit:100,scope:'ACTIVE',checkQuerySyntax:false,paginationMode:'PAGE_NUMBER'};
  const res=await fetch(ENDPOINT,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  if(!res.ok)throw new Error(`TED ${res.status}: ${await res.text()}`);
  const payload=await res.json();const notices=payload.notices||payload.results||[];
  const items=notices.map(n=>{
    const pub=String(scalar(n['publication-number'])||n.publicationNumber||'').trim();const title=multilingual(n['notice-title']||n.noticeTitle);const buyer=multilingual(n['buyer-name']||n.buyerName);const deadline=scalar(n.deadline||n['deadline-receipt-tender-date-lot'])||null;const products=productMatches(n);
    return {id:`ted_${pub.replace(/[^0-9a-z]+/gi,'_')}`,type:'tender_candidate',headline:title||`TED ${pub}`,deadline,buyer_or_program:buyer||'Public buyer',potential:'Public procurement opportunity; value must be checked in the original notice.',fit_score:fitScore(n),product_matches:products,why_fit:products.length?`Keyword-level discovery matched ${products.join(', ')}. Full requirements still need review.`:'AI-related German procurement candidate requiring manual qualification.',blockers:['Full procurement documents not yet reviewed','Formal suitability, references and value not yet established'],action_pack:['Open the official TED notice','Check scope, deadline, eligibility and references','Run proof matcher and decide DIRECT_BID_REVIEW vs PARTNER_FIRST','Only after approval: prepare submission or partner outreach'],source_status:'OFFICIAL_TED_API',sources:pub?[noticeUrl(pub)]:[],ted:{publication_number:pub,publication_date:scalar(n['publication-date'])||null,cpv:n['classification-cpv']||null}};
  }).filter(x=>x.sources.length&&x.headline);
  const output={schema_version:'citizen-ted-discovery/1.0',generated_at:new Date().toISOString(),query,coverage_complete:false,items,truth_boundary:'Automated keyword discovery from official TED Search API. A candidate is not a qualified opportunity until requirements are reviewed.'};
  fs.writeFileSync('discovered-ted-opportunities.json',JSON.stringify(output,null,2)+'\n');
  console.log(`TED discovery: ${items.length} active candidates.`);
}
main().catch(err=>{console.error(err.stack||err);process.exit(1)});
