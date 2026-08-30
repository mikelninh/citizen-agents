import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const read = (p) => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const write = (p, value) => {
  const file = path.join(root, p);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, typeof value === 'string' ? value : `${JSON.stringify(value, null, 2)}\n`);
};

const democracy = read('democracy-signals.json');
const rights = read('api/v1/changes.json');
const registry = read('watchdog-registry.json');

function rightSignal(change) {
  return {
    ...change,
    family: 'rights_money',
    jurisdictions: change.jurisdictions || ['DE'],
    related_terms: [...(change.related_terms || []), ...(change.topics || []), change.impact?.who_is_affected || ''],
  };
}

const items = [
  ...(democracy.items || []),
  ...(rights.items || []).map(rightSignal),
];

const familyCounts = Object.fromEntries(registry.families.map((family) => [family.id, items.filter((item) => item.family === family.id).length]));
const withDeadline = items.filter((item) => item.action_window?.deadline || item.change?.deadline).length;
const withAction = items.filter((item) => item.actionability?.action_available).length;
const withSources = items.filter((item) => Number(item.evidence?.source_count || 0) > 0).length;

const collection = {
  schema_version: 'citizen-democracy-radar/1.0',
  generated_on: democracy.generated_on,
  count: items.length,
  coverage_complete: false,
  families: familyCounts,
  health: {
    source_backed_rate: items.length ? Number((withSources / items.length).toFixed(3)) : null,
    actionable_rate: items.length ? Number((withAction / items.length).toFixed(3)) : null,
    action_window_items: withDeadline,
  },
  truth_boundary: {
    exhaustive_monitoring_claimed: false,
    financial_roi_claimed: false,
    note: 'The combined radar includes automated Rights & Money records plus curated official-source democracy signals. Coverage is not yet claimed complete.',
  },
  items,
};

write('api/v1/radar.json', collection);
write('api/v1/watchdogs.json', registry);
write('api/v1/radar.ndjson', `${items.map((item) => JSON.stringify(item)).join('\n')}\n`);
console.log(`Built Democracy Radar: ${items.length} records across ${Object.keys(familyCounts).length} watchdog families.`);
