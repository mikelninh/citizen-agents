# Gameplay Engineer — 2026-08-30

## What I shipped: the Saber Guard (deflect), priced against stamina

The lead's standing decision is **BOTH weapon families first-class**. Before today
the two families didn't actually interact: `Saber` (`src/modes/weapons/saber.js`)
could only swing at bodies, and `Projectiles.update()` had exactly one outcome for
an incoming shot — it hits you. A sword player walking into open ground against a
thrown-object loadout had no answer at all. That's not rock-paper-scissors, that's
a losing pick.

**The mechanic:** hold aim (right mouse) with the Verdant Blade lit and the blade
comes across your view in a distinct pose. Any *incoming* shot inside the guard
cone gets batted back at the thrower — retargeted to your team, 0.8× damage,
22 m/s. A live swing deflects too, with a wider arc (1.9 rad vs 1.35), so timing
beats turtling.

**It is not free.** This branch is stacked on top of today's earlier Stamina work,
so the guard is priced against the same pool the saber swings from: 16/s while
held, 12 per shot actually swatted, and the guard drops below a floor of 8. That
means roughly 8 deflects from a full bar, and a projectile team can break a guard
with volume of fire. Ranged keeps all its counterplay: the cone is front-only and
3 m deep, so flanking and lobbing over the guard still work.

## Changes

- `src/modes/weapons/saber.js` — new `GUARD` config + pure `deflectsProjectile()`
  (front-cone, in-reach, closing-velocity test, no Three.js state). `update()`
  takes `guarding` and blends a distinct guard pose so the silhouette reads.
- `src/modes/weapons/projectiles.js` — `update()` takes an optional
  `{ onDeflect }`; a bounce reflects velocity, reassigns owner/team, applies a
  damage multiplier and refreshes life. Signature is backwards compatible —
  existing callers behave exactly as before.
- `src/modes/weapons/tools.js` — `STAMINA.guardDrain/deflectCost/guardFloor`,
  plus `Stamina.canGuard()` and `Stamina.spend(cost)`.
- `src/modes/match-mode.js` — `_tryDeflect()` wires blade to projectile loop
  (local player only, no friendly-fire deflects), guard drains stamina while held,
  hitmarker + spark burst + "🛡️ deflected!" toast.
- `tools/deflect-test.mjs` — 6 geometry checks for the guard cone.

## Verified

- `node tools/deflect-test.mjs` → **6/6 pass**
- Stamina arithmetic sanity: 8 deflects from a full bar, then `canGuard()` is false
- `npm run build` in `experiences/little-planet` → **pass**
- `npm run build` at repo root → **pass**; `npm run check` → **pass**
- Explore mode untouched; no new dependencies; `package-lock.json` left alone.

## Note on branching

`studio/engineer-2026-08-30` already existed on the remote (the tactical/stamina
commit). I did **not** force-push over it — this work is cherry-picked on top of it
on `studio/engineer-2026-08-30-guard`, one conflict resolved by hand in the
`match-mode.js` import block.

## For Mikel

The stamina numbers are a first guess, not a balance pass. The question worth
answering after one playtest: **is 8 deflects per bar too generous?** If a saber
player can hold a lane against two throwers, drop `deflectCost` to punish spamming
the guard, or raise `guardDrain` so holding it is the expensive part rather than
the swatting.
