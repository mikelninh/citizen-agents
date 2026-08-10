#!/usr/bin/env python3
"""Regenerate agent-logs/manifest.json for impact.html.

impact.html works without this file (it falls back to the GitHub contents API),
but the manifest makes the page load in one request, keeps working when the
unauthenticated API rate limit is hit, and works offline from a local server.

Usage:
    python3 build_impact.py            # scan ./agent-logs, write manifest.json
    python3 build_impact.py --dir path/to/agent-logs
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

VERDICT_WORDS = ("VERIFIED", "PARTIAL", "FAILED", "BLOCKED", "SHIP", "PASS", "FAIL")

FINDING_KEYS = (
    "highlights", "issues", "issues_found", "critiques", "critique_titles",
    "critique_ids", "critique_targets", "deadlines", "changes", "directives",
    "source_checks", "static_checks_passed", "needs_human_eyes",
)


def agent_from_name(name: str) -> str:
    stem = re.sub(r"\.json$", "", name)
    stem = re.sub(r"-\d{4}-\d{2}-\d{2}.*$", "", stem)
    return stem or "unknown"


def date_from(name: str, data: dict) -> str | None:
    if isinstance(data.get("date"), str):
        return data["date"]
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else None


def count_findings(data: dict) -> int:
    total = 0
    for k in FINDING_KEYS:
        v = data.get(k)
        if isinstance(v, list):
            total += len(v)
        elif isinstance(v, int):
            total += v
    return total


def status_of(data: dict) -> str:
    """verified | partial | failed | unknown — defensive across shapes."""
    if isinstance(data.get("failed"), int) and data["failed"] > 0:
        return "failed"
    if isinstance(data.get("partial"), int) and data["partial"] > 0 and data.get("verified", 0) == 0:
        return "partial"
    if isinstance(data.get("verified"), int) and data["verified"] > 0:
        return "partial" if data.get("partial", 0) else "verified"
    blob = " ".join(
        str(data.get(k, "")) for k in ("verdict", "status", "result", "outcome")
    ).upper()
    if "FAIL" in blob or "BLOCK" in blob:
        return "failed"
    if "NOTES" in blob or "PARTIAL" in blob:
        return "partial"
    if any(w in blob for w in ("VERIFIED", "SHIP", "PASS", "OK")):
        return "verified"
    if data.get("build_passed") is True:
        return "verified"
    if data.get("build_passed") is False:
        return "failed"
    if data.get("issues_found") or data.get("issues"):
        return "partial"
    return "verified" if data else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="agent-logs")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    d = pathlib.Path(args.dir)
    if not d.is_dir():
        print(f"no such directory: {d}", file=sys.stderr)
        return 1
    out = pathlib.Path(args.out) if args.out else d / "manifest.json"

    runs = []
    for p in sorted(d.glob("*.json")):
        if p.name == "manifest.json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # keep going, note the bad file
            runs.append({"file": p.name, "agent": agent_from_name(p.name),
                         "error": str(e), "status": "failed", "findings": 0})
            continue
        if not isinstance(data, dict):
            data = {"items": data}
        runs.append({
            "file": p.name,
            "agent": agent_from_name(p.name),
            "date": date_from(p.name, data),
            "status": status_of(data),
            "findings": count_findings(data),
            "repo": data.get("repo"),
            "branch": data.get("branch"),
            "sources": len(data.get("sources") or []) or data.get("sources_fetched") or 0,
            "headline": (data.get("one_big_idea") or data.get("verdict")
                         or (data.get("highlights") or [None])[0]),
        })

    manifest = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(runs),
        "runs": runs,
    }
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
