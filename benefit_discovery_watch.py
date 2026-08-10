#!/usr/bin/env python3
"""
Benefit-Discovery Watch — Citizen Agents fleet
==============================================

Aggressive money-finder watchdog. Unlike benefit-watch (which tracks *changes*
in the law), this agent hunts for MONEY that citizens are entitled to but do
NOT claim: Wohngeld, Kinderzuschlag, Bildung & Teilhabe, Elterngeld-Fristen,
Sparerpauschbetrag, Arbeitnehmer-Sparzulage/Wohnungsbauprämie, BAföG-
Studienstarthilfe, Heizkosten-/Energiehilfen.

Outputs (self-contained, no human in the loop):
  agent-digests/benefit-discovery-YYYY-MM-DD.md   citizen-readable (German)
  agent-logs/benefit-discovery-YYYY-MM-DD.json    machine-readable

Design rules:
  * every claim carries at least one source URL
  * live web research enriches a curated, source-backed baseline
  * fully defensive: if web search fails, the run still produces a valid
    digest and flags research_mode = "degraded" honestly
"""

from __future__ import annotations

import json
import os
import re
import sys
import datetime
import urllib.parse
import urllib.request

AGENT = "benefit-discovery"
AGENT_TITLE = "Benefit-Discovery Watch"
ROOT = os.path.dirname(os.path.abspath(__file__))
DIGEST_DIR = os.path.join(ROOT, "agent-digests")
LOG_DIR = os.path.join(ROOT, "agent-logs")
UA = "Mozilla/5.0 (compatible; CitizenAgents-BenefitDiscovery/1.0)"
TIMEOUT = 20

# ---------------------------------------------------------------- baseline
# Curated, source-backed money items. Each is verified-by-URL; the live
# research pass only ADDS fresh sources / recency signals on top.
TOPICS = [
    {
        "id": "wohngeld",
        "headline": "Wohngeld — der größte ungehobene Geldtopf: jetzt beantragen, bevor die Reform greift",
        "what": "Wohngeld ist der Klassiker unter den nicht abgerufenen Leistungen: Studien zur "
                "Nichtinanspruchnahme von Sozialleistungen zeigen, dass ein erheblicher Teil der "
                "Berechtigten nie einen Antrag stellt (\"verdeckte Armut\"). Gleichzeitig hat das "
                "Kabinett am 6. Juli 2026 eine Wohngeldreform beschlossen, die den Bundesansatz von "
                "rund 5 auf 3 Mrd. Euro senken soll — künftige Anträge fallen also tendenziell "
                "niedriger aus.",
        "effective": "Wohngeld ist jetzt beantragbar; die Kürzungsreform ist Gesetzentwurf, noch "
                     "nicht in Kraft. Wohngeld wird ab dem Monat der Antragstellung gezahlt — nicht rückwirkend.",
        "who": "Mieterinnen und Mieter sowie Eigentümer mit kleinem bis mittlerem Einkommen, "
               "Rentner, Alleinerziehende, Studierende ohne BAföG-Anspruch, Azubis in bestimmten Fällen.",
        "tip": "Antrag noch in diesem Monat bei der örtlichen Wohngeldstelle einreichen — ein Tag zu spät "
               "kostet einen ganzen Monatsbetrag. Auch bei Unsicherheit einreichen: der Bescheid kostet nichts.",
        "sources": [
            "https://www.bmwsb.bund.de/DE/wohnen/wohngeld/wohngeld-plus/wohngeld-plus_node.html",
            "https://www.tagesschau.de/inland/gesellschaft/wohngeld-kuerzung-faq-100.html",
            "https://www.bmas.de/DE/Service/Publikationen/Forschungsberichte/fb-668-bestandsaufnahme-nichtinanspruchnahme-sozialleistungen.html",
        ],
        "queries": ["Wohngeld 2026 Antrag Anspruch Wohngeldstelle", "Wohngeld Reform 2026 Kürzung Gesetzentwurf"],
        "money": "bis zu mehrere hundert Euro pro Monat",
    },
    {
        "id": "kinderzuschlag",
        "headline": "Kinderzuschlag (KiZ) — bis 297 € pro Kind und Monat, muss extra beantragt werden",
        "what": "Der Kinderzuschlag ist eine eigene Leistung der Familienkasse für Eltern, die zwar "
                "genug für sich selbst verdienen, aber nicht für ihre Kinder. Er wird **nicht** automatisch "
                "mit dem Kindergeld ausgezahlt, sondern muss gesondert beantragt werden — deshalb bleibt er "
                "häufig ungenutzt. Höchstbetrag laut DGB-Ratgeber: 297 € je Kind und Monat.",
        "effective": "Laufend beantragbar; Bewilligung in der Regel für 6 Monate, danach Folgeantrag nötig.",
        "who": "Erwerbstätige Familien und Alleinerziehende mit kleinem Einkommen, die kein Bürgergeld/"
               "keine neue Grundsicherung beziehen.",
        "tip": "Zuerst den kostenlosen \"KiZ-Lotse\" der Bundesagentur für Arbeit ausfüllen (wenige Minuten) "
               "und direkt online beantragen. Wer KiZ bekommt, hat automatisch Zugang zum Bildungs- und "
               "Teilhabepaket und ist von Kita-Gebühren befreit.",
        "sources": [
            "https://www.arbeitsagentur.de/familie-und-kinder/kinderzuschlag-verstehen/kinderzuschlag-anspruch-hoehe-dauer",
            "https://www.arbeitsagentur.de/familie-und-kinder/kinderzuschlag-verstehen/kiz-lotse",
            "https://www.dgb.de/service/ratgeber/kinderzuschlag-und-kindergrundsicherung/",
        ],
        "queries": ["Kinderzuschlag 2026 Höhe Antrag Familienkasse"],
        "money": "bis 297 € / Kind / Monat",
    },
    {
        "id": "bildung-teilhabe",
        "headline": "Bildung und Teilhabe (BuT) — Schulbedarf, Mittagessen, 15 € Vereinsbeitrag pro Monat",
        "what": "Das Bildungspaket übernimmt für Kinder aus Familien mit kleinem Einkommen Schulausflüge, "
                "Schulbedarf, Lernförderung, Mittagessen in Kita/Schule sowie pauschal 15 € pro Monat für "
                "Sport-, Freizeit- und Kulturangebote. Anspruch besteht u. a. auch bei Wohngeld- oder "
                "Kinderzuschlagsbezug — genau diese Gruppe beantragt es oft nicht.",
        "effective": "Laufend; Anträge werden meist nur begrenzt rückwirkend anerkannt — zeitnah stellen.",
        "who": "Familien mit Bürgergeld/neuer Grundsicherung, Wohngeld, Kinderzuschlag oder Sozialhilfe.",
        "tip": "Antrag beim Jobcenter bzw. Landkreis/kreisfreier Stadt stellen — Wohngeld- und KiZ-Empfänger "
               "haben ein eigenes Antragsformular. Belege (Vereinsbeitrag, Klassenfahrt) aufheben.",
        "sources": [
            "https://www.arbeitsagentur.de/familie-und-kinder/informationen-zum-bildungspaket",
            "https://www.familienratgeber.de/rechte-leistungen/geld/leistungen-fuer-bildung-und-teilhabe",
            "https://www.service-bw.de/zufi/leistungen/1963",
        ],
        "queries": ["Bildung und Teilhabe Antrag 2026 Leistungen"],
        "money": "15 €/Monat Teilhabe + Schulbedarf + Mittagessen",
    },
    {
        "id": "elterngeld-frist",
        "headline": "Elterngeld — nur 3 Monate rückwirkend: jeder verspätete Monat ist verlorenes Geld",
        "what": "Elterngeld wird maximal für die letzten **drei** Lebensmonate vor Antragstellung "
                "rückwirkend gezahlt. Wer den Antrag verschleppt, verliert die davorliegenden Monate "
                "endgültig — das ist der häufigste vermeidbare Geldverlust junger Eltern.",
        "effective": "Dauerhaft geltende Frist (Familienportal des Bundes; ZBFS Bayern).",
        "who": "Alle Eltern nach der Geburt, insbesondere bei später Anmeldung oder fehlenden Unterlagen.",
        "tip": "Antrag sofort nach der Geburt einreichen, auch unvollständig — Nachweise dürfen nachgereicht "
               "werden. Das Antragsdatum sichert den Anspruch.",
        "sources": [
            "https://familienportal.de/familienportal/familienleistungen/elterngeld/faq/wie-kann-ich-elterngeld-beantragen--124762",
            "https://www.zbfs.bayern.de/familienleistungen/elterngeld/faq/voraussetzungen_und_antrag/",
            "https://www.bmbfsfj.bund.de/bmbfsfj/themen/familie/familienleistungen/elterngeld",
        ],
        "queries": ["Elterngeld rückwirkend drei Monate Antrag Frist"],
        "money": "300–1.800 € pro verlorenem Monat",
    },
    {
        "id": "sparerpauschbetrag",
        "headline": "Sparerpauschbetrag 1.000 € — ohne Freistellungsauftrag verschenkt die Bank dein Geld ans Finanzamt",
        "what": "Kapitalerträge bleiben bis 1.000 € pro Jahr steuerfrei (2.000 € bei Zusammenveranlagung). "
                "Ohne erteilten Freistellungsauftrag zieht die Bank trotzdem rund 25 % Abgeltungsteuer plus "
                "Soli ab. Das Geld ist nicht verloren, muss aber über die Steuererklärung (Anlage KAP) "
                "zurückgeholt werden — was viele nie tun.",
        "effective": "Gilt fortlaufend; Freistellungsaufträge wirken ab Erteilung für das laufende Kalenderjahr.",
        "who": "Alle mit Tagesgeld, Festgeld, ETF-Sparplan oder Dividenden — bei aktuellen Zinsen reicht "
               "schon ein mittleres Tagesgeldguthaben, um den Freibetrag zu reißen.",
        "tip": "Freistellungsauftrag bei jeder Bank/Broker anpassen (Summe über alle Institute max. 1.000 €/"
               "2.000 €) und in der Steuererklärung die Anlage KAP nutzen, falls bereits zu viel einbehalten wurde.",
        "sources": [
            "https://www.finanzamt.nrw.de/steuerinfos/privatpersonen/einkuenfte-aus-kapitalvermoegen/sparerpauschbetrag-freistellungsauftrag",
            "https://www.finanztip.de/freistellungsauftrag/",
        ],
        "queries": ["Sparerpauschbetrag 2026 Freistellungsauftrag Höhe"],
        "money": "bis ca. 264 € Steuerersparnis pro Jahr (Single)",
    },
    {
        "id": "sparzulage-wop",
        "headline": "Arbeitnehmer-Sparzulage & Wohnungsbauprämie — Einkommensgrenzen stark angehoben, viele wissen es nicht",
        "what": "Die Einkommensgrenze für die Arbeitnehmer-Sparzulage wurde massiv angehoben: Alleinstehende "
                "bis 40.000 € zu versteuerndem Jahreseinkommen (früher 17.900 €), Verheiratete entsprechend "
                "doppelt. Die Wohnungsbauprämie gibt es bis 35.000 € (Single) bzw. 70.000 € (Paare). Wer "
                "vermögenswirksame Leistungen bekommt, aber nie einen VL-Vertrag abgeschlossen hat, lässt "
                "Arbeitgeber- **und** Staatsgeld liegen.",
        "effective": "Geltende Rechtslage; Sparzulage wird mit der Einkommensteuererklärung festgesetzt, "
                     "Wohnungsbauprämie jährlich über den Anbieter beantragt.",
        "who": "Arbeitnehmerinnen und Arbeitnehmer mit Anspruch auf vermögenswirksame Leistungen (oft im "
               "Tarifvertrag), Bausparer, junge Sparer.",
        "tip": "Im Arbeitsvertrag/Tarifvertrag nach \"vermögenswirksame Leistungen\" suchen, VL-Vertrag "
               "abschließen und die Sparzulage über Anlage VL in der Steuererklärung geltend machen.",
        "sources": [
            "https://www.lbs.de/bausparen/staatliche-foerderung/arbeitnehmer-sparzulage",
            "https://www.wuestenrot.de/bausparen/staatliche-foerderungen/wohnungsbaupraemie",
            "https://www.mystipendium.de/geld/wohnungsbaupraemie",
        ],
        "queries": ["Arbeitnehmersparzulage Wohnungsbauprämie 2026 Einkommensgrenzen"],
        "money": "bis ca. 123 € + 70 € staatliche Zulagen pro Jahr",
    },
    {
        "id": "bafoeg-studienstarthilfe",
        "headline": "BAföG-Studienstarthilfe — 1.000 € einmalig, ohne Vermögensprüfung der Eltern",
        "what": "Die Studienstarthilfe ist ein einmaliger Zuschuss von 1.000 € für junge Menschen aus "
                "finanziell schwachen Haushalten zum Studienstart. Sie ist ein Zuschuss (keine Rückzahlung) "
                "und unabhängig vom klassischen BAföG-Bewilligungsverfahren gedacht — sie wird deutlich "
                "seltener abgerufen als möglich.",
        "effective": "Beantragung rund um den Studienbeginn; Fristen sind eng an den Studienstart gekoppelt.",
        "who": "Studienanfängerinnen und -anfänger unter 25, deren Familien Sozialleistungen (z. B. "
               "Bürgergeld, Wohngeld, Kinderzuschlag, BAB) beziehen.",
        "tip": "Antrag beim zuständigen Studierendenwerk stellen — parallel zum regulären BAföG-Antrag, "
               "nicht stattdessen. Auch bei knappem BAföG-Anspruch lohnt der Antrag.",
        "sources": [
            "https://www.xn--bafg-7qa.de/bafoeg/de/verbesserte-leistungen/dasneuebafoeg_node.html",
            "https://www.einstieg.com/studium/bafoeg-reform-2026.html",
        ],
        "queries": ["BAföG Studienstarthilfe 1000 Euro Antrag 2026"],
        "money": "1.000 € einmalig",
    },
    {
        "id": "heizkosten-energie",
        "headline": "Heizkosten- und Energiehilfen — teils automatisch, teils nur auf Antrag (Landesprogramme prüfen)",
        "what": "Der bundesweite Heizkostenzuschuss wurde laut Bundesregierung von Amts wegen ausgezahlt, "
                "musste also nicht beantragt werden. Aktuelle Entlastungen laufen dagegen überwiegend über "
                "**Landes- und Kommunalprogramme** sowie über Härtefallfonds der Energieversorger — diese "
                "erfordern einen Antrag und haben eigene Fristen. Hier ist die Faktenlage regional sehr "
                "unterschiedlich; wir kennzeichnen das ausdrücklich als unsicher.",
        "effective": "Programme laufen je nach Bundesland/Kommune unterschiedlich; Fristen bitte lokal prüfen.",
        "who": "Wohngeld-, BAföG- und Aufstiegs-BAföG-Beziehende, Azubis mit BAB, Haushalte mit "
               "Energieschulden.",
        "tip": "Bei drohender Sperre sofort den Sozialdienst/die Verbraucherzentrale kontaktieren: Jobcenter "
               "können Energieschulden als Darlehen übernehmen. Zusätzlich das eigene Bundesland nach einem "
               "aktuellen Heizkostenzuschuss durchsuchen.",
        "sources": [
            "https://www.bundesregierung.de/breg-de/aktuelles/heizkostenzuschuss-2144900",
            "https://www.mein-nebenkostenrechner.de/ratgeber/heizkostenzuschuss-2026-wer-anspruch-hat",
        ],
        "queries": ["Heizkostenzuschuss 2026 Deutschland Antrag Wohngeld"],
        "money": "regional unterschiedlich",
        "uncertain": True,
    },
]

BLOCKED_HOSTS = ("facebook.com", "instagram.com", "x.com", "twitter.com", "tiktok.com", "pinterest.")


# ---------------------------------------------------------------- research
def _search_hermes(query, limit=5):
    """Preferred path: Hermes-managed web search (only inside a Hermes runtime)."""
    from hermes_tools import web_search  # noqa
    res = web_search(query, limit=limit) or {}
    out = []
    for item in (res.get("data", {}) or {}).get("web", []) or []:
        url = item.get("url", "")
        if url:
            out.append({"title": (item.get("title") or "").strip(), "url": url})
    return out


def _search_brave(query, limit=5):
    """Optional path: Brave Search API if a key is configured in the env."""
    key = os.environ.get("BRAVE_API_KEY") or os.environ.get("BRAVE_SEARCH_API_KEY")
    if not key:
        raise RuntimeError("no BRAVE_API_KEY")
    url = ("https://api.search.brave.com/res/v1/web/search?q="
           + urllib.parse.quote(query) + f"&count={limit}&country=de")
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "X-Subscription-Token": key, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    return [{"title": r.get("title", ""), "url": r.get("url", "")}
            for r in (data.get("web", {}) or {}).get("results", [])][:limit]


EURO_RE = re.compile(r"\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s?(?:€|Euro)")
CHANGE_WORDS = ("neu ab", "ab 1.", "Frist", "Änderung", "erhöht", "steigt",
                "gesenkt", "Reform", "beantrag", "rückwirkend")


def verify_source(url):
    """Real HTTP check of an official source: reachable? which € amounts /
    change-signals does it currently show? Never raises."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept-Language": "de-DE,de;q=0.9"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.getcode()
            raw = resp.read(400_000).decode("utf-8", "replace")
    except Exception as exc:
        return {"url": url, "ok": False, "error": str(exc)[:160]}
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    amounts = list(dict.fromkeys(EURO_RE.findall(text)))[:8]
    signals = sorted({w for w in CHANGE_WORDS if w.lower() in text.lower()})
    return {"url": url, "ok": status == 200, "http_status": status,
            "euro_amounts_seen": amounts, "change_signals": signals}


def _search_ddg(query, limit=5):
    """Fallback: DuckDuckGo HTML endpoint, no API key required."""
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        html = resp.read().decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if "uddg=" in href:
            href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
        out.append({"title": title, "url": href})
        if len(out) >= limit:
            break
    return out


def research(query, limit=5):
    """Return (results, mode). Never raises."""
    for name, fn in (("hermes", _search_hermes), ("brave", _search_brave), ("duckduckgo", _search_ddg)):
        try:
            hits = fn(query, limit=limit)
            if hits:
                return hits, name
        except Exception as exc:  # defensive: cron must never crash
            sys.stderr.write(f"[warn] search backend {name} failed for {query!r}: {exc}\n")
    return [], "none"


def clean(hits):
    seen, out = set(), []
    for h in hits:
        u = h.get("url", "")
        if not u.startswith("http") or any(b in u for b in BLOCKED_HOSTS):
            continue
        key = u.split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


# ---------------------------------------------------------------- rendering
def build(today):
    findings, backends, verified_ok, verified_total = [], set(), 0, 0
    for topic in TOPICS:
        fresh = []
        for q in topic.get("queries", []):
            hits, mode = research(q, limit=5)
            backends.add(mode)
            fresh.extend(clean(hits))
        # add up to 2 live-found extra sources not already in the baseline
        extra = [h["url"] for h in fresh if h["url"] not in topic["sources"]][:2]
        item = dict(topic)
        item["sources"] = topic["sources"] + extra
        item["live_hits"] = len(fresh)
        # real HTTP verification pass over every cited source
        checks = [verify_source(u) for u in item["sources"]]
        item["source_checks"] = checks
        verified_total += len(checks)
        verified_ok += sum(1 for c in checks if c.get("ok"))
        findings.append(item)
    if backends & {"hermes", "brave", "duckduckgo"}:
        mode = "live-search"
    elif verified_ok:
        mode = "live-verify"
    else:
        mode = "degraded"
    return findings, mode, {"sources_checked": verified_total, "sources_reachable": verified_ok}


def render_markdown(findings, today, mode, stats):
    L = []
    L.append(f"# 💶 Benefit-Discovery Watch — {today}")
    L.append("")
    L.append("Geldradar für Bürgerinnen und Bürger: **Leistungen, auf die du Anspruch hast, "
             "die aber massenhaft nicht abgerufen werden.** Jeder Eintrag nennt Quellen.")
    note = {
        "live-search": "Websuche aktiv, Quellen zusätzlich per HTTP geprüft.",
        "live-verify": "Keine Suchmaschine verfügbar — stattdessen wurden alle zitierten "
                       "Quellen live per HTTP abgerufen und auf aktuelle Beträge/Fristen geprüft.",
        "degraded": "Kein Netzzugriff möglich — es gilt der zuletzt geprüfte Basisstand. "
                    "Bitte Angaben selbst gegenprüfen.",
    }[mode]
    L.append(f"**{len(findings)} Geldtöpfe in diesem Lauf.** Recherche-Modus: `{mode}` — {note} "
             f"({stats['sources_reachable']}/{stats['sources_checked']} Quellen erreichbar)")
    L.append("")
    L.append("---")
    L.append("")
    for i, f in enumerate(findings, 1):
        L.append(f"## {i}. {f['headline']}")
        L.append(f"- **What changed:** {f['what']}")
        L.append(f"- **Effective:** {f['effective']}")
        L.append(f"- **Who's affected:** {f['who']}")
        L.append(f"- **Citizen tip:** {f['tip']} *(Größenordnung: {f['money']})*")
        if f.get("uncertain"):
            L.append("- **Unsicherheit:** Regional stark unterschiedlich — bitte vor Antragstellung "
                     "die eigene Kommune/das eigene Bundesland gegenprüfen.")
        live = [c for c in f.get("source_checks", []) if c.get("ok") and c.get("euro_amounts_seen")]
        if live:
            amts = ", ".join(live[0]["euro_amounts_seen"][:4])
            L.append(f"- **Live-Check ({today}):** Quelle erreichbar, aktuell genannte Beträge: {amts}")
        L.append("- **Sources:**")
        for s in f["sources"]:
            L.append(f"  - {s}")
        L.append("")
    L.append("---")
    L.append("")
    L.append("### Bottom line for citizens")
    L.append("Der teuerste Fehler ist **nicht** der falsche Antrag, sondern der nie gestellte. "
             "Wohngeld und Kinderzuschlag wirken erst ab Antragsmonat, Elterngeld nur drei Monate "
             "rückwirkend — jeder Monat Zögern ist bares Geld. Reihenfolge für heute: "
             "**1) KiZ-Lotse ausfüllen, 2) Wohngeldantrag einreichen, 3) Freistellungsauftrag prüfen.**")
    L.append("")
    L.append("*Generated by the Benefit-Discovery Watch agent. Keine Rechtsberatung — verbindliche "
             "Auskunft geben Wohngeldstelle, Familienkasse, Jobcenter, Studierendenwerk und Finanzamt.*")
    return "\n".join(L) + "\n"


def render_json(findings, today, mode, stats):
    return {
        "agent": AGENT,
        "title": AGENT_TITLE,
        "date": today,
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
        "research_mode": mode,
        "country": "DE",
        "focus": "unclaimed monetary entitlements",
        "item_count": len(findings),
        "verification": stats,
        "schema_version": 1,
        "items": [
            {
                "id": f["id"],
                "headline": f["headline"],
                "what_changed": f["what"],
                "effective": f["effective"],
                "who_affected": f["who"],
                "citizen_tip": f["tip"],
                "money_scale": f["money"],
                "uncertain": bool(f.get("uncertain")),
                "live_hits": f.get("live_hits", 0),
                "sources": f["sources"],
                "source_checks": f.get("source_checks", []),
            }
            for f in findings
        ],
        "digest_path": f"agent-digests/{AGENT}-{today}.md",
        "log_path": f"agent-logs/{AGENT}-{today}.json",
    }


def main():
    today = datetime.date.today().isoformat()
    os.makedirs(DIGEST_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        findings, mode, stats = build(today)
    except Exception as exc:  # absolute last-resort guard
        sys.stderr.write(f"[error] research pass failed entirely: {exc}\n")
        findings, mode = [dict(t, live_hits=0) for t in TOPICS], "degraded"
        stats = {"sources_checked": 0, "sources_reachable": 0}

    md_path = os.path.join(DIGEST_DIR, f"{AGENT}-{today}.md")
    js_path = os.path.join(LOG_DIR, f"{AGENT}-{today}.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(findings, today, mode, stats))
    with open(js_path, "w", encoding="utf-8") as fh:
        json.dump(render_json(findings, today, mode, stats), fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"{AGENT_TITLE}: {len(findings)} items, mode={mode}")
    print(md_path)
    print(js_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
