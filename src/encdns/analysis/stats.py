"""Statistical primitives shared by every supported analysis."""
from __future__ import annotations
import math
import numpy as np


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for binomial proportion."""
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
    Supports single-seed predictions (1D) or multi-seed predictions (2D, shape S x N).
    When multi-seed predictions are provided, calculates the bootstrap confidence
    interval for the reported multi-seed mean accuracy.
    """
    actual_arr = np.asarray(actual)
    pred_arr = np.asarray(predicted)
    domain_arr = np.asarray(domains)
    if len(actual_arr) == 0:
        return (float("nan"), float("nan"))
    
    if pred_arr.ndim == 2:
        # Multi-seed predictions: compute mean correctness across seeds per query
        correctness = np.mean(pred_arr == actual_arr, axis=0)  # shape (N,)
    elif pred_arr.ndim == 1 and actual_arr.ndim == 1:
        correctness = (actual_arr == pred_arr).astype(float)
    else:
        correctness = np.asarray(predicted, dtype=float)
        
    unique_domains = np.unique(domain_arr)
    n_domains = len(unique_domains)
    if n_domains < 2:
        acc = float(np.mean(correctness))
        return (acc, acc)
        
    domain_to_indices = {d: np.where(domain_arr == d)[0] for d in unique_domains}
    rng = np.random.default_rng(seed)
    bootstrap_accs = np.empty(n_bootstraps, dtype=float)
    
    for b in range(n_bootstraps):
        sampled_domains = rng.choice(unique_domains, size=n_domains, replace=True)
        sampled_indices = np.concatenate([domain_to_indices[d] for d in sampled_domains])
        bootstrap_accs[b] = np.mean(correctness[sampled_indices])
        
    lower = float(np.percentile(bootstrap_accs, 100 * (alpha / 2)))
    upper = float(np.percentile(bootstrap_accs, 100 * (1 - alpha / 2)))
    return (max(0.0, lower), min(1.0, upper))


def domain_clustered_permutation_test(
    actual: list | np.ndarray,
    predicted: list | np.ndarray,
    domains: list | np.ndarray,
    n_permutations: int = 200,
    seed: int = 42,
) -> tuple[float, list[float]]:
    """Compute empirical p-value under H0 using domain-level label permutations.
    
    Permutes domain identity labels across domains, preserving repeat clustering
    for the same domain. Evaluates against multi-seed predictions to match the
    reported multi-seed observed mean.
    """
    actual_arr = np.asarray(actual)
    pred_arr = np.asarray(predicted)
    domain_arr = np.asarray(domains)
    
    if pred_arr.ndim == 2:
        obs_acc = float(np.mean([np.mean(pred_arr[s] == actual_arr) for s in range(len(pred_arr))]))
    else:
        obs_acc = float(np.mean(pred_arr == actual_arr))
        
    unique_domains = np.unique(domain_arr)
    n_domains = len(unique_domains)
    if n_domains < 2:
        return (1.0, [obs_acc])
        
    rng = np.random.default_rng(seed)
    null_scores = np.empty(n_permutations, dtype=float)
    
    for b in range(n_permutations):
        permuted_domains = rng.permutation(unique_domains)
        domain_map = dict(zip(unique_domains, permuted_domains))
        permuted_labels = np.array([domain_map[d] for d in actual_arr])
        
        if pred_arr.ndim == 2:
            null_scores[b] = np.mean([np.mean(pred_arr[s] == permuted_labels) for s in range(len(pred_arr))])
        else:
            null_scores[b] = np.mean(pred_arr == permuted_labels)
            
    p_val = (1.0 + np.sum(null_scores >= obs_acc)) / (1.0 + n_permutations)
    return (float(p_val), null_scores.tolist())


def empirical_p_value(observed: float, null_scores: list[float]) -> float:
    """Compute empirical p-value from observed score and permutation null distribution."""
    if not null_scores:
        return float("nan")
    return (1.0 + sum(score >= observed for score in null_scores)) / (1.0 + len(null_scores))


def fdr_correction(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Benjamini-Hochberg False Discovery Rate (FDR) adjusted p-values."""
    p_arr = np.asarray(p_values, dtype=float)
    n = len(p_arr)
    if n == 0:
        return []
    order = np.argsort(p_arr)
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(1, n + 1)
    
    adj = p_arr * n / ranks
    sorted_adj = adj[order]
    for i in range(n - 2, -1, -1):
        sorted_adj[i] = min(sorted_adj[i], sorted_adj[i + 1])
    adj[order] = sorted_adj
    return [float(min(1.0, max(0.0, val))) for val in adj]
