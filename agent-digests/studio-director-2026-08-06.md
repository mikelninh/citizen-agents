# 🎬 Studio Director Brief — 2026-08-06

Repo: `bla-keks-world` · Branch: `studio/director-2026-08-06` · HEAD: `0bd23bd`

Read: `README.md`, `src/modes/match-mode.js`, `src/modes/weapon.js`, `src/modes/weapons/{tools,saber,projectiles}.js`,
`src/modes/botbrain.js`, `src/shared/{items,match,conditions}.js`, `server/room.js`, `src/entities/`, `src/render/fx.js`.

---

## VISION

Bla Keks World's PvP fantasy is **a playground brawl with the readability of an arena shooter**. The tools pivot in
`src/modes/weapons/tools.js` is the best design decision in this repo: nobody dies, they get *soaked* and pop into a
bubble — losing is funny, so players re-engage instead of hiding. Lean all the way in. Every projectile is a visible,
dodgeable object; every hit leaves a mark on the world; every elimination is a comedy beat, not a punishment. From
Nostale steal **class identity** — you should know within two seconds of seeing someone move what they can do to you
and what you can do back. From Splatoon steal **the world as scoreboard** — paint and bubbles should persist so the
arena tells you where the fight is happening. From Quake steal **short respawn loops**. The target emotion is:
*"one more round"* — 90-second rounds where you were bubbled three times, laughed each time, and still nearly won.

---

## WHAT I CHALLENGE

**1. The bots are still playing the old game, and it's the worst bug in the build.**
`src/modes/botbrain.js:3` imports `WEAPON, applySpread, traceShot` from `src/modes/weapon.js` and line 246 fires
`traceShot(...)` — instant hitscan, 130m range, `headMult: 2.1`. Meanwhile human players fire slow arcing objects
(`bubbler` speed 19 with gravity 7; `petalbow` speed 62). So bots deal invisible, undodgeable, instant, headshot-capable
damage from four times the effective range of anything a player holds. The entire "you can see it coming and dodge it"
promise written in the `tools.js` header comment is false the moment a bot is in the match — and per the README, bot
fill is the default. This isn't a balance tweak; it's two different games in one room.

**2. `src/modes/weapon.js` is a ghost that still steers design.**
The carbine is gone from the fiction, but `WEAPON` (damage 26, magazine 24, reload 1.9, spreadAds) and `Magazine` are
still live exports, `buildViewModel()` still builds a grey military carbine, and `match-mode.js:10` still imports
`applySpread` from it. Dead code that defines combat constants is how a pivot quietly rots back to the old game.
The spread model itself is an FPS-hitscan idiom (`spreadHip`/`spreadAds`/`spreadMoving`) bolted onto a projectile
game where cone randomness just means "your visible bubble lied to you."

**3. There is no class. There is a slot machine.**
`_initLoadout()` (`match-mode.js:875`) hands everyone `splatter` + a random one of `bubbler|confetti|petalbow` +
`leafblade`, each with a `rollRarity()` multiplier. The comment defends this as "a hand you are dealt" — but the
result is that all eight players in a lobby are the same fuzzy generalist with slightly different RNG numbers.
Nobody can say "I'm the sniper" or "I'm the rusher." There's no counterplay to read, no team composition, no reason to
call out a role in voice chat, and rarity rolls mean two players with the identical tool have different damage for
reasons neither can see. That's the *bad* Nostale (gear RNG), not the good Nostale (class fantasy).

**4. Getting bubbled removes you from the game for up to a full round.**
`match-mode.js:480` — `'You are down — watching the round out.'` — and `_respawnForRound()` only fires on
`roundStart`. Spectating a team-mate (`match-mode.js:543`) is a decent consolation, but the funniest thing in the
game (the bubble pop) is also the thing that takes the controller out of your hands. With the `One Life` condition
in `conditions.js` already existing as an *opt-in* modifier, permadeath-per-round shouldn't also be the default.

**5. Server validation is one number wide.**
`src/shared/match.js:242` `_hit()` checks distance against a single `MAX_DAMAGE_RANGE` and clamps damage to 120.
That's fine for friends — but it means the `petalbow` and the `leafblade` (reach 3.4) share a range check, so a melee
tool can legally hit from across the plaza. Cheap fix, real feel improvement.

---

## THE ONE BIG IDEA

### Make bots play by projectile rules — then make eliminations a 6-second respawn.

**The problem in one line:** the game's core promise is *"you can see it coming and dodge"*, and against bots it is a lie.

**The change, in one session:**

1. Rip hitscan out of `botbrain.js`. Bots emit the *same* projectile a player would: given the bot's held tool stats
   from `TOOLS`, spawn a real projectile via the same path `match-mode.js:_shoot()` uses. Bots must **lead their
   target** (solve for `speed`/`gravity`) and must **miss** when the target is strafing — inaccuracy comes from bad
   prediction, not from a random cone.
2. Delete `spreadHip`/`spreadAds`/`WEAPON`/`Magazine`/`buildViewModel` from `weapon.js`; keep `raySphere` and a
   trimmed `traceShot` (the leafblade still needs a short-range trace). Move them to `weapons/trace.js`.
3. Replace round-lockout death with a **Bubble Float**: on elimination, the player becomes a floating bubble for
   6 seconds — they can drift with WASD (slowly, no attacking), watch the fight, and pop back in at their team spawn
   with a 1.5s invulnerability shimmer. Score the *tag*, not the removal.

**Why this is the highest-leverage change:** it makes every fight legible, makes bots feel like opponents instead of
aimbots, and cuts dead time to near zero — which is what turns a 3-round demo into a 40-minute session.

---

## STUDIO DIRECTIVES

### 1. Bots fire real projectiles (P0)
- **Files:** `src/modes/botbrain.js`, `src/modes/match-mode.js` (expose the spawn path), `src/modes/weapons/projectiles.js`
- **Change:** Remove the `traceShot` fire path at `botbrain.js:246`. Give each bot a held tool id from `TOOLS`; on fire,
  spawn the same projectile object the local player spawns, with a lead-prediction aim solved from target velocity and
  the tool's `speed`/`gravity`. Add a per-bot `aimError` scalar (difficulty) applied to the *predicted target position*,
  not the direction cone.
- **Acceptance:** No import of `WEAPON`/`traceShot` remains in `botbrain.js`. Standing still in the open, a bot hits you
  regularly; strafing perpendicular at sprint speed, you can dodge >60% of shots. Every bot shot is a visible object
  on screen. No bot damage lands from beyond its tool's realistic travel range.

### 2. Bubble Float respawn (P0)
- **Files:** `src/modes/match-mode.js` (`:475–:485`, `_respawnForRound`), `src/shared/match.js` (`_hit`, elimination path), `src/ui/ui.js`
- **Change:** On elimination in `tactical`, enter a `bubbled` state for 6s: camera rises, slow WASD drift, no fire input,
  full-screen soft-bubble vignette. Then respawn at team spawn with 1.5s invulnerability (visible shimmer, no damage taken
  or dealt). Keep the `One Life` condition working exactly as today — it *disables* the respawn. Round score counts tags.
- **Acceptance:** In a tactical round you are never out of control of a camera for more than 6s. `One Life` still ends
  your round on the first bubble. Kill feed reads "X bubbled Y". Invuln cannot be used to score.

### 3. Retire the carbine, tighten hit validation (P1)
- **Files:** `src/modes/weapon.js` → `src/modes/weapons/trace.js`, `src/modes/match-mode.js:10`, `src/shared/match.js:242`
- **Change:** Delete `WEAPON`, `Magazine`, `buildViewModel`, `applySpread` and the `spread*` constants. Keep `raySphere`
  and a `traceMelee(origin, dir, targets, reach)` used by the leafblade. In `_hit()`, accept an optional `tool` id from
  the client and validate distance against that tool's plausible range (`leafblade` → `reach + TAG_TOLERANCE`), falling
  back to `MAX_DAMAGE_RANGE`.
- **Acceptance:** `grep -rn "WEAPON\|Magazine\|applySpread" src/` returns nothing. Game boots, tactical and hide&seek both
  play. A forged `{type:'hit', tool:'leafblade'}` from 20m away is rejected by the server.

---

## PERSONAL CHALLENGE FOR MIKEL

`_initLoadout()` rolls a random secondary and a random rarity for every player, every match. That is a decision only
you can unmake.

**The dare: kill the rarity roll and give me four named classes by next week.**

Something like — **Splasher** (splatter, high mobility, no range), **Bubbler** (bubbler, area denial + slow),
**Petal** (petalbow, one-shot-ish at range, punished up close), **Blade** (leafblade + dash, terrifying in a corridor,
free food in the open). Same tools you already built. No new art. Chosen in the lobby, visible on the avatar's ring
colour and silhouette.

**The question you have to answer first:** *is Bla Keks World a game about **who you picked**, or a game about **what
you found**?* Right now the code is quietly voting "what you found" (rarity rolls, item field, random secondary) while
your README pitches "fight over it with 8 friends" — which is a **who you picked** promise. Pick one. If it's classes,
directive #4 next week is deleting `RARITY` and I will happily write that brief. If it's loot, then rarity has to
become *visible, tradeable and earned* — not a hidden multiplier nobody can see.

You can't have both. Which is it?


---

# 🎬 SECOND PASS — same day, deeper cut

_A second director review ran later on 2026-08-06. It is appended rather than overwriting the first pass; where they disagree, the lead decides._


Repo: `bla-keks-world` @ `0bd23bd` ("Update GitHub Sponsors funding button")
Read: `README.md`, `src/modes/match-mode.js`, `src/modes/weapon.js`, `src/modes/weapons/{saber,projectiles,tools}.js`, `src/shared/{match,items}.js`, `server/room.js`

---

## VISION

BlaKeks World should feel like **Nostale's arena moments rendered in toy plastic**: eight friends on a hand-made planet, every silhouette readable at 40 metres, every attack a *visible object in flight* or a *glowing arc through space* — never an invisible line and a number. The fantasy is not "shooter": it's **duelist vs. artillerist**. The saber player is a shark — they must close distance, read your rhythm, and commit; their skill is movement and timing. The tool player is a sniper-gardener — they must hold space, lead the arc, and deny approach; their skill is positioning and prediction. The joy is the *moment of contact*: a saber flashing through a bubble, a petal punishing a whiffed swing, a splat that everyone in the lobby sees and laughs at. Losing must be funny (you pop into a bubble and float away), winning must be legible (everyone saw *why*). Both weapon families are first-class citizens of the same match, and the match is only interesting because they beat each other in a circle.

---

## WHAT I CHALLENGE

**1. `src/modes/weapon.js` is a ghost. Kill it or own it.**
It still exports `WEAPON` (damage 26, rpm 460, magazine 24, `spreadAds`, `headMult: 2.1`), `Magazine`, `traceShot()` with headshot spheres, and `buildViewModel()` for a *tactical carbine*. Meanwhile `match-mode.js` imports `tools.js` and `saber.js` and never touches any of it. You have two contradictory combat philosophies in the tree at once — hitscan-with-reloads and visible-projectile-with-charge. The tools.js docstring literally argues against everything weapon.js implements. That 158-line file is a landmine for the next engineer and a signal that the pivot isn't finished.

**2. The saber has no economy of its own — it borrows the gun's.**
`TOOLS.leafblade` is `{ soak: 100, cost: 0.5, regen: 0.42, rate: 0.62 }` and shares the exact same `Charge` class as `bubbler` and `petalbow`. So the melee fantasy — movement + timing — is currently expressed by *one* thing: the `swing >= 0.25 && swing <= 0.7` window in `Saber.hits()`. There is no whiff punish (`recovery: 0.22` is nothing), no defense, no approach cost, no reason to feel clever. And `soak: 100` at `enchanted` rarity (×1.22) is a guaranteed one-shot: getting close is *all* the skill, and once you're close it's a coinflip. That's not a duelist, that's a lottery ticket.

**3. The server can't tell a 3.4m saber cut from a 60m petal — `_hit()` is a rubber stamp.**
`src/shared/match.js:242` validates exactly three things: same-team, `dist > MAX_DAMAGE_RANGE`, and `clamp(damage, 0, 120)`. There is no `weaponId` on the hit event, so there is no per-weapon range check, no fire-rate check, no charge check. `server/room.js` just forwards `case 'ev'` straight into `match.request()`. With 8 friends this is fine; the first time someone opens devtools it is not. More importantly it's a *design* problem: the server doesn't know what weapons exist, so you can never balance saber vs. ranged authoritatively.

**4. Five tools, zero classes, zero rock-paper-scissors.**
`TOOLS` entries differ only by numbers (soak/speed/gravity/spread). Every player carries a loadout that includes the leafblade *and* ranged tools (`match-mode.js:884`), so there is no identity to read, no matchup to learn, no "oh, he's a blade, back up". Nostale works because you can see a class and instantly know the threat model. Right now there is exactly one verb — attack — and no defensive verb anywhere in the codebase. No block, no dash, no reflect. A combat system with one verb has no depth to find.

---

## THE ONE BIG IDEA — **Guard & Reflect**

Give the game its **second verb**, and use it to make both weapon families first-class *by making them counter each other*.

**Hold RMB = Guard.** It means something different per family, and that difference is the class identity:

- **Saber guard**: the blade sweeps to a vertical block pose. Incoming projectiles that enter a ~110° frontal cone are **absorbed** — and if the guard was raised within **0.22s** before impact, they are **reflected**: velocity flipped (plus aim-nudge toward the shooter), `owner`/`team` swapped, damage ×1.25. Guard drains a new **Stamina** bar (separate from `Charge`). Empty stamina = **guard break**: 1.0s stagger, cannot swing, blade dims. Swinging also costs stamina, so the duelist must budget offense vs. defense — that is the timing game.
- **Ranged guard** (unchanged in spirit): RMB stays aim/zoom. Ranged keeps `Charge`; melee gets `Stamina`. Two resources, two rhythms.

**The RPS that falls out, for free:**
- Saber **beats** flat-trajectory ranged up close (`petalbow` gravity 1.2, `splatter` gravity 2.5) — reflect punishes anyone who panics and fires into a raised blade.
- Ranged **beats** saber at distance — stamina drains while guarding, so a blade that turtles across open ground arrives broken.
- **Lob/burst beats guard** — `bubbler` (gravity 7) and `confetti` (7 shots, spread 0.16) arc over or flood around the cone. The counter to a turtle is the party popper. That's a joke *and* a mechanic.

Then, to make the identity readable: **halve the loadout to 2 slots and force one melee + one ranged.** You pick a *lane*. Everyone can see what you are.

One engineer, one session. Nothing here needs new art — the saber already has an ignite/retract pose system, and `Projectiles` already stores `owner`, `team` and `vel` on every item.

---

## STUDIO DIRECTIVES

### Directive 1 — Delete the ghost, teach the server about weapons
**Files:** `src/modes/weapon.js` (remove), `src/shared/match.js`, `src/modes/match-mode.js`
- Delete `src/modes/weapon.js` entirely (confirm no live importers first; `raySphere`/`applySpread` move to `src/modes/weapons/util.js` only if something still needs them).
- Add a `WEAPON_LIMITS` table to `src/shared/match.js`: `{ leafblade: {maxRange: 5.0, minInterval: 0.55, maxDamage: 100}, petalbow: {maxRange: 90, minInterval: 0.95, maxDamage: 70}, ... }`.
- `_hit()` now reads `evt.w` (weapon id), rejects unknown ids, and validates range + damage + per-player last-hit interval against that table instead of one global `MAX_DAMAGE_RANGE`.
- All hit emitters in `match-mode.js` include `w: stats.id`.
**Acceptance:** no file in `src/` imports `weapon.js`; a spoofed `{t:'ev', e:{type:'hit', w:'leafblade', target, damage:100}}` from 40m away is silently dropped; normal 8-player match plays identically.

### Directive 2 — Stamina + Guard on the saber
**Files:** `src/modes/weapons/tools.js` (add `Stamina`), `src/modes/weapons/saber.js`, `src/modes/match-mode.js`
- `class Stamina { max=1, regen=0.28/s, regenDelay=0.6s after spend }`. Saber swing costs `0.30`; guarding drains `0.22/s`.
- `Saber`: add `guarding` bool, `guardT` (time since raise), `blockArc = 1.9rad`, `guardPose()` (blade vertical, centred, slight inward tilt), `breakGuard()` → `staggered = 1.0s` during which `startSwing()` returns false and blade ignition drops to 0.45.
- `match-mode.js`: RMB held while `activeWeapon.id === 'leafblade'` → guard instead of zoom. Draw a stamina bar under the charge bar, tinted red during stagger. Audio: reuse `saberHum` pitched up on guard, `saberHit` on a successful block.
**Acceptance:** holding RMB with the blade out visibly changes pose and drains a visible bar; running out triggers a 1s stagger where LMB does nothing; swinging with <0.30 stamina is refused; ranged tools are untouched (still zoom on RMB).

### Directive 3 — Reflect in the projectile layer
**Files:** `src/modes/weapons/projectiles.js`, `src/modes/match-mode.js`
- `Projectiles.update()` gains an optional per-target `guard` descriptor `{active, forward, arc, parry}`. Before the existing distance hit test, if the target is guarding and the incoming velocity is within `arc` of the guard forward: either **absorb** (`parry === false` → retire + `burst()` in white, no damage) or **reflect** (`parry === true` → `it.vel.negate()` blended 70/30 toward the original shooter, `it.owner`/`it.team` swapped to the blocker, `it.damage *= 1.25`, `it.life = max(it.life, 1.6)`).
- Lobbed projectiles with `gravity >= 6` (bubbler, confetti) bypass guard entirely when their velocity's `y` component at impact is negative — arcing shots land *over* the block.
- `match-mode.js` passes the local player's guard state in; reflected hits still route through the normal `_onProjectileHit` → hit-event path so the server sees the blocker as the shooter.
**Acceptance:** a `petalbow` shot into a freshly-raised guard visibly flies back and can soak the original shooter; a `bubbler` lob over a guard still connects; reflected kills are credited to the blocker on the scoreboard.

---

## PERSONAL CHALLENGE FOR MIKEL

You said **both** — good, that's the right call, and it's why the game needs a *shared verb* the two families answer differently. So here's the decision only you can make:

> **Should Guard be universal or melee-only?**
>
> If ranged tools also get a guard (a small deployable splat-shield, say), the game becomes more forgiving and more chess-like — everyone can turtle, matches get longer, positioning dominates. If Guard belongs *only* to the saber, then melee is genuinely a different class with a different skill ceiling, ranged players must solve it with movement and arcs, and the RPS is sharp — but the first week of playtests will have people screaming that blades are unfair.
>
> **Pick one and commit before the engineer touches Directive 2**, because it changes whether `Stamina` lives on the saber or on the player.
>
> And the smaller dare: **is a reflected shot funnier than a blocked one?** If yes, then reflect should be the *default* outcome of a guard and absorb the failure case — not the other way round. Say the word and I'll flip the directive.

---
*Director's note: I did not touch a line of `src/`. Engineer implements, human merges.*

---
---

# 🎬 THIRD PASS — the layer nobody has looked at yet

*Passes 1 and 2 covered the weapon economy (kill the carbine, stamina, guard/reflect, server authority). Nothing has changed in `src/` since — HEAD is still `0bd23bd`. So this pass deliberately goes somewhere else: **the body**. Not what you hold, but what other people can SEE you holding, and what your legs can do about it.*

## VISION

Class-based PvP is a **reading** game before it is a reflex game. In Nostale you know the fight the instant the other silhouette resolves. BlaKeks has beautiful weapons that literally nobody else in the match can see — and legs that can only walk, sprint or crouch. Until a remote player's blade glows across the field and until my legs can commit to a direction and *dodge*, "saber = movement + timing" and "projectiles = positioning + prediction" are slogans, not mechanics. Both weapon families need the same two things from outside the weapon files: **a readable third-person presence** and **a movement verb worth predicting.**

## WHAT I CHALLENGE

**5. Remote players are unarmed mannequins. `src/entities/remote.js` has no weapon at all.**
The whole file's visual state is `this.hp`, `this.label = makeLabel(name)` at `y = 2.25`, and a `_veil` fade (lines 38–43, 111). There is no held model, no hand attachment, no `weaponId` in the state the remote reconstructs. `src/entities/avatar.js` contains zero references to a hand prop — I grepped for `weapon|hold|hand|prop` and got one docstring comment about animation clips. So: the Verdant Blade's three nested glow shells, its `PointLight(SABER.color, 0, 9, 2)` and its ribbon trail (`saber.js:99–121`) exist **only in the local player's first-person view**. Eight friends in a match, and not one of them can tell whether the person running at them is holding a Leaf Blade or a Petal Bow. This is the single biggest hole in the "class identity" ambition from Pass 2 — you can halve the loadout to force a lane, and it still won't be readable, because there's nothing on the body to read.

**6. `src/entities/player.js` has no dodge, and therefore projectiles cannot actually be dodged.**
`SPEEDS = { walk: 5.4, sprint: 8.6, crouch: 2.7, swim: 3.1 }` (line 10) and that is the entire movement vocabulary. `this.sprinting` is just `ShiftLeft` held (line 161). `tools.js` sells the pivot as "you can see it coming and dodge" — but with an 8.6 m/s ceiling and no burst of lateral speed, a `petalbow` petal at `speed: 62` covers 20m in 0.32s. You cannot walk out of that. The dodge the design doc promises is not implemented anywhere. Meanwhile `src/shared/items.js` outsources the entire feeling of mobility to a *pickup* — `dash: { duration: 7, effect: { speedScale: 1.5 } }`. Movement excitement should be a button you own, not a crate you find.

**7. `src/shared/conditions.js` is doing the job that the match loop should be doing.**
Seven modifiers — Nightfall, Fog Bank, Low Gravity, Rush, One Life, Scarcity, Overgrown — and they're good, cheap variety. But they're *pre-round dressing*: rolled up front and joined with `·` in a label (line 117). Nothing happens **during** a round to create the arena moment. There is no shrinking play area beat, no mid-round objective, no "last 30 seconds" pressure. Smash has the ledge, Splatoon has the final-minute turf frenzy, Quake has the armour timer. BlaKeks has a timer that runs out. The variety is in the *setup*, not the *story*.

## THE ONE BIG IDEA — **Show the weapon, give them a Dodge Roll**

One session. Two changes. Both weapon families get first-class treatment from the movement/readability layer.

**A. Third-person weapon attachment.** Add `weaponId` to the per-player network state and mount the real model on the remote avatar's right hand:
- Ranged → `buildToolModel(id)` already returns a `group` (`tools.js:177`); it just needs a world-scale variant instead of the 0.4–0.5 view-model scale.
- Melee → instantiate a lightweight `Saber` in "world mode": full 1.55-unit blade, ignition driven by whether the remote is holding it, `PointLight` intensity halved for perf, trail enabled only while their swing flag is set.
- **This is the readability payoff:** a lit green blade at 40m says *back up*. A drawn Petal Bow says *break line of sight*. That single visual is what makes the Pass-2 RPS legible instead of theoretical.

**B. Dodge Roll (double-tap A/D/S, or `Ctrl`+direction).** A 0.35s burst to ~14 m/s lateral, with **0.12s of i-frames at the start** and a 0.45s recovery where you cannot dodge again.
- **For the projectile player:** this is the answer to a lunging saber. Positioning becomes a live skill instead of a starting position.
- **For the saber player:** the dodge *is* the approach tool. Roll through the petal, arrive in reach. Saber = movement + timing, finally literally true.
- Cost it from the **same stamina pool as the saber guard** (Pass 2, Directive 2) if Mikel answers "shared" below — that makes every roll a swing you didn't take, and it is the tightest version of this system.

Nothing here needs new art. `buildToolModel` and `Saber` already exist; `player.js` already has a velocity integrator and a `speedScale`.

## STUDIO DIRECTIVES

### Directive 1 — Weapon on the body (P0)
**Files:** `src/entities/remote.js`, `src/entities/avatar.js`, `src/modes/match-mode.js` (state emit), `src/net/client.js` if the state packet needs a field
- Add `w` (weapon id) and `sw` (swing/fire flag) to the per-player snapshot alongside the existing `hp`/`alive`.
- `remote.js`: create a `handAnchor` `Object3D` on the avatar's right arm; on `w` change, dispose the old model and mount `buildToolModel(w)` at world scale (~1.0) or a `Saber` with `wantIgnite: true` for `leafblade`.
- Respect `_veil`: a veiled player's weapon must fade with them (reuse the line 111 visibility gate).
**Acceptance:** in a 2-client `tools/mptest.mjs` run, client A swaps to the Leaf Blade and client B sees a lit green blade in A's hand within one snapshot; swapping to `petalbow` swaps the visible model; a veiled player shows no weapon; frame time in an 8-bot match does not regress more than 1ms.

### Directive 2 — Dodge Roll (P0)
**Files:** `src/entities/player.js`, `src/core/input.js`, `src/ui/ui.js`
- `input.js`: detect double-tap (<0.28s) on `KeyA`/`KeyD`/`KeyS`, and `ControlLeft`+direction as an accessibility alias.
- `player.js`: `dodge(dir)` → 0.35s at ~14 m/s along `dir`, `this.iframes = 0.12`, `this.dodgeCooldown = 0.45`, blocked while crouching/swimming/staggered. Expose `iframes` so the hit path can ignore damage.
- `ui.js`: a thin cooldown pip under the crosshair. No number.
**Acceptance:** double-tapping A visibly launches the player sideways ~4.5m; a `petalbow` shot timed into the first 0.12s deals no damage; you cannot chain-dodge (second input inside 0.45s is ignored); the roll works identically while holding any of the five tools.

### Directive 3 — The Last Thirty (P1)
**Files:** `src/shared/match.js`, `src/shared/regions.js`, `src/ui/ui.js`
- At `timeLeft <= 30` in a `tactical` round, emit a `finale` event: play area contracts toward a single region from `regions.js`, all charge regen ×1.4, and everyone outside the shrinking area takes 4 soak/sec.
- UI: the timer turns and pulses; a one-line callout — "THE LAST THIRTY".
**Acceptance:** rounds that would have ended in a stalemate now force contact; the contraction is server-authoritative and identical on all clients; a player who ignores it is bubbled within ~25s; the existing round-end and rematch flow is unchanged.

## PERSONAL CHALLENGE FOR MIKEL

Pass 2 asked you whether Guard is universal or melee-only. Here is the one this pass creates, and it is the more consequential of the two:

> **Does the Dodge Roll spend the same resource as the saber?**
>
> **Shared pool** (roll, swing and guard all drain one bar): every fight becomes a budget. A saber player who rolls in has less left to swing with; a ranged player who panic-rolls twice is defenceless. It is tense, it is legible, and it makes both families play the *same* mental game with different tools — which is the cleanest possible answer to your "BOTH" call.
>
> **Free roll on a flat cooldown**: the game is faster, friendlier, and eight tipsy friends will have more fun on night one — but the ceiling is lower and the roll stops being a decision.
>
> **My call: shared.** But I want you to say it out loud before the engineer starts Directive 2, because it decides whether `Stamina` lives on the saber or on `player.js`.
>
> And the dare: **let me see other people's weapons before you balance another number.** Every tuning argument this studio has had today has been about numbers nobody in the match can perceive. Readability first — then balance means something.

---
*Director's note, third pass: still zero lines of `src/` touched. Files read this pass: `src/entities/remote.js`, `src/entities/avatar.js`, `src/entities/player.js`, `src/shared/conditions.js`, `src/shared/items.js`, `src/shared/match.js`.*
