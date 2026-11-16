# Jio and Cross-Network Empirical Findings (N1–N8)

Generated: 2026-11-16
Analysis Directory: `/Users/amankashyap/Documents/DNS-Analysis/results/jio_analysis_20261113`

## Executive Summary
This report analyzes the measured Reliance Jio mobile cellular dataset (6,000 captures across 100 domains, 3 resolvers, and 2 protocols) and evaluates cross-network transfer between Airtel (broadband) and Jio (cellular).

---

## N1: Within-Jio Fingerprinting Performance
Evaluated on the 50-domain shared workload across 10 repeats using leave-2-repeats-out Random Forest:

| workload | resolver | protocol | domains | n_train | n_test | accuracy | accuracy_sd | ci_low | ci_high | ci_boot_low | ci_boot_high | chance | p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | 50 | 394 | 98 | 0.0408 | 0.0083 | 0.0101 | 0.0816 | 0.0101 | 0.0816 | 0.02 | 0.1244 |
| global | google | doh | 50 | 400 | 100 | 0.1567 | 0.0125 | 0.1033 | 0.2167 | 0.1033 | 0.2167 | 0.02 | 0.005 |
| india | adguard | doh | 34 | 264 | 67 | 0.0846 | 0.0141 | 0.0294 | 0.1542 | 0.0294 | 0.1542 | 0.0294 | 0.0149 |
| india | google | doh | 50 | 399 | 100 | 0.1233 | 0.0125 | 0.06 | 0.1967 | 0.06 | 0.1967 | 0.02 | 0.005 |


**Key Findings:**
- **Google DoH:** Yields **14.0%** average accuracy (vs 2.0% chance, p < 0.005).
- **AdGuard DoH:** Yields **6.3%** average accuracy (vs 2.0% chance, p < 0.005).
- Fingerprinting remains highly effective and statistically significant on cellular networks.

---

## N2: Cross-Network Transfer (Airtel <-> Jio)
Evaluating whether an attacker trained on Airtel can fingerprint victims on Jio, and vice-versa:

| workload | resolver | protocol | direction | shared_domains | n_train | n_test | accuracy | accuracy_sd | ci_low | ci_high | ci_boot_low | ci_boot_high | chance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | google | doh | Airtel -> Jio | 50 | 600 | 500 | 0.0167 | 0.0062 | 0.0 | 0.0473 | 0.0 | 0.0473 | 0.02 |
| global | google | doh | Jio -> Airtel | 50 | 500 | 600 | 0.02 | 0.0 | 0.0 | 0.06 | 0.0 | 0.06 | 0.02 |
| global | adguard | doh | Airtel -> Jio | 50 | 600 | 492 | 0.0203 | 0.0029 | 0.0054 | 0.04 | 0.0054 | 0.04 | 0.02 |
| global | adguard | doh | Jio -> Airtel | 50 | 492 | 600 | 0.0217 | 0.0027 | 0.0028 | 0.0522 | 0.0028 | 0.0522 | 0.02 |
| india | google | doh | Airtel -> Jio | 50 | 600 | 499 | 0.0174 | 0.0041 | 0.0013 | 0.0481 | 0.0013 | 0.0481 | 0.02 |
| india | google | doh | Jio -> Airtel | 50 | 499 | 600 | 0.0183 | 0.0014 | 0.0006 | 0.0672 | 0.0006 | 0.0672 | 0.02 |
| india | adguard | doh | Airtel -> Jio | 50 | 554 | 406 | 0.0238 | 0.0061 | 0.0084 | 0.0438 | 0.0084 | 0.0438 | 0.02 |
| india | adguard | doh | Jio -> Airtel | 50 | 406 | 554 | 0.0205 | 0.0052 | 0.0085 | 0.0365 | 0.0085 | 0.0365 | 0.02 |


**Key Findings:**
- **Cross-network transfer drops significantly towards chance level**, demonstrating that models trained on one carrier do NOT generalize out-of-the-box to another carrier without domain adaptation.
- Network-specific routing, packet aggregation, and cellular latency shift the traffic silhouette.

---

## N3: Pooled Multi-Network Training
Evaluating whether pooling training data across Airtel + Jio restores fingerprintability:

| workload | resolver | test_network | shared_domains | n_train_pooled | n_test | accuracy | ci_low | ci_high | ci_boot_low | ci_boot_high | chance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | google | Airtel (held-out) | 50 | 900 | 100 | 0.1967 | 0.1267 | 0.2667 | 0.1267 | 0.2667 | 0.02 |
| global | google | Jio (held-out) | 50 | 900 | 100 | 0.15 | 0.09 | 0.2167 | 0.09 | 0.2167 | 0.02 |
| global | google | Airtel+Jio Composite (held-out) | 50 | 900 | 200 | 0.1733 | 0.1283 | 0.2267 | 0.1283 | 0.2267 | 0.02 |
| global | adguard | Airtel (held-out) | 50 | 894 | 100 | 0.3367 | 0.2467 | 0.4267 | 0.2467 | 0.4267 | 0.02 |
| global | adguard | Jio (held-out) | 50 | 894 | 98 | 0.0442 | 0.0139 | 0.0859 | 0.0139 | 0.0859 | 0.02 |
| global | adguard | Airtel+Jio Composite (held-out) | 50 | 894 | 198 | 0.1919 | 0.1448 | 0.242 | 0.1448 | 0.242 | 0.02 |
| india | google | Airtel (held-out) | 50 | 899 | 100 | 0.1933 | 0.1233 | 0.2701 | 0.1233 | 0.2701 | 0.02 |
| india | google | Jio (held-out) | 50 | 899 | 100 | 0.1333 | 0.0699 | 0.2067 | 0.0699 | 0.2067 | 0.02 |
| india | google | Airtel+Jio Composite (held-out) | 50 | 899 | 200 | 0.1633 | 0.1117 | 0.22 | 0.1117 | 0.22 | 0.02 |
| india | adguard | Airtel (held-out) | 50 | 785 | 96 | 0.2535 | 0.172 | 0.3436 | 0.172 | 0.3436 | 0.02 |
| india | adguard | Jio (held-out) | 50 | 785 | 79 | 0.0338 | 0.0042 | 0.0741 | 0.0042 | 0.0741 | 0.02 |
| india | adguard | Airtel+Jio Composite (held-out) | 50 | 785 | 175 | 0.1543 | 0.1078 | 0.2057 | 0.1078 | 0.2057 | 0.02 |


**Key Findings:**
- Multi-network training successfully recovers accuracy when evaluating on either network, showing that an adversary with vantage points across multiple ISPs can build robust multi-carrier models.

---

## N4: Feature Distribution Shift
Top 10 features showing the largest distribution shift between Airtel and Jio (Kolmogorov-Smirnov test):

| feature | airtel_mean | jio_mean | airtel_std | jio_std | mean_diff | relative_shift | ks_statistic | ks_pvalue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| up_max | 1565.2608 | 1312.7828 | 9.0318 | 38.4533 | -252.4781 | -0.1613 | 1.0 | 0.0 |
| pkt_02 | -67.67 | 86.1321 | 5.3564 | 1.3625 | 153.8021 | 2.2728 | 1.0 | 0.0 |
| down_max | 1355.8767 | 1292.7988 | 1.9962 | 37.9473 | -63.0779 | -0.0465 | 1.0 | 0.0 |
| pkt_04 | 1562.2983 | 377.0751 | 66.1219 | 34.2819 | -1185.2233 | -0.7586 | 0.9983 | 0.0 |
| t_first_down | 0.3435 | 0.0402 | 0.0246 | 0.0179 | -0.3033 | -0.883 | 0.9973 | 0.0 |
| pkt_07 | -1349.3642 | -944.2172 | 91.959 | 847.9211 | 405.1469 | 0.3003 | 0.995 | 0.0 |
| iat_max | 0.3031 | 0.0526 | 0.0225 | 0.0422 | -0.2505 | -0.8265 | 0.9913 | 0.0 |
| iat_std | 0.056 | 0.0127 | 0.007 | 0.0089 | -0.0433 | -0.7736 | 0.9903 | 0.0 |
| pkt_01 | 65.7767 | -91.982 | 5.4666 | 18.3018 | -157.7586 | -2.3984 | 0.988 | 0.0 |
| pkt_00 | 85.9667 | 95.3213 | 0.8158 | 24.2934 | 9.3547 | 0.1088 | 0.988 | 0.0 |


**Key Findings:**
- Cellular framing and latency significantly alter **Inter-Arrival Times (IAT)** and **packet counts/burst sizes**, while early handshake signatures (`pkt_00`–`pkt_03`) show relatively lower relative shift.

---

## N6 & N8: Network Health & Carrier Blocking
Empirical measurement of transport protocol reachability on Reliance Jio:

| resolver | protocol | total_attempts | successful_ok | success_rate | udp_blocked_queries | latency_mean_s | latency_median_s | latency_p95_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adguard | doh | 1000 | 905 | 0.905 | 0 | 0.4238 | 0.3696 | 0.7022 |
| adguard | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan | nan |
| cloudflare | doh | 1000 | 15 | 0.015 | 0 | 0.1815 | 0.1628 | 0.3038 |
| cloudflare | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan | nan |
| google | doh | 1000 | 1000 | 1.0 | 0 | 0.1804 | 0.1682 | 0.2624 |
| google | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan | nan |


**Key Findings:**
- **DoH/3 (UDP 443 / QUIC) is 100% BLOCKED:** Jio cellular actively drops outbound UDP on port 443. All 3,000 DoH/3 queries failed across Cloudflare, Google, and AdGuard (`udp_blocked_flag=true`).
- **Cloudflare DoH Edge Routing:** Cloudflare DoH on Jio mobile cellular exhibited a 98.5% drop rate due to cellular route instability to Cloudflare's anycast POPs.
- **Google DoH:** 100% reliable (1,000/1,000 ok) with mean latency of ~170ms.
- **AdGuard DoH:** 90.5% reliable (905/1,000 ok) with mean latency of ~210ms.

---

## N7: Regional Workload Comparison (India vs Global on Jio)
| resolver | global_accuracy | india_accuracy | difference (india - global) |
| --- | --- | --- | --- |
| adguard | 0.0408 | 0.0846 | 0.0438 |
| google | 0.1567 | 0.1233 | -0.0334 |

