# Public-release handoff

## Outcome

A minimal local release candidate was created and audited. It is **blocked from publication** solely
because data and derived-output redistribution rights have not been established. Nothing was
pushed, no remote repository was created, and no local Git repository was initialized.

**IDENTITY REVIEW REQUIRED BEFORE PUBLICATION:**
The README identifies Rupayan Halder and contains his photograph, professional affiliations,
GitHub profile, LinkedIn profile, and email. Confirm whether the MIT Sloan-linked repository may
reveal author identity during the relevant review stage before making the repository public.

The README researcher section uses the public asset `assets/RupayanHalder.jpeg` and lists the
confirmed roles separately: PhD Student at Jadavpur University, Football AI Researcher, Assistant
Professor at UEM Kolkata, Research Collaborator at SoccerSolver, and Former Software Engineer —
Platform Engineering at Session AI. The collaboration section uses
`assets/SoccerSolverLogo.png` and contains only the approved collaboration statement. Both assets
were copied as physical files (not symbolic links) from the explicitly selected read-only source
files `RupayanHalder.jpeg` and `SoccerSolverLogo.png`. The photograph had no EXIF, GPS, XMP, camera,
serial-number, device, or original-filesystem metadata, so no re-encoding or metadata cleaning was
required. A standalone copy of the complete repository was tested in a temporary directory: both
relative README image references resolved, both assets existed as regular files, the aggregate
result verification passed, and no absolute user-home path was required. **Portability validation:
PASS.**

## Inspected and copied

The full private tree was recursively inventoried, including code, data, documents, final paper,
tables, figures, reports, hidden/cached files, and possible Git metadata. The scientific pipeline
was traced from SQL extraction through player-match foundation, 29-feature performance scoring,
chronological ratings, baselines, next-three-match targets, calibration, MAE evaluation, horizon/
history/position/opponent analyses, rating ranking, goalkeeper diagnosis, clustered bootstrap, and
final plots.

The public package contains sanitized Python source for those stages, ten aggregate evidence tables,
two final figures, seven focused design documents plus a consolidated methodology, and release
metadata/testing files. All copied code is repository-relative except the authorized source dump,
which is supplied through `SOCCER_DATA_SQL`.

## Exclusions and licensing decision

All row-level Parquet files, the source SQL dump, player summaries, case studies, trajectories,
private planning/handoff files, draft-review materials, unrelated research, redundant reports,
duplicate figures, caches, and machine files were excluded. The private project does not contain a
dataset licence or public acquisition URL. Consequently, none of the data is approved for public
redistribution. SoccerSolver/data-provider written review is required, including permission for
the aggregate tables and figures retained here.

## Structure and workflow

- `src/`: data preparation, scoring, rating, baseline, evaluation, experiments, plots, audits.
- `data/README.md`: missing-data decision, required inputs, and access notes.
- `docs/`: consolidated methodology and supporting design decisions.
- `results/tables/`: aggregate frozen evidence only.
- `results/figures/`: the two abstract figures.
- `scripts/reproduce.sh`: ordered full workflow when authorized data are available.
- `scripts/verify_release.py`: lightweight verification of frozen headline MAEs.

Create a Python 3.12 virtual environment, install `requirements.txt`, and run
`python scripts/verify_release.py`. For an authorized full run, set `SOCCER_DATA_SQL` and run
`bash scripts/reproduce.sh`.

## Validation and reproduced numbers

The aggregate verification passed for Variant A 4.231, last-5 4.448, season-to-date 4.395, and
career-to-date 4.349. Static compilation and public-tree scans were also run. Full raw-to-result
reproduction was not possible without redistributing/using the unlicensed source dataset, so not all
abstract numbers have been independently regenerated in the clean package. The frozen evidence
tables also match the abstract bootstrap interval (-0.217, [-0.286, -0.149]), seasonal ranking gaps
(+7.18/+7.66/+8.18), horizon finding, approximately-15-match finding, opponent result, and
goalkeeper limitation.

## Manual actions before publication

1. Obtain written rights-holder approval for data access and public release of aggregates/figures.
2. Confirm the complete author list, author order, acknowledgements, and copyright holder; Rupayan
   Halder is confirmed, while any additional authors remain unresolved.
3. Confirm MIT is the intended software licence and review trademark/provenance wording.
4. Decide whether to release an approved minimal dataset or publish controlled-access instructions.
5. Run the entire pipeline in a new clean environment once data access is resolved and compare every
   row in `final_claim_number_audit.csv`.
6. Have a human inspect both figures and all public files, then repeat the release audit before Git.

## Final README visual QA

Final QA rendered `README.md` locally with a GitHub-like CommonMark/GFM renderer and inspected
screenshots across the complete document at desktop (1280 px) and narrow/mobile-like (390 px)
widths. The top, dataset/methodology, findings and both figures, reproduction/limitations,
researcher, collaboration, citation, and licence areas were visually inspected. All four images
loaded (zero broken resources), spacing and hierarchy remained coherent, and no content overflowed.

- README CONTENT QA: **PASS**
- README VISUAL QA: **PASS**
- RESEARCHER PHOTO: **PASS** — correct aspect ratio, undistorted, professional, and appropriately
  modest at 150 px; no excessive padding.
- SOCCERSOLVER LOGO: **PASS** — sharp, readable, correctly proportioned, and restrained at 180 px;
  the transparent logo is understandable on the normal GitHub background. Dark-mode contrast
  should receive a final human check in GitHub itself because the supplied green artwork has no
  alternate dark-mode asset.
- RESEARCH FIGURE 1: **PASS** — correct order, crisp and legible on desktop, responsive on narrow
  view without overflow; detailed labels require normal zoom on a phone.
- RESEARCH FIGURE 2: **PASS** — correct order, crisp and legible on desktop, responsive on narrow
  view without overflow; detailed labels require normal zoom on a phone.
- MOBILE/NARROW VIEW: **PASS** — 390 px render inspected; headings, text, code, and images remain in
  bounds with no broken positioning.
- PORTABILITY: **PASS** — no absolute user-home paths, `file://` links, escaping `../` references,
  external symlinks, or private runtime locations were found.
- PRIVACY/METADATA: **PASS** — the public photograph contains no EXIF, XMP, GPS, device-model, or
  camera/body-serial metadata.
- SECRET SCAN: **PASS** — no credential patterns, environment files, keys, database dumps, or
  unexpected sensitive files were found.

The README remained primarily an academic research repository; the researcher block is modest and
the SoccerSolver block reads as an acknowledgement rather than advertising. No scientific or
stylistic README change was made during this final QA. The existing identity-review warning and
data-licensing publication blocker remain active. Nothing was pushed to GitHub.

## Final local pre-publication audit

The confirmed Connect links were added to the researcher section: GitHub
`https://github.com/RupayanHalder39`, LinkedIn
`https://www.linkedin.com/in/rupayan-halder-962922209/`, and the authorized public email link
`mailto:rupayanhalder313239@gmail.com`. GitHub returned HTTP 200. LinkedIn returned its automated-
access status 999, so the exact authorized URL and encoding were verified but automated page
resolution could not be conclusively validated. The email link is correctly encoded.

The current official SSAC27 Research Paper Competition page requires an open-source repository and
states that final reviews occur without knowledge of author names. It does not explicitly clarify
whether the linked repository must remain anonymous during each review stage. The profile was not
removed; the identity decision therefore remains **NEEDS CONFIRMATION** before publication.

One unresolved scientific inconsistency was found and not edited around: `README.md` and
`results/tables/final_claim_number_audit.csv` state goalkeeper Variant A test R² = -0.122, while
the cited included source table `results/tables/exp_position.csv` and the goalkeeper diagnosis table
report Variant A test R² = -0.068. An authoritative scientific decision is required before push.
Until resolved, **SCIENTIFIC README QA: FAIL** and **GITHUB CONTENT READY: NO**.

No row-level data, Parquet, DuckDB, SQL dump, database, archive, notebook, cache, or temporary output
is present. The ten CSVs are aggregate result tables without player-level rows or direct identifiers,
but permission to publish derived aggregates and figures has not been established; **DATA LICENCE:
BLOCKED**. Full raw-to-result reproduction also remains blocked by authorized data access.

The directory is not a Git repository. Consequently no file is tracked, staged, or currently queued
for commit. If Git were initialized and all non-ignored files added, every regular file in the
audited repository inventory would be prospective content; this includes source code, focused docs,
ten aggregate CSVs, two research figures, two image assets, and the release metadata. No suspicious
or unexpected file was found. Nothing was committed, pushed, uploaded, or published.
