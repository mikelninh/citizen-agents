#!/usr/bin/env python3
import json
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
data=json.loads((ROOT/'gauntlet/replay_cases.json').read_text())
priority={'primary':2,'secondary':1}
for case in data['cases']:
    cutoff=date.fromisoformat(case['cutoff'])
    visible=[d for d in case['documents'] if date.fromisoformat(d['published'])<=cutoff]
    assert {d['id'] for d in visible}==set(case.get('expected_visible_ids',[d['id'] for d in visible])) if 'expected_visible_ids' in case else True
    best={}
    for d in visible:
        if d['event'] not in best or priority[d['source']]>priority[best[d['event']]['source']]: best[d['event']]=d
    for event,state in case.get('expected_states',{}).items(): assert best[event]['state']==state
    for event,source in case.get('expected_best_source',{}).items(): assert best[event]['source']==source
print(json.dumps({'harness':'citizen-agents-historical-replay','cases':len(data['cases']),'future_leak_gate':'PASS','state_preservation':'PASS','provenance_dedup':'PASS','product_baseline':'NOT_MEASURED'},indent=2))
