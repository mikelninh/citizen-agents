# 🔧 Gameplay Engineer Digest — 2026-08-19

> Implemented the Studio Director's **2026-08-19** brief (D1 = the gate, plus the
> one-tap kill fix from D2). Read-only director brief is on `studio/director-2026-08-19`.
> Branch: `studio/engineer-2026-08-19`. Build: `npm run build` passes (56 modules).

## What I changed

**D1 — BOT/PLAYER WEAPON UNIFICATION (the gate).**
Bots no longer fire a hidden hitscan carbine. In `botbrain.js`, `botShoot` now:
- lazily gives each bot a real tool (`statsFor` → splatter/bubbler/confetti/petalbow) + a `Charge`,
- gates fire on `Charge.ready` (same bar the player has),
- spawns an actual `Projectiles` projectile via `c.spawnProjectile` that travels, can be dodged, and applies `stats.soak` (9–52) — exactly the player's kit.

Wiring in `match-mode.js`: added `spawnProjectile` to the bot context, and taught
`_onProjectileHit` to apply soak for **bot-owned** projectiles (previously only the
local player's shots applied; everything else was deferred as "remote").

`weapon.js` is now just `applySpread` — the `WEAPON`/`traceShot`/`Magazine`/`buildViewModel`
hitscan carbine is deleted. **No remaining code references to the old hitscan path.**

**D2 (partial) — no more one-tap saber.**
`leafblade.soak` 100 → 34. A full-HP enemy now needs ≥3 clean saber hits to go down,
on the existing 100-hp/soak model. This directly kills the director's #1 repeated critique.

## Why this ordering
The director's whole argument: you cannot tune soak or stamina against an AI that fires a
carbine you don't own. D1 fixes observability first, which is what unblocks D2/D3. So I
shipped D1 fully, plus the cheap, high-trust leafblade soak change, and deliberately
**deferred** the saber Stamina resource + whiff-punish and the petalbow/soak-regen tuning
(D2/D3 remainder) until the bot unification is in and we can actually watch a duel.

## Acceptance vs. the brief
- ✅ Bot shot is a visible, dodgeable projectile applying `stats.soak`, not `WEAPON.damage`.
- ✅ `traceShot` / `WEAPON.damage` no longer referenced in the bot path.
- ✅ `weapon.js` `Magazine`/`buildViewModel` deleted; build still green.
- ✅ Saber no longer one-taps (≥3 hits to down).
- ⏳ Saber Stamina/whiff-punish and petalbow anti-saber + out-of-combat soak regen: NOT done
  this run — await D1 observation, per the director's own gate logic.

## Next for the engineer (next run)
With D1 in, the highest-leverage follow-ups are D2 (saber `Stamina` commitment +
perfect-timing bonus + whiff opening) and D3 (petalbow as explicit anti-saber,
out-of-combat soak regen). These are now *measurable* in a bot duel.
