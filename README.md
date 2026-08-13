# Citizen Agents 🌍

**Free 24/7 watchdogs for every citizen.** Autonomous agents that watch parliaments, laws,
budgets, benefits and courts — every day, cited, logged, and human-reviewed.

> **Recht auf dem Papier → Recht im Leben.**

## The core promise (and the guardrails)

| Promise | How it's enforced |
|---|---|
| Free for every citizen | Open source (AGPL/MIT), public repo, no account, GitHub Pages hosting = €0 |
| Runs every day | Scheduled agents (cron), cloud-deployable 24/7 |
| Grounded in reality | Every claim carries a source URL |
| No hallucination-as-law | Agents **draft**; humans **review**; agents **never merge** |
| Auditable | Every run writes `agent-logs/*.json` (machine-readable) + `agent-digests/*.md` (readable) + opens a PR |

**Verify it yourself:** [PR #1 on faireint-bundestag](https://github.com/mikelninh/faireint-bundestag/pull/1)
— 5 findings, 9 cited sources, opened by an agent, waiting for human review. That is the whole model in one link.

## The fleet (10 agents)

| # | Agent | Level | Status | Watches | Impact potential |
|---|---|---|---|---|---|
| 1 | GitLaw Law-Watch | 🇩🇪 | **live** | BGBl, recht.bund.de | Never act on stale law — 5,936-law corpus |
| 2 | Bundestag-Watch | 🇩🇪 | **live** | abgeordnetenwatch, Lobbyregister | ~2h/day monitoring saved per researcher; lobbying becomes public data |
| 3 | EU Citizen-Rights Watch | 🇪🇺 | **live** | CJEU, EU-Kommission, airlines | Protects €4–5B/yr unclaimed EU261 |
| 4 | Money-Flow Watch | 🇩🇪 | scheduled | Bundeshaushalt, Bundesrechnungshof | Accountability on €476.5B budget |
| 5 | Benefit-Discovery Watch | 🇩🇪 | scheduled | WoGG, BEEG, SGB II | €1B+/yr unclaimed Wohngeld; 5–15h/family research → 1 question |
| 6 | Directive-Deadline Watch | 🇪🇺 | scheduled | EUR-Lex, BMI | Ends Germany's silent late transposition |
| 7 | Court-Watch | 🇩🇪 | scheduled | BVerfG, EuGH | Landmark rulings in plain language |
| 8 | Abuse-Safety Watch | 🇩🇪 | scheduled | StGB, NetzDG, BNetzA | Keeps SafeVoice's 30s court-file route legally current |
| 9 | Procurement-Watch | 🇩🇪 | planned | Vergabedatenbanken | Anomaly flags on public tenders (Gemeinde→Bund) |
| 10 | Consultation-Watch | 🇩🇪 | planned | Bundestag, Bundesrat, Ministerien | Turns "nothing I can do" into a 10-min submission |

**Fleet snapshot — August 2026:** **3 live** · **5 scheduled** · **2 planned**.  
The repository logs and digests are the source of truth as individual agents evolve.

## Impact math (honest, with assumptions stated)

**Known unclaimed-money baselines (public figures):**
- EU261 flight compensation: **€4–5B/yr unclaimed** — airlines pay ~40% of first claims only after pushback; brokers take 25–35% commission.
- Wohngeld: **~800,000 eligible households don't claim** ≈ **€1B+/yr**.
- SafeVoice: harassment-to-court-file goes from **~3 hours to ~30 seconds**.

**Time returned to citizens (per interaction):**
- Elterngeld research: **5–15 hours → 1 question** (deterministic BEEG engine, 38 tests).
- Rights question (EU261, AGB, Wohngeld): **€25–200 lawyer consult → free, 30s, cited**.

**What 24/7 costs (the honest part):**
- GitHub Pages hosting: **€0** (static portal + logs).
- Cloud VM for true always-on agent runtime (Hetzner CX): **~€5–10/month**.
- Token cost per agent run: cents (bounded toolsets, targeted searches, daily cadence not per-minute).
- Human review: **your time** — the real cost. This is a feature: no auto-merge ever.

**Is 24/7-for-all worth it? Yes — with two honest conditions:**
1. **Supply side** (agents + portal) is nearly free at the margin: €0–10/mo for unlimited citizens.
2. **Demand side** is the real work: citizens must *find* it. Impact = reach × relevance.
   Distribution (NGOs, Verbraucherzentrale, journalists, schools) is the next biggest win after the fleet is live.

## How a run works

```
scheduler → agent runs (cron)
  ├─ web research (cited sources only)
  ├─ writes agent-digests/<date>.md   (citizen-readable)
  ├─ writes agent-logs/<date>.json    (machine-readable)
  ├─ opens PR (human review; never merges)
  └─ pings Telegram (when wired)
every run: log · digest · PR · ping — nothing silent
```

## Repo map

```
citizen-agents/          ← you are here (hub: portal + registry + hub digests)
  index.html             free citizen portal (GitHub Pages)
  agents.json            machine-readable fleet registry
  agent-digests/         citizen-readable briefings per run
  agent-logs/            structured JSON per run (audit)
gitlaw/                  law corpus + explainers (Law-Watch home)
faireint-bundestag/      lobby/vote tracking (Bundestag-Watch home)
flight-rights-mcp/       EU261 + AGB (EU Rights-Watch home)
pmm-mcp/                 budget mirror (Money-Flow Watch home)
safevoice/               harassment → court file (Abuse-Safety home)
civic-ai-mcp-toolkit/    the machine that builds machines (M1)
```

## Next biggest wins (ranked)

1. **Wire Telegram delivery** — citizens (and you) get the daily briefings pushed, not just filed.
2. **Cloud 24/7 deploy** (Hetzner, ~€5/mo) — true always-on runtime, then the fleet scales to 10.
3. **Benefit-Discovery Watch live** — the single biggest direct-money agent (€1B+ Wohngeld).
4. **One distribution partner** (Verbraucherzentrale / NGO / journalist) — turns potential into impact.
5. **Impact dashboard** — auto-aggregate `agent-logs/*.json` into a live "what we found this month" page.

## Principles (non-negotiable)

- Free for every citizen. Always.
- Every claim carries a source URL.
- Agents draft, humans review, nobody auto-merges.
- Structured logs on every run.
- Open source, no lock-in, no paywall.

Built in Berlin. Open source wherever possible. — Digital Democracy Studio, 2026
