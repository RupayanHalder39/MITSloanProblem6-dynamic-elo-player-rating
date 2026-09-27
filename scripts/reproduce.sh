#!/usr/bin/env bash
set -euo pipefail

python src/data/build_raw_cache.py
python src/analysis/build_player_match_foundation.py
python src/features/build_performance_feature_inventory.py
python src/features/build_player_match_performance.py
python src/analysis/build_team_elo.py
python src/models/build_dynamic_player_rating.py
python src/features/build_future_performance_targets.py
python src/features/build_predictive_baselines.py
python src/models/calibrate_rating_predictions.py
python src/analysis/evaluate_dynamic_rating.py
python src/analysis/bootstrap_predictive_comparisons.py
python src/features/build_future_horizon_targets.py
python src/analysis/run_stage6_experiments.py
python src/analysis/run_stage6_sensitivity.py
python src/analysis/run_stage6_blocks_12to23.py
python src/analysis/plot_stage7_main_figures.py
python scripts/verify_release.py

