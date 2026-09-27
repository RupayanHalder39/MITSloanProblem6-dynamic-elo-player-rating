from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results" / "tables" / "stage5_primary_method_comparison.csv"
EXPECTED = {"variant_A": 4.231, "last5": 4.448, "season_to_date": 4.395, "career_to_date": 4.349}

with TABLE.open(newline="", encoding="utf-8") as handle:
    df = {row["method"]: row for row in csv.DictReader(handle)}
for method, expected in EXPECTED.items():
    actual = float(df[method]["MAE"])
    assert abs(actual - expected) < 1e-9, (method, actual, expected)
print("PASS: published aggregate headline MAEs match the frozen result table.")
