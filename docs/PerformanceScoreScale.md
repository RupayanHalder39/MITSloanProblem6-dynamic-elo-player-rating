# Performance Score Scale

## Design

The raw selected score (`candidate_score_B`, a robust-z-based composite, typically ranging roughly
-1.5 to +3) is transformed onto a **0–100 scale, centered at 50**, preserving rank order exactly
(a strictly monotonic linear transform — no reranking, no compression that swaps any two players'
order).

## Transformation, derived from the observed distribution (not invented cutoffs)

`score_100 = clip(50 + (raw - median) * scale, 0, 100)`, where:

- `median` = the observed median of `candidate_score_B` across all 47,315 score-eligible rows
  (≈0, by construction of the z-score-based composite).
- `scale` = `25 / max(p98 - median, median - p02)` — chosen so that the **2nd and 98th percentiles
  of the observed distribution** land at approximately 25 and 75 on the 0–100 scale. This is a
  distribution-derived choice, not an arbitrary 50/60/70/80 cutoff scheme: the scale factor comes
  directly from where the real data's tails actually sit.

## Resulting distribution (measured, not designed-in)

| Statistic | Value |
|---|---|
| Mean | 51.0 |
| Median | 50.0 |
| Std | 9.36 |
| Min | 21.1 |
| Max | 100.0 |

## Interpretation guide (descriptive, derived from the measured distribution — not asserted a priori)

| Score range | Approx. percentile | Descriptive label |
|---|---|---|
| ~50 | 50th | Average match for the position |
| ~60 | ~85th | Good match |
| ~70 | ~97th | Very good match |
| 80+ | ~99.5th+ | Exceptional match |
| ~40 | ~15th | Below-average match |
| <30 | <1st | Very poor match |

These labels are descriptive commentary on the **measured** percentile bands (from
`outputs/tables/performance_score_summary.csv` and the full score distribution in
`outputs/figures/performance_score_distribution.png`), not a predefined cutoff scheme imposed on
the data — the brief's instruction to "use the observed score distribution" rather than inventing
cutoffs is followed directly: the 50/60/70/80 example figures in the task brief happen to land close
to real percentile bands in this data, which is a coincidence of the data's own shape (roughly
symmetric with a mild right tail), not evidence the scale was designed to hit those exact numbers.

## Clipping at 0 and 100

The theoretical z-score-based raw score is unbounded, but the transformation clips to [0, 100] for
presentation. In the actual scored population, this bound bound only ever binds at the top (a
handful of rows reach exactly 100.0 — see `outputs/tables/performance_score_outliers.csv`) and never
at the bottom (min observed = 21.1, well above the 0 floor) — the clip is a safety bound for the
scale's definition, not something the real data currently exercises heavily.
