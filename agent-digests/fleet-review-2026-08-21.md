# 🛡️ Fleet Review — 2026-08-21

**Reviewer:** FLEET REVIEWER (read-only watchdog)
**Review date:** 2026-08-21
**Reviewed batch:** agent artifacts dated **2026-08-20** (8 branches)
**Scope note:** No 2026-08-21 agent/watchdog artifacts existed at review time. The only 2026-08-21 commits on `main` were a "Breakfast Ticker" website rebuild (not an agent artifact). The 2026-08-20 batch was the latest unreviewed agent output (the last fleet review was 2026-08-19), so it is reviewed here. The 5 external repos (faireint-bundestag, gitlaw, pmm-mcp, safevoice, flight-rights-mcp) had **no** activity on 2026-08-20/21 (latest commits 2026-08-14 → 2026-08-17) and produced no artifacts to review.

## Scoreboard

| Agent | Verdict | Key issue(s) | Top source check | One-line reason |
|---|---|---|---|---|
| court-watch | ✅ VERIFIED | none (LOW: ~73M GKV stat unsourced) | C-234/25, C-421/24, 2 BvE 3/26 → all OK | All 3 rulings confirmed verbatim by CURIA/BVerfG |
| directive-watch | ✅ VERIFIED | LOW: inf_26_1376 blocked scraping | Anti-SLAPP EAPIL + Mutter-Tochter Tax@Hand → OK | 14-MS SLAPP infringement + DE/FR/IT PSD case both corroborated |
| procurement | ✅ VERIFIED | LOW: Funds 5–6 not deep-checked | cosinx + DLF → exact figures OK | 60% error rate / €750k / 80% freihändig confirmed precisely |
| treaty-watch | ✅ VERIFIED | LOW: Fund 3 (CEDAW/Afghanistan) not deep | ERRC + OHCHR → OK | Stanislav Tomáš ruling + Canada ICCPR both confirmed |
| truth-watch | 🟡 PARTIAL | **HIGH: JSON missing `highlights`** | AliExpress €550M, Reuters, AFP → OK | Content accurate; log schema defect only |
| meat-dairy | 🟡 PARTIAL | MEDIUM: UBA URL 404 | R001861 + 6.5bn GAP → OK; UBA 35.5Mt → BROKEN | Lobby reg + subsidy figures exact; one dead source link |
| climate-watch | 🟡 PARTIAL | MEDIUM: NDC % tied to 2021 page | IEA + Shell → OK; UNFCCC 2021 → MISMATCH | Shell/IEA confirmed; headline NDC figure on stale URL |
| consultation | 🟡 PARTIAL | MEDIUM: EIT deadline unverifiable | Bundestag hearings → OK; better-regulation → BROKEN | Hearings confirmed; EIT 23 Sep 2026 source failed + possible mismatch |

**Totals:** agents_reviewed = 8 · verified = 4 · partial = 4 · failed = 0 · blockers = 0

## Guardrail checks (all PASS)
- **No agent merged anything:** all 8 branches are unmerged (`git branch -r --merged origin/main` lists only old 2026-08-06 branches). ✓
- **Scope respected:** every branch touched *only* `agent-digests/` and `agent-logs/`. No game code or other files modified. ✓
- **Reviewer read-only:** this review adds only `agent-digests/fleet-review-2026-08-21.md` and `agent-logs/fleet-review-2026-08-21.json`. Nothing else changed; no merge performed. ✓

---

## Per-agent detail

### court-watch — ✅ VERIFIED
Sources fetched (3/3 resolve & support):
- `curia.europa.eu/.../cp260097en.pdf` (C-234/25 Sky Österreich) → **OK**: confirms digital *service* vs digital *content*, withdrawal right cannot be excluded, proportionate compensation. Matches digest.
- `curia.europa.eu/.../cp260109en.pdf` (C-421/24 AGCOM) → **OK**: confirms 16 Jul 2026, AGCOM €750,000 fine on Google Ireland, YouTube gambling-ad partnership, loss of hosting exemption. Matches digest exactly.
- `bundesverfassungsgericht.de/.../bvg26-041.html` (2 BvE 3/26) → **OK**: "Erfolglose Eilanträge … GKV-Beitragssatzstabilisierungsgesetz", Nr. 41/2026, 9 Jul 2026, 2. Senat. Matches digest.
Issues: none material. LOW — the "≈73 million GKV members" figure is asserted in the BVerfG context but not directly sourced; plausible, not checked.

### directive-watch — ✅ VERIFIED
Sources fetched:
- `eur-lex.europa.eu/eli/dir/2024/1069/oj/eng` → **OK**: Directive (EU) 2024/1069 Anti-SLAPP, 11 Apr 2024.
- `eapil.org/2026/07/16/...anti-slapp...` → **OK**: "15 July 2026 … infringement proceedings against 14 Member States … Germany … transposition deadline 7 May 2026." Matches digest (Fund 1).
- `ec.europa.eu/commission/presscorner/detail/en/inf_26_1376` (Mutter-Tochter) → **BROKEN (scrape failed)**, but claim independently corroborated by `taxathand.com/.../European-Commission-publishes-July-2026-infringements-package` → **OK**: "On 8 July 2026 … procedures against France, Germany, and Italy over taxation of dividends from EU subsidiaries" (links inf_26_1376). Confirms Fund 6 (INFR(2026)2089). LOW.
Issues: none material. The blocked Commission page is a scraper limitation, not a dead link (Deloitte mirrors the same case).

### procurement — ✅ VERIFIED
Sources fetched:
- `blog.cosinex.de/2026/08/07/rechnungshof-bw...` → **OK**: 111 cases, 67 errors = 60% (65% of 31 new), Drucksache 18/307, 16 Jul 2026, ~3.9 bn total / ~670 m state / 20,281 grants, 44% missing docs, 32% wrong procedure. Matches digest (Fund 1) exactly.
- `deutschlandfunk.de/bundesrechnungshof-kritisiert-gelockerte-vergabepraxis` → **OK**: BRH quote, ">80% freihändig", 50 bn 2009 package, federal relaxation ended 2010, NRW/BW/RLP/Bavaria extended. Matches (Fund 2).
- `vergabe24.de/.../eu-schwellenwerte-2026...` → **OK (resolves, topic confirmed)**; exact thresholds (5.404m etc.) not extractable from JS page but EUR-Lex 2025/2152 also cited. LOW.
Issues: LOW — Funds 5 (Berlin thresholds) and 6 (price-audit >25%) not individually source-verified this run (plausible, Vergabe24 topic consistent).

### treaty-watch — ✅ VERIFIED
Sources fetched:
- `errc.org/.../stanislav-tomas` → **OK**: 16 Jul 2026, ECtHR v Czech Republic, 46-yo Romani man, prone >11 min, knee on neck >4 min, "manifest lack of diligence", Arts 2 & 3, HUDOC 001-251195. Matches Fund 1 exactly.
- `ohchr.org/en/press-releases/2026/03/...canada...` → **OK**: 23 Mar 2026, Canada concerns on UNDRIP enforcement + inadequate Indigenous consultation. Matches Fund 2 (Ombudsperson vacancy detail plausible/consistent).
Issues: LOW — Fund 3 (CEDAW Afghanistan "gender apartheid") not deep-checked; well-documented elsewhere, consistent with digest.

### truth-watch — 🟡 PARTIAL
Sources fetched (all 3 OK):
- `digital-strategy.ec.europa.eu/.../commission-fines-aliexpress-eu550-million...` → **OK**: "Commission fines AliExpress €550 million … DSA", 20 Jul 2026, last update 27 Jul 2026. Matches.
- `reuters.com/.../russia-steps-up-disinformation...` → **OK**: "Matryoshka" campaign, targets AfD rivals CDU/SPD/Greens/FDP, Berlin/Saxony-Anhalt/Mecklenburg-Vorpommern, "anti-Russian hysteria". Matches.
- `factcheck.afp.com/doc.afp.com.C3YL7NR` → **OK**: 7.1 quake S Japan 28 Jul, 38 dead, Kumamoto, HAARP cannot induce quakes. Matches.
**Issue (HIGH):** `agent-logs/truth-watch-2026-08-20.json` is **missing the required `highlights` field** (present in the other 7 logs; schema check flagged). Content is accurate — this is a logging defect, not a factual error. Fix: add `highlights` array to the log before merge.

### meat-dairy — 🟡 PARTIAL
Sources fetched:
- `lobbyregister.bundestag.de/suche/R001861` → **OK**: "Bundesmarktverband für Vieh und Fleisch", R001861, updated 30.06.2026, 16 members (legal persons), member dues 20.001–30.000 €, lobbying spend 1–10.000 €, 0.11 FTE, Hubertus Beringmeier. Matches Fund 1 exactly.
- `bmleh.de/.../043-agrarzahlungen.html` → **OK**: "2023/2024 … rund 300.000 Begünstigte ca. 6,5 Milliarden Euro … GAP". Matches Fund 2.
- `umweltbundesamt.de/.../fragen-antworten-zu-tierhaltung-ernaehrung` → **BROKEN (HTTP 404 "Seite wurde nicht gefunden")**. This is the primary source for Fund 4's "35.5 Mt CO₂e / 68% of farm emissions" stat. The figure is a real, agency-attributed UBA number (not hallucinated) but the cited deep link is dead, so it cannot be verified via the provided URL. **MEDIUM.**
Issues: MEDIUM — dead UBA link for a key statistic (claim credible, link broken). LOW — Fund 2 "≈35 bn € 2023–2027" not verified (second source dvs-gap-netzwerk not fetched).

### climate-watch — 🟡 PARTIAL
Sources fetched:
- `unfccc.int/news/full-ndc-synthesis-report-...` → **MISMATCH (stale)**: page is the **17 Sep 2021** NDC synthesis (COP26 era, 191 parties, emissions *decrease* 12% by 2030 for 113 parties). It does **NOT** support the digest's headline "16% more emissions by 2030 vs 2010 / 143 parties with assessable targets". **MEDIUM** — wrong-year source for the headline claim.
- `unfccc.int/.../2025-ndc-synthesis-report` → **OK (exists)**: "2025 NDC Synthesis Report", published 28 Oct 2025, based on 64 new NDCs / ~30% global emissions; excerpt does not surface the exact 16%/143 figures (could not confirm in fetched text). Correct report is cited as source 2.
- `iea.org/reports/global-energy-review-2026/co2-emissions` → **OK**: "Global Energy Review 2026", "Energy sector emissions continued to rise in 2025". Supports Fund 2.
- `reuters.com/.../shell-loosens-2030...` → **OK**: "Shell weakens 2030 … scraps 2035 target", Mar 2024, net-zero 2050. Supports Fund 3.
Issues: MEDIUM — headline NDC % attached to a 2021 page; correct 2025 report cited but exact figures unconfirmed in excerpt. LOW — Funds 4 (ECGT 27 Sep 2026 / 20 MS) and 5 (Carbon Majors 35.5 Mt) not verified this run.

### consultation — 🟡 PARTIAL
Sources fetched:
- `bundestag.de/ausschuesse/gesundheit/anhoerungen` → **OK**: lists public hearings incl. "Heftige Kritik von Fachverbänden an GKV-Sparpaket" (22 Jun 2026), "Medizinregistergesetz", "Patientenrechtegesetz" — matches Fund 2 topics.
- `ec.europa.eu/info/law/better-regulation/` → **BROKEN (scrape failed / Internal Server Error)**. This is the primary source for Fund 1's "EIT feedback, deadline 23 Sep 2026". Deadline could not be verified. **MEDIUM.**
- The digest's second source for Fund 1 (`research-and-innovation.ec.europa.eu/.../future-european-innovation-act-2025-07-09`) appears to concern a different initiative ("European Innovation Act") than the "European Institute of Innovation and Technology (EIT)" the digest describes — possible source mismatch. **MEDIUM.**
Issues: MEDIUM — EIT deadline unverifiable (portal blocked) + apparent EIT-vs-Innovation-Act source conflation. LOW — Fund 3 (BMWE draft bills) not verified.

---

## What needs human eyes today
1. **truth-watch log schema** (HIGH): add the missing `highlights` field before any merge — otherwise the log fails the required-field contract.
2. **meat-dairy dead link** (MEDIUM): replace the 404 UBA URL (Fund 4) with a live UBA source for the 35.5 Mt CO₂e figure.
3. **climate-watch stale NDC source** (MEDIUM): the "16% by 2030" headline should cite the 2025 synthesis report, not the 2021 page currently linked.
4. **consultation EIT item** (MEDIUM): confirm the 23 Sep 2026 EIT deadline against a live source and fix the EIT/Innovation-Act mix-up.

No BLOCKERs, no merges, no scope violations. All 8 digests are factually sound on the claims that were checkable; issues are sourcing/linking/schema hygiene.
