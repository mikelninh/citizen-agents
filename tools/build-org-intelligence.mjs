import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '..')
const apiDir = path.join(root, 'api', 'v1')

export function stableChangeId(item = {}) {
  const headline = String(item.headline || item?.de?.headline || '').trim()
  const firstSource = Array.isArray(item.sources) ? String(item.sources[0] || '') : ''
  return `chg_${createHash('sha256').update(`${headline}|${firstSource}`).digest('hex').slice(0, 16)}`
}

function cleanList(value) {
  return Array.isArray(value) ? [...new Set(value.map(v => String(v).trim()).filter(Boolean))] : []
}

function verificationStatus(sources) {
  if (sources.length >= 2) return 'MULTI_SOURCE'
  if (sources.length === 1) return 'SOURCE_BACKED'
  return 'UNVERIFIED'
}

export function normalizeChange(item = {}, feed = {}) {
  const sources = cleanList(item.sources)
  const headline = String(item.headline || item?.de?.headline || '').trim()
  const whatChanged = String(item.what_changed || item?.de?.what_changed || '').trim()
  const effective = String(item.effective || item?.de?.effective || '').trim()
  const deadline = String(item.deadline || item?.de?.deadline || '').trim()
  const affected = String(item.who_affected || item?.de?.who_affected || '').trim()
  const citizenTip = String(item.citizen_tip || item?.de?.citizen_tip || '').trim()
  const hasRecommendedAction = citizenTip.length > 0

  return {
    schema_version: 'citizen-intelligence/1.0',
    id: stableChangeId(item),
    observed_on: String(item.watchdog || feed.date || feed.generated || ''),
    topics: cleanList(item.tags),
    life_situations: cleanList(item.life),
    change: {
      headline,
      summary: whatChanged,
      effective,
      deadline,
    },
    impact: {
      who_is_affected: affected,
      criticality: 'UNASSESSED',
    },
    actionability: {
      recommended_action: citizenTip,
      action_available: hasRecommendedAction,
      authority: {
        information_read: 'ALLOW',
        external_or_consequential_action: hasRecommendedAction ? 'APPROVAL' : 'NOT_APPLICABLE',
        rule: 'Citizen Agents may suggest what to review. OCN/Company 01 or the consuming organisation decides whether an agent may actually act.',
      },
    },
    evidence: {
      verification_status: verificationStatus(sources),
      source_count: sources.length,
      sources,
    },
    provenance: {
      watchdog: String(item.watchdog || ''),
      source_feed: 'breakfast-feed.json',
      generated_feed_date: String(feed.generated || feed.date || ''),
    },
  }
}

export function buildIntelligence(feed = {}) {
  const items = Array.isArray(feed.items) ? feed.items.map(item => normalizeChange(item, feed)) : []
  const withSources = items.filter(x => x.evidence.source_count > 0).length
  const multiSource = items.filter(x => x.evidence.verification_status === 'MULTI_SOURCE').length
  const withAction = items.filter(x => x.actionability.action_available).length
  return {
    schema_version: 'citizen-intelligence-collection/1.0',
    generated_from: String(feed.generated || feed.date || ''),
    count: items.length,
    items,
    health: {
      item_count: items.length,
      items_with_sources: withSources,
      source_coverage_pct: items.length ? Number(((withSources / items.length) * 100).toFixed(1)) : 0,
      multi_source_pct: items.length ? Number(((multiSource / items.length) * 100).toFixed(1)) : 0,
      items_with_recommended_action: withAction,
      criticality_assessed_pct: 0,
      note: 'Health reports measured structure/provenance only. It does not claim completeness of all legal or policy changes.',
    },
  }
}

function xmlEscape(value = '') {
  return String(value).replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&apos;' }[ch]))
}

function buildRss(collection) {
  const items = collection.items.map(item => `\n    <item>\n      <guid>${xmlEscape(item.id)}</guid>\n      <title>${xmlEscape(item.change.headline)}</title>\n      <description>${xmlEscape(item.change.summary)}</description>\n      <pubDate>${xmlEscape(item.observed_on)}</pubDate>\n      <link>${xmlEscape(item.evidence.sources[0] || 'https://mikelninh.github.io/citizen-agents/')}</link>\n    </item>`).join('')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Citizen Agents Intelligence</title><link>https://mikelninh.github.io/citizen-agents/</link><description>Source-backed civic intelligence changes</description>${items}\n  </channel></rss>\n`
}

async function main() {
  const feed = JSON.parse(await readFile(path.join(root, 'breakfast-feed.json'), 'utf8'))
  const collection = buildIntelligence(feed)
  await mkdir(apiDir, { recursive: true })
  await writeFile(path.join(apiDir, 'changes.json'), `${JSON.stringify(collection, null, 2)}\n`)
  await writeFile(path.join(apiDir, 'latest.json'), `${JSON.stringify(collection.items, null, 2)}\n`)
  await writeFile(path.join(apiDir, 'health.json'), `${JSON.stringify({ schema_version: 'citizen-intelligence-health/1.0', generated_from: collection.generated_from, ...collection.health }, null, 2)}\n`)
  await writeFile(path.join(apiDir, 'changes.ndjson'), `${collection.items.map(x => JSON.stringify(x)).join('\n')}\n`)
  await writeFile(path.join(apiDir, 'changes.xml'), buildRss(collection))
  console.log(`Built Citizen Intelligence API v1: ${collection.count} changes, ${collection.health.source_coverage_pct}% source coverage.`)
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch(err => { console.error(err); process.exit(1) })
}
