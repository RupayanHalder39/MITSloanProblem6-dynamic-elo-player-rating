# Performance Feature Selection

Selected from the 111-column inventory (`docs/PerformanceFeatureInventory.md`), after removing
confirmed redundancies, SEMANTICS UNVERIFIED columns, and near-zero-variance columns unfit to carry
weight on their own. **29 features selected** (down from 111) — compact and defensible, not a
"throw everything in" approach, per the brief's explicit instruction.

## Selection rules applied

1. Where two columns were confirmed >95% row-identical (`docs/PerformanceFeatureInventory.md`'s
   redundancy table), only one is kept: `minutes_played` (not `minutes_tagged`), `aerial_duels`/
   `aerial_duels_won` (not the `field_*` near-duplicates).
2. Where two columns are a legacy/updated-methodology pair (`duels_won` family vs. `new_duels_won`
   family), the **`new_*` variant is preferred** as the provider's current methodology.
3. `lateral_passes`/`successful_lateral_passes` (SEMANTICS UNVERIFIED — 100% identical to the
   vertical variants) are **excluded entirely**; `vertical_passes`/`successful_vertical_passes` are
   kept as the sole directional-volume representative, with the caveat noted in the inventory.
4. `pressing_duels_won` and `gk_successful_exits` (always zero) are **excluded**.
5. Structurally rare columns with <1.5% non-zero rate (`penalties`, `direct_free_kicks*`,
   `second_assists`, `third_assists`) are **excluded from the core set** — legitimate events, but
   too sparse to carry independent weight in a per-match score; goals/assists already capture their
   downstream impact when they occur.
6. For attempted/completed pairs, only ONE side is kept per action type — generally the
   **completed/successful** count (reflects quality, not just volume), except where the raw
   attempt count itself is the meaningful signal (`shots`, `duels`, `dribbles`).

## Selected core feature set (29 features)

### ATTACKING
`goals`, `xg_shot`, `shots`, `shots_on_target`, `touch_in_box`, `new_successful_dribbles`,
`progressive_run`

### CREATION
`assists`, `xg_assist`, `key_passes`, `successful_crosses`, `successful_through_passes`,
`shot_assists`

### POSSESSION / PROGRESSION
`successful_passes`, `passes` (used together as a completion-rate pair, not two independent score
inputs — see `docs/PerformanceNormalizationDesign.md`), `successful_progressive_passes`,
`successful_passes_to_final_third`, `losses`

### DEFENDING
`new_duels_won`, `interceptions`, `successful_defensive_action`, `clearances`, `recoveries`,
`dribbles_against_won`, `aerial_duels_won`

### GOALKEEPING (GK-only; structurally zero/irrelevant for outfield players)
`gk_saves`, `xg_save`, `gk_conceded_goals`, `gk_clean_sheets`, `gk_aerial_duels_won`,
`successful_goal_kicks`

### DISCIPLINE / NEGATIVE EVENTS
`yellow_cards`, `red_cards`, `fouls`, `dangerous_own_half_losses`

### MINUTES / AVAILABILITY (used for eligibility + normalization, not scored as a performance input)
`minutes_played`, `is_starting`

## Explicitly excluded, with reason

| Excluded | Reason |
|---|---|
| `minutes_tagged` | 100% identical to `minutes_played` |
| `field_aerial_duels(_won)` | 98%+ identical to `aerial_duels(_won)` |
| `duels_won`, `defensive_duels_won`, `offensive_duels_won`, `successful_dribbles` | Superseded legacy versions of `new_*` methodology columns |
| `lateral_passes`, `successful_lateral_passes` | SEMANTICS UNVERIFIED (100% identical to vertical_passes — direction cannot be trusted) |
| `pressing_duels_won`, `gk_successful_exits` | Always zero — not populated for this competition |
| `penalties`, `successful_penalties`, `direct_free_kicks`, `direct_free_kicks_on_target`, `second_assists`, `third_assists` | <1.5% non-zero rate — too sparse to weight independently |
| `offsides` | Considered as a negative event but dropped: correlates with attacking intent as much as error, ambiguous sign, small effect either way |
| All remaining ~70 columns not listed above (e.g. `smart_passes`, `linkup_plays`, `accelerations`, `missed_balls`, positional pass-direction breakdowns, `own_half_losses` vs. its "dangerous" subset, GK exit/goal-kick sub-splits) | Overlapping in football meaning with a selected feature already carrying that signal (e.g. `key_passes` already captures creative-passing quality without also needing `smart_passes`), or too fine-grained a sub-split of an already-selected count to add independent information at this stage. Available for a future ablation (Stage 6) if the selected 29-feature set under-performs. |

## Football-defensibility check

No single metric dominates by construction: goals/assists (the two most "obvious" attacking metrics)
are 2 of 29 features and are further diluted by category aggregation
(`docs/PerformanceScoreCandidates.md`'s Score B), not summed directly against defensive or
goalkeeping metrics. Every position group has at least 5 CORE POSITIVE metrics available to it
(`docs/PositionSpecificPerformanceDesign.md`), so a defender or goalkeeper is never scored against
an attacker's metric set.
