# Security Policy — Citizen Agents

## Reporting a vulnerability

We take security seriously. If you find a vulnerability in any Citizen Agents
repository or the deployed fleet:

- **Email:** hallo.chupi@gmail.com (PGP key available on request)
- **Do NOT** open a public issue for security vulnerabilities
- **Do NOT** post details in the Telegram channel

## What we ask

- Include: affected repo/file, version/commit, reproduction steps, impact
- Give us a reasonable window (default 90 days) before public disclosure
- Test only on your own instances — not against deployed citizen services

## What we commit

- Acknowledgment within 48 hours
- A fix plan within 7 days (or a clear explanation why not)
- Credit in the security acknowledgments once the issue is resolved (if you want it)
- No legal action against good-faith researchers following this policy

## Known security posture (current state)

| Area | Posture |
|---|---|
| Agent autonomy | Bounded toolsets (web/terminal/file), no auto-merge, cost caps |
| Data | Watchdogs process zero personal data; browser-first for citizen tools |
| Secrets | API keys in ~/.hermes/.env only, never in repos; redaction ENABLED in gateway |
| Supply chain | Minimal deps per MCP; SBOM pending |
| Hosting | EU-only (Hetzner) for cloud; self-host option for authorities |
| Audit | Every run = digest + JSON log + review PR — a public audit trail |

## Out of scope

- Social engineering of the operator
- Physical attacks on the operator's hardware
- Issues in third-party dependencies (report to the upstream project)

## Acknowledgments

To be listed here as researchers report issues (none reported yet — 2026-08-06).

*Digital Democracy Studio, Berlin, 2026-08-06.*
