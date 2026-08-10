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


def domain(url):
    m = re.match(r"https?://([^/]+)", url)
    host = m.group(1) if m else url
    host = host[4:] if host.startswith("www.") else host
    if host.startswith("xn--"):
        try:
            import codecs
            return codecs.decode(host, "idna_codec").decode("utf-8")
        except Exception:
            pass
    return host


def render_finding(f):
    fields_order = [("what changed", "Was hat sich geändert"), ("why", "Warum wichtig"),
                    ("effective", "Ab wann"), ("deadline", "Termin"),
                    ("who's affected", "Wen betrifft's"), ("how", "Wie mitmachen"),
                    ("citizen tip", "Tipp für dich")]
    out = [f'<article class="finding"><h3><span class="fnum">{esc(f["num"])}</span> <span>{esc(f["headline"])}</span></h3>']
    rows = []
    for key, label in fields_order:
        if key in f["fields"] and f["fields"][key]:
            rows.append(f'<div class="frow"><span class="lbl">{esc(label)}</span>'
                        f'<span class="fval">{esc(f["fields"][key])}</span></div>')
    if rows:
        out.append('<div class="flist">' + "".join(rows) + "</div>")
    if f["sources"]:
        out.append('<div class="sources"><span class="lbl" data-i18n="sources">Quellen:</span>')
        for u in f["sources"]:
            out.append(f'<span class="srcchip"><a href="{esc(u)}" target="_blank" rel="noopener" '
                       f'title="{esc(u)}">{esc(domain(u))}</a></span>')
        out.append("</div>")
    first = f["sources"][0] if f["sources"] else "https://github.com/mikelninh/citizen-agents"
    out.append('<div class="factions">'
               f'<a class="btn primary small" href="{esc(first)}" target="_blank" rel="noopener">🔎 Mehr erfahren</a>'
               '<a class="btn ghost small" href="https://github.com/mikelninh/citizen-agents/discussions" '
               'target="_blank" rel="noopener">❓ Frage stellen</a></div>')
    out.append("</article>")
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
          <div class="table-scroll"><table class="verdicts"><tr><th>Wächter</th><th>Urteil</th><th>Kurzbegründung</th></tr>{verdict_rows}</table></div>
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
  :root{
    --bg:#f5f3f1; --card:#ffffff; --ink:#171a21; --navy:#02083a; --muted:#5b6472;
    --accent:#0068e6; --accent-soft:#e8f0ff; --ok:#1a7f4b; --ok-soft:#e6f4ec;
    --warn:#9a6400; --warn-soft:#fdf3e0; --bad:#c4322b; --bad-soft:#fdeaea;
    --line:#e7e3df; --line-soft:#f0edea;
    --radius:20px; --radius-sm:14px;
    --shadow:0 1px 2px rgba(2,8,58,.04), 0 10px 30px rgba(2,8,58,.06);
  }
  *{ box-sizing:border-box; }
  html{ -webkit-text-size-adjust:100%; }
  body{ margin:0; background:var(--bg); color:var(--ink);
    font:17px/1.65 "Onest",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased; }
  a{ color:var(--accent); }
  :focus-visible{ outline:3px solid var(--accent); outline-offset:2px; border-radius:6px; }
  .wrap{ max-width:800px; margin:0 auto; padding:20px 20px 96px; }

  /* topbar */
  .topbar{ display:flex; align-items:center; justify-content:space-between; gap:14px;
    flex-wrap:wrap; padding:10px 0 6px; }
  .brand{ display:flex; align-items:center; gap:10px; font-weight:700; color:var(--navy);
    font-size:15px; letter-spacing:-.2px; }
  .brand-mark{ width:24px; height:24px; flex:none; }

  /* language bar */
  .lang-bar{ display:flex; flex-wrap:wrap; gap:6px; align-items:center;
    background:#fff; border:1px solid var(--line); border-radius:999px; padding:4px; box-shadow:var(--shadow); }
  .lang-btn{ border:0; background:transparent; color:var(--muted); font:inherit; font-weight:700;
    font-size:12.5px; letter-spacing:.4px; padding:6px 12px; border-radius:999px; cursor:pointer;
    transition:background .15s, color .15s; }
  .lang-btn:hover{ background:var(--accent-soft); color:var(--accent); }
  .lang-btn.active{ background:var(--accent); color:#fff; }

  /* auto translation note */
  .auto-note{ font-size:13.5px; line-height:1.5; color:var(--warn); background:var(--warn-soft);
    border:1px solid #f0dcb4; border-inline-start:4px solid var(--warn);
    padding:12px 16px; border-radius:var(--radius-sm); margin:14px 0 0; }

  /* hero */
  .masthead{ position:relative; text-align:center; padding:34px 0 30px; }
  .masthead::before{ content:""; position:absolute; inset:-40px -24px auto -24px; height:300px;
    background:radial-gradient(120% 100% at 50% 0, rgba(0,104,230,.10), transparent 72%);
    z-index:0; pointer-events:none; }
  .masthead > *{ position:relative; z-index:1; }
  .coffee, .coffee svg{ width:60px; height:60px; display:block; margin:0 auto 14px; }
  .steam{ animation:rise 3s ease-in-out infinite; }
  .steam.s2{ animation-delay:.6s; }
  @keyframes rise{ 0%{opacity:0;transform:translateY(4px)} 40%{opacity:.8} 100%{opacity:0;transform:translateY(-6px)} }
  .kicker{ letter-spacing:2.4px; font-size:11px; color:var(--accent); text-transform:uppercase; font-weight:800; }
  h1{ font-size:clamp(30px,6vw,42px); line-height:1.12; margin:12px 0 12px; color:var(--navy); letter-spacing:-1px; font-weight:800; }
  .dateline{ display:inline-flex; align-items:center; gap:8px; color:var(--muted); font-size:14px;
    background:#fff; border:1px solid var(--line); border-radius:999px; padding:6px 14px; box-shadow:var(--shadow); }
  .tagline{ color:var(--navy); opacity:.85; font-size:16px; margin-top:16px; min-height:24px; font-style:italic; }
  .live{ display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--ok); flex:none;
    box-shadow:0 0 0 0 rgba(26,127,75,.5); animation:pulse 2s infinite; }
  @keyframes pulse{ 0%{box-shadow:0 0 0 0 rgba(26,127,75,.5)} 70%{box-shadow:0 0 0 9px rgba(26,127,75,0)} 100%{box-shadow:0 0 0 0 rgba(26,127,75,0)} }
  @media (prefers-reduced-motion:reduce){ .live,.steam{ animation:none; } }

  /* cards */
  .card{ background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:26px 28px; margin:22px 0; box-shadow:var(--shadow); }
  .card-head{ display:flex; align-items:center; gap:14px; margin-bottom:14px; }
  .card-head h2{ margin:6px 0 0; font-size:21px; line-height:1.25; color:var(--navy); letter-spacing:-.4px; }
  .mascot{ width:42px; height:42px; flex:none; }
  .badge{ display:inline-block; background:var(--accent-soft); color:var(--accent); font-size:10.5px;
    font-weight:800; letter-spacing:1.2px; padding:4px 11px; border-radius:999px; text-transform:uppercase; }
  .trust-badge{ background:#e9ebf5; color:var(--navy); }
  .sup-badge{ background:#fde7ef; color:#b23a68; }
  .intro{ color:var(--muted); margin:0 0 8px; font-size:16px; }

  /* findings */
  .findings{ margin-top:6px; }
  .finding{ border-top:1px solid var(--line-soft); padding:22px 0 6px; }
  .finding:first-child{ border-top:0; padding-top:8px; }
  .finding h3{ margin:0 0 12px; font-size:18px; line-height:1.35; color:var(--navy);
    display:flex; gap:10px; align-items:baseline; font-weight:700; letter-spacing:-.3px; }
  .fnum{ background:var(--navy); color:#fff; font-size:12px; font-weight:800; border-radius:999px;
    padding:2px 10px; flex:none; }
  .flist{ margin:0; display:grid; gap:10px; }
  .flist .frow{ display:block; }
  .lbl{ display:block; color:var(--muted); font-weight:700; font-size:11px; letter-spacing:1px;
    text-transform:uppercase; margin-bottom:2px; }
  .fval{ display:block; line-height:1.6; }
  .sources{ margin-top:16px; }
  .sources .lbl{ margin-bottom:6px; }
  .srcchip{ display:inline-block; margin:0 6px 6px 0; }
  .srcchip a{ display:inline-block; background:var(--bg); border:1px solid var(--line); color:var(--navy);
    font-size:12.5px; font-weight:600; padding:5px 12px; border-radius:999px; text-decoration:none;
    transition:.15s; max-width:100%; overflow-wrap:anywhere; }
  .srcchip a:hover{ border-color:var(--accent); color:var(--accent); background:var(--accent-soft); }
  .factions{ display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
  .bottom{ border-top:1px solid var(--line-soft); margin-top:18px; padding-top:16px;
    font-size:16px; color:var(--navy); }

  /* trust */
  .trust-totals{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:16px 0 20px; }
  .trust-totals .t{ text-align:center; background:var(--bg); border:1px solid var(--line);
    border-radius:var(--radius-sm); padding:16px 8px; }
  .trust-totals b{ font-size:28px; display:block; line-height:1.1; color:var(--navy); }
  .trust-totals span{ font-size:12px; color:var(--muted); }
  .trust-totals .ok b{ color:var(--ok); } .trust-totals .warn b{ color:var(--warn); } .trust-totals .bad b{ color:var(--bad); }
  .table-scroll{ overflow-x:auto; }
  table.verdicts{ width:100%; border-collapse:collapse; font-size:14px; }
  table.verdicts th, table.verdicts td{ text-align:start; padding:11px 10px; border-top:1px solid var(--line-soft); vertical-align:top; }
  table.verdicts th{ color:var(--muted); font-weight:700; font-size:11px; letter-spacing:1px; text-transform:uppercase; border-top:0; }
  .pill{ display:inline-block; font-size:11px; font-weight:800; padding:3px 10px; border-radius:999px; white-space:nowrap; }
  .pill.ok{ background:var(--ok-soft); color:var(--ok); }
  .pill.warn{ background:var(--warn-soft); color:var(--warn); }
  .pill.bad{ background:var(--bad-soft); color:var(--bad); }
  .note{ color:var(--muted); font-size:14px; margin-top:16px; }

  /* support */
  .tiers{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin:18px 0; }
  .tier{ background:var(--bg); border:1px solid var(--line); border-radius:var(--radius-sm); padding:20px 22px; }
  .tier h3{ margin:0 0 12px; font-size:17px; color:var(--navy); }
  .tier ul{ margin:0; padding-inline-start:20px; }
  .tier li{ margin:8px 0; }
  .tier.pro{ background:#fff; border-color:var(--accent); box-shadow:0 0 0 3px rgba(0,104,230,.08); }
  .soon{ font-size:10px; background:var(--accent-soft); color:var(--accent); padding:3px 9px;
    border-radius:999px; vertical-align:middle; font-weight:800; letter-spacing:.5px; }
  .price{ margin-top:14px; font-weight:800; color:var(--accent); }
  .donate-row{ display:flex; gap:12px; flex-wrap:wrap; margin-top:10px; }
  .btn{ display:inline-flex; align-items:center; gap:8px; padding:12px 20px; border-radius:999px;
    font-weight:700; text-decoration:none; font-size:14.5px; transition:.15s; border:1px solid transparent; }
  .btn.primary{ background:var(--accent); color:#fff; }
  .btn.primary:hover{ background:#0057c2; }
  .btn.ghost{ background:#fff; color:var(--navy); border-color:var(--line); }
  .btn.ghost:hover{ border-color:var(--accent); color:var(--accent); }
  .btn.small{ padding:9px 16px; font-size:13.5px; }
  .btn:hover{ transform:translateY(-1px); }

  footer{ color:var(--muted); font-size:14px; text-align:center; margin-top:44px; line-height:1.9; }
  footer a{ color:var(--accent); text-decoration:none; }
  footer a:hover{ text-decoration:underline; }

  [dir="rtl"] .finding h3{ text-align:right; }
  [dir="rtl"] .kicker, [dir="rtl"] .lbl{ letter-spacing:0; }

  @media (max-width:620px){
    body{ font-size:16px; }
    .wrap{ padding:12px 15px 72px; }
    .card{ padding:20px 18px; border-radius:18px; }
    .card-head{ gap:10px; }
    .trust-totals{ grid-template-columns:1fr; }
    .btn{ width:100%; justify-content:center; }
  }
</style>
</head>
<body data-latest="{LATEST}" data-today="{TODAY}">
<div class="wrap">
  <header class="topbar">
    <div class="brand">
      <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 L21 6 V12 C21 17 17 21 12 22 C7 21 3 17 3 12 V6 Z" fill="#0068e6"/><path d="M8 12 l3 3 l5 -6" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
      <span data-i18n="brand">Citizen Agents</span>
    </div>
    <nav class="lang-bar" id="langBar" aria-label="Sprache"></nav>
  </header>

  <div id="autoNote" class="auto-note" role="status" style="display:none"></div>

  <main>
  <div class="masthead">
    <div class="coffee">{COFFEE}</div>
    <p class="kicker" data-i18n="hero_kicker">Breakfast Ticker</p>
    <h1 data-i18n="hero_title">Guten Morgen, Bürger:in.</h1>
    <p class="dateline"><span class="live" aria-hidden="true"></span><span id="dateline"></span></p>
    <p id="tag" class="tagline"></p>
  </div>

  {CARDS}
  {TRUST}
  {SUPPORT}
  </main>

  <footer>
    <span data-i18n="footer">Citizen Agents — Digital Democracy Studio, Berlin.</span><br>
    <a href="https://github.com/mikelninh/citizen-agents" data-i18n="footer_src">Quellcode &amp; Rohdaten</a> ·
    <a href="https://mikelninh.github.io/citizen-agents/" data-i18n="footer_home">Zur Startseite</a>
  </footer>
</div>
<script>
  // Priority languages for Germany's affected communities.
  // DE + EN are source-of-truth (watchdogs will produce these).
  // TR, RU, AR, VI, PL are auto-translated — flagged honestly on screen.
  var LANGS = [
    {code:"de", label:"DE", auto:false},
    {code:"en", label:"EN", auto:false},
    {code:"tr", label:"TR", auto:true},
    {code:"ru", label:"RU", auto:true},
    {code:"ar", label:"AR", auto:true},
    {code:"vi", label:"VI", auto:true},
    {code:"pl", label:"PL", auto:true}
  ];
  var I18N = {
    de: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Guten Morgen, Bürger:in.",
      dateline:"Ausgabe {L} · erstellt {T} · jeden Morgen frisch",
      badge_watchdog:"WÄCHTER", badge_trust:"VERTRAUEN", badge_support:"UNTERSTÜTZEN",
      trust_title:"Vom Fleet-Reviewer geprüft",
      t_verified:"verifiziert", t_partial:"teilweise", t_failed:"fehlerhaft",
      trust_note:"Menschen prüfen, Agenten entwerfen — niemand merges automatisch. Jede Meldung trägt ihre Quelle.",
      support_title:"Kostenlos — und trotzdem nicht umsonst",
      support_intro:"Der Ticker bleibt für immer gratis. Server, Review und neue Wächter laufen über freiwillige Unterstützung. So sieht die Aufteilung aus:",
      tier_free_title:"🆓 Jeder Bürger",
      tier_free:["Täglicher Breakfast Ticker","Alle Quellen verlinkt","Trust-Panel (menschlich geprüft)","Keine Anmeldung, keine Paywall"],
      tier_pro_title:'⭐ „Dein Wächter“', soon:"in Planung",
      tier_pro:["Persönliche Alarme nach PLZ &amp; Lebenslage","Tiefere Digests + Archiv-Suche","Früher Zugang zu neuen Wächtern","API für Journalist:innen &amp; NGOs"],
      price:"ab 3 € / Monat",
      btn_sponsors:"☕ GitHub Sponsors (ab 1 €)", btn_org:"🤝 Für Organisationen &amp; NGOs",
      support_note:"Kostenlos. Für immer. Finanziert durch Menschen, die es ernst meinen.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Quellcode &amp; Rohdaten", footer_home:"Zur Startseite",
      sources:"Quellen:", auto_flag:"Automatisch übersetzt — bitte mit der offiziellen Quelle abgleichen.",
      tags:["Frisch gebrüht aus öffentlichen Quellen.","Deine Rechte, täglich geprüft.","Kein Bezahlschutz vor deinen Rechten.","Wächter schlafen nicht — damit du ruhig schläfst."]
    },
    en: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Good morning, citizen.",
      dateline:"Issue {L} · built {T} · fresh every morning",
      badge_watchdog:"WATCHDOG", badge_trust:"TRUST", badge_support:"SUPPORT",
      trust_title:"Reviewed by the Fleet Reviewer",
      t_verified:"verified", t_partial:"partial", t_failed:"failed",
      trust_note:"Humans review, agents draft — nothing merges automatically. Every item carries its source.",
      support_title:"Free — but not without cost",
      support_intro:"The ticker stays free forever. Servers, review and new watchdogs run on voluntary support. Here's the split:",
      tier_free_title:"🆓 Every citizen",
      tier_free:["Daily Breakfast Ticker","All sources linked","Trust panel (human-reviewed)","No sign-up, no paywall"],
      tier_pro_title:'⭐ "Your Watchdog"', soon:"planned",
      tier_pro:["Personal alerts by postcode &amp; situation","Deeper digests + archive search","Early access to new watchdogs","API for journalists &amp; NGOs"],
      price:"from €3 / month",
      btn_sponsors:"☕ GitHub Sponsors (from €1)", btn_org:"🤝 For organisations &amp; NGOs",
      support_note:"Free. Forever. Funded by people who mean it.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Source code &amp; raw data", footer_home:"To the homepage",
      sources:"Sources:", auto_flag:"Automatically translated — please verify against the official source.",
      tags:["Freshly brewed from public sources.","Your rights, checked daily.","No paywall in front of your rights.","Watchdogs don't sleep — so you can."]
    },
    tr: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Günaydın, vatandaş.",
      dateline:"Sayı {L} · {T} tarihinde hazırlandı · her sabah taze",
      badge_watchdog:"BEKÇİ", badge_trust:"GÜVEN", badge_support:"DESTEK",
      trust_title:"Fleet Reviewer tarafından incelendi",
      t_verified:"doğrulandı", t_partial:"kısmen", t_failed:"hatalı",
      trust_note:"İnsanlar inceler, ajanlar taslak hazırlar — hiçbiri otomatik birleştirilmez. Her kaydın kaynağı belirtilir.",
      support_title:"Ücretsiz — ama yine de bedava değil",
      support_intro:"Ticker sonsuza dek ücretsiz kalır. Sunucular, inceleme ve yeni bekçiler gönüllü destekle yürür. Bölünme şöyle:",
      tier_free_title:"🆓 Her vatandaş",
      tier_free:["Günlük Breakfast Ticker","Tüm kaynaklar bağlantılı","Güven paneli (insan inceledi)","Kayıt yok, ödeme duvarı yok"],
      tier_pro_title:'⭐ "Senin Bekçin"', soon:"planlama aşamasında",
      tier_pro:["Posta kodu ve yaşam durumuna göre kişisel uyarılar","Daha derin özetler + arşiv arama","Yeni bekçilere erken erişim","Gazeteciler ve STK'lar için API"],
      price:"aylık 3 €'dan",
      btn_sponsors:"☕ GitHub Sponsors (1 €'dan)", btn_org:"🤝 Kurumlar ve STK'lar için",
      support_note:"Ücretsiz. Sonsuza dek. Bunu ciddiye alan insanlar tarafından finanse edilir.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Kaynak kodu ve ham veri", footer_home:"Ana sayfaya",
      sources:"Kaynaklar:", auto_flag:"Otomatik çevrilmiştir — lütfen resmi kaynakla karşılaştırın.",
      tags:["Taze kamu kaynaklarından demlendi.","Hakların her gün incelenir.","Haklarının önünde ödeme duvarı yok.","Bekçiler uyumaz — sen rahat uyu."]
    },
    ru: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Доброе утро, гражданин.",
      dateline:"Выпуск {L} · создан {T} · свежий каждое утро",
      badge_watchdog:"СТРАЖ", badge_trust:"ДОВЕРИЕ", badge_support:"ПОДДЕРЖКА",
      trust_title:"Проверено Fleet Reviewer",
      t_verified:"подтверждено", t_partial:"частично", t_failed:"ошибка",
      trust_note:"Люди проверяют, агенты составляют черновики — ничего не сливается автоматически. У каждой записи указан источник.",
      support_title:"Бесплатно — но не бесполезно",
      support_intro:"Тикер остаётся бесплатным навсегда. Серверы, проверка и новые стражи работают на добровольной поддержке. Вот как это распределяется:",
      tier_free_title:"🆓 Каждый гражданин",
      tier_free:["Ежедневный Breakfast Ticker","Все источники по ссылкам","Панель доверия (проверено человеком)","Без регистрации, без платного доступа"],
      tier_pro_title:'⭐ «Твой страж»', soon:"в планах",
      tier_pro:["Персональные уведомления по индексу и ситуации","Более глубокие дайджесты + поиск по архиву","Ранний доступ к новым стражам","API для журналистов и НКО"],
      price:"от 3 € / месяц",
      btn_sponsors:"☕ GitHub Sponsors (от 1 €)", btn_org:"🤝 Для организаций и НКО",
      support_note:"Бесплатно. Навсегда. Финансируется людьми, которые относятся к этому серьёзно.",
      footer:"Citizen Agents — Digital Democracy Studio, Берлин.",
      footer_src:"Исходный код и сырые данные", footer_home:"На главную",
      sources:"Источники:", auto_flag:"Переведено автоматически — пожалуйста, сверьтесь с официальным источником.",
      tags:["Свежезаварено из открытых источников.","Ваши права проверяются ежедневно.","Перед вашими правами нет платной стены.","Стражи не спят — спите спокойно."]
    },
    ar: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"صباح الخير، أيها المواطن.",
      dateline:"العدد {L} · أُعد في {T} · طازج كل صباح",
      badge_watchdog:"حارس", badge_trust:"ثقة", badge_support:"دعم",
      trust_title:"تمت المراجعة بواسطة Fleet Reviewer",
      t_verified:"مؤكد", t_partial:"جزئي", t_failed:"خطأ",
      trust_note:"البشر يراجعون، والوكلاء يصيغون — لا شيء يُدمج تلقائياً. كل مدخل له مصدره.",
      support_title:"مجاني — ولكنه ليس بلا ثمن",
      support_intro:"يبقى التيكر مجانياً للأبد. الخوادم والمراجعة والحراس الجدد تعمل بالدعم التطوعي. إليك التوزيع:",
      tier_free_title:"🆓 كل مواطن",
      tier_free:["تيكر الإفطار اليومي","كل المصادر مرتبطة","لوحة الثقة (راجعها إنسان)","بدون تسجيل، بدون جدار دفع"],
      tier_pro_title:'⭐ «حارسك»', soon:"قيد التخطيط",
      tier_pro:["تنبيهات شخصية حسب الرمز البريدي والوضع","ملخصات أعمق + بحث في الأرشيف","وصول مبكر للحراس الجدد","واجهة برمجة للصحفيين والمنظمات"],
      price:"من 3 € / شهر",
      btn_sponsors:"☕ GitHub Sponsors (من 1 €)", btn_org:"🤝 للمنظمات والجمعيات",
      support_note:"مجاني. للأبد. يُموَّل من أناس يأخذون الأمر بجدية.",
      footer:"Citizen Agents — استوديو الديمقراطية الرقمية، برلين.",
      footer_src:"الكود المصدري والبيانات الخام", footer_home:"إلى الصفحة الرئيسية",
      sources:"المصادر:", auto_flag:"تُرجم آلياً — يرجى التحقق من المصدر الرسمي.",
      tags:["مُعدّ طازجاً من مصادر عامة.","حقوقك تُراجع يومياً.","لا جدار دفع أمام حقوقك.","الحراس لا ينامون — لترقد بسلام."]
    },
    vi: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Chào buổi sáng, công dân.",
      dateline:"Số {L} · lập ngày {T} · tươi mới mỗi sáng",
      badge_watchdog:"CANH GÁC", badge_trust:"TIN CẬY", badge_support:"HỖ TRỢ",
      trust_title:"Được Fleet Reviewer kiểm duyệt",
      t_verified:"đã xác minh", t_partial:"một phần", t_failed:"lỗi",
      trust_note:"Con người xem xét, tác nhân soạn thảo — không có gì tự động hợp nhất. Mỗi mục đều ghi rõ nguồn.",
      support_title:"Miễn phí — nhưng không phải không tốn kém",
      support_intro:"Bản tin luôn miễn phí mãi mãi. Máy chủ, kiểm duyệt và các canh gác mới chạy bằng sự hỗ trợ tự nguyện. Cách phân bổ như sau:",
      tier_free_title:"🆓 Mọi công dân",
      tier_free:["Bản tin Breakfast hàng ngày","Tất cả nguồn được liên kết","Bảng tin cậy (do người xem xét)","Không đăng ký, không tường phí"],
      tier_pro_title:'⭐ „Người canh gác của bạn“', soon:"đang lên kế hoạch",
      tier_pro:["Cảnh báo cá nhân theo mã bưu chính & hoàn cảnh","Bản tóm tắt sâu hơn + tìm kiếm lưu trữ","Truy cập sớm các canh gác mới","API cho nhà báo & NGO"],
      price:"từ 3 € / tháng",
      btn_sponsors:"☕ GitHub Sponsors (từ 1 €)", btn_org:"🤝 Dành cho tổ chức & NGO",
      support_note:"Miễn phí. Mãi mãi. Được tài trợ bởi những người nghiêm túc.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Mã nguồn & dữ liệu thô", footer_home:"Về trang chủ",
      sources:"Nguồn:", auto_flag:"Được dịch tự động — vui lòng đối chiếu với nguồn chính thức.",
      tags:["Pha tươi từ nguồn công khai.","Quyền của bạn được kiểm tra hàng ngày.","Không có tường phí trước quyền của bạn.","Canh gác không ngủ — để bạn ngủ ngon."]
    },
    pl: {
      brand:"Citizen Agents", hero_kicker:"Breakfast Ticker", hero_title:"Dzień dobry, obywatelu.",
      dateline:"Wydanie {L} · utworzono {T} · świeże każdego ranka",
      badge_watchdog:"STRAŻNIK", badge_trust:"ZAUFANIE", badge_support:"WSPARCIE",
      trust_title:"Sprawdzone przez Fleet Reviewer",
      t_verified:"potwierdzone", t_partial:"częściowo", t_failed:"błąd",
      trust_note:"Ludzie sprawdzają, agenci redagują — nic nie jest scalane automatycznie. Każdy wpis ma podane źródło.",
      support_title:"Bezpłatne — ale nie za darmo",
      support_intro:"Ticker pozostaje bezpłatny na zawsze. Serwery, przegląd i nowi strażnicy działają dzięki dobrowolnemu wsparciu. Oto podział:",
      tier_free_title:"🆓 Każdy obywatel",
      tier_free:["Codzienny Breakfast Ticker","Wszystkie źródła podlinkowane","Panel zaufania (przeglądane przez człowieka)","Bez rejestracji, bez paywalla"],
      tier_pro_title:'⭐ „Twój Strażnik”', soon:"w planach",
      tier_pro:["Osobiste alerty według kodu pocztowego i sytuacji","Głębsze skróty + wyszukiwanie w archiwum","Wczesny dostęp do nowych strażników","API dla dziennikarzy i NGO"],
      price:"od 3 € / miesiąc",
      btn_sponsors:"☕ GitHub Sponsors (od 1 €)", btn_org:"🤝 Dla organizacji i NGO",
      support_note:"Bezpłatne. Na zawsze. Finansowane przez ludzi, którzy traktują to poważnie.",
      footer:"Citizen Agents — Digital Democracy Studio, Berlin.",
      footer_src:"Kod źródłowy i surowe dane", footer_home:"Strona główna",
      sources:"Źródła:", auto_flag:"Przetłumaczono automatycznie — proszę zweryfikować ze źródłem oficjalnym.",
      tags:["Świeżo zaparzone z publicznych źródeł.","Twoje prawa sprawdzane codziennie.","Przed twoimi prawami nie ma paywalla.","Strażnicy nie śpią — ty śpij spokojnie."]
    }
  };
  function fillList(id, arr){ var u=document.getElementById(id); if(!u) return; u.innerHTML = arr.map(function(x){return '<li>'+x+'</li>';}).join(''); }
  function buildLangBar(){
    var bar=document.getElementById('langBar'); if(!bar) return;
    bar.innerHTML='';
    LANGS.forEach(function(L){
      var b=document.createElement('button');
      b.className='lang-btn'+( (getLang()===L.code)?' active':'' );
      b.textContent=L.label;
      b.onclick=function(){ setLang(L.code); };
      bar.appendChild(b);
    });
  }
  function getLang(){ try{ return localStorage.getItem('ca_lang')||'de'; }catch(e){ return 'de'; } }
  function setLang(code){ try{ localStorage.setItem('ca_lang', code); }catch(e){} applyLang(code); }
  function applyLang(lang){
    var d = I18N[lang] || I18N.de;
    var meta = LANGS.find(function(L){return L.code===lang;}) || {auto:false};
    document.documentElement.lang = lang;
    document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';
    document.querySelectorAll('[data-i18n]').forEach(function(el){ var k=el.getAttribute('data-i18n'); if(d[k]!=null) el.textContent=d[k]; });
    fillList('tierFree', d.tier_free);
    fillList('tierPro', d.tier_pro);
    var L=document.body.dataset.latest, T=document.body.dataset.today;
    var dl=document.getElementById('dateline'); if(dl) dl.textContent=d.dateline.replace('{L}',L).replace('{T}',T);
    var tg=document.getElementById('tag'); if(tg) tg.textContent=d.tags[Math.floor(Math.random()*d.tags.length)];
    var an=document.getElementById('autoNote');
    if(an){ if(meta.auto){ an.style.display='block'; an.textContent='⚠️ '+d.auto_flag; } else { an.style.display='none'; } }
    buildLangBar();
  }
  (function(){ applyLang(getLang()); })();
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
