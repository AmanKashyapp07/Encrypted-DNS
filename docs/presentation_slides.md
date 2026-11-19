# Presentation Slide Deck: Encrypted DNS Traffic Fingerprinting Across Multi-Carrier & Enterprise Networks

**Author:** Aman Kashyap (`iit2024140@iiita.ac.in`)  
**Department:** Information Technology, Indian Institute of Information Technology Allahabad (IIIT Allahabad)  
**Context:** Research Methodology Coursework / Project Defense, November 2026  
**Repository:** [github.com/AmanKashyapp07/Encrypted-DNS](https://github.com/AmanKashyapp07/Encrypted-DNS)  
**Associated Artifacts:** [`docs/paper.md`](paper.md) · [`docs/findings_report.md`](findings_report.md) · [`readme.md`](../readme.md)

---

## Slide 1: Title & Overview

### Empirical Evaluation of Encrypted DNS Traffic Fingerprinting Across Multi-Carrier and Institutional Networks

* **Speaker:** Aman Kashyap (IIIT Allahabad)
* **Core Question:** When DNS queries are encrypted using modern IETF standards (DoH & DoH/3), can an on-path eavesdropper still infer the requested domain using physical traffic metadata alone?
* **Empirical Scale:** 34,400 raw captures → 22,407 zero-leakage flow traces across 3 network archetypes (Airtel FTTH, Reliance Jio 4G, and IIIT Allahabad Campus Wi-Fi).

> **Speaker Note (30 sec):**  
> *"Good morning, Professor. Today I am presenting our empirical research on encrypted DNS privacy. While DNS-over-HTTPS and DNS-over-QUIC hide hostnames through cryptographic encryption, unencrypted transport metadata—packet sizes, directions, and timing—still crosses the physical wire. We built an end-to-end capture and analysis testbed to measure whether passive observers can fingerprint user browsing, and whether protocol resistance holds across real-world broadband, cellular, and campus networks."*

---

## Slide 2: The Core Problem — Encryption vs. Metadata Leakage

### Plaintext DNS is Broken, But Does Encryption Fully Protect the Wire?

* **RFC 8484 (DoH):** Encapsulates queries within TLS over TCP port 443.
* **RFC 9114 (DoH/3):** Uses HTTP/3 over QUIC (UDP port 443), eliminating TCP head-of-line blocking.
* **The Vulnerability (Traffic Fingerprinting):**
  * Even inside TLS/QUIC, packet lengths, directional sequences, and inter-arrival times (IATs) are transmitted in cleartext.
  * An on-path observer (ISP, cellular carrier, or local campus gateway) can train supervised classifiers on these flow "silhouettes" to predict the queried domain without decrypting any payload.

> **Speaker Note (45 sec):**  
> *"The key distinction to highlight is payload encryption versus transport metadata. A user assumes that because their browser connects to 1.1.1.1 over HTTPS, their ISP sees nothing. In reality, every website has a distinct DNS answer record profile—varying number of A/AAAA records, CNAME chains, and response sizes. This creates a unique physical silhouette that machine learning classifiers can identify."*

---

## Slide 3: Threat Model & Feature Representation

### Passive Eavesdropping with a Strict Zero-Leakage Guarantee

```
  Client Terminal             Physical Channel               Recursive Resolvers
┌─────────────────┐       ┌──────────────────────┐         ┌─────────────────────┐
│  q DNS Client   ├──────►│ Passive Probe Wire   ├────────►│ Cloudflare, Google, │
│ (DoH and DoH/3) │       │ (dumpcap / tshark)   │         │ Quad9, AdGuard      │
└─────────────────┘       └──────────┬───────────┘         └─────────────────────┘
                                     │
                          44 Directional Features
                          (No IPs, No Ports, No SNI)
                                     ▼
                          ┌─────────────────────┐
                          │  Random Forest /    │ ────► Predicted Domain
                          │  Gradient Boosting  │       (Top-1 Accuracy)
                          └─────────────────────┘
```

* **44 Features across 5 groups:**
  1. *Volume (7):* Total packets, total bytes, directional ratios.
  2. *Size Statistics (6):* Min, max, mean, std of upstream/downstream packet sizes.
  3. *Timing & Latency (6):* Flow duration, time-to-first-response (`t_first_down`), IAT statistics.
  4. *Burst Dynamics (5):* Number of directional bursts, max burst packet count.
  5. *Handshake Dynamics (20):* Signed directional sizes of first 20 packets (`pkt_00`–`pkt_19`).
* **Evaluation Protocol:** Strict leave-repeat-out temporal holdout (repeats 0–7 train, 8–9 test); 200 domain-clustered label permutations per slice ($p < 0.005$).

> **Speaker Note (45 sec):**  
> *"To ensure academic integrity, we enforce a strict zero-label-leakage guarantee. We strip client IPs, resolver IPs, port numbers, and SNI headers. The classifier learns purely from the physical physics of the traffic flow. Furthermore, we use temporal holdout validation across different query repeats rather than random splits to prevent session leakage."*

---

## Slide 4: Tri-Network Empirical Archetypes

### Capturing Real-World Network Heterogeneity Across India

| Parameter | Network 1: Residential FTTH | Network 2: Mobile Cellular | Network 3: Enterprise Campus Wi-Fi |
| :--- | :--- | :--- | :--- |
| **Operator / Entity** | Bharti Airtel Fiber (`AS24560`) | Reliance Jio Infocomm (`AS55836`) | IIIT Allahabad (`AS138231`) |
| **Link Topology** | Direct optical fiber | Wireless radio link (4G/LTE) | Multi-hop IEEE 802.11 Wi-Fi |
| **Middlebox Layer** | Direct routing; unconstrained | Carrier-Grade NAT (CGNAT) | Mandatory forward proxy (`172.31.2.4:8080`) |
| **MTU Configuration** | 1,500 Bytes | Clamped to 1,340 Bytes | 1,500 Bytes |
| **UDP 443 Policy** | Open (**100% DoH/3 reachable**) | Dropped (**0.0% DoH/3 reachable**) | Blocked by firewall (**0.0% DoH/3 reachable**) |
| **Processed Flows** | **18,926** traces | **1,912** traces | **1,569** traces |

**Total Combined Benchmark Dataset:** **22,407 zero-leakage feature traces** (`dataset_tri_network.csv`).

> **Speaker Note (45 sec):**  
> *"Previous studies evaluated encrypted DNS in synthetic lab environments or single broadband links. We evaluated three distinct physical access archetypes: home fiber, 4G cellular, and enterprise campus Wi-Fi. Notice how link properties differ: Jio cellular clamps MTU to 1,340 bytes, and IIIT Allahabad routes all web traffic through an institutional forward proxy while blocking outbound UDP 443."*

---

## Slide 5: Finding 1 — DoH vs. DoH/3 & The Google Anomaly

### QUIC Mitigates Leakage, but Implementation Outweighs Protocol

* **Headline Results on Broadband (100-domain closed world; Chance = 1.0%):**
  * **Quad9:** 45.2% (DoH) → **6.6% (DoH/3)** (**85% leakage reduction**, $p < 0.005$)
  * **Cloudflare:** 26.3% (DoH) → **7.2% (DoH/3)** (**73% leakage reduction**, $p < 0.005$)
  * **AdGuard:** 26.2% (DoH) → **11.2% (DoH/3)** (**57% leakage reduction**, $p < 0.005$)
  * **Google:** 21.3% (DoH) → **15.0% (DoH/3)** (**Only 30% reduction**)

* **The Google Anomaly Explained:**
  * Cloudflare and Quad9 apply aggressive QUIC padding and datagram coalescence, flattening packet-size variance.
  * Google returns **unpadded response records**: downstream packet sizes scale in lockstep with the number of DNS answers, preserving distinct byte signatures across both HTTP/2 and QUIC.

> **Speaker Note (1 min):**  
> *"Our first major finding is that migrating to QUIC reduces fingerprinting accuracy by 57% to 85% for Quad9, Cloudflare, and AdGuard. However, Google is a dramatic outlier, dropping only from 21.3% to 15.0%. When we inspected raw packet traces, we discovered that Google does not pad DNS answer sections. This proves a vital security insight: transport protocol upgrades are ineffective if the application layer fails to pad response records."*

---

## Slide 6: Finding 2 — Pervasive QUIC Inaccessibility & Ossification

### Figure 5: Outbound UDP 443 is Universally Blocked on Cellular and Campus Networks

```
100% ──────── 100%       100%                 100%
                █                                
                █                                
 50%            █                                
                █                                
  0% ───────────┴──────    0% (Blocked) ──────    0% (Blocked)
        Airtel FTTH           Reliance Jio          IIIT Allahabad
        (Broadband)            (Cellular)          (Campus Wi-Fi)

     [Green: DoH (TCP)]      [Red Hatch: DoH/3 (QUIC / UDP 443)]
```

* **The Empirical Reality:**
  * **Airtel Broadband:** 100% reachability for both TCP DoH and QUIC DoH/3.
  * **Reliance Jio Cellular:** **0 / 3,000 DoH/3 queries succeeded** (100% client timeouts on UDP 443).
  * **IIIT Allahabad Campus:** **0 / 3,000 DoH/3 queries succeeded** (100% dropped by perimeter firewall).
* **The Ossification Problem:** Despite RFC standardisation, HTTP/3 over QUIC cannot be deployed as a primary protocol for mobile or enterprise users without automatic TCP fallback.

> **Speaker Note (1 min):**  
> *"Slide 6 presents Figure 5 from our paper. While HTTP/3 is celebrated as the future of the web, our empirical audit reveals severe transport ossification. Across 3,000 attempts on Reliance Jio and 3,000 attempts on IIIT campus Wi-Fi, exactly zero QUIC packets were returned. Mobile CGNAT middleboxes and enterprise perimeter firewalls systematically drop outbound UDP 443. For most Indian mobile and campus users, DoH/3's privacy benefits are currently inaccessible."*

---

## Slide 7: Finding 3 — Universal Cross-Network Transfer Collapse

### Figure 6: $3 \times 3$ Cross-Network Transfer Matrix (Google DoH, 50 Shared Domains)

```
                       EVALUATION / VICTIM NETWORK
                   Airtel FTTH       Reliance Jio      Campus Wi-Fi
                 (Broadband)          (Cellular)        (Enterprise)
               ┌───────────────┬─────────────────┬────────────────┐
  Airtel FTTH  │     28.5%     │      1.7%       │      1.9%      │
 (Broadband)   │ (Within-Net)  │   (CI: 0-4.7%)  │  (CI: 0.8-3.3%)│
               ├───────────────┼─────────────────┼────────────────┤
  Reliance Jio │      2.0%     │      9.7%       │      2.7%      │
  (Cellular)   │  (CI: 0-6.0%) │  (Within-Net)   │  (CI: 0.8-5.0%)│
               ├───────────────┼─────────────────┼────────────────┤
  Campus Wi-Fi │      2.2%     │      2.4%       │      4.0%      │
  (Enterprise) │ (CI: 0.5-4.5%)│  (CI: 0.7-5.0%) │  (Within-Net)  │
               └───────────────┴─────────────────┴────────────────┘
                  Baseline Random Guessing Chance = 2.0% (1/50)
```

* **Observation:** Every off-diagonal transfer cell collapses to **1.7%–2.7%** (indistinguishable from the **2.0% chance baseline**), with 95% bootstrap confidence intervals spanning chance.
* **Why Transfer Fails:** Two-sample Kolmogorov-Smirnov tests confirm that channel characteristics alter feature distributions ($p < 10^{-15}$):
  * `up_max` KS = 0.994 (proxy TLS framing overhead)
  * `down_max` KS = 0.936 (cellular MTU clamping to 1,340 B)
  * `pkt_00` KS = 0.837 (proxy HTTP `CONNECT` handshake inverts first packet direction)

> **Speaker Note (1 min):**  
> *"Slide 7 displays our 3x3 transfer matrix (Figure 6). Notice the diagonal versus off-diagonal cells. An attacker who trains on residential broadband achieves 28.5% within their network. But when that model is deployed against victim traffic on Jio cellular or Campus Wi-Fi, accuracy collapses to 1.7% and 1.9%—pure random chance. Physical network physics (MTU clamping, wireless jitter, proxy framing) dominate the traffic shape far more than the domain identity."*

---

## Slide 8: Finding 4 — Forward Proxies as an Inadvertent Privacy Shield

### Within-Campus Fingerprinting Drops by $3\times$ to $8\times$

| Network Environment | AdGuard DoH | Cloudflare DoH | Google DoH | Baseline Chance |
| :--- | :---: | :---: | :---: | :---: |
| **Airtel Broadband** | **26.2%** | **26.3%** | **21.3%** | 1.0% |
| **Campus Wi-Fi (Behind Proxy)** | **5.6%** | **4.9%** | **3.7%** | 2.0% |

* **The Proxy Obfuscation Mechanism:**
  1. **Connection Reuse:** The campus forward proxy (`172.31.2.4:8080`) pools and reuses upstream TCP/TLS connections across multiple client sessions, mixing packets in time.
  2. **Buffering & Jitter:** The proxy introduces queueing delays and flushes responses in micro-bursts, smoothing out domain-specific inter-arrival times.
  3. **CONNECT Tunnelling:** HTTP `CONNECT` encapsulation adds variable byte framing that masks subtle answer-size distinctions.

> **Speaker Note (45 sec):**  
> *"Our fourth discovery was surprising: institutional forward proxies act as an accidental privacy defense. Within-campus fingerprinting accuracy is between 1.8% and 5.6%, compared to up to 45% on broadband. By multiplexing upstream connections and buffering packets, enterprise proxies naturally dilute flow signatures without requiring any cryptographic changes."*

---

## Slide 9: Finding 5 — Multi-Vantage Adversarial Recovery

### Co-Training on Multi-Carrier Data Restores Attack Power

| Test Set Partition (Held-Out) | Single-Network Transfer | Tri-Network Pooled Accuracy | Lift Over Chance |
| :--- | :---: | :---: | :---: |
| **Held-Out Airtel Broadband** | 2.0% (Transfer Collapse) | **18.0% – 73.3%** | **9× – 36×** |
| **Held-Out Jio Cellular** | 1.7% (Transfer Collapse) | **14.0%** | **7×** |
| **Held-Out Campus Wi-Fi** | 1.9% (Transfer Collapse) | **3.7%** | **1.8×** |
| **Tri-Network Composite Test Set** | **2.0% (Chance)** | **20.67% Mean Composite** | **10.3×** |

* **Adversarial Implication:** While a single-vantage attacker fails across network boundaries, an attacker who collects training data across diverse access networks builds a **carrier-resilient model**, achieving **over 10× above-chance accuracy** on unseen composite traffic.

> **Speaker Note (45 sec):**  
> *"Can an adversary overcome network distribution shift? Yes. When we pool training data across all three networks, composite test set accuracy recovers to 20.67%, and up to 73.3% on broadband flows. This demonstrates that multi-vantage adversaries with probes in multiple networks can successfully build generalized classifiers."*

---

## Slide 10: Conclusions & Practical Recommendations

### Summary of Contributions

1. **Protocol Reality:** DoH/3 over QUIC reduces fingerprinting by 57%–85% on padded resolvers (Quad9, Cloudflare), but implementation choices (the Google anomaly) limit privacy if padding is absent.
2. **Deployment Reality:** QUIC is 100% blocked on 2 of the 3 tested network archetypes (cellular and enterprise campus).
3. **Attack Reality:** Cross-network fingerprinting collapses to chance (1.7%–2.7%) under naive transfer, but recovers to 20.67% under multi-vantage co-training.
4. **Architectural Reality:** Institutional forward proxies provide accidental but effective flow obfuscation (1.8%–5.6% accuracy).

### Practical Recommendations
* **For Resolvers:** Enforce mandatory EDNS0 response padding (RFC 8467).
* **For Carriers & Campuses:** Unblock outbound UDP 443 to enable modern encrypted transport adoption.
* **For Researchers:** Move beyond single-network synthetic testbeds to multi-vantage evaluations.

> **Speaker Note (45 sec):**  
> *"To conclude: encrypted DNS significantly improves user privacy over plaintext DNS, but transport metadata remains a viable attack vector on unpadded resolvers. In real-world deployment, QUIC's benefits are throttled by institutional middleboxes, and single-network classifiers fail across carrier boundaries. Our complete dataset, verification suite, and paper manuscript are publicly available on GitHub. Thank you, and I look forward to your questions."*

---

## Slide Deck Appendix: Professor Defense & Viva Cheat Sheet

### Anticipated Tough Questions & Rapid-Fire Answers

| Professor's Question | Data-Backed Answer | Reference in Paper |
| :--- | :--- | :--- |
| *"Why didn't you use deep sequence models (1D-CNN or LSTMs)?"* | "We benchmarked 1D-CNN and GRU models in Section 5.6. They collapsed to 1.0%–1.4% (near random chance). DNS flows are micro-flows (15–40 packets total), so they lack the sequential token depth needed to train deep representations. Random Forest tabular ensembles that leverage aggregate burst and volume features decisively outperform deep learning on DNS." | Section 5.6, Table 9 |
| *"Why did you use 44 features instead of 100+?"* | "Our 44 features are strictly transport-agnostic and direction-aware, divided into 5 orthogonal groups (volume, sizes, timing, bursts, handshake). Adding raw packet payloads or non-robust timing features risks overfitting to transient network jitter." | Section 4.2 |
| *"How did you prevent label leakage?"* | "We completely stripped IP addresses, port numbers, SNI hostnames, and MAC identifiers. Models were trained strictly on traffic shape dynamics, verified by 200 label-permutation baseline tests ($p < 0.005$)." | Section 4.1 |
| *"Why did DoH/3 fail completely on Jio and Campus?"* | "Outbound UDP 443 queries experienced consistent client-side timeouts across 6,000 independent attempts (0 return packets). Campus perimeter firewalls enforce default-deny policies on UDP 443, and Jio CGNAT drops unsolicited UDP associations." | Section 5.2 & Section 5.4 |
| *"Why is 73.3% reported for Cloudflare in Table 7?"* | "73.3% is an isolated slice on Cloudflare Global where only 5 shared domains had valid completed traces across all three networks ($n_{\text{test}} = 10$). While statistically valid within its slice, the robust 50-domain benchmark is Google Global at 18.0%–20.7% composite accuracy." | Section 5.4, Table 7 note |
