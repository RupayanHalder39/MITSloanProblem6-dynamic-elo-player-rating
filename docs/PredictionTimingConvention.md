# Prediction Timing Convention

## Decision: **AFTER match T** (Option B), per the brief's explicit instruction

"Given everything we know after today's match, how well will this player perform over the next few
matches?"

## What this means concretely for every predictor

| Predictor | Includes match T? |
|---|---|
| Dynamic rating (A/B/C) | **`post_match_player_rating`** — the rating AFTER T's update is applied |
| `baseline_last1` | Match T's own score |
| `baseline_last3` / `baseline_last5` | Trailing window ending at and including T |
| `baseline_season_to_date` | All of P's scored appearances in T's season, up to and including T |
| `baseline_career_to_date` | All of P's scored appearances up to and including T (expanding) |
| `baseline_position_prior` | Unaffected by T — a fixed constant, included for completeness as the weakest reference |
| Target: `future_3_match_performance` | **Never** includes T — strictly T+1, T+2, T+3 |

This is the only internally consistent choice: the dynamic rating's `post_match_player_rating` is
naturally a "what we know as of just after this match" quantity (that is what Stage 4's engine
computes), so every other predictor is defined on the same T-inclusive footing for a fair
comparison — using `pre_match_player_rating` instead would compare a "before T" rating against
"after T" baselines, which is not a like-for-like predictor set.

## Why not BEFORE match T

A before-T convention would require pairing `pre_match_player_rating` with baselines computed only
from *prior* matches (excluding T), which is a different, also-valid research design, but not what
this stage was asked to build — and would make match T itself uninformative to any predictor, which
under-uses the very score Stage 3 was built to compute. Left as a documented, legitimate variant
design for a future ablation (Stage 6), not built here.
