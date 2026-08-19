# 🎬 Studio Director Brief — 2026-08-19

> Mode under review: **`experiences/little-planet/` — Tactical ("Splat Brawl")**
> Lead decision honored: **BOTH** — melee sabers AND ranged projectiles, first-class from the start.
> Read-only director. No `src/`/`server/` was modified. This is a brief, not a patch.
> Builds on the 2026-08-14 brief. I re-read the combat code; **all four challenges from that brief are still true**, because **none of its D1–D3 directives landed** — the tactical combat files have had *zero* commits since 08-14.

---

## VISION

BlaKeks World's PvP should feel like a Nostale-style class brawl squeezed onto a hand-made planet: up to eight friends, one readable arena, and a fight where *who* you are and *what* you brought matters more than who clicked first. The fantasy is **class-based real-time combat with arena moments** — a saber duelist who wins by closing distance and timing the swing, a marksman who wins by holding space and predicting your dodge, and the whole thing **legible to the people watching**, not just the people fighting. Right now we technically have both weapon families in Tactical, but because the AI fights with a different weapon than the player and the saber deletes anyone in one swing, the fight is neither readable nor fair — and a PvP fantasy you can't read is a PvP fantasy you won't return to.

---

## WHAT I CHALLENGE

> Proof of "still true": `git log --since=2026-08-14` on `match-mode.js`, `tools.js`, `saber.js`, `botbrain.js`, `weapon.js`, `shared/match.js` returns **no commits**. The tactical combat is frozen; the studio's post-08-14 energy went entirely into `duel/` Battle Arena.

**1. The saber is STILL a one-tap kill, and the HUD is still lying about it.**
`match-mode.js:982` submits `this._request({ type:'hit', target, damage: stats.soak })` using the **leafblade** stat `soak: 100` (`weapons/tools.js:75`). One clean swing deletes a full-HP enemy. The saber's own `SABER.damage = 68` (`weapons/saber.js:24`) is **still dead code — never read**. Ranged tools submit the same `stats.soak` as HP (splatter 9, bubbler 26, petalbow 52), so a splatter user needs *eleven* hits to do what the blade does in one. That is not "both first-class," that is "melee is the only class." The HUD *still* admits the lie in `hud()` (`match-mode.js:1206–1208`): *"Displayed as SOAK … Internally it is still hp counting down."* Ship the soak fantasy or a real HP bar — not an HP bar wearing a soak costume. (Unchanged since 08-14 challenge #1.)

**2. Bots STILL fight with a weapon players will never touch.**
`tacticalBrain` → `botShoot` (`botbrain.js:238–256`) fires the **hitscan carbine** `WEAPON` from `weapon.js` (26 dmg, headshot ×1.5, `traceShot`). No player ever uses that gun — players use soak projectiles + the saber. So the AI is a *third, invisible archetype*, and you can never practice against your own kit. Worse, `weapon.js` still exports a `Magazine` class (ammo/reload/reserve), a `buildViewModel()` carbine viewmodel, and the whole `WEAPON` hitscan config (`weapon.js:12–24`) that is **entirely dead for the player** — it exists only to feed the bot's hitscan. That is dead combat code masquerading as a feature. (Unchanged since 08-14 challenge #2.)

**3. 🆕 The studio is building PvP twice and starving the "BOTH" home.**
The README (`README.md:57–63`) still calls `duel/arena/` *"the main PvP game currently being worked on,"* and every commit since 08-14 is Battle Arena: *"v0.32 arena truth pass: hot-seat PVP, real combat mechanics,"* eight Worldforms, `src/game/spatial-duel.js` with rushdown/sniper/tank/control identities. Meanwhile the **only** place with melee **and** ranged first-class — `experiences/little-planet/` Tactical — has had **no combat commits at all** this fortnight. The lead's BOTH decision is being honored in the repo we refuse to touch, while we polish a *different* combat game next door. Either `little-planet` tactical is the BOTH home (then staff it) or it isn't (then port the vision into `duel/`). Right now we're paying double and shipping neither.

**4. 🆕 The lead's own open question — "ammo/heat vs stamina" — is still unanswered, two weeks on.**
The BOTH decision explicitly asked us to design a shared resource. It does not exist. Ranged `Charge` regen (`tools.js:99–120`) is generous and uniform: splatter cost 0.055 / regen 0.34 ≈ 6 shots/s, petalbow cost 0.34 / regen 0.24 ≈ 3/s — so there is *no* heat/ammo tension, every tool is just "spam until it refills." The saber's only limit is its 0.42s swing + a `Charge` (leafblade cost 0.5 / regen 0.42) that is the *same generic bar* as the guns — **no stamina, no movement commitment, no whiff punish, no prediction reward.** Mechanically today: melee = "walk to 3.4m, click, kill"; ranged = "lob slow blobs, hope." Neither expresses the movement+timing vs positioning+prediction split the lead wanted, and there is no rock-paper-scissors because the saber simply wins at ≤3.4m (see `saber.js:27` `reach: 3.4`, `arc: 1.5`) with no counter.

---

## THE ONE BIG IDEA

**Stop designing and start observing: ship the bot/player unification FIRST (the old D3), because it is the gate that makes every other balance number *measurable* — and that is exactly why D1/D2 have sat for two weeks.**

The root cause of the stall isn't disagreement about *what* to build; it's that **you cannot playtest soak or stamina against an AI that fires a hitscan carbine you don't own.** Until `botShoot` (`botbrain.js`) uses the real soak kit, any leafblade soak value, any stamina cost, any TTK curve we set is untestable in a bot match — so the directives keep slipping. The fix is ~40 lines: delete the `weapon.js` hitscan path from the bot, give the bot a loadout pulled from `TOOLS`/`statsFor`, and spawn a *real* `Projectiles` shot (reusing the existing pool) that applies `stats.soak` and is gated by `Charge`. Instantly the PvP loop becomes **observable** — you can watch a bot duel, see soak tick, watch a saber user close and a marksman hold space. D1 (soak-accumulate) and D2 (stamina-gated saber) then fall out naturally because for the first time you can *see* the fight. This is the highest-leverage week of PvP fun available, and it's the literal embodiment of the lead's BOTH call: one weapon truth, both families, finally first-class and finally watchable.

---

## STUDIO DIRECTIVES (ordered — for the engineer agent)

**D1 — GATE · `experiences/little-planet/src/modes/botbrain.js` (`botShoot`, lines 238–256).**
Replace the legacy hitscan `WEAPON` carbine with the same soak tools the player uses. Remove the `weapon.js` `WEAPON`/`traceShot` import; give the bot a loadout from `TOOLS`/`statsFor` and spawn a real `Projectiles` projectile (reuse the mode's pool) applying `stats.soak`, gated by `Charge`. Keep the bot's aim/spread/strafe brain — only the *delivery* changes.
*Acceptance:* a bot's shot travels as a visible, dodgeable projectile; it applies `soak` matching `tools.js` (splatter 9, petalbow 52, …), not `WEAPON.damage`; `traceShot` and `WEAPON.damage` are no longer referenced anywhere in the bot path; `weapon.js`'s `Magazine`/`buildViewModel` can be deleted without breaking the build.

**D2 — `experiences/little-planet/src/shared/match.js` (`_hit`, lines 242–263) + `weapons/tools.js` (leafblade) + `match-mode.js` (`_tacticalLocal`, 967–989) + `saber.js`.**
Make soak the single win condition for *everyone*: in `_hit`, accumulate `soak` instead of subtracting HP; at `soak >= 100` emit `down` (bubble-out via the existing `makeBubble()`, `projectiles.js:185`). Set `leafblade.soak` 100 → 34 (≥3 clean hits to down). Add a shared `Stamina` resource; a saber swing is a *commitment* — brief root + ~0.22s punishable recovery, blocked when stamina is empty, with a perfect-timing bonus in the `Saber.hits` 0.25–0.45 window.
*Acceptance:* full-HP enemy needs ≥3 saber hits to go down; HUD soak bar (0→100) honestly maps to `100−hp` with no secret HP math; swinging with empty stamina fails loudly; a whiffed swing shows a recoverable opening.

**D3 — `weapons/tools.js` (ranged stats) + `shared/match.js` (regen).**
Give the ranged family its *prediction/positioning* identity and a real counter to the saber: make `petalbow` the explicit anti-saber tool (long reach, high soak, slow fire) and add a small **out-of-combat soak regen** so chip damage isn't permanent (today only a Medkit pickup heals — `items.js:36`). Ensure no single action one-shots.
*Acceptance:* in a 1v1 bot duel, a saber user beats a splatter user *only* by closing distance; a petalbow user beats a saber user by holding space and leading the dodge; neither build is a free win; a player who breaks line-of-sight for ~3s recovers some soak.

---

## PERSONAL CHALLENGE FOR MIKEL

**Two weeks ago I asked "Soak or HP?", and you didn't answer — so the tactical combat hasn't moved while Battle Arena got a full v0.32 truth pass. The real question now is ownership, not tuning:** is `experiences/little-planet/` Tactical the canonical "BOTH" home or not? If **yes**, assign ONE engineer to D1 *this* week and I'll stop re-filing the same brief. If **no**, say so and I'll redirect the saber+projectile vision into `duel/arena/` where the studio's energy actually is. The saber is a one-tap kill today because **nobody owns the BOTH surface** — that's your call, not mine, and the lead's own "ammo/heat vs stamina" question stays unanswered until you make it.
