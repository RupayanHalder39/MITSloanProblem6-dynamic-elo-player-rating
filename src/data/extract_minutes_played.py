"""
Stage 2 only needs `minutes_played` out of sports.player_match_stats_total's 100+ columns (the
full table is deliberately NOT pulled into the raw cache in this stage -- see
docs/PlayerMatchFoundationDataDictionary.md -- to avoid an expensive, mostly-unused extraction
before Stage 3 defines which performance columns the rating actually needs).

player_id, match_id, minutes_played are columns 1-3 of the table (verified against the table's own
CREATE TABLE statement), so this uses `cut -f1,2,3` on the table's COPY block instead of a full
100-column pandas parse -- much faster for a 4.87M-row table.
"""
from pathlib import Path
import subprocess

import pandas as pd

from extract_sql_tables import DATA_SQL, _copy_block_line_range

OUT = (
    Path(__file__).resolve().parents[2]
    / "data" / "processed" / "raw" / "player_match_stats_minutes.parquet"
)


def main():
    start, end = _copy_block_line_range("player_match_stats_total")
    sed = subprocess.Popen(["sed", "-n", f"{start},{end - 1}p", DATA_SQL], stdout=subprocess.PIPE)
    tr = subprocess.Popen(["tr", "-d", "\r"], stdin=sed.stdout, stdout=subprocess.PIPE)
    sed.stdout.close()
    cut = subprocess.Popen(["cut", "-f1,2,3"], stdin=tr.stdout, stdout=subprocess.PIPE)
    tr.stdout.close()

    df = pd.read_csv(
        cut.stdout, sep="\t", header=None,
        names=["player_id", "match_id", "minutes_played"], dtype=str,
    )
    cut.wait()
    df = df[df.player_id != "\\."].reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT)
    print(f"wrote {OUT} ({len(df)} rows)")


if __name__ == "__main__":
    main()
