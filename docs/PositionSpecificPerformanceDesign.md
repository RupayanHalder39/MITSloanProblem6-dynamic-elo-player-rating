# Position-Specific Performance Design

A goalkeeper and a striker cannot be judged on the same metrics. Each of the 4 production position
groups (`docs/PositionGroupingDesign.md`) gets its own CORE POSITIVE / CORE NEGATIVE / CONTEXT /
EXCLUDED feature set, drawn from the 29 selected features
(`docs/PerformanceFeatureSelection.md`). **Goals are deliberately not the dominant universal metric**
— each group's positive set spans at least 3 football categories (not just attacking), so a
defender or a deep-lying passer has a real route to a high score without ever shooting.

## GK

- **CORE POSITIVE:** `gk_saves`, `xg_save` (shot-stopping quality above expectation),
  `gk_clean_sheets`, `gk_aerial_duels_won`, `successful_goal_kicks`
- **CORE NEGATIVE:** `gk_conceded_goals`, `red_cards`
- **CONTEXT:** `minutes_played`, `is_starting`
- **EXCLUDED (all outfield categories):** every ATTACKING/CREATION/DEFENDING/POSSESSION feature —
  a goalkeeper's touches on the ball are structurally rare and not comparable to an outfield
  player's; scoring a GK on `passes` or `duels_won` would penalize the position for existing.

## DEF

- **CORE POSITIVE:** `new_duels_won`, `interceptions`, `successful_defensive_action`, `clearances`,
  `recoveries`, `aerial_duels_won`, `successful_passes` (build-up contribution), `successful_progressive_passes`
- **CORE NEGATIVE:** `dangerous_own_half_losses`, `fouls`, `yellow_cards`, `red_cards`
- **CONTEXT:** `dribbles_against_won` (context, not core — a fullback facing more wingers than a
  centre-back is a positional artifact, not a skill difference at this stage of design)
- **EXCLUDED:** `goals`, `xg_shot`, `shots`, `touch_in_box`, GK metrics — defenders are not expected
  to shoot; a rare defensive goal is captured incidentally via the shared `goals` field being
  available generally, but is not part of the DEF core set so it cannot inflate a defender's score
  on the rare occasion it happens (it still shows in the raw data for case-study inspection).

## MID

- **CORE POSITIVE:** `key_passes`, `successful_through_passes`, `successful_crosses`,
  `successful_progressive_passes`, `successful_passes_to_final_third`, `new_duels_won`,
  `interceptions`, `recoveries`, `assists`, `xg_assist`
- **CORE NEGATIVE:** `losses`, `dangerous_own_half_losses`, `fouls`, `yellow_cards`, `red_cards`
- **CONTEXT:** `shot_assists`, `new_successful_dribbles`, `progressive_run`
- **EXCLUDED:** GK metrics. `goals`/`shots`/`touch_in_box` are CONTEXT-tier for MID (a midfielder
  who scores should benefit, but it is not one of the core expectations of the role the way it is
  for ATT).

## ATT

- **CORE POSITIVE:** `goals`, `xg_shot`, `shots_on_target`, `touch_in_box`,
  `new_successful_dribbles`, `progressive_run`, `assists`, `xg_assist`, `key_passes`
- **CORE NEGATIVE:** `losses`, `fouls`, `yellow_cards`, `red_cards`
- **CONTEXT:** `successful_crosses`, `shot_assists`, `new_duels_won` (defensive work-rate credit,
  not a core expectation)
- **EXCLUDED:** `interceptions`, `clearances`, `successful_defensive_action`, GK metrics —
  attackers are not penalized for low defensive-action counts, since defending is not their role's
  primary job.

## Design principle behind CORE vs. CONTEXT

CORE metrics are summed/averaged into the category and final scores with full weight
(`docs/PerformanceScoreCandidates.md`). CONTEXT metrics are retained in the output dataset for
case-study inspection and future ablations but are **not** part of the position's default score
formula in this stage — they represent real but secondary contributions (e.g. a striker's tackle,
a defender's dribble past an opponent) that would otherwise either inflate a position's score for an
atypical event or require an arbitrary secondary weight this stage prefers not to invent without
further validation.

## Handling `UNKNOWN` position (7 rows)

Scored using the full outfield union of CORE POSITIVE/NEGATIVE metrics (DEF+MID+ATT combined, GK
excluded) at reduced confidence (`position_confidence = "UNKNOWN"` flag retained in the output
dataset) — never silently dropped, never assigned a guessed position.
