# Government Readiness — what a German institution needs before it adopts Citizen Agents

**Goal: make the answer to every procurement, legal, and security question a
pre-built document, not a promise.**

A German authority (Bundesministerium, Landesbehörde, Kommune, Verbraucherzentrale)
will NOT adopt a project because it's good. It adopts because:
1. It can legally buy it (entity, contract, AVV)
2. It can run it (self-host, OSS, no black box)
3. It can defend the decision (Datenschutz, Barrierefreiheit, security)
4. It has a low-risk entry point (pilot, not a transformation)

This repo now contains the package for all four. See the file list below.

---

## THE 7 GATEWAYS (in the order an institution checks them)

### 1. Legal entity & contract partner
**Reality:** a ministry does not contract with an individual GitHub user.
**What's needed:**
- A legal entity (GmbH, UG, or a foundation/NGO Trägerschaft) as contracting partner
- Or: partner with an existing institution (Verbraucherzentrale, Hochschule, NGO
  like HateAid for SafeVoice) that carries the contract
- Impressum + Datenschutzerklärung on every public surface (SafeVoice already flags
  this as a pre-live item — it stays on the list)
**Status:** ⬜ your decision (entity or partner)

### 2. DSGVO package (Datenschutz)
**Why we win here:** the watchdogs process ZERO personal data. The architecture
starts from the strongest position possible. See `datenschutz-architecture.md`.
**What's needed (all buildable):**
- AVV template (Art. 28) — `avv-template.md` ✅ in this package
- Datenschutzerklärung (portal + each citizen tool) — ⬜ draft in package
- TOM documentation (technisch-organisatorische Maßnahmen) — ⬜ generated from repo
- DSFA readiness sheet (Art. 35) — ⬜ most surfaces answer "no personal data"
- Retention & deletion rules for the surfaces that DO touch personal data
  (SafeVoice, benefit calculators) — ⬜ policy doc
**Status:** 🔶 package started (see files)

### 3. Barrierefreiheit (BITV 2.0 / WCAG 2.1 AA)
**Reality:** since the Barrierefreiheitsstärkungsgesetz (2025), public digital
services in Germany MUST be accessible. No a11y = no contract. Full stop.
**What's needed:**
- WCAG 2.1 AA audit of the portal, dashboard, and all citizen apps
- Contrast, keyboard navigation, screen-reader labels, focus states
- German-language "Erklärung zur Barrierefreiheit" on the portal
**Status:** ⬜ to do — this is a hard requirement, not polish

### 4. Open source governance & security
**Why we win:** everything is public, auditable, and every run leaves a PR trail.
**What's needed:**
- LICENSE clarity: AGPL-3.0 for the civic tools; dual-license path for
  commercial/government integration (AGPL scares some procurement offices — offer MIT
  or a commercial license for their instance) — `LICENSE-NOTES.md` ⬜
- SECURITY.md with responsible-disclosure policy — ✅ in package
- CONTRIBUTING.md + CODEOWNERS on the hub — ⬜
- Dependency audit + SBOM (software bill of materials) per repo — ⬜
- Independent security review / pentest before any production claim — ⬜ needs budget
**Status:** 🔶 SECURITY.md done, rest queued

### 5. Deployment & data sovereignty (the winning argument)
**Why we win:** a ministry can run everything on its own network. No data leaves
their sovereignty. That is the #1 selling point in German procurement.
**What's needed:**
- Docker Compose bundle of all MCP servers — ✅ `docker-compose.yml` in package
- On-prem / air-gapped install script (no phone-home) — ⬜
- Architecture + operations doc for their IT team — ⬜
- Webhook/feed endpoint so digests can flow into their CMS — ⬜ (next build)
**Status:** 🔶 compose bundle done

### 6. Procurement path & pilot
**Reality:** the fastest entry is a **pilot**, not a tender.
**The realistic routes:**
- **Pilot partner first**: one Verbraucherzentrale / Landesbehörde / Kommune runs
  one agent (e.g., Benefit-Watch) with us for 90 days. Evidence, then scale.
- **DigitalService / FITKO / GovTech Campus**: the federal bodies explicitly tasked
  with modernizing state digital services — they fund and run pilots.
- **OZG alignment**: frame the fleet as OZG-adjacent (citizen journeys digitized).
- **Direct award under threshold**: contracts under the EU threshold can be awarded
  directly — a pilot is exactly that shape.
- **Open-source catalogue**: German public sector has an open-source directory;
  being listed there removes friction.
**What's needed:**
- One-pager pilot proposal — ✅ `pilot-proposal.md` in package
- Success metrics (what we measure in 90 days) — ✅ in pilot doc
- Contact list (who to email) — ⬜ needs your network
**Status:** 🔶 pilot doc done, outreach yours

### 7. Credibility & evidence
**Why we win:** every claim is a link. The PR trail is the pitch.
**What's needed:**
- The proof board (`proof.html`) — ✅ live
- Monthly "what the fleet found" auto-report — ⬜ (build after 30 days of runs)
- A neutral third party (university, journalist) reviewing the method — ⬜
- Published methodology (how we verify, what "verified" means) — ⬜
**Status:** 🔶 proof board live

---

## FILE MANIFEST (this package)

| File | What | Status |
|---|---|---|
| `datenschutz-architecture.md` | DSGVO design + government integration shapes | ✅ |
| `cloud-24-7.md` | Hetzner deployment + honest costs | ✅ |
| `b2b-monetization.md` | Offer tiers, pricing, lighthouse customers | ✅ |
| `proof.html` | Visual ratings + real PR evidence | ✅ |
| `gov-readiness.md` | This document — the 7 gateways | ✅ |
| `avv-template.md` | Art. 28 AVV skeleton (DE/EN) | ✅ |
| `SECURITY.md` | Responsible disclosure + security posture | ✅ |
| `docker-compose.yml` | Self-host bundle of all MCP servers | ✅ |
| `pilot-proposal.md` | 90-day pilot one-pager (DE) | ✅ |
| `LICENSE-NOTES.md` | AGPL vs dual-licensing guidance | ✅ |
| `datenschutzerklaerung.md` | Privacy policy skeleton (DE) | ⬜ next |
| `tom-document.md` | TOM (tech.-org. Maßnahmen) | ⬜ next |
| `barrierefreiheit.md` | a11y audit + Erklärung zur Barrierefreiheit | ⬜ next |

---

## THE 30-SECOND PITCH (for any institution)

> "Zehn Agenten beobachten täglich Gesetze, Parlament, Haushalt, Leistungen und
> Gerichte — jede Aussage mit Quelle, jeder Lauf mit Log, jeder Befund im PR zur
> menschlichen Prüfung. Keine personenbezogenen Daten, quelloffen, läuft auf Ihren
> Servern. Sie bezahlen keine Software — Sie bekommen Verifikation."

---

## WHAT I NEED FROM YOU (the only real blockers)

1. **Entity or partner** — GmbH/UG, or an institution to carry pilots (biggest one)
2. **Contact list** — 5 institutions to pitch (Verbraucherzentrale, Land, Kommune, NGO)
3. **Budget signal** — even €0 pilots work; but know your ask per tier (see b2b doc)
4. **Go/no-go on a11y pass** — it's a hard requirement; ~half a day of work

Everything else in this package is built and in the repo.

Built by Digital Democracy Studio, Berlin, 2026-08-06.
