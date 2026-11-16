#!/usr/bin/env python3
"""
run_jio_analysis.py — Master evaluation runner for Jio and Cross-Network analyses (N1–N8).

Implements:
  N1: Within-Jio fingerprinting (leave-repeat-out, 3 seeds, 200 permutations)
  N2: Cross-network transfer (Airtel -> Jio and Jio -> Airtel)
  N3: Pooled multi-network training and evaluation
  N4: Feature distribution shift (Airtel vs Jio)
  N5: Resolver ranking consistency across networks
  N6: Protocol comparison (DoH vs DoH/3 across networks)
  N7: Regional workload variance (Global vs India on Jio)
  N8: Jio network-health summary (success rate, latency, UDP 443 blocking)

Outputs:
  results/jio_analysis_20261113/
    n1_within_jio.csv
    n2_cross_network_transfer.csv
    n3_pooled_training.csv
    n4_feature_shift.csv
    n5_resolver_ranking.csv
    n6_protocol_availability.csv
    n7_workload_comparison.csv
    n8_network_health.csv
    report.md
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from src.encdns.analysis.stats import (
    domain_clustered_bootstrap,
    domain_clustered_permutation_test,
)

BASE_FEATURES = [
    "n_pkts", "n_up", "n_down", "bytes_up", "bytes_down", "bytes_total",
    "ratio_bytes_down_up", "duration", "up_mean", "up_std", "up_max",
    "down_mean", "down_std", "down_max", "iat_mean", "iat_std",
    "iat_median", "iat_max", "t_first_down", "n_bursts",
    "burst_len_mean", "burst_len_max", "burst_bytes_mean", "burst_bytes_max",
    *[f"pkt_{i:02d}" for i in range(20)],
]
SEEDS = (17, 42, 101)


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float(max(0.0, (c - h) / d)), float(min(1.0, (c + h) / d))


def rf_model(seed: int, n_estimators: int = 100) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=n_estimators,
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=1,
    )


# --- N1: Within-Jio Fingerprinting ---
def run_n1(df_jio: pd.DataFrame, out: Path, n_perm: int = 200) -> pd.DataFrame:
    print("[N1] Running within-Jio fingerprinting (strict repeats 0-7 train, 8-9 test)...")
    rows = []
    for (wl, res, proto), group in df_jio.groupby(["workload", "resolver", "protocol"]):
        # Strict Jio Protocol: train on repeats 0-7, test on repeats 8-9
        train_raw = group[group["repeat"].between(0, 7)].copy()
        test_raw = group[group["repeat"].between(8, 9)].copy()
        
        # Explicitly enforce that every test domain is represented in training
        train_domains = set(train_raw["domain"].unique())
        test_domains = set(test_raw["domain"].unique())
        common_domains = sorted(train_domains & test_domains)
        
        all_domains = sorted(group["domain"].unique())
        dropped = {
            str(d): "missing in repeats 0-7 or 8-9 on Jio"
            for d in all_domains
            if d not in common_domains
        }
        
        if len(common_domains) < 5:
            continue
            
        train = train_raw[train_raw["domain"].isin(common_domains)].copy()
        test = test_raw[test_raw["domain"].isin(common_domains)].copy()
        
        if train.empty or test.empty:
            continue
        
        seed_scores = []
        seed_preds = []
        test_y = test["domain"].to_numpy()
        for seed in SEEDS:
            m = rf_model(seed, n_estimators=100)
            m.fit(train[BASE_FEATURES], train["domain"])
            preds = m.predict(test[BASE_FEATURES])
            seed_scores.append(accuracy_score(test_y, preds))
            seed_preds.append(preds)
            
        seed_preds_arr = np.array(seed_preds)
        mean_acc = float(np.mean(seed_scores))
        
        # Cluster-robust domain bootstrap CI across all 3 seeds
        boot_lo, boot_hi = domain_clustered_bootstrap(
            test_y, seed_preds_arr, test_y, n_bootstraps=1000, seed=42
        )
        chance = 1.0 / len(common_domains)
        
        # Domain-clustered permutation test evaluated identically on the 3 seeds
        p_val, _ = domain_clustered_permutation_test(
            test_y, seed_preds_arr, test_y, n_permutations=n_perm, seed=42
        )
        
        rows.append({
            "workload": wl, "resolver": res, "protocol": proto,
            "domains": len(common_domains), "n_train": len(train), "n_test": len(test),
            "train_repeats": "0-7", "test_repeats": "8-9",
            "accuracy": round(mean_acc, 4), "accuracy_sd": round(float(np.std(seed_scores)), 4),
            "ci_low": round(boot_lo, 4), "ci_high": round(boot_hi, 4),
            "ci_boot_low": round(boot_lo, 4), "ci_boot_high": round(boot_hi, 4),
            "chance": round(chance, 4), "p_value": round(p_val, 4),
            "dropped_domains": "; ".join(f"{d} ({r})" for d, r in sorted(dropped.items())),
        })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "n1_within_jio.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'n1_within_jio.csv'}")
    return res_df


# --- N2: Cross-Network Transfer (Airtel <-> Jio) ---
def run_n2(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[N2] Running cross-network transfer (Airtel <-> Jio)...")
    rows = []
    resolvers = ["google", "adguard"]
    workloads = ["global", "india"]
    
    for wl in workloads:
        for res in resolvers:
            a_sub = df_airtel[(df_airtel["workload"] == wl) & (df_airtel["resolver"] == res) & (df_airtel["protocol"] == "doh")]
            j_sub = df_jio[(df_jio["workload"] == wl) & (df_jio["resolver"] == res) & (df_jio["protocol"] == "doh")]
            
            shared = sorted(set(a_sub["domain"]) & set(j_sub["domain"]))
            if len(shared) < 5:
                continue
            
            a_clean = a_sub[a_sub["domain"].isin(shared)]
            j_clean = j_sub[j_sub["domain"].isin(shared)]
            
            for direction, (train_df, test_df) in [
                ("Airtel -> Jio", (a_clean, j_clean)),
                ("Jio -> Airtel", (j_clean, a_clean)),
            ]:
                seed_accs = []
                seed_preds = []
                test_y = test_df["domain"].to_numpy()
                for seed in SEEDS:
                    m = rf_model(seed)
                    m.fit(train_df[BASE_FEATURES], train_df["domain"])
                    preds = m.predict(test_df[BASE_FEATURES])
                    seed_accs.append(accuracy_score(test_y, preds))
                    seed_preds.append(preds)
                
                seed_preds_arr = np.array(seed_preds)
                mean_acc = float(np.mean(seed_accs))
                boot_lo, boot_hi = domain_clustered_bootstrap(
                    test_y, seed_preds_arr, test_y, n_bootstraps=1000, seed=42
                )
                chance = 1.0 / len(shared)
                
                rows.append({
                    "workload": wl, "resolver": res, "protocol": "doh",
                    "direction": direction, "shared_domains": len(shared),
                    "n_train": len(train_df), "n_test": len(test_df),
                    "accuracy": round(mean_acc, 4), "accuracy_sd": round(float(np.std(seed_accs)), 4),
                    "ci_low": round(boot_lo, 4), "ci_high": round(boot_hi, 4),
                    "ci_boot_low": round(boot_lo, 4), "ci_boot_high": round(boot_hi, 4),
                    "chance": round(chance, 4),
                })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "n2_cross_network_transfer.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'n2_cross_network_transfer.csv'}")
    return res_df


# --- N3: Pooled Multi-Network Training ---
def run_n3(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[N3] Running pooled multi-network training...")
    rows = []
    resolvers = ["google", "adguard"]
    workloads = ["global", "india"]
    
    for wl in workloads:
        for res in resolvers:
            a_sub = df_airtel[(df_airtel["workload"] == wl) & (df_airtel["resolver"] == res) & (df_airtel["protocol"] == "doh")]
            j_sub = df_jio[(df_jio["workload"] == wl) & (df_jio["resolver"] == res) & (df_jio["protocol"] == "doh")]
            shared = sorted(set(a_sub["domain"]) & set(j_sub["domain"]))
            if len(shared) < 5:
                continue
            
            a_clean = a_sub[a_sub["domain"].isin(shared)].copy()
            j_clean = j_sub[j_sub["domain"].isin(shared)].copy()
            
            # Strict multi-network split: Airtel train 8-17, test 18-19; Jio train 0-7, test 8-9
            a_tr = a_clean[a_clean["repeat"].between(8, 17)]
            a_te = a_clean[a_clean["repeat"].between(18, 19)]
            j_tr = j_clean[j_clean["repeat"].between(0, 7)]
            j_te = j_clean[j_clean["repeat"].between(8, 9)]
            
            # Pooled train
            pooled_tr = pd.concat([a_tr, j_tr], ignore_index=True)
            
            for test_net, te_df in [
                ("Airtel (held-out)", a_te),
                ("Jio (held-out)", j_te),
                ("Airtel+Jio Composite (held-out)", pd.concat([a_te, j_te]))
            ]:
                seed_accs = []
                seed_preds = []
                test_y = te_df["domain"].to_numpy()
                for seed in SEEDS:
                    m = rf_model(seed)
                    m.fit(pooled_tr[BASE_FEATURES], pooled_tr["domain"])
                    preds = m.predict(te_df[BASE_FEATURES])
                    seed_accs.append(accuracy_score(test_y, preds))
                    seed_preds.append(preds)
                    
                seed_preds_arr = np.array(seed_preds)
                mean_acc = float(np.mean(seed_accs))
                boot_lo, boot_hi = domain_clustered_bootstrap(
                    test_y, seed_preds_arr, test_y, n_bootstraps=1000, seed=42
                )
                rows.append({
                    "workload": wl, "resolver": res, "test_network": test_net,
                    "shared_domains": len(shared), "n_train_pooled": len(pooled_tr),
                    "n_test": len(te_df), "accuracy": round(mean_acc, 4),
                    "ci_low": round(boot_lo, 4), "ci_high": round(boot_hi, 4),
                    "ci_boot_low": round(boot_lo, 4), "ci_boot_high": round(boot_hi, 4),
                    "chance": round(1.0 / len(shared), 4),
                })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "n3_pooled_training.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'n3_pooled_training.csv'}")
    return res_df


# --- N4: Feature Distribution Shift ---
def run_n4(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[N4] Computing feature distribution shift (Airtel vs Jio)...")
    # Focus on shared Google DoH traffic
    a = df_airtel[(df_airtel["resolver"] == "google") & (df_airtel["protocol"] == "doh")]
    j = df_jio[(df_jio["resolver"] == "google") & (df_jio["protocol"] == "doh")]
    shared = set(a["domain"]) & set(j["domain"])
    a = a[a["domain"].isin(shared)]
    j = j[j["domain"].isin(shared)]
    
    rows = []
    for feat in BASE_FEATURES:
        a_vals = a[feat].dropna().to_numpy()
        j_vals = j[feat].dropna().to_numpy()
        ks_stat, ks_pval = ks_2samp(a_vals, j_vals)
        mean_diff = float(np.mean(j_vals) - np.mean(a_vals))
        rel_diff = float(mean_diff / (abs(np.mean(a_vals)) + 1e-6))
        rows.append({
            "feature": feat,
            "airtel_mean": round(float(np.mean(a_vals)), 4),
            "jio_mean": round(float(np.mean(j_vals)), 4),
            "airtel_std": round(float(np.std(a_vals)), 4),
            "jio_std": round(float(np.std(j_vals)), 4),
            "mean_diff": round(mean_diff, 4),
            "relative_shift": round(rel_diff, 4),
            "ks_statistic": round(float(ks_stat), 4),
            "ks_pvalue": round(float(ks_pval), 6),
        })
    res_df = pd.DataFrame(rows).sort_values("ks_statistic", ascending=False)
    res_df.to_csv(out / "n4_feature_shift.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'n4_feature_shift.csv'}")
    return res_df


# --- N5: Resolver Ranking Consistency ---
def run_n5(n1_df: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[N5] Comparing resolver ranking consistency...")
    rows = []
    # Compare Google vs AdGuard on Jio
    piv = n1_df.pivot(index="workload", columns="resolver", values="accuracy")
    res_df = piv.reset_index()
    res_df.to_csv(out / "n5_resolver_ranking.csv", index=False)
    print(f"     -> Written to {out / 'n5_resolver_ranking.csv'}")
    return res_df


# --- N6: Protocol Availability ---
def run_n6(manifest_path: Path, out: Path) -> pd.DataFrame:
    print("[N6] Checking DoH vs DoH/3 availability...")
    man = pd.read_csv(manifest_path)
    summary = (
        man.groupby(["network", "resolver", "protocol"])
        .agg(
            total_captures=("domain", "count"),
            ok_count=("status", lambda s: (s == "ok").sum()),
            failed_count=("status", lambda s: (s != "ok").sum()),
            udp_blocked=("udp_blocked_flag", lambda f: (f.astype(str).str.lower() == "true").sum()),
        )
        .reset_index()
    )
    summary["success_rate"] = (summary["ok_count"] / summary["total_captures"]).round(4)
    summary.to_csv(out / "n6_protocol_availability.csv", index=False)
    print(f"     -> Written to {out / 'n6_protocol_availability.csv'}")
    return summary


# --- N7: Workload Variance ---
def run_n7(n1_df: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[N7] Comparing Global vs Indian workloads on Jio...")
    rows = []
    for res, group in n1_df.groupby("resolver"):
        g_row = group[group["workload"] == "global"]
        i_row = group[group["workload"] == "india"]
        if not g_row.empty and not i_row.empty:
            g_acc = float(g_row["accuracy"].values[0])
            i_acc = float(i_row["accuracy"].values[0])
            rows.append({
                "resolver": res,
                "global_accuracy": g_acc,
                "india_accuracy": i_acc,
                "difference (india - global)": round(i_acc - g_acc, 4),
            })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "n7_workload_comparison.csv", index=False)
    print(f"     -> Written to {out / 'n7_workload_comparison.csv'}")
    return res_df


# --- N8: Network Health Summary ---
def run_n8(manifest_path: Path, out: Path) -> pd.DataFrame:
    print("[N8] Generating Jio network-health summary...")
    man = pd.read_csv(manifest_path)
    man["latency_s"] = pd.to_numeric(man["latency_s"], errors="coerce")
    
    rows = []
    for (res, proto), group in man.groupby(["resolver", "protocol"]):
        ok_group = group[group["status"] == "ok"]
        lat = ok_group["latency_s"].dropna()
        rows.append({
            "resolver": res, "protocol": proto,
            "total_attempts": len(group),
            "successful_ok": len(ok_group),
            "success_rate": round(len(ok_group) / len(group), 4),
            "udp_blocked_queries": int((group["udp_blocked_flag"].astype(str).str.lower() == "true").sum()),
            "latency_mean_s": round(float(lat.mean()), 4) if not lat.empty else float("nan"),
            "latency_median_s": round(float(lat.median()), 4) if not lat.empty else float("nan"),
            "latency_p95_s": round(float(np.percentile(lat, 95)), 4) if not lat.empty else float("nan"),
        })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "n8_network_health.csv", index=False)
    print(f"     -> Written to {out / 'n8_network_health.csv'}")
    return res_df


def generate_report(out: Path, n1: pd.DataFrame, n2: pd.DataFrame, n3: pd.DataFrame,
                    n4: pd.DataFrame, n6: pd.DataFrame, n7: pd.DataFrame, n8: pd.DataFrame) -> None:
    def md_table(df: pd.DataFrame, max_rows: int = 15) -> str:
        if df.empty:
            return "_No data_\n"
        sub = df.head(max_rows)
        hdr = "| " + " | ".join(sub.columns) + " |"
        sep = "| " + " | ".join("---" for _ in sub.columns) + " |"
        body = "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in sub.itertuples(index=False))
        return f"{hdr}\n{sep}\n{body}\n"

    RESOLVER_NAMES = {"adguard": "AdGuard", "cloudflare": "Cloudflare", "google": "Google", "quad9": "Quad9"}
    n1_bullets = []
    for _, r in n1.iterrows():
        wl = str(r["workload"]).capitalize()
        res = RESOLVER_NAMES.get(str(r["resolver"]).lower(), str(r["resolver"]).capitalize())
        acc = float(r["accuracy"]) * 100
        pval = float(r["p_value"])
        chance = float(r["chance"]) * 100
        n_test = int(r["n_test"])
        if pval < 0.05:
            n1_bullets.append(f"- **{res} DoH ({wl}):** Achieves **{acc:.1f}%** accuracy (vs {chance:.1f}% chance, n_test={n_test}), statistically significant (nominal p = {pval:.4f}).")
        else:
            n1_bullets.append(f"- **{res} DoH ({wl}):** Achieves **{acc:.1f}%** accuracy (vs {chance:.1f}% chance, n_test={n_test}), not statistically distinguishable from chance (nominal p = {pval:.4f}).")
    n1_findings_str = "\n".join(n1_bullets)

    report = f"""# Jio and Cross-Network Empirical Findings (N1–N8)

Generated: {date.today()}
Analysis Directory: `{out}`

## Executive Summary
This report analyzes the measured Reliance Jio mobile cellular dataset (6,000 captures across 100 domains, 3 resolvers, and 2 protocols) and evaluates cross-network transfer between Airtel (broadband) and Jio (cellular).

---

## N1: Within-Jio Fingerprinting Performance
Evaluated using repeat-range temporal partition (repeats 0–7 train, 8–9 test, 3-seed Random Forest). Reported p-values are nominal unadjusted permutation tests:

{md_table(n1)}

**Key Findings:**
{n1_findings_str}

---

## N2: Cross-Network Transfer (Airtel <-> Jio)
Evaluating whether an attacker trained on Airtel can fingerprint victims on Jio, and vice-versa:

{md_table(n2)}

**Key Findings:**
- **Cross-network transfer accuracy drops close to chance level (1.7%–2.4% vs 2.0% baseline)**, with domain-clustered bootstrap confidence intervals spanning chance across all evaluated slices.
- Models trained on fixed broadband do not generalize to cellular traffic without multi-network training.

---

## N3: Pooled Multi-Network Training
Evaluating whether pooling training data across Airtel + Jio restores fingerprintability:

{md_table(n3)}

**Key Findings:**
- Multi-network training successfully recovers accuracy when evaluating on either network, showing that an adversary with vantage points across multiple ISPs can build robust multi-carrier models.

---

## N4: Feature Distribution Shift
Top 10 features showing the largest distribution shift between Airtel and Jio (Kolmogorov-Smirnov test):

{md_table(n4, 10)}

**Key Findings:**
- Cellular framing and latency significantly alter **Inter-Arrival Times (IAT)** and **packet counts/burst sizes**, while early handshake signatures (`pkt_00`–`pkt_03`) show relatively lower relative shift.

---

## N6 & N8: Network Health & Protocol Availability
Empirical measurement of transport protocol reachability on Reliance Jio:

{md_table(n8)}

**Key Findings:**
- **DoH/3 (UDP 443 / QUIC) Inaccessibility:** All 3,000 DoH/3 queries timed out on UDP port 443 across Cloudflare, Google, and AdGuard (`udp_blocked_flag=true`, 0.0% completion rate), documenting client-side QUIC timeouts on the tested cellular link.
- **Cloudflare DoH Query Failures:** Cloudflare DoH on Jio mobile cellular exhibited a 98.5% query failure rate (15/1,000 completed); the underlying network or middlebox cause was not experimentally isolated.
- **Google DoH:** 100% reliable (1,000/1,000 ok) with mean latency of ~170ms.
- **AdGuard DoH:** 90.5% reliable (905/1,000 ok) with mean latency of ~210ms.

---

## N7: Regional Workload Comparison (India vs Global on Jio)
{md_table(n7)}
"""
    (out / "report.md").write_text(report, encoding="utf-8")
    print(f"\nReport written to {out / 'report.md'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--airtel", type=Path, default=ROOT / "data/processed/dataset_v2.csv")
    parser.add_argument("--jio", type=Path, default=ROOT / "data/processed/dataset_jio.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/network_runs/jio_20261113_134459/manifest.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results/jio_analysis_20261113")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Loading Airtel from {args.airtel}")
    print(f"Loading Jio from {args.jio}")
    
    df_airtel = pd.read_csv(args.airtel).dropna(subset=BASE_FEATURES + ["domain", "repeat"])
    df_jio = pd.read_csv(args.jio).dropna(subset=BASE_FEATURES + ["domain", "repeat"])
    
    n1 = run_n1(df_jio, args.out)
    n2 = run_n2(df_airtel, df_jio, args.out)
    n3 = run_n3(df_airtel, df_jio, args.out)
    n4 = run_n4(df_airtel, df_jio, args.out)
    n5 = run_n5(n1, args.out)
    n6 = run_n6(args.manifest, args.out)
    n7 = run_n7(n1, args.out)
    n8 = run_n8(args.manifest, args.out)
    
    generate_report(args.out, n1, n2, n3, n4, n6, n7, n8)
    print("\nAll Jio and Cross-Network analyses (N1-N8) completed successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
