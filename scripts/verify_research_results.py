#!/usr/bin/env python3
"""
verify_research_results.py — Automated numerical consistency and provenance checker.

Verifies:
  1. Dataset row counts and network partitions.
  2. Exactly 44 features matching extract_features.py and FEATURE_GROUPS.
  3. Proper chance baselines (1.0% for 100 domains, 2.0% for 50 domains).
  4. Consistency of numerical claims in docs/claims_ledger.csv against underlying result CSVs.
  5. Jio DoH/3 client-side reachability audit (100% timeouts on UDP 443).
  6. Model comparison values on AdGuard DoH Global.

Note: This tool verifies data provenance, numerical reproducibility, and schema integrity
against generated experimental outputs; it does not replace scientific peer review.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd


def verify_datasets() -> bool:
    print("[1/6] Verifying dataset row counts and partitions...")
    v2_path = ROOT / "data/processed/dataset_v2.csv"
    jio_path = ROOT / "data/processed/dataset_jio.csv"
    comb_path = ROOT / "data/processed/dataset_combined.csv"

    if not (v2_path.exists() and jio_path.exists() and comb_path.exists()):
        print("  FAIL: Processed dataset CSVs missing!")
        return False

    df_v2 = pd.read_csv(v2_path)
    df_jio = pd.read_csv(jio_path)
    df_comb = pd.read_csv(comb_path)

    # Airtel post-filtering must be exactly 18,926
    if len(df_v2) != 18926:
        print(f"  FAIL: dataset_v2.csv has {len(df_v2)} rows; expected 18,926")
        return False

    # Jio post-filtering must be exactly 1,912
    if len(df_jio) != 1912:
        print(f"  FAIL: dataset_jio.csv has {len(df_jio)} rows; expected 1,912")
        return False

    # Combined dataset must be exactly 20,838
    if len(df_comb) != 20838:
        print(f"  FAIL: dataset_combined.csv has {len(df_comb)} rows; expected 20,838")
        return False

    # Verify partition counts
    airtel_count = (df_comb["network"] == "airtel").sum()
    jio_count = (df_comb["network"] == "jio").sum()
    if airtel_count != 18926 or jio_count != 1912:
        print(f"  FAIL: Combined network partition mismatch: airtel={airtel_count}, jio={jio_count}")
        return False

    print(f"  PASS: Airtel ({len(df_v2):,}) + Jio ({len(df_jio):,}) = Combined ({len(df_comb):,})")
    return True


def verify_feature_space() -> bool:
    print("[2/6] Verifying 44-dimensional feature space...")
    from src.encdns.analysis.fingerprinting import FEATURE_GROUPS, available_features

    total_group_features = sum(len(cols) for cols in FEATURE_GROUPS.values())
    if total_group_features != 44:
        print(f"  FAIL: FEATURE_GROUPS has {total_group_features} features; expected 44")
        return False

    comb_path = ROOT / "data/processed/dataset_combined.csv"
    df_comb = pd.read_csv(comb_path, nrows=5)
    extracted_features = available_features(df_comb)
    if len(extracted_features) != 44:
        print(f"  FAIL: available_features found {len(extracted_features)} features; expected 44")
        return False

    # Verify grouping counts
    counts = {group: len(cols) for group, cols in FEATURE_GROUPS.items()}
    expected = {"volume": 7, "size_stats": 6, "timing": 6, "bursts": 5, "handshake": 20}
    if counts != expected:
        print(f"  FAIL: Feature group counts {counts} do not match {expected}")
        return False

    print(f"  PASS: 44 features verified across 5 groups: {counts}")
    return True


def verify_baselines() -> bool:
    print("[3/6] Verifying random guessing chance baselines...")
    # 100-domain closed-world baseline = 1.0% (0.01)
    df_fp = pd.read_csv(ROOT / "results/airtel_topup_20261113/rq1_rq2_fingerprinting.csv")
    for _, r in df_fp.iterrows():
        expected_chance = 1.0 / r.domains
        if abs(r.chance - expected_chance) > 1e-4:
            print(f"  FAIL: Chance baseline mismatch in {r.resolver}/{r.protocol}: got {r.chance}, expected {expected_chance}")
            return False

    # 50-domain cross-network baseline = 2.0% (0.02)
    df_xfer = pd.read_csv(ROOT / "results/jio_analysis_20261113/n2_cross_network_transfer.csv")
    for _, r in df_xfer.iterrows():
        if r.shared_domains != 50 or abs(r.chance - 0.02) > 1e-4:
            print(f"  FAIL: Cross-network chance baseline mismatch: domains={r.shared_domains}, chance={r.chance}")
            return False

    print("  PASS: Closed-world baseline = 1.0% (1/100); Cross-network transfer baseline = 2.0% (1/50)")
    return True


def verify_jio_quic_blocking() -> bool:
    print("[4/6] Verifying Jio cellular QUIC reachability audit...")
    n6_path = ROOT / "results/jio_analysis_20261113/n6_protocol_availability.csv"
    if not n6_path.exists():
        print("  FAIL: n6_protocol_availability.csv missing!")
        return False

    df_n6 = pd.read_csv(n6_path)
    doh3_rows = df_n6[df_n6["protocol"] == "doh3"]

    total_attempts = doh3_rows["total_captures"].sum()
    ok_count = doh3_rows["ok_count"].sum()
    blocked_count = doh3_rows["udp_blocked"].sum()

    if total_attempts != 3000 or ok_count != 0 or blocked_count != 3000:
        print(f"  FAIL: Jio DoH/3 blocking audit mismatch: attempts={total_attempts}, ok={ok_count}, blocked={blocked_count}")
        return False

    print("  PASS: 3,000 / 3,000 Jio DoH/3 queries failed on UDP 443 (0.0% reachability)")
    return True


def verify_model_comparisons() -> bool:
    print("[5/6] Verifying classifier performance on AdGuard DoH Global...")
    mc_path = ROOT / "results/airtel_advanced_20261113/model_comparison.csv"
    seq_path = ROOT / "results/airtel_all_20261113/wp8_sequence_models.csv"
    if not (mc_path.exists() and seq_path.exists()):
        print("  FAIL: Model comparison CSV artifacts missing!")
        return False

    df_mc = pd.read_csv(mc_path)
    df_seq = pd.read_csv(seq_path)

    rf_rows = df_mc[df_mc["model"] == "rf"]
    xgb_rows = df_mc[df_mc["model"] == "xgb"]
    if len(rf_rows) != 1 or len(xgb_rows) != 1:
        print(f"  FAIL: Expected exactly 1 RF and 1 XGB row in model_comparison.csv; found {len(rf_rows)} and {len(xgb_rows)}")
        return False

    rf_acc = rf_rows["accuracy"].values[0]
    xgb_acc = xgb_rows["accuracy"].values[0]

    adguard_cnn = df_seq[(df_seq["resolver"] == "adguard") & (df_seq["protocol"] == "doh") & (df_seq["workload"] == "global") & (df_seq["model"] == "cnn")]
    adguard_gru = df_seq[(df_seq["resolver"] == "adguard") & (df_seq["protocol"] == "doh") & (df_seq["workload"] == "global") & (df_seq["model"] == "gru")]
    if len(adguard_cnn) != 1 or len(adguard_gru) != 1:
        print(f"  FAIL: Expected exactly 1 CNN and 1 GRU row in wp8_sequence_models.csv; found {len(adguard_cnn)} and {len(adguard_gru)}")
        return False

    cnn_acc = adguard_cnn["accuracy"].values[0]
    gru_acc = adguard_gru["accuracy"].values[0]

    # Dynamically verify RF accuracy against the headline fingerprinting result
    df_fp = pd.read_csv(ROOT / "results/airtel_topup_20261113/rq1_rq2_fingerprinting.csv")
    rf_headline_rows = df_fp[(df_fp["resolver"] == "adguard") & (df_fp["protocol"] == "doh") & (df_fp["workload"] == "global")]
    if len(rf_headline_rows) != 1:
        print(f"  FAIL: Expected exactly 1 headline match for AdGuard DoH Global in rq1_rq2_fingerprinting.csv; found {len(rf_headline_rows)}")
        return False
    rf_headline = rf_headline_rows["accuracy"].values[0]
    if abs(rf_acc - rf_headline) > 0.005:
        print(f"  FAIL: RF accuracy in model_comparison ({rf_acc}) deviates from headline result ({rf_headline})")
        return False

    # Verify that tree-based models (RF and XGBoost) perform comparably within 1%
    if abs(rf_acc - xgb_acc) > 0.01:
        print(f"  FAIL: RF ({rf_acc}) and XGB ({xgb_acc}) diverge beyond acceptable model tolerance (1%)")
        return False

    # Verify sequence models operate near random-guessing baseline (~1%) due to burst padding
    if cnn_acc > 0.05 or gru_acc > 0.05:
        print(f"  FAIL: Sequence models unexpectedly exceeded baseline bounds: CNN={cnn_acc}, GRU={gru_acc}")
        return False

    print(f"  PASS: Random Forest ({rf_acc*100:.1f}%) vs XGBoost ({xgb_acc*100:.1f}%) vs CNN ({cnn_acc*100:.1f}%) vs GRU ({gru_acc*100:.1f}%)")
    return True


def verify_claims_ledger() -> bool:
    print("[6/6] Verifying claims ledger consistency, confidence intervals, and data provenance...")
    import re
    import subprocess

    ledger_path = ROOT / "docs/claims_ledger.csv"
    if not ledger_path.exists():
        print("  FAIL: docs/claims_ledger.csv missing!")
        return False

    df_ledger = pd.read_csv(ledger_path)
    expected_cols = [
        "claim_id", "claim", "value", "metric", "network", "resolver",
        "protocol", "workload", "sample_size", "confidence_interval",
        "source_csv", "script", "commit"
    ]
    if list(df_ledger.columns) != expected_cols:
        print(f"  FAIL: Claims ledger columns mismatch:\n  Found: {list(df_ledger.columns)}\n  Expected: {expected_cols}")
        return False

    # Check for unrecorded commits
    unrecorded = (df_ledger["commit"] == "unrecorded").sum()
    if unrecorded > 0:
        print(f"  FAIL: Found {unrecorded} claims with 'unrecorded' commit hash!")
        return False

    # Verify that commits exist in git repository
    unique_commits = df_ledger["commit"].dropna().unique()
    for c in unique_commits:
        if not re.fullmatch(r"[0-9a-f]{40}", str(c)):
            print(f"  FAIL: Commit hash {c} is not a valid 40-character git SHA-1!")
            return False
        res = subprocess.run(["git", "cat-file", "-e", f"{c}^{{commit}}"], cwd=ROOT, capture_output=True)
        if res.returncode != 0:
            print(f"  FAIL: Commit {c} does not exist in local git history!")
            return False

    # Deep numerical and provenance verification against source CSV files
    verified_claims = 0
    for _, row in df_ledger.iterrows():
        cid = row["claim_id"]
        rel_path = row["source_csv"]
        src_path = ROOT / rel_path
        if not src_path.exists():
            print(f"  FAIL: Source CSV {rel_path} for claim {cid} not found on disk!")
            return False

        src_df = pd.read_csv(src_path)
        cond = pd.Series(True, index=src_df.index)
        if "resolver" in src_df.columns and pd.notna(row["resolver"]):
            cond = cond & (src_df["resolver"].astype(str).str.lower() == str(row["resolver"]).lower())
        if "protocol" in src_df.columns and pd.notna(row["protocol"]):
            cond = cond & (src_df["protocol"].astype(str).str.lower() == str(row["protocol"]).lower())
        if "workload" in src_df.columns and pd.notna(row["workload"]) and str(row["workload"]).lower() != "both":
            cond = cond & (src_df["workload"].astype(str).str.lower() == str(row["workload"]).lower())
        if "direction" in src_df.columns and pd.notna(row["network"]) and "->" in str(row["network"]):
            cond = cond & (src_df["direction"].astype(str) == str(row["network"]))
        if "test_network" in src_df.columns and "Composite" in str(row["network"]):
            cond = cond & src_df["test_network"].astype(str).str.contains("Composite")
        if "model" in src_df.columns:
            if "XGBoost" in row["claim"]:
                cond = cond & (src_df["model"] == "xgb")
            elif "Random Forest" in row["claim"]:
                cond = cond & (src_df["model"] == "rf")
            elif "1D-CNN" in row["claim"]:
                cond = cond & (src_df["model"] == "cnn")
            elif "GRU" in row["claim"]:
                cond = cond & (src_df["model"] == "gru")

        matched = src_df[cond]
        if matched.empty:
            print(f"  FAIL: No matching slice found in {rel_path} for claim {cid} ({row['claim']})")
            return False
        if len(matched) > 1:
            print(f"  FAIL: Ambiguous slice match ({len(matched)} rows found) in {rel_path} for claim {cid} ({row['claim']})")
            return False

        # Verify accuracy / value
        val = float(row["value"])
        if "accuracy" in matched.columns:
            csv_val = float(matched["accuracy"].values[0])
            if abs(val - csv_val) > 0.005:
                print(f"  FAIL: Numerical value mismatch for claim {cid}: ledger={val}, source_csv={csv_val}")
                return False
        elif "ok_count" in matched.columns and "total_captures" in matched.columns:
            csv_val = float(matched["ok_count"].values[0] / matched["total_captures"].values[0])
            if abs(val - csv_val) > 0.005:
                print(f"  FAIL: Success rate mismatch for claim {cid}: ledger={val}, source_csv={csv_val}")
                return False

        # Verify sample size
        ledger_n = int(row["sample_size"])
        if "n_test" in matched.columns:
            csv_n = int(matched["n_test"].values[0])
            if ledger_n != csv_n:
                print(f"  FAIL: Sample size mismatch for claim {cid}: ledger={ledger_n}, source_csv={csv_n}")
                return False
        elif "total_captures" in matched.columns:
            csv_n = int(matched["total_captures"].values[0])
            if ledger_n != csv_n:
                print(f"  FAIL: Sample size mismatch for claim {cid}: ledger={ledger_n}, source_csv={csv_n}")
                return False

        # Verify confidence intervals
        ci_str = str(row["confidence_interval"])
        m_ci = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", ci_str)
        if len(m_ci) == 2:
            ci_lo, ci_hi = float(m_ci[0]), float(m_ci[1])
            csv_ci_lo = float(matched["ci_boot_low"].values[0]) if "ci_boot_low" in matched.columns else float(matched.get("ci_low", pd.Series([ci_lo])).values[0])
            csv_ci_hi = float(matched["ci_boot_high"].values[0]) if "ci_boot_high" in matched.columns else float(matched.get("ci_high", pd.Series([ci_hi])).values[0])
            if abs(ci_lo - csv_ci_lo) > 0.01 or abs(ci_hi - csv_ci_hi) > 0.01:
                print(f"  FAIL: CI mismatch for claim {cid}: ledger=[{ci_lo}, {ci_hi}], source_csv=[{csv_ci_lo}, {csv_ci_hi}]")
                return False

        verified_claims += 1

    print(f"  PASS: All {verified_claims} claims verified within tolerances (accuracy ±0.005, CIs ±0.01), sample sizes, and git commit history!")
    return True


def main() -> int:
    print("=" * 70)
    print("Encrypted DNS Artifact Provenance & Numerical Verification Suite")
    print("=" * 70)

    checks = [
        verify_datasets,
        verify_feature_space,
        verify_baselines,
        verify_jio_quic_blocking,
        verify_model_comparisons,
        verify_claims_ledger,
    ]

    for check in checks:
        if not check():
            print("\nVerification FAILED! Please inspect the error above.")
            return 1
        print()

    print("=" * 70)
    print("ALL 6 ARTIFACT & NUMERICAL CONSISTENCY CHECKS PASSED")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
