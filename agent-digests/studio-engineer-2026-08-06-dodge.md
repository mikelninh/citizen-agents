# 🔧 Gameplay Engineer — 2026-08-06 (Dodge Roll)

Branch: `studio/engineer-2026-08-06-dodge` · base: `main` @ `0bd23bd`
Directive: **Studio Director, third pass — Directive 2, Dodge Roll (P0)**

---

## What I built

The director's third-pass critique was blunt and correct:

> `SPEEDS = { walk: 5.4, sprint: 8.6, ... }` and that is the entire movement vocabulary […]
> a `petalbow` petal at `speed: 62` covers 20m in 0.32s. You cannot walk out of that.

So the game now has a movement verb.

**Double-tap `W`/`A`/`S`/`D` (or the arrow keys) → dodge roll.**
0.35s committed burst at **14 m/s**, **0.12s of i-frames** at the front, **0.45s** of recovery
before you can roll again.

### The five touched files

| File | Change |
|---|---|
| `src/core/input.js` | New double-tap edge signal — `DOUBLE_TAP_WINDOW = 0.28s`, `doubleTapped(code)`, cleared in `endFrame()` like `justPressed` |
| `src/entities/player.js` | `DODGE` constants, `dodge(dirX, dirZ)`, `dodging` / `dodgeCharge` getters, `_dodgeInput()`, timers + velocity override in `_move()` |
| `src/modes/match-mode.js` | While `iframes > 0` the local player is filtered out of the target list; `dodge` / `dodgeActive` added to the HUD payload |
| `src/ui/ui.js` | `.dodge-pip` under the crosshair — no number, per the directive |
| `src/ui/styles.css` | Pip styling; dims when ready, cyan glow while the i-frames are live |
| `tools/dodgetest.mjs` | New headless test, 6 assertions on the tap window |

### Design decisions I made, and why

**The roll overrides steering, it does not add to it.** Inside `_move()` the burst is applied
*after* the normal accel/friction/speed-cap block, writing `vel.x`/`vel.z` directly. You commit to a
direction the moment you tap. That is what makes it a decision rather than a sprint button — and it
means the existing movement code is completely unmodified, just superseded for 0.35s.

**Collision still runs.** The override sits above the `world.slide()` integrate step, so you cannot
roll through a wall or off the collision grid.

**`ControlLeft` is not the accessibility alias the director asked for** — `player.js:154` already
binds it to crouch alongside `KeyC`. Rebinding it would have silently broken hide-and-seek, so
double-tap is the only binding for now. Arrow keys work identically to WASD, which covers most of
the intent.

**I-frames are enforced by filtering the target set, not by special-casing damage.** Combat is
shooter-authoritative (`_onProjectileHit`: *"Someone else's shot: we only draw it, the owner reports
it"*), so the honest hook is line 622 — while rolling, the local participant simply is not in the
list that `projectiles.update()` and `_driveBots()` resolve against. Every other participant behaves
byte-for-byte as before.

**Rolling is loud.** `dodge()` raises `noiseLevel` to at least 0.7 so you cannot use it as a free
escape in hide-and-seek.

**Blocked while** crouching, swimming, frozen (hide-phase seeker lockout), already rolling, or on
cooldown. State resets in `spawnAt()` so you never respawn mid-roll.

### Both weapon families, as the lead directed

This is deliberately the *shared* half of the combat foundation:

- **Ranged** gets the answer to a lunging blade — positioning becomes a live skill instead of a
  starting position.
- **Melee** gets its approach tool — roll through the petal, arrive in reach. "Saber = movement +
  timing" is now literally true.

Same button, same cost, opposite purposes. That is the cheapest possible way to serve **BOTH**.

---

## Verification

```
npm run build   → vite v7.3.6, 56 modules transformed, built in 1.86s, exit 0
node tools/dodgetest.mjs
  ok    single tap does not dodge
  ok    double tap inside 0.28s dodges
  ok    double tap clears on endFrame
  ok    third tap is not a second dodge
  ok    taps 1s apart do not dodge
  ok    A then D does not dodge
  all passing
```

Diff is **+116 / −3 across 5 source files**, plus one new test. Explore mode is unaffected — it
shares `Player`, so it gains the roll for free, and its HUD never supplies `h.dodge` so no pip is
drawn there.

---

## What I did NOT do

- **Directive 1 (weapon on the body)** — the higher-value change of the three, but it touches
  `remote.js`, `avatar.js` and the network snapshot. That deserves its own reviewable PR, not a
  second concern bolted onto this one.
- **Directive 3 (The Last Thirty)** — server-authoritative, separate PR.
- **Second-pass Stamina / Guard / Reflect** — genuinely blocked on Mikel.

## Open question for the lead

The director asked whether the roll spends the saber's resource. I shipped it on a **flat cooldown**
because `Stamina` does not exist in the tree yet — but the seam is one line wide. If you answer
**"shared"**, `dodge()` stops checking `dodgeCooldown` and starts checking `stamina.spend(0.30)`,
and every roll becomes a swing you didn't take.

Say the word and it is a five-minute change.
