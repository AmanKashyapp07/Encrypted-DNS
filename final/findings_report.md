# Empirical Findings & Conclusions
## Encrypted DNS Traffic Fingerprinting Across Multi-Carrier & Enterprise Networks

**Author:** Aman Kashyap  
**Institution:** Department of Information Technology, IIIT Allahabad  
**Coursework:** Research Methodology, November 2026  
**Repository:** [github.com/AmanKashyapp07/Encrypted-DNS](https://github.com/AmanKashyapp07/Encrypted-DNS)

---

## 1. Research Scope

### 1.1 Background & Motivation

The Domain Name System (DNS) is a foundational internet protocol that translates human-readable hostnames (e.g., `google.com`) into IP addresses. Historically, DNS queries were transmitted in cleartext over UDP port 53, making every domain lookup visible to any on-path observer — ISPs, enterprise network administrators, or eavesdroppers on shared Wi-Fi.

Two modern IETF standards address this privacy gap:
- **DNS over HTTPS (DoH, RFC 8484):** Encapsulates DNS queries inside HTTPS over TCP, hiding hostnames within TLS-encrypted payloads.
- **DNS over HTTPS/3 (DoH/3, RFC 9114):** Uses HTTP/3 over QUIC (UDP port 443), offering connection establishment speedups and improved multiplexing over its TCP counterpart.

While encryption hides the plaintext query content, **unencrypted transport metadata remains visible**: packet sizes, counts, inter-arrival timing, and burst structures still traverse the network in the clear. These metadata form the basis of *website fingerprinting (WFP)* — a class of traffic analysis attacks where a passive adversary infers which domain was queried from flow-level observations alone, without decrypting any payload.

### 1.2 Research Questions

This study empirically addresses three research questions:

**RQ1 — Protocol Resistance:** Does migrating from DoH (HTTP/2 over TCP) to DoH/3 (HTTP/3 over QUIC) inherently reduce website fingerprinting accuracy across public recursive resolvers?

**RQ2 — Resolver Implementation Variance:** Does the magnitude of fingerprinting leakage differ significantly across resolvers (Google, Cloudflare, AdGuard, Quad9) using the same protocol?

**RQ3 — Cross-Network Generalisability:** Can an adversary who trains a classifier on one access network (residential FTTH) successfully deploy it against traffic from a different access network (cellular or enterprise campus)?

### 1.3 Experimental Design & Scope

| Dimension | Scope |
| :--- | :--- |
| **Traffic Type** | Client-initiated DNS queries only (passive capture; no payload modification) |
| **Domains** | 100 pinned domains: 50 Global (Tranco top-50), 50 India (top Indian domains) |
| **Resolvers** | Google (`8.8.8.8`), Cloudflare (`1.1.1.1`), AdGuard (`94.140.14.14`), Quad9 (`9.9.9.9`) |
| **Protocols** | DoH (HTTP/2 over TCP/443) and DoH/3 (HTTP/3 over QUIC/UDP 443) |
| **Networks** | 3 physical access network archetypes (see §1.4) |
| **Evaluation** | Closed-world top-1 accuracy; leave-repeat-out temporal holdout partition |
| **Features** | 44 directional flow features per query (zero label leakage — no IPs, ports, or hostnames) |
| **Statistical Validation** | 200-iteration domain-clustered permutation tests; 95% bootstrap confidence intervals (1,000 resamples) |
| **Classifier** | Random Forest (primary); XGBoost, 1D-CNN, GRU (secondary comparisons) |
| **Total Data** | 34,400 raw capture attempts → **22,407 usable zero-leakage feature traces** |

### 1.4 Network Archetypes

Three fundamentally distinct physical access environments were measured:

| Archetype | Operator | AS Number | Key Characteristics |
| :--- | :--- | :--- | :--- |
| **Residential FTTH Broadband** | Bharti Airtel Fiber | `AS24560` | Direct optical fiber; MTU 1,500 B; low latency jitter; unrestricted outbound routing. |
| **Mobile Cellular (4G/LTE)** | Reliance Jio Infocomm | `AS55836` | Wireless radio link; Carrier-Grade NAT (CGNAT); MTU 1,340 B; carrier middlebox policies. |
| **Enterprise Academic Wi-Fi** | IIIT Allahabad | `AS138231` | Multi-hop campus Wi-Fi; mandatory forward HTTP/HTTPS proxy (`172.31.2.4:8080`); institutional perimeter firewall. |

### 1.5 Scope Boundaries & What This Study Does Not Claim

- **Closed-world assumption:** Classifiers are evaluated over a fixed set of 50–100 known domains. Real-world open-world settings (where most traffic comes from outside the monitored set) are evaluated separately but not the primary focus.
- **Single geographic region:** All measurements were collected in India. Results may not generalise to other countries, ISPs, or regulatory environments.
- **Passive observation only:** The adversary model is limited to a passive on-path observer. Active attacks (injection, manipulation) are out of scope.
- **No causality claimed for QUIC reduction:** The observed leakage reductions associated with DoH/3 are reported as empirical associations. Multiplexing effects, server-side caching, and other confounds were not isolated as independent causal factors.
- **Campus proxy credentials:** No authentication was required or performed. The forward proxy at `172.31.2.4:8080` was open for HTTP/HTTPS tunnelling to all campus clients.

---

## 2. Key Findings

### Finding 1 — DoH/3 (QUIC) Reduces Fingerprinting Leakage, But Implementation Matters

Switching from DoH (HTTP/2 over TCP) to DoH/3 (HTTP/3 over QUIC) meaningfully reduces website fingerprinting accuracy on three of four tested resolvers — but the magnitude of reduction depends heavily on how each resolver implements response padding and QUIC framing.

| Resolver | DoH Accuracy | DoH/3 Accuracy | Leakage Reduction | 95% CI (DoH/3) |
| :--- | :---: | :---: | :---: | :--- |
| **Quad9** | 45.2% | 6.6% | **85%** | [3.8%, 9.8%] |
| **Cloudflare** | 26.3% | 7.2% | **73%** | [3.8%, 11.2%] |
| **AdGuard** | 26.2% | 11.2% | **57%** | [7.0%, 16.2%] |
| **Google** | 21.3% | 15.0% | **30%** | [10.7%, 19.7%] |

*Closed-world evaluation, 100-domain global workload, Airtel FTTH broadband, chance baseline = 1.0%.*

**Why Google lags:** Packet inspection revealed that Google's resolver returns unpadded DNS response payloads. The number of resource records in an answer directly determines downstream packet size, preserving domain-specific size signatures that QUIC's transport-layer changes cannot mask.

**Why Quad9 and Cloudflare improve more:** These resolvers apply aggressive QUIC padding and coalesce QUIC datagrams more aggressively, flattening the inter-packet size variance that classifiers rely on most.

> **Conclusion F1:** Protocol migration from HTTP/2 to QUIC is not a sufficient privacy safeguard on its own. Resolver-level padding policy is the dominant determinant of residual fingerprinting exposure.

---

### Finding 2 — Pervasive QUIC / UDP 443 Inaccessibility Across Carrier & Institutional Networks

DoH/3 is unreachable in practice on two of the three tested access networks. Despite RFC 9000 and RFC 9114 standardisation, outbound QUIC traffic over UDP 443 is systematically dropped or blackholed.

| Network | Operator | DoH (TCP) Reachability | DoH/3 (QUIC) Reachability | UDP 443 Blocked |
| :--- | :--- | :---: | :---: | :---: |
| **Residential FTTH** | Airtel (`AS24560`) | 100% | **100%** | No |
| **Mobile Cellular** | Reliance Jio (`AS55836`) | 90.5%–100%* | **0.0%** | **Yes — 3,000/3,000** |
| **Enterprise Campus** | IIIT Allahabad (`AS138231`) | 30.9%–63.1%** | **0.0%** | **Yes — 3,000/3,000** |

\*Google DoH: 100%; AdGuard DoH: 90.5%; Cloudflare DoH on Jio: only 1.5% (resolver-level filtering suspected).  
\*\*Campus DoH passes through the mandatory forward proxy `172.31.2.4:8080` — lower success rates reflect proxy timeout overhead.

This is not a matter of QUIC falling back gracefully — the measurement harness used a strict 2-second UDP timeout, confirming that **zero QUIC packets were returned** in 6,000 independent attempts across both Jio and Campus networks.

> **Conclusion F2:** QUIC/HTTP3-based encrypted DNS faces an *ossification problem*: 2 out of 3 tested Indian access network archetypes (representing mobile and enterprise users) completely block outbound UDP 443, making DoH/3's privacy benefits irrelevant to these user populations without protocol fallback.

---

### Finding 3 — Cross-Network Fingerprinting Transfer Collapses to Chance

Fingerprinting classifiers trained on one access network **completely fail** when evaluated against traffic from a different network archetype. The 3×3 cross-network transfer matrix demonstrates a universal failure across all 6 directional pairs.

| Transfer Direction | Test Size | Transfer Accuracy | 95% Bootstrap CI | Chance Baseline |
| :--- | :---: | :---: | :---: | :---: |
| Airtel → Jio | 500 | **1.7%** | [0.0%, 4.7%] | 2.0% |
| Jio → Airtel | 600 | **2.0%** | [0.0%, 6.0%] | 2.0% |
| Airtel → Campus | 310 | **1.9%** | [0.8%, 3.3%] | 2.0% |
| Campus → Airtel | 600 | **2.2%** | [0.5%, 4.5%] | 2.0% |
| Jio → Campus | 310 | **2.7%** | [0.8%, 5.0%] | 2.0% |
| Campus → Jio | 500 | **2.4%** | [0.7%, 5.0%] | 2.0% |

*Google DoH, 50 shared domains, chance baseline = 2.0% (1/50). All 95% bootstrap CIs span the chance level.*

The physical mechanism behind this collapse is confirmed by feature-level Kolmogorov-Smirnov tests (all p < 10⁻¹⁵). The top distribution-shifting features are:

| Feature | Campus Mean | Airtel Mean | Jio Mean | KS Statistic |
| :--- | :---: | :---: | :---: | :---: |
| `up_max` (max upstream packet size) | 1,505 B | 1,320 B | 1,313 B | **0.994** |
| `down_max` (max downstream packet size) | 1,426 B | 1,320 B | 1,303 B | **0.936** |
| `pkt_00` (first packet direction/size) | −137 B | +698 B | +75 B | **0.837** |
| `t_first_down` (first downstream delay) | 93.7 ms | 216.1 ms | 248.5 ms | **0.727** |

Packet sizing differences stem from MTU clamping (Jio cellular enforces MTU 1,340 B vs Airtel's 1,500 B), and the proxy CONNECT handshake at IIIT Allahabad inverts the direction of the first packets, completely invalidating features trained on direct-connection traffic patterns.

> **Conclusion F3:** Network fingerprinting classifiers do not generalise across access network boundaries. The physical channel (MTU, jitter, latency, proxy topology) determines flow structure far more than the DNS resolver identity, making single-vantage attack models ineffective in multi-carrier deployment scenarios.

---

### Finding 4 — Institutional Forward Proxies Act as an Inadvertent Privacy Shield

Within-campus fingerprinting accuracy (1.8%–5.6%) is **3.2× to 8.0× lower** than on residential FTTH broadband (18.2%–45.2%), despite using the same 44 features and the same classification methodology.

| Within-Network DoH Fingerprinting | Accuracy | 95% Bootstrap CI | Chance | p-value | Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| AdGuard · Campus (Global) | **5.6%** | [1.0%, 11.8%] | 2.4% | 0.025 | **Significant** |
| Cloudflare · Campus (Global) | **4.9%** | [1.1%, 9.4%] | 2.0% | 0.010 | **Significant** |
| Google · Campus (Global) | **3.7%** | [0.4%, 7.8%] | 2.0% | 0.100 | Near-significant |
| Google · Campus (India) | **4.2%** | [1.2%, 8.0%] | 2.1% | 0.085 | Near-significant |
| AdGuard · Campus (India) | **3.2%** | [0.0%, 7.7%] | 2.8% | 0.433 | Non-significant |
| Cloudflare · Campus (India) | **1.9%** | [0.4%, 4.1%] | 2.0% | 0.508 | Non-significant |

The institutional HTTP/HTTPS proxy (`172.31.2.4:8080`) introduces three obfuscating mechanisms:
1. **Connection reuse:** Multiple DNS queries share the same upstream TLS session, mixing response packets in time.
2. **Buffering & batching:** The proxy queues outbound requests and flushes responses in bursts, flattening inter-query timing signals.
3. **Framing overhead:** CONNECT tunnel framing and proxy-level chunked encoding add variable byte counts that dilute per-domain size signatures.

> **Conclusion F4:** Enterprise and institutional forward proxies act as unintended, zero-configuration DNS flow obfuscators. Campus users are substantially more protected from passive fingerprinting than residential broadband users. Traditional WFP attack models trained on direct-connection traffic are ineffective in proxy-mediated environments.

---

### Finding 5 — Multi-Vantage Co-Training Recovers Adversarial Power

When an adversary collects training data simultaneously across all three network archetypes and co-trains a single pooled classifier, discriminative power is recovered.

| Test Network (Held-Out) | Pooled Train Size | Test Size | Accuracy | 95% CI | Chance |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Airtel Broadband (Google Global) | 1,120 | 100 | **18.0%** | [11.3%, 25.0%] | 2.0% |
| Reliance Jio Cellular (Google Global) | 1,120 | 100 | **14.0%** | [8.0%, 20.7%] | 2.0% |
| IIIT Campus Wi-Fi (Google Global) | 1,120 | 90 | **3.7%** | [0.4%, 7.8%] | 2.0% |
| **Tri-Network Composite (Google Global)** | **1,120** | **290** | **12.2%** | [8.7%, 16.2%] | **2.0%** |
| **Mean across all 6 composite slices** | — | — | **20.67%** | — | **2.0%** |

The pooled composite test set delivers **10.3× above-chance accuracy**, confirming that multi-vantage adversaries with simultaneous probes across diverse network environments can build resilient, carrier-agnostic fingerprinting models.

> **Conclusion F5:** While single-network adversaries face fundamental channel-induced failure when deploying across network boundaries, multi-vantage adversaries who diversify their training vantage points can effectively generalise. This represents a significant threat model escalation for real-world DNS privacy.

---

## 3. Overall Conclusions

This study empirically characterises encrypted DNS traffic fingerprinting across three distinct Indian access network archetypes — residential FTTH broadband, mobile cellular (4G/LTE), and enterprise academic campus Wi-Fi — using 34,400 live packet captures and a strict zero-leakage 44-feature extraction pipeline.

### 3.1 Summary Table

| Conclusion | Core Finding | Strength of Evidence |
| :---: | :--- | :--- |
| **C1** | DoH/3 reduces fingerprinting leakage by 57%–85% on Cloudflare, Quad9, and AdGuard. Google's unpadded implementation limits its gain to only 30%. | Strong — p < 0.005, 200 permutation iterations, tight 95% CIs. |
| **C2** | QUIC / UDP 443 is completely inaccessible on both Reliance Jio cellular and IIIT Allahabad campus (0.0% reachability across 6,000/6,000 attempts). DoH/3's privacy benefits are practically irrelevant to mobile and institutional Indian users. | Very Strong — exhaustive empirical audit, two independent network environments. |
| **C3** | Cross-network classifier transfer collapses to random chance (1.7%–2.7% vs 2.0% baseline) across all 6 pairs in the 3×3 matrix. Physical channel characteristics (MTU, proxy, CGNAT) dominate over resolver identity. | Strong — domain-clustered bootstrap CIs span chance in all off-diagonal slices. |
| **C4** | Institutional forward proxies act as unintended privacy shields, reducing campus fingerprinting to 1.8%–5.6% — a 3–8× reduction vs residential broadband — through connection reuse, buffering, and framing overhead. | Moderate — statistically significant in 2 of 6 slices; near-significant in 2 more. |
| **C5** | Multi-vantage co-training across all three networks yields 20.67% mean composite accuracy (10.3× above chance), demonstrating that adversaries with diverse collection vantage points can overcome single-network channel noise. | Moderate — robust on large-sample Google/AdGuard slices; Cloudflare slices use few shared domains. |

### 3.2 Practical Implications

**For users:**
- Choosing DoH over Quad9 or Cloudflare provides meaningful fingerprinting resistance compared to no encryption. Upgrading to DoH/3 provides further reduction on these resolvers — if you are on a residential broadband connection. Mobile and campus users cannot access DoH/3 at all.
- Enterprise campus users behind forward proxies enjoy substantial incidental fingerprinting protection; this should not be confused with intentional privacy design.

**For DNS resolver operators:**
- Response padding is not optional for meaningful privacy. Google's resolver demonstrates that QUIC alone is insufficient without padding; unpadded responses preserve per-domain size signatures across protocol upgrades.
- Quad9's combination of QUIC padding and datagram coalescence sets the best observed privacy standard in this study.

**For network administrators & policymakers:**
- Blocking outbound UDP 443 (as observed on Jio and IIIT campus) prevents DoH/3 adoption without user awareness. If QUIC is to be viable for privacy-sensitive applications, carrier and institutional packet filters must be updated.
- The accidental privacy benefit of forward proxies suggests that mandatory proxy deployment could be deliberately leveraged as a lightweight anonymisation tool.

**For security researchers:**
- Single-network WFP threat models are insufficient for real-world threat assessment. Future attack evaluations must account for cross-network deployment failure and multi-vantage adversary escalation paths.
- Feature distribution shift analysis (KS-test, p < 10⁻¹⁵) provides a principled diagnostic for understanding *why* transfer fails, not just *that* it fails.

### 3.3 Limitations

- **Closed-world assumption:** Results apply to 50–100 monitored domains. Open-world accuracy is substantially lower.
- **Single-country measurement:** All data collected in India; findings may not generalise globally.
- **Temporal snapshot:** Resolver implementations, carrier policies, and campus network configurations may change. Results reflect conditions observed in November 2026.
- **Causal isolation:** The relative contributions of QUIC padding, datagram coalescence, and multiplexing to leakage reduction were not independently isolated.
- **p-values not adjusted for multiple comparisons:** All reported p-values are nominal. Results should be treated as exploratory rather than confirmatory.

---

*All reported p-values are nominal unadjusted permutation test values. All confidence intervals are domain-clustered bootstrap (1,000 resamples). Full numerical derivations, source CSVs, and reproduction scripts are available in the project repository.*
