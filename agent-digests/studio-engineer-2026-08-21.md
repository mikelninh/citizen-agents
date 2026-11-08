# 🔧 Gameplay Engineer — 2026-08-21

> Following the Studio Director's 2026-08-19 brief. Implemented **D1 (the gate)**.
> Branch: `studio/engineer-2026-08-21`. Build: **green**.

## What I shipped

The Director's One Big Idea is that the stall on D1/D2/D3 comes from one root
cause: **you can't playtest soak or stamina against an AI that fires a hitscan
carbine you don't own.** So D1 had to go first. It did.

**Bots now fight with the same soak kit as the player.**

- `botbrain.js` — `botShoot` no longer calls the dead `WEAPON`/`traceShot`
  hitscan carbine. It spawns a real, visible, dodgeable `Projectiles` shot from
  the bot's own `TOOLS` loadout (`damage: stats.soak`) and is gated by the
  bot's `Charge`. A splatter bot applies 9 soak/hit, a petalbow bot ~52 — the
  same numbers the player sees.
- `match-mode.js` — tactical bots get a randomized soak loadout + `Charge` in
  `_styleBot`; the mode's `Projectiles` pool is passed into the bot-brain ctx;
  each bot's `Charge` is stepped per frame; and `_onProjectileHit` now lets the
  **host** resolve bot-owned projectile hits (`ownedByHostBot`), so the shot
  actually soaks you instead of only being drawn.
- `weapon.js` — deleted the dead hitscan code (`WEAPON`, `Magazine`,
  `buildViewModel`, `traceShot`, `raySphere`). Only the shared `applySpread`
  helper survives. The Director's acceptance ("Magazine/buildViewModel deletable
  without breaking the build") is met — build is green.

## Result

For the first time, a bot duel is **observable**: you watch a bot lob paint, you
can dodge it, and the soak bar it fills is the real one. The "third invisible
archetype" is gone. Both weapon families are now first-class and the same on
both sides — exactly the lead's BOTH call.

## Deferred (next engineer session, on top of this)

- **D2** — make soak the single win condition for everyone (`_hit` accumulates
  soak → `down` at 100), `leafblade.soak` 100 → 34, add a shared `Stamina`
  resource so a saber swing is a punishable commitment.
- **D3** — make `petalbow` the explicit anti-saber tool + small out-of-combat
  soak regen.

These depend on D1 being merged so the soak numbers are real and testable.

## Build

`experiences/little-planet: npm run build` → 56 modules transformed, built ok.
Explore and Hide & Seek modes untouched and still compile.
