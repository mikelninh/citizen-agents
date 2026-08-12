#!/usr/bin/env python3
"""Inject the bilingual (DE+EN) digest convention into every Citizen Agents
watchdog cron prompt in Hermes jobs.json.

The Breakfast Ticker now flips finding CONTENT by language (not just chrome).
For EN to work, each watchdog must emit an English block per finding using the
convention the parser in build_breakfast.py already understands:

  ### EN
  - **Headline:** <English headline>
  - **What changed:** …
  - **Why:** …  - **Effective:** …  - **Deadline:** …
  - **Who's affected:** …  - **How:** …  - **Citizen tip:** …

This script appends that instruction to any cron prompt that contains
"WATCH agent" (the Citizen Agents watchdog family). It does NOT touch other
crons. Backs up jobs.json first.
"""
import json
import shutil
import os

JOBS = os.path.expanduser("~/.hermes/cron/jobs.json")
BACKUP = JOBS + ".bak-bilingual"

BLOCK = (
    "\n\nLANGUAGE (WICHTIG — gilt ab sofort): Jeder Fund muss zweisprachig sein. "
    "Schreibe den Fund wie gewohnt auf Deutsch, dann hänge DIREKT nach den "
    "deutschen Feldern (und nach den Quellen) einen englischen Block an:\n\n"
    "### EN\n"
    "- **Headline:** <englische Überschrift>\n"
    "- **What changed:** …\n"
    "- **Why:** …\n"
    "- **Effective:** …\n"
    "- **Deadline:** …\n"
    "- **Who's affected:** …\n"
    "- **How:** …\n"
    "- **Citizen tip:** …\n\n"
    "Benutze GENAU die Überschrift \"### EN\" und GENAU diese Feldnamen. "
    "Wiederhole die Quellenliste NICHT im EN-Block — Quellen sind geteilt. "
    "Der englische Text muss eine echte Übersetzung des deutschen Inhalts "
    "sein (gleiche Fakten, gleiche Zahlen), keine Zusammenfassung."
)

def main():
    shutil.copy2(JOBS, BACKUP)
    print(f"backup -> {BACKUP}")
    with open(JOBS, encoding="utf-8") as fh:
        data = json.load(fh)
    n = 0
    for job in data.get("jobs", data if isinstance(data, list) else []):
        p = job.get("prompt", "")
        if "WATCH agent" in p and "### EN" not in p and BLOCK.strip()[:20] not in p:
            job["prompt"] = p.rstrip() + "\n" + BLOCK
            n += 1
    # jobs.json may be {"jobs":[...]} or a list
    with open(JOBS, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"injected bilingual instruction into {n} watchdog prompts")


if __name__ == "__main__":
    main()
