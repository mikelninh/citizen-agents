# Gameplay Engineer — 2026-08-10

Implemented all three of the director's directives. `npm run build` → ✓ built in 1.90s, 56 modules, exit 0.

## 1. Bots stop cheating (`src/modes/botbrain.js`, `src/modes/weapons/projectiles.js`)

`botShoot()` used `traceShot()` from the dead `weapon.js` — an instant hitscan line with a
cosmetic tracer, out to `WEAPON.range`. Players throw slow, visible, dodgeable arcs. That
asymmetry made bot fights feel like weather, not combat.

Bots now spawn a real pooled projectile (speed 42, gravity 7, lead + arc lift based on flight
time, existing accuracy spread untouched). The hitscan path stays only as a fallback when no
projectile pool is passed in — nothing else in the repo currently uses it.

Bot-owned shots carry `ownerBot`, so `_onProjectileHit` can report the hit on that bot's behalf
(`_request({type:'hit'}, bot.netId)`) — same authority path the brain already used.

**Net effect:** you can now see a bot's shot coming and sidestep it. Strafing matters.

## 2. The Duel Triangle — guard (`src/modes/weapons/saber.js`, `src/modes/match-mode.js`)

RMB with the Verdant Blade out is now **guard**. The blade blends to a flat cross-view pose
(readable at a glance from third person too, since it's the same view-model group).

`_deflect()` scans live projectiles each frame: hostile, inbound (`to·vel < 0`), within
`SABER.guardRange` 3.2m and inside `SABER.guardArc` 1.1rad of your aim. Those get their
velocity rewritten along your aim at 1.15× speed, ownership and team flipped to you, damage
×1.25, and recoloured saber-green with a small burst + hit sound.

The cost is real: you cannot guard mid-swing, and `startSwing()` refuses while guarding. Hold
guard and you are not threatening anyone — exactly the commitment the triangle needs.

**Net effect:** the two weapon families finally interact. Arcs zone the approach, guard
punishes the lazy shot, and the swing is the thing you have to drop guard to throw.

## 3. Shared Focus (`src/modes/match-mode.js`)

`_swapWeapon` now carries the current charge `value` onto the incoming weapon and keeps half
the outgoing cooldown. Q-mashing was a free full meter every 3 slots; now the meter is yours,
not the tool's. This is the minimal, non-invasive version of the director's "one Focus meter" —
the HUD still reads `activeCharge`, so nothing downstream changed.

## Not done / next

- Guard does not yet **stagger** on a broken guard (director's 0.9s). That needs a networked
  stagger state on participants — a server/room.js change, worth its own PR.
- Remote players can't see anyone guarding; the pose is local-only until guard is in the
  net snapshot.
- Deflection is client-authoritative like every other hit here. Fine for friends, not for
  strangers.
