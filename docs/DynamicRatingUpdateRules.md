# Dynamic Rating Update Rules

Three variants built (the brief's minimum requirement), one optional variant explicitly skipped
and justified. All three share the base update form:

```
rating_new = rating_old + update_multiplier * performance_surprise
```

`update_multiplier` differs by variant and always incorporates the confidence-tier weighting
(`docs/MinutesRatingUpdatePolicy.md`) uniformly, so that axis does not confound the variant
comparison in `docs/Stage4DynamicRatingDecision.md`.

## Variant A — Simple Dynamic Update

- **Expectation:** Expectation A (player-rating-only, no opponent term).
- **Update multiplier:** `K_base * confidence_weight`, `K_base = 3` (fixed, not history-aware).
- The simplest dynamic benchmark: no opponent adjustment anywhere in the pipeline.

## Variant B — Opponent-Adjusted Dynamic Update

- **Expectation:** Expectation B (player rating + opponent-strength adjustment).
- **Update multiplier:** `K_base * confidence_weight`, same fixed `K_base = 3` as Variant A.
- The main research candidate per the brief's own framing — isolates the effect of adding opponent
  context to the expectation, holding the update rule itself identical to Variant A.

## Variant C — History-Aware Update

- **Expectation:** Expectation B (same as Variant B — isolates the effect of history-awareness,
  not a second opponent-adjustment change).
- **Update multiplier:** `K_base * confidence_weight * decay_factor(matches_seen_before)`, where

  ```
  decay_factor(n) = FLOOR + (1 - FLOOR) / (1 + n / M0)
  ```

  `FLOOR = 0.4`, `M0 = 15` — both predefined, round design constants, not fit to any outcome. A
  brand-new player (`n=0`) updates at full strength (`decay_factor=1.0`); by `n=15` matches seen,
  the effective update rate has roughly halved toward the floor; it asymptotically approaches 0.4x
  (never frozen entirely — an established player can still meaningfully rise or fall, just more
  slowly than a newcomer). This is a **football-appropriate simplification**, not a copy of chess
  Elo's provisional-rating schedule (which uses a hard threshold and a discrete K-drop, not a smooth
  decay) — chosen because a smooth decay avoids an arbitrary cliff at some fixed match count.

## Optional Variant D — skipped, documented

An uncertainty-aware variant (update scales with a tracked uncertainty state, larger updates when
uncertain) was evaluated and **not built**, for a concrete reason: Variant C's `decay_factor(matches_seen_before)`
already implements the core idea the brief describes for uncertainty-awareness ("higher
uncertainty → larger update, lower uncertainty → smaller update") — under any reasonable definition,
uncertainty is highest when `matches_seen` is lowest, so a separate uncertainty state driving a
second update-scaling term would be *functionally redundant* with Variant C's decay factor, adding a
second free design constant without adding a genuinely new mechanism to compare. Per the brief's own
permission ("optional... only if it remains simple and defensible"), the honest conclusion is that a
distinct Variant D is not defensible as *distinct* from Variant C at this stage. `rating_uncertainty`
is still tracked and output as a descriptive field (`docs/PlayerRatingStateDefinition.md`,
`docs/InactivityPolicy.md`) for future use, just not wired into a fourth update rule here.

## Explicitly NOT tuned against Stage 5

`K_base=3`, `FLOOR=0.4`, `M0=15`, `RATING_SCALE=40`, `OPPONENT_SCALE=0.03` are all predefined design
constants, chosen once on legibility/round-number grounds before the engine was ever run, and never
adjusted based on any observed rating trajectory, update distribution, or (especially) any
future-performance comparison — Stage 5 does not exist yet in this project's pipeline. If Stage 5
later finds these constants materially miscalibrated, that is Stage 6's (Robustness & Ablations) job
to explore, not something corrected retroactively here.
