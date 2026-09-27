# Data access and schema

No row-level data is included. The study used an internal SoccerSolver PostgreSQL export, and no
redistribution licence or public download URL was present in the research project. Publication is
blocked until the data owner confirms a lawful access and redistribution route.

The pipeline expects raw Parquet tables under `data/processed/raw/` produced by
`src/data/build_raw_cache.py`: competitions, seasons, matches, match teams, players, player
appearances, player-match statistics, minutes, positions, and scoped total statistics. Identifiers,
timestamps, position labels, minutes, starting status, team/opponent identifiers, and the 29 match
features listed in `docs/PerformanceFeatureSelection.md` are required.

If authorized to use the original PostgreSQL dump, set `SOCCER_DATA_SQL` to its local path. Do not
commit the dump or generated row-level Parquet files. The `.gitignore` excludes both.

The CSV files in `results/tables/` are aggregate research outputs and contain no names or direct
identifiers. They permit verification of reported claims, but not full recomputation from source.

