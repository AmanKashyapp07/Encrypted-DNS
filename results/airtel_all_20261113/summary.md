# Airtel Analysis — All Work Packages

Generated: 2026-11-13  
Elapsed: 355s  
Skipped WPs: none

## WP7 — Feature Comparison (packet-size & post-handshake n-grams)

| workload | resolver | protocol | feature_set | accuracy | accuracy_seed_sd | domains | repeats_per_domain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | base | 0.2037 | 0.0086 | 99 | 10 |
| global | adguard | doh | packet_size_ngrams | 0.0152 | 0.0041 | 99 | 10 |
| global | adguard | doh | post_handshake_ngrams | 0.0152 | 0.0041 | 99 | 10 |
| global | adguard | doh3 | base | 0.0833 | 0.0103 | 100 | 10 |
| global | adguard | doh3 | packet_size_ngrams | 0.02 | 0.0041 | 100 | 10 |
| global | adguard | doh3 | post_handshake_ngrams | 0.02 | 0.0041 | 100 | 10 |

> **Note:** Burst n-grams are not reported (burst sequences not in feature table).

## WP8 — CNN/GRU Sequence Models

| workload | resolver | protocol | model | accuracy | accuracy_seed_sd | domains | epochs | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | cnn | 0.0101 | 0.0 | 99 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |
| global | adguard | doh | gru | 0.0135 | 0.0048 | 99 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |
| global | adguard | doh3 | cnn | 0.0217 | 0.0085 | 100 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |
| global | adguard | doh3 | gru | 0.01 | 0.0041 | 100 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |
| global | cloudflare | doh | cnn | 0.0135 | 0.0024 | 99 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |
| global | cloudflare | doh | gru | 0.0101 | 0.0041 | 99 | 20 | CPU-only; sequence = pkt_00..pkt_19 normalised per-sample |

## WP9 — Open-World Evaluation (monitored vs unmonitored)

| workload | resolver | protocol | n_monitored | n_unmonitored | seed | threshold | tpr_at_fpr5 | actual_fpr | closed_world_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | 10 | 89 | 17 | 0.6 | 0.15 | 0.0517 | 0.6667 |
| global | adguard | doh | 10 | 89 | 42 | 0.56 | 0.15 | 0.0517 | 0.6667 |
| global | adguard | doh | 10 | 89 | 101 | 0.57 | 0.15 | 0.0539 | 0.6667 |
| global | adguard | doh | 25 | 74 | 17 | 0.5505 | 0.08 | 0.05 | 0.75 |
| global | adguard | doh | 25 | 74 | 42 | 0.57 | 0.1 | 0.0541 | 0.8 |
| global | adguard | doh | 25 | 74 | 101 | 0.57 | 0.1 | 0.0527 | 0.8 |

> TPR @ FPR ≤ 5%. Threshold set on unmonitored confidence scores.

## WP10 — Scaling Curves

| workload | resolver | protocol | domain_count | repeat_count | accuracy | accuracy_seed_sd |
| --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | 10 | 4 | 0.2 | 0.0408 |
| global | adguard | doh | 25 | 4 | 0.26 | 0.0283 |
| global | adguard | doh | 50 | 4 | 0.1567 | 0.0125 |
| global | adguard | doh | 75 | 4 | 0.1289 | 0.0083 |
| global | adguard | doh | 100 | 4 | 0.1317 | 0.0085 |
| global | adguard | doh | 10 | 6 | 0.5 | 0.0816 |

> See wp10_scaling_curves.png for the full plot.

## WP11 — Time Stability (pilot → T0)

| workload | resolver | protocol | train_repeats | test_repeats | domains | n_train | n_test | accuracy | accuracy_seed_sd | ci_lo | ci_hi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | 0-7 (pilot) | 8-19 (T0) | 25 | 200 | 300 | 0.0422 | 0.0016 | 0.0255 | 0.0727 |
| global | adguard | doh3 | 0-7 (pilot) | 8-19 (T0) | 25 | 200 | 300 | 0.0711 | 0.0057 | 0.0462 | 0.1046 |
| global | cloudflare | doh | 0-7 (pilot) | 8-19 (T0) | 21 | 49 | 252 | 0.082 | 0.0082 | 0.0551 | 0.124 |
| global | cloudflare | doh3 | 0-7 (pilot) | 8-19 (T0) | 25 | 199 | 300 | 0.1111 | 0.0083 | 0.0794 | 0.1505 |
| global | google | doh | 0-7 (pilot) | 8-19 (T0) | 25 | 200 | 300 | 0.04 | 0.0027 | 0.023 | 0.0686 |
| global | google | doh3 | 0-7 (pilot) | 8-19 (T0) | 25 | 200 | 300 | 0.0844 | 0.0087 | 0.0571 | 0.1201 |

## WP13 — Defence Simulations (**SIMULATED**)

| workload | resolver | protocol | defence | accuracy | accuracy_seed_sd | domains | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global | adguard | doh | no_defence | 0.2037 | 0.0086 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |
| global | adguard | doh | pad_constant_64 | 0.1397 | 0.0063 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |
| global | adguard | doh | pad_constant_128 | 0.1397 | 0.0126 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |
| global | adguard | doh | pad_random_128 | 0.2054 | 0.0195 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |
| global | adguard | doh | jitter_50ms | 0.2155 | 0.0063 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |
| global | adguard | doh | jitter_200ms | 0.1953 | 0.0063 | 99 | SIMULATED — feature-vector perturbation, not measured traffic |

> **All results are simulated** (feature-vector perturbation, not measured traffic).
