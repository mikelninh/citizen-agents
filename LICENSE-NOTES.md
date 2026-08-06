# License Notes — AGPL vs dual licensing for government use

## Current state

- Civic tools (gitlaw, safevoice, MCPs, hub): **AGPL-3.0** (gitlaw) / **MIT** (most MCPs)
- This is a *strength* for credibility (open source, no black box)

## The procurement reality

Some German procurement offices are cautious about AGPL-3.0 because:
- Network-use clause (AGPL § 13) can be unfamiliar to legal teams
- They sometimes prefer MIT/BSD or a commercial license for internal integration

**This is solvable — dual licensing is the standard open-core answer:**

| Audience | License | Why |
|---|---|---|
| Citizens | AGPL / MIT (as today) | Free, auditable, no lock-in |
| Government integration | Commercial license (per-seat / per-instance) | They get a familiar contract, we get revenue |
| Verbraucherzentrale / NGO | Discounted or free commercial license | Mission alignment, reach |

## How to operationalize

1. Keep the repos AGPL/MIT (public good stays public)
2. Add a `LICENSE-COMMERCIAL.md` with terms (grant of rights, warranty, support, SLA)
3. In the README of each repo: "Community edition AGPL-3.0 · Commercial license available — contact"
4. The B2B doc already lists this under Offer 1 — MCP Licensing

## What NOT to do

- Do not relicense the citizen-facing apps (breaks trust, breaks the mission)
- Do not make the fleet's *output* proprietary (digests/logs stay public)
- Do not let a commercial deal delay open-source contributions

## One-line guidance

> Free for citizens, licensed for institutions — the data and the logs stay public
> in both cases; only the integration/support layer is commercial.

*Digital Democracy Studio, Berlin, 2026-08-06.*
