# Citizen Agents — 24/7 Cloud Deployment (Hetzner EU)

## Honest cost estimate (2026-08)

### Fixed (server)
| Item | Spec | Price |
|---|---|---|
| Hetzner CX22 (recommended) | 2 vCPU · 4 GB RAM · 40 GB SSD | €4.30/mo |
| Hetzner CX32 (comfortable) | 4 vCPU · 8 GB RAM · 80 GB SSD | €8.20/mo |
| Hetzner CPX21 (budget ARM) | 3 vCPU · 4 GB · 40 GB | €4.85/mo |
| IPv4 (optional, IPv6 free) | 1 address | +€0.50/mo |

**Server: ~€4.30–8.70/month** (≈ €0.15–0.29/day)

### Variable (AI tokens)
13 agents × ~1 run/day. Each run is a bounded, targeted research session.
- Small agent run (watchdog brief): ~30–60k tokens
- Studio director/engineer run (reads code + writes): ~80–150k tokens

At current provider rates (~€2–4 per M tokens for a mid-tier model), realistic spread:

| Scenario | Cost |
|---|---|
| Frugal (all 13 agents, daily, small model) | ~€3–6/month |
| Standard (mix, deepseek-class model) | ~€6–12/month |
| Comfortable (larger model for studio) | ~€10–20/month |

**Total honest range: €8–30/month** (≈ €0.30–1.00/day)
For comparison: one lawyer consult costs €25–200. The entire fleet costs less per month than a single rights question would cost a citizen.

### What it buys
- True 24/7: agents run even while your Mac sleeps
- All 13 agents, all 10 watchdogs + 3 studio roles
- Telegram delivery from the cloud
- Repo PRs + logs, human review stays with you

## Setup (one-time, ~20 min)

```bash
# 1. Create the server at console.hetzner.com (Ubuntu 24.04, CX22, Frankfurt/Falkenstein)
# 2. Add your SSH key (the one from this Mac)
# 3. Run this script on the server
```

## Script: `setup-cloud.sh` (run as root on the VM)

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "=== Citizen Agents cloud setup ==="

# --- basics ---
export DEBIAN_FRONTEND=noninteractive
apt-get update -y && apt-get upgrade -y
apt-get install -y git curl build-essential python3 python3-venv nodejs npm jq

# --- install uv (fast python) ---
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# --- install Hermes ---
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# --- node for the game studio (bla-keks-world) ---
npm install -g npm@latest

# --- SSH + git config for the bot account ---
# (see below: you need a deploy key or token with repo scope for mikelninh)

echo "=== next steps (manual, needs your secrets) ==="
echo "1. hermes setup        # choose provider + model (same as local)"
echo "2. Add HERMES_HOME secrets: API keys in ~/.hermes/.env"
echo "3. GitHub token: gh auth login (repo + workflow scope)"
echo "4. Copy skills: rsync from local ~/.hermes/skills/ to server"
echo "5. hermes gateway install   # systemd service, auto-start"
echo "6. Recreate the 13 cron jobs (hermes cron create ...) — or export/import"
echo ""
echo "=== systemd service (installed by hermes gateway install) ==="
echo "systemctl status hermes-gateway   # should say active (running)"
echo "journalctl -u hermes-gateway -f   # live agent logs"
```

## Migration path (local -> cloud)

Option A (simplest, recommended): keep local cron jobs as-is for now,
run ONE cloud instance with the same 13 jobs. When the cloud proves stable,
pause the local ones.

Option B (clean): export the cron jobs (they live in ~/.hermes/state.db),
restore on the server with `hermes cron restore` (if available) or recreate
from the prompts in this repo.

Option C (best for studio): run the studio agents in the cloud (they need
node + git), keep the watchdog cron jobs wherever the gateway runs.

## What I did NOT include (and why)

- No auto-scaling: 13 daily agents don't need it. One VM is enough.
- No GPU: agents are API calls, not local inference.
- No backup service: the repo IS the backup (every run = PR + log).
- No uptime monitoring yet: add UptimeRobot/healthchecks.io later if you want alerts.

## First-week check

```bash
# on the server, daily:
hermes cron list                    # all 13 jobs scheduled
hermes cron status                  # last runs, failures
ls ~/.hermes/logs/gateway.log       # delivery + errors
# on GitHub:
# every repo should show 1 new PR per agent per day
```

Built by Digital Democracy Studio, Berlin, 2026-08-06.
