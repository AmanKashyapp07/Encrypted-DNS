"""Leakage-safe, repeat-held-out domain fingerprinting evaluation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from .stats import (
    wilson_interval,
    domain_clustered_bootstrap,
    domain_clustered_permutation_test,
    empirical_p_value,
)

FEATURE_GROUPS = {
    "volume": ["n_pkts", "n_up", "n_down", "bytes_up", "bytes_down", "bytes_total", "ratio_bytes_down_up"],
    "size_stats": ["up_mean", "up_std", "up_max", "down_mean", "down_std", "down_max"],
    "timing": ["duration", "iat_mean", "iat_std", "iat_median", "iat_max", "t_first_down"],
    "bursts": ["n_bursts", "burst_len_mean", "burst_len_max", "burst_bytes_mean", "burst_bytes_max"],
    "handshake": [f"pkt_{index:02d}" for index in range(20)],
}


def available_features(frame: pd.DataFrame) -> list[str]:
    return [column for group in FEATURE_GROUPS.values() for column in group if column in frame.columns]


def select_headline_repeats(
    frame: pd.DataFrame,
    repeat_start: int = 8,
    repeat_end: int = 19,
    target_k: int = 10,
    split_strategy: str = "temporal_holdout",
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Select headline repeats and retain domains meeting evaluation criteria.
    
    In temporal_holdout:
      - Training repeats: repeat_start to repeat_end - 2 (e.g. 8 to 17, 10 repeats)
      - Testing repeats: repeat_end - 1 to repeat_end (e.g. 18 to 19, 2 repeats)
      - Retains all domains present in both training and test partitions with no
        random sampling across the train/test temporal boundary.
    """
    clean = frame[frame["repeat"].between(repeat_start, repeat_end)].copy()
    
    if split_strategy == "temporal_holdout":
        train_reps = set(range(repeat_start, repeat_end - 1))  # e.g., 8..17
        test_reps = set(range(repeat_end - 1, repeat_end + 1))  # e.g., 18..19
        
        train_domains = set(clean[clean["repeat"].isin(train_reps)]["domain"])
        test_domains = set(clean[clean["repeat"].isin(test_reps)]["domain"])
        kept = sorted(train_domains.intersection(test_domains))
        
        all_domains = sorted(clean["domain"].unique())
        dropped = {
            str(d): "missing in train (8-17) or test (18-19) partition"
            for d in all_domains if d not in kept
        }
        selected = clean[clean["domain"].isin(kept)].copy()
        return selected.reset_index(drop=True), dropped
    else:
        # kfold fallback: check >= target_k unique repeats
        counts = clean.groupby("domain")["repeat"].nunique()
        dropped = {
            str(domain): f"{int(count)} successful repeats; required {target_k}"
            for domain, count in counts.items()
            if count < target_k
        }
        kept = set(counts[counts >= target_k].index)
        selected = clean[clean["domain"].isin(kept)].copy()
        return selected.reset_index(drop=True), dropped


def evaluate(
    frame: pd.DataFrame,
    seeds: list[int] | None = None,
    permutations: int = 200,
    estimators: int = 100,
    features: list[str] | None = None,
    repeat_start: int = 8,
    repeat_end: int = 19,
    target_k: int = 10,
    workers: int = 1,
    split_strategy: str = "temporal_holdout",
) -> dict[str, float | int | str] | None:
    """Evaluate domain fingerprinting with strict temporal holdout and cluster-robust inference."""
    seeds = seeds or [17, 42, 101]
    features = features or available_features(frame)
    frame = frame.copy()
    frame["repeat"] = pd.to_numeric(frame["repeat"], errors="coerce")
    
    clean, dropped = select_headline_repeats(
        frame,
        repeat_start=repeat_start,
        repeat_end=repeat_end,
        target_k=target_k,
        split_strategy=split_strategy,
    )
    clean = clean.dropna(subset=features + ["domain", "repeat"]).copy()
    
    if clean.empty or clean["domain"].nunique() < 2 or clean["repeat"].nunique() < 2:
        return None
        
    if split_strategy == "temporal_holdout":
        train_reps = list(range(repeat_start, repeat_end - 1))
        test_reps = list(range(repeat_end - 1, repeat_end + 1))
        train = clean[clean["repeat"].isin(train_reps)].copy()
        test = clean[clean["repeat"].isin(test_reps)].copy()
        
        # Enforce that test domains exist in train
        known_domains = sorted(set(train["domain"]) & set(test["domain"]))
        train = train[train["domain"].isin(known_domains)]
        test = test[test["domain"].isin(known_domains)]
        
        if train.empty or test.empty:
            return None
            
        train_x = train[features].to_numpy(float)
        train_y = train["domain"].to_numpy()
        test_x = test[features].to_numpy(float)
        test_y = test["domain"].to_numpy()
        test_domains = test["domain"].to_numpy()
        
        seed_accs = []
        seed_top5 = []
        seed_f1 = []
        seed_preds = []
        
        for s in seeds:
            model = RandomForestClassifier(
                n_estimators=estimators,
                class_weight="balanced_subsample",
                random_state=s,
                n_jobs=-1,
            )
            model.fit(train_x, train_y)
            probs = model.predict_proba(test_x)
            preds = model.classes_[probs.argmax(axis=1)]
            
            acc = float(accuracy_score(test_y, preds))
            f1 = float(f1_score(test_y, preds, average="macro"))
            
            # Top-5 accuracy
            top5_indices = np.argsort(probs, axis=1)[:, -min(5, len(model.classes_)):]
            top5 = float(sum(test_y[i] in model.classes_[top5_indices[i]] for i in range(len(test_y))) / len(test_y))
            
            seed_accs.append(acc)
            seed_top5.append(top5)
            seed_f1.append(f1)
            seed_preds.append(preds)
            
        seed_preds_arr = np.array(seed_preds)  # shape (len(seeds), len(test_y))
        mean_accuracy = float(np.mean(seed_accs))
        
        # Domain-clustered bootstrap confidence interval for the 3-seed mean
        ci_boot_lo, ci_boot_hi = domain_clustered_bootstrap(
            actual=test_y,
            predicted=seed_preds_arr,
            domains=test_domains,
            n_bootstraps=1000,
            seed=42,
        )
        
        # Domain-clustered permutation test (evaluated on the exact same 3 seeds)
        p_val, null_scores = domain_clustered_permutation_test(
            actual=test_y,
            predicted=seed_preds_arr,
            domains=test_domains,
            n_permutations=permutations,
            seed=42,
        )
        
        return {
            "n": int(len(train) + len(test)),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "domains": int(len(known_domains)),
            "repeats_per_domain": target_k,
            "accuracy": mean_accuracy,
            "accuracy_seed_sd": float(np.std(seed_accs)),
            "ci_low": ci_boot_lo,
            "ci_high": ci_boot_hi,
            "ci_boot_low": ci_boot_lo,
            "ci_boot_high": ci_boot_hi,
            "top5": float(np.mean(seed_top5)),
            "macro_f1": float(np.mean(seed_f1)),
            "chance": float(1.0 / len(known_domains)),
            "p_value": float(p_val),
            "n_permutations": len(null_scores),
            "split_strategy": "temporal_holdout",
            "train_repeats": f"{repeat_start}-{repeat_end - 2}",
            "test_repeats": f"{repeat_end - 1}-{repeat_end}",
            "dropped_domains": "; ".join(
                f"{d} ({r})" for d, r in sorted(dropped.items())
            ),
        }
    else:
        # k-fold fallback if explicitly requested
        repeats = sorted(clean["repeat"].unique())
        folds = [repeats[idx:idx + 2] for idx in range(0, len(repeats), 2)]
        all_fold_accs = []
        for held_out in folds:
            tr = clean[~clean["repeat"].isin(held_out)]
            te = clean[clean["repeat"].isin(held_out)]
            known = sorted(set(tr["domain"]) & set(te["domain"]))
            tr = tr[tr["domain"].isin(known)]
            te = te[te["domain"].isin(known)]
            if tr.empty or te.empty:
                continue
            tr_x = tr[features].to_numpy(float)
            tr_y = tr["domain"].to_numpy()
            te_x = te[features].to_numpy(float)
            te_y = te["domain"].to_numpy()
            fold_seed_accs = []
            for s in seeds:
                m = RandomForestClassifier(n_estimators=estimators, class_weight="balanced_subsample", random_state=s, n_jobs=-1)
                m.fit(tr_x, tr_y)
                preds = m.predict(te_x)
                fold_seed_accs.append(accuracy_score(te_y, preds))
            all_fold_accs.append(np.mean(fold_seed_accs))
            
        mean_acc = float(np.mean(all_fold_accs)) if all_fold_accs else float("nan")
        return {
            "n": int(len(clean)),
            "domains": int(clean["domain"].nunique()),
            "accuracy": mean_acc,
            "chance": float(1.0 / clean["domain"].nunique()),
            "split_strategy": "kfold",
        }
