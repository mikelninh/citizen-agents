# 🎬 Studio Director Brief — 2026-08-14

> Mode under review: **`experiences/little-planet/` — Tactical ("Splat Brawl")**
> Lead decision honored: **BOTH** — melee sabers AND ranged projectiles, first-class from the start.
> Read-only director. No `src/`/`server/` was modified. This is a brief, not a patch.

---

## VISION

BlaKeks World's PvP should feel like a Nostale-style class brawl squeezed into a hand-made
planet: eight friends, one readable arena, and a fight where *who* you are and *what* you
brought matters more than who clicked first. The fantasy is **class-based real-time combat with
arena moments** — a saber duelist who wins by closing distance and timing the swing, a marksman
who wins by holding space and predicting your dodge, and the whole thing readable at a glance
because every hit, every soak tick and every down is legible to the people *watching*, not just
the people fighting. Right now we have two weapon families in the Tactical mode, but they don't
yet fight by the same rules — and a PvP fantasy you can't read is a PvP fantasy you won't return
to.

---

## WHAT I CHALLENGE

**1. The saber is a one-tap kill and the HUD is lying about it.**
In `match-mode.js` the melee path submits `this._request({ type:'hit', target, damage: stats.soak })`
(line 982) using the **leafblade** stat `soak: 100` (`weapons/tools.js` line 75). So one clean
saber swing deletes a full-HP enemy. Meanwhile the saber's own `SABER.damage = 68` constant
(`weapons/saber.js` line 24) is **dead** — never read. Ranged tools submit the same `stats.soak`
as HP (splatter 9, bubbler 26, petalbow 52), so a splatter user needs *eleven* hits to do what
the blade does in one. That is not "both first-class," that is "melee is the only class." The HUD
even admits the lie in `hud()` (lines 1206–1208): *"Displayed as SOAK … Internally it is still
hp counting down."* Ship either the soak fantasy or a real HP bar — not a HP bar wearing a soak
costume.

**2. Bots fight with a weapon the players will never touch.**
`tacticalBrain` → `botShoot` (`botbrain.js` lines 238–256) fires the **hitscan carbine**
`WEAPON` from `weapon.js` (26 dmg, headshot ×1.5, `traceShot`). No player ever uses that gun —
players use soak projectiles + the saber. So the AI is a *third, invisible archetype*, and you
can never practice against your own kit. Honoring "BOTH first-class" means the AI must exercise
the actual player weapons, or the balance pass is measuring the wrong fight.

**3. No rock-paper-scissors, no shared resource — the lead's own brief is unmet.**
The BOTH decision explicitly asked us to consider *"ammo/heat vs stamina"* and *"rock-paper-
scissors balance."* None of that exists. Ranged `Charge` regen is generous (splatter cost 0.055 /
regen 0.34 ≈ 6 shots/s; petalbow cost 0.34 / regen 0.24). The saber's only limit is its 0.64s
swing cycle and a 0.5 charge that refills in ~1.2s — no stamina, **no movement commitment, no
whiff punish, no prediction reward**. Mechanically today: melee = "walk to 3.4m, click, kill";
ranged = "lob slow blobs, hope." Neither expresses the movement+timing vs positioning+prediction
split the lead wanted.

**4. We are building PvP twice, in two different combat codes.**
The README names `duel/` Battle Arena (8 Worldforms, `src/game/spatial-duel.js`) the *"current
PvP focus,"* yet the only place that actually has **both** melee and ranged first-class is
`experiences/little-planet/`. Two combat codebases, two trust models, two fairness passes. The
lead's BOTH decision is being honored in the *less-finished* of the two, while the polished one
ships a different model. Pick one PvP surface to be the canonical "BOTH" home before we balance
either.

---

## THE ONE BIG IDEA

**Make Soak real, and gate BOTH weapons on one shared Stamina — so melee = timing/commitment and
ranged = prediction/positioning, with neither able to one-shot.**

Concretely, in one engineer session:

- **Soak becomes the single win condition for everyone.** In `shared/match.js` `_hit`, stop
  subtracting HP and start *accumulating soak*; at 100 emit `down` and use the already-built
  `makeBubble()` (`weapons/projectiles.js` line 185) for the bubble-out. Both saber and
  projectiles feed the *same* bar. This deletes the HP-vs-soak double bookkeeping and makes the
  HUD honest.
- **The saber gets a melee identity.** Add a `Stamina` resource; a swing is a *commitment*:
  briefly root the player (~0.15s) + a punishable ~0.22s recovery, per-hit soak ≈ 34 (three
  clean hits to down), and lower `leafblade.soak` from 100 → 34. Reward timing: a "perfect"
  early-swing window (the 0.25–0.45 band of `Saber.hits`) does bonus soak. Whiffing leaves you
  visibly open.
- **Projectiles get the prediction identity.** They apply soak at range and — unlike the saber —
  can be thrown *past* a dodge-read; precise tools (petalbow-style) reward leading a moving
  target. No single shot downs anyone.
- **Rock-paper-scissors falls out for free:** saber beats a ranged player who is reloading / out
  of position at close range; ranged beats saber by holding distance and predicting the lunge.
  Neither deletes the other from full in one action. Bot `botShoot` (challenge #2) is rewritten
  to use the real soak tools in the same pass, so the AI trains against the kit you ship.

This is the highest-leverage week of PvP fun available: it fixes the lie, the imbalance, and the
AI all at once, and it's the literal embodiment of the lead's BOTH call.

---

## STUDIO DIRECTIVES (ordered, for the engineer agent)

**D1 — `experiences/little-planet/src/shared/match.js` (`_hit`, lines 242–263).**
Convert HP-subtract to soak-accumulate. Track `soak` per player; at `soak >= 100` emit `down`
(bubble-out) and set `alive=false`. Keep the existing team/distance validation.
*Acceptance:* 100 combined soak = exactly one down; the HUD soak bar (0→100) maps cleanly to the
old `100−hp`; no code path subtracts raw HP anymore.

**D2 — `experiences/little-planet/src/modes/weapons/saber.js` + `match-mode.js` (`_tacticalLocal`,
lines 967–989) + `weapons/tools.js` (leafblade).**
Add a shared `Stamina` on the player/bot; make the saber a commitment (root + recovery), set
`leafblade.soak = 34`, add a perfect-timing bonus, and block a swing when stamina is empty.
*Acceptance:* a full-HP enemy needs ≥3 clean saber hits to go down; swinging with no stamina
fails loudly; a whiffed swing shows a recoverable opening the opponent can punish.

**D3 — `experiences/little-planet/src/modes/botbrain.js` (`botShoot`, lines 238–256).**
Replace the legacy hitscan `WEAPON` carbine with the same soak tools / saber the player uses
(pull from `tools.js` stats + `Charge`), and remove the `weapon.js` carbine import from the bot
path.
*Acceptance:* in a 1v1 bot match the bot's damage values equal the player's tool soak numbers;
the `WEAPON`/`traceShot` carbine is no longer referenced by the tactical AI.

---

## PERSONAL CHALLENGE FOR MIKEL

**Soak, or HP?** You've shipped a soak bar that is secretly HP — and a saber that one-shots under
the HP model. Decide the win condition *once*: is BlaKeks PvP a **Splatoon-style "fill the soak,
bubble them out"** game (keep `makeBubble`, friendly, endlessly replayable with friends, no one
feels "killed"), or a **HP deathmatch** (drop the soak skin, show real numbers, lean into
lethal duels)? The saber's entire tuning — and D1/D2 above — only makes sense after you pick.
You pick the fantasy; I'll build the combat around it.
