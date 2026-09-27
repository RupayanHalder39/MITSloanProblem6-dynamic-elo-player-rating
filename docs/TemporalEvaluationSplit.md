# Temporal Evaluation Split

## Verified season coverage (before deciding the split)

| Season ID | Label | Date range | Scored rows | Unique players |
|---|---|---|---|---|
| 188987 | 2023/24 | 2023-08-04 → 2024-05-26 | 16,939 | 706 |
| 189951 | 2024/25 | 2024-08-09 → 2025-05-24 | 16,924 | 737 |
| 191644 | 2025/26 (truncated — data ends mid-season) | 2025-08-08 → 2026-03-11 | 13,452 | 734 |

All three seasons are complete, well-populated, chronologically non-overlapping blocks — the
brief's own example split (one season each for train/validation/test) is directly supported by the
actual data, not blindly imposed.

## Adopted split

| Split | Season | Rows | Unique players |
|---|---|---|---|
| **Train** | 2023/24 (188987) | 16,939 | 706 |
| **Validation** | 2024/25 (189951) | 16,924 | 737 |
| **Test** | 2025/26 (191644) | 13,452 | 734 |

The dynamic rating itself is built as **one continuous chronological pass across all 3 seasons**
(Stage 4's own design — ratings carry across season boundaries deliberately, per
`docs/TeamOpponentStrengthMethod.md`'s sanity check #6 applied at player level too). The split
label only determines which rows are used for **calibration fitting** (train only) and **evaluation
reporting** (validation for tuning-adjacent checks, test for the primary reported numbers) — it does
not reset or partition the rating engine itself.

## Player-overlap audit (Task 8)

| Group | Count |
|---|---|
| Train-only players | 243 |
| Train ∩ Validation | 384 |
| Validation ∩ Test | 389 |
| **Test players unseen in train** | **434 / 734 (59.1%)** |
| Test players unseen in train OR validation (fully cold-start entering test) | 266 / 734 (36.2%) |
| Players in all 3 splits | 221 |

A majority of test-season players were not observed in the training season at all — expected, given
Championship promotion/relegation squad churn and normal transfer activity across 2 full seasons.
This is evaluated directly (Task 8's "known vs. cold-start" comparison):

| Group | n | Variant C MAE | Variant C Spearman | last5 MAE | last5 Spearman |
|---|---|---|---|---|---|
| Known (seen in train or validation) | 8,237 | 4.323 | 0.544 | 4.536 | 0.476 |
| Unseen before test (cold-start) | 3,116 | 4.165 | 0.495 | 4.217 | 0.474 |

Full table: `outputs/tables/stage5_known_vs_coldstart_comparison.csv`. **Variant C's advantage over
last5 is larger for known players** (MAE gap 0.213) **than for cold-start players** (MAE gap
0.052) — consistent with the mechanism: a dynamic rating needs accumulated history to differentiate
itself from a simple trailing average, and cold-start players' ratings sit closer to the flat
1500 prior, closer to what a simple baseline effectively assumes too.
