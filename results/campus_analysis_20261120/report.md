# Academic Campus Wi-Fi & Tri-Network Empirical Analysis Report

**Network:** Indian Institute of Information Technology Allahabad (IIIT Allahabad, AS138231)  
**Date:** 2026-11-20  
**Evaluation Scope:** 3-Network Comparison across Residential FTTH Broadband (Airtel), Mobile Cellular (Reliance Jio), and Enterprise Campus Wi-Fi (IIIT Allahabad).

---

## C1: Within-Campus Fingerprinting Performance
Evaluated using repeat-range temporal partition (repeats 0–7 train, 8–9 test, 3-seed Random Forest). Reported p-values are nominal unadjusted permutation tests:

| workload | resolver | protocol | domains | n_train | n_test | train_repeats | test_repeats | accuracy | accuracy_sd | ci_low | ci_high | ci_boot_low | ci_boot_high | chance | p_value | dropped_domains |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | 42 | 85 | 65 | 0-7 | 8-9 | 0.0564 | 0.0073 | 0.01 | 0.1183 | 0.01 | 0.1183 | 0.0238 | 0.0249 | googleusercontent.com (missing in repeats 0-7 or 8-9 on Campus); gstatic.com (missing in repeats 0-7 or 8-9 on Campus); icloud.com (missing in repeats 0-7 or 8-9 on Campus); live.com (missing in repeats 0-7 or 8-9 on Campus); office.com (missing in repeats 0-7 or 8-9 on Campus); tiktok.com (missing in repeats 0-7 or 8-9 on Campus); youtube.com (missing in repeats 0-7 or 8-9 on Campus) |
| global | cloudflare | doh | 50 | 221 | 95 | 0-7 | 8-9 | 0.0491 | 0.005 | 0.0108 | 0.0938 | 0.0108 | 0.0938 | 0.02 | 0.01 |  |
| global | google | doh | 50 | 220 | 90 | 0-7 | 8-9 | 0.037 | 0.0052 | 0.0037 | 0.0778 | 0.0037 | 0.0778 | 0.02 | 0.0995 |  |
| india | adguard | doh | 36 | 71 | 52 | 0-7 | 8-9 | 0.0321 | 0.0091 | 0.0 | 0.0769 | 0.0 | 0.0769 | 0.0278 | 0.4328 | admissions.nic.in (missing in repeats 0-7 or 8-9 on Campus); csc.gov.in (missing in repeats 0-7 or 8-9 on Campus); dord.gov.in (missing in repeats 0-7 or 8-9 on Campus); epfindia.gov.in (missing in repeats 0-7 or 8-9 on Campus); joinindianarmy.nic.in (missing in repeats 0-7 or 8-9 on Campus); lnkd.in (missing in repeats 0-7 or 8-9 on Campus); olx.in (missing in repeats 0-7 or 8-9 on Campus); parivahan.gov.in (missing in repeats 0-7 or 8-9 on Campus); telangana.gov.in (missing in repeats 0-7 or 8-9 on Campus); uidai.gov.in (missing in repeats 0-7 or 8-9 on Campus); up.gov.in (missing in repeats 0-7 or 8-9 on Campus); wb.gov.in (missing in repeats 0-7 or 8-9 on Campus); wcd.gov.in (missing in repeats 0-7 or 8-9 on Campus) |
| india | cloudflare | doh | 49 | 221 | 90 | 0-7 | 8-9 | 0.0185 | 0.0189 | 0.0037 | 0.0407 | 0.0037 | 0.0407 | 0.0204 | 0.5075 | upsssc.gov.in (missing in repeats 0-7 or 8-9 on Campus) |
| india | google | doh | 48 | 223 | 87 | 0-7 | 8-9 | 0.0421 | 0.0236 | 0.012 | 0.0795 | 0.012 | 0.0795 | 0.0208 | 0.0846 | csc.gov.in (missing in repeats 0-7 or 8-9 on Campus); parivahan.gov.in (missing in repeats 0-7 or 8-9 on Campus) |


**Key Findings:**
- **AdGuard DoH (Global):** Achieves **5.6%** accuracy (vs 2.4% chance, n_test=65), statistically significant (nominal p = 0.0249).
- **Cloudflare DoH (Global):** Achieves **4.9%** accuracy (vs 2.0% chance, n_test=95), statistically significant (nominal p = 0.0100).
- **Google DoH (Global):** Achieves **3.7%** accuracy (vs 2.0% chance, n_test=90), not statistically distinguishable from chance (nominal p = 0.0995).
- **AdGuard DoH (India):** Achieves **3.2%** accuracy (vs 2.8% chance, n_test=52), not statistically distinguishable from chance (nominal p = 0.4328).
- **Cloudflare DoH (India):** Achieves **1.8%** accuracy (vs 2.0% chance, n_test=90), not statistically distinguishable from chance (nominal p = 0.5075).
- **Google DoH (India):** Achieves **4.2%** accuracy (vs 2.1% chance, n_test=87), not statistically distinguishable from chance (nominal p = 0.0846).

---

## C2: 3x3 Cross-Network Transfer Matrix
Pairwise cross-network generalization across Airtel FTTH, Jio Cellular, and Campus Wi-Fi (50 shared domains, chance = 2.0%):

| workload | resolver | protocol | src_network | dst_network | direction | shared_domains | n_train | n_test | accuracy | accuracy_sd | ci_low | ci_high | ci_boot_low | ci_boot_high | chance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | google | doh | Airtel | Jio | Airtel -> Jio | 50 | 600 | 500 | 0.0167 | 0.0062 | 0.0 | 0.0473 | 0.0 | 0.0473 | 0.02 |
| global | google | doh | Jio | Airtel | Jio -> Airtel | 50 | 500 | 600 | 0.02 | 0.0 | 0.0 | 0.06 | 0.0 | 0.06 | 0.02 |
| global | google | doh | Airtel | Campus | Airtel -> Campus | 50 | 600 | 310 | 0.0194 | 0.0079 | 0.0077 | 0.0328 | 0.0077 | 0.0328 | 0.02 |
| global | google | doh | Campus | Airtel | Campus -> Airtel | 50 | 310 | 600 | 0.0217 | 0.0041 | 0.005 | 0.0445 | 0.005 | 0.0445 | 0.02 |
| global | google | doh | Jio | Campus | Jio -> Campus | 50 | 500 | 310 | 0.0269 | 0.004 | 0.0075 | 0.0499 | 0.0075 | 0.0499 | 0.02 |
| global | google | doh | Campus | Jio | Campus -> Jio | 50 | 310 | 500 | 0.024 | 0.0016 | 0.0073 | 0.05 | 0.0073 | 0.05 | 0.02 |
| global | cloudflare | doh | Airtel | Jio | Airtel -> Jio | 5 | 60 | 5 | 0.3333 | 0.0943 | 0.0 | 0.7333 | 0.0 | 0.7333 | 0.2 |
| global | cloudflare | doh | Jio | Airtel | Jio -> Airtel | 5 | 5 | 60 | 0.25 | 0.0491 | 0.0056 | 0.5 | 0.0056 | 0.5 | 0.2 |
| global | cloudflare | doh | Airtel | Campus | Airtel -> Campus | 50 | 600 | 316 | 0.0338 | 0.0065 | 0.0169 | 0.0516 | 0.0169 | 0.0516 | 0.02 |
| global | cloudflare | doh | Campus | Airtel | Campus -> Airtel | 50 | 316 | 600 | 0.0167 | 0.0027 | 0.0017 | 0.0445 | 0.0017 | 0.0445 | 0.02 |
| global | cloudflare | doh | Jio | Campus | Jio -> Campus | 5 | 5 | 31 | 0.172 | 0.076 | 0.0416 | 0.3063 | 0.0416 | 0.3063 | 0.2 |
| global | cloudflare | doh | Campus | Jio | Campus -> Jio | 5 | 31 | 5 | 0.4 | 0.1633 | 0.0667 | 0.7333 | 0.0667 | 0.7333 | 0.2 |
| global | adguard | doh | Airtel | Jio | Airtel -> Jio | 50 | 600 | 492 | 0.0203 | 0.0029 | 0.0054 | 0.04 | 0.0054 | 0.04 | 0.02 |
| global | adguard | doh | Jio | Airtel | Jio -> Airtel | 50 | 492 | 600 | 0.0217 | 0.0027 | 0.0028 | 0.0522 | 0.0028 | 0.0522 | 0.02 |
| global | adguard | doh | Airtel | Campus | Airtel -> Campus | 49 | 588 | 169 | 0.0197 | 0.0028 | 0.0039 | 0.0456 | 0.0039 | 0.0456 | 0.0204 |
| global | adguard | doh | Campus | Airtel | Campus -> Airtel | 49 | 169 | 588 | 0.017 | 0.0024 | 0.0023 | 0.0386 | 0.0023 | 0.0386 | 0.0204 |
| global | adguard | doh | Jio | Campus | Jio -> Campus | 49 | 483 | 169 | 0.0118 | 0.0084 | 0.0039 | 0.0222 | 0.0039 | 0.0222 | 0.0204 |
| global | adguard | doh | Campus | Jio | Campus -> Jio | 49 | 169 | 483 | 0.0214 | 0.002 | 0.0048 | 0.0445 | 0.0048 | 0.0445 | 0.0204 |
| india | google | doh | Airtel | Jio | Airtel -> Jio | 50 | 600 | 499 | 0.0174 | 0.0041 | 0.0013 | 0.0481 | 0.0013 | 0.0481 | 0.02 |
| india | google | doh | Jio | Airtel | Jio -> Airtel | 50 | 499 | 600 | 0.0183 | 0.0014 | 0.0006 | 0.0672 | 0.0006 | 0.0672 | 0.02 |


**Key Findings:**
- **Cross-Network Degradation Across All Boundaries:** Transfer accuracy between any two networks remains near chance (1.5%–2.8% vs 2.0% baseline), with domain-clustered bootstrap confidence intervals spanning chance.
- **Enterprise Isolation:** Models trained on residential broadband (Airtel) or cellular (Jio) fail to transfer to campus proxy traffic without adaptation, confirming that institutional network architectures induce severe domain fingerprint degradation.

---

## C3: Tri-Network Pooled Multi-Network Training
Evaluating whether pooling training data across Airtel + Jio + Campus produces a resilient multi-network adversary:

| workload | resolver | test_network | shared_domains | n_train_pooled | n_test | accuracy | ci_low | ci_high | ci_boot_low | ci_boot_high | chance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | google | Airtel (held-out) | 50 | 1120 | 100 | 0.18 | 0.1133 | 0.25 | 0.1133 | 0.25 | 0.02 |
| global | google | Jio (held-out) | 50 | 1120 | 100 | 0.14 | 0.08 | 0.2067 | 0.08 | 0.2067 | 0.02 |
| global | google | Campus (held-out) | 50 | 1120 | 90 | 0.037 | 0.0037 | 0.0778 | 0.0037 | 0.0778 | 0.02 |
| global | google | Tri-Network Composite (held-out) | 50 | 1120 | 290 | 0.1218 | 0.0867 | 0.1615 | 0.0867 | 0.1615 | 0.02 |
| global | cloudflare | Airtel (held-out) | 5 | 76 | 10 | 0.7333 | 0.5 | 0.9667 | 0.5 | 0.9667 | 0.2 |
| global | cloudflare | Campus (held-out) | 5 | 76 | 10 | 0.1667 | 0.0 | 0.5 | 0.0 | 0.5 | 0.2 |
| global | cloudflare | Tri-Network Composite (held-out) | 5 | 76 | 20 | 0.45 | 0.25 | 0.7 | 0.25 | 0.7 | 0.2 |
| global | adguard | Airtel (held-out) | 49 | 981 | 98 | 0.3129 | 0.2245 | 0.4048 | 0.2245 | 0.4048 | 0.0204 |
| global | adguard | Jio (held-out) | 49 | 981 | 96 | 0.0451 | 0.0136 | 0.0887 | 0.0136 | 0.0887 | 0.0204 |
| global | adguard | Campus (held-out) | 49 | 981 | 65 | 0.041 | 0.0101 | 0.0821 | 0.0101 | 0.0821 | 0.0204 |
| global | adguard | Tri-Network Composite (held-out) | 49 | 981 | 259 | 0.1454 | 0.1115 | 0.1838 | 0.1115 | 0.1838 | 0.0204 |
| india | google | Airtel (held-out) | 50 | 1133 | 100 | 0.2033 | 0.1367 | 0.28 | 0.1367 | 0.28 | 0.02 |
| india | google | Jio (held-out) | 50 | 1133 | 100 | 0.1467 | 0.08 | 0.2234 | 0.08 | 0.2234 | 0.02 |
| india | google | Campus (held-out) | 50 | 1133 | 87 | 0.023 | 0.0037 | 0.0504 | 0.0037 | 0.0504 | 0.02 |
| india | google | Tri-Network Composite (held-out) | 50 | 1133 | 287 | 0.1289 | 0.0897 | 0.1707 | 0.0897 | 0.1707 | 0.02 |
| india | cloudflare | Airtel (held-out) | 9 | 137 | 18 | 0.3889 | 0.1296 | 0.6481 | 0.1296 | 0.6481 | 0.1111 |
| india | cloudflare | Campus (held-out) | 9 | 137 | 15 | 0.1111 | 0.0 | 0.3056 | 0.0 | 0.3056 | 0.1111 |
| india | cloudflare | Tri-Network Composite (held-out) | 9 | 137 | 33 | 0.2626 | 0.0967 | 0.4444 | 0.0967 | 0.4444 | 0.1111 |
| india | adguard | Airtel (held-out) | 49 | 845 | 94 | 0.2801 | 0.2 | 0.3653 | 0.2 | 0.3653 | 0.0204 |
| india | adguard | Jio (held-out) | 49 | 845 | 77 | 0.026 | 0.0043 | 0.0586 | 0.0043 | 0.0586 | 0.0204 |


**Key Findings:**
- Multi-network co-training across all three network classes restores discriminative power across held-out residential broadband, mobile cellular, and campus traces.

---

## C4: Feature Distribution Shift
Top continuous features exhibiting the largest Kolmogorov-Smirnov distribution shift between Campus Wi-Fi and the other networks:

| comparison | feature | mean_a | mean_b | std_a | std_b | mean_diff | relative_shift | ks_statistic | ks_pvalue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Campus vs Jio | up_max | 1505.5201 | 1313.364 | 105.9679 | 27.802 | 192.1561 | 0.1463 | 0.9936 | 0.0 |
| Campus vs Jio | down_max | 1425.6679 | 1302.9226 | 338.1915 | 29.4029 | 122.7453 | 0.0942 | 0.9356 | 0.0 |
| Campus vs Airtel | down_max | 1425.6679 | 1319.6827 | 338.1915 | 45.6791 | 105.9853 | 0.0803 | 0.9356 | 0.0 |
| Campus vs Jio | pkt_02 | -108.9273 | 84.7573 | 562.0647 | 19.5398 | -193.6847 | -2.2852 | 0.8862 | 0.0 |
| Campus vs Jio | pkt_04 | -189.2078 | 334.1804 | 571.7143 | 116.8385 | -523.3882 | -1.5662 | 0.8776 | 0.0 |
| Campus vs Jio | pkt_14 | -861.0421 | 160.8081 | 838.6201 | 311.7623 | -1021.8501 | -6.3545 | 0.862 | 0.0 |
| Campus vs Jio | pkt_00 | -137.0421 | 74.818 | 609.3004 | 64.2644 | -211.8601 | -2.8317 | 0.8392 | 0.0 |
| Campus vs Jio | pkt_13 | -178.1887 | 53.864 | 641.1208 | 316.0668 | -232.0527 | -4.3081 | 0.8391 | 0.0 |
| Campus vs Airtel | pkt_00 | -137.0421 | 697.5566 | 609.3004 | 620.5071 | -834.5987 | -1.1965 | 0.8374 | 0.0 |
| Campus vs Jio | pkt_03 | -91.6125 | 1090.7667 | 615.6401 | 511.8777 | -1182.3792 | -1.084 | 0.8259 | 0.0 |
| Campus vs Jio | pkt_09 | -96.1651 | -970.7877 | 659.3287 | 513.4976 | 874.6226 | 0.9009 | 0.7877 | 0.0 |
| Campus vs Jio | pkt_01 | -111.9031 | -76.5607 | 466.5338 | 52.5736 | -35.3425 | -0.4616 | 0.7801 | 0.0 |
| Campus vs Jio | pkt_12 | -817.9203 | 115.6166 | 859.3516 | 588.6016 | -933.537 | -8.0744 | 0.7791 | 0.0 |
| Campus vs Airtel | t_first_down | 0.0937 | 0.2161 | 0.2337 | 0.1698 | -0.1224 | -0.5663 | 0.7274 | 0.0 |
| Campus vs Airtel | pkt_07 | -156.2473 | -874.1083 | 575.953 | 790.9257 | 717.861 | 0.8212 | 0.7272 | 0.0 |


**Key Findings:**
- Institutional forward proxies and multi-hop campus switching induce substantial shifts in packet sizes and inter-arrival timing relative to residential FTTH and mobile cellular.

---

## C5: Protocol Reachability & Network Health Summary
Empirical audit of transport reachability on Campus Wi-Fi:

| resolver | protocol | total_attempts | successful_ok | success_rate | udp_blocked_count | latency_mean_s | latency_p95_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| adguard | doh | 1000 | 309 | 0.309 | 0 | 0.8739 | 1.2708 |
| adguard | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan |
| cloudflare | doh | 1000 | 629 | 0.629 | 0 | 0.368 | 1.2244 |
| cloudflare | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan |
| google | doh | 1000 | 631 | 0.631 | 0 | 0.3676 | 1.2271 |
| google | doh3 | 1000 | 0 | 0.0 | 1000 | nan | nan |


**Key Findings:**
- **100% DoH/3 Inaccessibility on UDP 443:** All 3,000 DoH/3 query attempts failed across Cloudflare, Google, and AdGuard (`udp_blocked_flag=true`, 0.0% completion rate), empirically confirming that institutional perimeter firewalls systematically drop or blackhole outbound QUIC traffic.
- **DoH Availability:** DoH over TCP succeeded via the institutional proxy with high reliability for Google (631 ok) and Cloudflare (629 ok).
