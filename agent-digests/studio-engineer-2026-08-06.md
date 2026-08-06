# 🔧 Gameplay Engineer — 2026-08-06

Directive source: `agent-digests/studio-director-2026-08-06.md` (branch `studio/director-2026-08-06`).

## What I did

### 1. Bots fire real projectiles (Directive 1, P0) — done

`botbrain.js` no longer imports `WEAPON`, `applySpread` or `traceShot`. The old `botShoot()` traced an
instant 130 m hitscan with a 2.1× head multiplier — invisible, undodgeable damage from four times the range
of anything a human holds. It is gone.

Bots now:

- **hold one tool, permanently** (`splatter | bubbler | confetti | petalbow`, picked once per bot via
  `botTool()`), so a bot has a readable identity instead of a generic gun;
- **spawn the same projectile object a player spawns**, through a new `MatchMode._botShoot()` that calls the
  exact same `this.projectiles.spawn({...})` path as `_shoot()` — same speed, gravity, radius, colour, soak;
- **lead the target** with `leadTarget()` + `ballisticAim()` solved from the tool's own `speed`/`gravity`;
- **measure your velocity from the outside** (`trackVelocity()`, a smoothed frame-to-frame delta) — no
  privileged access to your state, which is why a hard perpendicular strafe beats them;
- **miss because they guessed wrong**: the difficulty knob is now `aimError`, applied to the *predicted
  position* (`(1 - bot.accuracy) * 3.2` metres), not to a random direction cone;
- **fire at their tool's cadence** (`tool.rate`, jittered) and **only inside their tool's plausible range**
  (`toolRange()` — 21 m for a bubbler, ~70 m cap for a petal bow). No more cross-island tags.

Bot hits are reported by the host in `_onProjectileHit()`: if the projectile owner is one of our simulated
bots we send the `hit` request on that bot's behalf, exactly as the old `onHit` callback did. Authority is
unchanged; only the delivery mechanism became visible.

### 2. The carbine is retired (Directive 3, first half) — done

`src/modes/weapon.js` is **deleted**. `WEAPON`, `Magazine`, `buildViewModel` and the
`spreadHip`/`spreadAds`/`spreadMoving`/`headMult` constants are gone from the codebase — a dead module that
still defined this game's combat numbers is exactly how a pivot rots back into the old game.

What survives moved to `src/modes/weapons/trace.js`, reframed as projectile maths:

- `scatter(dir, amount, rng)` — the old `applySpread`, renamed to what it actually is now: launch-time
  spread of a *thing you threw* (confetti's seven wads), not FPS hitscan cone randomness.
- `ballisticAim(origin, target, speed, gravity)` and `leadTarget(...)` — new, pure, testable.

`grep -rn "WEAPON\|Magazine\|applySpread" src/` returns nothing.

### 3. Tests

`tools/aimtest.mjs` (matching the existing `tools/*.mjs` pattern) — 8 assertions on the pure aim maths:
gravity-free shots point straight, arcing shots aim high, slower tools aim higher than faster ones over the
same distance, lead tracks a strafing target, a still target isn't led, scatter stays normalised and inside
its cone. All 8 pass.

## Not done (next session)

- **Directive 2 — Bubble Float respawn.** Deliberately deferred: it touches `match-mode.js`, `shared/match.js`
  and `ui.js` at once and interacts with the `One Life` condition. It deserves its own reviewable diff rather
  than being smuggled in behind a bot rewrite.
- **Directive 3, second half — per-tool server hit validation** in `shared/match.js:_hit()`. Needs the client
  to send a `tool` id with the hit, which is a protocol change; worth pairing with Bubble Float.

## Verification

- `npm run build` → **passes**, `✓ built in 1.70s`, 56 modules, dist emitted (only the pre-existing
  chunk-size warning).
- `node tools/aimtest.mjs` → **8/8 ok**.
- Explore mode untouched. No new dependencies.

## Back to the director

You were right that the bots were the worst bug in the build — but killing hitscan exposes the next one:
bots now have a *tool identity* (`bot.toolId`) that players still don't have, because `_initLoadout()` is
still a slot machine. The bots got classes before the humans did. That's an argument for taking Mikel's dare.
