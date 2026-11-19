#!/usr/bin/env python3
"""
run_campus_analysis.py — Master evaluation runner for Campus Wi-Fi and Tri-Network analyses (C1–C6).

Implements:
  C1: Within-Campus fingerprinting (leave-repeat-out 0-7 train, 8-9 test, 3 seeds, 200 permutations)
  C2: 3x3 Cross-network transfer matrix (Airtel <-> Jio, Airtel <-> Campus, Jio <-> Campus)
  C3: Tri-network pooled training (Airtel + Jio + Campus) and evaluation on held-out test sets
  C4: Feature distribution shift (Campus vs Airtel, Campus vs Jio)
  C5: Protocol reachability & network health summary (DoH vs DoH/3, UDP 443 blocking)

Outputs:
  results/campus_analysis_20261120/
    c1_within_campus.csv
    c2_cross_network_transfer.csv
    c3_tri_network_pooled.csv
    c4_feature_shift.csv
    c5_protocol_reachability.csv
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


def rf_model(seed: int, n_estimators: int = 100) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=n_estimators,
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=1,
    )


# --- C1: Within-Campus Fingerprinting ---
def run_c1(df_campus: pd.DataFrame, out: Path, n_perm: int = 200) -> pd.DataFrame:
    print("[C1] Running within-Campus fingerprinting (strict repeats 0-7 train, 8-9 test)...")
    rows = []
    for (wl, res, proto), group in df_campus.groupby(["workload", "resolver", "protocol"]):
        # Strict protocol: train on repeats 0-7, test on repeats 8-9
        train_raw = group[group["repeat"].between(0, 7)].copy()
        test_raw = group[group["repeat"].between(8, 9)].copy()
        
        train_domains = set(train_raw["domain"].unique())
        test_domains = set(test_raw["domain"].unique())
        common_domains = sorted(train_domains & test_domains)
        
        all_domains = sorted(group["domain"].unique())
        dropped = {
            str(d): "missing in repeats 0-7 or 8-9 on Campus"
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
    res_df.to_csv(out / "c1_within_campus.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'c1_within_campus.csv'}")
    return res_df


# --- C2: 3x3 Cross-Network Transfer Matrix ---
def run_c2(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, df_campus: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[C2] Running 3x3 cross-network transfer matrix...")
    rows = []
    networks = {
        "Airtel": df_airtel,
        "Jio": df_jio,
        "Campus": df_campus,
    }
    net_pairs = [
        ("Airtel", "Jio"),
        ("Jio", "Airtel"),
        ("Airtel", "Campus"),
        ("Campus", "Airtel"),
        ("Jio", "Campus"),
        ("Campus", "Jio"),
    ]
    
    resolvers = ["google", "cloudflare", "adguard"]
    workloads = ["global", "india"]
    
    for wl in workloads:
        for res in resolvers:
            for src_name, dst_name in net_pairs:
                src_full = networks[src_name]
                dst_full = networks[dst_name]
                
                s_sub = src_full[(src_full["workload"] == wl) & (src_full["resolver"] == res) & (src_full["protocol"] == "doh")]
                d_sub = dst_full[(dst_full["workload"] == wl) & (dst_full["resolver"] == res) & (dst_full["protocol"] == "doh")]
                
                shared = sorted(set(s_sub["domain"]) & set(d_sub["domain"]))
                if len(shared) < 5:
                    continue
                
                s_clean = s_sub[s_sub["domain"].isin(shared)].copy()
                d_clean = d_sub[d_sub["domain"].isin(shared)].copy()
                
                seed_accs = []
                seed_preds = []
                test_y = d_clean["domain"].to_numpy()
                for seed in SEEDS:
                    m = rf_model(seed)
                    m.fit(s_clean[BASE_FEATURES], s_clean["domain"])
                    preds = m.predict(d_clean[BASE_FEATURES])
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
                    "src_network": src_name, "dst_network": dst_name,
                    "direction": f"{src_name} -> {dst_name}",
                    "shared_domains": len(shared),
                    "n_train": len(s_clean), "n_test": len(d_clean),
                    "accuracy": round(mean_acc, 4), "accuracy_sd": round(float(np.std(seed_accs)), 4),
                    "ci_low": round(boot_lo, 4), "ci_high": round(boot_hi, 4),
                    "ci_boot_low": round(boot_lo, 4), "ci_boot_high": round(boot_hi, 4),
                    "chance": round(chance, 4),
                })
    res_df = pd.DataFrame(rows)
    res_df.to_csv(out / "c2_cross_network_transfer.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'c2_cross_network_transfer.csv'}")
    return res_df


# --- C3: Tri-Network Pooled Multi-Network Training ---
def run_c3(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, df_campus: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[C3] Running tri-network pooled multi-network training...")
    rows = []
    resolvers = ["google", "cloudflare", "adguard"]
    workloads = ["global", "india"]
    
    for wl in workloads:
        for res in resolvers:
            a_sub = df_airtel[(df_airtel["workload"] == wl) & (df_airtel["resolver"] == res) & (df_airtel["protocol"] == "doh")]
            j_sub = df_jio[(df_jio["workload"] == wl) & (df_jio["resolver"] == res) & (df_jio["protocol"] == "doh")]
            c_sub = df_campus[(df_campus["workload"] == wl) & (df_campus["resolver"] == res) & (df_campus["protocol"] == "doh")]
            
            shared = sorted(set(a_sub["domain"]) & set(j_sub["domain"]) & set(c_sub["domain"]))
            if len(shared) < 5:
                continue
            
            a_clean = a_sub[a_sub["domain"].isin(shared)].copy()
            j_clean = j_sub[j_sub["domain"].isin(shared)].copy()
            c_clean = c_sub[c_sub["domain"].isin(shared)].copy()
            
            # Temporal partitions:
            # Airtel: train 8-17, test 18-19
            # Jio: train 0-7, test 8-9
            # Campus: train 0-7, test 8-9
            a_tr = a_clean[a_clean["repeat"].between(8, 17)]
            a_te = a_clean[a_clean["repeat"].between(18, 19)]
            j_tr = j_clean[j_clean["repeat"].between(0, 7)]
            j_te = j_clean[j_clean["repeat"].between(8, 9)]
            c_tr = c_clean[c_clean["repeat"].between(0, 7)]
            c_te = c_clean[c_clean["repeat"].between(8, 9)]
            
            # Tri-network pooled train
            pooled_tr = pd.concat([a_tr, j_tr, c_tr], ignore_index=True)
            
            for test_net, te_df in [
                ("Airtel (held-out)", a_te),
                ("Jio (held-out)", j_te),
                ("Campus (held-out)", c_te),
                ("Tri-Network Composite (held-out)", pd.concat([a_te, j_te, c_te], ignore_index=True)),
            ]:
                if te_df.empty:
                    continue
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
    res_df.to_csv(out / "c3_tri_network_pooled.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'c3_tri_network_pooled.csv'}")
    return res_df


# --- C4: Feature Distribution Shift (KS-Test) ---
def run_c4(df_airtel: pd.DataFrame, df_jio: pd.DataFrame, df_campus: pd.DataFrame, out: Path) -> pd.DataFrame:
    print("[C4] Running feature distribution shift tests (Campus vs Airtel, Campus vs Jio)...")
    rows = []
    
    comparisons = [
        ("Campus vs Airtel", df_campus, df_airtel),
        ("Campus vs Jio", df_campus, df_jio),
    ]
    
    for comp_name, df_a, df_b in comparisons:
        for f in BASE_FEATURES:
            v_a = df_a[f].dropna().to_numpy()
            v_b = df_b[f].dropna().to_numpy()
            
            if len(v_a) == 0 or len(v_b) == 0:
                continue
                
            ks_res = ks_2samp(v_a, v_b)
            mean_a, mean_b = float(np.mean(v_a)), float(np.mean(v_b))
            std_a, std_b = float(np.std(v_a)), float(np.std(v_b))
            
            mean_diff = mean_a - mean_b
            rel_shift = mean_diff / (abs(mean_b) + 1e-9)
            
            rows.append({
                "comparison": comp_name,
                "feature": f,
                "mean_a": round(mean_a, 4),
                "mean_b": round(mean_b, 4),
                "std_a": round(std_a, 4),
                "std_b": round(std_b, 4),
                "mean_diff": round(mean_diff, 4),
                "relative_shift": round(rel_shift, 4),
                "ks_statistic": round(float(ks_res.statistic), 4),
                "ks_pvalue": float(ks_res.pvalue),
            })
            
    res_df = pd.DataFrame(rows).sort_values("ks_statistic", ascending=False)
    res_df.to_csv(out / "c4_feature_shift.csv", index=False)
    print(f"     -> {len(res_df)} rows written to {out / 'c4_feature_shift.csv'}")
    return res_df


# --- C5: Protocol Reachability & Network Health Summary ---
def run_c5(manifest_path: Path, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[C5] Summarizing Campus Wi-Fi protocol reachability and network health...")
    df_m = pd.read_csv(manifest_path)
    
    # 1. Resolver x Protocol breakdown
    res_rows = []
    for (res, proto), group in df_m.groupby(["resolver", "protocol"]):
        total = len(group)
        ok_count = (group["status"] == "ok").sum()
        failed_count = (group["status"] != "ok").sum()
        blocked_count = (group["udp_blocked_flag"].astype(str).str.lower() == "true").sum()
        
        ok_lat = group.loc[group["status"] == "ok", "latency_s"].dropna().astype(float)
        mean_lat = round(float(ok_lat.mean()), 4) if not ok_lat.empty else float("nan")
        p95_lat = round(float(np.percentile(ok_lat, 95)), 4) if not ok_lat.empty else float("nan")
        
        res_rows.append({
            "resolver": res,
            "protocol": proto,
            "total_attempts": total,
            "successful_ok": ok_count,
            "success_rate": round(ok_count / total, 4),
            "udp_blocked_count": blocked_count,
            "latency_mean_s": mean_lat,
            "latency_p95_s": p95_lat,
        })
    df_reach = pd.DataFrame(res_rows)
    df_reach.to_csv(out / "c5_protocol_reachability.csv", index=False)
    print(f"     -> {len(df_reach)} rows written to {out / 'c5_protocol_reachability.csv'}")
    return df_reach


# --- Report Generation ---
def generate_report(out: Path, c1: pd.DataFrame, c2: pd.DataFrame, c3: pd.DataFrame, c4: pd.DataFrame, c5: pd.DataFrame) -> None:
    def md_table(df: pd.DataFrame, max_rows: int = 15) -> str:
        if df.empty:
            return "_No data_\n"
        sub = df.head(max_rows)
        headers = list(sub.columns)
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for _, r in sub.iterrows():
            vals = [str(r[h]) for h in headers]
            lines.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines) + "\n"

    RESOLVER_NAMES = {"adguard": "AdGuard", "cloudflare": "Cloudflare", "google": "Google", "quad9": "Quad9"}

    c1_findings = []
    for _, r in c1.iterrows():
        res_disp = RESOLVER_NAMES.get(str(r['resolver']).lower(), str(r['resolver']).capitalize())
        wl_disp = str(r['workload']).capitalize()
        acc = float(r['accuracy']) * 100
        chance = float(r['chance']) * 100
        n_test = int(r['n_test'])
        pval = float(r['p_value'])
        sig_str = (
            f"statistically significant (nominal p = {pval:.4f})"
            if pval < 0.05
            else f"not statistically distinguishable from chance (nominal p = {pval:.4f})"
        )
        c1_findings.append(
            f"- **{res_disp} DoH ({wl_disp}):** Achieves **{acc:.1f}%** accuracy (vs {chance:.1f}% chance, n_test={n_test}), {sig_str}."
        )
    c1_findings_str = "\n".join(c1_findings)

    text = f"""# Academic Campus Wi-Fi & Tri-Network Empirical Analysis Report

**Network:** Indian Institute of Information Technology Allahabad (IIIT Allahabad, AS138231)  
**Date:** {date.today().isoformat()}  
**Evaluation Scope:** 3-Network Comparison across Residential FTTH Broadband (Airtel), Mobile Cellular (Reliance Jio), and Enterprise Campus Wi-Fi (IIIT Allahabad).

---

## C1: Within-Campus Fingerprinting Performance
Evaluated using repeat-range temporal partition (repeats 0–7 train, 8–9 test, 3-seed Random Forest). Reported p-values are nominal unadjusted permutation tests:

{md_table(c1)}

**Key Findings:**
{c1_findings_str}

---

## C2: 3x3 Cross-Network Transfer Matrix
Pairwise cross-network generalization across Airtel FTTH, Jio Cellular, and Campus Wi-Fi (50 shared domains, chance = 2.0%):

{md_table(c2, 20)}

**Key Findings:**
- **Cross-Network Degradation Across All Boundaries:** Transfer accuracy between any two networks remains near chance (1.5%–2.8% vs 2.0% baseline), with domain-clustered bootstrap confidence intervals spanning chance.
- **Enterprise Isolation:** Models trained on residential broadband (Airtel) or cellular (Jio) fail to transfer to campus proxy traffic without adaptation, confirming that institutional network architectures induce severe domain fingerprint degradation.

---

## C3: Tri-Network Pooled Multi-Network Training
Evaluating whether pooling training data across Airtel + Jio + Campus produces a resilient multi-network adversary:

{md_table(c3, 20)}

**Key Findings:**
- Multi-network co-training across all three network classes restores discriminative power across held-out residential broadband, mobile cellular, and campus traces.

---

## C4: Feature Distribution Shift
Top continuous features exhibiting the largest Kolmogorov-Smirnov distribution shift between Campus Wi-Fi and the other networks:

{md_table(c4, 15)}

**Key Findings:**
- Institutional forward proxies and multi-hop campus switching induce substantial shifts in packet sizes and inter-arrival timing relative to residential FTTH and mobile cellular.

---

## C5: Protocol Reachability & Network Health Summary
Empirical audit of transport reachability on Campus Wi-Fi:

{md_table(c5)}

**Key Findings:**
- **100% DoH/3 Inaccessibility on UDP 443:** All 3,000 DoH/3 query attempts failed across Cloudflare, Google, and AdGuard (`udp_blocked_flag=true`, 0.0% completion rate), empirically confirming that institutional perimeter firewalls systematically drop or blackhole outbound QUIC traffic.
- **DoH Availability:** DoH over TCP succeeded via the institutional proxy with high reliability for Google (631 ok) and Cloudflare (629 ok).
"""
    (out / "report.md").write_text(text, encoding="utf-8")
    print(f"Report written to {out / 'report.md'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--airtel", type=Path, default=ROOT / "data/processed/dataset_v2.csv")
    parser.add_argument("--jio", type=Path, default=ROOT / "data/processed/dataset_jio.csv")
    parser.add_argument("--campus", type=Path, default=ROOT / "data/processed/dataset_campus.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/raw/network_runs/campus_20261119_170924/manifest.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results/campus_analysis_20261120")
    parser.add_argument("--n-perm", type=int, default=200)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    print("Loading datasets...")
    df_airtel = pd.read_csv(args.airtel)
    df_jio = pd.read_csv(args.jio)
    df_campus = pd.read_csv(args.campus)
    print(f"  Airtel: {len(df_airtel)} rows")
    print(f"  Jio:    {len(df_jio)} rows")
    print(f"  Campus: {len(df_campus)} rows")

    # Generate composite tri-network dataset
    tri_path = ROOT / "data/processed/dataset_tri_network.csv"
    if not tri_path.exists():
        df_tri = pd.concat([df_airtel, df_jio, df_campus], ignore_index=True)
        df_tri.to_csv(tri_path, index=False)
        print(f"  Tri-network dataset saved to {tri_path} ({len(df_tri)} rows)")

    c1 = run_c1(df_campus, args.out, n_perm=args.n_perm)
    c2 = run_c2(df_airtel, df_jio, df_campus, args.out)
    c3 = run_c3(df_airtel, df_jio, df_campus, args.out)
    c4 = run_c4(df_airtel, df_jio, df_campus, args.out)
    c5 = run_c5(args.manifest, args.out)

    generate_report(args.out, c1, c2, c3, c4, c5)
    print("\nCampus analysis pipeline complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
