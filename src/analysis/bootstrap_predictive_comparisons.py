"""
Stage 5, Task 11: player-clustered bootstrap for the primary comparisons. Rows from the same
player are not independent (repeated observations of the same underlying ability), so resampling
resamples PLAYERS (with replacement), not individual rows, then takes all of that player's rows in
each bootstrap draw. Fixed seed for reproducibility. Descriptive 95% intervals only -- no formal
significance claim, per the brief's explicit instruction.
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"

SEED = 42
N_BOOT = 2000

METHOD_COLS = {
    "variant_A": "variant_A_rating_calibrated", "variant_B": "variant_B_rating_calibrated",
    "variant_C": "variant_C_rating_calibrated", "last5": "baseline_last5_calibrated",
    "season_to_date": "baseline_season_to_date_calibrated",
    "career_to_date": "baseline_career_to_date_calibrated",
}


def mae(pred, actual):
    return np.mean(np.abs(pred - actual))


def spearman_fast(pred, actual):
    from scipy.stats import spearmanr
    return spearmanr(pred, actual)[0]


def bootstrap_diff(df: pd.DataFrame, col_a: str, col_b: str, target_col: str, n_boot=N_BOOT, seed=SEED):
    """Vectorized player-clustered bootstrap: precompute each player's row-index array once, then
    each draw just concatenates integer index arrays (numpy, not pandas) and does a single
    fancy-index lookup -- orders of magnitude faster than pd.concat-per-draw."""
    y_all = df[target_col].to_numpy()
    a_all = df[col_a].to_numpy()
    b_all = df[col_b].to_numpy()
    player_ids = df.player_id.to_numpy()
    unique_players = np.unique(player_ids)
    player_positions = {p: np.where(player_ids == p)[0] for p in unique_players}

    rng = np.random.default_rng(seed)
    mae_diffs = np.empty(n_boot)
    spear_diffs = np.empty(n_boot)
    n_players = len(unique_players)
    for i in range(n_boot):
        sample_players = rng.choice(unique_players, size=n_players, replace=True)
        idx = np.concatenate([player_positions[p] for p in sample_players])
        y, pa, pb = y_all[idx], a_all[idx], b_all[idx]
        mae_diffs[i] = mae(pa, y) - mae(pb, y)
        spear_diffs[i] = spearman_fast(pa, y) - spearman_fast(pb, y)
    return mae_diffs, spear_diffs


def main():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    test = df[(df.split == "test") & df.future_3_match_performance.notna()].copy()
    for col in METHOD_COLS.values():
        test = test[test[col].notna()]
    print(f"Bootstrap cohort: {len(test)} rows, {test.player_id.nunique()} players")

    comparisons = [
        ("variant_C", "last5"),
        ("variant_C", "season_to_date"),
        ("variant_C", "career_to_date"),
        ("variant_C", "variant_B"),
        ("variant_A", "variant_B"),
        ("variant_B", "variant_C"),
    ]

    rows = []
    for a, b in comparisons:
        mae_d, spear_d = bootstrap_diff(test, METHOD_COLS[a], METHOD_COLS[b], "future_3_match_performance")
        rows.append({
            "comparison": f"{a} vs {b}",
            "mae_diff_mean": round(mae_d.mean(), 4),  # positive = A has HIGHER (worse) MAE than B
            "mae_diff_ci_lo": round(np.percentile(mae_d, 2.5), 4),
            "mae_diff_ci_hi": round(np.percentile(mae_d, 97.5), 4),
            "spearman_diff_mean": round(spear_d.mean(), 4),  # positive = A has HIGHER (better) Spearman
            "spearman_diff_ci_lo": round(np.percentile(spear_d, 2.5), 4),
            "spearman_diff_ci_hi": round(np.percentile(spear_d, 97.5), 4),
            "n_boot": N_BOOT, "seed": SEED,
        })

    out = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "stage5_bootstrap_comparisons.csv", index=False)
    print(out.to_string(index=False))
    print("\nNote: mae_diff = MAE(first) - MAE(second); negative means the first method has LOWER "
          "(better) error. spearman_diff = Spearman(first) - Spearman(second); positive means the "
          "first method ranks better. Descriptive 95% bootstrap intervals only.")


if __name__ == "__main__":
    main()
