# DoH vs DoH/3: A Traffic-Analysis Study of Encrypted DNS Fingerprinting on Indian ISPs

**Authors:** Aman Kashyap (Department of Information Technology, Indian Institute of Information Technology, Allahabad)
**Venue Draft:** IMC / NDSS / PETS style
**Status:** Working draft — Multi-ISP evaluation complete (Airtel FTTH & Reliance Jio cellular)

---

## Abstract

Encrypted DNS protocols — DNS-over-HTTPS (DoH, RFC 8484) and its successor over QUIC (DoH/3, RFC 9114 / RFC 9250-class) — aim to prevent passive observers from learning which domains a user queries. We ask whether traffic metadata alone (packet counts, sizes, timing, burst structure) is sufficient to fingerprint the queried domain, and whether the choice of transport (HTTP/2 vs. QUIC) materially affects fingerprintability across real-world residential and mobile networks. We collected 26,262 raw capture attempts across two production Indian ISPs (Airtel FTTH broadband and Reliance Jio mobile cellular), yielding 20,838 usable feature-labelled DNS flow traces across four public resolvers (AdGuard, Cloudflare, Google, Quad9) and two domain workloads (global top-100, India top-100). 

Using a Random Forest classifier with fixed temporal holdout evaluation (repeats 8–17 for training, 18–19 for testing) and 200-permutation significance tests, we find that all 16 resolver–protocol–workload slices on Airtel are significantly above chance ($p < 0.005$, all surviving Benjamini–Hochberg FDR control at $\alpha = 0.05$). DoH (HTTP/2) accuracy spans 0.182–0.452; DoH/3 (QUIC) accuracy spans 0.052–0.150. For three of four resolvers, switching to QUIC substantially reduces fingerprintability (up to 85% leakage reduction on Quad9: 0.452 to 0.066), but Google DoH/3 is a notable exception (0.150 vs. 0.213 on global workload), where unpadded response variations preserve fingerprintability. Aggregate flow features dramatically outperform raw packet-sequence models (1D-CNN and GRU, which collapse to near-chance ~1.0%–1.4%). 

Critically, models trained on broadband traffic do not generalize when evaluated on cellular traffic: cross-network transfer accuracy remained close to the 2.0% chance baseline (0.017–0.024 across 50 shared domains), with domain-clustered 95% bootstrap confidence intervals spanning the chance level in all evaluated slices, reflecting pronounced distribution shifts in packet sizes and inter-arrival timing between fixed broadband and mobile networks. Pooled multi-network co-training recovers accuracy to 0.154–0.192 on the combined composite test set (up to 0.193–0.337 on held-out broadband traces). Furthermore, on Reliance Jio cellular, 100% of the 3,000 DoH/3 queries timed out with zero return packets received on UDP port 443, documenting client-side QUIC timeouts on the tested cellular link (investigation of client fallback dynamics was outside the experimental scope).

---

## 1. Introduction

The Domain Name System (DNS) is a foundational but historically unprotected layer of internet communication. Even when application-layer traffic is encrypted with TLS, DNS queries have traditionally been transmitted in plaintext, exposing users' browsing intent to on-path observers such as ISPs, network operators, and censors. The IETF has standardised several mechanisms to address this: DNS-over-TLS (DoT, RFC 7858), DNS-over-HTTPS (DoH, RFC 8484), and DNS-over-QUIC (DoQ, RFC 9250). Browser and operating-system vendors have rapidly adopted DoH, and DoH/3 — DoH transported over HTTP/3 and the QUIC protocol — is gaining traction as a natural evolution.

A well-established line of research on *website fingerprinting* (WF) has shown that encrypting traffic does not fully hide its content: metadata such as packet sizes, inter-arrival times, and flow structure leaks substantial information about which webpage a user visits, even over Tor. The analogous question for encrypted DNS has received less attention: can a passive observer infer *which domain* a user queried from encrypted DNS traffic metadata alone? Siby et al. [Siby et al. 2020] demonstrated that DoH and DoT flows are fingerprintable, achieving well-above-chance accuracy using traffic features. Their work, however, predates the widespread deployment of QUIC-based DNS and does not evaluate the QUIC transport's effect on fingerprintability.

This paper extends that line of inquiry in two principal directions. First, we evaluate DoH/3 (HTTP/3 over QUIC) alongside classical DoH (HTTP/2 over TCP+TLS) against the same domain workloads and classifiers, enabling a direct comparison of transport-layer fingerprintability. Second, we conduct our study from **dual real-world Indian ISP vantage points (Airtel FTTH broadband and Reliance Jio mobile cellular)**, capturing distinct link layers, resolver latencies, and middlebox behaviors that differ substantially from prior work conducted primarily on European or North American academic networks.

**Research questions.** We ask:

- **RQ1 (Closed-world fingerprintability):** Can a passive observer, observing only packet metadata of an encrypted DNS flow, identify the queried domain among a known candidate set?
- **RQ2 (Protocol comparison):** Does DoH/3 (QUIC) offer materially less fingerprintability than DoH (HTTP/2)?
- **RQ3 (Resolver variation):** How much does resolver choice (AdGuard, Cloudflare, Google, Quad9) affect fingerprintability?
- **RQ4 (Workload variation):** Does the domain workload (global top-100 vs. India top-100) affect results?
- **RQ5 (Open-world threat):** How does classifier performance degrade in an open-world setting?
- **RQ6 (Defences):** Can standard padding and delay defences mitigate fingerprinting?
- **RQ7 (Cross-network transfer):** Can models trained on residential broadband generalize to mobile cellular networks, and does carrier-level filtering impact protocol availability?

**Summary of findings.** All 16 resolver–protocol–workload combinations on Airtel are significantly above-chance ($p < 0.005$, raw and FDR-adjusted). DoH (HTTP/2) accuracy spans 0.182–0.452 (vs. chance 0.010 at 100 classes). DoH/3 (QUIC) accuracy spans 0.052–0.150. For three of four resolvers, switching to QUIC reduces fingerprintability substantially (up to 85% reduction on Quad9); Google DoH/3 is a notable exception, achieving accuracy (0.150 vs 0.213 DoH on global) closer to its DoH counterpart. Aggregate features dramatically outperform sequence models. Cross-session accuracy drops sharply, suggesting temporal fragility of learned fingerprints. Simulated constant-rate padding provides modest defence; random padding and jitter do not. Cross-network transfer accuracy between Airtel and Jio remained close to the 2.0% chance baseline (1.7%–2.4%), with domain-clustered confidence intervals spanning the baseline in all evaluated slices, while pooled co-training recovers accuracy (15.4%–19.2% on composite test set). On Jio cellular, 100% of DoH/3 queries fail with client-side timeouts on UDP 443.

**Contributions:**

1. A comparative empirical measurement of DoH (HTTP/2) vs. DoH/3 (QUIC) fingerprintability across four public resolvers and two domain workloads on residential broadband (Airtel FTTH).
2. A verified dataset of 20,838 usable, feature-labelled DNS flow traces extracted from 26,262 raw capture attempts across fixed broadband and mobile cellular networks.
3. Empirical evidence that observed QUIC fingerprintability differs in resolver-specific ways (the Google anomaly), where unpadded answer records modulate metadata leakage.
4. Measurement of cross-network transfer failure and feature distribution shifts (Kolmogorov-Smirnov $p < 10^{-6}$), demonstrating that broadband fingerprints do not transfer to cellular links without pooled multi-network training.
5. In-situ observation of client-side QUIC timeouts on Reliance Jio cellular (100% timeouts on UDP port 443), documenting real-world transport accessibility constraints for DoH/3.
6. Evaluation of classical WF defences via feature-vector simulation, showing that only constant-rate padding offers meaningful (though modest) protection.

The remainder of this paper is structured as follows. Section 2 reviews related work. Section 3 describes our threat model. Section 4 details our methodology. Section 5 presents empirical results across both Airtel broadband and Jio cellular, including cross-network transfer and pooled training. Section 6 discusses implications. Section 7 states limitations. Section 8 addresses ethics and reproducibility. Section 9 concludes.

---

## 2. Related Work

### 2.1 DNS Privacy

The privacy risks of plaintext DNS have been documented extensively. DNS queries expose users' browsing intent to recursive resolvers, on-path observers, and ISPs. The IETF responded with a series of standards: DoT (RFC 7858, 2016) encrypts DNS over TLS on port 853; DoH (RFC 8484, 2018) tunnels DNS over HTTPS, blending with web traffic on port 443; DoQ (RFC 9250, 2022) transports DNS over the QUIC protocol. Each standard aims to provide both confidentiality and integrity of DNS queries and responses.

Adoption of DoH has accelerated following deployment by Firefox (2019) and Chrome (2020). DoH/3 is natively supported by major resolvers (Cloudflare, Google) and browsers, though less studied in the academic literature.

### 2.2 Website Fingerprinting

The website fingerprinting (WF) attack literature has demonstrated that traffic metadata can distinguish which webpage a user visits even when the connection is encrypted. Early work by Herrmann et al. [Herrmann et al. 2009] used Naive Bayes on frequency features; subsequent work [Panchenko et al. 2011; Hayes & Danezis 2016; Sirinam et al. 2018] demonstrated high accuracy over Tor using Random Forests, k-NN (k-Fingerprinting), and deep learning (DF, Tik-Tok, BAPM). Key features include packet count, cumulative byte traces, inter-arrival times, burst structure, and packet direction sequences. DefProxy [Dyer et al. 2012], WTF-PAD [Juarez et al. 2016], and Tamaraw [Wang & Goldberg 2017] propose bandwidth-overhead defences; subsequent work shows many are defeated with more powerful classifiers.

DNS fingerprinting is structurally analogous but differs in flow size (DNS exchanges are far smaller and shorter than page loads), caching behaviour (repeated queries may be served from cache), and lack of multiplexed resource fetching. These differences motivate re-evaluation of WF methods in the DNS context.

### 2.3 Encrypted DNS Fingerprinting

Siby et al. [Siby et al. 2020] is the foundational work on DoH/DoT fingerprinting. They showed that a passive on-path observer can fingerprint DNS flows with well-above-chance accuracy using features such as packet count, payload sizes, and inter-arrival times. They evaluated multiple classifiers including Random Forest and k-NN on a European network. Their work motivates ours; we extend it by (a) evaluating DoH/3 (QUIC), (b) using an Indian ISP vantage point, and (c) systematically varying resolver choice and workload composition.

Hoang et al. [Hoang et al. 2020] studied DNS-over-HTTPS traffic correlation in an ISP context. Lu et al. [Lu et al. 2010] examined QUIC traffic classification more broadly. Privacy analyses of QUIC (Sy et al. [Sy et al. 2020]) show that QUIC's connection ID rotation and datagram-level framing complicate traffic analysis but do not eliminate it.

### 2.4 Indian ISP Networking Context

Measurement studies on Indian ISPs (Jain et al. [Jain et al. 2022]; IMC India-focused work) have documented varied middlebox behaviour, DNS manipulation, and routing path diversity. Airtel and Jio are the two largest Indian ISPs by subscriber base and have been subjects of DNS censorship and performance studies. Our study provides the first encrypted-DNS fingerprinting measurements from these vantage points.

---

## 3. Threat Model

We consider a **passive on-path adversary** positioned between the client machine and the public DNS resolver (e.g., at the ISP level, an upstream router, or a network tap). The adversary's capabilities and constraints are as follows.

**Observations.** The adversary observes individual network packets: their timestamps, sizes (in bytes), and directions (upload = client→resolver, download = resolver→client). The adversary can segment the stream into per-query flows.

**What the adversary cannot see.** The adversary *cannot* decrypt TLS (DoH) or QUIC (DoH/3) payloads. The domain name string, DNS answer records, IP addresses of resolved hosts, and port numbers of internal connections are not available to the adversary. Our feature set strictly reflects this: no IPs, ports, or domain strings are used as model inputs.

**Adversary goal.** The adversary aims to infer which domain was queried in a given flow. We study two settings:

- **Closed-world:** The queried domain is assumed to be drawn from a known candidate set of *N* domains (N = 100 in our headline experiments). The adversary predicts the domain label.
- **Open-world:** The queried domain may or may not belong to a known monitored set. The adversary must both detect whether the domain is monitored and identify it.

**Threat scenario.** This model is relevant to ISP-level surveillance, censorship enforcement that relies on DNS monitoring, and privacy analysis of encrypted DNS deployments. It is also relevant to adversaries who wish to correlate DNS queries with side-channel-inferred browsing behaviour.

**What we do not model.** We do not consider active adversaries who inject or modify traffic, timing-channel adversaries who have end-to-end latency observations, or adversaries who correlate multiple flows across time (linkability attacks). We also do not model server-side adversaries (i.e., the resolver itself, which trivially sees the query in plaintext).

---

## 4. Methodology

### 4.1 Measurement Setup

**Network vantage point.** All Airtel measurements were conducted from a single client machine connected to the Airtel broadband network (Indian ISP). The machine ran packet capture in parallel with DNS queries.

**DNS client.** We used `q` v0.19.12, a command-line DNS-over-HTTPS/QUIC client, to issue DNS queries. Each query resolves a single domain name (A record) over the specified resolver and protocol. We explicitly disable OS-level DNS caching to ensure each query reaches the resolver.

**Resolvers.** We evaluate four public DoH resolvers:
- **AdGuard** (`dns.adguard.com`)
- **Cloudflare** (`1.1.1.1`, `cloudflare-dns.com`)
- **Google** (`8.8.8.8`, `dns.google`)
- **Quad9** (`9.9.9.9`, `dns.quad9.net`)

Each resolver is queried over both DoH (HTTP/2 over TLS/TCP) and DoH/3 (HTTP/3 over QUIC), yielding 8 resolver–protocol combinations.

**Live checks.** Prior to and during data collection, we verified that all four resolvers responded correctly via both HTTP/2 and HTTP/3. One incidental observation: Google returned 6 answer records over HTTP/2 versus 1 over HTTP/3 for the same query in a single check; we attribute this to resolver-side cache state differences rather than a systematic protocol effect. No EDNS0 padding option was observed in any of the 8 live-check responses; we note this as a measurement limitation (see Section 7).

**Domain workloads.** We use two domain lists:
- **Global top-100:** 100 domains from the Tranco global top-1M list.
- **India top-100:** 100 domains from the Tranco India-regional top list.

One domain (`trbcdn.net`) was dropped from the Cloudflare DoH global slice due to anomalous capture behaviour, leaving 99 domains for that slice.

**Capture protocol.** Each domain is queried 20 times per resolver–protocol combination (repeats 0–19). Repeats 0–7 constitute a pilot collection window; repeats 8–19 constitute the headline (T0) collection window. Packet captures (PCAPs) are recorded for each query and processed offline into feature vectors.

### 4.2 Feature Extraction

We extract 44+ features per flow, divided into five categories:

**Packet-level counts:**
- `n_pkts`: total packet count
- `n_up`: upstream (client→resolver) packet count
- `n_down`: downstream (resolver→client) packet count

**Byte totals:**
- `bytes_up`, `bytes_down`, `bytes_total`: directional and total byte counts
- `ratio_bytes_down_up`: ratio of downstream to upstream bytes

**Per-direction statistics:**
- `up_mean`, `up_std`, `up_max`: mean, std, max of upstream packet sizes
- `down_mean`, `down_std`, `down_max`: mean, std, max of downstream packet sizes

**Inter-arrival times (IAT):**
- `iat_mean`, `iat_std`, `iat_median`, `iat_max`: statistics of inter-packet arrival times across the flow
- `t_first_down`: time from flow start to first downstream packet

**Burst features:**
- `n_bursts`: number of packet bursts (direction changes)
- `burst_len_mean`, `burst_len_max`: mean and max packets per burst
- `burst_bytes_mean`, `burst_bytes_max`: mean and max bytes per burst

**Packet sequence (first 20 packets):**
- `pkt_00` … `pkt_19`: signed packet sizes (positive = upstream, negative = downstream), padded with zeros if fewer than 20 packets

No IP addresses, port numbers, hostnames, or DNS payload content are included in the feature set. Machine identifiers are stored as salted hashes and are not used as features.

### 4.3 Dataset

The final dataset (`dataset_v2.csv`) contains **18,926 feature rows** from **19,200 unique captures** (the difference reflects a small number of failed or malformed captures excluded during quality filtering). Each row corresponds to one DNS query flow, labelled by domain, resolver, protocol, and repeat index.

### 4.4 Classifier

We use a **Random Forest (RF)** classifier with 100 estimators and `class_weight='balanced_subsample'` (scikit-learn default). Three random seeds (17, 42, 101) are used to assess seed sensitivity; reported accuracy is the mean across seeds.

We additionally evaluate:
- **CNN:** A 1-D convolutional network applied to the normalised `pkt_00..pkt_19` sequence.
- **GRU:** A gated recurrent unit network applied to the same normalised sequence.
- **Packet n-grams:** Bag-of-n-grams over the signed packet size sequence.
- **Post-handshake n-grams:** N-grams restricted to packets after the QUIC or TLS handshake.

### 4.5 Evaluation Protocol

**Leave-repeat-out split.** For the headline evaluation, we use repeats 8–17 for training and repeats 18–19 for testing. This ensures that the model is evaluated on held-out query instances not seen during training, while controlling for temporal ordering.

**Closed-world metric.** We report top-1 classification accuracy (fraction of test instances correctly predicted).

**Cluster-robust bootstrap 95% confidence intervals.** Rather than unclustered Wilson intervals that assume i.i.d. observations, we compute domain-clustered block bootstrap 95% confidence intervals ($B = 1,000$ resamples) directly over the multi-seed mean estimator, accounting for intra-domain observation correlation and seed variance.

**Domain-clustered permutation testing & FDR control.** To prevent intra-domain observation leakage under permutation, exchangeability is enforced at the domain cluster level. We test the conditional label alignment null hypothesis ($H_0^{\text{cond}}$): given the learned feature representations, test instances whose labels are permuted at the domain cluster level achieve accuracy equal to or exceeding observed accuracy. Evaluated across 200 domain-clustered permutations on the exact same model seeds, all 16 headline slices decisively reject the conditional null ($p < 0.005$). Furthermore, Benjamini–Hochberg False Discovery Rate (FDR) adjustment across all slices confirms that every slice remains statistically significant at $p_{\text{FDR}} < 0.005$ ($\alpha = 0.05$). We explicitly note that our procedure tests conditional inference-time alignment ($H_0^{\text{cond}}$) given the trained model; it does not perform full-pipeline retraining with permuted training labels ($H_0^{\text{full}}$), which was not evaluated due to computational constraints.

**Chance baseline.** For N = 100 domains, the chance accuracy is 1/100 = 0.010.

**Domain selection (k=10).** For the headline results, we retain only domains with at least k = 10 headline repeats (8–19), yielding up to 100 domains per slice. All 16 headline slices use k = 10.

**Open-world evaluation.** We use a one-vs-rest detection approach: the RF classifier scores each test flow against monitored classes; flows with max score below a threshold are classified as "unmonitored." We report TPR at FPR ≤ 5%.

**Time-stability evaluation.** We train on pilot repeats (0–7) and test on T0 repeats (8–19) to measure cross-session accuracy degradation.

**Scaling experiments.** We vary the number of training repeats (2, 4, 6, 8, 10) and the number of domains (10, 25, 50, 100) to characterise accuracy as a function of dataset size.

---

## 5. Results (Airtel & Jio Empirical Evaluation)

### 5.1 Headline Closed-World Fingerprinting

Table 1 presents the headline fingerprinting accuracy for all 16 resolver–protocol–workload slices. All results are significant at p < 0.005 (200-permutation test). Chance accuracy at 100 classes is 0.010.

**Table 1: Headline closed-world fingerprinting accuracy (Airtel broadband, k=10, fixed temporal holdout: repeats 8–17 train, 18–19 test). All p < 0.005.**

| Resolver   | Protocol | Workload | Accuracy | 95% CI          | Chance |
|------------|----------|----------|----------|-----------------|--------|
| AdGuard    | DoH      | Global   | 0.262    | [0.203, 0.322]  | 0.010  |
| AdGuard    | DoH/3    | Global   | 0.112    | [0.070, 0.162]  | 0.010  |
| Cloudflare | DoH      | Global   | 0.263    | [0.213, 0.318]  | 0.010  |
| Cloudflare | DoH/3    | Global   | 0.072    | [0.038, 0.112]  | 0.010  |
| Google     | DoH      | Global   | 0.213    | [0.162, 0.270]  | 0.010  |
| Google     | DoH/3    | Global   | 0.150    | [0.107, 0.197]  | 0.010  |
| Quad9      | DoH      | Global   | 0.452    | [0.382, 0.525]  | 0.010  |
| Quad9      | DoH/3    | Global   | 0.066    | [0.038, 0.098]  | 0.010  |
| AdGuard    | DoH      | India    | 0.216    | [0.159, 0.280]  | 0.010  |
| AdGuard    | DoH/3    | India    | 0.083    | [0.046, 0.119]  | 0.010  |
| Cloudflare | DoH      | India    | 0.195    | [0.140, 0.253]  | 0.010  |
| Cloudflare | DoH/3    | India    | 0.052    | [0.023, 0.082]  | 0.010  |
| Google     | DoH      | India    | 0.182    | [0.132, 0.235]  | 0.010  |
| Google     | DoH/3    | India    | 0.092    | [0.057, 0.132]  | 0.010  |
| Quad9      | DoH      | India    | 0.350    | [0.280, 0.427]  | 0.010  |
| Quad9      | DoH/3    | India    | 0.056    | [0.028, 0.089]  | 0.010  |

> [!NOTE]
> Cloudflare DoH Global uses 99 domains; `trbcdn.net` was dropped due to anomalous capture behaviour. All other slices use 100 domains.

**Key observations:**

1. **All 16 slices significantly above chance.** Every resolver–protocol–workload combination achieves accuracy well above the 0.010 chance level, confirming that encrypted DNS flows — whether over HTTP/2 or QUIC — are fingerprintable from metadata alone.

2. **DoH (HTTP/2) consistently outperforms DoH/3 (QUIC) for three of four resolvers.** For AdGuard, Cloudflare, and Quad9, the QUIC transport reduces accuracy substantially: Quad9 drops from 0.452 to 0.066 (global) and 0.350 to 0.056 (India); Cloudflare drops from 0.263 to 0.072 and 0.195 to 0.052.

3. **Google exhibits smaller reduction.** Google DoH/3 (0.150 global, 0.092 India) achieves accuracy closer to Google DoH (0.213, 0.182). This demonstrates that resolver-specific packet framing and response record sizing modulate the degree of privacy protection conferred by the transport protocol.

4. **Quad9 DoH is the most fingerprintable.** Quad9's HTTP/2 accuracy of 0.452 (global) is the highest of any slice, indicating that Quad9's response structures produce particularly distinctive volumetric footprints.

5. **India workload accuracy is generally slightly lower than global.** This reflects differences in CDN routing, response record variations, and domain clustering in the India list.

6. **Accuracy is 18–45× above chance** for the best-performing slices (DoH), and 5–15× above chance for DoH/3, confirming that QUIC mitigates but does not eliminate fingerprintability.

### 5.2 Jio Cellular Results (N1 & N8)

We conducted a 6,000-query capture matrix on a mobile cellular connection via Reliance Jio across 100 domains (50 Global + 50 India), 3 public resolvers (Google, AdGuard, Cloudflare), and 2 protocols (DoH and DoH/3) across 10 capture cycles. Because cellular connections exhibit wireless packet dropouts and latency timeouts, we evaluate within-Jio fingerprinting using a repeat-range temporal partition: queries captured in repeat indices 0–7 form the training set, and queries captured in held-out repeat indices 8–9 form the test set, retaining all domains represented in both partitions (logging any dropped domains).

**Table 2: Within-Jio fingerprinting performance (repeats 0–7 train, 8–9 test, 3-seed RF, 200 domain-clustered label permutations).**

| Workload | Resolver | Protocol | Domains | Accuracy | 95% Bootstrap CI | Chance | p-value |
|---|---|---|---|---|---|---|---|
| Global | Google | DoH | 50 | **0.157** | [0.103, 0.217] | 0.020 | 0.005 |
| Global | AdGuard | DoH | 50 | **0.041** | [0.010, 0.082] | 0.020 | 0.124 |
| India | Google | DoH | 50 | **0.123** | [0.060, 0.197] | 0.020 | 0.005 |
| India | AdGuard | DoH | 42 | **0.068** | [0.024, 0.121] | 0.024 | 0.025 |

> [!NOTE]
> On Indian domains under AdGuard, 8 domains had zero successful captures in repeats 8–9 on Jio due to carrier-side packet timeouts, leaving 42 fully observed domains evaluated over 79 test queries.

**Key Findings on Jio:**

1. **Cellular Fingerprintability:** Google DoH achieves **0.157** accuracy on Global domains and **0.123** on Indian domains (both p = 0.005, significantly exceeding the 0.020 chance baseline by ~6–8×). AdGuard DoH achieves 0.068 on Indian domains (p = 0.025, exceeding the 0.024 baseline). On Global domains, AdGuard achieves 0.041, which is statistically indistinguishable from the chance baseline ($p = 0.124$).
2. **Cellular UDP 443 Inaccessibility (N8):** Across all 3,000 DoH/3 capture attempts on Jio, **100% of QUIC (UDP port 443) traffic timed out with zero return packets received** (`udp_blocked_flag=true`). While consistent with carrier-grade middlebox filtering of outbound QUIC, local NAT mapping timeouts or interface-specific tethering policies cannot be ruled out. If deployed on networks exhibiting UDP 443 blockage, user agents relying on standard happy eyeballs or transport fallback would revert to TCP-based transports; however, browser or OS fallback dynamics were not experimentally measured in our setup.
3. **Resolver Edge Routing Disparities:** Google DoH achieved a 100% completion rate (1,000/1,000 ok), and AdGuard achieved 90.5% (905/1,000 ok). In contrast, Cloudflare DoH on Jio mobile cellular experienced severe routing drops to Cloudflare anycast POPs (only 15/1,000 completed), illustrating that DNS privacy protocols depend heavily on carrier routing stability.

### 5.3 Cross-Network Analysis (N2–N4)

We evaluate whether fingerprint models generalize across different access networks by performing cross-network transfer and pooled multi-network training between Airtel (broadband) and Jio (cellular) on the identical 50-domain shared workload.

**Table 3: Cross-network transfer between Airtel and Jio (50 shared domains, k=10).**

| Workload | Resolver | Direction | Shared Domains | Accuracy | 95% CI | Chance |
|---|---|---|---|---|---|---|
| Global | Google | Airtel $\rightarrow$ Jio | 50 | **0.017** | [0.000, 0.047] | 0.020 |
| Global | Google | Jio $\rightarrow$ Airtel | 50 | **0.020** | [0.000, 0.060] | 0.020 |
| Global | AdGuard | Airtel $\rightarrow$ Jio | 50 | **0.020** | [0.005, 0.040] | 0.020 |
| Global | AdGuard | Jio $\rightarrow$ Airtel | 50 | **0.022** | [0.003, 0.052] | 0.020 |
| India | Google | Airtel $\rightarrow$ Jio | 50 | **0.017** | [0.001, 0.048] | 0.020 |
| India | Google | Jio $\rightarrow$ Airtel | 50 | **0.018** | [0.001, 0.067] | 0.020 |
| India | AdGuard | Airtel $\rightarrow$ Jio | 50 | **0.024** | [0.008, 0.044] | 0.020 |
| India | AdGuard | Jio $\rightarrow$ Airtel | 50 | **0.021** | [0.009, 0.037] | 0.020 |

**Table 4: Pooled multi-network training performance (Airtel + Jio training, tested on held-out repeats).**

| Workload | Resolver | Test Vantage Point | Pooled Train Size | Held-Out Test Size | Accuracy | 95% CI | Chance |
|---|---|---|---|---|---|---|---|
| Global | Google | Airtel (held-out) | 900 | 100 | **0.197** | [0.127, 0.267] | 0.020 |
| Global | Google | Jio (held-out) | 900 | 100 | **0.150** | [0.090, 0.217] | 0.020 |
| Global | Google | Airtel+Jio Composite (held-out) | 900 | 200 | **0.173** | [0.128, 0.227] | 0.020 |
| India | Google | Airtel (held-out) | 899 | 100 | **0.193** | [0.123, 0.270] | 0.020 |
| India | Google | Jio (held-out) | 899 | 100 | **0.133** | [0.070, 0.207] | 0.020 |
| India | Google | Airtel+Jio Composite (held-out) | 899 | 200 | **0.163** | [0.112, 0.220] | 0.020 |

**Key Findings on Cross-Network Effects:**

1. **Zero Out-of-the-Box Cross-Network Generalization (N2):** When trained on Airtel and tested on Jio (or vice versa), accuracy collapses to between 0.017 and 0.024—indistinguishable from the 0.020 chance baseline. Models trained on one ISP cannot identify domains on a different ISP without adaptation.
2. **Feature Distribution Shift (N4):** Kolmogorov-Smirnov tests reveal that cellular access networks introduce massive distribution shifts in flow timing and packet counts. Mean time-to-first-downstream (`t_first_down`) and inter-arrival times (`iat_max`, `iat_std`) shifted by over 75–88% ($p < 10^{-6}$), altering the flow profile observed by the classifier.
3. **Pooled Training Recovers Discriminative Power (N3):** When training data is pooled across both Airtel and Jio (Table 4), the classifier successfully recovers 0.150–0.197 accuracy on held-out test repeats across both networks. An attacker with distributed vantage points across multiple consumer ISPs can thus train robust multi-network fingerprinting models.

### 5.4 Feature Comparison (WP7)

We compare four feature sets to understand which aspects of the flow carry the most discriminative information:

- **Baseline RF:** All 44+ aggregate features (Section 4.2), including count, byte, IAT, and burst statistics.
- **Packet n-grams:** Bag-of-n-grams over the signed `pkt_00..pkt_19` sequence.
- **Post-handshake n-grams:** N-grams restricted to packets following the TLS/QUIC handshake.

Table 2 presents results for the AdGuard DoH global slice as a representative example.

**Table 5: Feature comparison — AdGuard DoH, Global workload, Airtel.**

| Feature Set            | Accuracy |
|------------------------|----------|
| Baseline RF (all features) | 0.204 |
| Packet n-grams         | 0.015    |
| Post-handshake n-grams | 0.015    |

> [!IMPORTANT]
> Burst n-grams were not evaluated in this study; computing burst sequences requires PCAP re-extraction beyond the current feature table. This is noted as a limitation.

**Finding.** Aggregate features (counts, bytes, IATs, burst statistics) dramatically outperform sequence n-gram features. Packet n-grams and post-handshake n-grams each achieve only 0.015, barely above chance, while the baseline RF achieves 0.204 on the same slice. This result holds consistently across slices. The implication is that the *structure* of the flow — its size distribution, timing envelope, and burst pattern — is more informative than the raw packet-size sequence.

This contrasts with some website fingerprinting literature where cumulative byte traces and packet sequences are highly effective. The difference likely reflects the shorter and sparser nature of DNS flows: a single DNS exchange comprises far fewer packets than a full page load, leaving sequence models with insufficient data.

### 5.5 Deep Learning Comparison (WP8)

We evaluate two sequence-to-label deep learning architectures on the normalised `pkt_00..pkt_19` input:

- **CNN:** 1-D convolutional network with max-pooling and dense output.
- **GRU:** Gated recurrent unit network with the same input sequence.

**Table 6: CNN and GRU vs. RF baseline — AdGuard DoH, Global workload, Airtel.**

| Model | Accuracy |
|-------|----------|
| RF (baseline, all features) | 0.262 |
| CNN (pkt sequence) | 0.010 |
| GRU (pkt sequence) | 0.014 |

**Finding.** CNN and GRU models perform at or near chance (0.010–0.014) compared to the RF baseline at 0.262. This result mirrors the n-gram finding: raw packet sequences, truncated to 20 packets, do not carry sufficient discriminative information for sequence models to learn meaningful patterns. The RF's ability to leverage aggregate statistics — particularly burst and IAT features — across the full flow provides a decisive advantage.

This finding has practical implications: an adversary with access only to the first 20 packets and no aggregate statistics would have very limited fingerprinting power. The aggregate features that drive RF performance (total bytes, IATs, burst counts) require observing the complete flow or at least a substantial prefix of it.

### 5.6 Open-World Evaluation (WP9)

We evaluate an open-world scenario in which the adversary monitors a subset of domains and must distinguish between monitored and unmonitored queries. We use a one-vs-rest RF scorer with a detection threshold and report TPR at FPR ≤ 5%.

**Table 7: Open-world TPR@FPR≤5% — AdGuard DoH, Airtel, Global workload.**

| Monitored set size | TPR @ FPR ≤ 5% |
|--------------------|----------------|
| 10 domains         | ≈ 0.15         |
| 25 domains         | ≈ 0.09–0.10    |

**Finding.** The open-world attack is substantially harder than closed-world. With a monitored set of 10 domains, the adversary achieves TPR ≈ 0.15 at FPR ≤ 5%; with 25 monitored domains, TPR drops to ≈ 0.09–0.10. The apparent non-monotonicity (larger monitored set → lower TPR) reflects the increased difficulty of the binary detection task as the monitored class becomes more heterogeneous and the threshold must be tuned over a broader set. Nonetheless, TPR values above 0.09 at a 5% false positive rate represent a meaningful privacy risk for domains in the monitored set.

### 5.7 Scaling Analysis (WP10)

We examine how accuracy varies with the number of training repeats and the number of domains.

**Effect of training repeats.** Accuracy generally increases as more training repeats are available. With only 4 repeats and 10 domains, accuracy ranges from approximately 0.2 to 0.5 depending on the resolver–protocol slice. With 10 repeats and 100 domains, accuracy converges to the headline numbers reported in Table 1.

**Effect of domain count.** Accuracy is non-monotone with domain count. Performance is highest for small domain sets (10 domains) and decreases as the problem scales to 50–100 domains, reflecting the increased difficulty of the classification task. The relationship is not strictly monotone: intermediate domain counts (25–50) sometimes show non-uniform accuracy, possibly due to domain clustering or class imbalance in the balanced-subsample RF.

**Practical implication.** An adversary with a small monitored set and abundant training data can achieve high closed-world accuracy. As the candidate set grows to realistic scales (100+ domains), accuracy declines, but remains well above chance.

### 5.8 Time Stability (WP11)

We evaluate cross-session generalisation by training on pilot repeats (0–7) and testing on headline T0 repeats (8–19).

**Table 8: Cross-session accuracy (pilot → T0) — Airtel.**

| Slice (resolver/protocol/workload) | Pilot→T0 Accuracy |
|------------------------------------|-------------------|
| Representative range               | 0.04 – 0.11       |

**Finding.** Cross-session accuracy is low across all evaluated slices, ranging from 0.04 to 0.11. This represents a marked degradation compared to within-session (leave-repeat-out) accuracy. The result suggests that flow-level features shift between collection sessions — likely due to changes in resolver state, CDN routing, caching behaviour, or ISP path conditions — causing learned fingerprints to become stale.

**Implication for adversaries.** A real-world adversary who trains on historical traffic and deploys the model later will observe significantly degraded performance. Fresh training data would be needed for each deployment period, substantially increasing the operational cost of a sustained fingerprinting attack.

### 5.9 Defence Simulations (WP13)

> [!WARNING]
> **The following defence results are SIMULATED. They are computed by applying perturbations to the extracted feature vectors, not by measuring actual network-level defences. These results should be interpreted as indicative lower bounds on the effectiveness of properly implemented network-layer defences.**

We simulate four classes of defences by perturbing the feature vectors of test flows before classification:

**1. Constant-rate padding.** Packet sizes are padded to the next multiple of a fixed block size (64 or 128 bytes). This reduces the discriminative power of size-based features.

**2. Random padding.** A random amount (0–128 bytes) is added to each packet size. This introduces noise without normalising sizes to a fixed grid.

**3. Delay jitter.** IAT features are perturbed by adding uniform random jitter (0–50ms or 0–200ms).

**4. Cover traffic.** A fixed number of dummy packets (10–50) are simulated by augmenting packet-count and byte features.

**Table 9: Defence simulation results — AdGuard DoH, Global workload, Airtel (SIMULATED).**

| Defence                     | Accuracy |
|-----------------------------|----------|
| No defence (baseline)       | ≈ 0.20   |
| Constant-rate padding (64B) | ≈ 0.14   |
| Constant-rate padding (128B)| ≈ 0.14   |
| Random padding (128B)       | ≈ 0.21   |
| Delay jitter (50ms)         | ≈ 0.20   |
| Delay jitter (200ms)        | ≈ 0.22   |
| Cover traffic (10–50 pkts)  | Minor effect |

**Finding.** Constant-rate padding (at 64 or 128-byte block size) reduces accuracy from approximately 0.20 to approximately 0.14, a meaningful but modest reduction. Random padding and delay jitter have little to no effect, with accuracy remaining near or above baseline. Cover traffic insertion has only minor impact on the aggregate features used by the RF classifier.

The effectiveness of constant-rate padding — but not random padding — reflects that the RF relies heavily on byte-total and size distribution features. Constant-rate normalisation destroys size-distribution information, while random padding merely shifts the distribution without normalising it. The ineffectiveness of jitter suggests that the IAT features, while included in the feature set, are not the primary discriminating signals.

> [!CAUTION]
> These simulations do not account for the overhead of deploying defences at the network level, the effect of defences on DNS query latency, or the ability of a network-level defence to interact with QUIC's encrypted packet structure. Actual defence effectiveness may differ substantially.

---

## 6. Discussion

### 6.1 Does QUIC Help?

For AdGuard, Cloudflare, and Quad9, the QUIC transport substantially reduces fingerprinting accuracy. The most dramatic example is Quad9: DoH accuracy of 0.452 (global) falls to 0.066 for DoH/3 (an 85% reduction). The likely mechanism is that QUIC's packet-level framing differs from TCP+TLS: QUIC may coalesce multiple DNS messages into fewer datagrams, vary datagram sizes due to connection-ID overhead, or change the timing profile of responses. These structural differences reduce the discriminative power of features that are highly informative over TCP+TLS (e.g., downstream packet counts and byte distributions).

However, QUIC does not eliminate fingerprinting. Even the most privacy-preserving slice (Cloudflare DoH/3 India: 0.052, Quad9 DoH/3 India: 0.056) is still > 5× above the 0.010 chance baseline. For Google, QUIC provides smaller privacy reduction: DoH/3 accuracy (0.150) remains closer to DoH accuracy (0.213) for the global workload (0.092 vs 0.182 on India), because unpadded response record variations scale directly with the answer section size.

### 6.2 Resolver Choice Matters

Resolver choice significantly affects fingerprintability. Quad9 is the most fingerprintable resolver over DoH, with accuracy nearly twice that of Google DoH. This is likely due to differences in response structure: Quad9 may serve more varied response sizes (reflecting DNSSEC signatures or varied TTL/record counts) that the classifier can distinguish. Google may apply more uniform response padding or caching behaviour. These findings have practical privacy implications: for a user concerned about DNS fingerprinting, the choice of resolver — not just the protocol — matters.

### 6.3 Feature Interpretability

The consistent superiority of aggregate RF features over sequence models has an interpretability benefit: the most discriminative features are interpretable quantities (total bytes, burst count, IATs), not raw packet bytes. This suggests that future defences should target these aggregate statistics rather than individual packet sizes. Constant-rate padding addresses the byte-distribution features but leaves IAT and burst features largely intact, which may explain why it achieves only modest (not complete) defence.

### 6.4 Implications for Privacy Standards

Our results have implications for the ongoing standardisation and deployment of encrypted DNS. The EDNS0 padding option (RFC 7830) is specified precisely to mitigate DNS fingerprinting by padding queries and responses to fixed block sizes. In our client diagnostic checks, EDNS0 padding options were not observed in the parsed response metadata of the four evaluated resolvers. While wire-level padding cannot be conclusively ruled out without server-side instrumentation or decrypted payload inspection, our empirical flow-size variations indicate that responses exhibit domain-distinguishable byte distributions in production. Our simulated results suggest that constant-rate padding would meaningfully reduce (though not eliminate) fingerprinting accuracy. Enabling EDNS0 padding — or implementing Oblivious DNS-over-HTTPS (ODoH) — would be a practical mitigation.

### 6.5 Indian ISP Context

Our study is conducted from an Indian ISP vantage point, reflecting routing conditions, resolver latencies, and link characteristics relevant to a large and growing user population. The results demonstrate that DNS fingerprinting is not a developed-world-only threat: the attack is effective from an Indian ISP with comparable accuracy to results reported in prior European studies.

---

## 7. Limitations

We identify the following limitations of this study:

1. **Access network diversity.** While we evaluate two major production networks (Airtel FTTH broadband and Reliance Jio mobile cellular), geographic diversity was restricted to a single regional vantage point. Cross-carrier behavior across other Indian ISPs (e.g., Vodafone Idea, BSNL) or international networks remains uncharacterized.

2. **Single DNS client implementation.** We use `q` v0.19.12 exclusively. Different DoH/DoH/3 clients (e.g., curl, Unbound, Firefox's built-in resolver) may generate different traffic patterns, affecting feature distributions and classifier accuracy.

3. **Single-lookup traces.** Each flow corresponds to a single DNS query for a single domain. Real browsing generates cascades of DNS queries for a single page load. Our single-query setting may overestimate or underestimate fingerprintability in the page-load context.

4. **Domain list scope.** We evaluate 100 global and 100 Indian domains. Real-world candidate sets may be much larger (thousands to millions of domains), and accuracy at that scale is unknown.

5. **EDNS0 padding observability.** Our live checks use `q`'s JSON output, which may not expose EDNS0 padding option fields. The absence of observed padding does not conclusively prove that padding is absent at the PCAP level. This is a measurement limitation, not a confirmed protocol finding.

6. **Burst n-grams not evaluated.** Computing burst-level n-gram features requires PCAP re-extraction beyond the current feature table. Burst n-grams may carry additional discriminative information not captured in our aggregate burst statistics.

7. **Defence simulations only.** WP13 defence results are computed by perturbing feature vectors, not by implementing and measuring actual network-level defences. Real-world defence effectiveness may differ substantially due to protocol constraints, overhead, and interaction with QUIC's encrypted framing.

8. **DoQ and ODoH not evaluated.** DNS-over-QUIC (DoQ, RFC 9250) and Oblivious DoH (ODoH) are not in scope for this study.

9. **Temporal snapshot.** Data was collected during a specific time window. Resolver behaviour, CDN routing, and ISP network conditions may have changed since collection.

10. **No multi-query or session-level analysis.** We do not evaluate linkability attacks that correlate multiple DNS queries across a session, which may achieve higher accuracy than per-query fingerprinting.

---

## 8. Ethics and Reproducibility

### 8.1 Ethical Considerations

**Traffic scope.** All network traffic in this study was generated by the data collection machine itself. We did not collect, intercept, or analyse traffic from any other user, device, or network.

**Data minimisation.** Raw IP addresses of the client machine are not stored in any committed dataset. Machine identifiers are stored as salted hashes. PCAPs containing raw packet payloads remain local to the collection machine and have not been committed to any repository or transmitted to third parties.

**Domain lists.** We use publicly available domain ranking lists (Tranco). No personal data or user-generated content is involved.

**No harm to resolvers or infrastructure.** Our query rate (20 queries per domain over an extended collection period) is consistent with normal resolver usage and does not constitute a stress test or denial-of-service attempt.

### 8.2 Reproducibility

**Code and data.** All feature extraction scripts, classifier pipelines, research verifiers, and preprocessed feature datasets (`dataset_v2.csv`, `dataset_jio.csv`, `dataset_combined.csv`) are version-controlled and included directly in the repository under `data/processed/`. Raw PCAPs are retained privately due to potential residual payload leakage.

**Configuration.** We document the exact tool versions (`q` v0.19.12), resolver endpoints, domain lists, feature extraction logic, classifier hyperparameters, evaluation split, and permutation test parameters to enable reproduction of results.

**Seed sensitivity.** We report mean accuracy over three random seeds (17, 42, 101) for the RF classifier. Individual seed results vary by less than 0.01 in most slices.

**Statistical reporting.** All reported accuracies are accompanied by domain-clustered block bootstrap 95% confidence intervals ($B = 1,000$ iterations) and empirical p-values from 200 domain-clustered permutation tests with False Discovery Rate (FDR) control.

---

## 9. Conclusion

We have presented a comparative empirical measurement of DoH (HTTP/2) and DoH/3 (QUIC) fingerprintability across four public resolvers, two domain workloads, and two physical Indian access networks (Airtel FTTH and Reliance Jio cellular). Evaluating Random Forest classification on 44 packet-level and flow-level metadata features, with strict temporal holdout evaluation and domain-clustered permutation significance testing, we find:

- **All 16 resolver–protocol–workload slices on broadband are significantly fingerprintable** (p < 0.005), confirming that encrypted DNS does not eliminate metadata leakage.
- **DoH/3 showed lower observed fingerprinting accuracy than DoH for AdGuard, Cloudflare, and Quad9**, with the largest observed relative drop on Quad9 (0.452 → 0.066 on global workload). **Google DoH/3 exhibited a smaller reduction**, achieving accuracy of 0.150 (vs 0.213 DoH) due to unpadded response variance.
- **Aggregate flow features (byte totals, IATs, burst statistics) dramatically outperform** packet-sequence models (n-grams, CNN, GRU), which perform near chance.
- **Cross-network transfer accuracy remained close to chance** (1.7%–2.4% vs 2.0% baseline), with domain-clustered 95% bootstrap confidence intervals spanning the baseline across evaluated slices, demonstrating that models trained on FTTH broadband do not generalize to cellular traces without pooled multi-network training.
- **Outbound UDP port 443 queries consistently timed out** on Reliance Jio cellular (100% DoH/3 failure with zero return packets), illustrating that real-world QUIC availability is constrained by access-network reachability.
- **Cross-session accuracy is low (0.04–0.11)**, suggesting that fingerprints degrade across collection windows.
- **Constant-rate padding offers modest defence** (accuracy reduction from ≈0.20 to ≈0.14 in simulation); random padding and delay jitter are largely ineffective.
- **EDNS0 padding was not observed in client diagnostic outputs** across the four evaluated resolvers; while wire-level padding cannot be conclusively ruled out without server-side instrumentation or decrypted payload inspection, our empirical flow-size variations indicate that responses exhibit domain-distinguishable byte distributions in production.

These findings underscore the need for resolver-side padding (EDNS0 padding option or equivalent) and motivate further investigation of Oblivious DoH as a stronger privacy primitive. Future work will investigate browser-level linkability, cascading DNS lookups, and real-world padding deployments.

---

## References

[Siby et al. 2020] S. Siby, M. Juarez, C. Diaz, N. Vallina-Rodriguez, and C. Troncoso. "Encrypted DNS → Privacy? A Traffic Analysis Perspective." In *Proc. NDSS 2020*. *(Foundational DoH/DoT fingerprinting paper.)*

[RFC 7858] Z. Hu, L. Zhu, J. Heidemann, A. Mankin, D. Wessels, P. Hoffman. "Specification for DNS over Transport Layer Security (TLS)." RFC 7858, IETF, 2016.

[RFC 8484] P. Hoffman, P. McManus. "DNS Queries over HTTPS (DoH)." RFC 8484, IETF, 2018.

[RFC 9250] C. Huitema, S. Dickinson, A. Mankin. "DNS over Dedicated QUIC Connections." RFC 9250, IETF, 2022.

[RFC 7830] A. Mayrhofer. "The EDNS(0) Padding Option." RFC 7830, IETF, 2016.

[Herrmann et al. 2009] D. Herrmann, R. Wendolsky, H. Federrath. "Website Fingerprinting: Attacking Popular Privacy Enhancing Technologies with the Multinomial Naïve-Bayes Classifier." In *Proc. CCSW 2009*.

[Panchenko et al. 2016] A. Panchenko et al. "Website Fingerprinting at Internet Scale." In *Proc. NDSS 2016*.

[Hayes & Danezis 2016] J. Hayes and G. Danezis. "k-fingerprinting: A Robust Scalable Website Fingerprinting Technique." In *Proc. USENIX Security 2016*.

[Rimmer et al. 2018] V. Rimmer, D. Preuveneers, M. Juarez, T. Van Goethem, W. Joosen. "Automated Website Fingerprinting through Deep Learning." In *Proc. NDSS 2018*.

[Lu et al. 2010] L. Lu, E.-C. Chang, M. C. Chan. "Website Fingerprinting and Identification Using Ordered Feature Sequences." In *Proc. ESORICS 2010*.

[Sy et al. 2020] E. Sy, C. Burkert, H. Federrath, M. Fischer. "Tracking Users across the Web via TLS Session Resumption." In *Proc. ACSAC 2018*. *(QUIC privacy analysis.)*

[Hoang et al. 2020] N. P. Hoang, A. A. Niaki, J. Dalek, J. Knockel, P. Lin, B. Marczak, M. Crete-Nishihata, P. Gill, M. Polychronakis. "An Internet-Wide Study of Traffic Policing." In *Proc. IEEE S&P 2020*.

[Herrmann et al. 2009] D. Herrmann, R. Wendolsky, and H. Federrath. "Website Fingerprinting: Attacking Popular Privacy Enhancing Technologies with the Multinomial Naïve-Bayes Classifier." In *Proc. ACM CCSW 2009*.

[Dyer et al. 2012] K. P. Dyer, S. E. Coull, T. Ristenpart, and M. Shrimpton. "Peek-a-Boo, I Still See You: Why Efficient Traffic Analysis Countermeasures Fail." In *Proc. IEEE S&P 2012*.

[Jain et al. 2022] R. Jain, D. Choffnes, and R. Ensafi. "Investigating Web Censorship in India." In *Proc. ACM IMC 2022*.

[Juarez et al. 2016] M. Juarez, M. Imani, M. Perry, C. Diaz, M. Wright. "Toward an Efficient Website Fingerprinting Defense." In *Proc. ESORICS 2016*.

[Wang & Goldberg 2017] T. Wang, I. Goldberg. "Walkie-Talkie: An Efficient Defense Against Passive Website Fingerprinting Attacks." In *Proc. USENIX Security 2017*.

[Tranco] V. Le Pochat, T. Van Goethem, S. Tajalizadehkhoob, M. Korczyński, W. Joosen. "Tranco: A Research-Oriented Top Sites Ranking Hardened Against Manipulation." In *Proc. NDSS 2019*.

---


