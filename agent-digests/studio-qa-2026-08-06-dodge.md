# QA Playtest — 2026-08-06 (second pass: PR #4, Dodge Roll)

**Verdict: SHIP WITH NOTES.**

This is a second QA pass for the day. The morning pass covered PR #2/#3; PR #4
(`studio/engineer-2026-08-06-dodge`, "Dodge Roll — double-tap burst + i-frames")
landed after it and had not been tested. That is what this report covers.

## What I ran

| Check | Result |
|---|---|
| `npm install --no-audit --no-fund` | pass — 97 packages |
| `npm run build` | **pass** — 56 modules, 5.40s, exit 0 |
| `node server/node.js` (8s boot) | **pass** — banner on :8787, no throw, clean kill |
| `curl http://localhost:8787/` | **pass** — HTTP 200 |
| `node tools/dodgetest.mjs` | **pass** — 6/6 assertions |

The engineer shipped `tools/dodgetest.mjs` with the feature, and it is a genuinely
good test: it covers the single tap, the double tap inside the window, the
`endFrame` clear, the triple-tap guard, the expired window, and the A-then-D
cross-key case. All six pass. Credit where it is due — this is the first agent
change in this repo to arrive with its own test.

Build note: the 927 kB / 255 kB gzip chunk warning is still present. It predates
this branch and is not a regression.

## The one thing that matters

**HIGH — the i-frames do not work in multiplayer.**

The feature's defining property is 0.12s of invulnerability at the front of the
roll. The implementation delivers that by filtering the local player out of the
target list in `match-mode.js`:

```js
const hittable = this.ctx.player.iframes > 0
  ? parts.filter((p) => p.id !== this.localId)
  : parts;
```

But damage in this game is **shooter-authoritative**. From `_onProjectileHit`:

```js
if (item.owner !== this.localId) {
  // Someone else's shot: we only draw it, the owner reports it.
  ...
  return;
}
...
this._request({ type: 'hit', target: target.id, damage: item.damage });
```

The shooter's client decides the hit and reports it. It resolves that hit against
*its own* participant list, which knows nothing about the victim's `iframes`. So
the filter above only ever protects you from bot fire (host-simulated on your
machine) and from your own projectiles.

Against another human, you roll, the pip glows blue, and you take the damage anyway.

Nobody will file this as a bug — they will just quietly conclude the roll "feels
unreliable" and stop using it. That is the worst kind of defect.

**Fix, smallest version:** put an `inv` flag in `_localReport()` — the plumbing is
already there — and drop inbound `hit` requests whose target reported `inv` within
the last ~150ms. Make invulnerability true where damage is *applied*, not where it
is *predicted*.

Worth flagging for the director separately: at 80ms RTT a 0.12s window is roughly
one round trip. Even done correctly, this value may need to grow.

## Also found

- **MEDIUM** — the filtered list is passed to `_driveBots`, so during i-frames the
  local player disappears from bot *perception*, not just from hit resolution.
  Bots can drop aim and re-target mid-roll. Pass unfiltered `parts` to the bots and
  enforce invulnerability at the `onHit`/`onTag` callbacks instead.
- **MEDIUM** — `dodge()` has no grounded check. Airborne double-taps give a 14 m/s
  burst that overwrites `vel.x`/`vel.z` and bypasses the air accel/friction model,
  repeatable every 0.8s. This reads as an unintended air-mobility tool for a move
  described as a committed ground roll.
- **MEDIUM** — hide & seek coverage is inconsistent: a bot seeker cannot tag you
  mid-roll, a human seeker can. Same root cause as the HIGH.
- **LOW** — entering water cancels the roll but keeps the full 0.8s cooldown.
- **LOW** — the pip is nested inside the crosshair render branch and vanishes
  whenever the crosshair is hidden.

## What I checked and found correct

The yaw-to-world math in `_dodgeInput` is right — I verified `forward = (-sin, -cos)`
and `right = (cos, -sin)` against the engine's own convention, and W/A/S/D map
correctly. `doubleTapped_` is cleared in `endFrame()` alongside `justPressed`, so no
stale edge leaks. The `-9` sentinel genuinely does stop a triple tap becoming two
dodges. `reset()` clears all three dodge fields, so respawn cannot inherit a live
roll. No new intervals or listeners — no leak surface in this diff.

## What I could NOT test

Automated QA cannot playtest feel. Whether 14 m/s over 0.35s with 0.12s of i-frames
and a 0.45s cooldown is *fun* — or broken — is a human judgement and this report
makes no claim about it. I also could not run two real clients against each other;
the HIGH issue was found by reading the netcode path, not by watching a desync.
Not covered: browser rendering of the pip, roll behaviour against terrain collision
on the curved planet (cliff edges, steep slopes), and any non-keyboard input path.

## Recommendation

Do not merge as-is. The build is green and nothing here is a BLOCKER, but the
headline feature is currently single-player-only. The `inv`-in-report fix is small
and the branch is otherwise clean and well-tested — worth one more engineer pass
before this goes to main.
