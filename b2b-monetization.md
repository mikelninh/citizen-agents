# Citizen Agents — B2B Monetization Package

**Status: 2026-08-06 — everything below is buildable on top of what already exists.
Free-for-citizens stays the core. B2B is how the fleet pays for itself.**

---

## The principle

> Citizens always get the core free. Organizations pay for scale, integration,
> verification, and bespoke data. No paywall ever sits between a person and their rights.

This is the same shape as GitLaw (free citizen app + GitLaw Pro closed beta) —
it already exists and it's the proof this works.

---

## Offer 1 — MCP Licensing (the existing moat)

**What we have:** 7 production MCP servers (gitlaw, safevoice, flight-rights, wohngeld,
elterngeld, agb-reader, pmm) + the civic-ai-mcp-toolkit that builds them in a day.

**Who buys:**
- Verbraucherzentralen / consumer advice centers — embed Wohngeld/Elterngeld/AGB tools
- Insurance & banks — compliance-grade AGB clause checks at onboarding
- Travel platforms — EU261 rights at the booking/claim moment (AirHelp takes 25-35%; we license the engine)
- Legal tech / law firms — GitLaw corpus + citation graph (already the Pro pitch)
- Public sector (Bund/Länder) — PMM budget anomaly layer

**Pricing (per MCP, per year):**
| Tier | What | Price |
|---|---|---|
| Community | self-host, open source | €0 |
| Professional | hosted endpoint, SLA, updates, 1 seat | €1,200/yr |
| Enterprise | dedicated instance, white-label, compliance, custom data | €6,000+/yr |
| Bundle | all 7 MCPs + toolkit, professional | €5,000/yr |

**Why they pay instead of building:** the corpus + jurisprudence + citation graphs
take months to assemble; we already have 200+ tests and 53/53 citation resolution.

---

## Offer 2 — Agent Fleet as a Service (the new thing)

**What we have:** 13 agents that daily produce cited, logged, human-reviewed briefings
on laws, parliament, lobby, budget, benefits, courts, procurement, EU deadlines.

**Who buys:**
- Media (journalism): "lobby radar" — monthly pattern reports on who registers before
  which vote; anomaly alerts on procurement.
- NGOs & advocacy: benefit-discovery alerts for their members; consultation windows
  with drafted submissions.
- Municipalities (as *customers*, not subjects): citizen-communication feeds —
  "what changed this week in your rights" for official portals.
- Political foundations & think tanks: FairEint policy-sim + Bundestag data.

**Pricing:**
| Tier | What | Price |
|---|---|---|
| Data feed | raw agent-logs JSON + digests, monthly | €500/mo |
| Briefing service | custom briefs on their topic, weekly | €1,500/mo |
| White-label fleet | dedicated agents in their domain | €3,000+/mo |

---

## Offer 3 — Data & API (passive revenue)

- **Lobby/Bundestag dataset** — normalized, deduplicated, cross-referenced
  (abgeordnetenwatch + Lobbyregister + votes): €300/mo for API access.
- **Benefit-change feed** — machine-readable Wohngeld/Elterngeld/Bürgergeld rule changes
  for apps that depend on current numbers: €400/mo.
- **CJEU jurisprudence feed** — EU261/consumer rulings as structured data: €250/mo.

---

## Offer 4 — Impact partnerships (not charity)

- **SafeVoice**: NGO Trägerschaft (HateAid-type partner) — grant-funded, free for victims.
  This is already the stated plan in the repo. Grant asks: €80-120k/yr for a small team.
- **Public-interest sponsors**: a company sponsors one watchdog (transparent, disclosed,
  no editorial control — the agent still publishes what it finds). €2,000-5,000/yr per agent.
- **University partnerships**: research access to the fleet + logs (privacy-safe),
  small grants.

---

## What to build next to sell this (in order)

1. **Demo pack** — a 5-page PDF: one real digest per agent, the PR trail, the numbers.
   (We already have the raw material — PR #1, the logs, the dashboard.)
2. **Pricing page** on the portal (the B2B section we just drafted).
3. **One lighthouse customer** in each segment:
   - a Verbraucherzentrale (MCPs),
   - a regional newsroom (fleet feed),
   - one municipality (citizen-communication).
4. **Contract templates** (MCP license, data feed, white-label) — keep simple, AGPL-compatible
   dual-licensing for the MCPs (community AGPL, commercial license for integration).
5. **Metrics page** — auto-aggregate agent-logs into monthly "what the fleet found"
   (hard numbers close deals).

## Numbers that close deals

- €4-5B/yr unclaimed EU261 — our engine is the rights side of that gap
- €1B+/yr unclaimed Wohngeld — 800k households — our tool surfaces eligibility in 30s
- 5-15h per Elterngeld application → 1 question
- 3h manual Strafanzeige → 30s (SafeVoice, 12 paragraphs, 35 validated cases)
- 53/53 citation resolution on the legal corpus
- 200+ tests across the MCP toolkit

## Guardrails (non-negotiable)

- Citizens: always free. No paywall on any existing citizen tool.
- Editorial independence: sponsors never control what agents publish.
- Open source where it works: AGPL/MIT stays the default; commercial is licensing, not forking.
- Every B2B claim must be verifiable — point to the PRs, not the promises.

Built by Digital Democracy Studio, Berlin, 2026-08-06.
