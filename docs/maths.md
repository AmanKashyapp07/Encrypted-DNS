# Mathematical & Statistical Foundations of the Study

This document provides a comprehensive, rigorous reference for every mathematical equation, statistical test, evaluation metric, and data aggregation method used in our study and presentation deck (*"DoH vs DoH/3: A Traffic-Analysis Study of Encrypted DNS Fingerprinting on Indian Networks"*).

---

## Table of Contents
1. [Core Classification & Information Metrics](#1-core-classification--information-metrics)
2. [Statistical Uncertainty & Confidence Intervals](#2-statistical-uncertainty--confidence-intervals)
3. [Hypothesis Testing & Permutation Null Models](#3-hypothesis-testing--permutation-null-models)
4. [Distribution Divergence: Two-Sample Kolmogorov-Smirnov Test](#4-distribution-divergence-two-sample-kolmogorov-smirnov-test)
5. [Mathematical Formulation of the 44 Flow Features](#5-mathematical-formulation-of-the-44-flow-features)
6. [Protocol Dynamics: Absolute Drop vs. Relative Reduction](#6-protocol-dynamics-absolute-drop-vs-relative-reduction)
7. [Cross-Network Aggregation: Micro vs. Macro Averages](#7-cross-network-aggregation-micro-vs-macro-averages)
8. [Middlebox Reachability & Capture Accounting](#8-middlebox-reachability--capture-accounting)
9. [Simulated Defenses: Mathematical Perturbations](#9-simulated-defenses-mathematical-perturbations)
10. [Empirical Real Data Tables (Ground Truth from Artifacts)](#10-empirical-real-data-tables-ground-truth-from-artifacts)

---

## 1. Core Classification & Information Metrics

### 1.1 Top-1 Classification Accuracy
In a closed-world website fingerprinting attack, an adversary observes a test flow $i$ and outputs a predicted domain label $\hat{y}_i \in \{1, 2, \dots, K\}$, where $K$ is the total number of candidate domains.

The empirical Top-1 accuracy is defined as:
$$\text{Top-1 Accuracy} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} \mathbf{1}_{\{\hat{y}_i = y_i\}}$$
where:
- $N_{\text{test}}$ is the total number of test flows.
- $y_i$ is the ground-truth domain label.
- $\mathbf{1}_{\{\cdot\}}$ is the indicator function ($1$ if predicted domain matches ground truth, $0$ otherwise).

---

### 1.2 Chance Baseline (Uniform Random Guessing)
The chance baseline represents the expected accuracy of an uninformed adversary who assigns uniform random guesses across all candidate classes:
$$\text{Chance} = \frac{1}{K}$$

- **100 Domains (Airtel Full Workload):**
  $$\text{Chance} = \frac{1}{100} = 0.010 \quad (1.0\%)$$
- **99 Domains (Airtel Shared Global Workload):**
  $$\text{Chance} = \frac{1}{99} \approx 0.0101 \quad (1.0\%)$$
- **79 Domains (Airtel Shared India Workload):**
  $$\text{Chance} = \frac{1}{79} \approx 0.0127 \quad (1.3\%)$$
- **50 Domains (Jio Cellular, Campus Wi-Fi, Shared Cross-Carrier):**
  $$\text{Chance} = \frac{1}{50} = 0.020 \quad (2.0\%)$$

> [!IMPORTANT]
> **Why Raw Percentages Cannot Be Averaged Across Datasets:**  
> A 20.0% accuracy on 100 domains represents **$20\times$ chance**, whereas a 20.0% accuracy on 50 domains represents only **$10\times$ chance**. Comparing raw percentages without scaling by the chance baseline is mathematically invalid.

---

### 1.3 Signal Amplification Factor (Fold-over-Chance)
To compare classification strength across differing numbers of classes ($K=100$ vs. $K=50$), we define the Signal Amplification Factor:
$$\text{Fold-over-Chance} = \frac{\text{Top-1 Accuracy}}{\text{Chance}} = K \times \text{Top-1 Accuracy}$$

**Examples from our findings:**
- **Airtel Quad9 DoH:** $45.2\% / 1.0\% = \mathbf{45.2\times \text{ chance}}$ (massive metadata leak).
- **Airtel Google DoH:** $21.3\% / 1.0\% = \mathbf{21.3\times \text{ chance}}$.
- **Jio Google DoH:** $15.7\% / 2.0\% = \mathbf{7.85\times \text{ chance}}$.
- **Campus Cloudflare DoH:** $4.9\% / 2.0\% = \mathbf{2.45\times \text{ chance}}$.
- **Cross-Carrier Transfer (Airtel $\to$ Jio):** $1.67\% / 2.0\% = \mathbf{0.84\times \text{ chance}}$ (indistinguishable from pure random noise).

---

## 2. Statistical Uncertainty & Confidence Intervals

In our project, two distinct confidence interval formulations are employed depending on the evaluation partition:

### 2.1 Empirical Percentile Bootstrap (1,000 Iterations)
Used for the 20-repeat temporal holdout, within-carrier Jio/Campus evaluations, and cross-network transfer matrices (`ci_boot_low`, `ci_boot_high`).

**Algorithm:**
1. Given test predictions $\{(\hat{y}_1, y_1), (\hat{y}_2, y_2), \dots, (\hat{y}_N, y_N)\}$.
2. Draw $B = 1,000$ bootstrap replicates of size $N$ with replacement:
   $$\mathcal{S}^{*(b)} = \{(\hat{y}^*_i, y^*_i)\}_{i=1}^N, \quad b = 1, 2, \dots, B$$
3. For each replicate, compute accuracy:
   $$\theta^{*(b)} = \frac{1}{N} \sum_{i=1}^N \mathbf{1}_{\{\hat{y}^*_i = y^*_i\}}$$
4. Sort bootstrap replicates: $\theta^{*(1)} \le \theta^{*(2)} \le \dots \le \theta^{*(B)}$.
5. The 95% two-sided empirical percentile interval is:
   $$[\text{CI}_{\text{boot\_low}}, \text{CI}_{\text{boot\_high}}] = \left[ \theta^{*(25)}, \theta^{*(975)} \right]$$

#### What "CI Overlaps Chance" Means Mathematically:
If the 2.0% chance line falls inside the interval:
$$\text{Chance} \in [\text{CI}_{\text{boot\_low}}, \text{CI}_{\text{boot\_high}}]$$
Then the null hypothesis that the classifier operates by uniform guessing cannot be rejected at significance level $\alpha = 0.05$.  
- *Observed in Cross-Carrier Transfer:* Airtel $\to$ Jio Google yields $1.67\% \text{ [0.00\%, 4.73\%]}$, meaning $2.0\%$ lies cleanly within the interval.

---

### 2.2 Wilson Score Confidence Interval
Used in the thesis headline table (Table 4.1) for the 5-fold cross-validation run on pooled predictions.

For $n$ pooled Bernoulli trials with observed sample proportion $\hat{p} = \frac{X}{n}$ and critical value $z = z_{1 - \alpha/2} = 1.96$ (for 95% confidence):
$$\text{CI}_{\text{Wilson}} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1 - \hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

---

## 3. Hypothesis Testing & Permutation Null Models

To prove that high accuracy does not arise from spurious correlation, random class imbalance, or model overfitting, we conduct **non-parametric label permutation tests**.

### 3.1 Permutation Test Formulation
1. **Null Hypothesis ($H_0$):** There is no statistical association between the flow feature vector $\mathbf{x} \in \mathbb{R}^{44}$ and the domain label $y \in \{1, \dots, K\}$. The true accuracy is governed by exchangeable random assignment.
2. **Procedure:**
   - Keep flow features $\mathbf{X}$ fixed.
   - For permutation $r = 1, 2, \dots, R$ (where $R = 200$):
     - Uniformly shuffle label assignments $\mathbf{y}_{\pi(r)} = \text{permute}(\mathbf{y})$.
     - Train classifier on $\mathbf{X}_{\text{train}}$ with scrambled labels $\mathbf{y}_{\pi(r), \text{train}}$.
     - Evaluate accuracy on test set: $A^{(r)}_{\text{null}}$.
3. **Exact Empirical p-value:**
   $$p = \frac{1 + \sum_{r=1}^R \mathbf{1}_{\{A^{(r)}_{\text{null}} \ge A_{\text{true}}\}}}{R + 1}$$

### 3.2 Attainable p-value Bound
When zero out of 200 label-shuffled permutations beat or match the true accuracy $A_{\text{true}}$:
$$p = \frac{1 + 0}{200 + 1} = \frac{1}{201} \approx 0.004975 \implies \mathbf{p < 0.005}$$

Every single headline within-carrier slice on Airtel FTTH achieves $p < 0.005$, confirming statistical significance at the 99.5% confidence tier.

---

## 4. Distribution Divergence: Two-Sample Kolmogorov-Smirnov Test

To understand why a classifier trained on Airtel fails completely when deployed on Jio cellular, we evaluate the divergence of feature probability distributions.

### 4.1 KS Statistic Formulation
For a scalar feature $x$ (e.g., maximum download packet size `down_max`), let:
- $F_1(x) = \frac{1}{n_1} \sum_{i=1}^{n_1} \mathbf{1}_{\{X_{1, i} \le x\}}$ (Empirical Cumulative Distribution Function on Network 1)
- $F_2(x) = \frac{1}{n_2} \sum_{i=1}^{n_2} \mathbf{1}_{\{X_{2, i} \le x\}}$ (ECDF on Network 2)

The two-sample Kolmogorov-Smirnov statistic $D$ measures the supremum divergence between the two empirical curves:
$$D = \sup_{x} |F_1(x) - F_2(x)| \in [0, 1]$$

### 4.2 Interpreting the Test Results
- Asymptotically, under $H_0: F_1 = F_2$:
  $$\sqrt{\frac{n_1 n_2}{n_1 + n_2}} D \xrightarrow{d} \text{Kolmogorov Distribution}$$
- In our measurements, comparing Jio Cellular vs. Airtel FTTH yields $D = 0.9356$ with empirical **$p < 10^{-15}$**.
- **Physical Meaning:** The hypothesis that Jio and Airtel share identical physical packet distributions is rejected beyond any statistical doubt. Jio’s radio link layer fragments large datagrams to an effective MTU of 1,340 B, while broadband supports full 1,500 B Ethernet frames. The classifier's decision boundaries are physically misaligned.

---

## 5. Mathematical Formulation of the 44 Flow Features

A capture session records an ordered sequence of $M$ packets:
$$\mathcal{F} = \{(t_i, s_i, d_i)\}_{i=1}^M$$
where $t_i \in \mathbb{R}^+$ is timestamp, $s_i \in \mathbb{N}$ is packet size in bytes (at IP layer), and $d_i \in \{+1, -1\}$ denotes direction ($+1 = \text{client} \to \text{resolver}$, $-1 = \text{resolver} \to \text{client}$).

### Group 1: Packet Count and Directional Ratios (7 Features)
1. **Total Packet Count ($M$):** $\texttt{n\_pkts} = \sum_{i=1}^M 1$
2. **Upstream Packets:** $\texttt{n\_up} = \sum_{i=1}^M \mathbf{1}_{\{d_i = +1\}}$
3. **Downstream Packets:** $\texttt{n\_down} = \sum_{i=1}^M \mathbf{1}_{\{d_i = -1\}}$
4. **Packet Up/Down Ratio:** $\texttt{ratio\_pkts} = \frac{\texttt{n\_up}}{\texttt{n\_down} + \epsilon}$
5. **Alternative Directional Ratios:** $\texttt{up\_frac} = \frac{\texttt{n\_up}}{M}, \quad \texttt{down\_frac} = \frac{\texttt{n\_down}}{M}$
6. **Signed Packet Sum:** $\texttt{n\_diff} = \texttt{n\_up} - \texttt{n\_down}$

### Group 2: Byte Volume Statistics (6 Features)
7. **Total Transferred Volume:** $\texttt{bytes\_total} = \sum_{i=1}^M s_i$
8. **Upstream Volume:** $\texttt{bytes\_up} = \sum_{i: d_i = +1} s_i$
9. **Downstream Volume:** $\texttt{bytes\_down} = \sum_{i: d_i = -1} s_i$
10. **Byte Volume Ratio:** $\texttt{ratio\_bytes} = \frac{\texttt{bytes\_up}}{\texttt{bytes\_down} + \epsilon}$
11. **Maximum Directional Packet Sizes:** $\texttt{up\_max} = \max_{\{i \mid d_i = +1\}} s_i, \quad \texttt{down\_max} = \max_{\{i \mid d_i = -1\}} s_i$

### Group 3: Temporal & Duration Metrics (6 Features)
12. **Flow Total Duration:** $\texttt{duration} = t_M - t_1$
13. **Inter-Arrival Times (IAT):**
    $$\Delta t_i = t_{i+1} - t_i \quad \text{for } i=1, \dots, M-1$$
    $$\texttt{iat\_mean} = \frac{1}{M-1} \sum_{i=1}^{M-1} \Delta t_i, \quad \texttt{iat\_std} = \sqrt{\frac{1}{M-2} \sum_{i=1}^{M-1} (\Delta t_i - \texttt{iat\_mean})^2}, \quad \texttt{iat\_max} = \max_{1 \le i \le M-1} \Delta t_i$$
14. **Time to First Response:** $\texttt{t\_first\_down} = \min \{ t_i - t_1 \mid d_i = -1 \}$
15. **Downstream Inter-Arrival Mean:** Mean of intervals between downstream packets.

### Group 4: Burst Dynamics (5 Features)
A burst $\beta_k$ is a contiguous maximal sequence of packets transmitted in the same direction:
16. **Burst Count:** $\texttt{burst\_count} = B$ (number of sign alternations).
17. **Mean Burst Size (Bytes):** $\texttt{burst\_bytes\_mean} = \frac{1}{B} \sum_{k=1}^B \left( \sum_{j \in \beta_k} s_j \right)$
18. **Max Burst Size (Bytes):** $\texttt{burst\_bytes\_max} = \max_{1 \le k \le B} \sum_{j \in \beta_k} s_j$
19. **Mean Burst Packets:** $\texttt{burst\_pkts\_mean} = \frac{1}{B} \sum_{k=1}^B |\beta_k|$
20. **Max Burst Packets:** $\texttt{burst\_pkts\_max} = \max_{1 \le k \le B} |\beta_k|$

### Group 5: First 20 Signed Packet Sizes (20 Features)
$$\texttt{pkt\_k} = \begin{cases} d_k \cdot s_k & \text{if } k \le M \\ 0 & \text{if } k > M \end{cases} \quad \text{for } k \in \{0, 1, \dots, 19\}$$

---

## 6. Protocol Dynamics: Absolute Drop vs. Relative Reduction

### 6.1 Percentage Point Drop (Absolute Drop)
$$\Delta_{\text{pp}} = \text{Acc}_{\text{DoH}} - \text{Acc}_{\text{DoH/3}}$$

### 6.2 Relative Leakage Reduction (Percentage Reduction)
$$\Delta_{\text{rel}} = \frac{\text{Acc}_{\text{DoH}} - \text{Acc}_{\text{DoH/3}}}{\text{Acc}_{\text{DoH}}} \times 100\%$$

### 6.3 Mathematical Breakdown by Resolver (Global Workload, Late Holdout)

$$\begin{array}{lccccc}
\toprule
\textbf{Resolver} & \textbf{DoH Accuracy} & \textbf{DoH/3 Accuracy} & \Delta_{\text{pp}} \textbf{ (Points)} & \Delta_{\text{rel}} \textbf{ (Relative Drop)} \\
\midrule
\textbf{Quad9}      & 45.17\% & 6.63\%  & 38.54\% \approx \mathbf{38.6 \text{ pp}} & \frac{38.54}{45.17} = \mathbf{85.3\% \approx 85\%} \\
\textbf{Cloudflare} & 26.33\% & 7.17\%  & 19.16\% \approx \mathbf{19.2 \text{ pp}} & \frac{19.16}{26.33} = \mathbf{72.8\% \approx 73\%} \\
\textbf{AdGuard}    & 26.17\% & 11.17\% & 15.00\% = \mathbf{15.0 \text{ pp}}       & \frac{15.00}{26.17} = \mathbf{57.3\% \approx 57\%} \\
\textbf{Google}     & 21.33\% & 15.00\% & 6.33\% \approx \mathbf{6.3 \text{ pp}}   & \frac{6.33}{21.33} = \mathbf{29.7\% \approx 30\%} \\
\bottomrule
\end{array}$$

---

## 7. Cross-Network Aggregation: Micro vs. Macro Averages

### 7.1 The Sample-Weighted Micro-Average in Pooled Co-Training (Table 4)
The Composite score is a **sample-weighted micro-average** pooled across all held-out test predictions:
$$\text{Acc}_{\text{composite}} = \frac{N_{\text{Airtel\_test}} \cdot \text{Acc}_{\text{Airtel}} + N_{\text{Jio\_test}} \cdot \text{Acc}_{\text{Jio}}}{N_{\text{Airtel\_test}} + N_{\text{Jio\_test}}}$$

#### Step-by-Step Derivation for AdGuard Global:
- Airtel held-out: $N_{\text{Airtel}} = 100$, accuracy $= 33.67\% \implies 33.67$ correct.
- Jio held-out: $N_{\text{Jio}} = 98$, accuracy $= 4.42\% \implies 0.0442 \times 98 = 4.33$ correct.
- Total test flows: $N_{\text{total}} = 100 + 98 = 198$.

$$\text{Acc}_{\text{composite}} = \frac{33.67 + 4.33}{198} = \frac{38.00}{198} = 0.191919 \dots = \mathbf{19.19\%}$$

#### Step-by-Step Derivation for AdGuard India:
- Airtel held-out: $N_{\text{Airtel}} = 96$, accuracy $= 25.35\% \implies 0.2535 \times 96 = 24.336$ correct.
- Jio held-out: $N_{\text{Jio}} = 79$, accuracy $= 3.38\% \implies 0.0338 \times 79 = 2.670$ correct.
- Total test flows: $N_{\text{total}} = 96 + 79 = 175$.

$$\text{Acc}_{\text{composite}} = \frac{24.336 + 2.670}{175} = \frac{27.006}{175} = 0.15432 \dots = \mathbf{15.43\%}$$

---

### 7.2 Tri-Network Co-Training Macro Mean (20.67%)
The **20.67%** figure represents the unweighted arithmetic mean across all six tri-network composite slices (`c3_tri_network_pooled.csv`):
$$\overline{\text{Acc}}_{\text{tri\_network}} = \frac{1}{6} \sum_{s=1}^6 \text{Acc}^{(s)}_{\text{composite}}$$

$$\begin{aligned}
\overline{\text{Acc}} &= \frac{12.18\% + 45.00\% + 14.54\% + 12.89\% + 26.26\% + 13.16\%}{6} \\
&= \frac{124.03\%}{6} = \mathbf{20.67\%}
\end{aligned}$$

---

## 8. Middlebox Reachability & Capture Accounting

### 8.1 Reachability Rate
$$\text{Reachability / Completion Rate} = \frac{\text{Completed Query Flows}}{\text{Total Attempted Captures}} \times 100\%$$

### 8.2 The 3,000 / 3,000 UDP 443 Timeout Formula
$$3,000 = 50 \text{ domains} \times 10 \text{ repeats} \times 3 \text{ resolvers} \times 2 \text{ workloads}$$

### 8.3 Headline Capture Yield Accounting

$$\begin{array}{lcccc}
\toprule
\textbf{Network Environment} & \textbf{Attempted Captures} & \textbf{Usable Clean Flows} & \textbf{Excluded / Lost} & \textbf{Yield Rate} \\
\midrule
\textbf{Airtel Residential FTTH} & 19,200 & 18,926 & 274   & \mathbf{98.6\%} \\
\textbf{Reliance Jio 4G Cellular} & 6,000  & 1,912  & 4,088 & \mathbf{31.9\%} \\
\textbf{Campus Wi-Fi (Forward Proxy)} & 6,000 & 1,569 & 4,431 & \mathbf{26.2\%} \\
\midrule
\textbf{Headline Total}          & \mathbf{31,200} & \mathbf{22,407} & \mathbf{8,793} & \mathbf{71.8\%} \\
\bottomrule
\end{array}$$

---

## 9. Simulated Defenses: Mathematical Perturbations

### 9.1 RFC 8467 Block Padding
$$s'_i = \left\lceil \frac{s_i}{B} \right\rceil \times B$$
- $B = 64$: Accuracy drops from **20.4%** to **14.2%**.
- $B = 128$: Accuracy drops from **20.4%** to **13.8%**.

### 9.2 Additive Gaussian Timing Jitter
$$\Delta t'_i = \max(0, \Delta t_i + \epsilon_i), \quad \epsilon_i \sim \mathcal{N}(0, \sigma^2)$$
- $\sigma = 10\text{ ms}, 50\text{ ms}$: Accuracy remains at **20.4%** (no effect).

---

## 10. Empirical Real Data Tables (Ground Truth from Artifacts)

### 10.1 Airtel Residential FTTH: Complete 16-Slice Protocol Benchmark
*Source: `results/airtel_topup_20261113/rq1_rq2_fingerprinting.csv` (Temporal Holdout, 20 repeats, Chance = 1.0%)*

| Workload | Resolver | Protocol | $N_{\text{train}}$ | $N_{\text{test}}$ | Top-1 Accuracy | 95% Bootstrap CI | Top-5 Acc | Macro-F1 | Empirical $p$-value |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Global** | **AdGuard**    | DoH   | 999  | 200 | **26.17%** | [20.33%, 32.17%] | 58.33% | 0.2337 | $p < 0.005$ |
| **Global** | **AdGuard**    | DoH/3 | 1000 | 200 | **11.17%** | [7.00%, 16.17%]  | 29.17% | 0.0898 | $p < 0.005$ |
| **Global** | **Cloudflare** | DoH   | 996  | 200 | **26.33%** | [21.33%, 31.83%] | 52.67% | 0.2423 | $p < 0.005$ |
| **Global** | **Cloudflare** | DoH/3 | 997  | 200 | **7.17%**  | [3.83%, 11.17%]  | 19.00% | 0.0548 | $p < 0.005$ |
| **Global** | **Google**     | DoH   | 1000 | 200 | **21.33%** | [16.17%, 27.00%] | 47.17% | 0.1911 | $p < 0.005$ |
| **Global** | **Google**     | DoH/3 | 1000 | 200 | **15.00%** | [10.67%, 19.67%] | 41.83% | 0.1453 | $p < 0.005$ |
| **Global** | **Quad9**      | DoH   | 1000 | 200 | **45.17%** | [38.16%, 52.50%] | 74.83% | 0.4116 | $p < 0.005$ |
| **Global** | **Quad9**      | DoH/3 | 979  | 191 | **6.63%**  | [3.76%, 9.81%]   | 14.49% | 0.0582 | $p < 0.005$ |
| **India**  | **AdGuard**    | DoH   | 921  | 188 | **21.63%** | [15.95%, 28.01%] | 47.34% | 0.1799 | $p < 0.005$ |
| **India**  | **AdGuard**    | DoH/3 | 925  | 185 | **8.29%**  | [4.63%, 11.92%]  | 19.64% | 0.0659 | $p < 0.005$ |
| **India**  | **Cloudflare** | DoH   | 993  | 198 | **19.53%** | [14.00%, 25.29%] | 45.96% | 0.1634 | $p < 0.005$ |
| **India**  | **Cloudflare** | DoH/3 | 997  | 200 | **5.17%**  | [2.33%, 8.17%]   | 16.17% | 0.0446 | $p < 0.005$ |
| **India**  | **Google**     | DoH   | 1000 | 200 | **18.17%** | [13.17%, 23.50%] | 43.83% | 0.1599 | $p < 0.005$ |
| **India**  | **Google**     | DoH/3 | 1000 | 200 | **9.17%**  | [5.67%, 13.17%]  | 27.00% | 0.0837 | $p < 0.005$ |
| **India**  | **Quad9**      | DoH   | 989  | 199 | **35.01%** | [27.97%, 42.71%] | 68.68% | 0.3052 | $p < 0.005$ |
| **India**  | **Quad9**      | DoH/3 | 959  | 189 | **5.64%**  | [2.81%, 8.91%]   | 13.40% | 0.0463 | $p < 0.005$ |

---

### 10.2 Mobile Cellular (Reliance Jio 4G/LTE) Within-Network
*Source: `results/jio_analysis_20261113/n1_within_jio.csv` (Chance = 2.0%)*

| Workload | Resolver | Domains | $N_{\text{train}}$ | $N_{\text{test}}$ | Top-1 Accuracy | 95% Bootstrap CI | Empirical $p$-value |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Global** | **AdGuard** | 50 | 394 | 98  | **4.08%**  | [1.01%, 8.16%]  | $p = 0.1244$ (Not Sig.) |
| **Global** | **Google**  | 50 | 400 | 100 | **15.67%** | [10.33%, 21.67%]| **$p = 0.0050$** (Sig.) |
| **India**  | **AdGuard** | 42 | 295 | 79  | **6.75%**  | [2.41%, 12.12%] | **$p = 0.0249$** (Sig.) |
| **India**  | **Google**  | 50 | 399 | 100 | **12.33%** | [6.00%, 19.67%] | **$p = 0.0050$** (Sig.) |

---

### 10.3 Institutional Campus Wi-Fi (Forward Proxy) Within-Network
*Source: `results/campus_analysis_20261120/c1_within_campus.csv` (Chance = 2.0%)*

| Workload | Resolver | Domains | $N_{\text{train}}$ | $N_{\text{test}}$ | Top-1 Accuracy | 95% Bootstrap CI | Empirical $p$-value |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Global** | **AdGuard**    | 42 | 85  | 65 | **5.64%** | [1.00%, 11.83%] | **$p = 0.0249$** (Sig.) |
| **Global** | **Cloudflare** | 50 | 221 | 95 | **4.91%** | [1.08%, 9.38%]  | **$p = 0.0100$** (Sig.) |
| **Global** | **Google**     | 50 | 220 | 90 | **3.70%** | [0.37%, 7.78%]  | $p = 0.0995$ (Not Sig.) |
| **India**  | **AdGuard**    | 36 | 71  | 52 | **3.21%** | [0.00%, 7.69%]  | $p = 0.4328$ (Not Sig.) |
| **India**  | **Cloudflare** | 49 | 221 | 90 | **1.85%** | [0.37%, 4.07%]  | $p = 0.5075$ (Not Sig.) |
| **India**  | **Google**     | 48 | 223 | 87 | **4.21%** | [1.20%, 7.95%]  | $p = 0.0846$ (Not Sig.) |

---

### 10.4 Cross-Carrier Transfer Matrix ($3 \times 3$ Boundary)
*Source: `results/campus_analysis_20261120/c2_cross_network_transfer.csv` (Google Global Workload, 50 Domains, Chance = 2.0%)*

| Source Link (Train) | Destination Link (Test) | Direction | $N_{\text{train}}$ | $N_{\text{test}}$ | Accuracy | 95% Bootstrap CI | Overlaps Chance (2.0%)? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Airtel FTTH**    | **Reliance Jio**     | Airtel $\to$ Jio   | 600 | 500 | **1.67%** | [0.00%, 4.73%] | **Yes** (Collapse) |
| **Reliance Jio**    | **Airtel FTTH**     | Jio $\to$ Airtel   | 500 | 600 | **2.00%** | [0.00%, 6.00%] | **Yes** (Exact Chance) |
| **Airtel FTTH**    | **Campus Wi-Fi**     | Airtel $\to$ Campus| 600 | 310 | **1.94%** | [0.77%, 3.28%] | **Yes** (Collapse) |
| **Campus Wi-Fi**    | **Airtel FTTH**     | Campus $\to$ Airtel| 310 | 600 | **2.17%** | [0.50%, 4.45%] | **Yes** (Collapse) |
| **Reliance Jio**    | **Campus Wi-Fi**     | Jio $\to$ Campus   | 500 | 310 | **2.69%** | [0.75%, 4.99%] | **Yes** (Collapse) |
| **Campus Wi-Fi**    | **Reliance Jio**     | Campus $\to$ Jio   | 310 | 500 | **2.40%** | [0.73%, 5.00%] | **Yes** (Collapse) |

---

### 10.5 Two-Sample Kolmogorov-Smirnov Divergence Statistics
*Source: `results/campus_analysis_20261120/c4_feature_shift.csv`*

| Comparison | Feature Name | Mean Value (Net A) | Mean Value (Net B) | KS Statistic $D$ | Exact Empirical $p$-value |
|:---|:---|:---:|:---:|:---:|:---:|
| **Campus vs. Jio**    | `up_max`    | 1,505.5 B | 1,313.4 B | **0.9936** | $p < 10^{-15}$ |
| **Campus vs. Jio**    | `down_max`  | 1,425.7 B | 1,302.9 B | **0.9356** | $p < 10^{-15}$ |
| **Campus vs. Airtel** | `down_max`  | 1,425.7 B | 1,319.7 B | **0.9356** | $p < 10^{-15}$ |
| **Campus vs. Jio**    | `pkt_02`    | -108.9 B  | +84.8 B   | **0.8862** | $p < 10^{-15}$ |
| **Campus vs. Jio**    | `pkt_04`    | -189.2 B  | +334.2 B  | **0.8776** | $p < 10^{-15}$ |
| **Campus vs. Jio**    | `pkt_14`    | -861.0 B  | +160.8 B  | **0.8620** | $p < 10^{-15}$ |
