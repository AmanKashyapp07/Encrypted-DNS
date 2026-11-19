#!/usr/bin/env python3
"""
plot_tri_network_figures.py — Generate publication-grade figures for the Tri-Network study:
  - fig5_tri_network_reachability.png: Protocol reachability across Airtel vs Jio vs Campus
  - fig6_tri_network_transfer_matrix.png: 3x3 transfer matrix heatmap
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results/figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def plot_tri_reachability():
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    networks = ["Airtel FTTH\n(Broadband)", "Reliance Jio\n(Cellular)", "IIIT Allahabad\n(Campus Wi-Fi)"]
    x = np.arange(len(networks))
    width = 0.35

    # Reachability rates
    doh_rates = [100.0, 100.0, 100.0]  # Available across all 3 networks
    doh3_rates = [100.0, 0.0, 0.0]     # Blocked on Jio and Campus

    bars1 = ax.bar(x - width/2, doh_rates, width, label="DoH (HTTP/2 over TCP)", color="#2ca02c", edgecolor="black")
    bars2 = ax.bar(x + width/2, doh3_rates, width, label="DoH/3 (HTTP/3 over QUIC / UDP 443)", color="#d62728", edgecolor="black", hatch="//")

    for bar in bars1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.0f}%", ha='center', va='bottom', weight='bold')

    for bar in bars2:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.0f}%", ha='center', va='bottom', weight='bold', color="#d62728" if yval == 0 else "black")

    ax.set_ylabel("Protocol Reachability (%)")
    ax.set_title("Tri-Network Protocol Reachability: Middlebox & Firewall Ossification", weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(networks)
    ax.set_ylim(0, 125)
    ax.legend(loc="upper right", framealpha=0.95)

    out_file = OUT_DIR / "fig5_tri_network_reachability.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    print(f"Wrote {out_file.name}")


def plot_transfer_matrix():
    c2_path = ROOT / "results/campus_analysis_20261120/c2_cross_network_transfer.csv"
    if not c2_path.exists():
        print(f"Warning: {c2_path} missing")
        return
    df_c2 = pd.read_csv(c2_path)
    
    # Average transfer accuracy across 3 networks
    matrix = pd.DataFrame(index=["Airtel", "Jio", "Campus"], columns=["Airtel", "Jio", "Campus"], dtype=float)
    
    # Within-network diagonal values
    matrix.loc["Airtel", "Airtel"] = 0.285  # Average within Airtel DoH
    matrix.loc["Jio", "Jio"] = 0.097        # Average within Jio DoH
    matrix.loc["Campus", "Campus"] = 0.040   # Average within Campus DoH
    
    # Off-diagonal transfer values from c2
    for _, row in df_c2.iterrows():
        src = row["src_network"]
        dst = row["dst_network"]
        # Use google global as representative slice or mean across slices
        sub = df_c2[(df_c2["src_network"] == src) & (df_c2["dst_network"] == dst) & (df_c2["workload"] == "global") & (df_c2["resolver"] == "google")]
        if not sub.empty:
            matrix.loc[src, dst] = float(sub.iloc[0]["accuracy"])

    fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
    cax = ax.matshow(matrix.values * 100, cmap="YlOrRd", vmin=0, vmax=35)
    fig.colorbar(cax, ax=ax, label="Fingerprinting Accuracy (%)")

    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(["Airtel\n(Broadband)", "Jio\n(Cellular)", "Campus\n(Enterprise)"])
    ax.set_yticklabels(["Airtel\n(Broadband)", "Jio\n(Cellular)", "Campus\n(Enterprise)"])
    ax.set_xlabel("Evaluation / Victim Network", labelpad=10, weight="bold")
    ax.set_ylabel("Training / Attacker Network", labelpad=10, weight="bold")
    ax.set_title("3x3 Cross-Network Transfer Matrix (Google DoH)", weight="bold", pad=20)

    for i in range(3):
        for j in range(3):
            val = matrix.iloc[i, j] * 100
            text_color = "white" if val > 20 else "black"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=text_color, weight="bold")

    out_file = OUT_DIR / "fig6_tri_network_transfer_matrix.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    print(f"Wrote {out_file.name}")


if __name__ == "__main__":
    plot_tri_reachability()
    plot_transfer_matrix()
    print("Tri-network slide figures generated successfully!")
