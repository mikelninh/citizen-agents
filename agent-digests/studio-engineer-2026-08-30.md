# 🔧 Gameplay Engineer — 2026-08-30

> Branch `studio/engineer-2026-08-30`. Read-only director brief `studio/director-2026-08-21`
> (One Combat World, Two Resources). Built against current `main` (post v0.32 Arena).
> `npm run build` ✅ passes.

## What I implemented (3 directives from the director's brief)

### 1. Killed the ghost carbine — bots now use the same dodgeable soak model
- `experiences/little-planet/src/modes/botbrain.js` — `botShoot` no longer calls
  `traceShot`/hitscan. It now spawns a **visible travelling soak blob** through the
  existing `Projectiles` pool (`kind:'blob'`, speed 46, gravity 3, dmg 20, team-coloured).
- `match-mode.js` `_driveBots` now passes `projectiles` into the bot brain context.
- `match-mode.js` `_onProjectileHit` now reports hits for **bot-owned** projectiles
  (`this.bots.some(b => b.netId === item.owner)`) through the same `_request({type:'hit'})`
  path the player uses, so vs-bot and vs-friend PvP are finally the same game.
- Deleted the orphaned hitscan code in `weapon.js` (`WEAPON`, `traceShot`, `raySphere`,
  `Magazine`, `buildViewModel`); kept only `applySpread`. Zero `ammo`/hitscan refs left.

### 2. Gave the saber its own Stamina resource (movement + timing, for real)
- `tools.js` — added `STAMINA` config + a `Stamina` class (max 100, swing cost 34,
  sprint drain 22/s, regen 30/s, swing-lock 0.42s).
- `match-mode.js` `_initLoadout` — the leafblade no longer creates a soak `Charge`;
  it draws from `this.stamina`. Stamina drains while sprinting and regens otherwise.
- `saber.js` — added a **winded** state: a swing attempted with too little stamina
  whiffs, stutters the blade (telegraphed, non-lethal), and locks `windLock` before
  you can swing again (`startSwing()` refuses while winded).
- `ui.js` + `styles.css` — added a dedicated **STAMINA** bar (distinct green), shown
  only in tactical; the soak-charge bar hides while the blade is out.

### 3. Fixed the dead pickup — `ammo` → `surge`, serving BOTH families
- `shared/items.js` — renamed `ammo` → `surge` (⚡, "Refill your soak-charge and
  stamina"). Keep `effect:{ refill:true }`.
- `match-mode.js` `_applyInstantEffect` — `refill` now tops up **both** the soak
  `Charge` and `stamina` (previously the player got nothing useful from a dead pickup).
- Updated README + the orphaned `.ammo` CSS (→ `.surge`) so zero `ammo` strings remain.

## Acceptance against the director's brief
- ✅ (1a) Bot shots are visible travelling objects you can dodge. (1c) No code path
  calls `traceShot`/`WEAPON` anymore. (1d) Per-shot damage kept in the same ballpark
  (was ~20.8/hit, now flat 20 travelling) with the same burst pattern.
- ✅ (2a) Blade cannot swing when stamina < cost even if the soak-charge is full
  (separate resource, gated in `match-mode`). (2b) Dedicated STAMINA HUD bar, drained
  by sprinting. (2c) Winded swing is telegraphed (blade stutter + optional sfx) and
  deals no damage.
- ✅ (3a) Picking up Surge fills soak-charge and stamina. (3b) Blurb matches. (3c) Zero
  `ammo` references in the repo.

## Build
`npm run build` → ✅ `built in 31.66s` (exit 0). Exploit/hideseek mode untouched.

## What's next (engineer recommendation)
- Add an `audio.saberWind()` cue so the winded whiff is audible, not just visible.
- Consider gating sprint when stamina ≈ 0 so a spent player can't kite forever.
- The director's open question (stamina vs heat) is now answered in code as **stamina
  (shared with movement)** — Mikel, confirm or flip to heat.
