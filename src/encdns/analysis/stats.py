"""Statistical primitives shared by every supported analysis."""
from __future__ import annotations
import math
import numpy as np

def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        return (float("nan"), float("nan"))
    proportion = successes / trials
    denominator = 1 + z * z / trials
    centre = proportion + z * z / (2 * trials)
    half_width = z * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials))
    return (float(max(0.0, (centre - half_width) / denominator)), float(min(1.0, (centre + half_width) / denominator)))

def domain_clustered_bootstrap(
    actual: list | np.ndarray,
    predicted: list | np.ndarray,
    domains: list | np.ndarray,
    n_bootstraps: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float]:
    """Compute cluster-robust confidence interval via domain-level block bootstrap.
    
    Resamples unique domains with replacement, collecting all test observations
    for each sampled domain, accounting for intra-domain correlation.
    """
    actual_arr = np.asarray(actual)
    pred_arr = np.asarray(predicted)
    domain_arr = np.asarray(domains)
    if len(actual_arr) == 0:
        return (float("nan"), float("nan"))
    
    unique_domains = np.unique(domain_arr)
    n_domains = len(unique_domains)
    if n_domains < 2:
        acc = float(np.mean(actual_arr == pred_arr))
        return (acc, acc)
    
    # Pre-group indices by domain for high performance
    domain_to_indices = {d: np.where(domain_arr == d)[0] for d in unique_domains}
    rng = np.random.default_rng(seed)
    bootstrap_accs = np.empty(n_bootstraps, dtype=float)
    
    for b in range(n_bootstraps):
        sampled_domains = rng.choice(unique_domains, size=n_domains, replace=True)
        # Gather indices for sampled domains
        sampled_indices = np.concatenate([domain_to_indices[d] for d in sampled_domains])
        bootstrap_accs[b] = np.mean(actual_arr[sampled_indices] == pred_arr[sampled_indices])
    
    lower = float(np.percentile(bootstrap_accs, 100 * (alpha / 2)))
    upper = float(np.percentile(bootstrap_accs, 100 * (1 - alpha / 2)))
    return (max(0.0, lower), min(1.0, upper))

def empirical_p_value(observed: float, null_scores: list[float]) -> float:
    if not null_scores:
        return float("nan")
    return (1 + sum(score >= observed for score in null_scores)) / (1 + len(null_scores))

def fdr_correction(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Benjamini-Hochberg False Discovery Rate (FDR) adjusted p-values."""
    p_arr = np.asarray(p_values, dtype=float)
    n = len(p_arr)
    if n == 0:
        return []
    order = np.argsort(p_arr)
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(1, n + 1)
    
    # Adjusted p-values: min(1, p * n / rank) with monotonicity constraint
    adj = p_arr * n / ranks
    # Enforce monotonicity backwards
    sorted_adj = adj[order]
    for i in range(n - 2, -1, -1):
        sorted_adj[i] = min(sorted_adj[i], sorted_adj[i + 1])
    adj[order] = sorted_adj
    return [float(min(1.0, max(0.0, val))) for val in adj]
