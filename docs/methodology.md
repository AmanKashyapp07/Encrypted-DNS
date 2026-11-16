# Experimental Methodology: Statistical Evaluation & Validation Protocols

This document specifies the exact machine learning protocols, temporal data splits, hyperparameter configurations, statistical hypothesis tests, and evaluation metrics used throughout this study.

---

## 1. Evaluation Splits: Leave-Repeat-Out Temporal Validation

To evaluate fingerprintability rigorously without leaking temporal artifacts:

* **The Fallacy of Random Splits:** Encrypted DNS traffic exhibits high temporal autocorrelation: queries executed within seconds of each other share transient network queuing delays and dynamic CDN edge conditions. Standard randomized train/test splits (e.g., k-fold CV) leak these transient artifacts, yielding severely inflated accuracy.
* **Leave-Repeat-Out Protocol:** Data is partitioned strictly by query repeat index:
  * **Headline Airtel Evaluation:** Queries from repeats 8–17 (10 repeats per domain) form the training set; queries from held-out repeats 18–19 form the evaluation test set.
  * **Jio Cellular Evaluation:** Queries from repeats 0–7 form the training set; queries from held-out repeats 8–9 form the test set.
  * **Balanced Repeats ($k=10$):** In the headline Airtel evaluation, only domains meeting the complete target of 10 successful repeats across the evaluated range are included, ensuring balanced multi-class evaluation.

---

## 2. Classifier Architectures & Configurations

### 2.1 Primary Model: Random Forest (Tree Ensemble)
* **Implementation:** `sklearn.ensemble.RandomForestClassifier`
* **Trees:** `n_estimators = 100`
* **Class Weighting:** `class_weight = 'balanced_subsample'` (re-weights classes inversely proportional to class frequencies on each bootstrap sample)
* **Random Seeds:** Evaluated across three fixed seeds: **`17`, `42`, and `101`**. The reported accuracy is the arithmetic mean across the three seeds.

### 2.2 Comparison Models
* **XGBoost:** `xgboost.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9, tree_method="hist")` evaluated on the full 44-feature space.
* **1D-CNN (Sequence):** 2-layer 1D Convolutional Neural Network (`Conv1d(1, 32, k=3) -> ReLU -> MaxPool1d(2) -> Conv1d(32, 64, k=3) -> AdaptiveAvgPool1d(1) -> Linear`) trained on per-sample normalized signed packet sequences (`pkt_00`..`pkt_19`).
* **GRU (Recurrent):** 2-layer Gated Recurrent Unit (`hidden_size=64, batch_first=True -> Linear`) trained on the same normalized packet sequences.
* **Deep Model Training:** Adam optimizer ($\text{lr} = 10^{-3}$), CrossEntropyLoss, 20 epochs, batch size 64.

---

## 3. Statistical Metrics & Significance Testing

### 3.1 Closed-World Top-1 Accuracy
Top-1 accuracy measures the proportion of test queries whose true domain matches the argmax predicted class probability:
$$\text{Accuracy} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} \mathbb{I}(\hat{y}_i = y_i)$$

### 3.2 Candidate Pool Sizes & Random Guessing Baselines
The random guessing chance baseline is strictly governed by the number of active candidate classes $N$:
$$\text{Chance Baseline} = \frac{1}{N}$$

* **Headline Closed-World Evaluation ($N = 100$):**
  $$\text{Chance} = \frac{1}{100} = \mathbf{1.0\%} \quad (0.010)$$
  *(Exception: Cloudflare Global DoH evaluated $N = 99$, where $\text{Chance} = 1/99 = 1.01\%$, due to `trbcdn.net` drop).*
* **Cross-Network Transfer Evaluation ($N = 50$):**
  Because Airtel tested 100 domains and Jio tested 50 domains within each workload, cross-network transfer is evaluated strictly on the **50 shared domains**:
  $$\text{Chance} = \frac{1}{50} = \mathbf{2.0\%} \quad (0.020)$$

### 3.3 Cluster-Robust Uncertainty: Domain-Level Block Bootstrap
Because repeated queries for the same domain exhibit intra-cluster correlation (violating independent Bernoulli assumptions), reported confidence intervals are constructed using a domain-level block bootstrap ($M = 1000$ iterations). In each bootstrap replicate, candidate domains are resampled with replacement, and all associated test observations are gathered. Multi-seed test accuracy across the three evaluation seeds is computed on the resampled set, yielding empirical 2.5th and 97.5th percentiles that robustly reflect sampling uncertainty under domain clustering.

### 3.4 Domain-Clustered Permutation Significance Tests (Empirical Null Distribution)
To evaluate statistical significance under the null hypothesis $H_0: P(Y \mid X) = P(Y)$ without breaking intra-domain repeat structure:
1. For each experimental slice, 200 independent permutations are executed.
2. In each iteration, domain identity labels are permuted at the domain level across unique test domains, mapping all queries of a domain to the same permuted identifier, preserving the repeated-measures clustering structure.
3. The empirical null distribution is evaluated identically across the same three model seeds as observed accuracy.
4. The empirical $p$-value is computed as:
   $$p = \frac{1 + \sum_{j=1}^{200} \mathbb{I}(\bar{\text{Acc}}_{\text{null}, j} \ge \bar{\text{Acc}}_{\text{observed}})}{201}$$
5. All 16 reported headline results satisfy $p < 0.005$ (0 out of 200 permuted iterations met or exceeded observed accuracy). Multi-comparison FDR adjustment using Benjamini-Hochberg confirms that all slices remain significant at $\alpha = 0.05$.

---

## 4. Open-World Evaluation Formulation (WP9)

In the open-world setting, a user visits both monitored domains (which an adversary cares about) and unmonitored background domains:

* **Setup:** Evaluated across monitored candidate sizes $M \in \{10, 25, 50, 75\}$, with the remaining $100 - M$ domains acting as unmonitored background traffic.
* **Decision Function:** The Random Forest outputs class posterior probabilities $P(y = d \mid x)$. The query is classified as the predicted domain if $\max_d P(y = d \mid x) \ge \tau$; otherwise, it is rejected as "unmonitored / unknown".
* **Metric:** Evaluated at a strict operational constraint of **$\text{False Positive Rate (FPR)} \le 5\%$**:
  $$\text{FPR} = \frac{\text{Unmonitored Queries Falsely Accepted as Monitored}}{\text{Total Unmonitored Queries}} \le 0.05$$
  Reported metric: **True Positive Rate (TPR) at $\text{FPR} \le 5\%$**.

---

## 5. Distribution Shift & Two-Sample Tests (N4)

To evaluate whether flow distributions differ significantly across physical access networks:
* **Two-Sample Kolmogorov-Smirnov (KS) Test:** Evaluated on continuous flow features between Airtel FTTH broadband and Reliance Jio cellular:
  $$D = \sup_x |F_{\text{Airtel}}(x) - F_{\text{Jio}}(x)|$$
  where $D \in [0, 1]$ ($0 = \text{identical distributions}, 1 = \text{complete non-overlapping shift}$).
* Features with $D > 0.80$ and $p < 10^{-6}$ indicate severe link-layer distribution shifts that invalidate static decision boundaries.
