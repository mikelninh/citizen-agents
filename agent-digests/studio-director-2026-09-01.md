# 🎬 Studio Director Brief — 2026-09-01

Repo: `citizen-agents` (published digest) · Source brief: `mikelninh/blakeks-world` · Branch: `studio/director-2026-09-01`

---

## VISION

BlaKeks World's PvP should feel like **Nostale's class combat meets Smash's read-it-clearly spectacle**, on a tiny hand-made planet you can lose sight of a friend behind a tree and then catch them turning a corner. The fantasy is: **pick a weapon family, read the fight, make a moment**. A saber duel at the ruins' edge should feel like timing and footwork — every swing has a commitment, every parry a window. A splat-brawl across the meadow should feel like positioning and prediction — watching the bubble drift toward you and deciding now or later. Both families must live in the same match, on the same health pool, with the same stakes, so choosing a weapon is a real choice and not a mode switch. The laugh-making bubble-pop resolution is great for the "splat" identity — but it must not sit parallel to a lethal HP system that the saber and carbine use. One fight, one resolution, two weapon families that play differently.

---

## WHAT I CHALLENGE

### 1. The README's status table lies about what combat exists.

`README.md` line 48-54 lists these PvP rows:

- Hide & Seek ✅
- **Tactical FPS ✅ — "Team rounds, hitscan gunplay, bot squads"**
- Explore ✅

There is **no row for the splat-brawl/projectile system and no row for the saber**. Yet `match-mode.js` imports all three weapon families: `weapon.js` (carbine, hitscan), `weapons/tools.js` (5 projectile tools with charge), `weapons/saber.js` (melee). `instructions` at line 75-78 wiring `"1 / 2 / 3"` tool swap confirms the projectile tools are live in match mode. The README tells a new player the game is a hitscan FPS and hides the two weapon systems the lead just decided are "both first-class." If BOTH is the decision, the README must say so — otherwise the engineer implementing BOTH is building inside a story the docs don't support.

Files: `README.md`, `src/modes/match-mode.js` (imports + `instructions`), `src/modes/weapons/tools.js`, `src/modes/weapons/saber.js`, `src/modes/weapon.js`.

### 2. BOTH is structurally present but mechanically isolated — three weapon systems, one health pool, no relationship between them.

`match.js` `_hit()` (line 242-263) is a single damage path: any weapon sends `evt.damage`, the server subtracts it from `target.hp`, a player at 0 is "down." That's good shared infrastructure. But look at what each weapon *means*:

- **Carbine** (`weapon.js`): hitscan, 26 base damage, 460 RPM, magazine + reload, headshot multiplier 2.1. Lethal HP damage.
- **Projectile tools** (`tools.js`): **no damage field at all.** Every tool has `soak`, `cost`, `regen`, `slow`, `burst` — but no HP damage. The entire docstring (line 7-19) commits: "nobody shoots anybody. You SOAK them … Fill someone's soak meter and they pop into a bubble." This is a **non-lethal parallel resolution** to the HP system.
- **Saber** (`saber.js`): `damage: 68`, `swingTime: 0.42`, `recovery: 0.22`, `reach: 3.4`. Lethal HP damage, but **no resource**. It has a cooldown (recovery), but no stamina, no heat, no cost to swing. The only constraint is the swing animation timing.

The fracture: **two weapon systems hit HP (carbine, saber), one fills a soak meter that is not defined in `match.js` at all** (tools). I read `match.js` fully — there is no soak field on players, no soak resolution, no bubble-on-soak logic in the shared match rules. The soak mechanic must live in `match-mode.js` only, which breaks the "same code in both places" discipline the codebase otherwise honors (`MatchSim` runs offline and online as identical code). If soak is real, it belongs in `match.js`.

And within the lethal lane, **saber and carbine are unbalanced by construction**: saber does 68 damage with zero ammo/charge/stamina cost and a 0.22s recovery; carbine does 26 per shot but costs ammo and has reload. At close range, a saber user can swing every 0.64s (0.42 swing + 0.22 recovery) = ~106 damage/s with no resource gate. A carbine user at the same range needs ammo, faces spread, and reloads. The saber doesn't just feel different — it's strictly stronger at melee range with no tradeoff. BOTH only works if both families have a resource the other can pressure.

Files: `src/shared/match.js` (no soak field), `src/modes/weapons/tools.js` (soak only, no damage), `src/modes/weapons/saber.js` (damage, no resource), `src/modes/weapon.js` (ammo + damage), `src/modes/match-mode.js` (where soak would have to be implemented client-side if anywhere).

### 3. The saber has no reason to exist in a "both" design — it's a cooldown-locked melee damage dealer with no identity.

`SABER` constant (line 19-31): damage 68, swingTime 0.42, recovery 0.22, reach 3.4, arc 1.5 rad. That's it. No resource, no parry, no stance, no risk. Compare the thoughtful design commit in `tools.js` (line 7-19): "No ammunition. Every tool recharges on its own … No hitscan. Everything is a visible object that travels, so you can see it coming and dodge." The projectile tools have a *philosophy*. The saber has a stats block and a pretty blade with a trail.

The saber's identity in the code is "a green glowing stick that does 68 damage if you time the swing." There's nothing about **movement commitment** (the lead's directive: "saber = movement + timing"). The swing is a 0.42s cone check — but there's no cost to *trying* a swing and whiffing except the recovery window. There's no footwork reward, no lunge, no stamina-drain-on-miss. Until the saber has a resource that makes whiffing hurt, and a movement mechanic that makes positioning matter (a lunge that commits you, a parry window, a step that trades distance for reach), it's a second carbine with a swing animation — not a first-class melee family.

Files: `src/modes/weapons/saber.js` (SABER constant + hits() cone check only).

### 4. The soak→bubble resolution is hilarious and should be kept — but it currently has no home in the shared rules and no interaction with the lethal lane.

`tools.js` line 7-12 commits hard: "Fill someone's soak meter and they pop into a bubble and float away, which is funny to watch and takes the sting out of losing." `projectiles.js` `makeBubble()` (line 185) builds the bubble visual. But `match.js` has no soak field, no "bubble when soaked" rule, no soak depletion on dodge/move. If the soak system is implemented only in `match-mode.js`, then offline and online could diverge on soak behavior — the exact bug the shared `MatchSim` architecture exists to prevent. And critically: if a player is being soaked by a petalbow and shot at by a saber at the same time, what wins? HP or soak? The current code has no answer because the two lanes never meet.

The strong move: keep the bubble as the **non-lethal terminal state** for the projectile family (it's charming and on-brand), but make HP the **lethal terminal state** for the saber/carbine family, and let the two interact cleanly — e.g., getting bubbled removes you from the lethal fight for a few seconds (you're floating, harmless, helpless), which is a real tactical stake for the saber user and a real risk for the petalbow user who bubbles someone right as a saber user moves in. That makes both families matter in the same fight. But it needs a shared rule, in `match.js`.

Files: `src/shared/match.js` (missing), `src/modes/weapons/tools.js` (soak semantics), `src/modes/weapons/projectiles.js` (bubble visual), `src/modes/match-mode.js` (would need soak step if not in match.js).

---

## THE ONE BIG IDEA

**Make the saber a resource weapon and wire both families into one shared resolution track in `match.js` — in one session.**

Concretely:

1. **Give the saber a stamina bar** (analogous to the `Charge` class already in `tools.js`). Each swing costs stamina; stamina regens when not swinging. Whiffing a swing still costs it. This makes the saber's "movement + timing" identity real — you can't spam swings, you have to time them and recover. A saber fight becomes about footwork and commitment, not click speed. Stats: maybe 100 stamina, swing cost ~35, regen ~0.35/s (so roughly 2-3 swings before a pause — comparable to a tool's 3-4 shots per charge). The `Saber.startSwing()` already checks `this.cooldown > 0` — add `!player.staminaReady()` there.

2. **Land the soak rule in `match.js`** (not just in `match-mode.js`). Add a `soak` field to players in `MatchSim`, a soak depletion on movement/dodge, and a "soaked → bubble" terminal rule. At the same time, keep HP as the lethal terminal rule for saber/carbine. Add one interaction rule: **a bubbled player is "out of the fight" for N seconds** (floating, can't act, can't be hit again — one terminal state at a time). This gives the projectile family a meaningful win condition that the saber family can exploit (bubble someone, saber the bubble) and gives the saber family a reason to care about the projectile family (don't let them bubble you before you close).

3. **Update the README status table** to list "Splat Brawl (projectiles)" and "Melee Saber" as distinct rows alongside "Tactical FPS" — because BOTH is the decision, the docs must say so.

This is one engineer session: add stamina to the saber swing path, add soak to `MatchSim`, add the bubble-out rule and the "one terminal state at a time" interaction, update README. It makes melee and ranged both first-class with real tradeoffs and a shared fight — the BOTH decision actually means something.

Files: `src/shared/match.js` (soak field + bubble rule + terminal interaction), `src/modes/weapons/saber.js` (stamina cost in startSwing + swing cost), `src/modes/match-mode.js` (stamina meter on player, step it, wire to saber), `README.md` (status table).

---

## STUDIO DIRECTIVES

### Directive 1 — Saber gets a stamina resource (melee identity).

**File:** `src/modes/weapons/saber.js` + `src/modes/match-mode.js` (player stamina meter).

**Change:**
- Add a `stamina` concept to the player in match-mode (meter 0-100, regen when not swinging, drain on swing). Mirror the existing `Charge` pattern from `tools.js` — same shape, different resource.
- In `Saber.startSwing()` (line 149): add a stamina gate. A swing only starts if the player has enough stamina; the swing costs stamina on initiation (or on contact — pick one, document it). Whiffing still costs the stamina (so positioning matters — you can't safely spam).
- Tune: 100 stamina, swing cost 35, regen 0.35/s → ~2.8 swings per full bar, pause ~2.5s to full regen. Comparable to the petalbow's 2-3 shots per charge. This makes the saber a rhythm weapon, not a click weapon.

**Acceptance criteria:**
- Saber cannot swing when stamina is below the cost. A swing visibly drains stamina (UX: stamina bar on the HUD or a saber glow dim that tracks stamina).
- Whiffing a swing still drains stamina (otherwise there's no cost to mistiming).
- Stamina regens while not swinging; regen rate tuned so a saber duel feels like trading swings with pauses, not a DPS race.
- The saber still has its cooldown/recovery after a swing (don't remove the animation lock — stamina + recovery together make the commitment real).

### Directive 2 — Land the soak→bubble rule in `match.js` (shared rules, not client-only).

**File:** `src/shared/match.js`.

**Change:**
- Add `soak: 0` to player state in `addPlayer` (line 75-88).
- Add soak depletion: movement (speed > threshold) drains soak at a rate; standing still / crouching lets it build or hold. This is the "exposure" logic's sibling — moving makes you harder to soak, still makes you vulnerable. Wire it into `step()`.
- Add a soak cap and a **"soaked → bubble"** terminal rule: when a player's soak reaches the cap, they are `bubbled = true`, removed from active combat for a fixed duration (e.g., 5s), then pop back in with soak 0. Add `bubbled` field to the snapshot.
- **One terminal state at a time**: if a player is bubbled, they can't also be "down" from HP — whichever happens first wins, the other is suppressed until they return. Document this. This is the interaction that makes both weapon families matter in the same fight.

**Acceptance criteria:**
- `MatchSim` (offline) and the server's `MatchSim` (online) both run the same soak logic — verify by reading the code, not by testing only one path.
- Soak drains on movement, holds/builds on stillness — tune rates so a player who knows they're being petalbowed can dodge by moving (a real gameplay choice).
- Bubbled player is removed from the lethal fight for the bubble duration (can't be hit, can't act); on return, soak = 0 and they rejoin.
- A player who is bubbled while at low HP does NOT also go "down" — the bubble is their terminal state; they return later and live. This is the key interaction.
- `down` (HP 0) is still the lethal terminal for the saber/carbine lane and works as before.

### Directive 3 — README status table reflects "both" and the combat identity.

**File:** `README.md`.

**Change:**
- Replace or supplement the "Tactical FPS ✅" row with a clear inventory of the three combat systems actually in the code: **Tactical FPS (hitscan carbine)**, **Splat Brawl (projectile tools, soak→bubble)**, **Melee Saber (energy sword, stamina-gated swings)**. Each with a one-line "what it feels like" note.
- Add a one-line note under "The modes" or a new "Combat" section explaining that both weapon families are first-class in match mode and how they interact (lethal HP for saber/carbine, bubble for projectiles, one terminal state at a time).

**Acceptance criteria:**
- A new player reading the README sees that melee saber AND ranged projectiles are both real, first-class combat systems — not a hidden detail.
- The README no longer says the PvP game is "hitscan gunplay" as if that's the only combat.

---

## PERSONAL CHALLENGE FOR MIKEL

**Saber combat needs a resource — stamina or heat? And does the saber parry or not?**

Here's the fork only you can make, because it defines the whole melee fantasy:

- **Stamina** (my recommendation for BOTH): swinging drains a bar that regens on rest. Melee becomes about pacing and footwork — you swing, you recover, you reposition. A saber duel reads as "I have 2 swings, then I need a second — do you?" This sits cleanly alongside the projectile charge bars and gives both families a visible resource the other can pressure (a saber user low on stamina is vulnerable to a closing petalbow; a projectile user low on charge is vulnerable to a saber closing). Clean symmetry.

- **Heat**: the saber overheats if you swing too fast and must vent (stop attacking, glow fades). This is more aggressive and action-movie — "I'm pressing this hard my sword is melting." It's higher-arousal, closer to a Smash/Quake feel. But heat is harder to read on a HUD and the "vent" pause is self-inflicted, which can feel bad if you mis-time it.

The deeper question: **does the saber parry?** A parry — a timed block that deflects an incoming projectile or trades a melee hit for a counter-window — would make the saber genuinely distinct from the carbine and give melee players a reason to engage ranged players (parry their bubble/projectile, close in). But a parry is a second timing skill on top of stamina management and swing timing, and it's a lot to build and tune in one session.

My challenge: **pick stamina over heat, and commit to the saber being a pacing/footwork weapon, not a damage-spike weapon.** Drop the parry for now (it's scope). Then the saber's identity is clear: you have 2-3 swings, you commit to each one, you recover and move. That's a melee fantasy. The projectile user's identity is: I'm loading up 2-3 shots, I'm predicting where you'll be, I'm watching the arc. Both read clearly, both have a resource, both coexist. You can add parry later as a v1 enrichment once the stamina saber feels good.

Files this touches (for your decision): `src/modes/weapons/saber.js` (the `SABER` constant and `startSwing` are where stamina or heat lives), `src/modes/weapon.js` (the carbine's ammo pattern is the closest existing resource to mirror), `src/modes/weapons/tools.js` (the `Charge` class is the resource pattern to copy).

---

*Director's note: I read `match-mode.js` fully (1275 lines, both halves), `match.js` fully (356 lines), `saber.js` fully, `tools.js` fully, `projectiles.js` fully, `weapon.js` fully, `engine.js`, `avatar.js`, `room.js`, and the README. The soak→bubble system is charming and on-brand; the fracture is that it has no shared rule and the saber has no resource. Fix those two things and BOTH stops being three parallel systems and becomes one fight with two families.*
