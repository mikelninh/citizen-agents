#!/usr/bin/env python3
"""
Breakfast Ticker builder for Citizen Agents.

Fetches the latest agent-digests + fleet-review from the citizen-agents repo,
parses them into citizen-friendly "breakfast" cards with cited sources and a
human-review trust score, and emits a self-contained, friendly breakfast.html.

Stdlib only. Re-run by the daily cron so the page stays current.
"""
import json
import re
import html
import urllib.request
import urllib.error
from datetime import date

REPO = "mikelninh/citizen-agents"
BRANCH = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
API = f"https://api.github.com/repos/{REPO}/contents"
UA = {"User-Agent": "citizen-agents-breakfast-builder"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def list_dir(path):
    data = get_json(f"{API}/{path}?ref={BRANCH}")
    return [d["name"] for d in data if d["type"] == "file"]


def latest_digest_dates():
    names = list_dir("agent-digests")
    dates = set()
    for n in names:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", n)
        if m:
            dates.add(m.group(1))
    return sorted(dates, reverse=True)


def parse_digest(md):
    lines = md.splitlines()
    title = ""
    date = ""
    intro = []
    findings = []
    bottom = []
    in_bottom = False
    cur = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            dm = re.search(r"(\d{4}-\d{2}-\d{2})", title)
            if dm:
                date = dm.group(1)
            i += 1
            continue
        if line.startswith("### Bottom line"):
            in_bottom = True
            i += 1
            continue
        if in_bottom:
            bottom.append(line)
            i += 1
            continue
        m = re.match(r"^##\s+(\d+)\.\s+(.*)", line)
        if m:
            if cur:
                findings.append(cur)
            cur = {"num": m.group(1), "headline": m.group(2).strip(), "fields": {}, "sources": []}
            i += 1
            continue
        if cur is not None:
            fm = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)", line)
            if fm:
                key = fm.group(1).strip().lower()
                val = fm.group(2).strip()
                if key in ("sources", "quelle", "source", "quellen"):
                    urls = extract_urls(val)
                    cur.setdefault("sources", [])
                    cur["sources"].extend(urls)
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith("-") and "http" in lines[j]:
                        cur["sources"].extend(extract_urls(lines[j]))
                        j += 1
                    i = j
                    continue
                elif key in ("warum wichtig", "wie mitmachen", "termin", "institution"):
                    fmap = {"warum wichtig": "why", "wie mitmachen": "how", "termin": "deadline", "institution": "institution"}
                    cur.setdefault("fields", {})
                    cur["fields"][fmap[key]] = val
                    i += 1
                    continue
                else:
                    cur.setdefault("fields", {})
                    cur["fields"][key] = val
                    i += 1
                    continue
        if cur is None and line.strip() and not line.startswith("#") and not line.startswith("---"):
            if not line.startswith("**") or "tracked changes" in line.lower() or "gefunden" in line.lower():
                intro.append(line)
        i += 1
    if cur:
        findings.append(cur)
    return {"title": title, "date": date, "intro": " ".join(intro).strip(),
            "findings": findings, "bottom_line": " ".join(bottom).strip()}


def extract_urls(text):
    return re.findall(r"https?://[^\s)\]]+", text)


def parse_fleet_review(md):
    totals = {}
    tm = re.search(r"Totals:\s*(\d+)\s*VERIFIED\s*[·•]\s*(\d+)\s*PARTIAL\s*[·•]\s*(\d+)\s*FAILED", md)
    if tm:
        totals = {"verified": int(tm.group(1)), "partial": int(tm.group(2)), "failed": int(tm.group(3))}
    verdicts = []
    for line in md.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6:
            vm = re.search(r"\*\*(VERIFIED|PARTIAL|FAILED|BLOCKED)\*\*", cells[2])
            if vm and cells[0] and not cells[0].startswith("Agent"):
                verdicts.append({"agent": cells[0], "repo": cells[1], "verdict": vm.group(1),
                                 "schema": cells[3], "guardrails": cells[4], "reason": cells[5].strip("*")})
    return {"totals": totals, "verdicts": verdicts}


def esc(s):
    return html.escape(str(s))


def verdict_class(v):
    return {"VERIFIED": "ok", "PARTIAL": "warn", "FAILED": "bad", "BLOCKED": "bad"}.get(v, "warn")


def render_finding(f):
    fields_order = [("what changed", "Was hat sich geändert"), ("effective", "Ab wann"),
                    ("who's affected", "Wen betrifft's"), ("citizen tip", "Tipp für dich")]
    out = [f'<div class="finding"><h3><span class="fnum">{esc(f["num"])}</span> {esc(f["headline"])}</h3>']
    for key, label in fields_order:
        if key in f["fields"]:
            out.append(f'<p><span class="lbl">{esc(label)}</span> {esc(f["fields"][key])}</p>')
    if f["sources"]:
        out.append('<div class="sources"><span class="lbl" data-i18n="sources">Quellen:</span>')
        for u in f["sources"]:
            out.append(f'<span class="srcchip"><a href="{esc(u)}" target="_blank" rel="noopener">{esc(u)}</a></span>')
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


WATCHDOG_SVG = """
<svg class="mascot" viewBox="0 0 64 64" aria-hidden="true">
  <defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffd479"/><stop offset="1" stop-color="#f0a429"/></linearGradient></defs>
  <path d="M32 4 L56 14 V34 C56 48 46 58 32 60 C18 58 8 48 8 34 V14 Z" fill="url(#g1)" stroke="#7a4d12" stroke-width="2"/>
  <circle cx="24" cy="30" r="6" fill="#1a212b"/><circle cx="40" cy="30" r="6" fill="#1a212b"/>
  <circle cx="26" cy="28" r="2" fill="#fff"/><circle cx="42" cy="28" r="2" fill="#fff"/>
  <path d="M26 40 Q32 46 38 40" stroke="#1a212b" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <path d="M20 18 l4 -6 l4 6 M40 18 l4 -6 l4 6" stroke="#7a4d12" stroke-width="2" fill="none"/>
  <circle cx="32" cy="9" r="3" fill="#ffd479" stroke="#7a4d12" stroke-width="1.5"/>
</svg>"""

COFFEE_SVG = """
<svg class="coffee" viewBox="0 0 64 64" aria-hidden="true">
  <path d="M14 26 h34 v14 a14 14 0 0 1 -14 14 h-6 a14 14 0 0 1 -14 -14 Z" fill="#fff" opacity="0.92"/>
  <path d="M48 30 h6 a6 6 0 0 1 0 12 h-6" fill="none" stroke="#fff" stroke-width="3"/>
  <path class="steam s1" d="M26 18 q-3 -6 0 -12" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.7"/>
  <path class="steam s2" d="M38 18 q3 -6 0 -12" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.7"/>
</svg>"""


def build_page(latest, digests, fr):
    today = date.today().isoformat()
    cards = []
    for d in digests:
        emoji = ""
        em = re.match(r"^#\s+(\S+)\s", d["title"])
        if em:
            emoji = em.group(1)
        findings_html = "\n".join(render_finding(f) for f in d["findings"])
        bottom = f'<div class="bottom">{esc(d["bottom_line"])}</div>' if d["bottom_line"] else ""
        intro = f'<p class="intro">{esc(d["intro"])}</p>' if d["intro"] else ""
        cards.append(f"""
        <section class="card">
          <header class="card-head">{WATCHDOG_SVG}<div><span class="badge" data-i18n="badge_watchdog">WÄCHTER</span>
            <h2>{emoji} {esc(d['title'].split('—',1)[-1].strip())}</h2></div></header>
          {intro}
          <div class="findings">{findings_html}</div>
          {bottom}
        </section>""")

    if fr and fr["totals"]:
        t = fr["totals"]
        verdict_rows = "\n".join(
            f'<tr><td><b>{esc(v["agent"])}</b></td><td><span class="pill {verdict_class(v["verdict"])}">{esc(v["verdict"])}</span></td>'
            f'<td>{esc(v["reason"])}</td></tr>' for v in fr["verdicts"])
        trust = f"""
        <section class="card trust">
          <header class="card-head">{WATCHDOG_SVG}<div><span class="badge trust-badge" data-i18n="badge_trust">VERTRAUEN</span>
            <h2 data-i18n="trust_title">Vom Fleet-Reviewer geprüft</h2></div></header>
          <div class="trust-totals">
            <div class="t ok"><b>{t['verified']}</b><span data-i18n="t_verified">verifiziert</span></div>
            <div class="t warn"><b>{t['partial']}</b><span data-i18n="t_partial">teilweise</span></div>
            <div class="t bad"><b>{t['failed']}</b><span data-i18n="t_failed">fehlerhaft</span></div>
          </div>
          <table class="verdicts"><tr><th>Wächter</th><th>Urteil</th><th>Kurzbegründung</th></tr>{verdict_rows}</table>
          <p class="note" data-i18n="trust_note">Menschen prüfen, Agenten entwerfen — niemand merges automatisch. Jede Meldung trägt ihre Quelle.</p>
        </section>"""
    else:
        trust = ""

    support = """
        <section class="card support">
          <header class="card-head">💛<div><span class="badge sup-badge" data-i18n="badge_support">UNTERSTÜTZEN</span>
            <h2 data-i18n="support_title">Kostenlos — und trotzdem nicht umsonst</h2></div></header>
          <p class="intro" data-i18n="support_intro">Der Ticker bleibt für immer gratis. Server, Review und neue Wächter laufen über freiwillige Unterstützung. So sieht die Aufteilung aus:</p>
          <div class="tiers">
            <div class="tier free">
              <h3 data-i18n="tier_free_title">🆓 Jeder Bürger</h3>
              <ul id="tierFree"></ul>
            </div>
            <div class="tier pro">
              <h3><span data-i18n="tier_pro_title">⭐ „Dein Wächter"</span> <span class="soon" data-i18n="soon">in Planung</span></h3>
              <ul id="tierPro"></ul>
              <div class="price" data-i18n="price">ab 3 € / Monat</div>
            </div>
          </div>
          <div class="donate-row">
            <a class="btn primary" href="https://github.com/sponsors/mikelninh" target="_blank" rel="noopener" data-i18n="btn_sponsors">☕ GitHub Sponsors (ab 1 €)</a>
            <a class="btn ghost" href="mailto:hallo.chupi@gmail.com?subject=Citizen%20Agents%20f%C3%BCr%20Organisationen" target="_blank" rel="noopener" data-i18n="btn_org">🤝 Für Organisationen &amp; NGOs</a>
          </div>
          <p class="note" data-i18n="support_note">Kostenlos. Für immer. Finanziert durch Menschen, die es ernst meinen.</p>
        </section>"""

    tags = ["Frisch gebrüht aus öffentlichen Quellen.",
            "Deine Rechte, täglich geprüft.",
            "Kein Bezahlschutz vor deinen Rechten.",
            "Wächter schlafen nicht — damit du ruhig schläfst."]

    return TEMPLATE.replace("{LATEST}", esc(latest)).replace("{TODAY}", esc(today)) \
        .replace("{CARDS}", "".join(cards)).replace("{TRUST}", trust).replace("{SUPPORT}", support) \
        .replace("{TAGS}", json.dumps(tags))


TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Breakfast Ticker — Citizen Agents</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root { --bg:#f5f3f1; --card:#ffffff; --ink:#202020; --navy:#02083a; --muted:#5b6472; --accent:#0068e6; --accent-soft:#e8f0ff; --ok:#1a7f4b; --ok-soft:#e6f4ec; --warn:#9a6400; --warn-soft:#fdf3e0; --bad:#c4322b; --bad-soft:#fdeaea; --line:#e7e3df; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font:16px/1.6 "Onest",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { max-width:760px; margin:0 auto; padding:36px 20px 96px; }
  .masthead { text-align:center; padding:16px 0 26px; }
  .coffee { width:58px; height:58px; display:block; margin:0 auto 10px; }
  .steam { animation:rise 3s ease-in-out infinite; }
  .steam.s2 { animation-delay:.6s; }
  @keyframes rise { 0%{opacity:0;transform:translateY(4px)} 40%{opacity:.8} 100%{opacity:0;transform:translateY(-6px)} }
  .kicker { letter-spacing:3px; font-size:11px; color:var(--accent); text-transform:uppercase; font-weight:700; }
  h1 { font-size:34px; margin:10px 0 6px; color:var(--navy); letter-spacing:-.5px; }
  .dateline { color:var(--muted); font-size:14px; }
  #tag { color:var(--accent); font-size:15px; margin-top:10px; min-height:22px; font-style:italic; }
  .lede { color:var(--muted); margin-top:8px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:20px;
    padding:22px 24px; margin:18px 0; box-shadow:0 6px 22px rgba(2,8,58,.05); }
  .card-head { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
  .card-head h2 { margin:0; font-size:19px; color:var(--navy); }
  .mascot { width:40px; height:40px; flex:none; }
  .badge { display:inline-block; background:var(--accent); color:#fff; font-size:10px; font-weight:800; letter-spacing:1px;
    padding:3px 10px; border-radius:999px; }
  .trust-badge { background:var(--navy); }
  .sup-badge { background:#e0729a; color:#fff; }
  .intro { color:var(--muted); margin:0 0 12px; }
  .finding { border-top:1px solid var(--line); padding:14px 0 6px; }
  .finding h3 { margin:0 0 6px; font-size:15px; color:var(--navy); display:flex; gap:8px; align-items:baseline; }
  .fnum { background:var(--accent); color:#fff; font-size:12px; font-weight:800; border-radius:999px; padding:1px 9px; }
  .finding p { margin:4px 0; }
  .lbl { color:var(--muted); font-weight:600; font-size:13px; }
  .sources { margin-top:10px; font-size:12px; }
  .sources a { color:var(--accent); text-decoration:none; display:block; word-break:break-all; margin:2px 0; }
  .sources a:hover { text-decoration:underline; }
  .bottom { border-top:1px solid var(--line); margin-top:12px; padding-top:14px; font-size:15px; color:var(--ink); }
  .trust-totals { display:flex; gap:12px; margin:12px 0 16px; }
  .trust-totals .t { flex:1; text-align:center; background:var(--bg); border:1px solid var(--line); border-radius:16px; padding:14px 6px; }
  .trust-totals b { font-size:26px; display:block; color:var(--navy); }
  .trust-totals span { font-size:12px; color:var(--muted); }
  .trust-totals .ok b { color:var(--ok); } .trust-totals .warn b { color:var(--warn); } .trust-totals .bad b { color:var(--bad); }
  table.verdicts { width:100%; border-collapse:collapse; font-size:13px; }
  table.verdicts th, table.verdicts td { text-align:left; padding:9px; border-top:1px solid var(--line); vertical-align:top; }
  table.verdicts th { color:var(--muted); font-weight:600; }
  .pill { font-size:11px; font-weight:800; padding:3px 10px; border-radius:999px; white-space:nowrap; }
  .pill.ok { background:var(--ok-soft); color:var(--ok); }
  .pill.warn { background:var(--warn-soft); color:var(--warn); }
  .pill.bad { background:var(--bad-soft); color:var(--bad); }
  .note { color:var(--muted); font-size:13px; margin-top:12px; }
  .tiers { display:flex; gap:14px; margin:14px 0; flex-wrap:wrap; }
  .tier { flex:1; min-width:240px; background:var(--bg); border:1px solid var(--line); border-radius:16px; padding:16px 18px; }
  .tier h3 { margin:0 0 10px; font-size:16px; color:var(--navy); }
  .tier ul { margin:0; padding-left:18px; color:var(--ink); }
  .tier li { margin:6px 0; }
  .tier.pro { border-color:var(--accent); box-shadow:0 0 0 1px rgba(0,104,230,.2) inset; }
  .soon { font-size:10px; background:var(--accent); color:#fff; padding:2px 8px; border-radius:999px; vertical-align:middle; }
  .price { margin-top:12px; font-weight:800; color:var(--accent); }
  .donate-row { display:flex; gap:12px; flex-wrap:wrap; margin-top:8px; }
  .btn { display:inline-block; padding:12px 18px; border-radius:999px; font-weight:700; text-decoration:none; font-size:14px; transition:.15s; }
  .btn.primary { background:var(--accent); color:#fff; }
  .btn.ghost { background:#fff; color:var(--navy); border:1px solid var(--line); }
  .btn:hover { transform:translateY(-1px); }
  footer { color:var(--muted); font-size:13px; text-align:center; margin-top:36px; }
  footer a { color:var(--accent); }
  .live { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--ok); margin-right:6px;
    box-shadow:0 0 0 0 rgba(26,127,75,.5); animation:pulse 2s infinite; vertical-align:middle; }
  @keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(26,127,75,.5)} 70%{box-shadow:0 0 0 10px rgba(26,127,75,0)} 100%{box-shadow:0 0 0 0 rgba(26,127,75,0)} }
  .topbar { display:flex; align-items:center; justify-content:space-between; padding:6px 2px 16px; }
  .brand { display:flex; align-items:center; gap:9px; font-weight:700; color:var(--navy); font-size:15px; }
  .brand-mark { width:22px; height:22px; flex:none; }
  .lang-toggle { border:1px solid var(--line); background:#fff; color:var(--navy); font-weight:700; font-size:13px;
    padding:7px 15px; border-radius:999px; cursor:pointer; transition:.15s; }
  .lang-toggle:hover { border-color:var(--accent); color:var(--accent); }
  .masthead { position:relative; text-align:center; padding:26px 0 30px; }
  .masthead::before { content:""; position:absolute; left:-20px; right:-20px; top:-30px; height:260px;
    background:radial-gradient(120% 100% at 50% 0, rgba(0,104,230,.09), transparent 70%); z-index:0; pointer-events:none; }
  .masthead > * { position:relative; z-index:1; }
  .tagline { color:var(--accent); font-size:15px; margin-top:12px; min-height:22px; font-style:italic; }
  .finding { border-left:3px solid var(--accent); padding:14px 0 14px 16px; margin:16px 0; border-top:0; }
  .finding h3 { font-size:16px; }
  .srcchip { display:inline-block; background:var(--accent-soft); color:var(--accent); font-size:11px; padding:3px 10px; border-radius:999px; margin:3px 6px 0 0; word-break:break-all; }
  .srcchip a { color:inherit; text-decoration:none; }
  .srcchip a:hover { text-decoration:underline; }
</style>
</head>
<body data-latest="{LATEST}" data-today="{TODAY}">
<div class="wrap">
  <header class="topbar">
    <div class="brand">
      <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 L21 6 V12 C21 17 17 21 12 22 C7 21 3 17 3 12 V6 Z" fill="#0068e6"/><path d="M8 12 l3 3 l5 -6" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
      <span data-i18n="brand">Citizen Agents</span>
    </div>
    <button id="langToggle" class="lang-toggle" onclick="toggleLang()" data-i18n="lang_label">EN</button>
  </header>

  <div class="masthead">
    <div class="coffee">{COFFEE}</div>
    <div class="kicker" data-i18n="hero_kicker">Breakfast Ticker</div>
    <h1 data-i18n="hero_title">Guten Morgen, Bürger:in.</h1>
    <div class="dateline"><span class="live"></span><span id="dateline"></span></div>
    <div id="tag" class="tagline"></div>
  </div>

  {CARDS}
  {TRUST}
  {SUPPORT}

  <footer>
    <span data-i18n="footer">Citizen Agents — Digital Democracy Studio, Berlin.</span><br>
    <a href="https://github.com/mikelninh/citizen-agents" data-i18n="footer_src">Quellcode &amp; Rohdaten</a> ·
    <a href="https://mikelninh.github.io/citizen-agents/" data-i18n="footer_home">Zur Startseite</a>
  </footer>
</div>
<script>
  var I18N = {
    de: {
      brand:"Citizen Agents",
      hero_kicker:"Breakfast Ticker",
      hero_title:"Guten Morgen, Bürger:in.",
      dateline:"Ausgabe {L} · erstellt {T} · jeden Morgen frisch",
      badge_watchdog:"WÄCHTER", badge_trust:"VERTRAUEN", badge_support:"UNTERSTÜTZEN",
      trust_title:"Vom Fleet-Reviewer geprüft",
      t_verified:"verifiziert", t_partial:"teilweise", t_failed:"fehlerhaft",
      trust_note:"Menschen prüfen, Agenten entwerfen — niemand merged automatisch. Jede Meldung trägt ihre Quelle.",
      support_title:"Kostenlos — und trotzdem nicht umsonst",
      support_intro:"Der Ticker bleibt für immer gratis. Server, Review und neue Wächter laufen über freiwillige Unterstützung. So sieht die Aufteilung aus:",
      tier_free_title:"🆓 Jeder Bürger",
      tier_free:["Täglicher Breakfast Ticker","Alle Quellen verlinkt","Trust-Panel (menschlich geprüft)","Keine Anmeldung, keine Paywall"],
      tier_pro_title:'⭐ „Dein Wächter"',
      soon:"in Planung",
      tier_pro:["Persönliche Alarme nach PLZ &amp; Lebenslage","Tiefere Digests + Archiv-Suche","Früher Zugang zu neuen Wächtern","API für Journalist:innen &amp; NGOs"],
      price:"ab 3 € / Monat",
      btn_sponsors:"☕ GitHub Sponsors (ab 1 €)",
      btn_org:"🤝 Für Organisationen &amp; NGOs",
      support_note:"Kostenlos. Für immer. Finanziert durch Menschen, die es ernst meinen.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Quellcode &amp; Rohdaten",
      footer_home:"Zur Startseite",
      sources:"Quellen:",
      lang_label:"EN",
      tags:["Frisch gebrüht aus öffentlichen Quellen.","Deine Rechte, täglich geprüft.","Kein Bezahlschutz vor deinen Rechten.","Wächter schlafen nicht — damit du ruhig schläfst."]
    },
    en: {
      brand:"Citizen Agents",
      hero_kicker:"Breakfast Ticker",
      hero_title:"Good morning, citizen.",
      dateline:"Issue {L} · built {T} · fresh every morning",
      badge_watchdog:"WATCHDOG", badge_trust:"TRUST", badge_support:"SUPPORT",
      trust_title:"Reviewed by the Fleet Reviewer",
      t_verified:"verified", t_partial:"partial", t_failed:"failed",
      trust_note:"Humans review, agents draft — nothing merges automatically. Every item carries its source.",
      support_title:"Free — and still not cheap",
      support_intro:"The ticker stays free forever. Servers, review and new watchdogs run on voluntary support. Here's the split:",
      tier_free_title:"🆓 Every citizen",
      tier_free:["Daily Breakfast Ticker","All sources linked","Trust panel (human-reviewed)","No sign-up, no paywall"],
      tier_pro_title:'⭐ "Your Watchdog"',
      soon:"planned",
      tier_pro:["Personal alerts by postcode &amp; situation","Deeper digests + archive search","Early access to new watchdogs","API for journalists &amp; NGOs"],
      price:"from €3 / month",
      btn_sponsors:"☕ GitHub Sponsors (from €1)",
      btn_org:"🤝 For organisations &amp; NGOs",
      support_note:"Free. Forever. Funded by people who mean it.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Source code &amp; raw data",
      footer_home:"To the homepage",
      sources:"Sources:",
      lang_label:"DE",
      tags:["Freshly brewed from public sources.","Your rights, checked daily.","No paywall in front of your rights.","Watchdogs don't sleep — so you can."]
    }
  };
  function fillList(id, arr){ var u=document.getElementById(id); if(!u) return; u.innerHTML = arr.map(function(x){return '<li>'+x+'</li>';}).join(''); }
  function applyLang(lang){
    var d = I18N[lang] || I18N.de;
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(function(el){ var k=el.getAttribute('data-i18n'); if(d[k]!=null) el.textContent=d[k]; });
    fillList('tierFree', d.tier_free);
    fillList('tierPro', d.tier_pro);
    var L=document.body.dataset.latest, T=document.body.dataset.today;
    var dl=document.getElementById('dateline'); if(dl) dl.textContent=d.dateline.replace('{L}',L).replace('{T}',T);
    var tg=document.getElementById('tag'); if(tg) tg.textContent=d.tags[Math.floor(Math.random()*d.tags.length)];
    var lt=document.getElementById('langToggle'); if(lt) lt.textContent=d.lang_label;
    try{ localStorage.setItem('ca_lang', lang); }catch(e){}
  }
  function toggleLang(){ var cur='de'; try{ cur=localStorage.getItem('ca_lang')||'de'; }catch(e){} applyLang(cur==='de'?'en':'de'); }
  (function(){ var s='de'; try{ s=localStorage.getItem('ca_lang')||'de'; }catch(e){} applyLang(s); })();
</script>
</body>
</html>"""


# ---- Personal-filter feed (P0/P1) -----------------------------------------
THEME_KEYWORDS = {
    "wohngeld": ["wohngeld"],
    "elterngeld": ["elterngeld"],
    "kindergeld": ["kindergeld"],
    "buergergeld": ["bürgergeld", "grundsicherung", "jobcenter"],
    "bauen_mieten": ["baugb", "miete", "wohn", "bau", "anhörung"],
    "eu": ["eu", "europa", "quanten", "halbleiter", "kommission"],
    "gerichte": ["urteil", "bverfg", "eugh", "gericht"],
    "lobby": ["lobby", "efuel", "verband"],
    "reise": ["reise", "flug", "eu261"],
}
LIFE_KEYWORDS = {
    "Mieter:in": ["wohngeld", "miete", "wohn", "baugb"],
    "Eltern/Familie": ["elterngeld", "kindergeld", "familie"],
    "Bürgergeld-Bezieher:in": ["bürgergeld", "grundsicherung", "jobcenter"],
}


def tag_text(text):
    low = text.lower()
    tags = [k for k, kws in THEME_KEYWORDS.items() if any(w in low for w in kws)]
    life = [l for l, kws in LIFE_KEYWORDS.items() if any(w in low for w in kws)]
    return tags, life


def build_feed(latest, digests, fr):
    items = []
    for d in digests:
        wd = d["title"].split("—", 1)[-1].strip() if "—" in d["title"] else d["title"]
        for f in d["findings"]:
            blob = f["headline"] + " " + " ".join(f["fields"].values())
            tags, life = tag_text(blob)
            items.append({
                "watchdog": wd,
                "headline": f["headline"],
                "what_changed": f["fields"].get("what changed", ""),
                "effective": f["fields"].get("effective", ""),
                "who_affected": f["fields"].get("who's affected", ""),
                "citizen_tip": f["fields"].get("citizen tip", ""),
                "why": f["fields"].get("why", ""),
                "how": f["fields"].get("how", ""),
                "deadline": f["fields"].get("deadline", ""),
                "sources": f["sources"],
                "tags": tags,
                "life": life,
            })
    totals = fr["totals"] if fr and fr["totals"] else {}
    return {"date": latest, "generated": date.today().isoformat(), "trust": totals, "items": items}


def main():
    dates = latest_digest_dates()
    if not dates:
        print("No digests found.")
        return
    latest = dates[0]
    print(f"Latest digest date: {latest}")
    digests = []
    for name in list_dir("agent-digests"):
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", name)
        if not dm or dm.group(1) != latest:
            continue
        if name.startswith("studio-") or name.startswith("fleet-review"):
            continue
        try:
            digests.append(parse_digest(get_text(f"{RAW}/agent-digests/{name}")))
        except Exception as e:
            print(f"skip {name}: {e}")
    fr = None
    try:
        fr = parse_fleet_review(get_text(f"{RAW}/agent-digests/fleet-review-{latest}.md"))
    except Exception as e:
        print(f"fleet-review: {e}")
    out = build_page(latest, digests, fr)
    with open("/Users/mikel/citizen-agents/breakfast.html", "w", encoding="utf-8") as fh:
        fh.write(out)
    feed = build_feed(latest, digests, fr)
    with open("/Users/mikel/citizen-agents/breakfast-feed.json", "w", encoding="utf-8") as fh:
        json.dump(feed, fh, ensure_ascii=False, indent=2)
    print(f"Wrote breakfast.html: {len(digests)} digests, trust={'yes' if fr and fr['totals'] else 'no'}.")
    print(f"Wrote breakfast-feed.json: {len(feed['items'])} filterable items.")


if __name__ == "__main__":
    main()
