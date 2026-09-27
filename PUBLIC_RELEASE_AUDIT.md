# Public Release Audit

## Decision

**BLOCKED FOR PUBLICATION.** A clean local package has been prepared, but the full result pipeline
requires an internal SoccerSolver SQL export. No licence, contract, public source URL, or written
redistribution permission was found in the private project. Row-level data must remain excluded
until the rights holder gives written authorization and confirms attribution/access terms.

## Scope inspected

The complete 207 MB private project was inventoried recursively: 50+ Python modules, all processed
and raw Parquet files, methodology and audit documents, final paper files, aggregate tables,
figures, reports, caches, and repository metadata. The source folder had no `.git` directory, so
there was no Git history, configuration, remote, or commit metadata to migrate.

## Safe to release, subject to final human approval

- Sanitized analysis, feature, rating, evaluation, validation, and plotting source code.
- Aggregate CSV result tables without player names or direct identifiers.
- The two final abstract figures generated from aggregate results.
- Methodology/design documentation without internal paths or correspondence.
- Environment, citation, licence, ignore, verification, and reproduction files created here.
- Rupayan Halder's profile photograph and the SoccerSolver logo, included at the user's explicit
  direction; both require final identity/mark-use review before publication.

## Must remain private / deliberately excluded

- All raw and processed Parquet files and the original 6.2 GB SQL export: rights unverified;
  row-level player, match, and provider data; necessary for full recomputation.
- Player-level summaries, case studies, error cases, and selected trajectories: unnecessary and
  potentially identifying.
- Private handoff, planning, reviewer/rules notes, draft variants, internal readiness documents,
  and unrelated research references.
- Generated reports/PDFs beyond the two selected figures, duplicate figures, caches, `.DS_Store`,
  and obsolete/intermediate outputs.
- Original `.git` history: none existed; no `.git` data was copied.

## Data and licensing

The dataset appears to be an internal SoccerSolver export. The project supplies neither an official
public download link nor a licence. Therefore no row-level dataset is approved for redistribution,
and no claim is made that the software licence covers the data. There is currently no verified
original-source link to provide. Required resolution: SoccerSolver/data-provider review confirming
(1) ownership, (2) public redistribution or controlled-access terms, (3) attribution, (4) whether
derived aggregates/figures may be published, and (5) any player-data/privacy conditions.

The included MIT licence is for repository software only and contains an authorship placeholder.
It does not license third-party data, names, marks, or provider content.

## Sensitive-material audit

Filename and content scans checked for common credentials, tokens, private keys, connection URLs,
environment files, email-like strings, absolute home paths, and database files. No credential or
secret was found. Three absolute local paths were found in the private extraction module and were
replaced in the public copy by `SOCCER_DATA_SQL` and a repository-relative safety check. The private
project itself was not edited. The public README now intentionally contains confirmed professional
information about Rupayan Halder, a supplied profile photograph, his GitHub and LinkedIn profiles,
and the explicitly authorized public email address `rupayanhalder313239@gmail.com`. References to
SoccerSolver remain only where needed for truthful provenance/collaboration and licensing warnings.

## Reproducibility limitation

Aggregate claims and figure inputs can be verified locally. End-to-end independent reproduction
cannot be claimed until authorized source data are accessible. This is a material blocker, not a
cosmetic limitation. No synthetic or fabricated substitute data were created.

## Publication gates

Before any public release: confirm that author identity may be disclosed during the review stage;
obtain written data/aggregate publication approval; confirm the complete author list and copyright
holder; review the MIT licence choice; review SoccerSolver naming/mark use;
provide a lawful data-access instruction or approved minimal dataset; rerun the full workflow in a
clean environment; and repeat the secret/path/licence audit.

An additional pre-publication scientific blocker was found during final QA: the goalkeeper Variant A
test R² is recorded as -0.122 in the README/final claim audit but as -0.068 in the included source
result tables. This must be resolved against the authoritative frozen analysis before publication;
no number was silently changed during the release audit.
