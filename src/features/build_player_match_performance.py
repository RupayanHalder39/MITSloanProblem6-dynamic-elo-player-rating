"""
Stage 3: builds data/processed/player_match_performance.parquet -- extends the Stage-2 foundation
with position groups, minutes buckets/confidence tiers, leakage-safe normalized features, category
scores, and 3 candidate per-match performance scores (A/B/C). This is a PERFORMANCE SCORE, not a
dynamic rating: it describes how well a player performed in one match, using only information from
that match. No rating update, no cross-match state, happens here (that is Stage 4).

See docs/PerformanceFeatureSelection.md, docs/PositionSpecificPerformanceDesign.md,
docs/MinutesNormalizationPolicy.md, docs/PerformanceNormalizationDesign.md,
docs/PerformanceScoreCandidates.md, docs/PerformanceScoreScale.md for the full design reasoning
behind every choice made in this script.
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "processed" / "raw"
PROCESSED = BASE / "data" / "processed"

# --- Task 3: position grouping (docs/PositionGroupingDesign.md) ---
FINE_TO_GROUP4 = {
    "gk": "GK",
    "rb": "DEF", "lb": "DEF", "rcb": "DEF", "lcb": "DEF", "cb": "DEF", "rcb3": "DEF", "lcb3": "DEF",
    "rwb": "DEF", "lwb": "DEF", "rb5": "DEF", "lb5": "DEF",
    "rcmf": "MID", "lcmf": "MID", "rcmf3": "MID", "lcmf3": "MID", "amf": "MID", "dmf": "MID",
    "rdmf": "MID", "ldmf": "MID", "ramf": "MID", "lamf": "MID", "rw": "MID", "lw": "MID",
    "cf": "ATT", "ss": "ATT", "rwf": "ATT", "lwf": "ATT",
}
COARSE_TO_GROUP = {"GKP": "GK", "DEF": "DEF", "MID": "MID", "FWD": "ATT"}

# --- Task 2/5: selected features, per docs/PerformanceFeatureSelection.md ---
POSITIVE_FEATURES = {
    "GK": ["gk_saves", "xg_save", "gk_clean_sheets", "gk_aerial_duels_won", "successful_goal_kicks"],
    "DEF": ["new_duels_won", "interceptions", "successful_defensive_action", "clearances",
            "recoveries", "aerial_duels_won", "successful_passes", "successful_progressive_passes"],
    "MID": ["key_passes", "successful_through_passes", "successful_crosses",
            "successful_progressive_passes", "successful_passes_to_final_third", "new_duels_won",
            "interceptions", "recoveries", "assists", "xg_assist"],
    "ATT": ["goals", "xg_shot", "shots_on_target", "touch_in_box", "new_successful_dribbles",
            "progressive_run", "assists", "xg_assist", "key_passes"],
}
NEGATIVE_FEATURES = {
    "GK": ["gk_conceded_goals", "red_cards"],
    "DEF": ["dangerous_own_half_losses", "fouls", "yellow_cards", "red_cards"],
    "MID": ["losses", "dangerous_own_half_losses", "fouls", "yellow_cards", "red_cards"],
    "ATT": ["losses", "fouls", "yellow_cards", "red_cards"],
}
# category membership of each positive feature, for Score B (docs/PerformanceScoreCandidates.md)
FEATURE_CATEGORY = {
    "gk_saves": "GOALKEEPING", "xg_save": "GOALKEEPING", "gk_clean_sheets": "GOALKEEPING",
    "gk_aerial_duels_won": "GOALKEEPING", "successful_goal_kicks": "GOALKEEPING",
    "new_duels_won": "DEFENDING", "interceptions": "DEFENDING",
    "successful_defensive_action": "DEFENDING", "clearances": "DEFENDING",
    "recoveries": "DEFENDING", "aerial_duels_won": "DEFENDING",
    "successful_passes": "POSSESSION", "successful_progressive_passes": "POSSESSION",
    "successful_passes_to_final_third": "POSSESSION",
    "key_passes": "CREATION", "successful_through_passes": "CREATION",
    "successful_crosses": "CREATION", "assists": "CREATION", "xg_assist": "CREATION",
    "goals": "ATTACKING", "xg_shot": "ATTACKING", "shots_on_target": "ATTACKING",
    "touch_in_box": "ATTACKING", "new_successful_dribbles": "ATTACKING",
    "progressive_run": "ATTACKING",
}

ALL_RAW_COLS = sorted(set(sum(POSITIVE_FEATURES.values(), []) + sum(NEGATIVE_FEATURES.values(), [])))

MIN_MINUTES_FULL = 20  # docs/MinutesNormalizationPolicy.md -- CV-based threshold
COLD_START_FLOOR = 50  # docs/PerformanceNormalizationDesign.md


def shrink_rate(count: pd.Series, minutes: pd.Series, prior_rate: pd.Series, k: float = 8.0) -> pd.Series:
    """Shrinkage-adjusted per-90 rate: blends the observed count toward a position-group prior
    using a pseudo-count of k*prior_rate matches worth of prior data. Reduces to something close
    to the raw per-90 rate as minutes grow large, and to the prior as minutes -> 0. See
    docs/MinutesNormalizationPolicy.md."""
    pseudo_minutes = k * 90.0
    return (count + prior_rate * pseudo_minutes / 90.0) / ((minutes + pseudo_minutes) / 90.0)


def expanding_robust_zscore(df: pd.DataFrame, value_col: str, group_col: str, date_col: str) -> tuple[pd.Series, pd.Series]:
    """Leakage-safe: for each row, uses only strictly-earlier rows (by date_col) within the same
    group_col to compute a running median/IQR, falling back to the full-sample distribution below
    COLD_START_FLOOR prior observations. See docs/PerformanceNormalizationDesign.md.

    Vectorized via pandas' C-level `.expanding()` + `.shift(1)` (excludes the current row) instead
    of a per-row Python loop -- the naive per-row np.median/np.percentile loop is O(n^2) per group
    per feature and does not finish in reasonable time at this dataset's size (tens of thousands of
    rows x 29 features x 4 groups); `.expanding()` is the standard vectorized equivalent."""
    out = pd.Series(index=df.index, dtype=float)
    basis = pd.Series(index=df.index, dtype=object)

    full_med = df.groupby(group_col)[value_col].transform("median")
    full_q1 = df.groupby(group_col)[value_col].transform(lambda s: s.quantile(0.25))
    full_q3 = df.groupby(group_col)[value_col].transform(lambda s: s.quantile(0.75))
    full_iqr = (full_q3 - full_q1).clip(lower=0.1)

    for grp, sub in df.groupby(group_col):
        sub = sub.sort_values(date_col)
        vals = sub[value_col]
        n = len(vals)
        exp_med = vals.expanding(min_periods=1).median().shift(1)
        exp_q1 = vals.expanding(min_periods=1).quantile(0.25).shift(1)
        exp_q3 = vals.expanding(min_periods=1).quantile(0.75).shift(1)
        exp_iqr = (exp_q3 - exp_q1).clip(lower=0.1)

        prior_count = pd.Series(range(n), index=sub.index)  # number of strictly-prior rows seen
        use_expanding = prior_count >= COLD_START_FLOOR

        med = exp_med.where(use_expanding, full_med.loc[sub.index])
        iqr = exp_iqr.where(use_expanding, full_iqr.loc[sub.index])
        z = (vals - med) / iqr

        out.loc[sub.index] = z.values
        basis.loc[sub.index] = np.where(use_expanding, "expanding", "cold_start_prior")
    return out, basis


def descriptive_robust_zscore(df: pd.DataFrame, value_col: str, group_col: str) -> pd.Series:
    """Full-sample robust z-score -- descriptive/diagnostic only, NOT leakage-safe, NOT used for
    final_stage3_score_candidate. See docs/PerformanceNormalizationDesign.md."""
    med = df.groupby(group_col)[value_col].transform("median")
    q1 = df.groupby(group_col)[value_col].transform(lambda s: s.quantile(0.25))
    q3 = df.groupby(group_col)[value_col].transform(lambda s: s.quantile(0.75))
    iqr = (q3 - q1).clip(lower=0.1)
    return (df[value_col] - med) / iqr


def main():
    foundation = pd.read_parquet(PROCESSED / "player_match_foundation.parquet")
    stats = pd.read_parquet(RAW / "player_match_stats_total_championship.parquet")
    for c in ALL_RAW_COLS + ["minutes_played"]:
        stats[c] = pd.to_numeric(stats[c], errors="coerce")

    # drop foundation's own appearance-level goals/assists (object dtype, from
    # match_player_appearances) so the merge below injects the numeric player_match_stats_total
    # versions under their plain column names instead of colliding into a shadowed "_stats" suffix
    foundation_for_merge = foundation.drop(columns=[c for c in ("goals", "assists") if c in foundation.columns])
    df = foundation_for_merge.merge(
        stats[["player_id", "match_id", "minutes_played"] + ALL_RAW_COLS],
        on=["player_id", "match_id"], how="left", suffixes=("", "_stats"),
    )

    # --- position group (Task 3) ---
    df["position_group"] = df.position_code.map(FINE_TO_GROUP4)
    fallback = df.position_group.isna() & df.coarse_role.notna()
    df.loc[fallback, "position_group"] = df.loc[fallback, "coarse_role"].map(COARSE_TO_GROUP)
    df["position_source"] = np.where(
        df.position_code.notna(), "fine_position",
        np.where(fallback, "coarse_role_fallback", "unknown"),
    )
    df["position_group"] = df.position_group.fillna("UNKNOWN")

    # --- minutes bucket / eligibility / confidence (Task 4) ---
    mp = df.minutes_played_stats if "minutes_played_stats" in df.columns else df.minutes_played
    df["minutes_for_scoring"] = pd.to_numeric(mp, errors="coerce")

    def elig(m):
        if pd.isna(m):
            return False, "no_stats_row", "NONE"
        if m == 0:
            return False, "did_not_play", "NONE"
        if m < MIN_MINUTES_FULL:
            return True, "", "LOW"
        if m < 60:
            return True, "", "MEDIUM"
        return True, "", "HIGH"

    elig_results = df.minutes_for_scoring.apply(elig)
    df["score_eligible"] = elig_results.apply(lambda t: t[0])
    df["exclusion_reason"] = elig_results.apply(lambda t: t[1])
    df["minutes_confidence"] = elig_results.apply(lambda t: t[2])

    # --- Task 6: shrinkage rate + leakage-safe normalization, per eligible row ---
    scoreable = df[df.score_eligible].copy()
    scoreable["match_datetime_utc"] = pd.to_datetime(scoreable.match_datetime_utc, utc=True)

    for group, feats in {**POSITIVE_FEATURES, **{}}.items():
        pass  # feature lists are position-specific; computed per-row below via position_group

    # position-group prior rate per feature (per-90, using HIGH+MEDIUM confidence rows only, so the
    # prior itself is not distorted by shrinking LOW-confidence rows against a prior partly built
    # from other LOW-confidence rows)
    reliable = scoreable[scoreable.minutes_confidence.isin(["MEDIUM", "HIGH"])]
    prior_rate = {}
    for feat in ALL_RAW_COLS:
        prior_rate[feat] = (reliable.groupby("position_group")[feat].sum() /
                             (reliable.groupby("position_group").minutes_for_scoring.sum() / 90.0))

    for feat in ALL_RAW_COLS:
        pr = scoreable.position_group.map(prior_rate[feat]).fillna(0)
        scoreable[f"{feat}_shrunk_per90"] = shrink_rate(
            scoreable[feat].fillna(0), scoreable.minutes_for_scoring, pr)

    # leakage-safe expanding normalization + descriptive full-sample normalization, per feature
    for feat in ALL_RAW_COLS:
        z, basis = expanding_robust_zscore(
            scoreable, f"{feat}_shrunk_per90", "position_group", "match_datetime_utc")
        scoreable[f"{feat}_z_expanding"] = z
        scoreable[f"{feat}_z_basis"] = basis
        scoreable[f"{feat}_z_descriptive"] = descriptive_robust_zscore(
            scoreable, f"{feat}_shrunk_per90", "position_group")

    # --- Task 7: candidate scores ---
    def row_features(row, feat_dict):
        return feat_dict.get(row.position_group, [])

    def score_a(row, use_col_suffix):
        pos_feats = row_features(row, POSITIVE_FEATURES)
        neg_feats = row_features(row, NEGATIVE_FEATURES)
        if not pos_feats:
            return np.nan
        pos_vals = [row[f"{f}{use_col_suffix}"] for f in pos_feats]
        neg_vals = [row[f"{f}{use_col_suffix}"] for f in neg_feats] if neg_feats else []
        pos_mean = np.nanmean(pos_vals)
        neg_mean = np.nanmean(neg_vals) if neg_vals else 0.0
        return pos_mean - 0.5 * neg_mean

    def score_b(row, use_col_suffix):
        pos_feats = row_features(row, POSITIVE_FEATURES)
        neg_feats = row_features(row, NEGATIVE_FEATURES)
        if not pos_feats:
            return np.nan
        cats = {}
        for f in pos_feats:
            cat = FEATURE_CATEGORY.get(f, "OTHER")
            cats.setdefault(cat, []).append(row[f"{f}{use_col_suffix}"])
        cat_means = [np.nanmean(v) for v in cats.values()]
        pos_component = np.nanmean(cat_means)
        neg_mean = np.nanmean([row[f"{f}{use_col_suffix}"] for f in neg_feats]) if neg_feats else 0.0
        return pos_component - 0.5 * neg_mean

    scoreable["candidate_score_A"] = scoreable.apply(lambda r: score_a(r, "_z_expanding"), axis=1)
    scoreable["candidate_score_B"] = scoreable.apply(lambda r: score_b(r, "_z_expanding"), axis=1)
    scoreable["candidate_score_A_descriptive"] = scoreable.apply(lambda r: score_a(r, "_z_descriptive"), axis=1)
    scoreable["candidate_score_B_descriptive"] = scoreable.apply(lambda r: score_b(r, "_z_descriptive"), axis=1)

    # Score C: PCA within position group, on descriptive z-scores of CORE POSITIVE features only.
    # Unsupervised (no future-performance target used, so it does not leak Stage 5 into Stage 3),
    # but fit on the full-sample descriptive distribution -- NOT chronologically leakage-safe, and
    # therefore explicitly exploratory/diagnostic only. See docs/PerformanceScoreCandidates.md.
    def first_principal_component(X: np.ndarray) -> np.ndarray:
        """Plain-numpy PCA (no sklearn dependency): center, eigendecompose the covariance matrix,
        project onto the top eigenvector, sign-fixed so higher = more positive contribution."""
        Xc = X - X.mean(axis=0, keepdims=True)
        cov = np.cov(Xc, rowvar=False)
        eigvals, eigvecs = np.linalg.eigh(cov)
        top = eigvecs[:, np.argmax(eigvals)]
        if top.sum() < 0:
            top = -top
        return Xc @ top

    scoreable["candidate_score_C"] = np.nan
    for group, feats in POSITIVE_FEATURES.items():
        mask = scoreable.position_group == group
        cols = [f"{f}_z_descriptive" for f in feats]
        X = scoreable.loc[mask, cols].fillna(0).to_numpy()
        if len(X) < 10:
            continue
        pc1 = first_principal_component(X)
        scoreable.loc[mask, "candidate_score_C"] = pc1

    # --- Task 8: presentation scale (docs/PerformanceScoreScale.md) applied to the selected score ---
    ref = scoreable.candidate_score_B.dropna()
    p50, p_lo, p_hi = ref.quantile([0.50, 0.02, 0.98])
    scale = 25.0 / max((p_hi - p50), (p50 - p_lo), 0.1)

    def to_100_scale(x):
        if pd.isna(x):
            return np.nan
        return float(np.clip(50 + (x - p50) * scale, 0, 100))

    scoreable["final_stage3_score_candidate"] = scoreable.candidate_score_B.apply(to_100_scale)

    # --- assemble output: `df` already carries position_group/source/eligibility for EVERY row
    # (including excluded ones -- computed before the `scoreable` filter, so nothing is silently
    # dropped); only the score columns themselves need to be merged in from `scoreable`. ---
    score_only_cols = [
        "candidate_score_A", "candidate_score_B", "candidate_score_C",
        "candidate_score_A_descriptive", "candidate_score_B_descriptive",
        "final_stage3_score_candidate",
    ]
    out = df.merge(
        scoreable[["player_id", "match_id"] + score_only_cols],
        on=["player_id", "match_id"], how="left",
    )

    # also carry category scores (Task 9: "category scores") for the descriptive expanding-z path
    for cat in ["ATTACKING", "CREATION", "POSSESSION", "DEFENDING", "GOALKEEPING"]:
        cat_feats = [f for f, c in FEATURE_CATEGORY.items() if c == cat]
        present = [f"{f}_z_expanding" for f in cat_feats if f"{f}_z_expanding" in scoreable.columns]
        if present:
            scoreable[f"category_score_{cat}"] = scoreable[present].mean(axis=1)
    cat_cols = [c for c in scoreable.columns if c.startswith("category_score_")]
    out = out.merge(scoreable[["player_id", "match_id"] + cat_cols], on=["player_id", "match_id"], how="left")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "player_match_performance.parquet"
    out.to_parquet(out_path)

    print(f"Total rows: {len(out)}")
    print(f"Score-eligible: {out.score_eligible.sum()} ({out.score_eligible.mean()*100:.1f}%)")
    print(f"Excluded (did_not_play): {(out.exclusion_reason=='did_not_play').sum()}")
    print(f"Excluded (no_stats_row): {(out.exclusion_reason=='no_stats_row').sum()}")
    print(out.position_group.value_counts(dropna=False))
    print(out.minutes_confidence.value_counts(dropna=False))
    print(f"Wrote {out_path}")

    # keep the intermediate scoreable frame available for downstream QC scripts
    scoreable.to_parquet(PROCESSED / "player_match_performance_scoreable_detail.parquet")


if __name__ == "__main__":
    main()
