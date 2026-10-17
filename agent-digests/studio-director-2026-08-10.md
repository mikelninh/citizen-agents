# 🎬 Studio Director — Direction Brief, 2026-08-10

Repo: `mikelninh/bla-keks-world` · branch `studio/director-2026-08-10` · head `0bd23bd`
Read: `README.md`, `src/modes/match-mode.js`, `src/modes/weapon.js`, `src/modes/weapons/{saber,projectiles,tools}.js`, `src/modes/botbrain.js`, `src/shared/{match,items}.js`, `server/room.js`, `src/entities/*`

---

## VISION

BlaKeks World is a **handmade toy planet where eight friends duel with craft-supplies**, and the fantasy is Nostale's class-based real-time combat compressed into a 3-minute arena round: you can *see* every threat in flight, you can *read* every commitment, and you die to a decision, not to a ping. A bubble arcing at you is a question — dodge, block, or trade? The Verdant Blade closing on you is a countdown you can hear (`audio.saberHum`). Ranged is **positioning and prediction**; melee is **movement and timing**; neither is the "real" weapon and neither is the panic button. Everything is legible at 40 metres in toon shading with no HUD text — colour, arc, trail, sound. Rounds should end in a moment worth clipping, not in an attrition wash.

---

## WHAT I CHALLENGE

1. **Bots play a different game than humans — literally different code.** `src/modes/botbrain.js:3` still imports `WEAPON, applySpread, traceShot` from the *dead* carbine module `src/modes/weapon.js`, and line 246-254 does an instant hitscan out to `WEAPON.range = 130` for 26 damage (×1.5 headshot). Meanwhile every human fires pooled, gravity-affected, dodgeable projectiles from `weapons/tools.js` (`petalbow` is the *fastest* at 62 m/s with gravity 1.2). The whole design thesis in the `projectiles.js` header comment — *"a hitscan line says you were shot, a bubble drifting toward you says here it comes, move"* — is contradicted by every bot in the room. `weapon.js` (Magazine, buildViewModel carbine) is 158 lines of unreferenced legacy dragging a second damage economy (`WEAPON.damage`) alongside `stats.soak`. This is the single biggest lie in the build.

2. **The saber isn't a class — it's a free third slot with no opportunity cost.** `_initLoadout()` (match-mode.js:875-899) hands *everyone* the same shape: splatter + rolled secondary + `leafblade` at hard-coded `'enchanted'` rarity. And `this.charges` is **one `Charge` per weapon**, so swapping with Q/wheel hands you a fresh full meter instantly. There is no resource decision anywhere in the loop. Worse, `leafblade` is `soak: 100` — a guaranteed one-shot — with `SABER.reach 3.4` and `SABER.arc 1.5` rad, which is an **86° cone**. That is not a timing weapon, that is a shotgun you swing. Rock-paper-scissors cannot exist when one option strictly dominates at its range and costs nothing to hold.

3. **The server does not know what a weapon is.** `MatchSim._hit()` (`src/shared/match.js:242-263`) validates only `dist(shooter,target) <= MAX_DAMAGE_RANGE` and clamps damage to 120. A client can send `{type:'hit', damage:120}` from any distance inside that cap with no weapon, no cooldown check, no charge check. `server/room.js:158` (`case 'ev'`) forwards it unfiltered. The bot path is worse: `case 'botEv'` spoofs `msg.from`. Melee especially deserves authority — a 3.4 m weapon accepted at 30 m is the exploit that kills a public playtest.

4. **Melee has commitment but no counterplay, so nobody will ever approach.** `Saber.hits()` correctly gates on the middle of the swing (`swing 0.25..0.7`) and `SABER.recovery 0.22` punishes a whiff — good instincts. But there is nothing on the *defending* side: no block, no parry, no deflect, no dash. Against four players lobbing arcs, walking into 3.4 m reach is never correct. `player.ads` is forced false for the blade (match-mode.js:968) so right-mouse is sitting **completely unused** while holding the saber. That free input is the whole opportunity.

---

## THE ONE BIG IDEA — **The Duel Triangle** (guard / swing / shot)

Give melee a defensive verb and both families become first-class in one move.

**Bind right-mouse while the blade is out to GUARD.** Blade rotates to a vertical parry pose, `Focus` drains ~0.35/s while held, movement speed ×0.65. Any enemy projectile whose next step lands inside a 70° cone in front of the guard is **deflected** — `it.vel` mirrored about the guard normal with a +15% speed bonus, `it.owner` reassigned to the guarder, `it.team` flipped, colour lerped toward the guarder's team tint, plus `projectiles.burst()` and a metallic ping. A deflected projectile can kill its original sender.

That closes the triangle:
- **Shot beats Approach** — arcs zone the closing saber; you can't guard while sprinting.
- **Guard beats Shot** — a read on a `petalbow` shot turns their 52-soak commitment into your kill.
- **Swing beats Guard** — a swing landing on a guarding player does no damage but **breaks guard**: Focus zeroed, 0.9 s stagger where they cannot guard or swing. That's the melee player's answer to a turtle.

And **one shared `Focus` meter for the whole loadout** kills the free-swap exploit in the same session: swapping costs 0.12, guarding drains, swinging costs 0.5. Suddenly the loop is *manage a meter across three ranges* instead of *press Q for more ammo*.

One engineer, one session: a guard state in `Saber`, a `deflect()` pass in `Projectiles.update`, a shared meter in `tools.js`, wiring in `_tacticalLocal`.

---

## STUDIO DIRECTIVES (ordered, for the engineer agent)

### 1. Unify the resource — one shared Focus meter
**Files:** `src/modes/weapons/tools.js`, `src/modes/match-mode.js`
Replace the per-weapon `this.charges = this.loadout.map(...)` array (match-mode.js:887-899) with a single shared `Focus` instance. Per-weapon `cost` stays; add `swapCost: 0.12` charged in `_swapWeapon()`. `leafblade.cost` → `0.5`, add `guardDrain: 0.35`. Regen becomes a single rate (start `0.30/s`) with a 0.6 s post-action delay before regen resumes.
**Acceptance:** Q-spamming through all three slots cannot produce more total shots than staying on one weapon; the HUD charge bar is continuous across a swap (no jump to full); firing `splatter` dry means the blade also cannot swing until Focus ≥ 0.5.

### 2. Ship the Duel Triangle — guard, deflect, guard-break
**Files:** `src/modes/weapons/saber.js`, `src/modes/weapons/projectiles.js`, `src/modes/match-mode.js`
- `saber.js`: add `guarding` state + `setGuard(bool)` (vertical pose, blade flare, `guardDir()` returning the world-space guard normal). Cannot guard while `swinging` or during `cooldown`, or while `staggered > 0`.
- `projectiles.js`: `update()` takes an optional `guards: [{id, team, origin, dir}]`; before the player-hit test, if the projectile's next position is within 2.2 m of a guard origin and inside a 70° cone of `dir`, reflect `vel`, ×1.15 speed, reassign `owner`/`team`, recolour, `burst(point, color, 10, 5)`, and continue instead of retiring.
- `match-mode.js`: in the `leafblade` branch of `_tacticalLocal` (line ~967), stop forcing `player.ads = false` — map `input.mouse.right` to guard; move speed ×0.65 while guarding. If `Saber.hits()` strikes a guarding target, send `{type:'guardBreak', target}` instead of damage.
**Acceptance:** in an offline match vs bots, a held guard visibly bounces an incoming bubble back and a deflected projectile can down its original owner; swinging into a guarding bot deals 0 damage and leaves that bot unable to guard or swing for 0.9 s; guard held with empty Focus drops automatically.

### 3. Delete the ghost carbine — one weapon economy, and let the server enforce it
**Files:** `src/modes/botbrain.js`, `src/modes/weapon.js` (delete), `src/shared/match.js`, `server/room.js`
- Port `botbrain.js:240-256` off `traceShot`/`WEAPON` onto `Projectiles.spawn()` with real `TOOLS` stats + lead prediction (aim at `target.pos + vel * dist/speed`). Bots must miss for the same reasons players do.
- Delete `src/modes/weapon.js` entirely once `raySphere`/`applySpread` are re-homed (`raySphere` is worth keeping in a small `src/shared/geom.js`).
- `match.js _hit()`: require `evt.weapon` ∈ `TOOL_IDS`, clamp damage to that tool's max soak at legendary rarity (`soak * 1.38`), and range-check per kind — `melee` ≤ 4.5 m, everything else ≤ `MAX_DAMAGE_RANGE`. Add a per-player minimum interval equal to that tool's `rate * 0.8`. Drop violating events silently and count them on the player record.
**Acceptance:** grep for `weapon.js`, `traceShot`, `Magazine`, `WEAPON.` returns nothing outside git history; a hand-crafted `{type:'hit', weapon:'leafblade', damage:120}` sent from 20 m is rejected by the sim; bot kills feel dodgeable in a 1v3 offline round.

---

## PERSONAL CHALLENGE FOR MIKEL

You said **BOTH** — good call, and directive 2 is what "both" actually costs. Now the decision only you can make:

**Is the Verdant Blade a universal third slot, or is it a CLASS?**

Right now `_initLoadout` gives it to everyone at hard-coded `'enchanted'`, which means BlaKeks has no classes — it has one character holding three things. Nostale is memorable because a swordsman *cannot* become an archer mid-fight; the identity is the constraint. So: **do you commit to picking a class at match start — Blade (saber + one short-range tool, extra Focus regen, a dash) vs Petal (two ranged tools, no saber, guard replaced by a one-charge roll) — or does everyone keep everything and you accept the game is a soup?**

I want Blade vs Petal. It makes the Duel Triangle a *matchup* instead of a mode you toggle with Q, and it gives your friends something to argue about in the lobby, which is worth more than any balance patch. But the loop is your call, and it needs to be made before the engineer hardens `_initLoadout`.

Answer with one word and I'll build the class brief next run.
