# 🎬 Studio Director — Direction Brief (2026-08-30)

> Role: co-creative director of BlaKeks World (Vite + Three.js, tiny hand-made
> planet, explore / hide / fight with up to 8 friends). Read-only director:
> this brief names files and mechanics; the engineer implements.
> Lead decision honored: **BOTH melee sabers and ranged projectiles are
> first-class from the start.**

## VISION

BlaKeks World should feel like a **Nostale-style class brawl on a toy planet**:
readable, real-time PvP where you always know who's winning, who's about to pop,
and what your one weapon is for. The fantasy is *combat you can read at a glance*
— a glowing saber arc, a fat slow bubble sailing at your face — not a stats
screen. Win by out-positioning and out-timing, never by out-DPSing a spreadsheet.
Up to 8 friends, one tiny curved island, every fight legible from across the map.

## WHAT I CHALLENGE

1. **The "SOAK" fantasy is painted on top of raw HP — it isn't real.**
   `src/modes/weapons/tools.js` (L6–19) and `src/modes/weapons/projectiles.js`
   (L184, `makeBubble`) sell "fill their soak meter, they pop into a floating
   bubble." But `src/shared/match.js` `_hit` (L249–251) just does
   `target.hp -= dmg`, and `src/modes/match-mode.js` L1206–1209 admits it:
   `const soak = 100 - this.hp;` — the soak bar is literally inverse health, and
   `makeBubble()` is imported (L13) but **never called**. The signature moment
   the whole pivot was built around does not exist in the authority. That is the
   product lying about itself, not a polish gap.

2. **Two damage models that don't speak the same language.** Human loadout hits
   = soak values sent as `damage` (splatter 9, bubbler 26, petalbow 52, leafblade
   100 → `match-mode.js` L982 / L1042). Bots hit = carbine `WEAPON.damage = 26`
   with a **1.5× headshot** (`src/modes/botbrain.js` L254) via hitscan
   `traceShot`. So bots get perfect tracking + crits; humans get no crit and must
   lead slow arcs. Per-shot, a bot out-damages a human sprayer and the two halves
   of "combat" are balanced against nothing. The lead said BOTH first-class —
   right now "ranged projectiles" humans use are the toy soak set while the *only*
   hitscan in the game belongs to bots.

3. **`weapon.js` is half-dead and the README still claims it's the game.**
   Only `applySpread` is imported by `match-mode.js`; `Magazine`, `buildViewModel`,
   `traceShot`, `WEAPON` exist solely for bots (`botbrain.js` L3). README L52
   advertises "Tactical FPS ✅ hitscan gunplay, bot squads" — but humans never
   fire the carbine. Either promote it to a first-class human weapon (honoring
   BOTH: saber / soak-tool / carbine) or retire it. As-is it is contradictory
   dead weight that contradicts the combat you're actually shipping.

4. **Melee and ranged share one resource clock, so neither has identity.** The
   lead asked to consider "ammo/heat vs stamina" and "saber = movement+timing,
   projectiles = positioning+prediction." Today both families drain the same
   `Charge` meter (`tools.js` L99–120). The leafblade just reuses `Charge`
   (cost 0.5 / regen 0.42, `tools.js` L75) — there is no stamina, no heat, no
   movement cost. Saber = "click on a cooldown," resource-wise indistinguishable
   from a gun. The swing *timing* exists (`saber.js` L250, 0.25–0.7 window) but
   nothing makes you *commit your body* to it.

## THE ONE BIG IDEA

**Make "Composure" the real, single health-shaped meter both weapon families feed
— and let it actually BUBBLE you out when it breaks.**

One authoritative `composure` field per player in `match.js` (replacing the
cosmetic `100 - hp`). Projectile hits add visible, decaying soak; the saber adds
a big chunk + a brief stagger; bots' carbine adds the same way. At 100 you emit a
`bubbled` event, float away in `makeBubble()` (which already exists, unused), and
respawn / lose the round.

Why this week:
- (a) it finally wires the sold fantasy into the authority — the game stops
  lying about itself;
- (b) it's the *only* change that lets the lead's BOTH decision live in one
  coherent rule layer instead of two drifting halves;
- (c) it's one session — add `composure` to the player, swap `_hit` to add
  (capped 100), emit `bubbled`, and call `makeBubble()` on the client.
  Everything else (saber stamina, bot parity) hangs off this.

## STUDIO DIRECTIVES (ordered, for the engineer)

1. **Unify the health layer into Composure.**
   Files: `src/shared/match.js` (`_hit`, L246–251) + `src/modes/match-mode.js`
   HUD (L1206–1209) + `src/modes/weapons/projectiles.js` (`makeBubble`, L184).
   Replace `hp` subtraction with a `composure` meter that fills 0→100 from any
   `hit` (saber, tool, or bot). At 100 emit `{type:'bubbled', id}` and on the
   client spawn `makeBubble()` and float the avatar out.
   *Acceptance:* a saber swing and a petalbow shot move the *same* bar; reaching
   100 eliminates you in a visible bubble; the `100 - hp` cosmetic is gone.

2. **Give the saber its own Stamina so melee = movement + timing.**
   Files: `src/modes/weapons/saber.js` (SABER config L19–31) +
   `src/modes/weapons/tools.js` (`Charge`, L99–120) +
   `src/modes/match-mode.js` (L967–989). Add a `stamina` resource to the saber:
   a new **lunge** (gap-close dash on a swing) costs stamina; stamina regenerates
   when not swinging; at 0 you cannot swing and recovery is longer. Remove
   leafblade's dependence on the generic `Charge`.
   *Acceptance:* saber has a distinct visible stamina bar; a lunge visibly closes
   distance and costs resource; whiffing at 0 stamina punishes you; ranged tools
   still use `Charge` so the two families feel different to manage.

3. **Reconcile bot combat with the human loadout (kill the twin damage model).**
   Files: `src/modes/botbrain.js` (L238–256) + `src/modes/weapon.js`.
   Make bots fire the *same* soak tools as humans (or formally promote the
   carbine to a 3rd first-class human weapon with its own ammo resource). Remove
   the silent 1.5× headshot and the hitscan-vs-projectile mismatch.
   *Acceptance:* in a scripted 1v1, a bot's time-to-eliminate is within ±20% of
   an average human loadout; no `hp`/`composure` event originates from a model
   humans can't use.

## PERSONAL CHALLENGE FOR MIKEL

Saber combat needs a resource — **stamina or heat?** And is a bubble elimination
**non-lethal (respawn with a penalty / score cost) or lethal (round lost)?**
You have to decide, because it changes whether `composure` is a health bar or a
scoreboard, and whether the saber's lunge is a comeback tool or a suicide play.
I'll build whatever you pick — but the engineer can't pick this for you.

---
*Files read this run: README.md, src/modes/weapon.js, src/modes/match-mode.js,
src/modes/mode.js, src/modes/botbrain.js, src/modes/weapons/saber.js,
src/modes/weapons/projectiles.js, src/modes/weapons/tools.js, src/shared/items.js,
src/shared/match.js, server/room.js.*
