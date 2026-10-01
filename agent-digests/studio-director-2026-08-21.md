# 🎬 Studio Director Brief — 2026-08-21

> Read-only director pass. No source touched. Branch: `studio/director-2026-08-21`.
> Scope read: Little Planet `tactical` ("Splat Brawl") PvP — `experiences/little-planet/src/...`.
> Mandate carried from lead (2026-08-06): **BOTH melee sabers and ranged projectiles are first-class.** No forcing a choice.

---

## VISION

BlaKeks World's PvP should feel like a *readable real-time skirmish* — the clarity of
Nostale's class combat with the legibility of Splatoon's paint and the swing-weight of
Quake's melee. You should always be able to answer, in under a second, three questions:
**who is shooting me, what are they using, and can I dodge it?** The fantasy is a tiny
hand-made planet where up to 8 friends close in, trade readable blows, and the *last
readable moment* — not the last invisible one — decides the round. Right now the bones
are good (charge-based soak tools, a gorgeous Verdant Blade, a shrinking arena, bot
fill). But the two weapon families are not yet two *first-class citizens*: ranged has two
competing implementations and melee has no identity of its own.

---

## WHAT I CHALLENGE

1. **Bots fight with a weapon the player cannot have — and it breaks the project's own
   philosophy.** `botbrain.js:238-256` (`botShoot`) calls `traceShot` from `weapon.js`,
   an *instant hitscan* carbine (26 dmg, headshot ×1.5) that shows only a 0.07 s tracer.
   Meanwhile `tools.js:4-19` states the manifesto outright: *"No hitscan. Everything is a
   visible object that travels, so you can see it coming and dodge."* And
   `match-mode.js:489-491` even says being shot with no idea where from is *"the single
   most frustrating thing in a shooter."* The bots do exactly that. Vs-bot tactical is a
   different game from vs-friend tactical. **This is the #1 enemy of "both first-class":
   ranged exists twice and the bot version is unreadable.**

2. **The `ammo` pickup is a lie to the player.** `items.js:42-47` defines an `ammo` crate
   — *"Refill your magazine and reserve."* But the player's loadout is built on `Charge`
   (`match-mode.js:888-898`), never `Magazine`. Only `botbrain`/`weapon.js` touch a
   magazine, and bots don't pick up crates. `match-mode.js` never reads the `refill`
   effect for the player. So anyone who grabs an Ammo Crate gets *nothing*. A dead,
   confusing pickup sitting in the tactical item pool.

3. **The saber has no identity of its own — it reuses the ranged charge bar.** The
   leafblade is gated by a `Charge` (`tools.js:74-76`, `cost 0.5 / regen 0.42 / rate
   0.62`), the *exact same* 0..1 soak meter as the Bubble Wand, with a flat `recovery
   0.22 s` cooldown (`saber.js:187`). The lead's mandate — *"saber = movement + timing,
   projectiles = positioning + prediction"* — is unmet: there is timing (the swing
   window) but no **melee-specific resource** that makes the blade *feel* different from a
   slow projectile. Today the saber reads as "a big soak tool with a sword skin."

4. **Loadout is 2/3 ranged, 1/3 a single always-on blade.** `match-mode.js:881-885`
   deals `splatter` + a rolled secondary + `leafblade`. Melee is one fallback slot. For
   "both first-class" to be true, melee should be a *real choice with its own risk math*,
   not a panic button — see the One Big Idea.

---

## THE ONE BIG IDEA

**One Combat World, Two Resources.**

Stop running two ranged models. Make the bots use the *same dodgeable soak-projectile
model the player uses* (route bot shots through `Projectiles` + the existing `onHit` →
`request('hit')` path), so PvP vs bots and vs friends are the same game. Then give the
**saber its own resource — Stamina** — a pool shared with sprint/dash: swings cost
stamina, closing distance costs stamina, a swing attempted while winded whiffs with a
long recovery. That makes "saber = movement + timing" *literally true* and mechanically
distinct from the ranged soak-charge, honoring the BOTH decision in one stroke. Finally,
repurpose the dead `ammo` crate into a **Surge** that refills *both* the soak-charge and
saber stamina, so pickups serve both families. Result: ranged = positioning/prediction
(safe, gradual), melee = movement/timing (risky, burst) — a clean rock-paper-scissors of
*resources*, not just damage numbers.

---

## STUDIO DIRECTIVES (ordered, engineer-implementable this week)

### 1. Kill the ghost carbine — unify bot combat into the soak model
- **File:** `experiences/little-planet/src/modes/botbrain.js` (`botShoot`, lines 238-256).
- **Change:** Replace the `traceShot`/`WEAPON` hitscan path with the existing
  `Projectiles` soak model. Pick a `TOOLS` entry (e.g. `splatter`/`bubbler` by bot
  personality), spawn a traveling blob toward the target using `applySpread` for the bot's
  accuracy, and let `Projectiles.update` + the mode's `onHit` deliver the hit through the
  same `request({ type:'hit', ... })` the player uses. Preserve `bot.accuracy` /
  `bot.reaction` knobs (`botbrain.js:294-295`) so difficulty stays intact. Remove the
  now-orphaned `WEAPON`/`Magazine`/`buildViewModel` from `weapon.js` if nothing else
  imports them.
- **Acceptance:** (a) A bot's shot is a *visible traveling object* the player can dodge;
  (b) a connect produces a `Projectiles.burst` splat, not a silent hp drop; (c) no code
  path calls `traceShot` or `WEAPON` anymore; (d) bot win-rate vs a standing player is
  unchanged within ±10%.

### 2. Give the saber a distinct Stamina resource (movement + timing, for real)
- **File:** `experiences/little-planet/src/modes/weapons/saber.js` + `match-mode.js`
  (`_tacticalLocal`, lines 961-989) + a small HUD addition.
- **Change:** Add a `Stamina` model (pool 100; swing cost ≈ 34; sprint/dash drain ≈
  22/s while moving; regen ≈ 30/s when not swinging/sprinting). Gate `Saber.startSwing()`
  on stamina ≥ cost; on insufficient stamina, enter a `winded` state (recovery ×2.5 +
  blade-flicker/audio cue) instead of swinging. Wire `player` sprint/dash to also draw
  from this pool. Show stamina as a **separate** bar from the soak-charge.
- **Acceptance:** (a) The blade cannot swing when stamina < cost even if the soak-charge
  is full (proves it's a *distinct* resource); (b) a dedicated stamina HUD element exists
  and is visibly drained by sprinting; (c) a winded swing is telegraphed and non-lethal.

### 3. Fix the dead pickup — make items serve BOTH families
- **File:** `experiences/little-planet/src/shared/items.js` (`ammo`, lines 42-47) +
  `match-mode.js` (consume `refill`/new effect for the player, currently unread).
- **Change:** Repurpose `ammo` → `surge`: *"Refill your soak-charge and stamina."*
  Implement the effect in `match-mode.js` to set every `Charge.value = 1` and top up
  saber stamina to full on pickup. Update the `blurb`/`icon` to match. Delete all
  `ammo`/`magazine` references.
- **Acceptance:** (a) Picking up the crate visibly fills the active soak-charge to 1 and
  the saber stamina to full; (b) the item's `blurb` describes what actually happens; (c)
  zero remaining `ammo` references in the repo.

---

## PERSONAL CHALLENGE FOR MIKEL

The lead's own open question — **stamina or heat?** My recommendation is **Stamina
(shared with sprint/dash)**: it makes the saber the "movement + timing" weapon the BOTH
mandate promises, and it creates the cleanest RPS with ranged (ranged = safe
positioning/prediction; melee = must spend *movement* stamina to close, high
risk/reward). But it's your call. **Decide: saber resource = stamina (shared with
movement) or heat (chaining swings overheats and forces recovery)?** Pick one and the
engineer builds the HUD + feel around it this week. No more punting it.
