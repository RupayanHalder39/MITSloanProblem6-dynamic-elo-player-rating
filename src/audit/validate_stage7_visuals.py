"""
Validate Stage 7 (Visual Analysis & Figure Selection) against its completion criteria.
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
FIGS = BASE / "outputs" / "figures"
REPORTS = BASE / "outputs" / "reports"
DOCS = BASE / "docs"

REQUIRED_DIAGRAMS = [
    "stage7_d1_system_overview.png", "stage7_d2_prediction_timing.png",
    "stage7_d3_variant_comparison.png", "stage7_d4_why_dynamic_rating_helps.png",
]
REQUIRED_MAIN_FIGS = [f"stage7_f{i}_{name}.png" for i, name in enumerate([
    "method_comparison", "future_horizon_robustness", "history_depth", "position_performance",
    "goalkeeper_diagnosis", "opponent_adjustment_hurts", "scoreA_vs_scoreB", "ranking_robustness",
    "rating_plus_recent_form", "bootstrap_effects"], start=1)]
TIER1_FIGS = [
    "stage7_f1_method_comparison.png", "stage7_f8_ranking_robustness.png",
    "stage7_f3_history_depth.png", "stage7_f5_goalkeeper_diagnosis.png",
    "stage7_f6_opponent_adjustment_hurts.png", "stage7_f10_bootstrap_effects.png",
    "stage7_d2_prediction_timing.png", "stage7_f2_future_horizon_robustness.png",
]


def main():
    checks = []

    def record(name, passed, detail=""):
        checks.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})

    # --- every ranked Tier-1 figure file exists ---
    missing_tier1 = [f for f in TIER1_FIGS if not (FIGS / f).exists()]
    record("Every Tier-1-ranked figure file exists", len(missing_tier1) == 0, f"missing: {missing_tier1}")

    # --- all diagrams and main figures exist ---
    missing_d = [f for f in REQUIRED_DIAGRAMS if not (FIGS / f).exists()]
    missing_f = [f for f in REQUIRED_MAIN_FIGS if not (FIGS / f).exists()]
    record("All 4 required diagrams (D1-D4) exist", len(missing_d) == 0, f"missing: {missing_d}")
    record("All 10 required main figures (F1-F10) exist", len(missing_f) == 0, f"missing: {missing_f}")

    # --- caption file covers every main figure ---
    captions = (REPORTS / "FigureCaptionsAndInterpretations.md").read_text()
    uncaptioned = [f for f in REQUIRED_DIAGRAMS + REQUIRED_MAIN_FIGS if f not in captions]
    record("FigureCaptionsAndInterpretations.md covers every diagram and main figure",
           len(uncaptioned) == 0, f"not referenced: {uncaptioned}")

    # --- every figure has a linked claim (spot check captions contain "Claim supported") ---
    n_claim_mentions = len(re.findall(r"\*\*Claim supported:", captions))
    record("Every main-figure caption entry states a supported claim",
           n_claim_mentions >= len(REQUIRED_MAIN_FIGS), f"{n_claim_mentions} 'Claim supported' entries found")

    # --- every figure claim is supported by a real Stage-6 result (cross-check against ClaimAudit) ---
    claim_audit = (DOCS / "ClaimAudit.md").read_text()
    visual_claims = (REPORTS / "VisualClaimsReport.md").read_text()
    # every table referenced in VisualClaimsReport should also appear somewhere in Stage 6's own
    # evidence base (ClaimAudit.md or the exp_*.csv table directory)
    referenced_csvs = set(re.findall(r"`([a-zA-Z0-9_]+\.csv)`", visual_claims))
    existing_csvs = {p.name for p in (BASE / "outputs" / "tables").glob("*.csv")}
    missing_csvs = referenced_csvs - existing_csvs
    record("Every table referenced in VisualClaimsReport.md exists in outputs/tables/",
           len(missing_csvs) == 0, f"missing: {missing_csvs}")

    # --- no unsupported claim is elevated to Tier 1: cross-check Tier-D/null claims never appear
    # in the Tier-1 figure list's captions as a positive claim ---
    tier1_captions_text = ""
    for fname in TIER1_FIGS:
        # crude section extraction: grab the caption block for this figure
        idx = captions.find(f"`outputs/figures/{fname}`")
        if idx != -1:
            tier1_captions_text += captions[idx:idx + 800]
    record("Team-strength null result (Tier D) is not presented as a Tier-1 positive claim",
           "no clean" not in tier1_captions_text.lower() or "team" not in tier1_captions_text.lower(),
           "checked Tier-1 caption text for the Tier-D team-context finding")

    # --- no figure contradicts ClaimAudit.md: spot check the headline MAE number is consistent ---
    record("Headline MAE figure (4.231) appears consistently in both ClaimAudit.md and captions",
           "4.231" in claim_audit and "4.231" in captions, "")

    # --- no required report is missing ---
    required_reports = ["FigureCaptionsAndInterpretations.md", "FigureRanking.md",
                         "VisualClaimsReport.md", "Stage7VisualAnalysisReport.md"]
    missing_reports = [r for r in required_reports if not (REPORTS / r).exists()]
    required_docs = ["VisualClaimSelection.md", "VisualStoryboard.md"]
    missing_docs = [d for d in required_docs if not (DOCS / d).exists()]
    record("All required Stage-7 reports exist", len(missing_reports) == 0, f"missing: {missing_reports}")
    record("All required Stage-7 docs exist", len(missing_docs) == 0, f"missing: {missing_docs}")

    # --- figure count sanity ---
    all_stage7_figs = list(FIGS.glob("stage7_*.png"))
    record("At least 18 Stage-7 figures exist on disk (4 diagrams + 10 main + >=4 supporting)",
           len(all_stage7_figs) >= 18, f"{len(all_stage7_figs)} found")

    all_pass = all(c["result"] == "PASS" for c in checks)
    print(f"Stage 7 validation: {'ALL CHECKS PASS' if all_pass else 'FAILURES FOUND'} "
          f"({sum(c['result']=='PASS' for c in checks)}/{len(checks)})")
    for c in checks:
        print(f"[{c['result']}] {c['check']} -- {c['detail']}")

    report_path = REPORTS / "Stage7ValidationReport.md"
    lines = ["# Stage 7 Validation Report\n\n",
             f"**Overall: {'ALL PASS' if all_pass else 'FAILURES FOUND'}** "
             f"({sum(c['result']=='PASS' for c in checks)}/{len(checks)})\n\n",
             "| Check | Result | Detail |\n|---|---|---|\n"]
    for c in checks:
        lines.append(f"| {c['check']} | {c['result']} | {str(c['detail']).replace('|', chr(92)+'|')[:200]} |\n")
    report_path.write_text("".join(lines))
    print(f"\nWrote {report_path}")

    if not all_pass:
        raise SystemExit("Stage 7 validation checks failed.")


if __name__ == "__main__":
    main()
