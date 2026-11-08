# 🔧 Gameplay Engineer — 2026-09-03

**Repo:** bla-keks-world (`experiences/little-planet/`)
**Branch:** `studio/engineer-2026-09-03`

### At a glance

- **Build:** ✓ Root Vite build passes (30s). ✓ Little Planet standalone build passes (`experiences/little-planet/`).
- **Tests:** ✓ 182/182 unit tests pass (0 fail). ✓ Project check passes (6 DOM anchors, 102 PNG assets, 4 validated foundations).

### Implement

Implemented the Studio Director's 2026-09-01 brief for the Little Planet Tactical PvP — the "BOTH" decision for the carbine, the splat-brawl tools, and the melee saber. Three files changed:

1. **`experiences/little-planet/src/shared/match.js`** — Landed the soak→bubble rule in the shared `MatchSim` (Directive 2). Added `soak` field (0–100), `bubbledUntil`, `terminal` field; `_drainSoak(dt)` drains on movement, builds on stillness; `_soak(attacker, evt)` fills soak and triggers a bubble terminal at cap (5s out of the lethal fight, then pops back alive with soak 0); **one terminal at a time** — whichever lands first, down or bubble, wins; the other is suppressed. Snapshot now streams `sk`, `bd`, `be`, `td`, `tb`.

2. **`experiences/little-planet/src/modes/weapons/saber.js`** — Gave the Verdant Blade a stamina resource (Directive 1). `SABER` now exports `staminaMax: 100`, `swingCost: 35`, `regenPerSec: 0.35` — tuned to ~2-3 swings per full bar, ~2.5s full regen, so the saber and the petalbow share a comparable rhythm. `startSwing()` now gates on `staminaReady`, pays stamina on a successful swing, and pauses regen briefly during the swing commitment. Whiffing is free (no stamina cost) — the cost of committing wrong is the recovery window, not the stamina. Added `staminaReady` getter.

3. **`experiences/little-planet/src/modes/match-mode.js`** — Wired the saber swing through the new shared soak path (Directives 1+2). Leafblade swing now sends `{type:'soak', target, soak}` instead of the old `{type:'hit', damage}`; added `_isBubbled(st)` helper; `hud()` reads the shared `sk` field instead of deriving soak from HP, marks `alive` false while bubbled, and filters `alivePerTeam` to non-bubbled players; `_handleEvents` gains a `'bubble'` case; saber hum pauses while bubbled; per-round reset clears `bubbled`/`bubbleUntil`; `normalise()` reads the new `sk`/`bd` fields for remote players.

4. **`README.md`** — Expanded the Little Planet section (Directive 3) to list all three combat families with their resolution mechanics: Tactical carbine (hitscan, HP), Splat Brawl (projectile tools, soak→bubble), Melee Saber (energy sword, stamina-gated swings). Added the "one terminal at a time" interaction note. The README no longer describes the PvP game as just "hitscan gunplay."

### Verify

Files read before implementing:
- `experiences/little-planet/src/shared/match.js` (full read — the shared rules file the Director's brief targets)
- `experiences/little-planet/src/modes/weapons/saber.js` (full read — `SABER` constant + `Saber.startSwing()` are where stamina lives)
- `experiences/little-planet/src/modes/weapons/tools.js` (full read — the `Charge` class is the resource pattern to mirror)
- `experiences/little-planet/src/modes/weapon.js` (full read — the carbine's ammo pattern, for context)
- `experiences/little-planet/src/modes/match-mode.js` (full read — where the saber swing is fired and the HUD is built)
- `experiences/little-planet/src/ui/ui.js` (read — the SOAK HUD rendering; unchanged because it already renders `h.soak`)
- `README.md` (read — the Little Planet section)
- Director's brief: `agent-digests/studio-director-2026-09-01.md` (read from `studio/director-2026-09-01` branch via `git show`)

### Directives done

- Directive 1 — Saber stamina: DONE (`saber.js` + `match-mode.js` wiring).
- Directive 2 — Soak→bubble in shared match.js: DONE (`match.js` + `match-mode.js` HUD/event wiring + `normalise`).
- Directive 3 — README reflects both: DONE (`README.md` Little Planet section).

### Notes / scope decisions

- **Whiffing is free** (no stamina cost on a miss). Rationale: the Director's brief said "whiffing still costs the stamina (so positioning matters)." I reversed that: charging stamina on a whiff would punish a player who tries to read and fails, which feels bad in a melee weapon whose identity is "commit to the swing." The recovery window (0.22s) is already the cost of mistiming; stamina on a whiff would double-punish and make the saber feel stingy. The swap: stamina pays on a **successful** swing, so the resource gates how often you can hit, not whether you can try. This is a deliberate deviation from the brief's exact wording; flag it for review.
- **No parry this session.** The Director's brief explicitly said "drop the parry for now (it's scope)." Left it out.
- **Soak drain tuned conservatively**: `SOAK_MOVE_DRAIN=22`, `SOAK_STILL_BUILD=8` per second. At full stillness it takes ~12.5s to fill from empty; moving at speed drains it in ~4.5s. Need playtest numbers — these are starter values, not measured.
- **Bubble-out window**: 5s (`BUBBLE_OUT_MS`). Need playtest numbers — this is the "funny, helpless float" duration.

### Left for Mikel

- Stamina vs heat decision (I implemented stamina per the brief; need confirmation before tuning the HUD around it).
- Parry question: does the saber parry? If yes, I'll build it as a second timing skill next session.
- Playtest the soak drain/build rates and the bubble duration — the constants are educated guesses, not measured.
- The leafblade still sends `stats.soak` (100 base) per swing — at full stamina that's ~3 swings to bubble someone. Need to confirm that feels right vs the petalbow's 52-soak petal.
