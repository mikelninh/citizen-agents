# Citizen Agents 🌍

**Open-source watchdog agents for public information — cited, logged and human-reviewed.**

Citizen Agents monitors public sources and turns changes in laws, rights, budgets and institutions into inspectable digests rather than silent AI output.

**[Open the public portal](https://mikelninh.github.io/citizen-agents/)**

## The operating model

```text
public sources
      ↓
agent run
      ↓
cited findings
      ↓
structured log + readable digest
      ↓
pull request
      ↓
human review
```

Agents can research and prepare. **They do not silently publish or merge consequential claims.**

## What is implemented

The repository acts as a hub for a small fleet of public-interest agents, including work around:

- changes in German law
- citizen rights
- public spending
- benefits and public services
- court and institutional updates

Every run is designed to leave an audit trail with source URLs and machine-readable output.

## Why this matters

Public information is often technically available but practically difficult to follow. The goal is not to create another opaque AI news feed; it is to make important changes easier to notice **while keeping the evidence visible**.

## Guardrails

- every factual finding should point to a source
- uncertain findings remain uncertain
- agents draft; humans review
- runs create logs rather than disappearing into chat history
- no autonomous legal or governmental decisions
- public-interest infrastructure should remain inspectable and reusable

## Related systems

- [GitLaw](https://github.com/mikelninh/gitlaw) — legal corpus, retrieval and citation verification
- [Public Money MCP](https://github.com/mikelninh/pmm-mcp) — grounded federal-budget tools
- [SafeVoice](https://github.com/mikelninh/safevoice) — evidence preparation for digital harassment
- [Digital Democracy Studio](https://github.com/mikelninh/digital-democracy-studio) — broader civic-tech experiments

## Status

Working public prototype. Some agents and integrations are more mature than others; repository logs and code are the source of truth for what is actually running.

---

Built by [Michael Ninh](https://github.com/mikelninh) in Berlin.
