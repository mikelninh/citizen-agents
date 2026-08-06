# Citizen Agents — Datenschutz & Architecture for Government Integration

**Goal: a data-protection design that a German federal agency can accept without a
10-page security review — because it starts from the strongest position possible.**

---

## 1. The core insight: we don't have the problem yet

> **The watchdogs process ZERO personal data.**

Every citizen-agent (Law-Watch, Bundestag-Watch, Money-Flow, Benefit-Watch, Court-Watch,
EU-Rights, Directive, Abuse-Safety, Procurement, Consultation) reads **public, official
sources**: laws, lobby register, Bundeshaushalt, court press releases, EUR-Lex,
official gazettes. No names of citizens, no addresses, no health data, no behavioral data.

Under DSGVO that means:
- **Art. 2 (sachlicher Anwendungsbereich)** — personal data processing is the trigger;
  no personal data, no DSGVO processing regime.
- **Datenminimierung (Art. 5(1)(c))** — we don't minimize data, we *avoid* it.
- **Privacy by Design (Art. 25)** — satisfied structurally, not as an afterthought.

This is the single strongest architectural answer you can give a German authority:
*"The system's normal operation never touches personal data. Here is the proof:
the input manifest (every source URL) and the output manifest (every digest) are
publicly auditable."*

---

## 2. Where personal data CAN appear (and the design for those cases)

| Surface | Personal data? | Design |
|---|---|---|
| Watchdog fleet | **No** — public sources only | N/A |
| SafeVoice (harassment → Strafanzeige) | **Yes** — victim's story | Browser-side processing FIRST (already built): classifier runs locally, no data leaves the device until the user explicitly submits; DSGVO-clean per repo README |
| Benefit calculators (Wohngeld/Elterngeld) | **Yes** — income, family | Pure functions, deterministic: compute locally in browser, nothing transmitted |
| Future: citizen submissions via Consultation-Watch | **Yes** — name, address | Pseudonymized submissions, explicit consent, retention limit (see below) |
| Fleet logs (`agent-logs/*.json`) | **No** — machine-readable digests of public sources | Redaction already enabled in gateway (secret redaction: ENABLED) |

### Rules that hold everywhere personal data could flow:
1. **Browser-first**: any citizen-facing computation happens in the browser. Server
   only sees what the citizen explicitly submits.
2. **Pseudonymization by default**: internal IDs, never names/emails in logs.
3. **Retention limits**: submitted data deleted after the purpose is served (e.g.,
   SafeVoice case data: delete after 30 days unless the user exports their file).
4. **Encryption**: TLS in transit (always), AES-256 at rest (any server storage).
5. **EU-only hosting**: Hetzner (Frankfurt/Falkenstein) — no US cloud for personal data.
6. **AVV-ready**: the moment we act as *processor* for an authority, we sign an
   Auftragsverarbeitungsvertrag (Art. 28) — template prepared (see below).
7. **DSB-ready**: a Datenschutzbeauftragter can audit the whole pipeline from the
   public repo — that IS the TOM (technisch-organisatorische Maßnahmen) documentation.

---

## 3. Government integration — plug-and-play by design

The fleet is already architected the way German authorities need:

### A. MCP servers = the plug-and-play unit
- Every capability is an MCP server (Model Context Protocol): stdio or HTTP/SSE.
- **No API key needed** (wohngeld, elterngeld, agb-reader, pmm, flight-rights: "no API key needed").
- Self-contained: `pip install -e .` and it runs. A ministry can run it on their own
  infrastructure — data never leaves their network.
- Standard interface = every LLM tool (Claude, ChatGPT, Cursor, custom) can use it.

### B. Deployment shapes for authorities
| Shape | What | Data sovereignty |
|---|---|---|
| **Self-host** (recommended) | Ministry runs the MCP servers in their own VPC | 100% — nothing leaves their network |
| **Hosted EU** | We run on Hetzner EU, AVV signed | EU-only, Art. 28 contract |
| **On-prem package** | Docker images + offline docs for classified needs | Full isolation |

### C. Open-source = the trust layer
- AGPL/MIT, public repo, no black box. Authorities can audit every line.
- Every agent run = digest + JSON log + PR. **Verifiability is the product.**
- German authorities explicitly prefer OSS (Open-Source-Strategie des Bundes).

### D. Standards we speak
- XÖV / ITZBund-friendly: JSON + REST + MCP — no proprietary formats.
- Dokumenten-Management: outputs as .md/.pdf-ready, importable into CMS.
- OZG spirit: citizens' interactions are digitized, reduced, verifiable.

### E. Integration workflow (for a ministry IT team)
```
1. Deploy: docker compose up (or pip install -e . per server)
2. Point agents at their data sources (or use our public fleet)
3. Add their internal knowledge base as an additional MCP tool
4. Subscribe to digests via webhook/feed → their CMS
5. Done. No data leaves their network.
```

---

## 4. The smart part — architecture that makes DSGVO *easier* for them

Most government software fights DSGVO. We inverted it:

1. **Auditability as a feature**: every claim has a source URL. An authority's
   review board can check ANY finding in minutes. That's Art. 5(2)
   (Rechenschaftspflicht) implemented literally.
2. **Human-in-the-loop as the default**: agents draft, humans decide, nobody
   auto-merges. The decision-making remains human — exactly what § 35a BDSG
   (automated decisions) requires us to preserve.
3. **No dark data**: nothing is collected "just in case". The input and output
   manifests are complete and public. No data hoarding = no data breach surface.
4. **Bounded autonomy**: agents have restricted toolsets, cost caps, and cannot
   merge. The blast radius of any single agent failure is one PR.
5. **The paper trail writes itself**: for a Behörde, the TOM documentation is
   usually the hardest part. Here it's generated daily — `agent-logs/` is a living
   TOM.

---

## 5. What to build next (checklist)

- [ ] AVV template (Auftragsverarbeitungsvertrag, Art. 28 DSGVO) — bilingual DE/EN
- [ ] Datenschutzerklärung for the portal + each citizen tool
- [ ] Docker Compose bundle (`docker-compose.yml` with all MCP servers)
- [ ] On-prem install script (air-gapped-friendly: no phone-home)
- [ ] TOM document (technisch-organisatorische Maßnahmen) generated from the repo
- [ ] DSFA-ready questionnaire (Datenschutz-Folgenabschätzung, Art. 35) — most
      surfaces answer "no processing of personal data", which simplifies it massively
- [ ] Webhook/feed endpoint so Behörden can subscribe to digests into their CMS
- [ ] Multi-tenancy design: each Behörde gets its own namespace, no shared data

---

## 6. Honest limits (say these out loud)

- We are not a law firm; final DSGVO sign-off needs a DSB (Datenschutzbeauftragter)
  — but we've made that sign-off cheap.
- SafeVoice and benefit calculators touch personal data *when the citizen opts in*;
  those surfaces need the retention + consent flow completed before mass rollout.
- "Self-host" shifts the burden: the authority becomes controller for their instance.
  That's exactly what most German institutions prefer — they want sovereignty, not
  a SaaS dependency.
- Cloud 24/7 (Hetzner) is EU-only by choice; if an authority insists on their own
  data center, the same Docker images run there unchanged.

---

## 7. One-sentence pitch for a ministry

> "Wir liefern das Wissen und die Verifikation — keine Daten. Die Agenten lesen nur
> öffentliche Quellen, alles ist quelloffen und prüfbar, und wenn Sie möchten, läuft
> das Ganze auf Ihren Servern. Datenschutz ist bei uns kein Feature, sondern die
> Architektur."

Built by Digital Democracy Studio, Berlin, 2026-08-06.
