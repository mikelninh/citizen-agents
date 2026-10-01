# 🎬 Studio Director — Direction Brief (2026-08-12)

*Read-only director. This brief adds no game code; the engineer implements. Repo: `blakeks-world`, branch `studio/director-2026-08-12`. Honors the lead's 2026-08-06 decision: **melee sabers AND ranged projectiles are both first-class from the start** — no forced choice.*

---

## VISION

BlaKeks World's PvP should feel like a Nostale-style class duel shrunk into one readable Garden Ring: eight friends pick a Worldform, the screen *tells you* who is a saber and who is a bow, and the fight is won by reading spacing and committing at the right instant. The fantasy is **"one clean read beats one clean build."** Saber duelists earn their kills through movement and timing — closing, feinting, parrying, whiffing on purpose; projectile duelists earn theirs through positioning and prediction — kiting, telegraphing, volleying, punishing a standing target. Both must be equally *legible* and equally *lethal*, so a lobby of eight never feels like "the two melee are just worse." Right now the foundation is real and unusually well-tested, but it is built as a ranged-first arena with melee bolted on. This brief pushes it to true parity.

---

## WHAT I CHALLENGE

**1. Melee is structurally second-class, despite the BOTH mandate.**
The ranged/melee cut exists and is respected everywhere (`hasRangedBasic` / `RANGED_BASIC_MIN=13` in `src/game/spatial-duel.js:56-57`, consumed by `chooseSpatialIntent`, `autoAttackStep`, `resolveAction`, the readout). Good. But the *roster* doesn't honor it: of the 8 duel-ready Worldforms in `src/data/character-transformations.js`, only **two** have a melee basic — Moonthorn (range 7) and Oathstar (range 11). The other six (Starfrost 22, Firstlight 20, Hearthsong 15, Mosslight 18, Stormline 13, Dreamtide 22) are ranged. Ranged also owns the entire *mechanic* ecosystem: `VOLLEY_SKILLS` (Calm Horizon, lines 87-102), `WHIFF_PUNISH_SKILLS` (Blackwater Break, 84-85), per-skill `EVADE_MS` (112-114), the auto-range cap, and the *only* shipped timing mechanic, `PARRY_SKILLS` (69-71) — which is melee's lone bright spot and belongs to exactly one fighter. Melee has no resource, no rhythm, no signature of its own. The lead said BOTH first-class; today ranged is the default class and melee is a guest.

**2. Melee auto-attack pays zero commitment while ranged pays a slow — so "saber timing" doesn't exist yet.**
`AUTO_ATTACK_COMMIT_SHARE=.78` and `AUTO_ATTACK_MOVE_PENALTY=.14` (`spatial-duel.js:204-205`) are applied to **ranged basics only** (the comment at 195-198 says so explicitly). That fix was correct for the kiting sniper. But it means a melee fighter gets *free, uninterrupted* contact damage with no tradeoff, while a ranged fighter is slowed every shot. The result: a saber duelist's optimal play is "stand in contact and never stop swinging." That is precisely the anti-pattern the `AUTO_ATTACK_RANGE_SCALE=.32` cap was invented to remove from ranged (lines 150-178) — but melee was exempted, so the problem just moved. There is no stamina/heat pressure creating the "saber = movement + timing" rhythm the lead imagined. Melee combat is currently a contact DPS race, not a timing duel.

**3. Oathstar — one of only two melee fighters — has no working signature.**
`LANE_SKILLS` is shipped **empty** (`spatial-duel.js:148`), with a candid comment (132-148) explaining Fourfold Verdict was disabled because Moonthorn beats Oathstar 82% and the author "was tuning constants rather than understanding the cause." A tank's signature is gated off in the live build, so Oathstar's identity collapses to "slow blader with a parry," and the melee-vs-melee matchup is structurally broken. The lead's BOTH vision needs melee signatures that actually resolve. Disabling a core skill to pass a gate is the gate working backwards.

**4. "Match mode" is strictly 1v1 — there is no 8-friend FFA, the PvP fantasy's destination.**
`duel/arena/arena.js:28` is `matchScore={player:0,opponent:0}` best-of-N rounds between two fighters, and `scripts/check-duel-fairness.mjs:25` filters `FORMS` into **pairwise** 1v1 matches. The combat sim `createSpatialDuel` is hard-wired to `player`/`opponent` (lines 274-293). The 8-friend PvP loop the README sells ("up to 8 friends," "all-vs-all selection") lives only in *Little Planet* (a separate Three.js build), not in the Arena. The lead's directive to "build toward both weapon families coexisting in match mode" can't be honored past a single melee-vs-ranged duel until a multi-actor step exists. This is the biggest structural gap.

---

## THE ONE BIG IDEA

**Saber Stamina — give melee its own first-class resource and rhythm, as the exact mirror of ranged's commit cost.**

Ranged already has a resource story: focus cost per skill + the per-shot move-slow (`AUTO_ATTACK_COMMIT_SHARE`). Melee has *nothing*. Add a `stamina` resource to `buildFighter` (`spatial-duel.js:261-272`) that drains on every melee basic (and on melee dashes), and when it drops below a threshold, **lengthens the swing cooldown / pauses the auto channel** until it regenerates out of contact. Now a saber duelist *must* weave movement between swings — exactly the "movement + timing" identity the lead named — and the ranged/melee rock-paper-scissors gains its second axis: ranged = ammo/heat discipline (focus + slow), melee = stamina discipline (swing + reposition). Ship it **with** a fixed Fourfold Verdict (see Directive 2) so melee arrives with a working signature, not just a new bar. One engineer, one session, fully covered by the existing `npm run check:duel` gate.

---

## STUDIO DIRECTIVES (engineer — ordered, each implementable, all gated by `npm run check:duel`)

**1. Saber Stamina — `src/game/spatial-duel.js` (`buildFighter`, `autoAttackStep`, `getSpatialSkillReadout`).**
Add `stamina`/`maxStamina` to fighters; melee basics (`hasRangedBasic(form)===false`) drain stamina per swing; below a floor, scale up swing cooldown / pause auto until regen (out of contact). Mirror the ranged commit model — do **not** exempt melee this time.
*Acceptance:* `getSpatialSkillReadout` exposes a `stamina` field for melee basics; an `advanceSpatialDuel` loop with a melee fighter swinging continuously measurably slows; `npm run check:duel` stays green (no matchup breaches the 80% bound, no invariant breaks).

**2. Ship Fourfold Verdict — `src/game/spatial-duel.js` (`LANE_SKILLS`, `resolveAction`) + `src/data/character-transformations.js` (`fourfold-verdict`).**
Do **not** tune constants. Find the real cause Moonthorn beats Oathstar 82% (likely Moonthorn's `marked`+`bleed` plus faster `twin-fang` cadence out-trading a tank with *no* working signature), then resolve it with a kit change and enable `LANE_SKILLS` as 4 readable bands (the `bands:4,bandWidth:74,bandGap:38,startAt:24,share:1.3` starting point is already in the file comment, lines 134-137).
*Acceptance:* Fourfold Verdict resolves as 4 dodgeable bands, lands more than the old single disc, AND the Oathstar↔Moonthorn pair moves toward the ~60% baseline without any other pair crossing the 80% bound; gate green.

**3. First step to FFA match mode — `src/game/spatial-duel.js` (new `createSpatialFfa` / multi-actor step) + `scripts/` headless test.**
Introduce a deterministic N-fighter (2–8) step that shares one `projectiles`/`effects` world, so ranged arrows and melee swings coexist in a single arena. Start with a 4-fighter FFA that boots and terminates. This is the structural bet the BOTH decision points at.
*Acceptance:* a headless script spins 4 Worldforms (mix of melee + ranged), runs under the existing 16ms tick, projectiles and melee hits coexist, the bounds/finite-vitals invariants hold, and the fight terminates (no 90s stall); `npm run check:duel` (still 1v1) stays green.

---

## PERSONAL CHALLENGE FOR MIKEL

**Saber combat needs a resource — *stamina* or *heat*?** You said both weapon families are first-class and to weigh "ammo/heat vs stamina." Ranged already has its answer: focus cost + the per-shot move-slow (`AUTO_ATTACK_COMMIT_SHARE`, `spatial-duel.js:204`). For melee I'm proposing **stamina** — drains on swings, regenerates out of contact, forcing the movement-between-swings rhythm. But you might want **heat** instead — builds while swinging, overheats and *forces a vent* (a hard stop, not a slow). They feel different and read differently on a HUD. **Decide: stamina or heat? And does it apply to ALL basics or melee-only?** Your call — I'll lock the constant and write Directive 1 around your answer.
