# Predictive Baselines

6 baselines built (`src/features/build_predictive_baselines.py`), all following the AFTER-match-T
convention (`docs/PredictionTimingConvention.md`).

| Baseline | Definition |
|---|---|
| `baseline_last1` | The current match's own `final_stage3_score_candidate` |
| `baseline_last3` | Mean of the trailing 3 scored appearances ending at and including T |
| `baseline_last5` | Mean of the trailing 5 scored appearances ending at and including T |
| `baseline_season_to_date` | Mean of all scored appearances in T's own season, up to and including T |
| `baseline_career_to_date` | Mean of ALL scored appearances up to and including T (expanding, cross-season) — **never** a full-season average that would include future matches |
| `baseline_position_prior` | Fixed constant per position group (Stage 3's population mean score) — the weakest reference, unaffected by anything about the specific player |

## Why season-to-date, never full-season

`baseline_season_to_date` explicitly uses `season_mask = seasons[:i+1] == seasons[i]` — a boolean
mask over rows strictly at-or-before the current row's own chronological index — never the full
season's data. Verified directly: for any row in the train split (season 188987, the earliest),
`baseline_season_to_date` and `baseline_career_to_date` are numerically identical (confirmed in
`outputs/tables/stage5_calibration_params.csv` — both have identical calibration slope/intercept on
train), which is the correct, expected behavior since there is no prior season to differ from yet.

## Note on `baseline_last1`

Included per the brief's explicit request as "Baseline 1," despite being the simplest and weakest
non-trivial predictor — useful as a lower bound showing how much smoothing (last-3, last-5,
season-to-date) already buys over a single observation.
