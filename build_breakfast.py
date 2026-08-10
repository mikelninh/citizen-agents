#!/usr/bin/env python3
"""
Breakfast Ticker builder for Citizen Agents.

Fetches the latest agent-digests + fleet-review from the citizen-agents repo,
parses them into citizen-friendly "breakfast" cards with cited sources and a
human-review trust score, and emits a self-contained, friendly breakfast.html.

Stdlib only. Re-run by the daily cron so the page stays current.
"""
import json
import os
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

# Opt-in local mode for testing: CA_LOCAL_DIGESTS=1 reads agent-digests/ from disk
# instead of GitHub raw. Default (unset) keeps the original remote behaviour.
LOCAL_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIGESTS = os.environ.get("CA_LOCAL_DIGESTS") == "1"


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def get_text(url):
    if LOCAL_DIGESTS and url.startswith(RAW + "/"):
        p = os.path.join(LOCAL_ROOT, url[len(RAW) + 1:])
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                return fh.read()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def list_dir(path):
    if LOCAL_DIGESTS and path == "agent-digests":
        p = os.path.join(LOCAL_ROOT, "agent-digests")
        if os.path.isdir(p):
            return sorted(n for n in os.listdir(p) if n.endswith(".md"))
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


# ---- bilingual content layer ----------------------------------------------
# Digest convention:
#   A finding starts with "## <n>. <German headline>" followed by the usual
#   German "- **Field:** value" lines. A watchdog MAY append an English block:
#
#       ### EN
#       - **Headline:** English headline
#       - **What changed:** ...
#       - **Why:** ...            (aliases: "Why it matters")
#       - **Effective:** ...      (alias: "In effect")
#       - **Deadline:** ...
#       - **Who's affected:** ...
#       - **How:** ...            (alias: "How to act")
#       - **Citizen tip:** ...    (alias: "Tip")
#
#   Sources stay shared (declared once, in the German part). The EN block ends
#   at the next "## " finding or "### Bottom line".
EN_HEADS = re.compile(r"^###\s*(EN|ENGLISH)\b", re.I)
DE_HEADS = re.compile(r"^###\s*(DE|DEUTSCH|GERMAN)\b", re.I)

FIELD_ALIASES = {
    "why it matters": "why",
    "warum wichtig": "why",
    "in effect": "effective",
    "in effect from": "effective",
    "how to act": "how",
    "wie mitmachen": "how",
    "termin": "deadline",
    "tip": "citizen tip",
    "tip for you": "citizen tip",
    "who is affected": "who's affected",
}

CONTENT_KEYS = [
    ("what changed", "what_changed"), ("why", "why"), ("effective", "effective"),
    ("deadline", "deadline"), ("who's affected", "who_affected"),
    ("how", "how"), ("citizen tip", "citizen_tip"),
]

LABELS = {
    "de": {"what changed": "Was hat sich geändert", "why": "Warum wichtig",
           "effective": "Ab wann", "deadline": "Termin",
           "who's affected": "Wen betrifft's", "how": "Wie mitmachen",
           "citizen tip": "Tipp für dich"},
    "en": {"what changed": "What changed", "why": "Why it matters",
           "effective": "In effect from", "deadline": "Deadline",
           "who's affected": "Who's affected", "how": "How to act",
           "citizen tip": "Tip for you"},
}


def norm_key(key):
    return FIELD_ALIASES.get(key, key)


def lang_block(f, lang):
    """Flat {headline, what_changed, ...} object for one language."""
    fields = f.get("en_fields") if lang == "en" else f.get("fields")
    fields = fields or {}
    head = f.get("en_headline") if lang == "en" else f.get("headline")
    obj = {"headline": head or f.get("headline", "")}
    for src, dst in CONTENT_KEYS:
        obj[dst] = fields.get(src, "")
    return obj


def has_en(f):
    return bool(f.get("en_fields")) or bool(f.get("en_headline"))


def parse_digest(md):
    lines = md.splitlines()
    title = ""
    date = ""
    intro = []
    findings = []
    bottom = []
    in_bottom = False
    cur = None
    lang_mode = "de"
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
            cur = {"num": m.group(1), "headline": m.group(2).strip(), "fields": {},
                   "en_fields": {}, "en_headline": "", "sources": []}
            lang_mode = "de"
            i += 1
            continue
        if cur is not None and EN_HEADS.match(line):
            lang_mode = "en"
            i += 1
            continue
        if cur is not None and DE_HEADS.match(line):
            lang_mode = "de"
            i += 1
            continue
        if cur is not None:
            fm = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)", line)
            if fm:
                key = norm_key(fm.group(1).strip().lower())
                val = fm.group(2).strip()
                if lang_mode == "en":
                    if key in ("sources", "quelle", "source", "quellen"):
                        cur["sources"].extend(extract_urls(val))
                        j = i + 1
                        while j < len(lines) and lines[j].strip().startswith("-") and "http" in lines[j]:
                            cur["sources"].extend(extract_urls(lines[j]))
                            j += 1
                        i = j
                        continue
                    if key == "headline":
                        cur["en_headline"] = val
                    else:
                        cur.setdefault("en_fields", {})[key] = val
                    i += 1
                    continue
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
            import idna
            return idna.decode(host)
        except Exception:
            pass
    return host


def finding_id(prefix, f):
    return f"finding-{prefix}-{re.sub(r'[^0-9a-zA-Z]', '', str(f['num'])) or '0'}"


def content_payload(f):
    """{de:{headline, rows:[[label,value],...]}, en:{...}} for client-side lang switch."""
    pay = {}
    for lang in ("de", "en"):
        if lang == "en" and not has_en(f):
            continue
        fields = f.get("en_fields") if lang == "en" else f.get("fields", {})
        fields = fields or {}
        head = (f.get("en_headline") or f.get("headline", "")) if lang == "en" else f.get("headline", "")
        rows = [[LABELS[lang][k], fields[k]] for k, _dst in CONTENT_KEYS if fields.get(k)]
        pay[lang] = {"headline": head, "rows": rows}
    return pay


def render_finding(f, prefix=0):
    fields_order = [(k, LABELS["de"][k]) for k, _dst in CONTENT_KEYS]
    fid = finding_id(prefix, f)
    payload = esc(json.dumps(content_payload(f), ensure_ascii=False))
    out = [f'<article class="finding" id="{fid}" tabindex="-1" data-content="{payload}">'
           f'<h3><span class="fnum" aria-hidden="true">{esc(f["num"])}</span> <span class="fhead">{esc(f["headline"])}</span></h3>']
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
    for di, d in enumerate(digests):
        emoji = ""
        em = re.match(r"^#\s+(\S+)\s", d["title"])
        if em:
            emoji = em.group(1)
        findings_html = "\n".join(render_finding(f, di) for f in d["findings"])
        toc = ""
        if len(d["findings"]) >= 3:
            links = "".join(
                f'<li><a href="#{finding_id(di, f)}"><span class="tocnum">{esc(f["num"])}</span>'
                f'<span class="toctxt">{esc(f["headline"])}</span></a></li>'
                for f in d["findings"])
            toc = ('<nav class="toc" aria-label="Übersicht der Meldungen">'
                   f'<p class="toc-h">Auf einen Blick · {len(d["findings"])}</p>'
                   f'<ol class="toc-list">{links}</ol></nav>')
        bottom = f'<div class="bottom">{esc(d["bottom_line"])}</div>' if d["bottom_line"] else ""
        intro = f'<p class="intro">{esc(d["intro"])}</p>' if d["intro"] else ""
        cards.append(f"""
        <section class="card">
          <header class="card-head">{WATCHDOG_SVG}<div><span class="badge" data-i18n="badge_watchdog">WÄCHTER</span>
            <h2>{emoji} {esc(d['title'].split('—',1)[-1].strip())}</h2></div></header>
          {intro}
          {toc}
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
    --bg:#f5f3f1; --card:#ffffff; --ink:#161a22; --navy:#02083a; --muted:#4f5866;
    --accent:#0068e6; --accent-soft:#e8f0ff; --ok:#166b40; --ok-soft:#e6f4ec;
    --warn:#845400; --warn-soft:#fdf3e0; --bad:#b32a24; --bad-soft:#fdeaea;
    --line:#e7e3df; --line-soft:#f0edea;
    --radius:20px; --radius-sm:14px;
    --measure:74ch;
    --shadow:0 1px 2px rgba(2,8,58,.04), 0 10px 30px rgba(2,8,58,.06);
    --shadow-lift:0 2px 6px rgba(2,8,58,.06), 0 16px 40px rgba(2,8,58,.10);
  }
  *{ box-sizing:border-box; }
  html{ -webkit-text-size-adjust:100%; scroll-behavior:smooth; scroll-padding-top:88px; }
  body{ margin:0; background:var(--bg); color:var(--ink);
    font:17px/1.72 "Onest",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    -webkit-font-smoothing:antialiased; }
  a{ color:var(--accent); }
  :focus-visible{ outline:3px solid var(--accent); outline-offset:2px; border-radius:6px; }
  .wrap{ max-width:820px; margin:0 auto; padding:0 20px 96px; }
  .skip{ position:absolute; inset-inline-start:-9999px; top:0; background:#fff; color:var(--navy);
    padding:10px 18px; border-radius:0 0 12px 0; font-weight:700; z-index:60; }
  .skip:focus{ inset-inline-start:0; }

  /* sticky topbar + language bar */
  .topbar{ position:sticky; top:0; z-index:50; display:flex; align-items:center;
    justify-content:space-between; gap:12px; flex-wrap:wrap;
    padding:10px 0 10px; margin-bottom:2px;
    background:rgba(245,243,241,.86); backdrop-filter:saturate(150%) blur(10px);
    -webkit-backdrop-filter:saturate(150%) blur(10px);
    border-bottom:1px solid transparent; transition:border-color .2s; }
  .topbar::after{ content:""; position:absolute; inset-inline:-20px; bottom:0; height:1px;
    background:linear-gradient(90deg,transparent,var(--line),transparent); }
  .brand{ display:flex; align-items:center; gap:10px; font-weight:700; color:var(--navy);
    font-size:15px; letter-spacing:-.2px; }
  .brand-mark{ width:24px; height:24px; flex:none; }

  .lang-bar{ display:flex; flex-wrap:nowrap; overflow-x:auto; gap:4px; align-items:center;
    background:#fff; border:1px solid var(--line); border-radius:999px; padding:4px;
    box-shadow:var(--shadow); scrollbar-width:none; max-width:100%; }
  .lang-bar::-webkit-scrollbar{ display:none; }
  .lang-btn{ border:0; background:transparent; color:var(--muted); font:inherit; font-weight:700;
    font-size:12.5px; letter-spacing:.6px; padding:7px 13px; border-radius:999px; cursor:pointer;
    white-space:nowrap; transition:background .15s, color .15s; }
  .lang-btn:hover{ background:var(--accent-soft); color:var(--accent); }
  .lang-btn.active{ background:var(--accent); color:#fff; }

  /* auto translation note */
  .auto-note{ font-size:14px; line-height:1.6; color:var(--warn); background:var(--warn-soft);
    border:1px solid #f0dcb4; border-inline-start:4px solid var(--warn);
    padding:13px 18px; border-radius:var(--radius-sm); margin:16px 0 0; }

  /* hero */
  .masthead{ position:relative; text-align:center; padding:40px 0 34px; }
  .masthead::before{ content:""; position:absolute; inset:-40px -24px auto -24px; height:320px;
    background:radial-gradient(120% 100% at 50% 0, rgba(0,104,230,.10), transparent 72%);
    z-index:0; pointer-events:none; }
  .masthead > *{ position:relative; z-index:1; }
  .coffee, .coffee svg{ width:62px; height:62px; display:block; margin:0 auto 16px; }
  .steam{ animation:rise 3s ease-in-out infinite; }
  .steam.s2{ animation-delay:.6s; }
  @keyframes rise{ 0%{opacity:0;transform:translateY(4px)} 40%{opacity:.8} 100%{opacity:0;transform:translateY(-6px)} }
  .kicker{ letter-spacing:2.6px; font-size:11.5px; color:var(--accent); text-transform:uppercase; font-weight:800; }
  h1{ font-size:clamp(34px,7vw,52px); line-height:1.06; margin:14px 0 16px; color:var(--navy);
    letter-spacing:-1.4px; font-weight:800; text-wrap:balance; }
  .dateline{ display:inline-flex; align-items:center; gap:8px; color:var(--muted); font-size:14px;
    background:#fff; border:1px solid var(--line); border-radius:999px; padding:7px 16px; box-shadow:var(--shadow); }
  .tagline{ color:var(--navy); opacity:.85; font-size:17px; margin:18px auto 0; max-width:44ch;
    min-height:26px; font-style:italic; text-wrap:balance; }
  .live{ display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--ok); flex:none;
    box-shadow:0 0 0 0 rgba(22,107,64,.5); animation:pulse 2s infinite; }
  @keyframes pulse{ 0%{box-shadow:0 0 0 0 rgba(22,107,64,.5)} 70%{box-shadow:0 0 0 9px rgba(22,107,64,0)} 100%{box-shadow:0 0 0 0 rgba(22,107,64,0)} }

  /* cards */
  .card{ background:var(--card); border:1px solid var(--line); border-radius:var(--radius);
    padding:34px 36px; margin:26px 0; box-shadow:var(--shadow); }
  .card-head{ display:flex; align-items:center; gap:16px; margin-bottom:18px; }
  .card-head h2{ margin:8px 0 0; font-size:24px; line-height:1.22; color:var(--navy); letter-spacing:-.6px; }
  .mascot{ width:44px; height:44px; flex:none; }
  .badge{ display:inline-block; background:var(--accent-soft); color:var(--accent); font-size:10.5px;
    font-weight:800; letter-spacing:1.4px; padding:4px 11px; border-radius:999px; text-transform:uppercase; }
  .trust-badge{ background:#e9ebf5; color:var(--navy); }
  .sup-badge{ background:#fde7ef; color:#a13360; }
  .intro{ color:var(--muted); margin:0 0 8px; font-size:16.5px; max-width:var(--measure); }

  /* jump nav / table of contents */
  .toc{ background:var(--bg); border:1px solid var(--line); border-radius:var(--radius-sm);
    padding:16px 18px; margin:18px 0 6px; }
  .toc-h{ margin:0 0 10px; font-size:11px; font-weight:800; letter-spacing:1.4px;
    text-transform:uppercase; color:var(--muted); }
  .toc-list{ list-style:none; margin:0; padding:0; display:grid; gap:2px; }
  .toc-list a{ display:flex; gap:10px; align-items:baseline; text-decoration:none; color:var(--navy);
    padding:7px 10px; border-radius:10px; font-size:15px; line-height:1.45; transition:background .15s, color .15s; }
  .toc-list a:hover{ background:var(--accent-soft); color:var(--accent); }
  .tocnum{ flex:none; font-weight:800; font-size:12px; color:var(--accent);
    min-width:1.4em; text-align:center; }
  .toctxt{ overflow-wrap:anywhere; }

  /* findings */
  .findings{ margin-top:10px; display:grid; gap:14px; }
  .finding{ position:relative; border:1px solid var(--line-soft); border-radius:var(--radius-sm);
    border-inline-start:4px solid var(--accent-soft);
    background:#fff; padding:24px 26px; scroll-margin-top:96px;
    transition:border-color .18s, box-shadow .18s, transform .18s; }
  .finding:hover{ border-inline-start-color:var(--accent); box-shadow:var(--shadow); }
  .finding:target{ border-inline-start-color:var(--accent); box-shadow:0 0 0 3px rgba(0,104,230,.12); }
  .finding:focus{ outline:none; }
  .finding h3{ margin:0 0 16px; font-size:20px; line-height:1.3; color:var(--navy);
    display:flex; gap:12px; align-items:baseline; font-weight:700; letter-spacing:-.4px;
    max-width:var(--measure); text-wrap:balance; }
  .fnum{ background:var(--navy); color:#fff; font-size:12px; font-weight:800; border-radius:999px;
    padding:3px 11px; flex:none; }
  .flist{ margin:0; display:grid; gap:14px; max-width:var(--measure); }
  .flist .frow{ display:block; }
  .lbl{ display:block; color:var(--muted); font-weight:700; font-size:11px; letter-spacing:1.4px;
    text-transform:uppercase; margin-bottom:3px; }
  .fval{ display:block; line-height:1.7; }
  .sources{ margin-top:20px; padding-top:16px; border-top:1px dashed var(--line); }
  .sources .lbl{ margin-bottom:8px; }
  .srcchip{ display:inline-block; margin:0 6px 6px 0; }
  [dir="rtl"] .srcchip{ margin:0 0 6px 6px; }
  .srcchip a{ display:inline-block; background:var(--bg); border:1px solid var(--line); color:var(--navy);
    font-size:12.5px; font-weight:600; padding:6px 13px; border-radius:999px; text-decoration:none;
    transition:.15s; max-width:100%; overflow-wrap:anywhere; }
  .srcchip a:hover{ border-color:var(--accent); color:var(--accent); background:var(--accent-soft); }
  .factions{ display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
  .bottom{ border-top:1px solid var(--line-soft); margin-top:24px; padding-top:20px;
    font-size:17px; line-height:1.7; color:var(--navy); max-width:var(--measure); }

  /* trust */
  .trust-totals{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:20px 0 24px; }
  .trust-totals .t{ text-align:center; background:var(--bg); border:1px solid var(--line);
    border-radius:var(--radius-sm); padding:20px 10px; }
  .trust-totals b{ font-size:32px; display:block; line-height:1.1; color:var(--navy); }
  .trust-totals span{ font-size:12px; color:var(--muted); letter-spacing:.4px; }
  .trust-totals .ok b{ color:var(--ok); } .trust-totals .warn b{ color:var(--warn); } .trust-totals .bad b{ color:var(--bad); }
  .table-scroll{ overflow-x:auto; border:1px solid var(--line-soft); border-radius:var(--radius-sm); }
  table.verdicts{ width:100%; border-collapse:collapse; font-size:14.5px; }
  table.verdicts th, table.verdicts td{ text-align:start; padding:13px 14px; border-top:1px solid var(--line-soft); vertical-align:top; }
  table.verdicts th{ color:var(--muted); font-weight:700; font-size:11px; letter-spacing:1.2px;
    text-transform:uppercase; border-top:0; background:var(--bg); }
  .pill{ display:inline-block; font-size:11px; font-weight:800; padding:3px 10px; border-radius:999px; white-space:nowrap; }
  .pill.ok{ background:var(--ok-soft); color:var(--ok); }
  .pill.warn{ background:var(--warn-soft); color:var(--warn); }
  .pill.bad{ background:var(--bad-soft); color:var(--bad); }
  .note{ color:var(--muted); font-size:14.5px; line-height:1.7; margin-top:20px; max-width:var(--measure); }

  /* support */
  .tiers{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:18px; margin:22px 0; }
  .tier{ background:var(--bg); border:1px solid var(--line); border-radius:var(--radius-sm); padding:24px 26px; }
  .tier h3{ margin:0 0 14px; font-size:18px; color:var(--navy); letter-spacing:-.3px; }
  .tier ul{ margin:0; padding-inline-start:20px; }
  .tier li{ margin:10px 0; line-height:1.65; }
  .tier.pro{ background:#fff; border-color:var(--accent); box-shadow:0 0 0 3px rgba(0,104,230,.08); }
  .soon{ font-size:10px; background:var(--accent-soft); color:var(--accent); padding:3px 9px;
    border-radius:999px; vertical-align:middle; font-weight:800; letter-spacing:.5px; }
  .price{ margin-top:16px; font-weight:800; color:var(--accent); }
  .donate-row{ display:flex; gap:12px; flex-wrap:wrap; margin-top:12px; }
  .btn{ display:inline-flex; align-items:center; gap:8px; padding:13px 22px; border-radius:999px;
    font-weight:700; text-decoration:none; font-size:14.5px; transition:.15s; border:1px solid transparent; }
  .btn.primary{ background:var(--accent); color:#fff; }
  .btn.primary:hover{ background:#0057c2; }
  .btn.ghost{ background:#fff; color:var(--navy); border-color:var(--line); }
  .btn.ghost:hover{ border-color:var(--accent); color:var(--accent); }
  .btn.small{ padding:9px 17px; font-size:13.5px; }
  .btn:hover{ transform:translateY(-1px); }

  /* back to top */
  .totop{ position:fixed; inset-block-end:20px; inset-inline-end:20px; z-index:40;
    background:#fff; color:var(--navy); border:1px solid var(--line); box-shadow:var(--shadow-lift);
    width:46px; height:46px; border-radius:999px; display:flex; align-items:center; justify-content:center;
    text-decoration:none; font-size:18px; font-weight:800; }
  .totop:hover{ border-color:var(--accent); color:var(--accent); }

  footer{ color:var(--muted); font-size:14.5px; text-align:center; margin-top:52px; line-height:2; }
  footer a{ color:var(--accent); text-decoration:none; }
  footer a:hover{ text-decoration:underline; }
  .follow{ display:flex; flex-wrap:wrap; gap:10px; justify-content:center; align-items:center;
    margin:0 0 16px; padding:14px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
  .follow-label{ font-weight:700; color:var(--navy); font-size:13px; text-transform:uppercase; letter-spacing:.5px; }
  .follow-btn{ display:inline-flex; align-items:center; gap:5px; padding:8px 15px; border-radius:999px;
    background:#fff; border:1px solid var(--line); color:var(--navy); font-weight:700; font-size:13px; text-decoration:none; transition:.15s; }
  .follow-btn:hover{ border-color:var(--accent); color:var(--accent); text-decoration:none; }
  .follow-btn.soon{ opacity:.6; }

  [dir="rtl"] .kicker, [dir="rtl"] .lbl, [dir="rtl"] .badge, [dir="rtl"] .toc-h{ letter-spacing:0; }
  [dir="rtl"] h1, [dir="rtl"] .card-head h2, [dir="rtl"] .finding h3{ letter-spacing:0; }

  @media (prefers-reduced-motion:reduce){
    html{ scroll-behavior:auto; }
    *,*::before,*::after{ animation:none !important; transition:none !important; }
    .btn:hover{ transform:none; }
  }

  @media (max-width:640px){
    body{ font-size:16.5px; }
    .wrap{ padding:0 15px 90px; }
    .card{ padding:22px 18px; border-radius:18px; }
    .finding{ padding:18px 16px; }
    .card-head{ gap:12px; }
    .card-head h2{ font-size:21px; }
    .masthead{ padding:26px 0 24px; }
    .trust-totals{ grid-template-columns:1fr; }
    .btn{ width:100%; justify-content:center; }
    .totop{ inset-block-end:14px; inset-inline-end:14px; }
    .brand span{ display:none; }
  }
</style>
</head>
<body data-latest="{LATEST}" data-today="{TODAY}">
<a class="skip" href="#main">Zum Inhalt springen</a>
<div class="wrap">
  <header class="topbar">
    <div class="brand">
      <svg class="brand-mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 L21 6 V12 C21 17 17 21 12 22 C7 21 3 17 3 12 V6 Z" fill="#0068e6"/><path d="M8 12 l3 3 l5 -6" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
      <span data-i18n="brand">Citizen Agents</span>
    </div>
    <nav class="lang-bar" id="langBar" aria-label="Sprache"></nav>
  </header>

  <div id="autoNote" class="auto-note" role="status" style="display:none"></div>

  <main id="main">
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
    <div class="follow">
      <span class="follow-label" data-i18n="follow_label">Folge uns:</span>
      <a class="follow-btn" href="https://t.me/CitizenAgentsTicker" target="_blank" rel="noopener">📨 Telegram</a>
      <a class="follow-btn soon" href="https://mikelninh.github.io/citizen-agents/" target="_blank" rel="noopener" data-i18n="follow_ig">📸 Instagram (bald)</a>
    </div>
    <span data-i18n="footer">Citizen Agents — Digital Democracy Studio, Berlin.</span><br>
    <a href="https://github.com/mikelninh/citizen-agents" data-i18n="footer_src">Quellcode &amp; Rohdaten</a> ·
    <a href="https://mikelninh.github.io/citizen-agents/" data-i18n="footer_home">Zur Startseite</a>
  </footer>
</div>
<a class="totop" href="#main" aria-label="Nach oben">↑</a>
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
      follow_label:"Folge uns:", follow_ig:"📸 Instagram (bald)",
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
      footer_src:"Source code &amp; raw data", footer_home:"To the homepage", follow_label:"Follow us:", follow_ig:"📸 Instagram (soon)",
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
      footer_src:"Kaynak kodu ve ham veri", footer_home:"Ana sayfaya", follow_label:"Bizi takip et:", follow_ig:"📸 Instagram (yakında)",
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
      footer_src:"Исходный код и сырые данные", footer_home:"На главную", follow_label:"Подписывайтесь:", follow_ig:"📸 Instagram (скоро)",
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
      footer_src:"الكود المصدري والبيانات الخام", footer_home:"إلى الصفحة الرئيسية", follow_label:"تابعنا:", follow_ig:"📸 إنستغرام (قريباً)",
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
      footer_src:"Mã nguồn & dữ liệu thô", footer_home:"Về trang chủ", follow_label:"Theo dõi chúng tôi:", follow_ig:"📸 Instagram (sớm)",
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
      footer_src:"Kod źródłowy i surowe dane", footer_home:"Strona główna", follow_label:"Śledź nas:", follow_ig:"📸 Instagram (wkrótce)",
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
  // ---- bilingual finding content --------------------------------------
  // Each <article class="finding"> carries data-content = {"de":{headline,rows},
  // "en":{...}}. EN is present only when the watchdog digest supplied an
  // "### EN" block; otherwise we fall back to DE.
  function applyContentLang(lang){
    var want = (lang === 'en') ? 'en' : 'de';
    document.querySelectorAll('article.finding[data-content]').forEach(function(art){
      var pay;
      try{ pay = JSON.parse(art.getAttribute('data-content')); }catch(e){ return; }
      var c = pay[want] || pay.de; if(!c) return;
      var h = art.querySelector('h3 .fhead'); if(h) h.textContent = c.headline;
      var list = art.querySelector('.flist');
      if(list && c.rows){
        list.innerHTML = c.rows.map(function(r){
          var lbl=document.createElement('span'); lbl.className='lbl'; lbl.textContent=r[0];
          var val=document.createElement('span'); val.className='fval'; val.textContent=r[1];
          var row=document.createElement('div'); row.className='frow';
          row.appendChild(lbl); row.appendChild(val);
          return row.outerHTML;
        }).join('');
      }
      art.setAttribute('lang', pay[want] ? want : 'de');
    });
  }
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
    applyContentLang(lang);
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
            de = lang_block(f, "de")
            en = lang_block(f, "en") if has_en(f) else dict(de)
            item = {
                "watchdog": wd,
                "sources": f["sources"],
                "tags": tags,
                "life": life,
                "has_en": has_en(f),
                "de": de,
                "en": en,
            }
            # backward compatible flat fields = DE
            item.update(de)
            items.append(item)
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
