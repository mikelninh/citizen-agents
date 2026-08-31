# Citizen Agents 🌍

**Open-source watchdog agents for public information — cited, logged and human-reviewed.**

Citizen Agents monitors public sources and turns changes in laws, rights, money, democratic action windows and institutions into inspectable intelligence rather than silent AI output.

**[Founder Control Center](https://mikelninh.github.io/citizen-agents/control-center.html)**  
**[Revenue Opportunity OS](https://mikelninh.github.io/citizen-agents/revenue-os.html)**  
**[Open the public portal](https://mikelninh.github.io/citizen-agents/)**  
**[Democracy Radar](https://mikelninh.github.io/citizen-agents/democracy-radar.html)**  
**[For organisations](https://mikelninh.github.io/citizen-agents/organisations.html)**

## The operating model

```text
public sources
      ↓
watchdogs
      ↓
source-backed signal
      ↓
Impact Graph
      ↓
what affects you?
what can you still do?
      ↓
usefulness feedback
      ↓
proof report
```

For consequential actions the intelligence layer never grants itself authority. Citizen Agents can recommend what to review; the consuming organisation / OCN decides `ALLOW`, `APPROVAL` or `BLOCK`.

## Watchdog families

- 💶 Rights & Money — benefits, taxes, housing, work, family support and deadlines
- ⏰ Democracy Action Window — hearings, consultations and submission/registration windows
- 💰 Funding Radar — grants, calls, eligibility and deadlines
- ⚖️ Rights & Courts — important judgments and rights changes
- 🏛️ Power & Influence — lobby positions, rulemaking and stakeholder pressure
- 🗳️ Elections, Petitions & Participation — concrete participation windows
- 📜 Promises → Laws → Votes — schema for tracing proposals through the legislative process

The machine-readable registry is in [`watchdog-registry.json`](watchdog-registry.json). Current curated official-source democracy signals are in [`democracy-signals.json`](democracy-signals.json). The existing Rights & Money fleet remains the most automated family.

## Proof of usefulness

The organisation Impact Graph does not claim generic AI ROI. Reviewers can mark each signal as:

- useful / not useful
- already known
- would otherwise have been missed
- action triggered

The exported evidence report measures observed usefulness and explicitly leaves estimated hours saved, customer value and guaranteed ROI unset until real evidence exists.

## What is implemented

- cited public watchdog findings and structured logs
- Breakfast Ticker and personal watchdog profile
- versioned Civic Intelligence API (`api/v1/changes.json`)
- combined Democracy Radar API (`api/v1/radar.json`, generated in CI)
- organisation Impact Graph and local usefulness evidence
- alerts, reliability surface and 14-day Intelligence Proof
- self-dogfood Revenue Opportunity OS with proof matching, route selection, partner mapping and outcome tracking
- Founder Control Center for today priorities, revenue pipeline, opportunity radar, reusable proofs, partner leverage and coverage health
- Company 01 intake for opted-in paid proofs

## Guardrails

- every factual finding should point to a source
- uncertain findings remain uncertain
- no completeness claim until coverage is measured
- programme budgets are not presented as customer value
- agents draft; humans review
- no autonomous legal or governmental decisions
- public-interest infrastructure remains inspectable and reusable

## Related systems

- [GitLaw](https://github.com/mikelninh/gitlaw) — legal corpus, retrieval and citation verification
- [Public Money MCP](https://github.com/mikelninh/pmm-mcp) — grounded federal-budget tools
- [SafeVoice](https://github.com/mikelninh/safevoice) — evidence preparation for digital harassment
- [Digital Democracy Studio](https://github.com/mikelninh/digital-democracy-studio) — broader civic-tech experiments

## Status

Working public prototype moving toward Civic Intelligence Infrastructure. Automation maturity differs by watchdog family; repository logs, registry status and code are the source of truth for what is actually automated versus currently curated.

---

Built by [Michael Ninh](https://github.com/mikelninh) in Berlin.
