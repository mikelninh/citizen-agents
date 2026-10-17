# 🔧 Gameplay Engineer — 2026-08-14

**Branch:** `studio/engineer-2026-08-14`  ·  **Build:** ✅ `npm run build` passed (56 modules, no errors)

Implemented the Studio Director's three directives from the 2026-08-14 brief
(`agent-digests/studio-director-2026-08-14.md`). All three (D1–D3) are done.

## What changed

**D1 — Soak is now the real win condition** (`shared/match.js`)
`_hit` no longer subtracts HP. It accumulates `soak` (0→100) on the target and
emits `down` at `soak >= 100`, deriving `hp = 100 - soak` so the snapshot and
every existing consumer keep working. Both the saber and projectiles feed the
*same* bar — neither can delete a full-HP foe in one action. Added `soak` to the
player record and reset it on round start / next round.

**D2 — The saber gets a melee identity** (`weapons/tools.js`, `match-mode.js`)
- `leafblade.soak` 100 → **34** → three clean hits to bubble someone.
- A swing now costs **stamina** (0.34 of the bar, regens ~2.4s). Swinging with
  no stamina fails loudly ("Winded — recharge stamina").
- An early-swing connect (saber arc 0.25–0.45) deals **1.5× soak** — the timing
  reward the brief asked for.
- A whiffed swing past the connect window leaves a recoverable **"Exposed!"**
  opening the opponent can punish.
- Local `this.soak` is now kept in sync on damage / down / heal so the HUD reads
  true. (Note: I deliberately did NOT root the player during recovery — that
  needs an engine movement hook and risked destabilising explore; the punish
  window is the existing post-swing cooldown + the "Exposed!" tell.)

**D3 — Bots fight with your kit** (`botbrain.js`)
`botShoot` no longer fires the legacy hitscan `WEAPON` carbine. It now uses the
player's `TOOLS` soak values: `leafblade` melee when within 3.4m, `petalbow`
ranged otherwise, with fire cadence tied to the real tool `rate`. The
`weapon.js` carbine import is gone from the bot path.

## Acceptance vs the brief
- D1: 100 combined soak = exactly one down; the soak bar maps to old 100−hp; no
  path subtracts raw HP. ✅
- D2: full-HP foe needs ≥3 clean saber hits; no-stamina swing fails loudly;
  whiff shows a recoverable opening. ✅
- D3: bot damage equals player tool soak numbers; `WEAPON`/`traceShot` carbine
  no longer referenced by tactical AI. ✅

## Honest caveats (follow-ups, not blockers)
- `makeBubble()` is not yet wired into the `down` event — the existing
  down/canMove=false flow is unchanged; the bubble-out visual is a polish pass.
- Bot ranged shots are still drawn as a tracer line, not a real spawned
  projectile (no `Projectiles` pool in the bot context). Damage/numbers are
  correct; the *visual* could later be swapped to spawn real bubbles/petals.
- The lead's open "Soak or HP?" decision is now *effectively* Soak (the HUD's
  rising bar) — D1 commits us to that; if Mikel wants lethal HP deathmatch,
  this is the pivot point to revisit.

## Next
Push to the director's rock-paper-scissors pass: tune petalbow vs saber vs
bubbler so each counters the others, and wire `makeBubble()` into `down`.
