# Methodology

The cohort comprises 1,554 English Championship matches across 2023/24–2025/26, 1,647 players,
62,001 canonical appearances, and 47,315 scoreable player-match observations.

Each eligible appearance is converted to a position-aware 0–100 performance score. Twenty-nine
selected features cover possession, defending, attacking, creation, and goalkeeping. Features are
normalized using only chronologically available history; short appearances are shrunk toward 50;
features are averaged within football categories before categories are combined. Full feature and
position rules are in the adjacent design documents.

The rating is centered on 1500 and updated after each match. For Variant A, expected performance is
derived from the player's pre-match rating, and a fixed update rate moves the rating according to
the difference between observed and expected performance. Variant A deliberately has no opponent
strength adjustment and no history-aware decay.

After match T, each method predicts the mean performance score in that player's next three
scoreable appearances (T+1 through T+3). Baselines are last 1, last 3, last 5, season-to-date,
career-to-date, and a position prior. Evaluation uses a common cohort and MAE; lower MAE is better.
Robustness analyses cover horizons 1, 2, 3, 5, and 7; rolling seasons; history buckets; position;
rating deciles; opponent-strength settings; and 2,000 player-clustered bootstrap resamples with
seed 42.

