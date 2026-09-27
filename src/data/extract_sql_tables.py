r"""
Generic extractor for tables inside a user-supplied PostgreSQL dump.

The dump is a plain-text PostgreSQL dump (schema `sports`) using CRLF line endings and standard
`COPY ... FROM stdin;` blocks terminated by a lone `\.` line. At 6.2GB it must never be loaded fully
into memory -- this module locates each table's COPY block by streaming `grep -n` for the exact
`COPY sports.<table>` line, then streams just that line range with `sed`, stripping the trailing
`\r` before parsing with pandas. This file only READS from Data/; every write target is supplied by
the caller and must live under this project's own directory (enforced by build_raw_cache.py).

Usage:
    from extract_sql_tables import extract_table
    df = extract_table("matches", columns=[...])
"""
from __future__ import annotations

import subprocess
import os
from pathlib import Path

import pandas as pd

DATA_SQL = os.environ.get("SOCCER_DATA_SQL", "")


def _copy_block_line_range(table: str, sql_path: str = DATA_SQL) -> tuple[int, int]:
    """Find the [start, end) line range of a table's COPY ... FROM stdin; data block
    (exclusive of the COPY line itself and the closing \\. line) by locating the COPY
    line for `table` and the next COPY line (or end of file) after it."""
    if not sql_path:
        raise RuntimeError("Set SOCCER_DATA_SQL to an authorized local PostgreSQL dump.")
    grep = subprocess.run(
        ["grep", "-na", "^COPY sports\\.", sql_path],
        capture_output=True, text=True, check=True,
    )
    lines = grep.stdout.splitlines()
    copy_lines = []
    for entry in lines:
        lineno_str, content = entry.split(":", 1)
        lineno = int(lineno_str)
        name = content.split(" ", 2)[1].removeprefix("sports.")
        copy_lines.append((lineno, name))
    copy_lines.sort()

    start = None
    end = None
    for i, (lineno, name) in enumerate(copy_lines):
        if name == table:
            start = lineno + 1  # first data row, right after the COPY line
            end = copy_lines[i + 1][0] if i + 1 < len(copy_lines) else None
            break
    if start is None:
        raise ValueError(f"Table sports.{table} not found in {sql_path}")
    if end is None:
        # last table in the file -- use wc -l to bound the range
        wc = subprocess.run(["wc", "-l", sql_path], capture_output=True, text=True, check=True)
        end = int(wc.stdout.strip().split()[0]) + 1
    return start, end  # [start, end) ; end line is the next COPY line or EOF+1


def extract_table(table: str, columns: list[str], sql_path: str = DATA_SQL) -> pd.DataFrame:
    """Stream-extract one table's COPY block into a DataFrame. Never loads the full 6.2GB
    file -- only the target table's own line range is piped through sed."""
    start, end = _copy_block_line_range(table, sql_path)
    # end-1 excludes the closing "\." terminator line
    proc = subprocess.Popen(
        ["sed", "-n", f"{start},{end - 1}p", sql_path],
        stdout=subprocess.PIPE,
    )
    # tr -d '\r' strips the dump's CRLF line endings before pandas sees the stream
    tr = subprocess.Popen(["tr", "-d", "\r"], stdin=proc.stdout, stdout=subprocess.PIPE)
    proc.stdout.close()
    df = pd.read_csv(
        tr.stdout, sep="\t", header=None, names=columns,
        na_values=["\\N"], dtype=str, engine="c",
    )
    tr.wait()
    # Defensive: drop a stray literal "\." row if the terminator line was ever included
    # (can happen if a table is the very last one in the file and the range computation
    # is off by one against an unexpected trailing blank line).
    first_col = columns[0]
    df = df[df[first_col] != "\\."].reset_index(drop=True)
    return df


def save_table(table: str, columns: list[str], out_path: Path, sql_path: str = DATA_SQL) -> Path:
    """Extract a table and save it as Parquet at out_path (caller-supplied, must be
    inside this project's own data/processed/raw/ directory)."""
    out_path = Path(out_path)
    project_root = Path(__file__).resolve().parents[2]
    try:
        out_path.resolve().relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"Refusing to write outside the project root: {out_path}") from exc
    df = extract_table(table, columns, sql_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path)
    return out_path
