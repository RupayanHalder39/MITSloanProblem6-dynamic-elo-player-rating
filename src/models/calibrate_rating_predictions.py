"""
Stage 5, Task 6 (scale issue) / Task 7: builds the full evaluation dataset.

Merges the Stage-3 scored population, the leakage-safe future targets, the 6 baselines, and the
A/B/C post-match dynamic ratings (docs/PredictionTimingConvention.md: AFTER-match-T convention --
post_match_player_rating, which already reflects match T, is the correct predictor under this
convention). Assigns a chronological season-based train/validation/test split
(docs/TemporalEvaluationSplit.md) and fits a simple linear calibration (future_3 ~ a + b*predictor)
for every predictor, USING TRAIN ROWS ONLY, then applies it to validation/test.

Output: data/processed/player_rating_predictive_evaluation.parquet
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

# docs/TemporalEvaluationSplit.md
SEASON_SPLIT = {"188987": "train", "189951": "validation", "191644": "test"}

PREDICTOR_COLS = [
    "baseline_last1", "baseline_last3", "baseline_last5", "baseline_season_to_date",
    "baseline_career_to_date", "baseline_position_prior",
    "variant_A_rating", "variant_B_rating", "variant_C_rating",
]


def fit_linear_calibration(x_train: np.ndarray, y_train: np.ndarray) -> tuple[float, float]:
    """OLS a + b*x, fit on TRAIN rows only. Returns (a, b)."""
    mask = np.isfinite(x_train) & np.isfinite(y_train)
    x, y = x_train[mask], y_train[mask]
    # explicit OLS via normal equations (no sklearn dependency, matches Stage 3's own no-sklearn policy)
    xm, ym = x.mean(), y.mean()
    b = np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2)
    a = ym - b * xm
    return float(a), float(b)


def main():
    scored = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = scored[scored.score_eligible & scored.final_stage3_score_candidate.notna()][
        ["match_id", "player_id", "match_datetime_utc", "season_id", "position_group",
         "team_id", "opponent_team_id", "minutes_confidence"]
    ]
    targets = pd.read_parquet(PROCESSED / "future_performance_targets.parquet")
    baselines = pd.read_parquet(PROCESSED / "predictive_baselines.parquet")
    ratings = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")

    ratings_wide = ratings.pivot_table(
        index=["match_id", "player_id"], columns="rating_variant",
        values=["post_match_player_rating", "matches_seen_before"],
    )
    ratings_wide.columns = [f"{a}_{b}" for a, b in ratings_wide.columns]
    ratings_wide = ratings_wide.rename(columns={
        "post_match_player_rating_A": "variant_A_rating",
        "post_match_player_rating_B": "variant_B_rating",
        "post_match_player_rating_C": "variant_C_rating",
        "matches_seen_before_A": "matches_seen_before",  # identical across variants by construction
    }).reset_index()
    ratings_wide = ratings_wide[["match_id", "player_id", "variant_A_rating", "variant_B_rating",
                                  "variant_C_rating", "matches_seen_before"]]

    df = scored.merge(targets, on=["match_id", "player_id"], how="left") \
               .merge(baselines, on=["match_id", "player_id"], how="left") \
               .merge(ratings_wide, on=["match_id", "player_id"], how="left")

    df["match_datetime_utc"] = pd.to_datetime(df.match_datetime_utc, utc=True)
    df["split"] = df.season_id.astype(str).map(SEASON_SPLIT)

    # --- experience bucket (Task 13) ---
    bins = [-1, 4, 14, 29, 10_000]
    labels = ["0-4", "5-14", "15-29", "30+"]
    df["experience_bucket"] = pd.cut(df.matches_seen_before, bins=bins, labels=labels)

    # --- calibration: fit on TRAIN rows only, against future_3_match_performance ---
    train_mask = (df.split == "train") & df.future_3_match_performance.notna()
    calib_params = {}
    for col in PREDICTOR_COLS:
        x_train = df.loc[train_mask, col].to_numpy(dtype=float)
        y_train = df.loc[train_mask, "future_3_match_performance"].to_numpy(dtype=float)
        a, b = fit_linear_calibration(x_train, y_train)
        calib_params[col] = (a, b)
        df[f"{col}_calibrated"] = a + b * df[col]

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "player_rating_predictive_evaluation.parquet"
    df.to_parquet(out_path)

    calib_df = pd.DataFrame(
        [{"predictor": k, "intercept_a": v[0], "slope_b": v[1]} for k, v in calib_params.items()]
    )
    calib_df.to_csv(BASE / "outputs" / "tables" / "stage5_calibration_params.csv", index=False)

    print(f"Wrote {out_path} ({len(df)} rows)")
    print(df.split.value_counts(dropna=False))
    print()
    print(calib_df.to_string())


if __name__ == "__main__":
    main()
