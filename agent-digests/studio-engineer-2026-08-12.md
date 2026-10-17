# 🔧 Gameplay Engineer — 2026-08-12

**Branch:** `studio/engineer-2026-08-12` · **Repo:** `bla-keks-world` (private)
**Built on the director's 2026-08-10 brief** — the *Duel Triangle* is this week's ONE BIG IDEA.

## What I shipped

The Battle Arena combat sim (`src/game/spatial-duel.js`) already had parry, guard,
volleys and projectiles — but the two weapon families (saber / projectile) never
*answered* each other. I closed that gap. Both changes are small, reviewable, and the
fairness gate stayed green (70/70).

### 1. Saber guard deflects projectiles (Duel Triangle, pt. 1)
A melee form (the sabers — Moonthorn, Oathstar; `range < 13` per `RANGED_BASIC_MIN`)
holding guard now **turns an incoming bolt back at its owner** instead of eating a 45%
hit. The bolt is re-owned by the defender and resolves next tick, so a parry or a
second guard can answer it. A bounce cap (3) stops two sabers ping-ponging one bolt.

- **Parry still wins:** a saber *inside its parry window* negates as before; only a
  plain guard deflects. (This fixed a regression where deflect ran before the parry
  check and broke the existing parry unit test.)
- **Balance:** the deflected bolt returns at `REFLECT_DAMAGE_SCALE = 0.5`. Full-value
  deflects handed melee a free damage stream that pushed Oathstar to 93–100% on the
  gate. The deflect also *consumes* the guard that produced it — one turned shot per
  guard cast, not a damage engine.

### 2. Committed saber swing breaks guard + 0.9s stagger (Duel Triangle, pt. 2)
A saber **signature** swing that lands on a guarding foe shatters the guard and
staggers them 0.9s (`staggerUntil`). While staggered they cannot raise a new guard.
No damage multiplier — the stagger is a commitment denial, not a snowball.

- **Why signature-only:** my first pass let *every* swing break guard, which left
  guard-reliant kits (Hearthsong, Mosslight) defenceless for their whole cooldown and
  ran Oathstar to 82–100%. Restricting to the long-cooldown signature pulled every
  matchup back under the 80% bound.

### 3. "Arcs zone the approach" — already true
Ranged basics and Calm Horizon's volley already zone space; the two changes above are
what let a saber *counter* that zoning. Both weapon families now coexist and interact.

## Verified
- `npm test` → **PASS** (project check, fairness gate 70/70, arena headless, unit
  tests, `vite build` green).
- Targeted sim test confirms: deflect fires + reflected bolt hits the shooter; signature
  swing breaks guard + staggers.

## What I deliberately did NOT touch
- **"Shared Focus / Q-swap is free ammo":** Battle Arena already has one shared `focus`
  meter per fighter (skills cost focus, basics refund it). That critique targeted the
  *separate* Little Planet experience, not the Arena.
- **"Bots hitscan-snipe at 130m via dead `src/modes/weapon.js`:"** that path lives in
  `experiences/little-planet/` — a different experience from the Arena. The Arena uses
  proper dodgeable projectiles. Surfaced for a separate pass; out of scope for this
  directed change.

## Decisions for Mikel
1. Guard-break is **signature-only**, not "every swing." If you want basics/setups to
   also break guard, say so and I'll do another balance pass.
2. Deflected bolt returns at **0.5×** damage. Bump `REFLECT_DAMAGE_SCALE` if you want
   the deflect punchier; the gate will tell us if it over-tunes.
3. Still open from the director's brief: **universal third slot vs Blade/Petal classes
   picked at match start?** That's your call — it gates the next class-identity pass.

*No source files outside this change were modified. Build green. Human review only — not merged.*
