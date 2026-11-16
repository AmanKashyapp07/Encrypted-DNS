# Encrypted-DNS Research Remediation Plan: Statistical Rigor, Reproducibility, and Publication Integrity

**Document Status:** Final Actionable Implementation Plan  
**Target Standard:** Academic Peer-Review (ACM IMC, USENIX Security, PETS)  
**Target Repository:** `AmanKashyapp07/Encrypted-DNS`  
**Author:** Senior Research Software Engineer & Academic Reproducibility Reviewer  
**Date:** November 16, 2026  

---

## 1. Executive Summary

This document presents a comprehensive, evidence-based remediation plan for the `Encrypted-DNS` research repository. The project studies privacy leakage and website fingerprinting resistance in encrypted DNS traffic, comparing DNS-over-HTTPS (DoH, HTTP/2) and DNS-over-HTTP/3 (DoH/3, QUIC) across residential broadband (Airtel FTTH) and mobile cellular (Reliance Jio) access networks.

While the repository contains authentic, large-scale empirical traffic measurements (26,262 raw capture attempts yielding 20,838 usable feature-extracted DNS flows), a forensic audit reveals **fundamental methodological divergences between the documented evaluation protocols and the executing code, broken provenance chains in the claims ledger, missing dataset artifacts in clean clones, hardcoded presentation figures, and unsubstantiated causal claims in the research paper draft.**

### Key Audit Findings
1. **Evaluation Split Discrepancy:** The paper and methodology documents assert that headline results were evaluated on a fixed temporal holdout (training on repeats 8–17, testing on repeats 18–19). In reality, `src/encdns/analysis/fingerprinting.py` executes a 5-fold cross-validation over randomly sampled repeat pairs, violating the documented temporal holdout protocol.
2. **Asymmetric Permutation Testing:** Permutation null models use 50 decision trees, whereas observed models use 100 decision trees. Furthermore, the test shuffles training labels rather than test labels or joint exchangeable units, and tests against a single seed rather than the three-seed mean, introducing systematic bias into the empirical null distribution.
3. **Invalid Uncertainty Estimation:** Reported Wilson confidence intervals treat repeated queries for the same domain as independent Bernoulli trials. Because multiple queries for the same domain exhibit intra-cluster correlation, naive Wilson intervals artificially understate uncertainty. Moreover, intervals are taken from the first random seed rather than accounting for inter-seed variation.
4. **Data Availability Breakdown:** `data/processed/dataset_jio.csv`, `data/processed/dataset_combined.csv`, and all `results/` directories (except `results/figures/`) are excluded by `.gitignore` and untracked in Git. A clean `git clone` fails automated verification immediately on step 1.
5. **Claims Ledger Mismatches & Fabrications:** Claim `ML-2` reports an XGBoost accuracy of `0.248` citing `e1_protocol_id.csv` and `src/analysis_v2.py`. In reality, `e1_protocol_id.csv` contains binary Random Forest protocol identification results with accuracy `0.9999`. No XGBoost fingerprinting evaluation output exists in the repository. Furthermore, pooled training claims (`POOL-1` through `POOL-4`) conflate combined multi-network test sets with individual access network evaluations.
6. **Hardcoded Visualizations:** Three of four publication figures in `scripts/plot_slide_figures.py` hardcode static Python lists rather than loading result CSVs dynamically, omit confidence intervals, and assert unverified causal claims ("100% BLOCKED by Carrier Gateway").
7. **Unsubstantiated Causal Language:** The paper draft claims that carrier middleboxes actively filter UDP port 443, that browsers silently fall back to older protocols, and that cellular radio scheduling and MTU clamping cause distribution shifts—none of which were directly measured or experimentally isolated.

This remediation plan establishes a strict, phased roadmap to resolve every identified issue without altering the original raw datasets or inflating classification results.

---

## 2. Repository Audit Findings & Evidence

Every finding in this section was independently verified by inspecting the codebase, configuration files, version control trees, and result CSVs.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   END-TO-END DATA FLOW                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
 [Raw PCAPs: Airtel/Jio] ──> [src/extract_features.py] ──> [data/processed/dataset_*.csv]
                                                                     │
          ┌──────────────────────────────────────────────────────────┴───────────────┐
          ▼                                                                          ▼
 [src/encdns/cli.py]                                                     [scripts/run_jio_analysis.py]
  └── fingerprinting.evaluate()                                           └── run_n1() .. run_n8()
      ├── 5-fold CV (10 repeats)                                              ├── Leave-2-out CV
      ├── RF (100 trees, 3 seeds)                                             ├── RF (100 trees, 3 seeds)
      └── Null RF (50 trees, 1 seed)                                          └── Null RF (50 trees, 1 seed)
          │                                                                          │
          ▼                                                                          ▼
 [results/airtel_topup_20261113/]                                        [results/jio_analysis_20261113/]
  └── rq1_rq2_fingerprinting.csv                                          └── n1_*.csv .. n8_*.csv
          │                                                                          │
          └──────────────────────────┬───────────────────────────────────────────────┘
                                     ▼
                         [docs/claims_ledger.csv]
                          (39 Claims with Hashes)
                                     │
          ┌──────────────────────────┴───────────────────────────────┐
          ▼                                                          ▼
 [scripts/plot_slide_figures.py]                                [docs/paper.md & readme.md]
  (3 of 4 figures hardcoded)                                    (Causal claims, placeholders)
```

### 2.1 Statistical Methodology & Model Evaluation

#### Issue STAT-1: Evaluation Split Divergence (Documented vs. Implemented)
- **File & Function:** `src/encdns/analysis/fingerprinting.py:select_headline_repeats` and `_evaluate`
- **Observed Code Behavior:** 
  In `select_headline_repeats` (lines 28–31), domains with $\ge 10$ repeats in range [8, 19] are randomly sampled down to exactly 10 repeats using fixed seed 17:
  ```python
  sampled = [group.sample(n=target_k, random_state=17) for _, group in selected.groupby("domain", sort=False)]
  ```
  In `_evaluate` (lines 43–45), the code partitions the 10 repeats into 5 two-repeat folds and performs complete 5-fold cross-validation:
  ```python
  repeats = sorted(clean.repeat.unique())
  folds = [repeats[index:index + 2] for index in range(0, len(repeats), 2)]
  for held_out in folds:
      train, test = clean[~clean.repeat.isin(held_out)], clean[clean.repeat.isin(held_out)]
  ```
- **Discrepancy:** `docs/methodology.md` (lines 12–15) and `docs/paper.md` state:
  > *"Headline Airtel Evaluation: Queries from repeats 8–17 (10 repeats per domain) form the training set; queries from held-out repeats 18–19 form the evaluation test set."*
- **Impact:** Critical. The reported accuracy represents average 5-fold out-of-fold generalization across randomly subsampled repeats, not the documented temporal holdout on future repeats 18–19. The paper makes claims about a temporal holdout that was never run.

#### Issue STAT-2: Asymmetric Null Distribution in Permutation Testing
- **File & Function:** `src/encdns/analysis/fingerprinting.py:evaluate` (lines 84–96) and `scripts/run_jio_analysis.py:run_n1` (lines 108–115)
- **Observed Code Behavior:**
  In `fingerprinting.py`:
  - Observed models are trained with `estimators=100` across three seeds (`17, 42, 101`):
    ```python
    observed = Parallel(n_jobs=workers)(delayed(_evaluate)(frame, features, seed, 100) for seed in seeds)
    ```
  - Permutation null models are trained with `estimators=50` across a single seed stream:
    ```python
    null_results = Parallel(n_jobs=workers)(delayed(_evaluate)(frame, features, seeds[0] + 10000 + index, 50, True) for index in range(permutations))
    ```
  In `run_jio_analysis.py`:
  - Observed models use `n_estimators=100` (line 97); null models use `n_estimators=50` (line 112).
- **Impact:** Critical. Reducing tree count from 100 to 50 in the null model increases estimator variance in the null distribution, altering the empirical critical values and biasing the empirical p-value computation. The null and observed estimators must be strictly identical under $H_0$.

#### Issue STAT-3: Label Permutation Mechanism Scrambles Training Labels Only
- **File & Function:** `src/encdns/analysis/fingerprinting.py:_evaluate` (lines 46–48)
- **Observed Code Behavior:**
  ```python
  labels = train.domain.to_numpy()
  if permute:
      labels = rng.permutation(labels)
  ```
- **Statistical Issue:** The permutation test shuffles only the training fold labels, leaving test fold labels untouched. While this tests whether the model can memorize randomized training patterns, the classical hypothesis test for supervised exchangeability under $H_0: P(Y|X) = P(Y)$ requires permuting the ground-truth labels across the test set (or globally before feature-label alignment) to establish the empirical null prediction rate on intact test data.

#### Issue STAT-4: Single-Seed Confidence Interval Reporting & Clustered Data Violation
- **File & Function:** `src/encdns/analysis/fingerprinting.py:evaluate` (lines 97–102) and `scripts/run_jio_analysis.py:run_n1` (lines 103–104)
- **Observed Code Behavior:**
  In `fingerprinting.py`:
  ```python
  reference = observed[0]
  # ...
  "ci_low": float(reference["ci_low"]), "ci_high": float(reference["ci_high"])
  ```
  In `run_jio_analysis.py`:
  ```python
  k = int(round(mean_acc * len(test)))
  lo, hi = wilson_interval(k, len(test))
  ```
- **Statistical Issue:** 
  1. The reported confidence intervals reflect only the first random seed (`observed[0]`), discarding inter-seed model variance.
  2. In `run_jio_analysis.py`, Wilson intervals are calculated using an artificial pseudo-count `round(mean_acc * len(test))` rather than true successes.
  3. **Cluster Violation:** The test sets contain multiple repeats of the same domains (e.g., 2 repeats per domain $\times$ 100 domains = 200 queries). Queries for the same domain share network routing, resolver answer structures, and record counts. Treating them as independent Bernoulli trials violates the fundamental independence assumption of the Wilson score interval, yielding confidence intervals that are artificially narrow.

#### Issue STAT-5: Pooled Training Accounting & Test Set Conflation
- **File & Function:** `scripts/run_jio_analysis.py:run_n3` (lines 198–225)
- **Observed Code Behavior:**
  Line 209 iterates over three evaluation targets:
  ```python
  for test_net, te_df in [
      ("Airtel (held-out)", a_te),
      ("Jio (held-out)", j_te),
      ("Combined (held-out)", pd.concat([a_te, j_te]))
  ]:
  ```
  In `docs/claims_ledger.csv`, claims `POOL-1` through `POOL-4` record the `Combined (held-out)` accuracy values (0.1733, 0.1785, 0.1733, 0.1695) under the network label `Airtel` or without clarifying that this metric is an artificial composite of the two primary test sets.
- **Statistical Issue:** High. The combined test set is an exact linear combination of `a_te` and `j_te`. Presenting it as a third independent experimental finding alongside its components represents redundant data accounting.

---

### 2.2 Reproducibility, Ledger Provenance & Data Availability

#### Issue REPRO-1: Clean-Clone Pipeline Failure (.gitignore Exclusions)
- **File:** `.gitignore` (lines 49–53)
- **Observed Behavior:**
  ```gitignore
  !data/processed/
  data/processed/*
  !data/processed/dataset.csv
  results/*
  !results/figures/
  ```
  Inspection of Git tracking via `git ls-files` reveals:
  - `data/processed/dataset_jio.csv` is **UNTRACKED**.
  - `data/processed/dataset_combined.csv` is **UNTRACKED**.
  - `results/airtel_topup_20261113/` is **UNTRACKED**.
  - `results/jio_analysis_20261113/` is **UNTRACKED**.
  - `results/airtel_all_20261113/` is **UNTRACKED**.
  - `results/airtel_advanced_20261113/` is **UNTRACKED**.
- **Impact:** Critical. Anyone cloning this repository from GitHub cannot run `python3 scripts/verify_research_results.py`, cannot run `python3 scripts/run_jio_analysis.py`, and cannot inspect the raw CSV outputs backing the claims ledger.

#### Issue REPRO-2: Claim ML-2 Mismatch & Fabrication in Claims Ledger
- **File:** `docs/claims_ledger.csv` (row 37, claim ID `ML-2`)
- **Recorded Claim Entry:**
  ```csv
  ML-2,XGBoost Top-1 accuracy on AdGuard DoH Global,0.248,Top-1 Accuracy,Airtel,adguard,doh,global,200,"[0.2160, 0.2830]",e1_protocol_id.csv,python src/analysis_v2.py,70cb017100bddbbfee5dacbb5ffac4903cb4cdbd
  ```
- **Forensic Verification:** 
  Inspection of `results/airtel_advanced_20261113/e1_protocol_id.csv` shows it contains:
  ```csv
  task,model,n,majority_baseline,accuracy,acc_sd_over_seeds,macro_f1
  DoH vs DoH3 (All Resolvers),rf,18926,0.5013,0.9999,0.0,0.9999
  DoH vs DoH3 (AdGuard),rf,4629,0.5005,1.0,0.0,1.0
  ```
  `e1_protocol_id.csv` evaluates binary Random Forest protocol classification (DoH vs. DoH/3), achieving accuracy 1.000. It does **not** evaluate XGBoost, does **not** evaluate 100-class domain fingerprinting, and contains **no** entry with value 0.248. No CSV in the repository contains the result claimed in `ML-2`.
- **Impact:** Critical scientific integrity failure. A headline model comparison claim cited in the README, paper, and verifier has an erroneous provenance pointer.

#### Issue REPRO-3: Superficial Verification Suite (`scripts/verify_research_results.py`)
- **File:** `scripts/verify_research_results.py`
- **Observed Behavior:**
  - Check `[6/6]` (`verify_claims_ledger`) checks only whether column headers exist and whether `commit != 'unrecorded'`. It **never opens the source CSVs** to check whether reported values match the underlying data.
  - Check `[1/6]` and `[5/6]` hardcode magic constants (`18926`, `1912`, `20838`, `0.0101`, `0.0135`).
  - The script prints `"ALL 6 RESEARCH VERIFICATION CHECKS PASSED (100% REPRODUCIBLE)"` despite the fact that `ML-2` is completely unverified.
- **Impact:** High. False assurance of reproducibility.

---

### 2.3 Figure Generation Integrity

#### Issue FIG-1: Hardcoded Experimental Numbers in `scripts/plot_slide_figures.py`
- **File:** `scripts/plot_slide_figures.py`
- **Observed Behavior:**
  - `plot_headline_airtel` (lines 43–48): Hardcodes static Python lists:
    ```python
    doh_global = [0.262, 0.236, 0.175, 0.342]
    doh3_global = [0.089, 0.060, 0.169, 0.046]
    doh_india = [0.233, 0.195, 0.148, 0.310]
    doh3_india = [0.092, 0.053, 0.101, 0.051]
    ```
  - `plot_cross_network` (lines 85–88): Hardcodes within-network and transfer accuracies.
  - `plot_carrier_blocking` (lines 116–117): Hardcodes completion rates `[98.5, 96.8, 95.3, 0.0]`.
- **Impact:** High. Figures are decoupled from the data pipeline. If models are retrained or data is updated, figures remain frozen and misleading.
- **Missing Elements:** Figure 1 plots bar charts with zero confidence intervals or error bars, failing basic academic publication guidelines.

#### Issue FIG-2: Unsubstantiated Text Annotations in Figures
- **File:** `scripts/plot_slide_figures.py:plot_carrier_blocking` (line 135)
- **Observed Code:**
  ```python
  ax.text(3, 10, "100% BLOCKED\nby Carrier Gateway", ha="center", color="#d62728", weight="bold", fontsize=11)
  ```
- **Scientific Issue:** High. The measurement harness observes client-side query timeouts (0 packets returned). Annotating this as `"100% BLOCKED by Carrier Gateway"` asserts a specific infrastructure cause (carrier middlebox gateway block) without packet-level traceroutes or middlebox isolation experiments.

---

### 2.4 Research Claims, Academic Tone & Paper Quality

#### Issue PAPER-1: Unsubstantiated Causal Language in `docs/paper.md` and `readme.md`
- **Locations:** `docs/paper.md` (Abstract, Section 1, Section 5.4) and `readme.md` (Section 2, Section 5)
- **Specific Problematic Statements:**
  1. *"demonstrating that real-world carrier middleboxes filter outbound UDP port 443, silently forcing user agents into higher-leakage fallback protocols."*
     - **Flaw:** Browser fallback was not tested. Middlebox gateway filtering was not isolated from potential APN-level firewalling, NAT mapping timeouts, or handset OS tethering behavior.
  2. *"dropping to 0.016–0.024 ... due to cellular radio scheduling, MTU clamping, and transport shifts."*
     - **Flaw:** While KS tests show distribution shifts in packet sizes and timing, no link-layer measurement of LTE/5G Radio Resource Control (RRC) states or Path MTU Discovery was conducted.
  3. *"All 16 resolver-protocol-workload slices on Airtel are significantly above chance ($p < 0.005$)."*
     - **Flaw:** The permutation test used to establish this claim was asymmetric (50 trees vs 100 trees) and permuted only training labels.

#### Issue PAPER-2: Unresolved Citation Placeholders in `docs/paper.md`
- **Location:** `docs/paper.md` (lines 3, 23, 62, 70, 74)
- **Unresolved Markers:**
  - Line 3: `**Authors:** [Author Names]`
  - Line 23: `Siby et al. [CITE: CCS 2020]`
  - Line 62: `Herrmann et al. [CITE]`, `[CITE: NDSS, CCS]`, `DefProxy [CITE]`, `WTF-PAD [CITE]`, `Tamaraw [CITE]`
  - Line 70: `Hoang et al. [CITE]`, `Lu et al. [CITE]`, `Sy et al. [CITE]`
  - Line 74: `Jain et al. [CITE]`
- **Impact:** Medium. Incomplete academic manuscript state.

---

### 2.5 Configuration & Dependency Inconsistencies

#### Issue CONF-1: Stale Network States in `config/project.yaml`
- **File:** `config/project.yaml` (lines 6–8, line 21)
- **Observed Behavior:**
  ```yaml
  networks:
    airtel: complete
    jio: pending
    campus: pending
  paths:
    manifest: data/raw/manifest.csv
  ```
  `jio` is marked as `pending` even though Jio data is fully captured and analyzed. `campus` is marked `pending` despite being permanently cancelled. `data/raw/manifest.csv` does not exist at that path.

#### Issue CONF-2: Python Version Specification Conflict
- **Locations:** `pyproject.toml` (line 9) vs `readme.md` (lines 5, 124)
- **Discrepancy:** `pyproject.toml` enforces `requires-python = ">=3.10"`. `readme.md` specifies `Python 3.9+`.

---

## 3. Verified vs. Unverified Audit Findings Matrix

| Finding from Preliminary Audit | Status | Verified Evidence & Code Location |
| :--- | :--- | :--- |
| **1. Permutation test shuffles train labels, not test labels** | **VERIFIED** | `src/encdns/analysis/fingerprinting.py:48`: `labels = rng.permutation(labels)` where `labels` is extracted from `train.domain`. |
| **2. Observed and null models use different tree counts** | **VERIFIED** | `fingerprinting.py:85` (100 trees) vs `fingerprinting.py:93` (50 trees); `run_jio_analysis.py:97` (100 trees) vs `run_jio_analysis.py:112` (50 trees). |
| **3. Observed averages 3 seeds; null uses 1 seed stream** | **VERIFIED** | `fingerprinting.py:90` (`np.mean` over 3 seeds) vs `fingerprinting.py:93` (null uses single seed `seeds[0] + 10000 + index`). |
| **4. Confidence intervals taken from first seed only** | **VERIFIED** | `fingerprinting.py:97, 102`: `reference = observed[0]` and `"ci_low": float(reference["ci_low"])`. |
| **5. Evaluation split does not match documented 8–17 / 18–19** | **VERIFIED** | `fingerprinting.py:43`: `folds = [repeats[index:index + 2] ...]` executes 5-fold CV across sampled repeats, not fixed holdout 18–19. |
| **6. N1 permutation test uses 50 trees vs 100 in observed** | **VERIFIED** | `run_jio_analysis.py:97` (default 100) vs `run_jio_analysis.py:112` (`n_estimators=50`). |
| **7. N1 CI calculated on rounded mean accuracy pseudo-counts** | **VERIFIED** | `run_jio_analysis.py:103`: `k = int(round(mean_acc * len(test)))`; Wilson computed on `k`. |
| **8. Cross-network CIs ignore seed variance** | **VERIFIED** | `run_jio_analysis.py:161–162`: `wilson_interval(int(round(mean_acc * len(test_df))), len(test_df))` ignores inter-seed SD. |
| **9. Pooled training repeats and test-set accounting unclear** | **VERIFIED** | `run_jio_analysis.py:209`: `Combined (held-out)` concatenates `a_te` and `j_te`, creating an overlapping third slice. |
| **10. Wilson intervals inappropriate for repeated domain queries** | **VERIFIED** | Multiple queries per domain violate independent Bernoulli trials assumption. |
| **11. Verifier checks schema, not actual ledger values** | **VERIFIED** | `scripts/verify_research_results.py:163–180` checks columns and commit string, never reads `source_csv`. |
| **12. Dataset verifier relies on hardcoded row counts** | **VERIFIED** | `verify_research_results.py:42, 48, 52` hardcodes `18926`, `1912`, `20838`. |
| **13. Datasets and result CSVs missing from clean clone** | **VERIFIED** | `.gitignore:49–53` excludes `dataset_jio.csv`, `dataset_combined.csv`, and `results/*`. |
| **14. Claim ML-2 has wrong source CSV and script** | **VERIFIED** | `claims_ledger.csv:37` maps ML-2 (XGBoost 0.248) to `e1_protocol_id.csv` (RF binary classification 0.9999). |
| **15. Figures 1, 2, 3 use hardcoded values** | **VERIFIED** | `scripts/plot_slide_figures.py:43–48, 85–88, 116–117` hardcode static Python lists. |
| **16. Fig 1 lacks confidence intervals** | **VERIFIED** | `plot_slide_figures.py:56–69` renders plain bar charts with no `yerr`. |
| **17. Carrier blocking claims unsupported by evidence** | **VERIFIED** | `paper.md:14` and `plot_slide_figures.py:135` assert middlebox blocking without path isolation. |
| **18. Stale configs and Python version conflicts** | **VERIFIED** | `config/project.yaml` marks Jio pending; `pyproject.toml` (>=3.10) conflicts with `readme.md` (3.9+). |

---

## 4. Severity-Ranked Issue Register

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             ISSUE SEVERITY BREAKDOWN                             │
└──────────────────────────────────────────────────────────────────────────────────┘
  CRITICAL (Must fix before any academic submission; invalidates conclusions/repro)
  ├── STAT-1: Evaluation split discrepancy (5-fold CV vs documented 18–19 holdout)
  ├── STAT-2: Asymmetric tree count in permutation testing (100 vs 50 trees)
  ├── REPRO-1: Processed datasets & result CSVs missing from Git clone (.gitignore)
  └── REPRO-2: Claim ML-2 provenance failure in claims ledger (XGBoost vs RF)

  HIGH (Methodological & presentation flaws that undermine credibility)
  ├── STAT-3: Permutation test permuting training labels instead of test/global labels
  ├── STAT-4: Single-seed CI reporting & clustered repeat violation
  ├── STAT-5: Pooled training overlapping test set accounting
  ├── FIG-1:  Hardcoded floating-point values in slide figure generation
  ├── FIG-2:  Unsubstantiated "Blocked by Carrier Gateway" visual annotations
  ├── REPRO-3: Superficial claims verification script (does not check numerical values)
  └── PAPER-1: Unsubstantiated causal language regarding middleboxes & radio scheduling

  MEDIUM (Documentation, configuration, and reproducibility friction)
  ├── CONF-1: Stale `pending` statuses in `config/project.yaml`
  ├── CONF-2: Python version mismatch (>=3.10 in pyproject vs 3.9+ in readme)
  └── PAPER-2: Unresolved citation placeholders (`[CITE]`, `[Author Names]`) in paper draft
```

---

## 5. Statistical Methodology Recommendations

### 5.1 Evaluation Split Protocol: Fixed Temporal Holdout vs. K-Fold CV
- **Background:** Encrypted DNS exhibits high temporal autocorrelation: queries executed within minutes of each other share transient resolver caching states, local ISP queue depths, and CDN edge routes.
- **Comparison:**
  - *Option A: Documented Fixed Temporal Holdout (Repeats 8–17 train, 18–19 test).* Strictly preserves temporal separation. Reflects realistic attacker scenario: training on past captures, testing on future queries.
  - *Option B: 5-Fold Leave-Two-Repeats-Out Cross-Validation (Current Code).* Evaluates across all 10 repeats by holding out 2 repeats at a time. Yields lower estimator variance across the 100 domains, but averages results across folds where the "test" fold occurred earlier in time than the "train" fold.
- **Recommendation:** **Adopt Option A (Strict Temporal Holdout: Train Repeats 8–17, Test Repeats 18–19) as the Primary Headline Evaluation.** Provide Option B (5-Fold Leave-Two-Repeats-Out CV) as an explicit robustness check in the supplementary materials/appendix. Re-run both pipelines deterministically and document their exact distinction.

### 5.2 Proper Permutation Testing Design under $H_0$
- **The Stated Null Hypothesis ($H_0$):** Traffic metadata features $X$ contain no predictive information regarding the queried domain label $Y$ ($P(Y|X) = P(Y)$).
- **Flaws in Current Implementation:**
  1. Shuffling only `train["domain"]` forces the classifier to fit random noise on the training set, while evaluating against non-shuffled test labels.
  2. Training with 50 trees under the null and 100 trees under the observed condition artificially inflates null variance.
- **Recommended Procedure:**
  1. Fix `n_estimators=100` identically for observed and null models.
  2. For each of $B = 200$ permutation iterations:
     - Keep the feature matrix $X$ intact.
     - Permute domain labels $Y$ uniformly across the entire evaluation dataset (or permute test labels $Y_{\text{test}}$ while keeping the marginal class distribution intact).
     - Fit the model using the exact same multi-seed pipeline.
     - Compute the empirical p-value as:
       $$p = \frac{1 + \sum_{b=1}^B \mathbb{I}(\text{Acc}_b^{\text{null}} \ge \text{Acc}^{\text{obs}})}{1 + B}$$

### 5.3 Uncertainty Estimation: Domain-Clustered Block Bootstrap
- **Flaw in Wilson Interval:** The Wilson score interval assumes independent Bernoulli trials:
  $$\text{Var}(\hat{p}) = \frac{p(1-p)}{N}$$
  However, queries for the same domain are clustered. If a domain has a distinctive packet size (e.g., Google DoH unpadded records), all repeats for that domain succeed or fail together. Naive Wilson intervals treat $N = 200$ queries as 200 independent trials, severely underestimating the true standard error.
- **Recommended Procedure (Cluster-Robust Uncertainty):**
  Implement a **Domain-Clustered Block Bootstrap**:
  1. Let $\mathcal{D} = \{d_1, d_2, \dots, d_K\}$ be the set of $K$ candidate domains ($K = 100$ or $50$).
  2. In each bootstrap replicate $m = 1, \dots, M$ ($M = 1000$):
     - Resample $K$ domains *with replacement* from $\mathcal{D}$.
     - Include all associated test queries for the sampled domains.
     - Compute test accuracy $\hat{p}_m$.
  3. Form the 95% confidence interval using the empirical 2.5th and 97.5th percentiles of $\{\hat{p}_m\}_{m=1}^M$.
  4. Compare with the multi-seed mean accuracy $\bar{p} = \frac{1}{S}\sum_{s=1}^S \hat{p}_s$.

### 5.4 Multiple Comparisons Control
- Evaluating 16 independent slices (4 resolvers $\times$ 2 protocols $\times$ 2 workloads) requires controlling the Family-Wise Error Rate (FWER) or False Discovery Rate (FDR).
- **Recommendation:** Apply **Benjamini-Hochberg (BH) FDR correction** across the 16 empirical p-values at $\alpha = 0.05$. Document both unadjusted and adjusted p-values in the paper and claims ledger.

---

## 6. Phased Implementation Plan

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASED EXECUTION ROADMAP                               │
└──────────────────────────────────────────────────────────────────────────────────────┘
  PHASE 1: Statistical Correctness & Evaluation Engines
  ├── T1.1: Refactor `src/encdns/analysis/fingerprinting.py` (holdout, symmetric null)
  ├── T1.2: Implement Cluster-Robust Domain Bootstrap in `stats.py`
  ├── T1.3: Refactor `scripts/run_jio_analysis.py` (N1 symmetric null, N3 pooled fix)
  └── T1.4: Resolve XGBoost evaluation implementation in `src/analysis_v2.py`
           │
           ▼
  PHASE 2: Data Governance, Provenance & Verification
  ├── T2.1: Overhaul `.gitignore` to track processed CSV datasets
  ├── T2.2: Audit and regenerate complete `docs/claims_ledger.csv`
  └── T2.3: Re-engineer `scripts/verify_research_results.py` for end-to-end data checks
           │
           ▼
  PHASE 3: Result & Figure Regeneration
  ├── T3.1: Re-execute Airtel headline analysis (`python -m encdns analyze`)
  ├── T3.2: Re-execute Jio and Cross-Network analysis (`scripts/run_jio_analysis.py`)
  ├── T3.3: Re-execute Sequence & Scaling models (`scripts/run_airtel_all.py`)
  └── T3.4: Overhaul `scripts/plot_slide_figures.py` to bind dynamically to CSVs
           │
           ▼
  PHASE 4: Manuscript & Documentation Alignment
  ├── T4.1: Neutralize causal language in `docs/paper.md` and `readme.md`
  ├── T4.2: Resolve citation placeholders with authoritative bibliography
  └── T4.3: Synchronize abstract, tables, and text with regenerated numbers
           │
           ▼
  PHASE 5: Repository Hardening & CI Validation
  ├── T5.1: Synchronize `config/project.yaml` and `pyproject.toml`
  ├── T5.2: Add unit tests for bootstrap, permutation, and ledger validator
  └── T5.3: Execute clean-clone reproduction test from scratch
```

---

### Phase 1: Statistical Correctness & Evaluation Engines

#### Task 1.1: Refactor `fingerprinting.py` Evaluation Split and Symmetric Permutation Testing
- **Files to Modify:** `src/encdns/analysis/fingerprinting.py`
- **Proposed Changes:**
  1. Add parameter `split_strategy: Literal["temporal_holdout", "kfold"] = "temporal_holdout"`.
     - In `"temporal_holdout"`: Strictly partition `train = frame[frame.repeat.between(8, 17)]` and `test = frame[frame.repeat.between(18, 19)]`.
     - In `"kfold"`: Execute 5-fold cross-validation on 2-repeat folds (for sensitivity comparison).
  2. Fix tree asymmetry: Set `estimators=100` identically for observed models and permutation null models.
  3. Redesign permutation test: Permute test labels $Y_{\text{test}}$ across the intact feature matrix $X_{\text{test}}$, or permute labels across the dataset prior to fitting, ensuring the null model evaluates under exchangeability.
  4. Average null distributions across all evaluation seeds rather than a single seed stream.
- **Expected Output:** Clean, unbiased accuracy estimates and valid empirical p-values.
- **Acceptance Criteria:** Permutation null tree count equals observed tree count (100); observed pipeline and null pipeline use identical feature subsets and splits.
- **Dependencies:** None.
- **Complexity:** Medium.

#### Task 1.2: Implement Domain-Clustered Block Bootstrap in `src/encdns/analysis/stats.py`
- **Files to Modify:** `src/encdns/analysis/stats.py`
- **Proposed Changes:**
  1. Implement `domain_clustered_bootstrap(y_true, y_pred, domains, n_bootstraps=1000, alpha=0.05, seed=42)`.
  2. Implement Benjamini-Hochberg FDR correction helper: `fdr_correction(p_values, alpha=0.05)`.
- **Expected Output:** Robust 95% confidence intervals that account for intra-domain correlation.
- **Acceptance Criteria:** Bootstrap intervals are wider than naive Wilson intervals when intra-domain accuracy correlation is positive.
- **Dependencies:** Task 1.1.
- **Complexity:** Small.

#### Task 1.3: Refactor `scripts/run_jio_analysis.py` (N1, N2, N3)
- **Files to Modify:** `scripts/run_jio_analysis.py`
- **Proposed Changes:**
  1. In `run_n1`: Set `n_estimators=100` for permutation baseline (matching observed model). Replace pseudo-count Wilson CI with domain-clustered bootstrap.
  2. In `run_n2`: Add domain-clustered bootstrap for cross-network transfer estimates.
  3. In `run_n3`: Eliminate the redundant `Combined (held-out)` test set from the primary result rows, or explicitly label it as `Airtel+Jio Composite Test Set (Non-Independent)`. Clarify repeat ranges for Airtel vs. Jio.
- **Expected Output:** Consistent methodology between broadband and cellular scripts.
- **Acceptance Criteria:** `run_jio_analysis.py` runs without hardcoded tree counts or unweighted pseudo-intervals.
- **Dependencies:** Task 1.2.
- **Complexity:** Medium.

#### Task 1.4: Resolve XGBoost Evaluation Pipeline in `src/analysis_v2.py`
- **Files to Modify:** `src/analysis_v2.py`
- **Proposed Changes:**
  1. Create an explicit function `run_model_comparison(df, out)` that trains Random Forest, XGBoost, and baseline models on the exact same AdGuard DoH Global slice (repeats 8–17 train, 18–19 test).
  2. Save results directly to `results/airtel_advanced_20261113/model_comparison.csv`.
- **Expected Output:** Legitimate, reproducible CSV artifact backing the XGBoost 24.8% claim.
- **Acceptance Criteria:** Generated CSV contains model names, parameters, seed scores, and verified accuracy.
- **Dependencies:** None.
- **Complexity:** Small.

---

### Phase 2: Data Governance, Provenance & Verification

#### Task 2.1: Overhaul `.gitignore` and Track Processed Datasets
- **Files to Modify:** `.gitignore`
- **Proposed Changes:**
  1. Whitelist essential preprocessed datasets:
     ```gitignore
     !data/processed/dataset_v2.csv
     !data/processed/dataset_jio.csv
     !data/processed/dataset_combined.csv
     !data/processed/drop_reasons_v2.csv
     !data/processed/drop_reasons_jio.csv
     ```
  2. Whitelist core result CSVs:
     ```gitignore
     !results/airtel_topup_20261113/*.csv
     !results/jio_analysis_20261113/*.csv
     !results/airtel_all_20261113/*.csv
     !results/airtel_advanced_20261113/*.csv
     ```
  3. Keep raw PCAPs (`*.pcap`, `data/raw/*`) excluded to preserve repository lightness.
- **Expected Output:** Clean git clones immediately contain all processed datasets and baseline results.
- **Acceptance Criteria:** `git status` displays required CSVs for staging; repo clone size remains under 50 MB.
- **Dependencies:** None.
- **Complexity:** Small.

#### Task 2.2: Audit and Regenerate `docs/claims_ledger.csv`
- **Files to Modify:** `docs/claims_ledger.csv`
- **Proposed Changes:**
  1. Re-map claim `ML-2` to `model_comparison.csv` generated by Task 1.4.
  2. Update `POOL-1` through `POOL-4` to explicitly reflect the exact test network evaluated (`Airtel held-out`, `Jio held-out`, or `Combined composite`).
  3. Update all confidence intervals to reflect the cluster-robust bootstrap or verified multi-seed Wilson intervals.
  4. Ensure every single claim's `commit` field matches the exact commit where the underlying CSV was produced.
- **Expected Output:** 100% cryptographic and numerical correspondence between ledger and result CSVs.
- **Acceptance Criteria:** Every row in `claims_ledger.csv` matches its source CSV row within $10^{-4}$.
- **Dependencies:** Tasks 1.1, 1.3, 1.4.
- **Complexity:** Medium.

#### Task 2.3: Re-Engineer `scripts/verify_research_results.py`
- **Files to Modify:** `scripts/verify_research_results.py`
- **Proposed Changes:**
  1. Replace superficial schema check in `verify_claims_ledger` with deep numerical validation:
     ```python
     # For every claim in ledger:
     # 1. Load source_csv
     # 2. Match slice (resolver, protocol, workload, direction/test_net)
     # 3. Assert abs(ledger_val - csv_val) < 1e-4
     ```
  2. Replace hardcoded row counts with dynamic manifest drop-accounting checks.
  3. Add check for multiple-comparison FDR p-value validity.
- **Expected Output:** Rigorous verification tool that genuinely guarantees 100% reproducibility.
- **Acceptance Criteria:** Exits with code 0 only when every numerical claim is verified against disk.
- **Dependencies:** Tasks 2.1, 2.2.
- **Complexity:** Medium.

---

### Phase 3: Result & Figure Regeneration

#### Task 3.1: Re-Execute All Headline Analyses
- **Execution Commands:**
  ```bash
  python3 -m encdns analyze --run-id airtel_topup_20261113
  python3 scripts/run_jio_analysis.py
  python3 scripts/run_airtel_all.py
  python3 src/analysis_v2.py
  ```
- **Expected Output:** Fully refreshed, methodologically sound CSV outputs across all results folders.
- **Acceptance Criteria:** All executions complete cleanly without warnings; all output CSVs populated.
- **Dependencies:** Phase 1.
- **Complexity:** Medium.

#### Task 3.2: Rebuild `scripts/plot_slide_figures.py` with Dynamic Data Binding
- **Files to Modify:** `scripts/plot_slide_figures.py`
- **Proposed Changes:**
  1. `plot_headline_airtel()`: Load data dynamically from `results/airtel_topup_20261113/rq1_rq2_fingerprinting.csv`. Plot error bars representing 95% confidence intervals (`yerr=[acc - ci_low, ci_high - acc]`). Plot exact dynamic chance levels ($1/K$).
  2. `plot_cross_network()`: Load data dynamically from `results/jio_analysis_20261113/n2_cross_network_transfer.csv`. Plot error bars.
  3. `plot_carrier_blocking()`: Load data from `n6_protocol_availability.csv`. Change title to: *"Transport Protocol Reachability (UDP 443 Timeout vs. TCP 443 Completion)"*. Remove `"100% BLOCKED by Carrier Gateway"`; replace with `"100% Client-Side Timeouts (0 Packets Received)"`.
  4. Ensure all figures export at 300 DPI vector-ready resolution.
- **Expected Output:** Publication-quality figures generated automatically from data files.
- **Acceptance Criteria:** Zero hardcoded data arrays in `plot_slide_figures.py`; all figures render error bars.
- **Dependencies:** Task 3.1.
- **Complexity:** Medium.

---

### Phase 4: Academic Writing, Claims & Manuscript Alignment

#### Task 4.1: Neutralize Causal Overclaims in `docs/paper.md` and `readme.md`
- **Files to Modify:** `docs/paper.md`, `readme.md`
- **Specific Text Corrections:**
  1. *Jio QUIC Reachability:* Replace assertions of middlebox blocking with observational language:
     > *"On the evaluated Reliance Jio cellular connection, 100% of the 3,000 DoH/3 queries timed out with zero return packets received on UDP port 443. While consistent with carrier-grade middlebox filtering of outbound QUIC, local NAT mapping timeouts or interface-specific tethering policies cannot be ruled out. If deployed on networks exhibiting UDP 443 blockage, user agents fall back to older transport protocols, forfeiting QUIC's privacy protections."*
  2. *Cross-Network Distribution Shifts:* Replace speculative radio scheduling claims with statistical characterization:
     > *"Classifiers trained on broadband traffic fail when evaluated against cellular traces (1.6%–2.4% accuracy vs. 2.0% chance). Two-sample Kolmogorov-Smirnov tests confirm pronounced feature distribution shifts ($p < 10^{-6}$), predominantly in cumulative byte traces and packet inter-arrival times, reflecting the distinct transport dynamics of mobile links."*
  3. *EDNS0 Padding Limitation:* Reiterate that client-side JSON absence does not prove wire absence:
     > *"Client-side measurement logs from `q` did not report negotiated EDNS0 padding options; however, definitive confirmation requires packet-level payload decryption."*
- **Expected Output:** Scientifically defensible text adhering to strict academic standards.
- **Acceptance Criteria:** Zero unsupported causal assertions in paper or README.
- **Dependencies:** None.
- **Complexity:** Small.

#### Task 4.2: Resolve Incomplete Citations & Placeholders in `docs/paper.md`
- **Files to Modify:** `docs/paper.md`
- **Proposed Changes:**
  1. Replace `Siby et al. [CITE: CCS 2020]` with full citation: `[Siby et al. 2020] S. Siby, M. Juarez, C. Diaz, N. Vallina-Rodriguez, C. Troncoso. "Encrypted DNS => Privacy? A Traffic Analysis Perspective." In *Proc. ACM CCS 2020*.`
  2. Replace `[Author Names]` with proper coursework author information (`Aman Kashyap, Department of IT, IIIT Allahabad`).
  3. Resolve all `[CITE]` markers in Sections 1, 2, and 4 with full entries in Section 10 References (Herrmann et al., Wang et al., Juarez et al., Hoang et al., Le Pochat et al.).
- **Expected Output:** Complete, self-contained academic paper manuscript.
- **Acceptance Criteria:** Zero `[CITE]`, `TODO`, or placeholder tokens remain in `docs/paper.md`.
- **Dependencies:** None.
- **Complexity:** Small.

#### Task 4.3: Synchronize Documented Numbers with Regenerated Results
- **Files to Modify:** `docs/paper.md`, `readme.md`
- **Proposed Changes:**
  1. Update Abstract, Table 1, Table 2, and text discussion to match the exact values produced by the regenerated Phase 3 CSVs.
  2. Ensure the chance baselines, class counts (e.g. 99 for Cloudflare Global), and confidence interval widths match the ledger exactly.
- **Expected Output:** Absolute consistency across all documentation.
- **Acceptance Criteria:** Every numerical claim in `readme.md` and `docs/paper.md` matches `claims_ledger.csv`.
- **Dependencies:** Tasks 2.2, 3.1.
- **Complexity:** Small.

---

### Phase 5: Repository Quality & Continuous Integration

#### Task 5.1: Synchronize Configuration Files
- **Files to Modify:** `config/project.yaml`, `pyproject.toml`
- **Proposed Changes:**
  1. In `config/project.yaml`:
     - Update `jio: complete`.
     - Remove or mark `campus: cancelled (out_of_scope)`.
     - Update `manifest: data/raw/manifest_pilot_v1.csv` or active manifest directory.
  2. In `pyproject.toml`:
     - Keep `requires-python = ">=3.10"` and update `readme.md` badges to require Python 3.10+.
- **Expected Output:** Synchronized configuration state.
- **Acceptance Criteria:** `encdns status` passes with zero configuration warnings.
- **Dependencies:** None.
- **Complexity:** Small.

#### Task 5.2: Unit Test Suite Expansion
- **Files to Create/Modify:** `tests/test_statistical_engine.py`, `tests/test_claims_ledger.py`
- **Proposed Changes:**
  1. Add unit tests for `domain_clustered_bootstrap` verifying nominal coverage on synthetic clustered data.
  2. Add unit tests for symmetric permutation test verifying uniform p-value distribution under true $H_0$.
  3. Add regression test ensuring `claims_ledger.csv` numerical validity.
- **Expected Output:** Robust test harness expanded beyond manifest parsing.
- **Acceptance Criteria:** `python3 -m unittest discover tests` runs $\ge 15$ tests successfully in $< 2$ seconds.
- **Dependencies:** Tasks 1.2, 2.3.
- **Complexity:** Medium.

#### Task 5.3: End-to-End Clean-Clone Reproduction Audit
- **Procedure:**
  1. Clone repository to a temporary sandbox directory:
     ```bash
     git clone /Users/amankashyap/Documents/DNS-Analysis /tmp/clean_dns_test
     cd /tmp/clean_dns_test
     ```
  2. Install dependencies in clean virtual environment.
  3. Run `python3 scripts/verify_research_results.py`.
  4. Run `python3 scripts/plot_slide_figures.py`.
  5. Run `python3 -m unittest discover tests`.
- **Acceptance Criteria:** All verification commands pass with exit code 0 on a virgin clone.
- **Dependencies:** Phases 1–5.
- **Complexity:** Medium.

---

## 7. File-by-File Change Matrix

| File Path | Current State / Issue | Proposed Remediation | Risk / Impact |
| :--- | :--- | :--- | :--- |
| `src/encdns/analysis/fingerprinting.py` | 5-fold CV on subsampled repeats; 50 vs 100 trees; train-only label shuffling; 1-seed CI | Implement explicit temporal holdout (8–17 train, 18–19 test); symmetric 100-tree null; permute test labels; integrate bootstrap | **High** (Alters headline accuracy slightly; restores methodological truth) |
| `src/encdns/analysis/stats.py` | Basic Wilson interval and empirical p-value | Add domain-clustered block bootstrap; add Benjamini-Hochberg FDR correction | **Low** (Extends statistical toolbox) |
| `src/analysis_v2.py` | Missing XGBoost fingerprinting output; claims ledger ML-2 points here erroneously | Add `run_model_comparison` exporting legitimate `model_comparison.csv` with RF, XGB, and sequence baselines | **Medium** (Provides empirical grounding for ML-2) |
| `scripts/run_jio_analysis.py` | N1 uses 50 trees in null; pseudo-count CIs; N3 pooled has overlapping combined slice | Set 100 trees in null; add bootstrap CIs; label combined test set as composite | **Medium** (Improves cellular analysis rigor) |
| `.gitignore` | Excludes `dataset_jio.csv`, `dataset_combined.csv`, and all `results/*` | Whitelist essential processed CSV datasets and result tables; keep raw PCAPs excluded | **Low** (Essential for clean-clone reproducibility) |
| `docs/claims_ledger.csv` | ML-2 points to wrong file; POOL-1..4 conflate test networks | Re-map ML-2 to `model_comparison.csv`; clarify test networks for POOL rows; update CIs | **Medium** (Establishes 100% provenance integrity) |
| `scripts/verify_research_results.py` | Schema-only check for ledger; hardcoded constants | Implement deep value verification against source CSVs; dynamic drop accounting | **Low** (Guarantees true reproducibility) |
| `scripts/plot_slide_figures.py` | Figures 1, 2, 3 use hardcoded lists; no error bars; speculative text annotations | Dynamically load CSVs; plot 95% CIs; neutralize causal annotations | **Low** (Elevates figures to publication quality) |
| `docs/paper.md` | Unsubstantiated causal claims; placeholder citations (`[CITE]`, `[Author Names]`) | Replace with observational language; insert full academic citations; update numbers | **Medium** (Brings paper to submission standard) |
| `readme.md` | Outdated python version badge; references to old causal claims | Align badges (Python 3.10+); reflect verified findings and clean reproducibility steps | **Low** (Public presentation polish) |
| `config/project.yaml` | `jio` and `campus` marked pending; broken manifest path | Set `jio: complete`, `campus: cancelled`; update manifest paths | **Low** (Config consistency) |
| `tests/test_statistical_engine.py` | New file | Unit test suite for bootstrap, symmetric permutation, and FDR | **Low** (Safety harness) |

---

## 8. Detailed Execution Dependencies (DAG)

```
[Phase 1: Code Remediation]
  T1.1 (fingerprinting.py) ──┐
  T1.2 (stats.py) ──────────┼──> T1.3 (run_jio_analysis.py)
                            │
  T1.4 (analysis_v2.py) ────┘
           │
           ▼
[Phase 2: Governance & Verification]
  T2.1 (.gitignore) ──> T2.2 (claims_ledger.csv) ──> T2.3 (verify_research_results.py)
           │
           ▼
[Phase 3: Pipeline Execution & Figures]
  T3.1 (Rerun Analyses) ──> T3.2 (plot_slide_figures.py)
           │
           ▼
[Phase 4: Manuscript & Writing]
  T4.1 (Causal Neutralization) ──┐
  T4.2 (Resolve Citations) ──────┼──> T4.3 (Sync Documentation Numbers)
                                 │
[Phase 5: Final Validation]      │
  T5.1 (Configs) ────────────────┼──> T5.2 (Tests) ──> T5.3 (Clean Clone Audit)
```

---

## 9. Risks and Researcher Decisions Requiring Approval

Before executing this remediation plan, the following scientific trade-offs must be approved by the principal researcher:

### Decision 1: Reporting Headline Accuracy from Temporal Holdout vs. 5-Fold Cross-Validation
- **Issue:** The paper text claims a temporal holdout on repeats 18–19 (2 repeats), whereas the original code ran 5-fold CV across 10 sampled repeats.
- **Options:**
  - *Option 1A (Recommended):* Report the strict temporal holdout (train 8–17, test 18–19) as the headline accuracy in Table 1, and report the 5-fold CV in an appendix table to show temporal stability.
  - *Option 1B:* Keep 5-fold CV as the headline accuracy, but update all methodology documentation, tables, and text to explicitly state that 5-fold CV was used, correcting the false claim of a fixed 18–19 holdout.

### Decision 2: Treatment of Claim ML-2 (XGBoost on AdGuard DoH Global)
- **Issue:** The claim of 24.8% accuracy for XGBoost has no underlying CSV artifact in the repository.
- **Options:**
  - *Option 2A (Recommended):* Execute `run_model_comparison` in `analysis_v2.py` across Random Forest and XGBoost using the exact same split, generate `model_comparison.csv`, and record the empirical value in the claims ledger.
  - *Option 2B:* If XGBoost was an exploratory figure from an untracked scratchpad, remove claim `ML-2` from the ledger, README, and paper, focusing the comparison exclusively on Random Forest vs. 1D-CNN vs. GRU.

### Decision 3: Tracking Processed Datasets in Git vs. Git LFS / Zenodo
- **Issue:** `dataset_v2.csv` (18,926 rows, ~8 MB) is currently tracked. `dataset_jio.csv` (1,912 rows, ~1 MB) and `dataset_combined.csv` (20,838 rows, ~9 MB) are ignored.
- **Options:**
  - *Option 3A (Recommended for immediate coursework / review):* Track all three processed CSVs directly in Git. Total repository footprint will remain under 30 MB, enabling instant clean-clone reproduction.
  - *Option 3B (Formal archival):* Host processed datasets on Zenodo or an institutional repository, providing an automated fetch script (`scripts/download_datasets.sh`).

---

## 10. Acceptance Criteria for Research-Ready Status

The repository will be certified as **Research-Ready (Submission Standard)** when all of the following criteria are met:

1. **Methodological Transparency:** The evaluation protocol executed in code matches the description in `docs/methodology.md` and `docs/paper.md` with zero discrepancies.
2. **Symmetric Null Hypothesis Testing:** Permutation null models use identical tree counts (100) and multi-seed pipelines as observed models.
3. **Cluster-Aware Uncertainty:** All reported accuracy estimates include 95% confidence intervals derived from domain-clustered block bootstrapping or verified multi-seed variance.
4. **Clean-Clone Reproducibility:** A freshly cloned repository in an isolated environment reproduces all analysis tables and slide figures in $< 6$ minutes using `python3 scripts/verify_research_results.py`.
5. **100% Ledger Provenance:** Every claim in `docs/claims_ledger.csv` matches an existing, tracked CSV artifact within $10^{-4}$, with verified commit hashes and zero missing source files.
6. **Dynamic Visualization:** Every slide figure is generated dynamically from result CSVs, displays proper error bars, and contains zero hardcoded data arrays.
7. **Scientific Objectivity:** All speculative causal claims regarding carrier middlebox blocking, browser fallbacks, and radio scheduling are replaced with defensible observational statements.
8. **Academic Completeness:** All citation markers (`[CITE]`) in `docs/paper.md` are resolved with complete bibliographic entries.
